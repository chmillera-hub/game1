# Fix 157: security-checker: no test covers the health check payload of the Ollama dialect

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(providers): ollama_chat.py の health_payload で未テストの分岐をテストする（1 行）
- Bug report: number 546 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/546))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/157-security-checker-546.patch](fixes/157-security-checker-546.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/157-security-checker-546.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-157-security-checker-546.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-157-security-checker-546.html

## The bug

health_payload in src/security_checker/providers/http/dialects/ollama_chat.py builds the small request used to check that an endpoint answers. No test ran that function.

## The fix

Tests only. A new file tests/unit/test_ollama_chat_health_payload.py expects the exact payload (a ping message with num_predict 1 and the default num_ctx) and expects a configured num_ctx to be used.

## Files changed

- tests/unit/test_ollama_chat_health_payload.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 157-security-checker-546.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 546.

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

security-checker ollama_chat health_payload ping num_ctx num_predict untested

## The full patch

`````diff
diff --git a/tests/unit/test_ollama_chat_health_payload.py b/tests/unit/test_ollama_chat_health_payload.py
new file mode 100644
index 0000000..3d5e058
--- /dev/null
+++ b/tests/unit/test_ollama_chat_health_payload.py
@@ -0,0 +1,27 @@
+"""ollama_chat.health_payload: 疎通確認でも num_ctx を明示し、出力は 1 トークンに抑えること."""
+
+from __future__ import annotations
+
+from security_checker.providers.base import Capabilities
+from security_checker.providers.http.dialects.base import DialectOptions
+from security_checker.providers.http.dialects.ollama_chat import (
+    DEFAULT_NUM_CTX,
+    OllamaChatDialect,
+)
+
+
+def test_health_payload_is_a_one_token_ping() -> None:
+    payload = OllamaChatDialect().health_payload("m", Capabilities())
+
+    assert payload == {
+        "model": "m",
+        "messages": [{"role": "user", "content": "ping"}],
+        "stream": False,
+        "options": {"num_ctx": DEFAULT_NUM_CTX, "num_predict": 1},
+    }
+
+
+def test_health_payload_uses_the_configured_num_ctx() -> None:
+    dialect = OllamaChatDialect(DialectOptions(num_ctx=2048))
+
+    assert dialect.health_payload("m", Capabilities())["options"]["num_ctx"] == 2048
`````

[Back to the shelf](README.md)
