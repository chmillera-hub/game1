# Fix 37: Archy: check and brief with --format json leave out coverage.governs_nothing

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: fix(check,brief): `--format json` omits `coverage.governs_nothing`, the "this config can never fire" verdict that CLI text and MCP both carry
- Bug report: number 796 ([open the bug report](https://github.com/hslee16/Archy/issues/796))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/37-archy-796.patch](fixes/37-archy-796.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/37-archy-796.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-37-archy-796.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-37-archy-796.html

## The bug

When no module falls under any root that archy.yaml names no rule can fire. The text output says so and the MCP answer carries governs_nothing true. The JSON output of archy check and archy brief left the field out. A script reading the JSON could not see the verdict.

## The fix

_coverage_to_json in src/archy/cli_render_check.py now includes governs_nothing. Both commands build the coverage block through that one function. tests/test_cli_check.py gains a test for check and brief with the config from the bug report and a test that the field is false for a covered project.

## Files changed

- src/archy/cli_render_check.py
- tests/test_cli_check.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 37-archy-796.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 796.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report names src/archy/cli_render.py. The function had moved to src/archy/cli_render_check.py by the day of writing. The bug report also suggests building the block from model_dump() and lists three smaller differences between the JSON and the MCP answer. The fix on this page takes the minimum option named in the bug report and leaves the three smaller differences for the maintainer to decide. The bug report asks for a test that compares the key sets of the JSON and the MCP answer. The test on this page checks the field directly.

## Search words

Archy check brief --format json coverage governs_nothing governs_no_edges _coverage_to_json this config can never fire

## The full patch

`````diff
diff --git a/src/archy/cli_render_check.py b/src/archy/cli_render_check.py
index 96d65bf..016d206 100644
--- a/src/archy/cli_render_check.py
+++ b/src/archy/cli_render_check.py
@@ -165,6 +165,10 @@ def _coverage_to_json(coverage: LayerCoverage) -> dict:
         # `violations` list otherwise has to re-derive "could this config have
         # said anything?" from the raw counts.
         "governs_no_edges": coverage.governs_no_edges,
+        # The stronger, distinct verdict: no module at all falls under any
+        # root the config names, so no rule here can fire. Text and MCP carry
+        # it; JSON has to as well.
+        "governs_nothing": coverage.governs_nothing,
         "exact_pattern_hints": [
             {
                 "layer": hint.layer,
diff --git a/tests/test_cli_check.py b/tests/test_cli_check.py
index 69bfe47..4b12c77 100644
--- a/tests/test_cli_check.py
+++ b/tests/test_cli_check.py
@@ -66,6 +66,38 @@ def test_check_says_so_when_the_config_governs_nothing(tmp_path: Path):
     assert "100%" not in result.output
 
 
+def _make_governs_nothing_project(tmp_path: Path) -> Path:
+    """Layer roots (`other.*`) that match no scanned module."""
+    project = tmp_path / "proj"
+    (project / "pkg").mkdir(parents=True)
+    (project / "pkg" / "__init__.py").write_text("")
+    (project / "pkg" / "a.py").write_text("from pkg import b\n")
+    (project / "pkg" / "b.py").write_text("X = 1\n")
+    (project / "archy.yaml").write_text(
+        "layers:\n"
+        "  ui:\n    modules: ['other.ui.**']\n"
+        "  core:\n    modules: ['other.core.**']\n"
+        "forbid:\n  - from: core\n    to: ui\n"
+    )
+    return project
+
+
+@pytest.mark.parametrize("command", ["check", "brief"])
+def test_json_carries_governs_nothing(tmp_path: Path, command: str):
+    """The "this config can never fire" verdict reaches `--format json` too (#796)."""
+    project = _make_governs_nothing_project(tmp_path)
+    result = CliRunner().invoke(main, [command, str(project), "--format", "json"])
+    coverage = json.loads(result.output)["coverage"]
+    assert coverage["modules_total"] == 0
+    assert coverage["governs_nothing"] is True
+
+
+def test_check_json_governs_nothing_is_false_when_modules_are_covered(tmp_path: Path):
+    project = _make_bare_pattern_project(tmp_path)
+    result = CliRunner().invoke(main, ["check", str(project), "--format", "json"])
+    assert json.loads(result.output)["coverage"]["governs_nothing"] is False
+
+
 def test_check_fails_when_declared_layers_are_absent(tmp_path: Path):
     """The Constraint Decay paper's other half: forbidding edges between layers
     says nothing about whether the layers exist, and a single-module solution
`````

[Back to the shelf](README.md)
