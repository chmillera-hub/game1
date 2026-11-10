# Fix 94: CONTINUUM: building an attempt lesson can hang forever or exceed its size limit when action ids are long

Status: UNSENT and UNTESTED. Free to take.

- Project: Under-Research-Labs/CONTINUUM
- Bug report title: recovery: build_attempt_lesson's 2048-byte shrink loop never trims scar_action_ids, so it breaches the cap or hangs
- Bug report: number 1966 ([open the bug report](https://github.com/Under-Research-Labs/CONTINUUM/issues/1966))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/94-continuum-1966.patch](fixes/94-continuum-1966.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/94-continuum-1966.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-94-continuum-1966.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-94-continuum-1966.html

## The bug

build_attempt_lesson promises a total size of 2048 bytes. The loop that shrinks the lesson never shortened the list of scar action ids. With long ids and evidence present the loop never ended and continuum resume --repair hung with no error. With long ids and no evidence the lesson was saved far over the limit.

## The fix

src/continuum/recovery/summary.py gains _shrink_tail which always returns a smaller list: drop the last item and then halve the single remaining item and then return an empty list. The loop uses the helper for the evidence and then for the scar ids. A new file tests/test_attempt_lesson_scar_budget.py covers both cases from the bug report and the helper. CHANGELOG.md gains one entry.

## Files changed

- CHANGELOG.md
- src/continuum/recovery/summary.py
- tests/test_attempt_lesson_scar_budget.py

## How to use the fix

1. Get a copy of the project Under-Research-Labs/CONTINUUM.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 94-continuum-1966.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1966.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The loop empties the text fields and the evidence before the loop touches the scar ids. That order is the chatbot's choice and the maintainers may prefer to shorten the ids earlier. The chatbot modelled the loop in a scratch script: the hang case ended after 41 rounds at 2004 bytes with 9 of 16 ids kept. The chatbot did not run the project's code or tests. Without the fix the first new test would hang. Fixes 69 and 81 on this shelf add a changelog entry at the same spot so this patch does not apply together with either of them: add the other changelog entries by hand.

## Search words

CONTINUUM build_attempt_lesson scar_action_ids 2048 byte budget infinite loop hang resume --repair shrink loop source_evidence

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 955adbc..cbd8279 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -281,6 +281,13 @@ Test counts: ~4400 collected on a minimal env.
   are configured.
 ### Fixed
 
+- **`build_attempt_lesson` keeps its 2 KB budget when the scar ids are
+  oversized (#1966).** The shrink loop never trimmed `scar_action_ids`, the one
+  field with no per-item bound. With evidence present the loop never ended and
+  `continuum resume --repair` hung; without evidence the lesson was committed
+  over the cap. The loop now trims the scar ids last (drop trailing ids, then
+  halve the remaining one) and the evidence trim is strictly decreasing.
+
 - **The daemon's active-run probe and detached startup deadline work on
   server-backed storage (#1855).** The probe gated on `Path(db).exists()`,
   which is never true for a `postgresql://` URL, so the daemon silently bound
diff --git a/src/continuum/recovery/summary.py b/src/continuum/recovery/summary.py
index 3021d78..727d807 100644
--- a/src/continuum/recovery/summary.py
+++ b/src/continuum/recovery/summary.py
@@ -221,6 +221,20 @@ def _truncate(text: str, cap: int = ATTEMPT_LESSON_FIELD_CAP) -> str:
     return text[:cap]
 
 
+def _shrink_tail(items: Any) -> list[str]:
+    """One strictly smaller copy of a list of strings.
+
+    Drops the last item while more than one is left, then halves the single
+    remaining item, and returns ``[]`` once that item is empty. The result is
+    always smaller than the input, so a loop that calls this makes progress.
+    """
+    shrunk = [str(item) for item in items]
+    if len(shrunk) > 1:
+        return shrunk[:-1]
+    half = shrunk[0][: len(shrunk[0]) // 2] if shrunk else ""
+    return [half] if half else []
+
+
 def _lesson_total_bytes(lesson: Any) -> int:
     import json
 
@@ -313,21 +327,23 @@ def build_attempt_lesson(
         current = getattr(lesson, largest)
         if not current:
             if lesson.source_evidence:
-                trimmed = list(lesson.source_evidence)
-                trimmed = (
-                    trimmed[:-1]
-                    if len(trimmed) > 1
-                    else [trimmed[0][: max(len(trimmed[0]) // 2, 0)]]
+                lesson = lesson.model_copy(
+                    update={"source_evidence": _shrink_tail(lesson.source_evidence)}
+                )
+                continue
+            if lesson.scar_action_ids:
+                # The scar ids are the one field with no per-item bound, so they
+                # are shrinkable too: without this an oversized id list either
+                # spun this loop forever or left the lesson over its budget.
+                lesson = lesson.model_copy(
+                    update={"scar_action_ids": _shrink_tail(lesson.scar_action_ids)}
                 )
-                lesson = lesson.model_copy(update={"source_evidence": trimmed})
                 continue
             break
         truncated = current[: max(len(current) // 2, 0)]
         lesson = lesson.model_copy(update={largest: truncated})
         if _lesson_total_bytes(lesson) <= 2048:
             break
-        if all(len(getattr(lesson, name)) == 0 for name in fields) and not lesson.source_evidence:
-            break
     return lesson
 
 
diff --git a/tests/test_attempt_lesson_scar_budget.py b/tests/test_attempt_lesson_scar_budget.py
new file mode 100644
index 0000000..c7eab9d
--- /dev/null
+++ b/tests/test_attempt_lesson_scar_budget.py
@@ -0,0 +1,79 @@
+"""build_attempt_lesson keeps its 2 KB budget when the scar ids are what is oversized (#1966).
+
+The shrink loop trimmed the text fields and the evidence and never the scar
+ids. With oversized ids it either never ended (evidence present) or returned
+a lesson far over the cap (no evidence).
+"""
+
+from __future__ import annotations
+
+import json
+from types import SimpleNamespace
+
+from continuum.models import (
+    Action,
+    Component,
+    ComponentValidationEntry,
+    StateStatus,
+    StateValidationResult,
+)
+from continuum.recovery.summary import _shrink_tail, build_attempt_lesson
+
+
+def _total_bytes(lesson) -> int:
+    return len(json.dumps(lesson.model_dump(mode="json"), sort_keys=True).encode())
+
+
+def _decision(*, with_evidence: bool) -> SimpleNamespace:
+    scars = [Action(run_id="run_1", action_type="shell", action_id="s" * 200) for _ in range(16)]
+    decision = SimpleNamespace(
+        run_id="run_1",
+        rationale=("the goal was not achieved",),
+        restored=None,
+        uncertain_actions=scars,
+    )
+    if with_evidence:
+        report = StateValidationResult(
+            run_id="run_1",
+            statuses=[
+                ComponentValidationEntry(
+                    component=Component.EXTERNAL_DEPENDENCY,
+                    component_id="dep_1",
+                    status=StateStatus.STALE,
+                    detail="e" * 900,
+                ),
+                ComponentValidationEntry(
+                    component=Component.GOAL,
+                    component_id=None,
+                    status=StateStatus.STALE,
+                    detail="a" * 900,
+                ),
+            ],
+            safe_to_resume=False,
+            reason="goal went stale",
+        )
+        decision.validation = SimpleNamespace(report=report)
+    return decision
+
+
+def test_oversized_scar_ids_with_evidence_end_within_budget() -> None:
+    lesson = build_attempt_lesson(_decision(with_evidence=True))
+
+    assert _total_bytes(lesson) <= 2048
+    assert 0 < len(lesson.scar_action_ids) < 16
+    assert all("s" * 200 == sid for sid in lesson.scar_action_ids)
+
+
+def test_oversized_scar_ids_without_evidence_end_within_budget() -> None:
+    lesson = build_attempt_lesson(_decision(with_evidence=False))
+
+    assert _total_bytes(lesson) <= 2048
+    assert 0 < len(lesson.scar_action_ids) < 16
+
+
+def test_shrink_tail_is_strictly_decreasing() -> None:
+    assert _shrink_tail(["a", "b", "c"]) == ["a", "b"]
+    assert _shrink_tail(["abcd"]) == ["ab"]
+    assert _shrink_tail(["a"]) == []
+    assert _shrink_tail([""]) == []
+    assert _shrink_tail([]) == []
`````

[Back to the shelf](README.md)
