/* Unit roster. pool: player | summon | enemy. Player units carry a supply
   cost, rarity and three talents. Movement: walk n (pathing, passes allies),
   slide n (chess-style straight lines), leap (knight jumps), blink n
   (teleport), shadow n (teleport next to an enemy), none.
   Attack patterns: melee, melee4, ranged (range, los), line (first unit along
   ranks/files/diagonals), reach (pike, 2 squares in lines, past allies),
   lob (no line of sight, min range), offsets. */
(function (AG) {
  'use strict';
  const T = '︎'; // force text presentation for chess glyphs

  const walk = (n, extra) => Object.assign({ type: 'walk', n }, extra);
  const slide = (n, dirs) => ({ type: 'slide', n, dirs });
  const melee = (extra) => Object.assign({ pattern: 'melee', vfx: 'slash' }, extra);
  const ranged = (range, extra) => Object.assign({ pattern: 'ranged', range, vfx: 'bolt' }, extra);
  const line = (range, dirs, extra) => Object.assign({ pattern: 'line', range, dirs, vfx: 'arrow' }, extra);

  AG.Units = {
    // ================================================================ PLAYER
    squire: {
      name: 'Squire', icon: '♟' + T, pool: 'player', rarity: 'starter', cost: 1, role: 'melee', tags: ['steel'],
      hp: 7, atk: 2, spd: 3,
      move: walk(1), attack: melee(),
      passives: {
        shieldWall: {},
        promotion: { name: 'Champion', icon: '⚔️', hp: 6, atk: 2, move: walk(2) },
      },
      talents: ['pikeman', 'stout', 'eager'],
      blurb: 'Cheap, stubborn, and secretly dreaming of the far rank.',
    },
    knight: {
      name: 'Knight', icon: '♞' + T, pool: 'player', rarity: 'starter', cost: 3, role: 'melee', tags: ['steel'],
      hp: 11, atk: 4, spd: 2, armor: 1,
      move: { type: 'leap' }, attack: melee(),
      passives: { charge: { bonus: 2 } },
      talents: ['destrier', 'lancer', 'barding'],
      blurb: 'Vaults over the line in an L and lands hooves-first.',
    },
    scout: {
      name: 'Scout', icon: '🎯', pool: 'player', rarity: 'starter', cost: 2, role: 'ranged', tags: ['wild'],
      hp: 6, atk: 3, spd: 8,
      move: slide(3, 'all'), attack: ranged(2, { vfx: 'dart', fx: { mark: 1 } }),
      passives: { spotter: {}, hitAndRun: { n: 2 } },
      talents: ['hawkeye', 'poisonDarts', 'openingShot'],
      blurb: 'First to move, first to strike, gone before the reply.',
    },
    cleric: {
      name: 'Cleric', icon: '♝' + T, pool: 'player', rarity: 'starter', cost: 3, role: 'support', tags: ['holy'],
      hp: 8, atk: 2, spd: 4,
      move: slide(3, 'diag'), attack: line(4, 'diag', { vfx: 'smite', tag: 'holy' }),
      abilities: ['mend'],
      passives: { blessed: { amt: 1 } },
      talents: ['sanctuary', 'radiance', 'devout'],
      blurb: 'Moves on the diagonals, as bishops do, mending what breaks.',
    },
    apprentice: {
      name: 'Apprentice', icon: '🔮', pool: 'player', rarity: 'starter', cost: 2, role: 'ranged', tags: ['arcane'],
      hp: 5, atk: 3, spd: 5,
      move: walk(2), attack: ranged(3, { vfx: 'arcane', tag: 'arcane' }),
      abilities: ['arcaneBolt'],
      talents: ['spark', 'blinkStep', 'focus'],
      blurb: 'Fragile, eager, and in possession of one very good spell.',
    },
    golem: {
      name: 'Bastion Golem', icon: '♜' + T, pool: 'player', rarity: 'common', cost: 4, role: 'tank', tags: ['construct'],
      hp: 18, atk: 3, spd: 1, armor: 2,
      move: slide(2, 'orth'), attack: { pattern: 'melee4', vfx: 'smash' },
      abilities: ['taunt'],
      passives: { unmovable: {}, construct: {} }, immune: ['burn', 'poison'],
      talents: ['spiked', 'fortress', 'overclocked'],
      blurb: 'A walking rook. Slow to start, impossible to move.',
    },
    pyromancer: {
      name: 'Pyromancer', icon: '🔥', pool: 'player', rarity: 'common', cost: 4, role: 'ranged', tags: ['fire'],
      hp: 7, atk: 3, spd: 5,
      move: walk(2), attack: ranged(3, { vfx: 'fire', tag: 'fire', fx: { burn: { d: 1, t: 2 } } }),
      abilities: ['fireball'],
      passives: { kindling: { amt: 1 } },
      talents: ['inferno', 'wildfire', 'emberWard'],
      blurb: 'Everything is flammable if you believe in it hard enough.',
    },
    frostWitch: {
      name: 'Frost Witch', icon: '❄️', pool: 'player', rarity: 'common', cost: 4, role: 'ranged', tags: ['frost'],
      hp: 7, atk: 2, spd: 6,
      move: walk(2), attack: ranged(3, { vfx: 'frost', tag: 'frost', fx: { chill: 2 } }),
      abilities: ['flashFreeze'],
      talents: ['deepFreeze', 'iceArmor', 'blizzard'],
      blurb: 'Slows the fast, stops the dangerous, and lets the Knight do the rest.',
    },
    stormCaller: {
      name: 'Storm Caller', icon: '⚡', pool: 'player', rarity: 'common', cost: 4, role: 'ranged', tags: ['storm'],
      hp: 7, atk: 3, spd: 5,
      move: walk(2), attack: ranged(3, { vfx: 'lightning', tag: 'storm', chain: { n: 2, falloff: 1, r: 1 } }),
      abilities: ['thunderclap'],
      talents: ['conductor', 'staticShock', 'tempest'],
      blurb: 'Lightning that jumps between enemies standing too close together.',
    },
    berserker: {
      name: 'Berserker', icon: '🪓', pool: 'player', rarity: 'common', cost: 3, role: 'melee', tags: ['wild'],
      hp: 12, atk: 3, spd: 4,
      move: walk(2), attack: melee({ cleave: 2, vfx: 'cleave' }),
      passives: { rage: { max: 4 } },
      talents: ['whirlwind', 'undying', 'bloodthirst'],
      blurb: 'Every wound makes the axe heavier.',
    },
    ranger: {
      name: 'Ranger', icon: '🏹', pool: 'player', rarity: 'common', cost: 3, role: 'ranged', tags: ['wild'],
      hp: 6, atk: 3, spd: 5,
      move: walk(2), attack: line(6, 'all'),
      abilities: ['pinningShot'],
      passives: { longshot: { amt: 1, dist: 4 } },
      talents: ['piercing', 'eagleEye', 'marksman'],
      blurb: 'Shoots down ranks, files and diagonals. Needs a clear lane.',
    },
    imp: {
      name: 'Imp', icon: '👿', pool: 'player', rarity: 'common', cost: 1, role: 'melee', tags: ['fire'],
      hp: 3, atk: 2, spd: 7, flying: true,
      move: walk(3), attack: melee({ vfx: 'claw' }),
      passives: { volatile: { d: 2 } },
      talents: ['fireborn', 'toughHide', 'pest'],
      blurb: 'Flies over everything, bites, explodes. Cheap at twice the price.',
    },
    monk: {
      name: 'Monk', icon: '👊', pool: 'player', rarity: 'common', cost: 3, role: 'melee', tags: ['holy'],
      hp: 9, atk: 2, spd: 6,
      move: walk(3), attack: { pattern: 'melee', hits: 2, vfx: 'fist' },
      passives: { counter: { d: 2 } },
      talents: ['ironFist', 'zen', 'pressurePoints'],
      blurb: 'Two quick strikes, and a third for anyone who swings back.',
    },
    paladin: {
      name: 'Paladin', icon: '🛡️', pool: 'player', rarity: 'uncommon', cost: 5, role: 'tank', tags: ['holy', 'steel'],
      hp: 14, atk: 3, spd: 3, armor: 1,
      move: walk(2), attack: melee({ tag: 'holy' }),
      abilities: ['divineShield'],
      passives: { guardian: { amt: 1 } },
      talents: ['consecration', 'zealot', 'martyr'],
      blurb: 'Stand next to the Paladin. Everything hurts less there.',
    },
    necromancer: {
      name: 'Necromancer', icon: '☠️', pool: 'player', rarity: 'uncommon', cost: 5, role: 'support', tags: ['shadow'],
      hp: 8, atk: 2, spd: 3,
      move: walk(2), attack: ranged(3, { vfx: 'shadow', tag: 'shadow', lifesteal: 1 }),
      abilities: ['corpseExplosion'],
      passives: { raiseDead: { r: 3, max: 3 } },
      talents: ['legion', 'lichdom', 'plague'],
      blurb: 'Every corpse on the board is a recruit waiting to be asked.',
    },
    vampire: {
      name: 'Vampire', icon: '🦇', pool: 'player', rarity: 'uncommon', cost: 4, role: 'melee', tags: ['shadow'],
      hp: 10, atk: 3, spd: 6, flying: true,
      move: walk(3), attack: melee({ vfx: 'bite', lifesteal: 1 }),
      passives: { bloodlust: {} },
      talents: ['nightStalker', 'crimsonFeast', 'batForm'],
      blurb: 'Drinks what it deals and grows stronger with every kill.',
    },
    shade: {
      name: 'Shade', icon: '🗡️', pool: 'player', rarity: 'uncommon', cost: 4, role: 'assassin', tags: ['shadow'],
      hp: 6, atk: 4, spd: 7,
      move: { type: 'shadow', n: 4 }, attack: melee({ vfx: 'stab' }),
      passives: { ambush: { bonus: 3 }, evasive: {} },
      talents: ['venom', 'vanish', 'twinBlades'],
      blurb: 'Steps out of the dark beside whoever has not moved yet.',
    },
    illusionist: {
      name: 'Illusionist', icon: '🎭', pool: 'player', rarity: 'uncommon', cost: 3, role: 'support', tags: ['arcane'],
      hp: 6, atk: 2, spd: 6,
      move: { type: 'blink', n: 3 }, attack: ranged(3, { vfx: 'psychic', ignoreArmor: true }),
      abilities: ['switcheroo'],
      passives: { mirrorImage: {} },
      talents: ['mindTwist', 'displacer', 'confound'],
      blurb: 'Trades places with anyone. Friend or foe, it does not ask.',
    },
    warlock: {
      name: 'Warlock', icon: '😈', pool: 'player', rarity: 'uncommon', cost: 4, role: 'ranged', tags: ['shadow'],
      hp: 8, atk: 3, spd: 4,
      move: walk(2), attack: ranged(3, { vfx: 'shadow', tag: 'shadow' }),
      abilities: ['hex'],
      passives: { soulSiphon: { max: 3 } },
      talents: ['agony', 'impPact', 'doom'],
      blurb: 'Curses the biggest threat so everyone else can finish it.',
    },
    druid: {
      name: 'Druid', icon: '🌿', pool: 'player', rarity: 'uncommon', cost: 4, role: 'support', tags: ['wild'],
      hp: 9, atk: 2, spd: 4,
      move: walk(2), attack: ranged(2, { vfx: 'thorn', tag: 'nature' }),
      abilities: ['summonWolf', 'entangle'],
      passives: { regrowth: { amt: 1 } },
      talents: ['alpha', 'bearForm', 'overgrowth'],
      blurb: 'Calls wolves out of the treeline and roots enemies in place.',
    },
    cannoneer: {
      name: 'Cannoneer', icon: '💣', pool: 'player', rarity: 'uncommon', cost: 4, role: 'ranged', tags: ['steel'],
      hp: 8, atk: 5, spd: 2,
      move: walk(1), attack: { pattern: 'lob', range: 5, minRange: 2, splash: 2, vfx: 'shell' },
      talents: ['grapeshot', 'heavyShells', 'carriage'],
      blurb: 'Lobs shells over walls. Do not stand next to what it is aiming at.',
    },
    bannerman: {
      name: 'Bannerman', icon: '🚩', pool: 'player', rarity: 'uncommon', cost: 3, role: 'support', tags: ['steel'],
      hp: 9, atk: 2, spd: 3,
      move: walk(2), attack: melee(),
      abilities: ['warCry'],
      passives: { rally: { r: 2, amt: 1 } },
      talents: ['standard', 'drummer', 'presence'],
      blurb: 'Allies nearby hit harder; a War Cry jumps them up the turn order.',
    },
    chronomancer: {
      name: 'Chronomancer', icon: '⏳', pool: 'player', rarity: 'rare', cost: 5, role: 'support', tags: ['arcane'],
      hp: 7, atk: 2, spd: 7,
      move: { type: 'blink', n: 2 }, attack: ranged(3, { vfx: 'time', fx: { chill: 1 } }),
      abilities: ['haste'],
      passives: { timeless: {} },
      talents: ['accelerate', 'stasis', 'paradox'],
      blurb: 'Gives its strongest ally a second turn, right now.',
    },
    archmage: {
      name: 'Archmage', icon: '♛' + T, pool: 'player', rarity: 'rare', cost: 7, role: 'ranged', tags: ['arcane'],
      hp: 10, atk: 4, spd: 5,
      move: slide(3, 'all'), attack: ranged(4, { vfx: 'arcane', tag: 'arcane' }),
      abilities: ['meteor', 'arcaneBarrier'],
      talents: ['archonForm', 'spellweaver', 'manaBurn'],
      blurb: 'The queen of the board. Moves like one, too.',
    },
    phoenix: {
      name: 'Phoenix', icon: '🦅', pool: 'player', rarity: 'rare', cost: 6, role: 'melee', tags: ['fire'],
      hp: 9, atk: 3, spd: 6, flying: true,
      move: walk(3), attack: melee({ vfx: 'fire', tag: 'fire', fx: { burn: { d: 2, t: 2 } } }),
      passives: { rebirth: { hatch: 2 } }, immune: ['burn'],
      talents: ['sunfire', 'quickHatch', 'radiantWings'],
      blurb: 'Dies gloriously, then does it again.',
    },

    // =============================================================== SUMMONS
    skeleton: {
      name: 'Skeleton', icon: '💀', pool: 'summon', hp: 6, atk: 3, spd: 4, tags: ['undead'],
      move: walk(2), attack: melee(), passives: { reassemble: {} }, threat: 2,
      blurb: 'Rattles forward. Put it down with fire or holy light or it gets back up.',
    },
    spiritWolf: {
      name: 'Spirit Wolf', icon: '🐺', pool: 'summon', hp: 6, atk: 3, spd: 6, tags: ['beast', 'wolf'],
      move: walk(3), attack: melee({ vfx: 'bite' }), passives: { packTactics: {} },
      blurb: 'Hunts in packs: +1 damage for each wolf beside it.',
    },
    emberEgg: {
      name: 'Ember Egg', icon: '🥚', pool: 'summon', hp: 5, atk: 0, spd: 0, noTurn: true, object: true,
      tags: ['fire'], passives: { hatch: {} }, immune: ['all'], value: 7,
      blurb: 'Warm to the touch. Do not let it hatch, or do, depending on whose it is.',
    },
    bonePile: {
      name: 'Bone Pile', icon: '🦴', pool: 'summon', hp: 3, atk: 0, spd: 0, noTurn: true, object: true,
      tags: ['undead'], passives: { reform: {} }, immune: ['all'], value: 3,
      blurb: 'A skeleton taking a short break.',
    },
    imp_summon: {
      name: 'Imp', icon: '👿', pool: 'summon', hp: 3, atk: 2, spd: 7, flying: true, tags: ['fire'],
      move: walk(3), attack: melee({ vfx: 'claw' }), passives: { volatile: { d: 2 } },
      blurb: 'A gift from the Warlock’s patron.',
    },

    // ============================================================ ACT I FOES
    goblin: {
      name: 'Goblin', icon: '👺', pool: 'enemy', hp: 5, atk: 2, spd: 5, tags: ['goblin'],
      move: walk(2), attack: melee({ vfx: 'stab' }), threat: 2,
      blurb: 'Quick, mean, and much braver in a crowd.',
    },
    goblinSlinger: {
      name: 'Goblin Slinger', icon: '🪨', pool: 'enemy', hp: 4, atk: 2, spd: 4, tags: ['goblin'], role: 'ranged',
      move: walk(2), attack: ranged(3, { vfx: 'rock' }), threat: 2,
      blurb: 'Throws rocks from a safe distance and complains about it.',
    },
    goblinShaman: {
      name: 'Goblin Shaman', icon: '🍄', pool: 'enemy', hp: 6, atk: 1, spd: 4, tags: ['goblin'], role: 'support',
      move: walk(2), attack: ranged(2, { vfx: 'nature' }),
      abilities: [{ id: 'mend', p: { heal: 4, range: 3 } }], threat: 3,
      blurb: 'Keeps the warband patched up with mushrooms of dubious origin.',
    },
    wolf: {
      name: 'Wolf', icon: '🐺', pool: 'enemy', hp: 6, atk: 2, spd: 7, tags: ['beast', 'wolf'],
      move: walk(3), attack: melee({ vfx: 'bite' }), passives: { packTactics: {} }, threat: 2,
      blurb: 'Fast. Dangerous in numbers: +1 damage per wolf beside it.',
    },
    slime: {
      name: 'Slime', icon: '🟢', pool: 'enemy', hp: 9, atk: 2, spd: 2, tags: ['ooze'], ai: 'brute',
      move: walk(1), attack: melee({ vfx: 'goo' }), passives: { splitter: { n: 2 }, mindless: {} }, threat: 2,
      blurb: 'Hit it and there are two of them.',
    },
    slimeling: {
      name: 'Slimeling', icon: '🫧', pool: 'enemy', hp: 3, atk: 1, spd: 3, tags: ['ooze'], ai: 'brute',
      move: walk(1), attack: melee({ vfx: 'goo' }), threat: 1,
      blurb: 'Small, wet, persistent.',
    },
    bandit: {
      name: 'Bandit Thug', icon: '🦹', pool: 'enemy', hp: 10, atk: 3, spd: 3, armor: 1, tags: ['human'],
      move: walk(2), attack: melee(), threat: 3,
      blurb: 'Padded leather and a cudgel. Hits like a door.',
    },
    boar: {
      name: 'Thornback Boar', icon: '🐗', pool: 'enemy', hp: 9, atk: 3, spd: 4, tags: ['beast'],
      move: slide(4, 'orth'), attack: melee({ vfx: 'gore' }), passives: { gore: { bonus: 2 } }, threat: 3,
      blurb: 'Charges in straight lines. The longer the run-up, the worse the gore.',
    },
    troll: {
      name: 'Bridge Troll', icon: '🧌', pool: 'enemy', hp: 22, atk: 5, spd: 2, armor: 1, big: true, ai: 'brute',
      move: walk(2), attack: melee({ vfx: 'smash' }), passives: { regen: { amt: 3 } }, threat: 6,
      blurb: 'Regenerates 3 every turn. Fire stops it.',
    },
    goblinChief: {
      name: 'Goblin Warboss', icon: '🤴', pool: 'enemy', hp: 15, atk: 3, spd: 5, armor: 1, tags: ['goblin'],
      move: walk(2), attack: melee(),
      abilities: [{ id: 'callGuards', p: { n: 1, def: 'goblin', max: 3 } }],
      passives: { rally: { r: 2, amt: 1 } }, threat: 5,
      blurb: 'Blows a horn and more goblins appear. Nearby goblins hit harder.',
    },
    alphaWolf: {
      name: 'Alpha Wolf', icon: '🐺', pool: 'enemy', hp: 16, atk: 4, spd: 8, tags: ['beast', 'wolf'], big: true,
      move: walk(3), attack: melee({ vfx: 'bite' }),
      abilities: [{ id: 'warCry', p: { r: 5, spd: 2, heal: 2, tag: 'wolf' } }],
      passives: { packLeader: {}, packTactics: {} }, threat: 5,
      blurb: 'Leads the pack. Its howl speeds every wolf up the turn order.',
    },
    broodMother: {
      name: 'Brood Mother', icon: '🕷️', pool: 'enemy', hp: 16, atk: 3, spd: 3, big: true, tags: ['beast'],
      move: walk(1), attack: melee({ vfx: 'bite', fx: { poison: { d: 1, t: 3 } } }),
      passives: { swarmQueen: {} }, threat: 6,
      blurb: 'Lays a Spiderling every round. Kill her quickly.',
    },
    spiderling: {
      name: 'Spiderling', icon: '🕸️', pool: 'enemy', hp: 3, atk: 1, spd: 6, tags: ['beast'], ai: 'brute',
      move: walk(3), attack: melee({ vfx: 'bite', fx: { poison: { d: 1, t: 2 } } }), threat: 1,
      blurb: 'Venomous and very numerous.',
    },
    goblinKing: {
      name: 'King Grumblewart', icon: '👑', pool: 'enemy', hp: 34, atk: 4, spd: 4, armor: 1, boss: true, big: true,
      tags: ['goblin'],
      move: walk(1), attack: melee({ vfx: 'smash' }),
      abilities: [{ id: 'callGuards', p: { n: 2, def: 'goblin', max: 3, initCd: 1 } }],
      passives: { royalDecree: {} }, threat: 12,
      blurb: 'The goblin king. Every goblin fights harder while he lives, and he always has more guards.',
    },

    // =========================================================== ACT II FOES
    zombie: {
      name: 'Zombie', icon: '🧟', pool: 'enemy', hp: 12, atk: 3, spd: 1, tags: ['undead'], ai: 'brute',
      move: walk(1), attack: melee({ vfx: 'claw' }), passives: { infectious: {}, mindless: {} }, threat: 3,
      blurb: 'Slow. Anything it kills gets up and joins it.',
    },
    ghost: {
      name: 'Ghost', icon: '👻', pool: 'enemy', hp: 7, atk: 3, spd: 6, tags: ['undead'], flying: true,
      move: walk(3), attack: melee({ vfx: 'shadow', tag: 'shadow' }), passives: { incorporeal: {} }, threat: 3,
      blurb: 'Drifts through walls of bodies. Shrugs off basic attacks; spells hit it fully.',
    },
    cultist: {
      name: 'Cultist', icon: '🕯️', pool: 'enemy', hp: 6, atk: 2, spd: 5, tags: ['human'], role: 'ranged',
      move: walk(2), attack: ranged(3, { vfx: 'shadow', tag: 'shadow' }), passives: { darkPact: { amt: 2 } }, threat: 2,
      blurb: 'When one dies, the others nearby grow stronger.',
    },
    boneArcher: {
      name: 'Bone Archer', icon: '🏹', pool: 'enemy', hp: 5, atk: 3, spd: 3, tags: ['undead'], role: 'ranged',
      move: walk(1), attack: line(6, 'all'), passives: { reassemble: {} }, threat: 3,
      blurb: 'Shoots along open lines. Reassembles unless burned or blessed.',
    },
    banshee: {
      name: 'Banshee', icon: '🗣️', pool: 'enemy', hp: 8, atk: 2, spd: 5, tags: ['undead'], flying: true, role: 'ranged',
      move: walk(3), attack: ranged(2, { vfx: 'shadow' }), abilities: ['wail'], threat: 3,
      blurb: 'Her wail chills everything nearby and drags it down the turn order.',
    },
    gravecaller: {
      name: 'Gravecaller', icon: '⚰️', pool: 'enemy', hp: 9, atk: 2, spd: 3, tags: ['human'], role: 'support',
      move: walk(2), attack: ranged(3, { vfx: 'shadow', tag: 'shadow' }),
      abilities: ['soulDrain'], passives: { raiseDead: { r: 3, max: 3 } }, threat: 4,
      blurb: 'Raises the fallen of either side. Kill it before the board fills with bones.',
    },
    deathKnight: {
      name: 'Death Knight', icon: '♞' + T, pool: 'enemy', hp: 22, atk: 5, spd: 3, armor: 2, big: true, tags: ['undead'],
      move: { type: 'leap', step: true }, attack: melee({ vfx: 'smash' }),
      passives: { charge: { bonus: 2 }, soulReap: { amt: 4 } }, threat: 6,
      blurb: 'A knight that leaps like one and heals on every kill.',
    },
    boneColossus: {
      name: 'Bone Colossus', icon: '🗿', pool: 'enemy', hp: 32, atk: 4, spd: 1, armor: 1, big: true, tags: ['undead'], ai: 'brute',
      move: walk(1), attack: melee({ whirl: true, vfx: 'smash' }), passives: { mindless: {} }, threat: 6,
      blurb: 'Every swing hits everything around it.',
    },
    vampireLord: {
      name: 'Vampire Lord', icon: '🧛', pool: 'enemy', hp: 20, atk: 4, spd: 7, flying: true, big: true, tags: ['shadow'],
      move: walk(3), attack: melee({ vfx: 'bite', lifesteal: 1 }),
      abilities: [{ id: 'batSwarm', p: { n: 2, max: 4 } }], passives: { bloodlust: {} }, threat: 7,
      blurb: 'Drinks deeply, summons bats, and grows stronger with each kill.',
    },
    bat: {
      name: 'Bat', icon: '🦇', pool: 'enemy', hp: 3, atk: 2, spd: 8, flying: true, tags: ['beast'], ai: 'brute',
      move: walk(3), attack: melee({ vfx: 'bite', lifesteal: 1 }), threat: 1,
      blurb: 'Flutters over the front line to nibble at whoever is behind it.',
    },
    lich: {
      name: 'Morvane the Lich', icon: '🧙', pool: 'enemy', hp: 32, atk: 4, spd: 5, boss: true, tags: ['undead'], role: 'ranged',
      move: { type: 'blink', n: 2 }, attack: ranged(4, { vfx: 'frost', tag: 'frost' }),
      abilities: ['frostNova', { id: 'soulDrain', p: { dmg: 5, range: 4 } }],
      passives: { phylacteryBound: {}, raiseDead: { r: 4, max: 3 } }, threat: 14, immune: ['frozen'],
      blurb: 'Cannot die while its phylactery stands. Raises the dead around it.',
    },
    phylactery: {
      name: 'Phylactery', icon: '🏺', pool: 'enemy', hp: 16, atk: 0, spd: 0, armor: 1, noTurn: true, object: true,
      immune: ['all'], value: 26, threat: 0,
      blurb: 'The Lich’s soul in a jar. Break it and the Lich can die.',
    },

    // ========================================================== ACT III FOES
    clockPawn: {
      name: 'Clockwork Pawn', icon: '⚙️', pool: 'enemy', hp: 7, atk: 2, spd: 3, armor: 1, tags: ['construct'], ai: 'brute',
      move: walk(1), attack: melee(),
      passives: {
        construct: {},
        promotion: { name: 'Clockwork Queen', icon: '♛' + T, hp: 6, atk: 2, move: slide(3, 'all'), attack: ranged(3, { vfx: 'arcane' }) },
      },
      immune: ['burn', 'poison'], threat: 2,
      blurb: 'If it reaches your back rank it becomes a queen.',
    },
    turret: {
      name: 'Arcane Turret', icon: '🗼', pool: 'enemy', hp: 10, atk: 3, spd: 4, armor: 1, tags: ['construct'], role: 'ranged',
      move: { type: 'none' }, attack: line(7, 'orth', { vfx: 'beam', pierce: true }),
      passives: { stationary: {}, construct: {}, unmovable: {} }, immune: ['burn', 'poison'], threat: 3,
      blurb: 'Never moves. Fires a beam down its rank and file that pierces everything.',
    },
    fireElemental: {
      name: 'Fire Elemental', icon: '☄️', pool: 'enemy', hp: 11, atk: 3, spd: 5, tags: ['fire'],
      move: walk(2), attack: melee({ vfx: 'fire', tag: 'fire', fx: { burn: { d: 1, t: 2 } } }),
      passives: { scorching: {} }, immune: ['burn'], threat: 4,
      blurb: 'Sets everything next to it on fire at the start of each round.',
    },
    frostElemental: {
      name: 'Frost Elemental', icon: '🧊', pool: 'enemy', hp: 11, atk: 3, spd: 4, tags: ['frost'], role: 'ranged',
      move: walk(2), attack: ranged(3, { vfx: 'frost', tag: 'frost', fx: { chill: 2 } }),
      passives: { frostDeath: {} }, immune: ['chill', 'frozen'], threat: 4,
      blurb: 'Its bolts chill. When it shatters, so does your tempo.',
    },
    voidStalker: {
      name: 'Void Stalker', icon: '🌑', pool: 'enemy', hp: 9, atk: 4, spd: 8, tags: ['shadow'], role: 'assassin',
      move: { type: 'shadow', n: 4 }, attack: melee({ vfx: 'stab' }), passives: { ambush: { bonus: 2 } }, threat: 4,
      blurb: 'Steps through the void to whoever is weakest.',
    },
    demonBrute: {
      name: 'Demon Brute', icon: '👹', pool: 'enemy', hp: 17, atk: 4, spd: 3, armor: 1, tags: ['demon'], ai: 'brute',
      move: walk(2), attack: melee({ vfx: 'smash' }), passives: { rage: { max: 4 } }, threat: 5,
      blurb: 'Gets angrier every time you hit it.',
    },
    mirrorKnight: {
      name: 'Mirror Knight', icon: '🪞', pool: 'enemy', hp: 13, atk: 3, spd: 4, armor: 1, tags: ['construct'],
      move: walk(2), attack: melee(), passives: { reflect: { d: 2 } }, threat: 4,
      blurb: 'Ranged attackers that hit it take 2 back.',
    },
    archon: {
      name: 'Archon Engine', icon: '🤖', pool: 'enemy', hp: 28, atk: 4, spd: 3, armor: 2, big: true, tags: ['construct'], role: 'ranged',
      move: walk(1), attack: ranged(3, { vfx: 'beam' }), abilities: ['laser'],
      passives: { construct: {} }, immune: ['burn', 'poison'], threat: 7,
      blurb: 'Every other turn it fires a beam down a whole rank or file.',
    },
    infernalDrake: {
      name: 'Infernal Drake', icon: '🐉', pool: 'enemy', hp: 24, atk: 5, spd: 5, flying: true, big: true, tags: ['fire', 'demon'],
      move: walk(3), attack: melee({ vfx: 'fire', tag: 'fire', fx: { burn: { d: 1, t: 2 } } }),
      abilities: [{ id: 'fireball', p: { dmg: 5, splash: 2, range: 4 } }], immune: ['burn'], threat: 7,
      blurb: 'Flies, breathes fireballs, and is generally having a wonderful time.',
    },
    ghostChampion: {
      name: 'The Old Champion', icon: '♘' + T, pool: 'enemy', hp: 20, atk: 4, spd: 4, armor: 1, big: true, flying: true, tags: ['undead'],
      move: { type: 'leap', step: true }, attack: melee({ vfx: 'lance', tag: 'shadow' }),
      passives: { incorporeal: {}, charge: { bonus: 2 } }, threat: 6,
      blurb: 'A spectral knight that still remembers every opening it ever played.',
    },
    ebonPawn: {
      name: 'Ebon Pawn', icon: '♟' + T, pool: 'enemy', hp: 6, atk: 2, spd: 3, tags: ['chess'],
      move: walk(1), attack: melee(),
      passives: { shieldWall: {}, promotion: { name: 'Ebon Queen', icon: '♛' + T, hp: 8, atk: 2, move: slide(4, 'all'), attack: ranged(3, { vfx: 'arcane' }) } },
      threat: 2,
      blurb: 'If it reaches your back rank, it becomes a queen.',
    },
    ebonKnight: {
      name: 'Ebon Knight', icon: '♞' + T, pool: 'enemy', hp: 12, atk: 4, spd: 4, armor: 1, tags: ['chess'],
      move: { type: 'leap' }, attack: melee(), passives: { charge: { bonus: 2 } }, threat: 4,
      blurb: 'Leaps in an L and charges.',
    },
    ebonBishop: {
      name: 'Ebon Bishop', icon: '♝' + T, pool: 'enemy', hp: 9, atk: 3, spd: 5, tags: ['chess'], role: 'support',
      move: slide(4, 'diag'), attack: line(5, 'diag', { vfx: 'shadow' }),
      abilities: [{ id: 'mend', p: { heal: 4, range: 3, cd: 3 } }], threat: 4,
      blurb: 'A dark priest on the diagonals.',
    },
    ebonRook: {
      name: 'Ebon Rook', icon: '♜' + T, pool: 'enemy', hp: 16, atk: 4, spd: 2, armor: 2, tags: ['chess', 'rook'], role: 'ranged',
      move: slide(4, 'orth'), attack: line(6, 'orth', { vfx: 'beam' }), threat: 4,
      blurb: 'A tower that fires down ranks and files.',
    },
    ebonQueen: {
      name: 'Ebon Queen', icon: '♛' + T, pool: 'enemy', hp: 18, atk: 4, spd: 6, tags: ['chess'], role: 'ranged',
      move: slide(4, 'all'), attack: ranged(3, { vfx: 'arcane' }), abilities: [{ id: 'queenStorm', p: { dmg: 3, initCd: 2 } }], threat: 7,
      blurb: 'The most dangerous piece on the board.',
    },
    ebonKing: {
      name: 'The Mad Grandmaster', icon: '♚' + T, pool: 'enemy', hp: 30, atk: 3, spd: 3, armor: 1, boss: true, big: true, tags: ['chess'],
      move: walk(1), attack: melee(), abilities: ['castling'],
      passives: { commanderAura: {}, oathbound: {} }, threat: 20, value: 60,
      blurb: 'Checkmate him and the whole army falls.',
    },
  };

  // Gore: a charging boar hits harder after a long run-up.
  AG.Passives.gore = {
    name: 'Gore',
    desc: (p) => '+' + p.bonus + ' damage after charging 2 or more squares.',
    outBonus(s, u, p, t, o) {
      if (o.kind !== 'attack') return 0;
      if (o.est) return p.bonus;
      return u.moveDist >= 2 ? p.bonus : 0;
    },
  };

  AG.playerUnitIds = function () {
    return Object.keys(AG.Units).filter((k) => AG.Units[k].pool === 'player');
  };
})(globalThis.AG = globalThis.AG || {});
