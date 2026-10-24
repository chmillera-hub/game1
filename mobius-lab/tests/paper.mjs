import fs from 'fs';
import vm from 'vm';
const root = new URL('..', import.meta.url).pathname;
const ctx = {
  window: { matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {}, devicePixelRatio: 1, innerWidth: 1366 },
  document: { documentElement: { getAttribute: () => null }, querySelectorAll: () => [], addEventListener() {} },
  MutationObserver: class { observe() {} }, getComputedStyle: () => ({ getPropertyValue: () => '' }), performance, console, Math, BigInt,
  requestAnimationFrame() {}, location: { hash: '' }, history: {}, ResizeObserver: undefined, Float32Array, Int32Array, Int16Array, Uint8Array, Array, Set, Object, Number, String, JSON
};
ctx.globalThis = ctx; ctx.matchMedia = ctx.window.matchMedia;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(root + 'src/core.js', 'utf8') + '\nglobalThis.Lab = Lab;', ctx);
let ch2 = fs.readFileSync(root + 'src/ch2_scissors.js', 'utf8');
ch2 = ch2.replace(/Lab\.register\(ch\);\s*\}\s*$/, 'globalThis.__ch2 = { planPieces, PaperSim, pieceSpec, curves, measure, sameTopology, setSim: s => { sim = s; } };\n}');
vm.runInContext(ch2, ctx);
const T = ctx.__ch2, Lab = ctx.Lab;
const cases = [[0, [1/2]], [1, [1/2]], [1, [1/3]], [1, [1/5, 2/5]], [1, [1/3, 1/2]], [2, [1/2]], [2, [1/3, 2/3]], [3, [1/2]], [3, [1/3]], [4, [1/2]], [5, [1/2]], [1, [1/6]], [2, [1/4, 1/2]]];
for (const chi of [-1]) for (const [n, fr] of cases) {
  const plan = T.planPieces(n, fr);
  const specs = plan.pieces.map(pc => T.pieceSpec(pc, n, chi));
  const sim = new T.PaperSim(specs, 0.04); T.setSim(sim);
  const pred = T.measure();
  const t0 = performance.now(); let steps = 0, bad = 0; let t = 0;
  for (let k = 0; k < 900; k++) { // 15 simulated seconds at 60 fps
    t += 1 / 60; sim.setBlend(Lab.smooth(Math.min(1, t / 2.2))); sim.rScale = Math.min(1, 0.3 + t / 1.6);
    if (k > 144 && !sim.asleep) sim.spread(6e-5, 1.5e-5);
    if (k > 150 && k < 200) { sim.wake(); sim.kick(0.016); }
    if (sim.asleep) { continue; }
    sim.step(1 / 60, sim.blend < 1 ? 6 : 4); sim.recenter(); steps++;
    if (k % 60 === 59) { const m = T.measure(); if (!T.sameTopology(pred, m)) bad++; }
  }
  const ms = (performance.now() - t0) / steps;
  // stretch error after relax
  let maxStrain = 0; for (let c = 0; c < sim.ca.length; c++) { if (sim.k[c] < 0.5) continue; const a = sim.ca[c] * 3, b = sim.cb[c] * 3; const L = Math.hypot(sim.pos[b] - sim.pos[a], sim.pos[b + 1] - sim.pos[a + 1], sim.pos[b + 2] - sim.pos[a + 2]); maxStrain = Math.max(maxStrain, Math.abs(L - sim.r1[c]) / sim.r1[c]); }
  const rg = sim.specs.map(sp => { let cx=0,cy=0,cz=0; const m=sp.M*sp.K; for (let q=0;q<m;q++){const id=(sp.offset+q)*3; cx+=sim.pos[id];cy+=sim.pos[id+1];cz+=sim.pos[id+2];} cx/=m;cy/=m;cz/=m; let r=0; for (let q=0;q<m;q++){const id=(sp.offset+q)*3; r+=(sim.pos[id]-cx)**2+(sim.pos[id+1]-cy)**2+(sim.pos[id+2]-cz)**2;} return Math.sqrt(r/m).toFixed(2); });
  console.log(`rg=${rg.join('/')} n=${n} cuts=${fr.map(x => x.toFixed(3)).join(',')} pieces=${specs.length} nodes=${sim.N} | pred knots=${pred.pieces.map(p => p.knot).join(',')} twists=${pred.pieces.map(p => p.twist).join(',')} links=${pred.links.map(l => l.lk).join(',')} | topology breaks: ${bad}/15 | asleep ${sim.asleep} | ${ms.toFixed(1)} ms/frame | max strain ${(maxStrain * 100).toFixed(1)}%`);
}
