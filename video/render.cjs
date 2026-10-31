// Frame-exact renderer for the storybook.
// usage: node render.cjs <storybook.html> <outdir> <scene indexes, e.g. 0,3,7> [--probe N] [--plan]
// Each scene is rendered as its own MP4 segment (scene start -> end of the page turn into the next one),
// so segments can be rendered in parallel and concatenated losslessly.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');

const FPS = 30, DT = 1000 / FPS;
const COVER_HOLD = 13, END_SECONDS = 18, FADE_IN = 1.2, FADE_OUT = 2.6;
const SHIM = fs.readFileSync(path.join(__dirname, 'shim.js'), 'utf8');
const CSS = fs.readFileSync(path.join(__dirname, 'video.css'), 'utf8');

async function openPage(browser, file) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5, colorScheme: 'dark' });
  await ctx.addInitScript({ content: SHIM });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.error('pageerror:', e.message));
  await page.goto('file://' + path.resolve(file));
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({ content: CSS });
  await page.evaluate(hold => {
    document.documentElement.classList.add('video');
    document.documentElement.dataset.theme = 'dark';
    const f = document.createElement('div'); f.id = 'fader'; document.body.appendChild(f);
    SCENES[0].hold = hold;
  }, COVER_HOLD);
  const cdp = await ctx.newCDPSession(page);
  return { ctx, page, cdp };
}

async function renderSegment(browser, file, i, outdir, probe, dump) {
  const { ctx, page, cdp } = await openPage(browser, file);
  const n = await page.evaluate(i => {
    if (i === 0) { state.started = true; state.sched = schedule(SCENES[0]); }
    else { window.__jump(i - 1, 0); go(i, 1); }
    return SCENES.length;
  }, i);
  if (i > 0) {
    let guard = 0;
    while (await page.evaluate(dt => { __advance(dt); return state.turning; }, DT)) if (++guard > 120) throw new Error('turn never ended');
  }
  const isLast = i === n - 1, endFrames = Math.round(END_SECONDS * FPS);
  const out = path.join(outdir, `seg${String(i).padStart(2, '0')}.mp4`);
  const ff = probe ? null : spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-tune', 'animation', '-pix_fmt', 'yuv420p', '-r', String(FPS), out]);
  const finished = ff ? new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg exit ' + c))))) : null;
  const events = [];
  let f = 0, prev = { beat: 0, turning: false };
  const t0 = Date.now();
  for (;;) {
    const fade = i === 0 && f < FADE_IN * FPS ? 1 - f / (FADE_IN * FPS) : isLast && f > endFrames - FADE_OUT * FPS ? (f - (endFrames - FADE_OUT * FPS)) / (FADE_OUT * FPS) : 0;
    const s = await page.evaluate(([dt, first, fade]) => {
      if (!first) __advance(dt);
      document.getElementById('fader').style.opacity = String(Math.max(0, Math.min(1, fade)));
      return { i: state.i, beat: state.beat, turning: state.turning };
    }, [DT, f === 0, fade]);
    if (!isLast && s.i === i + 1 && !s.turning) break;
    if (isLast && f >= endFrames) break;
    if (probe && f >= probe) break;
    if (s.beat !== prev.beat && s.beat > 0 && s.i === i) events.push({ f, type: 'beat', k: s.beat });
    if (s.turning && !prev.turning) events.push({ f, type: 'turn' });
    prev = s;
    const shot = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 92, optimizeForSpeed: true, clip: { x: 0, y: 0, width: 1280, height: 720, scale: 1.5 } });
    const buf = Buffer.from(shot.data, 'base64');
    if (dump && f % dump.every === 0 && f < dump.max) fs.writeFileSync(path.join(dump.dir, `s${i}-f${String(f).padStart(5, '0')}.jpg`), buf);
    if (ff && !ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    f++;
  }
  if (ff) { ff.stdin.end(); await finished; }
  const ms = (Date.now() - t0) / Math.max(1, f);
  fs.writeFileSync(path.join(outdir, `seg${String(i).padStart(2, '0')}.json`), JSON.stringify({ scene: i, frames: f, fps: FPS, events }));
  console.log(`scene ${i}: ${f} frames (${(f / FPS).toFixed(1)} s), ${ms.toFixed(0)} ms/frame`);
  await ctx.close();
}

(async () => {
  const [file, outdir, list = '', ...rest] = process.argv.slice(2);
  const probe = rest.includes('--probe') ? +rest[rest.indexOf('--probe') + 1] : 0;
  const dump = rest.includes('--dump') ? { dir: rest[rest.indexOf('--dump') + 1], every: +rest[rest.indexOf('--dump') + 2], max: +rest[rest.indexOf('--dump') + 3] } : null;
  if (dump) fs.mkdirSync(dump.dir, { recursive: true });
  fs.mkdirSync(outdir, { recursive: true });
  const browser = await chromium.launch();
  if (rest.includes('--plan')) {
    const { page } = await openPage(browser, file);
    const plan = await page.evaluate(() => SCENES.map((s, k) => ({ k, id: s.id, secs: +(schedule(s).end + (k ? 0.96 : 0)).toFixed(1) })));
    console.log(plan.map(p => `${p.k}:${p.id}=${p.secs}s`).join('  '));
    console.log('total ~', plan.reduce((a, p) => a + p.secs, 0).toFixed(0), 's');
  } else {
    for (const i of list.split(',').filter(Boolean).map(Number)) await renderSegment(browser, file, i, outdir, probe, dump);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
