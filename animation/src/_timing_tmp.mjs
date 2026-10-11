import path from 'path';
import { pathToFileURL } from 'url';
import { createCanvas } from '@napi-rs/canvas';
const ROOT = '/home/user/game1/animation';
const { loadTimeline, makeScene } = await import(pathToFileURL(path.join(ROOT, 'src/timeline.mjs')).href);
const [file, id] = process.argv.slice(2);
const TL = loadTimeline();
const m = await import(pathToFileURL(path.join(ROOT, 'src/scenes', file)).href);
const S = makeScene(id);
const c = createCanvas(720, 1280), g = c.getContext('2d');
const sc = TL.scenes.find((s) => s.id === id);
const res = [];
for (let t = sc.start; t < sc.end; t += 1 / 30) {
  const t0 = performance.now();
  g.save(); m.render(g, t, S); g.restore();
  res.push([performance.now() - t0, t]);
}
const raw = res.slice(); res.sort((a, b) => b[0] - a[0]);
const avg = res.reduce((a, b) => a + b[0], 0) / res.length;
const q = (p) => res[Math.floor(res.length * (1 - p))][0].toFixed(1); const seg = (a, b) => { const r = raw.filter(([d, t]) => t >= a && t < b).map(x => x[0]); return (r.reduce((x, y) => x + y, 0) / r.length).toFixed(1); }; console.log(id, "n", res.length, "avg", avg.toFixed(1), "p50", q(0.5), "p90", q(0.9), "p95", q(0.95), "top", res.slice(0, 5).map(([d, t]) => `${d.toFixed(0)}@${t.toFixed(2)}`).join(" "), "segB03", seg(155.97, 159.7), "segB02", seg(150.97, 155.97));
