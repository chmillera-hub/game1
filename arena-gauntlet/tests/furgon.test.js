// The Furgon's shrubs guard the Cleric while it lives, else whoever has the least HP: a
// shrub goes where it keeps the enemy's walkers from reaching them, on their real path.
// Run: node tests/furgon.test.js
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

// Row 5 is a wall of rock but for the gaps given; your side below it, the enemy above.
function field(gaps, units, seed) {
  const terrain = new Array(81).fill(E.T_GRASS);
  for (let x = 0; x < 9; x++) if (!gaps.includes(x)) terrain[5 * 9 + x] = E.T_ROCK;
  const s = E.createBattle({ w: 9, h: 9, terrain, seed: seed || 1, objective: 'all', loot: [], goals: [], waves: [], relics: { P: [], E: [] }, units });
  s.side = 'P';
  return s;
}

// The Furgon takes its turn: where did its shrub go (null if it grew none)?
function furgonTurn(s) {
  const fu = s.units.find((u) => u.type === 'furgon');
  for (const u of s.units) if (u.team === 'P' && u !== fu) u.wait = 3; // only the Furgon is ready
  const opts = { stance: 'balanced', temp: 0 };
  const plan = AG.AI.chooseActivation(s, 'P', opts);
  assert.strictEqual(plan && plan.uid, fu.uid, 'the Furgon acts');
  AG.AI.runPlan(s, plan, opts);
  const g = s.events.find((e) => e.t === 'summon');
  return g ? [g.x, g.y] : null;
}

// A shrub on the gap, or just behind it, seals that way through.
const seals = (spot, gx) => !!spot && spot[0] === gx && (spot[1] === 5 || spot[1] === 6);

test('one gap: the Furgon seals it before the brute walks through to the Cleric', () => {
  let sealed = 0;
  for (let seed = 1; seed <= 6; seed++) {
    const s = field([4], [
      { type: 'cleric', team: 'P', x: 4, y: 8 },
      { type: 'furgon', team: 'P', x: 2, y: 7 },
      { type: 'berserker', team: 'E', x: 4, y: 3, facing: 2 },
      { type: 'orc', team: 'E', x: 5, y: 2, facing: 2 },
    ], seed);
    if (seals(furgonTurn(s), 4)) sealed++;
  }
  assert.ok(sealed >= 5, `sealed the gap ${sealed}/6`);
});

test('no Cleric: it guards the ally with the least HP', () => {
  let right = 0;
  for (let seed = 1; seed <= 6; seed++) {
    const s = field([1, 7], [
      { type: 'archer', team: 'P', x: 1, y: 8 },
      { type: 'knight', team: 'P', x: 7, y: 8 },
      { type: 'furgon', team: 'P', x: 4, y: 7 },
      { type: 'berserker', team: 'E', x: 1, y: 3, facing: 2 },
      { type: 'berserker', team: 'E', x: 7, y: 3, facing: 2 },
    ], seed);
    s.units[1].hp = 6; // the knight is nearly down
    if (seals(furgonTurn(s), 7)) right++;
  }
  assert.ok(right >= 5, `sealed the wounded knight's gap ${right}/6`);
});

test('the Cleric comes first, even when another ally has less HP', () => {
  let right = 0;
  for (let seed = 1; seed <= 6; seed++) {
    const s = field([1, 7], [
      { type: 'cleric', team: 'P', x: 1, y: 8 },
      { type: 'knight', team: 'P', x: 7, y: 8 },
      { type: 'furgon', team: 'P', x: 4, y: 7 },
      { type: 'berserker', team: 'E', x: 1, y: 3, facing: 2 },
      { type: 'berserker', team: 'E', x: 7, y: 3, facing: 2 },
    ], seed);
    s.units[1].hp = 6;
    if (seals(furgonTurn(s), 1)) right++;
  }
  assert.ok(right >= 5, `sealed the Cleric's gap ${right}/6`);
});

console.log(`furgon: ${passed} tests passed`);
