// Campaign layer: the branching map, enemy armies, economy, rewards, shops, events and saving.
// The run object is plain JSON so it can be saved between sessions.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const D = AG.Data;
  const { UNITS, RECRUITABLE, TALENTS, RELICS, WARBANDS, DIFFICULTIES, ENCOUNTERS, NAMES, talentEligible, MAX_TALENTS } = D;
  const E = AG.Engine;

  const SAVE_KEY = 'arena-gauntlet-run-v1';
  const META_KEY = 'arena-gauntlet-meta-v1';
  const ROWS = 7; // regular rows per act; the boss sits on row ROWS
  const COLS = 5;
  const BOARD = 9;
  const MAX_ROSTER = 10;
  const MAX_BANNERS = 3;
  const RANK_COST = [0, 0, 1.2, 2.6];
  const PROMOTE_PRICE = [0, 0, 40, 80];
  const RECRUIT_PRICE = { common: 45, uncommon: 65, rare: 90, legendary: 150 };
  const RELIC_PRICE = { common: 85, uncommon: 115, rare: 150, boss: 200, event: 120 };
  const TALENT_PRICE = 50;
  const EFFICIENCY_GOLD = 4;

  const hasRelic = (run, id) => run.relics.includes(id);
  const unitById = (run, id) => run.roster.find((u) => u.id === id);
  const discount = (run, price) => Math.round(price * (hasRelic(run, 'guild_seal') ? 0.75 : 1));

  // ------------------------------------------------------------ roster

  function pickName(run) {
    const rng = AG.derive(run.seed, 'name:' + run.nextId);
    const free = NAMES.filter((n) => !run.usedNames.includes(n));
    const name = free.length ? rng.pick(free) : rng.pick(NAMES) + ' ' + run.nextId;
    run.usedNames.push(name);
    return name;
  }

  function addRecruit(run, type, rank, extra) {
    const u = { id: 'u' + run.nextId, type, rank: rank || 1, talents: [], wounded: false, name: '', kills: 0, battles: 0 };
    u.name = pickName(run);
    run.nextId++;
    if (extra) Object.assign(u, extra);
    run.roster.push(u);
    return u;
  }

  function canLearn(u, talent) {
    return u.talents.length < MAX_TALENTS && talentEligible(u.type, talent, u.talents);
  }

  function teach(run, rid, talent) {
    const u = unitById(run, rid);
    if (!u || !canLearn(u, talent)) return false;
    u.talents.push(talent);
    return true;
  }

  function promoteCost(run, u) {
    if (u.rank >= 3) return null;
    return discount(run, PROMOTE_PRICE[u.rank + 1]);
  }

  function promote(run, rid, free) {
    const u = unitById(run, rid);
    if (!u || u.rank >= 3) return false;
    if (!free) {
      const c = promoteCost(run, u);
      if (run.gold < c) return false;
      run.gold -= c;
    }
    u.rank++;
    return true;
  }

  function dismiss(run, rid) {
    if (run.roster.length <= 2) return false;
    const i = run.roster.findIndex((u) => u.id === rid);
    if (i < 0) return false;
    run.roster.splice(i, 1);
    run.gold += 15;
    return true;
  }

  // Battle-ready numbers for a roster unit (rank, talents and relics applied).
  function unitStats(spec, relics, team) {
    const s = { w: 1, h: 1, units: [], byId: {}, occ: [0], nextUid: 1, relics: { P: new Set(relics || []), E: new Set() } };
    return E.addUnit(s, { type: spec.type, rank: spec.rank || 1, talents: spec.talents || [], team: team || 'P', x: 0, y: 0, wounded: spec.wounded });
  }

  // ------------------------------------------------------------ new run

  function newRun(opts) {
    opts = opts || {};
    const seed = opts.seed >>> 0 || ((Math.random() * 2 ** 31) >>> 0) + 1;
    const wb = WARBANDS.find((w) => w.id === opts.warband) || WARBANDS[0];
    const diff = DIFFICULTIES.find((d) => d.id === opts.difficulty) || DIFFICULTIES[1];
    const run = {
      v: 1,
      seed,
      warband: wb.id,
      difficulty: diff.id,
      act: 1,
      gold: wb.gold,
      banners: MAX_BANNERS,
      maxBanners: MAX_BANNERS,
      cpBonus: 0,
      roster: [],
      relics: [wb.relic],
      nextId: 1,
      usedNames: [],
      map: null,
      pos: null,
      cur: null,
      visited: [],
      recentEnc: [],
      pending: null,
      over: false,
      won: false,
      stats: { battles: 0, elites: 0, bosses: 0, gold: 0, efficiency: 0, fallen: 0, kills: 0, losses: 0 },
    };
    for (const t of wb.units) addRecruit(run, t, 1);
    run.map = genMap(run, 1);
    return run;
  }

  // ------------------------------------------------------------ map

  function genMap(run, act) {
    const rng = AG.derive(run.seed, 'map:' + act);
    const nodes = new Map();
    const edges = new Set();
    const get = (r, c) => {
      const k = r + '-' + c;
      if (!nodes.has(k)) nodes.set(k, { id: k, row: r, col: c, kind: null, next: [], jx: +(rng.next() - 0.5).toFixed(3) });
      return nodes.get(k);
    };
    const crosses = (r, c, n) =>
      (n === c + 1 && edges.has(r + ':' + (c + 1) + '>' + c)) || (n === c - 1 && edges.has(r + ':' + (c - 1) + '>' + c));
    const starts = rng.shuffle([0, 1, 2, 3, 4]).slice(0, 3);
    const walks = [...starts, rng.int(COLS), rng.int(COLS)];
    for (const c0 of walks) {
      let c = c0;
      for (let r = 0; r < ROWS - 1; r++) {
        const n = get(r, c);
        let next = c;
        for (const o of rng.shuffle([c - 1, c, c + 1].filter((x) => x >= 0 && x < COLS))) {
          if (!crosses(r, c, o)) {
            next = o;
            break;
          }
        }
        edges.add(r + ':' + c + '>' + next);
        const m = get(r + 1, next);
        if (!n.next.includes(m.id)) n.next.push(m.id);
        c = next;
      }
    }
    const list = [...nodes.values()].sort((a, b) => a.row - b.row || a.col - b.col);
    const parentsOf = (n) => list.filter((p) => p.next.includes(n.id));
    for (const n of list) {
      if (n.row === 0) n.kind = 'battle';
      else if (n.row === ROWS - 1) n.kind = 'rest';
      else if (n.row === 3) n.kind = 'treasure';
      else {
        for (let tries = 0; tries < 12 && !n.kind; tries++) {
          const opts = [['battle', 45], ['event', 24]];
          if (n.row >= 2) opts.push(['elite', 14]);
          if (n.row >= 1) opts.push(['shop', 10]);
          if (n.row >= 2 && n.row <= 4) opts.push(['rest', 7]);
          const k = rng.weighted(opts);
          if ((k === 'elite' || k === 'shop' || k === 'rest') && parentsOf(n).some((p) => p.kind === k)) continue;
          n.kind = k;
        }
        if (!n.kind) n.kind = 'battle';
      }
    }
    const plain = () => list.filter((n) => n.row >= 2 && n.row <= 5 && n.kind === 'battle');
    if (!list.some((n) => n.kind === 'shop') && plain().length) rng.pick(plain()).kind = 'shop';
    if (!list.some((n) => n.kind === 'elite') && plain().length) rng.pick(plain()).kind = 'elite';
    for (const n of list) if (n.row === ROWS - 1) n.next = ['boss'];
    list.push({ id: 'boss', row: ROWS, col: 2, kind: 'boss', next: [], jx: 0 });
    return { act, nodes: list };
  }

  function getNode(run, id) {
    return run.map.nodes.find((n) => n.id === id) || null;
  }

  function availableNodes(run) {
    if (run.pending || run.over) return [];
    if (!run.pos) return run.map.nodes.filter((n) => n.row === 0);
    const at = getNode(run, run.pos);
    return at ? at.next.map((id) => getNode(run, id)) : [];
  }

  // ------------------------------------------------------------ encounters

  function cpFor(run, node, baseOnly, kind) {
    const k = kind || node.kind;
    let cp = 9 + (run.act - 1) * 4 + Math.floor(node.row / 2) + (k === 'elite' ? 1 : 0) + (k === 'boss' ? 2 : 0);
    if (baseOnly) return cp;
    cp += 1 + run.cpBonus;
    if (hasRelic(run, 'war_horn')) cp += 1;
    if (hasRelic(run, 'legion_banner')) cp += 2;
    if (hasRelic(run, 'tyrant_heart')) cp += 3;
    if (hasRelic(run, 'titan_gauntlet')) cp -= 1;
    return cp;
  }

  function encounterCost(units) {
    let c = 0;
    for (const u of units) c += UNITS[u.type].cost + RANK_COST[u.rank] + 0.6 * u.talents.length;
    return c;
  }

  function randomTalentFor(rng, type, owned) {
    const ids = Object.keys(TALENTS).filter((t) => talentEligible(type, t, owned));
    return ids.length ? rng.pick(ids) : null;
  }

  function connected(t, w, h) {
    const seen = new Uint8Array(w * h);
    const q = [];
    for (let x = 0; x < w; x++) {
      const i = (h - 1) * w + x;
      if (t[i] === 0) {
        seen[i] = 1;
        q.push(i);
      }
    }
    while (q.length) {
      const i = q.pop();
      const x = i % w;
      const y = (i - x) / w;
      for (const [dx, dy] of D.DIRS) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
        const ni = ny * w + nx;
        if (seen[ni] || t[ni] !== 0) continue;
        seen[ni] = 1;
        q.push(ni);
      }
    }
    for (let i = 0; i < w * h; i++) if (t[i] === 0 && !seen[i]) return false;
    return true;
  }

  // Obstacles sit in the middle rows, mirrored so neither side is favored.
  function genTerrain(rng, act, w, h) {
    for (let attempt = 0; attempt < 40; attempt++) {
      const t = new Array(w * h).fill(0);
      const put = (x, y, v) => {
        t[y * w + x] = v;
        t[(h - 1 - y) * w + (w - 1 - x)] = v;
      };
      const spot = () => [rng.range(0, w - 1), rng.range(2, Math.floor((h - 1) / 2))];
      const nRock = rng.range(1, act === 1 ? 2 : 3);
      const nWater = act === 2 ? rng.range(1, 3) : act === 1 ? rng.range(0, 1) : 0;
      const nLava = act === 3 ? rng.range(1, 2) : 0;
      for (let i = 0; i < nRock; i++) {
        const [x, y] = spot();
        put(x, y, E.T_ROCK);
      }
      for (let i = 0; i < nWater; i++) {
        const [x, y] = spot();
        put(x, y, E.T_WATER);
        if (x + 1 < w && rng.chance(0.5)) put(x + 1, y, E.T_WATER);
      }
      for (let i = 0; i < nLava; i++) {
        const [x, y] = spot();
        put(x, y, E.T_LAVA);
        if (x + 1 < w && rng.chance(0.5)) put(x + 1, y, E.T_LAVA);
      }
      if (connected(t, w, h)) return t;
    }
    return new Array(w * h).fill(0);
  }

  function placeEnemies(rng, units, terrain, w) {
    const used = new Set();
    const front = ['tank', 'melee', 'skirmisher', 'monster'];
    for (const u of units) {
      const T = UNITS[u.type];
      let rows;
      if (T.boss) rows = T.role === 'caster' ? [0, 1] : [1, 0];
      else if (front.includes(T.role) || u.type === 'lightning') rows = [1, 0];
      else rows = [0, 1];
      const xs = [...Array(w).keys()]
        .map((x) => [x, Math.abs(x - (w - 1) / 2) + rng.next() * 3.5])
        .sort((a, b) => a[1] - b[1])
        .map((a) => a[0]);
      let placed = false;
      for (const y of rows) {
        for (const x of xs) {
          const k = x + ',' + y;
          if (used.has(k) || terrain[y * w + x] !== 0) continue;
          used.add(k);
          u.x = x;
          u.y = y;
          u.facing = 2;
          placed = true;
          break;
        }
        if (placed) break;
      }
    }
  }

  // Mission goals. The primary goal decides how the battle is won (a full rout always works);
  // bonus goals pay out extra rewards when completed.
  const PRIMARY = {
    normal: [['rout', 34], ['banner', 16], ['prison', 14], ['hold', 14], ['commander', 12], ['survive', 10]],
    elite: [['rout', 45], ['commander', 30], ['banner', 25]],
  };

  // Units that sat out the last battle, for the featured-unit bonus.
  function musterCandidates(run) {
    if (!run.lastDeployed || !run.lastDeployed.length) return [];
    return run.roster.filter((u) => !run.lastDeployed.includes(u.id) && !u.wounded);
  }

  function genEncounter(run, node, kindOverride) {
    const kind = kindOverride || node.kind;
    const act = run.act;
    const rng = AG.derive(run.seed, 'enc:' + act + ':' + node.id + ':' + kind);
    const group = kind === 'boss' ? 'boss' : kind === 'elite' ? 'elite' : 'normal';
    const pool = ENCOUNTERS[act][group];
    const fresh = pool.filter((t) => !run.recentEnc.includes(t.name));
    const tpl = rng.pick(fresh.length ? fresh : pool);
    const diff = DIFFICULTIES.find((d) => d.id === run.difficulty) || DIFFICULTIES[1];
    const primary = group === 'boss' ? 'boss' : rng.weighted(PRIMARY[group]);
    // Unit count follows a Command Point budget, like the player's army. Ranks and
    // talents come on top, growing with the act and floor the way the player's do.
    const mult = { normal: [0, 0.9, 1.05, 1.12], elite: [0, 1.15, 1.3, 1.35], boss: [0, 1.35, 1.25, 1.3] }[group][act];
    const budget = cpFor(run, node, true, kind) * mult * diff.mult * (primary === 'survive' ? 1.3 : 1);
    const units = tpl.units.map((t, i) => ({ type: t, rank: tpl.ranks ? tpl.ranks[i] : 1, talents: [] }));
    const unitCost = () => units.reduce((t, u) => t + UNITS[u.type].cost, 0);
    while (unitCost() > budget + 0.5 && units.length > 2) {
      let i = units.length - 1;
      while (i >= 0 && UNITS[units[i].type].boss) i--;
      if (i < 0) break;
      units.splice(i, 1);
    }
    for (let guard = 0; guard < 30; guard++) {
      const addable = tpl.pool.filter((t) => UNITS[t].cost <= budget - unitCost() + 0.5);
      if (!addable.length || units.length >= 8) break;
      units.push({ type: rng.pick(addable), rank: 1, talents: [] });
    }
    const depth = Math.min(1, node.row / ROWS);
    const elite = group === 'elite' ? 1 : 0;
    const p2 = ([0, 0.12 * depth, 0.35 + 0.15 * depth, 0.45 + 0.1 * depth][act] + 0.15 * elite) * diff.mult;
    const p3 = ([0, 0, 0.04 + 0.06 * depth, 0.18 + 0.15 * depth][act] + 0.05 * elite) * diff.mult;
    const pt = [0, 0.05, 0.25, 0.45][act] + 0.2 * elite;
    for (const u of units) {
      if (UNITS[u.type].boss) continue;
      if (!tpl.ranks) {
        const r = rng.next();
        if (r < p3) u.rank = 3;
        else if (r < p3 + p2) u.rank = 2;
      }
      const talents = rng.chance(pt) ? (act === 3 && elite && rng.chance(0.3) ? 2 : 1) : 0;
      for (let k = 0; k < talents; k++) {
        const t = randomTalentFor(rng, u.type, u.talents);
        if (t) u.talents.push(t);
      }
    }
    if (primary === 'commander') {
      let lead = null;
      for (const u of units) if (!lead || UNITS[u.type].cost + u.rank > UNITS[lead.type].cost + lead.rank) lead = u;
      lead.vip = true;
      lead.rank = Math.min(3, lead.rank + 1);
    }
    const terrain = genTerrain(rng, act, BOARD, BOARD);
    placeEnemies(rng, units, terrain, BOARD);
    const used = new Set(units.map((u) => u.x + ',' + u.y));
    const open = (x, y) => x >= 0 && y >= 0 && x < BOARD && y < BOARD && terrain[y * BOARD + x] === 0 && !used.has(x + ',' + y);
    const pickTile = (rows, xs) => {
      const c = [];
      for (const y of rows) for (const x of xs) if (open(x, y)) c.push([x, y]);
      return c.length ? rng.pick(c) : null;
    };
    const enc = {
      name: tpl.name,
      kind,
      stance: tpl.stance,
      objective: 'all',
      primary,
      units,
      terrain,
      w: BOARD,
      h: BOARD,
      budget: Math.round(budget),
      seed: rng.int(2 ** 30) + 1,
      loot: [],
      bonus: [],
    };
    const addObject = (type, rows, xs) => {
      const t = pickTile(rows, xs) || pickTile([0, 1, 2], [...Array(BOARD).keys()]);
      if (!t) return false;
      units.push({ type, rank: 1, talents: [], x: t[0], y: t[1], facing: 2 });
      used.add(t[0] + ',' + t[1]);
      return true;
    };
    switch (primary) {
      case 'boss':
        enc.objective = 'boss';
        break;
      case 'commander':
        enc.objective = 'vip';
        break;
      case 'banner':
        if (addObject('warbanner', [0], [3, 4, 5, 2, 6])) enc.objective = 'destroy';
        break;
      case 'prison':
        if (addObject('cage', [1, 0], rng.chance(0.5) ? [1, 2, 0] : [6, 7, 8])) {
          enc.objective = 'destroy';
          enc.prisoner = { type: rollUnitType(run, rng, 'normal'), rank: recruitRank(run, rng) };
        }
        break;
      case 'hold': {
        const t = pickTile([4, 3, 5], [3, 4, 5, 2, 6]);
        if (t) {
          enc.hold = { x: t[0], y: t[1], need: 2 };
          enc.objective = 'hold';
          if (enc.stance === 'defensive') enc.stance = 'balanced';
        }
        break;
      }
      case 'survive':
        enc.objective = 'survive';
        enc.surviveTurns = act === 1 ? 5 : 6;
        enc.stance = 'aggressive';
        break;
    }
    if (enc.objective === 'all') enc.primary = primary === 'boss' ? 'boss' : 'rout';

    // Bonus: loot on the field, sometimes guarded by specters.
    if (rng.chance(group === 'boss' ? 0.35 : group === 'elite' ? 0.8 : 0.6)) {
      const lk = group === 'normal' ? rng.weighted([['chest', 50], ['tome', 35], ['relic', 15]]) : rng.weighted([['chest', 20], ['tome', 40], ['relic', 40]]);
      // Guarded treasure sits off to a flank so the main fight can happen elsewhere.
      const xs = lk === 'chest' ? rng.shuffle([0, 1, 2, 6, 7, 8, 3, 5, 4]) : rng.chance(0.5) ? [0, 1, 8, 7] : [8, 7, 0, 1];
      const t = pickTile(lk === 'chest' ? [4, 3, 5] : rng.shuffle([4, 3, 5]), xs);
      if (t && !(enc.hold && enc.hold.x === t[0] && enc.hold.y === t[1])) {
        enc.loot.push({ id: 'loot', kind: lk, x: t[0], y: t[1] });
        used.add(t[0] + ',' + t[1]);
        if (lk !== 'chest') {
          const n = act === 1 ? 1 : lk === 'relic' ? 2 : 1 + (rng.chance(0.4) ? 1 : 0);
          const spots = [[0, -1], [-1, 0], [1, 0], [0, 1]].map(([dx, dy]) => [t[0] + dx, t[1] + dy]).filter(([x, y]) => open(x, y));
          for (let i = 0; i < n && i < spots.length; i++) {
            const [x, y] = spots[i];
            units.push({ type: 'specter', rank: act >= 3 ? 2 : 1, talents: [], x, y, facing: 0, post: { x: t[0], y: t[1] } });
            used.add(x + ',' + y);
          }
        }
        enc.bonus.push({ type: 'loot', kind: lk, lootId: 'loot' });
      }
    }
    // Bonus: a challenge.
    if (rng.chance(group === 'boss' ? 0.4 : 0.65)) {
      const opts = [['flawless', 30]];
      if (primary !== 'survive') opts.push(['swift', 35]);
      const muster = musterCandidates(run);
      if (muster.length) opts.push(['muster', 50]);
      const c = rng.weighted(opts);
      if (c === 'swift') {
        const foes = units.filter((u) => !UNITS[u.type].traits.includes('object')).length;
        enc.bonus.push({ type: 'swift', turns: 4 + Math.ceil(foes / 2) + (enc.objective === 'hold' ? 1 : 0) });
      } else if (c === 'muster') enc.bonus.push({ type: 'muster', rid: rng.pick(muster).id });
      else enc.bonus.push({ type: 'flawless' });
    }
    return enc;
  }

  const LOOT_NAMES = { chest: 'War Chest', tome: 'Lost Tome', relic: 'Relic Cache' };

  // Plain-language goals for the war room and the battle panel.
  function objectiveInfo(run, enc) {
    const P = {
      rout: 'Rout the enemy: defeat every enemy unit.',
      boss: 'Slay the boss. Its retinue will scatter.',
      banner: 'Burn the War Banner, or rout the enemy. Enemies near their banner hit 15% harder.',
      prison: 'Break the prison cage, or rout the guards. The freed prisoner joins your army.',
      commander: 'Assassinate the enemy Commander (crowned), or rout them all.',
      hold: 'Hold the shrine: start 2 of your turns in a row with a unit on it. Or rout the enemy.',
      survive: `Survive ${enc.surviveTurns || 6} turns against a larger force. Or rout them.`,
    };
    const short = { rout: 'Rout', boss: 'Slay the boss', banner: 'Burn the banner', prison: 'Break the cage', commander: 'Kill the Commander', hold: 'Hold the shrine', survive: `Survive ${enc.surviveTurns || 6} turns` };
    const key = enc.primary || (enc.objective === 'boss' ? 'boss' : 'rout');
    const bonus = (enc.bonus || []).map((b) => {
      switch (b.type) {
        case 'loot':
          return {
            b,
            text: `Take the ${LOOT_NAMES[b.kind]}${b.kind === 'chest' ? '' : ' (guarded by specters)'}: stand a unit on it and spend its action.`,
            reward: b.kind === 'chest' ? `+${25 + 10 * run.act} gold` : b.kind === 'tome' ? 'Teach a talent' : 'A relic',
          };
        case 'swift':
          return { b, text: `Win within ${b.turns} turns.`, reward: `+${15 + 5 * run.act} gold` };
        case 'flawless':
          return { b, text: 'Win without losing a unit.', reward: `+${15 + 5 * run.act} gold` };
        case 'muster': {
          const u = unitById(run, b.rid);
          return { b, text: u ? `Field ${u.name} the ${UNITS[u.type].name}, who sat out the last battle.` : 'Field a unit that sat out the last battle.', reward: u && u.rank < 3 ? 'A free promotion for them' : '+30 gold' };
        }
      }
      return { b, text: '', reward: '' };
    });
    return { primary: P[key] || P.rout, short: short[key] || 'Rout', key, bonus };
  }

  function deployRows(run, enc) {
    const rows = [enc.h - 2, enc.h - 1];
    if (hasRelic(run, 'scout_map')) rows.unshift(enc.h - 3);
    return rows;
  }

  // ------------------------------------------------------------ entering nodes

  function enterNode(run, id) {
    const node = getNode(run, id);
    if (!node || !availableNodes(run).some((n) => n.id === id)) return false;
    run.cur = id;
    switch (node.kind) {
      case 'battle':
      case 'elite':
      case 'boss':
        run.pending = { type: 'battle', nodeId: id, enc: genEncounter(run, node), attempt: 0 };
        break;
      case 'shop':
        run.pending = { type: 'shop', nodeId: id, stock: genShop(run, node) };
        break;
      case 'rest':
        run.pending = { type: 'rest', nodeId: id };
        break;
      case 'treasure': {
        const rng = AG.derive(run.seed, 'treasure:' + run.act + ':' + id);
        const relic = pickRelic(run, rng, [randomRelicTier(rng, run.act)]) || pickRelic(run, rng, ['common', 'uncommon', 'rare']);
        const gold = rng.range(20, 35);
        run.pending = { type: 'treasure', nodeId: id, relic, gold, taken: false };
        break;
      }
      case 'event': {
        const rng = AG.derive(run.seed, 'event:' + run.act + ':' + id);
        const pool = EVENTS.filter((ev) => !run.seenEvents || !run.seenEvents.includes(ev.id));
        const ev = rng.pick(pool.length ? pool : EVENTS);
        run.seenEvents = (run.seenEvents || []).concat(ev.id);
        run.pending = { type: 'event', nodeId: id, eventId: ev.id, ctx: ev.prepare ? ev.prepare(run, rng) : {}, result: null };
        break;
      }
    }
    save(run);
    return true;
  }

  function completeNode(run) {
    if (!run.pending) return;
    const id = run.pending.nodeId;
    run.visited.push(run.act + ':' + id);
    run.pos = id;
    run.cur = null;
    run.pending = null;
    if (id === 'boss') {
      if (run.act >= 3) {
        run.over = true;
        run.won = true;
        recordMeta(run);
      } else {
        run.act++;
        run.map = genMap(run, run.act);
        run.pos = null;
        run.recentEnc = [];
      }
    }
    save(run);
  }

  // ------------------------------------------------------------ battles

  function deployCost(run, rid) {
    const u = unitById(run, rid);
    return u ? UNITS[u.type].cost : 0;
  }

  function battleConfig(run, deployment) {
    const enc = run.pending.enc;
    const units = [];
    for (const d of deployment) {
      const r = unitById(run, d.rid);
      if (!r) continue;
      units.push({ type: r.type, rank: r.rank, talents: r.talents, team: 'P', x: d.x, y: d.y, facing: d.facing != null ? d.facing : 0, rid: r.id, name: r.name, wounded: r.wounded });
    }
    for (const e of enc.units)
      units.push({ type: e.type, rank: e.rank, talents: e.talents, team: 'E', x: e.x, y: e.y, facing: e.facing, vip: e.vip, post: e.post });
    return {
      w: enc.w,
      h: enc.h,
      terrain: enc.terrain,
      units,
      relics: { P: run.relics.slice(), E: [] },
      seed: enc.seed + (run.pending.attempt || 0) * 7919,
      objective: enc.objective,
      hold: enc.hold,
      surviveTurns: enc.surviveTurns,
      loot: enc.loot,
      turnLimit: 30,
    };
  }

  function rarityWeights(act, kind) {
    const base = { 1: [55, 38, 7, 0], 2: [30, 45, 25, 0], 3: [18, 42, 33, 7] }[act];
    if (kind === 'elite' || kind === 'boss') return [base[0] * 0.5, base[1], base[2] * 1.6, base[3] * 2 + (act >= 2 ? 3 : 0)];
    return base;
  }

  function rollUnitType(run, rng, kind, exclude) {
    const w = rarityWeights(run.act, kind);
    const rarity = rng.weighted([['common', w[0]], ['uncommon', w[1]], ['rare', w[2]], ['legendary', w[3]]]);
    let pool = RECRUITABLE.filter((t) => UNITS[t].rarity === rarity && !(exclude || []).includes(t));
    if (!pool.length) pool = RECRUITABLE.filter((t) => UNITS[t].rarity !== 'legendary' && !(exclude || []).includes(t));
    return rng.pick(pool);
  }

  function recruitRank(run, rng) {
    const r = rng.next();
    if (run.act >= 3) return r < 0.1 ? 3 : r < 0.6 ? 2 : 1;
    if (run.act === 2) return r < 0.35 ? 2 : 1;
    return 1;
  }

  function rollTalent(run, rng, exclude) {
    const ids = Object.keys(TALENTS).filter((t) => !(exclude || []).includes(t) && run.roster.some((u) => canLearn(u, t)));
    return ids.length ? rng.pick(ids) : null;
  }

  function randomRelicTier(rng, act) {
    return rng.weighted([['common', 55 - act * 5], ['uncommon', 33], ['rare', 12 + act * 5]]);
  }

  function pickRelic(run, rng, tiers, exclude) {
    const pool = Object.keys(RELICS).filter((id) => tiers.includes(RELICS[id].tier) && !run.relics.includes(id) && !(exclude || []).includes(id));
    return pool.length ? rng.pick(pool) : null;
  }

  function gainRelic(run, id) {
    if (!id || run.relics.includes(id)) return;
    run.relics.push(id);
    if (id === 'kings_ransom') run.gold += 150;
    if (id === 'golden_standard') {
      run.maxBanners++;
      run.banners = run.maxBanners;
    }
  }

  function genSpoils(run, rng, kind) {
    const out = [];
    const t1 = rollUnitType(run, rng, kind);
    out.push({ type: 'recruit', unit: t1, rank: recruitRank(run, rng) });
    const tal = rollTalent(run, rng);
    if (tal) out.push({ type: 'talent', talent: tal });
    const canPromote = run.roster.some((u) => u.rank < 3);
    const third = rng.weighted([['promote', canPromote ? 40 : 0], ['recruit', 35], ['talent', 25]]);
    if (third === 'promote') out.push({ type: 'promote' });
    else if (third === 'talent' && rollTalent(run, rng, [tal])) out.push({ type: 'talent', talent: rollTalent(run, rng, [tal]) });
    else out.push({ type: 'recruit', unit: rollUnitType(run, rng, kind, [t1]), rank: recruitRank(run, rng) });
    while (out.length < 3) out.push(canPromote ? { type: 'promote' } : { type: 'gold', amount: 30 });
    return out;
  }

  // Apply the outcome of a finished battle. `s` is the engine state.
  function finishBattle(run, s, deployment) {
    const p = run.pending;
    const node = getNode(run, p.nodeId);
    const kind = p.enc.kind;
    if (s.winner !== 'P') {
      run.banners--;
      run.stats.losses++;
      if (run.banners <= 0) {
        run.over = true;
        run.won = false;
        recordMeta(run);
      } else {
        p.attempt = (p.attempt || 0) + 1;
      }
      save(run);
      return { won: false, bannersLeft: run.banners };
    }
    const rng = AG.derive(run.seed, 'loot:' + run.act + ':' + node.id + ':' + (p.attempt || 0));
    let gold = kind === 'boss' ? 75 : kind === 'elite' ? rng.range(30, 38) : rng.range(14, 20);
    if (hasRelic(run, 'coin_purse')) gold += 12;
    if (hasRelic(run, 'kings_ransom')) gold += 20;
    const cp = cpFor(run, node, false, kind);
    const used = deployment.reduce((t, d) => t + deployCost(run, d.rid), 0);
    const unspent = Math.max(0, cp - used);
    const eff = unspent * EFFICIENCY_GOLD * (hasRelic(run, 'alchemist_stone') ? 2 : 1);
    run.gold += gold + eff;
    run.stats.gold += gold + eff;
    run.stats.efficiency += eff;
    run.stats.battles++;
    if (kind === 'elite') run.stats.elites++;
    if (kind === 'boss') run.stats.bosses++;

    const deployedIds = new Set(deployment.map((d) => d.rid));
    const fallen = [];
    for (const r of run.roster) {
      if (!deployedIds.has(r.id)) {
        r.wounded = false;
        continue;
      }
      const bu = s.units.find((u) => u.rid === r.id);
      r.battles++;
      if (bu) {
        r.kills += bu.kills;
        run.stats.kills += bu.kills;
        if (!bu.alive) {
          fallen.push(r.name);
          run.stats.fallen++;
          if (!hasRelic(run, 'field_kit')) r.wounded = true;
        }
      }
    }
    if (kind === 'boss') {
      for (const r of run.roster) r.wounded = false;
      run.banners = Math.min(run.maxBanners, run.banners + 1);
    }
    run.recentEnc = run.recentEnc.concat(p.enc.name).slice(-3);
    run.lastDeployed = deployment.map((d) => d.rid);
    const reward = { type: 'reward', nodeId: p.nodeId, kind, gold, eff, unspent, fallen, spoils: genSpoils(run, rng, kind), spoilTaken: false, objectives: [] };
    const info = objectiveInfo(run, p.enc);
    for (const it of info.bonus) {
      const b = it.b;
      let done = false;
      if (b.type === 'loot') done = s.loot.some((l) => l.id === b.lootId && l.taken);
      else if (b.type === 'swift') done = s.turn <= b.turns;
      else if (b.type === 'flawless') done = !s.units.some((u) => u.team === 'P' && !u.nonCombat && !u.alive);
      else if (b.type === 'muster') done = deployment.some((d) => d.rid === b.rid);
      let got = '';
      if (done) {
        if (b.type === 'loot' && b.kind === 'chest') {
          const g = 25 + 10 * run.act;
          run.gold += g;
          run.stats.gold += g;
          got = `+${g} gold`;
        } else if (b.type === 'loot' && b.kind === 'tome') {
          const picks = [];
          for (let i = 0; i < 3; i++) {
            const t = rollTalent(run, rng, picks);
            if (t) picks.push(t);
          }
          reward.tome = picks;
          reward.tomeTaken = picks.length === 0;
          got = 'choose a talent below';
        } else if (b.type === 'loot' && b.kind === 'relic') {
          const id = pickRelic(run, rng, [randomRelicTier(rng, run.act)]) || pickRelic(run, rng, ['common', 'uncommon', 'rare']);
          if (id) {
            gainRelic(run, id);
            reward.lootRelic = id;
            got = RELICS[id].name;
          } else {
            run.gold += 40;
            got = '+40 gold';
          }
        } else if (b.type === 'swift' || b.type === 'flawless') {
          const g = 15 + 5 * run.act;
          run.gold += g;
          run.stats.gold += g;
          got = `+${g} gold`;
        } else if (b.type === 'muster') {
          const u = unitById(run, b.rid);
          if (u && u.rank < 3) {
            u.rank++;
            got = `${u.name} is promoted`;
          } else {
            run.gold += 30;
            got = '+30 gold';
          }
        }
      }
      reward.objectives.push({ text: it.text, done, got });
    }
    if (p.enc.prisoner) {
      if (run.roster.length < MAX_ROSTER) {
        const u = addRecruit(run, p.enc.prisoner.type, p.enc.prisoner.rank);
        reward.prisoner = u.id;
      } else {
        run.gold += 30;
        reward.prisonerGold = 30;
      }
    }
    if (kind === 'elite') {
      const id = pickRelic(run, rng, [randomRelicTier(rng, run.act)]) || pickRelic(run, rng, ['common', 'uncommon', 'rare']);
      if (id) {
        gainRelic(run, id);
        reward.relicGained = id;
      }
    }
    if (kind === 'boss') {
      const picks = [];
      for (let i = 0; i < 3; i++) {
        const id = pickRelic(run, rng, ['boss'], picks);
        if (id) picks.push(id);
      }
      reward.bossRelics = picks;
      reward.bossRelicTaken = picks.length === 0;
    }
    run.pending = reward;
    save(run);
    return { won: true, gold, eff, unspent };
  }

  function takeSpoil(run, index, rid) {
    const p = run.pending;
    if (!p || p.type !== 'reward' || p.spoilTaken) return false;
    const sp = p.spoils[index];
    if (!sp) return false;
    if (sp.type === 'recruit') {
      if (run.roster.length >= MAX_ROSTER) return false;
      addRecruit(run, sp.unit, sp.rank);
    } else if (sp.type === 'talent') {
      if (!teach(run, rid, sp.talent)) return false;
    } else if (sp.type === 'promote') {
      if (!promote(run, rid, true)) return false;
    } else if (sp.type === 'gold') {
      run.gold += sp.amount;
    }
    p.spoilTaken = true;
    save(run);
    return true;
  }

  function takeTome(run, index, rid) {
    const p = run.pending;
    if (!p || p.type !== 'reward' || !p.tome || p.tomeTaken) return false;
    const t = p.tome[index];
    if (!t || !teach(run, rid, t)) return false;
    p.tomeTaken = true;
    save(run);
    return true;
  }

  function skipTome(run) {
    const p = run.pending;
    if (!p || !p.tome || p.tomeTaken) return;
    p.tomeTaken = true;
    run.gold += 10;
    save(run);
  }

  function skipSpoils(run) {
    const p = run.pending;
    if (!p || p.type !== 'reward' || p.spoilTaken) return;
    run.gold += 10;
    p.spoilTaken = true;
    save(run);
  }

  function takeBossRelic(run, id) {
    const p = run.pending;
    if (!p || !p.bossRelics || p.bossRelicTaken || !p.bossRelics.includes(id)) return false;
    gainRelic(run, id);
    p.bossRelicTaken = true;
    save(run);
    return true;
  }

  // ------------------------------------------------------------ shop, rest, treasure

  function genShop(run, node) {
    const rng = AG.derive(run.seed, 'shop:' + run.act + ':' + node.id);
    const items = [];
    const seen = [];
    for (let i = 0; i < 3; i++) {
      const t = rollUnitType(run, rng, 'normal', seen);
      seen.push(t);
      const rank = recruitRank(run, rng);
      items.push({ kind: 'recruit', unit: t, rank, price: discount(run, RECRUIT_PRICE[UNITS[t].rarity] + (rank - 1) * 25), sold: false });
    }
    const tl = [];
    for (let i = 0; i < 3; i++) {
      const t = rollTalent(run, rng, tl);
      if (!t) break;
      tl.push(t);
      items.push({ kind: 'talent', talent: t, price: discount(run, TALENT_PRICE), sold: false });
    }
    const rl = [];
    for (let i = 0; i < 2; i++) {
      const id = pickRelic(run, rng, [randomRelicTier(rng, run.act)], rl) || pickRelic(run, rng, ['common', 'uncommon', 'rare'], rl);
      if (!id) break;
      rl.push(id);
      items.push({ kind: 'relic', relic: id, price: discount(run, RELIC_PRICE[RELICS[id].tier]), sold: false });
    }
    items.push({ kind: 'heal', price: discount(run, 25), sold: false });
    items.push({ kind: 'banner', price: discount(run, 60), sold: false });
    return items;
  }

  function canBuy(run, item) {
    if (item.sold || run.gold < item.price) return false;
    if (item.kind === 'recruit') return run.roster.length < MAX_ROSTER;
    if (item.kind === 'talent') return run.roster.some((u) => canLearn(u, item.talent));
    if (item.kind === 'heal') return run.roster.some((u) => u.wounded);
    if (item.kind === 'banner') return run.banners < run.maxBanners;
    return true;
  }

  function buy(run, index, rid) {
    const p = run.pending;
    if (!p || p.type !== 'shop') return false;
    const item = p.stock[index];
    if (!item || !canBuy(run, item)) return false;
    switch (item.kind) {
      case 'recruit':
        addRecruit(run, item.unit, item.rank);
        break;
      case 'talent':
        if (!teach(run, rid, item.talent)) return false;
        break;
      case 'relic':
        gainRelic(run, item.relic);
        break;
      case 'heal':
        for (const u of run.roster) u.wounded = false;
        break;
      case 'banner':
        run.banners++;
        break;
    }
    run.gold -= item.price;
    item.sold = true;
    save(run);
    return true;
  }

  function rest(run, choice, rid) {
    const p = run.pending;
    if (!p || p.type !== 'rest' || p.done) return false;
    if (choice === 'rest') {
      for (const u of run.roster) u.wounded = false;
      run.banners = Math.min(run.maxBanners, run.banners + 1);
    } else if (choice === 'train') {
      if (!promote(run, rid, true)) return false;
    } else return false;
    p.done = choice;
    save(run);
    return true;
  }

  function takeTreasure(run) {
    const p = run.pending;
    if (!p || p.type !== 'treasure' || p.taken) return false;
    gainRelic(run, p.relic);
    run.gold += p.gold;
    p.taken = true;
    save(run);
    return true;
  }

  // ------------------------------------------------------------ events

  const fullRoster = (run) => run.roster.length >= MAX_ROSTER;
  const uname = (t) => UNITS[t].name;

  const EVENTS = [
    {
      id: 'sellsword',
      title: "The Sellsword's Offer",
      text: 'A scarred mercenary sits by the road, honing a blade. "Coin first, loyalty after. I have fought for worse than you."',
      prepare: (run, rng) => ({ unit: rollUnitType(run, rng, 'elite') }),
      choices: (run, c) => [
        { id: 'hire', label: 'Hire', detail: `Pay 60 gold. A Rank II ${uname(c.unit)} joins your warband.`, enabled: run.gold >= 60 && !fullRoster(run) },
        { id: 'haggle', label: 'Haggle', detail: `Pay 30 gold. Even odds: a Rank I ${uname(c.unit)} joins, or the coin is simply gone.`, enabled: run.gold >= 30 && !fullRoster(run) },
        { id: 'leave', label: 'Move on', detail: 'Keep your gold.' },
      ],
      resolve: (run, c, choice, rid, rng) => {
        if (choice === 'hire') {
          run.gold -= 60;
          const u = addRecruit(run, c.unit, 2);
          return `${u.name} the ${uname(u.type)} counts the coin twice, then falls in line.`;
        }
        if (choice === 'haggle') {
          run.gold -= 30;
          if (rng.chance(0.5)) {
            const u = addRecruit(run, c.unit, 1);
            return `${u.name} the ${uname(u.type)} shrugs, takes the coin and joins you.`;
          }
          return 'The mercenary bites the coin, grins, and is gone before you can blink.';
        }
        return 'You leave the mercenary to the whetstone.';
      },
    },
    {
      id: 'shrine',
      title: 'Shrine of the Forgotten Saint',
      text: 'Candles still burn before a weathered statue, though no keeper is in sight. The air hums with old blessings.',
      prepare: (run, rng) => {
        const opts = [];
        for (let i = 0; i < 3; i++) {
          const t = rollTalent(run, rng, opts);
          if (t) opts.push(t);
        }
        return { talents: opts, seed: rng.int(1e9) };
      },
      choices: (run, c) => [
        { id: 'pray', label: 'Pray', detail: 'A random unit learns a random talent.', enabled: run.roster.some((u) => u.talents.length < MAX_TALENTS) },
        ...c.talents.map((t) => ({
          id: 'offer:' + t,
          label: 'Offer 40 gold: ' + TALENTS[t].name,
          detail: TALENTS[t].desc + ' Choose who learns it.',
          enabled: run.gold >= 40 && run.roster.some((u) => canLearn(u, t)),
          pick: { talent: t },
        })),
        { id: 'leave', label: 'Leave', detail: 'Let the candles burn.' },
      ],
      resolve: (run, c, choice, rid) => {
        if (choice === 'pray') {
          const rng = new AG.RNG(c.seed);
          const pairs = [];
          for (const u of run.roster) for (const t of Object.keys(TALENTS)) if (canLearn(u, t)) pairs.push([u, t]);
          if (!pairs.length) return 'The saint is silent.';
          const [u, t] = rng.pick(pairs);
          u.talents.push(t);
          return `A warm light settles on ${u.name}. They learn ${TALENTS[t].name}.`;
        }
        if (choice.startsWith('offer:')) {
          const t = choice.slice(6);
          if (!teach(run, rid, t)) return null;
          run.gold -= 40;
          return `${unitById(run, rid).name} kneels and rises with ${TALENTS[t].name}.`;
        }
        return 'You bow your head and walk on.';
      },
    },
    {
      id: 'gamble',
      title: "The Gambler's Tent",
      text: 'Dice clatter under a striped awning. A one-eyed bookmaker waves you closer. "Fortune favors the bold, captain."',
      choices: (run) => [
        { id: 'small', label: 'Bet 25 gold', detail: 'Half the time you win 60.', enabled: run.gold >= 25 },
        { id: 'big', label: 'Bet 50 gold', detail: 'Win 130 with odds a little under half.', enabled: run.gold >= 50 },
        { id: 'leave', label: 'Walk away', detail: 'Your purse thanks you.' },
      ],
      resolve: (run, c, choice, rid, rng) => {
        if (choice === 'small') {
          run.gold -= 25;
          if (rng.chance(0.5)) {
            run.gold += 60;
            return 'Double sixes! You scoop up 60 gold.';
          }
          return 'Snake eyes. The bookmaker sweeps your coins away.';
        }
        if (choice === 'big') {
          run.gold -= 50;
          if (rng.chance(0.45)) {
            run.gold += 130;
            return 'The tent erupts as your dice land. You walk off with 130 gold.';
          }
          return 'The dice betray you. Fifty gold, gone.';
        }
        return 'You leave the dice to braver fools.';
      },
    },
    {
      id: 'deserter',
      title: 'A Wounded Deserter',
      text: 'A soldier in a torn tabard limps out of the brush, hands raised. "I am done with my old lord. Take me in, or take my purse. Just let me live."',
      prepare: (run, rng) => ({ unit: rng.pick(RECRUITABLE.filter((t) => UNITS[t].rarity === 'common')) }),
      choices: (run, c) => [
        { id: 'take', label: 'Take them in', detail: `A wounded Rank I ${uname(c.unit)} joins.`, enabled: !fullRoster(run) },
        { id: 'rob', label: 'Take the purse', detail: 'Gain 35 gold.' },
        { id: 'leave', label: 'Let them go', detail: 'Nothing gained, nothing lost.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'take') {
          const u = addRecruit(run, c.unit, 1, { wounded: true });
          return `${u.name} the ${uname(u.type)} swears a new oath. They will need a battle's rest to heal.`;
        }
        if (choice === 'rob') {
          run.gold += 35;
          return 'You take the purse. The deserter vanishes into the trees.';
        }
        return 'The deserter stumbles away, muttering thanks.';
      },
    },
    {
      id: 'armory',
      title: 'The Sealed Armory',
      text: 'Behind a rusted gate lies a single blade, still wet with something dark. It whispers promises of victory.',
      choices: (run) => [
        { id: 'take', label: 'Take the blade', detail: RELICS.cursed_blade.desc, enabled: !hasRelic(run, 'cursed_blade') },
        { id: 'loot', label: 'Strip the racks', detail: 'Gain 30 gold of old iron.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'take') {
          gainRelic(run, 'cursed_blade');
          return 'The Bloodthirst Blade is yours. Your soldiers fight with a terrible hunger.';
        }
        run.gold += 30;
        return 'You haul away the old iron and sell it for 30 gold.';
      },
    },
    {
      id: 'fountain',
      title: 'Fountain of Renewal',
      text: 'Clear water bubbles from a marble basin carved with sleeping lions. Your soldiers gather around it in silence.',
      choices: (run) => [
        { id: 'drink', label: 'Drink deeply', detail: 'Heal all wounds and restore 1 Banner.' },
        { id: 'fill', label: 'Fill flasks to sell', detail: 'Gain 40 gold.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'drink') {
          for (const u of run.roster) u.wounded = false;
          run.banners = Math.min(run.maxBanners, run.banners + 1);
          return 'Wounds close and spirits lift. Your banners fly a little higher.';
        }
        run.gold += 40;
        return 'Pilgrims pay well for the water. You gain 40 gold.';
      },
    },
    {
      id: 'library',
      title: "The Tactician's Library",
      text: 'A ruined keep still holds shelves of campaign journals, annotated by a general long dead.',
      choices: () => [
        { id: 'study', label: 'Study the journals', detail: '+1 Command Point in every battle for the rest of the run.' },
        { id: 'sell', label: 'Sell the books', detail: 'Gain 60 gold.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'study') {
          run.cpBonus += 1;
          return 'You learn to do more with less. +1 Command Point.';
        }
        run.gold += 60;
        return 'A collector pays 60 gold for the lot.';
      },
    },
    {
      id: 'trial',
      title: 'Trial of Champions',
      text: 'A herald blocks the road. "The champions of this land challenge any who pass. Win, and claim a relic of the old kings."',
      choices: () => [
        { id: 'accept', label: 'Accept the challenge', detail: 'Fight an elite battle. Victory earns a relic.' },
        { id: 'decline', label: 'Decline', detail: 'The herald sneers as you pass.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'accept') return { text: 'The champions take the field.', battle: 'elite' };
        return 'You decline. Some battles are not worth fighting.';
      },
    },
    {
      id: 'alchemist',
      title: 'The Wandering Alchemist',
      text: 'A cart rattles with bubbling flasks. "Transformation, my friend! Or perhaps a tonic for the thin-skinned?"',
      choices: (run) => [
        {
          id: 'transmute',
          label: 'Transmute (50 gold)',
          detail: 'Choose a unit. It becomes a random unit of a higher rarity, keeping its rank.',
          enabled: run.gold >= 50 && run.roster.some((u) => ['common', 'uncommon'].includes(UNITS[u.type].rarity)),
          pick: { filter: 'transmute' },
        },
        { id: 'tonic', label: 'Tonic (35 gold)', detail: 'Choose a unit. It learns Thick Hide.', enabled: run.gold >= 35 && run.roster.some((u) => canLearn(u, 'thick_hide')), pick: { talent: 'thick_hide' } },
        { id: 'leave', label: 'Decline', detail: 'Leave the alchemist to the fumes.' },
      ],
      resolve: (run, c, choice, rid, rng) => {
        const u = unitById(run, rid);
        if (choice === 'transmute' && u) {
          const order = ['common', 'uncommon', 'rare'];
          const next = order[order.indexOf(UNITS[u.type].rarity) + 1];
          const t = rng.pick(RECRUITABLE.filter((x) => UNITS[x].rarity === next));
          const old = uname(u.type);
          u.type = t;
          u.talents = u.talents.filter((tl) => talentEligible(t, tl, []));
          run.gold -= 50;
          return `Smoke billows. ${u.name} the ${old} steps out as a ${uname(t)}.`;
        }
        if (choice === 'tonic' && u) {
          if (!teach(run, rid, 'thick_hide')) return null;
          run.gold -= 35;
          return `${u.name} grimaces at the taste, but their skin toughens like leather.`;
        }
        return 'The alchemist shrugs and rattles away.';
      },
    },
    {
      id: 'forge',
      title: 'The Old Forge',
      text: 'A smith with arms like oak branches looks up from the anvil. "Bring me steel and coin, and I will make a soldier better."',
      choices: (run) => [
        { id: 'temper', label: 'Temper (35 gold)', detail: 'Promote one unit by a rank.', enabled: run.gold >= 35 && run.roster.some((u) => u.rank < 3), pick: { filter: 'promote' } },
        { id: 'leave', label: 'Move on', detail: 'The forge fire dims behind you.' },
      ],
      resolve: (run, c, choice, rid) => {
        if (choice === 'temper') {
          if (!promote(run, rid, true)) return null;
          run.gold -= 35;
          const u = unitById(run, rid);
          return `${u.name} returns in reforged gear. Now Rank ${u.rank}.`;
        }
        return 'You leave the smith to the anvil.';
      },
    },
    {
      id: 'battlefield',
      title: 'The Haunted Battlefield',
      text: 'Broken spears and rusted helms cover a silent field. Something glints among the bones, and something else watches.',
      prepare: (run, rng) => ({ roll: rng.next(), relic: pickRelic(run, rng, ['common', 'uncommon']), victim: rng.int(1000) }),
      choices: () => [
        { id: 'search', label: 'Search the fallen', detail: 'Maybe a relic. Maybe a curse that wounds one of your soldiers.' },
        { id: 'leave', label: 'Leave the dead in peace', detail: 'Walk on quietly.' },
      ],
      resolve: (run, c, choice) => {
        if (choice !== 'search') return 'You leave the field to its ghosts.';
        if (c.roll < 0.55 && c.relic && !run.relics.includes(c.relic)) {
          gainRelic(run, c.relic);
          return `Under a shattered shield you find the ${RELICS[c.relic].name}.`;
        }
        const u = run.roster[c.victim % run.roster.length];
        u.wounded = true;
        run.gold += 15;
        return `A cold hand grips ${u.name}, who is now wounded. You find 15 gold in a dead captain's purse.`;
      },
    },
    {
      id: 'militia',
      title: 'Village Militia',
      text: 'Farmers with pitchforks and old bows stand at the village gate. "Bandits took our harvest. Some of us would rather fight than starve."',
      prepare: (run, rng) => {
        const a = rollUnitType(run, rng, 'normal');
        return { units: [a, rollUnitType(run, rng, 'normal', [a])] };
      },
      choices: (run, c) => [
        ...c.units.map((t) => ({ id: 'take:' + t, label: 'Recruit the ' + uname(t), detail: `A Rank I ${uname(t)} joins for free.`, enabled: !fullRoster(run) })),
        { id: 'leave', label: 'Wish them luck', detail: 'Ride on.' },
      ],
      resolve: (run, c, choice) => {
        if (choice.startsWith('take:')) {
          const u = addRecruit(run, choice.slice(5), 1);
          return `${u.name} picks up a weapon and joins your column.`;
        }
        return 'The villagers watch you go.';
      },
    },
    {
      id: 'hermit',
      title: "The Hermit's Counsel",
      text: 'An old warrior lives alone in a cave lined with trophies. "I will teach one of yours, but my lessons leave bruises."',
      prepare: (run, rng) => ({ talent: rollTalent(run, rng) }),
      choices: (run, c) => [
        c.talent
          ? { id: 'learn', label: 'Learn ' + TALENTS[c.talent].name, detail: TALENTS[c.talent].desc + ' The student is wounded.', pick: { talent: c.talent } }
          : { id: 'learn', label: 'Learn', detail: 'The hermit has nothing to teach you.', enabled: false },
        { id: 'leave', label: 'Decline politely', detail: 'Leave the hermit in peace.' },
      ],
      resolve: (run, c, choice, rid) => {
        if (choice === 'learn') {
          if (!teach(run, rid, c.talent)) return null;
          const u = unitById(run, rid);
          u.wounded = true;
          return `${u.name} limps out of the cave having learned ${TALENTS[c.talent].name}.`;
        }
        return 'The hermit returns to polishing an old helm.';
      },
    },
    {
      id: 'caravan',
      title: 'Merchant Caravan',
      text: 'Wagons circle around a campfire. A merchant in a fur hat sizes up your army and your purse.',
      choices: (run) => [
        { id: 'banner', label: 'Buy a new standard (40 gold)', detail: 'Restore 1 Banner.', enabled: run.gold >= 40 && run.banners < run.maxBanners },
        { id: 'sell', label: 'Sell spare gear', detail: 'Gain 25 gold.' },
        { id: 'leave', label: 'Ride on', detail: 'Nothing here for you.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'banner') {
          run.gold -= 40;
          run.banners++;
          return 'A fresh standard flies over your camp. Banners restored by 1.';
        }
        if (choice === 'sell') {
          run.gold += 25;
          return 'The merchant pays 25 gold for your spare gear.';
        }
        return 'The caravan rolls on without you.';
      },
    },
  ];

  function eventDef(id) {
    return EVENTS.find((e) => e.id === id);
  }

  function eventChoices(run) {
    const p = run.pending;
    const ev = eventDef(p.eventId);
    return ev.choices(run, p.ctx).map((c) => Object.assign({ enabled: true }, c));
  }

  // Resolve an event choice. Returns the result text, or null if it was not allowed.
  function chooseEvent(run, choiceId, rid) {
    const p = run.pending;
    if (!p || p.type !== 'event' || p.result) return null;
    const ev = eventDef(p.eventId);
    const choice = eventChoices(run).find((c) => c.id === choiceId);
    if (!choice || !choice.enabled) return null;
    const rng = AG.derive(run.seed, 'eventroll:' + run.act + ':' + p.nodeId + ':' + choiceId);
    const out = ev.resolve(run, p.ctx, choiceId, rid, rng);
    if (out == null) return null;
    if (typeof out === 'object' && out.battle) {
      const node = getNode(run, p.nodeId);
      p.result = out.text;
      run.pending = { type: 'battle', nodeId: p.nodeId, enc: genEncounter(run, node, out.battle), attempt: 0, fromEvent: true };
      save(run);
      return out.text;
    }
    p.result = out;
    save(run);
    return out;
  }

  // ------------------------------------------------------------ deployment

  const FRONT_ROLES = ['tank', 'melee', 'skirmisher', 'monster'];

  // Free deploy tiles nearest the center, front row first or back row first.
  function deploySlots(run, enc, front, taken) {
    const rows = deployRows(run, enc);
    const order = front ? rows.slice().sort((a, b) => a - b) : rows.slice().sort((a, b) => b - a);
    const out = [];
    for (const y of order) {
      const xs = [...Array(enc.w).keys()].sort((a, b) => Math.abs(a - (enc.w - 1) / 2) - Math.abs(b - (enc.w - 1) / 2) || a - b);
      for (const x of xs) if (enc.terrain[y * enc.w + x] === 0 && !taken.has(x + ',' + y)) out.push({ x, y });
    }
    return out;
  }

  const isAttacker = (type) => !!(UNITS[type].act.dmg || (UNITS[type].act.fx && UNITS[type].act.fx.poison));

  // A reasonable default deployment: healthy fighters first, then support, within the budget.
  function suggestDeployment(run, cp) {
    const enc = run.pending.enc;
    const worth = (u) => UNITS[u.type].cost * (1 + 0.3 * u.rank) * (isAttacker(u.type) ? 1 : 0.6) * (u.wounded ? 0.5 : 1);
    const units = run.roster.slice().sort((a, b) => worth(b) - worth(a));
    const pick = [];
    let spent = 0;
    for (const u of units) {
      const c = UNITS[u.type].cost;
      if (spent + c > cp) continue;
      if (!isAttacker(u.type) && pick.filter((p) => isAttacker(p.type)).length < 2 && units.some((o) => o !== u && !pick.includes(o) && isAttacker(o.type) && spent + UNITS[o.type].cost <= cp)) continue;
      pick.push(u);
      spent += c;
    }
    if (!pick.some((u) => isAttacker(u.type))) return [];
    const taken = new Set();
    const out = [];
    for (const u of pick) {
      const front = FRONT_ROLES.includes(UNITS[u.type].role) || u.type === 'lightning';
      const slot = deploySlots(run, enc, front, taken)[0];
      if (!slot) break;
      taken.add(slot.x + ',' + slot.y);
      out.push({ rid: u.id, x: slot.x, y: slot.y, facing: 0 });
    }
    return out;
  }

  // ------------------------------------------------------------ advice

  // Plain-language counter tips for the scout report.
  function scoutTips(enc) {
    const count = (pred) => enc.units.filter((u) => pred(UNITS[u.type], u)).length;
    const has = (...types) => enc.units.some((u) => types.includes(u.type));
    const tips = [];
    if (count((T) => T.armor >= 0.25) >= 2) tips.push('Heavy armor: magic from Pyromancers, Witches and Enchantresses ignores it.');
    if (has('knight')) tips.push('Knights block 70% of frontal blows. Hit them from the side or behind, or use magic.');
    if (count((T) => T.act.dmg === 'magic') >= 2) tips.push('Strong enemy magic: spread out, and a Barrier Ward halves magic damage around it.');
    else if (has('pyromancer', 'witch', 'dragon', 'ashen_tyrant')) tips.push('Area attacks punish clumps. Leave gaps between your units.');
    if (has('assassin', 'beastrider', 'scout')) tips.push('Fast flankers: face your fragile units toward them and screen them with tanks or shrubs.');
    if (has('archer') && count((T) => T.role === 'ranged') >= 2) tips.push('Archers outrange you. Close in with fast units, or soak arrows on a Knight\'s front.');
    if (has('cleric')) tips.push('Enemy Cleric: kill it early, or poison its huddle so the healing fails.');
    if (has('lightning', 'barrier')) tips.push('Wards cannot move. Archers and fireballs can hit them from outside their reach.');
    if (has('golem', 'golem_king')) tips.push('Golems are slow and immune to poison and paralysis. Kite them and burn them with magic.');
    if (has('enchantress')) tips.push('Paralysis strips block. Keep units near a Barrier Ward or use Golems.');
    if (has('wisp')) tips.push('Poison Wisps are fragile. A single arrow volley can drop one.');
    if (has('specter')) tips.unshift('Specters take half damage from physical attacks. Bring magic to claim their treasure.');
    return tips.slice(0, 4);
  }

  // ------------------------------------------------------------ saving

  function save(run) {
    try {
      root.localStorage && root.localStorage.setItem(SAVE_KEY, JSON.stringify(run));
    } catch (e) {
      /* storage unavailable */
    }
  }

  function load() {
    try {
      const j = root.localStorage && root.localStorage.getItem(SAVE_KEY);
      if (!j) return null;
      const r = JSON.parse(j);
      return r && r.v === 1 && !r.over ? r : null;
    } catch (e) {
      return null;
    }
  }

  function clearSave() {
    try {
      root.localStorage && root.localStorage.removeItem(SAVE_KEY);
    } catch (e) {
      /* storage unavailable */
    }
  }

  function loadMeta() {
    try {
      const j = root.localStorage && root.localStorage.getItem(META_KEY);
      return Object.assign({ runs: 0, wins: 0, bestAct: 0 }, j ? JSON.parse(j) : {});
    } catch (e) {
      return { runs: 0, wins: 0, bestAct: 0 };
    }
  }

  function recordMeta(run) {
    if (run.metaRecorded) return;
    run.metaRecorded = true;
    const m = loadMeta();
    m.runs++;
    if (run.won) m.wins++;
    m.bestAct = Math.max(m.bestAct, run.won ? 4 : run.act);
    try {
      root.localStorage && root.localStorage.setItem(META_KEY, JSON.stringify(m));
    } catch (e) {
      /* storage unavailable */
    }
  }

  AG.Run = {
    ROWS, COLS, MAX_ROSTER, EFFICIENCY_GOLD, EVENTS,
    newRun, genMap, getNode, availableNodes, enterNode, completeNode,
    LOOT_NAMES, objectiveInfo, musterCandidates, takeTome, skipTome,
    cpFor, deployRows, deploySlots, suggestDeployment, deployCost, battleConfig, finishBattle, takeSpoil, skipSpoils, takeBossRelic,
    genEncounter, genShop, canBuy, buy, rest, takeTreasure, eventDef, eventChoices, chooseEvent,
    canLearn, teach, promote, promoteCost, dismiss, unitById, unitStats, scoutTips, hasRelic,
    save, load, clearSave, loadMeta, recordMeta,
  };
})(typeof window !== 'undefined' ? window : globalThis);
