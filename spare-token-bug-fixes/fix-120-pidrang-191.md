# Fix 120: pidrang: the notice for an existing app says the app has its own routes when it may have none

Status: UNSENT and UNTESTED. Free to take.

- Project: pidrang/pidrang
- Bug report title: cli: make the existing app notice match what init checks
- Bug report: number 191 ([open the bug report](https://github.com/pidrang/pidrang/issues/191))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/120-pidrang-191.patch](fixes/120-pidrang-191.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/120-pidrang-191.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-120-pidrang-191.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-120-pidrang-191.html

## The bug

When pidrang init runs on an app that is not a fresh ng new app it printed that the app already has its own pages and routes. An app counts as not new when its start page was edited or when its routes file has routes. An app with an edited start page and no routes got the sentence about routes too.

## The fix

The sentence in apps/pidrang-cli/src/run-cli.ts now says: This is not a new ng new app (its start page or its routes file was changed). The two tests in apps/pidrang-cli/src/run-cli.spec.ts that check the old text now check the new text.

## Files changed

- apps/pidrang-cli/src/run-cli.spec.ts
- apps/pidrang-cli/src/run-cli.ts

## How to use the fix

1. Get a copy of the project pidrang/pidrang.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 120-pidrang-191.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 191.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The new wording follows the example in the bug report with one change: the chatbot wrote its start page or its routes file in place of the two file names because file names differ between Angular versions. The chatbot did not run the project's tests. The project builds its changelog from commit messages so the patch adds no changelog line.

## Search words

pidrang init existing app notice already has its own pages and routes printExistingAppNotice isNewApp app.html app.routes.ts

## The full patch

`````diff
diff --git a/apps/pidrang-cli/src/run-cli.spec.ts b/apps/pidrang-cli/src/run-cli.spec.ts
index 8842135..bf646b9 100644
--- a/apps/pidrang-cli/src/run-cli.spec.ts
+++ b/apps/pidrang-cli/src/run-cli.spec.ts
@@ -834,7 +834,7 @@ export const routes: Routes = [
         "export const routes: Routes = [\n  ...resourceRoutes,\n  { path: 'sign-in', component: SignInPage },\n];",
       );
       expect(output()).toContain(
-        'The app already has its own pages and routes, so pidrang only added the resource routes to src/app/app.routes.ts.',
+        'This is not a new `ng new` app (its start page or its routes file was changed), so pidrang only added the resource routes to src/app/app.routes.ts.',
       );
       expect(output()).toContain(
         "  { path: '', pathMatch: 'full', redirectTo: '/products' },",
@@ -933,7 +933,7 @@ export const routes: Routes = [
           await runCli(['init', '--plan', plan], context(undefined, tooling)),
         ).toBe(0);
 
-        expect(output()).not.toContain('The app already has its own pages');
+        expect(output()).not.toContain('This is not a new `ng new` app');
         expect(output()).not.toContain("redirectTo: '/products'");
       },
     );
diff --git a/apps/pidrang-cli/src/run-cli.ts b/apps/pidrang-cli/src/run-cli.ts
index df07ea0..5c75b99 100644
--- a/apps/pidrang-cli/src/run-cli.ts
+++ b/apps/pidrang-cli/src/run-cli.ts
@@ -342,7 +342,7 @@ function printExistingAppNotice(
   }
   context.out('');
   context.out(
-    `The app already has its own pages and routes, so pidrang only added the resource routes to ${layout.routesFile}. To open the first generated page, add this route above the others:`,
+    `This is not a new \`ng new\` app (its start page or its routes file was changed), so pidrang only added the resource routes to ${layout.routesFile}. To open the first generated page, add this route above the others:`,
   );
   context.out(
     `  { path: '', pathMatch: 'full', redirectTo: ${quote(entry.path)} },`,
`````

[Back to the shelf](README.md)
