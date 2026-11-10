# Fix 150: security-checker: no test covers a Retry-After header that is neither a number nor a date

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): transport.py の _retry_after で未テストの分岐をテストする（2 行）
- Bug report: number 549 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/549))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/150-security-checker-549.patch](fixes/150-security-checker-549.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/150-security-checker-549.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-150-security-checker-549.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-150-security-checker-549.html

## The bug

_retry_after in src/security_checker/providers/http/transport.py returns None when the Retry-After header is neither a number nor an HTTP date. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_transport_retry_after_unreadable.py expects None for the value soon and 2.5 for the value 2.5 and None for a missing header.

## Files changed

- tests/unit/test_transport_retry_after_unreadable.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 150-security-checker-549.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 549.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A scratch script confirmed that the standard library raises ValueError for the value soon on Python 3.13. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker transport _retry_after Retry-After header unreadable HTTP-date ValueError None untested

## The full patch

`````diff
diff --git a/tests/unit/test_transport_retry_after_unreadable.py b/tests/unit/test_transport_retry_after_unreadable.py
new file mode 100644
index 0000000..2a0a3c8
--- /dev/null
+++ b/tests/unit/test_transport_retry_after_unreadable.py
@@ -0,0 +1,24 @@
+"""_retry_after: 数値でも HTTP-date でもない Retry-After は None になること."""
+
+from __future__ import annotations
+
+import httpx
+
+from security_checker.providers.http.transport import _retry_after
+
+
+def test_unreadable_retry_after_is_none() -> None:
+    response = httpx.Response(429, headers={"Retry-After": "soon"})
+
+    assert _retry_after(response) is None
+
+
+def test_numeric_retry_after_is_seconds() -> None:
+    """対になるケース. 読める値はそのまま秒数になる."""
+    response = httpx.Response(429, headers={"Retry-After": "2.5"})
+
+    assert _retry_after(response) == 2.5
+
+
+def test_missing_retry_after_is_none() -> None:
+    assert _retry_after(httpx.Response(429)) is None
`````

[Back to the shelf](README.md)
