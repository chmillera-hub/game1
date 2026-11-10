# Fix 220: security-checker: public names in observability/quota.py have no docstring (__init__ and default_quota_path and remaining and used)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(observability): quota.py の公開クラス・メソッド 4 個に docstring が無い
- Bug report: number 405 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/405))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/220-security-checker-405.patch](fixes/220-security-checker-405.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/220-security-checker-405.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-220-security-checker-405.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-220-security-checker-405.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/observability/quota.py: __init__ and default_quota_path and remaining and used. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/observability/quota.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/observability/quota.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 220-security-checker-405.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 405.

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

security-checker docstring D1 ruff missing docstring quota.py __init__ and default_quota_path and remaining and used

## The full patch

`````diff
diff --git a/src/security_checker/observability/quota.py b/src/security_checker/observability/quota.py
index 5b3d4c7..c8d4f20 100644
--- a/src/security_checker/observability/quota.py
+++ b/src/security_checker/observability/quota.py
@@ -23,6 +23,7 @@ KEEP_DAYS = 7
 
 
 def default_quota_path() -> Path:
+    """クォータの記録の既定の場所. XDG_CACHE_HOME (無ければ ~/.cache) の下."""
     base = os.environ.get("XDG_CACHE_HOME")
     root = Path(base) if base else Path.home() / ".cache"
     return root / "security-checker" / QUOTA_FILENAME
@@ -36,6 +37,7 @@ class QuotaStore:
     """Reviewer ごとの当日の呼び出し回数. 読み書きに失敗しても実行は止めない (警告にする)."""
 
     def __init__(self, path: Path | None = None, *, today: Callable[[], date] = _today) -> None:
+        """`path` を省くと既定の場所を使う. `today` はテストで日付を差し替えるためのもの."""
         self.path = path or default_quota_path()
         self._today = today
         self.errors: list[str] = []
@@ -51,11 +53,13 @@ class QuotaStore:
         return data if isinstance(data, dict) else {}
 
     def used(self, key: str) -> int:
+        """`key` (Reviewer) の当日の累計. 記録が無い・読めないときは 0."""
         day = self._load().get(self._today().isoformat(), {})
         value = day.get(key, 0) if isinstance(day, dict) else 0
         return value if isinstance(value, int) else 0
 
     def remaining(self, key: str, limit: int) -> int:
+        """`limit` までの残り回数. 負にはならない."""
         return max(0, limit - self.used(key))
 
     def consume(self, key: str, count: int = 1) -> int:
`````

[Back to the shelf](README.md)
