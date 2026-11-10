# Fix 211: security-checker: no test covers a path that cannot be resolved in resolve_inside

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(context): slicer.py の resolve_inside で未テストの分岐をテストする（2 行）
- Bug report: number 495 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/495))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/211-security-checker-495.patch](fixes/211-security-checker-495.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/211-security-checker-495.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-211-security-checker-495.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-211-security-checker-495.html

## The bug

resolve_inside in src/security_checker/context/slicer.py returns None when resolving the path raises an error. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_slicer_resolve_inside_errors.py makes the resolve step raise an OS error and a RuntimeError and expects None and checks a path that leaves the root and a path inside the root.

## Files changed

- tests/unit/test_slicer_resolve_inside_errors.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 211-security-checker-495.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 495.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A scratch script confirmed the two path facts the paired tests rely on. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker slicer resolve_inside OSError RuntimeError symlink loop outside root None untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_slicer_resolve_inside_errors.py b/tests/unit/test_slicer_resolve_inside_errors.py
new file mode 100644
index 0000000..84df6fc
--- /dev/null
+++ b/tests/unit/test_slicer_resolve_inside_errors.py
@@ -0,0 +1,33 @@
+"""slicer.resolve_inside: 解決に失敗したパスと、root の外を指すパスは None にすること."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from security_checker.context.slicer import resolve_inside
+
+
+@pytest.mark.parametrize("exc", [OSError("壊れたリンク"), RuntimeError("リンクの循環")])
+def test_failed_resolution_gives_none(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exc: Exception
+) -> None:
+    def fail(_self: Path, strict: bool = False) -> Path:
+        raise exc
+
+    monkeypatch.setattr(Path, "resolve", fail)
+
+    assert resolve_inside(tmp_path, "src/a.py") is None
+
+
+def test_path_that_leaves_the_root_gives_none(tmp_path: Path) -> None:
+    root = tmp_path / "repo"
+    root.mkdir()
+
+    assert resolve_inside(root, "../outside.py") is None
+
+
+def test_path_inside_the_root_is_resolved(tmp_path: Path) -> None:
+    """対になるケース. 配下のパスは解決して返す."""
+    assert resolve_inside(tmp_path, "src/../a.py") == tmp_path.resolve() / "a.py"
`````

[Back to the shelf](README.md)
