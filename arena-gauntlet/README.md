# Arena Gauntlet

A single-player tactics roguelike in the style of classic isometric arena battles
(think Tactics Arena Online meets Slay the Spire). Scout the enemy army, spend
Command Points to field a counter, and fight across three acts and three bosses.

## Play

Open `index.html` in a browser. No build step or server needed. Battles play best
on a phone turned sideways.

## How it works

- **War Room**: before each battle you see the whole enemy army. Deploy units within
  your Command Point budget; every point left unspent pays gold if you win.
- **Combat**: each ready unit moves and acts once per turn, then picks a facing.
  Block works from the front, half from the side, never from behind. Armor reduces
  physical damage; magic ignores both. Acting starts a unit's Recover timer.
- **Missions**: rout the enemy, burn their War Banner, break a prison cage, kill a
  Commander, hold a shrine, or survive. Bonus goals (guarded loot, fast wins, no
  losses, fielding a unit that sat out last battle) pay extra.
- **Between battles**: recruits, talents, promotions, relics, shops, events, rest.

## Code

| File | Purpose |
| --- | --- |
| `js/data.js` | Units, talents, relics, warbands, encounters |
| `js/engine.js` | Battle rules (pure logic, emits animation events) |
| `js/ai.js` | Enemy commander |
| `js/run.js` | Campaign map, missions, economy, rewards, saving |
| `js/sprites.js`, `js/render.js` | Procedural sprites and the isometric board |
| `js/ui.js`, `js/main.js` | Screens and touch controls |

## Tests

```
node tests/engine.test.js   # rule checks
node tests/sim.js 200       # AI-vs-AI balance by unit type
node tests/chaos.js 200     # random ranks, talents, relics and bosses
node tests/run.test.js 20   # whole campaigns played by the AI
```
