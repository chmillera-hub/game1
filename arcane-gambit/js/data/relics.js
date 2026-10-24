/* Relics: run-wide trinkets. Battle hooks receive (s, side, ...). Fields
   such as supply, slots, gold, winHeal, discount and maxResolve are read by
   the run layer. */
(function (AG) {
  'use strict';
  const B = AG.B;
  const mine = (s, side) => s.units.filter((u) => u.alive && u.side === side && !u.object);

  AG.Relics = {
    warBanner: {
      name: 'War Banner', icon: '⚑', rarity: 'common',
      desc: 'Each of your units’ first attack deals +2.',
      battleStart(s, side) { for (const u of mine(s, side)) B.addStatus(s, u, 'emp', { a: 2 }); },
    },
    ledger: {
      name: 'Quartermaster’s Ledger', icon: '▤', rarity: 'common', supply: 2,
      desc: '+2 supply in every battle.',
    },
    recruitHorn: {
      name: 'Recruiter’s Horn', icon: '♫', rarity: 'uncommon', slots: 1,
      desc: '+1 unit slot in every battle.',
    },
    ironRations: {
      name: 'Iron Rations', icon: '▣', rarity: 'common',
      desc: 'Your units start each battle with 3 shield.',
      battleStart(s, side) { for (const u of mine(s, side)) B.giveShield(s, u, 3, true); },
    },
    wingedBoots: {
      name: 'Winged Boots', icon: '⟰', rarity: 'common',
      desc: 'Your units have +1 SPD.',
      battleStart(s, side) { for (const u of mine(s, side)) u.spd += 1; },
    },
    whetstone: {
      name: 'Whetstone', icon: '◆', rarity: 'common',
      desc: 'Your melee units have +1 ATK.',
      battleStart(s, side) { for (const u of mine(s, side)) if (B.isMelee(u.at)) u.atk += 1; },
    },
    spyglass: {
      name: 'Spyglass', icon: '⌕', rarity: 'common',
      desc: 'Your ranged units reach 1 square further.',
      battleStart(s, side) {
        for (const u of mine(s, side)) {
          if (u.at && (u.at.pattern === 'ranged' || u.at.pattern === 'line' || u.at.pattern === 'lob')) u.at = Object.assign({}, u.at, { range: u.at.range + 1 });
        }
      },
    },
    healingSpring: {
      name: 'Healing Spring', icon: '❀', rarity: 'common', winHeal: 5,
      desc: 'Recover 5 Resolve after every victory.',
    },
    goldTooth: {
      name: 'Gold Tooth', icon: '◉', rarity: 'common', gold: 12,
      desc: '+12 gold after every victory.',
    },
    bloodstone: {
      name: 'Bloodstone', icon: '♦', rarity: 'uncommon',
      desc: 'Whenever one of your units kills an enemy, it heals 3.',
      onEnemyDeath(s, side, victim, killer) { if (killer && killer.alive && killer.side === side) B.heal(s, killer, killer, 3); },
    },
    emberHeart: {
      name: 'Ember Heart', icon: '♨', rarity: 'uncommon',
      desc: 'Your fire units have +1 ATK, and everything your units set alight burns for 1 more.',
      battleStart(s, side) {
        for (const u of mine(s, side)) {
          if (u.tags.indexOf('fire') >= 0) u.atk += 1;
          if (u.at && u.at.fx && u.at.fx.burn) {
            u.at = Object.assign({}, u.at, { fx: Object.assign({}, u.at.fx, { burn: { d: u.at.fx.burn.d + 1, t: u.at.fx.burn.t } }) });
          }
          u.abil = u.abil.map((a) => (a.p.burn ? { id: a.id, p: Object.assign({}, a.p, { burn: a.p.burn + 1 }) } : a));
        }
      },
    },
    phylacteryShard: {
      name: 'Phylactery Shard', icon: '◊', rarity: 'uncommon',
      desc: 'The first of your units to fall in each battle rises again at once with half its health.',
      onAllyDeath(s, side, u) {
        if (s.flags['shard' + side] || u.summoned || u.object) return;
        s.flags['shard' + side] = true;
        const r = B.summon(s, u.def, side, u.y * s.board.w + u.x, { talents: u.talents, rune: u.rune, rank: u.rank, hpPct: 0.5 });
        if (r) { r.summoned = false; B.emit(s, 'note', { uid: r.uid, text: 'rises again!' }); }
      },
    },
    thunderDrum: {
      name: 'Thunder Drum', icon: '◍', rarity: 'uncommon',
      desc: 'At the start of round 3, every enemy takes 3 damage.',
      roundStart(s, side) {
        if (s.round !== 3) return;
        B.emit(s, 'storm', { dmg: 3, side: 1 - side, label: 'Thunder Drum' });
        for (const u of s.units.slice()) if (u.alive && u.side !== side && !u.object) B.hit(s, null, u, 3, { kind: 'true', label: 'Thunder Drum' });
      },
    },
    hourglass: {
      name: 'Cracked Hourglass', icon: '⧗', rarity: 'rare',
      desc: 'In the first round, your fastest unit takes an extra turn before anyone else.',
      afterQueue(s, side) {
        if (s.round !== 1) return;
        const id = s.queue.find((uid) => B.U(s, uid).side === side);
        if (id) s.extra.push(id);
      },
    },
    sentryLantern: {
      name: 'Sentry’s Lantern', icon: '☀', rarity: 'common',
      desc: 'Enemies start the battle Marked (+1 damage taken) for the first two rounds.',
      battleStart(s, side) {
        for (const u of s.units) if (u.alive && u.side !== side && !u.object) { u.st.marked = { a: 1, until: 2 }; }
      },
    },
    martyrsLocket: {
      name: 'Martyr’s Locket', icon: '♡', rarity: 'uncommon',
      desc: 'When one of your units dies, allies next to it gain +2 ATK.',
      onAllyDeath(s, side, u) {
        for (const o of AG.adjacentUnits(s, u.x, u.y, (o) => o.side === side && !o.object)) {
          o.atk += 2;
          B.emit(s, 'buff', { uid: o.uid, label: 'Vengeance', atk: o.atk });
        }
      },
    },
    grimoire: {
      name: 'Grimoire of Haste', icon: '❖', rarity: 'rare',
      desc: 'Your units’ ability cooldowns are 1 turn shorter.',
      battleStart(s, side) { for (const u of mine(s, side)) if (u.abil.length) u.pas = Object.assign({}, u.pas, { spellweaver: {} }); },
    },
    ironCrown: {
      name: 'Iron Crown', icon: '♔', rarity: 'uncommon',
      desc: 'Your most expensive unit gets +6 HP and +1 armor.',
      battleStart(s, side) {
        let best = null;
        for (const u of mine(s, side)) {
          const c = (AG.Units[u.def].cost || 0);
          if (!best || c > (AG.Units[best.def].cost || 0)) best = u;
        }
        if (best) { best.maxHp += 6; best.hp += 6; best.armor += 1; }
      },
    },
    vanguardStandard: {
      name: 'Vanguard Standard', icon: '⚐', rarity: 'common',
      desc: 'Units deployed on your front line start with 5 shield.',
      battleStart(s, side) {
        if (side !== 0) return;
        let front = 999;
        for (let i = 0; i < s.board.n; i++) if (s.board.deploy[i]) front = Math.min(front, (i / s.board.w) | 0);
        for (const u of mine(s, side)) if (u.y === front) B.giveShield(s, u, 5, true);
      },
    },
    pawnBadge: {
      name: 'Pawnmaster’s Badge', icon: '♙', rarity: 'common',
      desc: 'Units that cost 2 or less get +2 HP and +1 ATK.',
      battleStart(s, side) {
        for (const u of mine(s, side)) {
          const d = AG.Units[u.def];
          if (d.cost != null && d.cost <= 2) { u.maxHp += 2; u.hp += 2; u.atk += 1; }
        }
      },
    },
    luckyCoin: {
      name: 'Lucky Coin', icon: '¤', rarity: 'common', discount: 0.25,
      desc: 'Shop prices are 25% lower.',
    },
    aegis: {
      name: 'Commander’s Aegis', icon: '⛉', rarity: 'uncommon', maxResolve: 10,
      desc: '+10 maximum Resolve.',
    },
    crownOfCommand: {
      name: 'Crown of Command', icon: '♕', rarity: 'boss', supply: 3, slots: 1,
      desc: '+3 supply and +1 unit slot in every battle.',
    },
    stormHeart: {
      name: 'Storm Heart', icon: 'ϟ', rarity: 'boss',
      desc: 'At the start of every round, each enemy takes 1 damage.',
      roundStart(s, side) {
        for (const u of s.units.slice()) if (u.alive && u.side !== side && !u.object) B.hit(s, null, u, 1, { kind: 'true', label: 'Storm Heart' });
      },
    },
    phoenixAsh: {
      name: 'Phoenix Ash', icon: '✺', rarity: 'boss',
      desc: 'Your units heal 2 at the start of every round.',
      roundStart(s, side) { for (const u of mine(s, side)) B.heal(s, u, u, 2, true); },
    },
    tacticsTome: {
      name: 'Tome of Tactics', icon: '♗', rarity: 'boss', supply: 2,
      desc: '+2 supply, and talents cost 1 less (minimum 1).', talentDiscount: 1,
    },
  };

  AG.relicList = function (filter) {
    return Object.keys(AG.Relics).filter((k) => !filter || filter(AG.Relics[k], k));
  };
})(globalThis.AG = globalThis.AG || {});
