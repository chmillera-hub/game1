# Fix 256: security-checker: no test covers the log level option of the command line

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(cli): cli.py の _logging_overrides で未テストの分岐をテストする（1 行）
- Bug report: number 473 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/473))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/256-security-checker-473.patch](fixes/256-security-checker-473.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/256-security-checker-473.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-256-security-checker-473.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-256-security-checker-473.html

## The bug

_logging_overrides in src/security_checker/cli.py turns the log level option into a settings override. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_cli_logging_overrides.py checks the level alone and the format alone and both and neither.

## Files changed

- tests/unit/test_cli_logging_overrides.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 256-security-checker-473.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 473.

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

security-checker cli _logging_overrides log level format override untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_cli_logging_overrides.py b/tests/unit/test_cli_logging_overrides.py
new file mode 100644
index 0000000..eada46f
--- /dev/null
+++ b/tests/unit/test_cli_logging_overrides.py
@@ -0,0 +1,21 @@
+"""cli._logging_overrides: 指定されたログの設定だけを上書きにすること."""
+
+from __future__ import annotations
+
+from security_checker.cli import _logging_overrides
+
+
+def test_level_alone_overrides_only_the_level() -> None:
+    assert _logging_overrides(None, "debug") == {"logging": {"level": "debug"}}
+
+
+def test_format_alone_overrides_only_the_format() -> None:
+    assert _logging_overrides("json", None) == {"logging": {"format": "json"}}
+
+
+def test_both_are_combined() -> None:
+    assert _logging_overrides("json", "warn") == {"logging": {"format": "json", "level": "warn"}}
+
+
+def test_nothing_given_is_no_override() -> None:
+    assert _logging_overrides(None, None) == {}
`````

[Back to the shelf](README.md)
