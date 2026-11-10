# Fix 209: security-checker: no test covers the cases where no code window can be read

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(context): slicer.py の line_window で未テストの分岐をテストする（2 行）
- Bug report: number 497 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/497))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/209-security-checker-497.patch](fixes/209-security-checker-497.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/209-security-checker-497.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-209-security-checker-497.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-209-security-checker-497.html

## The bug

line_window in src/security_checker/context/slicer.py returns None when the file cannot be read as text or is empty. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_slicer_line_window_none.py checks a binary file and a missing file and an empty file and a line far past the end and a readable line.

## Files changed

- tests/unit/test_slicer_line_window_none.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 209-security-checker-497.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 497.

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

security-checker slicer line_window None binary empty file missing untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_slicer_line_window_none.py b/tests/unit/test_slicer_line_window_none.py
new file mode 100644
index 0000000..136272a
--- /dev/null
+++ b/tests/unit/test_slicer_line_window_none.py
@@ -0,0 +1,44 @@
+"""slicer.line_window: 読めない・空・範囲外のときは None を返すこと."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+from security_checker.context.slicer import line_window
+from security_checker.models.candidate import Location
+
+
+def _location(path: str, line: int = 1) -> Location:
+    return Location(path=path, start_line=line, end_line=line)
+
+
+def test_binary_file_gives_no_window(tmp_path: Path) -> None:
+    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\x02")
+
+    assert line_window(tmp_path, _location("blob.bin"), window_lines=3) is None
+
+
+def test_missing_file_gives_no_window(tmp_path: Path) -> None:
+    assert line_window(tmp_path, _location("absent.py"), window_lines=3) is None
+
+
+def test_empty_file_gives_no_window(tmp_path: Path) -> None:
+    (tmp_path / "empty.py").write_text("", encoding="utf-8")
+
+    assert line_window(tmp_path, _location("empty.py"), window_lines=3) is None
+
+
+def test_line_far_past_the_end_gives_no_window(tmp_path: Path) -> None:
+    (tmp_path / "short.py").write_text("a = 1\nb = 2\n", encoding="utf-8")
+
+    assert line_window(tmp_path, _location("short.py", line=50), window_lines=3) is None
+
+
+def test_line_inside_the_file_gives_its_window(tmp_path: Path) -> None:
+    """対になるケース. 読める行なら前後を含めて切り出す."""
+    (tmp_path / "short.py").write_text("a = 1\nb = 2\nc = 3\n", encoding="utf-8")
+
+    window = line_window(tmp_path, _location("short.py", line=2), window_lines=1)
+
+    assert window is not None
+    assert (window.start_line, window.end_line, window.text) == (1, 3, "a = 1\nb = 2\nc = 3")
`````

[Back to the shelf](README.md)
