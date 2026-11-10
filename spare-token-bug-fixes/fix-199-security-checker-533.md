# Fix 199: security-checker: no test covers a version check that fails in command_version

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): detect.py の command_version で未テストの分岐をテストする（2 行）
- Bug report: number 533 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/533))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/199-security-checker-533.patch](fixes/199-security-checker-533.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/199-security-checker-533.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-199-security-checker-533.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-199-security-checker-533.html

## The bug

command_version in src/security_checker/providers/detect.py reports a command as available with a reason when the version call fails. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_detect_command_version_failure.py replaces the command lookup and the process call and checks a permission error and a timeout and a missing command.

## Files changed

- tests/unit/test_detect_command_version_failure.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 199-security-checker-533.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 533.

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

security-checker detect command_version OSError TimeoutExpired CommandStatus available reason untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_detect_command_version_failure.py b/tests/unit/test_detect_command_version_failure.py
new file mode 100644
index 0000000..569e0c9
--- /dev/null
+++ b/tests/unit/test_detect_command_version_failure.py
@@ -0,0 +1,49 @@
+"""detect.command_version: バージョン取得に失敗しても「導入済み」として理由を返すこと."""
+
+from __future__ import annotations
+
+import subprocess
+from typing import Any
+
+import pytest
+
+from security_checker.providers import detect
+from security_checker.providers.detect import command_version
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
+        subprocess.TimeoutExpired(cmd="tool", timeout=10),
+    ],
+)
+def test_failed_version_call_keeps_the_command_available(
+    monkeypatch: pytest.MonkeyPatch, exc: BaseException
+) -> None:
+    monkeypatch.setattr(detect.shutil, "which", lambda _command: "/fake/bin/tool")
+    monkeypatch.setattr(detect.subprocess, "run", _raise(exc))
+
+    status = command_version("tool")
+
+    assert status.available is True
+    assert status.version is None
+    assert status.reason is not None
+    assert status.reason.startswith("バージョン取得に失敗しました")
+
+
+def test_missing_command_is_not_available(monkeypatch: pytest.MonkeyPatch) -> None:
+    """対になるケース. コマンド自体が無ければ available は False."""
+    monkeypatch.setattr(detect.shutil, "which", lambda _command: None)
+
+    status = command_version("tool")
+
+    assert status.available is False
+    assert status.reason == "tool が見つかりません"
`````

[Back to the shelf](README.md)
