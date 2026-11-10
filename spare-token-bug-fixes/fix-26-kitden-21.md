# Fix 26: kitden: add panels show one gap too many above the hint

Status: UNSENT and UNTESTED. Free to take.

- Project: KonstantinStarovoytov/kitden
- Bug report title: Add panels: one gap too many above the hint
- Bug report: number 21 ([open the bug report](https://github.com/KonstantinStarovoytov/kitden/issues/21))
- Project license: Apache-2.0
- Language: CSS and Python (test)
- Test included: yes
- Patch file: [fixes/26-kitden-21.patch](fixes/26-kitden-21.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/26-kitden-21.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-26-kitden-21.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-26-kitden-21.html

## The bug

In the Gateway and Library add panels the closed Add a GitHub source block draws nothing but still counts as an item of the panel's column. The block adds one more 12 pixel gap above the hint line.

## The fix

src/kitden/web/static/style.css gets one rule that hides the block while the block is closed. The Sources control still opens and closes the block. A new test in tests/unit/test_page_words.py pins the rule. ROADMAP.md gets a line under Not released yet.

## Files changed

- ROADMAP.md
- src/kitden/web/static/style.css
- tests/unit/test_page_words.py

## How to use the fix

1. Get a copy of the project KonstantinStarovoytov/kitden.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 26-kitden-21.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 21.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report asks for the README picture to be made again. The chatbot could not make pictures of the page. The bug report says the maintainer will make the picture in that case.

## Search words

kitden add panel discovery-source-add details closed extra gap 12px hint Click to review drag onto style.css

## The full patch

`````diff
diff --git a/ROADMAP.md b/ROADMAP.md
index d785436..71a628d 100644
--- a/ROADMAP.md
+++ b/ROADMAP.md
@@ -19,6 +19,9 @@ What Kitden does today and what comes next. Ideas and bugs:
   servers, skills, plugins, hooks or instruction files, and for requests to turn one on or off or
   remove it. Without Kitden it shows the install line itself, after checking `kitden --version`.
   The plugin's description says it needs Kitden installed.
+- **Add panels: no extra gap above the hint:** the closed "Add a GitHub source" block no longer
+  takes space between the search row and "Click to review · drag onto …", in the MCP panel and
+  in the Library's. **Sources** opens and closes it as before.
 
 ### 0.6.5
 
diff --git a/src/kitden/web/static/style.css b/src/kitden/web/static/style.css
index b8fd2d0..52e174d 100644
--- a/src/kitden/web/static/style.css
+++ b/src/kitden/web/static/style.css
@@ -1285,6 +1285,9 @@ html.map-entrance::view-transition-new(page) { animation: none; }
 .discovery:has(.discovery-workspace) .discovery-filters { margin-bottom: 0; }
 .discovery:has(.discovery-workspace) .discovery-source-add { margin: 0; }
 .discovery-source-add > summary { display: none; }
+/* Closed, the block shows nothing (its summary is hidden), but as an item of the panel's column it
+   still took one more gap above the hint. "Sources" sets [open], which brings it back. */
+.discovery-source-add:not([open]) { display: none; }
 .discovery-source-add[open] { padding: 16px; border: 1px solid var(--wire); border-radius: 8px; }
 .discovery-results .res[aria-pressed="true"] { border-color: var(--focus); background: var(--route-soft); }
 
diff --git a/tests/unit/test_page_words.py b/tests/unit/test_page_words.py
index 8562fca..290a230 100644
--- a/tests/unit/test_page_words.py
+++ b/tests/unit/test_page_words.py
@@ -3148,6 +3148,14 @@ def test_hints_follow_one_pattern_and_refusals_are_amber():
     assert ".form-message.error { color: var(--lamp-warn); }" in css
 
 
+def test_the_closed_source_block_takes_no_space_in_the_add_panels():
+    # "Add a GitHub source" sits between the search row and the hint. Closed, it drew nothing but
+    # was still an item of the panel's column, so it added one more gap (12 px) above the hint.
+    assert "display: none" in rule(".discovery-source-add:not([open])")
+    # Open, it is drawn as before: "Sources" still opens and closes it.
+    assert "padding: 16px" in rule(".discovery-source-add[open]")
+
+
 def test_the_add_panels_client_ticks_start_at_one_edge():
     # `.checks` centres its row; in the add panel's column that put each tick at another place.
     assert "align-items: flex-start" in rule(".discovery-inspector .checks")
`````

[Back to the shelf](README.md)
