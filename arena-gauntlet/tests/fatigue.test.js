// Fatigue, checked on real battles: each side its own timer, off until the mission is done,
// the enemy army falls (yours) or the set turn comes, then 1, 2, 3 for that side, one unit
// at a time as its own turn comes, never a side (or the field) at once, never reset or
// doubled. Plays a few hundred battles of every kind to the end and checks every hit.
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
  let side = null;
  let open = null; // the unit that has just tired and whose turn is not over yet
  const last = { P: 0, E: 0 }; // each side's own count
  const on = { P: false, E: false }; // each side's timer, as the events switch it on
  let hits = 0;
  let early = false; // a timer switched on before turn s.overtime
  const sides = new Set();
  let tired = new Set(); // units that tired this side's turn
  let midTurn = false; // a timer switched on partway through this turn: from the next one
  for (const e of events) {
    if (['routed', 'cleanup', 'overtime'].includes(e.t)) midTurn = e.t !== 'overtime';
    // The timers' switches: the mission done turns on both, the enemy army falling with
    // something left turns on yours, turn s.overtime turns on any still off.
    if (e.t === 'routed') {
      assert.deepStrictEqual(e.was, { E: on.E, P: on.P }, `${label}: mission done saw ${JSON.stringify(e.was)}`);
      on.E = on.P = true;
      early = early || !s.overtime || e.turn < s.overtime;
    }
    if (e.t === 'cleanup') {
      assert.strictEqual(e.was, on.P, `${label}: cleanup saw your timer ${e.was ? 'on' : 'off'}`);
      on.P = true;
      early = early || !s.overtime || e.turn < s.overtime;
    }
    if (e.t === 'overtime') {
      assert.strictEqual(e.turn, s.overtime, `${label}: fatigue for everyone on turn ${e.turn}, not ${s.overtime}`);
      // Which timers were on already; they carry on untouched.
      assert.deepStrictEqual(e.was, { E: on.E, P: on.P }, `${label}: turn ${e.turn} saw ${JSON.stringify(e.was)}`);
      on.E = on.P = true;
    }
    if (e.t === 'turn') {
      side = e.side;
      open = null;
      tired = new Set();
      midTurn = false;
    }
    // Once a side's timer is on, a unit of it (one that counts) passing, moving or acting
    // has tired first this turn.
    const own = ['sitout', 'move', 'action'].includes(e.t) || (e.t === 'pass' && e.uid && !e.auto);
    if (own && !midTurn && e.uid && s.byId[e.uid] && s.byId[e.uid].team === side && on[side]) {
      const u = s.byId[e.uid];
      if (!u.nonCombat && !u.bound && !u.structure) assert.ok(tired.has(u.uid), `${label}: unit ${u.uid} (${u.team}) took its turn with its side tiring, without tiring`);
    }
    if (open && e.uid === open && ['sitout', 'move', 'action', 'pass', 'death'].includes(e.t)) open = null;
    if (e.t !== 'dmg' || e.dmgType !== 'fatigue') continue;
    const u = s.byId[e.uid];
    hits++;
    sides.add(u.team);
    assert.ok(on[u.team], `${label}: ${u.team} unit tired before its side's timer was on`);
    // Each side its own count: 1, 2, 3 ... no number twice, none skipped, never reset.
    assert.strictEqual(e.fatigueNo, last[u.team] + 1, `${label}: ${u.team} hit #${last[u.team] + 1} came as #${e.fatigueNo}`);
    last[u.team] = e.fatigueNo;
    // Never more than the number: nothing doubles it.
    assert.strictEqual(e.amount, e.fatigueNo, `${label}: hit #${e.fatigueNo} dealt ${e.amount}`);
    // Only the side whose turn it is, and only once the last unit to tire has had its turn.
    assert.strictEqual(u.team, side, `${label}: ${u.team} unit tired on ${side}'s turn`);
    assert.ok(!open, `${label}: unit ${e.uid} tired while unit ${open} was still taking its turn`);
    open = e.uid;
    tired.add(e.uid);
  }
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

test('every battle the game builds runs on the unit rotation, where fatigue comes one unit at a time', () => {
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

test('a unit that falls to fatigue as its turn comes ends its side\'s turn: the other side moves next, never a chain', () => {
  let kills = 0;
  let handedOver = 0;
  for (let i = 0; i < 24; i++) {
    const run = R.newRun({ seed: 1700 + i * 7, warband: D.WARBANDS[i % D.WARBANDS.length].id });
    run.act = 1 + (i % 3);
    run.xp = [0, 0, 60, 220][run.act];
    const enc = R.genEncounter(run, { id: 'k' + i, row: 2, kind: 'battle' });
    run.pending = { type: 'battle', nodeId: 'x', enc, attempt: 0, tier: 'medium' };
    const cfg = R.battleConfig(run, R.autoDeploy(run, 0));
    cfg.overtime = 3; // fatigue from turn 3: plenty of units fall to it
    const s = E.createBattle(cfg);
    const events = [];
    play(s, enc.stance, events);
    let fell = null; // the side whose unit just fell to fatigue, until the next side's turn
    let lastFat = null;
    for (const e of events) {
      if (e.t === 'turn') {
        if (fell && e.side !== fell) handedOver++;
        fell = null;
        continue;
      }
      if (e.t === 'dmg' && e.dmgType === 'fatigue') {
        const u = s.byId[e.uid];
        assert.ok(!(fell && u.team === fell), `battle ${i}: after a unit fell to fatigue, another of its side tired before the other side moved`);
        lastFat = e.uid;
        continue;
      }
      if (e.t === 'death' && e.uid === lastFat) {
        kills++;
        fell = s.byId[e.uid].team;
      }
      if (e.t !== 'death') lastFat = null;
    }
  }
  assert.ok(kills > 10, `${kills} units fell to fatigue`);
  assert.ok(handedOver > 5, `${handedOver} times the other side moved next`);
});

test('the checker catches the old way: a whole side tiring at once', () => {
  // Outside the unit rotation (only ever used by engine tests) a side tires all at once,
  // which is exactly what the checks above rule out for real battles.
  const s = E.createBattle({ w: 9, h: 9, terrain: new Array(81).fill(0), relics: { P: [], E: [] }, seed: 2, overtime: 1, units: [
    { type: 'golem', team: 'P', x: 2, y: 8 }, { type: 'golem', team: 'P', x: 6, y: 8 }, { type: 'golem', team: 'E', x: 4, y: 0 }] });
  const events = [];
  for (let i = 0; i < 3; i++) {
    E.pass(s);
    events.push(...s.events);
    s.events.length = 0;
  }
  assert.throws(() => checkStream(s, events, 'side at once'), /still taking its turn/);
});

console.log(`fatigue: ${passed} tests passed · ${totals.battles} battles, ${totals.hits} fatigue hits checked one by one (${totals.both} with both sides tiring, ${totals.rout} routs, ${totals.cleanup} cleanups, ${totals.early} with a timer on before the set turn)`);
