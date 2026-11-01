// Keep Halving: for 1 to 5 cuts, measure the strip exactly as cut (twists, knots, links), then check that
// the pulled-apart ring drawing has the same twists and links and that no two strips touch, thickened or not.
import fs from 'fs'; import vm from 'vm';
const root = new URL('..', import.meta.url).pathname;
const ctx = { window: { matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {}, devicePixelRatio: 1 }, document: { documentElement: { getAttribute: () => null }, querySelectorAll: () => [], addEventListener() {} }, MutationObserver: class { observe() {} }, getComputedStyle: () => ({ getPropertyValue: () => '' }), performance, console, Math, BigInt, Float32Array, Int32Array, Map, Set };
ctx.globalThis = ctx; ctx.matchMedia = ctx.window.matchMedia; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(root + 'src/core.js', 'utf8') + '\nglobalThis.Lab = Lab;', ctx);
const src = fs.readFileSync(root + 'src/ch2a_halving.js', 'utf8').replace(/Lab\.register\(ch\);\s*\}\s*$/, 'globalThis.__h = { stripPoint, layoutFor, ringPoint, buildRing, pickTwistSign, count, st, SEG, NS };\n}');
vm.runInContext(src, ctx);
const H = ctx.__h, Lab = ctx.Lab;
H.pickTwistSign(); H.buildRing();
let fail = 0;
const uniq = a => [...new Set(a)].join(',');
for (let k = 1; k <= 5; k++) {
  const m = H.count(k), n = H.NS;
  const strip = (j, v) => Array.from({ length: n }, (_, i) => H.stripPoint(k, j, i / n, v));
  const cores = Array.from({ length: m }, (_, j) => strip(j, 0));
  const tw = cores.map((_, j) => Lab.linking(strip(j, -1), strip(j, 1)));
  const kn = cores.map(c => Lab.knotDet(c));
  const lk = []; for (let a = 0; a < m; a++) for (let b = a + 1; b < m; b++) lk.push(Lab.linking(cores[a], cores[b]));
  let line = `cuts ${k}: ${m} pieces | cut strip: twists {${uniq(tw)}} knots {${uniq(kn)}} links {${uniq(lk)}} (${lk.length} pairs)`;
  if (tw.some(v => Math.abs(v) !== 2) || kn.some(v => v !== 1) || lk.some(v => Math.abs(v) !== 2)) fail++;
  for (const thick of [true, false]) {
    const L = H.layoutFor(k, thick), S = H.SEG;
    const ring = (j, v) => Array.from({ length: S }, (_, i) => H.ringPoint(i, L.off[j], L.w[j], v));
    const rc = Array.from({ length: m }, (_, j) => ring(j, 0));
    const rtw = rc.map((_, j) => Lab.linking(ring(j, -1), ring(j, 1)));
    const rlk = []; for (let a = 0; a < m; a++) for (let b = a + 1; b < m; b++) rlk.push(Lab.linking(rc[a], rc[b]));
    // closest approach between the edges of different strips (sampled across each strip's width too)
    let gap = Infinity;
    const pts = Array.from({ length: m }, (_, j) => [-1, 0, 1].flatMap(v => ring(j, v)));
    for (let a = 0; a < m; a++) for (let b = a + 1; b < m; b++) for (const p of pts[a]) for (const q of pts[b]) { const d = Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]); if (d < gap) gap = d; }
    const same = rtw.every((v, i) => v === tw[i]) && rlk.every((v, i) => v === lk[i]);
    if (!same || gap < 0.004) fail++;
    line += `\n   ring ${thick ? 'thickened' : 'true width'}: twists {${uniq(rtw)}} links {${uniq(rlk)}} ${same ? 'same as the cut strip' : 'DIFFERENT'}; closest strips ${gap === Infinity ? '-' : gap.toFixed(3)}`;
  }
  console.log(line);
}
console.log(fail ? `FAIL (${fail})` : 'all checks held');
