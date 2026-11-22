"""The real subprocess runner, driven against tests/fake_claude.py (no Claude login needed)."""

import asyncio
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import COURSE_ID, FAKE_CLAUDE, make_library, read_sse, wait_for
from mathsmaster_server.app import create_app
from mathsmaster_server.claude.runner import CliRunner, RunRequest, classify_error, describe_tool


def collect(runner, req):
    async def go():
        return [ev async for ev in runner.run(req)]
    return asyncio.run(go())


def req_for(tmp_path, prompt="hello", **kw):
    return RunRequest(prompt=prompt, cwd=tmp_path, session_id=str(uuid.uuid4()), resume=False,
                      model="claude-opus-5-5", tools="Read,Glob,Grep,Write,Edit", **kw)


def test_stream_json_is_translated(tmp_path, monkeypatch):
    log = tmp_path / "log.jsonl"
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(log))
    monkeypatch.setenv("CLAUDECODE", "1")  # must not leak into the child
    req = req_for(tmp_path, effort="high", extra_args=["--max-turns", "50"])
    events = collect(CliRunner(str(FAKE_CLAUDE)), req)
    types = [e.type for e in events]
    assert types[0] == "session" and events[0].data["sessionId"] == req.session_id
    assert "status" in types and events[types.index("status")].data["text"] == "Reading course/cards.json"
    assert "".join(e.data["text"] for e in events if e.type == "delta") == "Here is the reply \\(x\\)."
    result = events[-1]
    assert result.type == "result" and not result.data["isError"] and result.data["costUsd"] == 0.01
    call = json.loads(log.read_text().splitlines()[0])
    argv = call["argv"]
    assert argv[:1] == ["-p"] and call["prompt"] == "hello"  # prompt goes over stdin
    for flag, value in [("--output-format", "stream-json"), ("--model", "claude-opus-5-5"), ("--effort", "high"),
                        ("--session-id", req.session_id), ("--tools", "Read,Glob,Grep,Write,Edit"), ("--max-turns", "50")]:
        assert argv[argv.index(flag) + 1] == value
    assert "--verbose" in argv and "--include-partial-messages" in argv


def test_resume_flag(tmp_path, monkeypatch):
    log = tmp_path / "log.jsonl"
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(log))
    req = req_for(tmp_path)
    req.resume = True
    collect(CliRunner(str(FAKE_CLAUDE)), req)
    argv = json.loads(log.read_text())["argv"]
    assert argv[argv.index("--resume") + 1] == req.session_id and "--session-id" not in argv


def test_not_logged_in(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "notloggedin")
    events = collect(CliRunner(str(FAKE_CLAUDE)), req_for(tmp_path))
    assert events[-1].type == "result" and events[-1].data["isError"] and events[-1].data["code"] == "claude_auth"


def test_crash_without_result(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "crash")
    events = collect(CliRunner(str(FAKE_CLAUDE)), req_for(tmp_path))
    assert events[-1].type == "error" and "boom" in events[-1].data["message"]


def test_timeout_kills_process(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "hang")
    events = collect(CliRunner(str(FAKE_CLAUDE)), req_for(tmp_path, timeout_s=1))
    assert events[-1].type == "error" and events[-1].data["code"] == "timeout"


def test_missing_binary(tmp_path):
    events = collect(CliRunner(str(tmp_path / "no-such-claude")), req_for(tmp_path))
    assert events == [events[0]] and events[0].data["code"] == "claude_missing"


def test_helpers():
    assert classify_error("Not logged in · Please run /login") == "claude_auth"
    assert classify_error("Claude AI usage limit reached|1764000000") == "claude_limit"
    assert classify_error("No conversation found with session ID: abc") == "session_not_found"
    cwd = Path("/w")
    assert describe_tool("Read", {"file_path": "/w/course/notes.pdf", "pages": "55-61"}, cwd) == "Reading course/notes.pdf pp. 55-61"
    assert describe_tool("Grep", {"pattern": "Sylow"}, cwd) == "Searching for “Sylow”"


@pytest.mark.parametrize("mode,status,checks_passed", [("ok", "succeeded", True), ("bad", "succeeded", True)])
def test_end_to_end_job_and_thread_through_subprocess(settings, token, monkeypatch, mode, status, checks_passed):
    """Full path: HTTP -> job queue -> workspace -> real subprocess runner -> validation (+ fix round)."""
    monkeypatch.setenv("FAKE_CLAUDE_MODE", mode)
    log = settings.data_dir.parent / "calls.jsonl"
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(log))
    settings.claude_bin = str(FAKE_CLAUDE)
    make_library(settings.mirror_dir)
    auth = {"Authorization": f"Bearer {token}"}
    with TestClient(create_app(settings)) as c:
        assert c.get("/v1/status", headers=auth).json()["claude"] == {"runner": "cli", "available": True, "model": "claude-opus-5-5"}
        jid = c.post("/v1/jobs", json={"kind": "generate_cards", "courseId": COURSE_ID}, headers=auth).json()["id"]
        job = wait_for(lambda: (j := c.get(f"/v1/jobs/{jid}", headers=auth).json())["status"] not in ("queued", "running") and j)
        assert job["status"] == status, job
        assert job["checks"]["passed"] is checks_passed
        assert job["result"]["cards"][0]["front"] == "Definition of a group"
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        assert len(calls) == (2 if mode == "bad" else 1)
        assert Path(calls[0]["cwd"]).name == COURSE_ID

        with c.stream("POST", "/v1/threads/card-1", json={"courseId": COURSE_ID, "cardId": "card-1",
                                                           "message": "please propose an addition"}, headers=auth) as r:
            events = read_sse(r)
        done = events[-1]
        assert done[0] == "done", events
        prop = done[1]["message"]["proposals"][0]
        assert prop["cardId"] == "card-1" and prop["additionsOnly"] is True


def test_cli_offline_import(tmp_path):
    from conftest import FIXTURES
    out = tmp_path / "out.json"
    r = subprocess.run([sys.executable, "-m", "mathsmaster_server", "import-apkg", str(FIXTURES / "synthetic.apkg"),
                        "-o", str(out), "--media", str(tmp_path / "media")], capture_output=True, text=True,
                       cwd=Path(__file__).parent.parent)
    assert r.returncode == 0, r.stderr
    assert json.loads(out.read_text())["summary"]["cards"] == 7 and (tmp_path / "media" / "diagram.png").is_file()


def test_cli_tokens_and_doctor(tmp_path):
    env = {"MM_DATA_DIR": str(tmp_path / "data"), "MM_CLAUDE_BIN": str(FAKE_CLAUDE), "PATH": "/usr/bin:/bin"}
    run = lambda *a: subprocess.run([sys.executable, "-m", "mathsmaster_server", *a], capture_output=True, text=True,
                                    env=env, cwd=Path(__file__).parent.parent)
    r = run("token", "add", "iPad · Playgrounds")
    assert r.returncode == 0 and "Token:  mm_" in r.stdout
    assert "iPad · Playgrounds" in run("token", "list").stdout
    d = run("doctor", "--live")
    assert d.returncode == 0, d.stdout + d.stderr
    assert "Claude Code answered" in d.stdout
    assert run("token", "revoke", "iPad · Playgrounds").returncode == 0
