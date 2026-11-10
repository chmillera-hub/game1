# Fix 222: security-checker: public names in eval/dataset.py have no docstring (negatives and positives)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(eval): dataset.py の公開クラス・メソッド 2 個に docstring が無い
- Bug report: number 393 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/393))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/222-security-checker-393.patch](fixes/222-security-checker-393.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/222-security-checker-393.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-222-security-checker-393.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-222-security-checker-393.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/eval/dataset.py: negatives and positives. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/eval/dataset.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/eval/dataset.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 222-security-checker-393.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 393.

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

security-checker docstring D1 ruff missing docstring dataset.py negatives and positives

## The full patch

`````diff
diff --git a/src/security_checker/eval/dataset.py b/src/security_checker/eval/dataset.py
index afc618b..c6ae656 100644
--- a/src/security_checker/eval/dataset.py
+++ b/src/security_checker/eval/dataset.py
@@ -90,10 +90,12 @@ class Dataset(BaseModel):
 
     @property
     def positives(self) -> int:
+        """正解が「脆弱」のケースの数."""
         return sum(1 for case in self.cases if case.ground_truth.vulnerable)
 
     @property
     def negatives(self) -> int:
+        """正解が「脆弱ではない」のケースの数."""
         return len(self.cases) - self.positives
`````

[Back to the shelf](README.md)
