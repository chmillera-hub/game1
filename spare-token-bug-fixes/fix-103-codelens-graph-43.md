# Fix 103: codelens-graph: function parameters with non-English names are dropped

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: Parameters with non-ASCII names are dropped
- Bug report: number 43 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/43))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/103-codelens-graph-43.patch](fixes/103-codelens-graph-43.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/103-codelens-graph-43.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-103-codelens-graph-43.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-103-codelens-graph-43.html

## The bug

Parameter names had to match a pattern that only allows English letters and digits and the underscore. A function such as café(ñame: number) was stored with no parameters and the parameter was then flagged as undefined inside the function.

## The fix

src/ingestion/astParser.ts gains IDENTIFIER_RE which accepts letters of any language (the pattern the bug report suggests) and extractParams uses the new pattern. PARSER_VERSION goes from 3 to 4 because the project's own comment says to raise the number whenever stored parse results change. The existing test in test/parser/robustness.test.ts loses its todo mark. changelog.md gains one line.

## Files changed

- changelog.md
- src/ingestion/astParser.ts
- test/parser/robustness.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 103-codelens-graph-43.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 43.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Raising PARSER_VERSION makes every existing index re-parse every file once. The bug report does not mention the version number and the chatbot raised the number because of the comment above the constant. A name that starts with a digit is no longer accepted and a name with a dollar sign is now accepted. Three other places in the file keep the old English-only pattern (import names and local variables) and are outside this fix. The chatbot compared the old and new patterns in a scratch script. The bug report asks people to comment before starting and the chatbot made no comment. Anyone who sends this fix should comment first. The test already existed in the project marked as todo and the patch removes the todo mark. The chatbot did not run the project's tests. Fixes 102 and 103 and 104 for this project apply one after another. Fixes 110 and 111 and 112 each add a changelog line next to one of those lines so each of them needs its changelog line added by hand when another codelens-graph fix from this shelf is already applied.

## Search words

codelens-graph astParser extractParams non-ASCII parameter names \w unicode identifier café ñ undefined warning PARSER_VERSION

## The full patch

`````diff
diff --git a/changelog.md b/changelog.md
index 2986438..f507e90 100644
--- a/changelog.md
+++ b/changelog.md
@@ -12,6 +12,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 - **Import hints match the project's module system**: CommonJS files get `const { x } = require(…)` instead of an ES-module `import`. "Import as" paths are now relative to the workspace root (they were relative to the symbol's own folder), and `codelens_node` no longer suggests a JavaScript import for Java, Go, C# and other languages.
 - **Arrow functions are now real symbols.** `const f = () => {}`, `const f = function () {}` and class fields like `handler = () => {}` were indexed as variables (or not at all), so the calls inside them were lost. They are now functions and methods with parameters, return types and call links, which adds a lot of call links in modern TypeScript and React code.
 - **Fewer false "undefined" warnings**: default, rest and destructured parameters in JavaScript (`function f({ items }, ...rest)`) are recognized, and HTML tags in JSX (`<div>`) and standard globals (`Uint8Array`, `TextEncoder`, `setImmediate`, …) are no longer flagged. Missing components like `<Missing />` still are.
+- Parameters with non-English names (`ñame`, `größe`) are kept. They were dropped and then flagged as undefined inside the function that declares them.
 - **The MCP server could index a second workspace without its call graph.** Only the first parser in a process worked properly; later ones silently fell back to regex parsing, which finds no calls or parameters.
 - **Importing a folder now links to its index file** (`require('./lib')` → `lib/index.js`, Python packages → `__init__.py`). Previously no link was created.
 - **Calls through an aliased import keep their link** when the imported file is edited (`import { helper as h }`). Previously the link was lost until a full rebuild.
diff --git a/src/ingestion/astParser.ts b/src/ingestion/astParser.ts
index 3e62698..c0a8df1 100644
--- a/src/ingestion/astParser.ts
+++ b/src/ingestion/astParser.ts
@@ -9,10 +9,15 @@ import { isConfigPath, isNodeModulePath } from '../utils';
 // every file once on the next scan, so existing users get the fix without a
 // manual rebuild. 2: CommonJS require() imports (#9). 3: arrow-function symbols,
 // JS default/rest/destructured params, no JSX intrinsics in undefinedRefs.
-export const PARSER_VERSION = '3';
+// 4: parameters with non-ASCII names are kept.
+export const PARSER_VERSION = '4';
 
 // ─── Language → WASM mapping ──────────────────────────────────────────────────
 
+// A parameter name as written in source. `\w` is ASCII-only and dropped names
+// such as `ñame` or `größe`, which were then reported as undefined.
+const IDENTIFIER_RE = /^[\p{L}\p{Nl}$_][\p{L}\p{Nl}\p{Mn}\p{Mc}\p{Nd}\p{Pc}$]*$/u;
+
 const EXTENSION_MAP: Record<string, { language: string; wasm: string }> = {
   '.ts':   { language: 'typescript', wasm: 'tree-sitter-typescript.wasm' },
   '.tsx':  { language: 'tsx',        wasm: 'tree-sitter-tsx.wasm'        },
@@ -877,7 +882,7 @@ export class TreeSitterParser {
           for (const name of new Set(names)) { params.push({ name, rest: false }); }
         } else {
           const name     = nameNode.text.replace(/^\.\.\./, '').trim();
-          if (name && /^\w+$/.test(name)) {
+          if (name && IDENTIFIER_RE.test(name)) {
             params.push({
               name,
               type:         typeNode?.text?.replace(/^:\s*/, '').trim(),
diff --git a/test/parser/robustness.test.ts b/test/parser/robustness.test.ts
index f72e38b..a9d2364 100644
--- a/test/parser/robustness.test.ts
+++ b/test/parser/robustness.test.ts
@@ -101,7 +101,7 @@ describe('Robustness', () => {
     assert.equal(get(p, 'afterEmoji').signature, 'function afterEmoji() { return s; }');
   });
 
-  it('keeps non-ASCII parameter names', { todo: 'BUG #43: params must match /^\\w+$/ (ASCII only), so `café(ñ: number)` has no params (astParser.ts:816)' }, async () => {
+  it('keeps non-ASCII parameter names', async () => {
     const p = await fx.parse('uni-params.ts', 'export function café(ñame: number, größe: string) { return ñame; }\n');
     assert.deepEqual(get(p, 'café').params?.map(x => x.name), ['ñame', 'größe']);
   });
`````

[Back to the shelf](README.md)
