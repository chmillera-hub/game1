// Hero Delve: floors, sleeping packs, exploring, kit and loot. Run: node tests/delve.test.js
const assert = require('assert');
const m = new Map();
globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js', 'dungeon.js']);
const E = AG.Engine;
const AI = AG.AI;
const DV = AG.Delve;

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

test('every floor: all its floor reachable, no monster in the first room, the Countess at the bottom', () => {
  for (let seed = 1; seed <= 30; seed++)
    for (let f = 1; f <= DV.FLOORS; f++) {
      const fl = DV.genFloor(seed, f);
      const reach = DV.flood(fl.terrain, fl.start.cx, fl.start.cy);
      for (let i = 0; i < fl.terrain.length; i++) if (fl.terrain[i] === 0) assert.ok(reach[i], `seed ${seed} floor ${f}: tile ${i} cut off`);
      for (const mo of fl.monsters) {
        assert.strictEqual(fl.terrain[mo.y * fl.w + mo.x], 0, 'monsters stand on floor');
        const r = fl.start;
        assert.ok(!(mo.x >= r.x && mo.x < r.x + r.w && mo.y >= r.y && mo.y < r.y + r.h), 'the way in is safe');
      }
      assert.ok(fl.monsters.length >= 4, `seed ${seed} floor ${f}: something to fight`);
      const boss = fl.monsters.filter((x) => x.type === 'countess');
      assert.strictEqual(boss.length, f === DV.FLOORS ? 1 : 0);
      if (boss.length) {
        const r = fl.end;
        assert.ok(boss[0].x >= r.x && boss[0].x < r.x + r.w && boss[0].y >= r.y && boss[0].y < r.y + r.h, 'she waits in the far room');
      }
    }
});

function battle(units, walls) {
  const terrain = new Array(144).fill(0);
  for (const [x, y] of walls || []) terrain[y * 12 + x] = E.T_ROCK;
  const s = E.createBattle({ w: 12, h: 12, terrain, seed: 3, objective: 'all', loot: [], goals: [], waves: [], relics: { P: [], E: [] }, units, queue: true });
  return s;
}

test('a sleeping pack takes no turns; the party in sight within 5 tiles wakes the whole pack', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 0, y: 0 },
    { type: 'skeleton', team: 'E', x: 9, y: 9, asleep: true, pack: 1 },
    { type: 'skeleton', team: 'E', x: 10, y: 10, asleep: true, pack: 1 },
    { type: 'spider', team: 'E', x: 11, y: 0, asleep: true, pack: 2 },
  ]);
  const [kn, s1, s2, sp] = s.units;
  assert.ok(!E.inQueue(s1) && !E.hasMove(s, 'E'), 'asleep: no turns');
  E.wakeCheck(s);
  assert.ok(s1.asleep && s2.asleep, 'too far to notice');
  kn.x = 6;
  kn.y = 7;
  E.wakeCheck(s);
  assert.ok(!s1.asleep && !s2.asleep, 'both wake together');
  assert.ok(sp.asleep, 'the other pack sleeps on');
  assert.ok(s.events.some((e) => e.t === 'wake'));
});

test('walls block the view; a blow wakes a pack at once', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 3, y: 3 },
    { type: 'skeleton', team: 'E', x: 6, y: 3, asleep: true, pack: 1 },
    { type: 'skeleton', team: 'E', x: 7, y: 3, asleep: true, pack: 1 },
  ], [[4, 3], [5, 3]]);
  E.wakeCheck(s);
  assert.ok(s.units[1].asleep, 'a wall between: still asleep');
  E.applyDamage(s, s.units[0], s.units[2], 5, { cat: 'none', dmgType: 'phys' });
  assert.ok(!s.units[1].asleep && !s.units[2].asleep, 'struck: the pack wakes');
});

test('the party walks toward the nearest sleeping pack; fights on its own; breaks a stalled fight', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 0, y: 0 },
    { type: 'skeleton', team: 'E', x: 10, y: 10, asleep: true, pack: 1 },
    { type: 'spider', team: 'E', x: 3, y: 11, asleep: true, pack: 2 },
  ]);
  const t = DV.exploreTarget(s, 0);
  assert.ok(t && t.tile && t.x === 3 && t.y === 11, 'the nearer pack first');
  s.units[2].asleep = false;
  assert.strictEqual(DV.exploreTarget(s, 0), null, 'a fight on: its own judgement');
  assert.deepStrictEqual(DV.exploreTarget(s, 99), { uid: s.units[2].uid, press: true }, 'stalled: go get it');
});

test('the top level, then prestige: XP past it buys from the Prestige Trainer', () => {
  const p = DV.newProfile();
  const h = p.party[0];
  for (let i = 0; i < 20; i++) DV.gainXp(h, DV.xpToNext(h.lv), p);
  assert.strictEqual(h.lv, DV.MAX_LV);
  assert.strictEqual(DV.MAX_LV, 10);
  const before = p.prestige || 0;
  DV.gainXp(h, DV.PRESTIGE_XP * 2 + 5, p);
  assert.strictEqual(h.lv, DV.MAX_LV, 'no higher');
  assert.strictEqual(p.prestige, before + 2, 'prestige instead');
  const stock = DV.stock(p);
  assert.ok(stock.length >= 6);
  p.prestige = 20;
  const price = DV.priceOf(DV.itemDef(stock[0]));
  const n = p.stash.length;
  const it = DV.buy(p, 0);
  assert.ok(it && p.stash.length === n + 1 && p.prestige === 20 - price, 'bought into the stash');
  p.prestige = 0;
  assert.strictEqual(DV.buy(p, 0), null, 'not without the points');
});

test('kit stays legal: own class talents unlocked by level and paid with points, one hero per item, slots by level', () => {
  const p = DV.newProfile();
  const [a, b] = p.party;
  const it = p.stash.find((x) => x.kind === 'gear' && AG.Data.eligible(a.type, DV.itemDef(x)) && AG.Data.eligible(b.type, DV.itemDef(x)));
  a.gear = [it.uid];
  b.gear = [it.uid];
  DV.normalize(p, a);
  DV.normalize(p, b);
  assert.ok(!(a.gear.includes(it.uid) && b.gear.includes(it.uid)), 'one hero per item');
  for (const h of DV.heroes(p)) {
    assert.strictEqual(h.lv, 1, 'everyone starts at Level 1');
    assert.strictEqual(h.talents.length, 0, 'no points yet, no talents');
    assert.ok(h.gear.length <= 1 && h.skills.length <= 1, 'one slot each at Level 1');
  }
  a.talents = ['pa_oath', 'pa_oath', DV.classTalents(a.type)[0]];
  DV.normalize(p, a);
  assert.deepStrictEqual(a.talents, [], 'no talents without the level and the points');
  DV.gainXp(a, DV.xpToNext(1));
  assert.strictEqual(a.lv, 2);
  assert.strictEqual(DV.pointsLeft(a) + DV.pointsSpent(a), 1, 'a point a level');
  const fresh = DV.setClass(p, 0, 'pyromancer');
  assert.strictEqual(fresh.type, 'pyromancer');
  assert.strictEqual(fresh.lv, 2, 'a new class keeps the level');
  assert.ok(!DV.CLASSES.includes('barrier') && !DV.CLASSES.includes('cleric'), 'no wards, the Cleric always comes');
});

test('levels: XP to level up, skill points for talents (by level) and training, respec, growth in the spec', () => {
  const p = DV.newProfile();
  const h = p.party[0];
  h.auto = false;
  let ups = 0;
  for (let i = 0; i < 4; i++) ups += DV.gainXp(h, DV.xpToNext(h.lv));
  assert.strictEqual(h.lv, 5);
  assert.strictEqual(ups, 4);
  assert.strictEqual(DV.pointsLeft(h), 4);
  const [t1] = DV.classTalents(h.type).filter((id) => DV.talentLevel(id) === 2);
  assert.ok(DV.learn(p, h, t1));
  assert.ok(!DV.learn(p, h, t1), 'once');
  assert.ok(DV.train(p, h, 'vit'));
  const spec = DV.specOf(p, h);
  assert.strictEqual(spec.dlv, 5);
  assert.strictEqual(spec.level, 2, 'Level 4+: the second ability');
  assert.ok(Math.abs(spec.hpMul - (DV.hpMul(5) + DV.TRAIN.vit.hp)) < 1e-9);
  assert.ok(spec.talents.includes(t1));
  DV.respec(p, h);
  assert.strictEqual(DV.pointsLeft(h), 4);
  assert.strictEqual(DV.slotsOf(h).gear, 2);
  assert.strictEqual(DV.slotsOf(h).skills, 2);
  const auto = p.party[1];
  assert.ok(!auto.auto, 'heroes wait for you to spend their points');
  auto.auto = true;
  for (let i = 0; i < 6; i++) DV.gainXp(auto, DV.xpToNext(auto.lv));
  assert.ok(auto.talents.length > 0, 'auto-spend learns talents as they open');
  const low = { dlv: 1, type: 'skeleton' };
  assert.ok(DV.killXp(low, 1) > DV.killXp(low, 6), 'monsters far below are worth little');
  assert.ok(DV.killXp({ dlv: 4, type: 'troll', champ: true }, 3) >= 4 * DV.killXp({ dlv: 4, type: 'troll' }, 3) * 0.99, 'champions are worth far more');
});

function roundBattle(units, walls, extra) {
  const terrain = new Array(144).fill(0);
  for (const [x, y] of walls || []) terrain[y * 12 + x] = E.T_ROCK;
  return E.createBattle(Object.assign({ w: 12, h: 12, terrain, seed: 3, objective: 'all', loot: [], goals: [], waves: [], relics: { P: [], E: [] }, units, queue: true, rounds: true, turnLimit: 100000, delve: { respawn: [[0, 0], [1, 0], [0, 1], [1, 1]] } }, extra || {}));
}

test('rounds: every unit takes one turn a round, the fastest first, whichever side', () => {
  const s = roundBattle([
    { type: 'knight', team: 'P', x: 0, y: 0 },
    { type: 'scout', team: 'P', x: 1, y: 0 },
    { type: 'skeleton', team: 'E', x: 6, y: 5 },
    { type: 'wolf', team: 'E', x: 7, y: 5 },
  ]);
  const order = [];
  for (let i = 0; i < 8; i++) {
    order.push(s.byId[s.due].type);
    E.endTurn(s);
  }
  assert.deepStrictEqual(order.slice(0, 4), ['scout', 'wolf', 'skeleton', 'knight'], 'speed order, both sides mixed');
  assert.deepStrictEqual(order.slice(4), order.slice(0, 4), 'and again next round');
  assert.strictEqual(s.turn, 3);
  const { now, next } = E.roundOrder(s);
  assert.strictEqual(next.length, 4);
  assert.ok(now.length <= 4);
});

test('rounds: a unit cooling down still takes its turn, and may move but not act', () => {
  const s = roundBattle([
    { type: 'pyromancer', team: 'P', x: 2, y: 2 },
    { type: 'skeleton', team: 'E', x: 6, y: 2 },
  ]);
  const py = s.units[0];
  while (s.byId[s.due] !== py) E.endTurn(s);
  py.wait = 2;
  E.endTurn(s);
  while (s.byId[s.due] !== py) E.endTurn(s);
  assert.strictEqual(s.due, py.uid, 'its turn, cooldown and all');
  assert.strictEqual(E.allTargets(s, py).length, 0, 'nothing to act with');
  assert.ok(E.beginActivation(s, py.uid));
  assert.ok(E.moveUnit(s, py.uid, 1, 2), 'it moves');
  const w = py.wait;
  E.endTurn(s);
  assert.strictEqual(py.wait, w - 1, 'and its cooldown drops as the turn ends');
});

test('fatigue sets in at round 20 of a fight, for both sides, and is gone once it is over', () => {
  const s = roundBattle([
    { type: 'knight', team: 'P', x: 5, y: 5 },
    { type: 'troll', team: 'E', x: 9, y: 9, asleep: true, pack: 1 },
  ]);
  E.wakePack(s, s.units[1]);
  const kn = s.units[0];
  kn.hp = kn.maxHp = 99999;
  s.units[1].hp = s.units[1].maxHp = 99999;
  let hits = 0;
  for (let i = 0; i < 80 && s.turn - s.fightFrom < E.FATIGUE_AT + 2; i++) {
    E.endTurn(s);
    hits += s.events.filter((e) => e.t === 'dmg' && e.dmgType === 'fatigue').length;
    if (s.turn - s.fightFrom + 1 < E.FATIGUE_AT) assert.strictEqual(hits, 0, 'not before round 20');
    s.events.length = 0;
  }
  assert.ok(hits >= 2 && s.tire.P.on && s.tire.E.on, 'both sides tire');
  E.applyDamage(s, kn, s.units[1], 999999, { cat: 'none', dmgType: 'true' });
  E.addUnit(s, { type: 'skeleton', team: 'E', x: 0, y: 11, asleep: true, pack: 2 });
  E.endTurn(s);
  E.endTurn(s);
  assert.ok(!s.tire.P.on && !s.tire.E.on, 'off again after the fight');
});

test('a pack left far behind gives up: home, full health, asleep; its dead stay dead', () => {
  const s = roundBattle([
    { type: 'knight', team: 'P', x: 0, y: 0 },
    { type: 'skeleton', team: 'E', x: 10, y: 10, asleep: true, pack: 1 },
    { type: 'skeleton', team: 'E', x: 11, y: 11, asleep: true, pack: 1 },
  ], null, { delve: { respawn: [[0, 0]], leash: 6 } });
  const [kn, a, b] = s.units;
  E.wakePack(s, a);
  a.hp = 5;
  s.occ[E.idx(s, a.x, a.y)] = 0;
  a.x = 4;
  a.y = 4;
  s.occ[E.idx(s, 4, 4)] = a.uid;
  b.alive = false;
  s.occ[E.idx(s, b.x, b.y)] = 0;
  for (let i = 0; i < 6 && !a.asleep; i++) E.endTurn(s);
  assert.ok(a.asleep, 'back to sleep');
  assert.strictEqual(a.hp, a.maxHp, 'healed');
  assert.deepStrictEqual([a.x, a.y], [10, 10], 'home');
  assert.ok(!b.alive, 'the slain stay slain');
  assert.ok(!s.over && kn.alive);
});

test('nobody loses a floor: a wiped party gets up at the way in; the fallen get up once a fight is over', () => {
  const s = roundBattle([
    { type: 'knight', team: 'P', x: 5, y: 5 },
    { type: 'archer', team: 'P', x: 6, y: 5 },
    { type: 'troll', team: 'E', x: 5, y: 6, asleep: true, pack: 1 },
  ]);
  const [kn, ar, tr] = s.units;
  E.wakePack(s, tr);
  E.endTurn(s);
  E.applyDamage(s, tr, kn, 999, { cat: 'none', dmgType: 'true' });
  E.applyDamage(s, tr, ar, 999, { cat: 'none', dmgType: 'true' });
  tr.hp = 10;
  assert.ok(!s.over, 'not a defeat');
  E.endTurn(s);
  assert.ok(kn.alive && ar.alive, 'everyone up');
  assert.strictEqual(kn.hp, kn.maxHp, 'at full health');
  assert.ok(kn.x <= 1 && kn.y <= 1, 'at the way in');
  assert.ok(tr.asleep && tr.hp === tr.maxHp, 'the monsters it fought heal and go home');
  E.applyDamage(s, kn, tr, 9999, { cat: 'none', dmgType: 'true' });
  E.checkOutcome(s);
  assert.ok(s.over && s.winner === 'P', 'the floor is clear');
});

test('a fallen hero gets up at half health once no pack is awake; abilities come back', () => {
  const s = roundBattle([
    { type: 'knight', team: 'P', x: 5, y: 5, a1: 'k_bash' },
    { type: 'archer', team: 'P', x: 6, y: 5 },
    { type: 'skeleton', team: 'E', x: 5, y: 7, asleep: true, pack: 1 },
    { type: 'skeleton', team: 'E', x: 11, y: 11, asleep: true, pack: 2 },
  ]);
  const [kn, ar, a] = s.units;
  E.wakePack(s, a);
  E.endTurn(s);
  const bash = kn.acts.find((x) => x.uses > 0);
  bash.left = 0;
  E.applyDamage(s, a, ar, 999, { cat: 'none', dmgType: 'true' });
  E.applyDamage(s, kn, a, 999, { cat: 'none', dmgType: 'true' });
  for (let i = 0; i < 6 && !ar.alive; i++) E.endTurn(s);
  assert.ok(ar.alive, 'back up');
  assert.ok(ar.hp < ar.maxHp && ar.hp >= Math.floor(ar.maxHp * E.REST_REGEN) , 'at about half health, healing as it walks');
  assert.ok(ar.x <= 1 && ar.y <= 1, 'at the way in');
  assert.strictEqual(bash.left, bash.uses, 'uses back');
});

test('levels count in a fight; level ups take hold once the fight is over', () => {
  const s = roundBattle([
    { type: 'knight', team: 'P', x: 5, y: 5, dlv: 3 },
    { type: 'skeleton', team: 'E', x: 5, y: 6, dlv: 1 },
    { type: 'skeleton', team: 'E', x: 7, y: 7, dlv: 5 },
  ]);
  const [kn, lo, hi] = s.units;
  const vsLo = E.calcHit(s, kn, lo, { cat: 'front' }).dmg;
  const vsHi = E.calcHit(s, kn, hi, { cat: 'front' }).dmg;
  assert.ok(vsLo > vsHi, 'a level edge');
  const p = DV.newProfile();
  DV.startRun(p, 77);
  const { s: fs } = DV.floorBattle(p);
  const hero = fs.units.find((u) => u.team === 'P' && u.rid);
  const h = DV.heroes(p).find((x) => x.id === hero.rid);
  const hp0 = hero.maxHp;
  DV.gainXp(h, DV.xpToNext(1));
  fs.inCombat = true;
  assert.deepStrictEqual(DV.refreshParty(p, fs), [], 'not mid-fight');
  fs.inCombat = false;
  assert.ok(DV.refreshParty(p, fs).includes(hero.uid));
  assert.ok(hero.maxHp > hp0 && hero.dlv === 2 && hero.hp === hero.maxHp, 'stronger, and healed up');
});

test('each floor has a Champion, away from the way in; the party leaves packs far above it for later', () => {
  for (let seed = 1; seed <= 20; seed++)
    for (let f = 1; f <= DV.FLOORS; f++) {
      const fl = DV.genFloor(seed, f);
      const ch = fl.monsters.filter((m) => m.champ);
      assert.strictEqual(ch.length, 1, `seed ${seed} floor ${f}: one Champion`);
      assert.ok(Math.abs(ch[0].x - fl.start.cx) + Math.abs(ch[0].y - fl.start.cy) > 8, 'away from the way in');
      assert.ok(ch[0].dlv > Math.max(...fl.monsters.filter((m) => !m.champ && m.type !== 'countess').map((m) => m.dlv)), 'above the rest');
    }
  const s = roundBattle([
    { type: 'knight', team: 'P', x: 0, y: 0, dlv: 2, rid: 'h1' },
    Object.assign(DV.monsterSpec('troll', 6), { team: 'E', x: 7, y: 0, asleep: true, pack: 1, champ: true }),
    Object.assign(DV.monsterSpec('skeleton', 2), { team: 'E', x: 0, y: 9, asleep: true, pack: 2 }),
  ]);
  assert.ok(s.units[1].asleep && s.units[2].asleep);
  const t = DV.exploreTarget(s, 0);
  assert.ok(t && t.tile, 'walking somewhere');
  assert.ok(Math.abs(t.x - 0) + Math.abs(t.y - 9) < Math.abs(t.x - 7) + Math.abs(t.y - 0), 'toward the pack it can take, not the Champion');
  assert.strictEqual(DV.danger(6, 2), 'deadly');
  assert.strictEqual(DV.danger(3, 2), 'high');
  assert.strictEqual(DV.danger(2, 2), 'even');
});

test('a whole delve plays out: floors cleared, levels gained, loot in the stash', () => {
  const p = DV.newProfile();
  DV.startRun(p, 1001);
  const start = p.stash.length;
  let floors = 0;
  while (p.run && floors < 3) {
    const { s } = DV.floorBattle(p);
    const known = new Set();
    const credited = new Set();
    let idle = 0;
    for (let g = 0; g < 12000 && !s.over; g++) {
      const focus = s.side === 'P' ? DV.exploreTarget(s, idle) : null;
      AI.playTurn(s, s.side, s.side === 'E' ? { stance: 'aggressive', temp: 0 } : { stance: 'balanced', temp: 0, focus });
      DV.creditKills(p, s, credited);
      for (const d of DV.packsDown(s, known)) DV.rollLoot(p, AG.derive(1, 'l' + d.pack), p.run.floor, d.kind);
      DV.refreshParty(p, s);
      idle = DV.idleAfter(s, s.events, idle);
      s.events.length = 0;
    }
    assert.ok(s.over && s.winner === 'P', `floor ${p.run.floor} cleared`);
    const before = p.run.floor;
    DV.finishFloor(p, s);
    floors++;
    if (p.run) {
      assert.strictEqual(p.run.floor, before + 1);
      const next = DV.floorBattle(p).s;
      for (const u of next.units.filter((x) => x.team === 'P')) assert.ok(u.alive && u.hp === u.maxHp, 'everyone starts the floor rested');
    }
  }
  assert.ok(floors >= 2, 'floors cleared');
  assert.ok(p.stash.length > start, 'loot found');
  assert.ok(DV.heroes(p).every((h) => h.lv >= 3), 'the party levelled up');
});

console.log(`delve: ${passed} tests passed`);
