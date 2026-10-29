// Render the film frame by frame in headless Chromium and encode with ffmpeg.
// Usage: node tools/render.mjs --out build/video.mp4 [--start 0] [--end <sec>] [--workers 4] [--fps 24]
import path from 'node:path';
import fs from 'node:fs';
import { spawn, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { serve } from './snap.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const tl = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/timeline.json'), 'utf8'));
const fps = +(args.fps || tl.fps);
const start = +(args.start || 0), end = Math.min(+(args.end || tl.duration), tl.duration);
const workers = +(args.workers || 4);
const out = path.resolve(args.out || path.join(ROOT, 'build/video.mp4'));
const crf = args.crf || '19';
const f0 = Math.round(start * fps), f1 = Math.round(end * fps);
const segDir = fs.mkdtempSync(path.join(path.dirname(out), 'segs-'));

const srv = await serve();
const url = `http://127.0.0.1:${srv.address().port}/index.html`;
const t0 = Date.now();
let done = 0;

async function worker(w, a, b) {
  const browser = await chromium.launch();
  const page = await (await browser.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();
  page.on('pageerror', (e) => console.log(`[w${w} pageerror]`, e.message));
  await page.goto(url);
  await page.waitForFunction(() => window.__ready === true);
  const cdp = await page.context().newCDPSession(page);
  const seg = path.join(segDir, `seg${String(w).padStart(2, '0')}.mp4`);
  const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', crf, '-pix_fmt', 'yuv420p', '-tune', 'animation', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = a; i < b; i++) {
    await page.evaluate(async (t) => { await E.renderAt(t); }, i / fps);
    const { data } = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 93, optimizeForSpeed: true });
    if (!ff.stdin.write(Buffer.from(data, 'base64'))) await new Promise((r) => ff.stdin.once('drain', r));
    done++;
    if (w === 0 && done % 96 === 0) {
      const el = (Date.now() - t0) / 1000, rate = done / el;
      console.log(`${done}/${f1 - f0} frames  ${rate.toFixed(1)} fps  eta ${((f1 - f0 - done) / rate / 60).toFixed(1)} min`);
    }
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await browser.close();
  return seg;
}

const per = Math.ceil((f1 - f0) / workers);
const jobs = [];
for (let w = 0; w < workers; w++) {
  const a = f0 + w * per, b = Math.min(f1, a + per);
  if (a < b) jobs.push(worker(w, a, b));
}
const segs = await Promise.all(jobs);
srv.close();
const list = path.join(segDir, 'list.txt');
fs.writeFileSync(list, segs.map((s) => `file '${s}'`).join('\n'));
execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out]);
fs.rmSync(segDir, { recursive: true });
console.log(`wrote ${out}  (${f1 - f0} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s)`);
