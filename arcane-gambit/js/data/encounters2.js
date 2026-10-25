/* Acts II and III. See encounters.js for the map legend. */
(function (AG) {
  'use strict';
  const add = (o) => { AG.Encounters[o.id] = o; };

  // ================================================================ ACT II
  add({
    id: 'graveyardShift', act: 2, tier: 'early', name: 'Graveyard Shift', theme: 'bone',
    flavor: 'Tombstones everywhere, and the skeletons keep getting back up. Fire or holy light keeps them down.',
    supply: 14, boost: -0.32,
    map: [
      '..s.as..',
      '.#.a..#.',
      '...s.s..',
      '.#..z.#.',
      '........',
      '..#..#..',
      'pppppppp',
      'pppppppp',
    ],
    legend: { s: 'skeleton', a: 'boneArcher', z: 'zombie' },
  });
  add({
    id: 'longCrypt', act: 2, tier: 'early', name: 'The Long Crypt', theme: 'bone',
    flavor: 'A narrow crypt, eleven ranks deep. The archers at the far end have a clear shot down every lane.',
    supply: 14, boost: -0.29,
    map: [
      '.a.a.',
      '..g..',
      '.....',
      'z...z',
      '.#.#.',
      '.....',
      '.#.#.',
      '.....',
      '.....',
      'ppppp',
      'ppppp',
    ],
    legend: { a: 'boneArcher', g: 'ghost', z: 'zombie' },
  });
  add({
    id: 'cultCircle', act: 2, tier: 'normal', name: 'The Cult Circle', theme: 'bone',
    flavor: 'Cultists chant around a black altar. Each one that dies empowers its neighbours.',
    supply: 15, boost: 0.2,
    map: [
      '  .c..  ',
      ' .c..c. ',
      '...##...',
      '..c##.G.',
      '........',
      '........',
      ' pppppp ',
      '  pppp  ',
    ],
    legend: { c: 'cultist', G: 'gravecaller' },
  });
  add({
    id: 'hauntedCauseway', act: 2, tier: 'normal', name: 'Haunted Causeway', theme: 'bone',
    flavor: 'A wide causeway crumbling into the marsh. Ghosts drift over the gaps; you cannot.',
    supply: 14, boost: -0.05,
    map: [
      '.bg..b.gg.',
      '~~......~~',
      '..~~..~~..',
      '..........',
      'pppppppppp',
      'pppppppppp',
    ],
    legend: { g: 'ghost', b: 'banshee' },
  });
  add({
    id: 'ossuary', act: 2, tier: 'normal', name: 'The Ossuary', theme: 'bone',
    flavor: 'A diamond vault stacked with bones. The Gravecaller will put them all to use.',
    supply: 14, boost: -0.08,
    map: [
      '    G    ',
      '   s.s   ',
      '  ..a..  ',
      ' .#...#. ',
      '.........',
      ' ....... ',
      '  ppppp  ',
      '   ppp   ',
      '    p    ',
    ],
    legend: { G: 'gravecaller', s: 'skeleton', a: 'boneArcher' },
  });
  add({
    id: 'plagueVillage', act: 2, tier: 'normal', name: 'Plague Village', theme: 'bone',
    flavor: 'The villagers are slow, hungry and very contagious. Anything they kill joins them.',
    supply: 15, boost: 0.61,
    map: [
      '..z...z..',
      '.z..c..z.',
      '...#.#...',
      '....z....',
      '.........',
      'ppppppppp',
      'ppppppppp',
    ],
    legend: { z: 'zombie', c: 'cultist' },
  });
  add({
    id: 'wailingBridge', act: 2, tier: 'normal', name: 'The Wailing Bridge', theme: 'bone',
    flavor: 'Two banshees haunt a broken bridge. Their wail drags your pieces down the turn order.',
    supply: 13, boost: 0.3,
    map: [
      '.b.ab.',
      '..ss..',
      '~....~',
      '~.~~.~',
      '~....~',
      '......',
      'pppppp',
      'pppppp',
    ],
    legend: { b: 'banshee', s: 'skeleton', a: 'boneArcher' },
  });
  add({
    id: 'mausoleum', act: 2, tier: 'normal', name: 'Mausoleum Steps', theme: 'bone',
    flavor: 'An hourglass-shaped hall that pinches to a single doorway in the middle.',
    supply: 15, boost: 0.3,
    map: [
      '.a.g.a.',
      '..sgs..',
      ' ..... ',
      '  ...  ',
      ' ..... ',
      '.......',
      'ppppppp',
      'ppppppp',
    ],
    legend: { a: 'boneArcher', g: 'ghost', s: 'skeleton' },
  });
  // Act II elites
  add({
    id: 'deathVigil', act: 2, tier: 'elite', name: 'The Death Knight’s Vigil', theme: 'bone',
    flavor: 'A Death Knight leaps like a chess knight and heals on every kill.',
    supply: 17, boost: 0.23,
    map: [
      '...D....',
      '.s....s.',
      '...aa...',
      '.#....#.',
      '........',
      '........',
      'pppppppp',
      'pppppppp',
    ],
    legend: { D: 'deathKnight', s: 'skeleton', a: 'boneArcher' },
  });
  add({
    id: 'colossus', act: 2, tier: 'elite', name: 'The Bone Colossus', theme: 'bone',
    flavor: 'A tower of fused bones whose every swing hits everything around it. Do not crowd it.',
    supply: 15, boost: 0.32,
    map: [
      '.z..C..z.',
      '..s...s..',
      '....z....',
      '.........',
      '..#...#..',
      'ppppppppp',
      'ppppppppp',
    ],
    legend: { C: 'boneColossus', z: 'zombie', s: 'skeleton' },
  });
  add({
    id: 'vampireHall', act: 2, tier: 'elite', name: 'The Vampire Lord’s Hall', theme: 'bone',
    flavor: 'The Lord drinks deep, calls bats and grows stronger with every kill.',
    supply: 15, boost: -0.46,
    map: [
      '#..V...#',
      '.c....c.',
      '..b..b..',
      '........',
      '.#....#.',
      '........',
      'pppppppp',
      'pppppppp',
    ],
    legend: { V: 'vampireLord', c: 'cultist', b: 'bat' },
  });
  // Act II boss
  add({
    id: 'lichVault', act: 2, tier: 'boss', name: 'Vault of Morvane', theme: 'bone',
    flavor: 'Morvane cannot die while the phylactery in the back of the vault stands. Break it, then break him.',
    supply: 20, boost: -0.53,
    map: [
      '....P....',
      '.##...##.',
      '.a..L..a.',
      '..s...s..',
      '.........',
      '.#.....#.',
      '.........',
      'ppppppppp',
      'ppppppppp',
    ],
    legend: { P: 'phylactery', L: 'lich', a: 'boneArcher', s: 'skeleton' },
  });

  // =============================================================== ACT III
  add({
    id: 'clockworkGambit', act: 3, tier: 'early', name: 'Clockwork Gambit', theme: 'astral',
    flavor: 'Six clockwork pawns march on your back rank. Any that reaches it becomes a queen.',
    supply: 17, boost: 1.2,
    map: [
      't......t',
      '........',
      'cc.cc.cc',
      '........',
      '........',
      '........',
      'pppppppp',
      'pppppppp',
    ],
    legend: { t: 'turret', c: 'clockPawn' },
  });
  add({
    id: 'confluence', act: 3, tier: 'early', name: 'Elemental Confluence', theme: 'astral',
    flavor: 'Fire and frost meet on a cross-shaped dais.',
    supply: 19, boost: 0.37,
    map: [
      '  .f.  ',
      '  .i.  ',
      '...f...',
      '.i...i.',
      '.......',
      '  ...  ',
      '  ppp  ',
      'ppppppp',
    ],
    legend: { f: 'fireElemental', i: 'frostElemental' },
  });
  add({
    id: 'voidRift', act: 3, tier: 'normal', name: 'The Void Rift', theme: 'astral',
    flavor: 'Islands of stone over nothing. Void Stalkers step between them at will.',
    supply: 19, boost: 0.92,
    map: [
      '..v.v.v..',
      '...~d~...',
      '~~.~~~.~~',
      '.........',
      '..~...~..',
      'ppppppppp',
      'ppppppppp',
    ],
    legend: { v: 'voidStalker', d: 'demonBrute' },
  });
  add({
    id: 'mirrorHall', act: 3, tier: 'normal', name: 'Hall of Mirrors', theme: 'astral',
    flavor: 'Mirror Knights punish anyone shooting at them, and the turrets cover every file.',
    supply: 18, boost: -0.32,
    map: [
      't.....t',
      '..m.m..',
      '.f.m.f.',
      '.......',
      '.#...#.',
      '.......',
      'ppppppp',
      'ppppppp',
    ],
    legend: { t: 'turret', m: 'mirrorKnight', f: 'frostElemental' },
  });
  add({
    id: 'demonPit', act: 3, tier: 'normal', name: 'The Demon Pit', theme: 'astral',
    flavor: 'Demon Brutes and their imps circle a bottomless pit. A good shove ends any argument.',
    supply: 20,
    map: [
      '.i.d.i..',
      '..d..d..',
      '..~~~~..',
      '..~~~~..',
      '........',
      '.i....i.',
      'pppppppp',
      'pppppppp',
    ],
    legend: { d: 'demonBrute', i: 'imp_summon' },
  });
  add({
    id: 'observatory', act: 3, tier: 'normal', name: 'The Observatory', theme: 'astral',
    flavor: 'A star-chart floor where turrets track you and frost slows you down.',
    supply: 18, boost: 0.5,
    map: [
      '   .t.   ',
      '  .i.i.  ',
      ' ..v.v.. ',
      '.........',
      '..#...#..',
      '.........',
      ' ppppppp ',
      '  ppppp  ',
    ],
    legend: { t: 'turret', i: 'frostElemental', v: 'voidStalker' },
  });
  add({
    id: 'starBridge', act: 3, tier: 'normal', name: 'Star Bridge', theme: 'astral',
    flavor: 'A long bridge of light. Turrets fire down its length while pawns advance.',
    supply: 15, boost: 0.34,
    map: [
      '..v..',
      'c.c.c',
      '.c.c.',
      '~t.t~',
      '~...~',
      '~...~',
      '~...~',
      '.....',
      '.....',
      'ppppp',
      'ppppp',
    ],
    legend: { t: 'turret', c: 'clockPawn', v: 'voidStalker' },
  });
  add({
    id: 'forge', act: 3, tier: 'normal', name: 'The Infernal Forge', theme: 'astral',
    flavor: 'Everything here is on fire, including the floor plan.',
    supply: 20, boost: 0.41,
    map: [
      '..f..f..',
      '...dd...',
      '.#....#.',
      '........',
      '...#....',
      '........',
      'pppppppp',
      'pppppppp',
    ],
    legend: { f: 'fireElemental', d: 'demonBrute' },
  });
  // Act III elites
  add({
    id: 'archonEngine', act: 3, tier: 'elite', name: 'The Archon Engine', theme: 'astral',
    flavor: 'An ancient war machine that fires a beam down an entire file every other turn.',
    supply: 19, boost: 1.2,
    map: [
      't...A...t',
      '.........',
      '.c.c.c.c.',
      '.........',
      '.#.....#.',
      '.........',
      'ppppppppp',
      'ppppppppp',
    ],
    legend: { A: 'archon', t: 'turret', c: 'clockPawn' },
  });
  add({
    id: 'drakeLair', act: 3, tier: 'elite', name: 'The Drake’s Lair', theme: 'astral',
    flavor: 'An Infernal Drake and its elemental servants. Bring something that does not burn.',
    supply: 22, boost: 1.2,
    map: [
      '...D....',
      '.f..f.f.',
      '...i....',
      '..#..#..',
      '........',
      '........',
      'pppppppp',
      'pppppppp',
    ],
    legend: { D: 'infernalDrake', f: 'fireElemental', i: 'imp_summon' },
  });
  add({
    id: 'stalkers', act: 3, tier: 'elite', name: 'The Stalkers', theme: 'astral',
    flavor: 'Four Void Stalkers that strike whoever has not moved yet. Speed matters here.',
    supply: 19, boost: 0.64,
    map: [
      'v..v...v.',
      '....m..v.',
      '.........',
      '~~.....~~',
      '.........',
      'ppppppppp',
      'ppppppppp',
    ],
    legend: { v: 'voidStalker', m: 'mirrorKnight' },
  });
  // Event battles
  add({
    id: 'goblinToll', act: 1, tier: 'event', name: 'The Goblin Toll', theme: 'moss',
    flavor: 'Six goblins and a rope across the road. They were hoping you would say no.',
    supply: 10, boost: 0.78,
    map: [
      'ag.g.ga',
      '..g.g..',
      '...g...',
      '.......',
      'ppppppp',
      'ppppppp',
    ],
    legend: { g: 'goblin', a: 'goblinSlinger' },
  });
  add({
    id: 'ghostDuel2', act: 2, tier: 'event', name: 'Ghost of the Old Champion', theme: 'bone',
    flavor: 'The Old Champion and its spectral retinue. They move like a real army, because once they were one.',
    supply: 16, boost: 0.3,
    map: [
      '..gCg..',
      '.k...k.',
      '.......',
      '.......',
      'ppppppp',
      'ppppppp',
    ],
    legend: { C: 'ghostChampion', g: 'ghost', k: 'skeleton' },
  });
  add({
    id: 'ghostDuel3', act: 3, tier: 'event', name: 'Ghost of the Old Champion', theme: 'astral',
    flavor: 'The Old Champion and its spectral retinue, brighter here among the stars.',
    supply: 21, boost: -0.08,
    map: [
      '.g.C.g.',
      '.k.b.k.',
      '..g.g..',
      '.......',
      '.......',
      'ppppppp',
      'ppppppp',
    ],
    legend: { C: 'ghostChampion', g: 'ghost', k: 'skeleton', b: 'banshee' },
  });
  // Final boss
  add({
    id: 'grandmaster', act: 3, tier: 'boss', name: 'The Mad Grandmaster', theme: 'classic',
    flavor: 'The Grandmaster plays the oldest game with a living army. Checkmate him and his whole army falls.',
    supply: 34, boost: 0.5,
    objective: { type: 'assassinate' },
    map: [
      'rnbqkbnr',
      'o.oooo.o',
      '........',
      '........',
      '........',
      '........',
      'pppppppp',
      'pppppppp',
    ],
    legend: {
      r: 'ebonRook', n: 'ebonKnight', b: 'ebonBishop', q: 'ebonQueen',
      k: { def: 'ebonKing', objective: true }, o: 'ebonPawn',
    },
  });
  // The mega boss, offered after the final boss. Not meant to be beaten.
  add({
    id: 'zugzwang', act: 3, tier: 'mega', name: 'The Heart of the Board', theme: 'void',
    flavor: 'Behind the Grandmaster’s board beats the Heart: Zugzwang, the position every game ends in. It has never lost. It takes at most 20 damage a round, every move you make costs you, and it grows stronger each round. Bring everything.',
    supply: 40, maxRounds: 20,
    objective: { type: 'assassinate' },
    map: [
      '   ....   ',
      '  ..e.e.  ',
      ' ....Z... ',
      '..........',
      '..........',
      '..........',
      'pppppppppp',
      'pppppppppp',
      ' pppppppp ',
      '  pppppp  ',
    ],
    legend: { Z: { def: 'zugzwang', objective: true }, e: 'echo' },
  });
})(globalThis.AG = globalThis.AG || {});
