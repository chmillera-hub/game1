# Fix 149: security-checker: no test covers the question mark in exclude patterns

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(scanners): filters.py の _compile で未テストの分岐をテストする（2 行）
- Bug report: number 580 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/580))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/149-security-checker-580.patch](fixes/149-security-checker-580.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/149-security-checker-580.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-149-security-checker-580.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-149-security-checker-580.html

## The bug

_compile in src/security_checker/scanners/filters.py turns ? into exactly one character that is not a slash. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_filters_compile_question_mark.py expects src/a?.py to match src/ab.py and not src/a.py or src/abc.py and expects ? not to match a slash.

## Files changed

- tests/unit/test_filters_compile_question_mark.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 149-security-checker-580.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 580.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a scratch copy of the pattern logic on the four inputs. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker filters _compile glob question mark ? single character gitignore untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_filters_compile_question_mark.py b/tests/unit/test_filters_compile_question_mark.py
new file mode 100644
index 0000000..b4bca1d
--- /dev/null
+++ b/tests/unit/test_filters_compile_question_mark.py
@@ -0,0 +1,17 @@
+"""_compile: `?` は `/` 以外のちょうど 1 文字に一致すること."""
+
+from __future__ import annotations
+
+from security_checker.scanners.filters import _compile
+
+
+def test_question_mark_matches_exactly_one_character() -> None:
+    pattern = _compile("src/a?.py")
+
+    assert pattern.match("src/ab.py")
+    assert not pattern.match("src/a.py")
+    assert not pattern.match("src/abc.py")
+
+
+def test_question_mark_does_not_match_a_path_separator() -> None:
+    assert not _compile("src?a.py").match("src/a.py")
`````

[Back to the shelf](README.md)
