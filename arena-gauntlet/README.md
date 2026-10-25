# Arena Gauntlet

A single-player auto-battler roguelike in the style of classic isometric arena
battles (think Tactics Arena Online meets Slay the Spire). Scout the enemy army,
spend Supply on a counter-army, set it up, and watch it fight across three acts to
the Ashen Tyrant, and, if your army is up to it, the Eclipse Wyrm beyond.

## Play

Open `index.html` in a browser. No build step or server needed. Battles play best
on a phone turned sideways, but portrait works too.

## How it works

- **The draft**: a new campaign drafts its army instead of taking a ready-made
  warband. Eight picks, each one of three: five units, a relic, a skill and a piece of
  gear. There is no difficulty setting: each round you pick how hard a battle to
  take (see The road). Every unit offer has at least two that deal damage, and the
  first one always offers a Cleric, your only healer (exactly once: no later pick
  offers another). The skills and gear offered are ones your units can use. Back
  undoes a pick; Start over deals a fresh draft. Every unit card shows all its numbers:
  HP, damage, armor, magic resistance, block, cooldown, move, range and speed. You start with 60 gold.

- **The road**: no map. Each act is four rounds; in each you choose one of three
  battles, shown as cards with a picture of the field, the mission and bonus goals,
  and what it pays: Easy (a smaller army, less gold and XP, two spoils to pick from),
  Medium, and Elite (a much tougher army, more gold and XP, and a relic). One event
  and one merchant sit somewhere in the middle of the act, and a boss ends it. Lose,
  and you come back to the round's choice (the same three, so you can try again or
  take an easier one); the War Room's Other battles button goes back too. Mostly
  medium battles with an easy one now and then should see most armies through; the
  bosses are the hard part. In the simulations, picking medium first wins about 80%
  of campaigns, and trying elite first (dropping to medium after a loss) does better
  still, thanks to the relics.
- **Victory and the final challenge**: beating the Act III boss wins the campaign.
  Then you may claim the victory, or face the Eclipse Wyrm for a super victory. It is
  not meant to be beaten (in the simulations it falls to about one strong army in
  four, and never to a middling one); losing to it costs you nothing, and you can try
  again or claim your win at any time.
- **Hall of Fame**: every campaign you win enters its final army in the Hall: the
  units that beat the Act III boss (or the Eclipse Wyrm), where they stood, their
  levels, abilities, talents, skills and gear, and your relics. It gets a name (The
  Iron Company, The Gilded Host ...) and is saved the moment you win, so starting a new
  campaign never loses it. The first army takes #1; later ones wait in line ("Waiting
  to climb") until you start their climb from the Hall, whenever you like, even several
  campaigns later. A climb starts at the bottom: it fights
  the army right above it, on a fresh field with mirrored obstacles, both sides on the
  AI. A win swaps the two; a loss, or reaching #1, ends the climb. Watch each match
  (pause and speed work as in a battle), or simulate the rest of the climb in a
  second. Tap any two armies (waiting ones too) for a friendly match that changes
  nobody's place. One army climbs at a time, and nothing is played out without you.
  The Hall is on the title screen (with how many armies wait to climb) and the end
  screen, and kept in the browser apart from your campaign save.
- **War Room**: tap a unit card to put that unit in the battle, and tap it again to
  take it out, so you can try armies out quickly. Tap a unit on the board (or hold its
  card) for its full loadout: cost, level, every slot and pick spelled out, stats and
  attacks, plus Priority (rally on it) and Take off the field. In battle, holding a
  unit shows everything about it, its loadout included. Equipped items and chosen
  abilities are gold with a ✓ Equipped or ✓ Chosen tag: they already work, and a tap
  only swaps them. Sheets opened from another sheet (equip a talent, pick an ability)
  have a Back button and no X, so you never close everything by accident; a tap
  outside the sheet, on the board above it, closes it all. To move a unit, long-press
  it on the board and drag it to an open blue tile, then let go; the board holds still
  while you drag. Units never swap places: dropped on another unit, it goes back. Or
  tap an empty blue tile first, then a unit card: that unit goes there (one already on
  the field moves there). A tap just
  off a blue tile still places it on the nearest one, and a tap on the empty space
  around the board lets it go. Your deployment zone is the three rows nearest you
  (rocks and water may block a few tiles); Auto keeps to the back two unless it needs
  more room. Drag the board to move it, even partly off screen, and pinch to zoom
  (there are no zoom buttons). Your relics show as small round badges in the board's corner, in
  the War Room and in battle: tap one to see what it does. Tap the Supply bar to see what every deployed unit
  costs. Begin battle stays in view at the bottom. The loadout says what each chosen
  ability does, and its talent, skill and gear sections list everything you own that
  fits the unit, right there: equipped ones first (gold, ✓ Equipped), then the rest
  (with ×2 for copies, or "on Kael" for one another unit holds; taking it moves it).
  Tap to equip or unequip, up to the slots its level gives ("1 of 2 slots used"); once
  they are full, the rest dim and a tap says why. The unit strip stays where you scrolled it.
- **Setup guide**: put a unit on the board and a short sheet walks through its kit,
  one question at a time: its level, its ability picks, then its talents, skills and
  gear (only what you have that fits, and what your Supply can pay for). Answer No to
  any question, or Done to stop; then pick your next unit. Questions with nothing to
  choose are skipped. Auto never asks.
- **The bench is bare**: units on the bench are always plain base units. Levels,
  abilities, talents, skills and gear go on a unit only once it is on the board, and
  taking it off sends all of it back to your pack. Each card's cost badge shows the
  base price, plus a small "+N" for whatever its loadout adds. Your plan for a battle
  is kept: lose, or step back to the other battles, and the army is still on the field
  when you return; a new battle opens with the army of your last one, kit and all.
- **Quest units**: when a bonus goal asks for a unit that sat out your last battle,
  that unit insists on fighting: it starts on the field and cannot be taken off (its
  card says Quest). It fights at full strength; the challenge is fitting a unit you
  might not have picked into your plan.
- **Army size**: there is no limit on how many units you recruit, or on how many
  take the field. Supply is the only limit: eight cheap Archers or four
  veterans, your call. Your commander level sets how big enemy armies get and
  how many units Auto starts from (Auto then spends what Supply is left on
  levels, items and, if it fits, one more unit).
- **Supply**: each battle gives you Supply to spend. A unit costs its base price,
  plus its level, plus any ability, skill, gear or enchantment it carries.
  Spend it however you like: two Level 1 Knights (3 + 3), or one Level 2 Knight
  (3 + 2) with an extra ability. Loadouts are free to change between battles, for
  units on the field.
- **Auto**: the War Room's Auto button builds an army for you. It weighs the
  enemy's armor against its magic resistance: magic attackers against armored
  armies, physical ones against magic-resistant armies, a mix otherwise. The
  scout report shows the same comparison. If a bonus goal asks for a unit, Auto
  always fields it, and the War Room lists that unit first.
- **Commander level**: battles give XP, and elites and bosses give more. XP raises
  your commander level, from 14 Supply at Level 1 to 33 Supply at Level 10.
- **Unit levels**: Level 1 picks an ability: the free one, or an active ability
  that costs extra Supply. Every active ability has 1 to 3 uses a battle, which never
  come back, and most have a cooldown of their own (shown as "Active, 3 uses, cooldown
  4"): after a use it waits that many of the unit's turns, on top of the unit's own
  cooldown, so a strong one cannot come out every turn. Using one is the unit's action
  for the turn, in place of its attack (Blink included). For example, the Archer chooses Snare Shot or Smoke
  Screen. Level 2 (+2 Supply) gets more HP and damage,
  another skill slot, a talent slot and a second ability pick. Level 3 (+5) adds a
  class mastery, a third talent slot and a second gear slot.
- **Talents**: the passives that cost Supply (Shield Wall, Riposte, Poison Arrows
  and the like) are class talents. Every unit you get brings one random talent of its
  class, which goes into your pack (the unit itself arrives bare, at its base price);
  slot it into any unit of that class on the field. Every class has at least three
  talents, and a new unit brings one you do not own yet (bought and found ones count),
  so three Clerics bring three different talents; only once you own them all does one
  come twice. You find more in shops and battle spoils,
  and only for classes in your army. A unit has one talent slot per level, three at
  Level 3, and can mix and match any of its class's talents you own (one copy of
  each per unit; each copy fits one unit at a time). The level picks keep the free
  option and the active abilities. The stronger talents turn up half as often, and
  copies you already own less often still, so a great combination takes hunting.
  Talent cards are teal in shops and spoils, and the rare ones glow magenta. Every
  talent improves something its class always has (its attack, its defenses, its
  innate traits), never an ability the unit might not have picked; a test checks it.
- **Enchantments**: binding a scroll to a unit gives it a permanent bonus and a
  Supply surcharge. It cannot be undone or moved to another unit.
- **Damage**: physical hits (marked with a sword) are reduced by armor and block;
  magic (a violet sparkle) is reduced by magic resistance. Armor and magic
  resistance both cap at 50%, and some units go as low as -50%: Specters shrug
  off steel but melt to spells, and Mage Knights do the reverse. A unit's DMG stat,
  its attacks and every damage preview show the damage-type icon.
- **Auto battle**: you build and place the army in the war room, tap Begin battle,
  and watch it fight; the same AI that runs the enemy runs your units, using their
  abilities and talents. Lost? Change the army and try again. Speed (1x or 2x) and
  pause sit in the top bar next to the menu, and tapping a unit pauses and inspects it; 1x plays at
  about half of the animations' full pace, to be easy to follow. Battles always play
  out on their own (commanding each turn yourself lives on in the classic version, on
  the `arena-gauntlet-tactics-classic` branch); units face the nearest enemy.
- **Priority**: while watching, tap an enemy unit, a building, a chest or the shrine,
  then Priority. Your army goes all out for it, whatever the cost: every unit attacks
  it, or heads for the chest and takes it. With the shrine, one unit makes for it and
  stays on it while the rest gather round to guard it, and any enemy standing on it
  gets driven off; it stays the priority until the shrine is held. Or pick any empty
  tile: your army moves there and huddles as close to it as it can (tap a corner to
  turtle in it, or a choke point to hold it), still attacking whatever comes in reach,
  until you clear it. Or pick one of your own units: the rest of the army gathers around
  it and follows wherever it goes, until you clear it or it falls. A marker shows the target. Once it falls or is
  taken, the army goes back to normal orders; you can also clear it. You can pick one
  in the War Room too, before the battle: tap an enemy, a building or a chest, then
  Priority, and your army goes for it from the very first turn (a dash for the chest,
  a rush at the Commander). It stays with your plan for that battle if you lose or
  step away.
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
  shows who is next, units only.
- **Cooldowns**: acting starts a unit's cooldown (CD on its card): it sits out that
  many of its own turns, and the next unit in line goes instead. Moving alone never
  starts a cooldown. Paralyzed units, and units with nothing in reach, sit out too;
  when every unit of a side must sit out, the side passes. Bosses sit out their
  first turn.
- **Regen**: some talents, gear, relics and units heal as the unit takes its turn,
  one unit a turn: units that sit a turn out do not regenerate (Living Moss 4,
  Healing Charm 3, the Furgon 3, a Mending Light aura 2). The only army-wide source
  is the boss relic Sacred Chalice (+2); the common Healing Salve adds 2 only to
  units that have regen of their own. Sources add up with no cap;
  unit cards and the battle log show it.
- **Fatigue**: from turn 30, the unit taking each turn loses HP as its turn starts,
  past armor and shields: 1 in the first round (the enemy's unit, then yours), 2 in
  the next, then 3 and so on, the same for both sides, like fatigue in Hearthstone.
  One unit a turn: units that sit the turn out (cooling down) are spared, and if a
  whole side sits out, the first in line takes it. The top bar shows this round's
  hit. Reinforcements stop. Big units and regen last longest; the last side
  standing wins. A tough tank can win a long battle on its own.
- **Nobody surrenders**: a battle ends only when one side has no units left. If all
  you have left are units that cannot attack (a Furgon, a Barrier Ward), they fight
  on and the enemy must still bring every one down; if neither side can hurt the
  other, fatigue settles it. A Furgon's regen can outlast a fading enemy. Summoned
  shrubs do not count: they take no turns and no fatigue, and once a side's real
  units are all down it has lost, shrubs or not.
- **Poison**: poison and burns tick at the start of the poisoned unit's own turn,
  for a set number of its turns. The Poison Wisp poisons every enemy within 2 tiles
  for 2 of their turns (3 with Lingering Spores); poisoned units cannot heal.
  Buildings, wagons, cages and constructs (golems, wards, the trebuchet) are immune,
  and Pestilence's extra damage never hits buildings. Poison looks nothing like
  healing: its numbers float up in magenta with a minus sign (every damage number has
  one; heals have a plus), with a magenta puff, and a poisoned unit's HP bar turns
  magenta.
- **Wards**: a Lightning Ward cannot move, so the AI (yours and the enemy's) does
  not walk into its pulse unless that move lets it hit a living unit the same turn;
  it goes around, and leaves the ward for last. A Barrier Ward gives allies within 4
  tiles +25% armor and +25% magic resistance (+35% armor with Steelfield), and makes
  them immune to poison and paralysis.
- **Friendly fire**: every damaging area attack hits your own fighters in its area
  too: a Berserker's cleave, a fireball, an arrow volley, a Lightning Ward's pulse,
  a breath. Upgrades can make one spare allies: Controlled Burn (fireball), Tamed
  Fire (dragon breath), Abyssal Bolt (dark lightning), or the Disciplined skill (any
  unit with an area attack). Some monsters (the bosses' breaths) spare their own.
  Area spells that only hinder, like roots or smoke, never touch allies.
- **Combat**: block works from the front, half from the side, never from behind.
  Roots, weakness, paralysis and frenzy count the affected unit's own turns; a mark
  counts the attacker side's turns.
- **Board features**: tap a rock, tree, water, lava, a treasure chest, the shrine,
  fire, smoke, caltrops or a red landing tile to see what it does: whether it blocks
  movement or attacks, what loot pays and which tiles wake its guards, and how long
  a hazard lasts. A unit's panel also says what it is standing on.
- **Reading the enemy**: a unit's own attack is called its **basic attack** (its
  **basic ability** for healers and helpers) everywhere: on its card, in talents and
  masteries ("its basic attack also hits every enemy beside the target") and in the
  battle log. Only abilities it picks go by name (Shield Bash, Boulder Toss). Tap any
  unit, yours or theirs, to see a small diagram of every attack: where it can aim and exactly which tiles one use hits (a Brute's
  maul strikes its target and the three tiles around it; a Witch's lightning runs
  five tiles straight). The board shows everywhere it could hit on its next move.
- **Missions**: defeat every enemy, burn a War Banner, break a prison cage, kill a
  Commander, hold a shrine, survive the waves, topple three totems, raze the
  buildings that send reinforcements, storm a castle gate, or stop a wagon convoy.
  Bonus goals (ghost-guarded loot, fast wins, no losses, blocking reinforcements,
  winning with a unit that sat out the last battle) pay extra.
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
- **Defeat**: lose as often as you need. You go back to the round's choice of
  battles; a battle an event started is fought again from the War Room.
- **Missed bonus goals**: a win that misses a bonus goal (say, winning within 30
  turns) pauses before the rewards and shows which goals you met. Retry the battle
  with a new setup (the win and its rewards are set aside, and it does not count as
  a loss), or keep the win and continue. You can retry as often as you like.
- **Rewards**: what a win gives you anyway (XP, gold, bonus-goal rewards, a freed
  prisoner, a relic, a commander level-up, the bonus goals you met) has a plain gold edge and a ✓ Collected badge, and no glow; goals you missed are listed apart, plainly. A
  choice still waiting for you (spoils, the Lost Tome, a boss relic, event choices,
  the draft, the challenge cards) has a soft aura that fades in and out; once you
  pick, your pick gets the gold edge and a ✓ Chosen badge and the rest go grey.
  Reward and shop cards say how many of that kind you already have. Once your last
  pick on the victory screen is made (spoils, the Lost Tome, a boss relic; picks are
  final), it moves on by itself after a moment; opening the Army screen first holds it. An enchanted
  recruit shows the Supply its enchantment adds right by its name (+2 Supply), and
  what it does in a violet box of its own, and every recruit card has a ? button that opens the unit's
  details (HP, numbers, attacks, traits, enchantment) without taking it.
- **The merchant**: six things: a recruit, a talent, a skill, gear and a relic, plus
  one of an enchantment scroll, a Supply Cache or a War Manual. Relics cost about
  twice as much as anything else. Resupply brings out a whole new stock for 20 gold,
  then 30, 40 and so on; press it as often as you can pay. Units cannot be dismissed.
- **Performance**: the board draws 30 frames a second while something moves and 10
  when nothing does, at no more than twice the screen's CSS pixels, to keep phones
  cool.
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
| `js/run.js` | The road (challenge rounds), Supply and XP, loadouts, missions, rewards, saving |
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
node tests/draft.test.js         # drafting a starting army
node tests/campaign.test.js      # the road: challenge rounds, merchant, bosses, final challenge
node tests/hall.test.js          # the Hall of Fame: entering, climbing, mirrored matches
node tests/talents.test.js       # class talents: slots, the pack, always usable
node tests/sim.js 200            # AI-vs-AI balance by unit type
node tests/chaos.js 200          # random loadouts, bosses, buildings and waves
node tests/run.test.js 20 medium # whole campaigns played by the AI, with retries
                                 # (pick medium | easy | elite | mix each round)
DRAFT=1 node tests/run.test.js 20 mix  # the same, with randomly drafted armies
MEGA=1 node tests/run.test.js 20 elite # ...and the final challenge after the win
```
