// The player's AI plays for the mission and its bonus goals. Run: node tests/objectives.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js']);
const E = AG.Engine;
const AI = AG.AI;

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

function battle(units, opts = {}) {
  const w = 9;
  const h = 9;
  return E.createBattle(Object.assign({ w, h, terrain: new Array(w * h).fill(0), units, relics: { P: [], E: [] }, seed: 7, queue: true }, opts));
}

// What the player's due unit goes for first.
function firstTarget(s) {
  const plan = AI.chooseActivation(s, 'P', { stance: 'balanced', temp: 0 });
  const t = plan && plan.target && s.byId[plan.target.uid];
  return t || null;
}

test('the Commander comes first when killing it wins the battle', () => {
  const units = [
    { type: 'archer', team: 'P', x: 4, y: 8 },
    { type: 'knight', team: 'E', x: 2, y: 4, vip: true },
    { type: 'orc', team: 'E', x: 6, y: 4 },
  ];
  const s = battle(units, { objective: 'vip' });
  E.pass(s);
  s.units[2].hp = 20; // the orc is the easier hit
  assert.strictEqual(firstTarget(s), s.units[1], 'it shoots the Commander');
});

test('the wagon nearest its way out is hit first', () => {
  const s = battle(
    [
      { type: 'archer', team: 'P', x: 4, y: 8 },
      { type: 'cart', team: 'E', x: 3, y: 4, goal: true },
      { type: 'cart', team: 'E', x: 7, y: 4, goal: true },
      { type: 'orc', team: 'E', x: 4, y: 0 },
    ],
    { objective: 'destroy', cartExit: 0 }
  );
  E.pass(s); // the wagons roll one tile toward the left edge
  assert.ok(s.units[1].alive && s.units[1].x < s.units[2].x);
  assert.strictEqual(firstTarget(s), s.units[1]);
});

test('win within N turns: the army presses on, but not off a shrine it must hold', () => {
  const units = [
    { type: 'knight', team: 'P', x: 4, y: 8 },
    { type: 'orc', team: 'E', x: 4, y: 0 },
  ];
  const plain = AI.makeCtx(battle(units), 'P', {});
  const swift = AI.makeCtx(battle(units, { goals: [{ type: 'swift', turns: 10 }] }), 'P', {});
  assert.ok(swift.approach > plain.approach * 1.25);
  const hold = { x: 4, y: 4, need: 4 };
  const held = AI.makeCtx(battle(units, { hold, goals: [{ type: 'swift', turns: 10 }] }), 'P', {});
  assert.ok(Math.abs(held.approach - AI.makeCtx(battle(units, { hold }), 'P', {}).approach) < 1e-9);
  const enemy = AI.makeCtx(battle(units, { goals: [{ type: 'swift', turns: 10 }] }), 'E', {});
  assert.ok(Math.abs(enemy.approach - AI.makeCtx(battle(units), 'E', {}).approach) < 1e-9, 'the enemy plays as before');
});

test('block reinforcements: a landing tile is worth far more until enough are blocked', () => {
  const units = [
    { type: 'knight', team: 'P', x: 4, y: 8 },
    { type: 'orc', team: 'E', x: 4, y: 0 },
  ];
  const s = battle(units, { goals: [{ type: 'blockade', n: 2 }] });
  assert.strictEqual(AI.makeCtx(s, 'P', {}).markValue, 20);
  s.stats.blocked = 2;
  assert.strictEqual(AI.makeCtx(s, 'P', {}).markValue, 7, 'done: back to normal');
  assert.strictEqual(AI.makeCtx(battle(units), 'P', {}).markValue, 7);
});

console.log(`objectives: ${passed} tests passed`);
