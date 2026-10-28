// Plays whole delves headless with the AI on both sides. Run: node tests/delve-sim.js [runs]
const m = new Map();
globalThis.localStorage = { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js', 'dungeon.js']);
const E = AG.Engine, AI = AG.AI, DV = AG.Delve;
const N = +process.argv[2] || 6;
const PARTY = process.env.PARTY ? process.env.PARTY.split(',') : null;
const t0 = Date.now();
const results = [];
for (let i = 0; i < N; i++) {
  const p = DV.newProfile();
  if (PARTY) PARTY.forEach((t, k) => DV.setClass(p, k, t));
  DV.startRun(p, 1000 + i);
  let line = `run ${i} ${p.party.map((h) => h.type).join('/')}:`;
  let outcome = 'cleared';
  while (p.run) {
    const { s, fl } = DV.floorBattle(p);
    const known = new Set();
    let g = 0;
    let plies = 0;
    let idle = 0;
    while (!s.over && g++ < 6000) {
      const focus = s.side === 'P' ? DV.exploreTarget(s, idle) : null;
      AI.playTurn(s, s.side, s.side === 'E' ? { stance: 'aggressive', temp: 0.4 } : { stance: 'balanced', temp: 0.3, focus });
      for (const d of DV.packsDown(s, known)) DV.rollLoot(p, AG.derive(p.run.seed, 'loot' + d.pack), p.run.floor, d.boss);
      idle = s.events.some((e) => e.t === 'dmg') ? 0 : idle + 1;
      s.events.length = 0;
      plies++;
    }
    if (!s.over) {
      const st = s.units.filter((u) => u.alive);
      console.log('  STALL left:', st.filter((u) => u.team === 'E').map((u) => `${u.type}@${u.x},${u.y} ${u.asleep ? 'asleep' : 'awake'} wait${u.wait} para${u.para} hold${u.holding} nc${u.nonCombat}`).join(' | '));
      console.log('  party:', st.filter((u) => u.team === 'P').map((u) => `${u.type}@${u.x},${u.y} para${u.para} held${u.heldBy}`).join(' | '), 'focus', JSON.stringify(DV.exploreTarget(s, 99)));
    }
    const alive = s.units.filter((u) => u.team === 'P' && u.alive && !u.nonCombat).length;
    const left = s.units.filter((u) => u.team === 'E' && u.alive && !u.nonCombat).length;
    line += ` F${p.run.floor} ${s.over ? (s.winner === 'P' ? 'W' : 'L') : 'STALL'}(${s.turn}t ${alive}up ${left}left)`;
    if (!s.over || s.winner !== 'P') {
      outcome = s.over ? 'died F' + p.run.floor : 'stall F' + p.run.floor;
      DV.endRun(p);
      break;
    }
    DV.finishFloor(p, s);
  }
  console.log(line, '→', outcome, '· loot', p.stash.length - 12);
  results.push(outcome);
}
console.log('cleared', results.filter((r) => r === 'cleared').length + '/' + N, '·', ((Date.now() - t0) / 1000).toFixed(1) + 's');
