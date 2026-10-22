// Rule checks for the battle engine. Run: node tests/engine.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js']);
const E = AG.Engine;

let passed = 0;
const failed = [];
function test(name, fn) {
  try {
    fn();
    passed++;
  } catch (e) {
    console.error('FAIL', name);
    if (!process.env.ALL) throw e;
    failed.push(name + ': ' + e.message.split('\n')[0]);
  }
}

function board(units, opts = {}) {
  const w = opts.w || 9;
  const h = opts.h || 9;
  const terrain = opts.terrain || new Array(w * h).fill(0);
  const s = E.createBattle({ w, h, terrain, units, relics: opts.relics || { P: [], E: [] }, seed: 7, objective: opts.objective, hold: opts.hold, surviveTurns: opts.surviveTurns, loot: opts.loot, waves: opts.waves });
  // Most rule checks start with the player to move; turn order has its own tests.
  if (!opts.enemyFirst) s.side = 'P';
  return s;
}

// Begin, act and finish in one go. `ai` picks the act (0 = main attack).
function act(s, u, target, ai) {
  s.side = u.team;
  s.spent = false;
  u.activated = false;
  u.wait = 0;
  assert.ok(E.beginActivation(s, u.uid), 'can activate ' + u.type);
  const ok = E.performAction(s, u.uid, Object.assign({ ai: ai || 0 }, target));
  assert.ok(ok, 'action allowed for ' + u.type);
  if (s.act) E.finishActivation(s, null);
}

// End turns until it is `side`'s turn again: a full round when it already is.
function until(s, side) {
  do E.endTurn(s);
  while (!s.over && s.side !== side);
}

function place(s, u, x, y) {
  s.occ[E.idx(s, u.x, u.y)] = 0;
  u.x = x;
  u.y = y;
  s.occ[E.idx(s, x, y)] = u.uid;
}

// ------------------------------------------------------------ core rules

test('facing categories', () => {
  const s = board([{ type: 'knight', team: 'E', x: 4, y: 4, facing: 0 }]);
  const k = s.units[0];
  assert.strictEqual(E.dirCategory(4, 3, k), 'front');
  assert.strictEqual(E.dirCategory(5, 4, k), 'side');
  assert.strictEqual(E.dirCategory(3, 4, k), 'side');
  assert.strictEqual(E.dirCategory(4, 5, k), 'back');
  assert.strictEqual(E.dirCategory(5, 3, k), 'front');
  assert.strictEqual(E.dirCategory(5, 5, k), 'side');
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

test('armor stops physical, magic resistance stops magic', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 8 },
    { type: 'pyromancer', team: 'P', x: 5, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
    { type: 'mageknight', team: 'E', x: 6, y: 4, facing: 2 },
    { type: 'golem', team: 'E', x: 2, y: 4, facing: 2 },
  ]);
  const [ar, py, kn, mk, go] = s.units;
  assert.strictEqual(E.calcHit(s, ar, kn, {}).dmg, 10); // 16 * (1 - 0.35)
  assert.strictEqual(E.calcHit(s, py, kn, {}).dmg, 16); // no magic resistance
  assert.strictEqual(E.calcHit(s, py, kn, {}).block, 0); // magic can't be blocked
  assert.strictEqual(E.calcHit(s, py, mk, {}).dmg, 8); // 50% magic resistance
  assert.strictEqual(E.calcHit(s, py, go, {}).dmg, 20); // -25%: a glaring weakness
  assert.strictEqual(E.calcHit(s, ar, go, {}).dmg, 8); // 50% armor
});

test('resistances never pass 50%', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 8, level: 2, a2: 'k_plate', skills: ['warded'], gear: ['silk_mantle'], enchant: 'runeward' },
    { type: 'golem', team: 'P', x: 5, y: 8, gear: ['plate_armor'] },
  ]);
  assert.strictEqual(s.units[0].res, 0.5);
  assert.ok(Math.abs(s.units[0].armor - 0.45) < 1e-9);
  assert.strictEqual(s.units[1].armor, 0.5);
});

test('levels scale stats; abilities need the right class and level', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 0, y: 8, level: 1 },
    { type: 'knight', team: 'P', x: 1, y: 8, level: 2 },
    { type: 'knight', team: 'P', x: 2, y: 8, level: 3 },
    { type: 'knight', team: 'P', x: 3, y: 8, level: 1, a1: 'k_wall', a2: 'k_plate' },
    { type: 'knight', team: 'P', x: 4, y: 8, level: 2, a1: 'a_poison', a2: 'k_plate' },
    { type: 'archer', team: 'P', x: 5, y: 8, level: 3 },
  ]);
  const [k1, k2, k3, kw, kp, ar] = s.units;
  assert.deepStrictEqual([k1.maxHp, k1.pow], [52, 18]);
  assert.deepStrictEqual([k2.maxHp, k2.pow], [62, 21]);
  assert.deepStrictEqual([k3.maxHp, k3.pow], [73, 23]);
  assert.ok(kw.traits.has('shieldwall'));
  assert.strictEqual(kw.armor, 0.35, 'level 2 ability ignored at level 1');
  assert.ok(Math.abs(kp.armor - 0.45) < 1e-9);
  assert.ok(!kp.props.onHit, 'archer ability ignored on a knight');
  assert.strictEqual(ar.act.range[1], 6, 'Deadeye mastery adds range');
  assert.ok(Math.abs(ar.props.dmgMult - 0.2) < 1e-9);
});

test('barrier aura grants magic resistance and immunity', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
    { type: 'barrier', team: 'E', x: 4, y: 2 },
  ]);
  const [py, kn] = s.units;
  assert.strictEqual(E.calcHit(s, py, kn, {}).dmg, 12);
  assert.ok(E.statusImmune(s, kn, 'para'));
  assert.ok(E.statusImmune(s, kn, 'poison'));
});

test('reachable counts and blocking', () => {
  const s = board([{ type: 'knight', team: 'P', x: 4, y: 4 }]);
  assert.strictEqual(E.reachable(s, s.units[0]).size, 25);
  const s2 = board([
    { type: 'knight', team: 'P', x: 4, y: 4 },
    { type: 'knight', team: 'E', x: 4, y: 3 },
    { type: 'knight', team: 'P', x: 5, y: 4 },
  ]);
  const r2 = E.reachable(s2, s2.units[0]);
  assert.ok(!r2.has(E.idx(s2, 4, 3)), 'cannot end on enemy');
  assert.ok(!r2.has(E.idx(s2, 5, 4)), 'cannot end on ally');
  assert.ok(r2.has(E.idx(s2, 6, 4)), 'can pass through ally');
});

test('walls block walking; shadowstep slips through enemies', () => {
  const s = board([
    { type: 'assassin', team: 'P', x: 4, y: 5 },
    { type: 'knight', team: 'E', x: 4, y: 4 },
    { type: 'wall', team: 'E', x: 2, y: 4 },
    { type: 'wall', team: 'E', x: 1, y: 4 },
    { type: 'wall', team: 'E', x: 0, y: 4 },
    { type: 'wall', team: 'E', x: 3, y: 4 },
    { type: 'knight', team: 'P', x: 2, y: 5 },
  ]);
  const as = s.units[0];
  const kn = s.units[6];
  const r = E.reachable(s, as);
  assert.ok(r.has(E.idx(s, 4, 2)), 'shadowstep through the enemy');
  const rk = E.reachable(s, kn);
  assert.ok(!rk.has(E.idx(s, 2, 3)), 'the wall blocks the knight');
});

test('cooldown: Recover 1 means acting every other turn', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'knight', team: 'E', x: 4, y: 3, facing: 2 },
    { type: 'scout', team: 'P', x: 0, y: 8 },
  ]);
  const [p, e, sc] = s.units;
  assert.strictEqual(E.cooldown(p), 2);
  assert.ok(E.beginActivation(s, p.uid));
  assert.ok(E.moveUnit(s, p.uid, 4, 4));
  assert.ok(E.performAction(s, p.uid, { kind: 'unit', uid: e.uid }));
  E.finishActivation(s, 0);
  assert.strictEqual(p.wait, 2);
  assert.ok(!E.canActivate(s, sc), 'one unit a turn');
  E.endTurn(s);
  assert.strictEqual(p.wait, 2, 'it does not tick on the enemy turn');
  E.endTurn(s);
  assert.strictEqual(s.side, 'P');
  assert.strictEqual(p.wait, 1, 'ticks at the start of your turn');
  assert.ok(!E.canActivate(s, p), 'still cooling down on your next turn');
  assert.ok(E.canActivate(s, sc), 'others are free to go');
  until(s, 'P');
  assert.strictEqual(p.wait, 0);
  assert.ok(E.canActivate(s, p), 'ready the turn after');
});

test('Recover 0 acts every turn; a Witch every third', () => {
  const s = board([
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'witch', team: 'P', x: 6, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 7, facing: 2 },
  ]);
  const [sc, wi] = s.units;
  assert.strictEqual(E.cooldown(sc), 1);
  assert.strictEqual(E.cooldown(wi), 3);
  act(s, sc, { kind: 'unit', uid: s.units[2].uid });
  until(s, 'P');
  assert.ok(E.canActivate(s, sc), 'the scout is ready again');
  sc.wait = 0;
  wi.wait = E.cooldown(wi);
  until(s, 'P');
  assert.strictEqual(wi.wait, 2);
  until(s, 'P');
  assert.strictEqual(wi.wait, 1);
  until(s, 'P');
  assert.ok(E.canActivate(s, wi), 'three turns on, the witch is back');
});

test('moving without acting costs half', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 0 },
  ]);
  const p = s.units[0];
  E.beginActivation(s, p.uid);
  E.moveUnit(s, p.uid, 4, 6);
  E.finishActivation(s, 0);
  assert.strictEqual(p.wait, 2, 'Recover 2: half is 1, plus the turn it ticks');
  assert.strictEqual(E.moveCooldown(s.units[1]), 1, 'a Knight can move every turn');
});

test('paralysis costs a turn on top of the cooldown and removes block', () => {
  const s = board([
    { type: 'enchantress', team: 'P', x: 4, y: 7 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
    { type: 'scout', team: 'P', x: 0, y: 8 },
    { type: 'scout', team: 'E', x: 0, y: 0 },
  ]);
  const [en, kn] = s.units;
  kn.wait = 2;
  E.beginActivation(s, en.uid);
  assert.ok(E.performAction(s, en.uid, { kind: 'tile', x: 4, y: 4 }));
  assert.strictEqual(kn.para, 1);
  assert.strictEqual(E.blockChance(s, kn, 'front'), 0);
  assert.strictEqual(E.turnsUntilReady(kn), 2);
  E.finishActivation(s, 0);
  E.endTurn(s);
  assert.strictEqual(s.side, 'E');
  assert.strictEqual(kn.wait, 1, 'the cooldown ticks first');
  assert.ok(!E.canActivate(s, kn));
  until(s, 'E');
  assert.strictEqual(kn.wait, 0);
  assert.strictEqual(kn.para, 1, 'paralysis waits for the cooldown');
  assert.ok(!E.canActivate(s, kn), 'still paralyzed');
  until(s, 'E');
  assert.strictEqual(kn.para, 0);
  assert.ok(E.canActivate(s, kn), 'free again');
});

test('poison ticks, blocks healing; golems and the undead are immune', () => {
  const s = board([
    { type: 'wisp', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'E', x: 4, y: 4 },
    { type: 'golem', team: 'E', x: 5, y: 5 },
    { type: 'skeleton', team: 'E', x: 3, y: 5 },
    { type: 'cleric', team: 'E', x: 3, y: 1 },
  ]);
  const [wi, kn, go, sk, cl] = s.units;
  act(s, wi, { kind: 'self' });
  assert.ok(kn.poison && kn.poison.turns === 3);
  assert.strictEqual(go.poison, null);
  assert.strictEqual(sk.poison, null);
  E.endTurn(s);
  assert.strictEqual(s.side, 'E');
  assert.strictEqual(kn.hp, kn.maxHp - 6, 'ticks at the start of its turn');
  assert.strictEqual(kn.poison.turns, 2);
  const before = kn.hp;
  assert.ok(E.beginActivation(s, cl.uid));
  E.performAction(s, cl.uid, { kind: 'self' });
  assert.strictEqual(kn.hp, before, 'poisoned unit not healed');
});

test('fireball hurts allies but not the caster; Controlled Burn spares them', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'P', x: 4, y: 3 },
    { type: 'archer', team: 'E', x: 4, y: 4 },
    { type: 'pyromancer', team: 'P', x: 0, y: 8, a1: 'p_kindling' },
  ]);
  const [py, kn, ar, py2] = s.units;
  act(s, py, { kind: 'tile', x: 4, y: 4 });
  assert.strictEqual(ar.hp, ar.maxHp - 14); // 16 * (1 - 0.1)
  assert.strictEqual(kn.hp, kn.maxHp - 16);
  assert.strictEqual(py.hp, py.maxHp);
  assert.strictEqual(py2.act.ff, false);
});

test('witch line stops at rocks and walls', () => {
  const terrain = new Array(81).fill(0);
  terrain[2 * 9 + 4] = E.T_ROCK;
  const s = board(
    [
      { type: 'witch', team: 'P', x: 4, y: 6 },
      { type: 'knight', team: 'E', x: 4, y: 4 },
      { type: 'archer', team: 'E', x: 4, y: 1 },
      { type: 'witch', team: 'P', x: 7, y: 6 },
      { type: 'wall', team: 'E', x: 7, y: 4 },
      { type: 'archer', team: 'E', x: 7, y: 3 },
    ],
    { terrain }
  );
  const [wi, kn, ar, w2, wall, ar2] = s.units;
  act(s, wi, { kind: 'dir', d: 0 });
  assert.ok(kn.hp < kn.maxHp);
  assert.strictEqual(ar.hp, ar.maxHp);
  act(s, w2, { kind: 'dir', d: 0 });
  assert.ok(wall.hp < wall.maxHp, 'the wall is struck');
  assert.strictEqual(ar2.hp, ar2.maxHp, 'nothing behind the wall');
});

test('furgon keeps at most three shrubs; Grove Keeper allows four', () => {
  const s = board([
    { type: 'furgon', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'E', x: 4, y: 0 },
    { type: 'archer', team: 'P', x: 0, y: 8 },
  ]);
  const f = s.units[0];
  for (const [x, y] of [[4, 5], [3, 6], [5, 6], [4, 7]]) act(s, f, { kind: 'tile', x, y });
  assert.strictEqual(s.units.filter((u) => u.type === 'shrub' && u.alive).length, 3);
  assert.ok(!E.at(s, 4, 5), 'oldest shrub withered');
  const s2 = board([
    { type: 'furgon', team: 'P', x: 4, y: 6, level: 2, a2: 'f_grove' },
    { type: 'knight', team: 'E', x: 4, y: 0 },
    { type: 'archer', team: 'P', x: 0, y: 8 },
  ]);
  const f2 = s2.units[0];
  for (const [x, y] of [[4, 5], [3, 6], [5, 6], [4, 7]]) act(s2, f2, { kind: 'tile', x, y });
  assert.strictEqual(s2.units.filter((u) => u.type === 'shrub' && u.alive).length, 4);
});

// ------------------------------------------------------------ abilities

test('Shield Bash knocks back, and slams into obstacles', () => {
  const terrain = new Array(81).fill(0);
  terrain[2 * 9 + 6] = E.T_ROCK;
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5, a1: 'k_bash' },
      { type: 'scout', team: 'E', x: 4, y: 4, facing: 0 },
      { type: 'knight', team: 'P', x: 6, y: 4, a1: 'k_bash' },
      { type: 'scout', team: 'E', x: 6, y: 3, facing: 0 },
    ],
    { terrain }
  );
  const [k1, sc1, k2, sc2] = s.units;
  assert.strictEqual(k1.acts[1].name, 'Shield Bash');
  act(s, k1, { kind: 'unit', uid: sc1.uid }, 1);
  assert.deepStrictEqual([sc1.x, sc1.y], [4, 3], 'pushed back');
  assert.strictEqual(sc1.hp, sc1.maxHp - 9);
  act(s, k2, { kind: 'unit', uid: sc2.uid }, 1);
  assert.deepStrictEqual([sc2.x, sc2.y], [6, 3], 'rock in the way');
  assert.strictEqual(sc2.hp, sc2.maxHp - 9 - 6, 'slam damage');
});

test("Snare Shot roots; roots wear off on the victim's turns", () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 6, a1: 'a_snare' },
    { type: 'knight', team: 'E', x: 4, y: 3, facing: 0 },
    { type: 'scout', team: 'P', x: 0, y: 8 },
    { type: 'scout', team: 'E', x: 8, y: 0 },
  ]);
  const [ar, kn] = s.units;
  act(s, ar, { kind: 'unit', uid: kn.uid }, 1);
  assert.strictEqual(kn.hp, kn.maxHp - 6);
  assert.strictEqual(kn.root, 2);
  assert.strictEqual(E.reachable(s, kn).size, 1, 'rooted units cannot move');
  E.endTurn(s);
  assert.strictEqual(kn.root, 2, 'rooted through its next turn');
  until(s, 'E');
  assert.strictEqual(kn.root, 1);
  until(s, 'E');
  assert.strictEqual(kn.root, 0);
  assert.ok(E.reachable(s, kn).size > 1);
});

test("a root that lands during its victim's own turn starts counting on its next one", () => {
  const s = board([
    { type: 'scout', team: 'P', x: 4, y: 7, a1: 's_caltrops' },
    { type: 'knight', team: 'E', x: 4, y: 2, facing: 0 },
    { type: 'scout', team: 'E', x: 8, y: 0 },
  ]);
  const [sc, kn] = s.units;
  act(s, sc, { kind: 'tile', x: 4, y: 5 }, 1);
  E.endTurn(s);
  assert.strictEqual(s.side, 'E');
  assert.ok(E.beginActivation(s, kn.uid));
  assert.ok(E.moveUnit(s, kn.uid, 4, 5));
  assert.strictEqual(kn.root, 1, 'caught in the caltrops');
  E.finishActivation(s, 0);
  E.endTurn(s);
  assert.strictEqual(kn.root, 1, 'the turn it stepped in does not count');
  until(s, 'E');
  assert.strictEqual(E.reachable(s, kn).size, 1, 'stuck on its next turn');
  E.endTurn(s);
  assert.strictEqual(kn.root, 0);
});

test('Poison Arrows poison on hit', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 6, a1: 'a_poison' },
    { type: 'knight', team: 'E', x: 4, y: 3, facing: 0 },
  ]);
  const [ar, kn] = s.units;
  act(s, ar, { kind: 'unit', uid: kn.uid });
  assert.deepStrictEqual([kn.poison.turns, kn.poison.dmg], [2, 5]);
});

test('smoke hides units from attacks more than 1 tile away', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 7, a1: 'a_smoke' },
    { type: 'knight', team: 'P', x: 4, y: 4 },
    { type: 'archer', team: 'E', x: 4, y: 1 },
    { type: 'scout', team: 'E', x: 5, y: 3 },
  ]);
  const [ar, kn, ea, sc] = s.units;
  assert.ok(E.targetsFrom(s, ea, 0).some((t) => t.uid === kn.uid));
  act(s, ar, { kind: 'tile', x: 4, y: 4 }, 1);
  assert.ok(E.tileFx(s, 4, 4, 'smoke'));
  assert.ok(!E.targetsFrom(s, ea, 0).some((t) => t.uid === kn.uid), 'archer cannot see into the smoke');
  place(s, sc, 5, 4);
  assert.ok(E.targetsFrom(s, sc, 0).some((t) => t.uid === kn.uid), 'adjacent attackers still can');
  assert.strictEqual(ar.acts[1].left, 1, 'a charge was spent');
});

test('caltrops stop a walker, hurt it and root it', () => {
  const s = board([
    { type: 'scout', team: 'P', x: 4, y: 7, a1: 's_caltrops' },
    { type: 'knight', team: 'E', x: 4, y: 2 },
  ]);
  const [sc, kn] = s.units;
  act(s, sc, { kind: 'tile', x: 4, y: 5 }, 1);
  s.side = 'P';
  E.endTurn(s);
  const r = E.reachable(s, kn);
  assert.ok(r.has(E.idx(s, 4, 5)), 'can step onto the trap');
  assert.ok(E.beginActivation(s, kn.uid));
  assert.ok(E.moveUnit(s, kn.uid, 4, 5));
  assert.strictEqual(kn.hp, kn.maxHp - 6);
  assert.strictEqual(kn.root, 1);
  assert.ok(!E.tileFx(s, 4, 5, 'caltrops'), 'trap is used up');
  assert.ok(!E.canUndo(s), 'cannot undo a sprung trap');
});

test('wall of fire burns units that enter it and start their turn in it', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 7, a1: 'p_firewall' },
    { type: 'knight', team: 'E', x: 4, y: 2 },
  ]);
  const [py, kn] = s.units;
  act(s, py, { kind: 'tile', x: 4, y: 4 }, 1);
  E.endTurn(s);
  assert.ok(E.beginActivation(s, kn.uid));
  assert.ok(E.moveUnit(s, kn.uid, 4, 4));
  assert.strictEqual(kn.hp, kn.maxHp - 12, 'two burning tiles crossed');
  E.finishActivation(s, 2);
  until(s, 'E');
  assert.strictEqual(kn.hp, kn.maxHp - 18, 'starts its next turn in the fire');
});

test('powder kegs explode and set off their neighbors', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 7 },
    { type: 'barrel', team: 'E', x: 4, y: 4 },
    { type: 'barrel', team: 'E', x: 5, y: 4 },
    { type: 'knight', team: 'E', x: 4, y: 3 },
    { type: 'orc', team: 'E', x: 6, y: 4 },
  ]);
  const [ar, b1, b2, kn, orc] = s.units;
  act(s, ar, { kind: 'unit', uid: b1.uid });
  assert.ok(!b1.alive && !b2.alive, 'chain reaction');
  assert.strictEqual(kn.hp, kn.maxHp - 22);
  assert.strictEqual(orc.hp, orc.maxHp - 22);
});

test('a goblin sapper detonates itself and everyone beside it', () => {
  const s = board([
    { type: 'sapper', team: 'E', x: 4, y: 4 },
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'archer', team: 'P', x: 3, y: 4 },
    { type: 'orc', team: 'E', x: 5, y: 4 },
  ]);
  const [sa, kn, ar, orc] = s.units;
  act(s, sa, { kind: 'self' });
  assert.ok(!sa.alive);
  assert.strictEqual(kn.hp, kn.maxHp - 24);
  assert.strictEqual(ar.hp, ar.maxHp - 22);
  assert.strictEqual(orc.hp, orc.maxHp - 24, 'friendly fire');
  const s2 = board([
    { type: 'archer', team: 'P', x: 4, y: 7 },
    { type: 'sapper', team: 'E', x: 4, y: 4, facing: 0 },
    { type: 'knight', team: 'P', x: 4, y: 3 },
  ]);
  const [a2, sp2, k2] = s2.units;
  sp2.hp = 1;
  act(s2, a2, { kind: 'unit', uid: sp2.uid });
  assert.strictEqual(k2.hp, k2.maxHp - 14, 'a slain sapper still bursts');
});

test('the necromancer raises skeletons that crumble when it dies', () => {
  const s = board([
    { type: 'necromancer', team: 'E', x: 4, y: 2 },
    { type: 'knight', team: 'P', x: 4, y: 7 },
  ]);
  const [ne, kn] = s.units;
  act(s, ne, { kind: 'tile', x: 4, y: 3 }, 1);
  const sk = E.at(s, 4, 3);
  assert.ok(sk && sk.type === 'skeleton' && sk.summoner === ne.uid);
  assert.ok(sk.activated, 'raised this turn: cannot act yet');
  ne.hp = 1;
  ne.facing = 2;
  place(s, kn, 4, 1);
  act(s, kn, { kind: 'unit', uid: ne.uid });
  assert.ok(!ne.alive && !sk.alive, 'its skeletons crumble');
});

test('troll regeneration stops after magic damage', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 7 },
    { type: 'troll', team: 'E', x: 4, y: 4 },
  ]);
  const [py, tr] = s.units;
  tr.hp = 40;
  E.endTurn(s);
  assert.strictEqual(tr.hp, 46, 'regenerates 6 at the start of its turn');
  until(s, 'P');
  act(s, py, { kind: 'tile', x: 4, y: 4 });
  const after = tr.hp;
  E.endTurn(s);
  assert.strictEqual(tr.hp, after, 'scorched: no regeneration');
  until(s, 'E');
  assert.strictEqual(tr.hp, Math.min(tr.maxHp, after + 6));
});

test('loot wagons flee for the exit; breaking them all wins', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 0, y: 8 },
      { type: 'knight', team: 'E', x: 8, y: 0 },
      { type: 'cart', team: 'E', x: 2, y: 4 },
    ],
    { objective: 'destroy' }
  );
  const cart = s.units[2];
  E.endTurn(s);
  E.endTurn(s);
  assert.strictEqual(cart.x, 1, 'one tile after the enemy turn');
  E.endTurn(s);
  E.endTurn(s);
  assert.ok(cart.escaped && !cart.alive, 'escaped off the left edge');
  assert.ok(!s.over, 'the battle goes on: rout them instead');
  const s2 = board(
    [
      { type: 'pyromancer', team: 'P', x: 6, y: 7 },
      { type: 'knight', team: 'E', x: 8, y: 0 },
      { type: 'cart', team: 'E', x: 6, y: 4 },
    ],
    { objective: 'destroy' }
  );
  s2.units[2].hp = 5;
  act(s2, s2.units[0], { kind: 'tile', x: 6, y: 4 });
  assert.ok(s2.over && s2.winner === 'P');
});

test('Divine Shield absorbs damage; charges run out', () => {
  const s = board([
    { type: 'cleric', team: 'P', x: 4, y: 7, level: 2, a1: 'c_mend', a2: 'c_shield' },
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'archer', team: 'E', x: 4, y: 1 },
  ]);
  const [cl, kn, ea] = s.units;
  assert.strictEqual(cl.acts[2].name, 'Divine Shield');
  act(s, cl, { kind: 'unit', uid: kn.uid }, 2);
  assert.strictEqual(kn.shield, 15);
  kn.facing = 0;
  kn.block = 0;
  act(s, ea, { kind: 'unit', uid: kn.uid });
  assert.strictEqual(kn.hp, kn.maxHp, 'fully absorbed');
  assert.strictEqual(kn.shield, 5);
  act(s, cl, { kind: 'unit', uid: kn.uid }, 2);
  assert.ok(!E.actUsable(s, cl, 2), 'no charges left');
});

test('marks and weakness change damage', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 4 },
  ]);
  const [py, kn] = s.units;
  kn.mark = 1;
  assert.strictEqual(E.calcHit(s, py, kn, {}).dmg, 20);
  kn.mark = 0;
  py.weak = 1;
  assert.strictEqual(E.calcHit(s, py, kn, {}).dmg, 11);
});

test('Savage Leap lands next to enemies and cleaves', () => {
  const s = board([
    { type: 'berserker', team: 'P', x: 4, y: 7, level: 2, a1: 'b_rage', a2: 'b_leap' },
    { type: 'scout', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [be, sc] = s.units;
  assert.ok(E.targetsFrom(s, be, 1).some((t) => t.x === 4 && t.y === 5));
  act(s, be, { kind: 'tile', x: 4, y: 5 }, 1);
  assert.deepStrictEqual([be.x, be.y], [4, 5]);
  assert.strictEqual(sc.hp, sc.maxHp - Math.round(be.pow * 0.8 * 0.95));
});

test('Shadow Strike appears behind the target and strikes its back', () => {
  const s = board([
    { type: 'assassin', team: 'P', x: 4, y: 7, level: 2, a2: 'as_shadow' },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
  ]);
  const [as, kn] = s.units;
  act(s, as, { kind: 'unit', uid: kn.uid }, 1);
  assert.deepStrictEqual([as.x, as.y], [4, 3]);
  assert.strictEqual(kn.hp, kn.maxHp - Math.round(as.pow * 1.5 * 0.65));
});

test('Blink replaces walking but still allows an attack', () => {
  const s = board([
    { type: 'mageknight', team: 'P', x: 4, y: 7, level: 2, a2: 'mk_blink' },
    { type: 'scout', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [mk, sc] = s.units;
  assert.ok(E.beginActivation(s, mk.uid));
  assert.ok(E.performAction(s, mk.uid, { kind: 'tile', x: 4, y: 5, ai: 1 }));
  assert.ok(s.act.moved && !s.act.acted);
  assert.ok(!E.moveUnit(s, mk.uid, 3, 5), 'cannot also walk');
  assert.ok(E.performAction(s, mk.uid, { kind: 'unit', uid: sc.uid, ai: 0 }), 'can still attack');
  assert.ok(sc.hp < sc.maxHp);
});

test('Resurrection brings back a fallen ally', () => {
  const s = board([
    { type: 'cleric', team: 'P', x: 4, y: 7, level: 2, a2: 'c_revive' },
    { type: 'archer', team: 'P', x: 4, y: 5 },
    { type: 'knight', team: 'E', x: 0, y: 0 },
  ]);
  const [cl, ar] = s.units;
  ar.alive = false;
  ar.hp = 0;
  s.occ[E.idx(s, 4, 5)] = 0;
  act(s, cl, { kind: 'tile', x: 4, y: 5, uid: ar.uid }, 1);
  assert.ok(ar.alive && ar.hp === Math.ceil(ar.maxHp * 0.4));
  assert.strictEqual(E.at(s, 4, 5), ar);
});

test('Rallying Cry speeds up recovering allies', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 7, level: 2, a2: 'k_rally' },
    { type: 'archer', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'E', x: 0, y: 0 },
  ]);
  const [kn, ar] = s.units;
  ar.wait = 2;
  act(s, kn, { kind: 'self' }, 1);
  assert.strictEqual(ar.wait, 1);
  until(s, 'P');
  assert.ok(E.canActivate(s, ar), 'ready a turn sooner');
});

test('war drums heal and send allies into a frenzy', () => {
  const s = board([
    { type: 'shaman', team: 'E', x: 4, y: 2 },
    { type: 'orc', team: 'E', x: 4, y: 3 },
    { type: 'knight', team: 'P', x: 4, y: 7 },
  ]);
  const [sh, orc, kn] = s.units;
  orc.hp = 20;
  const base = E.calcHit(s, orc, kn, {}).dmg;
  act(s, sh, { kind: 'self' });
  assert.strictEqual(orc.hp, 30);
  assert.strictEqual(orc.frenzy, 2);
  assert.ok(E.calcHit(s, orc, kn, {}).dmg > base);
});

test('gear bonuses: blessed blades, runic mastery and spellward', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5, gear: ['blessed_blade'] },
    { type: 'knight', team: 'P', x: 6, y: 5 },
    { type: 'skeleton', team: 'E', x: 4, y: 4 },
    { type: 'mageknight', team: 'P', x: 2, y: 5, level: 3 },
    { type: 'pyromancer', team: 'P', x: 0, y: 8 },
    { type: 'mageknight', team: 'E', x: 7, y: 2, a1: 'mk_ward' },
    { type: 'knight', team: 'E', x: 7, y: 1 },
    { type: 'knight', team: 'E', x: 1, y: 1 },
  ]);
  const [kb, kp, sk, mk, py, , guarded, open] = s.units;
  assert.strictEqual(E.calcHit(s, kb, sk, {}).dmg, 19);
  assert.strictEqual(E.calcHit(s, kp, sk, {}).dmg, 13);
  assert.strictEqual(mk.props.bonusMagic, 8);
  assert.strictEqual(E.calcHit(s, py, open, {}).dmg, 16);
  assert.strictEqual(E.calcHit(s, py, guarded, {}).dmg, 13, 'spellward softens magic by 20%');
});

test('towers and walls do not need to fall for a rout', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'scout', team: 'E', x: 4, y: 4, facing: 0 },
    { type: 'tower', team: 'E', x: 0, y: 0 },
    { type: 'wall', team: 'E', x: 1, y: 1 },
  ]);
  const [kn, sc] = s.units;
  sc.hp = 1;
  act(s, kn, { kind: 'unit', uid: sc.uid });
  assert.ok(s.over && s.winner === 'P');
});

test('second wind, the phoenix feather and phoenix soul', () => {
  const s = board(
    [
      { type: 'pyromancer', team: 'E', x: 4, y: 2 },
      { type: 'archer', team: 'P', x: 4, y: 5, skills: ['second_wind'] },
      { type: 'scout', team: 'P', x: 0, y: 8, enchant: 'phoenix_soul' },
    ],
    { relics: { P: ['phoenix_feather'], E: [] } }
  );
  const [py, ar, sc] = s.units;
  ar.hp = 3;
  act(s, py, { kind: 'tile', x: 4, y: 5 });
  assert.strictEqual(ar.hp, 1);
  act(s, py, { kind: 'tile', x: 4, y: 5 });
  assert.ok(ar.alive, 'phoenix feather revives');
  assert.strictEqual(ar.hp, Math.ceil(ar.maxHp / 2));
  sc.hp = 1;
  place(s, sc, 2, 2);
  act(s, py, { kind: 'tile', x: 2, y: 2 });
  assert.ok(sc.alive && sc.phoenixUsed, 'phoenix soul revives its own unit');
});

test('stormcaller zaps the nearest enemy each turn', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 6, enchant: 'stormcaller' },
    { type: 'knight', team: 'E', x: 4, y: 4 },
    { type: 'archer', team: 'E', x: 0, y: 0 },
  ]);
  const kn = s.units[1];
  E.endTurn(s);
  assert.strictEqual(kn.hp, kn.maxHp, 'not on the enemy turn');
  E.endTurn(s);
  assert.strictEqual(kn.hp, kn.maxHp - 5, 'at the start of your turn');
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

// ------------------------------------------------------------ outcomes

test('victory when last enemy falls; boss objective', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'scout', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [p, e] = s.units;
  e.hp = 1;
  act(s, p, { kind: 'unit', uid: e.uid });
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
  act(b, b.units[0], { kind: 'unit', uid: king.uid });
  assert.ok(b.over && b.winner === 'P', 'boss slain wins');
});

test('a side with no attackers left surrenders', () => {
  const s = board([
    { type: 'cleric', team: 'P', x: 4, y: 7 },
    { type: 'archer', team: 'P', x: 4, y: 5, facing: 2 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
  ]);
  const [, ar, kn] = s.units;
  ar.hp = 1;
  ar.block = 0;
  act(s, kn, { kind: 'unit', uid: ar.uid });
  assert.ok(s.over && s.winner === 'E' && s.events.some((e) => e.t === 'end' && e.surrender));
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
      { type: 'berserker', team: 'E', x: 4, y: 4, facing: 2, skills: ['retaliate'] },
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
  assert.ok(!E.beginActivation(s, kn.uid), 'its turn was spent');
  E.endTurn(s);
  assert.strictEqual(s.side, 'E');
  assert.ok(!s.events.some((e) => e.t === 'pass'), 'a turn, not a pass');
});

test('burning the war banner wins; it rallies nearby enemies', () => {
  const s = board(
    [
      { type: 'pyromancer', team: 'P', x: 4, y: 6 },
      { type: 'knight', team: 'E', x: 0, y: 0 },
      { type: 'archer', team: 'E', x: 4, y: 1 },
      { type: 'warbanner', team: 'E', x: 4, y: 3 },
    ],
    { objective: 'destroy' }
  );
  const [py, kn, ar, wb] = s.units;
  assert.ok(wb.nonCombat && wb.facing === -1);
  assert.ok(E.nearBanner(s, ar) && !E.nearBanner(s, kn));
  assert.strictEqual(E.calcHit(s, ar, py, {}).dmg, Math.round(16 * 1.15));
  wb.hp = 5;
  act(s, py, { kind: 'tile', x: 4, y: 3 });
  assert.ok(s.over && s.winner === 'P', 'banner destroyed wins');
});

test('slaying the commander wins', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'archer', team: 'E', x: 4, y: 4, facing: 0, vip: true },
      { type: 'knight', team: 'E', x: 0, y: 0 },
    ],
    { objective: 'vip' }
  );
  const [kn, cmd] = s.units;
  cmd.hp = 1;
  act(s, kn, { kind: 'unit', uid: cmd.uid });
  assert.ok(s.over && s.winner === 'P');
});

test('holding the shrine for two turns wins', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 4 },
      { type: 'knight', team: 'E', x: 0, y: 0 },
    ],
    { objective: 'hold', hold: { x: 4, y: 4, need: 2 } }
  );
  E.endTurn(s);
  E.endTurn(s);
  assert.strictEqual(s.hold.count, 1);
  assert.ok(!s.over);
  E.endTurn(s);
  E.endTurn(s);
  assert.ok(s.over && s.winner === 'P');
});

test('surviving the set number of turns wins', () => {
  const s = board(
    [
      { type: 'scout', team: 'P', x: 0, y: 8 },
      { type: 'golem', team: 'E', x: 8, y: 0 },
    ],
    { objective: 'survive', surviveTurns: 2 }
  );
  for (let i = 0; i < 4 && !s.over; i++) E.endTurn(s);
  assert.ok(s.over && s.winner === 'P' && s.turn === 3);
});

test('taking loot uses the action and needs the unit on the tile', () => {
  const s = board(
    [
      { type: 'archer', team: 'P', x: 4, y: 7 },
      { type: 'knight', team: 'E', x: 0, y: 0 },
    ],
    { loot: [{ id: 'l1', kind: 'tome', x: 4, y: 5 }] }
  );
  const ar = s.units[0];
  assert.ok(!E.canLoot(s, ar));
  E.beginActivation(s, ar.uid);
  assert.ok(!E.takeLoot(s, ar.uid), 'not on the loot yet');
  E.moveUnit(s, ar.uid, 4, 5);
  assert.ok(E.canLoot(s, ar));
  assert.ok(E.takeLoot(s, ar.uid));
  assert.ok(s.loot[0].taken && s.loot[0].by === ar.uid);
  E.finishActivation(s, 0);
  assert.strictEqual(ar.wait, E.cooldown(ar), 'looting counts as an action');
});

test('specters: steel barely scratches them, magic hurts them more, and they drain life', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'specter', team: 'E', x: 4, y: 4 },
  ]);
  const [kn, py, sp] = s.units;
  assert.strictEqual(E.calcHit(s, kn, sp, {}).dmg, 9);
  assert.strictEqual(E.calcHit(s, py, sp, {}).dmg, 20);
  sp.hp = 10;
  kn.block = 0;
  act(s, sp, { kind: 'unit', uid: kn.uid });
  assert.ok(sp.hp > 10, 'drained life');
});

// ------------------------------------------------------------ buildings and reinforcements

test('siege damage: hammers, Demolisher, the Trebuchet and the Sapper Kit hit buildings harder', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'knight', team: 'P', x: 3, y: 4, gear: ['siege_hammer'] },
    { type: 'knight', team: 'P', x: 5, y: 4, skills: ['demolisher'] },
    { type: 'trebuchet', team: 'P', x: 4, y: 8 },
    { type: 'totem', team: 'E', x: 4, y: 4 },
    { type: 'knight', team: 'E', x: 0, y: 0 },
  ]);
  const [plain, hammer, demo, treb, totem, foe] = s.units;
  assert.strictEqual(E.calcHit(s, plain, totem, {}).dmg, 9, 'stone halves a sword');
  assert.strictEqual(E.calcHit(s, hammer, totem, {}).dmg, 27, 'Siege Hammer triples it');
  assert.strictEqual(E.calcHit(s, demo, totem, {}).dmg, 18, 'Demolisher doubles it');
  assert.strictEqual(E.calcHit(s, treb, totem, {}).dmg, 19, 'Trebuchet: +150% to buildings');
  assert.strictEqual(E.calcHit(s, treb, foe, {}).dmg, 10, 'but no bonus against units');
  const k = board([{ type: 'knight', team: 'P', x: 4, y: 5 }, { type: 'totem', team: 'E', x: 4, y: 4 }], { relics: { P: ['sappers_kit'], E: [] } });
  assert.strictEqual(E.calcHit(k, k.units[0], k.units[1], {}).dmg, 14, "Sapper's Kit: +50%");
});

test('the Trebuchet cannot hit anything closer than 3 tiles', () => {
  const s = board([
    { type: 'trebuchet', team: 'P', x: 4, y: 8 },
    { type: 'orc', team: 'E', x: 4, y: 6 },
    { type: 'orc', team: 'E', x: 2, y: 6 },
  ]);
  const [treb, near, far] = s.units;
  const t = E.allTargets(s, treb).filter((x) => x.ai === 0);
  assert.ok(!t.some((x) => x.uid === near.uid), 'two tiles away is too close');
  assert.ok(t.some((x) => x.uid === far.uid), 'four tiles away is fine');
});

test('materials: wood burns, stone resists, portals unravel under magic', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'P', x: 0, y: 8 },
    { type: 'war_tent', team: 'E', x: 4, y: 4 },
    { type: 'crypt', team: 'E', x: 2, y: 4 },
    { type: 'portal', team: 'E', x: 6, y: 4 },
  ]);
  const [py, kn, tent, crypt, portal] = s.units;
  assert.strictEqual(E.calcHit(s, py, tent, {}).dmg, 20);
  assert.strictEqual(E.calcHit(s, py, crypt, {}).dmg, 11);
  assert.strictEqual(E.calcHit(s, py, portal, {}).dmg, 24);
  assert.strictEqual(E.calcHit(s, kn, portal, {}).dmg, 9);
});

test('totems heal nearby allies at the start of their turn, but not poisoned ones', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 8 },
    { type: 'totem', team: 'E', x: 4, y: 2 },
    { type: 'orc', team: 'E', x: 4, y: 4 },
    { type: 'orc', team: 'E', x: 4, y: 5 },
    { type: 'orc', team: 'E', x: 3, y: 2 },
  ]);
  const [, , near, far, sick] = s.units;
  for (const o of [near, far, sick]) o.hp = 20;
  sick.poison = { turns: 3, dmg: 2, src: 0 };
  E.endTurn(s);
  assert.strictEqual(near.hp, 24, 'within 2 tiles: +4');
  assert.strictEqual(far.hp, 20, '3 tiles away: nothing');
  assert.strictEqual(sick.hp, 18, 'poison blocks healing');
  assert.ok(s.events.some((e) => e.t === 'totem'));
});

function tentBattle(extra, opts) {
  const units = [{ type: 'knight', team: 'P', x: 4, y: 8 }, { type: 'war_tent', team: 'E', x: 4, y: 1, key: 't1' }].concat(extra || []);
  return board(units, Object.assign({ waves: [{ turn: 2, from: 't1', units: [{ type: 'orc' }] }, { turn: 4, from: 't1', units: [{ type: 'orc' }] }] }, opts));
}

test("waves are marked a turn ahead and arrive after the enemy's move", () => {
  const s = tentBattle();
  const w = s.waves[0];
  const kn = s.units[0];
  assert.strictEqual(s.turn, 1);
  assert.deepStrictEqual(w.marks, [[4, 2]], 'marked on your turn before it lands; the doorway faces your side');
  assert.strictEqual(s.waves[1].marks, null, 'later waves are not marked yet');
  assert.strictEqual(E.pendingWaves(s, 'E'), 2);
  assert.ok(E.beginActivation(s, kn.uid));
  assert.ok(E.moveUnit(s, kn.uid, 4, 6));
  E.finishActivation(s, 0);
  E.endTurn(s);
  const orc = s.units.find((u) => u.type === 'orc');
  assert.ok(orc && orc.x === 4 && orc.y === 2, 'arrived on its mark after the enemy turn');
  assert.strictEqual(w.state, 'done');
  assert.ok(!s.over, 'more waves are coming');
  assert.strictEqual(s.side, 'P');
  assert.strictEqual(s.turn, 2);
  assert.strictEqual(s.waves[1].marks, null, 'turn 4 is still two enemy turns off');
  until(s, 'P');
  assert.ok(s.waves[1].marks, 'marked a turn ahead');
});

test('standing on a mark blocks the arrival and costs the blocker HP', () => {
  const s = tentBattle();
  const kn = s.units[0];
  place(s, kn, 4, 2);
  E.endTurn(s);
  assert.ok(!s.units.some((u) => u.type === 'orc'), 'blocked');
  assert.strictEqual(kn.hp, kn.maxHp - E.BLOCK_DMG);
  assert.ok(s.events.some((e) => e.t === 'spawnBlock' && e.uid === kn.uid));
});

test('breaking the building cancels its waves; a rout needs no waves left', () => {
  const s = tentBattle([{ type: 'goblin_archer', team: 'E', x: 0, y: 0 }], { objective: 'all' });
  const [kn, tent, gob] = s.units;
  place(s, kn, 1, 0);
  gob.hp = 1;
  gob.block = 0;
  act(s, kn, { kind: 'unit', uid: gob.uid });
  assert.ok(!gob.alive);
  assert.ok(!s.over, 'waves still on the way');
  place(s, kn, 3, 1);
  tent.hp = 1;
  act(s, kn, { kind: 'unit', uid: tent.uid });
  assert.ok(!tent.alive);
  assert.ok(s.waves.every((w) => w.state === 'cancelled'));
  assert.ok(s.events.some((e) => e.t === 'waveCancel' && e.n === 2));
  assert.ok(s.over && s.winner === 'P', 'routed');
});

test('raze: breaking every goal building wins; optional buildings do not need to fall', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 3 },
    { type: 'war_tent', team: 'E', x: 4, y: 2, key: 'a' },
    { type: 'guardhouse', team: 'E', x: 0, y: 0, key: 'b', goal: false },
    { type: 'orc', team: 'E', x: 8, y: 0 },
  ], { objective: 'destroy', waves: [{ turn: 2, from: 'b', units: [{ type: 'orc' }] }] });
  const [kn, tent, house] = s.units;
  assert.ok(tent.goal && !house.goal);
  tent.hp = 1;
  act(s, kn, { kind: 'unit', uid: tent.uid });
  assert.ok(s.over && s.winner === 'P', 'the guardhouse and the orc did not matter');
});

test('edge waves appear along their edge', () => {
  const s = board([{ type: 'knight', team: 'P', x: 4, y: 8 }, { type: 'orc', team: 'E', x: 8, y: 0 }], {
    objective: 'survive', surviveTurns: 4,
    waves: [{ turn: 2, tiles: [[0, 0], [1, 0], [2, 0], [3, 0]], units: [{ type: 'orc' }, { type: 'goblin_archer', level: 2 }] }],
  });
  E.endTurn(s);
  E.endTurn(s);
  const fresh = s.units.filter((u) => u.born === 2);
  assert.strictEqual(fresh.length, 2);
  assert.ok(fresh.every((u) => u.y === 0 && u.x <= 3 && u.team === 'E'));
  assert.strictEqual(fresh.find((u) => u.type === 'goblin_archer').level, 2);
});

// ------------------------------------------------------------ taking turns

function duel(extra) {
  return board(
    [
      { type: 'knight', team: 'P', x: 3, y: 7 },
      { type: 'scout', team: 'P', x: 5, y: 7 },
      { type: 'knight', team: 'E', x: 3, y: 1 },
      { type: 'scout', team: 'E', x: 5, y: 1 },
    ].concat(extra || []),
    { enemyFirst: true }
  );
}

function step(s, uid, x, y) {
  assert.ok(E.beginActivation(s, uid), 'can activate');
  assert.ok(E.moveUnit(s, uid, x, y), 'can move');
  E.finishActivation(s, 2);
  E.endTurn(s);
}

test('the enemy opens; each turn one unit goes, then the other side picks one', () => {
  const s = duel();
  const [pk, ps, ek, es] = s.units;
  assert.strictEqual(s.side, 'E');
  assert.ok(!E.canActivate(s, pk), 'not your turn yet');
  assert.ok(E.beginActivation(s, ek.uid));
  assert.ok(E.moveUnit(s, ek.uid, 3, 2));
  assert.ok(!E.beginActivation(s, es.uid), 'one unit a turn');
  E.finishActivation(s, 2);
  assert.ok(!E.canActivate(s, es), 'still one unit a turn');
  E.endTurn(s);
  assert.strictEqual(s.side, 'P', 'your turn');
  assert.strictEqual(s.turn, 1);
  step(s, pk.uid, 3, 6);
  assert.strictEqual(s.side, 'E');
  assert.strictEqual(s.turn, 2, 'the next turn opens with the enemy');
  assert.ok(E.canActivate(s, ek), 'it only moved: ready again');
  step(s, es.uid, 5, 2);
  step(s, ps.uid, 5, 6);
  assert.strictEqual(s.turn, 3);
});

test('a side with nobody ready passes on its own', () => {
  const s = duel();
  const [pk, ps, ek] = s.units;
  pk.wait = 2;
  ps.wait = 2;
  step(s, ek.uid, 3, 2);
  assert.strictEqual(s.side, 'E', 'you had nothing ready, so the enemy goes again');
  assert.strictEqual(s.turn, 2);
  assert.ok(s.events.some((e) => e.t === 'pass' && e.side === 'P' && e.auto));
  assert.strictEqual(pk.wait, 1, 'your cooldowns still ticked');
  E.endTurn(s);
  assert.strictEqual(s.side, 'P');
  assert.ok(E.canActivate(s, pk), 'ready on your next turn');
});

test('passing hands the turn over and costs nothing', () => {
  const s = duel();
  const [, , ek] = s.units;
  E.pass(s);
  assert.strictEqual(s.side, 'P');
  assert.strictEqual(s.turn, 1);
  assert.ok(s.events.some((e) => e.t === 'pass' && e.side === 'E' && !e.auto));
  E.pass(s);
  assert.strictEqual(s.side, 'E');
  assert.strictEqual(s.turn, 2);
  assert.ok(ek.wait === 0 && E.canActivate(s, ek), 'passing costs nothing');
});

test('timed statuses count the turns of the side they matter to', () => {
  const s = duel();
  const [pk, , , es] = s.units;
  // On the enemy's turn, your knight is rooted for 2 turns.
  pk.root = 2;
  pk.fresh = { root: s.ply };
  E.pass(s);
  assert.strictEqual(pk.root, 2, 'the enemy turn does not count');
  // On your turn, their scout is marked for 2 turns.
  es.mark = 2;
  es.fresh = { mark: s.ply };
  E.pass(s);
  assert.strictEqual(pk.root, 1, 'your turn counted for the root');
  assert.strictEqual(es.mark, 2, 'the mark counts from your next turn');
  E.pass(s);
  assert.strictEqual(es.mark, 2, 'their turn does not count for the mark');
  E.pass(s);
  assert.strictEqual(pk.root, 0);
  assert.strictEqual(es.mark, 1, 'your turn counted for the mark');
});

test('when nobody can act, turns pass on their own and statuses still tick', () => {
  const s = duel();
  for (const u of s.units) u.wait = 3;
  s.units[0].root = 2;
  E.endTurn(s);
  assert.strictEqual(s.side, 'P');
  assert.strictEqual(s.turn, 3, 'two rounds went by with nobody able to act');
  assert.strictEqual(s.units[0].root, 0, 'the root still wore off');
  assert.ok(s.units.filter((u) => u.team === 'P').every((u) => u.wait === 0));
  assert.ok(s.events.filter((e) => e.t === 'pass' && e.auto).length >= 3);
});

test('sands of haste: enemy casters sit out their first turn', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'witch', team: 'E', x: 4, y: 0 },
      { type: 'knight', team: 'E', x: 2, y: 0 },
    ],
    { relics: { P: ['sands_of_haste'], E: [] }, enemyFirst: true }
  );
  const [, wi, kn] = s.units;
  assert.strictEqual(s.side, 'E');
  assert.ok(!E.canActivate(s, wi), 'the witch sits out');
  assert.ok(E.canActivate(s, kn));
  until(s, 'E');
  assert.ok(E.canActivate(s, wi), 'free on the next enemy turn');
});

console.log(`engine: ${passed} tests passed`);
if (failed.length) {
  console.log(failed.join('\n'));
  process.exit(1);
}
