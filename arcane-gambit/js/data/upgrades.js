/* Upgrades you spend supply on before a battle.
   Talents: each unit type has three; a unit may take one (two once trained
   to Elite). Runes: generic items from your satchel; one per unit, and each
   rune you own can only be socketed into one unit per battle. */
(function (AG) {
  'use strict';

  const set = (u, key, patch) => { u[key] = Object.assign({}, u[key], patch); };
  const ability = (u, id) => u.abil.find((a) => a.id === id);
  const tweak = (u, id, patch) => { const a = ability(u, id); if (a) a.p = Object.assign({}, a.p, patch); };
  const addPassive = (u, id, p) => { u.pas = Object.assign({}, u.pas); u.pas[id] = p || {}; };
  const fx = (u, patch) => { u.at = Object.assign({}, u.at); u.at.fx = Object.assign({}, u.at.fx, patch); };

  AG.Talents = {
    // Squire
    pikeman: { unit: 'squire', name: 'Pike Drill', cost: 1, desc: 'Attacks reach 2 squares in straight lines, striking past allies.',
      apply(u) { u.at = { pattern: 'reach', range: 2, dirs: 'all', vfx: 'pierce' }; } },
    stout: { unit: 'squire', name: 'Stout', cost: 1, desc: '+5 HP.', apply(u) { u.maxHp += 5; } },
    eager: { unit: 'squire', name: 'Eager', cost: 1, desc: '+3 SPD.', apply(u) { u.spd += 3; } },
    // Knight
    destrier: { unit: 'knight', name: 'Destrier', cost: 2, desc: '+3 SPD.', apply(u) { u.spd += 3; } },
    lancer: { unit: 'knight', name: 'Lancer', cost: 2, desc: 'Also strikes enemies a knight’s leap away. Kills capture the square.',
      apply(u) { set(u, 'at', { also: [{ pattern: 'offsets' }], capture: true, vfx: 'lance' }); } },
    barding: { unit: 'knight', name: 'Barding', cost: 1, desc: '+1 armor and +3 HP.', apply(u) { u.armor += 1; u.maxHp += 3; } },
    // Scout
    hawkeye: { unit: 'scout', name: 'Hawkeye', cost: 1, desc: '+2 attack range.', apply(u) { set(u, 'at', { range: u.at.range + 2 }); } },
    poisonDarts: { unit: 'scout', name: 'Poison Darts', cost: 2, desc: 'Hits also Poison: 1 damage a turn for 3 turns, stacking.',
      apply(u) { fx(u, { poison: { d: 1, t: 3 } }); } },
    openingShot: { unit: 'scout', name: 'Opening Shot', cost: 1, desc: 'Its first attack of the battle deals +4.',
      apply(u) { addPassive(u, 'ambusher', { bonus: 4 }); } },
    // Cleric
    sanctuary: { unit: 'cleric', name: 'Sanctuary', cost: 1, desc: 'Mend also gives 3 shield.', apply(u) { tweak(u, 'mend', { shield: 3 }); } },
    radiance: { unit: 'cleric', name: 'Radiance', cost: 2, desc: 'Smite pierces every enemy on its diagonal and deals +2 to undead.',
      apply(u) { set(u, 'at', { pierce: true }); addPassive(u, 'holyBane', { amt: 2 }); } },
    devout: { unit: 'cleric', name: 'Devout', cost: 1, desc: 'Mend heals 3 more.', apply(u) { tweak(u, 'mend', { heal: ability(u, 'mend').p.heal + 3 }); } },
    // Apprentice
    spark: { unit: 'apprentice', name: 'Spark', cost: 1, desc: 'Arcane Bolt arcs to an adjacent enemy for 3.', apply(u) { tweak(u, 'arcaneBolt', { chain: 3 }); } },
    blinkStep: { unit: 'apprentice', name: 'Blink Step', cost: 1, desc: 'Moves by teleporting up to 3 squares.', apply(u) { u.mv = { type: 'blink', n: 3 }; } },
    focus: { unit: 'apprentice', name: 'Focus', cost: 2, desc: '+1 ATK; Arcane Bolt recharges in 2 turns.', apply(u) { u.atk += 1; tweak(u, 'arcaneBolt', { cd: 2 }); } },
    // Golem
    spiked: { unit: 'golem', name: 'Spiked Plating', cost: 1, desc: 'Melee attackers take 2 damage.', apply(u) { addPassive(u, 'thorns', { d: 2 }); } },
    fortress: { unit: 'golem', name: 'Fortress', cost: 2, desc: '+8 HP.', apply(u) { u.maxHp += 8; } },
    overclocked: { unit: 'golem', name: 'Overclocked', cost: 1, desc: '+3 SPD.', apply(u) { u.spd += 3; } },
    // Pyromancer
    inferno: { unit: 'pyromancer', name: 'Inferno', cost: 2, desc: 'Fireball deals 6, with 3 to everything around it.', apply(u) { tweak(u, 'fireball', { dmg: 6, splash: 3 }); } },
    wildfire: { unit: 'pyromancer', name: 'Wildfire', cost: 1, desc: 'Burning enemies explode when they die, spreading the flames.', apply(u) { addPassive(u, 'wildfire', {}); } },
    emberWard: { unit: 'pyromancer', name: 'Ember Ward', cost: 1, desc: '+3 HP; melee attackers catch fire.', apply(u) { u.maxHp += 3; addPassive(u, 'emberWard', {}); } },
    // Frost Witch
    deepFreeze: { unit: 'frostWitch', name: 'Deep Freeze', cost: 2, desc: 'Flash Freeze lasts 2 turns (recharges in 5).', apply(u) { tweak(u, 'flashFreeze', { t: 2, cd: 5 }); } },
    iceArmor: { unit: 'frostWitch', name: 'Ice Armor', cost: 1, desc: 'Gains 2 shield each round, up to 6.', apply(u) { addPassive(u, 'iceArmor', { amt: 2, max: 6 }); } },
    blizzard: { unit: 'frostWitch', name: 'Blizzard', cost: 2, desc: 'Flash Freeze reaches 4 and Chills everything next to the target.', apply(u) { tweak(u, 'flashFreeze', { area: true, range: 4 }); } },
    // Storm Caller
    conductor: { unit: 'stormCaller', name: 'Conductor', cost: 1, desc: 'Lightning chains to 2 more enemies and loses no power.',
      apply(u) { set(u, 'at', { chain: Object.assign({}, u.at.chain, { n: u.at.chain.n + 2, falloff: 0 }) }); } },
    staticShock: { unit: 'stormCaller', name: 'Static Shock', cost: 1, desc: 'Chained enemies are also Chilled.',
      apply(u) { set(u, 'at', { chain: Object.assign({}, u.at.chain, { chill: 2 }) }); } },
    tempest: { unit: 'stormCaller', name: 'Tempest', cost: 2, desc: 'Thunderclap reaches 2 squares and recharges in 2.', apply(u) { tweak(u, 'thunderclap', { r: 2, cd: 2 }); } },
    // Berserker
    whirlwind: { unit: 'berserker', name: 'Whirlwind', cost: 2, desc: 'Attacks hit every adjacent enemy at full damage.', apply(u) { set(u, 'at', { whirl: true, cleave: 0, vfx: 'whirl' }); } },
    undying: { unit: 'berserker', name: 'Undying Rage', cost: 2, desc: 'The first lethal blow leaves it at 1 HP.', apply(u) { addPassive(u, 'undying', {}); } },
    bloodthirst: { unit: 'berserker', name: 'Bloodthirst', cost: 1, desc: 'Heals 4 on each kill.', apply(u) { addPassive(u, 'bloodthirst', { amt: 4 }); } },
    // Ranger
    piercing: { unit: 'ranger', name: 'Piercing Arrows', cost: 2, desc: 'Arrows pass through allies and hit every enemy in the line.', apply(u) { set(u, 'at', { pierce: true }); } },
    eagleEye: { unit: 'ranger', name: 'Eagle Eye', cost: 1, desc: 'Shoots any enemy in sight within 5, not just along lines.', apply(u) { u.at = { pattern: 'ranged', range: 5, vfx: 'arrow' }; } },
    marksman: { unit: 'ranger', name: 'Marksman', cost: 1, desc: '+1 ATK; Longshot deals +2.', apply(u) { u.atk += 1; addPassive(u, 'longshot', { amt: 2, dist: 4 }); } },
    // Imp
    fireborn: { unit: 'imp', name: 'Fireborn', cost: 1, desc: 'Explodes for 4 and sets neighbours alight.', apply(u) { addPassive(u, 'volatile', { d: 4, burn: true }); } },
    toughHide: { unit: 'imp', name: 'Tough Hide', cost: 1, desc: '+3 HP.', apply(u) { u.maxHp += 3; } },
    pest: { unit: 'imp', name: 'Pest', cost: 1, desc: 'Its bites Mark the target.', apply(u) { fx(u, { mark: 1 }); } },
    // Monk
    ironFist: { unit: 'monk', name: 'Iron Fist', cost: 1, desc: 'Strikes knock the target back.', apply(u) { fx(u, { knock: 1 }); } },
    zen: { unit: 'monk', name: 'Zen', cost: 2, desc: 'Dodges the first hit each round.', apply(u) { addPassive(u, 'zen', {}); } },
    pressurePoints: { unit: 'monk', name: 'Pressure Points', cost: 1, desc: 'Strikes Chill the target.', apply(u) { fx(u, { chill: 1 }); } },
    // Paladin
    consecration: { unit: 'paladin', name: 'Consecration', cost: 1, desc: 'Burns adjacent enemies with holy light at the end of each round.', apply(u) { addPassive(u, 'consecration', {}); } },
    zealot: { unit: 'paladin', name: 'Zealot', cost: 2, desc: '+2 ATK.', apply(u) { u.atk += 2; } },
    martyr: { unit: 'paladin', name: 'Purifier', cost: 1, desc: 'Divine Shield also removes afflictions and gives 2 more shield.',
      apply(u) { tweak(u, 'divineShield', { cleanse: true, amt: 8 }); } },
    // Necromancer
    legion: { unit: 'necromancer', name: 'Legion', cost: 2, desc: 'Raised Skeletons get +3 HP and +1 ATK.',
      apply(u) { u.pas = Object.assign({}, u.pas); u.pas.raiseDead = Object.assign({}, u.pas.raiseDead, { legion: true }); } },
    lichdom: { unit: 'necromancer', name: 'Lichdom', cost: 2, desc: 'The first time it would die, it returns with 5 HP.', apply(u) { addPassive(u, 'lichdom', {}); } },
    plague: { unit: 'necromancer', name: 'Plague', cost: 1, desc: 'Its drain bolts also Poison.', apply(u) { fx(u, { poison: { d: 1, t: 3 } }); } },
    // Vampire
    nightStalker: { unit: 'vampire', name: 'Night Stalker', cost: 1, desc: '+2 damage to targets below half health.', apply(u) { addPassive(u, 'nightStalker', {}); } },
    crimsonFeast: { unit: 'vampire', name: 'Crimson Feast', cost: 1, desc: 'Lifesteal beyond full health becomes shield (up to 6).', apply(u) { addPassive(u, 'crimsonFeast', { max: 6 }); } },
    batForm: { unit: 'vampire', name: 'Bat Form', cost: 1, desc: '+2 SPD and moves 4.', apply(u) { u.spd += 2; u.mv = { type: 'walk', n: 4 }; } },
    // Shade
    venom: { unit: 'shade', name: 'Venom', cost: 1, desc: 'Strikes Poison for 2 a turn.', apply(u) { fx(u, { poison: { d: 2, t: 2 } }); } },
    vanish: { unit: 'shade', name: 'Vanish', cost: 2, desc: 'Returns to stealth after each kill.', apply(u) { addPassive(u, 'vanish', {}); } },
    twinBlades: { unit: 'shade', name: 'Twin Blades', cost: 2, desc: 'Strikes twice (Ambush applies to the first).', apply(u) { set(u, 'at', { hits: 2 }); } },
    // Illusionist
    mindTwist: { unit: 'illusionist', name: 'Mind Twist', cost: 2, desc: 'Enemies it swaps with are Stunned.', apply(u) { tweak(u, 'switcheroo', { stun: true }); } },
    displacer: { unit: 'illusionist', name: 'Displacer', cost: 1, desc: 'Switcheroo reaches 6 and recharges in 2.', apply(u) { tweak(u, 'switcheroo', { range: 6, cd: 2 }); } },
    confound: { unit: 'illusionist', name: 'Confound', cost: 1, desc: 'Its attacks Mark the target.', apply(u) { fx(u, { mark: 1 }); } },
    // Warlock
    agony: { unit: 'warlock', name: 'Agony', cost: 1, desc: 'Hexed enemies also take 2 damage each turn.', apply(u) { tweak(u, 'hex', { dot: 2 }); } },
    impPact: { unit: 'warlock', name: 'Imp Pact', cost: 2, desc: 'Starts the battle with an Imp at its side.', apply(u) { addPassive(u, 'impPact', {}); } },
    doom: { unit: 'warlock', name: 'Doom', cost: 2, desc: 'Hex reaches 6 and adds +3 damage instead of +2.', apply(u) { tweak(u, 'hex', { range: 6, a: 3 }); } },
    // Druid
    alpha: { unit: 'druid', name: 'Alpha Call', cost: 2, desc: 'Its wolves get +3 HP and +1 ATK.', apply(u) { tweak(u, 'summonWolf', { hp: 3, atk: 1 }); } },
    bearForm: { unit: 'druid', name: 'Bear Form', cost: 2, desc: '+8 HP, +2 ATK and 1 armor, but it fights in melee.',
      apply(u) { u.maxHp += 8; u.atk += 2; u.armor += 1; u.at = { pattern: 'melee', vfx: 'claw' }; u.icon = '🐻'; u.art = 'druidBear'; u.role = 'melee'; } },
    overgrowth: { unit: 'druid', name: 'Overgrowth', cost: 1, desc: 'Entangle deals 2 and recharges in 3.', apply(u) { tweak(u, 'entangle', { dmg: 2, cd: 3 }); } },
    // Cannoneer
    grapeshot: { unit: 'cannoneer', name: 'Grapeshot', cost: 1, desc: 'Splash damage rises to 3.', apply(u) { set(u, 'at', { splash: 3 }); } },
    heavyShells: { unit: 'cannoneer', name: 'Heavy Shells', cost: 2, desc: '+1 ATK; the target is knocked back.', apply(u) { u.atk += 1; fx(u, { knock: 1 }); } },
    carriage: { unit: 'cannoneer', name: 'Gun Carriage', cost: 1, desc: 'Moves 2 and has +3 HP.', apply(u) { u.mv = { type: 'walk', n: 2 }; u.maxHp += 3; } },
    // Bannerman
    standard: { unit: 'bannerman', name: 'Standard of Valor', cost: 2, desc: 'Rally reaches 3 squares and grants +2 damage.',
      apply(u) { u.pas = Object.assign({}, u.pas, { rally: { r: 3, amt: 2 } }); } },
    drummer: { unit: 'bannerman', name: 'War Drummer', cost: 1, desc: 'War Cry grants +3 SPD and recharges in 3.', apply(u) { tweak(u, 'warCry', { spd: 3, cd: 3 }); } },
    presence: { unit: 'bannerman', name: 'Rallying Presence', cost: 1, desc: '+4 HP; allies within 2 heal 1 at the end of each round.',
      apply(u) { u.maxHp += 4; addPassive(u, 'rallyingPresence', {}); } },
    // Chronomancer
    accelerate: { unit: 'chronomancer', name: 'Accelerate', cost: 2, desc: 'Hasted allies also gain +2 SPD for the battle.', apply(u) { tweak(u, 'haste', { spd: 2 }); } },
    stasis: { unit: 'chronomancer', name: 'Stasis', cost: 2, desc: 'Its bolts Freeze enemies that are already Chilled.', apply(u) { fx(u, { freezeChilled: true }); } },
    paradox: { unit: 'chronomancer', name: 'Paradox', cost: 1, desc: 'Haste recharges in 2.', apply(u) { tweak(u, 'haste', { cd: 2 }); } },
    // Archmage
    archonForm: { unit: 'archmage', name: 'Archon Form', cost: 2, desc: '+6 HP and 1 armor.', apply(u) { u.maxHp += 6; u.armor += 1; } },
    spellweaver: { unit: 'archmage', name: 'Spellweaver', cost: 2, desc: 'Ability cooldowns are 1 shorter.', apply(u) { addPassive(u, 'spellweaver', {}); } },
    manaBurn: { unit: 'archmage', name: 'Mana Burn', cost: 1, desc: 'Attacks also deal 2 to enemies next to the target.', apply(u) { set(u, 'at', { blast: 2 }); addPassive(u, 'manaBurn', {}); } },
    // Phoenix
    sunfire: { unit: 'phoenix', name: 'Sunfire', cost: 2, desc: '+2 ATK.', apply(u) { u.atk += 2; } },
    quickHatch: { unit: 'phoenix', name: 'Quick Hatch', cost: 1, desc: 'Its egg hatches after 1 round.',
      apply(u) { u.pas = Object.assign({}, u.pas, { rebirth: { hatch: 1 } }); } },
    radiantWings: { unit: 'phoenix', name: 'Radiant Wings', cost: 1, desc: 'Adjacent allies heal 1 at the end of each round.', apply(u) { addPassive(u, 'blessed', { amt: 1 }); } },
  };

  AG.talentsFor = function (defId) {
    const d = AG.Units[defId];
    return (d && d.talents) || [];
  };

  AG.Runes = {
    vigor: { name: 'Rune of Vigor', icon: '♥', cost: 1, rarity: 'common', desc: '+4 HP.', apply(u) { u.maxHp += 4; } },
    swiftness: { name: 'Rune of Swiftness', icon: '»', cost: 1, rarity: 'common', desc: '+2 SPD.', apply(u) { u.spd += 2; } },
    warding: { name: 'Rune of Warding', icon: '◇', cost: 1, rarity: 'common', desc: 'Starts the battle with 5 shield.', apply(u) { u.shield += 5; } },
    thorns: { name: 'Rune of Thorns', icon: '✶', cost: 1, rarity: 'common', desc: 'Melee attackers take 2 damage.',
      apply(u) { const t = u.pas.thorns; addPassive(u, 'thorns', { d: (t ? t.d : 0) + 2 }); } },
    fury: { name: 'Rune of Fury', icon: '⚔', cost: 1, rarity: 'common', desc: '+2 damage while below half health.', apply(u) { addPassive(u, 'fury', { amt: 2 }); } },
    might: { name: 'Rune of Might', icon: '▲', cost: 2, rarity: 'uncommon', desc: '+1 ATK.', apply(u) { u.atk += 1; } },
    iron: { name: 'Rune of Iron', icon: '■', cost: 2, rarity: 'uncommon', desc: '+1 armor.', apply(u) { u.armor += 1; } },
    leech: { name: 'Rune of the Leech', icon: '♆', cost: 2, rarity: 'uncommon', desc: 'Attacks heal it for half the damage dealt.',
      apply(u) { if (u.at) set(u, 'at', { lifesteal: Math.max(u.at.lifesteal || 0, 0.5) }); } },
    embers: { name: 'Rune of Embers', icon: '♨', cost: 2, rarity: 'uncommon', desc: 'Attacks set the target alight.', apply(u) { if (u.at) fx(u, { burn: { d: 1, t: 2 } }); } },
    rime: { name: 'Rune of Rime', icon: '❅', cost: 2, rarity: 'uncommon', desc: 'Attacks Chill the target.', apply(u) { if (u.at) fx(u, { chill: 1 }); } },
    reach: { name: 'Rune of Reach', icon: '↗', cost: 2, rarity: 'uncommon', desc: 'Ranged attacks reach 1 further; melee attacks reach 2 squares in straight lines.',
      apply(u) {
        if (!u.at) return;
        if (u.at.pattern === 'melee' || u.at.pattern === 'melee4') u.at = Object.assign({}, u.at, { pattern: 'reach', range: 2, dirs: u.at.pattern === 'melee4' ? 'orth' : 'all' });
        else if (u.at.range) set(u, 'at', { range: u.at.range + 1 });
      } },
    blink: { name: 'Rune of Blinking', icon: '◌', cost: 2, rarity: 'uncommon', desc: 'May teleport up to 2 squares instead of moving normally.', apply(u) { u.mv2 = { type: 'blink', n: 2 }; } },
    precision: { name: 'Rune of Precision', icon: '✛', cost: 1, rarity: 'uncommon', desc: 'Attacks ignore armor.', apply(u) { if (u.at) set(u, 'at', { ignoreArmor: true }); } },
    phoenixFeather: { name: 'Phoenix Feather', icon: '❦', cost: 3, rarity: 'rare', desc: 'The first time it would die, it rises with half its health.', apply(u) { addPassive(u, 'secondWind', {}); } },
    tempo: { name: 'Rune of Tempo', icon: '⧖', cost: 3, rarity: 'rare', desc: 'Takes an extra turn at the start of the first round.', apply(u) { addPassive(u, 'tempoRune', {}); } },
  };

  // Would this rune change the unit at all (some already have the effect)?
  AG.runeHasEffect = function (defId, runeId, talents) {
    const snap = (u) => JSON.stringify([u.maxHp, u.atk, u.spd, u.armor, u.shield, u.mv, u.mv2, u.at, u.abil, u.pas]);
    const base = AG.B.makeUnit(defId, 0, 0, 0, { talents: talents || [] });
    const withRune = AG.B.makeUnit(defId, 0, 0, 0, { talents: talents || [], rune: runeId });
    return snap(base) !== snap(withRune);
  };

  // Training at camps: Veteran (rank 1) and Elite (rank 2, second talent slot).
  AG.RANKS = ['Recruit', 'Veteran', 'Elite'];
  AG.applyRank = function (u, rank) {
    const d = AG.Units[u.def];
    const bump = Math.max(2, Math.round(d.hp * 0.2));
    if (rank >= 1) { u.maxHp += bump; u.atk += 1; }
    if (rank >= 2) { u.maxHp += bump; u.spd += 1; }
  };
  AG.rankDesc = function (rank, defId) {
    const d = AG.Units[defId];
    const bump = Math.max(2, Math.round(d.hp * 0.2));
    if (rank === 1) return '+' + bump + ' HP, +1 ATK';
    if (rank === 2) return '+' + bump + ' HP, +1 SPD, and a second talent slot';
    return '';
  };

  // Passives granted by upgrades that the base roster does not use.
  Object.assign(AG.Passives, {
    fury: {
      name: 'Fury', desc: (p) => '+' + p.amt + ' damage while below half health.',
      outBonus(s, u, p) { return u.hp * 2 < u.maxHp ? p.amt : 0; },
    },
    secondWind: {
      name: 'Phoenix Feather', desc: () => 'The first time it would die, it rises with half its health.',
      preventDeath(s, u) {
        if (u.fl.secondWind) return false;
        u.fl.secondWind = true;
        u.hp = Math.max(1, Math.round(u.maxHp / 2));
        AG.B.emit(s, 'revive', { uid: u.uid, hp: u.hp, label: 'Phoenix Feather' });
        return true;
      },
    },
    tempoRune: {
      name: 'Tempo', desc: () => 'Takes an extra turn at the start of the first round.',
      roundStart(s, u) {
        if (s.round === 1 && !u.fl.tempo) { u.fl.tempo = true; s.extra.push(u.uid); }
      },
    },
    impPact: {
      name: 'Imp Pact', desc: () => 'Starts the battle with an Imp at its side.',
      battleStart(s, u) {
        const cells = AG.emptyAround(s, u.x, u.y, false);
        cells.sort((a, b) => ((a / s.board.w) | 0) - ((b / s.board.w) | 0));
        if (cells.length) AG.B.summon(s, 'imp_summon', u.side, cells[0], { owner: u.uid });
      },
    },
  });
})(globalThis.AG = globalThis.AG || {});
