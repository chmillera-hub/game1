# Fix 42: Archy: a module that imports itself counts as its own importer and ranks first as central and fragile

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: fix(instability,risk): a module that imports itself counts as its own importer, so an unimported module ranks #1 "central and fragile"
- Bug report: number 752 ([open the bug report](https://github.com/hslee16/Archy/issues/752))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/42-archy-752.patch](fixes/42-archy-752.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/42-archy-752.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-42-archy-752.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-42-archy-752.html

## The bug

A module that imports itself (for example inside a __main__ demo block) has a self-edge in the import graph. The self-edge was counted as one incoming and one outgoing import. A module that nobody imports got instability 0.5 and a non-zero edit risk and what-to-refactor-next ranked the module first.

## The fix

src/archy/instability.py leaves self-edges out of the incoming and outgoing counts. src/archy/risk.py and src/archy/refactor.py leave self-edges out of the fan-in count. Cycle detection is untouched and still reports the self-loop. tests/test_instability.py gains two tests and tests/test_risk.py gains one test with hand-worked values.

## Files changed

- src/archy/instability.py
- src/archy/refactor.py
- src/archy/risk.py
- tests/test_instability.py
- tests/test_risk.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 42-archy-752.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 752.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report also mentions propagation inputs and the equality score. The fix does not change either one: the equality score uses outgoing counts and the bug report asks for a change there only if the score uses fan-in. The bug report asks for command-level tests (graph and what-to-refactor-next and cycles). The tests on this page work on the graph functions directly. Fixes 34 and 35 and 36 and 37 and 41 and 42 and 43 and 45 all belong to Archy and apply together.

## Search words

Archy self-import self-edge instability Ca Ce fan-in edit_risk what-to-refactor-next central and fragile rich box.py

## The full patch

`````diff
diff --git a/src/archy/instability.py b/src/archy/instability.py
index e19caa0..e9a2f27 100644
--- a/src/archy/instability.py
+++ b/src/archy/instability.py
@@ -33,12 +33,17 @@ def compute_instability(graph: nx.DiGraph) -> dict[str, float]:
     Edges to external nodes (`external=True`) are excluded from both Ce
     and Ca counts so the metric is intrinsic to the project's own
     architecture.
+
+    A self-edge (a module that imports itself, as in a
+    `if __name__ == "__main__":` demo block) is excluded too: Python binds
+    the module already in `sys.modules`, so it is neither a dependency on
+    another module nor an importer. Cycle detection still sees the self-loop.
     """
     internal = {n for n, d in graph.nodes(data=True) if not d.get("external")}
     out: dict[str, float] = {}
     for node in internal:
-        ce = sum(1 for succ in graph.successors(node) if succ in internal)
-        ca = sum(1 for pred in graph.predecessors(node) if pred in internal)
+        ce = sum(1 for succ in graph.successors(node) if succ in internal and succ != node)
+        ca = sum(1 for pred in graph.predecessors(node) if pred in internal and pred != node)
         total = ce + ca
         out[node] = (ce / total) if total else 0.0
     return out
diff --git a/src/archy/refactor.py b/src/archy/refactor.py
index da2a2a2..085ea31 100644
--- a/src/archy/refactor.py
+++ b/src/archy/refactor.py
@@ -208,7 +208,9 @@ def compute_refactor_priorities(
                 propagation_cost=propagation_cost.get(module, 0.0),
                 instability=instability.get(module, 0.0),
                 fan_in=sum(
-                    1 for p in graph.predecessors(module) if not graph.nodes[p].get("external")
+                    1
+                    for p in graph.predecessors(module)
+                    if p != module and not graph.nodes[p].get("external")
                 ),
                 rationale=_rationale(tuple(lenses), cc_sum=cc_sum, churn=churn_n, edit_risk=risk),
             )
diff --git a/src/archy/risk.py b/src/archy/risk.py
index c946118..73613e3 100644
--- a/src/archy/risk.py
+++ b/src/archy/risk.py
@@ -62,7 +62,8 @@ def compute_edit_risk(graph: nx.DiGraph) -> dict[str, float]:
 
     out: dict[str, float] = {}
     for node in internal:
-        fan_in = sum(1 for pred in graph.predecessors(node) if pred in internal)
+        # A module importing itself is not its own importer (see instability).
+        fan_in = sum(1 for pred in graph.predecessors(node) if pred in internal and pred != node)
         fan_in_norm = fan_in / denom
         prop = propagation_cost.get(node, 0.0)
         inst = instability.get(node, 0.0)
diff --git a/tests/test_instability.py b/tests/test_instability.py
index 6424ed2..046f9fe 100644
--- a/tests/test_instability.py
+++ b/tests/test_instability.py
@@ -39,6 +39,27 @@ def test_isolated_module_reports_zero():
     assert result["loner"] == 0.0
 
 
+def test_a_self_import_counts_as_neither_importer_nor_dependency():
+    # `box` imports itself (a `__main__` demo block) and nothing else internal;
+    # `other` imports nothing. By hand, with the self-loop excluded, both have
+    # Ca = 0 and Ce = 0, so both report 0.0 (#752).
+    g = nx.DiGraph()
+    g.add_node("pkg.box", external=False)
+    g.add_node("pkg.other", external=False)
+    g.add_edge("pkg.box", "pkg.box")
+    assert g.has_edge("pkg.box", "pkg.box")
+    result = compute_instability(g)
+    assert result["pkg.box"] == result["pkg.other"] == 0.0
+
+
+def test_a_self_import_does_not_dilute_real_coupling():
+    # `a` imports `b` and itself: Ce = 1, Ca = 0 -> I(a) = 1.0, not 1/(2+1).
+    g = _g(("a", "b"), ("a", "a"))
+    result = compute_instability(g)
+    assert result["a"] == 1.0
+    assert result["b"] == 0.0
+
+
 def test_external_edges_do_not_affect_instability():
     # `a` imports an external module `ext`; that edge should not raise Ce.
     # Without `b`, `a` would be isolated -> I=0.
diff --git a/tests/test_risk.py b/tests/test_risk.py
index 2c70d0f..73b7871 100644
--- a/tests/test_risk.py
+++ b/tests/test_risk.py
@@ -37,6 +37,20 @@ def test_stable_sink_has_zero_risk():
     assert risk["b"] == 0.0
 
 
+def test_a_module_that_only_imports_itself_has_zero_risk():
+    # `box` imports itself and nobody imports it: fan-in 0 and instability 0
+    # with the self-loop excluded, so the composite is 0.0, the same as the
+    # untouched `other` (#752). Before, `box` scored above zero and ranked
+    # first as "central and fragile".
+    g = nx.DiGraph()
+    for name in ("pkg", "pkg.box", "pkg.other"):
+        g.add_node(name, external=False)
+    g.add_edge("pkg.box", "pkg.box")
+    assert g.has_edge("pkg.box", "pkg.box")
+    risk = compute_edit_risk(g)
+    assert risk["pkg.box"] == risk["pkg.other"] == 0.0
+
+
 def test_pure_source_has_zero_risk():
     # `a` imports `b` but no one imports `a`: fan_in=0 -> composite=0.
     g = _g(("a", "b"))
`````

[Back to the shelf](README.md)
