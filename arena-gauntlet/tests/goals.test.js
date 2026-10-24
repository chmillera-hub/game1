// Bonus goals after a win, and fighting a won battle again for the ones missed.
// Run: node tests/goals.test.js
const assert = require('assert');
const store = {};
globalThis.localStorage = { getItem: (k) => store[k] || null, setItem: (k, v) => (store[k] = v), removeItem: (k) => delete store[k] };
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

// A won first battle, with one goal met (field this unit) and one missed (win in 1 turn).
function wonBattle() {
  for (let seed = 1; seed < 40; seed++) {
    const run = R.newRun({ seed, warband: 'vanguard' });
    R.chooseChallenge(run, 0);
    const dep = R.autoDeploy(run, 0);
    run.pending.enc.bonus = [
      { type: 'muster', rid: dep[0].rid },
      { type: 'swift', turns: 1 },
    ];
    run.pending.lastDep = dep;
    const s = E.createBattle(R.battleConfig(run, dep));
    for (let g = 0; g < 2000 && !s.over; g++) AG.AI.playTurn(s, s.side, { stance: 'balanced', temp: 0.3 });
    if (s.winner === 'P') return { run, s, dep };
  }
  throw new Error('no win found');
}

test('goal results name what was met and what was missed', () => {
  const { run, s, dep } = wonBattle();
  const goals = R.goalResults(run, s, dep);
  assert.deepStrictEqual(goals.map((g) => g.done), [true, false]);
  assert.ok(/Win within 1 turns/.test(goals[1].text) && goals[1].reward);
  R.finishBattle(run, s, dep);
  assert.deepStrictEqual(run.pending.objectives.map((o) => o.done), [true, false], 'the rewards agree');
});

test('retrying a won battle puts the run back as it was before the win', () => {
  const { run, s, dep } = wonBattle();
  const before = R.snapshot(run);
  const gold = run.gold;
  const xp = run.xp;
  const battles = run.stats.battles;
  R.finishBattle(run, s, dep);
  assert.strictEqual(run.pending.type, 'reward');
  assert.ok(run.gold > gold);
  const back = R.restore(before);
  assert.strictEqual(back.pending.type, 'battle', 'the same battle again');
  assert.strictEqual(back.pending.nodeId, run.pending.nodeId, 'at the same map node');
  assert.strictEqual(back.gold, gold, 'no gold yet');
  assert.strictEqual(back.xp, xp, 'no XP yet');
  assert.strictEqual(back.stats.battles, battles);
  assert.strictEqual(back.stats.losses, 0, 'not counted as a loss');
  assert.strictEqual(back.pending.attempt || 0, 0, 'still a first try');
  assert.deepStrictEqual(back.pending.lastDep.map((d) => d.rid), dep.map((d) => d.rid), 'your army is still set up');
  assert.strictEqual(R.load().pending.type, 'battle', 'and that is what is saved');
});

test('keeping the win saves it straight away', () => {
  const { run, s, dep } = wonBattle();
  R.snapshot(run);
  R.finishBattle(run, s, dep);
  assert.strictEqual(R.load().pending.type, 'reward', 'leaving the app at the question keeps the win');
});

console.log(`goals: ${passed} tests passed`);
