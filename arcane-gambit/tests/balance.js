/* Throw random legal armies at encounters and report win rates.
   node tests/balance.js [--act 1] [--id encounterId] [--n 40] [--pool starter,common] [--seed 7]
   Uses up to 4 worker processes. */
'use strict';
const H = require('./harness');
const { fork } = require('child_process');

function parseArgs() {
  const a = process.argv.slice(2);
  const o = { n: 30, act: null, id: null, pool: null, seed: 7, workers: 4, child: false, upg: 0.6 };
  for (let i = 0; i < a.length; i++) {
    const k = a[i];
    if (k === '--n') o.n = +a[++i];
    else if (k === '--act') o.act = +a[++i];
    else if (k === '--id') o.id = a[++i];
    else if (k === '--pool') o.pool = a[++i].split(',');
    else if (k === '--seed') o.seed = +a[++i];
    else if (k === '--workers') o.workers = +a[++i];
    else if (k === '--upg') o.upg = +a[++i];
    else if (k === '--child') o.child = true;
  }
  return o;
}

const POOL_BY_ACT = {
  1: ['starter', 'common'],
  2: ['starter', 'common', 'uncommon'],
  3: ['starter', 'common', 'uncommon', 'rare'],
};

function randomArmy(AG, rng, enc, rarities, upgChance) {
  const ids = AG.playerUnitIds().filter((k) => rarities.indexOf(AG.Units[k].rarity) >= 0);
  let budget = enc.supply;
  const army = [];
  for (let guard = 0; guard < 50 && army.length < enc.slots; guard++) {
    const afford = ids.filter((k) => AG.Units[k].cost <= budget);
    if (!afford.length) break;
    const pick = rng.pick(afford);
    army.push({ def: pick, talents: [], rune: null });
    budget -= AG.Units[pick].cost;
    // Leave some budget for upgrades sometimes.
    if (rng.chance(0.25) && army.length >= 2) break;
  }
  const runes = Object.keys(AG.Runes);
  for (const e of rng.shuffle(army)) {
    if (!rng.chance(upgChance)) continue;
    const tals = AG.talentsFor(e.def).filter((t) => AG.Talents[t].cost <= budget);
    if (tals.length) { const t = rng.pick(tals); e.talents.push(t); budget -= AG.Talents[t].cost; }
    if (rng.chance(0.5)) {
      const rs = runes.filter((r) => AG.Runes[r].cost <= budget);
      if (rs.length) { const r = rng.pick(rs); e.rune = r; budget -= AG.Runes[r].cost; }
    }
  }
  return army;
}

function runJob(job) {
  const AG = H.load();
  const enc = AG.Encounters[job.id];
  const rng = new AG.RNG(job.seed);
  const out = [];
  for (let k = 0; k < job.n; k++) {
    const entries = randomArmy(AG, rng, enc, job.pool, job.upg);
    const army = H.autoPlace(AG, enc, entries);
    const t0 = Date.now();
    let s, err = null;
    try {
      s = AG.B.create(enc, army, { record: false });
      AG.B.runToEnd(s, 4000);
    } catch (e) {
      err = e.stack;
    }
    out.push({
      army: entries.map((e) => e.def + (e.talents.length ? ':' + e.talents.join(',') : '') + (e.rune ? '@' + e.rune : '')).join(' '),
      win: s && s.winner === 0, rounds: s ? s.round : -1, ms: Date.now() - t0, err,
      turns: s ? s.turnCount : 0, over: s ? s.over : false,
    });
  }
  return out;
}

if (process.argv.includes('--child')) {
  process.on('message', (job) => {
    process.send(runJob(job));
  });
} else {
  const o = parseArgs();
  const AG = H.load();
  let encs = AG.encounterList((e) => (o.id ? e.id === o.id : o.act ? e.act === o.act : true));
  const jobs = [];
  for (const e of encs) {
    const pool = o.pool || POOL_BY_ACT[e.act];
    const per = Math.ceil(o.n / o.workers);
    for (let w = 0; w < o.workers; w++) jobs.push({ id: e.id, n: per, pool, seed: o.seed * 1000 + w * 17 + e.id.length, upg: o.upg });
  }
  const results = {};
  let active = 0, next = 0;
  const t0 = Date.now();
  const kids = [];
  function launch() {
    while (active < o.workers && next < jobs.length) {
      const job = jobs[next++];
      const kid = fork(__filename, ['--child']);
      kids.push(kid);
      active++;
      kid.on('message', (res) => {
        (results[job.id] = results[job.id] || []).push(...res);
        kid.kill();
        active--;
        if (next < jobs.length) launch();
        else if (active === 0) report();
      });
      kid.send(job);
    }
  }
  function report() {
    console.log('encounter'.padEnd(22) + 'tier'.padEnd(8) + 'sup/sl  win%   rounds  avg-ms  max-ms  errors');
    for (const e of encs) {
      const r = results[e.id] || [];
      const wins = r.filter((x) => x.win).length;
      const rounds = r.reduce((n, x) => n + x.rounds, 0) / Math.max(1, r.length);
      const ms = r.reduce((n, x) => n + x.ms, 0) / Math.max(1, r.length);
      const mx = r.reduce((n, x) => Math.max(n, x.ms), 0);
      const errs = r.filter((x) => x.err);
      console.log(e.id.padEnd(22) + e.tier.padEnd(8) + (e.supply + '/' + e.slots).padEnd(8) +
        String(Math.round((100 * wins) / Math.max(1, r.length))).padStart(4) + '%  ' +
        rounds.toFixed(1).padStart(6) + '  ' + Math.round(ms).toString().padStart(6) + '  ' + String(mx).padStart(6) + '  ' + errs.length);
      for (const x of errs.slice(0, 2)) console.log('   ERR ' + x.army + '\n' + x.err.split('\n').slice(0, 6).join('\n'));
      if (process.argv.includes('--list')) {
        for (const x of r) console.log('   ' + (x.win ? 'W' : 'L') + ' r' + x.rounds + ' ' + x.army);
      }
    }
    console.log('total ' + ((Date.now() - t0) / 1000).toFixed(1) + 's');
  }
  launch();
}
