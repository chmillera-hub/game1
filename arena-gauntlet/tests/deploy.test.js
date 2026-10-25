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
  const run = R.newRun({ seed, warband });
  R.chooseChallenge(run, 1);
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
          assert.ok(R.supplyUsed(run, dep) <= R.supplyFor(run));
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

test('no field limit: eight Archers take the field when Supply pays for them', () => {
  const run = atBattle(3, 'vanguard');
  run.roster.length = 0;
  for (let i = 0; i < 8; i++) {
    const u = R.addRecruit(run, 'archer');
    u.load.talents = [];
  }
  run.supplyBonus = 24 - R.supplyFor(run);
  const enc = run.pending.enc;
  const rows = R.deployRows(run, enc);
  const dep = [];
  for (const y of rows) for (let x = 0; x < enc.w && dep.length < 8; x++) if (enc.terrain[y * enc.w + x] === 0) dep.push({ rid: run.roster[dep.length].id, x, y, facing: 0 });
  assert.strictEqual(dep.length, 8);
  assert.ok(R.supplyUsed(run, dep) <= R.supplyFor(run), 'eight 3-Supply Archers fit in 24 Supply');
  const s = AG.Engine.createBattle(R.battleConfig(run, dep));
  assert.strictEqual(s.units.filter((u) => u.team === 'P').length, 8);
  // Auto starts from the commander's usual army size, then spends what is left on one more unit.
  run.supplyBonus += 20;
  const auto = R.autoDeploy(run, 0);
  assert.ok(auto.length > R.armySize(run), `Auto used the spare Supply on more units (${auto.length})`);
  assert.ok(R.supplyUsed(run, auto) <= R.supplyFor(run));
});

test("Recruiter's Bell makes Level 1 units 1 Supply cheaper, never below 2", () => {
  const run = atBattle(4, 'vanguard');
  const archer = R.addRecruit(run, 'archer');
  archer.load.talents = [];
  const scout = R.addRecruit(run, 'scout');
  scout.load.talents = [];
  scout.load.a1 = AG.Data.UNITS.scout.abilities[1].find((id) => !AG.Data.ABILITIES[id].cost);
  const before = [R.unitCost(run, archer), R.unitCost(run, scout)];
  run.relics.push('recruiters_bell');
  assert.strictEqual(R.unitCost(run, archer), before[0] - 1);
  assert.strictEqual(R.unitCost(run, scout), Math.max(2, before[1] - 1));
  archer.load.lv = 2;
  R.normalizeLoad(run, archer);
  const lv2 = R.unitCost(run, archer);
  run.relics.pop();
  assert.strictEqual(R.unitCost(run, archer), lv2, 'no discount at Level 2');
});

test("a quest's featured unit fights injured: half health and half damage", () => {
  const run = atBattle(5, 'vanguard');
  const enc = run.pending.enc;
  enc.bonus = (enc.bonus || []).filter((b) => b.type !== 'muster');
  const u = run.roster[0];
  enc.bonus.push({ type: 'muster', rid: u.id });
  const dep = R.autoDeploy(run, 0);
  assert.ok(dep.some((d) => d.rid === u.id), 'Auto fields it');
  const s = AG.Engine.createBattle(R.battleConfig(run, dep));
  const hurt = s.units.find((x) => x.rid === u.id);
  const other = s.units.find((x) => x.team === 'P' && x.rid !== u.id);
  const fresh = R.unitStats(run, u);
  assert.ok(hurt.injured && !other.injured);
  assert.strictEqual(hurt.maxHp, Math.round(fresh.maxHp / 2));
  const foe = s.units.find((x) => x.team === 'E' && !x.nonCombat);
  const healthy = AG.Engine.calcHit(s, Object.assign({}, hurt, { injured: false }), foe, {}).dmg;
  assert.ok(AG.Engine.calcHit(s, hurt, foe, {}).dmg <= Math.ceil(healthy / 2) + 1, 'half damage');
});

test('bare: stripping a unit sends its kit back to the pack', () => {
  const run = atBattle(6, 'vanguard');
  const u = run.roster[0];
  R.setLevel(run, u.id, 2);
  const item = R.freeItems(run).find((i) => i.kind !== 'scroll' && R.assignItem(run, u.id, i.uid));
  assert.ok(R.unitCost(run, u) > R.bareCost(run, u));
  R.stripLoad(run, u);
  assert.strictEqual(u.load.lv, 1);
  assert.strictEqual(R.unitCost(run, u), R.bareCost(run, u));
  if (item) assert.ok(!R.itemHolder(run, item.uid), 'the item is free again');
});

test('a plan survives a defeat: back at the same battle, the army is where you left it', () => {
  const run = atBattle(7, 'vanguard');
  const dep = R.autoDeploy(run, 0);
  run.pending.lastDep = dep;
  const i = run.pending.offerIndex;
  R.backToChoice(run);
  assert.ok(R.chooseChallenge(run, i));
  assert.deepStrictEqual(run.pending.lastDep, dep);
  R.backToChoice(run);
  const other = (i + 1) % run.offer.length;
  assert.ok(R.chooseChallenge(run, other));
  assert.ok(!run.pending.lastDep, 'another battle has a plan of its own');
});

console.log(`deploy: ${passed} tests passed`);
