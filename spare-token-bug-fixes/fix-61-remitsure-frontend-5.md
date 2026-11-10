# Fix 61: remitsure-frontend: dashboard payee names only cover the first 20 payees

Status: UNSENT and UNTESTED. Free to take.

- Project: remitsure/remitsure-frontend
- Bug report title: Dashboard payee names only cover the first 20 payees
- Bug report: number 5 ([open the bug report](https://github.com/remitsure/remitsure-frontend/issues/5))
- Project license: MIT
- Language: TypeScript (React)
- Test included: yes
- Patch file: [fixes/61-remitsure-frontend-5.patch](fixes/61-remitsure-frontend-5.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/61-remitsure-frontend-5.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-61-remitsure-frontend-5.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-61-remitsure-frontend-5.html

## The bug

The dashboard built its name lookup from the payee list. The payee list returns only the first 20 payees. A payment to any other payee showed a raw address in place of the payee's name.

## The fix

src/lib/api.ts gains payeeNames which asks for each unique payee address once and returns the names. The dashboard uses payeeNames for the payees in the person's sent payments and no longer loads the payee list. A new file src/lib/__tests__/payee-names.test.ts checks one request per unique payee and that an unregistered payee is left out.

## Files changed

- src/app/(app)/dashboard/page.tsx
- src/lib/__tests__/payee-names.test.ts
- src/lib/api.ts

## How to use the fix

1. Get a copy of the project remitsure/remitsure-frontend.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 61-remitsure-frontend-5.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 5.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- When the lookup for one payee fails the row for that payee shows the address and the rest of the dashboard still loads. Before the fix a failed payee list request made the whole dashboard show an error. That handling is the chatbot's choice. The test covers the helper function only. Fix 61 applies together with fix 59 and together with fix 60.

## Search words

remitsure dashboard payee names first 20 payees api.payees raw address api.payee per unique address

## The full patch

`````diff
diff --git a/src/app/(app)/dashboard/page.tsx b/src/app/(app)/dashboard/page.tsx
index 8c9392e..8b13a3f 100644
--- a/src/app/(app)/dashboard/page.tsx
+++ b/src/app/(app)/dashboard/page.tsx
@@ -6,7 +6,7 @@ import { VerifiedBadge } from "@/components/Badges";
 import { Notice } from "@/components/Notice";
 import { RemittanceRow } from "@/components/RemittanceRow";
 import { useWallet } from "@/components/WalletProvider";
-import { api, NotFoundError, type Payee, type Remittance } from "@/lib/api";
+import { api, NotFoundError, payeeNames, type Payee, type Remittance } from "@/lib/api";
 import { shortAddress } from "@/lib/format";
 
 interface Data {
@@ -28,10 +28,11 @@ export default function Dashboard() {
       api.remittances({ sender: address }),
       api.remittances({ payee: address }),
       api.payee(address).catch((e) => (e instanceof NotFoundError ? null : Promise.reject(e))),
-      api.payees(),
     ])
-      .then(([sent, received, profile, payees]) => {
-        const names = Object.fromEntries(payees.map((p) => [p.address, p.name]));
+      .then(async ([sent, received, profile]) => {
+        // Only the payees this person paid, one request each. The payee list
+        // (`api.payees()`) holds the first 20 only, so later payees had no name.
+        const names = await payeeNames(sent.map((r) => r.payee));
         setData({ address, sent, received, profile, names });
         setError(null);
       })
diff --git a/src/lib/__tests__/payee-names.test.ts b/src/lib/__tests__/payee-names.test.ts
new file mode 100644
index 0000000..de9a14a
--- /dev/null
+++ b/src/lib/__tests__/payee-names.test.ts
@@ -0,0 +1,37 @@
+import { describe, expect, it, vi } from "vitest";
+import { NotFoundError, payeeNames, type Payee } from "../api";
+
+const payee = (address: string, name: string): Payee => ({
+  address,
+  name,
+  category: "SCHOOL",
+  verified: true,
+  registeredAt: "2026-01-01T00:00:00Z",
+});
+
+describe("payeeNames", () => {
+  it("asks once per unique payee and maps each address to its name", async () => {
+    const lookup = vi.fn(async (address: string) => payee(address, `Name of ${address}`));
+
+    const names = await payeeNames(["GA", "GB", "GA", "GA", "GB"], lookup);
+
+    expect(names).toEqual({ GA: "Name of GA", GB: "Name of GB" });
+    expect(lookup).toHaveBeenCalledTimes(2);
+  });
+
+  it("leaves out an address that is not a registered payee or whose lookup fails", async () => {
+    const lookup = vi.fn(async (address: string) => {
+      if (address === "GMISSING") throw new NotFoundError("no such payee");
+      if (address === "GDOWN") throw new Error("API 503 on /payees/GDOWN");
+      return payee(address, "Sunrise School");
+    });
+
+    expect(await payeeNames(["GMISSING", "GA", "GDOWN"], lookup)).toEqual({ GA: "Sunrise School" });
+  });
+
+  it("asks nothing when there is nothing to name", async () => {
+    const lookup = vi.fn();
+    expect(await payeeNames([], lookup)).toEqual({});
+    expect(lookup).not.toHaveBeenCalled();
+  });
+});
diff --git a/src/lib/api.ts b/src/lib/api.ts
index 56fafd5..d1f4f31 100644
--- a/src/lib/api.ts
+++ b/src/lib/api.ts
@@ -81,3 +81,26 @@ export const api = {
   remittance: (id: number) => get<RemittanceDetail>(`/remittances/${id}`),
   stats: () => get<Stats>("/stats"),
 };
+
+/**
+ * Names of the registered payees among `addresses`, keyed by address, with one request
+ * per unique address. An address that is not a registered payee is left out, and so is
+ * one whose lookup fails: the caller shows the address itself for those.
+ */
+export async function payeeNames(
+  addresses: string[],
+  lookup: (address: string) => Promise<Payee> = api.payee,
+): Promise<Record<string, string>> {
+  const unique = [...new Set(addresses)];
+  const found = await Promise.all(
+    unique.map((address) =>
+      lookup(address).then(
+        (payee) => [address, payee.name] as const,
+        () => null,
+      ),
+    ),
+  );
+  const names: Record<string, string> = {};
+  for (const entry of found) if (entry) names[entry[0]] = entry[1];
+  return names;
+}
`````

[Back to the shelf](README.md)
