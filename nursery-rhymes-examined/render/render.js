// Frame renderer.  node render.js --frames F0 F1 --out file.mkv   |   node render.js --still T ... --png prefix
'use strict';
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const LW = path.join(__dirname, '../../the-last-witness/render');
const { createCanvas } = require(path.join(LW, 'node_modules/@napi-rs/canvas'));
const U = require(path.join(LW, 'lib/util'));
const FX = require(path.join(LW, 'lib/fx'));
const { S, W, H } = require('./lib/shots');
const { clamp, smooth, rgba } = U;

const ROOT = path.join(__dirname, '..');
const T = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/timeline.json')));
const FPS = T.fps;
const segs = T.segments;

// hummed song: envelope of the note sounding at time t (0..1)
const notes = T.song;
function song(t) {
  if (!notes.length || t < notes[0].t || t > T.songEnd) return 0;
  let lo = 0, hi = notes.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (notes[m].t <= t) lo = m; else hi = m - 1; }
  const n = notes[lo], dt = t - n.t;
  if (dt > n.dur) return 0;
  return n.vel * smooth(dt / 0.08) * (1 - 0.35 * smooth((dt - 0.1) / Math.max(0.1, n.dur)));
}
function segIndexAt(t) {
  let lo = 0, hi = segs.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (segs[m].start <= t) lo = m; else hi = m - 1; }
  return lo;
}

const main = createCanvas(W, H), ctx = main.getContext('2d');
const prevCv = createCanvas(W, H), pctx = prevCv.getContext('2d');

function drawSeg(c, seg, t) {
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over';
  const p = { t, lt: t - seg.start, u: clamp((t - seg.start) / Math.max(0.5, seg.end - seg.start)), seg, params: seg.params || {}, song, songEnd: T.songEnd };
  (S[seg.shot] || S.bus_wide)(c, p);
  c.restore();
}

function drawTitle(c, t) {
  for (const ti of T.titles) {
    if (t < ti.start || t > ti.end + 0.8) continue;
    // fully visible on the very first frame of the film; later titles fade in
    const a = (ti.start === 0 ? 1 : smooth((t - ti.start) / 0.6)) * (1 - smooth((t - ti.end + 0.2) / 1.0));
    c.save(); c.globalAlpha = a;
    const g = c.createLinearGradient(0, 160, 0, 460);
    g.addColorStop(0, 'rgba(10,10,14,0)'); g.addColorStop(0.5, 'rgba(10,10,14,0.55)'); g.addColorStop(1, 'rgba(10,10,14,0)');
    c.fillStyle = g; c.fillRect(0, 160, W, 300);
    FX.text(c, ti.text, W / 2, 290, ti.text.length > 26 ? 34 : 38, [245, 240, 228], { weight: 300, family: 'Inter Display', glow: [0, 0, 0] });
    FX.text(c, `(${ti.sound})`, W / 2, 352, 19, [210, 214, 220], { weight: 400, italic: true, alpha: 0.85 });
    c.restore();
  }
}
function subAt(t) {
  const s = T.subs;
  let lo = 0, hi = s.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (s[m].start <= t) lo = m; else hi = m - 1; }
  return s[lo] && t >= s[lo].start && t <= s[lo].end ? lo : -1;
}
function wrap(c, text, maxW) {
  const out = []; let cur = '';
  for (const w of text.split(' ')) { const tr = cur ? cur + ' ' + w : w; if (c.measureText(tr).width > maxW && cur) { out.push(cur); cur = w; } else cur = tr; }
  if (cur) out.push(cur);
  return out;
}
function drawSubs(c, t) {
  const i = subAt(t);
  if (i < 0) return;
  const s = T.subs[i], prev = T.subs[i - 1], next = T.subs[i + 1];
  const fin = prev && s.start - prev.end < 0.2 ? 1 : smooth((t - s.start) / 0.12);
  const fout = next && next.start - s.end < 0.2 ? 1 : 1 - smooth((t - s.end + 0.12) / 0.12);
  const a = fin * fout;
  if (a < 0.03) return;
  c.save();
  let size = 31, lines;
  for (;;) { c.font = `600 ${size}px Inter`; lines = wrap(c, s.text, 604); if (lines.length <= 2 || size <= 25) break; size -= 2; }
  const lh = Math.round(size * 1.32), cy = 968;
  const bw = Math.min(W - 32, Math.max(...lines.map((l) => c.measureText(l).width)) + 40), bh = lines.length * lh + 22;
  c.globalAlpha = a;
  c.fillStyle = 'rgba(8,8,12,0.58)'; c.beginPath(); c.roundRect(W / 2 - bw / 2, cy - bh / 2, bw, bh, 16); c.fill();
  c.textAlign = 'center'; c.textBaseline = 'middle';
  c.shadowColor = `rgba(0,0,0,${(0.75 * a).toFixed(3)})`; c.shadowBlur = 5;
  c.fillStyle = 'rgb(246,242,232)';
  lines.forEach((l, k) => c.fillText(l, W / 2, cy - ((lines.length - 1) * lh) / 2 + k * lh + 1));
  c.restore();
}

function renderFrame(t) {
  const i = segIndexAt(t), seg = segs[i];
  drawSeg(ctx, seg, t);
  // dissolve only where the film changes part (the bus gives way to the spider)
  const prev = segs[i - 1];
  if (prev && prev.part !== seg.part && t - seg.start < 1.6) {
    drawSeg(pctx, prev, t);
    ctx.save(); ctx.globalAlpha = 1 - smooth((t - seg.start) / 1.6); ctx.drawImage(prevCv, 0, 0); ctx.restore();
  }
  // gentle fade-out over the last seconds (never at the start)
  if (t > T.duration - 3) { ctx.save(); ctx.fillStyle = `rgba(0,0,0,${smooth((t - T.duration + 3) / 3) * 0.85})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
  drawTitle(ctx, t);
  drawSubs(ctx, t);
  return main;
}

function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv.slice(i + 1) : null; }
module.exports = { renderFrame, T };
if (require.main === module) {
  const stills = arg('--still');
  if (stills) {
    const prefix = (arg('--png') || ['../build/stills/s'])[0];
    fs.mkdirSync(path.dirname(path.resolve(__dirname, prefix)), { recursive: true });
    for (const s of stills) {
      if (s.startsWith('--')) break;
      const t = parseFloat(s), t0 = Date.now();
      renderFrame(t);
      fs.writeFileSync(path.resolve(__dirname, `${prefix}_${t.toFixed(2)}.png`), main.toBuffer('image/png'));
      console.log('still', t, Date.now() - t0, 'ms', segs[segIndexAt(t)].shot);
    }
  } else {
    const fr = arg('--frames'), out = (arg('--out') || ['../build/out.mkv'])[0];
    const f0 = parseInt(fr[0]), f1 = Math.min(parseInt(fr[1]), T.nFrames);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-',
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '10', '-pix_fmt', 'yuv420p10le', '-g', '96', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    let f = f0; const t0 = Date.now();
    const pump = () => {
      while (f < f1) {
        renderFrame(f / FPS);
        const ok = ff.stdin.write(main.data());
        f++;
        if ((f - f0) % 480 === 0) console.log(`${out}: ${f - f0}/${f1 - f0}`);
        if (!ok) { ff.stdin.once('drain', pump); return; }
      }
      ff.stdin.end();
    };
    ff.on('close', (code) => { console.log('done', out, code, ((Date.now() - t0) / 1000).toFixed(0), 's'); process.exit(code); });
    pump();
  }
}
