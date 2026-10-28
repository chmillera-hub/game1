// Hero Delve: the dungeon layer. Your party (four heroes and the Cleric) goes down the
// Forgotten Tower a floor at a time, levelling up as it goes. Each floor is one big battle for the engine:
// the monster packs sleep in their rooms until the party comes near (see wakeCheck), and
// between fights the party's AI walks on toward the next pack it has not met.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const D = AG.Data;
  const E = AG.Engine;
  const { UNITS, TALENTS, SKILLS, GEAR, NAMES } = D;

  const SAVE_KEY = 'hero-delve-v1';
  const VERSION = 3;
  const FLOORS = 5;
  const W = 24;
  const H = 24;
  const HERO_SLOTS = 4;

  // Hero classes you can bring: every recruitable unit that walks (no wards), the Cleric aside.
  const CLASSES = D.RECRUITABLE.filter((t) => t !== 'cleric' && UNITS[t].role !== 'ward' && !UNITS[t].traits.includes('immobile'));

  // ------------------------------------------------------------ levels
  //
  // Heroes and monsters share one level scale. Each level makes a unit a little tougher
  // and stronger; heroes also get a skill point a level, and unlock their class's second
  // pick (Level 4), its mastery (Level 8) and more skill and gear slots as they grow.
  // The top level, reached about as the party starts down to the last floor. XP past it
  // earns prestige points instead, for the Prestige Trainer in town.
  const MAX_LV = 10;
  const hpMul = (lv) => 1 + 0.08 * (lv - 1);
  const powMul = (lv) => 1 + 0.05 * (lv - 1);
  // Monsters grow a little faster: heroes make up the rest with skill points and gear.
  const foeHpMul = (lv) => 1 + 0.11 * (lv - 1);
  const foePowMul = (lv) => 1 + 0.065 * (lv - 1);
  // The Arena tier a level stands for: its second pick at 2, its mastery at 3.
  const tierOf = (lv) => (lv >= 7 ? 3 : lv >= 4 ? 2 : 1);
  // XP from each level to the next: about two levels a floor, the top one reached as the
  // party clears Level 4.
  const XP_TABLE = [0, 150, 250, 500, 600, 800, 900, 1000, 1300, 1600];
  const xpToNext = (lv) => XP_TABLE[Math.min(lv, XP_TABLE.length - 1)] || XP_TABLE[XP_TABLE.length - 1];
  // Slots by hero level.
  const skillSlots = (lv) => (lv >= 9 ? 3 : lv >= 5 ? 2 : 1);
  const gearSlots = (lv) => (lv >= 8 ? 3 : lv >= 3 ? 2 : 1);
  // Talents unlock with level: the first tier at Level 2, the stronger tier at Level 5.
  const talentLevel = (id) => (TALENTS[id].tier >= 2 ? 5 : 2);
  // Training, for skill points past the talents: each point adds this much.
  const TRAIN = { vit: { name: 'Vitality', hp: 0.08, desc: '+8% HP' }, str: { name: 'Might', pow: 0.05, desc: '+5% power' } };

  // The tower, floor by floor: who sleeps in its rooms, how many to a pack, how strong; and
  // the floor's Champion, a named monster far tougher than the rest, with a pack of its own.
  const FLOOR_DEFS = [
    null,
    { name: 'Level 1', pool: ['skeleton', 'skeleton', 'spider', 'skelarcher'], pack: [2, 3], lv: [1, 2], empty: 0.2, champ: { type: 'troll', name: 'Gravelmaw' } },
    { name: 'Level 2', pool: ['skeleton', 'skelarcher', 'specter', 'spider'], pack: [2, 4], lv: [3, 4], empty: 0.15, champ: { type: 'necromancer', name: 'Old Rattlebones' } },
    { name: 'Level 3', pool: ['skelarcher', 'specter', 'cutthroat', 'spider', 'skeleton'], pack: [3, 4], lv: [5, 6], empty: 0.15, champ: { type: 'spider', name: 'Mother Venom' } },
    { name: 'Level 4', pool: ['specter', 'cutthroat', 'crossbow', 'necromancer', 'skeleton'], pack: [3, 4], lv: [7, 8], empty: 0.1, shackler: 1, champ: { type: 'colossus', name: 'The Bonepile' } },
    { name: 'Level 5', pool: ['cutthroat', 'specter', 'skelarcher', 'skeleton'], pack: [3, 4], lv: [9, 10], empty: 0.1, champ: { type: 'shackler', name: 'Chainwarden Vosk' }, boss: 'countess', bossLv: 11, bossPack: ['cutthroat', 'specter', 'skeleton'] },
  ];
  const CHAMP_LV = 3;

  // What the stash starts with: a few skills and pieces of gear to share out.
  const STARTER = [
    ['skill', 'vampiric'], ['skill', 'last_stand'], ['skill', 'executioner'], ['skill', 'guardian'], ['skill', 'undying_rage'], ['skill', 'flanker'],
    ['gear', 'healing_charm'], ['gear', 'reactive_plate'], ['gear', 'porcupine_ring'], ['gear', 'hex_charm'], ['gear', 'fire_flask'], ['gear', 'healing_draught'],
  ];
  const STARTER_PARTY = ['knight', 'archer', 'pyromancer', 'berserker'];

  // ------------------------------------------------------------ profile

  function newProfile() {
    const p = { v: VERSION, nextId: 1, party: [], cleric: null, stash: [], stats: { runs: 0, clears: 0, best: 0 }, run: null, prestige: 0, trainer: null };
    for (const t of STARTER_PARTY) p.party.push(newHero(p, t));
    p.cleric = newHero(p, 'cleric');
    for (const [kind, id] of STARTER) addItem(p, kind, id);
    autoKit(p);
    return p;
  }

  function newHero(p, type, from) {
    const T = UNITS[type];
    const used = new Set(heroes(p).map((h) => h.name));
    const free = NAMES.filter((n) => !used.has(n));
    const name = free[(p.nextId * 7) % free.length] || 'Hero ' + p.nextId;
    return { id: 'h' + p.nextId++, type, name, lv: from ? from.lv : 1, xp: from ? from.xp : 0, auto: false, a1: firstPick(T, 1), a2: firstPick(T, 2), talents: [], train: { vit: 0, str: 0 }, skills: [], gear: [] };
  }

  // The first level pick that is not a talent (talents are bought with skill points).
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

  // Level picks for this class at this tier (talents excluded: those cost skill points).
  function picks(type, tier) {
    const T = UNITS[type];
    return ((T.abilities && T.abilities[tier]) || []).filter((id) => !TALENTS[id]);
  }

  function classTalents(type) {
    return Object.keys(TALENTS).filter((id) => TALENTS[id].cls === type);
  }

  function slotsOf(h) {
    return { skills: skillSlots(h.lv), gear: gearSlots(h.lv) };
  }

  // Skill points: one a level past the first, spent on talents and training.
  function pointsSpent(h) {
    return h.talents.reduce((t, id) => t + (TALENTS[id] ? TALENTS[id].cost : 0), 0) + h.train.vit + h.train.str;
  }
  function pointsLeft(h) {
    return h.lv - 1 - pointsSpent(h);
  }
  function canLearn(h, id) {
    const t = TALENTS[id];
    return !!(t && t.cls === h.type && !h.talents.includes(id) && h.lv >= talentLevel(id) && pointsLeft(h) >= t.cost);
  }
  function learn(p, h, id) {
    if (!canLearn(h, id)) return false;
    h.talents.push(id);
    save(p);
    return true;
  }
  function train(p, h, k) {
    if (!TRAIN[k] || pointsLeft(h) < 1) return false;
    h.train[k]++;
    save(p);
    return true;
  }
  // Every point back, to spend again (free in town).
  function respec(p, h) {
    h.talents = [];
    h.train = { vit: 0, str: 0 };
    save(p);
  }
  // Spend whatever is left the way the hero's class would: talents first (cheapest, then
  // the first listed), then training, toughness for those who stand in front.
  function autoSpend(h) {
    for (let guard = 0; guard < 40 && pointsLeft(h) > 0; guard++) {
      const t = classTalents(h.type).filter((id) => canLearn(h, id)).sort((a, b) => TALENTS[a].cost - TALENTS[b].cost)[0];
      if (t) {
        h.talents.push(t);
        continue;
      }
      // Wait for a talent the next level opens, rather than spend the point now.
      if (classTalents(h.type).some((id) => !h.talents.includes(id) && h.lv < talentLevel(id))) break;
      if (classTalents(h.type).some((id) => !h.talents.includes(id) && pointsLeft(h) < TALENTS[id].cost)) break;
      const front = (UNITS[h.type].act.range || [1, 1])[1] <= 1;
      const k = front ? (h.train.vit <= h.train.str ? 'vit' : 'str') : h.train.str <= h.train.vit * 2 ? 'str' : 'vit';
      h.train[k]++;
    }
  }

  // XP: a hero levels up when it has enough; returns the levels gained. At the top level
  // its XP goes toward prestige instead: a point for the party (`p`) every PRESTIGE_XP.
  const PRESTIGE_XP = 2000;
  function gainXp(h, n, p) {
    let ups = 0;
    h.xp += n;
    while (h.lv < MAX_LV && h.xp >= xpToNext(h.lv)) {
      h.xp -= xpToNext(h.lv);
      h.lv++;
      ups++;
    }
    if (h.lv >= MAX_LV) {
      if (ups) h.xp = 0;
      while (h.xp >= PRESTIGE_XP) {
        h.xp -= PRESTIGE_XP;
        if (p) p.prestige = (p.prestige || 0) + 1;
      }
    }
    if (ups && h.auto) autoSpend(h);
    return ups;
  }

  // ------------------------------------------------------------ the Prestige Trainer
  //
  // In town, prestige points buy skills and gear from the trainer's stock: a new stock after
  // every floor cleared, or for a point. Prices go by how good a piece is.
  const STOCK = 8;
  function priceOf(d) {
    if (d.rarity === 'legendary') return 8;
    return Math.min(5, 1 + (d.cost || 0));
  }

  function stock(p) {
    if (!p.trainer || !p.trainer.items) restock(p);
    return p.trainer.items;
  }

  function restock(p) {
    p.trainer = p.trainer || { n: 0 };
    p.trainer.n = (p.trainer.n || 0) + 1;
    const rng = AG.derive(p.trainer.n * 7919 + (p.stats.runs || 0), 'trainer');
    const all = [];
    for (const [kind, table] of [['skill', SKILLS], ['gear', GEAR]]) for (const [id, d] of Object.entries(table)) if (!d.side && !goldOnly(d)) all.push({ kind, id });
    const items = [];
    const legend = all.filter((x) => itemDef(x).rarity === 'legendary');
    if (legend.length) items.push(rng.pick(legend));
    for (const x of rng.shuffle(all.filter((x) => itemDef(x).rarity !== 'legendary'))) if (items.length < STOCK) items.push(x);
    p.trainer.items = items;
    save(p);
    return items;
  }

  function buy(p, i) {
    const items = stock(p);
    const x = items[i];
    if (!x) return null;
    const price = priceOf(itemDef(x));
    if ((p.prestige || 0) < price) return null;
    p.prestige -= price;
    items.splice(i, 1);
    const it = addItem(p, x.kind, x.id);
    save(p);
    return it;
  }

  function buyRestock(p) {
    if ((p.prestige || 0) < 1) return false;
    p.prestige--;
    restock(p);
    return true;
  }

  // What a monster is worth: more for bigger monsters and higher levels, much more for a
  // Champion or the Countess; less to a hero far above it, more to one below.
  function killXp(u, heroLv) {
    const T = UNITS[u.type];
    const size = Math.min(2, Math.max(0.6, T.hp / 32));
    let xp = 15 * u.dlv * size;
    if (u.champ) xp *= 4;
    if (u.boss) xp *= 8;
    if (u.summoner) xp *= 0.25;
    const gap = u.dlv - heroLv;
    xp *= gap >= 0 ? 1 + 0.1 * Math.min(5, gap) : Math.max(0.1, 1 + 0.2 * gap);
    return Math.max(1, Math.round(xp));
  }

  // Keep a hero's kit legal: real picks, its own class talents, eligible items it holds alone.
  function normalize(p, h) {
    const T = UNITS[h.type];
    if (h.lv == null) h.lv = 1;
    if (h.xp == null) h.xp = 0;
    if (!h.train) h.train = { vit: 0, str: 0 };
    if (h.auto == null) h.auto = true;
    if (!picks(h.type, 1).includes(h.a1)) h.a1 = firstPick(T, 1);
    if (!picks(h.type, 2).includes(h.a2)) h.a2 = firstPick(T, 2);
    h.talents = [...new Set(h.talents)].filter((id) => TALENTS[id] && TALENTS[id].cls === h.type && h.lv >= talentLevel(id));
    while (pointsLeft(h) < 0) {
      if (h.train.vit + h.train.str > 0) h.train[h.train.vit >= h.train.str ? 'vit' : 'str']--;
      else h.talents.pop();
    }
    const taken = new Set(heroes(p).filter((o) => o !== h).flatMap((o) => o.skills.concat(o.gear)));
    const ok = (uid, kind) => {
      const it = itemByUid(p, uid);
      return it && it.kind === kind && !taken.has(uid) && D.eligible(h.type, itemDef(it));
    };
    const sl = slotsOf(h);
    h.skills = [...new Set(h.skills)].filter((uid) => ok(uid, 'skill')).slice(0, sl.skills);
    h.gear = [...new Set(h.gear)].filter((uid) => ok(uid, 'gear')).slice(0, sl.gear);
    return h;
  }

  // Fill every empty slot with the best free fit, and spend skill points if the hero spends
  // its own.
  function autoKit(p, only) {
    for (const h of only ? [only] : heroes(p)) {
      normalize(p, h);
      if (h.auto) autoSpend(h);
      fillSlots(p, h);
    }
  }

  function fillSlots(p, h) {
    const sl = slotsOf(h);
    for (const [kind, key] of [['skill', 'skills'], ['gear', 'gear']]) {
      const free = p.stash
        .filter((it) => it.kind === kind && !holderOf(p, it.uid) && D.eligible(h.type, itemDef(it)) && !itemDef(it).side)
        .sort((a, b) => (itemDef(b).cost || 0) - (itemDef(a).cost || 0));
      for (const it of free) if (h[key].length < sl[key]) h[key].push(it.uid);
    }
  }

  // The engine spec for a hero.
  function specOf(p, h) {
    normalize(p, h);
    return {
      type: h.type,
      level: tierOf(h.lv),
      dlv: h.lv,
      hpMul: hpMul(h.lv) + TRAIN.vit.hp * h.train.vit,
      powMul: powMul(h.lv) + TRAIN.str.pow * h.train.str,
      a1: h.a1,
      a2: h.a2,
      talents: h.talents.slice(),
      skills: h.skills.map((uid) => itemByUid(p, uid).id),
      gear: h.gear.map((uid) => itemByUid(p, uid).id),
      rid: h.id,
      name: h.name,
    };
  }

  // Swap a party slot to a new class: a fresh hero of the same level, kitted from what is free.
  function setClass(p, slot, type) {
    if (!CLASSES.includes(type)) return null;
    const h = newHero(p, type, p.party[slot]);
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
      if (!p || !p.party || !p.cleric) return null;
      // The first version had every hero at Level 3: they start over at Level 1, with their
      // items kept. The second went to Level 15: top levels come down to the new top, with
      // their points back to spend. Either way a delve under way is called off.
      if (p.v !== VERSION) {
        for (const h of heroes(p)) {
          if (p.v === 2) h.lv = Math.min(MAX_LV, h.lv || 1);
          else h.lv = 1;
          h.xp = 0;
          h.talents = [];
          h.train = { vit: 0, str: 0 };
          h.auto = false;
        }
        p.prestige = p.prestige || 0;
        p.run = null;
        p.v = VERSION;
      }
      for (const h of heroes(p)) normalize(p, h);
      return p;
    } catch (e) {
      /* fall through to a new profile */
    }
    return null;
  }

  function partyLevel(p) {
    const hs = heroes(p);
    return hs.length ? hs.reduce((t, h) => t + h.lv, 0) / hs.length : 1;
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
    const place = (r, types, lv, lead) => {
      pack++;
      const spots = spotsIn(r);
      types.forEach((type, i) => {
        const s = spots[i];
        if (!s) return;
        taken.add(idx(s[0], s[1]));
        const m = monsterSpec(type, i === 0 && lead ? lead.lv : lv);
        if (i === 0 && lead && lead.champ) Object.assign(m, { champ: true, name: lead.name });
        monsters.push(Object.assign(m, { x: s[0], y: s[1], facing: rng.int(4), asleep: true, pack }));
      });
    };
    let shacklers = def.shackler || 0;
    // The Champion keeps a room of its own off the way through, well away from the way in: a
    // dead end if there is one (a room only one corridor leads to), the further the better.
    const degree = new Map();
    for (const [a, b] of links) {
      degree.set(a, (degree.get(a) || 0) + 1);
      degree.set(b, (degree.get(b) || 0) + 1);
    }
    const far = (r) => Math.abs(r.cx - start.cx) + Math.abs(r.cy - start.cy);
    const middle = rooms.filter((r) => r !== start && r !== end && far(r) > 10).sort((a, b) => (degree.get(a) === 1 ? 0 : 1) - (degree.get(b) === 1 ? 0 : 1) || far(b) - far(a));
    // And never in the way: every other room must be reachable from the way in without
    // coming in sight of it, so a party too weak for it can always leave it for later.
    const clear = (r) => {
      const m = E.AGGRO + 1;
      const near = (x, y) => Math.max(0, r.x - x, x - (r.x + r.w - 1)) + Math.max(0, r.y - y, y - (r.y + r.h - 1)) <= m;
      const seen = new Uint8Array(W * H);
      const q = [idx(start.cx, start.cy)];
      seen[q[0]] = 1;
      for (let head = 0; head < q.length; head++) {
        const i = q[head];
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const x = (i % W) + dx;
          const y = Math.floor(i / W) + dy;
          if (x < 0 || y < 0 || x >= W || y >= H) continue;
          const j = idx(x, y);
          if (seen[j] || terrain[j] !== T_FLOOR || near(x, y)) continue;
          seen[j] = 1;
          q.push(j);
        }
      }
      return rooms.every((o) => o === r || o === start || spotsOf(o).some(([x, y]) => seen[idx(x, y)]));
    };
    const spotsOf = (r) => {
      const out = [];
      for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) if (terrain[idx(x, y)] === T_FLOOR) out.push([x, y]);
      return out;
    };
    const fine = middle.filter(clear);
    const pool = fine.length ? fine : middle;
    const champRoom = def.champ && pool.length ? pool[rng.int(Math.min(2, pool.length))] : null;
    for (const r of rooms) {
      if (r === start) continue;
      if (r === end && def.boss) {
        place(r, [def.boss].concat(def.bossPack), def.lv[1], { lv: def.bossLv });
        continue;
      }
      if (r === champRoom) {
        const lead = def.champ;
        place(r, [lead.type, rng.pick(def.pool), rng.pick(def.pool)], def.lv[1], { lv: def.lv[1] + CHAMP_LV, champ: true, name: lead.name });
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

  // A monster of this delve level: tougher and stronger with each level, like the heroes.
  function monsterSpec(type, lv) {
    return { type, level: tierOf(lv), dlv: lv, hpMul: foeHpMul(lv), powMul: foePowMul(lv) };
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
    p.run = { seed: seed || ((Date.now() % 1e9) + 1), floor: 1, loot: [], kills: 0 };
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
    // Every floor starts rested: everyone up, at full health.
    heroes(p).forEach((h, i) => units.push(Object.assign(specOf(p, h), { team: 'P', x: spots[i][0], y: spots[i][1], facing: 1 })));
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
      rounds: true,
      delve: { respawn: spots },
    });
    for (const u of s.units) if (u.team === 'P') u.specKey = JSON.stringify(specOf(p, heroes(p).find((h) => h.id === u.rid)));
    return { s, fl };
  }

  // After a floor: who is left and how hurt, onward (or the tower is beaten).
  function finishFloor(p, s) {
    const run = p.run;
    // The trainer has something new in.
    if (p.trainer) p.trainer.items = null;
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

  // The party's orders when you have set none.
  // - Fighting: its own judgement, unless the fight has stalled (`idle` plies without a blow,
  //   both sides waiting for the other); then the nearest awake monster, all out.
  // - A hero far from the rest (just back from the way in): the others wait while it
  //   catches up.
  // - Walking: the nearest sleeping pack it can take on. Packs two or more levels above the
  //   party are left for later, while there is anything else to fight; then the least
  //   strong of them. A priority you set overrides all this.
  const STALL = 12;
  const DANGER = 2;
  const STRAY = 6;
  const GATHERED = 4;
  const GATHER_ROUNDS = 6;
  const FLEES = 2;
  function exploreTarget(s, idle) {
    const awake = s.units.filter((u) => u.alive && u.team === 'E' && !u.asleep && !u.nonCombat);
    if (awake.length) {
      // Woke something far too strong by accident: fall back to the way in (the pack gives
      // up the chase once the party is well away from its lair), while there is anything
      // easier left on the floor. A priority you set on it means fight.
      const lvNow = partyLevelIn(s);
      const packLvNow = packLevels(s);
      const strong = (u) => (packLvNow.get(u.pack) || u.dlv) >= lvNow + DANGER;
      // Twice is enough: a pack the party has already run from twice, it fights.
      const tooStrong = awake.some((u) => strong(u) && (u.fled || 0) < FLEES);
      // Only if the party could get round it to something easier: a fight in the way of
      // everything else is a fight to have now.
      const lairs = s.units.filter((u) => u.alive && u.team === 'E' && strong(u)).map((u) => ({ x: u.home.x, y: u.home.y }));
      const zone = dangerZone(s, lairs, 2);
      const fightZone = dangerZone(s, lairs, 4);
      const easier = (v) => v.alive && v.asleep && !strong(v) && !fightZone[v.y * s.w + v.x];
      const way = s.delve && s.delve.respawn.length ? { x: s.delve.respawn[0][0], y: s.delve.respawn[0][1] } : null;
      if (tooStrong && way && nearestPath(s, easier, zone, [way])) {
        const { x, y } = way;
        return { tile: true, x, y, press: true, retreat: true };
      }
      if ((idle || 0) < STALL) return null;
      const m = nearest(s, (v) => awake.includes(v));
      return m ? { uid: m.uid, press: true } : null;
    }
    const goal = walkTarget(s);
    // Strung out (a hero back from the way in, a fast one far ahead): the rest close up on
    // whoever is furthest on toward where the party is going.
    // Once it starts closing up it keeps the same hero to close up on, until all are close.
    const party = s.units.filter((u) => u.alive && u.team === 'P' && !u.nonCombat && !u.summoner);
    const apart = (lead, r) => party.some((u) => Math.abs(u.x - lead.x) + Math.abs(u.y - lead.y) > r);
    // (A few rounds at most: crowded in a corridor, close enough is close enough.)
    const held = s.byId[s.regroup];
    if (held && held.alive && held.team === 'P' && s.turn - s.regroupFrom <= GATHER_ROUNDS) {
      if (apart(held, GATHERED)) return { ally: held.uid };
    }
    s.regroup = 0;
    if (party.length > 1 && goal && s.turn - (s.regroupFrom || -99) > GATHER_ROUNDS) {
      const d = (u) => Math.abs(u.x - goal.x) + Math.abs(u.y - goal.y);
      const lead = party.slice().sort((a, b) => d(a) - d(b) || a.uid - b.uid)[0];
      if (apart(lead, STRAY)) {
        s.regroup = lead.uid;
        s.regroupFrom = s.turn;
        return { ally: lead.uid };
      }
    }
    return goal;
  }

  // Where the party walks between fights (see exploreTarget).
  function walkTarget(s) {
    const lv = partyLevelIn(s);
    const packLv = packLevels(s);
    const deadly = (v) => v.alive && v.asleep && (packLv.get(v.pack) || v.dlv) >= lv + DANGER;
    const lairs = s.units.filter(deadly).map((u) => ({ x: u.home.x, y: u.home.y }));
    // A pack fought within sight of a deadly lair would wake it too: that one waits as well.
    const fightZone = dangerZone(s, lairs, 4);
    const safe = (v) => v.alive && v.asleep && !deadly(v) && !(fightZone && fightZone[v.y * s.w + v.x]);
    // Keep out of sight of the packs too strong for now: walk round them if there is a way.
    const avoid = dangerZone(s, lairs, 2);
    if (avoid) {
      const path = nearestPath(s, safe, avoid);
      if (path) {
        const step = path[Math.min(path.length - 1, 8)];
        return { tile: true, x: step[0], y: step[1] };
      }
    }
    let m = nearest(s, safe) || nearest(s, (v) => v.alive && v.asleep && !deadly(v));
    if (!m) {
      const sleeping = s.units.filter((v) => v.alive && v.asleep);
      if (!sleeping.length) return null;
      const least = Math.min(...sleeping.map((v) => packLv.get(v.pack) || v.dlv));
      m = nearest(s, (v) => v.alive && v.asleep && (packLv.get(v.pack) || v.dlv) === least);
    }
    return m ? { tile: true, x: m.x, y: m.y } : null;
  }

  // Tiles a sleeping pack would see the party on (`margin` tiles to spare), or null for none.
  function dangerZone(s, list, margin) {
    if (!list.length) return null;
    const z = new Uint8Array(s.w * s.h);
    const r = E.AGGRO + (margin || 1);
    for (const v of list)
      for (let dy = -r; dy <= r; dy++)
        for (let dx = -r; dx <= r; dx++) {
          const x = v.x + dx;
          const y = v.y + dy;
          if (x < 0 || y < 0 || x >= s.w || y >= s.h || Math.abs(dx) + Math.abs(dy) > r) continue;
          if (E.sightLine(s, v.x, v.y, x, y)) z[y * s.w + x] = 1;
        }
    return z;
  }

  // The walk to the nearest unit matching `pred` that keeps off `avoid`, from the party (or
  // from `starts`): its tiles from the first step on, or null when there is none.
  function nearestPath(s, pred, avoid, starts) {
    const party = starts || s.units.filter((u) => u.alive && u.team === 'P' && !u.nonCombat);
    if (!party.length) return null;
    const from = new Int32Array(s.w * s.h).fill(-2);
    const q = [];
    for (const u of party) {
      const i = u.y * s.w + u.x;
      from[i] = -1;
      q.push(i);
    }
    const targets = new Set(s.units.filter((v) => v.alive && v.team === 'E' && pred(v)).map((v) => v.y * s.w + v.x));
    for (let head = 0; head < q.length; head++) {
      const i = q[head];
      // A target in sight of nobody dangerous: reach a tile next to it.
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const x = (i % s.w) + dx;
        const y = Math.floor(i / s.w) + dy;
        if (x < 0 || y < 0 || x >= s.w || y >= s.h) continue;
        const j = y * s.w + x;
        if (targets.has(j)) {
          const path = [];
          for (let k = i; k >= 0 && from[k] !== -1; k = from[k]) path.push([k % s.w, Math.floor(k / s.w)]);
          path.reverse();
          return path.length ? path : [[x, y]];
        }
        if (from[j] !== -2 || s.terrain[j] === T_WALL || avoid[j]) continue;
        from[j] = i;
        q.push(j);
      }
    }
    return null;
  }

  // The party's level on the floor: its heroes' average.
  function partyLevelIn(s) {
    const hs = s.units.filter((u) => u.team === 'P' && u.rid);
    return hs.length ? hs.reduce((t, u) => t + (u.dlv || 1), 0) / hs.length : 1;
  }

  // Each pack's strength: the level of its strongest monster still standing.
  function packLevels(s) {
    const m = new Map();
    for (const u of s.units) if (u.alive && u.team === 'E' && u.pack) m.set(u.pack, Math.max(m.get(u.pack) || 0, u.dlv || 1));
    return m;
  }

  // How a monster's level looks next to the party's: 'low', 'even', 'high' (one above) or
  // 'deadly' (two or more above), as its health bar shows it.
  function danger(dlv, partyLv) {
    const gap = dlv - partyLv;
    return gap >= DANGER ? 'deadly' : gap >= 1 ? 'high' : gap <= -3 ? 'low' : 'even';
  }

  // Plies since the party last hurt a monster: what `exploreTarget` calls a stalled fight.
  function idleAfter(s, events, idle) {
    return events.some((e) => e.t === 'dmg' && s.byId[e.uid] && s.byId[e.uid].team === 'E') ? 0 : (idle || 0) + 1;
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

  // ------------------------------------------------------------ loot and XP

  // Items that only earn gold, which a delve has no use for.
  const goldOnly = (d) => !!(d.mod && d.mod.traits && d.mod.traits.includes('midas'));

  // Slay a whole pack and it may drop something for the stash: a skill or a piece of gear,
  // better the deeper you go. A Champion always drops one, of the better kind; the Countess
  // two, one of them legendary.
  function rollLoot(p, rng, floor, kind) {
    const out = [];
    const pool = (legend, minCost) => {
      const all = [];
      for (const [k, table] of [['skill', SKILLS], ['gear', GEAR]])
        for (const [id, d] of Object.entries(table)) if (!d.side && !goldOnly(d) && (legend ? d.rarity === 'legendary' : d.rarity !== 'legendary' && (d.cost || 0) >= minCost)) all.push([k, id]);
      return all;
    };
    const boss = kind === 'boss' || kind === true;
    const champ = kind === 'champ';
    const n = boss ? 2 : champ ? 1 : rng.chance(0.3 + 0.06 * floor) ? 1 : 0;
    for (let i = 0; i < n; i++) {
      const legend = boss ? i === 0 : (champ ? rng.chance(0.12 + 0.04 * floor) : floor >= 4 && rng.chance(0.06));
      const minCost = champ || boss ? 2 : rng.chance(0.12 * floor) ? 2 : 0;
      const list = pool(legend, minCost);
      if (!list.length) continue;
      const [k, id] = rng.pick(list);
      out.push(addItem(p, k, id));
    }
    if (out.length && p.run) p.run.loot.push(...out.map((it) => it.uid));
    // Heroes left on Auto put new finds in their empty slots (never swapping what they hold).
    if (out.length) for (const h of heroes(p)) if (h.auto) fillSlots(p, h);
    save(p);
    return out;
  }

  // Packs wiped out since `known` (a Set of pack ids already counted); adds them to it.
  function packsDown(s, known) {
    const packs = new Map();
    for (const u of s.units) if (u.team === 'E' && u.pack && !u.summoner) packs.set(u.pack, (packs.get(u.pack) || false) || u.alive);
    const fresh = [];
    for (const [pack, alive] of packs) if (!alive && !known.has(pack)) {
      known.add(pack);
      const members = s.units.filter((u) => u.pack === pack);
      fresh.push({ pack, boss: members.some((u) => u.boss), champ: members.some((u) => u.champ), kind: members.some((u) => u.boss) ? 'boss' : members.some((u) => u.champ) ? 'champ' : 'pack' });
    }
    return fresh;
  }

  // XP for monsters slain since the last call (`credited`: a Set of uids already paid for).
  // Every hero in the party gets it, standing or fallen. Returns [{ uid, xp, ups: [heroId] }].
  function creditKills(p, s, credited) {
    const out = [];
    for (const u of s.units) {
      if (u.alive || u.team !== 'E' || u.nonCombat || credited.has(u.uid) || !u.dlv) continue;
      credited.add(u.uid);
      const ups = [];
      let shown = 0;
      for (const h of heroes(p)) {
        const xp = killXp(u, h.lv);
        shown = Math.max(shown, xp);
        if (gainXp(h, xp, p)) {
          ups.push(h.id);
          if (h.auto) fillSlots(p, h);
        }
      }
      if (p.run) p.run.kills++;
      out.push({ uid: u.uid, x: u.x, y: u.y, xp: shown, ups });
    }
    if (out.length) save(p);
    return out;
  }

  // Bring the heroes on the floor up to date with their records (new levels, points spent,
  // items swapped), out of a fight only. Returns the uids rebuilt.
  function refreshParty(p, s) {
    if (s.inCombat) return [];
    const out = [];
    for (const u of s.units) {
      if (u.team !== 'P' || !u.rid) continue;
      const h = heroes(p).find((x) => x.id === u.rid);
      if (!h) continue;
      const spec = specOf(p, h);
      const key = JSON.stringify(spec);
      if (key === u.specKey) continue;
      const lvUp = h.lv > (u.dlv || 1);
      u.specKey = key;
      E.rebuildUnit(s, u, spec, lvUp);
      out.push(u.uid);
    }
    return out;
  }

  AG.Delve = {
    SAVE_KEY, FLOORS, FLOOR_DEFS, CLASSES, HERO_SLOTS, W, H, MAX_LV, TRAIN, DANGER,
    hpMul, powMul, foeHpMul, foePowMul, tierOf, xpToNext, skillSlots, gearSlots, talentLevel, slotsOf, pointsLeft, pointsSpent, canLearn, learn, train, respec, autoSpend, gainXp, killXp, partyLevel,
    PRESTIGE_XP, priceOf, stock, restock, buy, buyRestock,
    newProfile, newHero, heroes, addItem, itemDef, itemByUid, holderOf, picks, classTalents, normalize, autoKit, fillSlots, specOf, setClass, save, load, monsterSpec,
    genFloor, flood, startRun, floorBattle, finishFloor, endRun, exploreTarget, idleAfter, partyLevelIn, packLevels, danger, reveal, rollLoot, packsDown, creditKills, refreshParty,
  };
})(typeof window !== 'undefined' ? window : globalThis);
