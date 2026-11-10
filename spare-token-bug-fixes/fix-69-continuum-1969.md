# Fix 69: CONTINUUM: the recovery advice for an unreadable constraints file names a command that does not exist

Status: UNSENT and UNTESTED. Free to take.

- Project: Under-Research-Labs/CONTINUUM
- Bug report title: recovery: unreadable-registry guidance sends the operator to a command that does not exist
- Bug report: number 1969 ([open the bug report](https://github.com/Under-Research-Labs/CONTINUUM/issues/1969))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/69-continuum-1969.patch](fixes/69-continuum-1969.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/69-continuum-1969.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-69-continuum-1969.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-69-continuum-1969.html

## The bug

When the constraints registry file was present and unreadable the recovery advice told the operator to rerun continuum assess with the run id. No assess command exists so following the advice ended in an invalid choice error.

## The fix

src/continuum/recovery/guidance.py now names continuum validate which is the read-only command that checks a run again. A new file tests/test_unreadable_registry_guidance_command.py builds a repair plan with one registry step and checks that the advice names validate and does not name assess. CHANGELOG.md gains one line under Unreleased and Fixed.

## Files changed

- CHANGELOG.md
- src/continuum/recovery/guidance.py
- tests/test_unreadable_registry_guidance_command.py

## How to use the fix

1. Get a copy of the project Under-Research-Labs/CONTINUUM.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 69-continuum-1969.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1969.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The one-word change is the change the bug report itself proposes. The chatbot did not run the new test. The test builds the decision from a plain stand-in object the same way an existing test in tests/test_recovery_guidance.py does. Fix 81 on this shelf changes a line three lines above in the same file and adds a changelog entry at the same spot so the two patches do not apply together: apply one patch and make the other one-line change by hand. Fix 94 on this shelf adds a changelog entry at the same spot so the two patches do not apply together: add the other changelog entry by hand.

## Search words

CONTINUUM recovery guidance human_steps_for unreadable constraints registry continuum assess invalid choice continuum validate

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 955adbc..0341723 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -281,6 +281,11 @@ Test counts: ~4400 collected on a minimal env.
   are configured.
 ### Fixed
 
+- **Unreadable-registry guidance names a command that exists (#1969).** The
+  human step for an unreadable constraints registry told the operator to rerun
+  `continuum assess <run_id>`, and no `assess` subcommand exists. The step now
+  names `continuum validate <run_id>`, the read-only re-assessment command.
+
 - **The daemon's active-run probe and detached startup deadline work on
   server-backed storage (#1855).** The probe gated on `Path(db).exists()`,
   which is never true for a `postgresql://` URL, so the daemon silently bound
diff --git a/src/continuum/recovery/guidance.py b/src/continuum/recovery/guidance.py
index 579ac4f..484ce85 100644
--- a/src/continuum/recovery/guidance.py
+++ b/src/continuum/recovery/guidance.py
@@ -140,7 +140,7 @@ def human_steps_for(
             if step.target.startswith("registry"):
                 steps.append(
                     f"repair unreadable constraints registry file (.continuum/constraints.json), "
-                    f"then rerun `continuum assess {run_id}`"
+                    f"then rerun `continuum validate {run_id}`"
                 )
             elif step.target.startswith("pin:") or any(
                 e.component is Component.PIN and e.component_id == step.target for e in statuses
diff --git a/tests/test_unreadable_registry_guidance_command.py b/tests/test_unreadable_registry_guidance_command.py
new file mode 100644
index 0000000..8b01b0b
--- /dev/null
+++ b/tests/test_unreadable_registry_guidance_command.py
@@ -0,0 +1,30 @@
+"""The unreadable-registry human step must name a CLI command that exists (#1969)."""
+
+from __future__ import annotations
+
+from types import SimpleNamespace
+
+from continuum.models import RecoveryMode
+from continuum.recovery.guidance import human_steps_for
+from continuum.recovery.planner import RepairKind, RepairPlan, RepairStep
+
+
+def test_unreadable_registry_step_points_at_validate_not_assess() -> None:
+    plan = RepairPlan(
+        steps=[
+            RepairStep(
+                kind=RepairKind.HUMAN_REVIEW,
+                target="registry",
+                reason="constraints registry is unreadable",
+            )
+        ]
+    )
+    decision = SimpleNamespace(mode=RecoveryMode.REQUEST_HUMAN, plan=plan, uncertain_actions=())
+
+    steps = human_steps_for(decision, run_id="run_1")
+
+    registry_steps = [s for s in steps if "repair unreadable constraints registry file" in s]
+    assert len(registry_steps) == 1, steps
+    assert "`continuum validate run_1`" in registry_steps[0]
+    # `assess` is RecoveryEngine.assess, a method; it is not a CLI subcommand.
+    assert "continuum assess" not in registry_steps[0]
`````

[Back to the shelf](README.md)
