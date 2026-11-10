# Fix 231: security-checker: public names in aggregate/consensus.py have no docstring (__init__ and aggregate)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(aggregate): consensus.py の公開クラス・メソッド 2 個に docstring が無い
- Bug report: number 380 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/380))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/231-security-checker-380.patch](fixes/231-security-checker-380.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/231-security-checker-380.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-231-security-checker-380.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-231-security-checker-380.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/aggregate/consensus.py: __init__ and aggregate. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/aggregate/consensus.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/aggregate/consensus.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 231-security-checker-380.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 380.

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

security-checker docstring D1 ruff missing docstring consensus.py __init__ and aggregate

## The full patch

`````diff
diff --git a/src/security_checker/aggregate/consensus.py b/src/security_checker/aggregate/consensus.py
index eb5bd04..64272df 100644
--- a/src/security_checker/aggregate/consensus.py
+++ b/src/security_checker/aggregate/consensus.py
@@ -32,6 +32,7 @@ class ConsensusAggregator:
     name = "consensus"
 
     def __init__(self, weights: Mapping[str, float] | None = None) -> None:
+        """`weights` は Reviewer 名 → 重み. 票の数え方には使わず、severity の加重平均にだけ使う."""
         # 票の数え方に重みは使わない。使うのは severity: weighted_mean のときだけ (§14.1)
         self.weights = dict(weights or {})
 
@@ -44,6 +45,7 @@ class ConsensusAggregator:
         verdicts: list[ReviewVerdict],
         cfg: AggregationConfig,
     ) -> AggregationOutcome:
+        """有効な判定の多数決で 1 つの結論にまとめる (設計書 §14.1)."""
         valid = [verdict for verdict in verdicts if verdict.status is VerdictStatus.OK]
         if not valid:
             return AggregationOutcome(
`````

[Back to the shelf](README.md)
