# Fix 104: codelens-graph: plain text search treats _ and % as wildcards

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: Literal text search treats `_` and `%` as wildcards
- Bug report: number 30 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/30))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/104-codelens-graph-30.patch](fixes/104-codelens-graph-30.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/104-codelens-graph-30.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-104-codelens-graph-30.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-104-codelens-graph-30.html

## The bug

Plain (non-regex) text search passed the search text to the database as a LIKE pattern without escaping. A search for user_id also returned userXid and a search for 100% returned every line that contains 100.

## The fix

src/graph/graphDB.ts gains likeContains which escapes the backslash and % and _ in the search text. searchFileLines and getTextEntriesByWord use the helper and add an ESCAPE clause to the query. The existing test in test/graph/graphDB.search.test.ts loses its todo mark. changelog.md gains one line.

## Files changed

- changelog.md
- src/graph/graphDB.ts
- test/graph/graphDB.search.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 104-codelens-graph-30.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 30.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran the same pattern rule against a real SQLite engine in a scratch script: user_id no longer matched userXid and 100% no longer matched 1000 and a search text with a backslash still matched. Fix 112 on this shelf changes another part of the same file. The bug report asks people to comment before starting and the chatbot made no comment. Anyone who sends this fix should comment first. The test already existed in the project marked as todo and the patch removes the todo mark. The chatbot did not run the project's tests. Fixes 102 and 103 and 104 for this project apply one after another. Fixes 110 and 111 and 112 each add a changelog line next to one of those lines so each of them needs its changelog line added by hand when another codelens-graph fix from this shelf is already applied.

## Search words

codelens-graph graphDB searchFileLines getTextEntriesByWord LIKE ESCAPE underscore percent wildcard literal text search codelens_text_search

## The full patch

`````diff
diff --git a/changelog.md b/changelog.md
index 2986438..cb7a34f 100644
--- a/changelog.md
+++ b/changelog.md
@@ -8,6 +8,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 
 ### Fixed
 - **CommonJS `require()` is understood as an import** (#8, thanks @Sebxxs004 in #9). `const { dbAll } = require('./db')`, `const db = require('./db')` and renamed forms like `const { dbAll: myDb } = require('./db')` no longer cause false "undefined" warnings on the functions that use them, calls link to the required file even when another file has a function with the same name, and CommonJS files now show which files they import. Nodes named after the pattern (`{ dbAll, dbGet }`) are gone.
+- Literal text search no longer treats `_` and `%` as wildcards: searching for `user_id` no longer also returns `userXid`, and `100%` no longer returns every line that contains `100`.
 - **Calls into npm packages and Node built-ins** are no longer linked to an unrelated workspace symbol that happens to share the name (e.g. `path.normalize()` or `fast-deep-equal`'s `equal()`). Packages count as external when installed in `node_modules` or declared in `package.json`; workspace packages (symlinked or `workspace:`/`file:`/`link:`) and path aliases such as `@/utils` still link into the workspace.
 - **Import hints match the project's module system**: CommonJS files get `const { x } = require(…)` instead of an ES-module `import`. "Import as" paths are now relative to the workspace root (they were relative to the symbol's own folder), and `codelens_node` no longer suggests a JavaScript import for Java, Go, C# and other languages.
 - **Arrow functions are now real symbols.** `const f = () => {}`, `const f = function () {}` and class fields like `handler = () => {}` were indexed as variables (or not at all), so the calls inside them were lost. They are now functions and methods with parameters, return types and call links, which adds a lot of call links in modern TypeScript and React code.
diff --git a/src/graph/graphDB.ts b/src/graph/graphDB.ts
index cfde56b..83a36a2 100644
--- a/src/graph/graphDB.ts
+++ b/src/graph/graphDB.ts
@@ -12,6 +12,12 @@ import {
 
 const SEARCH_TIME_BUDGET_MS = 3000;
 
+// A LIKE pattern that finds `text` anywhere in a line as literal text. `\`, `%`
+// and `_` are escaped so they are not wildcards; use it with `ESCAPE '\'`.
+function likeContains(text: string): string {
+  return `%${text.replace(/[\\%_]/g, '\\$&')}%`;
+}
+
 // ─── Schema ───────────────────────────────────────────────────────────────────
 // Storage is keyed by integers and workspace-relative paths. Earlier versions
 // stored absolute-path string ids in every row and index (a node id is
@@ -1753,8 +1759,8 @@ export class GraphDB {
     this.refreshFromDiskIfChanged();
     const stmt = this.db.prepare(`SELECT f.id, f.path, l.line, l.raw_text, l.token_type
                                   FROM file_lines l JOIN files f ON l.file_id = f.id
-                                  WHERE lower(l.raw_text) LIKE ?`);
-    stmt.bind([`%${word.toLowerCase()}%`]);
+                                  WHERE lower(l.raw_text) LIKE ? ESCAPE '\\'`);
+    stmt.bind([likeContains(word.toLowerCase())]);
     const results: any[] = [];
     while (stmt.step()) {
       const [fileId, stored, line, rawText, tokenType] = stmt.get() as [number, string, number, string, string];
@@ -1803,8 +1809,8 @@ export class GraphDB {
     `;
     const params: any[] = [];
     if (!regex) {
-      sql += ' AND lower(l.raw_text) LIKE ?';
-      params.push(`%${normalizedQuery.toLowerCase()}%`);
+      sql += ` AND lower(l.raw_text) LIKE ? ESCAPE '\\'`;
+      params.push(likeContains(normalizedQuery.toLowerCase()));
     }
 
     const stmt = this.db.prepare(sql);
diff --git a/test/graph/graphDB.search.test.ts b/test/graph/graphDB.search.test.ts
index c9f14f6..0b46746 100644
--- a/test/graph/graphDB.search.test.ts
+++ b/test/graph/graphDB.search.test.ts
@@ -121,9 +121,7 @@ describe('GraphDB text lines', () => {
     assert.deepEqual(hits(db.searchFileLines('render(', undefined, false, false, 50)), ['a:3']);
   });
 
-  it('literal search does not treat _ or % as wildcards', {
-    todo: 'BUG #30: literal searchFileLines/getTextEntriesByWord use LIKE without ESCAPE and no JS re-check, so "_" and "%" match any characters',
-  }, () => {
+  it('literal search does not treat _ or % as wildcards', () => {
     assert.deepEqual(hits(db.searchFileLines('user_id', undefined, false, false, 50)), ['a:7']);
     assert.deepEqual(db.getTextEntriesByWord('user_id', true).map(e => e.line), [7]);
   });
`````

[Back to the shelf](README.md)
