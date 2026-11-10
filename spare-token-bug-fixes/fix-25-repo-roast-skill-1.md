# Fix 25: repo-roast-skill: the Bailiff cannot parse cited paths that contain spaces

Status: UNSENT and UNTESTED. Free to take.

- Project: vivekbhange-hub/repo-roast-skill
- Bug report title: Bailiff can't parse cited paths that contain spaces
- Bug report: number 1 ([open the bug report](https://github.com/vivekbhange-hub/repo-roast-skill/issues/1))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/25-repo-roast-skill-1.patch](fixes/25-repo-roast-skill-1.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/25-repo-roast-skill-1.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-25-repo-roast-skill-1.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-25-repo-roast-skill-1.html

## The bug

verdict.py matches evidence such as docs/My Guide.md:12 with a pattern that stops at whitespace. A citation of a real file and line is thrown out as having no evidence when the path contains a space.

## The fix

skills/roast-repo/verdict.py gains a second pattern for a citation wrapped whole in backticks. Inside backticks the path may contain spaces. Citations without backticks behave as before. The existing check that keeps paths inside the repository still applies. A new test covers paths with spaces and ranges and missing files and paths outside the repository. The chatbot checked both patterns with a separate script on ten phrases.

## Files changed

- skills/roast-repo/verdict.py
- tests/test_verdict.py

## How to use the fix

1. Get a copy of the project vivekbhange-hub/repo-roast-skill.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 25-repo-roast-skill-1.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A path with spaces is accepted only when the whole citation is wrapped in backticks. The bug report named that as the minimum.

## Search words

repo-roast-skill verdict.py Bailiff LOCATION regex path with spaces evidence path:line backticks

## The full patch

`````diff
diff --git a/skills/roast-repo/verdict.py b/skills/roast-repo/verdict.py
index 76c4fc2..41ac83f 100644
--- a/skills/roast-repo/verdict.py
+++ b/skills/roast-repo/verdict.py
@@ -48,6 +48,9 @@ DEFAULT_HEADLINES = {
 }
 
 LOCATION = re.compile(r"(?<![\w/\\.-])([\w.\-][\w.\-/\\]*?):(\d+)(?:-(\d+))?\b")
+# A citation wrapped whole in backticks, e.g. `docs/My Guide.md:12`. The backticks mark
+# where the path starts and ends, so here it may contain spaces (LOCATION stops at them).
+QUOTED_LOCATION = re.compile(r"`\s*([^`\n]+?):(\d+)(?:-(\d+))?\s*`")
 
 
 def tier(score: float) -> str:
@@ -108,13 +111,15 @@ class Bailiff:
             if self.facts is None:
                 return None
             return None if lookup_fact(self.facts, key) else f"facts key '{key}' does not exist"
-        matches = list(LOCATION.finditer(ev.replace("`", " ")))
+        matches = list(QUOTED_LOCATION.finditer(ev))
+        unquoted = QUOTED_LOCATION.sub(" ", ev)
+        matches += list(LOCATION.finditer(unquoted.replace("`", " ")))
         if not matches:
             return "evidence must be path:line, '$ command -> output' or 'facts.<key>'"
         if self.repo is None:
             return None
         for m in matches:
-            rel = m.group(1).replace("\\", "/")
+            rel = m.group(1).strip().replace("\\", "/")
             while rel.startswith("./"):
                 rel = rel[2:]
             line = int(m.group(2))
diff --git a/tests/test_verdict.py b/tests/test_verdict.py
index 99fe638..0b2e7c7 100644
--- a/tests/test_verdict.py
+++ b/tests/test_verdict.py
@@ -43,6 +43,18 @@ class BailiffTests(RepoCase):
         self.assertIsNone(self.bailiff.check("`src/db.py:50` builds SQL"))
         self.assertIsNone(self.bailiff.check("./app.py:1"))
 
+    def test_accepts_backticked_path_with_spaces(self):
+        (self.repo / "docs").mkdir()
+        (self.repo / "docs" / "My Guide.md").write_text("line\n" * 12, encoding="utf-8")
+        self.assertIsNone(self.bailiff.check("`docs/My Guide.md:12`"))
+        self.assertIsNone(self.bailiff.check("see `docs/My Guide.md:3-5` for the steps"))
+        self.assertIsNone(self.bailiff.check("`docs/My Guide.md:1` and `app.py:3`"))
+        self.assertIn("out of range", self.bailiff.check("`docs/My Guide.md:13`"))
+        self.assertIn("not found", self.bailiff.check("`docs/No Such Guide.md:1`"))
+        # A path outside the repo stays inadmissible however it is quoted.
+        self.assertIsNotNone(self.bailiff.check("`../outside dir/file.py:1`"))
+        self.assertIsNotNone(self.bailiff.check("`/etc/passwd:1`"))
+
     def test_rejects_missing_file(self):
         self.assertIn("not found", self.bailiff.check("nope.py:1"))
`````

[Back to the shelf](README.md)
