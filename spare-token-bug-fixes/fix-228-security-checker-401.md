# Fix 228: security-checker: public names in observability/estimate.py have no docstring (Estimate and ReviewerEstimate and total_input_tokens and total_usd)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(observability): estimate.py の公開クラス・メソッド 4 個に docstring が無い
- Bug report: number 401 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/401))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/228-security-checker-401.patch](fixes/228-security-checker-401.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/228-security-checker-401.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-228-security-checker-401.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-228-security-checker-401.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/observability/estimate.py: Estimate and ReviewerEstimate and total_input_tokens and total_usd. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/observability/estimate.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/observability/estimate.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 228-security-checker-401.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 401.

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

security-checker docstring D1 ruff missing docstring estimate.py Estimate and ReviewerEstimate and total_input_tokens and total_usd

## The full patch

`````diff
diff --git a/src/security_checker/observability/estimate.py b/src/security_checker/observability/estimate.py
index e0100c7..bcb593f 100644
--- a/src/security_checker/observability/estimate.py
+++ b/src/security_checker/observability/estimate.py
@@ -24,6 +24,8 @@ from security_checker.review.structured import verdict_schema
 
 @dataclass
 class ReviewerEstimate:
+    """Reviewer 1 つ分の見積り. `usd` が None なら価格が分からない."""
+
     name: str
     calls: int
     input_tokens: int
@@ -34,17 +36,21 @@ class ReviewerEstimate:
 
 @dataclass
 class Estimate:
+    """review 全体の見積り. 候補の数と Reviewer ごとの内訳."""
+
     tasks: int
     reviewers: list[ReviewerEstimate] = field(default_factory=list)
 
     @property
     def total_usd(self) -> float | None:
+        """全 Reviewer の合計 (USD). 価格の分からない Reviewer が 1 つでもあれば None."""
         if any(r.usd is None for r in self.reviewers):
             return None
         return sum(r.usd or 0.0 for r in self.reviewers)
 
     @property
     def total_input_tokens(self) -> int:
+        """全 Reviewer の入力トークン数の合計."""
         return sum(r.input_tokens for r in self.reviewers)
`````

[Back to the shelf](README.md)
