// Contact sheet for vignettes: node vtest.js <module file in vignettes/> [key ...]
// For each key renders the panel (672x480) at u = 0.05, 0.4, 0.8 plus the full portrait frame at u = 0.5,
// writes build/vtest/<key>.png and prints the average ms per frame.
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const path = require('path');
const mod = require(path.resolve(__dirname, 'vignettes', process.argv[2]));
const keys = process.argv.length > 3 ? process.argv.slice(3) : Object.keys(mod);
const out = path.join(__dirname, '..', 'build', 'vtest');
fs.mkdirSync(out, { recursive: true });
const PW = 672, PH = 480, FW = 720, FH = 1280, DUR = 8;
for (const key of keys) {
  const v = mod[key];
  if (!v) { console.log('missing', key); continue; }
  const sheet = createCanvas(PW * 2 + 30 + FW / 2, Math.max(PH * 2 + 20, FH / 2) + 40);
  const sc = sheet.getContext('2d');
  sc.fillStyle = '#333'; sc.fillRect(0, 0, sheet.width, sheet.height);
  const pc = createCanvas(PW, PH), fc = createCanvas(FW, FH);
  const params = v.testParams || {};
  let ms = 0, n = 0;
  [0.05, 0.4, 0.8].forEach((u, i) => {
    const ctx = pc.getContext('2d'); ctx.save();
    const t0 = Date.now();
    v.draw(ctx, PW, PH, { t: u * DUR, u, dur: DUR, params, seed: 7, full: false });
    ms += Date.now() - t0; n++;
    ctx.restore();
    sc.drawImage(pc, (i % 2) * (PW + 10), Math.floor(i / 2) * (PH + 10));
  });
  const ctx = fc.getContext('2d'); ctx.save();
  const t0 = Date.now();
  v.draw(ctx, FW, FH, { t: 0.5 * DUR, u: 0.5, dur: DUR, params, seed: 7, full: true });
  ms += Date.now() - t0; n++;
  ctx.restore();
  sc.drawImage(fc, PW * 2 + 20, 0, FW / 2, FH / 2);
  sc.fillStyle = '#fff'; sc.font = '20px sans-serif';
  sc.fillText(`${key}  (u=0.05, 0.4, 0.8 panel; u=0.5 full)  ${(ms / n).toFixed(1)} ms/frame`, 10, sheet.height - 12);
  fs.writeFileSync(path.join(out, `${key}.png`), sheet.toBuffer('image/png'));
  console.log(key, (ms / n).toFixed(1), 'ms/frame');
}
