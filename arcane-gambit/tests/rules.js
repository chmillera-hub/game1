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
function battle(map, legend, army, opts) {
  const enc = Object.assign({ id: 'rt' + n++, act: 1, tier: 'normal', name: 'test', map, legend, supply: 99, slots: 9 }, opts || {});
  AG.Encounters[enc.id] = enc;
  return B.create(enc, army.map((a) => Object.assign({ talents: [], rune: null, rank: 0 }, a)), { record: true });
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

console.log(passed + ' passed' + (failed.length ? ', ' + failed.length + ' failed:\n  ' + failed.join('\n  ') : ''));
process.exit(failed.length ? 1 : 0);
