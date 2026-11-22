"""HTTP API (FastAPI). The human-readable spec is server/API.md; server/openapi.json is generated from this."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any, Literal, Optional

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from . import __version__
from .anki import AnkiImportError
from .auth import Device, TokenStore
from .claude.jobs import JobManager
from .claude.runner import CliRunner, ClaudeRunner, FakeRunner
from .claude.threads import ThreadManager
from .claude.workspace import GUIDELINES_REL, ClaudeRequestError, Workspaces
from .config import Settings
from .imports import ImportManager
from .mirror import Mirror, MirrorError
from .util import BadPath, valid_id

log = logging.getLogger("mathsmaster")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def _err(status: int, code: str, message: str, headers: dict | None = None) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status, headers=headers)


# ----------------------------------------------------------------------------- models (for OpenAPI)

class Attachment(BaseModel):
    name: Optional[str] = Field(None, description="Original file name (informational)")
    mediaType: str = Field(..., description="image/png, image/jpeg, image/heic, image/webp, application/pdf or text/plain")
    data: str = Field(..., description="Base64-encoded file content (≤ 25 MB decoded, ≤ 8 per request)")


class CardSnapshot(BaseModel):
    """The card as the app has it right now (it may not be in the mirror yet)."""
    model_config = {"extra": "allow"}
    id: Optional[str] = None
    front: str = ""
    back: str = ""
    label: Optional[str] = None
    lecture: Optional[int] = None
    tags: list[str] = []


class JobIn(BaseModel):
    kind: Literal["generate_cards", "enhance_cards", "explain", "check_attempt", "transcribe"]
    courseId: str = Field(..., description="Course id from library.json (the course folder must be in the mirror)")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Per kind: generate_cards {lectures?: '13-16', documents?: [paths under the course], instructions?}; "
        "enhance_cards {cardIds?: [...], instructions?}; explain {cardId | card, question?}; "
        "check_attempt {cardId | card, instructions?}; transcribe {mode?: card|math|text}",
    )
    attachments: list[Attachment] = []


class ThreadMessageIn(BaseModel):
    courseId: str
    cardId: Optional[str] = Field(None, description="Set for a card thread; omit for the course thread")
    message: str = ""
    intent: Literal["chat", "explain", "check_attempt"] = "chat"
    card: Optional[CardSnapshot] = None
    attachments: list[Attachment] = []


# ----------------------------------------------------------------------------- app

def make_runner(settings: Settings) -> ClaudeRunner:
    if settings.claude_runner == "fake":
        return FakeRunner()
    return CliRunner(settings.claude_bin)


def create_app(settings: Settings, runner: ClaudeRunner | None = None) -> FastAPI:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    runner = runner or make_runner(settings)
    tokens = TokenStore(settings.tokens_path)
    mirror = Mirror(settings.mirror_dir, settings.data_dir / "mirror-index.json",
                    settings.data_dir / "trash", settings.trash_days)
    workspaces = Workspaces(settings.mirror_dir, settings.data_dir / "workspaces")
    imports = ImportManager(settings.data_dir, settings.mirror_dir, settings.max_upload_bytes, settings.trash_days)
    jobs = JobManager(settings, workspaces, runner)
    threads = ThreadManager(settings, workspaces, runner)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        await asyncio.to_thread(mirror.scan)
        await imports.recover()
        await jobs.start()

        async def housekeeping():
            while True:
                await asyncio.to_thread(mirror.purge_trash)
                await asyncio.sleep(24 * 3600)

        hk = asyncio.create_task(housekeeping())
        try:
            yield
        finally:
            hk.cancel()
            await jobs.stop()
            await threads.stop()
            await imports.stop()

    app = FastAPI(
        title="MathsMaster VPS API",
        version=__version__,
        description="Backup mirror, Anki import and Claude jobs/threads for the MathsMaster app. "
        "All /v1 endpoints except /v1/health need `Authorization: Bearer <device token>`. See server/API.md.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.mirror = mirror
    app.state.jobs = jobs
    app.state.threads = threads
    app.state.imports = imports
    app.state.tokens = tokens
    app.state.runner = runner

    @app.exception_handler(ApiError)
    async def _api_error(_req, exc: ApiError):
        return _err(exc.status, exc.code, exc.message)

    @app.exception_handler(MirrorError)
    async def _mirror_error(_req, exc: MirrorError):
        return _err(exc.status, exc.code, exc.message)

    @app.exception_handler(ClaudeRequestError)
    async def _claude_error(_req, exc: ClaudeRequestError):
        return _err(exc.status, exc.code, exc.message)

    @app.exception_handler(AnkiImportError)
    async def _anki_error(_req, exc: AnkiImportError):
        return _err(413 if exc.code == "too_large" else 400, exc.code, exc.message)

    @app.exception_handler(BadPath)
    async def _bad_path(_req, exc: BadPath):
        return _err(400, "bad_path", str(exc))

    @app.exception_handler(RequestValidationError)
    async def _validation(_req, exc: RequestValidationError):
        return _err(422, "invalid_request", "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()))

    def device(authorization: Optional[str] = Header(None)) -> Device:
        token = ""
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        dev = tokens.verify(token)
        if not dev:
            raise ApiError(401, "unauthorized", "missing or invalid device token")
        return dev

    # ------------------------------------------------------------------ meta
    @app.get("/v1/health", tags=["meta"], summary="Liveness check (no auth)")
    async def health():
        return {"ok": True}

    @app.get("/v1/status", tags=["meta"], summary="Server, mirror, Claude and queue status")
    async def status(dev: Device = Depends(device)):
        return {
            "version": __version__,
            "device": {"id": dev.id, "name": dev.name},
            "mirror": mirror.stats(),
            "library": (settings.mirror_dir / "library.json").is_file(),
            "guidelines": (settings.mirror_dir / GUIDELINES_REL).is_file(),
            "claude": {
                "runner": runner.name,
                "available": getattr(runner, "available", lambda: True)(),
                "model": settings.claude_model,
            },
            "jobs": jobs.counts(),
        }

    # ------------------------------------------------------------------ mirror
    @app.get("/v1/manifest", tags=["mirror"], summary="Every file in the backup mirror with its SHA-256")
    async def manifest(dev: Device = Depends(device)):
        files = await asyncio.to_thread(mirror.scan)
        st = mirror.stats()
        return {"files": files, "fileCount": st["files"], "bytes": st["bytes"], "lastUpload": st["lastUpload"]}

    @app.put("/v1/files/{path:path}", tags=["mirror"], summary="Upload (create or replace) one library file",
             openapi_extra={"requestBody": {"content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}, "required": True}})
    async def put_file(
        path: str,
        request: Request,
        dev: Device = Depends(device),
        x_content_sha256: Optional[str] = Header(None, description="SHA-256 (hex) of the body; verified if sent"),
        x_modified: Optional[str] = Header(None, description="The file's modification time in the library (ISO 8601), echoed in the manifest"),
    ):
        return await mirror.put(
            path, request.stream(), expected_sha256=x_content_sha256, max_bytes=settings.max_upload_bytes,
            client_modified=x_modified, device=dev.name,
        )

    @app.get("/v1/files/{path:path}", tags=["mirror"], summary="Download one file from the mirror (restore)")
    async def get_file(path: str, dev: Device = Depends(device)):
        full = mirror.path_for(path)
        if not full.is_file():
            raise ApiError(404, "not_found", "no such file in the mirror")
        info = mirror.stat(path)
        return FileResponse(full, media_type="application/octet-stream",
                            headers={"X-Content-SHA256": info["sha256"]} if info else None)

    @app.delete("/v1/files/{path:path}", tags=["mirror"], summary="Delete a file from the mirror (kept in server trash)")
    async def delete_file(path: str, dev: Device = Depends(device)):
        if not mirror.delete(path):
            raise ApiError(404, "not_found", "no such file in the mirror")
        return {"deleted": path}

    # ------------------------------------------------------------------ anki import
    @app.post("/v1/imports", tags=["anki"], status_code=202, summary="Upload an .apkg/.colpkg to convert",
              openapi_extra={"requestBody": {"content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}, "required": True}})
    async def create_import(request: Request, filename: str = Query("deck.apkg"), dev: Device = Depends(device)):
        return await imports.create(request.stream(), filename[:200], dev.name)

    @app.get("/v1/imports/{import_id}", tags=["anki"], summary="Import status and summary")
    async def get_import(import_id: str, dev: Device = Depends(device)):
        st = imports.get(import_id)
        if not st:
            raise ApiError(404, "not_found", "no such import")
        return st

    @app.get("/v1/imports/{import_id}/result", tags=["anki"], summary="The converted cards, reviews and decks")
    async def get_import_result(import_id: str, dev: Device = Depends(device)):
        path = imports.result_path(import_id)
        if not path or not path.is_file():
            raise ApiError(404, "not_ready", "no finished result for this import")
        return FileResponse(path, media_type="application/json")

    @app.get("/v1/imports/{import_id}/media/{name}", tags=["anki"], summary="One media file from the import")
    async def get_import_media(import_id: str, name: str, dev: Device = Depends(device)):
        path = imports.media_path(import_id, name)
        if not path:
            raise ApiError(404, "not_found", "no such media file")
        return FileResponse(path, media_type="application/octet-stream")

    @app.delete("/v1/imports/{import_id}", tags=["anki"], summary="Delete an import's result from the server")
    async def delete_import(import_id: str, dev: Device = Depends(device)):
        if not imports.delete(import_id):
            raise ApiError(404, "not_found", "no such finished import")
        return {"deleted": import_id}

    # ------------------------------------------------------------------ jobs
    def job_view(job: dict) -> dict:
        view = dict(job)
        view["queuePosition"] = jobs.queue_position(job["id"])
        return view

    @app.post("/v1/jobs", tags=["claude"], status_code=202, summary="Queue a Claude job")
    async def create_job(body: JobIn, dev: Device = Depends(device)):
        job = await asyncio.to_thread(
            jobs.create, kind=body.kind, course_id=body.courseId, params=body.params,
            attachments=[a.model_dump() for a in body.attachments], device=dev.name,
        )
        return job_view(job)

    @app.get("/v1/jobs", tags=["claude"], summary="Recent jobs (without results)")
    async def list_jobs(status: Optional[str] = None, courseId: Optional[str] = None,
                        limit: int = Query(50, ge=1, le=500), dev: Device = Depends(device)):
        return {"jobs": [{k: v for k, v in job_view(j).items() if k != "result"} for j in jobs.list(status, courseId, limit)]}

    @app.get("/v1/jobs/{job_id}", tags=["claude"], summary="Job status, progress and (when done) result")
    async def get_job(job_id: str, dev: Device = Depends(device)):
        job = jobs.get(job_id)
        if not job:
            raise ApiError(404, "not_found", "no such job")
        return job_view(job)

    @app.post("/v1/jobs/{job_id}/cancel", tags=["claude"], summary="Cancel a queued or running job")
    async def cancel_job(job_id: str, dev: Device = Depends(device)):
        job = jobs.cancel(job_id)
        if not job:
            raise ApiError(404, "not_found", "no such job")
        await asyncio.sleep(0)
        return job_view(job)

    # ------------------------------------------------------------------ threads
    def sse(run, after: int):
        async def gen():
            async for ev in run.follow(after):
                if ev is None:
                    yield ": ping\n\n"
                    continue
                yield f"id: {ev['seq']}\nevent: {ev['type']}\ndata: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Run-Id": run.id})

    @app.post("/v1/threads/{thread_id}", tags=["claude"], summary="Send a message; the reply streams back as SSE",
              responses={200: {"content": {"text/event-stream": {}}, "description": "Events: run, status, delta, done | error"}})
    async def post_thread(thread_id: str, body: ThreadMessageIn, dev: Device = Depends(device)):
        run = threads.start(
            thread_id, course_id=body.courseId, card_id=body.cardId, message=body.message, intent=body.intent,
            card=body.card.model_dump() if body.card else None,
            attachments=[a.model_dump() for a in body.attachments], device=dev.name,
        )
        return sse(run, -1)

    @app.get("/v1/threads/{thread_id}", tags=["claude"], summary="The server's copy of a thread")
    async def get_thread(thread_id: str, dev: Device = Depends(device)):
        state = threads.load(thread_id) if valid_id(thread_id) else None
        if not state:
            raise ApiError(404, "not_found", "no such thread")
        return threads.public(state)

    @app.get("/v1/threads/{thread_id}/runs/{run_id}/events", tags=["claude"],
             summary="Re-attach to a reply's event stream (SSE), from event `after`+1")
    async def run_events(thread_id: str, run_id: str, after: int = -1, dev: Device = Depends(device)):
        run = threads.runs.get(run_id)
        if not run or run.thread_id != thread_id:
            raise ApiError(404, "not_found", "no such run (finished runs are kept for an hour)")
        return sse(run, after)

    @app.delete("/v1/threads/{thread_id}", tags=["claude"], summary="Forget the thread's Claude session (next message starts fresh)")
    async def delete_thread(thread_id: str, dev: Device = Depends(device)):
        if not valid_id(thread_id) or not threads.forget(thread_id):
            raise ApiError(404, "not_found", "no such thread")
        return {"deleted": thread_id}

    return app


def app_from_env() -> FastAPI:  # uvicorn --factory mathsmaster_server.app:app_from_env
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return create_app(Settings.from_env())
