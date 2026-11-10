# Fix 32: kraft docs: the storage guide's policy.yaml block reads like a whole file

Status: UNSENT and UNTESTED. Free to take.

- Project: itsOmidKarami/kraft
- Bug report title: Docs: the storage guide's policy.yaml block reads like a whole file
- Bug report: number 1347 ([open the bug report](https://github.com/itsOmidKarami/kraft/issues/1347))
- Project license: Apache-2.0
- Language: Markdown (docs)
- Test included: no
- Patch file: [fixes/32-kraft-1347.patch](fixes/32-kraft-1347.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/32-kraft-1347.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-32-kraft-1347.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-32-kraft-1347.html

## The bug

The guide section Limit the disk worktrees use shows a storage block captioned config/policy.yaml. A reader can take the block for the whole file. Kraft refuses a policy.yaml that has no default key.

## The fix

docsite/content/3.guides/4.run/05.logs-and-disk-space.md now says in both places to edit the existing policy.yaml in ~/.kraft/config/ (or $KRAFT_HOME/config/) and that the storage block is already in the file commented out and to uncomment the block and not replace the file. The YAML examples and captions are kept.

## Files changed

- docsite/content/3.guides/4.run/05.logs-and-disk-space.md

## How to use the fix

1. Get a copy of the project itsOmidKarami/kraft.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 32-kraft-1347.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1347.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- This fix changes documentation only so no test is included. The project's docs checks (just ci-checks) were not run. The bug report asks people to comment on the bug report before starting and the chatbot made no comment. Anyone who sends this fix should comment first.

## Search words

kraft docs logs-and-disk-space policy.yaml storage worktrees limit quota auto_cleanup default key uncomment KRAFT_HOME

## The full patch

`````diff
diff --git a/docsite/content/3.guides/4.run/05.logs-and-disk-space.md b/docsite/content/3.guides/4.run/05.logs-and-disk-space.md
index b701600..fcff66d 100644
--- a/docsite/content/3.guides/4.run/05.logs-and-disk-space.md
+++ b/docsite/content/3.guides/4.run/05.logs-and-disk-space.md
@@ -105,7 +105,13 @@ item's documents and session logs stay readable on its page.
 _Added in 2.1_
 
 Without a limit, worktrees use disk until you notice. Set one in `policy.yaml`
-and Kraft tells you before the disk is full, and holds new starts at the limit:
+and Kraft tells you before the disk is full, and holds new starts at the limit.
+
+Edit the `policy.yaml` you already have, in `~/.kraft/config/` (or
+`$KRAFT_HOME/config/` if you set `KRAFT_HOME`). The `storage:` block is already
+in it, commented out: uncomment it and set your sizes. Don't replace the file
+with the block below. It is one part of the file, and Kraft refuses a
+`policy.yaml` without its `default:` key.
 
 ```yaml [config/policy.yaml]
 storage:
@@ -167,7 +173,10 @@ preview refuses one: it has no worktree to reclaim.
 
 An instance left running unattended can sit held with nobody to clean up. Add
 `auto_cleanup` and Kraft archives finished items itself when worktrees pass
-the limit:
+the limit. It goes in the same `storage:` block of your existing `policy.yaml`
+in `~/.kraft/config/` (or `$KRAFT_HOME/config/`). The seeded file has the
+`auto_cleanup` lines there too, commented out: uncomment them rather than
+replace the file with this block.
 
 ```yaml [config/policy.yaml]
 storage:
`````

[Back to the shelf](README.md)
