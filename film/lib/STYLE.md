# STYLE.md: the visual style bible

Every character, prop, environment and scene follows these rules, so twelve agents produce
one film. The reference look is set by the hero's sheets and the wash-house demo (render them
with `python3 film/render.py --sheet` and `python3 film/build/demo_hero.py`):

| file (film/build/preview/) | what it shows |
|---|---|
| `character_sheet_dragon_1.png` | turnaround: 3/4 left, front, 3/4 right, profile, lean, sigh |
| `character_sheet_dragon_2.png` | walk cycle, seated (bench / front / too-small stool), the sit-down blend |
| `character_sheet_dragon_3.png` | 21 expressions: moods, talk, laugh + embers, sigh + smoke, front and 3/4 |
| `character_sheet_dragon_4.png` | gestures and the props they hold: stone, bag, note, stamp, book, crumbs |
| `character_sheet_dragon_5.png` | the same dragon under all 8 scene lights, and his signature pose per scene |
| `character_sheet_dragon_6.png` | film-scale readability: 600 / 450 / 350 / 200 px tall |
| `character_sheet_lineup.png` | cast height chart: every creature with a `lineup()` hook vs the planned heights |
| `demo_hero.png` | a finished frame: the wash-house, S1 (background, light layer, bloom, grain) |

## 1. The look in one paragraph

This is premium 2D feature animation in a storybook medieval-fantasy world (think the warmth of
Disney's *Robin Hood* and the polish of a modern 2D short), **not** clip-art, vector-flat or MMO
gritty. Characters are appealing, readable shapes. They are cel-shaded with one lit tone, one
shadow tone and a coloured rim light, and drawn with a thin coloured outline. They stand in
painterly, softly focused worlds with no outlines. Light tells the story: glows, bloom, shafts,
warm against cold. Every frame gets subtle grain and a vignette. Nothing on screen is ever
frozen: everyone breathes, blinks and sways.

## 2. Shape language and appeal

* **One silhouette idea per creature**, readable in solid black at 200 px tall. Examples: the
  dragon is a tall S-curve (hunched shoulders, long coat, long tail); the gnome is a pear with a
  cone on top; the troll is a boulder with small legs; the pixie is a teardrop with wings.
* **Push proportions.** Heads and eyes are big, hands are big, feet are small, and waists and
  wrists are narrow. Contrast sizes (big/small) and shapes (round/square/triangle) inside one
  character.
* **No parallel straight lines and no symmetry in poses.** Limbs taper. Contours alternate a
  straight side against a curved side. Weight sits on one leg, the head tilts, the shoulders slope.
* Characters never touch the frame edge or each other's silhouettes by accident. Overlap on
  purpose, with a clear front/back order.
* **Period rule (SPEC 0.1):** no modern objects, clothes or lettering anywhere. Clothes are
  wool, linen, leather and felt. Fastenings are buttons, buckles, laces and toggles.

## 3. Scale and heights: one scale for the whole cast

All characters are authored so that **`scale = 1.0` means the heights below**. Characters in
the same depth plane get the **same** `scale` (e.g. everyone on the bench in S7 at 0.9), so
relative sizes are always on-model. A scene chooses one scale per depth plane and never
"fixes" a character by scaling it alone.

`base.CAST_HEIGHTS` is the table in code. Values are px at scale 1.0, ground to the top of the
silhouette in the default standing pose, horns and ears included; hats, hood tips and held
props are excluded.

| creature | top | notes |
|---|---|---|
| troll (bouncer, S4) | 660 | fills the tavern door, hunched |
| minotaur (S4/S5) | 600 | horns included |
| **dragon (hero)** | **520** | horn tips; crown 488; eyes 445; **seated on the bench: crown 390, eyes 345** |
| orc (S5) | 480 | broad |
| elf (S1, tavern) | 470 | ears included, slender |
| lioness (pharmacist, S2) | 450 | ears included |
| satyr (tavern) | 430 | horns included |
| faun (teen, S7) | 410 | gangly, little horns |
| harpy (S5) | 400 | |
| griffin (courier, S7) | 380 | sitting on its haunches |
| dwarf (worker, S7) | 300 | stout and wide |
| goblin | 260 | ears included |
| kobold | 220 | |
| **gnome (grandmother)** | **160** | hood tip extra; **seated on the bench her head reaches the dragon's elbow** |
| pixie (S5) | 90 | hovers; wings extra |
| pigeon | 42 | |

* **Bench seat height = 125 px at scale 1.0** (`base.BENCH_SEAT_H`, `dragon.DRAGON_SEAT_H`).
  Every bench, stool and chair is built to the seat height its sitter expects. The S1 stool
  is deliberately too small: 72.
* Anchors: a character's `(x, y)` is the **ground point** below its pelvis (between the feet,
  or below the seat when sitting). Never use the top-left corner of the character.
* Check your creature on `character_sheet_lineup.png` (add a `lineup()` hook, see API.md).

## 4. Line

* **Characters and the props they touch get outlines. Environments and set dressing do not.**
  For depth, background elements use value and colour (atmospheric perspective) and blur.
* The outline colour is never black. It comes from the part's own material:
  `line = saturate(shadow * 0.55, +25%)`, i.e. `palette(light, mat).line`. Teal scales get
  deep teal ink and the mustard scarf gets brown ink. Pass `line_color=` only for special
  cases.
* Weight: `base.LINE = 2.2` px at scale 1.0 for the whole cast (the dragon uses 2.4). Line
  weight does **not** grow with creature size: the troll and the gnome share it. On screen,
  never thinner than 1 px: `lw = max(LINE, MIN_LINE_PX / device_scale)`.
* Draw outlines as **filled dilated copies** of the shape: the `*_paths()` builders return
  `(shape, outline)`. Do not stroke them: strokes cost about 3x more and cross at joints.
  Overlapping parts of one material are **one union** with one outline. Then the joints have
  no seams: shoulder into arm, leg into foot, cranium into jaw.
* Interior lines (folds, creases, knuckles, plate seams, brow furrows): thinner (0.8-1.0 x
  lw), tapered at both ends, 40-70 % opacity, in the part's line colour, batched into one fill
  with `base.detail_lines()`. A good drawing has few of them. Put them where form turns:
  elbows, knees, the inside of a bend, where cloth hangs.

## 5. Shading: the house recipe (`base.shade`)

Three solid tones per part, never a gradient per part:

1. **outline**: the dilated fill, in the line colour;
2. **rim**: a ~1.6-line-width band on the edge facing the rim light. Its colour is the
   scene's rim colour added over the tone beneath it, scaled by how light the material is, so
   dark cloth gets a subtle rim and pale horns a bright one;
3. **shadow**: the shape filled shifted away from the rim;
4. **lit**: the shape filled shifted toward the key light. The leftover crescent on the far
   side is the core shadow: ~20 % of the part's `size`.

Tones come from `palette(light, mat)`:

* `lit = base * (1 + (key - 1) * 0.55) * exposure`. The key tints the colour but never
  replaces it, so teal stays teal under orange lanterns.
* `shadow = base * ambient / shadow_k` (+ warm translucency `sss` for skin, ears, membranes
  and bellies).
* Give `size` the part's real thickness (tail 24, sleeve 30, coat 110): it sets the crescent
  width. Use `rim=0.5` on thin parts (legs, fingers) so the rim does not turn into a pinstripe.

**Exceptions that may use gradients:** eyes (`base.eye` does it), glows and light (fx), skies and
backgrounds, and one big soft occlusion per character (`base.occlusion`) under a chin or
scarf.

Materials (`base.Mat`): `sss` 0.3-0.6 for skin and membranes, 0 for cloth and horn; `sheen`
0.4-0.6 for brass, horn and wet things; `shadow_k` > 1 makes the shadow lighter (pale
materials). Every creature module exposes its colours as a dict (`DRAGON_COLORS`) and its
materials through a function (`dragon_mats()`).

## 6. Colour

* **Characters are more saturated and higher in contrast than their backgrounds.** Backgrounds
  sit in a narrower value band (roughly 15-70 % value), lean toward the scene's palette and lose
  saturation with distance. Characters carry the brightest highlights and the darkest
  accents in their area of the frame.
* Each creature has **one signature warm or saturated accent**: the dragon's mustard scarf, the
  gnome's faded-red hood, the faun's red cowl, the dwarf's orange leather vest, the orc's red
  jerkin. Everything else on the character is calmer.
* Cast colours from SPEC §4 are law (e.g. dragon scales `#3E6E73`, coat `#2F3A4F`, scarf
  `#C9A13B`; gnome shawl `#9B8BB8`). Keep them as hex constants at the top of the module.
* Never use pure black (`#000`) or pure white (`#FFF`) on a character. Sclera is `#F3EEE4`;
  the darkest pupil is `#1d120c`.
* Magic glows are cold and arcane (cyan `#5fe0ff`, pale green, violet) everywhere the city
  "hands him stones". **Warm light (amber, candle, ember gold) is reserved for kindness**: the
  lantern, the bread, his laugh. Scene authors guard this contrast.

## 7. Lights (scene to character)

* Each scene picks a `base.LIGHTS` preset and passes it to **every** character and prop:
  `neutral`, `washhouse` (S1), `apothecary` (S2), `street_night` (S3), `tavern` (S4), `square`
  (S5), `dusk` (S6), `golden` / `blue_hour` (S7), `lantern_night` (S8).
* Local tweaks: `LIGHTS["washhouse"].with_(rim_strength=0.9)` (e.g. a stronger rim on the
  hero), or `Light.lerp(a, b, u)` for a light that changes over time (S7 golden to blue hour;
  a character walking into the lantern's pool).
* `direction` points **toward** the key light in screen space (y down). Match it to the
  painted light sources in the background: lamp above means `(0, -1)`, low sun from the left
  means `(-0.9, -0.4)`.
* Light that falls on the world (pools, shafts, glows around lamps and magic) is drawn by the
  scene into the `fx.LightLayer`, never baked into a character.

## 8. Faces and eyes

* **Everyone's eyes are `base.eye()`.** It draws: a warm off-white sclera with a lid-shadow
  band; a big iris (66 % of the opening height) with a lighter lower half and a darker limbal
  ring; a pupil (round, or `pupil_aspect` 0.6-0.8 for reptiles and cats); two catchlights; a
  heavy upper lash line and a thin lower lid line. Upper lids show character: the dragon's lid
  is at 0.46 (tired). The lid follows the iris, so looking down lowers it.
* **Faces must read at 350-600 px character height** (medium shots) and the expression must
  survive at 200 px (wide shots). Keep the eye-opening height at least 3.5 % of the standing
  height (the dragon's is ~19 px at 520), and push brows hard.
* Expressions come from the shared `base.MOODS` (neutral, tired, sad, lonely, raised,
  surprised, worried, happy, warm, laugh, skeptical, angry, bored, sneer, sigh, kind) via
  `base.Expr`, so "worried" means the same brows on every creature. Map the fields to your
  creature's features: `brow_in`/`brow_out`/`brow_y`/`brow_asym`, `lid`, `lid_bot`,
  `lid_tilt`, `smile`, `open`, `mouth`, `cheek`, `pupil`.
* Mouths move **only** when that character speaks: `talk = timeline.talk(scene, t,
  "SPEAKER")`. A closed mouth still acts, through `smile` and `sneer`.
* Eyes lead, then the head, then the body: when a character looks at something, move `look`
  first, the head 0.15-0.25 s later and the body after that.

## 9. Secondary motion (nobody is a frozen cut-out)

All of it is driven by `t` (deterministic) through `base` helpers:

| what | helper | typical values |
|---|---|---|
| breathing | `breathing(t, rate, seed)` | 0.20-0.25 Hz; big creatures slower (troll 0.15), small faster (pixie 0.5) |
| blinks | `auto_blink(t, seed)` | every 2.4-5.2 s, 0.18 s, 20 % doubles; **different seed per character** |
| idle sway / weight shift | `sway(t, freq, seed)` | 0.2-0.35 Hz, a few px |
| tails, scarves, hood tips, ears | `chain(t, n, freq, delay, amp, seed, grow)` | freq 0.3-0.45, delay 0.12-0.2 s per segment |
| settle after a move | `spring(t, t0, freq, damping)` | 2-3 Hz, damping 0.45 (ears, fins, the gnome's hood tip) |
| impact wobble | `wobble(t, t0, freq, decay)` | thunks, landings, stamps |
| walking | `walk_cycle(phase, stride, lift, bob, swing)` | phase from distance travelled (no foot sliding) |

* Overlap: a head turn drags its ears and hood tip a few frames later (`lagged` / `follow`).
* Anticipation before every big move (lean back before standing, wind up before tossing
  crumbs) and an ease-out settle after it. Use the `core` easings, never linear.
* Every grounded character gets a `base.contact_shadow()`. A sitting one gets one under the
  seat and the feet.

## 10. Level of detail and performance

* **Level of detail (LOD)** by on-screen size: `dev = scale * base.device_scale(cr)`. Use detail
  2 if `dev >= 0.9`, 1 if `>= 0.55`, else 0.
  * **2**: everything.
  * **1**: drop knit and stitch texture, knuckle ticks and minor creases.
  * **0**: silhouette, flat shading, eyes, mouth and claws only.
  Accept a `detail=None` argument that overrides this.
* Budget: about 350 ms per 1920x1080 frame for everything. Measured on this machine: the hero
  dragon costs ~21 ms at full size and ~13 ms at 0.45 scale; a finished wash-house frame
  (cached background, 6 drums, the dragon, light layer, bloom, grain) costs ~100 ms.
  Supporting cast: aim for **≤ 12 ms at full size**. Crowd members: **≤ 5 ms** at their
  on-screen size.
* What costs: raster area (each fill), strokes, `push_group`, per-part gradients, blend
  operators other than OVER, ADD and SOURCE, and big glows at full resolution. What is cheap:
  path building, solid fills of small parts, one union per material, and batched ink
  (`detail_lines`).
* Static art (walls, far buildings, skies) is drawn once in `setup()` into an `fx.Layer`
  (optionally pre-blurred for depth of field) and painted every frame. Never re-blur per
  frame.

## 11. Composition (for scene authors)

* Keep the bottom 180 px free of faces and key action (captions live there).
* Separate depth with atmospheric perspective (far layers lighter, bluer and blurred),
  parallax (`core.Camera.view(cr, parallax)`), a soft-focus foreground element now and then
  (`fx.Layer(..., blur=7)`), and contact shadows plus ambient occlusion where things meet the
  ground.
* Light leads the eye: the brightest value and the warmest colour go on the story point.
* Camera moves are slow and eased (push-ins, pans). Hold still on emotional beats.

## 12. Do / don't

| do | don't |
|---|---|
| one union per material with a dilated outline (`*_paths`) | stroke every part separately (seams at joints, 3x cost) |
| line colour from the material's palette | black outlines, or outlines on backgrounds |
| core shadow + rim from `shade()`, sized to the part | gradient fills on body parts, or no shadow side at all |
| big eyes from `base.eye()`, lids that act | dot eyes, or eyes that differ in construction from the rest of the cast |
| warm light only for kindness (lantern, bread, the laugh) | warm glows on the "stones" (crystals, rune-stone, wisps) |
| `look` first, then head, then body | everything turning at once, linearly |
| shared `CAST_HEIGHTS` and one scale per depth plane | per-character fudge scales |
| props held through the hand's `hold` callback (z-correct) | props pasted over the fingers |
| draw the dragon seated on a bench built to `seat_h` | benches of arbitrary height (his feet float or sink) |

See the sheets: the gestures page (4) shows the z-correct holds. The faces page (3) shows the
expression range. The lighting page (5) shows how one material reads under every scene light.
