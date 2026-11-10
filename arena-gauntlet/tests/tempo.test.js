// The pace of a battle: free marching and rest after acting, the two rules that sit on the
// unit rotation (tests/queue.test.js), fatigue as the game plays it (once a side turn), and
// what an attack on several at once feeds its wielder.
// Run: node tests/tempo.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js']);
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
  return E.createBattle(Object.assign({ w: 9, h: 9, terrain: new Array(81).fill(0), units, relics: { P: [], E: [] }, seed: 7, queue: true }, opts));
}

// The enemy's units stay where they are, one after the other, until you are up.
function toPlayer(s) {
  for (let i = 0; i < 60 && !s.over && s.side !== 'P'; i++) E.pass(s);
}

// The due unit steps one tile and is done.
function march(s) {
  const u = s.byId[s.due];
  const spot = [...E.reachable(s, u).values()].find((r) => r.d === 1);
  assert.ok(E.beginActivation(s, u.uid));
  assert.ok(E.moveUnit(s, u.uid, spot.x, spot.y));
  E.finishActivation(s, null);
  E.endTurn(s);
  return u;
}

// The due unit strikes `target` and is done.
function strike(s, target) {
  const u = s.byId[s.due];
  assert.ok(E.beginActivation(s, u.uid), 'the due unit can act');
  assert.ok(E.performAction(s, u.uid, { kind: 'unit', uid: target.uid, ai: 0 }), 'in reach');
  if (s.act) E.finishActivation(s, null);
  E.endTurn(s);
  return u;
}

const drain = (s) => s.events.splice(0);

test('the game plays with both rules on: rest 2, marching free; a battle can switch them off', () => {
  assert.deepStrictEqual(E.TEMPO, { rest: 2, march: true });
  const s = battle([{ type: 'scout', team: 'P', x: 4, y: 8 }, { type: 'golem', team: 'E', x: 4, y: 0 }]);
  assert.strictEqual(s.rest, 2);
  assert.strictEqual(s.march, true);
  const bare = battle([{ type: 'scout', team: 'P', x: 4, y: 8 }, { type: 'golem', team: 'E', x: 4, y: 0 }], { rest: 0, march: false });
  assert.ok(bare.rest === 0 && bare.march === false);
  // Outside the rotation (engine tests only) neither applies.
  const old = battle([{ type: 'scout', team: 'P', x: 4, y: 8 }, { type: 'golem', team: 'E', x: 4, y: 0 }], { queue: false });
  assert.ok(old.rest === 0 && old.march === false);
});

test('marching is free: a unit that only moves hands the turn to the next in line, each unit once', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'archer', team: 'P', x: 6, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  toPlayer(s);
  const turn = s.turn;
  const order = [];
  for (let i = 0; i < 3; i++) {
    assert.strictEqual(s.side, 'P', 'still your turn');
    order.push(march(s).type);
  }
  assert.deepStrictEqual(order, ['scout', 'archer', 'knight'], 'fastest first, the whole army in one turn');
  assert.strictEqual(s.side, 'E', 'everyone has had their go: the enemy is up');
  assert.strictEqual(s.turn, turn + 1);
  // None of them is cooling down or resting: marching costs nothing.
  for (const u of s.units.filter((v) => v.team === 'P')) assert.ok(u.wait === 0 && !E.resting(s, u));
});

test('a turn ends as soon as one unit acts: the units behind it wait for the next', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 0, y: 8 },
    { type: 'scout', team: 'P', x: 8, y: 8 },
    { type: 'archer', team: 'P', x: 4, y: 6 },
    { type: 'golem', team: 'E', x: 4, y: 2 },
  ]);
  const [kn, sc, ar, go] = s.units;
  toPlayer(s);
  assert.strictEqual(s.due, sc.uid);
  march(s); // the scout marches: free
  assert.strictEqual(s.side, 'P');
  assert.strictEqual(s.due, ar.uid);
  const hp = go.hp;
  strike(s, go); // the archer shoots: that is the turn
  assert.ok(go.hp < hp || s.events.some((e) => e.t === 'block'));
  assert.strictEqual(s.side, 'E', 'the turn is over');
  assert.strictEqual(kn.cycles, 0, 'the knight has not had its turn');
  toPlayer(s);
  assert.strictEqual(s.due, kn.uid, 'and is first up next turn');
});

test('a unit that stays put passes silently, and the next in line is up', () => {
  const s = battle([
    { type: 'scout', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'P', x: 2, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  const [sc, kn] = s.units;
  toPlayer(s);
  drain(s);
  E.pass(s);
  assert.ok(s.events.some((e) => e.t === 'sitout' && e.uid === sc.uid && e.why === 'stay'));
  assert.ok(!s.events.some((e) => e.t === 'pass'), 'no side pass yet');
  assert.ok(s.side === 'P' && s.due === kn.uid);
  drain(s);
  E.pass(s);
  assert.strictEqual(s.side, 'E');
  assert.ok(s.events.some((e) => e.t === 'pass' && e.side === 'P'), 'nobody did anything: the side passed');
});

test('catching its breath: a unit that acted sits out its side\'s next two turns', () => {
  const s = battle([
    { type: 'scout', team: 'P', x: 4, y: 4 },
    { type: 'knight', team: 'P', x: 0, y: 8 },
    { type: 'archer', team: 'P', x: 8, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 2, level: 3 },
  ]);
  const [sc, kn, ar, go] = s.units;
  toPlayer(s);
  assert.strictEqual(s.due, sc.uid);
  strike(s, go);
  assert.strictEqual(sc.wait, 0, 'a Scout has no cooldown');
  assert.ok(E.resting(s, sc), 'but it rests');
  const rests = [];
  for (let t = 0; t < 2; t++) {
    toPlayer(s);
    drain(s);
    // The others march; the scout's turn comes and it passes.
    while (s.side === 'P' && !s.over) {
      assert.notStrictEqual(s.due, sc.uid, 'the scout is not up while it rests');
      march(s);
    }
    rests.push(s.events.some((e) => e.t === 'sitout' && e.uid === sc.uid && e.why === 'rest'));
  }
  assert.deepStrictEqual(rests, [true, true], 'two turns of rest, shown as it passes');
  toPlayer(s);
  assert.ok(!E.resting(s, sc));
  // Its turn comes again in the rotation, and it may strike.
  while (s.side === 'P' && s.due !== sc.uid) march(s);
  assert.strictEqual(s.due, sc.uid, 'rested: up again');
  strike(s, go);
  assert.strictEqual(s.side, 'E');
});

test('two fighters cannot keep an army\'s pace: with everyone resting, the turn passes', () => {
  // How many of 9 turns a side acts in, striking whenever a unit is up.
  const actsIn = (mine) => {
    const s = battle(mine.concat([{ type: 'golem', team: 'E', x: 4, y: 3, level: 3 }, { type: 'golem', team: 'E', x: 4, y: 0, level: 3 }]));
    const go = s.units.find((u) => u.team === 'E');
    go.maxHp = go.hp = 9999;
    // (A turn nobody of yours can take passes on its own: the engine moves on to the enemy.)
    let acts = 0;
    for (let g = 0; g < 200 && !s.over && s.turn <= 9; g++) {
      if (s.side === 'P') {
        strike(s, go);
        acts++;
      } else E.pass(s);
    }
    return acts;
  };
  const scout = (x, y) => ({ type: 'scout', team: 'P', x, y: y || 5 });
  assert.strictEqual(actsIn([scout(4)]), 3, 'one: every third turn');
  assert.strictEqual(actsIn([scout(4), scout(3)]), 6, 'two: two turns in three');
  assert.strictEqual(actsIn([scout(4), scout(3), scout(5)]), 9, 'three: every turn');
  assert.strictEqual(actsIn([scout(4), scout(3), scout(5), scout(4, 6)]), 9, 'four: every turn, each unit less often');
});

test('rest comes on top of a cooldown, and the turn order shows it', () => {
  const s = battle([
    { type: 'scout', team: 'P', x: 4, y: 4 },
    { type: 'knight', team: 'P', x: 0, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 2, level: 3 },
  ]);
  const [sc, kn, go] = s.units;
  toPlayer(s);
  strike(s, go);
  // Your next turns: the knight, then the scout's turn comes while it rests.
  const next = E.upcoming(s, 'P', 3);
  assert.strictEqual(next[0].uid, kn.uid);
  const rest = next.flatMap((x) => x.passes).filter((p) => p.uid === sc.uid && p.why === 'rest');
  assert.ok(rest.length >= 1 && rest[0].rest >= 1, 'the scout shows as resting, with the turns left');
  // A Knight (cooldown 1) that acted: cooling down first, then still resting.
  const t = battle([
    { type: 'knight', team: 'P', x: 4, y: 3 },
    { type: 'scout', team: 'P', x: 0, y: 8 },
    { type: 'archer', team: 'P', x: 8, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 2, level: 3 },
  ]);
  const k2 = t.units[0];
  const g2 = t.units[3];
  k2.cycles = -1;
  toPlayer(t);
  assert.strictEqual(t.due, k2.uid);
  strike(t, g2);
  assert.strictEqual(k2.wait, 1);
  const why = [];
  for (let n = 0; n < 2; n++) {
    toPlayer(t);
    drain(t);
    while (t.side === 'P' && !t.over) march(t);
    const e = t.events.find((x) => x.t === 'sitout' && x.uid === k2.uid);
    why.push(e ? e.why : null);
  }
  assert.deepStrictEqual(why, ['cooldown', 'rest']);
});

test('fatigue takes its toll once a side turn, from the first unit up, however many march', () => {
  const s = battle(
    [
      { type: 'scout', team: 'P', x: 2, y: 8 },
      { type: 'archer', team: 'P', x: 4, y: 8 },
      { type: 'knight', team: 'P', x: 6, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { hold: { x: 2, y: 8, need: 1 }, objective: 'hold', overtime: 6 }
  );
  const [sc, ar, kn, go] = s.units;
  // The scout stands on the seal: the mission is done as your first turn starts, and both
  // sides tire from then on. Everyone stays put: each side turn brings every unit's turn.
  const log = [];
  for (let g = 0; g < 60 && !s.over && s.turn < 6; g++) {
    E.pass(s);
    log.push(...drain(s));
  }
  assert.ok(s.routed && E.tiring(s, 'P') && E.tiring(s, 'E'));
  // Between one 'turn' and the next: at most one fatigue hit, on the side whose turn it is,
  // and on the first of its units up (here the Scout, the fastest, every turn: nobody acts).
  const hits = { P: [], E: [] };
  let side = null;
  let inTurn = 0;
  for (const e of log) {
    if (e.t === 'overtime') break; // turn 6: fatigue for everyone, and bigger steps (below)
    if (e.t === 'turn') {
      side = e.side;
      inTurn = 0;
    }
    if (e.t !== 'dmg' || e.dmgType !== 'fatigue') continue;
    const v = s.byId[e.uid];
    assert.strictEqual(v.team, side);
    assert.strictEqual(++inTurn, 1, 'one hit a side turn, not one a unit');
    if (v.team === 'P') assert.strictEqual(v, sc, 'the first unit up');
    hits[v.team].push(e.amount);
  }
  assert.ok(hits.P.length >= 3 && hits.E.length >= 3);
  // Each side its own count, from 1, one more a turn (before fatigue is on for everyone).
  assert.deepStrictEqual(hits.P, hits.P.map((_, i) => i + 1));
  assert.deepStrictEqual(hits.E, hits.E.map((_, i) => i + 1));
  assert.ok(ar.hp === ar.maxHp && kn.hp === kn.maxHp, 'the others marched (or stood) for free');
  void go;
  const u = battle([{ type: 'golem', team: 'P', x: 4, y: 8 }, { type: 'knight', team: 'P', x: 2, y: 8 }, { type: 'golem', team: 'E', x: 4, y: 0 }], { overtime: 1 });
  // Fatigue on for everyone from the first turn: from 1, then two more each turn.
  const late = [];
  for (let g = 0; g < 40 && late.length < 4 && !u.over; g++) {
    E.pass(u);
    for (const e of drain(u)) if (e.t === 'dmg' && e.dmgType === 'fatigue' && u.byId[e.uid].team === 'P') late.push(e.amount);
  }
  assert.deepStrictEqual(late, [1, 3, 5, 7], 'from 1, then two more each turn once fatigue is on for everyone');
  assert.strictEqual(E.fatigueHit(u, 'P'), 9);
  // The victory lap: once the win is yours, your army tires by one more a turn however late
  // it is (time to gather what is left); the beaten side still tires by two.
  const w = battle(
    [
      { type: 'golem', team: 'P', x: 2, y: 8 },
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { hold: { x: 2, y: 8, need: 1 }, objective: 'hold', overtime: 1 }
  );
  const lap = { P: [], E: [] };
  for (let g = 0; g < 60 && lap.P.length < 4 && !w.over; g++) {
    E.pass(w);
    for (const e of drain(w)) if (e.t === 'dmg' && e.dmgType === 'fatigue') lap[w.byId[e.uid].team].push(e.amount);
  }
  assert.ok(w.won && w.routed, 'the seal is held: the win is yours');
  assert.deepStrictEqual(lap.P, [1, 2, 3, 4], 'your army: one more a turn');
  assert.deepStrictEqual(lap.E.slice(0, 3), [1, 3, 5], 'theirs: two more a turn');
});

test('an attack that strikes several at once feeds on its hardest hit only', () => {
  const s = battle(
    [
      { type: 'pyromancer', team: 'P', x: 4, y: 7, skills: ['vampiric'] },
      { type: 'orc', team: 'E', x: 4, y: 4 },
      { type: 'crossbow', team: 'E', x: 5, y: 4 },
      { type: 'crossbow', team: 'E', x: 3, y: 4 },
    ],
    { rest: 0, march: false }
  );
  const [py, orc] = s.units;
  toPlayer(s);
  py.hp = 5;
  drain(s);
  assert.ok(E.beginActivation(s, py.uid));
  assert.ok(E.performAction(s, py.uid, { kind: 'tile', x: 4, y: 4, ai: 0 }));
  const dealt = s.events.filter((e) => e.t === 'dmg' && e.src === py.uid).map((e) => e.amount);
  assert.ok(dealt.length >= 3, `the blast caught ${dealt.length}`);
  const healed = s.events.filter((e) => e.t === 'heal' && e.uid === py.uid).reduce((t, e) => t + e.amount, 0);
  assert.strictEqual(healed, Math.round(Math.max(...dealt) * 0.3), 'not 30% of the lot');
  assert.ok(healed < Math.round(dealt.reduce((a, b) => a + b, 0) * 0.3));
  // One target: 30% of the blow, as ever.
  const t = battle([{ type: 'berserker', team: 'P', x: 4, y: 5, skills: ['vampiric'] }, { type: 'orc', team: 'E', x: 4, y: 4, facing: 0 }], { rest: 0, march: false });
  const [bz, o2] = t.units;
  toPlayer(t);
  bz.hp = 5;
  drain(t);
  assert.ok(E.beginActivation(t, bz.uid));
  assert.ok(E.performAction(t, bz.uid, { kind: 'unit', uid: o2.uid, ai: 0 }));
  const hit = t.events.filter((e) => e.t === 'dmg' && e.src === bz.uid).map((e) => e.amount);
  const got = t.events.filter((e) => e.t === 'heal' && e.uid === bz.uid).reduce((a, e) => a + e.amount, 0);
  if (hit.length) assert.strictEqual(got, Math.max(1, Math.round(hit[0] * 0.3)));
  void orc;
});

console.log(`tempo: ${passed} tests passed`);
