# Fix 63: loop: a stale clipboard result overwrites the latest copy status

Status: UNSENT and UNTESTED. Free to take.

- Project: JimmyDi/loop
- Bug report title: bug(web): stale clipboard results overwrite the latest copy status
- Bug report: number 115 ([open the bug report](https://github.com/JimmyDi/loop/issues/115))
- Project license: MIT
- Language: TypeScript (React)
- Test included: yes
- Patch file: [fixes/63-loop-115.patch](fixes/63-loop-115.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/63-loop-115.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-63-loop-115.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-63-loop-115.html

## The bug

When two copy operations finished out of order the older one replaced the feedback of the newer one. The page could announce a failed copy even though the latest copy succeeded.

## The fix

The useCopy hook in packages/web-ui/src/frontend/hooks/useCopy.ts counts copy operations. Only the most recent operation sets the status and schedules the reset timer. A completion after unmount does nothing. The rich clipboard fallback is unchanged. The test file gains a test with two deferred clipboard promises that finish out of order and a test for a completion after unmount. CHANGELOG.md gains a line.

## Files changed

- CHANGELOG.md
- packages/web-ui/src/frontend/hooks/useCopy.test.tsx
- packages/web-ui/src/frontend/hooks/useCopy.ts

## How to use the fix

1. Get a copy of the project JimmyDi/loop.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 63-loop-115.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 115.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Nobody ran the new tests. The two new tests use a helper that the chatbot wrote for the test file and the helper may need small changes to run under the project's test setup. Fixes 62 and 63 each add a line at the same spot of CHANGELOG.md. Applying both needs a small manual merge of CHANGELOG.md.

## Search words

loop web-ui useCopy clipboard stale result out of order copyFailed copied revision counter unmount timer

## The full patch

`````diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index b4bfee1..aa97596 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -18,6 +18,8 @@ Notable changes across Agent, coding-agent, and Web UI are recorded here. Pendin
 
 - Website: eliminate the dark gap above the homepage background on mobile.
 
+- Web UI: keep copy feedback on the latest copy; an older copy that finishes late no longer replaces it, and none schedules a reset after unmount.
+
 ## [0.6.0] - 2026-11-06
 
 ### Added
diff --git a/packages/web-ui/src/frontend/hooks/useCopy.test.tsx b/packages/web-ui/src/frontend/hooks/useCopy.test.tsx
index 07e0a66..32aec4d 100644
--- a/packages/web-ui/src/frontend/hooks/useCopy.test.tsx
+++ b/packages/web-ui/src/frontend/hooks/useCopy.test.tsx
@@ -1,4 +1,4 @@
-import { expect, test } from "vitest";
+import { expect, test, vi } from "vitest";
 import { Window } from "happy-dom";
 
 test("copy hook reports clipboard failure without throwing into the UI", async () => {
@@ -85,3 +85,98 @@ test("rich clipboard failure falls back to readable plain text", async () => {
     await window.happyDOM.close();
   }
 });
+
+function deferred() {
+  let resolve!: () => void;
+  let reject!: (error: Error) => void;
+  const promise = new Promise<void>((res, rej) => {
+    resolve = res;
+    reject = rej;
+  });
+  return { promise, resolve, reject };
+}
+
+async function withClipboard(
+  writeText: (text: string) => Promise<void>,
+  run: (hooks: typeof import("@testing-library/react/pure")) => Promise<void>,
+) {
+  const window = new Window();
+  const previous = {
+    window: globalThis.window,
+    document: globalThis.document,
+    navigator: globalThis.navigator,
+  };
+  Object.assign(globalThis, { window, document: window.document });
+  Object.defineProperty(globalThis, "navigator", {
+    configurable: true,
+    value: { userAgent: window.navigator.userAgent, clipboard: { writeText } },
+  });
+  const hooks = await import("@testing-library/react/pure");
+  try {
+    await run(hooks);
+  } finally {
+    hooks.cleanup();
+    Object.assign(globalThis, { window: previous.window, document: previous.document });
+    Object.defineProperty(globalThis, "navigator", {
+      configurable: true,
+      value: previous.navigator,
+    });
+    await window.happyDOM.close();
+  }
+}
+
+test("an older copy finishing late does not replace the latest copy status", async () => {
+  const pending = { first: deferred(), second: deferred() };
+  await withClipboard(
+    (text) => pending[text as "first" | "second"].promise,
+    async ({ renderHook, act }) => {
+      const { useCopy } = await import("./useCopy");
+      const { result } = renderHook(useCopy);
+
+      let first!: Promise<void>;
+      let second!: Promise<void>;
+      act(() => {
+        first = result.current.copy("first");
+        second = result.current.copy("second");
+      });
+
+      await act(async () => {
+        pending.second.resolve();
+        await second;
+      });
+      expect(result.current.status).toBe("copied");
+
+      await act(async () => {
+        pending.first.reject(new Error("Denied"));
+        await first;
+      });
+      expect(result.current.status).toBe("copied");
+    },
+  );
+});
+
+test("a copy that finishes after unmount schedules no reset timer", async () => {
+  const pending = deferred();
+  await withClipboard(
+    () => pending.promise,
+    async ({ renderHook, act }) => {
+      const { useCopy } = await import("./useCopy");
+      const { result, unmount } = renderHook(useCopy);
+
+      let copy!: Promise<void>;
+      act(() => {
+        copy = result.current.copy("late");
+      });
+      unmount();
+
+      const timers = vi.spyOn(globalThis, "setTimeout");
+      try {
+        pending.resolve();
+        await copy;
+        expect(timers.mock.calls.filter(([, delay]) => delay === 1600)).toHaveLength(0);
+      } finally {
+        timers.mockRestore();
+      }
+    },
+  );
+});
diff --git a/packages/web-ui/src/frontend/hooks/useCopy.ts b/packages/web-ui/src/frontend/hooks/useCopy.ts
index 1fac8e1..146d16b 100644
--- a/packages/web-ui/src/frontend/hooks/useCopy.ts
+++ b/packages/web-ui/src/frontend/hooks/useCopy.ts
@@ -3,12 +3,23 @@ import { useEffect, useRef, useState } from "react";
 export const useCopy = () => {
   const [status, setStatus] = useState<"copy" | "copied" | "copyFailed">("copy");
   const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
+  // Counts copy operations, so a completion can tell whether a newer copy started after it.
+  const revision = useRef(0);
+  const disposed = useRef(false);
 
-  useEffect(() => () => clearTimeout(timer.current), []);
+  useEffect(() => {
+    disposed.current = false;
+    return () => {
+      disposed.current = true;
+      clearTimeout(timer.current);
+    };
+  }, []);
 
   const copy = async (text: string, html?: string) => {
+    const mine = ++revision.current;
     clearTimeout(timer.current);
 
+    let outcome: "copied" | "copyFailed";
     try {
       if (html && typeof ClipboardItem !== "undefined" && navigator.clipboard.write) {
         try {
@@ -22,11 +33,15 @@ export const useCopy = () => {
           await navigator.clipboard.writeText(text);
         }
       } else await navigator.clipboard.writeText(text);
-      setStatus("copied");
+      outcome = "copied";
     } catch {
-      setStatus("copyFailed");
+      outcome = "copyFailed";
     }
 
+    // Only the most recent copy reports and schedules the reset: an older one finishing late
+    // must not replace the newer feedback, and nothing is scheduled after unmount.
+    if (disposed.current || mine !== revision.current) return;
+    setStatus(outcome);
     timer.current = setTimeout(() => setStatus("copy"), 1600);
   };
`````

[Back to the shelf](README.md)
