# Fix 20: agent-blueprint: lint rule unused-produced-field ignores fields read by policies.escalation

Status: UNSENT and UNTESTED. Free to take.

- Project: ahmetatar/agent-blueprint
- Bug report title: lint: unused-produced-field ignores fields read by policies.escalation
- Bug report: number 84 ([open the bug report](https://github.com/ahmetatar/agent-blueprint/issues/84))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/20-agent-blueprint-84.patch](fixes/20-agent-blueprint-84.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/20-agent-blueprint-84.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-20-agent-blueprint-84.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-20-agent-blueprint-84.html

## The bug

abp lint warns that a node produces the state field confidence and that nothing consumes the field. The escalation policy reads that field at runtime to decide the route. The warning is a false positive and nudges people to delete a field the escalation guarantee depends on.

## The fix

The consumed state fields block in src/agent_blueprint/linting.py now counts confidence as consumed when policies.escalation has both on_low_confidence and confidence_threshold set. Those are the same two conditions the generated runtime checks before reading the field. A new test file covers the escalation case and two cases where the warning still fires. A changelog line is included.

## Files changed

- CHANGELOG.md
- src/agent_blueprint/linting.py
- tests/test_linting_unused_produced_field.py

## How to use the fix

1. Get a copy of the project ahmetatar/agent-blueprint.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 20-agent-blueprint-84.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 84.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report names an example file that is not in the main branch so the chatbot could not check that file. The patch also extends the warning text to mention the escalation policy.

## Search words

agent-blueprint abp lint unused-produced-field confidence policies.escalation on_low_confidence confidence_threshold false positive

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 2b83cc0..2268b03 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -6,6 +6,12 @@ The format is based on Keep a Changelog, and this project aims to follow Semanti
 
 ## [Unreleased]
 
+### Fixed
+
+- `abp lint` no longer reports `unused-produced-field` for the `confidence`
+  state field when `policies.escalation` has both `on_low_confidence` and
+  `confidence_threshold` set: the generated runtime routes on that field.
+
 ### Security
 
 - **Breaking:** the deployed `/invoke` endpoint now authenticates callers and
diff --git a/src/agent_blueprint/linting.py b/src/agent_blueprint/linting.py
index d37a0a3..4a89438 100644
--- a/src/agent_blueprint/linting.py
+++ b/src/agent_blueprint/linting.py
@@ -474,6 +474,17 @@ def _lint_contract_usage(spec: BlueprintSpec) -> list[LintFinding]:
         consumed_state_fields.update(spec.output.schema_def.keys())
     for contract in spec.contracts.nodes.values():
         consumed_state_fields.update(contract.requires)
+    # Low-confidence escalation reads the `confidence` state field at runtime:
+    # the generated `_apply_low_confidence_escalation` routes on it whenever the
+    # policy has both a target and a threshold. Mirror that condition exactly so
+    # the field the escalation guarantee depends on is not reported as unused.
+    escalation = spec.policies.escalation if spec.policies else None
+    if (
+        escalation is not None
+        and escalation.on_low_confidence is not None
+        and escalation.confidence_threshold is not None
+    ):
+        consumed_state_fields.add("confidence")
 
     for node_id, contract in spec.contracts.nodes.items():
         for field_name in contract.produces:
@@ -482,7 +493,7 @@ def _lint_contract_usage(spec: BlueprintSpec) -> list[LintFinding]:
                 severity=LintSeverity.warning,
                 code="unused-produced-field",
                 location=f"contracts.nodes.{node_id}.produces",
-                message=f"Node '{node_id}' produces state field '{field_name}' but no route, output, or node requirement consumes it",
+                message=f"Node '{node_id}' produces state field '{field_name}' but no route, output, node requirement, or escalation policy consumes it",
                 autofixable=False,
             ))
 
diff --git a/tests/test_linting_unused_produced_field.py b/tests/test_linting_unused_produced_field.py
new file mode 100644
index 0000000..3ea36e8
--- /dev/null
+++ b/tests/test_linting_unused_produced_field.py
@@ -0,0 +1,53 @@
+"""Tests for the unused-produced-field lint check and the escalation policy."""
+
+from agent_blueprint.ir.compiler import compile_blueprint
+from agent_blueprint.linting import lint_blueprint
+from agent_blueprint.models.blueprint import BlueprintSpec
+
+
+def lint(raw: dict):
+    spec = BlueprintSpec.model_validate(raw)
+    return [
+        f for f in lint_blueprint(spec, compile_blueprint(spec))
+        if f.code == "unused-produced-field"
+    ]
+
+
+def _raw(policies: dict | None = None) -> dict:
+    raw = {
+        "blueprint": {"name": "escalation-consumes-confidence"},
+        "state": {"fields": {
+            "messages": {"type": "list[message]", "reducer": "append"},
+            "confidence": {"type": "number", "nullable": True},
+        }},
+        "graph": {
+            "entry_point": "router",
+            "nodes": {"router": {"type": "function"}, "esc": {"type": "function"}},
+            "edges": [{"from": "router", "to": "END"}, {"from": "esc", "to": "END"}],
+        },
+        "contracts": {"nodes": {"router": {"produces": ["confidence"]}}},
+    }
+    if policies:
+        raw["policies"] = policies
+    return raw
+
+
+class TestUnusedProducedField:
+    def test_field_read_by_escalation_policy_is_consumed(self):
+        # The generated runtime routes on `confidence` when the policy has a
+        # target and a threshold, so the field is consumed.
+        findings = lint(_raw({
+            "escalation": {"on_low_confidence": "esc", "confidence_threshold": 0.7},
+        }))
+        assert findings == []
+
+    def test_warning_still_fires_without_an_escalation_policy(self):
+        findings = lint(_raw())
+        assert len(findings) == 1
+        assert "confidence" in findings[0].message
+        assert findings[0].location == "contracts.nodes.router.produces"
+
+    def test_warning_still_fires_when_the_policy_has_no_threshold(self):
+        # Without a threshold the runtime never reads `confidence`.
+        findings = lint(_raw({"escalation": {"on_low_confidence": "esc"}}))
+        assert len(findings) == 1
`````

[Back to the shelf](README.md)
