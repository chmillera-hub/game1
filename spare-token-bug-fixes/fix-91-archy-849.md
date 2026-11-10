# Fix 91: Archy: a code comment only repeats the line below it

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: chore(graph): a comment in _qualname_for restates the line below it
- Bug report: number 849 ([open the bug report](https://github.com/hslee16/Archy/issues/849))
- Project license: MIT
- Language: Python comment
- Test included: no
- Patch file: [fixes/91-archy-849.patch](fixes/91-archy-849.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/91-archy-849.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-91-archy-849.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-91-archy-849.html

## The bug

A comment in _qualname_for said the same thing as the line of code under it and did not say why the code works that way.

## The fix

The comment in src/archy/graph_discovery.py now gives the reason in the words the bug report suggests: an empty leaf makes _qualname_under_roots return the package's own dotted name because pkg/__init__.py is the module pkg and not pkg.__init__.

## Files changed

- src/archy/graph_discovery.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 91-archy-849.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 849.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Comment only. No behaviour changes. The bug report names src/archy/graph.py and the function had moved to src/archy/graph_discovery.py by 2026-11-10. One comment under the bug report could not be read.

## Search words

archy _qualname_for comment restates code __init__.py empty leaf graph_discovery.py

## The full patch

`````diff
diff --git a/src/archy/graph_discovery.py b/src/archy/graph_discovery.py
index bdecfdc..bf6bbb3 100644
--- a/src/archy/graph_discovery.py
+++ b/src/archy/graph_discovery.py
@@ -386,6 +386,7 @@ def _holds_no_package(directory: Path | None) -> bool:
 
 def _qualname_for(py_file: Path, package_roots: list[Path]) -> str | None:
     """Dotted qualname for a ``.py`` file; delegates to ``_qualname_under_roots``."""
-    # __init__.py names the package (empty leaf); other files contribute stem.
+    # An empty leaf makes `_qualname_under_roots` return the package's own
+    # dotted name: `pkg/__init__.py` is the module `pkg`, not `pkg.__init__`.
     leaf: list[str] = [] if py_file.name == "__init__.py" else [py_file.stem]
     return _qualname_under_roots(py_file, leaf, package_roots)
`````

[Back to the shelf](README.md)
