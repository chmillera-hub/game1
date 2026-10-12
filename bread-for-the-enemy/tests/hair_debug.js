const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const { drawHead } = require('../render/face');
const { C } = require('../render/characters');
const base = { mouthOpen: 0, mouthWide: 0, mouthSmile: 0, lid: 0.9, lidL: 1, lidR: 1, lidLower: 0.1, lidTilt: 0, gazeX: -0.3, gazeY: 0.2, browInner: 0, browOuter: 0, browHeight: 0, browFurrow: 0, pupil: 1 };
const who = process.argv[3] || 'asher';
const c = createCanvas(1500, 560); const x = c.getContext('2d');
x.fillStyle = '#56606a'; x.fillRect(0, 0, c.width, c.height);
const views = [[0, 0], [-0.3, 0.1], [0.3, 0.1], [-0.3, -0.15], [0.35, -0.1]];
views.forEach(([yaw, pitch], i) => {
  drawHead(x, { x: 150 + i * 300, y: 260, s: 100, yaw, pitch, roll: 0 }, C[who], Object.assign({}, base), { side: -1, key: '#e8ecff', amb: '#6c6e8c', shadow: 0.72, wrap: 0.8 }, { t: 1, sway: [0, 0] });
});
fs.writeFileSync(process.argv[2], c.toBuffer('image/png'));
