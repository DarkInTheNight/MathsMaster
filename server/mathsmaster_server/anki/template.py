"""A small renderer for Anki card templates, enough to turn notes into front/back HTML.

Supports {{Field}}, {{FrontSide}}, {{#Field}}…{{/Field}}, {{^Field}}…{{/Field}},
the common filters (text:, cloze:, type:, hint:, furigana-family pass-through)
and the special fields Tags / Deck / Subdeck / Card / Type. Unknown fields render
empty, as in Anki. The raw note fields are kept alongside the rendered sides in
the import result, so nothing is lost if a template does something exotic.
"""

from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"\{\{(.*?)\}\}", re.S)
_HTML_RE = re.compile(r"<[^>]*>")
_CLOZE_RE = re.compile(r"\{\{c(\d+)::(.*?)(?:::(.*?))?\}\}", re.S)


def strip_html(text: str) -> str:
    return html.unescape(_HTML_RE.sub("", text))


def _nonempty(value: str) -> bool:
    return bool(strip_html(value).strip())


def cloze_numbers(text: str) -> set[int]:
    return {int(m.group(1)) for m in _CLOZE_RE.finditer(text)}


def render_cloze(text: str, ord_: int, side: str) -> str:
    """Render cloze deletions for card number ord_+1. Active deletions become <b>[…]</b>/<b>answer</b>."""
    active = ord_ + 1

    def sub(m: re.Match) -> str:
        num, body, hint = int(m.group(1)), m.group(2), m.group(3)
        if num != active:
            return body
        if side == "q":
            return f"<b>[{hint}]</b>" if hint else "<b>[…]</b>"
        return f"<b>{body}</b>"

    # Nested clozes: repeat until stable (inner first is fine for display).
    prev = None
    while prev != text:
        prev, text = text, _CLOZE_RE.sub(sub, text)
    return text


def _apply_filters(value: str, filters: list[str], ord_: int, side: str) -> str:
    for flt in reversed(filters):  # Anki applies the filter nearest the field first
        flt = flt.strip()
        if flt == "text":
            value = strip_html(value)
        elif flt == "cloze":
            value = render_cloze(value, ord_, side)
        elif flt == "cloze-only":
            value = ", ".join(
                m.group(2) for m in _CLOZE_RE.finditer(value) if int(m.group(1)) == ord_ + 1
            )
        elif flt == "type" or flt.startswith("type"):
            value = "" if side == "q" else value
        elif flt.startswith("tts"):
            value = ""
        # hint, furigana, kana, kanji and unknown filters: pass the value through.
    return value


def render(template: str, fields: dict[str, str], *, ord_: int, side: str, extra: dict[str, str] | None = None) -> str:
    """Render one side ("q" or "a") of a card. `extra` holds special fields (FrontSide, Tags, …)."""
    extra = extra or {}
    lookup = {**{k.lower(): v for k, v in fields.items()}, **{k.lower(): v for k, v in extra.items()}}
    tokens: list[tuple[str, str]] = []
    pos = 0
    for m in _TAG_RE.finditer(template):
        if m.start() > pos:
            tokens.append(("text", template[pos : m.start()]))
        tokens.append(("tag", m.group(1).strip()))
        pos = m.end()
    if pos < len(template):
        tokens.append(("text", template[pos:]))

    def walk(i: int, stop: str | None) -> tuple[str, int]:
        out: list[str] = []
        while i < len(tokens):
            kind, val = tokens[i]
            if kind == "text":
                out.append(val)
                i += 1
                continue
            if val.startswith("/"):
                if stop is not None and val[1:].strip().lower() == stop:
                    return "".join(out), i + 1
                i += 1  # stray close tag: ignore
                continue
            if val.startswith("#") or val.startswith("^"):
                name = val[1:].strip()
                inner, i = walk(i + 1, name.lower())
                present = _nonempty(lookup.get(name.lower(), ""))
                if name.lower().startswith("c") and name[1:].isdigit():
                    present = int(name[1:]) == ord_ + 1
                if present == (val[0] == "#"):
                    out.append(inner)
                continue
            parts = val.split(":")
            name, filters = parts[-1].strip(), parts[:-1]
            value = lookup.get(name.lower(), "")
            out.append(_apply_filters(value, filters, ord_, side) if filters else value)
            i += 1
        return "".join(out), i

    rendered, _ = walk(0, None)
    return rendered


_ANSWER_HR = re.compile(r"^\s*(?:<br\s*/?>\s*)*<hr\s+id=[\"']?answer[\"']?\s*/?>\s*", re.I)


def answer_only(back_html: str) -> str:
    """Drop the leading `<hr id=answer>` left after removing {{FrontSide}} from an answer template."""
    return _ANSWER_HR.sub("", back_html, count=1).strip()
