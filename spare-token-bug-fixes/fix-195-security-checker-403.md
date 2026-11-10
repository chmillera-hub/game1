# Fix 195: security-checker: public names in logging.py have no docstring (disable and set_run_id)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(observability): logging.py の公開クラス・メソッド 2 個に docstring が無い
- Bug report: number 403 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/403))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/195-security-checker-403.patch](fixes/195-security-checker-403.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/195-security-checker-403.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-195-security-checker-403.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-195-security-checker-403.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/observability/logging.py: disable and set_run_id. A person who writes a plugin cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/observability/logging.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/observability/logging.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 195-security-checker-403.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 403.

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

security-checker docstring D1 ruff missing docstring logging.py disable and set_run_id

## The full patch

`````diff
diff --git a/src/security_checker/observability/logging.py b/src/security_checker/observability/logging.py
index e390fc9..3346205 100644
--- a/src/security_checker/observability/logging.py
+++ b/src/security_checker/observability/logging.py
@@ -37,6 +37,7 @@ logger.propagate = False
 
 
 def set_run_id(run_id: str | None) -> None:
+    """以降のログに付ける run_id を設定する. None で外す."""
     _run_id.set(run_id)
 
 
@@ -83,6 +84,7 @@ def configure(
 
 
 def disable() -> None:
+    """`configure` が付けたハンドラを外して閉じる. 付いていなければ何もしない."""
     for handler in list(logger.handlers):
         if handler.get_name() == "security-checker":
             logger.removeHandler(handler)
`````

[Back to the shelf](README.md)
