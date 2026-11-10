# Fix 182: security-checker: builder.py compares against unnamed numbers (3)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: builder.py の _mask_quoted にある比較用の数値 (3) を名前付き定数にする
- Bug report: number 366 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/366))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/182-security-checker-366.patch](fixes/182-security-checker-366.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/182-security-checker-366.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-182-security-checker-366.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-182-security-checker-366.html

## The bug

src/security_checker/context/builder.py compared the number of parts after a split on a quote character against bare numbers (3). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use the new constant MIN_PARTS_WITH_QUOTED_VALUE.

## Files changed

- src/security_checker/context/builder.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 182-security-checker-366.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 366.

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

security-checker PLR2004 magic value named constant builder.py 3

## The full patch

`````diff
diff --git a/src/security_checker/context/builder.py b/src/security_checker/context/builder.py
index 5fa69f4..bc6f21f 100644
--- a/src/security_checker/context/builder.py
+++ b/src/security_checker/context/builder.py
@@ -244,11 +244,15 @@ _SENSITIVE_ASSIGNMENT_RE = re.compile(
 _DETECTED_LINE_TOKEN_RE = re.compile(r"(?=[A-Za-z0-9+/_.~:@-]*[0-9])[A-Za-z0-9+/_.~:@-]{16,}={0,2}")
 
 
+#: 引用符で split した結果がこの数に満たなければ、閉じた引用 ("...") は 1 つも無い
+MIN_PARTS_WITH_QUOTED_VALUE = 3
+
+
 def _mask_quoted(line: str) -> str:
     result = line
     for quote in ('"', "'"):
         parts = result.split(quote)
-        if len(parts) < 3:
+        if len(parts) < MIN_PARTS_WITH_QUOTED_VALUE:
             continue
         for index in range(1, len(parts), 2):
             value = parts[index]
`````

[Back to the shelf](README.md)
