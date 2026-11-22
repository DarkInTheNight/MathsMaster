"""Small shared helpers: safe library paths, atomic writes, ids and timestamps."""

from __future__ import annotations

import json
import os
import secrets
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


class BadPath(ValueError):
    pass


# Names the mirror never stores: they'd escape the root, clash with our own
# bookkeeping, or are OS junk.
_FORBIDDEN_PARTS = {"", ".", ".."}
_JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def clean_relpath(raw: str) -> str:
    """Validate a library-relative path ("Courses/LA/cards.json") and return it NFC-normalised.

    Rejects absolute paths, "..", backslashes, NUL and control characters, so a
    path can never escape the mirror root. iOS hands us NFD names from some APIs
    and NFC from others; we store NFC so "Linear Algèbra" is one file, not two.
    """
    if not isinstance(raw, str) or not raw:
        raise BadPath("empty path")
    if len(raw) > 1024:
        raise BadPath("path too long")
    if "\\" in raw or any(ord(c) < 32 or ord(c) == 127 for c in raw):
        raise BadPath("path contains a backslash or control character")
    if raw.startswith("/"):
        raise BadPath("path must be relative")
    path = unicodedata.normalize("NFC", raw)
    parts = path.split("/")
    for part in parts:
        if part in _FORBIDDEN_PARTS:
            raise BadPath(f"bad path segment {part!r}")
        if len(part.encode()) > 255:
            raise BadPath("path segment too long")
    if parts[-1] in _JUNK_NAMES:
        raise BadPath("junk file name")
    return str(PurePosixPath(*parts))


def resolve_under(root: Path, rel: str) -> Path:
    """Join a cleaned relative path onto root, double-checking it stays inside."""
    rel = clean_relpath(rel)
    target = (root / rel).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise BadPath("path escapes root")
    return target


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def atomic_write_json(path: Path, obj: Any) -> None:
    atomic_write_bytes(path, json.dumps(obj, ensure_ascii=False, indent=1).encode())


def read_json(path: Path, default: Any = None) -> Any:
    try:
        with open(path, "rb") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def iso_from_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def new_id(prefix: str) -> str:
    """Sortable-ish opaque id: prefix + UTC time + random suffix."""
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{secrets.token_hex(4)}"


def valid_id(value: str, max_len: int = 128) -> bool:
    return bool(value) and len(value) <= max_len and all(c.isalnum() or c in "-_." for c in value) and value not in {".", ".."}
