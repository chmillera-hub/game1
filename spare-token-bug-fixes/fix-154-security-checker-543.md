# Fix 154: security-checker: no test covers a type list of only null in the Gemini conversion

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): gemini_generate.py の _convert_type で未テストの分岐をテストする（1 行）
- Bug report: number 543 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/543))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/154-security-checker-543.patch](fixes/154-security-checker-543.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/154-security-checker-543.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-154-security-checker-543.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-154-security-checker-543.html

## The bug

_convert_type in src/security_checker/providers/http/dialects/gemini_generate.py turns a type list that holds only null into a nullable string. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_gemini_convert_type_null_only.py expects a nullable STRING for [null] and for an empty list and checks that a concrete type in the list is kept.

## Files changed

- tests/unit/test_gemini_convert_type_null_only.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 154-security-checker-543.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 543.

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

security-checker gemini_generate _convert_type type list null only nullable STRING untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_gemini_convert_type_null_only.py b/tests/unit/test_gemini_convert_type_null_only.py
new file mode 100644
index 0000000..5ffab13
--- /dev/null
+++ b/tests/unit/test_gemini_convert_type_null_only.py
@@ -0,0 +1,19 @@
+"""gemini_generate._convert_type: 型の配列が null だけのときは nullable な STRING になること."""
+
+from __future__ import annotations
+
+from security_checker.providers.http.dialects.gemini_generate import _convert_type
+
+
+def test_type_list_of_null_only_becomes_a_nullable_string() -> None:
+    assert _convert_type(["null"]) == {"type": "STRING", "nullable": True}
+
+
+def test_empty_type_list_becomes_a_nullable_string() -> None:
+    assert _convert_type([]) == {"type": "STRING", "nullable": True}
+
+
+def test_type_list_with_a_concrete_type_keeps_that_type() -> None:
+    """対になるケース. 具体的な型があればそれを大文字にして使う."""
+    assert _convert_type(["integer", "null"]) == {"type": "INTEGER", "nullable": True}
+    assert _convert_type(["integer"]) == {"type": "INTEGER", "nullable": False}
`````

[Back to the shelf](README.md)
