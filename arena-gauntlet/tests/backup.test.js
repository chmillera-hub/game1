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

  console.log(`backup: ${passed} tests passed`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
