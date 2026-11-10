# Fix 241: security-checker: no test covers the cost in the footer of the pull request comment

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): comment.py の _footer で未テストの分岐をテストする（1 行）
- Bug report: number 512 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/512))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/241-security-checker-512.patch](fixes/241-security-checker-512.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/241-security-checker-512.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-241-security-checker-512.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-241-security-checker-512.html

## The bug

_footer in src/security_checker/github/comment.py adds the estimated cost when the cost is known. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_comment_footer_cost.py expects the amount with four decimals for a known cost and no dollar sign for an unknown cost and checks the report link.

## Files changed

- tests/unit/test_comment_footer_cost.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 241-security-checker-512.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 512.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker github comment _footer estimated_usd cost_known full report link untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_comment_footer_cost.py b/tests/unit/test_comment_footer_cost.py
new file mode 100644
index 0000000..6b16e19
--- /dev/null
+++ b/tests/unit/test_comment_footer_cost.py
@@ -0,0 +1,29 @@
+"""PR コメントのフッタ: コストが分かるときだけ金額を載せること."""
+
+from __future__ import annotations
+
+from security_checker.github.comment import _footer
+from security_checker.models.verdict import Usage
+from tests.factories import make_candidate, make_report
+
+
+def test_known_cost_is_shown_with_four_decimals() -> None:
+    usage = Usage(estimated_usd=0.01234, cost_known=True)
+    report = make_report([make_candidate()], usage=usage)
+
+    assert " · $0.0123" in _footer(report, None)
+
+
+def test_unknown_cost_is_not_shown() -> None:
+    """対になるケース. 測れなかったコストを 0 ドルのように見せない."""
+    usage = Usage(estimated_usd=None, cost_known=False)
+    report = make_report([make_candidate()], usage=usage)
+
+    assert "$" not in _footer(report, None)
+
+
+def test_report_link_is_added_when_given() -> None:
+    footer = _footer(make_report([make_candidate()]), "https://example.com/run/1")
+
+    assert footer.startswith("<sub>security-checker v2.0.0 · ")
+    assert footer.endswith("[full report](https://example.com/run/1)</sub>")
`````

[Back to the shelf](README.md)
