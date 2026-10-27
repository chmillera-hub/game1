// Gambler's Dice: one unit wears the Champion's crown between battles. If it sits a battle
// out, the Cleric wears it (else another unit on the field): it is never wasted. After each
// win it passes to a random unit that fought.
// Run: node tests/crown.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js', 'run.js']);
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

function setup(seed) {
  const run = R.newRun({ seed: seed || 3, warband: 'vanguard' });
  for (const t of ['berserker', 'archer']) R.addRecruit(run, t);
  assert.ok(R.chooseChallenge(run, 0), 'a battle to fight');
  return run;
}
const champs = (s) => s.units.filter((u) => u.team === 'P' && u.champion);
const deploy = (run, units) => units.map((u, i) => ({ rid: u.id, x: 1 + i, y: 8, facing: 0 }));

test('taking the relic crowns one of your units at once', () => {
  const run = setup();
  assert.strictEqual(R.crownHolder(run), null, 'no relic, no crown');
  R.gainRelic(run, 'gamblers_dice');
  assert.ok(run.champion && run.roster.some((u) => u.id === run.champion));
});

test('the crowned unit fights: it is the Champion, and the only one', () => {
  const run = setup(5);
  R.gainRelic(run, 'gamblers_dice');
  const holder = R.crownHolder(run);
  const others = run.roster.filter((u) => u !== holder).slice(0, 2);
  const s = E.createBattle(R.battleConfig(run, deploy(run, [holder, ...others])));
  const c = champs(s);
  assert.strictEqual(c.length, 1);
  assert.strictEqual(c[0].name, holder.name, 'the crowned unit itself');
  assert.ok(c[0].maxHp > 1.4 * AG.Data.UNITS[holder.type].hp * 0.9, '+50% max HP');
});

test('it sits out: the Cleric wears the crown for the battle; no Cleric either: another unit does', () => {
  const run = setup(7);
  R.gainRelic(run, 'gamblers_dice');
  const cleric = R.coreUnit(run) || run.roster.find((u) => u.type === 'cleric');
  assert.ok(cleric, 'the warband has its Cleric');
  // Crown someone else, then leave them on the bench.
  const other = run.roster.find((u) => u !== cleric);
  run.champion = other.id;
  const field = run.roster.filter((u) => u !== other).slice(0, 3);
  assert.ok(field.includes(cleric) || (field.push(cleric) && true));
  let s = E.createBattle(R.battleConfig(run, deploy(run, field)));
  assert.strictEqual(champs(s).length, 1, 'never wasted');
  assert.strictEqual(champs(s)[0].type, 'cleric', 'the Cleric wears it');
  assert.strictEqual(run.champion, other.id, 'the crown still belongs to the benched unit');
  const noCleric = run.roster.filter((u) => u !== other && u !== cleric).slice(0, 2);
  s = E.createBattle(R.battleConfig(run, deploy(run, noCleric)));
  assert.strictEqual(champs(s).length, 1, 'still never wasted');
});

test('after a win the crown passes to a unit that fought', () => {
  for (const seed of [11, 12, 13, 14]) {
    const run = setup(seed);
    R.gainRelic(run, 'gamblers_dice');
    const field = run.roster.slice(0, 3);
    const dep = deploy(run, field);
    const s = E.createBattle(R.battleConfig(run, dep));
    s.over = true;
    s.winner = 'P';
    R.finishBattle(run, s, dep);
    assert.ok(field.some((u) => u.id === run.champion), `seed ${seed}: crowned one of those who fought`);
  }
});

test('outside a campaign (a Hall match) the dice still pick a Champion', () => {
  const s = E.createBattle({ w: 9, h: 9, terrain: new Array(81).fill(0), seed: 2, objective: 'all', loot: [], goals: [], waves: [], relics: { P: ['gamblers_dice'], E: [] }, units: [
    { type: 'knight', team: 'P', x: 3, y: 8 }, { type: 'archer', team: 'P', x: 5, y: 8 }, { type: 'orc', team: 'E', x: 4, y: 0 },
  ] });
  assert.strictEqual(champs(s).length, 1);
});

console.log(`crown: ${passed} tests passed`);
