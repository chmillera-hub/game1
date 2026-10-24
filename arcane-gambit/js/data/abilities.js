/* Active abilities. Each has a cooldown (in the user's own turns), a target
   kind, targets(s,u,p) listing legal targets (unit uids or square indices)
   and exec(s,u,target,p). `kind` tells the AI and the UI what it is for. */
(function (AG) {
  'use strict';
  const B = AG.B;

  function foes(s, u, r, los) {
    const out = [];
    const b = s.board;
    const ui = u.y * b.w + u.x;
    for (const o of s.units) {
      if (!o.alive || o.side === u.side || o.st.stealth) continue;
      if (AG.cheb(u.x, u.y, o.x, o.y) > r) continue;
      if (los && !b.los[ui * b.n + o.y * b.w + o.x]) continue;
      out.push(o.uid);
    }
    return out;
  }
  function allies(s, u, r, self, pred) {
    const out = [];
    for (const o of s.units) {
      if (!o.alive || o.side !== u.side || o.object) continue;
      if (o === u && !self) continue;
      if (AG.cheb(u.x, u.y, o.x, o.y) > r) continue;
      if (pred && !pred(o)) continue;
      out.push(o.uid);
    }
    return out;
  }
  // Squares worth aiming an area spell at: on or next to a visible enemy.
  function areaCells(s, u, range, los, radius) {
    const b = s.board;
    const ui = u.y * b.w + u.x;
    const seen = new Uint8Array(b.n);
    const out = [];
    radius = radius == null ? 1 : radius;
    for (const o of s.units) {
      if (!o.alive || o.side === u.side) continue;
      for (let dy = -radius; dy <= radius; dy++) {
        for (let dx = -radius; dx <= radius; dx++) {
          const x = o.x + dx, y = o.y + dy;
          if (!AG.inBounds(b, x, y)) continue;
          const j = y * b.w + x;
          if (seen[j] || b.terr[j] === AG.TER.WALL || b.terr[j] === AG.TER.VOID) continue;
          if (AG.cheb(u.x, u.y, x, y) > range) continue;
          if (los && !b.los[ui * b.n + j]) continue;
          seen[j] = 1;
          out.push(j);
        }
      }
    }
    return out;
  }
  function unitsInArea(s, i, r) {
    const b = s.board;
    const cx = i % b.w, cy = (i / b.w) | 0;
    const out = [];
    for (const o of s.units) {
      if (o.alive && AG.cheb(o.x, o.y, cx, cy) <= r) out.push(o);
    }
    return out;
  }
  function hasFoeWithin(s, u, r) {
    for (const o of s.units) if (o.alive && o.side !== u.side && !o.object && AG.cheb(u.x, u.y, o.x, o.y) <= r) return true;
    return false;
  }
  function lineFoes(s, u, range, dirs) {
    const out = [];
    for (const [dx, dy] of AG.dirsFor(dirs)) {
      let x = u.x, y = u.y;
      for (let k = 1; k <= range; k++) {
        x += dx; y += dy;
        if (!AG.inBounds(s.board, x, y)) break;
        const j = y * s.board.w + x;
        if (s.board.terr[j] === AG.TER.WALL) break;
        const id = s.occ[j];
        if (!id) continue;
        const o = B.U(s, id);
        if (o.side !== u.side && !o.st.stealth) out.push(o.uid);
        break;
      }
    }
    return out;
  }
  AG.abilityHelpers = { foes, allies, areaCells, unitsInArea, hasFoeWithin, lineFoes };

  AG.Abilities = {
    mend: {
      name: 'Mend', icon: '✚', cd: 2, target: 'ally', kind: 'heal', vfx: 'heal',
      p: { heal: 5, range: 3, shield: 0 },
      desc: (p) => 'Heal an ally within ' + p.range + ' for ' + p.heal + (p.shield ? ' and give it ' + p.shield + ' shield.' : '.'),
      targets(s, u, p) { return allies(s, u, p.range, true, (o) => o.hp < o.maxHp || (p.shield && o.shield < 6)); },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        B.heal(s, u, o, p.heal);
        if (p.shield) B.giveShield(s, o, p.shield);
      },
    },
    arcaneBolt: {
      name: 'Arcane Bolt', icon: '✦', cd: 3, target: 'enemy', kind: 'damage', hostile: true, vfx: 'arcane',
      p: { dmg: 6, range: 4, chain: 0 },
      desc: (p) => 'Blast an enemy within ' + p.range + ' for ' + p.dmg + (p.chain ? '; it arcs to one adjacent enemy for ' + p.chain + '.' : '.'),
      targets(s, u, p) { return foes(s, u, p.range, true); },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        const ox = o.x, oy = o.y;
        B.hit(s, u, o, p.dmg, { kind: 'ability', tag: 'arcane' });
        if (p.chain) {
          const next = AG.adjacentUnits(s, ox, oy, (q) => q.side !== u.side && q !== o)[0];
          if (next) { B.emit(s, 'chain', { from: [ox, oy], to: [next.x, next.y] }); B.hit(s, u, next, p.chain, { kind: 'ability', tag: 'arcane' }); }
        }
      },
    },
    taunt: {
      name: 'Taunt', icon: '⚑', cd: 3, target: 'self', kind: 'cc', hostile: true, vfx: 'taunt',
      p: { r: 2 },
      desc: (p) => 'Enemies within ' + p.r + ' must attack this unit on their next turn if they can.',
      targets(s, u, p) { return hasFoeWithin(s, u, p.r) ? [u.uid] : []; },
      exec(s, u, t, p) {
        B.emit(s, 'aoe', { cells: [[u.x, u.y]], r: p.r, vfx: 'taunt' });
        for (const o of s.units) {
          if (o.alive && o.side !== u.side && !o.object && AG.cheb(u.x, u.y, o.x, o.y) <= p.r) B.addStatus(s, o, 'taunt', { by: u.uid });
        }
      },
    },
    fireball: {
      name: 'Fireball', icon: '☄', cd: 3, target: 'cell', kind: 'damage', hostile: true, vfx: 'fire',
      p: { dmg: 4, splash: 2, range: 4, burn: 1 },
      desc: (p) => 'Hurl a fireball at a square within ' + p.range + ': ' + p.dmg + ' damage there and ' + p.splash + ' to everything around it (allies too). Everything hit Burns.',
      targets(s, u, p) { return areaCells(s, u, p.range, true, 1); },
      exec(s, u, i, p) {
        B.emit(s, 'aoe', { cells: [B.xy(s, i)], r: 1, vfx: 'fire' });
        for (const o of unitsInArea(s, i, 1)) {
          if (o === u) continue;
          const center = o.y * s.board.w + o.x === i;
          B.hit(s, u, o, center ? p.dmg : p.splash, { kind: 'ability', tag: 'fire' });
          if (o.alive) B.addStatus(s, o, 'burn', { d: p.burn, t: 2 });
        }
      },
    },
    flashFreeze: {
      name: 'Flash Freeze', icon: '❄', cd: 4, target: 'enemy', kind: 'cc', hostile: true, vfx: 'frost',
      p: { range: 3, t: 1, area: false },
      desc: (p) => 'Freeze an enemy within ' + p.range + ': it skips its next ' + (p.t > 1 ? p.t + ' turns' : 'turn') + ' and takes +2 damage from hits while frozen.' + (p.area ? ' Enemies next to it are Chilled.' : ''),
      targets(s, u, p) { return foes(s, u, p.range, true).filter((id) => !B.U(s, id).st.frozen && !B.U(s, id).object); },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        B.addStatus(s, o, 'frozen', { t: p.t });
        if (p.area) {
          B.emit(s, 'aoe', { cells: [[o.x, o.y]], r: 1, vfx: 'frost' });
          for (const q of AG.adjacentUnits(s, o.x, o.y, (q) => q.side !== u.side)) B.addStatus(s, q, 'chill', { a: 2 });
        }
      },
    },
    thunderclap: {
      name: 'Thunderclap', icon: '⚡', cd: 3, target: 'self', kind: 'damage', hostile: true, vfx: 'storm',
      p: { dmg: 3, r: 1 },
      desc: (p) => 'Deal ' + p.dmg + ' to every enemy within ' + p.r + ' and knock them back a square. Chasms swallow those who cannot fly.',
      targets(s, u, p) { return hasFoeWithin(s, u, p.r) ? [u.uid] : []; },
      exec(s, u, t, p) {
        B.emit(s, 'aoe', { cells: [[u.x, u.y]], r: p.r, vfx: 'storm' });
        const hit = s.units.filter((o) => o.alive && o.side !== u.side && AG.cheb(u.x, u.y, o.x, o.y) <= p.r);
        // Push the farthest first so neighbours do not collide needlessly.
        hit.sort((a, b) => AG.cheb(u.x, u.y, b.x, b.y) - AG.cheb(u.x, u.y, a.x, a.y));
        for (const o of hit) {
          B.hit(s, u, o, p.dmg, { kind: 'ability', tag: 'storm' });
          if (o.alive) B.push(s, u, o, AG.sign(o.x - u.x), AG.sign(o.y - u.y));
        }
      },
    },
    corpseExplosion: {
      name: 'Corpse Explosion', icon: '✹', cd: 3, target: 'ally', kind: 'damage', hostile: true, vfx: 'bone',
      p: { dmg: 4, range: 4 },
      desc: (p) => 'Detonate one of your Skeletons within ' + p.range + ': ' + p.dmg + ' damage to every enemy next to it.',
      targets(s, u, p) {
        return allies(s, u, p.range, false, (o) => o.def === 'skeleton').filter((id) => {
          const o = B.U(s, id);
          return AG.adjacentUnits(s, o.x, o.y, (q) => q.side !== u.side).length > 0;
        });
      },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        const x = o.x, y = o.y;
        B.emit(s, 'aoe', { cells: [[x, y]], r: 1, vfx: 'bone' });
        B.kill(s, o, null, { kind: 'sacrifice' });
        for (const q of AG.adjacentUnits(s, x, y, (q) => q.side !== u.side)) B.hit(s, u, q, p.dmg, { kind: 'ability', tag: 'shadow' });
      },
    },
    divineShield: {
      name: 'Divine Shield', icon: '⛨', cd: 3, target: 'ally', kind: 'buff', vfx: 'holy',
      p: { amt: 6, range: 3, cleanse: false },
      desc: (p) => 'Give an ally within ' + p.range + ' (or itself) ' + p.amt + ' shield' + (p.cleanse ? ' and remove its afflictions.' : '.'),
      targets(s, u, p) { return allies(s, u, p.range, true, (o) => o.shield < 8 || (p.cleanse && hasBad(o))); },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        B.giveShield(s, o, p.amt);
        if (p.cleanse) B.cleanse(s, o);
      },
    },
    pinningShot: {
      name: 'Pinning Shot', icon: '➹', cd: 3, target: 'enemy', kind: 'cc', hostile: true, vfx: 'arrow',
      p: { dmg: 3, range: 6 },
      desc: (p) => 'Shoot the first enemy along a line (up to ' + p.range + '): ' + p.dmg + ' damage and it is Rooted for a turn.',
      targets(s, u, p) { return lineFoes(s, u, p.range, 'all'); },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        B.emit(s, 'attack', { uid: u.uid, tgt: o.uid, from: [u.x, u.y], to: [o.x, o.y], vfx: 'arrow' });
        B.hit(s, u, o, p.dmg, { kind: 'ability' });
        if (o.alive) B.addStatus(s, o, 'rooted', { t: 1 });
      },
    },
    switcheroo: {
      name: 'Switcheroo', icon: '⇄', cd: 3, target: 'unit', kind: 'swap', vfx: 'arcane',
      p: { range: 4, stun: false },
      desc: (p) => 'Trade places with any unit within ' + p.range + '.' + (p.stun ? ' An enemy swapped this way is Stunned.' : ''),
      targets(s, u, p) {
        const out = [];
        for (const o of s.units) {
          if (!o.alive || o === u || o.pas.unmovable || o.big || o.object || o.st.stealth) continue;
          if (AG.cheb(u.x, u.y, o.x, o.y) > p.range) continue;
          if (!AG.standable(s.board, o.y * s.board.w + o.x, u.flying) || !AG.standable(s.board, u.y * s.board.w + u.x, o.flying)) continue;
          out.push(o.uid);
        }
        return out;
      },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        if (B.swap(s, u, o) && p.stun && o.side !== u.side) B.addStatus(s, o, 'stunned', { t: 1 });
      },
    },
    haste: {
      name: 'Haste', icon: '⧗', cd: 3, target: 'ally', kind: 'tempo', vfx: 'time',
      p: { range: 4, spd: 0 },
      desc: (p) => 'An ally within ' + p.range + ' takes an extra turn right away.' + (p.spd ? ' It also gains +' + p.spd + ' SPD for the rest of the battle (up to +4).' : ''),
      targets(s, u, p) {
        if (s.extra.length) return [];
        return allies(s, u, p.range, false, (o) => !o.noTurn && !o.st.frozen && !o.st.stunned && o.at);
      },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        s.extra.push(o.uid);
        B.emit(s, 'note', { uid: o.uid, text: 'hasted!' });
        if (p.spd && (o.ctr.accel || 0) < 4) {
          o.ctr.accel = (o.ctr.accel || 0) + p.spd;
          o.spd += p.spd;
        }
      },
    },
    hex: {
      name: 'Hex', icon: '⛧', cd: 3, target: 'enemy', kind: 'cc', hostile: true, vfx: 'shadow',
      p: { range: 4, a: 2, r: 2, dot: 0 },
      desc: (p) => 'Curse an enemy within ' + p.range + ': it takes +' + p.a + ' damage from every hit for ' + p.r + ' rounds' + (p.dot ? ' and suffers ' + p.dot + ' damage each turn.' : '.'),
      targets(s, u, p) { return foes(s, u, p.range, false).filter((id) => !B.U(s, id).st.cursed && !B.U(s, id).object); },
      exec(s, u, t, p) { B.addStatus(s, B.U(s, t), 'cursed', { a: p.a, r: p.r, dot: p.dot }); },
    },
    summonWolf: {
      name: 'Call Wolf', icon: '☾', cd: 3, target: 'cell', kind: 'summon', vfx: 'nature',
      p: { max: 2, hp: 0, atk: 0, def: 'spiritWolf' },
      desc: (p) => 'Summon a Spirit Wolf beside itself (up to ' + p.max + ' at once).',
      targets(s, u, p) {
        if (AG.countOwned(s, u, p.def) >= p.max) return [];
        return AG.emptyAround(s, u.x, u.y, false);
      },
      exec(s, u, i, p) { B.summon(s, p.def, u.side, i, { owner: u.uid, mods: { hp: p.hp, atk: p.atk } }); },
    },
    entangle: {
      name: 'Entangle', icon: '❦', cd: 4, target: 'cell', kind: 'cc', hostile: true, vfx: 'nature',
      p: { range: 3, dmg: 1 },
      desc: (p) => 'Vines erupt in a 3×3 area within ' + p.range + ': enemies there take ' + p.dmg + ' and are Rooted.',
      targets(s, u, p) { return areaCells(s, u, p.range, false, 1); },
      exec(s, u, i, p) {
        B.emit(s, 'aoe', { cells: [B.xy(s, i)], r: 1, vfx: 'nature' });
        for (const o of unitsInArea(s, i, 1)) {
          if (o.side === u.side) continue;
          B.hit(s, u, o, p.dmg, { kind: 'ability', tag: 'nature' });
          if (o.alive) B.addStatus(s, o, 'rooted', { t: 1 });
        }
      },
    },
    meteor: {
      name: 'Meteor', icon: '☄', cd: 4, target: 'cell', kind: 'damage', hostile: true, vfx: 'meteor',
      p: { dmg: 5, range: 5 },
      desc: (p) => 'Call down a meteor on a 3×3 area within ' + p.range + ': ' + p.dmg + ' damage to everything there (allies too) and Burn.',
      targets(s, u, p) { return areaCells(s, u, p.range, false, 1); },
      exec(s, u, i, p) {
        B.emit(s, 'aoe', { cells: [B.xy(s, i)], r: 1, vfx: 'meteor' });
        for (const o of unitsInArea(s, i, 1)) {
          if (o === u) continue;
          B.hit(s, u, o, p.dmg, { kind: 'ability', tag: 'fire' });
          if (o.alive) B.addStatus(s, o, 'burn', { d: 1, t: 2 });
        }
      },
    },
    arcaneBarrier: {
      name: 'Arcane Barrier', icon: '◈', cd: 4, target: 'self', kind: 'buff', vfx: 'arcane',
      p: { amt: 4, r: 2 },
      desc: (p) => 'All allies within ' + p.r + ' (and itself) gain ' + p.amt + ' shield.',
      targets(s, u, p) { return allies(s, u, p.r, true, (o) => o.shield < 6).length >= 2 ? [u.uid] : []; },
      exec(s, u, t, p) {
        B.emit(s, 'aoe', { cells: [[u.x, u.y]], r: p.r, vfx: 'arcane' });
        for (const id of allies(s, u, p.r, true)) B.giveShield(s, B.U(s, id), p.amt);
      },
    },
    warCry: {
      name: 'War Cry', icon: '♪', cd: 4, target: 'self', kind: 'buff', vfx: 'rally',
      p: { r: 3, spd: 2, heal: 2, tag: null },
      desc: (p) => 'Allies within ' + p.r + (p.tag ? ' (' + p.tag + 's)' : '') + ' gain +' + p.spd + ' SPD until the end of next round' + (p.heal ? ' and heal ' + p.heal + '.' : '.'),
      targets(s, u, p) {
        const n = allies(s, u, p.r, false, (o) => !p.tag || o.tags.indexOf(p.tag) >= 0).length;
        return n >= 1 && s.units.some((o) => o.alive && o.side !== u.side) ? [u.uid] : [];
      },
      exec(s, u, t, p) {
        B.emit(s, 'aoe', { cells: [[u.x, u.y]], r: p.r, vfx: 'rally' });
        for (const id of allies(s, u, p.r, true, (o) => !p.tag || o.tags.indexOf(p.tag) >= 0)) {
          const o = B.U(s, id);
          B.addStatus(s, o, 'haste', { a: p.spd });
          if (p.heal) B.heal(s, u, o, p.heal, true);
        }
      },
    },
    callGuards: {
      name: 'Call the Guard', icon: '♜', cd: 3, target: 'self', kind: 'summon', vfx: 'rally',
      p: { n: 2, def: 'goblin', max: 4 },
      desc: (p) => 'Summon ' + p.n + ' ' + AG.Units[p.def].name + 's beside itself (up to ' + p.max + ' at a time).',
      targets(s, u, p) {
        if (AG.countOwned(s, u, p.def) >= p.max) return [];
        return AG.emptyAround(s, u.x, u.y, false).length ? [u.uid] : [];
      },
      exec(s, u, t, p) {
        const cells = AG.emptyAround(s, u.x, u.y, false);
        // Prefer squares toward the enemy.
        const dir = u.side === 1 ? 1 : -1;
        cells.sort((a, b) => dir * (((b / s.board.w) | 0) - ((a / s.board.w) | 0)));
        const room = Math.min(p.n, p.max - AG.countOwned(s, u, p.def));
        for (let k = 0; k < room && k < cells.length; k++) B.summon(s, p.def, u.side, cells[k], { owner: u.uid });
      },
    },
    wail: {
      name: 'Wail', icon: '♒', cd: 3, target: 'self', kind: 'damage', hostile: true, vfx: 'shadow',
      p: { r: 2, dmg: 2, chill: 2 },
      desc: (p) => 'A dreadful scream: enemies within ' + p.r + ' take ' + p.dmg + ' and are Chilled.',
      targets(s, u, p) { return hasFoeWithin(s, u, p.r) ? [u.uid] : []; },
      exec(s, u, t, p) {
        B.emit(s, 'aoe', { cells: [[u.x, u.y]], r: p.r, vfx: 'shadow' });
        for (const o of s.units.slice()) {
          if (!o.alive || o.side === u.side || AG.cheb(u.x, u.y, o.x, o.y) > p.r) continue;
          B.hit(s, u, o, p.dmg, { kind: 'ability', tag: 'shadow' });
          if (o.alive) B.addStatus(s, o, 'chill', { a: p.chill });
        }
      },
    },
    frostNova: {
      name: 'Frost Nova', icon: '✲', cd: 3, target: 'self', kind: 'cc', hostile: true, vfx: 'frost',
      p: { r: 1, dmg: 2 },
      desc: (p) => 'Enemies within ' + p.r + ' take ' + p.dmg + ' and are Frozen.',
      targets(s, u, p) { return hasFoeWithin(s, u, p.r) ? [u.uid] : []; },
      exec(s, u, t, p) {
        B.emit(s, 'aoe', { cells: [[u.x, u.y]], r: p.r, vfx: 'frost' });
        for (const o of s.units.slice()) {
          if (!o.alive || o.side === u.side || AG.cheb(u.x, u.y, o.x, o.y) > p.r) continue;
          B.hit(s, u, o, p.dmg, { kind: 'ability', tag: 'frost' });
          if (o.alive) B.addStatus(s, o, 'frozen', { t: 1 });
        }
      },
    },
    laser: {
      name: 'Annihilation Beam', icon: '═', cd: 2, target: 'enemy', kind: 'damage', hostile: true, vfx: 'beam',
      p: { dmg: 5, range: 7 },
      desc: (p) => 'Fire a beam along a rank or file (up to ' + p.range + '): ' + p.dmg + ' damage to every enemy in the line.',
      targets(s, u, p) { return lineFoes(s, u, p.range, 'orth'); },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        const dx = AG.sign(o.x - u.x), dy = AG.sign(o.y - u.y);
        let x = u.x, y = u.y, ex = x, ey = y;
        const victims = [];
        for (let k = 1; k <= p.range; k++) {
          x += dx; y += dy;
          if (!AG.inBounds(s.board, x, y) || s.board.terr[y * s.board.w + x] === AG.TER.WALL) break;
          ex = x; ey = y;
          const id = s.occ[y * s.board.w + x];
          if (id && B.U(s, id).side !== u.side) victims.push(B.U(s, id));
        }
        B.emit(s, 'beam', { from: [u.x, u.y], to: [ex, ey] });
        for (const v of victims) B.hit(s, u, v, p.dmg, { kind: 'ability', tag: 'arcane' });
      },
    },
    castling: {
      name: 'Castling', icon: '♖', cd: 4, target: 'ally', kind: 'swap', vfx: 'arcane',
      p: {},
      desc: () => 'Swap places with any allied Rook on the board.',
      targets(s, u) { return allies(s, u, 99, false, (o) => o.tags.indexOf('rook') >= 0); },
      exec(s, u, t) { B.swap(s, u, B.U(s, t)); },
    },
    batSwarm: {
      name: 'Bat Swarm', icon: '⌒', cd: 4, target: 'self', kind: 'summon', vfx: 'shadow',
      p: { n: 2, max: 4 },
      desc: (p) => 'Summon ' + p.n + ' bats beside itself (up to ' + p.max + ').',
      targets(s, u, p) {
        if (AG.countOwned(s, u, 'bat') >= p.max) return [];
        return AG.emptyAround(s, u.x, u.y, false).length ? [u.uid] : [];
      },
      exec(s, u, t, p) {
        const cells = AG.emptyAround(s, u.x, u.y, false);
        for (let k = 0; k < p.n && k < cells.length; k++) B.summon(s, 'bat', u.side, cells[k], { owner: u.uid });
      },
    },
    elixir: {
      name: 'Elixir', icon: '⚗', cd: 2, target: 'ally', kind: 'buff', vfx: 'heal',
      p: { range: 2, heal: 3, emp: 2 },
      desc: (p) => 'An ally within ' + p.range + ' heals ' + p.heal + ' and its next attack deals +' + p.emp + '.',
      targets(s, u, p) { return allies(s, u, p.range, false, (o) => o.at && !o.st.emp); },
      exec(s, u, t, p) {
        const o = B.U(s, t);
        B.heal(s, u, o, p.heal);
        B.addStatus(s, o, 'emp', { a: p.emp });
      },
    },
    soulDrain: {
      name: 'Soul Drain', icon: '♆', cd: 3, target: 'enemy', kind: 'damage', hostile: true, vfx: 'shadow',
      p: { dmg: 4, range: 4 },
      desc: (p) => 'Drain ' + p.dmg + ' life from an enemy within ' + p.range + ', healing itself.',
      targets(s, u, p) { return foes(s, u, p.range, true); },
      exec(s, u, t, p) {
        const d = B.hit(s, u, B.U(s, t), p.dmg, { kind: 'ability', tag: 'shadow' });
        B.heal(s, u, u, d);
      },
    },
    queenStorm: {
      name: 'Checkmate Storm', icon: '♛', cd: 3, target: 'cell', kind: 'damage', hostile: true, vfx: 'arcane',
      p: { dmg: 4, range: 5 },
      desc: (p) => 'Arcane lightning strikes a 3×3 area within ' + p.range + ' for ' + p.dmg + ' (enemies only).',
      targets(s, u, p) { return areaCells(s, u, p.range, false, 1); },
      exec(s, u, i, p) {
        B.emit(s, 'aoe', { cells: [B.xy(s, i)], r: 1, vfx: 'arcane' });
        for (const o of unitsInArea(s, i, 1)) if (o.side !== u.side) B.hit(s, u, o, p.dmg, { kind: 'ability', tag: 'arcane' });
      },
    },
  };

  function hasBad(o) {
    return !!(o.st.burn || o.st.poison || o.st.chill || o.st.frozen || o.st.stunned || o.st.rooted || o.st.marked || o.st.cursed);
  }
})(globalThis.AG = globalThis.AG || {});
