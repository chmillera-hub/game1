# Fix 146: security-checker: no test checks that _fixed_version skips the fixed version of another package

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(scanners): osv.py の _fixed_version で未テストの分岐をテストする（1 行）
- Bug report: number 585 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/585))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/146-security-checker-585.patch](fixes/146-security-checker-585.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/146-security-checker-585.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-146-security-checker-585.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-146-security-checker-585.html

## The bug

_fixed_version in src/security_checker/scanners/osv.py skips affected entries of other packages. No test ran that skip so a fixed version of the wrong package could be reported unnoticed.

## The fix

Tests only. A new file tests/unit/test_osv_fixed_version_other_package.py lists two affected packages and expects only the fixed version of the named package. A second test expects None when only another package is affected.

## Files changed

- tests/unit/test_osv_fixed_version_other_package.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 146-security-checker-585.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 585.

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

security-checker osv _fixed_version affected package name continue other package fixed version untested

## The full patch

`````diff
diff --git a/tests/unit/test_osv_fixed_version_other_package.py b/tests/unit/test_osv_fixed_version_other_package.py
new file mode 100644
index 0000000..105cb8e
--- /dev/null
+++ b/tests/unit/test_osv_fixed_version_other_package.py
@@ -0,0 +1,24 @@
+"""_fixed_version: 別のパッケージの修正版を拾わないこと."""
+
+from __future__ import annotations
+
+from typing import Any
+
+from security_checker.scanners.osv import _fixed_version
+
+
+def _affected(name: str, fixed: str) -> dict[str, Any]:
+    events = [{"introduced": "0"}, {"fixed": fixed}]
+    return {"package": {"name": name}, "ranges": [{"events": events}]}
+
+
+def test_fixed_version_of_another_package_is_skipped() -> None:
+    vulns = [{"affected": [_affected("other", "9.9.9"), _affected("target", "1.2.3")]}]
+
+    assert _fixed_version(vulns, "target") == "1.2.3"
+
+
+def test_no_fixed_version_when_only_other_packages_are_affected() -> None:
+    vulns = [{"affected": [_affected("other", "9.9.9")]}]
+
+    assert _fixed_version(vulns, "target") is None
`````

[Back to the shelf](README.md)
