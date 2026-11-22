#!/usr/bin/env python3
"""Stand-in for the `claude` binary, speaking Claude Code's stream-json format.

Used by the tests to exercise the real subprocess runner without a Claude login.
Behaviour comes from FAKE_CLAUDE_MODE: ok (default) | notloggedin | crash | hang | bad.
Each call appends its argv and prompt to FAKE_CLAUDE_LOG (JSON lines) if set.
"""
import json
import os
import re
import sys
import time


def emit(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main():
    argv = sys.argv[1:]
    prompt = sys.stdin.read()
    mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
    log = os.environ.get("FAKE_CLAUDE_LOG")
    if log:
        with open(log, "a") as fh:
            fh.write(json.dumps({"argv": argv, "prompt": prompt, "cwd": os.getcwd()}) + "\n")
    sid = None
    for flag in ("--session-id", "--resume"):
        if flag in argv:
            sid = argv[argv.index(flag) + 1]
    model = argv[argv.index("--model") + 1] if "--model" in argv else "?"
    emit({"type": "system", "subtype": "init", "cwd": os.getcwd(), "session_id": sid, "tools": ["Read"], "model": model})
    if mode == "crash":
        sys.stderr.write("boom: something broke\n")
        sys.exit(3)
    if mode == "notloggedin":
        emit({"type": "assistant", "message": {"content": [{"type": "text", "text": "Not logged in · Please run /login"}]}, "session_id": sid})
        emit({"type": "result", "subtype": "success", "is_error": True, "result": "Not logged in · Please run /login",
              "session_id": sid, "total_cost_usd": 0, "duration_ms": 5, "num_turns": 1})
        sys.exit(1)
    if mode == "hang":
        time.sleep(30)
    m = re.search(r"<!-- mm:kind=([a-z_]+) out=(\S+) -->", prompt)
    kind, out = (m.group(1), m.group(2)) if m else ("thread", None)
    emit({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": os.path.join(os.getcwd(), "course", "cards.json")}}]},
        "session_id": sid, "parent_tool_use_id": None})
    if out:
        os.makedirs(out, exist_ok=True)
        if kind == "generate_cards":
            front = "Definition of a $bad$ card" if mode == "bad" and "--resume" not in argv else "Definition of a group"
            data = {"cards": [{"front": front, "back": "A set \\(G\\) with an associative operation.", "label": "Definition",
                               "lecture": 1, "source": None, "tags": [], "status": "new"}],
                    "report": {"summary": "1 card", "possibleErrors": [], "unclear": [], "notDone": []}}
            with open(os.path.join(out, "result.json"), "w") as fh:
                json.dump(data, fh)
        elif kind == "thread" and "propose" in prompt:
            with open(os.path.join(out, "proposals.json"), "w") as fh:
                json.dump([{"cardId": "card-1", "back": "ORIGINAL BACK<br>Added line.", "summary": "adds a line"}], fh)
    reply = "Here is the reply \\(x\\)."
    for part in ("Here is ", "the reply ", "\\(x\\)."):
        emit({"type": "stream_event", "event": {"type": "content_block_delta", "index": 0,
              "delta": {"type": "text_delta", "text": part}}, "session_id": sid, "parent_tool_use_id": None})
    emit({"type": "assistant", "message": {"content": [{"type": "text", "text": reply}]}, "session_id": sid})
    emit({"type": "result", "subtype": "success", "is_error": False, "result": reply, "session_id": sid,
          "total_cost_usd": 0.01, "duration_ms": 12, "num_turns": 2, "usage": {"input_tokens": 10, "output_tokens": 5}})


if __name__ == "__main__":
    main()
