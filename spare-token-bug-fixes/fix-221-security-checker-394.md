# Fix 221: security-checker: public names in eval/metrics.py have no docstring (deferred and dismissed and errored and reported)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(eval): metrics.py の公開クラス・メソッド 4 個に docstring が無い
- Bug report: number 394 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/394))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/221-security-checker-394.patch](fixes/221-security-checker-394.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/221-security-checker-394.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-221-security-checker-394.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-221-security-checker-394.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/eval/metrics.py: deferred and dismissed and errored and reported. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/eval/metrics.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/eval/metrics.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 221-security-checker-394.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 394.

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

security-checker docstring D1 ruff missing docstring metrics.py deferred and dismissed and errored and reported

## The full patch

`````diff
diff --git a/src/security_checker/eval/metrics.py b/src/security_checker/eval/metrics.py
index 1e6b419..e41d316 100644
--- a/src/security_checker/eval/metrics.py
+++ b/src/security_checker/eval/metrics.py
@@ -53,18 +53,22 @@ class CaseOutcome(BaseModel):
 
     @property
     def reported(self) -> bool:
+        """脆弱と報告したか (confirmed / likely)."""
         return self.status in REPORTED_AS_VULNERABLE
 
     @property
     def dismissed(self) -> bool:
+        """脆弱ではないと切り捨てたか (false_positive)."""
         return self.status in DISMISSED
 
     @property
     def deferred(self) -> bool:
+        """人間に渡したか (review_required / inconclusive). 正解・不正解のどちらにも数えない."""
         return self.status in DEFERRED
 
     @property
     def errored(self) -> bool:
+        """判定がエラーで終わったか."""
         return self.status is FindingStatus.ERROR
 
     @property
`````

[Back to the shelf](README.md)
