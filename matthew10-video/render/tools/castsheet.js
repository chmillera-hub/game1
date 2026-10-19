'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const { drawCharacter } = require('../lib/character');
const { makeCast } = require('../lib/cast');
const { EXPR } = require('../lib/expressions');
const cast = makeCast();
const rows = [
  ['mom', ['bright', 'dismissive', 'placating', 'cracking']],
  ['dad', ['closed', 'irritated', 'weary', 'neutral']],
  ['jordan', ['awkward', 'guilty', 'neutral', 'soft_smile']],
  ['greg', ['chipper', 'patronizing', 'impatient', 'neutral']],
  ['priya', ['warm', 'smile', 'attentive', 'neutral']],
];
const W = 1600, cw = 400, ch = 420, H = ch * rows.length;
const c = createCanvas(W, H); const ctx = c.getContext('2d');
rows.forEach(([who, exprs], r) => exprs.forEach((e, i) => {
  const x = i * cw + cw / 2, y = r * ch;
  ctx.save(); ctx.beginPath(); ctx.rect(x - cw / 2, y, cw, ch); ctx.clip();
  ctx.fillStyle = (i + r) % 2 ? '#cfc8bd' : '#d8d2c8'; ctx.fillRect(x - cw / 2, y, cw, ch);
  drawCharacter(ctx, cast[who], { x, y: y + ch * 0.82, scale: 200, ...EXPR[e], yaw: i === 3 ? 0.4 : 0 }, { light: { x: -0.6, y: -0.8 } });
  ctx.fillStyle = '#222'; ctx.font = '22px Inter'; ctx.fillText(who + ': ' + e, x - cw / 2 + 8, y + 26);
  ctx.restore();
}));
fs.writeFileSync(process.argv[2], c.toBuffer('image/png'));
