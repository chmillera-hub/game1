# Fix 159: security-checker: no test covers the plain reason for a Gemini reply with no candidates

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): gemini_generate.py の _no_candidates_reason で未テストの分岐をテストする（1 行）
- Bug report: number 544 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/544))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/159-security-checker-544.patch](fixes/159-security-checker-544.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/159-security-checker-544.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-159-security-checker-544.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-159-security-checker-544.html

## The bug

_no_candidates_reason in src/security_checker/providers/http/dialects/gemini_generate.py returns a plain message when the reply has no candidates and no block reason. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_gemini_no_candidates_reason.py expects the plain message for four shapes without a block reason and expects a reply with a block reason to name the reason and expects parse_response to raise with the plain message.

## Files changed

- tests/unit/test_gemini_no_candidates_reason.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 159-security-checker-544.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 544.

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

security-checker gemini_generate _no_candidates_reason promptFeedback blockReason candidates missing untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_gemini_no_candidates_reason.py b/tests/unit/test_gemini_no_candidates_reason.py
new file mode 100644
index 0000000..fd29a2f
--- /dev/null
+++ b/tests/unit/test_gemini_no_candidates_reason.py
@@ -0,0 +1,37 @@
+"""gemini_generate._no_candidates_reason: 応答が空の理由を伝えること."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.providers.errors import ProviderResponseError
+from security_checker.providers.http.dialects.gemini_generate import (
+    GeminiGenerateDialect,
+    _no_candidates_reason,
+)
+
+
+@pytest.mark.parametrize(
+    "payload",
+    [
+        {},
+        {"promptFeedback": {}},
+        {"promptFeedback": "blocked"},
+        {"promptFeedback": {"blockReason": ""}},
+    ],
+)
+def test_reason_without_a_block_reason_is_the_plain_message(payload: dict[str, object]) -> None:
+    assert _no_candidates_reason(payload) == "応答に candidates がありません"
+
+
+def test_reason_with_a_block_reason_names_it() -> None:
+    """対になるケース. 拒否された理由があればそれを伝える."""
+    reason = _no_candidates_reason({"promptFeedback": {"blockReason": "SAFETY"}})
+
+    assert "blockReason: SAFETY" in reason
+
+
+@pytest.mark.parametrize("candidates", [None, [], "none"])
+def test_parse_response_raises_the_plain_message(candidates: object) -> None:
+    with pytest.raises(ProviderResponseError, match="応答に candidates がありません"):
+        GeminiGenerateDialect().parse_response({"candidates": candidates})
`````

[Back to the shelf](README.md)
