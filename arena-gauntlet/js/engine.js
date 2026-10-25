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

  // An act's charges and its own cooldown. Actives have a few uses a battle that never come
  // back, and many a cooldown of their own: after one is used it waits that many of the
  // unit's turns (on top of the unit's own cooldown) before it can be used again.
  function prepAct(a) {
    const act = clone(a);
    act.uses = act.uses || 0;
    act.left = act.uses > 0 ? act.uses : Infinity;
    act.cd = act.cd || 0;
    act.cdLeft = 0;
    return act;
  }

  // Ready to be used as far as its own cooldown goes.
  const offCooldown = (a) => !(a.cdLeft > 0);

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
      if (rel.has('pathfinder') && move > 0 && move <= 3) move += 1;
      if (rel.has('mana_crystal') && T.rec >= 2) rec -= 1;
      if (rel.has('glass_crown')) hpPct -= 0.25;
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
      talents: (spec.talents || []).filter((id) => D.TALENTS[id] && D.TALENTS[id].cls === spec.type),
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
      spd: T.spd || 0,
      // Turns taken in the unit queue; a newcomer joins the current cycle.
      cycles: queueStart(s, team),
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
    // Regen: HP healed as the unit takes its turn, from its type, talents, gear and relics,
    // all added up. The Healing Salve only strengthens regen a unit has of its own; the
    // boss relic Sacred Chalice is the one army-wide source.
    if (!u.nonCombat && !u.structure) {
      const rel = s.relics[team];
      const own = u.props.regen || 0;
      u.regen = own + (own && rel.has('healing_salve') ? 2 : 0) + (rel.has('sacred_chalice') ? 2 : 0);
    } else u.regen = 0;
    if (spec.armor != null) u.armor = spec.armor;
    if (spec.res != null) u.res = spec.res;
    if (spec.vip && !T.boss) u.value *= 1.8;
    if (u.bound) u.value *= 0.5;
    if (spec.hpFrac) u.hp = Math.max(1, Math.round(u.maxHp * spec.hpFrac));
    if (u.props.startShield) u.shield = u.props.startShield;
    u.guardReady = true;
    u.watchReady = true;
    u.braced = traits.has('brace');
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
      // Relics that fire once at the start of a side's first turn, and the War Drum's beat.
      opened: { P: false, E: false },
      drummed: { P: 0, E: 0 },
      stats: { dmg: { P: 0, E: 0 }, kills: { P: 0, E: 0 }, gold: 0, escaped: 0, blocked: 0 },
      summonCount: 0,
      hold: cfg.hold ? { x: cfg.hold.x, y: cfg.hold.y, need: cfg.hold.need || 2, count: 0 } : null,
      surviveTurns: cfg.surviveTurns || 0,
      loot: (cfg.loot || []).map((l) => ({ id: l.id, kind: l.kind, x: l.x, y: l.y, taken: false, by: 0 })),
      // The player's bonus goals ({ type, ... }), for the AI that fights for them.
      goals: (cfg.goals || []).map((g) => Object.assign({}, g)),
      tfx: [],
      booms: [],
      cartExit: cfg.cartExit != null ? cfg.cartExit : 0,
      waves: [],
      // Queue battles: each side's units take its turns in a set rotation (see pickDue).
      queue: !!cfg.queue,
      due: 0,
      // Fatigue from this turn on (0: never); see startFatigue.
      overtime: cfg.overtime || 0,
    };
    for (const spec of cfg.units) addUnit(s, spec);
    armRelics(s);
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

  // Poisoned units cannot be healed.
  function healBlocked(s, u) {
    return !!u.poison;
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

  // A Barrier Ward's aura reaches 4 tiles (Wide Field, 5).
  function auraRadius(v) {
    return 4 + ((v.props && v.props.auraR) || 0);
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

  // A Barrier Ward's aura: +25% armor and +25% magic resistance (Steel Field adds 10% more
  // armor).
  function effArmor(s, u) {
    let a = u.armor;
    if (!u.nonCombat && !u.structure) {
      const b = inBarrier(s, u);
      if (b) a += 0.25 + (b.traits.has('steelfield') ? 0.1 : 0);
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
        if (tr.has('stoneskin') || tr.has('undead') || tr.has('poisonproof') || u.tags.has('construct')) return true;
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

  // Fighters on its own side standing right next to it (summons and buildings aside).
  function alliesNext(s, u) {
    let n = 0;
    for (const v of s.units) if (v !== u && v.alive && v.team === u.team && !v.nonCombat && !v.structure && manhattan(u.x, u.y, v.x, v.y) === 1) n++;
    return n;
  }

  function blockChance(s, tgt, cat) {
    if (tgt.facing < 0 || tgt.para > 0) return 0;
    let b = tgt.block;
    if (cat === 'side') b = tgt.traits.has('shieldwall') ? b : b / 2;
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
    if (relA.has('glass_crown') && !atk.nonCombat) mult *= 1.4;
    if (relA.has('titan_gauntlet')) mult *= 1.25;
    // Grown in this battle: trophies from kills, fury from wounds, souls harvested.
    if (atk.trophies) mult *= 1 + 0.1 * atk.trophies;
    if (atk.fury) mult *= 1 + 0.05 * atk.fury;
    if (atk.harvest) mult *= 1 + 0.1 * atk.harvest;
    if (atk.champion) mult *= 1.5;
    if (P.momentum && opts.moved) mult *= 1 + P.momentum * (opts.moveDist || 0);
    if (atk.charge) mult *= 1 + 0.25 * atk.charge;
    if (atk.sink) mult *= 1.5;
    if (atk.traits.has('opportunist') && (tgt.para > 0 || tgt.root > 0 || tgt.weak > 0)) mult *= 1.4;
    if (atk.traits.has('cruelsong') && tgt.para > 0) mult *= 1.5;
    if (relA.has('lone_wolf') && !atk.nonCombat && !alliesNext(s, atk)) mult *= 1.3;
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
    if (tgt.hp < tgt.maxHp / 2 && P.execMult) mult *= 1 + P.execMult;
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
    // Phalanx Standard: shoulder to shoulder with two allies or more.
    if (s.relics[tgt.team].has('phalanx_standard') && !tgt.nonCombat && !tgt.structure && alliesNext(s, tgt) >= 2) dmg *= 0.8;
    // Hold the Line: it has not moved since its last turn. Last Stand: nearly down.
    if (tgt.braced) dmg *= 0.7;
    if (tgt.traits.has('laststand') && tgt.hp < tgt.maxHp * 0.25) dmg *= 0.5;
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

  // Friendly fire: a damaging area attack (a cleave, a fireball, a volley, a pulse, a breath)
  // hits your own fighters in its area too, unless something makes it spare them: an
  // upgrade that sets ff false (Controlled Burn, Tamed Fire, Abyssal Bolt), a monster that
  // spares its own kind, or the Disciplined skill. Area spells that only hinder hit foes only.
  function hitsAllies(u, a) {
    return !!a.dmg && a.ff !== false && !u.traits.has('precise');
  }

  // Who an area act reaches besides its caster: foes, plus allied fighters on friendly fire.
  function inArea(u, a, v) {
    if (!v.alive) return false;
    if (v.team !== u.team) return true;
    return hitsAllies(u, a) && !v.nonCombat && !v.structure;
  }

  // Who a nova reaches: a damaging one (the Lightning Ward) hits buildings too; a poison
  // one (the Poison Wisp, Pestilence or not) never does, and neither does a pure status one.
  function novaHits(a, v) {
    if (!v.nonCombat && !v.structure) return true;
    return !!a.dmg && !(a.fx && a.fx.poison);
  }

  // A unit in smoke cannot be singled out from more than 1 tile away.
  function concealed(s, v, fx, fy) {
    if (manhattan(fx, fy, v.x, v.y) <= 1) return false;
    return !!tileFx(s, v.x, v.y, 'smoke') || (v.traits.has('unseen') && !v.revealed);
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
    if (!a || a.kind === 'none' || a.left <= 0 || !offCooldown(a)) return false;
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
    if (!a || a.kind === 'none' || a.left <= 0 || !offCooldown(a)) return res;
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
        if (hits.some((v) => isFoe(u, v) && worthy(v) && novaHits(a, v))) push({ kind: 'self', x: u.x, y: u.y });
        break;
      }
      case 'pray':
      case 'drum': {
        const hits = unitsOnTiles(s, radiusTiles(s, u.x, u.y, a.radius, true));
        const useful = hits.some((v) => {
          if (v.team !== u.team || v.nonCombat || v.structure) return false;
          if (a.kind === 'drum' && v.frenzy === 0) return true;
          if (a.noHeal) return false;
          if (v.hp < v.maxHp && !healBlocked(s, v)) return true;
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
          if (a.kind === 'heal' && !((v.hp < v.maxHp && !healBlocked(s, v)) || (a.cure && (v.poison || v.burn)))) continue;
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
        return unitsOnTiles(s, tiles.slice(1)).filter((v) => v !== u && inArea(u, a, v));
    }
    const units = unitsOnTiles(s, tiles).filter((v) => v !== u || a.kind === 'pray' || a.kind === 'drum');
    switch (a.kind) {
      case 'cleave':
      case 'quake':
      case 'cross':
        return units.filter((v) => inArea(u, a, v));
      case 'nova':
        return units.filter((v) => inArea(u, a, v) && novaHits(a, v));
      case 'blast':
      case 'line':
      case 'cone':
        return units.filter((v) => inArea(u, a, v) && (a.dmg || (!v.nonCombat && !v.structure)));
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
          if (!a.noHeal) e.heal = healBlocked(s, v) ? 0 : Math.min(healAmount(u, a), v.maxHp - v.hp);
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
            if (fx.poison) e.poison = statusImmune(s, v, 'poison') ? 'resist' : { turns: fx.poison[0], dmg: fx.poison[1], key: poisonKey(u, a) };
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
    if (healBlocked(s, u)) {
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
    u.cycles = Math.max(u.cycles, queueStart(s, u.team));
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
      onKill(s, src, u);
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
    deathTriggers(s, u, src);
    if (u.nonCombat || u.structure) return;
    if (u.phoenix && !u.phoenixUsed && !at(s, u.x, u.y)) {
      u.phoenixUsed = true;
      revive(s, u, 0.5, 'phoenix');
      return;
    }
    if (s.relics[u.team].has('phoenix_feather') && !s.phoenixUsed[u.team] && !at(s, u.x, u.y)) {
      s.phoenixUsed[u.team] = true;
      revive(s, u, 0.5, 'phoenix');
      return;
    }
    afterlife(s, u, src);
  }

  // What a kill earns the killer: trophies, a bite of health, gold, a cheer for its friends.
  function onKill(s, src, u) {
    const rel = s.relics[src.team];
    if (!src.nonCombat && (src.traits.has('trophy') || rel.has('trophy_rack')) && (src.trophies || 0) < 5) {
      src.trophies = (src.trophies || 0) + 1;
      emit(s, { t: 'trophy', uid: src.uid, n: src.trophies });
    }
    const feed = (src.props.killHeal || 0) + (rel.has('vampire_fang') && !src.nonCombat ? 8 : 0);
    if (feed) heal(s, src, feed, 'drain');
    if (src.team === 'P' && src.traits.has('hoarder')) {
      s.stats.gold += 8;
      emit(s, { t: 'gold', uid: src.uid, amount: 8 });
    }
    if (src.traits.has('pyroclasm')) placeFire(s, src, [[u.x, u.y]], 2, 6);
    if (src.traits.has('spree') && !src.spree) {
      src.spree = true;
      emit(s, { t: 'spreeReady', uid: src.uid });
    }
    if (src.alive && src.traits.has('ogre')) {
      src.maxHp += 10;
      emit(s, { t: 'grow', uid: src.uid, maxHp: src.maxHp });
      heal(s, src, 10, 'drain');
    }
    if (src.alive && src.traits.has('rallykill')) {
      for (const v of s.units) if (v !== src && v.alive && v.team === src.team && manhattan(v.x, v.y, src.x, src.y) === 1) heal(s, v, 10, 'rally');
    }
  }

  // When something falls: explosions that spare its own side, poison and fire that spread,
  // shields for the friends it leaves, souls for those who reap.
  function deathTriggers(s, u, src) {
    const fighter = !u.nonCombat && !u.structure;
    const foes = other(u.team);
    if (fighter && s.relics[u.team].has('powder_keg')) s.booms.push({ x: u.x, y: u.y, dmg: 12, src: u, spare: u.team, kind: 'keg' });
    if (fighter && u.props.deathBoom) s.booms.push({ x: u.x, y: u.y, dmg: u.props.deathBoom, src: u, spare: u.team, kind: 'keg' });
    if (u.traits.has('overload')) s.booms.push({ x: u.x, y: u.y, r: 2, dmg: 20, src: u, spare: u.team, kind: 'storm' });
    if (u.type === 'shrub') {
      const f = s.byId[u.summoner];
      if (f && f.traits.has('bramble')) s.booms.push({ x: u.x, y: u.y, dmg: 8, src: f, spare: u.team, fx: { root: 1 }, kind: 'thorn' });
    }
    if (fighter && u.burn && src && src.team !== u.team && src.traits.has('combustion')) s.booms.push({ x: u.x, y: u.y, dmg: 10, src, spare: src.team, fx: { burn: [2, 5] }, kind: 'fire' });
    if (fighter && u.burn && s.relics[foes].has('wildfire_oil')) {
      const bsrc = s.byId[u.burn.src] || u;
      for (const v of s.units) {
        if (v.alive && v.team === u.team && !v.nonCombat && !v.structure && manhattan(v.x, v.y, u.x, u.y) === 1) applyStatus(s, bsrc, v, { burn: [Math.max(2, u.burn.turns), u.burn.dmg] }, null);
      }
    }
    if (fighter && u.poison) {
      const all = s.relics[foes].has('plague_mask');
      const jump = poisonStacks(u).filter((p) => all || (s.byId[p.src] && s.byId[p.src].traits.has('contagion')));
      const near = jump.length ? s.units.filter((v) => v.alive && v.team === u.team && !v.nonCombat && !v.structure && manhattan(v.x, v.y, u.x, u.y) === 1 && !statusImmune(s, v, 'poison')) : [];
      if (near.length) emit(s, { t: 'contagion', uid: u.uid, targets: near.map((v) => v.uid) });
      for (const v of near) {
        for (const p of jump) addPoison(v, s.byId[p.src] || null, p.key, Math.max(1, p.turns), p.dmg);
        emit(s, { t: 'status', uid: v.uid, status: 'poison', turns: v.poison.turns, dmg: v.poison.dmg, stacks: v.poison.stacks.length });
      }
    }
    if (u.traits.has('emberheart')) placeFire(s, u, radiusTiles(s, u.x, u.y, 1, true), 2, 6);
    if (u.traits.has('shatter')) {
      for (const v of s.units) {
        if (!v.alive || v.team !== u.team || v.nonCombat || v.structure || manhattan(v.x, v.y, u.x, u.y) > auraRadius(u)) continue;
        v.shield = Math.max(v.shield, 20);
        emit(s, { t: 'shield', uid: v.uid, amount: v.shield });
      }
    }
    if (!fighter) return;
    for (const w of s.units) {
      if (!w.alive || w.team === u.team || !w.traits.has('harvest') || manhattan(w.x, w.y, u.x, u.y) > 3) continue;
      if ((w.harvest || 0) < 5) w.harvest = (w.harvest || 0) + 1;
      emit(s, { t: 'harvest', uid: w.uid, from: u.uid, n: w.harvest });
      heal(s, w, 8, 'drain');
    }
  }

  // It stays down: its wolf may leap free, or it may rise again for the side that slew it.
  function afterlife(s, u, src) {
    if (u.traits.has('loyalwolf') && emptyGrass(s, u.x, u.y)) {
      const w = addUnit(s, { type: 'wolf', team: u.team, x: u.x, y: u.y, born: ++s.summonCount, facing: u.facing });
      w.activated = true;
      emit(s, { t: 'summon', uid: w.uid, x: u.x, y: u.y, by: u.uid, wolf: true });
      return;
    }
    if (!src || src.team === u.team || u.type === 'skeleton') return;
    const pact = src.traits.has('pact') && (src.raised || 0) < 2;
    const bell = s.relics[src.team].has('necro_bell') && s.rng.next() < 1 / 3;
    if (!(pact || bell) || !emptyGrass(s, u.x, u.y)) return;
    if (!bell) src.raised = (src.raised || 0) + 1;
    const sk = addUnit(s, { type: 'skeleton', team: src.team, x: u.x, y: u.y, born: ++s.summonCount, facing: src.team === 'P' ? 0 : 2 });
    sk.activated = true;
    sk.value *= 0.6;
    emit(s, { t: 'summon', uid: sk.uid, x: u.x, y: u.y, by: src.uid, raise: true });
  }

  // Relics that act as the armies take the field: Gambler's Dice crowns a Champion, the
  // Blood Pact costs every fighter a quarter of its health.
  function armRelics(s) {
    for (const team of ['P', 'E']) {
      const rel = s.relics[team];
      const army = s.units.filter((u) => u.team === team && !u.nonCombat && !u.structure);
      if (rel.has('gamblers_dice') && army.length) {
        const c = army[s.rng.int(army.length)];
        c.champion = true;
        c.maxHp = Math.round(c.maxHp * 1.5);
        c.hp = c.maxHp;
      }
      if (rel.has('blood_pact')) for (const u of army) u.hp = Math.max(1, Math.round(u.hp * 0.75));
      // Mirror Image: a shadow copy of it stands beside it, 1 HP, half the bite.
      for (const u of army) {
        if (!u.traits.has('mirrorimage')) continue;
        const spot = [[0, -1], [1, 0], [-1, 0], [0, 1]].map(([dx, dy]) => [u.x + dx, u.y + dy]).find(([x, y]) => emptyGrass(s, x, y));
        if (!spot) continue;
        const c = addUnit(s, { type: u.type, team, level: u.level, a1: u.a1, a2: u.a2, x: spot[0], y: spot[1], facing: u.facing, name: u.name + "'s image" });
        c.hp = 1;
        c.illusion = true;
        c.props.dmgMult = (c.props.dmgMult || 0) - 0.5;
        c.value *= 0.3;
      }
    }
  }

  // Bodyguard: a knight beside the target that has not stepped in since its own last turn.
  function bodyguardFor(s, v) {
    for (const g of s.units) {
      if (g === v || !g.alive || g.team !== v.team || !g.guardReady || g.para > 0 || !g.traits.has('bodyguard')) continue;
      if (manhattan(g.x, g.y, v.x, v.y) !== 1) continue;
      g.guardReady = false;
      emit(s, { t: 'intercept', uid: g.uid, for: v.uid });
      return g;
    }
    return null;
  }

  // Ricochet, Storm Jar and Shrapnel: an attack that lands carries on to more foes.
  function afterStrikes(s, u, a, struck, fx, opts) {
    if (!u.alive || !struck.length) return;
    const basic = a === u.acts[0];
    const done = new Set(struck.map((v) => v.uid));
    const more = (v, from, mult) => {
      const o = Object.assign({}, opts, { mult: (a.mult || 1) * mult, fromX: from.x, fromY: from.y, cat: null, noReact: true, noBonus: true, noCrit: true, deadeye: false });
      const landed = !hit(s, u, v, o).blocked;
      if (landed && v.alive && hasFx(fx)) applyStatus(s, u, v, fx, a);
      done.add(v.uid);
    };
    const jump = Math.max(basic ? u.props.bounce || 0 : 0, a.dmg === 'magic' && !u.nonCombat && s.relics[u.team].has('storm_jar') ? 0.5 : 0);
    if (jump) {
      const from = struck[struck.length - 1];
      let best = null;
      for (const v of s.units) {
        if (!isFoe(u, v) || done.has(v.uid) || v.nonCombat) continue;
        const d = manhattan(from.x, from.y, v.x, v.y);
        if (d <= 2 && (!best || d < best.d || (d === best.d && v.hp < best.v.hp))) best = { v, d };
      }
      if (best) {
        emit(s, { t: 'bounce', uid: u.uid, from: from.uid, to: best.v.uid, magic: a.dmg === 'magic' });
        more(best.v, from, jump);
      }
    }
    if (basic && a.kind === 'strike' && u.traits.has('grapple') && u.alive && struck[0].alive) pullToward(s, u, struck[0]);
    // Echo Amulet: a spell may strike the same foe again at half power.
    if (a.dmg === 'magic' && u.traits.has('echo')) {
      for (const v of struck) {
        if (!u.alive || !v.alive || s.rng.next() >= 0.25) continue;
        emit(s, { t: 'echo', uid: u.uid, target: v.uid });
        more(v, u, 0.5);
      }
    }
    if (basic && u.props.splash && u.alive) {
      const tgt = struck[0];
      const near = s.units.filter((v) => isFoe(u, v) && !done.has(v.uid) && !v.nonCombat && manhattan(tgt.x, tgt.y, v.x, v.y) === 1);
      if (near.length) emit(s, { t: 'splash', uid: u.uid, at: tgt.uid, targets: near.map((v) => v.uid) });
      for (const v of near) if (u.alive) more(v, tgt, u.props.splash);
    }
  }

  // A heal from a healer. With Halo, what spills past full HP becomes a shield (up to 15).
  function mend(s, u, v, amount) {
    const h = heal(s, v, amount, 'prayer');
    if (!u.traits.has('overshield') || !v.alive || v.nonCombat || v.structure || healBlocked(s, v)) return;
    const spill = Math.round(amount) - h;
    if (spill > 0 && v.shield < 15) {
      v.shield = Math.min(15, v.shield + spill);
      emit(s, { t: 'shield', uid: v.uid, amount: v.shield });
    }
  }

  // Discord: the paralyzed foe lashes out at one of its own beside it.
  function discord(s, u) {
    const w = s.units.find((v) => v.alive && v !== u && v.team === u.team && !v.nonCombat && !v.structure && manhattan(v.x, v.y, u.x, u.y) === 1);
    if (!w) return;
    emit(s, { t: 'discord', uid: u.uid, target: w.uid });
    applyDamage(s, u, w, Math.max(1, Math.round(u.pow * 0.5)), { cat: 'none', dmgType: 'true' });
  }

  // Pull a unit one step toward `src`, along the longer axis first. Returns true if it moved.
  function pullToward(s, src, v) {
    if (statusImmune(s, v, 'knock')) {
      shrug(s, v, 'steady');
      return false;
    }
    const dx = src.x - v.x;
    const dy = src.y - v.y;
    if (Math.abs(dx) + Math.abs(dy) <= 1) return false;
    const steps = Math.abs(dx) >= Math.abs(dy) ? [[Math.sign(dx), 0], [0, Math.sign(dy)]] : [[0, Math.sign(dy)], [Math.sign(dx), 0]];
    for (const [sx, sy] of steps) {
      if ((!sx && !sy) || !emptyGrass(s, v.x + sx, v.y + sy)) continue;
      const nx = v.x + sx;
      const ny = v.y + sy;
      emit(s, { t: 'pull', uid: v.uid, by: src.uid });
      relocate(s, v, nx, ny);
      emit(s, { t: 'push', uid: v.uid, x: nx, y: ny });
      enterTile(s, v, nx, ny);
      return true;
    }
    return false;
  }

  // Slippery: after a block it slips one tile away from the attacker.
  function slip(s, atk, u) {
    if (!u.alive) return;
    const d = dirFromDelta(u.x - atk.x, u.y - atk.y);
    if (d < 0) return;
    const nx = u.x + DIRS[d][0];
    const ny = u.y + DIRS[d][1];
    if (!emptyGrass(s, nx, ny)) return;
    emit(s, { t: 'slip', uid: u.uid });
    relocate(s, u, nx, ny);
    emit(s, { t: 'push', uid: u.uid, x: nx, y: ny });
    enterTile(s, u, nx, ny);
  }

  // Set grass tiles ablaze for `turns` of the owner's turns, hurting its enemies.
  function placeFire(s, owner, tiles, turns, dmg) {
    const placed = [];
    for (const [x, y] of tiles) {
      if (!inB(s, x, y) || s.terrain[idx(s, x, y)] !== T_GRASS) continue;
      const old = tileFx(s, x, y, 'fire');
      if (old) s.tfx.splice(s.tfx.indexOf(old), 1);
      s.tfx.push({ kind: 'fire', x, y, team: owner.team, turns, dmg, src: owner.uid });
      placed.push([x, y]);
    }
    if (placed.length) emit(s, { t: 'hazard', kind: 'fire', tiles: placed, team: owner.team });
  }

  // Trample: a charge carries through to the enemy behind its target.
  function trample(s, u, v, opts) {
    if (!v || !u.alive) return;
    const d = dirFromDelta(v.x - u.x, v.y - u.y);
    if (d < 0) return;
    const w = at(s, v.x + DIRS[d][0], v.y + DIRS[d][1]);
    if (!w || !isFoe(u, w) || w.nonCombat) return;
    emit(s, { t: 'trample', uid: u.uid, target: w.uid });
    hit(s, u, w, Object.assign({}, opts, { mult: 0.6, fromX: v.x, fromY: v.y, cat: null, noReact: true, noCrit: true, deadeye: false, spree: false }));
  }

  // Once a unit has walked: it is no longer holding the line, it may puff spores, and
  // enemies on overwatch may take a shot.
  function afterMove(s, u) {
    if (!u.alive) return;
    u.braced = false;
    if (u.traits.has('sporepuff')) {
      const near = s.units.filter((v) => isFoe(u, v) && !v.nonCombat && !v.structure && manhattan(u.x, u.y, v.x, v.y) === 1);
      if (near.length) emit(s, { t: 'puff', uid: u.uid });
      for (const v of near) applyStatus(s, u, v, { poison: [1, 4] }, { name: 'Spore Puff' });
    }
    for (const w of s.units) {
      if (!u.alive) return;
      if (!w.alive || w.team === u.team || !w.watchReady || w.para > 0 || !w.traits.has('overwatch') || !w.act.range) continue;
      const d = manhattan(w.x, w.y, u.x, u.y);
      if (d < w.act.range[0] || d > w.act.range[1] || u.nonCombat) continue;
      w.watchReady = false;
      emit(s, { t: 'overwatch', uid: w.uid, target: u.uid });
      hit(s, w, u, { act: w.act, mult: 0.5, fromX: w.x, fromY: w.y, noReact: true, noCrit: true });
    }
  }

  // Magnetic Core: yank the nearest foe 2 or 3 tiles away one step closer.
  function magnetize(s, u) {
    let best = null;
    for (const v of s.units) {
      if (!isFoe(u, v) || v.nonCombat || v.structure || v.boss) continue;
      const d = manhattan(u.x, u.y, v.x, v.y);
      if (d < 2 || d > 3) continue;
      if (!best || d < best.d || (d === best.d && v.hp < best.v.hp)) best = { v, d };
    }
    if (best) pullToward(s, u, best.v);
  }

  function applyDamage(s, src, tgt, amount, info) {
    if (!tgt.alive || amount <= 0) return 0;
    if (tgt.shield > 0 && info.dmgType !== 'poison' && info.dmgType !== 'fatigue') {
      const ab = Math.min(tgt.shield, amount);
      tgt.shield -= ab;
      amount -= ab;
      emit(s, { t: 'absorb', uid: tgt.uid, amount: ab, left: tgt.shield });
      if (amount <= 0) return 0;
    }
    if (info.dmgType === 'magic' || info.dmgType === 'burn') tgt.scorched = true;
    // An Hourglass Pendant or a Guardian Angel may undo a killing blow.
    if (amount >= tgt.hp && !tgt.secondWind && !tgt.nonCombat && !tgt.structure && cheatDeath(s, tgt, amount, info, src)) return 0;
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
      emit(s, { t: 'dmg', uid: tgt.uid, amount, cat: info.cat, dmgType: info.dmgType, src: src ? src.uid : 0, rout: info.rout || undefined });
      if (tgt.hp <= 0) kill(s, tgt, src);
    }
    if (src && src.team !== tgt.team) s.stats.dmg[src.team] += dealt;
    if (dealt > 0 && tgt.alive) woundTriggers(s, tgt, dealt, info);
    return dealt;
  }

  function cheatDeath(s, u, amount, info, src) {
    let hp = 0;
    let ev = null;
    if (u.traits.has('hourglass') && !u.rewound) {
      u.rewound = true;
      hp = Math.max(1, Math.min(u.maxHp, u.lastTurnHp || Math.ceil(u.maxHp / 2)));
      ev = { t: 'rewind', uid: u.uid, hp };
    } else {
      const angel = s.units.find((w) => w !== u && w.alive && w.team === u.team && !w.angelUsed && w.traits.has('angel') && manhattan(w.x, w.y, u.x, u.y) <= 3);
      if (!angel) return false;
      angel.angelUsed = true;
      hp = 1;
      ev = { t: 'angel', uid: u.uid, by: angel.uid, hp };
    }
    emit(s, { t: 'dmg', uid: u.uid, amount, cat: info.cat, dmgType: info.dmgType, src: src ? src.uid : 0 });
    u.hp = hp;
    emit(s, ev);
    return true;
  }

  // What a wound sets off in the one who took it.
  function woundTriggers(s, u, dealt, info) {
    // Blood Frenzy: every wound makes it hit harder, up to +50%.
    if (u.props.furyPerHit && (u.fury || 0) < 10) {
      u.fury = (u.fury || 0) + 1;
      emit(s, { t: 'fury', uid: u.uid, n: u.fury });
    }
    const magic = info.dmgType === 'magic';
    if (magic && u.traits.has('runecore') && (u.runes || 0) < 20) {
      u.runes = Math.min(20, (u.runes || 0) + dealt);
      emit(s, { t: 'charged', uid: u.uid, kind: 'runes' });
    }
    if (magic && u.traits.has('spellsink') && !u.sink) {
      u.sink = true;
      emit(s, { t: 'charged', uid: u.uid, kind: 'sink' });
    }
    if (u.traits.has('capacitor') && (u.charge || 0) < 3) {
      u.charge = (u.charge || 0) + 1;
      emit(s, { t: 'charged', uid: u.uid, kind: 'charge', n: u.charge });
    }
    if (u.traits.has('resonance') && u.resoPly !== s.ply) {
      u.resoPly = s.ply;
      emit(s, { t: 'resonance', uid: u.uid });
      for (const v of s.units) {
        if (!v.alive || v.team !== u.team || v.nonCombat || v.structure || manhattan(v.x, v.y, u.x, u.y) > 2 || v.shield >= 15) continue;
        v.shield = Math.min(15, v.shield + 5);
        emit(s, { t: 'shield', uid: v.uid, amount: v.shield });
      }
    }
    if (u.hp >= u.maxHp / 2) return;
    // Below half HP for the first time.
    if (u.traits.has('reactive') && !u.reacted) {
      u.reacted = true;
      u.shield = Math.max(u.shield, 25);
      emit(s, { t: 'shield', uid: u.uid, amount: u.shield });
    }
    if (u.traits.has('undying') && !u.raged) {
      u.raged = true;
      emit(s, { t: 'rage', uid: u.uid });
      heal(s, u, 15, 'rage');
      u.frenzy = Math.max(u.frenzy, 2);
      stamp(s, u, 'frenzy');
      emit(s, { t: 'status', uid: u.uid, status: 'frenzy', turns: 2 });
    }
    if (u.traits.has('sprout') && !u.sprouted) {
      u.sprouted = true;
      let n = 0;
      for (const [dx, dy] of [[0, -1], [1, 0], [0, 1], [-1, 0]]) if (n < 3 && emptyGrass(s, u.x + dx, u.y + dy)) {
        summonShrub(s, u, u.x + dx, u.y + dy);
        n++;
      }
    }
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
    // Ethereal: a blow of steel may pass right through it.
    if (dmgType === 'phys' && tgt.traits.has('ethereal') && s.rng.next() < 0.3) {
      emit(s, { t: 'phase', uid: tgt.uid, src: atk.uid });
      return { blocked: true, dmg: 0 };
    }
    if (r.block > 0 && s.rng.next() < r.block) {
      emit(s, { t: 'block', uid: tgt.uid, src: atk.uid, cat: r.cat });
      if (tgt.traits.has('stunshield') && atk.alive && manhattan(atk.x, atk.y, tgt.x, tgt.y) === 1) applyStatus(s, tgt, atk, { para: 1 }, null);
      reactToMelee(s, atk, tgt, opts);
      if (tgt.traits.has('slippery')) slip(s, atk, tgt);
      return { blocked: true, dmg: 0 };
    }
    // Mirror Aegis: the first hit each of your units takes in a battle bounces back.
    // Spell Mirror: so does the first spell.
    const mirror = opts.noReact || tgt.nonCombat || tgt.structure ? null
      : s.relics[tgt.team].has('mirror_aegis') && !tgt.mirrored ? 'mirrored'
      : dmgType === 'magic' && tgt.traits.has('spellmirror') && !tgt.spellMirrored ? 'spellMirrored' : null;
    if (mirror) {
      tgt[mirror] = true;
      emit(s, { t: 'reflect', uid: tgt.uid, src: atk.uid });
      applyDamage(s, tgt, atk, r.dmg, { cat: 'none', dmgType: 'true' });
      return { blocked: true, dmg: 0 };
    }
    // Critical hits: double damage. A Deadeye shot, and an Eagle Eye's first, always is one.
    let dmg = r.dmg;
    const critChance = (atk.props.crit || 0) + (s.relics[atk.team].has('lucky_coin') && !atk.nonCombat ? 0.12 : 0);
    const opener = atk.traits.has('opener') && !atk.openerUsed && !opts.noCrit;
    if (!opts.noCrit && (opts.deadeye || opener || (critChance > 0 && s.rng.next() < critChance))) {
      dmg *= 2;
      if (opener) atk.openerUsed = true;
      emit(s, { t: 'crit', uid: tgt.uid, src: atk.uid, deadeye: !!opts.deadeye });
    }
    // Killing Spree: the blow after a kill lands double. Gambler's Gauntlet: anything goes.
    if (opts.spree) {
      dmg *= 2;
      emit(s, { t: 'spree', uid: tgt.uid, src: atk.uid });
    }
    if (atk.props.gamble) {
      const f = 0.5 + 1.5 * s.rng.next();
      dmg = Math.max(1, Math.round(dmg * f));
      emit(s, { t: 'gamble', uid: tgt.uid, f: Math.round(f * 10) / 10 });
    }
    const dealt = applyDamage(s, atk, tgt, dmg, { cat: r.cat, dmgType });
    // Armor Breaker: each blow strips a tenth of the target's armor for good.
    if (dealt > 0 && tgt.alive && dmgType === 'phys' && atk.traits.has('sunder') && tgt.armor > 0) {
      tgt.armor = Math.max(0, Math.round((tgt.armor - 0.1) * 100) / 100);
      emit(s, { t: 'sunder', uid: tgt.uid, armor: tgt.armor });
    }
    // Runic Core: the magic it soaked up comes out with its next blow.
    if (atk.runes && atk.alive && tgt.alive && !opts.noBonus) {
      const rn = atk.runes;
      atk.runes = 0;
      emit(s, { t: 'runes', uid: atk.uid, amount: rn });
      magicDamage(s, atk, tgt, rn, 'bonus');
    }
    // Glamour: an attacker may be left spellbound.
    if (tgt.alive && atk.alive && !opts.noReact && tgt.traits.has('glamour') && s.rng.next() < 0.25) applyStatus(s, tgt, atk, { para: 1 }, null);
    // Execute: a foe left this low falls outright (never a boss or a building).
    const exec = Math.max(atk.props.execute || 0, s.relics[atk.team].has('executioner_hood') && !atk.nonCombat ? 0.15 : 0);
    if (exec && dealt > 0 && tgt.alive && !tgt.boss && !tgt.structure && !tgt.nonCombat && tgt.hp <= tgt.maxHp * exec) {
      emit(s, { t: 'execute', uid: tgt.uid, src: atk.uid });
      applyDamage(s, atk, tgt, tgt.hp + tgt.shield, { cat: 'none', dmgType: 'true' });
    }
    // Cutpurse: every hit lifts 2 gold, up to 12 a battle.
    if (dealt > 0 && atk.team === 'P' && atk.traits.has('cutpurse') && (atk.stolen || 0) < 12) {
      atk.stolen = (atk.stolen || 0) + 2;
      s.stats.gold += 2;
      emit(s, { t: 'gold', uid: atk.uid, amount: 2 });
    }
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
    if (atk.alive && !tgt.nonCombat) {
      if (tgt.traits.has('porcupine')) applyStatus(s, tgt, atk, { mark: 2 }, null);
      if (tgt.traits.has('rattle')) applyStatus(s, tgt, atk, { weak: 1 }, null);
      if (tgt.traits.has('burnscales')) applyStatus(s, tgt, atk, { burn: [2, 4] }, null);
      if (tgt.traits.has('shove') && tgt.alive && atk.alive) knockback(s, tgt, atk);
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

  // Poison from each source (one unit's ability) runs on its own, with its own damage and
  // its own turns. At the start of the poisoned unit's turn it takes them all added up,
  // then each counts down by itself. The same source again refreshes its own poison rather
  // than adding another. u.poison is null, or { stacks: [{ key, src, dmg, turns }], dmg,
  // turns, src }: dmg the total a turn, turns the longest still to run.
  function poisonKey(src, act) {
    return (src ? src.uid : 0) + ':' + (act ? act.name || act.kind : '');
  }

  function poisonStacks(u) {
    const P = u.poison;
    if (!P) return [];
    // One poison set by hand (or from before poisons stacked): a single source.
    if (!P.stacks) P.stacks = [{ key: 'one', src: P.src || 0, dmg: P.dmg, turns: P.turns }];
    return P.stacks;
  }

  function sumPoison(u) {
    const st = poisonStacks(u).filter((p) => p.turns > 0);
    if (!st.length) {
      u.poison = null;
      return;
    }
    u.poison.stacks = st;
    u.poison.dmg = st.reduce((t, p) => t + p.dmg, 0);
    u.poison.turns = Math.max(...st.map((p) => p.turns));
    u.poison.src = st[st.length - 1].src;
  }

  function addPoison(u, src, key, turns, dmg) {
    if (!u.poison) u.poison = { stacks: [], dmg: 0, turns: 0, src: 0 };
    const st = poisonStacks(u);
    const same = st.find((p) => p.key === key);
    if (same) {
      same.turns = Math.max(same.turns, turns);
      same.dmg = Math.max(same.dmg, dmg);
    } else st.push({ key, src: src ? src.uid : 0, dmg, turns });
    sumPoison(u);
  }

  // A status that does not take. Berserker's Torc turns the attempt into a frenzy.
  function shrug(s, u, why) {
    emit(s, { t: 'resist', uid: u.uid, why });
    if (!u.traits.has('torc') || !u.alive) return;
    u.frenzy = Math.max(u.frenzy, 1);
    stamp(s, u, 'frenzy');
    emit(s, { t: 'status', uid: u.uid, status: 'frenzy', turns: 1 });
  }

  function applyStatus(s, src, u, fx, act) {
    if (!u.alive || u.nonCombat || u.structure) return;
    if (fx.para) {
      if (statusImmune(s, u, 'para')) shrug(s, u);
      else {
        u.para = Math.max(u.para, fx.para);
        stamp(s, u, 'para');
        emit(s, { t: 'status', uid: u.uid, status: 'para', turns: u.para });
        if (src && src.traits.has('discord') && u.alive) discord(s, u);
      }
    }
    if (fx.poison) {
      if (statusImmune(s, u, 'poison')) emit(s, { t: 'resist', uid: u.uid });
      else {
        addPoison(u, src, poisonKey(src, act), fx.poison[0], fx.poison[1]);
        emit(s, { t: 'status', uid: u.uid, status: 'poison', turns: u.poison.turns, dmg: u.poison.dmg, stacks: u.poison.stacks.length });
      }
    }
    if (fx.burn) {
      const p = u.burn;
      u.burn = { turns: Math.max(fx.burn[0], p ? p.turns : 0), dmg: Math.max(fx.burn[1], p ? p.dmg : 0), src: src.uid };
      emit(s, { t: 'status', uid: u.uid, status: 'burn', turns: u.burn.turns });
    }
    if (fx.root) {
      if (statusImmune(s, u, 'root')) shrug(s, u);
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
      shrug(s, u, 'steady');
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
      const tiles = radiusTiles(s, b.x, b.y, b.r || 1, true);
      emit(s, { t: 'boom', x: b.x, y: b.y, tiles, kind: b.kind || null });
      for (const v of unitsOnTiles(s, tiles)) {
        if (!v.alive || v === b.src || (b.spare && v.team === b.spare)) continue;
        magicDamage(s, b.src, v, b.dmg, 'boom');
        if (b.fx && v.alive && !v.structure && !v.nonCombat) applyStatus(s, b.src, v, b.fx, null);
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
    if (s.queue && !(s.side === team && s.due === u.uid)) return false;
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
    afterMove(s, u);
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
    // Counted down at the start of each of the unit's later turns, so it waits a.cd of them.
    if (a.cd) a.cdLeft = a.cd + 1;
    const opts = { moved: A.movedBeforeAct, moveDist: A.moveDist, fromX: u.x, fromY: u.y, act: a };
    const tiles = affectedTiles(s, u, target);
    const fd = facingToward(u, target);
    if (fd >= 0 && u.facing >= 0 && fd !== u.facing && a.kind !== 'leap' && a.kind !== 'blink') {
      u.facing = fd;
      emit(s, { t: 'face', uid, facing: fd });
    }
    emit(s, { t: 'action', uid, kind: a.kind, name: a.name, target, tiles, x: u.x, y: u.y, dmg: a.dmg || null, ai, hz: a.hz || null, fixed: a.fixed != null });
    const fx = hitFx(u, a);
    // Deadeye: every third basic shot is a sure critical hit.
    if (a === u.acts[0] && a.dmg && u.traits.has('deadeye')) {
      u.shots = (u.shots || 0) + 1;
      if (u.shots % 3 === 0) opts.deadeye = true;
    }
    if (a.dmg) u.revealed = true;
    if (a.dmg && u.spree) {
      opts.spree = true;
      u.spree = false;
    }
    const struck = [];
    const strike = (v, o) => {
      if (!v.alive) return;
      // Bodyguard: a knight beside the target steps in front of a single-target blow.
      if (a.kind === 'strike' && a.dmg && v.team !== u.team) v = bodyguardFor(s, v) || v;
      let landed = true;
      if (a.dmg) landed = !hit(s, u, v, o || opts).blocked;
      if (landed && v.alive && v.team !== u.team && hasFx(fx)) applyStatus(s, u, v, fx, a);
      // Chaos Magic: a random curse on top.
      if (landed && v.alive && v.team !== u.team && a.dmg === 'magic' && u.traits.has('chaosmagic')) applyStatus(s, u, v, [{ burn: [2, 4] }, { root: 1 }, { weak: 2 }][s.rng.int(3)], a);
      if (a.dmg && v.team !== u.team) struck.push(v);
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
        if (a.kind === 'strike' && a === u.acts[0] && u.traits.has('trample') && opts.moved && opts.moveDist >= 3) trample(s, u, s.byId[target.uid], opts);
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
          mend(s, u, v, healAmount(u, a));
        }
        break;
      case 'heal': {
        const v = s.byId[target.uid];
        if (a.cure) cleanse(s, v, false);
        mend(s, u, v, healAmount(u, a));
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
    afterStrikes(s, u, a, struck, fx, opts);
    // Far Cast: the fireball leaves its centre burning.
    if (a === u.acts[0] && a.dmg && u.alive && u.traits.has('scorch') && target.x != null) placeFire(s, u, [[target.x, target.y]], 2, 6);
    // Stored charge is spent on the attack.
    if (a.dmg) {
      u.charge = 0;
      u.sink = false;
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
    if (u.traits.has('brace')) u.braced = !A.moved;
    u.activated = true;
    s.spent = true;
    emit(s, { t: 'done', uid: u.uid, wait: w });
    if (s.queue) {
      ownTurnDone(s, u);
      s.due = 0;
    }
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
  const MEND_REGEN = 2;
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
    if (!s.spent) emit(s, { t: 'pass', side: s.side, auto: !!auto, uid: s.due || 0 });
    if (s.queue && s.due && !s.spent && s.byId[s.due].alive) ownTurnDone(s, s.byId[s.due]);
    s.due = 0;
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
        if (!s.queue) {
          if (u.wait > 0) tick('wait');
          else tick('para');
          tick('root');
          tick('weak');
          tick('frenzy');
        }
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
    if (kind === 'poison') {
      // Every poison on it at once, added up; then each runs down on its own.
      sumPoison(u);
      if (!u.poison) return;
      const n = u.poison.stacks.length;
      const feeders = u.poison.stacks.map((p) => [s.byId[p.src], p.dmg]).filter(([w]) => w && w.alive && w.traits.has('parasite'));
      applyDamage(s, s.byId[u.poison.src] || null, u, u.poison.dmg, { cat: 'none', dmgType: 'poison' });
      // Parasite: the poisoner drinks what its poison takes.
      for (const [w, d] of feeders) heal(s, w, d, 'drain');
      if (!u.alive || !u.poison) return;
      for (const st of u.poison.stacks) st.turns--;
      sumPoison(u);
      if (!u.poison) emit(s, { t: 'cure', uid: u.uid, status: 'poison' });
      else if (u.poison.stacks.length < n) emit(s, { t: 'status', uid: u.uid, status: 'poison', turns: u.poison.turns, dmg: u.poison.dmg, stacks: u.poison.stacks.length });
      return;
    }
    const src = s.byId[p.src] || null;
    magicDamage(s, src, u, p.dmg, 'burn');
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
    // Poison, burns, fire underfoot, regen and fatigue all come at the start of
    // each unit's own turn (see unitTurnStart). In queue battles that is when its turn in the
    // rotation comes up (see pickDue), not at the start of its side's turn.
    if (!s.queue) for (const u of mine) if (u.alive && !u.nonCombat) unitTurnStart(s, u);
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
      if (!w.traits.has('purge')) continue;
      for (const v of s.units) {
        if (!v.alive || v.team !== team || v.nonCombat || v.structure || manhattan(v.x, v.y, w.x, w.y) > auraRadius(w)) continue;
        if (v.root || v.burn) {
          v.root = 0;
          v.burn = null;
          emit(s, { t: 'cleanse', uid: v.uid });
        }
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
    // Goblin Firecrackers: the side's first turn opens with a bang on three random foes.
    if (!s.opened[team]) {
      s.opened[team] = true;
      if (s.relics[team].has('firecrackers')) {
        const foes = s.units.filter((v) => v.alive && v.team !== team && !v.nonCombat && !v.structure);
        for (let i = 0; i < 3 && foes.length; i++) {
          const v = foes.splice(s.rng.int(foes.length), 1)[0];
          emit(s, { t: 'boom', x: v.x, y: v.y, tiles: [[v.x, v.y]], kind: 'firecracker' });
          magicDamage(s, null, v, 8, 'boom');
        }
      }
    }
    // War Drum: every fifth turn, the whole army heals 10 and flies into a frenzy.
    if (s.relics[team].has('echo_drum') && s.turn % 5 === 0 && s.drummed[team] !== s.turn) {
      s.drummed[team] = s.turn;
      emit(s, { t: 'echo', team });
      for (const v of mine) {
        if (!v.alive || v.nonCombat || v.structure) continue;
        heal(s, v, 10, 'drum');
        v.frenzy = Math.max(v.frenzy, 2);
        stamp(s, v, 'frenzy');
        emit(s, { t: 'status', uid: v.uid, status: 'frenzy', turns: 2 });
      }
    }
    resolveBooms(s);
  }

  // A unit's regen at the start of its turn: its own, plus a Mending Light aura it stands
  // in. A troll hurt by magic or fire since its last turn does not regenerate.
  function regenOf(s, u) {
    let r = u.regen || 0;
    for (const w of s.units) {
      if (w.alive && w.team === u.team && w.traits.has('auramend') && manhattan(u.x, u.y, w.x, w.y) <= auraRadius(w)) {
        r += MEND_REGEN;
        break;
      }
    }
    return r;
  }

  function regenerate(s, u) {
    const r = regenOf(s, u);
    if (r > 0) {
      if (u.traits.has('trollblood') && u.burnt) emit(s, { t: 'noregen', uid: u.uid });
      else heal(s, u, r, 'regen');
    }
    if (u.traits.has('mossy')) for (const v of s.units) if (v !== u && v.alive && v.team === u.team && manhattan(u.x, u.y, v.x, v.y) === 1) heal(s, v, 2, 'regen');
  }

  // The start of one unit's own turn: poison and burns tick and fire underfoot hurts.
  // Outside queue battles it then regenerates and
  // loses fatigue here too; in queue battles those come only to the unit that takes the
  // turn, not to the ones that sit it out (pickDue).
  function unitTurnStart(s, u) {
    for (const a of u.acts) if (a.cdLeft > 0) a.cdLeft--;
    u.lastTurnHp = u.hp;
    u.watchReady = true;
    if (u.traits.has('idol') && u.alive) {
      emit(s, { t: 'curse', uid: u.uid });
      applyDamage(s, null, u, 4, { cat: 'none', dmgType: 'true' });
    }
    // A troll hurt by magic or fire since its last turn does not regenerate this turn.
    u.burnt = u.scorched;
    u.scorched = false;
    tickDot(s, u, 'poison');
    tickDot(s, u, 'burn');
    resolveBooms(s);
    u.guardReady = true;
    if (u.alive && u.traits.has('magnet')) magnetize(s, u);
    if (u.alive && !u.traits.has('flying')) {
      const fire = tileFx(s, u.x, u.y, 'fire');
      if (fire && fire.team !== u.team) {
        emit(s, { t: 'scorch', uid: u.uid, x: u.x, y: u.y });
        magicDamage(s, s.byId[fire.src] || null, u, fire.dmg || FIRE_DMG, 'burn');
      }
    }
    if (!u.alive || s.queue) return;
    regenerate(s, u);
    fatigue(s, u);
  }

  // This round's fatigue, past armor and shields.
  function fatigue(s, u) {
    // A routed enemy bleeds every turn already (routTick); fatigue is for the other side.
    if (s.routed && u.team === 'E') return;
    const n = fatigueHit(s);
    if (n && u.alive && counts(u)) applyDamage(s, null, u, n, { cat: 'none', dmgType: 'fatigue' });
  }

  // HP a unit loses to fatigue at the start of its turn this round: 1 in the round it sets
  // in, 2 the next, and so on, the same for both sides (0 before it sets in).
  function fatigueHit(s) {
    return s.inOvertime ? Math.max(1, s.turn - s.overtime + 1) : 0;
  }

  // The mission is done: the cage broken, the wagons or the warbanner wrecked, the seal or
  // the shrine held, the commander or the boss slain, the waves outlasted. The battle does
  // not stop there: the enemy is routed. Their reinforcements stop coming, and from the
  // next enemy turn every enemy fighter bleeds at the start of each enemy turn, 1 HP more
  // each turn (routTick). You win when the last of them falls. Your own side tires only
  // when fatigue sets in for everyone (turn 30).
  function rout(s, why) {
    if (s.routed || s.over) return;
    s.routed = Object.assign({ turn: s.turn }, why);
    if (s.surviveTurns) s.surviveTurns = 0;
    if (s.hold) s.hold.done = true;
    for (const w of s.waves) if (w.team === 'E' && w.state === 'pending') w.state = 'cancelled';
    emit(s, Object.assign({ t: 'routed', turn: s.turn }, why));
  }

  // What each routed enemy loses at the start of an enemy turn: 1 in the first enemy turn
  // after the rout, then 2, 3 and so on (0 before the rout).
  function routHit(s) {
    return s.routed ? Math.max(1, s.turn - s.routed.turn) : 0;
  }

  function routTick(s) {
    if (!s.routed || s.routed.ticked === s.turn || s.over) return;
    s.routed.ticked = s.turn;
    const n = routHit(s);
    emit(s, { t: 'routTick', dmg: n });
    for (const u of s.units.slice()) if (u.alive && u.team === 'E' && counts(u)) applyDamage(s, null, u, n, { cat: 'none', dmgType: 'fatigue', rout: true });
    resolveBooms(s);
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
      if (s.surviveTurns && s.turn > s.surviveTurns) rout(s, { survived: true });
    }
    startFatigue(s);
    startEffects(s, side);
    if (side === 'E') routTick(s);
    checkOutcome(s);
    if (s.over) return;
    if (side === 'P' && s.hold && !s.routed) {
      const h = s.hold;
      const on = at(s, h.x, h.y);
      if (on && on.team === 'P' && !on.nonCombat) h.count++;
      else h.count = 0;
      emit(s, { t: 'hold', count: h.count, need: h.need, uid: on && on.team === 'P' ? on.uid : 0 });
      if (h.count >= h.need) rout(s, { held: true });
    }
    // The other side's next waves mark where they land, a turn before they arrive.
    planWaves(s, other(side), side === 'P' ? s.turn + 1 : s.turn);
    if (s.queue) pickDue(s, side);
  }

  // Fatigue: from turn `s.overtime` on, each fighter loses HP at the start of its turn, 1
  // more each round and the same for both sides (see fatigueHit), and no more
  // reinforcements come. Big units and regen last longest; the last side standing wins.
  function startFatigue(s) {
    if (!s.overtime || s.turn < s.overtime || s.inOvertime || s.over) return;
    s.inOvertime = true;
    for (const w of s.waves) if (w.state === 'pending') w.state = 'cancelled';
    emit(s, { t: 'overtime', turn: s.turn });
  }

  // ---------------------------------------------------------------- unit queue
  //
  // In queue battles each side's units take that side's turns in a set rotation: every
  // unit gets one turn per cycle, faster units first (ties: the earlier unit). A unit that
  // is cooling down, paralyzed or has nothing it could do sits its turn out, and the next
  // in line goes instead. Cooldowns, paralysis, roots, weakness and frenzy count the
  // unit's own turns, taken or sat out.

  function inQueue(u) {
    return u.alive && !u.nonCombat && hasAction(u);
  }

  function byQueue(a, b) {
    return a.cycles - b.cycles || b.spd - a.spd || a.uid - b.uid;
  }

  function queueStart(s, team) {
    let m = Infinity;
    for (const v of s.units) if (v.team === team && inQueue(v)) m = Math.min(m, v.cycles);
    return m === Infinity ? 0 : m;
  }

  function ownTurnDone(s, u) {
    u.cycles++;
    const fresh = u.fresh || {};
    const tick = (k) => {
      if (u[k] > 0 && fresh[k] !== s.ply) u[k]--;
    };
    if (u.wait > 0) tick('wait');
    else tick('para');
    tick('root');
    tick('weak');
    tick('frenzy');
  }

  function sitOutReason(s, u) {
    return u.para > 0 ? 'para' : u.wait > 0 ? 'cooldown' : !usefulUnit(s, u) ? 'idle' : null;
  }

  // The side's unit for this turn. Those who must sit out are passed over, each at most
  // once a turn; if everyone does, the side passes. Regen and fatigue come to one unit a
  // turn, the one that takes it: units that sit the turn out neither regenerate nor lose
  // HP to fatigue, except that when every unit sits out, the first in line still takes the
  // turn's fatigue.
  function pickDue(s, side) {
    s.due = 0;
    const seen = new Set();
    let tired = !s.inOvertime;
    let first = null;
    for (;;) {
      const u = s.units.filter((v) => v.team === side && inQueue(v)).sort(byQueue)[0];
      if (!u || seen.has(u.uid)) break;
      seen.add(u.uid);
      unitTurnStart(s, u);
      const why = u.alive ? sitOutReason(s, u) : null;
      if (u.alive && !why) {
        regenerate(s, u);
        if (!tired) {
          tired = true;
          fatigue(s, u);
        }
      }
      if (!u.alive) {
        checkOutcome(s);
        if (s.over) return;
        continue;
      }
      if (!why) {
        s.due = u.uid;
        return;
      }
      if (!first) first = u;
      emit(s, { t: 'sitout', uid: u.uid, why, wait: u.wait });
      ownTurnDone(s, u);
    }
    if (!tired && first && first.alive) {
      fatigue(s, first);
      checkOutcome(s);
    }
  }

  // Who takes each of `team`'s next `n` turns, predicted from the rotation as it stands
  // (each assumed to act and start its cooldown). Entries: { uid } or { uid: 0 } for a
  // turn nobody can take.
  function upcoming(s, team, n) {
    const vs = s.units.filter((v) => v.team === team && inQueue(v)).map((v) => ({ v, cycles: v.cycles, wait: v.wait, para: v.para, spd: v.spd, uid: v.uid }));
    const out = [];
    for (let turn = 0; turn < n && vs.length; turn++) {
      let picked = null;
      if (turn === 0 && s.side === team && s.due) picked = vs.find((x) => x.uid === s.due) || null;
      const seen = new Set();
      while (!picked) {
        vs.sort(byQueue);
        const x = vs[0];
        if (seen.has(x)) break;
        seen.add(x);
        const resting = x.para > 0 || x.wait > 0;
        x.cycles++;
        if (x.wait > 0) x.wait--;
        else if (x.para > 0) x.para--;
        if (!resting) picked = x;
        else continue;
        break;
      }
      if (!picked) {
        out.push({ uid: 0 });
        continue;
      }
      if (turn === 0 && s.side === team && s.due) picked.cycles++;
      picked.wait = picked.v.rec;
      out.push({ uid: picked.uid });
    }
    return out;
  }

  // In a queue battle: how many of its side's turns pass before `u` acts (0: next).
  function queueDelay(s, u, horizon) {
    const list = upcoming(s, u.team, horizon || 12);
    const i = list.findIndex((x) => x.uid === u.uid);
    return i < 0 ? horizon || 12 : i;
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
      if (u.alive && counts(u)) alive[u.team] = true;
    }
    // Reinforcements still on the way keep a side in the fight.
    for (const team of ['P', 'E']) if (pendingWaves(s, team)) alive[team] = true;
    const vipDown = (s.objective === 'boss' || s.objective === 'vip') && hasVip && !vipAlive;
    const objDown = s.objective === 'destroy' && hasObj && !objAlive && !objEscaped;
    // Nobody yields: a side that has only units that cannot hurt anyone (a Furgon, a
    // Barrier Ward) fights on, and the enemy must still bring every one down. Fatigue
    // settles it if neither side can.
    // The mission done (the boss or commander slain, every goal object broken), the enemy is
    // routed rather than beaten on the spot: you still have to finish them.
    if (vipDown) rout(s, { vipSlain: true });
    if (objDown) rout(s, { destroyed: true });
    let winner = null;
    if (!alive.P && !alive.E) winner = s.side;
    else if (!alive.P) winner = 'E';
    else if (!alive.E) winner = 'P';
    if (!winner) return;
    // A win after a rout keeps why the enemy broke (vipSlain, destroyed, held, survived).
    const why = {};
    if (winner === 'P' && s.routed) for (const k of ['vipSlain', 'destroyed', 'held', 'survived']) if (s.routed[k]) why[k] = true;
    finish(s, winner, why);
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
    patternTiles, lineTiles, coneTiles, radiusTiles, tileFx, healBlocked, hitsAllies, concealed,
    inBarrier, auraRadius, effArmor, effRes, guardianReduction, magicGuard, statusImmune, dirCategory, blockChance, calcHit,
    poisonDamage, poisonKey, poisonStacks, applyStatus, healAmount, hitFx, actUsable, targetsFrom, allTargets, sameTarget, actOf, affectedTiles, affectedUnits,
    previewAction, facingToward, lootAt, canLoot, takeLoot, nearBanner,
    canActivate, canActivateFor, readyUnits, beginActivation, cancelActivation, turnUnit, moveUnit, undoMove, canUndo, performAction,
    finishActivation, cooldown, turnsUntilReady, upcoming, queueDelay, inQueue, regenOf, fatigueHit, routHit, pass, endTurn, hasMove, usefulUnit, checkOutcome, forfeit, drainEvents,
    BLOCK_DMG, pendingWaves, waveSummary,
  };
})(typeof window !== 'undefined' ? window : globalThis);
