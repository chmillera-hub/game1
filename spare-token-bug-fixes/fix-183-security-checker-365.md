# Fix 183: security-checker: consensus.py compares against unnamed numbers (0.8)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: consensus.py の aggregate にある比較用の数値 (0.8) を名前付き定数にする
- Bug report: number 365 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/365))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/183-security-checker-365.patch](fixes/183-security-checker-365.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/183-security-checker-365.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-183-security-checker-365.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-183-security-checker-365.html

## The bug

src/security_checker/aggregate/consensus.py compared the mean confidence against bare numbers (0.8). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use the new constant CONSENSUS_CONFIRMED_CONFIDENCE.

## Files changed

- src/security_checker/aggregate/consensus.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 183-security-checker-365.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 365.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The file already has SINGLE_CONFIRMED_CONFIDENCE with the same value for the single reviewer case. The patch adds a separate name so the two thresholds can change apart. A rename of a number into a named constant with no change in behaviour. Nobody ran the lint tool or the project's tests.

## Search words

security-checker PLR2004 magic value named constant consensus.py 0.8

## The full patch

`````diff
diff --git a/src/security_checker/aggregate/consensus.py b/src/security_checker/aggregate/consensus.py
index eb5bd04..a155a33 100644
--- a/src/security_checker/aggregate/consensus.py
+++ b/src/security_checker/aggregate/consensus.py
@@ -24,6 +24,8 @@ SUMMARY_LIMIT = 200
 SUMMARY_HEAD_LIMIT = 160
 SINGLE_CONFIRMED_CONFIDENCE = 0.8
 SINGLE_LIKELY_CONFIDENCE = 0.5
+#: 複数の Reviewer が一致したとき、confirmed にする confidence の平均の下限
+CONSENSUS_CONFIRMED_CONFIDENCE = 0.8
 
 
 class ConsensusAggregator:
@@ -86,7 +88,7 @@ class ConsensusAggregator:
             mean_confidence = statistics.fmean(v.confidence for v in vulnerable)
             status = (
                 FindingStatus.CONFIRMED
-                if agreement is Agreement.HIGH and mean_confidence >= 0.8
+                if agreement is Agreement.HIGH and mean_confidence >= CONSENSUS_CONFIRMED_CONFIDENCE
                 else FindingStatus.LIKELY
             )
             return self._outcome(
`````

[Back to the shelf](README.md)
