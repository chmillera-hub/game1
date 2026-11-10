# Fix 252: security-checker: public names in review/scheduler.py have no docstring (three __init__ methods and two acquire methods and name and remaining)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(review): scheduler.py の公開クラス・メソッド 7 個に docstring が無い
- Bug report: number 421 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/421))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/252-security-checker-421.patch](fixes/252-security-checker-421.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/252-security-checker-421.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-252-security-checker-421.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-252-security-checker-421.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/review/scheduler.py: three __init__ methods and two acquire methods and name and remaining. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/review/scheduler.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/review/scheduler.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 252-security-checker-421.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 421.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring scheduler.py three __init__ methods and two acquire methods and name and remaining

## The full patch

`````diff
diff --git a/src/security_checker/review/scheduler.py b/src/security_checker/review/scheduler.py
index 880e550..82640bd 100644
--- a/src/security_checker/review/scheduler.py
+++ b/src/security_checker/review/scheduler.py
@@ -47,12 +47,14 @@ class RateLimiter:
     """rpm のトークンバケット. 送信直前に 1 リクエスト分を確保する."""
 
     def __init__(self, rpm: int) -> None:
+        """`rpm` は 1 分あたりに送れるリクエスト数."""
         self.rpm = rpm
         self.base_rpm = rpm
         self._events: deque[float] = deque()
         self._lock = asyncio.Lock()
 
     async def acquire(self, sleep: Callable[[float], Awaitable[None]] = asyncio.sleep) -> None:
+        """1 リクエスト分の枠が空くまで待って確保する. `sleep` はテストで差し替える."""
         while True:
             async with self._lock:
                 now = time.monotonic()
@@ -86,11 +88,13 @@ class TokenLimiter:
     """
 
     def __init__(self, tpm: int) -> None:
+        """`tpm` は 1 分あたりに送れるトークン数."""
         self.tpm = tpm
         self._events: deque[tuple[float, int]] = deque()
         self._lock = asyncio.Lock()
 
     async def acquire(self, tokens: int) -> None:
+        """`tokens` 分の枠が空くまで待って確保する."""
         while True:
             async with self._lock:
                 now = time.monotonic()
@@ -113,6 +117,7 @@ class DailyQuota:
     limit: int
 
     def remaining(self) -> int:
+        """当日の残り回数."""
         return self.store.remaining(self.key, self.limit)
 
 
@@ -132,6 +137,7 @@ class ReviewerRuntime:
 
     @property
     def name(self) -> str:
+        """Reviewer の名前."""
         return self.reviewer.name
 
 
@@ -191,6 +197,7 @@ class ReviewScheduler:
         deadline_s: float = DEFAULT_DEADLINE_S,
         sleep: Callable[[float], Awaitable[None]] | None = None,
     ) -> None:
+        """`deadline_s` は run 全体の制限時間. `sleep` はテストで待ち時間を差し替える."""
         self.runtimes = runtimes
         self.budget = budget
         self.deadline_s = deadline_s
`````

[Back to the shelf](README.md)
