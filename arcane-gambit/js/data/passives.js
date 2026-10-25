/* Passive traits. Each entry may implement engine hooks:
   battleStart, roundStart, roundEnd, turnStart, turnEnd, onMoved,
   outBonus(s,u,p,tgt,o) / inBonus(s,u,p,src,o)  -> extra damage (pure!)
   armorBonus(s,u,p), auraOut / auraIn (from a nearby holder, pure),
   negate(s,u,p,src,o) -> true cancels a hit, preventDeath(s,u,p,src,o),
   afterHit(s,u,p,tgt,dmg,o), afterHurt(s,u,p,src,dmg,o),
   onKill(s,u,p,victim,o), onDeath(s,u,p,killer,o), onAnyDeath(s,u,p,victim,killer),
   capDamage(s,u,p,dmg,o) -> damage actually taken, onEnemyAct(s,u,p,actor)
   (after an enemy attacks or uses an ability).
   Hooks marked pure are also called by the AI with o.est = true. */
(function (AG) {
  'use strict';
  const B = AG.B;
  const near = (a, b, r) => AG.cheb(a.x, a.y, b.x, b.y) <= r;

  function adjacentUnits(s, x, y, filter) {
    const out = [];
    const b = s.board;
    for (const [dx, dy] of AG.DIRS8) {
      const nx = x + dx, ny = y + dy;
      if (!AG.inBounds(b, nx, ny)) continue;
      const id = s.occ[ny * b.w + nx];
      if (!id) continue;
      const o = B.U(s, id);
      if (o.alive && (!filter || filter(o))) out.push(o);
    }
    return out;
  }
  AG.adjacentUnits = adjacentUnits;

  function emptyAround(s, x, y, includeCenter) {
    const b = s.board;
    const out = [];
    if (includeCenter) {
      const c = y * b.w + x;
      if (!s.occ[c] && AG.standable(b, c, false)) out.push(c);
    }
    for (const [dx, dy] of AG.DIRS8) {
      const nx = x + dx, ny = y + dy;
      if (!AG.inBounds(b, nx, ny)) continue;
      const j = ny * b.w + nx;
      if (!s.occ[j] && AG.standable(b, j, false)) out.push(j);
    }
    return out;
  }
  AG.emptyAround = emptyAround;

  function countOwned(s, u, def) {
    let n = 0;
    for (const o of s.units) if (o.alive && o.side === u.side && o.def === def && o.owner === u.uid) n++;
    return n;
  }
  AG.countOwned = countOwned;

  function buff(s, u, atk, label) {
    u.atk += atk;
    B.emit(s, 'buff', { uid: u.uid, label, atk: u.atk });
  }

  AG.Passives = {
    // ----------------------------------------------------------- the pieces
    shieldWall: {
      name: 'Shield Wall',
      desc: () => '+1 armor while an ally stands directly beside it (not diagonally).',
      armorBonus(s, u) {
        const b = s.board;
        for (const [dx, dy] of AG.DIRS4) {
          const x = u.x + dx, y = u.y + dy;
          if (!AG.inBounds(b, x, y)) continue;
          const id = s.occ[y * b.w + x];
          if (id) { const o = B.U(s, id); if (o.side === u.side && !o.object) return 1; }
        }
        return 0;
      },
    },
    promotion: {
      name: 'Promotion',
      desc: (p) => 'On reaching the far edge of the board it is promoted to ' + p.name + ': fully healed, +' + p.hp + ' HP, +' + p.atk + ' ATK.',
    },
    charge: {
      name: 'Charge',
      desc: (p) => '+' + p.bonus + ' damage on a turn it leapt.',
      outBonus(s, u, p, t, o) {
        if (o.kind !== 'attack') return 0;
        if (o.est) return p.bonus;
        return u.moveKind === 'leap' || u.moveKind === 'capture' ? p.bonus : 0;
      },
    },
    spotter: {
      name: 'Spotter',
      desc: () => 'Its hits Mark the target: +1 damage from every hit until the end of next round.',
    },
    hitAndRun: {
      name: 'Hit & Run',
      desc: (p) => 'After attacking it may slip up to ' + p.n + ' squares away.',
    },
    ambusher: {
      name: 'Opening Shot',
      desc: (p) => 'Its first attack of the battle deals +' + p.bonus + '.',
      outBonus(s, u, p, t, o) { return o.kind === 'attack' && !u.fl.ambushUsed ? p.bonus : 0; },
      afterHit(s, u, p, t, d, o) { if (o.kind === 'attack') u.fl.ambushUsed = true; },
    },
    blessed: {
      name: 'Blessed',
      desc: (p) => 'At the end of each round, adjacent allies heal ' + p.amt + '.',
      roundEnd(s, u, p) {
        for (const o of adjacentUnits(s, u.x, u.y, (o) => o.side === u.side && !o.object)) B.heal(s, u, o, p.amt, true);
      },
    },
    holyBane: {
      name: 'Holy Light',
      desc: (p) => '+' + p.amt + ' damage to undead.',
      outBonus(s, u, p, t) { return t.tags.indexOf('undead') >= 0 ? p.amt : 0; },
    },
    kindling: {
      name: 'Kindling',
      desc: (p) => '+' + p.amt + ' damage to burning targets.',
      outBonus(s, u, p, t) { return t.st.burn ? p.amt : 0; },
    },
    wildfire: {
      name: 'Wildfire',
      desc: () => 'Burning enemies that die explode, dealing 2 and spreading Burn to their neighbours.',
      onAnyDeath(s, u, p, v) {
        if (v.side === u.side || !v.st.burn) return;
        B.emit(s, 'aoe', { cells: [[v.x, v.y]], r: 1, vfx: 'fire' });
        for (const o of adjacentUnits(s, v.x, v.y, (o) => o.side !== u.side)) {
          B.hit(s, u, o, 2, { kind: 'ability', tag: 'fire', label: 'Wildfire' });
          if (o.alive) B.addStatus(s, o, 'burn', { d: 1, t: 2 });
        }
      },
    },
    emberWard: {
      name: 'Ember Ward',
      desc: () => 'Enemies that strike it in melee catch fire.',
      afterHurt(s, u, p, src, d, o) { if (src && src.alive && o.melee && !o.counter) B.addStatus(s, src, 'burn', { d: 1, t: 2 }); },
    },
    iceArmor: {
      name: 'Ice Armor',
      desc: (p) => 'Gains ' + p.amt + ' shield at the start of each round (up to ' + p.max + ').',
      roundStart(s, u, p) { if (u.shield < p.max) B.giveShield(s, u, Math.min(p.amt, p.max - u.shield), true); },
    },
    unmovable: {
      name: 'Unmovable',
      desc: () => 'Cannot be pushed or swapped.',
    },
    thorns: {
      name: 'Thorns',
      desc: (p) => 'Melee attackers take ' + p.d + ' damage.',
      afterHurt(s, u, p, src, d, o) {
        if (src && src.alive && o.melee && !o.thorns && src.side !== u.side) {
          B.hit(s, u, src, p.d, { kind: 'true', label: 'Thorns', thorns: true });
        }
      },
    },
    raiseDead: {
      name: 'Raise Dead',
      desc: (p) => 'When a unit dies within ' + p.r + ' squares, raises a Skeleton in its place (up to ' + p.max + ').',
      onAnyDeath(s, u, p, v) {
        if (v.summoned || v.object || !near(u, v, p.r)) return;
        if (countOwned(s, u, 'skeleton') >= p.max) return;
        const i = v.y * s.board.w + v.x;
        if (s.occ[i]) return;
        const sk = B.summon(s, 'skeleton', u.side, i, { owner: u.uid, mods: p.legion ? { hp: 3, atk: 1 } : null });
        if (sk) B.emit(s, 'note', { uid: sk.uid, text: 'rises' });
      },
    },
    lichdom: {
      name: 'Lichdom',
      desc: () => 'The first time it would die, it returns with 5 HP.',
      preventDeath(s, u) {
        if (u.fl.lichUsed) return false;
        u.fl.lichUsed = true;
        u.hp = 5;
        B.emit(s, 'revive', { uid: u.uid, hp: u.hp, label: 'Lichdom' });
        return true;
      },
    },
    bloodlust: {
      name: 'Bloodlust',
      desc: () => 'Gains +1 ATK for each kill.',
      onKill(s, u) { buff(s, u, 1, 'Bloodlust'); },
    },
    nightStalker: {
      name: 'Night Stalker',
      desc: () => '+2 damage to targets below half health.',
      outBonus(s, u, p, t) { return t.hp * 2 < t.maxHp ? 2 : 0; },
    },
    crimsonFeast: {
      name: 'Crimson Feast',
      desc: (p) => 'Lifesteal beyond full health becomes shield (up to ' + p.max + ').',
    },
    ambush: {
      name: 'Ambush',
      desc: (p) => '+' + p.bonus + ' damage to enemies that have not acted yet this round.',
      outBonus(s, u, p, t, o) {
        if (o.kind !== 'attack' || o.second) return 0;
        if (o.est) return B.spd(s, t) < B.spd(s, u) ? p.bonus : 0;
        return t.acted ? 0 : p.bonus;
      },
    },
    evasive: {
      name: 'Shadowed',
      desc: () => 'Starts the battle in stealth: enemies cannot target it until it strikes.',
      battleStart(s, u) { B.addStatus(s, u, 'stealth', {}); },
    },
    vanish: {
      name: 'Vanish',
      desc: () => 'After a kill it melts back into stealth.',
      onKill(s, u) { if (u.alive) B.addStatus(s, u, 'stealth', {}); },
    },
    guardian: {
      name: 'Guardian Aura',
      desc: (p) => 'Adjacent allies take ' + p.amt + ' less damage from hits.',
      auraIn(s, w, p, t, src, o) { return near(w, t, 1) ? -p.amt : 0; },
    },
    consecration: {
      name: 'Consecration',
      desc: () => 'At the end of each round deals 1 damage to adjacent enemies (2 to undead).',
      roundEnd(s, u) {
        const foes = adjacentUnits(s, u.x, u.y, (o) => o.side !== u.side && !o.object);
        if (foes.length) B.emit(s, 'aoe', { cells: [[u.x, u.y]], r: 1, vfx: 'holy' });
        for (const o of foes) B.hit(s, u, o, o.tags.indexOf('undead') >= 0 ? 2 : 1, { kind: 'true', tag: 'holy', label: 'Consecration' });
      },
    },
    rage: {
      name: 'Rage',
      desc: (p) => 'Gains +1 ATK each time it is damaged (up to +' + p.max + ').',
      afterHurt(s, u, p) {
        if (!u.alive || (u.ctr.rage || 0) >= p.max) return;
        u.ctr.rage = (u.ctr.rage || 0) + 1;
        buff(s, u, 1, 'Rage');
      },
    },
    undying: {
      name: 'Undying Rage',
      desc: () => 'The first lethal blow leaves it at 1 HP instead.',
      preventDeath(s, u) {
        if (u.fl.undying) return false;
        u.fl.undying = true;
        u.hp = 1;
        B.emit(s, 'revive', { uid: u.uid, hp: 1, label: 'Undying' });
        return true;
      },
    },
    bloodthirst: {
      name: 'Bloodthirst',
      desc: (p) => 'Heals ' + p.amt + ' after each kill.',
      onKill(s, u, p) { B.heal(s, u, u, p.amt); },
    },
    longshot: {
      name: 'Longshot',
      desc: (p) => '+' + p.amt + ' damage to targets ' + p.dist + ' or more squares away.',
      outBonus(s, u, p, t, o) {
        if (o.kind !== 'attack') return 0;
        let x = u.x, y = u.y;
        if (o.from != null) { x = o.from % s.board.w; y = (o.from / s.board.w) | 0; }
        return AG.cheb(x, y, t.x, t.y) >= p.dist ? p.amt : 0;
      },
    },
    mirrorImage: {
      name: 'Mirror Image',
      desc: () => 'A decoy absorbs the first hit it would take.',
      negate(s, u, p, src, o) {
        if (u.fl.mirror || o.est) return false;
        u.fl.mirror = true;
        return true;
      },
    },
    timeless: {
      name: 'Timeless',
      desc: () => 'Immune to Chill and Freeze.',
    },
    soulSiphon: {
      name: 'Soul Siphon',
      desc: (p) => 'Whenever an enemy dies, heals 2 and gains +1 ATK (up to +' + p.max + ').',
      onAnyDeath(s, u, p, v) {
        if (v.side === u.side || v.object) return;
        B.heal(s, u, u, 2, true);
        if ((u.ctr.siphon || 0) < p.max) { u.ctr.siphon = (u.ctr.siphon || 0) + 1; buff(s, u, 1, 'Soul Siphon'); }
      },
    },
    regrowth: {
      name: 'Regrowth',
      desc: (p) => 'Heals ' + p.amt + ' at the start of its turn.',
      turnStart(s, u, p) { B.heal(s, u, u, p.amt, true); },
    },
    packTactics: {
      name: 'Pack Tactics',
      desc: () => '+1 damage for each adjacent allied wolf.',
      outBonus(s, u, p, t, o) {
        if (o.kind !== 'attack') return 0;
        let n = 0;
        const b = s.board;
        for (const [dx, dy] of AG.DIRS8) {
          const x = u.x + dx, y = u.y + dy;
          if (!AG.inBounds(b, x, y)) continue;
          const id = s.occ[y * b.w + x];
          if (id) { const o2 = B.U(s, id); if (o2.side === u.side && o2.tags.indexOf('wolf') >= 0) n++; }
        }
        return n;
      },
    },
    rally: {
      name: 'Rally',
      desc: (p) => 'Allies within ' + p.r + ' squares deal +' + p.amt + ' damage.',
      auraOut(s, w, p, src, t, o) { return src !== w && near(w, src, p.r) && o.kind !== 'dot' ? p.amt : 0; },
    },
    rallyingPresence: {
      name: 'Rallying Presence',
      desc: () => 'At the end of each round, allies within 2 squares heal 1.',
      roundEnd(s, u) {
        for (const o of s.units) if (o.alive && o.side === u.side && o !== u && !o.object && near(u, o, 2)) B.heal(s, u, o, 1, true);
      },
    },
    rebirth: {
      name: 'Rebirth',
      desc: (p) => 'When it dies it bursts into flame (3 damage to adjacent enemies). The first time, it leaves an Ember Egg that hatches into a fresh Phoenix after ' + p.hatch + ' rounds.',
      onDeath(s, u, p, killer) {
        B.emit(s, 'aoe', { cells: [[u.x, u.y]], r: 1, vfx: 'fire' });
        for (const o of adjacentUnits(s, u.x, u.y, (o) => o.side !== u.side)) {
          B.hit(s, u, o, 3, { kind: 'ability', tag: 'fire', label: 'Rebirth' });
        }
        if (u.fl.reborn) return;
        const i = u.y * s.board.w + u.x;
        const egg = B.summon(s, 'emberEgg', u.side, i, {});
        if (egg) {
          egg.ctr.hatch = p.hatch;
          egg.fl.from = { talents: u.talents, rune: u.rune, rank: u.rank };
        }
      },
    },
    hatch: {
      name: 'Hatching',
      desc: () => 'Hatches into a Phoenix if it survives long enough.',
      roundStart(s, u) {
        u.ctr.hatch = (u.ctr.hatch || 2) - 1;
        if (u.ctr.hatch > 0) { B.emit(s, 'note', { uid: u.uid, text: 'hatching in ' + u.ctr.hatch }); return; }
        const i = u.y * s.board.w + u.x;
        const from = u.fl.from || {};
        u.alive = false;
        s.occ[i] = 0;
        B.emit(s, 'vanish', { uid: u.uid });
        const ph = B.summon(s, 'phoenix', u.side, i, { talents: from.talents, rune: from.rune, rank: from.rank });
        if (ph) { ph.fl.reborn = true; ph.acted = false; B.emit(s, 'note', { uid: ph.uid, text: 'reborn!' }); }
      },
    },
    counter: {
      name: 'Counter',
      desc: (p) => 'When struck in melee, strikes back for ' + p.d + '.',
      afterHurt(s, u, p, src, d, o) {
        if (!u.alive || !src || !src.alive || !o.melee || o.counter || src.side === u.side) return;
        if (AG.cheb(u.x, u.y, src.x, src.y) > 1) return;
        B.hit(s, u, src, p.d, { kind: 'attack', melee: true, counter: true, label: 'Counter' });
      },
    },
    zen: {
      name: 'Zen',
      desc: () => 'Dodges the first hit each round.',
      negate(s, u, p, src, o) {
        if (o.est || u.fl.zen === s.round) return false;
        u.fl.zen = s.round;
        return true;
      },
    },
    volatile: {
      name: 'Volatile',
      desc: (p) => 'Explodes on death for ' + p.d + ' damage to adjacent enemies' + (p.burn ? ' and sets them alight.' : '.'),
      onDeath(s, u, p) {
        const foes = adjacentUnits(s, u.x, u.y, (o) => o.side !== u.side);
        B.emit(s, 'aoe', { cells: [[u.x, u.y]], r: 1, vfx: 'fire' });
        for (const o of foes) {
          B.hit(s, u, o, p.d, { kind: 'ability', tag: 'fire', label: 'Explosion' });
          if (p.burn && o.alive) B.addStatus(s, o, 'burn', { d: 1, t: 2 });
        }
      },
    },
    splitter: {
      name: 'Split',
      desc: (p) => 'When destroyed it splits into ' + p.n + ' Slimelings.',
      onDeath(s, u, p, killer, o) {
        if (o && o.kind === 'fall') return;
        const cells = emptyAround(s, u.x, u.y, true).slice(0, p.n);
        for (const c of cells) B.summon(s, p.into || 'slimeling', u.side, c, {});
      },
    },
    regen: {
      name: 'Regenerate',
      desc: (p) => 'Heals ' + p.amt + ' at the start of its turn unless it is burning.',
      turnStart(s, u, p) { if (!u.st.burn && !u.fl.burning) B.heal(s, u, u, p.amt, true); },
    },
    reassemble: {
      name: 'Reassemble',
      desc: () => 'Collapses into a bone pile when killed; unless the pile is smashed or the killing blow was fire or holy, it stands back up after a round.',
      onDeath(s, u, p, killer, o) {
        if (u.fl.reassembled || (o && (o.tag === 'fire' || o.tag === 'holy' || o.kind === 'fall' || o.kind === 'sacrifice'))) return;
        const pile = B.summon(s, 'bonePile', u.side, u.y * s.board.w + u.x, { owner: u.owner });
        if (pile) { pile.ctr.hatch = 2; pile.fl.into = u.def; pile.fl.owner = u.owner; }
      },
    },
    reform: {
      name: 'Reforming',
      desc: () => 'Rises again as a skeleton unless destroyed.',
      roundStart(s, u) {
        u.ctr.hatch = (u.ctr.hatch || 2) - 1;
        if (u.ctr.hatch > 0) return;
        const i = u.y * s.board.w + u.x;
        u.alive = false;
        s.occ[i] = 0;
        B.emit(s, 'vanish', { uid: u.uid });
        const sk = B.summon(s, u.fl.into || 'skeleton', u.side, i, { hpPct: 0.5, owner: u.fl.owner || 0 });
        if (sk) { sk.fl.reassembled = true; sk.acted = false; B.emit(s, 'note', { uid: sk.uid, text: 'reassembles' }); }
      },
    },
    infectious: {
      name: 'Infectious',
      desc: () => 'Units it kills rise as Zombies on its side.',
      onKill(s, u, p, v) {
        if (v.object || v.big || v.boss || v.side === u.side) return;
        const i = v.y * s.board.w + v.x;
        if (s.occ[i]) return;
        const z = B.summon(s, 'zombie', u.side, i, { hpPct: 0.6 });
        if (z) B.emit(s, 'note', { uid: z.uid, text: 'turned!' });
      },
    },
    incorporeal: {
      name: 'Incorporeal',
      desc: () => 'Basic attacks deal 2 less damage to it. Abilities hit it normally.',
      inBonus(s, u, p, src, o) { return o.kind === 'attack' ? -2 : 0; },
    },
    darkPact: {
      name: 'Dark Pact',
      desc: (p) => 'On death, adjacent allies gain +' + p.amt + ' ATK.',
      onDeath(s, u, p) {
        for (const o of adjacentUnits(s, u.x, u.y, (o) => o.side === u.side && !o.object)) buff(s, o, p.amt, 'Dark Pact');
      },
    },
    royalDecree: {
      name: 'Royal Decree',
      desc: () => 'Goblins on its side deal +1 damage.',
      auraOut(s, w, p, src) { return src !== w && src.tags.indexOf('goblin') >= 0 ? 1 : 0; },
    },
    phylacteryBound: {
      name: 'Phylactery',
      desc: () => 'Cannot die while its Phylactery stands; lethal damage leaves it at 1 HP.',
      preventDeath(s, u) {
        for (const o of s.units) {
          if (o.alive && o.side === u.side && o.def === 'phylactery') {
            u.hp = 1;
            B.emit(s, 'revive', { uid: u.uid, hp: 1, label: 'Phylactery' });
            return true;
          }
        }
        return false;
      },
    },
    soulReap: {
      name: 'Soul Reap',
      desc: (p) => 'Heals ' + p.amt + ' after each kill.',
      onKill(s, u, p) { B.heal(s, u, u, p.amt); },
    },
    scorching: {
      name: 'Scorching',
      desc: () => 'At the start of each round, sets adjacent enemies alight.',
      roundStart(s, u) {
        for (const o of adjacentUnits(s, u.x, u.y, (o) => o.side !== u.side && !o.object)) B.addStatus(s, o, 'burn', { d: 1, t: 2 });
      },
    },
    frostDeath: {
      name: 'Shatterburst',
      desc: () => 'On death, adjacent enemies are Chilled.',
      onDeath(s, u) {
        for (const o of adjacentUnits(s, u.x, u.y, (o) => o.side !== u.side)) B.addStatus(s, o, 'chill', { a: 2 });
      },
    },
    reflect: {
      name: 'Mirrored',
      desc: (p) => 'Ranged attackers that hit it take ' + p.d + ' damage.',
      afterHurt(s, u, p, src, d, o) {
        if (src && src.alive && !o.melee && o.kind === 'attack' && src.side !== u.side && !o.chained) {
          B.hit(s, u, src, p.d, { kind: 'true', label: 'Reflect' });
        }
      },
    },
    packLeader: {
      name: 'Pack Leader',
      desc: () => 'Wolves on its side deal +1 damage.',
      auraOut(s, w, p, src) { return src !== w && src.tags.indexOf('wolf') >= 0 ? 1 : 0; },
    },
    construct: {
      name: 'Construct',
      desc: () => 'Immune to Burn and Poison.',
    },
    mindless: {
      name: 'Mindless',
      desc: () => 'Charges forward without regard for its own safety.',
    },
    stationary: {
      name: 'Rooted Emplacement',
      desc: () => 'Never moves.',
    },
    manaBurn: {
      name: 'Mana Burn',
      desc: () => 'Attacks also deal 2 damage to enemies next to the target.',
    },
    spellweaver: {
      name: 'Spellweaver',
      desc: () => 'Ability cooldowns are 1 turn shorter.',
    },
    unstoppable: {
      name: 'Unstoppable',
      desc: () => 'Immune to Freeze, Stun, Root and Chill.',
    },
    swarmQueen: {
      name: 'Brood Mother',
      desc: () => 'At the start of each round, spawns a Spiderling next to itself (up to 3).',
      roundStart(s, u) {
        if (countOwned(s, u, 'spiderling') >= 3) return;
        const cells = emptyAround(s, u.x, u.y, false);
        if (cells.length) B.summon(s, 'spiderling', u.side, cells[0], { owner: u.uid });
      },
    },
    oathbound: {
      name: 'Oathbound',
      desc: () => 'Its whole army fights to protect it. If it falls, the battle is won.',
    },
    commanderAura: {
      name: 'Royal Guard',
      desc: () => 'Adjacent allies take 1 less damage from hits.',
      auraIn(s, w, p, t) { return near(w, t, 1) ? -1 : 0; },
    },

    // ------------------------------------------------------- the mega boss
    invincible: {
      name: 'Invincible',
      desc: (p) => 'Takes at most ' + p.cap + ' damage each round, however hard it is hit.',
      capDamage(s, u, p, dmg) {
        if (u.ctr.capRound !== s.round) { u.ctr.capRound = s.round; u.ctr.capTaken = 0; }
        const d = Math.max(0, Math.min(dmg, p.cap - u.ctr.capTaken));
        u.ctr.capTaken += d;
        return d;
      },
    },
    beatOfDeath: {
      name: 'Beat of Death',
      desc: (p) => 'Whenever an enemy attacks or uses an ability, that enemy takes ' + p.d + ' damage.',
      onEnemyAct(s, u, p, actor) {
        if (actor.alive && !actor.object) B.hit(s, u, actor, p.d, { kind: 'true', label: 'Beat of Death' });
      },
    },
    inevitable: {
      name: 'Inevitable',
      desc: (p) => 'Gains +' + p.atk + ' ATK at the start of every round after the first.',
      roundStart(s, u, p) { if (s.round > 1) buff(s, u, p.atk, 'Inevitable'); },
    },
    echoes: {
      name: 'Echoes',
      desc: (p) => 'Every ' + p.every + ' rounds, ' + p.n + ' Echoes of old games appear beside it (up to ' + p.max + ').',
      roundStart(s, u, p) {
        if (s.round % p.every !== 0) return;
        const room = Math.min(p.n, p.max - countOwned(s, u, 'echo'));
        const cells = emptyAround(s, u.x, u.y, false);
        for (let k = 0; k < room && k < cells.length; k++) {
          const e = B.summon(s, 'echo', u.side, cells[k], { owner: u.uid });
          if (e) B.emit(s, 'note', { uid: e.uid, text: 'echoes' });
        }
      },
    },
    doubleMove: {
      name: 'Double Move',
      desc: () => 'Takes two turns every round: one before anything else moves, and one in its place in the queue.',
      roundStart(s, u) { s.extra.push(u.uid); },
    },
  };

  // Units with aura passives are flagged so damage maths can skip the rest.
  AG.refreshFlags = function (u) {
    u.aura = false;
    for (const k in u.pas) {
      const P = AG.Passives[k];
      if (P && (P.auraIn || P.auraOut)) u.aura = true;
    }
  };
})(globalThis.AG = globalThis.AG || {});
