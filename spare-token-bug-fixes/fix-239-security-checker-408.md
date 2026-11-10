# Fix 239: security-checker: public names in providers/base.py have no docstring (aclose and apply and capabilities and complete and health_check)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(providers): base.py の公開クラス・メソッド 5 個に docstring が無い
- Bug report: number 408 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/408))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/239-security-checker-408.patch](fixes/239-security-checker-408.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/239-security-checker-408.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-239-security-checker-408.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-239-security-checker-408.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/providers/base.py: aclose and apply and capabilities and complete and health_check. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/providers/base.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/providers/base.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 239-security-checker-408.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 408.

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

security-checker docstring D1 ruff missing docstring base.py aclose and apply and capabilities and complete and health_check

## The full patch

`````diff
diff --git a/src/security_checker/providers/base.py b/src/security_checker/providers/base.py
index 4594a69..0544392 100644
--- a/src/security_checker/providers/base.py
+++ b/src/security_checker/providers/base.py
@@ -110,13 +110,21 @@ class LLMProvider(Protocol):
     dialect: str
 
     @property
-    def capabilities(self) -> Capabilities: ...
+    def capabilities(self) -> Capabilities:
+        """このエンドポイントができること. 文脈長や構造化出力の方式を上位が読む."""
+        ...
 
-    async def complete(self, req: CompletionRequest) -> CompletionResponse: ...
+    async def complete(self, req: CompletionRequest) -> CompletionResponse:
+        """1 リクエスト = 1 判定. 失敗は ProviderError の系統で知らせ、リトライはしない."""
+        ...
 
-    async def health_check(self) -> HealthStatus: ...
+    async def health_check(self) -> HealthStatus:
+        """到達できるかを確かめる. 失敗しても例外にせず HealthStatus で返す."""
+        ...
 
-    async def aclose(self) -> None: ...
+    async def aclose(self) -> None:
+        """保持している資源を解放する. 2 回呼んでも安全であること."""
+        ...
 
 
 class CapabilityOverrides(BaseModel):
@@ -134,5 +142,6 @@ class CapabilityOverrides(BaseModel):
     output_limit_param: Literal["max_tokens", "max_completion_tokens"] | None = None
 
     def apply(self, base: Capabilities) -> Capabilities:
+        """指定された項目だけを `base` に上書きした写しを返す. None の項目は触らない."""
         updates = {key: value for key, value in self.model_dump().items() if value is not None}
         return base.model_copy(update=updates)
`````

[Back to the shelf](README.md)
