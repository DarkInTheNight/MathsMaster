import base64
import json
from pathlib import Path

from conftest import COURSE_ID, GUIDELINES, make_library, wait_for
from mathsmaster_server.claude.fake import MARKER
from mathsmaster_server.claude.runner import RunEvent


def finished(client, auth, job_id):
    return wait_for(lambda: (j := client.get(f"/v1/jobs/{job_id}", headers=auth).json())["status"]
                    in ("succeeded", "failed", "cancelled") and j)


def ok_events(req, text="done"):
    return [RunEvent("session", {"sessionId": req.session_id}), RunEvent("status", {"text": "Reading course/cards.json"}),
            RunEvent("result", {"text": text, "isError": False, "costUsd": 0.5, "durationMs": 10, "numTurns": 3})]


def write_out(req, data, name="result.json"):
    out = Path(req.cwd) / MARKER.search(req.prompt).group("out")
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text(json.dumps(data))


GOOD_CARDS = {"cards": [{"front": "Definition of a vector space", "back": "A set \\(V\\) with …", "label": "Definition",
                         "lecture": 1, "source": {"document": "Lecture notes/notes.pdf", "page": 3}, "tags": [], "status": "new"}],
              "report": {"summary": "1 card", "possibleErrors": [{"document": "notes.pdf", "page": 3, "text": "typo"}],
                         "unclear": [], "notDone": []}}


def test_generate_cards_job(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)

    def handler(req):
        write_out(req, GOOD_CARDS)
        return ok_events(req)
    fake_runner.handler = handler

    r = client.post("/v1/jobs", json={"kind": "generate_cards", "courseId": COURSE_ID, "params": {"lectures": "1-4"}}, headers=auth)
    assert r.status_code == 202, r.text
    job = finished(client, auth, r.json()["id"])
    assert job["status"] == "succeeded", job
    card = job["result"]["cards"][0]
    assert card["origin"] == {"kind": "claude", "job": job["id"]} and len(card["id"]) == 36 and card["lint"] == []
    assert job["checks"] == {"passed": True, "problems": []}
    assert job["result"]["report"]["possibleErrors"][0]["page"] == 3
    assert job["usage"]["costUsd"] == 0.5
    assert any(p["text"] == "Reading course/cards.json" for p in job["progress"])

    req = fake_runner.requests[0]
    # Whole course + guidelines + adapter in the prompt; Opus, high effort, fresh session.
    assert GUIDELINES.strip() in req.prompt
    assert "MathsMaster app adapter" in req.prompt
    assert "Lectures 1-8 are handwritten." in req.prompt  # course ai-instructions.md
    assert "course/Lecture notes/notes.pdf" in req.prompt and "lectures 1-4" in req.prompt
    assert req.model == "claude-opus-5-5" and req.effort == "high" and req.resume is False
    # The workspace is a copy: no ink binaries, and Claude never runs in the mirror.
    ws = Path(req.cwd)
    assert (ws / "course" / "cards.json").is_file() and (ws / "AI" / "card-guidelines.md").read_text() == GUIDELINES
    assert not list(ws.rglob("*.drawing"))
    assert settings.mirror_dir not in ws.parents

    listing = client.get("/v1/jobs", headers=auth).json()["jobs"]
    assert listing[0]["id"] == job["id"] and "result" not in listing[0]


def test_fix_loop_resumes_session(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)
    calls = []

    def handler(req):
        calls.append(req)
        if len(calls) == 1:
            bad = json.loads(json.dumps(GOOD_CARDS))
            bad["cards"][0]["back"] = "uses $x$ and **bold**"
            write_out(req, bad)
        else:
            write_out(req, GOOD_CARDS)
        return ok_events(req)
    fake_runner.handler = handler

    job = finished(client, auth, client.post("/v1/jobs", json={"kind": "generate_cards", "courseId": COURSE_ID}, headers=auth).json()["id"])
    assert job["status"] == "succeeded" and job["checks"]["passed"]
    assert len(calls) == 2
    assert calls[1].resume is True and calls[1].session_id == calls[0].session_id
    assert "uses $" in calls[1].prompt and "**" in calls[1].prompt and GUIDELINES.strip() not in calls[1].prompt


def test_unfixable_output_is_delivered_with_problems(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)
    settings.fix_rounds = 1

    def handler(req):
        bad = json.loads(json.dumps(GOOD_CARDS))
        bad["cards"][0]["front"] = "See Theorem 4.1"
        write_out(req, bad)
        return ok_events(req)
    fake_runner.handler = handler
    job = finished(client, auth, client.post("/v1/jobs", json={"kind": "generate_cards", "courseId": COURSE_ID}, headers=auth).json()["id"])
    assert job["status"] == "succeeded" and job["checks"]["passed"] is False
    assert len(fake_runner.requests) == 2
    assert job["result"]["cards"][0]["lint"]


def test_missing_output_fails(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)
    settings.fix_rounds = 0
    fake_runner.handler = lambda req: ok_events(req)
    job = finished(client, auth, client.post("/v1/jobs", json={"kind": "explain", "courseId": COURSE_ID, "params": {"cardId": "card-1"}}, headers=auth).json()["id"])
    assert job["status"] == "failed" and job["error"]["code"] == "bad_output"


def test_claude_errors_surface(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)
    fake_runner.handler = lambda req: [RunEvent("result", {"text": "Claude AI usage limit reached", "isError": True, "code": "claude_limit"})]
    job = finished(client, auth, client.post("/v1/jobs", json={"kind": "generate_cards", "courseId": COURSE_ID}, headers=auth).json()["id"])
    assert job["status"] == "failed" and job["error"]["code"] == "claude_limit"


def test_request_validation(client, auth, settings):
    r = client.post("/v1/jobs", json={"kind": "generate_cards", "courseId": COURSE_ID}, headers=auth)
    assert r.status_code == 409 and r.json()["error"]["code"] == "library_not_mirrored"
    make_library(settings.mirror_dir, guidelines=False)
    r = client.post("/v1/jobs", json={"kind": "generate_cards", "courseId": COURSE_ID}, headers=auth)
    assert r.status_code == 409 and r.json()["error"]["code"] == "guidelines_missing"
    make_library(settings.mirror_dir)
    assert client.post("/v1/jobs", json={"kind": "generate_cards", "courseId": "nope"}, headers=auth).status_code == 404
    assert client.post("/v1/jobs", json={"kind": "dance", "courseId": COURSE_ID}, headers=auth).status_code == 422
    r = client.post("/v1/jobs", json={"kind": "transcribe", "courseId": COURSE_ID}, headers=auth)
    assert r.json()["error"]["code"] == "attachment_required"
    r = client.post("/v1/jobs", json={"kind": "check_attempt", "courseId": COURSE_ID, "params": {"cardId": "card-1"},
                                      "attachments": [{"mediaType": "image/gif", "data": "AAAA"}]}, headers=auth)
    assert r.json()["error"]["code"] == "bad_attachment"


def test_transcribe_with_attachment(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)
    seen = {}

    def handler(req):
        att = Path(req.cwd) / "runs"
        seen["files"] = sorted(p.name for p in att.rglob("attachments/*"))
        seen["prompt"] = req.prompt
        write_out(req, {"html": "\\(\\int_0^1 x\\,dx\\)", "unclear": []})
        return ok_events(req)
    fake_runner.handler = handler
    png = base64.b64encode(b"\x89PNG fake").decode()
    r = client.post("/v1/jobs", json={"kind": "transcribe", "courseId": COURSE_ID, "params": {"mode": "math"},
                                      "attachments": [{"name": "ink.png", "mediaType": "image/png", "data": png}]}, headers=auth)
    job = finished(client, auth, r.json()["id"])
    assert job["status"] == "succeeded" and job["result"]["html"].startswith("\\(")
    assert seen["files"] == ["01-ink.png"] and "attachments/01-ink.png" in seen["prompt"]
    assert not (settings.data_dir / "uploads" / job["id"]).exists()


def test_enhance_marks_additions_only(client, auth, settings, fake_runner):
    make_library(settings.mirror_dir)

    def handler(req):
        write_out(req, {"changes": [
            {"cardId": "card-1", "back": "ORIGINAL BACK<br><br><b>Intuition:</b> more.", "summary": "intuition"},
            {"cardId": "card-1", "front": "Definition of basis", "summary": "reworded"},
        ], "report": {"summary": "", "possibleErrors": [], "unclear": [], "notDone": []}})
        return ok_events(req)
    fake_runner.handler = handler
    r = client.post("/v1/jobs", json={"kind": "enhance_cards", "courseId": COURSE_ID}, headers=auth)
    job = finished(client, auth, r.json()["id"])
    a, b = job["result"]["changes"]
    assert a["additionsOnly"] is True and a["checks"]["back"]["insertions"][0]["offset"] == len("ORIGINAL BACK")
    assert b["additionsOnly"] is False and b["original"]["front"] == "Definition of a basis"


def test_cancel_queued_and_running(client, auth, settings, fake_runner):
    import asyncio
    make_library(settings.mirror_dir)

    async def slow(req):
        await asyncio.sleep(30)
        return ok_events(req)
    fake_runner.handler = slow
    first = client.post("/v1/jobs", json={"kind": "generate_cards", "courseId": COURSE_ID}, headers=auth).json()
    second = client.post("/v1/jobs", json={"kind": "generate_cards", "courseId": COURSE_ID}, headers=auth).json()
    wait_for(lambda: client.get(f"/v1/jobs/{first['id']}", headers=auth).json()["status"] == "running")
    assert client.get(f"/v1/jobs/{second['id']}", headers=auth).json()["queuePosition"] == 1
    assert client.post(f"/v1/jobs/{second['id']}/cancel", headers=auth).json()["status"] == "cancelled"
    client.post(f"/v1/jobs/{first['id']}/cancel", headers=auth)
    assert finished(client, auth, first["id"])["status"] == "cancelled"


def test_jobs_survive_restart(settings, token, fake_runner):
    from fastapi.testclient import TestClient

    from mathsmaster_server.app import create_app
    make_library(settings.mirror_dir)
    auth = {"Authorization": f"Bearer {token}"}
    jobs_dir = settings.data_dir / "jobs"
    jobs_dir.mkdir(parents=True)
    (jobs_dir / "job_x.json").write_text(json.dumps({
        "id": "job_x", "kind": "explain", "courseId": COURSE_ID, "courseName": "Linear Algebra",
        "params": {"cardId": "card-1"}, "attachments": [], "status": "running", "createdAt": "2026-11-22T00:00:00.000Z",
        "startedAt": "2026-11-22T00:00:01.000Z", "finishedAt": None, "attempts": 1, "sessionId": None, "progress": [],
        "result": None, "checks": None, "error": None, "usage": None, "device": "x"}))

    def handler(req):
        write_out(req, {"html": "ok"})
        return ok_events(req)
    fake_runner.handler = handler
    with TestClient(create_app(settings, runner=fake_runner)) as c:
        job = finished(c, auth, "job_x")
    assert job["status"] == "succeeded" and job["attempts"] == 2
    assert any("restart" in p["text"] for p in job["progress"])
