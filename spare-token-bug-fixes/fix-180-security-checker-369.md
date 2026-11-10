# Fix 180: security-checker: client.py compares against unnamed numbers (400)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: client.py の _request にある比較用の数値 (400) を名前付き定数にする
- Bug report: number 369 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/369))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/180-security-checker-369.patch](fixes/180-security-checker-369.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/180-security-checker-369.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-180-security-checker-369.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-180-security-checker-369.html

## The bug

src/security_checker/github/client.py compared the HTTP status against bare numbers (400). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use http.HTTPStatus.BAD_REQUEST.

## Files changed

- src/security_checker/github/client.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 180-security-checker-369.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 369.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 132 on this shelf changes an import line right next to the new import so patches 132 and 180 do not apply together: apply one and add the other change by hand. A rename of a number into a named constant with no change in behaviour. Nobody ran the lint tool or the project's tests.

## Search words

security-checker PLR2004 magic value named constant client.py 400

## The full patch

`````diff
diff --git a/src/security_checker/github/client.py b/src/security_checker/github/client.py
index 8fcf3b0..57ee688 100644
--- a/src/security_checker/github/client.py
+++ b/src/security_checker/github/client.py
@@ -11,6 +11,7 @@ import json
 import os
 from collections.abc import Callable, Mapping
 from dataclasses import dataclass, field
+from http import HTTPStatus
 from pathlib import Path
 from typing import Any
 
@@ -114,7 +115,7 @@ class GithubClient:
             response = self._client.request(method, url, **kwargs)
         except httpx.HTTPError as exc:
             raise GithubError(f"GitHub API に接続できません: {exc}") from exc
-        if response.status_code >= 400:
+        if response.status_code >= HTTPStatus.BAD_REQUEST:
             message = ""
             try:
                 message = str(response.json().get("message", ""))
`````

[Back to the shelf](README.md)
