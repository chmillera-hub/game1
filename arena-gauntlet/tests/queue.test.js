// The unit queue: each side's units take its turns in a speed-ordered rotation.
// Run: node tests/queue.test.js
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

function battle(units, opts = {}) {
  const w = 9;
  const h = 9;
  return E.createBattle(Object.assign({ w, h, terrain: new Array(w * h).fill(0), units, relics: { P: [], E: [] }, seed: 7, queue: true }, opts));
}

// The enemy passes until it is the player's turn.
function toPlayer(s) {
  while (!s.over && s.side !== 'P') E.pass(s);
}

// The due unit steps one tile and ends the turn.
function shuffle(s) {
  const u = s.byId[s.due];
  const spot = [...E.reachable(s, u).values()].find((r) => r.d === 1);
  assert.ok(E.beginActivation(s, u.uid));
  assert.ok(E.moveUnit(s, u.uid, spot.x, spot.y));
  E.finishActivation(s, null);
  E.endTurn(s);
  return u;
}

const name = (s, uid) => s.byId[uid].type;

test('faster units go first, and everyone gets one turn per cycle', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'archer', team: 'P', x: 6, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  const order = [];
  for (let i = 0; i < 6; i++) {
    toPlayer(s);
    order.push(shuffle(s).type);
  }
  assert.deepStrictEqual(order, ['scout', 'archer', 'knight', 'scout', 'archer', 'knight']);
});

test('only the due unit may act', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  toPlayer(s);
  const [kn, sc] = s.units;
  assert.strictEqual(s.due, sc.uid);
  assert.ok(!E.canActivate(s, kn), 'the knight waits its turn');
  assert.deepStrictEqual(E.readyUnits(s, 'P').map((u) => u.uid), [sc.uid]);
});

test('a unit cooling down sits out its turn and the next one goes', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'archer', team: 'P', x: 0, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 4, facing: 2 },
  ]);
  const [kn, ar, go] = s.units;
  kn.cycles = -1; // the knight is up first
  toPlayer(s);
  assert.strictEqual(s.due, kn.uid);
  assert.ok(E.beginActivation(s, kn.uid));
  assert.ok(E.performAction(s, kn.uid, { kind: 'unit', uid: go.uid }));
  E.finishActivation(s, 0);
  assert.strictEqual(kn.wait, 1);
  E.endTurn(s);
  toPlayer(s);
  assert.strictEqual(s.due, ar.uid, 'the archer goes');
  shuffle(s);
  toPlayer(s);
  assert.strictEqual(s.due, ar.uid, 'the knight sat out its turn, so the archer goes again');
  assert.ok(s.events.some((e) => e.t === 'sitout' && e.uid === kn.uid && e.why === 'cooldown'));
  assert.strictEqual(kn.wait, 0);
  shuffle(s);
  toPlayer(s);
  assert.strictEqual(s.due, kn.uid, 'and then the knight is back');
});

test('moving never starts a cooldown in the queue either', () => {
  const s = battle([
    { type: 'witch', team: 'P', x: 4, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  toPlayer(s);
  const wi = shuffle(s);
  assert.strictEqual(wi.wait, 0);
  toPlayer(s);
  assert.strictEqual(s.due, wi.uid);
});

test('statuses count the unit’s own turns, not the side’s', () => {
  // The golem stands next to the knight, so a rooted knight still has a turn to take.
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'archer', team: 'P', x: 6, y: 8 },
    { type: 'golem', team: 'E', x: 2, y: 7 },
  ]);
  const kn = s.units[0];
  kn.root = 1;
  toPlayer(s);
  shuffle(s); // scout
  toPlayer(s);
  shuffle(s); // archer
  assert.strictEqual(kn.root, 1, 'other units’ turns do not wear it off');
  toPlayer(s);
  assert.strictEqual(s.due, kn.uid);
  E.pass(s);
  assert.strictEqual(kn.root, 0, 'its own turn does');
});

test('a unit with nothing it could do sits its turn out', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  const [kn, sc] = s.units;
  sc.root = 3;
  toPlayer(s);
  assert.strictEqual(s.due, kn.uid, 'a rooted scout with nobody in reach is passed over');
  assert.strictEqual(sc.root, 2, 'and that counted as one of its turns');
});

test('paralysis costs the unit its next turn', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  const [kn, sc] = s.units;
  sc.para = 1;
  toPlayer(s);
  assert.strictEqual(s.due, kn.uid, 'the scout is paralyzed, so the knight goes');
  assert.strictEqual(sc.para, 0);
  shuffle(s);
  toPlayer(s);
  assert.strictEqual(s.due, sc.uid, 'a new cycle, and the scout is fine again');
});

test('when every unit must sit out, the side passes', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  for (const u of s.units) if (u.team === 'P') u.wait = 1;
  E.pass(s);
  assert.strictEqual(s.side, 'E', 'your turn passed on its own');
  assert.ok(s.events.some((e) => e.t === 'pass' && e.side === 'P' && e.auto));
  assert.ok(s.units.filter((u) => u.team === 'P').every((u) => u.wait === 0), 'each sat out one turn');
});

test('a boss sits out its first turn and the next enemy goes', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 4, y: 8 },
    { type: 'warlord', team: 'E', x: 4, y: 0 },
    { type: 'orc', team: 'E', x: 2, y: 0 },
  ]);
  const [, boss, orc] = s.units;
  assert.strictEqual(s.side, 'E');
  assert.strictEqual(s.due, orc.uid);
  assert.ok(s.events.some((e) => e.t === 'sitout' && e.uid === boss.uid));
});

test('the preview matches the rotation', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'archer', team: 'P', x: 6, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  toPlayer(s);
  assert.deepStrictEqual(
    E.upcoming(s, 'P', 3).map((x) => name(s, x.uid)),
    ['scout', 'archer', 'knight']
  );
  assert.strictEqual(E.queueDelay(s, s.units[0]), 2);
});

test('the turn order shows units cooling down, with their cooldown, passing in their place', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'archer', team: 'P', x: 6, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  toPlayer(s);
  const [kn, sc, ar] = s.units;
  E.pass(s); // the enemy's turn: yours is next
  // The archer is up next, but cooling down for 2 more of its turns.
  ar.wait = 2;
  ar.cycles = Math.min(kn.cycles, sc.cycles);
  ar.spd = 99;
  const order = E.upcoming(s, 'P', 6);
  const flat = order.flatMap((x) => [...x.passes.map((p) => `${name(s, p.uid)}(${p.wait})`), x.uid ? name(s, x.uid) : 'none']);
  assert.strictEqual(flat.filter((t) => t === 'archer(2)').length, 1, flat.join(' '));
  assert.ok(flat.indexOf('archer(2)') < flat.indexOf('archer(1)') && flat.indexOf('archer(1)') < flat.indexOf('archer'), flat.join(' '));
  // And the battle plays out as shown: the archer's turns come, it passes them, and its cooldown counts down.
  const seen = [];
  for (let i = 0; i < 12 && !(s.side === 'P' && s.due === ar.uid); i++) {
    const ev = s.events.length;
    E.pass(s);
    for (const e of s.events.slice(ev)) if (e.t === 'sitout' && e.uid === ar.uid) seen.push(e.wait);
  }
  assert.deepStrictEqual(seen, [2, 1]);
  assert.strictEqual(s.due, ar.uid, 'then it acts');
});

test('reinforcements join the current cycle in speed order', () => {
  const s = battle(
    [
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'orc', team: 'E', x: 4, y: 0 },
    ],
    { waves: [{ turn: 1, team: 'E', tiles: [[0, 0], [1, 0], [2, 0]], units: [{ type: 'warg' }] }] }
  );
  E.pass(s); // the enemy's first turn ends and the warg arrives
  const warg = s.units.find((u) => u.type === 'warg');
  assert.ok(warg && warg.alive);
  const orc = s.units.find((u) => u.type === 'orc');
  assert.strictEqual(warg.cycles, orc.cycles, 'it joins the cycle the orc is on');
});

test('fatigue: each side its own count, from 1: enemy 1, you 1, enemy 2, you 2, past shields', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 2, y: 8 },
      { type: 'golem', team: 'P', x: 6, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2 }
  );
  for (const u of s.units) u.shield = 50;
  const hits = [];
  for (let i = 0; i < 8 && !s.over; i++) {
    E.pass(s);
    for (const e of s.events) if (e.t === 'dmg' && e.dmgType === 'fatigue' && !hits.includes(e)) hits.push(e);
  }
  assert.ok(s.events.some((e) => e.t === 'overtime'), 'fatigue set in');
  assert.deepStrictEqual(
    hits.map((e) => `${s.byId[e.uid].team}${e.amount}`),
    ['E1', 'P1', 'E2', 'P2', 'E3', 'P3', 'E4'],
    'one unit at a time, each side its own next number, enemy first'
  );
  assert.notStrictEqual(hits[1].uid, hits[3].uid, 'the two player golems take turns');
  assert.deepStrictEqual(hits.map((e) => e.fatigueNo), [1, 1, 2, 2, 3, 3, 4]);
  assert.strictEqual(E.fatigueHit(s, 'P'), 4);
  assert.strictEqual(E.fatigueHit(s, 'E'), 5);
  assert.ok(s.units.every((u) => u.shield === 50), 'shields do not stop it');
});

test('fatigue: a unit passing its turn (cooling down) loses HP too, then the next one goes and loses one more', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 2, y: 8 },
      { type: 'golem', team: 'P', x: 6, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2 }
  );
  E.pass(s); // the enemy's turn 1 ends
  E.pass(s); // yours ends, and fatigue sets in on the enemy's turn 2
  const [a, b] = s.units;
  a.wait = 1; // a sits out its next turn, so b goes in the same turn
  b.cycles = a.cycles;
  const ev = s.events.length;
  E.pass(s); // your turn 2 starts
  const hits = s.events.slice(ev).filter((e) => e.t === 'dmg' && e.dmgType === 'fatigue');
  assert.strictEqual(hits.length, 2);
  assert.deepStrictEqual(hits.map((e) => e.uid), [a.uid, b.uid], 'a passes and tires, then b takes the turn and tires');
  assert.strictEqual(hits[1].amount, hits[0].amount + 1, 'b loses the next number, one more');
  assert.strictEqual(s.due, b.uid);
  assert.ok(s.events.slice(ev).some((e) => e.t === 'sitout' && e.uid === a.uid && e.why === 'cooldown' && e.wait === 1));
  assert.strictEqual(a.wait, 0, 'its cooldown ticks down');
});

test('a unit\'s turn start comes in one order: fatigue, poison, burn, regen, then its pass with the cooldown ticking down', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 2, y: 8 },
      { type: 'golem', team: 'P', x: 6, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2 }
  );
  E.pass(s);
  E.pass(s);
  const [a, b] = s.units;
  a.wait = 2; // a passes, then b takes the side's turn
  b.cycles = a.cycles;
  a.poison = { turns: 2, dmg: 5, src: 0 };
  a.burn = { turns: 2, dmg: 4, src: 0 };
  // Poison stops healing, so b shows regen: burnt, but not poisoned.
  b.hp = b.maxHp - 60;
  b.regen = 3;
  b.burn = { turns: 2, dmg: 4, src: 0 };
  const ev = s.events.length;
  E.pass(s); // your turn starts
  const seen = s.events.slice(ev).filter((e) => e.uid && ['dmg', 'heal', 'sitout'].includes(e.t));
  const show = (e) => (e.uid === a.uid ? 'a ' : 'b ') + (e.t === 'dmg' ? e.dmgType : e.t);
  assert.deepStrictEqual(seen.map(show), ['a fatigue', 'a poison', 'a burn', 'a sitout', 'b fatigue', 'b burn', 'b heal']);
  const pass = seen[3];
  assert.deepStrictEqual([pass.why, pass.wait], ['cooldown', 2], 'the pass shows the cooldown before it ticks');
  assert.strictEqual(a.wait, 1, 'then it ticks down one');
  assert.strictEqual(seen[4].amount, seen[0].amount + 1, 'b tires one more than a');
  assert.strictEqual(s.due, b.uid);
});

test('fatigue at 15 with five units cooling down: they pass one by one and lose 15, 16, 17, 18, 19, then the sixth acts at 20', () => {
  const units = [];
  for (let x = 1; x <= 6; x++) units.push({ type: 'golem', team: 'P', x, y: 8 });
  units.push({ type: 'golem', team: 'E', x: 4, y: 0 });
  const s = battle(units, { overtime: 2 });
  E.pass(s);
  E.pass(s);
  const mine = s.units.filter((u) => u.team === 'P');
  for (const u of mine) {
    u.hp = u.maxHp = 999;
    u.cycles = mine[0].cycles;
  }
  for (const u of mine.slice(0, 5)) u.wait = 1;
  s.tire.P.n = 14;
  assert.strictEqual(E.fatigueHit(s, 'P'), 15);
  const ev = s.events.length;
  E.pass(s);
  const seq = s.events.slice(ev).filter((e) => (e.t === 'dmg' && e.dmgType === 'fatigue' && s.byId[e.uid].team === 'P') || (e.t === 'sitout' && s.byId[e.uid].team === 'P'));
  assert.deepStrictEqual(
    seq.map((e) => (e.t === 'sitout' ? 'pass' : e.amount)),
    [15, 'pass', 16, 'pass', 17, 'pass', 18, 'pass', 19, 'pass', 20],
    'each unit tires as its own turn comes, then passes, and the next one goes'
  );
  assert.strictEqual(s.due, mine[5].uid);
});

test('fatigue: when every unit passes, each loses HP as its turn comes, and the side passes', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 2, y: 8 },
      { type: 'golem', team: 'P', x: 6, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2 }
  );
  E.pass(s);
  E.pass(s);
  const [a, b] = s.units;
  a.wait = 1;
  b.wait = 1;
  b.cycles = a.cycles;
  const ev = s.events.length;
  E.pass(s);
  const hits = s.events.slice(ev).filter((e) => e.t === 'dmg' && e.dmgType === 'fatigue' && s.byId[e.uid].team === 'P');
  assert.deepStrictEqual(hits.map((e) => e.uid), [a.uid, b.uid]);
  assert.strictEqual(hits[1].amount, hits[0].amount + 1, 'each pass counts: the next number');
  assert.ok(s.events.slice(ev).some((e) => e.t === 'pass' && e.side === 'P' && e.auto), 'nobody acts: the side passes');
});

test('fatigue reaches wards: Barrier and Lightning Wards tire when their turn comes, acting or not', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 2, y: 8 },
      { type: 'barrier', team: 'P', x: 4, y: 8 },
      { type: 'lightning', team: 'P', x: 6, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2 }
  );
  const [g, bw, lw, eg] = s.units;
  for (const u of s.units) u.hp = u.maxHp = 999;
  // The Barrier Ward never acts: in the turn order it only ever passes.
  const order = E.upcoming(s, 'P', 6);
  assert.ok(!order.some((x) => x.uid === bw.uid));
  assert.ok(order.some((x) => x.passes.some((p) => p.uid === bw.uid && p.why === 'passive')));
  const ev = s.events.length;
  while (s.turn < 11) E.pass(s);
  const hits = {};
  for (const e of s.events.slice(ev)) if (e.t === 'dmg' && e.dmgType === 'fatigue') hits[e.uid] = (hits[e.uid] || 0) + 1;
  // Neither ward has anything in reach: both sit every turn out, and both still tire, once a cycle like the golem.
  assert.ok(hits[bw.uid] >= 2 && hits[lw.uid] >= 2, JSON.stringify(hits));
  assert.ok(Math.abs(hits[bw.uid] - hits[g.uid]) <= 1 && Math.abs(hits[lw.uid] - hits[g.uid]) <= 1, JSON.stringify(hits));
  assert.ok(hits[eg.uid] > 0);
  // The Barrier Ward passes quietly; only real sit-outs make the log.
  assert.ok(!s.events.some((e) => e.t === 'sitout' && e.uid === bw.uid && e.why !== 'passive'));
});

test('two lone Barrier Wards: fatigue settles it', () => {
  const s = battle(
    [
      { type: 'barrier', team: 'P', x: 4, y: 8 },
      { type: 'barrier', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2 }
  );
  for (let i = 0; i < 400 && !s.over; i++) E.pass(s);
  assert.ok(s.over && !s.timeout, 'fatigue ends it');
});

test('poison ticks on the poisoned unit\'s own turn, not for the whole side at once', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'knight', team: 'P', x: 6, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  toPlayer(s);
  const [a, b] = s.units;
  a.poison = { turns: 2, dmg: 5, src: 0 };
  b.poison = { turns: 2, dmg: 5, src: 0 };
  E.pass(s); // your turn ends
  const ev = s.events.length;
  E.pass(s); // the enemy's ends; your next turn starts with one of your knights
  const due = s.byId[s.due];
  const ticks = s.events.slice(ev).filter((e) => e.t === 'dmg' && e.dmgType === 'poison');
  assert.deepStrictEqual(ticks.map((e) => e.uid), [due.uid], 'only the unit whose turn it is');
});

test('fatigue: the bigger side outlasts the smaller, and reinforcements stop', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 4, y: 8 },
      { type: 'scout', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2, turnLimit: 500, waves: [{ turn: 5, team: 'E', tiles: [[0, 0], [1, 0]], units: [{ type: 'warg' }] }] }
  );
  for (let i = 0; i < 400 && !s.over; i++) E.pass(s);
  assert.ok(s.over);
  assert.strictEqual(s.winner, 'P', 'the golem outlasts the scout');
  assert.ok(!s.timeout);
  assert.ok(!s.units.some((u) => u.type === 'warg'), 'the warg never came');
});

test('fatigue: regen holds it off for a while, but not for ever', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 4, y: 8, level: 2, talents: ['g_moss'], gear: ['healing_charm'] },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2, turnLimit: 500 }
  );
  for (let i = 0; i < 600 && !s.over; i++) E.pass(s);
  assert.ok(s.over && !s.timeout, 'fatigue ends it');
  assert.strictEqual(s.winner, 'P', 'regen 7 outlasts no regen');
});

test('regen heals only on the unit’s own turn', () => {
  const s = battle([
    { type: 'furgon', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'archer', team: 'P', x: 6, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  const fu = s.units[0];
  assert.strictEqual(fu.regen, 3);
  fu.hp = 20;
  const heals = () => s.events.filter((e) => e.t === 'heal' && e.uid === fu.uid && e.why === 'regen').length;
  toPlayer(s);
  shuffle(s); // scout (speed 8)
  toPlayer(s);
  shuffle(s); // archer (speed 5)
  assert.strictEqual(fu.hp, 20, 'not on the others’ turns');
  assert.strictEqual(heals(), 0);
  toPlayer(s);
  assert.strictEqual(s.due, fu.uid);
  assert.strictEqual(fu.hp, 23, 'its own turn: +3');
});

test('regen from every source adds up, with no cap', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 4, y: 8, level: 2, talents: ['g_moss'], gear: ['healing_charm'] },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { relics: { P: ['sacred_chalice', 'healing_salve'], E: [] } }
  );
  const g = s.units[0];
  assert.strictEqual(g.regen, 11, 'Living Moss 4 + Healing Charm 3 + Salve 2 + Chalice 2');
  g.hp = 30;
  toPlayer(s);
  assert.strictEqual(g.hp, 41);
});

test('the Healing Salve only adds to regen a unit already has', () => {
  const s = battle(
    [
      { type: 'furgon', team: 'P', x: 2, y: 8 },
      { type: 'knight', team: 'P', x: 6, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { relics: { P: ['healing_salve'], E: [] } }
  );
  const [fu, kn] = s.units;
  assert.strictEqual(fu.regen, 5, 'Furgon 3 + Salve 2');
  assert.strictEqual(kn.regen, 0, 'no regen of its own, none from the Salve');
});

test('regen comes on every unit\'s own turn, acting or passing', () => {
  const s = battle(
    [
      { type: 'knight', team: 'P', x: 2, y: 8 },
      { type: 'knight', team: 'P', x: 6, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { relics: { P: ['sacred_chalice'], E: [] } }
  );
  toPlayer(s);
  const [a, b] = s.units;
  E.pass(s);
  a.hp = 20;
  b.hp = 20;
  a.wait = 1; // a passes its next turn, so b takes the side's turn
  b.cycles = a.cycles;
  E.pass(s);
  assert.strictEqual(s.due, b.uid);
  assert.strictEqual(b.hp, 22, 'b takes the turn: +2');
  assert.strictEqual(a.hp, 22, 'a passed its turn: +2 all the same');
});

test('healers act last on their side, so there is someone to heal by their turn', () => {
  const speeds = Object.values(AG.Data.UNITS).map((T) => T.spd).filter((v) => v > 0);
  for (const k of ['cleric', 'shaman']) assert.strictEqual(AG.Data.UNITS[k].spd, Math.min(...speeds), `${k} is among the slowest`);
  for (const healer of ['cleric', 'shaman']) {
    const s = battle([
      { type: healer, team: 'P', x: 1, y: 8 },
      { type: 'knight', team: 'P', x: 3, y: 8 },
      { type: 'archer', team: 'P', x: 5, y: 8 },
      { type: 'scout', team: 'P', x: 7, y: 8 },
      { type: 'orc', team: 'E', x: 4, y: 0 },
    ]);
    toPlayer(s);
    const order = E.upcoming(s, 'P', 4).map((x) => name(s, x.uid));
    assert.deepStrictEqual(order, ['scout', 'archer', 'knight', healer]);
  }
});

test('poisons from different sources stack: each keeps its own damage and turns, taken all at once', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 4, y: 8 },
    { type: 'archer', team: 'E', x: 2, y: 0 },
    { type: 'wisp', team: 'E', x: 6, y: 0 },
  ]);
  toPlayer(s);
  E.pass(s); // now the enemy's turn
  const [kn, ar, wi] = s.units;
  E.applyStatus(s, ar, kn, { poison: [1, 4] }, ar.act);
  E.applyStatus(s, wi, kn, { poison: [3, 8] }, wi.act);
  assert.deepStrictEqual([kn.poison.dmg, kn.poison.turns, kn.poison.stacks.length], [12, 3, 2]);
  const hits = [];
  for (let round = 0; round < 4; round++) {
    const hp = kn.hp;
    E.pass(s); // the knight's turn starts: every poison on it ticks
    hits.push(hp - kn.hp);
    E.pass(s);
  }
  assert.deepStrictEqual(hits, [12, 8, 8, 0], '4 + 8 together, then the 4 runs out and the 8 goes on alone');
  assert.ok(!kn.poison, 'all worn off');
});

test('the same source poisoning again refreshes its own poison instead of adding another', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 4, y: 8 },
    { type: 'archer', team: 'E', x: 2, y: 0 },
  ]);
  const [kn, ar] = s.units;
  E.applyStatus(s, ar, kn, { poison: [2, 5] }, ar.act);
  E.applyStatus(s, ar, kn, { poison: [2, 5] }, ar.act);
  assert.deepStrictEqual([kn.poison.dmg, kn.poison.turns, kn.poison.stacks.length], [5, 2, 1]);
  // A poison set the old way (one source) still works, and others stack on top of it.
  kn.poison = { turns: 2, dmg: 3, src: 0 };
  E.applyStatus(s, ar, kn, { poison: [1, 5] }, ar.act);
  assert.deepStrictEqual([kn.poison.dmg, kn.poison.turns], [8, 2]);
});

test('the mission done: the win is yours, and both sides tire at once, each from 1: the enemy 1, 2, 3, you 1, 2, 3', () => {
  const s = battle(
    [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'archer', team: 'E', x: 4, y: 4, vip: true },
      { type: 'golem', team: 'E', x: 0, y: 0 },
      { type: 'golem', team: 'E', x: 8, y: 0 },
    ],
    { objective: 'vip' }
  );
  const [kn, cmd, g1, g2] = s.units;
  toPlayer(s);
  cmd.hp = 0;
  cmd.alive = false;
  s.occ[cmd.y * s.w + cmd.x] = 0;
  E.checkOutcome(s);
  assert.ok(s.routed && s.won && !s.over, 'the win is yours, and the battle goes on');
  const before = () => [g1.hp, g2.hp];
  const lost = [];
  const mine = [];
  let hp = before();
  for (let round = 0; round < 3; round++) {
    E.pass(s); // the enemy's turn starts: its unit up tires
    const now = before();
    lost.push(hp[0] - now[0] + hp[1] - now[1]);
    assert.ok((hp[0] - now[0] === 0) !== (hp[1] - now[1] === 0), 'only the unit taking the turn tires');
    hp = now;
    const k = kn.hp;
    E.pass(s); // yours: your knight tires
    mine.push(k - kn.hp);
  }
  assert.deepStrictEqual(lost, [1, 2, 3], 'the enemy: its own count');
  assert.deepStrictEqual(mine, [1, 2, 3], 'yours: your own count, from 1 too');
});

test('the mission done, then your army falls to fatigue: still your win', () => {
  const s = battle(
    [
      { type: 'scout', team: 'P', x: 4, y: 8 },
      { type: 'archer', team: 'E', x: 4, y: 0, vip: true },
      { type: 'golem', team: 'E', x: 0, y: 0 },
    ],
    { objective: 'vip' }
  );
  const [sc, cmd, g] = s.units;
  g.hp = g.maxHp = 999;
  toPlayer(s);
  cmd.hp = 0;
  cmd.alive = false;
  s.occ[cmd.y * s.w + cmd.x] = 0;
  E.checkOutcome(s);
  assert.ok(s.won && !s.over);
  sc.hp = 3; // one fatigue hit or two from the end
  for (let i = 0; i < 20 && !s.over; i++) E.pass(s);
  assert.ok(!sc.alive && s.over, 'your army is gone');
  assert.strictEqual(s.winner, 'P', 'and the win stands');
  assert.ok(s.end.vipSlain && s.end.locked);
});

test('the mission done: Finish now takes the win at once', () => {
  const s = battle(
    [
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'archer', team: 'E', x: 4, y: 0, vip: true },
      { type: 'golem', team: 'E', x: 0, y: 0 },
    ],
    { objective: 'vip' }
  );
  const [, cmd] = s.units;
  toPlayer(s);
  E.endCleanup(s);
  assert.ok(!s.over, 'no win to take before the mission is done');
  cmd.hp = 0;
  cmd.alive = false;
  s.occ[cmd.y * s.w + cmd.x] = 0;
  E.checkOutcome(s);
  E.endCleanup(s);
  assert.ok(s.over && s.winner === 'P' && s.end.vipSlain);
});

// Each side's hits, in order, from a run of events.
const tireSeq = (s, evs, team) => evs.filter((e) => e.t === 'dmg' && e.dmgType === 'fatigue' && s.byId[e.uid].team === team).map((e) => e.amount);
const counting = (seq) => seq.map((_, i) => i + 1);

test('the mission done after turn 30: both timers were on already and simply go on, nothing reset or doubled', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 4, y: 8 },
      { type: 'archer', team: 'E', x: 4, y: 0, vip: true },
      { type: 'golem', team: 'E', x: 0, y: 0 },
    ],
    { objective: 'vip', overtime: 2 }
  );
  const [pg, cmd, eg] = s.units;
  pg.hp = pg.maxHp = eg.hp = eg.maxHp = 999;
  while (!(s.inOvertime && s.turn >= 4 && s.side === 'P')) E.pass(s);
  const nextE = E.fatigueHit(s, 'E');
  const nextP = E.fatigueHit(s, 'P');
  assert.ok(nextE > 1 && nextP > 1);
  cmd.hp = 0;
  cmd.alive = false;
  s.occ[cmd.y * s.w + cmd.x] = 0;
  E.checkOutcome(s);
  const done = s.events.find((e) => e.t === 'routed');
  assert.ok(s.won && done && done.was.E && done.was.P, 'both were on already');
  assert.strictEqual(E.fatigueHit(s, 'E'), nextE, 'the enemy: same next number');
  assert.strictEqual(E.fatigueHit(s, 'P'), nextP, 'yours: same next number');
  const ev = s.events.length;
  E.pass(s);
  E.pass(s);
  assert.deepStrictEqual(tireSeq(s, s.events.slice(ev), 'E'), [nextE]);
  assert.deepStrictEqual(tireSeq(s, s.events.slice(ev), 'P'), [nextP]);
});

test('a mission done early: both timers start at 1 then, and turn 30 does nothing to either', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 4, y: 8 },
      { type: 'archer', team: 'E', x: 4, y: 0, vip: true },
      { type: 'golem', team: 'E', x: 0, y: 0 },
    ],
    { objective: 'vip', overtime: 4 }
  );
  const [pg, cmd, eg] = s.units;
  pg.hp = pg.maxHp = eg.hp = eg.maxHp = 999;
  toPlayer(s);
  cmd.hp = 0;
  cmd.alive = false;
  s.occ[cmd.y * s.w + cmd.x] = 0;
  E.checkOutcome(s);
  assert.ok(s.won && s.turn < 4 && E.fatigueHit(s, 'E') === 1 && E.fatigueHit(s, 'P') === 1, 'both at 1');
  const ev = s.events.length;
  while (s.turn < 9 && !s.over) E.pass(s);
  assert.ok(s.turn >= 9 && !s.over, 'well past turn 4');
  const evs = s.events.slice(ev);
  const on = evs.filter((e) => e.t === 'overtime');
  assert.strictEqual(on.length, 1);
  assert.deepStrictEqual(on[0].was, { E: true, P: true }, 'both already on: turn 4 changes nothing');
  const es = tireSeq(s, evs, 'E');
  const ps = tireSeq(s, evs, 'P');
  assert.ok(es.length >= 5 && ps.length >= 5);
  assert.deepStrictEqual(es, counting(es), 'the enemy: 1, 2, 3 and so on, straight through turn 4');
  assert.deepStrictEqual(ps, counting(ps), 'yours: 1, 2, 3 and so on, straight through turn 4');
});

test('turn 30 with nothing on: both timers start, each at 1', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 4, y: 8 },
      { type: 'golem', team: 'E', x: 0, y: 0 },
    ],
    { overtime: 3 }
  );
  for (const u of s.units) u.hp = u.maxHp = 999;
  const ev = s.events.length;
  while (s.turn < 7 && !s.over) E.pass(s);
  const evs = s.events.slice(ev);
  const on = evs.find((e) => e.t === 'overtime');
  assert.ok(on && on.turn === 3);
  assert.deepStrictEqual(on.was, { E: false, P: false });
  const es = tireSeq(s, evs, 'E');
  const ps = tireSeq(s, evs, 'P');
  assert.ok(es.length >= 3 && ps.length >= 3);
  assert.deepStrictEqual(es, counting(es));
  assert.deepStrictEqual(ps, counting(ps));
});

test('your cleanup on before turn 30: yours carries on through it, and the enemy\'s switches on', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 4, y: 8 },
      { type: 'scout', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 4, loot: [{ id: 'c', kind: 'chest', x: 0, y: 0 }] }
  );
  const [pg, sc] = s.units;
  pg.hp = pg.maxHp = 999;
  sc.hp = 0;
  sc.alive = false;
  s.occ[sc.y * s.w + sc.x] = 0;
  E.checkOutcome(s);
  assert.ok(s.cleanup && s.won && !s.over && s.turn < 4, 'the army fell with a chest left: the cleanup is on');
  assert.ok(E.tiring(s, 'P') && !E.tiring(s, 'E'));
  const ev = s.events.length;
  while (s.turn < 8 && !s.over) E.pass(s);
  assert.ok(s.turn >= 8 && !s.over, 'well past turn 4');
  const evs = s.events.slice(ev);
  const on = evs.filter((e) => e.t === 'overtime');
  assert.strictEqual(on.length, 1);
  assert.deepStrictEqual(on[0].was, { E: false, P: true });
  assert.ok(E.tiring(s, 'E'), 'the enemy\'s timer is on now (nobody left to feel it)');
  const ps = tireSeq(s, evs, 'P');
  assert.ok(ps.length >= 4);
  assert.deepStrictEqual(ps, counting(ps), 'yours: 1, 2, 3 and so on, straight through turn 4');
});

console.log(`queue: ${passed} tests passed`);
