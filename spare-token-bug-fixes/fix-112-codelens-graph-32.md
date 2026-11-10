# Fix 112: codelens-graph: the list of dependencies is rewritten on every scan for some package names

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: Dependency manifest is rewritten on every scan for some package names
- Bug report: number 32 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/32))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/112-codelens-graph-32.patch](fixes/112-codelens-graph-32.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/112-codelens-graph-32.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-112-codelens-graph-32.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-112-codelens-graph-32.html

## The bug

replacePackages decided whether the list changed by comparing the database's sort order with a different sort order in JavaScript. With names such as JSONStream next to axios the two orders differ so every scan looked like a change and the database was rewritten every time.

## The fix

src/graph/graphDB.ts now sorts the new rows in plain code order which is the order the database uses. The existing test in test/graph/graphDB.packages.test.ts loses its todo mark. changelog.md gains one line.

## Files changed

- changelog.md
- src/graph/graphDB.ts
- test/graph/graphDB.packages.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 112-codelens-graph-32.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 32.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot compared both orders against a real SQLite engine in a scratch script with twelve names: plain code order matched the database and the old order did not. Plain code order and the database order can still differ for rare characters outside the basic range which npm names do not use. Fix 104 on this shelf changes another part of the same file. The bug report asks people to comment before starting and the chatbot made no comment. Anyone who sends this fix should comment first. The test already existed in the project marked as todo and the patch removes the todo mark. The chatbot did not run the project's tests. Fixes 102 and 103 and 104 for this project apply one after another. Fixes 110 and 111 and 112 each add a changelog line next to one of those lines so each of them needs its changelog line added by hand when another codelens-graph fix from this shelf is already applied.

## Search words

codelens-graph replacePackages ORDER BY name localeCompare binary collation JSONStream axios rewritten every scan

## The full patch

`````diff
diff --git a/changelog.md b/changelog.md
index 2986438..4752ef5 100644
--- a/changelog.md
+++ b/changelog.md
@@ -18,6 +18,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 - **CodeLens no longer damages your files when updating its section**: front matter in `CLAUDE.md` and similar files is kept, a leftover CodeLens marker no longer causes the text after it to be deleted, and removing the CodeLens block from `.gitignore` no longer merges the lines around it.
 - `codelens_clear_config` no longer recreates `.codelens` and starts re-indexing right after clearing it.
 - **The graph panel no longer freezes VS Code on large repos.** It built its data with two queries per symbol and drew every symbol, which on a 100k-symbol monorepo blocked the extension host for minutes. It now loads in about a second, and above 1,000 symbols it shows the most connected ones with their neighbours. Search and the filter buttons still find any symbol in the index.
+- The dependency list is no longer rewritten on every scan when package names mix upper and lower case (for example `JSONStream` next to `axios`), which saves disk writes and startup time.
 
 ### Security
 - `codelens_dependencies` no longer reads type definition files outside the workspace, which a pre-built index could point it at.
diff --git a/src/graph/graphDB.ts b/src/graph/graphDB.ts
index cfde56b..4196014 100644
--- a/src/graph/graphDB.ts
+++ b/src/graph/graphDB.ts
@@ -780,7 +780,15 @@ export class GraphDB {
       p.version, rel(p.dir), rel(p.types), rel(p.main), rel(p.readme),
     ]);
     const current = this.db.exec('SELECT name, declared_range, kind, declared_in, installed, version, dir, types, main, readme FROM packages ORDER BY name')[0]?.values ?? [];
-    if (JSON.stringify(current) === JSON.stringify([...rows].sort((a, b) => String(a[0]).localeCompare(String(b[0]))))) {
+    // Sort the way SQLite's `ORDER BY name` does (plain code order), not with localeCompare:
+    // the two orders differ for names like `JSONStream` and `axios`, which made every scan
+    // look like a change.
+    const byName = (a: unknown[], b: unknown[]) => {
+      const x = String(a[0]);
+      const y = String(b[0]);
+      return x < y ? -1 : x > y ? 1 : 0;
+    };
+    if (JSON.stringify(current) === JSON.stringify([...rows].sort(byName))) {
       return false;
     }
 
diff --git a/test/graph/graphDB.packages.test.ts b/test/graph/graphDB.packages.test.ts
index 0972a69..da1ecb2 100644
--- a/test/graph/graphDB.packages.test.ts
+++ b/test/graph/graphDB.packages.test.ts
@@ -40,9 +40,7 @@ describe('GraphDB dependency manifest', () => {
     assert.equal(db.replacePackages([]), false);
   });
 
-  it('detects an unchanged manifest whatever the package-name casing and punctuation', {
-    todo: 'BUG #32: replacePackages compares SQLite\'s binary ORDER BY name with JS localeCompare order, so e.g. "JSONStream" + "axios" always reports a change and rewrites the DB',
-  }, () => {
+  it('detects an unchanged manifest whatever the package-name casing and punctuation', () => {
     const packages = [pkg('JSONStream'), pkg('axios'), pkg('a_b'), pkg('a.b')];
     assert.equal(db.replacePackages(packages), true);
     assert.equal(db.replacePackages(packages), false);
`````

[Back to the shelf](README.md)
