// Frame renderer: node render.js <startFrame> <endFrame> <out.(mp4|png)> [png frame list]
const { spawn } = require('child_process');
const C = require('./core');
const { createCanvas, W, H, clamp, lerp, ease } = C;
const TL = require('./timeline.json');
const SCENES = require('./scenes2');
const FPS = TL.fps;

// --- build per-scene helper objects ---
function buildS(sc) {
  const L = sc.lines.map(l => ({
    spk: l.spk, s: l.start - sc.start, e: l.end - sc.start,
    c: l.chunks.map(c => ({ text: c.text, s: c.start - sc.start, e: c.end - sc.start })),
    raw: l,
  }));
  const S = { id: sc.id, dur: sc.end - sc.start, L, start: sc.start };
  S.mouth = (spks, T) => {
    if (typeof spks === 'string') spks = [spks];
    for (const l of L) {
      if (!spks.includes(l.spk)) continue;
      if (T < l.s - 0.05 || T > l.e + 0.1) continue;
      const tg = T + sc.start;
      const fi = tg * FPS - l.raw.f0;
      const i0 = Math.floor(fi), fr = fi - i0;
      const get = (arr, i) => arr[clamp(i, 0, arr.length - 1)] || 0;
      const o = lerp(get(l.raw.env, i0), get(l.raw.env, i0 + 1), fr);
      const b = lerp(get(l.raw.br, i0), get(l.raw.br, i0 + 1), fr);
      return { o: clamp(o * 0.9, 0, 1), b };
    }
    return { o: 0, b: 0.5 };
  };
  // chunk index helpers
  S.chunkAt = (i, T) => { const cs = L[i].c; let k = -1; for (let j = 0; j < cs.length; j++) if (T >= cs[j].s) k = j; return k; };
  S.cur = T => { let k = -1; for (let j = 0; j < L.length; j++) if (T >= L[j].s - 0.05) k = j; return k; };
  return S;
}
const SC = TL.scenes.map(sc => ({ sc, S: buildS(sc) }));

// --- subtitles ---
const LABEL = { TEO: ['TEO', '#9fd18b'], TEO_VO: ['TEO', '#9fd18b'], NOA: ['NOA', '#ffc857'], DAVID: ['DAVID', '#ff9d6e'], DAVID_OLD: ['DAVID', '#ff9d6e'], DAVID_CRY: ['DAVID', '#ff9d6e'],
  ABIGAIL: ['ABIGAIL', '#7fc4ff'], WOMEN: ['THE WOMEN OF ISRAEL', '#ff8fb8'], SOLOMON: ['SOLOMON', '#e6c35c'], SOLOMON_CHILD: ['YOUNG SOLOMON', '#e6c35c'],
  JESUS: ['JESUS', '#b8e0ff'], PETER: ['PETER', '#d7b38a'], AMI: ['AMI', '#ff7a6b'] };
function allChunks() {
  const out = [];
  for (const sc of TL.scenes) for (const l of sc.lines) l.chunks.forEach((c, k) => out.push({ ...c, spk: l.spk, lastInLine: k === l.chunks.length - 1 }));
  for (let i = 0; i < out.length; i++) { const n = out[i + 1]; out[i].hide = out[i].lastInLine ? Math.min(out[i].end + 0.7, n ? n.start - 0.05 : 1e9) : (n ? n.start : out[i].end + 0.7); }
  return out;
}
const CHUNKS = allChunks();
function wrap(g, text, maxW) {
  const words = text.split(' '); const lines = []; let cur = '';
  for (const w of words) { const t = cur ? cur + ' ' + w : w; if (g.measureText(t).width > maxW && cur) { lines.push(cur); cur = w; } else cur = t; }
  if (cur) lines.push(cur); return lines;
}
function drawSubs(g, t) {
  const c = CHUNKS.find(c => t >= c.start - 0.04 && t < c.hide);
  if (!c) return;
  const a = clamp((t - c.start + 0.04) / 0.08) * clamp((c.hide - t) / 0.08);
  const vo = c.spk === 'TEO_VO';
  g.save(); g.globalAlpha = a;
  g.font = `${vo ? '' : ''}38px ${vo ? 'InterSBI' : 'InterSB'}`;
  const lines = wrap(g, c.text, 600);
  const lh = 48, y0 = 1010;
  const bw = Math.max(...lines.map(l => g.measureText(l).width)) + 44;
  const bh = lines.length * lh + 22;
  const [name, col] = LABEL[c.spk] || ['', '#fff'];
  g.fillStyle = 'rgba(10,8,14,0.62)';
  g.beginPath(); g.roundRect(W / 2 - bw / 2, y0 - 6, bw, bh, 16); g.fill();
  g.font = '22px InterB'; g.textAlign = 'center';
  const nw = g.measureText(name + (vo ? ' (V.O.)' : '')).width + 22;
  g.fillStyle = col; g.beginPath(); g.roundRect(W / 2 - nw / 2, y0 - 34, nw, 30, 10); g.fill();
  g.fillStyle = '#16121a'; g.fillText(name + (vo ? ' (V.O.)' : ''), W / 2, y0 - 11);
  g.font = `38px ${vo ? 'InterSBI' : 'InterSB'}`;
  g.fillStyle = '#ffffff'; g.lineWidth = 5; g.strokeStyle = 'rgba(0,0,0,0.55)'; g.lineJoin = 'round';
  lines.forEach((l, i) => { g.strokeText(l, W / 2, y0 + 34 + i * lh); g.fillText(l, W / 2, y0 + 34 + i * lh); });
  g.restore();
}

// --- frame ---
const XF = 0.4;
const off = createCanvas(W, H), og = off.getContext('2d');
function sceneIndexAt(t) { for (let i = 0; i < SC.length; i++) if (t < SC[i].sc.end) return i; return SC.length - 1; }
function drawScene(g, i, t) {
  const { sc, S } = SC[i];
  const fn = SCENES[sc.id];
  g.save();
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  if (fn) fn(g, t - sc.start, S); else { g.fillStyle = '#334'; g.fillRect(0, 0, W, H); g.fillStyle = '#fff'; g.font = '40px InterB'; g.fillText(sc.id, 100, 300); }
  g.restore();
}
function renderFrame(g, f) {
  const t = f / FPS;
  const i = sceneIndexAt(t);
  drawScene(g, i, t);
  const nx = SC[i + 1];
  if (nx && t > SC[i].sc.end - XF) {
    drawScene(og, i + 1, t);
    g.save(); g.globalAlpha = ease((t - (SC[i].sc.end - XF)) / XF); g.drawImage(off, 0, 0); g.restore();
  }
  drawSubs(g, t);
}

module.exports = { renderFrame, SC };

if (require.main === module) {
  const [a, b, out] = process.argv.slice(2);
  const f0 = +a, f1 = +b;
  const cv = createCanvas(W, H), g = cv.getContext('2d');
  if (out.endsWith('.png')) {
    const fs = require('fs');
    const frames = process.argv.slice(5).map(Number);
    for (const f of frames.length ? frames : [f0]) { renderFrame(g, f); fs.writeFileSync(out.replace('.png', `_${f}.png`), cv.toBuffer('image/png')); }
    process.exit(0);
  }
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '10', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  let f = f0;
  function pump() {
    while (f < f1) {
      renderFrame(g, f);
      const buf = Buffer.from(g.getImageData(0, 0, W, H).data.buffer);
      f++;
      if (!ff.stdin.write(buf)) { ff.stdin.once('drain', pump); return; }
    }
    ff.stdin.end();
  }
  ff.on('close', code => { process.exit(code); });
  pump();
}
