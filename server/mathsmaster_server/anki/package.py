"""Open an Anki .apkg / .colpkg and get at its SQLite collection and media.

Package flavours (all are zip files):
  * legacy 1: `collection.anki2` (schema 11), `media` = JSON {"0": "name.png"}
  * legacy 2: `collection.anki21` (schema 11) + a stub collection.anki2
  * latest  : `meta` (protobuf, version 3), `collection.anki21b` = zstd-compressed
              SQLite (schema 18), `media` = zstd protobuf list, and every media
              member zstd-compressed too.
We always prefer the newest collection present.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import zstandard

from . import protobuf as pb

# Guard against zip/zstd bombs: a real collection for a degree's worth of cards
# is a few tens of MB.
MAX_COLLECTION_BYTES = 2 * 1024**3
MAX_MEDIA_FILE_BYTES = 200 * 1024**2


class AnkiImportError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


@dataclass
class AnkiPackage:
    path: Path
    db_path: Path
    format: str  # "anki21b" | "anki21" | "anki2"
    media: dict[str, str] = field(default_factory=dict)  # file name -> zip member
    zstd_media: bool = False

    def read_media(self, name: str) -> bytes:
        member = self.media[name]
        with zipfile.ZipFile(self.path) as zf:
            info = zf.getinfo(member)
            if info.file_size > MAX_MEDIA_FILE_BYTES:
                raise AnkiImportError("media_too_large", f"media file {name} is too large")
            raw = zf.read(member)
        if self.zstd_media:
            reader = zstandard.ZstdDecompressor().stream_reader(raw)
            data = reader.read(MAX_MEDIA_FILE_BYTES + 1)
            if len(data) > MAX_MEDIA_FILE_BYTES:
                raise AnkiImportError("media_too_large", f"media file {name} is too large")
            return data
        return raw


def _copy_limited(src, dst, limit: int) -> None:
    total = 0
    while True:
        chunk = src.read(1 << 20)
        if not chunk:
            return
        total += len(chunk)
        if total > limit:
            raise AnkiImportError("collection_too_large", "collection is larger than the import limit")
        dst.write(chunk)


def open_package(path: Path, workdir: Path) -> AnkiPackage:
    workdir.mkdir(parents=True, exist_ok=True)
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        raise AnkiImportError("not_a_package", "not an .apkg/.colpkg (zip) file") from exc
    with zf:
        names = set(zf.namelist())
        db_path = workdir / "collection.sqlite"
        if "collection.anki21b" in names:
            fmt = "anki21b"
            with zf.open("collection.anki21b") as src, open(db_path, "wb") as dst:
                try:
                    reader = zstandard.ZstdDecompressor().stream_reader(src)
                    _copy_limited(reader, dst, MAX_COLLECTION_BYTES)
                except zstandard.ZstdError as exc:
                    raise AnkiImportError("corrupt_package", "collection.anki21b is not valid zstd") from exc
        elif "collection.anki21" in names or "collection.anki2" in names:
            fmt = "anki21" if "collection.anki21" in names else "anki2"
            member = "collection." + fmt
            if zf.getinfo(member).file_size > MAX_COLLECTION_BYTES:
                raise AnkiImportError("collection_too_large", "collection is larger than the import limit")
            with zf.open(member) as src, open(db_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
        else:
            raise AnkiImportError("not_a_package", "no Anki collection inside the zip")

        latest = False
        if "meta" in names:
            meta = pb.parse(zf.read("meta"))
            latest = pb.get_int(meta, 1) >= 3

        media: dict[str, str] = {}
        if "media" in names:
            raw = zf.read("media")
            if latest:
                try:
                    raw = zstandard.ZstdDecompressor().stream_reader(raw).read(64 * 1024**2)
                except zstandard.ZstdError as exc:
                    raise AnkiImportError("corrupt_package", "media list is not valid zstd") from exc
                entries = pb.get_messages(pb.parse(raw), 1)
                for idx, entry in enumerate(entries):
                    name = pb.get_str(entry, 1)
                    member = str(pb.get_int(entry, 255, idx))
                    if name and member in names:
                        media[name] = member
            else:
                try:
                    mapping = json.loads(raw.decode("utf-8") or "{}")
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise AnkiImportError("corrupt_package", "media list is not valid JSON") from exc
                for member, name in mapping.items():
                    if member in names:
                        media[name] = member

    return AnkiPackage(path=path, db_path=db_path, format=fmt, media=media, zstd_media=latest)
