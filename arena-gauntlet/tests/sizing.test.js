// How hard the enemy is: army budgets by tier, enemy relics by faction, who resists what,
// what levels cost and give, the set army of the final challenge, and the goals a win is
// judged by. (How these numbers were arrived at: tests/balance.js, the balance lab.)
// Run: node tests/sizing.test.js
const assert = require('assert');
const store = {};
globalThis.localStorage = { getItem: (k) => store[k] || null, setItem: (k, v) => (store[k] = v), removeItem: (k) => delete store[k] };
const AG = require('./load')();
const R = AG.Run;
const E = AG.Engine;
const D = AG.Data;

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

const fighters = (enc) => enc.units.filter((u) => !D.UNITS[u.type].traits.includes('object') && !D.UNITS[u.type].traits.includes('structure'));
const runAt = (seed, act, xp) => {
  const run = R.newRun({ seed, warband: D.WARBANDS[seed % D.WARBANDS.length].id });
  run.act = act;
  run.xp = xp != null ? xp : [0, 30, 150, 300][act];
  run.boss = D.ACTS[act].bosses[seed % D.ACTS[act].bosses.length];
  return run;
};
const card = (run, tier, id) => R.genEncounter(run, { id: id || 'n', row: 2, kind: tier === 'elite' ? 'elite' : 'battle', tier, mult: R.TIERS[tier].mult }, null, []);

test('a level costs a flat price for ordinary units, a share of its own cost for a dear one', () => {
  assert.deepStrictEqual([D.levelCost('scout', 2), D.levelCost('scout', 3)], [2, 5]);
  assert.deepStrictEqual([D.levelCost('knight', 2), D.levelCost('knight', 3)], [2, 5]);
  assert.deepStrictEqual([D.levelCost('witch', 2), D.levelCost('witch', 3)], [2, 6]);
  assert.deepStrictEqual([D.levelCost('frostgiant', 2), D.levelCost('frostgiant', 3)], [4, 11]);
  assert.deepStrictEqual([D.levelCost('dragon', 2), D.levelCost('dragon', 3)], [5, 12]);
  assert.strictEqual(D.levelCost('knight', 1), 0);
  // The War Room charges it, and so does an enemy army's budget.
  const run = runAt(3, 2);
  const dr = R.addRecruit(run, 'dragon');
  dr.load.lv = 1;
  const base = R.unitCost(run, dr);
  dr.load.lv = 3;
  R.normalizeLoad(run, dr);
  assert.ok(R.unitCost(run, dr) - base >= 12, `a Level 3 Dragon costs at least 12 more (${R.unitCost(run, dr) - base})`);
  assert.strictEqual(R.specCost({ type: 'dragon', level: 3 }) - R.specCost({ type: 'dragon', level: 1 }), 12);
});

test('a level is worth more than it was: +30% and +60% HP, +20% and +40% damage', () => {
  assert.deepStrictEqual(D.LEVEL_HP.slice(1), [1, 1.3, 1.6]);
  assert.deepStrictEqual(D.LEVEL_POW.slice(1), [1, 1.2, 1.4]);
  const k = (lv) => E.buildUnit({ type: 'knight', level: lv }, new Set());
  assert.deepStrictEqual([k(1).maxHp, k(2).maxHp, k(3).maxHp], [52, 68, 83]);
  assert.deepStrictEqual([k(1).pow, k(2).pow, k(3).pow], [18, 22, 25]);
});

test('enemy armies carry relics of their faction: none on an Easy card, more by act and on harder cards', () => {
  const healing = ['vampire_fang', 'bloodstone', 'sacred_chalice', 'echo_drum', 'phoenix_feather', 'blood_moon', 'healing_salve', 'necro_bell'];
  for (const [id, f] of Object.entries(D.FACTIONS)) {
    assert.ok(f.relics.length >= 4, id);
    for (const r of f.relics) {
      assert.ok(D.RELICS[r], `${id}: ${r} is a relic`);
      assert.ok(D.FOE_RELIC[r], `${r} is explained from your side`);
      assert.ok(!healing.includes(r), `${r}: enemies never mend`);
      assert.ok(!R.HALL_INERT.has(r), `${r} does something in a battle`);
      // (A price in Supply means nothing to them: their words for it leave it out.)
      assert.ok(!/Supply/.test(D.FOE_RELIC[r]), `${r}: nothing about Supply`);
    }
  }
  // Every army has a faction.
  for (const act of [1, 2, 3]) for (const g of ['normal', 'elite', 'boss']) for (const t of Object.values(D.ENCOUNTERS[act][g])) assert.ok(D.FACTIONS[t.faction], t.name);
  assert.ok(D.FACTIONS[D.ENCOUNTERS.mega.faction]);
  for (const act of [1, 2, 3]) {
    for (let seed = 1; seed <= 6; seed++) {
      const run = runAt(seed, act);
      for (const tier of ['easy', 'medium', 'elite']) {
        const enc = card(run, tier, 'r' + seed);
        const want = R.BAL.relics[tier][act];
        assert.strictEqual(enc.relics.length, want, `act ${act} ${tier}: ${want} relics`);
        assert.strictEqual(new Set(enc.relics).size, enc.relics.length, 'all different');
        const tpl = D.ENCOUNTERS[act][tier === 'elite' ? 'elite' : 'normal'].find((t) => t.name === enc.name);
        for (const r of enc.relics) assert.ok(D.FACTIONS[tpl.faction].relics.includes(r), `${enc.name}: ${r} is its faction's`);
        // The same card, dealt again, carries the same relics.
        assert.deepStrictEqual(card(run, tier, 'r' + seed).relics, enc.relics);
      }
      const boss = R.genEncounter(run, { id: 'b', row: 6, kind: 'boss', tier: 'boss' }, null, []);
      assert.strictEqual(boss.relics.length, R.BAL.relics.boss[act]);
    }
  }
  assert.deepStrictEqual(R.BAL.relics.easy, [0, 0, 0, 0]);
  assert.ok(R.BAL.relics.medium[3] > R.BAL.relics.medium[1] && R.BAL.relics.elite[1] > R.BAL.relics.medium[1]);
});

test('an enemy relic takes the field with its army and works for it', () => {
  const run = runAt(2, 2);
  R.chooseChallenge(run, 1);
  run.pending.enc.relics = ['titan_gauntlet'];
  const cfg = R.battleConfig(run, R.autoDeploy(run, 0));
  assert.deepStrictEqual(cfg.relics.E, ['titan_gauntlet']);
  const mk = (relics) =>
    E.createBattle({ w: 9, h: 9, terrain: new Array(81).fill(0), seed: 3, relics: { P: [], E: relics }, units: [{ type: 'golem', team: 'P', x: 4, y: 5 }, { type: 'berserker', team: 'E', x: 4, y: 4 }] });
  const a = mk([]);
  const b = mk(['titan_gauntlet']);
  const hit = (s) => E.calcHit(s, s.units[1], s.units[0], {}).dmg;
  assert.ok(hit(b) > hit(a) && Math.abs(hit(b) / hit(a) - 1.25) < 0.1, `25% more damage for them (${hit(a)} -> ${hit(b)})`);
});

test('who resists what: steel for greenskins, magic for plate and the dead; and what they hit with', () => {
  const lean = (act, name, tier) => {
    const out = { phys: 0, magic: 0, mixed: 0 };
    for (let seed = 1; seed <= 30; seed++) {
      const run = runAt(seed, act);
      const enc = card(run, tier || 'medium', 'w' + seed);
      if (enc.name === name) out[R.damageProfile(enc).lean]++;
    }
    return out;
  };
  const orcs = lean(1, 'Orc Warband');
  assert.ok(orcs.phys > 0 && orcs.magic === 0, `greenskins: steel (${JSON.stringify(orcs)})`);
  const mercs = lean(1, 'Mercenary Company');
  assert.ok(mercs.magic > 0 && mercs.phys === 0, `plate: magic (${JSON.stringify(mercs)})`);
  const dead = lean(2, 'The Restless Dead');
  assert.ok(dead.magic > 0 && dead.phys === 0, `the dead: magic (${JSON.stringify(dead)})`);
  // Blocks count: a Knight stops most blows from the front, so steel does poorly on plate.
  const army = (types) => ({ units: types.map((type) => ({ type, level: 1 })), waves: [] });
  const plate = R.damageProfile(army(['knight', 'knight', 'knight']));
  assert.ok(plate.phys < 0.45 && plate.magic === 1 && plate.lean === 'magic');
  const paint = R.damageProfile(army(['orc', 'orc', 'goblin_archer']));
  assert.ok(paint.magic < 0.7 && paint.phys > 0.8 && paint.lean === 'phys');
  // What they hit with, and who stands up to it.
  const coven = army(['witch', 'witch', 'pyromancer', 'knight']);
  const horde = army(['orc', 'orc', 'wolf', 'goblin_archer']);
  assert.strictEqual(R.threatProfile(coven).lean, 'magic');
  assert.strictEqual(R.threatProfile(horde).lean, 'phys');
  assert.ok(R.counterScore('knight', horde) > R.counterScore('mageknight', horde), 'a Knight against steel');
  assert.ok(R.counterScore('mageknight', coven) > R.counterScore('knight', coven), 'a Mage Knight against spells');
  // The scout report says both, first thing.
  const run = runAt(4, 1);
  const tips = R.scoutTips(card(run, 'medium'));
  assert.ok(/Steel lands|Spells land/.test(tips[0]) && /their damage|their damage is|damage is steel|steel and spells/i.test(tips[1]), tips.slice(0, 2).join(' | '));
});

test('the tiers: an Easy card is under half a medium army; an elite one fields Shacklers and more relics', () => {
  assert.ok(R.TIERS.easy.mult < 0.5 && R.TIERS.medium.mult === 1 && R.TIERS.elite.mult > 1);
  for (const act of [1, 2, 3]) {
    let easy = 0;
    let med = 0;
    for (let seed = 1; seed <= 12; seed++) {
      const run = runAt(seed, act);
      const e = card(run, 'easy', 't' + seed);
      const m = card(run, 'medium', 't' + seed);
      const x = card(run, 'elite', 't' + seed);
      assert.strictEqual(e.name, m.name, 'the same army, sized for the card');
      assert.ok(e.budget < m.budget, `act ${act}: easy ${e.budget} under medium ${m.budget}`);
      assert.ok(!e.units.some((u) => u.type === 'shackler'), 'no Shackler on an Easy card');
      // An elite is its own kind of army (its Supply says little: what makes it hard is its
      // Shacklers, its relics and its picked troops).
      assert.ok(x.units.some((u) => u.type === 'shackler'));
      assert.ok(x.relics.length > m.relics.length || act === 3, 'more relics than a medium army');
      assert.ok(fighters(e).length >= 2 && fighters(x).filter((u) => u.type !== 'shackler').length >= 2);
      easy += R.encSupply(e).army;
      med += R.encSupply(m).army;
    }
    assert.ok(easy < 0.75 * med, `act ${act}: easy armies field well under a medium's Supply (${easy} vs ${med})`);
  }
  // A medium army outweighs yours: your Cleric, relics and healing make up the difference.
  const run = runAt(5, 2);
  const m = card(run, 'medium');
  assert.ok(m.budget > 0.7 * R.supplyFor(run), `${m.budget} against your ${R.supplyFor(run)}`);
});

test('the final challenge is a set army: the Wyrm, the Death Knight and the Lich, two Shacklers and two relics', () => {
  for (const xp of [150, 300, 420]) {
    const run = runAt(7, 3, xp);
    const enc = R.genEncounter(run, { id: 'mega', row: 7, kind: 'boss', tier: 'mega', mega: true }, null, []);
    const f = fighters(enc);
    assert.deepStrictEqual(f.map((u) => u.type).sort(), ['death_knight', 'lich', 'shackler', 'shackler', 'void_wyrm'], `whatever your Supply (${R.supplyFor(run)})`);
    assert.strictEqual(R.BAL.megaLevel, 2, 'its three bosses at Level 2');
    for (const u of f) if (D.UNITS[u.type].boss) assert.strictEqual(u.level || 1, R.BAL.megaLevel);
    assert.strictEqual(enc.relics.length, 2);
    assert.strictEqual(enc.units.filter((u) => u.type === 'barrel').length, 6, 'and its powder kegs');
    assert.ok(!enc.bonus.length && !enc.loot.length);
  }
});

test('outlasting them takes about a battle\'s length, and their commander is a veteran', () => {
  assert.deepStrictEqual(R.BAL.surviveTurns.slice(1), [19, 25, 25]);
  let survive = 0;
  let commander = 0;
  for (let seed = 1; seed <= 60 && (survive < 3 || commander < 3); seed++) {
    for (const act of [1, 2, 3]) {
      const run = runAt(seed, act);
      const enc = card(run, 'medium', 's' + seed);
      if (enc.primary === 'survive') {
        survive++;
        assert.strictEqual(enc.surviveTurns, R.BAL.surviveTurns[act]);
        assert.strictEqual(enc.waves.length, act === 1 ? 3 : 4, 'a wave more than there was');
        assert.ok(Math.max(...enc.waves.map((w) => w.turn)) < enc.surviveTurns);
      }
      if (enc.primary === 'commander') {
        commander++;
        const vip = enc.units.find((u) => u.vip);
        assert.ok(vip && vip.type !== 'shackler');
        assert.strictEqual(vip.baseHp, Math.round(D.UNITS[vip.type].hp * R.BAL.commanderHp));
        assert.ok(E.buildUnit(vip, new Set()).maxHp > E.buildUnit({ type: vip.type, level: vip.level }, new Set()).maxHp);
      }
    }
  }
  assert.ok(survive >= 3 && commander >= 3);
});

test('few losses: a win with one unit down meets the goal, with two it does not', () => {
  assert.strictEqual(R.FLAWLESS_MAX, 1);
  const run = runAt(1, 1);
  R.chooseChallenge(run, 0);
  run.pending.enc.bonus = [{ type: 'flawless' }];
  const fake = (lost) => ({ won: { turn: 9, lost }, turn: 12, units: [], loot: [], stats: {} });
  assert.deepStrictEqual(R.goalResults(run, fake(0), []).map((g) => g.done), [true]);
  assert.deepStrictEqual(R.goalResults(run, fake(1), []).map((g) => g.done), [true]);
  assert.deepStrictEqual(R.goalResults(run, fake(2), []).map((g) => g.done), [false]);
  assert.ok(/no more than one/.test(R.objectiveInfo(run, run.pending.enc).bonus[0].text));
  // Mid-battle, units down so far.
  const s = { units: [{ team: 'P', alive: false }, { team: 'P', alive: false, nonCombat: true }, { team: 'P', alive: true }, { team: 'E', alive: false }] };
  assert.strictEqual(R.fallen(s), 1);
});

test('Auto, tapped again, offers a different plan: fewer, better units, then the usual army shuffled', () => {
  const run = runAt(9, 2, 200);
  for (const t of ['archer', 'scout', 'berserker', 'pyromancer', 'witch']) R.addRecruit(run, t);
  R.chooseChallenge(run, 1);
  const size = (v) => R.autoDeploy(run, v).filter((d) => !R.unitById(run, d.rid).core).length;
  const usual = size(0);
  assert.ok(usual >= 5, `the usual army: ${usual} units and the Cleric`);
  assert.deepStrictEqual([size(1), size(2), size(3)], [usual - 1, usual - 2, usual - 3]);
  assert.deepStrictEqual([1, 2, 3].map((v) => R.autoFocus(run, v)), [usual - 1, usual - 2, usual - 3]);
  assert.strictEqual(R.autoFocus(run, 0), 0);
  assert.strictEqual(R.autoFocus(run, 4), 0);
  assert.strictEqual(size(4), usual, 'then the usual size again');
  // The Supply saved goes into the units that are left.
  const lv = (v) => {
    const dep = R.autoDeploy(run, v);
    return dep.reduce((t, d) => t + R.unitById(run, d.rid).load.lv, 0) / dep.length;
  };
  assert.ok(lv(3) > lv(0), 'higher levels on the smaller army');
  for (const v of [0, 1, 2, 3, 4]) assert.ok(R.supplyUsed(run, R.autoDeploy(run, v)) <= R.supplyFor(run));
  // A starting army is too small to shrink by three: never fewer than two units and the Cleric.
  const fresh = runAt(9, 1, 0);
  R.chooseChallenge(fresh, 1);
  for (const v of [1, 2, 3]) assert.ok(R.autoDeploy(fresh, v).filter((d) => !R.unitById(fresh, d.rid).core).length >= 2);
});

test('enemy buildings send half as many reinforcements on an Easy card', () => {
  assert.deepStrictEqual(R.BAL.spawns, { easy: 2, other: 4 });
  let seen = 0;
  for (let seed = 1; seed <= 80 && seen < 4; seed++) {
    for (const act of [2, 3]) {
      const run = runAt(seed, act);
      const e = card(run, 'easy', 'w' + seed);
      const m = card(run, 'medium', 'w' + seed);
      if (e.primary !== 'raze' && e.primary !== 'gate') continue;
      seen++;
      const perHouse = (enc) => {
        const n = {};
        for (const w of enc.waves) n[w.from] = (n[w.from] || 0) + w.units.length;
        return Object.values(n);
      };
      assert.ok(perHouse(e).length >= 1 && perHouse(e).every((n) => n === 2), `easy: two from each building (${perHouse(e)})`);
      assert.ok(perHouse(m).every((n) => n === 4), `medium: four from each (${perHouse(m)})`);
      assert.ok(R.encSupply(e).waves < R.encSupply(m).waves);
    }
  }
  assert.ok(seen >= 4);
});

test('a castle\'s gold is the gate\'s to give: none in the guardhouses behind the wall', () => {
  let seen = 0;
  for (let seed = 1; seed <= 80 && seen < 3; seed++) {
    for (const act of [1, 3]) {
      const run = runAt(seed, act);
      const enc = card(run, 'medium', 'g' + seed);
      if (enc.primary !== 'gate') continue;
      run.offer = null;
      run.pending = { type: 'battle', nodeId: 'n', node: { id: 'n' }, tier: 'medium', enc, attempt: 0 };
      seen++;
      const houses = enc.units.filter((u) => u.type === 'guardhouse');
      const gate = enc.units.find((u) => u.type === 'gate');
      assert.ok(houses.length >= 1 && houses.every((u) => u.salvage === 0));
      assert.strictEqual(gate.salvage, D.UNITS.gate.salvage + houses.length * D.UNITS.guardhouse.salvage);
      const s = E.createBattle(R.battleConfig(run, R.autoDeploy(run, 0)));
      const inBattle = (type) => s.units.filter((u) => u.type === type).map((u) => u.salvage);
      assert.deepStrictEqual(inBattle('gate'), [gate.salvage]);
      assert.ok(inBattle('guardhouse').every((n) => n === 0));
      assert.ok(inBattle('wall').every((n) => n === 0) && inBattle('tower').every((n) => n === 0));
    }
  }
  assert.ok(seen >= 3);
});

test('an elite commander brings no bigger army: a monster with half again its HP is no shortcut', () => {
  assert.ok(R.BAL.share.commander.elite < R.BAL.share.commander.normal);
  assert.ok(R.BAL.share.commander.elite < 1 && R.BAL.share.commander.normal > 1);
});

test('a boss wears down: nothing for two defeats, then 6% of its fighters\' HP a defeat, to 30%', () => {
  const run = runAt(4, 2);
  const boss = { enc: { kind: 'boss', units: [] }, tier: 'boss' };
  const at = (n, o) => R.wornDown(run, Object.assign({}, o || boss, { attempts: n }));
  assert.deepStrictEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 20].map((n) => at(n)), [0, 0, 0, 0.06, 0.12, 0.18, 0.24, 0.3, 0.3, 0.3]);
  // Only where there is no easier card: never a round's cards, never the final challenge.
  assert.strictEqual(at(9, { enc: { kind: 'battle' }, tier: 'medium' }), 0);
  assert.strictEqual(at(9, { enc: { kind: 'elite' }, tier: 'elite' }), 0);
  assert.strictEqual(at(9, { enc: { kind: 'boss' }, tier: 'mega' }), 0);
  // A battle an event started is retried as it is, so it wears down too.
  assert.strictEqual(R.wornDown({ pending: { enc: { kind: 'battle' }, fromEvent: true, attempt: 4 } }), 0.12);
  // In the battle: its fighters start hurt, its buildings and wreckage do not.
  const r1 = runAt(6, 1);
  r1.offer = null;
  const enc = R.genEncounter(r1, { id: 'b', row: 7, kind: 'boss', tier: 'boss' }, null, []);
  r1.pending = { type: 'battle', nodeId: 'b', node: { id: 'b' }, tier: 'boss', enc, attempt: 5 };
  const dep = R.autoDeploy(r1, 0);
  const s = E.createBattle(R.battleConfig(r1, dep));
  const foes = s.units.filter((u) => u.team === 'E');
  const fightersIn = foes.filter((u) => !u.structure && !u.traits.has('object'));
  assert.ok(fightersIn.length >= 2);
  for (const u of fightersIn) assert.strictEqual(u.hp, Math.max(1, Math.round(u.maxHp * 0.82)), `${u.type} starts 18% down`);
  const things = foes.filter((u) => u.structure || u.traits.has('object'));
  assert.ok(things.length >= 1 && things.every((u) => u.hp === u.maxHp), 'the wreckage is as it was');
  assert.ok(s.units.filter((u) => u.team === 'P').every((u) => u.hp === u.maxHp), 'your own army is fresh');
  // Fresh again without the defeats.
  r1.pending.attempt = 2;
  assert.ok(E.createBattle(R.battleConfig(r1, dep)).units.every((u) => u.hp === u.maxHp));
});

console.log(`sizing: ${passed} tests passed`);
