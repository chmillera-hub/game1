/* Replay encounters against realistic collections recorded from simulated
   runs (tests/runsim.js --dump snaps.json), so every fight gets a large
   sample. Each fight is measured as a medium fight halfway up its act (an
   elite on an elite floor, a boss at the top) with Auto-deploy's army (or
   the builders named by --kinds), the baseline every player has.
   --fit searches for the boost (extra enemy health) that brings each fight
   to its target first-try win rate; --write puts those numbers into
   js/data/encounters*.js.
   Elites are best measured against collections from runs that take the
   hard fights (runsim --policy hard), bosses against both kinds of run.
   node tests/calibrate.js snaps.json[,more.json] [--n 40] [--act 2] [--id x,y] [--tiers elite,boss]
                           [--kinds auto,value] [--fit] [--write] */
'use strict';
const H = require('./harness');
const Bot = require('./bot');
const { fork } = require('child_process');
const fs = require('fs');
const path = require('path');

const TARGET = { early: 72, normal: 62, event: 55, elite: 45, boss: 50 };

// The same sample of (collection, builder, seed) for every boost tried.
function samples(AG, snaps, enc, n, seed, kinds) {
  const rng = new AG.RNG(seed);
  let pool = snaps.filter((sn) => sn.act === enc.act);
  if (enc.tier === 'early') pool = pool.filter((sn) => sn.below <= 2);
  if (enc.tier === 'boss') pool = pool.filter((sn) => sn.below >= 4);
  if (enc.tier === 'elite') pool = pool.filter((sn) => sn.below >= 2);
  if (!pool.length) pool = snaps.filter((sn) => sn.act === enc.act);
  const out = [];
  for (let k = 0; k < n; k++) out.push({ snap: rng.pick(pool), kind: kinds[k % kinds.length], seed: seed * 31 + k });
  return out;
}

function winRate(AG, enc, list, boost) {
  const saved = enc.boost;
  enc.boost = boost;
  let wins = 0, rounds = 0;
  for (const sm of list) {
    const sn = sm.snap;
    const run = { units: sn.units, ranks: sn.ranks, runes: sn.runes, relics: sn.relics, supplyBonus: sn.supplyBonus || 0 };
    const army = Bot.armyFor(AG, run, enc, sm.kind, new AG.RNG(sm.seed));
    const ramp = enc.tier === 'boss' || enc.tier === 'event' ? 0 : sn.below * 0.04;
    const s = AG.B.create(enc, AG.Run.armyFor(run, army), { relics: run.relics, ramp, record: false });
    AG.B.runToEnd(s);
    rounds += s.round;
    if (s.winner === 0) wins++;
  }
  enc.boost = saved;
  return { pct: (100 * wins) / list.length, rounds: rounds / list.length };
}

function job(j) {
  const AG = H.load();
  const snaps = [].concat(...j.file.split(',').map((f) => JSON.parse(fs.readFileSync(f, 'utf8'))));
  const enc = AG.Encounters[j.id];
  const list = samples(AG, snaps, enc, j.n, j.seed, j.kinds);
  const base = winRate(AG, enc, list, enc.boost || 0);
  if (!j.fit) return { id: j.id, pct: base.pct, rounds: base.rounds };
  // Win rate falls as the boost rises: bisect for the target.
  const target = TARGET[enc.tier];
  let lo = -0.6, hi = 1.6, best = { boost: enc.boost || 0, pct: base.pct };
  for (let it = 0; it < 7; it++) {
    const mid = Math.round(((lo + hi) / 2) * 100) / 100;
    const r = winRate(AG, enc, list, mid);
    if (Math.abs(r.pct - target) < Math.abs(best.pct - target)) best = { boost: mid, pct: r.pct };
    if (r.pct > target) lo = mid; else hi = mid;
  }
  return { id: j.id, pct: base.pct, rounds: base.rounds, fit: best };
}

function writeBoosts(fits) {
  for (const f of ['encounters.js', 'encounters2.js']) {
    const p = path.join(__dirname, '..', 'js', 'data', f);
    let src = fs.readFileSync(p, 'utf8');
    for (const id of Object.keys(fits)) {
      const re = new RegExp("(id: '" + id + "',[^]*?supply: \\d+)(, boost: -?[\\d.]+)?");
      const b = Math.round(fits[id] * 100) / 100;
      src = src.replace(re, (m, head) => head + (b ? ', boost: ' + b : ''));
    }
    fs.writeFileSync(p, src);
  }
}

if (process.argv.includes('--child')) {
  process.on('message', (j) => process.send(job(j)));
} else {
  const a = process.argv.slice(2);
  const file = a[0];
  const get = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
  const n = +get('--n', 40), act = get('--act', null), id = get('--id', null), tiers = get('--tiers', null);
  const fit = a.includes('--fit'), write = a.includes('--write');
  const kinds = get('--kinds', 'auto').split(',');
  const AG = H.load();
  const encs = AG.encounterList((e) => TARGET[e.tier] != null && (!tiers || tiers.split(',').indexOf(e.tier) >= 0) &&
    (id ? id.split(',').indexOf(e.id) >= 0 : act ? e.act === +act : true));
  const jobs = encs.map((e) => ({ file, id: e.id, n, seed: 11 + e.id.length * 7, fit, kinds }));
  const res = {};
  let next = 0, active = 0;
  function launch() {
    while (active < 4 && next < jobs.length) {
      const j = jobs[next++];
      active++;
      const kid = fork(__filename, ['--child']);
      kid.on('message', (r) => {
        res[r.id] = r;
        kid.kill();
        active--;
        if (next < jobs.length) launch();
        else if (active === 0) done();
      });
      kid.send(j);
    }
  }
  function done() {
    const fits = {};
    for (const e of encs) {
      const r = res[e.id];
      const tg = TARGET[e.tier];
      const pct = Math.round(r.pct);
      const flag = pct > tg + 12 ? '  too easy' : pct < tg - 12 ? '  TOO HARD' : '';
      let line = 'A' + e.act + ' ' + e.id.padEnd(18) + e.tier.padEnd(7) + String(e.supply).padEnd(4) + ' boost ' + String(e.boost || 0).padEnd(5) + String(pct).padStart(4) + '%  (target ' + tg + ')  rounds ' + r.rounds.toFixed(1) + flag;
      if (r.fit) { line += '   fit: boost ' + r.fit.boost + ' -> ' + Math.round(r.fit.pct) + '%'; fits[e.id] = r.fit.boost; }
      console.log(line);
    }
    if (write && Object.keys(fits).length) { writeBoosts(fits); console.log('wrote ' + Object.keys(fits).length + ' boosts'); }
  }
  launch();
}
