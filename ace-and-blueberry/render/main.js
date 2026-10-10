// Renders frames. Usage:
//   node main.js preview <t1> <t2> ...      -> PNGs in ../preview
//   node main.js video <out.raw|-> [start] [end]  -> raw RGBA frames to stdout (piped to ffmpeg)
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const fs = require('fs');
const path = require('path');
const L = require('./lib');
const { SCENE_FN, SC } = require('./scenes');

const FONTS = path.join(__dirname, '..', 'fonts');
GlobalFonts.registerFromPath(path.join(FONTS, 'Fredoka-SemiBold.ttf'), 'FredokaSB');
GlobalFonts.registerFromPath(path.join(FONTS, 'Fredoka-Bold.ttf'), 'FredokaB');
GlobalFonts.registerFromPath(path.join(FONTS, 'LuckiestGuy-Regular.ttf'), 'Luckiest Guy');

const { W, H, FPS, TL, clamp, smooth } = L;
const canvas = createCanvas(W, H);
const ctx = canvas.getContext('2d');
const off = createCanvas(W, H);
const octx = off.getContext('2d');

const COLOURS = { N: '#3B2F55', ACE: '#D9481A', BB: '#6B3FC0', BABY: '#13879B' };
const NO_CAPTION = new Set(['N_title', 'N_end']);
const XFADE = 0.35;

function sceneAt(t) {
  let s = TL.scenes[0];
  for (const sc of TL.scenes) if (t >= sc.start) s = sc;
  return s;
}

function wrap(c, text, maxW) {
  const words = text.split(' '), lines = [];
  let cur = '';
  for (const w of words) {
    const test = cur ? cur + ' ' + w : w;
    if (c.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test;
  }
  if (cur) lines.push(cur);
  return lines;
}

function caption(c, t) {
  const l = L.activeLine(t);
  if (!l || NO_CAPTION.has(l.id)) return;
  const a = Math.min(smooth((t - (l.start - 0.12)) / 0.15), 1 - smooth((t - (l.end + 0.2)) / 0.15));
  if (a <= 0) return;
  c.save();
  c.globalAlpha = a;
  c.font = '40px FredokaSB';
  const lines = wrap(c, l.text, 560);
  const lh = 49, bh = lines.length * lh + 30;
  let bw = 0; for (const s of lines) bw = Math.max(bw, c.measureText(s).width);
  bw += 56;
  const cy = 1000, top = cy - bh / 2;
  c.beginPath(); c.roundRect(W / 2 - bw / 2, top, bw, bh, 26);
  c.fillStyle = 'rgba(255,255,255,0.9)'; c.fill();
  c.strokeStyle = COLOURS[l.who]; c.globalAlpha = a * 0.6; c.lineWidth = 4; c.stroke(); c.globalAlpha = a;
  c.fillStyle = COLOURS[l.who]; c.textAlign = 'center'; c.textBaseline = 'middle';
  lines.forEach((s, i) => c.fillText(s, W / 2, top + 15 + lh / 2 + i * lh + 1));
  c.restore();
}

function drawScene(c, sc, t) {
  c.save();
  c.lineCap = 'butt'; c.lineJoin = 'miter'; c.globalAlpha = 1;
  SCENE_FN[sc.name](c, t);
  c.restore();
}

function frame(t) {
  const sc = sceneAt(t);
  drawScene(ctx, sc, t);
  // crossfade from the previous scene
  const idx = TL.scenes.indexOf(sc);
  if (idx > 0 && t - sc.start < XFADE) {
    const prev = TL.scenes[idx - 1];
    drawScene(octx, prev, Math.min(t, prev.end - 0.001));
    ctx.save(); ctx.globalAlpha = 1 - smooth((t - sc.start) / XFADE); ctx.drawImage(off, 0, 0); ctx.restore();
  }
  caption(ctx, t);
  // fade from/to black at the very start and end
  const fin = 1 - smooth(t / 0.5), fout = smooth((t - (TL.duration - 0.7)) / 0.6);
  const k = Math.max(fin, fout);
  if (k > 0) { ctx.fillStyle = `rgba(0,0,0,${k})`; ctx.fillRect(0, 0, W, H); }
}

const mode = process.argv[2];
if (mode === 'preview') {
  const outDir = path.join(__dirname, '..', 'preview');
  fs.mkdirSync(outDir, { recursive: true });
  for (const a of process.argv.slice(3)) {
    const t = parseFloat(a);
    frame(t);
    fs.writeFileSync(path.join(outDir, `f_${t.toFixed(2)}.png`), canvas.toBuffer('image/png'));
  }
} else if (mode === 'sheet') {
  // contact sheet of many times: node main.js sheet out.png cols t1 t2 ...
  const out = process.argv[3], cols = parseInt(process.argv[4]);
  const ts = process.argv.slice(5).map(parseFloat);
  const sw = W / 3, sh = H / 3, rows = Math.ceil(ts.length / cols);
  const sheet = createCanvas(cols * sw, rows * sh), sc = sheet.getContext('2d');
  ts.forEach((t, i) => {
    frame(t);
    sc.drawImage(canvas, (i % cols) * sw, Math.floor(i / cols) * sh, sw, sh);
    sc.fillStyle = '#000'; sc.font = '20px FredokaB'; sc.fillText(t.toFixed(2), (i % cols) * sw + 6, Math.floor(i / cols) * sh + 22);
  });
  fs.writeFileSync(out, sheet.toBuffer('image/png'));
} else if (mode === 'video') {
  const start = parseFloat(process.argv[3] || '0');
  const end = parseFloat(process.argv[4] || String(TL.duration));
  const n0 = Math.round(start * FPS), n1 = Math.round(end * FPS);
  const out = process.stdout;
  let i = n0;
  const writeNext = () => {
    while (i < n1) {
      frame(i / FPS);
      const data = canvas.data(); // raw RGBA
      i++;
      if (!out.write(Buffer.from(data))) { out.once('drain', writeNext); return; }
    }
    out.end();
  };
  writeNext();
}
