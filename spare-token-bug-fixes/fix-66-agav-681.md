# Fix 66: agav: /undo with a mistyped argument reverts a file

Status: UNSENT and UNTESTED. Free to take.

- Project: prapaa-ai/agav
- Bug report title: fix(commands): reject unknown /undo arguments before reverting files
- Bug report: number 681 ([open the bug report](https://github.com/prapaa-ai/agav/issues/681))
- Project license: Apache-2.0
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/66-agav-681.patch](fixes/66-agav-681.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/66-agav-681.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-66-agav-681.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-66-agav-681.html

## The bug

The /undo command treated any unknown argument as a plain undo. A typo such as /undo lsit (meant as /undo list) reverted the last file change.

## The fix

source/commands/undo.ts now accepts only empty input (undo) or list (show the tracked changes). Any other argument returns the usage text and reverts nothing. The usage text now names list. A new file source/__tests__/commands.undo.test.ts checks unknown arguments and empty input and list.

## Files changed

- source/__tests__/commands.undo.test.ts
- source/commands/undo.ts

## How to use the fix

1. Get a copy of the project prapaa-ai/agav.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 66-agav-681.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 681.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The patch is written against the branch named beta because the bug report names beta as the target. The match for list is exact so /undo List also returns the usage text. Nobody ran the tests. The chatbot parsed both files with the TypeScript parser and found no syntax error.

## Search words

agav /undo unknown argument typo lsit reverts file performUndo usage list slash command

## The full patch

`````diff
diff --git a/source/__tests__/commands.undo.test.ts b/source/__tests__/commands.undo.test.ts
new file mode 100644
index 0000000..bee4a82
--- /dev/null
+++ b/source/__tests__/commands.undo.test.ts
@@ -0,0 +1,54 @@
+import { describe, it, expect, beforeEach, vi } from "vitest";
+
+vi.mock("../utils/undo.js", () => ({
+  performUndo: vi.fn(),
+  hasUndo: vi.fn(),
+  getUndoStack: vi.fn(),
+}));
+
+import { getUndoStack, hasUndo, performUndo } from "../utils/undo.js";
+import { undoCommand } from "../commands/undo.js";
+import type { CommandContext } from "../commands/types.js";
+
+const performUndoMock = vi.mocked(performUndo);
+const hasUndoMock = vi.mocked(hasUndo);
+const getUndoStackMock = vi.mocked(getUndoStack);
+const context = {} as CommandContext;
+
+describe("commands/undo", () => {
+  beforeEach(() => {
+    vi.clearAllMocks();
+    hasUndoMock.mockReturnValue(true);
+    performUndoMock.mockResolvedValue({ path: "src/a.ts", tool: "edit" });
+    getUndoStackMock.mockReturnValue([{ path: "src/a.ts", tool: "edit", timestamp: Date.now() }]);
+  });
+
+  it.each(["lsit", "List", "list all", "1", "--help"])("returns usage for the unknown argument %j and reverts nothing", async (args) => {
+    const result = await undoCommand.execute(args, context);
+
+    expect(result).toMatchObject({ type: "message" });
+    expect((result as { text: string }).text).toContain(`Unknown argument "${args}"`);
+    expect((result as { text: string }).text).toContain("Usage: /undo [list]");
+    expect(performUndoMock).not.toHaveBeenCalled();
+    expect(hasUndoMock).not.toHaveBeenCalled();
+  });
+
+  it.each(["", "   ", "\n"])("reverts the last change for empty input %j", async (args) => {
+    const result = await undoCommand.execute(args, context);
+
+    expect(performUndoMock).toHaveBeenCalledTimes(1);
+    expect(result).toEqual({ type: "message", text: "Reverted edit on src/a.ts" });
+  });
+
+  it.each(["list", "  list  "])("lists the tracked changes for %j without reverting", async (args) => {
+    const result = await undoCommand.execute(args, context);
+
+    expect(performUndoMock).not.toHaveBeenCalled();
+    expect((result as { text: string }).text).toContain("Undo stack:");
+    expect((result as { text: string }).text).toContain("src/a.ts");
+  });
+
+  it("names list in its usage", () => {
+    expect(undoCommand.usage).toContain("list");
+  });
+});
diff --git a/source/commands/undo.ts b/source/commands/undo.ts
index 380e540..05486d6 100644
--- a/source/commands/undo.ts
+++ b/source/commands/undo.ts
@@ -1,14 +1,23 @@
 import type { SlashCommand, CommandResult } from "./types.js"
 import { performUndo, hasUndo, getUndoStack } from "../utils/undo.js"
 
+const USAGE =
+  "Usage: /undo [list]\n\nRestores the previous version of the last file modified by the agent.\n`/undo list` shows the tracked changes without reverting anything.\nOnly tracks file writes and edits from the current session."
+
 /** Revert the most recent tracked file change. */
 export const undoCommand: SlashCommand = {
   name: "undo",
   description: "Revert the last file change",
   autoSubmit: true,
-  usage: "Usage: /undo\n\nRestores the previous version of the last file modified by the agent.\nOnly tracks file writes and edits from the current session.",
+  usage: USAGE,
   async execute(args: string): Promise<CommandResult> {
-    if (args.trim() === "list") {
+    const arg = args.trim()
+    // Only a bare `/undo` reverts. A typo such as `/undo lsit` must not cost a file its last change.
+    if (arg !== "" && arg !== "list") {
+      return { type: "message", text: `Unknown argument "${arg}".\n\n${USAGE}` }
+    }
+
+    if (arg === "list") {
       const stack = getUndoStack()
       if (stack.length === 0) {
         return { type: "message", text: "No changes to undo." }
`````

[Back to the shelf](README.md)
