# Fix 89: devswarm: the plan inspector leaves out the description of each API endpoint

Status: UNSENT and UNTESTED. Free to take.

- Project: himanshu748/devswarm
- Bug report title: Show planner API descriptions in the plan inspector
- Bug report: number 69 ([open the bug report](https://github.com/himanshu748/devswarm/issues/69))
- Project license: MIT
- Language: JavaScript (HTML page)
- Test included: yes
- Patch file: [fixes/89-devswarm-69.patch](fixes/89-devswarm-69.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/89-devswarm-69.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-89-devswarm-69.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-89-devswarm-69.html

## The bug

The planner writes each API entry with a field named description. The plan inspector in the app only showed a field named purpose. Normal endpoint descriptions were left out of the plan view.

## The fix

The API row template in ui/app.html now shows description and falls back to the older purpose field. A new file test/plan-inspector.test.js takes the row template out of the page source and runs the template against made-up plan entries: an entry with a description and an entry without one and an entry with both fields and an entry with text that needs escaping.

## Files changed

- test/plan-inspector.test.js
- ui/app.html

## How to use the fix

1. Get a copy of the project himanshu748/devswarm.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 89-devswarm-69.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 69.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- The chatbot ran the new test file in a scratch folder against a copy of ui/app.html and all four tests passed. That run executed the two template lines the chatbot had changed and no other project code. The test finds the template by its exact text so a later rewrite of those lines needs a matching change in the test. Keeping the older purpose field as a fallback is the chatbot's choice. Fix 74 on this shelf is for the same project and touches different files.

## Search words

devswarm plan inspector showPlan app.html API description purpose planner contract missing text

## The full patch

`````diff
diff --git a/test/plan-inspector.test.js b/test/plan-inspector.test.js
new file mode 100644
index 0000000..2c67ae9
--- /dev/null
+++ b/test/plan-inspector.test.js
@@ -0,0 +1,41 @@
+import { test } from 'node:test';
+import assert from 'node:assert/strict';
+import { readFile } from 'node:fs/promises';
+
+// showPlan() lives in an inline script of ui/app.html. These checks take the two
+// lines that render an API row out of the page source and run them against
+// synthetic plan entries, so no browser and no model call is needed.
+const page = await readFile(new URL('../ui/app.html', import.meta.url), 'utf8');
+const noteSource = page.match(/const apiNote = .*;/);
+const apiSource = page.match(/const api = \(p\.api \|\| \[\]\)\.map\([\s\S]*?\.join\(''\);/);
+
+function renderApi(entries) {
+  assert.ok(noteSource && apiSource, 'the API row template was not found in ui/app.html');
+  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
+  const run = new Function('p', 'esc', `${noteSource[0]}\n${apiSource[0]}\nreturn api;`);
+  return run({ api: entries }, esc);
+}
+
+test('an API entry with a description shows the text beside method and path', () => {
+  const html = renderApi([{ method: 'GET', path: '/api/notes', description: 'List notes, newest first.' }]);
+  assert.match(html, /<b>GET<\/b> \/api\/notes <span class="dim">List notes, newest first\.<\/span>/);
+});
+
+test('an API entry without a description still renders a row', () => {
+  const html = renderApi([{ method: 'POST', path: '/api/notes' }]);
+  assert.match(html, /<b>POST<\/b> \/api\/notes<\/li>/);
+  assert.doesNotMatch(html, /class="dim"/);
+});
+
+test('the older purpose field is still shown and description wins when both exist', () => {
+  assert.match(renderApi([{ method: 'GET', path: '/a', purpose: 'old name' }]), /old name/);
+  const both = renderApi([{ method: 'GET', path: '/a', purpose: 'old name', description: 'new name' }]);
+  assert.match(both, /new name/);
+  assert.doesNotMatch(both, /old name/);
+});
+
+test('description text is escaped', () => {
+  const html = renderApi([{ method: 'GET', path: '/a', description: '<img src=x onerror=1> & "quotes"' }]);
+  assert.doesNotMatch(html, /<img/);
+  assert.match(html, /&#60;img/);
+});
diff --git a/ui/app.html b/ui/app.html
index b35b37c..0db8a18 100644
--- a/ui/app.html
+++ b/ui/app.html
@@ -553,8 +553,10 @@ async function showPlan(id) {
           <td class="mono">${esc(f.name)}</td><td class="mono dim">${esc(f.type)}</td><td>${esc(f.rules || '')}</td>
         </tr>`).join('')}
       </table>`).join('');
+    // The planner contract names the field `description`; `purpose` is the older name some saved plans carry.
+    const apiNote = (r) => r.description || r.purpose || '';
     const api = (p.api || []).map((r) => `<li class="mono">
-      <b>${esc(r.method || '')}</b> ${esc(r.path || '')}${r.purpose ? ` <span class="dim">${esc(r.purpose)}</span>` : ''}</li>`).join('');
+      <b>${esc(r.method || '')}</b> ${esc(r.path || '')}${apiNote(r) ? ` <span class="dim">${esc(apiNote(r))}</span>` : ''}</li>`).join('');
     const chips = (list) => (list || []).map((x) => `<span class="plan-chip">${esc(typeof x === 'string' ? x : x.name || '')}</span>`).join('');
     body.innerHTML = `
       <p class="plan-summary">${esc(p.summary || '')}</p>
`````

[Back to the shelf](README.md)
