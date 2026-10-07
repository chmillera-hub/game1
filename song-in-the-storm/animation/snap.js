// usage: node snap.js part t1 t2 ... -> writes snaps/part_t.jpg
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
(async () => {
  const [part, ...ts] = process.argv.slice(2);
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  pg.on('console', m => console.log('console:', m.text())); pg.on('pageerror', e => console.log('ERR', e.message));
  const tl = fs.existsSync(`../${part}_timeline.json`) ? fs.readFileSync(`../${part}_timeline.json`, 'utf8') : '{}';
  await pg.addInitScript(`window.TIMELINE=${tl}; window.PART='${part}';`);
  await pg.goto('file://' + __dirname + '/page.html');
  fs.mkdirSync('snaps', { recursive: true });
  for (const t of ts) {
    const d = await pg.evaluate(t => { renderFrame(+t); return document.getElementById('c').toDataURL('image/jpeg', 0.85); }, t);
    fs.writeFileSync(`snaps/${part}_${t}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
  }
  await b.close();
})();
