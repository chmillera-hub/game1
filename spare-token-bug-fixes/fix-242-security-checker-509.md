# Fix 242: security-checker: no test covers the counts line of the pull request comment when nothing was judged

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): comment.py の _counts_line で未テストの分岐をテストする（3 行）
- Bug report: number 509 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/509))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/242-security-checker-509.patch](fixes/242-security-checker-509.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/242-security-checker-509.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-242-security-checker-509.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-242-security-checker-509.html

## The bug

_counts_line in src/security_checker/github/comment.py has a short form for a report with reviewers and no findings. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_comment_counts_line_no_findings.py checks a report with one reviewer and no findings and a report with scanners only.

## Files changed

- tests/unit/test_comment_counts_line_no_findings.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 242-security-checker-509.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 509.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report names two more lines of the same function (the diff range lines). The new tests do not cover those two lines. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker github comment _counts_line no findings reviewers candidates only untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_comment_counts_line_no_findings.py b/tests/unit/test_comment_counts_line_no_findings.py
new file mode 100644
index 0000000..9901b4a
--- /dev/null
+++ b/tests/unit/test_comment_counts_line_no_findings.py
@@ -0,0 +1,23 @@
+"""PR コメントの件数の行: 判定が 1 件も無いときの表記."""
+
+from __future__ import annotations
+
+from security_checker.github.comment import _counts_line
+from security_checker.models.report import ReviewerRun
+from tests.factories import make_candidate, make_report
+
+
+def test_reviewers_ran_but_nothing_was_judged() -> None:
+    report = make_report(
+        [make_candidate("c1"), make_candidate("c2", line=2)],
+        reviewers=[ReviewerRun(name="r1")],
+    )
+
+    assert _counts_line(report) == ["候補 2 件"]
+
+
+def test_scanners_only_says_that_no_llm_judged() -> None:
+    """対になるケース. Reviewer がいなければ、LLM の判定が無いことを明示する."""
+    report = make_report([make_candidate("c1")])
+
+    assert _counts_line(report) == ["候補 1 件 (スキャナのみ・LLM による判定なし)"]
`````

[Back to the shelf](README.md)
