// AI-vs-AI battle simulations. Run: node tests/sim.js [battles]
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js']);
const E = AG.Engine;
const { UNITS, RECRUITABLE } = AG.Data;

const N = +process.argv[2] || 200;

function randomArmy(rng, budget, team, pool) {
  const units = [];
  let spent = 0;
  let guard = 0;
  while (guard++ < 50) {
    const type = rng.pick(pool);
    const c = UNITS[type].cost;
    if (spent + c > budget) {
      if (spent >= budget - 1) break;
      continue;
    }
    const T = UNITS[type];
    units.push({ type, team, level: 1, a1: rng.pick(T.abilities[1]), a2: T.abilities[2][0] });
    spent += c + AG.Data.ABILITIES[units[units.length - 1].a1].cost;
  }
  return units;
}

function place(rng, units, team, w, h) {
  const rows = team === 'P' ? [h - 1, h - 2] : [0, 1];
  const used = new Set();
  for (const u of units) {
    const role = UNITS[u.type].role;
    const front = role === 'tank' || role === 'melee' || role === 'skirmisher' || role === 'monster';
    const pref = front ? [rows[1], rows[0]] : [rows[0], rows[1]];
    let placed = false;
    for (const y of pref) {
      const xs = rng.shuffle([...Array(w).keys()]);
      for (const x of xs) {
        if (used.has(x + ',' + y)) continue;
        used.add(x + ',' + y);
        u.x = x;
        u.y = y;
        u.facing = team === 'P' ? 0 : 2;
        placed = true;
        break;
      }
      if (placed) break;
    }
  }
  return units;
}

function terrain(rng, w, h) {
  const t = new Array(w * h).fill(0);
  const n = rng.range(1, 4);
  for (let i = 0; i < n; i++) {
    const x = rng.range(0, w - 1);
    const y = rng.range(2, h - 3);
    t[y * w + x] = 1;
    t[(h - 1 - y) * w + (w - 1 - x)] = 1;
  }
  return t;
}

function runBattle(seed, pPool, ePool, budget, opts = {}) {
  const rng = new AG.RNG(seed);
  const w = 9;
  const h = 9;
  const units = [
    ...place(rng, randomArmy(rng, budget, 'P', pPool), 'P', w, h),
    ...place(rng, randomArmy(rng, budget, 'E', ePool), 'E', w, h),
  ];
  const s = E.createBattle({ w, h, terrain: terrain(rng, w, h), units, seed, relics: { P: [], E: [] } });
  let actions = 0;
  const t0 = Date.now();
  while (!s.over) {
    const team = s.side;
    AG.AI.playTurn(s, team, { stance: team === 'P' ? opts.pStance || 'balanced' : opts.eStance || 'balanced', temp: 0.8 });
    actions++;
    s.events.length = 0;
    if (actions > 4000) throw new Error('runaway battle');
  }
  return { winner: s.winner, turns: s.turn, timeout: !!s.timeout, ms: Date.now() - t0, comp: units.map((u) => u.team + ':' + u.type) };
}

const pool = process.env.WITH_LEGENDS ? RECRUITABLE.slice() : RECRUITABLE.filter((t) => UNITS[t].rarity !== 'legendary');
let wins = { P: 0, E: 0 };
let turns = 0;
let timeouts = 0;
let ms = 0;
let maxMs = 0;
const typeWins = {};
for (let i = 0; i < N; i++) {
  const r = runBattle(1000 + i, pool, pool, 14);
  wins[r.winner]++;
  turns += r.turns;
  if (r.timeout) timeouts++;
  ms += r.ms;
  maxMs = Math.max(maxMs, r.ms);
  for (const c of r.comp) {
    const [team, type] = c.split(':');
    typeWins[type] = typeWins[type] || { w: 0, n: 0 };
    typeWins[type].n++;
    if (team === r.winner) typeWins[type].w++;
  }
}
console.log(`battles=${N} P=${wins.P} E=${wins.E} avgTurns=${(turns / N).toFixed(1)} timeouts=${timeouts} avgMs=${(ms / N).toFixed(0)} maxMs=${maxMs}`);
const rows = Object.entries(typeWins)
  .map(([t, v]) => [t, v.w / v.n, v.n])
  .sort((a, b) => b[1] - a[1]);
for (const [t, wr, n] of rows) console.log(`${t.padEnd(12)} winrate ${(wr * 100).toFixed(0)}%  (n=${n})`);
