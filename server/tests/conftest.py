from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mathsmaster_server.app import create_app
from mathsmaster_server.auth import TokenStore
from mathsmaster_server.claude.runner import FakeRunner
from mathsmaster_server.config import Settings

FIXTURES = Path(__file__).parent / "fixtures"
FAKE_CLAUDE = Path(__file__).parent / "fake_claude.py"

COURSE_ID = "course-la"
GUIDELINES = "# Card guidelines (synthetic test copy)\n\nMake macroscopic cards. Never use dollar signs.\n"


def make_library(mirror: Path, *, guidelines: bool = True, cards: list[dict] | None = None) -> None:
    """A minimal synthetic library in the mirror: library.json, one course, optional guidelines."""
    (mirror / "Courses" / "Linear Algebra" / "Lecture notes").mkdir(parents=True, exist_ok=True)
    (mirror / "library.json").write_text(json.dumps({
        "schemaVersion": 1,
        "courses": [{"id": COURSE_ID, "name": "Linear Algebra", "folder": "Courses/Linear Algebra"}],
    }))
    course = mirror / "Courses" / "Linear Algebra"
    (course / "Lecture notes" / "notes.pdf").write_bytes(b"%PDF-1.4 synthetic")
    (course / "Lecture notes" / "notes.pdf.ink").mkdir(exist_ok=True)
    (course / "Lecture notes" / "notes.pdf.ink" / "p1.drawing").write_bytes(b"binary ink")
    (course / "ai-instructions.md").write_text("Lectures 1-8 are handwritten.")
    (course / "cards.json").write_text(json.dumps({"schemaVersion": 1, "cards": cards if cards is not None else [
        {"id": "card-1", "front": "Definition of a basis", "back": "ORIGINAL BACK"},
    ]}))
    if guidelines:
        (mirror / "AI").mkdir(exist_ok=True)
        (mirror / "AI" / "card-guidelines.md").write_text(GUIDELINES)


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(data_dir=tmp_path / "data", fix_rounds=2)


@pytest.fixture
def token(settings) -> str:
    _dev, tok = TokenStore(settings.tokens_path).add("test iPad")
    return tok


@pytest.fixture
def auth(token) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fake_runner() -> FakeRunner:
    return FakeRunner()


@pytest.fixture
def client(settings, fake_runner, token):
    app = create_app(settings, runner=fake_runner)
    with TestClient(app) as c:
        yield c


def wait_for(fn, timeout: float = 10.0, interval: float = 0.05):
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = fn()
        if value:
            return value
        time.sleep(interval)
    raise AssertionError("timed out waiting")


def read_sse(response) -> list[tuple[str, dict]]:
    events, etype, data = [], None, None
    for line in response.iter_lines():
        if line.startswith("event: "):
            etype = line[7:]
        elif line.startswith("data: "):
            data = json.loads(line[6:])
        elif line == "" and etype:
            events.append((etype, data))
            etype, data = None, None
    return events
