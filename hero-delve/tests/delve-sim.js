// Plays whole delves headless with the AI on both sides. Run: node tests/delve-sim.js [runs]
// PARTY=scout,assassin,witch,golem picks the four heroes; LV=5 starts them at that level.
const m = new Map();
globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js', 'dungeon.js']);
const AI = AG.AI, DV = AG.Delve;
const N = +process.argv[2] || 6;
const PARTY = process.env.PARTY ? process.env.PARTY.split(',') : null;
const LV = +process.env.LV || 1;
// Seeded, so a run can be replayed (SEED=n).
let seed = +process.env.SEED || 7;
Math.random = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
const t0 = Date.now();
const results = [];
for (let i = 0; i < N; i++) {
  const p = DV.newProfile();
  if (PARTY) PARTY.forEach((t, k) => DV.setClass(p, k, t));
  // The sim's heroes spend their own points and fill their own slots.
  for (const h of DV.heroes(p)) h.auto = true;
  for (const h of DV.heroes(p)) while (h.lv < LV) DV.gainXp(h, DV.xpToNext(h.lv), p);
  DV.autoKit(p);
  DV.startRun(p, 1000 + i);
  console.log(`run ${i} ${p.party.map((h) => h.type).join('/')}:`);
  let outcome = 'cleared';
  while (p.run) {
    const { s } = DV.floorBattle(p);
    const known = new Set();
    const credited = new Set();
    const tally = { wipe: 0, leash: 0, fell: 0, champ: 0 };
    let g = 0;
    let idle = 0;
    const lv0 = DV.partyLevel(p);
    const total = (h) => { let t = h.xp; for (let l = 1; l < h.lv; l++) t += DV.xpToNext(l); return t; };
    const xp0 = total(p.party[0]);
    while (!s.over && g++ < 20000) {
      // RUSH=1: the player sends the party straight at the Champion, ready or not.
      const champ = process.env.RUSH && s.units.find((u) => u.champ && u.alive);
      const focus = s.side === 'P' ? (champ ? { uid: champ.uid } : DV.exploreTarget(s, idle)) : null;
      AI.playTurn(s, s.side, s.side === 'E' ? { stance: 'aggressive', temp: 0.4 } : { stance: 'balanced', temp: 0.3, focus });
      DV.creditKills(p, s, credited);
      for (const d of DV.packsDown(s, known)) {
        DV.rollLoot(p, AG.derive(p.run.seed, 'loot' + d.pack), p.run.floor, d.kind);
        if (d.champ) tally.champ = s.turn;
      }
      for (const e of s.events) {
        if (e.t === 'wipe') tally.wipe++;
        if (e.t === 'summon' && e.spawn) tally.spawned = (tally.spawned || 0) + 1;
        if (e.t === 'death' && s.byId[e.uid] && s.byId[e.uid].traits.has('spawner')) tally.broke = (tally.broke || 0) + 1;
        if (e.t === 'fatigue') tally.fat = (tally.fat || 0) + 1;
        if (e.t === 'dmg' && e.dmgType === 'fatigue' && s.byId[e.uid] && !s.byId[e.uid].alive && s.byId[e.uid].team === 'E') tally.fatKills = (tally.fatKills || 0) + 1;
        if (e.t === 'wake' && e.uids.some((id) => s.byId[id].champ)) tally.woke = (tally.woke ? tally.woke + ',' : '') + `r${s.turn}@L${DV.partyLevelIn(s).toFixed(1)}`;
        if (e.t === 'reset' && e.why === 'leash') tally.leash++;
        if (e.t === 'death' && s.byId[e.uid] && s.byId[e.uid].team === 'P') tally.fell++;
      }
      DV.refreshParty(p, s);
      idle = DV.idleAfter(s, s.events, idle);
      s.events.length = 0;
    }
    const left = s.units.filter((u) => u.team === 'E' && u.alive && !u.nonCombat);
    console.log(`  F${p.run.floor} ${s.over ? 'clear' : 'STALL'} ${s.turn} rounds · party Lv ${lv0.toFixed(1)}→${DV.partyLevel(p).toFixed(1)} · xp +${total(p.party[0]) - xp0} · fell ${tally.fell} wipes ${tally.wipe} leash ${tally.leash} · spawned ${tally.spawned || 0}, spawners broken ${tally.broke || 0}/${s.units.filter((u) => u.traits.has('spawner')).length} · fatigued fights ${tally.fat || 0} (monsters it killed ${tally.fatKills || 0}) · champion woke ${tally.woke} down r${tally.champ}${left.length ? ' · left ' + left.map((u) => u.type + u.dlv + (u.asleep ? 'z' : '')).join(',') : ''}`);
    if (!s.over) {
      outcome = 'stall F' + p.run.floor;
      DV.endRun(p);
      break;
    }
    DV.finishFloor(p, s);
  }
  console.log('  →', outcome, '· loot', p.stash.length - 12, '· levels', DV.heroes(p).map((h) => h.lv).join('/'), '· prestige', p.prestige || 0);
  results.push(outcome);
}
console.log('cleared', results.filter((r) => r === 'cleared').length + '/' + N, '·', ((Date.now() - t0) / 1000).toFixed(1) + 's');
