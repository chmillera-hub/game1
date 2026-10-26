// The Death Knight: the Eclipse Wyrm's reaper. Its basic attack sweeps every adjacent enemy;
// Reaper's Charge runs straight through a line of enemies, cutting each one it passes.
// Run: node tests/deathknight.test.js
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

// The knight at (4, 8) facing up the board; `others` are [type, team, x, y].
function battle(others, rocks) {
  const terrain = new Array(81).fill(E.T_GRASS);
  for (const [x, y] of rocks || []) terrain[y * 9 + x] = E.T_ROCK;
  const s = E.createBattle({ w: 9, h: 9, terrain, seed: 3, objective: 'all', loot: [], goals: [], waves: [], relics: { P: [], E: [] }, units: [
    { type: 'death_knight', team: 'E', x: 4, y: 8, facing: 0 },
    ...others.map(([type, team, x, y]) => ({ type, team, x, y })),
  ] });
  const dk = s.units[0];
  s.side = 'E';
  s.spent = false;
  dk.wait = 0;
  dk.activated = false;
  return { s, dk, ai: dk.acts.findIndex((a) => a.kind === 'charge') };
}

test('a boss of the final challenge, drawn as a reaper', () => {
  const T = D.UNITS.death_knight;
  assert.ok(T.boss);
  assert.strictEqual(T.act.kind, 'cleave');
  assert.ok(T.extra.some((a) => a.kind === 'charge'));
  assert.ok(AG.Sprites.HEIGHT.death_knight);
  assert.ok(D.ENCOUNTERS.mega.units.includes('death_knight'));
});

test('the charge runs through a line of enemies, cuts each, weakens them, and lands past them', () => {
  const { s, dk, ai } = battle([['knight', 'P', 4, 7], ['archer', 'P', 4, 6], ['scout', 'P', 0, 0]]);
  const [, a, b] = s.units;
  const hp = [a.hp, b.hp];
  const t = E.targetsFrom(s, dk, ai).find((x) => x.d === 0 || (x.x === 4 && x.y < 6));
  assert.ok(t, 'a charge up the line');
  assert.deepStrictEqual([t.x, t.y], [4, 4], 'stops on the farthest open tile, 4 away');
  assert.ok(E.beginActivation(s, dk.uid));
  assert.ok(E.performAction(s, dk.uid, t));
  assert.deepStrictEqual([dk.x, dk.y], [4, 4], 'stands past them');
  assert.ok(a.hp < hp[0] && b.hp < hp[1], 'both are cut');
  assert.ok(a.weak > 0 && b.weak > 0, 'and weakened');
  assert.ok(s.events.some((e) => e.t === 'charge'));
  assert.strictEqual(s.occ[E.idx(s, 4, 8)], 0, 'its old tile is free');
});

test('its own side is spared, and a rock stops the run short', () => {
  const { s, dk, ai } = battle([['knight', 'E', 4, 7], ['archer', 'P', 4, 6], ['scout', 'P', 0, 0]], [[4, 5]]);
  // Up the line: the ally, the enemy, then a rock. No open tile past them: no charge that way.
  assert.ok(!E.targetsFrom(s, dk, ai).some((t) => t.x === 4 && t.y < 8), 'nowhere to land');
  const s2 = battle([['knight', 'E', 4, 7], ['archer', 'P', 4, 6], ['scout', 'P', 0, 0]]);
  const t = E.targetsFrom(s2.s, s2.dk, s2.ai).find((x) => x.x === 4 && x.y < 8);
  const ally = s2.s.units[1];
  const hp = ally.hp;
  assert.ok(E.beginActivation(s2.s, s2.dk.uid));
  assert.ok(E.performAction(s2.s, s2.dk.uid, t));
  assert.strictEqual(ally.hp, hp, 'the ally it ran past is unhurt');
});

test('the AI uses the charge when a line of foes stands before it', () => {
  let charged = 0;
  for (let seed = 0; seed < 6; seed++) {
    const { s } = battle([['knight', 'P', 4, 6], ['archer', 'P', 4, 5], ['cleric', 'P', 4, 4], ['scout', 'P', 8, 0]]);
    s.seed = seed;
    AG.AI.playTurn(s, 'E', { stance: 'aggressive', temp: 0.3 });
    if (s.events.some((e) => e.t === 'charge')) charged++;
  }
  assert.ok(charged >= 3, `charged ${charged} of 6 times`);
});

test('the final challenge brings it, with the Wyrm and the Lich', () => {
  const run = R.newRun({ seed: 7, warband: 'vanguard' });
  R.startAct(run, 3);
  const enc = R.genEncounter(run, { id: 'mega', row: 6, kind: 'boss', tier: 'mega', mega: true });
  const types = enc.units.map((u) => u.type);
  for (const t of ['void_wyrm', 'death_knight', 'lich']) assert.ok(types.includes(t), t);
});

console.log(`deathknight: ${passed} tests passed`);
