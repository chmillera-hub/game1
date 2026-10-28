// Hero Delve: the dungeon layer. Your party (four heroes and the Cleric, all Level 3) goes
// down the Forgotten Tower a floor at a time. Each floor is one big battle for the engine:
// the monster packs sleep in their rooms until the party comes near (see wakeCheck), and
// between fights the party's AI walks on toward the next pack it has not met.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const D = AG.Data;
  const E = AG.Engine;
  const { UNITS, ABILITIES, TALENTS, SKILLS, GEAR, NAMES, SKILL_SLOTS, GEAR_SLOTS, TALENT_SLOTS } = D;

  const SAVE_KEY = 'hero-delve-v1';
  const FLOORS = 5;
  const W = 24;
  const H = 24;
  const LEVEL = 3;
  const HERO_SLOTS = 4;
  // A hero who fell gets back up at the shrine by the stairs, with this much HP.
  const SHRINE_HP = 0.4;

  // Hero classes you can bring: every recruitable unit that walks (no wards), the Cleric aside.
  const CLASSES = D.RECRUITABLE.filter((t) => t !== 'cleric' && UNITS[t].role !== 'ward' && !UNITS[t].traits.includes('immobile'));

  // The tower, floor by floor: who sleeps in its rooms, how many to a pack, how strong.
  const FLOOR_DEFS = [
    null,
    { name: 'Level 1', pool: ['skeleton', 'skeleton', 'spider', 'skelarcher'], pack: [2, 3], lv: [1, 1], empty: 0.25 },
    { name: 'Level 2', pool: ['skeleton', 'skelarcher', 'specter', 'spider'], pack: [2, 4], lv: [1, 2], empty: 0.2 },
    { name: 'Level 3', pool: ['skelarcher', 'specter', 'cutthroat', 'spider', 'skeleton'], pack: [3, 4], lv: [1, 2], empty: 0.15 },
    { name: 'Level 4', pool: ['specter', 'cutthroat', 'crossbow', 'necromancer', 'skeleton'], pack: [3, 4], lv: [2, 2], empty: 0.1, shackler: 1 },
    { name: 'Level 5', pool: ['cutthroat', 'specter', 'skelarcher', 'skeleton'], pack: [3, 4], lv: [2, 3], empty: 0.1, boss: 'countess', bossPack: ['cutthroat', 'specter', 'skeleton'] },
  ];

  // What the stash starts with: a few skills and pieces of gear to share out.
  const STARTER = [
    ['skill', 'vampiric'], ['skill', 'last_stand'], ['skill', 'executioner'], ['skill', 'guardian'], ['skill', 'undying_rage'], ['skill', 'flanker'],
    ['gear', 'healing_charm'], ['gear', 'reactive_plate'], ['gear', 'porcupine_ring'], ['gear', 'hex_charm'], ['gear', 'fire_flask'], ['gear', 'healing_draught'],
  ];
  const STARTER_PARTY = ['knight', 'archer', 'pyromancer', 'berserker'];

  // ------------------------------------------------------------ profile

  function newProfile() {
    const p = { v: 1, nextId: 1, party: [], cleric: null, stash: [], stats: { runs: 0, clears: 0, best: 0 }, run: null };
    for (const t of STARTER_PARTY) p.party.push(newHero(p, t));
    p.cleric = newHero(p, 'cleric');
    for (const [kind, id] of STARTER) addItem(p, kind, id);
    autoKit(p);
    return p;
  }

  function newHero(p, type) {
    const T = UNITS[type];
    const used = new Set(heroes(p).map((h) => h.name));
    const free = NAMES.filter((n) => !used.has(n));
    const name = free[(p.nextId * 7) % free.length] || 'Hero ' + p.nextId;
    return { id: 'h' + p.nextId++, type, name, a1: firstPick(T, 1), a2: firstPick(T, 2), talents: [], skills: [], gear: [] };
  }

  // The first level pick that is not a talent (talents go in their own slots).
  function firstPick(T, tier) {
    const list = (T.abilities && T.abilities[tier]) || [];
    return list.find((id) => !TALENTS[id]) || list[0] || null;
  }

  function heroes(p) {
    return p.party.concat(p.cleric ? [p.cleric] : []).filter(Boolean);
  }

  function addItem(p, kind, id) {
    const it = { uid: 'i' + p.nextId++, kind, id };
    p.stash.push(it);
    return it;
  }

  function itemDef(it) {
    return it ? (it.kind === 'skill' ? SKILLS[it.id] : GEAR[it.id]) : null;
  }

  function itemByUid(p, uid) {
    return p.stash.find((i) => i.uid === uid) || null;
  }

  // The hero an item is equipped on, if any.
  function holderOf(p, uid) {
    return heroes(p).find((h) => h.skills.includes(uid) || h.gear.includes(uid)) || null;
  }

  // Level picks for this class at this tier (talents excluded: those go in talent slots).
  function picks(type, tier) {
    const T = UNITS[type];
    return ((T.abilities && T.abilities[tier]) || []).filter((id) => !TALENTS[id]);
  }

  function classTalents(type) {
    return Object.keys(TALENTS).filter((id) => TALENTS[id].cls === type);
  }

  const SLOTS = { talents: TALENT_SLOTS[LEVEL], skills: SKILL_SLOTS[LEVEL], gear: GEAR_SLOTS[LEVEL] };

  // Keep a hero's kit legal: real picks, its own class talents, eligible items it holds alone.
  function normalize(p, h) {
    const T = UNITS[h.type];
    if (!picks(h.type, 1).includes(h.a1)) h.a1 = firstPick(T, 1);
    if (!picks(h.type, 2).includes(h.a2)) h.a2 = firstPick(T, 2);
    h.talents = [...new Set(h.talents)].filter((id) => TALENTS[id] && TALENTS[id].cls === h.type).slice(0, SLOTS.talents);
    const taken = new Set(heroes(p).filter((o) => o !== h).flatMap((o) => o.skills.concat(o.gear)));
    const ok = (uid, kind) => {
      const it = itemByUid(p, uid);
      return it && it.kind === kind && !taken.has(uid) && D.eligible(h.type, itemDef(it));
    };
    h.skills = h.skills.filter((uid) => ok(uid, 'skill')).slice(0, SLOTS.skills);
    h.gear = h.gear.filter((uid) => ok(uid, 'gear')).slice(0, SLOTS.gear);
    return h;
  }

  // Fill every empty slot with the best free fit: class talents first, then items.
  function autoKit(p, only) {
    for (const h of only ? [only] : heroes(p)) {
      normalize(p, h);
      for (const id of classTalents(h.type)) if (h.talents.length < SLOTS.talents && !h.talents.includes(id)) h.talents.push(id);
      for (const [kind, key] of [['skill', 'skills'], ['gear', 'gear']]) {
        const free = p.stash
          .filter((it) => it.kind === kind && !holderOf(p, it.uid) && D.eligible(h.type, itemDef(it)) && !itemDef(it).side)
          .sort((a, b) => (itemDef(b).cost || 0) - (itemDef(a).cost || 0));
        for (const it of free) if (h[key].length < SLOTS[key]) h[key].push(it.uid);
      }
    }
  }

  // The engine spec for a hero.
  function specOf(p, h) {
    normalize(p, h);
    return {
      type: h.type,
      level: LEVEL,
      a1: h.a1,
      a2: h.a2,
      talents: h.talents.slice(),
      skills: h.skills.map((uid) => itemByUid(p, uid).id),
      gear: h.gear.map((uid) => itemByUid(p, uid).id),
      rid: h.id,
      name: h.name,
    };
  }

  // Swap a party slot to a new class: a fresh hero, kitted from what is free.
  function setClass(p, slot, type) {
    if (!CLASSES.includes(type)) return null;
    const h = newHero(p, type);
    p.party[slot] = h;
    autoKit(p, h);
    save(p);
    return h;
  }

  function save(p) {
    try {
      root.localStorage && root.localStorage.setItem(SAVE_KEY, JSON.stringify(p));
    } catch (e) {
      /* storage blocked: the session still plays */
    }
  }

  function load() {
    try {
      const j = root.localStorage && root.localStorage.getItem(SAVE_KEY);
      const p = j ? JSON.parse(j) : null;
      if (p && p.v === 1 && p.party && p.cleric) return p;
    } catch (e) {
      /* fall through to a new profile */
    }
    return null;
  }

  // ------------------------------------------------------------ floors

  const idx = (x, y) => y * W + x;
  const T_FLOOR = 0;
  const T_WALL = 1;

  function genFloor(seed, floor) {
    const def = FLOOR_DEFS[floor];
    const rng = AG.derive(seed, 'floor:' + floor);
    const terrain = new Array(W * H).fill(T_WALL);
    const rooms = [];
    const fits = (x, y, w, h) => x >= 1 && y >= 1 && x + w <= W - 1 && y + h <= H - 1 && !rooms.some((r) => x < r.x + r.w + 2 && x + w + 2 > r.x && y < r.y + r.h + 2 && y + h + 2 > r.y);
    const add = (x, y, w, h) => {
      const r = { x, y, w, h, cx: x + (w >> 1), cy: y + (h >> 1) };
      rooms.push(r);
      for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) terrain[idx(xx, yy)] = T_FLOOR;
      return r;
    };
    // The way in at the top corner, the way down (or the Countess) at the far one.
    const start = add(1 + rng.int(2), 1 + rng.int(2), 5, 5);
    const bw = floor === FLOORS ? 8 : 6;
    const end = add(W - 1 - bw - rng.int(2), H - 1 - bw - rng.int(2), bw, bw);
    for (let tries = 0; tries < 500 && rooms.length < 9; tries++) {
      const w = rng.range(4, 7);
      const h = rng.range(4, 7);
      const x = rng.range(1, W - 1 - w);
      const y = rng.range(1, H - 1 - h);
      if (fits(x, y, w, h)) add(x, y, w, h);
    }
    // Corridors two tiles wide along a minimum spanning tree, and a loop or two.
    const dig = (x, y) => {
      for (const [dx, dy] of [[0, 0], [1, 0], [0, 1], [1, 1]]) {
        const xx = Math.min(W - 2, x + dx);
        const yy = Math.min(H - 2, y + dy);
        terrain[idx(xx, yy)] = T_FLOOR;
      }
    };
    const corridor = (a, b) => {
      const horizontalFirst = rng.chance(0.5);
      let x = a.cx;
      let y = a.cy;
      const stepX = () => {
        while (x !== b.cx) {
          dig(x, y);
          x += Math.sign(b.cx - x);
        }
      };
      const stepY = () => {
        while (y !== b.cy) {
          dig(x, y);
          y += Math.sign(b.cy - y);
        }
      };
      if (horizontalFirst) (stepX(), stepY());
      else (stepY(), stepX());
      dig(x, y);
    };
    const dist = (a, b) => Math.abs(a.cx - b.cx) + Math.abs(a.cy - b.cy);
    const inTree = [rooms[0]];
    const out = rooms.slice(1);
    const links = [];
    while (out.length) {
      let best = null;
      for (const a of inTree) for (const b of out) if (!best || dist(a, b) < dist(best[0], best[1])) best = [a, b];
      links.push(best);
      inTree.push(best[1]);
      out.splice(out.indexOf(best[1]), 1);
    }
    for (let k = 0; k < 2; k++) {
      const a = rng.pick(rooms);
      const b = rng.pick(rooms);
      if (a !== b) links.push([a, b]);
    }
    for (const [a, b] of links) corridor(a, b);
    // A pillar or two in the bigger rooms, for cover (never in the first room).
    for (const r of rooms) {
      if (r === start || r.w < 6 || r.h < 6) continue;
      for (const [px, py] of [[r.x + 1, r.y + 1], [r.x + r.w - 2, r.y + r.h - 2]]) if (rng.chance(0.6)) terrain[idx(px, py)] = T_WALL;
    }
    // Only what the party can walk to counts: a pillar never seals a room off.
    const reach = flood(terrain, start.cx, start.cy);
    for (let i = 0; i < W * H; i++) if (terrain[i] === T_FLOOR && !reach[i]) terrain[i] = T_WALL;

    // Who sleeps where.
    const monsters = [];
    let pack = 0;
    const taken = new Set();
    const spotsIn = (r) => {
      const out = [];
      for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) if (terrain[idx(x, y)] === T_FLOOR && !taken.has(idx(x, y))) out.push([x, y]);
      return rng.shuffle(out).sort((a, b) => Math.abs(a[0] - r.cx) + Math.abs(a[1] - r.cy) - (Math.abs(b[0] - r.cx) + Math.abs(b[1] - r.cy)));
    };
    const place = (r, types, lv) => {
      pack++;
      const spots = spotsIn(r);
      types.forEach((type, i) => {
        const s = spots[i];
        if (!s) return;
        taken.add(idx(s[0], s[1]));
        monsters.push({ type, level: lv, x: s[0], y: s[1], facing: rng.int(4), asleep: true, pack });
      });
    };
    let shacklers = def.shackler || 0;
    for (const r of rooms) {
      if (r === start) continue;
      if (r === end && def.boss) {
        place(r, [def.boss].concat(def.bossPack), Math.max(...def.lv));
        continue;
      }
      if (r !== end && rng.chance(def.empty)) continue;
      const n = rng.range(def.pack[0], def.pack[1]) + (r === end ? 1 : 0);
      const types = [];
      for (let i = 0; i < n; i++) types.push(rng.pick(def.pool));
      if (shacklers > 0 && r !== end && rng.chance(0.5)) {
        types[0] = 'shackler';
        shacklers--;
      }
      place(r, types, rng.range(def.lv[0], def.lv[1]));
    }
    return { floor, name: def.name, w: W, h: H, terrain, rooms, start, end, monsters, boss: def.boss || null };
  }

  // Tiles reachable on foot from (x, y).
  function flood(terrain, x, y) {
    const seen = new Uint8Array(W * H);
    const q = [[x, y]];
    seen[idx(x, y)] = 1;
    while (q.length) {
      const [cx, cy] = q.pop();
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = cx + dx;
        const ny = cy + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const i = idx(nx, ny);
        if (seen[i] || terrain[i] !== T_FLOOR) continue;
        seen[i] = 1;
        q.push([nx, ny]);
      }
    }
    return seen;
  }

  // ------------------------------------------------------------ a delve

  // A new descent: floor 1, everyone at full HP.
  function startRun(p, seed) {
    p.run = { seed: seed || ((Date.now() % 1e9) + 1), floor: 1, hp: {}, loot: [], kills: 0 };
    p.stats.runs++;
    save(p);
    return p.run;
  }

  // The battle for the current floor: the party at the way in, the floor's packs asleep.
  function floorBattle(p) {
    const run = p.run;
    const fl = genFloor(run.seed, run.floor);
    const units = [];
    const r = fl.start;
    const spots = [];
    for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) if (fl.terrain[idx(x, y)] === T_FLOOR) spots.push([x, y]);
    spots.sort((a, b) => Math.abs(a[0] - r.cx) + Math.abs(a[1] - r.cy) - (Math.abs(b[0] - r.cx) + Math.abs(b[1] - r.cy)));
    heroes(p).forEach((h, i) => {
      const frac = run.hp[h.id] == null ? 1 : run.hp[h.id] <= 0 ? SHRINE_HP : run.hp[h.id];
      units.push(Object.assign(specOf(p, h), { team: 'P', x: spots[i][0], y: spots[i][1], facing: 1, hpFrac: frac < 1 ? frac : undefined }));
    });
    for (const m of fl.monsters) units.push(Object.assign({ team: 'E', foe: true }, m));
    const s = E.createBattle({
      w: fl.w,
      h: fl.h,
      terrain: fl.terrain,
      units,
      relics: { P: [], E: [] },
      seed: run.seed + run.floor * 7919,
      objective: 'all',
      turnLimit: 100000,
      loot: [],
      goals: [],
      waves: [],
      queue: true,
    });
    return { s, fl };
  }

  // After a floor: who is left and how hurt, onward (or the tower is beaten).
  function finishFloor(p, s) {
    const run = p.run;
    for (const u of s.units) if (u.team === 'P' && u.rid) run.hp[u.rid] = u.alive ? u.hp / u.maxHp : 0;
    p.stats.best = Math.max(p.stats.best, run.floor);
    if (run.floor >= FLOORS) {
      p.stats.clears++;
      p.run = null;
      save(p);
      return { done: true };
    }
    run.floor++;
    save(p);
    return { done: false, floor: run.floor };
  }

  function endRun(p) {
    p.run = null;
    save(p);
  }

  // The party's orders when you have set none. Walking: the nearest sleeping monster it can
  // reach. Fighting: its own judgement, unless the fight has stalled (`idle` plies without a
  // blow, both sides waiting for the other), then the nearest awake monster, all out.
  const STALL = 12;
  function exploreTarget(s, idle) {
    const awake = s.units.filter((u) => u.alive && u.team === 'E' && !u.asleep && !u.nonCombat);
    if (awake.length) {
      if ((idle || 0) < STALL) return null;
      const m = nearest(s, (v) => awake.includes(v));
      return m ? { uid: m.uid } : null;
    }
    const m = nearest(s, (v) => v.alive && v.asleep);
    return m ? { tile: true, x: m.x, y: m.y } : null;
  }

  // The unit matching `pred` the party can walk to soonest.
  function nearest(s, pred) {
    const party = s.units.filter((u) => u.alive && u.team === 'P' && !u.nonCombat);
    if (!party.length) return null;
    const dist = new Int32Array(s.w * s.h).fill(-1);
    const q = [];
    for (const u of party) {
      dist[u.y * s.w + u.x] = 0;
      q.push([u.x, u.y]);
    }
    let best = null;
    for (let head = 0; head < q.length; head++) {
      const [x, y] = q[head];
      const d = dist[y * s.w + x];
      const m = s.units.find((v) => v.alive && v.team === 'E' && v.x === x && v.y === y && pred(v));
      if (m) {
        best = m;
        break;
      }
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= s.w || ny >= s.h) continue;
        const i = ny * s.w + nx;
        if (dist[i] >= 0 || s.terrain[i] === T_WALL) continue;
        dist[i] = d + 1;
        q.push([nx, ny]);
      }
    }
    return best;
  }

  // Fog of war: what the party can see from where it stands, added to what it has seen.
  // Returns true when something new came into view.
  const SIGHT = 6;
  function reveal(s, fl, seen) {
    let changed = false;
    const mark = (x, y) => {
      const i = y * s.w + x;
      if (!seen[i]) {
        seen[i] = 1;
        changed = true;
      }
    };
    for (const u of s.units) {
      if (!u.alive || u.team !== 'P' || u.nonCombat) continue;
      for (let dy = -SIGHT; dy <= SIGHT; dy++)
        for (let dx = -SIGHT; dx <= SIGHT; dx++) {
          const x = u.x + dx;
          const y = u.y + dy;
          if (x < 0 || y < 0 || x >= s.w || y >= s.h || Math.abs(dx) + Math.abs(dy) > SIGHT + 2) continue;
          if (s.terrain[y * s.w + x] === T_WALL || E.sightLine(s, u.x, u.y, x, y)) mark(x, y);
        }
      // Step into a room and you see all of it.
      for (const r of fl.rooms) if (u.x >= r.x && u.x < r.x + r.w && u.y >= r.y && u.y < r.y + r.h) for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) mark(x, y);
    }
    return changed;
  }

  // ------------------------------------------------------------ loot

  // Slay a whole pack and it may drop something for the stash: a skill or a piece of gear,
  // better the deeper you go. The Countess always drops two, one of them legendary.
  function rollLoot(p, rng, floor, boss) {
    const out = [];
    const pool = (legend) => {
      const all = [];
      for (const [kind, table] of [['skill', SKILLS], ['gear', GEAR]])
        for (const [id, d] of Object.entries(table)) if (!d.side && (legend ? d.rarity === 'legendary' : d.rarity !== 'legendary')) all.push([kind, id]);
      return all;
    };
    const n = boss ? 2 : rng.chance(0.35 + 0.08 * floor) ? 1 : 0;
    for (let i = 0; i < n; i++) {
      const legend = boss ? i === 0 : floor >= 4 && rng.chance(0.08);
      const list = pool(legend);
      if (!list.length) continue;
      const [kind, id] = rng.pick(list);
      out.push(addItem(p, kind, id));
    }
    if (out.length && p.run) p.run.loot.push(...out.map((it) => it.uid));
    save(p);
    return out;
  }

  // Packs wiped out since `known` (a Set of pack ids already counted); adds them to it.
  function packsDown(s, known) {
    const packs = new Map();
    for (const u of s.units) if (u.team === 'E' && u.pack) packs.set(u.pack, (packs.get(u.pack) || false) || u.alive);
    const fresh = [];
    for (const [pack, alive] of packs) if (!alive && !known.has(pack)) {
      known.add(pack);
      fresh.push({ pack, boss: s.units.some((u) => u.pack === pack && u.boss) });
    }
    return fresh;
  }

  AG.Delve = {
    SAVE_KEY, FLOORS, FLOOR_DEFS, CLASSES, SLOTS, HERO_SLOTS, LEVEL, SHRINE_HP, W, H,
    newProfile, newHero, heroes, addItem, itemDef, itemByUid, holderOf, picks, classTalents, normalize, autoKit, specOf, setClass, save, load,
    genFloor, flood, startRun, floorBattle, finishFloor, endRun, exploreTarget, reveal, rollLoot, packsDown,
  };
})(typeof window !== 'undefined' ? window : globalThis);
