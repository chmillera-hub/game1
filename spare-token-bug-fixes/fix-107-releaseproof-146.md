# Fix 107: releaseproof: older package names with capital letters such as JSONStream are rejected

Status: UNSENT and UNTESTED. Free to take.

- Project: ujjwalv01/releaseproof
- Bug report title: Legacy package names with uppercase letters (JSONStream) are rejected as invalid
- Bug report: number 146 ([open the bug report](https://github.com/ujjwalv01/releaseproof/issues/146))
- Project license: MIT
- Language: TypeScript
- Test included: yes
- Patch file: [fixes/107-releaseproof-146.patch](fixes/107-releaseproof-146.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/107-releaseproof-146.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-107-releaseproof-146.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-107-releaseproof-146.html

## The bug

releaseproof check JSONStream@1.3.5 failed with Invalid package name. JSONStream is a real and widely used npm package. npm stopped allowing capital letters in new names in 2016 and packages made before that keep them so those packages could not be checked at all.

## The fix

The name rule in packages/core/src/registry/spec.ts now allows capital letters in the scope and in the package part and keeps every other rule. The name is never changed to lower case. packages/core/src/registry/spec.test.ts gains a test for JSONStream and more rejected names. A new file packages/core/src/fetch/version-path.test.ts checks that the registry path keeps the capital letters. A changeset file is included.

## Files changed

- .changeset/legacy-uppercase-names.md
- packages/core/src/fetch/version-path.test.ts
- packages/core/src/registry/spec.test.ts
- packages/core/src/registry/spec.ts

## How to use the fix

1. Get a copy of the project ujjwalv01/releaseproof.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 107-releaseproof-146.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 146.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The existing test listed Sigstore@1.0.0 as an invalid name. The patch removes that entry because a name with a capital letter is now accepted. The chatbot checked the new rule with a scratch script and did not run the project's tests or build.

## Search words

releaseproof parseSpec NAME_RE uppercase legacy package name JSONStream Invalid package name validForOldPackages versionPath

## The full patch

`````diff
diff --git a/.changeset/legacy-uppercase-names.md b/.changeset/legacy-uppercase-names.md
new file mode 100644
index 0000000..e53ecab
--- /dev/null
+++ b/.changeset/legacy-uppercase-names.md
@@ -0,0 +1,8 @@
+---
+"releaseproof": patch
+---
+
+Package names with uppercase letters, which npm still serves for packages published before
+2017 (for example `JSONStream`), are accepted and no longer fail with `Invalid package name`.
+The name is used exactly as written, so the registry path and the attestation subject keep
+its case.
diff --git a/packages/core/src/fetch/version-path.test.ts b/packages/core/src/fetch/version-path.test.ts
new file mode 100644
index 0000000..3cb4df1
--- /dev/null
+++ b/packages/core/src/fetch/version-path.test.ts
@@ -0,0 +1,13 @@
+import { describe, expect, it } from "vitest";
+import { parseSpec } from "../registry/spec.js";
+import { versionPath } from "./published.js";
+
+describe("versionPath", () => {
+  it("keeps the case of a pre-2017 package name", () => {
+    expect(versionPath(parseSpec("JSONStream@1.3.5"))).toBe("/JSONStream/1.3.5");
+  });
+
+  it("still escapes the slash of a scoped name", () => {
+    expect(versionPath(parseSpec("@sigstore/verify@4.1.2"))).toBe("/@sigstore%2fverify/4.1.2");
+  });
+});
diff --git a/packages/core/src/registry/spec.test.ts b/packages/core/src/registry/spec.test.ts
index a5fc02a..6e8ff59 100644
--- a/packages/core/src/registry/spec.test.ts
+++ b/packages/core/src/registry/spec.test.ts
@@ -54,7 +54,24 @@ describe("parseSpec", () => {
     },
   );
 
-  it.each(["Sigstore@1.0.0", ".hidden@1.0.0", "bad name@1.0.0", "@scope@1.0.0", "a/b@1.0.0"])(
+  it("accepts the uppercase letters of a pre-2017 package name and keeps them", () => {
+    expect(parseSpec("JSONStream@1.3.5")).toEqual({
+      name: "JSONStream",
+      version: "1.3.5",
+      purl: "pkg:npm/JSONStream@1.3.5",
+    });
+    expect(parseSpec("@Scope/Pkg@1.0.0").name).toBe("@Scope/Pkg");
+  });
+
+  it.each([
+    ".hidden@1.0.0",
+    "_private@1.0.0",
+    "..@1.0.0",
+    "bad name@1.0.0",
+    "Bad Name@1.0.0",
+    "@scope@1.0.0",
+    "a/b@1.0.0",
+  ])(
     "rejects invalid package name in %j",
     (input) => {
       expect(() => parseSpec(input)).toThrow(/Invalid package name/);
diff --git a/packages/core/src/registry/spec.ts b/packages/core/src/registry/spec.ts
index d2f38f2..1125987 100644
--- a/packages/core/src/registry/spec.ts
+++ b/packages/core/src/registry/spec.ts
@@ -7,8 +7,11 @@ export interface PackageSpec {
   purl: string;
 }
 
-// npm name rules: lowercase, URL-safe, optional @scope/, max 214 chars.
-const NAME_RE = /^(@[a-z0-9-~][a-z0-9-._~]*\/)?[a-z0-9-~][a-z0-9-._~]*$/;
+// npm name rules: URL-safe, optional @scope/, max 214 chars. Uppercase letters are accepted
+// only because packages published before 2017 keep them (JSONStream); npm refuses them in
+// new names. The name is never lowercased: the registry path and the attestation subject
+// use it exactly as published.
+const NAME_RE = /^(@[A-Za-z0-9-~][A-Za-z0-9-._~]*\/)?[A-Za-z0-9-~][A-Za-z0-9-._~]*$/;
 // An exact semver version. Ranges and tags are rejected on purpose: a verdict must be about
 // one immutable tarball.
 const VERSION_RE = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/;
`````

[Back to the shelf](README.md)
