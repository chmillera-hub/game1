# Arcane Gambit

An auto-battling wizard chess roguelike. You are the general, not the player: draft wizard-chess pieces within a supply budget, give them talents and runes, place them on your side of the board and press **Begin battle**. The pieces then fight on their own, one unit at a time in speed order, using an AI that understands what every move, attack, ability and trait does, and tells you why it made each choice.

Open `index.html` in a browser to play. No build step and no dependencies.

## How it plays

- **Turn queue.** Every round, each unit acts once in order of speed (fastest first, ties go to your side). The strip above the board shows the queue live; chills and war cries reshuffle it mid-round.
- **Wizard chess movement.** Knights leap in an L, bishops slide diagonally, golems move like rooks, wizards teleport, shades step out of the shadows next to their prey. Each unit card shows a Chess Evolved-style diagram of where it moves and what it can hit.
- **Supply and slots.** Every fight sets a supply budget and a unit cap ("up to 3 units", "up to 6"). Units, talents and runes all cost supply.
- **Boards of every shape.** Squares, diamonds, octagons, long bridges, short-and-wide fords, hourglass halls, chasms you can knock enemies into, walls that block line of sight.
- **The AI.** On each turn a unit tries every square it can reach and every attack or ability it could use from there, simulates each one, and scores the result: what every piece is worth, how much damage each side could deal next turn, and how far each piece is from the fight. The chosen line is explained above the board ("Freezes the Troll before it can act", "Swaps the Shaman into our lines"), bonus damage from synergies floats over the target (Charge +2, Shatter +2, Marked +1), and "Show alternatives" lists the runner-up options it rejected.
- **Fatigue.** From round 12 an Arcane Storm hits every unit at the start of each round for 1, then 2, then 3 and so on. If three rounds pass without anyone being hurt, the storm arrives early, so nobody chases anybody in circles.
- **Retry with intent.** Battles are deterministic, so the same setup always plays out the same way. Lose, read the after-battle report (damage dealt and taken per unit, the enemy's biggest threats), change your army or placement, try again. In the war room, selecting a piece shows where it can move and strike, and "Show enemy reach" shades every square the enemy can hit on its first turn.
- **The run.** Three acts, each a branching Slay the Spire-style map of battles, elites, events, merchants, camps and treasure with a boss at the top. Wins recruit new unit types or runes; elites and bosses give relics. Defeats cost Resolve; at zero the run ends (Casual mode turns that off).
- **Skirmish.** Every unit and rune unlocked; pick any of the 40 fights and experiment.

Battle controls: Space pauses, → steps one turn, 1/2/3 set the speed, S skips to the result.

## Content

25 player units with three talents each, 15 runes, 26 relics, 40+ enemy types, 40 encounters across three acts plus event battles, 12 events, three bosses (the last is a full chess army: checkmate the Mad Grandmaster to win).

## Project layout

```
index.html            loads everything (plain script tags, works from file://)
css/style.css
js/core/              util, board geometry and line of sight, battle rules, AI
js/data/              passives, abilities, units, talents/runes/ranks, relics, encounters, events
js/game/run.js        the roguelike run: map, rewards, shop, camp, events, saves
js/ui/                DOM helpers, board renderer and animations, war room, battle screen, other screens
tests/                headless and browser tools (below)
tools/bundle.js       inline everything into one HTML file
```

The engine (`js/core`, `js/data`, `js/game`) has no DOM code and runs under Node.

## Tools

```
node tests/rules.js                                      # deterministic rule and AI checks
node tests/watch.js goblinSkirmish knight scout cleric   # watch one battle as text
node tests/balance.js --act 1 --n 24                     # random legal armies vs each encounter
node tests/runsim.js --runs 24                           # whole runs played by a simple bot
node tests/runsim.js --runs 48 --dump snaps.json         # record realistic mid-run collections
node tests/calibrate.js snaps.json --n 40                # replay every fight against them
node tests/fuzz.js --n 4                                 # invariant fuzzer: random armies, relics, every encounter
node tests/smoke.js [outDir] [--mobile]                  # browser play-through with screenshots (Playwright)
node tests/tour.js [outDir] [--mobile]                   # visit every screen
node tests/longrun.js 10 [--mobile]                      # drive the real UI through ten floors of a run
node tools/bundle.js dist/arcane-gambit.html             # single-file build
```
