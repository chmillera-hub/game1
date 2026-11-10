# Fix 60: remitsure-frontend: an invalid receipt link says Could not reach the API instead of saying the link is not valid

Status: UNSENT and UNTESTED. Free to take.

- Project: remitsure/remitsure-frontend
- Bug report title: Invalid receipt ids show "Could not reach the API" instead of not found
- Bug report: number 1 ([open the bug report](https://github.com/remitsure/remitsure-frontend/issues/1))
- Project license: MIT
- Language: TypeScript (React)
- Test included: yes
- Patch file: [fixes/60-remitsure-frontend-1.patch](fixes/60-remitsure-frontend-1.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/60-remitsure-frontend-1.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-60-remitsure-frontend-1.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-60-remitsure-frontend-1.html

## The bug

The receipt page turned the id in the address into a number with no check. For /r/abc the API answered with an error and the page said Could not reach the RemitSure API. The message sent people looking for an outage. The page also kept asking for the bad id every 8 seconds.

## The fix

src/lib/format.ts gains parseReceiptId which accepts only a positive whole number. For any other value the receipt page shows This is not a valid receipt link and makes no API request and starts no refresh. src/lib/__tests__/format.test.ts gains tests for the helper.

## Files changed

- src/app/(app)/r/[id]/page.tsx
- src/lib/__tests__/format.test.ts
- src/lib/format.ts

## How to use the fix

1. Get a copy of the project remitsure/remitsure-frontend.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 60-remitsure-frontend-1.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The test covers the helper function only. The project has no test setup for pages. Fixes 59 and 60 change the same lines of the receipt page. Applying both needs a small manual merge. The chatbot checked the helper with a scratch script.

## Search words

remitsure receipt /r/abc invalid id NaN Could not reach the RemitSure API not a valid receipt link parseReceiptId

## The full patch

`````diff
diff --git a/src/app/(app)/r/[id]/page.tsx b/src/app/(app)/r/[id]/page.tsx
index 350631b..dd15f32 100644
--- a/src/app/(app)/r/[id]/page.tsx
+++ b/src/app/(app)/r/[id]/page.tsx
@@ -9,7 +9,7 @@ import { useWallet } from "@/components/WalletProvider";
 import { api, NotFoundError, type RemittanceDetail } from "@/lib/api";
 import { config, explorerAccount, explorerTx } from "@/lib/config";
 import { remitsure } from "@/lib/contract";
-import { formatDate, fromUnits, relativeTime, shortAddress } from "@/lib/format";
+import { formatDate, fromUnits, parseReceiptId, relativeTime, shortAddress } from "@/lib/format";
 
 type Action = "claim" | "reject" | "refund";
 
@@ -21,7 +21,8 @@ const labels: Record<Action, string> = {
 
 export default function Receipt() {
   const { id: rawId } = useParams<{ id: string }>();
-  const id = Number(rawId);
+  // null for a link that is not a receipt link (`/r/abc`, `/r/0`): nothing is asked of the API then.
+  const id = parseReceiptId(rawId);
   const { address, connect } = useWallet();
   const [r, setR] = useState<RemittanceDetail | null>(null);
   const [error, setError] = useState<string | null>(null);
@@ -34,32 +35,36 @@ export default function Receipt() {
 
   const load = useCallback(
     () =>
-      api
-        .remittance(id)
-        .then((data) => {
-          setR(data);
-          setError(null);
-        })
-        .catch((e) =>
-          setError(
-            e instanceof NotFoundError
-              ? "Receipt not found yet. If you just sent it, it will appear in a few seconds."
-              : "Could not reach the RemitSure API. It may be waking up.",
-          ),
-        ),
+      id === null
+        ? Promise.resolve()
+        : api
+            .remittance(id)
+            .then((data) => {
+              setR(data);
+              setError(null);
+            })
+            .catch((e) =>
+              setError(
+                e instanceof NotFoundError
+                  ? "Receipt not found yet. If you just sent it, it will appear in a few seconds."
+                  : "Could not reach the RemitSure API. It may be waking up.",
+              ),
+            ),
     [id],
   );
 
   useEffect(() => {
+    if (id === null) return;
     load();
     const t = setInterval(() => {
       setNow(Date.now());
       load();
     }, 8_000);
     return () => clearInterval(t);
-  }, [load]);
+  }, [id, load]);
 
   async function run(action: Action) {
+    if (id === null) return;
     if (!address) return connect();
     setBusy(action);
     setTxError(null);
@@ -81,6 +86,7 @@ export default function Receipt() {
     setTimeout(() => setCopied(false), 2_000);
   }
 
+  if (id === null) return <Notice tone="error">This is not a valid receipt link.</Notice>;
   if (!r) return <Notice tone={error ? "error" : "info"}>{error ?? "Loading receipt..."}</Notice>;
 
   const expired = new Date(r.expiresAt).getTime() <= now;
diff --git a/src/lib/__tests__/format.test.ts b/src/lib/__tests__/format.test.ts
index 3747b00..e39ea29 100644
--- a/src/lib/__tests__/format.test.ts
+++ b/src/lib/__tests__/format.test.ts
@@ -1,5 +1,5 @@
 import { describe, expect, it } from "vitest";
-import { fromUnits, relativeTime, shortAddress, toUnits } from "../format";
+import { fromUnits, parseReceiptId, relativeTime, shortAddress, toUnits } from "../format";
 
 describe("toUnits", () => {
   it("converts whole and decimal amounts", () => {
@@ -39,3 +39,21 @@ describe("relativeTime", () => {
     expect(relativeTime("2026-10-29T12:05:00Z", now)).toBe("in 5 minutes");
   });
 });
+
+describe("parseReceiptId", () => {
+  it("reads a positive whole number", () => {
+    expect(parseReceiptId("1")).toBe(1);
+    expect(parseReceiptId("42")).toBe(42);
+  });
+
+  it.each(["abc", "0", "-1", "1.5", "", " 7", "7abc", "1e3", "99999999999999999999"])(
+    "refuses %j, so no request is made for it",
+    (raw) => {
+      expect(parseReceiptId(raw)).toBeNull();
+    },
+  );
+
+  it("refuses a missing id", () => {
+    expect(parseReceiptId(undefined)).toBeNull();
+  });
+});
diff --git a/src/lib/format.ts b/src/lib/format.ts
index becd309..5c20e1d 100644
--- a/src/lib/format.ts
+++ b/src/lib/format.ts
@@ -51,3 +51,13 @@ export const categoryLabels = {
   UTILITY: "Utility",
   OTHER: "Other",
 } as const;
+
+/**
+ * The receipt id in a `/r/<id>` link: a positive whole number, or null when the
+ * link is not a receipt link at all (`abc`, `0`, `-1`, `1.5`, an empty value).
+ */
+export function parseReceiptId(raw: string | undefined): number | null {
+  if (raw === undefined || !/^[0-9]+$/.test(raw)) return null;
+  const id = Number(raw);
+  return Number.isSafeInteger(id) && id > 0 ? id : null;
+}
`````

[Back to the shelf](README.md)
