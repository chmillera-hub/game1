# Fix 247: security-checker: no test covers the advice texts of the provider check

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): check.py の _suggest で未テストの分岐をテストする（8 行）
- Bug report: number 531 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/531))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/247-security-checker-531.patch](fixes/247-security-checker-531.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/247-security-checker-531.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-247-security-checker-531.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-247-security-checker-531.html

## The bug

_suggest in src/security_checker/providers/check.py gives a different next step for an authentication error and a rate limit and a timeout and a refused request. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_check_suggest.py checks the advice for five kinds of failure and for a missing key variable and for a process reviewer.

## Files changed

- tests/unit/test_check_suggest.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 247-security-checker-531.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 531.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The tests pass a small stand-in object for the reviewer settings that holds only the four fields the function reads. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker providers check _suggest ProviderAuthError ProviderRateLimitError ProviderTimeoutError ProviderBadRequestError advice untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_check_suggest.py b/tests/unit/test_check_suggest.py
new file mode 100644
index 0000000..7a67181
--- /dev/null
+++ b/tests/unit/test_check_suggest.py
@@ -0,0 +1,55 @@
+"""providers.check._suggest: 失敗の種類ごとに、次に取れる行動を案内すること."""
+
+from __future__ import annotations
+
+from types import SimpleNamespace
+from typing import Any
+
+import pytest
+
+from security_checker.providers.check import _suggest
+from security_checker.providers.errors import (
+    ProviderAuthError,
+    ProviderBadRequestError,
+    ProviderError,
+    ProviderRateLimitError,
+    ProviderTimeoutError,
+)
+
+
+def _reviewer(**overrides: Any) -> Any:
+    """_suggest が読む項目だけを持つ、設定の代役."""
+    fields = {
+        "api_key_env": "EXAMPLE_API_KEY",
+        "timeout_s": 45.0,
+        "transport": "http",
+        "base_url": "https://api.example.com/v1",
+    }
+    fields.update(overrides)
+    return SimpleNamespace(**fields)
+
+
+@pytest.mark.parametrize(
+    ("exc", "expected"),
+    [
+        (ProviderAuthError("x"), "EXAMPLE_API_KEY の値"),
+        (ProviderRateLimitError("x"), "rate_limit.rpm を下げる"),
+        (ProviderTimeoutError("x"), "timeout_s (現在 45.0) を延ばしてください"),
+        (ProviderBadRequestError("x"), "structured_output: prompt_only"),
+        (ProviderError("x"), "base_url (https://api.example.com/v1) に到達できるか"),
+    ],
+)
+def test_each_failure_gets_its_own_advice(exc: Exception, expected: str) -> None:
+    assert expected in _suggest(exc, _reviewer())
+
+
+def test_auth_error_without_a_key_variable_names_a_generic_one() -> None:
+    advice = _suggest(ProviderAuthError("x"), _reviewer(api_key_env=None))
+
+    assert "API キーの環境変数 の値" in advice
+
+
+def test_other_failure_of_a_process_reviewer_points_at_the_command() -> None:
+    advice = _suggest(ProviderError("x"), _reviewer(transport="process"))
+
+    assert "command が非対話で JSON を標準出力に返すか" in advice
`````

[Back to the shelf](README.md)
