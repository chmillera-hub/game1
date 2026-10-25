// Campaign layer: the branching map, commander level and Supply, loadouts, enemy armies,
// rewards, shops, events and saving. The run object is plain JSON so it can be saved.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const D = AG.Data;
  const { UNITS, RECRUITABLE, ABILITIES, TALENTS, SKILLS, GEAR, ENCHANTS, RELICS, WARBANDS, DIFFICULTIES, ENCOUNTERS, NAMES, COMMAND, LEVEL_COST, SKILL_SLOTS, GEAR_SLOTS, TALENT_SLOTS } = D;
  const E = AG.Engine;

  const SAVE_KEY = 'arena-gauntlet-run-v2';
  const META_KEY = 'arena-gauntlet-meta-v2';
  // Each act: FIGHTS challenge rounds (pick one of three: easy, medium or elite), one event
  // and one merchant somewhere in the middle, then the boss.
  const FIGHTS = 4;
  // How far into its act each round is, for enemy strength (0 = the first fight).
  const ROUND_ROW = [0, 1, 3, 5];
  const BOARD = 9;
  const LEAN_GOLD = 3;
  // Shop prices. Relics cost about twice as much as anything else: a passive that lasts the
  // whole campaign can be extraordinarily strong.
  const RECRUIT_PRICE = { common: 60, uncommon: 90, rare: 128, legendary: 210 };
  const RELIC_PRICE = { common: 160, uncommon: 200, rare: 250, boss: 320, event: 200 };
  const ITEM_PRICE = (cost) => 42 + 21 * cost;
  const SCROLL_PRICE = 120;
  // Resupplying a merchant (a fresh stock): 20 gold, then 10 more each time.
  const REROLL_PRICE = (n) => 20 + 10 * n;
  // Class talents cost a little more than skills of the same Supply cost.
  const TALENT_PRICE = (cost) => 60 + 30 * cost;

  const hasRelic = (run, id) => run.relics.includes(id);
  const unitById = (run, id) => run.roster.find((u) => u.id === id);
  const itemByUid = (run, uid) => run.items.find((i) => i.uid === uid);
  const isTalent = (id) => !!(id && TALENTS[id]);
  const discount = (run, price) => Math.round(price * (hasRelic(run, 'guild_seal') ? 0.75 : 1));
  const isObjectType = (t) => UNITS[t].traits.includes('object') || UNITS[t].traits.includes('summon');
  const isAttacker = (type) => {
    const T = UNITS[type];
    return !!(T.act.dmg || (T.act.fx && T.act.fx.poison) || (T.extra || []).some((a) => a.dmg));
  };

  // ------------------------------------------------------------ commander

  function commanderLevel(run) {
    let lv = 1;
    for (let i = 1; i < COMMAND.length; i++) if (run.xp >= COMMAND[i].xp) lv = i;
    return lv;
  }

  // XP progress toward the next commander level.
  function levelInfo(run) {
    const lv = commanderLevel(run);
    const cur = COMMAND[lv];
    const next = COMMAND[lv + 1] || null;
    return { lv, xp: run.xp, from: cur.xp, to: next ? next.xp : null, max: !next };
  }

  function supplyFor(run) {
    let s = COMMAND[commanderLevel(run)].supply + (run.supplyBonus || 0);
    if (hasRelic(run, 'war_horn')) s += 1;
    if (hasRelic(run, 'legion_banner')) s += 2;
    if (hasRelic(run, 'tyrant_heart')) s += 3;
    if (hasRelic(run, 'crown_command')) s += 2;
    if (hasRelic(run, 'titan_gauntlet')) s -= 1;
    return s;
  }

  // How many units a commander of this level usually fields. Not a limit (Supply is the
  // only one): it sizes enemy armies and is how many units Auto starts from.
  function armySize(run) {
    return COMMAND[commanderLevel(run)].cap;
  }

  function gainXp(run, amount) {
    const from = commanderLevel(run);
    const amt = Math.round(amount * (hasRelic(run, 'drill_manual') ? 1.25 : 1) * (hasRelic(run, 'crown_command') ? 1.25 : 1));
    run.xp += amt;
    run.stats.xp += amt;
    return { amount: amt, from, to: commanderLevel(run) };
  }

  // ------------------------------------------------------------ roster and items

  function pickName(run) {
    const rng = AG.derive(run.seed, 'name:' + run.nextId);
    const free = NAMES.filter((n) => !run.usedNames.includes(n));
    const name = free.length ? rng.pick(free) : rng.pick(NAMES) + ' ' + run.nextId;
    run.usedNames.push(name);
    return name;
  }

  function defaultLoad(type) {
    const T = UNITS[type];
    return { lv: 1, a1: T.abilities ? T.abilities[1][0] : null, a2: T.abilities ? T.abilities[2][0] : null, talents: [], skills: [], gear: [] };
  }

  function addRecruit(run, type, extra) {
    const u = { id: 'u' + run.nextId, type, name: '', enchant: null, kills: 0, battles: 0, load: defaultLoad(type) };
    u.name = pickName(run);
    run.nextId++;
    if (extra) Object.assign(u, extra);
    if (u.enchant && !D.eligible(type, ENCHANTS[u.enchant])) u.enchant = null;
    run.roster.push(u);
    giveTalent(run, u);
    return u;
  }

  // Every new unit brings one random talent of its class. It goes into your pack: units on
  // the bench carry nothing, and you equip it in the War Room once the unit is on the field.
  function giveTalent(run, u) {
    const opts = Object.values(TALENTS)
      .filter((t) => t.cls === u.type)
      .map((t) => [t.id, talentWeight(run, t)]);
    if (!opts.length) return;
    const rng = AG.derive(run.seed, 'talent:' + u.id);
    u.brought = addItem(run, 'talent', rng.weighted(opts)).id;
  }

  // " Mira brings the Poison Arrows talent (in your pack)." for a unit that just joined.
  function talentNote(run, u) {
    return u && u.brought && TALENTS[u.brought] ? ` ${u.name} brings the ${TALENTS[u.brought].name} talent (in your pack).` : '';
  }

  // Back to the bare unit, as it sits on the bench: Level 1, the free picks, nothing slotted
  // (its talents, skills and gear go back to the pack). An enchantment is bound for good.
  function stripLoad(run, r) {
    if (r) r.load = defaultLoad(r.type);
  }

  function addItem(run, kind, id) {
    const it = { uid: 'i' + run.nextItem++, kind, id };
    run.items.push(it);
    return it;
  }

  function itemDef(it) {
    if (!it) return null;
    if (it.kind === 'scroll') return ENCHANTS[it.id];
    return D.itemDef(it.kind, it.id);
  }

  const SLOT_KEY = { skill: 'skills', gear: 'gear', talent: 'talents' };

  // The unit an item is slotted into, if any.
  function itemHolder(run, uid) {
    for (const r of run.roster) if (r.load.skills.includes(uid) || r.load.gear.includes(uid) || r.load.talents.includes(uid)) return r;
    return null;
  }

  function slotsFor(lv) {
    return { skills: SKILL_SLOTS[lv], gear: GEAR_SLOTS[lv], talents: TALENT_SLOTS[lv] };
  }

  // Keep a unit's loadout legal: valid picks, owned and eligible items, slots within its level.
  function normalizeLoad(run, r) {
    const T = UNITS[r.type];
    const L = r.load || (r.load = defaultLoad(r.type));
    L.lv = Math.max(1, Math.min(D.MAX_LEVEL, L.lv || 1));
    if (T.abilities) {
      // Level picks are the free option and the actives; talents go in their own slots.
      for (const tier of [1, 2]) if (!T.abilities[tier].includes(L['a' + tier]) || isTalent(L['a' + tier])) L['a' + tier] = T.abilities[tier][0];
    }
    const sl = slotsFor(L.lv);
    const ok = (uid, kind) => {
      const it = itemByUid(run, uid);
      return it && it.kind === kind && D.eligible(r.type, itemDef(it));
    };
    L.skills = (L.skills || []).filter((uid) => ok(uid, 'skill')).slice(0, sl.skills);
    L.gear = (L.gear || []).filter((uid) => ok(uid, 'gear')).slice(0, sl.gear);
    // One copy of each talent per unit.
    const ids = new Set();
    L.talents = (L.talents || [])
      .filter((uid) => {
        if (!ok(uid, 'talent')) return false;
        const id = itemByUid(run, uid).id;
        if (ids.has(id)) return false;
        ids.add(id);
        return true;
      })
      .slice(0, sl.talents);
    return L;
  }

  function setLevel(run, rid, lv) {
    const r = unitById(run, rid);
    if (!r) return false;
    r.load.lv = Math.max(1, Math.min(D.MAX_LEVEL, lv));
    normalizeLoad(run, r);
    return true;
  }

  function setAbility(run, rid, tier, id) {
    const r = unitById(run, rid);
    const T = r && UNITS[r.type];
    if (!T || !T.abilities || !T.abilities[tier].includes(id) || isTalent(id)) return false;
    r.load['a' + tier] = id;
    return true;
  }

  // Slot an owned item into a unit, taking it off whoever had it.
  function assignItem(run, rid, uid) {
    const r = unitById(run, rid);
    const it = itemByUid(run, uid);
    if (!r || !it || !SLOT_KEY[it.kind]) return false;
    if (!D.eligible(r.type, itemDef(it))) return false;
    const key = SLOT_KEY[it.kind];
    if (r.load[key].includes(uid)) return true;
    if (it.kind === 'talent' && r.load.talents.some((x) => itemByUid(run, x).id === it.id)) return false;
    if (r.load[key].length >= slotsFor(r.load.lv)[key]) return false;
    unassignItem(run, uid);
    r.load[key].push(uid);
    return true;
  }

  function unassignItem(run, uid) {
    for (const r of run.roster) {
      r.load.skills = r.load.skills.filter((x) => x !== uid);
      r.load.gear = r.load.gear.filter((x) => x !== uid);
      r.load.talents = r.load.talents.filter((x) => x !== uid);
    }
  }

  // Items not slotted into anyone.
  function freeItems(run, kind) {
    return run.items.filter((it) => (!kind || it.kind === kind) && (it.kind === 'scroll' || !itemHolder(run, it.uid)));
  }

  function abilityCost(id) {
    return id && ABILITIES[id] ? ABILITIES[id].cost : 0;
  }

  // What fielding this unit costs, line by line.
  function costBreakdown(run, r) {
    normalizeLoad(run, r);
    const T = UNITS[r.type];
    const L = r.load;
    const out = [{ label: T.name + ' (Level 1)', cost: T.cost }];
    if (L.lv > 1) out.push({ label: 'Level ' + L.lv, cost: LEVEL_COST[L.lv] });
    if (L.a1) out.push({ label: ABILITIES[L.a1].name, cost: abilityCost(L.a1) });
    if (L.lv >= 2 && L.a2) out.push({ label: ABILITIES[L.a2].name, cost: abilityCost(L.a2) });
    for (const uid of L.talents.concat(L.skills, L.gear)) {
      const d = itemDef(itemByUid(run, uid));
      if (d) out.push({ label: d.name, cost: d.cost });
    }
    if (r.enchant) out.push({ label: ENCHANTS[r.enchant].name + ' (enchantment)', cost: ENCHANTS[r.enchant].surcharge });
    if (L.lv === 1 && hasRelic(run, 'recruiters_bell') && out.reduce((t, x) => t + x.cost, 0) > 2) out.push({ label: RELICS.recruiters_bell.name, cost: -1 });
    return out;
  }

  function unitCost(run, r) {
    return costBreakdown(run, r).reduce((t, x) => t + x.cost, 0);
  }

  // What a unit costs bare, as it sits on the bench (its enchantment included).
  function bareCost(run, r) {
    const keep = r.load;
    r.load = defaultLoad(r.type);
    const c = unitCost(run, r);
    r.load = keep;
    return c;
  }

  function deployCost(run, rid) {
    const r = unitById(run, rid);
    return r ? unitCost(run, r) : 0;
  }

  function supplyUsed(run, deployment) {
    return deployment.reduce((t, d) => t + deployCost(run, d.rid), 0);
  }

  // An engine unit spec for a roster unit.
  function specFor(run, r) {
    normalizeLoad(run, r);
    const L = r.load;
    return {
      type: r.type,
      level: L.lv,
      a1: L.a1,
      a2: L.a2,
      talents: L.talents.map((uid) => itemByUid(run, uid).id),
      skills: L.skills.map((uid) => itemByUid(run, uid).id),
      gear: L.gear.map((uid) => itemByUid(run, uid).id),
      enchant: r.enchant,
      rid: r.id,
      name: r.name,
    };
  }

  // Battle-ready numbers for a roster unit (or any spec), with relics applied.
  function unitStats(run, rOrSpec, team) {
    const spec = rOrSpec.load ? specFor(run, rOrSpec) : Object.assign({}, rOrSpec);
    const s = { w: 1, h: 1, units: [], byId: {}, occ: [0], nextUid: 1, relics: { P: new Set(run ? run.relics : []), E: new Set() } };
    return E.addUnit(s, Object.assign(spec, { team: team || 'P', x: 0, y: 0 }));
  }

  // Bind an enchantment scroll to a unit, for good.
  function applyScroll(run, uid, rid) {
    const it = itemByUid(run, uid);
    const r = unitById(run, rid);
    if (!it || it.kind !== 'scroll' || !r || r.enchant) return false;
    if (!D.eligible(r.type, ENCHANTS[it.id])) return false;
    r.enchant = it.id;
    run.items = run.items.filter((x) => x.uid !== uid);
    save(run);
    return true;
  }

  // ------------------------------------------------------------ new run

  // ------------------------------------------------------------ the draft
  //
  // A new campaign drafts its army instead of taking a ready-made warband: five units, a
  // relic, a skill and a piece of gear, each one of three. The offers come from the draft's
  // seed (and, for the items, the units chosen), so stepping back shows the same three.

  const DRAFT_STEPS = ['unit', 'unit', 'unit', 'unit', 'unit', 'relic', 'skill', 'gear'];
  const DRAFT_GOLD = 60;
  // Units fit to start a campaign with: the common and uncommon ones, and the Witch.
  const DRAFT_POOL = RECRUITABLE.filter((t) => UNITS[t].rarity === 'common' || UNITS[t].rarity === 'uncommon').concat(['witch']);

  // The three options for a step of the draft, given the picks so far.
  function draftOffer(seed, step, picks) {
    const kind = DRAFT_STEPS[step];
    if (!kind) return null;
    const units = picks.slice(0, 5);
    const rng = AG.derive(seed, 'draft:' + step + (kind === 'skill' || kind === 'gear' ? ':' + units.join(',') : ''));
    const three = (list, weight, ok) => {
      for (let tries = 0; tries < 60; tries++) {
        const out = [];
        while (out.length < 3) {
          const v = rng.weighted(list.filter((x) => !out.includes(x)).map((x) => [x, weight(x)]));
          out.push(v);
        }
        if (!ok || ok(out) || tries === 59) return out;
      }
      return null;
    };
    if (kind === 'unit') {
      // Commons come up most; every offer has at least two units that deal damage and at
      // most one healer or ward. A Cleric, the one unit that heals your army, is offered
      // exactly once: in the first pick, beside two units that deal damage.
      const support = (t) => ['support', 'ward'].includes(UNITS[t].role);
      const weight = (t) => (UNITS[t].rarity === 'common' ? 3 : UNITS[t].rarity === 'uncommon' ? 2 : 1);
      const pool = DRAFT_POOL.filter((t) => t !== 'cleric');
      if (step === 0) {
        const options = three(pool, weight, (o) => o.filter(isAttacker).length === 3 && !o.some(support)).slice(0, 2);
        options.splice(rng.int(3), 0, 'cleric');
        return { kind, options };
      }
      const options = three(pool, weight, (o) => o.filter(isAttacker).length >= 2 && o.filter(support).length <= 1);
      return { kind, options };
    }
    if (kind === 'relic') {
      const options = three(Object.keys(RELICS).filter((id) => RELICS[id].tier === 'common'), () => 1);
      return { kind, options };
    }
    // A skill or gear that at least one of the units chosen can use.
    const table = kind === 'skill' ? SKILLS : GEAR;
    const fit = Object.keys(table).filter((id) => table[id].cost <= 2 && units.some((t) => D.eligible(t, table[id])));
    return { kind, options: three(fit, () => 1) };
  }

  function newRun(opts) {
    opts = opts || {};
    const seed = opts.seed >>> 0 || ((Math.random() * 2 ** 31) >>> 0) + 1;
    // A drafted army, or one of the old ready-made warbands (tests and simulations).
    const draft = opts.draft;
    const wb = draft
      ? { id: 'draft', units: draft.units, relic: draft.relic, items: draft.items, gold: DRAFT_GOLD }
      : WARBANDS.find((w) => w.id === opts.warband) || WARBANDS[0];
    // The old difficulty setting is gone: each round's choice of challenge sets the pace.
    const diff = DIFFICULTIES.find((d) => d.id === opts.difficulty) || DIFFICULTIES[1];
    const run = {
      v: 2,
      talents: 2,
      seed,
      warband: wb.id,
      difficulty: diff.id,
      act: 1,
      gold: wb.gold,
      xp: 0,
      supplyBonus: 0,
      roster: [],
      items: [],
      relics: [wb.relic],
      nextId: 1,
      nextItem: 1,
      usedNames: [],
      plan: null,
      step: 0,
      offer: null,
      boss: null,
      recentEnc: [],
      seenEvents: [],
      lastDeployed: [],
      pending: null,
      over: false,
      won: false,
      stats: { battles: 0, elites: 0, bosses: 0, gold: 0, xp: 0, kills: 0, losses: 0, firstTry: 0, lean: 0 },
    };
    for (const t of wb.units) addRecruit(run, t);
    for (const [kind, id] of wb.items || []) addItem(run, kind, id);
    startAct(run, 1);
    return run;
  }

  // ------------------------------------------------------------ the road

  // The steps of one act: the challenge rounds, with the event and the merchant slotted in
  // after one of the middle rounds (a little random), then the boss.
  function genPlan(run, act) {
    const rng = AG.derive(run.seed, 'plan:' + act);
    const eventAfter = rng.range(1, 2);
    const shopAfter = rng.range(2, 3);
    const plan = [];
    for (let i = 0; i < FIGHTS; i++) {
      plan.push({ kind: 'fight', round: i });
      if (i + 1 === eventAfter) plan.push({ kind: 'event' });
      if (i + 1 === shopAfter) plan.push({ kind: 'shop' });
    }
    plan.push({ kind: 'boss' });
    return plan;
  }

  function startAct(run, act) {
    run.act = act;
    run.plan = genPlan(run, act);
    run.step = 0;
    run.boss = AG.derive(run.seed, 'boss:' + act).pick(D.ACTS[act].bosses);
    run.recentEnc = [];
    enterStep(run);
  }

  function curStep(run) {
    return run.plan ? run.plan[run.step] || null : null;
  }

  // Challenge tiers: what each asks of you and pays.
  const TIERS = {
    easy: { name: 'Easy', kind: 'battle', mult: 0.8, gold: [10, 14], xp: 0.75, spoils: 2 },
    medium: { name: 'Medium', kind: 'battle', mult: 1, gold: [14, 20], xp: 1, spoils: 3 },
    elite: { name: 'Elite', kind: 'elite', mult: 1.85, gold: [30, 38], xp: 1, spoils: 3, relic: true, extraUnits: 1 },
    boss: { name: 'Boss', kind: 'boss', mult: 1, gold: [75, 75], xp: 1, spoils: 3 },
    mega: { name: 'Final challenge', kind: 'boss', mult: 1, gold: [0, 0], xp: 1, spoils: 0 },
  };

  // Arrive at the current step: a round deals three challenges to pick from (the boss and
  // the final challenge, one); the event and the merchant open at once.
  function enterStep(run) {
    const st = curStep(run);
    run.offer = null;
    run.pending = null;
    if (!st) return;
    const tag = run.act + ':' + run.step;
    if (st.kind === 'fight' || st.kind === 'boss' || st.kind === 'mega') {
      const tiers = st.kind === 'fight' ? ['easy', 'medium', 'elite'] : [st.kind];
      const seen = run.recentEnc.slice();
      run.offer = tiers.map((tier) => {
        const T = TIERS[tier];
        const node = { id: 's' + run.step + tier, row: st.kind === 'fight' ? ROUND_ROW[st.round] : 6, kind: T.kind, tier, mult: T.mult, mega: tier === 'mega' };
        const enc = genEncounter(run, node, null, seen);
        seen.push(enc.name);
        return { tier, node, enc, attempts: 0 };
      });
    } else if (st.kind === 'shop') {
      run.pending = { type: 'shop', nodeId: tag, stock: genShop(run, { id: tag }), rerolls: 0 };
    } else if (st.kind === 'event') {
      const rng = AG.derive(run.seed, 'event:' + tag);
      const pool = EVENTS.filter((ev) => !run.seenEvents.includes(ev.id));
      const ev = rng.pick(pool.length ? pool : EVENTS);
      run.seenEvents = run.seenEvents.concat(ev.id);
      run.pending = { type: 'event', nodeId: tag, eventId: ev.id, ctx: ev.prepare ? ev.prepare(run, rng) : {}, result: null };
    }
  }

  // Take on one of the challenges on offer: off to the war room.
  function chooseChallenge(run, index) {
    const o = run.offer && run.offer[index];
    if (!o || run.pending || run.over) return false;
    // Back at a battle you lost or stepped away from: your plan for it is still on the field.
    run.pending = { type: 'battle', nodeId: o.node.id, node: o.node, tier: o.tier, enc: o.enc, attempt: o.attempts, offerIndex: index, lastDep: o.lastDep || null };
    save(run);
    return true;
  }

  // After a defeat: back to the choice of challenges (the one you lost stays on offer).
  function backToChoice(run) {
    const p = run.pending;
    if (!p || p.type !== 'battle') return;
    if (run.offer && run.offer[p.offerIndex]) Object.assign(run.offer[p.offerIndex], { attempts: p.attempt || 0, lastDep: p.lastDep || null });
    run.pending = null;
    save(run);
  }

  // What a challenge pays if won on the first try (bonus goals and loot come on top).
  function challengeReward(run, o) {
    const T = TIERS[o.tier];
    const out = { gold: Math.round((T.gold[0] + T.gold[1]) / 2) + 10, xp: Math.round(battleXp(run, T.kind) * T.xp), spoils: T.spoils, relic: !!T.relic };
    if (o.tier === 'boss') out.bossRelic = run.act < 3;
    return out;
  }

  function bossOf(run) {
    return run.boss || D.ACTS[run.act].bosses[0];
  }

  // XP a victory pays, by battle kind.
  function battleXp(run, kind) {
    const a = run.act - 1;
    if (kind === 'boss') return 25 + 5 * a;
    if (kind === 'elite') return 15 + 3 * a;
    return 8 + 2 * a;
  }

  // ------------------------------------------------------------ encounters

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
  function genTerrain(rng, act, w, h, layout) {
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
      if (layout === 'siege') for (let i = 0; i < 3 * w; i++) t[i] = 0;
      if (layout === 'convoy') for (let y = 3; y <= 5; y++) for (const x of [0, w - 1, w - 2]) t[y * w + x] = 0;
      if (connected(t, w, h)) return t;
    }
    return new Array(w * h).fill(0);
  }

  // Supply cost of an enemy spec, measured like the player's.
  function enemyCost(u) {
    const T = UNITS[u.type];
    if (isObjectType(u.type) || T.traits.includes('structure')) return u.type === 'tower' ? 3 : 0;
    let c = T.cost + LEVEL_COST[u.level || 1] + abilityCost(u.a1) + ((u.level || 1) >= 2 ? abilityCost(u.a2) : 0);
    for (const id of u.skills || []) c += SKILLS[id].cost;
    for (const id of u.gear || []) c += GEAR[id].cost;
    return c;
  }

  function placeEnemies(rng, units, terrain, w, layout, taken) {
    const used = taken || new Set();
    const front = ['tank', 'melee', 'skirmisher', 'monster'];
    for (const u of units) {
      if (u.x != null) {
        used.add(u.x + ',' + u.y);
        continue;
      }
      const T = UNITS[u.type];
      let rows;
      if (layout === 'siege') rows = front.includes(T.role) ? [1, 0] : [0, 1];
      else if (layout === 'convoy') rows = front.includes(T.role) ? [2, 3, 1] : [1, 2, 0];
      else if (T.boss) rows = T.role === 'caster' ? [0, 1] : [1, 0];
      else if (front.includes(T.role) || u.type === 'lightning') rows = [1, 0];
      else rows = [0, 1];
      let xs = [...Array(w).keys()].map((x) => [x, Math.abs(x - (w - 1) / 2) + rng.next() * 3.5]);
      if (layout === 'convoy') xs = xs.map(([x, k]) => [x, Math.abs(x - 6.5) + rng.next() * 2]);
      xs = xs.sort((a, b) => a[1] - b[1]).map((a) => a[0]);
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
      if (!placed) {
        for (let y = 0; y < 4 && !placed; y++)
          for (let x = 0; x < w && !placed; x++) {
            const k = x + ',' + y;
            if (used.has(k) || terrain[y * w + x] !== 0) continue;
            used.add(k);
            u.x = x;
            u.y = y;
            u.facing = 2;
            placed = true;
          }
      }
    }
    return used;
  }

  // Mission goals. The primary goal decides how the battle is won (defeating every enemy always works);
  // bonus goals pay out extra rewards when completed.
  const PRIMARY = {
    normal: [['rout', 30], ['banner', 13], ['prison', 12], ['hold', 12], ['commander', 10], ['survive', 12], ['totems', 12], ['raze', 12]],
    elite: [['rout', 40], ['commander', 24], ['banner', 20], ['raze', 14], ['totems', 12]],
    // The first fights of a run: straightforward goals while you learn the ropes.
    intro: [['rout', 40], ['banner', 18], ['prison', 16], ['hold', 14], ['commander', 12]],
  };

  // Missions with buildings or reinforcements field a smaller army up front.
  const BUDGET_SHARE = { survive: 0.8, raze: 0.6, totems: 0.85 };
  // Totems and spawners grow sturdier act by act.
  const BUILDING_HP = { 1: 0.8, 2: 1, 3: 1.15 };
  // Turns count rounds: an enemy move, then yours. Each side moves one unit a turn.
  // A backstop only: fatigue ends battles long before it.
  const TURN_LIMIT = 250;
  // Fatigue sets in on this turn: each round every fighter loses 1 HP more at the start of
  // its turn, until one side is left.
  const OVERTIME = 30;
  const HOLD_NEED = 4;

  // When buildings send their reinforcements: the first, then one every few turns.
  function spawnRhythm(primary, act, group) {
    if (primary !== 'raze') return { first: 4, every: 8 };
    return { first: 3, every: act >= 2 && group !== 'normal' ? 6 : 7 };
  }
  const TOTEM_BY_ACT = { 1: 'totem', 2: 'hexstone', 3: 'obelisk' };
  // Buildings a mission is about breaking: they scale with the act.
  function isGoalBuilding(type) {
    const T = UNITS[type];
    return T.traits.includes('totem') || T.traits.includes('spawner') || ['gate', 'cart', 'warbanner', 'cage'].includes(type);
  }
  const SPAWNER_BY_ACT = { 1: 'war_tent', 2: 'crypt', 3: 'guardhouse' };

  // Who comes out of each kind of building: the warband's own reserves when they fit the
  // building, or else its usual residents.
  const SPAWN_FIT = {
    den: (T) => T.tags.includes('beast'),
    crypt: (T) => T.tags.includes('undead'),
    guardhouse: (T) => T.tags.includes('human'),
    war_tent: (T) => !T.tags.includes('undead'),
    portal: () => true,
  };
  const SPAWN_DEFAULT = {
    den: { 1: ['wolf', 'warg'], 2: ['wolf', 'spider'], 3: ['warg', 'spider'] },
    crypt: { 1: ['skeleton', 'skelarcher'], 2: ['skeleton', 'skelarcher', 'specter'], 3: ['skeleton', 'specter'] },
    guardhouse: { 1: ['knight', 'archer'], 2: ['knight', 'archer'], 3: ['knight', 'crossbow'] },
    war_tent: { 1: ['orc', 'goblin_archer'], 2: ['orc', 'goblin_archer'], 3: ['orc', 'brute'] },
    portal: { 1: ['wisp', 'specter'], 2: ['wisp', 'specter'], 3: ['specter', 'wisp'] },
  };

  function spawnPool(type, act, pool) {
    const fit = pool.filter((t) => SPAWN_FIT[type](UNITS[t]));
    return fit.length ? fit : SPAWN_DEFAULT[type][act];
  }

  // One reinforcement, a little tougher in later acts.
  function waveSpec(rng, run, pool, group) {
    const type = rng.pick(pool);
    const T = UNITS[type];
    const u = { type, level: run.act >= 2 && group !== 'normal' ? 2 : 1 };
    if (T.abilities) {
      u.a1 = rng.pick(T.abilities[1]);
      u.a2 = T.abilities[2][0];
    }
    return u;
  }

  // A wave worth about `budget` Supply.
  function waveOf(rng, run, pool, budget, group, maxN) {
    const out = [];
    let spent = 0;
    for (let g = 0; g < 16 && out.length < maxN; g++) {
      const u = waveSpec(rng, run, pool, group);
      const c = enemyCost(u);
      if (spent + c > budget + 0.5) {
        if (out.length) break;
        continue;
      }
      out.push(u);
      spent += c;
    }
    return out.length ? out : [waveSpec(rng, run, pool, group)];
  }

  // The unit a bonus goal asks you to field, if there is one. It always fights: the War
  // Room will not let it sit out.
  function bonusUnit(run, enc) {
    const b = (enc.bonus || []).find((x) => x.type === 'muster');
    return b ? unitById(run, b.rid) || null : null;
  }

  // Units that sat out the last battle, for the featured-unit bonus.
  function musterCandidates(run) {
    if (!run.lastDeployed || !run.lastDeployed.length) return [];
    return run.roster.filter((u) => !run.lastDeployed.includes(u.id));
  }

  // Enemy armies grow with the act and the floor, but never outgrow your own Supply by much,
  // so an under-leveled army can always find a winning plan.
  // Later acts lean harder on you, to answer the relics and gear you have piled up.
  const BUDGET_CAP = { normal: 1.0, elite: 1.2, boss: 1.15 };
  // With one unit acting a turn, a bigger army counts for less, so ordinary foes get a
  // little more to spend.
  const BUDGET_SCALE = { normal: 1.2, elite: 1.05, boss: 0.8 };
  // The optional final challenge is meant to break most armies.
  const MEGA_BUDGET = 1.5;

  function enemyBudget(run, node, kind) {
    const diff = DIFFICULTIES.find((d) => d.id === run.difficulty) || DIFFICULTIES[1];
    const group = kind === 'boss' ? 'boss' : kind === 'elite' ? 'elite' : 'normal';
    let b = 12 + (run.act - 1) * 7.5 + node.row;
    if (group === 'elite') b *= 1.2;
    if (group === 'boss') b = 12 + (run.act - 1) * 7 + 8;
    const lean = group === 'boss' ? 0.03 : 0.08;
    b = Math.min(b, supplyFor(run) * (BUDGET_CAP[group] + lean * (run.act - 1)));
    return b * diff.mult * BUDGET_SCALE[group];
  }

  // Give enemy units abilities, levels and (later on) gear, within the budget.
  function outfitEnemies(rng, run, units, budget, group) {
    const cost = () => units.reduce((t, u) => t + enemyCost(u), 0);
    const classUnits = units.filter((u) => UNITS[u.type].abilities);
    for (const u of classUnits) {
      const ab = UNITS[u.type].abilities;
      const pick = rng.pick(ab[1]);
      u.a1 = cost() + abilityCost(pick) <= budget ? pick : ab[1][0];
      u.a2 = ab[2][0];
    }
    const maxLv = run.act === 1 ? (group === 'normal' ? 2 : 3) : 3;
    for (let guard = 0; guard < 24; guard++) {
      const left = budget - cost();
      const opts = units.filter((u) => {
        const T = UNITS[u.type];
        if (T.boss || isObjectType(u.type) || T.traits.includes('structure') || (u.level || 1) >= maxLv) return false;
        const lv = u.level || 1;
        return LEVEL_COST[lv + 1] - LEVEL_COST[lv] <= left;
      });
      if (!opts.length) break;
      const u = rng.pick(opts);
      u.level = (u.level || 1) + 1;
      if (u.level === 2 && UNITS[u.type].abilities) {
        const ab = UNITS[u.type].abilities[2];
        const pick = rng.pick(ab);
        u.a2 = cost() + abilityCost(pick) - abilityCost(u.a2) <= budget ? pick : ab[0];
      }
    }
    // Later acts: leftover budget buys skills and gear.
    if (run.act >= 2) {
      for (let guard = 0; guard < 6; guard++) {
        const left = budget - cost();
        if (left < 1) break;
        const u = rng.pick(units.filter((x) => !isObjectType(x.type) && !UNITS[x.type].traits.includes('structure')));
        if (!u) break;
        const pool = rng.chance(0.5) ? ['skill', SKILLS] : ['gear', GEAR];
        const ids = Object.keys(pool[1]).filter((id) => pool[1][id].cost <= left && D.eligible(u.type, pool[1][id]) && !pool[1][id].mod.active);
        if (!ids.length) continue;
        const key = pool[0] === 'skill' ? 'skills' : 'gear';
        u[key] = u[key] || [];
        if (u[key].length >= (key === 'skills' ? SKILL_SLOTS : GEAR_SLOTS)[u.level || 1]) continue;
        u[key].push(rng.pick(ids));
      }
    }
  }

  // `recent`: encounter names to steer away from (default: the last few you fought).
  function genEncounter(run, node, kindOverride, recent) {
    const kind = kindOverride || node.kind;
    const act = run.act;
    const rng = AG.derive(run.seed, 'enc:' + act + ':' + node.id + ':' + kind);
    const group = kind === 'boss' ? 'boss' : kind === 'elite' ? 'elite' : 'normal';
    // The first two rounds of Act I: no sieges or convoys, and a slightly smaller army.
    const intro = act === 1 && group === 'normal' && node.row <= 1;
    let tpl;
    if (node.mega) tpl = ENCOUNTERS.mega;
    else if (group === 'boss') tpl = ENCOUNTERS[act].boss[bossOf(run)];
    else {
      const avoid = recent || run.recentEnc;
      const pool = ENCOUNTERS[act][group].filter((t) => !intro || !t.layout);
      const fresh = pool.filter((t) => !avoid.includes(t.name));
      tpl = rng.pick(fresh.length ? fresh : pool);
    }
    const layout = tpl.layout || null;
    let primary = group === 'boss' ? 'boss' : layout === 'siege' ? 'gate' : layout === 'convoy' ? 'convoy' : rng.weighted(PRIMARY[intro ? 'intro' : group]);
    const fullBudget = enemyBudget(run, node, kind) * (intro ? (node.row === 0 ? 0.85 : 0.92) : 1) * (node.mult || 1) * (node.mega ? MEGA_BUDGET : 1);
    const budget = fullBudget * (BUDGET_SHARE[primary] || 1);
    const units = tpl.units.map((t, i) => ({ type: t, level: tpl.lv ? tpl.lv[i] : 1 }));
    const cost = () => units.reduce((t, u) => t + enemyCost(u), 0);
    const structures = layout === 'siege' ? (act >= 3 || group === 'elite' ? 2 : 1) * 3 : 0;
    // Enemy armies stay a little above your usual army size; spare Supply buys levels instead.
    const tierExtra = (TIERS[node.tier] && TIERS[node.tier].extraUnits) || 0;
    const maxUnits = node.mega ? 10 : Math.min(9, armySize(run) + (group === 'normal' ? 0 : group === 'elite' ? 1 : 2) + tierExtra);
    while ((cost() + structures > budget + 0.5 && units.length > 2) || units.length > maxUnits) {
      let i = units.length - 1;
      while (i >= 0 && UNITS[units[i].type].boss) i--;
      if (i < 0) break;
      units.splice(i, 1);
    }
    for (let guard = 0; guard < 30; guard++) {
      const addable = tpl.pool.filter((t) => enemyCost({ type: t, level: 1 }) <= budget - structures - cost() + 0.5);
      if (!addable.length || units.length >= maxUnits) break;
      units.push({ type: rng.pick(addable), level: 1 });
    }
    outfitEnemies(rng, run, units, budget - structures, group);
    if (primary === 'commander') {
      let lead = null;
      for (const u of units) if (!lead || enemyCost(u) > enemyCost(lead)) lead = u;
      lead.vip = true;
      lead.level = Math.min(3, (lead.level || 1) + 1);
      if (UNITS[lead.type].abilities && !lead.a2) lead.a2 = UNITS[lead.type].abilities[2][0];
    }
    const terrain = genTerrain(rng, act, BOARD, BOARD, layout);
    const taken = new Set();
    const objects = [];
    const putObj = (type, x, y, extra) => {
      if (terrain[y * BOARD + x] !== 0 || taken.has(x + ',' + y)) return false;
      const T = UNITS[type];
      const sturdy = isGoalBuilding(type) ? { baseHp: Math.round(T.hp * BUILDING_HP[act]) } : {};
      objects.push(Object.assign({ type, level: 1, x, y, facing: 2 }, sturdy, extra || {}));
      taken.add(x + ',' + y);
      return true;
    };
    // Buildings that send reinforcements keep their doorway clear.
    const spawners = [];
    const putSpawner = (type, x, y, goal) => {
      if (terrain[(y + 1) * BOARD + x] !== 0 || taken.has(x + ',' + (y + 1))) return false;
      const key = 'sp' + spawners.length;
      if (!putObj(type, x, y, { key, goal })) return false;
      taken.add(x + ',' + (y + 1));
      spawners.push({ key, x, y });
      return true;
    };
    if (layout === 'siege') {
      for (const x of [1, 2, 3, 5, 6, 7]) putObj('wall', x, 2);
      putObj('gate', 4, 2);
      const towers = structures / 3 === 2 ? [2, 6] : [rng.pick([2, 6])];
      for (const x of towers) putObj('tower', x, 1);
      const houses = act >= 3 || group === 'elite' ? [1, 7] : [rng.pick([1, 7])];
      for (const x of houses) putSpawner('guardhouse', x, 0, false);
    } else if (primary === 'raze') {
      // One building in Act I skirmishes, two everywhere else.
      const type = tpl.spawner || SPAWNER_BY_ACT[act];
      const lanes = act === 1 && group === 'normal' ? [rng.shuffle([3, 4, 5])] : [rng.shuffle([1, 2, 3]), rng.shuffle([5, 6, 7])];
      for (const xs of lanes) {
        let ok = false;
        for (const x of xs) for (const y of rng.shuffle([0, 1])) if (!ok) ok = putSpawner(type, x, y, true);
      }
    } else if (primary === 'totems') {
      for (const xs of [[0, 1, 2], [3, 4, 5], [6, 7, 8]]) {
        let ok = false;
        for (let tries = 0; tries < 20 && !ok; tries++) ok = putObj(TOTEM_BY_ACT[act], rng.pick(xs), rng.range(1, 3));
      }
    } else if (layout === 'convoy') {
      const n = act >= 2 && group !== 'normal' ? 3 : 2;
      const spots = [[8, 3], [8, 5], [7, 4]];
      for (let i = 0; i < n; i++) putObj('cart', spots[i][0], spots[i][1]);
    }
    placeEnemies(rng, units, terrain, BOARD, layout, taken);
    for (const u of units) {
      if (layout === 'convoy' && u.y >= 2) u.facing = rng.pick([2, 3]);
    }
    units.push(...objects);
    if (layout === 'camp') {
      const n = act >= 2 ? 4 : 3;
      let placed = 0;
      for (let tries = 0; tries < 60 && placed < n; tries++) {
        const x = rng.int(BOARD);
        const y = rng.range(0, 3);
        const k = x + ',' + y;
        const near = units.some((u) => Math.abs(u.x - x) + Math.abs(u.y - y) === 1 && !isObjectType(u.type));
        if (!near || terrain[y * BOARD + x] !== 0 || units.some((u) => u.x + ',' + u.y === k)) continue;
        units.push({ type: 'barrel', level: 1, x, y, facing: 2 });
        placed++;
      }
    }
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
      layout,
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
      // Timings made for one unit a turn (see retime).
      tm: 2,
    };
    const addObject = (type, rows, xs) => {
      const t = pickTile(rows, xs) || pickTile([0, 1, 2], [...Array(BOARD).keys()]);
      if (!t) return false;
      units.push({ type, level: 1, x: t[0], y: t[1], facing: 2, baseHp: Math.round(UNITS[type].hp * BUILDING_HP[act]) });
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
      case 'gate':
      case 'convoy':
        enc.objective = 'destroy';
        break;
      case 'totems':
        if (units.some((u) => UNITS[u.type].traits.includes('totem'))) enc.objective = 'destroy';
        break;
      case 'raze':
        if (spawners.length) enc.objective = 'destroy';
        break;
      case 'banner':
        if (addObject('warbanner', [0], [3, 4, 5, 2, 6])) enc.objective = 'destroy';
        break;
      case 'prison':
        if (addObject('cage', [1, 0], rng.chance(0.5) ? [1, 2, 0] : [6, 7, 8])) {
          enc.objective = 'destroy';
          enc.prisoner = { type: rollUnitType(run, rng, 'normal') };
        }
        break;
      case 'hold': {
        const t = pickTile([4, 3, 5], [3, 4, 5, 2, 6]);
        if (t) {
          enc.hold = { x: t[0], y: t[1], need: HOLD_NEED };
          enc.objective = 'hold';
          if (enc.stance === 'defensive') enc.stance = 'balanced';
        }
        break;
      }
      case 'survive':
        enc.objective = 'survive';
        enc.surviveTurns = act === 1 ? 12 : 15;
        enc.stance = 'aggressive';
        break;
    }
    if (enc.objective === 'all') enc.primary = primary = primary === 'boss' ? 'boss' : 'rout';

    // Reinforcements. Buildings send one unit at a time until they fall; survival battles
    // bring whole waves in from the far edge.
    const pool = tpl.pool.filter((t) => !UNITS[t].boss);
    enc.waves = [];
    if (primary === 'raze' || layout === 'siege') {
      const { first, every } = spawnRhythm(primary, act, group);
      for (const sp of spawners) {
        let sPool = spawnPool(units.find((u) => u.key === sp.key).type, act, pool);
        // Act I buildings send light troops.
        if (act === 1) {
          const cheap = (list) => list.filter((t) => UNITS[t].cost <= 2);
          const type = units.find((u) => u.key === sp.key).type;
          sPool = cheap(sPool).length ? cheap(sPool) : cheap(SPAWN_DEFAULT[type][1]).length ? cheap(SPAWN_DEFAULT[type][1]) : sPool;
        }
        for (let k = 0, t = first; k < 4; k++, t += every) enc.waves.push({ turn: t, from: sp.key, units: [waveSpec(rng, run, sPool, group)] });
      }
    } else if (primary === 'survive') {
      const tiles = [];
      for (const y of [0, 1]) for (let x = 0; x < BOARD; x++) if (terrain[y * BOARD + x] === 0) tiles.push([x, y]);
      const turns = act === 1 ? [3, 7] : [2, 6, 10];
      const share = (fullBudget * 2.2 - budget) / turns.length;
      for (const t of turns) enc.waves.push({ turn: t, tiles, units: waveOf(rng, run, pool, share, group, 3) });
    }

    // Barricades: obstacles worth breaking through.
    if (!layout && group !== 'boss' && rng.chance(primary === 'raze' || primary === 'totems' ? 0.75 : 0.25)) {
      const n = rng.range(1, 2);
      for (let k = 0, tries = 0; k < n && tries < 30; tries++) {
        const x = rng.int(BOARD);
        const y = rng.range(3, 5);
        if (!open(x, y) || (enc.hold && enc.hold.x === x && enc.hold.y === y)) continue;
        units.push({ type: 'barricade', level: 1, x, y, facing: 2 });
        used.add(x + ',' + y);
        k++;
      }
    }

    // Bonus: loot on the field, sometimes guarded by specters.
    if (layout !== 'siege' && rng.chance(group === 'boss' ? 0.35 : group === 'elite' ? 0.8 : 0.6)) {
      const lk = group === 'normal' ? rng.weighted([['chest', 50], ['tome', 35], ['relic', 15]]) : rng.weighted([['chest', 20], ['tome', 40], ['relic', 40]]);
      // Guarded treasure sits off to a flank so the main fight can happen elsewhere.
      const xs = lk === 'chest' ? rng.shuffle([0, 1, 2, 6, 7, 8, 3, 5, 4]) : rng.chance(0.5) ? [0, 1, 8, 7] : [8, 7, 0, 1];
      const t = pickTile(lk === 'chest' ? [4, 3, 5] : rng.shuffle([4, 3, 5]), xs);
      if (t && !(enc.hold && enc.hold.x === t[0] && enc.hold.y === t[1])) {
        enc.loot.push({ id: 'loot', kind: lk, x: t[0], y: t[1] });
        used.add(t[0] + ',' + t[1]);
        if (lk !== 'chest') {
          const n = act === 1 ? 1 : lk === 'relic' ? 2 : 1 + (rng.chance(0.4) ? 1 : 0);
          // Guards stay out of your deployment zone.
          const spots = [[0, -1], [-1, 0], [1, 0], [0, 1]].map(([dx, dy]) => [t[0] + dx, t[1] + dy]).filter(([x, y]) => open(x, y) && y < BOARD - DEPLOY_ROWS - 1);
          for (let i = 0; i < n && i < spots.length; i++) {
            const [x, y] = spots[i];
            units.push({ type: 'specter', level: act >= 3 ? 2 : 1, x, y, facing: 0, post: { x: t[0], y: t[1] } });
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
      if (enc.waves.length) opts.push(['blockade', 40]);
      const muster = musterCandidates(run);
      if (muster.length) opts.push(['muster', 50]);
      const c = rng.weighted(opts);
      if (c === 'swift') {
        const foes = units.filter((u) => !isObjectType(u.type) && !UNITS[u.type].traits.includes('structure')).length;
        enc.bonus.push({ type: 'swift', turns: Math.round(3.75 * (4 + Math.ceil(foes / 2) + (enc.objective === 'hold' ? 1 : 0) + (layout === 'siege' ? 2 : 0) + (primary === 'raze' || primary === 'totems' ? 1 : 0))) });
      } else if (c === 'muster') enc.bonus.push({ type: 'muster', rid: rng.pick(muster).id });
      else if (c === 'blockade') enc.bonus.push({ type: 'blockade', n: 2 });
      else enc.bonus.push({ type: 'flawless' });
    }
    if (layout === 'convoy') enc.bonus.push({ type: 'plunder' });
    return enc;
  }

  const LOOT_NAMES = { chest: 'War Chest', tome: 'Lost Tome', relic: 'Relic Cache' };

  // Plain-language goals for the war room and the battle panel.
  function objectiveInfo(run, enc) {
    const typesWith = (trait) => enc.units.filter((u) => UNITS[u.type].traits.includes(trait));
    const totems = typesWith('totem');
    const spawners = typesWith('spawner');
    const tName = totems.length ? UNITS[totems[0].type].name : 'Totem';
    const sName = spawners.length ? UNITS[spawners[0].type].name : 'building';
    // How often each building sends someone: the gap between its first two waves.
    const own = (enc.waves || []).filter((w) => w.from && w.from === (enc.waves || []).find((x) => x.from).from);
    const every = own.length > 1 ? own[1].turn - own[0].turn : 3;
    const P = {
      rout: `Every enemy fighter must fall.${typesWith('structure').length ? ' Buildings do not need to.' : ''}`,
      boss: 'Slay the boss. Its retinue will scatter.',
      banner: 'Burn the War Banner, or defeat every enemy. Enemies near their banner hit 15% harder.',
      prison: 'Break the prison cage, or defeat all the guards. The freed prisoner joins your army.',
      commander: 'Assassinate the enemy Commander (crowned), or defeat them all.',
      hold: `Hold the shrine: start ${enc.hold ? enc.hold.need : HOLD_NEED} of your turns in a row with a unit on it. Or defeat every enemy.`,
      survive: `Survive ${enc.surviveTurns || 12} turns while waves of reinforcements march in from the far edge. Or defeat them all.`,
      gate: `Break the Castle Gate, or defeat the whole garrison.${spawners.length ? ` ${spawners.length > 1 ? 'Guardhouses send' : 'A Guardhouse sends'} a soldier every ${every} turns until destroyed.` : ''} Towers and walls do not need to fall.`,
      totems: `Topple all ${totems.length} ${tName}s, or defeat every enemy. Each heals enemies within 2 tiles every turn.`,
      raze: `Destroy ${spawners.length > 1 ? 'every' : 'the'} ${sName}. ${spawners.length > 1 ? 'Each' : 'It'} sends a fresh unit every ${every} turns until it falls.`,
      convoy: 'Break every Loot Wagon before it escapes off the left edge, or defeat the whole escort.',
    };
    const short = { rout: 'Defeat them all', boss: 'Slay the boss', banner: 'Burn the banner', prison: 'Break the cage', commander: 'Kill the Commander', hold: 'Hold the shrine', survive: `Survive ${enc.surviveTurns || 12} turns`, gate: 'Break the gate', convoy: 'Stop the convoy', totems: `Topple the ${tName}s`, raze: `Raze the ${sName}${spawners.length > 1 ? 's' : ''}` };
    const key = enc.primary || (enc.objective === 'boss' ? 'boss' : 'rout');
    const bonus = (enc.bonus || []).map((b) => {
      switch (b.type) {
        case 'loot':
          return {
            b,
            text: `Take the ${LOOT_NAMES[b.kind]}${b.kind === 'chest' ? '' : ' (guarded by specters)'}: stand a unit on it and spend its action.`,
            reward: b.kind === 'chest' ? `+${25 + 10 * run.act} gold` : b.kind === 'tome' ? 'Choose a skill' : 'A relic',
          };
        case 'swift':
          return { b, text: `Win within ${b.turns} turns.`, reward: `+${15 + 5 * run.act} gold, +3 XP` };
        case 'flawless':
          return { b, text: 'Win without losing a unit.', reward: `+${15 + 5 * run.act} gold, +3 XP` };
        case 'plunder':
          return { b, text: 'Break every wagon (none may escape).', reward: '+20 gold per wagon' };
        case 'blockade':
          return { b, text: `Block ${b.n} reinforcements: stand on their marked tiles as they arrive.`, reward: `+${15 + 5 * run.act} gold, +3 XP` };
        case 'muster': {
          const u = unitById(run, b.rid);
          return { b, text: u ? `${u.name} the ${UNITS[u.type].name}, who sat out the last battle, insists on fighting this one. Win with them in the fight.` : 'A unit that sat out the last battle insists on fighting.', reward: '+6 XP, +20 gold' };
        }
      }
      return { b, text: '', reward: '' };
    });
    return { primary: P[key] || P.rout, short: short[key] || short.rout, key, bonus };
  }

  // Your deployment zone: the three rows nearest you (rocks and water may block a few
  // tiles), one more with the Cartographer's Map.
  const DEPLOY_ROWS = 3;
  function deployRows(run, enc) {
    const rows = [];
    for (let i = DEPLOY_ROWS; i >= 1; i--) rows.push(enc.h - i);
    if (hasRelic(run, 'scout_map')) rows.unshift(enc.h - DEPLOY_ROWS - 1);
    return rows;
  }

  // A deployment tile your unit can stand on: open ground, with no enemy, building, chest
  // or shrine on it.
  function deployOpen(enc, x, y) {
    if (x < 0 || y < 0 || x >= enc.w || y >= enc.h || enc.terrain[y * enc.w + x] !== 0) return false;
    if (enc.units.some((u) => u.x === x && u.y === y)) return false;
    if ((enc.loot || []).some((l) => l.x === x && l.y === y)) return false;
    return !(enc.hold && enc.hold.x === x && enc.hold.y === y);
  }

  // ------------------------------------------------------------ moving on

  // Done with the current step (rewards taken, shop left, event resolved): on to the next.
  // The boss of Act III wins the campaign; the final challenge after it is optional.
  function completeNode(run) {
    const p = run.pending;
    if (!p) return;
    const st = curStep(run);
    run.pending = null;
    if (p.mega) {
      run.superWon = true;
      recordLegend(run);
      endRun(run);
    } else if (st && st.kind === 'boss') {
      if (run.act >= 3) {
        run.won = true;
        recordMeta(run);
        recordLegend(run);
        run.summit = true;
        run.pending = { type: 'summit' };
      } else startAct(run, run.act + 1);
    } else {
      run.step++;
      enterStep(run);
    }
    save(run);
  }

  // The campaign is won: take on the final challenge, or call it a victory.
  function faceFinal(run) {
    if (!run.summit) return false;
    run.plan.push({ kind: 'mega' });
    run.step = run.plan.length - 1;
    enterStep(run);
    save(run);
    return true;
  }

  function endRun(run) {
    run.over = true;
    run.pending = null;
    if (run.superWon) recordMeta(run);
    save(run);
  }

  // ------------------------------------------------------------ battles

  // `enc` defaults to the battle at hand (another, for a preview of a challenge).
  function battleConfig(run, deployment, enc) {
    enc = enc || run.pending.enc;
    const units = [];
    for (const d of deployment) {
      const r = unitById(run, d.rid);
      if (!r) continue;
      units.push(Object.assign(specFor(run, r), { team: 'P', x: d.x, y: d.y, facing: d.facing != null ? d.facing : 0 }));
    }
    for (const e of enc.units)
      units.push({ type: e.type, level: e.level || 1, a1: e.a1, a2: e.a2, skills: e.skills, gear: e.gear, team: 'E', x: e.x, y: e.y, facing: e.facing, vip: e.vip, post: e.post, key: e.key, goal: e.goal, baseHp: e.baseHp });
    return {
      w: enc.w,
      h: enc.h,
      terrain: enc.terrain,
      units,
      relics: { P: run.relics.slice(), E: [] },
      seed: enc.seed + ((run.pending && run.pending.attempt) || 0) * 7919,
      objective: enc.objective,
      hold: enc.hold,
      surviveTurns: enc.surviveTurns,
      loot: enc.loot,
      goals: enc.bonus || [],
      cartExit: 0,
      turnLimit: TURN_LIMIT,
      waves: (enc.waves || []).map((w) => Object.assign({ team: 'E' }, w)),
      // Both sides take their turns in a speed-ordered unit rotation.
      queue: true,
      overtime: OVERTIME,
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

  // Some recruits arrive already bound to an enchantment.
  function rollRecruit(run, rng, kind, exclude) {
    const unit = rollUnitType(run, rng, kind, exclude);
    const chance = kind === 'elite' || kind === 'boss' ? 0.3 : 0.15;
    let enchant = null;
    if (rng.chance(chance)) enchant = rollEnchant(run, rng, unit);
    return { unit, enchant };
  }

  function rollMany(rng, n, fn) {
    const out = [];
    for (let i = 0; i < n * 4 && out.length < n; i++) {
      const v = fn();
      if (v && !out.includes(v)) out.push(v);
    }
    return out;
  }

  // Skills and gear that at least one of your units could use.
  function usable(run, def) {
    return run.roster.some((r) => D.eligible(r.type, def));
  }

  function rollSkill(run, rng, exclude) {
    const ids = Object.keys(SKILLS).filter((id) => !(exclude || []).includes(id) && usable(run, SKILLS[id]));
    return ids.length ? rng.pick(ids) : null;
  }

  function rollGear(run, rng, exclude) {
    const ids = Object.keys(GEAR).filter((id) => !(exclude || []).includes(id) && usable(run, GEAR[id]));
    return ids.length ? rng.pick(ids) : null;
  }

  // How often a talent turns up: the stronger ones (from the Level 2 list) half as often,
  // and ones you already own less often still, so a full build takes some hunting.
  function talentWeight(run, t) {
    return (t.tier === 2 ? 1 : 2) / (1 + 2 * run.items.filter((i) => i.kind === 'talent' && i.id === t.id).length);
  }

  // A talent for a class in your army, never for one you do not field.
  function rollTalent(run, rng, exclude) {
    const types = [...new Set(run.roster.map((r) => r.type))];
    const opts = Object.values(TALENTS)
      .filter((t) => types.includes(t.cls) && !(exclude || []).includes(t.id))
      .map((t) => [t.id, talentWeight(run, t)]);
    return opts.length ? rng.weighted(opts) : null;
  }

  function rollEnchant(run, rng, type, exclude) {
    const ids = Object.keys(ENCHANTS).filter((id) => !(exclude || []).includes(id) && (type ? D.eligible(type, ENCHANTS[id]) : true));
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
  }

  function genSpoils(run, rng, kind) {
    const out = [];
    const r1 = rollRecruit(run, rng, kind);
    out.push({ type: 'recruit', unit: r1.unit, enchant: r1.enchant });
    const firstItem = rng.chance(0.5) ? 'skill' : 'gear';
    const id1 = firstItem === 'skill' ? rollSkill(run, rng) : rollGear(run, rng);
    if (id1) out.push({ type: firstItem, id: id1 });
    const scrollW = kind === 'normal' || kind === 'battle' ? 10 : 30;
    for (let guard = 0; guard < 8 && out.length < 3; guard++) {
      const talentW = kind === 'normal' || kind === 'battle' ? 14 : 28;
      const k = rng.weighted([['recruit', 30], ['skill', 22], ['gear', 22], ['talent', talentW], ['scroll', scrollW]]);
      if (k === 'recruit') {
        const r = rollRecruit(run, rng, kind, [r1.unit]);
        out.push({ type: 'recruit', unit: r.unit, enchant: r.enchant });
      } else if (k === 'skill' || k === 'gear' || k === 'talent') {
        const ex = out.map((o) => o.id);
        const id = k === 'skill' ? rollSkill(run, rng, ex) : k === 'gear' ? rollGear(run, rng, ex) : rollTalent(run, rng, ex);
        if (id) out.push({ type: k, id });
      } else {
        const id = rollEnchant(run, rng);
        if (id) out.push({ type: 'scroll', id });
      }
    }
    while (out.length < 3) out.push({ type: 'gold', amount: 30 });
    return out;
  }

  // Apply the outcome of a finished battle. `s` is the engine state.
  // Whether a won battle met one bonus goal.
  function bonusDone(s, deployment, b) {
    if (b.type === 'loot') return s.loot.some((l) => l.id === b.lootId && l.taken);
    if (b.type === 'swift') return s.turn <= b.turns;
    if (b.type === 'flawless') return !s.units.some((u) => u.team === 'P' && !u.nonCombat && !u.alive);
    if (b.type === 'muster') return deployment.some((d) => d.rid === b.rid);
    if (b.type === 'blockade') return (s.stats.blocked || 0) >= b.n;
    if (b.type === 'plunder') {
      const carts = s.units.filter((u) => u.type === 'cart');
      return carts.length > 0 && carts.every((u) => !u.alive && !u.escaped);
    }
    return false;
  }

  // Every bonus goal of the battle in progress, met or not, before the rewards are paid.
  function goalResults(run, s, deployment) {
    return objectiveInfo(run, run.pending.enc).bonus.map((it) => ({ text: it.text, reward: it.reward, done: bonusDone(s, deployment, it.b) }));
  }

  // A copy of the run to come back to: a won battle with goals missed can be fought again,
  // setting its victory and rewards aside.
  function snapshot(run) {
    return JSON.stringify(run);
  }

  function restore(copy) {
    const run = JSON.parse(copy);
    save(run);
    return run;
  }

  function finishBattle(run, s, deployment) {
    const p = run.pending;
    const node = p.node || { id: p.nodeId, row: 0 };
    const kind = p.enc.kind;
    const tier = TIERS[p.tier] || TIERS[kind === 'boss' ? 'boss' : kind === 'elite' ? 'elite' : 'medium'];
    if (s.winner !== 'P') {
      p.attempt = (p.attempt || 0) + 1;
      run.stats.losses++;
      save(run);
      return { won: false, attempt: p.attempt };
    }
    const rng = AG.derive(run.seed, 'loot:' + run.act + ':' + node.id + ':' + (p.attempt || 0));
    let gold = rng.range(tier.gold[0], tier.gold[1]);
    if (hasRelic(run, 'coin_purse')) gold += 12;
    if (hasRelic(run, 'kings_ransom')) gold += 20;
    const firstTry = !p.attempt;
    if (firstTry) {
      gold += 10;
      run.stats.firstTry++;
    }
    const supply = supplyFor(run);
    const used = supplyUsed(run, deployment);
    const unspent = Math.max(0, supply - used);
    const lean = unspent * LEAN_GOLD * (hasRelic(run, 'alchemist_stone') ? 3 : 1);
    const midas = s.stats.gold || 0;
    let xp = Math.round(battleXp(run, kind) * tier.xp) + (firstTry ? 2 : 0);
    run.gold += gold + lean + midas;
    run.stats.gold += gold + lean + midas;
    run.stats.lean += lean;
    run.stats.battles++;
    if (kind === 'elite') run.stats.elites++;
    if (kind === 'boss') run.stats.bosses++;

    const deployedIds = new Set(deployment.map((d) => d.rid));
    const fallen = [];
    for (const r of run.roster) {
      if (!deployedIds.has(r.id)) continue;
      const bu = s.units.find((u) => u.rid === r.id);
      r.battles++;
      if (bu) {
        r.kills += bu.kills;
        run.stats.kills += bu.kills;
        if (!bu.alive) fallen.push(r.name);
      }
    }
    run.recentEnc = run.recentEnc.concat(p.enc.name).slice(-3);
    run.lastDeployed = deployment.map((d) => d.rid);
    // The army that beats the Act III boss (or the final challenge) is the one the Hall of
    // Fame remembers: who fought, kitted out how, and where they stood.
    if (kind === 'boss' && run.act >= 3) {
      run.finalArmy = deployment.map((d) => {
        const spec = specFor(run, unitById(run, d.rid));
        delete spec.rid;
        return { spec, x: d.x, y: d.y, facing: d.facing != null ? d.facing : 0 };
      });
    }
    // Easy challenges offer two spoils, the rest three; the final challenge pays in glory.
    const spoils = tier.spoils ? genSpoils(run, rng, kind).slice(0, tier.spoils) : [];
    const reward = {
      type: 'reward', nodeId: p.nodeId, kind, tier: p.tier, gold, lean, unspent, midas, firstTry, fallen,
      spoils, spoilTaken: !spoils.length, objectives: [], mega: !!node.mega,
    };
    const info = objectiveInfo(run, p.enc);
    for (const it of info.bonus) {
      const b = it.b;
      const done = bonusDone(s, deployment, b);
      let got = '';
      if (done) {
        if (b.type === 'loot' && b.kind === 'chest') {
          const g = 25 + 10 * run.act;
          run.gold += g;
          run.stats.gold += g;
          got = `+${g} gold`;
        } else if (b.type === 'loot' && b.kind === 'tome') {
          reward.tome = rollMany(rng, 3, () => rollSkill(run, rng));
          reward.tomeTaken = reward.tome.length === 0;
          got = 'choose a skill below';
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
        } else if (b.type === 'swift' || b.type === 'flawless' || b.type === 'blockade') {
          const g = 15 + 5 * run.act;
          run.gold += g;
          run.stats.gold += g;
          xp += 3;
          got = `+${g} gold, +3 XP`;
        } else if (b.type === 'muster') {
          run.gold += 20;
          run.stats.gold += 20;
          xp += 6;
          got = '+6 XP, +20 gold';
        } else if (b.type === 'plunder') {
          const g = 20 * s.units.filter((u) => u.type === 'cart').length;
          run.gold += g;
          run.stats.gold += g;
          got = `+${g} gold`;
        }
      }
      reward.objectives.push({ text: it.text, done, got });
    }
    const lv = gainXp(run, xp);
    reward.xp = lv.amount;
    reward.lvFrom = lv.from;
    reward.lvTo = lv.to;
    if (p.enc.prisoner) reward.prisoner = addRecruit(run, p.enc.prisoner.type).id;
    if (tier.relic) {
      const id = pickRelic(run, rng, [randomRelicTier(rng, run.act)]) || pickRelic(run, rng, ['common', 'uncommon', 'rare']);
      if (id) {
        gainRelic(run, id);
        reward.relicGained = id;
      }
    }
    if (kind === 'boss' && !node.mega && run.act < 3) {
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
    return { won: true, gold, lean, xp: reward.xp, lvFrom: reward.lvFrom, lvTo: reward.lvTo };
  }

  function takeSpoil(run, index) {
    const p = run.pending;
    if (!p || p.type !== 'reward' || p.spoilTaken) return false;
    const sp = p.spoils[index];
    if (!sp) return false;
    if (sp.type === 'recruit') addRecruit(run, sp.unit, { enchant: sp.enchant || null });
    else if (sp.type === 'skill' || sp.type === 'gear' || sp.type === 'talent' || sp.type === 'scroll') addItem(run, sp.type, sp.id);
    else if (sp.type === 'gold') run.gold += sp.amount;
    p.spoilTaken = true;
    p.spoilPick = index;
    save(run);
    return true;
  }

  function skipSpoils(run) {
    const p = run.pending;
    if (!p || p.type !== 'reward' || p.spoilTaken) return;
    run.gold += 10;
    p.spoilTaken = true;
    save(run);
  }

  function takeTome(run, index) {
    const p = run.pending;
    if (!p || p.type !== 'reward' || !p.tome || p.tomeTaken) return false;
    const id = p.tome[index];
    if (!id) return false;
    addItem(run, 'skill', id);
    p.tomeTaken = true;
    p.tomePick = index;
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

  function takeBossRelic(run, id) {
    const p = run.pending;
    if (!p || !p.bossRelics || p.bossRelicTaken || !p.bossRelics.includes(id)) return false;
    gainRelic(run, id);
    p.bossRelicTaken = true;
    p.bossPick = id;
    save(run);
    return true;
  }

  // ------------------------------------------------------------ shop, rest, treasure

  // One of each kind of thing, at most eight: a recruit, a talent, a skill, gear, an
  // enchantment scroll, a relic, and the two services.
  // Six things at most: a recruit, a talent, a skill, gear and a relic, plus one of an
  // enchantment scroll, a Supply Cache or a War Manual.
  function genShop(run, node) {
    const rng = AG.derive(run.seed, 'shop:' + run.act + ':' + node.id);
    const items = [];
    const extra = rng.pick(['scroll', 'supply', 'manual']);
    const r = rollRecruit(run, rng, 'normal');
    const price = RECRUIT_PRICE[UNITS[r.unit].rarity] + (r.enchant ? 40 : 0);
    items.push({ kind: 'recruit', unit: r.unit, enchant: r.enchant, price: discount(run, price), sold: false });
    const talent = rollTalent(run, rng);
    if (talent) items.push({ kind: 'talent', id: talent, price: discount(run, TALENT_PRICE(TALENTS[talent].cost)), sold: false });
    const skill = rollSkill(run, rng);
    if (skill) items.push({ kind: 'skill', id: skill, price: discount(run, ITEM_PRICE(SKILLS[skill].cost)), sold: false });
    const gear = rollGear(run, rng);
    if (gear) items.push({ kind: 'gear', id: gear, price: discount(run, ITEM_PRICE(GEAR[gear].cost)), sold: false });
    const relic = pickRelic(run, rng, [randomRelicTier(rng, run.act)]) || pickRelic(run, rng, ['common', 'uncommon', 'rare']);
    if (relic) items.push({ kind: 'relic', relic, price: discount(run, RELIC_PRICE[RELICS[relic].tier]), sold: false });
    const sc = extra === 'scroll' && rollEnchant(run, rng);
    if (sc) items.push({ kind: 'scroll', id: sc, price: discount(run, SCROLL_PRICE), sold: false });
    else if (extra === 'manual') items.push({ kind: 'manual', price: discount(run, 68), sold: false });
    else items.push({ kind: 'supply', price: discount(run, 105 + 30 * (run.supplyBonus || 0)), sold: false });
    return items;
  }

  function rerollPrice(run) {
    const p = run.pending;
    return REROLL_PRICE((p && p.rerolls) || 0);
  }

  // Resupply: the merchant brings out a whole new stock.
  function rerollShop(run) {
    const p = run.pending;
    if (!p || p.type !== 'shop') return false;
    const price = rerollPrice(run);
    if (run.gold < price) return false;
    run.gold -= price;
    p.rerolls = (p.rerolls || 0) + 1;
    p.stock = genShop(run, { id: p.nodeId + ':r' + p.rerolls });
    save(run);
    return true;
  }

  function canBuy(run, item) {
    if (item.sold || run.gold < item.price) return false;
    return true;
  }

  function buy(run, index) {
    const p = run.pending;
    if (!p || p.type !== 'shop') return false;
    const item = p.stock[index];
    if (!item || !canBuy(run, item)) return false;
    switch (item.kind) {
      case 'recruit':
        addRecruit(run, item.unit, { enchant: item.enchant || null });
        break;
      case 'skill':
      case 'gear':
      case 'talent':
      case 'scroll':
        addItem(run, item.kind, item.id);
        break;
      case 'relic':
        gainRelic(run, item.relic);
        break;
      case 'supply':
        run.supplyBonus = (run.supplyBonus || 0) + 1;
        break;
      case 'manual':
        item.levels = gainXp(run, 10);
        break;
    }
    run.gold -= item.price;
    item.sold = true;
    save(run);
    return true;
  }

  // ------------------------------------------------------------ events

  const uname = (t) => UNITS[t].name;

  const EVENTS = [
    {
      id: 'sellsword',
      title: "The Sellsword's Offer",
      text: 'A scarred mercenary sits by the road, honing a blade that hums with old magic. "Coin first, loyalty after."',
      prepare: (run, rng) => {
        const unit = rollUnitType(run, rng, 'elite');
        return { unit, enchant: rollEnchant(run, rng, unit) };
      },
      choices: (run, c) => [
        { id: 'hire', label: 'Hire (65 gold)', detail: `An enchanted ${uname(c.unit)} joins, bound with ${ENCHANTS[c.enchant].name}: ${ENCHANTS[c.enchant].desc}`, enabled: run.gold >= 65 },
        { id: 'haggle', label: 'Haggle (30 gold)', detail: `Even odds: a plain ${uname(c.unit)} joins, or the coin is simply gone.`, enabled: run.gold >= 30 },
        { id: 'leave', label: 'Move on', detail: 'Keep your gold.' },
      ],
      resolve: (run, c, choice, rid, rng) => {
        if (choice === 'hire') {
          run.gold -= 65;
          const u = addRecruit(run, c.unit, { enchant: c.enchant });
          return `${u.name} the ${uname(u.type)} counts the coin twice, then falls in line.${talentNote(run, u)}`;
        }
        if (choice === 'haggle') {
          run.gold -= 30;
          if (rng.chance(0.5)) {
            const u = addRecruit(run, c.unit);
            return `${u.name} the ${uname(u.type)} shrugs, takes the coin and joins you.${talentNote(run, u)}`;
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
      prepare: (run, rng) => ({ skills: rollMany(rng, 2, () => rollSkill(run, rng)), free: rollSkill(run, rng) }),
      choices: (run, c) => [
        { id: 'pray', label: 'Pray', detail: c.free ? `Receive a random skill.` : 'The saint is silent.', enabled: !!c.free },
        ...c.skills.map((id) => ({ id: 'offer:' + id, label: `Offer 35 gold: ${SKILLS[id].name}`, detail: `${SKILLS[id].desc} (Skill, ${SKILLS[id].cost} Supply)`, enabled: run.gold >= 35 })),
        { id: 'leave', label: 'Leave', detail: 'Let the candles burn.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'pray') {
          addItem(run, 'skill', c.free);
          return `A warm light settles on your camp. You learn ${SKILLS[c.free].name}.`;
        }
        if (choice.startsWith('offer:')) {
          const id = choice.slice(6);
          run.gold -= 35;
          addItem(run, 'skill', id);
          return `You kneel and rise with ${SKILLS[id].name}.`;
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
      title: 'A Deserter in the Brush',
      text: 'A soldier in a torn tabard limps out of the brush, hands raised. "I am done with my old lord. Take me in, or take my purse. Just let me live."',
      prepare: (run, rng) => ({ unit: rng.pick(RECRUITABLE.filter((t) => UNITS[t].rarity === 'common')) }),
      choices: (run, c) => [
        { id: 'take', label: 'Take them in', detail: `A ${uname(c.unit)} joins your army.` },
        { id: 'rob', label: 'Take the purse', detail: 'Gain 35 gold.' },
        { id: 'leave', label: 'Let them go', detail: 'Nothing gained, nothing lost.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'take') {
          const u = addRecruit(run, c.unit);
          return `${u.name} the ${uname(u.type)} swears a new oath.${talentNote(run, u)}`;
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
      text: 'Behind a rusted gate lies a single blade, still wet with something dark. It whispers promises of victory. The racks around it hold older steel.',
      prepare: (run, rng) => ({ gear: rollGear(run, rng) }),
      choices: (run, c) => [
        { id: 'take', label: 'Take the blade', detail: RELICS.cursed_blade.desc, enabled: !hasRelic(run, 'cursed_blade') },
        { id: 'loot', label: 'Search the racks', detail: c.gear ? `Find a ${GEAR[c.gear].name}: ${GEAR[c.gear].desc}` : 'Gain 30 gold of old iron.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'take') {
          gainRelic(run, 'cursed_blade');
          return 'The Bloodthirst Blade is yours. Your soldiers fight with a terrible hunger.';
        }
        if (c.gear) {
          addItem(run, 'gear', c.gear);
          return `You pull a ${GEAR[c.gear].name} from the racks.`;
        }
        run.gold += 30;
        return 'You haul away the old iron and sell it for 30 gold.';
      },
    },
    {
      id: 'fountain',
      title: 'Fountain of Renewal',
      text: 'Clear water bubbles from a marble basin carved with sleeping lions. Your soldiers gather around it in silence.',
      choices: () => [
        { id: 'drink', label: 'Drink and reflect', detail: 'Gain 10 XP.' },
        { id: 'fill', label: 'Fill flasks to sell', detail: 'Gain 40 gold.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'drink') {
          gainXp(run, 10);
          return 'Clear water, clear minds. Your command grows sharper.';
        }
        run.gold += 40;
        return 'Pilgrims pay well for the water. You gain 40 gold.';
      },
    },
    {
      id: 'library',
      title: "The Quartermaster's Ledgers",
      text: 'A ruined keep still holds the ledgers of a long-dead quartermaster: depots, wagon routes, hidden caches.',
      choices: () => [
        { id: 'study', label: 'Study the ledgers', detail: '+1 Supply in every battle for the rest of the run.' },
        { id: 'sell', label: 'Sell the books', detail: 'Gain 60 gold.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'study') {
          run.supplyBonus = (run.supplyBonus || 0) + 1;
          return 'You find caches no one else remembers. +1 Supply.';
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
        { id: 'accept', label: 'Accept the challenge', detail: 'Fight an elite battle. Victory earns a relic and extra XP.' },
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
      text: 'A cart rattles with bubbling flasks. "Transformation, my friend! Or perhaps something for the road?"',
      choices: (run) => [
        {
          id: 'transmute',
          label: 'Transmute (50 gold)',
          detail: 'Choose a common or uncommon unit. It becomes a random unit of a higher rarity.',
          enabled: run.gold >= 50 && run.roster.some((u) => ['common', 'uncommon'].includes(UNITS[u.type].rarity)),
          pick: { filter: 'transmute' },
        },
        { id: 'flasks', label: 'Buy flasks (30 gold)', detail: 'Gain a Fire Flask and a Healing Draught.', enabled: run.gold >= 30 },
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
          u.load = defaultLoad(t);
          if (u.enchant && !D.eligible(t, ENCHANTS[u.enchant])) u.enchant = null;
          run.gold -= 50;
          return `Smoke billows. ${u.name} the ${old} steps out as a ${uname(t)}.`;
        }
        if (choice === 'flasks') {
          run.gold -= 30;
          addItem(run, 'gear', 'fire_flask');
          addItem(run, 'gear', 'healing_draught');
          return 'Two flasks, one red and one gold. Handle with care.';
        }
        return 'The alchemist shrugs and rattles away.';
      },
    },
    {
      id: 'forge',
      title: 'The Old Forge',
      text: 'A smith with arms like oak branches looks up from the anvil. "Bring me coin, and I will make you something worth carrying."',
      prepare: (run, rng) => ({ gear: rollMany(rng, 3, () => rollGear(run, rng)) }),
      choices: (run, c) => [
        ...c.gear.map((id) => ({ id: 'forge:' + id, label: `Commission (40 gold): ${GEAR[id].name}`, detail: `${GEAR[id].desc} (Gear, ${GEAR[id].cost} Supply)`, enabled: run.gold >= 40 })),
        { id: 'leave', label: 'Move on', detail: 'The forge fire dims behind you.' },
      ],
      resolve: (run, c, choice) => {
        if (choice.startsWith('forge:')) {
          const id = choice.slice(6);
          run.gold -= 40;
          addItem(run, 'gear', id);
          return `The smith hands you a ${GEAR[id].name}, still warm.`;
        }
        return 'You leave the smith to the anvil.';
      },
    },
    {
      id: 'battlefield',
      title: 'The Haunted Battlefield',
      text: 'Broken spears and rusted helms cover a silent field. Something glints among the bones, and something else watches.',
      prepare: (run, rng) => ({ roll: rng.next(), relic: pickRelic(run, rng, ['common', 'uncommon']) }),
      choices: () => [
        { id: 'search', label: 'Search the fallen', detail: 'Maybe a relic. Maybe a curse.' },
        { id: 'raise', label: 'Raise a fallen archer', detail: 'A Skeleton Archer rises to serve you.' },
        { id: 'leave', label: 'Leave the dead in peace', detail: 'Walk on quietly.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'raise') {
          const u = addRecruit(run, 'skelarcher');
          return `${u.name}, long dead, takes up a bow for you.${talentNote(run, u)}`;
        }
        if (choice !== 'search') return 'You leave the field to its ghosts.';
        if (c.roll < 0.6 && c.relic && !run.relics.includes(c.relic)) {
          gainRelic(run, c.relic);
          return `Under a shattered shield you find the ${RELICS[c.relic].name}.`;
        }
        const lost = Math.min(run.gold, 25);
        run.gold -= lost;
        return `A cold wind tears through your camp and scatters your purse. You lose ${lost} gold.`;
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
        ...c.units.map((t) => ({ id: 'take:' + t, label: 'Recruit the ' + uname(t), detail: `A ${uname(t)} joins for free.` })),
        { id: 'leave', label: 'Wish them luck', detail: 'Ride on.' },
      ],
      resolve: (run, c, choice) => {
        if (choice.startsWith('take:')) {
          const u = addRecruit(run, choice.slice(5));
          return `${u.name} picks up a weapon and joins your column.${talentNote(run, u)}`;
        }
        return 'The villagers watch you go.';
      },
    },
    {
      id: 'tower',
      title: "The Enchanter's Tower",
      text: 'A crooked tower leans over the road, its windows flickering with colored light. An old enchanter peers down. "Binding magic, captain. Permanent. Choose wisely."',
      prepare: (run, rng) => ({ scrolls: rollMany(rng, 2, () => rollEnchant(run, rng)) }),
      choices: (run, c) => [
        ...c.scrolls.map((id) => ({ id: 'buy:' + id, label: `Buy a scroll (55 gold): ${ENCHANTS[id].name}`, detail: `${ENCHANTS[id].desc} Bind it to a unit from the Army screen. +${ENCHANTS[id].surcharge} Supply to field that unit.`, enabled: run.gold >= 55 })),
        { id: 'steal', label: 'Steal a scroll', detail: 'Even odds: a free scroll, or the enchanter catches you and fines you 40 gold.' },
        { id: 'leave', label: 'Leave', detail: 'Some magic is best left alone.' },
      ],
      resolve: (run, c, choice, rid, rng) => {
        if (choice.startsWith('buy:')) {
          const id = choice.slice(4);
          run.gold -= 55;
          addItem(run, 'scroll', id);
          return `The scroll of ${ENCHANTS[id].name} hums in your hands.`;
        }
        if (choice === 'steal') {
          if (rng.chance(0.5)) {
            const id = rng.pick(c.scrolls);
            addItem(run, 'scroll', id);
            return `You slip away with the scroll of ${ENCHANTS[id].name}.`;
          }
          const lost = Math.min(run.gold, 40);
          run.gold -= lost;
          return `A glowing hand seizes your collar. You pay ${lost} gold to be let go.`;
        }
        return 'The tower lights wink out behind you.';
      },
    },
    {
      id: 'lodge',
      title: "Veterans' Lodge",
      text: 'Old soldiers drink by a long fire. "We drilled the king\'s own guard once," says one. "Pay us and we will teach your sergeants to run a bigger line."',
      choices: (run) => [
        { id: 'train', label: 'Pay for drills (90 gold)', detail: '+1 Supply in every battle for the rest of the run.', enabled: run.gold >= 90 },
        { id: 'stories', label: 'Listen to their stories', detail: 'Gain 8 XP.' },
        { id: 'leave', label: 'Leave', detail: 'March on.' },
      ],
      resolve: (run, c, choice) => {
        if (choice === 'train') {
          run.gold -= 90;
          run.supplyBonus = (run.supplyBonus || 0) + 1;
          return 'Your sergeants learn to hold a wider line. +1 Supply in every battle.';
        }
        if (choice === 'stories') {
          gainXp(run, 8);
          return 'Old wars, hard lessons. You take notes.';
        }
        return 'The veterans raise their cups as you go.';
      },
    },
    {
      id: 'caravan',
      title: 'Merchant Caravan',
      text: 'Wagons circle around a campfire. A merchant in a fur hat sizes up your army and your purse.',
      prepare: (run, rng) => ({ gear: rollGear(run, rng), skill: rollSkill(run, rng) }),
      choices: (run, c) => [
        c.gear ? { id: 'gear', label: `Buy ${GEAR[c.gear].name} (35 gold)`, detail: GEAR[c.gear].desc, enabled: run.gold >= 35 } : null,
        c.skill ? { id: 'skill', label: `Buy a manual of ${SKILLS[c.skill].name} (35 gold)`, detail: SKILLS[c.skill].desc, enabled: run.gold >= 35 } : null,
        { id: 'sell', label: 'Sell spare gear', detail: 'Gain 25 gold.' },
      ].filter(Boolean),
      resolve: (run, c, choice) => {
        if (choice === 'gear') {
          run.gold -= 35;
          addItem(run, 'gear', c.gear);
          return `The ${GEAR[c.gear].name} is yours.`;
        }
        if (choice === 'skill') {
          run.gold -= 35;
          addItem(run, 'skill', c.skill);
          return `You learn ${SKILLS[c.skill].name} from a dog-eared manual.`;
        }
        run.gold += 25;
        return 'The merchant pays 25 gold for your spare gear.';
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
      const node = { id: p.nodeId, row: 3, kind: out.battle };
      p.result = out.text;
      run.pending = { type: 'battle', nodeId: p.nodeId, node, enc: genEncounter(run, node, out.battle), attempt: 0, fromEvent: true };
      save(run);
      return out.text;
    }
    p.result = out;
    save(run);
    return out;
  }

  // ------------------------------------------------------------ deployment

  const FRONT_ROLES = ['tank', 'melee', 'skirmisher', 'monster'];

  function isFront(type) {
    return FRONT_ROLES.includes(UNITS[type].role) || type === 'lightning';
  }

  // Free deploy tiles nearest the center, front row first or back row first.
  // Free deployment tiles for a unit, best first. Auto keeps to the back two rows (front
  // liners ahead, the rest behind) and uses the rows further forward only when those fill.
  function deploySlots(run, enc, front, taken) {
    const back = [enc.h - 2, enc.h - 1];
    if (!front) back.reverse();
    const order = back.concat(deployRows(run, enc).filter((y) => !back.includes(y)).sort((a, b) => b - a));
    const out = [];
    for (const y of order) {
      const xs = [...Array(enc.w).keys()].sort((a, b) => Math.abs(a - (enc.w - 1) / 2) - Math.abs(b - (enc.w - 1) / 2) || a - b);
      for (const x of xs) if (deployOpen(enc, x, y) && !taken.has(x + ',' + y)) out.push({ x, y });
    }
    return out;
  }

  // The army the War Room opens with: your plan for this battle if you have one (you lost
  // it or stepped away); for a new battle, the army you last fought with, kit and all. A
  // unit whose old tile is blocked on this field goes to the nearest open blue tile. A
  // quest's unit joins on top of that, so you choose what to change.
  function startingPlan(run, enc) {
    const p = run.pending || {};
    const rows = deployRows(run, enc);
    const dep = [];
    const taken = new Set();
    const free = (x, y) => rows.includes(y) && deployOpen(enc, x, y) && !taken.has(x + ',' + y);
    const put = (rid, x, y, facing) => {
      dep.push({ rid, x, y, facing });
      taken.add(x + ',' + y);
    };
    for (const d of p.lastDep || run.lastPlan || []) {
      if (!unitById(run, d.rid) || dep.some((o) => o.rid === d.rid)) continue;
      const facing = d.facing != null ? d.facing : 0;
      if (free(d.x, d.y)) {
        put(d.rid, d.x, d.y, facing);
        continue;
      }
      let best = null;
      for (const y of rows)
        for (let x = 0; x < enc.w; x++) {
          if (!free(x, y)) continue;
          const dist = Math.abs(x - d.x) + Math.abs(y - d.y);
          if (!best || dist < best.dist) best = { x, y, dist };
        }
      if (best) put(d.rid, best.x, best.y, facing);
    }
    const star = bonusUnit(run, enc);
    if (star && !dep.some((d) => d.rid === star.id)) {
      const slot = deploySlots(run, enc, isFront(star.type), taken)[0];
      if (slot) put(star.id, slot.x, slot.y, 0);
    }
    return dep;
  }

  // How well a unit type answers this enemy army: magic against armor, steel against wards.
  // Buildings in this battle worth bringing siege damage for: goals, spawners and gates.
  function siegeTargets(enc) {
    return enc.units.filter((u) => UNITS[u.type].material && (u.goal !== false || u.key) && !['barrel', 'cart', 'barricade', 'wall'].includes(u.type)).length;
  }

  function isSiegeItem(def) {
    const m = def.mod || {};
    return !!((m.props && m.props.vs && m.props.vs.structure) || (m.active && m.active.vs && m.active.vs.structure));
  }

  // Which damage type gets through this enemy better: its armor against its magic
  // resistance, averaged over its fighters and reinforcements by HP (treasure guardians
  // count half). A gap under 8 points counts as even. `share` is the part of your
  // attackers Auto makes magic.
  function damageProfile(enc) {
    let w = 0;
    let armor = 0;
    let res = 0;
    const add = (spec, k) => {
      if (isObjectType(spec.type) || UNITS[spec.type].traits.includes('structure')) return;
      const b = E.buildUnit(spec, new Set());
      w += b.maxHp * k;
      armor += b.maxHp * k * b.armor;
      res += b.maxHp * k * b.res;
    };
    for (const u of enc.units) add(u, u.post ? 0.5 : 1);
    for (const wv of enc.waves || []) for (const u of wv.units) add(u, 1);
    if (!w) return { armor: 0, res: 0, share: 0.5, lean: 'mixed' };
    armor /= w;
    res /= w;
    const share = Math.min(0.85, Math.max(0.15, 0.5 + (armor - res) * 2.5));
    return { armor, res, share, lean: share >= 0.7 ? 'magic' : share <= 0.3 ? 'phys' : 'mixed' };
  }

  function counterScore(type, enc, prof) {
    const T = UNITS[type];
    // Siege engines earn their place when buildings must fall, and are a poor pick otherwise.
    const siege = T.act.vs && T.act.vs.structure ? (siegeTargets(enc) ? 1 + Math.min(0.6, 0.2 * siegeTargets(enc)) : 0.7) : 1;
    const p = prof || damageProfile(enc);
    const dmg = T.act.dmg;
    let k = 1;
    // Units whose damage gets through this enemy better are worth more.
    if (dmg === 'magic') k *= (p.share / 0.5) ** 0.7;
    else if (dmg === 'phys') k *= ((1 - p.share) / 0.5) ** 0.7;
    if (!isAttacker(type)) k *= 0.75;
    return Math.max(0.4, k * siege);
  }

  // A reasonable army for this battle within Supply: picks units,
  // levels, abilities and items, and places them. Rewrites the chosen units' loadouts.
  // variant > 0 shuffles the priorities a little, for a different suggestion each time.
  function autoDeploy(run, variant) {
    const enc = run.pending.enc;
    const vr = variant ? AG.derive(run.seed, 'auto:' + variant) : null;
    const jitter = {};
    for (const r of run.roster) jitter[r.id] = vr ? 0.6 + vr.next() * 0.8 : 1;
    const supply = supplyFor(run);
    const cap = armySize(run);
    for (const r of run.roster) {
      r.load.lv = 1;
      r.load.skills = [];
      r.load.gear = [];
      normalizeLoad(run, r);
      r.load.a1 = UNITS[r.type].abilities[1][0];
      r.load.a2 = UNITS[r.type].abilities[2][0];
      r.load.talents = [];
    }
    const prof = damageProfile(enc);
    const kind = (r) => UNITS[r.type].act.dmg;
    const worth = (r) => ((UNITS[r.type].cost + (r.enchant ? 1.5 : 0)) * counterScore(r.type, enc, prof) * jitter[r.id]) / Math.max(1, unitCost(run, r));
    const pool = run.roster.slice().sort((a, b) => worth(b) - worth(a) || UNITS[b.type].cost - UNITS[a.type].cost);
    const pick = [];
    let spent = 0;
    // A unit a bonus goal asks for always goes in, so you can see the goal is in reach.
    const wanted = bonusUnit(run, enc);
    if (wanted && unitCost(run, wanted) <= supply) {
      pick.push(wanted);
      spent += unitCost(run, wanted);
    }
    while (pick.length < cap) {
      const open = pool.filter((r) => !pick.includes(r) && spent + unitCost(run, r) <= supply);
      if (!open.length) break;
      const attackers = pick.filter((p) => isAttacker(p.type));
      // Supporting units wait until two attackers are in, and fill at most a third of the army.
      const supportFull = attackers.length < 2 || pick.length - attackers.length >= Math.max(1, Math.floor(cap / 3));
      const options = supportFull && open.some((o) => isAttacker(o.type)) ? open.filter((o) => isAttacker(o.type)) : open;
      // Steer the attackers toward the mix of damage types this enemy is weakest to.
      const magicIn = attackers.filter((p) => kind(p) === 'magic').length;
      const want = magicIn + 0.5 <= prof.share * (attackers.length + 1) ? 'magic' : 'phys';
      let r = options[0];
      if (kind(r) && kind(r) !== want) {
        const alt = options.find((o) => kind(o) === want);
        if (alt && worth(alt) >= worth(r) * 0.55) r = alt;
      }
      pick.push(r);
      spent += unitCost(run, r);
    }
    if (!pick.some((r) => isAttacker(r.type))) return [];
    // Spend what is left: levels on the best units, then owned items in open slots.
    for (let guard = 0; guard < 30; guard++) {
      const left = supply - pick.reduce((t, r) => t + unitCost(run, r), 0);
      if (left <= 0) break;
      let did = false;
      for (const r of pick) {
        if (r.load.lv >= 2) continue;
        // Priced by trying it: Level 2 also loses the Recruiter's Bell discount.
        const before = unitCost(run, r);
        r.load.lv = 2;
        if (unitCost(run, r) - before <= left) {
          did = true;
          break;
        }
        r.load.lv = 1;
      }
      if (!did) {
        // Siege gear first when buildings must fall; left in the pack otherwise.
        const siegeNeeded = siegeTargets(enc) > 0;
        const items = freeItems(run).filter((i) => i.kind !== 'scroll' && (siegeNeeded || !isSiegeItem(itemDef(i))));
        items.sort((a, b) => (siegeNeeded ? isSiegeItem(itemDef(b)) - isSiegeItem(itemDef(a)) : 0));
        for (const it of items) {
          const d = itemDef(it);
          if (d.cost > left) continue;
          const holder = pick.find((r) => assignItem(run, r.id, it.uid));
          if (holder) {
            did = true;
            break;
          }
        }
      }
      if (!did) {
        for (const r of pick) {
          if (r.load.lv >= 3) continue;
          if (LEVEL_COST[3] - LEVEL_COST[2] <= left && r.load.lv === 2) {
            r.load.lv = 3;
            did = true;
            break;
          }
        }
      }
      if (!did) {
        // No field limit: Supply left over after all that buys one more unit.
        const extra = pool.find((r) => !pick.includes(r) && unitCost(run, r) <= left);
        if (extra) {
          pick.push(extra);
          did = true;
        }
      }
      if (!did) break;
    }
    const taken = new Set();
    const out = [];
    for (const r of pick) {
      const slot = deploySlots(run, enc, isFront(r.type), taken)[0];
      if (!slot) break;
      taken.add(slot.x + ',' + slot.y);
      out.push({ rid: r.id, x: slot.x, y: slot.y, facing: 0 });
    }
    return out;
  }

  // ------------------------------------------------------------ advice

  // The scout report's first line: which damage type gets through this army better.
  function damageTip(enc) {
    const p = damageProfile(enc);
    const a = Math.round(p.armor * 100) + '%';
    const r = Math.round(p.res * 100) + '%';
    if (p.lean === 'magic') return `Their armor (${a} on average) outweighs their magic resistance (${r}): magic hits harder here. Auto favors magic attackers.`;
    if (p.lean === 'phys') return `Their magic resistance (${r} on average) outweighs their armor (${a}): steel hits harder here. Auto favors physical attackers.`;
    return `Their armor (${a}) and magic resistance (${r}) are close: both damage types work. Auto mixes physical and magic attackers.`;
  }

  // Plain-language counter tips for the scout report.
  function scoutTips(enc) {
    const foes = enc.units.filter((u) => !isObjectType(u.type));
    const count = (pred) => foes.filter((u) => pred(UNITS[u.type], u)).length;
    const has = (...types) => enc.units.some((u) => types.includes(u.type));
    const tips = [damageTip(enc)];
    const waves = enc.waves || [];
    if (waves.length) {
      const n = waves.reduce((t, w) => t + w.units.length, 0);
      tips.push(
        waves.some((w) => w.from)
          ? 'Reinforcements keep coming until their building falls. Stand on a marked tile to block an arrival; the blocker takes 10 damage.'
          : `${n} reinforcements are coming in waves. Stand on a marked tile to block an arrival; the blocker takes 10 damage.`
      );
    }
    // Only buildings that matter: goals, spawners and the castle.
    const buildings = enc.units.filter((u) => UNITS[u.type].material && (u.goal !== false || u.key) && !['barrel', 'cart', 'barricade', 'wall', 'tower'].includes(u.type));
    if (buildings.some((u) => UNITS[u.type].material === 'stone'))
      tips.push('Stone buildings shrug off swords and spells. Siege damage breaks them fast: a Trebuchet, Siege Hammer, Demolisher or Boulder Toss.');
    if (buildings.some((u) => UNITS[u.type].material === 'wood')) tips.push('Wooden buildings burn: fire and magic deal extra damage to them.');
    if (has('portal')) tips.push('Dark Portals: steel barely scratches them, but magic unravels them.');
    if (count((T) => T.act.dmg === 'magic') >= 2) tips.push('Heavy enemy magic: Mage Knights, Silk Mantles and a Barrier Ward blunt it. Spread out.');
    if (has('knight', 'castellan')) tips.push('Knights block 70% of frontal blows. Hit them from the side or behind, or use magic.');
    if (has('skeleton', 'specter', 'colossus', 'lich', 'skelarcher')) tips.push('Undead: magic and Blessed Blades shatter them. Specters have 50% armor.');
    if (has('orc', 'brute', 'goblin_archer', 'sapper', 'shaman', 'warlord')) tips.push('Greenskins: an Orcbane Axe deals 40% more. Kill the Shaman before the drums start.');
    if (has('sapper')) tips.push('Goblin Sappers explode beside you. Shoot them at range and keep a gap between your units.');
    if (has('barrel')) tips.push('Powder kegs explode for 22 when broken. Shoot them when enemies stand beside them.');
    if (has('troll')) tips.push(`Trolls regenerate ${UNITS.troll.props.regen} on each of their turns unless magic or fire hurt them since their last one.`);
    if (has('necromancer', 'lich')) tips.push('Kill the Necromancer and every skeleton it raised crumbles.');
    if (has('tower')) tips.push('Arrow Towers need not fall: stay out of their reach.');
    if (has('cart')) tips.push(`The wagons flee left ${UNITS.cart.move} tile${UNITS.cart.move > 1 ? 's' : ''} at the end of every enemy turn. Block their path with units and break them fast.`);
    if (has('spider')) tips.push('Spiders root from range: rooted units can still fight but cannot move.');
    if (has('assassin', 'beastrider', 'scout', 'warg', 'wolf', 'cutthroat')) tips.push('Fast flankers: face your fragile units toward them and screen them with tanks or shrubs.');
    if (has('cleric', 'shaman')) tips.push('Enemy healers: kill them early, or poison the huddle so the healing fails.');
    if (has('golem', 'golem_king')) tips.push('Golems have 50% armor but take 25% extra from magic.');
    if (has('dragon', 'ashen_tyrant', 'drake', 'brute', 'colossus')) tips.push('Huge foes: Dragonslayer Spears deal 50% more to them.');
    return tips.slice(0, 4);
  }

  // ------------------------------------------------------------ saving

  // A battle planned back when every unit moved each turn: stretch its timings to the
  // one-unit-a-turn rhythm.
  function retime(run, enc) {
    if (!enc || enc.tm === 2) return;
    enc.tm = 2;
    const group = enc.kind === 'boss' ? 'boss' : enc.kind === 'elite' ? 'elite' : 'normal';
    if (enc.hold) enc.hold.need = HOLD_NEED;
    if (enc.surviveTurns) enc.surviveTurns = run.act === 1 ? 12 : 15;
    const waves = enc.waves || [];
    const { first, every } = spawnRhythm(enc.primary, run.act, group);
    const k = {};
    for (const w of waves) {
      if (w.from) {
        k[w.from] = (k[w.from] || 0) + 1;
        w.turn = first + (k[w.from] - 1) * every;
      }
    }
    const edge = waves.filter((w) => !w.from);
    const turns = run.act === 1 ? [3, 7] : [2, 6, 10];
    edge.forEach((w, i) => (w.turn = turns[Math.min(i, turns.length - 1)] + Math.max(0, i - turns.length + 1) * 4));
    for (const b of enc.bonus || []) if (b.type === 'swift') b.turns = Math.round(b.turns * 2.5);
  }

  // ------------------------------------------------------------ hall of fame

  // Every campaign won leaves its army in the Hall of Fame, ranked best first. A newcomer
  // starts at the bottom and climbs by beating the army above it, one match at a time.
  const HALL_KEY = 'arena-gauntlet-hall-v1';
  const LEGEND_A = ['Iron', 'Ember', 'Silent', 'Golden', 'Crimson', 'Ashen', 'Storm', 'Wild', 'Grim', 'Bright', 'Hollow', 'Thorned', 'Gilded', 'Black'];
  const LEGEND_B = ['Company', 'Host', 'Band', 'Legion', 'Guard', 'Vanguard', 'Wardens', 'Brotherhood', 'Banner', 'Pact', 'Lances', 'Shields'];

  function loadHall() {
    try {
      const j = root.localStorage && root.localStorage.getItem(HALL_KEY);
      const h = j ? JSON.parse(j) : null;
      return h && Array.isArray(h.legends) ? h : { legends: [] };
    } catch (e) {
      return { legends: [] };
    }
  }

  function saveHall(h) {
    try {
      root.localStorage && root.localStorage.setItem(HALL_KEY, JSON.stringify(h));
    } catch (e) {
      /* storage unavailable */
    }
  }

  // Enter (or update, after the final challenge) this campaign's army in the Hall.
  function recordLegend(run) {
    if (!run.finalArmy || !run.finalArmy.length) return null;
    const h = loadHall();
    let legend = h.legends.find((l) => l.id === run.legendId);
    if (!legend) {
      // One army climbs at a time: one still climbing (you never watched) finishes its climb
      // first, played out at once, then the new one takes the bottom place.
      for (const l of h.legends.slice()) if (!l.climbed) finishClimb(h, l.id, run.seed);
      const rng = AG.derive(run.seed, 'legend');
      legend = {
        id: 'L' + run.seed.toString(36) + '-' + (h.legends.length + 1),
        name: `The ${rng.pick(LEGEND_A)} ${rng.pick(LEGEND_B)}`,
        date: new Date().toISOString().slice(0, 10),
        wins: 0,
        losses: 0,
        // The first army in an empty Hall has no one to climb past.
        climbed: !h.legends.length,
      };
      h.legends.push(legend);
      run.legendId = legend.id;
    }
    Object.assign(legend, { level: commanderLevel(run), relics: run.relics.slice(), units: run.finalArmy, superWon: !!run.superWon });
    saveHall(h);
    return legend;
  }

  // A Hall of Fame match: `a` from the south (blue), `b` from the north (red, mirrored), on
  // a fresh field with obstacles mirrored so neither side is favored.
  function hallBattleConfig(a, b, seed) {
    const rng = AG.derive(seed, 'hall');
    const terrain = genTerrain(rng, 1 + rng.int(3), BOARD, BOARD, null);
    const units = [];
    const free = (x, y) => terrain[y * BOARD + x] === 0 && !units.some((u) => u.x === x && u.y === y);
    const place = (L, team) => {
      for (const it of L.units) {
        let x = team === 'P' ? it.x : BOARD - 1 - it.x;
        let y = team === 'P' ? it.y : BOARD - 1 - it.y;
        // A rock where it once stood: the nearest open tile on its own half.
        if (!free(x, y)) {
          let best = null;
          for (let ty = 0; ty < BOARD; ty++)
            for (let tx = 0; tx < BOARD; tx++) {
              if ((team === 'P' ? ty < 5 : ty > 3) || !free(tx, ty)) continue;
              const d = Math.abs(tx - x) + Math.abs(ty - y);
              if (!best || d < best.d) best = { x: tx, y: ty, d };
            }
          if (!best) continue;
          x = best.x;
          y = best.y;
        }
        units.push(Object.assign({}, it.spec, { team, x, y, facing: team === 'P' ? 0 : 2 }));
      }
    };
    place(a, 'P');
    place(b, 'E');
    return { w: BOARD, h: BOARD, terrain, units, relics: { P: (a.relics || []).slice(), E: (b.relics || []).slice() }, seed, objective: 'all', loot: [], goals: [], cartExit: 0, turnLimit: TURN_LIMIT, waves: [], queue: true, overtime: OVERTIME };
  }

  // Play a Hall match out at once, both sides on the AI. Returns 'P' (a) or 'E' (b).
  function playHallMatch(a, b, seed) {
    const s = E.createBattle(hallBattleConfig(a, b, seed));
    for (let guard = 0; guard < 6000 && !s.over; guard++) {
      AG.AI.playTurn(s, s.side, { stance: 'balanced', temp: 0.3 });
      s.events.length = 0;
    }
    return s.winner || 'E';
  }

  // Record a climb match: the challenger (a) beat the army right above it? They swap places.
  // Either way the record grows; a loss (or reaching the top) ends the climb.
  function applyHallResult(h, aId, bId, winner) {
    const L = h.legends;
    const ia = L.findIndex((l) => l.id === aId);
    const ib = L.findIndex((l) => l.id === bId);
    if (ia < 0 || ib < 0) return;
    const a = L[ia];
    const b = L[ib];
    if (winner === 'P') {
      a.wins++;
      b.losses++;
      if (ib === ia - 1) [L[ia], L[ib]] = [b, a];
    } else {
      a.losses++;
      b.wins++;
    }
    if (winner !== 'P' || L.indexOf(a) === 0) a.climbed = true;
  }

  function hallResult(aId, bId, winner) {
    const h = loadHall();
    applyHallResult(h, aId, bId, winner);
    saveHall(h);
    return h;
  }

  // The army a climbing legend faces next: the one right above it (null when done).
  function hallNext(h, id) {
    const i = h.legends.findIndex((l) => l.id === id);
    if (i <= 0 || h.legends[i].climbed) return null;
    return h.legends[i - 1];
  }

  // The army climbing now, if any (the lowest one that has not finished its climb).
  function hallClimber(h) {
    return h.legends.slice().reverse().find((l) => hallNext(h, l.id)) || null;
  }

  // Play a whole climb out at once.
  function finishClimb(h, id, seed) {
    const me = h.legends.find((l) => l.id === id);
    for (let i = 0; i < 200 && me; i++) {
      const foe = hallNext(h, id);
      if (!foe) break;
      applyHallResult(h, id, foe.id, playHallMatch(me, foe, (seed || 1) + i));
    }
    if (me) me.climbed = true;
  }

  function save(run) {
    try {
      root.localStorage && root.localStorage.setItem(SAVE_KEY, JSON.stringify(run));
    } catch (e) {
      /* storage unavailable */
    }
  }

  // Older saves picked talents as level abilities (with the copy in t1/t2, or with no item
  // before talents were items). Each unit keeps them, as talents in its slots.
  function grantPickedTalents(run) {
    if (run.talents === 2) return;
    run.talents = 2;
    for (const r of run.roster) {
      const L = r.load;
      L.talents = L.talents || [];
      for (const tier of [1, 2]) {
        const id = L['a' + tier];
        if (isTalent(id)) {
          const held = itemByUid(run, L['t' + tier]);
          L.talents.push(held && held.id === id ? held.uid : addItem(run, 'talent', id).uid);
          L['a' + tier] = UNITS[r.type].abilities[tier][0];
        }
        delete L['t' + tier];
      }
    }
  }

  function load() {
    try {
      const j = root.localStorage && root.localStorage.getItem(SAVE_KEY);
      if (!j) return null;
      const r = JSON.parse(j);
      // Saves from the map days (before the challenge rounds) cannot carry on.
      if (!r || r.v !== 2 || r.over || !r.plan) return null;
      if (r.pending && r.pending.type === 'battle') retime(r, r.pending.enc);
      grantPickedTalents(r);
      // Saves from before the field limit went: a paid-for wider line becomes Supply.
      if (r.capBonus) {
        r.supplyBonus = (r.supplyBonus || 0) + r.capBonus;
        delete r.capBonus;
      }
      return r;
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
      return Object.assign({ runs: 0, wins: 0, superWins: 0, bestAct: 0 }, j ? JSON.parse(j) : {});
    } catch (e) {
      return { runs: 0, wins: 0, superWins: 0, bestAct: 0 };
    }
  }

  function recordMeta(run) {
    const m = loadMeta();
    if (run.superWon && !run.superRecorded) {
      run.superRecorded = true;
      m.superWins++;
    }
    if (!run.metaRecorded) {
      run.metaRecorded = true;
      m.runs++;
      if (run.won) m.wins++;
      m.bestAct = Math.max(m.bestAct, run.won ? 4 : run.act);
    }
    try {
      root.localStorage && root.localStorage.setItem(META_KEY, JSON.stringify(m));
    } catch (e) {
      /* storage unavailable */
    }
  }

  AG.Run = {
    FIGHTS, TIERS, LEAN_GOLD, OVERTIME, EVENTS, LOOT_NAMES,
    newRun, curStep, chooseChallenge, backToChoice, challengeReward, completeNode, faceFinal, endRun, bossOf, battleXp,
    commanderLevel, levelInfo, supplyFor, armySize, gainXp,
    DRAFT_STEPS, DRAFT_GOLD, draftOffer, addRecruit, talentNote, stripLoad, addItem, itemDef, itemByUid, itemHolder, slotsFor, normalizeLoad, setLevel, setAbility, assignItem, unassignItem, freeItems,
    costBreakdown, unitCost, bareCost, deployCost, supplyUsed, specFor, unitStats, applyScroll, unitById, hasRelic,
    objectiveInfo, bonusUnit, musterCandidates, deployRows, deployOpen, deploySlots, startingPlan, autoDeploy, counterScore, damageProfile, isFront, battleConfig,
    genEncounter, enemyCost, finishBattle, takeSpoil, skipSpoils, takeTome, skipTome, takeBossRelic,
    genShop, canBuy, buy, rerollPrice, rerollShop, eventDef, eventChoices, chooseEvent, scoutTips,
    save, load, clearSave, snapshot, restore, goalResults, loadMeta, recordMeta,
    loadHall, saveHall, recordLegend, hallBattleConfig, playHallMatch, hallResult, hallNext, hallClimber, finishClimb,
  };
})(typeof window !== 'undefined' ? window : globalThis);
