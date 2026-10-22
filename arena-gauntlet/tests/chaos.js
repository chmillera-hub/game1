// Stress test: random ranks, talents, relics, dragons and bosses. Run: node tests/chaos.js [battles]
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js']);
const E = AG.Engine;
const { UNITS, RECRUITABLE, TALENTS, RELICS, talentEligible } = AG.Data;
const N = +process.argv[2] || 200;
const bosses = ['golem_king', 'witch_queen', 'ashen_tyrant'];
let over = 0;
let wins = { P: 0, E: 0 };
for (let i = 0; i < N; i++) {
  const rng = new AG.RNG(5000 + i);
  const units = [];
  const used = new Set();
  const spot = (team) => {
    for (let g = 0; g < 100; g++) {
      const x = rng.range(0, 8);
      const y = team === 'P' ? rng.range(6, 8) : rng.range(0, 2);
      if (!used.has(x + ',' + y)) {
        used.add(x + ',' + y);
        return [x, y];
      }
    }
  };
  for (const team of ['P', 'E']) {
    const n = rng.range(3, 7);
    for (let k = 0; k < n; k++) {
      const type = team === 'E' && k === 0 && rng.chance(0.4) ? rng.pick(bosses) : rng.pick(RECRUITABLE);
      const talents = [];
      for (const t of rng.shuffle(Object.keys(TALENTS))) if (talents.length < 2 && rng.chance(0.3) && talentEligible(type, t, talents)) talents.push(t);
      const [x, y] = spot(team);
      units.push({ type, team, rank: rng.range(1, 3), talents, x, y, wounded: rng.chance(0.1) });
    }
  }
  const relics = { P: rng.shuffle(Object.keys(RELICS)).slice(0, rng.range(0, 6)), E: rng.chance(0.3) ? [rng.pick(Object.keys(RELICS))] : [] };
  const terrain = new Array(81).fill(0);
  for (let k = 0; k < rng.range(0, 6); k++) terrain[rng.range(3, 5) * 9 + rng.range(0, 8)] = rng.pick([1, 2, 3]);
  const objective = units.some((u) => UNITS[u.type].boss) ? 'boss' : 'all';
  const s = E.createBattle({ w: 9, h: 9, terrain, units, relics, seed: 77 + i, objective });
  let turns = 0;
  while (!s.over && turns++ < 200) {
    AG.AI.playTurn(s, s.side, { stance: rng.pick(['aggressive', 'balanced', 'defensive']), temp: 1 });
    s.events.length = 0;
  }
  if (!s.over) throw new Error('battle did not end, seed ' + i);
  over++;
  wins[s.winner]++;
}
console.log(`chaos: ${over}/${N} battles finished cleanly`, wins);
