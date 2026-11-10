# Fix 177: security-checker: gemini_generate.py compares against unnamed numbers (400 and 404)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: gemini_generate.py の explain_error にある比較用の数値 (400, 404) を名前付き定数にする
- Bug report: number 372 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/372))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/177-security-checker-372.patch](fixes/177-security-checker-372.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/177-security-checker-372.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-177-security-checker-372.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-177-security-checker-372.html

## The bug

src/security_checker/providers/http/dialects/gemini_generate.py compared the HTTP status against bare numbers (400 and 404). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use http.HTTPStatus.BAD_REQUEST and http.HTTPStatus.NOT_FOUND in four spots.

## Files changed

- src/security_checker/providers/http/dialects/gemini_generate.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 177-security-checker-372.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 372.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A rename of a number into a named constant with no change in behaviour. Nobody ran the lint tool or the project's tests. Fix 235 on this shelf adds a docstring on the lines right above so patches 177 and 235 do not apply together: apply one and add the other change by hand.

## Search words

security-checker PLR2004 magic value named constant gemini_generate.py 400 and 404

## The full patch

`````diff
diff --git a/src/security_checker/providers/http/dialects/gemini_generate.py b/src/security_checker/providers/http/dialects/gemini_generate.py
index f23ac24..60f4a5f 100644
--- a/src/security_checker/providers/http/dialects/gemini_generate.py
+++ b/src/security_checker/providers/http/dialects/gemini_generate.py
@@ -10,6 +10,7 @@
 
 from __future__ import annotations
 
+from http import HTTPStatus
 from typing import Any
 
 from security_checker.models.verdict import Usage
@@ -134,19 +135,19 @@ class GeminiGenerateDialect:
 
     def is_auth_error(self, status: int, body: str) -> bool:
         # この形は鍵の不備を 401 ではなく 400 で返す
-        return status == 400 and "api key" in body.lower()
+        return status == HTTPStatus.BAD_REQUEST and "api key" in body.lower()
 
     def explain_error(self, status: int, body: str) -> str | None:
         lowered = body.lower()
-        if status == 400 and "api key" in lowered:
+        if status == HTTPStatus.BAD_REQUEST and "api key" in lowered:
             # この形は鍵の不備を 401 ではなく 400 で返すため、認証エラーに見えない
             return "API キーが受け付けられませんでした。api_key_env の環境変数を確認してください"
-        if status == 404 and "model" in lowered:
+        if status == HTTPStatus.NOT_FOUND and "model" in lowered:
             return (
                 "model に指定した ID がこのエンドポイントに存在しません。"
                 "設定の model を確認してください"
             )
-        if status == 400 and "response_schema" in lowered.replace(
+        if status == HTTPStatus.BAD_REQUEST and "response_schema" in lowered.replace(
             "responseschema", "response_schema"
         ):
             return (
`````

[Back to the shelf](README.md)
