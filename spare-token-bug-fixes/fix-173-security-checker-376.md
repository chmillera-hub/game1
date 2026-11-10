# Fix 173: security-checker: scheduler.py compares against unnamed numbers (60.0)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: scheduler.py の acquire にある比較用の数値 (60.0) を名前付き定数にする
- Bug report: number 376 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/376))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/173-security-checker-376.patch](fixes/173-security-checker-376.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/173-security-checker-376.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-173-security-checker-376.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-173-security-checker-376.html

## The bug

src/security_checker/review/scheduler.py compared the age of rate limit events against bare numbers (60.0). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use the new constant RATE_WINDOW_S in all four spots (the request limiter and the token limiter).

## Files changed

- src/security_checker/review/scheduler.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 173-security-checker-376.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 376.

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

security-checker PLR2004 magic value named constant scheduler.py 60.0

## The full patch

`````diff
diff --git a/src/security_checker/review/scheduler.py b/src/security_checker/review/scheduler.py
index 880e550..62eac90 100644
--- a/src/security_checker/review/scheduler.py
+++ b/src/security_checker/review/scheduler.py
@@ -34,6 +34,8 @@ SYSTEM_PROMPT_TOKENS = PROMPT_OVERHEAD_TOKENS
 MAX_ATTEMPTS = 3
 BACKOFF_BASE_S = 1.0
 BACKOFF_CAP_S = 60.0
+#: rpm / tpm を数える窓の長さ (秒). 「1 分あたり」の 1 分
+RATE_WINDOW_S = 60.0
 CIRCUIT_BREAKER_FAILURES = 5
 DEFAULT_DEADLINE_S = 1800.0
 #: rate_limit.rpm を書いていない Reviewer の初期値. 429 を受けるまでは絞らない
@@ -56,13 +58,13 @@ class RateLimiter:
         while True:
             async with self._lock:
                 now = time.monotonic()
-                while self._events and now - self._events[0] >= 60.0:
+                while self._events and now - self._events[0] >= RATE_WINDOW_S:
                     self._events.popleft()
                 if len(self._events) < self.rpm:
                     self._events.append(now)
                     return
                 oldest = self._events[0]
-                wait_for = 60.0 - (now - oldest)
+                wait_for = RATE_WINDOW_S - (now - oldest)
             await sleep(max(0.05, wait_for))
             async with self._lock:
                 # 待った分の枠は空いたものとして扱う
@@ -94,13 +96,13 @@ class TokenLimiter:
         while True:
             async with self._lock:
                 now = time.monotonic()
-                while self._events and now - self._events[0][0] >= 60.0:
+                while self._events and now - self._events[0][0] >= RATE_WINDOW_S:
                     self._events.popleft()
                 used = sum(count for _, count in self._events)
                 if not self._events or used + tokens <= self.tpm:
                     self._events.append((now, tokens))
                     return
-                wait_for = 60.0 - (now - self._events[0][0])
+                wait_for = RATE_WINDOW_S - (now - self._events[0][0])
             await asyncio.sleep(max(0.05, wait_for))
`````

[Back to the shelf](README.md)
