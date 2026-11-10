# Fix 67: agent-custody: door receipts are exported to OpenTelemetry as CLIENT spans

Status: UNSENT and UNTESTED. Free to take.

- Project: svayatta/agent-custody
- Bug report title: OTel: export door receipts as SERVER spans, not CLIENT
- Bug report: number 265 ([open the bug report](https://github.com/svayatta/agent-custody/issues/265))
- Project license: Apache-2.0
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/67-agent-custody-265.patch](fixes/67-agent-custody-265.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/67-agent-custody-265.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-67-agent-custody-265.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-67-agent-custody-265.html

## The bug

Every receipt was exported as a span of kind 3 (CLIENT: the agent calling out). A door receipt records an inbound request to the business's own site or API. The span for a door receipt should be kind 2 (SERVER).

## The fix

packages/receipts/src/otel.ts sets kind 2 when the receipt's issuer kind is door and keeps kind 3 for every other issuer. The comment beside the line is updated. packages/receipts/test/otel.test.ts gains a case that checks the kind for a door receipt and for four other issuer kinds.

## Files changed

- packages/receipts/src/otel.ts
- packages/receipts/test/otel.test.ts

## How to use the fix

1. Get a copy of the project svayatta/agent-custody.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 67-agent-custody-265.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 265.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Nobody ran the tests (bun run ci). The chatbot parsed both files with the TypeScript parser and found no syntax error. The new test builds a minimal receipt by hand in the same way the neighbouring test does.

## Search words

agent-custody OpenTelemetry OTel otel.ts span kind SERVER CLIENT door receipt inbound request kind 2

## The full patch

`````diff
diff --git a/packages/receipts/src/otel.ts b/packages/receipts/src/otel.ts
index 0f85b9e..c200dcf 100644
--- a/packages/receipts/src/otel.ts
+++ b/packages/receipts/src/otel.ts
@@ -71,7 +71,8 @@ export function spanFor(p: ReceiptPredicate, bundle: ReceiptBundle, serviceName:
                 traceId,
                 spanId: traceId.slice(0, 16),
                 name: reconciliation ? `${p.tool.name} reconciliation` : `${p.tool.name}`,
-                kind: 3, // CLIENT: the agent calling out
+                // SERVER for a door receipt: an inbound request to the business's own site or API. CLIENT for every other issuer: the agent calling out
+                kind: p.issuer.kind === "door" ? 2 : 3,
                 startTimeUnixNano: start.toString(),
                 endTimeUnixNano: (end > start ? end : start).toString(),
                 attributes,
diff --git a/packages/receipts/test/otel.test.ts b/packages/receipts/test/otel.test.ts
index 91e90fa..5224e81 100644
--- a/packages/receipts/test/otel.test.ts
+++ b/packages/receipts/test/otel.test.ts
@@ -100,4 +100,12 @@ describe("OpenTelemetry export", () => {
     expect(span({ status: "executed", result: null, resultDigest: "x", provenance: "claimed" }).traceId).toBe("0f1e2d3c4b5a69788796a5b4c3d2e1f0");
     expect(() => otlpExporter({ url: "http://127.0.0.1:1", headersEnv: { authorization: "NOT_SET_ANYWHERE_OTEL" } })).toThrow(/NOT_SET_ANYWHERE_OTEL/);
   });
+
+  it("a door receipt is a SERVER span (kind 2); every other issuer stays a CLIENT span (kind 3)", () => {
+    const base = { receiptId: "0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0", timestamp: "2026-09-08T10:00:00.000Z", principal: { id: null, provenance: "claimed" as const }, agent: { id: "a", provenance: "claimed" as const }, session: { id: null, toolUseId: null, provenance: "claimed" as const }, model: { id: null, provenance: "claimed" as const }, tool: { name: "t", provenance: "claimed" as const }, request: { args: {}, argsDigest: "d", provenance: "claimed" as const }, facts: {}, policy: null, execution: { status: "executed", result: null, resultDigest: "x", provenance: "claimed" } };
+    const bundle = { envelope: { payloadType: "", payload: "", signatures: [] }, treeHead: { payloadType: "", payload: "", signatures: [] }, inclusion: { leafIndex: 3, treeSize: 4, hashes: [] } };
+    const kindOf = (issuerKind: string) => (spanFor({ ...base, issuer: { kind: issuerKind, keyid: "k", version: "0" } } as any, bundle, "svc") as any).resourceSpans[0].scopeSpans[0].spans[0].kind;
+    expect(kindOf("door")).toBe(2);
+    for (const other of ["sdk", "gateway", "egress", "guardian"]) expect(kindOf(other), other).toBe(3);
+  });
 });
`````

[Back to the shelf](README.md)
