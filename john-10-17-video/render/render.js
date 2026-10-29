// Playwright driver.
//   node render/render.js preview <shotId> [p1,p2,...]   -> stills at normalized times into previews/
//   node render/render.js frames <shotId|all> [--from k]  -> JPEG frame sequence per shot into frames/<id>/
// Frames are numbered by global frame index so the compositor can overlap shots for dissolves.
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const SCRATCH = process.env.SCRATCH || '/tmp/claude-0/-home-user-game1/2b62858c-fbb0-5a8d-a052-11a01031b8ed/scratchpad';
const ASSETS = path.join(SCRATCH, 'assets');
const OUT = process.env.OUT || path.join(SCRATCH, 'out');
const FPS = 24;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.ttf': 'font/ttf', '.hdr': 'application/octet-stream', '.gltf': 'model/gltf+json', '.bin': 'application/octet-stream' };

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((q, r) => {
      const url = decodeURIComponent(q.url.split('?')[0]);
      const file = url.startsWith('/assets/') ? path.join(ASSETS, url.slice(8)) : path.join(ROOT, url);
      fs.stat(file, (err, st) => {
        if (err || !st.isFile()) { r.writeHead(404); r.end(); return; }
        r.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Content-Length': st.size, 'Cache-Control': 'max-age=3600' });
        if (q.method === 'HEAD') { r.end(); return; }
        fs.createReadStream(file).pipe(r);
      });
    }).listen(0, '127.0.0.1', () => resolve(srv));
  });
}

async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 720, height: 1280 } });
  page.on('console', (m) => { const t = m.text(); if (!/GPU stall|Automatic fallback/.test(t)) console.log('  page:', t); });
  page.on('pageerror', (e) => console.log('  PAGE ERROR:', e.message));
  await page.goto(`http://127.0.0.1:${port}/render/index.html`);
  await page.waitForFunction('window.ready === true', null, { timeout: 120000 });
  return page;
}

function loadShots() {
  const shots = JSON.parse(fs.readFileSync(process.env.SHOTS || path.join(ROOT, 'script/shots.json'), 'utf8'));
  return shots.shots;
}

async function main() {
  const [mode, which, extra] = process.argv.slice(2);
  const srv = await serve();
  const port = srv.address().port;
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-watchdog', '--js-flags=--max-old-space-size=8192'] });
  const shots = loadShots();
  try {
    if (mode === 'preview') {
      const spec = shots.find((s) => s.id === which);
      if (!spec) throw new Error('no shot ' + which);
      const ps = (extra || '0.1,0.5,0.9').split(',').map(Number);
      const page = await openPage(browser, port);
      const t0 = Date.now();
      await page.evaluate((s) => window.setupShot(s), spec);
      console.log(`setup ${which}: ${((Date.now() - t0) / 1000).toFixed(1)}s`);
      fs.mkdirSync(path.join(OUT, 'previews'), { recursive: true });
      for (const p of ps) {
        const t1 = Date.now();
        const data = await page.evaluate((t) => window.renderFrame(t, 0.92), p * spec.duration);
        const f = path.join(OUT, 'previews', `${which}_${String(Math.round(p * 100)).padStart(3, '0')}.jpg`);
        fs.writeFileSync(f, Buffer.from(data.split(',')[1], 'base64'));
        console.log(`  p=${p} ${((Date.now() - t1) / 1000).toFixed(2)}s -> ${f}`);
      }
      await page.close();
    } else if (mode === 'bench') {
      const q = JSON.parse(extra || '{}');
      const base = shots.find((s) => s.id === which);
      const spec = { ...base, quality: q, params: { ...base.params, ...(q.params || {}) } };
      const page = await openPage(browser, port);
      await page.evaluate((s) => window.setupShot(s), spec);
      for (let i = 0; i < 2; i++) await page.evaluate((t) => window.renderFrame(t), i / 24);
      const t0 = Date.now();
      for (let i = 0; i < 6; i++) await page.evaluate((t) => window.renderFrame(t), (i + 2) / 24);
      console.log(`bench ${which} ${extra}: ${((Date.now() - t0) / 6000).toFixed(2)} s/frame`);
      await page.close();
    } else if (mode === 'frames') {
      const list = which === 'all' ? shots : shots.filter((s) => which.split(',').includes(s.id));
      for (const spec of list) {
        const dir = path.join(OUT, 'frames', spec.id);
        fs.mkdirSync(dir, { recursive: true });
        const f0 = spec.frame_start, f1 = spec.frame_end;
        const done = fs.readdirSync(dir).filter((f) => f.endsWith('.jpg')).length;
        if (done >= f1 - f0 + 1 && extra !== '--force') { console.log(`${spec.id}: complete (${done})`); continue; }
        const page = await openPage(browser, port);
        const t0 = Date.now();
        await page.evaluate((s) => window.setupShot(s), spec);
        console.log(`${spec.id}: setup ${((Date.now() - t0) / 1000).toFixed(1)}s, frames ${f0}-${f1}`);
        const t1 = Date.now();
        for (let f = f0; f <= f1; f++) {
          const tl = f / FPS - spec.start;
          const data = await page.evaluate((t) => window.renderFrame(t), tl);
          fs.writeFileSync(path.join(dir, `${String(f).padStart(5, '0')}.jpg`), Buffer.from(data.split(',')[1], 'base64'));
          if ((f - f0) % 48 === 0) console.log(`  ${spec.id} frame ${f} (${(((Date.now() - t1) / 1000) / (f - f0 + 1)).toFixed(2)} s/frame)`);
        }
        console.log(`${spec.id}: done in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
        await page.close();
      }
    }
  } finally {
    await browser.close();
    srv.close();
  }
}
main().catch((e) => { console.error(e); process.exit(1); });
