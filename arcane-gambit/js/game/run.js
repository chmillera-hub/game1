/* The roguelike run: a branching map per act, battles with retries,
   rewards, shops, camps and events. Pure data + functions; the UI reads and
   mutates a run through these helpers and saves after each change. */
(function (AG) {
  'use strict';
  const Run = (AG.Run = {});
  const SAVE_KEY = 'arcane-gambit/run/v1';
  const SANDBOX_KEY = 'arcane-gambit/sandbox/v1';
  const STARTERS = ['squire', 'knight', 'scout', 'cleric', 'apprentice'];
  const ROWS = 7, COLS = 5;
  Run.STARTERS = STARTERS;
  Run.ACTS = {
    1: { name: 'The Thornwood Board', blurb: 'Goblins, wolves and things that ooze.' },
    2: { name: 'The Gravemarch Board', blurb: 'The dead do not stay down here.' },
    3: { name: 'The Astral Spire', blurb: 'Clockwork, fire and a very old opponent.' },
  };

  function withRng(run, fn) {
    const r = new AG.RNG(run.rng);
    const out = fn(r);
    run.rng = r.s;
    return out;
  }
  Run.withRng = withRng;

  // ------------------------------------------------------------- creation
  Run.newRun = function (opts) {
    opts = opts || {};
    const seed = (opts.seed || (Date.now() ^ Math.floor(Math.random() * 1e9))) >>> 0;
    const run = {
      v: 1, seed, rng: seed, mode: opts.mode || 'standard',
      act: 1, resolve: 40, maxResolve: 40, gold: 50,
      units: STARTERS.slice(), ranks: {}, runes: ['vigor'], relics: [],
      map: null, pos: null, floor: 0,
      usedEnc: [], usedEvents: [],
      screen: 'boon', battle: null, pending: null, event: null, shop: null,
      formations: {}, lastArmy: null,
      stats: { wins: 0, losses: 0, battles: 0, resolveLost: 0, startedAt: Date.now(), mvp: {} },
    };
    run.map = Run.genMap(run, 1);
    run.boons = ['recruit', 'ledger', 'armory', 'veteran'];
    return run;
  };

  Run.sandbox = function () {
    const all = AG.playerUnitIds();
    const runes = [];
    for (const k of Object.keys(AG.Runes)) runes.push(k, k);
    return {
      v: 1, sandbox: true, seed: 1, rng: 1, mode: 'sandbox', act: 1, resolve: 1, maxResolve: 1, gold: 0,
      units: all, ranks: {}, runes, relics: [], formations: {}, lastArmy: null,
      supplyBonus: 0, slotBonus: 0, screen: 'sandbox', stats: { wins: 0, losses: 0, battles: 0, mvp: {} },
    };
  };

  // ---------------------------------------------------------- persistence
  Run.save = function (run) {
    try {
      localStorage.setItem(run.sandbox ? SANDBOX_KEY : SAVE_KEY, JSON.stringify(run));
    } catch (e) { /* storage unavailable: the run lives in memory only */ }
  };
  Run.load = function (sandbox) {
    try {
      const raw = localStorage.getItem(sandbox ? SANDBOX_KEY : SAVE_KEY);
      if (!raw) return null;
      const run = JSON.parse(raw);
      return run && run.v === 1 ? run : null;
    } catch (e) { return null; }
  };
  Run.clear = function () {
    try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* ignore */ }
  };

  // -------------------------------------------------------------- the map
  Run.genMap = function (run, act) {
    return withRng(run, (rng) => {
      const nodes = {};
      const edges = {};
      const key = (r, c) => r + '-' + c;
      const startCols = rng.shuffle([0, 1, 2, 3, 4]).slice(0, 3).concat([rng.int(0, 4), rng.int(0, 4)]);
      for (const c0 of startCols) {
        let c = c0;
        for (let r = 0; r < ROWS; r++) {
          const id = key(r, c);
          if (!nodes[id]) nodes[id] = { id, r, c, next: [], type: null };
          if (r === ROWS - 1) break;
          let nc = c;
          for (const o of rng.shuffle([c - 1, c, c + 1].filter((x) => x >= 0 && x < COLS))) {
            if (o !== c && edges[key(r, o) + '>' + key(r + 1, c)]) continue; // no crossing paths
            nc = o;
            break;
          }
          const nid = key(r + 1, nc);
          edges[id + '>' + nid] = true;
          if (nodes[id].next.indexOf(nid) < 0) nodes[id].next.push(nid);
          c = nc;
        }
      }
      nodes.boss = { id: 'boss', r: ROWS, c: 2, next: [], type: 'boss' };
      const list = Object.keys(nodes).map((k) => nodes[k]).filter((n) => n.id !== 'boss');
      for (const n of list) if (n.r === ROWS - 1) n.next = ['boss'];
      const parents = {};
      for (const n of list) for (const m of n.next) (parents[m] = parents[m] || []).push(n.id);
      list.sort((a, b) => a.r - b.r || a.c - b.c);
      for (const n of list) {
        if (n.r === 0) { n.type = 'battle'; continue; }
        if (n.r === ROWS - 1) { n.type = 'rest'; continue; }
        if (n.r === 3) { n.type = 'treasure'; continue; }
        const par = (parents[n.id] || []).map((id) => nodes[id].type);
        const opts = [
          { t: 'battle', w: 44 },
          { t: 'event', w: 24 },
          { t: 'elite', w: n.r >= 2 ? 15 : 0 },
          { t: 'shop', w: n.r >= 1 ? 10 : 0 },
          { t: 'rest', w: n.r >= 2 && n.r <= 4 ? 7 : 0 },
        ].filter((o) => !(o.t !== 'battle' && o.t !== 'event' && par.indexOf(o.t) >= 0));
        n.type = rng.weighted(opts, (o) => o.w).t;
      }
      // Make sure each act has at least one shop and one elite.
      const mids = list.filter((n) => n.r >= 2 && n.r <= 5 && n.r !== 3);
      if (!list.some((n) => n.type === 'shop') && mids.length) {
        const c = mids.filter((n) => n.type === 'battle' || n.type === 'event');
        (c.length ? rng.pick(c) : rng.pick(mids)).type = 'shop';
      }
      if (!list.some((n) => n.type === 'elite') && mids.length) {
        const c = mids.filter((n) => n.type === 'battle');
        (c.length ? rng.pick(c) : rng.pick(mids)).type = 'elite';
      }
      return { act, nodes, rows: ROWS, cols: COLS };
    });
  };

  Run.reachable = function (run) {
    const nodes = run.map.nodes;
    if (!run.pos) return Object.keys(nodes).filter((k) => nodes[k].r === 0);
    const cur = nodes[run.pos];
    return cur ? cur.next.slice() : [];
  };

  Run.pickEncounter = function (run, tier, rowHint) {
    return withRng(run, (rng) => {
      const act = run.act;
      let want = tier === 'battle' ? (rowHint <= 1 ? 'early' : 'normal') : tier;
      let pool = AG.encounterList((e) => e.act === act && e.tier === want && run.usedEnc.indexOf(e.id) < 0);
      if (!pool.length && want === 'early') pool = AG.encounterList((e) => e.act === act && e.tier === 'normal' && run.usedEnc.indexOf(e.id) < 0);
      if (!pool.length) pool = AG.encounterList((e) => e.act === act && e.tier === want);
      const e = rng.pick(pool);
      run.usedEnc.push(e.id);
      return e.id;
    });
  };

  Run.enter = function (run, id) {
    const node = run.map.nodes[id];
    run.pos = id;
    run.floor++;
    node.visited = true;
    run.pending = null;
    run.event = null;
    run.shop = null;
    switch (node.type) {
      case 'battle':
      case 'elite':
      case 'boss': {
        if (!node.enc) node.enc = node.type === 'boss' ? Run.bossFor(run) : Run.pickEncounter(run, node.type, node.r);
        Run.startBattle(run, node.enc, node.type, null);
        break;
      }
      case 'event':
        run.event = { id: Run.pickEvent(run), result: null };
        run.screen = 'event';
        break;
      case 'shop':
        run.shop = Run.makeShop(run);
        run.screen = 'shop';
        break;
      case 'rest':
        run.rested = false;
        run.screen = 'rest';
        break;
      case 'treasure':
        run.pending = Run.treasure(run);
        run.screen = 'reward';
        break;
      default:
        run.screen = 'map';
    }
  };

  Run.bossFor = function (run) {
    const b = AG.encounterList((e) => e.act === run.act && e.tier === 'boss');
    return b[0].id;
  };

  Run.startBattle = function (run, encId, tier, bonus) {
    const node = run.pos && run.map ? run.map.nodes[run.pos] : null;
    // Later floors of an act are a little tougher.
    const ramp = tier === 'boss' ? 0 : node ? Math.min(6, node.r) * 0.03 : 0;
    run.battle = { enc: encId, tier, attempts: 0, bonus: bonus || null, ramp };
    run.screen = 'setup';
  };
  Run.battleOpts = function (run) {
    return { relics: run.relics || [], ramp: run.battle ? run.battle.ramp || 0 : 0 };
  };

  // --------------------------------------------------------- the army
  Run.limits = function (run, enc) {
    let supply = enc.supply, slots = enc.slots;
    for (const id of run.relics || []) {
      const R = AG.Relics[id];
      if (R.supply) supply += R.supply;
      if (R.slots) slots += R.slots;
    }
    if (run.sandbox) { supply += run.supplyBonus || 0; slots += run.slotBonus || 0; }
    return { supply, slots };
  };
  Run.talentCost = function (run, tid) {
    const T = AG.Talents[tid];
    let c = T.cost;
    if ((run.relics || []).indexOf('tacticsTome') >= 0) c = Math.max(1, c - 1);
    return c;
  };
  Run.entryCost = function (run, e) {
    let c = AG.Units[e.def].cost;
    for (const t of e.talents || []) c += Run.talentCost(run, t);
    if (e.rune) c += AG.Runes[e.rune].cost;
    return c;
  };
  Run.formationCost = function (run, formation) {
    let c = 0;
    for (const e of formation) c += Run.entryCost(run, e);
    return c;
  };
  Run.talentSlots = function (run, def) { return (run.ranks[def] || 0) >= 2 ? 2 : 1; };
  Run.runeCounts = function (run) {
    const n = {};
    for (const r of run.runes) n[r] = (n[r] || 0) + 1;
    return n;
  };
  Run.runesFree = function (run, formation, exceptIdx) {
    const n = Run.runeCounts(run);
    formation.forEach((e, i) => { if (e.rune && i !== exceptIdx) n[e.rune] = (n[e.rune] || 0) - 1; });
    return n;
  };
  Run.validate = function (run, enc, formation) {
    const lim = Run.limits(run, enc);
    const errors = [];
    const cost = Run.formationCost(run, formation);
    if (!formation.length) errors.push('Place at least one unit.');
    if (formation.length > lim.slots) errors.push('Too many units: ' + formation.length + ' of ' + lim.slots + '.');
    if (cost > lim.supply) errors.push('Over supply: ' + cost + ' of ' + lim.supply + '.');
    const free = Run.runesFree(run, formation, -1);
    for (const k in free) if (free[k] < 0) errors.push('Not enough ' + AG.Runes[k].name + 's.');
    return { ok: errors.length === 0, errors, cost, lim };
  };
  Run.armyFor = function (run, formation) {
    return formation.map((e) => ({ def: e.def, x: e.x, y: e.y, talents: (e.talents || []).slice(), rune: e.rune || null, rank: run.ranks[e.def] || 0 }));
  };

  // ------------------------------------------------------------- outcomes
  Run.lossDamage = function (run, s) {
    if (run.mode === 'casual' || run.sandbox) return 0;
    const tier = run.battle.tier;
    let dmg = { battle: 2, event: 2, elite: 3, boss: 4 }[tier] || 2;
    let extra = 0;
    for (const u of s.units) {
      if (!u.alive || u.side !== 1 || u.object) continue;
      extra += u.summoned ? 1 : Math.ceil(u.threat / 2);
    }
    return Math.min(dmg + extra, tier === 'boss' ? 12 : tier === 'elite' ? 10 : 8);
  };

  Run.recordStats = function (run, s) {
    if (!s.stats) return;
    const mvp = run.stats.mvp || (run.stats.mvp = {});
    for (const u of s.units) {
      if (u.side !== 0 || u.summoned) continue;
      const st = s.stats[u.uid];
      if (!st) continue;
      mvp[u.def] = (mvp[u.def] || 0) + st.dealt + st.healed;
    }
  };

  Run.battleLost = function (run, s) {
    const dmg = Run.lossDamage(run, s);
    run.resolve = Math.max(0, run.resolve - dmg);
    run.stats.losses++;
    run.stats.battles++;
    run.stats.resolveLost = (run.stats.resolveLost || 0) + dmg;
    run.battle.attempts++;
    Run.recordStats(run, s);
    if (run.resolve <= 0) run.screen = 'gameover';
    return dmg;
  };

  Run.battleWon = function (run, s) {
    const b = run.battle;
    run.stats.wins++;
    run.stats.battles++;
    Run.recordStats(run, s);
    const reward = withRng(run, (rng) => {
      const act = run.act;
      const r = { title: 'Victory', gold: 0, offers: [], offerTaken: -1, relic: null, relicChoices: null, relicTaken: null, heal: 0, from: b.tier };
      if (b.tier === 'boss') r.gold = rng.int(60, 75);
      else if (b.tier === 'elite') r.gold = rng.int(30, 40) + act * 2;
      else r.gold = rng.int(14, 22) + act * 2;
      if (b.bonus && b.bonus.gold) r.gold += b.bonus.gold;
      for (const id of run.relics) {
        const R = AG.Relics[id];
        if (R.gold) r.gold += R.gold;
        if (R.winHeal) r.heal += R.winHeal;
      }
      r.offers = Run.offers(run, rng, b.tier);
      if (b.tier === 'elite' || (b.bonus && b.bonus.relic)) r.relic = Run.randomRelic(run, rng, ['common', 'uncommon', 'rare']);
      if (b.tier === 'boss') {
        r.title = 'Boss defeated';
        r.relicChoices = Run.relicChoices(run, rng, ['boss', 'rare'], 3);
        r.heal += 15;
      }
      return r;
    });
    run.gold += reward.gold;
    if (reward.heal) reward.heal = Run.heal(run, reward.heal);
    if (reward.relic) Run.addRelic(run, reward.relic);
    run.pending = reward;
    run.battle = null;
    run.screen = 'reward';
    return reward;
  };

  Run.offers = function (run, rng, tier) {
    const act = run.act;
    const w = act === 1 ? { common: 70, uncommon: 27, rare: 3 } : act === 2 ? { common: 35, uncommon: 50, rare: 15 } : { common: 20, uncommon: 45, rare: 35 };
    if (tier === 'elite' || tier === 'boss') { w.rare += 20; w.uncommon += 10; }
    const out = [];
    const used = {};
    const pickUnit = () => {
      const pool = AG.playerUnitIds().filter((k) => run.units.indexOf(k) < 0 && !used[k] && AG.Units[k].rarity !== 'starter');
      if (!pool.length) return null;
      const rar = rng.weighted(['common', 'uncommon', 'rare'].filter((r) => pool.some((k) => AG.Units[k].rarity === r)), (r) => w[r]);
      const k = rng.pick(pool.filter((k2) => AG.Units[k2].rarity === rar));
      used[k] = true;
      return { kind: 'unit', def: k };
    };
    const pickRune = () => {
      const rar = rng.weighted(['common', 'uncommon', 'rare'], (r) => w[r]);
      const pool = Object.keys(AG.Runes).filter((k) => AG.Runes[k].rarity === rar && !used[k]);
      const k = rng.pick(pool.length ? pool : Object.keys(AG.Runes));
      used[k] = true;
      return { kind: 'rune', id: k };
    };
    for (let i = 0; i < 3; i++) {
      const o = (i < 2 || rng.chance(0.3)) ? pickUnit() || pickRune() : pickRune();
      out.push(o);
    }
    return out;
  };

  Run.claimOffer = function (run, idx) {
    const p = run.pending;
    if (!p || p.offerTaken >= 0) return;
    const o = p.offers[idx];
    if (!o) return;
    if (o.kind === 'unit') Run.addUnit(run, o.def);
    else Run.addRune(run, o.id);
    p.offerTaken = idx;
  };
  Run.claimRelic = function (run, id) {
    const p = run.pending;
    if (!p || p.relicTaken) return;
    Run.addRelic(run, id);
    p.relicTaken = id;
  };

  Run.finishReward = function (run) {
    const p = run.pending;
    run.pending = null;
    if (p && p.from === 'boss') {
      if (run.act >= 3) { run.screen = 'victory'; run.stats.endedAt = Date.now(); return; }
      run.act++;
      run.map = Run.genMap(run, run.act);
      run.pos = null;
      run.screen = 'actIntro';
      return;
    }
    run.screen = 'map';
  };

  Run.treasure = function (run) {
    return withRng(run, (rng) => {
      const relic = Run.randomRelic(run, rng, ['common', 'uncommon', 'rare']);
      const gold = rng.int(20, 30);
      run.gold += gold;
      if (relic) Run.addRelic(run, relic);
      return { title: 'Treasure', gold, offers: [], offerTaken: -1, relic, from: 'treasure', heal: 0 };
    });
  };

  // ----------------------------------------------------------- collection
  Run.addUnit = function (run, def) { if (run.units.indexOf(def) < 0) run.units.push(def); };
  Run.addRune = function (run, id) { run.runes.push(id); };
  Run.addRelic = function (run, id) {
    if (!id || run.relics.indexOf(id) >= 0) return;
    run.relics.push(id);
    const R = AG.Relics[id];
    if (R.maxResolve) { run.maxResolve += R.maxResolve; run.resolve += R.maxResolve; }
  };
  Run.heal = function (run, n) {
    const before = run.resolve;
    run.resolve = Math.min(run.maxResolve, run.resolve + n);
    return run.resolve - before;
  };
  Run.hurt = function (run, n) {
    if (run.mode === 'casual') n = Math.ceil(n / 2);
    run.resolve = Math.max(1, run.resolve - n);
  };
  Run.trainable = function (run) { return run.units.filter((d) => (run.ranks[d] || 0) < 2); };
  Run.train = function (run, def) { run.ranks[def] = Math.min(2, (run.ranks[def] || 0) + 1); };
  Run.unitPool = function (run, rarity) {
    return AG.playerUnitIds().filter((k) => AG.Units[k].rarity === rarity && run.units.indexOf(k) < 0);
  };
  Run.randomRune = function (run, rng, rarity) {
    const pool = Object.keys(AG.Runes).filter((k) => !rarity || AG.Runes[k].rarity === rarity);
    return rng.pick(pool);
  };
  Run.randomRelic = function (run, rng, rarities) {
    const pool = AG.relicList((R, k) => rarities.indexOf(R.rarity) >= 0 && run.relics.indexOf(k) < 0);
    if (!pool.length) return null;
    return rng.weighted(pool, (k) => ({ common: 6, uncommon: 4, rare: 2, boss: 1 })[AG.Relics[k].rarity]);
  };
  Run.relicChoices = function (run, rng, rarities, n) {
    const pool = rng.shuffle(AG.relicList((R, k) => rarities.indexOf(R.rarity) >= 0 && run.relics.indexOf(k) < 0));
    return pool.slice(0, n);
  };

  // ---------------------------------------------------------------- boons
  Run.BOONS = {
    recruit: { name: 'Recruit', desc: 'Start with a random common unit.' },
    ledger: { name: 'Quartermaster', desc: 'Start with the Quartermaster’s Ledger: +2 supply in every battle.' },
    armory: { name: 'Armory', desc: 'Start with two random runes.' },
    veteran: { name: 'Veteran', desc: 'Train one of your starting units to Veteran.', pick: 'trainable' },
  };
  Run.takeBoon = function (run, id, picked) {
    withRng(run, (rng) => {
      if (id === 'recruit') Run.addUnit(run, rng.pick(Run.unitPool(run, 'common')));
      else if (id === 'ledger') Run.addRelic(run, 'ledger');
      else if (id === 'armory') { Run.addRune(run, Run.randomRune(run, rng, 'common')); Run.addRune(run, Run.randomRune(run, rng, 'uncommon')); }
      else if (id === 'veteran' && picked) Run.train(run, picked);
    });
    run.boons = null;
    run.screen = 'actIntro';
  };

  // ----------------------------------------------------------------- shop
  const PRICE = { unit: { common: 45, uncommon: 70, rare: 100 }, rune: { common: 30, uncommon: 50, rare: 80 }, relic: { common: 90, uncommon: 120, rare: 150, boss: 200 } };
  Run.discount = function (run) {
    let d = 0;
    for (const id of run.relics) if (AG.Relics[id].discount) d += AG.Relics[id].discount;
    return d;
  };
  Run.price = function (run, base) { return Math.round(base * (1 - Run.discount(run))); };
  Run.makeShop = function (run) {
    return withRng(run, (rng) => {
      const shop = { units: [], runes: [], relics: [], train: { price: 60, used: false }, heal: { price: 35, amt: 10, used: false } };
      const upool = rng.shuffle(AG.playerUnitIds().filter((k) => run.units.indexOf(k) < 0 && AG.Units[k].rarity !== 'starter'));
      for (const k of upool.slice(0, 3)) shop.units.push({ def: k, price: PRICE.unit[AG.Units[k].rarity] + rng.int(-5, 5), sold: false });
      const rpool = rng.shuffle(Object.keys(AG.Runes));
      for (const k of rpool.slice(0, 3)) shop.runes.push({ id: k, price: PRICE.rune[AG.Runes[k].rarity] + rng.int(-4, 4), sold: false });
      for (const k of Run.relicChoices(run, rng, ['common', 'uncommon', 'rare'], 2)) shop.relics.push({ id: k, price: PRICE.relic[AG.Relics[k].rarity] + rng.int(-8, 8), sold: false });
      return shop;
    });
  };
  Run.buy = function (run, kind, idx, picked) {
    const shop = run.shop;
    if (!shop) return false;
    if (kind === 'train' || kind === 'heal') {
      const svc = shop[kind];
      const cost = Run.price(run, svc.price);
      if (svc.used || run.gold < cost) return false;
      if (kind === 'train') { if (!picked) return false; Run.train(run, picked); }
      else Run.heal(run, svc.amt);
      run.gold -= cost;
      svc.used = true;
      return true;
    }
    const item = shop[kind][idx];
    if (!item || item.sold) return false;
    const cost = Run.price(run, item.price);
    if (run.gold < cost) return false;
    run.gold -= cost;
    item.sold = true;
    if (kind === 'units') Run.addUnit(run, item.def);
    else if (kind === 'runes') Run.addRune(run, item.id);
    else if (kind === 'relics') Run.addRelic(run, item.id);
    return true;
  };

  // ----------------------------------------------------------------- camp
  Run.REST_HEAL = 0.3;
  Run.rest = function (run, choice, picked) {
    if (run.rested) return null;
    let text = '';
    if (choice === 'recover') {
      const n = Run.heal(run, Math.round(run.maxResolve * Run.REST_HEAL));
      text = 'You rest by the fire. (+' + n + ' Resolve)';
    } else if (choice === 'train' && picked) {
      Run.train(run, picked);
      text = 'Your ' + AG.Units[picked].name + 's drill until dawn. They are now ' + AG.RANKS[run.ranks[picked]] + 's.';
    } else return null;
    run.rested = true;
    run.restText = text;
    return text;
  };

  // --------------------------------------------------------------- events
  Run.pickEvent = function (run) {
    return withRng(run, (rng) => {
      let pool = AG.Events.filter((e) => e.acts.indexOf(run.act) >= 0 && run.usedEvents.indexOf(e.id) < 0);
      if (!pool.length) pool = AG.Events.filter((e) => e.acts.indexOf(run.act) >= 0);
      const e = rng.pick(pool);
      run.usedEvents.push(e.id);
      return e.id;
    });
  };
  Run.choiceAvailable = function (run, choice) {
    if (!choice.available) return true;
    const r = choice.available(run);
    return r === true ? true : r;
  };
  Run.resolveEvent = function (run, idx, picked) {
    const ev = AG.eventById(run.event.id);
    const ch = ev.choices[idx];
    if (!ch || Run.choiceAvailable(run, ch) !== true) return null;
    const out = withRng(run, (rng) => ch.apply(run, rng, picked));
    if (out && typeof out === 'object' && out.battle) {
      let enc = out.battle;
      if (AG.Encounters[enc + run.act]) enc = enc + run.act;
      run.event.result = out.text;
      Run.startBattle(run, enc, 'event', out.bonus);
      return out.text;
    }
    run.event.result = out;
    return out;
  };
})(globalThis.AG = globalThis.AG || {});
