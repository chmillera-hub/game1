// Render the cast side by side (and face close-ups) to check the rig art.
'use strict';
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const fs = require('fs');
const path = require('path');
const { drawCharacter } = require('../src/rig');
const { makeCast } = require('../src/chars');

const cast = makeCast();
const L = { keyDir: -2.4, keyColor: '#ffe2b8', keyAmt: 0.8, rimDir: -0.6, rimColor: '#ffd9a0', rimAmt: 0.5, shadowColor: '#3a2440', shadowAmt: 0.35, ambient: '#fff2e0', ambientAmt: 0.1 };
const out = path.join(__dirname, '..', 'build', 'preview');
fs.mkdirSync(out, { recursive: true });

function face(expr) { return { lidU: 0.15, ...expr }; }
const arg = process.argv[2] || 'all';
const W = 2400, H = 1300;
const c = createCanvas(W, H);
const ctx = c.getContext('2d');
ctx.fillStyle = '#c9b8a0'; ctx.fillRect(0, 0, W, H);
ctx.fillStyle = '#a89478'; ctx.fillRect(0, 1150, W, 150);
const list = ['maya', 'eli', 'nana', 'youngMaya', 'anger', 'annoy', 'fear', 'sadness', 'innerMaya'];
const exprs = {
  maya: { brow: 0.1, browIn: 0.4, smile: -0.2, glisten: 0.6, lidTilt: 0.3 }, eli: { smile: 0.0, browIn: -0.2 }, nana: { smile: 0.5, lidL: 0.2 },
  youngMaya: { smile: 0.7, lidL: 0.15 }, anger: { browIn: -1, browSq: 1, smile: -0.6, press: 0.5 }, annoy: { lidU: 0.45, browR: 0.6, browL: -0.1, smile: -0.2 },
  fear: { lidU: 0.0, brow: 0.6, browIn: 0.6, smile: -0.4 }, sadness: { lidU: 0.35, browIn: 0.7, smile: -0.45, lidTilt: 0.4 }, innerMaya: { smile: 0.3 },
};
list.forEach((id, i) => {
  const C = cast[id];
  const S = {
    x: 140 + i * 265, y: 1150, s: 0.95, pose: 'stand', facing: (i % 3 - 1) * 0.5,
    head: { yaw: (i % 3 - 1) * 0.5, pitch: 0, tilt: 0 }, gaze: [(i % 3 - 1) * 0.4, 0],
    face: face(exprs[id] || {}), mouth: { open: i === 4 ? 0.6 : 0 }, breath: 0,
    arms: { L: { tx: -30, ty: (C.body.upper + C.body.fore) * 0.92 }, R: { tx: 30, ty: (C.body.upper + C.body.fore) * 0.92 } },
    flame: id === 'anger' ? 0.8 : 0, glow: 1,
  };
  drawCharacter(ctx, C, S, L, 1.0);
  ctx.fillStyle = '#222'; ctx.font = 'bold 28px sans-serif'; ctx.fillText(id, S.x - 50, 1230);
});
fs.writeFileSync(path.join(out, 'lineup.png'), c.toBuffer('image/png'));
console.log('wrote lineup.png');
