# Fix 257: security-checker: no test covers a tiktoken dictionary that cannot be loaded

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: test(context): budget.py の _encode_fn で未テストの分岐をテストする（4 行）
- Bug report: number 491 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/491))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/257-security-checker-491.patch](fixes/257-security-checker-491.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/257-security-checker-491.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-257-security-checker-491.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-257-security-checker-491.html

## The bug

_encode_fn in src/security_checker/context/budget.py returns None when tiktoken cannot load its dictionary so the token estimate falls back to a character count. No test ran those lines.

## The fix

Tests only. A new file tests/unit/test_budget_encode_fn_fallback.py puts a stand-in tiktoken module in place whose loader fails and expects None plus the fallback count. A paired test uses a stand-in that works. The cached result is cleared before and after each test.

## Files changed

- tests/unit/test_budget_encode_fn_fallback.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 257-security-checker-491.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 491.

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

security-checker budget _encode_fn tiktoken get_encoding cl100k_base failure fallback lru_cache untested branch

## The full patch

`````diff
diff --git a/tests/unit/test_budget_encode_fn_fallback.py b/tests/unit/test_budget_encode_fn_fallback.py
new file mode 100644
index 0000000..3a2a436
--- /dev/null
+++ b/tests/unit/test_budget_encode_fn_fallback.py
@@ -0,0 +1,57 @@
+"""budget._encode_fn: tiktoken の辞書を取得できない環境では None を返し、概算に落とすこと."""
+
+from __future__ import annotations
+
+import sys
+from collections.abc import Iterator
+from types import ModuleType
+
+import pytest
+
+from security_checker.context import budget
+
+
+@pytest.fixture(autouse=True)
+def _fresh_cache() -> Iterator[None]:
+    """_encode_fn は結果を覚えるので、前後で消す (他のテストに偽物を残さない)."""
+    budget._encode_fn.cache_clear()
+    yield
+    budget._encode_fn.cache_clear()
+
+
+def _fake_tiktoken(get_encoding: object) -> ModuleType:
+    module = ModuleType("tiktoken")
+    module.get_encoding = get_encoding  # type: ignore[attr-defined]
+    return module
+
+
+def test_failed_dictionary_download_gives_none(monkeypatch: pytest.MonkeyPatch) -> None:
+    def fail(_name: str) -> object:
+        raise OSError("辞書をダウンロードできません")
+
+    monkeypatch.setitem(sys.modules, "tiktoken", _fake_tiktoken(fail))
+
+    assert budget._encode_fn() is None
+    assert budget.estimate_tokens("abcd" * 10) == 10
+
+
+def test_available_encoder_is_returned(monkeypatch: pytest.MonkeyPatch) -> None:
+    """対になるケース. 辞書が取れれば、その encode を返す."""
+
+    class _Encoder:
+        def encode(self, text: str) -> list[int]:
+            return [0] * len(text)
+
+    requested: list[str] = []
+
+    def get_encoding(name: str) -> _Encoder:
+        requested.append(name)
+        return _Encoder()
+
+    monkeypatch.setitem(sys.modules, "tiktoken", _fake_tiktoken(get_encoding))
+
+    encode = budget._encode_fn()
+
+    assert encode is not None
+    assert encode("abc") == [0, 0, 0]
+    assert requested == ["cl100k_base"]
`````

[Back to the shelf](README.md)
