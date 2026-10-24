// The War Room's Auto button. Run: node tests/deploy.test.js
const assert = require('assert');
const AG = require('./load')();
const R = AG.Run;

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

function atBattle(seed, warband) {
  const run = R.newRun({ seed, warband, difficulty: 'knight' });
  R.enterNode(run, R.availableNodes(run).find((n) => n.kind === 'battle').id);
  return run;
}

test('Auto always fields the unit a bonus goal asks for', () => {
  let left = 0;
  for (const warband of ['vanguard', 'ember', 'shadow', 'grove', 'grave']) {
    for (let seed = 1; seed <= 6; seed++) {
      const run = atBattle(seed, warband);
      const enc = run.pending.enc;
      enc.bonus = (enc.bonus || []).filter((b) => b.type !== 'muster');
      for (const u of run.roster) {
        // Every unit in turn, including the ones Auto would leave out.
        if (!R.autoDeploy(run, 0).some((d) => d.rid === u.id)) left++;
        enc.bonus.push({ type: 'muster', rid: u.id });
        assert.strictEqual(R.bonusUnit(run, enc), u);
        for (let variant = 0; variant < 3; variant++) {
          const dep = R.autoDeploy(run, variant);
          assert.ok(dep.some((d) => d.rid === u.id), `${warband} ${seed}: ${u.type} left out`);
          assert.ok(R.supplyUsed(run, dep) <= R.supplyFor(run) && dep.length <= R.unitCap(run));
        }
        enc.bonus.pop();
      }
    }
  }
  assert.ok(left > 0, 'some of these units would have sat out without the bonus');
});

test('no bonus unit, no change', () => {
  const run = atBattle(2, 'vanguard');
  run.pending.enc.bonus = [];
  assert.strictEqual(R.bonusUnit(run, run.pending.enc), null);
  assert.ok(R.autoDeploy(run, 0).length > 0);
});

console.log(`deploy: ${passed} tests passed`);
