# Fix 153: security-checker: no test covers a null-only union or a carried description in the Gemini conversion

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): gemini_generate.py の _convert_any_of で未テストの分岐をテストする（2 行）
- Bug report: number 542 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/542))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/153-security-checker-542.patch](fixes/153-security-checker-542.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/153-security-checker-542.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-153-security-checker-542.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-153-security-checker-542.html

## The bug

_convert_any_of in src/security_checker/providers/http/dialects/gemini_generate.py turns a union of only null into a nullable string and copies the union's description onto the chosen branch. No test ran those two lines.

## The fix

Tests only. A new file tests/unit/test_gemini_convert_any_of_edges.py checks a null-only union and an empty union and a description carried from the union and a branch description that is not overwritten.

## Files changed

- tests/unit/test_gemini_convert_any_of_edges.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 153-security-checker-542.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 542.

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

security-checker gemini_generate _convert_any_of anyOf null nullable STRING description untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_gemini_convert_any_of_edges.py b/tests/unit/test_gemini_convert_any_of_edges.py
new file mode 100644
index 0000000..57bff6f
--- /dev/null
+++ b/tests/unit/test_gemini_convert_any_of_edges.py
@@ -0,0 +1,31 @@
+"""gemini_generate._convert_any_of: null だけの union と description の引き継ぎ."""
+
+from __future__ import annotations
+
+from security_checker.providers.http.dialects.gemini_generate import _convert_any_of
+
+
+def test_union_of_null_only_becomes_a_nullable_string() -> None:
+    node = {"anyOf": [{"type": "null"}]}
+
+    assert _convert_any_of(node, defs={}) == {"type": "STRING", "nullable": True}
+
+
+def test_empty_union_becomes_a_nullable_string() -> None:
+    assert _convert_any_of({"anyOf": []}, defs={}) == {"type": "STRING", "nullable": True}
+
+
+def test_description_of_the_union_is_carried_to_the_chosen_branch() -> None:
+    node = {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "理由"}
+
+    assert _convert_any_of(node, defs={}) == {
+        "type": "STRING",
+        "nullable": True,
+        "description": "理由",
+    }
+
+
+def test_description_of_the_branch_is_not_overwritten() -> None:
+    node = {"anyOf": [{"type": "string", "description": "枝"}], "description": "親"}
+
+    assert _convert_any_of(node, defs={})["description"] == "枝"
`````

[Back to the shelf](README.md)
