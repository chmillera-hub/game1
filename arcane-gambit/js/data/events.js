/* Tower events, one halfway up each act. Each choice may need a pick from the player
   (pick: 'trainable' | 'rune' | 'unit'), and returns a short outcome text.
   A choice can also start a battle: return { text, battle: encounterId, bonus }. */
(function (AG) {
  'use strict';
  const R = () => AG.Run;

  AG.Events = [
    {
      id: 'tutor', name: 'The Wandering Tutor', acts: [1, 2, 3],
      text: 'An old grandmaster sits beside the road with a travelling board. "Your pieces move like amateurs," she says. "I can fix one of them. Or I can teach you a trick."',
      choices: [
        { label: 'Train a unit', desc: 'Promote one unit type a rank, for free.', pick: 'trainable',
          available: (run) => R().trainable(run).length > 0 || 'Every unit is fully trained.',
          apply(run, rng, def) { R().train(run, def); return 'Your ' + AG.Units[def].name + 's are now ' + AG.RANKS[run.ranks[def]] + 's.'; } },
        { label: 'Learn a trick', desc: 'Gain a random rune.',
          apply(run, rng) { const r = R().randomRune(run, rng, 'uncommon'); R().addRune(run, r); return 'She presses a ' + AG.Runes[r].name + ' into your hand.'; } },
        { label: 'Thank her and leave', desc: '', apply() { return 'You leave her to her endgame studies.'; } },
      ],
    },
    {
      id: 'blackBoard', name: 'The Black Glass Board', acts: [1, 2, 3],
      text: 'A chessboard of black glass stands alone in a clearing. A single piece waits on it, warm to the touch and humming. Something on the board wants payment.',
      choices: [
        { label: 'Take the piece', desc: 'Gain a random rare unit. Your next battle has 4 less supply.',
          available: (run) => R().unitPool(run, 'rare').length > 0 || 'You already command every rare unit.',
          apply(run, rng) { const u = rng.pick(R().unitPool(run, 'rare')); R().addUnit(run, u); R().nextBattleSupply(run, -4); return 'The ' + AG.Units[u].name + ' joins you. The board keeps something back: 4 less supply in your next battle.'; } },
        { label: 'Leave it', desc: '', apply() { return 'You back away slowly.'; } },
      ],
    },
    {
      id: 'toll', name: 'The Goblin Toll', acts: [1],
      text: 'A rope across the road, a sign that says TOLL, and six goblins who look like they have never been paid.',
      choices: [
        { label: 'Pay 25 gold', desc: '', available: (run) => run.gold >= 25 || 'Not enough gold.',
          apply(run) { run.gold -= 25; return 'The goblins bite your coins, nod, and lower the rope.'; } },
        { label: 'Fight through', desc: 'A battle. Win for 40 gold.',
          apply(run, rng) { return { text: 'You draw steel. The goblins look delighted.', battle: 'goblinToll', bonus: { gold: 40 } }; } },
        { label: 'Sneak around', desc: 'Your next battle has 2 less supply.', apply(run) { R().nextBattleSupply(run, -2); return 'You wade through a bramble thicket for an hour and lose some kit on the way. Nobody sees you. Everything itches.'; } },
      ],
    },
    {
      id: 'fountain', name: 'Fountain of Mana', acts: [1, 2, 3],
      text: 'Glowing water bubbles up from a cracked flagstone. It smells of ozone and old libraries.',
      choices: [
        { label: 'Drink deeply', desc: 'Your next battle has 4 more supply.', apply(run) { R().nextBattleSupply(run, 4); return 'Your head clears. You will field more in the next battle. (+4 supply)'; } },
        { label: 'Fill a vial', desc: 'Gain the Rune of Warding.', apply(run) { R().addRune(run, 'warding'); return 'The vial glows faintly. Rune of Warding gained.'; } },
      ],
    },
    {
      id: 'gambler', name: 'The Gambler', acts: [1, 2, 3],
      text: 'A grinning stranger shuffles a deck of cards with too many queens in it. "Double or nothing?"',
      choices: [
        { label: 'Bet 30 gold', desc: 'Even odds to win 60.', available: (run) => run.gold >= 30 || 'Not enough gold.',
          apply(run, rng) {
            if (rng.chance(0.5)) { run.gold += 30; return 'Queen of hearts. You win 30 gold.'; }
            run.gold -= 30; return 'Queen of spades. He pockets your 30 gold and vanishes.';
          } },
        { label: 'Walk on', desc: '', apply() { return 'You keep your gold and your dignity.'; } },
      ],
    },
    {
      id: 'armory', name: 'Abandoned Armory', acts: [1, 2, 3],
      text: 'A collapsed armory, its rune racks half buried. You could pick through it carefully, or tear it apart.',
      choices: [
        { label: 'Search carefully', desc: 'Gain a random rune.', apply(run, rng) { const r = R().randomRune(run, rng); R().addRune(run, r); return 'You find a ' + AG.Runes[r].name + '.'; } },
        { label: 'Tear it apart', desc: 'Gain 2 random runes. Your next battle has 3 less supply.',
          apply(run, rng) {
            const a = R().randomRune(run, rng), b = R().randomRune(run, rng);
            R().addRune(run, a); R().addRune(run, b); R().nextBattleSupply(run, -3);
            return 'A beam comes down on your wagons, but you dig out a ' + AG.Runes[a].name + ' and a ' + AG.Runes[b].name + '. (3 less supply next battle)';
          } },
      ],
    },
    {
      id: 'shrine', name: 'Shrine of the Swift', acts: [1, 2, 3],
      text: 'A wind-worn shrine to a forgotten god of first moves. Offerings of boots and spurs are piled at its base.',
      choices: [
        { label: 'Pray', desc: 'Pay 35 gold. Gain the Winged Boots relic (+1 SPD to your units).',
          available: (run) => (run.relics.indexOf('wingedBoots') >= 0 ? 'You already have them.' : run.gold >= 35 || 'Not enough gold.'),
          apply(run) { run.gold -= 35; R().addRelic(run, 'wingedBoots'); return 'A gust lifts you off your feet. Your pieces will move a little sooner now.'; } },
        { label: 'Leave an offering', desc: 'Pay 15 gold. Your next battle has 3 more supply.', available: (run) => run.gold >= 15 || 'Not enough gold.',
          apply(run) { run.gold -= 15; R().nextBattleSupply(run, 3); return 'The wind is at your back. (+3 supply next battle)'; } },
        { label: 'Move on', desc: '', apply() { return 'Some other day.'; } },
      ],
    },
    {
      id: 'egg', name: 'The Smouldering Egg', acts: [1, 2],
      text: 'A merchant is trying to sell a large, very hot egg. "Fell off a phoenix," he says. "Probably."',
      choices: [
        { label: 'Buy it (45 gold)', desc: 'Gain the Phoenix.',
          available: (run) => (run.gold >= 45 ? run.units.indexOf('phoenix') < 0 || 'You already have a Phoenix.' : 'Not enough gold.'),
          apply(run) { run.gold -= 45; R().addUnit(run, 'phoenix'); return 'The egg hatches in your pack that night. You have a Phoenix now.'; } },
        { label: 'Haggle', desc: 'Gain 15 gold.', apply(run) { run.gold += 15; return 'You talk him into paying you to take a look. He leaves confused.'; } },
      ],
    },
    {
      id: 'deserters', name: 'Deserters', acts: [1, 2, 3],
      text: 'A squad of deserters huddles around a fire. They have run from someone else’s war and are looking for a better one.',
      choices: [
        { label: 'Recruit them', desc: 'Gain a random common or uncommon unit.',
          available: (run) => R().unitPool(run, 'common').concat(R().unitPool(run, 'uncommon')).length > 0 || 'Nobody here you do not already have.',
          apply(run, rng) {
            const pool = R().unitPool(run, 'common').concat(R().unitPool(run, 'uncommon'));
            const u = rng.pick(pool); R().addUnit(run, u);
            return 'A ' + AG.Units[u].name + ' falls in with your army.';
          } },
        { label: 'Shake them down', desc: 'Gain 30 gold. Your next battle has 2 less supply.', apply(run) { run.gold += 30; R().nextBattleSupply(run, -2); return 'You take their purses. Word gets around, and fewer hands help with the baggage. (2 less supply next battle)'; } },
      ],
    },
    {
      id: 'library', name: 'The Drowned Library', acts: [2, 3],
      text: 'Half the library is underwater. The other half is on fire. One shelf of spellbooks is, improbably, fine.',
      choices: [
        { label: 'Read the old texts', desc: 'Gain a rare rune.', apply(run, rng) { const r = R().randomRune(run, rng, 'rare'); R().addRune(run, r); return 'You decipher a ' + AG.Runes[r].name + '.'; } },
        { label: 'Study tactics', desc: 'Train two random unit types. Your next battle has 4 less supply.',
          available: (run) => R().trainable(run).length > 0 || 'Every unit is fully trained.',
          apply(run, rng) {
            const list = rng.shuffle(R().trainable(run)).slice(0, 2);
            for (const d of list) R().train(run, d);
            R().nextBattleSupply(run, -4);
            return 'You study until dawn and march out half asleep. ' + list.map((d) => AG.Units[d].name).join(' and ') + ' improve. (4 less supply next battle)';
          } },
      ],
    },
    {
      id: 'mirrorPool', name: 'The Mirror Pool', acts: [2, 3],
      text: 'A perfectly still pool reflects a slightly better version of you.',
      choices: [
        { label: 'Gaze into it', desc: '+1 supply in every battle for the rest of the run.', apply(run) { run.supplyBonus = (run.supplyBonus || 0) + 1; return 'You see the board a little more clearly. (+1 supply in every battle)'; } },
        { label: 'Reach in', desc: 'Copy one of your runes.', pick: 'rune',
          available: (run) => run.runes.length > 0 || 'You have no runes.',
          apply(run, rng, rune) { R().addRune(run, rune); return 'You draw out a perfect copy of your ' + AG.Runes[rune].name + '.'; } },
      ],
    },
    {
      id: 'oldChampion', name: 'Ghost of the Old Champion', acts: [2, 3],
      text: 'A spectral knight bars the bridge. "None pass without a game," it intones, and its ghostly army takes the far side of the board.',
      choices: [
        { label: 'Accept the game', desc: 'A hard battle. Win a relic.',
          apply() { return { text: 'The ghost bows and the pieces take their places.', battle: 'ghostDuel', bonus: { relic: true, gold: 20 } }; } },
        { label: 'Bow and go around', desc: '', apply() { return 'The ghost watches you leave with something like disappointment.'; } },
      ],
    },
  ];

  AG.eventById = function (id) { return AG.Events.find((e) => e.id === id); };
})(globalThis.AG = globalThis.AG || {});
