// The balance lab. Whole campaigns are played by the usual simulated player (Auto armies,
// medium battles, retries), so commander level, Supply, relics and rosters are what real
// runs have at each point. At every challenge card on the way (easy, medium, elite, each
// boss, the final challenge) the run is cloned and a set of test armies takes the battle on
// instead, each several times:
//
//   stale     the army of the last battle, unchanged: a player who just taps Begin battle
//   auto      the War Room's Auto army for this battle (auto1 to auto4: its next plans, the
//             first three of them smaller armies of better units)
//   top3      Auto with only the three best-suited units of the roster (top2, top4, top5),
//             steel / spells: Auto with the magic / the physical attackers left at home
//   wide      an army of Level 1 units, as many as the Supply buys      (wideK: with kit)
//   mid       Level 2 units                                              (midK: with kit)
//   tall      Level 3 units                                              (tallK: with kit)
//   duo:X     one Level 3 X with everything on it, and the Cleric, nothing else
//
// The shaped armies pick their units the way Auto does (what gets through this enemy), from
// every non-legendary class, so only the shape differs. Nothing here changes the game.
//
// Run: node tests/balance.js [campaigns] [tries per army]     (writes rows as JSON lines)
//   OUT=file     where the rows go (default: balance-rows.jsonl in the working directory)
//   CANDS=a,b    only these armies          TIERS=medium,boss   only these cards
//   SEED0=9000   first campaign seed        DRAFT=1             drafted armies, not warbands
//   MISSIONS=survive,gate                   only cards with these missions
//   WEAR=5       bosses as worn down as five defeats leave them (off otherwise)
//   HOST=elite   the tier the host campaign itself takes (default medium)
//   TUNE='{"bal.scale.normal":1.5,"tempo.rest":3,"tiers.elite.mult":2,"units.dragon.hp":90}'
//                other numbers for this run only: bal (Run.BAL), tiers (Run.TIERS), tempo
//                (Engine.TEMPO), units (Data.UNITS), data (anything else in Data)
// Then: node tests/balance-report.js [file]
const fs = require('fs');
const AG = require('./load')();
const R = AG.Run;
const E = AG.Engine;
const D = AG.Data;
const { UNITS, TALENTS, SKILLS, GEAR, ENCHANTS, ABILITIES } = D;

const N = +process.argv[2] || 4;
const TRIES = +process.argv[3] || 2;
const OUT = process.env.OUT || 'balance-rows.jsonl';
const SEED0 = +process.env.SEED0 || 9000;
const HOST = process.env.HOST || 'medium';
const RANK = { easy: 0, medium: 1, elite: 2 };
const ONLY = process.env.CANDS ? process.env.CANDS.split(',') : null;
const ONLY_TIERS = process.env.TIERS ? process.env.TIERS.split(',') : null;
const ONLY_MISSIONS = process.env.MISSIONS ? process.env.MISSIONS.split(',') : null;
// As in the game: your units play sharply, the enemy commander a little loosely.
const P_TEMP = process.env.PTEMP != null ? +process.env.PTEMP : 0.3;
const E_TEMP = process.env.ETEMP != null ? +process.env.ETEMP : (D.DIFFICULTIES.find((d) => d.id === 'knight') || { temp: 1.2 }).temp;

const clone = (o) => JSON.parse(JSON.stringify(o));

// Numbers to try, set in memory before anything is played.
function applyTune(json) {
  const roots = { bal: R.BAL, tiers: R.TIERS, tempo: E.TEMPO, units: D.UNITS, data: D };
  for (const [key, v] of Object.entries(JSON.parse(json))) {
    const parts = key.split('.');
    let o = roots[parts[0]];
    if (!o) throw new Error('TUNE: no such table: ' + parts[0]);
    for (const k of parts.slice(1, -1)) {
      if (o[k] == null) o[k] = {};
      o = o[k];
    }
    // A table the game holds on to (level costs, level stats) is changed in place.
    const last = parts[parts.length - 1];
    if (Array.isArray(o[last]) && Array.isArray(v)) o[last].splice(0, o[last].length, ...v);
    else o[last] = v;
  }
}
if (process.env.TUNE) applyTune(process.env.TUNE);
// A boss worn down by earlier defeats would blur the comparison (each army's tries count as
// defeats): off here, unless WEAR=n asks for an army n defeats in.
const WEAR = process.env.WEAR != null ? +process.env.WEAR : null;
if (WEAR == null) R.BAL.wear.step = 0;

function playOut(run, dep) {
  const enc = run.pending.enc;
  const s = E.createBattle(R.battleConfig(run, dep));
  let guard = 0;
  while (!s.over && guard++ < 4000) {
    AG.AI.playTurn(s, s.side, s.side === 'E' ? { stance: enc.stance, temp: E_TEMP } : { stance: 'balanced', temp: P_TEMP });
    s.events.length = 0;
  }
  return s;
}

// What a battle gathered, as the Victory screen counts it.
// `lab`: a made-up army has no roster to answer a "field this unit" goal from, so that goal
// counts as met for it whenever it wins (a real army just adds the unit).
function measure(run, s, dep, lab) {
  const enc = run.pending.enc;
  const won = s.winner === 'P';
  const pouches = s.units.filter((u) => u.team === 'E' && (u.structure || u.nonCombat) && !u.traits.has('summon') && (u.bounty || u.salvage));
  const goldTotal = pouches.reduce((t, u) => t + (u.bounty || u.salvage), 0);
  const goldGot = won ? s.stats.bounty || 0 : 0;
  const goals = won ? R.goalResults(run, s, dep) : (enc.bonus || []).map(() => ({ done: false }));
  const goalTypes = (enc.bonus || []).map((b) => (b.type === 'loot' ? 'loot:' + b.kind : b.type));
  const met = goals.map((g, i) => !!g.done || (won && lab && goalTypes[i] === 'muster'));
  const mine = s.units.filter((u) => u.team === 'P' && u.rid);
  const lost = mine.filter((u) => !u.alive).length;
  const full = won && goldGot >= goldTotal && met.every(Boolean);
  // Everything on offer, counted as parts: the win, the building gold, each goal.
  const parts = 1 + (goldTotal ? 1 : 0) + met.length;
  const got = (won ? 1 : 0) + (goldTotal && goldGot >= goldTotal ? 1 : 0) + met.filter(Boolean).length;
  // lostW: units down when the win was sealed (what the flawless goal counts); the rest fell to the cleanup's fatigue.
  return { won, full, goldGot, goldTotal, goalTypes, met, turns: s.turn, lost, lostW: s.won ? s.won.lost : lost, units: mine.length, haul: got / parts, wonAt: s.won ? s.won.turn : s.turn, ot: !!s.inOvertime };
}

// ------------------------------------------------------------ test armies

const CATALOG = D.RECRUITABLE.filter((t) => UNITS[t].rarity !== 'legendary' && UNITS[t].role !== 'ward' && t !== 'cleric');
// Kit a unit of any army could want (the counters, siege tools and gold-finders are left out).
const GOOD_SKILLS = ['vampiric', 'executioner', 'killing_spree', 'lucky', 'headhunter', 'last_stand', 'second_wind', 'undying_rage', 'flanker', 'pack_tactics', 'bloodlust', 'quickened', 'chaos_magic', 'overwatch', 'eagle_eye', 'guardian', 'retaliate', 'disciplined'];
const GOOD_GEAR = ['flame_brand', 'venom_edge', 'armor_breaker', 'healing_charm', 'porcupine_ring', 'reactive_plate', 'echo_amulet', 'momentum_boots', 'ogre_belt', 'hourglass_pendant', 'hex_charm', 'frost_brand', 'storm_rod', 'stunning_shield', 'spellsink_mantle', 'berserker_torc'];

const SHAPES = {
  wide: { lv: 1, kit: 0 },
  wideK: { lv: 1, kit: 1 },
  mid: { lv: 2, kit: 0 },
  midK: { lv: 2, kit: 1 },
  tall: { lv: 3, kit: 0 },
  tallK: { lv: 3, kit: 1 },
  // One-sided Level 2 armies, picked without a look at the enemy: what a matchup is worth.
  phys: { lv: 2, kit: 0, blind: true, only: (T) => T.act.dmg === 'phys' },
  magic: { lv: 2, kit: 0, blind: true, only: (T) => T.act.dmg === 'magic' || !!(T.act.fx && T.act.fx.poison) },
  ranged: { lv: 2, kit: 0, blind: true, only: (T) => ['ranged', 'caster'].includes(T.role) },
  melee: { lv: 2, kit: 0, blind: true, only: (T) => ['tank', 'melee', 'skirmisher', 'monster'].includes(T.role) },
  tanks: { lv: 2, kit: 0, blind: true, only: (T) => T.role === 'tank' || T.hp >= 46 },
  swift: { lv: 1, kit: 0, blind: true, only: (T) => T.cost <= 3 && T.spd >= 4 },
  // The same shapes with no look at the enemy at all.
  blindWide: { lv: 1, kit: 0, blind: true },
  blindMid: { lv: 2, kit: 0, blind: true },
  blindTall: { lv: 3, kit: 0, blind: true },
};

function bareLoad(type) {
  const T = UNITS[type];
  const free = (tier) => T.abilities[tier].find((id) => !TALENTS[id] && ABILITIES[id].cost === 0) || T.abilities[tier].find((id) => !TALENTS[id]) || T.abilities[tier][0];
  return { lv: 1, a1: free(1), a2: free(2), talents: [], skills: [], gear: [] };
}

const isAttacker = (type) => {
  const T = UNITS[type];
  return !!(T.act.dmg || (T.act.fx && T.act.fx.poison) || (T.extra || []).some((a) => a.dmg));
};

function place(run, enc, pick) {
  const taken = new Set();
  const out = [];
  const put = (r, slot) => {
    taken.add(slot.x + ',' + slot.y);
    out.push({ rid: r.id, x: slot.x, y: slot.y, facing: 0 });
  };
  const cleric = pick.find((r) => r.core);
  if (cleric) {
    const y = enc.h - 1;
    const mid = (enc.w - 1) / 2;
    const xs = [...Array(enc.w).keys()].filter((x) => R.deployOpen(enc, x, y)).sort((a, b) => Math.abs(a - mid) - Math.abs(b - mid) || a - b);
    const slot = xs.length ? { x: xs[0], y } : R.deploySlots(run, enc, false, taken)[0];
    if (slot) put(cleric, slot);
  }
  for (const r of pick) {
    if (r === cleric) continue;
    const slot = R.deploySlots(run, enc, R.isFront(r.type), taken)[0];
    if (!slot) break;
    put(r, slot);
  }
  return out;
}

// Slot one more piece of kit of `kind` into `r` from `ids` (a new copy each time), if a slot
// is open; returns its Supply cost, or -1.
function addKit(run, r, kind, ids, rng) {
  const key = { talent: 'talents', skill: 'skills', gear: 'gear' }[kind];
  const sl = R.slotsFor(r.load.lv)[key];
  if (r.load[key].length >= sl) return -1;
  const have = new Set(r.load[key].map((uid) => R.itemByUid(run, uid).id));
  const table = kind === 'talent' ? TALENTS : kind === 'skill' ? SKILLS : GEAR;
  const open = ids.filter((id) => !have.has(id) && D.eligible(r.type, table[id]));
  if (!open.length) return -1;
  const id = rng.pick(open);
  const it = R.addItem(run, kind, id);
  r.load[key].push(it.uid);
  return table[id].cost;
}

function dropKit(run, r) {
  for (const key of ['gear', 'skills', 'talents']) {
    if (r.load[key].length) {
      const uid = r.load[key].pop();
      run.items = run.items.filter((i) => i.uid !== uid);
      return true;
    }
  }
  return false;
}

// Fill a unit's slots as the shape asks (kit: every slot its level opens).
function outfit(run, r, shape, rng) {
  r.load = bareLoad(r.type);
  r.load.lv = shape.lv;
  if (!shape.kit) return;
  const tal = Object.keys(TALENTS).filter((id) => TALENTS[id].cls === r.type);
  for (let g = 0; g < 8; g++) {
    let any = false;
    for (const [kind, ids] of [['talent', tal], ['skill', GOOD_SKILLS], ['gear', GOOD_GEAR]]) if (addKit(run, r, kind, ids, rng) >= 0) any = true;
    if (!any) break;
  }
}

function shapeArmy(run, name, rng) {
  const shape = SHAPES[name];
  const enc = run.pending.enc;
  const core = R.coreUnit(run);
  run.roster = [core];
  run.items = [];
  core.enchant = null;
  const supply = R.supplyFor(run);
  const cost = () => run.roster.reduce((t, r) => t + R.unitCost(run, r), 0);
  // The Cleric at the shape's level; its kit is the first thing to go when Supply is short.
  outfit(run, core, shape, rng);
  while (cost() > supply && dropKit(run, core));
  while (cost() > supply && core.load.lv > 1) core.load.lv--;
  const prof = R.damageProfile(enc);
  const threat = R.threatProfile(enc);
  const jit = {};
  for (const t of CATALOG) jit[t] = 0.6 + rng.next() * 0.8;
  const worth = (t) => (shape.blind ? 1 : R.counterScore(t, enc, prof, threat)) * jit[t];
  const order = CATALOG.filter((t) => !shape.only || shape.only(UNITS[t])).sort((a, b) => worth(b) - worth(a));
  if (!order.length) return null;
  const count = (t) => run.roster.filter((r) => r.type === t).length;
  const kind = (t) => UNITS[t].act.dmg;
  for (let guard = 0; guard < 40; guard++) {
    const others = run.roster.filter((r) => !r.core);
    const attackers = others.filter((r) => isAttacker(r.type));
    const supportFull = attackers.length < 2 || others.length - attackers.length >= Math.max(1, Math.floor(others.length / 3));
    let open = order.filter((t) => count(t) < 2);
    if (supportFull && open.some(isAttacker)) open = open.filter(isAttacker);
    const magicIn = attackers.filter((r) => kind(r.type) === 'magic').length;
    const want = magicIn + 0.5 <= prof.share * (attackers.length + 1) ? 'magic' : 'phys';
    let added = false;
    const tryOrder = open.slice();
    if (!tryOrder.length) break;
    if (!shape.blind && kind(tryOrder[0]) && kind(tryOrder[0]) !== want) {
      const alt = tryOrder.find((t) => kind(t) === want);
      if (alt && worth(alt) >= worth(tryOrder[0]) * 0.55) tryOrder.unshift(alt);
    }
    for (const t of tryOrder) {
      const r = R.addRecruit(run, t);
      run.items = run.items.filter((i) => i.id !== r.brought || R.itemHolder(run, i.uid)); // its free talent stays in the catalog, not the pack
      outfit(run, r, shape, rng);
      // A kitted unit that does not quite fit sheds kit, down to half of it, before giving up.
      let shed = 0;
      while (cost() > supply && shed < 3 && dropKit(run, r)) shed++;
      if (cost() <= supply) {
        added = true;
        break;
      }
      while (dropKit(run, r));
      run.roster.pop();
    }
    if (!added) break;
  }
  // Spare Supply: one more unit a level lower if it fits, else kit.
  for (let guard = 0; guard < 12; guard++) {
    const left = supply - cost();
    if (left <= 0) break;
    let did = false;
    if (shape.lv > 1) {
      for (const t of order) {
        if (count(t) >= 2 || !isAttacker(t)) continue;
        const r = R.addRecruit(run, t);
        run.items = run.items.filter((i) => i.id !== r.brought || R.itemHolder(run, i.uid));
        r.load = bareLoad(t);
        r.load.lv = shape.lv - 1;
        if (cost() <= supply) {
          did = true;
          break;
        }
        run.roster.pop();
      }
    }
    if (!did) {
      for (const r of rng.shuffle(run.roster.slice())) {
        const tal = Object.keys(TALENTS).filter((id) => TALENTS[id].cls === r.type);
        for (const [kindOf, ids] of rng.shuffle([['talent', tal], ['skill', GOOD_SKILLS], ['gear', GOOD_GEAR]])) {
          const c = addKit(run, r, kindOf, ids.filter((id) => (kindOf === 'talent' ? TALENTS : kindOf === 'skill' ? SKILLS : GEAR)[id].cost <= left), rng);
          if (c >= 0) {
            did = true;
            break;
          }
        }
        if (did) break;
      }
    }
    if (!did) break;
  }
  for (const r of run.roster) R.normalizeLoad(run, r);
  if (!run.roster.some((r) => isAttacker(r.type))) return null;
  return place(run, enc, run.roster);
}

// One Level 3 carry with everything on it, and the Cleric: the carry first, then the Cleric.
// Variants take parts of the kit away again, to see which part carries it (duo:knight:vl):
//   v  no lifesteal        l  no second lives        k  no heals or growth on a kill
//   0  no kit on the carry c  a bare Level 1 Cleric  2  the carry at Level 2   q  no enchantment
const CARRY_SKILLS = ['vampiric', 'undying_rage', 'second_wind', 'last_stand', 'headhunter', 'killing_spree', 'executioner', 'lucky'];
const CARRY_GEAR = ['reactive_plate', 'ogre_belt', 'hourglass_pendant', 'healing_charm', 'porcupine_ring', 'flame_brand'];
const CLERIC_PLAN = [['talent', 'c_bless'], ['talent', 'c_angel'], ['gear', 'healing_charm'], ['skill', 'last_stand'], ['gear', 'hourglass_pendant'], ['skill', 'second_wind'], ['talent', 'c_halo']];
const KIT_GROUPS = {
  v: ['vampiric', 'bloodforged'],
  l: ['second_wind', 'hourglass_pendant', 'c_angel', 'reactive_plate', 'undying_rage', 'last_stand'],
  k: ['headhunter', 'ogre_belt', 'killing_spree'],
};
function duoArmy(run, type, rng, extras, flags) {
  flags = flags || '';
  const banned = new Set();
  for (const f of flags) for (const id of KIT_GROUPS[f] || []) banned.add(id);
  const bare = flags.includes('0');
  const enc = run.pending.enc;
  const core = R.coreUnit(run);
  run.roster = [core];
  run.items = [];
  core.enchant = null;
  core.load = bareLoad('cleric');
  const supply = R.supplyFor(run);
  const cost = () => run.roster.reduce((t, r) => t + R.unitCost(run, r), 0);
  const carry = R.addRecruit(run, type);
  run.items = [];
  carry.load = bareLoad(type);
  const T = UNITS[type];
  const tryDo = (fn, undo) => {
    fn();
    if (cost() > supply) {
      undo();
      return false;
    }
    return true;
  };
  const lvUp = (r, lv) => {
    const was = r.load.lv;
    for (let l = lv; l > was; l--) if (tryDo(() => (r.load.lv = l), () => (r.load.lv = was))) return;
  };
  const give = (r, kind, id) => {
    if (banned.has(id) || (bare && r === carry) || (flags.includes('c') && r === core)) return false;
    const key = { talent: 'talents', skill: 'skills', gear: 'gear' }[kind];
    const table = kind === 'talent' ? TALENTS : kind === 'skill' ? SKILLS : GEAR;
    if (!table[id] || !D.eligible(r.type, table[id]) || r.load[key].length >= R.slotsFor(r.load.lv)[key]) return false;
    if (r.load[key].some((uid) => R.itemByUid(run, uid).id === id)) return false;
    let it;
    return tryDo(
      () => {
        it = R.addItem(run, kind, id);
        r.load[key].push(it.uid);
      },
      () => {
        r.load[key].pop();
        run.items = run.items.filter((i) => i.uid !== it.uid);
      }
    );
  };
  lvUp(carry, flags.includes('2') ? 2 : 3);
  if (!flags.includes('c')) lvUp(core, 3);

  // The carry's cooldown first (the enchantment that shortens it), then its kit, dearest first.
  const quick = T.rec >= 1 ? 'quicksilver' : 'bloodforged';
  if (!bare && !banned.has(quick) && !flags.includes('q')) tryDo(() => (carry.enchant = quick), () => (carry.enchant = null));
  const tal = Object.keys(TALENTS).filter((id) => TALENTS[id].cls === type).sort((a, b) => TALENTS[b].cost - TALENTS[a].cost);
  const rounds = Math.max(tal.length, CARRY_SKILLS.length, CARRY_GEAR.length, CLERIC_PLAN.length);
  for (let i = 0; i < rounds; i++) {
    if (tal[i]) give(carry, 'talent', tal[i]);
    if (CARRY_SKILLS[i]) give(carry, 'skill', CARRY_SKILLS[i]);
    if (CARRY_GEAR[i]) give(carry, 'gear', CARRY_GEAR[i]);
    if (CLERIC_PLAN[i]) give(core, CLERIC_PLAN[i][0], CLERIC_PLAN[i][1]);
  }
  // duo+: what is left over buys Level 1 bodies to stand around it.
  if (extras) {
    const prof = R.damageProfile(enc);
    const threat = R.threatProfile(enc);
    const order = CATALOG.filter(isAttacker).sort((a, b) => R.counterScore(b, enc, prof, threat) * (0.6 + rng.next() * 0.8) - R.counterScore(a, enc, prof, threat) * (0.6 + rng.next() * 0.8));
    for (const t of order) {
      const r = R.addRecruit(run, t);
      run.items = run.items.filter((i) => R.itemHolder(run, i.uid));
      r.load = bareLoad(t);
      if (cost() > supply) run.roster.pop();
    }
  }
  for (const r of run.roster) R.normalizeLoad(run, r);
  return place(run, enc, run.roster);
}

// The army of the last battle, as the War Room opens with it; over Supply (a relic taken
// since), it sheds its dearest units until it fits.
function staleArmy(run) {
  if (!run.lastPlan || !run.lastPlan.length) return null;
  let dep = R.startingPlan(run, run.pending.enc);
  const supply = R.supplyFor(run);
  while (R.supplyUsed(run, dep) > supply && dep.length > 1) {
    const out = dep.filter((d) => !R.unitById(run, d.rid).core).sort((a, b) => R.deployCost(run, b.rid) - R.deployCost(run, a.rid))[0];
    if (!out) break;
    dep = dep.filter((d) => d !== out);
  }
  return dep.some((d) => isAttacker(R.unitById(run, d.rid).type)) ? dep : null;
}

// Auto with part of the roster left at home: what a player does who reads the enemy and
// brings fewer, better-suited units (Auto then spends the Supply on their levels and kit).
// `keep`: how many units besides the Cleric; `only`: a filter on unit types.
function rosterArmy(run, keep, only) {
  const enc = run.pending.enc;
  const prof = R.damageProfile(enc);
  const threat = R.threatProfile(enc);
  const star = R.bonusUnit(run, enc);
  const worth = (r) => UNITS[r.type].cost * R.counterScore(r.type, enc, prof, threat);
  let pool = run.roster.filter((r) => !r.core && UNITS[r.type].role !== 'ward' && (!only || only(UNITS[r.type]) || r === star));
  pool.sort((a, b) => (b === star) - (a === star) || worth(b) - worth(a));
  // The best-suited attackers first, then whoever is left.
  const pick = pool.filter((r) => isAttacker(r.type)).slice(0, keep);
  for (const r of pool) if (pick.length < keep && !pick.includes(r)) pick.push(r);
  if (!pick.some((r) => isAttacker(r.type))) return null;
  run.roster = run.roster.filter((r) => r.core || pick.includes(r));
  return R.autoDeploy(run, 0);
}

const CANDS = {
  stale: (run) => staleArmy(run),
  auto: (run) => R.autoDeploy(run, 0),
  auto1: (run) => R.autoDeploy(run, 1),
  auto2: (run) => R.autoDeploy(run, 2),
  auto3: (run) => R.autoDeploy(run, 3),
  auto4: (run) => R.autoDeploy(run, 4),
  top2: (run) => rosterArmy(run, 2),
  top3: (run) => rosterArmy(run, 3),
  top4: (run) => rosterArmy(run, 4),
  top5: (run) => rosterArmy(run, 5),
  steel: (run) => rosterArmy(run, 99, (T) => T.act.dmg !== 'magic'),
  spells: (run) => rosterArmy(run, 99, (T) => T.act.dmg !== 'phys'),
};
for (const name of Object.keys(SHAPES)) CANDS[name] = (run, rng) => shapeArmy(run, name, rng);
// duo:knight, duo+:knight (spare Supply on Level 1 bodies), duo:knight:vl (kit taken away).
function candFor(name) {
  if (CANDS[name]) return CANDS[name];
  const m = /^duo(\+?):([a-z]+)(?::([a-z0-9]+))?$/.exec(name);
  if (!m || !UNITS[m[2]]) throw new Error('no such army: ' + name);
  return (run, rng) => duoArmy(run, m[2], rng, !!m[1], m[3] || '');
}
const DEFAULT_CANDS = ['stale', 'auto', 'auto1', 'wide', 'wideK', 'mid', 'midK', 'tall', 'tallK', 'duo:dragon', 'duo:berserker', 'duo:frostgiant', 'duo:golem', 'duo:assassin', 'duo:witch', 'duo:knight'];
const cands = ONLY || DEFAULT_CANDS;

// Written as it goes (the whole run is one synchronous loop), so a long run can be read early.
let out = null;
let rows = 0;

function evalCards(host, hostIdx) {
  const offer = host.offer;
  for (let idx = 0; idx < offer.length; idx++) {
    const tier = offer[idx].tier;
    if (ONLY_TIERS && !ONLY_TIERS.includes(tier)) continue;
    if (ONLY_MISSIONS && !ONLY_MISSIONS.includes(offer[idx].enc.primary)) continue;
    for (const name of cands) {
      for (let t = 0; t < TRIES; t++) {
        const c = clone(host);
        if (!R.chooseChallenge(c, idx)) continue;
        c.pending.attempt = t;
        if (WEAR != null) c.pending.wear = WEAR;
        const rng = AG.derive(host.seed, `lab:${host.act}:${host.step}:${tier}:${name}:${t}`);
        const dep = candFor(name)(c, rng);
        if (!dep || !dep.length) continue;
        const used = R.supplyUsed(c, dep);
        if (used > R.supplyFor(c)) throw new Error(`${name} over Supply: ${used} > ${R.supplyFor(c)}`);
        const s = playOut(c, dep);
        const m = measure(c, s, dep, !!SHAPES[name] || name.startsWith('duo'));
        const enc = c.pending.enc;
        const lv = dep.map((d) => R.unitById(c, d.rid).load.lv);
        const foes = enc.units.filter((u) => !UNITS[u.type].traits.includes('object') && !UNITS[u.type].traits.includes('structure'));
        fs.writeSync(
          out,
          JSON.stringify(Object.assign(m, {
            host: hostIdx, seed: host.seed, act: host.act, step: host.step, tier, kind: enc.kind, enc: enc.name, primary: enc.primary, cand: name, t,
            supply: R.supplyFor(c), used, relics: host.relics.length, cmd: R.commanderLevel(host), n: dep.length, lv: (lv.reduce((a, b) => a + b, 0) / lv.length).toFixed(2), foes: foes.length, budget: enc.budget, fs: R.encSupply(enc), fl: +(foes.reduce((a, u) => a + (u.level || 1), 0) / Math.max(1, foes.length)).toFixed(2), ft: [...new Set(foes.map((u) => u.type))].sort().join(','), fr: (enc.relics || []).join(','),
          })) + '\n'
        );
        rows++;
      }
    }
  }
}

// ------------------------------------------------------------ the host campaign

function hostBattle(run) {
  const p = run.pending;
  const dep = R.autoDeploy(run, p.attempt || 0);
  const s = playOut(run, dep);
  if (s.winner === 'P') run.lastPlan = dep.map((d) => ({ rid: d.rid, x: d.x, y: d.y, facing: 0 }));
  return R.finishBattle(run, s, dep);
}

function main() {
  out = fs.openSync(OUT, 'w');
  const t0 = Date.now();
  for (let i = 0; i < N; i++) hostCampaign(i, t0, evalCards);
  fs.closeSync(out);
}

// One host campaign; `onCards(run, i)` is called at every choice of battles.
function hostCampaign(i, t0, onCards) {
  let run;
  if (process.env.DRAFT) {
    const pick = AG.derive(SEED0 + i, 'sim-draft');
    const picks = [];
    for (let s = 0; s < R.DRAFT_STEPS.length; s++) picks.push(pick.pick(R.draftOffer(SEED0 + i, s, picks).options));
    run = R.newRun({ seed: SEED0 + i, draft: { units: picks.slice(0, 5), relic: picks[5], items: [['skill', picks[6]], ['gear', picks[7]]] } });
  } else run = R.newRun({ seed: SEED0 + i, warband: D.WARBANDS[i % D.WARBANDS.length].id });
  const rng = new AG.RNG(i + 1);
  let steps = 0;
  let stuck = false;
  let stuckAt = '';
  while (!run.over && steps++ < 500 && !stuck) {
    if (!run.pending) {
      const offer = run.offer;
      onCards(run, i);
      if (offer[0].tier === 'mega') {
        R.endRun(run);
        continue;
      }
      // Cards come easiest first (easy, medium, elite; a boss's three the same way), so the
      // host picks by place: its usual tier, or the one card there is.
      let at = offer.length === 1 ? 0 : RANK[HOST];
      let res;
      let tries = 0;
      do {
        R.chooseChallenge(run, at);
        res = hostBattle(run);
        tries++;
        if (!res.won) {
          R.backToChoice(run);
          // The host must get through: after two losses it steps down a tier, and if even
          // the easy card will not fall (four more losses) it goes round the cards.
          if (offer.length > 1 && tries >= 2) at = Math.max(0, at - 1);
          if (offer.length > 1 && tries >= 6) at = [0, 1, 2, 0][Math.floor((tries - 6) / 2) % 4];
        }
      } while (!res.won && tries < (offer.length === 1 ? 40 : 30));
      if (!res.won) {
        stuck = true;
        stuckAt = `${offer[at].tier} ${offer.map((o) => o.enc.name).join(' / ')}`;
      }
      continue;
    }
    const p = run.pending;
    if (p.type === 'summit') {
      R.faceFinal(run);
      continue;
    }
    if (p.type === 'battle') {
      let res;
      let tries = 0;
      do {
        res = hostBattle(run);
        tries++;
      } while (!res.won && tries < 40);
      if (!res.won) stuck = true;
      continue;
    }
    if (p.type === 'reward') {
      if (p.bossRelics && !p.bossRelicTaken) R.takeBossRelic(run, p.bossRelics[0]);
      if (p.tome && !p.tomeTaken) R.takeTome(run, 0);
      if (!R.takeSpoil(run, rng.int(p.spoils.length))) R.skipSpoils(run);
      for (const sc of run.items.filter((it) => it.kind === 'scroll')) {
        const r = run.roster.find((u) => !u.enchant && D.eligible(u.type, ENCHANTS[sc.id]));
        if (r) R.applyScroll(run, sc.uid, r.id);
      }
      R.completeNode(run);
      continue;
    }
    if (p.type === 'shop') {
      for (let k = 0; k < p.stock.length; k++) if (R.canBuy(run, p.stock[k]) && rng.chance(0.5)) R.buy(run, k);
      R.completeNode(run);
      continue;
    }
    if (p.type === 'event') {
      const choices = R.eventChoices(run).filter((c) => c.enabled);
      const c = rng.pick(choices);
      const rid = c.pick ? (run.roster.find((u) => R.eventPickOk(run, c.pick, u)) || {}).id || null : null;
      let res = R.chooseEvent(run, c.id, rid);
      if (res == null) res = R.chooseEvent(run, choices[choices.length - 1].id, null);
      if (run.pending && run.pending.type === 'event') R.completeNode(run);
      continue;
    }
    throw new Error('unknown pending ' + p.type);
  }
  if (t0 && stuck) console.log(`  stuck at ${stuckAt || (run.pending && run.pending.enc ? run.pending.enc.name : '?')}; roster ${run.roster.map((r) => r.type).join(',')}`);
  if (t0) console.log(`host ${i} ${run.warband} ${run.won ? 'won' : stuck ? 'STUCK' : 'ended'} act ${run.act} supply ${R.supplyFor(run)} relics ${run.relics.length} losses ${run.stats.losses} · ${rows} rows · ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  return run;
}

if (require.main === module) main();
else module.exports = { AG, candFor, playOut, measure, hostCampaign, clone, P_TEMP, E_TEMP };
