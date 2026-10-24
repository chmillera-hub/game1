/* The battle AI. On each unit's turn it tries every square the unit can
   reach and every attack or ability it could use from there, simulating each
   on a cloned board. Results are scored by:
     material   - what every unit is worth, scaled by health and afflictions
     threat     - how much damage each side could deal on its next turns,
                  assigned greedily so attackers do not double-count a target
     approach   - how many turns each piece needs to get into the fight
   A cheap score prunes the candidates; the best few get the full score.
   Both sides use the same brain; mindless monsters simply ignore danger. */
(function (AG) {
  'use strict';
  const B = AG.B;
  const AI = (AG.AI = {});

  const PROFILES = {
    smart: { off: 0.4, def: 0.45, app: 1.0 },
    brute: { off: 0.15, def: 0.06, app: 1.6 },
  };
  const ROLE = {
    melee: { def: 0.85, app: 1.0 },
    tank: { def: 0.7, app: 0.95 },
    ranged: { def: 1.1, app: 0.8 },
    support: { def: 1.3, app: 0.55, supp: true },
    assassin: { def: 0.85, app: 1.1 },
  };
  const APP_W = 0.55;
  const CD_W = 0.3;
  const TOP_K = 12;

  function profileFor(u) {
    const base = PROFILES[u.ai] || PROFILES.smart;
    const r = ROLE[u.role] || ROLE.melee;
    return { off: base.off, def: base.def * r.def, app: base.app * r.app, supp: !!r.supp, brute: u.ai === 'brute' };
  }
  AI.profileFor = profileFor;

  // ------------------------------------------------------------- valuation
  function objMul(s, u) {
    if (s.objective && s.objective.uid === u.uid) return 3;
    return 1;
  }
  function baseWorth(s, u) { return u.value * objMul(s, u); }

  // What a unit leaves behind when it dies (or the extra life it still has).
  // Counting it up front means finishing such a unit is never scored as a loss.
  const childWorth = {};
  function worthOfDef(def) {
    if (childWorth[def] == null) childWorth[def] = B.computeValue(B.makeUnit(def, 0, 0, 0, {}));
    return childWorth[def];
  }
  function residual(u, v) {
    let r = 0;
    const p = u.pas;
    if (p.splitter) r += p.splitter.n * worthOfDef(p.splitter.into || 'slimeling');
    if (p.rebirth && !u.fl.reborn) r += worthOfDef('emberEgg');
    if (p.reassemble && !u.fl.reassembled) r += worthOfDef('bonePile');
    if (p.lichdom && !u.fl.lichUsed) r += v * 0.3;
    if (p.undying && !u.fl.undying) r += v * 0.1;
    if (p.secondWind && !u.fl.secondWind) r += v * 0.35;
    if (p.mirrorImage && !u.fl.mirror) r += v * 0.12;
    return r;
  }

  function worth(s, u) {
    if (!u.alive) return 0;
    const v = baseWorth(s, u);
    const eff = u.hp + u.shield * 0.8;
    const frac = eff >= u.maxHp ? 1 + Math.min(0.3, (eff - u.maxHp) / u.maxHp) * 0.5 : eff / u.maxHp;
    let w = residual(u, v) + v * (0.3 + 0.7 * frac);
    const st = u.st;
    if (st.frozen) w -= v * 0.2 * st.frozen.t;
    if (st.stunned) w -= v * 0.2;
    if (st.rooted) w -= v * 0.05;
    if (st.burn) w -= (v * 0.7 * Math.min(u.hp, st.burn.d * st.burn.t)) / u.maxHp;
    if (st.poison) w -= (v * 0.7 * Math.min(u.hp, st.poison.d * st.poison.t)) / u.maxHp;
    if (st.chill) w -= v * 0.03 * st.chill.a;
    if (st.haste) w += v * 0.03 * st.haste.a;
    if (st.marked) w -= v * 0.03 * st.marked.a;
    if (st.cursed) {
      w -= v * 0.05 * st.cursed.a;
      if (st.cursed.dot) w -= (v * 0.7 * Math.min(u.hp, st.cursed.dot * 2)) / u.maxHp;
    }
    if (st.taunt) w -= v * 0.04;
    if (st.stealth) w += v * 0.1;
    if (st.emp) w += st.emp.a * 0.45;
    if (st.weak) w -= st.weak.a * 0.4;
    if (st.corrode) w -= v * 0.05;
    for (const k in u.cd) if (u.cd[k] > 0) w -= CD_W * Math.min(u.cd[k], 4);
    return w;
  }
  AI.worth = worth;

  function material(s, side) {
    let m = 0;
    for (const u of s.units) {
      if (!u.alive) continue;
      const w = worth(s, u);
      m += u.side === side ? w : -w;
    }
    return m;
  }

  // ----------------------------------------------------------- reach/threat
  function attackRange(at) {
    if (!at) return 0;
    let r = 1;
    const one = (ap) => {
      if (ap.pattern === 'melee' || ap.pattern === 'melee4') return 1;
      if (ap.pattern === 'offsets') return 2;
      return ap.range || 1;
    };
    r = one(at);
    if (at.also) for (const ap of at.also) r = Math.max(r, one(ap));
    return r;
  }
  function moveRange(u) {
    const one = (mv) => {
      if (!mv) return 0;
      if (mv.type === 'leap') return 2;
      if (mv.type === 'none') return 0;
      return mv.n || 0;
    };
    return Math.max(one(u.mv), one(u.mv2));
  }
  AI.attackRange = attackRange;
  AI.moveRange = moveRange;

  function reachOf(s, u) {
    const list = [B.cellOf(s, u)];
    if (!u.st.rooted) for (const m of B.moveOptions(s, u)) list.push(m.i);
    const mask = new Uint8Array(s.board.n);
    for (const i of list) mask[i] = 1;
    return { list, mask };
  }

  function canAct(u) {
    return u.alive && !u.noTurn && !u.st.frozen && !u.st.stunned && (u.at || u.abil.length);
  }

  // Best single-turn damage A can deal to T next turn (0 if out of reach).
  function threatOn(s, A, T, reach) {
    let best = 0;
    if (A.at) {
      const origins = B.attackOrigins(s, A, T);
      let from = -1;
      for (const o of origins) if (reach.mask[o]) { from = o; break; }
      if (from >= 0) {
        let base = A.atk + (A.st.emp ? A.st.emp.a : 0) - (A.st.weak ? A.st.weak.a : 0);
        if (base < 1) base = 1;
        const d = B.calcDamage(s, A, T, base, { kind: 'attack', est: true, melee: B.isMelee(A.at), from, pierceArmor: !!A.at.ignoreArmor });
        best = d * (A.at.hits || 1);
      }
    }
    for (const ab of A.abil) {
      if ((A.cd[ab.id] || 0) > 1) continue;
      const Ad = AG.Abilities[ab.id];
      if (Ad.kind !== 'damage' || !ab.p.dmg) continue;
      const r = (ab.p.range || ab.p.r || 1) + (Ad.target === 'cell' ? 1 : 0);
      let ok = false;
      for (const i of reach.list) {
        if (AG.cheb(i % s.board.w, (i / s.board.w) | 0, T.x, T.y) <= r) { ok = true; break; }
      }
      if (!ok) continue;
      const d = B.calcDamage(s, A, T, ab.p.dmg, { kind: 'ability', est: true });
      if (d > best) best = d;
    }
    return best;
  }

  /* How much worth `side` could strip from the other side on its next turns.
     Attackers act in speed order and target greedily, tracking remaining
     health so two attackers do not both "kill" the same piece. */
  function potential(s, side, detail) {
    const atk = [], def = [];
    for (const u of s.units) {
      if (!u.alive) continue;
      if (u.side === side) { if (canAct(u)) atk.push(u); } else if (!u.st.stealth) def.push(u);
    }
    if (!def.length || !atk.length) return 0;
    atk.sort((a, b) => B.spd(s, b) - B.spd(s, a));
    const rem = {};
    for (const t of def) rem[t.uid] = t.hp + t.shield;
    let total = 0;
    for (const A of atk) {
      const reach = reachOf(s, A);
      let best = 0, bestT = null, bestD = 0;
      let forced = null;
      if (A.st.taunt) {
        const by = B.U(s, A.st.taunt.by);
        if (by && by.alive && threatOn(s, A, by, reach) > 0) forced = by;
      }
      for (const T of forced ? [forced] : def) {
        const r = rem[T.uid];
        if (r <= 0) continue;
        const d = threatOn(s, A, T, reach);
        if (d <= 0) continue;
        const dealt = Math.min(d, r);
        const v = baseWorth(s, T);
        const val = v * 0.7 * (dealt / T.maxHp) + (d >= r ? v * 0.3 : 0);
        if (val > best) { best = val; bestT = T; bestD = dealt; }
      }
      if (bestT) {
        rem[bestT.uid] -= bestD;
        total += best;
        if (detail) detail.push({ by: A.uid, on: bestT.uid, dmg: bestD, val: best });
      }
    }
    return total;
  }
  AI.potential = potential;

  // ------------------------------------------------------------ positioning
  function makeCtx(s, actor) {
    const side = actor.side;
    const ctx = { side, fields: {}, cover: [], foes: [] };
    for (const u of s.units) if (u.alive && u.side !== side) ctx.foes.push(u.uid);
    // Where could each enemy hit the actor next turn, and for how much?
    for (const id of ctx.foes) {
      const E = B.U(s, id);
      if (!canAct(E)) continue;
      const reach = reachOf(s, E);
      const mask = new Uint8Array(s.board.n);
      const probe = actor;
      let dmg = 0;
      if (E.at) {
        let base = E.atk + (E.st.emp ? E.st.emp.a : 0);
        dmg = B.calcDamage(s, E, probe, base, { kind: 'attack', est: true, melee: B.isMelee(E.at) }) * (E.at.hits || 1);
        coverMask(s, E, reach, mask, actor.uid);
      }
      for (const ab of E.abil) {
        if ((E.cd[ab.id] || 0) > 1) continue;
        const Ad = AG.Abilities[ab.id];
        if (Ad.kind !== 'damage' || !ab.p.dmg) continue;
        const r = (ab.p.range || ab.p.r || 1) + (Ad.target === 'cell' ? 1 : 0);
        for (const i of reach.list) markRadius(s, i, r, mask);
        dmg = Math.max(dmg, B.calcDamage(s, E, probe, ab.p.dmg, { kind: 'ability', est: true }));
      }
      if (dmg > 0) ctx.cover.push({ uid: id, mask, dmg });
    }
    ctx.potBefore = null;
    return ctx;
  }

  function markRadius(s, i, r, mask) {
    const b = s.board;
    const x0 = i % b.w, y0 = (i / b.w) | 0;
    for (let y = Math.max(0, y0 - r); y <= Math.min(b.h - 1, y0 + r); y++) {
      for (let x = Math.max(0, x0 - r); x <= Math.min(b.w - 1, x0 + r); x++) mask[y * b.w + x] = 1;
    }
  }

  // Squares E's basic attack could reach from anywhere it can move to.
  function coverMask(s, E, reach, mask, ignoreUid) {
    const b = s.board, w = b.w;
    const pats = [E.at].concat(E.at.also || []);
    for (const fi of reach.list) {
      const fx = fi % w, fy = (fi / w) | 0;
      for (const ap of pats) {
        switch (ap.pattern) {
          case 'melee':
          case 'melee4':
            for (const [dx, dy] of ap.pattern === 'melee4' ? AG.DIRS4 : AG.DIRS8) {
              const x = fx + dx, y = fy + dy;
              if (AG.inBounds(b, x, y)) mask[y * w + x] = 1;
            }
            break;
          case 'offsets':
            for (const [dx, dy] of ap.offsets || AG.KNIGHT) {
              const x = fx + dx, y = fy + dy;
              if (AG.inBounds(b, x, y)) mask[y * w + x] = 1;
            }
            break;
          case 'ranged':
          case 'lob': {
            const r = ap.range, mn = ap.minRange || 1;
            for (let y = Math.max(0, fy - r); y <= Math.min(b.h - 1, fy + r); y++) {
              for (let x = Math.max(0, fx - r); x <= Math.min(w - 1, fx + r); x++) {
                if (AG.cheb(x, y, fx, fy) < mn) continue;
                const j = y * w + x;
                if (ap.pattern === 'ranged' && ap.los !== false && !b.los[fi * b.n + j]) continue;
                mask[j] = 1;
              }
            }
            break;
          }
          case 'reach':
          case 'line':
            for (const [dx, dy] of AG.dirsFor(ap.dirs)) {
              let x = fx, y = fy;
              for (let k = 1; k <= ap.range; k++) {
                x += dx; y += dy;
                if (!AG.inBounds(b, x, y)) break;
                const j = y * w + x;
                if (b.terr[j] === AG.TER.WALL) break;
                mask[j] = 1;
                const id = s.occ[j];
                if (ap.pattern === 'line' && !ap.pierce && id && id !== E.uid && id !== ignoreUid) break;
              }
            }
            break;
          default:
            break;
        }
      }
    }
  }

  /* For the UI: squares unit u could move to, and squares it threatens
     (from where it stands, or from anywhere it can reach this turn). */
  AI.reachInfo = function (s, u, fromAnywhere) {
    const reach = reachOf(s, u);
    const mask = new Uint8Array(s.board.n);
    if (u.at) coverMask(s, u, fromAnywhere ? reach : { list: [B.cellOf(s, u)] }, mask, -1);
    for (const ab of u.abil) {
      const Ad = AG.Abilities[ab.id];
      if (Ad.kind !== 'damage' || !ab.p.dmg || !fromAnywhere) continue;
      const r = (ab.p.range || ab.p.r || 1) + (Ad.target === 'cell' ? 1 : 0);
      for (const i of reach.list) markRadius(s, i, r, mask);
    }
    const attack = [];
    for (let i = 0; i < mask.length; i++) if (mask[i] && s.board.terr[i] !== AG.TER.WALL && s.board.terr[i] !== AG.TER.VOID) attack.push(i);
    return { move: reach.list.slice(1), attack };
  };

  function field(s, ctx, foe, fly) {
    const key = foe.uid + (fly ? 'f' : 'w');
    let f = ctx.fields[key];
    if (!f) {
      f = ctx.fields[key] = AG.distField(s.board, foe.y * s.board.w + foe.x, fly);
    }
    return f;
  }

  // Turns this unit needs before it can attack anything.
  function engagement(s, u, ctx) {
    if (!u.at) return 0;
    const range = attackRange(u.at);
    const mr = moveRange(u);
    const here = u.y * s.board.w + u.x;
    let best = 99;
    for (const id of ctx.foes) {
      const E = B.U(s, id);
      if (!E.alive || E.st.stealth) continue;
      let d = field(s, ctx, E, u.flying)[here];
      if (d >= 999) d = AG.cheb(u.x, u.y, E.x, E.y) + 4;
      const need = Math.max(0, d - range);
      const turns = need === 0 ? 0 : mr > 0 ? need / mr : 20;
      if (turns < best) best = turns;
      if (best === 0) break;
    }
    return best === 99 ? 0 : Math.min(best, 8);
  }
  AI.engagement = engagement;

  function supportSpread(s, u) {
    // Healers and buffers want an ally within reach of their spells.
    let range = 0;
    for (const ab of u.abil) {
      const Ad = AG.Abilities[ab.id];
      if (Ad.kind === 'heal' || Ad.kind === 'buff' || Ad.kind === 'tempo') range = Math.max(range, ab.p.range || ab.p.r || 2);
    }
    if (!range) return 0;
    let best = 99;
    for (const o of s.units) {
      if (!o.alive || o === u || o.side !== u.side || o.object) continue;
      best = Math.min(best, AG.cheb(u.x, u.y, o.x, o.y));
    }
    return best === 99 ? 0 : Math.max(0, best - range);
  }

  function positional(s, side, ctx) {
    let p = 0;
    for (const u of s.units) {
      if (!u.alive || u.side !== side || u.noTurn) continue;
      const prof = profileFor(u);
      p -= prof.app * APP_W * engagement(s, u, ctx);
      if (prof.supp) p -= 0.25 * supportSpread(s, u);
      if (u.pas.promotion) {
        // Pawns like to march: a little credit for each rank gained.
        const b = s.board;
        let far = 0;
        for (let y = 0; y < b.h; y++) {
          const i = y * b.w + u.x;
          if ((side === 0 ? b.farP[i] : b.farE[i])) { far = Math.abs(y - u.y); break; }
        }
        p -= 0.12 * far;
      }
    }
    return p;
  }

  // ------------------------------------------------------------ evaluation
  function dangerAt(s2, ctx, u) {
    const i = u.y * s2.board.w + u.x;
    let d = 0;
    for (const c of ctx.cover) {
      const E = B.U(s2, c.uid);
      if (!E.alive || E.st.frozen || E.st.stunned) continue;
      if (c.mask[i]) d += c.dmg;
    }
    return d;
  }

  function quickEval(s2, side, prof, ctx, uid) {
    if (s2.over) return (s2.winner === side ? 1e5 : -1e5) + material(s2, side);
    let sc = material(s2, side);
    const u = B.U(s2, uid);
    if (u.alive) {
      const danger = dangerAt(s2, ctx, u);
      if (danger > 0) {
        const eff = u.hp + u.shield;
        const v = baseWorth(s2, u);
        sc -= prof.def * 1.6 * (v * 0.7 * Math.min(danger, eff) / u.maxHp + (danger >= eff ? v * 0.3 : 0));
      }
      sc -= prof.app * APP_W * engagement(s2, u, ctx);
    }
    return sc;
  }

  function fullEval(s2, side, prof, ctx) {
    if (s2.over) return (s2.winner === side ? 1e5 : -1e5) + material(s2, side);
    let sc = material(s2, side);
    sc += prof.off * potential(s2, side);
    sc -= prof.def * potential(s2, 1 - side);
    sc += positional(s2, side, ctx);
    return sc;
  }
  AI.evaluate = function (s, side) {
    const any = s.units.find((u) => u.alive && u.side === side) || s.units[0];
    const ctx = makeCtx(s, any);
    return fullEval(s, side, profileFor(any), ctx);
  };

  // ------------------------------------------------------------ candidates
  function applyAct(s2, u2, a) {
    if (a.k === 'atk') {
      const t = B.U(s2, a.t);
      if (t && t.alive) B.doAttack(s2, u2, t);
    } else B.useAbility(s2, u2, a.id, a.t);
  }

  function actOptions(s1, u1) {
    const acts = [null];
    if (u1.at) for (const t of B.attackTargets(s1, u1)) acts.push({ k: 'atk', t });
    for (const ab of u1.abil) {
      if (u1.cd[ab.id]) continue;
      const Ad = AG.Abilities[ab.id];
      for (const t of Ad.targets(s1, u1, ab.p)) acts.push({ k: 'ab', id: ab.id, t });
    }
    return acts;
  }

  function bestRetreat(s2, u2, ctx, prof) {
    const here = B.cellOf(s2, u2);
    let best = here, bestSc = -Infinity;
    const opts = [{ i: here }].concat(B.walkOptions(s2, u2, u2.pas.hitAndRun.n));
    for (const o of opts) {
      const ox = u2.x, oy = u2.y;
      // Score the square without mutating the state.
      u2.x = o.i % s2.board.w; u2.y = (o.i / s2.board.w) | 0;
      const sc = -dangerAt(s2, ctx, u2) * (prof.def + 0.2) - 0.4 * engagement(s2, u2, ctx);
      u2.x = ox; u2.y = oy;
      if (sc > bestSc + 1e-9) { bestSc = sc; best = o.i; }
    }
    return best;
  }

  // A hasted ally's best turn hardly depends on where the caster stands, so
  // plan it once per ally and replay it for every square the caster tries.
  function playHaste(s2, ally, cache) {
    let sub = cache[ally.uid];
    if (sub) {
      const dest = sub.mv;
      const ok = dest < 0 || !s2.occ[dest] || s2.occ[dest] === ally.uid;
      const tOk = !sub.act || sub.act.k !== 'atk' || (B.U(s2, sub.act.t) && B.U(s2, sub.act.t).alive);
      if (ok && tOk) { B.execPlan(s2, ally, sub); return sub; }
    }
    sub = AI.choose(s2, ally, { nested: true });
    if (!cache[ally.uid]) cache[ally.uid] = sub;
    B.execPlan(s2, ally, sub);
    return sub;
  }

  function enumerate(s, u, ctx, prof, nested) {
    const side = u.side;
    const here = B.cellOf(s, u);
    const dests = [{ i: here, k: 'stay' }].concat(B.moveOptions(s, u));
    const cands = [];
    const hasteCache = {};
    for (const d of dests) {
      const s1 = B.clone(s);
      const u1 = B.U(s1, u.uid);
      if (d.k !== 'stay') B.applyMove(s1, u1, d.i, d.k);
      if (s1.over || !u1.alive) {
        cands.push({ d, a: null, post: -1, s: s1, q: quickEval(s1, side, prof, ctx, u.uid) });
        continue;
      }
      for (const a of actOptions(s1, u1)) {
        const s2 = a ? B.clone(s1) : s1;
        const u2 = B.U(s2, u.uid);
        let post = -1;
        let hasted = null;
        if (a) {
          applyAct(s2, u2, a);
          if (a.k === 'atk' && u2.alive && !s2.over && u2.pas.hitAndRun && !u2.st.rooted) {
            post = bestRetreat(s2, u2, ctx, prof);
            if (post !== B.cellOf(s2, u2)) B.applyMove(s2, u2, post, 'walk');
            else post = -1;
          }
          if (a.k === 'ab' && a.id === 'haste' && !nested && !s2.over) {
            // Value an extra turn by actually playing it out.
            const ally = B.U(s2, a.t);
            const i = s2.extra.indexOf(ally.uid);
            if (i >= 0) s2.extra.splice(i, 1);
            if (ally.alive) hasted = playHaste(s2, ally, hasteCache);
          }
        }
        cands.push({ d, a, post, s: s2, hasted, q: quickEval(s2, side, prof, ctx, u.uid) });
      }
    }
    return cands;
  }

  /* Pick a plan for unit u: { mv, mk, act, post, reason, score }. */
  AI.choose = function (s, u, opts) {
    opts = opts || {};
    const side = u.side;
    const prof = profileFor(u);
    const ctx = makeCtx(s, u);
    const cands = enumerate(s, u, ctx, prof, opts.nested);
    cands.sort((a, b) => b.q - a.q);
    let pool;
    if (opts.nested) pool = cands.slice(0, 4);
    else {
      pool = cands.slice(0, TOP_K);
      // Keep a little variety: the best few of each kind of action, plus the
      // moves that bring this unit closest to the fight.
      const seen = {};
      for (const c of cands) {
        const key = c.a ? (c.a.k === 'atk' ? 'atk' : c.a.id) : 'none';
        seen[key] = (seen[key] || 0) + 1;
        if (seen[key] <= 2 && pool.indexOf(c) < 0) pool.push(c);
      }
      const adv = cands.filter((c) => !c.a && c.d.k !== 'stay');
      if (adv.length) {
        for (const c of adv) c.eng = engagement(c.s, B.U(c.s, u.uid), ctx);
        adv.sort((a, b) => a.eng - b.eng || b.q - a.q);
        for (const c of adv.slice(0, 2)) if (pool.indexOf(c) < 0) pool.push(c);
      }
    }
    let best = null;
    for (const c of pool) {
      c.f = fullEval(c.s, side, prof, ctx) + (c.d.k === 'stay' ? 0.01 : 0);
      if (!best || c.f > best.f + 1e-9) best = c;
    }
    const plan = {
      mv: best.d.k === 'stay' ? -1 : best.d.i,
      mk: best.d.k,
      act: best.a,
      post: best.post,
      score: best.f,
    };
    if (!opts.nested) {
      plan.reason = explain(s, u, best, ctx, prof);
      if (opts.debug) plan.debug = pool.map((c) => ({ d: c.d, a: c.a, q: c.q, f: c.f }));
    }
    return plan;
  };

  // ------------------------------------------------------------ explanation
  function nameOf(u) { return u.name; }
  function listNames(arr) {
    if (arr.length <= 1) return arr.join('');
    return arr.slice(0, -1).join(', ') + ' and ' + arr[arr.length - 1];
  }

  const VERB = {
    slash: 'strikes', smash: 'smashes', stab: 'stabs', claw: 'claws', bite: 'bites', gore: 'gores', fist: 'pummels',
    cleave: 'cleaves', whirl: 'whirls into', lance: 'lances', pierce: 'skewers', dart: 'pegs', arrow: 'shoots',
    smite: 'smites', arcane: 'blasts', bolt: 'blasts', fire: 'scorches', frost: 'frosts', lightning: 'zaps',
    shadow: 'withers', psychic: 'rattles', thorn: 'pricks', shell: 'shells', beam: 'beams', rock: 'pelts',
    goo: 'slimes', time: 'unravels', holy: 'smites', nature: 'lashes',
  };

  function explain(s, u, c, ctx, prof) {
    const s2 = c.s;
    const side = u.side;
    const kills = [], hurt = [], healed = [], shielded = [], cc = [], summoned = [], lostAllies = [];
    for (const o of s.units) {
      const o2 = B.U(s2, o.uid);
      if (!o.alive) continue;
      if (o.side !== side) {
        if (!o2.alive) kills.push(o);
        else if (o2.hp < o.hp || o2.shield < o.shield) hurt.push({ o, d: o.hp + o.shield - o2.hp - o2.shield });
        for (const k of ['frozen', 'stunned', 'rooted', 'taunt', 'cursed']) if (o2.st[k] && !o.st[k]) cc.push({ o, k });
      } else {
        if (!o2.alive && o.uid !== u.uid) lostAllies.push(o);
        if (o2.alive && o2.hp > o.hp) healed.push({ o, d: o2.hp - o.hp });
        if (o2.alive && o2.shield > o.shield) shielded.push({ o, d: o2.shield - o.shield });
      }
    }
    for (let i = s.units.length; i < s2.units.length; i++) {
      const n = s2.units[i];
      if (n.alive && n.side === side) summoned.push(n);
    }
    const a = c.a;
    const moved = c.d.k !== 'stay';
    let parts = [];

    if (c.hasted) {
      const ally = B.U(s, a.t);
      parts.push('Hastes ' + nameOf(ally) + ' for an extra turn' + (kills.length ? ', and it finishes ' + listNames(kills.map(nameOf)) + '.' : '.'));
      return parts.join(' ');
    }
    if (a && a.k === 'ab') {
      const Ad = AG.Abilities[a.id];
      const tgt = typeof a.t === 'number' && Ad.target !== 'cell' ? B.U(s, a.t) : null;
      switch (Ad.kind) {
        case 'heal':
          if (healed.length) parts.push(Ad.name + (healed[0].o.uid === u.uid ? ' on itself' : ' on ' + nameOf(healed[0].o)) + ' (+' + healed[0].d + ' HP).');
          break;
        case 'buff':
          if (shielded.length) parts.push(Ad.name + ': shields ' + listNames(shielded.map((x) => nameOf(x.o))) + '.');
          else if (Ad.name) parts.push(Ad.name + '.');
          break;
        case 'summon':
          parts.push(Ad.name + ': ' + (summoned.length ? summoned.length + ' ' + nameOf(summoned[0]) + (summoned.length > 1 ? 's' : '') + ' join the fight.' : 'reinforcements.'));
          break;
        case 'swap':
          if (tgt && tgt.side !== side) parts.push(Ad.name + ': drags ' + nameOf(tgt) + ' into our lines.');
          else if (tgt) parts.push(Ad.name + ' with ' + nameOf(tgt) + (dangerAt(s, ctx, tgt) > 0 ? ', pulling it out of danger.' : '.'));
          break;
        case 'cc': {
          const names = cc.map((x) => nameOf(x.o));
          const label = { frozen: 'Freezes', stunned: 'Stuns', rooted: 'Roots', taunt: 'Taunts', cursed: 'Hexes' };
          if (cc.length) {
            const k = cc[0].k;
            let why = '';
            const t0 = cc[0].o;
            const qpos = s.queue.indexOf(t0.uid);
            if (k === 'frozen' || k === 'stunned') why = qpos >= 0 && qpos <= 2 ? ' before it can act.' : ' to buy a turn.';
            else if (k === 'taunt') why = ' away from our back line.';
            else if (k === 'cursed') why = ' so the others can finish it.';
            else why = '.';
            parts.push(label[k] + ' ' + listNames(names) + why);
          } else parts.push(Ad.name + '.');
          break;
        }
        default:
          if (tgt && kills.indexOf(tgt) >= 0) parts.push(Ad.name + ' destroys ' + nameOf(tgt) + '.');
          else if (tgt) {
            const h = hurt.find((x) => x.o.uid === tgt.uid);
            parts.push(Ad.name + ' on ' + nameOf(tgt) + (h ? ' for ' + h.d : '') + '.');
          } else {
            const total = hurt.reduce((n, x) => n + x.d, 0);
            parts.push(Ad.name + (hurt.length || kills.length ? ' hits ' + AG.plural(hurt.length + kills.length, 'enemy').replace('enemys', 'enemies') + (total ? ' for ' + total + ' total' : '') + '.' : '.'));
          }
      }
    } else if (a && a.k === 'atk') {
      const t = B.U(s, a.t);
      const verb = VERB[(u.at && u.at.vfx) || 'slash'] || 'attacks';
      const h = hurt.find((x) => x.o.uid === t.uid);
      if (kills.indexOf(t) >= 0) parts.push((moved && u.mv.type === 'leap' ? 'Leaps in and ' : moved ? 'Closes in and ' : '') + (moved ? verb : verb[0].toUpperCase() + verb.slice(1)) + ' ' + nameOf(t) + ' down.');
      else parts.push((moved ? 'Moves up and ' + verb : verb[0].toUpperCase() + verb.slice(1)) + ' ' + nameOf(t) + (h ? ' for ' + h.d : '') + '.');
    }
    const extraKills = kills.filter((k) => !a || a.t !== k.uid);
    if (extraKills.length) parts.push('Takes out ' + listNames(extraKills.map(nameOf)) + '.');
    if (lostAllies.length) parts.push('(Costs us ' + listNames(lostAllies.map(nameOf)) + '.)');
    if (!a) {
      const u2 = B.U(s2, u.uid);
      const dBefore = dangerAt(s, ctx, u), dAfter = dangerAt(s2, ctx, u2);
      const eB = engagement(s, u, ctx), eA = engagement(s2, u2, ctx);
      if (!moved) parts.push(eB > 0 ? 'Holds position and waits for an opening.' : 'Holds the line.');
      else if (dAfter < dBefore && dBefore > 0) parts.push(dAfter === 0 ? 'Falls back out of reach.' : 'Repositions to a safer square.');
      else if (eA < eB) {
        let near = null, nd = 99;
        for (const id of ctx.foes) {
          const E = B.U(s, id);
          if (!E.alive) continue;
          const dd = AG.cheb(u2.x, u2.y, E.x, E.y);
          if (dd < nd) { nd = dd; near = E; }
        }
        parts.push('Advances' + (near ? ' on ' + nameOf(near) : '') + '.');
      } else parts.push('Shifts position.');
    } else if (c.post >= 0) parts.push('Then slips back.');
    if (u.pas.promotion && B.U(s2, u.uid).name !== u.name) parts.push('Promoted to ' + B.U(s2, u.uid).name + '!');
    void prof;
    return parts.join(' ') || 'Waits.';
  }
})(globalThis.AG = globalThis.AG || {});
