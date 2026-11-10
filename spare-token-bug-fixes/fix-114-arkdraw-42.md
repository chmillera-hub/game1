# Fix 114: arkdraw: saving an AI key can hang forever when the browser aborts the write

Status: UNSENT and UNTESTED. Free to take.

- Project: gabe-santana/arkdraw
- Bug report title: Key vault IndexedDB write can hang forever on transaction abort
- Bug report: number 42 ([open the bug report](https://github.com/gabe-santana/arkdraw/issues/42))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/114-arkdraw-42.patch](fixes/114-arkdraw-42.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/114-arkdraw-42.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-114-arkdraw-42.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-114-arkdraw-42.html

## The bug

The key vault only listened for the complete and error signals of a database write. When the browser aborts a write because storage is full it sends an abort signal with no error signal. The save never finished and the AI settings window stayed stuck as busy.

## The fix

src/ai/keyVault.ts now also listens for the abort signal and rejects with the write's error or a plain error. A new file test/ai/keyVault.test.ts uses a small stand-in for the browser database: one test stores a value and one test aborts the write and checks that the save fails and does not hang.

## Files changed

- src/ai/keyVault.ts
- test/ai/keyVault.test.ts

## How to use the fix

1. Get a copy of the project gabe-santana/arkdraw.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 114-arkdraw-42.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 42.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot modelled the rule in a scratch script: without the new line an aborted write hung and with the new line the write was rejected. The chatbot did not run the new test file. The test relies on the test environment providing the Web Crypto functions which the chatbot did not confirm. Fix 115 on this shelf is for the same project and the two patches apply together.

## Search words

arkdraw keyVault IndexedDB transaction onabort quota abort vaultPut never settles AI settings dialog busy

## The full patch

`````diff
diff --git a/src/ai/keyVault.ts b/src/ai/keyVault.ts
index c3278f3..160e400 100644
--- a/src/ai/keyVault.ts
+++ b/src/ai/keyVault.ts
@@ -35,6 +35,12 @@ function run<T>(mode: IDBTransactionMode, fn: (store: IDBObjectStore) => IDBRequ
           db.close();
           reject(tx.error);
         };
+        // A quota abort fires `abort` without `error`. Without this the promise never
+        // settled and the AI settings dialog stayed busy.
+        tx.onabort = () => {
+          db.close();
+          reject(tx.error ?? new Error('The key vault write was aborted'));
+        };
       }),
   );
 }
diff --git a/test/ai/keyVault.test.ts b/test/ai/keyVault.test.ts
new file mode 100644
index 0000000..2cad4cc
--- /dev/null
+++ b/test/ai/keyVault.test.ts
@@ -0,0 +1,85 @@
+import { afterEach, describe, expect, it, vi } from 'vitest';
+
+/**
+ * A tiny stand-in for IndexedDB: one object store kept in a Map. Each
+ * transaction settles on the next tick, either with `complete` or, when its
+ * number is listed in `abortOn`, with `abort` and no `error` event (which is
+ * what a quota abort looks like).
+ */
+function fakeIndexedDb(abortOn: number[] = []) {
+  const data = new Map<string, unknown>();
+  let transactions = 0;
+  const db = {
+    close() {},
+    createObjectStore() {},
+    transaction() {
+      const number = ++transactions;
+      const tx: Record<string, unknown> & { error: unknown } = { error: null };
+      const request = <T>(result: T) => ({ result });
+      const store = {
+        get: (key: string) => request(data.get(key)),
+        put: (value: unknown, key: string) => {
+          if (!abortOn.includes(number)) data.set(key, value);
+          return request(key);
+        },
+        delete: (key: string) => request(data.delete(key)),
+        getAll: () => request([...data.values()]),
+        getAllKeys: () => request([...data.keys()]),
+        openCursor: () => request(null),
+      };
+      queueMicrotask(() => {
+        const handler = abortOn.includes(number) ? tx.onabort : tx.oncomplete;
+        if (typeof handler === 'function') handler();
+      });
+      return Object.assign(tx, { objectStore: () => store });
+    },
+  };
+  return {
+    data,
+    indexedDB: {
+      open() {
+        const req: Record<string, unknown> = { result: db, error: null };
+        queueMicrotask(() => typeof req.onsuccess === 'function' && req.onsuccess());
+        return req;
+      },
+    },
+  };
+}
+
+const settleOrHang = <T>(work: Promise<T>) =>
+  Promise.race([
+    work.then(
+      () => 'resolved' as const,
+      (err: unknown) => err,
+    ),
+    new Promise<'hung'>((resolve) => setTimeout(() => resolve('hung'), 200)),
+  ]);
+
+describe('keyVault', () => {
+  afterEach(() => {
+    vi.unstubAllGlobals();
+    vi.resetModules();
+  });
+
+  it('stores a value when every transaction completes', async () => {
+    const fake = fakeIndexedDb();
+    vi.stubGlobal('indexedDB', fake.indexedDB);
+    const { vaultPut } = await import('@/ai/keyVault');
+
+    expect(await settleOrHang(vaultPut('openai', { key: 'k' }))).toBe('resolved');
+    expect(fake.data.has('openai')).toBe(true);
+  });
+
+  it('rejects instead of hanging when the write transaction aborts', async () => {
+    // 1: read the master key, 2: store the new master key, 3: store the value.
+    const fake = fakeIndexedDb([3]);
+    vi.stubGlobal('indexedDB', fake.indexedDB);
+    const { vaultPut } = await import('@/ai/keyVault');
+
+    const outcome = await settleOrHang(vaultPut('openai', { key: 'k' }));
+
+    expect(outcome).not.toBe('hung');
+    expect(outcome).toBeInstanceOf(Error);
+    expect(fake.data.has('openai')).toBe(false);
+  });
+});
`````

[Back to the shelf](README.md)
