// Headless check of "Cut again": cut, relax, re-cut a piece from its relaxed shape, relax again,
// and confirm the simulated paper keeps the topology it had at the moment of each cut.
import fs from 'fs'; import vm from 'vm';
const root = new URL('..', import.meta.url).pathname;
const ctx = { window: { matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {}, devicePixelRatio: 1, innerWidth: 1366 }, document: { documentElement: { getAttribute: () => null }, querySelectorAll: () => [], addEventListener() {} }, MutationObserver: class { observe() {} }, getComputedStyle: () => ({ getPropertyValue: () => '' }), performance, console, Math, BigInt, Float32Array, Float64Array, Int32Array, Int16Array, Uint8Array };
ctx.globalThis = ctx; ctx.matchMedia = ctx.window.matchMedia; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(root + 'src/core.js', 'utf8') + '\nglobalThis.Lab = Lab;', ctx);
let src = fs.readFileSync(root + 'src/ch2_scissors.js', 'utf8').replace(/Lab\.register\(ch\);\s*\}\s*$/, 'globalThis.__ch2 = { planPieces, PaperSim, pieceSpec, measure, sameTopology, splitSpec, specFromCurrent, recutBlocker, describe, NAMES, COLORS, setSim: s => { sim = s; }, getSim: () => sim };\n}');
vm.runInContext(src, ctx);
const T = ctx.__ch2, Lab = ctx.Lab;

function relax(sim, secs, pred, label) {
  let t = 0, jig = 0, auto = false, bad = 0, checks = 0;
  for (let k = 0; k < 60 * secs; k++) {
    const dt = 1 / 60; t += dt;
    sim.setBlend(Lab.smooth(Math.min(1, t / 2.2))); sim.rScale = Math.min(1, 0.3 + t / 1.6);
    if (t > 2.4 && !sim.asleep) sim.spread(6e-5, 1.5e-5);
    if (!auto && t > 2.4) { auto = true; jig = 0.5; }
    if (jig > 0) { sim.wake(); sim.kick(0.016 * jig); jig = Math.max(0, jig - dt); }
    if (!sim.asleep) { sim.step(dt, sim.blend < 1 ? 6 : 4); sim.recenter(); }
    if (k % 60 === 59 && t > 2.6) { checks++; if (!T.sameTopology(pred, T.measure())) bad++; }
  }
  let maxStr = 0; for (let c = 0; c < sim.ca.length; c++) { if (sim.k[c] < 0.5) continue; const a = sim.ca[c] * 3, b = sim.cb[c] * 3; const L = Math.hypot(sim.pos[b] - sim.pos[a], sim.pos[b + 1] - sim.pos[a + 1], sim.pos[b + 2] - sim.pos[a + 2]); maxStr = Math.max(maxStr, Math.abs(L - sim.r1[c]) / sim.r1[c]); }
  return { bad, checks, maxStr };
}
const fmt = m => `twists=${m.pieces.map(p => p.twist).join(',')} knots=${m.pieces.map(p => p.knot).join(',')} links=${m.links.map(l => `${l.a}${l.b}:${l.lk}`).join(' ') || '–'}`;

const cases = [
  { n: 1, fr: [1 / 2], cuts: [0] },        // infinity loop, cut again: two linked infinity loops
  { n: 1, fr: [1 / 2], cuts: [0, 0] },     // and again
  { n: 3, fr: [1 / 2], cuts: [0] },        // trefoil loop cut again
  { n: 1, fr: [1 / 3], cuts: [0] },        // thin Möbius cut again: becomes a long loop
  { n: 1, fr: [1 / 3], cuts: [1] },        // long loop cut again
  { n: 0, fr: [1 / 2], cuts: [0] },        // plain ring
  { n: 2, fr: [1 / 2], cuts: [1] },
];
let fails = 0;
for (const cs of cases) {
  const plan = T.planPieces(cs.n, cs.fr);
  const specs = plan.pieces.map(pc => T.pieceSpec(pc, cs.n, 1));
  specs.forEach((sp, i) => { sp.name = T.NAMES[i]; sp.color = T.COLORS[i]; });
  let sim = new T.PaperSim(specs, 0.04); T.setSim(sim);
  let pred = T.measure();
  let r = relax(sim, 8, pred);
  let line = `n=${cs.n} cut ${cs.fr.map(f => f.toFixed(2)).join(',')}: ${specs.length} pc ${fmt(pred)} [breaks ${r.bad}/${r.checks}]`;
  if (r.bad) fails++;
  for (const idx of cs.cuts) {
    const old = sim.specs, target = old[idx];
    const why = T.recutBlocker(target); if (why) { line += `\n   blocked: ${why}`; break; }
    const kids = T.splitSpec(target);
    const ns = []; old.forEach(sp => { if (sp === target) ns.push(...kids); else ns.push(T.specFromCurrent(sp)); });
    ns.forEach((sp, i) => { sp.name = sp.name || T.NAMES[i]; });
    sim = new T.PaperSim(ns, 0.04); ns.forEach((sp, i) => { sim.fresh[i] = kids.includes(sp) ? 1 : 0; }); T.setSim(sim);
    pred = T.measure();
    const t0 = performance.now();
    r = relax(sim, 12, pred);
    if (r.bad) fails++;
    line += `\n   then cut ${target.name} (${target.oneSided ? 'one' : 'two'}-sided, ${target.laps} lap): ${ns.length} pc, laps ${ns.map(s => s.laps).join(',')}, K ${ns.map(s => s.K).join(',')}, N=${sim.N} ${fmt(pred)} [breaks ${r.bad}/${r.checks}, strain ${(r.maxStr * 100).toFixed(0)}%, ${((performance.now() - t0) / 720).toFixed(1)} ms/frame]`;
    line += `\n   "${T.describe(sim.specs, pred)}"`;
  }
  console.log(line);
}
console.log(fails ? `FAIL: ${fails} topology breaks` : 'all topology checks held');
