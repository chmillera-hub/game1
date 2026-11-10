# Fix 45: Archy: simulate still says overall +0.000 in JSON and on MCP when no edge resolved

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: fix(simulate): the JSON and MCP `summary.headline` still says "overall +0.000" when no edge resolved, an unmet acceptance criterion of #627
- Bug report: number 795 ([open the bug report](https://github.com/hslee16/Archy/issues/795))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/45-archy-795.patch](fixes/45-archy-795.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/45-archy-795.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-45-archy-795.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-45-archy-795.html

## The bug

When archy simulate is given an edge whose module does not exist nothing is simulated. The text output says so. The JSON output and the MCP answer still carried the headline overall +0.000 which reads as a free edit.

## The fix

find_simulate in src/archy/simulate.py replaces the headline with the nothing simulated sentence when no edge resolved. The text renderer in src/archy/cli_render_history.py now prints that headline in place of its own copy of the sentence so all three outputs read one value. tests/test_simulate.py gains a test for the unresolved case and a control test for a resolved edge.

## Files changed

- src/archy/cli_render_history.py
- src/archy/simulate.py
- tests/test_simulate.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 45-archy-795.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 795.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The text output keeps the same words as before. The tests on this page call find_simulate and check the dumped summary. The bug report also asks for a check through the command line JSON and the MCP run function and those two checks are not included.

## Search words

Archy simulate summary.headline overall +0.000 nothing simulated no edge resolved coverage none archy_simulate

## The full patch

`````diff
diff --git a/src/archy/cli_render_history.py b/src/archy/cli_render_history.py
index 85e3d08..9479421 100644
--- a/src/archy/cli_render_history.py
+++ b/src/archy/cli_render_history.py
@@ -217,11 +217,9 @@ def _simulate_to_text(result: SimulateReport) -> str:
     lines.append("")
     if a.coverage == "none":
         # Every number below would describe the unchanged graph: a `+0.000` that
-        # reads as "this edit is free" when no edit was simulated.
-        lines.append(
-            "# summary: nothing simulated: no edge resolved, so no score, cycle or "
-            "violation delta was computed"
-        )
+        # reads as "this edit is free" when no edit was simulated. `simulate`
+        # put the reason in the headline; JSON and MCP carry the same one.
+        lines.append(f"# summary: {result.summary.headline}")
         return "\n".join(lines)
     if a.coverage == "partial":
         lines.append(
diff --git a/src/archy/simulate.py b/src/archy/simulate.py
index 0fbf2d3..95a034c 100644
--- a/src/archy/simulate.py
+++ b/src/archy/simulate.py
@@ -144,6 +144,11 @@ class SimulateReport(BaseModel):
     summary: DiffSummary
 
 
+_NOTHING_SIMULATED = (
+    "nothing simulated: no edge resolved, so no score, cycle or violation delta was computed"
+)
+
+
 def find_simulate(
     graph: nx.DiGraph,
     *,
@@ -191,6 +196,12 @@ def find_simulate(
     after = take_snapshot(hypo, config_path=config_path, reach_graph=hypo_reach)
     report = compute_diff(before, after)
     summary = summarize_diff(report, hypo, hypothetical=True)
+    if applied.coverage == "none":
+        # No edge resolved, so the delta describes the unchanged graph: an
+        # "overall +0.000" headline would read as "this edit is free" for an
+        # import that was never simulated. Decided here, where coverage is
+        # known, so text, JSON and MCP all carry the same sentence.
+        summary = summary.model_copy(update={"headline": _NOTHING_SIMULATED})
 
     prop_before = compute_propagation_cost(graph)[0]
     prop_after = compute_propagation_cost(hypo)[0]
diff --git a/tests/test_simulate.py b/tests/test_simulate.py
index 8b7cb31..da6f7cc 100644
--- a/tests/test_simulate.py
+++ b/tests/test_simulate.py
@@ -312,6 +312,27 @@ def test_a_file_path_endpoint_is_answered_with_a_file_path_in_the_form_typed(tmp
     )
 
 
+def test_headline_says_nothing_was_simulated_when_no_edge_resolved(tmp_path: Path):
+    """`overall +0.000` beside `coverage: none` reads as "free edit" (#795)."""
+    project = _make_pkg(tmp_path, {"a.py": "", "b.py": ""})
+    g = _internal(project)
+    result = find_simulate(g, add=[("app.nope", "app.a")], remove=[], project_root=project)
+    assert result.applied.coverage == "none"
+    headline = result.model_dump()["summary"]["headline"]
+    assert "nothing simulated" in headline
+    assert "+0.000" not in headline
+
+
+def test_headline_stays_numeric_when_an_edge_resolved(tmp_path: Path):
+    project = _make_pkg(tmp_path, {"a.py": "", "b.py": ""})
+    g = _internal(project)
+    result = find_simulate(g, add=[("app.a", "app.b")], remove=[], project_root=project)
+    assert result.applied.coverage == "complete"
+    headline = result.model_dump()["summary"]["headline"]
+    assert headline.startswith("overall ")
+    assert "nothing simulated" not in headline
+
+
 def test_coverage_survives_model_dump(tmp_path: Path):
     """FastMCP sends `model_dump()`; a plain property would drop the verdict."""
     project = _make_pkg(tmp_path, {"a.py": "", "b.py": ""})
`````

[Back to the shelf](README.md)
