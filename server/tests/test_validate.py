import pytest

from mathsmaster_server.claude.validate import additions_only, check_result, lint_html


@pytest.mark.parametrize("text", [
    "Definition of a group",
    "<b>1. Definition:</b> \\(G\\) is a group if \\[ \\forall a,b \\in G: ab \\in G \\]<br><br><ul><li>one</li></ul>",
    "\\(a &lt; b\\) and \\(\\{x\\}\\)",
    "\\[\\begin{aligned} a &= b \\\\ c &= d \\end{aligned}\\]",
    '<svg viewBox="0 0 10 10"><path d="M0 0L10 10" stroke="currentColor"/><text x="1" y="2">A</text></svg>',
    "costs \\$5",
])
def test_clean_text_passes(text):
    assert lint_html(text) == []


@pytest.mark.parametrize("text,needle", [
    ("uses $x$", "$"),
    ("**bold**", "**"),
    ("\\(x", "unclosed"),
    ("x\\)", "unmatched"),
    ("\\(x^{2\\)", "braces"),
    ("\\[\\begin{aligned} a \\end{align}\\]", "match"),
    ("<span>x</span>", "isn't allowed"),
    ("<b>x", "never closed"),
    ("\\(a < b\\)", "raw <"),
    ("By Theorem 3.2 we get", "numbering"),
    ("using equation (5)", "numbering"),
    ("as on the previous card", "another card"),
    ("<script>alert(1)</script>", "isn't allowed"),
])
def test_problems_found(text, needle):
    issues = lint_html(text)
    assert any(needle in i for i in issues), issues


def test_additions_only():
    assert additions_only("abc", "abXc") == {"additionsOnly": True, "insertions": [{"offset": 2, "text": "X"}]}
    r = additions_only("Proof: trivial.", "Proof: <b>Step 1.</b> trivial. <i>Intuition.</i>")
    assert r["additionsOnly"] and len("".join(i["text"] for i in r["insertions"])) == len("<b>Step 1.</b>  <i>Intuition.</i>")
    # removing exactly the insertions gives back the original
    new = "Proof: <b>Step 1.</b> trivial. <i>Intuition.</i>"
    out, last = [], 0
    for ins in r["insertions"]:
        out.append(new[last:ins["offset"]])
        last = ins["offset"] + len(ins["text"])
    out.append(new[last:])
    assert "".join(out) == "Proof: trivial."
    assert additions_only("abc", "abd")["additionsOnly"] is False
    assert additions_only("abc", "acb")["additionsOnly"] is False


def test_check_result_shapes():
    ok = {"cards": [{"front": "Definition of X", "back": "Y", "label": "Definition", "lecture": 2, "tags": []}],
          "report": {"summary": "", "possibleErrors": [], "unclear": [], "notDone": []}}
    assert check_result("generate_cards", ok) == []
    bad = {"cards": [{"front": "$x$", "back": "", "label": "Lemma", "lecture": "two"}]}
    errs = check_result("generate_cards", bad)
    assert any("missing \"report\"" in e or "report" in e for e in errs)
    assert any("label" in e for e in errs) and any("lecture" in e for e in errs) and any("$" in e for e in errs)
    assert check_result("enhance_cards", {"changes": [{"cardId": "zzz", "back": "x"}], "report": {}}, {"a": {}}) \
        == ["changes[0]: unknown cardId zzz"]
    assert check_result("check_attempt", {"verdict": "great", "html": "x"}) != []
    assert check_result("transcribe", {"html": "\\(x\\)"}) == []
    assert check_result("explain", []) == ["result.json must contain a JSON object"]
