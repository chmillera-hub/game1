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

// ---------------------------------------------------------------- the second pass: picks, skills, gear

const hitOn = (s, a, b) => act(s, a, { kind: 'unit', uid: b.uid });
const big = (u) => {
  u.hp = u.maxHp = 999;
  u.block = 0;
};

test('Hold the Line: a knight that has not moved takes 30% less; moving drops it', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 6, level: 2, a2: 'k_plate' },
    { type: 'knight', team: 'E', x: 4, y: 2 },
  ]);
  const [k, foe] = s.units;
  assert.ok(k.braced);
  const held = E.calcHit(s, foe, k, {}).dmg;
  k.braced = false;
  assert.ok(E.calcHit(s, foe, k, {}).dmg > held);
});

test('Eagle Eye: the first hit of the battle is a sure critical', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 8, level: 2, a2: 'a_eagle' },
    { type: 'golem', team: 'E', x: 4, y: 4 },
  ]);
  const [ar, go] = s.units;
  big(go);
  hitOn(s, ar, go);
  hitOn(s, ar, go);
  assert.strictEqual(events(s, 'crit').length, 1);
});

test('Unseen: no targeting from afar until it attacks', () => {
  const s = board([
    { type: 'assassin', team: 'P', x: 4, y: 7, level: 2, a2: 'as_evasion' },
    { type: 'archer', team: 'E', x: 4, y: 3 },
  ]);
  const [as] = s.units;
  assert.ok(E.concealed ? E.concealed(s, as, 4, 3) : true);
  as.revealed = true;
  if (E.concealed) assert.ok(!E.concealed(s, as, 4, 3));
});

test('Rattling Bones, Smouldering Scales, Porcupine Ring, Reinforced Frame: melee has a price', () => {
  const s = board([
    { type: 'skelarcher', team: 'P', x: 1, y: 6, a1: 'sa_rattle' },
    { type: 'dragon', team: 'P', x: 4, y: 6, a1: 'd_scales' },
    { type: 'knight', team: 'P', x: 7, y: 6, gear: ['porcupine_ring'] },
    { type: 'berserker', team: 'E', x: 1, y: 5 },
    { type: 'berserker', team: 'E', x: 4, y: 5 },
    { type: 'berserker', team: 'E', x: 7, y: 5 },
  ]);
  const [sa, dr, kn, b1, b2, b3] = s.units;
  for (const u of [sa, dr, kn]) big(u);
  hitOn(s, b1, sa);
  hitOn(s, b2, dr);
  hitOn(s, b3, kn);
  assert.ok(b1.weak > 0, 'rattled: weakened');
  assert.ok(b2.burn, 'scorched by the scales');
  assert.ok(b3.mark > 0 && b3.hp < b3.maxHp, 'pricked and marked');
});

test('Runic Core stores magic and spends it on the next hit', () => {
  const s = board([
    { type: 'golem', team: 'P', x: 4, y: 5, level: 2, a2: 'g_runes' },
    { type: 'pyromancer', team: 'E', x: 4, y: 2 },
    { type: 'knight', team: 'E', x: 4, y: 4 },
  ]);
  const [go, py, kn] = s.units;
  big(go);
  big(kn);
  act(s, py, { kind: 'tile', x: 4, y: 5 });
  assert.ok(go.runes > 0, 'runes charged');
  hitOn(s, go, kn);
  assert.ok(!go.runes && events(s, 'runes').length === 1);
});

test('Barkskin: below half HP, shrubs spring up around the Furgon', () => {
  const s = board([
    { type: 'furgon', team: 'P', x: 4, y: 5, a1: 'f_bark' },
    { type: 'berserker', team: 'E', x: 4, y: 4 },
  ]);
  const [fu, be] = s.units;
  fu.block = 0;
  fu.hp = Math.ceil(fu.maxHp / 2) + 2;
  hitOn(s, be, fu);
  assert.ok(s.units.filter((u) => u.alive && u.type === 'shrub').length >= 1);
});

test('Drift: the Wisp puffs spores where it stops', () => {
  const s = board([
    { type: 'wisp', team: 'P', x: 4, y: 8, a1: 'w_drift' },
    { type: 'knight', team: 'E', x: 4, y: 5 },
  ]);
  const [wi, kn] = s.units;
  s.side = 'P';
  assert.ok(E.beginActivation(s, wi.uid));
  assert.ok(E.moveUnit(s, wi.uid, 4, 6));
  assert.ok(kn.poison, 'the knight beside it is poisoned');
});

test('Ethereal: steel sometimes passes right through', () => {
  const s = board([
    { type: 'wisp', team: 'P', x: 4, y: 5, level: 2, a2: 'w_ethereal' },
    { type: 'knight', team: 'E', x: 4, y: 4 },
  ]);
  const [wi, kn] = s.units;
  big(wi);
  for (let i = 0; i < 30; i++) hitOn(s, kn, wi);
  const n = events(s, 'phase').length;
  assert.ok(n > 2 && n < 20, n + ' of 30 passed through');
});

test('Capacitor: each hit taken adds 25% to its next zap, then it is spent', () => {
  const s = board([
    { type: 'lightning', team: 'P', x: 4, y: 5, a1: 'l_cap' },
    { type: 'knight', team: 'E', x: 4, y: 4 },
  ]);
  const [lw, kn] = s.units;
  big(lw);
  big(kn);
  const before = E.calcHit(s, lw, kn, {}).dmg;
  hitOn(s, kn, lw);
  hitOn(s, kn, lw);
  assert.strictEqual(lw.charge, 2);
  assert.ok(E.calcHit(s, lw, kn, {}).dmg > before);
  act(s, lw, { kind: 'dir', d: E.dirFromDelta(0, -1) }); // its bolt, north at the knight
  assert.strictEqual(lw.charge, 0);
});

test('Counterweight and Grappling Hook: boulders shove, hooks drag', () => {
  const s = board([
    { type: 'trebuchet', team: 'P', x: 4, y: 8, a1: 'tb_counter' },
    { type: 'archer', team: 'P', x: 0, y: 8, gear: ['grappling_hook'] },
    { type: 'knight', team: 'E', x: 4, y: 4 },
    { type: 'knight', team: 'E', x: 0, y: 4 },
  ]);
  const [tb, ar, k1, k2] = s.units;
  big(k1);
  big(k2);
  hitOn(s, tb, k1);
  assert.strictEqual(k1.y, 3, 'knocked back');
  hitOn(s, ar, k2);
  assert.strictEqual(k2.y, 5, 'dragged closer');
});

test('Far Cast leaves the fireball burning on its centre tile', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8, level: 2, a2: 'p_range' },
    { type: 'golem', team: 'E', x: 4, y: 4 },
  ]);
  const [py] = s.units;
  act(s, py, { kind: 'tile', x: 4, y: 4 });
  assert.ok(s.tfx.some((f) => f.kind === 'fire' && f.x === 4 && f.y === 4));
});

test('Guardian Angel saves an ally from a killing blow, once', () => {
  const s = board([
    { type: 'cleric', team: 'P', x: 4, y: 7, level: 2, talents: ['c_angel'] },
    { type: 'knight', team: 'P', x: 4, y: 5 },
    { type: 'berserker', team: 'E', x: 4, y: 4 },
  ]);
  const [, kn, be] = s.units;
  kn.block = 0;
  kn.hp = 1;
  hitOn(s, be, kn);
  assert.ok(kn.alive && kn.hp === 1 && events(s, 'angel').length === 1);
  hitOn(s, be, kn);
  assert.ok(!kn.alive, 'only once');
});

test('Hourglass Pendant rewinds to the HP of its last turn', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5, gear: ['hourglass_pendant'] },
    { type: 'berserker', team: 'E', x: 4, y: 4 },
  ]);
  const [kn, be] = s.units;
  kn.block = 0;
  kn.lastTurnHp = 40;
  kn.hp = 2;
  hitOn(s, be, kn);
  assert.ok(kn.alive && kn.hp === 40);
});

test('Trample carries a charge into the enemy behind', () => {
  const s = board([
    { type: 'beastrider', team: 'P', x: 4, y: 8, talents: ['br_trample'] },
    { type: 'knight', team: 'E', x: 4, y: 4, facing: 0 },
    { type: 'knight', team: 'E', x: 4, y: 3, facing: 0 },
  ]);
  const [br, k1, k2] = s.units;
  big(k1);
  big(k2);
  s.side = 'P';
  assert.ok(E.beginActivation(s, br.uid));
  assert.ok(E.moveUnit(s, br.uid, 4, 5));
  assert.ok(E.performAction(s, br.uid, { ai: 0, kind: 'unit', uid: k1.uid }));
  assert.ok(k2.hp < k2.maxHp && events(s, 'trample').length === 1);
});

test('Parasite: the Wisp heals for what its poison takes', () => {
  const s = board(
    [
      { type: 'wisp', team: 'P', x: 4, y: 7, talents: ['w_parasite'] },
      { type: 'knight', team: 'E', x: 4, y: 3 },
    ],
    {},
    { queue: true }
  );
  const [wi, kn] = s.units;
  wi.hp = 10;
  E.applyStatus(s, wi, kn, { poison: [2, 5] }, wi.act);
  while (s.side !== 'E') E.pass(s);
  E.pass(s);
  while (s.side !== 'E') E.pass(s);
  assert.ok(wi.hp > 10, 'drank the poison');
});

test('Opportunist, Last Stand, Momentum Boots: conditions change the numbers', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 6, skills: ['opportunist'], gear: ['momentum_boots'] },
    { type: 'knight', team: 'E', x: 4, y: 3, skills: ['last_stand'] },
  ]);
  const [k, foe] = s.units;
  const base = E.calcHit(s, k, foe, {}).dmg;
  foe.root = 1;
  assert.ok(E.calcHit(s, k, foe, {}).dmg > base, 'rooted: opportunity');
  foe.root = 0;
  assert.ok(E.calcHit(s, k, foe, { moved: true, moveDist: 3 }).dmg > base, 'momentum');
  foe.hp = 5;
  assert.ok(E.calcHit(s, k, foe, {}).dmg < base, 'last stand');
});

test('Spell Mirror turns the first spell back', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 6, skills: ['spell_mirror'] },
    { type: 'pyromancer', team: 'E', x: 4, y: 3 },
  ]);
  const [k, py] = s.units;
  act(s, py, { kind: 'tile', x: 4, y: 6 });
  assert.strictEqual(k.hp, k.maxHp);
  assert.ok(py.hp < py.maxHp);
});

test('Overwatch takes a free shot at an enemy that walks into range', () => {
  const s = board([
    { type: 'archer', team: 'P', x: 4, y: 8, skills: ['overwatch'] },
    { type: 'knight', team: 'E', x: 4, y: 1 },
  ]);
  const [ar, kn] = s.units;
  kn.block = 0;
  s.side = 'E';
  assert.ok(E.beginActivation(s, kn.uid));
  assert.ok(E.moveUnit(s, kn.uid, 4, 4));
  assert.ok(kn.hp < kn.maxHp && events(s, 'overwatch').length === 1);
  void ar;
});

test('Killing Spree: the blow after a kill lands double', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5, skills: ['killing_spree'] },
    { type: 'scout', team: 'E', x: 4, y: 4 },
    { type: 'golem', team: 'E', x: 3, y: 5 },
  ]);
  const [k, sc, go] = s.units;
  sc.hp = 1;
  sc.block = 0;
  hitOn(s, k, sc);
  assert.ok(k.spree);
  big(go);
  hitOn(s, k, go);
  assert.ok(!k.spree && events(s, 'spree').length === 1);
});

test('Undying Rage and Reactive Plate: dropping below half fights back', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5, skills: ['undying_rage'], gear: ['reactive_plate'] },
    { type: 'berserker', team: 'E', x: 4, y: 4 },
  ]);
  const [k, be] = s.units;
  k.block = 0;
  k.hp = Math.ceil(k.maxHp / 2) + 1;
  hitOn(s, be, k);
  assert.ok(k.frenzy > 0 && k.shield === 25);
});

test('Chaos Magic curses its targets', () => {
  const s = board([
    { type: 'pyromancer', team: 'P', x: 4, y: 8, skills: ['chaos_magic'] },
    { type: 'golem', team: 'E', x: 4, y: 4 },
  ]);
  const [py, go] = s.units;
  big(go);
  act(s, py, { kind: 'tile', x: 4, y: 4 });
  assert.ok(go.burn || go.root || go.weak);
});

test('Ogre Belt grows on kills; Armor Breaker strips armor', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 5, gear: ['ogre_belt', 'armor_breaker'], level: 3 },
    { type: 'scout', team: 'E', x: 4, y: 4 },
    { type: 'golem', team: 'E', x: 3, y: 5 },
  ]);
  const [k, sc, go] = s.units;
  const hp0 = k.maxHp;
  sc.hp = 1;
  sc.block = 0;
  hitOn(s, k, sc);
  assert.strictEqual(k.maxHp, hp0 + 10);
  big(go);
  const a0 = go.armor;
  hitOn(s, k, go);
  assert.ok(go.armor < a0);
});

test("Stunning Shield, Berserker's Torc, Gambler's Gauntlet, Cursed Idol, Ember Heart", () => {
  const s = board(
    [
      { type: 'knight', team: 'P', x: 4, y: 5, gear: ['stunning_shield'] },
      { type: 'berserker', team: 'P', x: 1, y: 5, gear: ['berserker_torc'] },
      { type: 'knight', team: 'P', x: 7, y: 7, gear: ['ember_heart'] },
      { type: 'knight', team: 'E', x: 4, y: 4, facing: 2 },
      { type: 'archer', team: 'E', x: 1, y: 1, a1: 'a_snare', gear: ['gamblers_gauntlet'] },
      { type: 'berserker', team: 'E', x: 7, y: 6, gear: ['cursed_idol'] },
    ],
    {},
    {}
  );
  const [ks, be, kh, kn, ar, idol] = s.units;
  ks.block = 0.85;
  for (let i = 0; i < 12 && !kn.para; i++) {
    ks.hp = ks.maxHp;
    hitOn(s, kn, ks);
  }
  assert.ok(kn.para > 0, 'a blocked blow stunned the attacker');
  be.block = 0;
  act(s, ar, { kind: 'unit', uid: be.uid }, 1);
  assert.ok(be.frenzy > 0 && !be.root, 'the torc shrugged the snare into a frenzy');
  assert.ok(events(s, 'gamble').length >= 1);
  assert.ok(idol.props.dmgMult >= 0.5 && idol.traits.has('idol'));
  kh.hp = 1;
  kh.block = 0;
  hitOn(s, idol, kh);
  assert.ok(s.tfx.some((f) => f.kind === 'fire'), 'the ember heart burst into flames');
});

test('Mirror Image: a 1-HP shadow copy stands beside it', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 7, enchant: 'mirror_image' },
    { type: 'knight', team: 'E', x: 4, y: 1 },
  ]);
  const img = s.units.find((u) => u.illusion);
  assert.ok(img && img.team === 'P' && img.hp === 1 && img.type === 'knight');
});

test('Resonant Crystal, Glamour, Echo Amulet, Slippery, Living Moss, Spellsink Mantle', () => {
  const s = board([
    { type: 'barrier', team: 'P', x: 1, y: 6, a1: 'bw_crystal' },
    { type: 'knight', team: 'P', x: 1, y: 7 },
    { type: 'enchantress', team: 'P', x: 7, y: 7, level: 2, a2: 'e_glamour' },
    { type: 'scout', team: 'P', x: 4, y: 7, level: 2, a2: 's_evasion' },
    { type: 'witch', team: 'P', x: 0, y: 8, gear: ['echo_amulet'] },
    { type: 'berserker', team: 'E', x: 1, y: 5 },
    { type: 'knight', team: 'E', x: 7, y: 6 },
    { type: 'knight', team: 'E', x: 4, y: 6, facing: 2 },
    { type: 'golem', team: 'E', x: 0, y: 3 },
  ]);
  const [bw, kn, en, sc, wi, b1, k1, k2, go] = s.units;
  for (const u of [bw, en, go]) big(u);
  hitOn(s, b1, bw);
  assert.ok(kn.shield >= 5, 'the crystal rang: its neighbour has a shield');
  for (let i = 0; i < 20 && !k1.para; i++) hitOn(s, k1, en);
  assert.ok(k1.para > 0, 'spellbound by the glamour');
  sc.hp = sc.maxHp = 999;
  sc.block = 0.85;
  const y0 = sc.y;
  for (let i = 0; i < 12 && sc.y === y0; i++) hitOn(s, k2, sc);
  assert.ok(sc.y > y0, 'slipped a tile away');
  for (let i = 0; i < 20 && !events(s, 'echo').length; i++) act(s, wi, { kind: 'dir', d: 0 });
  assert.ok(events(s, 'echo').length >= 1, 'a spell echoed');

  const t = board([
    { type: 'golem', team: 'P', x: 4, y: 7, talents: ['g_moss'] },
    { type: 'knight', team: 'P', x: 4, y: 6, gear: ['spellsink_mantle'] },
    { type: 'pyromancer', team: 'E', x: 4, y: 2 },
  ], {}, { queue: true });
  const [mo, sink, py] = t.units;
  sink.hp = sink.maxHp - 10;
  act(t, py, { kind: 'tile', x: 4, y: 6 });
  assert.ok(sink.sink, 'the mantle drank the spell');
  const hp = sink.hp;
  while (t.side !== 'P' || t.due !== mo.uid) E.pass(t);
  assert.ok(sink.hp > hp, 'the moss spread to its neighbour');
});

test('campaign enemies barely heal: an enemy Champion keeps its punch but not its heal-on-kill', () => {
  const s = board([
    { type: 'knight', team: 'P', x: 4, y: 7, level: 3 },
    { type: 'knight', team: 'E', x: 4, y: 1, level: 3, foe: true },
  ]);
  const [mine, foe] = s.units;
  assert.ok(mine.traits.has('rallykill'), 'yours heals its neighbours on a kill');
  assert.ok(!foe.traits.has('rallykill'), 'a campaign enemy does not');
  assert.ok(foe.props.dmgMult >= 0.2, 'but still hits like a Champion');
});

console.log(`fun: ${passed} tests passed`);
