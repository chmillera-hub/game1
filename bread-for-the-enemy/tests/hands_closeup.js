// Large hands in the orientations used most in the film (for checking anatomy up close).
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const H = require('../render/hands');
const B = require('../render/body');
const { C } = require('../render/characters');
const out = process.argv[2] || 'hands_closeup.png';
const cell = 420;
const cases = [
  ['back, relaxed', 'relax', [0.2, -1, 0.1], [0.9, 0, -0.45], true],
  ['palm up, offering', 'offer', [-0.9, -0.1, 0.35], [0, 1, 0.3], false],
  ['back of hand on lap', 'relax', [0.6, -0.4, 0.7], [0, -0.8, -0.4], true],
  ['holding bread', 'cup', [0.9, 0.1, 0.3], [0.05, 1, 0.3], true],
  ['gripping', 'grip', [0.35, 0.1, 0.9], [-0.9, 0.05, -0.3], true],
  ['open palm to camera', 'open', [0.1, 1, -0.1], [0.05, 0.35, 0.93], true],
  ['raised, back to camera', 'open', [0.05, 1, 0], [0, 0, -1], true],
  ['fist, knuckles', 'fist', [1, 0.1, 0.2], [0, -0.3, -0.95], true],
];
const c = createCanvas(cell * 4, cell * 2);
const ctx = c.getContext('2d');
ctx.fillStyle = '#5a6070'; ctx.fillRect(0, 0, c.width, c.height);
const Lt = { side: -1, key: '#fff6ec', amb: '#c8b8b8', lineW: 1 };
cases.forEach(([label, sh, f, n, right], i) => {
  const x = (i % 4) * cell + cell / 2, y = Math.floor(i / 4) * cell + cell / 2;
  const fl = Math.hypot(f[0], f[1]) || 1;
  const W = [x - f[0] / fl * 110, y + f[1] / fl * 110];
  const h = H.handParts(W, 150, C.asher, Lt, { f, n, right, shape: H.preset(sh) });
  if (label === 'holding bread') {
    const g = h.gripAt(150 * 0.95);
    h.draw(ctx, (p) => p.depth < g[2]);
    B.drawBread(ctx, g[0], g[1], 150, Lt, {});
    h.draw(ctx, (p) => p.depth >= g[2]);
  } else h.draw(ctx);
  ctx.fillStyle = '#fff'; ctx.font = '20px sans-serif'; ctx.fillText(label, x - cell / 2 + 10, y - cell / 2 + 26);
});
fs.writeFileSync(out, c.toBuffer('image/png'));
