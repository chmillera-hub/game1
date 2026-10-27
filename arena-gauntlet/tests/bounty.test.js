// Bounties: an army leaning on one decked-out Level 3 unit gets that unit hunted by the
// next elites, with Spellbinders. Their curse, the Severed status and the unbreakable
// chains. Run: node tests/bounty.test.js
const assert = require('assert');
const m = new Map();
globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
const AG = require('./load')();
const R = AG.Run;
const D = AG.Data;
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

const field = (run, ids) => ids.map((rid, i) => ({ rid, x: i, y: 8 }));

function battle(units) {
  const s = E.createBattle({ w: 9, h: 9, terrain: new Array(81).fill(E.T_GRASS), seed: 3, objective: 'all', loot: [], goals: [], waves: [], relics: { P: [], E: [] }, units });
  s.side = 'P';
  return s;
}

// The Cleric prays (its AI picks the prayer), healing whoever it can.
function pray(s) {
  s.side = 'P';
  s.spent = false;
  s.due = 0;
  for (const u of s.units) u.activated = false;
  const plan = AI.chooseActivation(s, 'P', { stance: 'balanced', temp: 0 });
  if (plan) AI.runPlan(s, plan, { stance: 'balanced', temp: 0 });
}

test('one Level 3 unit holding most of the fielded Supply is a carry; a spread army is not', () => {
  const run = R.newRun({ seed: 11, warband: D.WARBANDS[0].id });
  const cleric = R.coreUnit(run);
  const zerk = R.addRecruit(run, 'berserker');
  zerk.load.lv = 3;
  for (const id of ['vampiric', 'undying_rage']) zerk.load.skills.push(R.addItem(run, 'skill', id).uid);
  const c = R.carryOf(run, field(run, [cleric.id, zerk.id]));
  assert.ok(c && c.rid === zerk.id && c.type === 'berserker', 'the Berserker is the carry');
  // The same Berserker at Level 2: not a carry, however much it costs.
  zerk.load.lv = 2;
  assert.strictEqual(R.carryOf(run, field(run, [cleric.id, zerk.id])), null, 'Level 2 is never hunted');
  zerk.load.lv = 3;
  // Spread the Supply over a wide army and nobody stands out.
  const others = run.roster.filter((u) => !u.core && u !== zerk).map((u) => u.id);
  zerk.load.skills = [];
  for (const r of run.roster) if (!r.core) r.load.lv = 2;
  zerk.load.lv = 3;
  const wide = R.carryOf(run, field(run, [cleric.id, zerk.id, ...others]));
  assert.strictEqual(wide, null, 'a wide army is not hunted');
});

test('after a carry battle, the elite card brings Spellbinders and names the hunted unit', () => {
  const run = R.newRun({ seed: 12, warband: D.WARBANDS[1].id });
  const dragon = R.addRecruit(run, 'dragon');
  run.lastCarry = { rid: dragon.id, name: dragon.name, type: 'dragon' };
  for (const act of [1, 2, 3]) {
    run.act = act;
    const enc = R.genEncounter(run, { id: 'b' + act, row: 2, kind: 'elite', tier: 'elite', mult: 1.85 }, null, []);
    const sb = enc.units.filter((u) => u.type === 'spellbinder');
    const sh = enc.units.filter((u) => u.type === 'shackler');
    assert.strictEqual(sb.length, act === 1 ? 1 : 2, `act ${act}: Spellbinders`);
    assert.strictEqual(sh.length, act === 3 ? 2 : 1, `act ${act}: Shacklers`);
    assert.ok(enc.bounty && enc.bounty.rid === dragon.id && enc.bounty.hunters === sb.length && enc.bounty.shacklers === sh.length, 'the card names the hunted unit');
    assert.ok(!enc.units.some((u) => ['spellbinder', 'shackler'].includes(u.type) && u.vip), 'a hunter is never the commander');
    assert.ok(R.scoutTips(enc)[0].startsWith('Bounty on ' + dragon.name), 'the war room says so first');
    // Medium battles never carry a bounty.
    const med = R.genEncounter(run, { id: 'm' + act, row: 2, kind: 'battle', tier: 'medium', mult: 1 }, null, []);
    assert.ok(!med.bounty && !med.units.some((u) => ['spellbinder', 'shackler'].includes(u.type)), 'no bounty on a medium battle');
  }
  // The carry left the army: no bounty.
  run.roster = run.roster.filter((u) => u !== dragon);
  const enc = R.genEncounter(run, { id: 'x', row: 2, kind: 'elite', tier: 'elite', mult: 1.85 }, null, []);
  assert.ok(!enc.bounty, 'no bounty on a unit you no longer have');
});

test('the hunted unit cannot be healed and takes 25% more damage while a Spellbinder stands', () => {
  const s = battle([
    { type: 'cleric', team: 'P', x: 4, y: 8, a1: 'c_bless' },
    { type: 'knight', team: 'P', x: 4, y: 6, hunted: true },
    { type: 'knight', team: 'E', x: 4, y: 3 },
    { type: 'spellbinder', team: 'E', x: 0, y: 0 },
  ]);
  const [, kn, foe, sb] = s.units;
  assert.ok(E.huntedNow(s, kn));
  const cursed = E.calcHit(s, foe, kn, {}).dmg;
  kn.hp -= 30;
  pray(s);
  assert.strictEqual(kn.hp, kn.maxHp - 30, 'no healing while hunted, even with Blessing');
  sb.alive = false;
  assert.ok(!E.huntedNow(s, kn), 'the curse lifts when the hunters fall');
  const plain = E.calcHit(s, foe, kn, {}).dmg;
  assert.ok(Math.abs(cursed - plain * 1.25) <= 1, `+25% damage (${plain} -> ${cursed})`);
  kn.wait = 0;
  s.units[0].wait = 0;
  pray(s);
  assert.ok(kn.hp > kn.maxHp - 30, 'healed again');
});

test('Severed blocks healing and no cure lifts it; chains hold through Blessing', () => {
  const s = battle([
    { type: 'cleric', team: 'P', x: 4, y: 8, a1: 'c_bless' },
    { type: 'knight', team: 'P', x: 4, y: 6 },
    { type: 'spellbinder', team: 'E', x: 0, y: 0 },
  ]);
  const [cl, kn, sb] = s.units;
  E.applyStatus(s, sb, kn, { sever: 3 }, null);
  E.applyStatus(s, sb, kn, { para: 2, chains: 1 }, null);
  assert.strictEqual(kn.sever, 3);
  assert.ok(kn.para === 2 && kn.chains === 2, 'chained');
  kn.hp -= 20;
  pray(s);
  assert.strictEqual(kn.hp, kn.maxHp - 20, 'severed: no healing');
  assert.ok(kn.sever > 0 && kn.para > 0, 'Blessing lifted neither the sever nor the chains');
  // A plain paralysis still breaks under Blessing.
  const t = battle([
    { type: 'cleric', team: 'P', x: 4, y: 8, a1: 'c_bless' },
    { type: 'knight', team: 'P', x: 4, y: 6 },
    { type: 'spellbinder', team: 'E', x: 0, y: 0 },
  ]);
  const k2 = t.units[1];
  E.applyStatus(t, t.units[2], k2, { para: 2 }, null);
  k2.hp -= 20;
  pray(t);
  assert.strictEqual(k2.para, 0, 'plain paralysis is cured');
  assert.ok(cl.alive);
});

test('a Spellbinder hunts: its chains go on the hunted unit over a bigger threat', () => {
  const s = battle([
    { type: 'knight', team: 'P', x: 2, y: 6, hunted: true },
    { type: 'berserker', team: 'P', x: 6, y: 6, level: 3 },
    { type: 'spellbinder', team: 'E', x: 4, y: 3 },
  ]);
  const [kn, , sb] = s.units;
  s.side = 'E';
  const plan = AI.chooseActivation(s, 'E', { stance: 'balanced', temp: 0 });
  AI.runPlan(s, plan, { stance: 'balanced', temp: 0 });
  const hit = s.events.find((e) => e.t === 'action' && e.uid === sb.uid);
  assert.ok(hit, 'it acted');
  assert.ok(e2(hit, kn), `it went for the hunted Knight (${hit.name} at ${hit.target && hit.target.x},${hit.target && hit.target.y})`);
  function e2(ev, u) {
    return ev.target && ev.target.x === u.x && ev.target.y === u.y;
  }
});

test('Spellbinders only ever come with a bounty', () => {
  for (const act of [1, 2, 3]) for (const g of ['normal', 'elite', 'boss']) {
    const pools = Object.values(D.ENCOUNTERS[act][g] || {});
    for (const t of pools) for (const h of ['spellbinder', 'shackler']) assert.ok(!(t.units || []).includes(h) && !(t.pool || []).includes(h), t.name);
  }
  assert.ok(!D.RECRUITABLE.includes('spellbinder') && !D.RECRUITABLE.includes('shackler'));
  assert.strictEqual(R.bountySquad({ shacklers: 1, hunters: 2 }), 'a Shackler and 2 Spellbinders');
});

// A Shackler with its net thrown at the knight.
function shackled(extra) {
  const s = battle([
    { type: 'knight', team: 'P', x: 4, y: 7, skills: extra && extra.skills },
    { type: 'cleric', team: 'P', x: 4, y: 8, a1: 'c_bless' },
    { type: 'shackler', team: 'E', x: 4, y: 3 },
    { type: 'orc', team: 'E', x: 0, y: 0 },
  ]);
  const [kn, cl, sh] = s.units;
  E.applyStatus(s, sh, kn, { hold: 3 }, null);
  return { s, kn, cl, sh };
}

test('Shackles: the held unit cannot act while the Shackler holds on; the Shackler sits out too', () => {
  const { s, kn, sh } = shackled();
  assert.ok(kn.heldBy === sh.uid && sh.holding === kn.uid && kn.para > 0, 'held');
  // Its next two turns it holds on (sits out); the third it lets go.
  E.unitTurnStart(s, sh);
  assert.strictEqual(E.sitOutReason(s, sh), 'hold');
  assert.strictEqual(E.sitOutReason(s, kn), 'para');
  E.unitTurnStart(s, sh);
  assert.ok(sh.holding, 'still holding');
  E.unitTurnStart(s, sh);
  assert.ok(!sh.holding && !kn.heldBy && kn.para === 0, 'let go after its 3 turns');
  assert.ok(s.events.some((e) => e.t === 'release' && e.uid === kn.uid));
});

test('no cure, rally or immunity slips the net; killing or paralyzing the Shackler does', () => {
  // Unshakable (immune to paralysis) is held all the same.
  const a = shackled();
  a.kn.traits.add('steadfast');
  E.applyStatus(a.s, a.sh, a.kn, { hold: 3 }, null);
  assert.ok(a.kn.heldBy === a.sh.uid, 'held through paralysis immunity');
  pray(a.s);
  assert.ok(a.kn.para > 0 && a.kn.heldBy, 'Blessing does not cut the net');
  // Killing the Shackler frees it at once.
  E.applyDamage(a.s, a.kn, a.sh, 999, { cat: 'none', dmgType: 'true' });
  assert.ok(!a.sh.alive && !a.kn.heldBy && a.kn.para === 0, 'freed when the Shackler falls');
  // Paralyzing the Shackler frees it too.
  const b = shackled();
  E.applyStatus(b.s, b.kn, b.sh, { para: 1 }, null);
  assert.ok(!b.sh.holding && !b.kn.heldBy && b.kn.para === 0, 'freed when the Shackler is paralyzed');
  // A boss is too big to hold.
  const c = battle([
    { type: 'golem_king', team: 'P', x: 4, y: 7 },
    { type: 'shackler', team: 'E', x: 4, y: 3 },
  ]);
  E.applyStatus(c, c.units[1], c.units[0], { hold: 3 }, null);
  assert.ok(!c.units[0].heldBy && !c.units[1].holding, 'bosses slip it');
});

test('a held unit that falls frees its Shackler to throw again', () => {
  const { s, kn, sh } = shackled();
  E.applyDamage(s, sh, kn, 999, { cat: 'none', dmgType: 'true' });
  assert.ok(!kn.alive && !sh.holding);
});

test('the Shackler nets the biggest hitter, and the hunted unit above all', () => {
  const s = battle([
    { type: 'archer', team: 'P', x: 1, y: 7 },
    { type: 'berserker', team: 'P', x: 7, y: 7, level: 3 },
    { type: 'shackler', team: 'E', x: 4, y: 3 },
  ]);
  const [ar, bz, sh] = s.units;
  s.side = 'E';
  const plan = AI.chooseActivation(s, 'E', { stance: 'balanced', temp: 0 });
  AI.runPlan(s, plan, { stance: 'balanced', temp: 0 });
  assert.ok(bz.heldBy === sh.uid, `netted the Level 3 Berserker (holding ${sh.holding}, archer ${ar.uid}, berserker ${bz.uid})`);
  const t = battle([
    { type: 'archer', team: 'P', x: 1, y: 7, hunted: true },
    { type: 'berserker', team: 'P', x: 7, y: 7, level: 3 },
    { type: 'shackler', team: 'E', x: 4, y: 3 },
  ]);
  t.side = 'E';
  const p2 = AI.chooseActivation(t, 'E', { stance: 'balanced', temp: 0 });
  AI.runPlan(t, p2, { stance: 'balanced', temp: 0 });
  assert.ok(t.units[0].heldBy === t.units[2].uid || t.units[1].heldBy === t.units[2].uid, 'it threw its net');
});

console.log(`bounty: ${passed} tests passed`);
