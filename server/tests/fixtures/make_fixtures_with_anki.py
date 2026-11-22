"""Regenerate the synthetic Anki fixtures with the official `anki` Python package.

The committed fixtures (synthetic.apkg, synthetic-legacy.apkg, synthetic.colpkg)
were produced by this script, so the importer is tested against files written by
real Anki code rather than by our own writer. Everything in them is made up:
never commit a real deck.

    python -m venv /tmp/anki-venv && /tmp/anki-venv/bin/pip install anki
    /tmp/anki-venv/bin/python server/tests/fixtures/make_fixtures_with_anki.py

The tests don't need `anki` installed; they only read the committed files.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time

from anki.collection import Collection, ExportAnkiPackageOptions, DeckIdLimit

HERE = os.path.dirname(os.path.abspath(__file__))

# A tiny 1x1 PNG, written as a media file.
PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360f8cf00000301010018dd8db00000000049454e44ae426082"
)

DAY_MS = 86_400_000


def build(tmp: str) -> None:
    col = Collection(os.path.join(tmp, "collection.anki2"))
    col.set_config("fsrs", True)

    parent_did = col.decks.id("Synthetic IB")
    did = col.decks.id("Synthetic IB::Linear Algebra")
    other_did = col.decks.id("Synthetic IB::Methods")

    conf = col.decks.config_dict_for_deck_id(did)
    conf["fsrsParams6"] = [
        0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722,
        0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425,
        0.0912, 0.0658, 0.1542,
    ]
    conf["desiredRetention"] = 0.9
    col.decks.update_config(conf)

    basic = col.models.by_name("Basic")
    reversed_ = col.models.by_name("Basic (and reversed card)")
    cloze = col.models.by_name("Cloze")

    with open(os.path.join(col.media.dir(), "diagram.png"), "wb") as fh:
        fh.write(PNG_1X1)

    def add(model, fields, deck, tags):
        note = col.new_note(model)
        for k, v in fields.items():
            note[k] = v
        note.tags = tags
        col.add_note(note, deck)
        return note

    n_def = add(
        basic,
        {
            "Front": "Definition of an eigenvalue",
            "Back": "<b>1. Definition:</b> \\(\\lambda \\in F\\) is an eigenvalue of "
            "\\(\\alpha \\in L(V)\\) if \\(\\alpha(v) = \\lambda v\\) for some "
            "\\(v \\neq 0\\).<br><br><b>Intuition:</b> a direction that "
            "\\(\\alpha\\) only stretches.",
        },
        did,
        ["eigenvalues", "LA::L13"],
    )
    n_dollar = add(
        basic,
        {
            "Front": "Statement and Proof of the Cayley$-$Hamilton Theorem",
            "Back": "<b>Statement:</b> if $\\chi_A(t) = \\det(tI - A)$ then "
            "$$\\chi_A(A) = 0.$$ It costs \\$5 to print.<br>"
            "<img src=\"diagram.png\"> and [$]x^2[/$] and [$$]\\int_0^1 f[/$$]",
        },
        did,
        ["cayley-hamilton"],
    )
    n_rev = add(
        reversed_,
        {"Front": "\\(\\dim \\ker \\alpha + \\dim \\operatorname{im} \\alpha\\)",
         "Back": "\\(\\dim V\\) (rank&ndash;nullity) &lt; infinity"},
        did,
        [],
    )
    n_cloze = add(
        cloze,
        {"Text": "A matrix is diagonalisable iff its {{c1::minimal polynomial::poly}} "
                 "has {{c2::distinct linear factors}}.",
         "Back Extra": "<i>Over an algebraically closed field.</i>"},
        did,
        ["diagonalisation"],
    )
    n_other = add(
        basic,
        {"Front": "Practice: solve \\(y'' + y = 0\\)",
         "Back": "\\[y = A\\cos x + B\\sin x\\]"},
        other_did,
        [],
    )

    # --- Real reviews through Anki's own scheduler (FSRS on) ------------------
    # The v3 scheduler only answers the card at the top of the queue, so walk
    # the queue: answer cards whose note still has ratings left, bury the rest.
    col.decks.select(parent_did)
    plan = {n_def.id: [3, 3], n_cloze.id: [1, 3, 3], n_other.id: [4]}
    buried = []
    for _ in range(40):
        queued = col.sched.get_queued_cards(fetch_limit=1)
        if not queued.cards:
            break
        card = col.get_card(queued.cards[0].card.id)
        ratings = plan.get(card.nid)
        if ratings:
            card.start_timer()
            col.sched.answerCard(card, ratings.pop(0))
        else:
            col.sched.bury_cards([card.id])
            buried.append(card.id)
    col.sched.unbury_deck(did)
    col.sched.unbury_deck(other_did)

    # --- Backdated history for a "mature" card, written straight to revlog ----
    # Synthetic but shaped exactly like Anki's rows (ids are ms timestamps).
    card = n_dollar.cards()[0]
    now_ms = int(time.time() * 1000)
    start = now_ms - 60 * DAY_MS
    rows = [
        # id, ease, ivl, lastIvl, factor, time(ms), type
        (start, 3, -600, 0, 0, 41_000, 0),                 # learn
        (start + 700_000, 3, 1, -600, 2500, 22_000, 0),    # learn -> graduate
        (start + 1 * DAY_MS, 3, 4, 1, 2500, 30_000, 1),    # review
        (start + 5 * DAY_MS, 1, -600, 4, 2300, 90_000, 1),  # lapse
        (start + 5 * DAY_MS + 600_000, 3, 2, -600, 2300, 25_000, 2),  # relearn
        (start + 7 * DAY_MS, 0, 0, 2, 2300, 0, 4),          # manual (set due date)
        (start + 8 * DAY_MS, 3, 9, 2, 2300, 61_000, 1),
        (start + 17 * DAY_MS, 2, 14, 9, 2150, 120_000, 1),  # hard
        (start + 20 * DAY_MS, 3, 0, 14, 2150, 15_000, 3),   # filtered/cram
        (start + 31 * DAY_MS, 4, 40, 14, 2300, 33_000, 1),  # easy
    ]
    for rid, ease, ivl, last, factor, ms, typ in rows:
        col.db.execute(
            "insert into revlog (id,cid,usn,ease,ivl,lastIvl,factor,time,type) "
            "values (?,?,?,?,?,?,?,?,?)",
            rid, card.id, -1, ease, ivl, last, factor, ms, typ,
        )
    card = col.get_card(card.id)
    card.type = 2
    card.queue = 2
    card.ivl = 40
    card.due = col.sched.today + 11
    card.reps = 9
    card.lapses = 1
    card.factor = 2300
    card.flags = 1  # red flag
    card.memory_state = None
    col.update_card(card)
    # Let Anki compute the FSRS memory state from that history.

    # Suspend the reversed card's second sibling.
    rev_cards = n_rev.cards()
    col.sched.suspend_cards([rev_cards[1].id])


    def export_deck(path, legacy):
        col.export_anki_package(
            out_path=path,
            options=ExportAnkiPackageOptions(
                with_scheduling=True, with_deck_configs=True, with_media=True, legacy=legacy
            ),
            limit=DeckIdLimit(deck_id=parent_did),
        )

    export_deck(os.path.join(HERE, "synthetic.apkg"), legacy=False)
    export_deck(os.path.join(HERE, "synthetic-legacy.apkg"), legacy=True)
    col.export_collection_package(os.path.join(HERE, "synthetic.colpkg"), True, False)
    col.close()


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="mm-anki-fixture-")
    try:
        build(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name in ("synthetic.apkg", "synthetic-legacy.apkg", "synthetic.colpkg"):
        print(name, os.path.getsize(os.path.join(HERE, name)), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
