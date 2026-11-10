# Fix 98: SMART toolkit: a test meant to cover three blueprints only ever builds the minimal blueprint

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: tests: test_init_gives_ai_tools_one_rules_file scaffolds only the minimal blueprint
- Bug report: number 36 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/36))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/98-social-messaging-agent-runtime-toolkit-36.patch](fixes/98-social-messaging-agent-runtime-toolkit-36.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/98-social-messaging-agent-runtime-toolkit-36.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-98-social-messaging-agent-runtime-toolkit-36.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-98-social-messaging-agent-runtime-toolkit-36.html

## The bug

test_init_gives_ai_tools_one_rules_file runs once for each of three blueprints and passed the blueprint name under the key template. The init command reads the key blueprint so all three runs built the minimal blueprint and the other two blueprints were never checked.

## The fix

tests/test_cli_init.py now passes blueprint=blueprint and each run also checks one file that only the named blueprint ships (and one file the blueprint does not ship).

## Files changed

- tests/test_cli_init.py

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 98-social-messaging-agent-runtime-toolkit-36.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 36.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Test only. The chatbot confirmed by reading the blueprint folders that agent.py and src/skills.py and src/catalog.py tell the three blueprints apart and that all three blueprints carry the two rules files the test checks. The chatbot did not run the test. The end of the bug report text was cut off in the search result.

## Search words

socialagent test_cli_init test_init_gives_ai_tools_one_rules_file template= blueprint= parametrize minimal personal-assistant appointment-scheduler

## The full patch

`````diff
diff --git a/tests/test_cli_init.py b/tests/test_cli_init.py
index 5e61fea..ea31516 100644
--- a/tests/test_cli_init.py
+++ b/tests/test_cli_init.py
@@ -287,12 +287,24 @@ _VENDOR_RULE_DIRS = (".amazonq", ".kiro", ".clinerules", ".cursor", ".windsurf")
 
 
 @pytest.mark.parametrize(
-    "blueprint", ["minimal", "personal-assistant", "appointment-scheduler"]
+    ("blueprint", "ships", "does_not_ship"),
+    [
+        ("minimal", "agent.py", "src"),
+        ("personal-assistant", "src/skills.py", "src/catalog.py"),
+        ("appointment-scheduler", "src/catalog.py", None),
+    ],
 )
-def test_init_gives_ai_tools_one_rules_file(tmp_project, blueprint):
+def test_init_gives_ai_tools_one_rules_file(
+    tmp_project, blueprint, ships, does_not_ship
+):
     """A scaffolded project carries AGENTS.md and CLAUDE.md, and no vendor rule dir."""
-    cmd_init(_args(name="my-agent", template=blueprint))
+    cmd_init(_args(name="my-agent", blueprint=blueprint))
     project = tmp_project / "my-agent"
+    # The case must scaffold the blueprint it names. It once passed `template=`,
+    # a key `init` does not read, so all three cases scaffolded `minimal`.
+    assert (project / ships).exists(), f"{blueprint} was not scaffolded"
+    if does_not_ship:
+        assert not (project / does_not_ship).exists(), f"not the {blueprint} blueprint"
     agents = (project / "AGENTS.md").read_text()
     assert "## Rules for AI assistants" in agents
     # Claude Code reads CLAUDE.md; a one-line import keeps AGENTS.md the one file.
`````

[Back to the shelf](README.md)
