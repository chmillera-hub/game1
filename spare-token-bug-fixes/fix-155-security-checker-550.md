# Fix 155: security-checker: no test covers a preset whose model pattern does not match

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): loader.py の matches で未テストの分岐をテストする（1 行）
- Bug report: number 550 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/550))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/155-security-checker-550.patch](fixes/155-security-checker-550.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/155-security-checker-550.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-155-security-checker-550.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-155-security-checker-550.html

## The bug

PresetMatch.matches in src/security_checker/providers/presets/loader.py returns False when the model pattern does not match. No test ran that line so a preset could apply to the wrong model unnoticed.

## The fix

Tests only. A new file tests/unit/test_preset_match_mismatch.py checks a model mismatch and a host match with a model mismatch and a host mismatch and a full match and a match with no condition.

## Files changed

- tests/unit/test_preset_match_mismatch.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 155-security-checker-550.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 550.

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

security-checker presets loader PresetMatch matches host model regex mismatch False untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_preset_match_mismatch.py b/tests/unit/test_preset_match_mismatch.py
new file mode 100644
index 0000000..5798d57
--- /dev/null
+++ b/tests/unit/test_preset_match_mismatch.py
@@ -0,0 +1,32 @@
+"""PresetMatch.matches: host や model が合わないプリセットは適用されないこと."""
+
+from __future__ import annotations
+
+from security_checker.providers.presets.loader import PresetMatch
+
+BASE_URL = "https://api.example.com/v1"
+
+
+def test_model_pattern_that_does_not_match_is_rejected() -> None:
+    assert PresetMatch(model="^gpt-").matches(BASE_URL, "claude-x") is False
+
+
+def test_matching_host_with_a_model_that_does_not_match_is_rejected() -> None:
+    match = PresetMatch(host="api.example.com", model="^gpt-")
+
+    assert match.matches(BASE_URL, "claude-x") is False
+
+
+def test_different_host_is_rejected() -> None:
+    assert PresetMatch(host="other.example.com").matches(BASE_URL, "gpt-x") is False
+
+
+def test_matching_host_and_model_is_accepted() -> None:
+    """対になるケース. 両方合えば適用される."""
+    match = PresetMatch(host="api.example.com", model="^gpt-")
+
+    assert match.matches(BASE_URL, "gpt-x") is True
+
+
+def test_match_without_any_condition_never_applies() -> None:
+    assert PresetMatch().matches(BASE_URL, "gpt-x") is False
`````

[Back to the shelf](README.md)
