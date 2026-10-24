// Do two unlinked objects really come apart? Cut, then pull apart for a long time and watch the gap.
import fs from 'fs'; import vm from 'vm';
const root = new URL('..', import.meta.url).pathname;
const ctx = { window: { matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {}, removeEventListener() {}, devicePixelRatio: 1, innerWidth: 1366 }, document: { documentElement: { getAttribute: () => null }, querySelectorAll: () => [], addEventListener() {} }, MutationObserver: class { observe() {} }, getComputedStyle: () => ({ getPropertyValue: () => '' }), performance, console, Math, BigInt, Float32Array, Float64Array, Int32Array, Int16Array, Int8Array, Uint8Array, Map, Set };
ctx.globalThis = ctx; ctx.matchMedia = ctx.window.matchMedia; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(root + 'src/core.js', 'utf8') + '\nglobalThis.Lab = Lab;', ctx);
const src = fs.readFileSync(root + 'src/ch2b_tape.js', 'utf8').replace(/Lab\.register\(ch\);\s*\}\s*$/, `globalThis.__tape = { st, reset, startCut, stepCut, step, setBlend, spread, recenter, kick, measureGeo, get blend() { return blend; }, get asleep() { return asleep; }, wake, pos, alive, objOfNode, NN };\n}`);
vm.runInContext(src, ctx);
const T = ctx.__tape, Lab = ctx.Lab, st = T.st;
const [A, B, join, push] = [process.argv[2] || 'left', process.argv[3] || 'left', process.argv[4] || 'cross', +(process.argv[5] || 6e-5)];
function frames(secs) {
  for (let k = 0; k < Math.round(secs * 60); k++) {
    const dt = 1 / 60; st.t += dt; st.tCut += dt;
    T.setBlend(Lab.smooth(Math.min(1, st.t / 2.2)));
    if (st.cutting) T.stepCut(dt);
    if (!st.autoJig && st.tCut > 0.8 && !st.cutting) { st.autoJig = true; st.jiggle = 0.4; }
    if (st.jiggle > 0) { T.wake(); T.kick(0.016 * st.jiggle); st.jiggle = Math.max(0, st.jiggle - dt); }
    if (st.t > 2.4 && !T.asleep) T.spread(push, 1.5e-5);
    if (!T.asleep) { T.step(dt, T.blend < 1 ? 6 : 4); T.recenter(); }
  }
}
function gap() {
  const no = st.res.objects.length; if (no < 2) return 'one object';
  const P = T.pos, c = Array.from({ length: no }, () => [0, 0, 0, 0]);
  for (let i = 0; i < T.NN; i++) if (T.alive[i]) { const o = T.objOfNode[i]; c[o][0] += P[i * 3]; c[o][1] += P[i * 3 + 1]; c[o][2] += P[i * 3 + 2]; c[o][3]++; }
  const cc = c.map(v => v.slice(0, 3).map(x => x / v[3]));
  // closest approach between the two objects' points
  let best = Infinity; const pts = [[], []];
  for (let i = 0; i < T.NN; i += 2) if (T.alive[i]) pts[T.objOfNode[i] ? 1 : 0].push(i);
  for (const a of pts[0]) for (const b of pts[1]) { const d = Math.hypot(P[a * 3] - P[b * 3], P[a * 3 + 1] - P[b * 3 + 1], P[a * 3 + 2] - P[b * 3 + 2]); if (d < best) best = d; }
  return `centroid gap ${Math.hypot(cc[0][0] - cc[1][0], cc[0][1] - cc[1][1], cc[0][2] - cc[1][2]).toFixed(2)}, closest points ${best.toFixed(3)}, asleep ${T.asleep}`;
}
st.A = A; st.B = B; st.join = join; T.reset();
frames(2.6); T.startCut('A'); frames(4.5); frames(2); T.startCut('B'); frames(4.5);
frames(2); st.geo = T.measureGeo(); console.log("olinks", st.geo.olinks.join(",")); for (let s = 0; s <= 40; s += 10) { console.log(`t+${s}s: ${gap()}`); frames(10); }
