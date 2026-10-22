// Static game data: units, talents, relics, warbands, acts and encounters.
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

  const RANK_MULT = [1, 1, 1.2, 1.4]; // index by rank (1..3)

  // kind: strike | cleave | quake | blast | line | cone | cross | nova | pray | grow | none
  const UNITS = {
    knight: {
      name: 'Knight', rarity: 'common', cost: 3, role: 'tank',
      hp: 52, pow: 18, armor: 0.25, block: 0.7, rec: 1, move: 3,
      act: { name: 'Sword Strike', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: [],
      star3: { name: 'Shield Wall', desc: 'Attacks from the side face full block instead of half.' },
      desc: 'Plate-clad swordsman. Turns aside most blows that come from the front.',
      tip: 'Magic ignores armor and cannot be blocked. Flank Knights or strike from behind.',
    },
    archer: {
      name: 'Archer', rarity: 'common', cost: 3, role: 'ranged',
      hp: 34, pow: 16, armor: 0.1, block: 0.3, rec: 1, move: 3,
      act: { name: 'Longbow', kind: 'strike', range: [2, 5], dmg: 'phys', arc: true },
      traits: [],
      star3: { name: 'Bodkin Arrows', desc: "Arrows ignore half of the target's armor." },
      desc: 'Shoots up to 5 tiles over the heads of other units. Cannot shoot an adjacent foe.',
      tip: "Fragile up close. Rush it with fast units, or soak arrows on a Knight's front block.",
    },
    scout: {
      name: 'Scout', rarity: 'common', cost: 2, role: 'skirmisher',
      hp: 28, pow: 11, armor: 0.05, block: 0.5, rec: 0, move: 5,
      act: { name: 'Throwing Knives', kind: 'strike', range: [1, 3], dmg: 'phys', arc: true },
      traits: [],
      star3: { name: 'Ambusher', desc: '+50% damage on attacks from behind.' },
      desc: 'Fast and cheap. Recover 0: it can act every single turn.',
      tip: 'Its light hits glance off armor. Keep your backs covered against its flanking.',
    },
    cleric: {
      name: 'Cleric', rarity: 'common', cost: 3, role: 'support',
      hp: 28, pow: 12, armor: 0, block: 0, rec: 2, move: 3,
      act: { name: 'Prayer', kind: 'pray', radius: 3 },
      traits: [],
      star3: { name: 'Purify', desc: 'Prayer also cures poison and paralysis, and reaches 4 tiles.' },
      desc: 'Heals every ally within 3 tiles, itself included. Cannot attack.',
      tip: 'Poisoned units cannot be healed. Kill the Cleric first, or burn its huddle.',
    },
    berserker: {
      name: 'Berserker', rarity: 'common', cost: 3, role: 'melee',
      hp: 44, pow: 19, armor: 0, block: 0.1, rec: 1, move: 3,
      act: { name: 'Cleave', kind: 'cleave', range: [1, 1], dmg: 'phys' },
      traits: ['rage'],
      star3: { name: 'Bloodrage', desc: 'Heals 5 HP for every enemy its Cleave strikes.' },
      desc: 'Cleave strikes every adjacent enemy at once. Hits 30% harder below half HP.',
      tip: 'No armor and almost no block. Arrows and spells cut it down before it arrives.',
    },
    pyromancer: {
      name: 'Pyromancer', rarity: 'uncommon', cost: 4, role: 'caster',
      hp: 28, pow: 16, armor: 0, block: 0.2, rec: 2, move: 3,
      act: { name: 'Fireball', kind: 'blast', range: [2, 4], dmg: 'magic', pattern: 'plus', ff: true, arc: true },
      traits: [],
      star3: { name: 'Inferno', desc: 'Fireball scorches a full 3x3 area.' },
      desc: 'Fireball bursts over 5 tiles. Magic ignores armor and block, and it burns allies too.',
      tip: 'Spread out against fire. A Barrier Ward halves magic damage around it.',
    },
    assassin: {
      name: 'Assassin', rarity: 'uncommon', cost: 3, role: 'skirmisher',
      hp: 32, pow: 20, armor: 0.1, block: 0.6, rec: 1, move: 4,
      act: { name: 'Backstab', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: ['backstab', 'shadowstep'],
      star3: { name: 'Deathmark', desc: 'Attacks from behind deal double damage.' },
      desc: 'Slips through enemy lines and deals +50% damage from behind.',
      tip: 'Turn your fragile units to face it. Shrubs, Knights and Lightning Wards stop it cold.',
    },
    golem: {
      name: 'Stone Golem', rarity: 'uncommon', cost: 4, role: 'tank',
      hp: 74, pow: 18, armor: 0.35, block: 0, rec: 1, move: 2,
      act: { name: 'Stone Fist', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: ['stoneskin', 'guardian'],
      star3: { name: 'Bulwark', desc: 'Its Guardian protection rises to 35%.' },
      desc: 'Slow living rock. Immune to poison and paralysis. Adjacent allies take 20% less damage.',
      tip: 'Heavy armor, no block, moves 2. Kite it with range or melt it with magic.',
    },
    beastrider: {
      name: 'Beast Rider', rarity: 'uncommon', cost: 4, role: 'melee',
      hp: 46, pow: 19, armor: 0.15, block: 0.35, rec: 1, move: 5,
      act: { name: 'Lance', kind: 'strike', range: [1, 1], dmg: 'phys' },
      traits: ['charge'],
      star3: { name: 'Trample', desc: 'Its Charge bonus rises to +60%.' },
      desc: 'Rides a war-wolf. Charge: +30% damage after moving 3 or more tiles before striking.',
      tip: "A Knight's front block blunts its charge. Box it in with shrubs and wards.",
    },
    furgon: {
      name: 'Furgon', rarity: 'uncommon', cost: 3, role: 'support',
      hp: 38, pow: 0, armor: 0.1, block: 0.3, rec: 1, move: 3,
      act: { name: 'Grow Shrub', kind: 'grow', range: [1, 3] },
      traits: ['regrowth'],
      star3: { name: 'Thornwall', desc: 'Shrubs have double HP and prick melee attackers for 6.' },
      desc: 'Forest spirit. Raises a shrub that blocks movement and lines (3 at a time). Regains 4 HP each turn.',
      tip: 'Shrubs can be cut down, and flyers and arcing shots ignore them.',
    },
    wisp: {
      name: 'Poison Wisp', rarity: 'uncommon', cost: 3, role: 'caster',
      hp: 24, pow: 6, armor: 0, block: 0.4, rec: 1, move: 4,
      act: { name: 'Miasma', kind: 'nova', radius: 2, fx: { poison: 3 } },
      traits: ['flying'],
      star3: { name: 'Plague', desc: 'Miasma reaches 3 tiles.' },
      desc: 'Floats over anything. Poisons enemies within 2 tiles for 3 turns. Poisoned units cannot heal.',
      tip: 'Only 24 HP. Golems, and units near a Barrier Ward, are immune to poison.',
    },
    barrier: {
      name: 'Barrier Ward', rarity: 'uncommon', cost: 3, role: 'ward',
      hp: 40, pow: 0, armor: 0.2, block: 0, rec: 0, move: 0,
      act: { name: 'Barrier Aura', kind: 'none' },
      traits: ['immobile', 'aura_barrier', 'nofacing'],
      star3: { name: 'Aegis Field', desc: 'Its aura reaches 3 tiles and also softens physical blows by 15%.' },
      desc: 'Rooted crystal. Allies within 2 tiles take half magic damage and are immune to poison and paralysis.',
      tip: 'It cannot move or fight. Bring physical attackers, or draw foes out of its reach.',
    },
    enchantress: {
      name: 'Enchantress', rarity: 'rare', cost: 4, role: 'caster',
      hp: 30, pow: 10, armor: 0, block: 0.25, rec: 2, move: 3,
      act: { name: 'Mesmerize', kind: 'blast', range: [2, 4], dmg: 'magic', pattern: 'plus', ff: false, arc: true, fx: { para: 1 } },
      traits: [],
      star3: { name: 'Deep Trance', desc: 'Paralysis lasts 2 turns.' },
      desc: 'Paralyzes enemies in a 5-tile burst. They lose a turn and cannot block until it wears off.',
      tip: 'Golems, and units near a Barrier Ward, shrug off paralysis.',
    },
    witch: {
      name: 'Dark Magic Witch', rarity: 'rare', cost: 4, role: 'caster',
      hp: 28, pow: 17, armor: 0, block: 0.2, rec: 2, move: 3,
      act: { name: 'Dark Lightning', kind: 'line', len: 5, dmg: 'magic', ff: true },
      traits: [],
      star3: { name: 'Abyssal Bolt', desc: 'Lightning reaches 7 tiles and passes through allies harmlessly.' },
      desc: 'Black lightning strikes every unit in a straight line up to 5 tiles. Rocks stop it.',
      tip: 'Never line up in front of a Witch. Rocks and staggered formations break the line.',
    },
    lightning: {
      name: 'Lightning Ward', rarity: 'rare', cost: 4, role: 'ward',
      hp: 46, pow: 16, armor: 0.2, block: 0, rec: 1, move: 0,
      act: { name: 'Storm Pulse', kind: 'nova', radius: 2, dmg: 'magic' },
      traits: ['immobile', 'nofacing'],
      star3: { name: 'Overcharge', desc: 'Storm Pulse reaches 3 tiles.' },
      desc: 'Rooted totem. Zaps every enemy within 2 tiles with magic.',
      tip: 'It cannot move. Archers and fireballs can hit it from outside its reach.',
    },
    dragon: {
      name: 'Dragon Tyrant', rarity: 'legendary', cost: 8, role: 'monster',
      hp: 100, pow: 22, armor: 0.2, block: 0, rec: 2, move: 4,
      act: { name: 'Fire Breath', kind: 'cone', len: 3, dmg: 'magic', ff: true },
      traits: ['flying', 'big'],
      star3: { name: 'Hellfire', desc: 'Its breath reaches 4 tiles deep.' },
      desc: 'Winged tyrant. Breathes fire over a 7-tile cone and flies over anything.',
      tip: 'Mighty but slow to recover. Swarm it from the sides while it rests.',
    },

    // Summons and bosses (never recruitable).
    shrub: {
      name: 'Shrub', rarity: 'none', cost: 0, role: 'object',
      hp: 18, pow: 0, armor: 0, block: 0, rec: 0, move: 0,
      act: { name: 'None', kind: 'none' },
      traits: ['immobile', 'nofacing', 'summon'],
      desc: 'A thorny thicket. Blocks movement and lines until cut down.',
      tip: 'Cut it down, or fly and shoot over it.',
    },
    specter: {
      name: 'Specter', rarity: 'none', cost: 3, role: 'skirmisher',
      hp: 26, pow: 11, armor: 0, block: 0, rec: 1, move: 3,
      act: { name: 'Soul Drain', kind: 'strike', range: [1, 2], dmg: 'magic' },
      traits: ['flying', 'ethereal', 'drain'],
      desc: 'A restless spirit bound to a relic. Takes half damage from physical attacks and drains life with every touch.',
      tip: 'Magic hurts it fully. It will not stray far from the treasure it guards.',
    },
    warbanner: {
      name: 'War Banner', rarity: 'none', cost: 0, role: 'object',
      hp: 44, pow: 0, armor: 0.1, block: 0, rec: 0, move: 0,
      act: { name: 'Rally', kind: 'none' },
      traits: ['immobile', 'nofacing', 'object'],
      desc: 'The enemy standard. Enemies within 2 tiles of it deal 15% more damage.',
      tip: 'Burn it to break their will and win the battle.',
    },
    cage: {
      name: 'Prison Cage', rarity: 'none', cost: 0, role: 'object',
      hp: 52, pow: 0, armor: 0.2, block: 0, rec: 0, move: 0,
      act: { name: 'None', kind: 'none' },
      traits: ['immobile', 'nofacing', 'object'],
      desc: 'Captives rattle the bars. Break the cage to free them.',
      tip: 'Breaking the cage wins the battle. The freed prisoner joins your army.',
    },
    golem_king: {
      name: 'Golem King', rarity: 'boss', cost: 8, role: 'tank', boss: true,
      hp: 150, pow: 22, armor: 0.35, block: 0, rec: 1, move: 2,
      act: { name: 'Earthshatter', kind: 'quake', range: [1, 1], dmg: 'phys' },
      traits: ['stoneskin', 'guardian', 'big'],
      desc: 'Ancient king of the quarry. Earthshatter strikes a foe and every enemy beside it.',
      tip: 'Slow and immune to status. Slay the King to win; its guards will scatter.',
    },
    witch_queen: {
      name: 'Witch Queen', rarity: 'boss', cost: 8, role: 'caster', boss: true,
      hp: 140, pow: 18, armor: 0.1, block: 0.3, rec: 1, move: 3,
      act: { name: 'Hexstorm', kind: 'cross', len: 4, dmg: 'magic', ff: false },
      traits: ['spellward'],
      desc: 'Mistress of the Witchwood. Hexstorm lashes enemies in all four directions. Takes half magic damage.',
      tip: 'Stay off her four lines. Physical attackers and flanks bring her down.',
    },
    ashen_tyrant: {
      name: 'Ashen Tyrant', rarity: 'boss', cost: 9, role: 'monster', boss: true,
      hp: 250, pow: 25, armor: 0.25, block: 0, rec: 1, move: 4,
      act: { name: 'Cinder Breath', kind: 'cone', len: 3, dmg: 'magic', ff: false },
      traits: ['flying', 'big'],
      desc: 'The dragon that rules the Spire. Its breath spares its own servants.',
      tip: 'Spread out and strike from several sides at once.',
    },
  };

  const RECRUITABLE = Object.keys(UNITS).filter((k) => ['common', 'uncommon', 'rare', 'legendary'].includes(UNITS[k].rarity));

  // Which talent families a unit type can use.
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
    return tags;
  }

  const TALENTS = {
    vampiric: { name: 'Vampiric', desc: 'Heals for 30% of the damage it deals.', req: 'damage' },
    swift: { name: 'Swift', desc: '+1 Move.', req: 'mobile' },
    hardened: { name: 'Hardened', desc: '+10% armor.' },
    sentinel: { name: 'Sentinel', desc: '+12% block.', req: 'facing' },
    eagle_eye: { name: 'Eagle Eye', desc: '+1 maximum range.', req: 'ranged' },
    brutal: { name: 'Brutal', desc: '+15% damage.', req: 'damage' },
    executioner: { name: 'Executioner', desc: '+40% damage to targets below half HP.', req: 'damage' },
    thick_hide: { name: 'Thick Hide', desc: '+15 max HP.' },
    second_wind: { name: 'Second Wind', desc: 'Once per battle, survives a fatal blow with 1 HP.' },
    bloodlust: { name: 'Bloodlust', desc: 'Slaying an enemy lets it skip its recovery.', req: 'damage' },
    flanker: { name: 'Flanker', desc: '+30% damage from the side or from behind.', req: 'phys' },
    unshakable: { name: 'Unshakable', desc: 'Immune to poison and paralysis.' },
    guardian: { name: 'Guardian', desc: 'Adjacent allies take 15% less damage.' },
    retaliate: { name: 'Retaliate', desc: 'When struck in melee and still standing, strikes back for half power.', req: 'damage' },
    quickened: { name: 'Quickened', desc: 'Recovers 1 turn faster.', req: 'slow' },
    martyr: { name: 'Martyr', desc: 'When it falls, heals allies within 2 tiles for 20.' },
    arcane_focus: { name: 'Arcane Focus', desc: '+20% magic damage, healing and poison.', req: 'magic' },
  };

  function talentEligible(typeId, talentId, owned) {
    const t = TALENTS[talentId];
    if (!t) return false;
    if (owned && owned.includes(talentId)) return false;
    if (UNITS[typeId].traits.includes('summon')) return false;
    if (!t.req) return true;
    return unitTags(typeId).has(t.req);
  }

  const MAX_TALENTS = 2;

  // tier: common | uncommon | rare | boss
  const RELICS = {
    war_horn: { name: 'War Horn', tier: 'common', desc: '+1 Command Point in every battle.' },
    whetstone: { name: 'Whetstone', tier: 'common', desc: 'Physical attacks deal +2 damage.' },
    steel_bucklers: { name: 'Steel Bucklers', tier: 'common', desc: 'Your units have +8% block.' },
    iron_plating: { name: 'Iron Plating', tier: 'common', desc: 'Your units have +6% armor.' },
    coin_purse: { name: "Merchant's Purse", tier: 'common', desc: 'Gain 12 extra gold after each victory.' },
    healing_salve: { name: 'Healing Salve', tier: 'common', desc: 'At the start of your turn, your most injured unit heals 6 HP.' },
    scout_map: { name: "Cartographer's Map", tier: 'common', desc: 'Your deployment zone reaches one row further forward.' },
    field_kit: { name: "Surgeon's Kit", tier: 'common', desc: 'Units that fall in a victory are not wounded.' },
    swift_boots: { name: 'Pathfinder Boots', tier: 'common', desc: 'Units with 3 Move or less gain +1 Move.' },
    oak_charm: { name: 'Oaken Charm', tier: 'common', desc: 'Your units have +8 max HP.' },
    mana_crystal: { name: 'Mana Crystal', tier: 'uncommon', desc: 'Spellcasters (Recover 2 or more) recover 1 turn faster.' },
    bloodstone: { name: 'Bloodstone', tier: 'uncommon', desc: 'Your units heal for 20% of the damage they deal.' },
    thorned_mail: { name: 'Thorned Mail', tier: 'uncommon', desc: 'Enemies that strike your units in melee take 5 damage.' },
    headsman_axe: { name: "Headsman's Axe", tier: 'uncommon', desc: '+30% damage against enemies below half HP.' },
    phoenix_feather: { name: 'Phoenix Feather', tier: 'uncommon', desc: 'The first of your units to fall in each battle rises again with half HP.' },
    guild_seal: { name: 'Guild Seal', tier: 'uncommon', desc: 'Shop items and promotions cost 25% less.' },
    legion_banner: { name: 'Banner of the Legion', tier: 'uncommon', desc: '+2 Command Points in every battle.' },
    sands_of_haste: { name: 'Sands of Haste', tier: 'uncommon', desc: 'Enemy spellcasters (Recover 2 or more) start each battle recovering.' },
    old_crown: { name: 'Crown of the Old King', tier: 'rare', desc: 'Your units deal 15% more damage.' },
    shadow_cloak: { name: 'Shadow Cloak', tier: 'rare', desc: 'Your attacks from behind deal 40% more damage.' },
    aegis: { name: 'Aegis of Dawn', tier: 'rare', desc: 'Attacks against the sides of your units face full block.' },
    warlord_helm: { name: "Warlord's Helm", tier: 'rare', desc: 'A unit that slays an enemy skips its recovery.' },
    alchemist_stone: { name: "Alchemist's Stone", tier: 'rare', desc: 'Unspent Command Points earn double gold.' },
    dragon_scale: { name: 'Dragon Scale', tier: 'rare', desc: 'Your units take 25% less magic damage.' },
    tyrant_heart: { name: 'Heart of the Tyrant', tier: 'boss', desc: '+3 Command Points in every battle.' },
    titan_gauntlet: { name: "Titan's Gauntlet", tier: 'boss', desc: 'Your units deal 25% more damage, but you have 1 fewer Command Point.' },
    eternal_flame: { name: 'Eternal Flame', tier: 'boss', desc: "Each unit's first action in a battle needs no recovery." },
    kings_ransom: { name: "King's Ransom", tier: 'boss', desc: 'Gain 150 gold now and 20 extra gold after each victory.' },
    golden_standard: { name: 'Golden Standard', tier: 'boss', desc: 'Gain 1 max Banner and restore all Banners.' },
    sacred_chalice: { name: 'Sacred Chalice', tier: 'boss', desc: 'At the start of your turn, all your units heal 3 HP.' },
    cursed_blade: { name: 'Bloodthirst Blade', tier: 'event', desc: 'Your units deal 20% more damage and take 10% more damage.' },
  };

  const WARBANDS = [
    {
      id: 'vanguard', name: 'Iron Vanguard',
      desc: 'Shields and faith. Sturdy and forgiving.',
      units: ['knight', 'knight', 'archer', 'cleric'], relic: 'steel_bucklers', gold: 60,
    },
    {
      id: 'ember', name: 'Ember Circle',
      desc: 'Fire burns through armor. Fragile if caught up close.',
      units: ['pyromancer', 'knight', 'archer', 'scout'], relic: 'iron_plating', gold: 50,
    },
    {
      id: 'shadow', name: 'Shadow Syndicate',
      desc: 'Flankers and knives. Rewards careful positioning.',
      units: ['assassin', 'scout', 'scout', 'archer'], relic: 'whetstone', gold: 70,
    },
    {
      id: 'grove', name: 'Wildgrove Pact',
      desc: 'Beasts and brambles. Wall off the field, then charge.',
      units: ['beastrider', 'furgon', 'archer', 'cleric'], relic: 'healing_salve', gold: 55,
    },
  ];

  const DIFFICULTIES = [
    { id: 'squire', name: 'Squire', desc: 'Weaker enemy armies. A gentle introduction.', mult: 0.85, temp: 2.5 },
    { id: 'knight', name: 'Knight', desc: 'The intended challenge.', mult: 1.0, temp: 1.2 },
    { id: 'warlord', name: 'Warlord', desc: 'Larger armies and sharper enemy commanders.', mult: 1.15, temp: 0.5 },
  ];

  const ACTS = [
    null,
    { name: 'The Proving Grounds', short: 'Act I', palette: 'grass', boss: 'golem_king' },
    { name: 'The Witchwood', short: 'Act II', palette: 'swamp', boss: 'witch_queen' },
    { name: "The Tyrant's Spire", short: 'Act III', palette: 'ember', boss: 'ashen_tyrant' },
  ];

  // Enemy squads. Units listed are the core; the run scales them to the floor's budget.
  const ENCOUNTERS = {
    1: {
      normal: [
        { name: 'Bandit Patrol', units: ['knight', 'archer', 'scout'], stance: 'balanced', pool: ['scout', 'archer', 'knight'] },
        { name: 'Archer Nest', units: ['archer', 'archer', 'knight'], stance: 'defensive', pool: ['archer', 'knight'] },
        { name: 'Raiders', units: ['berserker', 'scout', 'scout'], stance: 'aggressive', pool: ['berserker', 'scout'] },
        { name: 'Fire Cult', units: ['pyromancer', 'knight', 'scout'], stance: 'balanced', pool: ['knight', 'scout'] },
        { name: 'Temple Guard', units: ['cleric', 'knight', 'knight'], stance: 'balanced', pool: ['knight', 'archer'] },
        { name: 'Hunting Party', units: ['beastrider', 'archer', 'scout'], stance: 'aggressive', pool: ['scout', 'archer'] },
      ],
      elite: [
        { name: 'Golem Sentinels', units: ['golem', 'golem', 'archer', 'cleric'], stance: 'defensive', pool: ['archer'] },
        { name: 'Twin Flames', units: ['pyromancer', 'pyromancer', 'knight', 'knight'], stance: 'balanced', pool: ['knight'] },
        { name: "Assassins' Guild", units: ['assassin', 'assassin', 'scout', 'archer'], stance: 'aggressive', pool: ['scout', 'archer'] },
      ],
      boss: [{ name: 'The Golem King', units: ['golem_king', 'knight', 'archer', 'archer', 'cleric', 'knight'], stance: 'balanced', objective: 'boss', pool: ['knight', 'archer'] }],
    },
    2: {
      normal: [
        { name: 'Witch Circle', units: ['witch', 'knight', 'archer', 'scout'], stance: 'balanced', pool: ['knight', 'scout'] },
        { name: 'Bog Wisps', units: ['wisp', 'wisp', 'berserker', 'berserker'], stance: 'aggressive', pool: ['berserker', 'wisp'] },
        { name: 'Enchanted Guard', units: ['enchantress', 'knight', 'knight', 'archer'], stance: 'balanced', pool: ['knight', 'archer'] },
        { name: 'Furgon Grove', units: ['furgon', 'archer', 'archer', 'cleric', 'furgon'], stance: 'defensive', pool: ['archer'] },
        { name: 'Wolf Riders', units: ['beastrider', 'beastrider', 'archer', 'cleric'], stance: 'aggressive', pool: ['beastrider', 'scout'] },
        { name: 'Ward Line', units: ['lightning', 'archer', 'archer', 'knight', 'barrier'], stance: 'defensive', pool: ['archer', 'knight'] },
      ],
      elite: [
        { name: 'The Coven', units: ['witch', 'witch', 'barrier', 'knight', 'knight'], stance: 'balanced', pool: ['knight'] },
        { name: 'Poison Court', units: ['wisp', 'wisp', 'enchantress', 'assassin', 'assassin'], stance: 'aggressive', pool: ['assassin'] },
        { name: 'Stone Circle', units: ['golem', 'golem', 'cleric', 'pyromancer', 'lightning'], stance: 'defensive', pool: ['golem', 'archer'] },
      ],
      boss: [{ name: 'The Witch Queen', units: ['witch_queen', 'enchantress', 'wisp', 'knight', 'knight', 'witch', 'wisp'], stance: 'balanced', objective: 'boss', pool: ['knight', 'wisp'] }],
    },
    3: {
      normal: [
        { name: 'Spire Garrison', units: ['knight', 'knight', 'lightning', 'archer', 'archer', 'cleric'], stance: 'defensive', pool: ['knight', 'archer'] },
        { name: 'Shadow Strike', units: ['assassin', 'assassin', 'enchantress', 'scout', 'assassin'], stance: 'aggressive', pool: ['assassin', 'scout'] },
        { name: 'Berserk Horde', units: ['berserker', 'berserker', 'beastrider', 'berserker', 'beastrider'], stance: 'aggressive', pool: ['berserker', 'beastrider'] },
        { name: 'Arcane Battery', units: ['pyromancer', 'pyromancer', 'barrier', 'golem', 'witch'], stance: 'balanced', pool: ['golem', 'knight'] },
        { name: 'Drake Keepers', units: ['dragon', 'knight', 'archer', 'cleric'], stance: 'balanced', pool: ['knight', 'archer'] },
        { name: 'Iron Wall', units: ['golem', 'golem', 'knight', 'knight', 'archer', 'archer'], stance: 'defensive', pool: ['archer', 'knight'] },
      ],
      elite: [
        { name: 'Twin Tyrants', units: ['dragon', 'dragon', 'cleric'], stance: 'aggressive', pool: ['knight'] },
        { name: 'Champions of the Spire', units: ['knight', 'assassin', 'pyromancer', 'cleric', 'archer'], stance: 'balanced', ranks: [3, 3, 3, 2, 2], pool: ['knight', 'archer'] },
        { name: 'Storm Fortress', units: ['lightning', 'lightning', 'barrier', 'archer', 'archer', 'archer'], stance: 'defensive', pool: ['archer'] },
      ],
      boss: [{ name: 'The Ashen Tyrant', units: ['ashen_tyrant', 'pyromancer', 'knight', 'knight', 'lightning', 'cleric', 'pyromancer'], stance: 'balanced', objective: 'boss', pool: ['knight', 'archer'] }],
    },
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
    DIRS, RANK_MULT, UNITS, RECRUITABLE, TALENTS, MAX_TALENTS, RELICS, WARBANDS,
    DIFFICULTIES, ACTS, ENCOUNTERS, NAMES, unitTags, talentEligible,
  };
})(typeof window !== 'undefined' ? window : globalThis);
