# Fix 208: security-checker: no test covers shrinking a code slice that already fits

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(context): slicer.py の shrink で未テストの分岐をテストする（1 行）
- Bug report: number 498 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/498))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/208-security-checker-498.patch](fixes/208-security-checker-498.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/208-security-checker-498.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-208-security-checker-498.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-208-security-checker-498.html

## The bug

shrink in src/security_checker/context/slicer.py returns the slice unchanged when the slice already fits. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_slicer_shrink_short_slice.py expects the same object back for a slice within the limit and checks the cut of a longer slice around the focus line.

## Files changed

- tests/unit/test_slicer_shrink_short_slice.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 208-security-checker-498.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 498.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a scratch copy of the arithmetic for the longer slice. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker slicer shrink keep_lines focus_line unchanged untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_slicer_shrink_short_slice.py b/tests/unit/test_slicer_shrink_short_slice.py
new file mode 100644
index 0000000..c04e018
--- /dev/null
+++ b/tests/unit/test_slicer_shrink_short_slice.py
@@ -0,0 +1,27 @@
+"""slicer.shrink: すでに収まっている文脈はそのまま返すこと."""
+
+from __future__ import annotations
+
+from security_checker.context.slicer import shrink
+from security_checker.models.task import CodeSlice
+
+
+def _slice(lines: int, start_line: int = 10) -> CodeSlice:
+    text = "\n".join(f"line {start_line + index}" for index in range(lines))
+    end_line = start_line + lines - 1
+    return CodeSlice(path="src/a.py", start_line=start_line, end_line=end_line, text=text)
+
+
+def test_slice_within_the_limit_is_returned_unchanged() -> None:
+    slice_ = _slice(5)
+
+    assert shrink(slice_, keep_lines=5, focus_line=12) is slice_
+    assert shrink(slice_, keep_lines=9, focus_line=12) is slice_
+
+
+def test_longer_slice_is_cut_around_the_focus_line() -> None:
+    """対になるケース. 上限を超えていれば該当行を含めたまま前後を削る."""
+    shrunk = shrink(_slice(11), keep_lines=3, focus_line=15)
+
+    assert (shrunk.start_line, shrunk.end_line) == (14, 16)
+    assert shrunk.text == "line 14\nline 15\nline 16"
`````

[Back to the shelf](README.md)
