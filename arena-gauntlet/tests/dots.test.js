// Poison and burns split the work. Poison never takes on buildings or the undead, but it
// stops all healing and regen. Burns catch on buildings and the undead alike, and leave
// healing and regen alone.
// Run: node tests/dots.test.js
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

function battle(units) {
  const terrain = new Array(81).fill(E.T_GRASS);
  return E.createBattle({ w: 9, h: 9, terrain, seed: 1, objective: 'all', loot: [], goals: [], waves: [], relics: { P: [], E: [] }, queue: true, units });
}
const POISON = { poison: [3, 6] };
const BURN = { burn: [3, 6] };

test('poison does not take on buildings or the undead', () => {
  const s = battle([
    { type: 'witch', team: 'P', x: 4, y: 8 },
    { type: 'war_tent', team: 'E', x: 2, y: 2 },
    { type: 'crypt', team: 'E', x: 6, y: 2 },
    { type: 'tower', team: 'E', x: 4, y: 0 },
    { type: 'skeleton', team: 'E', x: 0, y: 4 },
    { type: 'specter', team: 'E', x: 8, y: 4 },
  ]);
  const src = s.units[0];
  for (const v of s.units.slice(1)) {
    E.applyStatus(s, src, v, POISON, { name: 'test' });
    assert.ok(!v.poison, `${v.type} is not poisoned`);
  }
});

test('burns catch on buildings and the undead, and burn them down turn by turn', () => {
  const s = battle([
    { type: 'pyromancer', team: 'P', x: 4, y: 8 },
    { type: 'war_tent', team: 'E', x: 2, y: 2 },
    { type: 'crypt', team: 'E', x: 6, y: 2 },
    { type: 'tower', team: 'E', x: 4, y: 0 },
    { type: 'skeleton', team: 'E', x: 0, y: 4 },
    { type: 'specter', team: 'E', x: 8, y: 4 },
  ]);
  const src = s.units[0];
  const foes = s.units.slice(1);
  for (const v of foes) {
    E.applyStatus(s, src, v, BURN, null);
    assert.ok(v.burn, `${v.type} catches fire`);
  }
  const hp0 = foes.map((v) => v.hp);
  for (let i = 0; i < 12 && !s.over; i++) E.endTurn(s);
  foes.forEach((v, i) => assert.ok(!v.alive || v.hp < hp0[i], `${v.type} burned (${hp0[i]} -> ${v.hp})`));
});

test('poison stops healing and regen; burns do not', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 3, y: 7 },
    { type: 'knight', team: 'P', x: 5, y: 7 },
    { type: 'knight', team: 'E', x: 4, y: 0 },
  ]);
  const [a, b, foe] = s.units;
  for (const u of [a, b]) {
    u.hp -= 40;
    u.regen = 3;
  }
  E.applyStatus(s, foe, a, POISON, { name: 'test' });
  E.applyStatus(s, foe, b, BURN, null);
  const regen = (u) => s.events.filter((e) => e.t === 'heal' && e.uid === u.uid).length;
  for (let i = 0; i < 6 && !s.over; i++) E.endTurn(s);
  assert.strictEqual(regen(a), 0, 'poisoned: no regen');
  assert.ok(regen(b) >= 1, 'burning: still regenerates');
  assert.ok(E.healBlocked(s, a) || !a.poison, 'poison blocks heals while it lasts');
  assert.ok(!E.healBlocked(s, b), 'a burn never blocks heals');
});

console.log(`dots: ${passed} tests passed`);
