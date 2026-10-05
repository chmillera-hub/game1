#!/usr/bin/env node
/*
 * Render FLEECED to MP4 (or a few stills) with headless Chromium + ffmpeg.
 *
 *   node render/render.cjs                      -> FLEECED.mp4 (1920x1080, 30 fps)
 *   node render/render.cjs --stills 3,20.5,61   -> .cache/stills/*.png
 *   node render/render.cjs --workers 3 --fps 30 --from 40 --to 60 --out clip.mp4
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

function loadPlaywright() {
  try { return require('playwright'); } catch (e) { /* fall through to global install */ }
  const root = execSync('npm root -g').toString().trim();
  return require(path.join(root, 'playwright'));
}

const ROOT = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf('--' + name);
  return i >= 0 ? args[i + 1] : def;
};
const FPS = +opt('fps', 30);
const WORKERS = +opt('workers', 3);
const OUT = path.resolve(ROOT, opt('out', 'FLEECED.mp4'));
const STILLS = opt('stills', null);
const CACHE = path.join(ROOT, '.cache');
const PAGE = 'file://' + path.join(ROOT, 'web', 'index.html') + '?render=1';

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => { console.error('page error:', e.message); process.exitCode = 1; });
  await page.goto(PAGE);
  await page.evaluate(() => window.fleecedReady);
  return page;
}

function grab(page, t) {
  return page.evaluate((tt) => {
    window.renderAt(tt);
    return document.getElementById('film').toDataURL('image/png');
  }, t).then((url) => Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
}

function ffmpeg(argv) {
  const p = spawn('ffmpeg', argv, { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => p.on('close', (code) => (code === 0 ? res() : rej(new Error('ffmpeg exited ' + code)))));
  return { p, done };
}

async function main() {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb'] });
  const duration = await (async () => {
    const page = await openPage(browser);
    const d = await page.evaluate(() => window.FLEECED_TIMELINE.duration);
    await page.close();
    return d;
  })();

  if (STILLS) {
    const dir = path.join(CACHE, 'stills');
    fs.mkdirSync(dir, { recursive: true });
    const page = await openPage(browser);
    for (const t of STILLS.split(',').map(Number)) {
      const file = path.join(dir, `t${t.toFixed(2).padStart(7, '0')}.png`);
      fs.writeFileSync(file, await grab(page, t));
      console.log(file);
    }
    await browser.close();
    return;
  }

  const from = +opt('from', 0), to = Math.min(+opt('to', duration), duration);
  const first = Math.round(from * FPS), last = Math.ceil(to * FPS); // [first, last)
  const total = last - first;
  const per = Math.ceil(total / WORKERS);
  fs.mkdirSync(CACHE, { recursive: true });
  const t0 = Date.now();
  let doneFrames = 0;
  const segs = [];
  await Promise.all(Array.from({ length: WORKERS }, async (_, w) => {
    const a = first + w * per, b = Math.min(last, a + per);
    if (a >= b) return;
    const seg = path.join(CACHE, `seg${w}.mp4`);
    segs[w] = seg;
    const page = await openPage(browser);
    const enc = ffmpeg(['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', opt('preset', 'slow'), '-tune', 'animation', '-crf', opt('crf', '23'), '-pix_fmt', 'yuv420p', '-r', String(FPS), seg]);
    for (let f = a; f < b; f++) {
      const png = await grab(page, f / FPS);
      if (!enc.p.stdin.write(png)) await new Promise((r) => enc.p.stdin.once('drain', r));
      doneFrames++;
      if (w === 0 && doneFrames % 150 < WORKERS) {
        const el = (Date.now() - t0) / 1000;
        process.stdout.write(`\r${doneFrames}/${total} frames  ${(doneFrames / el).toFixed(1)} fps  eta ${Math.round((total - doneFrames) / (doneFrames / el))}s   `);
      }
    }
    enc.p.stdin.end();
    await enc.done;
    await page.close();
  }));
  await browser.close();
  console.log(`\nrendered ${total} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`);

  const list = path.join(CACHE, 'segments.txt');
  fs.writeFileSync(list, segs.filter(Boolean).map((s) => `file '${s}'`).join('\n') + '\n');
  const wav = path.join(CACHE, 'soundtrack.wav');
  const mux = ffmpeg(['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list,
    '-ss', String(from), '-t', String(to - from), '-i', wav,
    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT]);
  mux.p.stdin.end();
  await mux.done;
  console.log('wrote', OUT);
}

main().catch((e) => { console.error(e); process.exit(1); });
