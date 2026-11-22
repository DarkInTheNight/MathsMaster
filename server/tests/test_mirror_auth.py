import hashlib

import pytest

from mathsmaster_server.auth import TokenStore
from mathsmaster_server.util import BadPath, clean_relpath


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def test_health_needs_no_token(client):
    assert client.get("/v1/health").json() == {"ok": True}


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer nope"}, {"Authorization": "Basic abc"},
                                     {"Authorization": "Bearer mm_wrongtoken"}])
def test_endpoints_need_a_valid_token(client, headers):
    for method, url in [("get", "/v1/status"), ("get", "/v1/manifest"), ("put", "/v1/files/a.txt"),
                        ("get", "/v1/jobs"), ("post", "/v1/imports")]:
        r = getattr(client, method)(url, headers=headers)
        assert r.status_code == 401, (method, url)
        assert r.json()["error"]["code"] == "unauthorized"


def test_status(client, auth):
    s = client.get("/v1/status", headers=auth).json()
    assert s["device"]["name"] == "test iPad"
    assert s["claude"]["runner"] == "fake" and s["claude"]["model"] == "claude-opus-5-5"
    assert s["mirror"]["files"] == 0 and s["guidelines"] is False


def test_put_get_manifest_delete(client, auth, settings):
    body = b'{"schemaVersion":1}'
    r = client.put("/v1/files/Courses/Linear Algèbra/cards.json", content=body,
                   headers={**auth, "X-Content-SHA256": sha(body), "X-Modified": "2026-11-22T09:00:00Z"})
    assert r.status_code == 200, r.text
    assert r.json()["sha256"] == sha(body) and r.json()["modified"] == "2026-11-22T09:00:00Z"

    m = client.get("/v1/manifest", headers=auth).json()
    assert [f["path"] for f in m["files"]] == ["Courses/Linear Algèbra/cards.json"]
    assert m["files"][0]["size"] == len(body) and m["files"] and m["bytes"] == len(body)

    g = client.get("/v1/files/Courses/Linear Algèbra/cards.json", headers=auth)
    assert g.content == body and g.headers["x-content-sha256"] == sha(body)

    # Replace
    body2 = b"v2"
    client.put("/v1/files/Courses/Linear Algèbra/cards.json", content=body2, headers=auth)
    assert client.get("/v1/manifest", headers=auth).json()["files"][0]["sha256"] == sha(body2)

    # Delete moves it to the server trash
    assert client.delete("/v1/files/Courses/Linear Algèbra/cards.json", headers=auth).status_code == 200
    assert client.get("/v1/manifest", headers=auth).json()["files"] == []
    assert list((settings.data_dir / "trash").rglob("cards.json"))
    assert not (settings.mirror_dir / "Courses").exists()  # empty folders tidied
    assert client.delete("/v1/files/nope.txt", headers=auth).status_code == 404


def test_hash_mismatch_rejected_and_nothing_written(client, auth, settings):
    r = client.put("/v1/files/a.bin", content=b"abc", headers={**auth, "X-Content-SHA256": "0" * 64})
    assert r.status_code == 400 and r.json()["error"]["code"] == "hash_mismatch"
    assert not (settings.mirror_dir / "a.bin").exists()
    assert not list(settings.mirror_dir.glob(".tmp-*"))


def test_size_limit(client, auth, settings):
    settings.max_upload_mb = 0
    r = client.put("/v1/files/big.bin", content=b"x" * 10, headers=auth)
    assert r.status_code == 413


def test_files_changed_on_disk_are_rehashed(client, auth, settings):
    client.put("/v1/files/notes.txt", content=b"one", headers=auth)
    (settings.mirror_dir / "notes.txt").write_bytes(b"changed outside the API")
    (settings.mirror_dir / "extra.txt").write_bytes(b"restored by restic")
    files = {f["path"]: f for f in client.get("/v1/manifest", headers=auth).json()["files"]}
    assert files["notes.txt"]["sha256"] == sha(b"changed outside the API")
    assert "extra.txt" in files


@pytest.mark.parametrize("path", ["../etc/passwd", "a/../../b", "a//b", "a/./b", "a\\b", ".DS_Store", "x/\x00y"])
def test_bad_paths_rejected(path):
    with pytest.raises(BadPath):
        clean_relpath(path)


def test_traversal_over_http(client, auth, settings):
    for url in ["/v1/files/..%2F..%2Fsecret", "/v1/files/a/%2E%2E/%2E%2E/x", "/v1/files/a%5Cb"]:
        r = client.put(url, content=b"x", headers=auth)
        assert r.status_code in (400, 404), url
    assert not (settings.data_dir.parent / "secret").exists()


def test_file_folder_conflicts(client, auth):
    client.put("/v1/files/a", content=b"x", headers=auth)
    assert client.put("/v1/files/a/b", content=b"y", headers=auth).status_code == 409
    client.put("/v1/files/d/e", content=b"y", headers=auth)
    assert client.put("/v1/files/d", content=b"z", headers=auth).status_code == 409


def test_token_store(tmp_path):
    store = TokenStore(tmp_path / "tokens.json")
    dev, tok = store.add("iPhone")
    assert tok.startswith("mm_") and store.verify(tok) == dev
    assert tok not in (tmp_path / "tokens.json").read_text()  # only the hash is stored
    other_dev, other = store.add("iPad")
    assert store.revoke("iPhone")
    assert store.verify(tok) is None and store.verify(other) == other_dev
    assert [d["revoked"] for d in store.list()] == [True, False]


def test_revoked_token_rejected_live(client, auth, settings):
    assert client.get("/v1/status", headers=auth).status_code == 200
    TokenStore(settings.tokens_path).revoke("test iPad")
    assert client.get("/v1/status", headers=auth).status_code == 401
