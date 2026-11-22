"""Canned Claude behaviour for tests and demo mode (MM_CLAUDE_RUNNER=fake).

Every prompt we send carries a marker line such as
    <!-- mm:kind=generate_cards out=runs/run_x/out -->
so a fake can tell what was asked and where the output file goes, exactly as
the real model is told in prose. tests/fake_claude.py does the same from a
subprocess, to exercise the real CLI runner.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .runner import RunEvent, RunRequest

MARKER = re.compile(r"<!-- mm:kind=(?P<kind>[a-z_]+) out=(?P<out>\S+) -->")


def canned_output(kind: str) -> tuple[str, dict | list | None, str]:
    """(file name, JSON content, reply text) for a request kind."""
    if kind == "generate_cards":
        return "result.json", {
            "cards": [
                {
                    "front": "Definition of a demo eigenvalue",
                    "back": "<b>1. Definition:</b> \\(\\lambda\\) with \\(Av = \\lambda v\\), \\(v \\neq 0\\).",
                    "label": "Definition",
                    "lecture": 13,
                    "source": {"document": "Lecture notes/notes.pdf", "page": 1},
                    "tags": ["demo"],
                    "status": "new",
                }
            ],
            "report": {"summary": "Demo mode: one canned card.", "possibleErrors": [], "unclear": [], "notDone": []},
        }, "Done: 1 card written."
    if kind == "enhance_cards":
        return "result.json", {"changes": [], "report": {"summary": "Demo mode: no changes.", "possibleErrors": [], "unclear": [], "notDone": []}}, "No changes."
    if kind == "explain":
        return "result.json", {"html": "Demo explanation: \\(1 + 1 = 2\\)."}, "Explained."
    if kind == "check_attempt":
        return "result.json", {"verdict": "minor_issues", "summary": "Demo check.", "html": "Mostly right.", "issues": []}, "Checked."
    if kind == "transcribe":
        return "result.json", {"html": "\\(x^2 + y^2 = 1\\)", "unclear": []}, "Transcribed."
    return "proposals.json", [], "Demo reply: \\(e^{i\\pi} + 1 = 0\\)."


def demo_handler(req: RunRequest) -> list[RunEvent]:
    m = MARKER.search(req.prompt)
    kind = m.group("kind") if m else "thread"
    events = [RunEvent("session", {"sessionId": req.session_id, "model": req.model}),
              RunEvent("status", {"text": "Reading course files"})]
    name, content, reply = canned_output(kind)
    if m:
        out = Path(req.cwd) / m.group("out")
        out.mkdir(parents=True, exist_ok=True)
        if content is not None and (content != [] or name == "proposals.json"):
            (out / name).write_text(json.dumps(content))
    for word in reply.split(" "):
        events.append(RunEvent("delta", {"text": word + " "}))
    events.append(RunEvent("result", {"text": reply, "isError": False, "sessionId": req.session_id,
                                      "costUsd": 0, "durationMs": 1, "numTurns": 1, "usage": {}}))
    return events
