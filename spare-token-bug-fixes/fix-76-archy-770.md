# Fix 76: Archy: SCORING.md and a code comment name MCP tools that were removed

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: docs(scoring): SCORING.md says call data reaches agents "via the `archy_graph_*` MCP tools", a tool family removed in v0.36
- Bug report: number 770 ([open the bug report](https://github.com/hslee16/Archy/issues/770))
- Project license: MIT
- Language: Markdown and Python comment
- Test included: no
- Patch file: [fixes/76-archy-770.patch](fixes/76-archy-770.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/76-archy-770.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-76-archy-770.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-76-archy-770.html

## The bug

docs/SCORING.md said call data reaches agents through the archy_graph_* MCP tools. Those tools were folded into the single tool archy_graph and no archy_graph_* tool exists. A description inside src/archy/score.py named the removed tool archy_graph_focus.

## The fix

docs/SCORING.md now says the archy_graph MCP tool. The description of _cc_stats in src/archy/score.py now says archy_graph with focus. Both new wordings are the wordings suggested in the bug report.

## Files changed

- docs/SCORING.md
- src/archy/score.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 76-archy-770.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 770.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Text only. No behaviour changes. The bug report says no test is needed. Mentions of the removed tools in history notes were left alone as the bug report asks.

## Search words

archy SCORING.md archy_graph_* archy_graph_focus removed MCP tool stale docs score.py _cc_stats

## The full patch

`````diff
diff --git a/docs/SCORING.md b/docs/SCORING.md
index 675715b..0ad6482 100644
--- a/docs/SCORING.md
+++ b/docs/SCORING.md
@@ -867,7 +867,7 @@ directionality, actionability, and discriminant-validity grounds (see
 [`AXIS_REVIEW.md`](research/AXIS_REVIEW.md)). The call data continues to be
 useful as a diagnostic on `archy score`'s output, as a refinement
 candidate for the modularity axis (call-weighted Newman Q), and as
-agent navigation data via the `archy_graph_*` MCP tools. Detailed
+agent navigation data via the `archy_graph` MCP tool. Detailed
 empirics in [`docs/research/RESEARCH_METRICS.md` §16](research/RESEARCH_METRICS.md).
 
 **Cyclomatic complexity (v0.17.0 diagnostic, v0.20.0 promoted).**
diff --git a/src/archy/score.py b/src/archy/score.py
index 5a2bfb1..9e2a195 100644
--- a/src/archy/score.py
+++ b/src/archy/score.py
@@ -167,7 +167,7 @@ def _cc_stats(graph: nx.DiGraph) -> tuple[int, int, int, float]:
     attributes attached by `build_graph` so we don't re-parse anything.
     External modules have no CC data; they're skipped via the missing-key
     default rather than a node-type check, which keeps subgraph callers
-    (e.g. archy_graph_focus) honest.
+    (e.g. `archy_graph` with `focus`) honest.
     """
     n = 0
     total = 0
`````

[Back to the shelf](README.md)
