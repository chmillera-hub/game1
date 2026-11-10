# Fix 122: Archy: writing a header into a file with no docstring pushes the shebang line and the coding line down

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: fix(conventions): `--emit-headers --write` puts the new docstring above a shebang and coding cookie, disabling both
- Bug report: number 784 ([open the bug report](https://github.com/hslee16/Archy/issues/784))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/122-archy-784.patch](fixes/122-archy-784.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/122-archy-784.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-122-archy-784.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-122-archy-784.html

## The bug

archy conventions --emit-headers --write put the new docstring at the very top of a file that had no docstring. A line that starts with #! only works as line 1 and a coding line only works on line 1 or 2. After the write the script no longer started with its shebang line and the coding line was ignored.

## The fix

apply_header in src/archy/headers.py now keeps a leading #! line and a coding line where they are and places the new docstring right below them. Two tests in tests/test_headers.py check a file with both lines and a file with only the #! line.

## Files changed

- src/archy/headers.py
- tests/test_headers.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 122-archy-784.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 784.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The fix does the minimum the bug report names: only a #! line and a coding line stay on top. Other leading comment lines (a license comment for example) still end up below the new docstring. The chatbot ran a scratch copy of the new logic on five small inputs. The chatbot did not run the project's tests. The older Archy patches on the shelf were not re-checked against the newest Archy code.

## Search words

Archy conventions emit-headers write apply_header shebang coding cookie PEP 263 docstring byte 0 headers.py

## The full patch

`````diff
diff --git a/src/archy/headers.py b/src/archy/headers.py
index faba319..3d7bf65 100644
--- a/src/archy/headers.py
+++ b/src/archy/headers.py
@@ -37,6 +37,7 @@ from __future__ import annotations
 
 import ast
 import io
+import re
 import tokenize
 from collections.abc import Iterable
 from pathlib import Path
@@ -277,6 +278,22 @@ def split_block(doc: str) -> tuple[list[str], list[str]]:
     return block, prose
 
 
+_CODING_COOKIE = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*[-\w.]+")
+
+
+def _shebang_and_cookie_end(source: str) -> int:
+    """The offset just past a leading `#!` line and a coding cookie on line 1 or 2."""
+    lines = source.splitlines(keepends=True)
+    end = 0
+    index = 0
+    if lines and lines[0].startswith("#!"):
+        end += len(lines[0])
+        index = 1
+    if index < len(lines) and _CODING_COOKIE.match(lines[index]):
+        end += len(lines[index])
+    return end
+
+
 def apply_header(source: str, block: str) -> str:
     """Put `block` at the end of the module docstring, replacing any block already there.
 
@@ -289,7 +306,15 @@ def apply_header(source: str, block: str) -> str:
     if span is None:
         # Nothing to preserve here by construction, so the block can be the
         # whole docstring rather than being merged into one.
-        return f'"""{block}\n"""\n\n{source}' if source.strip() else f'"""{block}\n"""\n'
+        if not source.strip():
+            return f'"""{block}\n"""\n'
+        # A shebang only works on line 1 and a PEP 263 coding cookie only on
+        # line 1 or 2, so the docstring goes below them rather than at byte 0.
+        keep = _shebang_and_cookie_end(source)
+        head = source[:keep]
+        if head and not head.endswith("\n"):
+            head += "\n"
+        return f'{head}"""{block}\n"""\n\n{source[keep:]}'
 
     doc = source[span[0] : span[1]]
     quote = '"""' if '"""' in doc else "'''"
diff --git a/tests/test_headers.py b/tests/test_headers.py
index 8ca1317..ddc1ce8 100644
--- a/tests/test_headers.py
+++ b/tests/test_headers.py
@@ -8,6 +8,7 @@ wrote, which is the part archy cannot derive.
 
 from __future__ import annotations
 
+import ast
 from pathlib import Path
 
 from click.testing import CliRunner
@@ -250,6 +251,28 @@ def test_apply_header_gives_a_docstring_to_a_module_without_one(tmp_path: Path):
     assert "import sys" in out
 
 
+def test_apply_header_keeps_a_shebang_and_coding_cookie_on_their_lines():
+    source = (
+        "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\nimport os\n\n\ndef shebang_fn():\n    return os\n"
+    )
+    assert ast.get_docstring(ast.parse(source)) is None
+
+    out = apply_header(source, "archy:owns        shebang_fn")
+    lines = out.splitlines()
+
+    assert lines[0] == "#!/usr/bin/env python"
+    assert lines[1] == "# -*- coding: utf-8 -*-"
+    assert ast.get_docstring(ast.parse(out)) == "archy:owns        shebang_fn"
+    assert "import os" in out
+
+
+def test_apply_header_keeps_a_lone_shebang_on_line_one():
+    out = apply_header("#!/usr/bin/env python\nimport os\n", "archy:owns        f")
+
+    assert out.splitlines()[0] == "#!/usr/bin/env python"
+    assert existing_block(out) == "archy:owns        f"
+
+
 def test_render_wraps_long_lists_under_the_value_column(tmp_path: Path):
     root = _project(tmp_path)
     header = next(h for h in _headers(root) if h.module == "myapp.core.rules")
`````

[Back to the shelf](README.md)
