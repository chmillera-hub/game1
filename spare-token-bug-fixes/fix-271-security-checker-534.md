# Fix 271: security-checker: no test covers the combined detection of process and HTTP reviewers

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): detect.py の detect_all で未テストの分岐をテストする（1 行）
- Bug report: number 534 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/534))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/271-security-checker-534.patch](fixes/271-security-checker-534.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/271-security-checker-534.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-271-security-checker-534.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-271-security-checker-534.html

## The bug

detect_all in src/security_checker/providers/detect.py returns the process detections followed by the HTTP detections. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_detect_all.py replaces both detection functions and expects the combined list in that order and expects the environment to be passed on.

## Files changed

- tests/unit/test_detect_all.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 271-security-checker-534.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 534.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker detect detect_all detect_process detect_http order environ untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_detect_all.py b/tests/unit/test_detect_all.py
new file mode 100644
index 0000000..3e78fc1
--- /dev/null
+++ b/tests/unit/test_detect_all.py
@@ -0,0 +1,32 @@
+"""detect.detect_all: process と http の検出結果を、この順でつなげて返すこと."""
+
+from __future__ import annotations
+
+from typing import Any
+
+import pytest
+
+from security_checker.providers import detect
+from security_checker.providers.detect import detect_all
+
+
+def test_process_detections_come_before_http_detections(monkeypatch: pytest.MonkeyPatch) -> None:
+    seen: list[Any] = []
+
+    def fake_http(*, environ: Any = None) -> list[str]:
+        seen.append(environ)
+        return ["http-a", "http-b"]
+
+    monkeypatch.setattr(detect, "detect_process", lambda: ["process-a"])
+    monkeypatch.setattr(detect, "detect_http", fake_http)
+    environ = {"EXAMPLE_API_KEY": "x"}
+
+    assert detect_all(environ=environ) == ["process-a", "http-a", "http-b"]
+    assert seen == [environ]
+
+
+def test_nothing_detected_is_an_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
+    monkeypatch.setattr(detect, "detect_process", lambda: [])
+    monkeypatch.setattr(detect, "detect_http", lambda *, environ=None: [])
+
+    assert detect_all(environ={}) == []
`````

[Back to the shelf](README.md)
