// Headless render driver (Playwright + SwiftShader WebGL).
//   node tools/render.js stills  --t 1.5,12,40 [--lab name] [--out out/stills] [--prefix name]
//   node tools/render.js sheet   --from 10 --to 40 --n 12 [--lab name] [--out out/sheets/x.jpg] [--cols 4] [--scale 0.33]
//   node tools/render.js frames  --from F0 --to F1 [--out out/frames]     (frame indices, inclusive; JPEG q 0.94)
//   node tools/render.js bench   --t 12 [--lab name]
// Times are play-time seconds (data/timeline.json). Frames: f / 24.
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const ROOT = path.resolve(__dirname, '..');
const FPS = 24;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.ttf': 'font/ttf', '.woff2': 'font/woff2' };

function arg(name, def) { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : def; }
function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((q, r) => {
      const url = decodeURIComponent(q.url.split('?')[0]);
      const file = path.join(ROOT, url.startsWith('/node_modules/') || url.startsWith('/data/') || url.startsWith('/assets/') ? url : path.join('web', url));
      fs.readFile(file, (err, buf) => {
        if (err) { r.writeHead(404); r.end(); return; }
        r.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
        r.end(buf);
      });
    }).listen(0, '127.0.0.1', () => resolve(srv));
  });
}
async function open(browser, port, lab) {
  const page = await browser.newPage({ viewport: { width: 720, height: 1280 } });
  page.on('console', (m) => { const t = m.text(); if (!/GPU stall|Automatic fallback|WebGL-|GroupMarkerNotSet/.test(t)) console.log('  page:', t); });
  page.on('pageerror', (e) => console.log('  PAGE ERROR:', e.message));
  const q = [lab ? 'lab=' + lab : '', process.env.QUERY || ''].filter(Boolean).join('&');
  await page.goto(`http://127.0.0.1:${port}/index.html${q ? '?' + q : ''}`);
  await page.waitForFunction('window.ready === true', null, { timeout: 180000 });
  const err = await page.evaluate(() => window.initError || null);
  if (err) throw new Error('init failed: ' + err);
  return page;
}
const save = (data, f) => { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, Buffer.from(data.split(',')[1], 'base64')); };

async function main() {
  const mode = process.argv[2];
  const lab = arg('lab', null);
  const srv = await serve();
  const port = srv.address().port;
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-watchdog', '--js-flags=--max-old-space-size=6144'] });
  try {
    const page = await open(browser, port, lab);
    const dur = await page.evaluate(() => window.duration);
    if (mode === 'stills') {
      const ts = arg('t', '0').split(',').map(Number);
      const outDir = path.join(ROOT, arg('out', 'out/stills'));
      for (const t of ts) {
        const t0 = Date.now();
        const data = await page.evaluate((tt) => window.renderAt(tt, 0.93), t);
        const f = path.join(outDir, `${arg('prefix', lab || 'film')}_${t.toFixed(2)}.jpg`);
        save(data, f);
        const where = lab ? '' : JSON.stringify(await page.evaluate((tt) => window.whereAt(tt), t));
        console.log(`t=${t} ${((Date.now() - t0) / 1000).toFixed(2)}s ${where} -> ${path.relative(ROOT, f)}`);
      }
    } else if (mode === 'sheet') {
      const a = Number(arg('from', 0)), b = Number(arg('to', dur || 10)), n = Number(arg('n', 12));
      const tmp = path.join(ROOT, 'out/tmp_sheet_' + process.pid);
      fs.mkdirSync(tmp, { recursive: true });
      const files = [];
      for (let k = 0; k < n; k++) {
        const t = n === 1 ? a : a + (b - a) * k / (n - 1);
        const data = await page.evaluate((tt) => window.renderAt(tt, 0.9), t);
        const f = path.join(tmp, `${String(k).padStart(3, '0')}.jpg`); save(data, f); files.push([f, t]);
      }
      const outF = path.join(ROOT, arg('out', `out/sheets/${lab || 'film'}_${a}-${b}.jpg`));
      fs.mkdirSync(path.dirname(outF), { recursive: true });
      const scale = Number(arg('scale', 0.33)), cols = Number(arg('cols', 4));
      const labeled = files.map(([f, t]) => { const g = f.replace('.jpg', '_l.jpg'); execFileSync('convert', [f, '-resize', `${Math.round(scale * 100)}%`, '-gravity', 'North', '-fill', 'yellow', '-undercolor', '#000a', '-pointsize', '16', '-annotate', '+0+4', t.toFixed(2) + 's', g]); return g; });
      execFileSync('montage', [...labeled, '-tile', `${cols}x`, '-geometry', '+2+2', '-background', '#222', outF]);
      fs.rmSync(tmp, { recursive: true, force: true });
      console.log('sheet ->', path.relative(ROOT, outF));
    } else if (mode === 'frames') {
      const f0 = Number(arg('from', 0)), f1 = Number(arg('to', Math.floor(dur * FPS)));
      const outDir = path.join(ROOT, arg('out', 'out/frames'));
      fs.mkdirSync(outDir, { recursive: true });
      await page.evaluate(([a, b]) => window.prepareRange && window.prepareRange(a, b), [f0 / FPS, f1 / FPS]);
      const t0 = Date.now();
      for (let f = f0; f <= f1; f++) {
        const file = path.join(outDir, `${String(f).padStart(5, '0')}.jpg`);
        if (fs.existsSync(file) && !process.argv.includes('--force')) continue;
        const data = await page.evaluate((tt) => window.renderAt(tt, 0.94), f / FPS);
        save(data, file);
        if ((f - f0) % 48 === 0) console.log(`frame ${f}/${f1} ${(((Date.now() - t0) / 1000) / (f - f0 + 1)).toFixed(2)} s/frame`);
      }
      console.log(`done ${f0}-${f1} in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    } else if (mode === 'bench') {
      const t = Number(arg('t', 1));
      for (let i = 0; i < 2; i++) await page.evaluate((tt) => window.renderAt(tt, 0.93), t + i / FPS);
      const t0 = Date.now();
      for (let i = 0; i < 8; i++) await page.evaluate((tt) => window.renderAt(tt, 0.93), t + (i + 2) / FPS);
      console.log(`bench t=${t}: ${((Date.now() - t0) / 8000).toFixed(3)} s/frame`);
    }
    await page.close();
  } finally {
    await browser.close(); srv.close();
  }
}
main().catch((e) => { console.error(e.message || e); process.exit(1); });
