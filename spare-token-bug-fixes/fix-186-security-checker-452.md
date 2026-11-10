# Fix 186: security-checker: a pricing.yml whose top level is a list crashes with AttributeError

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(observability): pricing.yml のトップレベルがリストだと AttributeError で落ちる
- Bug report: number 452 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/452))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/186-security-checker-452.patch](fixes/186-security-checker-452.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/186-security-checker-452.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-186-security-checker-452.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-186-security-checker-452.html

## The bug

load_price_table in src/security_checker/observability/cost.py called raw.get on whatever the YAML file held. A top level that is a list or plain text has no get so the program ended with an AttributeError traceback where a ConfigError belongs.

## The fix

The loader now raises ConfigError when the top level is not a mapping. A new file tests/unit/test_cost_top_level_shape.py checks a list and plain text and a number and checks that an empty file still gives an empty table.

## Files changed

- src/security_checker/observability/cost.py
- tests/unit/test_cost_top_level_shape.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 186-security-checker-452.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 452.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report asks for a test of exit code 2 with a formatted message. The new tests check the ConfigError at the loader and not the exit code of the command line. The chatbot did not run the tests.

## Search words

security-checker pricing.yml load_price_table top level list AttributeError ConfigError raw.get models mapping

## The full patch

`````diff
diff --git a/src/security_checker/observability/cost.py b/src/security_checker/observability/cost.py
index 2ec7b56..a55ed38 100644
--- a/src/security_checker/observability/cost.py
+++ b/src/security_checker/observability/cost.py
@@ -68,6 +68,8 @@ def load_price_table(config_dir: Path | None = None, explicit: Path | None = Non
             raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
         except (OSError, yaml.YAMLError) as exc:
             raise ConfigError(f"{path} を読み込めません: {exc}") from exc
+        if not isinstance(raw, dict):
+            raise ConfigError(f"{path}: トップレベルはマッピングである必要があります")
         entries = raw.get("models", raw)
         if not isinstance(entries, dict):
             raise ConfigError(f"{path}: models はマッピングである必要があります")
diff --git a/tests/unit/test_cost_top_level_shape.py b/tests/unit/test_cost_top_level_shape.py
new file mode 100644
index 0000000..bc1ca15
--- /dev/null
+++ b/tests/unit/test_cost_top_level_shape.py
@@ -0,0 +1,35 @@
+"""pricing.yml のトップレベルがマッピングでなければ ConfigError になること."""
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
+@pytest.mark.parametrize("text", ["- m\n- n\n", "just text\n", "3\n"])
+def test_top_level_that_is_not_a_mapping_is_a_config_error(tmp_path: Path, text: str) -> None:
+    path = tmp_path / "pricing.yml"
+    path.write_text(text, encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="トップレベルはマッピング"):
+        load_price_table(explicit=path)
+
+
+def test_models_that_is_not_a_mapping_is_still_a_config_error(tmp_path: Path) -> None:
+    path = tmp_path / "pricing.yml"
+    path.write_text("models:\n  - m\n", encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="models はマッピング"):
+        load_price_table(explicit=path)
+
+
+def test_empty_file_is_an_empty_table(tmp_path: Path) -> None:
+    """対になるケース. 空のファイルは「価格の定義なし」として読める."""
+    path = tmp_path / "pricing.yml"
+    path.write_text("", encoding="utf-8")
+
+    assert load_price_table(explicit=path).prices == {}
`````

[Back to the shelf](README.md)
