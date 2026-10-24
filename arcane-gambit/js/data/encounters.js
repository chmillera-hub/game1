/* Encounters. Maps are drawn top (enemy side) to bottom (your side):
     .  floor     p  floor you may deploy on     #  wall     ~  chasm
     (space) off-board     letters: enemies from the legend.
   supply = points to spend on units + upgrades; slots = max units. */
(function (AG) {
  'use strict';

  const E = [];
  const add = (o) => { E.push(o); return o; };

  // ================================================================= ACT I
  add({
    id: 'goblinSkirmish', act: 1, tier: 'early', name: 'Goblin Skirmish', theme: 'moss',
    flavor: 'A handful of goblins have set up an ambush on the old chessboard road.',
    supply: 8, slots: 3,
    map: [
      '...g..',
      '.g..g.',
      '..s..g',
      '......',
      'pppppp',
      'pppppp',
    ],
    legend: { g: 'goblin', s: 'goblinSlinger' },
  });
  add({
    id: 'wolfFord', act: 1, tier: 'early', name: 'Wolves at the Ford', theme: 'moss',
    flavor: 'Three wolves pace the far bank. The river can only be crossed at two fords.',
    supply: 8, slots: 3, boost: 0.1,
    map: [
      '...w.w.a.',
      '....w....',
      '~~.~~~.~~',
      '.........',
      'ppppppppp',
      'ppppppppp',
    ],
    legend: { w: 'wolf', a: 'goblinSlinger' },
  });
  add({
    id: 'slimeCellar', act: 1, tier: 'early', name: 'The Slime Cellar', theme: 'moss',
    flavor: 'A diamond-shaped cellar. Something wet is multiplying down here.',
    supply: 8, slots: 3, boost: 0.15,
    map: [
      '   s   ',
      '  .s.  ',
      ' ss.m. ',
      '.......',
      ' ppppp ',
      '  ppp  ',
      '   p   ',
    ],
    legend: { s: 'slime', m: 'goblinShaman' },
  });
  add({
    id: 'banditBridge', act: 1, tier: 'normal', name: 'Bandit Bridge', theme: 'moss',
    flavor: 'A long rope bridge over a gorge. The toll collectors are not friendly.',
    supply: 10, slots: 3, boost: 0.35,
    map: [
      '.a.a.',
      '..b..',
      '.b...',
      '~...~',
      '~...~',
      '~...~',
      '.....',
      'ppppp',
      'ppppp',
    ],
    legend: { a: 'goblinSlinger', b: 'bandit' },
  });
  add({
    id: 'boarRun', act: 1, tier: 'normal', name: 'Boar Run', theme: 'moss',
    flavor: 'Hedgerows split the field into lanes. The boars like a long run-up.',
    supply: 10, slots: 4, boost: 0.1,
    map: [
      '.o..a.o.',
      '........',
      '#..##..#',
      '..g..g..',
      '...g....',
      '........',
      'pppppppp',
      'pppppppp',
    ],
    legend: { o: 'boar', g: 'goblin', a: 'goblinSlinger' },
  });
  add({
    id: 'thornwood', act: 1, tier: 'normal', name: 'The Thornwood', theme: 'moss',
    flavor: 'An eight-sided glade ringed with thorn trees. Wolves and slingers wait in the shadows.',
    supply: 10, slots: 4,
    map: [
      '  ....  ',
      ' .w..w. ',
      '..#..#..',
      '...ss...',
      '....w...',
      '..#..#..',
      ' pppppp ',
      '  pppp  ',
    ],
    legend: { w: 'wolf', s: 'goblinSlinger' },
  });
  add({
    id: 'watchtower', act: 1, tier: 'normal', name: 'Goblin Watchtower', theme: 'moss',
    flavor: 'A slinger perches in a stone tower while the rest of the patrol guards the approach.',
    supply: 10, slots: 4, boost: 0.35,
    map: [
      '.#s#.s.',
      '.#.#.m.',
      '.g...g.',
      '.......',
      '#..g..#',
      '.......',
      'ppppppp',
      'ppppppp',
    ],
    legend: { s: 'goblinSlinger', g: 'goblin', m: 'goblinShaman' },
  });
  add({
    id: 'fairyRing', act: 1, tier: 'normal', name: 'The Fairy Ring', theme: 'moss',
    flavor: 'A sinkhole ringed by mushrooms. Slimes ooze around both sides.',
    supply: 10, slots: 5, boost: 0.25,
    map: [
      '.s.g.s.',
      '..gm.s.',
      '..~~~..',
      '..~~~..',
      '..~~~..',
      '.......',
      'ppppppp',
      'ppppppp',
    ],
    legend: { s: 'slime', m: 'goblinShaman', g: 'goblin' },
  });
  // Act I elites
  add({
    id: 'trollBridge', act: 1, tier: 'elite', name: 'The Troll Bridge', theme: 'moss',
    flavor: 'Under the bridge lives a troll who regenerates faster than most things can hurt it. Fire helps.',
    supply: 12, slots: 3,
    map: [
      '..t..',
      '.g.g.',
      '.....',
      '~...~',
      '~...~',
      '~...~',
      '.....',
      'ppppp',
      'ppppp',
    ],
    legend: { t: 'troll', g: 'goblin' },
  });
  add({
    id: 'warboss', act: 1, tier: 'elite', name: 'The Warboss', theme: 'moss',
    flavor: 'A goblin warboss with a horn and a temper. More goblins arrive every few turns.',
    supply: 12, slots: 4, boost: 0.4,
    map: [
      '.s.W.s.',
      '..g.g..',
      '.......',
      '.#...#.',
      '.......',
      'ppppppp',
      'ppppppp',
    ],
    legend: { W: 'goblinChief', g: 'goblin', s: 'goblinSlinger' },
  });
  add({
    id: 'alphaDen', act: 1, tier: 'elite', name: 'The Alpha’s Den', theme: 'moss',
    flavor: 'The pack leader howls and every wolf surges up the turn order.',
    supply: 12, slots: 4,
    map: [
      '...A....',
      '.w..w.w.',
      '........',
      '..#..#..',
      '........',
      'pppppppp',
      'pppppppp',
    ],
    legend: { A: 'alphaWolf', w: 'wolf' },
  });
  add({
    id: 'spiderNest', act: 1, tier: 'elite', name: 'The Spider Nest', theme: 'moss',
    flavor: 'The Brood Mother lays a new spiderling every round. End this quickly.',
    supply: 12, slots: 4, boost: 0.55,
    map: [
      '#..B..#',
      '.x...x.',
      '.......',
      '#.....#',
      '.......',
      'ppppppp',
      'ppppppp',
    ],
    legend: { B: 'broodMother', x: 'spiderling' },
  });
  // Act I boss
  add({
    id: 'goblinThrone', act: 1, tier: 'boss', name: 'Throne of King Grumblewart', theme: 'moss',
    flavor: 'The goblin king holds court on a ruined chessboard. While he lives, every goblin fights harder, and his guard never runs out.',
    supply: 14, slots: 5, boost: 0.2,
    map: [
      '.#.K..#.',
      '..m..s..',
      '.g.gg.s.',
      '........',
      '.#....#.',
      '........',
      'pppppppp',
      'pppppppp',
    ],
    legend: { K: 'goblinKing', g: 'goblin', s: 'goblinSlinger', m: 'goblinShaman' },
  });

  AG.Encounters = {};
  for (const e of E) AG.Encounters[e.id] = e;
  AG.encounterList = function (filter) {
    return Object.keys(AG.Encounters).map((k) => AG.Encounters[k]).filter((e) => !filter || filter(e));
  };
})(globalThis.AG = globalThis.AG || {});
