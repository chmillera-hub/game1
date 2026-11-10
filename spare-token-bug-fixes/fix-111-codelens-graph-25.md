# Fix 111: codelens-graph: the snippet of a one-line function includes the code that follows it

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: One-line symbols pull the following code into their snippet
- Bug report: number 25 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/25))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/111-codelens-graph-25.patch](fixes/111-codelens-graph-25.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/111-codelens-graph-25.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-111-codelens-graph-25.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-111-codelens-graph-25.html

## The bug

Snippet extraction treated a symbol that starts and ends on the same line as having no known end and returned 12 lines. The snippet of a one-line function included the next functions which wasted tokens and confused readers.

## The fix

src/context/snippetExtractor.ts now accepts an end line equal to the start line so a one-line symbol gives a one-line snippet. The existing test in test/context/snippet_extractor.test.ts loses its todo mark. changelog.md gains one line.

## Files changed

- changelog.md
- src/context/snippetExtractor.ts
- test/context/snippet_extractor.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 111-codelens-graph-25.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 25.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The one-character change is the change the bug report suggests. The bug report asks people to comment before starting and the chatbot made no comment. Anyone who sends this fix should comment first. The test already existed in the project marked as todo and the patch removes the todo mark. The chatbot did not run the project's tests. Fixes 102 and 103 and 104 for this project apply one after another. Fixes 110 and 111 and 112 each add a changelog line next to one of those lines so each of them needs its changelog line added by hand when another codelens-graph fix from this shelf is already applied.

## Search words

codelens-graph snippetExtractor extractSnippet endLine > line one-line symbol 12 lines bleed following code

## The full patch

`````diff
diff --git a/changelog.md b/changelog.md
index 2986438..9c4a813 100644
--- a/changelog.md
+++ b/changelog.md
@@ -14,6 +14,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 - **Fewer false "undefined" warnings**: default, rest and destructured parameters in JavaScript (`function f({ items }, ...rest)`) are recognized, and HTML tags in JSX (`<div>`) and standard globals (`Uint8Array`, `TextEncoder`, `setImmediate`, …) are no longer flagged. Missing components like `<Missing />` still are.
 - **The MCP server could index a second workspace without its call graph.** Only the first parser in a process worked properly; later ones silently fell back to regex parsing, which finds no calls or parameters.
 - **Importing a folder now links to its index file** (`require('./lib')` → `lib/index.js`, Python packages → `__init__.py`). Previously no link was created.
+- Snippets of one-line functions and constants stop at that line. They used to include up to 12 lines of the code that follows.
 - **Calls through an aliased import keep their link** when the imported file is edited (`import { helper as h }`). Previously the link was lost until a full rebuild.
 - **CodeLens no longer damages your files when updating its section**: front matter in `CLAUDE.md` and similar files is kept, a leftover CodeLens marker no longer causes the text after it to be deleted, and removing the CodeLens block from `.gitignore` no longer merges the lines around it.
 - `codelens_clear_config` no longer recreates `.codelens` and starts re-indexing right after clearing it.
diff --git a/src/context/snippetExtractor.ts b/src/context/snippetExtractor.ts
index 8fb2b8a..0880707 100644
--- a/src/context/snippetExtractor.ts
+++ b/src/context/snippetExtractor.ts
@@ -35,7 +35,8 @@ export class SnippetExtractor {
       const start = Math.max(0, node.line - 1);           // line is 1-based
       const end   = Math.min(
         lines.length,
-        node.endLine > node.line
+        // `>=`: a one-line symbol has endLine === line and its end is known too.
+        node.endLine >= node.line
           ? Math.min(node.endLine, start + MAX_SNIPPET_LINES)
           : start + MAX_SNIPPET_LINES
       );
diff --git a/test/context/snippet_extractor.test.ts b/test/context/snippet_extractor.test.ts
index c43dda3..7044a2d 100644
--- a/test/context/snippet_extractor.test.ts
+++ b/test/context/snippet_extractor.test.ts
@@ -80,7 +80,7 @@ describe('SnippetExtractor.extractSnippet', () => {
     assert.equal(extractor.extractSnippet(makeNode({ name: 'dir', filePath: ws.path('src') })), null);
   });
 
-  it('does not bleed a one-line symbol into the following code', { todo: 'BUG #25: snippetExtractor.ts:173 uses endLine > line, so a symbol with endLine === line gets 12 lines' }, () => {
+  it('does not bleed a one-line symbol into the following code', () => {
     const node = ws.node('first', 'src/oneLiners.ts');
     assert.equal(node.line, node.endLine, 'parser reports a one-line function');
     const snippet = extractor.extractSnippet(node)!;
`````

[Back to the shelf](README.md)
