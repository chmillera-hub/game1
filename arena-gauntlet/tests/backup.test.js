// Save backup: the campaign, the Hall of Fame and the record go out as one text code and
// come back whole in another browser; anything that is not a good code is refused untouched.
// Run: node tests/backup.test.js
const assert = require('assert');

// A browser's storage, one per "device".
function storage() {
  const m = new Map();
  return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), _m: m };
}
globalThis.localStorage = storage();
const AG = require('./load')();
const R = AG.Run;

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


// Win the battle at hand without fighting it (as the Hall tests do), and a whole campaign.
function win(run) {
  const E = AG.Engine;
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
  assert.ok(run.won, 'campaign won');
  return run;
}

(async () => {
  // A real campaign a few picks in, a Hall entry and a record on device A.
  const run = R.newRun(4242);
  R.save(run);
  globalThis.localStorage.setItem('arena-gauntlet-meta-v2', JSON.stringify({ runs: 3, wins: 2, superWins: 0, bestAct: 4 }));
  globalThis.localStorage.setItem('arena-gauntlet-hall-v1', JSON.stringify({ legends: [{ id: 'x1', name: 'Test Army', units: [] }], queue: [] }));
  const before = new Map(globalThis.localStorage._m);

  let code;
  await test('a backup is one short-ish text code', async () => {
    code = await R.exportSave();
    assert.ok(/^AGZ1\.[A-Za-z0-9+/=]+$/.test(code), code.slice(0, 20));
    assert.ok(code.length < 200000, `code is ${code.length} characters`);
  });

  await test('restoring on a fresh device brings back the campaign, Hall and record', async () => {
    globalThis.localStorage = storage();
    // Pasted with line breaks and spaces, as phones do.
    const r = await R.importSave(' ' + code.replace(/(.{60})/g, '$1\n') + ' \n');
    assert.ok(r.ok, r.error);
    for (const [k, v] of before) assert.deepStrictEqual(JSON.parse(globalThis.localStorage.getItem(k)), JSON.parse(v), k);
    const back = R.load();
    assert.ok(back && back.seed === run.seed, 'the campaign loads');
    assert.strictEqual(R.loadMeta().wins, 2);
    assert.strictEqual(R.loadHall().legends.length, 1);
  });

  await test('a plain (uncompressed) code reads too', async () => {
    const data = { v: 1, meta: { runs: 1, wins: 1 } };
    const plain = 'AG1.' + Buffer.from(JSON.stringify(data)).toString('base64');
    const r = await R.readBackup(plain);
    assert.deepStrictEqual(r.data, data);
  });

  await test('junk, cut-short and foreign codes are refused and change nothing', async () => {
    const snap = new Map(globalThis.localStorage._m);
    for (const bad of ['', 'hello', 'AGZ1.!!!', code.slice(0, code.length >> 1), 'AG1.' + Buffer.from('{"v":9}').toString('base64'), 'AG1.' + Buffer.from('[1,2]').toString('base64')]) {
      const r = await R.importSave(bad);
      assert.ok(r.error, `refused: ${bad.slice(0, 16)}`);
    }
    assert.deepStrictEqual(new Map(globalThis.localStorage._m), snap);
  });

  await test('three won campaigns: their Hall of Fame armies, formations and records come back whole', async () => {
    globalThis.localStorage = storage();
    const runs = [101, 202, 303].map(winCampaign);
    R.hallStart(); // one army has started its climb, the other waits in line
    const hall = R.loadHall();
    const mine = hall.legends.concat(hall.queue).filter((l) => runs.some((r) => r.legendId === l.id));
    assert.strictEqual(mine.length, 3, 'three of my armies in the Hall');
    const saved = globalThis.localStorage.getItem('arena-gauntlet-hall-v1');
    const backup = await R.exportSave();

    // Weeks later, a wiped browser (or another device): paste the code from Notepad.
    globalThis.localStorage = storage();
    assert.strictEqual(R.loadHall().legends.length, 0, 'the wiped browser has no Hall');
    assert.ok((await R.importSave(backup)).ok);
    assert.strictEqual(globalThis.localStorage.getItem('arena-gauntlet-hall-v1'), saved, 'the Hall comes back byte for byte');
    const back = R.loadHall();
    assert.deepStrictEqual(back.legends.map((l) => l.id), hall.legends.map((l) => l.id), 'same ladder order');
    assert.deepStrictEqual(back.queue.map((l) => l.id), hall.queue.map((l) => l.id), 'same armies waiting to climb');
    for (const l of mine) {
      const b = back.legends.concat(back.queue).find((x) => x.id === l.id);
      assert.strictEqual(b.name, l.name);
      assert.deepStrictEqual(b.units, l.units, `${l.name}: every unit, loadout and tile of its formation`);
      assert.deepStrictEqual(b.relics, l.relics, `${l.name}: its relics`);
    }
    // And the restored armies still fight: the climber takes on the army above it.
    const climber = R.hallClimber(back);
    const foe = climber && R.hallNext(back, climber.id);
    assert.ok(climber && foe, 'a climb is under way');
    const s = AG.Engine.createBattle(R.hallBattleConfig(climber, foe, 7));
    assert.ok(s.units.some((u) => u.team === 'P') && s.units.some((u) => u.team === 'E'), 'both armies take the field');
  });

  console.log(`backup: ${passed} tests passed`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
