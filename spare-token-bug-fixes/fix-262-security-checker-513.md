# Fix 262: security-checker: no test covers inline comment planning when inline comments are turned off

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): comment.py の plan_inline で未テストの分岐をテストする（1 行）
- Bug report: number 513 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/513))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/262-security-checker-513.patch](fixes/262-security-checker-513.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/262-security-checker-513.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-262-security-checker-513.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-262-security-checker-513.html

## The bug

plan_inline in src/security_checker/github/comment.py returns an empty plan when inline comments are turned off. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_comment_plan_inline_disabled.py checks the setting turned off and a minimum status that is never posted inline and the normal case with one confirmed finding on a changed line.

## Files changed

- tests/unit/test_comment_plan_inline_disabled.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 262-security-checker-513.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 513.

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

security-checker github comment plan_inline inline_comments False inline_min_status empty plan untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_comment_plan_inline_disabled.py b/tests/unit/test_comment_plan_inline_disabled.py
new file mode 100644
index 0000000..085b864
--- /dev/null
+++ b/tests/unit/test_comment_plan_inline_disabled.py
@@ -0,0 +1,37 @@
+"""plan_inline: inline コメントが無効なら何も計画しないこと."""
+
+from __future__ import annotations
+
+from security_checker.config.schema import GithubConfig
+from security_checker.github.comment import plan_inline
+from security_checker.models.enums import FindingStatus
+from security_checker.models.report import Report
+from tests.factories import make_candidate, make_finding, make_report
+
+
+def _report() -> Report:
+    candidate = make_candidate(path="src/app.py", line=42)
+    return make_report([candidate], [make_finding(candidate, FindingStatus.CONFIRMED)])
+
+
+COMMENTABLE = {"src/app.py": [(40, 45)]}
+
+
+def test_disabled_inline_comments_plan_nothing() -> None:
+    plan = plan_inline(_report(), GithubConfig(inline_comments=False), COMMENTABLE, set())
+
+    assert plan.comments == []
+    assert (plan.already_posted, plan.outside_diff, plan.over_limit) == (0, 0, 0)
+
+
+def test_min_status_that_is_never_posted_inline_plans_nothing() -> None:
+    settings = GithubConfig(inline_min_status=FindingStatus.FALSE_POSITIVE)
+
+    assert plan_inline(_report(), settings, COMMENTABLE, set()).comments == []
+
+
+def test_enabled_inline_comments_plan_the_confirmed_finding() -> None:
+    """対になるケース. 有効なら、変更行にある confirmed の検出を 1 件計画する."""
+    plan = plan_inline(_report(), GithubConfig(), COMMENTABLE, set())
+
+    assert [(c.path, c.line, c.finding_id) for c in plan.comments] == [("src/app.py", 42, "c1")]
`````

[Back to the shelf](README.md)
