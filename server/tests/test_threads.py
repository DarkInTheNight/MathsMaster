import asyncio
import json
from pathlib import Path

from conftest import COURSE_ID, GUIDELINES, make_library, read_sse, wait_for
from mathsmaster_server.claude.fake import MARKER
from mathsmaster_server.claude.runner import RunEvent


def reply_events(req, text="Because \\(x = 1\\)."):
    evs = [RunEvent("session", {"sessionId": req.session_id}), RunEvent("status", {"text": "Reading course/Lecture notes/notes.pdf pp. 3"})]
    evs += [RunEvent("delta", {"text": w}) for w in ("Because ", "\\(x = 1\\).")]
    evs.append(RunEvent("result", {"text": text, "isError": False, "costUsd": 0.1, "durationMs": 5, "numTurns": 1}))
    return evs


def post(client, auth, thread="card-1", **body):
    payload = {"courseId": COURSE_ID, "cardId": "card-1", "message": "why?", **body}
    with client.stream("POST", f"/v1/threads/{thread}", json=payload, headers=auth) as r:
        assert r.status_code == 200, r.read()
        assert r.headers["content-type"].startswith("text/event-stream")
        return read_sse(r)


def test_thread_streams_and_resumes(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)
    fake_runner.handler = reply_events
    events = post(client, auth)
    types = [t for t, _ in events]
    assert types[0] == "run" and types[-1] == "done"
    assert "status" in types and [d["text"] for t, d in events if t == "delta"] == ["Because ", "\\(x = 1\\)."]
    done = events[-1][1]
    assert done["message"]["text"] == "Because \\(x = 1\\)." and done["message"]["proposals"] == []

    first = fake_runner.requests[0]
    assert first.resume is False and GUIDELINES.strip() in first.prompt and "ORIGINAL BACK" in first.prompt
    assert first.effort == ""  # threads use Claude Code's default effort unless configured

    post(client, auth, message="and then?")
    second = fake_runner.requests[1]
    assert second.resume is True and second.session_id == first.session_id
    assert GUIDELINES.strip() not in second.prompt and "and then?" in second.prompt

    # Guidelines changed in the mirror -> context is sent again on the next turn.
    (settings.mirror_dir / "AI" / "card-guidelines.md").write_text(GUIDELINES + "\nNew rule.\n")
    post(client, auth, message="again")
    assert "New rule." in fake_runner.requests[2].prompt

    thread = client.get("/v1/threads/card-1", headers=auth).json()
    assert [m["role"] for m in thread["messages"]] == ["user", "assistant"] * 3
    assert thread["activeRunId"] is None


def test_proposals_get_additions_only_check(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)

    def handler(req):
        out = Path(req.cwd) / MARKER.search(req.prompt).group("out")
        out.mkdir(parents=True, exist_ok=True)
        (out / "proposals.json").write_text(json.dumps([
            {"cardId": "card-1", "back": "UNSYNCED BACK<br>Added.", "summary": "adds"},
            {"cardId": None, "front": "Definition of a span", "back": "uses $x$", "label": "Definition"},
        ]))
        return reply_events(req)
    fake_runner.handler = handler
    # The app sends its current (not yet synced) version of the card: the check uses that.
    events = post(client, auth, card={"id": "card-1", "front": "Definition of a basis", "back": "UNSYNCED BACK"})
    edit, new = events[-1][1]["message"]["proposals"]
    assert edit["additionsOnly"] is True and edit["original"]["back"] == "UNSYNCED BACK"
    assert edit["checks"]["back"]["insertions"] == [{"offset": len("UNSYNCED BACK"), "text": "<br>Added."}]
    assert new["additionsOnly"] is None and any("$" in x for x in new["lint"])


def test_thread_errors_and_busy(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)

    async def slow(req):
        await asyncio.sleep(0.5)
        return reply_events(req)
    fake_runner.handler = slow
    with client.stream("POST", "/v1/threads/card-1", json={"courseId": COURSE_ID, "cardId": "card-1", "message": "a"}, headers=auth) as r:
        busy = client.post("/v1/threads/card-1", json={"courseId": COURSE_ID, "cardId": "card-1", "message": "b"}, headers=auth)
        assert busy.status_code == 409 and busy.json()["error"]["code"] == "thread_busy"
        events = read_sse(r)
    assert events[-1][0] == "done"

    fake_runner.handler = lambda req: [RunEvent("error", {"code": "claude_auth", "message": "Not logged in"})]
    events = post(client, auth, thread="card-2", cardId="card-2")
    assert events[-1] == ("error", {"runId": events[0][1]["runId"], "code": "claude_auth", "message": "Not logged in"})
    msgs = client.get("/v1/threads/card-2", headers=auth).json()["messages"]
    assert msgs[-1]["error"]["code"] == "claude_auth"

    assert client.post("/v1/threads/bad id!", json={"courseId": COURSE_ID, "message": "x"}, headers=auth).status_code in (400, 404)
    r = client.post("/v1/threads/c", json={"courseId": COURSE_ID, "message": "", "intent": "chat"}, headers=auth)
    assert r.json()["error"]["code"] == "empty_message"
    r = client.post("/v1/threads/c", json={"courseId": COURSE_ID, "intent": "check_attempt"}, headers=auth)
    assert r.json()["error"]["code"] == "attachment_required"


def test_reattach_after_disconnect(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)

    async def slow(req):
        await asyncio.sleep(0.3)
        return reply_events(req)
    fake_runner.handler = slow
    with client.stream("POST", "/v1/threads/course-la", json={"courseId": COURSE_ID, "message": "hi"}, headers=auth) as r:
        run_id = r.headers["x-run-id"]
        # leave without reading: the client went to sleep
    wait_for(lambda: client.get("/v1/threads/course-la", headers=auth).json()["activeRunId"] is None)
    with client.stream("GET", f"/v1/threads/course-la/runs/{run_id}/events?after=1", headers=auth) as r:
        events = read_sse(r)
    assert events[-1][0] == "done" and events[0][0] != "run"
    msgs = client.get("/v1/threads/course-la", headers=auth).json()["messages"]
    assert msgs[-1]["role"] == "assistant" and msgs[-1]["text"]


def test_lost_session_restarts_with_history(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)
    fake_runner.handler = reply_events
    post(client, auth, message="first question")

    def handler(req):
        if req.resume:
            return [RunEvent("result", {"text": "No conversation found with session ID: x", "isError": True, "code": "session_not_found"})]
        return reply_events(req)
    fake_runner.handler = handler
    events = post(client, auth, message="second question")
    assert events[-1][0] == "done"
    retry = fake_runner.requests[-1]
    assert retry.resume is False and "first question" in retry.prompt and GUIDELINES.strip() in retry.prompt
    assert retry.session_id != fake_runner.requests[0].session_id


def test_forget_thread(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)
    fake_runner.handler = reply_events
    post(client, auth)
    assert client.delete("/v1/threads/card-1", headers=auth).status_code == 200
    assert client.get("/v1/threads/card-1", headers=auth).status_code == 404
