# Fix 230: security-checker: public names in aggregate/weighted.py have no docstring (__init__ and aggregate and weight_of)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(aggregate): weighted.py の公開クラス・メソッド 3 個に docstring が無い
- Bug report: number 381 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/381))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/230-security-checker-381.patch](fixes/230-security-checker-381.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/230-security-checker-381.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-230-security-checker-381.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-230-security-checker-381.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/aggregate/weighted.py: __init__ and aggregate and weight_of. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/aggregate/weighted.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/aggregate/weighted.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 230-security-checker-381.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 381.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring weighted.py __init__ and aggregate and weight_of

## The full patch

`````diff
diff --git a/src/security_checker/aggregate/weighted.py b/src/security_checker/aggregate/weighted.py
index b8fa4ea..bf119fc 100644
--- a/src/security_checker/aggregate/weighted.py
+++ b/src/security_checker/aggregate/weighted.py
@@ -37,10 +37,12 @@ class WeightedAggregator:
     name = "weighted"
 
     def __init__(self, weights: Mapping[str, float] | None = None) -> None:
+        """`weights` は Reviewer 名 → 重み. 書かれていない Reviewer は等倍."""
         # 設定に書かれていない Reviewer は等倍。重みの解決はここに閉じる
         self.weights = dict(weights or {})
 
     def weight_of(self, verdict: ReviewVerdict) -> float:
+        """この判定を出した Reviewer の重み."""
         return self.weights.get(verdict.reviewer, DEFAULT_WEIGHT)
 
     def aggregate(
@@ -49,6 +51,7 @@ class WeightedAggregator:
         verdicts: list[ReviewVerdict],
         cfg: AggregationConfig,
     ) -> AggregationOutcome:
+        """有効な判定を Reviewer の重みで足し合わせ、1 つの結論にまとめる."""
         valid = [verdict for verdict in verdicts if verdict.status is VerdictStatus.OK]
         if not valid:
             return AggregationOutcome(
`````

[Back to the shelf](README.md)
