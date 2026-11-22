"""Output checks run on the VPS before anything reaches the app (card guidelines §8.2, DESIGN.md §5.4).

* `lint_html`: the delivery checks (no `$`, no `**`, balanced delimiters, braces,
  environments and tags, the allowed HTML subset, no raw `<`, no contextual
  numbering, no references to other cards).
* `additions_only`: an edit may only insert text; deleting exactly the inserted
  text must give back the original character for character (guidelines §6.2).
* `check_result`: per-kind schema checks for the JSON Claude writes.

The app runs the same lint again (DESIGN.md §4.4). A MathJax compile check and
SVG rendering are later additions (see API.md "Not yet").
"""

from __future__ import annotations

import difflib
import re

ALLOWED_TAGS = {"b", "i", "br", "ul", "li", "svg"}
# Elements allowed inside an inline <svg> diagram.
SVG_TAGS = {
    "g", "path", "line", "polyline", "polygon", "rect", "circle", "ellipse", "text", "tspan",
    "defs", "marker", "title", "desc", "use", "clippath", "lineargradient", "radialgradient", "stop",
}
VOID_TAGS = {"br"}
LABELS = {"Definition", "Theorem", "Practice", "Synthesis", "Other"}

_TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9:-]*)((?:\s+[^<>]*?)?)\s*(/?)>")
_NUMBERING = re.compile(
    r"\b(?:Theorem|Lemma|Proposition|Corollary|Definition|Example|Exercise|Remark|Section|Chapter|Equation|Figure)"
    r"\s+\(?\d+(?:\.\d+)*[a-z]?\)?",
    re.I,
)
_EQ_REF = re.compile(r"\b(?:equation|eq\.|eqn\.?)\s*\(\d+(?:\.\d+)*\)", re.I)
_CROSS_CARD = re.compile(r"\b(?:previous|next|earlier|above|following|other|last)\s+card\b|\bsee card\b", re.I)


def _math_segments(text: str) -> tuple[list[str], list[str]]:
    """Split on \\( \\) and \\[ \\]; return (math segments, delimiter problems)."""
    problems: list[str] = []
    segs: list[str] = []
    i = 0
    open_kind: str | None = None
    start = 0
    while i < len(text):
        two = text[i : i + 2]
        if two in ("\\(", "\\["):
            if open_kind:
                problems.append(f"{two} opened inside {open_kind}")
            else:
                open_kind, start = two, i + 2
            i += 2
            continue
        if two in ("\\)", "\\]"):
            want = {"\\)": "\\(", "\\]": "\\["}[two]
            if open_kind != want:
                problems.append(f"unmatched {two}")
            else:
                segs.append(text[start:i])
                open_kind = None
            i += 2
            continue
        if text[i] == "\\":
            i += 2
            continue
        i += 1
    if open_kind:
        problems.append(f"unclosed {open_kind}")
    return segs, problems


def _brace_problems(math: str) -> list[str]:
    depth = 0
    i = 0
    while i < len(math):
        c = math[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth < 0:
                return ["unbalanced braces in maths"]
        i += 1
    return ["unbalanced braces in maths"] if depth else []


def _env_problems(math: str) -> list[str]:
    stack: list[str] = []
    for m in re.finditer(r"\\(begin|end)\{([^}]*)\}", math):
        if m.group(1) == "begin":
            stack.append(m.group(2))
        elif not stack or stack.pop() != m.group(2):
            return [f"\\end{{{m.group(2)}}} doesn't match its \\begin"]
    return [f"\\begin{{{stack[-1]}}} is never closed"] if stack else []


def lint_html(text: str) -> list[str]:
    if not isinstance(text, str):
        return ["not a string"]
    issues: list[str] = []
    for i, c in enumerate(text):
        if c == "$" and (i == 0 or text[i - 1] != "\\"):
            issues.append("uses $ (use \\( \\) or \\[ \\])")
            break
    if "**" in text:
        issues.append("uses ** (use <b>…</b>)")

    segs, delim = _math_segments(text)
    issues += delim
    for seg in segs:
        issues += _brace_problems(seg)
        issues += _env_problems(seg)

    # Tags: allowed subset, balanced; any other `<` is a raw less-than.
    stack: list[str] = []
    pos = 0
    in_svg = 0
    raw_lt = False
    for m in _TAG.finditer(text):
        if "<" in text[pos : m.start()]:
            raw_lt = True
        pos = m.end()
        closing, name, self_closing = m.group(1) == "/", m.group(2).lower(), m.group(4) == "/"
        allowed = name in ALLOWED_TAGS or (in_svg and name in SVG_TAGS)
        if not allowed:
            issues.append(f"tag <{name}> isn't allowed (only <b> <i> <br> <ul> <li> and inline <svg>)")
            continue
        if name == "svg" and not closing and not self_closing:
            in_svg += 1
        if name in VOID_TAGS or self_closing:
            continue
        if closing:
            if not stack or stack[-1] != name:
                issues.append(f"</{name}> doesn't match an open tag")
            else:
                stack.pop()
                if name == "svg":
                    in_svg -= 1
        else:
            stack.append(name)
    if "<" in text[pos:]:
        raw_lt = True
    if stack:
        issues.append(f"<{stack[-1]}> is never closed")
    if raw_lt:
        issues.append("raw < (write &lt;)")
    if _NUMBERING.search(text) or _EQ_REF.search(text):
        issues.append("contextual numbering (e.g. “Theorem 3.2”, “equation (5)”): cards must stand alone")
    if _CROSS_CARD.search(text):
        issues.append("refers to another card: cards must stand alone")
    # de-duplicate, keep order
    return list(dict.fromkeys(issues))


def is_subsequence(original: str, new: str) -> bool:
    it = iter(new)
    return all(ch in it for ch in original)


def additions_only(original: str, new: str) -> dict:
    """{"additionsOnly": bool, "insertions": [{"offset", "text"}]} (offsets into `new`)."""
    if not is_subsequence(original, new):
        return {"additionsOnly": False, "insertions": []}
    sm = difflib.SequenceMatcher(None, original, new, autojunk=False)
    ops = sm.get_opcodes()
    if all(tag in ("equal", "insert") for tag, *_ in ops):
        ins = [{"offset": j1, "text": new[j1:j2]} for tag, _i1, _i2, j1, j2 in ops if tag == "insert"]
    else:
        # difflib chose a non-minimal alignment; fall back to a greedy alignment.
        ins, j, buf_start = [], 0, None
        k = 0
        for j, ch in enumerate(new):
            if k < len(original) and ch == original[k]:
                if buf_start is not None:
                    ins.append({"offset": buf_start, "text": new[buf_start:j]})
                    buf_start = None
                k += 1
            elif buf_start is None:
                buf_start = j
        if buf_start is not None:
            ins.append({"offset": buf_start, "text": new[buf_start:]})
    return {"additionsOnly": True, "insertions": ins}


# --------------------------------------------------------------------------- results

def _str(obj: dict, key: str, where: str, errors: list[str], required: bool = True) -> str | None:
    v = obj.get(key)
    if v is None:
        if required:
            errors.append(f"{where}: missing \"{key}\"")
        return None
    if not isinstance(v, str):
        errors.append(f"{where}: \"{key}\" must be a string")
        return None
    return v


def _report(obj: dict, errors: list[str]) -> None:
    rep = obj.get("report")
    if not isinstance(rep, dict):
        errors.append('missing "report" object')
        return
    for key in ("possibleErrors", "unclear", "notDone"):
        if key in rep and not isinstance(rep[key], list):
            errors.append(f'report.{key} must be a list')


def check_card(card: dict, where: str, errors: list[str]) -> None:
    if not isinstance(card, dict):
        errors.append(f"{where}: must be an object")
        return
    for field in ("front", "back"):
        v = _str(card, field, where, errors)
        if v is not None:
            if not v.strip():
                errors.append(f"{where}.{field}: empty")
            for issue in lint_html(v):
                errors.append(f"{where}.{field}: {issue}")
    label = card.get("label")
    if label is not None and label not in LABELS:
        errors.append(f"{where}.label: must be one of {sorted(LABELS)}")
    if card.get("lecture") is not None and not isinstance(card.get("lecture"), int):
        errors.append(f"{where}.lecture: must be an integer or null")
    if card.get("tags") is not None and not (isinstance(card["tags"], list) and all(isinstance(t, str) for t in card["tags"])):
        errors.append(f"{where}.tags: must be a list of strings")


def check_result(kind: str, data, existing_cards: dict[str, dict] | None = None) -> list[str]:
    """Return a list of human-readable problems ("" list = passed)."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["result.json must contain a JSON object"]
    if kind == "generate_cards":
        cards = data.get("cards")
        if not isinstance(cards, list):
            errors.append('missing "cards" list')
        else:
            for i, c in enumerate(cards):
                check_card(c, f"cards[{i}]", errors)
        _report(data, errors)
    elif kind == "enhance_cards":
        changes = data.get("changes")
        if not isinstance(changes, list):
            errors.append('missing "changes" list')
        else:
            for i, ch in enumerate(changes):
                where = f"changes[{i}]"
                if not isinstance(ch, dict):
                    errors.append(f"{where}: must be an object")
                    continue
                cid = _str(ch, "cardId", where, errors)
                if cid is not None and existing_cards is not None and cid not in existing_cards:
                    errors.append(f"{where}: unknown cardId {cid}")
                for field in ("front", "back"):
                    v = _str(ch, field, where, errors, required=False)
                    if v is not None:
                        for issue in lint_html(v):
                            errors.append(f"{where}.{field}: {issue}")
        _report(data, errors)
    elif kind in ("explain", "transcribe"):
        v = _str(data, "html", "result", errors)
        if v is not None:
            errors += [f"html: {i}" for i in lint_html(v)]
    elif kind == "check_attempt":
        if data.get("verdict") not in ("correct", "minor_issues", "incomplete", "incorrect"):
            errors.append('"verdict" must be one of correct, minor_issues, incomplete, incorrect')
        v = _str(data, "html", "result", errors)
        if v is not None:
            errors += [f"html: {i}" for i in lint_html(v)]
        if "issues" in data and not isinstance(data["issues"], list):
            errors.append('"issues" must be a list')
    else:
        errors.append(f"unknown kind {kind}")
    return errors
