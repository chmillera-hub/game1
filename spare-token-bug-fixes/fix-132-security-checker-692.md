# Fix 132: security-checker: GithubClient.__enter__ is typed to return the parent class and not Self

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor(github): GithubClient.__enter__ の戻り値の型を Self にする (PYI034)
- Bug report: number 692 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/692))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/132-security-checker-692.patch](fixes/132-security-checker-692.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/132-security-checker-692.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-132-security-checker-692.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-132-security-checker-692.html

## The bug

__enter__ in src/security_checker/github/client.py was annotated to return GithubClient. A subclass used in a with block (a test fake for example) lost its own type. The lint rule PYI034 reports the line.

## The fix

__enter__ now returns typing.Self. The project needs Python 3.11 or newer so Self is available.

## Files changed

- src/security_checker/github/client.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 132-security-checker-692.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 692.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A type annotation change only with no change in behaviour. Nobody ran the lint tool or the type checker.

## Search words

security-checker GithubClient __enter__ Self PYI034 ruff typing return type context manager

## The full patch

`````diff
diff --git a/src/security_checker/github/client.py b/src/security_checker/github/client.py
index 8fcf3b0..485f92c 100644
--- a/src/security_checker/github/client.py
+++ b/src/security_checker/github/client.py
@@ -12,7 +12,7 @@ import os
 from collections.abc import Callable, Mapping
 from dataclasses import dataclass, field
 from pathlib import Path
-from typing import Any
+from typing import Any, Self
 
 import httpx
 
@@ -103,7 +103,7 @@ class GithubClient:
     def close(self) -> None:
         self._client.close()
 
-    def __enter__(self) -> GithubClient:
+    def __enter__(self) -> Self:
         return self
 
     def __exit__(self, *_: object) -> None:
`````

[Back to the shelf](README.md)
