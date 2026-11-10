# Fix 245: security-checker: no test covers an event file that cannot be read in context_from_env

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): client.py の context_from_env で未テストの分岐をテストする（2 行）
- Bug report: number 505 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/505))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/245-security-checker-505.patch](fixes/245-security-checker-505.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/245-security-checker-505.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-245-security-checker-505.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-245-security-checker-505.html

## The bug

context_from_env in src/security_checker/github/client.py ignores a GitHub event file that cannot be read as JSON. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_github_context_from_env_event_file.py writes a broken event file and expects the arguments to be used and expects a ConfigError when no number is given. A paired test reads a valid event file.

## Files changed

- tests/unit/test_github_context_from_env_event_file.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 245-security-checker-505.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 505.

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

security-checker github client context_from_env GITHUB_EVENT_PATH broken JSON event pull_request untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_github_context_from_env_event_file.py b/tests/unit/test_github_context_from_env_event_file.py
new file mode 100644
index 0000000..25ea838
--- /dev/null
+++ b/tests/unit/test_github_context_from_env_event_file.py
@@ -0,0 +1,42 @@
+"""context_from_env: 読めないイベントペイロードは無視し、引数と環境変数で PR を特定すること."""
+
+from __future__ import annotations
+
+import json
+from pathlib import Path
+
+import pytest
+
+from security_checker.errors import ConfigError
+from security_checker.github.client import context_from_env
+
+
+def test_broken_event_file_falls_back_to_the_arguments(tmp_path: Path) -> None:
+    event = tmp_path / "event.json"
+    event.write_text("{not json", encoding="utf-8")
+    environ = {"GITHUB_EVENT_PATH": str(event), "GITHUB_REPOSITORY": "owner/repo"}
+
+    context = context_from_env(environ, number=7, head_sha="abc123")
+
+    assert (context.repository, context.number, context.head_sha) == ("owner/repo", 7, "abc123")
+
+
+def test_broken_event_file_without_a_number_is_a_config_error(tmp_path: Path) -> None:
+    event = tmp_path / "event.json"
+    event.write_text("{not json", encoding="utf-8")
+    environ = {"GITHUB_EVENT_PATH": str(event), "GITHUB_REPOSITORY": "owner/repo"}
+
+    with pytest.raises(ConfigError, match="コメント先の PR を特定できません"):
+        context_from_env(environ)
+
+
+def test_readable_event_file_supplies_the_number_and_the_head(tmp_path: Path) -> None:
+    """対になるケース. 読めるペイロードからは番号と head の sha を取る."""
+    event = tmp_path / "event.json"
+    payload = {"pull_request": {"number": 12, "head": {"sha": "def456"}}}
+    event.write_text(json.dumps(payload), encoding="utf-8")
+    environ = {"GITHUB_EVENT_PATH": str(event), "GITHUB_REPOSITORY": "owner/repo"}
+
+    context = context_from_env(environ)
+
+    assert (context.repository, context.number, context.head_sha) == ("owner/repo", 12, "def456")
`````

[Back to the shelf](README.md)
