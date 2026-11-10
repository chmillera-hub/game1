# Fix 260: security-checker: no test covers the lookup of evaluation results by case id

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(eval): runner.py の outcomes_by_case で未テストの分岐をテストする（1 行）
- Bug report: number 504 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/504))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/260-security-checker-504.patch](fixes/260-security-checker-504.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/260-security-checker-504.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-260-security-checker-504.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-260-security-checker-504.html

## The bug

outcomes_by_case in src/security_checker/eval/runner.py builds a mapping from case id to result. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_eval_outcomes_by_case.py checks two results and an empty list.

## Files changed

- tests/unit/test_eval_outcomes_by_case.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 260-security-checker-504.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 504.

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

security-checker eval runner outcomes_by_case case_id mapping untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_eval_outcomes_by_case.py b/tests/unit/test_eval_outcomes_by_case.py
new file mode 100644
index 0000000..00a8e0d
--- /dev/null
+++ b/tests/unit/test_eval_outcomes_by_case.py
@@ -0,0 +1,28 @@
+"""eval.runner.outcomes_by_case: ケース ID から結果を引けること."""
+
+from __future__ import annotations
+
+from security_checker.eval.metrics import CaseOutcome
+from security_checker.eval.runner import outcomes_by_case
+from security_checker.models.enums import FindingStatus, Severity
+
+
+def _outcome(case_id: str, status: FindingStatus) -> CaseOutcome:
+    return CaseOutcome(
+        case_id=case_id,
+        expected_vulnerable=True,
+        expected_severity=Severity.HIGH,
+        status=status,
+        severity=Severity.HIGH,
+    )
+
+
+def test_outcomes_are_indexed_by_case_id() -> None:
+    first = _outcome("hand-0001", FindingStatus.CONFIRMED)
+    second = _outcome("hand-0002", FindingStatus.FALSE_POSITIVE)
+
+    assert outcomes_by_case([first, second]) == {"hand-0001": first, "hand-0002": second}
+
+
+def test_no_outcomes_is_an_empty_mapping() -> None:
+    assert outcomes_by_case([]) == {}
`````

[Back to the shelf](README.md)
