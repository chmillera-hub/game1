# Fix 125: Archy: no test checks that the transitive hint stays away when the check already found a violation

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: test(check): `transitive_unverified_reason` can appear beside a concrete violation with the suite green, and two of its clauses are dead
- Bug report: number 808 ([open the bug report](https://github.com/hslee16/Archy/issues/808))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/125-archy-808.patch](fixes/125-archy-808.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/125-archy-808.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-125-archy-808.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-125-archy-808.html

## The bug

contracts_unverified is meant to hide the hint (this run cannot prove there is no transitive path) when the run already found a concrete violation. No test covered a project with a violation plus unlayered modules so the hint could appear beside a violation with every test green. Two of the five or-clauses in the function can also never change the result.

## The fix

A new file tests/test_transitive_hint_beside_violation.py runs the check on a project with one violation and one unlayered module and expects no hint. A paired test removes the violating import and expects the hint. In src/archy/layers_check.py a comment marks the two clauses that are implied by the unlayered list and the clauses stay as documentation.

## Files changed

- src/archy/layers_check.py
- tests/test_transitive_hint_beside_violation.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 125-archy-808.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 808.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report offers two options for the two dead clauses (drop them or keep them with a comment). The patch keeps them with a comment because that option changes no behaviour. The chatbot did not run the tests.

## Search words

Archy contracts_unverified transitive_unverified_reason violations unlayered_modules dead clause exact_pattern_hints edges_governed

## The full patch

`````diff
diff --git a/src/archy/layers_check.py b/src/archy/layers_check.py
index c0593dd..358c269 100644
--- a/src/archy/layers_check.py
+++ b/src/archy/layers_check.py
@@ -161,9 +161,12 @@ def contracts_unverified(
     return (
         coverage.governs_nothing
         or coverage.governs_no_edges
-        or bool(coverage.exact_pattern_hints)
+        # The two clauses marked "implied" can never decide the result: a hint
+        # is computed from the unlayered list and an edge is ungoverned only
+        # when one endpoint is unlayered. Kept as documentation (#808).
+        or bool(coverage.exact_pattern_hints)  # implied by unlayered_modules
         or bool(coverage.unlayered_modules)
-        or coverage.edges_governed < coverage.edges_total
+        or coverage.edges_governed < coverage.edges_total  # implied by unlayered_modules
     )
 
 
diff --git a/tests/test_transitive_hint_beside_violation.py b/tests/test_transitive_hint_beside_violation.py
new file mode 100644
index 0000000..1e988f8
--- /dev/null
+++ b/tests/test_transitive_hint_beside_violation.py
@@ -0,0 +1,45 @@
+"""The "cannot prove there is no transitive path" hint stays off beside a concrete violation (#808)."""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+from archy.mcp_runs import run_check
+
+
+def _project(root: Path, core_source: str) -> None:
+    """Layers ui and core with `forbid core -> ui` plus one unlayered module (app.other)."""
+    for package in ("app", "app/ui", "app/core"):
+        (root / package).mkdir(exist_ok=True)
+        (root / package / "__init__.py").write_text("")
+    (root / "app" / "ui" / "x.py").write_text("x = 1\n")
+    (root / "app" / "core" / "y.py").write_text(core_source)
+    (root / "app" / "other.py").write_text("z = 1\n")
+    (root / "archy.yaml").write_text(
+        "layers:\n"
+        "  ui:\n    modules: ['app.ui.**']\n"
+        "  core:\n    modules: ['app.core.**']\n"
+        "forbid:\n  - {from: core, to: ui}\n"
+    )
+
+
+def test_no_transitive_hint_when_the_run_found_a_concrete_violation(tmp_path: Path):
+    _project(tmp_path, "from app.ui import x\n")
+
+    dumped = run_check(tmp_path, config_path=None).model_dump()
+
+    # Asserted first so the fixture provably reaches the suppression branch.
+    assert len(dumped["violations"]) == 1
+    assert dumped["coverage"]["unlayered_modules"]
+    assert dumped["transitive_unverified_reason"] is None
+
+
+def test_transitive_hint_present_for_the_same_project_without_the_violation(tmp_path: Path):
+    """The paired case: the test above cannot pass by the reason being always absent."""
+    _project(tmp_path, "y = 1\n")
+
+    dumped = run_check(tmp_path, config_path=None).model_dump()
+
+    assert dumped["violations"] == []
+    assert dumped["coverage"]["unlayered_modules"]
+    assert dumped["transitive_unverified_reason"]
`````

[Back to the shelf](README.md)
