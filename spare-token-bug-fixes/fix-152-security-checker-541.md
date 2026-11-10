# Fix 152: security-checker: no test covers a schema node that is not a dictionary in the Gemini conversion

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): gemini_generate.py の _convert で未テストの分岐をテストする（1 行）
- Bug report: number 541 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/541))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/152-security-checker-541.patch](fixes/152-security-checker-541.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/152-security-checker-541.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-152-security-checker-541.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-152-security-checker-541.html

## The bug

_convert in src/security_checker/providers/http/dialects/gemini_generate.py returns an empty schema for a node that is not a dictionary. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_gemini_convert_non_dict_node.py expects an empty schema for None and a string and a number and a list and a boolean. A second test expects an array whose items value is not a dictionary to convert without an error.

## Files changed

- tests/unit/test_gemini_convert_non_dict_node.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 152-security-checker-541.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 541.

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

security-checker gemini_generate _convert non-dict node empty schema responseSchema untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_gemini_convert_non_dict_node.py b/tests/unit/test_gemini_convert_non_dict_node.py
new file mode 100644
index 0000000..5f7fadf
--- /dev/null
+++ b/tests/unit/test_gemini_convert_non_dict_node.py
@@ -0,0 +1,19 @@
+"""gemini_generate._convert: 辞書でないノードは空のスキーマになること."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.providers.http.dialects.gemini_generate import _convert
+
+
+@pytest.mark.parametrize("node", [None, "string", 3, ["type", "string"], True])
+def test_non_dict_node_becomes_an_empty_schema(node: object) -> None:
+    assert _convert(node, defs={}) == {}
+
+
+def test_non_dict_items_becomes_an_empty_schema_inside_an_array() -> None:
+    """配列の items が辞書でなくても落ちず、空のスキーマとして送られる."""
+    converted = _convert({"type": "array", "items": True}, defs={})
+
+    assert converted == {"type": "ARRAY", "items": {}}
`````

[Back to the shelf](README.md)
