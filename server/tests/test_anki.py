import json
import sqlite3
import zipfile

import pytest

from conftest import FIXTURES, wait_for
from mathsmaster_server.anki import AnkiImportError, convert_package
from mathsmaster_server.anki.convert import card_uuid, label_for, suggest_course
from mathsmaster_server.anki.mathfix import fix_math
from mathsmaster_server.anki.template import render, render_cloze

PACKAGES = ["synthetic.apkg", "synthetic-legacy.apkg", "synthetic.colpkg"]


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    out = {}
    for name in PACKAGES:
        tmp = tmp_path_factory.mktemp(name.replace(".", "-"))
        out[name] = convert_package(FIXTURES / name, tmp / "work", tmp / "media",
                                    [{"id": "c-la", "name": "Linear Algebra"}, {"id": "c-m", "name": "Methods"}])
        out[name]["_media_dir"] = tmp / "media"
    return out


def by_front(result, prefix):
    return next(c for c in result["cards"] if c["front"].startswith(prefix))


@pytest.mark.parametrize("name", PACKAGES)
def test_summary_and_decks(results, name):
    r = results[name]
    assert r["source"]["format"] == {"synthetic.apkg": "anki21b", "synthetic-legacy.apkg": "anki21",
                                     "synthetic.colpkg": "anki21b"}[name]
    s = r["summary"]
    assert (s["cards"], s["notes"], s["reviews"], s["media"], s["suspended"]) == (7, 5, 16, 1, 1)
    decks = {d["name"]: d for d in r["decks"]}
    assert set(decks) == {"Synthetic IB::Linear Algebra", "Synthetic IB::Methods"}
    la = decks["Synthetic IB::Linear Algebra"]
    assert la["cardCount"] == 6 and la["reviewCount"] == 15
    assert la["suggestedCourseId"] == "c-la"
    assert decks["Synthetic IB::Methods"]["suggestedCourseId"] == "c-m"
    sch = la["scheduler"]
    assert sch["fsrsVersion"] == 6 and len(sch["fsrsParams"]) == 21
    assert sch["fsrsParams"][0] == pytest.approx(0.212)
    assert sch["desiredRetention"] == pytest.approx(0.9)
    assert r["warnings"] == []


@pytest.mark.parametrize("name", PACKAGES)
def test_cards_content_and_math_fix(results, name):
    r = results[name]
    ch = by_front(r, "Statement and Proof of the Cayley")
    # $…$ -> \( \), $$…$$ -> \[ \], [$]…[/$] and [$$]…[/$$] too; \$ stays literal.
    assert ch["front"] == "Statement and Proof of the Cayley\\(-\\)Hamilton Theorem"
    assert "\\(\\chi_A(t) = \\det(tI - A)\\)" in ch["back"]
    assert "\\[\\chi_A(A) = 0.\\]" in ch["back"]
    assert "\\(x^2\\)" in ch["back"] and "\\[\\int_0^1 f\\]" in ch["back"]
    assert "\\$5" in ch["back"]
    assert "$" not in ch["back"].replace("\\$", "")
    # The raw Anki fields are kept verbatim.
    assert ch["origin"]["fields"]["Front"] == "Statement and Proof of the Cayley$-$Hamilton Theorem"
    assert ch["label"] == "Theorem" and ch["flagged"] is True and ch["tags"] == ["cayley-hamilton"]

    d = by_front(r, "Definition of an eigenvalue")
    assert d["back"].startswith("<b>1. Definition:</b> \\(\\lambda \\in F\\)")
    assert "<hr" not in d["back"]  # {{FrontSide}}<hr id=answer> removed
    assert d["label"] == "Definition" and d["lecture"] == 13
    assert d["origin"]["kind"] == "anki" and d["origin"]["notetype"] == "Basic"


@pytest.mark.parametrize("name", PACKAGES)
def test_reversed_cloze_and_suspended(results, name):
    r = results[name]
    rev = [c for c in r["cards"] if c["origin"]["notetype"] == "Basic (and reversed card)"]
    assert len(rev) == 2
    fwd, back = sorted(rev, key=lambda c: c["origin"]["ord"])
    assert fwd["front"] == back["back"] and fwd["back"] == back["front"]
    assert back["suspended"] and not fwd["suspended"]
    assert "&lt;" in fwd["back"]  # entities preserved

    clozes = sorted([c for c in r["cards"] if c["origin"]["notetype"] == "Cloze"], key=lambda c: c["origin"]["ord"])
    assert clozes[0]["front"] == "A matrix is diagonalisable iff its <b>[poly]</b> has distinct linear factors."
    assert clozes[1]["front"].endswith("has <b>[…]</b>.")
    assert "<b>minimal polynomial</b>" in clozes[0]["back"] and "Over an algebraically closed field" in clozes[0]["back"]


@pytest.mark.parametrize("name", PACKAGES)
def test_review_history_carries_over(results, name):
    r = results[name]
    ch = by_front(r, "Statement and Proof of the Cayley")
    revs = [x for x in r["reviews"] if x["card"] == ch["id"]]
    assert len(revs) == 10
    assert [x["rating"] for x in revs] == [3, 3, 3, 1, 3, 0, 3, 2, 3, 4]
    assert [x["kind"] for x in revs] == ["learn", "learn", "review", "review", "relearn", "manual",
                                         "review", "review", "filtered", "review"]
    assert revs[0]["ms"] == 41000 and revs[0]["anki"]["intervalSeconds"] == 600
    assert revs[-1]["anki"]["intervalDays"] == 40
    assert all(x["t"].endswith("Z") for x in revs)
    assert revs == sorted(revs, key=lambda x: x["t"])
    snap = ch["anki"]
    assert snap["type"] == "review" and snap["intervalDays"] == 40 and snap["lapses"] == 1 and "dueDate" in snap
    # Cards reviewed by Anki's FSRS carry their memory state.
    d = by_front(r, "Definition of an eigenvalue")
    assert d["anki"]["fsrs"]["stability"] > 0 and 1 <= d["anki"]["fsrs"]["difficulty"] <= 10


def test_ids_are_stable_across_formats_and_runs(results):
    ids = [sorted(c["id"] for c in results[n]["cards"]) for n in PACKAGES]
    assert ids[0] == ids[1] == ids[2]
    rids = [sorted(x["id"] for x in results[n]["reviews"]) for n in PACKAGES]
    assert rids[0] == rids[1] == rids[2] and len(set(rids[0])) == 16
    c = results["synthetic.apkg"]["cards"][0]
    assert c["id"] == card_uuid(c["origin"]["noteGuid"], c["origin"]["ord"])


def test_media_extracted(results):
    for name in PACKAGES:
        r = results[name]
        assert r["media"][0]["name"] == "diagram.png"
        assert r["media"][0]["referencedBy"] == [by_front(r, "Statement and Proof")["id"]]
        assert (r["_media_dir"] / "diagram.png").read_bytes().startswith(b"\x89PNG")


def test_rejects_non_packages(tmp_path):
    bad = tmp_path / "x.apkg"
    bad.write_bytes(b"not a zip")
    with pytest.raises(AnkiImportError) as e:
        convert_package(bad, tmp_path / "w")
    assert e.value.code == "not_a_package"
    empty = tmp_path / "y.apkg"
    with zipfile.ZipFile(empty, "w") as zf:
        zf.writestr("readme.txt", "hi")
    with pytest.raises(AnkiImportError) as e:
        convert_package(empty, tmp_path / "w2")
    assert e.value.code == "not_a_package"


def test_handwritten_schema11_collection(tmp_path):
    """A legacy-1 package (collection.anki2 + JSON media) built by hand, not by Anki."""
    db_path = tmp_path / "collection.anki2"
    db = sqlite3.connect(db_path)
    db.executescript("""
      create table col (id integer primary key, crt integer, mod integer, scm integer, ver integer, dty integer,
        usn integer, ls integer, conf text, models text, decks text, dconf text, tags text);
      create table notes (id integer primary key, guid text, mid integer, mod integer, usn integer, tags text,
        flds text, sfld text, csum integer, flags integer, data text);
      create table cards (id integer primary key, nid integer, did integer, ord integer, mod integer, usn integer,
        type integer, queue integer, due integer, ivl integer, factor integer, reps integer, lapses integer,
        left integer, odue integer, odid integer, flags integer, data text);
      create table revlog (id integer primary key, cid integer, usn integer, ease integer, ivl integer,
        lastIvl integer, factor integer, time integer, type integer);
    """)
    models = {"11": {"id": 11, "name": "Basic", "type": 0, "flds": [{"name": "Front", "ord": 0}, {"name": "Back", "ord": 1}],
                     "tmpls": [{"name": "Card 1", "ord": 0, "qfmt": "{{Front}}", "afmt": "{{FrontSide}}<hr id=answer>{{Back}}"}]}}
    decks = {"22": {"id": 22, "name": "Groups", "conf": 1, "dyn": 0}}
    dconf = {"1": {"id": 1, "name": "Default", "new": {"delays": [1, 10], "perDay": 20}, "lapse": {"delays": [10], "leechFails": 8}, "rev": {"perDay": 200}}}
    db.execute("insert into col values (1, 1700000000, 0, 0, 11, 0, 0, 0, '{}', ?, ?, ?, '{}')",
               (json.dumps(models), json.dumps(decks), json.dumps(dconf)))
    db.execute("insert into notes values (100, 'abc', 11, 1700000000, 0, ' t1 ', ?, '', 0, 0, '')",
               ("Definition of a group\x1fA set with $e$ and $$ab$$",))
    db.execute("insert into cards values (200, 100, 22, 0, 1700000000, 0, 2, 2, 10, 5, 2500, 3, 0, 0, 0, 0, 0, '')")
    db.execute("insert into revlog values (1700000000000, 200, 0, 3, 1, 0, 2500, 5000, 0)")
    db.commit()
    db.close()
    pkg = tmp_path / "hand.apkg"
    with zipfile.ZipFile(pkg, "w") as zf:
        zf.write(db_path, "collection.anki2")
        zf.writestr("media", "{}")
    r = convert_package(pkg, tmp_path / "w")
    assert r["source"]["format"] == "anki2"
    c = r["cards"][0]
    assert c["back"] == "A set with \\(e\\) and \\[ab\\]"
    assert c["anki"]["dueDate"] == "2023-11-24"
    assert r["reviews"][0]["rating"] == 3 and r["decks"][0]["scheduler"]["fsrsParams"] is None


@pytest.mark.parametrize("src,expected,warns", [
    ("plain", "plain", 0),
    ("$x$", "\\(x\\)", 0),
    ("a $$y$$ b", "a \\[y\\] b", 0),
    ("cost \\$5 and $z$", "cost \\$5 and \\(z\\)", 0),
    ("one $ lonely", "one $ lonely", 1),
    ("[$]a[/$] [$$]b[/$$]", "\\(a\\) \\[b\\]", 0),
    ("$a$ then $$b$$ then $c$", "\\(a\\) then \\[b\\] then \\(c\\)", 0),
    ("already \\(x\\)", "already \\(x\\)", 0),
])
def test_fix_math(src, expected, warns):
    out, w = fix_math(src)
    assert out == expected and len(w) == warns


def test_template_renderer():
    fields = {"Front": "F", "Back": "B", "Extra": ""}
    assert render("{{Front}}{{#Extra}} [{{Extra}}]{{/Extra}}{{^Extra}} none{{/Extra}}", fields, ord_=0, side="q") == "F none"
    assert render("{{text:Front}} {{type:Back}}", {"Front": "<b>F</b>", "Back": "B"}, ord_=0, side="q") == "F "
    assert render("{{type:Back}}", {"Back": "B"}, ord_=0, side="a") == "B"
    assert render("{{Missing}}x", fields, ord_=0, side="q") == "x"
    assert render_cloze("{{c1::a}} {{c2::b::hint}}", 1, "q") == "a <b>[hint]</b>"
    assert render_cloze("{{c1::a}} {{c2::b::hint}}", 1, "a") == "a <b>b</b>"


def test_labels_and_course_matching():
    assert label_for("Definition of a ring") == "Definition"
    assert label_for("<b>Statement and Proof of</b> Sylow") == "Theorem"
    assert label_for("Practice: compute") == "Practice"
    assert label_for("Why?") == "Other"
    courses = [{"id": "a", "name": "Analysis and Topology"}, {"id": "b", "name": "Methods"}]
    assert suggest_course("IB::Methods", courses) == "b"
    assert suggest_course("Analysis and Topology", courses) == "a"
    assert suggest_course("Quantum", courses) is None


# ---------------------------------------------------------------------------- over HTTP

def test_import_endpoint_end_to_end(client, auth, settings):
    from conftest import make_library

    make_library(settings.mirror_dir)
    body = (FIXTURES / "synthetic.apkg").read_bytes()
    r = client.post("/v1/imports?filename=Synthetic.apkg", content=body, headers=auth)
    assert r.status_code == 202, r.text
    imp = r.json()
    st = wait_for(lambda: (s := client.get(f"/v1/imports/{imp['id']}", headers=auth).json())["status"] in ("succeeded", "failed") and s)
    assert st["status"] == "succeeded", st
    assert st["summary"]["cards"] == 7
    assert {d["suggestedCourseId"] for d in st["decks"]} == {"course-la", None}
    res = client.get(f"/v1/imports/{imp['id']}/result", headers=auth).json()
    assert res["id"] == imp["id"] and res["source"]["filename"] == "Synthetic.apkg" and len(res["reviews"]) == 16
    m = client.get(f"/v1/imports/{imp['id']}/media/diagram.png", headers=auth)
    assert m.status_code == 200 and m.content.startswith(b"\x89PNG")
    assert client.get(f"/v1/imports/{imp['id']}/media/..%2Fstatus.json", headers=auth).status_code == 404
    # The uploaded deck is not kept on the server.
    assert not (settings.data_dir / "imports" / imp["id"] / "upload.apkg").exists()
    assert client.delete(f"/v1/imports/{imp['id']}", headers=auth).status_code == 200
    assert client.get(f"/v1/imports/{imp['id']}", headers=auth).status_code == 404


def test_import_bad_upload(client, auth):
    r = client.post("/v1/imports", content=b"garbage", headers=auth)
    st = wait_for(lambda: (s := client.get(f"/v1/imports/{r.json()['id']}", headers=auth).json())["status"] != "queued" and s["status"] != "running" and s)
    assert st["status"] == "failed" and st["error"]["code"] == "not_a_package"
    assert client.post("/v1/imports", content=b"", headers=auth).json()["error"]["code"] == "empty_upload"
