# Fix 5: Gulliver: parse_period with a huge number crashes with OverflowError

Status: UNSENT and UNTESTED. Free to take.

- Project: laaielichter/Gulliver
- Bug report: number 108 ([open the bug report](https://github.com/laaielichter/Gulliver/issues/108))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/5-gulliver-108.patch](fixes/5-gulliver-108.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/5-gulliver-108.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-5-gulliver-108.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-5-gulliver-108.html

## The bug

Giving the period reader a very large number of minutes or hours or days or weeks crashes with OverflowError instead of a clear error.

## The fix

The fix wraps the timedelta creation in parse_period in src/gulliver/incremental.py and raises ValueError with the message "period is too large". One new test line covers the case.

## Files changed

- src/gulliver/incremental.py
- tests/test_features.py

## How to use the fix

1. Get a copy of the project laaielichter/Gulliver.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 5-gulliver-108.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 108.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.

## Search words

gulliver parse_period OverflowError timedelta days too large incremental.py period is too large

## The full patch

`````diff
diff --git a/src/gulliver/incremental.py b/src/gulliver/incremental.py
index 144fb64..6707e3d 100644
--- a/src/gulliver/incremental.py
+++ b/src/gulliver/incremental.py
@@ -28,13 +28,16 @@ def parse_period(text: str) -> timedelta:
     if not m:
         raise ValueError("period looks like '1d', '24h', '7 days' or '30 min'")
     n, unit = int(m.group(1)), m.group(2).lower()
-    if unit.startswith("m"):
-        return timedelta(minutes=n)
-    if unit.startswith("h"):
-        return timedelta(hours=n)
-    if unit.startswith("w"):
-        return timedelta(weeks=n)
-    return timedelta(days=n)
+    try:
+        if unit.startswith("m"):
+            return timedelta(minutes=n)
+        if unit.startswith("h"):
+            return timedelta(hours=n)
+        if unit.startswith("w"):
+            return timedelta(weeks=n)
+        return timedelta(days=n)
+    except OverflowError:
+        raise ValueError("period is too large") from None
 
 
 def _batch_size(period: timedelta) -> str:
diff --git a/tests/test_features.py b/tests/test_features.py
index baeb3f7..1634998 100644
--- a/tests/test_features.py
+++ b/tests/test_features.py
@@ -294,6 +294,8 @@ def test_parse_period():
     assert incremental.parse_period("24h").total_seconds() == 86400
     with pytest.raises(ValueError):
         incremental.parse_period("soon")
+    with pytest.raises(ValueError):
+        incremental.parse_period("99999999999d")
 
 
 # -- checks -------------------------------------------------------------------------------------------------
`````

[Back to the shelf](README.md)
