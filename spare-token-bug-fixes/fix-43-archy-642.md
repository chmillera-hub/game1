# Fix 43: Archy: score --strict with no recorded history says passed with no reason in JSON and on MCP

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: fix(score): `--strict` with no recorded history says passed=true with no reason in JSON and on MCP
- Bug report: number 642 ([open the bug report](https://github.com/hslee16/Archy/issues/642))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/43-archy-642.patch](fixes/43-archy-642.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/43-archy-642.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-43-archy-642.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-43-archy-642.html

## The bug

With no recorded history archy score --strict cannot compare anything. The text output says so. The JSON output and the MCP answer only said passed true. A script or an AI agent read that as no regression when no comparison happened.

## The fix

ScoreGate in src/archy/mcp_payloads.py gains a reason field. The MCP gate in src/archy/mcp_runs_check.py and the JSON gate in src/archy/cli_render_common.py fill the reason when there is no earlier score and leave the reason empty after a comparison. The JSON gate also carries previous_commit and previous_timestamp as the bug report asks. The passed value is unchanged as the bug report asks. tests/test_cli_score.py gains two tests and tests/test_mcp_scorehist.py checks the dumped gate.

## Files changed

- src/archy/cli_render_common.py
- src/archy/mcp_payloads.py
- src/archy/mcp_runs_check.py
- tests/test_cli_score.py
- tests/test_mcp_scorehist.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 43-archy-642.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 642.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report has one comment that the chatbot could not read. Another person may already be working on this bug. The reason sentence exists in two places (one for JSON and one for MCP) because the chatbot did not want to add a shared name to a module whose header lists are checked by the project's own tooling. The maintainer may prefer one shared constant. The field name reason is one of two shapes the bug report offers.

## Search words

Archy score --strict no history gate passed true reason nothing to compare ScoreGate previous_commit previous_timestamp _gate_to_dict

## The full patch

`````diff
diff --git a/src/archy/cli_render_common.py b/src/archy/cli_render_common.py
index b8b94c9..b570f93 100644
--- a/src/archy/cli_render_common.py
+++ b/src/archy/cli_render_common.py
@@ -41,10 +41,19 @@ def _gate_to_dict(gate: dict, tolerance: float) -> dict:
     delta = gate["delta"]
     return {
         "previous": gate["previous"],
+        "previous_commit": gate.get("previous_commit"),
+        "previous_timestamp": gate.get("previous_timestamp"),
         "current": gate["current"],
         "delta": delta,
         "tolerance": tolerance,
         "passed": delta is None or delta >= -tolerance,
+        # Why nothing was compared; None when a comparison happened. The same
+        # sentence as the MCP gate (`mcp_runs_check._score_gate`).
+        "reason": (
+            "no prior score recorded; nothing to compare. Record a baseline first."
+            if delta is None
+            else None
+        ),
     }
 
 
diff --git a/src/archy/mcp_payloads.py b/src/archy/mcp_payloads.py
index 4e92160..a5d35a9 100644
--- a/src/archy/mcp_payloads.py
+++ b/src/archy/mcp_payloads.py
@@ -70,6 +70,9 @@ class ScoreGate(BaseModel):
     delta: float | None
     tolerance: float
     passed: bool
+    # Why nothing was compared; None when a comparison happened. Without it
+    # `passed: true` on a first run reads as "no regression" when no check ran.
+    reason: str | None = None
 
 
 class ScorePayload(BaseModel):
diff --git a/src/archy/mcp_runs_check.py b/src/archy/mcp_runs_check.py
index 45ad65e..0682602 100644
--- a/src/archy/mcp_runs_check.py
+++ b/src/archy/mcp_runs_check.py
@@ -245,7 +245,13 @@ def _score_gate(history_path: Path, current: float, tolerance: float) -> ScoreGa
     rows = read_history(history_path)
     if not rows:
         return ScoreGate(
-            previous=None, current=current, delta=None, tolerance=tolerance, passed=True
+            previous=None,
+            current=current,
+            delta=None,
+            tolerance=tolerance,
+            passed=True,
+            # The same sentence as the CLI (`cli_render_common._gate_to_dict`).
+            reason="no prior score recorded; nothing to compare. Record a baseline first.",
         )
     previous = rows[-1]
     delta = current - previous.overall
diff --git a/tests/test_cli_score.py b/tests/test_cli_score.py
index 6da320f..dc813cc 100644
--- a/tests/test_cli_score.py
+++ b/tests/test_cli_score.py
@@ -287,6 +287,30 @@ def test_score_strict_json_includes_gate_block(tmp_path: Path):
     assert payload["gate"]["tolerance"] == 0.02
 
 
+def test_score_strict_json_says_why_nothing_was_compared(tmp_path: Path):
+    """No history: `passed` alone would read as "no regression" (#642)."""
+    project = _make_acyclic_project(tmp_path)
+    result = CliRunner().invoke(main, ["score", str(project), "--strict", "--format", "json"])
+    assert result.exit_code == 0
+    gate = json.loads(result.output)["gate"]
+    assert gate["previous"] is None and gate["delta"] is None
+    assert "nothing to compare" in gate["reason"]
+    assert gate["previous_commit"] is None and gate["previous_timestamp"] is None
+
+
+def test_score_strict_json_has_no_reason_once_a_row_is_recorded(tmp_path: Path):
+    project = _make_acyclic_project(tmp_path)
+    runner = CliRunner()
+    runner.invoke(main, ["score", str(project), "--record"])
+    result = runner.invoke(main, ["score", str(project), "--strict", "--format", "json"])
+    gate = json.loads(result.output)["gate"]
+    assert gate["reason"] is None
+    assert gate["previous"] is not None
+    # The row's own metadata reaches the CLI JSON, as it reaches MCP.
+    assert gate["previous_timestamp"]
+    assert "previous_commit" in gate
+
+
 def test_trend_json_output(tmp_path: Path):
     project = _make_acyclic_project(tmp_path)
     runner = CliRunner()
diff --git a/tests/test_mcp_scorehist.py b/tests/test_mcp_scorehist.py
index 2f2798c..1d77dc7 100644
--- a/tests/test_mcp_scorehist.py
+++ b/tests/test_mcp_scorehist.py
@@ -149,6 +149,10 @@ def test_run_score_strict_includes_gate_block(acyclic_project: Path):
     )
     assert payload.gate is not None
     assert payload.gate.tolerance == 0.02
+    # No history yet: the dumped gate says why nothing was compared (#642).
+    dumped = payload.model_dump()["gate"]
+    assert dumped["previous"] is None and dumped["passed"] is True
+    assert "nothing to compare" in dumped["reason"]
 
 
 def test_archy_score_rejects_strict_tolerance_outside_unit_interval(acyclic_project: Path):
`````

[Back to the shelf](README.md)
