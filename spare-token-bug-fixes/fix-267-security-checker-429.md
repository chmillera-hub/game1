# Fix 267: security-checker: public names in testing/fakes.py have no docstring (two __init__ methods and aclose and capabilities and complete and health_check and probe and scan)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(testing): fakes.py の公開クラス・メソッド 8 個に docstring が無い
- Bug report: number 429 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/429))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/267-security-checker-429.patch](fixes/267-security-checker-429.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/267-security-checker-429.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-267-security-checker-429.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-267-security-checker-429.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/testing/fakes.py: two __init__ methods and aclose and capabilities and complete and health_check and probe and scan. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/testing/fakes.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/testing/fakes.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 267-security-checker-429.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 429.

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

security-checker docstring D1 ruff missing docstring fakes.py two __init__ methods and aclose and capabilities and complete and health_check and probe and scan

## The full patch

`````diff
diff --git a/src/security_checker/testing/fakes.py b/src/security_checker/testing/fakes.py
index 72f9971..05ebdd3 100644
--- a/src/security_checker/testing/fakes.py
+++ b/src/security_checker/testing/fakes.py
@@ -39,6 +39,7 @@ class FakeScanner:
         exit_code: int | None = 0,
         raises: Exception | None = None,
     ) -> None:
+        """返す結果を決める. `raises` を渡すと scan がその例外を投げる."""
         self.name = name
         self.category = category
         self._status = status
@@ -49,9 +50,11 @@ class FakeScanner:
         self.calls = 0
 
     def probe(self) -> ToolStatus:
+        """status が skipped のときだけ「未導入」として答える."""
         return ToolStatus(available=self._status is not ScanStatus.SKIPPED, reason=self._reason)
 
     async def scan(self, target: Target, ctx: ScanContext) -> ScanResult:
+        """呼ばれた回数を数え、決めておいた結果を返す (または例外を投げる)."""
         self.calls += 1
         if self._raises is not None:
             raise self._raises
@@ -83,6 +86,7 @@ class ScriptedProvider:
         capabilities: Capabilities | None = None,
         usage: Usage | None = None,
     ) -> None:
+        """`script` は返す応答 (または投げる例外) の列. 先頭から 1 回に 1 つ使う."""
         self.name = name
         self.model = model
         self.dialect = dialect
@@ -96,9 +100,11 @@ class ScriptedProvider:
 
     @property
     def capabilities(self) -> Capabilities:
+        """渡された Capabilities. 省略時は既定値."""
         return self._capabilities
 
     async def complete(self, req: CompletionRequest) -> CompletionResponse:
+        """リクエストを記録し、script の次の項目を返す. 例外ならそれを投げる."""
         self.requests.append(req)
         if not self._script:
             raise AssertionError("ScriptedProvider: 応答が尽きました")
@@ -114,9 +120,11 @@ class ScriptedProvider:
         )
 
     async def health_check(self) -> HealthStatus:
+        """常に ok."""
         return HealthStatus(ok=True)
 
     async def aclose(self) -> None:
+        """閉じられたことを `closed` に記録する."""
         self.closed = True
`````

[Back to the shelf](README.md)
