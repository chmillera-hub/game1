# Fix 184: security-checker: agreement.py compares against unnamed numbers (0.25 and 0.75 and 2)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: agreement.py の compute_agreement にある比較用の数値 (0.25, 0.75, 2) を名前付き定数にする
- Bug report: number 364 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/364))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/184-security-checker-364.patch](fixes/184-security-checker-364.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/184-security-checker-364.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-184-security-checker-364.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-184-security-checker-364.html

## The bug

src/security_checker/aggregate/agreement.py compared the share of vulnerable verdicts and the severity spread and the number of reviewers against bare numbers (0.25 and 0.75 and 2). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use the new constants MIN_REVIEWERS and MEDIUM_LOW_RATIO and MEDIUM_HIGH_RATIO and MEDIUM_MAX_SPREAD.

## Files changed

- src/security_checker/aggregate/agreement.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 184-security-checker-364.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 364.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A rename of a number into a named constant with no change in behaviour. Nobody ran the lint tool or the project's tests.

## Search words

security-checker PLR2004 magic value named constant agreement.py 0.25 and 0.75 and 2

## The full patch

`````diff
diff --git a/src/security_checker/aggregate/agreement.py b/src/security_checker/aggregate/agreement.py
index b3a171d..3b3ad4e 100644
--- a/src/security_checker/aggregate/agreement.py
+++ b/src/security_checker/aggregate/agreement.py
@@ -10,10 +10,18 @@ from security_checker.aggregate.base import SEVERITY_NUMBER
 from security_checker.models.enums import Agreement
 from security_checker.models.verdict import ReviewVerdict
 
+#: 一致度を出せる最小の人数. 1 人では「合意」にならない (§13.2)
+MIN_REVIEWERS = 2
+#: medium にする vulnerable の割合の帯. この値以下か、MEDIUM_HIGH_RATIO 以上
+MEDIUM_LOW_RATIO = 0.25
+MEDIUM_HIGH_RATIO = 0.75
+#: medium にする severity の幅の上限
+MEDIUM_MAX_SPREAD = 2
+
 
 def compute_agreement(valid: list[ReviewVerdict]) -> Agreement:
     """vulnerable の割合と severity の幅の 2 軸で決める."""
-    if len(valid) < 2:
+    if len(valid) < MIN_REVIEWERS:
         # 「1 モデルの合意」を high agreement と偽装しない (§13.2)
         return Agreement.NOT_APPLICABLE
 
@@ -24,6 +32,7 @@ def compute_agreement(valid: list[ReviewVerdict]) -> Agreement:
 
     if vuln_ratio in (0.0, 1.0) and spread <= 1:
         return Agreement.HIGH
-    if (vuln_ratio <= 0.25 or vuln_ratio >= 0.75) and spread <= 2:
+    lopsided = vuln_ratio <= MEDIUM_LOW_RATIO or vuln_ratio >= MEDIUM_HIGH_RATIO
+    if lopsided and spread <= MEDIUM_MAX_SPREAD:
         return Agreement.MEDIUM
     return Agreement.LOW
`````

[Back to the shelf](README.md)
