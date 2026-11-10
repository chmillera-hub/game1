# Fix 85: security-checker: changed files whose names hold a tab or a quote are not matched to findings

Status: UNSENT and UNTESTED. Free to take.

- Project: Sh1n1230/security-checker
- Bug report title: fix(github): diff の解析で、C 形式でエスケープされたパス (タブ・改行・引用符を含む) を元に戻していない
- Bug report: number 669 ([open the bug report](https://github.com/Sh1n1230/security-checker/issues/669))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/85-security-checker-669.patch](fixes/85-security-checker-669.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/85-security-checker-669.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-85-security-checker-669.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-85-security-checker-669.html

## The bug

git writes a file name that holds a tab or a line break or a double quote or a backslash in a quoted form with escape codes. The diff reader only removed the outer quotes and left the escape codes in place. The resulting path did not match the path of any finding so findings in such a file were treated as outside the change.

## The fix

src/security_checker/github/pr.py gains _unquote_c which turns the escape codes (letter codes and \\ and \" and octal numbers) back into the real characters. _strip_prefix calls the helper for a quoted path. A new file tests/unit/test_diff_quoted_paths.py covers six quoted names and one plain name.

## Files changed

- src/security_checker/github/pr.py
- tests/unit/test_diff_quoted_paths.py

## How to use the fix

1. Get a copy of the project Sh1n1230/security-checker.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 85-security-checker-669.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 669.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot made seven files with such names in a scratch git repository and ran a scratch copy of the rule over the real git diff output: all seven names came back correctly. An escape code the helper does not know is left as written. The chatbot did not run the project's tests.

## Search words

security-checker parse_unified_diff _strip_prefix quoted path C-style escape tab newline quote core.quotePath diff header

## The full patch

`````diff
diff --git a/src/security_checker/github/pr.py b/src/security_checker/github/pr.py
index d412df7..bc4db51 100644
--- a/src/security_checker/github/pr.py
+++ b/src/security_checker/github/pr.py
@@ -117,12 +117,52 @@ def _strip_prefix(raw: str) -> str | None:
     path = raw.split("\t", 1)[0]
     if path == "/dev/null":
         return None
-    if path.startswith('"') and path.endswith('"'):
-        # 非 ASCII パスは core.quotePath=false で避けているが、念のため引用符を外す
-        path = path[1:-1]
+    if len(path) >= 2 and path.startswith('"') and path.endswith('"'):
+        # core.quotePath=false でも、タブ・改行・`"`・`\\` を含むパスは C 形式で引用される
+        path = _unquote_c(path[1:-1])
     return path[2:] if path[:2] in ("a/", "b/") else path
 
 
+_C_ESCAPES = {
+    "a": 0x07,
+    "b": 0x08,
+    "f": 0x0C,
+    "n": 0x0A,
+    "r": 0x0D,
+    "t": 0x09,
+    "v": 0x0B,
+    "\\": 0x5C,
+    '"': 0x22,
+}
+
+
+def _unquote_c(quoted: str) -> str:
+    """git が引用したパスの中身 (両端の引用符は除く) から C 形式のエスケープを解除する."""
+    out = bytearray()
+    i = 0
+    while i < len(quoted):
+        ch = quoted[i]
+        if ch != "\\" or i + 1 >= len(quoted):
+            out += ch.encode("utf-8")
+            i += 1
+            continue
+        nxt = quoted[i + 1]
+        if nxt in _C_ESCAPES:
+            out.append(_C_ESCAPES[nxt])
+            i += 2
+        elif nxt in "01234567":
+            end = i + 1
+            while end < len(quoted) and end < i + 4 and quoted[end] in "01234567":
+                end += 1
+            out.append(int(quoted[i + 1 : end], 8) & 0xFF)
+            i = end
+        else:
+            # 知らないエスケープはそのまま残す
+            out += ch.encode("utf-8")
+            i += 1
+    return out.decode("utf-8", errors="replace")
+
+
 def _git(root: Path, *args: str) -> str:
     try:
         completed = subprocess.run(
diff --git a/tests/unit/test_diff_quoted_paths.py b/tests/unit/test_diff_quoted_paths.py
new file mode 100644
index 0000000..95240e0
--- /dev/null
+++ b/tests/unit/test_diff_quoted_paths.py
@@ -0,0 +1,34 @@
+"""diff のヘッダで C 形式に引用されたパス (タブ・改行・引用符・バックスラッシュ) を元に戻す."""
+
+from __future__ import annotations
+
+import pytest
+
+from security_checker.github.pr import parse_unified_diff
+
+
+def _diff(old: str, new: str) -> str:
+    return f"diff --git {old} {new}\n--- {old}\n+++ {new}\n@@ -0,0 +1,2 @@\n+x\n+y\n"
+
+
+@pytest.mark.parametrize(
+    ("quoted", "path"),
+    [
+        (r"foo\tbar.py", "foo\tbar.py"),
+        (r"line\nbreak.py", "line\nbreak.py"),
+        (r"say \"hi\".py", 'say "hi".py'),
+        (r"back\\slash.py", "back\\slash.py"),
+        (r"bell\007.py", "bell\x07.py"),
+        (r"caf\303\251\t.py", "café\t.py"),
+    ],
+)
+def test_quoted_header_paths_are_unescaped(quoted: str, path: str) -> None:
+    added, changed = parse_unified_diff(_diff(f'"a/{quoted}"', f'"b/{quoted}"'))
+    assert changed == {path}
+    assert added == {path: ((1, 2),)}
+
+
+def test_unquoted_paths_are_unchanged() -> None:
+    added, changed = parse_unified_diff(_diff("a/src/app.py", "b/src/app.py"))
+    assert changed == {"src/app.py"}
+    assert added == {"src/app.py": ((1, 2),)}
`````

[Back to the shelf](README.md)
