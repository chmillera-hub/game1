# Fix 210: security-checker: no test covers a read error in the text file reader

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(context): slicer.py の read_text_file で未テストの分岐をテストする（2 行）
- Bug report: number 496 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/496))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/210-security-checker-496.patch](fixes/210-security-checker-496.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/210-security-checker-496.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-210-security-checker-496.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-210-security-checker-496.html

## The bug

read_text_file in src/security_checker/context/slicer.py returns None when reading raises an OS error. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_slicer_read_text_file_os_error.py makes the read raise a permission error and expects None and checks a folder and a readable file.

## Files changed

- tests/unit/test_slicer_read_text_file_os_error.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 210-security-checker-496.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 496.

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

security-checker slicer read_text_file OSError PermissionError None untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_slicer_read_text_file_os_error.py b/tests/unit/test_slicer_read_text_file_os_error.py
new file mode 100644
index 0000000..afd68a5
--- /dev/null
+++ b/tests/unit/test_slicer_read_text_file_os_error.py
@@ -0,0 +1,33 @@
+"""slicer.read_text_file: 読み込みで OSError が出たら None を返すこと."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker.context.slicer import read_text_file
+
+
+def test_os_error_while_reading_gives_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
+    path = tmp_path / "a.py"
+    path.write_text("a = 1\n", encoding="utf-8")
+
+    def refuse(_self: Path) -> bytes:
+        raise PermissionError("読めません")
+
+    monkeypatch.setattr(Path, "read_bytes", refuse)
+
+    assert read_text_file(path) is None
+
+
+def test_directory_gives_none(tmp_path: Path) -> None:
+    assert read_text_file(tmp_path) is None
+
+
+def test_readable_text_file_gives_its_lines(tmp_path: Path) -> None:
+    """対になるケース. 読めるテキストは行のリストになる."""
+    path = tmp_path / "a.py"
+    path.write_text("a = 1\nb = 2\n", encoding="utf-8")
+
+    assert read_text_file(path) == ["a = 1", "b = 2"]
`````

[Back to the shelf](README.md)
