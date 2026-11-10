# Fix 48: Archy: three safety tests fail on mcp 2.x and the mcp 2.x CI job does not run them

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: test(safety): three safety-claim tests fail with AttributeError on mcp 2.x, and the mcp 2.x CI job does not run them
- Bug report: number 768 ([open the bug report](https://github.com/hslee16/Archy/issues/768))
- Project license: MIT
- Language: Python (tests) and YAML (CI)
- Test included: yes
- Patch file: [fixes/48-archy-768.patch](fixes/48-archy-768.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/48-archy-768.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-48-archy-768.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-48-archy-768.html

## The bug

Three tests behind SAFETY.md read attribute names from mcp 1.x (inputSchema and readOnlyHint). On mcp 2.x the names differ and the three tests stop with AttributeError before checking anything. The mcp 2.x CI job did not run the file so nobody saw the failure.

## The fix

tests/test_safety_claims.py now reads both values through tool.model_dump(by_alias=True) which works on both mcp versions. The bug report names that approach. .github/workflows/ci.yml adds tests/test_safety_claims.py to the mcp 2.x job.

## Files changed

- .github/workflows/ci.yml
- tests/test_safety_claims.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 48-archy-768.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 768.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- This fix changes tests and the CI file only. Nobody ran the tests on mcp 1.x or on mcp 2.x. Other differences between the two mcp versions may still stop the three tests on mcp 2.x.

## Search words

Archy test_safety_claims mcp 2.x AttributeError inputSchema input_schema readOnlyHint read_only_hint model_dump by_alias CI job

## The full patch

`````diff
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 5bf7388..c80f980 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -99,4 +99,4 @@ jobs:
           "
 
       - name: MCP suites (in-process + real stdio protocol)
-        run: .venv-mcp2/bin/python -m pytest tests/test_mcp_*.py tests/test_qualname_collision.py tests/test_config_unknown_keys.py -q
+        run: .venv-mcp2/bin/python -m pytest tests/test_mcp_*.py tests/test_qualname_collision.py tests/test_config_unknown_keys.py tests/test_safety_claims.py -q
diff --git a/tests/test_safety_claims.py b/tests/test_safety_claims.py
index a44bf05..4342066 100644
--- a/tests/test_safety_claims.py
+++ b/tests/test_safety_claims.py
@@ -389,7 +389,9 @@ def test_render_out_writes_only_the_named_file(sandbox):
 def _mcp_args(tool, proj: Path) -> dict:
     """Minimal arguments that make each archy MCP tool answer for the fixture project."""
     args: dict = {}
-    if "path" in tool.inputSchema.get("properties", {}):
+    # The wire form, not the attribute: mcp 2.x renamed `inputSchema` to
+    # `input_schema` and kept the alias, so this reads the same on both majors.
+    if "path" in tool.model_dump(by_alias=True)["inputSchema"].get("properties", {}):
         args["path"] = str(proj)
     if tool.name in {"archy_impact", "archy_affected"}:
         args["files"] = ["pkg/b.py"]
@@ -433,7 +435,9 @@ def test_mcp_tools_write_only_cache_and_baseline(sandbox):
     # The page says every tool but archy_snapshot is annotated read-only.
     for name, tool in tools.items():
         assert tool.annotations is not None, name
-        assert (tool.annotations.readOnlyHint is False) == (name == "archy_snapshot"), name
+        # The wire form again: `readOnlyHint` is `read_only_hint` on mcp 2.x.
+        read_only = tool.model_dump(by_alias=True)["annotations"]["readOnlyHint"]
+        assert (read_only is False) == (name == "archy_snapshot"), name
 
     written: set[str] = set()
     for name, tool in tools.items():
`````

[Back to the shelf](README.md)
