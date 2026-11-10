# Fix 145: security-checker: no test covers a max_severity that is not a number in _group_severity

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(scanners): osv.py の _group_severity で未テストの分岐をテストする（2 行）
- Bug report: number 584 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/584))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/145-security-checker-584.patch](fixes/145-security-checker-584.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/145-security-checker-584.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-145-security-checker-584.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-145-security-checker-584.html

## The bug

_group_severity in src/security_checker/scanners/osv.py falls back to the text severity when max_severity cannot be read as a number. No test ran that fallback.

## The fix

Tests only. A new file tests/unit/test_osv_group_severity_non_numeric.py gives a non-numeric max_severity and expects the heaviest text severity (HIGH) or None when no text severity exists. A paired test checks that a readable number still wins.

## Files changed

- tests/unit/test_osv_group_severity_non_numeric.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 145-security-checker-584.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 584.

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

security-checker osv _group_severity max_severity ValueError non-numeric database_specific severity fallback untested

## The full patch

`````diff
diff --git a/tests/unit/test_osv_group_severity_non_numeric.py b/tests/unit/test_osv_group_severity_non_numeric.py
new file mode 100644
index 0000000..54e7320
--- /dev/null
+++ b/tests/unit/test_osv_group_severity_non_numeric.py
@@ -0,0 +1,27 @@
+"""_group_severity: max_severity が数値として読めないときの振る舞い."""
+
+from __future__ import annotations
+
+from security_checker.models.enums import Severity
+from security_checker.scanners.osv import _group_severity
+
+
+def test_non_numeric_max_severity_falls_back_to_the_text_severity() -> None:
+    group = {"max_severity": "not-a-number"}
+    vulns = [
+        {"database_specific": {"severity": "LOW"}},
+        {"database_specific": {"severity": "HIGH"}},
+    ]
+
+    assert _group_severity(group, vulns) is Severity.HIGH
+
+
+def test_non_numeric_max_severity_without_text_severity_is_none() -> None:
+    assert _group_severity({"max_severity": "not-a-number"}, [{}]) is None
+
+
+def test_numeric_max_severity_still_wins_over_the_text_severity() -> None:
+    """対になるケース. 数値が読めれば文字列表記は使わない."""
+    vulns = [{"database_specific": {"severity": "LOW"}}]
+
+    assert _group_severity({"max_severity": "9.8"}, vulns) is Severity.CRITICAL
`````

[Back to the shelf](README.md)
