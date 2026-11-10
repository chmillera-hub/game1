# Fix 72: SMART toolkit: socialagent templates validate fails in a project that has no templates.yaml

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: cli: templates validate fails on a project with no templates.yaml
- Bug report: number 83 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/83))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/72-social-messaging-agent-runtime-toolkit-83.patch](fixes/72-social-messaging-agent-runtime-toolkit-83.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/72-social-messaging-agent-runtime-toolkit-83.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-72-social-messaging-agent-runtime-toolkit-83.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-72-social-messaging-agent-runtime-toolkit-83.html

## The bug

A project made with the minimal blueprint has no templates.yaml. In that project socialagent templates validate ended with the error templates file not found. A continuous integration step that validates every project failed on the minimal project even though the project has nothing to validate.

## The fix

src/socialagent/cli/templates.py gains _configured_templates_path which returns the path a person chose with --templates or whatsapp.templates in the project file or TEMPLATES_PATH and returns an empty text when nobody chose a path. cmd_templates_validate prints No templates to check and returns normally when nobody chose a path and the default templates.yaml is absent. A chosen path that does not exist is still an error. A new file tests/test_cli_templates_validate_missing.py covers the three cases. CHANGELOG.md gains one line under Unreleased.

## Files changed

- CHANGELOG.md
- src/socialagent/cli/templates.py
- tests/test_cli_templates_validate_missing.py

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 72-social-messaging-agent-runtime-toolkit-83.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 83.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The exact wording of the new message is the chatbot's choice. templates sync is unchanged and still reports a missing file as an error. The chatbot did not run the project's code or tests and did not run a formatter. Fixes 72 and 96 and 97 and 99 on this shelf each add a line at the same spot of CHANGELOG.md so those patches do not apply one after another: apply one patch and add the other changelog lines by hand. The other files in those patches do not overlap.

## Search words

socialagent templates validate templates file not found minimal blueprint templates.yaml TEMPLATES_PATH cmd_templates_validate

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 6ecb773..936f595 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -4,6 +4,9 @@ All notable changes to SMART, the Social Messaging Agent Runtime Toolkit, are re
 
 ## [Unreleased]
 
+### Fixed
+- `socialagent templates validate` exits 0 with "No templates to check" in a project that has no `templates.yaml` and no configured templates path (the minimal blueprint). A path given with `--templates`, `TEMPLATES_PATH` or `whatsapp.templates` that does not exist is still an error.
+
 ## [2026.10.0] - 2026-11-05
 
 The first public release. Everything below was in the toolkit when it was published.
diff --git a/src/socialagent/cli/templates.py b/src/socialagent/cli/templates.py
index 6ebdceb..0c66c65 100644
--- a/src/socialagent/cli/templates.py
+++ b/src/socialagent/cli/templates.py
@@ -30,16 +30,21 @@ def _project_config(root: Path, env: str) -> dict:
     return load(find_config(root, env))
 
 
-def _templates_path(args: argparse.Namespace, root: Path, cfg: dict) -> str:
+def _configured_templates_path(args: argparse.Namespace, root: Path, cfg: dict) -> str:
+    """The templates path somebody chose (flag, project YAML or environment), or ""."""
     yaml_templates = _schema.get(cfg, "whatsapp.templates")
     return (
         args.templates
         or (str(root / yaml_templates) if yaml_templates else "")
         or os.environ.get("TEMPLATES_PATH")
-        or str(root / "templates.yaml")
+        or ""
     )
 
 
+def _templates_path(args: argparse.Namespace, root: Path, cfg: dict) -> str:
+    return _configured_templates_path(args, root, cfg) or str(root / "templates.yaml")
+
+
 def _prefix(args: argparse.Namespace, cfg: dict) -> str:
     return (
         args.prefix
@@ -70,8 +75,14 @@ def cmd_templates_validate(args: argparse.Namespace) -> None:
     """Execute ``socialagent templates validate``: local checks only, no AWS."""
     root = project_root()
     cfg = _project_config(root, args.env)
-    templates = _templates_path(args, root, cfg)
+    configured = _configured_templates_path(args, root, cfg)
+    templates = configured or str(root / "templates.yaml")
     if not Path(templates).is_file():
+        if not configured:
+            # A project with no templates (the minimal blueprint) has nothing
+            # to validate. A path somebody configured must still exist.
+            print("No templates to check: no templates.yaml in this project")
+            return
         raise CliError(f"templates file not found: {templates}")
     if _report(templates, _prefix(args, cfg), cfg):
         raise CliError(f"{templates} has errors that Meta would reject")
diff --git a/tests/test_cli_templates_validate_missing.py b/tests/test_cli_templates_validate_missing.py
new file mode 100644
index 0000000..1711973
--- /dev/null
+++ b/tests/test_cli_templates_validate_missing.py
@@ -0,0 +1,42 @@
+# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
+# SPDX-License-Identifier: Apache-2.0
+
+"""``socialagent templates validate`` in a project that has no templates file."""
+
+from __future__ import annotations
+
+import argparse
+
+import pytest
+
+from socialagent.cli._errors import CliError
+from socialagent.cli.templates import cmd_templates_validate
+
+
+@pytest.fixture(autouse=True)
+def _empty_project(tmp_path, monkeypatch):
+    """Run in an empty directory with no ambient templates path."""
+    monkeypatch.chdir(tmp_path)
+    monkeypatch.delenv("TEMPLATES_PATH", raising=False)
+
+
+def _args(**kwargs) -> argparse.Namespace:
+    return argparse.Namespace(**{"env": "dev", "prefix": "", "templates": "", **kwargs})
+
+
+def test_no_default_templates_file_is_nothing_to_check(capsys):
+    cmd_templates_validate(_args())
+    out = capsys.readouterr().out
+    assert "No templates to check" in out
+    assert "OK:" not in out
+
+
+def test_missing_file_from_the_flag_is_still_an_error():
+    with pytest.raises(CliError, match="templates file not found: missing.yaml"):
+        cmd_templates_validate(_args(templates="missing.yaml"))
+
+
+def test_missing_file_from_the_environment_is_still_an_error(tmp_path, monkeypatch):
+    monkeypatch.setenv("TEMPLATES_PATH", str(tmp_path / "elsewhere.yaml"))
+    with pytest.raises(CliError, match="templates file not found"):
+        cmd_templates_validate(_args())
`````

[Back to the shelf](README.md)
