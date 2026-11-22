"""Claude batch jobs (DESIGN.md §5.5, §7.7): queued, persisted, validated, retried.

A job runs `claude -p` in the course workspace with the full context prompt,
reads the JSON Claude wrote to runs/<id>/out/result.json, runs the delivery
checks, and resumes the same session to fix failures (MM_FIX_ROUNDS times)
before marking the job done. Jobs survive restarts: one that was running when
the service stopped is re-queued.

Status: queued -> running -> succeeded | failed | cancelled
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import uuid
from pathlib import Path
from typing import Callable

from ..config import Settings
from ..util import atomic_write_json, new_id, now_iso, read_json
from . import prompts
from .runner import ClaudeRunner, RunEvent, RunRequest
from .validate import additions_only, check_result, lint_html
from .workspace import ClaudeRequestError, Workspace, Workspaces, save_attachments

log = logging.getLogger("mathsmaster.jobs")

ACTIVE = ("queued", "running")
MAX_PROGRESS = 40


class RunFailed(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


async def run_claude(runner: ClaudeRunner, req: RunRequest, on_event: Callable[[RunEvent], None]) -> dict:
    """Drive one Claude run to its result event; raise RunFailed on error."""
    result: dict | None = None
    async for ev in runner.run(req):
        on_event(ev)
        if ev.type == "result":
            result = ev.data
        elif ev.type == "error":
            raise RunFailed(ev.data.get("code", "claude_error"), ev.data.get("message", "Claude failed"))
    if result is None:
        raise RunFailed("claude_error", "Claude Code produced no result")
    if result.get("isError"):
        raise RunFailed(result.get("code") or "claude_error", result.get("text") or "Claude reported an error")
    return result


def decorate_result(kind: str, data: dict, ws: Workspace, job_id: str) -> dict:
    """Give generated cards ids/origin, and annotate edits with the additions-only check."""
    if kind == "generate_cards":
        for card in data.get("cards", []):
            if isinstance(card, dict):
                card["id"] = str(uuid.uuid4())
                card["origin"] = {"kind": "claude", "job": job_id}
                card["lint"] = lint_html(card.get("front", "")) + lint_html(card.get("back", ""))
    elif kind == "enhance_cards":
        existing = ws.cards()
        for ch in data.get("changes", []):
            if not isinstance(ch, dict):
                continue
            orig = existing.get(ch.get("cardId"), {})
            checks = {}
            ok = True
            for field in ("front", "back"):
                if isinstance(ch.get(field), str):
                    res = additions_only(orig.get(field, ""), ch[field])
                    checks[field] = res
                    ok = ok and res["additionsOnly"]
            ch["original"] = {k: orig.get(k) for k in ("front", "back")}
            ch["checks"] = checks
            ch["additionsOnly"] = ok
    return data


class JobManager:
    def __init__(self, settings: Settings, workspaces: Workspaces, runner: ClaudeRunner):
        self.settings = settings
        self.workspaces = workspaces
        self.runner = runner
        self.dir = settings.data_dir / "jobs"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.uploads = settings.data_dir / "uploads"
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._jobs: dict[str, dict] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._workers: list[asyncio.Task] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    # ------------------------------------------------------------- lifecycle
    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        for path in sorted(self.dir.glob("*.json")):
            job = read_json(path, None)
            if not isinstance(job, dict) or "id" not in job:
                continue
            self._jobs[job["id"]] = job
            if job["status"] in ACTIVE:
                job["status"] = "queued"
                job["attempts"] = job.get("attempts", 0)
                self._progress(job, "Re-queued after a server restart" if job.get("startedAt") else "Queued")
                self._save(job)
                await self._queue.put(job["id"])
        for _ in range(self.settings.job_concurrency):
            self._workers.append(asyncio.create_task(self._worker()))

    async def stop(self) -> None:
        for t in self._workers:
            t.cancel()
        for t in list(self._tasks.values()):
            t.cancel()
        await asyncio.gather(*self._workers, *self._tasks.values(), return_exceptions=True)

    # ------------------------------------------------------------- api
    def create(self, *, kind: str, course_id: str, params: dict, attachments: list[dict], device: str | None) -> dict:
        if kind not in prompts.JOB_KINDS:
            raise ClaudeRequestError(400, "bad_kind", f"kind must be one of {', '.join(prompts.JOB_KINDS)}")
        course = self.workspaces.check(course_id)
        if kind in ("check_attempt", "transcribe") and not attachments:
            raise ClaudeRequestError(400, "attachment_required", f"{kind} needs an image attachment")
        if kind in ("explain", "check_attempt") and not (params.get("cardId") or params.get("card")):
            raise ClaudeRequestError(400, "card_required", f"{kind} needs params.cardId (or params.card)")
        job_id = new_id("job")
        names = save_attachments(attachments, self.uploads / job_id) if attachments else []
        job = {
            "id": job_id,
            "kind": kind,
            "courseId": course_id,
            "courseName": course.name,
            "params": params,
            "attachments": names,
            "status": "queued",
            "createdAt": now_iso(),
            "startedAt": None,
            "finishedAt": None,
            "attempts": 0,
            "sessionId": None,
            "progress": [],
            "result": None,
            "checks": None,
            "error": None,
            "usage": None,
            "device": device,
        }
        self._progress(job, "Queued")
        self._jobs[job_id] = job
        self._save(job)
        # create() may run in a worker thread (attachment decoding); asyncio.Queue isn't thread-safe.
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, job_id)
        else:
            self._queue.put_nowait(job_id)
        return job

    def get(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)

    def list(self, status: str | None = None, course_id: str | None = None, limit: int = 50) -> list[dict]:
        jobs = sorted(self._jobs.values(), key=lambda j: j["createdAt"], reverse=True)
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        if course_id:
            jobs = [j for j in jobs if j["courseId"] == course_id]
        return jobs[:limit]

    def queue_position(self, job_id: str) -> int | None:
        queued = sorted((j for j in self._jobs.values() if j["status"] == "queued"), key=lambda j: j["createdAt"])
        for i, j in enumerate(queued):
            if j["id"] == job_id:
                return i + 1
        return None

    def cancel(self, job_id: str) -> dict | None:
        job = self._jobs.get(job_id)
        if not job:
            return None
        if job["status"] == "queued":
            self._finish(job, "cancelled")
        elif job["status"] == "running" and job_id in self._tasks:
            self._tasks[job_id].cancel()
        return job

    def counts(self) -> dict:
        out = {"queued": 0, "running": 0}
        for j in self._jobs.values():
            if j["status"] in out:
                out[j["status"]] += 1
        return out

    # ------------------------------------------------------------- internals
    def _save(self, job: dict) -> None:
        atomic_write_json(self.dir / f"{job['id']}.json", job)

    def _progress(self, job: dict, text: str) -> None:
        job["progress"].append({"t": now_iso(), "text": text})
        del job["progress"][:-MAX_PROGRESS]

    def _finish(self, job: dict, status: str, error: dict | None = None) -> None:
        job["status"] = status
        job["finishedAt"] = now_iso()
        job["error"] = error
        self._progress(job, {"succeeded": "Done", "failed": "Failed", "cancelled": "Cancelled"}.get(status, status))
        self._save(job)
        shutil.rmtree(self.uploads / job["id"], ignore_errors=True)

    async def _worker(self) -> None:
        while True:
            job_id = await self._queue.get()
            job = self._jobs.get(job_id)
            if not job or job["status"] != "queued":
                continue
            task = asyncio.create_task(self._run(job))
            self._tasks[job_id] = task
            try:
                await task
            except asyncio.CancelledError:
                if job["status"] == "running":
                    self._finish(job, "cancelled")
                if asyncio.current_task().cancelling():  # the worker itself is stopping
                    raise
            except Exception as exc:  # never let one job kill the worker
                log.exception("job %s crashed", job_id)
                self._finish(job, "failed", {"code": "internal_error", "message": str(exc)})
            finally:
                self._tasks.pop(job_id, None)

    async def _run(self, job: dict) -> None:
        job["status"] = "running"
        job["startedAt"] = job.get("startedAt") or now_iso()
        job["attempts"] = job.get("attempts", 0) + 1
        self._progress(job, "Preparing the course workspace")
        self._save(job)
        try:
            ws = await asyncio.to_thread(self.workspaces.prepare, job["courseId"])
        except ClaudeRequestError as exc:
            self._finish(job, "failed", {"code": exc.code, "message": exc.message})
            return
        run_id = job["id"]
        att_dir, out_dir = ws.run_dirs(run_id)
        for f in out_dir.glob("*"):
            f.unlink()
        src = self.uploads / job["id"]
        for name in job["attachments"]:
            if (src / name).is_file():
                shutil.copy2(src / name, att_dir / name)

        session_id = str(uuid.uuid4())
        job["sessionId"] = session_id
        prompt = prompts.job_prompt(job["kind"], job["params"], ws, run_id, job["attachments"])
        last_saved = [0.0]

        def on_event(ev: RunEvent) -> None:
            if ev.type == "status":
                self._progress(job, ev.data.get("text", ""))
                loop = asyncio.get_running_loop()
                if loop.time() - last_saved[0] > 2:
                    last_saved[0] = loop.time()
                    self._save(job)

        resume = False
        errors: list[str] = []
        data = None
        usage_total = {"costUsd": 0.0, "durationMs": 0, "numTurns": 0}
        for round_ in range(self.settings.fix_rounds + 1):
            self._progress(job, "Asking Claude" if round_ == 0 else f"Asking Claude to fix {len(errors)} problem(s)")
            self._save(job)
            req = RunRequest(
                prompt=prompt,
                cwd=ws.root,
                session_id=session_id,
                resume=resume,
                model=self.settings.claude_model,
                tools=self.settings.claude_tools,
                effort=self.settings.claude_effort_jobs,
                timeout_s=self.settings.job_timeout_s,
                extra_args=self.settings.claude_extra_args,
            )
            try:
                result = await run_claude(self.runner, req, on_event)
            except RunFailed as exc:
                self._finish(job, "failed", {"code": exc.code, "message": exc.message})
                return
            for k in usage_total:
                v = result.get(k)
                if isinstance(v, (int, float)):
                    usage_total[k] += v
            resume = True
            out_file = out_dir / "result.json"
            try:
                data = json.loads(out_file.read_text("utf-8"))
                errors = check_result(job["kind"], data, ws.cards() if job["kind"] == "enhance_cards" else None)
            except FileNotFoundError:
                data, errors = None, [f"runs/{run_id}/out/result.json was not written"]
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                data, errors = None, [f"result.json is not valid JSON: {exc}"]
            if not errors:
                break
            prompt = prompts.fix_prompt(job["kind"], run_id, errors)

        job["usage"] = usage_total
        if data is None or not isinstance(data, dict):
            self._finish(job, "failed", {"code": "bad_output", "message": "; ".join(errors[:5])})
            return
        job["result"] = decorate_result(job["kind"], data, ws, job["id"])
        job["checks"] = {"passed": not errors, "problems": errors}
        if errors:
            self._progress(job, f"Delivered with {len(errors)} unresolved check problem(s)")
        self._finish(job, "succeeded")
