# Fix 121: security-checker: the simple secret check in the pre-commit hook misses several common key formats

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(contrib): pre-commit フックの簡易パターンが github_pat_・sk-・AIza などを見ない
- Bug report: number 672 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/672))
- Project license: MIT
- Language: Bash and Python
- Test included: yes
- Patch file: [fixes/121-security-checker-672.patch](fixes/121-security-checker-672.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/121-security-checker-672.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-121-security-checker-672.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-121-security-checker-672.html

## The bug

When gitleaks is not installed the pre-commit hook falls back to a simple text search. The search only looked for four formats. Fine-grained GitHub tokens (github_pat_) and keys that start with sk- and Google keys that start with AIza were not found even though another part of the project already treats those formats as known secrets.

## The fix

contrib/host-audit/hooks/pre-commit now searches for the same formats as redact_known_patterns in the project plus github_pat_ tokens and private keys. A new file tests/unit/test_contrib_pre_commit_hook.py makes a small repository and runs the hook with gitleaks hidden: nine made-up values in secret formats stop the commit and three ordinary lines pass.

## Files changed

- contrib/host-audit/hooks/pre-commit
- tests/unit/test_contrib_pre_commit_hook.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 121-security-checker-672.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 672.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The new patterns are looser than the old ones (for example any word that starts with sk- followed by eight or more letters is stopped) so harmless text can stop a commit more often. The hook already tells the person how to skip the check. The chatbot ran a scratch copy of the pattern lines against eleven made-up values in a scratch repository. The chatbot did not run the project's hook or tests. The test builds its made-up values from two parts so the test file itself holds no text in a secret format. Fixes 71 and 79 and 82 and 83 and 84 and 85 on this shelf are for the same project and all seven patches apply one after another. Fix 136 on this shelf changes the line right above in the same file so patches 121 and 136 do not apply together: apply one and add the other change by hand.

## Search words

security-checker pre-commit hook simple pattern gitleaks missing github_pat_ sk- AIza redact_known_patterns grep

## The full patch

`````diff
diff --git a/contrib/host-audit/hooks/pre-commit b/contrib/host-audit/hooks/pre-commit
index 6234647..60aadce 100755
--- a/contrib/host-audit/hooks/pre-commit
+++ b/contrib/host-audit/hooks/pre-commit
@@ -18,8 +18,12 @@ if command -v gitleaks >/dev/null 2>&1; then
     exit 1
   fi
 else
-  # gitleaks が無い場合の簡易パターン検査
-  if git diff --cached -U0 | grep -E '^\+' | grep -qE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|xox[bp]-[0-9A-Za-z-]{20,}|-----BEGIN .*PRIVATE KEY'; then
+  # gitleaks が無い場合の簡易パターン検査。
+  # 形式は src/security_checker/context/redact.py の redact_known_patterns にそろえ、
+  # fine-grained PAT (github_pat_) と秘密鍵を加えている。
+  keys='sk-[A-Za-z0-9_-]{8,}|AIza[A-Za-z0-9_-]{10,}|gh[pousr]_[A-Za-z0-9]{16,}'
+  keys="$keys|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{12,}|xox[baprs]-[A-Za-z0-9-]{8,}"
+  if git diff --cached -U0 | grep -E '^\+' | grep -qE "(^|[^A-Za-z0-9_])($keys)|-----BEGIN .*PRIVATE KEY"; then
     echo "❌ コミットにシークレットらしき文字列が含まれています"
     echo "   誤検知なら: git commit --no-verify"
     exit 1
diff --git a/tests/unit/test_contrib_pre_commit_hook.py b/tests/unit/test_contrib_pre_commit_hook.py
new file mode 100644
index 0000000..3ccea5a
--- /dev/null
+++ b/tests/unit/test_contrib_pre_commit_hook.py
@@ -0,0 +1,79 @@
+"""contrib/host-audit/hooks/pre-commit の、gitleaks が無いときの簡易パターン検査。
+
+実際のシークレットは使わない。形式だけ合わせた偽の値をテストの中で組み立てる。
+"""
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
+HOOK = Path(__file__).resolve().parents[2] / "contrib" / "host-audit" / "hooks" / "pre-commit"
+
+pytestmark = pytest.mark.skipif(
+    not all(shutil.which(tool) for tool in ("bash", "git", "grep")),
+    reason="bash・git・grep が必要",
+)
+
+
+@pytest.fixture
+def repo(tmp_path: Path) -> tuple[Path, dict[str, str]]:
+    """空の git リポジトリと、git と grep だけが見える PATH (gitleaks は見えない)。"""
+    bin_dir = tmp_path / "bin"
+    bin_dir.mkdir()
+    for tool in ("git", "grep"):
+        found = shutil.which(tool)
+        assert found is not None
+        (bin_dir / tool).symlink_to(found)
+    work = tmp_path / "work"
+    work.mkdir()
+    env = {
+        **os.environ,
+        "PATH": str(bin_dir),
+        "HOME": str(tmp_path),
+        "GIT_CONFIG_NOSYSTEM": "1",
+    }
+    subprocess.run(["git", "init", "-q", str(work)], check=True, env=env)
+    return work, env
+
+
+def _commit_check(repo: tuple[Path, dict[str, str]], text: str) -> int:
+    work, env = repo
+    (work / "config.txt").write_text(text + "\n", encoding="utf-8")
+    subprocess.run(["git", "add", "config.txt"], cwd=work, check=True, env=env)
+    bash = shutil.which("bash")
+    assert bash is not None
+    result = subprocess.run(
+        [bash, str(HOOK)], cwd=work, env=env, capture_output=True, check=False
+    )
+    return result.returncode
+
+
+@pytest.mark.parametrize(
+    "fake_secret",
+    [
+        "github_pat_" + "A1b2C3d4E5" * 3,
+        "sk-" + "a1B2c3D4" * 4,
+        "AIza" + "Sy0123456789abcdef",
+        "ghs_" + "0123456789abcdefABCD",
+        "gho_" + "0123456789abcdefABCD",
+        "AKIA" + "IOSFODNN7EXAMPLE",
+        "ghp_" + "0123456789abcdefABCDEFGHIJ0123456789",
+        "xoxb-" + "123456789012-abcdefABCDEF",
+        "-----BEGIN RSA " + "PRIVATE KEY-----",
+    ],
+)
+def test_simple_check_stops_known_secret_formats(repo, fake_secret: str) -> None:
+    assert _commit_check(repo, f"token = {fake_secret}") == 1
+
+
+@pytest.mark.parametrize(
+    "harmless",
+    ["name = task-management-board", "color = desk-lamp", "note = see the risk-assessment-file"],
+)
+def test_simple_check_lets_ordinary_text_through(repo, harmless: str) -> None:
+    assert _commit_check(repo, harmless) == 0
`````

[Back to the shelf](README.md)
