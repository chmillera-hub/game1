# Fix 77: Archy: the contributing guide leaves out one check that the project's automated checks run

Status: UNSENT and UNTESTED. Free to take.

- Project: hslee16/Archy
- Bug report title: docs(contributing): "Run what CI runs, not a subset" omits the `archy contracts .` gate that CI runs
- Bug report: number 769 ([open the bug report](https://github.com/hslee16/Archy/issues/769))
- Project license: MIT
- Language: Markdown and Python
- Test included: yes
- Patch file: [fixes/77-archy-769.patch](fixes/77-archy-769.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/77-archy-769.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-77-archy-769.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-77-archy-769.html

## The bug

CONTRIBUTING.md lists commands under Run what CI runs and not a subset. The list left out uv run archy contracts . which the automated checks run. A contributor could run the whole documented list with success and then fail the automated checks on a step the guide never named.

## The fix

CONTRIBUTING.md gains the line uv run archy contracts . after the cycles line and the sentence after the list now says the last four commands. A new file tests/test_contributing_ci_gates.py reads the uv run commands of the check job in .github/workflows/ci.yml and fails when the guide leaves one out.

## Files changed

- CONTRIBUTING.md
- tests/test_contributing_ci_gates.py

## How to use the fix

1. Get a copy of the project hslee16/Archy.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 77-archy-769.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 769.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran a scratch copy of the test logic over the two text files: the scratch copy reported the missing command before the change and reported nothing missing after the change. The chatbot did not run the project's tests. The new test only compares commands that start with uv run and the two checks that the automated job runs through the project's own action are not compared.

## Search words

archy CONTRIBUTING.md before you push run what CI runs archy contracts ci.yml missing gate last three commands

## The full patch

`````diff
diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
index 4d488bb..060801d 100644
--- a/CONTRIBUTING.md
+++ b/CONTRIBUTING.md
@@ -103,11 +103,12 @@ uv run ty check
 uv run pytest
 uv run archy check .       # archy enforces its own layer rules
 uv run archy cycles . --strict
+uv run archy contracts .      # transitive forbid rules, derived from archy.yaml
 uv run archy conventions . --emit-headers --check   # derived headers still true
 ```
 
 `ruff check some/file.py` is a different command from `ruff check` and will pass
-while CI fails. The last three commands are archy checking itself: a new fixture
+while CI fails. The last four commands are archy checking itself: a new fixture
 or sample tree can introduce a real cycle or layer violation, and the fix is to
 add it to `exclude:` in `archy.yaml` with a note saying why, not to weaken a
 rule. The headers check fails when a public symbol or a mirror set changes
diff --git a/tests/test_contributing_ci_gates.py b/tests/test_contributing_ci_gates.py
new file mode 100644
index 0000000..dc21643
--- /dev/null
+++ b/tests/test_contributing_ci_gates.py
@@ -0,0 +1,34 @@
+"""CONTRIBUTING's "Before you push" block lists every command the CI check job runs (#769).
+
+The block says "Run what CI runs, not a subset". It once missed
+`uv run archy contracts .`, so a contributor ran the documented list green
+and then failed CI on a step the guide never named.
+"""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import yaml
+
+ROOT = Path(__file__).resolve().parents[1]
+
+
+def _ci_run_commands() -> list[str]:
+    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
+    runs = [step.get("run", "") for step in ci["jobs"]["check"]["steps"]]
+    return [run.strip() for run in runs if run.strip().startswith("uv run ")]
+
+
+def _documented_commands() -> list[str]:
+    text = (ROOT / "CONTRIBUTING.md").read_text()
+    block = text.split("### Before you push", 1)[1].split("```bash", 1)[1].split("```", 1)[0]
+    return [line.split("#", 1)[0].strip() for line in block.splitlines() if line.strip()]
+
+
+def test_before_you_push_block_has_every_ci_run_command():
+    ci_commands = _ci_run_commands()
+    assert "uv run archy contracts ." in ci_commands  # the fixture still has the gate
+    documented = _documented_commands()
+    missing = [command for command in ci_commands if command not in documented]
+    assert not missing, f"CONTRIBUTING.md 'Before you push' omits: {missing}"
`````

[Back to the shelf](README.md)
