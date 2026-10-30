// Close-up grid: expressions on one character + hand poses.
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs'), path = require('path');
const { drawCharacter, drawHand, HANDS } = require('../src/rig');
const { makeCast } = require('../src/chars');
const { EXPR } = require('../src/acting');
const cast = makeCast();
const L = { keyDir: -2.4, keyColor: '#ffe2b8', keyAmt: 0.8, rimDir: -0.6, rimColor: '#ffd9a0', rimAmt: 0.5, shadowColor: '#3a2440', shadowAmt: 0.35, ambient: '#fff2e0', ambientAmt: 0.1 };
const id = process.argv[2] || 'maya';
const C = cast[id];
const names = Object.keys(EXPR);
const cols = 6, cell = 420;
const rows = Math.ceil(names.length / cols) + 1;
const c = createCanvas(cols * cell, rows * cell);
const ctx = c.getContext('2d');
ctx.fillStyle = '#cdbca6'; ctx.fillRect(0, 0, c.width, c.height);
names.forEach((n, i) => {
  const cx = (i % cols) * cell + cell / 2, cy = Math.floor(i / cols) * cell;
  ctx.save();
  ctx.beginPath(); ctx.rect(cx - cell / 2, cy, cell, cell); ctx.clip();
  const z = 1.25 * 150 / C.head.h;
  const S = { x: 0, y: 0, s: 1, pose: 'stand', facing: i % 2 ? 0.35 : -0.2, head: { yaw: i % 2 ? 0.45 : -0.25, pitch: 0, tilt: i % 3 - 1 }, gaze: [i % 2 ? 0.3 : -0.2, 0.05],
    face: { ...EXPR[n] }, mouth: { open: n.includes('shout') || n === 'surprised' ? 0.7 : 0 }, breath: 0, flame: 0, glow: 0,
    arms: { L: { tx: -20, ty: 300 }, R: { tx: 20, ty: 300 } }, tears: n === 'cry' ? [{ eye: -1, t0: 0, dur: 3 }] : [] };
  ctx.translate(cx, cy + cell * 0.55);
  ctx.scale(z, z);
  // place head centre near the cell middle
  const { skeleton } = require('../src/rig');
  const sk = skeleton(C, S);
  ctx.translate(-sk.headC[0], -sk.headC[1]);
  drawCharacter(ctx, C, S, L, 1.6);
  ctx.restore();
  ctx.fillStyle = '#222'; ctx.font = 'bold 26px sans-serif'; ctx.fillText(n, cx - cell / 2 + 10, cy + 30);
});
// hand poses row
const hn = Object.keys(HANDS);
hn.forEach((n, i) => {
  const x = 80 + i * (c.width - 100) / hn.length, y = (rows - 1) * cell + cell * 0.5;
  for (const [k, view] of [[0, 'back'], [1, 'palm']]) {
    ctx.save(); ctx.translate(x + k * 0, y + (k ? 120 : -80)); ctx.rotate(-Math.PI / 2); ctx.scale(1.6, 1.6);
    drawHand(ctx, cast.maya, HANDS[n], 1, view, L);
    ctx.restore();
  }
  ctx.fillStyle = '#222'; ctx.font = 'bold 24px sans-serif'; ctx.fillText(n, x - 20, (rows - 1) * cell + 30);
});
fs.writeFileSync(path.join(__dirname, '..', 'build', 'preview', `faces_${id}.png`), c.toBuffer('image/png'));
console.log('ok');
