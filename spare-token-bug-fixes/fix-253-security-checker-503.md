# Fix 253: security-checker: no test covers the cost text of the evaluation report

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(eval): runner.py の _usd で未テストの分岐をテストする（3 行）
- Bug report: number 503 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/503))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/253-security-checker-503.patch](fixes/253-security-checker-503.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/253-security-checker-503.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-253-security-checker-503.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-253-security-checker-503.html

## The bug

_usd in src/security_checker/eval/runner.py shows a dash when no total cost exists and a dollar amount otherwise. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_eval_runner_usd.py checks a cost that cannot be measured and a missing total and a known total.

## Files changed

- tests/unit/test_eval_runner_usd.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 253-security-checker-503.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 503.

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

security-checker eval runner _usd total_usd cost_known dash untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_eval_runner_usd.py b/tests/unit/test_eval_runner_usd.py
new file mode 100644
index 0000000..47a4ce7
--- /dev/null
+++ b/tests/unit/test_eval_runner_usd.py
@@ -0,0 +1,18 @@
+"""eval.runner._usd: コストが測れないとき・無いとき・あるときの表記."""
+
+from __future__ import annotations
+
+from security_checker.eval.metrics import Metrics
+from security_checker.eval.runner import _usd
+
+
+def test_unmeasurable_cost_is_not_shown_as_a_number() -> None:
+    assert _usd(Metrics(cost_known=False, total_usd=1.0)).startswith("unknown")
+
+
+def test_missing_total_is_a_dash() -> None:
+    assert _usd(Metrics(cost_known=True, total_usd=None)) == "—"
+
+
+def test_known_total_has_four_decimals() -> None:
+    assert _usd(Metrics(cost_known=True, total_usd=1.5)) == "$1.5000"
`````

[Back to the shelf](README.md)
