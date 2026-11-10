# Fix 218: security-checker: no test covers a pricing file that is not valid YAML

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(observability): cost.py の load_price_table で未テストの分岐をテストする（3 行）
- Bug report: number 522 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/522))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/218-security-checker-522.patch](fixes/218-security-checker-522.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/218-security-checker-522.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-218-security-checker-522.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-218-security-checker-522.html

## The bug

load_price_table in src/security_checker/observability/cost.py raises ConfigError for a pricing file that cannot be read as YAML. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_cost_load_price_table_unreadable.py checks broken YAML and a price that is not a number and a missing file.

## Files changed

- tests/unit/test_cost_load_price_table_unreadable.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 218-security-checker-522.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 522.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Fix 186 on this shelf covers the other untested line of the same function (a models value that is not a mapping). The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker cost load_price_table pricing.yml YAMLError ConfigError untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_cost_load_price_table_unreadable.py b/tests/unit/test_cost_load_price_table_unreadable.py
new file mode 100644
index 0000000..f2be144
--- /dev/null
+++ b/tests/unit/test_cost_load_price_table_unreadable.py
@@ -0,0 +1,31 @@
+"""load_price_table: YAML として読めない pricing.yml は ConfigError になること."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker.errors import ConfigError
+from security_checker.observability.cost import load_price_table
+
+
+def test_invalid_yaml_is_a_config_error_that_names_the_file(tmp_path: Path) -> None:
+    path = tmp_path / "pricing.yml"
+    path.write_text("models: [unclosed\n", encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="pricing.yml を読み込めません"):
+        load_price_table(explicit=path)
+
+
+def test_price_that_is_not_a_number_is_a_config_error(tmp_path: Path) -> None:
+    path = tmp_path / "pricing.yml"
+    path.write_text("models:\n  m:\n    input_per_1m: cheap\n", encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="価格定義が不正です"):
+        load_price_table(explicit=path)
+
+
+def test_missing_explicit_file_is_an_empty_table(tmp_path: Path) -> None:
+    """対になるケース. 指定したファイルが無ければ空表 (すべて cost unknown)."""
+    assert load_price_table(explicit=tmp_path / "absent.yml").prices == {}
`````

[Back to the shelf](README.md)
