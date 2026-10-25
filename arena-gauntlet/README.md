# Arena Gauntlet

A single-player auto-battler roguelike in the style of classic isometric arena
battles (think Tactics Arena Online meets Slay the Spire). Scout the enemy army,
spend Supply on a counter-army, set it up, and watch it fight across three acts to
the Ashen Tyrant, and, if your army is up to it, the Eclipse Wyrm beyond.

## Experiment: the fun pass (branch `arena-gauntlet-fun-experiment`)

This branch is an experiment on top of the main game (kept as it was on
`ccr-64c96724-quo604`). It reworks passive talents, Level 3 masteries, a few skills and
the relics to be more fun. The idea: a passive should make something happen that you
can see on the board, not add an invisible +6%. So the flat stat bumps became
triggers ("when it kills...", "when it falls...", "when it is hit..."), with combos
between them, a few positional and cursed choices, and a callout on the board each
time one fires (CRITICAL!, EXECUTED, REFLECTED, BODYGUARD, TROPHY, BANG!...).

Talents (each replaces the flattest talent of its class):

| Class | Was | Now |
| --- | --- | --- |
| Knight | Guardian (allies beside take 15% less) | **Bodyguard**: once between its turns, takes a single-target blow meant for an ally beside it |
| Archer | Bodkin Arrows (ignore half armor) | **Ricochet**: arrows bounce to a second enemy within 2 tiles for 50%, poison and marks included |
| Scout | Ambusher (+50% from behind) | **Cutpurse**: every hit steals 2 gold, up to 12 a battle |
| Cleric | Fortitude (+12 HP, +15% res) | **Halo**: healing past full HP becomes a shield (up to 15) |
| Berserker | Battle Scars (+15% armor, +10 HP) | **Blood Frenzy**: +5% damage every time it is hurt, up to +50% (the ground under it reddens) |
| Pyromancer | Flame Cloak (8 thorns) | **Combustion**: burning enemies it slays explode, 10 damage to their neighbours, setting them alight |
| Assassin | Executioner (+40% below half HP) | **Execute**: finishes off enemies left below 20% (never bosses) |
| Golem | Bulwark (35% guard) | **Magnetic Core**: each turn yanks the nearest enemy 2-3 tiles away a step closer |
| Beast Rider | Swift Mount (+1 Move) | **Loyal Wolf**: when it falls, its wolf leaps free and fights on |
| Furgon | Deep Roots (+2 regen, +10 HP) | **Bramble Burst**: its shrubs burst when destroyed, 8 damage and a root to enemies beside |
| Poison Wisp | Lingering Spores (+1 poison turn) | **Contagion**: when an enemy carrying its poison falls, the poison leaps to its neighbours |
| Barrier Ward | Steel Field (+10% aura armor) | **Shatter Shield**: when destroyed, every ally in its aura gets a 20 shield |
| Enchantress | Mind Spike (+50% damage) | **Discord**: enemies it paralyzes lash out at an ally beside them |
| Witch | Warding Sigils (+20% res, +10 HP) | **Soul Harvest**: every enemy that falls within 3 tiles heals it 8 and adds +10% damage (up to +50%) |
| Lightning Ward | Grounding Field (magic guard) | **Overload**: when destroyed, 20 magic damage to every enemy within 2 tiles |
| Dragon | Ancient Hide (+30 HP) | **Hoarder**: every kill drops 8 gold, +15 HP |
| Mage Knight | Runic Bulwark (+15% armor, +15% block) | **Runic Ward**: starts every battle behind a 20 shield |
| Trebuchet | Wrecking Shot (ignore half armor) | **Shrapnel**: boulders spray 40% damage on enemies beside the target |

Level 3 masteries that were plain "+X% damage" now do something: Knight **Champion**
(a kill heals allies beside it 10), Archer **Deadeye** (every third shot is a sure
critical, instead of +20% damage), Berserker **Juggernaut** (kills earn trophies:
+10% damage each and it grows, instead of +15% damage), Pyromancer **Pyroclasm**
(kills leave fire behind), Witch **Shadow Pact** (its first 2 kills rise as your
skeletons), Lightning Ward **Thunderhead** (lightning strikes the nearest enemy each
turn), Golem **Colossus** (the ground shakes where it stops).

New skills: **Lucky** (15% crit), **Powder Belt** (explodes for 15 when it falls),
**Headhunter** (kill trophies and a 6 HP bite).

Relics. Out: Whetstone, Steel Bucklers, Iron Plating, Oaken Charm, Headsman's Axe,
Crown of the Old King, Aegis of Dawn, Dragon Scale (flat stat bumps). In:

- Common: **Lucky Coin** (12% crits), **Phalanx Standard** (20% less damage with two
  allies beside), **Lone Wolf Pelt** (+30% damage with no ally beside), **Powder Keg**
  (your fallen explode for 12, sparing your side), **Goblin Firecrackers** (three
  random enemies take 8 on your first turn), **Vampire Fang** (heal 8 per kill).
- Uncommon: **Executioner's Hood** (finish off foes below 15%), **Plague Doctor's
  Mask** (poison leaps from the dead), **Wildfire Oil** (the burning dead set their
  neighbours alight), **Trophy Rack** (every kill a trophy), **Storm in a Jar** (magic
  attacks arc to one more enemy), **Blood Pact** (cursed: +3 Supply, but start every
  battle at 75% HP).
- Rare: **Gambler's Dice** (a random Champion each battle: +50% damage and HP, a gold
  crown), **Mirror Aegis** (each unit's first hit bounces back), **Necromancer's Bell**
  (a 1 in 3 chance slain enemies rise as your skeletons), **Glass Crown** (cursed: +40%
  damage, -25% max HP).
- Boss: **War Drum of Ages** (every tenth turn, one great beat: the army heals 25 and frenzies for 3 turns, announced once over the army).

Second pass: the remaining plain "+X armor / +X HP / +X% damage" picks, talents, skills,
gear and enchantments each got a mechanic of their own. Kept as they were, on purpose:
upgrades that change range, area or cooldown (they change how a unit plays), the
anti-type weapons (Blessed Blade, Orcbane Axe and the like, which are counters), and
the economy relics (Supply, gold, XP).

- Free level picks: **Hold the Line** (Knight: hasn't moved since its last turn, 30%
  less damage), **Eagle Eye** (Archer: +1 range, first hit of the battle is a sure
  crit), **Slippery** (Scout: slips a tile away when it blocks), **Unseen** (Assassin:
  can't be targeted from afar until it first attacks), **Rattling Bones** (Skeleton
  Archer: melee attackers are weakened), **Hollow Gaze** (+1 range, arrows mark),
  **Runic Core** (Golem: stores magic it takes and adds it to its next hit),
  **Barkskin** (Furgon: below half HP, shrubs spring up around it), **Drift** (Wisp:
  puffs spores where it stops), **Ethereal** (Wisp: 30% of physical blows pass
  through), **Resonant Crystal** (Barrier Ward: when struck, nearby allies get a
  shield), **Far Song** (Enchantress: +50% on paralyzed foes), **Glamour** (attackers
  may be left spellbound), **Capacitor** (Lightning Ward: each hit taken charges its
  next zap), **Smouldering Scales** (Dragon: melee attackers catch fire),
  **Counterweight** (Trebuchet: boulders knock back), **Reinforced Frame** (shoves
  melee attackers away), **Far Cast** (Pyromancer: the fireball leaves fire behind).
- Talents: **Guardian Angel** (Cleric: once a battle, saves an ally from a killing
  blow), **Living Moss** (Golem: its regen spreads to neighbours), **Trample** (Beast
  Rider: a charge carries into the enemy behind), **Parasite** (Wisp: heals for what
  its poison takes).
- Skills: **Opportunist** (+40% on paralyzed, rooted or weakened foes), **Last
  Stand** (half damage below 25% HP), **Spell Mirror** (the first spell bounces back),
  **Overwatch** (a free shot at an enemy that walks into range), **Killing Spree**
  (double damage after a kill), **Undying Rage** (below half HP: heal and frenzy),
  **Chaos Magic** (spells add a random curse).
- Gear: **Reactive Plate** (a 25 shield below half HP), **Spellsink Mantle** (a spell
  taken charges +50%), **Ogre Belt** (+10 max HP per kill), **Momentum Boots** (+10%
  per tile moved before attacking), **Stunning Shield** (blocking a melee blow stuns
  the attacker), **Echo Amulet** (spells may strike twice), **Armor Breaker** (each hit
  strips 10% armor), **Porcupine Ring** (melee attackers are pricked and marked),
  **Berserker's Torc** (immune to stuns, roots and knockback, and each attempt
  enrages it), plus new **Grappling Hook** (drags targets closer), **Gambler's
  Gauntlet** (half to double damage), **Hourglass Pendant** (once, a killing blow
  rewinds it to its last turn's HP), **Cursed Idol** (+50% damage, -4 HP a turn) and
  **Ember Heart** (bursts into flames when it falls).
- Enchantment: **Mirror Image** (a 1-HP shadow copy of the unit joins each battle).

The warbands' starting kits use the new items (Undying Rage and a Stunning Shield
for the Iron Vanguard, Chaos Magic and a Spellsink Mantle for the Ember Circle,
Overwatch for the Gravewatch Order). With both passes in, the balance sims win 19 of
24 medium campaigns, back in the 19-22 range of the main game.

Starting relics: Iron Vanguard gets the Phalanx Standard, Ember Circle the Powder
Keg, Shadow Syndicate the Lucky Coin, Gravewatch Order the Vampire Fang (the Wildgrove Pact keeps its
Healing Salve).

## Play

Open `index.html` in a browser. No build step or server needed. Battles play best
on a phone turned sideways, but portrait works too.

## How it works

- **The draft**: a new campaign drafts its army instead of taking a ready-made
  warband. Eight picks, each one of three: five units, a relic, a skill and a piece of
  gear. There is no difficulty setting: each round you pick how hard a battle to
  take (see The road). Every unit offer has at least two that deal damage and none
  is a Cleric: every army starts with its own (see Your Cleric). The skills and gear
  offered are ones your units can use. Back
  undoes a pick; Start over deals a fresh draft. Every unit card shows all its numbers:
  HP, damage, armor, magic resistance, block, cooldown, move, range and speed, and
  names the talent it brings (one its class has not brought from an earlier pick).
  Your Cleric sits in the army strip from the first pick, with the talent it brings:
  tap it for its details before you choose the rest. Every unit you draft joins the
  strip and opens the same way (its numbers, attacks, abilities and the talent it comes
  with), so you can pick the relic, skill and gear to suit them; so do the rows of the
  final "Ready to march" summary. You start with 60 gold. How to
  play never pops up on its own: it is in the menu and on the title screen.

- **The road**: no map. Each act is four rounds; in each you choose one of three
  battles, shown as cards with a picture of the field, the mission and bonus goals,
  and what it pays: Easy (a smaller army, less gold and XP, two spoils to pick from),
  Medium, and Elite (a much tougher army, more gold and XP, and a relic). Now and
  then an Easy or Medium battle carries a relic too (6% and 10% of them). What each
  battle pays (its gold, its spoils, its relic) is settled when the three cards are
  dealt and saved with them: the card names the relic, and losing, retrying or
  closing and reopening the game never changes any of it. One event
  and one merchant sit somewhere in the middle of the act, and a boss ends it. Lose,
  and you come back to the round's choice (the same three, so you can try again or
  take an easier one); the War Room's Other battles button goes back too. Mostly
  medium battles with an easy one now and then should see most armies through; the
  bosses are the hard part. In the simulations, picking medium first wins about 90%
  of campaigns, and trying elite first (dropping to medium after a loss) does better
  still, thanks to the relics.
- **Enemies never heal**: your army has its Cleric; the enemy has nothing that mends,
  bosses included, and nothing that rises again once it falls. Chip away at a horde
  and it stays chipped. Orc Shamans' war drums only whip the warband into a frenzy, a
  Specter's touch weakens you instead of draining life, Bog Trolls are huge but never
  regenerate, totems enrage instead of mend, enemy Clerics are swapped for fighters,
  enemy armies never carry healing abilities, skills or gear, and an enemy's Level 3
  mastery drops any healing or rising again (a Skeleton Archer's Undying).
- **Victory and the final challenge**: beating the Act III boss wins the campaign.
  Then you may claim the victory, or face the Eclipse Wyrm for a super victory. It is
  not meant to be beaten (in the simulations it falls to about one strong army in
  four, and never to a middling one); losing to it costs you nothing. Lose, and Try
  again takes you straight back to the War Room with the same plan, as many times as
  you like. Whatever army last fought the Wyrm, won or lost, takes your campaign's
  place in the Hall of Fame the moment the battle ends (same name and record), with no
  question asked; call it a day whenever you like. The Wyrm's field has no chests and no
  bonus goals (nothing they pay could be spent after it): six powder kegs lie strewn
  between the armies instead, to blow up under whoever stands next to them.
- **Hall of Fame**: every campaign you win enters its final army in the Hall: the
  units that beat the Act III boss (or the Eclipse Wyrm), where they stood, their
  levels, abilities, talents, skills and gear, and your relics. It gets a name (The
  Iron Company, The Gilded Host ...) and is saved the moment you win, so starting a new
  campaign never loses it. Each army in the Hall shows its win-loss record right by its
  name and a small picture of it in formation, facing you like a team photo: its front
  line nearest, the rows behind stepping back. An army that beat the Eclipse Wyrm wears
  a purple skull-and-crossbones "Wyrm slayer" badge, and its row glows purple. Priority
  is banned in Hall matches, on purpose: whichever army you steered would almost always
  win, and the ranking would mean nothing. Tap a unit and the Priority button shows
  crossed out with a red X; tap it and it says why. The very first army to enter finds
  four **house armies** holding the Hall, mobs of one kind spammed onto the field,
  Level 1 and bare: The Scamper Pack (24 Scouts, #1), The Tin Can Brigade (16
  Knights) and The Thousand Arrows (16 Archers), 48 Supply each, and The Witching Hour
  (12 Witches with Abyssal Bolt, at the bottom), 72 Supply once their Abyssal Bolts
  (2 each) are priced in. Can your carefully chosen army beat them? In the
  simulations most winning armies do (83 to 93% of the time); at 30 Supply every one
  walked over them, so the mobs field about one and a half winning armies' worth.
  Later armies wait in line ("Waiting
  to climb") until you start their climb from the Hall, whenever you like, even several
  campaigns later. A climb starts at the bottom: it fights
  the army right above it, on a fresh field with mirrored obstacles, both sides on the
  AI. A win swaps the two; a loss, or reaching #1, ends the climb. Watch each match
  (pause and speed work as in a battle), or simulate the rest of the climb in a
  second. Skirmishes: tap any two ranked armies, whenever you like, then watch or
  simulate the match. If the lower-ranked army wins, the two swap places (#4 beating
  #1 takes #1, and #1 drops to #4; the armies between stay put); if the higher one
  wins, nothing moves. Both records count it either way. A skirmish is not part of a
  climb: a climbing army keeps climbing from wherever it ends up, unless it reaches #1.
  An army still waiting in line has no place yet, so a match with it is a friendly one
  that changes nothing. One army climbs at a time, and nothing is played out without
  you.
  The Hall is on the title screen (with how many armies wait to climb) and the end
  screen, and kept in the browser apart from your campaign save. It survives every
  update of the game: armies from older versions keep their places and fight by
  today's rules (whatever was rebalanced since applies to them too); anything they
  carry that no longer exists is left out, never the army. Only Reset Hall of Fame
  (at the bottom of the Hall, or in the menu, with a confirmation) clears it.
- **War Room**: tap a unit card to put that unit in the battle, and tap it again to
  take it out, so you can try armies out quickly. Tap a unit on the board (or hold its
  card) for its full loadout: cost, level, every slot and pick spelled out, stats and
  attacks, plus Priority (rally on it) and Take off the field. In battle, holding a
  unit shows everything about it, its loadout included. Equipped items and chosen
  abilities are gold with a ✓ Equipped or ✓ Chosen tag: they already work, and a tap
  only swaps them. Sheets opened from another sheet (equip a talent, pick an ability)
  have a Back button and no X, so you never close everything by accident; a tap
  outside the sheet, on the board above it, closes it all. To move a unit, long-press
  it on the board: it pops up off its tile and wriggles in your hand, so you can see it
  past your finger (phones that can buzz give a short buzz). Drag it to an open blue
  tile and let go; it drops down with a little bump. The board holds still while you
  drag. Units never swap places: dropped on another unit, it goes back. Or
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
  gear (only what you have that fits, and what your Supply can pay for). Pick one, or
  tap Continue to pass on that question (keeping its level or ability, or leaving the
  slot empty) and go on to the next; Exit leaves the setup there. Then pick your next
  unit. Questions with nothing to choose are skipped. Auto never asks.
- **The bench is bare**: units on the bench are always plain base units. Levels,
  abilities, talents, skills and gear go on a unit only once it is on the board, and
  taking it off sends all of it back to your pack. Each card's cost badge shows the
  base price, plus a small "+N" for whatever its loadout adds. Your plan for a battle
  is kept: lose, or step back to the other battles, and the army is still on the field
  when you return; a new battle opens with the army of your last one, kit and all.
- **Your Cleric**: every army has a Cleric, the only unit that heals. It fights in
  every battle: it starts on the field, cannot be taken off, and its base cost is free
  of Supply (levels, abilities and kit you give it still cost Supply as usual). Where
  it stands, and who guards it, is up to you. Its cards say Always. More Clerics can
  still join later; those cost Supply like any unit.
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
  Auto never fields a Lightning or Barrier Ward: a ward is only as good as the exact
  tile it stands on, so place yours by hand (a quest's ward still goes in). The
  Cleric always goes in the middle of the back row (the open tile nearest it if
  something stands there), with the fighters placed just ahead of it; move it
  afterwards if you like.
- **Commander level**: battles give XP, and elites and bosses give more. XP raises
  your commander level, from 16 Supply at Level 1 to 35 Supply at Level 10 (two more
  than enemy armies are sized for, so there is room for abilities and kit early on).
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
  and the like) are class talents. Every unit you get brings one talent of its
  class, named on its card wherever it is offered (draft, spoils, merchant) as "Comes
  with the ... talent" (the unit itself arrives bare, at its base price); slot it into
  that unit, or any other unit of its class, on the field. Every class has at least three
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
- **Free side-grades**: some skills and gear cost 0 Supply but still take a slot.
  Immunities that rarely matter (Unshakable) are free, and so are trades
  more than upgrades, marked "Free · side-grade": Bull Rush (your basic attack
  shoves), the Grappling Hook (it drags, for ranged units),
  War Paint (+15% damage, -10 HP), Reckless (+15% damage, -15% armor) and the
  Featherweight Cloak (+1 Move, -10% armor). Auto leaves side-grades to you.
- **The AI and positioning**: picks that only pay off from the right spot say how
  the AI plays them. A Guardian (or a Knight's Bodyguard, Holy Aegis, Spellward Aura,
  Grounding Field, a Golem's protection) escorts: it marches with your fragile units instead of ahead
  of them and keeps one beside it, and the fragile ones stay beside it too. Pack
  Hunter picks targets your other units already stand beside; Ambusher and Flanker
  go round the side or back; Trample takes the long way in. Your army also loves a
  good shove: when it can bump a foe into water, lava, a rock, the edge, another foe
  or a building, it goes out of its way to.
- **Enchantments**: binding a scroll to a unit gives it a permanent bonus and a
  Supply surcharge. It cannot be undone or moved to another unit.
- **Damage**: physical hits (marked with a sword) are reduced by armor and block;
  magic (a violet sparkle) is reduced by magic resistance. Armor and magic
  resistance both cap at 50%, and some units go as low as -50%. Specters are ghosts:
  steel mostly passes through them (50% armor, the cap) and magic tears them apart
  (-50% magic resistance, the floor). Mage Knights do the reverse. A unit's DMG stat,
  its attacks and every damage preview show the damage-type icon.
- **Auto battle**: you build and place the army in the war room, tap Begin battle,
  and watch it fight; the same AI that runs the enemy runs your units, using their
  abilities and talents. Lost? Change the army and try again. Speed (1x or 2x) and
  pause sit in the top bar next to the menu. Tapping a unit or a tile shows it without
  pausing: the battle plays on, and its Priority button works on the move; 1x plays at
  about half of the animations' full pace, to be easy to follow. Battles always play
  out on their own (commanding each turn yourself lives on in the classic version, on
  the `arena-gauntlet-tactics-classic` branch); units face the nearest enemy.
- **Goals in view**: the battle's goals sit pinned at the top of the panel below the
  board, above the unit card, turn order and battle log, and stay there however far the
  panel scrolls: the mission with its live count (the boss's HP, buildings down, turns
  to go, enemies left, or the cleanup's progress and your army's next fatigue hit), the
  gold still waiting in wreckage or barricades, each bonus goal with its reward (struck
  through once it is out of reach), and the next reinforcements. The full wording of
  every goal is further down, under Mission details.
- **Supply on the board**: each army's Supply sits in a small badge by its own back
  row, the enemy's at the top right and yours at the bottom left. In battle it reads
  what is still standing of what has taken the field (25/40: the units still alive,
  priced as in the War Room) and any reinforcements still to come; Hall of Fame matches
  show both armies' names and Supply the same way. In the War Room it reads what you
  field of your Supply, and what the enemy brings. The challenge cards show each enemy
  army's Supply (and its reinforcements) next to yours, and every army in the Hall of
  Fame shows its total. It is a rough guide to strength, not a promise: levels,
  relics, the field and the mission all count too. Enemy towers count 3; walls, gates,
  kegs and the like count nothing.
- **Tapping what is behind**: when one unit stands in front of another (a Lightning
  Ward before a barricade, say), tap the same spot again to pick the one behind; its
  panel says when something is hidden there.
- **Priority**: while watching, tap an enemy unit, a building, a barricade with gold
  inside, a chest or the shrine, then Priority. Your army goes all out for it, whatever
  the cost: every unit attacks it (a barricade is broken for its gold), or heads for
  the chest and takes it. With the shrine, one unit makes for it and
  stays on it while the rest gather round to guard it, and any enemy standing on it
  gets driven off; it stays the priority until the shrine is held. Or pick any empty
  tile: your army moves there and huddles as close to it as it can (tap a corner to
  turtle in it, or a choke point to hold it), still attacking whatever comes in reach,
  until you clear it. A boulder, a tree, a basalt spire or a shrub works the same way:
  the army gathers around it and holds there, without trying to cut it down. Or pick one of your own units: the rest of the army gathers around
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
  It goes for the Commander when killing it completes the mission, hits the wagon nearest its way out
  first, presses harder toward the end of a "win within N turns" goal (but never off
  a shrine it must hold), and values hitting the enemies that arrive in waves more while
  an "ambush the reinforcements" goal is open.
- **Taking turns**: the sides alternate one unit at a time, and the enemy goes
  first. Each side's units take its turns in a rotation, faster units first (Speed,
  SPD on the card: a Scout at 8 goes before a Knight at 2). A strip under the board
  shows who is next, units only.
- **Cooldowns**: acting starts a unit's cooldown (CD on its card). Its turns still
  come in the rotation, but it passes that many of them: when its turn comes it
  passes at once, its cooldown ticks down by one, and the next unit in line goes.
  Moving alone never starts a cooldown. Paralyzed units, and units with nothing in
  reach, pass too; when every unit of a side passes, the side passes. Bosses pass
  their first turn. The turn order strip shows every unit's turn, passes included:
  a unit about to pass is greyed out with its cooldown on its portrait (a yellow
  number for paralysis), and the number counts down as its turns pass. Over its head
  the board says so: "PASS COOLDOWN 2→1" (the badge by its health bar drops to 1 at
  the same moment), "PASS PARALYZED", "PASS HOLDS GROUND" (it could act and stays put),
  or plain "PASS"; the battle log gathers a row of passes into one line ("Cass, Osric
  and Jarek pass (cooling down).").
- **A unit's turn, step by step**: whatever comes with a unit's turn comes in one
  fixed order, acting or passing: its fatigue hit, then a Cursed Idol's 4, then poison,
  then burns, then fire underfoot, then regen, and only then does it act, or pass with
  its cooldown ticking down. The board plays each step as a beat of its own over the unit's head ("-16
  FATIGUE", then "-5 POISON", then "-4 BURN", then "+3 REGEN", then "PASS COOLDOWN
  2→1"), never two at once on one unit and never closer together than about 0.4
  seconds, at 2× speed too. Floating numbers never land on each other: a new one starts
  just below the ones still showing, and they all rise at one pace, so a run of them
  reads as a list, top to bottom in the order it happened. The next unit's turn starts
  only once the last one's steps have played. tests/beats.test.js plays real battles
  through the board's own playback and checks every beat for exactly this.
- **Events**: one an act, each a short scene with two or three choices, and every
  choice gives you something to play with rather than a pile of gold: a talent (often
  from the stronger list), a skill or two, gear, an enchantment bound straight onto a
  unit you pick (the Fountain of Renewal, the Old Forge, a duel with the Sellsword),
  a relic, a recruit, a mirror copy of one of your units, a unit transformed (the
  Alchemist's sure transmutation or free green vial), +1 Supply, Commander XP, or an
  elite battle for a relic. Some cost gold; a few are gambles (stake a soldier at the
  Gambler's Tent: an enchantment, or they leave your army). Your Cleric can be
  blessed, never transformed or lost.
- **Regen**: some talents, gear, relics and units heal whenever the unit's turn
  comes, whether it acts or passes (Living Moss 4,
  Healing Charm 3, the Furgon 3, a Mending Light aura 2). The only army-wide source
  is the boss relic Sacred Chalice (+2); the common Healing Salve adds 2 only to
  units that have regen of their own. Sources add up with no cap;
  unit cards and the battle log show it.
- **Fatigue**: from turn 30, every unit loses HP whenever its turn comes, acting or
  passing (cooling down, paralyzed, or a Barrier Ward, which never acts), past armor
  and shields, before it moves or acts: never a whole side at once, always one unit at
  a time. Each hit is the battle's next number, 1, then 2, 3 and so on, one count for
  both sides, like fatigue in Hearthstone: as the turns alternate, the hits go back and
  forth (the enemy 15, you 16, the enemy 17), five units passing in a row at 15 lose
  15, 16, 17, 18 and 19, one after another, and no number comes twice. Each hit plays on
  its own moment on the board (a unit that falls to it included) and gets its own line
  in the battle log. tests/fatigue.test.js plays hundreds of battles of every kind and
  checks every hit for exactly this. Fatigue comes first in a unit's turn, before its
  poison, burns and regen. Poison and burns tick on passed turns too. A short
  "Fatigue triggered!" banner marks the start (no message to tap away), and the top
  bar shows the next number. Reinforcements stop. Big units and regen last longest; the last side
  standing wins. A tough tank can win a long battle on its own.
- **Cleanup**: when the enemy army falls while the field still holds something worth
  having (loot, and enemy buildings with gold or a goal in them: totems, the cage, a
  wagon, barricades, walls, towers, the buildings that send reinforcements), the
  battle does not end on the spot. A banner says the army is beaten, the win is
  yours already, and your army goes round collecting: it breaks the buildings, cuts
  down any guards still at their posts (the specters by the Lost Tome) and takes the
  loot, gold and quest rewards and all. This is the victory lap, and it is not free:
  your army's fatigue sets in the moment the enemy army falls, whatever the turn. Each
  of your units loses HP as its turn comes (acting or passing), 1 for the first, then
  2, 3 and so on, one more for every turn one of your units takes (carrying on from
  where it was if fatigue had already set in). So collect fast: you may get some of it
  and not all. There is no time limit: the cleanup ends, with your win, only when
  everything worth having is taken or broken, or when your army has fallen to its
  fatigue, or when you tap Finish now (the menu's Retreat becomes Finish the battle). The top bar counts what is left and your
  army's next fatigue hit. A flawless or fast win
  counts from the moment the enemy army fell, so a unit fatigue takes during the
  cleanup does not spoil it.
- **Nobody surrenders**: a battle ends only when one side has no units left. If all
  you have left are units that cannot attack (a Furgon, a Barrier Ward), they fight
  on and the enemy must still bring every one down; if neither side can hurt the
  other, fatigue settles it. A Furgon's regen can outlast a fading enemy. Summoned
  shrubs do not count: they take no turns and no fatigue, and once a side's real
  units are all down it has lost, shrubs or not.
- **Poison**: poison and burns tick at the start of the poisoned unit's own turn,
  for a set number of its turns. Poisons from different sources stack: each keeps its
  own damage and its own turns, and the unit takes them all added up. Poisoned for 4
  (1 turn left) and for 8 (3 turns left), it takes 12, then 8, then 8. The same unit's
  same ability poisoning again only refreshes its own poison (the longer turns and the
  bigger damage), so one archer cannot pile poison on by itself; its chip in the unit
  card reads like "Poisoned 3 · 12 a turn (2 sources)". The Poison Wisp poisons every enemy within 2 tiles
  for 2 of their turns; poisoned units cannot heal.
  Buildings, wagons, cages and constructs (golems, wards, the trebuchet) are immune,
  and Pestilence's extra damage never hits buildings. Poison looks nothing like
  healing: its numbers float up in magenta with a minus sign (every damage number has
  one; heals have a plus), with a magenta puff, and a poisoned unit's HP bar turns
  magenta.
- **Wards**: a Lightning Ward cannot move. Each turn it sprays lightning at one side,
  north, south, east or west, like a shotgun: the row of three right in front of it and
  one tile beyond the middle, 4 tiles (7 with Overcharge, a second row of three). It picks the
  side with the most foes and the fewest of its own, so friendly fire still happens,
  but far less than when it zapped everything around it. The AI (yours and the
  enemy's) does not step into its reach unless that move lets it hit a living unit the
  same turn; it goes around, and leaves the ward for last. A Barrier Ward gives allies within 4
  tiles +25% armor and +25% magic resistance (+35% armor with Steelfield), and makes
  them immune to poison and paralysis.
- **Friendly fire**: every damaging area attack hits your own fighters in its area
  too: a Berserker's cleave, a fireball, an arrow volley, a Lightning Ward's spray,
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
  Commander, hold a shrine, survive the waves, topple three war totems (each whips
  the enemies within 2 tiles into a frenzy, 25% more damage, until it falls), raze the
  buildings that send reinforcements, storm a castle gate, or stop a wagon convoy.
  Getting it done does not end the battle on the spot: the enemy is **fatigued**. Their
  reinforcements stop and their fatigue sets in at once: from the next enemy turn, each
  enemy unit loses HP when its turn comes, acting or passing, 1 for the first, then 2, 3
  and so on, one more every enemy turn, past armor and shields, just like fatigue. Done
  after fatigue has set in for everyone (turn 30), and the enemy's fatigue doubles from
  then on instead (6 becomes 12, then 7 becomes 14), while your side keeps the normal
  amount. The battle
  ends when the last of them falls, so a mission done early tips it well in your favor, without the enemy
  simply giving up. Your own side tires only when
  fatigue sets in for everyone on turn 30. A short banner ("Enemy fatigued!") and the
  battle log say when it happens, the top bar shows the enemy's fatigue, and the mission line turns to
  "Done!". A "win within N turns" goal counts from the turn the mission was done.
  Bonus goals (ghost-guarded loot, fast wins, no losses, ambushing reinforcements,
  winning with a unit that sat out the last battle) pay extra.
- **Pushes and pulls**: some attacks shove a unit straight away (Shield Bash, Ground
  Slam, Boulder Toss, Arcane Burst, Wing Buffet, the Bull Rush skill, a Gale Horn, an
  Orc Brute's maul) and some drag it straight in (the Scout's Grapnel, a Grappling Hook, a Chain
  Hook, the Witch's Void Grasp, the Enchantress's Siren's Lure, a Giant Spider's web,
  Grukk the Warlord's chain). It moves tile by tile, and whatever stops it hurts, past
  armor and block: a rock or the edge of the field 8; another unit or a building 6,
  and that one takes 6 too, friend or foe (a building can break, coins and all);
  water 6, after which it climbs out onto the nearest dry tile, rooted for a turn and
  with any burn put out; lava 12, and it climbs out burning. Flyers sail over water
  and lava. Bosses, huge units and the steadfast never budge, and a blocked blow
  shoves nobody. Hooks fly straight along a row or column, with no rock or unit in
  the way. Relics: Iron Ram (+6 to every impact), Tidecaller's Conch (a tile
  further), Anchor Stone (your units cannot be moved). Previews say where a shove
  lands and what it hits, and the AI on both sides goes looking for a rock, a crowd,
  water or lava to shove its enemies into.
- **Buildings and siege**: walls, gates, towers, totems, tents, crypts, dens,
  portals and barricades are buildings. A castle gate opens for its own garrison (they
  walk through it, never stopping in the gateway); you have to break it. No battle
  walls anyone in: every map is checked so each enemy on foot, and each building's
  doorway, has a way across to your side, and a rock, pool or lava tile that would
  seal one in is cleared. Units of one side always walk through each other. Stone resists swords and spells alike,
  wood burns, and portals unravel under magic. Siege damage breaks them fast:
  the Trebuchet, the Siege Hammer, the Demolisher skill, a Blasting Charge, the
  Golem's Boulder Toss and the Sapper's Kit relic. A barricade your army breaks
  spills a pouch of gold (12 in Act I, 16 in Act II, 20 in Act III) in a burst of
  coins, paid with the battle's gold on a win. Your units go for it only when no
  enemy fighter is within reach that turn. Every other enemy building your army
  breaks drops a few coins too: 3 gold for a wall, tower, totem, banner or cage, 5
  for the gate and for buildings that send reinforcements (tents, crypts, dens,
  portals, guardhouses). Your units do not go out of their way for it.
- **Wreckage**: the Act I boss's camp (the Golem King's or Grukk's) is strewn with
  four wrecked supply carts, 8 gold in each. They are spoils, not targets: your army
  leaves them be while the fight is on (the AI gives them no value at all until then).
  Once the boss and its retinue fall, the cleanup begins, your army's fatigue sets in
  and it breaks what wreckage it can before that fatigue tells. A cart takes a hit or
  two (22 HP, light armor, and wood burns). In simulated campaigns a winning army
  salvages about half of it, anywhere from none to all four, and loses about three
  units to fatigue doing so (still a win, and nobody is lost for good). Their HP bars
  show from the start, and the boss line in the goals says how much gold waits there.
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
node tests/fatigue.test.js       # fatigue on hundreds of real battles: one unit at a time, the next number each hit
node tests/beats.test.js         # what the board shows as a unit's turn comes: one step a beat, in order, numbers never on each other
node tests/hall.test.js          # the Hall of Fame: entering, climbing, skirmishes, mirrored matches
node tests/fun.test.js           # the trigger passives and relics: crits, executions, explosions, bounces, the dead rising
node tests/talents.test.js       # class talents: slots, the pack, always usable
node tests/sim.js 200            # AI-vs-AI balance by unit type
node tests/chaos.js 200          # random loadouts, bosses, buildings and waves
node tests/run.test.js 20 medium # whole campaigns played by the AI, with retries
                                 # (pick medium | easy | elite | mix each round)
DRAFT=1 node tests/run.test.js 20 mix  # the same, with randomly drafted armies
MEGA=1 node tests/run.test.js 20 elite # ...and the final challenge after the win
```
