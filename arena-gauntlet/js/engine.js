// Battle rules. Pure game logic: no DOM, no drawing. Every change is also pushed to
// state.events so the renderer can animate what happened.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const { DIRS, UNITS, RANK_MULT } = AG.Data;

  const T_GRASS = 0;
  const T_ROCK = 1;
  const T_WATER = 2;
  const T_LAVA = 3;

  const other = (t) => (t === 'P' ? 'E' : 'P');
  const manhattan = (ax, ay, bx, by) => Math.abs(ax - bx) + Math.abs(ay - by);
  const idx = (s, x, y) => y * s.w + x;
  const inB = (s, x, y) => x >= 0 && y >= 0 && x < s.w && y < s.h;

  function at(s, x, y) {
    if (!inB(s, x, y)) return null;
    const id = s.occ[idx(s, x, y)];
    return id ? s.byId[id] : null;
  }

  function dirFromDelta(dx, dy) {
    if (dx === 0 && dy === 0) return -1;
    if (Math.abs(dx) >= Math.abs(dy)) return dx > 0 ? 1 : 3;
    return dy > 0 ? 2 : 0;
  }

  function unitValue(type, rank) {
    const T = UNITS[type];
    if (T.traits.includes('summon')) return 5;
    if (T.traits.includes('object')) return 45;
    return T.cost * 10 * (1 + 0.3 * ((rank || 1) - 1)) * (T.boss ? 2 : 1);
  }

  // ---------------------------------------------------------------- setup

  function applyStar3(type, act, traits) {
    switch (type) {
      case 'knight': traits.add('shieldwall'); break;
      case 'archer': traits.add('pierce'); break;
      case 'scout': traits.add('ambush'); break;
      case 'cleric': act.radius = 4; act.cleanse = true; break;
      case 'berserker': traits.add('bloodrage'); break;
      case 'pyromancer': act.pattern = 'square'; break;
      case 'assassin': traits.add('deathmark'); break;
      case 'golem': traits.add('bulwark'); break;
      case 'beastrider': traits.add('trample'); break;
      case 'furgon': traits.add('thornwall'); break;
      case 'wisp': act.radius = 3; break;
      case 'barrier': traits.add('aegisfield'); break;
      case 'enchantress': act.fx = { para: 2 }; break;
      case 'witch': act.len = 7; act.ff = false; break;
      case 'lightning': act.radius = 3; break;
      case 'dragon': act.len = 4; break;
    }
  }

  function addUnit(s, spec) {
    const T = UNITS[spec.type];
    const rank = spec.rank || 1;
    const team = spec.team;
    const rel = s.relics[team];
    const tal = new Set(spec.talents || []);
    const traits = new Set(T.traits || []);
    const m = RANK_MULT[rank];
    const act = JSON.parse(JSON.stringify(T.act));
    let maxHp = Math.round((spec.baseHp || T.hp) * m);
    let pow = Math.round(T.pow * m);
    let armor = T.armor;
    let block = T.block;
    let rec = T.rec;
    let move = T.move;
    if (rank >= 3) applyStar3(spec.type, act, traits);
    if (tal.has('thick_hide')) maxHp += 15;
    if (tal.has('hardened')) armor += 0.1;
    if (tal.has('sentinel')) block += 0.12;
    if (tal.has('swift') && move > 0) move += 1;
    if (tal.has('eagle_eye') && act.range && act.range[1] >= 2) act.range[1] += 1;
    if (tal.has('quickened')) rec = Math.max(0, rec - 1);
    const summon = traits.has('summon') || traits.has('object');
    if (!summon) {
      if (rel.has('oak_charm')) maxHp += 8;
      if (rel.has('iron_plating')) armor += 0.06;
      if (rel.has('steel_bucklers') && !traits.has('nofacing')) block += 0.08;
      if (rel.has('swift_boots') && move > 0 && move <= 3) move += 1;
      if (rel.has('mana_crystal') && T.rec >= 2) rec = Math.max(1, rec - 1);
    }
    const u = {
      uid: s.nextUid++,
      type: spec.type,
      team,
      rid: spec.rid || null,
      name: spec.name || T.name,
      x: spec.x,
      y: spec.y,
      facing: traits.has('nofacing') ? -1 : spec.facing != null ? spec.facing : team === 'P' ? 0 : 2,
      rank,
      tal,
      traits,
      act,
      maxHp,
      hp: spec.wounded ? Math.ceil(maxHp / 2) : maxHp,
      pow,
      armor: Math.min(0.8, armor),
      block: traits.has('nofacing') ? 0 : Math.min(0.85, block),
      rec,
      move,
      wait: spec.wait || 0,
      para: 0,
      poison: null,
      alive: true,
      activated: false,
      secondWind: tal.has('second_wind'),
      firstActionFree: !summon && rel.has('eternal_flame'),
      boss: !!T.boss,
      vip: !!(spec.vip || T.boss),
      post: spec.post || null,
      bound: !!spec.post,
      nonCombat: summon,
      summoner: spec.summoner || 0,
      born: spec.born || 0,
      thorns: spec.thorns || 0,
      kills: 0,
      value: unitValue(spec.type, rank),
    };
    if (traits.has('object')) u.value = 45;
    if (spec.vip && !T.boss) u.value *= 1.8;
    if (u.bound) u.value *= 0.5;
    if (u.hp < 1) u.hp = 1;
    s.units.push(u);
    s.byId[u.uid] = u;
    s.occ[idx(s, u.x, u.y)] = u.uid;
    return u;
  }

  // cfg: { w, h, terrain, units: [{type, team, rank, talents, x, y, facing, rid, name, wounded, vip, post}],
  //        relics: {P: [], E: []}, seed, turnLimit,
  //        objective: 'all' | 'boss' | 'vip' | 'destroy' | 'hold' | 'survive',
  //        hold: {x, y, need}, surviveTurns, loot: [{id, kind, x, y}] }
  function createBattle(cfg) {
    const s = {
      w: cfg.w,
      h: cfg.h,
      terrain: cfg.terrain.slice(),
      units: [],
      byId: {},
      occ: new Array(cfg.w * cfg.h).fill(0),
      side: 'P',
      turn: 1,
      over: false,
      winner: null,
      rng: new AG.RNG(cfg.seed || 1),
      act: null,
      nextUid: 1,
      relics: { P: new Set((cfg.relics && cfg.relics.P) || []), E: new Set((cfg.relics && cfg.relics.E) || []) },
      objective: cfg.objective || 'all',
      turnLimit: cfg.turnLimit || 30,
      events: [],
      phoenixUsed: { P: false, E: false },
      stats: { dmg: { P: 0, E: 0 }, kills: { P: 0, E: 0 } },
      summonCount: 0,
      hold: cfg.hold ? { x: cfg.hold.x, y: cfg.hold.y, need: cfg.hold.need || 2, count: 0 } : null,
      surviveTurns: cfg.surviveTurns || 0,
      loot: (cfg.loot || []).map((l) => ({ id: l.id, kind: l.kind, x: l.x, y: l.y, taken: false, by: 0 })),
    };
    for (const spec of cfg.units) addUnit(s, spec);
    for (const team of ['P', 'E']) {
      if (!s.relics[team].has('sands_of_haste')) continue;
      for (const u of s.units) if (u.team === other(team) && UNITS[u.type].rec >= 2 && !u.boss) u.wait = 1;
    }
    return s;
  }

  // ------------------------------------------------------------- geometry

  function withUnitAt(s, u, x, y, fn) {
    if (u.x === x && u.y === y) return fn();
    const ox = u.x;
    const oy = u.y;
    s.occ[idx(s, ox, oy)] = 0;
    u.x = x;
    u.y = y;
    s.occ[idx(s, x, y)] = u.uid;
    try {
      return fn();
    } finally {
      s.occ[idx(s, x, y)] = 0;
      u.x = ox;
      u.y = oy;
      s.occ[idx(s, ox, oy)] = u.uid;
    }
  }

  // Tiles a unit can end its move on. Map<index, {x, y, d, prev}>.
  function reachable(s, u, maxMove) {
    const res = new Map();
    const start = idx(s, u.x, u.y);
    res.set(start, { x: u.x, y: u.y, d: 0, prev: -1 });
    const mv = maxMove != null ? maxMove : u.move;
    if (mv <= 0 || u.traits.has('immobile') || u.para > 0) return res;
    const flying = u.traits.has('flying');
    const shadow = u.traits.has('shadowstep');
    const dist = new Map([[start, 0]]);
    const queue = [start];
    let qi = 0;
    while (qi < queue.length) {
      const ci = queue[qi++];
      const cd = dist.get(ci);
      if (cd >= mv) continue;
      const cx = ci % s.w;
      const cy = (ci - cx) / s.w;
      for (const [dx, dy] of DIRS) {
        const nx = cx + dx;
        const ny = cy + dy;
        if (!inB(s, nx, ny)) continue;
        const ni = idx(s, nx, ny);
        if (dist.has(ni)) continue;
        const t = s.terrain[ni];
        if (t !== T_GRASS && !flying) continue;
        const o = at(s, nx, ny);
        if (o && o !== u) {
          const pass =
            flying || (!o.nonCombat && (o.team === u.team || shadow));
          if (!pass) continue;
        }
        dist.set(ni, cd + 1);
        queue.push(ni);
        if (!o && t === T_GRASS) res.set(ni, { x: nx, y: ny, d: cd + 1, prev: ci });
      }
    }
    res.dist = dist;
    return res;
  }

  // Rebuild a step-by-step path to (tx, ty) using a fresh BFS that records parents.
  function findPath(s, u, tx, ty) {
    const start = idx(s, u.x, u.y);
    const goal = idx(s, tx, ty);
    const flying = u.traits.has('flying');
    const shadow = u.traits.has('shadowstep');
    const parent = new Map([[start, -1]]);
    const dist = new Map([[start, 0]]);
    const queue = [start];
    let qi = 0;
    while (qi < queue.length) {
      const ci = queue[qi++];
      if (ci === goal) break;
      const cd = dist.get(ci);
      if (cd >= u.move) continue;
      const cx = ci % s.w;
      const cy = (ci - cx) / s.w;
      for (const [dx, dy] of DIRS) {
        const nx = cx + dx;
        const ny = cy + dy;
        if (!inB(s, nx, ny)) continue;
        const ni = idx(s, nx, ny);
        if (dist.has(ni)) continue;
        if (s.terrain[ni] !== T_GRASS && !flying) continue;
        const o = at(s, nx, ny);
        if (o && o !== u && !(flying || (!o.nonCombat && (o.team === u.team || shadow)))) continue;
        dist.set(ni, cd + 1);
        parent.set(ni, ci);
        queue.push(ni);
      }
    }
    if (!parent.has(goal)) return null;
    const path = [];
    for (let i = goal; i !== -1; i = parent.get(i)) path.push({ x: i % s.w, y: Math.floor(i / s.w) });
    return path.reverse();
  }

  function patternTiles(s, pattern, cx, cy) {
    const offs =
      pattern === 'square'
        ? [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]
        : [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]];
    const out = [];
    for (const [dx, dy] of offs) if (inB(s, cx + dx, cy + dy)) out.push([cx + dx, cy + dy]);
    return out;
  }

  function lineTiles(s, ox, oy, d, len) {
    const [dx, dy] = DIRS[d];
    const out = [];
    let x = ox;
    let y = oy;
    for (let i = 0; i < len; i++) {
      x += dx;
      y += dy;
      if (!inB(s, x, y) || s.terrain[idx(s, x, y)] === T_ROCK) break;
      out.push([x, y]);
    }
    return out;
  }

  function coneTiles(s, ox, oy, d, len) {
    const [dx, dy] = DIRS[d];
    const px = -dy;
    const py = dx;
    const out = [];
    for (let i = 1; i <= len; i++) {
      const spread = i === 1 ? 0 : 1;
      for (let j = -spread; j <= spread; j++) {
        const x = ox + dx * i + px * j;
        const y = oy + dy * i + py * j;
        if (inB(s, x, y) && s.terrain[idx(s, x, y)] !== T_ROCK) out.push([x, y]);
      }
    }
    return out;
  }

  function radiusTiles(s, ox, oy, r, includeSelf) {
    const out = [];
    for (let y = oy - r; y <= oy + r; y++)
      for (let x = ox - r; x <= ox + r; x++) {
        if (!inB(s, x, y)) continue;
        const d = manhattan(ox, oy, x, y);
        if (d > r || (d === 0 && !includeSelf)) continue;
        out.push([x, y]);
      }
    return out;
  }

  // ---------------------------------------------------------- modifiers

  function inBarrier(s, u) {
    for (const v of s.units) {
      if (!v.alive || v.team !== u.team || !v.traits.has('aura_barrier')) continue;
      const r = v.traits.has('aegisfield') ? 3 : 2;
      if (manhattan(u.x, u.y, v.x, v.y) <= r) return v;
    }
    return null;
  }

  function aegisField(s, u) {
    const b = inBarrier(s, u);
    return !!(b && b.traits.has('aegisfield'));
  }

  function nearBanner(s, u) {
    for (const v of s.units) {
      if (v.alive && v.team === u.team && v.type === 'warbanner' && manhattan(u.x, u.y, v.x, v.y) <= 2) return true;
    }
    return false;
  }

  function guardianReduction(s, u) {
    let best = 0;
    for (const v of s.units) {
      if (!v.alive || v === u || v.team !== u.team || manhattan(u.x, u.y, v.x, v.y) !== 1) continue;
      if (v.traits.has('guardian')) best = Math.max(best, v.traits.has('bulwark') ? 0.35 : 0.2);
      if (v.tal.has('guardian')) best = Math.max(best, 0.15);
    }
    return best;
  }

  function magicTakenMult(s, u) {
    let m = 1;
    if (u.traits.has('spellward')) m *= 0.5;
    if (inBarrier(s, u)) m *= 0.5;
    if (s.relics[u.team].has('dragon_scale') && !u.nonCombat) m *= 0.75;
    return m;
  }

  function statusImmune(s, u, kind) {
    if (u.nonCombat || u.traits.has('stoneskin') || u.tal.has('unshakable')) return true;
    if (kind === 'para' && u.boss) return true;
    return !!inBarrier(s, u);
  }

  function dirCategory(fx, fy, tgt) {
    if (tgt.facing < 0) return 'front';
    const dx = fx - tgt.x;
    const dy = fy - tgt.y;
    const [ux, uy] = DIRS[tgt.facing];
    const a = dx * ux + dy * uy;
    const b = Math.abs(dx * uy - dy * ux);
    if (a > 0 && a >= b) return 'front';
    if (a < 0 && -a > b) return 'back';
    return 'side';
  }

  function blockChance(s, tgt, cat) {
    if (tgt.facing < 0 || tgt.para > 0) return 0;
    let b = tgt.block;
    if (cat === 'side') b = tgt.traits.has('shieldwall') || s.relics[tgt.team].has('aegis') ? b : b / 2;
    else if (cat === 'back') b = 0;
    return Math.min(0.85, b);
  }

  // Damage one attacker deals to one target, before the block roll.
  // opts: { fromX, fromY, moved, moveDist, mult, dmgType }
  function calcHit(s, atk, tgt, opts) {
    const dmgType = opts.dmgType || atk.act.dmg;
    const fx = opts.fromX != null ? opts.fromX : atk.x;
    const fy = opts.fromY != null ? opts.fromY : atk.y;
    const cat = dirCategory(fx, fy, tgt);
    const relA = s.relics[atk.team];
    let mult = opts.mult || 1;
    if (atk.traits.has('rage') && atk.hp < atk.maxHp / 2) mult *= 1.3;
    if (atk.tal.has('brutal')) mult *= 1.15;
    if (relA.has('old_crown')) mult *= 1.15;
    if (relA.has('titan_gauntlet')) mult *= 1.25;
    if (nearBanner(s, atk)) mult *= 1.15;
    if (relA.has('cursed_blade')) mult *= 1.2;
    if (s.relics[tgt.team].has('cursed_blade') && !tgt.nonCombat) mult *= 1.1;
    if (cat === 'back') {
      if (atk.traits.has('backstab')) mult *= atk.traits.has('deathmark') ? 2 : 1.5;
      if (atk.traits.has('ambush')) mult *= 1.5;
      if (relA.has('shadow_cloak')) mult *= 1.4;
    }
    if (cat !== 'front' && dmgType === 'phys' && atk.tal.has('flanker')) mult *= 1.3;
    if (atk.traits.has('charge') && opts.moved && (opts.moveDist || 0) >= 3) mult *= atk.traits.has('trample') ? 1.6 : 1.3;
    if (tgt.hp < tgt.maxHp / 2) {
      if (atk.tal.has('executioner')) mult *= 1.4;
      if (relA.has('headsman_axe')) mult *= 1.3;
    }
    if (dmgType === 'magic' && atk.tal.has('arcane_focus')) mult *= 1.2;
    let dmg = atk.pow * mult;
    if (dmgType === 'phys') {
      if (relA.has('whetstone')) dmg += 2;
      if (tgt.traits.has('ethereal')) dmg *= 0.5;
      const armor = atk.traits.has('pierce') ? tgt.armor * 0.5 : tgt.armor;
      dmg *= 1 - armor;
      if (aegisField(s, tgt)) dmg *= 0.85;
    } else if (dmgType === 'magic') {
      dmg *= magicTakenMult(s, tgt);
    }
    dmg *= 1 - guardianReduction(s, tgt);
    dmg = Math.max(1, Math.round(dmg));
    const block = dmgType === 'phys' ? blockChance(s, tgt, cat) : 0;
    return { dmg, block, cat };
  }

  function poisonDamage(u) {
    return Math.max(1, Math.round(u.pow * (u.tal.has('arcane_focus') ? 1.2 : 1)));
  }

  function healAmount(u) {
    return Math.round(u.pow * (u.tal.has('arcane_focus') ? 1.2 : 1));
  }

  // ------------------------------------------------------------ targeting

  function isFoe(u, v) {
    return v.alive && v.team !== u.team;
  }

  function unitsOnTiles(s, tiles) {
    const out = [];
    for (const [x, y] of tiles) {
      const v = at(s, x, y);
      if (v) out.push(v);
    }
    return out;
  }

  // Legal targets for u's action from its current tile.
  function targetsFrom(s, u) {
    const a = u.act;
    const res = [];
    switch (a.kind) {
      case 'strike':
      case 'cleave':
      case 'quake': {
        const [r0, r1] = a.range;
        for (const v of s.units) {
          if (!isFoe(u, v)) continue;
          const d = manhattan(u.x, u.y, v.x, v.y);
          if (d >= r0 && d <= r1) res.push({ kind: 'unit', uid: v.uid, x: v.x, y: v.y });
        }
        break;
      }
      case 'blast': {
        const [r0, r1] = a.range;
        for (let y = u.y - r1; y <= u.y + r1; y++)
          for (let x = u.x - r1; x <= u.x + r1; x++) {
            if (!inB(s, x, y)) continue;
            const d = manhattan(u.x, u.y, x, y);
            if (d < r0 || d > r1) continue;
            const hits = unitsOnTiles(s, patternTiles(s, a.pattern, x, y));
            if (hits.some((v) => isFoe(u, v))) res.push({ kind: 'tile', x, y });
          }
        break;
      }
      case 'line':
      case 'cone': {
        for (let d = 0; d < 4; d++) {
          const tiles = a.kind === 'line' ? lineTiles(s, u.x, u.y, d, a.len) : coneTiles(s, u.x, u.y, d, a.len);
          if (!tiles.length) continue;
          if (unitsOnTiles(s, tiles).some((v) => isFoe(u, v))) res.push({ kind: 'dir', d, x: u.x + DIRS[d][0], y: u.y + DIRS[d][1] });
        }
        break;
      }
      case 'cross': {
        const tiles = [];
        for (let d = 0; d < 4; d++) tiles.push(...lineTiles(s, u.x, u.y, d, a.len));
        if (unitsOnTiles(s, tiles).some((v) => isFoe(u, v))) res.push({ kind: 'self', x: u.x, y: u.y });
        break;
      }
      case 'nova': {
        const hits = unitsOnTiles(s, radiusTiles(s, u.x, u.y, a.radius));
        if (hits.some((v) => isFoe(u, v) && !v.nonCombat)) res.push({ kind: 'self', x: u.x, y: u.y });
        break;
      }
      case 'pray': {
        const hits = unitsOnTiles(s, radiusTiles(s, u.x, u.y, a.radius, true));
        const useful = hits.some(
          (v) => v.team === u.team && !v.nonCombat && ((v.hp < v.maxHp && !v.poison) || (a.cleanse && (v.poison || v.para)))
        );
        if (useful) res.push({ kind: 'self', x: u.x, y: u.y });
        break;
      }
      case 'grow': {
        const [r0, r1] = a.range;
        for (const [x, y] of radiusTiles(s, u.x, u.y, r1)) {
          if (manhattan(u.x, u.y, x, y) < r0) continue;
          if (s.terrain[idx(s, x, y)] !== T_GRASS || at(s, x, y)) continue;
          res.push({ kind: 'tile', x, y });
        }
        break;
      }
    }
    return res;
  }

  function sameTarget(a, b) {
    if (a.kind !== b.kind) return false;
    if (a.kind === 'unit') return a.uid === b.uid;
    if (a.kind === 'dir') return a.d === b.d;
    if (a.kind === 'self') return true;
    return a.x === b.x && a.y === b.y;
  }

  function affectedTiles(s, u, target) {
    const a = u.act;
    if (target.kind === 'unit' && s.byId[target.uid]) {
      const v = s.byId[target.uid];
      target = { kind: 'unit', uid: v.uid, x: v.x, y: v.y };
    }
    switch (a.kind) {
      case 'strike':
        return [[target.x, target.y]];
      case 'cleave':
        return radiusTiles(s, u.x, u.y, 1);
      case 'quake':
        return radiusTiles(s, target.x, target.y, 1, true);
      case 'blast':
        return patternTiles(s, a.pattern, target.x, target.y);
      case 'line':
        return lineTiles(s, u.x, u.y, target.d, a.len);
      case 'cone':
        return coneTiles(s, u.x, u.y, target.d, a.len);
      case 'cross': {
        const t = [];
        for (let d = 0; d < 4; d++) t.push(...lineTiles(s, u.x, u.y, d, a.len));
        return t;
      }
      case 'nova':
        return radiusTiles(s, u.x, u.y, a.radius);
      case 'pray':
        return radiusTiles(s, u.x, u.y, a.radius, true);
      case 'grow':
        return [[target.x, target.y]];
    }
    return [];
  }

  // Units an action would touch, in resolution order.
  function affectedUnits(s, u, target) {
    const a = u.act;
    const tiles = affectedTiles(s, u, target);
    const units = unitsOnTiles(s, tiles).filter((v) => v !== u || a.kind === 'pray');
    switch (a.kind) {
      case 'strike':
        return units.filter((v) => v.uid === target.uid);
      case 'cleave':
      case 'quake':
      case 'cross':
      case 'nova':
        return units.filter((v) => isFoe(u, v));
      case 'blast':
      case 'line':
      case 'cone':
        return units.filter((v) => (a.ff ? v.alive : isFoe(u, v)));
      case 'pray':
        return units.filter((v) => v.team === u.team && !v.nonCombat);
    }
    return [];
  }

  function facingToward(u, target) {
    if (target.kind === 'dir') return target.d;
    if (target.kind === 'self') return -1;
    return dirFromDelta(target.x - u.x, target.y - u.y);
  }

  // Predicted outcome of an action, without rolling dice.
  // ctx: { moved, moveDist } (defaults to the live activation)
  function previewAction(s, u, target, ctx) {
    const a = u.act;
    const c = ctx || (s.act && s.act.uid === u.uid ? { moved: s.act.moved && !s.act.acted, moveDist: s.act.moveDist } : { moved: false, moveDist: 0 });
    const tiles = affectedTiles(s, u, target);
    const effects = [];
    const opts = { moved: c.moved, moveDist: c.moveDist };
    for (const v of affectedUnits(s, u, target)) {
      const e = { uid: v.uid, friendly: v.team === u.team };
      if (a.kind === 'pray') {
        e.heal = v.poison && !a.cleanse ? 0 : Math.min(healAmount(u), v.maxHp - v.hp);
        if (a.cleanse && (v.poison || v.para)) e.cleanse = true;
      } else {
        if (a.dmg) {
          const r = calcHit(s, u, v, opts);
          e.dmg = r.dmg;
          e.block = r.block;
          e.cat = r.cat;
          e.kill = r.dmg >= v.hp && !v.secondWind;
        }
        if (a.fx && a.fx.para) e.para = statusImmune(s, v, 'para') ? 'resist' : a.fx.para;
        if (a.fx && a.fx.poison) e.poison = statusImmune(s, v, 'poison') ? 'resist' : { turns: a.fx.poison, dmg: poisonDamage(u) };
      }
      effects.push(e);
    }
    return { tiles, effects };
  }

  // ------------------------------------------------------------ resolution

  function emit(s, ev) {
    s.events.push(ev);
  }

  function heal(s, u, amount, why) {
    if (!u.alive || u.nonCombat) return 0;
    if (u.poison) {
      if (why === 'prayer') emit(s, { t: 'healblock', uid: u.uid });
      return 0;
    }
    const h = Math.min(Math.round(amount), u.maxHp - u.hp);
    if (h <= 0) return 0;
    u.hp += h;
    emit(s, { t: 'heal', uid: u.uid, amount: h, why });
    return h;
  }

  function kill(s, u, src) {
    u.alive = false;
    u.hp = 0;
    s.occ[idx(s, u.x, u.y)] = 0;
    if (s.act && s.act.uid === u.uid) {
      // Died mid-action (thorns or a counterattack): its turn is over.
      s.act = null;
      u.activated = true;
      u.wait = u.rec;
    }
    emit(s, { t: 'death', uid: u.uid, src: src ? src.uid : 0 });
    if (src && src.team !== u.team && !u.nonCombat) {
      s.stats.kills[src.team]++;
      src.kills++;
      if (s.act && s.act.uid === src.uid) s.act.killed = true;
    }
    if (u.tal.has('martyr')) {
      for (const v of s.units)
        if (v.alive && v.team === u.team && manhattan(u.x, u.y, v.x, v.y) <= 2) heal(s, v, 20, 'martyr');
    }
    if (!u.nonCombat && s.relics[u.team].has('phoenix_feather') && !s.phoenixUsed[u.team] && !at(s, u.x, u.y)) {
      s.phoenixUsed[u.team] = true;
      u.alive = true;
      u.hp = Math.ceil(u.maxHp / 2);
      u.poison = null;
      u.para = 0;
      s.occ[idx(s, u.x, u.y)] = u.uid;
      emit(s, { t: 'revive', uid: u.uid, hp: u.hp });
    }
  }

  function applyDamage(s, src, tgt, amount, info) {
    if (!tgt.alive || amount <= 0) return 0;
    let dealt;
    if (amount >= tgt.hp && tgt.secondWind) {
      tgt.secondWind = false;
      dealt = tgt.hp - 1;
      tgt.hp = 1;
      emit(s, { t: 'dmg', uid: tgt.uid, amount, cat: info.cat, dmgType: info.dmgType, src: src ? src.uid : 0 });
      emit(s, { t: 'secondwind', uid: tgt.uid });
    } else {
      dealt = Math.min(amount, tgt.hp);
      tgt.hp -= dealt;
      emit(s, { t: 'dmg', uid: tgt.uid, amount, cat: info.cat, dmgType: info.dmgType, src: src ? src.uid : 0 });
      if (tgt.hp <= 0) kill(s, tgt, src);
    }
    if (src && src.team !== tgt.team) s.stats.dmg[src.team] += dealt;
    return dealt;
  }

  function hit(s, atk, tgt, opts) {
    if (!tgt.alive) return { blocked: false, dmg: 0 };
    const r = calcHit(s, atk, tgt, opts);
    const dmgType = opts.dmgType || atk.act.dmg;
    if (r.block > 0 && s.rng.next() < r.block) {
      emit(s, { t: 'block', uid: tgt.uid, src: atk.uid, cat: r.cat });
      reactToMelee(s, atk, tgt, opts);
      return { blocked: true, dmg: 0 };
    }
    const dealt = applyDamage(s, atk, tgt, r.dmg, { cat: r.cat, dmgType });
    if (dealt > 0 && atk.alive && !opts.noDrain) {
      let ls = 0;
      if (atk.tal.has('vampiric')) ls += 0.3;
      if (atk.traits.has('drain')) ls += 0.4;
      if (s.relics[atk.team].has('bloodstone')) ls += 0.2;
      if (ls > 0) heal(s, atk, Math.max(1, Math.round(dealt * ls)), 'drain');
    }
    reactToMelee(s, atk, tgt, opts);
    return { blocked: false, dmg: dealt };
  }

  // Thorns and Retaliate after a melee blow.
  function reactToMelee(s, atk, tgt, opts) {
    if (opts.noReact || !atk.alive) return;
    const fx = opts.fromX != null ? opts.fromX : atk.x;
    const fy = opts.fromY != null ? opts.fromY : atk.y;
    const dmgType = opts.dmgType || atk.act.dmg;
    if (dmgType !== 'phys' || manhattan(fx, fy, tgt.x, tgt.y) !== 1) return;
    let thorns = tgt.thorns || 0;
    if (!tgt.nonCombat && s.relics[tgt.team].has('thorned_mail')) thorns += 5;
    if (thorns > 0) {
      emit(s, { t: 'thorns', uid: atk.uid, src: tgt.uid });
      applyDamage(s, tgt, atk, thorns, { cat: 'none', dmgType: 'true' });
    }
    if (atk.alive && tgt.alive && tgt.tal.has('retaliate') && tgt.para === 0) {
      emit(s, { t: 'retaliate', uid: tgt.uid, target: atk.uid });
      hit(s, tgt, atk, { mult: 0.5, dmgType: 'phys', noReact: true, noDrain: true });
    }
  }

  function applyPara(s, u, n) {
    if (!u.alive) return;
    if (statusImmune(s, u, 'para')) {
      emit(s, { t: 'resist', uid: u.uid });
      return;
    }
    u.para = Math.max(u.para, n);
    emit(s, { t: 'status', uid: u.uid, status: 'para', turns: u.para });
  }

  function applyPoison(s, src, u, turns, dmg) {
    if (!u.alive) return;
    if (statusImmune(s, u, 'poison')) {
      emit(s, { t: 'resist', uid: u.uid });
      return;
    }
    const p = u.poison;
    u.poison = { turns: Math.max(turns, p ? p.turns : 0), dmg: Math.max(dmg, p ? p.dmg : 0), src: src.uid };
    emit(s, { t: 'status', uid: u.uid, status: 'poison', turns: u.poison.turns });
  }

  function summonShrub(s, u, x, y) {
    const mine = s.units.filter((v) => v.alive && v.type === 'shrub' && v.summoner === u.uid).sort((a, b) => a.born - b.born);
    while (mine.length >= 3) {
      const old = mine.shift();
      old.alive = false;
      s.occ[idx(s, old.x, old.y)] = 0;
      emit(s, { t: 'wither', uid: old.uid });
    }
    const thorn = u.traits.has('thornwall');
    const shrub = addUnit(s, {
      type: 'shrub',
      team: u.team,
      rank: 1,
      x,
      y,
      summoner: u.uid,
      born: ++s.summonCount,
      thorns: thorn ? 6 : 0,
      baseHp: Math.round(18 * RANK_MULT[u.rank] * (thorn ? 2 : 1)),
    });
    emit(s, { t: 'summon', uid: shrub.uid, x, y, by: u.uid });
  }

  // ------------------------------------------------------------ loot

  function lootAt(s, x, y) {
    return s.loot.find((l) => !l.taken && l.x === x && l.y === y) || null;
  }

  function canLoot(s, u) {
    if (!u || !u.alive || u.team !== 'P' || u.nonCombat || !lootAt(s, u.x, u.y)) return false;
    if (s.act && s.act.uid === u.uid) return !s.act.acted;
    return canActivate(s, u);
  }

  // Spend a unit's action to pick up the loot it is standing on.
  function takeLoot(s, uid) {
    const u = s.byId[uid];
    const A = s.act;
    if (!A || A.uid !== uid || A.acted || s.over) return false;
    const l = lootAt(s, u.x, u.y);
    if (!l) return false;
    A.acted = true;
    l.taken = true;
    l.by = uid;
    emit(s, { t: 'loot', uid, kind: l.kind, id: l.id, x: u.x, y: u.y });
    return true;
  }

  // ------------------------------------------------------------ activation

  function canActivate(s, u) {
    return !!(
      u && u.alive && !s.over && u.team === s.side && !u.activated && u.wait === 0 && u.para === 0 && !u.nonCombat &&
      !(u.act.kind === 'none' && u.move === 0)
    );
  }

  function readyUnits(s, team) {
    return s.units.filter((u) => u.team === team && canActivateFor(s, u, team));
  }

  function canActivateFor(s, u, team) {
    return !!(
      u.alive && u.team === team && !u.activated && u.wait === 0 && u.para === 0 && !u.nonCombat && !(u.act.kind === 'none' && u.move === 0)
    );
  }

  function beginActivation(s, uid) {
    const u = s.byId[uid];
    if (s.act) {
      if (s.act.uid === uid) return true;
      if (s.act.moved || s.act.acted) return false;
      s.act = null;
    }
    if (!canActivate(s, u)) return false;
    s.act = { uid, sx: u.x, sy: u.y, sf: u.facing, moved: false, acted: false, moveDist: 0, movedBeforeAct: false, killed: false };
    return true;
  }

  function cancelActivation(s) {
    if (s.act && !s.act.moved && !s.act.acted) s.act = null;
  }

  function moveUnit(s, uid, x, y) {
    const A = s.act;
    const u = s.byId[uid];
    if (!A || A.uid !== uid || A.moved || s.over) return null;
    const reach = reachable(s, u);
    const r = reach.get(idx(s, x, y));
    if (!r || r.d === 0) return null;
    const path = findPath(s, u, x, y);
    if (!path) return null;
    s.occ[idx(s, u.x, u.y)] = 0;
    u.x = x;
    u.y = y;
    s.occ[idx(s, x, y)] = u.uid;
    A.moved = true;
    A.moveDist = r.d;
    A.movedBeforeAct = !A.acted;
    if (u.facing >= 0 && path.length >= 2) {
      const a = path[path.length - 2];
      u.facing = dirFromDelta(x - a.x, y - a.y);
    }
    emit(s, { t: 'move', uid, path, facing: u.facing });
    return path;
  }

  function undoMove(s) {
    const A = s.act;
    if (!A || !A.moved || A.acted) return false;
    const u = s.byId[A.uid];
    s.occ[idx(s, u.x, u.y)] = 0;
    u.x = A.sx;
    u.y = A.sy;
    s.occ[idx(s, u.x, u.y)] = u.uid;
    u.facing = A.sf;
    A.moved = false;
    A.moveDist = 0;
    A.movedBeforeAct = false;
    emit(s, { t: 'teleport', uid: u.uid, x: u.x, y: u.y, facing: u.facing });
    return true;
  }

  function performAction(s, uid, target) {
    const A = s.act;
    const u = s.byId[uid];
    if (!A || A.uid !== uid || A.acted || s.over) return false;
    const legal = targetsFrom(s, u).find((t) => sameTarget(t, target));
    if (!legal) return false;
    target = legal;
    const a = u.act;
    A.acted = true;
    const opts = { moved: A.movedBeforeAct, moveDist: A.moveDist, fromX: u.x, fromY: u.y };
    const tiles = affectedTiles(s, u, target);
    const fd = facingToward(u, target);
    if (fd >= 0 && u.facing >= 0 && fd !== u.facing) {
      u.facing = fd;
      emit(s, { t: 'face', uid, facing: fd });
    }
    emit(s, { t: 'action', uid, kind: a.kind, name: a.name, target, tiles, x: u.x, y: u.y, dmg: a.dmg || null });
    const victims = affectedUnits(s, u, target);
    switch (a.kind) {
      case 'strike':
      case 'quake':
      case 'line':
      case 'cone':
      case 'cross':
        for (const v of victims) if (u.alive) hit(s, u, v, opts);
        break;
      case 'cleave': {
        let struck = 0;
        for (const v of victims) {
          if (!u.alive) break;
          hit(s, u, v, opts);
          struck++;
        }
        if (u.traits.has('bloodrage') && u.alive) heal(s, u, 5 * struck, 'drain');
        break;
      }
      case 'blast':
        for (const v of victims) {
          if (a.dmg) hit(s, u, v, opts);
          if (a.fx && a.fx.para && v.team !== u.team) applyPara(s, v, a.fx.para);
        }
        break;
      case 'nova':
        for (const v of victims) {
          if (v.nonCombat && !a.dmg) continue;
          if (a.dmg) hit(s, u, v, opts);
          if (a.fx && a.fx.poison) applyPoison(s, u, v, a.fx.poison, poisonDamage(u));
        }
        break;
      case 'pray':
        for (const v of victims) {
          if (a.cleanse && (v.poison || v.para)) {
            v.poison = null;
            v.para = 0;
            emit(s, { t: 'cleanse', uid: v.uid });
          }
          heal(s, v, healAmount(u), 'prayer');
        }
        break;
      case 'grow':
        summonShrub(s, u, target.x, target.y);
        break;
    }
    checkOutcome(s);
    return true;
  }

  function finishActivation(s, facing) {
    const A = s.act;
    if (!A) return;
    const u = s.byId[A.uid];
    s.act = null;
    if (!u.alive) return;
    if (facing != null && facing >= 0 && u.facing >= 0 && u.facing !== facing) {
      u.facing = facing;
      emit(s, { t: 'face', uid: u.uid, facing });
    }
    let w = 0;
    if (A.acted) {
      w = u.rec;
      if (u.firstActionFree) {
        w = 0;
        u.firstActionFree = false;
      }
      if (A.killed && (u.tal.has('bloodlust') || s.relics[u.team].has('warlord_helm'))) w = 0;
    } else if (A.moved) {
      w = Math.floor(u.rec / 2);
    }
    u.wait = w;
    u.activated = true;
    emit(s, { t: 'done', uid: u.uid, wait: w });
  }

  function endTurn(s) {
    if (s.over) return;
    if (s.act) finishActivation(s, null);
    const side = s.side;
    for (const u of s.units) {
      if (!u.alive || u.team !== side) continue;
      if (!u.activated) {
        if (u.wait > 0) u.wait--;
        else if (u.para > 0) u.para--;
      }
      u.activated = false;
    }
    s.side = other(side);
    if (s.side === 'P') s.turn++;
    startTurn(s);
  }

  function startTurn(s) {
    const team = s.side;
    emit(s, { t: 'turn', side: team, turn: s.turn });
    if (team === 'P' && s.turn > s.turnLimit) {
      s.over = true;
      s.winner = strength(s, 'P') > strength(s, 'E') ? 'P' : 'E';
      s.timeout = true;
      emit(s, { t: 'end', winner: s.winner, timeout: true });
      return;
    }
    for (const u of s.units) {
      if (!u.alive || u.team !== team || !u.poison) continue;
      const p = u.poison;
      applyDamage(s, s.byId[p.src] || null, u, p.dmg, { cat: 'none', dmgType: 'poison' });
      if (!u.alive) continue;
      p.turns--;
      if (p.turns <= 0) {
        u.poison = null;
        emit(s, { t: 'cure', uid: u.uid });
      }
    }
    for (const u of s.units) {
      if (!u.alive || u.team !== team || u.nonCombat) continue;
      if (u.traits.has('regrowth')) heal(s, u, 4, 'regrowth');
      if (s.relics[team].has('sacred_chalice')) heal(s, u, 3, 'chalice');
    }
    if (team === 'P' && s.hold) {
      const h = s.hold;
      const on = at(s, h.x, h.y);
      if (on && on.team === 'P' && !on.nonCombat) h.count++;
      else h.count = 0;
      emit(s, { t: 'hold', count: h.count, need: h.need, uid: on && on.team === 'P' ? on.uid : 0 });
      if (h.count >= h.need) {
        s.over = true;
        s.winner = 'P';
        s.act = null;
        emit(s, { t: 'end', winner: 'P', held: true });
        return;
      }
    }
    if (team === 'P' && s.surviveTurns && s.turn > s.surviveTurns) {
      s.over = true;
      s.winner = 'P';
      s.act = null;
      emit(s, { t: 'end', winner: 'P', survived: true });
      return;
    }
    if (s.relics[team].has('healing_salve')) {
      let best = null;
      for (const u of s.units) {
        if (!u.alive || u.team !== team || u.nonCombat || u.poison) continue;
        if (!best || u.maxHp - u.hp > best.maxHp - best.hp) best = u;
      }
      if (best && best.hp < best.maxHp) heal(s, best, 6, 'salve');
    }
    checkOutcome(s);
  }

  function canDealDamage(u) {
    return !!(u.act.dmg || (u.act.fx && u.act.fx.poison));
  }

  // Remaining fighting strength, used to settle battles that hit the turn limit.
  function strength(s, team) {
    let t = 0;
    for (const u of s.units) if (u.alive && u.team === team && !u.nonCombat) t += u.value * (u.hp / u.maxHp);
    return t;
  }

  function checkOutcome(s) {
    if (s.over) return;
    const alive = { P: false, E: false };
    const armed = { P: false, E: false };
    let hasVip = false;
    let vipAlive = false;
    let hasObj = false;
    let objAlive = false;
    for (const u of s.units) {
      if (u.vip && u.team === 'E') {
        hasVip = true;
        if (u.alive) vipAlive = true;
      }
      if (u.traits.has('object') && u.team === 'E') {
        hasObj = true;
        if (u.alive) objAlive = true;
      }
      // Treasure guardians are bound to their post and do not need to be defeated.
      if (u.alive && !u.nonCombat && !u.bound) {
        alive[u.team] = true;
        if (canDealDamage(u)) armed[u.team] = true;
      }
    }
    const vipDown = (s.objective === 'boss' || s.objective === 'vip') && hasVip && !vipAlive;
    const objDown = s.objective === 'destroy' && hasObj && !objAlive;
    let winner = null;
    let surrender = false;
    if (!alive.P && !alive.E) winner = s.side;
    else if (!alive.P) winner = 'E';
    else if (!alive.E || vipDown || objDown) winner = 'P';
    else if (!armed.P || !armed.E) {
      // A side with nobody left who can hurt the enemy yields.
      winner = armed.P ? 'P' : 'E';
      surrender = true;
    }
    if (winner) {
      s.over = true;
      s.winner = winner;
      s.act = null;
      emit(s, { t: 'end', winner, surrender, vipSlain: vipDown, destroyed: objDown });
    }
  }

  function forfeit(s) {
    if (s.over) return;
    s.over = true;
    s.winner = 'E';
    s.act = null;
    emit(s, { t: 'end', winner: 'E', forfeit: true });
  }

  function drainEvents(s) {
    const ev = s.events;
    s.events = [];
    return ev;
  }

  AG.Engine = {
    T_GRASS, T_ROCK, T_WATER, T_LAVA,
    other, manhattan, idx, inB, at, dirFromDelta, unitValue,
    canDealDamage, strength, createBattle, addUnit, withUnitAt, reachable, findPath,
    patternTiles, lineTiles, coneTiles, radiusTiles,
    inBarrier, guardianReduction, magicTakenMult, statusImmune, dirCategory, blockChance, calcHit,
    poisonDamage, healAmount, targetsFrom, sameTarget, affectedTiles, affectedUnits, previewAction, facingToward,
    lootAt, canLoot, takeLoot, nearBanner,
    canActivate, canActivateFor, readyUnits, beginActivation, cancelActivation, moveUnit, undoMove, performAction,
    finishActivation, endTurn, startTurn, checkOutcome, forfeit, drainEvents,
  };
})(typeof window !== 'undefined' ? window : globalThis);
