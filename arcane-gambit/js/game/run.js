/* The roguelike run. Draft a starting army, take an opening, then climb a
   tower per act: battle floors where you pick an easy, medium or hard (or
   elite) fight, an event and a shop halfway up, and a boss at the top.
   Losing costs nothing: rearrange and retry, or pick another fight. After
   the last boss comes an optional mega boss, and the army that won joins
   the Hall of Fame by duelling the champions of earlier runs.
   Pure data + functions; the UI reads and changes a run through these
   helpers and saves after each change. */
(function (AG) {
  'use strict';
  const Run = (AG.Run = {});
  const SAVE_KEY = 'arcane-gambit/run/v2';
  const SANDBOX_KEY = 'arcane-gambit/sandbox/v1';
  const HALL_KEY = 'arcane-gambit/hall/v1';
  Run.HALL_SIZE = 10;
  // Every army has pawns: the Squire comes with every run.
  Run.BASE_UNITS = ['squire'];
  // The starting draft: five picks, each one of three.
  Run.DRAFT = ['common', 'common', 'uncommon', 'uncommon', 'rare'];
  // One act's tower, bottom floor first.
  Run.FLOORS = ['battle', 'battle', 'battle', 'event', 'shop', 'battle', 'battle', 'boss'];
  // Battle floors whose third choice is an elite fight rather than a hard one.
  Run.ELITE_FLOORS = [2, 6];
  // What each choice of fight changes and pays (hp and atk may differ by act).
  Run.DIFF = {
    easy: { name: 'Easy', hp: [-0.2, -0.25, -0.3], atk: [0, 0, -1], gold: [10, 14], offers: 2, luck: 0 },
    medium: { name: 'Medium', hp: 0, atk: 0, gold: [16, 22], offers: 3, luck: 0 },
    hard: { name: 'Hard', hp: [0.35, 0.5, 0.65], atk: [0, 1, 1], gold: [26, 34], offers: 3, luck: 1 },
    elite: { name: 'Elite', hp: 0, atk: 0, gold: [30, 40], offers: 3, luck: 1, relic: true },
  };
  Run.ACTS = {
    1: { name: 'The Thornwood Board', blurb: 'Goblins, wolves and things that ooze.' },
    2: { name: 'The Gravemarch Board', blurb: 'The dead do not stay down here.' },
    3: { name: 'The Astral Spire', blurb: 'Clockwork, fire and a very old opponent.' },
  };

  // A number, or one per act.
  Run.byAct = function (run, v) { return (Array.isArray(v) ? v[run.act - 1] : v) || 0; };

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
      v: 2, seed, rng: seed,
      act: 1, gold: 50, supplyBonus: 0, nextSupply: 0,
      units: Run.BASE_UNITS.slice(), ranks: {}, runes: ['vigor'], relics: [],
      tower: null, floor: 0,
      usedEnc: [], usedEvents: [],
      screen: 'draft', draft: { step: 0, picks: [], options: [] },
      boons: ['recruit', 'ledger', 'armory', 'veteran'],
      battle: null, pending: null, event: null, shop: null,
      formations: {}, lastArmy: null, finalArmy: null, megaWon: false, climb: null,
      stats: { wins: 0, losses: 0, battles: 0, startedAt: Date.now(), mvp: {} },
    };
    run.draft.options = Run.draftOptions(run);
    return run;
  };

  Run.sandbox = function () {
    const all = AG.playerUnitIds();
    const runes = [];
    for (const k of Object.keys(AG.Runes)) runes.push(k, k);
    return {
      v: 2, sandbox: true, seed: 1, rng: 1, act: 1, gold: 0,
      units: all, ranks: {}, runes, relics: [], formations: {}, lastArmy: null,
      supplyBonus: 0, screen: 'sandbox', stats: { wins: 0, losses: 0, battles: 0, mvp: {} },
    };
  };

  // ---------------------------------------------------------- persistence
  // A finished run (placed in the Hall of Fame) is not kept.
  Run.save = function (run) {
    if (run.done) { Run.clear(); return; }
    try {
      localStorage.setItem(run.sandbox ? SANDBOX_KEY : SAVE_KEY, JSON.stringify(run));
    } catch (e) { /* storage unavailable: the run lives in memory only */ }
  };
  Run.load = function (sandbox) {
    try {
      const raw = localStorage.getItem(sandbox ? SANDBOX_KEY : SAVE_KEY);
      if (!raw) return null;
      const run = JSON.parse(raw);
      return run && run.v === 2 && !run.done ? run : null;
    } catch (e) { return null; }
  };
  Run.clear = function () {
    try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* ignore */ }
  };

  // ---------------------------------------------------------------- draft
  // Unit types of a rarity the run does not have yet.
  Run.draftPool = function (run, rarity) {
    return AG.playerUnitIds().filter((k) => AG.Units[k].rarity === rarity && run.units.indexOf(k) < 0);
  };
  Run.draftOptions = function (run) {
    const rarity = Run.DRAFT[run.draft.step];
    return withRng(run, (rng) => rng.shuffle(Run.draftPool(run, rarity)).slice(0, 3));
  };
  Run.draftPick = function (run, def) {
    const d = run.draft;
    if (!d || d.options.indexOf(def) < 0) return;
    Run.addUnit(run, def);
    d.picks.push(def);
    d.step++;
    if (d.step >= Run.DRAFT.length) {
      run.draft = null;
      run.screen = 'boon';
      return;
    }
    d.options = Run.draftOptions(run);
  };

  // ---------------------------------------------------------------- boons
  Run.BOONS = {
    recruit: { name: 'Recruit', desc: 'Add a random common unit to your army.' },
    ledger: { name: 'Quartermaster', desc: 'Start with the Quartermaster’s Ledger: +2 supply in every battle.' },
    armory: { name: 'Armory', desc: 'Start with two random runes, one of them uncommon.' },
    veteran: { name: 'Veteran', desc: 'Train one of your unit types to Veteran (+HP, +1 ATK).', pick: 'trainable' },
  };
  Run.takeBoon = function (run, id, picked) {
    withRng(run, (rng) => {
      if (id === 'recruit') { const pool = Run.draftPool(run, 'common'); if (pool.length) Run.addUnit(run, rng.pick(pool)); }
      else if (id === 'ledger') Run.addRelic(run, 'ledger');
      else if (id === 'armory') { Run.addRune(run, Run.randomRune(run, rng, 'common')); Run.addRune(run, Run.randomRune(run, rng, 'uncommon')); }
      else if (id === 'veteran' && picked) Run.train(run, picked);
    });
    run.boons = null;
    Run.startAct(run, 1);
    run.screen = 'actIntro';
  };

  // ---------------------------------------------------------------- tower
  Run.startAct = function (run, act) {
    run.act = act;
    run.floor = 0;
    run.tower = Run.FLOORS.map((type) => ({ type, options: null, choice: -1, done: false }));
    Run.prepareFloor(run);
  };
  Run.currentFloor = function (run) { return run.tower ? run.tower[run.floor] : null; };
  Run.prepareFloor = function (run) {
    const f = Run.currentFloor(run);
    if (f && f.type === 'battle' && !f.options) f.options = Run.fightOptions(run);
  };
  // How many battle floors of this act lie below the current one.
  Run.battlesBelow = function (run) {
    let n = 0;
    for (let i = 0; i < run.floor; i++) if (run.tower[i].type === 'battle') n++;
    return n;
  };
  Run.fightOptions = function (run) {
    return withRng(run, (rng) => {
      const act = run.act;
      const taken = {};
      const pick = (tiers) => {
        for (const fresh of [true, false]) {
          for (const tier of tiers) {
            const pool = AG.encounterList((e) => e.act === act && e.tier === tier && !taken[e.id] && (!fresh || run.usedEnc.indexOf(e.id) < 0));
            if (pool.length) { const id = rng.pick(pool).id; taken[id] = true; return id; }
          }
        }
        return null;
      };
      const third = Run.ELITE_FLOORS.indexOf(run.floor) >= 0 ? 'elite' : 'hard';
      return [
        { diff: 'easy', enc: pick(['early', 'normal']) },
        { diff: 'medium', enc: pick(['normal', 'early']) },
        { diff: third, enc: third === 'elite' ? pick(['elite']) : pick(['normal', 'early']) },
      ];
    });
  };
  // Step onto the current floor: pick a fight, or walk into the event,
  // the shop or the boss's hall.
  Run.chooseFight = function (run, i) {
    const f = Run.currentFloor(run);
    const o = f && f.options && f.options[i];
    if (!o) return;
    f.choice = i;
    if (run.usedEnc.indexOf(o.enc) < 0) run.usedEnc.push(o.enc);
    Run.startBattle(run, o.enc, o.diff);
  };
  Run.enterFloor = function (run) {
    const f = Run.currentFloor(run);
    run.pending = null;
    if (f.type === 'event') {
      if (!run.event) run.event = { id: Run.pickEvent(run), result: null };
      run.screen = 'event';
    } else if (f.type === 'shop') {
      if (!run.shop) run.shop = Run.makeShop(run);
      run.screen = 'shop';
    } else if (f.type === 'boss') {
      Run.startBattle(run, Run.bossFor(run), 'boss');
    }
  };
  // A fight left unwon gives back the supply an event lent (or took) for it.
  function unspend(run) {
    if (run.battle && run.battle.supplyMod) run.nextSupply = (run.nextSupply || 0) + run.battle.supplyMod;
    run.battle = null;
  }
  // Back out of a fight that has not been won, to choose another.
  Run.backToTower = function (run) {
    const f = Run.currentFloor(run);
    if (f) f.choice = -1;
    unspend(run);
    run.screen = 'tower';
  };
  // Walk away from an event's fight (its prize is lost) or from the mega boss.
  Run.leaveFight = function (run) {
    const tier = run.battle && run.battle.tier;
    unspend(run);
    if (tier === 'mega') { run.screen = 'victory'; return; }
    Run.advance(run);
  };
  Run.advance = function (run) {
    const f = Run.currentFloor(run);
    if (f) f.done = true;
    run.event = null;
    run.shop = null;
    run.battle = null;
    run.floor++;
    Run.prepareFloor(run);
    run.screen = 'tower';
  };
  Run.bossFor = function (run) {
    return AG.encounterList((e) => e.act === run.act && e.tier === 'boss')[0].id;
  };

  Run.startBattle = function (run, encId, diff, bonus) {
    const D = Run.DIFF[diff] || {};
    // Each battle floor up the tower is a little tougher.
    const ramp = run.tower && D.name ? Run.battlesBelow(run) * 0.04 : 0;
    run.battle = {
      enc: encId, tier: diff, attempts: 0, bonus: bonus || null, ramp,
      hpMod: Run.byAct(run, D.hp), atkMod: Run.byAct(run, D.atk), supplyMod: run.nextSupply || 0,
      formation: run.formations && run.formations[encId] ? AG.deepCopy(run.formations[encId]) : [],
    };
    run.nextSupply = 0;
    run.screen = 'setup';
  };
  Run.battleOpts = function (run) {
    const b = run.battle || {};
    return { relics: run.relics || [], ramp: b.ramp || 0, hpMod: b.hpMod || 0, atkMod: b.atkMod || 0 };
  };

  // --------------------------------------------------------- the army
  // Only supply limits the army, and the squares there are to stand on.
  Run.limits = function (run, enc) {
    let supply = enc.supply + (run.supplyBonus || 0);
    for (const id of run.relics || []) {
      const R = AG.Relics[id];
      if (R && R.supply) supply += R.supply;
    }
    if (run.battle && run.battle.enc === enc.id) supply += run.battle.supplyMod || 0;
    const { board } = AG.parseBoard(enc.map, enc.legend);
    let cells = 0;
    for (let i = 0; i < board.n; i++) if (board.deploy[i]) cells++;
    return { supply: Math.max(1, supply), cells };
  };
  Run.talentCost = function (run, tid) {
    const T = AG.Talents[tid];
    let c = T.cost;
    for (const id of run.relics || []) if (AG.Relics[id] && AG.Relics[id].talentDiscount) c -= AG.Relics[id].talentDiscount;
    return Math.max(1, c);
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
    if (cost > lim.supply) errors.push('Over supply: ' + cost + ' of ' + lim.supply + '.');
    const free = Run.runesFree(run, formation, -1);
    for (const k in free) if (free[k] < 0) errors.push('Not enough ' + AG.Runes[k].name + 's.');
    return { ok: errors.length === 0, errors, cost, lim };
  };
  Run.armyFor = function (run, formation) {
    return formation.map((e) => ({ def: e.def, x: e.x, y: e.y, talents: (e.talents || []).slice(), rune: e.rune || null, rank: run.ranks[e.def] || 0 }));
  };

  /* Auto-deploy: as many units as the supply and the deploy squares allow,
     then the leftover supply spent turning the cheapest pieces into stronger
     ones, a few of each kind. Fighters stand in front, shooters and healers
     behind, the centre first. */
  const RARITY_RANK = { common: 1, uncommon: 2, rare: 3 };
  const BACK_ROLES = { ranged: 1, support: 1 };
  Run.autoArmy = function (run, enc) {
    return Run.placeArmy(enc, Run.autoUnits(run, enc).map((def) => ({ def, talents: [], rune: null })));
  };
  // The unit types Auto-deploy brings, most expensive first.
  Run.autoUnits = function (run, enc) {
    const cells = Run.limits(run, enc).cells;
    const supply = Run.limits(run, enc).supply;
    const types = run.units.filter((d) => AG.Units[d]).map((d) => ({ def: d, cost: AG.Units[d].cost, d: AG.Units[d] }));
    if (!types.length || !cells) return [];
    const minCost = Math.min.apply(null, types.map((t) => t.cost));
    const n = Math.min(cells, Math.floor(supply / minCost));
    if (n <= 0) return [];
    const cheapest = types.filter((t) => t.cost === minCost);
    const army = [];
    for (let i = 0; i < n; i++) army.push(cheapest[i % cheapest.length]);
    let left = supply - n * minCost;
    const better = types.slice().sort((a, b) => b.cost - a.cost || (RARITY_RANK[b.d.rarity] || 0) - (RARITY_RANK[a.d.rarity] || 0));
    for (let extraCopies = 0; extraCopies < 6 && left > 0; extraCopies++) {
      let changed = true;
      while (changed && left > 0) {
        changed = false;
        for (const t of better) {
          const cap = (t.cost >= 5 ? 1 : t.cost >= 3 ? 2 : 3) + extraCopies;
          if (army.filter((a) => a.def === t.def).length >= cap) continue;
          let at = -1;
          army.forEach((a, i) => { if (a.cost < t.cost && (at < 0 || a.cost < army[at].cost)) at = i; });
          if (at < 0 || t.cost - army[at].cost > left) continue;
          left -= t.cost - army[at].cost;
          army[at] = t;
          changed = true;
          break;
        }
      }
    }
    return army.sort((a, b) => b.cost - a.cost).map((t) => t.def);
  };
  // Stand entries ({def, talents, rune}) on the deploy squares: fighters
  // front and centre, shooters and healers at the back.
  Run.placeArmy = function (enc, entries) {
    const { board } = AG.parseBoard(enc.map, enc.legend);
    const cells = [];
    for (let i = 0; i < board.n; i++) if (board.deploy[i]) cells.push(i);
    const w = board.w, mid = (w - 1) / 2;
    const row = (i) => (i / w) | 0, central = (i) => Math.abs((i % w) - mid);
    const front = cells.slice().sort((a, b) => row(a) - row(b) || central(a) - central(b));
    const back = cells.slice().sort((a, b) => row(b) - row(a) || central(a) - central(b));
    const used = new Set();
    const out = [];
    const place = (e, list) => {
      const c = list.find((i) => !used.has(i));
      if (c == null) return;
      used.add(c);
      out.push({ def: e.def, x: c % w, y: row(c), talents: (e.talents || []).slice(), rune: e.rune || null });
    };
    for (const e of entries) if (!BACK_ROLES[AG.Units[e.def].role]) place(e, front);
    for (const e of entries) if (BACK_ROLES[AG.Units[e.def].role]) place(e, back);
    return out;
  };

  // ------------------------------------------------------------- outcomes
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
  // A lost fight costs nothing: the war room is waiting.
  Run.battleLost = function (run, s) {
    run.stats.losses++;
    run.stats.battles++;
    run.battle.attempts++;
    Run.recordStats(run, s);
    run.screen = 'setup';
  };

  Run.battleWon = function (run, s) {
    const b = run.battle;
    run.stats.wins++;
    run.stats.battles++;
    Run.recordStats(run, s);
    if (b.tier === 'mega') {
      run.megaWon = true;
      run.battle = null;
      run.screen = 'victory';
      return null;
    }
    if (b.tier === 'boss' && run.act >= 3) {
      run.finalArmy = { army: Run.armyFor(run, b.formation), relics: run.relics.slice(), enc: b.enc };
    }
    const reward = withRng(run, (rng) => {
      const act = run.act;
      const D = Run.DIFF[b.tier];
      const r = { title: 'Victory', gold: 0, offers: [], offerTaken: -1, relic: null, relicChoices: null, relicTaken: null, from: b.tier };
      if (b.tier === 'boss') {
        r.title = 'Boss defeated';
        r.gold = rng.int(60, 75);
        r.offers = Run.offers(run, rng, 2, 3);
        r.relicChoices = Run.relicChoices(run, rng, ['boss', 'rare'], 3);
      } else if (D) {
        r.title = D.name + ' fight won';
        r.gold = rng.int(D.gold[0], D.gold[1]) + act * 2;
        r.offers = Run.offers(run, rng, D.luck, D.offers);
        if (D.relic) r.relic = Run.randomRelic(run, rng, ['common', 'uncommon', 'rare']);
      } else {
        r.gold = rng.int(14, 22) + act * 2;
        r.offers = Run.offers(run, rng, 0, 3);
      }
      if (b.bonus && b.bonus.gold) r.gold += b.bonus.gold;
      if (b.bonus && b.bonus.relic) r.relic = Run.randomRelic(run, rng, ['common', 'uncommon', 'rare']);
      for (const id of run.relics) if (AG.Relics[id].gold) r.gold += AG.Relics[id].gold;
      return r;
    });
    run.gold += reward.gold;
    if (reward.relic) Run.addRelic(run, reward.relic);
    run.pending = reward;
    run.battle = null;
    run.screen = 'reward';
    return reward;
  };

  // Rewards to choose from: n of units and runes, luckier after hard fights.
  Run.offers = function (run, rng, luck, n) {
    const act = run.act;
    const w = act === 1 ? { common: 70, uncommon: 27, rare: 3 } : act === 2 ? { common: 35, uncommon: 50, rare: 15 } : { common: 20, uncommon: 45, rare: 35 };
    w.rare += 12 * (luck || 0);
    w.uncommon += 8 * (luck || 0);
    const out = [];
    const used = {};
    const pickUnit = () => {
      const pool = AG.playerUnitIds().filter((k) => run.units.indexOf(k) < 0 && !used[k]);
      if (!pool.length) return null;
      const tier = (k) => AG.Units[k].rarity;
      const rar = rng.weighted(['common', 'uncommon', 'rare'].filter((r) => pool.some((k) => tier(k) === r)), (r) => w[r]);
      const k = rng.pick(pool.filter((k2) => tier(k2) === rar));
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
    for (let i = 0; i < (n || 3); i++) {
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
      if (run.act >= 3) {
        run.screen = 'victory';
        run.stats.endedAt = Date.now();
        return;
      }
      Run.startAct(run, run.act + 1);
      run.screen = 'actIntro';
      return;
    }
    Run.advance(run);
  };

  // ----------------------------------------------------------- collection
  Run.addUnit = function (run, def) { if (run.units.indexOf(def) < 0) run.units.push(def); };
  Run.addRune = function (run, id) { run.runes.push(id); };
  Run.addRelic = function (run, id) {
    if (!id || run.relics.indexOf(id) >= 0) return;
    run.relics.push(id);
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
  // A one-battle change of supply from an event, good or bad.
  Run.nextBattleSupply = function (run, n) { run.nextSupply = (run.nextSupply || 0) + n; };

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
      const shop = { units: [], runes: [], relics: [], train: { price: 60, used: false } };
      const upool = rng.shuffle(AG.playerUnitIds().filter((k) => run.units.indexOf(k) < 0));
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
    if (kind === 'train') {
      const svc = shop.train;
      const cost = Run.price(run, svc.price);
      if (svc.used || run.gold < cost || !picked) return false;
      Run.train(run, picked);
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

  // ------------------------------------------------------------ mega boss
  Run.MEGA = 'zugzwang';
  Run.startMega = function (run) {
    run.battle = {
      enc: Run.MEGA, tier: 'mega', attempts: 0, bonus: null, ramp: 0, hpMod: 0, atkMod: 0, supplyMod: 0,
      formation: run.formations[Run.MEGA] ? AG.deepCopy(run.formations[Run.MEGA]) : run.lastArmy ? AG.deepCopy(run.lastArmy) : [],
    };
    run.screen = 'setup';
  };

  // ---------------------------------------------------------- Hall of Fame
  // Entries run from the champion (index 0) down. A finished run starts
  // below them all and duels its way up until it loses.
  Run.loadHall = function () {
    try {
      const h = JSON.parse(localStorage.getItem(HALL_KEY) || 'null');
      if (h && Array.isArray(h.entries)) return h;
    } catch (e) { /* fall through */ }
    return { entries: [], runs: 0 };
  };
  Run.saveHall = function (hall) {
    try { localStorage.setItem(HALL_KEY, JSON.stringify(hall)); } catch (e) { /* ignore */ }
  };
  Run.hallEntry = function (run, number) {
    const f = run.finalArmy;
    return {
      id: run.seed + '-' + (run.stats.endedAt || 0), name: 'Run ' + number, date: run.stats.endedAt || Date.now(),
      army: f.army, relics: f.relics, enc: f.enc, heart: !!run.megaWon,
      wins: run.stats.wins, losses: run.stats.losses,
    };
  };
  // Where a challenger lands: below the first entry it lost to (climbing
  // from the bottom), or at the top if it beat them all.
  Run.hallRank = function (count, results) {
    let rank = count;
    for (const won of results) {
      if (!won) break;
      rank--;
    }
    return rank;
  };
  Run.startClimb = function (run) {
    const hall = Run.loadHall();
    const opponents = hall.entries.map((e) => e.id).reverse();
    run.climb = { opponents, results: [], placed: false, rank: null, number: hall.runs + 1 };
    run.screen = 'climb';
    if (!opponents.length) Run.finishClimb(run);
  };
  Run.climbOpponent = function (run) {
    const c = run.climb;
    if (!c || c.placed) return null;
    const hall = Run.loadHall();
    return hall.entries.find((e) => e.id === c.opponents[c.results.length]) || null;
  };
  Run.climbResult = function (run, won) {
    const c = run.climb;
    c.results.push(!!won);
    if (!won || c.results.length >= c.opponents.length) Run.finishClimb(run);
  };
  Run.finishClimb = function (run) {
    const c = run.climb;
    if (c.placed) return;
    const hall = Run.loadHall();
    const rank = Run.hallRank(c.opponents.length, c.results);
    hall.runs = (hall.runs || 0) + 1;
    const entry = Run.hallEntry(run, hall.runs);
    hall.entries.splice(Math.min(rank, hall.entries.length), 0, entry);
    hall.entries = hall.entries.slice(0, Run.HALL_SIZE);
    Run.saveHall(hall);
    c.placed = true;
    c.rank = rank;
    c.entryId = entry.id;
    run.done = true;
  };
  /* The arena for duels: the final boss's board, emptied. The defender's
     army stands mirrored on the far side (see B.create's enemyArmy). The
     challenger moves first on speed ties; if time runs out, the defender
     keeps its place. */
  Run.duelEncounter = function (encId) {
    const base = AG.Encounters[encId] || AG.Encounters.grandmaster;
    const map = base.map.map((r) => r.replace(/[^p.#~ ]/g, '.'));
    return { id: 'hallDuel', act: 0, tier: 'duel', name: 'Hall of Fame duel', theme: 'astral', map, legend: {}, supply: base.supply, flavor: '' };
  };
  // The battle options for a duel between two saved armies.
  Run.duelOpts = function (challenger, defender) {
    return { relics: challenger.relics || [], enemyRelics: defender.relics || [], enemyArmy: defender.army };
  };
  // Play a duel out at once: true if the challenger wins.
  Run.duelWinner = function (challenger, defender) {
    const enc = Run.duelEncounter(challenger.enc);
    const s = AG.B.create(enc, challenger.army, Object.assign({ record: false }, Run.duelOpts(challenger, defender)));
    AG.B.runToEnd(s);
    return s.winner === 0;
  };
})(globalThis.AG = globalThis.AG || {});
