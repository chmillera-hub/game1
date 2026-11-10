# Fix 246: security-checker: no test covers a missing or failing git in the diff helper

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): pr.py の _git で未テストの分岐をテストする（4 行）
- Bug report: number 516 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/516))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/246-security-checker-516.patch](fixes/246-security-checker-516.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/246-security-checker-516.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-246-security-checker-516.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-246-security-checker-516.html

## The bug

_git in src/security_checker/github/pr.py raises DiffError when git is missing or does not finish in time. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_pr_git_failures.py replaces the process call and checks a missing git and a timeout and a failed command with its last error line and a successful call.

## Files changed

- tests/unit/test_pr_git_failures.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 246-security-checker-516.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 516.

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

security-checker github pr _git FileNotFoundError TimeoutExpired DiffError stderr untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_pr_git_failures.py b/tests/unit/test_pr_git_failures.py
new file mode 100644
index 0000000..4d3d620
--- /dev/null
+++ b/tests/unit/test_pr_git_failures.py
@@ -0,0 +1,59 @@
+"""pr._git: git が無い・終わらない・失敗したときは DiffError になること."""
+
+from __future__ import annotations
+
+import subprocess
+from pathlib import Path
+from typing import Any
+
+import pytest
+
+from security_checker.github import pr
+from security_checker.github.pr import DiffError, _git
+
+
+def _raise(exc: BaseException) -> Any:
+    def run(*_args: Any, **_kwargs: Any) -> Any:
+        raise exc
+
+    return run
+
+
+def test_missing_git_is_a_diff_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
+    monkeypatch.setattr(pr.subprocess, "run", _raise(FileNotFoundError("git")))
+
+    with pytest.raises(DiffError, match="git が見つかりません"):
+        _git(tmp_path, "diff")
+
+
+def test_git_that_does_not_finish_is_a_diff_error(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
+) -> None:
+    timeout = subprocess.TimeoutExpired(cmd="git", timeout=pr.GIT_TIMEOUT_S)
+    monkeypatch.setattr(pr.subprocess, "run", _raise(timeout))
+
+    with pytest.raises(DiffError, match="git diff が .* 秒以内に終わりませんでした"):
+        _git(tmp_path, "diff")
+
+
+def test_failed_git_reports_the_last_line_of_stderr(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
+) -> None:
+    def run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
+        return subprocess.CompletedProcess(argv, 128, "", "hint: x\nfatal: bad revision\n")
+
+    monkeypatch.setattr(pr.subprocess, "run", run)
+
+    with pytest.raises(DiffError, match="git diff main が失敗しました: fatal: bad revision"):
+        _git(tmp_path, "diff", "main")
+
+
+def test_successful_git_returns_stdout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
+    """対になるケース. 成功すれば標準出力をそのまま返す."""
+
+    def run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
+        return subprocess.CompletedProcess(argv, 0, "ok\n", "")
+
+    monkeypatch.setattr(pr.subprocess, "run", run)
+
+    assert _git(tmp_path, "status") == "ok\n"
`````

[Back to the shelf](README.md)
