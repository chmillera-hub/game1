// Render a contact sheet of shots for review.
// Usage: node tools/sheet.mjs <out.png> <spec> [<spec> ...]   spec = shotId[:lt[:take[:dur]]]  or  t=<seconds>
import path from 'node:path';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import { serve } from './snap.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const [out, ...specs] = process.argv.slice(2);
const srv = await serve();
const browser = await chromium.launch();
const pg = await (await browser.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
pg.on('console', (m) => { if (m.type() === 'error') console.log('[console]', m.text()); });
await pg.goto(`http://127.0.0.1:${srv.address().port}/index.html`);
await pg.waitForFunction(() => window.__ready === true);
const tmp = fs.mkdtempSync(path.join(path.dirname(out), 'sheet-'));
const files = [];
for (const [i, spec] of specs.entries()) {
  if (spec.startsWith('t=')) {
    await pg.evaluate(async (t) => { await E.renderAt(t); }, +spec.slice(2));
  } else {
    const [id, lt = '2', take = '1', dur = '8'] = spec.split(':');
    await pg.evaluate(async ([id, lt, take, dur]) => { await E.renderShot(id, lt, take, dur); }, [id, +lt, +take, +dur]);
  }
  const f = path.join(tmp, `s${String(i).padStart(2, '0')}.png`);
  await pg.screenshot({ path: f });
  files.push(f);
}
await browser.close();
srv.close();
const cols = Math.min(files.length, +(process.env.COLS || 5));
const rows = Math.ceil(files.length / cols);
const args = [];
files.forEach((f) => args.push('-i', f));
const fc = files.map((_, i) => `[${i}]scale=360:640,drawtext=text='${specs[i].replace(/:/g, ' ')}':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6[v${i}]`).join(';') +
  ';' + files.map((_, i) => `[v${i}]`).join('') + `xstack=inputs=${files.length}:layout=` +
  files.map((_, i) => `${(i % cols) * 360}_${Math.floor(i / cols) * 640}`).join('|') + (files.length < cols * rows ? ':fill=black' : '');
execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...args, '-filter_complex', fc, out]);
fs.rmSync(tmp, { recursive: true });
console.log('wrote', out);
