// Run with: node test/core.test.js
// Checks the simulator against results you get with real paper.
const assert = require('assert');
const C = require('../src/core.js');

function run(strips, joints) {
  return C.cutModel(C.buildModel({ strips, joints }));
}
const kinds = (r) => r.pieces.map((p) => p.type).sort().join(',');
let passed = 0;
function check(name, fn) {
  try { fn(); passed++; console.log('ok   ' + name); }
  catch (e) { console.log('FAIL ' + name + '\n     ' + e.message); process.exitCode = 1; }
}

check('uncut Möbius strip is one-sided with one edge', () => {
  const r = run([{ halfTwists: 1, cuts: [] }]);
  assert.strictEqual(kinds(r), 'mobius');
  assert.strictEqual(r.pieces[0].edgeCount, 1);
  assert.strictEqual(r.pieces[0].halfTwists, 1);
});

check('Möbius cut in half: one loop, twice as long, 4 half-twists', () => {
  const r = run([{ halfTwists: 1, cuts: [1 / 2] }]);
  assert.strictEqual(kinds(r), 'band');
  assert.strictEqual(Math.abs(r.pieces[0].halfTwists), 4);
  assert.ok(Math.abs(r.pieces[0].lengthRatio - 2) < 0.25);
  assert.strictEqual(r.pieces[0].knot.det, 1);
});

for (const c of [1 / 3, 1 / 4, 0.2]) {
  check(`Möbius cut at ${c.toFixed(3)}: Möbius strip linked with a long loop`, () => {
    const r = run([{ halfTwists: 1, cuts: [c] }]);
    assert.strictEqual(kinds(r), 'band,mobius');
    const band = r.pieces.find((p) => p.type === 'band');
    const mob = r.pieces.find((p) => p.type === 'mobius');
    assert.strictEqual(Math.abs(band.halfTwists), 4);
    assert.strictEqual(Math.abs(mob.halfTwists), 1);
    assert.strictEqual(r.links.length, 1);
    assert.strictEqual(r.links[0].lk, 1);
  });
}

check('left-handed twist stays left-handed', () => {
  const r = run([{ halfTwists: -1, cuts: [1 / 3] }]);
  assert.ok(r.pieces.every((p) => p.halfTwists < 0));
});

check('plain loop cut in half: two plain loops, not linked', () => {
  const r = run([{ halfTwists: 0, cuts: [1 / 2] }]);
  assert.strictEqual(kinds(r), 'band,band');
  assert.ok(r.pieces.every((p) => p.halfTwists === 0));
  assert.strictEqual(r.links.length, 0);
});

check('full twist cut in half: two loops linked once', () => {
  const r = run([{ halfTwists: 2, cuts: [1 / 2] }]);
  assert.strictEqual(kinds(r), 'band,band');
  assert.strictEqual(r.links.length, 1);
});

check('three half-twists cut in half: one loop tied in a trefoil', () => {
  const r = run([{ halfTwists: 3, cuts: [1 / 2] }]);
  assert.strictEqual(kinds(r), 'band');
  assert.strictEqual(r.pieces[0].knot.det, 3);
});

check('two plain loops crossed and halved: one square frame', () => {
  const r = run([{ halfTwists: 0, cuts: [1 / 2] }, { halfTwists: 0, cuts: [1 / 2] }], ['orthogonal']);
  assert.strictEqual(kinds(r), 'band');
  assert.strictEqual(r.pieces[0].halfTwists, 0);
});

check('two crossed loops, uncut: a punctured torus', () => {
  const r = run([{ halfTwists: 0, cuts: [] }, { halfTwists: 0, cuts: [] }], ['orthogonal']);
  assert.strictEqual(r.pieces[0].chi, -1);
  assert.strictEqual(r.pieces[0].genus, 1);
});

check('Möbius strips with opposite twists crossed and halved: two interlocked hearts', () => {
  const r = run([{ halfTwists: 1, cuts: [1 / 2] }, { halfTwists: -1, cuts: [1 / 2] }], ['orthogonal']);
  assert.strictEqual(kinds(r), 'band,band');
  assert.strictEqual(r.links.length, 1);
});

check('Möbius strips with the same twist crossed and halved: two separate loops', () => {
  const r = run([{ halfTwists: 1, cuts: [1 / 2] }, { halfTwists: 1, cuts: [1 / 2] }], ['orthogonal']);
  assert.strictEqual(kinds(r), 'band,band');
  assert.strictEqual(r.links.length, 0);
});

check('parallel tape keeps the layers joined', () => {
  const r = run([{ halfTwists: 1, cuts: [1 / 2] }, { halfTwists: 1, cuts: [1 / 2] }], ['parallel']);
  assert.ok(r.pieces.some((p) => p.type === 'compound'));
});

check('cut results do not depend on mesh details (0.33 vs 1/3)', () => {
  const a = run([{ halfTwists: 1, cuts: [1 / 3] }]);
  const b = run([{ halfTwists: 1, cuts: [0.33] }]);
  assert.strictEqual(kinds(a), kinds(b));
  assert.strictEqual(a.links.length, b.links.length);
});

check('fractions parse', () => {
  assert.strictEqual(C.parseFraction('1/3'), 1 / 3);
  assert.strictEqual(C.parseFraction('25%'), 0.25);
  assert.strictEqual(C.parseFraction('0.4'), 0.4);
  assert.strictEqual(C.parseFraction('abc'), null);
});

console.log(`\n${passed} checks passed`);
