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
    return a.kind !== 'none' && a.left > 0 && !!(a.dmg || (a.fx && (a.fx.para || a.fx.poison || a.fx.hold)));
  }

  // How many of its side's turns pass before a unit acts: its cooldown and paralysis, or
  // in a queue battle its place in the rotation (cached for the turn being planned).
  const delayCache = new WeakMap();
  function delayOf(s, v) {
    if (!s.queue) return E.turnsUntilReady(v);
    let c = delayCache.get(s);
    if (!c || c.ply !== s.ply || c.due !== s.due) {
      c = { ply: s.ply, due: s.due, map: new Map() };
      for (const team of ['P', 'E']) {
        const n = s.units.filter((u) => u.team === team && E.inQueue(u)).length * 2 + 1;
        E.upcoming(s, team, n).forEach((x, i) => {
          if (x.uid && !c.map.has(x.uid)) c.map.set(x.uid, i);
        });
      }
      delayCache.set(s, c);
    }
    return c.map.has(v.uid) ? c.map.get(v.uid) : 99;
  }

  // How much a foe's reach counts: whoever acts next fully; in a queue battle the units
  // behind it in the rotation count less the longer they wait.
  function threatWeight(s, delay) {
    if (s.queue) return delay === 0 ? 1 : delay === 1 ? 0.6 : delay === 2 ? 0.4 : delay < 99 ? 0.25 : 0;
    return delay === 0 ? 1 : delay === 1 ? 0.3 : 0;
  }

  // Everything the opposing side could do on its next turns, one entry per unit.
  function buildSources(s, foeTeam) {
    const out = [];
    for (const v of s.units) {
      if (!v.alive || v.team !== foeTeam || v.nonCombat || dormant(s, v)) continue;
      const acts = v.acts.filter(harmful);
      if (!acts.length) continue;
      const delay = delayOf(s, v);
      const weight = threatWeight(s, delay);
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
        case 'charge':
          for (let d = 0; d < 4; d++) mark(E.lineTiles(s, r.x, r.y, d, a.len));
          break;
        case 'cone':
          for (let d = 0; d < 4; d++) mark(E.coneTiles(s, r.x, r.y, d, a.len, a.fan));
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
            if (a.fx && a.fx.poison && !u.poison && !E.statusImmune(s, u, 'poison')) e += E.poisonDamage(v, a) * (1 - u.res) * a.fx.poison * 0.6;
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
  function buildDistField(s, foes, team) {
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
        // Nobody walks through a building, a keg or a thicket, its own side's included: a
        // garrison goes round its gate, not up against it.
        const o = E.at(s, nx, ny);
        if (o && (o.structure || o.traits.has('object') || (o.nonCombat && o.traits.has('immobile'))) && !(o.team === team && o.traits.has('opens'))) continue;
        dist[ni] = dist[i] + 1;
        q.push(ni);
      }
    }
    return dist;
  }

  function nearestFoe(ctx, x, y) {
    let best = null;
    let bd = 99;
    for (const v of ctx.chase || ctx.foes) {
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

  // ------------------------------------------------------------ priority target

  // A target the player has told their army to go all out for: an enemy unit or building
  // to destroy ({ uid }), or loot to take ({ loot: id }). Null once it is gone or taken.
  function focusOf(s, team, f) {
    if (!f) return null;
    if (f.uid) {
      const v = s.byId[f.uid];
      return v && v.alive && v.team !== team ? { unit: v, x: v.x, y: v.y } : null;
    }
    if (f.loot != null && team === 'P') {
      const l = (s.loot || []).find((x) => x.id === f.loot && !x.taken);
      return l ? { loot: l, x: l.x, y: l.y } : null;
    }
    // The shrine to hold: it stays the priority until the battle is won.
    if (f.hold && s.hold && !s.hold.done) return { hold: true, x: s.hold.x, y: s.hold.y };
    // A spot on open ground to gather at: it stays the priority until cleared.
    if (f.tile && team === 'P') return { tile: true, x: f.x, y: f.y };
    // One of your own units to rally on: the army gathers around it wherever it goes.
    if (f.ally) {
      const v = s.byId[f.ally];
      return v && v.alive && v.team === team ? { tile: true, ally: v, x: v.x, y: v.y } : null;
    }
    return null;
  }

  // Loot the player's army goes for on its own: worth more than an ordinary hit, less than
  // a kill. Units drift toward it while it lies there (LOOT_PULL a tile).
  const LOOT_VALUE = { chest: 18, tome: 20, relic: 24 };
  const LOOT_PULL = 0.5;

  // How much a tile costs a unit for being far from the priority target: walking distance
  // to loot, or distance beyond striking range of a unit.
  const FOCUS_PULL = 5;
  function focusPull(ctx, u, x, y) {
    const f = ctx.focus;
    const flat = Math.abs(x - f.x) + Math.abs(y - f.y);
    const walk = u.traits.has('flying') ? flat : Math.min(ctx.focusField[E.idx(ctx.s, x, y)], flat + 6);
    if (f.loot) return walk * FOCUS_PULL;
    // The shrine: one unit stands on it and stays there; the rest gather around to guard it.
    if (f.hold) return flat === 0 ? -120 : Math.max(0, walk - 1) * FOCUS_PULL;
    // A spot on open ground: everyone huddles as close to it as they can get.
    if (f.tile) return walk * FOCUS_PULL;
    let best = null;
    for (const a of u.acts) if (a.dmg && a.kind !== 'none' && a.left > 0 && (!best || actSpan(a) > actSpan(best))) best = a;
    // Units that cannot hurt it tag along.
    if (!best) return walk * FOCUS_PULL * 0.3;
    const reach = actSpan(best);
    const d = reach > 1 ? flat : walk;
    const near = best.range ? best.range[0] : 1;
    return Math.max(0, d - reach) * FOCUS_PULL + (d < near ? (near - d) * FOCUS_PULL * 0.5 : 0);
  }

  function makeCtx(s, team, opts) {
    opts = opts || {};
    const foe = E.other(team);
    const stanceName = opts.stance || 'balanced';
    const st = STANCES[stanceName] || STANCES.balanced;
    // Objective objects count as targets to march on when breaking them wins the battle.
    // Treasure guardians and towers are left alone unless they get in the way.
    // The enemy army beaten, the player's army cleans up: buildings with gold or a goal in
    // them, and the treasure's guards, whose coins are still worth having.
    const cleanup = team === 'P' && !!s.cleanup;
    const foes = cleanup
      ? E.cleanupTargets(s)
      : s.units.filter((u) => u.alive && u.team === foe && !u.bound && !u.structure && (!u.nonCombat || (s.objective === 'destroy' && isGoal(u)) || isSpawning(s, u)));
    // Hostile Lightning Wards (anything rooted to the spot that zaps what comes near), and
    // the living foes worth walking into one for. While any of those remain, nobody marches
    // on a ward: it is fought from outside its reach.
    const wards = foes.filter((u) => u.traits.has('immobile') && ['nova', 'line', 'cone'].includes(u.act.kind) && u.act.dmg);
    const flesh = foes.filter((u) => !u.nonCombat && !u.traits.has('immobile'));
    const chase = wards.length && flesh.length ? foes.filter((u) => !wards.includes(u)) : foes;
    const ctx = {
      s,
      team,
      foe,
      opts,
      sources: buildSources(s, foe),
      distField: buildDistField(s, chase, team),
      wards: flesh.length ? wards : [],
      flesh,
      chase,
      allies: s.units.filter((u) => u.alive && u.team === team && !u.nonCombat && !u.structure),
      foes,
      objects: s.units.filter((u) => u.alive && u.team === team && u.goal),
      // Enemies to march on: buildings that must fall, anything still spawning, and the
      // Commander whose death wins the battle.
      siege: cleanup
        ? foes.filter((u) => u.nonCombat || u.structure)
        : s.units.filter((u) => u.alive && u.team === foe && ((s.objective === 'destroy' && u.goal && u.nonCombat) || isSpawning(s, u) || (s.objective === 'vip' && u.vip))),
      cleanup,
      // The win is yours already (the mission done): spoils are worth going for.
      won: team === 'P' && !!s.won,
      // Tiles where enemy reinforcements land at the end of the enemy's next turn.
      marks: new Set(
        s.waves
          .filter((w) => w.state === 'pending' && w.team === foe && w.marks)
          .flatMap((w) => w.marks.map(([mx, my]) => E.idx(s, mx, my)))
      ),
      foeRanged: s.units.some((u) => u.alive && u.team === foe && !u.nonCombat && u.acts.some((a) => a.range && a.range[1] >= 2 && a.dmg)),
      foeMagic: s.units.some((u) => u.alive && u.team === foe && !u.nonCombat && u.acts.some((a) => a.dmg === 'magic')),
      approach: st.approach,
      risk: st.risk,
      focus: focusOf(s, team, opts.focus),
      // Loot lying there for the taking (only the player's side takes loot).
      loot: team === 'P' ? (s.loot || []).filter((l) => !l.taken) : [],
    };
    if (ctx.focus) {
      ctx.focusField = buildDistField(s, [ctx.focus], team);
      // Everything else gives way to the priority target: danger barely counts.
      ctx.risk *= 0.15;
    }
    // Loot to drift toward, unless sleeping guards lie around it (walking up would wake
    // them) or an enemy is the priority.
    const lure = ctx.loot.filter((l) => !s.units.some((g) => g.alive && g.post && g.post.x === l.x && g.post.y === l.y && dormant(s, g)));
    ctx.lootField = lure.length && !(ctx.focus && ctx.focus.unit) ? buildDistField(s, lure, team) : null;
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
    // The further ahead, the more a detour for loot is worth: up to 3 times the pull.
    ctx.lootPull = LOOT_PULL * Math.min(3, Math.max(1, ratio));
    // The player's bonus goals.
    const goal = (type) => (team === 'P' ? (s.goals || []).find((g) => g.type === type) : null);
    // Win within N turns: press on, harder in the last few turns before the deadline (not
    // when holding the shrine is what wins).
    const swift = goal('swift');
    if (swift && !s.hold && s.turn <= swift.turns) ctx.approach *= 1.3 + 0.7 * Math.min(1, Math.max(0, (s.turn - swift.turns + 8) / 8));
    // Block reinforcements (an old save's goal): stepping onto a landing tile is worth much
    // more until enough are. Otherwise a mark is worth stepping on when it is handy.
    const block = goal('blockade');
    ctx.markValue = block && (s.stats.blocked || 0) < block.n ? 20 : 7;
    // Ambush the reinforcements: new arrivals are worth more to cut down until enough fall.
    const ambush = goal('ambush');
    ctx.ambush = !!(ambush && (s.stats.waveKills || 0) < ambush.n);
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

  // Whether u could strike a living foe (not a ward or a building) from (x, y) this turn.
  function canHitFlesh(ctx, u, x, y) {
    for (const a of u.acts) {
      if (!a.dmg || a.kind === 'none' || a.left <= 0 || a.cdLeft > 0) continue;
      let [r0, r1] = a.range || [1, a.radius || a.len || 1];
      if (a.kind === 'blast') r1 += a.pattern === 'square' ? 2 : 1;
      if (a.kind === 'nova' || a.kind === 'cleave') r0 = 1;
      for (const f of ctx.flesh) {
        const d = Math.abs(f.x - x) + Math.abs(f.y - y);
        if (d >= r0 && d <= r1) return true;
      }
    }
    return false;
  }

  // A Lightning Ward sprays one side at a time (a fanned cone); anything else rooted pulses
  // all around.
  function inWardReach(s, w, x, y) {
    if (w.act.kind === 'line' || w.act.kind === 'cone') {
      const tiles = w.act.kind === 'line' ? E.lineTiles : E.coneTiles;
      for (let d = 0; d < 4; d++) if (tiles(s, w.x, w.y, d, w.act.len, w.act.fan).some(([tx, ty]) => tx === x && ty === y)) return true;
      return false;
    }
    return Math.abs(w.x - x) + Math.abs(w.y - y) <= (w.act.radius || 2);
  }

  // Standing in a hostile ward's reach without a living foe to hit from there: the ward
  // zaps you for nothing. Worth a lot to avoid.
  function wardPenalty(ctx, u, x, y) {
    if (ctx.focus) return 0; // a priority target overrides this caution
    for (const w of ctx.wards) {
      if (!inWardReach(ctx.s, w, x, y)) continue;
      if (canHitFlesh(ctx, u, x, y)) return 0;
      const zap = w.pow * (1 - Math.max(0, u.res));
      return 20 + zap * (u.value / u.maxHp) * 3;
    }
    return 0;
  }

  function primaryRange(u) {
    const a = u.act;
    return a.range ? a.range : null;
  }

  // Picks that pay off only from the right tile, beyond the attack itself (which the
  // planner already previews from each tile it could move to): spread out for the Lone
  // Wolf Pelt, close ranks for the Phalanx Standard, hold still to Hold the Line, end a move
  // beside enemies with Thunderstep or Drift, keep the wounded beside a healer of
  // neighbours. `hurt`: what the blows it may take here are worth.
  function formationValue(ctx, u, x, y, hurt) {
    const s = ctx.s;
    if (u.nonCombat || u.structure) return 0;
    const rel = s.relics[u.team];
    const near = (v) => v !== u && v.alive && Math.abs(v.x - x) + Math.abs(v.y - y) === 1;
    const next = ctx.allies.filter(near);
    const foesNext = ctx.foes.filter((f) => near(f) && !f.nonCombat && !f.structure);
    const home = ctx.from && ctx.from.uid === u.uid ? ctx.from : null;
    const stays = !home || (home.x === x && home.y === y);
    const hits = (w) => w.acts.some((a) => a.dmg && a.kind !== 'none');
    let v = 0;
    if (rel.has('lone_wolf') && next.length) {
      if (hits(u)) v -= 0.3 * u.pow * 0.8 + 1;
      // ...and it spoils it for a neighbour that stood alone.
      for (const al of next) {
        const alone = !ctx.allies.some((o) => o !== al && o !== u && o.alive && Math.abs(o.x - al.x) + Math.abs(o.y - al.y) === 1);
        if (alone && hits(al)) v -= 0.3 * al.pow * 0.5;
      }
    }
    if (rel.has('phalanx_standard')) {
      // Its own two neighbours, and any ally it gives a second one to.
      if (next.length >= 2) v += 0.2 * hurt + 3;
      else if (next.length === 1) v += 1;
      for (const al of next) {
        const others = ctx.allies.filter((o) => o !== al && o !== u && o.alive && Math.abs(o.x - al.x) + Math.abs(o.y - al.y) === 1).length;
        if (others === 1) v += 1.5;
      }
    }
    if (u.traits.has('brace') && stays) v += 0.3 * hurt + 0.5;
    if (!stays) {
      for (const f of foesNext) {
        const fv = f.value / f.maxHp;
        if (u.traits.has('thunderstep')) v += Math.min(6 * (1 - f.res), f.hp) * fv;
        if (u.traits.has('sporepuff') && !E.statusImmune(s, f, 'poison')) v += 4 * fv * 0.85;
      }
    }
    for (const al of next) {
      const av = al.value / al.maxHp;
      if (u.traits.has('mossy') && al.hp < al.maxHp) v += 2 * av * 1.5;
      if (al.traits.has('mossy') && u.hp < u.maxHp) v += 2 * (u.value / u.maxHp) * 1.5;
      if (al.traits.has('rallykill') && u.hp < u.maxHp) v += 1;
      if (u.traits.has('rallykill') && al.hp < al.maxHp) v += 0.5;
    }
    return v;
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
    let v = -expTaken * hpv * ctx.risk + offense(ctx, u, x, y) - wardPenalty(ctx, u, x, y);
    if (expTaken >= u.hp) v -= u.value * 0.6 * ctx.risk;
    else if (expTaken >= u.hp * 0.6) v -= u.value * 0.15 * ctx.risk;
    if (u.boss) v *= 1.5;

    const role = UNITS[u.type].role;
    const flying = u.traits.has('flying');
    const nf = nearestFoe(ctx, x, y);
    const walk = flying ? nf.d : Math.min(ctx.distField[E.idx(s, x, y)], nf.d + 6);
    const a = u.act;
    // Guardians and spellwards (Guardian, Holy Aegis, Spellward Aura, Grounding Field) keep
    // their friends beside them, the fragile ones first, and the fragile ones stay beside a
    // guardian: the stronger the protection, the more it is worth. A Bodyguard, who takes a
    // blow meant for an ally beside it, counts like a Guardian.
    const fragile = (t) => ['ranged', 'caster', 'support'].includes(UNITS[t.type].role);
    const cover = (t) => ((t.props.guard || 0) + (t.props.magicGuard || 0) * (ctx.foeMagic ? 1 : 0.5)) / 0.15 + (t.traits.has('bodyguard') ? 1 : 0);
    const mine = cover(u);
    const charges = mine && !ctx.cleanup ? ctx.allies.filter((al) => al !== u && fragile(al)) : [];
    switch (role) {
      case 'tank':
      case 'melee':
      case 'skirmisher':
        // A guardian escorts: it marches with the fragile, not ahead of them.
        if (charges.length) {
          const dc = Math.min(...charges.map((al) => Math.abs(al.x - x) + Math.abs(al.y - y)));
          v -= walk * ctx.approach * 0.35 + Math.max(0, dc - 1) * 1.6 * Math.min(2, mine);
        } else v -= walk * ctx.approach;
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
    if (s.hold && !s.hold.done) {
      const dh = Math.abs(x - s.hold.x) + Math.abs(y - s.hold.y);
      if (dh === 0) v += u.team === 'P' ? 8 : 6;
      else if (dh === 1) v += 1.5;
    }
    if (u.post) {
      const dp = Math.abs(x - u.post.x) + Math.abs(y - u.post.y);
      if (dp > 1) v -= (dp - 1) * 6;
    }
    // Push on toward the buildings that must fall (wagons: the one nearest its way out).
    if (ctx.siege.length && u.acts.some((x2) => x2.dmg)) {
      let dg = 99;
      const carts = ctx.siege.filter((o) => o.traits.has('cart'));
      const lead = carts.length ? carts.reduce((a, b) => (Math.abs(b.x - s.cartExit) < Math.abs(a.x - s.cartExit) ? b : a)) : null;
      for (const o of lead ? [lead] : ctx.siege) dg = Math.min(dg, Math.abs(x - o.x) + Math.abs(y - o.y));
      const r = primaryRange(u);
      const ideal = r && r[1] >= 2 ? r[1] : 1;
      v -= Math.abs(dg - ideal) * 0.5 * ctx.approach;
    }
    // Stand on a marked tile to stop a reinforcement from arriving.
    if (ctx.marks.has(E.idx(s, x, y)) && !u.nonCombat && u.hp > E.BLOCK_DMG + 4) v += ctx.markValue - E.BLOCK_DMG * hpv * 0.4;
    if (ctx.objects.length && s.objective === 'destroy') {
      for (const o of ctx.objects) {
        if (Math.abs(x - o.x) + Math.abs(y - o.y) <= 2) {
          v += 1.5;
          break;
        }
      }
    }
    for (const al of ctx.allies) {
      if (al === u || Math.abs(al.x - x) + Math.abs(al.y - y) !== 1) continue;
      if (mine) v += (fragile(al) ? 2.5 : 1) * mine;
      if (fragile(u)) v += 1.2 * cover(al);
    }
    v += formationValue(ctx, u, x, y, expTaken * hpv * ctx.risk);
    // Hazards underfoot, and powder kegs that the enemy could set off.
    if (!flying) {
      for (const f of s.tfx) {
        if (f.x !== x || f.y !== y || f.team === u.team) continue;
        if (f.kind === 'fire') v -= (f.dmg || 8) * hpv * 1.2;
        if (f.kind === 'caltrops') v -= 6 * hpv + 3;
      }
    }
    // A meteor the other side is calling down: get out from under it.
    for (const c of s.channels || []) {
      if (c.team === u.team || !c.tiles.some(([tx, ty]) => tx === x && ty === y)) continue;
      const caster = s.byId[c.uid];
      const a = caster && caster.acts[c.ai];
      v -= ((a && a.fixed) || 20) * hpv * 1.6 + 4;
    }
    if (ctx.foeRanged) {
      for (const [bx, by] of E.radiusTiles(s, x, y, 1)) {
        const b = E.at(s, bx, by);
        if (b && b.alive && b.traits.has('volatile') && b !== u) v -= 0.12 * (b.props.boom || 15) * hpv * 2;
      }
    }
    if (ctx.focus && u.team === ctx.team) v -= focusPull(ctx, u, x, y);
    if (ctx.lootField && u.team === ctx.team && !u.nonCombat) v -= Math.min(14, ctx.lootField[E.idx(s, x, y)]) * ctx.lootPull;
    return { score: v, facing, danger };
  }

  function paraValue(s, t) {
    const ready = delayOf(s, t) === 0 ? 1 : 0.6;
    return (t.pow * 0.8 + 6) * ready;
  }

  // Who a Furgon's shrubs guard: the Cleric while it lives, else the ally with the least HP.
  function shrubWard(ctx, u) {
    const mine = ctx.allies.filter((al) => al.alive && al.type !== 'shrub' && !al.summoner);
    const clerics = mine.filter((al) => al.type === 'cleric');
    const pool = clerics.length ? clerics : mine;
    let best = null;
    for (const al of pool) if (!best || al.hp < best.hp) best = al;
    return best;
  }

  // Steps a walker needs to reach a tile beside `w` (limit + 1 if it cannot within `limit`).
  function stepsBeside(s, m, w, limit) {
    if (Math.abs(m.x - w.x) + Math.abs(m.y - w.y) === 1) return 0;
    const res = E.reachable(s, m, limit);
    let best = limit + 1;
    for (const [dx, dy] of DIRS) {
      if (!E.inB(s, w.x + dx, w.y + dy)) continue;
      const r = res.get(E.idx(s, w.x + dx, w.y + dy));
      if (r && r.d < best) best = r.d;
    }
    return best;
  }

  // Where a Furgon's shrub does the most good. Any shrub between an enemy walker that could
  // strike soon and one of your fragile units screens them, and three times over for the one
  // it guards (the Cleric, or with no Cleric left whoever has the least HP). On top of that,
  // for the guarded one, the enemy's real walk is measured (round rocks, water, units and
  // other shrubs, and the oldest shrub withering if the Furgon already has all of them):
  // a shrub that keeps a walker from reaching it this turn is worth a lot more, one that
  // only adds steps a little. In campaign sims this keeps the Cleric alive longer than
  // the screen alone, at no cost to battles won.
  function shrubValue(ctx, u, tx, ty) {
    const s = ctx.s;
    const ward = shrubWard(ctx, u);
    const base = shrubScreen(ctx, tx, ty, ward);
    if (!ward) return base;
    const walkers = ctx.foes.filter((m) => m.alive && !m.nonCombat && m.move > 0 && !m.traits.has('flying') && !m.traits.has('immobile') && m.root === 0 && m.para === 0 && m.act.range && m.act.range[1] <= 1);
    if (!walkers.length) return base;
    const before = walkers.map((m) => stepsBeside(s, m, ward, m.move + 4));
    // Only threats due within about two turns.
    if (!walkers.some((m, i) => before[i] <= m.move * 2)) return base;
    const cap = 3 + (u.props.shrubs || 0);
    const mine = s.units.filter((v) => v.alive && v.type === 'shrub' && v.summoner === u.uid).sort((a, b) => a.born - b.born);
    const withers = mine.length >= cap ? mine[0] : null;
    // Grow it for a moment: a stand-in that blocks like a shrub.
    const ti = E.idx(s, tx, ty);
    const occT = s.occ[ti];
    s.byId[-7] = { uid: -7, alive: true, team: u.team, type: 'shrub', nonCombat: true, structure: false, traits: new Set(), tags: new Set() };
    s.occ[ti] = -7;
    let oi = -1;
    let occO = 0;
    if (withers) {
      oi = E.idx(s, withers.x, withers.y);
      occO = s.occ[oi];
      s.occ[oi] = 0;
    }
    let wb = 0;
    try {
      walkers.forEach((m, i) => {
        const b = before[i];
        if (b > m.move * 2) return;
        const after = stepsBeside(s, m, ward, m.move + 4);
        if (after < b) wb -= Math.min(3, b - after) * 2;
        else if (after > b) wb += b <= m.move && after > m.move ? 6 + m.pow * (ward.value / ward.maxHp) * 0.5 : Math.min(3, after - b) * 1.5;
      });
    } finally {
      s.occ[ti] = occT;
      delete s.byId[-7];
      if (oi >= 0) s.occ[oi] = occO;
    }
    return Math.max(0, base + Math.max(-6, Math.min(wb, 8)));
  }

  // A shrub between an enemy walker close enough to strike soon and one of your fragile
  // units (archers, casters, healers, and the guarded one), on a shortest way between them.
  function shrubScreen(ctx, tx, ty, ward) {
    let v = 1;
    for (const m of ctx.foes) {
      const T = UNITS[m.type];
      if (m.move === 0 || !m.act.range || m.act.range[1] > 1 || m.traits.has('flying')) continue;
      const dm = Math.abs(m.x - tx) + Math.abs(m.y - ty);
      if (dm > m.move + 1) continue;
      for (const al of ctx.allies) {
        const r = UNITS[al.type].role;
        if (r !== 'ranged' && r !== 'caster' && r !== 'support' && al !== ward) continue;
        const da = Math.abs(al.x - tx) + Math.abs(al.y - ty);
        if (dm + da === Math.abs(m.x - al.x) + Math.abs(m.y - al.y)) v += 2.5 * (T.cost / 3) * (al === ward ? 3 : 1);
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
    // A channelled act lands a turn later: foes that can walk may well be gone by then.
    const later = (t) => (a.channel && t.team !== u.team && t.move > 0 && !t.root && !t.para && !t.traits.has('immobile') ? 0.4 : 1);
    for (const e of pv.effects) {
      const t = s.byId[e.uid];
      // Wreckage (spoils) is worth nothing to either side until the enemy army falls.
      if (t.traits.has('spoils') && !ctx.won) continue;
      const hpv = t.value / t.maxHp;
      if (e.self) {
        v -= u.value;
        continue;
      }
      const bossTarget = t.team !== u.team && ((s.objective === 'boss' && t.boss) || (s.objective === 'vip' && t.vip) || (s.objective === 'destroy' && isGoal(t)));
      // Popping a Spell Shield clears the way for the next blow; more so on a Shackler
      // holding one of ours.
      if (e.ward) v += 6 + t.value * 0.06 + (t.holding ? 20 : 0);
      if (e.dmg != null) {
        const p = 1 - e.block;
        const dealt = Math.min(e.dmg, t.hp + t.shield);
        let val = Math.max(0, dealt - t.shield) * hpv + Math.min(dealt, t.shield) * 0.2;
        if (e.kill) val += t.value * 0.8;
        if (bossTarget) val *= t.boss || t.vip ? 2.5 : 3;
        // A wagon about to get away matters most.
        if (t.team !== u.team && t.traits.has('cart')) val *= 1 + 4 / (1 + Math.abs(t.x - s.cartExit));
        else if (t.team !== u.team && isSpawning(s, t)) val *= 2;
        if (e.kill && t.traits.has('volatile')) val += boomValue(ctx, u, t);
        if (e.kill && t.team !== u.team) val += crowdKill(ctx, u, t, e);
        if (ctx.ambush && t.reinforcement && t.team !== u.team) val *= e.kill ? 1.6 : 1.25;
        // A barricade's gold is worth breaking it for when nothing better is in reach.
        if (t.bounty && t.team !== u.team && ctx.idle) val += e.kill ? t.bounty * 0.4 : (dealt / t.maxHp) * t.bounty * 0.15;
        // Cleaning up after the enemy army fell: every blow at what is left is progress.
        if (ctx.cleanup && t.team !== u.team && !e.friendly) val += dealt * 0.6 + (e.kill ? 25 : 0);
        // A Shackler holding one of ours: every blow on it is a step toward the chain breaking.
        if (t.holding && t.team !== u.team && !e.friendly) {
          const held = s.byId[t.holding];
          if (held && held.alive) val += (dealt / Math.max(1, t.hp)) * held.value * 0.5 + (e.kill ? held.value * 0.8 : 0);
        }
        // A hit on the priority target outweighs anything else this unit could do.
        if (ctx.focus && ctx.focus.unit === t && !e.friendly) val += 80 + dealt * 3 + (e.kill ? 150 : 0);
        // With the shrine the priority, an enemy standing on it must be driven off.
        else if (ctx.focus && ctx.focus.hold && t.team !== u.team && t.x === ctx.focus.x && t.y === ctx.focus.y && !e.friendly) val += 40 + dealt * 2 + (e.kill ? 100 : 0);
        if (e.friendly) v -= p * val * 1.4 * (a.channel ? 0.6 : 1);
        else v += p * val * later(t);
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
      // Shackles: the target sits out for as long as the Shackler holds on. Worth the most on
      // the enemy's biggest hitter, never on one already held.
      if (e.hold && e.hold !== 'resist' && !t.heldBy) v += p * e.hold * 2.5 * paraValue(ctx.s, t);
      if (e.para && e.para !== 'resist') {
        v += p * e.para * paraValue(ctx.s, t);
        // Discord: it lashes out at one of its own beside it.
        if (u.traits.has('discord') && ctx.foes.some((o) => o !== t && !o.nonCombat && !o.structure && Math.abs(o.x - t.x) + Math.abs(o.y - t.y) === 1)) v += p * 0.5 * t.pow * 0.6;
      }
      if (e.poison && e.poison !== 'resist') {
        // Poisons from different sources add up; the same source only tops up its own.
        const own = t.poison && E.poisonStacks(t).find((st) => st.key === e.poison.key);
        const fresh = own ? Math.max(0, e.poison.turns - own.turns) : e.poison.turns;
        v += p * (Math.min(fresh * e.poison.dmg * (1 - t.res), t.hp) * hpv * 0.85 + (t.poison ? 0 : 3));
      }
      if (e.burn) {
        // Burns from different sources add up; the same source only tops up its own.
        const own = t.burn && E.dotStacks(t, 'burn').find((st) => st.key === e.burn.key);
        const fresh = own ? Math.max(0, e.burn.turns - own.turns) : e.burn.turns;
        v += p * Math.min(fresh * e.burn.dmg * (1 - t.res), t.hp) * hpv * 0.8;
      }
      if (e.root && e.root !== 'resist' && t.move > 0 && t.root === 0) v += p * (2 + 0.3 * t.pow) * Math.min(2, e.root);
      if (e.weak && t.weak === 0 && t.acts.some((x) => x.dmg)) v += p * 0.3 * t.pow * 1.2 * (delayOf(ctx.s, t) === 0 ? 1 : 0.6);
      if (e.mark && t.mark === 0) v += p * 0.25 * 18 * hpv * Math.min(3, alliesNear(ctx, t, 5));
      if (e.knock && e.knock !== 'resist' && !e.kill) v += p * shoveValue(ctx, u, t, e.knock, t.hp - (e.dmg || 0) * p);
    }
    if (a.kind === 'grow') v += shrubValue(ctx, u, target.x, target.y);
    v += spillValue(ctx, u, a, target, pv);
    // Acting starts recovery; small cost so weak pokes don't lock down slow casters.
    v -= u.rec * u.pow * 0.08;
    if (a.uses) v -= 1.5;
    return v;
  }

  // Enemies huddled around the one about to fall: Combustion and Wildfire Oil spread its
  // fire to them, Contagion and the Plague Doctor's Mask its poison.
  function crowdKill(ctx, u, t, e) {
    const s = ctx.s;
    const rel = s.relics[u.team];
    const burning = !!t.burn || !!e.burn;
    const fire = burning && (u.traits.has('combustion') || rel.has('wildfire_oil'));
    const plague = !!t.poison && (rel.has('plague_mask') || E.poisonStacks(t).some((st) => s.byId[st.src] && s.byId[st.src].traits.has('contagion')));
    if (!fire && !plague) return 0;
    let v = 0;
    for (const o of ctx.foes) {
      if (o === t || o.nonCombat || o.structure || Math.abs(o.x - t.x) + Math.abs(o.y - t.y) !== 1) continue;
      const ov = o.value / o.maxHp;
      if (fire) v += ((u.traits.has('combustion') ? 10 : 0) + 6) * ov;
      if (plague) v += 6 * ov;
    }
    return v;
  }

  // Ricochet and Shrapnel: a basic attack at a foe with others close by hits them too.
  function spillValue(ctx, u, a, target, pv) {
    if (a !== u.act || target.kind !== 'unit' || !(u.props.bounce || u.props.splash)) return 0;
    const t = ctx.s.byId[target.uid];
    const main = t && pv.effects.find((e) => e.uid === t.uid && e.dmg != null);
    if (!main) return 0;
    let best = 0;
    let splash = 0;
    for (const o of ctx.foes) {
      if (o === t || o.nonCombat) continue;
      const d = Math.abs(o.x - t.x) + Math.abs(o.y - t.y);
      const ov = o.value / o.maxHp;
      if (u.props.bounce && d <= 2) best = Math.max(best, Math.min(main.dmg * u.props.bounce, o.hp) * ov);
      if (u.props.splash && d === 1) splash += Math.min(main.dmg * u.props.splash, o.hp) * ov;
    }
    return (best + splash) * 0.8;
  }

  // A shove or pull: a little for knocking the enemy out of place, and what it hurts where
  // it lands (a rock, the edge, water, lava, or a unit it crashes into, friend or foe).
  function shoveValue(ctx, u, t, k, left) {
    const s = ctx.s;
    let v = k.n ? 1 : 0;
    left = Math.max(1, left);
    if (k.dmg) {
      const hpv = t.value / t.maxHp;
      v += Math.min(k.dmg, left) * hpv + (k.dmg >= left ? t.value * 0.6 : 0);
      if (k.end === 'water' && t.move > 0 && t.root === 0) v += 2 + 0.3 * t.pow;
      if (k.end === 'lava') v += Math.min(10, Math.max(0, left - k.dmg)) * hpv * 0.6;
    }
    const o = k.other != null && s.byId[k.other];
    if (o && o.alive) {
      const val = Math.min(k.otherDmg, o.hp) * (o.value / o.maxHp) + (k.otherDmg >= o.hp ? o.value * 0.6 : 0);
      v += o.team === u.team ? -val * 1.4 : val;
    }
    // Your army loves a good shove: when it can bump a foe into something (water, lava, a
    // rock, the edge, another foe or a building), it goes out of its way to, chaos and all.
    if (u.team === 'P' && k.end && !(o && o.team === u.team)) v += k.end === 'water' || k.end === 'lava' ? CHAOS + 5 : CHAOS;
    return v;
  }
  const CHAOS = 8;

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
    if (a.kind === 'leap' || a.kind === 'blink' || a.kind === 'charge') return { x: t.x, y: t.y };
    if (a.kind === 'shadowstrike') return { x: t.bx, y: t.by };
    return null;
  }

  // No enemy fighter this unit could reach this turn: time enough to go after loose gold.
  function idleHands(ctx, u) {
    let span = 1;
    for (const a of u.acts) if (a.dmg && a.kind !== 'none') span = Math.max(span, actSpan(a));
    const r = u.move + span + 1;
    return !ctx.foes.some((f) => !f.nonCombat && Math.abs(f.x - u.x) + Math.abs(f.y - u.y) <= r);
  }

  function planFor(ctx, u) {
    const s = ctx.s;
    ctx.from = { uid: u.uid, x: u.x, y: u.y };
    ctx.idle = u.team === 'P' && idleHands(ctx, u);
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
    // Loot within reach: step onto it and take it. Priority loot beats anything else;
    // otherwise it beats an ordinary hit but not a kill. Not while an enemy is the priority.
    if (u.team === 'P' && !u.nonCombat && !(ctx.focus && ctx.focus.unit)) {
      for (const l of ctx.loot) {
        const r = reach.get(E.idx(s, l.x, l.y));
        if (!r) continue;
        const p = E.withUnitAt(s, u, r.x, r.y, () => positionValue(ctx, u, r.x, r.y));
        const prize = ctx.focus && ctx.focus.loot === l ? 1000 : LOOT_VALUE[l.kind] || LOOT_VALUE.chest;
        plans.push({ uid: u.uid, kind: r.d > 0 ? 'moveLoot' : 'loot', to: r, score: p.score + prize, facing: p.facing });
      }
    }
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
    // In a queue battle the turn belongs to this unit whatever it does, so any gain is worth
    // taking; otherwise only a clear one beats leaving the turn to another unit.
    const minGain = s.queue ? 0.1 : 0.75;
    for (const u of ready) {
      const plans = planFor(ctx, u);
      const best = plans[0];
      if (best.kind === 'hold' || best.gain < minGain) {
        holds.push({ u, plan: plans.find((p) => p.kind === 'hold') });
        continue;
      }
      // Keep a few top options per unit for variety.
      for (const p of plans.slice(0, 3)) if (p.kind !== 'hold' && p.gain >= minGain) candidates.push(p);
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
    if (plan.kind === 'move' || plan.kind === 'moveAct' || plan.kind === 'moveLoot') {
      if (!E.moveUnit(s, plan.uid, plan.to.x, plan.to.y)) {
        E.cancelActivation(s);
        return false;
      }
    }
    if (plan.kind === 'loot' || plan.kind === 'moveLoot') {
      if (s.over || !u.alive) return true;
      E.takeLoot(s, plan.uid);
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

  AG.AI = { chooseActivation, executePlan, runPlan, smartFacing, nearestFacing, threatMap, unitThreat, playTurn, dangerAt, makeCtx, positionValue, dormant, focusOf };
})(typeof window !== 'undefined' ? window : globalThis);
