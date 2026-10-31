#!/usr/bin/env node
/* Packet Loss · render-video.cjs
   Renders the animation frame by frame in headless Chromium and pipes the frames
   into ffmpeg, so the video is frame-exact no matter how fast the machine is.

   Requirements: Node 18+, Playwright with Chromium (npm i -D playwright &&
   npx playwright install chromium), and ffmpeg on PATH.

   Usage:
     node render-video.cjs                       # 1920×1080 landscape → packet-loss-1920x1080.mp4
     node render-video.cjs --vertical            # 1080×1920 for Reels / Shorts / TikTok
     node render-video.cjs --fps 30 --out my.mp4 --from 60 --to 120
     node render-video.cjs --light               # light theme instead of dark
*/
'use strict';
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const args = process.argv.slice(2);
const flag = (name) => args.includes('--' + name);
const opt = (name, def) => { const i = args.indexOf('--' + name); return i >= 0 && args[i + 1] != null ? args[i + 1] : def; };

const vertical = flag('vertical');
const orient = vertical ? 'port' : 'land';
const size = vertical ? { width: 1080, height: 1920 } : { width: 1920, height: 1080 };
const fps = Number(opt('fps', 30));
const quality = Number(opt('quality', 0.95));
const crf = String(opt('crf', 18));
const out = path.resolve(opt('out', `packet-loss-${size.width}x${size.height}.mp4`));

(async () => {
  const launch = {};
  if (process.env.HTTPS_PROXY) launch.proxy = { server: process.env.HTTPS_PROXY };
  const browser = await chromium.launch(launch);
  const page = await browser.newPage({ viewport: size, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => { console.error('Page error:', e.message); process.exit(1); });
  const url = 'file://' + path.resolve(__dirname, 'index.html') + '#render-' + orient;
  await page.goto(url);
  await page.waitForFunction(() => window.__PL && window.__PL.ready === true, null, { timeout: 60000 });
  if (flag('light')) await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'light'));

  const total = await page.evaluate(() => window.__PL.total);
  const from = Math.max(0, Number(opt('from', 0)));
  const to = Math.min(total, Number(opt('to', total)));
  const frames = Math.max(1, Math.round((to - from) * fps));
  console.log(`Rendering ${frames} frames (${(to - from).toFixed(1)} s at ${fps} fps, ${size.width}×${size.height}) → ${out}`);

  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-tune', 'animation', '-crf', crf,
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const closed = new Promise((resolve, reject) => ff.on('close', (code) => (code === 0 ? resolve() : reject(new Error('ffmpeg exited with ' + code)))));

  const started = Date.now();
  for (let f = 0; f < frames; f++) {
    const t = from + f / fps;
    const dataUrl = await page.evaluate(([tt, q]) => window.__PL.frame(tt, q), [t, quality]);
    const buf = Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (f % (fps * 10) === 0) {
      const el = (Date.now() - started) / 1000, rate = (f + 1) / Math.max(0.001, el);
      console.log(`  ${String(Math.round((f / frames) * 100)).padStart(3)}%  frame ${f}/${frames}  ${rate.toFixed(1)} fps  eta ${Math.round((frames - f) / rate)} s`);
    }
  }
  ff.stdin.end();
  await closed;
  await browser.close();
  console.log(`Done in ${Math.round((Date.now() - started) / 1000)} s → ${out}`);
})().catch((e) => { console.error(e); process.exit(1); });
