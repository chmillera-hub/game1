// Render review stills: 3 per shot (just after the cut, middle, just before the next cut),
// then contact sheets of 6 with timestamps + shot info. Usage: node tools/keyframes.js [from] [to]
'use strict';
const fs = require('fs'), path = require('path');
const { createCanvas } = require('@napi-rs/canvas');
const { buildFilm } = require('../src/shots');
const B = path.join(__dirname, '..', 'build');
const sched = JSON.parse(fs.readFileSync(path.join(B, 'schedule.json')));
const st = buildFilm(sched);
const from = +(process.argv[2] || 0), to = +(process.argv[3] || 1e9);
const W = 540, H = 960;
const c = createCanvas(W, H), ctx = c.getContext('2d');
const dir = path.join(B, 'review');
fs.mkdirSync(dir, { recursive: true });
const items = [];
st.shots.forEach((s, i) => {
  const t1 = i + 1 < st.shots.length ? st.shots[i + 1].t0 : sched.duration;
  const ts = [s.t0 + Math.min(0.3, (t1 - s.t0) / 3), (s.t0 + t1) / 2, t1 - 0.12];
  for (const t of ts) if (t >= from && t < to) items.push({ t, shot: i, env: s.env, actors: [...(s.actors || []), ...(s.foreground || [])].join('+') });
});
const line = (t) => { const l = sched.lines.find((x) => t >= x.t0 - 0.3 && t <= x.t1 + 0.3); return l ? `${l.id} ${l.sp}: ${l.text}` : ''; };
const sheetCols = 3, sheetRows = 2, tw = 360, th = 640;
for (let k = 0; k < items.length; k += 6) {
  const sheet = createCanvas(sheetCols * tw, sheetRows * (th + 54));
  const so = sheet.getContext('2d');
  so.fillStyle = '#1b1b1b'; so.fillRect(0, 0, sheet.width, sheet.height);
  items.slice(k, k + 6).forEach((it, j) => {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    st.render(ctx, it.t, W, H);
    fs.writeFileSync(path.join(dir, `t${it.t.toFixed(2).padStart(7, '0')}.png`), c.toBuffer('image/png'));
    const x = (j % sheetCols) * tw, y = Math.floor(j / sheetCols) * (th + 54);
    so.drawImage(c, x, y + 54, tw, th);
    so.fillStyle = '#ffd36a'; so.font = 'bold 18px sans-serif';
    so.fillText(`t=${it.t.toFixed(2)}s  shot ${it.shot} ${it.env}`, x + 6, y + 20);
    so.fillStyle = '#ddd'; so.font = '13px sans-serif';
    so.fillText(`${it.actors}`.slice(0, 48), x + 6, y + 36);
    so.fillText(line(it.t).slice(0, 52), x + 6, y + 50);
  });
  const name = `sheet_${String(k / 6).padStart(2, '0')}.png`;
  fs.writeFileSync(path.join(dir, name), sheet.toBuffer('image/png'));
}
console.log(`${items.length} stills, ${Math.ceil(items.length / 6)} sheets in build/review/`);
