# Fix 18: huri-modules: test_install.sh reads $target before setting the variable (SC2318)

Status: UNSENT and UNTESTED. Free to take.

- Project: Lucy-Robotics/huri-modules
- Bug report title: test_install.sh: prepare_workdir reads $target before it sets it (SC2318)
- Bug report: number 14 ([open the bug report](https://github.com/Lucy-Robotics/huri-modules/issues/14))
- Project license: GPL-3.0
- Language: Bash
- Test included: no
- Patch file: [fixes/18-huri-modules-14.patch](fixes/18-huri-modules-14.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/18-huri-modules-14.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-18-huri-modules-14.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-18-huri-modules-14.html

## The bug

In scripts/test_install.sh the function prepare_workdir declares local target="$1" dir="$WORK_BASE/$target" on one line. Bash expands $target in the second assignment before the first assignment has taken effect. The function works only because the caller's loop variable has the same name. shellcheck reports the line as SC2318.

## The fix

The fix splits the line into two local statements so dir is built from the function's own target. The chatbot confirmed with bash -n that the script still parses. shellcheck was not available to the chatbot.

## Files changed

- scripts/test_install.sh

## How to use the fix

1. Get a copy of the project Lucy-Robotics/huri-modules.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 18-huri-modules-14.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 14.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 9 November 2026 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 9 November 2026 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.

## Search words

huri-modules test_install.sh prepare_workdir SC2318 local target dir same line shellcheck bash

## The full patch

`````diff
diff --git a/scripts/test_install.sh b/scripts/test_install.sh
index b6f4f34..a41618d 100755
--- a/scripts/test_install.sh
+++ b/scripts/test_install.sh
@@ -93,7 +93,8 @@ else
 fi
 
 prepare_workdir() { # prepare_workdir <target> -> echoes the path
-  local target="$1" dir="$WORK_BASE/$target"
+  local target="$1"
+  local dir="$WORK_BASE/$target"
   # Guard the rm: this runs unattended and HURI_TEST_WORKDIR is user-supplied.
   # Refuse anything that is not a scratch path we would have created ourselves.
   case "$dir" in
`````

[Back to the shelf](README.md)
