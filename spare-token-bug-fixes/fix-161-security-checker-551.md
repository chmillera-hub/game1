# Fix 161: security-checker: no test covers a preset file that cannot be read or has the wrong shape

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): loader.py の _read_presets で未テストの分岐をテストする（3 行）
- Bug report: number 551 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/551))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/161-security-checker-551.patch](fixes/161-security-checker-551.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/161-security-checker-551.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-161-security-checker-551.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-161-security-checker-551.html

## The bug

_read_presets in src/security_checker/providers/presets/loader.py raises ConfigError for a preset file that is not valid YAML or cannot be read or whose top level is not a mapping. No test ran those three lines.

## The fix

Tests only. A new file tests/unit/test_presets_read_errors.py checks broken YAML and an unreadable entry (a folder named like a .yml file) and three top levels that are not mappings and a missing folder.

## Files changed

- tests/unit/test_presets_read_errors.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 161-security-checker-551.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 551.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A scratch script confirmed how the YAML library reads the four small texts. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker presets loader _read_presets YAML error OSError top level mapping ConfigError untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_presets_read_errors.py b/tests/unit/test_presets_read_errors.py
new file mode 100644
index 0000000..0fe3019
--- /dev/null
+++ b/tests/unit/test_presets_read_errors.py
@@ -0,0 +1,38 @@
+"""_read_presets: 読めない・形の違うプリセットファイルは ConfigError になること."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker.errors import ConfigError
+from security_checker.providers.presets.loader import HttpPreset, _read_presets
+
+
+def test_invalid_yaml_is_a_config_error_that_names_the_file(tmp_path: Path) -> None:
+    path = tmp_path / "broken.yml"
+    path.write_text("dialect: [unclosed\n", encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="broken.yml"):
+        _read_presets(tmp_path, "user", HttpPreset)
+
+
+def test_unreadable_file_is_a_config_error(tmp_path: Path) -> None:
+    # ディレクトリを *.yml の名前で置くと read_text が OSError になる
+    (tmp_path / "folder.yml").mkdir()
+
+    with pytest.raises(ConfigError, match="folder.yml"):
+        _read_presets(tmp_path, "user", HttpPreset)
+
+
+@pytest.mark.parametrize("text", ["- a\n- b\n", "just text\n", "3\n"])
+def test_top_level_that_is_not_a_mapping_is_a_config_error(tmp_path: Path, text: str) -> None:
+    (tmp_path / "shape.yml").write_text(text, encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="マッピング"):
+        _read_presets(tmp_path, "user", HttpPreset)
+
+
+def test_missing_directory_gives_no_presets(tmp_path: Path) -> None:
+    assert _read_presets(tmp_path / "absent", "user", HttpPreset) == {}
`````

[Back to the shelf](README.md)
