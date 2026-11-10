# Fix 138: codelens-graph: files with the .cjs extension are not indexed at all

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: Index `.cjs` files
- Bug report: number 47 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/47))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/138-codelens-graph-47.patch](fixes/138-codelens-graph-47.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/138-codelens-graph-47.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-138-codelens-graph-47.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-138-codelens-graph-47.html

## The bug

Files ending in .mjs were indexed as JavaScript. Files ending in .cjs (explicit CommonJS) were skipped so a CommonJS project that uses the .cjs extension was invisible to CodeLens.

## The fix

.cjs is added to EXTENSION_MAP in src/ingestion/astParser.ts and to IMPORT_EXTENSIONS in src/graph/graphDB.ts and to the default extension lists in package.json and src/extension.ts and src/mcp/mcpServer.ts. A new file test/cjs_extension.test.ts parses a .cjs file and checks that require('./x.cjs') and require('./x') both link to the .cjs file. changelog.md gains one line.

## Files changed

- changelog.md
- package.json
- src/extension.ts
- src/graph/graphDB.ts
- src/ingestion/astParser.ts
- src/mcp/mcpServer.ts
- test/cjs_extension.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 138-codelens-graph-47.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 47.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report says to comment on the report before starting: nobody commented so comment first. The package.json default list has no .mjs entry and the patch leaves that as found. PARSER_VERSION is not raised because stored results for already indexed files do not change. The chatbot did not run the tests or the TypeScript compiler. Fixes 138 and 139 and 140 on this shelf apply one after another.

## Search words

codelens-graph .cjs CommonJS extension EXTENSION_MAP IMPORT_EXTENSIONS supportedExtensions astParser graphDB require not indexed

## The full patch

`````diff
diff --git a/changelog.md b/changelog.md
index 2986438..80941f5 100644
--- a/changelog.md
+++ b/changelog.md
@@ -14,6 +14,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 - **Fewer false "undefined" warnings**: default, rest and destructured parameters in JavaScript (`function f({ items }, ...rest)`) are recognized, and HTML tags in JSX (`<div>`) and standard globals (`Uint8Array`, `TextEncoder`, `setImmediate`, …) are no longer flagged. Missing components like `<Missing />` still are.
 - **The MCP server could index a second workspace without its call graph.** Only the first parser in a process worked properly; later ones silently fell back to regex parsing, which finds no calls or parameters.
 - **Importing a folder now links to its index file** (`require('./lib')` → `lib/index.js`, Python packages → `__init__.py`). Previously no link was created.
+- **`.cjs` files are indexed.** Explicit CommonJS files were skipped entirely; they are now parsed as JavaScript, and `require('./x')` and `require('./x.cjs')` link to them. `.cjs` is part of the default `codeLensGraph.supportedExtensions` setting.
 - **Calls through an aliased import keep their link** when the imported file is edited (`import { helper as h }`). Previously the link was lost until a full rebuild.
 - **CodeLens no longer damages your files when updating its section**: front matter in `CLAUDE.md` and similar files is kept, a leftover CodeLens marker no longer causes the text after it to be deleted, and removing the CodeLens block from `.gitignore` no longer merges the lines around it.
 - `codelens_clear_config` no longer recreates `.codelens` and starts re-indexing right after clearing it.
diff --git a/package.json b/package.json
index 4dcd27d..d2d87f4 100644
--- a/package.json
+++ b/package.json
@@ -251,6 +251,7 @@
             ".tsx",
             ".js",
             ".jsx",
+            ".cjs",
             ".py",
             ".go",
             ".rs",
diff --git a/src/extension.ts b/src/extension.ts
index d2bbf09..4dab030 100644
--- a/src/extension.ts
+++ b/src/extension.ts
@@ -805,7 +805,7 @@ function getConfig() {
     includeFolders:         normalizeFolders(cfg.get<string[]>('includeFolders', [])),
     largeWorkspaceThreshold: cfg.get<number>('largeWorkspaceThreshold', 5000),
     supportedExtensions:    cfg.get<string[]>('supportedExtensions',
-      ['.ts','.tsx','.js','.jsx','.mjs','.py','.go','.rs','.java','.cs','.cpp','.c','.rb','.php','.swift','.kt']),
+      ['.ts','.tsx','.js','.jsx','.mjs','.cjs','.py','.go','.rs','.java','.cs','.cpp','.c','.rb','.php','.swift','.kt']),
   };
 }
 
diff --git a/src/graph/graphDB.ts b/src/graph/graphDB.ts
index cfde56b..5662c4c 100644
--- a/src/graph/graphDB.ts
+++ b/src/graph/graphDB.ts
@@ -149,7 +149,7 @@ export interface FileLine {
 
 // ─── Relationship resolution helpers ─────────────────────────────────────────
 
-const IMPORT_EXTENSIONS = ['.ts','.tsx','.js','.jsx','.mjs','.py','.go','.rs','.java','.cs','.cpp','.c','.rb','.php','.swift','.kt'];
+const IMPORT_EXTENSIONS = ['.ts','.tsx','.js','.jsx','.mjs','.cjs','.py','.go','.rs','.java','.cs','.cpp','.c','.rb','.php','.swift','.kt'];
 
 // A full resolve can take seconds on large workspaces; it commits and hands
 // the shared extension-host thread back this often.
diff --git a/src/ingestion/astParser.ts b/src/ingestion/astParser.ts
index 3e62698..ce9f37c 100644
--- a/src/ingestion/astParser.ts
+++ b/src/ingestion/astParser.ts
@@ -19,6 +19,7 @@ const EXTENSION_MAP: Record<string, { language: string; wasm: string }> = {
   '.js':   { language: 'javascript', wasm: 'tree-sitter-javascript.wasm' },
   '.jsx':  { language: 'javascript', wasm: 'tree-sitter-javascript.wasm' },
   '.mjs':  { language: 'javascript', wasm: 'tree-sitter-javascript.wasm' },
+  '.cjs':  { language: 'javascript', wasm: 'tree-sitter-javascript.wasm' },
   '.py':   { language: 'python',     wasm: 'tree-sitter-python.wasm'     },
   '.go':   { language: 'go',         wasm: 'tree-sitter-go.wasm'         },
   '.rs':   { language: 'rust',       wasm: 'tree-sitter-rust.wasm'       },
diff --git a/src/mcp/mcpServer.ts b/src/mcp/mcpServer.ts
index d929517..40ac061 100644
--- a/src/mcp/mcpServer.ts
+++ b/src/mcp/mcpServer.ts
@@ -290,7 +290,7 @@ export class MCPServer {
               '**/DerivedData/**', '**/xcuserdata/**', '**/.build/**',
             ],
             supportedExtensions: [
-              '.ts','.tsx','.js','.jsx','.mjs',
+              '.ts','.tsx','.js','.jsx','.mjs','.cjs',
               '.py','.go','.rs','.java','.cs',
               '.cpp','.c','.rb','.php','.swift','.kt',
             ],
diff --git a/test/cjs_extension.test.ts b/test/cjs_extension.test.ts
new file mode 100644
index 0000000..b8e5993
--- /dev/null
+++ b/test/cjs_extension.test.ts
@@ -0,0 +1,39 @@
+import { describe, it, before, after } from 'node:test';
+import assert from 'node:assert/strict';
+import { TestWorkspace } from './helpers';
+
+// Explicit CommonJS files (.cjs) are indexed like .js files, and imports of
+// them resolve with and without the extension.
+describe('.cjs files', () => {
+  const ws = new TestWorkspace();
+  const options = { supportedExtensions: ['.js', '.cjs'] };
+
+  before(async () => {
+    ws.write('lib/db.cjs', 'function dbAll(sql) { return [sql]; }\nmodule.exports = { dbAll };\n');
+    ws.write('withExt.js', "const { dbAll } = require('./lib/db.cjs');\nfunction listUsers() { return dbAll('users'); }\nmodule.exports = { listUsers };\n");
+    ws.write('withoutExt.cjs', "const { dbAll } = require('./lib/db');\nfunction listOrders() { return dbAll('orders'); }\nmodule.exports = { listOrders };\n");
+    await ws.scan(options);
+  });
+
+  after(() => ws.close());
+
+  it('parses a .cjs file as javascript', async () => {
+    const parsed = await ws.parser.parseFileAsync(ws.path('lib/db.cjs'));
+
+    assert.equal(parsed.language, 'javascript');
+    assert.ok(parsed.nodes.find(n => n.type === 'function' && n.name === 'dbAll'));
+  });
+
+  it('indexes symbols declared in .cjs files', () => {
+    assert.equal(ws.node('dbAll', 'lib/db.cjs').type, 'function');
+    assert.equal(ws.node('listOrders', 'withoutExt.cjs').type, 'function');
+  });
+
+  it("resolves require('./x.cjs') to the .cjs file", () => {
+    assert.deepEqual(ws.callsFrom('listUsers', 'withExt.js'), ['dbAll@lib/db.cjs']);
+  });
+
+  it("resolves require('./x') to x.cjs", () => {
+    assert.deepEqual(ws.callsFrom('listOrders', 'withoutExt.cjs'), ['dbAll@lib/db.cjs']);
+  });
+});
`````

[Back to the shelf](README.md)
