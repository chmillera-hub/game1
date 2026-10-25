// The Hall of Fame: every won campaign enters its final army at the bottom, then climbs by
// beating the army right above it. Run: node tests/hall.test.js
const assert = require('assert');
const store = {};
globalThis.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => (store[k] = String(v)), removeItem: (k) => delete store[k] };
const AG = require('./load')();
const R = AG.Run;
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

const HALL = 'arena-gauntlet-hall-v1';
const clearHall = () => delete store[HALL];

// Win the battle at hand without fighting it (the reward logic runs as after a real win).
function win(run) {
  const dep = R.autoDeploy(run, 0);
  const s = E.createBattle(R.battleConfig(run, dep));
  s.over = true;
  s.winner = 'P';
  R.finishBattle(run, s, dep);
  const p = run.pending;
  if (p.bossRelics && !p.bossRelicTaken) R.takeBossRelic(run, p.bossRelics[0]);
  if (p.tome && !p.tomeTaken) R.skipTome(run);
  if (!p.spoilTaken) R.skipSpoils(run);
  R.completeNode(run);
}

function advance(run) {
  const p = run.pending;
  if (!p) {
    const i = run.offer.findIndex((o) => o.tier === 'medium');
    assert.ok(R.chooseChallenge(run, i < 0 ? 0 : i));
    return win(run);
  }
  if (p.type === 'shop') return R.completeNode(run);
  if (p.type === 'event') {
    const c = R.eventChoices(run).filter((x) => x.enabled && !x.pick).pop();
    R.chooseEvent(run, c.id, null);
    if (run.pending.type === 'battle') return win(run);
    return R.completeNode(run);
  }
  throw new Error('unexpected ' + p.type);
}

function winCampaign(seed) {
  const run = R.newRun({ seed, warband: 'vanguard' });
  for (let guard = 0; !run.won && guard < 60; guard++) advance(run);
  assert.ok(run.won);
  return run;
}

// A made-up legend: one unit of a type at a spot, for ladder tests that need no real armies.
const fake = (id, type) => ({ id, name: id, wins: 0, losses: 0, climbed: false, level: 1, relics: [], units: [{ spec: { type, level: 1 }, x: 4, y: 7, facing: 0 }] });

test('winning a campaign saves its final army at once: the first takes #1, later ones wait in line', () => {
  clearHall();
  const run = winCampaign(21);
  let h = R.loadHall();
  assert.strictEqual(h.legends.length, 1);
  const L = h.legends[0];
  assert.strictEqual(L.id, run.legendId);
  assert.ok(/^The \w+ \w+$/.test(L.name), L.name);
  assert.ok(L.units.length > 0 && L.units.every((u) => u.spec && u.spec.type && u.x != null && u.y != null));
  assert.ok(L.units.every((u) => u.spec.rid == null), 'no ties to the old campaign');
  assert.deepStrictEqual(L.relics, run.relics);
  assert.ok(L.climbed, 'the first army has no one to climb past');
  assert.ok(!R.hallNext(h, L.id));

  const run2 = winCampaign(22);
  h = R.loadHall();
  assert.strictEqual(h.legends.length, 1);
  assert.strictEqual(h.queue.length, 1, 'saved right away, waiting to climb');
  assert.strictEqual(h.queue[0].id, run2.legendId);
  assert.deepStrictEqual(R.hallPlace(h, run2.legendId), { inLine: 1 });
  assert.ok(!R.hallClimber(h), 'nothing climbs until you start it');
  const l = R.hallStart();
  h = R.loadHall();
  assert.strictEqual(l.id, run2.legendId);
  assert.strictEqual(h.legends[1].id, run2.legendId, 'it starts at the bottom');
  assert.ok(!h.legends[1].climbed && !h.queue.length);
  assert.strictEqual(R.hallNext(h, run2.legendId).id, run.legendId, 'and faces the army above it');
});

test('the final challenge updates the same entry, crowned', () => {
  clearHall();
  const run = winCampaign(23);
  assert.ok(R.faceFinal(run));
  R.chooseChallenge(run, 0);
  win(run);
  assert.ok(run.superWon);
  const h = R.loadHall();
  assert.strictEqual(h.legends.length, 1, 'still one entry');
  assert.ok(h.legends[0].superWon);
});

test('climbing: a win swaps places with the army above, a loss ends the climb', () => {
  clearHall();
  const h0 = { legends: [fake('A', 'knight'), fake('B', 'archer'), fake('C', 'mage'), fake('D', 'cleric')] };
  h0.legends.slice(0, 3).forEach((l) => (l.climbed = true));
  R.saveHall(h0);
  let h = R.hallResult('D', 'C', 'P');
  assert.deepStrictEqual(h.legends.map((l) => l.id), ['A', 'B', 'D', 'C']);
  assert.ok(!h.legends[2].climbed, 'still climbing');
  assert.strictEqual(R.hallNext(h, 'D').id, 'B');
  h = R.hallResult('D', 'B', 'E');
  assert.deepStrictEqual(h.legends.map((l) => l.id), ['A', 'B', 'D', 'C'], 'a loss keeps the order');
  assert.ok(h.legends[2].climbed && !R.hallNext(h, 'D'), 'and ends the climb');
  const d = h.legends[2];
  assert.strictEqual(d.wins, 1);
  assert.strictEqual(d.losses, 1);
  assert.strictEqual(h.legends[1].wins, 1, 'the winner above gets the win');
  assert.strictEqual(h.legends[3].losses, 1);
});

test('reaching the top ends the climb', () => {
  clearHall();
  const h0 = { legends: [fake('A', 'knight'), fake('B', 'archer')] };
  h0.legends[0].climbed = true;
  R.saveHall(h0);
  const h = R.hallResult('B', 'A', 'P');
  assert.deepStrictEqual(h.legends.map((l) => l.id), ['B', 'A']);
  assert.ok(h.legends[0].climbed && !R.hallNext(h, 'B'));
});

test('armies wait in line, nothing is played without you, and one climbs at a time', () => {
  clearHall();
  winCampaign(26);
  winCampaign(27);
  winCampaign(28);
  let h = R.loadHall();
  assert.strictEqual(h.legends.length, 1);
  assert.strictEqual(h.queue.length, 2, 'two armies waiting, in the order they won');
  assert.strictEqual(h.legends.concat(h.queue).reduce((t, l) => t + l.wins + l.losses, 0), 0, 'no match played behind your back');
  const first = R.hallStart();
  assert.ok(first && R.hallClimber(R.loadHall()).id === first.id);
  assert.strictEqual(R.hallStart(), null, 'the next waits while one is climbing');
  h = R.hallResult(first.id, R.hallNext(R.loadHall(), first.id).id, 'E');
  assert.ok(!R.hallClimber(h), 'a loss ends the climb');
  const second = R.hallStart();
  h = R.loadHall();
  assert.ok(second && second.id !== first.id && !h.queue.length);
  assert.strictEqual(h.legends[h.legends.length - 1].id, second.id, 'the next starts at the bottom');
});

test('a Hall match: the armies face each other on a mirrored field, kit and relics intact', () => {
  clearHall();
  winCampaign(24);
  winCampaign(25);
  const hall = R.loadHall();
  const [a, b] = hall.legends.concat(hall.queue);
  for (let seed = 1; seed <= 10; seed++) {
    const cfg = R.hallBattleConfig(b, a, seed);
    const W = cfg.w;
    for (let y = 0; y < cfg.h; y++)
      for (let x = 0; x < W; x++) assert.strictEqual(cfg.terrain[y * W + x], cfg.terrain[(cfg.h - 1 - y) * W + (W - 1 - x)], 'mirrored obstacles');
    const P = cfg.units.filter((u) => u.team === 'P');
    const En = cfg.units.filter((u) => u.team === 'E');
    assert.strictEqual(P.length, b.units.length);
    assert.strictEqual(En.length, a.units.length);
    assert.ok(P.every((u) => u.y >= 5) && En.every((u) => u.y <= 3), 'each army on its own side');
    const spots = new Set(cfg.units.map((u) => u.x + ',' + u.y));
    assert.strictEqual(spots.size, cfg.units.length, 'no two units on one tile');
    assert.ok(cfg.units.every((u) => cfg.terrain[u.y * W + u.x] === 0), 'nobody on a rock');
    assert.deepStrictEqual(cfg.relics.P, b.relics);
    assert.deepStrictEqual(cfg.relics.E, a.relics);
    P.forEach((u, i) => {
      const { team, x, y, facing, ...spec } = u;
      assert.deepStrictEqual(spec, b.units[i].spec, 'the unit as it fought: level, abilities, talents, skills, gear');
    });
    const s = E.createBattle(cfg);
    assert.strictEqual(s.units.filter((u) => u.team === 'P').length, P.length);
  }
});

test('a Hall match plays out to a winner', () => {
  const hall = R.loadHall();
  const [a, b] = hall.legends.concat(hall.queue);
  const wins = { P: 0, E: 0 };
  for (let seed = 1; seed <= 4; seed++) wins[R.playHallMatch(a, b, seed)]++;
  assert.strictEqual(wins.P + wins.E, 4);
});

console.log(`hall: ${passed} tests passed`);
