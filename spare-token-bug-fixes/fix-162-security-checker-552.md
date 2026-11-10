# Fix 162: security-checker: no test covers resolve_http_preset when nothing matches

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): loader.py の resolve_http_preset で未テストの分岐をテストする（1 行）
- Bug report: number 552 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/552))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/162-security-checker-552.patch](fixes/162-security-checker-552.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/162-security-checker-552.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-162-security-checker-552.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-162-security-checker-552.html

## The bug

resolve_http_preset in src/security_checker/providers/presets/loader.py returns None when no name is given and no pattern matches. No test ran that line.

## The fix

Tests only. A new file tests/unit/test_presets_resolve_no_match.py expects None when no pattern matches and when the base address or the model is missing and checks that a preset is still found by name.

## Files changed

- tests/unit/test_presets_resolve_no_match.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 162-security-checker-552.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 552.

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

security-checker presets loader resolve_http_preset no match None base_url model untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_presets_resolve_no_match.py b/tests/unit/test_presets_resolve_no_match.py
new file mode 100644
index 0000000..a54940d
--- /dev/null
+++ b/tests/unit/test_presets_resolve_no_match.py
@@ -0,0 +1,29 @@
+"""resolve_http_preset: 名前も一致するパターンも無ければ None を返すこと."""
+
+from __future__ import annotations
+
+from security_checker.providers.presets.loader import HttpPreset, resolve_http_preset
+
+PRESETS = {
+    "local": HttpPreset(name="local", dialect="ollama_chat", base_url="http://localhost:11434"),
+}
+
+
+def test_no_preset_when_no_pattern_matches() -> None:
+    resolved = resolve_http_preset(
+        PRESETS, name=None, base_url="https://api.example.com/v1", model="gpt-x"
+    )
+
+    assert resolved is None
+
+
+def test_no_preset_without_a_base_url_or_a_model() -> None:
+    assert resolve_http_preset(PRESETS, name=None, base_url=None, model="gpt-x") is None
+    assert resolve_http_preset(PRESETS, name=None, base_url="https://x.test", model=None) is None
+
+
+def test_named_preset_is_still_found() -> None:
+    """対になるケース. 名前で指定すればパターンに関係なく返る."""
+    resolved = resolve_http_preset(PRESETS, name="local", base_url=None, model=None)
+
+    assert resolved is PRESETS["local"]
`````

[Back to the shelf](README.md)
