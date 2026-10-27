// Poison and burns split the work. Poison never takes on buildings (wards included) or
// skeletons, and only those: golems, Specters and the Death Knight take it. It
// stops all healing and regen. Burns catch on buildings and the undead alike, and leave
// healing and regen alone. Both are elemental: magic resistance cuts them.
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

test('poison does not take on buildings or skeletons', () => {
  const s = battle([
    { type: 'witch', team: 'P', x: 4, y: 8 },
    { type: 'war_tent', team: 'E', x: 2, y: 2 },
    { type: 'crypt', team: 'E', x: 6, y: 2 },
    { type: 'tower', team: 'E', x: 4, y: 0 },
    { type: 'skeleton', team: 'E', x: 0, y: 4 },
    { type: 'skelarcher', team: 'E', x: 8, y: 4 },
    { type: 'colossus', team: 'E', x: 2, y: 6 },
    { type: 'lich', team: 'E', x: 6, y: 6 },
  ]);
  const src = s.units[0];
  for (const v of s.units.slice(1)) {
    E.applyStatus(s, src, v, POISON, { name: 'test' });
    assert.ok(!v.poison, `${v.type} is not poisoned`);
  }
});

test('the robed undead, Specters and the Death Knight, are poisoned like anyone', () => {
  const s = battle([
    { type: 'witch', team: 'P', x: 4, y: 8 },
    { type: 'specter', team: 'E', x: 2, y: 2 },
    { type: 'death_knight', team: 'E', x: 6, y: 2 },
  ]);
  for (const v of s.units.slice(1)) {
    E.applyStatus(s, s.units[0], v, POISON, { name: 'test' });
    assert.ok(v.poison, `${v.type} is poisoned`);
  }
});

test('golems and the Golem King can be poisoned; wards, like buildings, cannot', () => {
  const s = battle([
    { type: 'witch', team: 'P', x: 4, y: 8 },
    { type: 'golem', team: 'E', x: 2, y: 2 },
    { type: 'golem_king', team: 'E', x: 4, y: 0 },
    { type: 'barrier', team: 'E', x: 6, y: 2 },
    { type: 'lightning', team: 'E', x: 4, y: 4 },
  ]);
  const [src, golem, king, barrier, lightning] = s.units;
  for (const v of [golem, king, barrier, lightning]) E.applyStatus(s, src, v, POISON, { name: 'test' });
  assert.ok(golem.poison && king.poison, 'golems are poisoned');
  assert.ok(!barrier.poison && !lightning.poison, 'wards are not');
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

test('magic resistance cuts poison and burns alike', () => {
  const tick = (res, fx) => {
    const s = battle([
      { type: 'knight', team: 'P', x: 4, y: 7 },
      { type: 'knight', team: 'E', x: 4, y: 0 },
    ]);
    const [u, foe] = s.units;
    u.res = res;
    E.applyStatus(s, foe, u, fx, { name: 'test' });
    const hp = u.hp;
    E.endTurn(s);
    return hp - u.hp;
  };
  for (const fx of [{ poison: [3, 10] }, { burn: [3, 10] }]) {
    const k = Object.keys(fx)[0];
    assert.strictEqual(tick(0, fx), 10, `${k}: full damage with no magic resistance`);
    assert.strictEqual(tick(0.5, fx), 5, `${k}: halved at 50%`);
    assert.strictEqual(tick(-0.2, fx), 12, `${k}: worse on a unit weak to magic`);
  }
});

test("a Cleric's free Mend cannot help a poisoned ally; Blessing (1 Supply) cures and heals", () => {
  const AI = AG.AI;
  const run = (a1) => {
    const terrain = new Array(81).fill(E.T_GRASS);
    const s = E.createBattle({ w: 9, h: 9, terrain, seed: 1, objective: 'all', loot: [], goals: [], waves: [], relics: { P: [], E: [] }, units: [
      { type: 'cleric', team: 'P', x: 4, y: 8, a1 },
      { type: 'knight', team: 'P', x: 4, y: 6 },
      { type: 'knight', team: 'E', x: 0, y: 0 },
    ] });
    const [cl, kn] = s.units;
    kn.hp -= 30;
    kn.poison = { dmg: 5, turns: 3 };
    kn.wait = 5;
    s.side = 'P';
    const plan = AI.chooseActivation(s, 'P', { stance: 'balanced', temp: 0 });
    if (plan) AI.runPlan(s, plan, { stance: 'balanced', temp: 0 });
    return kn;
  };
  assert.strictEqual(AG.Data.ABILITIES.c_mend.cost, 0);
  const mended = run('c_mend');
  assert.ok(mended.poison && mended.hp === mended.maxHp - 30, 'Mend: still poisoned, not healed');
  assert.ok(AG.Data.ABILITIES.c_bless.cost >= 1);
  const blessed = run('c_bless');
  assert.ok(!blessed.poison && blessed.hp > blessed.maxHp - 30, 'Blessing: cured, then healed');
});

console.log(`dots: ${passed} tests passed`);
