# Fix 95: remitsure-frontend: Copy receipt link does nothing when the browser has no clipboard access

Status: UNSENT and UNTESTED. Free to take.

- Project: remitsure/remitsure-frontend
- Bug report title: Copy receipt link fails silently when the Clipboard API is unavailable
- Bug report: number 3 ([open the bug report](https://github.com/remitsure/remitsure-frontend/issues/3))
- Project license: MIT
- Language: TypeScript (React)
- Test included: yes
- Patch file: [fixes/95-remitsure-frontend-3.patch](fixes/95-remitsure-frontend-3.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/95-remitsure-frontend-3.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-95-remitsure-frontend-3.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-95-remitsure-frontend-3.html

## The bug

The Copy receipt link button called the clipboard directly. The clipboard is missing on pages without a secure connection and inside some in-app browsers and the call fails when permission is denied. The button then did nothing and left an unhandled error.

## The fix

A new file src/lib/share.ts holds shareLink: use the share sheet when the browser has one and then the clipboard and otherwise report that a manual copy is needed. The receipt page calls shareLink and shows the link in a read-only field when a manual copy is needed. A new file src/lib/__tests__/share.test.ts covers six cases. CHANGELOG.md gains one line.

## Files changed

- CHANGELOG.md
- src/app/(app)/r/[id]/page.tsx
- src/lib/__tests__/share.test.ts
- src/lib/share.ts

## How to use the fix

1. Get a copy of the project remitsure/remitsure-frontend.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 95-remitsure-frontend-3.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 3.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- On browsers with a share sheet the button now opens the share sheet and no longer copies straight to the clipboard. That follows the bug report. The chatbot type-checked a scratch copy of share.ts with the TypeScript compiler and ran a scratch JavaScript copy of the rule. The chatbot did not type-check the changed page and did not run the app or the project's tests. Fixes 59 and 60 on this shelf change the same page and the same spot of CHANGELOG.md so this patch does not apply together with either of them. Fix 61 applies together with this patch.

## Search words

remitsure receipt page Copy receipt link navigator.clipboard undefined in-app browser Web Share API fallback unhandled rejection

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index e2100b5..15a4498 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -7,3 +7,7 @@ All notable changes to this repo are listed here. The format follows [Keep a Cha
 ### Added
 
 - Initial MVP scaffold.
+
+### Fixed
+
+- "Copy receipt link" no longer fails silently where the Clipboard API is missing or denied: it uses the share sheet when the browser has one, then the clipboard, and otherwise shows the link in a field to copy by hand.
diff --git a/src/app/(app)/r/[id]/page.tsx b/src/app/(app)/r/[id]/page.tsx
index 350631b..78885bf 100644
--- a/src/app/(app)/r/[id]/page.tsx
+++ b/src/app/(app)/r/[id]/page.tsx
@@ -10,6 +10,7 @@ import { api, NotFoundError, type RemittanceDetail } from "@/lib/api";
 import { config, explorerAccount, explorerTx } from "@/lib/config";
 import { remitsure } from "@/lib/contract";
 import { formatDate, fromUnits, relativeTime, shortAddress } from "@/lib/format";
+import { shareLink } from "@/lib/share";
 
 type Action = "claim" | "reject" | "refund";
 
@@ -29,6 +30,7 @@ export default function Receipt() {
   const [busy, setBusy] = useState<Action | null>(null);
   const [lastTx, setLastTx] = useState<string | null>(null);
   const [copied, setCopied] = useState(false);
+  const [manualLink, setManualLink] = useState<string | null>(null);
   // Ticks with the refresh so the expired check and countdown stay current.
   const [now, setNow] = useState(() => Date.now());
 
@@ -76,9 +78,16 @@ export default function Receipt() {
   }
 
   async function share() {
-    await navigator.clipboard.writeText(window.location.href.split("?")[0]!);
-    setCopied(true);
-    setTimeout(() => setCopied(false), 2_000);
+    const url = window.location.href.split("?")[0]!;
+    const outcome = await shareLink(url);
+    if (outcome === "copied") {
+      setManualLink(null);
+      setCopied(true);
+      setTimeout(() => setCopied(false), 2_000);
+    } else if (outcome === "manual") {
+      // No share sheet and no clipboard: show the link so it can be copied by hand.
+      setManualLink(url);
+    }
   }
 
   if (!r) return <Notice tone={error ? "error" : "info"}>{error ?? "Loading receipt..."}</Notice>;
@@ -226,6 +235,17 @@ export default function Receipt() {
           {copied ? "Link copied" : "Copy receipt link"}
         </button>
       </div>
+      {manualLink && (
+        <label className="block text-sm">
+          Copy this link
+          <input
+            readOnly
+            value={manualLink}
+            onFocus={(e) => e.currentTarget.select()}
+            className="mt-1 w-full rounded-lg border border-line bg-card px-3 py-2"
+          />
+        </label>
+      )}
     </div>
   );
 }
diff --git a/src/lib/__tests__/share.test.ts b/src/lib/__tests__/share.test.ts
new file mode 100644
index 0000000..465f081
--- /dev/null
+++ b/src/lib/__tests__/share.test.ts
@@ -0,0 +1,59 @@
+import { describe, expect, it } from "vitest";
+import { shareLink } from "../share";
+
+const url = "https://example.test/r/42";
+
+function abortError(): Error {
+  return Object.assign(new Error("share cancelled"), { name: "AbortError" });
+}
+
+describe("shareLink", () => {
+  it("uses the share sheet when the browser has one", async () => {
+    const seen: string[] = [];
+    const outcome = await shareLink(url, {
+      share: async (data) => void seen.push(data.url),
+      clipboard: { writeText: async () => void seen.push("clipboard") },
+    });
+    expect(outcome).toBe("shared");
+    expect(seen).toEqual([url]);
+  });
+
+  it("copies to the clipboard when there is no share sheet", async () => {
+    const seen: string[] = [];
+    const outcome = await shareLink(url, {
+      clipboard: { writeText: async (text) => void seen.push(text) },
+    });
+    expect(outcome).toBe("copied");
+    expect(seen).toEqual([url]);
+  });
+
+  it("falls back to the clipboard when the share sheet fails", async () => {
+    const outcome = await shareLink(url, {
+      share: async () => Promise.reject(new Error("not allowed")),
+      clipboard: { writeText: async () => undefined },
+    });
+    expect(outcome).toBe("copied");
+  });
+
+  it("does not copy when the user closes the share sheet", async () => {
+    const seen: string[] = [];
+    const outcome = await shareLink(url, {
+      share: async () => Promise.reject(abortError()),
+      clipboard: { writeText: async (text) => void seen.push(text) },
+    });
+    expect(outcome).toBe("cancelled");
+    expect(seen).toEqual([]);
+  });
+
+  it("asks for a manual copy when the clipboard is missing", async () => {
+    expect(await shareLink(url, {})).toBe("manual");
+    expect(await shareLink(url, undefined)).toBe("manual");
+  });
+
+  it("asks for a manual copy when the clipboard rejects, without throwing", async () => {
+    const outcome = await shareLink(url, {
+      clipboard: { writeText: async () => Promise.reject(new Error("denied")) },
+    });
+    expect(outcome).toBe("manual");
+  });
+});
diff --git a/src/lib/share.ts b/src/lib/share.ts
new file mode 100644
index 0000000..f498dfa
--- /dev/null
+++ b/src/lib/share.ts
@@ -0,0 +1,39 @@
+export type ShareOutcome = "shared" | "copied" | "cancelled" | "manual";
+
+/** The parts of `navigator` that sharing a link needs. Both are missing in some browsers. */
+export type ShareTarget = {
+  share?: (data: { url: string }) => Promise<void>;
+  clipboard?: { writeText?: (text: string) => Promise<void> };
+};
+
+/**
+ * Hands a link to the user and never rejects.
+ *
+ * Tries the Web Share sheet first (mobile browsers), then the clipboard. The
+ * clipboard is undefined on non secure origins and in some in app browsers,
+ * and `writeText` rejects when permission is denied. When neither works the
+ * result is "manual" and the caller shows the link in a selectable field.
+ */
+export async function shareLink(
+  url: string,
+  target: ShareTarget | undefined = globalThis.navigator,
+): Promise<ShareOutcome> {
+  if (typeof target?.share === "function") {
+    try {
+      await target.share({ url });
+      return "shared";
+    } catch (err) {
+      // Closing the share sheet is a choice, not a failure.
+      if ((err as { name?: string } | null)?.name === "AbortError") return "cancelled";
+    }
+  }
+  if (typeof target?.clipboard?.writeText === "function") {
+    try {
+      await target.clipboard.writeText(url);
+      return "copied";
+    } catch {
+      // Permission denied or the document is not focused: fall through.
+    }
+  }
+  return "manual";
+}
`````

[Back to the shelf](README.md)
