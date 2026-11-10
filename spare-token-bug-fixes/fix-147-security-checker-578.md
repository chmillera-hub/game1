# Fix 147: security-checker: no test covers a blank stderr in the excerpt helper

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(scanners): base.py の excerpt で未テストの分岐をテストする（1 行）
- Bug report: number 578 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/578))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/147-security-checker-578.patch](fixes/147-security-checker-578.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/147-security-checker-578.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-147-security-checker-578.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-147-security-checker-578.html

## The bug

excerpt in src/security_checker/scanners/base.py returns None when the stderr bytes hold only blank characters. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_scanner_base_excerpt_blank.py expects None for empty bytes and for blank-only bytes and expects the trimmed text for a value with blank lines around.

## Files changed

- tests/unit/test_scanner_base_excerpt_blank.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 147-security-checker-578.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 578.

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

security-checker scanners base excerpt stderr blank whitespace None untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_scanner_base_excerpt_blank.py b/tests/unit/test_scanner_base_excerpt_blank.py
new file mode 100644
index 0000000..041f415
--- /dev/null
+++ b/tests/unit/test_scanner_base_excerpt_blank.py
@@ -0,0 +1,16 @@
+"""excerpt: 中身が空白だけの stderr は None になること."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.scanners.base import excerpt
+
+
+@pytest.mark.parametrize("data", [b"", b"   \n\t\n"])
+def test_empty_or_blank_stderr_gives_none(data: bytes) -> None:
+    assert excerpt(data) is None
+
+
+def test_surrounding_blank_lines_are_stripped() -> None:
+    assert excerpt(b"\n  boom  \n") == "boom"
`````

[Back to the shelf](README.md)
