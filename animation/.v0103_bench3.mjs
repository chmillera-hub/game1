import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import path from 'path'; import fs from 'fs'; import { pathToFileURL } from 'url';
const ROOT = '/home/user/game1/animation';
for (const [f, name] of [['Caveat.ttf', 'Caveat'], ['Fraunces.ttf', 'Fraunces'], ['PatrickHand.ttf', 'Patrick Hand']]) {
  const p = path.join(ROOT, 'assets/fonts', f); if (fs.existsSync(p)) GlobalFonts.registerFromPath(p, name); }
const { loadTimeline, makeScene } = await import(pathToFileURL(ROOT + '/src/timeline.mjs').href);
loadTimeline();
const [id, file, a, b] = process.argv.slice(2);
const m = await import(pathToFileURL(path.resolve(file)).href);
const S = makeScene(id);
const c = createCanvas(720, 1280); const g = c.getContext('2d');
for (let pass = 0; pass < 2; pass++) {
  const res = [];
  for (let f = Math.round(+a * 24); f < Math.round(+b * 24); f++) {
    const t = f / 24; const t0 = performance.now(); g.save(); m.render(g, t, S); g.restore(); g.getImageData(0,0,1,1); res.push([performance.now() - t0, t]);
  }
  const v = res.map(r => r[0]).sort((x, y) => x - y);
  res.sort((x, y) => y[0] - x[0]);
  console.log(path.basename(file), a, b, 'pass', pass, 'med', v[v.length >> 1].toFixed(1), 'p90', v[Math.floor(v.length * 0.9)].toFixed(1), 'max', res.slice(0, 4).map(r => r[0].toFixed(1) + '@' + r[1].toFixed(2)).join(' '));
}
