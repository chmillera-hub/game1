// Road events: every choice of every event resolves, rewards are things (talents, skills,
// gear, enchantments, relics, recruits, transformations), never a pile of gold, and the
// Cleric that always fights is never touched. Run: node tests/events.test.js
const assert = require('assert');
const AG = require('./load')();
const R = AG.Run;
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

// A run at the given event, with gold to spend and a mixed army.
function atEvent(seed, id, gold) {
  const run = R.newRun({ seed, warband: ['vanguard', 'ember', 'shadow', 'grove', 'grave'][seed % 5] });
  run.gold = gold;
  run.pending = { type: 'event', nodeId: '1:' + seed, eventId: id, ctx: {}, result: null };
  return run;
}

const clone = (run) => JSON.parse(JSON.stringify(run));

test('every choice of every event resolves, pays in things rather than gold, and leaves the Cleric alone', () => {
  let tried = 0;
  for (const ev of R.EVENTS) {
    for (let seed = 1; seed <= 12; seed++) {
      const base = atEvent(seed, ev.id, 200);
      const choices = R.eventChoices(base);
      assert.ok(choices.length >= 2, `${ev.id}: at least two choices`);
      for (const c of choices) {
        if (!c.enabled) continue;
        const run = clone(base);
        const ids = run.roster.map((u) => u.id);
        const target = c.pick ? run.roster.find((u) => R.eventPickOk(run, c.pick, u)) : null;
        if (c.pick) assert.ok(target, `${ev.id}/${c.id}: enabled, so someone can be picked`);
        const core = R.coreUnit(run);
        const coreBefore = JSON.stringify(core);
        const goldBefore = run.gold;
        const out = R.chooseEvent(run, c.id, target ? target.id : null);
        assert.ok(typeof out === 'string' && out.length > 0, `${ev.id}/${c.id} resolves`);
        tried++;
        assert.ok(run.gold <= goldBefore, `${ev.id}/${c.id}: no event pays out gold (${goldBefore} -> ${run.gold})`);
        assert.ok(run.gold >= 0);
        assert.ok(R.coreUnit(run), `${ev.id}/${c.id}: the Cleric stays`);
        // It may be blessed with an enchantment (an upgrade that costs Supply to field), but it
        // stays your Cleric: never transformed, never gone.
        const after = Object.assign({}, R.coreUnit(run), { enchant: null });
        assert.strictEqual(JSON.stringify(after), JSON.stringify(Object.assign(JSON.parse(coreBefore), { enchant: null })), `${ev.id}/${c.id}: still your Cleric`);
        for (const u of run.roster) if (u.enchant) assert.ok(D.eligible(u.type, D.ENCHANTS[u.enchant]), `${ev.id}/${c.id}: ${u.type} can take ${u.enchant}`);
        for (const it of run.items) assert.ok(D.itemDef(it.kind, it.id) || it.kind === 'scroll', `${ev.id}/${c.id}: ${it.kind} ${it.id} exists`);
        if (run.pending.type === 'battle') assert.strictEqual(ev.id, 'trial');
        // No choice does nothing: each one changes the army, the pack, the relics, the
        // Commander's XP or Supply, or starts a battle.
        const sig = (r) => JSON.stringify([r.roster, r.items, r.relics, r.xp, r.supplyBonus]);
        assert.ok(run.pending.type === 'battle' || sig(run) !== sig(base) || run.gold !== base.gold, `${ev.id}/${c.id}: does something`);
        // Units only ever leave by the gambler's wager.
        if (run.roster.length < ids.length) assert.strictEqual(c.id, 'wager');
      }
    }
  }
  assert.ok(tried > 300, 'tried ' + tried);
});

test('a pick that does not fit the choice is refused', () => {
  const run = atEvent(3, 'alchemist', 200);
  const core = R.coreUnit(run);
  assert.strictEqual(R.chooseEvent(run, 'mutagen', core.id), null, 'the Cleric cannot drink the green vial');
  assert.strictEqual(R.chooseEvent(run, 'mutagen', null), null, 'a pick is needed');
  assert.strictEqual(run.pending.result, null);
});

test('the fountain binds an enchantment straight onto the unit picked', () => {
  const run = atEvent(5, 'fountain', 0);
  const u = run.roster.find((x) => R.eventPickOk(run, { filter: 'bare' }, x));
  R.chooseEvent(run, 'bathe', u.id);
  assert.ok(u.enchant && D.eligible(u.type, D.ENCHANTS[u.enchant]));
});

test('the mirror pool copies a unit, enchantment and all', () => {
  const run = atEvent(7, 'mirror', 0);
  const u = run.roster.find((x) => R.eventPickOk(run, { filter: 'mirror' }, x));
  u.enchant = Object.keys(D.ENCHANTS).find((id) => D.eligible(u.type, D.ENCHANTS[id]));
  const n = run.roster.length;
  R.chooseEvent(run, 'reflect', u.id);
  assert.strictEqual(run.roster.length, n + 1);
  const twin = run.roster[run.roster.length - 1];
  assert.strictEqual(twin.type, u.type);
  assert.strictEqual(twin.enchant, u.enchant);
  assert.ok(!twin.core, 'a copy of the Cleric is not free');
});

test('the mentor teaches a stronger talent of the picked unit\'s class', () => {
  const run = atEvent(9, 'mentor', 0);
  const u = run.roster.find((x) => R.eventPickOk(run, { filter: 'trained' }, x));
  const before = run.items.length;
  R.chooseEvent(run, 'train', u.id);
  const t = run.items[before];
  assert.strictEqual(t.kind, 'talent');
  assert.strictEqual(D.TALENTS[t.id].cls, u.type);
  assert.strictEqual(D.TALENTS[t.id].tier, 2);
});

test('the Merchant Caravan lets you pick which common relic to trade, one choice for each', () => {
  const run = atEvent(3, 'caravan', 200);
  const tierOf = (t) => Object.keys(D.RELICS).filter((id) => D.RELICS[id].tier === t);
  run.relics = [...tierOf('common').slice(0, 2), tierOf('uncommon')[0]];
  const commons = run.relics.filter((id) => D.RELICS[id].tier === 'common');
  run.pending.ctx = { v: 2, relic: Object.keys(D.RELICS).find((id) => D.RELICS[id].tier === 'rare' && !run.relics.includes(id)) };
  const swaps = R.eventChoices(run).filter((c) => c.id.startsWith('swap'));
  assert.deepStrictEqual(swaps.map((c) => c.id), commons.map((id) => 'swap:' + id), 'one trade per common relic, named');
  const keep = commons[0];
  const give = commons[commons.length - 1];
  assert.ok(R.chooseEvent(run, 'swap:' + give, null));
  assert.ok(!run.relics.includes(give) && run.relics.includes(keep) && run.relics.includes(run.pending.ctx.relic), 'the one you picked goes, the rest stay');
});

test("a save caught mid-event from before the rewrite gets a fresh deal", () => {
  const run = atEvent(2, 'forge', 100);
  run.pending.ctx = { gear: ['x'] };
  const choices = R.eventChoices(run);
  assert.ok(choices.every((c) => !c.id.includes('forge:x')));
  assert.strictEqual(run.pending.ctx.v, 3);
});

console.log(`events: ${passed} tests passed`);
