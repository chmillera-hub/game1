# Fix 73: MyFinances: the server answers 500 for a malformed JSON body or an oversize body

Status: UNSENT and UNTESTED. Free to take.

- Project: jasonkryst/MyFinances
- Bug report title: maint: Server error handler turns client errors (bad JSON, oversize body) into 500s
- Bug report: number 531 ([open the bug report](https://github.com/jasonkryst/MyFinances/issues/531))
- Project license: MIT
- Language: JavaScript (Node)
- Test included: yes
- Patch file: [fixes/73-myfinances-531.patch](fixes/73-myfinances-531.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/73-myfinances-531.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-73-myfinances-531.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-73-myfinances-531.html

## The bug

The last error handler of the server always answered 500 INTERNAL_ERROR and logged the full error. A malformed JSON body sent to /auth/login got a 500 answer even though the body parser had marked the error as 400. An oversize body (413) took the same path.

## The fix

The last error handler in server/src/app.js now reads the status on the error. A status from 400 to 499 is sent back with the code BAD_REQUEST or PAYLOAD_TOO_LARGE for 413 and nothing is logged. Every other error is logged and answered with 500 as before. A new file server/test/errorHandler.test.js sends a malformed body and a body of two megabytes and checks for 400 and 413.

## Files changed

- server/src/app.js
- server/test/errorHandler.test.js

## How to use the fix

1. Get a copy of the project jasonkryst/MyFinances.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 73-myfinances-531.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 531.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- Every client error other than 413 gets the code BAD_REQUEST including statuses such as 404 raised by middleware. The wording of the two messages is the chatbot's choice. The patch adds no changelog entry because the project ties each changelog entry to a version number that the maintainer chooses. The chatbot checked the rule with a scratch copy of the handler and did not start the server or run the project's tests. Fix 80 on this shelf is for the same project and touches different files.

## Search words

MyFinances express error handler 500 INTERNAL_ERROR entity.parse.failed malformed JSON 413 payload too large err.status app.js

## The full patch

`````diff
diff --git a/server/src/app.js b/server/src/app.js
index 05fb99a..4a1da42 100644
--- a/server/src/app.js
+++ b/server/src/app.js
@@ -88,6 +88,20 @@ export function createApp() {
 
     // eslint-disable-next-line no-unused-vars
     app.use((err, req, res, next) => {
+        // Client errors raised by middleware carry their own status: the JSON
+        // body parser sets 400 for malformed JSON and 413 for an oversize
+        // body. Answer with that status and skip the stack trace; only
+        // server faults are logged.
+        const status = err?.status ?? err?.statusCode;
+        if (Number.isInteger(status) && status >= 400 && status < 500) {
+            const tooLarge = status === 413;
+            return res.status(status).json({
+                error: {
+                    code: tooLarge ? 'PAYLOAD_TOO_LARGE' : 'BAD_REQUEST',
+                    message: tooLarge ? 'Request body is too large' : 'Bad request',
+                },
+            });
+        }
         console.error(err);
         res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Something went wrong' } });
     });
diff --git a/server/test/errorHandler.test.js b/server/test/errorHandler.test.js
new file mode 100644
index 0000000..983a2d7
--- /dev/null
+++ b/server/test/errorHandler.test.js
@@ -0,0 +1,39 @@
+import { test, before, after } from 'node:test';
+import assert from 'node:assert/strict';
+import { createApp } from '../src/app.js';
+
+// The final error handler must keep a client error's own status (issue #531):
+// malformed JSON is 400 and an oversize body is 413, not 500 INTERNAL_ERROR.
+
+let server, baseUrl;
+
+before(() => {
+    const app = createApp();
+    server = app.listen(0);
+    baseUrl = `http://127.0.0.1:${server.address().port}`;
+});
+
+after(() => server.close());
+
+test('malformed JSON body returns 400 BAD_REQUEST', async () => {
+    const res = await fetch(`${baseUrl}/auth/login`, {
+        method: 'POST',
+        headers: { 'Content-Type': 'application/json' },
+        body: '{"email": ',
+    });
+    assert.equal(res.status, 400);
+    const body = await res.json();
+    assert.equal(body.error.code, 'BAD_REQUEST');
+});
+
+test('oversize JSON body returns 413 PAYLOAD_TOO_LARGE', async () => {
+    // express.json is mounted with limit: '1mb'.
+    const res = await fetch(`${baseUrl}/auth/login`, {
+        method: 'POST',
+        headers: { 'Content-Type': 'application/json' },
+        body: JSON.stringify({ padding: 'x'.repeat(2 * 1024 * 1024) }),
+    });
+    assert.equal(res.status, 413);
+    const body = await res.json();
+    assert.equal(body.error.code, 'PAYLOAD_TOO_LARGE');
+});
`````

[Back to the shelf](README.md)
