// Drafting a starting army. Run: node tests/draft.test.js
const assert = require('assert');
const AG = require('./load')();
const R = AG.Run;
const D = AG.Data;

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

const attacker = (t) => !!(D.UNITS[t].act.dmg || (D.UNITS[t].act.fx && D.UNITS[t].act.fx.poison));
const draftAll = (seed, choose) => {
  const picks = [];
  for (let s = 0; s < R.DRAFT_STEPS.length; s++) picks.push(choose(R.draftOffer(seed, s, picks).options, s));
  return picks;
};

test('eight picks: five units, a relic, a skill and gear, each one of three different things', () => {
  assert.deepStrictEqual(R.DRAFT_STEPS, ['unit', 'unit', 'unit', 'unit', 'unit', 'relic', 'skill', 'gear']);
  for (let seed = 1; seed <= 200; seed++) {
    draftAll(seed, (o, s) => {
      assert.strictEqual(o.length, 3);
      assert.strictEqual(new Set(o).size, 3, `seed ${seed} step ${s}: three different options`);
      return o[seed % 3];
    });
  }
  assert.strictEqual(R.draftOffer(1, 8, []), null, 'nothing after the last pick');
});

test('every army can fight: each unit pick offers at least two attackers', () => {
  for (let seed = 1; seed <= 300; seed++) {
    const picks = [];
    for (let s = 0; s < 5; s++) {
      const o = R.draftOffer(seed, s, picks).options;
      assert.ok(o.filter(attacker).length >= 2, `seed ${seed} step ${s}: ${o}`);
      assert.ok(o.filter((t) => ['support', 'ward'].includes(D.UNITS[t].role)).length <= 1);
      picks.push(o[(seed + s) % 3]);
    }
  }
});

test('the draft never offers a Cleric: every army starts with its own, free and always on the field', () => {
  for (let seed = 1; seed <= 300; seed++) {
    const picks = [];
    for (let s = 0; s < 5; s++) {
      const o = R.draftOffer(seed, s, picks).options;
      assert.ok(!o.includes('cleric'), `seed ${seed} step ${s}: ${o}`);
      picks.push(o[(seed + s) % 3]);
    }
  }
  const picks = draftAll(5, (o) => o[0]);
  const run = R.newRun({ seed: 5, draft: { units: picks.slice(0, 5), relic: picks[5], items: [['skill', picks[6]], ['gear', picks[7]]] } });
  assert.strictEqual(run.roster.length, 6, 'five drafted units and the Cleric');
  const core = R.coreUnit(run);
  assert.ok(core && core.type === 'cleric' && run.roster[0] === core);
  assert.strictEqual(R.unitCost(run, core), 0, 'its base cost is free');
  core.load.lv = 2;
  assert.ok(R.unitCost(run, core) > 0, 'levels still cost Supply');
  core.load.lv = 1;
  // A ready-made warband's own Cleric becomes it: no second one.
  const wb = R.newRun({ seed: 5, warband: 'vanguard' });
  assert.strictEqual(wb.roster.filter((u) => u.type === 'cleric').length, 1);
  assert.ok(R.coreUnit(wb));
});

test('offered items fit the units chosen; the same picks give the same offers', () => {
  for (let seed = 1; seed <= 100; seed++) {
    const picks = draftAll(seed, (o) => o[2]);
    const units = picks.slice(0, 5);
    for (const [step, table] of [[6, D.SKILLS], [7, D.GEAR]]) {
      for (const id of R.draftOffer(seed, step, picks.slice(0, step)).options) assert.ok(units.some((t) => D.eligible(t, table[id])), id);
    }
    assert.deepStrictEqual(R.draftOffer(seed, 3, picks.slice(0, 3)), R.draftOffer(seed, 3, picks.slice(0, 3)), 'stepping back shows the same three');
  }
});

test('a drafted army starts the campaign', () => {
  const picks = draftAll(77, (o) => o[0]);
  const run = R.newRun({ seed: 77, draft: { units: picks.slice(0, 5), relic: picks[5], items: [['skill', picks[6]], ['gear', picks[7]]] } });
  assert.deepStrictEqual(run.roster.map((r) => r.type), ['cleric', ...picks.slice(0, 5)], 'your Cleric, then the five you drafted');
  assert.deepStrictEqual(run.relics, [picks[5]]);
  assert.ok(run.items.some((i) => i.kind === 'skill' && i.id === picks[6]));
  assert.ok(run.items.some((i) => i.kind === 'gear' && i.id === picks[7]));
  assert.strictEqual(run.gold, R.DRAFT_GOLD);
  assert.ok(run.roster.every((r) => r.brought && r.load.talents.length === 0), 'each brought its random talent, into the pack');
  assert.strictEqual(run.items.filter((i) => i.kind === 'talent').length, 6);
  assert.ok(run.offer && run.offer.length === 3, 'the first round of challenges is on offer');
});

test('every unit on offer names the talent it brings, one its class has not brought yet; so does the Cleric', () => {
  for (let seed = 1; seed <= 40; seed++) {
    const picks = [];
    for (let k = 0; k < R.DRAFT_STEPS.length; k++) {
      const opts = R.draftOffer(seed, k, picks).options;
      // A class already picked whenever it comes up again, to test the no-repeat rule.
      picks.push(k < 5 ? opts.find((t) => picks.includes(t)) || opts[seed % 3] : opts[0]);
    }
    const units = picks.slice(0, 5);
    const brought = [];
    for (let k = 0; k < 5; k++) {
      const o = R.draftOffer(seed, k, picks);
      assert.strictEqual(o.talents.length, 3);
      o.options.forEach((t, i) => assert.ok(!o.talents[i] || D.TALENTS[o.talents[i]].cls === t, 'a talent of its own class'));
      brought.push(o.talents[o.options.indexOf(units[k])]);
    }
    const ct = R.draftClericTalent(seed);
    assert.ok(ct && D.TALENTS[ct].cls === 'cleric');
    const run = R.newRun({ seed, draft: { units, relic: picks[5], items: [['skill', picks[6]], ['gear', picks[7]]] } });
    const got = run.roster.filter((r) => !r.core).map((r) => r.brought || null);
    assert.deepStrictEqual(got, brought, 'each unit brings the talent its card named');
    const core = run.roster.find((r) => r.core);
    assert.strictEqual(core.brought, ct, 'and the Cleric brings its own');
    // No two units of a class bring the same talent while their class has others left.
    for (const t of new Set(units)) {
      const mine = brought.filter((id, k) => units[k] === t && id);
      const pool = Object.keys(D.TALENTS).filter((id) => D.TALENTS[id].cls === t).length;
      if (mine.length <= pool) assert.strictEqual(new Set(mine).size, mine.length, `seed ${seed}: two ${t}s, two talents`);
    }
  }
});

test('battle spoils and the merchant name the talent a recruit brings, and that is the one it brings', () => {
  for (let seed = 1; seed <= 12; seed++) {
    const run = R.newRun({ seed, warband: 'vanguard' });
    const o = run.offer[1];
    const sp = o.reward.spoils.find((x) => x.type === 'recruit');
    assert.ok(sp && sp.talent && D.TALENTS[sp.talent].cls === sp.unit);
    R.chooseChallenge(run, 1);
    const dep = R.autoDeploy(run, 0);
    const s = AG.Engine.createBattle(R.battleConfig(run, dep));
    s.over = true;
    s.winner = 'P';
    R.finishBattle(run, s, dep);
    R.takeSpoil(run, run.pending.spoils.indexOf(run.pending.spoils.find((x) => x.type === 'recruit')));
    const u = run.roster[run.roster.length - 1];
    assert.strictEqual(u.brought, sp.talent);
    assert.ok(run.items.some((it) => it.kind === 'talent' && it.id === sp.talent), 'in the pack');
  }
});

console.log(`draft: ${passed} tests passed`);
