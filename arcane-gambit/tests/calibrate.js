/* Replay encounters against realistic collections recorded from simulated
   runs (tests/runsim.js --dump snaps.json), so every fight gets a large
   sample. node tests/calibrate.js snaps.json [--n 40] [--act 2] [--id x] */
'use strict';
const H = require('./harness');
const { fork } = require('child_process');
const fs = require('fs');

function armyFor(AG, rng, snap, enc) {
  const run = { units: snap.units, ranks: snap.ranks, runes: snap.runes, relics: snap.relics };
  const lim = AG.Run.limits(run, enc);
  let budget = lim.supply;
  const out = [];
  const units = rng.shuffle(run.units).sort((a, b) => AG.Units[b].cost - AG.Units[a].cost);
  for (const d of units) {
    if (out.length >= lim.slots) break;
    const reserve = Math.max(0, lim.slots - out.length - 1);
    if (AG.Units[d].cost <= budget - reserve) { out.push({ def: d, talents: [], rune: null }); budget -= AG.Units[d].cost; }
  }
  for (const e of rng.shuffle(out)) {
    const t = AG.talentsFor(e.def).filter((t) => AG.Run.talentCost(run, t) <= budget);
    if (t.length) { const pick = rng.pick(t); e.talents.push(pick); budget -= AG.Run.talentCost(run, pick); }
  }
  const free = AG.Run.runeCounts(run);
  for (const e of out) {
    const r = Object.keys(free).filter((k) => free[k] > 0 && AG.Runes[k].cost <= budget);
    if (r.length) { const k = rng.pick(r); e.rune = k; free[k]--; budget -= AG.Runes[k].cost; }
  }
  return { run, army: H.autoPlace(AG, enc, out) };
}

function job(j) {
  const AG = H.load();
  const snaps = JSON.parse(fs.readFileSync(j.file, 'utf8'));
  const enc = AG.Encounters[j.id];
  const tierOf = (t) => (t === 'early' || t === 'normal' || t === 'event' ? 'battle' : t);
  let pool = snaps.filter((sn) => sn.act === enc.act && tierOf(sn.tier) === tierOf(enc.tier));
  if (enc.tier === 'early') pool = pool.filter((sn) => sn.row <= 1);
  else if (enc.tier === 'normal') pool = pool.filter((sn) => sn.row >= 2);
  if (!pool.length) pool = snaps.filter((sn) => sn.act === enc.act);
  const rng = new AG.RNG(j.seed);
  let wins = 0, n = 0, rounds = 0;
  for (let k = 0; k < j.n; k++) {
    const snap = rng.pick(pool);
    const { run, army } = armyFor(AG, rng, snap, enc);
    const ramp = enc.tier === 'boss' ? 0 : enc.tier === 'early' ? 0.02 : 0.14;
    const s = AG.B.create(enc, AG.Run.armyFor(run, army), { relics: run.relics, ramp, record: false });
    AG.B.runToEnd(s);
    n++; rounds += s.round;
    if (s.winner === 0) wins++;
  }
  return { id: j.id, wins, n, rounds };
}

if (process.argv.includes('--child')) {
  process.on('message', (j) => process.send(job(j)));
} else {
  const a = process.argv.slice(2);
  const file = a[0];
  const get = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
  const n = +get('--n', 40), act = get('--act', null), id = get('--id', null);
  const AG = H.load();
  const encs = AG.encounterList((e) => (id ? e.id === id : act ? e.act === +act : true));
  const jobs = [];
  for (const e of encs) for (let w = 0; w < 2; w++) jobs.push({ file, id: e.id, n: Math.ceil(n / 2), seed: 11 + w * 1000 + e.id.length * 7 });
  const res = {};
  let next = 0, active = 0;
  const target = { early: 85, normal: 78, event: 70, elite: 65, boss: 50 };
  function launch() {
    while (active < 4 && next < jobs.length) {
      const j = jobs[next++];
      active++;
      const kid = fork(__filename, ['--child']);
      kid.on('message', (r) => {
        const t = (res[r.id] = res[r.id] || { wins: 0, n: 0, rounds: 0 });
        t.wins += r.wins; t.n += r.n; t.rounds += r.rounds;
        kid.kill(); active--;
        if (next < jobs.length) launch();
        else if (active === 0) {
          for (const e of encs) {
            const t = res[e.id];
            const pct = Math.round((100 * t.wins) / t.n);
            const tg = target[e.tier];
            const flag = pct > tg + 12 ? '  too easy' : pct < tg - 12 ? '  TOO HARD' : '';
            console.log('A' + e.act + ' ' + e.id.padEnd(18) + e.tier.padEnd(7) + (e.supply + '/' + e.slots).padEnd(6) + ' boost ' + String(e.boost || 0).padEnd(5) + String(pct).padStart(4) + '%  (target ' + tg + ')  rounds ' + (t.rounds / t.n).toFixed(1) + flag);
          }
        }
      });
      kid.send(j);
    }
  }
  launch();
}
