# Fix 126: SMART toolkit: a config file with the same key written twice silently loses the first block

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: config: Reject duplicate YAML keys in socialagent.&lt;env>.yaml
- Bug report: number 65 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/65))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/126-social-messaging-agent-runtime-toolkit-65.patch](fixes/126-social-messaging-agent-runtime-toolkit-65.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/126-social-messaging-agent-runtime-toolkit-65.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-126-social-messaging-agent-runtime-toolkit-65.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-126-social-messaging-agent-runtime-toolkit-65.html

## The bug

load() in src/socialagent/cli/config_file.py read socialagent.<env>.yaml with yaml.safe_load. That function keeps the last of two identical keys with no warning. A second pasted terraform: block dropped every setting of the first block and a later save of the file lost the settings for good.

## The fix

The file is now read with a SafeLoader subclass that raises on a repeated key. load() and file_schema_version() both use the loader and the ConfigError names the key and the line. A new file tests/test_cli_config_duplicate_keys.py covers a repeated top-level key and a repeated nested key and a file with no repeat. CHANGELOG.md gains one line under Unreleased.

## Files changed

- CHANGELOG.md
- src/socialagent/cli/config_file.py
- tests/test_cli_config_duplicate_keys.py

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 126-social-messaging-agent-runtime-toolkit-65.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 65.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- file_schema_version() used to let a raw YAML error through for a broken file and now raises ConfigError like load() does. The chatbot ran a scratch copy of the loader on four small YAML texts (including a merge key). The chatbot did not run the project's tests. Fixes 72 and 96 and 97 and 99 and 126 and 128 and 129 on this shelf each add text at the same spot of CHANGELOG.md so those patches do not apply one after another: apply one patch and add the other changelog lines by hand.

## Search words

SMART socialagent config_file load yaml.safe_load duplicate key terraform block SafeLoader ConfigError line

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 6ecb773..5f89538 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -4,6 +4,9 @@ All notable changes to SMART, the Social Messaging Agent Runtime Toolkit, are re
 
 ## [Unreleased]
 
+### Fixed
+- `socialagent.<env>.yaml` with the same key written twice (for example two `terraform:` blocks) is refused with an error that names the key and its line; before, the last block silently replaced the first.
+
 ## [2026.10.0] - 2026-11-05
 
 The first public release. Everything below was in the toolkit when it was published.
diff --git a/src/socialagent/cli/config_file.py b/src/socialagent/cli/config_file.py
index 7d36629..55d1209 100644
--- a/src/socialagent/cli/config_file.py
+++ b/src/socialagent/cli/config_file.py
@@ -51,6 +51,43 @@ def find_config(project_dir: Path, env: str = "dev") -> Path:
     return project_dir / f"socialagent.{env}.yaml"
 
 
+class _UniqueKeyLoader(yaml.SafeLoader):
+    """A ``SafeLoader`` that refuses a mapping with the same key written twice.
+
+    Plain ``yaml.safe_load`` keeps the last of two identical keys without a
+    word, so a second pasted ``terraform:`` block drops every setting of the
+    first one.
+    """
+
+    def construct_mapping(
+        self, node: yaml.MappingNode, deep: bool = False
+    ) -> dict:
+        seen: set[str] = set()
+        for key_node, _ in node.value:
+            if not isinstance(key_node, yaml.ScalarNode):
+                continue
+            if key_node.value in seen:
+                raise yaml.constructor.ConstructorError(
+                    None,
+                    None,
+                    f"duplicate key {key_node.value!r} "
+                    f"on line {key_node.start_mark.line + 1}; keep one block per key",
+                    key_node.start_mark,
+                )
+            seen.add(key_node.value)
+        return super().construct_mapping(node, deep=deep)
+
+
+def _load_yaml(path: Path) -> Any:
+    """Parse *path* as YAML; a ConfigError names a duplicated key and its line."""
+    try:
+        text = path.read_text(encoding="utf-8")
+        # A SafeLoader subclass: no arbitrary object construction.
+        return yaml.load(text, Loader=_UniqueKeyLoader) or {}
+    except yaml.YAMLError as exc:
+        raise ConfigError(f"{path.name} is not valid YAML: {exc}") from exc
+
+
 def load(path: Path) -> dict[str, Any]:
     """Load and return an socialagent config file, or empty dict if missing.
 
@@ -59,10 +96,7 @@ def load(path: Path) -> dict[str, Any]:
     """
     if not path.exists():
         return {}
-    try:
-        config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
-    except yaml.YAMLError as exc:
-        raise ConfigError(f"{path.name} is not valid YAML: {exc}") from exc
+    config = _load_yaml(path)
     if not isinstance(config, dict):
         raise ConfigError(f"{path.name} must be a YAML mapping of fields")
     # v1/v2 files are read as v3 in memory (lossless); the file is rewritten
@@ -92,7 +126,7 @@ def check_environment(config: dict[str, Any], env_name: str, path: Path) -> None
 
 def file_schema_version(path: Path) -> int:
     """The ``schema_version`` written in *path*, before :func:`load` upgrades it."""
-    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
+    raw = _load_yaml(path)
     version = raw.get("schema_version", 1) if isinstance(raw, dict) else 1
     return version if isinstance(version, int) else 1
 
diff --git a/tests/test_cli_config_duplicate_keys.py b/tests/test_cli_config_duplicate_keys.py
new file mode 100644
index 0000000..caed2ad
--- /dev/null
+++ b/tests/test_cli_config_duplicate_keys.py
@@ -0,0 +1,55 @@
+"""A config file with the same key written twice is refused, not silently merged."""
+
+from __future__ import annotations
+
+import pytest
+
+from socialagent.cli._errors import ConfigError
+from socialagent.cli.config_file import file_schema_version, load
+
+_TWO_TERRAFORM_BLOCKS = (
+    "schema_version: 3\n"
+    "environment: dev\n"
+    "terraform:\n"
+    "  aws_region: us-east-1\n"
+    "terraform:\n"
+    "  enable_deployment_metrics: false\n"
+)
+
+
+def test_load_names_a_duplicated_top_level_key_and_its_line(tmp_path):
+    path = tmp_path / "socialagent.dev.yaml"
+    path.write_text(_TWO_TERRAFORM_BLOCKS, encoding="utf-8")
+
+    with pytest.raises(ConfigError) as excinfo:
+        load(path)
+
+    message = str(excinfo.value)
+    assert "duplicate key 'terraform'" in message
+    assert "line 5" in message
+
+
+def test_load_names_a_duplicated_nested_key(tmp_path):
+    path = tmp_path / "socialagent.dev.yaml"
+    path.write_text(
+        "terraform:\n  aws_region: us-east-1\n  aws_region: eu-west-1\n",
+        encoding="utf-8",
+    )
+
+    with pytest.raises(ConfigError, match="duplicate key 'aws_region' on line 3"):
+        load(path)
+
+
+def test_file_schema_version_refuses_a_duplicated_key(tmp_path):
+    path = tmp_path / "socialagent.dev.yaml"
+    path.write_text(_TWO_TERRAFORM_BLOCKS, encoding="utf-8")
+
+    with pytest.raises(ConfigError, match="duplicate key 'terraform'"):
+        file_schema_version(path)
+
+
+def test_the_same_key_in_two_different_blocks_still_loads(tmp_path):
+    path = tmp_path / "socialagent.dev.yaml"
+    path.write_text("a:\n  name: one\nb:\n  name: two\n", encoding="utf-8")
+
+    assert file_schema_version(path) == 1
`````

[Back to the shelf](README.md)
