"""Backup mirror of the library folder (DESIGN.md §7.7).

The app is the source of truth. It asks for the manifest, compares content
hashes with its local files and uploads whatever changed (PUT), deleting what it
no longer has (DELETE moves to a server-side trash, kept MM_TRASH_DAYS). The
mirror is a plain folder tree identical to the library, so:
  * nightly snapshots are just `restic backup <data>/mirror` (deploy/),
  * Claude jobs read the course files straight from it,
  * a restore is "download every file in the manifest into a new folder".
"""

from __future__ import annotations

import hashlib
import os
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from .util import BadPath, atomic_write_json, clean_relpath, now_iso, read_json, resolve_under


class MirrorError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def _is_temp(name: str) -> bool:
    return name.startswith(".tmp-") and name.endswith(".part")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Mirror:
    def __init__(self, root: Path, index_path: Path, trash_dir: Path, trash_days: int = 30):
        self.root = root
        self.index_path = index_path
        self.trash_dir = trash_dir
        self.trash_days = trash_days
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._index: dict[str, dict] = read_json(index_path, {}) or {}

    # ------------------------------------------------------------------ index
    def _save_index(self) -> None:
        atomic_write_json(self.index_path, self._index)

    def scan(self) -> list[dict]:
        """Walk the tree and return the manifest, re-hashing only files whose size/mtime changed."""
        with self._lock:
            seen: dict[str, dict] = {}
            changed = False
            for dirpath, dirnames, filenames in os.walk(self.root):
                dirnames.sort()
                for name in sorted(filenames):
                    if _is_temp(name):
                        continue
                    full = Path(dirpath) / name
                    rel = full.relative_to(self.root).as_posix()
                    st = full.stat()
                    entry = self._index.get(rel)
                    if not entry or entry.get("size") != st.st_size or entry.get("mtimeNs") != st.st_mtime_ns:
                        entry = {
                            **(entry or {}),
                            "size": st.st_size,
                            "mtimeNs": st.st_mtime_ns,
                            "sha256": sha256_file(full),
                        }
                        changed = True
                    seen[rel] = entry
            if changed or set(seen) != set(self._index):
                self._index = seen
                self._save_index()
            return [self._public(rel, e) for rel, e in sorted(seen.items())]

    @staticmethod
    def _public(rel: str, e: dict) -> dict:
        return {
            "path": rel,
            "size": e["size"],
            "sha256": e["sha256"],
            "modified": e.get("clientModified"),
            "uploaded": e.get("uploaded"),
        }

    def stats(self) -> dict:
        with self._lock:
            return {
                "files": len(self._index),
                "bytes": sum(e.get("size", 0) for e in self._index.values()),
                "lastUpload": max((e.get("uploaded") or "" for e in self._index.values()), default="") or None,
            }

    # ------------------------------------------------------------------ files
    def path_for(self, rel: str) -> Path:
        try:
            return resolve_under(self.root, rel)
        except BadPath as exc:
            raise MirrorError(400, "bad_path", str(exc)) from exc

    def stat(self, rel: str) -> dict | None:
        rel = clean_relpath(rel)
        full = self.path_for(rel)
        if not full.is_file():
            return None
        with self._lock:
            entry = self._index.get(rel)
            st = full.stat()
            if not entry or entry.get("size") != st.st_size or entry.get("mtimeNs") != st.st_mtime_ns:
                self.scan()
                entry = self._index.get(rel)
        return self._public(rel, entry) if entry else None

    async def put(
        self,
        rel: str,
        chunks: AsyncIterator[bytes],
        *,
        expected_sha256: str | None,
        max_bytes: int,
        client_modified: str | None = None,
        device: str | None = None,
    ) -> dict:
        try:
            rel = clean_relpath(rel)
        except BadPath as exc:
            raise MirrorError(400, "bad_path", str(exc)) from exc
        if _is_temp(rel.rsplit("/", 1)[-1]):
            raise MirrorError(400, "bad_path", "reserved file name")
        target = self.path_for(rel)
        # A file can't sit where a folder is needed, or vice versa.
        for parent in target.parents:
            if parent == self.root.resolve():
                break
            if parent.is_file():
                raise MirrorError(409, "path_conflict", f"{parent.relative_to(self.root.resolve())} is a file")
        if target.is_dir():
            raise MirrorError(409, "path_conflict", f"{rel} is a folder")
        target.parent.mkdir(parents=True, exist_ok=True)

        tmp = target.parent / f".tmp-{os.getpid()}-{threading.get_ident()}-{time.monotonic_ns()}.part"
        h = hashlib.sha256()
        size = 0
        try:
            with open(tmp, "wb") as fh:
                async for chunk in chunks:
                    size += len(chunk)
                    if size > max_bytes:
                        raise MirrorError(413, "too_large", f"file exceeds {max_bytes} bytes")
                    h.update(chunk)
                    fh.write(chunk)
                fh.flush()
                os.fsync(fh.fileno())
            digest = h.hexdigest()
            if expected_sha256 and expected_sha256.lower() != digest:
                raise MirrorError(400, "hash_mismatch", f"body hash {digest} != X-Content-SHA256")
            with self._lock:
                os.replace(tmp, target)
                st = target.stat()
                self._index[rel] = {
                    "size": st.st_size,
                    "mtimeNs": st.st_mtime_ns,
                    "sha256": digest,
                    "clientModified": client_modified,
                    "uploaded": now_iso(),
                    "device": device,
                }
                self._save_index()
                return self._public(rel, self._index[rel])
        finally:
            if tmp.exists():
                tmp.unlink()

    def delete(self, rel: str) -> bool:
        try:
            rel = clean_relpath(rel)
        except BadPath as exc:
            raise MirrorError(400, "bad_path", str(exc)) from exc
        target = self.path_for(rel)
        if not target.is_file():
            return False
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        dest = self.trash_dir / stamp / rel
        with self._lock:
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.replace(target, dest)
            self._index.pop(rel, None)
            self._save_index()
            # Tidy empty folders up to the root.
            parent = target.parent
            root = self.root.resolve()
            while parent != root and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        return True

    def purge_trash(self, now: float | None = None) -> int:
        if not self.trash_dir.is_dir():
            return 0
        cutoff = (now or time.time()) - self.trash_days * 86400
        removed = 0
        for entry in self.trash_dir.iterdir():
            try:
                stamp = datetime.strptime(entry.name, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).timestamp()
            except ValueError:
                continue
            if stamp < cutoff:
                shutil.rmtree(entry, ignore_errors=True)
                removed += 1
        return removed
