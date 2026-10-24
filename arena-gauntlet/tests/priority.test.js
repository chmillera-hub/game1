// The player's priority target: the army goes all out for it, then back to normal.
// Run: node tests/priority.test.js
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

// Play until the player has had `n` turns, the player's AI using `focus`.
function play(s, n, focus) {
  for (let turns = 0, g = 0; turns < n && !s.over && g < 500; g++) {
    const team = s.side;
    AI.playTurn(s, team, { stance: 'balanced', temp: 0, focus: team === 'P' ? focus : null });
    if (team === 'P') turns++;
  }
}

const army = () => [
  { type: 'knight', team: 'P', x: 3, y: 8 },
  { type: 'archer', team: 'P', x: 5, y: 8 },
  { type: 'orc', team: 'E', x: 4, y: 3 },
  { type: 'orc', team: 'E', x: 5, y: 3 },
];
const chest = { loot: [{ id: 'c1', kind: 'chest', x: 0, y: 2 }] };

test('left alone, the army ignores a chest', () => {
  const s = battle(army(), chest);
  play(s, 8, null);
  assert.ok(!s.loot[0].taken);
});

test('made the priority, a unit goes and takes the chest', () => {
  const s = battle(army(), chest);
  play(s, 8, { loot: 'c1' });
  assert.ok(s.loot[0].taken, 'the chest is taken');
  assert.strictEqual(s.byId[s.loot[0].by].team, 'P');
  assert.strictEqual(AI.focusOf(s, 'P', { loot: 'c1' }), null, 'and the priority is done');
});

test('made the priority, an enemy is struck first even when another is the better hit', () => {
  const units = [
    { type: 'archer', team: 'P', x: 4, y: 8 },
    { type: 'scout', team: 'E', x: 4, y: 5, hp: 5 },
    { type: 'knight', team: 'E', x: 1, y: 4 },
  ];
  const first = (focus) => {
    const s = battle(units.map((u) => Object.assign({}, u)));
    E.pass(s); // the enemy's first turn
    s.units[1].hp = 4; // a nearly dead scout: the obvious kill
    const plan = AI.chooseActivation(s, 'P', { stance: 'balanced', temp: 0, focus });
    return plan.target && s.byId[plan.target.uid] ? s.byId[plan.target.uid].type : plan.kind;
  };
  assert.strictEqual(first(null), 'scout', 'normally it finishes the scout');
  const s = battle(units);
  assert.strictEqual(first({ uid: s.units[2].uid }), 'knight', 'with the knight as priority, it shoots the knight');
});

test('once the priority target falls, the army goes back to normal', () => {
  const s = battle(army());
  const target = s.units[3];
  play(s, 30, { uid: target.uid });
  assert.ok(!target.alive || s.over, 'the target went down');
  assert.strictEqual(AI.focusOf(s, 'P', { uid: target.uid }), null);
  const ctx = AI.makeCtx(s, 'P', { focus: { uid: target.uid } });
  assert.strictEqual(ctx.focus, null, 'no pull toward a fallen target');
});

test('an ally or a taken chest is never a priority', () => {
  const s = battle(army(), chest);
  assert.strictEqual(AI.focusOf(s, 'P', { uid: s.units[0].uid }), null);
  s.loot[0].taken = true;
  assert.strictEqual(AI.focusOf(s, 'P', { loot: 'c1' }), null);
});

console.log(`priority: ${passed} tests passed`);
