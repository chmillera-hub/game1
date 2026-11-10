# Fix 181: security-checker: facts.py compares against unnamed numbers (10)

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: refactor: facts.py の collect_repo_facts にある比較用の数値 (10) を名前付き定数にする
- Bug report: number 367 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/367))
- Project license: MIT
- Language: Python
- Test included: no
- Patch file: [fixes/181-security-checker-367.patch](fixes/181-security-checker-367.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/181-security-checker-367.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-181-security-checker-367.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-181-security-checker-367.html

## The bug

src/security_checker/context/facts.py compared the number of entry points collected against bare numbers (10). The lint rule PLR2004 reports each spot because the meaning of the number cannot be read from the code.

## The fix

The comparisons now use the new constant MAX_ENTRYPOINTS.

## Files changed

- src/security_checker/context/facts.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 181-security-checker-367.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 367.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A rename of a number into a named constant with no change in behaviour. Nobody ran the lint tool or the project's tests.

## Search words

security-checker PLR2004 magic value named constant facts.py 10

## The full patch

`````diff
diff --git a/src/security_checker/context/facts.py b/src/security_checker/context/facts.py
index 1f22479..8ecf973 100644
--- a/src/security_checker/context/facts.py
+++ b/src/security_checker/context/facts.py
@@ -65,6 +65,8 @@ ENTRYPOINT_NAMES = {
 AUTH_MARKERS = ("auth", "login", "session", "jwt", "oauth", "permission")
 SKIP_DIRS = {".git", "node_modules", "vendor", "__pycache__", ".venv", "dist", "build"}
 MAX_FILES = 4000
+#: プロンプトに載せるエントリポイントの上限
+MAX_ENTRYPOINTS = 10
 
 
 def collect_repo_facts(root: Path) -> RepoFacts:
@@ -90,7 +92,7 @@ def collect_repo_facts(root: Path) -> RepoFacts:
         language = LANGUAGE_BY_SUFFIX.get(path.suffix)
         if language:
             languages[language] = languages.get(language, 0) + 1
-        if name in ENTRYPOINT_NAMES and len(entrypoints) < 10:
+        if name in ENTRYPOINT_NAMES and len(entrypoints) < MAX_ENTRYPOINTS:
             entrypoints.append(relative)
         if name in DEPLOYMENT_FILES:
             hint = DEPLOYMENT_FILES[name]
`````

[Back to the shelf](README.md)
