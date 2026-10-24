import fs from 'fs'; import vm from 'vm';
const root = new URL('..', import.meta.url).pathname;
const ctx = { window: { matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {}, devicePixelRatio: 1, innerWidth: 1366 }, document: { documentElement: { getAttribute: () => null }, querySelectorAll: () => [], addEventListener() {} }, MutationObserver: class { observe() {} }, getComputedStyle: () => ({ getPropertyValue: () => '' }), performance, console, Math, BigInt, Float32Array, Float64Array, Int32Array, Int16Array, Uint8Array };
ctx.globalThis = ctx; ctx.matchMedia = ctx.window.matchMedia; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(root + 'src/core.js', 'utf8') + '\nglobalThis.Lab = Lab;', ctx);
let ch2 = fs.readFileSync(root + 'src/ch2_scissors.js', 'utf8').replace(/Lab\.register\(ch\);\s*\}\s*$/, 'globalThis.__ch2 = { planPieces, PaperSim, pieceSpec, curves, measure, sameTopology, setSim: s => { sim = s; } };\n}');
vm.runInContext(ch2, ctx);
const T = ctx.__ch2, Lab = ctx.Lab;
const [n, fr] = [+process.argv[2] || 2, (process.argv[3] || '0.3333333,0.6666667').split(',').map(Number)];
const specs = T.planPieces(n, fr).pieces.map(pc => T.pieceSpec(pc, n, 1));
const sim = new T.PaperSim(specs, 0.04); T.setSim(sim);
const pred = T.measure(); let t = 0, jig = 0, auto = false;
for (let k = 0; k < 60 * 16; k++) {
  const dt = 1 / 60; t += dt;
  sim.setBlend(Lab.smooth(Math.min(1, t / 2.2))); sim.rScale = Math.min(1, 0.3 + t / 1.6);
  if (t > 2.4 && !sim.asleep) sim.spread(6e-5, 1.5e-5);
  if (!auto && t > 2.4) { auto = true; jig = 0.5; }
  if (jig > 0) { sim.wake(); sim.kick(0.016 * jig); jig = Math.max(0, jig - dt); }
  if (!sim.asleep) { sim.step(dt, sim.blend < 1 ? 6 : 4); sim.recenter(); }
  if (k % 60 === 59) {
    const m = T.measure();
    const cents = sim.specs.map(sp => { let x = 0, y = 0, z = 0; const mm = sp.M * sp.K; for (let q = 0; q < mm; q++) { const id = (sp.offset + q) * 3; x += sim.pos[id]; y += sim.pos[id + 1]; z += sim.pos[id + 2]; } return [x / mm, y / mm, z / mm].map(v => v.toFixed(1)).join(','); });
    let maxStr = 0; for (let c = 0; c < sim.ca.length; c++) { if (sim.k[c] < 0.5) continue; const a = sim.ca[c] * 3, b = sim.cb[c] * 3; const L = Math.hypot(sim.pos[b] - sim.pos[a], sim.pos[b + 1] - sim.pos[a + 1], sim.pos[b + 2] - sim.pos[a + 2]); maxStr = Math.max(maxStr, Math.abs(L - sim.rest[c]) / sim.rest[c]); }
    console.log(`t=${t.toFixed(0)} same=${T.sameTopology(pred, m)} links=${m.links.map(l => l.lk).join(',')} cents=[${cents.join(' | ')}] maxStrain=${(maxStr * 100).toFixed(0)}% asleep=${sim.asleep}`);
  }
}
