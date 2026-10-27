// Sandbox armies: built straight for the Hall of Fame with any units and kit, up to five
// hand-picked relics and a fixed Supply. Legal kits only, never touching the campaign, and
// marked Sandbox in the Hall. Run: node tests/sandbox.test.js
const assert = require('assert');
const m = new Map();
globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
const AG = require('./load')();
const R = AG.Run;
const D = AG.Data;
const E = AG.Engine;

let passed = 0;
async function test(name, fn) {
  try {
    await fn();
    passed++;
  } catch (e) {
    console.error('FAIL', name);
    throw e;
  }
}

(async () => {
  await test('Supply: a fixed base, moved only by relics that add or cost Supply', () => {
    assert.strictEqual(R.sandboxSupply([]), R.SANDBOX_SUPPLY);
    assert.strictEqual(R.sandboxSupply(['war_horn', 'tyrant_heart']), R.SANDBOX_SUPPLY + 4);
    assert.strictEqual(R.sandboxSupply(['worldbreaker']), R.SANDBOX_SUPPLY - 4);
  });

  await test('kits are kept legal: class talents, eligible items, one of each, within slots', () => {
    const d = R.fixSandbox({ relics: ['war_horn', 'nope', 'war_horn', 'lucky_coin', 'guild_seal', 'tyrant_heart', 'blood_pact', 'crown_command'], units: [] });
    assert.deepStrictEqual(d.relics, ['war_horn', 'lucky_coin', 'tyrant_heart', 'blood_pact', 'crown_command'].filter((id, i, all) => i < 5 && R.sandboxTierOk(all.slice(0, i), id)), 'real ones, no repeats, nothing useless in the Hall (the Guild Seal goes)');
    assert.ok(!d.relics.includes('guild_seal'));
    // One boss relic and one legendary at most: the second of each is dropped.
    const t = R.fixSandbox({ relics: ['tyrant_heart', 'crown_command', 'worldbreaker', 'mountain_heart', 'lucky_coin', 'war_horn'] });
    assert.deepStrictEqual(t.relics, ['tyrant_heart', 'worldbreaker', 'lucky_coin', 'war_horn']);
    assert.ok(!R.sandboxTierOk(t.relics, 'sacred_chalice') && !R.sandboxTierOk(t.relics, 'blood_moon') && R.sandboxTierOk(t.relics, 'bloodstone'));
    R.addSandboxUnit(d, 'knight');
    const sp = d.units[0].spec;
    const pyroTalent = Object.keys(D.TALENTS).find((id) => D.TALENTS[id].cls === 'pyromancer');
    const knightTalents = Object.keys(D.TALENTS).filter((id) => D.TALENTS[id].cls === 'knight');
    Object.assign(sp, { level: 1, talents: [pyroTalent, knightTalents[0], knightTalents[0], knightTalents[1]], a1: 'p_ignite', gear: Object.keys(D.GEAR) });
    R.fixSandbox(d);
    assert.deepStrictEqual(sp.talents, [knightTalents[0]], "a Level 1 Knight: one talent slot, its own class's");
    assert.ok(D.UNITS.knight.abilities[1].includes(sp.a1), 'a Knight pick, not a Pyromancer one');
    assert.strictEqual(sp.gear.length, D.GEAR_SLOTS[1]);
    sp.level = 3;
    sp.talents = knightTalents.slice();
    R.fixSandbox(d);
    assert.strictEqual(sp.talents.length, Math.min(knightTalents.length, D.TALENT_SLOTS[3]));
  });

  await test('one copy of each item in the whole army: the first unit keeps it', () => {
    const d = R.fixSandbox({});
    R.addSandboxUnit(d, 'knight');
    R.addSandboxUnit(d, 'berserker');
    const gear = Object.keys(D.GEAR).find((id) => D.eligible('knight', D.GEAR[id]) && D.eligible('berserker', D.GEAR[id]));
    const ench = Object.keys(D.ENCHANTS).find((id) => D.eligible('knight', D.ENCHANTS[id]) && D.eligible('berserker', D.ENCHANTS[id]));
    for (const it of d.units) Object.assign(it.spec, { gear: [gear], enchant: ench });
    R.fixSandbox(d);
    assert.deepStrictEqual(d.units[0].spec.gear, [gear]);
    assert.strictEqual(d.units[0].spec.enchant, ench);
    assert.deepStrictEqual(d.units[1].spec.gear, [], 'no second copy');
    assert.ok(!d.units[1].spec.enchant);
    assert.strictEqual(R.sandboxHolder(d, 'gear', gear), 0);
    assert.strictEqual(R.sandboxHolder(d, 'enchant', ench), 0);
    // Two Knights may still share an ability pick: picks are not items.
    R.addSandboxUnit(d, 'knight');
    assert.strictEqual(d.units[2].spec.a1, d.units[0].spec.a1);
  });

  await test('units stand on their own side, one to a tile; fighters up front, support at the back', () => {
    const d = R.fixSandbox({});
    for (const t of ['knight', 'cleric', 'archer', 'berserker']) R.addSandboxUnit(d, t);
    const at = (t) => d.units.find((it) => it.spec.type === t);
    assert.strictEqual(at('knight').y, 6);
    assert.strictEqual(at('cleric').y, 8);
    assert.ok(d.units.every((it) => it.y >= 6));
    assert.strictEqual(new Set(d.units.map((it) => it.x + ',' + it.y)).size, d.units.length);
    assert.ok(!R.addSandboxUnit(d, 'void_wyrm'), 'no bosses or enemies');
  });

  await test('over Supply or without a fighter it cannot enter the Hall', () => {
    const d = R.fixSandbox({});
    R.addSandboxUnit(d, 'cleric');
    assert.ok(!R.sandboxStatus(d).ok, 'a lone Cleric cannot fight');
    for (let i = 0; i < 6; i++) R.addSandboxUnit(d, 'dragon');
    assert.ok(R.sandboxStatus(d).used > R.sandboxStatus(d).cap);
    assert.ok(!R.sandboxStatus(d).ok);
    assert.strictEqual(R.enterSandbox(d), null);
  });

  await test('a sandbox army enters the Hall marked Sandbox, fights, and leaves the campaign alone', () => {
    const run = R.newRun(5);
    R.save(run);
    const before = localStorage.getItem('arena-gauntlet-run-v2');
    const d = R.fixSandbox({ name: 'Test Lab', relics: ['war_horn', 'lucky_coin'] });
    for (const t of ['knight', 'knight', 'archer', 'cleric', 'pyromancer']) R.addSandboxUnit(d, t);
    assert.ok(R.sandboxStatus(d).ok);
    R.saveSandbox(d);
    assert.strictEqual(R.loadSandbox().units.length, 5, 'the draft keeps');
    const l = R.enterSandbox(d);
    assert.ok(l && l.sandbox && l.name === 'Test Lab' && !l.superWon);
    const h = R.loadHall();
    assert.ok(h.queue.some((x) => x.id === l.id));
    assert.strictEqual(localStorage.getItem('arena-gauntlet-run-v2'), before, 'the campaign is untouched');
    const foe = h.legends[h.legends.length - 1];
    const s = E.createBattle(R.hallBattleConfig(l, foe, 3));
    assert.strictEqual(s.units.filter((u) => u.team === 'P').length, 5);
  });

  await test('shared sandbox armies stay marked Sandbox in a friend\'s Hall', async () => {
    const code = await R.exportArmies('Lab');
    const r = await R.readArmies(code);
    assert.ok(r.armies.some((l) => l.sandbox && l.foreign));
  });

  await test('Auto: legal armies within Supply, every relic working in its army, never an inert one', () => {
    let notes = 0;
    for (let seed = 1; seed <= 60; seed++) {
      const d = R.autoSandbox(seed);
      const st = R.sandboxStatus(d);
      assert.ok(st.ok, `seed ${seed}: ${st.used}/${st.cap}`);
      assert.ok(d.relics.length >= 3 && d.relics.length <= R.SANDBOX_RELICS);
      for (const id of d.relics) {
        assert.ok(!R.HALL_INERT.has(id), `${id} does nothing in the Hall`);
        assert.ok(R.relicFit(d, id).ok, `seed ${seed}: ${id} has what it needs`);
      }
      assert.ok(!(d.relics.includes('lone_wolf') && d.relics.includes('phalanx_standard')));
      assert.ok(d.relics.filter((id) => D.RELICS[id].tier === 'legendary').length <= 1, 'one legendary at most');
      assert.ok(d.relics.filter((id) => D.RELICS[id].tier === 'boss').length <= 1, 'one boss relic at most');
      assert.ok(d.units.some((it) => it.spec.type === 'cleric'));
      assert.deepStrictEqual(JSON.parse(JSON.stringify(R.fixSandbox(JSON.parse(JSON.stringify(d))))), JSON.parse(JSON.stringify(d)), 'already legal');
      notes += d.why.length;
    }
    assert.ok(notes > 30, 'synergy relics come up and say why');
  });

  await test("Auto takes the Plague Doctor's Mask only with a poisoner, and gives one the kit when it can", () => {
    const d = R.fixSandbox({});
    for (const t of ['cleric', 'knight', 'berserker']) R.addSandboxUnit(d, t);
    const fit = R.relicFit(d, 'plague_mask');
    assert.ok(fit.ok && fit.fix, 'nobody poisons yet, but one can be given the kit (Venom Edge)');
    fit.fix.apply();
    R.fixSandbox(d);
    assert.ok(R.relicFit(d, 'plague_mask').ok && !R.relicFit(d, 'plague_mask').fix, 'and now it does');
    const w = R.fixSandbox({});
    R.addSandboxUnit(w, 'wisp');
    assert.strictEqual(R.relicFit(w, 'plague_mask').why, 'your Poison Wisp poisons');
    // Shapes: Lone Wolf needs a mostly ranged army.
    const melee = R.fixSandbox({});
    for (const t of ['knight', 'berserker', 'golem']) R.addSandboxUnit(melee, t);
    assert.ok(!R.relicFit(melee, 'lone_wolf').ok);
    assert.ok(R.relicFit(melee, 'phalanx_standard').ok);
  });

  await test('relics and kit with no use in a Hall battle are never kept, offered or auto-picked', () => {
    const d = R.fixSandbox({ relics: ['guild_seal', 'coin_purse', 'lucky_coin', 'drill_manual'] });
    assert.deepStrictEqual(d.relics, ['lucky_coin']);
    R.addSandboxUnit(d, 'scout');
    R.addSandboxUnit(d, 'knight');
    Object.assign(d.units[0].spec, { level: 3, talents: ['s_cutpurse'], skills: ['demolisher'], gear: ['siege_hammer', 'gilded_gauntlet'], enchant: 'midas' });
    R.fixSandbox(d);
    const sp = d.units[0].spec;
    assert.ok(sp.talents.includes('s_cutpurse'), 'Light Fingers fights now, so it stays');
    assert.ok(!sp.skills.includes('demolisher') && !sp.gear.length && !sp.enchant);
    for (let seed = 1; seed <= 60; seed++) {
      const a = R.autoSandbox(seed);
      for (const it of a.units) {
        for (const k of ['talents', 'skills', 'gear']) assert.ok(!it.spec[k].some((id) => R.kitInert(k, id)), `seed ${seed}: ${k}`);
        assert.ok(!(it.spec.enchant && R.kitInert('enchant', it.spec.enchant)));
      }
    }
  });

  console.log(`sandbox: ${passed} tests passed`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
