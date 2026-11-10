# Fix 166: security-checker: no test covers a version check that fails in probe_command

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(scanners): base.py の probe_command で未テストの分岐をテストする（2 行）
- Bug report: number 577 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/577))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/166-security-checker-577.patch](fixes/166-security-checker-577.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/166-security-checker-577.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-166-security-checker-577.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-166-security-checker-577.html

## The bug

probe_command in src/security_checker/scanners/base.py reports a tool as available with a reason when the version call fails. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_scanner_base_probe_command_failure.py replaces the command lookup and the process call and expects available true with the failure reason for a permission error and for a timeout. A paired test expects available false for a missing command.

## Files changed

- tests/unit/test_scanner_base_probe_command_failure.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 166-security-checker-577.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 577.

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

security-checker scanners base probe_command version OSError TimeoutExpired ToolStatus available reason untested

## The full patch

`````diff
diff --git a/tests/unit/test_scanner_base_probe_command_failure.py b/tests/unit/test_scanner_base_probe_command_failure.py
new file mode 100644
index 0000000..0d5debe
--- /dev/null
+++ b/tests/unit/test_scanner_base_probe_command_failure.py
@@ -0,0 +1,49 @@
+"""probe_command: バージョン取得に失敗しても「導入済み」として理由を返すこと."""
+
+from __future__ import annotations
+
+import subprocess
+from typing import Any
+
+import pytest
+
+from security_checker.scanners import base
+from security_checker.scanners.base import probe_command
+
+
+def _raise(exc: BaseException) -> Any:
+    def run(*_args: Any, **_kwargs: Any) -> Any:
+        raise exc
+
+    return run
+
+
+@pytest.mark.parametrize(
+    "exc",
+    [
+        PermissionError("実行できません"),
+        subprocess.TimeoutExpired(cmd="tool", timeout=15),
+    ],
+)
+def test_failed_version_call_keeps_the_tool_available(
+    monkeypatch: pytest.MonkeyPatch, exc: BaseException
+) -> None:
+    monkeypatch.setattr(base.shutil, "which", lambda _command: "/fake/bin/tool")
+    monkeypatch.setattr(base.subprocess, "run", _raise(exc))
+
+    status = probe_command("tool")
+
+    assert status.available is True
+    assert status.version is None
+    assert status.reason is not None
+    assert status.reason.startswith("バージョン取得に失敗しました")
+
+
+def test_missing_command_is_not_available(monkeypatch: pytest.MonkeyPatch) -> None:
+    """対になるケース. コマンド自体が無ければ available は False."""
+    monkeypatch.setattr(base.shutil, "which", lambda _command: None)
+
+    status = probe_command("tool")
+
+    assert status.available is False
+    assert status.reason == "tool が見つかりません"
`````

[Back to the shelf](README.md)
