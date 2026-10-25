/* Army builders for the simulation scripts. Each returns placed entries
   ({def, x, y, talents, rune}) within the fight's supply and squares.
     auto   what the war room's Auto-deploy button does
     value  the best value per supply, a little wary of duplicates
     big    the priciest pieces first, one of each, then fill
     mix    random picks (pricier ones likelier), random upgrades */
'use strict';

const KINDS = ['auto', 'value', 'big', 'mix'];

function upgrade(AG, run, entries, budget, rng) {
  for (const e of rng.shuffle(entries.slice())) {
    const t = AG.talentsFor(e.def).filter((x) => AG.Run.talentCost(run, x) <= budget);
    if (t.length && rng.chance(0.7)) { const pick = rng.pick(t); e.talents.push(pick); budget -= AG.Run.talentCost(run, pick); }
  }
  const free = AG.Run.runeCounts(run);
  for (const e of entries) {
    const r = Object.keys(free).filter((k) => free[k] > 0 && AG.Runes[k].cost <= budget);
    if (r.length) { const k = rng.pick(r); e.rune = k; free[k]--; budget -= AG.Runes[k].cost; }
  }
  return budget;
}

function armyFor(AG, run, enc, kind, rng) {
  const Run = AG.Run;
  if (kind === 'auto') return Run.autoArmy(run, enc);
  const lim = Run.limits(run, enc);
  let budget = lim.supply;
  const types = run.units.filter((d) => AG.Units[d]).map((def) => {
    const u = AG.B.makeUnit(def, 0, 0, 0, { rank: run.ranks[def] || 0 });
    return { def, cost: AG.Units[def].cost, v: AG.B.computeValue(u) };
  });
  const minCost = Math.min.apply(null, types.map((t) => t.cost));
  const out = [];
  const count = {};
  const add = (t) => { out.push({ def: t.def, talents: [], rune: null }); count[t.def] = (count[t.def] || 0) + 1; budget -= t.cost; };
  if (kind === 'value') {
    while (out.length < lim.cells) {
      let best = null, score = -1;
      for (const t of types) {
        if (t.cost > budget) continue;
        const sc = (t.v / t.cost) * Math.pow(0.85, count[t.def] || 0);
        if (sc > score) { best = t; score = sc; }
      }
      if (!best) break;
      add(best);
    }
  } else if (kind === 'big') {
    for (const t of types.slice().sort((a, b) => b.cost - a.cost)) {
      if (out.length >= lim.cells) break;
      if (t.cost <= budget - minCost || (t.cost <= budget && out.length === lim.cells - 1)) add(t);
    }
    const cheap = types.filter((t) => t.cost === minCost);
    while (out.length < lim.cells && budget >= minCost) add(rng.pick(cheap));
  } else {
    for (let guard = 0; guard < 200 && out.length < lim.cells && budget >= minCost; guard++) {
      const ok = types.filter((t) => t.cost <= budget);
      add(rng.weighted(ok, (t) => t.cost));
    }
  }
  upgrade(AG, run, out, budget, rng);
  return Run.placeArmy(enc, out);
}

module.exports = { armyFor, KINDS };
