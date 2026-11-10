# Fix 269: security-checker: public names in testing/scanner_contract.py have no docstring (make_scanner and test_candidates_are_well_formed and test_identity and test_ids_are_stable_across_runs and test_probe_does_not_raise and test_status_is_explicit)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(testing): scanner_contract.py の公開クラス・メソッド 6 個に docstring が無い
- Bug report: number 431 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/431))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/269-security-checker-431.patch](fixes/269-security-checker-431.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/269-security-checker-431.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-269-security-checker-431.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-269-security-checker-431.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/testing/scanner_contract.py: make_scanner and test_candidates_are_well_formed and test_identity and test_ids_are_stable_across_runs and test_probe_does_not_raise and test_status_is_explicit. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/testing/scanner_contract.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/testing/scanner_contract.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 269-security-checker-431.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 431.

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

security-checker docstring D1 ruff missing docstring scanner_contract.py make_scanner and test_candidates_are_well_formed and test_identity and test_ids_are_stable_across_runs and test_probe_does_not_raise and test_status_is_explicit

## The full patch

`````diff
diff --git a/src/security_checker/testing/scanner_contract.py b/src/security_checker/testing/scanner_contract.py
index 1225faf..1c48722 100644
--- a/src/security_checker/testing/scanner_contract.py
+++ b/src/security_checker/testing/scanner_contract.py
@@ -35,6 +35,7 @@ class ScannerContractTests:
     """すべての Scanner が満たすべき契約."""
 
     def make_scanner(self) -> Scanner:  # pragma: no cover - サブクラスが実装する
+        """検証する Scanner を作る."""
         raise NotImplementedError
 
     def populate(self, root: Path) -> None:
@@ -51,15 +52,18 @@ class ScannerContractTests:
         return result, root, raw
 
     def test_identity(self) -> None:
+        """name と category を持つこと."""
         scanner = self.make_scanner()
         assert isinstance(scanner.name, str) and scanner.name
         assert isinstance(scanner.category, Category)
 
     def test_probe_does_not_raise(self) -> None:
+        """probe が例外を投げず、ToolStatus を返すこと."""
         assert isinstance(self.make_scanner().probe(), ToolStatus)
 
     @pytest.mark.asyncio
     async def test_status_is_explicit(self, tmp_path: Path) -> None:
+        """結果の status が明示され、ツールが無ければ skipped になること."""
         scanner = self.make_scanner()
         result, _, _ = await self._scan(tmp_path)
         assert isinstance(result, ScanResult)
@@ -77,6 +81,7 @@ class ScannerContractTests:
 
     @pytest.mark.asyncio
     async def test_candidates_are_well_formed(self, tmp_path: Path) -> None:
+        """候補の ID が run 内で重複せず、各項目が契約どおりの形であること."""
         scanner = self.make_scanner()
         result, root, raw = await self._scan(tmp_path)
         ids = [candidate.id for candidate in result.candidates]
@@ -95,6 +100,7 @@ class ScannerContractTests:
 
     @pytest.mark.asyncio
     async def test_ids_are_stable_across_runs(self, tmp_path: Path) -> None:
+        """同じ入力なら、実行をまたいで候補の ID が変わらないこと."""
         first, _, _ = await self._scan(tmp_path, "first")
         second, _, _ = await self._scan(tmp_path, "second")
         assert [c.id for c in first.candidates] == [c.id for c in second.candidates], (
`````

[Back to the shelf](README.md)
