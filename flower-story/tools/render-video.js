#!/usr/bin/env node
/* ==========================================================================
   render-video.js — render the film to an MP4 (H.264 + AAC) with ffmpeg.

   node tools/render-video.js --out film.mp4 [--fps 30] [--w 1920] [--workers 3] [--crf 20]
   Frames are rendered deterministically with Film.renderAt (no real-time
   playback), split across parallel headless browsers; the score is rendered
   offline through FilmAudio.debug.renderTimeline, then everything is muxed.
   Film grain is left out of the video (the encoder would spend its bits on it).
   ========================================================================== */
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2), opt = {};
for (let i = 0; i < argv.length; i++) if (argv[i].startsWith('--')) { const k = argv[i].slice(2); const v = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true; opt[k] = v; }
const root = path.resolve(__dirname, '..');
const OUT = path.resolve(opt.out || path.join(root, '..', 'the-hikers-and-the-flower.mp4'));
const FPS = +(opt.fps || 30), WIDTH = +(opt.w || 1920), HEIGHT = Math.round((WIDTH * 9) / 16);
const WORKERS = +(opt.workers || 3), CRF = String(opt.crf || 20);
const TMP = path.resolve(opt.tmp || path.join(path.dirname(OUT), '.render-tmp'));
fs.mkdirSync(TMP, { recursive: true });

async function openFilm(browser) {
  const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(root, 'index.html') + '?test&w=' + WIDTH);
  await page.waitForFunction(() => window.Film && window.Film.ready, null, { timeout: 30000 });
  await page.evaluate(() => { Art.grain = () => {}; });
  return page;
}

async function renderSegment(idx, f0, f1) {
  const browser = await chromium.launch();
  const page = await openFilm(browser);
  const file = path.join(TMP, `seg${idx}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', CRF, '-pix_fmt', 'yuv420p', '-tune', 'animation', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const BATCH = 8;
  for (let f = f0; f < f1; f += BATCH) {
    const n = Math.min(BATCH, f1 - f);
    const shots = await page.evaluate(({ f, n, fps }) => {
      const out = [];
      for (let i = 0; i < n; i++) { FILM.renderAt((f + i) / fps); out.push(FILM.canvas().toDataURL('image/jpeg', 0.95).split(',')[1]); }
      return out;
    }, { f, n, fps: FPS });
    for (const s of shots) if (!ff.stdin.write(Buffer.from(s, 'base64'))) await new Promise((r) => ff.stdin.once('drain', r));
    if (idx === 0 && f % (FPS * 10) < BATCH) process.stdout.write(`  worker 0: ${((f - f0) / (f1 - f0) * 100).toFixed(0)}%\r`);
  }
  ff.stdin.end();
  await new Promise((r, j) => ff.on('close', (c) => (c === 0 ? r() : j(new Error('ffmpeg exited ' + c)))));
  const errors = await page.evaluate(() => FILM.errors);
  await browser.close();
  if (errors.length) console.log(`segment ${idx} scene errors:`, errors.map((e) => e.scene + ': ' + e.message));
  return file;
}

async function renderAudio(total) {
  const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const page = await openFilm(browser);
  const SR = 48000;
  const info = await page.evaluate(async ({ dur, fps, sr }) => {
    const r = await FilmAudio.debug.renderTimeline({ from: 0, duration: dur, fps, sampleRate: sr });
    window.__buf = r.buffer;
    return { len: r.buffer.length, ch: r.buffer.numberOfChannels, errors: r.errors.length };
  }, { dur: total + 0.5, fps: FPS, sr: SR });
  const data = Buffer.alloc(info.len * 2 * 2);
  const CH = SR * 10;
  for (let s = 0; s < info.len; s += CH) {
    const b64 = await page.evaluate(({ s, n }) => {
      const b = window.__buf, L = b.getChannelData(0), R = b.getChannelData(b.numberOfChannels > 1 ? 1 : 0);
      const out = new Int16Array(n * 2);
      for (let i = 0; i < n; i++) {
        out[i * 2] = Math.max(-32768, Math.min(32767, Math.round(L[s + i] * 32767)));
        out[i * 2 + 1] = Math.max(-32768, Math.min(32767, Math.round(R[s + i] * 32767)));
      }
      let str = '';
      const u8 = new Uint8Array(out.buffer);
      for (let i = 0; i < u8.length; i += 0x8000) str += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
      return btoa(str);
    }, { s, n: Math.min(CH, info.len - s) });
    Buffer.from(b64, 'base64').copy(data, s * 4);
  }
  await browser.close();
  const hdr = Buffer.alloc(44);
  hdr.write('RIFF', 0); hdr.writeUInt32LE(36 + data.length, 4); hdr.write('WAVE', 8); hdr.write('fmt ', 12);
  hdr.writeUInt32LE(16, 16); hdr.writeUInt16LE(1, 20); hdr.writeUInt16LE(2, 22); hdr.writeUInt32LE(SR, 24);
  hdr.writeUInt32LE(SR * 4, 28); hdr.writeUInt16LE(4, 32); hdr.writeUInt16LE(16, 34); hdr.write('data', 36); hdr.writeUInt32LE(data.length, 40);
  const file = path.join(TMP, 'score.wav');
  fs.writeFileSync(file, Buffer.concat([hdr, data]));
  console.log(`score rendered (${(info.len / SR).toFixed(1)} s${info.errors ? ', ' + info.errors + ' audio errors' : ''})`);
  return file;
}

(async () => {
  const t0 = Date.now();
  const probe = await chromium.launch();
  let total = await (await openFilm(probe)).evaluate(() => FILM.duration);
  if (opt.limit) total = Math.min(total, +opt.limit);
  await probe.close();
  const frames = Math.ceil(total * FPS);
  console.log(`rendering ${total.toFixed(1)} s = ${frames} frames at ${WIDTH}×${HEIGHT}, ${FPS} fps, ${WORKERS} workers`);
  const per = Math.ceil(frames / WORKERS);
  const jobs = [];
  for (let i = 0; i < WORKERS; i++) jobs.push(renderSegment(i, i * per, Math.min(frames, (i + 1) * per)));
  jobs.push(renderAudio(total));
  const done = await Promise.all(jobs);
  const wav = done.pop();
  const list = path.join(TMP, 'list.txt');
  fs.writeFileSync(list, done.map((f) => `file '${f}'`).join('\n'));
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-i', wav,
    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart',
    '-metadata', 'title=The Hikers, the Flower, and the Meaning We Create', OUT]);
  fs.rmSync(TMP, { recursive: true, force: true });
  console.log(`\nwrote ${OUT} (${(fs.statSync(OUT).size / 1048576).toFixed(1)} MB) in ${((Date.now() - t0) / 60000).toFixed(1)} min`);
})().catch((e) => { console.error(e); process.exit(1); });
