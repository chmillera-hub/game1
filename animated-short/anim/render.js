// Renders the film.
//   node render.js <timeline.json> png <outdir> <t1,t2,...>
//   node render.js <timeline.json> video <out.mkv> <fromFrame> <toFrame>
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const { Stage } = require('./stage');
const { drawCharacter } = require('./rig');
const { drawRoom, drawCouchFront, drawTable, buildLightmap, drawGlows, roundRect } = require('./set');
const { clamp } = require('./core');
const direct = require(process.env.DIRECTION || './direction');

const OUT_W = +(process.env.OUT_W || 720), OUT_H = Math.round(OUT_W * 16 / 9);
const S = OUT_W / 1080;
const FPS = 24;

for (const f of ['Inter-Bold', 'Inter-SemiBold', 'Inter-SemiBoldItalic', 'Inter-ExtraBold', 'Inter-Medium', 'Inter-MediumItalic']) {
  GlobalFonts.registerFromPath(`/usr/share/fonts/opentype/inter/${f}.otf`, f);
}

const tl = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const stage = new Stage(tl);
direct(stage);
stage.finalize();

const canvas = createCanvas(OUT_W, OUT_H);
const ctx = canvas.getContext('2d');
const lcanvas = createCanvas(OUT_W, OUT_H);
const lctx = lcanvas.getContext('2d');

function wrap(text, font, maxW) {
  ctx.font = font;
  const words = text.split(' ');
  const lines = [];
  let cur = '';
  for (const w of words) {
    const test = cur ? cur + ' ' + w : w;
    if (ctx.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test;
  }
  if (cur) lines.push(cur);
  return lines;
}

function drawCaption(t) {
  const lines = tl.lines;
  let ln = null;
  for (let i = 0; i < lines.length; i++) {
    const next = lines[i + 1];
    const until = Math.min(lines[i].end + 0.45, next ? next.start - 0.04 : 1e9);
    if (t >= lines[i].start - 0.05 && t < until) { ln = lines[i]; break; }
  }
  if (!ln) return;
  const narr = ln.speaker === 'narrator';
  const size = 44;
  const font = narr ? `${size}px Inter-MediumItalic` : `${size}px Inter-SemiBold`;
  const rows = wrap(ln.caption, font, 860);
  const lh = size * 1.28;
  const cy = 1405;
  const h = rows.length * lh;
  let wmax = 0;
  for (const r of rows) wmax = Math.max(wmax, ctx.measureText(r).width);
  const fadeIn = clamp((t - ln.start + 0.05) / 0.12, 0, 1);
  ctx.globalAlpha = fadeIn;
  ctx.fillStyle = 'rgba(14,12,22,0.62)';
  roundRect(ctx, 540 - wmax / 2 - 26, cy - h / 2 - 16, wmax + 52, h + 30, 22); ctx.fill();
  ctx.fillStyle = narr ? '#f4e2bd' : '#ffffff';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  rows.forEach((r, i) => ctx.fillText(r, 540, cy - h / 2 + lh * (i + 0.5) + 1));
  ctx.globalAlpha = 1;
}

function drawTitle(t) {
  let a = 0;
  if (t < 3.5) a = 1 - clamp((t - 2.9) / 0.6, 0, 1);
  const endT = tl.marks.end;
  if (t > endT + 0.4) a = clamp((t - endT - 0.4) / 0.8, 0, 1);
  if (a <= 0) return;
  ctx.globalAlpha = a;
  // soft dark band so the title reads over bright backgrounds too
  const band = ctx.createLinearGradient(0, 200, 0, 520);
  band.addColorStop(0, 'rgba(12,10,24,0)'); band.addColorStop(0.3, 'rgba(12,10,24,0.42)');
  band.addColorStop(0.7, 'rgba(12,10,24,0.42)'); band.addColorStop(1, 'rgba(12,10,24,0)');
  ctx.fillStyle = band; ctx.fillRect(0, 200, 1080, 320);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.font = '104px Inter-ExtraBold';
  ctx.fillStyle = 'rgba(10,8,20,0.55)';
  ctx.fillText('Yeah. I know.', 544, 334);
  ctx.fillStyle = '#fff6e6';
  ctx.fillText('Yeah. I know.', 540, 328);
  ctx.font = '36px Inter-MediumItalic';
  ctx.fillStyle = 'rgba(10,8,20,0.55)';
  ctx.fillText('a short film about the jokes we hide behind', 542, 418);
  ctx.fillStyle = '#f2dfbf';
  ctx.fillText('a short film about the jokes we hide behind', 540, 416);
  ctx.globalAlpha = 1;
}

function drawTimeCard(t) {
  const s3 = tl.marks.s3;
  if (t < s3 || t > s3 + 2.6) return;
  const a = Math.min(clamp((t - s3) / 0.3, 0, 1), clamp((s3 + 2.6 - t) / 0.5, 0, 1));
  ctx.globalAlpha = a;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.font = '50px Inter-SemiBoldItalic';
  ctx.fillStyle = 'rgba(40,28,20,0.35)';
  ctx.fillText('The next morning', 543, 303);
  ctx.fillStyle = '#4a3324';
  ctx.fillText('The next morning', 540, 300);
  ctx.globalAlpha = 1;
}

function renderFrame(t) {
  const cam = stage.camera(t);
  const tf = [S * cam.z, 0, 0, S * cam.z, S * (540 - cam.cx * cam.z), S * (960 - cam.cy * cam.z)];
  ctx.setTransform(...tf);
  ctx.globalCompositeOperation = 'source-over';
  const L = stage.lightAt(t);
  drawRoom(ctx, L, t);
  drawCouchFront(ctx);
  const light = {
    side: L.morning > 0.5 ? -1 : 1,
    glare: `rgba(${Math.round(200 - 40 * L.tv)},${Math.round(220 - 10 * L.tv)},255,${(0.1 + 0.22 * L.tv * (1 - L.morning)).toFixed(3)})`,
  };
  for (const name of stage.orderS.at(t)) {
    const p = stage.puppets[name];
    const P = p.evaluate(t, stage);
    if (P.visible) drawCharacter(ctx, name, P, t, light);
  }
  drawTable(ctx, L, t, stage.itemsS.at(t));
  // light pass
  lctx.setTransform(...tf);
  buildLightmap(lctx, L, t);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalCompositeOperation = 'multiply';
  ctx.drawImage(lcanvas, 0, 0);
  ctx.globalCompositeOperation = 'source-over';
  ctx.setTransform(...tf);
  drawGlows(ctx, L);
  // overlays (screen space)
  ctx.setTransform(S, 0, 0, S, 0, 0);
  drawCaption(t);
  drawTitle(t);
  drawTimeCard(t);
}

async function main() {
  const mode = process.argv[3];
  if (mode === 'png') {
    const outdir = process.argv[4];
    fs.mkdirSync(outdir, { recursive: true });
    for (const ts of process.argv[5].split(',')) {
      const t = +ts;
      renderFrame(t);
      fs.writeFileSync(path.join(outdir, `f_${t.toFixed(2)}.png`), canvas.toBuffer('image/png'));
    }
    return;
  }
  const out = process.argv[4];
  const f0 = +process.argv[5], f1 = +process.argv[6];
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${OUT_W}x${OUT_H}`, '-r', `${FPS}`, '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-pix_fmt', 'yuv444p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    renderFrame(f / FPS);
    const buf = Buffer.from(canvas.data());
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if ((f - f0) % 240 === 0) process.stderr.write(`[${f0}-${f1}] frame ${f} ${((Date.now() - t0) / 1000).toFixed(0)}s\n`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
}

main();
