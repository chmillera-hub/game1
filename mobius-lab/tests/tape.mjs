// Headless run of the Tape chapter: build each construction, cut it, relax it, and report the exact
// topology plus whether the measured twists and links stay put (no paper passing through paper).
import fs from 'fs'; import vm from 'vm';
const root = new URL('..', import.meta.url).pathname;
const ctx = { window: { matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {}, removeEventListener() {}, devicePixelRatio: 1, innerWidth: 1366 }, document: { documentElement: { getAttribute: () => null }, querySelectorAll: () => [], addEventListener() {} }, MutationObserver: class { observe() {} }, getComputedStyle: () => ({ getPropertyValue: () => '' }), performance, console, Math, BigInt, Float32Array, Float64Array, Int32Array, Int16Array, Int8Array, Uint8Array, Map, Set };
ctx.globalThis = ctx; ctx.matchMedia = ctx.window.matchMedia; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(root + 'src/core.js', 'utf8') + '\nglobalThis.Lab = Lab;', ctx);
const src = fs.readFileSync(root + 'src/ch2b_tape.js', 'utf8').replace(/Lab\.register\(ch\);\s*\}\s*$/, `globalThis.__tape = { st, reset, startCut, stepCut, step, setBlend, spread, recenter, kick, measureGeo, analyze, describe, CHECKS, sameGeo,
  get blend() { return blend; }, get asleep() { return asleep; }, wake };\n}`);
vm.runInContext(src, ctx);
const T = ctx.__tape, Lab = ctx.Lab, st = T.st;
const only = process.argv[2];

function frames(secs, mode = 'apart') {
  for (let k = 0; k < Math.round(secs * 60); k++) {
    const dt = 1 / 60; st.t += dt; st.tCut += dt;
    T.setBlend(Lab.smooth(Math.min(1, st.t / 2.2)));
    if (st.cutting) T.stepCut(dt);
    if (!st.autoJig && st.tCut > 0.8 && !st.cutting) { st.autoJig = true; st.jiggle = 0.4; }
    if (st.jiggle > 0) { T.wake(); T.kick(0.016 * st.jiggle); st.jiggle = Math.max(0, st.jiggle - dt); }
    if (mode === 'apart' && st.t > 2.4 && !T.asleep) T.spread(6e-5, 1.5e-5);
    if (!T.asleep) { T.step(dt, T.blend < 1 ? 6 : 4); T.recenter(); }
  }
}
const sum = r => `${r.objects.length} obj / ${r.pieces.length} pc: ` + r.pieces.map(p => `${p.name}=${p.kind}${p.oneSided ? '(1-sided)' : ''} laps ${p.laps} edges ${p.nB}`).join(', ') +
  ' | objects: ' + r.objects.map(o => `χ${o.chi} ${o.manifold ? (o.oneSided ? 'one-sided' : 'two-sided') : 'non-manifold'} edges ${o.nB}`).join('; ') + ' | taped: ' + r.taped.map(t => `${r.pieces[t.p].name}-${r.pieces[t.q].name}×${t.places}`).join(' ');
const cases = [
  { A: 'plain', B: 'plain', join: 'cross', cuts: ['A', 'B'] },
  { A: 'left', B: 'plain', join: 'cross', cuts: ['A', 'B'] },
  { A: 'left', B: 'plain', join: 'cross', cuts: ['B', 'A'] },
  { A: 'left', B: 'right', join: 'par', cuts: ['A', 'B'] },
  { A: 'left', B: 'left', join: 'par', cuts: ['A', 'B'] },
  { A: 'left', B: 'left', join: 'cross', cuts: ['A', 'B'] },
  { A: 'plain', B: 'plain', join: 'par', cuts: ['A', 'B'] },
  { A: 'full', B: 'plain', join: 'cross', cuts: ['A', 'B'] },
];
let bad = 0;
for (const [ci, cs] of cases.entries()) {
  if (only != null && +only !== ci) continue;
  st.A = cs.A; st.B = cs.B; st.join = cs.join; T.reset();
  const t0 = performance.now(); let nf = 0;
  console.log(`\n#${ci} A=${cs.A} B=${cs.B} ${cs.join}\n  uncut: ${sum(st.res)}`);
  frames(2.6); nf += 156;
  for (const sh of cs.cuts) {
    T.startCut(sh); frames(4.2); nf += 252;
    console.log(`  after ${sh}: ${sum(st.res)}`);
    frames(1.6); nf += 96;
    const g0 = T.measureGeo(); let breaks = 0;
    for (let s = 0; s < 6; s++) { frames(1); nf += 60; if (!T.sameGeo(g0, T.measureGeo())) breaks++; }
    if (breaks) bad++;
    console.log(`    twists ${g0.twist.map(v => v == null ? '-' : v).join(',')} links ${g0.links.join(',')} | object twists ${g0.otwist.map(v => v == null ? '-' : v).join(',')} object links ${g0.olinks.join(',') || '-'} | geometry changes: ${breaks}/6`);
    st.geo = g0; console.log(`    "${T.describe(st.res).replace(/<\/?b>/g, '')}"`);
  }
  console.log(`  ${((performance.now() - t0) / nf).toFixed(1)} ms/frame`);
}
console.log(bad ? `\nFAIL: ${bad} geometry breaks` : '\nall geometry checks held');
