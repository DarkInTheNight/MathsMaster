"""The one approved mechanical fix on import (card guidelines §6.7, DESIGN.md §4.8).

`$…$` -> `\\( … \\)` and `$$…$$` -> `\\[ … \\]`, plus Anki's own `[$]…[/$]` and
`[$$]…[/$$]` LaTeX tags. `\\$` (a literal dollar) is left alone, as is an
unpaired `$`, which is reported as a warning instead of guessed at.
"""

from __future__ import annotations

import re

_ANKI_INLINE = re.compile(r"\[\$\](.*?)\[/\$\]", re.S)
_ANKI_DISPLAY = re.compile(r"\[\$\$\](.*?)\[/\$\$\]", re.S)


def _find_unescaped(s: str, needle: str, start: int) -> int:
    i = start
    while True:
        j = s.find(needle, i)
        if j < 0:
            return -1
        # count preceding backslashes
        k, n = j - 1, 0
        while k >= 0 and s[k] == "\\":
            n += 1
            k -= 1
        if n % 2 == 0:
            if needle == "$" and s.startswith("$$", j):
                # a lone $ closer must not be the start of $$
                i = j + 2
                continue
            return j
        i = j + 1


def fix_math(text: str) -> tuple[str, list[str]]:
    """Return (fixed text, warnings)."""
    warnings: list[str] = []
    text = _ANKI_DISPLAY.sub(lambda m: "\\[" + m.group(1) + "\\]", text)
    text = _ANKI_INLINE.sub(lambda m: "\\(" + m.group(1) + "\\)", text)
    if "[latex]" in text.lower():
        warnings.append("contains an Anki [latex]…[/latex] block, which MathJax can't render; left as is")
    if "$" not in text:
        return text, warnings

    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n:
            out.append(text[i : i + 2])
            i += 2
            continue
        if c != "$":
            out.append(c)
            i += 1
            continue
        if text.startswith("$$", i):
            j = _find_unescaped(text, "$$", i + 2)
            if j < 0:
                warnings.append("unpaired $$ left as is")
                out.append(text[i:])
                break
            out.append("\\[" + text[i + 2 : j] + "\\]")
            i = j + 2
            continue
        j = _find_unescaped(text, "$", i + 1)
        if j < 0:
            warnings.append("unpaired $ left as is")
            out.append(text[i:])
            break
        out.append("\\(" + text[i + 1 : j] + "\\)")
        i = j + 1
    return "".join(out), warnings
