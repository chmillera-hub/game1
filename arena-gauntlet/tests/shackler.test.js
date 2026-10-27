// Shacklers: every elite army fields them, to pin down a carry. Their net (a channel no
// cure breaks), their Spell Shield, and the AI on both sides. Run: node tests/shackler.test.js
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

test('every elite army fields Shacklers (two from Act II); other battles never do', () => {
  const run = R.newRun({ seed: 12, warband: D.WARBANDS[1].id });
  for (const act of [1, 2, 3]) {
    run.act = act;
    for (let k = 0; k < 4; k++) {
      const enc = R.genEncounter(run, { id: 'e' + act + k, row: 2, kind: 'elite', tier: 'elite', mult: 1.85 }, null, []);
      const sh = enc.units.filter((u) => u.type === 'shackler');
      assert.strictEqual(sh.length, act === 1 ? 1 : 2, `act ${act}: Shacklers`);
      assert.ok(!sh.some((u) => u.vip), 'a Shackler is never the commander');
      assert.ok(!('bounty' in enc), 'no bounty on the card');
      assert.ok(R.scoutTips(enc).some((t) => t.startsWith('Shacklers')), 'the war room explains them');
      const med = R.genEncounter(run, { id: 'm' + act + k, row: 2, kind: 'battle', tier: 'medium', mult: 1 }, null, []);
      assert.ok(!med.units.some((u) => u.type === 'shackler'), 'no Shackler in a medium battle');
    }
  }
  for (const act of [1, 2, 3]) for (const g of ['normal', 'elite', 'boss']) {
    for (const t of Object.values(D.ENCOUNTERS[act][g] || {})) assert.ok(!(t.units || []).includes('shackler') && !(t.pool || []).includes('shackler'), t.name);
  }
  assert.ok(!D.RECRUITABLE.includes('shackler'));
  assert.ok(!D.UNITS.spellbinder, 'the Spellbinder is gone');
});

test('a save from the bounty days loads clean: no bounty, no Spellbinder', () => {
  const run = R.newRun({ seed: 14, warband: D.WARBANDS[0].id });
  const o = run.offer.find((x) => x.tier === 'elite');
  o.enc.bounty = { rid: 'u1', name: 'X', type: 'dragon', hunters: 1, shacklers: 1 };
  o.enc.units.push({ type: 'spellbinder', level: 1, x: 0, y: 0 });
  run.lastCarry = { rid: 'u1', name: 'X', type: 'dragon' };
  R.save(run);
  const back = R.load();
  const enc = back.offer.find((x) => x.tier === 'elite').enc;
  assert.ok(!enc.bounty && !enc.units.some((u) => u.type === 'spellbinder') && !back.lastCarry);
});

test('Spell Shield: the first physical or magic hit does nothing and pops it; the next lands', () => {
  for (const atk of ['phys', 'magic']) {
    const s = battle([
      { type: 'knight', team: 'P', x: 4, y: 4 },
      { type: 'shackler', team: 'E', x: 4, y: 3 },
    ]);
    const [a, sh] = s.units;
    assert.strictEqual(sh.ward, 1, 'shielded');
    const pv = E.previewAction(s, a, { kind: 'unit', uid: sh.uid, ai: 0 }).effects.find((e) => e.uid === sh.uid);
    assert.ok(pv && pv.ward && pv.dmg === 0 && !pv.kill, 'the forecast shows the shield taking it');
    const hp = sh.hp;
    const r1 = E.hit(s, a, sh, { dmgType: atk });
    assert.ok(r1.blocked && sh.hp === hp && sh.ward === 0, `${atk}: the first hit does nothing`);
    assert.ok(s.events.some((e) => e.t === 'ward' && e.uid === sh.uid));
    sh.block = 0;
    E.hit(s, a, sh, { dmgType: atk });
    assert.ok(sh.hp < hp, `${atk}: the second lands`);
  }
  // Poison and burns tick past it without popping it.
  const s = battle([
    { type: 'knight', team: 'P', x: 4, y: 4 },
    { type: 'shackler', team: 'E', x: 4, y: 3 },
  ]);
  const sh = s.units[1];
  E.applyDamage(s, null, sh, 5, { cat: 'none', dmgType: 'poison' });
  assert.ok(sh.ward === 1 && sh.hp === sh.maxHp - 5);
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
  assert.strictEqual(E.sitOutReason(s, kn), 'held');
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

test('the Shackler nets the biggest hitter', () => {
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
});

test('Shackles have no limit: when its hold runs out it throws again at once', () => {
  const { s, kn, sh } = shackled();
  const net = sh.acts.find((a) => a.name === 'Shackles');
  assert.ok(!net.uses && net.left === Infinity, 'no use limit');
  E.unitTurnStart(s, sh);
  E.unitTurnStart(s, sh);
  E.unitTurnStart(s, sh);
  assert.ok(!sh.holding && !kn.heldBy, 'let go after 3 of its turns');
  assert.strictEqual(E.sitOutReason(s, sh), null, 'free to act that same turn');
  s.side = 'E';
  s.due = sh.uid;
  const plan = AI.chooseActivation(s, 'E', { stance: 'balanced', temp: 0 });
  AI.runPlan(s, plan, { stance: 'balanced', temp: 0 });
  assert.ok(kn.heldBy === sh.uid && sh.holding === kn.uid, 'it threw the net again, and holds it');
  assert.ok(sh.x === 4 && sh.y === 3, 'and stayed put, holding the chain');
});

test('shoving or dragging a Shackler breaks its hold, even a shove into a wall', () => {
  for (const how of ['shove', 'pull', 'wall']) {
    const s = battle([
      { type: 'knight', team: 'P', x: 4, y: 7 },
      { type: 'shackler', team: 'E', x: 4, y: how === 'wall' ? 0 : 3 },
      { type: 'golem', team: 'P', x: 4, y: how === 'wall' ? 1 : 4 },
    ]);
    const [kn, sh, go] = s.units;
    E.applyStatus(s, sh, kn, { hold: 3 }, null);
    assert.ok(kn.heldBy === sh.uid);
    E.applyStatus(s, go, sh, how === 'pull' ? { pull: 1 } : { knock: 1 }, null);
    assert.ok(!sh.holding && !kn.heldBy && kn.para === 0, `${how}: the net falls away`);
  }
});

test('a decked-out Level 3 Dragon cannot kill a Shackler before it acts: the shield, then a hit it survives', () => {
  const run = R.newRun({ seed: 3, warband: D.WARBANDS[0].id });
  const r = R.addRecruit(run, 'dragon');
  r.load.lv = 3;
  r.load.a2 = 'd_tamed';
  for (const [kind, key, id] of [['talent', 'talents', 'd_hellfire'], ['talent', 'talents', 'd_hoard'], ['talent', 'talents', 'd_searing'], ['skill', 'skills', 'vampiric'], ['skill', 'skills', 'avatar'], ['gear', 'gear', 'flame_brand'], ['gear', 'gear', 'reactive_plate']]) r.load[key].push(R.addItem(run, kind, id).uid);
  r.enchant = 'spellblade';
  const s = battle([Object.assign(R.specFor(run, r), { team: 'P', x: 4, y: 5 }), { type: 'shackler', team: 'E', x: 4, y: 4 }]);
  const [dr, sh] = s.units;
  sh.block = 0;
  E.hit(s, dr, sh, {});
  assert.ok(sh.hp === sh.maxHp && sh.ward === 0, 'the first breath only pops the shield');
  E.hit(s, dr, sh, { noCrit: true });
  assert.ok(sh.alive && sh.hp > 0, `it survives the second (${sh.hp}/${sh.maxHp} left)`);
});

test("your army goes for the Shackler holding one of its own", () => {
  const s = battle([
    { type: 'archer', team: 'P', x: 4, y: 7 },
    { type: 'berserker', team: 'P', x: 2, y: 6, level: 3 },
    { type: 'shackler', team: 'E', x: 4, y: 3 },
    { type: 'orc', team: 'E', x: 6, y: 4 },
  ]);
  const [ar, bz, sh, orc] = s.units;
  E.applyStatus(s, sh, bz, { hold: 3 }, null);
  sh.ward = 0;
  s.side = 'P';
  s.due = ar.uid;
  const plan = AI.chooseActivation(s, 'P', { stance: 'balanced', temp: 0 });
  AI.runPlan(s, plan, { stance: 'balanced', temp: 0 });
  const shot = s.events.find((e) => e.t === 'action' && e.uid === ar.uid);
  assert.ok(shot && shot.target && shot.target.x === sh.x && shot.target.y === sh.y, `the Archer shot the Shackler, not the Orc (${shot && JSON.stringify(shot.target)})`);
  assert.ok(orc.alive);
});

console.log(`shackler: ${passed} tests passed`);
