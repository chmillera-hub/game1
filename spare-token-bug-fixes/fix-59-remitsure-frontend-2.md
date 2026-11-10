# Fix 59: remitsure-frontend: the receipt page keeps polling after the remittance is settled

Status: UNSENT and UNTESTED. Free to take.

- Project: remitsure/remitsure-frontend
- Bug report title: Receipt keeps polling after the remittance is settled
- Bug report: number 2 ([open the bug report](https://github.com/remitsure/remitsure-frontend/issues/2))
- Project license: MIT
- Language: TypeScript (React)
- Test included: yes
- Patch file: [fixes/59-remitsure-frontend-2.patch](fixes/59-remitsure-frontend-2.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/59-remitsure-frontend-2.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-59-remitsure-frontend-2.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-59-remitsure-frontend-2.html

## The bug

The receipt page asked the API for the remittance every 8 seconds forever. A remittance that is claimed or rejected or refunded can never change again. Every open receipt tab kept sending requests for nothing.

## The fix

src/lib/api.ts gains isFinalStatus. The receipt page loads once and runs the 8 second refresh only while the remittance is not final. src/lib/__tests__/api.test.ts gains tests for isFinalStatus. CHANGELOG.md gains a line.

## Files changed

- CHANGELOG.md
- src/app/(app)/r/[id]/page.tsx
- src/lib/__tests__/api.test.ts
- src/lib/api.ts

## How to use the fix

1. Get a copy of the project remitsure/remitsure-frontend.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 59-remitsure-frontend-2.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 2.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The test covers the helper function only. The project has no test setup for pages so the stopping of the timer itself has no test. After a person claims or rejects or refunds on the page two follow-up loads (after 4 and 9 seconds) still run once each and one of the two may land after the final status is shown. Fixes 59 and 60 change the same lines of the receipt page. Applying both needs a small manual merge. Fix 95 on this shelf changes the same page and the same spot of CHANGELOG.md so the two patches do not apply together.

## Search words

remitsure receipt page polling setInterval 8 seconds CLAIMED REJECTED REFUNDED final status stop load

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index e2100b5..0833ea4 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -7,3 +7,7 @@ All notable changes to this repo are listed here. The format follows [Keep a Cha
 ### Added
 
 - Initial MVP scaffold.
+
+### Fixed
+
+- The receipt page stops polling the API once a remittance is claimed, rejected or refunded.
diff --git a/src/app/(app)/r/[id]/page.tsx b/src/app/(app)/r/[id]/page.tsx
index 350631b..8889ca0 100644
--- a/src/app/(app)/r/[id]/page.tsx
+++ b/src/app/(app)/r/[id]/page.tsx
@@ -6,7 +6,7 @@ import { CategoryTag, StatusBadge, VerifiedBadge } from "@/components/Badges";
 import { Notice } from "@/components/Notice";
 import { TxError } from "@/components/TxError";
 import { useWallet } from "@/components/WalletProvider";
-import { api, NotFoundError, type RemittanceDetail } from "@/lib/api";
+import { api, isFinalStatus, NotFoundError, type RemittanceDetail } from "@/lib/api";
 import { config, explorerAccount, explorerTx } from "@/lib/config";
 import { remitsure } from "@/lib/contract";
 import { formatDate, fromUnits, relativeTime, shortAddress } from "@/lib/format";
@@ -50,14 +50,22 @@ export default function Receipt() {
     [id],
   );
 
+  // A settled remittance never changes again, so the refresh stops with it: no more API
+  // requests from an open receipt tab, and no clock tick (it only drives the countdown).
+  const settled = r !== null && isFinalStatus(r.status);
+
   useEffect(() => {
     load();
+  }, [load]);
+
+  useEffect(() => {
+    if (settled) return;
     const t = setInterval(() => {
       setNow(Date.now());
       load();
     }, 8_000);
     return () => clearInterval(t);
-  }, [load]);
+  }, [load, settled]);
 
   async function run(action: Action) {
     if (!address) return connect();
diff --git a/src/lib/__tests__/api.test.ts b/src/lib/__tests__/api.test.ts
index 0f231bd..dc85534 100644
--- a/src/lib/__tests__/api.test.ts
+++ b/src/lib/__tests__/api.test.ts
@@ -1,5 +1,5 @@
 import { afterEach, describe, expect, it, vi } from "vitest";
-import { get, NotFoundError } from "../api";
+import { get, isFinalStatus, NotFoundError } from "../api";
 
 const json = (status: number, body: unknown = {}) =>
   new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
@@ -36,3 +36,13 @@ describe("get", () => {
     expect(fetchMock).toHaveBeenCalledTimes(2);
   });
 });
+
+describe("isFinalStatus", () => {
+  it("is false only while a remittance is pending, so the receipt keeps refreshing", () => {
+    expect(isFinalStatus("PENDING")).toBe(false);
+  });
+
+  it.each(["CLAIMED", "REJECTED", "REFUNDED"] as const)("is true for %s, so the receipt stops polling", (status) => {
+    expect(isFinalStatus(status)).toBe(true);
+  });
+});
diff --git a/src/lib/api.ts b/src/lib/api.ts
index 56fafd5..b23b47b 100644
--- a/src/lib/api.ts
+++ b/src/lib/api.ts
@@ -3,6 +3,11 @@ import { config } from "./config";
 export type PayeeCategory = "SCHOOL" | "LANDLORD" | "HOSPITAL" | "UTILITY" | "OTHER";
 export type RemittanceStatus = "PENDING" | "CLAIMED" | "REJECTED" | "REFUNDED";
 
+/** A claimed, rejected or refunded remittance can never change again; only a pending one can. */
+export function isFinalStatus(status: RemittanceStatus): boolean {
+  return status !== "PENDING";
+}
+
 export interface Payee {
   address: string;
   name: string;
`````

[Back to the shelf](README.md)
