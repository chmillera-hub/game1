/* Battle rules engine. Pure state + functions so the AI can clone a state,
   try an action, and score the result. When state.ev is an array, every
   change is also recorded as an event for the UI to animate. Combat has no
   randomness: the same setup always plays out the same way. */
(function (AG) {
  'use strict';
  const { FLOOR, WALL, PIT, VOID } = AG.TER;
  const B = (AG.B = {});

  const STORM_ROUND = 12;
  const MAX_ROUNDS = 24;
  // Enemies get tougher act by act; bosses are tuned by hand and skip this.
  AG.ACT_SCALE = { 1: { hp: 0, atk: 0 }, 2: { hp: 0.25, atk: 0 }, 3: { hp: 0.45, atk: 1 } };
  AG.TIER_SCALE = { elite: 0.15 };
  const SHATTER = 2; // bonus damage frozen units take from hits
  const SHIELD_CAP = 12;

  // ---------------------------------------------------------------- basics
  function emit(s, type, data) {
    if (!s.ev) return;
    data = data || {};
    data.type = type;
    s.ev.push(data);
  }
  B.emit = emit;

  function U(s, uid) { return s.units[uid - 1]; }
  B.U = U;
  B.at = function (s, i) { const id = s.occ[i]; return id ? s.units[id - 1] : null; };
  function cellOf(s, u) { return u.y * s.board.w + u.x; }
  B.cellOf = cellOf;
  B.xy = function (s, i) { return [i % s.board.w, (i / s.board.w) | 0]; };

  function stat(s, u) {
    if (!s.stats) return null;
    return s.stats[u.uid] || (s.stats[u.uid] = { dealt: 0, taken: 0, healed: 0, kills: 0, shielded: 0 });
  }

  // ------------------------------------------------------------ unit setup
  B.computeValue = function (u) {
    const d = AG.Units[u.def];
    if (d && d.value != null) return d.value * (u.boss ? 1 : 1);
    let v = 1.5 + u.maxHp * 0.32 + u.atk * 1.15 + u.spd * 0.18 + u.armor * 1.4;
    if (u.at) {
      const p = u.at.pattern;
      if (p === 'ranged' || p === 'line' || p === 'lob') v += u.atk * 0.35 + 0.5;
      if (u.at.hits > 1) v += u.atk * 0.8;
      if (u.at.splash || u.at.chain || u.at.whirl || u.at.pierce) v += 1;
    } else v *= 0.6;
    v += u.abil.length * 1.6;
    v += Object.keys(u.pas).length * 0.5;
    if (u.boss) v *= 1.6;
    return v;
  };

  B.makeUnit = function (defId, side, x, y, opts) {
    opts = opts || {};
    const d = AG.Units[defId];
    if (!d) throw new Error('Unknown unit ' + defId);
    const u = {
      uid: 0, def: defId, side, x, y,
      name: d.name, icon: d.icon,
      hp: d.hp, maxHp: d.hp, atk: d.atk, spd: d.spd, armor: d.armor || 0, shield: 0,
      mv: AG.deepCopy(d.move || { type: 'none' }),
      mv2: null,
      at: d.attack ? AG.deepCopy(d.attack) : null,
      flying: !!d.flying,
      abil: (d.abilities || []).map(function (a) {
        const id = typeof a === 'string' ? a : a.id;
        const A = AG.Abilities[id];
        if (!A) throw new Error('Unknown ability ' + id);
        return { id, p: Object.assign({}, A.p, typeof a === 'string' ? null : a.p) };
      }),
      pas: AG.deepCopy(d.passives || {}),
      immune: (d.immune || []).slice(),
      st: {}, cd: {}, fl: {}, ctr: {},
      alive: true, acted: false, moved: false, moveKind: null, moveDist: 0,
      tags: d.tags || [], role: d.role || 'melee', ai: d.ai || 'smart',
      summoned: !!opts.summoned, owner: opts.owner || 0,
      boss: !!d.boss, noTurn: !!d.noTurn, object: !!d.object, big: !!d.big,
      threat: d.threat || 2, rank: opts.rank || 0,
      talents: (opts.talents || []).slice(), rune: opts.rune || null,
      value: 0, order: 0, objective: false,
    };
    if (u.rank > 0) AG.applyRank(u, u.rank);
    for (const tid of u.talents) {
      const T = AG.Talents[tid];
      if (T && T.apply) T.apply(u);
    }
    if (u.rune) {
      const R = AG.Runes[u.rune];
      if (R && R.apply) R.apply(u);
    }
    if (opts.mods) applyMods(u, opts.mods);
    u.hp = u.maxHp;
    AG.refreshFlags(u);
    for (const a of u.abil) {
      const A = AG.Abilities[a.id];
      const init = a.p.initCd != null ? a.p.initCd : A.initCd || 0;
      if (init) u.cd[a.id] = init;
    }
    u.value = B.computeValue(u);
    return u;
  };

  function applyMods(u, m) {
    if (m.hp) u.maxHp += m.hp;
    if (m.atk) u.atk += m.atk;
    if (m.spd) u.spd += m.spd;
    if (m.armor) u.armor += m.armor;
    if (m.name) u.name = m.name;
    if (m.passives) u.pas = Object.assign({}, u.pas, AG.deepCopy(m.passives));
    if (m.shield) u.shield += m.shield;
  }

  B.addUnit = function (s, u) {
    u.uid = s.nextUid++;
    s.units.push(u);
    s.occ[cellOf(s, u)] = u.uid;
    stat(s, u);
    return u;
  };

  B.summon = function (s, defId, side, i, opts) {
    const b = s.board;
    if (s.occ[i] || !AG.standable(b, i, !!(AG.Units[defId] && AG.Units[defId].flying))) return null;
    const u = B.makeUnit(defId, side, i % b.w, (i / b.w) | 0, Object.assign({ summoned: true }, opts));
    u.order = 1000 + s.nextUid;
    if (opts && opts.hpPct) u.hp = Math.max(1, Math.round(u.maxHp * opts.hpPct));
    B.addUnit(s, u);
    u.acted = true; // joins the queue from the next round
    emit(s, 'summon', { uid: u.uid, unit: B.snap(u) });
    if (s.relics) relicHook(s, side, 'onSummon', u);
    return u;
  };

  B.snap = function (u) {
    return {
      uid: u.uid, def: u.def, side: u.side, x: u.x, y: u.y, name: u.name, icon: u.icon,
      hp: u.hp, maxHp: u.maxHp, shield: u.shield, atk: u.atk, alive: u.alive,
      st: Object.keys(u.st), summoned: u.summoned, boss: u.boss, object: u.object,
    };
  };

  // ----------------------------------------------------------- battle setup
  /* enc: encounter definition; army: [{def, x, y, talents, rune, rank}] for the
     player; opts: {relics:[ids], enemyRelics:[ids], record:true} */
  B.create = function (enc, army, opts) {
    opts = opts || {};
    const parsed = AG.parseBoard(enc.map, enc.legend);
    const b = parsed.board;
    const s = {
      board: b, units: [], occ: new Int32Array(b.n), nextUid: 1,
      round: 0, queue: [], extra: [], active: 0, over: false, winner: -1,
      ev: opts.record === false ? null : [],
      stats: opts.record === false ? null : {},
      objective: Object.assign({ type: 'rout' }, enc.objective),
      rules: { storm: enc.storm || STORM_ROUND, maxRounds: enc.maxRounds || MAX_ROUNDS },
      relics: [opts.relics || [], opts.enemyRelics || []],
      encounter: enc.id,
      turnCount: 0,
      flags: {},
      lastHit: 0,
      holdEnd: false,
    };
    for (const a of army) {
      const u = B.makeUnit(a.def, 0, a.x, a.y, { talents: a.talents, rune: a.rune, rank: a.rank });
      B.addUnit(s, u);
    }
    const sc = AG.ACT_SCALE[enc.act] || { hp: 0, atk: 0 };
    const hpBoost = sc.hp + (opts.ramp || 0) + (AG.TIER_SCALE[enc.tier] || 0) + (enc.boost || 0);
    for (const sp of parsed.spawns) {
      const u = B.makeUnit(sp.def, 1, sp.x, sp.y, { mods: sp.mods, talents: sp.talents });
      if (!u.boss && !u.object) {
        u.maxHp += Math.round(u.maxHp * hpBoost);
        u.hp = u.maxHp;
        if (u.at) u.atk += sc.atk;
        u.value = B.computeValue(u);
      }
      B.addUnit(s, u);
      if (sp.objective) { u.objective = true; s.objective.uid = u.uid; }
    }
    s.hpBoost = hpBoost;
    s.atkBoost = sc.atk;
    // Speed ties go to the player, then to whichever piece stands further forward.
    for (const u of s.units) {
      u.order = u.side === 0 ? u.y * 100 + u.x : (b.h - u.y) * 100 + u.x;
    }
    for (let side = 0; side < 2; side++) relicHook(s, side, 'battleStart');
    for (const u of s.units.slice()) passiveHook(s, u, 'battleStart');
    for (const u of s.units) { AG.refreshFlags(u); u.value = B.computeValue(u); u.hp = Math.min(u.hp, u.maxHp); }
    return s;
  };

  function relicHook(s, side, hook, a1, a2) {
    const list = s.relics[side];
    for (let i = 0; i < list.length; i++) {
      const R = AG.Relics[list[i]];
      if (R && R[hook]) R[hook](s, side, a1, a2);
    }
  }
  B.relicHook = relicHook;

  function passiveHook(s, u, hook, a1, a2, a3) {
    for (const k in u.pas) {
      const P = AG.Passives[k];
      if (P && P[hook]) P[hook](s, u, u.pas[k], a1, a2, a3);
    }
  }
  B.passiveHook = passiveHook;

  // ------------------------------------------------------------- cloning
  function cloneSt(st) {
    const o = {};
    for (const k in st) {
      const v = st[k];
      o[k] = typeof v === 'object' ? Object.assign({}, v) : v;
    }
    return o;
  }
  function cloneUnit(u) {
    const c = Object.assign({}, u);
    c.st = cloneSt(u.st);
    c.cd = Object.assign({}, u.cd);
    c.fl = Object.assign({}, u.fl);
    c.ctr = Object.assign({}, u.ctr);
    return c;
  }
  B.clone = function (s) {
    return {
      board: s.board, units: s.units.map(cloneUnit), occ: s.occ.slice(), nextUid: s.nextUid,
      round: s.round, queue: s.queue.slice(), extra: s.extra.slice(), active: s.active,
      over: s.over, winner: s.winner, ev: null, stats: null,
      objective: s.objective, rules: s.rules, relics: s.relics, encounter: s.encounter,
      turnCount: s.turnCount, sim: true, flags: Object.assign({}, s.flags), hpBoost: s.hpBoost, atkBoost: s.atkBoost,
      lastHit: s.lastHit, holdEnd: false,
    };
  };

  // --------------------------------------------------------------- speed
  B.spd = function (s, u) {
    let v = u.spd;
    if (u.st.chill) v -= u.st.chill.a;
    if (u.st.haste) v += u.st.haste.a;
    return v < 0 ? 0 : v;
  };
  function queueCmp(s) {
    return function (a, b) {
      const sa = B.spd(s, a), sb = B.spd(s, b);
      if (sa !== sb) return sb - sa;
      if (a.side !== b.side) return a.side - b.side;
      return a.order - b.order;
    };
  }
  B.buildQueue = function (s) {
    const list = s.units.filter((u) => u.alive && !u.noTurn);
    list.sort(queueCmp(s));
    s.queue = list.map((u) => u.uid);
  };
  B.resortQueue = function (s) {
    const list = [];
    for (const id of s.queue) { const u = U(s, id); if (u && u.alive) list.push(u); }
    list.sort(queueCmp(s));
    s.queue = list.map((u) => u.uid);
    emit(s, 'queue', { queue: s.queue.slice() });
  };
  // Upcoming turn order: rest of this round, then a projected next round.
  B.projectedQueue = function (s) {
    const now = s.extra.concat(s.queue).filter((id) => U(s, id).alive);
    const next = s.units.filter((u) => u.alive && !u.noTurn).sort(queueCmp(s)).map((u) => u.uid);
    return { now, next };
  };

  // ------------------------------------------------------------ statuses
  const CC = { frozen: 1, stunned: 1, rooted: 1, chill: 1 };
  B.isImmune = function (u, key) {
    if (u.immune.indexOf(key) >= 0 || u.immune.indexOf('all') >= 0) return true;
    if (CC[key] && u.pas.unstoppable) return true;
    if ((key === 'chill' || key === 'frozen') && u.pas.timeless) return true;
    return false;
  };
  B.addStatus = function (s, u, key, data) {
    if (!u.alive) return false;
    if (B.isImmune(u, key)) { emit(s, 'resist', { uid: u.uid, key }); return false; }
    const cur = u.st[key];
    switch (key) {
      case 'burn':
        u.st.burn = { d: Math.max(cur ? cur.d : 0, data.d), t: Math.max(cur ? cur.t : 0, data.t) };
        break;
      case 'poison':
        u.st.poison = { d: Math.min(5, (cur ? cur.d : 0) + data.d), t: Math.max(cur ? cur.t : 0, data.t) };
        break;
      case 'chill':
      case 'haste':
        u.st[key] = { a: Math.max(cur ? cur.a : 0, data.a), until: s.round + 1 };
        if (s.queue.indexOf(u.uid) >= 0) B.resortQueue(s);
        break;
      case 'marked':
      case 'cursed':
        u.st[key] = { a: Math.max(cur ? cur.a : 0, data.a), until: s.round + (data.r || 1) };
        if (data.dot) u.st[key].dot = Math.max(cur && cur.dot ? cur.dot : 0, data.dot);
        break;
      case 'frozen':
      case 'stunned':
      case 'rooted': {
        let t = data.t || 1;
        if (u.big && key !== 'rooted') t = 1;
        u.st[key] = { t: Math.max(cur ? cur.t : 0, t) };
        break;
      }
      case 'taunt':
        u.st.taunt = { by: data.by, t: 1 };
        break;
      case 'stealth':
        u.st.stealth = { t: data.t || 99 };
        break;
      case 'emp':
        u.st.emp = { a: (cur ? cur.a : 0) + data.a };
        break;
      default:
        u.st[key] = Object.assign({}, data);
    }
    emit(s, 'status', { uid: u.uid, key, st: Object.keys(u.st) });
    return true;
  };
  B.clearStatus = function (s, u, key) {
    if (u.st[key]) { delete u.st[key]; emit(s, 'status', { uid: u.uid, key, removed: true, st: Object.keys(u.st) }); }
  };
  B.cleanse = function (s, u) {
    let any = false;
    for (const k of ['burn', 'poison', 'chill', 'frozen', 'stunned', 'rooted', 'marked', 'cursed', 'taunt']) {
      if (u.st[k]) { delete u.st[k]; any = true; }
    }
    if (any) emit(s, 'status', { uid: u.uid, key: 'cleanse', st: Object.keys(u.st) });
  };
  function breakStealth(s, u) {
    if (u.st.stealth) B.clearStatus(s, u, 'stealth');
  }
  B.breakStealth = breakStealth;

  // --------------------------------------------------------- damage model
  B.armorOf = function (s, u) {
    let a = u.armor;
    for (const k in u.pas) {
      const P = AG.Passives[k];
      if (P && P.armorBonus) a += P.armorBonus(s, u, u.pas[k]);
    }
    if (u.st.corrode) a -= u.st.corrode.a || 1;
    return a;
  };

  /* Final damage of one hit before shields, with no side effects. Shared by
     real hits and by the AI's estimates (o.est = true). */
  // `parts`, when given, collects each named modifier ({label, amt}) so the
  // UI can show synergies such as Charge +2 or Shatter +2.
  B.calcDamage = function (s, src, tgt, base, o, parts) {
    let d = base;
    let v;
    if (src) {
      for (const k in src.pas) {
        const P = AG.Passives[k];
        if (P && P.outBonus && (v = P.outBonus(s, src, src.pas[k], tgt, o))) {
          d += v;
          if (parts) parts.push({ label: P.name, amt: v });
        }
      }
    }
    // Auras from nearby units (Rally, Guardian...)
    const units = s.units;
    for (let i = 0; i < units.length; i++) {
      const w = units[i];
      if (!w.alive || !w.aura) continue;
      for (const k in w.pas) {
        const P = AG.Passives[k];
        if (!P) continue;
        if (src && P.auraOut && w.side === src.side && (v = P.auraOut(s, w, w.pas[k], src, tgt, o))) {
          d += v;
          if (parts) parts.push({ label: P.name, amt: v });
        }
        if (P.auraIn && w.side === tgt.side && w !== tgt && (v = P.auraIn(s, w, w.pas[k], tgt, src, o))) {
          d += v;
          if (parts) parts.push({ label: P.name, amt: v });
        }
      }
    }
    if (tgt.st.marked) { d += tgt.st.marked.a; if (parts) parts.push({ label: 'Marked', amt: tgt.st.marked.a }); }
    if (tgt.st.cursed) { d += tgt.st.cursed.a; if (parts) parts.push({ label: 'Hex', amt: tgt.st.cursed.a }); }
    if (tgt.st.frozen) { d += SHATTER; if (parts) parts.push({ label: 'Shatter', amt: SHATTER }); }
    for (const k in tgt.pas) {
      const P = AG.Passives[k];
      if (P && P.inBonus && (v = P.inBonus(s, tgt, tgt.pas[k], src, o))) {
        d += v;
        if (parts) parts.push({ label: P.name, amt: v });
      }
    }
    if (!o.pierceArmor && (v = B.armorOf(s, tgt))) {
      d -= v;
      if (parts) parts.push({ label: 'Armor', amt: -v });
    }
    return d < 1 ? 1 : d;
  };

  /* Deal one hit. o.kind: attack | ability | splash | dot | storm | true.
     Returns damage dealt (including what shields absorbed). */
  B.hit = function (s, src, tgt, base, o) {
    if (!tgt || !tgt.alive || base <= 0) return 0;
    const raw = o.kind === 'dot' || o.kind === 'storm' || o.kind === 'true';
    const parts = s.ev && !raw ? [] : null;
    let dmg = raw ? base : B.calcDamage(s, src, tgt, base, o, parts);
    if (!raw) {
      for (const k in tgt.pas) {
        const P = AG.Passives[k];
        if (P && P.negate && P.negate(s, tgt, tgt.pas[k], src, o)) {
          emit(s, 'negate', { uid: tgt.uid, src: src ? src.uid : 0, label: P.name });
          return 0;
        }
      }
    }
    if (o.kind !== 'storm') s.lastHit = s.round;
    const absorbed = Math.min(tgt.shield, dmg);
    tgt.shield -= absorbed;
    tgt.hp -= dmg - absorbed;
    if (tgt.hp <= 0) {
      // Death prevention (Undying, Lichdom, the Lich's phylactery...)
      for (const k in tgt.pas) {
        const P = AG.Passives[k];
        if (P && P.preventDeath && P.preventDeath(s, tgt, tgt.pas[k], src, o)) break;
      }
    }
    emit(s, 'dmg', {
      uid: tgt.uid, src: src ? src.uid : 0, amt: dmg, absorbed, hp: tgt.hp, shield: tgt.shield,
      kind: o.kind, tag: o.tag || null, label: o.label || null, mods: parts && parts.length ? parts : null,
    });
    if (s.stats) {
      if (src) stat(s, src).dealt += dmg;
      stat(s, tgt).taken += dmg;
    }
    const lethal = tgt.hp <= 0;
    if (lethal) B.kill(s, tgt, src, o);
    if (src && src.alive && !raw) {
      for (const k in src.pas) {
        const P = AG.Passives[k];
        if (P && P.afterHit) P.afterHit(s, src, src.pas[k], tgt, dmg, o);
      }
      if (o.lifesteal) B.heal(s, src, src, Math.ceil(dmg * o.lifesteal), true);
    }
    if (!raw || o.kind === 'dot') {
      for (const k in tgt.pas) {
        const P = AG.Passives[k];
        if (P && P.afterHurt) P.afterHurt(s, tgt, tgt.pas[k], src, dmg, o);
      }
    }
    return dmg;
  };

  B.heal = function (s, src, u, amt, quiet) {
    if (!u.alive || amt <= 0) return 0;
    const before = u.hp;
    u.hp = Math.min(u.maxHp, u.hp + amt);
    const got = u.hp - before;
    let over = amt - got;
    if (src && src.alive && over > 0 && src.pas.crimsonFeast && src === u) {
      B.giveShield(s, u, Math.min(over, src.pas.crimsonFeast.max || 6), true);
    }
    if (got > 0) {
      emit(s, 'heal', { uid: u.uid, src: src ? src.uid : 0, amt: got, hp: u.hp, quiet: !!quiet });
      if (s.stats && src) stat(s, src).healed += got;
    }
    return got;
  };

  B.giveShield = function (s, u, amt, quiet) {
    if (!u.alive || amt <= 0) return 0;
    const before = u.shield;
    u.shield = Math.min(SHIELD_CAP, u.shield + amt);
    const got = u.shield - before;
    if (got > 0) emit(s, 'shield', { uid: u.uid, amt: got, shield: u.shield, quiet: !!quiet });
    return got;
  };

  B.kill = function (s, u, killer, o) {
    if (!u.alive) return;
    u.alive = false;
    u.hp = 0;
    s.occ[cellOf(s, u)] = 0;
    emit(s, 'death', { uid: u.uid, by: killer ? killer.uid : 0, how: o && o.kind });
    if (s.stats && killer && killer.side !== u.side) stat(s, killer).kills++;
    passiveHook(s, u, 'onDeath', killer, o);
    if (killer && killer.alive) passiveHook(s, killer, 'onKill', u, o);
    for (const w of s.units) {
      if (w.alive && w !== u) passiveHook(s, w, 'onAnyDeath', u, killer);
    }
    relicHook(s, u.side, 'onAllyDeath', u, killer);
    relicHook(s, 1 - u.side, 'onEnemyDeath', u, killer);
    B.checkEnd(s);
  };

  // ------------------------------------------------------- forced movement
  B.place = function (s, u, i, kind) {
    const b = s.board;
    const from = cellOf(s, u);
    if (s.occ[from] === u.uid) s.occ[from] = 0;
    const fx = u.x, fy = u.y;
    u.x = i % b.w;
    u.y = (i / b.w) | 0;
    s.occ[i] = u.uid;
    emit(s, 'move', { uid: u.uid, from: [fx, fy], to: [u.x, u.y], kind });
    checkPromotion(s, u);
  };

  // Knock a unit one square. Walls and other units stop it with a jolt;
  // chasms swallow anything that cannot fly.
  B.push = function (s, src, u, dx, dy) {
    if (!u.alive) return;
    if (u.pas.unmovable || u.big) { emit(s, 'resist', { uid: u.uid, key: 'push' }); return; }
    const b = s.board;
    const nx = u.x + dx, ny = u.y + dy;
    const j = ny * b.w + nx;
    const blockedEdge = !AG.inBounds(b, nx, ny) || b.terr[j] === VOID || b.terr[j] === WALL;
    if (blockedEdge) {
      emit(s, 'bump', { uid: u.uid, dir: [dx, dy] });
      B.hit(s, src, u, 2, { kind: 'true', label: 'Slam' });
      return;
    }
    const other = s.occ[j] ? U(s, s.occ[j]) : null;
    if (other) {
      emit(s, 'bump', { uid: u.uid, dir: [dx, dy] });
      B.hit(s, src, u, 1, { kind: 'true', label: 'Collision' });
      B.hit(s, src, other, 1, { kind: 'true', label: 'Collision' });
      return;
    }
    if (b.terr[j] === PIT && !u.flying) {
      B.place(s, u, j, 'push');
      emit(s, 'fall', { uid: u.uid });
      B.kill(s, u, src, { kind: 'fall' });
      return;
    }
    B.place(s, u, j, 'push');
  };

  B.swap = function (s, a, b2) {
    if (b2.pas.unmovable || b2.big) return false;
    const ia = cellOf(s, a), ib = cellOf(s, b2);
    const [ax, ay] = [a.x, a.y];
    a.x = b2.x; a.y = b2.y;
    b2.x = ax; b2.y = ay;
    s.occ[ia] = b2.uid;
    s.occ[ib] = a.uid;
    emit(s, 'swap', { a: a.uid, b: b2.uid, pa: [a.x, a.y], pb: [b2.x, b2.y] });
    checkPromotion(s, a);
    checkPromotion(s, b2);
    return true;
  };

  function checkPromotion(s, u) {
    const p = u.pas.promotion;
    if (!p || !u.alive) return;
    const i = cellOf(s, u);
    const far = u.side === 0 ? s.board.farP[i] : s.board.farE[i];
    if (!far) return;
    u.pas = Object.assign({}, u.pas);
    delete u.pas.promotion;
    u.name = p.name;
    u.icon = p.icon || u.icon;
    u.maxHp += p.hp || 0;
    u.hp = u.maxHp;
    u.atk += p.atk || 0;
    u.spd += p.spd || 0;
    if (p.move) u.mv = p.move;
    if (p.attack) u.at = p.attack;
    if (p.passives) Object.assign(u.pas, p.passives);
    AG.refreshFlags(u);
    u.value = B.computeValue(u);
    emit(s, 'promote', { uid: u.uid, unit: B.snap(u) });
  }

  // ------------------------------------------------------------- movement
  function genMoves(s, u, mv, out, seen) {
    const b = s.board, w = b.w;
    const start = cellOf(s, u);
    const fly = u.flying;
    function add(j, k) {
      if (seen[j]) return;
      seen[j] = 1;
      out.push({ i: j, k });
    }
    switch (mv.type) {
      case 'walk': {
        const n = mv.n;
        const dist = new Int8Array(b.n).fill(-1);
        const q = [start];
        dist[start] = 0;
        for (let h = 0; h < q.length; h++) {
          const i = q[h];
          if (dist[i] >= n) continue;
          const x = i % w, y = (i / w) | 0;
          const dirs = mv.dirs === 'orth' ? AG.DIRS4 : AG.DIRS8;
          for (let d = 0; d < dirs.length; d++) {
            const dx = dirs[d][0], dy = dirs[d][1];
            if (!AG.canStep(b, x, y, dx, dy)) continue;
            const j = (y + dy) * w + (x + dx);
            if (dist[j] >= 0) continue;
            const t = b.terr[j];
            if (t === WALL || t === VOID) continue;
            if (t === PIT && !fly) continue;
            const oc = s.occ[j];
            if (oc && !fly && U(s, oc).side !== u.side) continue; // enemies block walkers
            dist[j] = dist[i] + 1;
            q.push(j);
            if (!oc) add(j, 'walk');
          }
        }
        break;
      }
      case 'slide': {
        for (const [dx, dy] of AG.dirsFor(mv.dirs)) {
          let x = u.x, y = u.y;
          for (let k = 1; k <= mv.n; k++) {
            if (!AG.canStep(b, x, y, dx, dy)) break;
            x += dx; y += dy;
            const j = y * w + x;
            const t = b.terr[j];
            if (t === WALL || t === VOID) break;
            if (t === PIT && !fly) break;
            if (s.occ[j]) break;
            add(j, 'slide');
          }
        }
        break;
      }
      case 'leap': {
        for (const [dx, dy] of mv.offsets || AG.KNIGHT) {
          const x = u.x + dx, y = u.y + dy;
          if (!AG.inBounds(b, x, y)) continue;
          const j = y * w + x;
          if (!AG.standable(b, j, fly) || s.occ[j]) continue;
          add(j, 'leap');
        }
        if (mv.step) {
          for (const [dx, dy] of AG.DIRS8) {
            const x = u.x + dx, y = u.y + dy;
            if (!AG.inBounds(b, x, y) || !AG.canStep(b, u.x, u.y, dx, dy)) continue;
            const j = y * w + x;
            if (!AG.standable(b, j, fly) || s.occ[j]) continue;
            add(j, 'walk');
          }
        }
        break;
      }
      case 'blink':
      case 'shadow': {
        const n = mv.n;
        for (let y = Math.max(0, u.y - n); y <= Math.min(b.h - 1, u.y + n); y++) {
          for (let x = Math.max(0, u.x - n); x <= Math.min(w - 1, u.x + n); x++) {
            const j = y * w + x;
            if (j === start || s.occ[j] || !AG.standable(b, j, fly)) continue;
            if (mv.type === 'shadow' && !nextToEnemy(s, u, x, y)) continue;
            add(j, 'blink');
          }
        }
        if (mv.type === 'shadow') genMoves(s, u, { type: 'walk', n: 1 }, out, seen);
        break;
      }
      default:
        break;
    }
  }
  function nextToEnemy(s, u, x, y) {
    const b = s.board;
    for (const [dx, dy] of AG.DIRS8) {
      const nx = x + dx, ny = y + dy;
      if (!AG.inBounds(b, nx, ny)) continue;
      const id = s.occ[ny * b.w + nx];
      if (id) { const o = U(s, id); if (o.side !== u.side && !o.st.stealth) return true; }
    }
    return false;
  }

  // All squares this unit could move to this turn (not including staying put).
  B.moveOptions = function (s, u) {
    const out = [];
    if (!u.alive || u.st.rooted || u.st.frozen || u.st.stunned) return out;
    const seen = new Uint8Array(s.board.n);
    seen[cellOf(s, u)] = 1;
    genMoves(s, u, u.mv, out, seen);
    if (u.mv2) genMoves(s, u, u.mv2, out, seen);
    return out;
  };
  B.walkOptions = function (s, u, n) {
    const out = [];
    const seen = new Uint8Array(s.board.n);
    seen[cellOf(s, u)] = 1;
    genMoves(s, u, { type: 'walk', n }, out, seen);
    return out;
  };

  // Shortest walking path for animation.
  function walkPath(s, u, dest) {
    const b = s.board, w = b.w;
    const start = cellOf(s, u);
    const prev = new Int16Array(b.n).fill(-1);
    prev[start] = start;
    const q = [start];
    for (let h = 0; h < q.length; h++) {
      const i = q[h];
      if (i === dest) break;
      const x = i % w, y = (i / w) | 0;
      for (const [dx, dy] of AG.DIRS8) {
        if (!AG.canStep(b, x, y, dx, dy)) continue;
        const j = (y + dy) * w + (x + dx);
        if (prev[j] >= 0) continue;
        const t = b.terr[j];
        if (t === WALL || t === VOID || (t === PIT && !u.flying)) continue;
        const oc = s.occ[j];
        if (oc && !u.flying && U(s, oc).side !== u.side && j !== dest) continue;
        prev[j] = i;
        q.push(j);
      }
    }
    if (prev[dest] < 0) return [[dest % w, (dest / w) | 0]];
    const path = [];
    for (let i = dest; i !== start; i = prev[i]) path.push([i % w, (i / w) | 0]);
    path.reverse();
    return path;
  }

  B.applyMove = function (s, u, i, kind) {
    const from = cellOf(s, u);
    if (i === from) return;
    const path = s.ev && kind === 'walk' ? walkPath(s, u, i) : null;
    const fx = u.x, fy = u.y;
    s.occ[from] = 0;
    u.x = i % s.board.w;
    u.y = (i / s.board.w) | 0;
    s.occ[i] = u.uid;
    u.moved = true;
    u.moveKind = kind;
    u.moveDist = AG.cheb(fx, fy, u.x, u.y);
    emit(s, 'move', { uid: u.uid, from: [fx, fy], to: [u.x, u.y], kind, path });
    passiveHook(s, u, 'onMoved', kind);
    checkPromotion(s, u);
  };

  // ------------------------------------------------------- attack patterns
  const MELEE = { melee: 1, melee4: 1, offsets: 1, reach: 1 };
  B.isMelee = function (at) { return !!(at && MELEE[at.pattern]); };

  function patternTargets(s, u, ap, fi, out) {
    const b = s.board, w = b.w;
    const fx = fi % w, fy = (fi / w) | 0;
    const enemyAt = function (j) {
      const id = s.occ[j];
      if (!id) return null;
      const o = U(s, id);
      return o.side !== u.side && o.alive ? o : null;
    };
    const push = function (o) { if (o && out.indexOf(o.uid) < 0 && !o.st.stealth) out.push(o.uid); };
    switch (ap.pattern) {
      case 'melee':
      case 'melee4': {
        const dirs = ap.pattern === 'melee4' ? AG.DIRS4 : AG.DIRS8;
        for (const [dx, dy] of dirs) {
          const x = fx + dx, y = fy + dy;
          if (AG.inBounds(b, x, y)) push(enemyAt(y * w + x));
        }
        break;
      }
      case 'offsets':
        for (const [dx, dy] of ap.offsets || AG.KNIGHT) {
          const x = fx + dx, y = fy + dy;
          if (AG.inBounds(b, x, y)) push(enemyAt(y * w + x));
        }
        break;
      case 'ranged':
      case 'lob': {
        const r = ap.range, mn = ap.minRange || 1;
        for (const o of s.units) {
          if (!o.alive || o.side === u.side) continue;
          const d = AG.cheb(fx, fy, o.x, o.y);
          if (d < mn || d > r) continue;
          if (ap.pattern === 'ranged' && ap.los !== false && !b.los[fi * b.n + o.y * w + o.x]) continue;
          push(o);
        }
        break;
      }
      case 'reach':
      case 'line': {
        for (const [dx, dy] of AG.dirsFor(ap.dirs)) {
          let x = fx, y = fy;
          for (let k = 1; k <= ap.range; k++) {
            x += dx; y += dy;
            if (!AG.inBounds(b, x, y)) break;
            const j = y * w + x;
            const t = b.terr[j];
            if (t === WALL) break;
            if (t === VOID) continue;
            const id = s.occ[j];
            if (!id || id === u.uid) continue;
            const o = U(s, id);
            if (o.side !== u.side) {
              if (!o.st.stealth) { push(o); if (ap.pattern === 'line') break; }
            } else if (ap.pattern === 'line' && !ap.pierce) break;
          }
        }
        break;
      }
      default:
        break;
    }
  }

  // Enemies this unit could attack from square fi (defaults to where it stands).
  B.attackTargets = function (s, u, fi) {
    const out = [];
    if (!u.at) return out;
    if (fi == null) fi = cellOf(s, u);
    patternTargets(s, u, u.at, fi, out);
    if (u.at.also) for (const ap of u.at.also) patternTargets(s, u, ap, fi, out);
    if (u.st.taunt) {
      const by = u.st.taunt.by;
      if (out.indexOf(by) >= 0 && U(s, by).alive) return [by];
    }
    return out;
  };

  /* Squares from which unit a could hit target t with its basic attack, given
     the current board. Used by the AI to measure threats without moving. */
  function patternOrigins(s, a, ap, t, out) {
    const b = s.board, w = b.w;
    const tx = t.x, ty = t.y;
    const ti = ty * w + tx;
    switch (ap.pattern) {
      case 'melee':
      case 'melee4':
        for (const [dx, dy] of ap.pattern === 'melee4' ? AG.DIRS4 : AG.DIRS8) {
          const x = tx + dx, y = ty + dy;
          if (AG.inBounds(b, x, y)) out.push(y * w + x);
        }
        break;
      case 'offsets':
        for (const [dx, dy] of ap.offsets || AG.KNIGHT) {
          const x = tx - dx, y = ty - dy;
          if (AG.inBounds(b, x, y)) out.push(y * w + x);
        }
        break;
      case 'ranged':
      case 'lob': {
        const r = ap.range, mn = ap.minRange || 1;
        for (let y = Math.max(0, ty - r); y <= Math.min(b.h - 1, ty + r); y++) {
          for (let x = Math.max(0, tx - r); x <= Math.min(w - 1, tx + r); x++) {
            const d = AG.cheb(x, y, tx, ty);
            if (d < mn) continue;
            const j = y * w + x;
            if (ap.pattern === 'ranged' && ap.los !== false && !b.los[j * b.n + ti]) continue;
            out.push(j);
          }
        }
        break;
      }
      case 'reach':
      case 'line':
        for (const [dx, dy] of AG.dirsFor(ap.dirs)) {
          let x = tx, y = ty;
          for (let k = 1; k <= ap.range; k++) {
            x -= dx; y -= dy;
            if (!AG.inBounds(b, x, y)) break;
            const j = y * w + x;
            const tt = b.terr[j];
            if (tt === WALL) break;
            if (tt === VOID) continue;
            const id = s.occ[j];
            if (id && id !== a.uid && ap.pattern === 'line') {
              const o = U(s, id);
              if (!ap.pierce || o.side !== a.side) break; // something else would take the shot
              continue;
            }
            out.push(j);
          }
        }
        break;
      default:
        break;
    }
  }
  B.attackOrigins = function (s, a, t) {
    const out = [];
    if (!a.at) return out;
    patternOrigins(s, a, a.at, t, out);
    if (a.at.also) for (const ap of a.at.also) patternOrigins(s, a, ap, t, out);
    return out;
  };

  // ---------------------------------------------------------- attacking
  function onHitFx(s, u, t, fx) {
    if (!fx || !t.alive) return;
    if (fx.burn) B.addStatus(s, t, 'burn', fx.burn);
    if (fx.poison) B.addStatus(s, t, 'poison', fx.poison);
    if (fx.chill) {
      if (fx.freezeChilled && t.st.chill) B.addStatus(s, t, 'frozen', { t: 1 });
      B.addStatus(s, t, 'chill', { a: fx.chill });
    }
    if (fx.mark) B.addStatus(s, t, 'marked', { a: fx.mark });
    if (fx.root) B.addStatus(s, t, 'rooted', { t: 1 });
    if (fx.corrode) B.addStatus(s, t, 'corrode', { a: fx.corrode });
    if (fx.weaken) B.addStatus(s, t, 'weak', { a: fx.weaken });
    if (fx.knock && t.alive) B.push(s, u, t, AG.sign(t.x - u.x), AG.sign(t.y - u.y));
  }
  B.onHitFx = onHitFx;

  B.doAttack = function (s, u, t) {
    const at = u.at;
    if (!at || !t.alive) return;
    breakStealth(s, u);
    const melee = B.isMelee(at);
    emit(s, 'attack', { uid: u.uid, tgt: t.uid, from: [u.x, u.y], to: [t.x, t.y], vfx: at.vfx || (melee ? 'slash' : 'bolt'), melee });
    let base = u.atk;
    if (u.st.weak) { base -= u.st.weak.a; delete u.st.weak; }
    if (u.st.emp) { base += u.st.emp.a; delete u.st.emp; }
    if (base < 1) base = 1;
    const o = { kind: 'attack', melee, tag: at.tag, pierceArmor: !!at.ignoreArmor, lifesteal: at.lifesteal || 0 };
    const tx = t.x, ty = t.y, ti = cellOf(s, t);
    if (at.pattern === 'line' && at.pierce) {
      // A beam: everything hostile along the line.
      const dx = AG.sign(tx - u.x), dy = AG.sign(ty - u.y);
      let x = u.x, y = u.y;
      const b = s.board;
      for (let k = 1; k <= at.range; k++) {
        x += dx; y += dy;
        if (!AG.inBounds(b, x, y) || b.terr[y * b.w + x] === WALL) break;
        const id = s.occ[y * b.w + x];
        if (!id) continue;
        const o2 = U(s, id);
        if (o2.side !== u.side && o2.alive) {
          B.hit(s, u, o2, base, o);
          onHitFx(s, u, o2, at.fx);
        }
      }
    } else {
      const hits = at.hits || 1;
      for (let h = 0; h < hits && t.alive && u.alive; h++) {
        B.hit(s, u, t, base, o);
        onHitFx(s, u, t, at.fx);
        o.second = true;
      }
    }
    if (!u.alive) return;
    if (at.splash) {
      for (const [dx, dy] of AG.DIRS8) {
        const x = tx + dx, y = ty + dy;
        if (!AG.inBounds(s.board, x, y)) continue;
        const id = s.occ[y * s.board.w + x];
        if (!id || id === u.uid) continue;
        B.hit(s, u, U(s, id), at.splash, { kind: 'splash', tag: at.tag });
      }
      emit(s, 'aoe', { cells: [[tx, ty]], r: 1, vfx: at.vfx || 'blast' });
    }
    if (at.blast) {
      for (const o2 of AG.adjacentUnits(s, tx, ty, (q) => q.side !== u.side)) {
        B.hit(s, u, o2, at.blast, { kind: 'splash', tag: at.tag });
      }
    }
    if (at.chain) {
      const hitIds = [t.uid];
      let last = { x: tx, y: ty };
      let dmg = base;
      for (let k = 0; k < at.chain.n; k++) {
        dmg -= at.chain.falloff || 0;
        if (dmg < 1) break;
        let next = null;
        for (const o2 of s.units) {
          if (!o2.alive || o2.side === u.side || hitIds.indexOf(o2.uid) >= 0) continue;
          if (AG.cheb(o2.x, o2.y, last.x, last.y) > (at.chain.r || 1)) continue;
          if (!next || o2.hp < next.hp) next = o2;
        }
        if (!next) break;
        emit(s, 'chain', { from: [last.x, last.y], to: [next.x, next.y] });
        B.hit(s, u, next, dmg, { kind: 'attack', tag: at.tag, chained: true });
        if (at.chain.chill) B.addStatus(s, next, 'chill', { a: at.chain.chill });
        hitIds.push(next.uid);
        last = { x: next.x, y: next.y };
      }
    }
    if (at.whirl || at.cleave) {
      const others = [];
      for (const [dx, dy] of AG.DIRS8) {
        const x = u.x + dx, y = u.y + dy;
        if (!AG.inBounds(s.board, x, y)) continue;
        const id = s.occ[y * s.board.w + x];
        if (!id || id === t.uid) continue;
        const o2 = U(s, id);
        if (o2.side !== u.side && o2.alive) others.push(o2);
      }
      if (at.whirl) {
        if (others.length) emit(s, 'aoe', { cells: [[u.x, u.y]], r: 1, vfx: 'whirl' });
        for (const o2 of others) B.hit(s, u, o2, base, { kind: 'attack', melee: true, tag: at.tag, cleave: true });
      } else if (others.length) {
        others.sort((p, q) => p.hp - q.hp);
        B.hit(s, u, others[0], at.cleave, { kind: 'attack', melee: true, tag: at.tag, cleave: true });
      }
    }
    if (at.capture && !t.alive && u.alive && !s.occ[ti] && AG.standable(s.board, ti, u.flying)) {
      B.applyMove(s, u, ti, 'capture');
    }
  };

  // -------------------------------------------------------------- abilities
  B.abilityReady = function (u, ab) { return !u.cd[ab.id]; };

  B.useAbility = function (s, u, abId, target) {
    const ab = u.abil.find((a) => a.id === abId);
    const A = AG.Abilities[abId];
    if (!ab || !A) return;
    let cd = ab.p.cd != null ? ab.p.cd : A.cd;
    if (u.pas.spellweaver) cd = Math.max(1, cd - 1);
    u.cd[abId] = cd;
    let to = null;
    if (typeof target === 'number' && A.target === 'cell') to = B.xy(s, target);
    else if (typeof target === 'number' && U(s, target)) { const t = U(s, target); to = [t.x, t.y]; }
    emit(s, 'ability', { uid: u.uid, id: abId, name: A.name, from: [u.x, u.y], to, vfx: A.vfx || null });
    if (A.hostile) breakStealth(s, u);
    A.exec(s, u, target, ab.p);
  };

  // ------------------------------------------------------------- turn flow
  B.execPlan = function (s, u, plan) {
    if (plan.mv >= 0 && plan.mv !== cellOf(s, u)) B.applyMove(s, u, plan.mv, plan.mk);
    if (s.over || !u.alive) return;
    if (plan.act) {
      if (plan.act.k === 'atk') {
        const t = U(s, plan.act.t);
        if (t && t.alive) B.doAttack(s, u, t);
      } else if (plan.act.k === 'ab') {
        B.useAbility(s, u, plan.act.id, plan.act.t);
      }
    }
    if (s.over || !u.alive) return;
    if (plan.post >= 0 && plan.post !== cellOf(s, u) && !s.occ[plan.post]) B.applyMove(s, u, plan.post, 'walk');
  };

  B.startRound = function (s) {
    s.round++;
    emit(s, 'round', { round: s.round, storm: s.round >= s.rules.storm ? s.round - s.rules.storm + 1 : 0 });
    if (s.round > s.rules.maxRounds) {
      s.over = true;
      s.winner = s.objective.type === 'survive' ? 0 : 1;
      emit(s, 'timeout', {});
      return;
    }
    // Fatigue. A stalemate (3 rounds without anyone being hurt once the
    // fighting has started, 5 before) brings the Arcane Storm early.
    const quiet = s.lastHit > 0 ? 3 : 5;
    if (s.round < s.rules.storm && s.round - s.lastHit > quiet) {
      s.rules = Object.assign({}, s.rules, { storm: s.round });
      emit(s, 'stormEarly', { round: s.round });
    }
    if (s.round >= s.rules.storm) {
      const dmg = s.round - s.rules.storm + 1;
      emit(s, 'storm', { dmg });
      // The storm strikes everyone at once; the outcome is judged afterwards.
      s.holdEnd = true;
      for (const u of s.units.slice()) {
        if (u.alive && !u.object) B.hit(s, null, u, dmg, { kind: 'storm', label: 'Arcane Storm' });
      }
      s.holdEnd = false;
      if (B.checkEnd(s)) return;
    }
    for (const u of s.units.slice()) {
      if (u.alive) passiveHook(s, u, 'roundStart');
      if (s.over) return;
    }
    relicHook(s, 0, 'roundStart');
    relicHook(s, 1, 'roundStart');
    for (const u of s.units) u.acted = false;
    B.buildQueue(s);
    relicHook(s, 0, 'afterQueue');
    relicHook(s, 1, 'afterQueue');
    emit(s, 'queue', { queue: s.queue.slice(), fresh: true });
  };

  B.endRound = function (s) {
    for (const u of s.units.slice()) {
      if (u.alive) passiveHook(s, u, 'roundEnd');
      if (s.over) return;
    }
    for (const u of s.units) {
      if (!u.alive) continue;
      for (const k of ['chill', 'haste', 'marked', 'cursed']) {
        if (u.st[k] && u.st[k].until <= s.round) B.clearStatus(s, u, k);
      }
    }
    if (s.objective.type === 'survive' && s.round >= s.objective.rounds) {
      s.over = true;
      s.winner = 0;
      emit(s, 'survived', {});
    }
  };

  // Returns true if the unit loses this turn.
  B.startTurn = function (s, u) {
    u.moved = false;
    u.moveKind = null;
    u.moveDist = 0;
    for (const k in u.cd) if (u.cd[k] > 0) u.cd[k]--;
    if (u.st.burn) {
      const b = u.st.burn;
      B.hit(s, null, u, b.d, { kind: 'dot', tag: 'fire', label: 'Burn' });
      if (u.st.burn && --u.st.burn.t <= 0) B.clearStatus(s, u, 'burn');
      if (!u.alive || s.over) return true;
    }
    if (u.st.poison) {
      B.hit(s, null, u, u.st.poison.d, { kind: 'dot', tag: 'poison', label: 'Poison' });
      if (u.st.poison && --u.st.poison.t <= 0) B.clearStatus(s, u, 'poison');
      if (!u.alive || s.over) return true;
    }
    if (u.st.cursed && u.st.cursed.dot) {
      const src = null;
      B.hit(s, src, u, u.st.cursed.dot, { kind: 'dot', tag: 'shadow', label: 'Agony' });
      if (!u.alive || s.over) return true;
    }
    passiveHook(s, u, 'turnStart');
    if (!u.alive || s.over) return true;
    if (u.st.frozen) {
      emit(s, 'skip', { uid: u.uid, why: 'frozen' });
      if (--u.st.frozen.t <= 0) B.clearStatus(s, u, 'frozen');
      return true;
    }
    if (u.st.stunned) {
      emit(s, 'skip', { uid: u.uid, why: 'stunned' });
      if (--u.st.stunned.t <= 0) B.clearStatus(s, u, 'stunned');
      return true;
    }
    return false;
  };

  B.endTurn = function (s, u) {
    u.acted = true;
    if (u.st.rooted && --u.st.rooted.t <= 0) B.clearStatus(s, u, 'rooted');
    if (u.st.taunt && --u.st.taunt.t <= 0) B.clearStatus(s, u, 'taunt');
    passiveHook(s, u, 'turnEnd');
  };

  B.checkEnd = function (s) {
    if (s.over) return true;
    if (s.holdEnd) return false;
    let p = false, e = false;
    for (const u of s.units) {
      if (!u.alive) continue;
      if (u.side === 0) p = true;
      else e = true;
    }
    if (s.objective.type === 'assassinate' && s.objective.uid && !U(s, s.objective.uid).alive) e = false;
    if (!e) { s.over = true; s.winner = 0; }
    else if (!p) { s.over = true; s.winner = 1; }
    if (s.over) emit(s, 'end', { winner: s.winner });
    return s.over;
  };

  /* Advance the battle by one unit's turn (or a round change). The AI picks
     the plan. Returns a small record; events accumulate in s.ev. */
  B.step = function (s) {
    if (s.over) return null;
    if (s.round === 0 || (s.queue.length === 0 && s.extra.length === 0)) {
      if (s.round > 0) B.endRound(s);
      if (!s.over) B.startRound(s);
      return { kind: 'round', round: s.round };
    }
    const extra = s.extra.length > 0;
    const uid = extra ? s.extra.shift() : s.queue.shift();
    const u = U(s, uid);
    if (!u || !u.alive) return B.step(s);
    s.active = uid;
    s.turnCount++;
    emit(s, 'turn', { uid, extra, queue: s.queue.slice() });
    const skipped = B.startTurn(s, u);
    let plan = null;
    if (!skipped && u.alive && !s.over) {
      plan = AG.AI.choose(s, u);
      emit(s, 'think', { uid, reason: plan.reason, score: plan.score, alts: plan.alts, mv: plan.mv });
      B.execPlan(s, u, plan);
    }
    if (u.alive && !s.over) B.endTurn(s, u);
    s.active = 0;
    B.checkEnd(s);
    return { kind: 'turn', uid, plan, skipped };
  };

  // Run a whole battle with no animation (sandbox previews, tests).
  B.runToEnd = function (s, maxSteps) {
    maxSteps = maxSteps || 5000;
    let n = 0;
    while (!s.over && n++ < maxSteps) {
      B.step(s);
      if (s.ev) s.ev.length = 0;
    }
    return s.winner;
  };
})(globalThis.AG = globalThis.AG || {});
