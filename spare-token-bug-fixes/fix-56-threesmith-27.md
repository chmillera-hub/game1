# Fix 56: Threesmith: undo --steps abc says Nothing to undo and --steps 0 undoes one write

Status: UNSENT and UNTESTED. Free to take.

- Project: laaielichter/Threesmith
- Bug report title: undo: `--steps abc` says "Nothing to undo." and `--steps 0` undoes one write
- Bug report: number 27 ([open the bug report](https://github.com/laaielichter/Threesmith/issues/27))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/56-threesmith-27.patch](fixes/56-threesmith-27.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/56-threesmith-27.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-56-threesmith-27.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-56-threesmith-27.html

## The bug

threesmith undo never checked the --steps value. --steps abc undid nothing and said Nothing to undo even with a write in the journal. --steps 0 undid one write that the person did not ask to undo.

## The fix

The undo action in src/program.ts now calls the existing positiveInt helper before anything is touched. A bad value stops with the message from the bug report and exit code 2. A new file test/cli-undo-steps.test.ts checks four bad values and that no file changes and that a valid count still restores the file.

## Files changed

- src/program.ts
- test/cli-undo-steps.test.ts

## How to use the fix

1. Get a copy of the project laaielichter/Threesmith.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 56-threesmith-27.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 27.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- undo --list together with a bad --steps value is now refused too. The bug report says --list ignores --steps. The test lives in a new file so the three Threesmith fixes do not collide. The bug report ends with an invitation to comment before taking the work and the chatbot made no comment. Anyone who sends this fix should comment first. The new test runs only when the built command line (dist/cli.js) exists.

## Search words

Threesmith undo --steps abc 0 Nothing to undo NaN positiveInt journal whole number of 1 or more exit code 2

## The full patch

`````diff
diff --git a/src/program.ts b/src/program.ts
index 4e68e8d..e64e1ab 100644
--- a/src/program.ts
+++ b/src/program.ts
@@ -699,8 +699,10 @@ export function buildProgram(): Command {
     .option("--list", "only show the journal")
     .action((dir: string | undefined, o: { path: string; steps: string; force?: boolean; list?: boolean }) => {
       if (dir) o.path = dir;
+      // Checked before anything is touched: `--steps abc` used to undo nothing and say so, `--steps 0` undid one write.
+      const steps = positiveInt("--steps", o.steps);
       const root = projectRootOf(o.path);
-      out(o.list ? formatJournal(readJournal(root)) : formatUndo(undoJournal(root, { steps: Number(o.steps), ...(o.force ? { force: true } : {}) })));
+      out(o.list ? formatJournal(readJournal(root)) : formatUndo(undoJournal(root, { steps, ...(o.force ? { force: true } : {}) })));
     });
 
   program
diff --git a/test/cli-undo-steps.test.ts b/test/cli-undo-steps.test.ts
new file mode 100644
index 0000000..010b512
--- /dev/null
+++ b/test/cli-undo-steps.test.ts
@@ -0,0 +1,34 @@
+import { spawnSync } from "node:child_process";
+import { existsSync, readFileSync } from "node:fs";
+import { join } from "node:path";
+import { describe, expect, it } from "vitest";
+import { readJournal, writeFiles } from "../src/project/journal.js";
+import { project } from "./helpers.js";
+
+describe.skipIf(!existsSync("dist/cli.js"))("built cli: undo --steps", () => {
+  it("refuses a count that is not a whole number of 1 or more, and changes no file", () => {
+    const dir = project({ "package.json": "{}", "a.js": "old" });
+    writeFiles(dir, "test", "one file", [{ file: "a.js", data: "new" }]);
+
+    for (const value of ["abc", "0", "-2", "1.5"]) {
+      // `--steps=-2`: the joined form, so the value is not read as another option.
+      const bad = spawnSync("node", ["dist/cli.js", "undo", dir, `--steps=${value}`]);
+      expect(bad.status, `--steps ${value}`).toBe(2);
+      expect(bad.stderr.toString()).toContain(`threesmith: --steps must be a whole number of 1 or more (got "${value}")`);
+      expect(readFileSync(join(dir, "a.js"), "utf8")).toBe("new");
+      expect(readJournal(dir)).toHaveLength(1);
+    }
+
+    const good = spawnSync("node", ["dist/cli.js", "undo", dir, "--steps", "1"]);
+    expect(good.status).toBe(0);
+    expect(readFileSync(join(dir, "a.js"), "utf8")).toBe("old");
+    expect(readJournal(dir)).toHaveLength(0);
+  });
+
+  it("undoes one write by default", () => {
+    const dir = project({ "package.json": "{}", "a.js": "old" });
+    writeFiles(dir, "test", "one file", [{ file: "a.js", data: "new" }]);
+    expect(spawnSync("node", ["dist/cli.js", "undo", dir]).status).toBe(0);
+    expect(readFileSync(join(dir, "a.js"), "utf8")).toBe("old");
+  });
+});
`````

[Back to the shelf](README.md)
