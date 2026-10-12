const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const { drawHead } = require('../render/face');
const st = { skin: '#e9bf9c', skinShadow: '#c08a72', line: '#3a221c', iris: '#5b3b25', browColor: '#2e1d16' };
const base = { mouthOpen: 0, mouthWide: 0, mouthSmile: 0, lid: 1, lidL: 1, lidR: 1, lidLower: 0, lidTilt: 0, gazeX: 0, gazeY: 0, browInner: 0, browOuter: 0, browHeight: 0, browFurrow: 0, pupil: 1 };
const cases = [
  ['neutral', {}, 0], ['yaw+.35', {}, 0.35], ['yaw-.35', {}, -0.35],
  ['sad', { browInner: 0.8, lid: 0.7, lidTilt: -0.5, mouthSmile: -0.4 }, 0.2],
  ['angry', { browInner: -0.7, browFurrow: 0.9, lid: 0.9, lidLower: 0.35, lidTilt: 0.5, mouthSmile: -0.3, mouthPress: 0.4 }, -0.2],
  ['smile', { mouthSmile: 0.7, lidLower: 0.45, cheekRaise: 0.5, lid: 0.85 }, 0.15],
  ['talk A', { mouthOpen: 0.8, mouthWide: 0.1 }, 0.1], ['talk O', { mouthOpen: 0.6, mouthWide: -0.9 }, -0.1],
  ['cry', { browInner: 1, lid: 0.55, lidLower: 0.5, mouthOpen: 0.25, mouthSmile: -0.6, tears: 1, tearFlow: 1 }, 0.25],
  ['shock', { browHeight: 0.9, browInner: 0.5, lid: 1.3, pupil: 0.75, mouthOpen: 0.4 }, 0],
  ['look down', { gazeY: 0.8, lid: 0.6 }, 0.1, 0.25], ['closed', { lid: 0 }, 0.3],
];
const W = 360, Hh = 420, cols = 4;
const c = createCanvas(W * cols, Hh * Math.ceil(cases.length / cols)); const x = c.getContext('2d');
x.fillStyle = '#6d7a86'; x.fillRect(0, 0, c.width, c.height);
cases.forEach(([name, f, yaw, pitch], i) => {
  const cx = (i % cols) * W + W / 2, cy = Math.floor(i / cols) * Hh + 170;
  const F = Object.assign({}, base, f);
  drawHead(x, { x: cx, y: cy, s: 105, yaw, pitch: pitch || 0, roll: 0 }, st, F, { side: -1, key: '#fff6ec', amb: '#d8d4ee', shadow: 0.8 }, { t: 1.3 });
  x.fillStyle = '#fff'; x.font = '22px sans-serif'; x.fillText(name, cx - 150, cy + 230);
});
fs.writeFileSync(process.argv[2], c.toBuffer('image/png'));
