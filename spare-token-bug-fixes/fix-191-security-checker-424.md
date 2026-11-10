# Fix 191: security-checker: public names in osv.py have no docstring (__init__ and scan)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(scanners): osv.py の公開クラス・メソッド 2 個に docstring が無い
- Bug report: number 424 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/424))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/191-security-checker-424.patch](fixes/191-security-checker-424.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/191-security-checker-424.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-191-security-checker-424.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-191-security-checker-424.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/scanners/osv.py: __init__ and scan. A person who writes a plugin cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/scanners/osv.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/scanners/osv.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 191-security-checker-424.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 424.

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

security-checker docstring D1 ruff missing docstring osv.py __init__ and scan

## The full patch

`````diff
diff --git a/src/security_checker/scanners/osv.py b/src/security_checker/scanners/osv.py
index e1f2901..84d06e9 100644
--- a/src/security_checker/scanners/osv.py
+++ b/src/security_checker/scanners/osv.py
@@ -182,9 +182,14 @@ class OsvScanner(BaseScanner):
     settings: OsvConfig
 
     def __init__(self, settings: OsvConfig) -> None:
+        """設定 (`scanners.osv`) を受け取る. 実行はしない."""
         super().__init__(settings)
 
     async def scan(self, target: Target, ctx: ScanContext) -> ScanResult:
+        """osv-scanner を実行し、依存パッケージの脆弱性を Candidate に正規化して返す.
+
+        osv-scanner が未導入なら skipped、実行に失敗すれば failed を返す (例外にはしない)。
+        """
         status = self.probe()
         if not status.available:
             return self.skipped(status.reason or "osv-scanner が利用できません")
`````

[Back to the shelf](README.md)
