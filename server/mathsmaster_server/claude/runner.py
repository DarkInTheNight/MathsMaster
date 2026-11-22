"""How we talk to Claude: one swappable interface, two implementations.

`CliRunner` spawns headless Claude Code (`claude -p --output-format stream-json`)
signed in with the owner's subscription on the VPS. `FakeRunner` runs a Python
callback instead, so tests (and a demo mode, MM_CLAUDE_RUNNER=fake) work with
no Claude login at all. Everything above this module only sees `RunEvent`s.

Event types:
  session  {"sessionId", "model"}          Claude Code started (or resumed) a session
  status   {"text"}                        what Claude is doing ("Reading LA notes.pdf")
  delta    {"text"}                        streamed reply text
  result   {"text", "isError", "sessionId", "costUsd", "durationMs", "numTurns", "usage"}
  error    {"code", "message"}             the run failed (no result)
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable, Protocol, Union


@dataclass
class RunRequest:
    prompt: str
    cwd: Path
    session_id: str
    resume: bool
    model: str
    tools: str
    effort: str = ""
    timeout_s: int = 1800
    extra_args: list[str] = field(default_factory=list)


@dataclass
class RunEvent:
    type: str
    data: dict


class ClaudeRunner(Protocol):
    name: str

    def run(self, req: RunRequest) -> AsyncIterator[RunEvent]: ...


def classify_error(text: str) -> str:
    t = (text or "").lower()
    if "not logged in" in t or "/login" in t or "invalid api key" in t or "oauth" in t or "authentication" in t:
        return "claude_auth"
    if "usage limit" in t or "limit reached" in t or "rate limit" in t or "rate_limit" in t or "429" in t:
        return "claude_limit"
    if "no conversation found" in t:
        return "session_not_found"
    return "claude_error"


def describe_tool(name: str, inp: dict, cwd: Path) -> str:
    def rel(p: str) -> str:
        try:
            return str(Path(p).resolve().relative_to(cwd.resolve()))
        except (ValueError, OSError):
            return Path(p).name

    path = inp.get("file_path") or inp.get("path") or ""
    if name == "Read":
        extra = ""
        if inp.get("pages"):
            extra = f" pp. {inp['pages']}"
        elif inp.get("offset"):
            extra = f" from line {inp['offset']}"
        return f"Reading {rel(path)}{extra}" if path else "Reading"
    if name == "Grep":
        return f"Searching for “{str(inp.get('pattern', ''))[:60]}”"
    if name == "Glob":
        return f"Looking for {str(inp.get('pattern', 'files'))[:60]}"
    if name == "Write":
        return f"Writing {rel(path)}" if path else "Writing"
    if name == "Edit":
        return f"Editing {rel(path)}" if path else "Editing"
    if name in ("Task", "Agent"):
        return f"Delegating: {str(inp.get('description', ''))[:60]}"
    if name == "TodoWrite":
        return "Planning"
    return f"Using {name}"


# Env vars set when this server itself runs inside a Claude Code session (local
# development); passing them on would make the child think it's nested.
_STRIP_ENV = {
    "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_PID", "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_CODE_CHILD_NOTES_DIR", "CLAUDE_EFFORT", "CLAUDE_CODE_EXECPATH",
}


class CliRunner:
    name = "cli"

    def __init__(self, binary: str = "claude"):
        self.binary = binary

    def available(self) -> bool:
        return shutil.which(self.binary) is not None or Path(self.binary).is_file()

    def argv(self, req: RunRequest) -> list[str]:
        args = [
            self.binary, "-p",
            "--output-format", "stream-json", "--verbose", "--include-partial-messages",
            "--model", req.model,
            "--tools", req.tools,
            "--allowedTools", req.tools,
        ]
        args += ["--resume", req.session_id] if req.resume else ["--session-id", req.session_id]
        if req.effort:
            args += ["--effort", req.effort]
        return args + list(req.extra_args)

    async def run(self, req: RunRequest) -> AsyncIterator[RunEvent]:
        env = {k: v for k, v in os.environ.items() if k not in _STRIP_ENV}
        try:
            proc = await asyncio.create_subprocess_exec(
                *self.argv(req),
                cwd=str(req.cwd),
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=64 * 1024 * 1024,  # stream-json lines can be large
            )
        except FileNotFoundError:
            yield RunEvent("error", {"code": "claude_missing", "message": f"Claude Code binary {self.binary!r} not found"})
            return

        stderr_tail = bytearray()

        async def pump_stderr() -> None:
            assert proc.stderr
            while chunk := await proc.stderr.read(4096):
                stderr_tail.extend(chunk)
                del stderr_tail[:-8192]

        async def feed_stdin() -> None:
            assert proc.stdin
            try:
                proc.stdin.write(req.prompt.encode())
                await proc.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                proc.stdin.close()

        err_task = asyncio.create_task(pump_stderr())
        in_task = asyncio.create_task(feed_stdin())
        got_result = False
        loop = asyncio.get_running_loop()
        deadline = loop.time() + req.timeout_s
        try:
            assert proc.stdout
            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise asyncio.TimeoutError
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=remaining)
                if not line:
                    break
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for ev in self._translate(msg, req.cwd):
                    if ev.type == "result":
                        got_result = True
                    yield ev
            await proc.wait()
            await err_task
            if not got_result:
                tail = stderr_tail.decode("utf-8", "replace").strip()[-2000:]
                yield RunEvent(
                    "error",
                    {"code": classify_error(tail) if tail else "claude_error",
                     "message": f"Claude Code exited with code {proc.returncode} and no result. {tail}".strip()},
                )
        except asyncio.TimeoutError:
            yield RunEvent("error", {"code": "timeout", "message": f"Claude Code ran longer than {req.timeout_s}s"})
        finally:
            if proc.returncode is None:
                proc.kill()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=10)
                except asyncio.TimeoutError:
                    pass
            for t in (err_task, in_task):
                if not t.done():
                    t.cancel()

    @staticmethod
    def _translate(msg: dict, cwd: Path) -> list[RunEvent]:
        kind = msg.get("type")
        if kind == "system" and msg.get("subtype") == "init":
            return [RunEvent("session", {"sessionId": msg.get("session_id"), "model": msg.get("model")})]
        if kind == "stream_event":
            ev = msg.get("event") or {}
            delta = ev.get("delta") or {}
            if ev.get("type") == "content_block_delta" and delta.get("type") == "text_delta" and delta.get("text"):
                # Only top-level text (sub-agents have a parent_tool_use_id).
                if not msg.get("parent_tool_use_id"):
                    return [RunEvent("delta", {"text": delta["text"]})]
            return []
        if kind == "assistant":
            out = []
            for block in (msg.get("message") or {}).get("content") or []:
                if block.get("type") == "tool_use":
                    out.append(RunEvent("status", {"text": describe_tool(block.get("name", ""), block.get("input") or {}, cwd)}))
            return out
        if kind == "result":
            is_error = bool(msg.get("is_error")) or (msg.get("subtype") not in (None, "success"))
            text = msg.get("result") or ""
            data = {
                "text": text,
                "isError": is_error,
                "subtype": msg.get("subtype"),
                "sessionId": msg.get("session_id"),
                "costUsd": msg.get("total_cost_usd"),
                "durationMs": msg.get("duration_ms"),
                "numTurns": msg.get("num_turns"),
                "usage": msg.get("usage"),
            }
            if is_error:
                data["code"] = classify_error(text or str(msg.get("subtype")))
            return [RunEvent("result", data)]
        return []


FakeHandler = Callable[[RunRequest], Union[list[RunEvent], Awaitable[list[RunEvent]]]]


class FakeRunner:
    """Runs a Python callback instead of Claude. The callback may write files into req.cwd."""

    name = "fake"

    def __init__(self, handler: FakeHandler | None = None, delay_s: float = 0.0):
        from .fake import demo_handler

        self.handler = handler or demo_handler
        self.delay_s = delay_s
        self.requests: list[RunRequest] = []

    def available(self) -> bool:
        return True

    async def run(self, req: RunRequest) -> AsyncIterator[RunEvent]:
        self.requests.append(req)
        result = self.handler(req)
        if asyncio.iscoroutine(result):
            result = await result
        for ev in result:  # type: ignore[union-attr]
            if self.delay_s:
                await asyncio.sleep(self.delay_s)
            yield ev
