/* Play whole runs with a simple bot (greedy army, random upgrades, auto
   placement, random map choices) to calibrate difficulty.
   node tests/runsim.js [--runs 16] [--seed 1] [--mode standard|casual] [--verbose] */
'use strict';
const H = require('./harness');
const { fork } = require('child_process');

function botRun(seed, mode, verbose) {
  const AG = H.load();
  global.localStorage = global.localStorage || { _d: {}, getItem(k) { return this._d[k] || null; }, setItem(k, v) { this._d[k] = String(v); }, removeItem(k) { delete this._d[k]; } };
  const log = verbose ? console.log : () => {};
  const run = AG.Run.newRun({ seed, mode });
  const rng = new AG.RNG(seed * 7 + 3);
  const losses = [];
  const fights = [];
  const snaps = [];
  function army(enc) {
    const lim = AG.Run.limits(run, enc);
    let budget = lim.supply;
    const out = [];
    const units = rng.shuffle(run.units).sort((a, b) => AG.Units[b].cost - AG.Units[a].cost);
    // Mix: one or two big pieces, then fill.
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
    return H.autoPlace(AG, enc, out);
  }
  for (let guard = 0; guard < 600; guard++) {
    const sc = run.screen;
    if (sc === 'boon') { AG.Run.takeBoon(run, rng.pick(['recruit', 'ledger', 'armory', 'veteran']), 'knight'); continue; }
    if (sc === 'actIntro') { run.screen = 'map'; continue; }
    if (sc === 'map') { AG.Run.enter(run, rng.pick(AG.Run.reachable(run))); continue; }
    if (sc === 'setup') {
      const enc = AG.Encounters[run.battle.enc];
      if (run.battle.attempts === 0) {
        snaps.push({ act: run.act, tier: enc.tier, row: run.map.nodes[run.pos] ? run.map.nodes[run.pos].r : 0,
          units: run.units.slice(), ranks: Object.assign({}, run.ranks), runes: run.runes.slice(), relics: run.relics.slice() });
      }
      const a = army(enc);
      const s = AG.B.create(enc, AG.Run.armyFor(run, a), Object.assign({ record: true }, AG.Run.battleOpts(run)));
      AG.B.runToEnd(s);
      fights.push({ id: enc.id, tier: run.battle.tier, win: s.winner === 0, act: run.act });
      if (s.winner === 0) { AG.Run.battleWon(run, s); log('W ' + enc.id); }
      else { const d = AG.Run.battleLost(run, s); losses.push(enc.id); log('L ' + enc.id + ' -' + d + ' -> ' + run.resolve); }
      continue;
    }
    if (sc === 'reward') {
      const p = run.pending;
      if (p.offers.length) AG.Run.claimOffer(run, rng.int(0, p.offers.length - 1));
      if (p.relicChoices && p.relicChoices.length) AG.Run.claimRelic(run, rng.pick(p.relicChoices));
      AG.Run.finishReward(run);
      continue;
    }
    if (sc === 'event') {
      if (run.event.result) { run.screen = 'map'; continue; }
      const ev = AG.eventById(run.event.id);
      const choices = ev.choices.map((c, i) => [c, i]).filter(([c]) => AG.Run.choiceAvailable(run, c) === true);
      const [c, i] = rng.pick(choices);
      let picked = null;
      if (c.pick === 'trainable') picked = rng.pick(AG.Run.trainable(run));
      if (c.pick === 'rune') picked = run.runes[0];
      AG.Run.resolveEvent(run, i, picked);
      if (run.screen === 'event') run.screen = 'map';
      continue;
    }
    if (sc === 'shop') {
      const s = run.shop;
      s.units.forEach((u, i) => { if (rng.chance(0.6)) AG.Run.buy(run, 'units', i); });
      s.runes.forEach((u, i) => { if (rng.chance(0.4)) AG.Run.buy(run, 'runes', i); });
      if (run.resolve < 25) AG.Run.buy(run, 'heal');
      run.screen = 'map';
      continue;
    }
    if (sc === 'rest') {
      const t = AG.Run.trainable(run);
      AG.Run.rest(run, run.resolve < run.maxResolve * 0.6 || !t.length ? 'recover' : 'train', rng.pick(t));
      run.screen = 'map';
      continue;
    }
    if (sc === 'gameover' || sc === 'victory') break;
  }
  return { seed, result: run.screen, act: run.act, floor: run.floor, resolve: run.resolve, losses, fights, snaps, relics: run.relics.length, units: run.units.length };
}

module.exports = { botRun };
if (require.main !== module) {
  // imported
} else if (process.argv.includes("--child")) {
  process.on('message', (job) => process.send(job.seeds.map((sd) => botRun(sd, job.mode, false))));
} else {
  const a = process.argv.slice(2);
  const get = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
  const runs = +get('--runs', 16), seed0 = +get('--seed', 1), mode = get('--mode', 'standard');
  if (a.includes('--verbose')) { console.log(botRun(seed0, mode, true)); process.exit(0); }
  const seeds = [...Array(runs)].map((_, i) => seed0 + i * 101);
  const W = 4, chunks = [...Array(W)].map((_, w) => seeds.filter((_, i) => i % W === w));
  let done = 0; const all = [];
  for (const ch of chunks) {
    const kid = fork(__filename, ['--child']);
    kid.on('message', (res) => {
      all.push(...res); kid.kill();
      if (++done === W) {
        const wins = all.filter((r) => r.result === 'victory').length;
        console.log('runs ' + all.length + '  victories ' + wins + ' (' + Math.round((100 * wins) / all.length) + '%)');
        const dump = get('--dump', null);
        if (dump) require('fs').writeFileSync(dump, JSON.stringify(all.flatMap((r) => r.snaps)));
        const byAct = { 1: 0, 2: 0, 3: 0 };
        for (const r of all) if (r.result !== 'victory') byAct[r.act]++;
        console.log('died in act: ' + JSON.stringify(byAct));
        const fights = all.flatMap((r) => r.fights);
        const tiers = {};
        for (const f of fights) { const k = 'A' + f.act + ' ' + f.tier; const t = (tiers[k] = tiers[k] || { n: 0, w: 0 }); t.n++; if (f.win) t.w++; }
        for (const k of Object.keys(tiers).sort()) console.log('  ' + k.padEnd(12) + ' fights ' + String(tiers[k].n).padStart(4) + '  first-try-or-retry win ' + Math.round((100 * tiers[k].w) / tiers[k].n) + '%');
        const lossBy = {};
        for (const r of all) for (const l of r.losses) lossBy[l] = (lossBy[l] || 0) + 1;
        console.log('losses by encounter: ' + JSON.stringify(Object.entries(lossBy).sort((x, y) => y[1] - x[1])));
        console.log('avg losses per run: ' + (all.reduce((n, r) => n + r.losses.length, 0) / all.length).toFixed(2));
        const byEnc = {};
        for (const f of fights) { const t = (byEnc[f.id] = byEnc[f.id] || { n: 0, w: 0, tier: f.tier, act: f.act }); t.n++; if (f.win) t.w++; }
        const rows = Object.entries(byEnc).sort((x, y) => x[1].act - y[1].act || x[0].localeCompare(y[0]));
        console.log(rows.map(([k, t]) => '  A' + t.act + ' ' + k.padEnd(18) + t.tier.padEnd(7) + String(t.n).padStart(4) + ' fights ' + String(Math.round((100 * t.w) / t.n)).padStart(4) + '%').join('\n'));
      }
    });
    kid.send({ seeds: ch, mode });
  }
}
