# Fix 55: Threesmith: review and assets hide every finding when --limit is abc or 0

Status: UNSENT and UNTESTED. Free to take.

- Project: laaielichter/Threesmith
- Bug report title: review and assets: `--limit abc` or `--limit 0` hides every finding
- Bug report: number 26 ([open the bug report](https://github.com/laaielichter/Threesmith/issues/26))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/55-threesmith-26.patch](fixes/55-threesmith-26.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/55-threesmith-26.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-55-threesmith-26.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-55-threesmith-26.html

## The bug

threesmith review and threesmith assets never checked the --limit value. --limit abc became NaN and --limit 0 became 0 and the report printed no finding at all. A script with a mistyped limit got a clean-looking report.

## The fix

The review action and the assets action in src/program.ts now call the existing positiveInt helper at the top. A bad value stops with the message from the bug report and exit code 2. test/cli.test.ts gains a case for both commands.

## Files changed

- src/program.ts
- test/cli.test.ts

## How to use the fix

1. Get a copy of the project laaielichter/Threesmith.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 55-threesmith-26.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 26.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report says the lessons command has the same gap and that including lessons is optional. The fix does not include lessons. The bug report ends with an invitation to comment before taking the work. The chatbot posts nothing so no comment was made. Anyone who sends this fix should comment first. The new test runs only when the built command line (dist/cli.js) exists. Fixes 55 and 56 and 57 all change src/program.ts in different places and apply together.

## Search words

Threesmith review assets --limit abc 0 NaN hides findings positiveInt whole number of 1 or more exit code 2

## The full patch

`````diff
diff --git a/src/program.ts b/src/program.ts
index 4e68e8d..ef4885b 100644
--- a/src/program.ts
+++ b/src/program.ts
@@ -158,6 +158,7 @@ export function buildProgram(): Command {
     .option("--disable <rules>", "comma separated rule ids to skip")
     .action(
       (path: string, o: { three?: string; json?: boolean; markdown?: boolean; sarif?: string; compact?: boolean; limit: string; minScore?: string; failOn: string; disable?: string }) => {
+        const limit = positiveInt("--limit", o.limit);
         const disable = o.disable ? parseRuleList(o.disable, "--disable") : undefined;
         const { review: r, learned } = applyFeedback(review({ path, ...(o.three ? { three: o.three } : {}), ...(disable ? { disable } : {}) }));
         const note = formatLearned(learned);
@@ -166,7 +167,7 @@ export function buildProgram(): Command {
           mkdirSync(dirname(o.sarif), { recursive: true });
           writeFileSync(o.sarif, JSON.stringify(toSarif(r), null, 1) + "\n");
         }
-        out(o.json ? JSON.stringify(r, null, 2) : o.markdown ? formatMarkdown(r, { limit: Number(o.limit) }) : o.compact ? formatCompact(r, { limit: Number(o.limit) }) : formatText(r, { limit: Number(o.limit) }));
+        out(o.json ? JSON.stringify(r, null, 2) : o.markdown ? formatMarkdown(r, { limit }) : o.compact ? formatCompact(r, { limit }) : formatText(r, { limit }));
         const rank: Record<string, number> = { error: 0, warn: 1, info: 2 };
         if (o.failOn !== "none" && r.findings.some((f) => (rank[f.severity] ?? 9) <= (rank[o.failOn] ?? -1))) process.exitCode = 1;
         if (o.minScore !== undefined && r.score !== null && r.score < Number(o.minScore)) process.exitCode = 1;
@@ -669,9 +670,10 @@ export function buildProgram(): Command {
     .option("--limit <n>", "max problems shown", "50")
     .option("--json", "JSON output")
     .action((path: string, o: { limit: string; json?: boolean }) => {
+      const limit = positiveInt("--limit", o.limit);
       const root = projectRootOf(path);
       const r = checkAssets(root, collect(root).files);
-      out(o.json ? JSON.stringify(r, null, 2) : formatAssets(r, { limit: Number(o.limit) }));
+      out(o.json ? JSON.stringify(r, null, 2) : formatAssets(r, { limit }));
       if (r.problems.some((p) => p.severity === "error")) process.exitCode = 1;
     });
 
diff --git a/test/cli.test.ts b/test/cli.test.ts
index 7bb3bd5..f5e01e4 100644
--- a/test/cli.test.ts
+++ b/test/cli.test.ts
@@ -62,6 +62,24 @@ describe.skipIf(!existsSync("dist/cli.js"))("built cli", () => {
     expect(goodLimit.stdout.toString()).toContain("Vector3");
   });
 
+  it("rejects a --limit that is not a whole number of 1 or more, for review and for assets", () => {
+    const example = "examples/agent-mistakes";
+    for (const [command, value] of [["review", "abc"], ["review", "0"], ["assets", "abc"], ["assets", "0"], ["assets", "-3"], ["review", "1.5"]] as const) {
+      const bad = spawnSync("node", ["dist/cli.js", command, example, "--limit", value]);
+      expect(bad.status, `${command} --limit ${value}`).toBe(2);
+      expect(bad.stderr.toString()).toContain(`threesmith: --limit must be a whole number of 1 or more (got "${value}")`);
+      expect(bad.stdout.toString()).toBe("");
+    }
+
+    // Valid limits behave as before: the same exit code as the default, and findings are printed.
+    const byDefault = spawnSync("node", ["dist/cli.js", "review", example]);
+    const one = spawnSync("node", ["dist/cli.js", "review", example, "--limit", "1"]);
+    expect(one.status).toBe(byDefault.status);
+    expect(one.stdout.toString()).toContain("Threesmith review:");
+    const assets = spawnSync("node", ["dist/cli.js", "assets", example, "--limit", "50"]);
+    expect(assets.stdout.toString()).toContain("Assets:");
+  });
+
   it("rejects unknown lesson filters and keeps the valid ones working", () => {
     const badTopic = spawnSync("node", ["dist/cli.js", "lessons", "--topic", "shadowz", "shadow"]);
     expect(badTopic.status).toBe(2);
`````

[Back to the shelf](README.md)
