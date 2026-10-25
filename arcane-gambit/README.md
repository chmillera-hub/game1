# Arcane Gambit

An auto-battling wizard chess roguelike. You are the general, not the player: draft wizard-chess pieces, field as many as your supply allows, give them talents and runes, place them on your side of the board and press **Begin battle**. The pieces then fight on their own, the two sides taking turns one piece at a time as in chess, using an AI that understands what every move, attack, ability and trait does, and tells you why it made each choice.

Open `index.html` in a browser to play. No build step and no dependencies.

## How it plays

- **Turns.** The two sides take turns, one piece at a time, as in chess. Each side moves its pieces fastest first and every piece moves once a round; a side with more pieces gets its extra turns spread evenly through the round. The side with the quicker lead piece opens the round (yours on a tie). The strip above the board shows the order live; chills and war cries reshuffle it mid-round.
- **Wizard chess movement.** Knights leap in an L, bishops slide diagonally, golems move like rooks, wizards teleport, shades step out of the shadows next to their prey. Each unit card shows a Chess Evolved-style diagram of where it moves and what it can hit.
- **Supply, and nothing else.** Every fight sets a supply budget; units, talents and runes all cost supply. There is no cap on how many units you bring beyond the supply and the deploy squares. **Auto-deploy** fills the board for you: as many units as the supply allows, then any leftover supply turns cheap pieces into stronger ones.
- **Boards of every shape.** Squares, diamonds, octagons, long bridges, short-and-wide fords, hourglass halls, chasms you can knock enemies into, walls that block line of sight.
- **The AI.** On each turn a unit tries every square it can reach and every attack or ability it could use from there, simulates each one, and scores the result: what every piece is worth, how much damage each side could deal next turn, and how far each piece is from the fight. The chosen line is explained above the board ("Freezes the Troll before it can act", "Swaps the Shaman into our lines"), bonus damage from synergies floats over the target (Charge +2, Shatter +2, Marked +1), and "Show alternatives" lists the runner-up options it rejected.
- **Fatigue.** From round 12 an Arcane Storm hits every unit at once at the start of each round for 1, then 2, then 3 and so on. If three rounds pass without anyone being hurt (five before the first blow), the storm arrives early, so nobody chases anybody in circles. A battle still undecided after round 24 is lost, except in fights where the goal is to survive.
- **Retry for free.** Losing costs nothing. Battles are deterministic, so the same setup always plays out the same way: read the after-battle report (damage dealt and taken per unit, the enemy's biggest threats), change your army or placement and try again, as often as you like, or go back and pick another fight. In the war room, holding a placed piece picks it up (it wiggles, with a little sound) so you can drag it or tap another square to set it down; selecting a piece shows where it can move and strike, and "Show enemy reach" shades every square the enemy can hit on its first turn.
- **The draft.** A run starts by drafting its army: two commons, two uncommons and one rare, each picked from three. Every run also brings Squires. Then choose an opening (a random common unit, +2 supply in every battle, two runes, or a trained unit type) with the whole army on screen.
- **The tower.** Three acts, each a tower of eight floors: battle floors where you choose an easy, medium or hard fight (on two floors of each act, an elite instead of the hard one), an event and a merchant halfway up, and a boss at the top. Each floor up the enemy is a little stronger. Hard fights add enemy health and attack and pay more gold and rarer finds; elites also give a relic.
- **The Heart of the Board.** After the last boss you may face Zugzwang, an optional mega boss in the spirit of Slay the Spire's Heart. It takes at most 20 damage a round, every attack or spell you make costs that piece 1 health, it gains attack every round and moves twice, and it summons Echoes. Armies built on the hard fights and elites stand a chance; little else does.
- **The Hall of Fame.** Each finished run keeps its final army: the one that beat the Mad Grandmaster, or the one that beat the Heart (marked ♥) if you did. It starts at the bottom of the Hall and duels each earlier champion in the Hall's arena, from the bottom up, until it loses (watch each duel or resolve them at once). Beat them all and it takes first place. The top ten stay.
- **Sound.** Effects and music are synthesised in the browser with the Web Audio API: no audio files. The music is generative, with a mood for each act's tower, battles, bosses, the Heart and victory. The speaker button sets the volumes; M mutes.
- **Skirmish.** Every unit and rune unlocked; pick any of the 41 fights, the Heart included, and experiment.

Battle controls: Space pauses, → steps one turn, 1–4 set the speed (½×, 1×, 2×, 4×), S skips to the result.

## Content

25 player units with three talents each, 15 runes, 26 relics, 49 enemy and summoned unit types, 37 encounters across three acts plus three event battles, 12 events, three bosses (the last is a full chess army: checkmate the Mad Grandmaster to win) and the mega boss.

## Project layout

```
index.html            loads everything (plain script tags, works from file://)
css/style.css
js/core/              util, board geometry and line of sight, battle rules, AI
js/data/              passives, abilities, units, talents/runes/ranks, relics, encounters, events
js/game/run.js        the roguelike run: draft, tower, rewards, shop, events, mega boss, Hall of Fame, saves
js/ui/                DOM helpers, sound and music, piece-art toolkit, board renderer and animations, war room, battle screen, other screens
js/art/               one drawing per unit: player.js, enemy.js (acts I–II), enemy3.js (act III)
tests/                headless and browser tools (below)
tools/bundle.js       inline everything into one HTML file
tools/art-sheet.html  contact sheet of every figurine (open it in a browser)
```

The engine (`js/core`, `js/data`, `js/game`) has no DOM code and runs under Node.

## The look

The game is drawn in the manner of Chess Evolved Online, set on dark slate so it is easy on the eyes: chunky ink outlines, bevelled grey squares in a dark frame, a faint doodled maze in the background, and colour only where it means something. Blue brackets mark where a piece can move, red where it can strike, white where it can do both.

Every unit is a small statue on a pedestal: white for your side, black for the enemy, with coloured flares for rarity (blue uncommon, purple rare, red for the enemy's heavies, gold for bosses). The figures are drawn in code, not stored as images. `js/ui/pieces.js` provides a pen (`P.solid` shades and outlines a shape, `P.base` draws the pedestal, `P.eye` marks details that flip between dark and light with the side) and path helpers (`D.lathe` turns a half-profile into a symmetric piece; `D.flame`, `D.gear`, `D.batWing` and friends draw common motifs). Each unit's drawing is built once into an SVG symbol, and the side, glow and line weight come from CSS custom properties.

## Tools

```
node tests/rules.js                                      # deterministic rule and AI checks
node tests/art.js                                        # every unit has a figurine that draws cleanly
node tests/watch.js goblinSkirmish knight scout cleric   # watch one battle as text
node tests/balance.js --act 1 --n 24                     # random legal armies vs each encounter
node tests/runsim.js --runs 24 [--policy medium|hard|random] # whole runs played by a bot (tests/bot.js builds its armies)
node tests/runsim.js --runs 48 --dump snaps.json         # record realistic mid-run collections
node tests/calibrate.js snaps.json --n 40 [--fit --write] # replay every fight against them; fit enemy health to targets
node tests/fuzz.js --n 4                                 # invariant fuzzer: random armies, relics, every encounter
node tests/smoke.js [outDir] [--mobile]                  # browser play-through with screenshots (Playwright)
node tests/tour.js [outDir] [--mobile]                   # visit every screen
node tests/longrun.js 10 [--mobile]                      # drive the real UI through ten floors of a run
node tools/bundle.js dist/arcane-gambit.html             # single-file build
node tools/art-shot.js sheet.png knight,goblin --size 150 # screenshot of chosen figurines (all if no ids)
node tools/audio-check.js                                # render every effect and music track offline, report levels
```
