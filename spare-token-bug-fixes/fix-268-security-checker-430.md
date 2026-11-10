# Fix 268: security-checker: public names in testing/provider_contract.py have no docstring (make_provider and make_request and test_aclose_is_idempotent and test_capabilities_are_valid and test_complete_returns_response and test_identity_fields)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(testing): provider_contract.py の公開クラス・メソッド 7 個に docstring が無い
- Bug report: number 430 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/430))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/268-security-checker-430.patch](fixes/268-security-checker-430.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/268-security-checker-430.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-268-security-checker-430.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-268-security-checker-430.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/testing/provider_contract.py: make_provider and make_request and test_aclose_is_idempotent and test_capabilities_are_valid and test_complete_returns_response and test_identity_fields. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/testing/provider_contract.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/testing/provider_contract.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 268-security-checker-430.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 430.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring provider_contract.py make_provider and make_request and test_aclose_is_idempotent and test_capabilities_are_valid and test_complete_returns_response and test_identity_fields

## The full patch

`````diff
diff --git a/src/security_checker/testing/provider_contract.py b/src/security_checker/testing/provider_contract.py
index 6ccbe96..e4f9133 100644
--- a/src/security_checker/testing/provider_contract.py
+++ b/src/security_checker/testing/provider_contract.py
@@ -44,6 +44,7 @@ class ProviderContractTests:
     """すべての Provider が満たすべき契約."""
 
     def make_provider(self) -> LLMProvider:  # pragma: no cover - サブクラスが実装する
+        """検証する Provider を作る. 正常な応答を 1 回返せる状態にしておく."""
         raise NotImplementedError
 
     def make_http_provider(
@@ -70,6 +71,7 @@ class ProviderContractTests:
         return provider
 
     def make_request(self, **overrides: Any) -> CompletionRequest:
+        """契約テストで送る最小の CompletionRequest. 項目は `overrides` で差し替えられる."""
         payload: dict[str, Any] = {
             "system": "system",
             "user": "user",
@@ -81,6 +83,7 @@ class ProviderContractTests:
         return CompletionRequest(**payload)
 
     def test_capabilities_are_valid(self) -> None:
+        """capabilities が Capabilities 型で、上限が正の値であること."""
         provider = self.make_provider()
         capabilities = provider.capabilities
         assert isinstance(capabilities, Capabilities)
@@ -89,12 +92,14 @@ class ProviderContractTests:
         assert isinstance(capabilities.structured_output, StructuredMode)
 
     def test_identity_fields(self) -> None:
+        """transport と dialect が名乗られていること."""
         provider = self.make_provider()
         assert provider.transport in ("http", "process")
         assert isinstance(provider.dialect, str) and provider.dialect
 
     @pytest.mark.asyncio
     async def test_complete_returns_response(self) -> None:
+        """complete が CompletionResponse を返し、usage が埋まっていること."""
         provider = self.make_provider()
         response = await provider.complete(self.make_request())
         assert isinstance(response, CompletionResponse)
@@ -104,6 +109,7 @@ class ProviderContractTests:
 
     @pytest.mark.asyncio
     async def test_aclose_is_idempotent(self) -> None:
+        """aclose を 2 回呼んでも失敗しないこと."""
         provider = self.make_provider()
         await provider.aclose()
         await provider.aclose()
`````

[Back to the shelf](README.md)
