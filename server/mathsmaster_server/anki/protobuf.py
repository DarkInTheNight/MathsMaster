"""Just enough protobuf decoding to read Anki's schema-18 config blobs.

Anki ≥ 2.1.50 stores notetype, template, deck and deck-config settings as
protobuf messages inside SQLite, and the newest package format stores its media
list as protobuf too. We only need a handful of fields, so a 40-line decoder
beats a protobuf dependency plus vendored .proto files. Field numbers are from
Anki's proto/anki/*.proto (checked against anki 26.09).
"""

from __future__ import annotations

import struct

Fields = dict[int, list[tuple[int, object]]]


def _varint(buf: bytes, i: int) -> tuple[int, int]:
    shift = result = 0
    while True:
        if i >= len(buf):
            raise ValueError("truncated varint")
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, i
        shift += 7
        if shift > 70:
            raise ValueError("varint too long")


def parse(buf: bytes) -> Fields:
    fields: Fields = {}
    i = 0
    while i < len(buf):
        key, i = _varint(buf, i)
        num, wire = key >> 3, key & 7
        if wire == 0:
            val, i = _varint(buf, i)
        elif wire == 1:
            val, i = buf[i : i + 8], i + 8
        elif wire == 2:
            n, i = _varint(buf, i)
            val, i = buf[i : i + n], i + n
        elif wire == 5:
            val, i = buf[i : i + 4], i + 4
        else:
            raise ValueError(f"unsupported wire type {wire}")
        if i > len(buf):
            raise ValueError("truncated field")
        fields.setdefault(num, []).append((wire, val))
    return fields


def get_int(f: Fields, num: int, default: int = 0) -> int:
    for wire, val in f.get(num, []):
        if wire == 0:
            return int(val)  # type: ignore[arg-type]
    return default


def get_str(f: Fields, num: int, default: str = "") -> str:
    for wire, val in f.get(num, []):
        if wire == 2:
            return bytes(val).decode("utf-8", "replace")  # type: ignore[arg-type]
    return default


def get_bytes(f: Fields, num: int) -> bytes | None:
    for wire, val in f.get(num, []):
        if wire == 2:
            return bytes(val)  # type: ignore[arg-type]
    return None


def get_messages(f: Fields, num: int) -> list[Fields]:
    return [parse(bytes(val)) for wire, val in f.get(num, []) if wire == 2]  # type: ignore[arg-type]


def get_float(f: Fields, num: int) -> float | None:
    for wire, val in f.get(num, []):
        if wire == 5:
            return struct.unpack("<f", val)[0]  # type: ignore[arg-type]
    return None


def get_floats(f: Fields, num: int) -> list[float]:
    """Repeated float: packed (one length-delimited blob) or one fixed32 per value."""
    out: list[float] = []
    for wire, val in f.get(num, []):
        if wire == 2:
            raw = bytes(val)  # type: ignore[arg-type]
            out.extend(struct.unpack(f"<{len(raw) // 4}f", raw[: len(raw) // 4 * 4]))
        elif wire == 5:
            out.append(struct.unpack("<f", val)[0])  # type: ignore[arg-type]
    return out
