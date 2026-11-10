# Fix 124: Archy: the external edge count of the graph summary and the call statistics of the score have no test

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: test(mcp,score): `external_edge_count`, the score call statistics and the MCP duplicates "nothing found" note can be wrong with the suite green
- Bug report: number 807 ([open the bug report](https://github.com/hslee16/Archy/issues/807))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/124-archy-807.patch](fixes/124-archy-807.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/124-archy-807.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-124-archy-807.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-124-archy-807.html

## The bug

Nothing in the tests checked external_edge_count in the archy_graph summary or the three numbers from _call_stats in the score. Either value could be computed wrongly with every test green.

## The fix

Tests only. A new file tests/test_summary_counts_pinned.py builds the three-module example from the bug report and expects two internal edges and one external edge. A second test gives _call_stats a graph with a zero-call edge and expects (2 and 5 and 2.5).

## Files changed

- tests/test_summary_counts_pinned.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 124-archy-807.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 807.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report lists a third gap (the nothing found note of archy_duplicates on the MCP side). A test for that note already exists in tests/test_mcp_git.py in the newest code so the patch leaves that part out. The chatbot did not run the tests.

## Search words

Archy external_edge_count run_graph_summary _call_stats call_edge_count calls_per_edge total_calls unpinned mutation test

## The full patch

`````diff
diff --git a/tests/test_summary_counts_pinned.py b/tests/test_summary_counts_pinned.py
new file mode 100644
index 0000000..b7d3266
--- /dev/null
+++ b/tests/test_summary_counts_pinned.py
@@ -0,0 +1,36 @@
+"""Pin two counts that reach agents and users and had no assertion (#807)."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import networkx as nx
+
+from archy.mcp_runs import run_graph_summary
+from archy.score import _call_stats
+
+
+def test_graph_summary_counts_internal_and_external_edges_apart(tmp_path: Path):
+    """Three modules: a -> b and b -> c are internal; a -> os is the one external edge."""
+    pkg = tmp_path / "p"
+    pkg.mkdir()
+    (pkg / "__init__.py").write_text("")
+    (pkg / "a.py").write_text("import os\nfrom p import b\n")
+    (pkg / "b.py").write_text("from p import c\n")
+    (pkg / "c.py").write_text("")
+
+    dumped = run_graph_summary(tmp_path, top_n=3).model_dump()
+
+    assert dumped["internal_edge_count"] == 2
+    assert dumped["external_edge_count"] == 1
+
+
+def test_call_stats_averages_over_edges_that_carry_calls_only():
+    """Two edges carry calls; 2 + 3 = 5 calls; 5 / 2 = 2.5. The zero-call edge is not counted."""
+    graph = nx.DiGraph()
+    graph.add_edge("a", "b", call_count=0)
+    graph.add_edge("a", "c", call_count=2)
+    graph.add_edge("b", "c", call_count=3)
+    assert graph["a"]["b"]["call_count"] == 0
+
+    assert _call_stats(graph) == (2, 5, 2.5)
`````

[Back to the shelf](README.md)
