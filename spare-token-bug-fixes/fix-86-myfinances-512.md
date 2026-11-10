# Fix 86: MyFinances: dates in the Health surplus analysis follow the browser language and not the app language

Status: UNSENT and UNTESTED. Free to take.

- Project: jasonkryst/MyFinances
- Bug report title: i18n: Health surplus dates use toLocaleDateString() without the app locale
- Bug report: number 512 ([open the bug report](https://github.com/jasonkryst/MyFinances/issues/512))
- Project license: MIT
- Language: JavaScript
- Test included: yes
- Patch file: [fixes/86-myfinances-512.patch](fixes/86-myfinances-512.patch)
- Direct download address for programs and chatbots: https://raw.githubusercontent.com/chmillera-hub/spare-token-bug-fixes/main/fixes/86-myfinances-512.patch
- Same page on GitHub: https://github.com/chmillera-hub/spare-token-bug-fixes/blob/main/fix-86-myfinances-512.md
- Same page as a plain website page: https://chmillera-hub.github.io/game1/spare-token-bug-fixes/fix-86-myfinances-512.html

## The bug

Four places in the Health surplus analysis formatted dates with the browser's own language setting. When the browser language and the app language differ the dates in that part of the app looked different from the dates in the other parts of the app.

## The fix

The four places in src/health.js now call formatShortDate from utils.js which formats with the app language. A new file tests/unit/healthDateLocale.test.js reads src/health.js and fails when any date call without a language remains.

## Files changed

- src/health.js
- tests/unit/healthDateLocale.test.js

## How to use the fix

1. Get a copy of the project jasonkryst/MyFinances.
2. Download the patch file from the direct download address shown near the top of this page.
3. Run: git apply 86-myfinances-512.patch
4. Run the project's own tests.
5. Read the project's contribution rules and then open a pull request that mentions bug report 512.

## Warnings

- An AI chatbot (Claude) wrote this fix. No human has reviewed the fix.
- Nobody has run the fix against the project's own test suite.
- The chatbot read the full bug report text and could not read the comments under the bug report.
- Nobody has checked whether someone else already sent a fix for the same bug.
- The fix was written against the project's code as of 2026-11-10 and may no longer apply cleanly.
- The patch applied cleanly to the project's newest code on 2026-11-10 (checked with git apply --check).
- Nobody has sent the fix to the project. Anyone is free to test the fix and send the fix.
- formatShortDate writes a date in the short month form (for example Nov 9 2026 in English) so the dates and the chart labels in the surplus analysis look different from before. The new test checks the source text and does not render the page. The chatbot ran the two text checks from the test over the file before and after the change. The chatbot did not run the project's tests. Fixes 73 and 80 on this shelf are for the same project and touch different files.

## Search words

MyFinances health.js toLocaleDateString locale formatShortDate getIntlLocale surplus analysis i18n

## The full patch

`````diff
diff --git a/src/health.js b/src/health.js
index db02d28..6ceb5bb 100644
--- a/src/health.js
+++ b/src/health.js
@@ -547,7 +547,7 @@ function renderSurplusSection(app) {
     const dipWarningHtml = (surplus > 0 && minBalance < minimumReserve) ? `
         <div class="health-surplus-dip-warning">
             &#9888; Balance dips to ${escapeHtml(formatCurrency(minBalance))} on
-            ${escapeHtml(minDate instanceof Date ? minDate.toLocaleDateString() : String(minDate))}
+            ${escapeHtml(minDate instanceof Date ? formatShortDate(minDate) : String(minDate))}
             &mdash; below your minimum reserve.
         </div>` : '';
 
@@ -561,7 +561,7 @@ function renderSurplusSection(app) {
         const cls  = tx.originalAmount >= 0 ? 'health-cf-income' : 'health-cf-out';
         return `<div class="health-surplus-tx-row">
             <span class="health-surplus-tx-name">${escapeHtml(tx.name || '')}</span>
-            <span class="health-surplus-tx-date">${escapeHtml(tx.date instanceof Date ? tx.date.toLocaleDateString() : String(tx.date))}</span>
+            <span class="health-surplus-tx-date">${escapeHtml(tx.date instanceof Date ? formatShortDate(tx.date) : String(tx.date))}</span>
             <span class="health-surplus-tx-amt ${cls}">${sign}${escapeHtml(formatCurrency(tx.originalAmount))}</span>
         </div>`;
     }
@@ -660,7 +660,7 @@ function renderSurplusSection(app) {
         app._healthSurplusSparkline = new Chart(sparkCanvas, {
             type: 'line',
             data: {
-                labels: sparkPoints.map(p => p.date instanceof Date ? p.date.toLocaleDateString() : String(p.date)),
+                labels: sparkPoints.map(p => p.date instanceof Date ? formatShortDate(p.date) : String(p.date)),
                 datasets: [
                     {
                         label: 'Projected balance',
@@ -715,7 +715,7 @@ function renderSurplusSection(app) {
             caption: t('health.surplusSparklineCaption', { days: windowDays }),
             columns: ['Date', 'Balance'],
             rows: sparkPoints.map(p => [
-                p.date instanceof Date ? p.date.toLocaleDateString() : String(p.date),
+                p.date instanceof Date ? formatShortDate(p.date) : String(p.date),
                 formatCurrency(p.balance),
             ]),
         });
diff --git a/tests/unit/healthDateLocale.test.js b/tests/unit/healthDateLocale.test.js
new file mode 100644
index 0000000..202a711
--- /dev/null
+++ b/tests/unit/healthDateLocale.test.js
@@ -0,0 +1,18 @@
+// Health surplus dates must follow the app locale (issue #512): every
+// toLocaleDateString() call in src/health.js has to pass a locale, and the
+// surplus analysis uses formatShortDate() from utils.js.
+const fs = require('fs');
+const path = require('path');
+
+const source = fs.readFileSync(path.join(__dirname, '../../src/health.js'), 'utf8');
+
+describe('src/health.js date formatting', () => {
+    test('no toLocaleDateString() call is made without a locale argument', () => {
+        expect(source).not.toMatch(/\.toLocaleDateString\(\s*\)/);
+    });
+
+    test('the surplus analysis formats Date values with formatShortDate', () => {
+        const calls = source.match(/instanceof Date \? formatShortDate\(/g) || [];
+        expect(calls).toHaveLength(4);
+    });
+});
`````

[Back to the shelf](README.md)
