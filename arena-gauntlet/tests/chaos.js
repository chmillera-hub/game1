// Stress test: random levels, abilities, skills, gear, enchantments, relics, bosses,
// walls, kegs, wagons, totems, spawners and reinforcement waves. Checks board invariants
// every turn. Run: node tests/chaos.js [battles]
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js']);
const E = AG.Engine;
const D = AG.Data;
const N = +process.argv[2] || 200;
const bosses = Object.keys(D.UNITS).filter((k) => D.UNITS[k].boss);
const foes = Object.keys(D.UNITS).filter((k) => D.UNITS[k].rarity === 'enemy' && k !== 'tower');
let over = 0;
const wins = { P: 0, E: 0 };
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
    return null;
  };
  const spec = (type, team) => {
    const T = D.UNITS[type];
    const sp = { type, team, level: rng.range(1, 3) };
    if (T.abilities) {
      sp.a1 = rng.pick(T.abilities[1]);
      sp.a2 = rng.pick(T.abilities[2]);
    }
    sp.skills = rng.shuffle(Object.keys(D.SKILLS)).slice(0, rng.range(0, 2)).filter((id) => D.eligible(type, D.SKILLS[id]));
    sp.gear = rng.shuffle(Object.keys(D.GEAR)).slice(0, rng.range(0, 2)).filter((id) => D.eligible(type, D.GEAR[id]));
    if (rng.chance(0.25)) sp.enchant = rng.pick(Object.keys(D.ENCHANTS));
    return sp;
  };
  for (const team of ['P', 'E']) {
    const n = rng.range(3, 7);
    for (let k = 0; k < n; k++) {
      let type = rng.pick(D.RECRUITABLE);
      if (team === 'E' && k === 0 && rng.chance(0.4)) type = rng.pick(bosses);
      else if (team === 'E' && rng.chance(0.5)) type = rng.pick(foes);
      const p = spot(team);
      if (!p) continue;
      units.push(Object.assign(spec(type, team), { x: p[0], y: p[1], facing: team === 'P' ? 0 : 2 }));
    }
  }
  for (const [type, x, y] of [['barrel', rng.range(0, 8), 3], ['wall', rng.range(0, 8), 4], ['cart', 8, 5], ['tower', rng.range(0, 8), 2],
    [rng.pick(['totem', 'hexstone', 'obelisk']), rng.range(0, 8), rng.range(1, 3)], ['barricade', rng.range(0, 8), 4]]) {
    if (used.has(x + ',' + y) || rng.chance(0.3)) continue;
    used.add(x + ',' + y);
    units.push({ type, team: 'E', x, y });
  }
  // Reinforcements: some from buildings (goal or optional), some from the back edge.
  const waves = [];
  const spawners = rng.range(0, 2);
  for (let k = 0; k < spawners; k++) {
    const p = spot('E');
    if (!p) continue;
    const key = 'sp' + k;
    units.push({ type: rng.pick(['war_tent', 'crypt', 'den', 'portal', 'guardhouse']), team: 'E', x: p[0], y: p[1], key, goal: rng.chance(0.5) });
    for (let t = rng.range(1, 3); t <= 12; t += rng.range(2, 3)) waves.push({ turn: t, from: key, units: [spec(rng.pick(foes), 'E')] });
  }
  if (rng.chance(0.3)) {
    const tiles = [];
    for (let x = 0; x < 9; x++) tiles.push([x, 0], [x, 1]);
    for (let t = 1; t <= 5; t += 2) waves.push({ turn: t, tiles, units: [spec(rng.pick(foes), 'E'), spec(rng.pick(foes), 'E')] });
  }
  const relics = { P: rng.shuffle(Object.keys(D.RELICS)).slice(0, rng.range(0, 6)), E: rng.chance(0.3) ? [rng.pick(Object.keys(D.RELICS))] : [] };
  const terrain = new Array(81).fill(0);
  for (let k = 0; k < rng.range(0, 6); k++) {
    const x = rng.range(0, 8);
    const y = rng.range(3, 5);
    if (!used.has(x + ',' + y)) terrain[y * 9 + x] = rng.pick([1, 2, 3]);
  }
  const objective = units.some((u) => D.UNITS[u.type].boss) ? 'boss' : rng.pick(['all', 'all', 'destroy', 'survive']);
  const s = E.createBattle({ w: 9, h: 9, terrain, units, relics, seed: 77 + i, objective, surviveTurns: objective === 'survive' ? 6 : 0, waves });
  let turns = 0;
  while (!s.over && turns++ < 200) {
    AG.AI.playTurn(s, s.side, { stance: rng.pick(['aggressive', 'balanced', 'defensive']), temp: 1 });
    s.events.length = 0;
    for (const u of s.units) {
      if (u.alive && s.occ[E.idx(s, u.x, u.y)] !== u.uid) throw new Error('occupancy mismatch, seed ' + i + ' ' + u.type);
      if (u.alive && (u.hp <= 0 || u.hp > u.maxHp)) throw new Error('bad hp, seed ' + i + ' ' + u.type + ' ' + u.hp);
      if (u.armor > 0.5 || u.res > 0.5) throw new Error('resistance over cap ' + u.type);
    }
  }
  if (!s.over) throw new Error('battle did not end, seed ' + i);
  over++;
  wins[s.winner]++;
}
console.log(`chaos: ${over}/${N} battles finished cleanly`, wins);
