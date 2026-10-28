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
  assert.deepStrictEqual(DV.exploreTarget(s, 99), { uid: s.units[2].uid }, 'stalled: go get it');
});

test('kit stays legal: own class talents, one hero per item, slots respected; auto-kit fills', () => {
  const p = DV.newProfile();
  const [a, b] = p.party;
  const it = p.stash.find((x) => x.kind === 'gear' && AG.Data.eligible(a.type, DV.itemDef(x)) && AG.Data.eligible(b.type, DV.itemDef(x)));
  a.gear = [it.uid];
  b.gear = [it.uid];
  DV.normalize(p, a);
  DV.normalize(p, b);
  assert.ok(!(a.gear.includes(it.uid) && b.gear.includes(it.uid)), 'one hero per item');
  a.talents = ['pa_oath', 'pa_oath'];
  DV.normalize(p, a);
  assert.ok(a.talents.every((id) => AG.Data.TALENTS[id].cls === a.type), 'own class talents only');
  const fresh = DV.setClass(p, 0, 'pyromancer');
  assert.strictEqual(fresh.type, 'pyromancer');
  assert.ok(fresh.talents.length > 0, 'a new hero comes kitted');
  for (const h of DV.heroes(p)) {
    assert.ok(h.talents.length <= DV.SLOTS.talents && h.skills.length <= DV.SLOTS.skills && h.gear.length <= DV.SLOTS.gear);
    const spec = DV.specOf(p, h);
    assert.strictEqual(spec.level, 3);
  }
  assert.ok(!DV.CLASSES.includes('barrier') && !DV.CLASSES.includes('cleric'), 'no wards, the Cleric always comes');
});

test('a whole delve plays out: floors cleared, fallen heroes up at the shrine, loot in the stash', () => {
  const p = DV.newProfile();
  DV.startRun(p, 1001);
  const start = p.stash.length;
  let floors = 0;
  while (p.run && floors < DV.FLOORS) {
    const { s } = DV.floorBattle(p);
    const known = new Set();
    let idle = 0;
    for (let g = 0; g < 6000 && !s.over; g++) {
      const focus = s.side === 'P' ? DV.exploreTarget(s, idle) : null;
      AI.playTurn(s, s.side, s.side === 'E' ? { stance: 'aggressive', temp: 0 } : { stance: 'balanced', temp: 0, focus });
      for (const d of DV.packsDown(s, known)) DV.rollLoot(p, AG.derive(1, 'l' + d.pack), p.run.floor, d.boss);
      idle = s.events.some((e) => e.t === 'dmg') ? 0 : idle + 1;
      s.events.length = 0;
    }
    assert.ok(s.over, `floor ${p.run.floor} finished`);
    if (s.winner !== 'P') break;
    const before = p.run.floor;
    DV.finishFloor(p, s);
    floors++;
    if (p.run) {
      assert.strictEqual(p.run.floor, before + 1);
      const next = DV.floorBattle(p).s;
      for (const u of next.units.filter((x) => x.team === 'P')) assert.ok(u.alive && u.hp > 0, 'everyone starts the floor standing');
    }
  }
  assert.ok(floors >= 1, 'at least one floor cleared');
  assert.ok(p.stash.length > start, 'loot found');
});

console.log(`delve: ${passed} tests passed`);
