# Fix 123: Archy: no test checks that a project that meets the layer floor exactly passes the MCP check

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: test(mcp): `archy_check` can fail a project that meets `min_layers_present` exactly, with the suite green
- Bug report: number 805 ([open the bug report](https://github.com/hslee16/Archy/issues/805))
- Project license: MIT
- Language: Python
- Test included: yes
- Patch file: [fixes/123-archy-805.patch](fixes/123-archy-805.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/123-archy-805.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-123-archy-805.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-123-archy-805.html

## The bug

The only test of min_layers_present on the MCP side had zero layers present against a floor of two. A change of the comparison from less-than to less-than-or-equal would fail every project that meets the floor exactly and the tests would stay green.

## The fix

Tests only. tests/test_mcp_check.py gains a small project with two filled layers and one empty layer. One test sets the floor to 2 and expects passed true and presence_fails false. One test sets the floor to 3 and expects passed false and presence_fails true.

## Files changed

- tests/test_mcp_check.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 123-archy-805.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 805.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report's example uses two declared layers and a floor of 3. The project rejects a floor above the number of declared layers so the tests declare a third empty layer. The chatbot did not run the tests. The optional comparison with the command line in the bug report is not included.

## Search words

Archy archy_check min_layers_present boundary run_check presence_fails layers_present mutation test mcp

## The full patch

`````diff
diff --git a/tests/test_mcp_check.py b/tests/test_mcp_check.py
index 404ea34..1c7f191 100644
--- a/tests/test_mcp_check.py
+++ b/tests/test_mcp_check.py
@@ -63,6 +63,50 @@ def test_check_passed_respects_the_layer_presence_floor(tmp_path: Path):
     assert sorted(dumped["coverage"]["empty_layers"]) == ["routes", "services"]
 
 
+def _three_layer_project(root: Path, floor: int) -> None:
+    """Two populated layers (ui and core) and one empty layer (data)."""
+    for package in ("app", "app/ui", "app/core"):
+        (root / package).mkdir(exist_ok=True)
+        (root / package / "__init__.py").write_text("")
+    (root / "app" / "ui" / "x.py").write_text("x = 1\n")
+    (root / "app" / "core" / "y.py").write_text("y = 1\n")
+    (root / "archy.yaml").write_text(
+        f"min_layers_present: {floor}\n"
+        "layers:\n"
+        "  ui:\n    modules: ['app.ui.**']\n"
+        "  core:\n    modules: ['app.core.**']\n"
+        "  data:\n    modules: ['app.data.**']\n"
+    )
+
+
+def test_check_passes_when_the_layer_presence_floor_is_met_exactly(tmp_path: Path):
+    """The boundary of the floor: `layers_present == min_layers_present` passes (#805).
+
+    The floor test above sits far from the boundary (0 present against 2), so
+    the comparison could become `<=` unnoticed and fail a project that meets
+    the floor exactly while `archy check` on the same project exits 0.
+    """
+    _three_layer_project(tmp_path, floor=2)
+
+    dumped = run_check(tmp_path, config_path=None).model_dump()
+
+    # Asserted first so the fixture provably sits on the boundary.
+    assert dumped["coverage"]["layers_present"] == 2
+    assert dumped["min_layers_present"] == 2
+    assert dumped["passed"] is True
+    assert dumped["presence_fails"] is False
+
+
+def test_check_fails_one_layer_below_the_layer_presence_floor(tmp_path: Path):
+    _three_layer_project(tmp_path, floor=3)
+
+    dumped = run_check(tmp_path, config_path=None).model_dump()
+
+    assert dumped["coverage"]["layers_present"] == 2
+    assert dumped["passed"] is False
+    assert dumped["presence_fails"] is True
+
+
 @pytest.mark.parametrize("relative", [True, False], ids=["relative", "absolute"])
 def test_check_config_path_is_relative_to_project(
     tmp_path: Path,
`````

[Back to the shelf](README.md)
