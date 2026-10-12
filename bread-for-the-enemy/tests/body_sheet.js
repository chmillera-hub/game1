const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const { World } = require('../render/engine');
const { drawCharacter } = require('../render/actor');
const tl = JSON.parse(fs.readFileSync(process.env.BFE_WORK + '/timeline.json'));
const W = new World(tl);
const c = createCanvas(1620, 1100); const x = c.getContext('2d');
x.fillStyle = '#4a5560'; x.fillRect(0, 0, c.width, c.height);
const Lt = { side: -1, key: '#fff3e6', amb: '#cfc6e6', shadow: 0.7, rim: '#ffd9a0', rimA: 0.4, rimSide: 1 };
const look = { default: { gx: 0.2, gy: 0.1, yaw: 0.25, pitch: 0.05 }, bread: { gx: 0.1, gy: 0.9, yaw: 0.1, pitch: 0.25 }, cam: { gx: 0, gy: 0, yaw: 0.05, pitch: 0 } };
const cases = [
  ['jesus', 2.0, { x: 270, y: 470, s: 62, facing: 1, by: 0.1 }],
  ['jesus', 5.0, { x: 810, y: 470, s: 62, facing: 1, by: 0.1 }],
  ['asher', 30.0, { x: 1350, y: 470, s: 62, facing: 1, by: 0.3 }],
];
for (const [who, t, place] of cases) {
  const F = W.state(who, t, look);
  drawCharacter(x, who, F, place, Lt, t, {});
  x.fillStyle = '#fff'; x.font = '24px sans-serif'; x.fillText(`${who} t=${t} pose=${F.pose} emo=${F.emo}`, place.x - 250, 1060);
}
fs.writeFileSync(process.argv[2], c.toBuffer('image/png'));
