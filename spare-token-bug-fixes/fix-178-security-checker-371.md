# Fix 178: security-checker: anthropic_messages.py compares against unnamed numbers (400 and 404)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: anthropic_messages.py の explain_error にある比較用の数値 (400, 404) を名前付き定数にする
- Bug report: number 371 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/371))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/178-security-checker-371.patch](fixes/178-security-checker-371.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/178-security-checker-371.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-178-security-checker-371.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-178-security-checker-371.html

## The bug

src/security_checker/providers/http/dialects/anthropic_messages.py compared the HTTP status against bare numbers (400 and 404). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use http.HTTPStatus.BAD_REQUEST and http.HTTPStatus.NOT_FOUND.

## Files changed

- src/security_checker/providers/http/dialects/anthropic_messages.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 178-security-checker-371.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 371.

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

security-checker PLR2004 magic value named constant anthropic_messages.py 400 and 404

## The full patch

`````diff
diff --git a/src/security_checker/providers/http/dialects/anthropic_messages.py b/src/security_checker/providers/http/dialects/anthropic_messages.py
index 62bcf33..1280e45 100644
--- a/src/security_checker/providers/http/dialects/anthropic_messages.py
+++ b/src/security_checker/providers/http/dialects/anthropic_messages.py
@@ -14,6 +14,7 @@
 from __future__ import annotations
 
 import json
+from http import HTTPStatus
 from typing import Any
 
 from security_checker.models.verdict import Usage
@@ -147,12 +148,12 @@ class AnthropicMessagesDialect:
     def explain_error(self, status: int, body: str) -> str | None:
         """次に取れる行動が分かる場合だけ文章にする (§20.2)."""
         lowered = body.lower()
-        if status == 404 and "model" in lowered:
+        if status == HTTPStatus.NOT_FOUND and "model" in lowered:
             return (
                 "model に指定した ID がこのエンドポイントに存在しません。"
                 "設定の model を確認してください"
             )
-        if status == 400 and "max_tokens" in lowered:
+        if status == HTTPStatus.BAD_REQUEST and "max_tokens" in lowered:
             return (
                 "出力トークンの上限がモデルの許容範囲を超えています。"
                 "max_output_tokens を下げてください"
`````

[Back to the shelf](README.md)
