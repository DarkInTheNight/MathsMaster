# MathsMaster VPS service

The companion service that runs on the owner's Linux VPS (DESIGN.md §7.7, workstream D). It does three things and nothing else:

1. **Backup mirror** of the library folder: the app uploads changed files; the VPS keeps a plain copy (plus nightly restic snapshots). It is not the live sync; iCloud Drive does that.
2. **Anki import:** `.apkg`/`.colpkg` in, cards (Anki-compatible HTML + MathJax with `\( \)` / `\[ \]`) plus the full review history out, so FSRS carries on where Anki left off.
3. **Claude runtime:** batch jobs (course → cards, enhance deck, explain, check my attempt, transcribe) and per-card threads, run by headless Claude Code (`claude -p`, Opus 5.5) signed in with the owner's subscription. Every request gets the whole course plus the owner's `AI/card-guidelines.md` from the mirror.

- **API spec for the app:** [API.md](API.md) (and the generated [openapi.json](openapi.json)).
- **Stack:** Python 3.11+, FastAPI + uvicorn, stdlib SQLite, `zstandard`. Three runtime dependencies, pinned in `requirements.lock`. State is plain files under one data directory; no database to run.

```
server/
├── mathsmaster_server/
│   ├── app.py            HTTP routes
│   ├── auth.py           per-device bearer tokens (hashed)
│   ├── mirror.py         backup mirror
│   ├── imports.py        Anki import jobs
│   ├── anki/             .apkg reader, template renderer, $→\( \) fix, converter
│   ├── claude/           runner (CLI + fake), workspaces, prompts, validator, jobs, threads
│   └── cli.py            serve · token · import-apkg · doctor · openapi
├── tests/                pytest; synthetic Anki fixtures made with the official anki package
├── deploy/               systemd units, env example, Caddyfile, restic timer, install.sh
├── API.md · openapi.json
└── requirements.lock
```

## Run it locally

```bash
cd server
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock -e ".[test]"
.venv/bin/python -m pytest -q                       # the full suite, no Claude login needed

export MM_DATA_DIR=$PWD/data MM_PORT=8787
.venv/bin/mathsmaster-server token add "dev"         # prints a token
MM_CLAUDE_RUNNER=fake .venv/bin/mathsmaster-server serve   # fake = canned Claude replies
curl -H "Authorization: Bearer mm_…" localhost:8787/v1/status
```

Convert a deck offline, no server: `mathsmaster-server import-apkg deck.apkg -o deck.json --media ./media`.

## Deploy guide

Written for Debian 12 / Ubuntu 22.04+ (anything with systemd and Python ≥ 3.11 works). 1 vCPU / 1 GB RAM is enough for the service; Claude Code itself wants about 1 GB more while a job runs. Disk: about 1 GB a year for the mirror (DESIGN.md §7.8), plus snapshots.

### 1. Install the service

```bash
sudo apt install -y python3 python3-venv git
git clone https://github.com/DarkInTheNight/MathsMaster.git /srv/mathsmaster-src
cd /srv/mathsmaster-src/server
sudo ./deploy/install.sh
```

`install.sh` creates a `mathsmaster` system user (with a home, for Claude Code's login), `/var/lib/mathsmaster` (data), `/opt/mathsmaster/venv`, `/etc/mathsmaster/mathsmaster.env` (from the example) and the `mathsmaster.service` systemd unit, then starts it on `127.0.0.1:8787`. To update later: `git pull && sudo ./deploy/install.sh`.

### 2. Install Claude Code and sign in (as the service user)

Claude jobs run as the `mathsmaster` user, so Claude Code must be installed and signed in **for that user**:

```bash
sudo -iu mathsmaster
curl -fsSL https://claude.ai/install.sh | bash      # native installer → ~/.local/bin/claude
claude                                               # then /login: choose the Claude subscription,
                                                     # open the URL on any device, paste the code back
exit
```

The login lives in `/home/mathsmaster/.claude/` on the VPS and nowhere else. **Alternative:** run `claude setup-token` (on the VPS or any machine where you're signed in), and put the token it prints in `/etc/mathsmaster/mathsmaster.env` as `CLAUDE_CODE_OAUTH_TOKEN=…` (that file is `chmod 600` and never in the repo).

Check it:

```bash
sudo -u mathsmaster env $(sudo cat /etc/mathsmaster/mathsmaster.env | xargs) \
  PATH=/home/mathsmaster/.local/bin:$PATH /opt/mathsmaster/venv/bin/mathsmaster-server doctor --live
```

`doctor --live` makes one tiny real call (`Reply with exactly: OK`) on the configured model and reports `claude_auth` if the login is missing.

### 3. Make it reachable: pick one

The service only listens on localhost; something in front provides the network path and TLS.

**A. Tailscale (private, recommended if you already use it).** No ports open to the internet.

```bash
curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up
sudo tailscale serve --bg 8787        # https://<vps-name>.<tailnet>.ts.net → 127.0.0.1:8787
```

Install Tailscale on the iPad and iPhone; the app's base URL is `https://<vps-name>.<tailnet>.ts.net`. (MagicDNS and HTTPS certificates must be enabled in the Tailscale admin console.)

**B. A subdomain behind Caddy (public HTTPS).** Point `mm.example.com` at the VPS, open ports 80/443, then:

```bash
sudo apt install -y caddy
sudo cp deploy/Caddyfile.example /etc/caddy/Caddyfile   # edit the host name
sudo systemctl reload caddy
```

The app's base URL is `https://mm.example.com`. The device tokens are the only gate, so keep them secret; revoke a lost device with `token revoke`.

### 4. Create a token per device

```bash
sudo -u mathsmaster /opt/mathsmaster/venv/bin/mathsmaster-server token add "iPad · Playgrounds"
sudo -u mathsmaster /opt/mathsmaster/venv/bin/mathsmaster-server token add "iPad · SideStore"
sudo -u mathsmaster /opt/mathsmaster/venv/bin/mathsmaster-server token add "iPhone"
```

Each prints a token once. Enter it in that app copy (Settings → VPS); it lives in that copy's Keychain. `token list`, `token revoke NAME` manage them; changes apply immediately, no restart.

### 5. Nightly snapshots (optional but recommended)

```bash
sudo apt install -y restic
sudo -u mathsmaster sh -c 'head -c 32 /dev/urandom | base64 > /home/mathsmaster/.restic-pass && chmod 600 /home/mathsmaster/.restic-pass'
printf 'RESTIC_REPOSITORY=/var/lib/mathsmaster-snapshots\nRESTIC_PASSWORD_FILE=/home/mathsmaster/.restic-pass\n' | sudo tee /etc/mathsmaster/restic.env
sudo install -d -o mathsmaster /var/lib/mathsmaster-snapshots
sudo -u mathsmaster env $(cat /etc/mathsmaster/restic.env | xargs) restic init
sudo cp deploy/mathsmaster-snapshot.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now mathsmaster-snapshot.timer
```

Keeps 90 daily snapshots of the mirror. A snapshot repository on another machine or a bucket (restic supports S3/B2/SFTP) protects against losing the VPS itself; keep the password somewhere safe.

### 6. Logs and operations

```bash
journalctl -u mathsmaster -f              # service log
systemctl restart mathsmaster             # running jobs are re-queued on start
ls /var/lib/mathsmaster                   # mirror/ jobs/ threads/ imports/ workspaces/ trash/ tokens.json
```

## Configuration

All settings are environment variables (see [`deploy/mathsmaster.env.example`](deploy/mathsmaster.env.example)):

| Variable | Default | |
|---|---|---|
| `MM_DATA_DIR` | `/var/lib/mathsmaster` | everything the service stores |
| `MM_HOST`, `MM_PORT` | `127.0.0.1`, `8787` | listen address |
| `MM_TOKENS_FILE` | `$MM_DATA_DIR/tokens.json` | hashed device tokens |
| `MM_CLAUDE_RUNNER` | `cli` | `fake` = canned replies (demo/dev) |
| `MM_CLAUDE_BIN` | `claude` | path to Claude Code |
| `MM_CLAUDE_MODEL` | `claude-opus-5-5` | |
| `MM_CLAUDE_EFFORT_JOBS` / `_THREADS` | `high` / Claude Code default | `--effort` |
| `MM_CLAUDE_TOOLS` | `Read,Glob,Grep,Write,Edit` | tools Claude may use (`--tools` and `--allowedTools`); no Bash or web by default |
| `MM_CLAUDE_EXTRA_ARGS` | | extra flags, e.g. `--max-turns 200` |
| `MM_JOB_CONCURRENCY`, `MM_THREAD_CONCURRENCY` | 1, 2 | |
| `MM_JOB_TIMEOUT_S`, `MM_THREAD_TIMEOUT_S` | 21600, 1800 | |
| `MM_FIX_ROUNDS` | 2 | times Claude is asked to fix failed checks |
| `MM_MAX_UPLOAD_MB` | 1024 | per file / package |
| `MM_TRASH_DAYS` | 30 | deleted mirror files and unclaimed imports |
| `CLAUDE_CODE_OAUTH_TOKEN` | | optional, from `claude setup-token` |

## How the Claude side works

- **Workspace per course** (`$MM_DATA_DIR/workspaces/<courseId>/`): before every run the mirrored course folder is copied in (changed files only; PencilKit `.drawing` files, `attempts/` and `threads/` skipped) with the guidelines next to it. Claude runs there, never in the mirror, so a stray edit can't touch the backup. The path is stable, which is what lets Claude Code resume a thread's session.
- **Prompt:** the first turn of every session carries the app adapter ([`claude/prompts/app-adapter.md`](mathsmaster_server/claude/prompts/app-adapter.md)), the guidelines verbatim, the course's `ai-instructions.md` and a file inventory. Resumed thread turns repeat it only when those files changed.
- **Output** is a JSON file Claude writes in `runs/<id>/out/`, not parsed prose. The server runs the guidelines' delivery checks on it (no `$`/`**`, balanced delimiters/braces/environments/tags, the HTML subset, no raw `<`, no contextual numbering or cross-card references, additions-only edits) and resumes the session to fix failures.
- **Swappable runner:** `claude/runner.py` defines the interface. `CliRunner` spawns `claude -p --output-format stream-json`; `FakeRunner` runs a Python callback. Tests use `FakeRunner` and `tests/fake_claude.py` (a stand-in binary that speaks stream-json), so CI never needs a login and no AI ever runs on GitHub Actions.
- **Permissions:** Claude gets file tools only (`Read, Glob, Grep, Write, Edit`). Lecture notes are third-party content, so shell and web access stay off unless you opt in via `MM_CLAUDE_TOOLS`.

## Tests

```bash
cd server && .venv/bin/python -m pytest -q
```

CI runs them on Ubuntu with Python 3.11–3.13 (`.github/workflows/server.yml`), only when `server/` changes. The Anki fixtures in `tests/fixtures/` are synthetic decks generated with the official `anki` package by `tests/fixtures/make_fixtures_with_anki.py`; never commit a real deck. If you change the API, regenerate the spec with `python -m mathsmaster_server openapi > openapi.json` (a test checks it).
