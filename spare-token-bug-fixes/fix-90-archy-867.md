# Fix 90: Archy: no test covers the 40-character limit on registry literal names

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: test(conventions): the 40-character slug cap on registry literal names has no test
- Bug report: number 867 ([open the bug report](https://github.com/hslee16/Archy/issues/867))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/90-archy-867.patch](fixes/90-archy-867.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/90-archy-867.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-90-archy-867.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-90-archy-867.html

## The bug

archy conventions only collects the first text argument of a registry entry as a copyable name when the text is short and has no spaces. No test covered the length limit: changing the limit from 40 to 400 left every test passing.

## The fix

A new file tests/test_conventions_slug_cap.py builds a registry with one name of 40 characters and one name of 41 characters and one short name and checks that only the 40-character name and the short name are reported.

## Files changed

- tests/test_conventions_slug_cap.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 90-archy-867.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 867.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Test only. No behaviour changes. The chatbot did not run the test and did not run the mutation check the bug report asks for (change 40 to 400 and confirm the test fails).

## Search words

archy conventions registries literal_names _first_arg_slug 40 character slug cap missing test mutation

## The full patch

`````diff
diff --git a/tests/test_conventions_slug_cap.py b/tests/test_conventions_slug_cap.py
new file mode 100644
index 0000000..d043e2f
--- /dev/null
+++ b/tests/test_conventions_slug_cap.py
@@ -0,0 +1,29 @@
+"""The 40-character cap on registry literal names (#867)."""
+
+from __future__ import annotations
+
+from archy.conventions import compute_conventions
+from tests.conventions_helpers import _tmp
+
+
+def test_registry_literal_name_cap_is_40_characters():
+    """A first argument of 40 characters is a copyable slug; 41 is content.
+
+    The space rule was covered and the length bound was not: changing
+    `len(first) <= 40` to `<= 400` left every test green.
+    """
+    at_cap = "a" * 40
+    over_cap = "b" * 41
+    src = f"""
+class ErrorCode:
+    def __init__(self, code): ...
+A = ErrorCode("{at_cap}")
+B = ErrorCode("{over_cap}")
+C = ErrorCode("short-code")
+"""
+    report = compute_conventions(_tmp(src))
+    entry = next(r for r in report.registries if r.constructor == "ErrorCode")
+    assert entry.count == 3
+    assert at_cap in entry.literal_names
+    assert over_cap not in entry.literal_names
+    assert entry.literal_names == tuple(sorted({at_cap, "short-code"}))
`````

[Back to the shelf](README.md)
