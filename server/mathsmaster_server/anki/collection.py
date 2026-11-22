"""Read notetypes, decks and deck options from an Anki collection, schema 11 or 18."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field

from . import protobuf as pb


@dataclass
class Template:
    name: str
    qfmt: str
    afmt: str


@dataclass
class Notetype:
    id: int
    name: str
    kind: str  # "normal" | "cloze"
    fields: list[str]
    templates: list[Template]


@dataclass
class Deck:
    id: int
    name: str  # "Parent::Child"
    config_id: int | None
    filtered: bool
    desired_retention: float | None = None


@dataclass
class DeckConfig:
    id: int
    name: str
    fsrs_params: list[float] = field(default_factory=list)
    fsrs_version: int | None = None  # 6, 5 or 4: which parameter set was found
    desired_retention: float | None = None
    learn_steps_min: list[float] = field(default_factory=list)
    relearn_steps_min: list[float] = field(default_factory=list)
    new_per_day: int | None = None
    reviews_per_day: int | None = None
    leech_threshold: int | None = None


@dataclass
class CollectionInfo:
    schema: int
    crt: int  # collection creation (day rollover), epoch seconds
    notetypes: dict[int, Notetype]
    decks: dict[int, Deck]
    configs: dict[int, DeckConfig]
    fsrs_enabled: bool | None


def _has_table(db: sqlite3.Connection, name: str) -> bool:
    return db.execute("select 1 from sqlite_master where type='table' and name=?", (name,)).fetchone() is not None


def _round(xs: list[float]) -> list[float]:
    # float32 -> shortest sensible decimal (0.21199999749660492 -> 0.212)
    return [float(f"{x:.6g}") for x in xs]


def read_collection(db: sqlite3.Connection) -> CollectionInfo:
    ver, crt = db.execute("select ver, crt from col").fetchone()
    if _has_table(db, "notetypes"):
        return _read_schema18(db, ver, crt)
    return _read_schema11(db, ver, crt)


def _read_schema11(db: sqlite3.Connection, ver: int, crt: int) -> CollectionInfo:
    models_json, decks_json, dconf_json, conf_json = db.execute(
        "select models, decks, dconf, conf from col"
    ).fetchone()
    notetypes: dict[int, Notetype] = {}
    for m in json.loads(models_json or "{}").values():
        flds = sorted(m.get("flds", []), key=lambda f: f.get("ord", 0))
        tmpls = sorted(m.get("tmpls", []), key=lambda t: t.get("ord", 0))
        notetypes[int(m["id"])] = Notetype(
            id=int(m["id"]),
            name=m.get("name", ""),
            kind="cloze" if m.get("type") == 1 else "normal",
            fields=[f["name"] for f in flds],
            templates=[Template(t.get("name", ""), t.get("qfmt", ""), t.get("afmt", "")) for t in tmpls],
        )
    decks: dict[int, Deck] = {}
    for d in json.loads(decks_json or "{}").values():
        decks[int(d["id"])] = Deck(
            id=int(d["id"]),
            name=d.get("name", ""),
            config_id=int(d["conf"]) if d.get("conf") is not None and not d.get("dyn") else None,
            filtered=bool(d.get("dyn")),
            desired_retention=d.get("desiredRetention"),
        )
    configs: dict[int, DeckConfig] = {}
    for c in json.loads(dconf_json or "{}").values():
        params, version = [], None
        for key, v in (("fsrsParams6", 6), ("fsrsParams5", 5), ("fsrsWeights", 4)):
            if c.get(key):
                params, version = c[key], v
                break
        configs[int(c["id"])] = DeckConfig(
            id=int(c["id"]),
            name=c.get("name", ""),
            fsrs_params=_round([float(x) for x in params]),
            fsrs_version=version,
            desired_retention=c.get("desiredRetention"),
            learn_steps_min=list(c.get("new", {}).get("delays", [])),
            relearn_steps_min=list(c.get("lapse", {}).get("delays", [])),
            new_per_day=c.get("new", {}).get("perDay"),
            reviews_per_day=c.get("rev", {}).get("perDay"),
            leech_threshold=c.get("lapse", {}).get("leechFails"),
        )
    fsrs = None
    try:
        conf = json.loads(conf_json or "{}")
        if "fsrs" in conf:
            fsrs = bool(conf["fsrs"])
    except json.JSONDecodeError:
        pass
    return CollectionInfo(ver, crt, notetypes, decks, configs, fsrs)


def _read_schema18(db: sqlite3.Connection, ver: int, crt: int) -> CollectionInfo:
    fields_by_nt: dict[int, list[str]] = {}
    for ntid, _ord, name in db.execute("select ntid, ord, name from fields order by ntid, ord"):
        fields_by_nt.setdefault(ntid, []).append(name)
    tmpls_by_nt: dict[int, list[Template]] = {}
    for ntid, _ord, name, config in db.execute("select ntid, ord, name, config from templates order by ntid, ord"):
        f = pb.parse(config)
        tmpls_by_nt.setdefault(ntid, []).append(Template(name, pb.get_str(f, 1), pb.get_str(f, 2)))
    notetypes: dict[int, Notetype] = {}
    for ntid, name, config in db.execute("select id, name, config from notetypes"):
        f = pb.parse(config)
        notetypes[ntid] = Notetype(
            id=ntid,
            name=name,
            kind="cloze" if pb.get_int(f, 1) == 1 else "normal",
            fields=fields_by_nt.get(ntid, []),
            templates=tmpls_by_nt.get(ntid, []),
        )

    decks: dict[int, Deck] = {}
    for did, name, kind in db.execute("select id, name, kind from decks"):
        k = pb.parse(kind)
        normal = pb.get_messages(k, 1)
        decks[did] = Deck(
            id=did,
            name=name.replace("\x1f", "::"),
            config_id=pb.get_int(normal[0], 1, 1) if normal else None,
            filtered=not normal and bool(k.get(2)),
            desired_retention=pb.get_float(normal[0], 10) if normal else None,
        )

    configs: dict[int, DeckConfig] = {}
    for cid, name, config in db.execute("select id, name, config from deck_config"):
        f = pb.parse(config)
        params, version = [], None
        for num, v in ((6, 6), (5, 5), (3, 4)):
            got = pb.get_floats(f, num)
            if got:
                params, version = got, v
                break
        dr = pb.get_float(f, 37)
        configs[cid] = DeckConfig(
            id=cid,
            name=name,
            fsrs_params=_round(params),
            fsrs_version=version,
            desired_retention=float(f"{dr:.4g}") if dr else None,
            learn_steps_min=_round(pb.get_floats(f, 1)),
            relearn_steps_min=_round(pb.get_floats(f, 2)),
            new_per_day=pb.get_int(f, 9) or None,
            reviews_per_day=pb.get_int(f, 10) or None,
            leech_threshold=pb.get_int(f, 22) or None,
        )

    fsrs = None
    if _has_table(db, "config"):
        row = db.execute("select val from config where key='fsrs'").fetchone()
        if row:
            try:
                fsrs = bool(json.loads(row[0]))
            except (TypeError, json.JSONDecodeError):
                pass
    return CollectionInfo(ver, crt, notetypes, decks, configs, fsrs)
