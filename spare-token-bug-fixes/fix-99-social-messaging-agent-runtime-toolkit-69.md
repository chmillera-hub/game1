# Fix 99: SMART toolkit: socialagent deploy prints its own header after the Terraform output when the output goes to a file

Status: UNSENT and UNTESTED. Free to take.

- Project: awslabs/social-messaging-agent-runtime-toolkit
- Bug report title: cli: deploy prints its header after Terraform's output when stdout is not a terminal
- Bug report: number 69 ([open the bug report](https://github.com/awslabs/social-messaging-agent-runtime-toolkit/issues/69))
- Project license: Apache-2.0
- Language: Python
- Test included: yes
- Patch file: [fixes/99-social-messaging-agent-runtime-toolkit-69.patch](fixes/99-social-messaging-agent-runtime-toolkit-69.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/99-social-messaging-agent-runtime-toolkit-69.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-99-social-messaging-agent-runtime-toolkit-69.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-99-social-messaging-agent-runtime-toolkit-69.html

## The bug

socialagent deploy prints a header and a notice before running Terraform. When the output goes to a file or a pipe Python holds those lines back while Terraform writes directly. The header and the notice then appeared after all of the Terraform output.

## The fix

run in src/socialagent/cli/_runner.py now flushes standard output and standard error before starting any command. A new file tests/test_cli_runner_flush.py sends the output to a file and checks that a line printed before the command comes before the command's own line. CHANGELOG.md gains one line.

## Files changed

- CHANGELOG.md
- src/socialagent/cli/_runner.py
- tests/test_cli_runner_flush.py

## How to use the fix

1. Get a copy of the project awslabs/social-messaging-agent-runtime-toolkit.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 99-social-messaging-agent-runtime-toolkit-69.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 69.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The new test uses a small Python child process and not Terraform so the test is lighter than the test the bug report describes. The chatbot modelled the ordering in a scratch script: the parent line came last without the flush and first with the flush. The chatbot did not run the project's tests. Fixes 72 and 96 and 97 and 99 on this shelf each add a line at the same spot of CHANGELOG.md so those patches do not apply one after another: apply one patch and add the other changelog lines by hand. The other files in those patches do not overlap.

## Search words

socialagent deploy header after terraform output stdout not a terminal block buffered flush _runner.py run subprocess

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 6ecb773..d90cfcf 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -4,6 +4,9 @@ All notable changes to SMART, the Social Messaging Agent Runtime Toolkit, are re
 
 ## [Unreleased]
 
+### Fixed
+- The CLI flushes its own output before it starts a command, so `socialagent deploy` prints its header and notices before Terraform's output when stdout is a file or a pipe.
+
 ## [2026.10.0] - 2026-11-05
 
 The first public release. Everything below was in the toolkit when it was published.
diff --git a/src/socialagent/cli/_runner.py b/src/socialagent/cli/_runner.py
index 6dd1266..cc55f7b 100644
--- a/src/socialagent/cli/_runner.py
+++ b/src/socialagent/cli/_runner.py
@@ -22,9 +22,11 @@ a fake instead of needing a real ``terraform`` on PATH.
 
 from __future__ import annotations
 
+import contextlib
 import shlex
 import signal
 import subprocess
+import sys
 import threading
 from collections.abc import Callable, Mapping, Sequence
 from dataclasses import dataclass
@@ -79,6 +81,13 @@ def run(
     argv = [str(c) for c in cmd]
     shown = shlex.join(argv)
     pipe = subprocess.PIPE if capture else None
+    # The child writes straight to the inherited file descriptors. When stdout
+    # is a file or a pipe Python block-buffers it, so lines the CLI printed
+    # before this call would otherwise land after the child's output.
+    for stream in (sys.stdout, sys.stderr):
+        # A closed or broken stream must not stop the command.
+        with contextlib.suppress(OSError, ValueError):
+            stream.flush()
     try:
         proc = subprocess.Popen(  # noqa: S603 — argv list, no shell
             argv,
diff --git a/tests/test_cli_runner_flush.py b/tests/test_cli_runner_flush.py
new file mode 100644
index 0000000..17e52dd
--- /dev/null
+++ b/tests/test_cli_runner_flush.py
@@ -0,0 +1,35 @@
+# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
+# SPDX-License-Identifier: Apache-2.0
+
+"""``run`` flushes the CLI's own buffered output before the child writes."""
+
+from __future__ import annotations
+
+import subprocess
+import sys
+
+_SCRIPT = """
+import sys
+from socialagent.cli._runner import run
+
+print("parent line")
+print("parent error line", file=sys.stderr)
+run([sys.executable, "-c", "print('child line')"])
+"""
+
+
+def test_lines_printed_before_run_precede_the_child_output_in_a_file(tmp_path):
+    """With stdout redirected to a file Python block-buffers it, so the lines
+    the CLI printed before a command used to appear after the command's output."""
+    log = tmp_path / "out.log"
+    with log.open("w", encoding="utf-8") as fh:
+        subprocess.run(  # noqa: S603 - argv list, no shell
+            [sys.executable, "-c", _SCRIPT],
+            stdout=fh,
+            stderr=subprocess.STDOUT,
+            check=True,
+        )
+
+    lines = log.read_text(encoding="utf-8").splitlines()
+    assert lines.index("parent line") < lines.index("child line")
+    assert lines.index("parent error line") < lines.index("child line")
`````

[Back to the shelf](README.md)
