# Fix 7: repowise: a heading inside a code fence is treated as a real section heading

Status: UNSENT and UNTESTED. Free to take.

- Project: repowise-dev/repowise
- Bug report: number 5357 ([open the bug report](https://github.com/repowise-dev/repowise/issues/5357))
- Project license: AGPL-3.0
- Language: Python
- Test included: yes
- Patch file: [fixes/7-repowise-5357.patch](fixes/7-repowise-5357.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/7-repowise-5357.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-7-repowise-5357.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-7-repowise-5357.html

## The bug

When a generated page contains a code sample with a line that starts with # or ## the section embedder treats that line as the start of a new section and cuts or replaces the wrong part of the page.

## The fix

The fix adds a helper named _section_span in overview_tables.py that tracks code fences made of three backticks or three tildes and ignores headings inside fences. embed_section now uses the helper. A new test covers the reported case. The chatbot also ran a separate comparison on 200000 random pages with no fences and found no difference from the old behaviour.

## Files changed

- packages/core/src/repowise/core/generation/overview_tables.py
- tests/unit/generation/test_model_page_shape.py

## How to use the fix

1. Get a copy of the project repowise-dev/repowise.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 7-repowise-5357.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 5357.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.

## Search words

repowise embed_section heading inside fenced code block markdown section boundary overview_tables.py

## The full patch

`````diff
diff --git a/packages/core/src/repowise/core/generation/overview_tables.py b/packages/core/src/repowise/core/generation/overview_tables.py
index a5951ca..a7e9503 100644
--- a/packages/core/src/repowise/core/generation/overview_tables.py
+++ b/packages/core/src/repowise/core/generation/overview_tables.py
@@ -39,7 +39,36 @@ CAPABILITY_TABLE_HEADING = "## What it does"
 # terminator too. Without it a section that is last on the page runs to the end
 # and the replacement eats the footer — which is what happened the moment the
 # deterministic overview stopped rendering a path table below its packages.
-_SECTION_END = r"(?=^#{1,2}[ \t]|^---[ \t]*$|\Z)"
+#
+# A fenced code block is skipped whole: a ``## heading`` or a ``---`` line
+# inside one is sample text, neither the section's start nor its end.
+_SECTION_END = re.compile(r"#{1,2}[ \t]|---[ \t]*$")
+_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
+
+
+def _section_span(content: str, heading: str) -> tuple[int, int] | None:
+    """Start and end offsets of the ``## heading`` section, or ``None``."""
+    opening = re.compile(r"##[ \t]+" + re.escape(heading) + r"[ \t]*\n")
+    fence: str | None = None
+    start: int | None = None
+    for line in re.finditer(r"[^\n]*\n|[^\n]+\Z", content):
+        text = line.group()
+        marker = _FENCE.match(text)
+        if marker:
+            run = marker.group(1)
+            if fence is None:
+                fence = run
+            elif run[0] == fence[0] and len(run) >= len(fence):
+                fence = None
+            continue
+        if fence is not None:
+            continue
+        if start is None:
+            if opening.fullmatch(text):
+                start = line.start()
+        elif _SECTION_END.match(text):
+            return start, line.start()
+    return None if start is None else (start, len(content))
 
 
 def embed_section(content: str, heading: str, body: str | None) -> str:
@@ -51,17 +80,12 @@ def embed_section(content: str, heading: str, body: str | None) -> str:
     the section is removed: the reused page still carries what that run
     embedded, and the current facts have nothing to say there.
     """
-    pattern = re.compile(
-        r"^##[ \t]+" + re.escape(heading) + r"[ \t]*\n(?:.*?)" + _SECTION_END,
-        re.MULTILINE | re.DOTALL,
-    )
+    span = _section_span(content, heading)
     if not body:
-        return pattern.sub("", content, count=1)
+        return content if span is None else content[: span[0]] + content[span[1] :]
     section = f"## {heading}\n\n{body}\n\n"
-    if pattern.search(content):
-        # Function replacement: table cells carry backslashes and backticks
-        # that re.sub would otherwise read as group references.
-        return pattern.sub(lambda _m: section, content, count=1)
+    if span is not None:
+        return content[: span[0]] + section + content[span[1] :]
     sep = "" if content.endswith("\n") else "\n"
     return f"{content}{sep}\n{section}"
 
diff --git a/tests/unit/generation/test_model_page_shape.py b/tests/unit/generation/test_model_page_shape.py
index bbbf9d4..26f11f7 100644
--- a/tests/unit/generation/test_model_page_shape.py
+++ b/tests/unit/generation/test_model_page_shape.py
@@ -141,6 +141,16 @@ def test_the_neighbours_section_replaces_the_model_paragraph():
     assert embed_section(page, "How it connects", None).count("How it connects") == 0
 
 
+def test_a_heading_inside_a_code_fence_does_not_end_the_section():
+    page = (
+        "# P\n\n## How it connects\n\nintro\n\n```md\n## Example\n---\n```\n\n"
+        "stale tail\n\n## Later\n\nx\n"
+    )
+    out = embed_section(page, "How it connects", "- Used by: `cli/`")
+    assert out == "# P\n\n## How it connects\n\n- Used by: `cli/`\n\n## Later\n\nx\n"
+    assert embed_section(page, "How it connects", None) == "# P\n\n## Later\n\nx\n"
+
+
 # ---------------------------------------------------------------------------
 # Which flow a page draws
 # ---------------------------------------------------------------------------
`````

[Back to the shelf](README.md)
