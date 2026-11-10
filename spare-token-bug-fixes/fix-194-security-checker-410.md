# Fix 194: security-checker: public names in errors.py have no docstring (three __init__ methods)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(providers): errors.py の公開クラス・メソッド 2 個に docstring が無い
- Bug report: number 410 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/410))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/194-security-checker-410.patch](fixes/194-security-checker-410.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/194-security-checker-410.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-194-security-checker-410.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-194-security-checker-410.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/providers/errors.py: three __init__ methods. A person who writes a plugin cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/providers/errors.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/providers/errors.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 194-security-checker-410.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 410.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report counts two items and the newest code has three __init__ methods without a docstring so the patch covers all three. Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring errors.py three __init__ methods

## The full patch

`````diff
diff --git a/src/security_checker/providers/errors.py b/src/security_checker/providers/errors.py
index 9e625ab..6f06f09 100644
--- a/src/security_checker/providers/errors.py
+++ b/src/security_checker/providers/errors.py
@@ -16,6 +16,7 @@ class ProviderError(SecurityCheckerError):
     retryable: bool = False
 
     def __init__(self, message: str, *, provider: str | None = None) -> None:
+        """`provider` は失敗した Provider の名前. 警告やログでどれが失敗したかを示す."""
         super().__init__(message)
         self.provider = provider
 
@@ -36,6 +37,7 @@ class ProviderRateLimitError(ProviderError):
         provider: str | None = None,
         retry_after: float | None = None,
     ) -> None:
+        """`retry_after` はサーバが示した待ち時間 (秒). 示されなければ None."""
         super().__init__(message, provider=provider)
         self.retry_after = retry_after
 
@@ -60,6 +62,7 @@ class ProviderBadRequestError(ProviderError):
     """
 
     def __init__(self, message: str, *, provider: str | None = None, status: int = 400) -> None:
+        """`status` は返ってきた HTTP ステータス. 降格して再送するかの判断に使う."""
         super().__init__(message, provider=provider)
         self.status = status
`````

[Back to the shelf](README.md)
