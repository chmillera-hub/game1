// Fatigue, checked on real battles: one unit at a time, as its own turn comes, the battle's
// next number each time, never a side (or the field) at once. Plays a few hundred battles
// of every kind to the end, fatigue forced in early, and checks every hit.
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
  let last = 0;
  let hits = 0;
  const sides = new Set();
  let on = null; // what turned fatigue on early: a mission done, or the cleanup
  for (const e of events) {
    if ((e.t === 'routed' && !e.already) || e.t === 'cleanup') on = on || e.t;
    // Once fatigue is on, the turn it would set in for everyone adds nothing.
    assert.ok(!(e.t === 'overtime' && on), `${label}: fatigue triggered again on turn ${e.turn} after the ${on}`);
    if (e.t === 'turn') {
      side = e.side;
      open = null;
    }
    if (open && e.uid === open && ['sitout', 'move', 'action', 'pass', 'death'].includes(e.t)) open = null;
    if (e.t !== 'dmg' || e.dmgType !== 'fatigue') continue;
    const u = s.byId[e.uid];
    hits++;
    sides.add(u.team);
    // One count for the battle: 1, 2, 3 ... no number twice, none skipped.
    assert.strictEqual(e.fatigueNo, last + 1, `${label}: hit #${last + 1} came as #${e.fatigueNo}`);
    last = e.fatigueNo;
    // Never more than the number: nothing doubles it.
    assert.strictEqual(e.amount, e.fatigueNo, `${label}: hit #${e.fatigueNo} dealt ${e.amount}`);
    // Only the side whose turn it is, and only once the last unit to tire has had its turn.
    assert.strictEqual(u.team, side, `${label}: ${u.team} unit tired on ${side}'s turn`);
    assert.ok(!open, `${label}: unit ${e.uid} tired while unit ${open} was still taking its turn`);
    open = e.uid;
  }
  return { hits, sides };
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

const totals = { battles: 0, hits: 0, both: 0, rout: 0, cleanup: 0 };
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
        // Fatigue early (turn 4 to 14), so every battle has plenty of it.
        cfg.overtime = 4 + (i % 11);
        const s = E.createBattle(cfg);
        const events = [];
        play(s, enc.stance, events);
        const r = checkStream(s, events, `act ${act} ${kind} ${enc.name} #${i}`);
        totals.battles++;
        totals.hits += r.hits;
        if (r.sides.size === 2) totals.both++;
        if (s.routed) totals.rout++;
        if (s.cleanup) totals.cleanup++;
      }
  assert.ok(totals.hits > 1000 && totals.both > 10, `${totals.hits} hits, ${totals.both} battles with both sides tiring`);
  assert.ok(totals.rout > 5 && totals.cleanup > 5, `routs ${totals.rout}, cleanups ${totals.cleanup}`);
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

console.log(`fatigue: ${passed} tests passed · ${totals.battles} battles, ${totals.hits} fatigue hits checked one by one (${totals.both} with both sides tiring, ${totals.rout} routs, ${totals.cleanup} cleanups)`);
