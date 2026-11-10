# Fix 176: security-checker: ollama_chat.py compares against unnamed numbers (404)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: ollama_chat.py の explain_error にある比較用の数値 (404) を名前付き定数にする
- Bug report: number 373 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/373))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/176-security-checker-373.patch](fixes/176-security-checker-373.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/176-security-checker-373.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-176-security-checker-373.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-176-security-checker-373.html

## The bug

src/security_checker/providers/http/dialects/ollama_chat.py compared the HTTP status against bare numbers (404). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use http.HTTPStatus.NOT_FOUND.

## Files changed

- src/security_checker/providers/http/dialects/ollama_chat.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 176-security-checker-373.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 373.

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

security-checker PLR2004 magic value named constant ollama_chat.py 404

## The full patch

`````diff
diff --git a/src/security_checker/providers/http/dialects/ollama_chat.py b/src/security_checker/providers/http/dialects/ollama_chat.py
index d067300..2043656 100644
--- a/src/security_checker/providers/http/dialects/ollama_chat.py
+++ b/src/security_checker/providers/http/dialects/ollama_chat.py
@@ -8,6 +8,7 @@
 
 from __future__ import annotations
 
+from http import HTTPStatus
 from typing import Any
 
 from security_checker.models.verdict import Usage
@@ -122,7 +123,7 @@ class OllamaChatDialect:
 
     def explain_error(self, status: int, body: str) -> str | None:
         """モデル未取得を、実行できるコマンドの案内に変える (§9.4)."""
-        if status == 404 and "not found" in body.lower():
+        if status == HTTPStatus.NOT_FOUND and "not found" in body.lower():
             return (
                 "モデルが見つかりません。先にモデルを取得してください (例: `ollama pull <model>`)"
             )
`````

[Back to the shelf](README.md)
