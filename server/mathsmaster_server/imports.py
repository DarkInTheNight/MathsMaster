"""Anki import jobs (DESIGN.md §4.8): upload an .apkg, convert in the background, fetch the result.

    <data>/imports/<id>/status.json   status + summary
    <data>/imports/<id>/result.json   cards + reviews + decks (API.md "Anki import result")
    <data>/imports/<id>/media/        media files, served one by one

The uploaded package and the extracted collection are deleted as soon as the
conversion finishes; the result stays until the app deletes it (DELETE) or
MM_TRASH_DAYS pass.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import time
from pathlib import Path
from typing import AsyncIterator

from .anki import AnkiImportError, convert_package
from .util import atomic_write_json, new_id, now_iso, read_json, valid_id

log = logging.getLogger("mathsmaster.imports")


class ImportManager:
    def __init__(self, data_dir: Path, mirror_root: Path, max_bytes: int, keep_days: int = 30):
        self.dir = data_dir / "imports"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.mirror_root = mirror_root
        self.max_bytes = max_bytes
        self.keep_days = keep_days
        self._tasks: set[asyncio.Task] = set()

    def _status_path(self, import_id: str) -> Path:
        return self.dir / import_id / "status.json"

    def get(self, import_id: str) -> dict | None:
        if not valid_id(import_id):
            return None
        return read_json(self._status_path(import_id), None)

    def result_path(self, import_id: str) -> Path | None:
        st = self.get(import_id)
        if not st or st["status"] != "succeeded":
            return None
        return self.dir / import_id / "result.json"

    def media_path(self, import_id: str, name: str) -> Path | None:
        if not self.get(import_id) or "/" in name or "\\" in name or name.startswith(".") or not name:
            return None
        p = self.dir / import_id / "media" / name
        return p if p.is_file() else None

    def delete(self, import_id: str) -> bool:
        st = self.get(import_id)
        if not st or st["status"] in ("queued", "running"):
            return False
        shutil.rmtree(self.dir / import_id, ignore_errors=True)
        return True

    def _save(self, st: dict) -> None:
        atomic_write_json(self._status_path(st["id"]), st)

    async def create(self, chunks: AsyncIterator[bytes], filename: str, device: str | None) -> dict:
        import_id = new_id("imp")
        folder = self.dir / import_id
        folder.mkdir(parents=True)
        upload = folder / "upload.apkg"
        size = 0
        try:
            with open(upload, "wb") as fh:
                async for chunk in chunks:
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise AnkiImportError("too_large", f"package exceeds {self.max_bytes} bytes")
                    fh.write(chunk)
        except BaseException:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        if size == 0:
            shutil.rmtree(folder, ignore_errors=True)
            raise AnkiImportError("empty_upload", "the request body was empty")
        st = {
            "id": import_id,
            "status": "queued",
            "filename": filename,
            "size": size,
            "createdAt": now_iso(),
            "finishedAt": None,
            "summary": None,
            "decks": None,
            "warnings": [],
            "error": None,
            "device": device,
        }
        self._save(st)
        task = asyncio.create_task(self._run(st))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return st

    async def _run(self, st: dict) -> None:
        folder = self.dir / st["id"]
        st["status"] = "running"
        self._save(st)
        library = read_json(self.mirror_root / "library.json", {}) or {}
        courses = library.get("courses", []) if isinstance(library, dict) else []
        try:
            result = await asyncio.to_thread(
                convert_package, folder / "upload.apkg", folder / "work", folder / "media", courses
            )
            result["id"] = st["id"]
            result["source"]["filename"] = st["filename"]
            atomic_write_json(folder / "result.json", result)
            st.update(
                status="succeeded",
                summary=result["summary"],
                decks=[{k: d[k] for k in ("id", "name", "cardCount", "reviewCount", "suggestedCourseId")} for d in result["decks"]],
                warnings=result["warnings"][:50],
            )
        except AnkiImportError as exc:
            st.update(status="failed", error={"code": exc.code, "message": exc.message})
        except Exception as exc:
            log.exception("import %s crashed", st["id"])
            st.update(status="failed", error={"code": "internal_error", "message": str(exc)})
        finally:
            st["finishedAt"] = now_iso()
            self._save(st)
            (folder / "upload.apkg").unlink(missing_ok=True)
            shutil.rmtree(folder / "work", ignore_errors=True)

    async def recover(self) -> None:
        """On startup: imports cut off by a restart are failed (their upload may be partial); old ones purged."""
        cutoff = time.time() - self.keep_days * 86400
        for folder in self.dir.iterdir():
            st = read_json(folder / "status.json", None)
            if not st:
                shutil.rmtree(folder, ignore_errors=True)
                continue
            if st["status"] in ("queued", "running"):
                if (folder / "upload.apkg").is_file() and st.get("size") == (folder / "upload.apkg").stat().st_size:
                    task = asyncio.create_task(self._run(st))
                    self._tasks.add(task)
                    task.add_done_callback(self._tasks.discard)
                else:
                    st.update(status="failed", error={"code": "interrupted", "message": "the server restarted"})
                    self._save(st)
            elif folder.stat().st_mtime < cutoff:
                shutil.rmtree(folder, ignore_errors=True)

    async def stop(self) -> None:
        await asyncio.gather(*self._tasks, return_exceptions=True)
