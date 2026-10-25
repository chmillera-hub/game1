/* Tower events, one halfway up each act. Most change one of your unit types
   for the rest of the run: a talent learned by heart (always on, free),
   stats traded for other stats, a new trait, two types fused into one.
   A choice may need a pick from the player:
     pick: 'unit'      one of your unit types (choice.filter(run, def) narrows it)
           'trainable' a unit type that can still be trained
           'talent'    a unit type and one of its talents it has not learned
           'rune'      one of your runes
           'fuse'      two unit types: the first is given up into the second
   available(run) returns true or the reason it is not; apply(run, rng,
   picked) returns the outcome text, or { text, battle, bonus } to start a
   fight. */
(function (AG) {
  'use strict';
  const R = () => AG.Run;
  const name = (def) => AG.Units[def].name;
  // A unit type's name in the plural: Frost Witches, Bannermen, Phoenixes.
  const names = (def) => {
    const n = name(def);
    return /man$/.test(n) ? n.slice(0, -3) + 'men' : /(ch|sh|x|s)$/.test(n) ? n + 'es' : n + 's';
  };
  const talentName = (t) => AG.Talents[t].name;
  // Unit-type picks some choices need.
  const hasAbility = (run, def) => AG.Units[def].abilities && AG.Units[def].abilities.length > 0;
  const hasAttack = (run, def) => !!AG.Units[def].attack;
  const lacks = (pas) => (run, def) => {
    const m = R().modOf(run, def);
    return !(AG.Units[def].passives || {})[pas] && !(m && m.passives && m.passives[pas]);
  };
  const anyUnit = (filter, why) => (run) => run.units.some((d) => !filter || filter(run, d)) || why;
  const canLearn = (run) => run.units.some((d) => R().learnable(run, d).length) || 'Your units know every talent already.';
  const spare = (run) => run.units.length > 3 || 'You need more than three unit types to give one up.';

  const learn = (verb) => (run, rng, p) => {
    R().modify(run, p.def, { innate: p.talent });
    return 'Your ' + names(p.def) + ' ' + verb + ' ' + talentName(p.talent) + ' by heart. From now on they always have it, free.';
  };
  const change = (c, text) => (run, rng, def) => { R().modify(run, def, c); return text.replace('%', names(def)); };

  AG.Events = [
    {
      id: 'tutor', name: 'The Wandering Tutor', acts: [1, 2, 3],
      text: 'An old grandmaster sits beside the stairs with a travelling board. "Your pieces move like amateurs," she says. "I can drill one of them until a trick is second nature. Or I can work the whole rank of them hard."',
      choices: [
        { label: 'Learn a talent by heart', desc: 'Pick a unit type and one of its talents: it always has that talent, free, without using a talent slot.', pick: 'talent',
          available: canLearn, apply: learn('learn') },
        { label: 'Drill the ranks', desc: 'Train one unit type a rank, for free.', pick: 'trainable',
          available: (run) => R().trainable(run).length > 0 || 'Every unit is fully trained.',
          apply(run, rng, def) { R().train(run, def); return 'Your ' + names(def) + ' are now ' + AG.RANKS[run.ranks[def]] + 's.'; } },
        { label: 'Thank her and leave', desc: '', apply() { return 'You leave her to her endgame studies.'; } },
      ],
    },
    {
      id: 'blackBoard', name: 'The Black Glass Board', acts: [1, 2, 3],
      text: 'A chessboard of black glass stands alone on the landing. A single piece waits on it, warm and humming. The board wants a piece in return, and it is not fussy about which.',
      choices: [
        { label: 'Take the piece', desc: 'Gain a random rare unit. Your next battle has 4 less supply.',
          available: (run) => R().unitPool(run, 'rare').length > 0 || 'You already command every rare unit.',
          apply(run, rng) { const u = rng.pick(R().unitPool(run, 'rare')); R().addUnit(run, u); R().nextBattleSupply(run, -4); return 'The ' + name(u) + ' joins you. The board keeps something back: 4 less supply in your next battle.'; } },
        { label: 'Feed it a piece', desc: 'Give up one of your unit types for good. Every other unit type you have gains +2 HP.', pick: 'unit',
          available: spare,
          apply(run, rng, def) {
            R().removeUnit(run, def);
            for (const d of run.units) R().modify(run, d, { hp: 2 });
            return 'The board swallows your ' + names(def) + ' whole. The rest of your army feels heavier, harder to break. (+2 HP to every other unit type)';
          } },
        { label: 'Leave it', desc: '', apply() { return 'You back away slowly.'; } },
      ],
    },
    {
      id: 'toll', name: 'The Goblin Toll', acts: [1],
      text: 'A rope across the stairs, a sign that says TOLL, and six goblins who have clearly never been paid. Their fighting style is filthy and, you have to admit, effective.',
      choices: [
        { label: 'Fight through', desc: 'A battle. Win for 40 gold and the usual spoils.',
          apply() { return { text: 'You draw steel. The goblins look delighted.', battle: 'goblinToll', bonus: { gold: 40 } }; } },
        { label: 'Learn their dirty tricks', desc: 'Pick a unit type: +1 ATK, but −2 HP, for good.', pick: 'unit',
          apply: change({ atk: 1, hp: -2 }, 'Your % learn to kick, bite and gouge. They hit harder and stop worrying about getting hurt. (+1 ATK, −2 HP)') },
        { label: 'Sneak around', desc: 'Your next battle has 2 less supply.', apply(run) { R().nextBattleSupply(run, -2); return 'You wade through a bramble thicket for an hour and lose some kit on the way. (2 less supply next battle)'; } },
      ],
    },
    {
      id: 'fountain', name: 'Fountain of Mana', acts: [1, 2, 3],
      text: 'Glowing water bubbles up from a cracked flagstone. It smells of ozone and old libraries, and the air above it hums with half-cast spells.',
      choices: [
        { label: 'Anoint a spellcaster', desc: 'Pick a unit type with an ability: its abilities recharge a turn faster, for good.', pick: 'unit',
          filter: (run, d) => hasAbility(run, d) && lacks('spellweaver')(run, d),
          available: anyUnit((run, d) => hasAbility(run, d) && lacks('spellweaver')(run, d), 'None of your unit types has an ability to quicken.'),
          apply: change({ passives: { spellweaver: {} } }, 'Your % come up from the water crackling. Their spells come back a turn sooner.') },
        { label: 'Bathe in it', desc: 'Pick a unit type: +3 HP, but −1 SPD, for good.', pick: 'unit',
          apply: change({ hp: 3, spd: -1 }, 'Your % soak until their skin glows. Tougher, and a little waterlogged. (+3 HP, −1 SPD)') },
        { label: 'Fill a vial', desc: 'Gain the Rune of Warding.', apply(run) { R().addRune(run, 'warding'); return 'The vial glows faintly. Rune of Warding gained.'; } },
      ],
    },
    {
      id: 'clockmaker', name: 'The Clockmaker', acts: [1, 2, 3],
      text: 'A workshop wedged into the tower wall, full of ticking. The clockmaker peers at your pieces through three pairs of spectacles. "Wonderful mechanisms. Terribly slow. I could fix that."',
      choices: [
        { label: 'Wind one up', desc: 'Pick a unit type: +1 SPD, but −2 HP, for good.', pick: 'unit',
          apply: change({ spd: 1, hp: -2 }, 'Your % tick faster now, and rattle a little when they run. (+1 SPD, −2 HP)') },
        { label: 'Fit a spring', desc: 'Pick a unit type with an attack: after attacking it may slip up to 2 squares away (Hit & Run), for good.', pick: 'unit',
          filter: (run, d) => hasAttack(run, d) && lacks('hitAndRun')(run, d),
          available: anyUnit((run, d) => hasAttack(run, d) && lacks('hitAndRun')(run, d), 'Every unit type already darts away.'),
          apply: change({ passives: { hitAndRun: { n: 2 } } }, 'Your % strike and spring back out of reach. (Hit & Run)') },
        { label: 'Buy the cracked hourglass', desc: 'Pay 55 gold for the Cracked Hourglass relic.',
          available: (run) => (run.relics.indexOf('hourglass') >= 0 ? 'You already have it.' : run.gold >= 55 || 'Not enough gold.'),
          apply(run) { run.gold -= 55; R().addRelic(run, 'hourglass'); return 'It runs a little fast. In the first round, your quickest piece will get a second turn.'; } },
      ],
    },
    {
      id: 'armory', name: 'Abandoned Armory', acts: [1, 2, 3],
      text: 'A collapsed armory on a landing, its rune racks half buried under salvaged plate. The forge in the corner is still warm.',
      choices: [
        { label: 'Reforge a rune', desc: 'Pick one of your runes: it becomes a random rune of the next rarity up.', pick: 'rune',
          available: (run) => run.runes.length > 0 || 'You have no runes.',
          apply(run, rng, rune) {
            const up = { common: 'uncommon', uncommon: 'rare', rare: 'rare' }[AG.Runes[rune].rarity];
            run.runes.splice(run.runes.indexOf(rune), 1);
            const r = R().randomRune(run, rng, up);
            R().addRune(run, r);
            return 'The ' + AG.Runes[rune].name + ' cracks in the heat and comes out as a ' + AG.Runes[r].name + '.';
          } },
        { label: 'Strap on salvaged plate', desc: 'Pick a unit type: +1 armor, but −1 SPD, for good.', pick: 'unit',
          apply: change({ armor: 1, spd: -1 }, 'Your % clank up the stairs in mismatched plate. (+1 armor, −1 SPD)') },
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
      text: 'A wind-worn shrine to a forgotten god of first moves. Boots and spurs are piled at its base, and a vow is carved over the door: SPEED, AND NOTHING ELSE.',
      choices: [
        { label: 'Swear the vow', desc: 'Pick a unit type: +2 SPD, but −1 ATK, for good.', pick: 'unit',
          apply: change({ spd: 2, atk: -1 }, 'Your % swear to be first and leave their heavy weapons at the altar. (+2 SPD, −1 ATK)') },
        { label: 'Pray', desc: 'Pay 35 gold. Gain the Winged Boots relic (+1 SPD to all your units).',
          available: (run) => (run.relics.indexOf('wingedBoots') >= 0 ? 'You already have them.' : run.gold >= 35 || 'Not enough gold.'),
          apply(run) { run.gold -= 35; R().addRelic(run, 'wingedBoots'); return 'A gust lifts you off your feet. Your pieces will move a little sooner now.'; } },
        { label: 'Move on', desc: '', apply() { return 'Some other day.'; } },
      ],
    },
    {
      id: 'egg', name: 'The Smouldering Egg', acts: [1, 2],
      text: 'A merchant is trying to sell a large, very hot egg. "Fell off a phoenix," he says. "Probably." It is too hot to hold for long, but something could be forged in that heat.',
      choices: [
        { label: 'Buy it (45 gold)', desc: 'Gain the Phoenix.',
          available: (run) => (run.gold >= 45 ? run.units.indexOf('phoenix') < 0 || 'You already have a Phoenix.' : 'Not enough gold.'),
          apply(run) { run.gold -= 45; R().addUnit(run, 'phoenix'); return 'The egg hatches in your pack that night. You have a Phoenix now.'; } },
        { label: 'Temper a unit in its heat', desc: 'Pick a unit type: +2 ATK, but −3 HP, for good.', pick: 'unit',
          apply: change({ atk: 2, hp: -3 }, 'Your % hold the egg until their hands blister. They come away fierce and a little scorched. (+2 ATK, −3 HP)') },
        { label: 'Smash it', desc: 'Gain the Ember Heart relic. Your next battle has 3 less supply.',
          available: (run) => run.relics.indexOf('emberHeart') < 0 || 'You already have it.',
          apply(run) { R().addRelic(run, 'emberHeart'); R().nextBattleSupply(run, -3); return 'The shell bursts into a heart of embers. The merchant demands compensation in kit. (3 less supply next battle)'; } },
      ],
    },
    {
      id: 'deserters', name: 'Deserters', acts: [1, 2, 3],
      text: 'A squad of deserters huddles around a fire. They have run from someone else’s war, and they know a few things about staying alive.',
      choices: [
        { label: 'Recruit them', desc: 'Gain a random common or uncommon unit type, already trained to Veteran.',
          available: (run) => R().unitPool(run, 'common').concat(R().unitPool(run, 'uncommon')).length > 0 || 'Nobody here you do not already have.',
          apply(run, rng) {
            const u = rng.pick(R().unitPool(run, 'common').concat(R().unitPool(run, 'uncommon')));
            R().addUnit(run, u);
            R().train(run, u);
            return 'A squad of ' + names(u) + ' falls in with your army, already Veterans.';
          } },
        { label: 'Learn to survive', desc: 'Pick a unit type: it starts every battle in stealth (Shadowed), for good.', pick: 'unit',
          filter: (run, d) => lacks('evasive')(run, d),
          available: anyUnit((run, d) => lacks('evasive')(run, d), 'Your units are already hard to see.'),
          apply: change({ passives: { evasive: {} } }, 'Your % learn to keep their heads down. They start every battle unseen until they strike. (Shadowed)') },
        { label: 'Send them home', desc: '', apply() { return 'They go, grateful and a little disappointed.'; } },
      ],
    },
    {
      id: 'library', name: 'The Drowned Library', acts: [2, 3],
      text: 'Half the library is underwater. The other half is on fire. One shelf of battle manuals is, improbably, fine.',
      choices: [
        { label: 'Memorise a manual', desc: 'Pick a unit type and one of its talents: it always has that talent, free, without using a talent slot.', pick: 'talent',
          available: canLearn, apply: learn('commit') },
        { label: 'Read the old texts', desc: 'Gain a rare rune.', apply(run, rng) { const r = R().randomRune(run, rng, 'rare'); R().addRune(run, r); return 'You decipher a ' + AG.Runes[r].name + '.'; } },
        { label: 'Study all night', desc: 'Train two random unit types. Your next battle has 4 less supply.',
          available: (run) => R().trainable(run).length > 0 || 'Every unit is fully trained.',
          apply(run, rng) {
            const list = rng.shuffle(R().trainable(run)).slice(0, 2);
            for (const d of list) R().train(run, d);
            R().nextBattleSupply(run, -4);
            return 'You study until dawn and march out half asleep. ' + list.map(name).join(' and ') + ' improve. (4 less supply next battle)';
          } },
      ],
    },
    {
      id: 'mirrorPool', name: 'The Mirror Pool', acts: [2, 3],
      text: 'A perfectly still pool reflects a slightly better version of your army. One of the reflections is waving.',
      choices: [
        { label: 'Step through', desc: 'Pick a unit type: a decoy absorbs the first hit each of them would take (Mirror Image), for good.', pick: 'unit',
          filter: (run, d) => lacks('mirrorImage')(run, d),
          available: anyUnit((run, d) => lacks('mirrorImage')(run, d), 'Your units already have reflections.'),
          apply: change({ passives: { mirrorImage: {} } }, 'Your % come back out with their reflections still attached. (Mirror Image)') },
        { label: 'Reach in', desc: 'Copy one of your runes.', pick: 'rune',
          available: (run) => run.runes.length > 0 || 'You have no runes.',
          apply(run, rng, rune) { R().addRune(run, rune); return 'You draw out a perfect copy of your ' + AG.Runes[rune].name + '.'; } },
        { label: 'Gaze into it', desc: '+1 supply in every battle for the rest of the run.', apply(run) { run.supplyBonus = (run.supplyBonus || 0) + 1; return 'You see the board a little more clearly. (+1 supply in every battle)'; } },
      ],
    },
    {
      id: 'soulForge', name: 'The Soul Forge', acts: [2, 3],
      text: 'An anvil of white fire on a landing with no stairs leading away. The smith has no face, only an open hand. It can melt one kind of piece into another.',
      choices: [
        { label: 'Fuse two unit types', desc: 'Pick a unit type to give up, then one to receive it: the second gains half the first one’s HP and +1 ATK, for good.', pick: 'fuse',
          available: spare,
          apply(run, rng, p) {
            const hp = Math.ceil(R().unitFor(run, p.from).maxHp / 2);
            R().removeUnit(run, p.from);
            R().modify(run, p.into, { hp, atk: 1 });
            return 'Your ' + names(p.from) + ' are poured into your ' + names(p.into) + '. (+' + hp + ' HP, +1 ATK)';
          } },
        { label: 'Temper', desc: 'Pick a unit type: +2 HP and +1 armor, but −1 ATK, for good.', pick: 'unit',
          apply: change({ hp: 2, armor: 1, atk: -1 }, 'Your % come off the anvil dense and slow to anger. (+2 HP, +1 armor, −1 ATK)') },
        { label: 'Walk away', desc: '', apply() { return 'The hand closes, patiently.'; } },
      ],
    },
    {
      id: 'oldChampion', name: 'Ghost of the Old Champion', acts: [2, 3],
      text: 'A spectral knight bars the stairs. "None pass without a game," it intones, and its ghostly army takes the far side of the board. "Or, if you are afraid, a lesson."',
      choices: [
        { label: 'Accept the game', desc: 'A hard battle. Win a relic.',
          apply() { return { text: 'The ghost bows and the pieces take their places.', battle: 'ghostDuel', bonus: { relic: true, gold: 20 } }; } },
        { label: 'Ask for a lesson', desc: 'Pick a unit type and one of its talents: it always has that talent, free, without using a talent slot.', pick: 'talent',
          available: canLearn, apply: learn('are taught') },
        { label: 'Bow and go around', desc: '', apply() { return 'The ghost watches you leave with something like disappointment.'; } },
      ],
    },
  ];

  AG.eventById = function (id) { return AG.Events.find((e) => e.id === id); };
})(globalThis.AG = globalThis.AG || {});
