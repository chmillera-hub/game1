const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const { drawHead } = require('../render/face');
const { C } = require('../render/characters');
const base = { mouthOpen: 0, mouthWide: 0, mouthSmile: 0, lid: 0.9, lidL: 1, lidR: 1, lidLower: 0.1, lidTilt: 0, gazeX: 0.2, gazeY: 0, browInner: 0, browOuter: 0, browHeight: 0, browFurrow: 0, pupil: 1 };
const names = ['jesus', 'paul', 'asher', 'yosef', 'saul', 'saul_travel', 'child', 'guard', 'elder'];
const extraF = { jesus: { mouthSmile: 0.3, lid: 0.78, browInner: 0.25 }, paul: { browInner: 0.3, mouthOpen: 0.3 }, asher: { browFurrow: 0.5, browInner: -0.3, mouthPress: 0.4 } };
const W = 400, Hh = 560, cols = 3;
const c = createCanvas(W * cols, Hh * Math.ceil(names.length / cols)); const x = c.getContext('2d');
x.fillStyle = '#56606a'; x.fillRect(0, 0, c.width, c.height);
names.forEach((n, i) => {
  const cx = (i % cols) * W + W / 2, cy = Math.floor(i / cols) * Hh + 230;
  const F = Object.assign({}, base, extraF[n] || {});
  drawHead(x, { x: cx, y: cy, s: 95, yaw: i % 2 ? -0.3 : 0.3, pitch: 0, roll: 0 }, C[n], F, { side: -1, key: '#fff4e8', amb: '#d0cce8', shadow: 0.8, rim: '#ffe0b0', rimA: 0.5, rimSide: 1 }, { t: 1.3, sway: [0, 0] });
  x.fillStyle = '#fff'; x.font = '22px sans-serif'; x.fillText(n, cx - 170, cy + 300);
});
fs.writeFileSync(process.argv[2], c.toBuffer('image/png'));
