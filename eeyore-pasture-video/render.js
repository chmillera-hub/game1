// Render frames with headless Chromium.
//   node render.js still <t1,t2,...> <outdir>           -> PNG stills
//   node render.js sheet <outfile>                       -> character sheet
//   node render.js video <outdir> [workers]              -> MP4 segments + concat
const path = require('path'), fs = require('fs'), { spawn, execFileSync } = require('child_process');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const ROOT = __dirname, WEB = 'file://' + path.join(ROOT, 'web', 'index.html');
const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'build', 'timeline.json')));

async function page(browser, scale = 1) {
  const p = await browser.newPage({ viewport: { width: 1920 * scale, height: 1080 * scale } });
  p.on('pageerror', e => console.error('PAGEERROR', e.message)); p.on('console', m => m.type() === 'error' && console.error('CONSOLE', m.text()));
  await p.addInitScript(`window.TIMELINE = ${JSON.stringify(TL)}; window.SCALE = ${scale};`);
  await p.goto(WEB);
  await p.evaluate(() => Promise.all([document.fonts.load('44px "Patrick Hand"'), document.fonts.load('italic 44px "Patrick Hand"'), document.fonts.load('600 40px Fredoka')]));
  await p.evaluate(() => window.renderAt(0));
  return p;
}

async function main() {
  const [mode, a, b, c] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(() => chromium.launch());
  if (mode === 'still') {
    const p = await page(browser, .5);
    fs.mkdirSync(b, { recursive: true });
    for (const t of a.split(',').map(Number)) {
      await p.evaluate((t) => window.renderAt(t), t);
      await p.screenshot({ path: path.join(b, `t${t.toFixed(2).padStart(7, '0')}.png`) });
    }
  } else if (mode === 'sheet') {
    const p = await page(browser, .5);
    await p.evaluate((n) => n ? window.renderSheet2() : window.renderSheet(), b === '2');
    await p.screenshot({ path: a });
  } else if (mode === 'video') {
    const out = a, workers = +(b || 4), fps = TL.fps;
    const total = Math.ceil(TL.duration * fps);
    fs.mkdirSync(out, { recursive: true });
    const per = Math.ceil(total / workers);
    const jobs = [];
    for (let w = 0; w < workers; w++) jobs.push((async () => {
      const f0 = w * per, f1 = Math.min(total, f0 + per);
      const p = await page(browser, 1);
      const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(out, `seg${w}.mp4`)]);
      for (let f = f0; f < f1; f++) {
        await p.evaluate((t) => window.renderAt(t), f / fps);
        const buf = await p.screenshot({ type: 'jpeg', quality: 94 });
        if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
        if (w === 0 && (f - f0) % 150 === 0) console.log(`worker0 ${f - f0}/${f1 - f0}`);
      }
      ff.stdin.end();
      await new Promise(r => ff.on('close', r));
    })());
    await Promise.all(jobs);
    fs.writeFileSync(path.join(out, 'list.txt'), Array.from({ length: workers }, (_, w) => `file 'seg${w}.mp4'`).join('\n'));
  }
  await browser.close();
}
main().catch(e => { console.error(e); process.exit(1); });
