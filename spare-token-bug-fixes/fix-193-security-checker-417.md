# Fix 193: security-checker: public names in runner.py have no docstring (__init__ and capabilities)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(providers): runner.py の公開クラス・メソッド 2 個に docstring が無い
- Bug report: number 417 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/417))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/193-security-checker-417.patch](fixes/193-security-checker-417.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/193-security-checker-417.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-193-security-checker-417.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-193-security-checker-417.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/providers/process/runner.py: __init__ and capabilities. A person who writes a plugin cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/providers/process/runner.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/providers/process/runner.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 193-security-checker-417.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 417.

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

security-checker docstring D1 ruff missing docstring runner.py __init__ and capabilities

## The full patch

`````diff
diff --git a/src/security_checker/providers/process/runner.py b/src/security_checker/providers/process/runner.py
index 49e2670..3eb17c6 100644
--- a/src/security_checker/providers/process/runner.py
+++ b/src/security_checker/providers/process/runner.py
@@ -85,6 +85,11 @@ class ProcessProvider:
         environ: Mapping[str, str] | None = None,
         runner: Runner | None = None,
     ) -> None:
+        """起動するコマンドと、その CLI の入出力の形を受け取る. ここでは起動しない.
+
+        `capabilities` は設定で宣言された値をそのまま使う (CLI に問い合わせない)。
+        `runner` はテストで子プロセスの起動を差し替えるためのもの。
+        """
         self.name = name
         self.dialect = TEXT_IO_DIALECT
         self.command = list(command)
@@ -98,6 +103,7 @@ class ProcessProvider:
 
     @property
     def capabilities(self) -> Capabilities:
+        """設定で宣言された Capabilities. 実行中に変わらない."""
         return self._capabilities
 
     async def complete(self, req: CompletionRequest) -> CompletionResponse:
`````

[Back to the shelf](README.md)
