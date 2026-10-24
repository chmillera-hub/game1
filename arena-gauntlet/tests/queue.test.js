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

test('overtime: fighters lose 2 more HP each round, past armor and shields', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 4, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2 }
  );
  const [pg, eg] = s.units;
  pg.shield = 50;
  E.pass(s); // the enemy's turn 1
  assert.strictEqual(pg.hp, pg.maxHp, 'no overtime yet');
  E.pass(s); // your turn 1; the enemy's turn 2 opens overtime
  assert.ok(s.events.some((e) => e.t === 'overtime'));
  assert.strictEqual(eg.hp, eg.maxHp - 2);
  E.pass(s);
  assert.strictEqual(pg.hp, pg.maxHp - 2, 'shields do not stop it');
  E.pass(s);
  assert.strictEqual(eg.hp, eg.maxHp - 2 - 4, 'and it grows each round');
});

test('overtime: the bigger side outlasts the smaller, and reinforcements stop', () => {
  const s = battle(
    [
      { type: 'golem', team: 'P', x: 4, y: 8 },
      { type: 'scout', team: 'E', x: 4, y: 0 },
    ],
    { overtime: 2, waves: [{ turn: 5, team: 'E', tiles: [[0, 0], [1, 0]], units: [{ type: 'warg' }] }] }
  );
  for (let i = 0; i < 200 && !s.over; i++) E.pass(s);
  assert.ok(s.over);
  assert.strictEqual(s.winner, 'P', 'the golem outlasts the scout');
  assert.ok(!s.timeout);
  assert.ok(!s.units.some((u) => u.type === 'warg'), 'the warg never came');
});

console.log(`queue: ${passed} tests passed`);
