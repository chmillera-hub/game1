# Fix 167: security-checker: no test covers a missing or failing gitleaks in the dir subcommand check

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(scanners): gitleaks.py の _supports_dir_subcommand で未テストの分岐をテストする（3 行）
- Bug report: number 581 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/581))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/167-security-checker-581.patch](fixes/167-security-checker-581.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/167-security-checker-581.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-167-security-checker-581.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-167-security-checker-581.html

## The bug

GitleaksScanner._supports_dir_subcommand in src/security_checker/scanners/gitleaks.py returns False when gitleaks is missing or the help call fails. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_gitleaks_supports_dir_subcommand.py replaces the command lookup and the process call and checks a missing gitleaks and a permission error and a timeout and both exit codes of the help call.

## Files changed

- tests/unit/test_gitleaks_supports_dir_subcommand.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 167-security-checker-581.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 581.

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

security-checker gitleaks _supports_dir_subcommand shutil.which subprocess OSError dir detect untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_gitleaks_supports_dir_subcommand.py b/tests/unit/test_gitleaks_supports_dir_subcommand.py
new file mode 100644
index 0000000..5a4944e
--- /dev/null
+++ b/tests/unit/test_gitleaks_supports_dir_subcommand.py
@@ -0,0 +1,58 @@
+"""GitleaksScanner._supports_dir_subcommand: gitleaks が無い・呼べないときは旧形式を使うこと."""
+
+from __future__ import annotations
+
+import subprocess
+from typing import Any
+
+import pytest
+
+from security_checker.scanners import gitleaks
+from security_checker.scanners.gitleaks import GitleaksScanner
+
+
+def _completed(returncode: int) -> Any:
+    def run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
+        return subprocess.CompletedProcess(argv, returncode, b"", b"")
+
+    return run
+
+
+def _raise(exc: BaseException) -> Any:
+    def run(*_args: Any, **_kwargs: Any) -> Any:
+        raise exc
+
+    return run
+
+
+def test_missing_gitleaks_does_not_support_dir(monkeypatch: pytest.MonkeyPatch) -> None:
+    monkeypatch.setattr(gitleaks.shutil, "which", lambda _command: None)
+
+    assert GitleaksScanner._supports_dir_subcommand() is False
+
+
+@pytest.mark.parametrize(
+    "exc",
+    [
+        PermissionError("実行できません"),
+        subprocess.TimeoutExpired(cmd="gitleaks", timeout=15),
+    ],
+)
+def test_failed_help_call_does_not_support_dir(
+    monkeypatch: pytest.MonkeyPatch, exc: BaseException
+) -> None:
+    monkeypatch.setattr(gitleaks.shutil, "which", lambda _command: "/fake/bin/gitleaks")
+    monkeypatch.setattr(gitleaks.subprocess, "run", _raise(exc))
+
+    assert GitleaksScanner._supports_dir_subcommand() is False
+
+
+@pytest.mark.parametrize(("returncode", "expected"), [(0, True), (1, False)])
+def test_exit_code_of_the_help_call_decides(
+    monkeypatch: pytest.MonkeyPatch, returncode: int, expected: bool
+) -> None:
+    """対になるケース. `gitleaks dir --help` が 0 で終われば dir を使う."""
+    monkeypatch.setattr(gitleaks.shutil, "which", lambda _command: "/fake/bin/gitleaks")
+    monkeypatch.setattr(gitleaks.subprocess, "run", _completed(returncode))
+
+    assert GitleaksScanner._supports_dir_subcommand() is expected
`````

[Back to the shelf](README.md)
