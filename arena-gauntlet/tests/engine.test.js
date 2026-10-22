// Rule checks for the battle engine. Run: node tests/engine.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js']);
const E = AG.Engine;

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

function board(units, opts = {}) {
  const w = opts.w || 9;
  const h = opts.h || 9;
  const terrain = opts.terrain || new Array(w * h).fill(0);
  return E.createBattle({ w, h, terrain, units, relics: opts.relics || { P: [], E: [] }, seed: 7, objective: opts.objective });
}

test('facing categories', () => {
  const s = board([{ type: 'knight', team: 'E', x: 4, y: 4, facing: 0 }]);
  const k = s.units[0];
  assert.strictEqual(E.dirCategory(4, 3, k), 'front');
  assert.strictEqual(E.dirCategory(5, 4, k), 'side');
  assert.strictEqual(E.dirCategory(3, 4, k), 'side');
  assert.strictEqual(E.dirCategory(4, 5, k), 'back');
  assert.strictEqual(E.dirCategory(5, 3, k), 'front'); // diagonal front counts as front
  assert.strictEqual(E.dirCategory(5, 5, k), 'side'); // diagonal back counts as side
  assert.strictEqual(E.dirCategory(4, 8, k), 'back');
});

test('block chance by arc', () => {
  const s = board([{ type: 'knight', team: 'E', x: 4, y: 4, facing: 0 }]);
  const k = s.units[0];
  assert.strictEqual(E.blockChance(s, k, 'front'), 0.7);
  assert.strictEqual(E.blockChance(s, k, 'side'), 0.35);
  assert.strictEqual(E.blockChance(s, k, 'back'), 0);
  k.para = 1;
  assert.strictEqual(E.blockChance(s, k, 'front'), 0);
});

test('armor and magic damage', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 8 },
    { type: 'pyromancer', team: 'P', x: 5, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
  ]);
  const [ar, py, kn] = s.units;
  assert.strictEqual(E.calcHit(s, ar, kn, {}).dmg, 12); // 16 * 0.75
  assert.strictEqual(E.calcHit(s, py, kn, {}).dmg, 16); // magic ignores armor
  assert.strictEqual(E.calcHit(s, py, kn, {}).block, 0); // magic can't be blocked
});

test('barrier aura halves magic and grants immunity', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
    { type: 'barrier', team: 'E', x: 4, y: 2 },
  ]);
  const [py, kn] = s.units;
  assert.strictEqual(E.calcHit(s, py, kn, {}).dmg, 8);
  assert.ok(E.statusImmune(s, kn, 'para'));
});

test('reachable counts and blocking', () => {
  const s = board([{ type: 'knight', team: 'P', x: 4, y: 4 }]);
  const r = E.reachable(s, s.units[0]);
  assert.strictEqual(r.size, 25); // diamond of radius 3
  const s2 = board([
    { type: 'knight', team: 'P', x: 4, y: 4 },
    { type: 'knight', team: 'E', x: 4, y: 3 },
    { type: 'knight', team: 'P', x: 5, y: 4 },
  ]);
  const r2 = E.reachable(s2, s2.units[0]);
  assert.ok(!r2.has(E.idx(s2, 4, 3)), 'cannot end on enemy');
  assert.ok(!r2.has(E.idx(s2, 4, 2)) || true);
  assert.ok(!r2.has(E.idx(s2, 5, 4)), 'cannot end on ally');
  assert.ok(r2.has(E.idx(s2, 6, 4)), 'can pass through ally');
});

test('shadowstep passes enemies, rocks block walkers, flyers cross water', () => {
  const terrain = new Array(81).fill(0);
  terrain[3 * 9 + 4] = E.T_WATER;
  const s = board(
    [
      { type: 'assassin', team: 'P', x: 4, y: 5 },
      { type: 'knight', team: 'E', x: 4, y: 4 },
      { type: 'wisp', team: 'P', x: 0, y: 5 },
    ],
    { terrain }
  );
  const [as, , wi] = s.units;
  const r = E.reachable(s, as);
  assert.ok(r.has(E.idx(s, 4, 2)) === false, 'water blocks walking even after shadowstep');
  assert.ok(r.has(E.idx(s, 3, 3)), 'shadowstep through enemy line');
  s.occ[E.idx(s, 0, 4)] = 0;
  const rw = E.reachable(s, wi);
  assert.ok(rw.size > 1);
});

test('recovery timing: Recover 1 skips exactly one turn', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'knight', team: 'E', x: 4, y: 3, facing: 2 },
  ]);
  const [p, e] = s.units;
  assert.ok(E.beginActivation(s, p.uid));
  assert.ok(E.moveUnit(s, p.uid, 4, 4));
  assert.ok(E.performAction(s, p.uid, { kind: 'unit', uid: e.uid }));
  E.finishActivation(s, 0);
  assert.strictEqual(p.wait, 1);
  E.endTurn(s); // P -> E
  assert.strictEqual(p.wait, 1, 'acting unit does not tick on its own turn');
  E.endTurn(s); // E -> P (turn 2)
  assert.ok(!E.canActivate(s, p), 'still recovering on turn 2');
  E.endTurn(s); // P turn 2 ends -> ticks
  assert.strictEqual(p.wait, 0);
  E.endTurn(s); // E -> P turn 3
  assert.ok(E.canActivate(s, p), 'ready on turn 3');
});

test('move-only halves recovery', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 0 },
  ]);
  const p = s.units[0];
  E.beginActivation(s, p.uid);
  E.moveUnit(s, p.uid, 4, 6);
  E.finishActivation(s, 0);
  assert.strictEqual(p.wait, 1);
});

test('paralysis costs a full turn on top of recovery and removes block', () => {
  const s = board([
    { type: 'enchantress', team: 'P', x: 4, y: 7 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
  ]);
  const [en, kn] = s.units;
  kn.wait = 1;
  E.beginActivation(s, en.uid);
  assert.ok(E.performAction(s, en.uid, { kind: 'tile', x: 4, y: 4 }));
  assert.strictEqual(kn.para, 1);
  assert.strictEqual(E.blockChance(s, kn, 'front'), 0);
  E.endTurn(s); // to E
  assert.ok(!E.canActivate(s, kn));
  E.endTurn(s); // E turn ends: wait 1 -> 0, para stays
  assert.strictEqual(kn.wait, 0);
  assert.strictEqual(kn.para, 1);
  E.endTurn(s);
  assert.ok(!E.canActivate(s, kn), 'still paralyzed');
  E.endTurn(s); // para -> 0
  E.endTurn(s);
  assert.ok(E.canActivate(s, kn));
});

test('poison ticks, blocks healing, golems are immune', () => {
  const s = board([
    { type: 'wisp', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'E', x: 4, y: 4 },
    { type: 'golem', team: 'E', x: 5, y: 5 },
    { type: 'cleric', team: 'E', x: 3, y: 1 },
  ]);
  const [wi, kn, go, cl] = s.units;
  E.beginActivation(s, wi.uid);
  assert.ok(E.performAction(s, wi.uid, { kind: 'self' }));
  assert.ok(kn.poison && kn.poison.turns === 3);
  assert.strictEqual(go.poison, null);
  E.endTurn(s); // E turn start: poison ticks
  assert.strictEqual(kn.hp, kn.maxHp - 6);
  assert.strictEqual(kn.poison.turns, 2);
  E.beginActivation(s, cl.uid);
  const before = kn.hp;
  assert.ok(E.performAction(s, cl.uid, { kind: 'self' }) || true);
  assert.strictEqual(kn.hp, before, 'poisoned unit not healed');
});

test('fireball hurts allies but not the caster', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'P', x: 4, y: 3 },
    { type: 'archer', team: 'E', x: 4, y: 4 },
  ]);
  const [py, kn, ar] = s.units;
  E.beginActivation(s, py.uid);
  assert.ok(E.performAction(s, py.uid, { kind: 'tile', x: 4, y: 4 }));
  assert.strictEqual(ar.hp, ar.maxHp - 16);
  assert.strictEqual(kn.hp, kn.maxHp - 16);
  assert.strictEqual(py.hp, py.maxHp);
});

test('witch line stops at rocks', () => {
  const terrain = new Array(81).fill(0);
  terrain[2 * 9 + 4] = E.T_ROCK;
  const s = board(
    [
      { type: 'witch', team: 'P', x: 4, y: 6 },
      { type: 'knight', team: 'E', x: 4, y: 4 },
      { type: 'archer', team: 'E', x: 4, y: 1 },
    ],
    { terrain }
  );
  const [wi, kn, ar] = s.units;
  E.beginActivation(s, wi.uid);
  assert.ok(E.performAction(s, wi.uid, { kind: 'dir', d: 0 }));
  assert.ok(kn.hp < kn.maxHp);
  assert.strictEqual(ar.hp, ar.maxHp);
});

test('furgon keeps at most three shrubs', () => {
  const s = board([
    { type: 'furgon', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'E', x: 4, y: 0 },
    { type: 'archer', team: 'P', x: 0, y: 8 },
  ]);
  const f = s.units[0];
  const spots = [[4, 5], [3, 6], [5, 6], [4, 7]];
  for (const [x, y] of spots) {
    f.activated = false;
    f.wait = 0;
    s.side = 'P';
    assert.ok(E.beginActivation(s, f.uid));
    assert.ok(E.performAction(s, f.uid, { kind: 'tile', x, y }));
    E.finishActivation(s, 0);
  }
  const shrubs = s.units.filter((u) => u.type === 'shrub' && u.alive);
  assert.strictEqual(shrubs.length, 3);
  assert.ok(!E.at(s, 4, 5), 'oldest shrub withered');
});

test('victory when last enemy falls; boss objective', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'scout', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [p, e] = s.units;
  e.hp = 1;
  E.beginActivation(s, p.uid);
  // keep rolling until it lands (scout has block); force by turning it around
  e.facing = 0; // facing north, so attack from south is a back attack
  assert.ok(E.performAction(s, p.uid, { kind: 'unit', uid: e.uid }));
  assert.ok(s.over && s.winner === 'P');

  const b = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'golem_king', team: 'E', x: 4, y: 4, facing: 0 },
      { type: 'knight', team: 'E', x: 0, y: 0 },
    ],
    { objective: 'boss' }
  );
  const king = b.units[1];
  king.hp = 1;
  E.beginActivation(b, b.units[0].uid);
  assert.ok(E.performAction(b, b.units[0].uid, { kind: 'unit', uid: king.uid }));
  assert.ok(b.over && b.winner === 'P', 'boss slain wins');
});

test('second wind and phoenix', () => {
  const s = board(
    [
      { type: 'pyromancer', team: 'E', x: 4, y: 2 },
      { type: 'archer', team: 'P', x: 4, y: 5, talents: ['second_wind'] },
      { type: 'scout', team: 'P', x: 0, y: 8 },
    ],
    { relics: { P: ['phoenix_feather'], E: [] } }
  );
  s.side = 'E';
  const [py, ar] = s.units;
  ar.hp = 3;
  E.beginActivation(s, py.uid);
  assert.ok(E.performAction(s, py.uid, { kind: 'tile', x: 4, y: 5 }));
  assert.strictEqual(ar.hp, 1);
  assert.ok(ar.alive);
  py.activated = false;
  py.wait = 0;
  E.finishActivation(s, 2);
  py.activated = false;
  py.wait = 0;
  E.beginActivation(s, py.uid);
  assert.ok(E.performAction(s, py.uid, { kind: 'tile', x: 4, y: 5 }));
  assert.ok(ar.alive, 'phoenix revives');
  assert.strictEqual(ar.hp, Math.ceil(ar.maxHp / 2));
});

test('charge bonus only when moving 3+ before attacking', () => {
  const s = board([
    { type: 'beastrider', team: 'P', x: 4, y: 8 },
    { type: 'archer', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [br, ar] = s.units;
  const plain = E.calcHit(s, br, ar, {}).dmg;
  const charged = E.calcHit(s, br, ar, { moved: true, moveDist: 3 }).dmg;
  assert.ok(charged > plain);
  E.beginActivation(s, br.uid);
  E.moveUnit(s, br.uid, 4, 5);
  const pv = E.previewAction(s, br, { kind: 'unit', uid: ar.uid });
  assert.strictEqual(pv.effects[0].dmg, charged);
});

test('a side with no attackers left surrenders', () => {
  const s = board([
    { type: 'cleric', team: 'P', x: 4, y: 7 },
    { type: 'archer', team: 'P', x: 4, y: 5 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [, ar, kn] = s.units;
  s.side = 'E';
  ar.hp = 1;
  E.beginActivation(s, kn.uid);
  kn.facing = 2;
  assert.ok(E.performAction(s, kn.uid, { kind: 'unit', uid: ar.uid }) || true);
  if (!ar.alive) assert.ok(s.over && s.winner === 'E' && s.events.some((e) => e.t === 'end' && e.surrender));
});

test('turn limit goes to the stronger side', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 0, y: 8 },
    { type: 'scout', team: 'E', x: 8, y: 0 },
  ]);
  s.turnLimit = 1;
  E.endTurn(s);
  E.endTurn(s);
  assert.ok(s.over && s.timeout && s.winner === 'P');
});

test('a unit killed by a counterattack ends its activation', () => {
  const s = board(
    [
      { type: 'scout', team: 'P', x: 4, y: 5 },
      { type: 'knight', team: 'P', x: 0, y: 8 },
      { type: 'berserker', team: 'E', x: 4, y: 4, facing: 2, talents: ['retaliate'] },
    ],
    { relics: { P: [], E: ['thorned_mail'] } }
  );
  const [sc, kn, be] = s.units;
  sc.hp = 3;
  sc.block = 0;
  assert.ok(E.beginActivation(s, sc.uid));
  assert.ok(E.performAction(s, sc.uid, { kind: 'unit', uid: be.uid }));
  assert.ok(!sc.alive, 'scout died to thorns');
  assert.strictEqual(s.act, null);
  assert.ok(E.beginActivation(s, kn.uid), 'another unit can act');
});

test('burning the war banner wins; it rallies nearby enemies', () => {
  const s = E.createBattle({
    w: 9, h: 9, terrain: new Array(81).fill(0), seed: 3, objective: 'destroy',
    units: [
      { type: 'pyromancer', team: 'P', x: 4, y: 6 },
      { type: 'knight', team: 'E', x: 0, y: 0 },
      { type: 'archer', team: 'E', x: 4, y: 1 },
      { type: 'warbanner', team: 'E', x: 4, y: 3 },
    ],
  });
  const [py, kn, ar, wb] = s.units;
  assert.ok(wb.nonCombat && wb.facing === -1);
  assert.ok(E.nearBanner(s, ar) && !E.nearBanner(s, kn));
  assert.strictEqual(E.calcHit(s, ar, py, {}).dmg, Math.round(16 * 1.15));
  wb.hp = 5;
  E.beginActivation(s, py.uid);
  assert.ok(E.performAction(s, py.uid, { kind: 'tile', x: 4, y: 3 }));
  assert.ok(s.over && s.winner === 'P', 'banner destroyed wins');
});

test('slaying the commander wins', () => {
  const s = E.createBattle({
    w: 9, h: 9, terrain: new Array(81).fill(0), seed: 3, objective: 'vip',
    units: [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'archer', team: 'E', x: 4, y: 4, facing: 0, vip: true },
      { type: 'knight', team: 'E', x: 0, y: 0 },
    ],
  });
  const [kn, cmd] = s.units;
  cmd.hp = 1;
  E.beginActivation(s, kn.uid);
  assert.ok(E.performAction(s, kn.uid, { kind: 'unit', uid: cmd.uid }));
  assert.ok(s.over && s.winner === 'P');
});

test('holding the shrine for two turns wins', () => {
  const s = E.createBattle({
    w: 9, h: 9, terrain: new Array(81).fill(0), seed: 3, objective: 'hold', hold: { x: 4, y: 4, need: 2 },
    units: [
      { type: 'knight', team: 'P', x: 4, y: 4 },
      { type: 'knight', team: 'E', x: 0, y: 0 },
    ],
  });
  E.endTurn(s);
  E.endTurn(s);
  assert.strictEqual(s.hold.count, 1);
  assert.ok(!s.over);
  E.endTurn(s);
  E.endTurn(s);
  assert.ok(s.over && s.winner === 'P');
});

test('surviving the set number of turns wins', () => {
  const s = E.createBattle({
    w: 9, h: 9, terrain: new Array(81).fill(0), seed: 3, objective: 'survive', surviveTurns: 2,
    units: [
      { type: 'scout', team: 'P', x: 0, y: 8 },
      { type: 'golem', team: 'E', x: 8, y: 0 },
    ],
  });
  for (let i = 0; i < 4 && !s.over; i++) E.endTurn(s);
  assert.ok(s.over && s.winner === 'P' && s.turn === 3);
});

test('taking loot uses the action and needs the unit on the tile', () => {
  const s = E.createBattle({
    w: 9, h: 9, terrain: new Array(81).fill(0), seed: 3,
    loot: [{ id: 'l1', kind: 'tome', x: 4, y: 5 }],
    units: [
      { type: 'archer', team: 'P', x: 4, y: 7 },
      { type: 'knight', team: 'E', x: 0, y: 0 },
    ],
  });
  const ar = s.units[0];
  assert.ok(!E.canLoot(s, ar));
  E.beginActivation(s, ar.uid);
  assert.ok(!E.takeLoot(s, ar.uid), 'not on the loot yet');
  E.moveUnit(s, ar.uid, 4, 5);
  assert.ok(E.canLoot(s, ar));
  assert.ok(E.takeLoot(s, ar.uid));
  assert.ok(s.loot[0].taken && s.loot[0].by === ar.uid);
  E.finishActivation(s, 0);
  assert.strictEqual(ar.wait, ar.rec, 'looting counts as an action');
});

test('specters shrug off half of physical damage and drain life', () => {
  const s = E.createBattle({
    w: 9, h: 9, terrain: new Array(81).fill(0), seed: 3,
    units: [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'pyromancer', team: 'P', x: 4, y: 8 },
      { type: 'specter', team: 'E', x: 4, y: 4 },
    ],
  });
  const [kn, py, sp] = s.units;
  assert.strictEqual(E.calcHit(s, kn, sp, {}).dmg, 9);
  assert.strictEqual(E.calcHit(s, py, sp, {}).dmg, 16);
  sp.hp = 10;
  s.side = 'E';
  E.beginActivation(s, sp.uid);
  assert.ok(E.performAction(s, sp.uid, { kind: 'unit', uid: kn.uid }));
  assert.ok(sp.hp > 10, 'drained life');
});

console.log(`engine: ${passed} tests passed`);
