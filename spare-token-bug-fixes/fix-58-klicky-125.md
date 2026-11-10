# Fix 58: klicky: the docs checker reports a broken link for a Markdown link in angle brackets that has spaces

Status: UNSENT and UNTESTED. Free to take.

- Project: Muneer320/klicky
- Bug report title: Handle angle-enclosed Markdown link destinations containing spaces
- Bug report: number 125 ([open the bug report](https://github.com/Muneer320/klicky/issues/125))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/58-klicky-125.patch](fixes/58-klicky-125.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/58-klicky-125.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-58-klicky-125.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-58-klicky-125.html

## The bug

The documentation checker cut a link destination at the first space. A valid link such as [Guide](<guide with spaces.md#usage>) was reported as a broken link to guide even though the file exists.

## The fix

scripts/check-docs.py gains link_destination which takes the text between < and > as the destination when the link uses angle brackets and otherwise keeps the old rule. scripts/test_check_docs.py gains tests for a destination with spaces and with a fragment and with a title and for a missing file in angle brackets and for plain links.

## Files changed

- scripts/check-docs.py
- scripts/test_check_docs.py

## How to use the fix

1. Get a copy of the project Muneer320/klicky.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 58-klicky-125.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 125.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The link pattern in the checker still stops at the first closing round bracket so a destination that holds a round bracket is still cut. The bug report asks people to comment before starting and the chatbot made no comment. Anyone who sends this fix should comment first. The chatbot checked the extraction rule with a scratch script and did not run the project's checker or tests.

## Search words

klicky check-docs.py check_markdown_links angle-enclosed destination spaces broken link CommonMark link destination

## The full patch

`````diff
diff --git a/scripts/check-docs.py b/scripts/check-docs.py
index b5ea679..1bbf67f 100755
--- a/scripts/check-docs.py
+++ b/scripts/check-docs.py
@@ -34,11 +34,26 @@ def check_em_dashes(errors: list[str]) -> None:
             errors.append(f"em dash: {path.relative_to(ROOT)}")
 
 
+def link_destination(raw_target: str) -> str:
+    """The destination of a link, without its optional title.
+
+    CommonMark lets a destination sit between `<` and `>`, and only that form
+    may hold spaces: `[Guide](<guide with spaces.md#usage> "Title")`.
+    """
+    raw = raw_target.strip()
+    if raw.startswith("<"):
+        end = raw.find(">", 1)
+        if end != -1:
+            return raw[1:end]
+    parts = raw.split()
+    return parts[0].strip("<>") if parts else ""
+
+
 def check_markdown_links(errors: list[str]) -> None:
     for path in repository_files("*.md"):
         text = path.read_text(encoding="utf-8")
         for raw_target in MARKDOWN_LINK.findall(text):
-            target = raw_target.split()[0].strip("<>")
+            target = link_destination(raw_target)
             if target.startswith(("http://", "https://", "mailto:", "#")):
                 continue
             target = target.split("#", 1)[0]
diff --git a/scripts/test_check_docs.py b/scripts/test_check_docs.py
index 2dc89d6..0857875 100644
--- a/scripts/test_check_docs.py
+++ b/scripts/test_check_docs.py
@@ -60,6 +60,26 @@ class MarkdownLinkTests(unittest.TestCase):
             "[Section](#usage)\n[Site](https://example.com/missing.md)")
         self.assertEqual(errors, [])
 
+    def test_angle_enclosed_destination_with_spaces_resolves(self):
+        self.write("guide with spaces.md")
+        self.assertEqual(self.errors_for("[Guide](<guide with spaces.md>)"), [])
+        self.assertEqual(self.errors_for("[Guide](<guide with spaces.md#usage>)"), [])
+
+    def test_angle_enclosed_destination_with_a_title_resolves(self):
+        self.write("guide with spaces.md")
+        errors = self.errors_for('[Guide](<guide with spaces.md#usage> "The guide")')
+        self.assertEqual(errors, [])
+
+    def test_missing_angle_enclosed_file_is_reported_by_its_whole_name(self):
+        errors = self.errors_for("[Gone](<gone with spaces.md>)")
+        self.assertEqual(len(errors), 1)
+        self.assertIn("gone with spaces.md", errors[0])
+
+    def test_plain_destination_with_a_title_is_unchanged(self):
+        self.write("guide.md")
+        self.assertEqual(self.errors_for('[Guide](guide.md "The guide")'), [])
+        self.assertEqual(self.errors_for("[Guide](<guide.md>)"), [])
+
     def test_missing_file_is_still_reported(self):
         errors = self.errors_for("[Gone](gone.md)")
         self.assertEqual(len(errors), 1)
`````

[Back to the shelf](README.md)
