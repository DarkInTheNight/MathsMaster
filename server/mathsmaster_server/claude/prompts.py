"""Prompt building for jobs and thread turns.

Every first turn of a session carries the app adapter, the owner's card
guidelines verbatim, the course's extra instructions and an inventory of the
course files ("whole course plus guidelines, every time", DESIGN.md §5.1).
Resumed thread turns already have that context, so they repeat it only if the
guidelines or instructions changed since.
"""

from __future__ import annotations

import json
from importlib import resources

from .workspace import Workspace

JOB_KINDS = ("generate_cards", "enhance_cards", "explain", "check_attempt", "transcribe")
INTENTS = ("chat", "explain", "check_attempt")


def adapter_text() -> str:
    return resources.files(__package__).joinpath("prompts/app-adapter.md").read_text("utf-8")


def marker(kind: str, out_rel: str) -> str:
    return f"<!-- mm:kind={kind} out={out_rel} -->"


def context_block(ws: Workspace) -> str:
    cards = ws.cards()
    inventory = "\n".join(f"- {line}" for line in ws.inventory()) or "- (no files yet)"
    return "\n\n".join(
        [
            adapter_text().strip(),
            "# The owner's card guidelines (AI/card-guidelines.md, verbatim)\n\n" + ws.guidelines.strip(),
            "# Extra instructions for this course (course/ai-instructions.md)\n\n"
            + (ws.instructions.strip() or "(none)"),
            f"# The course: {ws.course.name}\n\n"
            f"`course/` is a copy of the library folder `{ws.course.folder}`. "
            f"The existing deck is `course/cards.json` ({len(cards)} cards). Files:\n\n{inventory}",
        ]
    )


def _card_block(card: dict | None, card_id: str | None) -> str:
    if not card:
        return f"(card {card_id} not found in course/cards.json)" if card_id else ""
    shown = {k: card.get(k) for k in ("id", "front", "back", "label", "lecture", "tags", "source") if k in card}
    return "```json\n" + json.dumps(shown, ensure_ascii=False, indent=1) + "\n```"


def _attachments_block(run_id: str, names: list[str]) -> str:
    if not names:
        return ""
    return "Attached with this request (open them with Read):\n" + "\n".join(
        f"- runs/{run_id}/attachments/{n}" for n in names
    )


def job_task(kind: str, params: dict, ws: Workspace, run_id: str, attachments: list[str]) -> str:
    out = f"runs/{run_id}/out/result.json"
    cards = ws.cards()
    extra = (params.get("instructions") or "").strip()
    extra_block = f"\n\nThe student adds: {extra}" if extra else ""
    att = _attachments_block(run_id, attachments)

    if kind == "generate_cards":
        if params.get("lectures"):
            scope = f"lectures {params['lectures']}"
        elif params.get("documents"):
            scope = "these documents: " + ", ".join(f"course/{d}" for d in params["documents"])
        else:
            scope = "the whole course"
        return (
            f"# Task: generate cards for {ws.course.name}, {scope}\n\n"
            "Follow the guidelines' workflow end to end: read all the relevant material first, chunk it, "
            "plan, write the cards, then check them. Don't duplicate cards already in `course/cards.json`; "
            "if an existing card covers something, leave it."
            f"{extra_block}\n\n{att}\n\n"
            f"# Output\n\nWrite `{out}`:\n"
            '{"cards": [{"front": "...", "back": "...", "label": "Theorem", "lecture": 14, '
            '"source": {"document": "Lecture notes/LA notes.pdf", "page": 61}, "tags": ["..."], "status": "new"}], '
            '"report": {"summary": "...", "possibleErrors": [], "unclear": [], "notDone": []}}'
        )
    if kind == "enhance_cards":
        ids = params.get("cardIds") or []
        which = (
            "these cards: " + ", ".join(ids) if ids else f"the whole deck ({len(cards)} cards)"
        )
        return (
            f"# Task: enhance existing cards in {ws.course.name}: {which}\n\n"
            "Apply the guidelines' rules for existing cards. Edits are additions only: keep every character "
            "of the original, only insert. Only list cards you actually change."
            f"{extra_block}\n\n{att}\n\n"
            f"# Output\n\nWrite `{out}`:\n"
            '{"changes": [{"cardId": "<id from cards.json>", "front": "<full new front, or omit if unchanged>", '
            '"back": "<full new back, or omit>", "summary": "what you added and why"}], '
            '"report": {"summary": "...", "possibleErrors": [], "unclear": [], "notDone": []}}'
        )
    card_id = params.get("cardId")
    card = params.get("card") or (cards.get(card_id) if card_id else None)
    if kind == "explain":
        q = (params.get("question") or "").strip()
        return (
            f"# Task: explain a card from {ws.course.name}\n\n{_card_block(card, card_id)}\n\n"
            + (f"The student asks: {q}\n\n" if q else "Explain the card's content so it makes sense: the idea, why each step holds, and how it connects to the rest of the course. Use the lecture notes.\n\n")
            + f"{att}\n\n# Output\n\nWrite `{out}`: " + '{"html": "<the explanation, card HTML subset + MathJax>"}'
        )
    if kind == "check_attempt":
        return (
            f"# Task: check the student's handwritten attempt at this card from {ws.course.name}\n\n"
            f"{_card_block(card, card_id)}\n\n{att}\n\n"
            "Read the attempt (the attached image) carefully, compare it with the card and the course, and say "
            "what is right, what is missing and where the logic slips. Be precise and kind; don't grade for them."
            f"{extra_block}\n\n# Output\n\nWrite `{out}`: "
            '{"verdict": "correct|minor_issues|incomplete|incorrect", "summary": "one line", '
            '"html": "<feedback, card HTML subset + MathJax>", '
            '"issues": [{"quote": "what they wrote", "problem": "...", "suggestion": "..."}]}'
        )
    if kind == "transcribe":
        mode = params.get("mode", "card")
        what = {
            "math": "a single MathJax expression (no surrounding prose)",
            "text": "prose with inline MathJax",
            "card": "card-ready HTML subset + MathJax, keeping the structure (lists, display maths)",
        }.get(mode, "card-ready HTML subset + MathJax")
        return (
            f"# Task: transcribe handwriting from {ws.course.name}\n\n{att}\n\n"
            f"Transcribe the attached handwriting into {what}. Use the course's notation (check the notes when a "
            "symbol is ambiguous). Mark genuinely unreadable parts as [unclear: read as …].\n\n"
            f"# Output\n\nWrite `{out}`: " + '{"html": "...", "unclear": ["..."]}'
        )
    raise ValueError(kind)


def job_prompt(kind: str, params: dict, ws: Workspace, run_id: str, attachments: list[str]) -> str:
    return "\n\n".join(
        [
            marker(kind, f"runs/{run_id}/out"),
            "# MathsMaster request",
            context_block(ws),
            job_task(kind, params, ws, run_id, attachments),
        ]
    )


def fix_prompt(kind: str, run_id: str, errors: list[str]) -> str:
    listed = "\n".join(f"- {e}" for e in errors[:80])
    more = f"\n- … and {len(errors) - 80} more" if len(errors) > 80 else ""
    return (
        f"{marker(kind, f'runs/{run_id}/out')}\n\n"
        f"The server's checks found problems in `runs/{run_id}/out/result.json`:\n\n{listed}{more}\n\n"
        "Fix every one (keeping the rest of your work) and write the complete file again."
    )


def thread_prompt(
    *,
    ws: Workspace,
    run_id: str,
    include_context: bool,
    intent: str,
    message: str,
    card: dict | None,
    card_id: str | None,
    attachments: list[str],
    history: list[dict] | None = None,
) -> str:
    parts = [marker("thread", f"runs/{run_id}/out")]
    if include_context:
        parts += ["# MathsMaster conversation", context_block(ws)]
        if card_id:
            parts.append(
                "# This conversation\n\nIt is the thread for one card. You can propose edits to it (or new "
                "cards); the student applies or rejects them in the app."
            )
        else:
            parts.append(f"# This conversation\n\nIt is the general thread for the course {ws.course.name}.")
        if history:
            lines = [f"**{m['role']}:** {m.get('text', '')}" for m in history[-20:] if m.get("text")]
            if lines:
                parts.append("# Earlier messages in this thread (the previous session was lost)\n\n" + "\n\n".join(lines))
    if card_id or card:
        parts.append("# The card as it is now\n\n" + _card_block(card, card_id))
    if intent == "explain":
        parts.append("The student pressed **Explain**: explain this card so it makes sense, using the course notes.")
    elif intent == "check_attempt":
        parts.append(
            "The student pressed **Check my attempt**: read their handwritten attempt (attached) against the card "
            "and the course. Say what's right, what's missing and where the logic slips, before they grade."
        )
    att = _attachments_block(run_id, attachments)
    if att:
        parts.append(att)
    if message.strip():
        parts.append("# The student says\n\n" + message.strip())
    parts.append(
        "# How to answer\n\nReply in the card HTML subset with MathJax (no Markdown, no $). "
        f"If you propose a change to a card or a new card, also write `runs/{run_id}/out/proposals.json`: "
        '[{"cardId": "<id, or null for a new card>", "front": "<full new front, or omit>", '
        '"back": "<full new back, or omit>", "label": "...", "summary": "what changes and why"}]. '
        "Edits to existing cards must be additions only unless the student asked for a rewrite. "
        "Don't write the file if you're not proposing anything."
    )
    return "\n\n".join(parts)
