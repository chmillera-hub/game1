# Fix 81: CONTINUUM: a rule whose id starts with registry gets the wrong recovery advice

Status: UNSENT and UNTESTED. Free to take.

- Project: Under-Research-Labs/CONTINUUM
- Bug report title: recovery: registry guidance matches constraint ids by prefix, hijacking the pin confirmation step
- Bug report: number 1970 ([open the bug report](https://github.com/Under-Research-Labs/CONTINUUM/issues/1970))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/81-continuum-1970.patch](fixes/81-continuum-1970.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/81-continuum-1970.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-81-continuum-1970.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-81-continuum-1970.html

## The bug

A hard constraint with an id such as registry_write_guard that needs review was reported to the operator as an unreadable constraints registry file. The operator was told to repair a file that was fine and was not shown the confirmation step that clears the review.

## The fix

src/continuum/recovery/guidance.py now compares the step target with the exact word registry and no longer accepts any target that starts with registry. A new file tests/test_registry_prefix_constraint_guidance.py checks that registry_write_guard gets the pin confirmation step and that the exact word registry still gets the repair step. CHANGELOG.md gains one entry under Unreleased and Fixed.

## Files changed

- CHANGELOG.md
- src/continuum/recovery/guidance.py
- tests/test_registry_prefix_constraint_guidance.py

## How to use the fix

1. Get a copy of the project Under-Research-Labs/CONTINUUM.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 81-continuum-1970.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1970.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The one-line change is the first change the bug report proposes. A constraint whose id is exactly registry would still be taken for the registry file and the bug report's second option (a reserved marker) would close that gap. Fix 69 on this shelf changes a line three lines below in the same file and adds a changelog entry at the same spot so the two patches do not apply together: apply one patch and make the other one-line change by hand. The chatbot did not run the new test.

## Search words

CONTINUUM recovery guidance human_steps_for startswith registry constraint id prefix pin confirmation registry_write_guard

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 955adbc..e5cd003 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -281,6 +281,12 @@ Test counts: ~4400 collected on a minimal env.
   are configured.
 ### Fixed
 
+- **Registry guidance no longer captures constraint ids that start with
+  `registry` (#1970).** `human_steps_for` matched the unreadable-registry
+  sentinel by prefix, so a hard constraint such as `registry_write_guard` in
+  REQUIRES_REVIEW was reported as an unreadable constraints file. The sentinel
+  is now matched by equality and such a pin gets the pin-confirmation step.
+
 - **The daemon's active-run probe and detached startup deadline work on
   server-backed storage (#1855).** The probe gated on `Path(db).exists()`,
   which is never true for a `postgresql://` URL, so the daemon silently bound
diff --git a/src/continuum/recovery/guidance.py b/src/continuum/recovery/guidance.py
index 579ac4f..8ec1928 100644
--- a/src/continuum/recovery/guidance.py
+++ b/src/continuum/recovery/guidance.py
@@ -137,7 +137,7 @@ def human_steps_for(
                 statuses = decision.validation.report.statuses
             # An unreadable registry cannot be cleared by a pin confirmation:
             # the only remedy is repairing the file and reassessing.
-            if step.target.startswith("registry"):
+            if step.target == "registry":
                 steps.append(
                     f"repair unreadable constraints registry file (.continuum/constraints.json), "
                     f"then rerun `continuum assess {run_id}`"
diff --git a/tests/test_registry_prefix_constraint_guidance.py b/tests/test_registry_prefix_constraint_guidance.py
new file mode 100644
index 0000000..f1dd604
--- /dev/null
+++ b/tests/test_registry_prefix_constraint_guidance.py
@@ -0,0 +1,38 @@
+"""A constraint id that starts with ``registry`` is a pin, not the registry file (#1970)."""
+
+from __future__ import annotations
+
+from types import SimpleNamespace
+
+from continuum.models import Component, RecoveryMode
+from continuum.recovery.guidance import human_steps_for
+from continuum.recovery.planner import RepairKind, RepairPlan, RepairStep
+
+
+def _decision(target: str, *, pin_ids: tuple[str, ...] = ()) -> SimpleNamespace:
+    plan = RepairPlan(steps=[RepairStep(kind=RepairKind.HUMAN_REVIEW, target=target)])
+    statuses = [SimpleNamespace(component=Component.PIN, component_id=cid) for cid in pin_ids]
+    return SimpleNamespace(
+        mode=RecoveryMode.REQUEST_HUMAN,
+        plan=plan,
+        uncertain_actions=(),
+        validation=SimpleNamespace(report=SimpleNamespace(statuses=statuses)),
+    )
+
+
+def test_pin_whose_id_starts_with_registry_gets_the_pin_confirmation_step() -> None:
+    decision = _decision("registry_write_guard", pin_ids=("registry_write_guard",))
+
+    steps = human_steps_for(decision, run_id="run_1")
+
+    assert len(steps) == 1, steps
+    assert "repair unreadable constraints registry file" not in steps[0]
+    assert "constraint pin 'registry_write_guard'" in steps[0]
+    assert "`continuum confirm run_1 --scope pin`" in steps[0]
+
+
+def test_the_exact_registry_sentinel_still_gets_the_repair_step() -> None:
+    steps = human_steps_for(_decision("registry"), run_id="run_1")
+
+    assert len(steps) == 1, steps
+    assert "repair unreadable constraints registry file" in steps[0]
`````

[Back to the shelf](README.md)
