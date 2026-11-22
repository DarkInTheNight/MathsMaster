"""Per-device bearer tokens.

Each app install (iPad Playgrounds copy, iPad SideStore copy, iPhone) gets its
own random token, created on the VPS with `mathsmaster-server token add NAME`.
Only a SHA-256 of each token is stored (tokens.json in the data dir), so the
file leaking doesn't leak usable tokens, and one device can be revoked without
touching the others. The app sends `Authorization: Bearer <token>` and keeps the
token in its Keychain (DESIGN.md §7.6).

Transport security comes from the layer in front: Tailscale (WireGuard, optionally
`tailscale serve` for HTTPS) or Caddy with a real certificate. The service itself
listens on localhost by default.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
from dataclasses import dataclass
from pathlib import Path

from .util import atomic_write_json, new_id, now_iso, read_json

TOKEN_PREFIX = "mm_"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True)
class Device:
    id: str
    name: str


class TokenStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._mtime: float | None = None
        self._by_hash: dict[str, Device] = {}

    def _load(self) -> dict:
        return read_json(self.path, {"devices": []}) or {"devices": []}

    def _refresh(self) -> None:
        try:
            mtime = self.path.stat().st_mtime
        except FileNotFoundError:
            mtime = None
        if mtime == self._mtime and self._mtime is not None:
            return
        data = self._load()
        self._by_hash = {
            d["sha256"]: Device(d["id"], d["name"])
            for d in data.get("devices", [])
            if not d.get("revoked")
        }
        self._mtime = mtime

    def verify(self, token: str) -> Device | None:
        if not token or not token.startswith(TOKEN_PREFIX) or len(token) > 200:
            return None
        with self._lock:
            self._refresh()
            h = hash_token(token)
            for known, device in self._by_hash.items():
                if secrets.compare_digest(known, h):
                    return device
        return None

    def add(self, name: str) -> tuple[Device, str]:
        token = TOKEN_PREFIX + secrets.token_urlsafe(32)
        with self._lock:
            data = self._load()
            device = Device(new_id("dev"), name)
            data.setdefault("devices", []).append(
                {"id": device.id, "name": name, "sha256": hash_token(token), "createdAt": now_iso(), "revoked": False}
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(self.path, data)
            try:
                self.path.chmod(0o600)
            except OSError:
                pass
            self._mtime = None
        return device, token

    def list(self) -> list[dict]:
        return [
            {k: d.get(k) for k in ("id", "name", "createdAt", "revoked")}
            for d in self._load().get("devices", [])
        ]

    def revoke(self, ident: str) -> bool:
        with self._lock:
            data = self._load()
            hit = False
            for d in data.get("devices", []):
                if d["id"] == ident or d["name"] == ident:
                    d["revoked"] = True
                    d["revokedAt"] = now_iso()
                    hit = True
            if hit:
                atomic_write_json(self.path, data)
                self._mtime = None
        return hit
