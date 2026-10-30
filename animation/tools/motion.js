// Motion glitch scan: render frames small, measure frame-to-frame change, report spikes not at cuts.
// usage: node tools/motion.js <from> <to> <out.json>
'use strict';
const fs = require('fs'), path = require('path');
const { createCanvas } = require('@napi-rs/canvas');
const { buildFilm } = require('../src/shots');
const sched = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'build', 'schedule.json')));
const st = buildFilm(sched);
st.subsOn = false;
const W = 180, H = 320, FPS = 24;
const c = createCanvas(W, H), ctx = c.getContext('2d');
const [from, to, out] = process.argv.slice(2);
let prev = null;
const res = [];
for (let f = Math.round(+from * FPS); f < Math.round(+to * FPS); f++) {
  const T = f / FPS;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  st.render(ctx, T, W, H);
  const d = ctx.getImageData(0, 0, W, H).data;
  // luminance on a coarse grid
  const g = new Float32Array((W / 2) * (H / 2));
  for (let y = 0, k = 0; y < H; y += 2) for (let x = 0; x < W; x += 2, k++) { const i = (y * W + x) * 4; g[k] = 0.3 * d[i] + 0.59 * d[i + 1] + 0.11 * d[i + 2]; }
  if (prev) { let s = 0; for (let k = 0; k < g.length; k++) s += Math.abs(g[k] - prev[k]); res.push([+T.toFixed(3), +(s / g.length).toFixed(2)]); }
  prev = g;
}
fs.writeFileSync(out, JSON.stringify({ cuts: st.shots.map((s) => s.t0), diffs: res }));
