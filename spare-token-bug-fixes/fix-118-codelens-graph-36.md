# Fix 118: codelens-graph: on Windows unchecking a folder that is spelled with different capital letters fails

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: Windows: unchecking a folder spelled with different letter case fails
- Bug report: number 36 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/36))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/118-codelens-graph-36.patch](fixes/118-codelens-graph-36.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/118-codelens-graph-36.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-118-codelens-graph-36.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-118-codelens-graph-36.html

## The bug

On Windows folder names are compared without regard to capital letters everywhere except one comparison. With the folder Src selected unchecking src treated Src as a parent folder and selected its subfolders and did not remove the folder.

## The fix

toggleFolder in src/ingestion/indexScope.ts now compares the two names with the same helper the rest of the file uses. The existing Windows-only test in test/ingestion/indexScope.test.ts loses its todo mark. changelog.md gains one line.

## Files changed

- changelog.md
- src/ingestion/indexScope.ts
- test/ingestion/indexScope.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 118-codelens-graph-36.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 36.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The test only runs on Windows and the chatbot works on Linux so the chatbot checked the rule with a scratch copy that has case folding switched on. The bug report asks people to comment before starting and the chatbot made no comment. Anyone who sends this fix should comment first. This patch applies together with fix 102 or fix 103 and its changelog line collides with fix 104: add that changelog line by hand when both are wanted.

## Search words

codelens-graph indexScope toggleFolder Windows case-insensitive includeFolders Src src uncheck folder ancestor

## The full patch

`````diff
diff --git a/changelog.md b/changelog.md
index 2986438..da87d4d 100644
--- a/changelog.md
+++ b/changelog.md
@@ -9,6 +9,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 ### Fixed
 - **CommonJS `require()` is understood as an import** (#8, thanks @Sebxxs004 in #9). `const { dbAll } = require('./db')`, `const db = require('./db')` and renamed forms like `const { dbAll: myDb } = require('./db')` no longer cause false "undefined" warnings on the functions that use them, calls link to the required file even when another file has a function with the same name, and CommonJS files now show which files they import. Nodes named after the pattern (`{ dbAll, dbGet }`) are gone.
 - **Calls into npm packages and Node built-ins** are no longer linked to an unrelated workspace symbol that happens to share the name (e.g. `path.normalize()` or `fast-deep-equal`'s `equal()`). Packages count as external when installed in `node_modules` or declared in `package.json`; workspace packages (symlinked or `workspace:`/`file:`/`link:`) and path aliases such as `@/utils` still link into the workspace.
+- On Windows, unchecking a folder that is selected under a different spelling (`Src` and `src`) removes the folder. It used to select the folder's subfolders instead.
 - **Import hints match the project's module system**: CommonJS files get `const { x } = require(…)` instead of an ES-module `import`. "Import as" paths are now relative to the workspace root (they were relative to the symbol's own folder), and `codelens_node` no longer suggests a JavaScript import for Java, Go, C# and other languages.
 - **Arrow functions are now real symbols.** `const f = () => {}`, `const f = function () {}` and class fields like `handler = () => {}` were indexed as variables (or not at all), so the calls inside them were lost. They are now functions and methods with parameters, return types and call links, which adds a lot of call links in modern TypeScript and React code.
 - **Fewer false "undefined" warnings**: default, rest and destructured parameters in JavaScript (`function f({ items }, ...rest)`) are recognized, and HTML tags in JSX (`<div>`) and standard globals (`Uint8Array`, `TextEncoder`, `setImmediate`, …) are no longer flagged. Missing components like `<Missing />` still are.
diff --git a/src/ingestion/indexScope.ts b/src/ingestion/indexScope.ts
index ef77206..1af2829 100644
--- a/src/ingestion/indexScope.ts
+++ b/src/ingestion/indexScope.ts
@@ -87,7 +87,8 @@ export function toggleFolder(
   // Unchecking: drop the folder itself and anything selected inside it.
   const withoutTarget = folders.filter(f => !isWithin(f, target));
   const ancestor = folders.length
-    ? folders.find(f => f !== target && isWithin(target, f))
+    // `key` folds case on Windows, where `Src` and `src` are the same folder and not a parent of it.
+    ? folders.find(f => key(f) !== key(target) && isWithin(target, f))
     : '';
   if (ancestor === undefined) {
     return withoutTarget.length ? withoutTarget : null;
diff --git a/test/ingestion/indexScope.test.ts b/test/ingestion/indexScope.test.ts
index 7734203..588dfd3 100644
--- a/test/ingestion/indexScope.test.ts
+++ b/test/ingestion/indexScope.test.ts
@@ -193,7 +193,7 @@ describe('toggleFolder', () => {
   });
 
   it('on Windows, unchecking a selected folder spelled differently removes it',
-    { skip: !isWin, todo: 'BUG #36: indexScope.ts:90 compares `f !== target` case-sensitively, so ["Src"] unchecking "src" treats Src as an ancestor and selects its children instead of removing it' },
+    { skip: !isWin },
     () => {
       // On Windows, listing "Src" or "src" reads the same directory.
       const winFs = (relDir: string) => (relDir.toLowerCase() === 'src' ? ['a', 'b'] : relDir === '' ? ['src'] : []);
`````

[Back to the shelf](README.md)
