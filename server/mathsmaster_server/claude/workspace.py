"""Per-course workspaces where Claude Code runs.

Claude never runs inside the backup mirror itself: a stray Write/Edit there
would corrupt the backup. Instead each course gets a stable workspace

    <data>/workspaces/<courseId>/
        course/                  copy of the mirrored course folder, refreshed before every run
        AI/card-guidelines.md    copy of the owner's guidelines
        runs/<runId>/attachments ink/photos sent with the request
        runs/<runId>/out         where Claude writes its JSON output

The path is stable so Claude Code sessions (stored per working directory) can be
resumed for card threads. The refresh copies only changed files (size + mtime)
and skips what Claude can't use: PencilKit .drawing files, kept attempts and
other threads.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path

from ..util import BadPath, read_json, resolve_under, valid_id

GUIDELINES_REL = "AI/card-guidelines.md"
SKIP_DIRS = {"attempts", "threads", ".trash"}
SKIP_SUFFIXES = {".drawing"}
MAX_ATTACHMENTS = 8
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024
ATTACHMENT_TYPES = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/heic": ".heic", "image/webp": ".webp",
    "application/pdf": ".pdf", "text/plain": ".txt",
}


class ClaudeRequestError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


@dataclass
class Course:
    id: str
    name: str
    folder: str  # library-relative, e.g. "Courses/Linear Algebra"


@dataclass
class Workspace:
    root: Path
    course: Course
    guidelines: str
    instructions: str  # course/ai-instructions.md, "" if absent

    @property
    def course_dir(self) -> Path:
        return self.root / "course"

    def context_hash(self, adapter: str) -> str:
        h = hashlib.sha256()
        for part in (adapter, self.guidelines, self.instructions):
            h.update(part.encode())
            h.update(b"\0")
        return h.hexdigest()[:16]

    def run_dirs(self, run_id: str) -> tuple[Path, Path]:
        base = self.root / "runs" / run_id
        att, out = base / "attachments", base / "out"
        att.mkdir(parents=True, exist_ok=True)
        out.mkdir(parents=True, exist_ok=True)
        return att, out

    def inventory(self, limit: int = 400) -> list[str]:
        lines: list[str] = []
        for dirpath, dirnames, filenames in os.walk(self.course_dir):
            dirnames.sort()
            for name in sorted(filenames):
                p = Path(dirpath) / name
                rel = p.relative_to(self.root).as_posix()
                size = p.stat().st_size
                lines.append(f"{rel} ({size // 1024 or 1} KB)")
                if len(lines) >= limit:
                    lines.append("… (more files not listed; use Glob)")
                    return lines
        return lines

    def cards(self) -> dict[str, dict]:
        """The course deck (course/cards.json) as id -> card. Tolerates a bare list or {"cards": [...]}."""
        data = read_json(self.course_dir / "cards.json", None)
        items = data.get("cards", []) if isinstance(data, dict) else (data or [])
        return {c["id"]: c for c in items if isinstance(c, dict) and isinstance(c.get("id"), str) and not c.get("deletedAt")}


def save_attachments(items: list[dict], dest: Path) -> list[str]:
    """Decode base64 attachments ({name, mediaType, data}) into dest; return the saved file names."""
    if len(items) > MAX_ATTACHMENTS:
        raise ClaudeRequestError(400, "too_many_attachments", f"at most {MAX_ATTACHMENTS} attachments")
    dest.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    for i, item in enumerate(items):
        media_type = item.get("mediaType", "")
        ext = ATTACHMENT_TYPES.get(media_type)
        if not ext:
            raise ClaudeRequestError(400, "bad_attachment", f"unsupported attachment type {media_type!r}")
        try:
            data = base64.b64decode(item.get("data", ""), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ClaudeRequestError(400, "bad_attachment", "attachment data must be base64") from exc
        if len(data) > MAX_ATTACHMENT_BYTES:
            raise ClaudeRequestError(413, "too_large", "attachment too large")
        stem = "".join(c if c.isalnum() or c in "-_" else "-" for c in Path(item.get("name") or f"attachment-{i + 1}").stem)[:60]
        name = f"{i + 1:02d}-{stem or 'attachment'}{ext}"
        (dest / name).write_bytes(data)
        names.append(name)
    return names


class Workspaces:
    def __init__(self, mirror_root: Path, root: Path):
        self.mirror_root = mirror_root
        self.root = root
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _lock(self, key: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(key, threading.Lock())

    def resolve_course(self, course_id: str) -> Course:
        library = read_json(self.mirror_root / "library.json", None)
        if not isinstance(library, dict):
            raise ClaudeRequestError(409, "library_not_mirrored", "library.json isn't in the backup mirror yet; let the app sync first")
        for c in library.get("courses", []):
            if isinstance(c, dict) and c.get("id") == course_id:
                folder = c.get("folder") or f"Courses/{c.get('name', '')}"
                try:
                    path = resolve_under(self.mirror_root, folder)
                except BadPath as exc:
                    raise ClaudeRequestError(409, "bad_course_folder", str(exc)) from exc
                if not path.is_dir():
                    raise ClaudeRequestError(409, "course_not_mirrored", f"{folder} isn't in the backup mirror yet")
                return Course(course_id, c.get("name") or folder.rsplit("/", 1)[-1], folder)
        raise ClaudeRequestError(404, "unknown_course", f"no course {course_id!r} in library.json")

    def guidelines(self) -> str:
        path = self.mirror_root / GUIDELINES_REL
        try:
            text = path.read_text("utf-8")
        except FileNotFoundError:
            text = ""
        if not text.strip():
            raise ClaudeRequestError(
                409, "guidelines_missing",
                f"{GUIDELINES_REL} isn't in the backup mirror; every Claude request needs the card guidelines",
            )
        return text

    def check(self, course_id: str) -> Course:
        """Cheap validation at request time (before queueing)."""
        if not valid_id(course_id):
            raise ClaudeRequestError(400, "bad_course_id", "courseId has invalid characters")
        course = self.resolve_course(course_id)
        self.guidelines()
        return course

    def prepare(self, course_id: str) -> Workspace:
        course = self.check(course_id)
        guidelines = self.guidelines()
        ws_root = self.root / course_id
        with self._lock(course_id):
            src = self.mirror_root / course.folder
            dst = ws_root / "course"
            _sync_tree(src, dst)
            gpath = ws_root / GUIDELINES_REL
            gpath.parent.mkdir(parents=True, exist_ok=True)
            gpath.write_text(guidelines, "utf-8")
        instr_path = dst / "ai-instructions.md"
        instructions = instr_path.read_text("utf-8") if instr_path.is_file() else ""
        return Workspace(ws_root, course, guidelines, instructions)


def _skip(rel_parts: tuple[str, ...]) -> bool:
    if any(p in SKIP_DIRS or p.startswith(".") for p in rel_parts):
        return True
    return Path(rel_parts[-1]).suffix.lower() in SKIP_SUFFIXES


def _sync_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    wanted: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(src):
        rel_dir = Path(dirpath).relative_to(src)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            rel = rel_dir / name
            if _skip(rel.parts):
                continue
            wanted.add(rel.as_posix())
            s, d = src / rel, dst / rel
            st = s.stat()
            try:
                dt = d.stat()
                if dt.st_size == st.st_size and int(dt.st_mtime) == int(st.st_mtime):
                    continue
            except FileNotFoundError:
                pass
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
    # Remove what's gone from the mirror (and anything Claude wrote into course/).
    for dirpath, dirnames, filenames in os.walk(dst, topdown=False):
        for name in filenames:
            rel = (Path(dirpath) / name).relative_to(dst).as_posix()
            if rel not in wanted:
                (Path(dirpath) / name).unlink()
        if Path(dirpath) != dst and not any(Path(dirpath).iterdir()):
            Path(dirpath).rmdir()
