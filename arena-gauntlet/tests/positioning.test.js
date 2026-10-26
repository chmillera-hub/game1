// The battles play themselves, so the AI has to know the picks that depend on where units
// stand: spread out for the Lone Wolf Pelt, close ranks for the Phalanx Standard, hold
// still to Hold the Line, end moves beside enemies with Thunderstep, and aim Ricochet at a
// crowd. Each is checked against the same fight without the pick.
// Run: node tests/positioning.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js', 'run.js']);
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

function battle(units, relicsP, seed) {
  return E.createBattle({ w: 9, h: 9, terrain: new Array(81).fill(E.T_GRASS), seed: seed || 1, objective: 'all', loot: [], goals: [], waves: [], relics: { P: relicsP || [], E: [] }, units });
}

const alliesBeside = (s, u) => s.units.filter((v) => v !== u && v.alive && v.team === u.team && !v.nonCombat && Math.abs(v.x - u.x) + Math.abs(v.y - u.y) === 1).length;

// Your side's turns only, the enemy standing still: where do your units end their turns?
function playP(s, turns, look) {
  for (let i = 0; i < turns && !s.over; i++) {
    if (s.side !== 'P') E.endTurn(s);
    if (s.over) break;
    const opts = { stance: 'balanced', temp: 0 };
    const plan = AG.AI.chooseActivation(s, 'P', opts);
    AG.AI.runPlan(s, plan, opts);
    const u = plan && s.byId[plan.uid];
    if (u && u.alive) look(u, s);
    s.events.length = 0;
  }
}

// Four fighters packed together, a line of archers up the board (all unkillable).
const army = () => [
  { type: 'berserker', team: 'P', x: 3, y: 8, facing: 0 },
  { type: 'berserker', team: 'P', x: 4, y: 8, facing: 0 },
  { type: 'knight', team: 'P', x: 5, y: 8, facing: 0 },
  { type: 'knight', team: 'P', x: 4, y: 7, facing: 0 },
  { type: 'archer', team: 'E', x: 1, y: 3, facing: 2 },
  { type: 'archer', team: 'E', x: 4, y: 2, facing: 2 },
  { type: 'archer', team: 'E', x: 7, y: 3, facing: 2 },
];

function huddle(relics) {
  let beside = 0;
  let n = 0;
  for (let seed = 1; seed <= 6; seed++) {
    const s = battle(army(), relics, seed);
    for (const u of s.units) u.hp = u.maxHp = 999;
    playP(s, 16, (u, st) => {
      beside += alliesBeside(st, u);
      n++;
    });
  }
  return beside / n;
}

test('the Lone Wolf Pelt spreads your units out; the Phalanx Standard closes ranks', () => {
  const plain = huddle([]);
  const wolf = huddle(['lone_wolf']);
  const phalanx = huddle(['phalanx_standard']);
  assert.ok(wolf < plain * 0.5, `Lone Wolf: ${wolf.toFixed(2)} allies beside each unit after its turn, vs ${plain.toFixed(2)} without`);
  assert.ok(phalanx > plain * 2, `Phalanx: ${phalanx.toFixed(2)} vs ${plain.toFixed(2)}`);
  console.log(`  allies beside a unit after its turn: ${plain.toFixed(2)} plain, ${wolf.toFixed(2)} Lone Wolf, ${phalanx.toFixed(2)} Phalanx`);
});

test('Hold the Line: holding its ground under fire is worth more to the AI, moving is not', () => {
  const score = (brace, x, y) => {
    const s = battle([
      { type: 'knight', team: 'P', x: 4, y: 6, facing: 0, level: 2, a2: 'k_plate' },
      { type: 'archer', team: 'E', x: 4, y: 2, facing: 2 },
      { type: 'archer', team: 'E', x: 2, y: 3, facing: 2 },
    ]);
    const kn = s.units[0];
    assert.ok(kn.traits.has('brace'), 'Hold the Line slotted');
    if (!brace) kn.traits.delete('brace');
    const ctx = AG.AI.makeCtx(s, 'P', { stance: 'balanced', temp: 0 });
    ctx.from = { uid: kn.uid, x: kn.x, y: kn.y };
    return E.withUnitAt(s, kn, x, y, () => AG.AI.positionValue(ctx, kn, x, y).score);
  };
  assert.ok(score(true, 4, 6) > score(false, 4, 6) + 1, 'staying put under the archers: worth more with it');
  assert.strictEqual(+score(true, 4, 5).toFixed(3), +score(false, 4, 5).toFixed(3), 'moving: no different');
});

test('Thunderstep: ending a move beside enemies is worth more to the AI', () => {
  const score = (step, x, y) => {
    const s = battle([
      { type: 'knight', team: 'P', x: 4, y: 8, facing: 0, enchant: 'thunderstep' },
      { type: 'scout', team: 'E', x: 4, y: 4, facing: 2 },
      { type: 'scout', team: 'E', x: 5, y: 5, facing: 2 },
    ]);
    const kn = s.units[0];
    assert.ok(kn.traits.has('thunderstep'), 'enchanted');
    if (!step) kn.traits.delete('thunderstep');
    const ctx = AG.AI.makeCtx(s, 'P', { stance: 'balanced', temp: 0 });
    ctx.from = { uid: kn.uid, x: kn.x, y: kn.y };
    return E.withUnitAt(s, kn, x, y, () => AG.AI.positionValue(ctx, kn, x, y).score);
  };
  // (4, 5) is beside both scouts; (3, 7) beside neither; (4, 8) is where it stands.
  assert.ok(score(true, 4, 5) > score(false, 4, 5) + 3, 'beside two enemies: worth more with it');
  assert.strictEqual(+score(true, 3, 7).toFixed(3), +score(false, 3, 7).toFixed(3), 'away from them: no different');
  assert.strictEqual(+score(true, 4, 8).toFixed(3), +score(false, 4, 8).toFixed(3), 'staying put: no move, no shock');
});

test('Ricochet: the archer shoots into the crowd', () => {
  const crowd = { plain: 0, ricochet: 0 };
  for (const k of ['plain', 'ricochet']) {
    for (let seed = 1; seed <= 6; seed++) {
      const s = battle([
        { type: 'archer', team: 'P', x: 4, y: 8, facing: 0, level: 2, a2: k === 'ricochet' ? 'a_ricochet' : 'a_eagle' },
        // A lone foe, and two standing together, all in range.
        { type: 'scout', team: 'E', x: 2, y: 6, facing: 2 },
        { type: 'scout', team: 'E', x: 5, y: 5, facing: 2 },
        { type: 'scout', team: 'E', x: 6, y: 5, facing: 2 },
      ], [], seed);
      const ar = s.units[0];
      ar.move = 0;
      s.side = 'P';
      AG.AI.playTurn(s, 'P', { stance: 'balanced', temp: 0 });
      const shot = s.events.find((e) => e.t === 'action' && e.uid === ar.uid);
      if (shot && shot.target && shot.target.uid !== s.units[1].uid) crowd[k]++;
    }
  }
  assert.ok(crowd.ricochet > crowd.plain && crowd.ricochet >= 5, `into the crowd ${crowd.ricochet}/6 with Ricochet, ${crowd.plain}/6 without`);
  console.log(`  shots into the crowd: ${crowd.ricochet}/6 with Ricochet, ${crowd.plain}/6 without`);
});

test('every positioning pick says the AI plays to it', () => {
  for (const id of ['lone_wolf', 'phalanx_standard', 'shadow_cloak']) assert.ok(/The AI /.test(D.RELICS[id].desc), id);
  for (const id of ['k_plate', 'k_bodyguard', 'w_drift', 'g_moss', 'e_discord', 'p_combust', 'a_ricochet', 'tb_shrapnel', 'w_contagion', 'mk_ward']) assert.ok(/The AI /.test(D.ABILITIES[id].desc), id);
  for (const id of ['flanker', 'guardian', 'pack_tactics']) assert.ok(/The AI /.test(D.SKILLS[id].desc), id);
  assert.ok(/The AI /.test(D.GEAR.momentum_boots.desc));
  assert.ok(/The AI /.test(D.ENCHANTS.thunderstep.desc) && /The AI /.test(D.ENCHANTS.holy_aegis.desc));
  for (const t of ['golem', 'knight', 'scout', 'assassin']) assert.ok(/The AI /.test(D.MASTERY[t].desc), t);
});

console.log(`positioning: ${passed} tests passed`);
