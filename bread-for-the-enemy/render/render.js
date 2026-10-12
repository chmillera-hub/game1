// Frame renderer.
//   node render/render.js --timeline T.json --still 12.5 --out frame.png
//   node render/render.js --timeline T.json --from 0 --to 240 > raw.rgba   (raw RGBA frames on stdout)
'use strict';
const path = require('path');
const fs = require('fs');
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const L = require('./lib');
const { clamp, lerp, rgba, smooth } = L;
const { World } = require('./engine');
const { SHOTS, grade, VW, VH } = require('./shots');

const args = {};
for (let i = 2; i < process.argv.length; i += 2) args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
const OUT_W = parseInt(args.width || '720', 10);
const R = OUT_W / VW;
global.RENDER_SCALE = R;
const OUT_H = Math.round(VH * R);

const FONTS = args.fonts || path.join(__dirname, '..', 'fonts');
for (const f of fs.existsSync(FONTS) ? fs.readdirSync(FONTS) : []) {
  if (f.endsWith('.ttf')) GlobalFonts.registerFromPath(path.join(FONTS, f));
}
const SANS = GlobalFonts.has('Inter') ? 'Inter' : 'sans-serif';

const tl = JSON.parse(fs.readFileSync(args.timeline, 'utf8'));
const W = new World(tl);
const FPS = tl.fps;

function shotAt(t) {
  let i = tl.shots.findIndex((s) => t >= s.start && t < s.end);
  if (i < 0) i = t < tl.shots[0].start ? 0 : tl.shots.length - 1;
  return i;
}

const main = createCanvas(OUT_W, OUT_H);
const mctx = main.getContext('2d');
const tmp = createCanvas(OUT_W, OUT_H);
const tctx = tmp.getContext('2d');

function drawShot(ctx, idx, t) {
  const sh = tl.shots[idx];
  const fn = SHOTS[sh.id];
  ctx.save();
  ctx.setTransform(R, 0, 0, R, 0, 0);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, VW, VH);
  if (fn) fn(ctx, W, t, t - sh.start, sh.end - sh.start, sh.params || {});
  else { ctx.fillStyle = '#333'; ctx.fillRect(0, 0, VW, VH); ctx.fillStyle = '#fff'; ctx.font = '50px sans-serif'; ctx.fillText(sh.id, 100, 900); }
  ctx.restore();
  ctx.save();
  ctx.setTransform(R, 0, 0, R, 0, 0);
  grade(ctx, sh.params && sh.params.grade, t - sh.start);
  ctx.restore();
}

const TRANS = { dissolve: 0.8, memory: 0.7, memory_out: 0.7 };

function renderFrame(t) {
  const idx = shotAt(t);
  const sh = tl.shots[idx];
  drawShot(mctx, idx, t);
  const tr = sh.params && sh.params.trans;
  const lt = t - sh.start;
  if (tr && TRANS[tr] && lt < TRANS[tr] && idx > 0) {
    const k = smooth(lt / TRANS[tr]);
    drawShot(tctx, idx - 1, t);
    mctx.save();
    mctx.globalAlpha = 1 - k;
    mctx.drawImage(tmp, 0, 0);
    mctx.restore();
    if (tr === 'memory' || tr === 'memory_out') {
      const fl = Math.sin(clamp(lt / TRANS[tr]) * Math.PI);
      mctx.save();
      mctx.globalCompositeOperation = 'screen';
      mctx.fillStyle = rgba(tr === 'memory' ? '#c8d8ff' : '#fff0d8', 0.55 * fl);
      mctx.fillRect(0, 0, OUT_W, OUT_H);
      mctx.restore();
    }
  }
  mctx.save();
  mctx.setTransform(R, 0, 0, R, 0, 0);
  drawTexts(mctx, t);
  drawSubs(mctx, t);
  mctx.restore();
}

// ------------------------------------------------------------ text cards
function spaced(ctx, text, x, y, spacing) {
  // centered text with letter spacing
  let w = 0;
  for (const ch of text) w += ctx.measureText(ch).width + spacing;
  w -= spacing;
  let cx = x - w / 2;
  for (const ch of text) { ctx.fillText(ch, cx, y); cx += ctx.measureText(ch).width + spacing; }
}
function drawTexts(ctx, t) {
  for (const tx of tl.texts) {
    const lt = t - tx.t;
    if (lt < 0 || lt > tx.dur) continue;
    ctx.save();
    ctx.textBaseline = 'alphabetic';
    if (tx.style === 'title') {
      const a = tx.t <= 0.01 ? 1 - smooth((lt - (tx.dur - 0.9)) / 0.9) : Math.min(smooth(lt / 0.6), 1 - smooth((lt - (tx.dur - 0.9)) / 0.9));
      ctx.globalAlpha = a;
      ctx.fillStyle = L.radial(ctx, 540, 330, 50, 620, [[0, rgba('#000000', 0.55)], [1, rgba('#000000', 0)]]);
      ctx.fillRect(0, 60, VW, 560);
      ctx.font = `700 84px Cinzel`;
      ctx.shadowColor = 'rgba(0,0,0,0.85)'; ctx.shadowBlur = 18;
      ctx.fillStyle = L.linear(ctx, 0, 260, 0, 360, [[0, '#fff3cf'], [0.5, '#f0c868'], [1, '#c8902e']]);
      spaced(ctx, 'BREAD FOR', 540, 300, 6);
      spaced(ctx, 'THE ENEMY', 540, 398, 6);
      ctx.shadowBlur = 10;
      ctx.font = `500 27px Cinzel`;
      ctx.fillStyle = '#f2e6cc';
      spaced(ctx, tx.sub || '', 540, 462, 2);
      ctx.strokeStyle = rgba('#e8c878', 0.8); ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(300, 430); ctx.lineTo(780, 430); ctx.stroke();
    } else if (tx.style === 'place') {
      ctx.globalAlpha = Math.min(smooth(lt / 0.7), 1 - smooth((lt - (tx.dur - 0.8)) / 0.8));
      ctx.font = `600 38px Cinzel`;
      ctx.shadowColor = 'rgba(0,0,0,0.9)'; ctx.shadowBlur = 14;
      ctx.fillStyle = '#efe4cc';
      spaced(ctx, tx.text, 540, 250, 4);
    } else if (tx.style === 'end') {
      ctx.globalAlpha = Math.min(smooth(lt / 1.2), 1);
      ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 16;
      ctx.font = `italic 500 60px Lora`;
      ctx.fillStyle = '#fff6e4';
      const lines = wrap(ctx, '“' + tx.text + '”', 860);
      lines.forEach((ln, i) => { ctx.textAlign = 'center'; ctx.fillText(ln, 540, 640 + i * 84); });
      ctx.font = `600 38px Cinzel`;
      ctx.fillStyle = '#f0c868';
      ctx.textAlign = 'left';
      spaced(ctx, (tx.sub || '').toUpperCase(), 540, 660 + lines.length * 84 + 30, 4);
      ctx.globalAlpha = Math.min(smooth((lt - 1.5) / 1.2), 1) * 0.8;
      ctx.font = `400 24px ${SANS}`;
      ctx.fillStyle = '#e8dcc8';
      ctx.textAlign = 'center';
      ctx.fillText('Scripture quotations: New International Version (NIV)', 540, 1780);
    }
    ctx.restore();
  }
}

// ------------------------------------------------------------ subtitles
function wrap(ctx, text, maxW) {
  const words = text.split(/\s+/);
  const lines = [];
  let cur = '';
  for (const w of words) {
    const test = cur ? cur + ' ' + w : w;
    if (ctx.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test;
  }
  if (cur) lines.push(cur);
  // balance two lines
  if (lines.length === 2) {
    const all = words;
    let best = null;
    for (let i = 1; i < all.length; i++) {
      const a = all.slice(0, i).join(' '), b = all.slice(i).join(' ');
      const wa = ctx.measureText(a).width, wb = ctx.measureText(b).width;
      if (wa > maxW || wb > maxW) continue;
      const sc = Math.abs(wa - wb);
      if (!best || sc < best.sc) best = { sc, l: [a, b] };
    }
    if (best) return best.l;
  }
  return lines;
}
function subStyle(who) {
  if (who === 'narrator') return { font: (sz) => `italic 500 ${sz}px Lora`, color: '#f6ecd6', size: 50 };
  if (who === 'jesus') return { font: (sz) => `600 ${sz}px ${SANS}`, color: '#ffe7b0', size: 46 };
  return { font: (sz) => `600 ${sz}px ${SANS}`, color: '#ffffff', size: 46 };
}
function drawSubs(ctx, t) {
  const lines = tl.lines;
  for (let i = 0; i < lines.length; i++) {
    const ln = lines[i];
    const next = lines[i + 1];
    const endT = Math.min(ln.end + 0.35, next ? next.start - 0.02 : 1e9);
    if (t < ln.start - 0.04 || t > endT) continue;
    const a = Math.min(clamp((t - (ln.start - 0.04)) / 0.08), clamp((endT - t) / 0.1));
    const st = subStyle(ln.who);
    let size = st.size;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    ctx.font = st.font(size);
    let ls = wrap(ctx, ln.text, 860);
    if (ls.length > 2) { size = Math.round(size * 0.86); ctx.font = st.font(size); ls = wrap(ctx, ln.text, 880); }
    const lh = size * 1.28;
    const y0 = 1430 - (ls.length - 1) * lh * 0.5;
    ls.forEach((s, k) => {
      const y = y0 + k * lh;
      ctx.lineJoin = 'round';
      ctx.strokeStyle = 'rgba(0,0,0,0.88)';
      ctx.lineWidth = size * 0.2;
      ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 10;
      ctx.strokeText(s, 525, y);
      ctx.shadowBlur = 0;
      ctx.fillStyle = st.color;
      ctx.fillText(s, 525, y);
    });
    ctx.restore();
  }
}

// ------------------------------------------------------------ main
async function run() {
  if (args.still !== undefined) {
    const t = parseFloat(args.still);
    renderFrame(t);
    fs.writeFileSync(args.out, main.toBuffer('image/png'));
    return;
  }
  if (args.stills) {
    // comma list of times -> contact sheet
    const ts = args.stills.split(',').map(parseFloat);
    const cols = parseInt(args.cols || '4', 10);
    const sc = parseFloat(args.thumb || '0.5');
    const tw = Math.round(OUT_W * sc), th = Math.round(OUT_H * sc);
    const sheet = createCanvas(tw * cols, th * Math.ceil(ts.length / cols));
    const sx = sheet.getContext('2d');
    ts.forEach((t, i) => {
      renderFrame(t);
      sx.drawImage(main, (i % cols) * tw, Math.floor(i / cols) * th, tw, th);
      sx.fillStyle = '#ff0'; sx.font = '16px sans-serif'; sx.fillText(t.toFixed(1) + ' ' + tl.shots[shotAt(t)].id, (i % cols) * tw + 6, Math.floor(i / cols) * th + 18);
    });
    fs.writeFileSync(args.out, sheet.toBuffer('image/png'));
    return;
  }
  const f0 = parseInt(args.from || '0', 10);
  const f1 = parseInt(args.to || String(Math.ceil(tl.duration * FPS)), 10);
  const out = process.stdout;
  for (let f = f0; f < f1; f++) {
    renderFrame(f / FPS);
    const buf = main.data();
    if (!out.write(Buffer.from(buf))) await new Promise((r) => out.once('drain', r));
    if (args.progress && f % 48 === 0) process.stderr.write(`frame ${f}/${f1}\n`);
  }
}
run().catch((e) => { console.error(e); process.exit(1); });
