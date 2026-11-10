# Fix 74: devswarm: an unreadable .env file is silently treated as a missing file

Status: UNSENT and UNTESTED. Free to take.

- Project: himanshu748/devswarm
- Bug report title: Report unreadable .env files instead of silently ignoring every load error
- Bug report: number 18 ([open the bug report](https://github.com/himanshu748/devswarm/issues/18))
- Project license: MIT
- Language: JavaScript (Node)
- Test included: yes
- Patch file: [fixes/74-devswarm-18.patch](fixes/74-devswarm-18.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/74-devswarm-18.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-74-devswarm-18.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-74-devswarm-18.html

## The bug

src/env.js caught every error from loading the .env file and treated every error as a missing file. A .env file that exists and cannot be read (for example because of file permissions) was skipped with no message so the person could not tell why the settings were not applied.

## The fix

src/env.js now exports loadEnv. A missing file (error code ENOENT) stays silent as before. Any other failure prints one warning that holds only the error code and never the error message or file contents. The file is still loaded once on import and shell variables still win over .env values. A new file test/env.test.js covers a missing file and an injected permission error and a check that the warning never repeats a made-up token and a normal load.

## Files changed

- src/env.js
- test/env.test.js

## How to use the fix

1. Get a copy of the project himanshu748/devswarm.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 74-devswarm-18.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 18.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The warning text and the return values loaded and missing and failed are the chatbot's choice. An error with no code or with an unusual code is reported as unknown error. The chatbot checked the rule with a scratch copy on Node 22 and confirmed there that a missing file gives ENOENT. The chatbot did not run the project's tests or start the server. The bug report asks people to check for existing pull requests first and the chatbot could not check.

## Search words

devswarm src/env.js process.loadEnvFile ENOENT EACCES unreadable .env silent catch diagnostic

## The full patch

`````diff
diff --git a/src/env.js b/src/env.js
index fa0e4c4..8b5fa6d 100644
--- a/src/env.js
+++ b/src/env.js
@@ -1,7 +1,24 @@
 // Imported first so .env is applied before telemetry reads its endpoint.
 // Real environment variables win over .env values.
-try {
-  process.loadEnvFile('.env');
-} catch {
-  /* no .env file; env comes from the shell */
+
+// Returns 'loaded', 'missing' or 'failed'. A missing .env is the normal case:
+// env then comes from the shell. Any other failure (permissions, a directory
+// named .env, a read error) is reported once. The message carries only the
+// error code, never err.message or file contents, so no .env value or token
+// can reach the log.
+export function loadEnv({
+  loadEnvFile = (file) => process.loadEnvFile(file),
+  warn = (message) => console.warn(message),
+} = {}) {
+  try {
+    loadEnvFile('.env');
+    return 'loaded';
+  } catch (err) {
+    if (err?.code === 'ENOENT') return 'missing';
+    const code = typeof err?.code === 'string' && /^[A-Z0-9_]+$/.test(err.code) ? err.code : 'unknown error';
+    warn(`[env] could not load .env (${code}); continuing with the shell environment`);
+    return 'failed';
+  }
 }
+
+loadEnv();
diff --git a/test/env.test.js b/test/env.test.js
new file mode 100644
index 0000000..7649d00
--- /dev/null
+++ b/test/env.test.js
@@ -0,0 +1,57 @@
+import { test } from 'node:test';
+import assert from 'node:assert/strict';
+import { loadEnv } from '../src/env.js';
+
+function enoent() {
+  return Object.assign(new Error("ENOENT: no such file or directory, open '.env'"), { code: 'ENOENT' });
+}
+
+test('a missing .env stays silent', () => {
+  const warnings = [];
+  const result = loadEnv({
+    loadEnvFile: () => {
+      throw enoent();
+    },
+    warn: (message) => warnings.push(message),
+  });
+  assert.equal(result, 'missing');
+  assert.deepEqual(warnings, []);
+});
+
+test('an unreadable .env is reported by error code', () => {
+  const warnings = [];
+  const result = loadEnv({
+    loadEnvFile: () => {
+      throw Object.assign(new Error("EACCES: permission denied, open '.env'"), { code: 'EACCES' });
+    },
+    warn: (message) => warnings.push(message),
+  });
+  assert.equal(result, 'failed');
+  assert.equal(warnings.length, 1);
+  assert.match(warnings[0], /could not load \.env \(EACCES\)/);
+});
+
+test('the diagnostic never repeats the error message or .env values', () => {
+  const warnings = [];
+  loadEnv({
+    loadEnvFile: () => {
+      throw Object.assign(new Error('HF_TOKEN=hf_synthetic_secret is not valid'), { code: 'hf_synthetic_secret' });
+    },
+    warn: (message) => warnings.push(message),
+  });
+  assert.equal(warnings.length, 1);
+  assert.doesNotMatch(warnings[0], /hf_synthetic_secret|HF_TOKEN/);
+  assert.match(warnings[0], /unknown error/);
+});
+
+test('a loaded .env reports nothing', () => {
+  const warnings = [];
+  const seen = [];
+  const result = loadEnv({
+    loadEnvFile: (file) => seen.push(file),
+    warn: (message) => warnings.push(message),
+  });
+  assert.equal(result, 'loaded');
+  assert.deepEqual(seen, ['.env']);
+  assert.deepEqual(warnings, []);
+});
`````

[Back to the shelf](README.md)
