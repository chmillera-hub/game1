// Contact sheet of the anatomical hand in many orientations (for visual checks).
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const H = require('../render/hands');
const { C } = require('../render/characters');
const out = process.argv[2] || 'hands_sheet.png';
const cols = 6, cell = 260;
const cases = [];
const shapes = ['open', 'relax', 'offer', 'cup', 'hold', 'grip', 'fist', 'pen'];
// fingers up, palm to camera (right then left), back to camera, palm up, palm down, hanging
const orients = [
  ['R up palm→cam', [0, 1, 0], [0, 0, 1], true],
  ['L up palm→cam', [0, 1, 0], [0, 0, 1], false],
  ['R up back→cam', [0, 1, 0], [0, 0, -1], true],
  ['R hang palm in', [0, -1, 0], [1, 0, -0.3], true],
  ['R fwd palm up', [0.3, -0.2, 0.9], [0, 1, 0], true],
  ['R side palm down', [1, -0.2, 0.2], [0, -1, 0], true],
];
for (const sh of shapes) for (const o of orients) cases.push([sh, ...o]);
const rows = Math.ceil(cases.length / cols);
const c = createCanvas(cols * cell, rows * cell);
const ctx = c.getContext('2d');
ctx.fillStyle = '#5a6070'; ctx.fillRect(0, 0, c.width, c.height);
const Lt = { side: -1, key: '#ffffff', amb: '#c8b8b8', lineW: 1 };
cases.forEach(([sh, label, f, n, right], i) => {
  const x = (i % cols) * cell + cell / 2, y = Math.floor(i / cols) * cell + cell / 2 + 20;
  const W = [x - f[0] * 60, y + f[1] * 60];
  H.drawHand3D(ctx, W, 75, C.asher, Lt, { f, n, right, shape: H.preset(sh) });
  ctx.fillStyle = '#fff'; ctx.font = '15px sans-serif'; ctx.fillText(sh + ' · ' + label, x - cell / 2 + 6, y - cell / 2 - 2);
  ctx.fillStyle = '#ff0'; ctx.beginPath(); ctx.arc(W[0], W[1], 3, 0, 6.3); ctx.fill();
});
fs.writeFileSync(out, c.toBuffer('image/png'));
console.log('wrote', out);
