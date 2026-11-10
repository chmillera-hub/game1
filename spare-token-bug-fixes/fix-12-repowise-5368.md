# Fix 12: repowise: test_tool_overview.py fails when run alone because ov.health does not exist yet

Status: UNSENT and UNTESTED. Free to take.

- Project: repowise-dev/repowise
- Bug report title: [Bug] test_tool_overview.py fails when run on its own because `ov.health` only exists after another test imports it
- Bug report: number 5368 ([open the bug report](https://github.com/repowise-dev/repowise/issues/5368))
- Project license: AGPL-3.0
- Language: Python (test only)
- Test included: yes
- Patch file: [fixes/12-repowise-5368.patch](fixes/12-repowise-5368.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/12-repowise-5368.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-12-repowise-5368.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-12-repowise-5368.html

## The bug

Running tests/unit/server/mcp/test_tool_overview.py alone fails with AttributeError: module 'repowise.server.mcp_server.tool_overview' has no attribute 'health'. The package loads its submodules lazily so ov.health only exists after another test imports the submodule.

## The fix

The test now imports repowise.server.mcp_server.tool_overview.health itself and patches _get_health_metrics on that module. One test changed. No product code changed.

## Files changed

- tests/unit/server/mcp/test_tool_overview.py

## How to use the fix

1. Get a copy of the project repowise-dev/repowise.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 12-repowise-5368.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 5368.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report already had one comment on 9 November 2026 and the chatbot could not read comments. Someone may already be working on the bug report.

## Search words

repowise test_tool_overview AttributeError has no attribute health lazy_exports monkeypatch test order dependent

## The full patch

`````diff
diff --git a/tests/unit/server/mcp/test_tool_overview.py b/tests/unit/server/mcp/test_tool_overview.py
index 9ddafda..0e1f8c3 100644
--- a/tests/unit/server/mcp/test_tool_overview.py
+++ b/tests/unit/server/mcp/test_tool_overview.py
@@ -284,10 +284,14 @@ async def test_code_health_read_failure_degrades_to_an_empty_block(
 ):
     """A broken health read must cost the block, never the whole overview call."""
 
+    # The package exports its submodules lazily, so ``ov.health`` only exists once
+    # something has imported it. Import it here so this test also passes on its own.
+    from repowise.server.mcp_server.tool_overview import health
+
     async def boom(*_a, **_k):
         raise RuntimeError("health tables unreadable")
 
-    monkeypatch.setattr(ov.health, "_get_health_metrics", boom)
+    monkeypatch.setattr(health, "_get_health_metrics", boom)
     repo = SimpleNamespace(id=populated_db)
     assert await ov._build_code_health(session, repo) == {}
`````

[Back to the shelf](README.md)
