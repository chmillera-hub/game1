// Plays whole campaigns with the AI on both sides. Losses are retried, as in the game.
// Run: node tests/run.test.js [runs] [policy] [maxTries]
// policy, which challenge to pick each round: medium (default: medium, easy after a loss),
// easy, elite (elite, then medium, then easy after losses) or mix (mostly medium, some easy
// and elite). MEGA=1 also tries the optional final challenge.
const assert = require('assert');
const AG = require('./load')();
const R = AG.Run;
const E = AG.Engine;
const D = AG.Data;
const N = +process.argv[2] || 12;
const POLICY = process.argv[3] || 'medium';
const TIER_ORDER = ['elite', 'medium', 'easy'];
const MAX_TRIES = +process.argv[4] || 6;
const OVERTIME = R.OVERTIME;

function checkLoadouts(run) {
  const seen = new Set();
  for (const r of run.roster) {
    R.normalizeLoad(run, r);
    for (const uid of r.load.skills.concat(r.load.gear)) {
      assert.ok(!seen.has(uid), 'an item is slotted in two units');
      seen.add(uid);
      assert.ok(R.itemByUid(run, uid), 'slotted item exists');
    }
  }
}

function playBattle(run) {
  const p = run.pending;
  const dep = R.autoDeploy(run, p.attempt || 0);
  assert.ok(dep.length > 0, 'deployment possible');
  assert.ok(R.supplyUsed(run, dep) <= R.supplyFor(run), 'within Supply');
  const star = R.bonusUnit(run, p.enc);
  if (star) assert.ok(dep.some((d) => d.rid === star.id), 'Auto fields the unit a bonus goal asks for');
  const rows = R.deployRows(run, p.enc);
  for (const d of dep) assert.ok(rows.includes(d.y) && R.deployOpen(p.enc, d.x, d.y), 'valid deploy tile');
  checkLoadouts(run);
  for (const w of p.enc.waves || []) {
    assert.ok(w.units.length > 0, 'a wave brings someone');
    if (w.from) assert.ok(p.enc.units.some((u) => u.key === w.from && D.UNITS[u.type].traits.includes('spawner')), 'wave source is a spawner');
    else assert.ok(w.tiles && w.tiles.length, 'edge wave has tiles');
  }
  const s = E.createBattle(R.battleConfig(run, dep));
  let guard = 0;
  while (!s.over && guard++ < 4000) {
    AG.AI.playTurn(s, s.side, { stance: s.side === 'E' ? p.enc.stance : 'balanced', temp: 0.6 });
    for (const e of s.events) {
      const k = e.t === 'dunk' ? (e.lava ? 'lava' : 'water') : e.t === 'push' && e.pull ? null : ['crash', 'slam', 'climb'].includes(e.t) ? e.t : null;
      if (k) results.shoves[k] = (results.shoves[k] || 0) + 1;
      if (e.t === 'push') results.shoves[e.pull ? 'pulled tiles' : 'shoved tiles'] = (results.shoves[e.pull ? 'pulled tiles' : 'shoved tiles'] || 0) + 1;
    }
    s.events.length = 0;
  }
  assert.ok(s.over, 'battle ended');
  if (s.winner === 'P') {
    // Goal results come in the order of the encounter's bonus goals.
    for (const [i, g] of R.goalResults(run, s, dep).entries()) {
      const type = p.enc.bonus[i].type;
      const k = (results.bonus[type] = results.bonus[type] || [0, 0]);
      k[1]++;
      if (g.done) k[0]++;
    }
  }
  for (const b of p.enc.bonus || []) {
    if (b.type !== 'loot') continue;
    const k = (results.loot[b.kind] = results.loot[b.kind] || [0, 0]);
    k[1]++;
    if (s.winner === 'P' && s.loot.some((l) => l.id === b.lootId && l.taken)) k[0]++;
  }
  const len = (results.lens[p.enc.primary] = results.lens[p.enc.primary] || []);
  len.push(s.turn);
  if (s.inOvertime) {
    results.overtime[s.winner]++;
    const k = (results.otKinds[p.enc.kind] = results.otKinds[p.enc.kind] || [0, 0]);
    k[1]++;
    if (s.winner === 'P') k[0]++;
  }
  if (s.timeout) {
    results.timeouts++;
    if (process.env.VERBOSE) console.log(`  TIMEOUT ${p.enc.name} (${p.enc.primary}) winner ${s.winner}: E left ${s.units.filter((u) => u.alive && u.team === 'E' && !u.nonCombat).map((u) => u.type).join(' ')} | P left ${s.units.filter((u) => u.alive && u.team === 'P').map((u) => u.type).join(' ')}`);
  }
  if (s.winner === 'P') {
    const k = (results.coins[p.enc.primary] = results.coins[p.enc.primary] || [0, 0]);
    k[0] += s.stats.bounty || 0;
    k[1]++;
  }
  // The Act I boss's wreckage: how much of it a winning army salvages before it tires.
  const wrecks = s.units.filter((u) => u.type === 'wreckage');
  if (wrecks.length && s.winner === 'P') {
    results.wreck[0] += wrecks.filter((u) => !u.alive).length;
    results.wreck[1] += wrecks.length;
    results.wreck[2]++;
    results.wreck[3] += s.units.filter((u) => u.team === 'P' && !u.nonCombat && !u.alive).length - (s.cleanup ? s.cleanup.lost : 0);
  }
  if (s.cleanup && s.winner === 'P') results.cleanups.push(s.turn - s.cleanup.turn);
  const swift = (p.enc.bonus || []).find((b) => b.type === 'swift');
  if (swift && s.winner === 'P') {
    results.swift[1]++;
    if (s.turn <= swift.turns) results.swift[0]++;
  }
  return R.finishBattle(run, s, dep);
}

function pickUnit(run, pick) {
  const ok = run.roster.filter((u) => R.eventPickOk(run, pick, u));
  return ok.length ? ok[0].id : null;
}

const results = { done: 0, stuck: 0, battles: 0, tries: 0, first: { 1: [0, 0], 2: [0, 0], 3: [0, 0] }, kinds: {}, missions: {}, lv: [], walls: [], lens: {}, timeouts: 0, swift: [0, 0], overtime: { P: 0, E: 0 }, otKinds: {}, loot: {}, bonus: {}, tiers: {}, mega: [0, 0], coins: {}, shoves: {}, armies: [], wreck: [0, 0, 0, 0], cleanups: [] };

// The tier a player of this policy picks first in a round.
function firstTier(rng) {
  if (POLICY === 'easy' || POLICY === 'elite') return POLICY;
  if (POLICY === 'mix') return rng.weighted([['medium', 70], ['easy', 15], ['elite', 15]]);
  return 'medium';
}
const t0 = Date.now();
for (let i = 0; i < N; i++) {
  // DRAFT=1: draft each army, picking at random as a player might, instead of a warband.
  let run;
  if (process.env.DRAFT) {
    const pick = AG.derive(9000 + i, 'sim-draft');
    const picks = [];
    for (let s = 0; s < R.DRAFT_STEPS.length; s++) picks.push(pick.pick(R.draftOffer(9000 + i, s, picks).options));
    run = R.newRun({ seed: (+process.env.SEED0 || 9000) + i, draft: { units: picks.slice(0, 5), relic: picks[5], items: [['skill', picks[6]], ['gear', picks[7]]] } });
  } else run = R.newRun({ seed: (+process.env.SEED0 || 9000) + i, warband: D.WARBANDS[i % D.WARBANDS.length].id });
  const rng = new AG.RNG(i + 1);
  let steps = 0;
  let stuck = false;
  while (!run.over && steps++ < 500 && !stuck) {
    if (!run.pending) {
      // A round of challenges (or the boss, or the final challenge): pick one, and after a
      // loss pick again, a tier easier, up to MAX_TRIES tries in all.
      const offer = run.offer;
      assert.ok(offer && offer.length, 'a challenge on offer');
      const act = run.act;
      let tier = offer.length === 1 ? offer[0].tier : firstTier(rng);
      let res;
      let tries = 0;
      let firstKind = null;
      let enc = null;
      do {
        const idx = offer.findIndex((o) => o.tier === tier);
        assert.ok(R.chooseChallenge(run, idx), 'challenge taken');
        enc = run.pending.enc;
        if (!firstKind) firstKind = enc.kind + (offer.length === 1 ? '' : '/' + tier);
        res = playBattle(run);
        tries++;
        if (!res.won) {
          R.backToChoice(run);
          const t = TIER_ORDER.indexOf(tier);
          if (offer.length > 1 && t < TIER_ORDER.length - 1) tier = TIER_ORDER[t + 1];
        }
      } while (!res.won && tries < MAX_TRIES);
      const isMega = offer[0].tier === 'mega';
      if (isMega) {
        results.mega[1]++;
        if (res.won) results.mega[0]++;
        else R.endRun(run);
        continue;
      }
      results.battles++;
      results.tries += tries;
      results.first[act][1]++;
      if (tries === 1) results.first[act][0]++;
      const k = (results.kinds[firstKind + act] = results.kinds[firstKind + act] || [0, 0]);
      k[1]++;
      if (tries === 1) k[0]++;
      const tk = (results.tiers[tier] = results.tiers[tier] || [0, 0]);
      tk[1]++;
      if (res.won) tk[0]++;
      const m = (results.missions[enc.primary] = results.missions[enc.primary] || [0, 0]);
      m[1]++;
      if (tries === 1) m[0]++;
      if (!res.won) {
        stuck = true;
        results.walls.push(`${run.warband} act ${act} ${firstKind} ${enc.name}`);
      }
      continue;
    }
    const p = run.pending;
    if (p.type === 'summit') {
      if (process.env.MEGA) R.faceFinal(run);
      else R.endRun(run);
      continue;
    }
    if (p.type === 'battle') {
      // A battle an event started: retried as it is.
      let res;
      let tries = 0;
      do {
        res = playBattle(run);
        tries++;
      } while (!res.won && tries < MAX_TRIES);
      if (!res.won) stuck = true;
      continue;
    }
    if (p.type === 'reward') {
      if (p.bossRelics && !p.bossRelicTaken) R.takeBossRelic(run, p.bossRelics[0]);
      if (p.tome && !p.tomeTaken) R.takeTome(run, 0);
      const idx = rng.int(p.spoils.length);
      if (!R.takeSpoil(run, idx)) R.skipSpoils(run);
      for (const sc of run.items.filter((it) => it.kind === 'scroll')) {
        const r = run.roster.find((u) => !u.enchant && D.eligible(u.type, D.ENCHANTS[sc.id]));
        if (r) assert.ok(R.applyScroll(run, sc.uid, r.id));
      }
      R.completeNode(run);
      continue;
    }
    if (p.type === 'shop') {
      for (let k = 0; k < p.stock.length; k++) if (R.canBuy(run, p.stock[k]) && rng.chance(0.5)) R.buy(run, k);
      R.completeNode(run);
      continue;
    }
    if (p.type === 'event') {
      const choices = R.eventChoices(run).filter((c) => c.enabled);
      const c = rng.pick(choices);
      const rid = c.pick ? pickUnit(run, c.pick) : null;
      let res = R.chooseEvent(run, c.id, rid);
      if (res == null) res = R.chooseEvent(run, choices[choices.length - 1].id, null);
      assert.ok(res != null, 'event resolved');
      if (run.pending.type === 'event') R.completeNode(run);
      continue;
    }
    throw new Error('unknown pending ' + p.type);
  }
  JSON.parse(JSON.stringify(run));
  if (run.won) results.done++;
  else results.stuck++;
  if (run.won && run.finalArmy) results.armies.push({ name: `${run.warband} ${i}`, level: R.commanderLevel(run), relics: run.relics.slice(), units: run.finalArmy });
  results.lv.push(R.commanderLevel(run));
  console.log(
    `run ${i} ${run.warband.padEnd(8)} ${run.won ? 'WON  ' : 'STUCK'} act ${run.act} lv ${R.commanderLevel(run)} xp ${run.xp} supply ${R.supplyFor(run)} army ${R.armySize(run)} roster=${run.roster.length} items=${run.items.length} relics=${run.relics.length} gold=${run.gold} battles=${run.stats.battles} losses=${run.stats.losses}`
  );
}
const pct = ([a, b]) => (b ? Math.round((100 * a) / b) + '%' : '-');
console.log(`campaigns: won ${results.done}, stuck ${results.stuck} (more than ${MAX_TRIES} tries) · battles ${results.battles}, avg tries ${(results.tries / Math.max(1, results.battles)).toFixed(2)}`);
console.log(`first-try wins: act1 ${pct(results.first[1])} act2 ${pct(results.first[2])} act3 ${pct(results.first[3])} · policy ${POLICY}`);
console.log('won with (the tier that finally won each round):', Object.entries(results.tiers).map(([k, v]) => `${k} ${v[0]}/${v[1]}`).join(' · '));
if (results.mega[1]) console.log(`final challenge: won ${results.mega[0]} of ${results.mega[1]} tries`);
console.log('by kind:', Object.entries(results.kinds).map(([k, v]) => `${k} ${pct(v)} (${v[1]})`).join(' · '));
console.log('by mission:', Object.entries(results.missions).map(([k, v]) => `${k} ${pct(v)} (${v[1]})`).join(' · '));
const q = (list, f) => list.slice().sort((a, b) => a - b)[Math.min(list.length - 1, Math.floor(list.length * f))];
console.log(
  `battle length in turns (p25/median/p75), ${results.timeouts} timeouts:`,
  Object.entries(results.lens).map(([k, v]) => `${k} ${q(v, 0.25)}/${q(v, 0.5)}/${q(v, 0.75)}`).join(' · ')
);
const otLens = Object.values(results.lens).flat().filter((n) => n > OVERTIME);
console.log(`fatigue: ${results.overtime.P + results.overtime.E} battles reached it (you won ${results.overtime.P}), lasting ${otLens.length ? `${q(otLens, 0.5) - OVERTIME} turns (median), ${Math.max(...otLens) - OVERTIME} at most` : '-'} · ${Object.entries(results.otKinds).map(([k, v]) => `${k} ${v[0]}/${v[1]}`).join(' · ')}`);
console.log(`fast-win bonus met in ${pct(results.swift)} of ${results.swift[1]} wins that offered it`);
console.log('bonus goals met in wins:', Object.entries(results.bonus).map(([k, v]) => `${k} ${pct(v)} (${v[1]})`).join(' · '));
console.log(`pushes and pulls, per battle: ${Object.entries(results.shoves).map(([k, v]) => `${k} ${(v / Math.max(1, results.battles)).toFixed(2)}`).join(' · ') || '-'}`);
console.log('gold from broken buildings, per win:', Object.entries(results.coins).filter(([, v]) => v[0]).map(([k, v]) => `${k} ${(v[0] / v[1]).toFixed(1)}`).join(' · ') || '-');
if (results.wreck[2]) console.log(`Act I boss wreckage broken: ${results.wreck[0]}/${results.wreck[1]} carts in ${results.wreck[2]} wins (${(results.wreck[3] / results.wreck[2]).toFixed(1)} units lost to the cleanup per win)`);
if (results.cleanups.length) console.log(`cleanups: ${results.cleanups.length}, lasting ${q(results.cleanups, 0.25)}/${q(results.cleanups, 0.5)}/${q(results.cleanups, 0.75)} turns (p25/median/p75)`);
console.log('loot taken in won battles:', Object.entries(results.loot).map(([k, v]) => `${k} ${v[0]}/${v[1]}`).join(' · ') || '-');
if (results.walls.length) console.log('walls:', results.walls.join(' | '));
// HALLDUMP=file: the winning armies, for Hall of Fame checks.
if (process.env.HALLDUMP) require('fs').writeFileSync(process.env.HALLDUMP, JSON.stringify(results.armies));
console.log(`final commander levels: ${results.lv.join(',')} · ${((Date.now() - t0) / 1000).toFixed(1)}s`);
