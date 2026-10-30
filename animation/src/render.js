// Frame renderer. Usage:
//   node src/render.js stills <t1,t2,...> [--w 540]          -> build/stills/*.png
//   node src/render.js video --from 0 --to 30 [--w 1080] --out build/seg.mp4  (raw frames -> ffmpeg)
//   node src/render.js parallel [--jobs 4] [--w 1080]        -> build/video_nosound.mp4
'use strict';
const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');
const { createCanvas } = require('@napi-rs/canvas');

const ROOT = path.join(__dirname, '..');
const BUILD = path.join(ROOT, 'build');
const FPS = 24;

function args() {
  const a = process.argv.slice(2), o = { _: [] };
  for (let i = 0; i < a.length; i++) {
    if (a[i].startsWith('--')) o[a[i].slice(2)] = a[i + 1], i++;
    else o._.push(a[i]);
  }
  return o;
}
function loadStage() {
  const sched = JSON.parse(fs.readFileSync(path.join(BUILD, 'schedule.json'), 'utf8'));
  const { buildFilm } = require('./shots');
  return buildFilm(sched);
}

async function stills(times, W) {
  const stage = loadStage();
  const H = Math.round(W * 16 / 9);
  const c = createCanvas(W, H), ctx = c.getContext('2d');
  const dir = path.join(BUILD, 'stills');
  fs.mkdirSync(dir, { recursive: true });
  for (const t of times) {
    const t0 = Date.now();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, W, H);
    stage.render(ctx, t, W, H);
    const f = path.join(dir, `t${t.toFixed(2).padStart(7, '0')}.png`);
    fs.writeFileSync(f, c.toBuffer('image/png'));
    console.log(`${f} ${Date.now() - t0}ms`);
  }
}

async function video(from, to, W, out) {
  const stage = loadStage();
  const H = Math.round(W * 16 / 9);
  const c = createCanvas(W, H), ctx = c.getContext('2d');
  const f0 = Math.round(from * FPS), f1 = Math.round(to * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    const T = f / FPS;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
    stage.render(ctx, T, W, H);
    const buf = Buffer.from(ctx.getImageData(0, 0, W, H).data.buffer);
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if ((f - f0) % 96 === 0) console.log(`[${path.basename(out)}] frame ${f - f0}/${f1 - f0} ${((Date.now() - t0) / Math.max(1, f - f0)).toFixed(0)}ms/f`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
}

async function parallel(jobs, W) {
  const sched = JSON.parse(fs.readFileSync(path.join(BUILD, 'schedule.json'), 'utf8'));
  const dur = sched.duration;
  const segDir = path.join(BUILD, 'segments');
  fs.rmSync(segDir, { recursive: true, force: true });
  fs.mkdirSync(segDir, { recursive: true });
  // split on frame boundaries
  const totalF = Math.round(dur * FPS);
  const per = Math.ceil(totalF / jobs);
  const procs = [];
  const list = [];
  for (let j = 0; j < jobs; j++) {
    const a = j * per, b = Math.min(totalF, (j + 1) * per);
    if (a >= b) break;
    const out = path.join(segDir, `seg${j}.mp4`);
    list.push(out);
    procs.push(new Promise((res, rej) => {
      const p = spawn(process.execPath, [__filename, 'video', '--from', String(a / FPS), '--to', String(b / FPS), '--w', String(W), '--out', out], { stdio: 'inherit' });
      p.on('close', (code) => (code === 0 ? res() : rej(new Error('job ' + j + ' failed'))));
    }));
  }
  await Promise.all(procs);
  fs.writeFileSync(path.join(segDir, 'list.txt'), list.map((f) => `file '${f}'`).join('\n'));
  spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(segDir, 'list.txt'), '-c', 'copy', path.join(BUILD, 'video_nosound.mp4')], { stdio: 'inherit' });
  console.log('wrote build/video_nosound.mp4');
}

(async () => {
  const o = args();
  const mode = o._[0];
  if (mode === 'stills') await stills(o._[1].split(',').map(Number), +(o.w || 540));
  else if (mode === 'video') await video(+o.from, +o.to, +(o.w || 1080), o.out || path.join(BUILD, 'seg.mp4'));
  else if (mode === 'parallel') await parallel(+(o.jobs || 4), +(o.w || 1080));
  else if (mode === 'cues') { const st = loadStage(); fs.writeFileSync(path.join(BUILD, 'cues.json'), JSON.stringify(st.cues, null, 1)); console.log('wrote cues.json'); }
  else console.log('usage: stills|video|parallel|cues');
})().catch((e) => { console.error(e); process.exit(1); });
