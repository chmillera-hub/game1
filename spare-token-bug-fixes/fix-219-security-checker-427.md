# Fix 219: security-checker: public names in scanners/untrusted.py have no docstring (gitleaks_args and osv_args and semgrep_args and trivy_args)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(scanners): untrusted.py の公開クラス・メソッド 4 個に docstring が無い
- Bug report: number 427 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/427))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/219-security-checker-427.patch](fixes/219-security-checker-427.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/219-security-checker-427.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-219-security-checker-427.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-219-security-checker-427.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/scanners/untrusted.py: gitleaks_args and osv_args and semgrep_args and trivy_args. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/scanners/untrusted.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/scanners/untrusted.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 219-security-checker-427.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 427.

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

security-checker docstring D1 ruff missing docstring untrusted.py gitleaks_args and osv_args and semgrep_args and trivy_args

## The full patch

`````diff
diff --git a/src/security_checker/scanners/untrusted.py b/src/security_checker/scanners/untrusted.py
index 21acf27..631319a 100644
--- a/src/security_checker/scanners/untrusted.py
+++ b/src/security_checker/scanners/untrusted.py
@@ -39,6 +39,10 @@ class UntrustedOverrides:
     osv_config: Path
 
     def gitleaks_args(self) -> list[str]:
+        """gitleaks に渡す引数.
+
+        検査対象の .gitleaks.toml・.gitleaksignore・行内の allow 注釈を読ませない。
+        """
         return [
             "--config",
             str(self.gitleaks_config),
@@ -48,13 +52,16 @@ class UntrustedOverrides:
         ]
 
     def semgrep_args(self) -> list[str]:
+        """semgrep に渡す引数. 検査対象のコードにある nosemgrep 注釈を無効にする."""
         return ["--disable-nosem"]
 
     def trivy_args(self) -> list[str]:
+        """trivy に渡す引数. 検査対象の trivy.yaml と .trivyignore を読ませない."""
         # 空文字列は「読み込まない」(trivy の公式の指定方法)
         return ["--config", str(self.trivy_config), "--ignorefile", ""]
 
     def osv_args(self) -> list[str]:
+        """osv-scanner に渡す引数. 検査対象の osv-scanner.toml を読ませない."""
         return ["--config", str(self.osv_config)]
`````

[Back to the shelf](README.md)
