#!/usr/bin/env node
/* ==========================================================================
   snap.js — render frames of the film headlessly for review.

   node tools/snap.js --list
       print the scene table (id, start, duration)
   node tools/snap.js --scene trail --times 0,4,8 --out /tmp/shots
       one PNG per time (times are LOCAL to the scene)
   node tools/snap.js --scene trail --every 2 --sheet /tmp/trail.png
       a contact sheet (grid of frames, labelled) — best for reviewing motion
   node tools/snap.js --T 125.5 --out /tmp/shots
       absolute film time(s)
   options: --cols 4  --cell 480  --w 1920  --timing (report ms per frame)
   Exit code 1 if any scene threw an error.
   ========================================================================== */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const argv = process.argv.slice(2);
const opt = {};
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) {
    const k = a.slice(2);
    const v = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
    opt[k] = v;
  }
}
const W = +(opt.w || 1920);
const H = Math.round((W * 9) / 16);
const root = path.resolve(__dirname, '..');
const page_ = opt.page ? path.resolve(opt.page) : path.join(root, 'index.html');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const logs = [];
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') logs.push(`[${m.type()}] ${m.text()}`); });
  page.on('pageerror', (e) => logs.push(`[pageerror] ${e.message}`));
  page.on('requestfailed', (r) => logs.push(`[requestfailed] ${r.url().replace('file://' + root, '')}`));
  await page.goto('file://' + page_ + '?test&w=' + W);
  await page.waitForFunction(() => window.Film && window.Film.ready, null, { timeout: 20000 });
  const info = await page.evaluate(() => ({ duration: FILM.duration, scenes: FILM.scenes }));

  if (opt.list) {
    console.log(`total ${info.duration.toFixed(1)}s (${Math.floor(info.duration / 60)}m${Math.round(info.duration % 60)}s)`);
    for (const s of info.scenes) console.log(`${String(s.order).padStart(2)}  ${s.id.padEnd(16)} start ${s.start.toFixed(1).padStart(6)}  dur ${s.duration.toFixed(1).padStart(5)}  ${s.title}`);
    if (logs.length) console.log(logs.join('\n'));
    await browser.close();
    return;
  }

  let base = 0, span = info.duration, label = 'film';
  if (opt.scene) {
    const s = info.scenes.find((x) => x.id === opt.scene);
    if (!s) { console.error('no scene ' + opt.scene + '. scenes: ' + info.scenes.map((x) => x.id).join(', ')); await browser.close(); process.exit(2); }
    base = s.start; span = s.duration; label = s.id;
  }
  let times = [];
  if (opt.times) times = String(opt.times).split(',').map(Number);
  else if (opt.T) { base = 0; times = String(opt.T).split(',').map(Number); }
  else {
    const every = +(opt.every || Math.max(1, span / 12));
    for (let t = 0; t < span - 0.01; t += every) times.push(+t.toFixed(3));
    times.push(+(span - 0.05).toFixed(3));
  }

  const out = opt.out ? path.resolve(opt.out) : null;
  if (out) fs.mkdirSync(out, { recursive: true });
  const cols = +(opt.cols || 4), cell = +(opt.cell || 480);
  const results = await page.evaluate(async ({ times, base, sheet, cols, cell, label, timing }) => {
    const cv = FILM.canvas();
    const rows = Math.ceil(times.length / cols);
    const ch = Math.round((cell * 9) / 16);
    let sc, sx;
    if (sheet) {
      sc = document.createElement('canvas');
      sc.width = cols * cell; sc.height = rows * (ch + 26);
      sx = sc.getContext('2d');
      sx.fillStyle = '#111'; sx.fillRect(0, 0, sc.width, sc.height);
    }
    const shots = [], ms = [];
    for (let i = 0; i < times.length; i++) {
      const T = base + times[i];
      const t0 = performance.now();
      FILM.renderAt(T);
      ms.push(performance.now() - t0);
      if (timing) { for (let r = 0; r < 2; r++) { const a = performance.now(); FILM.renderAt(T + 0.016 * (r + 1)); ms.push(performance.now() - a); } FILM.renderAt(T); }
      if (sheet) {
        const x = (i % cols) * cell, y = Math.floor(i / cols) * (ch + 26);
        sx.drawImage(cv, x, y, cell, ch);
        sx.fillStyle = '#ddd'; sx.font = '15px sans-serif';
        sx.fillText(`${label} t=${times[i].toFixed(2)}  (T=${T.toFixed(1)})`, x + 6, y + ch + 18);
      } else shots.push(cv.toDataURL('image/png'));
    }
    return { shots, sheet: sheet ? sc.toDataURL('image/png') : null, ms, errors: FILM.errors };
  }, { times, base, sheet: !!opt.sheet, cols, cell, label, timing: !!opt.timing });

  if (opt.sheet) {
    const f = path.resolve(String(opt.sheet));
    fs.mkdirSync(path.dirname(f), { recursive: true });
    fs.writeFileSync(f, Buffer.from(results.sheet.split(',')[1], 'base64'));
    console.log('sheet → ' + f + `  (${times.length} frames)`);
  }
  if (out) {
    results.shots.forEach((d, i) => {
      const f = path.join(out, `${label}-${String(times[i].toFixed(2)).replace('.', '_')}.png`);
      fs.writeFileSync(f, Buffer.from(d.split(',')[1], 'base64'));
      console.log('frame → ' + f);
    });
  }
  const avg = results.ms.reduce((a, b) => a + b, 0) / results.ms.length;
  const max = Math.max(...results.ms);
  console.log(`render ms: avg ${avg.toFixed(1)}  max ${max.toFixed(1)}  (headless software raster; real GPUs are much faster)`);
  if (logs.length) console.log('console:\n' + logs.join('\n'));
  if (results.errors.length) {
    console.log('SCENE ERRORS:');
    for (const e of results.errors) console.log(`  [${e.scene}] ${e.message}\n${(e.stack || '').split('\n').slice(0, 4).join('\n')}`);
    await browser.close();
    process.exit(1);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(3); });
