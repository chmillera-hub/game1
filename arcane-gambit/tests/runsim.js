/* Play whole runs with a bot to calibrate difficulty: a random draft and
   opening, then up each tower choosing fights by policy. Each fight is tried
   with a few army builders (tests/bot.js); when all of them lose, the bot
   goes back down and takes an easier fight, and a run is stuck only when
   even the easy fight (or the boss) cannot be won. After the last boss it
   tries the mega boss and climbs the Hall of Fame.
   node tests/runsim.js [--runs 16] [--seed 1] [--policy medium|random|hard|easy]
                        [--tries 4] [--verbose] [--dump snaps.json] */
'use strict';
const H = require('./harness');
const Bot = require('./bot');
const { fork } = require('child_process');

const EASIER = { elite: 'medium', hard: 'medium', medium: 'easy', easy: null };

function botRun(seed, opts) {
  const AG = H.load();
  const Run = AG.Run;
  global.localStorage = global.localStorage || { _d: {}, getItem(k) { return this._d[k] || null; }, setItem(k, v) { this._d[k] = String(v); }, removeItem(k) { delete this._d[k]; } };
  const log = opts.verbose ? console.log : () => {};
  const tries = opts.tries || 4;
  const run = Run.newRun({ seed });
  const rng = new AG.RNG(seed * 7 + 3);
  const fights = [];
  const snaps = [];
  let stuck = null, mega = null;

  // Fight the current battle with up to n army builders. True on a win.
  function fight(n, label) {
    const enc = AG.Encounters[run.battle.enc];
    for (let k = 0; k < n; k++) {
      const kind = Bot.KINDS[k % Bot.KINDS.length];
      const army = Bot.armyFor(AG, run, enc, kind, rng);
      if (!army.length) break;
      const tier = run.battle.tier;
      run.battle.formation = army;
      const s = AG.B.create(enc, Run.armyFor(run, army), Object.assign({ record: true }, Run.battleOpts(run)));
      AG.B.runToEnd(s);
      const win = s.winner === 0;
      fights.push({ act: run.act, floor: run.floor, tier, id: enc.id, attempt: k, kind, win, units: army.length });
      log((win ? 'W ' : 'L ') + label + ' ' + enc.id + ' (' + tier + ', ' + kind + ', ' + army.length + ' units)');
      if (win) { Run.battleWon(run, s); return true; }
      Run.battleLost(run, s);
    }
    return false;
  }
  function chooseDiff(options) {
    const avail = options.filter((o) => o.enc).map((o) => o.diff);
    if (opts.policy === 'random') return rng.pick(avail);
    if (opts.policy === 'hard') return avail[2];
    if (opts.policy === 'easy') return avail[0];
    return avail[1] || avail[0];
  }

  for (let guard = 0; guard < 400 && !stuck; guard++) {
    const sc = run.screen;
    // A random answer to whatever an event choice (or service) asks for.
    const pickFor = (c) => {
      if (c.pick === 'trainable') return rng.pick(Run.trainable(run));
      if (c.pick === 'rune') return run.runes[0];
      if (c.pick === 'unit') return rng.pick(run.units.filter((d) => !c.filter || c.filter(run, d)));
      if (c.pick === 'talent') { const def = rng.pick(run.units.filter((d) => Run.learnable(run, d).length)); return def ? { def, talent: rng.pick(Run.learnable(run, def)) } : null; }
      if (c.pick === 'fuse') { const from = rng.pick(run.units); return { from, into: rng.pick(run.units.filter((d) => d !== from)) }; }
      return null;
    };
    if (sc === 'draft') {
      // Mostly the priciest of the three, as a player chasing power would.
      const o = run.draft.options;
      Run.draftPick(run, rng.chance(0.5) ? o.slice().sort((a, b) => AG.Units[b].cost - AG.Units[a].cost)[0] : rng.pick(o));
    } else if (sc === 'boon') {
      Run.takeBoon(run, rng.pick(run.boons), rng.pick(Run.trainable(run)));
    } else if (sc === 'actIntro') {
      run.screen = 'tower';
    } else if (sc === 'tower') {
      const f = Run.currentFloor(run);
      if (f.type !== 'battle') { Run.enterFloor(run); continue; }
      snaps.push({ act: run.act, floor: run.floor, below: Run.battlesBelow(run), units: run.units.slice(), ranks: Object.assign({}, run.ranks), runes: run.runes.slice(), relics: run.relics.slice(), supplyBonus: run.supplyBonus });
      let diff = chooseDiff(f.options);
      for (;;) {
        Run.chooseFight(run, f.options.findIndex((o) => o.diff === diff));
        if (fight(tries, 'A' + run.act + 'F' + (run.floor + 1))) break;
        Run.backToTower(run);
        diff = EASIER[diff === 'elite' ? 'hard' : diff];
        if (!diff) { stuck = { act: run.act, floor: run.floor }; break; }
      }
    } else if (sc === 'setup') {
      // Boss or event fights (tower fights are fought from the tower).
      const tier = run.battle.tier;
      if (!fight(tier === 'boss' ? tries * 2 : tries, tier)) {
        if (tier === 'boss') stuck = { act: run.act, floor: run.floor, boss: true };
        else Run.leaveFight(run);
      }
    } else if (sc === 'reward') {
      const p = run.pending;
      if (p.offers.length) Run.claimOffer(run, rng.int(0, p.offers.length - 1));
      if (p.relicChoices && p.relicChoices.length) Run.claimRelic(run, rng.pick(p.relicChoices));
      Run.finishReward(run);
    } else if (sc === 'event') {
      if (run.event.result) { Run.advance(run); continue; }
      const ev = AG.eventById(run.event.id);
      const choices = ev.choices.map((c, i) => [c, i]).filter(([c]) => Run.choiceAvailable(run, c) === true);
      const [c, i] = rng.pick(choices);
      Run.resolveEvent(run, i, pickFor(c));
    } else if (sc === 'shop') {
      const s = run.shop;
      if (rng.chance(0.3)) Run.refreshShop(run);
      s.items.forEach((it, i) => {
        if (!rng.chance(it.kind === 'rune' ? 0.4 : 0.5)) return;
        Run.buy(run, i, it.kind === 'train' ? rng.pick(Run.trainable(run)) : it.kind === 'lesson' ? pickFor({ pick: 'talent' }) : null);
      });
      Run.advance(run);
    } else if (sc === 'victory') {
      if (!mega) {
        // The collection that faces the mega boss (act 4 in the dump).
        snaps.push({ act: 4, floor: 0, below: 0, units: run.units.slice(), ranks: Object.assign({}, run.ranks), runes: run.runes.slice(), relics: run.relics.slice(), supplyBonus: run.supplyBonus });
        Run.startMega(run);
        mega = { win: fight(Bot.KINDS.length, 'MEGA') };
        if (!mega.win) Run.leaveFight(run);
        continue;
      }
      Run.startClimb(run);
    } else if (sc === 'climb') {
      while (!run.climb.placed) {
        const o = Run.climbOpponent(run);
        if (!o) { Run.finishClimb(run); break; }
        Run.climbResult(run, Run.duelWinner(run.finalArmy, o));
      }
      break;
    } else break;
  }
  return {
    seed, result: run.climb && run.climb.placed ? 'victory' : run.screen, stuck, act: run.act, floor: run.floor, fights, snaps,
    relics: run.relics.length, units: run.units.length, gold: run.gold, mega: mega && mega.win, rank: run.climb ? run.climb.rank : null,
  };
}

function report(all) {
  const pct = (a, b) => (b ? Math.round((100 * a) / b) + '%' : '-');
  const wins = all.filter((r) => r.result === 'victory').length;
  console.log('runs ' + all.length + '  finished ' + wins + ' (' + pct(wins, all.length) + ')  mega wins ' + all.filter((r) => r.mega).length);
  const stuckAt = {};
  for (const r of all) if (r.stuck) { const k = 'A' + r.stuck.act + 'F' + (r.stuck.floor + 1) + (r.stuck.boss ? ' boss' : ''); stuckAt[k] = (stuckAt[k] || 0) + 1; }
  console.log('stuck at: ' + JSON.stringify(stuckAt));
  const fights = all.flatMap((r) => r.fights);
  const by = {};
  for (const f of fights) {
    const k = 'A' + f.act + ' ' + f.tier;
    const t = (by[k] = by[k] || { first: 0, firstWin: 0, n: 0, w: 0, units: 0 });
    t.n++; t.units += f.units;
    if (f.win) t.w++;
    if (f.attempt === 0) { t.first++; if (f.win) t.firstWin++; }
  }
  for (const k of Object.keys(by).sort()) {
    const t = by[k];
    console.log('  ' + k.padEnd(12) + ' first try ' + pct(t.firstWin, t.first).padStart(4) + ' of ' + String(t.first).padStart(3) + '   any attempt ' + pct(t.w, t.n).padStart(4) + ' of ' + String(t.n).padStart(4) + '   avg units ' + (t.units / t.n).toFixed(1));
  }
  const kinds = {};
  for (const f of fights) { const t = (kinds[f.kind] = kinds[f.kind] || { n: 0, w: 0 }); t.n++; if (f.win) t.w++; }
  console.log('by army builder: ' + Object.keys(kinds).map((k) => k + ' ' + pct(kinds[k].w, kinds[k].n)).join(', '));
  const byEnc = {};
  for (const f of fights) {
    if (f.attempt !== 0) continue;
    const t = (byEnc[f.id] = byEnc[f.id] || { n: 0, w: 0, act: f.act, tiers: {} });
    t.n++; if (f.win) t.w++;
    t.tiers[f.tier] = (t.tiers[f.tier] || 0) + 1;
  }
  const rows = Object.entries(byEnc).sort((x, y) => x[1].act - y[1].act || x[0].localeCompare(y[0]));
  console.log('first-try wins by encounter:');
  console.log(rows.map(([k, t]) => '  A' + t.act + ' ' + k.padEnd(18) + String(t.n).padStart(4) + ' ' + pct(t.w, t.n).padStart(5) + '  ' + JSON.stringify(t.tiers)).join('\n'));
  const avg = (f) => (all.reduce((n, r) => n + f(r), 0) / all.length).toFixed(1);
  console.log('avg at the end: ' + avg((r) => r.units) + ' unit types, ' + avg((r) => r.relics) + ' relics, ' + avg((r) => r.gold) + ' gold');
}

module.exports = { botRun };
if (require.main !== module) {
  // imported
} else if (process.argv.includes('--child')) {
  process.on('message', (job) => process.send(job.seeds.map((sd) => botRun(sd, job.opts))));
} else {
  const a = process.argv.slice(2);
  const get = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
  const runs = +get('--runs', 16), seed0 = +get('--seed', 1);
  const opts = { policy: get('--policy', 'medium'), tries: +get('--tries', 4), verbose: a.includes('--verbose') };
  if (opts.verbose) {
    const r = botRun(seed0, opts);
    delete r.snaps;
    delete r.fights;
    console.log(r);
    process.exit(0);
  }
  const seeds = [...Array(runs)].map((_, i) => seed0 + i * 101);
  const W = Math.min(4, runs), chunks = [...Array(W)].map((_, w) => seeds.filter((_, i) => i % W === w));
  let done = 0;
  const all = [];
  for (const ch of chunks) {
    const kid = fork(__filename, ['--child']);
    kid.on('message', (res) => {
      all.push(...res);
      kid.kill();
      if (++done === W) {
        report(all);
        const dump = get('--dump', null);
        if (dump) require('fs').writeFileSync(dump, JSON.stringify(all.flatMap((r) => r.snaps)));
      }
    });
    kid.send({ seeds: ch, opts });
  }
}
