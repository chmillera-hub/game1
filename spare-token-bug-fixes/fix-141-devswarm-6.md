# Fix 141: devswarm: the last event of a model stream is dropped when the stream ends without a newline

Status: UNSENT and UNTESTED. Free to take.

- Project: himanshu748/devswarm
- Bug report title: Preserve the final SSE data line when a model stream closes
- Bug report: number 6 ([open the bug report](https://github.com/himanshu748/devswarm/issues/6))
- Project license: MIT
- Language: JavaScript
- Test included: yes
- Patch file: [fixes/141-devswarm-6.patch](fixes/141-devswarm-6.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/141-devswarm-6.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-141-devswarm-6.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-141-devswarm-6.html

## The bug

callModel in src/llm.js kept the last partial line in a buffer and never processed the buffer after the stream ended. A final data: event with no trailing newline was lost. That event often carries finish_reason. The text decoder was also never flushed at the end.

## The fix

The line handling moves into one small inner function. After the read loop the decoder is flushed and whatever is left in the buffer goes through the same function. A new file test/llm_stream_eof.test.js covers a final line with no newline and every chunk size including a cut inside a multibyte character and CRLF and usage-only events and [DONE] and malformed payloads and array content and a reasoning-only reply and finish_reason length and an empty stream.

## Files changed

- src/llm.js
- test/llm_stream_eof.test.js

## How to use the fix

1. Get a copy of the project himanshu748/devswarm.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 141-devswarm-6.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 6.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The bug report asks for a comment with the approach before work starts: nobody commented so comment first. The patch does not add the separate parser helper the report mentions as an option. The chatbot ran a scratch copy of the parsing logic with node on the same synthetic streams. The chatbot did not run the project's tests. Fixes 74 and 89 on this shelf are for the same project and touch other files.

## Search words

devswarm llm.js callModel SSE stream final data line no trailing newline buffer EOF TextDecoder flush finish_reason

## The full patch

`````diff
diff --git a/src/llm.js b/src/llm.js
index 749d646..9308f3c 100644
--- a/src/llm.js
+++ b/src/llm.js
@@ -33,29 +33,37 @@ async function callModel(model, messages, temperature, params) {
   let reasoning = '';
   let usage = {};
   let finish = null;
+  // One SSE line. A line that is not a `data:` event, `[DONE]`, or a payload
+  // that is not JSON adds nothing.
+  const consume = (line) => {
+    const payload = line.replace(/^data:\s*/, '').trim();
+    if (!payload || payload === '[DONE]' || !line.startsWith('data:')) return;
+    let data;
+    try { data = JSON.parse(payload); } catch { return; }
+    if (data.usage) usage = data.usage;
+    const choice = data.choices?.[0];
+    if (!choice) return;
+    if (choice.finish_reason) finish = choice.finish_reason;
+    const delta = choice.delta || {};
+    if (typeof delta.content === 'string') content += delta.content;
+    else if (Array.isArray(delta.content)) content += delta.content.map((p) => p.text ?? '').join('');
+    // Providers disagree on the key: most use reasoning_content, together uses reasoning.
+    if (typeof delta.reasoning_content === 'string') reasoning += delta.reasoning_content;
+    else if (typeof delta.reasoning === 'string') reasoning += delta.reasoning;
+  };
+
   let buffer = '';
   const decoder = new TextDecoder();
   for await (const chunk of res.body) {
     buffer += decoder.decode(chunk, { stream: true });
     const lines = buffer.split('\n');
     buffer = lines.pop();
-    for (const line of lines) {
-      const payload = line.replace(/^data:\s*/, '').trim();
-      if (!payload || payload === '[DONE]' || !line.startsWith('data:')) continue;
-      let data;
-      try { data = JSON.parse(payload); } catch { continue; }
-      if (data.usage) usage = data.usage;
-      const choice = data.choices?.[0];
-      if (!choice) continue;
-      if (choice.finish_reason) finish = choice.finish_reason;
-      const delta = choice.delta || {};
-      if (typeof delta.content === 'string') content += delta.content;
-      else if (Array.isArray(delta.content)) content += delta.content.map((p) => p.text ?? '').join('');
-      // Providers disagree on the key: most use reasoning_content, together uses reasoning.
-      if (typeof delta.reasoning_content === 'string') reasoning += delta.reasoning_content;
-      else if (typeof delta.reasoning === 'string') reasoning += delta.reasoning;
-    }
+    for (const line of lines) consume(line);
   }
+  // A stream can close without a final newline: flush the decoder and process
+  // what is left, or the last event (often the one with finish_reason) is lost.
+  buffer += decoder.decode();
+  if (buffer) consume(buffer);
 
   if (!content) content = reasoning;
   if (!content) throw new Error(`Empty completion from ${model} (finish: ${finish})`);
diff --git a/test/llm_stream_eof.test.js b/test/llm_stream_eof.test.js
new file mode 100644
index 0000000..b2ccc5c
--- /dev/null
+++ b/test/llm_stream_eof.test.js
@@ -0,0 +1,81 @@
+import { test, after, afterEach } from 'node:test';
+import assert from 'node:assert/strict';
+// Never export test traces to a developer's configured collector.
+delete process.env.SIGNOZ_OTLP_ENDPOINT;
+delete process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
+const { chat } = await import('../src/llm.js');
+import { promoted, demote } from '../src/models.js';
+const { swarm } = await import('../src/telemetry.js');
+
+const originalFetch = globalThis.fetch;
+const originalToken = process.env.HF_TOKEN;
+afterEach(() => {
+  globalThis.fetch = originalFetch;
+  if (originalToken === undefined) delete process.env.HF_TOKEN;
+  else process.env.HF_TOKEN = originalToken;
+  for (const role of Object.keys(promoted)) demote(role);
+});
+after(() => swarm.shutdown());
+
+const event = (delta, finish = null) => `data: ${JSON.stringify({ choices: [{ delta, finish_reason: finish }] })}`;
+
+// A synthetic stream: `text` cut into chunks of `size` bytes (the whole text when 0).
+function stream(text, size = 0) {
+  const bytes = new TextEncoder().encode(text);
+  return new Response(new ReadableStream({
+    start(controller) {
+      if (!size) controller.enqueue(bytes);
+      else for (let i = 0; i < bytes.length; i += size) controller.enqueue(bytes.slice(i, i + size));
+      controller.close();
+    }
+  }));
+}
+
+async function chatWith(text, size) {
+  process.env.HF_TOKEN = 'synthetic-test-token';
+  globalThis.fetch = async () => stream(text, size);
+  return chat('planner', [{ role: 'user', content: 'synthetic prompt' }]);
+}
+
+test('a final data line with no trailing newline is processed', async () => {
+  const text = `${event({ content: 'first ' })}\n\n${event({ content: 'last' }, 'stop')}`;
+  assert.equal(text.endsWith('\n'), false);
+  assert.equal(await chatWith(text), 'first last');
+});
+
+test('a stream that is one data line with no newline at all is processed', async () => {
+  assert.equal(await chatWith(event({ content: 'only' }, 'stop')), 'only');
+});
+
+test('content survives any chunk size, including a cut inside a multibyte character', async () => {
+  const text = `${event({ content: 'héllo 🌱 ' })}\n\n${event({ content: '世界' }, 'stop')}`;
+  for (const size of [1, 2, 3, 5, 7]) {
+    assert.equal(await chatWith(text, size), 'héllo 🌱 世界', `chunk size ${size}`);
+  }
+});
+
+test('CRLF line endings, usage-only events, [DONE] and malformed payloads are tolerated', async () => {
+  const text = [
+    event({ content: 'ok' }),
+    'data: {not json',
+    ': keep-alive comment',
+    `data: ${JSON.stringify({ usage: { total_tokens: 3 }, choices: [] })}`,
+    event({ content: '!' }, 'stop'),
+    'data: [DONE]'
+  ].join('\r\n\r\n');
+  assert.equal(await chatWith(text, 4), 'ok!');
+});
+
+test('array content and a reasoning-only reply are still read at end of stream', async () => {
+  assert.equal(await chatWith(event({ content: [{ text: 'a' }, { text: 'b' }] }, 'stop')), 'ab');
+  assert.equal(await chatWith(event({ reasoning_content: 'thought' }, 'stop')), 'thought');
+});
+
+test('finish_reason length on an unterminated final line still fails as truncated', async () => {
+  const text = `${event({ content: 'partial' })}\n\n${event({ content: ' code' }, 'length')}`;
+  await assert.rejects(chatWith(text), /Truncated completion/);
+});
+
+test('an empty stream still fails as an empty completion', async () => {
+  await assert.rejects(chatWith(''), /Empty completion/);
+});
`````

[Back to the shelf](README.md)
