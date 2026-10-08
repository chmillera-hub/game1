#!/usr/bin/env node
// Renders the animation frame by frame and pipes raw pixels into ffmpeg.
//   node render/main.js --stills 3,40.5,90         -> PNG previews in build/stills
//   node render/main.js --events                   -> build/sfx.json (sound-effect cues)
//   node render/main.js --from 0 --to 60 --out x.mp4 [--w 720]
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const U = require('./util');

const ROOT = path.join(__dirname, '..');
const FONT_DIR = path.join(ROOT, '.cache', 'fonts');
for (const [f, n] of [['Nunito.ttf', 'Nunito'], ['Fredoka.ttf', 'Fredoka'], ['PatrickHand.ttf', 'Patrick Hand'], ['JetBrainsMono.ttf', 'JetBrains Mono'], ['Caveat.ttf', 'Caveat']]) {
  GlobalFonts.registerFromPath(path.join(FONT_DIR, f), n);
}

const args = {};
process.argv.slice(2).forEach((a, i, all) => { if (a.startsWith('--')) args[a.slice(2)] = all[i + 1] && !all[i + 1].startsWith('--') ? all[i + 1] : true; });

const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'build', 'timeline.json')));
const OW = +(args.w || 720), OH = Math.round(OW * 16 / 9), SCALE = OW / U.W;
const H = require('./helpers')(TL);
H.scale = SCALE;
H.makeCanvas = () => { const c = createCanvas(OW, OH); return { c, ctx: c.getContext('2d') }; };
const scenes = require('./scenes')(H);
const main = H.makeCanvas(), trans = H.makeCanvas();
const fps = TL.fps, DUR = TL.duration;
const XF = 0.35; // half-length of the crossfade between scenes

function drawScene(ctx, sc, t) {
  ctx.setTransform(SCALE, 0, 0, SCALE, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.save(); scenes[sc.id].draw(ctx, t); ctx.restore();
}
function sceneIndex(t) {
  for (let i = 0; i < TL.scenes.length; i++) if (t < TL.scenes[i].end) return i;
  return TL.scenes.length - 1;
}
function renderFrame(t) {
  const ctx = main.ctx, i = sceneIndex(t), sc = TL.scenes[i];
  drawScene(ctx, sc, t);
  let other = null, a = 0;
  if (i + 1 < TL.scenes.length && t > sc.end - XF) { other = TL.scenes[i + 1]; a = 0.5 * U.smooth(U.prog(t, sc.end - XF, sc.end)); }
  else if (i > 0 && t < sc.start + XF) { other = TL.scenes[i - 1]; a = 0.5 * (1 - U.smooth(U.prog(t, sc.start, sc.start + XF))); }
  if (other && a > 0.002) {
    drawScene(trans.ctx, other, t);
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = a; ctx.drawImage(trans.c, 0, 0); ctx.globalAlpha = 1;
  }
  ctx.setTransform(SCALE, 0, 0, SCALE, 0, 0);
  H.captions(ctx, t);
  // fade in from black / fade out at the very end
  const fade = Math.max(1 - U.prog(t, 0, 0.8), U.prog(t, DUR - 1.2, DUR - 0.1));
  if (fade > 0) { ctx.fillStyle = `rgba(0,0,0,${fade})`; ctx.fillRect(0, 0, U.W, U.H); }
}

async function main_() {
  if (args.events) {
    const ev = [];
    for (const sc of TL.scenes) if (scenes[sc.id].sfx) ev.push(...scenes[sc.id].sfx());
    ev.sort((a, b) => a.t - b.t);
    fs.writeFileSync(path.join(ROOT, 'build', 'sfx.json'), JSON.stringify(ev.filter((e) => e.vol > 0)));
    console.log(`wrote ${ev.length} sound cues`);
    return;
  }
  if (args.stills) {
    const dir = path.join(ROOT, 'build', 'stills');
    fs.mkdirSync(dir, { recursive: true });
    // times can be seconds, or relative to a line/scene: "a_s2a+1.5", "step3+4", "r_her.end-0.5"
    const resolve = (spec) => {
      const m = /^([a-z_0-9]+?)(\.end)?([+-][\d.]+)?$/i.exec(spec);
      if (!m || !isNaN(+spec)) return +spec;
      const base = TL.lines[m[1]] || TL.scenes.find((x) => x.id === m[1]);
      return (m[2] ? base.end : base.start) + (+(m[3] || 0));
    };
    for (const s of String(args.stills).split(',')) {
      const t = resolve(s); renderFrame(t);
      const f = path.join(dir, `t${t.toFixed(2).padStart(7, '0')}.png`);
      fs.writeFileSync(f, main.c.toBuffer('image/png')); console.log(f);
    }
    return;
  }
  const from = +(args.from || 0), to = Math.min(DUR, +(args.to || DUR));
  const f0 = Math.round(from * fps), f1 = Math.round(to * fps);
  const out = args.out || path.join(ROOT, 'build', 'video.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${OW}x${OH}`, '-r', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    renderFrame(f / fps);
    if (!ff.stdin.write(main.c.data())) await new Promise((r) => ff.stdin.once('drain', r));
    if ((f - f0) % 240 === 0) process.stderr.write(`  [${path.basename(out)}] ${((f - f0) / (f1 - f0) * 100).toFixed(0)}%  ${((f - f0) / ((Date.now() - t0) / 1000 + 1e-3)).toFixed(1)} fps\n`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  console.log(`rendered ${f1 - f0} frames -> ${out} in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}
main_().catch((e) => { console.error(e); process.exit(1); });
