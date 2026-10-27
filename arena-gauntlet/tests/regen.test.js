// Regen heals a unit every time its turn comes, acting or passing: paralyzed, cooling down,
// rooted or dazzled, it still heals. Poison is the only status that stops it.
// Run: node tests/regen.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js', 'run.js']);
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

// A wounded Frost Giant with Regen 2 under `status`, its side's turns played out: the HP
// it healed by regen.
function regenUnder(status) {
  const terrain = new Array(81).fill(E.T_GRASS);
  const s = E.createBattle({ w: 9, h: 9, terrain, seed: 1, objective: 'all', loot: [], goals: [], waves: [], relics: { P: [], E: [] }, queue: true, units: [
    { type: 'frostgiant', team: 'P', x: 4, y: 7 },
    { type: 'knight', team: 'E', x: 0, y: 0 },
  ] });
  const g = s.units.find((u) => u.type === 'frostgiant');
  g.regen = 2;
  g.hp -= 30;
  if (status === 'poison') g.poison = { dmg: 1, turns: 3 };
  else if (status) g[status] = 3;
  for (let i = 0; i < 4 && !s.over; i++) E.endTurn(s);
  return s.events.filter((e) => e.t === 'heal' && e.why === 'regen' && e.uid === g.uid).reduce((n, e) => n + e.amount, 0);
}

test('regen heals on every turn of a healthy unit', () => assert.ok(regenUnder(null) >= 4));
for (const st of ['para', 'wait', 'root', 'weak']) {
  test(`regen still heals while ${st}`, () => assert.ok(regenUnder(st) >= 4, `${st}: healed ${regenUnder(st)}`));
}
test('poison stops regen', () => assert.strictEqual(regenUnder('poison'), 0));

console.log(`regen: ${passed} tests passed`);
