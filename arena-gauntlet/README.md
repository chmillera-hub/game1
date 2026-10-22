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
- **Missions**: rout the enemy, burn a War Banner, break a prison cage, kill a
  Commander, hold a shrine, survive, storm a castle gate, or stop a wagon convoy.
  Bonus goals (ghost-guarded loot, fast wins, no losses, fielding a unit that sat
  out the last battle) pay extra.
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
node tests/chaos.js 200          # random levels, abilities, items and bosses
node tests/run.test.js 20 knight # whole campaigns played by the AI, with retries
```
