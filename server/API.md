# MathsMaster VPS API (v1)

This is the contract the iPad and iPhone apps code against. The machine-readable version is [`openapi.json`](openapi.json), generated from the code; a test keeps both in step. Design background: `docs/DESIGN.md` §4.8 (Anki import), §5 (Claude), §7.7 (VPS).

- **Base URL:** whatever the owner sets up, e.g. `https://mathsmaster.example.ts.net` (Tailscale) or `https://mm.example.com` (Caddy). Every path starts with `/v1`.
- **Auth:** `Authorization: Bearer mm_…`, one token per app install (see [Auth](#auth)). Only `GET /v1/health` is open.
- **Format:** JSON in UTF-8, except file bodies (raw bytes) and thread replies (server-sent events). Times are ISO 8601 UTC (`2026-11-22T09:14:03.120Z`).
- **Errors** always look like `{"error": {"code": "guidelines_missing", "message": "…"}}` with a fitting HTTP status. Codes are listed in [Errors](#errors). The app should show the message and switch on the code.

## Contents

1. [Auth](#auth)
2. [Meta](#meta)
3. [Backup mirror](#backup-mirror)
4. [Anki import](#anki-import)
5. [Claude jobs](#claude-jobs)
6. [Claude threads](#claude-threads)
7. [Errors](#errors)
8. [Limits](#limits)
9. [Not yet](#not-yet)

---

## Auth

Each app copy (iPad Playgrounds, iPad SideStore, iPhone) gets its own token, created on the VPS:

```
mathsmaster-server token add "iPad · Playgrounds"
```

The token is printed once; the server stores only its SHA-256. The app keeps it in its Keychain (never in the library folder, which is synced) and sends it on every request. `token revoke NAME` disables one device without touching the others. A missing, unknown or revoked token gets `401 unauthorized`.

The service listens on `127.0.0.1` and relies on the layer in front for transport security: Tailscale (WireGuard, with `tailscale serve` for HTTPS) or Caddy with a real certificate. See [README.md](README.md).

## Meta

### `GET /v1/health`
No auth. `{"ok": true}`. For uptime checks.

### `GET /v1/status`
What the Settings → VPS screen shows.

```json
{
  "version": "0.1.0",
  "device": {"id": "dev_…", "name": "iPad · Playgrounds"},
  "mirror": {"files": 1840, "bytes": 612000000, "lastUpload": "2026-11-22T09:14:03.120Z"},
  "library": true,
  "guidelines": true,
  "claude": {"runner": "cli", "available": true, "model": "claude-opus-5-5"},
  "jobs": {"queued": 1, "running": 1}
}
```

`library` / `guidelines`: whether `library.json` and `AI/card-guidelines.md` are in the mirror yet. Claude features need both.

## Backup mirror

The VPS keeps a plain copy of the library folder, path for path. The app is the source of truth; the mirror never pushes changes back. Nightly snapshots of the mirror (restic) give history. The mirror is also what Claude reads, so keeping it current means Claude sees the latest notes without per-request uploads.

Paths are library-relative with `/` separators, e.g. `Courses/Linear Algebra/cards.json`. Send them percent-encoded in the URL (`Courses/Linear%20Algebra/cards.json`). The server normalises names to Unicode NFC and rejects `..`, `.`, empty segments, backslashes, control characters, absolute paths and junk names (`.DS_Store`).

### `GET /v1/manifest`

```json
{
  "files": [
    {"path": "Courses/Linear Algebra/cards.json", "size": 40213,
     "sha256": "9f2c…", "modified": "2026-11-22T09:00:00Z", "uploaded": "2026-11-22T09:14:03.120Z"}
  ],
  "fileCount": 1, "bytes": 40213, "lastUpload": "2026-11-22T09:14:03.120Z"
}
```

`modified` echoes the `X-Modified` header sent with the upload (null if none). Files placed in the mirror by other means (a restic restore) appear too, with `modified`/`uploaded` null.

### `PUT /v1/files/{path}`

Create or replace one file. Body: the raw bytes (`Content-Type: application/octet-stream`).

| Header | |
|---|---|
| `X-Content-SHA256` | optional, recommended: hex SHA-256 of the body. On mismatch → `400 hash_mismatch` and nothing is written. |
| `X-Modified` | optional: the file's modification time in the library (ISO 8601), stored for restores. |

Writes are atomic (temp file + fsync + rename). Response: the manifest entry for the file. A file can't sit where a folder exists or vice versa → `409 path_conflict`.

### `GET /v1/files/{path}`
The raw bytes, with `X-Content-SHA256`. Used by *Settings → Backups → Restore*, which always restores into a **new** folder: list the manifest, then download every file.

### `DELETE /v1/files/{path}`
Removes the file from the mirror. It goes to a server-side trash, purged after `MM_TRASH_DAYS` (30). `404` if absent.

### Recommended sync loop (app side)

1. Debounce changes (and run on launch/foreground, optionally Wi-Fi only).
2. `GET /v1/manifest`, hash local files (cache hashes by size + mtime), and compare.
3. `PUT` each local file whose hash differs or is missing on the server; `DELETE` server files the library no longer has.
4. Skip caches and per-install noise: `.open-<installID>` heartbeat files and anything in the app sandbox. Do upload `library.json`, `AI/card-guidelines.md`, `Courses/**` (including `cards.json`, `ai-instructions.md`, PDFs and `.drawing` ink), `Reviews/**`, `Inbox/jobs/**`, `.trash/` is optional.
5. Show "VPS backup: 2 min ago" from `lastUpload`.

## Anki import

One-off import of an Anki deck with its review history (DESIGN.md §4.8). iOS has no zip/zstd, so the VPS unpacks it.

Supported: `.apkg` and `.colpkg` in every format Anki writes: the current one (`collection.anki21b`, zstd, schema 18, zstd media), legacy 2 (`collection.anki21`) and legacy 1 (`collection.anki2`).

### `POST /v1/imports?filename=Methods.apkg`
Body: the raw package bytes. Returns `202` with the import status (below) and converts in the background. The uploaded package is deleted as soon as conversion ends.

### `GET /v1/imports/{import_id}`

```json
{
  "id": "imp_20261122T091403_ab12cd34",
  "status": "succeeded",
  "filename": "Methods.apkg", "size": 1203344,
  "createdAt": "…", "finishedAt": "…",
  "summary": {"decks": 1, "cards": 214, "notes": 214, "reviews": 1930, "media": 3, "suspended": 2, "cardsWithWarnings": 0},
  "decks": [{"id": "1795318240149", "name": "IB::Methods", "cardCount": 214, "reviewCount": 1930, "suggestedCourseId": "c-methods"}],
  "warnings": [],
  "error": null
}
```

`status`: `queued` → `running` → `succeeded` | `failed` (`error` = `{code, message}`). Poll every second or two; small decks finish in well under a second. Show the Inbox item as *"Methods: 214 cards, 1,930 past reviews"*.

`suggestedCourseId` matches the deck name against course names in the mirrored `library.json`; the user confirms the mapping.

### `GET /v1/imports/{import_id}/result`

The full conversion. Shape:

```jsonc
{
  "schemaVersion": 1,
  "kind": "anki-import",
  "id": "imp_…",
  "source": {"format": "anki21b", "schema": 18, "collectionCreated": "2025-09-01T04:00:00Z", "filename": "Methods.apkg"},
  "summary": { … as above … },
  "decks": [{
    "id": "1795318240149",                 // Anki deck id (string)
    "name": "IB::Methods",                 // full Anki name, "::" for nesting
    "cardCount": 214, "reviewCount": 1930, "suggestedCourseId": "c-methods",
    "scheduler": {
      "fsrsEnabled": true,                 // null if the package doesn't say
      "fsrsParams": [0.212, 1.2931, …],    // the deck preset's FSRS parameters, or null
      "fsrsVersion": 6,                    // 6, 5 or 4: which parameter set that is
      "desiredRetention": 0.9,
      "learnStepsMinutes": [1, 10], "relearnStepsMinutes": [10],
      "newPerDay": 20, "reviewsPerDay": 200, "leechThreshold": 8, "configName": "Default"
    }
  }],
  "cards": [{
    "id": "57a4c06b-625f-5089-bea8-408fd4116648",   // UUIDv5 of (note GUID, card ordinal): stable across re-imports
    "deck": "1795318240149",
    "front": "Statement and Proof of the Cayley\\(-\\)Hamilton Theorem",
    "back": "<b>Statement:</b> if \\(\\chi_A(t) = …\\) then \\[\\chi_A(A) = 0.\\] <img src=\"diagram.png\">",
    "tags": ["cayley-hamilton"],                    // lower-cased Anki tags ("::" kept)
    "label": "Theorem",                             // Definition | Theorem | Practice | Synthesis | Other, from the front
    "lecture": 14,                                  // from a tag like L14 / Lecture14 / LA::L14, else null
    "flagged": true, "suspended": false,
    "origin": {
      "kind": "anki", "noteId": 1795318240212, "noteGuid": "G};A01]J3_", "cardId": 1795318240212, "ord": 0,
      "notetype": "Basic", "template": "Card 1", "deckName": "IB::Methods",
      "fields": {"Front": "…$…$…", "Back": "…"},   // raw Anki fields, untouched (for export back to Anki)
      "tags": ["cayley-hamilton"], "flag": 1
    },
    "anki": {                                        // Anki's own state: a cross-check for the app's FSRS replay
      "type": "review", "queue": "review", "due": 11, "dueDate": "2026-12-02",
      "intervalDays": 40, "easeFactor": 2.3, "reps": 9, "lapses": 1, "left": 0,
      "fsrs": {"stability": 31.2, "difficulty": 5.1, "desiredRetention": 0.9, "decay": 0.154, "lastReview": "…"}  // if Anki had FSRS on
    },
    "warnings": [],                                  // e.g. "back: unpaired $ left as is"
    "createdAt": "…", "updatedAt": "…"
  }],
  "reviews": [{
    "id": "22ef1bdb-d3e6-5b89-b630-6552473f0159",   // UUIDv5 of (GUID, ord, revlog id): re-imports de-duplicate
    "card": "57a4c06b-…",
    "t": "2026-09-23T03:30:40.395Z",
    "rating": 3,          // 1 Again, 2 Hard, 3 Good, 4 Easy; 0 = not a review (manual reschedule / forget)
    "ms": 41000,          // answer time
    "session": null,
    "kind": "learn",      // learn | review | relearn | filtered | manual | reschedule
    "source": "anki",
    "anki": {"revlogId": 1790134240395, "intervalDays": null, "intervalSeconds": 600,
             "lastIntervalDays": 0, "lastIntervalSeconds": null, "factor": 0, "type": 0}
  }],
  "media": [{"name": "diagram.png", "size": 69, "sha256": "7c36…", "referencedBy": ["57a4c06b-…"]}],
  "warnings": []
}
```

What the app does with it (DESIGN.md §4.8):

- **Cards:** front and back are the Anki template output with `{{FrontSide}}<hr id=answer>` removed from the back, plus the one approved mechanical fix: `$…$` → `\( … \)`, `$$…$$` → `\[ … \]` (and Anki's `[$]…[/$]`, `[$$]…[/$$]`). `\$` stays literal; an unpaired `$` is left alone and reported in `warnings`. HTML entities and markup are untouched. Cloze cards render the active deletion as `<b>[…]</b>` (or `<b>[hint]</b>`) on the front and `<b>answer</b>` on the back. Write accepted cards into the course's `cards.json`, keeping `origin`.
- **Reviews:** append them to the review log (e.g. `Reviews/anki-import/<yyyy-mm>.jsonl`, one JSON object per line exactly as given). FSRS replays them to get each card's state. Lines with `rating` 0 aren't reviews: a `manual` line with `intervalDays` 0 is Anki's *Forget* (reset to new); other `manual`/`reschedule` lines only moved the due date. `filtered` lines are reviews done in a filtered deck. Use `scheduler.fsrsParams` for the deck if present (DESIGN.md §4.6).
- **Media:** download each file from `/media/{name}` into `Courses/<course>/cards-media/`, and resolve `<img src="name">` against that folder. (The card sanitiser needs to allow `<img src>` pointing into `cards-media/` for imported cards.)
- **Re-import:** ids are deterministic, so importing the same deck again updates the same cards and the review ids de-duplicate.

### `GET /v1/imports/{import_id}/media/{name}`
One media file (raw bytes).

### `DELETE /v1/imports/{import_id}`
Deletes the result and media from the server once the app has stored them. Unclaimed results are purged after `MM_TRASH_DAYS`.

The same conversion runs offline: `mathsmaster-server import-apkg deck.apkg -o out.json --media ./media`.

## Claude jobs

Batch work that can take minutes to hours: card generation, deck enhancement, and one-shot explain / check / transcribe. Jobs queue (one at a time by default, to respect subscription limits), survive restarts, and always report progress.

Every job runs headless Claude Code (`claude-opus-5-5`, high effort) in a per-course workspace holding a fresh copy of the mirrored course folder. The prompt always carries the app adapter, the owner's `AI/card-guidelines.md` verbatim, the course's `ai-instructions.md` and an inventory of the course files; Claude opens what it needs. Output is checked (the guidelines' §8.2 delivery checks) and Claude is asked to fix failures before the job completes.

Prerequisites: `library.json`, the course folder and `AI/card-guidelines.md` must be in the mirror, otherwise the request fails with `409` (`library_not_mirrored`, `course_not_mirrored`, `guidelines_missing`).

### `POST /v1/jobs`

```json
{
  "kind": "generate_cards",
  "courseId": "c-la",
  "params": {"lectures": "13-16", "instructions": "focus on the proofs"},
  "attachments": []
}
```

| kind | params | attachments | result |
|---|---|---|---|
| `generate_cards` | `lectures?` ("13-16"), `documents?` (paths under the course folder), `instructions?` | optional | `{cards[], report}` |
| `enhance_cards` | `cardIds?` (default: whole deck), `instructions?` | optional | `{changes[], report}` |
| `explain` | `cardId` or `card`, `question?` | optional | `{html}` |
| `check_attempt` | `cardId` or `card`, `instructions?` | **required**: the attempt as an image | `{verdict, summary, html, issues[]}` |
| `transcribe` | `mode?`: `card` (default) \| `math` \| `text` | **required**: the handwriting image | `{html, unclear[]}` |

`card` is a card object (`{id, front, back, …}`) for cards not yet in the mirror. **Attachments** are `{"name": "attempt.png", "mediaType": "image/png", "data": "<base64>"}`; types `image/png`, `image/jpeg`, `image/heic`, `image/webp`, `application/pdf`, `text/plain`; at most 8, 25 MB each.

Returns `202` with the job object.

### `GET /v1/jobs/{job_id}`

```jsonc
{
  "id": "job_20261122T091403_ab12cd34",
  "kind": "generate_cards", "courseId": "c-la", "courseName": "Linear Algebra",
  "params": {"lectures": "13-16"}, "attachments": [],
  "status": "running",                    // queued | running | succeeded | failed | cancelled
  "queuePosition": null,                  // 1, 2, … while queued
  "createdAt": "…", "startedAt": "…", "finishedAt": null, "attempts": 1,
  "sessionId": "…",                       // the Claude Code session (for debugging)
  "progress": [{"t": "…", "text": "Reading course/Lecture notes/LA notes.pdf pp. 55-61"}],  // last 40 lines
  "result": null,                         // set when succeeded (shapes below)
  "checks": null,                         // {"passed": true, "problems": []} when succeeded
  "error": null,                          // {"code", "message"} when failed
  "usage": null,                          // {"costUsd", "durationMs", "numTurns"} as reported by Claude Code
  "device": "iPad · Playgrounds"
}
```

Poll every few seconds while the job is on screen (the last `progress` line is the status line). A job that was running when the server restarted is re-queued (`attempts` goes up).

If problems remain after the fix rounds, the job still succeeds with `checks.passed: false` and the problems listed (and per-card `lint`), so the Inbox can flag them rather than lose the work.

**Result shapes**

```jsonc
// generate_cards — the Inbox job (DESIGN.md §4.5). The app stores it as Inbox/jobs/<jobID>.json.
{"cards": [{"id": "<uuid assigned by the server>", "front": "…", "back": "…", "label": "Theorem", "lecture": 14,
            "source": {"document": "Lecture notes/LA notes.pdf", "page": 61}, "tags": [], "status": "new",
            "origin": {"kind": "claude", "job": "job_…"}, "lint": []}],
 "report": {"summary": "…", "possibleErrors": [{"document": "…", "page": 12, "text": "…"}],
            "unclear": [{"document": "…", "page": 3, "reading": "…", "cardIndex": 0}], "notDone": ["…"]}}

// enhance_cards — proposals shown as diffs
{"changes": [{"cardId": "…", "front": "<full new text, if changed>", "back": "…", "summary": "…",
              "original": {"front": "…", "back": "…"},
              "checks": {"back": {"additionsOnly": true, "insertions": [{"offset": 120, "text": "<br><b>Intuition:</b> …"}]}},
              "additionsOnly": true}],
 "report": {…}}

// explain / transcribe
{"html": "…"}                       // transcribe also has "unclear": [...]

// check_attempt
{"verdict": "minor_issues", "summary": "…", "html": "…", "issues": [{"quote": "…", "problem": "…", "suggestion": "…"}]}
```

`source.document` paths are relative to the course folder. `insertions[].offset` is a character offset into the new text; deleting each inserted span gives back the original exactly (the additions-only rule, guidelines §6.2). HTML in every result uses the card subset with MathJax `\( \)` / `\[ \]`.

### `GET /v1/jobs?status=&courseId=&limit=50`
Recent jobs, newest first, without `result`.

### `POST /v1/jobs/{job_id}/cancel`
Cancels a queued job, or stops a running one (the Claude process is killed). Returns the job.

## Claude threads

Every card has a thread, and every course has one (`threadId` = the card's id, or e.g. `course-<courseId>`; letters, digits, `-`, `_`, `.`). Each thread is one Claude Code session on the VPS, resumed for every message, so Claude remembers the conversation (DESIGN.md §5.3).

### `POST /v1/threads/{thread_id}`

```json
{
  "courseId": "c-la",
  "cardId": "57a4c06b-…",
  "message": "this step: why can we swap the sum and the integral?",
  "intent": "chat",
  "card": {"id": "57a4c06b-…", "front": "…", "back": "…"},
  "attachments": [{"name": "lasso.png", "mediaType": "image/png", "data": "…"}]
}
```

- `intent`: `chat` (default), `explain` (the *Explain* button) or `check_attempt` (*Check my attempt*: attach the handwriting).
- `card`: the card as the app has it now; send it whenever it may differ from the mirror. Omit `cardId` for a course thread.
- Pencil-written messages and lassoed regions go in `attachments` as images.

The response is `text/event-stream`:

```
event: run
data: {"runId": "run_…", "threadId": "57a4c06b-…", "sessionId": "…"}

event: status
data: {"text": "Reading course/Lecture notes/LA notes.pdf pp. 55-61"}

event: delta
data: {"text": "Because the series converges "}

event: done
data: {"runId": "run_…", "message": {…assistant message…}, "usage": {"costUsd": 0.12, "durationMs": 21000, "numTurns": 4}}
```

or, instead of `done`, `event: error` with `{"runId", "code", "message"}`. Each event has an `id:` (its sequence number). Comment lines (`: ping`) are heartbeats every 15 s.

The assistant message:

```jsonc
{
  "id": "run_…-a", "role": "assistant", "runId": "run_…", "at": "…",
  "text": "Because … \\( \\sum_n \\int f_n = \\int \\sum_n f_n \\) …",   // card HTML subset + MathJax
  "lint": [],
  "proposals": [{
    "id": "run_…-p1",
    "cardId": "57a4c06b-…",          // null = a new card
    "front": null, "back": "<full proposed back>", "label": null, "summary": "adds the dominated-convergence step",
    "original": {"front": "…", "back": "…"},
    "checks": {"back": {"additionsOnly": true, "insertions": [{"offset": 812, "text": "…"}]}},
    "additionsOnly": true,           // null for new cards
    "lint": []
  }]
}
```

Render `delta` text as it streams, then replace it with `message.text` on `done`. Proposals become *Apply* / *Keep talking* blocks; applying keeps the card id and review history and is stored as a revision. Write both the user's message and the reply into the library's `threads/<cardID>.jsonl`; that file is the user-facing record.

Only one message at a time per thread: a second POST while a reply is being written gets `409 thread_busy`.

**Dropped connections don't lose the reply.** The run continues on the server. Re-attach with `GET /v1/threads/{thread_id}/runs/{run_id}/events?after=<last event id>` (the run id is in the first `run` event and the `X-Run-Id` response header), or read the finished message from `GET /v1/threads/{thread_id}`.

### `GET /v1/threads/{thread_id}`

```json
{"id": "…", "courseId": "c-la", "cardId": "…", "createdAt": "…", "updatedAt": "…",
 "activeRunId": null, "messages": [{"id": "run_…-u", "role": "user", "text": "…", "intent": "chat", "attachments": ["01-lasso.png"], "at": "…", "runId": "run_…"}, {…assistant…}]}
```

A failed reply appears as an assistant message with `error: {code, message}` and empty `text`.

### `GET /v1/threads/{thread_id}/runs/{run_id}/events?after=-1`
Replays a run's events after the given sequence number, then follows it live until it ends. Runs are kept for an hour after they finish.

### `DELETE /v1/threads/{thread_id}`
Forgets the server's session for the thread; the next message starts a fresh Claude session (with full context again). The app's `threads/*.jsonl` is unaffected.

If a Claude Code session has been lost on the VPS (e.g. after moving servers), the server notices, starts a new session and includes the earlier messages of the thread.

## Errors

| Status | Code | Meaning |
|---|---|---|
| 400 | `bad_path` | path rejected (see Backup mirror) |
| 400 | `hash_mismatch` | body doesn't match `X-Content-SHA256` |
| 400 | `not_a_package`, `corrupt_package`, `empty_upload` | Anki upload problems (also appear as an import's `error`) |
| 400 | `bad_attachment`, `too_many_attachments`, `attachment_required`, `card_required`, `empty_message`, `bad_intent`, `bad_thread_id`, `bad_course_id`, `bad_kind` | request problems |
| 401 | `unauthorized` | missing/invalid/revoked token |
| 404 | `not_found`, `not_ready`, `unknown_course` | |
| 409 | `library_not_mirrored`, `course_not_mirrored`, `guidelines_missing` | sync first: Claude needs these files in the mirror |
| 409 | `path_conflict`, `thread_busy`, `course_mismatch` | |
| 413 | `too_large` | over `MM_MAX_UPLOAD_MB` (files/packages) or 25 MB (attachments) |
| 422 | `invalid_request` | JSON body doesn't match the schema |

Job/thread failure codes (in `job.error.code` or the `error` event): `claude_auth` (Claude Code isn't signed in on the VPS), `claude_limit` (subscription usage limit reached: try later), `claude_missing` (Claude Code not installed), `timeout`, `bad_output` (no valid result file after the fix rounds), `claude_error`, `cancelled`, `interrupted`, `internal_error`.

## Limits

| | Default | Env var |
|---|---|---|
| File / package upload | 1024 MB | `MM_MAX_UPLOAD_MB` |
| Attachments | 8 per request, 25 MB each | — |
| Concurrent jobs | 1 | `MM_JOB_CONCURRENCY` |
| Concurrent thread replies | 2 | `MM_THREAD_CONCURRENCY` |
| Job timeout | 6 h | `MM_JOB_TIMEOUT_S` |
| Thread reply timeout | 30 min | `MM_THREAD_TIMEOUT_S` |
| Fix rounds after failed checks | 2 | `MM_FIX_ROUNDS` |
| Trash / unclaimed import retention | 30 days | `MM_TRASH_DAYS` |

## Not yet

Planned, not built in v1 (DESIGN.md roadmap):

- MathJax compile check and SVG → image rendering in the validator (the lint covers delimiters, braces, environments and tags meanwhile).
- `POST /v1/fsrs/optimize` (Phase 5) and Anki export (`.apkg`/TSV).
- Restoring from a nightly snapshot through the API (snapshots are restored on the VPS with restic; the API restores the current mirror).
- Claude can't read PencilKit `.drawing` files. Ink that matters for a request has to arrive as an image attachment; for whole-course context, the app could also mirror a flattened PDF/PNG of inked pages.
