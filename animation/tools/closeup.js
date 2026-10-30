// Single large close-up of one character with an expression (detail check).
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs'), path = require('path');
const { drawCharacter, skeleton } = require('../src/rig');
const { makeCast } = require('../src/chars');
const { faceOf, resolveFace } = require('../src/acting');
const cast = makeCast();
const [id = 'maya', ex = 'sad', yaw = '0.3', open = '0'] = process.argv.slice(2);
const C = cast[id];
const L = { keyDir: -2.4, keyColor: '#ffd8a8', keyAmt: 0.8, rimDir: -0.4, rimColor: '#ffcf90', rimAmt: 0.6, shadowColor: '#3a2440', shadowAmt: 0.38, ambient: '#fff2e0', ambientAmt: 0.1 };
const c = createCanvas(1080, 1080), ctx = c.getContext('2d');
const g = ctx.createLinearGradient(0, 0, 0, 1080); g.addColorStop(0, '#6e5a4c'); g.addColorStop(1, '#3a2e2a');
ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 1080);
const S = { x: 0, y: 0, s: 1, pose: 'stand', facing: +yaw * 0.7, head: { yaw: +yaw, pitch: 0, tilt: 2 }, gaze: [+yaw * -0.4, 0.05],
  face: resolveFace(faceOf(ex)), mouth: { open: +open, wide: 0.2 }, breath: 0, glow: 1, flame: id === 'anger' ? 0.7 : 0,
  arms: { L: { tx: -10, ty: 300 }, R: { tx: 10, ty: 300 } }, tears: ex.startsWith('tear') || ex === 'cry' ? [{ eye: 1, t0: 0, dur: 3 }] : [] };
const sk = skeleton(C, S);
const z = 3.4 * 150 / C.head.h;
ctx.translate(540, 470); ctx.scale(z, z); ctx.translate(-sk.headC[0], -sk.headC[1]);
drawCharacter(ctx, C, S, L, 1.5);
fs.writeFileSync(path.join(__dirname, '..', 'build', 'preview', `close_${id}_${ex}.png`), c.toBuffer('image/png'));
console.log('ok');
