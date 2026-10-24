/* Screenshot the figurine contact sheet.
   node tools/art-shot.js out.png [id,id,...] [--size 160] [--width 1200] */
'use strict';
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const args = process.argv.slice(2);
  const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
  const out = args[0];
  const ids = args[1] && !args[1].startsWith('--') ? args[1] : '';
  const q = new URLSearchParams();
  if (ids) q.set('ids', ids);
  q.set('size', opt('--size', '104'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +opt('--width', '1200'), height: 600 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('file://' + path.join(__dirname, 'art-sheet.html') + '?' + q);
  await page.waitForTimeout(300);
  await page.screenshot({ path: out, fullPage: true });
  await browser.close();
  if (errors.length) { console.log('errors:\n' + errors.join('\n')); process.exit(1); }
  console.log('wrote ' + out);
})();
