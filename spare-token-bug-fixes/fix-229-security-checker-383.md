# Fix 229: security-checker: public names in context/builder.py have no docstring (build)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: docs(context): builder.py の公開クラス・メソッド 2 個に docstring が無い
- Bug report: number 383 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/383))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/229-security-checker-383.patch](fixes/229-security-checker-383.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/229-security-checker-383.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-229-security-checker-383.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-229-security-checker-383.html

## The bug

The lint rule D1 reports public names without a docstring in src/security_checker/context/builder.py: build. A person who writes a plugin or a contribution cannot read the meaning of the arguments from the types alone.

## The fix

Each of the named items in src/security_checker/context/builder.py gets a short Japanese docstring that says what the item does.

## Files changed

- src/security_checker/context/builder.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 229-security-checker-383.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 383.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report counts two items. The other one (__init__) already has a docstring in the newest code so the patch adds one docstring. Docstrings only with no change in behaviour. The chatbot wrote the Japanese text and a native reader should check the wording. Nobody ran the lint tool.

## Search words

security-checker docstring D1 ruff missing docstring builder.py build

## The full patch

`````diff
diff --git a/src/security_checker/context/builder.py b/src/security_checker/context/builder.py
index 5fa69f4..949eb30 100644
--- a/src/security_checker/context/builder.py
+++ b/src/security_checker/context/builder.py
@@ -52,6 +52,7 @@ class ContextBuilder:
         self.repo_facts = repo_facts if config.include_repo_facts else RepoFacts()
 
     def build(self, candidate: Candidate) -> ReviewTask:
+        """候補 1 件の ReviewTask を作る. コード本文を出せない理由や切り詰めは notes に残す."""
         notes: list[str] = []
         primary: CodeSlice | None = None
         truncated = False
`````

[Back to the shelf](README.md)
