# Fix 6: AgenticResourceRegistry: web screens show the command observal pull which does not exist

Status: UNSENT and UNTESTED. Free to take.

- Project: AgenticResourceRegistry/AgenticResourceRegistry
- Bug report: number 1971 ([open the bug report](https://github.com/AgenticResourceRegistry/AgenticResourceRegistry/issues/1971))
- Project license: Apache-2.0
- Language: TypeScript (text only)
- Test included: no
- Patch file: [fixes/6-agenticresourceregistry-1971.patch](fixes/6-agenticresourceregistry-1971.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/6-agenticresourceregistry-1971.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-6-agenticresourceregistry-1971.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-6-agenticresourceregistry-1971.html

## The bug

Five places in the web interface tell people to type observal pull. The real command is observal agent pull. A person who copies the shown command gets an error.

## The fix

The fix changes the shown text to observal agent pull in preview-panel.tsx and home.tsx and teamspace-detail.tsx and teamspaces.tsx. Text change only. No test is included.

## Files changed

- web/src/components/builder/preview-panel.tsx
- web/src/pages/registry/home.tsx
- web/src/pages/registry/teamspace-detail.tsx
- web/src/pages/registry/teamspaces.tsx

## How to use the fix

1. Get a copy of the project AgenticResourceRegistry/AgenticResourceRegistry.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 6-agenticresourceregistry-1971.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 1971.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot worked from the bug report title plus the code and did not read the full bug report text.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-09 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-09 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.

## Search words

observal pull observal agent pull wrong command in UI No such command registry home teamspaces preview panel

## The full patch

`````diff
diff --git a/web/src/components/builder/preview-panel.tsx b/web/src/components/builder/preview-panel.tsx
index a5a4cde..0a47e78 100644
--- a/web/src/components/builder/preview-panel.tsx
+++ b/web/src/components/builder/preview-panel.tsx
@@ -282,7 +282,7 @@ export function PreviewPanel({
 				Telemetry hooks and environment variables are configured during
 				installation via{" "}
 				<code className="font-[family-name:var(--font-mono)]">
-					observal pull
+					observal agent pull
 				</code>
 				.
 			</p>
@@ -295,7 +295,7 @@ export function PreviewPanel({
 						<DialogDescription>
 							Exact files written by{" "}
 							<code className="font-[family-name:var(--font-mono)]">
-								observal pull
+								observal agent pull
 							</code>
 							. Server URLs are placeholders.
 						</DialogDescription>
diff --git a/web/src/pages/registry/home.tsx b/web/src/pages/registry/home.tsx
index 76edddf..0fd4163 100644
--- a/web/src/pages/registry/home.tsx
+++ b/web/src/pages/registry/home.tsx
@@ -190,7 +190,7 @@ export default function RegistryHome() {
               <li className="min-w-0">
                 <p className="mb-1.5 font-medium text-foreground">3. Pull it into your harness</p>
                 <code className="block overflow-x-auto whitespace-nowrap rounded-md bg-background px-3 py-2 font-mono text-xs text-foreground">
-                  observal pull namespace/agent --harness pi
+                  observal agent pull namespace/agent --harness pi
                 </code>
               </li>
             </ol>
diff --git a/web/src/pages/registry/teamspace-detail.tsx b/web/src/pages/registry/teamspace-detail.tsx
index b4bd1d1..ace6bb2 100644
--- a/web/src/pages/registry/teamspace-detail.tsx
+++ b/web/src/pages/registry/teamspace-detail.tsx
@@ -1200,7 +1200,7 @@ export default function TeamspaceDetailPage() {
 							</div>
 						</div>
 						<code className="rounded-md border border-border/80 bg-background px-3 py-2 font-mono text-xs text-foreground">
-							observal pull {team.handle}/agent-name
+							observal agent pull {team.handle}/agent-name
 						</code>
 							</footer>
 						</>
diff --git a/web/src/pages/registry/teamspaces.tsx b/web/src/pages/registry/teamspaces.tsx
index 1bfe7c2..eb8af73 100644
--- a/web/src/pages/registry/teamspaces.tsx
+++ b/web/src/pages/registry/teamspaces.tsx
@@ -280,7 +280,7 @@ function CreatePanel({
         <div className="self-center" aria-live="polite" aria-atomic="true">
           <p className="text-xs font-medium text-muted-foreground">Live install identity</p>
           <div className="mt-3 min-h-16 border-b border-border pb-4 font-mono text-xl tracking-tight 2xl:text-2xl">
-            <span className="text-muted-foreground">observal pull </span>
+            <span className="text-muted-foreground">observal agent pull </span>
             <span key={previewHandle} className="inline-block text-foreground">
               {previewHandle}
             </span>
`````

[Back to the shelf](README.md)
