#!/usr/bin/env node
// Drives index.html in headless Chromium (Playwright).
//
//   node tools/render.mjs cues                 -> build/cues.json (sound cues for tools/audio.py)
//   node tools/render.mjs stills 12.5 40 ...   -> build/stills/*.png (quick visual checks)
//   node tools/render.mjs video [--workers 3] [--from 0] [--to 30] [--crf 20] [--out out/the-plan.mp4]
//
// Frames are rendered one at a time at exact timestamps (t = frame / fps), so
// the picture never drifts from the audio.
import { spawn, execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BUILD = path.join(ROOT, 'build');

async function loadPlaywright() {
  try { return await import('playwright'); } catch {}
  const globalRoot = execSync('npm root -g').toString().trim();
  const require = createRequire(path.join(globalRoot, 'noop.js'));
  return require('playwright');
}

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log('  [page]', m.text()); });
  page.on('pageerror', (e) => console.log('  [page error]', e.message));
  await page.goto(pathToFileURL(path.join(ROOT, 'index.html')).href + '?render');
  await page.evaluate(() => window.ready);
  return page;
}

function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  return i > 0 ? process.argv[i + 1] : dflt;
}

async function main() {
  const mode = process.argv[2] || 'video';
  const { chromium } = await loadPlaywright();
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--font-render-hinting=none'] });
  try {
    if (mode === 'cues') {
      const page = await openPage(browser);
      const cues = await page.evaluate(() => window.collectCues());
      fs.writeFileSync(path.join(BUILD, 'cues.json'), JSON.stringify(cues, null, 1));
      console.log(`cues: ${cues.sfx.length} sound effects, ${cues.music.length} music sections`);
      return;
    }
    if (mode === 'stills') {
      const page = await openPage(browser);
      const dir = path.join(BUILD, 'stills');
      fs.mkdirSync(dir, { recursive: true });
      for (const a of process.argv.slice(3)) {
        const t = parseFloat(a);
        await page.evaluate((t) => window.renderAt(t), t);
        const file = path.join(dir, `t${t.toFixed(2).padStart(7, '0')}.png`);
        await page.screenshot({ path: file, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
        console.log(file);
      }
      return;
    }
    await renderVideo(browser);
  } finally {
    await browser.close();
  }
}

async function renderVideo(browser) {
  const tl = JSON.parse(fs.readFileSync(path.join(BUILD, 'timeline.json')));
  const fps = tl.fps;
  const from = Math.round(parseFloat(arg('from', '0')) * fps);
  const to = Math.min(Math.round(parseFloat(arg('to', String(tl.duration))) * fps), Math.round(tl.duration * fps));
  const workers = parseInt(arg('workers', '3'), 10);
  const out = path.resolve(ROOT, arg('out', 'out/the-plan.mp4'));
  const audio = path.join(BUILD, 'mix.wav');
  const segDir = path.join(BUILD, 'segments');
  fs.rmSync(segDir, { recursive: true, force: true });
  fs.mkdirSync(segDir, { recursive: true });
  fs.mkdirSync(path.dirname(out), { recursive: true });

  const total = to - from;
  const per = Math.ceil(total / workers);
  const started = Date.now();
  let done = 0;
  const progress = setInterval(() => {
    const el = (Date.now() - started) / 1000;
    const eta = done ? (el / done) * (total - done) : 0;
    process.stdout.write(`\r  frames ${done}/${total}  ${(done / el).toFixed(1)} fps  eta ${Math.round(eta)}s   `);
  }, 2000);

  const jobs = [];
  for (let w = 0; w < workers; w++) {
    const a = from + w * per, b = Math.min(to, a + per);
    if (a >= b) continue;
    const seg = path.join(segDir, `seg${w}.mp4`);
    jobs.push((async () => {
      const page = await openPage(browser);
      const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
        // fast, near-lossless intermediate; the final pass below does the real compression
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '10', '-pix_fmt', 'yuv420p', '-r', String(fps), seg],
      { stdio: ['pipe', 'inherit', 'inherit'] });
      const closed = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg exited ' + c)))));
      for (let f = a; f < b; f++) {
        const b64 = await page.evaluate((t) => {
          window.renderAt(t);
          return document.getElementById('stage').toDataURL('image/jpeg', 0.94).split(',')[1];
        }, f / fps);
        if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise((r) => ff.stdin.once('drain', r));
        done++;
      }
      ff.stdin.end();
      await closed;
      await page.close();
      return seg;
    })());
  }
  const segs = await Promise.all(jobs);
  clearInterval(progress);
  process.stdout.write('\n');

  const list = path.join(segDir, 'list.txt');
  fs.writeFileSync(list, segs.map((s) => `file '${s}'`).join('\n'));
  const muxArgs = ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list];
  const withAudio = fs.existsSync(audio);
  if (withAudio) muxArgs.push('-ss', String(from / fps), '-t', String(total / fps), '-i', audio);
  muxArgs.push('-c:v', 'libx264', '-preset', 'slow', '-crf', arg('crf', '20'), '-tune', 'animation', '-pix_fmt', 'yuv420p');
  if (withAudio) muxArgs.push('-c:a', 'aac', '-b:a', '192k', '-map', '0:v:0', '-map', '1:a:0', '-shortest');
  muxArgs.push('-movflags', '+faststart', out);
  execSync('ffmpeg ' + muxArgs.map((x) => JSON.stringify(x)).join(' '), { stdio: 'inherit' });
  console.log(`wrote ${path.relative(ROOT, out)} (${(fs.statSync(out).size / 1e6).toFixed(1)} MB, ${(total / fps).toFixed(1)}s${withAudio ? '' : ', no audio yet'}) in ${Math.round((Date.now() - started) / 1000)}s`);
}

main().catch((e) => { console.error(e); process.exit(1); });
