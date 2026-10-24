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

test('every army can fight: the first pick is all attackers, later ones at least two', () => {
  for (let seed = 1; seed <= 300; seed++) {
    const picks = [];
    for (let s = 0; s < 5; s++) {
      const o = R.draftOffer(seed, s, picks).options;
      assert.ok(o.filter(attacker).length >= (s === 0 ? 3 : 2), `seed ${seed} step ${s}: ${o}`);
      assert.ok(o.filter((t) => ['support', 'ward'].includes(D.UNITS[t].role)).length <= 1);
      picks.push(o[(seed + s) % 3]);
    }
  }
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
  assert.deepStrictEqual(run.roster.map((r) => r.type), picks.slice(0, 5));
  assert.deepStrictEqual(run.relics, [picks[5]]);
  assert.ok(run.items.some((i) => i.kind === 'skill' && i.id === picks[6]));
  assert.ok(run.items.some((i) => i.kind === 'gear' && i.id === picks[7]));
  assert.strictEqual(run.gold, R.DRAFT_GOLD);
  assert.ok(run.roster.every((r) => r.load.talents.length === 1), 'each with its random talent');
  assert.ok(run.offer && run.offer.length === 3, 'the first round of challenges is on offer');
});

console.log(`draft: ${passed} tests passed`);
