// Static game data: units and their ability picks, skills, gear, enchantments, relics,
// warbands, commander levels, acts and themed enemy encounters.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});

  // Grid directions: 0 = north (toward the enemy line), 1 = east, 2 = south, 3 = west.
  const DIRS = [
    [0, -1],
    [1, 0],
    [0, 1],
    [-1, 0],
  ];

  // Unit levels are bought per battle with Supply.
  const MAX_LEVEL = 3;
  const LEVEL_COST = [0, 0, 2, 5]; // extra Supply on top of the unit's base cost
  const LEVEL_HP = [1, 1, 1.2, 1.4];
  const LEVEL_POW = [1, 1, 1.15, 1.3];
  const SKILL_SLOTS = [0, 1, 2, 2];
  const GEAR_SLOTS = [0, 1, 1, 2];
  const TALENT_SLOTS = [0, 1, 2, 3];
  const RES_CAP = 0.5; // armor and magic resistance never go above 50%, or below -50%

  // Commander level: total Supply per battle, and the usual army size (cap): how big enemy
  // armies get and how many units Auto starts from. It does not limit your own army.
  const COMMAND = [
    null,
    { xp: 0, supply: 14, cap: 4 },
    { xp: 12, supply: 16, cap: 4 },
    { xp: 30, supply: 18, cap: 5 },
    { xp: 55, supply: 20, cap: 5 },
    { xp: 85, supply: 22, cap: 6 },
    { xp: 120, supply: 24, cap: 6 },
    { xp: 160, supply: 26, cap: 7 },
    { xp: 205, supply: 28, cap: 7 },
    { xp: 255, supply: 30, cap: 8 },
    { xp: 310, supply: 33, cap: 8 },
  ];

  // ---------------------------------------------------------------- abilities
  //
  // Each class picks 1 of 3 abilities at Level 1 and 1 of 3 more at Level 2; Level 3
  // adds a fixed mastery. An ability is a "mod": stat changes, traits, numeric props,
  // changes to the main attack, on-hit effects, or a second action (active).
  //
  // Act kinds: strike | cleave | quake | blast | line | cone | cross | nova | pray | grow |
  //   heal | shield | hazard | rally | drum | raise | revive | detonate | leap | blink |
  //   shadowstrike | none.  uses: 0 = unlimited, n = charges per battle.

  const A = {
    // Knight
    k_bash: { name: 'Shield Bash', cost: 0, desc: 'Active: slam an adjacent enemy for half damage and knock it back 1 tile. If it cannot move, it takes 6 extra damage.',
      mod: { active: { name: 'Shield Bash', kind: 'strike', range: [1, 1], dmg: 'phys', mult: 0.5, fx: { knock: 1 } } } },
    k_guard: { name: 'Guardian', cost: 1, desc: 'Adjacent allies take 15% less damage.', mod: { props: { guard: 0.15 } } },
    k_wall: { name: 'Shield Wall', cost: 2, desc: 'Attacks from the side face full block instead of half.', mod: { traits: ['shieldwall'] } },
    k_riposte: { name: 'Riposte', cost: 1, desc: 'When struck in melee and still standing, strikes back for half damage.', mod: { traits: ['retaliate'] } },
    k_plate: { name: 'Heavy Plate', cost: 0, desc: '+10% armor and +15% magic resistance.', mod: { stat: { armor: 0.1, res: 0.15 } } },
    k_rally: { name: 'Rallying Cry', cost: 2, desc: 'Active, 1 use: allies within 2 tiles take 1 turn off their cooldowns and shake off paralysis and roots.',
      mod: { active: { name: 'Rallying Cry', kind: 'rally', radius: 2, uses: 1 } } },

    // Archer
    a_snare: { name: 'Snare Shot', cost: 0, desc: 'Active: an arrow for 60% damage that roots the target for 2 turns. Rooted units cannot move.',
      mod: { active: { name: 'Snare Shot', kind: 'strike', range: [2, 5], dmg: 'phys', arc: true, mult: 0.6, fx: { root: 2 } } } },
    a_poison: { name: 'Poison Arrows', cost: 1, desc: 'Its basic attack poisons the target for 2 turns: 5 damage a turn, and it cannot be healed.', mod: { onHit: { poison: [2, 5] } } },
    a_smoke: { name: 'Smoke Screen', cost: 1, desc: 'Active, 2 uses: smoke over a 5-tile area up to 4 tiles away. For 2 turns, units inside cannot be targeted from more than 1 tile away.',
      mod: { active: { name: 'Smoke Screen', kind: 'hazard', hz: 'smoke', range: [0, 4], pattern: 'plus', turns: 2, arc: true, uses: 2 } } },
    a_eagle: { name: 'Eagle Eye', cost: 0, desc: '+1 range.', mod: { stat: { range: 1 } } },
    a_bodkin: { name: 'Bodkin Arrows', cost: 1, desc: "Arrows ignore half of the target's armor.", mod: { props: { pierce: 0.5 } } },
    a_hunter: { name: "Hunter's Mark", cost: 1, desc: 'Its hits mark the target for 2 turns: it takes 25% more damage from everyone.', mod: { onHit: { mark: 2 } } },
    a_volley: { name: 'Arrow Volley', cost: 2, desc: 'Active, 2 uses: rain arrows on a 5-tile area 3 to 5 tiles away, 70% damage to each enemy.',
      mod: { active: { name: 'Arrow Volley', kind: 'blast', range: [3, 5], pattern: 'plus', dmg: 'phys', arc: true, mult: 0.7, uses: 2 } } },

    // Scout
    s_caltrops: { name: 'Caltrops', cost: 0, desc: 'Active, 2 uses: scatter caltrops on an empty tile up to 3 away. The first enemy to step there stops, takes 6 damage and is rooted for 1 turn.',
      mod: { active: { name: 'Caltrops', kind: 'hazard', hz: 'caltrops', range: [1, 3], pattern: 'single', turns: 6, arc: true, uses: 2 } } },
    s_ambush: { name: 'Ambusher', cost: 1, desc: '+50% damage on attacks from behind.', mod: { props: { backMult: 0.5 } } },
    s_fleet: { name: 'Fleet-footed', cost: 1, desc: '+1 Move, and it slips through enemy units.', mod: { stat: { move: 1 }, traits: ['shadowstep'] } },
    s_evasion: { name: 'Evasion', cost: 0, desc: '+15% block.', mod: { stat: { block: 0.15 } } },
    s_mark: { name: 'Mark Prey', cost: 1, desc: 'Active, 2 uses: mark an enemy up to 5 tiles away. It takes 25% more damage for 2 turns.',
      mod: { active: { name: 'Mark Prey', kind: 'strike', range: [1, 5], arc: true, fx: { mark: 2 }, uses: 2 } } },
    s_venom: { name: 'Venom Blades', cost: 2, desc: 'Knife hits poison the target for 2 turns: 5 damage a turn, and no healing.', mod: { onHit: { poison: [2, 5] } } },

    // Cleric
    c_mend: { name: 'Mend', cost: 0, desc: 'Active: heal one ally up to 4 tiles away for 150% and cure its poison and burns.',
      mod: { active: { name: 'Mend', kind: 'heal', range: [0, 4], mult: 1.5, cure: true } } },
    c_smite: { name: 'Smite', cost: 1, desc: 'Active: holy light strikes an enemy 1 to 4 tiles away for full magic damage, +50% against undead and spirits.',
      mod: { active: { name: 'Smite', kind: 'strike', range: [1, 4], dmg: 'magic', arc: true, mult: 1, vs: { undead: 0.5, spirit: 0.5 } } } },
    c_bless: { name: 'Blessing', cost: 1, desc: 'Its basic ability (the healing prayer) also cures poison, burns, paralysis and roots.', mod: { act: { cleanse: true } } },
    c_fortitude: { name: 'Fortitude', cost: 1, desc: '+12 max HP and +15% magic resistance.', mod: { stat: { hp: 12, res: 0.15 } } },
    c_radiance: { name: 'Radiance', cost: 1, desc: 'Its basic ability (the healing prayer) heals 30% more.', mod: { props: { healMult: 0.3 } } },
    c_greater: { name: 'Greater Prayer', cost: 0, desc: 'Its basic ability (the healing prayer) reaches 1 tile further and heals 25% more.', mod: { stat: { radius: 1 }, props: { healMult: 0.25 } } },
    c_shield: { name: 'Divine Shield', cost: 1, desc: 'Active, 2 uses: an ally up to 3 tiles away gains a shield that absorbs 15 damage.',
      mod: { active: { name: 'Divine Shield', kind: 'shield', range: [0, 3], amount: 15, uses: 2 } } },
    c_revive: { name: 'Resurrection', cost: 2, desc: 'Active, 1 use: an ally that fell within 2 tiles rises again with 40% HP.',
      mod: { active: { name: 'Resurrection', kind: 'revive', range: [1, 2], pct: 0.4, uses: 1 } } },

    // Berserker
    b_rage: { name: 'Rage', cost: 0, desc: '+30% damage while below half HP.', mod: { props: { rageMult: 0.3 } } },
    b_warcry: { name: 'War Cry', cost: 1, desc: 'Active, 2 uses: enemies within 2 tiles are weakened for 2 turns: they deal 30% less damage.',
      mod: { active: { name: 'War Cry', kind: 'nova', radius: 2, fx: { weak: 2 }, uses: 2 } } },
    b_thirst: { name: 'Bloodthirst', cost: 1, desc: 'Its basic attack heals it 5 HP for every enemy struck.', mod: { traits: ['bloodrage'] } },
    b_scars: { name: 'Battle Scars', cost: 1, desc: '+15% armor and +10 max HP.', mod: { stat: { armor: 0.15, hp: 10 } } },
    b_leap: { name: 'Savage Leap', cost: 1, desc: 'Active, 2 uses: leap to an empty tile 2 or 3 away, over anything, and cleave every adjacent enemy for 80% damage.',
      mod: { active: { name: 'Savage Leap', kind: 'leap', range: [2, 3], dmg: 'phys', mult: 0.8, uses: 2 } } },
    b_unstop: { name: 'Unstoppable', cost: 0, desc: 'Immune to paralysis, roots and knockback.', mod: { traits: ['steadfast'] } },
    b_bloodlust: { name: 'Bloodlust', cost: 2, desc: 'Slaying an enemy resets its cooldown: it is ready again next turn.', mod: { traits: ['bloodlust'] } },

    // Pyromancer
    p_kindling: { name: 'Controlled Burn', cost: 0, desc: 'Its basic attack no longer burns allies.', mod: { act: { ff: false } } },
    p_ignite: { name: 'Ignite', cost: 1, desc: 'Its basic attack sets enemies burning: 5 damage a turn for 2 turns.', mod: { onHit: { burn: [2, 5] } } },
    p_firewall: { name: 'Wall of Fire', cost: 1, desc: 'Active, 2 uses: set a 5-tile area 2 to 4 tiles away ablaze for 2 turns. Enemies that enter it or start their turn in it take 6 damage.',
      mod: { active: { name: 'Wall of Fire', kind: 'hazard', hz: 'fire', range: [2, 4], pattern: 'plus', turns: 2, dmgFixed: 6, arc: true, uses: 2 } } },
    p_range: { name: 'Far Cast', cost: 0, desc: '+1 range.', mod: { stat: { range: 1 } } },
    p_cloak: { name: 'Flame Cloak', cost: 1, desc: 'Enemies that strike it in melee take 8 damage.', mod: { props: { thorns: 8 } } },
    p_inferno: { name: 'Inferno', cost: 2, desc: 'Its basic attack scorches a full 3x3 area.', mod: { act: { pattern: 'square' } } },

    // Assassin
    as_smoke: { name: 'Smoke Bomb', cost: 0, desc: 'Active, 2 uses: smoke around itself for 2 turns. Units in the smoke cannot be targeted from more than 1 tile away.',
      mod: { active: { name: 'Smoke Bomb', kind: 'hazard', hz: 'smoke', range: [0, 1], pattern: 'plus', turns: 2, uses: 2 } } },
    as_poison: { name: 'Poisoned Dagger', cost: 1, desc: 'Hits poison the target for 2 turns: 6 damage a turn, and no healing.', mod: { onHit: { poison: [2, 6] } } },
    as_exec: { name: 'Executioner', cost: 1, desc: '+40% damage against targets below half HP.', mod: { props: { execMult: 0.4 } } },
    as_evasion: { name: 'Evasion', cost: 0, desc: '+15% block.', mod: { stat: { block: 0.15 } } },
    as_cripple: { name: 'Hamstring', cost: 1, desc: 'Hits root the target for 1 turn.', mod: { onHit: { root: 1 } } },
    as_shadow: { name: 'Shadow Strike', cost: 2, desc: "Active, 2 uses: vanish and reappear behind an enemy 2 to 4 tiles away, striking its back. The tile behind it must be free.",
      mod: { active: { name: 'Shadow Strike', kind: 'shadowstrike', range: [2, 4], dmg: 'phys', mult: 1, uses: 2 } } },

    // Golem
    g_toss: { name: 'Boulder Toss', cost: 0, desc: 'Active: hurl a boulder at an enemy 2 to 4 tiles away for 80% damage, double against buildings.',
      mod: { active: { name: 'Boulder Toss', kind: 'strike', range: [2, 4], dmg: 'phys', arc: true, mult: 0.8, vs: { structure: 1 } } } },
    g_quake: { name: 'Earthshaker', cost: 1, desc: 'Its basic attack also hits every enemy beside the target.', mod: { act: { kind: 'quake' } } },
    g_moss: { name: 'Living Moss', cost: 1, desc: '+4 Regen: heals 4 HP each time it takes a turn.', mod: { props: { regen: 4 } } },
    g_bulwark: { name: 'Bulwark', cost: 1, desc: 'Its Guardian protection rises to 35%.', mod: { props: { guard: 0.35 } } },
    g_runes: { name: 'Runic Core', cost: 0, desc: '+30% magic resistance.', mod: { stat: { res: 0.3 } } },
    g_slam: { name: 'Ground Slam', cost: 2, desc: 'Active, 2 uses: strike every adjacent enemy for 80% damage and knock them back.',
      mod: { active: { name: 'Ground Slam', kind: 'nova', radius: 1, dmg: 'phys', mult: 0.8, fx: { knock: 1 }, uses: 2 } } },

    // Beast Rider
    br_howl: { name: 'Howl', cost: 0, desc: 'Active, 2 uses: enemies within 2 tiles are weakened for 2 turns: they deal 30% less damage.',
      mod: { active: { name: 'Howl', kind: 'nova', radius: 2, fx: { weak: 2 }, uses: 2 } } },
    br_trample: { name: 'Trample', cost: 1, desc: 'Its Charge bonus rises to +60%.', mod: { props: { chargeMult: 0.3 } } },
    br_hamstring: { name: 'Hamstring', cost: 1, desc: 'Its basic attack roots the target for 1 turn.', mod: { onHit: { root: 1 } } },
    br_pack: { name: 'Pack Hunter', cost: 0, desc: '+25% damage when another ally stands next to the target.', mod: { props: { packMult: 0.25 } } },
    br_swift: { name: 'Swift Mount', cost: 1, desc: '+1 Move.', mod: { stat: { move: 1 } } },
    br_scent: { name: 'Bloodscent', cost: 1, desc: 'Heals for 30% of the damage it deals.', mod: { props: { lifesteal: 0.3 } } },

    // Furgon
    f_bark: { name: 'Barkskin', cost: 0, desc: '+10% armor and +10% magic resistance.', mod: { stat: { armor: 0.1, res: 0.1 } } },
    f_roots: { name: 'Entangling Roots', cost: 1, desc: 'Active, 2 uses: roots every enemy in a 5-tile area 2 to 4 tiles away for 2 turns.',
      mod: { active: { name: 'Entangling Roots', kind: 'blast', range: [2, 4], pattern: 'plus', arc: true, fx: { root: 2 }, uses: 2 } } },
    f_thorn: { name: 'Thornwall', cost: 1, desc: 'Its shrubs have double HP and prick melee attackers for 6.', mod: { traits: ['thornwall'] } },
    f_deeproot: { name: 'Deep Roots', cost: 1, desc: '+2 Regen and +10 max HP.', mod: { stat: { hp: 10 }, props: { regen: 2 } } },
    f_grove: { name: 'Grove Keeper', cost: 0, desc: 'Grow reaches 1 tile further, and 4 shrubs can stand at once.', mod: { stat: { range: 1 }, props: { shrubs: 1 } } },
    f_rejuv: { name: 'Rejuvenate', cost: 1, desc: 'Active, 2 uses: heal an ally up to 3 tiles away for 16 and cure its poison and burns.',
      mod: { active: { name: 'Rejuvenate', kind: 'heal', range: [0, 3], fixed: 16, cure: true, uses: 2 } } },
    f_ironwood: { name: 'Ironwood', cost: 1, desc: 'Its shrubs have 40% armor and magic resistance.', mod: { traits: ['ironwood'] } },

    // Poison Wisp
    w_drift: { name: 'Drift', cost: 0, desc: '+1 Move.', mod: { stat: { move: 1 } } },
    w_virulent: { name: 'Virulence', cost: 1, desc: 'Its poison deals 2 more damage a turn.', mod: { props: { poisonDmg: 2 } } },
    w_wither: { name: 'Withering Mist', cost: 1, desc: 'Its basic attack also weakens the enemies in reach for 2 turns: they deal 30% less damage.', mod: { act: { fx: { weak: 2 } } } },
    w_ethereal: { name: 'Ethereal', cost: 0, desc: '+20% armor.', mod: { stat: { armor: 0.2 } } },
    w_linger: { name: 'Lingering Spores', cost: 1, desc: 'Its poison lasts 1 turn longer: 3 turns.', mod: { props: { poisonTurns: 1 } } },
    w_plague: { name: 'Plague', cost: 2, desc: 'Its basic attack reaches 3 tiles.', mod: { stat: { radius: 1 } } },

    // Barrier Ward
    bw_crystal: { name: 'Hardened Crystal', cost: 0, desc: '+20 max HP.', mod: { stat: { hp: 20 } } },
    bw_mend: { name: 'Mending Light', cost: 1, desc: 'Allies in its aura have +2 Regen.', mod: { traits: ['auramend'] } },
    bw_reach: { name: 'Wide Field', cost: 2, desc: 'Its aura reaches 5 tiles.', mod: { props: { auraR: 1 } } },
    bw_reflect: { name: 'Reflection', cost: 0, desc: 'Enemies that strike it in melee take 6 damage.', mod: { props: { thorns: 6 } } },
    bw_steel: { name: 'Steel Field', cost: 1, desc: 'Its aura grants 10% more armor: +35% in all.', mod: { traits: ['steelfield'] } },
    bw_purge: { name: 'Purging Pulse', cost: 1, desc: 'At the start of your turn, allies in its aura are cured of roots and burns.', mod: { traits: ['purge'] } },

    // Enchantress
    e_far: { name: 'Far Song', cost: 0, desc: '+1 range.', mod: { stat: { range: 1 } } },
    e_spike: { name: 'Mind Spike', cost: 1, desc: 'Its basic attack deals 50% more damage.', mod: { act: { mult: 1.5 } } },
    e_chain: { name: "Siren's Chain", cost: 1, desc: 'Its basic attack also roots its targets for 2 turns.', mod: { act: { fx: { root: 2 } } } },
    e_glamour: { name: 'Glamour', cost: 0, desc: '+15% block and +10% magic resistance.', mod: { stat: { block: 0.15, res: 0.1 } } },
    e_frailty: { name: 'Hex of Frailty', cost: 1, desc: 'Its basic attack marks its targets for 2 turns: they take 25% more damage.', mod: { act: { fx: { mark: 2 } } } },
    e_trance: { name: 'Deep Trance', cost: 2, desc: 'Paralysis lasts 2 turns.', mod: { act: { fx: { para: 2 } } } },

    // Dark Magic Witch
    wi_siphon: { name: 'Soul Siphon', cost: 0, desc: 'Heals for 30% of the damage it deals.', mod: { props: { lifesteal: 0.3 } } },
    wi_hex: { name: 'Hex', cost: 1, desc: 'Active, 2 uses: curse an enemy up to 5 tiles away. It takes 25% more damage for 2 turns.',
      mod: { active: { name: 'Hex', kind: 'strike', range: [1, 5], arc: true, fx: { mark: 2 }, uses: 2 } } },
    wi_abyss: { name: 'Abyssal Bolt', cost: 2, desc: 'Its basic attack passes through allies harmlessly and reaches 7 tiles.', mod: { act: { ff: false }, stat: { len: 2 } } },
    wi_long: { name: 'Long Reach', cost: 0, desc: 'Its basic attack reaches 1 tile further.', mod: { stat: { len: 1 } } },
    wi_curse: { name: 'Withering Curse', cost: 1, desc: 'Its basic attack weakens its targets for 2 turns: they deal 30% less damage.', mod: { act: { fx: { weak: 2 } } } },
    wi_sigils: { name: 'Warding Sigils', cost: 1, desc: '+20% magic resistance and +10 max HP.', mod: { stat: { res: 0.2, hp: 10 } } },
    wi_storm: { name: 'Black Storm', cost: 2, desc: 'Active, 1 use: dark lightning lashes out 4 tiles in all four directions, striking only enemies.',
      mod: { active: { name: 'Black Storm', kind: 'cross', len: 4, dmg: 'magic', uses: 1 } } },

    // Lightning Ward
    l_cap: { name: 'Capacitor', cost: 0, desc: '+15 max HP.', mod: { stat: { hp: 15 } } },
    l_shock: { name: 'Static Snare', cost: 1, desc: 'Its basic attack roots its targets for 1 turn.', mod: { act: { fx: { root: 1 } } } },
    l_over: { name: 'Overcharge', cost: 2, desc: 'Its basic attack reaches 3 tiles.', mod: { stat: { radius: 1 } } },
    l_conduct: { name: 'Conductor', cost: 0, desc: '+30% damage against armored targets (30% armor or more).', mod: { props: { vsArmored: 0.3 } } },
    l_ground: { name: 'Grounding Field', cost: 1, desc: 'Adjacent allies take 20% less magic damage.', mod: { props: { magicGuard: 0.2 } } },
    l_rapid: { name: 'Rapid Discharge', cost: 2, desc: 'Cooldown 1 turn shorter.', mod: { stat: { rec: -1 } } },

    // Dragon Tyrant
    d_scales: { name: 'Iron Scales', cost: 0, desc: '+10% armor and +10% magic resistance.', mod: { stat: { armor: 0.1, res: 0.1 } } },
    d_buffet: { name: 'Wing Buffet', cost: 1, desc: 'Active: knock back every adjacent enemy and deal 50% damage.',
      mod: { active: { name: 'Wing Buffet', kind: 'nova', radius: 1, dmg: 'phys', mult: 0.5, fx: { knock: 1 } } } },
    d_hellfire: { name: 'Hellfire', cost: 2, desc: 'Its basic attack reaches 4 tiles deep.', mod: { stat: { len: 1 } } },
    d_tamed: { name: 'Tamed Fire', cost: 0, desc: 'Its basic attack spares allies.', mod: { act: { ff: false } } },
    d_hide: { name: 'Ancient Hide', cost: 1, desc: '+30 max HP.', mod: { stat: { hp: 30 } } },
    d_searing: { name: 'Searing Flames', cost: 2, desc: 'Its hits set enemies burning: 5 damage a turn for 2 turns.', mod: { onHit: { burn: [2, 5] } } },
    d_terror: { name: 'Terror', cost: 2, desc: 'Active, 1 use: enemies within 3 tiles are weakened for 2 turns and marked: they deal 30% less and take 25% more damage.',
      mod: { active: { name: 'Terror', kind: 'nova', radius: 3, fx: { weak: 2, mark: 2 }, uses: 1 } } },

    // Mage Knight
    mk_ward: { name: 'Spellward Aura', cost: 0, desc: 'Adjacent allies take 20% less magic damage.', mod: { props: { magicGuard: 0.2 } } },
    mk_arcane: { name: 'Arcane Edge', cost: 1, desc: 'Its basic attack deals magic damage: armor and block do not stop it.', mod: { act: { dmg: 'magic' } } },
    mk_brand: { name: 'Rune Brand', cost: 1, desc: 'Hits mark the target for 2 turns: it takes 25% more damage.', mod: { onHit: { mark: 2 } } },
    mk_bulwark: { name: 'Runic Bulwark', cost: 1, desc: '+15% armor and +15% block.', mod: { stat: { armor: 0.15, block: 0.15 } } },
    mk_spellbreak: { name: 'Spellbreaker', cost: 0, desc: '+30% damage against spellcasters.', mod: { props: { vs: { caster: 0.3 } } } },
    mk_blink: { name: 'Blink', cost: 1, desc: 'Active, 2 uses: teleport to an empty tile up to 3 tiles away, ignoring anything in between. It is its action for the turn.',
      mod: { active: { name: 'Blink', kind: 'blink', range: [1, 3], uses: 2 } } },
    mk_burst: { name: 'Arcane Burst', cost: 2, desc: 'Active, 2 uses: arcane force strikes every adjacent enemy for 80% magic damage.',
      mod: { active: { name: 'Arcane Burst', kind: 'nova', radius: 1, dmg: 'magic', mult: 0.8, uses: 2 } } },

    // Skeleton Archer
    sa_rattle: { name: 'Rattling Bones', cost: 0, desc: '+8 max HP.', mod: { stat: { hp: 8 } } },
    sa_grave: { name: 'Grave Arrows', cost: 1, desc: 'Hits weaken the target for 2 turns: it deals 30% less damage.', mod: { onHit: { weak: 2 } } },
    sa_frost: { name: 'Frost Arrows', cost: 1, desc: 'Hits root the target for 1 turn.', mod: { onHit: { root: 1 } } },
    sa_gaze: { name: 'Hollow Gaze', cost: 0, desc: '+1 range.', mod: { stat: { range: 1 } } },
    sa_volley: { name: 'Bone Volley', cost: 1, desc: 'Active, 2 uses: bones rain on a 5-tile area 2 to 4 tiles away, 60% damage to each enemy.',
      mod: { active: { name: 'Bone Volley', kind: 'blast', range: [2, 4], pattern: 'plus', dmg: 'phys', arc: true, mult: 0.6, uses: 2 } } },
    sa_reform: { name: 'Reassemble', cost: 2, desc: 'Once per battle, survives a fatal blow with 1 HP.', mod: { traits: ['secondwind'] } },

    // Trebuchet
    tb_counter: { name: 'Counterweight', cost: 0, desc: '+1 range.', mod: { stat: { range: 1 } } },
    tb_firepots: { name: 'Fire Pots', cost: 1, desc: 'Its basic attack sets targets burning: 5 damage a turn for 2 turns.', mod: { onHit: { burn: [2, 5] } } },
    tb_scatter: { name: 'Scattershot', cost: 2, desc: 'Active, 2 uses: stones rain on a 5-tile area 3 to 5 tiles away, 70% damage to each enemy.',
      mod: { active: { name: 'Scattershot', kind: 'blast', range: [3, 5], pattern: 'plus', dmg: 'phys', arc: true, mult: 0.7, uses: 2 } } },
    tb_frame: { name: 'Reinforced Frame', cost: 0, desc: '+20 max HP and +10% armor.', mod: { stat: { hp: 20, armor: 0.1 } } },
    tb_wreck: { name: 'Wrecking Shot', cost: 1, desc: "Its basic attack ignores half of the target's armor.", mod: { props: { pierce: 0.5 } } },
    tb_crew: { name: 'Veteran Crew', cost: 2, desc: 'Cooldown 1 turn shorter.', mod: { stat: { rec: -1 } } },
  };

  // Every active ability: [uses a battle, cooldown]. Uses never come back. The cooldown is
  // its own, counted in the unit's turns after each use and on top of the unit's cooldown,
  // so a strong one cannot come out every turn. Using one is the unit's action that turn,
  // in place of its attack.
  const ACTIVE_LIMITS = {
    k_bash: [3, 2], k_rally: [1, 0],
    a_snare: [3, 2], a_smoke: [2, 3], a_volley: [3, 4],
    s_caltrops: [2, 2], s_mark: [2, 2],
    c_mend: [3, 2], c_smite: [3, 2], c_shield: [2, 2], c_revive: [1, 0],
    b_warcry: [2, 3], b_leap: [3, 3],
    p_firewall: [2, 3],
    as_smoke: [2, 2], as_shadow: [2, 3],
    g_toss: [3, 2], g_slam: [2, 3],
    br_howl: [2, 3],
    f_roots: [2, 3], f_rejuv: [2, 2],
    wi_hex: [2, 2], wi_storm: [1, 0],
    d_buffet: [3, 2], d_terror: [1, 0],
    mk_blink: [2, 2], mk_burst: [3, 3],
    sa_volley: [2, 3],
    tb_scatter: [3, 4],
  };
  const activeTag = (a) => `Active, ${a.uses} use${a.uses > 1 ? 's' : ''}${a.cd ? `, cooldown ${a.cd}` : ''}`;
  for (const id in ACTIVE_LIMITS) {
    const ab = A[id];
    [ab.mod.active.uses, ab.mod.active.cd] = ACTIVE_LIMITS[id];
    ab.desc = ab.desc.replace(/^Active(, \d+ uses?)?:/, activeTag(ab.mod.active) + ':');
  }

  // Level 3 masteries (fixed per class).
  const MASTERY = {
    knight: { name: 'Champion', desc: '+20% damage and +10% block.', mod: { props: { dmgMult: 0.2 }, stat: { block: 0.1 } } },
    archer: { name: 'Deadeye', desc: '+20% damage and +1 range.', mod: { props: { dmgMult: 0.2 }, stat: { range: 1 } } },
    scout: { name: 'Shadow Dance', desc: '+30% damage from the side or behind.', mod: { props: { flankMult: 0.3 } } },
    cleric: { name: 'Devotion', desc: 'Its basic ability (the healing prayer) heals 50% more, and +10 max HP.', mod: { stat: { hp: 10 }, props: { healMult: 0.5 } } },
    berserker: { name: 'Juggernaut', desc: '+15 max HP and +15% damage.', mod: { stat: { hp: 15 }, props: { dmgMult: 0.15 } } },
    pyromancer: { name: 'Pyroclasm', desc: '+25% damage.', mod: { props: { dmgMult: 0.25 } } },
    assassin: { name: 'Deathmark', desc: 'Attacks from behind deal double damage.', mod: { props: { backMult: 0.5 } } },
    golem: { name: 'Colossus', desc: '+25 max HP and +1 Move.', mod: { stat: { hp: 25, move: 1 } } },
    beastrider: { name: 'Ride Down', desc: 'After moving 3 or more tiles, its basic attack knocks the target back.', mod: { traits: ['ridedown'] } },
    furgon: { name: 'Ancient Bark', desc: '+20 max HP and +2 Regen.', mod: { stat: { hp: 20 }, props: { regen: 2 } } },
    wisp: { name: 'Pestilence', desc: 'Its basic attack also deals 8 magic damage (never to buildings).', mod: { act: { dmg: 'magic', fixed: 8 } } },
    barrier: { name: 'Aegis Field', desc: 'Its aura also softens physical blows by 15%.', mod: { traits: ['aegisfield'] } },
    enchantress: { name: 'Grand Illusion', desc: 'Its basic attack covers a full 3x3 area.', mod: { act: { pattern: 'square' } } },
    witch: { name: 'Shadow Pact', desc: '+25% damage.', mod: { props: { dmgMult: 0.25 } } },
    lightning: { name: 'Thunderhead', desc: '+25% damage.', mod: { props: { dmgMult: 0.25 } } },
    dragon: { name: 'Wyrmlord', desc: '+25% damage and +20 max HP.', mod: { stat: { hp: 20 }, props: { dmgMult: 0.25 } } },
    trebuchet: { name: 'Siege Master', desc: '+25% damage, and boulders deal a further +100% to buildings.', mod: { props: { dmgMult: 0.25, vs: { structure: 1 } } } },
    mageknight: { name: 'Runic Mastery', desc: 'Hits also deal 8 bonus magic damage.', mod: { props: { bonusMagic: 8 } } },
    skelarcher: { name: 'Undying', desc: 'The first time it falls in a battle, it rises again with half HP.', mod: { traits: ['phoenix'] } },
  };

  // ---------------------------------------------------------------- units
  //
  // res = magic resistance. tags drive gear bonuses (Blessed Blade vs undead, and so on).
  // Buildings carry the 'structure' tag, which siege damage targets, and a material:
  // stone resists swords and spells, wood burns, arcane unravels under magic.

  const TOTEM = {
    rarity: 'none', cost: 0, role: 'object',
    pow: 0, armor: 0.5, res: 0.3, block: 0, rec: 0, move: 0,
    act: { name: 'Mending Ward', kind: 'none' },
    traits: ['immobile', 'nofacing', 'object', 'totem'], tags: ['structure'], material: 'stone',
    tip: 'Stone shrugs off swords and spells alike. Siege damage cracks it fast.',
  };

  const SPAWNER = {
    rarity: 'none', cost: 0, role: 'object',
    pow: 0, block: 0, rec: 0, move: 0,
    act: { name: 'Reinforce', kind: 'none' },
    traits: ['immobile', 'nofacing', 'object', 'spawner'], tags: ['structure'],
  };

  const UNITS = {
    knight: {
      name: 'Knight', rarity: 'common', cost: 3, role: 'tank',
      hp: 52, pow: 18, armor: 0.35, res: 0, block: 0.7, rec: 1, move: 3,
      act: { name: 'Sword Strike', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['human'],
      abilities: { 1: ['k_bash', 'k_guard', 'k_wall'], 2: ['k_plate', 'k_riposte', 'k_rally'] },
      desc: 'Plate-clad swordsman. Turns aside most blows that come from the front.',
      tip: 'No magic resistance. Burn it with spells, or strike from behind.',
    },
    archer: {
      name: 'Archer', rarity: 'common', cost: 3, role: 'ranged',
      hp: 34, pow: 16, armor: 0.1, res: 0.1, block: 0.3, rec: 1, move: 3,
      act: { name: 'Longbow', kind: 'strike', range: [2, 5], dmg: 'phys', arc: true },
      traits: [], tags: ['human'],
      abilities: { 1: ['a_snare', 'a_poison', 'a_smoke'], 2: ['a_eagle', 'a_bodkin', 'a_volley', 'a_hunter'] },
      desc: 'Shoots up to 5 tiles over the heads of other units. Cannot shoot an adjacent foe.',
      tip: "Fragile up close. Rush it with fast units, or soak arrows on a Knight's front.",
    },
    scout: {
      name: 'Scout', rarity: 'common', cost: 2, role: 'skirmisher',
      hp: 28, pow: 11, armor: 0.05, res: 0.1, block: 0.5, rec: 0, move: 5,
      act: { name: 'Throwing Knives', kind: 'strike', range: [1, 3], dmg: 'phys', arc: true },
      traits: [], tags: ['human'],
      abilities: { 1: ['s_caltrops', 's_ambush', 's_fleet'], 2: ['s_evasion', 's_mark', 's_venom'] },
      desc: 'Fast and cheap. No cooldown: it can act every single turn.',
      tip: 'Its light hits glance off armor. Keep your backs covered against its flanking.',
    },
    cleric: {
      name: 'Cleric', rarity: 'common', cost: 3, role: 'support',
      hp: 28, pow: 12, armor: 0, res: 0.3, block: 0, rec: 2, move: 3,
      act: { name: 'Prayer', kind: 'pray', radius: 3 },
      traits: [], tags: ['human', 'caster'],
      abilities: { 1: ['c_mend', 'c_smite', 'c_bless', 'c_fortitude'], 2: ['c_greater', 'c_shield', 'c_revive', 'c_radiance'] },
      desc: 'Heals every ally within 3 tiles, itself included.',
      tip: 'Poisoned units cannot be healed. Kill the Cleric first, or poison its huddle.',
    },
    berserker: {
      name: 'Berserker', rarity: 'common', cost: 3, role: 'melee',
      hp: 46, pow: 19, armor: 0.1, res: 0, block: 0.1, rec: 1, move: 3,
      act: { name: 'Cleave', kind: 'cleave', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['human'],
      abilities: { 1: ['b_rage', 'b_warcry', 'b_thirst', 'b_scars'], 2: ['b_unstop', 'b_leap', 'b_bloodlust'] },
      desc: 'Its basic attack strikes every adjacent enemy at once.',
      tip: 'Almost no armor or block. Arrows and spells cut it down before it arrives.',
    },
    skelarcher: {
      name: 'Skeleton Archer', rarity: 'common', cost: 2, role: 'ranged',
      hp: 24, pow: 13, armor: 0.2, res: 0, block: 0.2, rec: 1, move: 3,
      act: { name: 'Bone Bow', kind: 'strike', range: [2, 4], dmg: 'phys', arc: true },
      traits: ['undead'], tags: ['undead'],
      abilities: { 1: ['sa_rattle', 'sa_grave', 'sa_frost'], 2: ['sa_gaze', 'sa_volley', 'sa_reform'] },
      desc: 'A cheap, tireless bowman raised from an old battlefield. Immune to poison.',
      tip: 'Brittle against magic, and Blessed weapons shatter it.',
    },
    pyromancer: {
      name: 'Pyromancer', rarity: 'uncommon', cost: 4, role: 'caster',
      hp: 28, pow: 16, armor: 0, res: 0.3, block: 0.2, rec: 2, move: 3,
      act: { name: 'Fireball', kind: 'blast', range: [2, 4], dmg: 'magic', pattern: 'plus', ff: true, arc: true },
      traits: [], tags: ['human', 'caster'],
      abilities: { 1: ['p_kindling', 'p_ignite', 'p_firewall'], 2: ['p_range', 'p_cloak', 'p_inferno'] },
      desc: 'Its basic attack, a fireball, bursts over 5 tiles. Magic ignores armor and block, but not magic resistance.',
      tip: 'Spread out against fire. High magic resistance halves it.',
    },
    assassin: {
      name: 'Assassin', rarity: 'uncommon', cost: 3, role: 'skirmisher',
      hp: 32, pow: 20, armor: 0.1, res: 0.15, block: 0.6, rec: 1, move: 4,
      act: { name: 'Backstab', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: ['shadowstep'], tags: ['human'], props: { backMult: 0.5 },
      abilities: { 1: ['as_smoke', 'as_poison', 'as_exec'], 2: ['as_evasion', 'as_cripple', 'as_shadow'] },
      desc: 'Slips through enemy lines and deals +50% damage from behind.',
      tip: 'Turn your fragile units to face it. Shrubs, Knights and wards stop it cold.',
    },
    mageknight: {
      name: 'Mage Knight', rarity: 'uncommon', cost: 4, role: 'tank',
      hp: 48, pow: 17, armor: 0.2, res: 0.5, block: 0.45, rec: 1, move: 3,
      act: { name: 'Runeblade', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['human'],
      abilities: { 1: ['mk_ward', 'mk_arcane', 'mk_brand'], 2: ['mk_spellbreak', 'mk_blink', 'mk_burst', 'mk_bulwark'] },
      desc: 'Rune-etched armor shrugs off half of all magic. Strikes with a physical blade.',
      tip: 'Light armor for a frontliner: arrows and axes hurt it more than spells do.',
    },
    golem: {
      name: 'Stone Golem', rarity: 'uncommon', cost: 4, role: 'tank',
      hp: 74, pow: 18, armor: 0.5, res: -0.25, block: 0, rec: 1, move: 2,
      act: { name: 'Stone Fist', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: ['stoneskin'], tags: ['construct'], props: { guard: 0.2 },
      abilities: { 1: ['g_toss', 'g_quake', 'g_moss'], 2: ['g_runes', 'g_bulwark', 'g_slam'] },
      desc: 'Slow living rock: 50% armor, immune to poison and paralysis. Adjacent allies take 20% less damage.',
      tip: 'Magic tears through it: it takes 25% extra magic damage. Kite it, it moves 2.',
    },
    beastrider: {
      name: 'Beast Rider', rarity: 'uncommon', cost: 4, role: 'melee',
      hp: 46, pow: 19, armor: 0.2, res: 0.1, block: 0.35, rec: 1, move: 5,
      act: { name: 'Lance', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['human', 'beast'], props: { chargeMult: 0.3 },
      abilities: { 1: ['br_howl', 'br_trample', 'br_hamstring'], 2: ['br_pack', 'br_swift', 'br_scent'] },
      desc: 'Rides a war-wolf. Charge: +30% damage after moving 3 or more tiles before striking.',
      tip: "A Knight's front block blunts its charge. Box it in with shrubs and wards.",
    },
    furgon: {
      name: 'Furgon', rarity: 'uncommon', cost: 3, role: 'support',
      hp: 38, pow: 10, armor: 0.1, res: 0.2, block: 0.3, rec: 1, move: 3,
      act: { name: 'Grow Shrub', kind: 'grow', range: [1, 3] },
      traits: [], tags: ['beast'], props: { regen: 3 },
      abilities: { 1: ['f_bark', 'f_roots', 'f_thorn', 'f_deeproot'], 2: ['f_grove', 'f_rejuv', 'f_ironwood'] },
      desc: 'Forest spirit. Raises a shrub that blocks movement and lines, 3 at a time. Regen 3.',
      tip: 'Shrubs can be cut down, and flyers and arcing shots ignore them.',
    },
    wisp: {
      name: 'Poison Wisp', rarity: 'uncommon', cost: 3, role: 'caster',
      hp: 24, pow: 8, armor: 0, res: 0.4, block: 0.4, rec: 1, move: 4,
      act: { name: 'Miasma', kind: 'nova', radius: 2, fx: { poison: 2 } },
      traits: ['flying'], tags: ['spirit'],
      abilities: { 1: ['w_drift', 'w_virulent', 'w_wither'], 2: ['w_ethereal', 'w_linger', 'w_plague'] },
      desc: 'Floats over anything. Poisons enemies within 2 tiles for 2 of their turns: they lose HP as each turn starts and cannot heal. Buildings, wagons, cages and constructs are immune.',
      tip: 'Only 24 HP and no armor. One arrow volley can drop it.',
    },
    barrier: {
      name: 'Barrier Ward', rarity: 'uncommon', cost: 3, role: 'ward',
      hp: 40, pow: 0, armor: 0.2, res: 0.5, block: 0, rec: 0, move: 0,
      act: { name: 'Barrier Aura', kind: 'none' },
      traits: ['immobile', 'aura_barrier', 'nofacing'], tags: ['construct'],
      abilities: { 1: ['bw_crystal', 'bw_mend', 'bw_reach'], 2: ['bw_reflect', 'bw_steel', 'bw_purge'] },
      desc: 'Rooted crystal. Allies within 4 tiles gain +25% armor and +25% magic resistance, and are immune to poison and paralysis.',
      tip: 'It cannot move or fight. Bring physical attackers, or draw foes out of its reach.',
    },
    enchantress: {
      name: 'Enchantress', rarity: 'rare', cost: 4, role: 'caster',
      hp: 30, pow: 10, armor: 0, res: 0.35, block: 0.25, rec: 2, move: 3,
      act: { name: 'Mesmerize', kind: 'blast', range: [2, 4], dmg: 'magic', pattern: 'plus', arc: true, fx: { para: 1 } },
      traits: [], tags: ['human', 'caster'],
      abilities: { 1: ['e_far', 'e_spike', 'e_chain'], 2: ['e_glamour', 'e_frailty', 'e_trance'] },
      desc: 'Paralyzes enemies in a 5-tile burst. They lose a turn and cannot block until it wears off.',
      tip: 'Golems, and units near a Barrier Ward, shrug off paralysis.',
    },
    witch: {
      name: 'Dark Magic Witch', rarity: 'rare', cost: 4, role: 'caster',
      hp: 28, pow: 17, armor: 0, res: 0.35, block: 0.2, rec: 2, move: 3,
      act: { name: 'Dark Lightning', kind: 'line', len: 5, dmg: 'magic', ff: true },
      traits: [], tags: ['human', 'caster'],
      abilities: { 1: ['wi_siphon', 'wi_hex', 'wi_abyss', 'wi_sigils'], 2: ['wi_long', 'wi_curse', 'wi_storm'] },
      desc: 'Black lightning strikes every unit in a straight line up to 5 tiles. Rocks stop it.',
      tip: 'Never line up in front of a Witch. Rocks and staggered formations break the line.',
    },
    lightning: {
      name: 'Lightning Ward', rarity: 'rare', cost: 4, role: 'ward',
      hp: 46, pow: 16, armor: 0.25, res: 0.25, block: 0, rec: 1, move: 0,
      act: { name: 'Storm Pulse', kind: 'nova', radius: 2, dmg: 'magic' },
      traits: ['immobile', 'nofacing'], tags: ['construct'],
      abilities: { 1: ['l_cap', 'l_shock', 'l_over'], 2: ['l_conduct', 'l_ground', 'l_rapid'] },
      desc: 'Rooted totem. Zaps every enemy within 2 tiles with magic.',
      tip: 'It cannot move. Archers and fireballs can hit it from outside its reach.',
    },
    dragon: {
      name: 'Dragon Tyrant', rarity: 'legendary', cost: 8, role: 'monster',
      hp: 100, pow: 22, armor: 0.3, res: 0.3, block: 0, rec: 2, move: 4,
      act: { name: 'Fire Breath', kind: 'cone', len: 3, dmg: 'magic', ff: true },
      traits: ['flying', 'big'], tags: ['big', 'beast'],
      abilities: { 1: ['d_scales', 'd_buffet', 'd_hellfire'], 2: ['d_tamed', 'd_hide', 'd_terror', 'd_searing'] },
      desc: 'Winged tyrant. Breathes fire over a 7-tile cone and flies over anything.',
      tip: 'Mighty but slow to recover. Swarm it from the sides while it rests.',
    },
    trebuchet: {
      name: 'Trebuchet', rarity: 'uncommon', cost: 4, role: 'ranged',
      hp: 40, pow: 15, armor: 0.25, res: -0.2, block: 0, rec: 2, move: 2,
      act: { name: 'Boulder', kind: 'strike', range: [3, 6], dmg: 'phys', arc: true, vs: { structure: 1.5 } },
      traits: [], tags: ['construct'],
      abilities: { 1: ['tb_counter', 'tb_firepots', 'tb_scatter'], 2: ['tb_frame', 'tb_wreck', 'tb_crew'] },
      desc: 'Siege engine. Lobs boulders 3 to 6 tiles and deals +150% damage to buildings. Cannot hit anything closer than 3 tiles.',
      tip: 'Helpless up close, and its timber burns: rush it, or hit it with magic.',
    },

    // ------------------------------------------------ summons and objects
    shrub: {
      name: 'Shrub', rarity: 'none', cost: 0, role: 'object',
      hp: 18, pow: 0, armor: 0, res: 0, block: 0, rec: 0, move: 0,
      act: { name: 'None', kind: 'none' },
      traits: ['immobile', 'nofacing', 'summon'], tags: [],
      desc: 'A thorny thicket. Blocks movement and lines until cut down.',
      tip: 'Cut it down, or fly and shoot over it.',
    },
    warbanner: {
      name: 'War Banner', rarity: 'none', cost: 0, role: 'object',
      hp: 70, pow: 0, armor: 0.1, res: -0.2, block: 0, rec: 0, move: 0,
      act: { name: 'Rally', kind: 'none' },
      traits: ['immobile', 'nofacing', 'object'], tags: ['structure'], material: 'wood',
      desc: 'The enemy standard. Enemies within 2 tiles of it deal 15% more damage.',
      tip: 'Burn it to break their will and win the battle.',
    },
    cage: {
      name: 'Prison Cage', rarity: 'none', cost: 0, role: 'object',
      hp: 78, pow: 0, armor: 0.3, res: 0.2, block: 0, rec: 0, move: 0,
      act: { name: 'None', kind: 'none' },
      traits: ['immobile', 'nofacing', 'object'], tags: ['structure'], material: 'iron',
      desc: 'Captives rattle the bars. Break the cage to free them.',
      tip: 'Breaking the cage wins the battle. The freed prisoner joins your army.',
    },
    cart: {
      name: 'Loot Wagon', rarity: 'none', cost: 0, role: 'object',
      hp: 56, pow: 0, armor: 0.3, res: -0.2, block: 0, rec: 0, move: 1,
      act: { name: 'Flee', kind: 'none' },
      traits: ['nofacing', 'object', 'cart'], tags: ['structure'], material: 'wood',
      desc: 'A wagon heavy with stolen goods, rumbling for the far edge of the field.',
      tip: 'Break every wagon before it escapes off the left edge. Units in its way slow it down.',
    },
    wall: {
      name: 'Castle Wall', rarity: 'none', cost: 0, role: 'object',
      hp: 70, pow: 0, armor: 0.45, res: 0.3, block: 0, rec: 0, move: 0,
      act: { name: 'None', kind: 'none' },
      traits: ['immobile', 'nofacing', 'object', 'scenery'], tags: ['structure'], material: 'stone',
      desc: 'Thick castle stone. Blocks movement and lines. Flyers and arcing shots pass over it.',
      tip: 'Go through the gate or around the ends. Siege damage breaks stone fast.',
    },
    gate: {
      name: 'Castle Gate', rarity: 'none', cost: 0, role: 'object',
      hp: 130, pow: 0, armor: 0.4, res: -0.2, block: 0, rec: 0, move: 0,
      act: { name: 'None', kind: 'none' },
      traits: ['immobile', 'nofacing', 'object'], tags: ['structure'], material: 'wood',
      desc: 'An oak-and-iron gate. Breaking it opens the castle.',
      tip: 'Breaking the gate wins a siege. Siege damage and fire bring it down fastest.',
    },
    barrel: {
      name: 'Powder Keg', rarity: 'none', cost: 0, role: 'object',
      hp: 10, pow: 0, armor: 0, res: 0, block: 0, rec: 0, move: 0,
      act: { name: 'None', kind: 'none' },
      traits: ['immobile', 'nofacing', 'object', 'scenery', 'volatile'], tags: ['structure'], material: 'wood', props: { boom: 22 },
      desc: 'Black powder. Explodes when broken, dealing 22 damage to everything next to it.',
      tip: 'Shoot it when enemies stand beside it. Explosions set off other kegs too.',
    },
    barricade: {
      name: 'Barricade', rarity: 'none', cost: 0, role: 'object',
      hp: 30, pow: 0, armor: 0.3, res: -0.25, block: 0, rec: 0, move: 0,
      act: { name: 'None', kind: 'none' },
      traits: ['immobile', 'nofacing', 'object', 'scenery'], tags: ['structure'], material: 'wood',
      desc: 'Sharpened stakes. Blocks movement and lines until broken.',
      tip: 'Break through with siege damage or fire, or go around.',
    },

    // Totems: objectives that mend the enemies around them.
    totem: Object.assign({}, TOTEM, {
      name: 'Stone Totem', hp: 40, props: { totemHeal: 4 },
      desc: 'A carved war-stone. At the start of their turn, enemies within 2 tiles heal 4 HP.',
    }),
    hexstone: Object.assign({}, TOTEM, {
      name: 'Hex Stone', hp: 46, props: { totemHeal: 5 },
      desc: 'A rune-cut standing stone. At the start of their turn, enemies within 2 tiles heal 5 HP.',
    }),
    obelisk: Object.assign({}, TOTEM, {
      name: 'Ember Obelisk', hp: 52, props: { totemHeal: 6 },
      desc: 'A shard of black glass, warm to the touch. At the start of their turn, enemies within 2 tiles heal 6 HP.',
    }),

    // Spawners: reinforcements march out of them until they fall.
    war_tent: Object.assign({}, SPAWNER, {
      name: 'War Tent', hp: 44, armor: 0.3, res: -0.25, material: 'wood',
      desc: 'Hide and canvas. Fresh warriors march out of it every few turns until it falls.',
      tip: 'Fire and siege damage tear it down. Stand in the doorway to block an arrival.',
    }),
    crypt: Object.assign({}, SPAWNER, {
      name: 'Crypt', hp: 56, armor: 0.5, res: 0.3, material: 'stone',
      desc: 'The dead claw their way out of it every few turns until it is broken.',
      tip: 'Thick stone: bring siege damage. Stand in the doorway to block an arrival.',
    }),
    den: Object.assign({}, SPAWNER, {
      name: 'Beast Den', hp: 50, armor: 0.5, res: 0.3, material: 'stone',
      desc: 'A rocky lair. Beasts prowl out of it every few turns until it caves in.',
      tip: 'Solid rock: bring siege damage. Stand at the mouth to block an arrival.',
    }),
    portal: Object.assign({}, SPAWNER, {
      name: 'Dark Portal', hp: 40, armor: 0.5, res: -0.5, material: 'arcane',
      desc: 'A tear in the world. Creatures step through every few turns until it is closed.',
      tip: 'Steel barely scratches it, but magic unravels it.',
    }),
    guardhouse: Object.assign({}, SPAWNER, {
      name: 'Guardhouse', hp: 54, armor: 0.5, res: 0.3, material: 'stone',
      desc: 'Soldiers muster here and march out every few turns until it falls.',
      tip: 'Stone walls: bring siege damage, or win before the garrison gathers.',
    }),

    // ------------------------------------------------ enemy forces
    orc: {
      name: 'Orc Warrior', rarity: 'enemy', cost: 3, role: 'melee',
      hp: 46, pow: 17, armor: 0.2, res: 0, block: 0.3, rec: 1, move: 3,
      act: { name: 'Cleaver', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['greenskin'],
      desc: 'A tusked brawler in scavenged mail.',
      tip: 'No magic resistance. Orcbane weapons bite deep.',
    },
    brute: {
      name: 'Orc Brute', rarity: 'enemy', cost: 4, role: 'tank',
      hp: 64, pow: 21, armor: 0.3, res: -0.1, block: 0.1, rec: 1, move: 3,
      act: { name: 'Crushing Maul', kind: 'quake', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['greenskin', 'big'],
      desc: 'A hulking orc whose maul flattens a foe and everyone beside it.',
      tip: 'Weak to magic. Do not bunch up next to the unit it is about to hit.',
    },
    goblin_archer: {
      name: 'Goblin Archer', rarity: 'enemy', cost: 2, role: 'ranged',
      hp: 22, pow: 12, armor: 0.05, res: 0, block: 0.4, rec: 1, move: 4,
      act: { name: 'Shortbow', kind: 'strike', range: [2, 4], dmg: 'phys', arc: true },
      traits: [], tags: ['greenskin'],
      desc: 'Small, quick and spiteful, with a short bow.',
      tip: 'Only 22 HP. Anything that reaches it kills it.',
    },
    sapper: {
      name: 'Goblin Sapper', rarity: 'enemy', cost: 2, role: 'skirmisher',
      hp: 20, pow: 24, armor: 0, res: 0, block: 0.2, rec: 0, move: 4,
      act: { name: 'Detonate', kind: 'detonate', radius: 1, dmg: 'magic', ff: true },
      traits: ['volatile'], tags: ['greenskin'], props: { boom: 14 },
      desc: 'Carries a lit keg. Runs at your lines and blows itself up, hurting everything next to it.',
      tip: 'Kill it at range before it arrives, and keep your units spread. If killed it still bursts for 14.',
    },
    shaman: {
      name: 'Orc Shaman', rarity: 'enemy', cost: 3, role: 'support',
      hp: 30, pow: 10, armor: 0.1, res: 0.3, block: 0.2, rec: 2, move: 3,
      act: { name: 'War Drums', kind: 'drum', radius: 2 },
      traits: [], tags: ['greenskin', 'caster'],
      desc: 'Beats the war drums: allies within 2 tiles heal 10 and fly into a frenzy, dealing 25% more damage for 2 turns.',
      tip: 'Kill the drummer first and the warband loses its fury.',
    },
    warg: {
      name: 'Warg', rarity: 'enemy', cost: 3, role: 'skirmisher',
      hp: 34, pow: 15, armor: 0.1, res: 0.1, block: 0.2, rec: 0, move: 5,
      act: { name: 'Savage Bite', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['beast'], props: { packMult: 0.25 },
      desc: 'A great wolf. Acts every turn and bites 25% harder when an ally flanks the same target.',
      tip: 'Keep your units shoulder to shoulder so wargs cannot gang up.',
    },
    wolf: {
      name: 'Dire Wolf', rarity: 'enemy', cost: 2, role: 'skirmisher',
      hp: 26, pow: 12, armor: 0.05, res: 0.05, block: 0.3, rec: 0, move: 5,
      act: { name: 'Bite', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['beast'], props: { packMult: 0.25 },
      desc: 'Hunts in packs. Bites 25% harder when an ally flanks the same target.',
      tip: 'Fragile alone. A Knight facing the pack blocks most bites.',
    },
    cutthroat: {
      name: 'Cutthroat', rarity: 'enemy', cost: 3, role: 'skirmisher',
      hp: 30, pow: 14, armor: 0.1, res: 0.1, block: 0.45, rec: 0, move: 4,
      act: { name: 'Dirk', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['human'], props: { backMult: 0.5 },
      desc: 'A bandit with a long knife. Acts every turn and deals +50% damage from behind.',
      tip: 'Face it. Its dirk is deadly only from behind.',
    },
    crossbow: {
      name: 'Crossbowman', rarity: 'enemy', cost: 3, role: 'ranged',
      hp: 32, pow: 19, armor: 0.2, res: 0, block: 0.3, rec: 2, move: 3,
      act: { name: 'Heavy Bolt', kind: 'strike', range: [2, 5], dmg: 'phys', arc: true },
      traits: [], tags: ['human'], props: { pierce: 0.5 },
      desc: 'Heavy bolts ignore half of armor, but reloading takes two turns.',
      tip: 'Rush it while it reloads.',
    },
    skeleton: {
      name: 'Skeleton', rarity: 'enemy', cost: 2, role: 'melee',
      hp: 28, pow: 14, armor: 0.3, res: 0, block: 0.35, rec: 1, move: 3,
      act: { name: 'Rusty Blade', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: ['undead'], tags: ['undead'],
      desc: 'Bones bound by dark magic. Blades skitter off its ribs. Immune to poison.',
      tip: 'Magic and Blessed weapons break it apart.',
    },
    specter: {
      name: 'Specter', rarity: 'enemy', cost: 3, role: 'skirmisher',
      hp: 26, pow: 11, armor: 0.5, res: -0.25, block: 0, rec: 1, move: 3,
      act: { name: 'Soul Drain', kind: 'strike', range: [1, 2], dmg: 'magic' },
      traits: ['flying', 'undead'], tags: ['spirit', 'undead'], props: { lifesteal: 0.4 },
      desc: 'A restless spirit. 50% armor, but magic hurts it 25% more. Drains life with every touch.',
      tip: 'Bring magic or Blessed weapons. Steel barely touches it.',
    },
    necromancer: {
      name: 'Necromancer', rarity: 'enemy', cost: 4, role: 'caster',
      hp: 30, pow: 13, armor: 0, res: 0.35, block: 0.2, rec: 2, move: 3,
      act: { name: 'Grave Bolt', kind: 'strike', range: [2, 4], dmg: 'magic', arc: true },
      extra: [{ name: 'Raise Dead', kind: 'raise', range: [1, 2], max: 3, uses: 3, cd: 2 }],
      traits: [], tags: ['human', 'caster'],
      desc: 'Raises skeletons from the earth, up to 3 at a time. They crumble when it dies.',
      tip: 'Kill the Necromancer and every skeleton it raised falls apart.',
    },
    colossus: {
      name: 'Bone Colossus', rarity: 'enemy', cost: 6, role: 'tank',
      hp: 92, pow: 22, armor: 0.4, res: -0.2, block: 0, rec: 2, move: 2,
      act: { name: 'Bone Crush', kind: 'quake', range: [1, 1], dmg: 'phys' },
      traits: ['undead', 'big'], tags: ['undead', 'big'],
      desc: 'A towering heap of fused bones. Crushes a foe and everyone beside it.',
      tip: 'Slow and slow to recover, and weak to magic.',
    },
    spider: {
      name: 'Giant Spider', rarity: 'enemy', cost: 3, role: 'skirmisher',
      hp: 36, pow: 14, armor: 0.2, res: 0.1, block: 0.2, rec: 1, move: 4,
      act: { name: 'Venom Fangs', kind: 'strike', range: [1, 1], dmg: 'phys', fx: { poison: 2 }, poisonDmg: 5 },
      extra: [{ name: 'Web Shot', kind: 'strike', range: [2, 4], arc: true, fx: { root: 2 }, uses: 3, cd: 2 }],
      traits: [], tags: ['beast'],
      desc: 'Pins prey in webs from range, then poisons it up close.',
      tip: 'Rooted units can still attack and turn. Keep a Cleric near the front.',
    },
    troll: {
      name: 'Bog Troll', rarity: 'enemy', cost: 5, role: 'tank',
      hp: 80, pow: 20, armor: 0.15, res: -0.1, block: 0.1, rec: 1, move: 3,
      act: { name: 'Club', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: ['trollblood', 'big'], tags: ['beast', 'big'], props: { regen: 5 },
      desc: 'Regen 5, unless magic or fire hurt it since its last turn.',
      tip: 'Burn it. Any magic damage stops its regeneration for a turn.',
    },
    drake: {
      name: 'Fire Drake', rarity: 'enemy', cost: 5, role: 'monster',
      hp: 58, pow: 16, armor: 0.2, res: 0.3, block: 0, rec: 1, move: 4,
      act: { name: 'Flame Spit', kind: 'cone', len: 2, dmg: 'magic', ff: false },
      traits: ['flying'], tags: ['beast'],
      desc: 'A young dragon that spits fire over a short cone.',
      tip: 'Arrows hit it well: only 20% armor.',
    },
    tower: {
      name: 'Arrow Tower', rarity: 'enemy', cost: 0, role: 'ranged',
      hp: 60, pow: 14, armor: 0.4, res: 0.2, block: 0, rec: 1, move: 0,
      act: { name: 'Arrow Slits', kind: 'strike', range: [2, 5], dmg: 'phys', arc: true },
      traits: ['immobile', 'nofacing', 'structure'], tags: ['structure'], material: 'stone',
      desc: 'A stone tower full of archers. You do not need to destroy it to win.',
      tip: 'Stay out of its reach, or bring siege damage.',
    },
    castellan: {
      name: 'Castellan', rarity: 'enemy', cost: 4, role: 'tank',
      hp: 58, pow: 18, armor: 0.35, res: 0.15, block: 0.6, rec: 1, move: 3,
      act: { name: 'Longsword', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: [], tags: ['human'], props: { guard: 0.15 },
      desc: 'Lord of the keep. Adjacent defenders take 15% less damage.',
      tip: 'Strong from the front. Magic and flanks bring it down.',
    },

    // ------------------------------------------------ bosses
    golem_king: {
      name: 'Golem King', rarity: 'boss', cost: 12, role: 'tank', boss: true,
      hp: 135, pow: 22, armor: 0.5, res: -0.15, block: 0, rec: 2, move: 2,
      act: { name: 'Earthshatter', kind: 'quake', range: [1, 1], dmg: 'phys' },
      extra: [{ name: 'Boulder Hurl', kind: 'strike', range: [2, 4], dmg: 'phys', arc: true, mult: 0.8, uses: 3, cd: 2 }],
      traits: ['stoneskin', 'big'], tags: ['construct', 'big'], props: { guard: 0.2 },
      desc: 'Ancient king of the quarry. Hurls boulders, and its basic attack strikes a foe and everyone beside it.',
      tip: 'Half armor but weak to magic. Slay the King to win.',
    },
    warlord: {
      name: 'Grukk the Warlord', rarity: 'boss', cost: 12, role: 'melee', boss: true,
      hp: 150, pow: 23, armor: 0.35, res: 0.1, block: 0.45, rec: 2, move: 3,
      act: { name: 'Brutal Cleave', kind: 'cleave', range: [1, 1], dmg: 'phys' },
      extra: [{ name: 'War Roar', kind: 'drum', radius: 3, noHeal: true, uses: 2, cd: 3 }],
      traits: ['big'], tags: ['greenskin', 'big'],
      desc: 'Warlord of the border tribes. Cleaves everything around him, and his roar whips the horde into a frenzy.',
      tip: 'Do not surround him with weak units. Strike from behind, where he cannot block.',
    },
    witch_queen: {
      name: 'Witch Queen', rarity: 'boss', cost: 13, role: 'caster', boss: true,
      hp: 126, pow: 18, armor: 0.1, res: 0.5, block: 0.3, rec: 2, move: 3,
      act: { name: 'Hexstorm', kind: 'cross', len: 4, dmg: 'magic', ff: false },
      extra: [{ name: 'Hex', kind: 'strike', range: [1, 5], arc: true, fx: { mark: 2 }, uses: 3, cd: 2 }],
      traits: [], tags: ['human', 'caster', 'big'],
      desc: 'Mistress of the Witchwood. Her basic attack lashes enemies in all four directions. 50% magic resistance.',
      tip: 'Stay off her four lines. Physical attackers and flanks bring her down.',
    },
    lich: {
      name: 'The Lich', rarity: 'boss', cost: 13, role: 'caster', boss: true,
      hp: 122, pow: 18, armor: 0.25, res: 0.4, block: 0, rec: 2, move: 3,
      act: { name: 'Frost Bolt', kind: 'strike', range: [1, 4], dmg: 'magic', arc: true, fx: { root: 1 } },
      extra: [{ name: 'Raise Dead', kind: 'raise', range: [1, 2], max: 4, uses: 3, cd: 2 }],
      traits: ['flying', 'undead'], tags: ['undead', 'big'],
      desc: 'A dead sorcerer-king. Its frost roots its victims, and the dead rise at its call.',
      tip: 'Blessed weapons and Smite hurt it badly. Its skeletons crumble when it dies.',
    },
    ashen_tyrant: {
      name: 'Ashen Tyrant', rarity: 'boss', cost: 17, role: 'monster', boss: true,
      hp: 155, pow: 20, armor: 0.35, res: 0.35, block: 0, rec: 2, move: 4,
      act: { name: 'Cinder Breath', kind: 'cone', len: 3, dmg: 'magic', ff: false },
      extra: [{ name: 'Wing Buffet', kind: 'nova', radius: 1, dmg: 'phys', mult: 0.6, fx: { knock: 1 }, uses: 3, cd: 2 }],
      traits: ['flying', 'big'], tags: ['big', 'beast'],
      desc: 'The great dragon that rules the Spire. Its breath spares its own servants.',
      tip: 'Spread out and strike from several sides at once. Dragonslayer weapons help.',
    },
    // The optional final challenge after the campaign is won: not meant to be beaten.
    void_wyrm: {
      name: 'Eclipse Wyrm', rarity: 'boss', cost: 24, role: 'monster', boss: true,
      hp: 250, pow: 21, armor: 0.35, res: 0.35, block: 0, rec: 2, move: 4,
      act: { name: 'Void Breath', kind: 'cone', len: 4, dmg: 'magic', ff: false },
      extra: [
        { name: 'Tail Sweep', kind: 'nova', radius: 1, dmg: 'phys', mult: 0.8, ff: false, fx: { knock: 1 }, uses: 3, cd: 2 },
        { name: 'Eclipse', kind: 'nova', radius: 3, dmg: 'magic', mult: 0.6, ff: false, fx: { weak: 2 }, uses: 2, cd: 4 },
      ],
      traits: ['flying', 'big'], tags: ['big', 'beast'],
      desc: 'A dragon of the dark between the stars. Its breath and its wings spare its own.',
      tip: 'Nobody expects you to win this. Bring everything: magic and steel, healers, and units that can take a breath.',
    },
  };

  // Speed sets a unit's place in its side's turn order: each cycle, faster units go first.
  // Buildings, objects and summoned shrubs take no turns.
  const SPEED = {
    knight: 2, archer: 5, scout: 8, cleric: 1, berserker: 4, skelarcher: 4, pyromancer: 3, assassin: 7,
    mageknight: 3, golem: 1, beastrider: 6, furgon: 3, wisp: 6, enchantress: 4, witch: 3, lightning: 3,
    dragon: 5, trebuchet: 1, orc: 3, brute: 2, goblin_archer: 6, sapper: 7, shaman: 1, warg: 8, wolf: 7,
    cutthroat: 7, crossbow: 3, skeleton: 3, specter: 6, necromancer: 3, colossus: 1, spider: 6, troll: 2,
    drake: 5, tower: 2, castellan: 2, golem_king: 1, warlord: 3, witch_queen: 4, lich: 3, ashen_tyrant: 4, void_wyrm: 4,
  };
  for (const [k, T] of Object.entries(UNITS)) T.spd = SPEED[k] || 0;

  const RECRUITABLE = Object.keys(UNITS).filter((k) => ['common', 'uncommon', 'rare', 'legendary'].includes(UNITS[k].rarity));

  // Talents: a class's passives that cost Supply. They are not level picks: you find them
  // in shops and battle spoils and slot them into a unit of that class, one slot per level.
  // The level picks keep the free option and the active abilities. `tier` is the level list
  // a talent came from; the Level 2 ones are the stronger, rarer finds.
  const TALENTS = {};
  for (const [type, T] of Object.entries(UNITS)) {
    if (!T.abilities) continue;
    for (const tier of [1, 2]) {
      for (const id of T.abilities[tier]) {
        const ab = A[id];
        if (ab.cost > 0 && !ab.mod.active) TALENTS[id] = Object.assign({}, ab, { id, cls: type, tier });
      }
    }
  }

  // Which skill and gear families a unit type can use.
  function unitTags(typeId) {
    const T = UNITS[typeId];
    const a = T.act;
    const tags = new Set();
    if (a.dmg) tags.add('damage');
    if (a.dmg === 'phys') tags.add('phys');
    if (a.dmg === 'magic' || a.kind === 'pray' || (a.fx && a.fx.poison)) tags.add('magic');
    if (a.range && a.range[1] >= 2) tags.add('ranged');
    if (T.move > 0) tags.add('mobile');
    if (!T.traits.includes('nofacing')) tags.add('facing');
    if (T.rec >= 2) tags.add('slow');
    if (a.kind !== 'none') tags.add('active');
    // An area attack, its own or from one of its abilities: Disciplined has work to do.
    const AREA = ['cleave', 'quake', 'cross', 'nova', 'blast', 'line', 'cone', 'leap'];
    const areaAct = (x) => x && x.dmg && AREA.includes(x.kind);
    const abil = T.abilities ? [...T.abilities[1], ...T.abilities[2]].map((id) => A[id] && A[id].mod.active) : [];
    if (areaAct(a) || abil.some(areaAct)) tags.add('area');
    return tags;
  }

  // ---------------------------------------------------------------- skills and gear
  // Both are owned items: each copy can be slotted into one unit at a time.

  const SKILLS = {
    vampiric: { name: 'Vampiric', cost: 2, desc: 'Heals for 30% of the damage it deals.', req: 'damage', mod: { props: { lifesteal: 0.3 } } },
    disciplined: { name: 'Disciplined', cost: 1, desc: 'Its area attacks and abilities never hit allies.', req: 'area', mod: { traits: ['precise'] } },
    swift: { name: 'Swift', cost: 2, desc: '+1 Move.', req: 'mobile', mod: { stat: { move: 1 } } },
    hardened: { name: 'Hardened', cost: 1, desc: '+10% armor.', mod: { stat: { armor: 0.1 } } },
    warded: { name: 'Warded', cost: 1, desc: '+15% magic resistance.', mod: { stat: { res: 0.15 } } },
    sentinel: { name: 'Sentinel', cost: 1, desc: '+12% block.', req: 'facing', mod: { stat: { block: 0.12 } } },
    eagle_eye: { name: 'Eagle Eye', cost: 2, desc: '+1 maximum range.', req: 'ranged', mod: { stat: { range: 1 } } },
    brutal: { name: 'Brutal', cost: 2, desc: '+15% damage.', req: 'damage', mod: { props: { dmgMult: 0.15 } } },
    executioner: { name: 'Executioner', cost: 1, desc: '+40% damage to targets below half HP.', req: 'damage', mod: { props: { execMult: 0.4 } } },
    thick_hide: { name: 'Thick Hide', cost: 1, desc: '+15 max HP.', mod: { stat: { hp: 15 } } },
    second_wind: { name: 'Second Wind', cost: 2, desc: 'Once per battle, survives a fatal blow with 1 HP.', mod: { traits: ['secondwind'] } },
    bloodlust: { name: 'Bloodlust', cost: 2, desc: 'Slaying an enemy resets its cooldown: it is ready again next turn.', req: 'damage', mod: { traits: ['bloodlust'] } },
    flanker: { name: 'Flanker', cost: 1, desc: '+30% damage from the side or from behind.', req: 'phys', mod: { props: { flankMult: 0.3 } } },
    unshakable: { name: 'Unshakable', cost: 1, desc: 'Immune to poison, paralysis, roots and knockback.', mod: { traits: ['steadfast', 'poisonproof'] } },
    guardian: { name: 'Guardian', cost: 1, desc: 'Adjacent allies take 15% less damage.', mod: { props: { guard: 0.15 } } },
    retaliate: { name: 'Retaliate', cost: 2, desc: 'When struck in melee and still standing, strikes back for half damage.', req: 'damage', mod: { traits: ['retaliate'] } },
    quickened: { name: 'Quickened', cost: 3, desc: 'Cooldown 1 turn shorter.', req: 'slow', mod: { stat: { rec: -1 } } },
    martyr: { name: 'Martyr', cost: 1, desc: 'When it falls, heals allies within 2 tiles for 20.', mod: { traits: ['martyr'] } },
    arcane_focus: { name: 'Arcane Focus', cost: 2, desc: '+20% magic damage, healing and poison.', req: 'magic', mod: { props: { magicMult: 0.2 } } },
    demolisher: { name: 'Demolisher', cost: 1, desc: 'Double damage against buildings and wagons.', req: 'damage', mod: { props: { vs: { structure: 1 } } } },
  };

  const GEAR = {
    flame_brand: { name: 'Flame Brand', cost: 2, desc: 'Hits also set the target burning: 4 damage a turn for 2 turns.', req: 'damage', mod: { onHit: { burn: [2, 4] } } },
    venom_edge: { name: 'Venom Edge', cost: 2, desc: 'Hits also poison the target for 2 turns: 4 damage a turn, and no healing.', req: 'damage', mod: { onHit: { poison: [2, 4] } } },
    blessed_blade: { name: 'Blessed Blade', cost: 1, desc: '+50% damage against undead and spirits.', req: 'damage', mod: { props: { vs: { undead: 0.5, spirit: 0.5 } } } },
    orcbane: { name: 'Orcbane Axe', cost: 1, desc: '+40% damage against orcs and goblins.', req: 'damage', mod: { props: { vs: { greenskin: 0.4 } } } },
    dragonslayer: { name: 'Dragonslayer Spear', cost: 2, desc: '+50% damage against huge foes: dragons, trolls, brutes and bosses.', req: 'damage', mod: { props: { vs: { big: 0.5 } } } },
    siege_hammer: { name: 'Siege Hammer', cost: 1, desc: 'Triple damage against buildings and wagons.', req: 'damage', mod: { props: { vs: { structure: 2 } } } },
    war_pick: { name: 'War Pick', cost: 2, desc: 'Physical attacks ignore half of armor.', req: 'phys', mod: { props: { pierce: 0.5 } } },
    healing_charm: { name: 'Healing Charm', cost: 1, desc: '+3 Regen: heals 3 HP each time it takes a turn.', mod: { props: { regen: 3 } } },
    thorn_ring: { name: 'Thorn Ring', cost: 1, desc: 'Enemies that strike it in melee take 6 damage.', mod: { props: { thorns: 6 } } },
    iron_will: { name: 'Iron Will', cost: 1, desc: 'Immune to paralysis, roots and knockback.', mod: { traits: ['steadfast'] } },
    focus_amulet: { name: 'Focus Amulet', cost: 2, desc: '+15% magic damage and healing.', req: 'magic', mod: { props: { magicMult: 0.15 } } },
    tower_shield: { name: 'Tower Shield', cost: 1, desc: '+15% block, but -1 Move.', req: 'facing', mod: { stat: { block: 0.15, move: -1 } } },
    plate_armor: { name: 'Plate Armor', cost: 2, desc: '+15% armor.', mod: { stat: { armor: 0.15 } } },
    silk_mantle: { name: 'Silk Mantle', cost: 1, desc: '+15% magic resistance.', mod: { stat: { res: 0.15 } } },
    swift_boots: { name: 'Swift Boots', cost: 2, desc: '+1 Move.', req: 'mobile', mod: { stat: { move: 1 } } },
    giant_belt: { name: "Giant's Belt", cost: 1, desc: '+20 max HP.', mod: { stat: { hp: 20 } } },
    smoke_pouch: { name: 'Smoke Pouch', cost: 1, desc: 'Active, 1 use: smoke over its own 5-tile area for 2 turns. Units inside cannot be targeted from more than 1 tile away.',
      mod: { active: { name: 'Smoke Pouch', kind: 'hazard', hz: 'smoke', range: [0, 0], pattern: 'plus', turns: 2, uses: 1 } } },
    fire_flask: { name: 'Fire Flask', cost: 1, desc: 'Active, 1 use: throw a flask 2 or 3 tiles: 14 magic damage in a 5-tile burst that also burns enemies.',
      mod: { active: { name: 'Fire Flask', kind: 'blast', range: [2, 3], pattern: 'plus', dmg: 'magic', fixed: 14, arc: true, ff: true, fx: { burn: [2, 4] }, uses: 1 } } },
    healing_draught: { name: 'Healing Draught', cost: 1, desc: 'Active, 1 use: heal itself or an adjacent ally for 20 and cure poison and burns.',
      mod: { active: { name: 'Healing Draught', kind: 'heal', range: [0, 1], fixed: 20, cure: true, uses: 1 } } },
    blasting_charge: { name: 'Blasting Charge', cost: 1, desc: 'Active, 1 use: blow up an adjacent target for 20 damage, triple against buildings, ignoring half of armor.',
      mod: { active: { name: 'Blasting Charge', kind: 'strike', range: [1, 1], dmg: 'phys', fixed: 20, pierce: 0.5, vs: { structure: 2 }, uses: 1 } } },
  };

  // Enchantments are bound to one unit forever and raise its Supply cost.
  const ENCHANTS = {
    stormcaller: { name: 'Stormcaller', surcharge: 2, desc: 'At the start of your turn, lightning strikes the nearest enemy within 3 tiles for 5 magic damage.', mod: { traits: ['stormcaller'] } },
    bloodforged: { name: 'Bloodforged', surcharge: 2, desc: '+10 max HP. Heals for 25% of the damage it deals.', req: 'damage', mod: { stat: { hp: 10 }, props: { lifesteal: 0.25 } } },
    runeward: { name: 'Runeward', surcharge: 1, desc: '+20% magic resistance. Immune to paralysis.', mod: { stat: { res: 0.2 }, traits: ['paraproof'] } },
    phoenix_soul: { name: 'Phoenix Soul', surcharge: 3, desc: 'The first time it falls in a battle, it rises again with half HP.', mod: { traits: ['phoenix'] } },
    spellblade: { name: 'Spellblade', surcharge: 2, desc: 'Its attacks also deal 6 bonus magic damage.', req: 'damage', mod: { props: { bonusMagic: 6 } } },
    frostbound: { name: 'Frostbound', surcharge: 2, desc: 'Hits root the target for 1 turn. +10% armor.', req: 'damage', mod: { onHit: { root: 1 }, stat: { armor: 0.1 } } },
    giantblood: { name: 'Giantblood', surcharge: 2, desc: '+30% max HP and +10% damage.', mod: { stat: { hpPct: 0.3 }, props: { dmgMult: 0.1 } } },
    windwalker: { name: 'Windwalker', surcharge: 2, desc: '+1 Move, and it flies over units, water and rocks.', req: 'mobile', mod: { stat: { move: 1 }, traits: ['flying'] } },
    holy_aegis: { name: 'Holy Aegis', surcharge: 2, desc: 'Adjacent allies take 15% less damage. Immune to poison.', mod: { props: { guard: 0.15 }, traits: ['poisonproof'] } },
    quicksilver: { name: 'Quicksilver', surcharge: 3, desc: 'Cooldown 1 turn shorter.', req: 'recovers', mod: { stat: { rec: -1 } } },
    midas: { name: 'Midas Touch', surcharge: 1, desc: 'Every enemy it slays earns 6 gold.', req: 'damage', mod: { traits: ['midas'] } },
    thunderstep: { name: 'Thunderstep', surcharge: 2, desc: 'When it finishes a move, enemies next to it take 6 magic damage.', req: 'mobile', mod: { traits: ['thunderstep'] } },
  };

  function itemDef(kind, id) {
    return kind === 'skill' ? SKILLS[id] : kind === 'gear' ? GEAR[id] : kind === 'talent' ? TALENTS[id] : null;
  }

  // Can this unit type use this skill, gear or enchantment?
  function eligible(typeId, def) {
    if (!def) return false;
    const T = UNITS[typeId];
    if (!T || T.traits.includes('summon')) return false;
    if (def.cls) return def.cls === typeId;
    if (!def.req) return true;
    if (def.req === 'recovers') return T.rec >= 1;
    return unitTags(typeId).has(def.req);
  }

  // tier: common | uncommon | rare | boss | event
  const RELICS = {
    war_horn: { name: 'War Horn', tier: 'common', desc: '+1 Supply in every battle.' },
    whetstone: { name: 'Whetstone', tier: 'common', desc: 'Physical attacks deal +2 damage.' },
    steel_bucklers: { name: 'Steel Bucklers', tier: 'common', desc: 'Your units have +8% block.' },
    iron_plating: { name: 'Iron Plating', tier: 'common', desc: 'Your units have +6% armor.' },
    coin_purse: { name: "Merchant's Purse", tier: 'common', desc: 'Gain 12 extra gold after each victory.' },
    healing_salve: { name: 'Healing Salve', tier: 'common', desc: 'Your units that have Regen of their own (a Furgon, Living Moss, a Healing Charm) regenerate 2 more.' },
    scout_map: { name: "Cartographer's Map", tier: 'common', desc: 'Your deployment zone reaches one row further forward.' },
    drill_manual: { name: 'Drill Manual', tier: 'common', desc: 'Gain 25% more XP from battles.' },
    pathfinder: { name: 'Pathfinder Boots', tier: 'common', desc: 'Units with 3 Move or less gain +1 Move.' },
    oak_charm: { name: 'Oaken Charm', tier: 'common', desc: 'Your units have +8 max HP.' },
    sappers_kit: { name: "Sapper's Kit", tier: 'common', desc: 'Your units deal 50% more damage to buildings and wagons.' },
    mana_crystal: { name: 'Mana Crystal', tier: 'uncommon', desc: 'Spellcasters (Cooldown 2 or more) cool down 1 turn faster.' },
    bloodstone: { name: 'Bloodstone', tier: 'uncommon', desc: 'Your units heal for 20% of the damage they deal.' },
    thorned_mail: { name: 'Thorned Mail', tier: 'uncommon', desc: 'Enemies that strike your units in melee take 5 damage.' },
    headsman_axe: { name: "Headsman's Axe", tier: 'uncommon', desc: '+30% damage against enemies below half HP.' },
    phoenix_feather: { name: 'Phoenix Feather', tier: 'uncommon', desc: 'The first of your units to fall in each battle rises again with half HP.' },
    guild_seal: { name: 'Guild Seal', tier: 'uncommon', desc: 'Shop prices are 25% lower.' },
    legion_banner: { name: 'Banner of the Legion', tier: 'uncommon', desc: '+2 Supply in every battle.' },
    sands_of_haste: { name: 'Sands of Haste', tier: 'uncommon', desc: 'Enemy spellcasters (Cooldown 2 or more) start each battle cooling down and sit out the first enemy turn.' },
    recruiters_bell: { name: "Recruiter's Bell", tier: 'uncommon', desc: 'Level 1 units cost 1 less Supply, never below 2.' },
    old_crown: { name: 'Crown of the Old King', tier: 'rare', desc: 'Your units deal 15% more damage.' },
    shadow_cloak: { name: 'Shadow Cloak', tier: 'rare', desc: 'Your attacks from behind deal 40% more damage.' },
    aegis: { name: 'Aegis of Dawn', tier: 'rare', desc: 'Attacks against the sides of your units face full block.' },
    warlord_helm: { name: "Warlord's Helm", tier: 'rare', desc: 'A unit that slays an enemy resets its cooldown: it is ready again next turn.' },
    alchemist_stone: { name: "Alchemist's Stone", tier: 'rare', desc: 'Unspent Supply earns triple gold.' },
    dragon_scale: { name: 'Dragon Scale', tier: 'rare', desc: 'Your units have +15% magic resistance.' },
    tyrant_heart: { name: 'Heart of the Tyrant', tier: 'boss', desc: '+3 Supply in every battle.' },
    titan_gauntlet: { name: "Titan's Gauntlet", tier: 'boss', desc: 'Your units deal 25% more damage, but you have 1 less Supply.' },
    eternal_flame: { name: 'Eternal Flame', tier: 'boss', desc: "Each unit's first action in a battle has no cooldown: it is ready again next turn." },
    kings_ransom: { name: "King's Ransom", tier: 'boss', desc: 'Gain 150 gold now and 20 extra gold after each victory.' },
    crown_command: { name: 'Crown of Command', tier: 'boss', desc: '+2 Supply in every battle, and 25% more XP.' },
    sacred_chalice: { name: 'Sacred Chalice', tier: 'boss', desc: 'Your units have +2 Regen.' },
    cursed_blade: { name: 'Bloodthirst Blade', tier: 'event', desc: 'Your units deal 20% more damage and take 10% more damage.' },
  };

  const WARBANDS = [
    {
      id: 'vanguard', name: 'Iron Vanguard',
      desc: 'Shields and faith. Sturdy and forgiving.',
      units: ['knight', 'knight', 'archer', 'cleric', 'scout'], relic: 'steel_bucklers', gold: 60,
      items: [['skill', 'thick_hide'], ['gear', 'tower_shield']],
    },
    {
      id: 'ember', name: 'Ember Circle',
      desc: 'Fire and runes. Magic burns through armor; the Mage Knight holds the line.',
      units: ['pyromancer', 'mageknight', 'archer', 'scout', 'knight'], relic: 'iron_plating', gold: 50,
      items: [['skill', 'arcane_focus'], ['gear', 'silk_mantle']],
    },
    {
      id: 'shadow', name: 'Shadow Syndicate',
      desc: 'Flankers and knives. Rewards careful positioning.',
      units: ['assassin', 'scout', 'scout', 'archer', 'berserker'], relic: 'whetstone', gold: 70,
      items: [['skill', 'flanker'], ['gear', 'venom_edge']],
    },
    {
      id: 'grove', name: 'Wildgrove Pact',
      desc: 'Beasts and brambles. Wall off the field, then charge.',
      units: ['beastrider', 'furgon', 'archer', 'cleric', 'berserker'], relic: 'healing_salve', gold: 55,
      items: [['skill', 'guardian'], ['gear', 'healing_charm']],
    },
    {
      id: 'grave', name: 'Gravewatch Order',
      desc: 'Bone archers and dark magic. Cheap bodies, so you can field more of them.',
      units: ['skelarcher', 'skelarcher', 'knight', 'witch', 'cleric'], relic: 'oak_charm', gold: 55,
      items: [['skill', 'sentinel'], ['gear', 'blessed_blade']],
    },
  ];

  // mult scales enemy armies; temp is how loosely the enemy commander plays.
  const DIFFICULTIES = [
    { id: 'squire', name: 'Squire', desc: 'Smaller enemy armies. A gentle introduction.', mult: 0.85, temp: 2.5 },
    { id: 'knight', name: 'Knight', desc: 'The intended challenge.', mult: 1.0, temp: 1.2 },
    { id: 'warlord', name: 'Warlord', desc: 'Larger armies and sharper enemy commanders.', mult: 1.1, temp: 0.5 },
  ];

  const ACTS = [
    null,
    { name: 'The Borderlands', short: 'Act I', palette: 'grass', bosses: ['golem_king', 'warlord'] },
    { name: 'The Witchwood', short: 'Act II', palette: 'swamp', bosses: ['witch_queen', 'lich'] },
    { name: "The Dragon's Spire", short: 'Act III', palette: 'ember', bosses: ['ashen_tyrant'] },
  ];

  // Enemy warbands. `units` is the core; the campaign scales it to the floor's Supply.
  // layout: siege (walls, a gate and towers) | convoy (loot wagons fleeing) | camp (powder kegs)
  // lv: optional fixed levels per unit.
  const ENCOUNTERS = {
    1: {
      normal: [
        { name: 'Bandit Ambush', units: ['cutthroat', 'cutthroat', 'crossbow', 'scout'], spawner: 'war_tent', stance: 'aggressive', pool: ['cutthroat', 'crossbow', 'scout'] },
        { name: 'Goblin Raiders', units: ['goblin_archer', 'goblin_archer', 'sapper', 'orc'], spawner: 'war_tent', stance: 'aggressive', pool: ['goblin_archer', 'sapper', 'orc'] },
        { name: 'Warg Riders', units: ['warg', 'warg', 'orc', 'goblin_archer'], spawner: 'den', stance: 'aggressive', pool: ['warg', 'goblin_archer'] },
        { name: "Smugglers' Convoy", units: ['cutthroat', 'crossbow', 'scout'], layout: 'convoy', spawner: 'war_tent', stance: 'balanced', pool: ['cutthroat', 'scout'] },
        { name: 'Border Keep', units: ['knight', 'archer', 'castellan'], layout: 'siege', spawner: 'guardhouse', stance: 'defensive', pool: ['archer', 'knight'] },
        { name: 'Mercenary Company', units: ['knight', 'archer', 'cleric', 'scout'], spawner: 'war_tent', stance: 'balanced', pool: ['knight', 'archer', 'scout'] },
        { name: 'Orc Warband', units: ['orc', 'orc', 'shaman', 'goblin_archer'], spawner: 'war_tent', stance: 'balanced', pool: ['orc', 'goblin_archer'] },
      ],
      elite: [
        { name: "Warchief's Guard", units: ['brute', 'brute', 'shaman', 'orc'], lv: [2, 1, 1, 2], spawner: 'war_tent', stance: 'balanced', pool: ['orc'] },
        { name: 'Goblin Powder Camp', units: ['sapper', 'sapper', 'goblin_archer', 'goblin_archer', 'orc'], layout: 'camp', spawner: 'war_tent', stance: 'aggressive', pool: ['sapper', 'goblin_archer'] },
        { name: 'Knights of the March', units: ['knight', 'knight', 'archer', 'cleric'], lv: [2, 2, 1, 1], spawner: 'war_tent', stance: 'balanced', pool: ['knight', 'archer'] },
      ],
      boss: {
        golem_king: { name: 'The Golem King', units: ['golem_king', 'knight', 'archer', 'archer', 'cleric'], stance: 'balanced', pool: ['knight', 'archer'] },
        warlord: { name: 'Grukk the Warlord', units: ['warlord', 'orc', 'shaman', 'goblin_archer', 'sapper'], stance: 'aggressive', pool: ['orc', 'goblin_archer', 'sapper'] },
      },
    },
    2: {
      normal: [
        { name: 'The Restless Dead', units: ['skeleton', 'skeleton', 'skelarcher', 'specter'], spawner: 'crypt', stance: 'aggressive', pool: ['skeleton', 'skelarcher'] },
        { name: "Necromancer's Circle", units: ['necromancer', 'skeleton', 'skeleton', 'specter'], spawner: 'crypt', stance: 'balanced', pool: ['skeleton', 'skelarcher'] },
        { name: 'Spider Nest', units: ['spider', 'spider', 'wisp', 'wolf'], spawner: 'den', stance: 'aggressive', pool: ['spider', 'wolf'] },
        { name: 'Troll Bridge', units: ['troll', 'goblin_archer', 'goblin_archer', 'wolf'], spawner: 'den', stance: 'balanced', pool: ['goblin_archer', 'wolf'] },
        { name: 'Witch Circle', units: ['witch', 'enchantress', 'knight', 'wisp'], spawner: 'portal', stance: 'balanced', pool: ['knight', 'wisp'] },
        { name: 'Wolf Pack', units: ['wolf', 'wolf', 'wolf', 'beastrider'], spawner: 'den', stance: 'aggressive', pool: ['wolf', 'beastrider'] },
        { name: 'Bog Raiders', units: ['berserker', 'berserker', 'wisp', 'cutthroat'], layout: 'convoy', spawner: 'portal', stance: 'aggressive', pool: ['berserker', 'cutthroat'] },
      ],
      elite: [
        { name: 'The Coven', units: ['witch', 'witch', 'barrier', 'knight', 'knight'], spawner: 'portal', stance: 'balanced', pool: ['knight'] },
        { name: 'Bone Colossus', units: ['colossus', 'necromancer', 'skeleton', 'skelarcher'], spawner: 'crypt', stance: 'balanced', pool: ['skeleton', 'skelarcher'] },
        { name: 'Troll Kin', units: ['troll', 'troll', 'spider', 'shaman'], spawner: 'den', stance: 'aggressive', pool: ['spider', 'wolf'] },
      ],
      boss: {
        witch_queen: { name: 'The Witch Queen', units: ['witch_queen', 'enchantress', 'wisp', 'knight', 'knight', 'witch'], stance: 'balanced', pool: ['knight', 'wisp'] },
        lich: { name: 'The Lich', units: ['lich', 'specter', 'skeleton', 'skeleton', 'skelarcher', 'necromancer'], stance: 'balanced', pool: ['skeleton', 'skelarcher'] },
      },
    },
    3: {
      normal: [
        { name: 'Spire Garrison', units: ['castellan', 'knight', 'knight', 'archer'], layout: 'siege', spawner: 'guardhouse', stance: 'defensive', pool: ['knight', 'archer'] },
        { name: 'Cult of Flame', units: ['pyromancer', 'pyromancer', 'enchantress', 'golem'], spawner: 'portal', stance: 'balanced', pool: ['golem', 'knight'] },
        { name: 'Drake Keepers', units: ['drake', 'drake', 'knight', 'cleric'], spawner: 'den', stance: 'balanced', pool: ['knight', 'archer'] },
        { name: 'Iron Legion', units: ['knight', 'knight', 'mageknight', 'archer', 'archer', 'cleric'], spawner: 'guardhouse', stance: 'defensive', pool: ['knight', 'archer'] },
        { name: 'Orc Vanguard', units: ['brute', 'orc', 'orc', 'shaman', 'warg'], lv: [1, 2, 2, 1, 1], spawner: 'war_tent', stance: 'aggressive', pool: ['orc', 'warg'] },
        { name: 'Shadow Strike', units: ['assassin', 'assassin', 'enchantress', 'scout', 'cutthroat'], spawner: 'portal', stance: 'aggressive', pool: ['assassin', 'scout'] },
        { name: 'Storm Battery', units: ['lightning', 'barrier', 'pyromancer', 'archer', 'archer'], layout: 'camp', spawner: 'guardhouse', stance: 'defensive', pool: ['archer', 'knight'] },
      ],
      elite: [
        { name: 'Dragon Brood', units: ['dragon', 'drake', 'cleric', 'knight'], spawner: 'den', stance: 'aggressive', pool: ['knight'] },
        { name: 'Champions of the Spire', units: ['knight', 'assassin', 'pyromancer', 'cleric', 'archer'], lv: [3, 3, 2, 2, 1], spawner: 'guardhouse', stance: 'balanced', pool: ['knight', 'archer'] },
        { name: 'The Inner Keep', units: ['castellan', 'mageknight', 'mageknight', 'crossbow', 'cleric'], lv: [3, 1, 1, 1, 1], layout: 'siege', spawner: 'guardhouse', stance: 'defensive', pool: ['crossbow', 'knight'] },
      ],
      boss: {
        ashen_tyrant: { name: 'The Ashen Tyrant', units: ['ashen_tyrant', 'pyromancer', 'knight', 'knight', 'drake', 'cleric'], stance: 'balanced', pool: ['knight', 'archer'] },
      },
    },
    // The optional final challenge: the Eclipse Wyrm and the best of the Spire.
    mega: { name: 'The Eclipse Wyrm', units: ['void_wyrm', 'drake', 'drake', 'lich', 'mageknight', 'knight', 'cleric', 'witch'], lv: [3, 2, 2, 2, 3, 3, 3, 2], stance: 'aggressive', pool: ['knight', 'crossbow', 'drake'] },
  };

  const NAMES = [
    'Aldric', 'Bryn', 'Cedric', 'Dorian', 'Elric', 'Fenna', 'Garrick', 'Hale', 'Isolde', 'Jory',
    'Kael', 'Lys', 'Marek', 'Nell', 'Osric', 'Perrin', 'Quill', 'Rowan', 'Sable', 'Tamsin',
    'Ulric', 'Vesna', 'Wren', 'Yara', 'Bram', 'Corin', 'Dara', 'Edda', 'Finn', 'Gwen',
    'Hollis', 'Ivo', 'Jessa', 'Kestrel', 'Leof', 'Mira', 'Niall', 'Odo', 'Pell', 'Rhosyn',
    'Sorrel', 'Teague', 'Una', 'Varek', 'Wynn', 'Ash', 'Briar', 'Cass', 'Dunstan', 'Ebba',
    'Faro', 'Gilda', 'Hew', 'Ilse', 'Jarek', 'Kit', 'Lorne', 'Maud', 'Nyle', 'Orla',
  ];

  AG.Data = {
    DIRS, MAX_LEVEL, LEVEL_COST, LEVEL_HP, LEVEL_POW, SKILL_SLOTS, GEAR_SLOTS, TALENT_SLOTS, RES_CAP, COMMAND,
    ABILITIES: A, TALENTS, MASTERY, UNITS, RECRUITABLE, SKILLS, GEAR, ENCHANTS, RELICS, WARBANDS,
    DIFFICULTIES, ACTS, ENCOUNTERS, NAMES, unitTags, itemDef, eligible,
  };
})(typeof window !== 'undefined' ? window : globalThis);
