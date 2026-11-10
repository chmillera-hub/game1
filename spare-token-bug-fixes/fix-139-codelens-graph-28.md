# Fix 139: codelens-graph: the per-tool token figures in the MCP usage report do not add up to the session total

Status: UNSENT and UNTESTED. Free to take.

- Project: Pranayd555/codelens-graph
- Bug report title: MCP usage report: per-tool token figures do not add up to the session total
- Bug report: number 28 ([open the bug report](https://github.com/Pranayd555/codelens-graph/issues/28))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/139-codelens-graph-28.patch](fixes/139-codelens-graph-28.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/139-codelens-graph-28.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-139-codelens-graph-28.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-139-codelens-graph-28.html

## The bug

formatUsageReport in src/mcp/mcpLogger.ts priced the tool breakdown from a fixed table (TOOL_TOKEN_COST) and not from the logged tokensEst of each call. The per-tool figures did not match the Tokens used total of the same session.

## The fix

The breakdown now sums the logged tokensEst per tool and the fixed table is removed. In test/context/mcp_logger.test.ts the waiting test loses its todo option and the test for an unknown tool now expects the logged figure (7) and not the old fallback (50). changelog.md gains one line.

## Files changed

- changelog.md
- src/mcp/mcpLogger.ts
- test/context/mcp_logger.test.ts

## How to use the fix

1. Get a copy of the project Pranayd555/codelens-graph.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 139-codelens-graph-28.patch
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
- The bug report says to comment on the report before starting: nobody commented so comment first. One existing test expected the old fallback of 50 tokens for an unknown tool and the patch changes that expectation. The chatbot did not run the tests. Fixes 138 and 139 and 140 on this shelf apply one after another.

## Search words

codelens-graph mcpLogger formatUsageReport TOOL_TOKEN_COST tokensEst per-tool breakdown Tokens used usage report

## The full patch

`````diff
diff --git a/changelog.md b/changelog.md
index 2986438..fbcadb8 100644
--- a/changelog.md
+++ b/changelog.md
@@ -17,6 +17,7 @@ All notable changes to the **CodeLens Graph** extension will be documented in th
 - **Calls through an aliased import keep their link** when the imported file is edited (`import { helper as h }`). Previously the link was lost until a full rebuild.
 - **CodeLens no longer damages your files when updating its section**: front matter in `CLAUDE.md` and similar files is kept, a leftover CodeLens marker no longer causes the text after it to be deleted, and removing the CodeLens block from `.gitignore` no longer merges the lines around it.
 - `codelens_clear_config` no longer recreates `.codelens` and starts re-indexing right after clearing it.
+- **The MCP usage report's per-tool token figures add up to the session's "Tokens used".** The tool breakdown was priced from a fixed table instead of the logged estimate of each call.
 - **The graph panel no longer freezes VS Code on large repos.** It built its data with two queries per symbol and drew every symbol, which on a 100k-symbol monorepo blocked the extension host for minutes. It now loads in about a second, and above 1,000 symbols it shows the most connected ones with their neighbours. Search and the filter buttons still find any symbol in the index.
 
 ### Security
diff --git a/src/mcp/mcpLogger.ts b/src/mcp/mcpLogger.ts
index 0123a57..048634a 100644
--- a/src/mcp/mcpLogger.ts
+++ b/src/mcp/mcpLogger.ts
@@ -21,20 +21,6 @@ export interface ToolCallLog {
   sessionId:  string;   // groups calls within one MCP session
 }
 
-// Approximate token cost per tool call (based on typical response sizes)
-const TOOL_TOKEN_COST: Record<string, number> = {
-  codelens_triage:       10,
-  codelens_search:       50,
-  codelens_node:         80,
-  codelens_files:        120,
-  codelens_relations:    100,
-  codelens_context:      400,
-  codelens_impact:       300,
-  codelens_status:       30,
-  codelens_text_search:  60,
-  codelens_dependencies: 80,
-};
-
 export class MCPLogger {
   private logPath: string;
   private sessionId: string;
@@ -162,6 +148,7 @@ export function formatUsageReport(logs: ToolCallLog[]): string {
     const totalTokens   = calls.reduce((s, c) => s + c.tokensEst, 0);
     const totalDuration = calls.reduce((s, c) => s + c.durationMs, 0);
     const toolCounts    = calls.reduce((m, c) => { m[c.tool]=(m[c.tool]||0)+1; return m; }, {} as Record<string,number>);
+    const toolTokens    = calls.reduce((m, c) => { m[c.tool]=(m[c.tool]||0)+c.tokensEst; return m; }, {} as Record<string,number>);
     const contextCalls  = toolCounts['codelens_context'] || 0;
     const searchCalls   = toolCounts['codelens_search']  || 0;
     const savedEst      = contextCalls * 1800 + searchCalls * 400;
@@ -174,8 +161,8 @@ export function formatUsageReport(logs: ToolCallLog[]): string {
     lines.push(`- Triage used: ${usedTriage ? '✅ yes' : '❌ no — agent skipped codelens_triage'}`);
     lines.push('- Tool breakdown:');
     for (const [tool, count] of Object.entries(toolCounts).sort(([,a],[,b]) => b-a)) {
-      const estCost = TOOL_TOKEN_COST[tool] ?? 50;
-      lines.push(`  · ${tool} ×${count} (~${estCost * count} tokens)`);
+      // The logged estimate of each call, so the breakdown adds up to "Tokens used".
+      lines.push(`  · ${tool} ×${count} (~${toolTokens[tool] ?? 0} tokens)`);
     }
 
     // Show individual calls
diff --git a/test/context/mcp_logger.test.ts b/test/context/mcp_logger.test.ts
index 43da973..f486167 100644
--- a/test/context/mcp_logger.test.ts
+++ b/test/context/mcp_logger.test.ts
@@ -217,8 +217,8 @@ describe('formatUsageReport', () => {
     const tools = [...old.matchAll(/^ {2}· (\S+) ×(\d+)/gm)].map(m => `${m[1]}×${m[2]}`);
     assert.equal(tools[0], 'codelens_search×2');
     assert.deepEqual(new Set(tools), new Set(['codelens_search×2', 'codelens_triage×1', 'codelens_context×1']));
-    // Unknown tools fall back to the default per-call estimate.
-    assert.match(sessionBlock(formatUsageReport(logs), 1), /· mystery_tool ×1 \(~50 tokens\)/);
+    // Unknown tools are priced from their logged estimate like every other tool.
+    assert.match(sessionBlock(formatUsageReport(logs), 1), /· mystery_tool ×1 \(~7 tokens\)/);
   });
 
   it('lists every call with its time, tool, trimmed input and cost', () => {
@@ -228,7 +228,7 @@ describe('formatUsageReport', () => {
     assert.match(old, new RegExp(`task="${'z'.repeat(60)}" → 500 tokens`), 'input values are cut to 60 characters');
   });
 
-  it('per-tool token figures agree with the session\'s "Tokens used"', { todo: 'BUG #28: mcpLogger.ts:403-404 prices the tool breakdown from a static table (TOOL_TOKEN_COST), not the logged tokensEst' }, () => {
+  it('per-tool token figures agree with the session\'s "Tokens used"', () => {
     const old = sessionBlock(formatUsageReport(logs), 2);
     const total = Number(old.match(/Tokens used: ~(\d+)/)![1]);
     const perTool = [...old.matchAll(/^ {2}· \S+ ×\d+ \(~(\d+) tokens\)$/gm)].reduce((s, m) => s + Number(m[1]), 0);
`````

[Back to the shelf](README.md)
