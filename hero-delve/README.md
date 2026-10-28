# Hero Delve

A party-based dungeon crawl that plays itself, in the spirit of Diablo II's Forgotten Tower
and Guild Wars heroes. Built on the Arena Gauntlet engine (its battle rules, AI, art and
renderer), as a separate game: Arena Gauntlet is untouched.

## How it plays

- **Your party**: four heroes of any walking class plus your Cleric, who always comes. They
  start at Level 1 and level up as they fight: every monster slain gives the whole party XP
  (more for bigger monsters and higher levels, much more for a Champion or the Countess,
  little for monsters far below you).
- **Levels and skill points**: each level makes a hero tougher (+8% HP) and stronger (+5%
  power) and gives one skill point. Points buy the class's talents (the first tier from
  Level 2, the stronger tier from Level 5) or training: Vitality (+8% HP a point) and Might
  (+5% power a point). Heroes on Auto spend their own points and put new finds in empty
  slots (never swapping what they hold); turn Auto off to choose yourself. Reset gives every
  point back. Level 3 opens a second gear slot, Level 4 the class's second
  ability, Level 5 a second skill slot, Level 8 its mastery, Level 10 a third gear slot,
  Level 12 a third skill slot. Changing class keeps the level.
- **The stash and loot**: the skills and gear you own, shared by the party; an item is on one
  hero at a time. Packs you wipe out may drop more, better the deeper you go; a floor's
  Champion always drops one of the better kind, the Countess two (one legendary). Equip
  anything any time, even mid-floor (tap a hero, then Kit, or the menu): changes take hold
  once the fight in hand is over. XP and items are never lost.
- **The Forgotten Tower**: five floors, each a fresh 24x24 maze of rooms and two-wide
  corridors under fog of war. Monsters on floor 1 are Levels 1-2, on floor 5 Levels 7-8.
  Each floor has a **Champion**: a named, crowned monster three levels above the floor's
  strongest, with twice the HP, in a room of its own away from the way in. Floor 5 holds the
  Countess (Level 10) with a guard, in the far room.
- **Rounds**: every unit, hero or monster, takes one turn a round, fastest first (the turn
  order strip shows this round and the next). A unit that is cooling down or paralyzed passes
  its turn as it comes.
- **Levels on health bars**: each health bar carries its unit's level. A monster's badge is
  grey well below your party, plain about even, amber one level above, red two or more above.
  A level edge counts in a fight: each level up on the target hits 10% harder, each level
  down 10% softer.
- **Begin**: the party explores and fights on its own. Monster packs sleep in their rooms and
  take no turns until a hero comes within 5 tiles in sight of one, or strikes one; then the
  whole pack wakes. Between fights the party walks to the nearest pack it can take on. It
  leaves red packs (and packs within sight of them) for later while there is anything else to
  fight, and walks round them where there is a way. If it wakes one by accident, it falls
  back to the way in, at most twice for the same pack (after that it stands and fights).
  If a fight stalls, the party goes for the nearest monster.
- **Watching**: pause, change speed (1x, 2x, 4x), or tap: a monster, then Priority, sends
  everyone after it (red or not); a seen floor tile sends the party there; a hero, then Rally
  on, gathers the party round them, or Kit opens their sheet. **Retreat** runs for the way in.
- **No lost floors**: a pack whose prey gets more than 11 tiles from its lair gives up the
  chase: it goes home at full health and goes back to sleep (its dead stay dead). A fight
  where nobody lands a blow for 8 rounds ends the same way. A hero who falls gets up at the
  way in, at half health, once no pack is awake, and runs to catch up (the party waits). A
  party wiped out gets up at the way in at full health, and the packs it was fighting heal.
  So a strong pack can always be beaten by throwing the party at it again and again; it is
  just quicker to level up elsewhere first. Out of a fight the party heals 10% a round and
  its once-a-fight abilities come back.
- **Floors**: clear every monster on a floor to take the stairs. The next floor starts with
  everyone up and rested. The town portal (between floors, or from the menu) takes you back;
  a floor left halfway starts over when you come back.

## What is new on top of the Arena engine

- `js/dungeon.js`: the profile (party, levels, skill points, stash), floor generation with a
  Champion a floor, sleeping packs, exploring orders (danger levels, routes round red packs,
  falling back, regrouping), fog of war, XP and loot, the floor-to-floor run.
- `js/engine.js`:
  - round battles (`rounds`: every unit once a round in speed order, `roundOrder`);
  - delve levels (`dlv`, `hpMul`, `powMul`, the level edge in `calcHit`, Champions);
  - sleeping packs (`asleep`, `pack`, `wakeCheck`, `wakePack`, `sightLine`);
  - the delve rules (`delveRound`: leashes, stale fights, respawns at the way in, wipes,
    rest between fights; `rebuildUnit` for level ups and kit changes);
  - flyers keep to the corridors.
- `js/ai.js`: sleeping monsters are neither threats nor targets; walking distances on big
  maps; threats counted by rounds; a stalled fight pressed toward its target.
- `js/render.js`: the dungeon palette, stone walls, fog of war, a camera that glides after
  the party, level badges coloured by danger, Champions' crowns and auras, level-up and
  respawn effects, packs giving up.
- `js/data.js`, `js/sprites.js`: the Countess.
- `js/ui.js`: town, party and hero sheets (levels, skill points, kit), the delve screen
  (round order, Retreat, Kit, the log).

## Tests

- `node tests/delve.test.js`: floors and Champions, sleeping and waking, rounds, levels and
  skill points, leashes, wipes and respawns, the level edge, exploring round danger, a delve.
- `node tests/delve-sim.js [runs]`: whole delves headless. `PARTY=scout,assassin,witch,golem`
  picks the four heroes, `LV=5` starts them at that level, `RUSH=1` sends the party straight
  at each floor's Champion.
