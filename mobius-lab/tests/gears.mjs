import fs from 'fs'; import vm from 'vm';
const root = new URL('..', import.meta.url).pathname;
const ctx = { window: { matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {}, devicePixelRatio: 1, innerWidth: 1366 }, document: { documentElement: { getAttribute: () => null }, querySelectorAll: () => [], addEventListener() {} }, MutationObserver: class { observe() {} }, getComputedStyle: () => ({ getPropertyValue: () => '' }), performance, console, Math };
ctx.globalThis = ctx; ctx.matchMedia = ctx.window.matchMedia; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(root + 'src/core.js', 'utf8') + '\nglobalThis.Lab = Lab;', ctx);
let src = fs.readFileSync(root + 'src/ch5_gears.js', 'utf8').replace(/Lab\.register\(ch\);\s*\}\s*$/, 'globalThis.__g = { st, build: () => { W = 600; H = 450; build(); }, step, get gears() { return gears; }, get meshes() { return meshes; } };\n}');
vm.runInContext(src, ctx);
const G = ctx.__g;
for (const layout of ['ring', 'strip']) for (const mob of [false, true]) {
  const row = [];
  for (let N = 3; N <= 9; N++) {
    G.st.layout = layout; G.st.N = N; G.st.mobius = mob; G.st.grip = 1e9; G.st.motor = true; G.build();
    for (let k = 0; k < 6 * 60 * 6; k++) G.step(1 / 360);
    const w = G.gears[0].w; row.push(`${N}:${Math.abs(w) > 0.12 ? 'spin' : 'LOCK'}(${w.toFixed(2)})`);
  }
  console.log(layout.padEnd(5), mob ? 'mobius' : 'plain ', row.join(' '));
}
for (const lat of ['square', 'triangle']) { G.st.layout = 'lattice'; G.st.lattice = lat; G.build(); for (let k = 0; k < 2160; k++) G.step(1 / 360); console.log('lattice', lat, 'gears', G.gears.length, 'contacts', G.meshes.length, 'motor w', G.gears[G.st.motorGear].w.toFixed(2)); }
G.st.layout = 'ring'; G.st.N = 5; G.st.mobius = false; G.st.grip = 2; G.build(); for (let k = 0; k < 2160 * 2; k++) G.step(1 / 360); console.log('slippery odd ring: slips', G.st.slips, 'final w', G.gears[0].w.toFixed(2));
