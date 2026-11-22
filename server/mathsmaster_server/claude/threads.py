"""Card and course threads (DESIGN.md §5.3): one resumable Claude Code session per thread.

POST /v1/threads/{id} starts a *run* and streams its events over SSE. The run
itself is a background task writing into an in-memory event buffer, so a
dropped connection (an iPad going to sleep) doesn't kill the reply: the app can
re-attach with GET /v1/threads/{id}/runs/{runId}/events?after=N, or just read
the finished message from GET /v1/threads/{id}.

The library's threads/<cardID>.jsonl stays the app's record of the
conversation; the server keeps its own small state file per thread (session id,
messages) so it can resume the right Claude Code session.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import time
import uuid
from dataclasses import dataclass, field

from ..config import Settings
from ..util import atomic_write_json, new_id, now_iso, read_json, valid_id
from . import prompts
from .jobs import RunFailed
from .runner import ClaudeRunner, RunRequest
from .validate import additions_only, lint_html
from .workspace import ClaudeRequestError, Workspaces, save_attachments

log = logging.getLogger("mathsmaster.threads")
RUN_KEEP_S = 3600


@dataclass
class Run:
    id: str
    thread_id: str
    events: list[dict] = field(default_factory=list)
    done: bool = False
    finished_at: float | None = None
    cond: asyncio.Condition = field(default_factory=asyncio.Condition)

    async def emit(self, type_: str, data: dict) -> None:
        async with self.cond:
            self.events.append({"seq": len(self.events), "type": type_, "data": data})
            if type_ in ("done", "error"):
                self.done = True
                self.finished_at = time.time()
            self.cond.notify_all()

    async def follow(self, after: int = -1, heartbeat_s: float = 15.0):
        """Yield events with seq > after, live, until the run is done. None = heartbeat."""
        i = after + 1
        while True:
            async with self.cond:
                while i >= len(self.events) and not self.done:
                    try:
                        await asyncio.wait_for(self.cond.wait(), timeout=heartbeat_s)
                    except asyncio.TimeoutError:
                        break
                batch = self.events[i:]
                finished = self.done
            if not batch and not finished:
                yield None
                continue
            for ev in batch:
                yield ev
            i += len(batch)
            if finished and i >= len(self.events):
                return


class ThreadManager:
    def __init__(self, settings: Settings, workspaces: Workspaces, runner: ClaudeRunner):
        self.settings = settings
        self.workspaces = workspaces
        self.runner = runner
        self.dir = settings.data_dir / "threads"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.runs: dict[str, Run] = {}
        self._busy: dict[str, str] = {}  # thread id -> run id
        self._sem = asyncio.Semaphore(settings.thread_concurrency)
        self._tasks: set[asyncio.Task] = set()

    async def stop(self) -> None:
        for t in list(self._tasks):
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    # ------------------------------------------------------------- state
    def _path(self, thread_id: str):
        return self.dir / f"{thread_id}.json"

    def load(self, thread_id: str) -> dict | None:
        return read_json(self._path(thread_id), None)

    def _save(self, state: dict) -> None:
        atomic_write_json(self._path(state["id"]), state)

    def public(self, state: dict) -> dict:
        return {
            "id": state["id"],
            "courseId": state["courseId"],
            "cardId": state.get("cardId"),
            "createdAt": state["createdAt"],
            "updatedAt": state["updatedAt"],
            "activeRunId": self._busy.get(state["id"]),
            "messages": state["messages"],
        }

    def forget(self, thread_id: str) -> bool:
        if thread_id in self._busy:
            raise ClaudeRequestError(409, "thread_busy", "a reply is still being written")
        try:
            self._path(thread_id).unlink()
            return True
        except FileNotFoundError:
            return False

    def _gc_runs(self) -> None:
        now = time.time()
        for rid, run in list(self.runs.items()):
            if run.done and run.finished_at and now - run.finished_at > RUN_KEEP_S:
                del self.runs[rid]

    # ------------------------------------------------------------- start a run
    def start(
        self,
        thread_id: str,
        *,
        course_id: str,
        card_id: str | None,
        message: str,
        intent: str,
        card: dict | None,
        attachments: list[dict],
        device: str | None,
    ) -> Run:
        if not valid_id(thread_id):
            raise ClaudeRequestError(400, "bad_thread_id", "thread id has invalid characters")
        if intent not in prompts.INTENTS:
            raise ClaudeRequestError(400, "bad_intent", f"intent must be one of {', '.join(prompts.INTENTS)}")
        if not message.strip() and not attachments and intent == "chat":
            raise ClaudeRequestError(400, "empty_message", "send some text or an attachment")
        if intent == "check_attempt" and not attachments:
            raise ClaudeRequestError(400, "attachment_required", "check_attempt needs the attempt as an image")
        if thread_id in self._busy:
            raise ClaudeRequestError(409, "thread_busy", "a reply is still being written in this thread")
        self.workspaces.check(course_id)
        self._gc_runs()

        state = self.load(thread_id)
        if state and state["courseId"] != course_id:
            raise ClaudeRequestError(409, "course_mismatch", "this thread belongs to another course")
        if not state:
            state = {
                "id": thread_id,
                "courseId": course_id,
                "cardId": card_id,
                "sessionId": str(uuid.uuid4()),
                "sessionStarted": False,
                "contextHash": None,
                "createdAt": now_iso(),
                "updatedAt": now_iso(),
                "messages": [],
            }
        run = Run(new_id("run"), thread_id)
        # Attachments are decoded now, so a bad one fails the request rather than the stream.
        staged = self.settings.data_dir / "uploads" / run.id
        names = save_attachments(attachments, staged) if attachments else []
        state["messages"].append(
            {"id": run.id + "-u", "role": "user", "text": message, "intent": intent,
             "attachments": names, "at": now_iso(), "runId": run.id, "device": device}
        )
        state["updatedAt"] = now_iso()
        self._save(state)
        self._busy[thread_id] = run.id
        self.runs[run.id] = run
        task = asyncio.create_task(self._execute(state, run, message, intent, card, card_id, names))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return run

    async def _execute(self, state, run: Run, message, intent, card, card_id, names) -> None:
        reply_parts: list[str] = []
        staged = self.settings.data_dir / "uploads" / run.id
        try:
            await run.emit("run", {"runId": run.id, "threadId": state["id"], "sessionId": state["sessionId"]})
            async with self._sem:
                await run.emit("status", {"text": "Syncing the course files"})
                ws = await asyncio.to_thread(self.workspaces.prepare, state["courseId"])
                att_dir, out_dir = ws.run_dirs(run.id)
                for name in names:
                    shutil.copy2(staged / name, att_dir / name)
                cards = ws.cards()
                current = card or (cards.get(card_id) if card_id else None)
                ctx_hash = ws.context_hash(prompts.adapter_text())

                async def attempt(history: list[dict] | None) -> dict:
                    include = not state["sessionStarted"] or state.get("contextHash") != ctx_hash
                    prompt = prompts.thread_prompt(
                        ws=ws, run_id=run.id, include_context=include, intent=intent, message=message,
                        card=current, card_id=card_id, attachments=names, history=history,
                    )
                    req = RunRequest(
                        prompt=prompt, cwd=ws.root, session_id=state["sessionId"],
                        resume=state["sessionStarted"], model=self.settings.claude_model,
                        tools=self.settings.claude_tools, effort=self.settings.claude_effort_threads,
                        timeout_s=self.settings.thread_timeout_s, extra_args=self.settings.claude_extra_args,
                    )
                    result = None
                    async for ev in self.runner.run(req):
                        if ev.type == "session" and not state["sessionStarted"]:
                            state["sessionStarted"] = True
                            self._save(state)
                        elif ev.type == "status":
                            await run.emit("status", ev.data)
                        elif ev.type == "delta":
                            reply_parts.append(ev.data.get("text", ""))
                            await run.emit("delta", ev.data)
                        elif ev.type == "result":
                            result = ev.data
                        elif ev.type == "error":
                            raise RunFailed(ev.data.get("code", "claude_error"), ev.data.get("message", "Claude failed"))
                    if result is None:
                        raise RunFailed("claude_error", "Claude Code produced no result")
                    if result.get("isError"):
                        raise RunFailed(result.get("code") or "claude_error", result.get("text") or "Claude reported an error")
                    state["sessionStarted"] = True
                    state["contextHash"] = ctx_hash
                    return result

                try:
                    result = await attempt(None)
                except RunFailed as exc:
                    if exc.code != "session_not_found":
                        raise
                    # The Claude Code session is gone (e.g. moved servers): start a new one with the history.
                    await run.emit("status", {"text": "Starting a fresh session"})
                    state["sessionId"] = str(uuid.uuid4())
                    state["sessionStarted"] = False
                    reply_parts.clear()
                    result = await attempt(state["messages"][:-1])

                text = result.get("text") or "".join(reply_parts)
                proposals = self._proposals(out_dir, cards, card, card_id)
                msg = {
                    "id": run.id + "-a", "role": "assistant", "text": text, "at": now_iso(), "runId": run.id,
                    "proposals": proposals, "lint": lint_html(text),
                }
                state["messages"].append(msg)
                state["updatedAt"] = now_iso()
                self._save(state)
                await run.emit("done", {"runId": run.id, "message": msg,
                                        "usage": {k: result.get(k) for k in ("costUsd", "durationMs", "numTurns")}})
        except RunFailed as exc:
            await self._fail(state, run, exc.code, exc.message)
        except ClaudeRequestError as exc:
            await self._fail(state, run, exc.code, exc.message)
        except asyncio.CancelledError:
            await self._fail(state, run, "cancelled", "the server is shutting down")
            raise
        except Exception as exc:  # pragma: no cover - defensive
            log.exception("thread run %s crashed", run.id)
            await self._fail(state, run, "internal_error", str(exc))
        finally:
            self._busy.pop(state["id"], None)
            shutil.rmtree(staged, ignore_errors=True)

    async def _fail(self, state: dict, run: Run, code: str, message: str) -> None:
        state["messages"].append(
            {"id": run.id + "-a", "role": "assistant", "text": "", "at": now_iso(), "runId": run.id,
             "error": {"code": code, "message": message}}
        )
        state["updatedAt"] = now_iso()
        self._save(state)
        await run.emit("error", {"runId": run.id, "code": code, "message": message})

    @staticmethod
    def _proposals(out_dir, cards: dict, card: dict | None, card_id: str | None) -> list[dict]:
        path = out_dir / "proposals.json"
        if not path.is_file():
            return []
        try:
            raw = json.loads(path.read_text("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return [{"error": "proposals.json was not valid JSON"}]
        if isinstance(raw, dict):
            raw = raw.get("proposals", [raw])
        out = []
        for i, p in enumerate(raw if isinstance(raw, list) else []):
            if not isinstance(p, dict):
                continue
            target = p.get("cardId")
            if target and card and target == card_id:
                orig = card  # the app sent the card as it is now (may not be synced yet)
            else:
                orig = cards.get(target) or {}
            prop = {
                "id": f"{out_dir.parent.name}-p{i + 1}",
                "cardId": target,
                "front": p.get("front"),
                "back": p.get("back"),
                "label": p.get("label"),
                "summary": p.get("summary", ""),
                "lint": [],
                "checks": {},
            }
            ok = True
            for fld in ("front", "back"):
                if isinstance(p.get(fld), str):
                    prop["lint"] += [f"{fld}: {x}" for x in lint_html(p[fld])]
                    if target:
                        res = additions_only(orig.get(fld, ""), p[fld])
                        prop["checks"][fld] = res
                        ok = ok and res["additionsOnly"]
            prop["additionsOnly"] = ok if target else None
            if target:
                prop["original"] = {k: orig.get(k) for k in ("front", "back")}
            out.append(prop)
        return out
