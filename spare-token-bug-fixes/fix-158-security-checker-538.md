# Fix 158: security-checker: no test covers a first candidate that is not an object in the Gemini reply parser

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): gemini_generate.py の parse_response で未テストの分岐をテストする（1 行）
- Bug report: number 538 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/538))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/158-security-checker-538.patch](fixes/158-security-checker-538.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/158-security-checker-538.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-158-security-checker-538.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-158-security-checker-538.html

## The bug

parse_response in src/security_checker/providers/http/dialects/gemini_generate.py raises an error when candidates[0] is not an object. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_gemini_parse_response_first_candidate.py expects ProviderResponseError for a string and a number and null and a list as the first candidate. A paired test expects an empty object to give empty text without an error.

## Files changed

- tests/unit/test_gemini_parse_response_first_candidate.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 158-security-checker-538.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 538.

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

security-checker gemini_generate parse_response candidates[0] not an object ProviderResponseError untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_gemini_parse_response_first_candidate.py b/tests/unit/test_gemini_parse_response_first_candidate.py
new file mode 100644
index 0000000..c118c91
--- /dev/null
+++ b/tests/unit/test_gemini_parse_response_first_candidate.py
@@ -0,0 +1,22 @@
+"""gemini_generate.parse_response: candidates[0] がオブジェクトでない応答はエラーになること."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.providers.errors import ProviderResponseError
+from security_checker.providers.http.dialects.gemini_generate import GeminiGenerateDialect
+
+
+@pytest.mark.parametrize("first", ["text", 3, None, ["a"]])
+def test_first_candidate_that_is_not_an_object_is_a_response_error(first: object) -> None:
+    with pytest.raises(ProviderResponseError, match=r"candidates\[0\]"):
+        GeminiGenerateDialect().parse_response({"candidates": [first]})
+
+
+def test_first_candidate_without_content_is_read_as_empty_text() -> None:
+    """対になるケース. オブジェクトであれば、本文が無くてもエラーにはしない."""
+    response = GeminiGenerateDialect().parse_response({"candidates": [{}]})
+
+    assert response.text == ""
+    assert response.finish_reason == "stop"
`````

[Back to the shelf](README.md)
