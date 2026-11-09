// CPU-time bench (added with the USER review fixes): CPU-seconds burned by the whole Chromium process tree per
// rendered frame, robust to other processes loading the machine. Usage (from the project root):
//   node tools/cpubench.js <lab> <frames> <t,t,...>      e.g. node tools/cpubench.js user 6 2,96.6,97.6
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = '/home/user/game1/void-humor-3d';
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.ttf': 'font/ttf', '.woff2': 'font/woff2' };
const [lab, N, tl] = [process.argv[2], Number(process.argv[3] || 6), process.argv[4].split(',').map(Number)];
const HZ = 100;
function tree(root) {
  const kids = {}; const stat = {};
  for (const d of fs.readdirSync('/proc')) {
    if (!/^\d+$/.test(d)) continue;
    try { const s = fs.readFileSync(`/proc/${d}/stat`, 'utf8'); const r = s.slice(s.lastIndexOf(')') + 2).split(' '); stat[d] = r; (kids[r[1]] = kids[r[1]] || []).push(d); } catch (e) {}
  }
  let sum = 0; const st = [String(root)];
  while (st.length) { const p = st.pop(); if (stat[p]) sum += (Number(stat[p][11]) + Number(stat[p][12])) / HZ; for (const k of kids[p] || []) st.push(k); }
  return sum;
}
const srv = http.createServer((q, r) => {
  const url = decodeURIComponent(q.url.split('?')[0]);
  const file = path.join(ROOT, url.startsWith('/node_modules/') || url.startsWith('/data/') || url.startsWith('/assets/') ? url : path.join('web', url));
  fs.readFile(file, (err, buf) => { if (err) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); r.end(buf); });
}).listen(0, '127.0.0.1', async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-watchdog'] });
  const pid = process.pid;   // the browser tree hangs off this node process
  const page = await browser.newPage({ viewport: { width: 720, height: 1280 } });
  page.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  await page.goto(`http://127.0.0.1:${srv.address().port}/index.html?lab=${lab}`);
  await page.waitForFunction('window.ready === true', null, { timeout: 180000 });
  for (const t of tl) {
    for (let k = 0; k < 2; k++) await page.evaluate((tt) => window.renderAt(tt, 0.93), t + k / 240);
    const c0 = tree(pid), w0 = Date.now();
    for (let k = 0; k < N; k++) await page.evaluate((tt) => window.renderAt(tt, 0.93), t + (k + 2) / 240);
    console.log(`t=${t}: ${((tree(pid) - c0) / N).toFixed(3)} cpu-s/frame  (wall ${((Date.now() - w0) / 1000 / N).toFixed(2)} s)`);
  }
  await browser.close(); srv.close();
});
