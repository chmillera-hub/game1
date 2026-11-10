# Fix 255: security-checker: no test covers the edge cases of settings taken from environment variables

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(config): loader.py の env_overrides で未テストの分岐をテストする（5 行）
- Bug report: number 490 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/490))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/255-security-checker-490.patch](fixes/255-security-checker-490.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/255-security-checker-490.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-255-security-checker-490.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-255-security-checker-490.html

## The bug

env_overrides in src/security_checker/config/loader.py skips a key that is only the prefix and keeps a value that is not valid YAML as text and replaces an earlier plain value with a nested one. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_config_env_overrides_edges.py checks all three cases and a normal case with a number and a boolean.

## Files changed

- tests/unit/test_config_env_overrides_edges.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 255-security-checker-490.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 490.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a scratch copy of the function on the four inputs. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker config loader env_overrides SECURITY_CHECKER__ prefix YAMLError nested override untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_config_env_overrides_edges.py b/tests/unit/test_config_env_overrides_edges.py
new file mode 100644
index 0000000..4057b63
--- /dev/null
+++ b/tests/unit/test_config_env_overrides_edges.py
@@ -0,0 +1,32 @@
+"""config.loader.env_overrides: 接頭辞だけのキー・YAML でない値・入れ子の上書きの扱い."""
+
+from __future__ import annotations
+
+from security_checker.config.loader import ENV_PREFIX, env_overrides
+
+
+def test_key_that_is_only_the_prefix_is_ignored() -> None:
+    assert env_overrides({ENV_PREFIX: "x", ENV_PREFIX + "__": "y"}) == {}
+
+
+def test_value_that_is_not_valid_yaml_is_kept_as_text() -> None:
+    overrides = env_overrides({ENV_PREFIX + "OUTPUT__DIR": "[unclosed"})
+
+    assert overrides == {"output": {"dir": "[unclosed"}}
+
+
+def test_nested_key_replaces_an_earlier_scalar_at_the_same_place() -> None:
+    environ = {ENV_PREFIX + "POLICY": "3", ENV_PREFIX + "POLICY__FAIL_ON": "critical"}
+
+    assert env_overrides(environ) == {"policy": {"fail_on": "critical"}}
+
+
+def test_values_are_read_as_yaml_and_other_variables_are_ignored() -> None:
+    """対になるケース. 数値や真偽値は YAML として読み、接頭辞の無い変数は見ない."""
+    environ = {
+        ENV_PREFIX + "POLICY__MIN_SCORE": "70",
+        ENV_PREFIX + "POLICY__STRICT": "true",
+        "PATH": "/usr/bin",
+    }
+
+    assert env_overrides(environ) == {"policy": {"min_score": 70, "strict": True}}
`````

[Back to the shelf](README.md)
