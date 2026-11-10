# Fix 213: security-checker: no test covers a config file that cannot be read or has the wrong shape

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(config): loader.py の _read_yaml で未テストの分岐をテストする（4 行）
- Bug report: number 489 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/489))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/213-security-checker-489.patch](fixes/213-security-checker-489.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/213-security-checker-489.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-213-security-checker-489.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-213-security-checker-489.html

## The bug

_read_yaml in src/security_checker/config/loader.py raises ConfigError for an unreadable file and for a top level that is not a mapping and returns an empty mapping for an empty file. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_config_read_yaml_errors.py checks a folder and a missing file and a comment-only file and two wrong shapes and broken YAML.

## Files changed

- tests/unit/test_config_read_yaml_errors.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 213-security-checker-489.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 489.

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

security-checker config loader _read_yaml OSError empty file top level mapping ConfigError untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_config_read_yaml_errors.py b/tests/unit/test_config_read_yaml_errors.py
new file mode 100644
index 0000000..0899adc
--- /dev/null
+++ b/tests/unit/test_config_read_yaml_errors.py
@@ -0,0 +1,45 @@
+"""config.loader._read_yaml: 読めない・空・形の違う設定ファイルの扱い."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker.config.loader import _read_yaml
+from security_checker.errors import ConfigError
+
+
+def test_unreadable_path_is_a_config_error(tmp_path: Path) -> None:
+    # ディレクトリを渡すと read_text が OSError になる
+    with pytest.raises(ConfigError, match="を読み込めません"):
+        _read_yaml(tmp_path)
+
+
+def test_missing_file_is_a_config_error(tmp_path: Path) -> None:
+    with pytest.raises(ConfigError, match="absent.yml"):
+        _read_yaml(tmp_path / "absent.yml")
+
+
+def test_empty_file_is_an_empty_mapping(tmp_path: Path) -> None:
+    path = tmp_path / "config.yml"
+    path.write_text("# コメントだけ\n", encoding="utf-8")
+
+    assert _read_yaml(path) == {}
+
+
+@pytest.mark.parametrize("text", ["- a\n- b\n", "just text\n"])
+def test_top_level_that_is_not_a_mapping_is_a_config_error(tmp_path: Path, text: str) -> None:
+    path = tmp_path / "config.yml"
+    path.write_text(text, encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="トップレベルはマッピング"):
+        _read_yaml(path)
+
+
+def test_invalid_yaml_is_a_config_error(tmp_path: Path) -> None:
+    path = tmp_path / "config.yml"
+    path.write_text("policy: [unclosed\n", encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="YAML を解釈できません"):
+        _read_yaml(path)
`````

[Back to the shelf](README.md)
