# Fix 214: security-checker: no test covers a report file that is missing or unreadable in explain

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(observability): explain.py の load_report で未テストの分岐をテストする（3 行）
- Bug report: number 525 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/525))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/214-security-checker-525.patch](fixes/214-security-checker-525.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/214-security-checker-525.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-214-security-checker-525.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-214-security-checker-525.html

## The bug

load_report in src/security_checker/observability/explain.py raises ConfigError for a missing report and for a report that cannot be read. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_explain_load_report_errors.py checks a missing file and a folder and three unreadable contents.

## Files changed

- tests/unit/test_explain_load_report_errors.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 214-security-checker-525.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 525.

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

security-checker explain load_report missing report.json ConfigError invalid JSON untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_explain_load_report_errors.py b/tests/unit/test_explain_load_report_errors.py
new file mode 100644
index 0000000..ff8b86b
--- /dev/null
+++ b/tests/unit/test_explain_load_report_errors.py
@@ -0,0 +1,29 @@
+"""explain.load_report: レポートが無い・読めないときは ConfigError になること."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker.errors import ConfigError
+from security_checker.observability.explain import load_report
+
+
+def test_missing_report_is_a_config_error(tmp_path: Path) -> None:
+    with pytest.raises(ConfigError, match="レポートが見つかりません"):
+        load_report(tmp_path / "report.json")
+
+
+def test_directory_is_a_config_error(tmp_path: Path) -> None:
+    with pytest.raises(ConfigError, match="レポートが見つかりません"):
+        load_report(tmp_path)
+
+
+@pytest.mark.parametrize("text", ["not json", "{}", "[]"])
+def test_unreadable_report_is_a_config_error(tmp_path: Path, text: str) -> None:
+    path = tmp_path / "report.json"
+    path.write_text(text, encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="レポートを読めません"):
+        load_report(path)
`````

[Back to the shelf](README.md)
