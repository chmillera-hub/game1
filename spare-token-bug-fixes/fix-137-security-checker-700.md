# Fix 137: security-checker: a scanner's internal error is recorded without the exception type or a traceback

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(run): スキャナの内部エラーを str(exc) だけで記録し、例外の型とトレースバックが失われる
- Bug report: number 700 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/700))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/137-security-checker-700.patch](fixes/137-security-checker-700.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/137-security-checker-700.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-137-security-checker-700.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-137-security-checker-700.html

## The bug

_run_one in src/security_checker/run.py caught any scanner exception and recorded only the message. A KeyError('x') left the reason as 内部エラー: 'x' so nobody could tell what kind of error happened or where.

## The fix

The reason now holds the exception type name before the message. The traceback goes to the debug log as an event named scanner.internal_error. A new file tests/unit/test_run_scanner_internal_error.py checks the reason text and that the traceback shows at debug level and not at info level.

## Files changed

- src/security_checker/run.py
- tests/unit/test_run_scanner_internal_error.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 137-security-checker-700.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 700.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The event name scanner.internal_error is the chatbot's choice. The traceback passes through the project's own log formatter which hides known secret formats. The chatbot did not run the tests.

## Search words

security-checker run.py _run_one scanner internal error str(exc) exception type traceback debug log reason

## The full patch

`````diff
diff --git a/src/security_checker/run.py b/src/security_checker/run.py
index cefc183..968b344 100644
--- a/src/security_checker/run.py
+++ b/src/security_checker/run.py
@@ -11,6 +11,7 @@ import asyncio
 import contextlib
 import tempfile
 import time
+import traceback
 from collections.abc import Sequence
 from dataclasses import dataclass, field
 from pathlib import Path
@@ -224,11 +225,19 @@ async def _run_one(
         try:
             return await scanner.scan(target, ctx)
         except Exception as exc:  # 1 つの失敗で全体を落とさない (§20.2)
+            # report.json には型名と短いメッセージだけを残し、トレースバックは debug ログに出す
+            log.event(
+                "scanner.internal_error",
+                level="debug",
+                scanner=scanner.name,
+                error_type=type(exc).__name__,
+                traceback=traceback.format_exc(),
+            )
             return ScanResult(
                 scanner=scanner.name,
                 category=scanner.category,
                 status=ScanStatus.FAILED,
-                reason=f"内部エラー: {exc}",
+                reason=f"内部エラー: {type(exc).__name__}: {exc}",
             )
 
 
diff --git a/tests/unit/test_run_scanner_internal_error.py b/tests/unit/test_run_scanner_internal_error.py
new file mode 100644
index 0000000..2bcbe59
--- /dev/null
+++ b/tests/unit/test_run_scanner_internal_error.py
@@ -0,0 +1,48 @@
+"""スキャナの内部エラーに例外の型名が残り、トレースバックが debug ログに出ること."""
+
+from __future__ import annotations
+
+import io
+
+from security_checker.config.schema import Config
+from security_checker.models.enums import ScanStatus
+from security_checker.observability import logging as log
+from security_checker.run import run_scan
+from security_checker.testing.fakes import FakeScanner
+
+
+async def test_internal_error_reason_names_the_exception_type(tmp_path):
+    scanners = [FakeScanner("boom", raises=KeyError("x"))]
+
+    outcome = await run_scan(Config(), tmp_path, base_dir=tmp_path, scanners=scanners)
+
+    (run,) = outcome.report.scanners
+    assert run.status is ScanStatus.FAILED
+    assert run.reason == "内部エラー: KeyError: 'x'"
+
+
+async def test_internal_error_traceback_goes_to_the_debug_log(tmp_path):
+    stream = io.StringIO()
+    log.configure(level="debug", fmt="json", stream=stream)
+    try:
+        scanners = [FakeScanner("boom", raises=KeyError("x"))]
+        await run_scan(Config(), tmp_path, base_dir=tmp_path, scanners=scanners)
+    finally:
+        log.disable()
+
+    lines = [line for line in stream.getvalue().splitlines() if "scanner.internal_error" in line]
+    assert len(lines) == 1
+    assert "KeyError" in lines[0]
+    assert "Traceback" in lines[0]
+
+
+async def test_internal_error_traceback_stays_out_of_the_info_log(tmp_path):
+    stream = io.StringIO()
+    log.configure(level="info", fmt="json", stream=stream)
+    try:
+        scanners = [FakeScanner("boom", raises=KeyError("x"))]
+        await run_scan(Config(), tmp_path, base_dir=tmp_path, scanners=scanners)
+    finally:
+        log.disable()
+
+    assert "Traceback" not in stream.getvalue()
`````

[Back to the shelf](README.md)
