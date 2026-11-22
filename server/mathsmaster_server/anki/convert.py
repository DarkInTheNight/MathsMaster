"""Convert an Anki package into MathsMaster cards + review history (DESIGN.md §4.1, §4.8).

Output (see server/API.md, "Anki import result"):
  decks[]   one per Anki deck that has cards, with its FSRS parameters if set
  cards[]   app cards: front/back HTML + MathJax, tags, flags, origin = anki
  reviews[] the full revlog as app review-log lines, so FSRS can recompute state
  media[]   media files (written next to the result, for cards-media/)

Card and review ids are UUIDv5s derived from the note GUID, card ordinal and
revlog id, so importing the same deck twice yields the same ids: a re-import
updates cards instead of duplicating them, and reviews de-duplicate.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..util import iso_from_ms
from .collection import CollectionInfo, Deck, read_collection
from .mathfix import fix_math
from .package import AnkiImportError, open_package
from .template import answer_only, cloze_numbers, render

# Fixed namespace so ids are stable across servers and re-imports.
NAMESPACE = uuid.UUID("6f1c7a52-3b0e-4f8e-9a4c-2d1b5e7c9a10")

REVLOG_KIND = {0: "learn", 1: "review", 2: "relearn", 3: "filtered", 4: "manual", 5: "reschedule"}
CARD_TYPE = {0: "new", 1: "learning", 2: "review", 3: "relearning"}
QUEUE = {0: "new", 1: "learning", 2: "review", 3: "day-learning", 4: "preview", -1: "suspended", -2: "buried", -3: "buried"}

_IMG_RE = re.compile(r"""<img[^>]*?\ssrc\s*=\s*["']?([^"' >]+)""", re.I)
_SOUND_RE = re.compile(r"\[sound:([^\]]+)\]")
_LECTURE_TAG = re.compile(r"(?:^|::)(?:l|lec|lecture)[ _-]?(\d{1,2})$", re.I)


def card_uuid(guid: str, ord_: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"anki-card:{guid}:{ord_}"))


def review_uuid(guid: str, ord_: int, revlog_id: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"anki-revlog:{guid}:{ord_}:{revlog_id}"))


def label_for(front: str) -> str:
    """Card label from the front, per the guidelines' front patterns (DESIGN.md §4.1)."""
    text = re.sub(r"<[^>]*>", "", front).strip().lower()
    if text.startswith(("definition of", "definitions of", "definition:")):
        return "Definition"
    if text.startswith(("statement and proof", "statement of", "proof of", "theorem")):
        return "Theorem"
    if text.startswith("practice"):
        return "Practice"
    if text.startswith(("synthesis", "connections between", "comparison of", "compare")):
        return "Synthesis"
    return "Other"


def _date_from_day(crt: int, day: int) -> str:
    return datetime.fromtimestamp(crt + day * 86400, timezone.utc).strftime("%Y-%m-%d")


def _schedule_snapshot(row: sqlite3.Row, info: CollectionInfo) -> dict:
    """Anki's own scheduling state for the card, as a cross-check for the app's FSRS replay."""
    queue = row["queue"]
    due = row["odue"] if row["odid"] else row["due"]
    snap: dict = {
        "type": CARD_TYPE.get(row["type"], str(row["type"])),
        "queue": QUEUE.get(queue, str(queue)),
        "due": due,
        "intervalDays": row["ivl"],
        "easeFactor": row["factor"] / 1000 if row["factor"] else None,
        "reps": row["reps"],
        "lapses": row["lapses"],
        "left": row["left"],
    }
    if row["type"] == 0:
        snap["newPosition"] = due
    elif queue == 1 or (queue in (-1, -2, -3) and row["type"] in (1, 3) and due > 1_000_000_000):
        snap["dueAt"] = datetime.fromtimestamp(due, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif row["type"] in (2, 3) or queue == 3:
        snap["dueDate"] = _date_from_day(info.crt, due)
    data = row["data"] or ""
    if data.startswith("{"):
        try:
            d = json.loads(data)
        except json.JSONDecodeError:
            d = {}
        if "s" in d and "d" in d:
            snap["fsrs"] = {
                "stability": d["s"],
                "difficulty": d["d"],
                "desiredRetention": d.get("dr"),
                "decay": d.get("decay"),
                "lastReview": (
                    datetime.fromtimestamp(d["lrt"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    if d.get("lrt")
                    else None
                ),
            }
    return snap


def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def suggest_course(deck_name: str, courses: list[dict]) -> str | None:
    """Match an Anki deck to a library course by name (the user confirms in the app)."""
    leaf = _norm_name(deck_name.split("::")[-1])
    full = _norm_name(deck_name)
    best: tuple[int, str] | None = None
    for c in courses:
        name = _norm_name(c.get("name", ""))
        if not name or not c.get("id"):
            continue
        if name == leaf:
            score = 3
        elif name in full or (leaf and leaf in name):
            score = 2
        else:
            continue
        if not best or score > best[0]:
            best = (score, c["id"])
    return best[1] if best else None


def convert_package(path: Path, workdir: Path, media_out: Path | None = None, courses: list[dict] | None = None) -> dict:
    pkg = open_package(path, workdir)
    db = sqlite3.connect(f"file:{pkg.db_path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        try:
            info = read_collection(db)
        except sqlite3.DatabaseError as exc:
            raise AnkiImportError("corrupt_package", f"can't read the collection: {exc}") from exc
        return _convert(pkg, db, info, media_out, courses or [])
    finally:
        db.close()


def _convert(pkg, db: sqlite3.Connection, info: CollectionInfo, media_out: Path | None, courses: list[dict]) -> dict:
    warnings: list[str] = []
    cards_out: list[dict] = []
    reviews_out: list[dict] = []
    deck_counts: dict[int, int] = {}
    card_id_map: dict[int, tuple[str, str, int]] = {}  # anki cid -> (uuid, guid, ord)
    media_refs: dict[str, list[str]] = {}

    rows = db.execute(
        """select c.id cid, c.nid, c.did, c.ord, c.mod cmod, c.type, c.queue, c.due, c.ivl, c.factor,
                  c.reps, c.lapses, c.left, c.odue, c.odid, c.flags, c.data,
                  n.guid, n.mid, n.mod nmod, n.tags, n.flds
             from cards c join notes n on n.id = c.nid
            order by c.nid, c.ord"""
    ).fetchall()

    for row in rows:
        nt = info.notetypes.get(row["mid"])
        if nt is None:
            warnings.append(f"card {row['cid']}: unknown notetype {row['mid']}, skipped")
            continue
        values = row["flds"].split("\x1f")
        fields = {name: (values[i] if i < len(values) else "") for i, name in enumerate(nt.fields)}
        home_did = row["odid"] or row["did"]
        deck: Deck | None = info.decks.get(home_did)
        deck_name = deck.name if deck else f"Deck {home_did}"
        tags_raw = row["tags"].split()

        if nt.kind == "cloze":
            tmpl = nt.templates[0] if nt.templates else None
        else:
            tmpl = nt.templates[row["ord"]] if row["ord"] < len(nt.templates) else None
        if tmpl is None:
            warnings.append(f"card {row['cid']}: notetype {nt.name!r} has no template {row['ord']}, skipped")
            continue

        extra = {
            "Tags": " ".join(tags_raw),
            "Deck": deck_name,
            "Subdeck": deck_name.split("::")[-1],
            "Type": nt.name,
            "Card": tmpl.name,
        }
        front = render(tmpl.qfmt, fields, ord_=row["ord"], side="q", extra=extra).strip()
        back = render(tmpl.afmt, fields, ord_=row["ord"], side="a", extra={**extra, "FrontSide": ""})
        back = answer_only(back)
        if nt.kind == "cloze" and (row["ord"] + 1) not in set().union(*(cloze_numbers(v) for v in fields.values())):
            warnings.append(f"card {row['cid']}: cloze c{row['ord'] + 1} not found in note")

        card_warnings: list[str] = []
        front, w1 = fix_math(front)
        back, w2 = fix_math(back)
        card_warnings += [f"front: {w}" for w in w1] + [f"back: {w}" for w in w2]

        cid = card_uuid(row["guid"], row["ord"])
        card_id_map[row["cid"]] = (cid, row["guid"], row["ord"])
        deck_counts[home_did] = deck_counts.get(home_did, 0) + 1

        for value in fields.values():
            for ref in _IMG_RE.findall(value) + _SOUND_RE.findall(value):
                media_refs.setdefault(ref, [])
                if cid not in media_refs[ref]:
                    media_refs[ref].append(cid)

        lecture = None
        for t in tags_raw:
            m = _LECTURE_TAG.search(t)
            if m:
                lecture = int(m.group(1))
                break

        created = iso_from_ms(row["nid"])  # note ids are creation timestamps (ms)
        updated = datetime.fromtimestamp(max(row["cmod"], row["nmod"]), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cards_out.append(
            {
                "id": cid,
                "deck": str(home_did),
                "front": front,
                "back": back,
                "tags": [t.lower() for t in tags_raw],
                "label": label_for(front),
                "lecture": lecture,
                "flagged": bool(row["flags"] & 7),
                "suspended": row["queue"] == -1,
                "origin": {
                    "kind": "anki",
                    "noteId": row["nid"],
                    "noteGuid": row["guid"],
                    "cardId": row["cid"],
                    "ord": row["ord"],
                    "notetype": nt.name,
                    "template": tmpl.name,
                    "deckName": deck_name,
                    "fields": fields,
                    "tags": tags_raw,
                    "flag": row["flags"] & 7,
                },
                "anki": _schedule_snapshot(row, info),
                "warnings": card_warnings,
                "createdAt": created,
                "updatedAt": updated,
            }
        )

    # ---- review history ---------------------------------------------------
    for r in db.execute("select id, cid, ease, ivl, lastIvl, factor, time, type from revlog order by id"):
        mapped = card_id_map.get(r["cid"])
        if not mapped:
            continue  # review of a card not in this package (deleted card)
        cid, guid, ord_ = mapped
        reviews_out.append(
            {
                "id": review_uuid(guid, ord_, r["id"]),
                "card": cid,
                "t": iso_from_ms(r["id"]),
                "rating": r["ease"],
                "ms": r["time"],
                "session": None,
                "kind": REVLOG_KIND.get(r["type"], str(r["type"])),
                "source": "anki",
                "anki": {
                    "revlogId": r["id"],
                    "intervalDays": r["ivl"] if r["ivl"] >= 0 else None,
                    "intervalSeconds": -r["ivl"] if r["ivl"] < 0 else None,
                    "lastIntervalDays": r["lastIvl"] if r["lastIvl"] >= 0 else None,
                    "lastIntervalSeconds": -r["lastIvl"] if r["lastIvl"] < 0 else None,
                    "factor": r["factor"],
                    "type": r["type"],
                },
            }
        )

    # ---- decks ------------------------------------------------------------
    decks_out = []
    for did, count in sorted(deck_counts.items(), key=lambda kv: info.decks.get(kv[0], Deck(kv[0], "", None, False)).name):
        deck = info.decks.get(did)
        conf = info.configs.get(deck.config_id) if deck and deck.config_id is not None else None
        dr = (deck.desired_retention if deck and deck.desired_retention else None) or (conf.desired_retention if conf else None)
        name = deck.name if deck else f"Deck {did}"
        decks_out.append(
            {
                "id": str(did),
                "name": name,
                "cardCount": count,
                "reviewCount": 0,
                "suggestedCourseId": suggest_course(name, courses),
                "scheduler": {
                    "fsrsEnabled": info.fsrs_enabled,
                    "fsrsParams": conf.fsrs_params if conf and conf.fsrs_params else None,
                    "fsrsVersion": conf.fsrs_version if conf and conf.fsrs_params else None,
                    "desiredRetention": dr,
                    "learnStepsMinutes": conf.learn_steps_min if conf else None,
                    "relearnStepsMinutes": conf.relearn_steps_min if conf else None,
                    "newPerDay": conf.new_per_day if conf else None,
                    "reviewsPerDay": conf.reviews_per_day if conf else None,
                    "leechThreshold": conf.leech_threshold if conf else None,
                    "configName": conf.name if conf else None,
                },
            }
        )
    by_deck = {d["id"]: d for d in decks_out}
    card_deck = {c["id"]: c["deck"] for c in cards_out}
    for rv in reviews_out:
        d = by_deck.get(card_deck.get(rv["card"], ""))
        if d:
            d["reviewCount"] += 1

    # ---- media ------------------------------------------------------------
    media_out_list = []
    for name in sorted(pkg.media):
        if "/" in name or "\\" in name or name in (".", "..") or name.startswith("."):
            warnings.append(f"media {name!r}: unsafe file name, skipped")
            continue
        try:
            data = pkg.read_media(name)
        except AnkiImportError as exc:
            warnings.append(exc.message)
            continue
        if media_out is not None:
            media_out.mkdir(parents=True, exist_ok=True)
            (media_out / name).write_bytes(data)
        media_out_list.append(
            {
                "name": name,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "referencedBy": media_refs.get(name, []),
            }
        )
    missing = sorted(set(media_refs) - set(pkg.media))
    for name in missing:
        warnings.append(f"media {name!r} is referenced by a card but missing from the package")

    return {
        "schemaVersion": 1,
        "kind": "anki-import",
        "source": {
            "format": pkg.format,
            "schema": info.schema,
            "collectionCreated": datetime.fromtimestamp(info.crt, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "summary": {
            "decks": len(decks_out),
            "cards": len(cards_out),
            "notes": len({c["origin"]["noteId"] for c in cards_out}),
            "reviews": len(reviews_out),
            "media": len(media_out_list),
            "suspended": sum(1 for c in cards_out if c["suspended"]),
            "cardsWithWarnings": sum(1 for c in cards_out if c["warnings"]),
        },
        "decks": decks_out,
        "cards": cards_out,
        "reviews": reviews_out,
        "media": media_out_list,
        "warnings": warnings,
    }
