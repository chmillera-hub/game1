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

  // Campaign enemies (spec.foe) never heal: their masteries keep everything but the mending
  // and the rising again (a Skeleton Archer's Undying, say).
  const HEAL_TRAITS = ['bloodrage', 'auramend', 'martyr', 'phoenix'];
  function calmMastery(m) {
    if (!m.traits || !m.traits.some((t) => HEAL_TRAITS.includes(t))) return m;
    return Object.assign({}, m, { traits: m.traits.filter((t) => !HEAL_TRAITS.includes(t)) });
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
      if (lv >= 3 && D.MASTERY[spec.type]) out.push(spec.foe ? calmMastery(D.MASTERY[spec.type].mod) : D.MASTERY[spec.type].mod);
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
      // Arrived with a wave of reinforcements (for the Ambush bonus goal).
      reinforcement: !!spec.reinforcement,
      kills: 0,
      // Gold your army earns for breaking it: a barricade's pouch, or a little from any other building.
      bounty: spec.bounty || 0,
      // What it costs its side in Supply (for the readout of both armies' strength).
      supply: spec.supply || 0,
      salvage: T.salvage || 0,
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
      stats: { dmg: { P: 0, E: 0 }, kills: { P: 0, E: 0 }, gold: 0, escaped: 0, blocked: 0, waveKills: 0, lapGold: 0 },
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
      // Fatigue hits taken so far in the battle, by anyone (see fatigue).
      tire: { P: { on: false, n: 0, since: 0 }, E: { on: false, n: 0, since: 0 } },
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

  // Allies walk through each other (never stopping on one), and a castle gate opens for its
  // own garrison; anything else in the way blocks, unless the mover flies or shadowsteps
  // past enemies.
  function passable(u, o, flying, shadow) {
    if (o.team === u.team && o.traits.has('opens')) return true;
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

  // A cone: one tile, then rows of three (a drake's breath). Fanned (`fan`), it is the
  // other way round: rows of three, then one tile at the tip (a Lightning Ward's spray).
  function coneTiles(s, ox, oy, d, len, fan) {
    const [dx, dy] = DIRS[d];
    const px = -dy;
    const py = dx;
    const out = [];
    for (let i = 1; i <= len; i++) {
      const spread = fan ? (i === len ? 0 : 1) : i === 1 ? 0 : 1;
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
    if (!a || a.kind === 'none' || a.left <= 0 || !offCooldown(a)) return false;
    const A = s.act && s.act.uid === u.uid ? s.act : null;
    if (a.asMove) {
      if (A && A.moved) return false;
    } else if (A && A.acted) return false;
    if ((a.kind === 'blink' || a.kind === 'leap' || a.kind === 'shadowstrike') && (u.root > 0 || u.traits.has('immobile'))) return false;
    return true;
  }

  // A hook flies straight: same row or column, nothing but open ground, water or lava in
  // between (no rock, no unit).
  function clearLine(s, u, v) {
    if (u.x !== v.x && u.y !== v.y) return false;
    const d = dirFromDelta(v.x - u.x, v.y - u.y);
    for (let x = u.x + DIRS[d][0], y = u.y + DIRS[d][1]; x !== v.x || y !== v.y; x += DIRS[d][0], y += DIRS[d][1]) {
      if (s.terrain[idx(s, x, y)] === T_ROCK) return false;
      const o = at(s, x, y);
      if (o && o !== u) return false;
    }
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
          if (a.straight && !clearLine(s, u, v)) continue;
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
          const tiles = a.kind === 'line' ? lineTiles(s, u.x, u.y, d, a.len) : coneTiles(s, u.x, u.y, d, a.len, a.fan);
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
        return coneTiles(s, u.x, u.y, target.d, a.len, a.fan);
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
            if (fx.knock) e.knock = shoveForecast(s, u, v, fx.knock);
            else if (fx.pull) e.knock = shoveForecast(s, u, v, fx.pull, true);
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
    if (u.reinforcement && u.team === 'E') s.stats.waveKills = (s.stats.waveKills || 0) + 1;
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
    // A barricade broken by your army spills its gold, and any other enemy building a few
    // coins, paid with the battle's other gold.
    const coins = u.bounty || u.salvage;
    if (coins && src && src.team === 'P' && u.team !== 'P') {
      s.stats.bounty = (s.stats.bounty || 0) + coins;
      emit(s, { t: 'gold', uid: u.uid, amount: coins, x: u.x, y: u.y, coins: true });
    }
    // Every enemy unit (not a building, not a shrub) your army cuts down, at any point in the
    // battle, is worth a coin or two: 2 for a big one (3 Supply or more), 1 for the rest.
    // Ones that fall to their own fatigue pay nothing.
    if (src && src.team === 'P' && u.team === 'E' && !u.nonCombat && !u.structure && !u.traits.has('summon')) {
      const n = (u.supply || 0) >= LAP_BIG ? 2 : 1;
      s.stats.lapGold = (s.stats.lapGold || 0) + n;
      emit(s, { t: 'gold', uid: u.uid, amount: n, x: u.x, y: u.y, lap: true });
    }
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

  // A unit worth 2 gold rather than 1 when your army cuts it down (see kill).
  const LAP_BIG = 3;

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
    let dealt;
    if (amount >= tgt.hp && tgt.secondWind) {
      tgt.secondWind = false;
      dealt = tgt.hp - 1;
      tgt.hp = 1;
      emit(s, { t: 'dmg', uid: tgt.uid, amount, cat: info.cat, dmgType: info.dmgType, src: src ? src.uid : 0, fatigueNo: info.fatigueNo });
      emit(s, { t: 'secondwind', uid: tgt.uid });
    } else {
      dealt = Math.min(amount, tgt.hp);
      tgt.hp -= dealt;
      emit(s, { t: 'dmg', uid: tgt.uid, amount, cat: info.cat, dmgType: info.dmgType, src: src ? src.uid : 0, rout: info.rout || undefined, fatigueNo: info.fatigueNo });
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

  // Why a unit shrugs off a status (see statusImmune), for the board and the battle log.
  function immuneWhy(s, u, kind) {
    const tr = u.traits;
    if (kind === 'para' && u.boss) return 'boss';
    if (tr.has('undead') && kind === 'poison') return 'undead';
    if (u.tags.has('construct') && kind === 'poison') return 'construct';
    if (tr.has('stoneskin')) return 'stone skin';
    if (kind === 'root' && tr.has('immobile')) return 'rooted in place';
    if (tr.has('steadfast') || tr.has('paraproof') || tr.has('poisonproof')) return 'its loadout';
    if (inBarrier(s, u)) return 'Barrier Ward';
    return '';
  }

  // A status that does not take: the board says so over the unit's head.
  function resisted(s, u, kind) {
    emit(s, { t: 'resist', uid: u.uid, status: kind, why: immuneWhy(s, u, kind) });
  }

  function applyStatus(s, src, u, fx, act) {
    if (!u.alive || u.nonCombat || u.structure) return;
    if (fx.para) {
      if (statusImmune(s, u, 'para')) resisted(s, u, 'para');
      else {
        u.para = Math.max(u.para, fx.para);
        stamp(s, u, 'para');
        emit(s, { t: 'status', uid: u.uid, status: 'para', turns: u.para });
      }
    }
    if (fx.poison) {
      if (statusImmune(s, u, 'poison')) resisted(s, u, 'poison');
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
      if (statusImmune(s, u, 'root')) resisted(s, u, 'root');
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
    if (fx.knock && u.alive) shove(s, src, u, fx.knock);
    if (fx.pull && u.alive) shove(s, src, u, fx.pull, true);
  }

  // ------------------------------------------------------------ pushes and pulls
  // A shove moves a unit straight away from whoever shoved it; a pull drags it straight
  // toward them, stopping beside them. Tile by tile, up to the distance, until something
  // is in the way, and that hurts (true damage, past armor and block):
  //  - a rock or the edge of the field: it slams into it (8)
  //  - another unit or a building: a crash, and both take 6
  //  - water: it splashes in (6), climbs out onto the nearest dry tile, and is rooted
  //    for 1 turn while it shakes itself off (the water also puts out burns)
  //  - lava: it falls in (12), climbs out the same way, and burns (5 for 2 turns)
  // Flyers sail over water and lava, but still slam into rocks, the edge and units. Bosses,
  // huge units, the steadfast and anything rooted to the spot do not budge.
  const IMPACT = { rock: 8, edge: 8, unit: 6, water: 6, lava: 12 };

  // The direction a shove (or, with pull, a drag) sends u, from `src`'s tile.
  function shoveDir(src, u, pull) {
    let d = pull ? dirFromDelta(src.x - u.x, src.y - u.y) : dirFromDelta(u.x - src.x, u.y - src.y);
    if (d < 0) d = src.facing >= 0 ? src.facing : 0;
    return d;
  }

  // Where it would go: the tiles it passes, and what stops it at the end (null: nothing).
  // A pull never drags it onto the puller's own tile.
  function forcePath(s, src, u, dist, pull) {
    const d = shoveDir(src, u, pull);
    const flying = u.traits.has('flying');
    const steps = [];
    let x = u.x;
    let y = u.y;
    for (let i = 0; i < dist; i++) {
      const nx = x + DIRS[d][0];
      const ny = y + DIRS[d][1];
      if (pull && nx === src.x && ny === src.y) break;
      if (!inB(s, nx, ny)) return { d, steps, end: 'edge', x: nx, y: ny };
      const t = s.terrain[idx(s, nx, ny)];
      if (t === T_ROCK) return { d, steps, end: 'rock', x: nx, y: ny };
      const o = at(s, nx, ny);
      if (o && o !== u) return { d, steps, end: 'unit', other: o.uid, x: nx, y: ny };
      steps.push([nx, ny]);
      x = nx;
      y = ny;
      if (!flying && (t === T_WATER || t === T_LAVA)) return { d, steps, end: t === T_WATER ? 'water' : 'lava', x, y };
    }
    return { d, steps, end: null, x, y };
  }

  // How far a shove or pull goes, and how hard what stops it hits, with relics.
  function shoveDist(s, src, u, dist) {
    return dist + (src && src.team !== u.team && s.relics[src.team].has('tide_conch') ? 1 : 0);
  }
  function impactOf(s, src, v, end) {
    return (IMPACT[end] || 0) + (src && src.team !== v.team && s.relics[src.team].has('iron_ram') ? 6 : 0);
  }
  function unmovable(s, src, u) {
    return statusImmune(s, u, 'knock') || (src && src.team !== u.team && s.relics[u.team].has('anchor_stone'));
  }

  // What a shove or pull would do, for previews and the AI: 'resist', or where it ends up,
  // what stops it and the damage dealt (dmg to it, otherDmg to a unit it crashes into).
  function shoveForecast(s, src, u, dist, pull) {
    if (unmovable(s, src, u)) return 'resist';
    const p = forcePath(s, src, u, shoveDist(s, src, u, dist), pull);
    const out = { pull: !!pull, n: p.steps.length, end: p.end, x: p.x, y: p.y, dmg: p.end ? impactOf(s, src, u, p.end) : 0 };
    if (p.end === 'unit') {
      out.other = p.other;
      out.otherDmg = impactOf(s, src, s.byId[p.other], 'unit');
    }
    return out;
  }

  function shove(s, src, u, dist, pull) {
    if (!u.alive) return;
    if (unmovable(s, src, u)) {
      emit(s, { t: 'resist', uid: u.uid, why: 'steady' });
      return;
    }
    const p = forcePath(s, src, u, shoveDist(s, src, u, dist), pull);
    let from = [u.x, u.y];
    for (let i = 0; i < p.steps.length; i++) {
      const [x, y] = p.steps[i];
      from = [u.x, u.y];
      relocate(s, u, x, y);
      emit(s, { t: 'push', uid: u.uid, x, y, pull: !!pull, by: src ? src.uid : 0 });
      // Fire underfoot burns it as it passes; caltrops stop it on the spot.
      const wet = i === p.steps.length - 1 && (p.end === 'water' || p.end === 'lava');
      if (!wet && (enterTile(s, u, x, y) || !u.alive)) return;
    }
    const opts = { cat: 'none', dmgType: 'true' };
    if (p.end === 'rock' || p.end === 'edge') {
      emit(s, { t: 'slam', uid: u.uid, x: p.x, y: p.y, why: p.end });
      applyDamage(s, src, u, impactOf(s, src, u, p.end), opts);
    } else if (p.end === 'unit') {
      const o = s.byId[p.other];
      emit(s, { t: 'crash', uid: u.uid, other: o.uid, x: o.x, y: o.y });
      applyDamage(s, src, u, impactOf(s, src, u, 'unit'), opts);
      applyDamage(s, src, o, impactOf(s, src, o, 'unit'), opts);
    } else if (p.end === 'water' || p.end === 'lava') dunk(s, src, u, p.end === 'lava', from);
  }

  // Shoved into water or lava: the hit, then it climbs out onto the nearest dry open tile
  // (back the way it came, if it can) and pays for it.
  function dunk(s, src, u, lava, from) {
    emit(s, { t: 'dunk', uid: u.uid, x: u.x, y: u.y, lava });
    applyDamage(s, src, u, impactOf(s, src, u, lava ? 'lava' : 'water'), { cat: 'none', dmgType: 'true' });
    if (!u.alive) return;
    let best = null;
    for (let y = 0; y < s.h; y++)
      for (let x = 0; x < s.w; x++) {
        if (s.terrain[idx(s, x, y)] !== T_GRASS || at(s, x, y)) continue;
        const k = manhattan(u.x, u.y, x, y) * 10 + manhattan(from[0], from[1], x, y);
        if (!best || k < best.k) best = { x, y, k };
      }
    if (best) {
      relocate(s, u, best.x, best.y);
      emit(s, { t: 'climb', uid: u.uid, x: best.x, y: best.y });
    }
    if (lava) applyStatus(s, src || u, u, { burn: [2, 5] });
    else {
      if (u.burn) {
        u.burn = null;
        emit(s, { t: 'cleanse', uid: u.uid });
      }
      applyStatus(s, src || u, u, { root: 1 });
    }
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
    const strike = (v, o) => {
      if (!v.alive) return;
      let landed = true;
      if (a.dmg) landed = !hit(s, u, v, o || opts).blocked;
      if (landed && v.alive && v.team !== u.team && hasFx(fx)) applyStatus(s, u, v, fx, a);
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
          if (v && v.alive && u.alive) shove(s, u, v, 1);
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
        const u = addUnit(s, Object.assign({}, spec, { team, x: tile[0], y: tile[1], facing: team === 'E' ? 2 : 0, born: s.turn, reinforcement: true }));
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
      applyDamage(s, s.byId[u.poison.src] || null, u, u.poison.dmg, { cat: 'none', dmgType: 'poison' });
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
    // War totems whip allies within 2 tiles into a frenzy (25% more damage) while they stand.
    // Enemies barely ever heal: a totem never mends anyone.
    const totems = mine.filter((w) => w.alive && w.props.totemRage);
    if (totems.length) {
      const pulsed = new Set();
      for (const v of mine) {
        if (!v.alive || v.nonCombat || v.structure) continue;
        const w = totems.find((t) => manhattan(v.x, v.y, t.x, t.y) <= 2);
        if (!w) continue;
        if (!pulsed.has(w.uid)) {
          pulsed.add(w.uid);
          emit(s, { t: 'totem', uid: w.uid });
        }
        // Announced when it starts, not every turn the totem keeps it going.
        if (v.frenzy === 0) emit(s, { t: 'status', uid: v.uid, status: 'frenzy', turns: 2 });
        v.frenzy = Math.max(v.frenzy, 2);
        stamp(s, v, 'frenzy');
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
  }

  // The start of one unit's own turn, acting or passing, always in this order: its fatigue,
  // then poison, then burns, then fire underfoot, then regen. (Then it acts, or passes and
  // its cooldown ticks down.) The board plays each of these as a beat of its own.
  function unitTurnStart(s, u) {
    for (const a of u.acts) if (a.cdLeft > 0) a.cdLeft--;
    // A troll hurt by magic or fire since its last turn does not regenerate this turn.
    u.burnt = u.scorched;
    u.scorched = false;
    fatigue(s, u);
    tickDot(s, u, 'poison');
    tickDot(s, u, 'burn');
    if (u.alive && !u.traits.has('flying')) {
      const fire = tileFx(s, u.x, u.y, 'fire');
      if (fire && fire.team !== u.team) {
        emit(s, { t: 'scorch', uid: u.uid, x: u.x, y: u.y });
        magicDamage(s, s.byId[fire.src] || null, u, fire.dmg || FIRE_DMG, 'burn');
      }
    }
    if (u.alive) regenerate(s, u);
  }

  // Fatigue, past armor and shields: one unit at a time, never a side at once. Each side has
  // a fatigue timer of its own, off at first. Once a side's timer is on, each of its units
  // loses HP as its own turn comes, before it moves, acts or passes (see pickDue): that
  // side's next number, 1 for its first hit, then 2, 3 and so on, one more every time one
  // of its units takes its turn. Five of your units passing in a row at 15 lose 15, 16, 17,
  // 18 and 19. The two sides count apart, and neither count ever resets or doubles.
  // Your timer switches on when the mission is done or the enemy army falls (the win is
  // yours, see lockWin), the enemy's when the mission is done; turn s.overtime switches on
  // any timer still off and does nothing to one already on (see startFatigue).
  function fatigue(s, u) {
    if (!u.alive || !counts(u) || !s.tire[u.team].on) return;
    const n = ++s.tire[u.team].n;
    applyDamage(s, null, u, n, { cat: 'none', dmgType: 'fatigue', fatigueNo: n });
  }

  // Switch `team`'s fatigue timer on, at 1. Already on: nothing happens.
  function startTiring(s, team) {
    if (s.tire[team].on) return false;
    s.tire[team].on = true;
    s.tire[team].since = s.turn;
    return true;
  }

  function tiring(s, team) {
    return s.tire[team].on;
  }

  // What `team`'s next unit to take its turn loses to fatigue (0 while its timer is off).
  function fatigueHit(s, team) {
    return s.tire[team].on ? s.tire[team].n + 1 : 0;
  }

  // The win is yours from here on, whatever happens: the mission is done, or the enemy army
  // has fallen with something left to collect. The battle goes on while there is anything
  // left to fight or collect and anyone left to do it, with your fatigue timer on, so you
  // can grab a few more barricades or bonus goals before fatigue wears your army down.
  // Bonus goals about losses and speed are judged as of now. Finish now ends it.
  function lockWin(s) {
    if (s.won) return;
    s.won = { turn: s.turn, lost: s.units.filter((u) => u.team === 'P' && !u.nonCombat && !u.alive).length };
  }

  // The mission is done: the cage broken, the wagons or the warbanner wrecked, the seal or
  // the shrine held, the commander or the boss slain, the waves outlasted. The win is yours
  // (see lockWin). The battle goes on: both fatigue timers switch on, each at 1 (a timer
  // already on carries on), so the enemy wears down while your army goes for whatever else
  // it can get. Reinforcements still march in (until turn s.overtime), so an ambush bonus
  // is still there for the taking.
  function rout(s, why) {
    if (s.routed || s.over) return;
    const was = { E: tiring(s, 'E'), P: tiring(s, 'P') };
    s.routed = Object.assign({ turn: s.turn }, why);
    lockWin(s);
    startTiring(s, 'E');
    startTiring(s, 'P');
    if (s.surviveTurns) s.surviveTurns = 0;
    if (s.hold) s.hold.done = true;
    emit(s, Object.assign({ t: 'routed', turn: s.turn, was }, why));
  }

  // The enemy's next fatigue hit once routed, and your army's once the win is yours.
  function routHit(s) {
    return s.routed ? fatigueHit(s, 'E') : 0;
  }
  function cleanupHit(s) {
    return s.won ? fatigueHit(s, 'P') : 0;
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
        if (s.won) return endCleanup(s);
        return finish(s, strength(s, 'P') > strength(s, 'E') ? 'P' : 'E', { timeout: true });
      }
      if (s.surviveTurns && s.turn > s.surviveTurns) rout(s, { survived: true });
    }
    startFatigue(s);
    startEffects(s, side);
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

  // Fatigue for everyone: on turn `s.overtime` each side's timer still off switches on, at
  // 1; a timer already on (yours after the win, the enemy's after the mission) carries on
  // untouched. No more reinforcements come. Big units and regen last longest; the last
  // side standing wins. `was` says which timers were already on.
  function startFatigue(s) {
    if (!s.overtime || s.turn < s.overtime || s.inOvertime || s.over) return;
    const was = { E: tiring(s, 'E'), P: tiring(s, 'P') };
    s.inOvertime = true;
    startTiring(s, 'E');
    startTiring(s, 'P');
    for (const w of s.waves) if (w.state === 'pending') w.state = 'cancelled';
    emit(s, { t: 'overtime', turn: s.turn, was });
  }

  // ---------------------------------------------------------------- unit queue
  //
  // In queue battles each side's units take that side's turns in a set rotation: every
  // unit gets one turn per cycle, faster units first (ties: the earlier unit). A unit that
  // is cooling down, paralyzed or has nothing it could do still has its turn, but passes
  // it at once, and the next in line goes. Cooldowns, paralysis, roots, weakness and
  // frenzy count the unit's own turns, taken or passed.

  // Wards (Barrier and Lightning Wards) keep their place in the rotation even with nothing
  // to do: their turns come like everyone's.
  function inQueue(u) {
    return u.alive && !u.nonCombat && (hasAction(u) || isWard(u));
  }

  function isWard(u) {
    return u.traits.has('immobile') && counts(u);
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

  // The side's unit for this turn. Units take their turns in rotation order; one that is
  // cooling down, paralyzed or has nothing it could do passes its turn (its cooldown ticks
  // down) and the next in line goes, each unit at most once a side's turn. If everyone
  // passes, the side passes. Whatever comes with a unit's turn comes whether it acts or
  // passes: poison, burns, regen and fatigue.
  function pickDue(s, side) {
    s.due = 0;
    const seen = new Set();
    for (;;) {
      const u = s.units.filter((v) => v.team === side && inQueue(v)).sort(byQueue)[0];
      if (!u || seen.has(u.uid)) break;
      seen.add(u.uid);
      unitTurnStart(s, u);
      if (!u.alive) {
        checkOutcome(s);
        if (s.over) return;
        continue;
      }
      const why = sitOutReason(s, u);
      if (!why) {
        s.due = u.uid;
        return;
      }
      // A ward with no action at all (the Barrier Ward) passes every turn.
      emit(s, { t: 'sitout', uid: u.uid, why: hasAction(u) ? why : 'passive', wait: u.wait, para: u.para });
      ownTurnDone(s, u);
    }
  }

  // Who takes each of `team`'s next `n` turns, predicted from the rotation as it stands
  // (each assumed to act and start its cooldown). Entries: { uid, passes } or { uid: 0,
  // passes } for a turn nobody can take; `passes` lists the units whose turns come first
  // that turn and are passed ({ uid, wait, para, why }), cooling down, paralyzed or never
  // acting (the Barrier Ward).
  function upcoming(s, team, n) {
    const vs = s.units.filter((v) => v.team === team && inQueue(v)).map((v) => ({ v, cycles: v.cycles, wait: v.wait, para: v.para, spd: v.spd, uid: v.uid, idle: !hasAction(v) }));
    const out = [];
    for (let turn = 0; turn < n && vs.length; turn++) {
      let picked = null;
      const passes = [];
      if (turn === 0 && s.side === team && s.due) picked = vs.find((x) => x.uid === s.due) || null;
      const seen = new Set();
      while (!picked) {
        vs.sort(byQueue);
        const x = vs[0];
        if (seen.has(x)) break;
        seen.add(x);
        const resting = x.para > 0 || x.wait > 0 || x.idle;
        if (resting) passes.push({ uid: x.uid, wait: x.wait, para: x.para, why: x.idle ? 'passive' : x.wait > 0 ? 'cooldown' : 'para' });
        x.cycles++;
        if (x.wait > 0) x.wait--;
        else if (x.para > 0) x.para--;
        if (!resting) picked = x;
        else continue;
        break;
      }
      if (!picked) {
        out.push({ uid: 0, passes });
        continue;
      }
      if (turn === 0 && s.side === team && s.due) picked.cycles++;
      picked.wait = picked.v.rec;
      out.push({ uid: picked.uid, passes });
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

  // ------------------------------------------------------------ cleanup
  // The enemy army is gone but the field still holds something worth having: loot, and
  // enemy buildings with gold in them or a goal to break (a totem, the cage, a wagon, a
  // barricade, a wall). The win is already yours. Your army goes round collecting until
  // nothing is left or until it has nobody left standing: there is no other limit, as its
  // fatigue sets in at once and grows with every turn it takes (see fatigue). It cannot
  // cost you the battle. Finish now (or a retreat) ends it early.
  function cleanupTargets(s) {
    return s.units.filter((u) => u.alive && u.team === 'E' && !u.escaped && (u.nonCombat || u.structure) && !u.traits.has('summon') && (u.goal || u.bounty > 0 || u.salvage > 0));
  }
  function cleanupLoot(s) {
    return (s.loot || []).filter((l) => !l.taken);
  }
  function cleanupLeft(s) {
    return cleanupTargets(s).length + cleanupLoot(s).length;
  }
  // Why the enemy broke, for the result screen (vipSlain, destroyed, held, survived).
  function brokeWhy(s) {
    const why = {};
    if (s.routed) for (const k of ['vipSlain', 'destroyed', 'held', 'survived']) if (s.routed[k]) why[k] = true;
    return why;
  }
  // Take the win now, once it is yours (the player's Finish now, or a retreat after it).
  function endCleanup(s) {
    if (s.over || !s.won) return;
    finish(s, 'P', Object.assign(brokeWhy(s), s.cleanup ? { cleaned: cleanupLeft(s) === 0 } : {}));
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
    if (s.won || winner === 'P') {
      // The win is yours (the mission done, or the enemy army down). It goes on while there
      // is someone left to fight or something left to collect, and someone to do it.
      if (alive.P && !alive.E && cleanupLeft(s) && !s.cleanup) {
        // The enemy army is down with gold, goals or loot still on the field: collect them.
        const was = tiring(s, 'P');
        lockWin(s);
        s.cleanup = { turn: s.turn, lost: s.units.filter((u) => u.team === 'P' && !u.nonCombat && !u.alive).length };
        startTiring(s, 'P');
        emit(s, { t: 'cleanup', turn: s.turn, left: cleanupLeft(s), was, next: fatigueHit(s, 'P') });
      }
      if (alive.P && (alive.E || cleanupLeft(s))) return;
      winner = 'P';
    }
    if (!winner) return;
    // A win after a rout keeps why the enemy broke (vipSlain, destroyed, held, survived).
    const why = winner === 'P' ? brokeWhy(s) : {};
    if (s.cleanup) why.cleaned = cleanupLeft(s) === 0;
    if (s.won) why.locked = true;
    finish(s, winner, why);
  }

  function forfeit(s) {
    if (s.won) return endCleanup(s);
    if (!s.over) finish(s, 'E', { forfeit: true });
  }

  function drainEvents(s) {
    const ev = s.events;
    s.events = [];
    return ev;
  }

  AG.Engine = {
    T_GRASS, T_ROCK, T_WATER, T_LAVA, IMPACT, shoveForecast, forcePath, clearLine, cleanupTargets, cleanupLoot, cleanupLeft, endCleanup,
    other, manhattan, idx, inB, at, dirFromDelta, unitValue, buildUnit, specMods,
    canDealDamage, strength, counts, createBattle, addUnit, withUnitAt, reachable, findPath,
    patternTiles, lineTiles, coneTiles, radiusTiles, tileFx, healBlocked, hitsAllies, concealed,
    inBarrier, auraRadius, effArmor, effRes, guardianReduction, magicGuard, statusImmune, dirCategory, blockChance, calcHit,
    poisonDamage, poisonKey, poisonStacks, applyStatus, healAmount, hitFx, actUsable, targetsFrom, allTargets, sameTarget, actOf, affectedTiles, affectedUnits,
    previewAction, facingToward, lootAt, canLoot, takeLoot, nearBanner,
    canActivate, canActivateFor, readyUnits, beginActivation, cancelActivation, turnUnit, moveUnit, undoMove, canUndo, performAction,
    finishActivation, cooldown, turnsUntilReady, upcoming, queueDelay, inQueue, regenOf, fatigueHit, tiring, routHit, cleanupHit, pass, endTurn, hasMove, usefulUnit, checkOutcome, forfeit, drainEvents,
    BLOCK_DMG, pendingWaves, waveSummary,
  };
})(typeof window !== 'undefined' ? window : globalThis);
