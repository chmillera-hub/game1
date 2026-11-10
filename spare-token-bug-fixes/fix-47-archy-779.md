# Fix 47: Archy: archy_graph accepts an invalid direction or depth or max_nodes unless the call takes the path that reads the value

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: fix(mcp): `archy_graph` accepts an invalid `direction`, `depth` or `max_nodes` unless the call happens to take the path that uses it
- Bug report: number 779 ([open the bug report](https://github.com/hslee16/Archy/issues/779))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/47-archy-779.patch](fixes/47-archy-779.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/47-archy-779.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-47-archy-779.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-47-archy-779.html

## The bug

The archy_graph tool checked direction and depth only on the focus path and max_nodes only on the full dump path. Without focus a call with direction sideways or depth -5 or max_nodes 0 returned a normal summary. The caller never learned that the argument was invalid.

## The fix

run_graph in src/archy/mcp_runs_graph.py now checks direction and depth and max_nodes and top_n at the top with the same messages the inner paths already use. tests/test_mcp_graph.py gains tests for each invalid value with and without focus and through the tool call.

## Files changed

- src/archy/mcp_runs_graph.py
- tests/test_mcp_graph.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 47-archy-779.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 779.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report says depth below 1 should be refused. The existing inner check refuses depth below 0 and the bug report also says to reuse the existing messages. The fix reuses the existing rule (depth below 0). The maintainer may want depth 0 refused too. A call with focus and max_nodes 0 was accepted before and is refused now.

## Search words

Archy archy_graph run_graph invalid direction sideways depth max_nodes top_n validation ToolError summary path focus

## The full patch

`````diff
diff --git a/src/archy/mcp_runs_graph.py b/src/archy/mcp_runs_graph.py
index 834afcd..7f3f5ce 100644
--- a/src/archy/mcp_runs_graph.py
+++ b/src/archy/mcp_runs_graph.py
@@ -311,9 +311,19 @@ def run_graph(
     apply to it. Otherwise summary is the default (top-N overview, identical to
     the old archy_graph_summary) and full is the opt-in dump, guarded by
     max_nodes. response_format is validated on every path so an invalid value
-    raises even when focus is set.
+    raises even when focus is set. direction, depth, max_nodes and top_n are too:
+    each is read by one path only, and an invalid value must be refused the same
+    way whichever path the call takes, with the message that path already uses.
     """
     _validate_response_format(response_format)
+    if direction not in ("in", "out", "both"):
+        raise ValueError(f"direction must be 'in', 'out', or 'both'; got {direction!r}")
+    if depth < 0:
+        raise ValueError(f"depth must be >= 0; got {depth}")
+    if max_nodes <= 0:
+        raise ValueError(f"max_nodes must be >= 1; got {max_nodes}")
+    if top_n <= 0:
+        raise ValueError(f"top_n must be >= 1; got {top_n}")
     if focus:
         return run_graph_focus(
             path,
diff --git a/tests/test_mcp_graph.py b/tests/test_mcp_graph.py
index a1b14ab..8408b03 100644
--- a/tests/test_mcp_graph.py
+++ b/tests/test_mcp_graph.py
@@ -423,6 +423,38 @@ def test_graph_tool_focus_still_validates_response_format(acyclic_project: Path)
         )
 
 
+_INVALID_GRAPH_ARGUMENTS = [
+    ({"direction": "sideways"}, "direction must be"),
+    ({"depth": -5}, "depth must be"),
+    ({"max_nodes": 0}, "max_nodes must be"),
+    ({"top_n": 0}, "top_n must be"),
+]
+
+
+@pytest.mark.parametrize(("bad", "message"), _INVALID_GRAPH_ARGUMENTS)
+def test_graph_refuses_an_invalid_argument_on_the_path_that_never_reads_it(
+    acyclic_project: Path, bad: dict, message: str
+):
+    """No `focus`, so the summary path is taken, which reads none of direction,
+    depth or max_nodes; with `focus`, the focus path reads neither max_nodes nor
+    top_n. The invalid value is refused either way (#779)."""
+    args = {"response_format": "summary", "internal_only": True, "max_nodes": 500, "top_n": 20}
+    with pytest.raises(ValueError, match=message):
+        run_graph(acyclic_project, **{**args, **bad})
+    with pytest.raises(ValueError, match=message):
+        run_graph(acyclic_project, focus=["pkg.a"], **{**args, **bad})
+
+
+@pytest.mark.parametrize(("bad", "message"), _INVALID_GRAPH_ARGUMENTS)
+def test_archy_graph_tool_names_the_invalid_argument(
+    acyclic_project: Path, bad: dict, message: str
+):
+    from archy.mcp_compat import ToolError
+
+    with pytest.raises(ToolError, match=message):
+        _call_tool(create_server(), "archy_graph", {"path": str(acyclic_project), **bad})
+
+
 def test_graph_focus_preserves_edge_attributes(tmp_path: Path):
     # Spec contract: agents use edge `lines` to pinpoint import sites and
     # `is_relative` to distinguish `from .x import y` from absolute imports.
`````

[Back to the shelf](README.md)
