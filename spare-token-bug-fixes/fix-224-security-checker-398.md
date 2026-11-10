# Fix 224: security-checker: public names in models/enums.py have no docstring (__ge__ and __gt__ and __le__ and __lt__)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(models): enums.py の公開クラス・メソッド 4 個に docstring が無い
- Bug report: number 398 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/398))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/224-security-checker-398.patch](fixes/224-security-checker-398.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/224-security-checker-398.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-224-security-checker-398.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-224-security-checker-398.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/models/enums.py: __ge__ and __gt__ and __le__ and __lt__. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/models/enums.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/models/enums.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 224-security-checker-398.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 398.

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

security-checker docstring D1 ruff missing docstring enums.py __ge__ and __gt__ and __le__ and __lt__

## The full patch

`````diff
diff --git a/src/security_checker/models/enums.py b/src/security_checker/models/enums.py
index dfb5450..42df028 100644
--- a/src/security_checker/models/enums.py
+++ b/src/security_checker/models/enums.py
@@ -21,21 +21,25 @@ class Severity(StrEnum):
         return _SEVERITY_ORDER[self]
 
     def __ge__(self, other: object) -> bool:
+        """深刻さの順で比べる (文字列としての順ではない). Severity 以外とは比べない."""
         if not isinstance(other, Severity):
             return NotImplemented
         return self.order >= other.order
 
     def __gt__(self, other: object) -> bool:
+        """深刻さの順で比べる (文字列としての順ではない). Severity 以外とは比べない."""
         if not isinstance(other, Severity):
             return NotImplemented
         return self.order > other.order
 
     def __le__(self, other: object) -> bool:
+        """深刻さの順で比べる (文字列としての順ではない). Severity 以外とは比べない."""
         if not isinstance(other, Severity):
             return NotImplemented
         return self.order <= other.order
 
     def __lt__(self, other: object) -> bool:
+        """深刻さの順で比べる (文字列としての順ではない). Severity 以外とは比べない."""
         if not isinstance(other, Severity):
             return NotImplemented
         return self.order < other.order
`````

[Back to the shelf](README.md)
