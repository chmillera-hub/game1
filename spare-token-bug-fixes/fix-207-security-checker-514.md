# Fix 207: security-checker: no test covers a code finding without a location in the diff check

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): pr.py の touches で未テストの分岐をテストする（1 行）
- Bug report: number 514 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/514))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/207-security-checker-514.patch](fixes/207-security-checker-514.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/207-security-checker-514.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-207-security-checker-514.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-207-security-checker-514.html

## The bug

DiffScope.touches in src/security_checker/github/pr.py returns False for a code or secret finding that has no location. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_pr_touches_without_location.py checks both categories without a location and checks three line numbers against an added range.

## Files changed

- tests/unit/test_pr_touches_without_location.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 207-security-checker-514.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 514.

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

security-checker github pr DiffScope touches location None SAST SECRET added lines untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_pr_touches_without_location.py b/tests/unit/test_pr_touches_without_location.py
new file mode 100644
index 0000000..f17aa14
--- /dev/null
+++ b/tests/unit/test_pr_touches_without_location.py
@@ -0,0 +1,28 @@
+"""DiffScope.touches: 位置を持たない SAST / シークレットの候補は変更に関係しないと扱うこと."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.github.pr import DiffScope
+from security_checker.models.enums import Category
+from tests.factories import make_candidate
+
+SCOPE = DiffScope(
+    base="main",
+    added={"src/app.py": ((40, 45),)},
+    changed_files=frozenset({"src/app.py"}),
+)
+
+
+@pytest.mark.parametrize("category", [Category.SAST, Category.SECRET])
+def test_candidate_without_a_location_does_not_touch_the_diff(category: Category) -> None:
+    candidate = make_candidate(location=None, category=category)
+
+    assert SCOPE.touches(candidate) is False
+
+
+@pytest.mark.parametrize(("line", "expected"), [(42, True), (45, True), (46, False)])
+def test_candidate_with_a_location_touches_only_added_lines(line: int, expected: bool) -> None:
+    """対になるケース. 位置があれば、追加された行範囲との重なりで決まる."""
+    assert SCOPE.touches(make_candidate(path="src/app.py", line=line)) is expected
`````

[Back to the shelf](README.md)
