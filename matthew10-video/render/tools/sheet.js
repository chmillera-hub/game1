'use strict';
// Renders a grid of expressions for one character: node tools/sheet.js <who> <out.png> [outfit]
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const { drawCharacter } = require('../lib/character');
const { makeCast } = require('../lib/cast');
const { EXPR } = require('../lib/expressions');
const who = process.argv[2] || 'maya';
const out = process.argv[3] || '/tmp/sheet.png';
const cast = makeCast(process.argv[4] ? { [who]: process.argv[4] } : {});
const A = cast[who];
const cells = [
  ['neutral', {}], ['soft_smile', {}], ['fake_smile', {}], ['sad', { gazeY: 0.5 }],
  ['hurt', {}], ['stung', {}], ['earnest', { open: 0.5 }], ['crying', { tears: [{ side: -1, t: 0.6 }] }],
  ['neutral', { yaw: 0.7, gazeX: 0.5 }], ['neutral', { yaw: -0.7, gazeX: -0.6 }], ['neutral', { pitch: 0.6, gazeY: 0.7 }], ['joy', { open: 0.3 }],
  ['neutral', { blink: 1 }], ['surprised', {}], ['resolved', { yaw: 0.3 }], ['tender', { roll: 0.12 }],
];
const W = 1600, H = 1800, cw = W / 4, ch = H / 4;
const c = createCanvas(W, H); const ctx = c.getContext('2d');
ctx.fillStyle = '#d8d2c8'; ctx.fillRect(0, 0, W, H);
cells.forEach(([e, extra], i) => {
  const x = (i % 4) * cw + cw / 2, y = Math.floor(i / 4) * ch;
  ctx.save(); ctx.beginPath(); ctx.rect(x - cw / 2, y, cw, ch); ctx.clip();
  ctx.fillStyle = i % 2 ? '#cfc8bd' : '#d8d2c8'; ctx.fillRect(x - cw / 2, y, cw, ch);
  const P = { x, y: y + ch * 0.86, scale: 215, ...EXPR[e], ...extra };
  drawCharacter(ctx, A, P, { light: { x: -0.6, y: -0.8 } });
  ctx.fillStyle = '#222'; ctx.font = '22px Inter'; ctx.fillText(e + (Object.keys(extra).length ? ' ' + JSON.stringify(extra).slice(0, 26) : ''), x - cw / 2 + 8, y + 26);
  ctx.restore();
});
fs.writeFileSync(out, c.toBuffer('image/png'));
console.log('wrote', out);
