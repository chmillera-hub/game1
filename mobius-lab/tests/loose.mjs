// Keep Halving, loose paper: for 0 to 3 cuts, let the pieces as cut go under the paper physics, shake them
// and pull them apart hard, and check that every twist and link measured at the start is still there.
import fs from 'fs'; import vm from 'vm';
const root = new URL('..', import.meta.url).pathname;
const ctx = { window: { matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {}, devicePixelRatio: 1, innerWidth: 1366 }, document: { documentElement: { getAttribute: () => null }, querySelectorAll: () => [], addEventListener() {} }, MutationObserver: class { observe() {} }, getComputedStyle: () => ({ getPropertyValue: () => '' }), performance, console, Math, BigInt, Float32Array, Float64Array, Int32Array, Int16Array, Uint8Array, Map, Set };
ctx.globalThis = ctx; ctx.matchMedia = ctx.window.matchMedia; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(root + 'src/core.js', 'utf8') + '\nglobalThis.Lab = Lab;', ctx);
const src = fs.readFileSync(root + 'src/ch2a_halving.js', 'utf8').replace(/Lab\.register\(ch\);\s*\}\s*$/, 'globalThis.__h = { looseSpecs, measureLoose, sameArr, st, count, LOOSE_MAXK, RAD, PUSH, BURST, INFLATE };\n}');
vm.runInContext(src, ctx);
const H = ctx.__h, Lab = ctx.Lab, st = H.st;
let fail = 0;
for (let k = 0; k <= H.LOOSE_MAXK; k++) {
  st.k = k;
  const specs = H.looseSpecs(k), sim = new Lab.PaperSim(specs, H.RAD);
  st.loose = { sim, specs };
  const before = H.measureLoose(), t0 = performance.now();
  let t = 0, jig = 0, burst = 0, breaks = 0, checks = 0, frames = 0;
  // 2.4 s settle, shake, pull hard, shake again, pull hard again: 16 s in all
  const events = { 2.5: () => { jig = 0.9; }, 5: () => { burst = 3; }, 9: () => { jig = 0.9; }, 11: () => { burst = 3; } };
  for (let f = 0; f < 60 * 16; f++) {
    const dt = 1 / 60; t += dt;
    for (const [at, fn] of Object.entries(events)) if (Math.abs(t - +at) < dt / 2) fn();
    sim.setBlend(Lab.smooth(Math.min(1, t / 2.2))); sim.rScale = Math.min(1, 0.3 + t / 1.6);
    if (jig > 0) { sim.wake(); sim.kick(0.016 * jig); jig = Math.max(0, jig - dt); }
    if (burst > 0) { burst -= dt; sim.wake(); }
    if (t > 2.4 && !sim.asleep) sim.spread(burst > 0 ? H.PUSH * H.BURST : H.PUSH, H.INFLATE);
    if (!sim.asleep) { sim.step(dt, sim.blend < 1 ? 6 : 4); sim.recenter(); frames++; }
    if (f % 60 === 59 && t > 2.6) { checks++; const now = H.measureLoose(); if (!H.sameArr(now.twist, before.twist) || !H.sameArr(now.links, before.links)) breaks++; }
  }
  let maxStr = 0; for (let c = 0; c < sim.ca.length; c++) { if (sim.k[c] < 0.5) continue; const a = sim.ca[c] * 3, b = sim.cb[c] * 3; const L = Math.hypot(sim.pos[b] - sim.pos[a], sim.pos[b + 1] - sim.pos[a + 1], sim.pos[b + 2] - sim.pos[a + 2]); maxStr = Math.max(maxStr, Math.abs(L - sim.r1[c]) / sim.r1[c]); }
  if (breaks) fail++;
  console.log(`cuts ${k}: ${specs.length} pieces, ${sim.N} points | twists {${[...new Set(before.twist)]}} links {${[...new Set(before.links)]}} | changed in ${breaks}/${checks} checks | max stretch ${(maxStr * 100).toFixed(0)}% | ${((performance.now() - t0) / Math.max(1, frames)).toFixed(1)} ms/frame`);
}
console.log(fail ? `FAIL (${fail})` : 'all loose checks held');
