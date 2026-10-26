// The legendaries: four units with a huge act and a long cooldown, and legendary skills and
// gear. None turn up before the second half of Act 2; then more and more through Act 3.
// Run: node tests/legendary.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js', 'run.js', 'sprites.js']);
const R = AG.Run;
const D = AG.Data;
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

const NEW = ['archmage', 'phoenix', 'frostgiant', 'paladin'];
const legendUnits = D.RECRUITABLE.filter((t) => D.UNITS[t].rarity === 'legendary');
const legendItems = (table) => Object.keys(table).filter((id) => table[id].rarity === 'legendary');

test('four new legendary units, each with a long cooldown, its picks, talents, mastery and art', () => {
  for (const t of NEW) {
    const T = D.UNITS[t];
    assert.strictEqual(T.rarity, 'legendary', t);
    assert.ok(T.rec >= 3, `${t}: a long cooldown`);
    assert.ok(T.cost >= 7, `${t}: priced like a legendary`);
    assert.ok(T.abilities[1].length >= 3 && T.abilities[2].length >= 3);
    assert.ok(Object.values(D.TALENTS).filter((x) => x.cls === t).length >= 3, `${t}: talents to find`);
    assert.ok(D.MASTERY[t], `${t}: a mastery`);
    assert.ok(AG.Sprites.HEIGHT[t], `${t}: drawn`);
  }
  assert.strictEqual(legendUnits.length, 5, 'the Dragon Tyrant and the four new ones');
});

test('legendary skills and gear exist, and cost more Supply than the rest', () => {
  for (const table of [D.SKILLS, D.GEAR]) {
    const ids = legendItems(table);
    assert.ok(ids.length >= 4, 'four of each');
    for (const id of ids) assert.ok(table[id].cost >= 3, `${id}: costs at least 3 Supply`);
  }
});

// A run at a given act and step of its plan.
function runAt(act, step, seed) {
  const run = R.newRun({ seed: seed || 5, warband: 'vanguard' });
  for (const t of NEW) R.addRecruit(run, t); // so every legendary skill and piece of gear is usable
  R.startAct(run, act);
  run.step = Math.min(step, run.plan.length - 1);
  return run;
}

test('the chance of a legendary: none in Act 1 or early Act 2, then rising to the end of Act 3', () => {
  const last = runAt(1, 0).plan.length - 1;
  for (let st = 0; st <= last; st++) assert.strictEqual(R.legendChance(runAt(1, st)), 0, 'Act 1');
  assert.strictEqual(R.legendChance(runAt(2, 0)), 0, 'early Act 2');
  assert.strictEqual(R.legendChance(runAt(2, 2)), 0, 'early Act 2');
  const late2 = R.legendChance(runAt(2, last));
  assert.ok(late2 > 0 && late2 < 0.1, `late Act 2: ${late2}`);
  const a3 = [0, 2, 4, last].map((st) => R.legendChance(runAt(3, st)));
  for (let i = 1; i < a3.length; i++) assert.ok(a3[i] > a3[i - 1], 'it rises through Act 3');
  assert.ok(a3[0] > late2 && a3[a3.length - 1] >= 0.2, `Act 3: ${a3}`);
  assert.ok(R.legendChance(runAt(3, last), 'elite') > R.legendChance(runAt(3, last)), 'elite rewards more so');
});

// Battle spoils, many times over, at one point of the campaign.
function spoilsAt(act, step, n) {
  const got = { units: 0, items: 0, rolls: 0, itemRolls: 0 };
  for (let i = 0; i < n; i++) {
    const run = runAt(act, step, 100 + i);
    for (const o of R.genSpoils(run, AG.derive(900 + i, 'sp'), i % 3 ? 'battle' : 'elite', 'x' + i)) {
      if (o.type === 'recruit') {
        got.rolls++;
        if (D.UNITS[o.unit].rarity === 'legendary') got.units++;
      }
      if (o.type === 'skill' || o.type === 'gear') {
        got.itemRolls++;
        if ((o.type === 'skill' ? D.SKILLS : D.GEAR)[o.id].rarity === 'legendary') got.items++;
      }
    }
  }
  return got;
}

test('spoils: nothing legendary in Act 1 or early Act 2; some late in Act 2; plenty late in Act 3', () => {
  for (const [act, st] of [[1, 0], [1, 6], [2, 0], [2, 2]]) {
    const g = spoilsAt(act, st, 150);
    assert.deepStrictEqual([g.units, g.items], [0, 0], `act ${act} step ${st}`);
  }
  const late2 = spoilsAt(2, 6, 300);
  const early3 = spoilsAt(3, 0, 300);
  const late3 = spoilsAt(3, 6, 300);
  assert.ok(late2.units + late2.items > 0, 'late Act 2 turns some up');
  assert.ok(late3.units + late3.items > early3.units + early3.items, 'late Act 3 more than early');
  assert.ok(late3.units / late3.rolls > 0.15 && late3.items / late3.itemRolls > 0.15, `late Act 3: ${JSON.stringify(late3)}`);
});

test('the merchant: legendary skills and gear cost half as much again', () => {
  let seen = 0;
  for (let i = 0; i < 300 && seen < 3; i++) {
    const run = runAt(3, 6, 300 + i);
    for (const it of R.genShop(run, { id: 'm' + i })) {
      if (it.kind !== 'skill' && it.kind !== 'gear') continue;
      const d = (it.kind === 'skill' ? D.SKILLS : D.GEAR)[it.id];
      if (d.rarity !== 'legendary') continue;
      seen++;
      assert.ok(it.price >= Math.round((42 + 21 * d.cost) * 1.5) - 5, `${it.id}: ${it.price} gold`);
    }
  }
  assert.ok(seen >= 3, 'legendaries turn up at the late Act 3 merchant');
});

test('each new legendary uses its big act in battle, and its cooldown is long', () => {
  for (const t of NEW) {
    const units = [
      { type: t, team: 'P', x: 4, y: 8 },
      { type: 'knight', team: 'P', x: 3, y: 7 },
      { type: 'knight', team: 'P', x: 5, y: 7 },
      { type: 'orc', team: 'E', x: 3, y: 1 },
      { type: 'orc', team: 'E', x: 5, y: 1 },
      { type: 'goblin_archer', team: 'E', x: 4, y: 0 },
      { type: 'brute', team: 'E', x: 6, y: 0 },
    ];
    const s = E.createBattle({ w: 9, h: 9, terrain: new Array(81).fill(0), units, seed: 7, objective: 'all', loot: [], goals: [], waves: [], queue: true, overtime: 30, turnLimit: 40, relics: { P: [], E: [] } });
    const me = s.units[0];
    let acts = 0;
    let rest = 0;
    for (let g = 0; g < 4000 && !s.over; g++) {
      AG.AI.playTurn(s, s.side, { stance: 'balanced', temp: 0.3 });
      for (const e of s.events) {
        if (e.t === 'action' && e.uid === me.uid && !e.ai) acts++;
        if (e.t === 'sitout' && e.uid === me.uid && e.why !== 'passive') rest++;
      }
      s.events.length = 0;
    }
    assert.ok(acts >= 1, `${t} used ${D.UNITS[t].act.name}`);
    assert.ok(rest >= 2 * Math.min(acts, 2) || !me.alive, `${t} rested between them (${acts} acts, ${rest} turns resting)`);
  }
});

console.log(`legendary: ${passed} tests passed`);
