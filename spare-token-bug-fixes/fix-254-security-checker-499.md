# Fix 254: security-checker: no test covers evaluation cases that cannot be read or have the wrong shape

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(eval): dataset.py の load_dataset で未テストの分岐をテストする（3 行）
- Bug report: number 499 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/499))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/254-security-checker-499.patch](fixes/254-security-checker-499.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/254-security-checker-499.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-254-security-checker-499.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-254-security-checker-499.html

## The bug

load_dataset in src/security_checker/eval/dataset.py raises ConfigError for a case file that is not valid YAML or whose top level is not a mapping. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_eval_dataset_load_errors.py checks a missing cases folder and an empty one and broken YAML and three wrong shapes and a case with missing fields.

## Files changed

- tests/unit/test_eval_dataset_load_errors.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 254-security-checker-499.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 499.

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

security-checker eval dataset load_dataset YAMLError top level mapping ConfigError cases untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_eval_dataset_load_errors.py b/tests/unit/test_eval_dataset_load_errors.py
new file mode 100644
index 0000000..cd3ed37
--- /dev/null
+++ b/tests/unit/test_eval_dataset_load_errors.py
@@ -0,0 +1,50 @@
+"""eval.dataset.load_dataset: 壊れたケースを黙って飛ばさず ConfigError にすること."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker.errors import ConfigError
+from security_checker.eval.dataset import load_dataset
+
+
+def _cases(tmp_path: Path) -> Path:
+    cases = tmp_path / "cases"
+    cases.mkdir()
+    return cases
+
+
+def test_missing_cases_directory_is_a_config_error(tmp_path: Path) -> None:
+    with pytest.raises(ConfigError, match="評価ケースが見つかりません"):
+        load_dataset(tmp_path)
+
+
+def test_empty_cases_directory_is_a_config_error(tmp_path: Path) -> None:
+    _cases(tmp_path)
+
+    with pytest.raises(ConfigError, match="評価ケースが 1 件もありません"):
+        load_dataset(tmp_path)
+
+
+def test_invalid_yaml_is_a_config_error_that_names_the_file(tmp_path: Path) -> None:
+    (_cases(tmp_path) / "broken.yaml").write_text("id: [unclosed\n", encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="broken.yaml を読み込めません"):
+        load_dataset(tmp_path)
+
+
+@pytest.mark.parametrize("text", ["- a\n- b\n", "just text\n", ""])
+def test_top_level_that_is_not_a_mapping_is_a_config_error(tmp_path: Path, text: str) -> None:
+    (_cases(tmp_path) / "shape.yml").write_text(text, encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="トップレベルはマッピング"):
+        load_dataset(tmp_path)
+
+
+def test_case_with_missing_fields_is_a_config_error(tmp_path: Path) -> None:
+    (_cases(tmp_path) / "thin.yaml").write_text("id: thin\n", encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="thin.yaml が不正です"):
+        load_dataset(tmp_path)
`````

[Back to the shelf](README.md)
