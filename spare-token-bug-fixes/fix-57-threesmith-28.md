# Fix 57: Threesmith: model lint ignores --max-triangles abc and the model scores 100 out of 100

Status: UNSENT and UNTESTED. Free to take.

- Project: laaielichter/Threesmith
- Bug report title: model lint: `--max-triangles abc` is ignored and the model scores 100/100
- Bug report: number 28 ([open the bug report](https://github.com/laaielichter/Threesmith/issues/28))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/57-threesmith-28.patch](fixes/57-threesmith-28.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/57-threesmith-28.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-57-threesmith-28.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-57-threesmith-28.html

## The bug

threesmith model lint takes --max-triangles and --max-draw-calls as budgets. A value that is not a number became NaN and every comparison against NaN is false. The budget was dropped without a word and the report said everything is fine.

## The fix

The model lint action in src/program.ts now calls the existing positiveInt helper for each of the two options when the option is given. A bad value stops with the message from the bug report and exit code 2. A new file test/cli-model-lint-budgets.test.ts checks four bad values and that a valid budget still works.

## Files changed

- src/program.ts
- test/cli-model-lint-budgets.test.ts

## How to use the fix

1. Get a copy of the project laaielichter/Threesmith.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 57-threesmith-28.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 28.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The test lives in a new file so the three Threesmith fixes do not collide. The bug report ends with an invitation to comment before taking the work and the chatbot made no comment. Anyone who sends this fix should comment first. The new test runs only when the built command line (dist/cli.js) exists.

## Search words

Threesmith model lint --max-triangles --max-draw-calls abc NaN budget ignored 100/100 positiveInt exit code 2

## The full patch

`````diff
diff --git a/src/program.ts b/src/program.ts
index 4e68e8d..ee490b5 100644
--- a/src/program.ts
+++ b/src/program.ts
@@ -460,7 +460,10 @@ export function buildProgram(): Command {
     .option("--full", "every finding")
     .option("--json", "JSON output")
     .action((file: string, o: { archetype?: string; maxTriangles?: string; maxDrawCalls?: string; full?: boolean; json?: boolean }) => {
-      const r = lintModelFile(file, { ...(o.archetype ? { archetype: o.archetype } : {}), ...(o.maxTriangles ? { maxTriangles: Number(o.maxTriangles) } : {}), ...(o.maxDrawCalls ? { maxDrawCalls: Number(o.maxDrawCalls) } : {}) });
+      // A budget that is not a number used to be dropped without a word: every comparison against NaN is false.
+      const maxTriangles = o.maxTriangles === undefined ? undefined : positiveInt("--max-triangles", o.maxTriangles);
+      const maxDrawCalls = o.maxDrawCalls === undefined ? undefined : positiveInt("--max-draw-calls", o.maxDrawCalls);
+      const r = lintModelFile(file, { ...(o.archetype ? { archetype: o.archetype } : {}), ...(maxTriangles === undefined ? {} : { maxTriangles }), ...(maxDrawCalls === undefined ? {} : { maxDrawCalls }) });
       out(o.json ? JSON.stringify(r, null, 2) : formatLint(r, o.full ? "full" : "brief"));
       if (r.failed) process.exitCode = 1;
     });
diff --git a/test/cli-model-lint-budgets.test.ts b/test/cli-model-lint-budgets.test.ts
new file mode 100644
index 0000000..51f006e
--- /dev/null
+++ b/test/cli-model-lint-budgets.test.ts
@@ -0,0 +1,26 @@
+import { spawnSync } from "node:child_process";
+import { existsSync } from "node:fs";
+import { describe, expect, it } from "vitest";
+
+const ROBOT = "examples/agent-mistakes/public/models/robot.glb";
+
+describe.skipIf(!existsSync("dist/cli.js"))("built cli: model lint budgets", () => {
+  it.each([
+    ["--max-triangles", "abc"],
+    ["--max-triangles", "1.5"],
+    ["--max-draw-calls", "0"],
+    ["--max-draw-calls", "-5"],
+  ])("refuses %s %s", (option, value) => {
+    // The joined form, so `-5` is not read as another option.
+    const bad = spawnSync("node", ["dist/cli.js", "model", "lint", ROBOT, `${option}=${value}`]);
+    expect(bad.status).toBe(2);
+    expect(bad.stderr.toString()).toContain(`threesmith: ${option} must be a whole number of 1 or more (got "${value}")`);
+    expect(bad.stdout.toString()).toBe("");
+  });
+
+  it("keeps a valid budget working", () => {
+    const roomy = spawnSync("node", ["dist/cli.js", "model", "lint", ROBOT, "--max-triangles", "100000"]);
+    expect(roomy.status).toBe(0);
+    expect(roomy.stdout.toString()).toContain("Model lint:");
+  });
+});
`````

[Back to the shelf](README.md)
