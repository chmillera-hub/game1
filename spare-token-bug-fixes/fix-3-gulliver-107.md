# Fix 3: Gulliver: spend with a huge --days value crashes with OverflowError

Status: UNSENT and UNTESTED. Free to take.

- Project: laaielichter/Gulliver
- Bug report: number 107 ([open the bug report](https://github.com/laaielichter/Gulliver/issues/107))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/3-gulliver-107.patch](fixes/3-gulliver-107.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/3-gulliver-107.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-3-gulliver-107.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-3-gulliver-107.html

## The bug

Running the spend command with a very large --days number such as 10000000 crashes with OverflowError: date value out of range instead of showing a clear message.

## The fix

The fix wraps the date arithmetic in runaway.py in a try block and returns the error message "--days is too large." with a suggested next step. A new test covers two huge values.

## Files changed

- src/gulliver/runaway.py
- tests/test_runaway.py

## How to use the fix

1. Get a copy of the project laaielichter/Gulliver.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 3-gulliver-107.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 107.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.

## Search words

gulliver spend --days OverflowError date value out of range timedelta runaway.py

## The full patch

`````diff
diff --git a/src/gulliver/runaway.py b/src/gulliver/runaway.py
index 03a55d5..4e2bebd 100644
--- a/src/gulliver/runaway.py
+++ b/src/gulliver/runaway.py
@@ -314,7 +314,10 @@ def spend(settings: Settings, by: str = "agent", days: int = 7) -> dict[str, Any
     if days < 1:
         return _error("--days must be at least 1.", "Give a positive number of days, for example --days 7.")
     days = int(days)
-    first = now_utc().date() - timedelta(days=days - 1)
+    try:
+        first = now_utc().date() - timedelta(days=days - 1)
+    except OverflowError:
+        return _error("--days is too large.", "Give a smaller number of days, for example --days 365.")
     groups: dict[str, dict[str, Any]] = {}
     total = {"usd": 0.0, "executions": 0, "bytes": 0}
     for e in read_ledger(Store(settings.state_dir)):
diff --git a/tests/test_runaway.py b/tests/test_runaway.py
index ef1dbf1..27a763a 100644
--- a/tests/test_runaway.py
+++ b/tests/test_runaway.py
@@ -414,6 +414,14 @@ def test_spend_refuses_a_window_below_one_day(settings, demo_db, capsys):
     assert runaway.spend(settings, by="agent", days=1)["status"] == "ok"  # one day is still a window
 
 
+def test_spend_refuses_a_window_too_large_for_a_date(settings, demo_db, capsys):
+    for days in (10**7, 10**12):
+        res = runaway.spend(settings, by="agent", days=days)
+        assert res["status"] == "error" and "--days" in res["error"] and res["next_step"]
+        assert main(["--dsn", demo_db, "spend", "--days", str(days)]) == 1
+        assert "--days" in capsys.readouterr().out
+
+
 # -- audit chain ------------------------------------------------------------------------------------------
 def _some_history(settings):
     core.preflight(settings, Q)
`````

[Back to the shelf](README.md)
