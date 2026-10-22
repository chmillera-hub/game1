// Enemy commander. Scores every (unit, move, action, facing) option by expected damage,
// kills, friendly fire and how exposed the unit ends up, then plays the best one.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const E = AG.Engine;
  const { DIRS, UNITS } = AG.Data;

  const STANCES = {
    aggressive: { approach: 2.4, risk: 0.6 },
    balanced: { approach: 1.6, risk: 0.9 },
    defensive: { approach: 0.35, risk: 1.1 },
  };

  // ------------------------------------------------------------ threat model

  // Treasure guardians sleep until someone comes near their treasure or strikes them.
  function dormant(s, u) {
    if (!u.bound || !u.post || u.hp < u.maxHp) return false;
    for (const v of s.units) {
      if (v.alive && v.team !== u.team && !v.nonCombat && Math.abs(v.x - u.post.x) + Math.abs(v.y - u.post.y) <= 3) return false;
    }
    return true;
  }

  function isArea(kind) {
    return kind === 'blast' || kind === 'line' || kind === 'cone' || kind === 'cross' || kind === 'nova' || kind === 'detonate';
  }

  function harmful(a) {
    return a.kind !== 'none' && a.left > 0 && !!(a.dmg || (a.fx && (a.fx.para || a.fx.poison)));
  }

  // Everything the opposing side could do on its next turn, one entry per unit.
  function buildSources(s, foeTeam) {
    const out = [];
    for (const v of s.units) {
      if (!v.alive || v.team !== foeTeam || v.nonCombat || dormant(s, v)) continue;
      const acts = v.acts.filter(harmful);
      if (!acts.length) continue;
      const delay = E.turnsUntilReady(v);
      const weight = delay === 0 ? 1 : delay === 1 ? 0.3 : 0;
      if (weight === 0) continue;
      // Reach as if it could move next turn (paralysis and roots wear off by then for weight>0 cases).
      const savedPara = v.para;
      const savedRoot = v.root;
      v.para = 0;
      v.root = Math.max(0, v.root - 1);
      const reach = E.reachable(s, v);
      v.para = savedPara;
      v.root = savedRoot;
      const list = [...reach.values()];
      const profiles = acts.map((a) => {
        const p = { a, area: isArea(a.kind) };
        if (p.area) p.cover = areaCover(s, v, a, list);
        return p;
      });
      out.push({ v, weight, reach, list, profiles });
    }
    return out;
  }

  // Tiles an area attacker could catch from any tile it can reach.
  function areaCover(s, v, a, list) {
    const cover = new Uint8Array(s.w * s.h);
    const mark = (tiles) => {
      for (const [x, y] of tiles) cover[E.idx(s, x, y)] = 1;
    };
    for (const r of list) {
      switch (a.kind) {
        case 'blast':
          mark(E.radiusTiles(s, r.x, r.y, a.range[1] + (a.pattern === 'square' ? 2 : 1)));
          break;
        case 'line':
        case 'cross':
          for (let d = 0; d < 4; d++) mark(E.lineTiles(s, r.x, r.y, d, a.len));
          break;
        case 'cone':
          for (let d = 0; d < 4; d++) mark(E.coneTiles(s, r.x, r.y, d, a.len));
          break;
        case 'nova':
        case 'detonate':
          mark(E.radiusTiles(s, r.x, r.y, a.radius));
          break;
      }
    }
    return cover;
  }

  // Tiles from which a direct attack could strike (x, y). Smoke hides it from afar.
  function directOrigins(s, src, a, x, y) {
    const [r0, r1] = a.range;
    const smoke = !!E.tileFx(s, x, y, 'smoke');
    const out = [];
    for (const r of src.list) {
      const d = Math.abs(r.x - x) + Math.abs(r.y - y);
      if (d >= r0 && d <= r1 && !(smoke && d > 1)) out.push(r);
    }
    return out;
  }

  function catFor(fx, fy, x, y, facing) {
    if (facing < 0) return 'front';
    const dx = fx - x;
    const dy = fy - y;
    const [ux, uy] = DIRS[facing];
    const a = dx * ux + dy * uy;
    const b = Math.abs(dx * uy - dy * ux);
    if (a > 0 && a >= b) return 'front';
    if (a < 0 && -a > b) return 'back';
    return 'side';
  }

  // Each foe strikes only one target, so later threats count for less.
  const STACK = [1, 0.6, 0.4, 0.25, 0.2, 0.15];
  function combine(list) {
    list.sort((a, b) => b - a);
    let t = 0;
    for (let i = 0; i < list.length; i++) t += list[i] * (STACK[i] || 0.1);
    return t;
  }

  // Expected damage u would take at (x, y) for each of the 4 facings.
  function dangerAt(ctx, u, x, y) {
    const per = [[], [], [], []];
    dangerParts(ctx, u, x, y, per);
    return per.map(combine);
  }

  function dangerParts(ctx, u, x, y, res) {
    const s = ctx.s;
    E.withUnitAt(s, u, x, y, () => {
      const savedF = u.facing;
      const ti = E.idx(s, x, y);
      for (const src of ctx.sources) {
        const v = src.v;
        const best = [0, 0, 0, 0];
        for (const prof of src.profiles) {
          const a = prof.a;
          if (prof.area) {
            if (!prof.cover[ti]) continue;
            let e = 0;
            if (a.dmg) e += E.calcHit(s, v, u, { act: a, dmgType: a.dmg }).dmg;
            if (a.fx && a.fx.para && !E.statusImmune(s, u, 'para')) e += 10;
            if (a.fx && a.fx.poison && !u.poison && !E.statusImmune(s, u, 'poison')) e += E.poisonDamage(v, a) * a.fx.poison * 0.6;
            e *= 0.75;
            for (let f = 0; f < 4; f++) best[f] = Math.max(best[f], e);
            continue;
          }
          if (!a.range || !a.dmg) continue;
          const origins = directOrigins(s, src, a, x, y);
          if (!origins.length) continue;
          // Expected damage per arc, computed once with a reference facing of north.
          u.facing = savedF < 0 ? -1 : 0;
          const moveDist = Math.max(0, Math.abs(v.x - x) + Math.abs(v.y - y) - 1);
          const exp = {};
          for (const [cat, fx, fy] of [
            ['front', x, y - 1],
            ['side', x + 1, y],
            ['back', x, y + 1],
          ]) {
            const r = E.calcHit(s, v, u, { act: a, fromX: fx, fromY: fy, moved: true, moveDist });
            exp[cat] = r.dmg * (1 - r.block);
          }
          if (a.kind === 'cleave' || a.kind === 'quake') {
            exp.front *= 1.15;
            exp.side *= 1.15;
            exp.back *= 1.15;
          }
          for (let f = 0; f < 4; f++) {
            for (const o of origins) {
              const e = exp[catFor(o.x, o.y, x, y, savedF < 0 ? -1 : f)];
              if (e > best[f]) best[f] = e;
            }
          }
        }
        for (let f = 0; f < 4; f++) if (best[f] > 0) res[f].push(best[f] * src.weight);
      }
      u.facing = savedF;
    });
    return res;
  }

  // Walking distance from every tile to the nearest foe (units ignored).
  function buildDistField(s, foes) {
    const n = s.w * s.h;
    const dist = new Int16Array(n).fill(99);
    const q = [];
    for (const v of foes) {
      const i = E.idx(s, v.x, v.y);
      dist[i] = 0;
      q.push(i);
    }
    let qi = 0;
    while (qi < q.length) {
      const i = q[qi++];
      const x = i % s.w;
      const y = (i - x) / s.w;
      for (const [dx, dy] of DIRS) {
        const nx = x + dx;
        const ny = y + dy;
        if (!E.inB(s, nx, ny)) continue;
        const ni = E.idx(s, nx, ny);
        if (dist[ni] <= dist[i] + 1 || s.terrain[ni] !== E.T_GRASS) continue;
        const o = E.at(s, nx, ny);
        if (o && o.type === 'wall') continue;
        dist[ni] = dist[i] + 1;
        q.push(ni);
      }
    }
    return dist;
  }

  function nearestFoe(ctx, x, y) {
    let best = null;
    let bd = 99;
    for (const v of ctx.foes) {
      const d = Math.abs(v.x - x) + Math.abs(v.y - y);
      if (d < bd) {
        bd = d;
        best = v;
      }
    }
    return { unit: best, d: bd };
  }

  // An object whose destruction wins the battle (banner, cage, gate, wagon, totem).
  function isGoal(u) {
    return u.goal;
  }

  // A building that still has reinforcements to send.
  function isSpawning(s, u) {
    return u.traits.has('spawner') && s.waves.some((w) => w.src === u.uid && w.state === 'pending');
  }

  function makeCtx(s, team, opts) {
    opts = opts || {};
    const foe = E.other(team);
    const stanceName = opts.stance || 'balanced';
    const st = STANCES[stanceName] || STANCES.balanced;
    // Objective objects count as targets to march on when breaking them wins the battle.
    // Treasure guardians and towers are left alone unless they get in the way.
    const foes = s.units.filter(
      (u) => u.alive && u.team === foe && !u.bound && !u.structure && (!u.nonCombat || (s.objective === 'destroy' && isGoal(u)) || isSpawning(s, u))
    );
    const ctx = {
      s,
      team,
      foe,
      opts,
      sources: buildSources(s, foe),
      distField: buildDistField(s, foes),
      allies: s.units.filter((u) => u.alive && u.team === team && !u.nonCombat && !u.structure),
      foes,
      objects: s.units.filter((u) => u.alive && u.team === team && u.goal),
      // Enemy buildings to bring down: goals of a 'destroy' battle, and anything still spawning.
      siege: s.units.filter((u) => u.alive && u.team === foe && ((s.objective === 'destroy' && u.goal && u.nonCombat) || isSpawning(s, u))),
      // Tiles where enemy reinforcements land at the end of the enemy's next turn.
      marks: new Set(
        s.waves
          .filter((w) => w.state === 'pending' && w.team === foe && w.marks)
          .flatMap((w) => w.marks.map(([mx, my]) => E.idx(s, mx, my)))
      ),
      foeRanged: s.units.some((u) => u.alive && u.team === foe && !u.nonCombat && u.acts.some((a) => a.range && a.range[1] >= 2 && a.dmg)),
      approach: st.approach,
      risk: st.risk,
    };
    if (stanceName === 'defensive') {
      // Defenders hold their line until the enemy closes in or time passes.
      let closest = 99;
      for (const a of ctx.allies) closest = Math.min(closest, nearestFoe(ctx, a.x, a.y).d);
      if (closest <= 5 || s.turn >= 10) ctx.approach = 1.2;
    }
    // Press harder as the battle drags on, and when we are the stronger side.
    const strength = (list) => list.reduce((t, u) => t + u.value * (u.hp / u.maxHp), 0);
    const ratio = strength(ctx.allies) / Math.max(1, strength(ctx.foes.filter((u) => !u.nonCombat)));
    ctx.approach *= (1 + 0.08 * Math.max(0, s.turn - 4)) * Math.min(1.5, Math.max(0.7, ratio));
    ctx.risk *= Math.min(1.3, Math.max(0.7, 1 / ratio));
    let cx = 0;
    let cy = 0;
    for (const a of ctx.allies) {
      cx += a.x;
      cy += a.y;
    }
    ctx.cx = ctx.allies.length ? cx / ctx.allies.length : s.w / 2;
    ctx.cy = ctx.allies.length ? cy / ctx.allies.length : s.h / 2;
    return ctx;
  }

  // ------------------------------------------------------------ evaluation

  function towardFacing(ctx, x, y) {
    const nf = nearestFoe(ctx, x, y);
    if (!nf.unit) return -1;
    return E.dirFromDelta(nf.unit.x - x, nf.unit.y - y);
  }

  function actSpan(a) {
    return a.range ? a.range[1] : a.radius || a.len || 1;
  }

  // How hard this unit could hit someone next turn from (x, y).
  function offense(ctx, u, x, y) {
    let best = 0;
    for (const a of u.acts) {
      if (a.left <= 0 || a.kind === 'none' || (!a.dmg && !a.fx)) continue;
      const reachR = u.move + actSpan(a) + (a.kind === 'blast' || a.kind === 'quake' ? 1 : 0);
      for (const f of ctx.foes) {
        const d = Math.abs(f.x - x) + Math.abs(f.y - y);
        if (d > reachR) continue;
        const base = a.fixed != null ? a.fixed : u.pow * (a.mult || 1);
        let dmg;
        if (a.dmg === 'phys') dmg = base * (1 - f.armor) * (1 - f.block * 0.5);
        else if (a.dmg === 'magic') dmg = base * (1 - f.res);
        else dmg = a.fx.poison ? E.poisonDamage(u, a) * 2 : 6;
        const val = dmg * (f.value / f.maxHp);
        if (val > best) best = val;
      }
    }
    return best * 0.35;
  }

  function primaryRange(u) {
    const a = u.act;
    return a.range ? a.range : null;
  }

  function positionValue(ctx, u, x, y) {
    const s = ctx.s;
    const dz = dangerAt(ctx, u, x, y);
    let facing = u.facing < 0 ? -1 : towardFacing(ctx, x, y);
    if (facing < 0 && u.facing >= 0) facing = u.facing;
    let danger = dz[Math.max(0, facing)];
    if (u.facing >= 0) {
      for (let f = 0; f < 4; f++) {
        if (dz[f] < danger - 0.25) {
          danger = dz[f];
          facing = f;
        }
      }
    }
    const hpv = u.value / u.maxHp;
    const expTaken = Math.max(0, danger * 0.85 - u.shield * 0.8);
    let v = -expTaken * hpv * ctx.risk + offense(ctx, u, x, y);
    if (expTaken >= u.hp) v -= u.value * 0.6 * ctx.risk;
    else if (expTaken >= u.hp * 0.6) v -= u.value * 0.15 * ctx.risk;
    if (u.boss) v *= 1.5;

    const role = UNITS[u.type].role;
    const flying = u.traits.has('flying');
    const nf = nearestFoe(ctx, x, y);
    const walk = flying ? nf.d : Math.min(ctx.distField[E.idx(s, x, y)], nf.d + 6);
    const a = u.act;
    switch (role) {
      case 'tank':
      case 'melee':
      case 'skirmisher':
        v -= walk * ctx.approach;
        break;
      case 'monster': {
        const ideal = a.kind === 'cone' ? 2 : 1;
        v -= Math.abs(nf.d - ideal) * ctx.approach;
        break;
      }
      case 'ranged': {
        const r = primaryRange(u) || [1, 1];
        v -= Math.abs(nf.d - r[1]) * 1.1 * Math.max(0.5, ctx.approach / 1.6);
        if (nf.d < r[0]) v -= 4;
        break;
      }
      case 'caster': {
        let ideal = 3;
        if (a.kind === 'blast' || a.kind === 'strike') ideal = a.range[1];
        else if (a.kind === 'nova') ideal = a.radius + 1;
        else if (a.kind === 'cross') ideal = 2;
        v -= Math.abs(nf.d - ideal) * 1.1 * Math.max(0.5, ctx.approach / 1.6);
        break;
      }
      case 'support': {
        const dc = Math.abs(x - ctx.cx) + Math.abs(y - ctx.cy);
        v -= dc * 0.8;
        if (a.kind === 'grow') v -= Math.abs(nf.d - 3) * 0.8;
        else if (nf.d < 3) v -= (3 - nf.d) * 3;
        if (a.kind === 'pray' || a.kind === 'drum') {
          for (const al of ctx.allies) if (al !== u && Math.abs(al.x - x) + Math.abs(al.y - y) <= a.radius) v += 0.8;
        }
        break;
      }
    }
    if (s.hold) {
      const dh = Math.abs(x - s.hold.x) + Math.abs(y - s.hold.y);
      if (dh === 0) v += u.team === 'P' ? 8 : 6;
      else if (dh === 1) v += 1.5;
    }
    if (u.post) {
      const dp = Math.abs(x - u.post.x) + Math.abs(y - u.post.y);
      if (dp > 1) v -= (dp - 1) * 6;
    }
    // Push on toward the buildings that must fall.
    if (ctx.siege.length && u.acts.some((x2) => x2.dmg)) {
      let dg = 99;
      for (const o of ctx.siege) dg = Math.min(dg, Math.abs(x - o.x) + Math.abs(y - o.y));
      const r = primaryRange(u);
      const ideal = r && r[1] >= 2 ? r[1] : 1;
      v -= Math.abs(dg - ideal) * 0.5 * ctx.approach;
    }
    // Stand on a marked tile to stop a reinforcement from arriving.
    if (ctx.marks.has(E.idx(s, x, y)) && !u.nonCombat && u.hp > E.BLOCK_DMG + 4) v += 7 - E.BLOCK_DMG * hpv * 0.4;
    if (ctx.objects.length && s.objective === 'destroy') {
      for (const o of ctx.objects) {
        if (Math.abs(x - o.x) + Math.abs(y - o.y) <= 2) {
          v += 1.5;
          break;
        }
      }
    }
    if (u.props.guard) {
      for (const al of ctx.allies) {
        if (al === u || Math.abs(al.x - x) + Math.abs(al.y - y) !== 1) continue;
        const r = UNITS[al.type].role;
        v += r === 'ranged' || r === 'caster' || r === 'support' ? 2.5 : 1;
      }
    }
    // Hazards underfoot, and powder kegs that the enemy could set off.
    if (!flying) {
      const f = E.tileFx(s, x, y);
      if (f && f.team !== u.team && f.kind === 'fire') v -= (f.dmg || 8) * hpv * 1.2;
      if (f && f.team !== u.team && f.kind === 'caltrops') v -= 6 * hpv + 3;
    }
    if (ctx.foeRanged) {
      for (const [bx, by] of E.radiusTiles(s, x, y, 1)) {
        const b = E.at(s, bx, by);
        if (b && b.alive && b.traits.has('volatile') && b !== u) v -= 0.12 * (b.props.boom || 15) * hpv * 2;
      }
    }
    return { score: v, facing, danger };
  }

  function paraValue(t) {
    const ready = E.turnsUntilReady(t) === 0 ? 1 : 0.6;
    return (t.pow * 0.8 + 6) * ready;
  }

  function shrubValue(ctx, u, tx, ty) {
    let v = 1;
    for (const m of ctx.foes) {
      const T = UNITS[m.type];
      if (m.move === 0 || !m.act.range || m.act.range[1] > 1 || m.traits.has('flying')) continue;
      const dm = Math.abs(m.x - tx) + Math.abs(m.y - ty);
      if (dm > m.move + 1) continue;
      for (const al of ctx.allies) {
        const r = UNITS[al.type].role;
        if (r !== 'ranged' && r !== 'caster' && r !== 'support') continue;
        const da = Math.abs(al.x - tx) + Math.abs(al.y - ty);
        if (dm + da === Math.abs(m.x - al.x) + Math.abs(m.y - al.y)) v += 2.5 * (T.cost / 3);
      }
    }
    return Math.min(v, 14);
  }

  // Our damage dealers that could reach a target next turn (for marks and roots).
  function alliesNear(ctx, t, r) {
    let n = 0;
    for (const al of ctx.allies) if (al.acts.some((a) => a.dmg) && Math.abs(al.x - t.x) + Math.abs(al.y - t.y) <= r) n++;
    return n;
  }

  function hazardValue(ctx, u, a, target) {
    const s = ctx.s;
    const tiles = E.patternTiles(s, a.pattern || 'single', target.x, target.y).filter(([x, y]) => s.terrain[E.idx(s, x, y)] !== E.T_ROCK);
    let v = 0;
    if (a.hz === 'smoke') {
      if (!ctx.foeRanged) return 0;
      for (const [x, y] of tiles) {
        if (E.tileFx(s, x, y, 'smoke')) continue;
        const o = E.at(s, x, y);
        if (!o || o.team !== u.team || o.nonCombat || o.structure) continue;
        let threatened = false;
        for (const src of ctx.sources) {
          if (src.weight < 1) continue;
          for (const prof of src.profiles) {
            if (prof.area || !prof.a.range || prof.a.range[1] < 2) continue;
            if (Math.abs(src.v.x - x) + Math.abs(src.v.y - y) <= prof.a.range[1] + src.v.move) threatened = true;
          }
        }
        if (threatened) v += 3 + (o.value / o.maxHp) * 4;
      }
    } else if (a.hz === 'fire') {
      for (const [x, y] of tiles) {
        if (s.terrain[E.idx(s, x, y)] !== E.T_GRASS) continue;
        const o = E.at(s, x, y);
        if (o && o.team !== u.team && !o.nonCombat && !o.structure && !o.traits.has('flying')) {
          v += Math.min(o.hp, (a.dmgFixed || 8) * (1 - o.res)) * (o.value / o.maxHp) * 1.3;
        }
        for (const f of ctx.foes) if (!f.nonCombat && Math.abs(f.x - x) + Math.abs(f.y - y) === 1) v += 0.3;
      }
    } else if (a.hz === 'caltrops') {
      for (const f of ctx.foes) {
        if (f.nonCombat || f.traits.has('flying') || f.move === 0) continue;
        const d = Math.abs(f.x - target.x) + Math.abs(f.y - target.y);
        if (d <= f.move + 1 && d >= 1) v = Math.max(v, 3 + (f.value / f.maxHp) * 2);
      }
    }
    return v;
  }

  function actionValue(ctx, u, target, c) {
    const s = ctx.s;
    const a = E.actOf(u, target);
    if (a.kind === 'hazard') return hazardValue(ctx, u, a, target) - (a.uses ? 1 : 0);
    if (a.kind === 'blink') return 0.6;
    if (a.kind === 'raise') {
      const sk = UNITS.skeleton;
      return sk.cost * 10 * 0.6 * 0.8 + 2;
    }
    if (a.kind === 'revive') {
      const d = s.byId[target.uid];
      return d ? d.value * (a.pct || 0.4) * 1.2 : 0;
    }
    const pv = E.previewAction(s, u, target, c);
    let v = 0;
    for (const e of pv.effects) {
      const t = s.byId[e.uid];
      const hpv = t.value / t.maxHp;
      if (e.self) {
        v -= u.value;
        continue;
      }
      const bossTarget = t.team !== u.team && ((s.objective === 'boss' && t.boss) || (s.objective === 'destroy' && isGoal(t)));
      if (e.dmg != null) {
        const p = 1 - e.block;
        const dealt = Math.min(e.dmg, t.hp + t.shield);
        let val = Math.max(0, dealt - t.shield) * hpv + Math.min(dealt, t.shield) * 0.2;
        if (e.kill) val += t.value * 0.8;
        if (bossTarget) val *= t.boss ? 2.5 : 3;
        else if (t.team !== u.team && isSpawning(s, t)) val *= 2;
        if (e.kill && t.traits.has('volatile')) val += boomValue(ctx, u, t);
        if (e.friendly) v -= p * val * 1.4;
        else v += p * val;
      }
      if (e.friendly) {
        if (e.heal) v += e.heal * hpv;
        if (e.cleanse) v += 6;
        if (e.shield) v += Math.min(e.shield, 12) * hpv * (ctx.sources.length ? 1 : 0.3);
        // Only one ally acts a turn, so a frenzy pays off for few of them.
        if (e.frenzy && t.frenzy === 0) v += t.pow * 0.25 * (t.wait <= 1 ? 0.5 : 0.25) * hpv * 2;
        // A cooldown of 1 runs out next turn anyway.
        if (e.rally) v += (t.wait >= 2 ? 5 : 0) + (t.para ? 6 : 0) + (t.root ? 2 : 0);
        continue;
      }
      if (t.nonCombat || t.structure) continue;
      const p = e.block != null ? 1 - e.block : 1;
      if (e.para && e.para !== 'resist') v += p * e.para * paraValue(t);
      if (e.poison && e.poison !== 'resist') {
        const fresh = t.poison ? Math.max(0, e.poison.turns - t.poison.turns) : e.poison.turns;
        v += p * (Math.min(fresh * e.poison.dmg, t.hp) * hpv * 0.85 + (t.poison ? 0 : 3));
      }
      if (e.burn) {
        const fresh = t.burn ? Math.max(0, e.burn.turns - t.burn.turns) : e.burn.turns;
        v += p * Math.min(fresh * e.burn.dmg * (1 - t.res), t.hp) * hpv * 0.8;
      }
      if (e.root && e.root !== 'resist' && t.move > 0 && t.root === 0) v += p * (2 + 0.3 * t.pow) * Math.min(2, e.root);
      if (e.weak && t.weak === 0 && t.acts.some((x) => x.dmg)) v += p * 0.3 * t.pow * 1.2 * (E.turnsUntilReady(t) === 0 ? 1 : 0.6);
      if (e.mark && t.mark === 0) v += p * 0.25 * 18 * hpv * Math.min(3, alliesNear(ctx, t, 5));
      if (e.knock === true) v += p * 2;
    }
    if (a.kind === 'grow') v += shrubValue(ctx, u, target.x, target.y);
    // Acting starts recovery; small cost so weak pokes don't lock down slow casters.
    v -= u.rec * u.pow * 0.08;
    if (a.uses) v -= 1.5;
    return v;
  }

  // What a dying powder keg or sapper would do to everyone beside it.
  function boomValue(ctx, u, t) {
    const s = ctx.s;
    let v = 0;
    for (const [x, y] of E.radiusTiles(s, t.x, t.y, 1)) {
      const o = E.at(s, x, y);
      if (!o || !o.alive || o === t || o.nonCombat) continue;
      const dmg = Math.min(o.hp, Math.round((t.props.boom || 15) * (1 - o.res)));
      const val = dmg * (o.value / o.maxHp) + (dmg >= o.hp ? o.value * 0.6 : 0);
      v += o.team === u.team ? -val * 1.4 : val;
    }
    return v;
  }

  // ------------------------------------------------------------ planning

  // The tile a unit ends up on after an act that moves it.
  function landing(a, t) {
    if (a.kind === 'leap' || a.kind === 'blink') return { x: t.x, y: t.y };
    if (a.kind === 'shadowstrike') return { x: t.bx, y: t.by };
    return null;
  }

  function planFor(ctx, u) {
    const s = ctx.s;
    const reach = E.reachable(s, u);
    const pos = new Map();
    const posAt = (r) => {
      const i = E.idx(s, r.x, r.y);
      let p = pos.get(i);
      if (!p) {
        p = positionValue(ctx, u, r.x, r.y);
        pos.set(i, p);
      }
      return p;
    };
    const start = reach.get(E.idx(s, u.x, u.y));
    const hold = posAt(start);
    const plans = [{ uid: u.uid, kind: 'hold', score: hold.score, facing: hold.facing, gain: 0 }];
    const holdScore = hold.score;
    const acts = [];
    for (let i = 0; i < u.acts.length; i++) if (E.actUsable(s, u, i)) acts.push(i);

    for (const r of reach.values()) {
      E.withUnitAt(s, u, r.x, r.y, () => {
        const p = posAt(r);
        if (r.d > 0) plans.push({ uid: u.uid, kind: 'move', to: r, score: p.score, facing: p.facing });
        for (const i of acts) {
          const a = u.acts[i];
          if (a.asMove && r.d > 0) continue;
          for (const t of E.targetsFrom(s, u, i)) {
            const av = actionValue(ctx, u, t, { moved: r.d > 0, moveDist: r.d });
            if (av <= 0.5) continue;
            const land = landing(a, t);
            let after = p;
            if (land) after = positionValue(ctx, u, land.x, land.y);
            plans.push({ uid: u.uid, kind: r.d > 0 ? 'moveAct' : 'act', to: r, target: t, score: av + after.score, facing: after.facing, av });
          }
        }
      });
    }

    // Act first, then reposition (hit and run).
    if (u.move > 0 && !u.traits.has('immobile') && u.root === 0) {
      const fromHere = [];
      for (const i of acts) if (!u.acts[i].asMove && !landing(u.acts[i], {})) fromHere.push(...E.targetsFrom(s, u, i));
      if (fromHere.length) {
        let bestPos = null;
        for (const r of reach.values()) {
          if (r.d === 0) continue;
          const p = posAt(r);
          if (!bestPos || p.score > bestPos.p.score) bestPos = { r, p };
        }
        if (bestPos && bestPos.p.score > hold.score + 1) {
          for (const t of fromHere) {
            const av = actionValue(ctx, u, t, { moved: false, moveDist: 0 });
            if (av <= 0.5) continue;
            plans.push({ uid: u.uid, kind: 'actMove', to: bestPos.r, target: t, score: av + bestPos.p.score, facing: bestPos.p.facing, av });
          }
        }
      }
    }
    for (const p of plans) p.gain = p.score - holdScore;
    plans.sort((a, b) => b.score - a.score);
    return plans;
  }

  // Pick the next activation for `team`, or null when nothing is worth doing.
  // opts: { stance, temp (randomness), rng }
  function chooseActivation(s, team, opts) {
    opts = opts || {};
    if (s.over || s.side !== team) return null;
    const ready = E.readyUnits(s, team).filter((u) => !dormant(s, u));
    if (!ready.length) return null;
    const ctx = makeCtx(s, team, opts);
    const candidates = [];
    const holds = [];
    for (const u of ready) {
      const plans = planFor(ctx, u);
      const best = plans[0];
      if (best.kind === 'hold' || best.gain < 0.75) {
        holds.push({ u, plan: plans.find((p) => p.kind === 'hold') });
        continue;
      }
      // Keep a few top options per unit for variety.
      for (const p of plans.slice(0, 3)) if (p.kind !== 'hold' && p.gain >= 0.75) candidates.push(p);
    }
    if (candidates.length) {
      candidates.sort((a, b) => b.gain - a.gain);
      const temp = opts.temp != null ? opts.temp : 1.2;
      const top = candidates[0].gain;
      const pool = candidates.filter((p) => p.gain >= top - temp * 3);
      const rng = opts.rng || s.rng;
      if (temp <= 0.01 || pool.length === 1) return pool[0];
      const weights = pool.map((p) => Math.exp((p.gain - top) / temp));
      let r = rng.next() * weights.reduce((a, b) => a + b, 0);
      for (let i = 0; i < pool.length; i++) {
        r -= weights[i];
        if (r < 0) return pool[i];
      }
      return pool[0];
    }
    // Nothing worth moving for: turn to face threats if that helps.
    for (const h of holds) {
      if (h.u.facing >= 0 && h.plan.facing >= 0 && h.plan.facing !== h.u.facing) {
        const dz = dangerAt(ctx, h.u, h.u.x, h.u.y);
        if (dz[h.u.facing] - dz[h.plan.facing] > 1) return { uid: h.u.uid, kind: 'turn', facing: h.plan.facing, score: 0, gain: 0 };
      }
    }
    return null;
  }

  // Carry out a plan through the engine. Returns false if it could not be applied.
  function executePlan(s, plan, opts) {
    const u = s.byId[plan.uid];
    if (!E.beginActivation(s, plan.uid)) return false;
    if (plan.kind === 'move' || plan.kind === 'moveAct') {
      if (!E.moveUnit(s, plan.uid, plan.to.x, plan.to.y)) {
        E.cancelActivation(s);
        return false;
      }
    }
    if (plan.kind === 'moveAct' || plan.kind === 'act' || plan.kind === 'actMove') {
      if (s.over || !u.alive) return true;
      if (!E.performAction(s, plan.uid, plan.target) && plan.kind === 'act') {
        E.cancelActivation(s);
        return false;
      }
    }
    if (s.over) return true;
    let facing = plan.facing;
    if (u.alive && plan.kind === 'actMove' && s.act && !s.act.moved) {
      const ctx = makeCtx(s, u.team, opts);
      let best = null;
      for (const r of E.reachable(s, u).values()) {
        if (r.d === 0) continue;
        const p = positionValue(ctx, u, r.x, r.y);
        if (!best || p.score > best.p.score) best = { r, p };
      }
      const stay = positionValue(ctx, u, u.x, u.y);
      if (best && best.p.score > stay.score + 0.5) {
        E.moveUnit(s, u.uid, best.r.x, best.r.y);
        facing = best.p.facing;
      } else facing = stay.facing;
    } else if (u.alive && (plan.kind === 'moveAct' || plan.kind === 'act' || plan.kind === 'actMove')) {
      // The board changed after the action; re-check which way to face.
      facing = smartFacing(s, u, opts);
    }
    if (s.act) E.finishActivation(s, facing);
    return true;
  }

  // Best facing for a unit on its current tile (also used as the player's default).
  function smartFacing(s, u, opts) {
    if (u.facing < 0) return -1;
    const ctx = makeCtx(s, u.team, opts);
    const dz = dangerAt(ctx, u, u.x, u.y);
    let facing = towardFacing(ctx, u.x, u.y);
    if (facing < 0) facing = u.facing;
    let danger = dz[facing];
    for (let f = 0; f < 4; f++) {
      if (dz[f] < danger - 0.25) {
        danger = dz[f];
        facing = f;
      }
    }
    return facing;
  }

  // The facing a player's unit takes on its own when its turn ends: toward the nearest
  // enemy fighter, awake ones first and the more valuable on a tie.
  function nearestFacing(s, u) {
    if (u.facing < 0) return -1;
    let best = null;
    for (const v of s.units) {
      if (!v.alive || v.team === u.team || v.nonCombat || (v.structure && !E.canDealDamage(v))) continue;
      const k = (dormant(s, v) ? 1000 : 0) + Math.abs(v.x - u.x) + Math.abs(v.y - u.y) - v.value / 10000;
      if (!best || k < best.k) best = { v, k };
    }
    const f = best ? E.dirFromDelta(best.v.x - u.x, best.v.y - u.y) : -1;
    return f < 0 ? u.facing : f;
  }

  // Tiles the opposing side can strike next turn (for the danger overlay).
  function threatMap(s, team) {
    const foe = E.other(team);
    const sources = buildSources(s, foe).filter((src) => src.weight >= 1);
    const map = new Uint8Array(s.w * s.h);
    for (const src of sources) {
      for (const prof of src.profiles) {
        if (prof.area) {
          for (let i = 0; i < map.length; i++) if (prof.cover[i]) map[i] = Math.max(map[i], 2);
          continue;
        }
        if (!prof.a.range) continue;
        const [r0, r1] = prof.a.range;
        const quake = prof.a.kind === 'quake';
        for (const r of src.list)
          for (const [x, y] of E.radiusTiles(s, r.x, r.y, r1 + (quake ? 1 : 0))) {
            const d = Math.abs(x - r.x) + Math.abs(y - r.y);
            if (d >= r0 || quake) map[E.idx(s, x, y)] = Math.max(map[E.idx(s, x, y)], 1);
          }
      }
    }
    return map;
  }

  // Where one unit could move and strike on its next turn (for inspecting enemies).
  function unitThreat(s, v) {
    const savedPara = v.para;
    const savedRoot = v.root;
    v.para = 0;
    v.root = 0;
    const reach = E.reachable(s, v);
    v.para = savedPara;
    v.root = savedRoot;
    const list = [...reach.values()];
    const map = new Uint8Array(s.w * s.h);
    for (const a of v.acts) {
      if (a.kind === 'none' || a.left <= 0 || !(a.dmg || a.fx)) continue;
      if (isArea(a.kind)) {
        const c = areaCover(s, v, a, list);
        for (let i = 0; i < map.length; i++) if (c[i]) map[i] = 1;
      } else if (a.range) {
        const [r0, r1] = a.range;
        const extra = a.kind === 'quake' ? 1 : 0;
        for (const r of list)
          for (const [x, y] of E.radiusTiles(s, r.x, r.y, r1 + extra)) {
            if (extra || Math.abs(x - r.x) + Math.abs(y - r.y) >= r0) map[E.idx(s, x, y)] = 1;
          }
      }
    }
    const hit = [];
    for (let i = 0; i < map.length; i++) if (map[i]) hit.push([i % s.w, Math.floor(i / s.w)]);
    return { move: list.map((r) => [r.x, r.y]), hit };
  }

  // Carry out a chosen plan as this side's turn, then hand over to the other side. With no
  // plan (or one that no longer works), the side passes.
  function runPlan(s, plan, opts) {
    if (plan && plan.kind === 'turn') {
      E.beginActivation(s, plan.uid);
      E.finishActivation(s, plan.facing);
    } else if (plan && !executePlan(s, plan, opts)) E.cancelActivation(s);
    if (!s.over) E.endTurn(s);
  }

  // One turn for `team`, played instantly (tests, simulations and fast-forward).
  function playTurn(s, team, opts) {
    if (s.over || s.side !== team) return;
    runPlan(s, chooseActivation(s, team, opts), opts);
  }

  AG.AI = { chooseActivation, executePlan, runPlan, smartFacing, nearestFacing, threatMap, unitThreat, playTurn, dangerAt, makeCtx, positionValue, dormant };
})(typeof window !== 'undefined' ? window : globalThis);
