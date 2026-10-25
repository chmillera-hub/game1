// The trigger passives and relics: crits, executions, explosions, bounces, spreading
// poison and fire, the dead rising, bodyguards and the rest. Run: node tests/fun.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js']);
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

function board(units, relics, opts = {}) {
  const s = E.createBattle(Object.assign({ w: 9, h: 9, terrain: new Array(81).fill(0), units, relics: Object.assign({ P: [], E: [] }, relics), seed: 7 }, opts));
  if (!opts.queue) s.side = 'P';
  return s;
}

function act(s, u, target, ai) {
  s.side = u.team;
  s.spent = false;
  u.activated = false;
  u.wait = 0;
  assert.ok(E.beginActivation(s, u.uid), 'can activate ' + u.type);
  assert.ok(E.performAction(s, u.uid, Object.assign({ ai: ai || 0 }, target)), 'action allowed for ' + u.type);
  if (s.act) E.finishActivation(s, null);
}

const events = (s, t) => s.events.filter((e) => e.t === t);
const at = (s, x, y) => s.units.find((u) => u.alive && u.x === x && u.y === y);

test('critical hits deal double damage', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 7 },
    { type: 'golem', team: 'E', x: 4, y: 4 },
  ]);
  const [ar, go] = s.units;
  go.block = 0;
  ar.props.crit = 1;
  const plain = E.calcHit(s, ar, go, {}).dmg;
  act(s, ar, { kind: 'unit', uid: go.uid });
  assert.strictEqual(events(s, 'crit').length, 1);
  assert.strictEqual(go.maxHp - go.hp, plain * 2);
});

test('Deadeye: every third basic shot is a sure critical', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 8, level: 3 },
    { type: 'golem', team: 'E', x: 4, y: 4 },
  ]);
  const [ar, go] = s.units;
  go.block = 0;
  go.hp = go.maxHp = 999;
  for (let i = 0; i < 6; i++) act(s, ar, { kind: 'unit', uid: go.uid });
  assert.deepStrictEqual(events(s, 'crit').map((e) => e.deadeye), [true, true]);
});

test('Execute finishes off a foe left below 20%, never a boss', () => {
  const s = board([
    { type: 'assassin', team: 'P', x: 4, y: 5, a1: 'as_smoke', talents: ['as_execute'] },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 0 },
  ]);
  const [as, kn] = s.units;
  assert.ok(as.props.execute === 0.2);
  kn.block = 0;
  kn.hp = Math.round(kn.maxHp * 0.2) + E.calcHit(s, as, kn, {}).dmg;
  act(s, as, { kind: 'unit', uid: kn.uid });
  assert.ok(!kn.alive && events(s, 'execute').length === 1);
});

test("Executioner's Hood: below 15% is the end", () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'knight', team: 'E', x: 4, y: 4, facing: 0 },
    ],
    { P: ['executioner_hood'] }
  );
  const [a, b] = s.units;
  b.block = 0;
  b.hp = Math.round(b.maxHp * 0.15) + E.calcHit(s, a, b, {}).dmg - 1;
  act(s, a, { kind: 'unit', uid: b.uid });
  assert.ok(!b.alive);
});

test('Powder Keg: a fallen unit explodes on enemies beside it, sparing its friends', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'knight', team: 'P', x: 5, y: 5 },
      { type: 'berserker', team: 'E', x: 4, y: 4 },
      { type: 'knight', team: 'E', x: 3, y: 5 },
    ],
    { P: ['powder_keg'] }
  );
  const [k, friend, be, foe] = s.units;
  k.hp = 1;
  k.block = 0;
  act(s, be, { kind: 'unit', uid: k.uid });
  assert.ok(!k.alive);
  assert.strictEqual(friend.hp, friend.maxHp, 'its friend is spared');
  assert.ok(foe.hp < foe.maxHp, 'the enemy beside it is hurt');
});

test('trophies: each kill adds 10% damage, up to five', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'scout', team: 'E', x: 4, y: 4 },
      { type: 'golem', team: 'E', x: 0, y: 0 },
    ],
    { P: ['trophy_rack'] }
  );
  const [k, sc, go] = s.units;
  const before = E.calcHit(s, k, go, {}).dmg;
  sc.hp = 1;
  sc.block = 0;
  act(s, k, { kind: 'unit', uid: sc.uid });
  assert.strictEqual(k.trophies, 1);
  assert.ok(E.calcHit(s, k, go, {}).dmg > before);
});

test('Ricochet: the arrow bounces to a second enemy within 2 tiles', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 8, talents: ['a_ricochet'] },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
    { type: 'knight', team: 'E', x: 5, y: 3, facing: 2 },
  ]);
  const [ar, k1, k2] = s.units;
  k1.block = k2.block = 0;
  act(s, ar, { kind: 'unit', uid: k1.uid });
  assert.strictEqual(events(s, 'bounce').length, 1);
  assert.ok(k2.hp < k2.maxHp);
});

test("Plague Doctor's Mask: a poisoned enemy's poisons leap to its neighbours", () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'archer', team: 'P', x: 0, y: 8 },
      { type: 'scout', team: 'E', x: 4, y: 4 },
      { type: 'knight', team: 'E', x: 5, y: 4 },
    ],
    { P: ['plague_mask'] }
  );
  const [k, ar, sc, nb] = s.units;
  E.applyStatus(s, ar, sc, { poison: [2, 5] }, ar.act);
  sc.hp = 1;
  sc.block = 0;
  act(s, k, { kind: 'unit', uid: sc.uid });
  assert.ok(nb.poison && nb.poison.dmg === 5, 'the neighbour caught it');
});

test('Shadow Pact: the Witch raises the first two enemies it slays', () => {
  const s = board([
    { type: 'witch', team: 'P', x: 4, y: 8, level: 3 },
    { type: 'scout', team: 'E', x: 4, y: 6 },
  ]);
  const [wi, sc] = s.units;
  sc.hp = 1;
  act(s, wi, { kind: 'dir', d: 0 });
  const sk = at(s, 4, 6);
  assert.ok(sk && sk.type === 'skeleton' && sk.team === 'P', 'a skeleton rises for you');
});

test('Loyal Wolf: the rider falls, the wolf fights on', () => {
  const s = board([
    { type: 'beastrider', team: 'P', x: 4, y: 5, talents: ['br_wolf'] },
    { type: 'berserker', team: 'E', x: 4, y: 4 },
  ]);
  const [br, be] = s.units;
  br.hp = 1;
  br.block = 0;
  act(s, be, { kind: 'unit', uid: br.uid });
  const w = at(s, 4, 5);
  assert.ok(w && w.type === 'wolf' && w.team === 'P');
  assert.ok(!s.over, 'the battle goes on');
});

test('Mirror Aegis: the first hit bounces back, the second lands', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5 },
      { type: 'berserker', team: 'E', x: 4, y: 4 },
    ],
    { P: ['mirror_aegis'] }
  );
  const [k, be] = s.units;
  k.block = 0;
  act(s, be, { kind: 'unit', uid: k.uid });
  assert.strictEqual(k.hp, k.maxHp);
  assert.ok(be.hp < be.maxHp && events(s, 'reflect').length === 1);
  act(s, be, { kind: 'unit', uid: k.uid });
  assert.ok(k.hp < k.maxHp);
});

test("Gambler's Dice crowns one Champion with half again the health", () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 3, y: 8 },
      { type: 'knight', team: 'P', x: 5, y: 8 },
      { type: 'golem', team: 'E', x: 4, y: 0 },
    ],
    { P: ['gamblers_dice'] }
  );
  const champs = s.units.filter((u) => u.champion);
  assert.strictEqual(champs.length, 1);
  assert.strictEqual(champs[0].maxHp, Math.round(52 * 1.5));
});

test('Bodyguard: the knight takes the first blow aimed at its neighbour, once between its turns', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 6, talents: ['k_bodyguard'] },
    { type: 'archer', team: 'P', x: 3, y: 6 },
    { type: 'archer', team: 'E', x: 3, y: 3 },
  ]);
  const [kn, ar, foe] = s.units;
  kn.block = ar.block = 0;
  act(s, foe, { kind: 'unit', uid: ar.uid });
  assert.strictEqual(ar.hp, ar.maxHp, 'the archer is untouched');
  assert.ok(kn.hp < kn.maxHp && events(s, 'intercept').length === 1);
  act(s, foe, { kind: 'unit', uid: ar.uid });
  assert.ok(ar.hp < ar.maxHp, 'the next one lands');
});

test('Phalanx Standard and Lone Wolf Pelt reward how you stand', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 6 },
      { type: 'knight', team: 'P', x: 3, y: 6 },
      { type: 'knight', team: 'P', x: 5, y: 6 },
      { type: 'knight', team: 'P', x: 0, y: 8 },
      { type: 'knight', team: 'E', x: 4, y: 2 },
    ],
    { P: ['phalanx_standard', 'lone_wolf'] }
  );
  const [mid, , , alone, foe] = s.units;
  const plain = board([
    { type: 'knight', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'E', x: 4, y: 2 },
  ]);
  const base = E.calcHit(plain, plain.units[1], plain.units[0], {}).dmg;
  assert.ok(E.calcHit(s, foe, mid, {}).dmg < base, 'flanked by friends: harder to hurt');
  assert.ok(E.calcHit(s, alone, foe, {}).dmg > E.calcHit(plain, plain.units[0], plain.units[1], {}).dmg, 'alone: hits harder');
});

test('Halo: healing past full HP becomes a shield, up to 15', () => {
  const s = board([
    { type: 'cleric', team: 'P', x: 4, y: 7, talents: ['c_halo'] },
    { type: 'knight', team: 'P', x: 4, y: 6 },
    { type: 'golem', team: 'E', x: 4, y: 0 },
  ]);
  const [cl, kn] = s.units;
  kn.hp = kn.maxHp - 2;
  act(s, cl, { kind: 'self' });
  assert.strictEqual(kn.hp, kn.maxHp);
  assert.ok(kn.shield > 0 && kn.shield <= 15);
});

test('Goblin Firecrackers open the battle on three foes', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'knight', team: 'E', x: 1, y: 0 },
      { type: 'knight', team: 'E', x: 4, y: 0 },
      { type: 'knight', team: 'E', x: 7, y: 0 },
      { type: 'knight', team: 'E', x: 4, y: 1 },
    ],
    { P: ['firecrackers'] },
    { queue: true }
  );
  while (s.side !== 'P') E.pass(s);
  assert.strictEqual(s.units.filter((u) => u.team === 'E' && u.hp < u.maxHp).length, 3);
});

test('Magnetic Core yanks the nearest foe a step closer', () => {
  const s = board(
    [
      { type: 'golem', team: 'P', x: 4, y: 8, talents: ['g_magnet'] },
      { type: 'archer', team: 'E', x: 4, y: 5 },
    ],
    {},
    { queue: true }
  );
  const [, ar] = s.units;
  while (s.side !== 'P') E.pass(s);
  assert.strictEqual(ar.y, 6, 'pulled from 3 tiles to 2');
});

test('Discord: a paralyzed foe lashes out at its neighbour', () => {
  const s = board([
    { type: 'enchantress', team: 'P', x: 4, y: 8, talents: ['e_discord'] },
    { type: 'knight', team: 'E', x: 4, y: 5 },
    { type: 'knight', team: 'E', x: 5, y: 5 },
  ]);
  const [en] = s.units;
  act(s, en, { kind: 'tile', x: 4, y: 5 });
  assert.ok(events(s, 'discord').length >= 1);
});

test('Overload and Shatter Shield: wards go out with a bang or a blessing', () => {
  const s = board([
    { type: 'lightning', team: 'P', x: 4, y: 6, talents: ['l_overload'] },
    { type: 'barrier', team: 'P', x: 0, y: 8, talents: ['bw_shatter'] },
    { type: 'knight', team: 'P', x: 1, y: 8 },
    { type: 'berserker', team: 'E', x: 4, y: 5 },
    { type: 'knight', team: 'E', x: 3, y: 5 },
    { type: 'berserker', team: 'E', x: 0, y: 7 },
  ]);
  const [lw, bw, kn, be, far, be2] = s.units;
  lw.hp = 1;
  act(s, be, { kind: 'unit', uid: lw.uid });
  assert.ok(!lw.alive && far.hp < far.maxHp, 'the ward discharged 2 tiles out');
  bw.hp = 1;
  act(s, be2, { kind: 'unit', uid: bw.uid });
  assert.ok(!bw.alive && kn.shield === 20, 'its friend got the shield');
});

test('Combustion: a burning foe it slays explodes and sets its neighbours alight', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8, talents: ['p_combust'] },
    { type: 'scout', team: 'E', x: 4, y: 5 },
    { type: 'golem', team: 'E', x: 5, y: 5 },
  ]);
  const [py, sc, go] = s.units;
  sc.burn = { turns: 2, dmg: 5, src: py.uid };
  sc.hp = 1;
  act(s, py, { kind: 'tile', x: 4, y: 5 });
  assert.ok(!sc.alive);
  assert.ok(go.burn, 'the golem beside it burns');
});

test('Blood Pact and Glass Crown: the price of power', () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 6 },
      { type: 'knight', team: 'E', x: 4, y: 2 },
    ],
    { P: ['blood_pact', 'glass_crown'] }
  );
  const [k, foe] = s.units;
  assert.strictEqual(k.maxHp, Math.round(52 * 0.75));
  assert.strictEqual(k.hp, Math.round(k.maxHp * 0.75));
  const plain = board([
    { type: 'knight', team: 'P', x: 4, y: 6 },
    { type: 'knight', team: 'E', x: 4, y: 2 },
  ]);
  assert.ok(E.calcHit(s, k, foe, {}).dmg > E.calcHit(plain, plain.units[0], plain.units[1], {}).dmg);
});

console.log(`fun: ${passed} tests passed`);
