# Hero Delve

A party-based dungeon crawl that plays itself, in the spirit of Diablo II's Forgotten Tower
and Guild Wars heroes. Built on the Arena Gauntlet engine (its battle rules, AI, art and
renderer), as a separate game: Arena Gauntlet is untouched.

## How it plays

- **Your party**: four heroes of any walking class plus your Cleric, who always comes. All
  are Level 3, each with their two level picks, three class talents, two skills and two
  pieces of gear. Change a hero's class from the party screen (a fresh hero of that class,
  kitted from what is free).
- **The stash**: the skills and gear you own, shared by the party; an item is on one hero
  at a time. It starts with a dozen common pieces.
- **The Forgotten Tower**: five floors, each a fresh 24x24 maze of rooms and two-wide
  corridors. Fog of war hides what the party has not seen; stepping into a room shows all of
  it. Floor 5 holds the Countess, with a guard, in the far room.
- **Begin**: the party explores and fights on its own. Monster packs sleep in their rooms
  and take no turns until a hero comes within 5 tiles in sight of one (walls block the view)
  or strikes one; then the whole pack wakes. Between fights the party walks to the nearest
  sleeping pack; during one, the battle AI fights as in Arena Gauntlet (one unit a side a
  turn). If a fight stalls, both sides waiting, the party goes for the nearest monster.
  Walking plays two and a half times faster than fighting.
- **Watching**: pause, change speed (1x, 2x, 4x), or tap: a monster, then Priority, sends
  everyone after it; a seen floor tile sends the party there; a hero, then Rally on, gathers
  the party round them. Clear the priority to let them roam again.
- **Floors**: clear every monster on a floor to take the stairs. HP carries over; a hero who
  fell gets up at the shrine on the stairs with 40% HP. The town portal (between floors, or
  from the menu) takes you back to swap kit; the delve waits on that floor.
- **Loot**: a pack wiped out may drop a skill or a piece of gear (more likely the deeper you
  go, with a small legendary chance from floor 4). The Countess always drops two, one of
  them legendary. Loot is kept whether the delve ends in victory or defeat.

## What is new on top of the Arena engine

- `js/dungeon.js`: the profile (party, stash, stats), floor generation, sleeping packs,
  exploring orders, fog of war, loot, and the floor-to-floor run.
- `js/engine.js`: sleeping packs (`asleep`, `pack`, `wakeCheck`, `wakePack`, `sightLine`).
- `js/ai.js`: sleeping monsters are neither threats nor targets; walking distances on big
  maps (999 for out of reach, no cap to the straight-line distance).
- `js/render.js`: the dungeon palette, stone walls (low on the near side so they never hide
  the heroes), fog of war, a camera that glides after the party, a "!" when a pack wakes.
- `js/data.js`, `js/sprites.js`: the Countess.
- `js/ui.js`: town, party and kit, the delve screen.

## Tests

- `node tests/delve.test.js`: floors (connected, safe start, the Countess at the bottom),
  sleeping and waking, exploring, kit rules, a whole delve.
- `node tests/delve-sim.js [runs]`: whole delves headless; `PARTY=scout,assassin,witch,golem`
  picks the four heroes.
