"""Settings, read once from environment variables (see server/deploy/mathsmaster.env.example)."""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    return int(raw) if raw else default


def _str(name: str, default: str) -> str:
    raw = os.environ.get(name, "").strip()
    return raw if raw else default


@dataclass
class Settings:
    data_dir: Path
    host: str = "127.0.0.1"
    port: int = 8787
    tokens_file: Path | None = None
    max_upload_mb: int = 1024
    trash_days: int = 30

    # Claude Code
    claude_runner: str = "cli"  # "cli" (real `claude -p`) or "fake" (canned replies, for demos)
    claude_bin: str = "claude"
    claude_model: str = "claude-opus-5-5"
    claude_effort_jobs: str = "high"
    claude_effort_threads: str = ""  # empty: Claude Code's default
    claude_tools: str = "Read,Glob,Grep,Write,Edit"
    claude_extra_args: list[str] = field(default_factory=list)
    job_timeout_s: int = 6 * 3600
    thread_timeout_s: int = 30 * 60
    job_concurrency: int = 1
    thread_concurrency: int = 2
    fix_rounds: int = 2

    @property
    def mirror_dir(self) -> Path:
        return self.data_dir / "mirror"

    @property
    def tokens_path(self) -> Path:
        return self.tokens_file or (self.data_dir / "tokens.json")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @classmethod
    def from_env(cls) -> "Settings":
        tokens = os.environ.get("MM_TOKENS_FILE", "").strip()
        return cls(
            data_dir=Path(_str("MM_DATA_DIR", "/var/lib/mathsmaster")),
            host=_str("MM_HOST", "127.0.0.1"),
            port=_int("MM_PORT", 8787),
            tokens_file=Path(tokens) if tokens else None,
            max_upload_mb=_int("MM_MAX_UPLOAD_MB", 1024),
            trash_days=_int("MM_TRASH_DAYS", 30),
            claude_runner=_str("MM_CLAUDE_RUNNER", "cli"),
            claude_bin=_str("MM_CLAUDE_BIN", "claude"),
            claude_model=_str("MM_CLAUDE_MODEL", "claude-opus-5-5"),
            claude_effort_jobs=_str("MM_CLAUDE_EFFORT_JOBS", "high"),
            claude_effort_threads=os.environ.get("MM_CLAUDE_EFFORT_THREADS", "").strip(),
            claude_tools=_str("MM_CLAUDE_TOOLS", "Read,Glob,Grep,Write,Edit"),
            claude_extra_args=shlex.split(os.environ.get("MM_CLAUDE_EXTRA_ARGS", "")),
            job_timeout_s=_int("MM_JOB_TIMEOUT_S", 6 * 3600),
            thread_timeout_s=_int("MM_THREAD_TIMEOUT_S", 30 * 60),
            job_concurrency=max(1, _int("MM_JOB_CONCURRENCY", 1)),
            thread_concurrency=max(1, _int("MM_THREAD_CONCURRENCY", 2)),
            fix_rounds=max(0, _int("MM_FIX_ROUNDS", 2)),
        )
