/* Deterministic rule checks on tiny hand-built boards.
   node tests/rules.js */
'use strict';
const H = require('./harness');
const AG = H.load();
const B = AG.B;
let passed = 0;
const failed = [];

function test(name, fn) {
  try { fn(); passed++; } catch (e) { failed.push(name + ': ' + e.message); }
}
function eq(a, b, msg) { if (a !== b) throw new Error((msg || 'expected') + ' ' + JSON.stringify(b) + ', got ' + JSON.stringify(a)); }
function ok(v, msg) { if (!v) throw new Error(msg || 'expected truthy'); }

let n = 0;
function battle(map, legend, army, opts, bopts) {
  const enc = Object.assign({ id: 'rt' + n++, act: 1, tier: 'normal', name: 'test', map, legend, supply: 99 }, opts || {});
  AG.Encounters[enc.id] = enc;
  return B.create(enc, army.map((a) => Object.assign({ talents: [], rune: null, rank: 0 }, a)), Object.assign({ record: true }, bopts));
}
const find = (s, def, side) => s.units.find((u) => u.def === def && (side == null || u.side === side));

test('speed orders the queue, ties go to the player', () => {
  const s = battle(['g....', '.....', 'p....'], { g: 'goblin' }, [{ def: 'apprentice', x: 0, y: 2 }]);
  B.startRound(s);
  // Apprentice and Goblin both have SPD 5: the player's piece goes first.
  eq(B.U(s, s.queue[0]).def, 'apprentice', 'first in queue');
});

test('chill re-sorts the rest of the round', () => {
  const s = battle(['w...', '....', 'p...'], { w: 'wolf' }, [{ def: 'squire', x: 0, y: 2 }]);
  B.startRound(s);
  const wolf = find(s, 'wolf');
  eq(s.queue[0], wolf.uid, 'wolf first');
  B.addStatus(s, wolf, 'chill', { a: 5 });
  eq(s.queue[0], find(s, 'squire').uid, 'chilled wolf drops behind the squire');
});

test('frozen units skip their next turn and take +2 from hits', () => {
  const s = battle(['g...', '....', 'p...'], { g: 'goblin' }, [{ def: 'squire', x: 0, y: 2 }]);
  const g = find(s, 'goblin');
  B.addStatus(s, g, 'frozen', { t: 1 });
  const d = B.calcDamage(s, find(s, 'squire'), g, 2, { kind: 'attack', melee: true });
  eq(d, 4, 'shatter damage');
  eq(B.startTurn(s, g), true, 'turn skipped');
  ok(!g.st.frozen, 'thawed after skipping');
});

test('knockback into a chasm destroys a walker, not a flyer', () => {
  const s = battle(['....', '.g..', '.~..', '....', 'pppp'], { g: 'goblin' }, [{ def: 'stormCaller', x: 1, y: 0 }]);
  const g = find(s, 'goblin');
  B.push(s, find(s, 'stormCaller'), g, 0, 1);
  eq(g.alive, false, 'goblin fell');
  const s2 = battle(['....', '.b..', '.~..', '....', 'pppp'], { b: 'bat' }, [{ def: 'stormCaller', x: 1, y: 0 }]);
  const bat = find(s2, 'bat');
  B.push(s2, find(s2, 'stormCaller'), bat, 0, 1);
  eq(bat.alive && bat.y === 2, true, 'bat hovers over the chasm');
});

test('a squire promotes on the far rank', () => {
  const s = battle(['....', '.g..', 'pp..'], { g: 'goblin' }, [{ def: 'squire', x: 0, y: 2 }]);
  const sq = find(s, 'squire');
  B.applyMove(s, sq, 0 * s.board.w + 0, 'walk');
  eq(sq.name, 'Champion', 'promoted');
  eq(sq.hp, sq.maxHp, 'fully healed');
  ok(!AG.Units.squire.passives.promotion.done, 'shared definition untouched');
});

test('the phylactery keeps the lich alive until it breaks', () => {
  const s = battle(['P.L.', '....', 'pppp'], { P: 'phylactery', L: 'lich' }, [{ def: 'knight', x: 0, y: 2 }]);
  const lich = find(s, 'lich'), jar = find(s, 'phylactery');
  B.hit(s, null, lich, 999, { kind: 'true' });
  eq(lich.alive && lich.hp === 1, true, 'lich clings on');
  B.hit(s, null, jar, 999, { kind: 'true' });
  eq(jar.alive, false, 'jar broken');
  B.hit(s, null, lich, 5, { kind: 'true' });
  eq(lich.alive, false, 'now it can die');
});

test('slimes split, skeletons reassemble unless burned', () => {
  const s = battle(['.s..', '....', 'pppp'], { s: 'slime' }, [{ def: 'knight', x: 0, y: 2 }]);
  B.hit(s, null, find(s, 'slime'), 99, { kind: 'true' });
  eq(s.units.filter((u) => u.def === 'slimeling' && u.alive).length, 2, 'two slimelings');
  const s2 = battle(['.k..', '....', 'pppp'], { k: 'skeleton' }, [{ def: 'knight', x: 0, y: 2 }]);
  B.hit(s2, null, find(s2, 'skeleton'), 99, { kind: 'true' });
  ok(s2.units.some((u) => u.def === 'bonePile' && u.alive), 'bone pile left behind');
  const s3 = battle(['.k..', '....', 'pppp'], { k: 'skeleton' }, [{ def: 'knight', x: 0, y: 2 }]);
  B.hit(s3, null, find(s3, 'skeleton'), 99, { kind: 'ability', tag: 'fire' });
  ok(!s3.units.some((u) => u.def === 'bonePile'), 'fire leaves nothing');
});

test('haste grants an extra turn right after the caster', () => {
  const s = battle(['g...', '....', 'pp..'], { g: 'goblin' }, [{ def: 'chronomancer', x: 0, y: 2 }, { def: 'knight', x: 1, y: 2 }]);
  B.startRound(s);
  const k = find(s, 'knight');
  B.useAbility(s, find(s, 'chronomancer'), 'haste', k.uid);
  eq(s.extra[0], k.uid, 'knight queued for an extra turn');
});

test('cooldowns tick at the start of the owner turn', () => {
  const s = battle(['g...', '....', 'p...'], { g: 'goblin' }, [{ def: 'apprentice', x: 0, y: 2 }]);
  const a = find(s, 'apprentice');
  B.useAbility(s, a, 'arcaneBolt', find(s, 'goblin').uid);
  eq(a.cd.arcaneBolt, 3, 'set to 3');
  B.startTurn(s, a); B.startTurn(s, a); B.startTurn(s, a);
  eq(a.cd.arcaneBolt, 0, 'ready again on the third turn');
});

test('a stalemate brings the storm early and the battle ends', () => {
  const s = battle(['..s..', '.....', '~~~~~', '.....', 'ppppp'], { s: 'slime' }, [{ def: 'golem', x: 2, y: 4 }]);
  let early = 0;
  for (let i = 0; i < 2000 && !s.over; i++) {
    B.step(s);
    for (const e of s.ev) if (e.type === 'stormEarly') early = e.round;
    s.ev.length = 0;
  }
  ok(early > 0 && early < 12, 'storm came early (round ' + early + ')');
  ok(s.over && s.round <= 14, 'battle over by round ' + s.round);
});

test('the storm resolves simultaneously', () => {
  const s = battle(['g...', '....', 'p...'], { g: 'goblin' }, [{ def: 'imp', x: 0, y: 2 }], { storm: 1 });
  find(s, 'goblin').hp = 1;
  find(s, 'imp').hp = 1;
  B.startRound(s);
  eq(s.over, true, 'over');
  eq(s.winner, 0, 'a mutual wipe counts as clearing the board');
});

test('the AI finishes a dying enemy rather than poking a healthy one', () => {
  // A Squire (2 ATK) next to two goblins: kill the 1-HP one, do not chip the other.
  const s = battle(['......', '..gG..', '......', 'pppppp'], { g: 'goblin', G: 'goblin' }, [{ def: 'squire', x: 2, y: 2 }]);
  const [g1] = s.units.filter((u) => u.def === 'goblin');
  g1.hp = 1;
  const plan = AG.AI.choose(s, find(s, 'squire'));
  ok(plan.act && plan.act.k === 'atk' && plan.act.t === g1.uid, 'targets the wounded goblin: ' + plan.reason);
});

test('with a kill available on either target, the AI removes the healthier enemy', () => {
  const s = battle(['......', '..gG..', '......', '..p...'], { g: 'goblin', G: 'goblin' }, [{ def: 'knight', x: 2, y: 3 }]);
  const [g1, g2] = s.units.filter((u) => u.def === 'goblin');
  g1.hp = 1;
  const plan = AG.AI.choose(s, find(s, 'knight'));
  ok(plan.act && plan.act.k === 'atk' && plan.act.t === g2.uid, 'kills the full-health goblin: ' + plan.reason);
});

test('the AI will not fireball its own allies for a small gain', () => {
  const s = battle(['.......', '...g...', '.......', '.......', 'ppppppp'], { g: 'goblin' }, [{ def: 'pyromancer', x: 3, y: 4 }, { def: 'knight', x: 3, y: 2 }]);
  const plan = AG.AI.choose(s, find(s, 'pyromancer'));
  const fb = plan.act && plan.act.k === 'ab' && plan.act.id === 'fireball';
  if (fb) {
    const t = plan.act.t;
    const tx = t % s.board.w, ty = (t / s.board.w) | 0;
    ok(AG.cheb(tx, ty, 3, 2) > 1, 'fireball does not splash the knight');
  }
});

test('a death burst cannot end the battle before the phoenix lays its egg', () => {
  const s = battle(['g....', '.....', '..g..', '.....'], { g: 'goblin' }, [{ def: 'phoenix', x: 2, y: 3 }]);
  const near = s.units.find((u) => u.def === 'goblin' && u.y === 2);
  near.hp = 1;
  B.hit(s, near, find(s, 'phoenix'), 999, { kind: 'true' });
  eq(near.alive, false, 'the burst killed the goblin');
  ok(s.units.some((u) => u.def === 'emberEgg' && u.alive), 'egg laid');
  eq(s.over, false, 'battle goes on');
});

test('a unit can be hasted only once per round', () => {
  const s = battle(['g....', '.....', 'ppp..'], { g: 'goblin' }, [{ def: 'chronomancer', x: 0, y: 2 }, { def: 'chronomancer', x: 1, y: 2 }, { def: 'knight', x: 2, y: 2 }]);
  B.startRound(s);
  const [c1, c2] = s.units.filter((u) => u.def === 'chronomancer');
  const k = find(s, 'knight');
  B.useAbility(s, c1, 'haste', k.uid);
  s.extra.length = 0; // the knight has taken its extra turn
  const ts = AG.Abilities.haste.targets(s, c2, c2.abil[0].p);
  ok(ts.indexOf(k.uid) < 0, 'knight cannot be hasted again');
  ok(ts.indexOf(c1.uid) >= 0, 'the other chronomancer still can');
});

test('the Phylactery Shard raises a unit that fell into a chasm beside it', () => {
  const s = battle(['g...', '....', '.~..', 'pppp'], { g: 'goblin' }, [{ def: 'knight', x: 1, y: 1 }], null, { relics: ['phylacteryShard'] });
  B.push(s, find(s, 'goblin'), find(s, 'knight'), 0, 1);
  const k = s.units.find((u) => u.def === 'knight' && u.alive);
  ok(k, 'knight rose again');
  ok(AG.cheb(k.x, k.y, 1, 2) === 1, 'next to the chasm');
  eq(k.hp, Math.round(k.maxHp / 2), 'with half its health');
  eq(s.flags.shard0, true, 'shard spent');
});

test('Corpse Explosion leaves no bone pile', () => {
  const s = battle(['.....', '..g..', '.....', 'ppppp'], { g: 'goblin' }, [{ def: 'necromancer', x: 0, y: 3 }]);
  const nec = find(s, 'necromancer');
  const sk = B.summon(s, 'skeleton', 0, 2 * s.board.w + 2, { owner: nec.uid });
  B.useAbility(s, nec, 'corpseExplosion', sk.uid);
  eq(sk.alive, false, 'skeleton detonated');
  ok(!s.units.some((u) => u.def === 'bonePile' && u.alive), 'nothing left to reassemble');
});

test('a reassembled skeleton still counts toward its necromancer', () => {
  const s = battle(['..g..', '.....', '.....', 'ppppp'], { g: 'goblin' }, [{ def: 'necromancer', x: 0, y: 3 }]);
  const nec = find(s, 'necromancer');
  const sk = B.summon(s, 'skeleton', 0, 2 * s.board.w + 2, { owner: nec.uid });
  B.hit(s, null, sk, 99, { kind: 'true' });
  const pile = s.units.find((u) => u.def === 'bonePile' && u.alive);
  ok(pile, 'bone pile');
  eq(pile.owner, nec.uid, 'pile owned by the necromancer');
  B.startRound(s);
  B.startRound(s);
  const back = s.units.find((u) => u.def === 'skeleton' && u.alive);
  ok(back, 'skeleton stood back up');
  eq(AG.countOwned(s, nec, 'skeleton'), 1, 'counted toward Raise Dead');
});

test('on an odd-shaped board only the true far rank promotes', () => {
  const s = battle(['  .  ', ' ... ', '....g', ' ppp ', '  p  '], { g: 'goblin' }, [{ def: 'squire', x: 1, y: 3 }]);
  const sq = find(s, 'squire');
  const w = s.board.w;
  B.applyMove(s, sq, 2 * w + 0, 'walk');
  eq(sq.name, 'Squire', 'top of the left column is not the far rank');
  B.applyMove(s, sq, 1 * w + 1, 'walk');
  eq(sq.name, 'Squire', 'nor is the next one');
  B.applyMove(s, sq, 0 * w + 2, 'walk');
  eq(sq.name, 'Champion', 'the apex is');
});

test('area spells are not aimed at stealthed enemies', () => {
  const s = battle(['.....', '..g..', '.....', 'ppppp'], { g: 'goblin' }, [{ def: 'pyromancer', x: 2, y: 3 }]);
  const pyro = find(s, 'pyromancer');
  const fb = pyro.abil.find((a) => a.id === 'fireball');
  ok(AG.Abilities.fireball.targets(s, pyro, fb.p).length > 0, 'a visible goblin can be targeted');
  B.addStatus(s, find(s, 'goblin'), 'stealth', { t: 2 });
  eq(AG.Abilities.fireball.targets(s, pyro, fb.p).length, 0, 'a hidden one cannot');
});

const hitsOn = (s, u) => s.ev.filter((e) => e.type === 'dmg' && e.uid === u.uid).length;

test('a shell that knocks its target back does not splash it too', () => {
  const s = battle(['.....', '..g..', '.....', '.....', '..p..'], { g: 'goblin' }, [{ def: 'cannoneer', x: 2, y: 4, talents: ['heavyShells'] }]);
  const g = find(s, 'goblin');
  g.maxHp = g.hp = 30;
  B.doAttack(s, find(s, 'cannoneer'), g);
  eq(g.y, 0, 'knocked back');
  eq(hitsOn(s, g), 1, 'hit once');
});

test('Iron Fist: the second strike needs the target still in reach', () => {
  const s = battle(['.....', '..g..', '..p..', '.....'], { g: 'goblin' }, [{ def: 'monk', x: 2, y: 2, talents: ['ironFist'] }]);
  const g = find(s, 'goblin');
  g.maxHp = g.hp = 30;
  B.doAttack(s, find(s, 'monk'), g);
  eq(g.y, 0, 'knocked back');
  eq(hitsOn(s, g), 1, 'one strike landed');
});

test('Bat Swarm never exceeds its cap', () => {
  const s = battle(['.......', '...V...', '.......', '.......', 'ppppppp'], { V: 'vampireLord' }, [{ def: 'knight', x: 0, y: 4 }]);
  const v = find(s, 'vampireLord');
  for (const x of [0, 5, 6]) B.summon(s, 'bat', 1, 3 * s.board.w + x, { owner: v.uid });
  B.useAbility(s, v, 'batSwarm', v.uid);
  eq(AG.countOwned(s, v, 'bat'), 4, 'capped at 4');
});

test('a troll does not regenerate on the turn its burn runs out', () => {
  const s = battle(['.....', '..T..', '.....', 'ppppp'], { T: 'troll' }, [{ def: 'knight', x: 0, y: 3 }]);
  const t = find(s, 'troll');
  t.hp = t.maxHp - 6;
  B.addStatus(s, t, 'burn', { d: 1, t: 1 });
  const before = t.hp;
  B.startTurn(s, t);
  ok(!t.st.burn && t.hp < before, 'burned without healing: ' + before + ' -> ' + t.hp);
  const mid = t.hp;
  B.startTurn(s, t);
  eq(t.hp, mid + 3, 'regenerates once the fire is out');
});

test('Accelerate moves a hasted ally up the rest of the round', () => {
  const s = battle(['...s', '....', 'pp..'], { s: 'slimeling' }, [{ def: 'chronomancer', x: 0, y: 2, talents: ['accelerate'] }, { def: 'knight', x: 1, y: 2 }]);
  B.startRound(s);
  const c = find(s, 'chronomancer'), k = find(s, 'knight'), sl = find(s, 'slimeling');
  eq(s.queue.indexOf(sl.uid) < s.queue.indexOf(k.uid), true, 'slimeling (SPD 3) starts ahead of the knight (SPD 2)');
  s.queue.splice(s.queue.indexOf(c.uid), 1);
  B.useAbility(s, c, 'haste', k.uid);
  eq(s.queue[0], k.uid, 'the knight (now SPD 4) goes next');
});

test('when valuing Haste the AI only replays turns that are still legal', () => {
  // The Ranger shoots up the file; squares the Chronomancer can blink to
  // block that shot, so a cached plan must not be replayed there.
  const s = battle(['...g...', '.......', '.......', '.......', '.......', '.......', 'ppppppp'], { g: 'goblin' }, [{ def: 'chronomancer', x: 1, y: 6 }, { def: 'ranger', x: 3, y: 6 }]);
  B.startRound(s);
  const orig = B.execPlan;
  const bad = [];
  B.execPlan = function (s2, u2, plan) {
    const c = B.clone(s2), cu = B.U(c, u2.uid), here = B.cellOf(c, cu);
    if (plan.mv >= 0 && plan.mv !== here) {
      if (!B.moveOptions(c, cu).some((m) => m.i === plan.mv && m.k === plan.mk)) bad.push(cu.name + ' move');
      else B.applyMove(c, cu, plan.mv, plan.mk);
    }
    const a = plan.act;
    if (a && cu.alive && !c.over) {
      const ab = a.k === 'ab' ? cu.abil.find((x) => x.id === a.id) : null;
      const legal = a.k === 'atk' ? B.attackTargets(c, cu) : ab && !cu.cd[a.id] ? AG.Abilities[a.id].targets(c, cu, ab.p) : [];
      if (legal.indexOf(a.t) < 0) bad.push(cu.name + ' ' + (a.id || 'attack'));
    }
    return orig.apply(this, arguments);
  };
  let plan;
  try { plan = AG.AI.choose(s, find(s, 'chronomancer')); } finally { B.execPlan = orig; }
  ok(plan, 'a plan was chosen');
  eq(bad.length, 0, 'illegal replays: ' + bad.join(', '));
});

// ------------------------------------------------------------ the run
global.localStorage = global.localStorage || { _d: {}, getItem(k) { return this._d[k] || null; }, setItem(k, v) { this._d[k] = String(v); }, removeItem(k) { delete this._d[k]; } };
const Run = AG.Run;

test('the draft offers two commons, two uncommons and a rare, then an opening', () => {
  const run = Run.newRun({ seed: 42 });
  const got = [];
  for (const r of Run.DRAFT) {
    eq(run.screen, 'draft', 'still drafting');
    eq(run.draft.options.length, 3, 'three to choose from');
    ok(run.draft.options.every((d) => AG.Units[d].rarity === r && run.units.indexOf(d) < 0), 'options of the right rarity, not owned');
    const pick = run.draft.options[1];
    Run.draftPick(run, pick);
    got.push(AG.Units[pick].rarity);
  }
  eq(got.join(','), 'common,common,uncommon,uncommon,rare', 'picks');
  eq(run.screen, 'boon', 'then the opening');
  eq(run.units.length, 6, 'the Squire and five picks');
  Run.takeBoon(run, 'ledger');
  eq(run.screen, 'actIntro', 'then the act');
  eq(run.tower.length, 8, 'eight floors');
});

test('each battle floor offers easy, medium and hard, or elite on the elite floors', () => {
  const run = Run.newRun({ seed: 7 });
  while (run.draft) Run.draftPick(run, run.draft.options[0]);
  Run.takeBoon(run, 'ledger');
  for (let f = 0; f < Run.FLOORS.length; f++) {
    run.floor = f;
    const fl = Run.currentFloor(run);
    Run.prepareFloor(run);
    if (fl.type !== 'battle') { ok(!fl.options, 'no fights on a ' + fl.type + ' floor'); continue; }
    const diffs = fl.options.map((o) => o.diff).join(',');
    eq(diffs, Run.ELITE_FLOORS.indexOf(f) >= 0 ? 'easy,medium,elite' : 'easy,medium,hard', 'floor ' + (f + 1));
    ok(fl.options.every((o) => AG.Encounters[o.enc] && AG.Encounters[o.enc].act === 1), 'act I fights');
    eq(new Set(fl.options.map((o) => o.enc)).size, 3, 'three different fights');
  }
});

test('a lost battle costs nothing and can be retried or swapped for another fight', () => {
  const run = Run.newRun({ seed: 9 });
  while (run.draft) Run.draftPick(run, run.draft.options[0]);
  Run.takeBoon(run, 'ledger');
  run.screen = 'tower';
  const gold = run.gold, units = run.units.length;
  Run.chooseFight(run, 2);
  eq(run.screen, 'setup', 'war room');
  const s = B.create(AG.Encounters[run.battle.enc], [], { record: true });
  Run.battleLost(run, s);
  eq(run.screen, 'setup', 'straight back to the war room');
  eq(run.gold, gold, 'no gold lost');
  eq(run.units.length, units, 'no units lost');
  eq(run.battle.attempts, 1, 'attempt counted');
  Run.backToTower(run);
  eq(run.screen, 'tower', 'back to the tower');
  eq(run.floor, 0, 'same floor');
  Run.chooseFight(run, 0);
  eq(run.battle.tier, 'easy', 'took the easy one instead');
});

test('an event’s supply for the next battle survives backing out of a fight', () => {
  const run = Run.newRun({ seed: 11 });
  while (run.draft) Run.draftPick(run, run.draft.options[0]);
  Run.takeBoon(run, 'ledger');
  run.screen = 'tower';
  Run.nextBattleSupply(run, 4);
  Run.chooseFight(run, 1);
  const enc = AG.Encounters[run.battle.enc];
  eq(Run.limits(run, enc).supply, enc.supply + 2 + 4, 'ledger and the event both count');
  Run.backToTower(run);
  eq(run.nextSupply, 4, 'still owed');
  Run.chooseFight(run, 0);
  eq(run.battle.supplyMod, 4, 'applied to the fight actually taken');
  eq(run.nextSupply, 0, 'and only once');
});

test('only supply and squares limit the army', () => {
  const run = Run.sandbox();
  const enc = AG.Encounters.zugzwang;
  const lim = Run.limits(run, enc);
  const army = Run.autoArmy(run, enc);
  const cost = Run.formationCost(run, army);
  ok(cost <= lim.supply, 'within supply: ' + cost + ' of ' + lim.supply);
  ok(army.length <= lim.cells, 'within the squares');
  const minCost = Math.min.apply(null, run.units.map((d) => AG.Units[d].cost));
  eq(army.length, Math.min(lim.cells, Math.floor(lim.supply / minCost)), 'as many units as possible');
  eq(new Set(army.map((e) => e.x + ',' + e.y)).size, army.length, 'one unit per square');
  const { board } = AG.parseBoard(enc.map, enc.legend);
  ok(army.every((e) => board.deploy[e.y * board.w + e.x]), 'all on deploy squares');
  ok(Run.validate(run, enc, army).ok, 'a legal army');
  const big = Run.autoArmy(Object.assign({}, run, { supplyBonus: 200 }), enc);
  eq(big.length, lim.cells, 'with endless supply, every square is filled');
});

test('Invincible caps the damage taken each round', () => {
  const s = battle(['..Z..', '.....', 'ppppp'], { Z: 'zugzwang' }, [{ def: 'archmage', x: 2, y: 2 }]);
  const z = find(s, 'zugzwang');
  s.round = 1;
  const hp = z.hp;
  B.hit(s, null, z, 15, { kind: 'true' });
  B.hit(s, null, z, 15, { kind: 'true' });
  eq(hp - z.hp, 20, 'capped at 20 in round 1');
  eq(B.hit(s, null, z, 5, { kind: 'true' }), 0, 'nothing more this round');
  s.round = 2;
  B.hit(s, null, z, 7, { kind: 'true' });
  eq(hp - z.hp, 27, 'a new round, a new cap');
});

test('Beat of Death hurts every piece that attacks', () => {
  const s = battle(['..Z..', '..q..', '.....', 'ppppp'], { Z: 'zugzwang', q: 'goblin' }, [{ def: 'scout', x: 2, y: 3 }]);
  const scout = find(s, 'scout');
  const hp = scout.hp;
  B.doAttack(s, scout, find(s, 'goblin'));
  eq(hp - scout.hp, 1, 'the scout paid 1 health for its shot');
});

test('a duel puts the defending army on the far side, mirrored', () => {
  const enc = Run.duelEncounter('grandmaster');
  const mine = [{ def: 'knight', x: 1, y: 7, talents: [], rune: null, rank: 0 }];
  const theirs = [{ def: 'cleric', x: 2, y: 6, talents: [], rune: null, rank: 1 }];
  const s = B.create(enc, mine, Object.assign({ record: false }, Run.duelOpts({ relics: [] }, { army: theirs, relics: ['ironRations'] })));
  const c = find(s, 'cleric');
  eq(c.side, 1, 'the defender is the enemy');
  eq(c.x + ',' + c.y, '2,1', 'mirrored to the far side');
  eq(c.rank, 1, 'keeps its rank');
  eq(c.shield, 2, 'and its relics (Iron Rations)');
  eq(find(s, 'knight').side, 0, 'the challenger is the near side');
  eq(s.units.length, 2, 'nobody else on the board');
});

test('a challenger climbs the Hall until its first loss', () => {
  eq(Run.hallRank(0, []), 0, 'an empty Hall: first place');
  eq(Run.hallRank(3, [false]), 3, 'lost the first duel: bottom');
  eq(Run.hallRank(3, [true, false]), 2, 'won one, then lost');
  eq(Run.hallRank(3, [true, true, true]), 0, 'beat them all: top');
  localStorage._d = {};
  const run = Run.newRun({ seed: 5 });
  run.finalArmy = { army: [{ def: 'knight', x: 0, y: 7, talents: [], rune: null, rank: 0 }], relics: [], enc: 'grandmaster' };
  run.stats.endedAt = 1;
  Run.startClimb(run);
  ok(run.climb.placed, 'nobody to duel');
  eq(Run.loadHall().entries.length, 1, 'enshrined');
  ok(run.done && !Run.load(false), 'the finished run is not kept');
});
console.log(passed + ' passed' + (failed.length ? ', ' + failed.length + ' failed:\n  ' + failed.join('\n  ') : ''));
process.exit(failed.length ? 1 : 0);
