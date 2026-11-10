# Fix 93: SMART toolkit: two architecture tests fail in a copy of the code that has no .git folder

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: tests: two architecture tests fail on a source archive without .git
- Bug report: number 84 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/84))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/93-social-messaging-agent-runtime-toolkit-84.patch](fixes/93-social-messaging-agent-runtime-toolkit-84.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/93-social-messaging-agent-runtime-toolkit-84.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-93-social-messaging-agent-runtime-toolkit-84.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-93-social-messaging-agent-runtime-toolkit-84.html

## The bug

Two tests in tests/test_architecture.py listed the shipped files with git ls-files. In a source archive with no .git folder the tests failed with CalledProcessError and on a machine with no git program the tests failed with FileNotFoundError. A third helper in the same file already had a fallback.

## The fix

tests/test_architecture.py gains _shipped_files which asks git first and otherwise walks the folders with the same skips the existing helper uses. Both tests call the new helper. A new test makes the git call fail in both ways and checks that the helper still returns the files.

## Files changed

- tests/test_architecture.py

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 93-social-messaging-agent-runtime-toolkit-84.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 84.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a scratch copy of the folder walk over a clean clone and compared the result with git ls-files: 471 files both ways with no difference. In a working folder with untracked files the walk can return more files than git does. The chatbot did not run the project's tests. Tests only so the patch adds no changelog line.

## Search words

socialagent test_architecture git ls-files CalledProcessError FileNotFoundError source archive no .git fallback _tracked_markdown

## The full patch

`````diff
diff --git a/tests/test_architecture.py b/tests/test_architecture.py
index b4fc0e8..e325d24 100644
--- a/tests/test_architecture.py
+++ b/tests/test_architecture.py
@@ -34,6 +34,7 @@ client name held in a variable.
 from __future__ import annotations
 
 import ast
+import fnmatch
 import re
 import subprocess
 from pathlib import Path
@@ -380,6 +381,55 @@ def test_layer_rules_cover_real_files():
         )
 
 
+def _shipped_files(*globs: str) -> list[str]:
+    """Repo-relative paths of shipped files whose name matches one of *globs*.
+
+    Asks git when it is available, so an untracked local directory cannot
+    fail a test. Without git (a source archive with no .git, or a CI image
+    with no git binary) it walks the tree with the same skips as
+    ``_tracked_markdown``: generated projects, build noise, and every hidden
+    directory except .github.
+    """
+    try:
+        out = subprocess.run(
+            ["git", "ls-files", "-z", "--", *globs],
+            cwd=REPO_ROOT,
+            capture_output=True,
+            check=True,
+        ).stdout.decode()
+    except (OSError, subprocess.CalledProcessError):
+        found = []
+        for path in REPO_ROOT.rglob("*"):
+            rel = path.relative_to(REPO_ROOT)
+            parts = rel.parts[:-1]
+            if _SKIP_PARTS.intersection(parts) or "projects" in parts:
+                continue
+            if any(p.startswith(".") and p != ".github" for p in parts):
+                continue
+            if path.is_file() and any(fnmatch.fnmatch(path.name, g) for g in globs):
+                found.append(rel.as_posix())
+        return sorted(found)
+    return sorted(name for name in out.split("\0") if name)
+
+
+@pytest.mark.architecture
+@pytest.mark.parametrize("failure", ["no-git-binary", "not-a-checkout"])
+def test_shipped_files_falls_back_to_walking_the_tree(monkeypatch, failure):
+    """Without git, or outside a checkout, the shipped-file tests still get a file list."""
+
+    def refuse(cmd, *args, **kwargs):
+        if failure == "no-git-binary":
+            raise FileNotFoundError("git")
+        raise subprocess.CalledProcessError(128, cmd)
+
+    monkeypatch.setattr(subprocess, "run", refuse)
+    found = _shipped_files("*.py", "*.md")
+    assert "README.md" in found
+    assert "tests/test_architecture.py" in found
+    assert all(not name.startswith(".venv/") for name in found)
+    assert all(name.endswith((".py", ".md")) for name in found)
+
+
 @pytest.mark.architecture
 def test_shipped_files_name_no_real_product_brands():
     """The demo domain is fictional: no real car model or make in shipped files.
@@ -390,31 +440,10 @@ def test_shipped_files_name_no_real_product_brands():
     from regressing. Tracked files only, so an untracked local directory
     cannot fail it; this file is the one place the names appear.
     """
-    import subprocess
-
     brands = ["Honda", "Toyota", "Tesla", "Civic", "RAV4", "Model 3", "Mazda"]
     pattern = re.compile(r"\b(" + "|".join(brands) + r")\b", re.IGNORECASE)
     here = Path(__file__).resolve()
-    tracked = (
-        subprocess.run(
-            [
-                "git",
-                "ls-files",
-                "-z",
-                "--",
-                "*.py",
-                "*.md",
-                "*.yaml",
-                "*.yml",
-                "*.json",
-            ],
-            cwd=REPO_ROOT,
-            capture_output=True,
-            check=True,
-        )
-        .stdout.decode()
-        .split("\0")
-    )
+    tracked = _shipped_files("*.py", "*.md", "*.yaml", "*.yml", "*.json")
     offenders = [
         f"{rel}:{i}"
         for rel in tracked
@@ -450,16 +479,7 @@ def test_shipped_files_carry_only_placeholder_mx_numbers():
     pattern = re.compile(r"(?<!\d)\+?(521?[2-9]\d{9})(?!\d)")
     globs = ["*.py", "*.md", "*.yaml", "*.yml", "*.json", "*.ts", "*.tsx"]
     globs += ["*.tf", "*.example", "*.sh", "*.txt"]
-    tracked = (
-        subprocess.run(
-            ["git", "ls-files", "-z", "--", *globs],
-            cwd=REPO_ROOT,
-            capture_output=True,
-            check=True,
-        )
-        .stdout.decode()
-        .split("\0")
-    )
+    tracked = _shipped_files(*globs)
     offenders = [
         f"{rel}:{i}: {number}"
         for rel in tracked
`````

[Back to the shelf](README.md)
