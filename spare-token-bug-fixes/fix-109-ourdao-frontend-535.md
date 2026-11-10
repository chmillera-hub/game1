# Fix 109: ourdao-frontend: the manifest test can never pass because it looks for icons at the root of the disk

Status: UNSENT and UNTESTED. Free to take.

- Project: ourdao/ourdao-frontend
- Bug report title: `manifest.test.ts` can never pass: `resolve(PUBLIC_DIR, '/icon-192x192.png')` ignores `PUBLIC_DIR`
- Bug report: number 535 ([open the bug report](https://github.com/ourdao/ourdao-frontend/issues/535))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/109-ourdao-frontend-535.patch](fixes/109-ourdao-frontend-535.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/109-ourdao-frontend-535.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-109-ourdao-frontend-535.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-109-ourdao-frontend-535.html

## The bug

The manifest lists icons with a leading slash such as /icon-192x192.png. The test joined that text to the public folder with path.resolve which treats a leading slash as an absolute path and drops the folder. The test looked at the root of the disk so two checks always failed even though every icon exists.

## The fix

src/__tests__/manifest.test.ts now uses path.join for the two icon checks so the public folder is kept.

## Files changed

- src/__tests__/manifest.test.ts

## How to use the fix

1. Get a copy of the project ourdao/ourdao-frontend.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 109-ourdao-frontend-535.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 535.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The change is to a test file only. The chatbot confirmed with a scratch script that all six icons named in the manifest exist in the public folder. The chatbot did not run the project's tests. Fix 113 on this shelf is for the same project and touches a different file.

## Search words

ourdao-frontend manifest.test.ts path.resolve leading slash PUBLIC_DIR icon files exist always fails join

## The full patch

`````diff
diff --git a/src/__tests__/manifest.test.ts b/src/__tests__/manifest.test.ts
index 59cee58..f2a9712 100644
--- a/src/__tests__/manifest.test.ts
+++ b/src/__tests__/manifest.test.ts
@@ -1,6 +1,6 @@
 import { describe, it, expect } from 'vitest'
 import { readFileSync, existsSync } from 'fs'
-import { resolve } from 'path'
+import { join, resolve } from 'path'
 
 const PUBLIC_DIR = resolve(import.meta.dirname, '../../public')
 
@@ -20,7 +20,9 @@ describe('PWA Manifest', () => {
 
   it('all referenced icon files exist', () => {
     for (const icon of manifest.icons) {
-      const iconPath = resolve(PUBLIC_DIR, icon.src)
+      // join, not resolve: resolve treats a src such as '/icon-192x192.png' as
+      // absolute and drops PUBLIC_DIR, so the check looked at the filesystem root.
+      const iconPath = join(PUBLIC_DIR, icon.src)
       expect(existsSync(iconPath)).toBe(true)
     }
   })
@@ -30,7 +32,7 @@ describe('PWA Manifest', () => {
       for (const shortcut of manifest.shortcuts) {
         if (shortcut.icons) {
           for (const icon of shortcut.icons) {
-            const iconPath = resolve(PUBLIC_DIR, icon.src)
+            const iconPath = join(PUBLIC_DIR, icon.src)
             expect(existsSync(iconPath)).toBe(true)
           }
         }
`````

[Back to the shelf](README.md)
