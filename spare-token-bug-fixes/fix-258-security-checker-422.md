# Fix 258: security-checker: public names in scanners/base.py have no docstring (__init__ and elapsed_ms and failed and ok and probe and scan and skipped)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(scanners): base.py の公開クラス・メソッド 9 個に docstring が無い
- Bug report: number 422 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/422))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/258-security-checker-422.patch](fixes/258-security-checker-422.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/258-security-checker-422.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-258-security-checker-422.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-258-security-checker-422.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/scanners/base.py: __init__ and elapsed_ms and failed and ok and probe and scan and skipped. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/scanners/base.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/scanners/base.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 258-security-checker-422.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 422.

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

security-checker docstring D1 ruff missing docstring base.py __init__ and elapsed_ms and failed and ok and probe and scan and skipped

## The full patch

`````diff
diff --git a/src/security_checker/scanners/base.py b/src/security_checker/scanners/base.py
index bb8f154..f5fa4ab 100644
--- a/src/security_checker/scanners/base.py
+++ b/src/security_checker/scanners/base.py
@@ -87,9 +87,13 @@ class Scanner(Protocol):
     category: Category
     requires: ClassVar[list[str]]
 
-    def probe(self) -> ToolStatus: ...
+    def probe(self) -> ToolStatus:
+        """外部コマンドが使えるかを調べる. 使えなくても例外にせず ToolStatus で返す."""
+        ...
 
-    async def scan(self, target: Target, ctx: ScanContext) -> ScanResult: ...
+    async def scan(self, target: Target, ctx: ScanContext) -> ScanResult:
+        """検査して結果を返す. 未導入は skipped、失敗は failed とし、例外にしない."""
+        ...
 
 
 @dataclass
@@ -176,20 +180,24 @@ class BaseScanner:
     install_hint: str = ""
 
     def __init__(self, settings: ScannerConfig) -> None:
+        """`settings` はこのスキャナの設定 (`scanners.<名前>`)."""
         self.settings = settings
 
     def probe(self) -> ToolStatus:
+        """`requires` の先頭のコマンドを調べる. 無ければ導入方法の案内を理由に足す."""
         status = probe_command(self.requires[0])
         if not status.available and self.install_hint:
             return status.model_copy(update={"reason": f"{status.reason}。{self.install_hint}"})
         return status
 
     async def scan(self, target: Target, ctx: ScanContext) -> ScanResult:  # pragma: no cover
+        """各スキャナが実装する."""
         raise NotImplementedError
 
     # --- 結果生成のヘルパ ---------------------------------------------------
 
     def skipped(self, reason: str, *, version: str | None = None) -> ScanResult:
+        """実行しなかった (未導入など) という結果を作る."""
         return ScanResult(
             scanner=self.name,
             category=self.category,
@@ -208,6 +216,7 @@ class BaseScanner:
         version: str | None = None,
         raw_path: Path | None = None,
     ) -> ScanResult:
+        """実行に失敗したという結果を作る. stderr は先頭だけを抜き出して残す."""
         stderr_text = excerpt(stderr) if isinstance(stderr, bytes) else stderr
         return ScanResult(
             scanner=self.name,
@@ -232,6 +241,7 @@ class BaseScanner:
         parse_warnings: list[str] | None = None,
         stderr: bytes | str | None = None,
     ) -> ScanResult:
+        """実行に成功したという結果を作る. 候補が 0 件でも ok."""
         stderr_text = excerpt(stderr) if isinstance(stderr, bytes) else stderr
         return ScanResult(
             scanner=self.name,
@@ -248,6 +258,7 @@ class BaseScanner:
 
 
 def elapsed_ms(started: float) -> int:
+    """`time.monotonic()` で取った開始時刻からの経過時間 (ミリ秒)."""
     return int((time.monotonic() - started) * 1000)
`````

[Back to the shelf](README.md)
