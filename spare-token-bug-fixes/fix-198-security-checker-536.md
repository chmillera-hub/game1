# Fix 198: security-checker: no test covers a missing base address in the local endpoint check

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): detect.py の _is_local で未テストの分岐をテストする（1 行）
- Bug report: number 536 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/536))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/198-security-checker-536.patch](fixes/198-security-checker-536.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/198-security-checker-536.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-198-security-checker-536.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-198-security-checker-536.html

## The bug

_is_local in src/security_checker/providers/detect.py returns False when no base address is given. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_detect_is_local.py checks a missing and an empty address and four loopback addresses and two other hosts.

## Files changed

- tests/unit/test_detect_is_local.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 198-security-checker-536.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 536.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A scratch script confirmed how the standard library reads the host of each address. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker detect _is_local base_url None localhost LOCAL_HOSTS untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_detect_is_local.py b/tests/unit/test_detect_is_local.py
new file mode 100644
index 0000000..1d70557
--- /dev/null
+++ b/tests/unit/test_detect_is_local.py
@@ -0,0 +1,30 @@
+"""detect._is_local: base_url が無い・ローカルでないエンドポイントの判定."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.providers.detect import _is_local
+
+
+@pytest.mark.parametrize("base_url", [None, ""])
+def test_missing_base_url_is_not_local(base_url: str | None) -> None:
+    assert _is_local(base_url) is False
+
+
+@pytest.mark.parametrize(
+    "base_url",
+    [
+        "http://localhost:11434",
+        "http://127.0.0.1:8080/v1",
+        "http://[::1]:11434",
+        "http://0.0.0.0:1",
+    ],
+)
+def test_loopback_hosts_are_local(base_url: str) -> None:
+    assert _is_local(base_url) is True
+
+
+@pytest.mark.parametrize("base_url", ["https://api.example.com/v1", "http://localhost.example.com"])
+def test_other_hosts_are_not_local(base_url: str) -> None:
+    assert _is_local(base_url) is False
`````

[Back to the shelf](README.md)
