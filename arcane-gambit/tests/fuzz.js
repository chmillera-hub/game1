/* Invariant fuzzer: random armies (with talents, runes and relics) on every
   encounter, checking the board after every step and that the AI never
   changes the real state while it thinks.
   node tests/fuzz.js [--n 4] [--seed 1] */
'use strict';
const H = require('./harness');
const AG = H.load();

const args = process.argv.slice(2);
const get = (k, d) => { const i = args.indexOf(k); return i >= 0 ? +args[i + 1] : d; };
const N = get('--n', 4);
const rng = new AG.RNG(get('--seed', 1));
const failures = [];

function fail(ctx, msg) {
  failures.push(ctx + ': ' + msg);
  if (failures.length > 40) { report(); process.exit(1); }
}

function check(s, ctx) {
  const b = s.board;
  for (let i = 0; i < b.n; i++) {
    const id = s.occ[i];
    if (!id) continue;
    const u = AG.B.U(s, id);
    if (!u) { fail(ctx, 'occ points at missing uid ' + id); continue; }
    if (!u.alive) fail(ctx, 'dead ' + u.name + '#' + id + ' still occupies ' + i);
    if (u.y * b.w + u.x !== i) fail(ctx, u.name + '#' + id + ' occupies ' + i + ' but stands at ' + (u.y * b.w + u.x));
  }
  for (const u of s.units) {
    for (const k of ['hp', 'maxHp', 'atk', 'spd', 'armor', 'shield']) {
      if (!Number.isFinite(u[k])) fail(ctx, u.name + '#' + u.uid + ' has ' + k + '=' + u[k]);
    }
    if (!u.alive) continue;
    const i = u.y * b.w + u.x;
    if (s.occ[i] !== u.uid) fail(ctx, 'alive ' + u.name + '#' + u.uid + ' not in occ at its square');
    if (u.hp <= 0 && !s.holdEnd) fail(ctx, 'alive ' + u.name + ' with hp ' + u.hp);
    if (u.hp > u.maxHp) fail(ctx, u.name + ' hp ' + u.hp + ' > max ' + u.maxHp);
    if (u.shield < 0) fail(ctx, u.name + ' negative shield');
    if (!AG.standable(b, i, u.flying)) fail(ctx, u.name + ' stands on illegal terrain ' + b.terr[i]);
    for (const k in u.cd) if (!(u.cd[k] >= 0)) fail(ctx, u.name + ' cooldown ' + k + '=' + u.cd[k]);
  }
}

function randomArmy(enc) {
  const ids = AG.playerUnitIds();
  const out = [];
  let budget = enc.supply + 6;
  while (out.length < enc.slots + 1) {
    const ok = ids.filter((d) => AG.Units[d].cost <= budget);
    if (!ok.length) break;
    const d = rng.pick(ok);
    budget -= AG.Units[d].cost;
    const talents = rng.chance(0.7) ? rng.shuffle(AG.Units[d].talents).slice(0, rng.int(1, 2)) : [];
    const rune = rng.chance(0.5) ? rng.pick(Object.keys(AG.Runes)) : null;
    out.push({ def: d, talents, rune });
  }
  return out;
}

const t0 = Date.now();
let battles = 0, steps = 0, aiChecks = 0;
for (const enc of AG.encounterList()) {
  for (let k = 0; k < N; k++) {
    const entries = randomArmy(enc);
    const army = H.autoPlace(AG, enc, entries).map((e) => Object.assign({ rank: rng.int(0, 2) }, e));
    const relics = rng.shuffle(Object.keys(AG.Relics)).slice(0, rng.int(0, 5));
    const ctx0 = enc.id + ' [' + army.map((e) => e.def + (e.talents.length ? ':' + e.talents.join(',') : '') + (e.rune ? '@' + e.rune : '')).join(' ') + '] relics ' + relics.join(',');
    let s;
    try {
      s = AG.B.create(enc, army, { relics, record: rng.chance(0.5), ramp: rng.int(0, 6) * 0.03 });
    } catch (e) { fail(ctx0, 'create threw ' + e.stack.split('\n').slice(0, 3).join(' | ')); continue; }
    battles++;
    let n = 0;
    try {
      while (!s.over && n++ < 3000) {
        // Every so often, make sure thinking does not change the real board.
        const next = s.extra[0] || s.queue[0];
        if (next && rng.chance(0.08)) {
          const u = AG.B.U(s, next);
          if (u && u.alive && !u.st.frozen && !u.st.stunned) {
            const before = JSON.stringify(s.units) + JSON.stringify(Array.from(s.occ)) + JSON.stringify(s.queue) + JSON.stringify(s.extra) + JSON.stringify(s.rules) + JSON.stringify(s.flags);
            AG.AI.choose(s, u);
            const after = JSON.stringify(s.units) + JSON.stringify(Array.from(s.occ)) + JSON.stringify(s.queue) + JSON.stringify(s.extra) + JSON.stringify(s.rules) + JSON.stringify(s.flags);
            if (before !== after) fail(ctx0, 'AI.choose for ' + u.name + ' changed the real state');
            aiChecks++;
          }
        }
        AG.B.step(s);
        steps++;
        if (s.ev) s.ev.length = 0;
        check(s, ctx0 + ' r' + s.round);
      }
    } catch (e) {
      fail(ctx0 + ' r' + (s && s.round), 'threw ' + e.stack.split('\n').slice(0, 4).join(' | '));
      continue;
    }
    if (!s.over) fail(ctx0, 'did not finish in 3000 steps (round ' + s.round + ')');
    if (s.round > s.rules.maxRounds + 1) fail(ctx0, 'ran to round ' + s.round);
  }
}
function report() {
  const uniq = Array.from(new Set(failures.map((f) => f.replace(/\[.*?\] relics [^:]*/, '[..]'))));
  console.log('battles ' + battles + ', steps ' + steps + ', AI purity checks ' + aiChecks + ', ' + ((Date.now() - t0) / 1000).toFixed(1) + 's');
  console.log(failures.length ? 'FAILURES (' + failures.length + '):\n' + failures.slice(0, 25).join('\n') : 'all invariants held');
  if (uniq.length < failures.length) console.log('distinct: ' + uniq.length);
}
report();
process.exit(failures.length ? 1 : 0);
