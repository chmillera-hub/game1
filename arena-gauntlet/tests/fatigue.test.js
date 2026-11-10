// Fatigue, checked on real battles: each side its own timer, off until the mission is done,
// the enemy army falls (yours) or the set round comes. Once a side's timer is on, each of
// its units loses that side's number as its turn comes, before it does anything: 1 in the
// timer's first round, one more every round (two more once fatigue is on for everyone, but
// only ever one more for your army once the win is yours). Never a side (or the field) at
// once, never reset or doubled. Plays a few hundred battles of every kind to the end and
// checks every hit.
// Run: node tests/fatigue.test.js [battles per kind]
const assert = require('assert');
const AG = require('./load')();
const R = AG.Run;
const E = AG.Engine;
const D = AG.Data;
const N = +process.argv[2] || 12;

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

// Every rule a stream of battle events must keep. Returns what it saw.
function checkStream(s, events, label) {
  let round = 1;
  let side = null;
  let turnUid = 0; // the unit whose turn it is
  let onAtStart = false; // its side's timer was on as its turn started
  let tired = false; // it has taken its fatigue hit this turn
  let began = false; // it has done something this turn
  const num = { P: 0, E: 0 }; // each side's own number
  const numRound = { P: 0, E: 0 }; // the round that number was set in
  const on = { P: false, E: false }; // each side's timer, as the events switch it on
  let everyone = false; // fatigue on for everyone: from then a number rises by two a round
  let won = false; // the win is yours: your number rises by one, however late
  let hits = 0;
  let early = false; // a timer switched on before round s.overtime
  const sides = new Set();
  const counts = (u) => u && !u.nonCombat && !u.bound && !u.structure;
  // A unit whose side was tiring as its turn started has tired by the time it does anything.
  const closeTurn = () => {
    const u = turnUid && s.byId[turnUid];
    if (u && counts(u) && onAtStart && began) assert.ok(tired, `${label}: unit ${turnUid} (${side}) took its turn with its side tiring, without tiring`);
  };
  for (const e of events) {
    // The timers' switches: the mission done turns on both, the enemy army falling with
    // something left turns on yours, round s.overtime turns on any still off.
    if (e.t === 'routed') {
      assert.deepStrictEqual(e.was, { E: on.E, P: on.P }, `${label}: mission done saw ${JSON.stringify(e.was)}`);
      on.E = on.P = true;
      won = true;
      early = early || !s.overtime || e.turn < s.overtime;
    }
    if (e.t === 'cleanup') {
      assert.strictEqual(e.was, on.P, `${label}: cleanup saw your timer ${e.was ? 'on' : 'off'}`);
      on.P = true;
      won = true;
      early = early || !s.overtime || e.turn < s.overtime;
    }
    if (e.t === 'overtime') {
      assert.strictEqual(e.turn, s.overtime, `${label}: fatigue for everyone on round ${e.turn}, not ${s.overtime}`);
      // Which timers were on already; they carry on untouched.
      assert.deepStrictEqual(e.was, { E: on.E, P: on.P }, `${label}: round ${e.turn} saw ${JSON.stringify(e.was)}`);
      on.E = on.P = true;
      everyone = true;
    }
    if (e.t === 'round') round = e.turn;
    if (e.t === 'turn') {
      closeTurn();
      side = e.side;
      turnUid = e.uid || 0;
      onAtStart = on[side];
      tired = false;
      began = false;
    }
    const own = ['sitout', 'move', 'action', 'done', 'pass'].includes(e.t) && e.uid === turnUid;
    if (own) {
      if (counts(s.byId[e.uid]) && onAtStart) assert.ok(tired, `${label}: unit ${e.uid} (${side}) acted or passed before tiring`);
      began = true;
    }
    if (e.t !== 'dmg' || e.dmgType !== 'fatigue') continue;
    const u = s.byId[e.uid];
    hits++;
    sides.add(u.team);
    assert.ok(on[u.team], `${label}: ${u.team} unit tired before its side's timer was on`);
    // Only the unit whose turn it is, once, and before it does anything.
    assert.strictEqual(e.uid, turnUid, `${label}: unit ${e.uid} tired on unit ${turnUid}'s turn: more than one unit at once`);
    assert.strictEqual(u.team, side, `${label}: ${u.team} unit tired on ${side}'s turn`);
    assert.ok(!tired, `${label}: unit ${e.uid} tired twice in one turn`);
    assert.ok(!began, `${label}: unit ${e.uid} tired after it had started its turn`);
    tired = true;
    // Each side its own number: the same for all its units within a round; the round after,
    // one more, or two more once fatigue is on for everyone (but only ever one more for
    // your army once the win is yours: its victory lap). Never reset, and a hit is never
    // more than the number: nothing doubles it.
    const step = everyone && !(u.team === 'P' && won) ? 2 : 1;
    const want = numRound[u.team] === round ? num[u.team] : num[u.team] === 0 ? 1 : num[u.team] + step;
    assert.strictEqual(e.fatigueNo, want, `${label}: ${u.team} number ${num[u.team]} went to ${e.fatigueNo} in round ${round}`);
    num[u.team] = e.fatigueNo;
    numRound[u.team] = round;
    assert.strictEqual(e.amount, e.fatigueNo, `${label}: number ${e.fatigueNo} dealt ${e.amount}`);
  }
  closeTurn();
  return { hits, sides, early };
}

function play(s, stance, events) {
  for (let guard = 0; guard < 8000 && !s.over; guard++) {
    AG.AI.playTurn(s, s.side, { stance: s.side === 'E' ? stance : 'balanced', temp: 0.6 });
    events.push(...s.events);
    s.events.length = 0;
  }
  assert.ok(s.over, 'the battle ended');
}

test('every battle the game builds runs on the unit rotation, where fatigue comes one unit a side turn', () => {
  const run = R.newRun({ seed: 5, warband: 'ember' });
  run.pending = { type: 'battle', nodeId: 'x', enc: R.genEncounter(run, { id: 'q', row: 2, kind: 'battle' }), attempt: 0, tier: 'medium' };
  assert.strictEqual(R.battleConfig(run, R.autoDeploy(run, 0)).queue, true);
  const h = R.houseArmies();
  assert.strictEqual(R.hallBattleConfig(h[0], h[1], 3).queue, true);
});

const totals = { battles: 0, hits: 0, both: 0, rout: 0, cleanup: 0, early: 0 };
test(`real battles of every kind, fatigue forced in early: ${N} per act and kind`, () => {
  for (const act of [1, 2, 3])
    for (const kind of ['battle', 'elite', 'boss'])
      for (let i = 0; i < N; i++) {
        const run = R.newRun({ seed: 700 + i * 13 + act, warband: D.WARBANDS[i % D.WARBANDS.length].id });
        run.act = act;
        run.xp = [0, 60, 220, 420][act];
        run.boss = D.ACTS[act].bosses[i % D.ACTS[act].bosses.length];
        const enc = R.genEncounter(run, { id: `f${i}`, row: 1 + (i % 3), kind });
        run.pending = { type: 'battle', nodeId: 'x', enc, attempt: 0, tier: kind === 'battle' ? 'medium' : kind };
        const cfg = R.battleConfig(run, R.autoDeploy(run, 0));
        // Fatigue early (turn 4 to 14) in two battles of three, so every battle has plenty of
        // it; the third keeps the real turn, so missions done first get their share too.
        if (i % 3) cfg.overtime = 4 + (i % 11);
        const s = E.createBattle(cfg);
        const events = [];
        play(s, enc.stance, events);
        const r = checkStream(s, events, `act ${act} ${kind} ${enc.name} #${i}`);
        totals.battles++;
        totals.hits += r.hits;
        if (r.sides.size === 2) totals.both++;
        if (s.routed) totals.rout++;
        if (s.cleanup) totals.cleanup++;
        if (r.early) totals.early++;
      }
  assert.ok(totals.hits > 1000 && totals.both > 10, `${totals.hits} hits, ${totals.both} battles with both sides tiring`);
  assert.ok(totals.rout > 5 && totals.cleanup > 5, `routs ${totals.rout}, cleanups ${totals.cleanup}`);
  assert.ok(totals.early > 5, 'battles where a timer switched on before the turn fatigue comes for everyone');
});

test('Hall of Fame matches, fatigue forced in early: the same rules', () => {
  const H = R.houseArmies();
  let hits = 0;
  for (let i = 0; i < 6; i++) {
    const cfg = R.hallBattleConfig(H[i % 4], H[(i + 1) % 4], 40 + i);
    cfg.overtime = 3 + i;
    const s = E.createBattle(cfg);
    const events = [];
    play(s, 'balanced', events);
    hits += checkStream(s, events, `hall ${i}`).hits;
  }
  assert.ok(hits > 50);
});

test('a unit that falls to fatigue as its turn comes has no turn: the next in the order is up', () => {
  let kills = 0;
  let next = 0;
  for (let i = 0; i < 24; i++) {
    const run = R.newRun({ seed: 1700 + i * 7, warband: D.WARBANDS[i % D.WARBANDS.length].id });
    run.act = 1 + (i % 3);
    run.xp = [0, 0, 60, 220][run.act];
    const enc = R.genEncounter(run, { id: 'k' + i, row: 2, kind: 'battle' });
    run.pending = { type: 'battle', nodeId: 'x', enc, attempt: 0, tier: 'medium' };
    const cfg = R.battleConfig(run, R.autoDeploy(run, 0));
    cfg.overtime = 3; // fatigue from round 3: plenty of units fall to it
    const s = E.createBattle(cfg);
    const events = [];
    play(s, enc.stance, events);
    let fell = 0; // the unit that just fell to fatigue as its turn came
    let lastFat = null;
    for (const e of events) {
      if (fell) {
        // Nothing more from it: no move, no action, no pass. The next turn is another's.
        assert.ok(!(['move', 'action', 'pass', 'sitout', 'done'].includes(e.t) && e.uid === fell), `battle ${i}: unit ${fell} fell to fatigue and still took its turn`);
        if (e.t === 'turn') {
          assert.notStrictEqual(e.uid, fell);
          next++;
          fell = 0;
        }
      }
      if (e.t === 'dmg' && e.dmgType === 'fatigue') {
        lastFat = e.uid;
        continue;
      }
      if (e.t === 'death' && e.uid === lastFat) {
        kills++;
        fell = e.uid;
      }
      if (e.t !== 'death') lastFat = null;
    }
  }
  assert.ok(kills > 10, `${kills} units fell to fatigue`);
  assert.ok(next > 10, `${next} times the next unit in the order was up`);
});

test('the checker catches the old way: a whole side tiring at once', () => {
  // Outside the unit queue (only ever used by engine tests) a side tires all at once,
  // which is exactly what the checks above rule out for real battles.
  const s = E.createBattle({ w: 9, h: 9, terrain: new Array(81).fill(0), relics: { P: [], E: [] }, seed: 2, overtime: 1, units: [
    { type: 'golem', team: 'P', x: 2, y: 8 }, { type: 'golem', team: 'P', x: 6, y: 8 }, { type: 'golem', team: 'E', x: 4, y: 0 }] });
  const events = [];
  for (let i = 0; i < 3; i++) {
    E.pass(s);
    events.push(...s.events);
    s.events.length = 0;
  }
  assert.throws(() => checkStream(s, events, 'side at once'), /more than one unit at once|tired twice/);
});

test('an army tires the same whatever its size: every unit by the round\'s number', () => {
  for (const n of [1, 3, 6]) {
    const units = [];
    for (let k = 0; k < n; k++) units.push({ type: 'golem', team: 'P', x: 1 + k, y: 8 });
    units.push({ type: 'golem', team: 'E', x: 4, y: 0 });
    const s = E.createBattle({ w: 9, h: 9, terrain: new Array(81).fill(0), relics: { P: [], E: [] }, seed: 2, queue: true, overtime: 1, units });
    const taken = new Map();
    for (let g = 0; g < 400 && !s.over && s.turn <= 3; g++) {
      E.pass(s);
      for (const e of s.events.splice(0)) if (e.t === 'dmg' && e.dmgType === 'fatigue' && s.byId[e.uid].team === 'P') taken.set(e.uid, (taken.get(e.uid) || []).concat(e.amount));
    }
    // Fatigue for everyone from round 1: 1, then two more each round.
    for (const u of s.units.filter((x) => x.team === 'P')) assert.deepStrictEqual((taken.get(u.uid) || []).slice(0, 3), [1, 3, 5], `${n} units: each takes 1, 3, 5`);
  }
});

console.log(`fatigue: ${passed} tests passed · ${totals.battles} battles, ${totals.hits} fatigue hits checked one by one (${totals.both} with both sides tiring, ${totals.rout} routs, ${totals.cleanup} cleanups, ${totals.early} with a timer on before the set turn)`);
