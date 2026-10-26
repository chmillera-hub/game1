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
// An empty Hall that has already had its house armies (so the ladder tests below start
// truly empty); freshHall() is a Hall nobody has ever entered.
const clearHall = () => (store[HALL] = JSON.stringify({ legends: [], queue: [], house: true }));
const freshHall = () => delete store[HALL];

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
      const { team, x, y, facing, supply, ...spec } = u;
      assert.strictEqual(supply, R.specCost(spec));
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

test('skirmish: the lower-ranked army wins and they swap places; the ones between stay put', () => {
  clearHall();
  const h0 = { legends: ['A', 'B', 'C', 'D', 'E'].map((id, i) => fake(id, ['knight', 'archer', 'mage', 'cleric', 'scout'][i])), queue: [] };
  h0.legends.forEach((l) => (l.climbed = true));
  R.saveHall(h0);
  // D (#4, blue) beats A (#1, red).
  let r = R.hallSkirmish('D', 'A', 'P');
  let h = R.loadHall();
  assert.deepStrictEqual(h.legends.map((l) => l.id), ['D', 'B', 'C', 'A', 'E']);
  assert.ok(r.swapped && r.rank === 1 && r.loserRank === 4 && r.winner.id === 'D');
  assert.strictEqual(h.legends[0].wins, 1);
  assert.strictEqual(h.legends[3].losses, 1);
  // Blue or red makes no difference: E (#5, red) beats C (#3, blue).
  r = R.hallSkirmish('C', 'E', 'E');
  h = R.loadHall();
  assert.deepStrictEqual(h.legends.map((l) => l.id), ['D', 'B', 'E', 'A', 'C']);
  assert.ok(r.swapped && r.rank === 3);
});

test('skirmish: the higher-ranked army wins and nothing moves, but both records count it', () => {
  clearHall();
  const h0 = { legends: [fake('A', 'knight'), fake('B', 'archer'), fake('C', 'mage')], queue: [fake('Q', 'scout')] };
  h0.legends.forEach((l) => (l.climbed = true));
  R.saveHall(h0);
  const r = R.hallSkirmish('C', 'A', 'E');
  const h = R.loadHall();
  assert.deepStrictEqual(h.legends.map((l) => l.id), ['A', 'B', 'C']);
  assert.ok(!r.swapped && r.rank === 1);
  assert.strictEqual(h.legends[0].wins, 1);
  assert.strictEqual(h.legends[2].losses, 1);
  // An army still waiting in line has no place to win or lose: nothing is recorded.
  assert.strictEqual(R.hallSkirmish('Q', 'A', 'P'), null);
  assert.strictEqual(R.hallSkirmish('A', 'A', 'P'), null);
  assert.deepStrictEqual(R.loadHall(), h);
});

test('skirmish: a climbing army keeps climbing from its new place; reaching #1 ends its climb', () => {
  clearHall();
  const h0 = { legends: [fake('A', 'knight'), fake('B', 'archer'), fake('C', 'mage'), fake('D', 'cleric')], queue: [] };
  h0.legends.slice(0, 3).forEach((l) => (l.climbed = true));
  R.saveHall(h0);
  assert.strictEqual(R.hallClimber(R.loadHall()).id, 'D');
  // D skirmishes past B: still climbing, now facing A.
  R.hallSkirmish('D', 'B', 'P');
  let h = R.loadHall();
  assert.deepStrictEqual(h.legends.map((l) => l.id), ['A', 'D', 'C', 'B']);
  assert.strictEqual(R.hallClimber(h).id, 'D');
  assert.strictEqual(R.hallNext(h, 'D').id, 'A');
  // A skirmish loss is not a climb loss.
  R.hallSkirmish('C', 'D', 'P');
  h = R.loadHall();
  assert.deepStrictEqual(h.legends.map((l) => l.id), ['A', 'C', 'D', 'B']);
  assert.strictEqual(R.hallClimber(h).id, 'D');
  // Skirmishing to the top leaves nothing to climb.
  R.hallSkirmish('D', 'A', 'P');
  h = R.loadHall();
  assert.strictEqual(h.legends[0].id, 'D');
  assert.ok(h.legends[0].climbed && !R.hallClimber(h));
});

test('the final challenge can be retried as often as you like; whatever army last tried it goes to the Hall, no asking', () => {
  clearHall();
  const run = winCampaign(29);
  const before = JSON.stringify(R.loadHall().legends[0].units);
  assert.ok(R.faceFinal(run));
  // Lose it three times, with a smaller army than the one that won the campaign.
  let last = null;
  for (let t = 1; t <= 3; t++) {
    assert.ok(R.chooseChallenge(run, 0), 'the final challenge is still on offer');
    assert.strictEqual(run.pending.tier, 'mega');
    const dep = R.autoDeploy(run, 0).slice(0, 4 - (t % 2));
    const s = E.createBattle(R.battleConfig(run, dep));
    s.over = true;
    s.winner = 'E';
    assert.ok(!R.finishBattle(run, s, dep).won);
    assert.ok(!run.over, 'a loss never ends the campaign');
    // At once, after each try: the Hall's entry is this army now.
    last = R.loadHall().legends[0].units;
    assert.strictEqual(last.length, dep.length);
    R.backToChoice(run);
    assert.strictEqual(run.offer[0].attempts, t);
  }
  assert.notStrictEqual(JSON.stringify(last), before);
  assert.strictEqual(last.length, 3, 'the last try (three units) is the one kept');
  // Calling it a day changes nothing more: same entry, the last army in it.
  R.claimVictory(run);
  const h = R.loadHall();
  assert.strictEqual(h.legends.length + h.queue.length, 1, 'still one entry');
  assert.strictEqual(h.legends[0].id, run.legendId);
  assert.deepStrictEqual(h.legends[0].units, last);
  assert.ok(!h.legends[0].superWon && run.over && run.won);
});

test('a save from before: an army set aside after the final challenge goes to the Hall when you call it a day', () => {
  clearHall();
  const run = winCampaign(31);
  const other = JSON.parse(JSON.stringify(run.finalArmy)).slice(0, 2);
  run.megaArmy = other;
  R.claimVictory(run);
  assert.deepStrictEqual(R.loadHall().legends[0].units, other);
});

test('the first army ever to enter finds the house armies holding the Hall: a few Level 3 veterans of one kind each', () => {
  freshHall();
  const run = winCampaign(21);
  const h = R.loadHall();
  const D = AG.Data;
  assert.deepStrictEqual(h.legends.map((l) => l.type), ['scout', 'knight', 'archer', 'witch']);
  assert.deepStrictEqual(h.legends.map((l) => l.units.length), [8, 6, 5, 5], 'small squads, not mobs');
  for (const l of h.legends) {
    assert.ok(l.house && l.climbed);
    const T = D.UNITS[l.type];
    for (const it of l.units) {
      const sp = it.spec;
      assert.strictEqual(sp.type, l.type, 'all of a kind');
      assert.strictEqual(sp.level, D.MAX_LEVEL, 'every one Level 3, mastery and all');
      assert.ok(T.abilities[1].includes(sp.a1) && T.abilities[2].includes(sp.a2), `${l.name}: both picks are its own`);
      assert.ok(it.y >= 6, 'on their own half');
    }
    assert.strictEqual(new Set(l.units.map((it) => it.x + ',' + it.y)).size, l.units.length);
    // The Hall shows the full price: unit, Level 3 and both picks.
    const sp = l.units[0].spec;
    assert.strictEqual(R.armySupply(l), l.units.length * (T.cost + D.LEVEL_COST[3] + D.ABILITIES[sp.a1].cost + D.ABILITIES[sp.a2].cost));
  }
  // It fights as Level 3: masteries in, stats up.
  const s = E.createBattle(R.hallBattleConfig(h.legends[1], h.legends[0], 9));
  const kn = s.units.find((u) => u.team === 'P');
  assert.strictEqual(kn.level, 3);
  assert.ok(kn.maxHp > D.UNITS.knight.hp * 1.3, 'Level 3 hit points');
  assert.deepStrictEqual(R.hallPlace(h, run.legendId), { inLine: 1 }, 'it waits to climb past them');
  R.hallStart();
  const h2 = R.loadHall();
  assert.strictEqual(R.hallNext(h2, run.legendId).type, 'witch', 'from the bottom up');
  // Later armies do not bring more house armies.
  winCampaign(22);
  assert.strictEqual(R.loadHall().legends.concat(R.loadHall().queue).filter((l) => l.house).length, 4);
});

test('a Hall saved with the old house mobs fields today\'s house armies, in the same places, records kept', () => {
  freshHall();
  const old = R.houseArmies().map((l, i) => Object.assign(l, { wins: i, losses: 2, units: Array.from({ length: 16 }, (_, k) => ({ spec: { type: l.type, level: 1, a1: AG.Data.UNITS[l.type].abilities[1][0] }, x: k % 9, y: 6 + Math.floor(k / 9), facing: 0 })) }));
  const mine = { id: 'mine', name: 'The Mine', wins: 5, losses: 0, climbed: true, level: 8, relics: [], units: [{ spec: { type: 'knight', level: 2, talents: [], skills: [], gear: [] }, x: 4, y: 7, facing: 0 }] };
  // Ours beat the Archers: it stands above them.
  store[HALL] = JSON.stringify({ legends: [old[0], old[1], mine, old[2], old[3]], queue: [], house: true });
  const h = R.loadHall();
  assert.deepStrictEqual(h.legends.map((l) => l.id), ['H-scouts', 'H-knights', 'mine', 'H-archers', 'H-witches']);
  const now = R.houseArmies();
  for (const l of h.legends.filter((x) => x.house)) {
    const i = now.findIndex((x) => x.id === l.id);
    assert.deepStrictEqual(l.units, now[i].units, `${l.name} fields today's line-up`);
    assert.deepStrictEqual([l.wins, l.losses], [i, 2], 'its record stays');
  }
  assert.deepStrictEqual(h.legends[2].units, mine.units, 'a real army is never touched');
});

test('old Hall armies survive any update: what no longer exists is left out, never the army', () => {
  freshHall();
  const D = AG.Data;
  const relic = Object.keys(D.RELICS)[0];
  const skill = Object.keys(D.SKILLS).find((id) => D.eligible('knight', D.SKILLS[id]));
  const gear = Object.keys(D.GEAR).find((id) => D.eligible('knight', D.GEAR[id]));
  store[HALL] = JSON.stringify({
    legends: [
      { id: 'old1', name: 'The Old Guard', wins: 3, losses: 1, climbed: true, level: 7, relics: [relic, 'gone_relic'], units: [
        { spec: { type: 'knight', level: 3, a1: 'k_bash', a2: 'no_such_pick', talents: ['gone_talent'], skills: [skill, 'old_skill'], gear: [gear, 'old_gear'], enchant: 'old_enchant' }, x: 4, y: 7, facing: 0 },
        { spec: { type: 'retired_unit', level: 2 }, x: 3, y: 7, facing: 0 },
        { spec: { type: 'archer', level: 9 }, x: 5, y: 8, facing: 0 },
      ] },
    ],
    queue: [],
  });
  const h = R.loadHall();
  assert.strictEqual(h.legends.length, 1, 'still there');
  const L = h.legends[0];
  assert.deepStrictEqual([L.name, L.wins, L.losses], ['The Old Guard', 3, 1]);
  assert.deepStrictEqual(L.relics, [relic]);
  assert.deepStrictEqual(L.units.map((it) => it.spec.type), ['knight', 'archer']);
  const kn = L.units[0].spec;
  assert.deepStrictEqual([kn.a1, kn.a2, kn.talents, kn.skills, kn.gear, kn.enchant], ['k_bash', undefined, [], [skill], [gear], undefined]);
  assert.strictEqual(L.units[1].spec.level, AG.Data.MAX_LEVEL);
  // It still fights, by today's rules.
  const w = R.playHallMatch(L, fake('x', 'scout'), 5);
  assert.ok(w === 'P' || w === 'E');
  // Junk in storage does not take the Hall down either.
  store[HALL] = '{not json';
  assert.deepStrictEqual(R.loadHall(), { legends: [], queue: [] });
});

test('only Reset Hall of Fame clears it', () => {
  clearHall();
  winCampaign(23);
  assert.strictEqual(R.loadHall().legends.length, 1);
  R.resetHall();
  assert.deepStrictEqual(R.loadHall(), { legends: [], queue: [] });
});

console.log(`hall: ${passed} tests passed`);
