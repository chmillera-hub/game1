// Screenshot a page of this project in headless Chromium.
// Usage: node tools/snap.mjs <page.html?query> <out.png> [width] [height] [scale]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.woff2': 'font/woff2', '.png': 'image/png', '.css': 'text/css' };

export function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(res);
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [page, out, w = '1080', h = '1920', sc = '1'] = process.argv.slice(2);
  const srv = await serve();
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: +w, height: +h }, deviceScaleFactor: +sc });
  const pg = await ctx.newPage();
  pg.on('console', (m) => console.log('[page]', m.text()));
  pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
  await pg.goto(`http://127.0.0.1:${srv.address().port}/${page}`);
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForFunction(() => window.__ready === true, null, { timeout: 30000 }).catch(() => {});
  await pg.screenshot({ path: out });
  await browser.close();
  srv.close();
}
