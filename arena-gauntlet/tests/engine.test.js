// Rule checks for the battle engine. Run: node tests/engine.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js']);
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

// A mission done routs the enemy instead of ending the battle: their fatigue sets in at
// once (1, 2, 3...) until the last falls, and the win is yours.
function routedThenWon(s, why) {
  assert.ok(s.routed && s.routed[why], 'routed: ' + why);
  assert.ok(!s.over, 'the battle goes on');
  const foe = s.units.find((u) => u.alive && u.team === 'E' && E.counts(u));
  const hp = foe && foe.hp;
  for (let i = 0; i < 80 && !s.over; i++) E.endTurn(s);
  assert.ok(!foe || foe.hp < hp, 'the routed enemy bleeds');
  assert.ok(s.over && s.winner === 'P', 'and the last of them falls');
  assert.ok(s.end[why], 'the win remembers why');
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

test('no Level 3 mastery shortens a cooldown', () => {
  for (const [cls, m] of Object.entries(AG.Data.MASTERY)) assert.ok(!(m.mod.stat && m.mod.stat.rec), cls);
  const s = board([
    { type: 'cleric', team: 'P', x: 0, y: 8, level: 2 },
    { type: 'cleric', team: 'P', x: 1, y: 8, level: 3 },
    { type: 'dragon', team: 'P', x: 3, y: 8, level: 2 },
    { type: 'dragon', team: 'P', x: 6, y: 8, level: 3 },
  ]);
  const [c2, c3, d2, d3] = s.units;
  assert.strictEqual(c3.rec, c2.rec, 'the Cleric still waits as long');
  assert.strictEqual(d3.rec, d2.rec, 'and so does the Dragon');
  assert.ok(E.healAmount(c3) >= 1.5 * E.healAmount(c2), 'Devotion: prayer heals 50% more');
  assert.ok(c3.maxHp > c2.maxHp + 10 && d3.maxHp > d2.maxHp + 20);
  assert.ok(Math.abs(d3.props.dmgMult - 0.25) < 1e-9, 'Wyrmlord: +25% damage');
});

test('barrier aura grants armor, magic resistance and immunity', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
    { type: 'barrier', team: 'E', x: 4, y: 2 },
  ]);
  const [py, kn] = s.units;
  assert.strictEqual(E.calcHit(s, py, kn, {}).dmg, 12);
  assert.strictEqual(+E.effArmor(s, kn).toFixed(2), +Math.min(AG.Data.RES_CAP, kn.armor + 0.25).toFixed(2), '+25% armor');
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

test('cooldown: a Knight (CD 1) sits out one turn after attacking', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'knight', team: 'E', x: 4, y: 3, facing: 2 },
    { type: 'scout', team: 'P', x: 0, y: 8 },
  ]);
  const [p, e, sc] = s.units;
  assert.strictEqual(E.cooldown(p), 1);
  assert.ok(E.beginActivation(s, p.uid));
  assert.ok(E.moveUnit(s, p.uid, 4, 4));
  assert.ok(E.performAction(s, p.uid, { kind: 'unit', uid: e.uid }));
  E.finishActivation(s, 0);
  assert.strictEqual(p.wait, 1);
  assert.ok(!E.canActivate(s, sc), 'one unit a turn');
  E.endTurn(s);
  assert.strictEqual(p.wait, 1, 'the turn it attacked in does not count');
  E.endTurn(s);
  assert.strictEqual(s.side, 'P');
  assert.strictEqual(p.wait, 1, 'still there at the start of your next turn');
  assert.ok(!E.canActivate(s, p), 'so it sits that turn out');
  assert.ok(E.canActivate(s, sc), 'others are free to go');
  until(s, 'P');
  assert.strictEqual(p.wait, 0, 'it ran out at the end of the turn it sat out');
  assert.ok(E.canActivate(s, p), 'ready the turn after');
});

test('a Scout (CD 0) acts every turn; a Witch (CD 2) every third', () => {
  const s = board([
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'witch', team: 'P', x: 6, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 7, facing: 2 },
    { type: 'knight', team: 'E', x: 6, y: 6, facing: 2 },
  ]);
  const [sc, wi] = s.units;
  assert.strictEqual(E.cooldown(sc), 0);
  assert.strictEqual(E.cooldown(wi), 2);
  act(s, sc, { kind: 'unit', uid: s.units[2].uid });
  assert.strictEqual(sc.wait, 0);
  until(s, 'P');
  assert.ok(E.canActivate(s, sc), 'the scout is ready again');
  act(s, wi, { kind: 'dir', d: 0 });
  assert.strictEqual(wi.wait, 2);
  until(s, 'P');
  assert.ok(!E.canActivate(s, wi), 'the witch sits out one turn');
  assert.strictEqual(wi.wait, 2);
  until(s, 'P');
  assert.ok(!E.canActivate(s, wi), 'and a second');
  assert.strictEqual(wi.wait, 1);
  until(s, 'P');
  assert.ok(E.canActivate(s, wi), 'three turns on, the witch is back');
});

test('moving alone never starts a cooldown', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 0 },
  ]);
  const p = s.units[0];
  assert.strictEqual(E.cooldown(p), 2);
  E.beginActivation(s, p.uid);
  E.moveUnit(s, p.uid, 4, 6);
  E.finishActivation(s, 0);
  assert.strictEqual(p.wait, 0, 'it only moved');
  until(s, 'P');
  assert.ok(E.canActivate(s, p), 'free to go again on your next turn');
});

test('cooldown exceptions: Bloodlust kills, Eternal Flame and bosses', () => {
  const s = board([
    { type: 'berserker', team: 'P', x: 4, y: 3, level: 2, a2: 'b_bloodlust' },
    { type: 'scout', team: 'E', x: 4, y: 4, facing: 2 },
    { type: 'knight', team: 'E', x: 0, y: 0 },
  ]);
  const [b, sc] = s.units;
  sc.hp = 1;
  act(s, b, { kind: 'unit', uid: sc.uid });
  assert.ok(!sc.alive);
  assert.strictEqual(b.wait, 0, 'the kill reset its cooldown');
  until(s, 'P');
  assert.ok(E.canActivate(s, b), 'ready again on your next turn');

  const f = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'knight', team: 'E', x: 4, y: 4, facing: 0 },
    ],
    { relics: { P: ['eternal_flame'], E: [] } }
  );
  const [k, ek] = f.units;
  act(f, k, { kind: 'unit', uid: ek.uid });
  assert.strictEqual(k.wait, 0, 'Eternal Flame: the first action is free');
  until(f, 'P');
  act(f, k, { kind: 'unit', uid: ek.uid });
  assert.strictEqual(k.wait, 1, 'the second one is not');

  const g = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'golem_king', team: 'E', x: 4, y: 0 },
      { type: 'knight', team: 'E', x: 2, y: 0 },
    ],
    { enemyFirst: true }
  );
  const boss = g.units[1];
  assert.ok(!E.canActivate(g, boss), "a boss sits out its side's first turn");
  until(g, 'E');
  assert.ok(E.canActivate(g, boss), 'and joins in on the second');
});

test('paralysis costs a turn on top of the cooldown and removes block', () => {
  const s = board([
    { type: 'enchantress', team: 'P', x: 4, y: 7 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
    { type: 'scout', team: 'P', x: 0, y: 8 },
    { type: 'scout', team: 'E', x: 0, y: 0 },
  ]);
  const [en, kn] = s.units;
  // It attacked on its last turn, so it sits out its next one.
  kn.wait = 1;
  E.beginActivation(s, en.uid);
  assert.ok(E.performAction(s, en.uid, { kind: 'tile', x: 4, y: 4 }));
  assert.strictEqual(kn.para, 1);
  assert.strictEqual(E.blockChance(s, kn, 'front'), 0);
  assert.strictEqual(E.turnsUntilReady(kn), 2);
  E.finishActivation(s, 0);
  E.endTurn(s);
  assert.strictEqual(s.side, 'E');
  assert.strictEqual(kn.wait, 1, 'the cooldown runs first');
  assert.ok(!E.canActivate(s, kn));
  until(s, 'E');
  assert.strictEqual(kn.wait, 0);
  assert.strictEqual(kn.para, 1, 'paralysis waits for the cooldown');
  assert.ok(!E.canActivate(s, kn), 'still paralyzed');
  until(s, 'E');
  assert.strictEqual(kn.para, 0);
  assert.ok(E.canActivate(s, kn), 'free again');
});

test('Miasma poisons for 2 turns, blocks healing; buildings, constructs and the undead are immune', () => {
  const s = board([
    { type: 'wisp', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'E', x: 4, y: 4 },
    { type: 'golem', team: 'E', x: 5, y: 5 },
    { type: 'skeleton', team: 'E', x: 3, y: 5 },
    { type: 'cleric', team: 'E', x: 3, y: 1 },
    { type: 'lightning', team: 'E', x: 2, y: 6 },
    { type: 'cage', team: 'E', x: 4, y: 8 },
  ]);
  const [wi, kn, go, sk, cl, lw, cage] = s.units;
  act(s, wi, { kind: 'self' });
  assert.ok(kn.poison && kn.poison.turns === 2);
  for (const u of [go, sk, lw, cage]) assert.ok(!u.poison, u.type + ' is immune');
  E.endTurn(s);
  assert.strictEqual(s.side, 'E');
  assert.strictEqual(kn.hp, kn.maxHp - 8, 'ticks at the start of its turn');
  assert.strictEqual(kn.poison.turns, 1);
  const before = kn.hp;
  assert.ok(E.beginActivation(s, cl.uid));
  E.performAction(s, cl.uid, { kind: 'self' });
  assert.strictEqual(kn.hp, before, 'poisoned unit not healed');
});

test('Lingering Spores: 3 turns; Pestilence never hits buildings', () => {
  const s = board([
    { type: 'wisp', team: 'P', x: 4, y: 6, level: 3, a2: 'w_linger' },
    { type: 'knight', team: 'E', x: 4, y: 4 },
    { type: 'cage', team: 'E', x: 4, y: 8 },
  ]);
  const [wi, kn, cage] = s.units;
  act(s, wi, { kind: 'self' });
  assert.strictEqual(kn.poison.turns, 3);
  assert.ok(kn.hp < kn.maxHp, 'Pestilence hits the knight');
  assert.strictEqual(cage.hp, cage.maxHp, 'but not the cage');
});

test('friendly fire: a cleave hits an adjacent ally; Disciplined spares it', () => {
  const s = board([
    { type: 'berserker', team: 'P', x: 4, y: 5 },
    { type: 'knight', team: 'P', x: 3, y: 5 },
    { type: 'archer', team: 'E', x: 4, y: 4 },
    { type: 'berserker', team: 'P', x: 7, y: 5, skills: ['disciplined'] },
    { type: 'knight', team: 'P', x: 6, y: 5 },
    { type: 'archer', team: 'E', x: 7, y: 4 },
  ]);
  const [be, kn, ar, be2, kn2, ar2] = s.units;
  for (const u of s.units) u.block = 0;
  act(s, be, { kind: 'unit', uid: ar.uid });
  assert.ok(ar.hp < ar.maxHp && kn.hp < kn.maxHp, 'the foe and the ally beside it both take the cleave');
  act(s, be2, { kind: 'unit', uid: ar2.uid });
  assert.ok(ar2.hp < ar2.maxHp, 'the foe is hit');
  assert.strictEqual(kn2.hp, kn2.maxHp, 'Disciplined: the ally is spared');
});

test('friendly fire: an Arrow Volley hits allies in its area', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 8, level: 2, a2: 'a_volley' },
    { type: 'knight', team: 'P', x: 4, y: 4 },
    { type: 'orc', team: 'E', x: 4, y: 3 },
  ]);
  const [ar, kn, orc] = s.units;
  for (const u of s.units) u.block = 0;
  const vi = ar.acts.findIndex((a) => a.name === 'Arrow Volley');
  act(s, ar, { kind: 'tile', x: 4, y: 3 }, vi);
  assert.ok(orc.hp < orc.maxHp && kn.hp < kn.maxHp);
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

test('two poisoners stack their poisons; hitting again only refreshes its own', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 6, a1: 'a_poison' },
    { type: 'assassin', team: 'P', x: 5, y: 3, a1: 'as_poison' },
    { type: 'knight', team: 'E', x: 4, y: 3, facing: 0 },
  ]);
  const [ar, as, kn] = s.units;
  kn.hp = kn.maxHp = 500;
  kn.block = 0; // no blocks: both hits land
  act(s, ar, { kind: 'unit', uid: kn.uid });
  act(s, as, { kind: 'unit', uid: kn.uid });
  assert.strictEqual(kn.poison.stacks.length, 2);
  assert.strictEqual(kn.poison.dmg, 5 + 6, 'Poison Arrows 5 + Poisoned Dagger 6');
  for (const u of [ar, as]) {
    u.activated = false;
    for (const a of u.acts) a.cdLeft = 0;
  }
  act(s, ar, { kind: 'unit', uid: kn.uid });
  assert.strictEqual(kn.poison.stacks.length, 2, 'the archer again: still two');
  assert.strictEqual(kn.poison.dmg, 11);
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

test('trollblood regeneration stops after magic damage', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 7 },
    { type: 'troll', team: 'E', x: 4, y: 4 },
  ]);
  const [py, tr] = s.units;
  // Bog Trolls no longer regenerate (enemies barely heal); the mechanic stays for anything that does.
  tr.traits.add('trollblood');
  tr.regen = 5;
  tr.hp = 40;
  E.endTurn(s);
  assert.strictEqual(tr.hp, 45, 'regenerates 5 at the start of its turn');
  until(s, 'P');
  act(s, py, { kind: 'tile', x: 4, y: 4 });
  const after = tr.hp;
  E.endTurn(s);
  assert.strictEqual(tr.hp, after, 'scorched: no regeneration');
  until(s, 'E');
  assert.strictEqual(tr.hp, Math.min(tr.maxHp, after + 5));
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
  routedThenWon(s2, 'destroyed');
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
  assert.ok(!E.actUsable(s, cl, 2), 'cooling down');
  cl.acts[2].cdLeft = 0;
  act(s, cl, { kind: 'unit', uid: kn.uid }, 2);
  cl.acts[2].cdLeft = 0;
  assert.ok(!E.actUsable(s, cl, 2), 'no charges left');
});

test("an active's own cooldown counts the unit's turns; uses never come back", () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 7, level: 2, a2: 'a_volley' },
    { type: 'knight', team: 'P', x: 0, y: 8 },
    { type: 'knight', team: 'E', x: 4, y: 3 },
  ]);
  const [ar] = s.units;
  const vol = ar.acts.find((a) => a.name === 'Arrow Volley');
  const vi = ar.acts.indexOf(vol);
  assert.deepStrictEqual([vol.uses, vol.cd], [3, 4]);
  act(s, ar, { kind: 'tile', x: 4, y: 3 }, vi);
  assert.strictEqual(vol.left, 2);
  let waited = 0;
  while (!E.actUsable(s, ar, vi)) {
    until(s, 'P');
    ar.wait = 0;
    waited++;
    assert.ok(waited < 10);
  }
  assert.strictEqual(waited, 5, 'usable on its 5th turn after: it waited 4');
  assert.ok(E.actUsable(s, ar, 0), 'the plain attack was free all along');
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

test('Blink is the turn\'s action: it replaces the attack', () => {
  const s = board([
    { type: 'mageknight', team: 'P', x: 4, y: 7, level: 2, a2: 'mk_blink' },
    { type: 'scout', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [mk, sc] = s.units;
  assert.ok(E.beginActivation(s, mk.uid));
  assert.ok(E.performAction(s, mk.uid, { kind: 'tile', x: 4, y: 5, ai: 1 }));
  assert.ok(s.act.acted, 'blinking is its action');
  assert.ok(!E.performAction(s, mk.uid, { kind: 'unit', uid: sc.uid, ai: 0 }), 'no attack after it');
  assert.strictEqual(sc.hp, sc.maxHp);
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

test('a Lightning Ward sprays one side at a time, like a shotgun: the row of three in front, then one tile', () => {
  const s = board([
    { type: 'lightning', team: 'P', x: 4, y: 5 },
    { type: 'orc', team: 'E', x: 3, y: 4 },
    { type: 'orc', team: 'E', x: 4, y: 4 },
    { type: 'orc', team: 'E', x: 5, y: 4 },
    { type: 'orc', team: 'E', x: 4, y: 3 },
    { type: 'orc', team: 'E', x: 3, y: 3 },
    { type: 'orc', team: 'E', x: 7, y: 5 },
  ]);
  const [lw, l1, m1, r1, tip, offTip, east] = s.units;
  assert.deepStrictEqual(E.coneTiles(s, 4, 5, E.dirFromDelta(0, -1), 2, true).map((t) => t.join(',')).sort(), ['3,4', '4,3', '4,4', '5,4']);
  const dirs = E.targetsFrom(s, lw, 0);
  assert.ok(dirs.every((t) => t.kind === 'dir'), 'it aims a direction, not a ring');
  const north = dirs.find((t) => t.d === E.dirFromDelta(0, -1));
  act(s, lw, north);
  for (const o of [l1, m1, r1, tip]) assert.ok(o.hp < o.maxHp, 'the row of three and the tip: hit');
  assert.strictEqual(offTip.hp, offTip.maxHp, 'beside the tip: out of the spray');
  assert.strictEqual(east.hp, east.maxHp, 'it sprayed north, not east');
});

test('war drums send allies into a frenzy, but heal no one', () => {
  const s = board([
    { type: 'shaman', team: 'E', x: 4, y: 2 },
    { type: 'orc', team: 'E', x: 4, y: 3 },
    { type: 'knight', team: 'P', x: 4, y: 7 },
  ]);
  const [sh, orc, kn] = s.units;
  orc.hp = 20;
  const base = E.calcHit(s, orc, kn, {}).dmg;
  act(s, sh, { kind: 'self' });
  assert.strictEqual(orc.hp, 20, 'enemies barely ever heal');
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
  routedThenWon(b, 'vipSlain');
});

test('nobody surrenders: a side with no attackers left fights on until it falls', () => {
  const s = board([
    { type: 'cleric', team: 'P', x: 4, y: 7 },
    { type: 'archer', team: 'P', x: 4, y: 5, facing: 2 },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
  ]);
  const [cl, ar, kn] = s.units;
  ar.hp = 1;
  ar.block = 0;
  act(s, kn, { kind: 'unit', uid: ar.uid });
  assert.ok(!ar.alive && cl.alive);
  assert.ok(!s.over, 'the Cleric is still standing, so the battle goes on');
});

test('with nobody able to hurt anyone, fatigue decides it', () => {
  const s = E.createBattle({
    w: 9, h: 9, terrain: new Array(81).fill(0), seed: 3, queue: true, overtime: 4, turnLimit: 250,
    units: [
      { type: 'furgon', team: 'P', x: 1, y: 8 },
      { type: 'barrier', team: 'P', x: 0, y: 8 },
      { type: 'cleric', team: 'E', x: 7, y: 0 },
    ],
    relics: { P: [], E: [] },
  });
  for (let i = 0; i < 4000 && !s.over; i++) {
    AG.AI.playTurn(s, s.side, { stance: 'balanced', temp: 0 });
    s.events.length = 0;
  }
  assert.ok(s.over && !s.timeout, 'fatigue wears one side down before the turn limit');
  assert.ok(s.turn < 60, 'and soon: turn ' + s.turn);
  assert.ok(s.units.filter((u) => u.team !== s.winner).every((u) => !u.alive), 'the loser has nobody left');
});

test('shrubs are summons: no fatigue, and they do not keep a side in the fight', () => {
  for (const [foe, overtime] of [['knight', 30], ['cleric', 3]]) {
    const s = E.createBattle({
      w: 9, h: 9, terrain: new Array(81).fill(0), seed: 1, queue: true, overtime, turnLimit: 250,
      units: [
        { type: 'furgon', team: 'P', x: 4, y: 8 },
        { type: 'shrub', team: 'P', x: 3, y: 7 },
        { type: 'shrub', team: 'P', x: 5, y: 7 },
        { type: 'shrub', team: 'P', x: 4, y: 6 },
        { type: foe, team: 'E', x: 4, y: 0 },
      ],
      relics: { P: [], E: [] },
    });
    let tired = 0;
    for (let i = 0; i < 4000 && !s.over; i++) {
      AG.AI.playTurn(s, s.side, { stance: 'balanced', temp: 0 });
      for (const e of s.events) if (e.t === 'dmg' && e.dmgType === 'fatigue' && s.byId[e.uid].type === 'shrub') tired++;
      s.events.length = 0;
    }
    assert.ok(s.over && !s.timeout, foe);
    assert.strictEqual(tired, 0, 'fatigue never hits a shrub');
    const furgon = s.units.find((u) => u.type === 'furgon');
    if (!furgon.alive) assert.strictEqual(s.winner, 'E', 'the Furgon down: the battle is over, shrubs or not');
  }
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

test('Face: a facing picked mid-turn holds when the turn ends; dropping the unit undoes it', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 6, facing: 0 },
    { type: 'knight', team: 'E', x: 4, y: 3, facing: 2 },
    { type: 'scout', team: 'P', x: 0, y: 8, facing: 0 },
  ]);
  const [k, e, sc] = s.units;
  assert.ok(E.beginActivation(s, sc.uid));
  assert.ok(E.turnUnit(s, sc.uid, 1));
  assert.strictEqual(sc.facing, 1);
  assert.ok(E.beginActivation(s, k.uid), 'you can still switch to another unit');
  assert.strictEqual(sc.facing, 0, 'the scout turned back: no free turn');
  assert.ok(E.turnUnit(s, k.uid, 3));
  assert.ok(E.moveUnit(s, k.uid, 4, 4));
  assert.ok(E.undoMove(s));
  assert.strictEqual(k.facing, 3, 'undoing the move keeps the pick');
  assert.ok(E.moveUnit(s, k.uid, 4, 4));
  assert.ok(E.performAction(s, k.uid, { kind: 'unit', uid: e.uid }));
  assert.strictEqual(k.facing, 0, 'it turns to strike');
  E.finishActivation(s, null);
  assert.strictEqual(k.facing, 3, 'and to the pick when it is done');
  assert.strictEqual(k.wait, 1);
  // Turning in place is a turn of its own, with no cooldown.
  until(s, 'P');
  assert.ok(E.beginActivation(s, sc.uid));
  assert.ok(E.turnUnit(s, sc.uid, 2));
  E.finishActivation(s, null);
  assert.strictEqual(sc.facing, 2);
  assert.strictEqual(sc.wait, 0);
  assert.ok(s.spent, 'it used the turn');
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
  routedThenWon(s, 'destroyed');
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
  routedThenWon(s, 'vipSlain');
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
  routedThenWon(s, 'held');
});

test('surviving the set number of turns wins', () => {
  const s = board(
    [
      { type: 'scout', team: 'P', x: 0, y: 8 },
      { type: 'golem', team: 'E', x: 8, y: 0 },
    ],
    { objective: 'survive', surviveTurns: 2 }
  );
  for (let i = 0; i < 4 && !s.routed; i++) E.endTurn(s);
  assert.strictEqual(s.routed && s.routed.turn, 3);
  routedThenWon(s, 'survived');
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

test('specters: steel barely scratches them, magic hurts them more, and their touch weakens instead of healing them', () => {
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
  assert.strictEqual(sp.hp, 10, 'no life drained');
  assert.ok(kn.weak > 0, 'the knight is weakened');
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

test('war totems whip nearby allies into a frenzy at the start of their turn, and heal nobody', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 8 },
    { type: 'totem', team: 'E', x: 4, y: 2 },
    { type: 'orc', team: 'E', x: 4, y: 4 },
    { type: 'orc', team: 'E', x: 4, y: 5 },
  ]);
  const [, , near, far] = s.units;
  for (const o of [near, far]) o.hp = 20;
  E.endTurn(s);
  assert.ok(near.frenzy > 0, 'within 2 tiles: in a frenzy');
  assert.strictEqual(far.frenzy, 0, '3 tiles away: nothing');
  assert.strictEqual(near.hp, 20, 'no healing');
  assert.ok(s.events.some((e) => e.t === 'totem'));
  assert.ok(!s.events.some((e) => e.t === 'heal'));
  // Kept up turn after turn, it is announced only the once.
  const said = () => s.events.filter((e) => e.t === 'status' && e.status === 'frenzy' && e.uid === near.uid).length;
  for (let i = 0; i < 6; i++) E.endTurn(s);
  assert.ok(near.frenzy > 0, 'still in a frenzy');
  assert.strictEqual(said(), 1, 'FRENZY shown once, not every turn');
});

test('regular enemies never heal: Orc Shaman drums only rouse, a Specter weakens instead of draining, a Bog Troll does not regenerate', () => {
  const D = AG.Data;
  assert.ok(D.UNITS.shaman.act.noHeal);
  assert.ok(!D.UNITS.specter.props || !D.UNITS.specter.props.lifesteal);
  assert.ok(!D.UNITS.troll.props || !D.UNITS.troll.props.regen);
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 6 },
    { type: 'shaman', team: 'E', x: 4, y: 3 },
    { type: 'orc', team: 'E', x: 4, y: 4 },
  ]);
  const [kn, sh, orc] = s.units;
  orc.hp = 20;
  const pv = E.previewAction(s, sh, { kind: 'self', x: sh.x, y: sh.y }, {});
  assert.ok(pv.effects.every((e) => !e.heal), 'the drums heal no one');
  assert.ok(kn);
});

function tentBattle(extra, opts) {
  const units = [{ type: 'knight', team: 'P', x: 4, y: 8 }, { type: 'war_tent', team: 'E', x: 4, y: 1, key: 't1' }].concat(extra || []);
  return board(units, Object.assign({ waves: [{ turn: 2, from: 't1', units: [{ type: 'orc' }] }, { turn: 4, from: 't1', units: [{ type: 'orc' }] }] }, opts));
}

test('reinforcements are marked as such, and cutting them down counts for the Ambush goal', () => {
  const s = tentBattle();
  const kn = s.units[0];
  for (let g = 0; g < 12 && !s.units.some((u) => u.reinforcement); g++) E.endTurn(s);
  const arrived = s.units.find((u) => u.reinforcement);
  assert.ok(arrived && arrived.team === 'E', 'a wave unit landed, tagged');
  assert.ok(!kn.reinforcement, 'the army a battle starts with is not');
  assert.strictEqual(s.stats.waveKills, 0);
  // The knight steps up beside it and cuts it down.
  s.occ[E.idx(s, kn.x, kn.y)] = 0;
  kn.x = arrived.x;
  kn.y = arrived.y + 1;
  s.occ[E.idx(s, kn.x, kn.y)] = kn.uid;
  kn.facing = 2;
  arrived.hp = 1;
  arrived.block = 0;
  act(s, kn, { kind: 'unit', uid: arrived.uid });
  assert.ok(!arrived.alive);
  assert.strictEqual(s.stats.waveKills, 1);
});

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
  assert.ok(s.waves.every((w) => w.state !== 'pending'), 'its reinforcements stop');
  routedThenWon(s, 'destroyed');
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
  pk.wait = 1;
  ps.wait = 1;
  step(s, ek.uid, 3, 2);
  assert.strictEqual(s.side, 'E', 'you had nothing ready, so the enemy goes again');
  assert.strictEqual(s.turn, 2);
  assert.ok(s.events.some((e) => e.t === 'pass' && e.side === 'P' && e.auto));
  assert.strictEqual(pk.wait, 0, 'the skipped turn still counted for your cooldowns');
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
  for (const u of s.units) u.wait = u.team === 'P' ? 2 : 3;
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

test('a barricade broken by your army spills its gold; the AI breaks one when nothing better is in reach', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'barricade', team: 'E', x: 4, y: 4, bounty: 16 },
    { type: 'barricade', team: 'E', x: 7, y: 2, bounty: 16 },
    { type: 'knight', team: 'E', x: 0, y: 0 },
  ]);
  const [kn, b1, b2, foe] = s.units;
  assert.strictEqual(b1.bounty, 16);
  b1.hp = 1;
  act(s, kn, { kind: 'unit', uid: b1.uid });
  assert.ok(!b1.alive);
  assert.strictEqual(s.stats.bounty, 16);
  assert.ok(s.events.some((e) => e.t === 'gold' && e.coins && e.amount === 16));
  // Only your army's blows pay: the other barricade still stands, its gold unclaimed.
  assert.ok(b2.alive && foe.alive && s.stats.bounty === 16);

  // The AI: a barricade in reach, the enemy far off. It breaks it.
  const t = board([
    { type: 'knight', team: 'P', x: 4, y: 7 },
    { type: 'barricade', team: 'E', x: 4, y: 6, bounty: 16 },
    { type: 'golem', team: 'E', x: 0, y: 0 },
  ]);
  const bar = t.units[1];
  for (let i = 0; i < 4 && bar.alive; i++) {
    t.side = 'P';
    t.spent = false;
    t.units[0].wait = 0;
    t.units[0].activated = false;
    AG.AI.playTurn(t, 'P', { stance: 'balanced', temp: 0 });
  }
  assert.ok(bar.hp < bar.maxHp, 'the knight went for the gold');
});

test('every enemy building your army breaks drops a few coins: 3 for a wall or tower, 5 for a gate or a guardhouse', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'wall', team: 'E', x: 4, y: 4 },
    { type: 'guardhouse', team: 'E', x: 5, y: 5 },
    { type: 'tower', team: 'E', x: 3, y: 5 },
    { type: 'knight', team: 'E', x: 0, y: 0 },
  ]);
  const [kn, wall, house, tower, foe] = s.units;
  assert.deepStrictEqual([wall.salvage, house.salvage, tower.salvage, foe.salvage, kn.salvage], [3, 5, 3, 0, 0]);
  for (const [b, gold] of [[wall, 3], [house, 8]]) {
    b.hp = 1;
    act(s, kn, { kind: 'unit', uid: b.uid });
    assert.ok(!b.alive);
    assert.strictEqual(s.stats.bounty, gold);
  }
  assert.ok(s.events.some((e) => e.t === 'gold' && e.coins && e.amount === 5));
  assert.ok(tower.alive && s.stats.bounty === 8, 'the tower still stands, its coins unclaimed');
  // Your own wards hold no coins.
  assert.strictEqual(AG.Data.UNITS.lightning.salvage, undefined);
  assert.strictEqual(AG.Data.UNITS.gate.salvage, 5);
});

console.log(`engine: ${passed} tests passed`);
if (failed.length) {
  console.log(failed.join('\n'));
  process.exit(1);
}
