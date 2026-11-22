"""Command line: run the server, manage device tokens, convert a deck offline, check the setup.

    mathsmaster-server serve
    mathsmaster-server token add "iPad · Playgrounds"     (prints the token once)
    mathsmaster-server token list | token revoke NAME_OR_ID
    mathsmaster-server import-apkg deck.apkg -o out.json  (offline conversion, no server needed)
    mathsmaster-server doctor [--live]                     (check data dir, tokens, Claude Code)
    mathsmaster-server openapi > openapi.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

from .config import Settings


def _serve(settings: Settings) -> int:
    import logging

    import uvicorn

    from .app import create_app

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port, proxy_headers=True,
                forwarded_allow_ips="127.0.0.1", log_level="info")
    return 0


def _token(settings: Settings, args) -> int:
    from .auth import TokenStore

    store = TokenStore(settings.tokens_path)
    if args.action == "add":
        if not args.name:
            print("usage: token add NAME", file=sys.stderr)
            return 2
        device, token = store.add(args.name)
        print(f"Device: {device.name} ({device.id})")
        print(f"Token:  {token}")
        print("Enter it in the app (Settings → VPS). It is shown only once; only its hash is stored.")
        return 0
    if args.action == "list":
        for d in store.list():
            print(f"{d['id']}  {d['name']!r}  created {d['createdAt']}{'  REVOKED' if d.get('revoked') else ''}")
        return 0
    if args.action == "revoke":
        ok = store.revoke(args.name or "")
        print("revoked" if ok else "no such device")
        return 0 if ok else 1
    return 2


def _import(args) -> int:
    from .anki import AnkiImportError, convert_package

    with tempfile.TemporaryDirectory(prefix="mm-import-") as tmp:
        media = Path(args.media) if args.media else None
        try:
            result = convert_package(Path(args.package), Path(tmp) / "work", media)
        except AnkiImportError as exc:
            print(f"error ({exc.code}): {exc.message}", file=sys.stderr)
            return 1
    text = json.dumps(result, ensure_ascii=False, indent=1)
    if args.output:
        Path(args.output).write_text(text, "utf-8")
        print(json.dumps(result["summary"]), file=sys.stderr)
    else:
        print(text)
    return 0


def _doctor(settings: Settings, live: bool) -> int:
    from .auth import TokenStore
    from .claude.runner import CliRunner, RunRequest

    ok = True

    def line(good: bool, text: str) -> None:
        nonlocal ok
        ok = ok and good
        print(("  ok   " if good else "  FAIL ") + text)

    print(f"MathsMaster server doctor (data dir {settings.data_dir})")
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        probe = settings.data_dir / ".doctor"
        probe.write_text("x")
        probe.unlink()
        line(True, "data dir is writable")
    except OSError as exc:
        line(False, f"data dir not writable: {exc}")
    devices = [d for d in TokenStore(settings.tokens_path).list() if not d.get("revoked")]
    line(bool(devices), f"{len(devices)} device token(s)" + ("" if devices else ": run `token add NAME`"))
    lib = settings.mirror_dir / "library.json"
    print(f"  info library.json in mirror: {'yes' if lib.is_file() else 'not yet (the app uploads it)'}")
    gl = settings.mirror_dir / "AI" / "card-guidelines.md"
    print(f"  info card guidelines in mirror: {'yes' if gl.is_file() else 'not yet (needed for Claude jobs)'}")
    if settings.claude_runner == "fake":
        print("  info MM_CLAUDE_RUNNER=fake: Claude is simulated")
        return 0 if ok else 1
    runner = CliRunner(settings.claude_bin)
    found = shutil.which(settings.claude_bin)
    line(bool(found), f"Claude Code binary: {found or settings.claude_bin + ' not found on PATH'}")
    if live and found:
        async def ping():
            with tempfile.TemporaryDirectory() as tmp:
                req = RunRequest(prompt="Reply with exactly: OK", cwd=Path(tmp), session_id=str(uuid.uuid4()),
                                 resume=False, model=settings.claude_model, tools="Read", timeout_s=180,
                                 extra_args=settings.claude_extra_args)
                async for ev in runner.run(req):
                    if ev.type in ("result", "error"):
                        return ev
        ev = asyncio.run(ping())
        if ev is None:
            line(False, "Claude Code gave no result")
        elif ev.type == "error" or ev.data.get("isError"):
            line(False, f"Claude Code call failed ({ev.data.get('code')}): {ev.data.get('text') or ev.data.get('message')}")
        else:
            line(True, f"Claude Code answered with {settings.claude_model}: {ev.data.get('text', '')[:40]!r}")
    elif not live:
        print("  info run `doctor --live` to make one tiny real Claude call (checks the login)")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mathsmaster-server")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve", help="run the HTTP server")
    t = sub.add_parser("token", help="manage device tokens")
    t.add_argument("action", choices=["add", "list", "revoke"])
    t.add_argument("name", nargs="?")
    i = sub.add_parser("import-apkg", help="convert an .apkg/.colpkg to the app's JSON, offline")
    i.add_argument("package")
    i.add_argument("-o", "--output")
    i.add_argument("--media", help="folder to write media files into")
    d = sub.add_parser("doctor", help="check the setup")
    d.add_argument("--live", action="store_true", help="make one tiny real Claude call")
    sub.add_parser("openapi", help="print the OpenAPI spec")
    args = parser.parse_args(argv)

    if args.cmd == "import-apkg":
        return _import(args)
    settings = Settings.from_env()
    if args.cmd == "serve":
        return _serve(settings)
    if args.cmd == "token":
        return _token(settings, args)
    if args.cmd == "doctor":
        return _doctor(settings, args.live)
    if args.cmd == "openapi":
        from .app import create_app

        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(Settings(data_dir=Path(tmp)))
            print(json.dumps(app.openapi(), indent=1, ensure_ascii=False))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
