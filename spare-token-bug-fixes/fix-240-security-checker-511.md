# Fix 240: security-checker: no test covers the row limit of the candidates table in the pull request comment

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): comment.py の _candidate_table で未テストの分岐をテストする（1 行）
- Bug report: number 511 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/511))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/240-security-checker-511.patch](fixes/240-security-checker-511.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/240-security-checker-511.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-240-security-checker-511.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-240-security-checker-511.html

## The bug

_candidate_table in src/security_checker/github/comment.py lists at most 15 rows and then says how many more exist. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_comment_candidate_table_limit.py builds 17 candidates and expects 15 rows plus the note for 2 more. A second test builds exactly 15 and expects no note.

## Files changed

- tests/unit/test_comment_candidate_table_limit.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 240-security-checker-511.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 511.

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

security-checker github comment _candidate_table MAX_SUMMARY_FINDINGS remaining rows untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_comment_candidate_table_limit.py b/tests/unit/test_comment_candidate_table_limit.py
new file mode 100644
index 0000000..c8bd149
--- /dev/null
+++ b/tests/unit/test_comment_candidate_table_limit.py
@@ -0,0 +1,26 @@
+"""PR コメントの候補表: 上限を超えた分は件数だけを示すこと."""
+
+from __future__ import annotations
+
+from security_checker.github.comment import MAX_SUMMARY_FINDINGS, _candidate_table
+from security_checker.models.candidate import Candidate
+from tests.factories import make_candidate, make_report
+
+
+def _many(count: int) -> list[Candidate]:
+    return [make_candidate(f"c{index}", line=index + 1) for index in range(count)]
+
+
+def test_rows_past_the_limit_are_counted_not_listed() -> None:
+    lines = _candidate_table(make_report(_many(MAX_SUMMARY_FINDINGS + 2)))
+
+    assert "\n_ほか 2 件_" in lines
+    assert sum("`semgrep`" in line for line in lines) == MAX_SUMMARY_FINDINGS
+
+
+def test_exactly_the_limit_has_no_note() -> None:
+    """境界. ちょうど上限の件数なら注記は出ない."""
+    lines = _candidate_table(make_report(_many(MAX_SUMMARY_FINDINGS)))
+
+    assert not any("ほか" in line for line in lines)
+    assert sum("`semgrep`" in line for line in lines) == MAX_SUMMARY_FINDINGS
`````

[Back to the shelf](README.md)
