#!/usr/bin/env bash
# Install or update the MathsMaster service on a Debian/Ubuntu VPS. Run as root from server/:
#   sudo ./deploy/install.sh
# Idempotent: re-run after `git pull` to update.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PYTHON:-python3}
"$PY" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ needed"'

id mathsmaster >/dev/null 2>&1 || useradd --system --create-home --home-dir /home/mathsmaster --shell /bin/bash mathsmaster
install -d -o mathsmaster -g mathsmaster -m 750 /var/lib/mathsmaster
install -d -m 750 /etc/mathsmaster
install -d -o mathsmaster -g mathsmaster /opt/mathsmaster

if [ ! -x /opt/mathsmaster/venv/bin/python ]; then
  "$PY" -m venv /opt/mathsmaster/venv
fi
/opt/mathsmaster/venv/bin/pip install --quiet --upgrade pip
/opt/mathsmaster/venv/bin/pip install --quiet -r requirements.lock
/opt/mathsmaster/venv/bin/pip install --quiet --no-deps --force-reinstall .

if [ ! -f /etc/mathsmaster/mathsmaster.env ]; then
  install -m 600 deploy/mathsmaster.env.example /etc/mathsmaster/mathsmaster.env
  echo "Created /etc/mathsmaster/mathsmaster.env: review it."
fi
install -m 644 deploy/mathsmaster.service /etc/systemd/system/mathsmaster.service
systemctl daemon-reload
systemctl enable --now mathsmaster
systemctl restart mathsmaster
echo "Installed. Next: sign in to Claude Code as the mathsmaster user and add device tokens (see README.md)."
