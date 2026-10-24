# Arena Gauntlet

A single-player auto-battler roguelike in the style of classic isometric arena
battles (think Tactics Arena Online meets Slay the Spire). Scout the enemy army,
spend Supply on a counter-army, set it up, and watch it fight across three acts to
the Ashen Tyrant.

## Play

Open `index.html` in a browser. No build step or server needed. Battles play best
on a phone turned sideways, but portrait works too.

## How it works

- **War Room**: tap a unit card to deploy it, then a blue tile to place it, or another
  of your units to swap places; a move lets go of the unit, so the next tap does not
  move it again. A picked unit's loadout opens right under your army: what each part
  costs (Knight 3 + Level 2 2 + Guardian 1 ...), its level, and a button for each
  ability, talent, skill and gear slot. Tap the Supply bar to see what every deployed
  unit costs. Details opens the full sheet; Begin battle stays in view at the bottom.
- **Supply**: each battle gives you Supply to spend. A unit costs its base price,
  plus its level, plus any ability, skill, gear or enchantment it carries.
  Spend it however you like: two Level 1 Knights (3 + 3), or one Level 2 Knight
  (3 + 2) with an extra ability. Loadouts are free to change between battles.
- **Auto**: the War Room's Auto button builds an army for you. It weighs the
  enemy's armor against its magic resistance: magic attackers against armored
  armies, physical ones against magic-resistant armies, a mix otherwise. The
  scout report shows the same comparison. If a bonus goal asks for a unit, Auto
  always fields it, and the War Room lists that unit first.
- **Commander level**: battles give XP, and elites and bosses give more. XP raises
  your commander level, from 14 Supply and 4 units on the field at Level 1 to
  33 Supply and 8 units at Level 10.
- **Unit levels**: Level 1 picks an ability: the free one, or an active ability
  that costs extra Supply. For example, the Archer chooses Snare Shot or Smoke
  Screen. Level 2 (+2 Supply) gets more HP and damage,
  another skill slot, a talent slot and a second ability pick. Level 3 (+5) adds a
  class mastery, a third talent slot and a second gear slot.
- **Talents**: the passives that cost Supply (Shield Wall, Riposte, Poison Arrows
  and the like) are class talents. Every unit you get comes with one random talent
  of its class, equipped (it costs Supply like any talent, and you can unequip it or
  move it to another unit of the class). You find more in shops and battle spoils,
  and only for classes in your army. A unit has one talent slot per level, three at
  Level 3, and can mix and match any of its class's talents you own (one copy of
  each per unit; each copy fits one unit at a time). The level picks keep the free
  option and the active abilities. The stronger talents turn up half as often, and
  copies you already own less often still, so a great combination takes hunting.
- **Enchantments**: binding a scroll to a unit gives it a permanent bonus and a
  Supply surcharge. It cannot be undone or moved to another unit.
- **Damage**: physical hits (marked with a sword) are reduced by armor and block;
  magic (a violet sparkle) is reduced by magic resistance. Armor and magic
  resistance both cap at 50%, and some units go as low as -50%: Specters shrug
  off steel but melt to spells, and Mage Knights do the reverse. A unit's DMG stat,
  its attacks and every damage preview show the damage-type icon.
- **Auto battle**: you build and place the army in the war room, tap Begin battle,
  and watch it fight; the same AI that runs the enemy runs your units, using their
  abilities and talents. Lost? Change the army and try again. Speed (1x, 2x, 4x),
  pause, skip-to-result and tap-a-unit-to-inspect are beside the board; 1x plays a
  little slower than the animations' full pace, to be easy to follow. The menu's
  Battles setting switches to commanding each turn yourself (the classic version
  lives on the `arena-gauntlet-tactics-classic` branch).
- **Priority**: while watching, tap an enemy unit, a building or a chest, then
  Priority. Your army goes all out for it, whatever the cost: every unit attacks it,
  or heads for the chest and takes it. A marker shows the target. Once it falls or is
  taken, the army goes back to normal orders; you can also clear it.
- **Loot on its own**: without a priority, your army drifts toward chests (more so
  when it is winning) and takes one in reach rather than make an ordinary attack,
  though a kill still comes first. It does not walk up to loot whose guards are
  asleep, but grabs it if a unit can reach it in one move.
- **Playing for the mission**: your army also knows the mission and its bonus goals.
  It goes for the Commander when killing it wins, hits the wagon nearest its way out
  first, presses harder toward the end of a "win within N turns" goal (but never off
  a shrine it must hold), and values stepping onto a red landing tile far more while
  a "block reinforcements" goal is open.
- **Taking turns**: the sides alternate one unit at a time, and the enemy goes
  first. Each side's units take its turns in a rotation, faster units first (Speed,
  SPD on the card: a Scout at 8 goes before a Knight at 2). A strip under the board
  shows who is next.
- **Cooldowns**: acting starts a unit's cooldown (CD on its card): it sits out that
  many of its own turns, and the next unit in line goes instead. Moving alone never
  starts a cooldown. Paralyzed units, and units with nothing in reach, sit out too;
  when every unit of a side must sit out, the side passes. Bosses sit out their
  first turn.
- **Regen**: some talents, gear, relics and units heal at the start of each of the
  unit's own turns (Living Moss 4, Healing Charm 3, the Furgon 3, the Healing Salve
  relic 1, Sacred Chalice 2, a Mending Light aura 2). Sources add up with no cap;
  unit cards and the battle log show it.
- **Fatigue**: from turn 30, each unit loses HP at the start of its turn, past armor
  and shields: 1 in the first round (the enemy's unit, then yours), 2 in the next,
  then 3 and so on, the same for both sides, like fatigue in Hearthstone. The top bar
  shows this round's hit. Reinforcements stop. Big units and regen last longest; the last side
  standing wins. A tough tank can win a long battle on its own.
- **Combat**: block works from the front, half from the side, never from behind.
  Roots, weakness, paralysis and frenzy count the affected unit's own turns; a mark
  counts the attacker side's turns.
- **Board features**: tap a rock, tree, water, lava, a treasure chest, the shrine,
  fire, smoke, caltrops or a red landing tile to see what it does: whether it blocks
  movement or attacks, what loot pays and which tiles wake its guards, and how long
  a hazard lasts. A unit's panel also says what it is standing on.
- **Reading the enemy**: tap any unit, yours or theirs, to see a small diagram of
  every attack: where it can aim and exactly which tiles one use hits (a Brute's
  maul strikes its target and the three tiles around it; a Witch's lightning runs
  five tiles straight). The board shows everywhere it could hit on its next move.
- **Missions**: defeat every enemy, burn a War Banner, break a prison cage, kill a
  Commander, hold a shrine, survive the waves, topple three totems, raze the
  buildings that send reinforcements, storm a castle gate, or stop a wagon convoy.
  Bonus goals (ghost-guarded loot, fast wins, no losses, blocking reinforcements,
  fielding a unit that sat out the last battle) pay extra.
- **Buildings and siege**: walls, gates, towers, totems, tents, crypts, dens,
  portals and barricades are buildings. Stone resists swords and spells alike,
  wood burns, and portals unravel under magic. Siege damage breaks them fast:
  the Trebuchet, the Siege Hammer, the Demolisher skill, a Blasting Charge, the
  Golem's Boulder Toss and the Sapper's Kit relic.
- **Reinforcements**: some battles send enemy waves on set turns, from the far
  edge or out of buildings. The War Room shows the schedule, and badges count
  down on each building. Waves land after the enemy's move; a turn ahead, red
  tiles mark where. Standing on one blocks that arrival at a cost of 10 HP.
  Destroy a building and its remaining waves are cut off.
- **Defeat**: lose as often as you need. Retry with a new setup, or quit; Continue
  on the title screen returns to the same battle.
- **Missed bonus goals**: a win that misses a bonus goal (say, winning within 30
  turns) pauses before the rewards and shows which goals you met. Retry the battle
  with a new setup (the win and its rewards are set aside, and it does not count as
  a loss), or keep the win and continue. You can retry as often as you like.
- **Between battles**: recruits, skills, gear, enchantment scrolls, relics, shops,
  events, and camps to drill, study or tinker. A shop sells one of each kind of thing,
  eight at most: a recruit, a talent, a skill, gear, an enchantment scroll, a relic,
  a Supply Cache and a War Manual.
- **Music**: synthesized in the browser like the sound effects, no audio files. Two
  camp tracks between battles (Campfire, a lute and flute; Tavern Jig, a fiddle jig),
  two battle tracks (March of Iron, war drums and horns; Clash of Steel, a faster
  charge) and a boss track (The Ashen Tyrant, choir and great drums). Each mood moves
  on to its next track every couple of loops, and battles alternate. The menu has its
  own Music switch, apart from Sound.

## Code

| File | Purpose |
| --- | --- |
| `js/data.js` | Units, abilities, skills, gear, enchantments, relics, encounters |
| `js/engine.js` | Battle rules (pure logic, emits animation events) |
| `js/ai.js` | Enemy commander |
| `js/run.js` | Campaign map, Supply and XP, loadouts, missions, rewards, saving |
| `js/sprites.js`, `js/render.js` | Procedural sprites and the isometric board |
| `js/ui.js`, `js/main.js` | Screens and touch controls |
| `js/audio.js`, `js/music.js` | Synthesized sound effects and background music |

## Tests

```
node tests/engine.test.js        # rule checks
node tests/deploy.test.js        # the War Room's Auto button
node tests/goals.test.js         # bonus goals, and retrying a won battle for them
node tests/priority.test.js      # the priority target your army goes all out for
node tests/objectives.test.js    # your army playing for the mission and bonus goals
node tests/music.test.js         # the music's notation: every bar the right length
node tests/sim.js 200            # AI-vs-AI balance by unit type
node tests/chaos.js 200          # random loadouts, bosses, buildings and waves
node tests/run.test.js 20 knight # whole campaigns played by the AI, with retries
```
