# Fix 36: Archy: the tree-sitter version floor admits versions that lack QueryCursor so every command crashes at import

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: chore(deps): `tree-sitter>=0.23` admits versions without `QueryCursor`, so every command crashes at import on tree-sitter 0.23/0.24
- Bug report: number 764 ([open the bug report](https://github.com/hslee16/Archy/issues/764))
- Project license: MIT
- Language: TOML (packaging)
- Test included: no
- Patch file: [fixes/36-archy-764.patch](fixes/36-archy-764.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/36-archy-764.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-36-archy-764.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-36-archy-764.html

## The bug

pyproject.toml allowed tree-sitter 0.23 and 0.24. The parser imports QueryCursor which tree-sitter added in 0.25. With an older tree-sitter already installed every archy command and the MCP server stopped with an ImportError.

## The fix

pyproject.toml now requires tree-sitter>=0.25. The matching specifier line in uv.lock is changed by hand to >=0.25. The locked version stays 0.25.2.

## Files changed

- pyproject.toml
- uv.lock

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 36-archy-764.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 764.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- No test is included. The bug report says a unit test cannot see this bug and suggests an optional CI job which is not part of this fix. The bug report asks for a re-lock. The chatbot edited the one specifier line in uv.lock by hand and did not run uv lock. Anyone who sends this fix should run uv lock and confirm nothing else changes. The chatbot read the tree-sitter 0.24.0 and 0.25.0 source packages and confirmed QueryCursor is missing from 0.24.0 and present in 0.25.0.

## Search words

Archy tree-sitter>=0.23 QueryCursor ImportError cannot import name floor 0.25 pyproject.toml uv.lock dependency

## The full patch

`````diff
diff --git a/pyproject.toml b/pyproject.toml
index 7347bb9..cab7084 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -19,7 +19,7 @@ classifiers = [
     "Topic :: Software Development :: Quality Assurance",
 ]
 dependencies = [
-    "tree-sitter>=0.23",
+    "tree-sitter>=0.25",
     "tree-sitter-python>=0.23",
     "networkx>=3.2",
     "pyyaml>=6.0",
diff --git a/uv.lock b/uv.lock
index 758d8ef..199e544 100644
--- a/uv.lock
+++ b/uv.lock
@@ -85,7 +85,7 @@ requires-dist = [
     { name = "pyyaml", specifier = ">=6.0" },
     { name = "tomli", marker = "python_full_version < '3.11'", specifier = ">=2.0" },
     { name = "tomli-w", specifier = ">=1.0" },
-    { name = "tree-sitter", specifier = ">=0.23" },
+    { name = "tree-sitter", specifier = ">=0.25" },
     { name = "tree-sitter-python", specifier = ">=0.23" },
     { name = "watchdog", specifier = ">=4.0" },
 ]
`````

[Back to the shelf](README.md)
