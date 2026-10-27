// Rival armies: share your best Hall armies as a code, paste a friend's into your Hall. They
// arrive as rivals waiting to climb, the same army only once, only what the game can field,
// and you can remove them. Run: node tests/rivals.test.js
const assert = require('assert');

function storage() {
  const m = new Map();
  return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
}
globalThis.localStorage = storage();
const AG = require('./load')();
const R = AG.Run;
const E = AG.Engine;

let passed = 0;
async function test(name, fn) {
  try {
    await fn();
    passed++;
  } catch (e) {
    console.error('FAIL', name);
    throw e;
  }
}

// Win the battle at hand without fighting it, and a whole campaign (as the Hall tests do).
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
function winCampaign(seed) {
  const run = R.newRun(seed);
  for (let guard = 0; !run.won && guard < 60; guard++) {
    const p = run.pending;
    if (!p) {
      const i = run.offer.findIndex((o) => o.tier === 'medium');
      R.chooseChallenge(run, i < 0 ? 0 : i);
      win(run);
    } else if (p.type === 'shop') R.completeNode(run);
    else if (p.type === 'event') {
      const c = R.eventChoices(run).filter((x) => x.enabled && !x.pick).pop();
      R.chooseEvent(run, c.id, null);
      if (run.pending.type === 'battle') win(run);
      else R.completeNode(run);
    }
  }
  assert.ok(run.won);
  return run;
}

(async () => {
  // Alex wins three campaigns.
  [11, 22, 33].map(winCampaign);
  const alexHall = R.loadHall();
  const alexOwn = alexHall.legends.concat(alexHall.queue).filter((l) => !l.house);
  assert.strictEqual(alexOwn.length, 3);
  let code;

  await test('sharing: your own armies only, best first, up to five', async () => {
    code = await R.exportArmies('Alex');
    assert.ok(/^AGAZ1\./.test(code));
    const r = await R.readArmies(code);
    assert.strictEqual(r.by, 'Alex');
    assert.deepStrictEqual(r.armies.map((l) => l.name).sort(), alexOwn.map((l) => l.name).sort());
    assert.ok(r.armies.every((l) => l.foreign && l.owner === 'Alex' && l.wins === 0 && l.losses === 0));
  });

  await test("pasting a friend's code adds their armies as rivals waiting to climb, once", async () => {
    globalThis.localStorage = storage(); // Sam's browser, a fresh Hall
    const r = await R.importArmies(code);
    assert.deepStrictEqual([r.by, r.added.length, r.already], ['Alex', 3, 0]);
    const h = R.loadHall();
    assert.ok(h.legends.every((l) => l.house), 'the house armies hold the ladder');
    assert.strictEqual(h.queue.length, 3);
    assert.ok(h.queue.every((l) => l.foreign && l.owner === 'Alex'));
    const again = await R.importArmies(code.replace(/(.{50})/g, '$1\n'));
    assert.deepStrictEqual([again.added.length, again.already], [0, 3], 'the same armies are not added twice');
    assert.strictEqual(R.loadHall().queue.length, 3);
  });

  await test('rivals climb and fight like any army', async () => {
    const l = R.hallStart();
    assert.ok(l && l.foreign);
    const h = R.loadHall();
    const foe = R.hallNext(h, l.id);
    const s = E.createBattle(R.hallBattleConfig(l, foe, 5));
    assert.ok(s.units.some((u) => u.team === 'P') && s.units.some((u) => u.team === 'E'));
  });

  await test("a rival's code never shares your rivals or the house armies onward", async () => {
    assert.strictEqual(await R.exportArmies('Sam'), null, 'Sam has no armies of their own yet');
  });

  await test('rivals can be removed; your own and the house armies cannot', async () => {
    const h = R.loadHall();
    const rival = h.legends.concat(h.queue).find((l) => l.foreign);
    const house = h.legends.find((l) => l.house);
    assert.ok(R.removeRival(rival.id));
    assert.ok(!R.loadHall().legends.concat(R.loadHall().queue).some((l) => l.id === rival.id));
    assert.ok(!R.removeRival(house.id), 'house armies stay');
  });

  await test('bad, hacked and foreign codes are refused or cleaned', async () => {
    const enc = (o) => 'AGA1.' + Buffer.from(JSON.stringify(o)).toString('base64');
    for (const bad of ['', 'hello', 'AGAZ1.!!', code.slice(0, code.length >> 1)]) assert.ok((await R.readArmies(bad)).error, bad.slice(0, 12));
    assert.ok(/save backup/.test((await R.readArmies('AGZ1.abc')).error), 'a save code gets pointed to Restore');
    // Units of a made-up type, on the enemy's side, stacked on one tile, or far too many.
    const spec = (type) => ({ spec: { type, level: 9, a1: 'nonsense', gear: ['not_gear'] }, x: 4, y: 0 });
    const r = await R.readArmies(enc({ v: 1, by: 'Hax<script>', armies: [{ name: 'Cheats', units: [spec('knight'), spec('knight'), spec('dragonzilla')] }, { name: 'Huge', units: Array.from({ length: 40 }, (_, i) => ({ spec: { type: 'dragon', level: 3 }, x: i % 9, y: 6 + (i % 3) })) }] }));
    assert.ok(!/[<>]/.test(r.by), 'no markup in names');
    const army = r.armies.find((l) => l.name === 'Cheats');
    assert.strictEqual(army.units.length, 1, 'unknown type gone, the stacked knight dropped');
    const u = army.units[0];
    assert.ok(u.y >= 6, 'moved back to its own side');
    assert.strictEqual(u.spec.level, AG.Data.MAX_LEVEL);
    assert.ok(!u.spec.a1 && !u.spec.gear.length, 'unknown picks and gear dropped');
    const huge = r.armies.find((l) => l.name === 'Huge');
    assert.ok(!huge || (huge.units.length <= 16 && R.armySupply(huge) <= 150), 'no army past the caps');
    assert.ok((await R.readArmies(enc({ v: 1, armies: [{ name: 'Empty', units: [] }] }))).error);
  });

  console.log(`rivals: ${passed} tests passed`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
