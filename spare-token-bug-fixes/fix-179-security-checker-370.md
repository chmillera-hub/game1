# Fix 179: security-checker: score.py compares against unnamed numbers (50 and 70 and 90)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: score.py の rank_for にある比較用の数値 (50, 70, 90) を名前付き定数にする
- Bug report: number 370 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/370))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/179-security-checker-370.patch](fixes/179-security-checker-370.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/179-security-checker-370.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-179-security-checker-370.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-179-security-checker-370.html

## The bug

src/security_checker/policy/score.py compared the score against bare numbers (50 and 70 and 90). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use the new constants RANK_A_MIN and RANK_B_MIN and RANK_C_MIN.

## Files changed

- src/security_checker/policy/score.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 179-security-checker-370.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 370.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 197 on this shelf adds a docstring on the line right above so patches 179 and 197 do not apply together: apply one and add the other change by hand. A rename of a number into a named constant with no change in behaviour. Nobody ran the lint tool or the project's tests.

## Search words

security-checker PLR2004 magic value named constant score.py 50 and 70 and 90

## The full patch

`````diff
diff --git a/src/security_checker/policy/score.py b/src/security_checker/policy/score.py
index 95ea466..201271f 100644
--- a/src/security_checker/policy/score.py
+++ b/src/security_checker/policy/score.py
@@ -25,14 +25,18 @@ DEDUCTION = {
     Severity.NONE: 0,
 }
 CATEGORY_CAP = 40
+#: ランクの下限 (この点数以上). どれにも届かなければ D
+RANK_A_MIN = 90
+RANK_B_MIN = 70
+RANK_C_MIN = 50
 
 
 def rank_for(value: int) -> Literal["A", "B", "C", "D"]:
-    if value >= 90:
+    if value >= RANK_A_MIN:
         return "A"
-    if value >= 70:
+    if value >= RANK_B_MIN:
         return "B"
-    if value >= 50:
+    if value >= RANK_C_MIN:
         return "C"
     return "D"
`````

[Back to the shelf](README.md)
