# Fix 135: security-checker: the protected branches of the pre-push hook cannot be changed without editing the hook

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: feat(contrib): pre-push フックの保護ブランチを設定できるようにする
- Bug report: number 674 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/674))
- Project license: MIT
- Language: Bash and Python
- Test included: yes
- Patch file: [fixes/135-security-checker-674.patch](fixes/135-security-checker-674.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/135-security-checker-674.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-135-security-checker-674.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-135-security-checker-674.html

## The bug

contrib/host-audit/hooks/pre-push had the protected branches fixed to main and master. A repository that wants to protect develop or release branches had to edit the hook and a reinstall of the hooks overwrote the edit.

## The fix

The hook now reads the pattern from the environment variable SECURITY_CHECKER_PROTECTED_BRANCHES first and then from git config security-checker.protectedBranches and falls back to the old default. A new file tests/unit/test_contrib_pre_push_hook.py checks the default and the git config value and the environment variable.

## Files changed

- contrib/host-audit/hooks/pre-push
- tests/unit/test_contrib_pre_push_hook.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 135-security-checker-674.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 674.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The environment variable name is the chatbot's choice: the bug report only says git config or an environment variable. The pattern is matched against the full ref name (refs/heads/...). The chatbot ran a scratch copy of the new lines in a scratch repository for all three cases. The chatbot did not run the project's hook or tests.

## Search words

security-checker pre-push hook PROTECTED branches git config security-checker.protectedBranches develop release environment variable

## The full patch

`````diff
diff --git a/contrib/host-audit/hooks/pre-push b/contrib/host-audit/hooks/pre-push
index 869566e..66bed7e 100755
--- a/contrib/host-audit/hooks/pre-push
+++ b/contrib/host-audit/hooks/pre-push
@@ -9,7 +9,18 @@
 # 導入: contrib/host-audit/install_hooks.sh   /   一時的に外す: git push --no-verify
 set -uo pipefail
 
-PROTECTED='^refs/heads/(main|master)$'
+# 保護ブランチの正規表現 (refs/heads/... 全体に対して照合する)。上書きの優先順:
+#   1. 環境変数 SECURITY_CHECKER_PROTECTED_BRANCHES
+#   2. git config security-checker.protectedBranches
+#      例: git config security-checker.protectedBranches '^refs/heads/(main|develop|release/.*)$'
+#   3. 既定値 (main / master)
+PROTECTED="${SECURITY_CHECKER_PROTECTED_BRANCHES:-}"
+if [[ -z "$PROTECTED" ]]; then
+  PROTECTED="$(git config --get security-checker.protectedBranches 2>/dev/null || true)"
+fi
+if [[ -z "$PROTECTED" ]]; then
+  PROTECTED='^refs/heads/(main|master)$'
+fi
 ALL_ZERO='^0+$' # 全ゼロ = ブランチの新規作成 or 削除 (sha1/sha256 どちらでも成立)
 
 status=0
diff --git a/tests/unit/test_contrib_pre_push_hook.py b/tests/unit/test_contrib_pre_push_hook.py
new file mode 100644
index 0000000..fffc587
--- /dev/null
+++ b/tests/unit/test_contrib_pre_push_hook.py
@@ -0,0 +1,74 @@
+"""contrib/host-audit/hooks/pre-push の保護ブランチを設定で上書きできること."""
+
+from __future__ import annotations
+
+import os
+import shutil
+import subprocess
+from pathlib import Path
+
+import pytest
+
+HOOK = Path(__file__).resolve().parents[2] / "contrib" / "host-audit" / "hooks" / "pre-push"
+ZERO = "0" * 40
+
+pytestmark = pytest.mark.skipif(
+    shutil.which("bash") is None or shutil.which("git") is None,
+    reason="bash と git が必要",
+)
+
+
+def _repo(tmp_path: Path) -> Path:
+    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
+    return tmp_path
+
+
+def _push(repo: Path, branch: str, env: dict[str, str] | None = None) -> int:
+    """新しいブランチを作る push をフックに渡し、終了コードを返す."""
+    line = f"refs/heads/{branch} {'1' * 40} refs/heads/{branch} {ZERO}\n"
+    merged = {k: v for k, v in os.environ.items() if k != "SECURITY_CHECKER_PROTECTED_BRANCHES"}
+    merged.update(env or {})
+    done = subprocess.run(
+        ["bash", str(HOOK)],
+        cwd=repo,
+        input=line,
+        text=True,
+        capture_output=True,
+        env=merged,
+        check=False,
+    )
+    return done.returncode
+
+
+def test_default_protects_main_only(tmp_path: Path) -> None:
+    repo = _repo(tmp_path)
+
+    assert _push(repo, "main") == 1
+    assert _push(repo, "develop") == 0
+
+
+def test_git_config_overrides_the_protected_branches(tmp_path: Path) -> None:
+    repo = _repo(tmp_path)
+    pattern = "^refs/heads/(develop|release/.*)$"
+    subprocess.run(
+        ["git", "config", "security-checker.protectedBranches", pattern],
+        cwd=repo,
+        check=True,
+    )
+
+    assert _push(repo, "develop") == 1
+    assert _push(repo, "release/1.2") == 1
+    assert _push(repo, "feature") == 0
+
+
+def test_environment_variable_wins_over_git_config(tmp_path: Path) -> None:
+    repo = _repo(tmp_path)
+    subprocess.run(
+        ["git", "config", "security-checker.protectedBranches", "^refs/heads/develop$"],
+        cwd=repo,
+        check=True,
+    )
+    env = {"SECURITY_CHECKER_PROTECTED_BRANCHES": "^refs/heads/feature$"}
+
+    assert _push(repo, "feature", env) == 1
+    assert _push(repo, "develop", env) == 0
`````

[Back to the shelf](README.md)
