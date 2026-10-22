// Rules for class talents. Run: node tests/talents.test.js
const assert = require('assert');
const store = {};
globalThis.localStorage = { getItem: (k) => store[k] || null, setItem: (k, v) => (store[k] = v), removeItem: (k) => delete store[k] };
const AG = require('./load')();
const R = AG.Run;
const D = AG.Data;

let passed = 0;
function test(name, fn) {
  try {
    fn();
    passed++;
  } catch (e) {
    console.error('FAIL', name);
    throw e;
  }
}

const fresh = () => R.newRun({ seed: 3, warband: 'vanguard', difficulty: 'knight' });

test('talents are the passive picks that cost Supply', () => {
  for (const t of Object.values(D.TALENTS)) {
    assert.ok(t.cost > 0 && !t.mod.active, t.name);
    assert.ok(D.UNITS[t.cls].abilities[t.tier].includes(t.id));
  }
  for (const T of Object.values(D.UNITS)) if (T.abilities) for (const tier of [1, 2]) assert.ok(!D.TALENTS[T.abilities[tier][0]], 'the default pick is always free');
  assert.ok(D.TALENTS.k_wall && D.TALENTS.k_riposte && !D.TALENTS.k_bash && !D.TALENTS.k_plate);
});

test('a talent must be owned before a unit can pick it', () => {
  const run = fresh();
  const k = R.addRecruit(run, 'knight');
  assert.ok(!R.setAbility(run, k.id, 1, 'k_wall'));
  assert.ok(R.setAbility(run, k.id, 1, 'k_bash'), 'actives stay free');
  const it = R.addItem(run, 'talent', 'k_wall');
  assert.ok(R.setAbility(run, k.id, 1, 'k_wall'));
  assert.strictEqual(R.itemHolder(run, it.uid), k);
  assert.ok(R.unitStats(run, k).traits.has('shieldwall'));
  assert.ok(R.costBreakdown(run, k).some((x) => x.label === 'Shield Wall' && x.cost === 2));
});

test('one copy, one unit: picking it elsewhere takes it', () => {
  const run = fresh();
  const a = R.addRecruit(run, 'knight');
  const b = R.addRecruit(run, 'knight');
  R.addItem(run, 'talent', 'k_wall');
  R.setAbility(run, a.id, 1, 'k_wall');
  assert.ok(R.setAbility(run, b.id, 1, 'k_wall'));
  R.normalizeLoad(run, a);
  assert.strictEqual(a.load.a1, 'k_bash', 'the first knight falls back to its free pick');
  assert.strictEqual(R.specFor(run, b).a1, 'k_wall');
  R.addItem(run, 'talent', 'k_wall');
  assert.ok(R.setAbility(run, a.id, 1, 'k_wall'), 'a second copy serves a second knight');
  R.normalizeLoad(run, b);
  assert.strictEqual(b.load.a1, 'k_wall');
});

test('class and level limits', () => {
  const run = fresh();
  const k = R.addRecruit(run, 'knight');
  const ar = R.addRecruit(run, 'archer');
  const wall = R.addItem(run, 'talent', 'k_wall');
  const rip = R.addItem(run, 'talent', 'k_riposte');
  assert.ok(!R.assignItem(run, ar.id, wall.uid), 'an archer cannot use a knight talent');
  assert.ok(!R.assignItem(run, k.id, rip.uid), 'Riposte needs Level 2');
  R.setLevel(run, k.id, 2);
  assert.ok(R.assignItem(run, k.id, rip.uid));
  assert.strictEqual(k.load.a2, 'k_riposte');
  R.unassignItem(run, rip.uid);
  assert.strictEqual(k.load.a2, 'k_plate', 'unequipping restores the free pick');
});

test('shops and spoils offer talents for your classes', () => {
  const run = fresh();
  const types = new Set(run.roster.map((r) => r.type));
  let shop = 0;
  for (let i = 0; i < 20; i++) {
    for (const it of R.genShop(run, { id: 'n' + i }).filter((x) => x.kind === 'talent')) {
      shop++;
      assert.ok(types.has(D.TALENTS[it.id].cls));
    }
  }
  assert.ok(shop > 0);
});

test('saves from before talents keep what units had picked', () => {
  const run = fresh();
  const k = R.addRecruit(run, 'knight');
  delete run.talents;
  k.load.a1 = 'k_wall';
  delete k.load.t1;
  R.save(run);
  const back = R.load();
  const k2 = back.roster.find((r) => r.id === k.id);
  R.normalizeLoad(back, k2);
  assert.strictEqual(k2.load.a1, 'k_wall');
  assert.ok(back.items.some((i) => i.kind === 'talent' && i.id === 'k_wall' && i.uid === k2.load.t1));
});

console.log(`talents: ${passed} tests passed`);
