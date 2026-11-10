# Fix 172: security-checker: semgrep.py compares against unnamed numbers (2)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: semgrep.py の scan にある比較用の数値 (2) を名前付き定数にする
- Bug report: number 378 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/378))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/172-security-checker-378.patch](fixes/172-security-checker-378.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/172-security-checker-378.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-172-security-checker-378.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-172-security-checker-378.html

## The bug

src/security_checker/scanners/semgrep.py compared the semgrep exit code against bare numbers (2). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use the new constant FAILURE_EXIT_CODE.

## Files changed

- src/security_checker/scanners/semgrep.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 172-security-checker-378.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 378.

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

security-checker PLR2004 magic value named constant semgrep.py 2

## The full patch

`````diff
diff --git a/src/security_checker/scanners/semgrep.py b/src/security_checker/scanners/semgrep.py
index ac8f80c..2f5dc89 100644
--- a/src/security_checker/scanners/semgrep.py
+++ b/src/security_checker/scanners/semgrep.py
@@ -27,6 +27,8 @@ from security_checker.scanners.base import (
 from security_checker.scanners.filters import is_excluded
 
 CWE_RE = re.compile(r"CWE-\d+")
+#: semgrep は「検出あり」でも 0 を返す。この値以上の終了コードが実行失敗
+FAILURE_EXIT_CODE = 2
 
 SEVERITY_MAP = {
     "ERROR": Severity.HIGH,
@@ -213,7 +215,7 @@ class SemgrepScanner(BaseScanner):
                 version=status.version,
             )
         # semgrep は「検出あり」でも 0 を返す。2 以上が実行失敗。
-        if result.exit_code is None or result.exit_code >= 2:
+        if result.exit_code is None or result.exit_code >= FAILURE_EXIT_CODE:
             return self.failed(
                 "semgrep の実行に失敗しました",
                 exit_code=result.exit_code,
`````

[Back to the shelf](README.md)
