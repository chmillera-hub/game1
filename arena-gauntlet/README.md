# Arena Gauntlet

A single-player tactics roguelike in the style of classic isometric arena battles
(think Tactics Arena Online meets Slay the Spire). Scout the enemy army, spend
Supply on a counter-army, and fight across three acts to the Ashen Tyrant.

## Play

Open `index.html` in a browser. No build step or server needed. Battles play best
on a phone turned sideways, but portrait works too.

## How it works

- **Supply**: each battle gives you Supply to spend. A unit costs its base price,
  plus its level, plus any ability, skill, gear or enchantment it carries.
  Spend it however you like: two Level 1 Knights (3 + 3), or one Level 2 Knight
  (3 + 2) with an extra ability. Loadouts are free to change between battles.
- **Commander level**: battles give XP, and elites and bosses give more. XP raises
  your commander level, from 14 Supply and 4 units on the field at Level 1 to
  33 Supply and 8 units at Level 10.
- **Unit levels**: Level 1 picks one of three abilities; the free one comes first
  and stronger picks cost extra Supply. For example, the Archer chooses Snare Shot,
  Poison Arrows or Smoke Screen. Level 2 (+2 Supply) gets more HP and power,
  another skill slot and a second pick of three. Level 3 (+5) adds a class mastery
  and a second gear slot.
- **Enchantments**: binding a scroll to a unit gives it a permanent power and a
  Supply surcharge. It cannot be undone or moved to another unit.
- **Damage**: physical hits are reduced by armor and block; magic is reduced by
  magic resistance. Both cap at 50%, and some units go as low as -50%: Specters
  shrug off steel but melt to spells, and Mage Knights do the reverse.
- **Combat**: each ready unit moves and acts once per turn, then picks a facing.
  Block works from the front, half from the side, never from behind. Acting
  starts a unit's Recover timer.
- **Reading the enemy**: tap any unit, yours or theirs, to see a small diagram of
  every attack: where it can aim and exactly which tiles one use hits (a Brute's
  maul strikes its target and the three tiles around it; a Witch's lightning runs
  five tiles straight). The board shows everywhere it could hit next turn.
- **Missions**: rout the enemy, burn a War Banner, break a prison cage, kill a
  Commander, hold a shrine, survive the waves, topple three totems, raze the
  buildings that send reinforcements, storm a castle gate, or stop a wagon convoy.
  Bonus goals (ghost-guarded loot, fast wins, no losses, blocking reinforcements,
  fielding a unit that sat out the last battle) pay extra.
- **Buildings and siege**: walls, gates, towers, totems, tents, crypts, dens,
  portals and barricades are buildings. Stone resists swords and spells alike,
  wood burns, and portals unravel under magic. Siege damage breaks them fast:
  the Trebuchet, the Siege Hammer, the Demolisher skill, a Blasting Charge, the
  Golem's Boulder Toss and the Sapper's Kit relic.
- **Reinforcements**: some battles send enemy waves at set turns, from the far
  edge or out of buildings. The War Room shows the schedule, and badges count
  down on each building. A turn ahead, red tiles mark where they land; standing
  on one blocks that arrival at a cost of 10 HP. Destroy a building and its
  remaining waves are cut off.
- **Defeat**: lose as often as you need. Retry with a new setup and +1 Supply per
  loss after the first (up to +3), or quit; Continue on the title screen returns
  to the same battle.
- **Between battles**: recruits, skills, gear, enchantment scrolls, relics, shops,
  events, and camps to drill, study or tinker.

## Code

| File | Purpose |
| --- | --- |
| `js/data.js` | Units, abilities, skills, gear, enchantments, relics, encounters |
| `js/engine.js` | Battle rules (pure logic, emits animation events) |
| `js/ai.js` | Enemy commander |
| `js/run.js` | Campaign map, Supply and XP, loadouts, missions, rewards, saving |
| `js/sprites.js`, `js/render.js` | Procedural sprites and the isometric board |
| `js/ui.js`, `js/main.js` | Screens and touch controls |

## Tests

```
node tests/engine.test.js        # rule checks
node tests/sim.js 200            # AI-vs-AI balance by unit type
node tests/chaos.js 200          # random loadouts, bosses, buildings and waves
node tests/run.test.js 20 knight # whole campaigns played by the AI, with retries
```
