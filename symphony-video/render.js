// usage: node render.js <buildDir> <outDir> [--stills t1,t2,...] [--workers N]
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const [buildDir, outDir] = process.argv.slice(2);
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const stills = arg('--stills', null);
const workers = +arg('--workers', 4);
const tl = JSON.parse(fs.readFileSync(path.join(buildDir, 'timeline.json'), 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

async function page(browser) {
  const p = await browser.newPage({ viewport: { width: 720, height: 1280 } });
  await p.goto('file://' + path.resolve(__dirname, 'anim.html'));
  await p.evaluate(tl => window.setup(tl), tl);
  return p;
}
async function grab(p, t, file) {
  await p.evaluate(t => window.renderAt(t), t);
  const data = await p.evaluate(() => document.getElementById('c').toDataURL('image/jpeg', 0.93));
  fs.writeFileSync(file, Buffer.from(data.split(',')[1], 'base64'));
}
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--disable-web-security', '--allow-file-access-from-files'] });
  if (stills) {
    const p = await page(browser);
    for (const s of stills.split(',')) await grab(p, +s, path.join(outDir, `still_${(+s).toFixed(2)}.jpg`));
  } else {
    const n = Math.ceil(tl.duration * tl.fps);
    const pages = await Promise.all(Array.from({ length: workers }, () => page(browser)));
    let next = 0, done = 0; const t0 = Date.now();
    await Promise.all(pages.map(async p => {
      while (true) {
        const i = next++; if (i >= n) break;
        await grab(p, i / tl.fps, path.join(outDir, `f${String(i).padStart(6, '0')}.jpg`));
        if (++done % 240 === 0) console.log(`${done}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
      }
    }));
  }
  await browser.close();
})();
