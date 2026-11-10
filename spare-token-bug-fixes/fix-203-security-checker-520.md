# Fix 203: security-checker: no test covers a less-or-equal comparison of a severity with another type

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(models): enums.py の __le__ で未テストの分岐をテストする（1 行）
- Bug report: number 520 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/520))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/203-security-checker-520.patch](fixes/203-security-checker-520.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/203-security-checker-520.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-203-security-checker-520.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-203-security-checker-520.html

## The bug

Severity.__le__ in src/security_checker/models/enums.py returns NotImplemented for a value that is not a severity. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_severity_le_other_type.py expects NotImplemented for four other values and a TypeError for a comparison with a number and checks the order between two severities.

## Files changed

- tests/unit/test_severity_le_other_type.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 203-security-checker-520.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 520.

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

security-checker enums Severity __le__ NotImplemented TypeError comparison untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_severity_le_other_type.py b/tests/unit/test_severity_le_other_type.py
new file mode 100644
index 0000000..af78011
--- /dev/null
+++ b/tests/unit/test_severity_le_other_type.py
@@ -0,0 +1,23 @@
+"""Severity の比較: Severity 以外との <= は NotImplemented を返し、TypeError になること."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.models.enums import Severity
+
+
+@pytest.mark.parametrize("other", [3, "high", None, 2.5])
+def test_less_or_equal_with_another_type_is_not_implemented(other: object) -> None:
+    assert Severity.HIGH.__le__(other) is NotImplemented
+
+
+def test_less_or_equal_with_an_int_raises_type_error() -> None:
+    with pytest.raises(TypeError):
+        _ = Severity.HIGH <= 3  # type: ignore[operator]
+
+
+def test_less_or_equal_between_severities_follows_the_order() -> None:
+    """対になるケース. Severity どうしは深刻さの順で比べる."""
+    assert Severity.HIGH <= Severity.HIGH
+    assert not (Severity.HIGH <= Severity.LOW)
`````

[Back to the shelf](README.md)
