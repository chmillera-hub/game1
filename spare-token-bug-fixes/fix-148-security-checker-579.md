# Fix 148: security-checker: no test covers a path that starts with ./ in relative_path

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(scanners): base.py の relative_path で未テストの分岐をテストする（1 行）
- Bug report: number 579 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/579))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/148-security-checker-579.patch](fixes/148-security-checker-579.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/148-security-checker-579.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-148-security-checker-579.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-148-security-checker-579.html

## The bug

relative_path in src/security_checker/scanners/base.py removes a leading ./ from a scanner's path. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_scanner_base_relative_path_dot_slash.py checks ./src/app.py and the backslash form and a doubled prefix and a path without the prefix.

## Files changed

- tests/unit/test_scanner_base_relative_path_dot_slash.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 148-security-checker-579.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 579.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 142 on this shelf rewrites the same line with removeprefix and the tests hold for both forms. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker scanners base relative_path leading ./ prefix removed untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_scanner_base_relative_path_dot_slash.py b/tests/unit/test_scanner_base_relative_path_dot_slash.py
new file mode 100644
index 0000000..9ed31ea
--- /dev/null
+++ b/tests/unit/test_scanner_base_relative_path_dot_slash.py
@@ -0,0 +1,23 @@
+"""relative_path: 先頭の "./" を落とすこと."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+from security_checker.scanners.base import relative_path
+
+
+def test_leading_dot_slash_is_removed(tmp_path: Path) -> None:
+    assert relative_path("./src/app.py", tmp_path) == "src/app.py"
+
+
+def test_backslash_form_is_normalized_first(tmp_path: Path) -> None:
+    assert relative_path(".\\src\\app.py", tmp_path) == "src/app.py"
+
+
+def test_only_one_leading_dot_slash_is_removed(tmp_path: Path) -> None:
+    assert relative_path("././src/app.py", tmp_path) == "./src/app.py"
+
+
+def test_path_without_the_prefix_is_unchanged(tmp_path: Path) -> None:
+    assert relative_path("src/app.py", tmp_path) == "src/app.py"
`````

[Back to the shelf](README.md)
