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

const fresh = () => R.newRun({ seed: 3, warband: 'vanguard' });
// A fresh recruit: it arrives bare (its talent goes to the pack), so its slots are empty.
const bare = (run, type) => R.addRecruit(run, type);
const talentsOf = (run, u) => u.load.talents.map((uid) => R.itemByUid(run, uid).id);

test('every new unit brings one random talent of its class, into the pack: it arrives bare', () => {
  const run = fresh();
  for (const u of run.roster) {
    assert.strictEqual(u.load.talents.length, 0, u.type + ' arrives bare');
    assert.strictEqual(D.TALENTS[u.brought].cls, u.type);
    assert.ok(R.freeItems(run, 'talent').some((i) => i.id === u.brought), 'its talent waits in the pack');
    assert.strictEqual(R.unitCost(run, u), R.bareCost(run, u), 'so it costs its base price');
  }
  const seen = {};
  for (let seed = 1; seed <= 200; seed++) {
    const r = R.newRun({ seed, warband: 'vanguard' });
    const ar = R.addRecruit(r, 'archer');
    const id = ar.brought;
    seen[id] = (seen[id] || 0) + 1;
    assert.ok(R.talentNote(r, ar).includes(D.TALENTS[id].name));
  }
  assert.ok(seen.a_poison && seen.a_ricochet, 'either archer talent can come');
  assert.ok(seen.a_poison > seen.a_ricochet, 'the stronger one less often');
});

test('the talent a unit brought can move to another unit of its class', () => {
  const run = fresh();
  const a = R.addRecruit(run, 'archer');
  const b = R.addRecruit(run, 'archer');
  const k = bare(run, 'knight');
  const uid = R.freeItems(run, 'talent').find((i) => i.id === a.brought).uid;
  assert.ok(R.assignItem(run, a.id, uid));
  const own = R.freeItems(run, 'talent').find((i) => i.id === b.brought);
  if (own) R.assignItem(run, b.id, own.uid);
  assert.ok(!R.assignItem(run, k.id, uid), 'not to a knight');
  R.setLevel(run, b.id, 2);
  const same = R.itemByUid(run, uid).id === talentsOf(run, b)[0];
  assert.strictEqual(R.assignItem(run, b.id, uid), !same, 'to another archer with room, unless it has that talent already');
  if (!same) {
    assert.deepStrictEqual(a.load.talents, [], 'it leaves the first archer');
    assert.strictEqual(b.load.talents.length, 2);
  }
  R.unassignItem(run, uid);
  assert.ok(R.freeItems(run, 'talent').some((i) => i.uid === uid), 'or back to the pack');
});

test('talents are the passives that cost Supply', () => {
  for (const t of Object.values(D.TALENTS)) {
    assert.ok(t.cost > 0 && !t.mod.active, t.name);
    assert.ok(D.UNITS[t.cls].abilities[t.tier].includes(t.id));
  }
  for (const T of Object.values(D.UNITS)) if (T.abilities) for (const tier of [1, 2]) assert.ok(!D.TALENTS[T.abilities[tier][0]], 'the default pick is always free');
  assert.ok(D.TALENTS.k_wall && D.TALENTS.k_riposte && !D.TALENTS.k_bash && !D.TALENTS.k_plate);
});

test('talents are not level picks; they go in their own slots', () => {
  const run = fresh();
  const k = bare(run, 'knight');
  assert.ok(!R.setAbility(run, k.id, 1, 'k_wall'), 'not a level pick');
  assert.ok(R.setAbility(run, k.id, 1, 'k_bash'), 'actives stay free');
  const wall = R.addItem(run, 'talent', 'k_wall');
  assert.ok(R.assignItem(run, k.id, wall.uid));
  assert.strictEqual(R.itemHolder(run, wall.uid), k);
  const u = R.unitStats(run, k);
  assert.ok(u.traits.has('shieldwall'));
  assert.ok(u.acts.some((a) => a.name === 'Shield Bash'), 'and it keeps its ability pick');
  assert.ok(R.costBreakdown(run, k).some((x) => x.label === 'Shield Wall' && x.cost === 2));
});

test('one slot per level, any talent of the class in any slot', () => {
  const run = fresh();
  const k = bare(run, 'knight');
  const [wall, rip, guard] = ['k_wall', 'k_riposte', 'k_bodyguard'].map((id) => R.addItem(run, 'talent', id));
  assert.ok(R.assignItem(run, k.id, rip.uid), 'a stronger talent fits a Level 1 unit too');
  assert.ok(!R.assignItem(run, k.id, wall.uid), 'Level 1: one slot');
  R.setLevel(run, k.id, 2);
  assert.ok(R.assignItem(run, k.id, wall.uid));
  assert.ok(!R.assignItem(run, k.id, guard.uid), 'Level 2: two slots');
  R.setLevel(run, k.id, 3);
  assert.ok(R.assignItem(run, k.id, guard.uid), 'Level 3: three slots');
  const u = R.unitStats(run, k);
  assert.ok(u.traits.has('shieldwall') && u.traits.has('retaliate'));
  R.setLevel(run, k.id, 1);
  assert.strictEqual(k.load.talents.length, 1, 'dropping a level empties the extra slots');
  assert.ok(!R.itemHolder(run, guard.uid), 'and the talent is free again');
});

test('one copy, one unit; no doubling up on one unit', () => {
  const run = fresh();
  const a = bare(run, 'knight');
  const b = bare(run, 'knight');
  const w1 = R.addItem(run, 'talent', 'k_wall');
  const w2 = R.addItem(run, 'talent', 'k_wall');
  R.setLevel(run, a.id, 2);
  assert.ok(R.assignItem(run, a.id, w1.uid));
  assert.ok(!R.assignItem(run, a.id, w2.uid), 'two Shield Walls on one knight');
  assert.ok(R.assignItem(run, b.id, w1.uid), 'taking it moves it');
  assert.deepStrictEqual(a.load.talents, []);
  assert.ok(R.assignItem(run, a.id, w2.uid), 'a second copy serves a second knight');
});

test('class limits', () => {
  const run = fresh();
  const ar = bare(run, 'archer');
  const wall = R.addItem(run, 'talent', 'k_wall');
  assert.ok(!R.assignItem(run, ar.id, wall.uid), 'an archer cannot use a knight talent');
  const spec = R.specFor(run, ar);
  spec.talents = ['k_wall'];
  assert.ok(!R.unitStats(run, spec).traits.has('shieldwall'), 'the engine ignores another class too');
});

test('shops and spoils only offer talents for classes in your army', () => {
  const run = fresh();
  run.roster = run.roster.filter((r) => r.type !== 'cleric');
  const types = new Set(run.roster.map((r) => r.type));
  let shop = 0;
  for (let i = 0; i < 40; i++) {
    for (const it of R.genShop(run, { id: 'n' + i }).filter((x) => x.kind === 'talent')) {
      shop++;
      assert.ok(types.has(D.TALENTS[it.id].cls), 'no talent for a class you do not have: ' + it.id);
    }
  }
  assert.ok(shop > 0);
});

test('saves from before talent slots keep what units had', () => {
  const run = fresh();
  const k = bare(run, 'knight');
  const old = R.addItem(run, 'talent', 'k_riposte');
  run.talents = 1;
  k.load.lv = 2;
  k.load.a1 = 'k_wall';
  k.load.a2 = 'k_riposte';
  k.load.t2 = old.uid;
  delete k.load.talents;
  const before = run.items.filter((i) => i.kind === 'talent').length;
  R.save(run);
  const back = R.load();
  const k2 = back.roster.find((r) => r.id === k.id);
  R.normalizeLoad(back, k2);
  assert.strictEqual(k2.load.a1, 'k_bash');
  assert.strictEqual(k2.load.a2, 'k_plate');
  const ids = k2.load.talents.map((uid) => back.items.find((i) => i.uid === uid).id).sort();
  assert.deepStrictEqual(ids, ['k_riposte', 'k_wall']);
  assert.ok(k2.load.talents.includes(old.uid), 'the copy it held is the one it keeps');
  assert.strictEqual(back.items.filter((i) => i.kind === 'talent').length, before + 1, 'one new item, for Shield Wall');
});

test('every talent improves something its class always has, never an optional ability', () => {
  for (const id in D.TALENTS) {
    const t = D.TALENTS[id];
    const T = D.UNITS[t.cls];
    assert.ok(!t.mod.active, id + ' is not an active');
    // The actives a unit of this class might or might not have picked.
    const optional = [...T.abilities[1], ...T.abilities[2]].map((a) => D.ABILITIES[a].mod.active).filter(Boolean).map((a) => a.name);
    for (const name of optional) assert.ok(!t.desc.includes(name), `${id} (${t.desc}) leans on ${name}, which a ${T.name} may not have`);
    if (t.mod.act) assert.ok(T.act && T.act.kind !== 'none', id + ' changes a main attack the class has');
  }
});

test('every class has at least three talents', () => {
  for (const type of D.RECRUITABLE) {
    const n = Object.values(D.TALENTS).filter((t) => t.cls === type).length;
    assert.ok(n >= 3, `${type} has ${n}`);
  }
});

test('recruits of one class bring different talents until you own them all', () => {
  for (const type of D.RECRUITABLE) {
    const all = Object.values(D.TALENTS).filter((t) => t.cls === type).map((t) => t.id);
    for (let seed = 1; seed <= 20; seed++) {
      const run = R.newRun({ seed, warband: 'vanguard' });
      // Start from no talents of this class at all.
      run.items = run.items.filter((i) => !(i.kind === 'talent' && D.TALENTS[i.id].cls === type));
      const got = [];
      for (let k = 0; k < all.length * 2; k++) got.push(R.addRecruit(run, type).brought);
      assert.deepStrictEqual(got.slice(0, all.length).sort(), all.slice().sort(), `${type} seed ${seed}: the first ${all.length} are all different`);
      assert.deepStrictEqual(got.slice(all.length).sort(), all.slice().sort(), 'then each comes a second time before any comes a third');
    }
  }
});

test('a talent you already own (bought or found) is not what the next recruit brings', () => {
  const run = R.newRun({ seed: 5, warband: 'vanguard' });
  run.items = run.items.filter((i) => !(i.kind === 'talent' && D.TALENTS[i.id].cls === 'cleric'));
  R.addItem(run, 'talent', 'c_bless');
  R.addItem(run, 'talent', 'c_halo');
  assert.strictEqual(R.addRecruit(run, 'cleric').brought, 'c_radiance');
});

console.log(`talents: ${passed} tests passed`);
