# Fix 206: security-checker: no test covers a quoted path in a diff header

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(github): pr.py の _strip_prefix で未テストの分岐をテストする（1 行）
- Bug report: number 515 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/515))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/206-security-checker-515.patch](fixes/206-security-checker-515.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/206-security-checker-515.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-206-security-checker-515.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-206-security-checker-515.html

## The bug

_strip_prefix in src/security_checker/github/pr.py removes quotes around a path in a diff header. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_pr_strip_prefix.py checks a quoted path with and without the b/ prefix and /dev/null and text after a tab and plain paths.

## Files changed

- tests/unit/test_pr_strip_prefix.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 206-security-checker-515.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 515.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a scratch copy of the function on three inputs. The bug report lists the untested lines from a coverage run on an older commit. The chatbot did not run the tests or a coverage tool so nobody has confirmed that the new tests reach the named lines.

## Search words

security-checker github pr _strip_prefix quoted path diff header a/ b/ prefix untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_pr_strip_prefix.py b/tests/unit/test_pr_strip_prefix.py
new file mode 100644
index 0000000..2d50ce7
--- /dev/null
+++ b/tests/unit/test_pr_strip_prefix.py
@@ -0,0 +1,27 @@
+"""pr._strip_prefix: diff のヘッダ行からパスを取り出すこと."""
+
+from __future__ import annotations
+
+from security_checker.github.pr import _strip_prefix
+
+
+def test_quotes_around_the_path_are_removed() -> None:
+    assert _strip_prefix('"b/docs/my file.md"') == "docs/my file.md"
+
+
+def test_quoted_path_without_a_prefix_is_kept() -> None:
+    assert _strip_prefix('"docs/my file.md"') == "docs/my file.md"
+
+
+def test_dev_null_is_no_path() -> None:
+    assert _strip_prefix("/dev/null") is None
+
+
+def test_text_after_a_tab_is_dropped() -> None:
+    assert _strip_prefix("b/src/app.py\t2026-01-01 00:00:00") == "src/app.py"
+
+
+def test_plain_paths_lose_only_the_a_or_b_prefix() -> None:
+    assert _strip_prefix("a/src/app.py") == "src/app.py"
+    assert _strip_prefix("b/src/app.py") == "src/app.py"
+    assert _strip_prefix("src/app.py") == "src/app.py"
`````

[Back to the shelf](README.md)
