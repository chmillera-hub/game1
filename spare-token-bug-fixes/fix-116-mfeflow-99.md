# Fix 116: mfeflow: mfeflow add in a tooling repo prints a --features flag that the command does not have

Status: UNSENT and UNTESTED. Free to take.

- Project: mfeflow/mfeflow
- Bug report title: add in a tooling repo prints --features in its E216 message
- Bug report: number 99 ([open the bug report](https://github.com/mfeflow/mfeflow/issues/99))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/116-mfeflow-99.patch](fixes/116-mfeflow-99.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/116-mfeflow-99.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-116-mfeflow-99.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-116-mfeflow-99.html

## The bug

In a tooling repo the command mfeflow add theming is refused which is correct. The message started with --features theming even though add takes feature names as plain arguments and has no --features flag. The same happened for ci-github.

## The fix

toolingRefusal in packages/cli/src/polyrepo.ts now takes the label to print. init passes --features plus the name and add passes the plain name (packages/cli/src/commands/add.ts). The add tests in packages/cli/src/kind-tooling.test.ts now expect the plain name and check that --features is absent. A changeset file is included.

## Files changed

- .changeset/add-tooling-refusal-label.md
- packages/cli/src/commands/add.ts
- packages/cli/src/kind-tooling.test.ts
- packages/cli/src/polyrepo.ts

## How to use the fix

1. Get a copy of the project mfeflow/mfeflow.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 116-mfeflow-99.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 99.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot did not run the project's tests. The bug report also names packages/cli/src/commands/add.test.ts and the chatbot found no check of this message in that file so that file is unchanged.

## Search words

mfeflow add tooling repo E216 E107 --features theming message toolingRefusal polyrepo.ts label

## The full patch

`````diff
diff --git a/.changeset/add-tooling-refusal-label.md b/.changeset/add-tooling-refusal-label.md
new file mode 100644
index 0000000..5c5c1ae
--- /dev/null
+++ b/.changeset/add-tooling-refusal-label.md
@@ -0,0 +1,5 @@
+---
+'mfeflow': patch
+---
+
+`mfeflow add` in a tooling repo no longer prints a `--features` flag it does not have. The E216 and E107 refusals now read `theming: needs an app ...` and `ci-github: not in a tooling repo ...`. `mfeflow init --kind tooling --features ...` keeps the flag in its message.
diff --git a/packages/cli/src/commands/add.ts b/packages/cli/src/commands/add.ts
index 68849b3..8756fdd 100644
--- a/packages/cli/src/commands/add.ts
+++ b/packages/cli/src/commands/add.ts
@@ -381,7 +381,8 @@ async function addFeatures(
   );
   if (hasNoApps(project) && project.topology !== 'polyrepo') {
     for (const feature of loaded) {
-      const refusal = toolingRefusal(feature);
+      // `add` takes feature names as arguments, so the message names the feature alone.
+      const refusal = toolingRefusal(feature, feature.manifest.name);
       if (refusal) throw refusal;
     }
   }
diff --git a/packages/cli/src/kind-tooling.test.ts b/packages/cli/src/kind-tooling.test.ts
index 17b7bcf..fed8452 100644
--- a/packages/cli/src/kind-tooling.test.ts
+++ b/packages/cli/src/kind-tooling.test.ts
@@ -503,7 +503,9 @@ describe('mfeflow add in a tooling repo', () => {
       const { code, err } = await add(root, name);
       expect(code).toBe(2);
       expect(err).toContain('MFEFLOW_E216');
-      expect(err).toContain(`--features ${name}: needs an app (`);
+      // `add` has no --features flag: the message names the feature alone.
+      expect(err).toContain(`: ${name}: needs an app (`);
+      expect(err).not.toContain('--features');
       expect(err).toContain('a tooling repo has none');
       expect(await readTree(root)).toEqual(before);
     },
@@ -515,7 +517,8 @@ describe('mfeflow add in a tooling repo', () => {
     const { code, err } = await add(root, 'ci-github');
     expect(code).toBe(2);
     expect(err).toContain('MFEFLOW_E107');
-    expect(err).toContain('--features ci-github: not in a tooling repo');
+    expect(err).toContain(': ci-github: not in a tooling repo');
+    expect(err).not.toContain('--features');
     expect(await readTree(root)).toEqual(before);
   });
 
diff --git a/packages/cli/src/polyrepo.ts b/packages/cli/src/polyrepo.ts
index a91fe88..73e08b9 100644
--- a/packages/cli/src/polyrepo.ts
+++ b/packages/cli/src/polyrepo.ts
@@ -70,18 +70,22 @@ export function appPartOf(feature: LoadedFeature): string | undefined {
   return part && `${part.label} goes to ${part.target ?? 'root'}`;
 }
 
-/** The one place that decides whether a tooling repo takes a feature: the refusal, or undefined. */
-export function toolingRefusal(feature: LoadedFeature): MfeflowError | undefined {
+/**
+ * The one place that decides whether a tooling repo takes a feature: the refusal, or undefined.
+ * `label` is how the caller's command names the feature: `--features theming` for init, which
+ * takes a flag, and plain `theming` for add, which takes feature names as arguments.
+ */
+export function toolingRefusal(feature: LoadedFeature, label: string): MfeflowError | undefined {
   const name = feature.manifest.name;
   const clash = TOOLING_CLASHES[name];
   if (clash !== undefined) {
-    return new MfeflowError('E107', `--features ${name}: not in a tooling repo, ${clash}`);
+    return new MfeflowError('E107', `${label}: not in a tooling repo, ${clash}`);
   }
   const app = appPartOf(feature);
   if (app !== undefined) {
     return new MfeflowError(
       'E216',
-      `--features ${name}: needs an app (${app}), and a tooling repo has none. Use a repo with apps, or the shell and remote repos of a polyrepo.`,
+      `${label}: needs an app (${app}), and a tooling repo has none. Use a repo with apps, or the shell and remote repos of a polyrepo.`,
     );
   }
   return undefined;
@@ -94,7 +98,7 @@ export async function assertToolingFeatures(
 ): Promise<void> {
   const loaded = await Promise.all(features.map((name) => loadAny(name, { roots: rt.roots })));
   for (const feature of loaded) {
-    const refusal = toolingRefusal(feature);
+    const refusal = toolingRefusal(feature, `--features ${feature.manifest.name}`);
     if (refusal) throw refusal;
   }
 }
`````

[Back to the shelf](README.md)
