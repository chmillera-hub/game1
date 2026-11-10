# Fix 223: security-checker: public names in models/candidate.py have no docstring (__init__ and as_key and make)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(models): candidate.py の公開クラス・メソッド 3 個に docstring が無い
- Bug report: number 397 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/397))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/223-security-checker-397.patch](fixes/223-security-checker-397.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/223-security-checker-397.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-223-security-checker-397.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-223-security-checker-397.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/models/candidate.py: __init__ and as_key and make. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/models/candidate.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/models/candidate.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 223-security-checker-397.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 397.

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

security-checker docstring D1 ruff missing docstring candidate.py __init__ and as_key and make

## The full patch

`````diff
diff --git a/src/security_checker/models/candidate.py b/src/security_checker/models/candidate.py
index 14be518..fe47edc 100644
--- a/src/security_checker/models/candidate.py
+++ b/src/security_checker/models/candidate.py
@@ -50,6 +50,7 @@ class PackageRef(BaseModel):
     manifest: str | None = None
 
     def as_key(self) -> str:
+        """`ecosystem:name@version` の形の表記. 版が無ければ `*`."""
         return f"{self.ecosystem}:{self.name}@{self.version or '*'}"
 
 
@@ -114,9 +115,11 @@ class IdFactory:
     """同一 (scanner, rule_id, path, snippet) の重複に出現順の連番を振る (設計書 §6.1)."""
 
     def __init__(self) -> None:
+        """出現回数の記録を空で始める. 1 回のスキャン結果ごとに 1 つ作る."""
         self._seen: dict[tuple[str, str, str, str], int] = {}
 
     def make(self, scanner: str, rule_id: str, path: str, fingerprint_source: str) -> str:
+        """候補の安定 ID を作る. 同じ内容の 2 つ目以降には出現順の連番が入り、別の ID になる."""
         key = (scanner, rule_id, path, normalize_snippet(fingerprint_source))
         occurrence = self._seen.get(key, 0)
         self._seen[key] = occurrence + 1
`````

[Back to the shelf](README.md)
