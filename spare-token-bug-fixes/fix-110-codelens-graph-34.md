# Fix 110: codelens-graph: safe regex searches such as \d{1,3} are searched as plain text

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: Safe regex searches like `\d{1,3}` fall back to literal text
- Bug report: number 34 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/34))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/110-codelens-graph-34.patch](fixes/110-codelens-graph-34.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/110-codelens-graph-34.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-110-codelens-graph-34.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-110-codelens-graph-34.html

## The bug

The check that rejects risky regex patterns counted a bounded repeat such as {1,3} as unbounded. A pattern such as an IP address pattern with four bounded repeats was rejected and silently searched as plain text which returned nothing.

## The fix

src/utils.ts now treats only the form {n,} (no upper limit) as unbounded which is the change the bug report suggests. The existing test in test/ingestion/utils.test.ts loses its todo mark. changelog.md gains one line.

## Files changed

- changelog.md
- src/utils.ts
- test/ingestion/utils.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 110-codelens-graph-34.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 34.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- A very large bounded repeat such as {1,100000} now also counts as bounded. The chatbot checked the three forms of the repeat in a scratch script. The bug report asks people to comment before starting and the chatbot made no comment. Anyone who sends this fix should comment first. The test already existed in the project marked as todo and the patch removes the todo mark. The chatbot did not run the project's tests. Fixes 102 and 103 and 104 for this project apply one after another. Fixes 110 and 111 and 112 each add a changelog line next to one of those lines so each of them needs its changelog line added by hand when another codelens-graph fix from this shelf is already applied.

## Search words

codelens-graph compileSearchRegex bounded quantifier {n,m} unbounded brace[3] regex rejected literal fallback

## The full patch

`````diff
diff --git a/changelog.md b/changelog.md
index 2986438..a96843b 100644
--- a/changelog.md
+++ b/changelog.md
@@ -10,6 +10,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 - **CommonJS `require()` is understood as an import** (#8, thanks @Sebxxs004 in #9). `const { dbAll } = require('./db')`, `const db = require('./db')` and renamed forms like `const { dbAll: myDb } = require('./db')` no longer cause false "undefined" warnings on the functions that use them, calls link to the required file even when another file has a function with the same name, and CommonJS files now show which files they import. Nodes named after the pattern (`{ dbAll, dbGet }`) are gone.
 - **Calls into npm packages and Node built-ins** are no longer linked to an unrelated workspace symbol that happens to share the name (e.g. `path.normalize()` or `fast-deep-equal`'s `equal()`). Packages count as external when installed in `node_modules` or declared in `package.json`; workspace packages (symlinked or `workspace:`/`file:`/`link:`) and path aliases such as `@/utils` still link into the workspace.
 - **Import hints match the project's module system**: CommonJS files get `const { x } = require(…)` instead of an ES-module `import`. "Import as" paths are now relative to the workspace root (they were relative to the symbol's own folder), and `codelens_node` no longer suggests a JavaScript import for Java, Go, C# and other languages.
+- Regex searches with bounded repeats such as `\d{1,3}\.\d{1,3}` run as regexes. They were mistaken for risky patterns and silently searched as literal text, which returned nothing.
 - **Arrow functions are now real symbols.** `const f = () => {}`, `const f = function () {}` and class fields like `handler = () => {}` were indexed as variables (or not at all), so the calls inside them were lost. They are now functions and methods with parameters, return types and call links, which adds a lot of call links in modern TypeScript and React code.
 - **Fewer false "undefined" warnings**: default, rest and destructured parameters in JavaScript (`function f({ items }, ...rest)`) are recognized, and HTML tags in JSX (`<div>`) and standard globals (`Uint8Array`, `TextEncoder`, `setImmediate`, …) are no longer flagged. Missing components like `<Missing />` still are.
 - **The MCP server could index a second workspace without its call graph.** Only the first parser in a process worked properly; later ones silently fell back to regex parsing, which finds no calls or parameters.
diff --git a/src/utils.ts b/src/utils.ts
index 2de51b5..6b397fe 100644
--- a/src/utils.ts
+++ b/src/utils.ts
@@ -223,7 +223,9 @@ function isRegexBacktrackSafe(pattern: string): boolean {
 
     const brace = c === '{' ? /^\{(\d+)(,(\d*))?\}/.exec(pattern.slice(i)) : null;
     if (c === '*' || c === '+' || c === '?' || brace) {
-      const unbounded = c === '*' || c === '+' || (brace !== null && brace[2] !== undefined);
+      // Only `{n,}` has no upper bound: its third group is the empty string. `{n}` leaves the
+      // group undefined and `{n,m}` fills it, and neither can repeat without limit.
+      const unbounded = c === '*' || c === '+' || (brace !== null && brace[3] === '');
       if (unbounded) {
         if (prevAtomWasRiskyGroup) { return false; }
         if (++unboundedCount > 2) { return false; }
diff --git a/test/ingestion/utils.test.ts b/test/ingestion/utils.test.ts
index 9870270..e8ab50f 100644
--- a/test/ingestion/utils.test.ts
+++ b/test/ingestion/utils.test.ts
@@ -258,11 +258,9 @@ describe('compileSearchRegex', () => {
     assert.deepEqual(compileSearchRegex('a**'), { regex: null, rejected: false });
   });
 
-  it('accepts bounded {n,m} quantifiers (they cannot backtrack unboundedly)',
-    { todo: 'BUG #34: {n,m} counted as unbounded (src/utils.ts:226 checks brace[2] instead of brace[3] === ""), so e.g. \\d{1,3}\\.\\d{1,3}\\.\\d{1,3} is rejected' },
-    () => {
-      assert.ok(accepted('\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}'));
-    });
+  it('accepts bounded {n,m} quantifiers (they cannot backtrack unboundedly)', () => {
+    assert.ok(accepted('\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}'));
+  });
 });
 
 describe('regexTestCapped', () => {
`````

[Back to the shelf](README.md)
