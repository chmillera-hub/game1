# Fix 175: security-checker: transport.py compares against unnamed numbers (400 and 429 and 500)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: transport.py の _raise_for_status にある比較用の数値 (400, 429, 500) を名前付き定数にする
- Bug report: number 374 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/374))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/175-security-checker-374.patch](fixes/175-security-checker-374.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/175-security-checker-374.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-175-security-checker-374.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-175-security-checker-374.html

## The bug

src/security_checker/providers/http/transport.py compared the HTTP status against bare numbers (400 and 429 and 500). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use http.HTTPStatus names (BAD_REQUEST and TOO_MANY_REQUESTS and REQUEST_TIMEOUT and INTERNAL_SERVER_ERROR) as the bug report asks.

## Files changed

- src/security_checker/providers/http/transport.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 175-security-checker-374.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 374.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The patch also names the 408 comparison in the same function. One comparison with 400 in another function of the same file is left as found because the bug report does not list that line. A rename of a number into a named constant with no change in behaviour. Nobody ran the lint tool or the project's tests.

## Search words

security-checker PLR2004 magic value named constant transport.py 400 and 429 and 500

## The full patch

`````diff
diff --git a/src/security_checker/providers/http/transport.py b/src/security_checker/providers/http/transport.py
index 15b09c9..8baf6b3 100644
--- a/src/security_checker/providers/http/transport.py
+++ b/src/security_checker/providers/http/transport.py
@@ -9,6 +9,7 @@ from __future__ import annotations
 import time
 from datetime import UTC, datetime
 from email.utils import parsedate_to_datetime
+from http import HTTPStatus
 from typing import Any, Literal
 
 import httpx
@@ -160,7 +161,7 @@ class HttpProvider:
 
     def _raise_for_status(self, response: httpx.Response) -> None:
         status = response.status_code
-        if status < 400:
+        if status < HTTPStatus.BAD_REQUEST:
             return
         detail = _excerpt(response.text)
         if status in (401, 403) or self.dialect_impl.is_auth_error(status, response.text):
@@ -169,18 +170,18 @@ class HttpProvider:
                 f"api_key_env に指定した環境変数の値を確認してください: {detail}",
                 provider=self.name,
             )
-        if status == 429:
+        if status == HTTPStatus.TOO_MANY_REQUESTS:
             raise ProviderRateLimitError(
                 f"{self.name}: レート制限に達しました: {detail}",
                 provider=self.name,
                 retry_after=_retry_after(response),
             )
-        if status == 408:
+        if status == HTTPStatus.REQUEST_TIMEOUT:
             raise ProviderTimeoutError(
                 f"{self.name}: サーバがタイムアウトを返しました (408): {detail}",
                 provider=self.name,
             )
-        if status >= 500:
+        if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
             raise ProviderServerError(
                 f"{self.name}: サーバエラー ({status}): {detail}", provider=self.name
             )
`````

[Back to the shelf](README.md)
