// Frame renderer.
//   node render/render.mjs --from 0 --to 240 --out build/parts/p0.mkv      render a frame range to a video part
//   node render/render.mjs --stills s01a@0.5,s01a@2.0 --dir tests/x        render PNG stills at shot-local times
// Each scene file render/shots/sNN.mjs exports default { <shotId>: (g, t, ctx) => void }.
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { createCanvas } from '@napi-rs/canvas';
import { W, H, FPS } from './lib/core.mjs';
import { TL, shotById, ROOT_DIR } from './lib/timeline.mjs';
import { drawFrameAt } from './lib/frame.mjs';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) =>
  v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]?.startsWith('--') || arr[i + 1] === undefined ? true : arr[i + 1]]] : a, []));

const cv = createCanvas(W, H); const g = cv.getContext('2d');

function drawFrame(i) {
  const T = (i + 0.5) / FPS; // sample at frame center
  const shot = TL.shots.find(s => T >= s.start && T < s.end) ?? TL.shots[TL.shots.length - 1];
  drawFrameAt(g, shot, T - shot.start);
}

if (args.stills) {
  const dir = path.resolve(ROOT_DIR, args.dir || 'tests/stills'); fs.mkdirSync(dir, { recursive: true });
  for (const spec of String(args.stills).split(',')) {
    const [id, ts] = spec.split('@'); const shot = shotById(id); const t = Number(ts);
    drawFrameAt(g, shot, t);
    const out = path.join(dir, `${id}_${t.toFixed(2)}.png`);
    fs.writeFileSync(out, await cv.encode('png')); console.log(out);
  }
} else {
  const from = Number(args.from ?? 0), to = Math.min(Number(args.to ?? TL.frames), TL.frames);
  const out = path.resolve(ROOT_DIR, args.out || 'build/parts/p.mkv'); fs.mkdirSync(path.dirname(out), { recursive: true });
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`,
    '-r', String(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '6', '-pix_fmt', 'yuv420p', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = from; i < to; i++) {
    drawFrame(i);
    const buf = Buffer.from(g.getImageData(0, 0, W, H).data.buffer);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((i - from) % 240 === 0) console.error(`[${path.basename(out)}] frame ${i}/${to} ${((Date.now() - t0) / (i - from + 1)).toFixed(0)}ms/f`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
