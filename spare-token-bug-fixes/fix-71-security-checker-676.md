# Fix 71: security-checker: run_all.sh stops with an unbound variable error when --domain has no value

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(contrib): run_all.sh で --domain に値を付け忘れると unbound variable で落ちる
- Bug report: number 676 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/676))
- Project license: MIT
- Language: Bash
- Test included: yes
- Patch file: [fixes/71-security-checker-676.patch](fixes/71-security-checker-676.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/71-security-checker-676.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-71-security-checker-676.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-71-security-checker-676.html

## The bug

Running contrib/host-audit/run_all.sh with --domain as the last argument ended with the shell message $2: unbound variable. The message did not tell the person which argument was wrong.

## The fix

contrib/host-audit/run_all.sh now checks that a value follows --domain. With no value the script prints a short message and the usage line to standard error and exits with code 2. A new file tests/unit/test_contrib_run_all.py runs the script with --domain alone and checks for exit code 2 and the usage text.

## Files changed

- contrib/host-audit/run_all.sh
- tests/unit/test_contrib_run_all.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 71-security-checker-676.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 676.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The messages are in Japanese to match the script. The check only catches a missing value at the end of the arguments. A following option such as --domain --other is still taken as the value. The chatbot ran a scratch copy of the argument loop and ran bash -n (a syntax check) on the changed script. The chatbot did not run the project's script or tests. The project builds CHANGELOG.md with release-please so the patch adds no changelog line.

## Search words

security-checker run_all.sh --domain unbound variable set -u host-audit usage exit 2

## The full patch

`````diff
diff --git a/contrib/host-audit/run_all.sh b/contrib/host-audit/run_all.sh
index 417262b..5983a8f 100755
--- a/contrib/host-audit/run_all.sh
+++ b/contrib/host-audit/run_all.sh
@@ -8,7 +8,13 @@ PROJECT=""
 DOMAIN=""
 while [[ $# -gt 0 ]]; do
   case "$1" in
-    --domain) DOMAIN="$2"; shift 2 ;;
+    --domain)
+      if [[ $# -lt 2 ]]; then
+        echo "--domain には値が必要です" >&2
+        echo "使い方: ./run_all.sh [検査対象プロジェクトのパス] [--domain example.com]" >&2
+        exit 2
+      fi
+      DOMAIN="$2"; shift 2 ;;
     *) PROJECT="$1"; shift ;;
   esac
 done
diff --git a/tests/unit/test_contrib_run_all.py b/tests/unit/test_contrib_run_all.py
new file mode 100644
index 0000000..2f0ac19
--- /dev/null
+++ b/tests/unit/test_contrib_run_all.py
@@ -0,0 +1,27 @@
+"""contrib/host-audit/run_all.sh の引数解析。"""
+
+from __future__ import annotations
+
+import shutil
+import subprocess
+from pathlib import Path
+
+import pytest
+
+RUN_ALL = Path(__file__).resolve().parents[2] / "contrib" / "host-audit" / "run_all.sh"
+
+
+@pytest.mark.skipif(shutil.which("bash") is None, reason="bash が必要")
+def test_domain_without_value_prints_usage_and_exits_2() -> None:
+    """--domain に値が無いとき、unbound variable ではなく使い方を出して exit 2 にする。"""
+    result = subprocess.run(
+        ["bash", str(RUN_ALL), "--domain"],
+        capture_output=True,
+        text=True,
+        timeout=30,
+        check=False,
+    )
+
+    assert result.returncode == 2
+    assert "使い方" in result.stderr
+    assert "unbound variable" not in result.stderr
`````

[Back to the shelf](README.md)
