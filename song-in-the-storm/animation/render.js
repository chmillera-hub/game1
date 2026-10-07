// node render.js part startFrame endFrame out.mp4
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'); const { spawn } = require('child_process');
(async () => {
  const [part, s0, s1, out] = process.argv.slice(2); const a = +s0, b = +s1;
  const b2 = await chromium.launch(); const pg = await b2.newPage({ viewport: { width: 1280, height: 720 } });
  pg.on('pageerror', e => console.log('ERR', e.message));
  const tl = fs.readFileSync(`../${part}_timeline.json`, 'utf8');
  await pg.addInitScript(`window.TIMELINE=${tl}; window.PART='${part}';`);
  await pg.goto('file://' + __dirname + '/page.html');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = a; f < b; f++) {
    const d = await pg.evaluate(t => { renderFrame(t); return document.getElementById('c').toDataURL('image/jpeg', 0.93); }, f / 24);
    const buf = Buffer.from(d.slice(d.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - a) % 240 === 0) console.log(part, out, f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b2.close();
  console.log('done', out, ((Date.now() - t0) / 1000).toFixed(0) + 's');
})();
