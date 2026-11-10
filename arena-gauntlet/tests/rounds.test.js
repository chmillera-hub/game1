// Rounds: how a battle is played. In a round every unit of both armies takes one turn, in
// order of Speed, fastest first, whichever side it is on; equal Speeds alternate between
// the sides, yours first. A unit cooling down still has its turn, to move in. What used to
// open and close a side's turn frames the round: hazards, the shrine, reinforcements,
// wagons. (The older tempo, where the sides alternate: tests/queue.test.js, tempo.test.js.)
// Run: node tests/rounds.test.js
const assert = require('assert');
const AG = require('./load')();
const E = AG.Engine;
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

function battle(units, opts = {}) {
  return E.createBattle(Object.assign({ w: 9, h: 9, terrain: new Array(81).fill(0), units, relics: { P: [], E: [] }, seed: 7, queue: true }, opts));
}
const drain = (s) => s.events.splice(0);
const due = (s) => s.byId[s.due];
// Everyone holds their ground until round `n` opens; returns the units whose turns came,
// round by round.
function passUntil(s, n) {
  const turns = {};
  const note = () => {
    for (const e of drain(s)) if (e.t === 'turn') (turns[e.turn] = turns[e.turn] || []).push(e.uid);
  };
  note();
  for (let g = 0; g < 500 && !s.over && s.turn < n; g++) {
    E.pass(s);
    note();
  }
  return turns;
}
// The unit whose turn it is strikes `target` and is done.
function strike(s, target) {
  const u = due(s);
  assert.ok(E.beginActivation(s, u.uid), 'the unit whose turn it is can act');
  assert.ok(E.performAction(s, u.uid, { kind: 'unit', uid: target.uid, ai: 0 }), 'in reach');
  if (s.act) E.finishActivation(s, null);
  E.endTurn(s);
  return u;
}

test('the game plays in rounds: every unit of both armies takes one turn a round, fastest first', () => {
  assert.strictEqual(E.TEMPO.rounds, true);
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 8 }, // Speed 2
    { type: 'scout', team: 'P', x: 4, y: 8 }, // 8
    { type: 'cleric', team: 'P', x: 6, y: 8 }, // 1
    { type: 'orc', team: 'E', x: 2, y: 0 }, // 3
    { type: 'wolf', team: 'E', x: 4, y: 0 }, // 7
    { type: 'goblin_archer', team: 'E', x: 6, y: 0 }, // 6
  ]);
  assert.ok(s.rounds && s.rest === 0 && s.march === false);
  const [kn, sc, cl, orc, wolf, gob] = s.units;
  const order = [sc, wolf, gob, orc, kn, cl].map((u) => u.uid);
  assert.deepStrictEqual(s.order, order, 'by Speed, whichever side');
  assert.deepStrictEqual(E.initiative(s), order);
  assert.strictEqual(s.turn, 1);
  assert.strictEqual(due(s), sc, 'the fastest unit opens the battle');
  assert.strictEqual(s.side, 'P', 'the side to move is the side of the unit whose turn it is');
  const turns = passUntil(s, 4);
  for (const r of [1, 2, 3]) assert.deepStrictEqual(turns[r], order, `round ${r}: everyone once, in order`);
  assert.strictEqual(s.turn, 4, 'the counter counts rounds');
  assert.strictEqual(due(s), sc);
});

test('equal Speeds alternate between the sides, yours first', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 1, y: 8 },
    { type: 'knight', team: 'P', x: 3, y: 8 },
    { type: 'knight', team: 'P', x: 5, y: 8 },
    { type: 'knight', team: 'E', x: 1, y: 0 },
    { type: 'knight', team: 'E', x: 3, y: 0 },
  ]);
  const [p1, p2, p3, e1, e2] = s.units;
  assert.deepStrictEqual(s.order, [p1, e1, p2, e2, p3].map((u) => u.uid));
  // And a faster unit goes before all of them, whichever side it is on.
  const t = battle([
    { type: 'knight', team: 'P', x: 1, y: 8 },
    { type: 'knight', team: 'E', x: 1, y: 0 },
    { type: 'warg', team: 'E', x: 3, y: 0 },
  ]);
  assert.deepStrictEqual(t.order.map((uid) => t.byId[uid].type + t.byId[uid].team), ['wargE', 'knightP', 'knightE']);
});

test('more units, more turns: a side takes as many turns a round as it has units', () => {
  for (const n of [1, 2, 4, 7]) {
    const units = [];
    for (let k = 0; k < n; k++) units.push({ type: 'scout', team: 'P', x: 1 + k, y: 8 });
    units.push({ type: 'golem', team: 'E', x: 4, y: 0 });
    const s = battle(units);
    const turns = passUntil(s, 3);
    const mine = (r) => turns[r].filter((uid) => s.byId[uid].team === 'P').length;
    assert.deepStrictEqual([mine(1), mine(2)], [n, n], `${n} units: ${n} turns a round`);
  }
});

test('acting starts the cooldown: the unit\'s turn still comes every round, to move in, not to act', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'golem', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [kn, go] = s.units;
  go.hp = go.maxHp = 999;
  assert.strictEqual(due(s), kn, 'the Knight (Speed 2) before the Golem (1)');
  strike(s, go);
  assert.strictEqual(kn.wait, D.UNITS.knight.rec, 'cooling down');
  passUntil(s, 2);
  // Round 2: its turn comes all the same.
  assert.strictEqual(due(s), kn);
  assert.ok(E.recovering(s, kn) && E.canActivate(s, kn), 'it has its turn');
  assert.ok(!E.actUsable(s, kn, 0) && E.allTargets(s, kn).length === 0, 'but it cannot act');
  assert.ok(E.beginActivation(s, kn.uid));
  assert.strictEqual(E.performAction(s, kn.uid, { kind: 'unit', uid: go.uid, ai: 0 }), false);
  const spot = [...E.reachable(s, kn).values()].find((r) => r.d === 1);
  assert.ok(E.moveUnit(s, kn.uid, spot.x, spot.y), 'it may move');
  E.finishActivation(s, null);
  assert.strictEqual(kn.wait, 0, 'the turn counted off its cooldown');
  E.endTurn(s);
  passUntil(s, 3);
  assert.ok(due(s) === kn && !E.recovering(s, kn) && E.actUsable(s, kn, 0), 'round 3: ready again');
  // Staying put while cooling down counts the cooldown off too, quietly.
  const t = battle([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'golem', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  t.units[1].hp = t.units[1].maxHp = 999;
  strike(t, t.units[1]);
  passUntil(t, 2);
  drain(t);
  E.pass(t);
  const ev = drain(t).find((e) => e.t === 'pass' && e.uid === t.units[0].uid);
  assert.ok(ev && ev.cool && ev.wait === 1);
  assert.strictEqual(t.units[0].wait, 0);
});

test('a unit cooling down that cannot move, and a paralyzed one, pass their turn', () => {
  const s = battle([
    { type: 'lightning', team: 'P', x: 4, y: 5 },
    { type: 'knight', team: 'P', x: 0, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 3, facing: 0 },
  ]);
  const [ward, kn, go] = s.units;
  go.hp = go.maxHp = 999;
  // The ward (Speed 3) is up first and strikes; next round it is cooling down, rooted to
  // the spot as it always is.
  assert.strictEqual(due(s), ward);
  const target = E.targetsFrom(s, ward, 0)[0];
  assert.ok(target, 'the Golem is in its reach');
  assert.ok(E.beginActivation(s, ward.uid) && E.performAction(s, ward.uid, target));
  if (s.act) E.finishActivation(s, null);
  E.endTurn(s);
  assert.ok(ward.wait > 0);
  kn.para = 2;
  const sit = [];
  for (let g = 0; g < 40 && s.turn < 3; g++) {
    if (s.due) E.pass(s);
    for (const e of drain(s)) if (e.t === 'sitout') sit.push(`${s.byId[e.uid].type}:${e.why}`);
  }
  assert.ok(sit.includes('lightning:cooldown'), `the ward passes while it cools down (${sit})`);
  assert.ok(sit.includes('knight:para'), 'the paralyzed Knight passes');
});

test('whoever joins a round under way has its first turn in the next', () => {
  const s = battle(
    [
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'orc', team: 'E', x: 4, y: 0 },
    ],
    { waves: [{ turn: 1, tiles: [[0, 0], [8, 0]], units: [{ type: 'wolf' }] }] }
  );
  const turns = passUntil(s, 3);
  const wolf = s.units.find((u) => u.type === 'wolf');
  assert.ok(wolf && wolf.reinforcement, 'the wave landed as round 1 closed');
  assert.ok(!turns[1].includes(wolf.uid), 'no turn in the round it arrived in');
  assert.strictEqual(turns[2][0], wolf.uid, 'round 2: its first turn (and it is the fastest)');
  // A unit added in the middle of a round waits for the next too.
  const t = battle([
    { type: 'knight', team: 'P', x: 4, y: 8 },
    { type: 'orc', team: 'E', x: 4, y: 0 },
  ]);
  const late = E.addUnit(t, { type: 'scout', team: 'P', x: 0, y: 8 });
  const tt = passUntil(t, 3);
  assert.ok(!tt[1] || !tt[1].includes(late.uid));
  assert.strictEqual(tt[2][0], late.uid);
});

test('what frames a round: the shrine counts round starts, fire burns out, wagons roll as it closes', () => {
  // The shrine: a unit standing on it as two rounds in a row open.
  const s = battle(
    [
      { type: 'knight', team: 'P', x: 4, y: 4 },
      { type: 'golem', team: 'E', x: 0, y: 0 },
    ],
    { objective: 'hold', hold: { x: 4, y: 4, need: 2 } }
  );
  assert.strictEqual(s.hold.count, 1, 'round 1 opens with the Knight on it');
  assert.ok(!s.routed);
  passUntil(s, 2);
  assert.ok(s.routed && s.routed.held, 'round 2 opens: held');
  // Wagons roll once a round, as it closes.
  const c = battle(
    [
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'cart', team: 'E', x: 6, y: 4, goal: true },
      { type: 'orc', team: 'E', x: 8, y: 0 },
    ],
    { objective: 'destroy', cartExit: 0 }
  );
  const cart = c.units[1];
  const x0 = cart.x;
  E.pass(c);
  assert.strictEqual(cart.x, x0, 'not in the middle of a round');
  passUntil(c, 2);
  assert.ok(cart.x < x0, 'it rolled as round 1 closed');
  const x1 = cart.x;
  passUntil(c, 3);
  assert.ok(cart.x < x1, 'and again as round 2 closed');
});

test('the turn order: the unit whose turn it is, the rest of this round, then the next', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'scout', team: 'P', x: 0, y: 8 },
    { type: 'golem', team: 'E', x: 4, y: 4, facing: 0 },
    { type: 'barrier', team: 'P', x: 8, y: 8 },
  ]);
  const [kn, sc, go, ward] = s.units;
  go.hp = go.maxHp = 999;
  let list = E.turnOrder(s, 8);
  assert.deepStrictEqual(list.slice(0, 4).map((x) => [x.uid, x.round]), [[sc.uid, 1], [kn.uid, 1], [go.uid, 1], [ward.uid, 1]]);
  assert.deepStrictEqual(list.slice(4, 8).map((x) => [x.uid, x.round]), [[sc.uid, 2], [kn.uid, 2], [go.uid, 2], [ward.uid, 2]]);
  assert.strictEqual(list[3].why, 'passive', 'a Barrier Ward never acts');
  // Each is assumed to act when it can: the Knight (Cooldown 1) cools down next round, the
  // Golem (1) too, the Scout (0) never.
  assert.ok(list[5].cool && !list[5].why && list[5].wait === 1, 'the Knight will be cooling down: it moves, it does not act');
  assert.ok(!list[4].cool && !list[4].why);
  // After the Scout holds and the Knight strikes: the Knight is next round's second.
  E.pass(s);
  strike(s, go);
  list = E.turnOrder(s, 6);
  assert.strictEqual(list[0].uid, go.uid, 'the unit whose turn it is comes first');
  const knNext = list.find((x) => x.uid === kn.uid);
  assert.ok(knNext.round === 2 && knNext.cool && knNext.wait === 1);
  // Paralysis shows as a pass.
  sc.para = 1;
  const scNext = E.turnOrder(s, 6).find((x) => x.uid === sc.uid);
  assert.strictEqual(scNext.why, 'para');
});

test('a mark counts the marked unit\'s own turns, like every other status', () => {
  const s = battle([
    { type: 'scout', team: 'P', x: 4, y: 5 },
    { type: 'golem', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [sc, go] = s.units;
  go.hp = go.maxHp = 999;
  E.applyStatus(s, sc, go, { mark: 2 }, sc.act);
  assert.strictEqual(go.mark, 2);
  E.pass(s); // the Scout's turn; then the Golem's comes
  assert.strictEqual(go.mark, 2, 'not while others take their turns');
  E.pass(s); // the Golem's own turn ends
  assert.strictEqual(go.mark, 1);
  passUntil(s, 3);
  assert.strictEqual(go.mark, 0, 'gone after its second turn');
});

test('the War Drum of Ages beats every fourth round', () => {
  const s = battle(
    [
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { relics: { P: ['echo_drum'], E: [] } }
  );
  const beats = [];
  for (let g = 0; g < 200 && s.turn <= 9; g++) {
    E.pass(s);
    for (const e of drain(s)) if (e.t === 'wardrum') beats.push(s.turn);
  }
  assert.deepStrictEqual(beats, [4, 8]);
});

test('the older tempo is still there, switched off: the sides alternate, one unit a turn', () => {
  const s = battle(
    [
      { type: 'scout', team: 'P', x: 2, y: 8 },
      { type: 'knight', team: 'P', x: 6, y: 8 },
      { type: 'wolf', team: 'E', x: 2, y: 0 },
      { type: 'orc', team: 'E', x: 6, y: 0 },
    ],
    { rounds: false, rest: 0, march: false }
  );
  assert.ok(!s.rounds && s.queue);
  const sides = [];
  for (let g = 0; g < 6; g++) {
    sides.push(s.side);
    E.pass(s);
  }
  assert.deepStrictEqual(sides, ['E', 'P', 'E', 'P', 'E', 'P']);
});

test('every battle the game builds is played in rounds, to the end, by the AI on both sides', () => {
  let rounds = 0;
  let n = 0;
  for (let i = 0; i < 9; i++) {
    const run = R.newRun({ seed: 300 + i, warband: D.WARBANDS[i % D.WARBANDS.length].id });
    run.act = 1 + (i % 3);
    run.xp = [0, 30, 150, 300][run.act];
    const tier = ['easy', 'medium', 'elite'][i % 3];
    const enc = R.genEncounter(run, { id: 'r' + i, row: 2, kind: tier === 'elite' ? 'elite' : 'battle', tier, mult: R.TIERS[tier].mult }, null, []);
    run.offer = null;
    run.pending = { type: 'battle', nodeId: 'n', node: { id: 'n' }, tier, enc, attempt: 0 };
    const cfg = R.battleConfig(run, R.autoDeploy(run, 0));
    assert.ok(cfg.queue);
    const s = E.createBattle(cfg);
    assert.ok(s.rounds);
    // Within a round nobody takes two turns, and the order is by Speed.
    let round = s.turn;
    let seen = new Set();
    let lastSpd = Infinity;
    const check = () => {
      for (const e of drain(s)) {
        if (e.t === 'round') {
          round = e.turn;
          seen = new Set();
          lastSpd = Infinity;
        }
        if (e.t !== 'turn') continue;
        assert.ok(!seen.has(e.uid), `unit ${e.uid} took two turns in round ${round}`);
        seen.add(e.uid);
        const spd = s.byId[e.uid].spd;
        assert.ok(spd <= lastSpd, `round ${round}: Speed ${spd} after ${lastSpd}`);
        lastSpd = spd;
      }
    };
    check();
    for (let g = 0; g < 6000 && !s.over; g++) {
      AG.AI.playTurn(s, s.side, s.side === 'E' ? { stance: enc.stance, temp: 1.2 } : { stance: 'balanced', temp: 0.3 });
      check();
    }
    assert.ok(s.over, 'the battle ended');
    rounds += s.turn;
    n++;
  }
  assert.ok(rounds / n >= 4 && rounds / n <= R.BAL.overtime + 10, `about ${(rounds / n).toFixed(1)} rounds a battle`);
});

console.log(`rounds: ${passed} tests passed`);
