# Fix 83: security-checker: a reviewer name with a backtick or a line break can break the layout of the pull request summary

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(github): サマリの Reviewer 名をバッククォートで直接囲み、code_span を通していない
- Bug report: number 600 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/600))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/83-security-checker-600.patch](fixes/83-security-checker-600.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/83-security-checker-600.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-83-security-checker-600.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-83-security-checker-600.html

## The bug

The summary comment wrapped each reviewer name in backticks directly. A reviewer name comes from the settings file and can hold a backtick or a line break. Such a name broke the formatting of the summary. Other parts of the summary already pass text through a safe helper.

## The fix

src/security_checker/github/comment.py now passes the reviewer names and the name of a failed scanner and the base of the compared range through the project's code_span helper. A new file tests/unit/test_github_summary_names.py checks a reviewer name with a backtick and a line break and checks the scanner name and the base.

## Files changed

- src/security_checker/github/comment.py
- tests/unit/test_github_summary_names.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 83-security-checker-600.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 600.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- code_span also hides known secret patterns and squeezes runs of spaces so a name with such content now shows differently. The chatbot confirmed the expected texts with a scratch copy of the code_span rule that leaves out the secret-hiding step. The chatbot did not run the project's tests.

## Search words

security-checker render_summary _counts_line reviewer name backtick code_span sanitize _scanner_warnings markdown injection

## The full patch

`````diff
diff --git a/src/security_checker/github/comment.py b/src/security_checker/github/comment.py
index 274992a..995a361 100644
--- a/src/security_checker/github/comment.py
+++ b/src/security_checker/github/comment.py
@@ -150,7 +150,7 @@ def _counts_line(report: Report) -> list[str]:
     ):
         if counts.get(status.value):
             lines.append(f"⚠️ {label} {counts[status.value]} 件 (「問題なし」ではありません)")
-    reviewers = ", ".join(f"`{run.name}`" for run in report.reviewers)
+    reviewers = ", ".join(md.code_span(run.name) for run in report.reviewers)
     strategy = next(
         (f.aggregation.strategy for f in report.findings if f.aggregation is not None), None
     )
@@ -160,7 +160,8 @@ def _counts_line(report: Report) -> list[str]:
         )
     if report.target.mode == "diff":
         lines.append(
-            f"範囲: `{report.target.base}` との差分 ({report.target.changed_files or 0} ファイル)"
+            f"範囲: {md.code_span(str(report.target.base))} との差分"
+            f" ({report.target.changed_files or 0} ファイル)"
         )
     return [line + "  " for line in lines[:-1]] + lines[-1:]
 
@@ -168,7 +169,7 @@ def _counts_line(report: Report) -> list[str]:
 def _scanner_warnings(report: Report) -> list[str]:
     """壊れた事実を隠さない (§7.2)."""
     return [
-        f"⚠️ `{run.scanner}` が失敗したため、この観点の検査は行われていません。"
+        f"⚠️ {md.code_span(run.scanner)} が失敗したため、この観点の検査は行われていません。"
         for run in report.scanners
         if run.status is ScanStatus.FAILED
     ]
diff --git a/tests/unit/test_github_summary_names.py b/tests/unit/test_github_summary_names.py
new file mode 100644
index 0000000..7801a22
--- /dev/null
+++ b/tests/unit/test_github_summary_names.py
@@ -0,0 +1,33 @@
+"""サマリに出す Reviewer 名・scanner 名・範囲の base は code_span を通す."""
+
+from __future__ import annotations
+
+from security_checker.github.comment import render_summary
+from security_checker.models.enums import FindingStatus, ScanStatus
+from security_checker.models.report import ReviewerRun, ScannerRun, TargetInfo
+from tests.factories import make_candidate, make_finding, make_report
+
+
+def test_reviewer_name_with_backtick_and_newline_stays_one_code_span():
+    candidate = make_candidate()
+    report = make_report(
+        [candidate],
+        [make_finding(candidate, FindingStatus.CONFIRMED)],
+        reviewers=[ReviewerRun(name="al`pha\n## injected")],
+    )
+    body = render_summary(report)
+    assert "Reviewers: `al'pha ## injected`" in body
+    assert "\n## injected" not in body
+
+
+def test_failed_scanner_name_and_diff_base_are_code_spans():
+    candidate = make_candidate()
+    report = make_report(
+        [candidate],
+        [make_finding(candidate, FindingStatus.CONFIRMED)],
+        scanners=[ScannerRun(scanner="tri`vy", category="config", status=ScanStatus.FAILED)],
+        target=TargetInfo(root="/repo", mode="diff", base="origin/ma`in", changed_files=2),
+    )
+    body = render_summary(report)
+    assert "`tri'vy` が失敗" in body
+    assert "範囲: `origin/ma'in` との差分 (2 ファイル)" in body
`````

[Back to the shelf](README.md)
