# Fix 212: security-checker: no test covers empty text or a real encoder in the token estimate

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(context): budget.py の estimate_tokens で未テストの分岐をテストする（2 行）
- Bug report: number 492 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/492))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/212-security-checker-492.patch](fixes/212-security-checker-492.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/212-security-checker-492.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-212-security-checker-492.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-212-security-checker-492.html

## The bug

estimate_tokens in src/security_checker/context/budget.py returns 0 for empty text and uses the tiktoken encoder when one is available. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_budget_estimate_tokens.py checks empty text and a stand-in encoder and the character count fallback.

## Files changed

- tests/unit/test_budget_estimate_tokens.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 212-security-checker-492.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 492.

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

security-checker budget estimate_tokens empty tiktoken encode fallback CHARS_PER_TOKEN untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_budget_estimate_tokens.py b/tests/unit/test_budget_estimate_tokens.py
new file mode 100644
index 0000000..1cf0e1b
--- /dev/null
+++ b/tests/unit/test_budget_estimate_tokens.py
@@ -0,0 +1,27 @@
+"""budget.estimate_tokens: 空の文字列は 0、tiktoken があればその数え方を使うこと."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.context import budget
+from security_checker.context.budget import CHARS_PER_TOKEN, estimate_tokens
+
+
+def test_empty_text_is_zero_tokens() -> None:
+    assert estimate_tokens("") == 0
+
+
+def test_encoder_is_used_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
+    # 1 文字 = 1 トークンと数える偽のエンコーダ
+    monkeypatch.setattr(budget, "_encode_fn", lambda: lambda text: [0] * len(text))
+
+    assert estimate_tokens("abcdefghij") == 10
+
+
+def test_character_count_is_the_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
+    """対になるケース. エンコーダが無ければ文字数から概算し、切り上げる."""
+    monkeypatch.setattr(budget, "_encode_fn", lambda: None)
+
+    assert estimate_tokens("a") == 1
+    assert estimate_tokens("a" * (CHARS_PER_TOKEN + 1)) == 2
`````

[Back to the shelf](README.md)
