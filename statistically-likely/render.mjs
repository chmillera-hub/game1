// Renders index.html frame-by-frame into an MP4.
//   node render.mjs                 -> full film (video only) + events.json
//   node render.mjs --stills 12,40  -> PNG stills at those seconds (for checking)
// Every frame is a pure function of time, so the film is split across workers.
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import os from 'node:os';

// CommonJS require so a globally installed playwright (NODE_PATH) is found too
const { chromium } = createRequire(import.meta.url)('playwright');

const here = path.dirname(fileURLToPath(import.meta.url));
const out = process.env.OUT_DIR || path.join(here, 'build');
mkdirSync(out, { recursive: true });
const url = pathToFileURL(path.join(here, 'index.html')).href + '?render=1';
const args = process.argv.slice(2);

async function openFilm(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => { console.error('page error:', e.message); process.exitCode = 1; });
  await page.goto(url);
  await page.evaluate(() => window.FILM.ready);
  return page;
}

const browser = await chromium.launch();

if (args[0] === '--stills') {
  const page = await openFilm(browser);
  for (const s of args[1].split(',').map(Number)) {
    const b64 = await page.evaluate(t => window.FILM.frameDataURL(Math.round(t * 30)), s);
    const file = path.join(out, `still-${String(s).replace('.', '_')}.png`);
    writeFileSync(file, Buffer.from(b64.split(',')[1], 'base64'));
    console.log(file);
  }
  await browser.close();
  process.exit();
}

const probe = await openFilm(browser);
const { frames, events, T, cues } = await probe.evaluate(() => ({ frames: window.FILM.frames, events: window.FILM.events, T: window.FILM.T, cues: window.FILM.cues }));
writeFileSync(path.join(out, 'events.json'), JSON.stringify({ T, events, cues }));
await probe.close();

// RANGE=start:end (frames) renders just a slice, for checking size and quality
const [first, last] = process.env.RANGE ? process.env.RANGE.split(':').map(Number) : [0, frames];
const workers = Number(process.env.WORKERS || Math.min(4, os.cpus().length));
const per = Math.ceil((last - first) / workers);
const started = Date.now();
let done = 0;

await Promise.all(Array.from({ length: workers }, async (_, w) => {
  const from = first + w * per, to = Math.min(last, from + per);
  const page = await openFilm(browser);
  const seg = path.join(out, `seg${w}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', process.env.CRF || '24', '-tune', 'film', '-pix_fmt', 'yuv420p', '-threads', '2', seg],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const closed = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error(`ffmpeg ${w} exited ${c}`))));
  for (let f = from; f < to; f++) {
    const b64 = await page.evaluate(i => window.FILM.frameDataURL(i), f);
    if (!ff.stdin.write(Buffer.from(b64.slice(b64.indexOf(',') + 1), 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (++done % 300 === 0) console.log(`${done}/${last - first} frames  ${((Date.now() - started) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await closed;
  await page.close();
}));

writeFileSync(path.join(out, 'segments.txt'), Array.from({ length: workers }, (_, w) => `file 'seg${w}.mp4'`).join('\n') + '\n');
await browser.close();
console.log(`rendered ${last - first} frames in ${((Date.now() - started) / 1000).toFixed(0)}s`);
