# Fix 270: security-checker: no test covers the summary of the weighted strategy when no reviewer said vulnerable

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(aggregate): weighted.py の _summary で未テストの分岐をテストする（1 行）
- Bug report: number 471 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/471))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/270-security-checker-471.patch](fixes/270-security-checker-471.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/270-security-checker-471.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-270-security-checker-471.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-270-security-checker-471.html

## The bug

WeightedAggregator._summary in src/security_checker/aggregate/weighted.py shows only the weighted score when no reviewer said vulnerable. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_weighted_summary_without_vulnerable.py checks a negative and a positive score with no vulnerable verdict and checks that a vulnerable verdict leads with its headline.

## Files changed

- tests/unit/test_weighted_summary_without_vulnerable.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 270-security-checker-471.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 471.

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

security-checker aggregate weighted _summary score no vulnerable verdicts untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_weighted_summary_without_vulnerable.py b/tests/unit/test_weighted_summary_without_vulnerable.py
new file mode 100644
index 0000000..2932717
--- /dev/null
+++ b/tests/unit/test_weighted_summary_without_vulnerable.py
@@ -0,0 +1,19 @@
+"""WeightedAggregator._summary: 「脆弱」の判定が無いときはスコアだけを見出しにすること."""
+
+from __future__ import annotations
+
+from security_checker.aggregate.weighted import WeightedAggregator
+from tests.factories import make_verdict
+
+
+def test_summary_without_vulnerable_verdicts_is_the_score_alone() -> None:
+    assert WeightedAggregator()._summary([], -0.25) == "重み付きスコア -0.25。"
+    assert WeightedAggregator()._summary([], 0.5) == "重み付きスコア +0.50。"
+
+
+def test_summary_with_a_vulnerable_verdict_leads_with_its_headline() -> None:
+    """対になるケース. 「脆弱」の判定があれば、その見出しの後ろにスコアを添える."""
+    summary = WeightedAggregator()._summary([make_verdict("r1")], 0.5)
+
+    assert summary.endswith(" (重み付きスコア +0.50)")
+    assert not summary.startswith("重み付きスコア")
`````

[Back to the shelf](README.md)
