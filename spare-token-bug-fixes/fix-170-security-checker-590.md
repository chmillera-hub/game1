# Fix 170: security-checker: no test covers an unknown bundled rule name in resolve_config

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(scanners): semgrep.py の resolve_config で未テストの分岐をテストする（1 行）
- Bug report: number 590 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/590))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/170-security-checker-590.patch](fixes/170-security-checker-590.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/170-security-checker-590.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-170-security-checker-590.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-170-security-checker-590.html

## The bug

resolve_config in src/security_checker/scanners/semgrep.py raises ConfigError for a bundled: name that does not exist. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_semgrep_resolve_config_unknown_bundled.py expects ConfigError for an unknown name and an empty name and a name with a path in it and expects values without the prefix to pass through unchanged.

## Files changed

- tests/unit/test_semgrep_resolve_config_unknown_bundled.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 170-security-checker-590.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 590.

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

security-checker semgrep resolve_config bundled: unknown rule ConfigError untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_semgrep_resolve_config_unknown_bundled.py b/tests/unit/test_semgrep_resolve_config_unknown_bundled.py
new file mode 100644
index 0000000..96a4a06
--- /dev/null
+++ b/tests/unit/test_semgrep_resolve_config_unknown_bundled.py
@@ -0,0 +1,20 @@
+"""resolve_config: 存在しない同梱ルールの名前は ConfigError になること."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.errors import ConfigError
+from security_checker.scanners.semgrep import resolve_config
+
+
+@pytest.mark.parametrize("value", ["bundled:no-such-rule", "bundled:", "bundled:../llm"])
+def test_unknown_bundled_rule_is_a_config_error(value: str) -> None:
+    with pytest.raises(ConfigError, match="未知の同梱ルール"):
+        resolve_config(value)
+
+
+@pytest.mark.parametrize("value", ["p/default", "rules/custom.yml", "auto"])
+def test_value_without_the_bundled_prefix_is_passed_through(value: str) -> None:
+    """対になるケース. レジストリ名やパスは変えずに渡す."""
+    assert resolve_config(value) == value
`````

[Back to the shelf](README.md)
