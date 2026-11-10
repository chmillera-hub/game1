# Fix 205: security-checker: no test covers the place text of a candidate that has no file location

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(models): candidate.py の where で未テストの分岐をテストする（3 行）
- Bug report: number 518 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/518))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/205-security-checker-518.patch](fixes/205-security-checker-518.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/205-security-checker-518.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-205-security-checker-518.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-205-security-checker-518.html

## The bug

Candidate.where in src/security_checker/models/candidate.py shows the package key for a dependency finding and a dash when neither a location nor a package exists. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_candidate_where.py checks a package with a version and a package without a version and a candidate with neither and a candidate with a location.

## Files changed

- tests/unit/test_candidate_where.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 205-security-checker-518.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 518.

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

security-checker candidate where package as_key location None dash untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_candidate_where.py b/tests/unit/test_candidate_where.py
new file mode 100644
index 0000000..25d7a31
--- /dev/null
+++ b/tests/unit/test_candidate_where.py
@@ -0,0 +1,36 @@
+"""Candidate.where: 位置が無い候補の人間向けの表記."""
+
+from __future__ import annotations
+
+from security_checker.models.candidate import PackageRef
+from security_checker.models.enums import Category
+from tests.factories import make_candidate
+
+
+def test_where_of_a_dependency_candidate_is_the_package_key() -> None:
+    candidate = make_candidate(
+        location=None,
+        category=Category.DEPENDENCY,
+        package=PackageRef(ecosystem="PyPI", name="requests", version="2.31.0"),
+    )
+
+    assert candidate.where == "PyPI:requests@2.31.0"
+
+
+def test_where_of_a_package_without_a_version_uses_a_star() -> None:
+    candidate = make_candidate(
+        location=None,
+        category=Category.DEPENDENCY,
+        package=PackageRef(ecosystem="npm", name="left-pad"),
+    )
+
+    assert candidate.where == "npm:left-pad@*"
+
+
+def test_where_without_location_or_package_is_a_dash() -> None:
+    assert make_candidate(location=None).where == "-"
+
+
+def test_where_prefers_the_location() -> None:
+    """対になるケース. 位置があればパスと行を示す."""
+    assert make_candidate(path="src/a.py", line=7).where == "src/a.py:7"
`````

[Back to the shelf](README.md)
