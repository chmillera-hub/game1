// Battle rules. Pure game logic: no DOM, no drawing. Every change is also pushed to
// state.events so the renderer can animate what happened.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const D = AG.Data;
  const { DIRS, UNITS } = D;

  const T_GRASS = 0;
  const T_ROCK = 1;
  const T_WATER = 2;
  const T_LAVA = 3;

  const other = (t) => (t === 'P' ? 'E' : 'P');
  const manhattan = (ax, ay, bx, by) => Math.abs(ax - bx) + Math.abs(ay - by);
  const idx = (s, x, y) => y * s.w + x;
  const inB = (s, x, y) => x >= 0 && y >= 0 && x < s.w && y < s.h;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const clampRes = (v) => clamp(v, -D.RES_CAP, D.RES_CAP);
  const clone = (o) => JSON.parse(JSON.stringify(o));

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

  function unitValue(type, level) {
    const T = UNITS[type];
    if (T.traits.includes('summon')) return 5;
    if (T.traits.includes('scenery')) return 6;
    if (T.traits.includes('object')) return T.traits.includes('cart') ? 40 : 45;
    if (T.traits.includes('structure')) return 30;
    return Math.max(2, T.cost) * 10 * (1 + 0.35 * ((level || 1) - 1)) * (T.boss ? 2 : 1);
  }

  // ---------------------------------------------------------------- unit build

  const MAX_PROPS = { guard: 1, magicGuard: 1, pierce: 1 };

  // Status effects stack by keeping the stronger value. Poison and burn are [turns, damage].
  function mergeFx(into, add) {
    for (const k in add) {
      const v = add[k];
      const o = into[k];
      if (Array.isArray(v) && Array.isArray(o)) into[k] = [Math.max(o[0], v[0]), Math.max(o[1], v[1])];
      else if (Array.isArray(v)) into[k] = v.slice();
      else if (!Array.isArray(o)) into[k] = Math.max(o || 0, v);
    }
    return into;
  }

  function mergeProps(into, add) {
    for (const k in add) {
      const v = add[k];
      if (k === 'vs') {
        into.vs = into.vs || {};
        for (const t in v) into.vs[t] = (into.vs[t] || 0) + v[t];
      } else if (k === 'onHit') into.onHit = mergeFx(into.onHit || {}, v);
      else if (MAX_PROPS[k]) into[k] = Math.max(into[k] || 0, v);
      else into[k] = (into[k] || 0) + v;
    }
    return into;
  }

  // Every mod that applies to a unit spec: class abilities, mastery, skills, gear, enchantment.
  function specMods(spec) {
    const T = UNITS[spec.type];
    const lv = spec.level || 1;
    const out = [];
    const ab = T.abilities;
    if (ab) {
      if (spec.a1 && ab[1].includes(spec.a1)) out.push(D.ABILITIES[spec.a1].mod);
      if (lv >= 2 && spec.a2 && ab[2].includes(spec.a2)) out.push(D.ABILITIES[spec.a2].mod);
      if (lv >= 3 && D.MASTERY[spec.type]) out.push(D.MASTERY[spec.type].mod);
    }
    for (const id of new Set(spec.talents || [])) if (D.TALENTS[id] && D.TALENTS[id].cls === spec.type) out.push(D.TALENTS[id].mod);
    for (const id of spec.skills || []) if (D.SKILLS[id]) out.push(D.SKILLS[id].mod);
    for (const id of spec.gear || []) if (D.GEAR[id]) out.push(D.GEAR[id].mod);
    if (spec.enchant && D.ENCHANTS[spec.enchant]) out.push(D.ENCHANTS[spec.enchant].mod);
    return out;
  }

  function prepAct(a) {
    const act = clone(a);
    act.uses = act.uses || 0;
    act.left = act.uses > 0 ? act.uses : Infinity;
    return act;
  }

  // Compile a unit spec into battle numbers.
  function buildUnit(spec, relics) {
    const T = UNITS[spec.type];
    const lv = Math.max(1, Math.min(D.MAX_LEVEL, spec.level || 1));
    const traits = new Set(T.traits || []);
    const props = mergeProps({}, T.props || {});
    const primary = prepAct(T.act);
    const acts = [primary];
    for (const x of T.extra || []) acts.push(prepAct(x));
    let hpAdd = 0;
    let hpPct = 0;
    let powAdd = 0;
    let armor = T.armor;
    let res = T.res || 0;
    let block = T.block;
    let rec = T.rec;
    let move = T.move;
    for (const m of specMods(spec)) {
      const st = m.stat || {};
      hpAdd += st.hp || 0;
      hpPct += st.hpPct || 0;
      powAdd += st.pow || 0;
      armor += st.armor || 0;
      res += st.res || 0;
      block += st.block || 0;
      if (move > 0) move += st.move || 0;
      rec += st.rec || 0;
      if (st.range && primary.range && primary.range[1] >= 2) primary.range[1] += st.range;
      if (st.len && primary.len) primary.len += st.len;
      if (st.radius && primary.radius) primary.radius += st.radius;
      for (const t of m.traits || []) traits.add(t);
      if (m.props) mergeProps(props, m.props);
      if (m.onHit) props.onHit = mergeFx(props.onHit || {}, m.onHit);
      if (m.act) {
        for (const k in m.act) {
          if (k === 'fx') primary.fx = mergeFx(primary.fx || {}, m.act.fx);
          else primary[k] = m.act[k];
        }
      }
      if (m.active) acts.push(prepAct(m.active));
    }
    const isObj = traits.has('summon') || traits.has('object');
    const rel = relics || new Set();
    if (!isObj && !traits.has('structure')) {
      if (rel.has('oak_charm')) hpAdd += 8;
      if (rel.has('iron_plating')) armor += 0.06;
      if (rel.has('steel_bucklers') && !traits.has('nofacing')) block += 0.08;
      if (rel.has('pathfinder') && move > 0 && move <= 3) move += 1;
      if (rel.has('mana_crystal') && T.rec >= 2) rec -= 1;
      if (rel.has('dragon_scale')) res += 0.15;
    }
    const baseHp = spec.baseHp || T.hp;
    const maxHp = Math.round((Math.round(baseHp * D.LEVEL_HP[lv]) + hpAdd) * (1 + hpPct));
    const pow = Math.round(T.pow * D.LEVEL_POW[lv]) + powAdd;
    if (primary.range && primary.range[1] > 7) primary.range[1] = 7;
    if (primary.len) primary.len = Math.min(primary.len, 8);
    if (primary.radius) primary.radius = Math.min(primary.radius, 4);
    return {
      level: lv,
      traits,
      props,
      acts,
      maxHp: Math.max(1, maxHp),
      pow,
      armor: clampRes(armor),
      res: clampRes(res),
      block: traits.has('nofacing') ? 0 : clamp(block, 0, 0.85),
      rec: Math.max(T.rec >= 2 ? 1 : 0, rec),
      move: T.move > 0 ? Math.max(1, move) : 0,
    };
  }

  // ---------------------------------------------------------------- setup

  function addUnit(s, spec) {
    const T = UNITS[spec.type];
    const team = spec.team;
    const b = buildUnit(spec, s.relics[team]);
    const traits = b.traits;
    const summon = traits.has('summon') || traits.has('object');
    const u = {
      uid: s.nextUid++,
      type: spec.type,
      team,
      rid: spec.rid || null,
      name: spec.name || T.name,
      x: spec.x,
      y: spec.y,
      facing: traits.has('nofacing') ? -1 : spec.facing != null ? spec.facing : team === 'P' ? 0 : 2,
      level: b.level,
      a1: spec.a1 || null,
      a2: b.level >= 2 ? spec.a2 || null : null,
      skills: (spec.skills || []).slice(),
      gear: (spec.gear || []).slice(),
      enchant: spec.enchant || null,
      traits,
      tags: new Set(T.tags || []),
      props: b.props,
      acts: b.acts,
      act: b.acts[0],
      maxHp: b.maxHp,
      hp: b.maxHp,
      pow: b.pow,
      armor: b.armor,
      res: b.res,
      block: b.block,
      rec: b.rec,
      move: b.move,
      wait: spec.wait || 0,
      para: 0,
      poison: null,
      burn: null,
      root: 0,
      weak: 0,
      mark: 0,
      frenzy: 0,
      shield: 0,
      alive: true,
      activated: false,
      secondWind: traits.has('secondwind'),
      phoenix: traits.has('phoenix'),
      firstActionFree: !summon && s.relics[team].has('eternal_flame'),
      boss: !!T.boss,
      vip: !!(spec.vip || T.boss),
      post: spec.post || null,
      bound: !!spec.post,
      // Breaking every goal object wins a 'destroy' battle. Optional buildings set goal: false.
      goal: spec.goal != null ? !!spec.goal : traits.has('object') && !traits.has('scenery'),
      key: spec.key || null,
      structure: traits.has('structure') || traits.has('scenery'),
      nonCombat: summon,
      summoner: spec.summoner || 0,
      born: spec.born || 0,
      kills: 0,
      scorched: false,
      value: unitValue(spec.type, b.level),
    };
    if (spec.thorns) u.props.thorns = (u.props.thorns || 0) + spec.thorns;
    if (spec.armor != null) u.armor = spec.armor;
    if (spec.res != null) u.res = spec.res;
    if (spec.vip && !T.boss) u.value *= 1.8;
    if (u.bound) u.value *= 0.5;
    if (spec.hpFrac) u.hp = Math.max(1, Math.round(u.maxHp * spec.hpFrac));
    s.units.push(u);
    s.byId[u.uid] = u;
    s.occ[idx(s, u.x, u.y)] = u.uid;
    return u;
  }

  // cfg: { w, h, terrain, units: [spec], relics: {P: [], E: []}, seed, turnLimit,
  //        objective: 'all' | 'boss' | 'vip' | 'destroy' | 'hold' | 'survive',
  //        hold: {x, y, need}, surviveTurns, loot: [{id, kind, x, y}], cartExit,
  //        waves: [{ turn, team, from, tiles, units: [spec] }] }
  // A unit spec: { type, team, level, a1, a2, skills, gear, enchant, x, y, facing, rid, name, vip, post, goal, key }
  // A wave arrives at the end of its team's turn `turn`, around the building whose key is
  // `from` (cancelled if it falls first), or else on the edge `tiles`.
  function createBattle(cfg) {
    const s = {
      w: cfg.w,
      h: cfg.h,
      terrain: cfg.terrain.slice(),
      units: [],
      byId: {},
      occ: new Array(cfg.w * cfg.h).fill(0),
      side: 'E',
      turn: 1,
      // Side turns so far, both sides counted; statuses remember the one they landed in.
      ply: 1,
      // Whether the side to move has used its one activation this turn.
      spent: false,
      over: false,
      winner: null,
      rng: new AG.RNG(cfg.seed || 1),
      act: null,
      nextUid: 1,
      relics: { P: new Set((cfg.relics && cfg.relics.P) || []), E: new Set((cfg.relics && cfg.relics.E) || []) },
      objective: cfg.objective || 'all',
      turnLimit: cfg.turnLimit || 90,
      events: [],
      phoenixUsed: { P: false, E: false },
      stats: { dmg: { P: 0, E: 0 }, kills: { P: 0, E: 0 }, gold: 0, escaped: 0, blocked: 0 },
      summonCount: 0,
      hold: cfg.hold ? { x: cfg.hold.x, y: cfg.hold.y, need: cfg.hold.need || 2, count: 0 } : null,
      surviveTurns: cfg.surviveTurns || 0,
      loot: (cfg.loot || []).map((l) => ({ id: l.id, kind: l.kind, x: l.x, y: l.y, taken: false, by: 0 })),
      tfx: [],
      booms: [],
      cartExit: cfg.cartExit != null ? cfg.cartExit : 0,
      waves: [],
    };
    for (const spec of cfg.units) addUnit(s, spec);
    (cfg.waves || []).forEach((w, i) => {
      const team = w.team || 'E';
      const src = w.from ? s.units.find((u) => u.key === w.from) : null;
      s.waves.push({
        i,
        team,
        turn: w.turn,
        src: src ? src.uid : 0,
        tiles: w.tiles || null,
        units: w.units.map(clone),
        marks: null,
        state: w.from && !src ? 'cancelled' : 'pending',
      });
    });
    planWaves(s, 'E', s.turn);
    // Bosses take the field on their side's second turn, after you have had a move.
    for (const u of s.units) if (u.boss) u.wait = Math.max(u.wait, 1);
    // Slow casters start out cooling down: they sit out their side's first turn.
    for (const team of ['P', 'E']) {
      if (!s.relics[team].has('sands_of_haste')) continue;
      for (const u of s.units) if (u.team === other(team) && UNITS[u.type].rec >= 2 && !u.boss) u.wait = 1;
    }
    // The enemy opens the battle. With nothing to open with, it passes.
    startTurn(s);
    if (!s.over && !hasMove(s, 'E')) endTurn(s, true);
    return s;
  }

  // ------------------------------------------------------------- geometry

  function withUnitAt(s, u, x, y, fn) {
    if (u.x === x && u.y === y) return fn();
    const ox = u.x;
    const oy = u.y;
    const prev = s.occ[idx(s, x, y)];
    s.occ[idx(s, ox, oy)] = 0;
    u.x = x;
    u.y = y;
    s.occ[idx(s, x, y)] = u.uid;
    try {
      return fn();
    } finally {
      s.occ[idx(s, x, y)] = prev;
      u.x = ox;
      u.y = oy;
      s.occ[idx(s, ox, oy)] = u.uid;
    }
  }

  function tileFx(s, x, y, kind) {
    for (const f of s.tfx) if (f.x === x && f.y === y && (!kind || f.kind === kind)) return f;
    return null;
  }

  // A hostile trap on this tile stops a walking unit there. Flyers pass over traps and fire.
  function trapFor(s, u, x, y) {
    if (u.traits.has('flying')) return null;
    const f = tileFx(s, x, y, 'caltrops');
    return f && f.team !== u.team ? f : null;
  }

  function passable(u, o, flying, shadow) {
    return flying || (!o.nonCombat && !o.structure && (o.team === u.team || shadow));
  }

  // Tiles a unit can end its move on. Map<index, {x, y, d, prev}>.
  function reachable(s, u, maxMove) {
    const res = new Map();
    const start = idx(s, u.x, u.y);
    res.set(start, { x: u.x, y: u.y, d: 0, prev: -1 });
    const mv = maxMove != null ? maxMove : u.move;
    if (mv <= 0 || u.traits.has('immobile') || u.para > 0 || u.root > 0) return res;
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
      if (ci !== start && trapFor(s, u, cx, cy)) continue;
      for (const [dx, dy] of DIRS) {
        const nx = cx + dx;
        const ny = cy + dy;
        if (!inB(s, nx, ny)) continue;
        const ni = idx(s, nx, ny);
        if (dist.has(ni)) continue;
        const t = s.terrain[ni];
        if (t !== T_GRASS && !flying) continue;
        const o = at(s, nx, ny);
        if (o && o !== u && !passable(u, o, flying, shadow)) continue;
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
      if (ci !== start && trapFor(s, u, cx, cy)) continue;
      for (const [dx, dy] of DIRS) {
        const nx = cx + dx;
        const ny = cy + dy;
        if (!inB(s, nx, ny)) continue;
        const ni = idx(s, nx, ny);
        if (dist.has(ni)) continue;
        if (s.terrain[ni] !== T_GRASS && !flying) continue;
        const o = at(s, nx, ny);
        if (o && o !== u && !passable(u, o, flying, shadow)) continue;
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
    let offs;
    if (pattern === 'square') offs = [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]];
    else if (pattern === 'single') offs = [[0, 0]];
    else offs = [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]];
    const out = [];
    for (const [dx, dy] of offs) if (inB(s, cx + dx, cy + dy)) out.push([cx + dx, cy + dy]);
    return out;
  }

  // A straight line that stops at rocks and walls (the wall itself is struck).
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
      const o = at(s, x, y);
      if (o && o.type === 'wall') break;
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

  function auraRadius(v) {
    return 2 + (v.props.auraR || 0);
  }

  function inBarrier(s, u) {
    for (const v of s.units) {
      if (!v.alive || v.team !== u.team || !v.traits.has('aura_barrier')) continue;
      if (manhattan(u.x, u.y, v.x, v.y) <= auraRadius(v)) return v;
    }
    return null;
  }

  function nearBanner(s, u) {
    for (const v of s.units) {
      if (v.alive && v.team === u.team && v.type === 'warbanner' && manhattan(u.x, u.y, v.x, v.y) <= 2) return true;
    }
    return false;
  }

  function effArmor(s, u) {
    let a = u.armor;
    if (!u.nonCombat && !u.structure) {
      const b = inBarrier(s, u);
      if (b && b.traits.has('steelfield')) a += 0.1;
    }
    return clampRes(a);
  }

  function effRes(s, u) {
    let r = u.res;
    if (!u.nonCombat && !u.structure && inBarrier(s, u)) r += 0.25;
    return clampRes(r);
  }

  function guardianReduction(s, u) {
    let best = 0;
    for (const v of s.units) {
      if (!v.alive || v === u || v.team !== u.team || v.nonCombat || manhattan(u.x, u.y, v.x, v.y) !== 1) continue;
      best = Math.max(best, v.props.guard || 0);
    }
    return best;
  }

  function magicGuard(s, u) {
    let best = 0;
    for (const v of s.units) {
      if (!v.alive || v === u || v.team !== u.team || manhattan(u.x, u.y, v.x, v.y) !== 1) continue;
      best = Math.max(best, v.props.magicGuard || 0);
    }
    return best;
  }

  // kind: para | poison | root | knock
  function statusImmune(s, u, kind) {
    if (u.nonCombat || u.structure) return true;
    const tr = u.traits;
    switch (kind) {
      case 'para':
        if (u.boss || tr.has('stoneskin') || tr.has('steadfast') || tr.has('paraproof')) return true;
        return !!inBarrier(s, u);
      case 'poison':
        if (tr.has('stoneskin') || tr.has('undead') || tr.has('poisonproof')) return true;
        return !!inBarrier(s, u);
      case 'root':
        return tr.has('steadfast') || tr.has('immobile');
      case 'knock':
        return u.boss || tr.has('steadfast') || tr.has('immobile') || tr.has('big');
    }
    return false;
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

  // Another fighter on the attacker's side stands next to the target.
  function packed(s, atk, tgt) {
    for (const v of s.units) {
      if (v.alive && v !== atk && v.team === atk.team && !v.nonCombat && !v.structure && manhattan(v.x, v.y, tgt.x, tgt.y) === 1) return true;
    }
    return false;
  }

  // Damage one attacker deals to one target, before the block roll.
  // opts: { fromX, fromY, moved, moveDist, mult, dmgType, act, cat }
  function calcHit(s, atk, tgt, opts) {
    const act = opts.act || atk.act;
    const dmgType = opts.dmgType || act.dmg;
    const fx = opts.fromX != null ? opts.fromX : atk.x;
    const fy = opts.fromY != null ? opts.fromY : atk.y;
    const cat = opts.cat || dirCategory(fx, fy, tgt);
    const relA = s.relics[atk.team];
    const P = atk.props;
    let mult = opts.mult != null ? opts.mult : act.mult || 1;
    if (P.rageMult && atk.hp < atk.maxHp / 2) mult *= 1 + P.rageMult;
    if (P.dmgMult) mult *= 1 + P.dmgMult;
    if (relA.has('old_crown')) mult *= 1.15;
    if (relA.has('titan_gauntlet')) mult *= 1.25;
    if (relA.has('cursed_blade')) mult *= 1.2;
    if (s.relics[tgt.team].has('cursed_blade') && !tgt.nonCombat) mult *= 1.1;
    if (nearBanner(s, atk)) mult *= 1.15;
    if (atk.frenzy > 0) mult *= 1.25;
    if (atk.weak > 0) mult *= 0.7;
    if (cat === 'back') {
      let b = P.backMult || 0;
      if (relA.has('shadow_cloak')) b += 0.4;
      mult *= 1 + b;
    }
    if (cat !== 'front' && dmgType === 'phys' && P.flankMult) mult *= 1 + P.flankMult;
    if (P.chargeMult && opts.moved && (opts.moveDist || 0) >= 3) mult *= 1 + P.chargeMult;
    if (tgt.hp < tgt.maxHp / 2) {
      if (P.execMult) mult *= 1 + P.execMult;
      if (relA.has('headsman_axe')) mult *= 1.3;
    }
    let vs = 0;
    for (const t of tgt.tags) vs += ((P.vs && P.vs[t]) || 0) + ((act.vs && act.vs[t]) || 0);
    if (vs) mult *= 1 + vs;
    if (relA.has('sappers_kit') && tgt.tags.has('structure')) mult *= 1.5;
    if (P.vsArmored && tgt.armor >= 0.3) mult *= 1 + P.vsArmored;
    if (P.packMult && packed(s, atk, tgt)) mult *= 1 + P.packMult;
    if (dmgType === 'magic' && P.magicMult) mult *= 1 + P.magicMult;
    const base = act.fixed != null ? act.fixed : atk.pow;
    let dmg = base * mult;
    if (dmgType === 'phys') {
      if (relA.has('whetstone')) dmg += 2;
      const armor = effArmor(s, tgt);
      const pierce = Math.max(P.pierce || 0, act.pierce || 0);
      dmg *= 1 - (armor > 0 ? armor * (1 - pierce) : armor);
      const b = !tgt.nonCombat && inBarrier(s, tgt);
      if (b && b.traits.has('aegisfield')) dmg *= 0.85;
    } else if (dmgType === 'magic') {
      dmg *= 1 - effRes(s, tgt);
      dmg *= 1 - magicGuard(s, tgt);
    }
    if (tgt.mark > 0) dmg *= 1.25;
    dmg *= 1 - guardianReduction(s, tgt);
    dmg = Math.max(1, Math.round(dmg));
    const block = dmgType === 'phys' ? blockChance(s, tgt, cat) : 0;
    return { dmg, block, cat };
  }

  function poisonDamage(u, act) {
    const a = act || u.act;
    const base = a.poisonDmg || Math.max(1, Math.round(u.pow * (1 + (u.props.magicMult || 0))));
    return base + (u.props.poisonDmg || 0);
  }

  function healAmount(u, act) {
    const a = act || u.act;
    const base = a.fixed != null ? a.fixed : u.pow * (a.mult || 1);
    return Math.round(base * (1 + (u.props.magicMult || 0) + (u.props.healMult || 0)));
  }

  // Status effects an act applies when it lands: its own plus the unit's on-hit effects.
  function hitFx(u, act) {
    const fx = {};
    const add = (src) => {
      for (const k in src) {
        let v = src[k];
        if (k === 'poison' && !Array.isArray(v)) v = [v, poisonDamage(u, act)];
        if (k === 'burn' && !Array.isArray(v)) v = [v, 4];
        mergeFx(fx, { [k]: v });
      }
    };
    add(act.fx || {});
    if (act.dmg && u.props.onHit) add(u.props.onHit);
    if (fx.poison) fx.poison = [fx.poison[0] + (u.props.poisonTurns || 0), fx.poison[1]];
    return fx;
  }

  function hasFx(fx) {
    for (const k in fx) if (fx[k]) return true;
    return false;
  }

  // ------------------------------------------------------------ targeting

  function isFoe(u, v) {
    return v.alive && v.team !== u.team;
  }

  // Walls and kegs never make a spell worth casting on their own.
  const worthy = (v) => !v.traits.has('scenery');

  // A unit in smoke cannot be singled out from more than 1 tile away.
  function concealed(s, v, fx, fy) {
    return !!tileFx(s, v.x, v.y, 'smoke') && manhattan(fx, fy, v.x, v.y) > 1;
  }

  function unitsOnTiles(s, tiles) {
    const out = [];
    for (const [x, y] of tiles) {
      const v = at(s, x, y);
      if (v) out.push(v);
    }
    return out;
  }

  function raisedCount(s, u) {
    let n = 0;
    for (const v of s.units) if (v.alive && v.summoner === u.uid && v.type === 'skeleton') n++;
    return n;
  }

  function emptyGrass(s, x, y) {
    return inB(s, x, y) && s.terrain[idx(s, x, y)] === T_GRASS && !at(s, x, y);
  }

  // The tile behind a target, from the attacker's point of view.
  function behindTile(s, u, v) {
    let d = v.facing;
    if (d < 0) d = dirFromDelta(v.x - u.x, v.y - u.y);
    const [dx, dy] = DIRS[(d + 2) % 4];
    return [v.x + dx, v.y + dy];
  }

  // Whether act `ai` can be used right now (charges left, move-like acts, roots).
  function actUsable(s, u, ai) {
    const a = u.acts[ai];
    if (!a || a.kind === 'none' || a.left <= 0) return false;
    const A = s.act && s.act.uid === u.uid ? s.act : null;
    if (a.asMove) {
      if (A && A.moved) return false;
    } else if (A && A.acted) return false;
    if ((a.kind === 'blink' || a.kind === 'leap' || a.kind === 'shadowstrike') && (u.root > 0 || u.traits.has('immobile'))) return false;
    return true;
  }

  // Legal targets for u's act `ai` (default 0) from its current tile. Each target carries `ai`.
  function targetsFrom(s, u, ai) {
    ai = ai || 0;
    const a = u.acts[ai];
    const res = [];
    if (!a || a.kind === 'none' || a.left <= 0) return res;
    const push = (t) => {
      t.ai = ai;
      res.push(t);
    };
    switch (a.kind) {
      case 'strike':
      case 'cleave':
      case 'quake':
      case 'shadowstrike': {
        const [r0, r1] = a.range;
        for (const v of s.units) {
          if (!isFoe(u, v)) continue;
          if (!a.dmg && (v.nonCombat || v.structure)) continue;
          const d = manhattan(u.x, u.y, v.x, v.y);
          if (d < r0 || d > r1) continue;
          if (concealed(s, v, u.x, u.y)) continue;
          if (a.kind === 'shadowstrike') {
            if (v.nonCombat || v.structure) continue;
            const [bx, by] = behindTile(s, u, v);
            if (!emptyGrass(s, bx, by)) continue;
            push({ kind: 'unit', uid: v.uid, x: v.x, y: v.y, bx, by });
            continue;
          }
          push({ kind: 'unit', uid: v.uid, x: v.x, y: v.y });
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
            if (hits.some((v) => isFoe(u, v) && (a.dmg || (!v.nonCombat && !v.structure)))) push({ kind: 'tile', x, y });
          }
        break;
      }
      case 'line':
      case 'cone': {
        for (let d = 0; d < 4; d++) {
          const tiles = a.kind === 'line' ? lineTiles(s, u.x, u.y, d, a.len) : coneTiles(s, u.x, u.y, d, a.len);
          if (!tiles.length) continue;
          if (unitsOnTiles(s, tiles).some((v) => isFoe(u, v))) push({ kind: 'dir', d, x: u.x + DIRS[d][0], y: u.y + DIRS[d][1] });
        }
        break;
      }
      case 'cross': {
        const tiles = [];
        for (let d = 0; d < 4; d++) tiles.push(...lineTiles(s, u.x, u.y, d, a.len));
        if (unitsOnTiles(s, tiles).some((v) => isFoe(u, v))) push({ kind: 'self', x: u.x, y: u.y });
        break;
      }
      case 'nova':
      case 'detonate': {
        const hits = unitsOnTiles(s, radiusTiles(s, u.x, u.y, a.radius));
        if (hits.some((v) => isFoe(u, v) && worthy(v) && (a.dmg || (!v.nonCombat && !v.structure)))) push({ kind: 'self', x: u.x, y: u.y });
        break;
      }
      case 'pray':
      case 'drum': {
        const hits = unitsOnTiles(s, radiusTiles(s, u.x, u.y, a.radius, true));
        const useful = hits.some((v) => {
          if (v.team !== u.team || v.nonCombat || v.structure) return false;
          if (a.kind === 'drum' && v.frenzy === 0) return true;
          if (a.noHeal) return false;
          if (v.hp < v.maxHp && !v.poison) return true;
          return !!a.cleanse && !!(v.poison || v.para || v.burn || v.root);
        });
        if (useful) push({ kind: 'self', x: u.x, y: u.y });
        break;
      }
      case 'rally': {
        const hits = unitsOnTiles(s, radiusTiles(s, u.x, u.y, a.radius));
        if (hits.some((v) => v.team === u.team && !v.nonCombat && !v.structure && (v.wait > 0 || v.para > 0 || v.root > 0))) push({ kind: 'self', x: u.x, y: u.y });
        break;
      }
      case 'grow':
      case 'raise':
      case 'blink':
      case 'leap': {
        if (a.kind === 'raise' && raisedCount(s, u) >= (a.max || 3)) break;
        const [r0, r1] = a.range;
        for (const [x, y] of radiusTiles(s, u.x, u.y, r1)) {
          if (manhattan(u.x, u.y, x, y) < r0 || !emptyGrass(s, x, y)) continue;
          if (a.kind === 'leap') {
            const near = unitsOnTiles(s, radiusTiles(s, x, y, 1)).some((v) => v !== u && isFoe(u, v) && worthy(v));
            if (!near) continue;
          }
          push({ kind: 'tile', x, y });
        }
        break;
      }
      case 'heal':
      case 'shield': {
        const [r0, r1] = a.range;
        for (const v of s.units) {
          if (!v.alive || v.team !== u.team || v.nonCombat || v.structure) continue;
          const d = manhattan(u.x, u.y, v.x, v.y);
          if (d < r0 || d > r1) continue;
          if (a.kind === 'heal' && !((v.hp < v.maxHp && !v.poison) || (a.cure && (v.poison || v.burn)))) continue;
          if (a.kind === 'shield' && v.shield >= (a.amount || 15)) continue;
          push({ kind: 'unit', uid: v.uid, x: v.x, y: v.y });
        }
        break;
      }
      case 'hazard': {
        const [r0, r1] = a.range;
        for (const [x, y] of radiusTiles(s, u.x, u.y, r1, true)) {
          if (manhattan(u.x, u.y, x, y) < r0 || s.terrain[idx(s, x, y)] === T_ROCK) continue;
          if (a.hz === 'caltrops' && (!emptyGrass(s, x, y) || tileFx(s, x, y, 'caltrops'))) continue;
          push({ kind: 'tile', x, y });
        }
        break;
      }
      case 'revive': {
        const [r0, r1] = a.range;
        for (const v of s.units) {
          if (v.alive || v.team !== u.team || v.nonCombat || v.structure || v.revived || v.escaped || v.summoner) continue;
          const d = manhattan(u.x, u.y, v.x, v.y);
          if (d < r0 || d > r1 || !emptyGrass(s, v.x, v.y)) continue;
          push({ kind: 'tile', uid: v.uid, x: v.x, y: v.y });
        }
        break;
      }
    }
    return res;
  }

  // Targets for every act the unit can use right now.
  function allTargets(s, u) {
    const out = [];
    for (let i = 0; i < u.acts.length; i++) if (actUsable(s, u, i)) out.push(...targetsFrom(s, u, i));
    return out;
  }

  function sameTarget(a, b) {
    if (!a || !b || a.kind !== b.kind || (a.ai || 0) !== (b.ai || 0)) return false;
    if (a.kind === 'unit') return a.uid === b.uid;
    if (a.kind === 'dir') return a.d === b.d;
    if (a.kind === 'self') return true;
    return a.x === b.x && a.y === b.y;
  }

  function actOf(u, target) {
    return u.acts[(target && target.ai) || 0] || u.act;
  }

  function affectedTiles(s, u, target) {
    const a = actOf(u, target);
    if (target.kind === 'unit' && s.byId[target.uid]) {
      const v = s.byId[target.uid];
      target = Object.assign({}, target, { x: v.x, y: v.y });
    }
    switch (a.kind) {
      case 'strike':
      case 'heal':
      case 'shield':
      case 'shadowstrike':
      case 'grow':
      case 'raise':
      case 'blink':
      case 'revive':
        return [[target.x, target.y]];
      case 'cleave':
        return radiusTiles(s, u.x, u.y, 1);
      case 'quake':
        return radiusTiles(s, target.x, target.y, 1, true);
      case 'blast':
      case 'hazard':
        return patternTiles(s, a.pattern || 'single', target.x, target.y);
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
      case 'detonate':
      case 'rally':
        return radiusTiles(s, u.x, u.y, a.radius);
      case 'pray':
      case 'drum':
        return radiusTiles(s, u.x, u.y, a.radius, true);
      case 'leap':
        return [[target.x, target.y], ...radiusTiles(s, target.x, target.y, 1)];
    }
    return [];
  }

  // Units an action would touch, in resolution order.
  function affectedUnits(s, u, target) {
    const a = actOf(u, target);
    const tiles = affectedTiles(s, u, target);
    switch (a.kind) {
      case 'strike':
      case 'shadowstrike':
      case 'heal':
      case 'shield': {
        const v = s.byId[target.uid];
        return v && v.alive ? [v] : [];
      }
      case 'leap':
        return unitsOnTiles(s, tiles.slice(1)).filter((v) => v !== u && isFoe(u, v));
    }
    const units = unitsOnTiles(s, tiles).filter((v) => v !== u || a.kind === 'pray' || a.kind === 'drum');
    switch (a.kind) {
      case 'cleave':
      case 'quake':
      case 'cross':
        return units.filter((v) => isFoe(u, v));
      case 'nova':
        return units.filter((v) => isFoe(u, v) && (a.dmg || (!v.nonCombat && !v.structure)));
      case 'blast':
      case 'line':
      case 'cone':
        return units.filter((v) => (a.ff ? v.alive : isFoe(u, v)) && (a.dmg || (!v.nonCombat && !v.structure)));
      case 'detonate':
        return units.filter((v) => v.alive);
      case 'pray':
      case 'drum':
      case 'rally':
        return units.filter((v) => v.team === u.team && !v.nonCombat && !v.structure);
    }
    return [];
  }

  function facingToward(u, target) {
    if (target.kind === 'dir') return target.d;
    if (target.kind === 'self') return -1;
    if (target.x === u.x && target.y === u.y) return -1;
    return dirFromDelta(target.x - u.x, target.y - u.y);
  }

  // Predicted outcome of an action, without rolling dice.
  // ctx: { moved, moveDist } (defaults to the live activation)
  function previewAction(s, u, target, ctx) {
    const a = actOf(u, target);
    const c = ctx || (s.act && s.act.uid === u.uid ? { moved: s.act.moved && !s.act.acted, moveDist: s.act.moveDist } : { moved: false, moveDist: 0 });
    const tiles = affectedTiles(s, u, target);
    const effects = [];
    const run = () => {
      const opts = { moved: c.moved, moveDist: c.moveDist, act: a };
      if (a.kind === 'shadowstrike') opts.cat = 'back';
      const fx = hitFx(u, a);
      for (const v of affectedUnits(s, u, target)) {
        const e = { uid: v.uid, friendly: v.team === u.team };
        if (a.kind === 'pray' || a.kind === 'heal') {
          const cures = (a.cleanse && (v.poison || v.para || v.burn || v.root)) || (a.cure && (v.poison || v.burn));
          e.heal = v.poison && !cures ? 0 : Math.min(healAmount(u, a), v.maxHp - v.hp);
          if (cures) e.cleanse = true;
        } else if (a.kind === 'drum') {
          if (!a.noHeal) e.heal = v.poison ? 0 : Math.min(healAmount(u, a), v.maxHp - v.hp);
          e.frenzy = 2;
        } else if (a.kind === 'shield') e.shield = a.amount || 15;
        else if (a.kind === 'rally') e.rally = true;
        else {
          if (a.dmg) {
            const r = calcHit(s, u, v, opts);
            e.dmg = r.dmg;
            e.block = r.block;
            e.cat = r.cat;
            const bonus = u.props.bonusMagic ? u.props.bonusMagic : 0;
            e.kill = r.dmg + bonus >= v.hp + v.shield && !v.secondWind && !v.phoenix;
          }
          if (!e.friendly) {
            if (fx.para) e.para = statusImmune(s, v, 'para') ? 'resist' : fx.para;
            if (fx.poison) e.poison = statusImmune(s, v, 'poison') ? 'resist' : { turns: fx.poison[0], dmg: fx.poison[1] };
            if (fx.burn) e.burn = { turns: fx.burn[0], dmg: fx.burn[1] };
            if (fx.root) e.root = statusImmune(s, v, 'root') ? 'resist' : fx.root;
            if (fx.weak) e.weak = fx.weak;
            if (fx.mark) e.mark = fx.mark;
            if (fx.knock) e.knock = statusImmune(s, v, 'knock') ? 'resist' : true;
          }
        }
        effects.push(e);
      }
    };
    if (a.kind === 'leap') withUnitAt(s, u, target.x, target.y, run);
    else if (a.kind === 'shadowstrike') withUnitAt(s, u, target.bx, target.by, run);
    else run();
    if (a.kind === 'detonate') effects.push({ uid: u.uid, friendly: true, self: true, dmg: u.hp, kill: true, block: 0 });
    return { tiles, effects };
  }

  // ------------------------------------------------------------ resolution

  function emit(s, ev) {
    s.events.push(ev);
  }

  function heal(s, u, amount, why) {
    if (!u.alive || u.nonCombat || u.structure) return 0;
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

  function cleanse(s, v, all) {
    let any = false;
    if (v.poison) {
      v.poison = null;
      any = true;
    }
    if (v.burn) {
      v.burn = null;
      any = true;
    }
    if (all && (v.para || v.root)) {
      v.para = 0;
      v.root = 0;
      any = true;
    }
    if (any) emit(s, { t: 'cleanse', uid: v.uid });
    return any;
  }

  function revive(s, u, frac, why) {
    u.alive = true;
    u.hp = Math.max(1, Math.ceil(u.maxHp * frac));
    u.poison = null;
    u.burn = null;
    u.para = 0;
    u.root = 0;
    u.weak = 0;
    u.mark = 0;
    u.shield = 0;
    s.occ[idx(s, u.x, u.y)] = u.uid;
    emit(s, { t: 'revive', uid: u.uid, hp: u.hp, why });
  }

  function kill(s, u, src) {
    u.alive = false;
    u.hp = 0;
    s.occ[idx(s, u.x, u.y)] = 0;
    if (s.act && s.act.uid === u.uid) {
      // Died mid-action (thorns, a counterattack or its own blast): its turn is over.
      s.act = null;
      s.spent = true;
      u.activated = true;
      u.wait = cooldown(u);
      stamp(s, u, 'wait');
    }
    emit(s, { t: 'death', uid: u.uid, src: src ? src.uid : 0 });
    if (src && src.team !== u.team && !u.nonCombat && !u.structure) {
      s.stats.kills[src.team]++;
      src.kills++;
      if (s.act && s.act.uid === src.uid) s.act.killed = true;
      if (src.traits.has('midas') && src.team === 'P') {
        s.stats.gold += 6;
        emit(s, { t: 'gold', uid: src.uid, amount: 6 });
      }
    }
    if (u.traits.has('volatile') && !u.exploded) {
      u.exploded = true;
      s.booms.push({ x: u.x, y: u.y, dmg: u.props.boom || 15, src: u });
    }
    if (u.traits.has('martyr')) {
      for (const v of s.units)
        if (v.alive && v.team === u.team && manhattan(u.x, u.y, v.x, v.y) <= 2) heal(s, v, 20, 'martyr');
    }
    if (u.traits.has('spawner')) {
      let n = 0;
      for (const w of s.waves) {
        if (w.src !== u.uid || w.state !== 'pending') continue;
        w.state = 'cancelled';
        n += w.units.length;
      }
      if (n) emit(s, { t: 'waveCancel', uid: u.uid, n });
    }
    // The raised dead crumble with their master.
    for (const v of s.units) {
      if (v.alive && v.summoner === u.uid && v.type === 'skeleton') {
        v.alive = false;
        v.hp = 0;
        s.occ[idx(s, v.x, v.y)] = 0;
        emit(s, { t: 'wither', uid: v.uid, crumble: true });
      }
    }
    if (u.nonCombat || u.structure) return;
    if (u.phoenix && !u.phoenixUsed && !at(s, u.x, u.y)) {
      u.phoenixUsed = true;
      revive(s, u, 0.5, 'phoenix');
      return;
    }
    if (s.relics[u.team].has('phoenix_feather') && !s.phoenixUsed[u.team] && !at(s, u.x, u.y)) {
      s.phoenixUsed[u.team] = true;
      revive(s, u, 0.5, 'phoenix');
    }
  }

  function applyDamage(s, src, tgt, amount, info) {
    if (!tgt.alive || amount <= 0) return 0;
    if (tgt.shield > 0 && info.dmgType !== 'poison') {
      const ab = Math.min(tgt.shield, amount);
      tgt.shield -= ab;
      amount -= ab;
      emit(s, { t: 'absorb', uid: tgt.uid, amount: ab, left: tgt.shield });
      if (amount <= 0) return 0;
    }
    if (info.dmgType === 'magic' || info.dmgType === 'burn') tgt.scorched = true;
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

  // Magic damage that is not an attack: bonus magic, zaps, burns, fire and explosions.
  function magicDamage(s, src, tgt, base, why) {
    if (!tgt.alive) return 0;
    let dmg = base * (1 - effRes(s, tgt)) * (1 - magicGuard(s, tgt));
    if (tgt.mark > 0) dmg *= 1.25;
    dmg = Math.max(1, Math.round(dmg));
    return applyDamage(s, src, tgt, dmg, { cat: 'none', dmgType: why === 'burn' ? 'burn' : 'magic' });
  }

  function hit(s, atk, tgt, opts) {
    if (!tgt.alive) return { blocked: false, dmg: 0 };
    const act = opts.act || atk.act;
    const r = calcHit(s, atk, tgt, opts);
    const dmgType = opts.dmgType || act.dmg;
    if (r.block > 0 && s.rng.next() < r.block) {
      emit(s, { t: 'block', uid: tgt.uid, src: atk.uid, cat: r.cat });
      reactToMelee(s, atk, tgt, opts);
      return { blocked: true, dmg: 0 };
    }
    const dealt = applyDamage(s, atk, tgt, r.dmg, { cat: r.cat, dmgType });
    if (atk.alive && !opts.noBonus && atk.props.bonusMagic && tgt.alive) magicDamage(s, atk, tgt, atk.props.bonusMagic, 'bonus');
    if (dealt > 0 && atk.alive && !opts.noDrain) {
      let ls = atk.props.lifesteal || 0;
      if (s.relics[atk.team].has('bloodstone') && !atk.nonCombat) ls += 0.2;
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
    const dmgType = opts.dmgType || (opts.act || atk.act).dmg;
    if (manhattan(fx, fy, tgt.x, tgt.y) !== 1 || !dmgType || dmgType === 'true') return;
    let thorns = tgt.props.thorns || 0;
    if (!tgt.nonCombat && !tgt.structure && s.relics[tgt.team].has('thorned_mail') && dmgType === 'phys') thorns += 5;
    if (thorns > 0) {
      emit(s, { t: 'thorns', uid: atk.uid, src: tgt.uid });
      applyDamage(s, tgt, atk, thorns, { cat: 'none', dmgType: 'true' });
    }
    if (atk.alive && tgt.alive && tgt.traits.has('retaliate') && tgt.para === 0) {
      emit(s, { t: 'retaliate', uid: tgt.uid, target: atk.uid });
      hit(s, tgt, atk, { mult: 0.5, dmgType: 'phys', act: { dmg: 'phys' }, noReact: true, noDrain: true, noBonus: true });
    }
  }

  // Remember the turn a timed status landed in: it starts counting down from the next turn
  // that counts for it, so "roots for 2 turns" always costs its victim two turns.
  function stamp(s, u, k) {
    u.fresh = u.fresh || {};
    u.fresh[k] = s.ply;
  }

  function applyStatus(s, src, u, fx) {
    if (!u.alive || u.nonCombat || u.structure) return;
    if (fx.para) {
      if (statusImmune(s, u, 'para')) emit(s, { t: 'resist', uid: u.uid });
      else {
        u.para = Math.max(u.para, fx.para);
        stamp(s, u, 'para');
        emit(s, { t: 'status', uid: u.uid, status: 'para', turns: u.para });
      }
    }
    if (fx.poison) {
      if (statusImmune(s, u, 'poison')) emit(s, { t: 'resist', uid: u.uid });
      else {
        const p = u.poison;
        u.poison = { turns: Math.max(fx.poison[0], p ? p.turns : 0), dmg: Math.max(fx.poison[1], p ? p.dmg : 0), src: src.uid };
        emit(s, { t: 'status', uid: u.uid, status: 'poison', turns: u.poison.turns });
      }
    }
    if (fx.burn) {
      const p = u.burn;
      u.burn = { turns: Math.max(fx.burn[0], p ? p.turns : 0), dmg: Math.max(fx.burn[1], p ? p.dmg : 0), src: src.uid };
      emit(s, { t: 'status', uid: u.uid, status: 'burn', turns: u.burn.turns });
    }
    if (fx.root) {
      if (statusImmune(s, u, 'root')) emit(s, { t: 'resist', uid: u.uid });
      else {
        u.root = Math.max(u.root, fx.root);
        stamp(s, u, 'root');
        emit(s, { t: 'status', uid: u.uid, status: 'root', turns: u.root });
      }
    }
    if (fx.weak) {
      u.weak = Math.max(u.weak, fx.weak);
      stamp(s, u, 'weak');
      emit(s, { t: 'status', uid: u.uid, status: 'weak', turns: u.weak });
    }
    if (fx.mark) {
      u.mark = Math.max(u.mark, fx.mark);
      stamp(s, u, 'mark');
      emit(s, { t: 'status', uid: u.uid, status: 'mark', turns: u.mark });
    }
    if (fx.knock && u.alive) knockback(s, src, u);
  }

  // Shove a unit one tile away from `src`. If something is in the way it slams into it.
  function knockback(s, src, u) {
    if (statusImmune(s, u, 'knock')) {
      emit(s, { t: 'resist', uid: u.uid, why: 'steady' });
      return;
    }
    let d = dirFromDelta(u.x - src.x, u.y - src.y);
    if (d < 0) d = src.facing >= 0 ? src.facing : 0;
    const nx = u.x + DIRS[d][0];
    const ny = u.y + DIRS[d][1];
    const flying = u.traits.has('flying');
    const t = inB(s, nx, ny) ? s.terrain[idx(s, nx, ny)] : T_ROCK;
    const ok = inB(s, nx, ny) && !at(s, nx, ny) && (t === T_GRASS || (flying && t !== T_ROCK));
    if (!ok) {
      emit(s, { t: 'slam', uid: u.uid, x: nx, y: ny });
      applyDamage(s, src, u, 6, { cat: 'none', dmgType: 'true' });
      return;
    }
    relocate(s, u, nx, ny);
    emit(s, { t: 'push', uid: u.uid, x: nx, y: ny });
    enterTile(s, u, nx, ny);
  }

  // Hostile hazards trigger when a walking unit steps onto them. Returns true if it must stop.
  function enterTile(s, u, x, y) {
    if (!u.alive || u.traits.has('flying')) return false;
    let stop = false;
    for (const f of s.tfx.slice()) {
      if (f.x !== x || f.y !== y || f.team === u.team) continue;
      if (f.kind === 'fire') {
        emit(s, { t: 'scorch', uid: u.uid, x, y });
        magicDamage(s, s.byId[f.src] || null, u, f.dmg || FIRE_DMG, 'burn');
      } else if (f.kind === 'caltrops') {
        s.tfx.splice(s.tfx.indexOf(f), 1);
        emit(s, { t: 'trap', uid: u.uid, x, y });
        applyDamage(s, s.byId[f.src] || null, u, 6, { cat: 'none', dmgType: 'true' });
        if (u.alive && !statusImmune(s, u, 'root')) {
          u.root = Math.max(u.root, 1);
          stamp(s, u, 'root');
          emit(s, { t: 'status', uid: u.uid, status: 'root', turns: u.root });
        }
        stop = true;
      }
      if (!u.alive) return true;
    }
    return stop;
  }

  function relocate(s, u, x, y) {
    s.occ[idx(s, u.x, u.y)] = 0;
    u.x = x;
    u.y = y;
    s.occ[idx(s, x, y)] = u.uid;
  }

  function summonShrub(s, u, x, y) {
    const cap = 3 + (u.props.shrubs || 0);
    const mine = s.units.filter((v) => v.alive && v.type === 'shrub' && v.summoner === u.uid).sort((a, b) => a.born - b.born);
    while (mine.length >= cap) {
      const old = mine.shift();
      old.alive = false;
      s.occ[idx(s, old.x, old.y)] = 0;
      emit(s, { t: 'wither', uid: old.uid });
    }
    const thorn = u.traits.has('thornwall');
    const iron = u.traits.has('ironwood');
    const shrub = addUnit(s, {
      type: 'shrub',
      team: u.team,
      x,
      y,
      summoner: u.uid,
      born: ++s.summonCount,
      thorns: thorn ? 6 : 0,
      baseHp: Math.round(18 * D.LEVEL_HP[u.level] * (thorn ? 2 : 1)),
      armor: iron ? 0.4 : 0,
      res: iron ? 0.4 : 0,
    });
    emit(s, { t: 'summon', uid: shrub.uid, x, y, by: u.uid });
  }

  function raiseDead(s, u, x, y) {
    const sk = addUnit(s, { type: 'skeleton', team: u.team, x, y, summoner: u.uid, born: ++s.summonCount, facing: u.team === 'P' ? 0 : 2 });
    sk.activated = true;
    sk.value *= 0.6;
    emit(s, { t: 'summon', uid: sk.uid, x, y, by: u.uid, raise: true });
  }

  // Explosions resolve one at a time; each may set off more.
  function resolveBooms(s) {
    let guard = 0;
    while (s.booms.length && guard++ < 50) {
      const b = s.booms.shift();
      const tiles = radiusTiles(s, b.x, b.y, 1, true);
      emit(s, { t: 'boom', x: b.x, y: b.y, tiles });
      for (const v of unitsOnTiles(s, tiles)) {
        if (!v.alive || v === b.src) continue;
        magicDamage(s, b.src, v, b.dmg, 'boom');
      }
    }
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
    A.noUndo = true;
    l.taken = true;
    l.by = uid;
    emit(s, { t: 'loot', uid, kind: l.kind, id: l.id, x: u.x, y: u.y });
    return true;
  }

  // ------------------------------------------------------------ activation

  function hasAction(u) {
    if (u.move > 0 && !u.traits.has('immobile')) return true;
    return u.acts.some((a) => a.kind !== 'none' && a.left > 0);
  }

  function canActivate(s, u) {
    return !!(u && !s.over && !s.spent && u.team === s.side && canActivateFor(s, u, u.team));
  }

  function readyUnits(s, team) {
    return s.units.filter((u) => u.team === team && canActivateFor(s, u, team));
  }

  function canActivateFor(s, u, team) {
    return !!(u.alive && u.team === team && !u.activated && u.wait === 0 && u.para === 0 && !u.nonCombat && hasAction(u));
  }

  function beginActivation(s, uid) {
    const u = s.byId[uid];
    if (s.act) {
      if (s.act.uid === uid) return true;
      if (s.act.moved || s.act.acted) return false;
      cancelActivation(s);
    }
    if (!canActivate(s, u)) return false;
    s.act = { uid, sx: u.x, sy: u.y, sf: u.facing, moved: false, acted: false, moveDist: 0, movedBeforeAct: false, killed: false, blinked: false, noUndo: false };
    return true;
  }

  function cancelActivation(s) {
    const A = s.act;
    if (!A || A.moved || A.acted) return;
    // A facing picked for a turn that never happened is undone too.
    const u = s.byId[A.uid];
    if (A.face != null && u.alive && u.facing !== A.sf) {
      u.facing = A.sf;
      emit(s, { t: 'face', uid: u.uid, facing: u.facing });
    }
    s.act = null;
  }

  // Pick where the active unit faces when its turn ends, and turn it now. Moving and
  // attacking still turn it along the way; finishing turns it back to this choice.
  function turnUnit(s, uid, d) {
    const A = s.act;
    const u = s.byId[uid];
    if (!A || A.uid !== uid || s.over || u.facing < 0 || !(d >= 0 && d < 4)) return false;
    A.face = d;
    if (u.facing !== d) {
      u.facing = d;
      emit(s, { t: 'face', uid, facing: d });
    }
    return true;
  }

  function thunderstep(s, u) {
    if (!u.alive || !u.traits.has('thunderstep')) return;
    const near = unitsOnTiles(s, radiusTiles(s, u.x, u.y, 1)).filter((v) => isFoe(u, v) && !v.nonCombat && !v.structure);
    if (!near.length) return;
    emit(s, { t: 'zap', uid: u.uid, targets: near.map((v) => v.uid) });
    for (const v of near) magicDamage(s, u, v, 6, 'zap');
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
    relocate(s, u, x, y);
    A.moved = true;
    A.moveDist = path.length - 1;
    A.movedBeforeAct = !A.acted;
    if (u.facing >= 0 && path.length >= 2) {
      const a = path[path.length - 2];
      u.facing = dirFromDelta(x - a.x, y - a.y);
    }
    emit(s, { t: 'move', uid, path, facing: u.facing });
    const mark = s.events.length;
    // Fire along the way burns; a trap can only be the last tile (reachable stops there).
    for (let i = 1; i < path.length && u.alive; i++) enterTile(s, u, path[i].x, path[i].y);
    thunderstep(s, u);
    resolveBooms(s);
    if (s.events.length > mark) A.noUndo = true;
    checkOutcome(s);
    return path;
  }

  function canUndo(s) {
    const A = s.act;
    return !!(A && A.moved && !A.acted && !A.blinked && !A.noUndo);
  }

  function undoMove(s) {
    const A = s.act;
    if (!canUndo(s)) return false;
    const u = s.byId[A.uid];
    if (!u.alive) return false;
    relocate(s, u, A.sx, A.sy);
    u.facing = A.face != null ? A.face : A.sf;
    A.moved = false;
    A.moveDist = 0;
    A.movedBeforeAct = false;
    emit(s, { t: 'teleport', uid: u.uid, x: u.x, y: u.y, facing: u.facing });
    return true;
  }

  function performAction(s, uid, target) {
    const A = s.act;
    const u = s.byId[uid];
    if (!A || A.uid !== uid || s.over || !target) return false;
    const ai = target.ai || 0;
    if (!actUsable(s, u, ai)) return false;
    const legal = targetsFrom(s, u, ai).find((t) => sameTarget(t, target));
    if (!legal) return false;
    target = legal;
    const a = u.acts[ai];
    if (a.asMove) {
      A.moved = true;
      A.blinked = true;
      A.moveDist = 0;
      A.movedBeforeAct = !A.acted;
    } else A.acted = true;
    A.noUndo = true;
    if (a.left !== Infinity) a.left--;
    const opts = { moved: A.movedBeforeAct, moveDist: A.moveDist, fromX: u.x, fromY: u.y, act: a };
    const tiles = affectedTiles(s, u, target);
    const fd = facingToward(u, target);
    if (fd >= 0 && u.facing >= 0 && fd !== u.facing && a.kind !== 'leap' && a.kind !== 'blink') {
      u.facing = fd;
      emit(s, { t: 'face', uid, facing: fd });
    }
    emit(s, { t: 'action', uid, kind: a.kind, name: a.name, target, tiles, x: u.x, y: u.y, dmg: a.dmg || null, ai, hz: a.hz || null, fixed: a.fixed != null });
    const fx = hitFx(u, a);
    const strike = (v, o) => {
      if (!v.alive) return;
      let landed = true;
      if (a.dmg) landed = !hit(s, u, v, o || opts).blocked;
      if (landed && v.alive && v.team !== u.team && hasFx(fx)) applyStatus(s, u, v, fx);
    };
    switch (a.kind) {
      case 'strike':
      case 'quake':
      case 'line':
      case 'cone':
      case 'cross':
      case 'blast':
      case 'nova': {
        for (const v of affectedUnits(s, u, target)) {
          if (!u.alive) break;
          strike(v);
        }
        if (a.kind === 'strike' && u.traits.has('ridedown') && opts.moved && opts.moveDist >= 3) {
          const v = s.byId[target.uid];
          if (v && v.alive && u.alive) knockback(s, u, v);
        }
        break;
      }
      case 'cleave': {
        let struck = 0;
        for (const v of affectedUnits(s, u, target)) {
          if (!u.alive) break;
          strike(v);
          struck++;
        }
        if (u.traits.has('bloodrage') && u.alive) heal(s, u, 5 * struck, 'drain');
        break;
      }
      case 'shadowstrike': {
        const v = s.byId[target.uid];
        emit(s, { t: 'blink', uid, fx: u.x, fy: u.y, x: target.bx, y: target.by });
        relocate(s, u, target.bx, target.by);
        if (u.facing >= 0) {
          u.facing = dirFromDelta(v.x - u.x, v.y - u.y);
          emit(s, { t: 'face', uid, facing: u.facing });
        }
        strike(v, Object.assign({}, opts, { fromX: u.x, fromY: u.y, cat: 'back' }));
        if (u.alive) enterTile(s, u, u.x, u.y);
        break;
      }
      case 'leap': {
        emit(s, { t: 'leap', uid, fx: u.x, fy: u.y, x: target.x, y: target.y });
        relocate(s, u, target.x, target.y);
        let struck = 0;
        for (const v of affectedUnits(s, u, target)) {
          if (!u.alive) break;
          strike(v, Object.assign({}, opts, { fromX: u.x, fromY: u.y }));
          struck++;
        }
        if (u.traits.has('bloodrage') && u.alive) heal(s, u, 5 * struck, 'drain');
        if (u.alive) enterTile(s, u, u.x, u.y);
        break;
      }
      case 'blink': {
        emit(s, { t: 'blink', uid, fx: u.x, fy: u.y, x: target.x, y: target.y });
        relocate(s, u, target.x, target.y);
        if (u.alive) enterTile(s, u, u.x, u.y);
        thunderstep(s, u);
        break;
      }
      case 'detonate': {
        u.exploded = true;
        for (const v of affectedUnits(s, u, target)) strike(v, Object.assign({}, opts, { noReact: true }));
        if (u.alive) kill(s, u, null);
        break;
      }
      case 'pray':
        for (const v of affectedUnits(s, u, target)) {
          if (a.cleanse) cleanse(s, v, true);
          heal(s, v, healAmount(u, a), 'prayer');
        }
        break;
      case 'heal': {
        const v = s.byId[target.uid];
        if (a.cure) cleanse(s, v, false);
        heal(s, v, healAmount(u, a), 'prayer');
        break;
      }
      case 'drum':
        for (const v of affectedUnits(s, u, target)) {
          if (!a.noHeal) heal(s, v, healAmount(u, a), 'drum');
          v.frenzy = Math.max(v.frenzy, 2);
          stamp(s, v, 'frenzy');
          emit(s, { t: 'status', uid: v.uid, status: 'frenzy', turns: 2 });
        }
        break;
      case 'rally':
        for (const v of affectedUnits(s, u, target)) {
          v.wait = Math.max(0, v.wait - 1);
          v.para = 0;
          v.root = 0;
          emit(s, { t: 'rally', uid: v.uid, wait: v.wait });
        }
        break;
      case 'shield': {
        const v = s.byId[target.uid];
        v.shield = Math.max(v.shield, a.amount || 15);
        emit(s, { t: 'shield', uid: v.uid, amount: v.shield });
        break;
      }
      case 'hazard': {
        const placed = [];
        for (const [x, y] of tiles) {
          const t = s.terrain[idx(s, x, y)];
          if (t === T_ROCK) continue;
          if (a.hz === 'fire' && t !== T_GRASS) continue;
          if (a.hz === 'caltrops' && (t !== T_GRASS || at(s, x, y))) continue;
          const old = tileFx(s, x, y, a.hz);
          if (old) s.tfx.splice(s.tfx.indexOf(old), 1);
          s.tfx.push({ kind: a.hz, x, y, team: u.team, turns: a.turns || 2, dmg: a.dmgFixed || 0, src: u.uid });
          placed.push([x, y]);
        }
        emit(s, { t: 'hazard', kind: a.hz, tiles: placed, team: u.team });
        break;
      }
      case 'grow':
        summonShrub(s, u, target.x, target.y);
        break;
      case 'raise':
        raiseDead(s, u, target.x, target.y);
        break;
      case 'revive': {
        const v = s.byId[target.uid];
        if (v && !v.alive && emptyGrass(s, v.x, v.y)) {
          v.revived = true;
          revive(s, v, a.pct || 0.4, 'prayer');
          v.activated = true;
          v.wait = Math.max(v.wait, 1);
          stamp(s, v, 'wait');
        }
        break;
      }
    }
    resolveBooms(s);
    checkOutcome(s);
    return true;
  }

  function finishActivation(s, facing) {
    const A = s.act;
    if (!A) return;
    const u = s.byId[A.uid];
    s.act = null;
    if (!u.alive) return;
    if (facing == null && A.face != null) facing = A.face;
    if (facing != null && facing >= 0 && u.facing >= 0 && u.facing !== facing) {
      u.facing = facing;
      emit(s, { t: 'face', uid: u.uid, facing });
    }
    // Acting starts the cooldown: the unit sits out that many of its side's turns, and the
    // count drops at the end of each one (not the turn it acted in). Moving alone is free.
    let w = 0;
    if (A.acted) {
      w = cooldown(u);
      if (u.firstActionFree) {
        w = 0;
        u.firstActionFree = false;
      }
      if (A.killed && (u.traits.has('bloodlust') || s.relics[u.team].has('warlord_helm'))) w = 0;
    }
    u.wait = w;
    stamp(s, u, 'wait');
    u.activated = true;
    s.spent = true;
    emit(s, { t: 'done', uid: u.uid, wait: w });
  }

  // The CD on a unit's card: how many of its turns it sits out after acting.
  function cooldown(u) {
    return u.rec;
  }

  // Own turns a unit sits out before it can act again, seen from the other side's turn:
  // its cooldown, then any paralysis (which only wears off once the cooldown has).
  function turnsUntilReady(u) {
    return u.wait + u.para;
  }

  // Loot wagons trundle toward their exit edge at the end of their side's turn.
  function driveCarts(s, side) {
    for (const u of s.units) {
      if (!u.alive || u.team !== side || !u.traits.has('cart') || s.over) continue;
      const reach = reachable(s, u);
      let best = null;
      for (const r of reach.values()) {
        const k = Math.abs(r.x - s.cartExit) * 10 + Math.abs(r.y - u.y) + r.d * 0.01;
        if (!best || k < best.k) best = { r, k };
      }
      if (!best || best.r.d === 0) continue;
      const path = findPath(s, u, best.r.x, best.r.y);
      if (!path) continue;
      relocate(s, u, best.r.x, best.r.y);
      emit(s, { t: 'move', uid: u.uid, path, facing: u.facing });
      for (let i = 1; i < path.length && u.alive; i++) enterTile(s, u, path[i].x, path[i].y);
      if (u.alive && u.x === s.cartExit) {
        u.alive = false;
        u.escaped = true;
        s.occ[idx(s, u.x, u.y)] = 0;
        s.stats.escaped++;
        emit(s, { t: 'escape', uid: u.uid, x: u.x, y: u.y });
      }
    }
    resolveBooms(s);
  }

  // ------------------------------------------------------------ reinforcements

  const BLOCK_DMG = 10;
  const FIRE_DMG = 6;

  function pendingWaves(s, team) {
    let n = 0;
    for (const w of s.waves) if (w.state === 'pending' && w.team === team) n += w.units.length;
    return n;
  }

  // Free tiles where a wave's units step onto the field: around its building, front first,
  // or anywhere along its edge.
  function spawnTiles(s, w, n, taken) {
    const ok = (x, y) => inB(s, x, y) && s.terrain[idx(s, x, y)] === T_GRASS && !s.occ[idx(s, x, y)] && !taken.has(idx(s, x, y));
    const src = w.src ? s.byId[w.src] : null;
    let cands = [];
    if (src) {
      const ahead = w.team === 'E' ? 1 : -1;
      for (let r = 1; r <= 3 && cands.length < n; r++) {
        const ring = [];
        for (let dx = -r; dx <= r; dx++) {
          for (const dy of [r - Math.abs(dx), Math.abs(dx) - r]) {
            if (ring.some((c) => c[0] === src.x + dx && c[1] === src.y + dy)) continue;
            if (ok(src.x + dx, src.y + dy)) ring.push([src.x + dx, src.y + dy, dy * ahead, Math.abs(dx)]);
          }
        }
        ring.sort((a, b) => b[2] - a[2] || a[3] - b[3]);
        cands.push(...ring);
      }
    } else {
      cands = s.rng.shuffle((w.tiles || []).filter(([x, y]) => ok(x, y)));
    }
    const out = [];
    for (const c of cands) {
      if (out.length >= n) break;
      taken.add(idx(s, c[0], c[1]));
      out.push([c[0], c[1]]);
    }
    return out;
  }

  // Mark where `team`'s waves due by turn `upTo` will appear, so the other side gets a turn
  // to see them coming.
  function planWaves(s, team, upTo) {
    const taken = new Set();
    for (const w of s.waves) if (w.state === 'pending' && w.marks) for (const [x, y] of w.marks) taken.add(idx(s, x, y));
    for (const w of s.waves) {
      if (w.state !== 'pending' || w.team !== team || w.marks || w.turn > upTo) continue;
      w.marks = spawnTiles(s, w, w.units.length, taken);
      emit(s, { t: 'waveWarn', i: w.i, marks: w.marks });
    }
  }

  // At the end of a team's turn its due waves arrive. A foe standing on a marked tile
  // blocks that arrival and takes the hit.
  function spawnWaves(s, team) {
    for (const w of s.waves) {
      if (w.state !== 'pending' || w.team !== team || w.turn > s.turn) continue;
      const src = w.src ? s.byId[w.src] : null;
      if (src && !src.alive) {
        w.state = 'cancelled';
        continue;
      }
      const taken = new Set();
      const marks = w.marks || spawnTiles(s, w, w.units.length, taken);
      const spawned = [];
      let blocked = 0;
      w.units.forEach((spec, k) => {
        let tile = marks[k] || null;
        if (tile) {
          const o = at(s, tile[0], tile[1]);
          if (o && o.team !== team) {
            blocked++;
            if (o.team === 'P') s.stats.blocked++;
            emit(s, { t: 'spawnBlock', uid: o.uid, x: tile[0], y: tile[1], type: spec.type });
            applyDamage(s, null, o, BLOCK_DMG, { cat: 'none', dmgType: 'true' });
            return;
          }
          if (o) tile = null;
        }
        if (!tile) tile = spawnTiles(s, w, 1, taken)[0];
        if (!tile) return;
        const u = addUnit(s, Object.assign({}, spec, { team, x: tile[0], y: tile[1], facing: team === 'E' ? 2 : 0, born: s.turn }));
        spawned.push(u.uid);
      });
      w.state = 'done';
      emit(s, { t: 'wave', i: w.i, src: w.src, uids: spawned, blocked });
    }
  }

  // What is still coming, for the battle panel and the board.
  function waveSummary(s) {
    return s.waves
      .filter((w) => w.state === 'pending')
      .map((w) => ({ i: w.i, team: w.team, turn: w.turn, in: w.turn - s.turn, src: w.src, types: w.units.map((u) => u.type), marks: w.marks }));
  }

  // ---------------------------------------------------------------- turns
  //
  // The sides take turns, the enemy first. A turn is one unit's activation: it moves, acts,
  // or both, then faces. Acting starts that unit's cooldown: it sits out that many of its
  // side's turns, and any unit at 0 may be picked. A side with nothing it can do passes on
  // its own. "Turn N" on the board counts rounds: the enemy's move, then yours.
  //
  // A turn opens with poison, burns, healing and auras for the side to move. It closes with
  // that side's cooldowns and statuses ticking down, its wagons rolling and its
  // reinforcements arriving.

  // A ready unit that can actually do something: move somewhere, or reach a target.
  function usefulUnit(s, u) {
    if (u.move > 0 && !u.traits.has('immobile') && u.root === 0 && reachable(s, u).size > 1) return true;
    return allTargets(s, u).length > 0;
  }

  function hasMove(s, team) {
    return readyUnits(s, team).some((u) => usefulUnit(s, u));
  }

  // End the turn of the side to move: its activation (if any) is done, and the other side
  // is up. Sides with nothing to do pass on their own (`auto` marks such a pass).
  function endTurn(s, auto) {
    if (s.over) return;
    if (s.act) {
      if (s.act.moved || s.act.acted) finishActivation(s, null);
      else s.act = null;
    }
    if (!s.spent) emit(s, { t: 'pass', side: s.side, auto: !!auto });
    // Bounded: cooldowns run out, and the turn limit ends the battle well before this.
    for (let guard = 0; guard < 1000 && !s.over; guard++) {
      closeTurn(s, s.side);
      if (s.over) return;
      s.side = other(s.side);
      if (s.side === 'E') s.turn++;
      s.ply++;
      startTurn(s);
      if (s.over || hasMove(s, s.side)) return;
      emit(s, { t: 'pass', side: s.side, auto: true });
    }
  }

  // Skip this turn without moving anyone.
  function pass(s) {
    endTurn(s);
  }

  // Timed statuses count the turns of the side they matter to: cooldowns, roots, weakness,
  // paralysis and frenzy the unit's own, marks those of its enemies (who get the bonus). A
  // count set during this turn starts with the next one. Paralysis waits for the cooldown
  // to run out, so it always costs a turn the unit could have used.
  function closeTurn(s, side) {
    for (const u of s.units) {
      if (!u.alive) continue;
      const fresh = u.fresh || {};
      const tick = (k) => {
        if (u[k] > 0 && fresh[k] !== s.ply) u[k]--;
      };
      if (u.team === side) {
        if (u.wait > 0) tick('wait');
        else tick('para');
        tick('root');
        tick('weak');
        tick('frenzy');
        u.activated = false;
      } else tick('mark');
    }
    driveCarts(s, side);
    checkOutcome(s);
    if (s.over) return;
    spawnWaves(s, side);
    checkOutcome(s);
  }

  function tickDot(s, u, kind) {
    const p = u[kind];
    if (!p || !u.alive) return;
    const src = s.byId[p.src] || null;
    if (kind === 'poison') applyDamage(s, src, u, p.dmg, { cat: 'none', dmgType: 'poison' });
    else magicDamage(s, src, u, p.dmg, 'burn');
    if (!u.alive || !u[kind]) return;
    p.turns--;
    if (p.turns <= 0) {
      u[kind] = null;
      emit(s, { t: 'cure', uid: u.uid, status: kind });
    }
  }

  // What happens to a team at the start of its turn.
  function startEffects(s, team) {
    // Hazards fade at the start of their owner's turns.
    const before = s.tfx.length;
    s.tfx = s.tfx.filter((f) => f.team !== team || --f.turns > 0);
    if (s.tfx.length !== before) emit(s, { t: 'hazardEnd' });
    const mine = s.units.filter((u) => u.alive && u.team === team);
    for (const u of mine) {
      tickDot(s, u, 'poison');
      tickDot(s, u, 'burn');
      if (!u.alive || u.traits.has('flying')) continue;
      const fire = tileFx(s, u.x, u.y, 'fire');
      if (fire && fire.team !== team) {
        emit(s, { t: 'scorch', uid: u.uid, x: u.x, y: u.y });
        magicDamage(s, s.byId[fire.src] || null, u, fire.dmg || FIRE_DMG, 'burn');
      }
    }
    for (const u of mine) {
      if (!u.alive || u.nonCombat) continue;
      if (u.props.regen) {
        if (u.traits.has('trollblood') && u.scorched) emit(s, { t: 'noregen', uid: u.uid });
        else heal(s, u, u.props.regen, 'regrowth');
      }
      u.scorched = false;
      if (s.relics[team].has('sacred_chalice')) heal(s, u, 2, 'chalice');
    }
    // Totems mend allies within 2 tiles. Several totems in reach do not stack.
    const totems = mine.filter((w) => w.alive && w.props.totemHeal);
    if (totems.length) {
      const pulsed = new Set();
      for (const v of mine) {
        if (!v.alive || v.nonCombat || v.structure || v.hp >= v.maxHp) continue;
        let best = null;
        for (const w of totems) if (manhattan(v.x, v.y, w.x, w.y) <= 2 && (!best || w.props.totemHeal > best.props.totemHeal)) best = w;
        if (!best) continue;
        if (!pulsed.has(best.uid)) {
          pulsed.add(best.uid);
          emit(s, { t: 'totem', uid: best.uid });
        }
        heal(s, v, best.props.totemHeal, 'totem');
      }
    }
    for (const w of mine) {
      if (!w.alive || !w.traits.has('aura_barrier')) continue;
      const mend = w.traits.has('auramend');
      const purge = w.traits.has('purge');
      if (!mend && !purge) continue;
      for (const v of s.units) {
        if (!v.alive || v.team !== team || v.nonCombat || v.structure || manhattan(v.x, v.y, w.x, w.y) > auraRadius(w)) continue;
        if (purge && (v.root || v.burn)) {
          v.root = 0;
          v.burn = null;
          emit(s, { t: 'cleanse', uid: v.uid });
        }
        if (mend) heal(s, v, 3, 'aura');
      }
    }
    for (const u of mine) {
      if (!u.alive || !u.traits.has('stormcaller')) continue;
      let best = null;
      for (const v of s.units) {
        if (!isFoe(u, v) || v.nonCombat || v.structure) continue;
        const d = manhattan(u.x, u.y, v.x, v.y);
        if (d <= 3 && (!best || d < best.d || (d === best.d && v.hp < best.v.hp))) best = { v, d };
      }
      if (best) {
        emit(s, { t: 'zap', uid: u.uid, targets: [best.v.uid] });
        magicDamage(s, u, best.v, 5, 'zap');
      }
    }
    resolveBooms(s);
    if (s.relics[team].has('healing_salve')) {
      let best = null;
      for (const u of s.units) {
        if (!u.alive || u.team !== team || u.nonCombat || u.structure || u.poison) continue;
        if (!best || u.maxHp - u.hp > best.maxHp - best.hp) best = u;
      }
      if (best && best.hp < best.maxHp) heal(s, best, 4, 'salve');
    }
  }

  // The battle is decided. `s.end` keeps why, after the events have been played.
  function finish(s, winner, why) {
    s.over = true;
    s.winner = winner;
    s.act = null;
    s.end = Object.assign({ t: 'end', winner }, why);
    emit(s, s.end);
  }

  function startTurn(s) {
    const side = s.side;
    s.spent = false;
    emit(s, { t: 'turn', side, turn: s.turn });
    if (side === 'E') {
      if (s.turn > s.turnLimit) {
        s.timeout = true;
        return finish(s, strength(s, 'P') > strength(s, 'E') ? 'P' : 'E', { timeout: true });
      }
      if (s.surviveTurns && s.turn > s.surviveTurns) return finish(s, 'P', { survived: true });
    }
    startEffects(s, side);
    checkOutcome(s);
    if (s.over) return;
    if (side === 'P' && s.hold) {
      const h = s.hold;
      const on = at(s, h.x, h.y);
      if (on && on.team === 'P' && !on.nonCombat) h.count++;
      else h.count = 0;
      emit(s, { t: 'hold', count: h.count, need: h.need, uid: on && on.team === 'P' ? on.uid : 0 });
      if (h.count >= h.need) return finish(s, 'P', { held: true });
    }
    // The other side's next waves mark where they land, a turn before they arrive.
    planWaves(s, other(side), side === 'P' ? s.turn + 1 : s.turn);
  }

  function canDealDamage(u) {
    return u.acts.some((a) => a.left > 0 && (a.dmg || (a.fx && a.fx.poison) || a.kind === 'raise'));
  }

  // Remaining fighting strength, used to settle battles that hit the turn limit.
  function strength(s, team) {
    let t = 0;
    for (const u of s.units) if (u.alive && u.team === team && !u.nonCombat && !u.structure) t += u.value * (u.hp / u.maxHp);
    return t;
  }

  // Units that must fall to defeat a side (not objects, structures or bound guardians).
  function counts(u) {
    return !u.nonCombat && !u.bound && !u.structure;
  }

  function checkOutcome(s) {
    if (s.over) return;
    const alive = { P: false, E: false };
    const armed = { P: false, E: false };
    let hasVip = false;
    let vipAlive = false;
    let hasObj = false;
    let objAlive = false;
    let objEscaped = false;
    for (const u of s.units) {
      if (u.vip && u.team === 'E') {
        hasVip = true;
        if (u.alive) vipAlive = true;
      }
      if (u.team === 'E' && u.goal) {
        hasObj = true;
        if (u.alive) objAlive = true;
        if (u.escaped) objEscaped = true;
      }
      if (u.alive && counts(u)) {
        alive[u.team] = true;
        if (canDealDamage(u)) armed[u.team] = true;
      }
    }
    // Reinforcements still on the way keep a side in the fight.
    for (const team of ['P', 'E']) {
      if (!pendingWaves(s, team)) continue;
      alive[team] = true;
      armed[team] = true;
    }
    const vipDown = (s.objective === 'boss' || s.objective === 'vip') && hasVip && !vipAlive;
    const objDown = s.objective === 'destroy' && hasObj && !objAlive && !objEscaped;
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
    if (winner) finish(s, winner, { surrender, vipSlain: vipDown, destroyed: objDown });
  }

  function forfeit(s) {
    if (!s.over) finish(s, 'E', { forfeit: true });
  }

  function drainEvents(s) {
    const ev = s.events;
    s.events = [];
    return ev;
  }

  AG.Engine = {
    T_GRASS, T_ROCK, T_WATER, T_LAVA,
    other, manhattan, idx, inB, at, dirFromDelta, unitValue, buildUnit, specMods,
    canDealDamage, strength, counts, createBattle, addUnit, withUnitAt, reachable, findPath,
    patternTiles, lineTiles, coneTiles, radiusTiles, tileFx, concealed,
    inBarrier, effArmor, effRes, guardianReduction, magicGuard, statusImmune, dirCategory, blockChance, calcHit,
    poisonDamage, healAmount, hitFx, actUsable, targetsFrom, allTargets, sameTarget, actOf, affectedTiles, affectedUnits,
    previewAction, facingToward, lootAt, canLoot, takeLoot, nearBanner,
    canActivate, canActivateFor, readyUnits, beginActivation, cancelActivation, turnUnit, moveUnit, undoMove, canUndo, performAction,
    finishActivation, cooldown, turnsUntilReady, pass, endTurn, hasMove, usefulUnit, checkOutcome, forfeit, drainEvents,
    BLOCK_DMG, pendingWaves, waveSummary,
  };
})(typeof window !== 'undefined' ? window : globalThis);
