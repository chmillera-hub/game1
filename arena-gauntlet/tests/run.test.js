// Plays whole campaigns with the AI on both sides. Losses are retried, as in the game.
// Run: node tests/run.test.js [runs] [difficulty] [maxTries]
const assert = require('assert');
const AG = require('./load')();
const R = AG.Run;
const E = AG.Engine;
const D = AG.Data;
const N = +process.argv[2] || 12;
const DIFF = process.argv[3] || 'knight';
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
  for (const d of dep) assert.ok(rows.includes(d.y) && p.enc.terrain[d.y * p.enc.w + d.x] === 0, 'valid deploy tile');
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
  const swift = (p.enc.bonus || []).find((b) => b.type === 'swift');
  if (swift && s.winner === 'P') {
    results.swift[1]++;
    if (s.turn <= swift.turns) results.swift[0]++;
  }
  return R.finishBattle(run, s, dep);
}

function pickUnit(run, pick) {
  const ok = run.roster.filter((u) => (pick.filter === 'transmute' ? ['common', 'uncommon'].includes(D.UNITS[u.type].rarity) : true));
  return ok.length ? ok[0].id : null;
}

const results = { done: 0, stuck: 0, battles: 0, tries: 0, first: { 1: [0, 0], 2: [0, 0], 3: [0, 0] }, kinds: {}, missions: {}, lv: [], walls: [], lens: {}, timeouts: 0, swift: [0, 0], overtime: { P: 0, E: 0 }, otKinds: {}, loot: {}, bonus: {} };
const t0 = Date.now();
for (let i = 0; i < N; i++) {
  // DRAFT=1: draft each army, picking at random as a player might, instead of a warband.
  let run;
  if (process.env.DRAFT) {
    const pick = AG.derive(9000 + i, 'sim-draft');
    const picks = [];
    for (let s = 0; s < R.DRAFT_STEPS.length; s++) picks.push(pick.pick(R.draftOffer(9000 + i, s, picks).options));
    run = R.newRun({ seed: 9000 + i, difficulty: DIFF, draft: { units: picks.slice(0, 5), relic: picks[5], items: [['skill', picks[6]], ['gear', picks[7]]] } });
  } else run = R.newRun({ seed: 9000 + i, warband: D.WARBANDS[i % D.WARBANDS.length].id, difficulty: DIFF });
  const rng = new AG.RNG(i + 1);
  let steps = 0;
  let stuck = false;
  while (!run.over && steps++ < 500 && !stuck) {
    if (!run.pending) {
      const opts = R.availableNodes(run);
      assert.ok(opts.length, 'map has a way forward');
      assert.ok(R.enterNode(run, rng.pick(opts).id));
      continue;
    }
    const p = run.pending;
    if (p.type === 'battle') {
      const act = run.act;
      const kind = p.enc.kind;
      let res;
      let tries = 0;
      do {
        res = playBattle(run);
        tries++;
      } while (!res.won && tries < MAX_TRIES);
      results.battles++;
      results.tries += tries;
      results.first[act][1]++;
      if (tries === 1) results.first[act][0]++;
      const k = (results.kinds[kind + act] = results.kinds[kind + act] || [0, 0]);
      k[1]++;
      if (tries === 1) k[0]++;
      const m = (results.missions[p.enc.primary] = results.missions[p.enc.primary] || [0, 0]);
      m[1]++;
      if (tries === 1) m[0]++;
      if (!res.won) {
        stuck = true;
        results.walls.push(`${run.warband} act ${act} ${kind} ${p.enc.name}`);
        if (process.env.VERBOSE) {
          const army = R.autoDeploy(run).map((d) => { const r = R.unitById(run, d.rid); return r.type + 'L' + r.load.lv; });
          console.log(`  WALL ${p.enc.name} (${p.enc.primary}, budget ${p.enc.budget}) E: ${p.enc.units.map((u) => u.type + 'L' + (u.level || 1)).join(' ')} | P supply ${R.supplyFor(run)}: ${army.join(' ')}`);
        }
      }
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
    if (p.type === 'rest') {
      const c = rng.pick(['drill', 'study', 'tinker']);
      assert.ok(R.rest(run, c, 0) || R.rest(run, 'drill'));
      R.completeNode(run);
      continue;
    }
    if (p.type === 'treasure') {
      R.takeTreasure(run);
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
  results.lv.push(R.commanderLevel(run));
  console.log(
    `run ${i} ${run.warband.padEnd(8)} ${run.won ? 'WON  ' : 'STUCK'} act ${run.act} lv ${R.commanderLevel(run)} xp ${run.xp} supply ${R.supplyFor(run)} army ${R.armySize(run)} roster=${run.roster.length} items=${run.items.length} relics=${run.relics.length} gold=${run.gold} battles=${run.stats.battles} losses=${run.stats.losses}`
  );
}
const pct = ([a, b]) => (b ? Math.round((100 * a) / b) + '%' : '-');
console.log(`campaigns: won ${results.done}, stuck ${results.stuck} (more than ${MAX_TRIES} tries) · battles ${results.battles}, avg tries ${(results.tries / Math.max(1, results.battles)).toFixed(2)}`);
console.log(`first-try wins: act1 ${pct(results.first[1])} act2 ${pct(results.first[2])} act3 ${pct(results.first[3])}`);
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
console.log('loot taken in won battles:', Object.entries(results.loot).map(([k, v]) => `${k} ${v[0]}/${v[1]}`).join(' · ') || '-');
if (results.walls.length) console.log('walls:', results.walls.join(' | '));
console.log(`final commander levels: ${results.lv.join(',')} · ${((Date.now() - t0) / 1000).toFixed(1)}s`);
