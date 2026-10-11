# API — `engine/fx.py` (effects, comedy marks, story overlays, UI screens, titles)

```python
from engine import fx
```

## Conventions (read first)

* **Pure functions of time.** Every effect with a start time (`t0`, `t_in`, `t_on`) draws
  **nothing before it starts and nothing after it ends**. Continuous effects
  (`motion_lines`, `dizzy_stars` without t0, `heat_squiggles`, `music_notes`,
  `power_aura`, `alarm_wash`, `time_slow`, `vignette`) are driven by an
  `amount`/`intensity` and draw nothing at 0. Ramp the amount yourself (e.g. with
  `core.seg`/`core.tween`). All of this is checked by `preview/fx_check.py`.
* **Scene-local time.** Pass scene `t` and cue times (`info.cue("freeze")`); never hard-code
  dialogue times.
* **Spaces.** Local effects (marks, emotes, auras, rings, screens, label cards) work in
  whatever user space you're in, including inside `core.camera(...)` (pass world coords).
  **Full-frame effects belong in screen space**, after the camera block:
  `flash`, `black`, `whip_pan`, `alarm_wash`, `vignette`, `eyelid_wipe`, `time_slow`,
  `end_card`, `lights_out` (default rect), and also `name_tag` (it slides off the frame edge).
  The Episode 2 reveal effects (`sense_reveal`, `flashlight`, `sense_outline`) work in
  either space: inside a camera pass world coords and a fixed world `rect` (§6).
* **`s`** is a size factor. All sizes below are at `s=1` in logical 1080x1920 px. Medium
  shots usually want s≈1.3–1.8 to match the characters.
* **Safe zone / captions.** Keep text inside x 60..930, y 120..1330. Don't put screens or
  labels in the caption band (y≈1330–1560).
* **Bitrate rules are built in.** Shapes, not particles: ≤ ~12 moving pieces per effect,
  no noise, pulses ≥ 0.6 s period, full-frame flashes ≤ 3 frames.
* **Determinism.** Randomness comes from `core.hash01` with a `seed` argument where
  variety matters (use different seeds for repeated dust/sweat).
* **Caching.** Static parts (tag slabs, title letters, screens, vignettes, label plates)
  are rasterised once into **fx's own layer cache**. It uses the same 1/8-octave
  scale quantisation as `core.cached`, but it is a separate LRU (96 entries), so fx never
  evicts set/background layers from core's 16-slot cache. It can also blit with an alpha,
  and screen-space layers use an exact-scale pixel copy (fast path). `fx.clear_cache()`
  drops it. A cache miss costs a few ms once per process.
* **Costs** below are the mean per frame at 720x1280 (ctx scaled 720/1080), measured by
  `python3 preview/fx_perf.py` over one in-order pass from an empty cache, i.e. what a
  render worker pays. Budgets are < 2 ms per effect, < 4 ms for eyelid_wipe/alarm_wash,
  and < 5 ms for screens. **All are within budget.**

### Character tag colours

`TAG_COLORS = {"tired": "#8fa3f2" (periwinkle), "embar": "#ff8ab4" (pink),
"imp": "#f7b33a" (gold), "boss": "#5fdcc2" (mint), "curiosity": "#26d9c9" (teal)}`.
Aliases are accepted: `tiredness, embarrassment, impulsivity, the boss, periwinkle, pink,
gold, mint, teal (= boss, unchanged), cur, specimen (= curiosity)`. Any `#rrggbb` or `PAL`
key also works. The boss mint is deliberately *not* the special `power` teal; Curiosity's
slab is a deeper cut of the power teal so the white title keeps its contrast.

---------------------------------------------------------------------------

## 1. Name tags

### `name_tag(ctx, title, subtitle, t, t_in, t_out, x=90, y=170, color="tired", align="left", s=1.0, max_w=None)`
Character intro tag: chunky Luckiest-Guy title (white, ink outline, hard ink drop shadow)
on a skewed colour slab with a darker lower band, plus a smaller subtitle (Nunito) on an
ink strip tucked under it. The whole tag tilts about 2°.
* **Timing:** invisible before `t_in`. The slab stretches in with overshoot (0–0.30 s),
  the title pops (0.10–0.40 s) and the subtitle wipes in (0.26–0.52 s); `fx.TAG_IN = 0.5`.
  Then a tiny idle wobble (±0.4°, 2.5 px bob). At `t_out` the subtitle leaves first, then
  the tag slides off its anchor side (left/right) or shrinks (center) over
  `fx.TAG_OUT = 0.32` s. Invisible after `t_out + 0.32`.
* **Anchor:** `(x, y)` = top-left (`align="left"`), top-right (`"right"`) or top-centre
  (`"center"`) of the slab. It auto-shrinks to fit the safe zone (`max_w` defaults to the
  room left before x=930 or x=60).
* **Size:** title 104 px font (caps ≈ 80 px), slab ≈ title width + 70 px, subtitle 46 px.
  At y=170 the whole tag spans y ≈ 135–355 (≈ 210 px with shadow and tilt). EMBARRASSMENT
  at x=90 reaches x ≈ 919.
* Script cues (Ep1): s01 `name_tag(ctx,"TIREDNESS","just wants to play his game",t,0.3,3.0)`;
  s02 `"EMBARRASSMENT","junior lab scientist", color="embar"`;
  s04 `"IMPULSIVITY","a tripwire that never goes off", color="imp"`;
  s08 `"THE BOSS","HushCorp", color="boss"`.
* **Ep2 s01 "perk":** `name_tag(ctx, "CURIOSITY", "specimen 00", t, t_in, t_out,
  color="curiosity")`. Checked: "CURIOSITY" at x=90, s=1 spans x ≈ 90–690 (fits easily, no
  auto-shrink); preview `preview/fx_ep2_ui.png` (last two cells).
* **Cost:** 1.5 ms (rotated sprite blits; 5 ms on the first frame).
* Previews: `preview/fx_tags_phone.png` (phone size), `fx_tags_anim.png`, `fx_tags_align.png`.

---------------------------------------------------------------------------

## 2. Motion, impact and comedy marks

| function | timing | size @ s=1 | look | cost |
|---|---|---|---|---|
| `motion_lines(ctx, x, y, angle, length, t, intensity=1.0, color="ink", n=None, spread=None, width=12, seed=0)` | continuous; nothing at intensity 0 | lines stream back `length` px from (x,y); band `spread` = 0.6·length; 3–6 lines (`n`≤9) | bold tapered ink speed lines **behind** a mover heading along `angle` (rad, 0 = right); each shoots out, stretches, detaches and fades (≈2.2–3.2 Hz) | 0.1 ms |
| `smear(ctx, x0, y0, x1, y1, t, t0, dur=0.38, color="#f4f6f8", width=120, seed=0)` | t0 .. t0+dur | band `width` at the head | teleport zip: three tapered strands from the old spot (x0,y0) to the new one (x1,y1). The head arrives in 15% of dur, the tail retracts, and a cloud poof sits at the origin. Draw the character at (x1,y1) from t0 | 0.3 ms |
| `whip_pan(ctx, t, t0, dur=0.32, direction=1, colors=WHIP_COLORS, seed=0)` | t0 .. t0+dur; peak cover at t0+dur/2 | full frame | 12 bold horizontal streak bands plus a soft wash; **cut scenes at t0+dur/2**. `direction=+1`: streaks travel right→left (camera pans right). Pass `colors` from the two scenes to blend | 0.8 ms |
| `whip_pan_offset(t, t0, dur=0.32, dist=1500, direction=1)` → `(dx, incoming)` | helper | — | camera shift for the whip: outgoing scene eases out by dx, incoming scene eases in from dx | — |
| `impact_star(ctx, x, y, s, t, t0, dur=0.45, color=STAR_YELLOW, inner="#ffffff", word=None, word_color="danger", seed=0, spikes=11)` | t0 .. t0+dur | r ≈ 110 px (spikes 80–135) | yellow comic burst with a white core, overshoot pop, 6 flying impact ticks; optional `word="BONK!"` in Bangers | 1.1 ms |
| `dust_puff(ctx, x, y, s, t, t0, seed=0, dur=0.8, color=DUST, spread=1.0)` | t0 .. t0+dur | two clouds rolling ~130 px each way from the ground point (x,y), ~70 px tall | landing/skid dust: two puffy clouds (one outline each) + 4 flecks behind | 0.3 ms |
| `plaster_dust(ctx, x, y, s, t, t0, seed=0, dur=1.4, width=220, n=10, fall=520, color=...)` | t0 .. t0+dur (cloud gone by 0.8 s) | cloud `width` px wide under the ceiling line y; ≤12 flecks 12–28 px falling `fall` px | ceiling bonk: a puffy plaster cloud bulging down + tumbling flecks | 0.4 ms |
| `dizzy_stars(ctx, x, y, s, t, t0=None, dur=None, n=3, rx=95, ry=26, speed=1.0, layer="both", color=STAR_YELLOW, ring=True)` | continuous; with t0 pops in 0.3 s; with dur pops out by t0+dur | orbit 190×52 px around (x,y) (head top); stars r ≈ 25 | 3 (≤5) yellow stars orbiting at 0.85 turns/s on a faint dashed ring; far stars smaller/darker. `layer="back"` before drawing the character, `"front"` after | 0.35 ms |
| `shock_lines(ctx, x, y, s, t, t0, dur=1.0, rx=200, ry=420, color="#fff36b", bolts=8, seed=0)` | t0 .. t0+dur (pops 0.12 s, fades last 0.22 s) | jagged ring rx×ry around the figure's centre (x,y), 8 bolts 110–170 px | the "struck by lightning" freeze: a crackling yellow/white jagged outline + filled zigzag ⚡ bolts; pattern re-rolls 8×/s. Fit rx/ry to the figure (full Emb in a doorway ≈ rx 230, ry 520) | 1.25 ms |
| `flash(ctx, t, t0, frames=2, color="white", peak=1.0)` | frames [t0, t0+frames/24); frames ≤ 3 | full frame | flash at alpha 1.0 / 0.7 / 0.4 per frame. Use with shock_lines (same t0) and on the s11 impact | 0.1 ms |
| `sweat_fly(ctx, x, y, s, t, t0, seed=0, n=4, dur=0.65, side=0, color=SWEAT_BLUE)` | t0 .. t0+dur | drops r 14–19, flung ~200 px | blue teardrops (ink outline, highlight) flicking off the temple at (x,y) on ballistic arcs, tips trailing. `side` +1 right, −1 left, 0 both. Repeat with new t0/seed for panic | 0.2 ms |
| `heat_squiggles(ctx, x, y, s, t, amount=1.0, width=170, color=HEAT_RED, n=None)` | continuous; nothing at 0 | 2–5 lines across `width`, 50–80 px tall above the head top (x,y) | hot-pink wavy heat lines with a pale core, rising/fading on a 1.8 s loop; count, height and opacity follow `amount` (tie to Emb's blush) | 0.3 ms |
| `tap_marks(ctx, x, y, s, t, t0, taps=2, gap=0.32, angle=-pi/2, label="tap", color="ink")` | t0 .. t0+(taps−1)·gap+0.6 | ticks ~30–60 px from the contact point; word 46 px | "tap tap": a fan of 3 ink ticks per tap at (x,y) aimed along `angle` + a small Bangers "TAP" popping up and fading. `label=None` for ticks only | 0.3 ms |
| `emote(ctx, kind, x, y, s, t, t0, dur=None, color=None)` | pops in at t0 (0.25 s overshoot); if dur, pops out by t0+dur | ~90–130 px, centred on (x,y) | `question` white "?" (tilting), `exclaim` yellow drawn "!" + burst ticks, `sweatdrop` big anime drop sliding 18 px, `anger_vein` red 💢 cross (0.7 s pulse), `sparkle` 3 twinkles, `heart` pink heart floating up with a beat, `zzz` three Z's drifting up-right (1.8 s loop), `gulp` "GULP" with throat arcs and a swallow squash. `fx.EMOTES` lists them | 0.1–0.35 ms |

Previews: `preview/fx_marks1.png`, `fx_marks2.png`, `fx_emotes.png`; at real scale in a full
frame: `fx_phone.png` (shock freeze, ceiling bonk, dazed).

---------------------------------------------------------------------------

## 3. Story effects

### `music_notes(ctx, x, y, s, t, intensity=1.0, direction=1, color="#fff3c4", n=4, rise=190, period=2.4, seed=0)`
Notes leaking from a headphone cup at (x, y): eighth notes and beamed pairs drawn as shapes
(cream with ink outline, no font glyphs). They rise `rise` px and drift ~120 px toward
`direction` (+1 right / −1 left) on a 2.4 s cycle, fading in and out. At most `n` (4) on
screen; `intensity` 0..1 thins them out. Notes ~45 px tall. Continuous. **Cost 0.35 ms.**
s05: `music_notes(ctx, cup_x, cup_y, 1.3, t, 0.8)`.

### `ripple_rings(ctx, x, y, s, t, t0, color="power", n=3, interval=0.4, ring_dur=1.5, max_r=760, width=9, outline_fn=None, outline_fill=0.12)`
The new SENSE: teal sonar rings from (x, y), one every `interval` s starting at t0, each
growing from 26 to `max_r·s` px over `ring_dur`. There is a ping dot at the centre and a
soft halo while each ring is young. Visible t0 .. t0+(n−1)·interval+ring_dur (+0.6 s
afterglow when `outline_fn` is given).
**outline_fn(ctx)** appends a silhouette **path** (no fill/stroke), e.g. the shadow creature.
As a ring reaches its bounding box, the path lights up with a teal glow outline and a faint
fill, then fades 0.6 s after the last ring passes. **Cost 1.5 ms.** s12 "sense".

### `power_aura(ctx, x, y, w, h, t, amount, color="power", outline_fn=None, pulse=0.0)`
Soft teal aura, static for a given amount (cached per 0.05 step), so it is cheap and
bitrate-friendly. Without `outline_fn`: concentric soft strokes around a capsule centred at
(x, y), size w×h (0.45 ms). With `outline_fn` (a silhouette path): 5 widening soft strokes
plus a bright core line around the path (1.1 ms). Draw it **before** the character so the
glow sits behind. `pulse>0` adds a gentle 1.2 s breathing. s11 "powers", s12–13 glows.

### `eye_glint(ctx, x, y, s, t, t0, dur=0.4, color="white", halo="power")`
Tiny glint: a 4-point twinkle (r ≈ 26) with a short horizontal flare and a teal halo that
blooms, turns 45° and vanishes by t0+dur. `halo=None` for a plain white glint. **0.1 ms.**

### `eyelid_wipe(ctx, t, t0, dur=1.3, blinks=2, color="#07040b", cy=0.47*H)`
Waking-up POV (s12 opens out of s11's black). Screen space. At t0 it paints **full black**
(hold ~7%). Two big dark lids with curved, lens-shaped edges (soft-edged by 4 layered alpha
bands with a warm tint near the edge) part slowly and half-close `blinks` times (default
2: open 0.46 → 0.12, 0.66 → 0.36). Then they open fully, leaving the frame exactly at
t0+dur. A soft dark vignette recedes over the whole duration (blur suggestion). Draw the
POV scene first, then this. **Cost 2.4 ms** (13 ms on the first frame, vignette raster).

### `alarm_wash(ctx, t, amount=1.0, beacon=(540, 120), period=1.6, tint_period=1.2, color="danger", lamp=False)`
Rotating red beacon, screen space. A deep-red tint pulses gently (alpha 0.34–0.48 ×
amount, sine period `tint_period` ≥ 0.7 s, no strobing). Two flat, two-band red light
cones sweep from `beacon` (one rotation per `period`); a beam is widest and brightest when
facing camera. `lamp=True` draws a small glowing lamp at the beacon. Ramp `amount` in over
~0.3 s at the alarm cue. **Cost 0.9 ms.**

### `vignette(ctx, amount=0.5, color="ink", inner=0.55, x=0, y=0, w=W, h=H)`
Static elliptical darkening frame, cached once per (color, inner, rect) and blitted at
opacity `amount` (fully transparent centre skipped). `inner` = where darkening starts
(0..0.95 of the ellipse radius). **Cost 1.5 ms** (≈12 ms on the first frame).

### `heartbeat_sync(ctx, x1, y1, x2, y2, t, t0, sync, s=1.0, period=0.9, c1="#ff6f91", c2="#ff6f91", glow="power", t1=None, link=True)`
Two small pink hearts (r ≈ 30, ink outline, highlight) on soft teal glows beating
"lub-dub" every `period`. At `sync=0` heart 2 beats off-phase with a wandering lag; as
`sync` → 1 the lag shrinks smoothly to 0. Past sync 0.6, a dotted arc between them lights
up on each shared beat. Fades in 0.3 s from t0; optional fade-out ending at `t1`. Ramp sync
over a few seconds for the s12 bonding beat. **Cost 0.6–0.9 ms.**

### `time_slow(ctx, t, amount, cx=540, cy=864)`
Slowed time during the fall (s11 "powers"), screen space: a cool teal tint, 18 faint
tapered radial streaks from (cx, cy) and a dark-teal vignette, all in one static cached
layer blitted at `amount` (static on purpose: bitrate). Pair with `power_aura`. **Cost
1.2 ms** (13 ms on the first frame).

### `black(ctx, a=1.0)`
Full black paint (s11 "black" beat only). 0.2 ms.

Previews: `preview/fx_story.png`, `fx_full.png` (whip, eyelid sequence, alarm, vignette,
time_slow, flash), `fx_phone.png` (sense rings revealing a hidden silhouette, aura, bond
hearts, notes at real scale).

---------------------------------------------------------------------------

## 4. UI screens

Every screen draws **into a rect (x, y, w, h)** and scales from its design width (search and
lab 900 px wide, tablet 600, hologram 500), so text sizes scale with `w`. For phone
legibility, use roughly the design width in the 1080 frame for the readable inserts. All
screens are clipped to rounded corners and outlined in ink. Static content is cached per
phase.

### `search_screen(ctx, x, y, w, h, t, t_type, query="HUSHCORP", t_results=None, t_site=None, char_dt=0.11)`
Browser (chrome, tab, address bar) with a parody search engine, "seekly".
* **Home** (until `t_results`): search box with a blinking caret (1 s period). The query
  types one letter every `char_dt` from `t_type` (50 px text), then the box glows on
  "Enter".
* **Results** at `t_results` (default typing end + 0.35 s): they wipe in. "HushCorp —
  Official Site / We keep secrets so you don't have to.", "Research Campus — Visitor
  Entrance", "Is HushCorp hiding something? — This thread has been removed." A mouse
  cursor glides to result 1 (+0.35..0.85 s) and clicks (+0.95 s).
* **Site** at `t_site` (default `t_results` + 1.3 s): a loading bar, then the HushCorp site
  (logo header, dark-teal hero "HUSHCORP" / "We keep secrets so / you don't have to.").
  The "Research Campus — Visitor Entrance" card slides up (+0.45 s), with a mini map and a
  red map pin that drops and bounces (+0.9 s), plus a "Get directions" button.
* `type_times(t_type, query, char_dt)` → per-key times for typing SFX.
* Designed for 900×600 (landscape); taller rects get a bigger hero and map.
* **Cost 0.8 ms** (4.5 ms on the first frame of each phase).
* s10 "search": `search_screen(ctx, 90, 380, 900, 620, t, info.cue("search")+0.3)`.

### `lab_screen(ctx, x, y, w, h, t, t_on, off=False)`
HushCorp wall screen (dark navy, faint teal grid). It powers on at `t_on` like a CRT: a
bright line opens vertically over 0.25 s, with a brief glare. Content: header **"SPECIMEN
ZERO"**; a framed panel with a big glowing-outlined creature silhouette (sleek, long fin
ears swept back, slim legs, long S-curved finned tail, teal eye slit) with a scan bar
(2.4 s loop). **"STATUS:" + "ESCAPED"** box blinks bright red ↔ dark (1 s period, soft
edges). **"LAST SEEN:" "SEWER LINE 7"**, plus a little sewer map whose line 7 is highlighted
amber, with a pulsing red last-seen dot. Landscape layout for w ≥ 1.18·h; tall rects
stack vertically. `off=True` draws dark glass before `t_on`; otherwise nothing.
**Cost 0.9 ms.**

### `tablet_screen(ctx, x, y, w, h, t, portrait_fn=None, t_on=None, t_check=None, glow=True, bezel=True, portrait_key=None)`
The Boss's dossier: a charcoal bezel (`bezel`) and a soft cyan glow (`glow`) around an icy
screen. A dark-teal HushCorp header with "DOSSIER"; a portrait frame; **"SUBJECT:"
"TIREDNESS"**; three redacted bars; **"KNOWN ASSOCIATE:" "EMBARRASSMENT"** with a teal check
box whose ✓ is drawn on (stroke animation, small pop) at `t_check`.
* `t_on=None`: fully on, check drawn.
* With `t_on`: it wakes over 0.25 s, the associate row fades in (+0.4 s) and the check
  draws at `t_check` (default `t_on` + 0.75).
* Designed for 600×450; taller rects centre the content.
* **Cost 1.2 ms.**

### `hologram_photo(ctx, x, y, w, h, t, t_on, portrait_fn=None, label="SUBJECT: TIREDNESS", color=HOLO, cache_key="auto")`
The photo of Tiredness appearing on the glass wall (s09).
* A dark-glass backing panel (so it reads on light walls), cyan corner brackets and a soft
  glow.
* The portrait is tinted cool cyan-white with static scanlines, at 90% opacity, with a mono
  label.
* **Flicker-on:** 8 frames of alpha steps from `t_on` (0, .75, .1, .95, .35, .85, .55, 1),
  with 3 glitch frames that shift a horizontal slice by 16 px. Then steady.
* Nothing before `t_on`.
* The tinted photo is cached (`cache_key="auto"` derives the key from `portrait_fn`). Pass
  `cache_key=None` if your portrait animates.
* **Cost 1.1 ms.**

**Portrait callback contract** (tablet + hologram): `portrait_fn(ctx, cx, cy, s)` draws a
head-and-shoulders bust centred at (cx, cy). `s = 1` means the frame is a **300 px square**
(head ≈ 150 px tall), and output is clipped to the frame. `None` uses
`fx.standin_portrait`: Tiredness in a navy hoodie with headphones round his neck, messy mop
with cowlick, heavy lids and bags. Use a module-level function so the cache key is stable.

### `label_card(ctx, x, y, text_, t, t_in, color="hush", t_out=None, sub=None, size=52, style="plate", max_w=820, rot=-0.025)`
A readable sign or label centred at (x, y): a cream plate, ink outline, soft ink drop
shadow, tilted −1.5°.
* `text_` is in Inter Black, ink colour; `\n` gives multiple lines. The optional `sub` line
  is smaller (0.64×).
* `style="plate"` adds a `color` stripe on the left; `style="hazard"` adds a yellow/ink
  hazard-stripe header.
* It pops in with overshoot over 0.3 s at `t_in` and pops out over 0.2 s at `t_out`.
* It auto-fits `max_w`. At size 52 the card is ~130 px tall.
* s11 close-up: `label_card(ctx, 495, 640, "CARRIER", t, t_in, "warn", sub="BITE TRANSFERS TRAITS", style="hazard")`
  or the single-line `"CARRIER — BITE TRANSFERS TRAITS"`.
* **Cost 0.5 ms.**

### `hush_logo(ctx, x, y, s=1.0, wordmark=True, color="hush", hole="#ffffff", text_color="ink", text_size=None)`
The HushCorp logo: a teal circle (r 40·s) with a keyhole, centred at (x, y), plus the
wide-tracked "HUSHCORP" wordmark (Nunito) to the right. Exposed for convenience (screens
use it).

Previews: `preview/fx_search.png` (all phases), `fx_screens.png` (lab power-on, portrait
layout, tablet + check), `fx_screens2.png` (hologram flicker frames, label cards),
`fx_screens_detail.png` (1:1-ish legibility check).

---------------------------------------------------------------------------

## 5. Titles

### `end_card(ctx, t, t0, title="TIREDNESS", cx=468, baseline=730, size=168, t_tbc=None, tbc="to be continued…", t_out=None, subtitle=None, t_sub=None)`
The end title, in screen space over the caller's shaft scene. Hide captions yourself.
* **Look:** big Luckiest-Guy letters (≈130 px tall, auto-fit to ≤ 840 px wide). Each has a
  periwinkle fill, a darker lower band, a thin highlight, a thick ink outline, a hard ink
  drop shadow, and a soft dark halo, so it reads over the busy teal pods.
* **Timing:**
  * 0–0.7 s: letters pop in left→right.
  * 0.75–1.75 s: the word **nods off**. Later letters sink and tip forward, and the last S
    slumps most.
  * From +1.1 s: little white "z"s drift up off the S (1.6 s loop, 3 max).
  * At `t_tbc` (default t0 + 1.5): "to be continued…" (Fredoka, white, ink outline) fades
    up under it.
  * It holds until the caller stops drawing; optional 0.4 s fade-out from `t_out`.
* **Placement:** occupies x ≈ 50–930 and y ≈ 480–890, z's included.
* The settled/sagging word is composed into one cached layer per sag step (14 steps), so
  it's cheap. **Cost 1.1 ms** (≈6–10 ms on cache-miss frames during the 1 s sag).
* s13 "title" (3 s): `end_card(ctx, t, info.cue("title"))`.
* **Episode subtitle (Ep2).** `subtitle="Episode 2: Lights Out"` adds a skewed ink ribbon
  (Fredoka, ≈ 49 px at size 168; the part up to and including ':' is power teal, the rest
  white) between the title and "to be continued…". It wipes in left→right over 0.42 s at
  `t_sub` (default t0 + 1.15, i.e. during the nod-off). With a subtitle the tbc line moves
  down to baseline + 1.34·size (≈ 955) and defaults to t0 + 2.0, so the card spans
  y ≈ 480–975 (still well above the caption band). `subtitle=None` (default) is exactly the
  Episode 1 card.
* **Ep2 s08 "title" (3.6 s):** `end_card(ctx, t, info.cue("title"), subtitle="Episode 2: Lights Out")`
  (captions hidden). Timeline: letters 0–0.7 s, nod-off 0.75–1.75 s, subtitle 1.15–1.57 s,
  tbc 2.0–2.6 s, then a 1 s held frame. Cost 1.2 ms (0.7 ms warm).
* Previews: `preview/fx_end.png` (timeline over teal), `fx_end_detail.png` (teal vs grey);
  Ep2: `fx_ep2_end_full.png`, `fx_ep2_ui.png` (end 1.3 / 2.0 / 3.4).


---------------------------------------------------------------------------

## 6. Episode 2: darkness, the sense, flashlights, lights out, eyes, dream, phone, feed

### 6.0 How the reveal effects work (read once)
`sense_reveal`, `sense_outline` and `flashlight` reveal a **lit world** that you draw with a
callback, `draw_lit(ctx)`, in the current user space over `rect` (default the 1080x1920
frame).
* **Bake once, blit per frame.** On the first call for a `key`, draw_lit is rendered ONCE at
  the device scale. Its pixels are then treated with numpy into a small family of bitmaps:
  * `echo`: teal echo image (bright teal edge lines with a bloom, over dark teal fills that
    follow the scene's luminance);
  * `flare`: white-hot lines only;
  * `outline`: lines + bloom on transparent;
  * `dark`: darkness with a faint outline hint;
  * `warm`: the flashlight's warm-tinted lit world.
  
  They are cached in a separate 14-entry LRU (`fx.clear_bakes()` drops it). Per frame only
  aliased clip shapes are composited with pixel copies of those bitmaps.
* **`key`** is any hashable. It must change whenever the lit drawing changes (another set
  state, another pose). `key=None` re-bakes every frame (100–250 ms!), so never use it for
  sets.
* **Cold cost:** the first frame per key costs ≈ 100–250 ms at 720p (render + numpy), once
  per process (each render worker pays it once).
* **Moving characters:** don't bake them into draw_lit. Draw them yourself on top (dim, or
  lit by `sense_at`), or pass them as sense_reveal's `live` layer.
* **Cameras.** Inside `core.camera(...)`, pass world coords (pings, lens) and a **fixed world
  `rect`** that covers the whole shot (not the per-frame view).
  * Static or panning cameras are fast: blits snap to whole device pixels (≤ 0.5 px, which
    is invisible).
  * A **zooming** camera re-bakes at every new zoom with the default `exact=True`. Pass
    `exact=False` to bake at 1/8-octave scale steps instead (a bilinear blit, ≈ 1.5x the
    cost, and a re-bake roughly every 9% of zoom).
  * `s` scales all sense distances; at camera zoom Z use `s = 1/Z` for the same on-screen
    rings.
* Everything is a pure function of `t` and the arguments, and deterministic. It is checked
  by `preview/fx_ep2_check.py`.

### 6.1 `sense_reveal(ctx, t, pings, draw_lit, draw_dark=None, key=None, rect=None, s=1.0, speed=None, band=None, soft=None, fade=None, max_r=None, color="power", dark=fx.DARK, hint=None, rings=True, live=None, live_rect=None, exact=True, flare=0.6, live_key=None)`
**The new sense, and the signature visual of the episode.** It draws the WHOLE frame.

**Darkness.** `draw_dark(ctx)`, e.g. the set at power 0. Without it, the function paints
`fx.DARK` (#04080b) with a faint `hint` (default 0.05) of the outline, so the world stays
"almost black but readable". This is pre-composed into one opaque bitmap, a plain copy.
Keep `hint` static: it is quantised to 0.01 and part of the bake key, so ramping it
re-bakes.

**Pings.** Each ping `(t0, x, y)` or `(t0, x, y, k)` emits a sonar ring. Its band reveals
`draw_lit` as a teal echo image (bright edges, dark fills). Behind the band the reveal fades
to an afterglow of lines, then darkness. `k` (default 1) scales a ping's reach and brightness:
`k ≈ 0.4–0.5` is a small quiet ping (s03 hiding).

**Defaults** (`fx.SENSE`; px at s=1, scaled by `s`):

| part | value | look |
|---|---|---|
| speed | 820 px/s | constant |
| leading soft edge | 80 px | 6 steps |
| band | 300 px (≈ 0.37 s per point) | full echo, easing 1.0 → 0.64 |
| afterglow | `fade` 0.85 s (≈ 700 px) | eases to 0; fills vanish first, lines linger |
| reach `max_r` | 1500 px | strength fades from 750 px to max_r |
| ping lifetime | ≈ 3.1 s | nothing drawn after it |

So each point is lit ≈ 1.2 s per ping.

**Visible sonar** (`rings=True`):
* a crisp light-teal leading line (4 px) on two flat teal halo bands (13 / 32 px);
* a whisper line at the back of the band;
* at the source, for 0.45 s, a ping flash: a white dot, an expanding ring and a glow.

`flare` (0..1, default 0.6) is the wavefront flash: lines light up white-hot as the front
passes over them.

**Live layer.** `live(ctx)` is optional animated content (Curiosity nodding in the dark). It
is drawn and echo-treated per frame inside `live_rect=(x0, y0, w, h)` (keep that small). It
is revealed exactly like the set, and only when a band touches the rect. Cost ≈ +8–10 ms per
frame for a 420x330 rect at 720p while a band touches it. `live_key` caches the live layer:
e.g. `("cur", int(t*12))` updates at 12 fps, and a pose name suits a still pose.

**Merging.** Concentric pings (same x, y within 1 px) are merged into one union profile and
composited once.

**Order.** Draw the dark world, the reveal and the rings with this call, then draw your
characters on top (Tiredness dim with his hood; Curiosity's `eyes_in_dark`).

**Cost at 720p** (screen space; a camera at zoom 1.55 is similar). The budget is < 8 ms:

| case | mean | worst |
|---|---|---|
| 1 ring | 2.5 ms | 4.4 ms |
| 2 rings | 4.2–4.5 ms | 6.0–6.7 ms |

This is the fx cost only; add your draw_dark (a cached set ≈ 1.4 ms).

**Previews.**
* `fx_ep2_sense.png`: a time strip on a busy catwalk (rails, pods, stair, pipes).
* `fx_ep2_sense2.png`: a dark set, 2 pings and a live creature.
* `fx_ep2_sense_full_a/b.png`: 1:1 frames.
* `fx_ep2_sense_shaft.png`: `sets.shaft` inside a camera at zoom 3.2 with s=1/3.2.
* `fx_ep2_s02.png` / `fx_ep2_s02_full.png`: an s02-like medium shot with the hooded
  Tiredness, 3 pings including a small k=0.45 one, and the live Curiosity.

```python
pings = [(info.cue("ping"), hx, hy), (info.cue("ping") + 1.4, hx, hy)]   # from his head
fx.sense_reveal(ctx, t, pings, lambda c: sets.shaft(c, 0, "bg", power=1), # lit (baked)
                lambda c: sets.shaft(c, t, "bg", power=0),                # dark
                key="shaft_s02", rect=WORLD_RECT, s=1 / zoom)              # inside the camera
```

### 6.2 `sense_at(t, pings, x, y, s=1.0, ...)` → 0..1 and `sense_active(t, pings, ...)` → bool
* `sense_at` is how strongly the sense reveals the point (x, y) right now (the max over the
  pings, same params as sense_reveal). Use it to light live things by hand, e.g. fade a
  character's teal rim in as the band passes, or dim Curiosity's glowing eyes while its
  echo is revealed.
* `sense_active` is True while any ping is visible (front, band or afterglow).

### 6.3 `sense_outline(ctx, draw_lit, key=None, rect=None, a=1.0, fill=False, color="power", exact=True)`
The teal **edge-only** look of a drawing: bright lines + bloom on transparent. `fill=True`
gives the full echo image instead. It is baked once per key and blitted at opacity `a`.
Use it for a held "sensed" frame, a sense-POV insert, an afterglow, or a faint outline of
the world over darkness. It shares the bake with sense_reveal when key/rect match.
**Cost 0.6 ms.** Preview `fx_ep2_outline.png`.

### 6.4 `flashlight(ctx, x, y, angle, length, spread, t, draw_lit, key=None, rect=None, power=1.0, warm=0.3, soft=0.5, haze=0.035, hotspot=1.0, lens=True, s=1.0, flicker=0.0, seed=0, exact=True, warm_color=fx.FLASH_WARM)`
A torch cone from the lens at (x, y) pointing along `angle` (radians, 0 = right, π/2 =
down). `length` is its reach in px; `spread` is the FULL cone angle (≈ 0.45–0.7 rad reads as
a torch). Inside the cone it reveals the **normally lit world** (draw_lit, baked once per
key) over the dark frame you already drew:
* 9 nested soft steps give soft sides and a soft far end (the falloff runs from 0.7 to
  1.06 of length);
* `warm` sets the slight warm tint;
* `haze` is a faint beam haze (lit dust in the air);
* the bright hotspot near the lens is a small radial glow;
* a lens glow plus a white lens ellipse marks the torch.

`power` 0..1 switches or dims it (nothing at 0). `flicker` 0..1 adds a gentle, smooth,
irregular dimming (the scared guard), never a strobe. Two cones = two calls, sharing one
bake; where they overlap they union.

`flashlights(ctx, t, cones, draw_lit, key=None, rect=None, **kw)` is a convenience wrapper:
cones = `[(x, y, angle, length, spread), ...]` or dicts with those keys plus per-cone
extras.

Draw the torch body (in the guard's hand) yourself. **Cost: 2 cones 4.6 ms** (budget 6).
Previews `fx_ep2_flash.png`, `fx_ep2_flash_full.png`.

### 6.5 `lights_out(ctx, t, t0, sections=6, gap=0.38, flicker=0.4, rect=(0,0,W,H), dark=0.9, color="#020509", floor=0.0, order="top", draw=True, seed=0)` → powers
The lights dying section by section.
* **Sections.** An int (equal horizontal bands over `rect`) or a list of `(y0, y1)` bands.
  `order` is "top" (the far top dies first), "bottom", or a list of band indices in dying
  order.
* **Each section:**
  1. it flickers gently for `flicker` s (≥ 0.3; two soft dips of ≈ 45% and ≈ 68%, each
     ≥ 3 frames, so it is not a strobe);
  2. it **chunks** to dark;
  3. a short ember (0.16) cools to `floor` over ≈ 0.5 s.
* **Overlay.** A heavy flat darkening band with alpha = `dark·(1 − power)` (hard edges,
  graphic).
* **Return value.** The per-section power list (0..1, in band order, top to bottom), so the
  set can dim its own lamps and pods. `draw=False` only computes it (ctx may be None).
  Nothing is drawn before t0. After the last chunk the full darkness holds until you stop
  calling.
* `lights_out_times(t0, sections, gap, flicker)` gives the chunk times (die moments, for
  the "chunk" SFX): `t0 + flicker + i·gap`.
* `lights_out_power(t, t0, i, gap, flicker, floor)` gives one section.

Defaults: 6 sections, last chunk at t0 + 2.3 s (s01 "click" + "dark").
**Cost 0.3 ms.** Preview `fx_ep2_lights.png` (it ends on the two eye pairs).

### 6.6 `eyes_in_dark(ctx, x, y, s, t, kind="curiosity", blink=None, look=(0, 0), amount=1.0, gap=None, tilt=0.0, seed=0, lid=None, color="power", glow=True)`
A pair of glowing teal eyes in darkness, centred at (x, y) (between the eyes).
* **Kinds:**

  | kind | eyes at s=1 | gap (centres) | look |
  |---|---|---|---|
  | `"curiosity"` | 62x70 px | 112 px | big and bright: round, a slight lid, dark round pupils, two catchlights, a lighter iris around the pupil, a soft 105 px glow each, a sassy tilt |
  | `"tired"` | 30x23 px | 66 px | small and faint: heavy-lidded (46%) half-moons with the outer corners drooping, a lit lid rim, tiny pupils, a 44 px glow at 0.17 |

* **blink:** `None` = automatic natural blinks (seeded; Curiosity 0.22/s, Tiredness
  0.18/s), or a number 0..1 (1 = shut, which leaves a faint lash line). Drive slow blinks
  yourself with `core.tween`.
* **look** (−1..1, −1..1) slides the pupils. **amount** 0..1 fades everything (nothing at
  0). **lid** overrides the resting lid. **tilt** rotates the pair.
* Match the rigs: a Curiosity at s≈1.4 wants s≈1.4.
* **Cost 0.5 ms per pair.** Preview `fx_ep2_eyes.png` (blink 0 / look / 0.5 / 0.85 / 1, and
  phone-size pairs).

### 6.7 `daydream(ctx, x, y, s, t, t0, t1, draw_content, tail=None, seed=0, fill="#f7f2ff", glow=True)` and `dream_bed(ctx, s=1.0, t=0.0)`
A soft thought bubble centred at (x, y).
* **Shape:** a cream-lavender cloud (11 lobes, ink outline 6 px, soft white glow, lavender
  shading on the lower lobes), ≈ 600x440 px at s=1.
* **Trailing dots:** three dots (r 11/17/25) lead from `tail`, which you put just above the
  dreamer's head (default: lower-left of the bubble, (x − 250s, y + 300s)).
* **Timing:**
  * the dots pop in at t0, +0.08 and +0.16 s;
  * the cloud puffs in from t0 + 0.3 with staggered lobes (done by ≈ t0 + 0.85,
    `fx.DREAM_IN`);
  * it holds with a gentle breathing and bob;
  * from `t1` it dissolves: fade, slight grow, lobes drifting apart, dots fading in
    reverse. It is gone by t1 + 0.8 (`fx.DREAM_OUT`). Nothing outside t0 .. t1 + 0.8.
* `draw_content(ctx, s, t)` is drawn with the origin at the bubble centre, clipped inside
  the cloud. The content area is ≈ 470x330 px at s=1.
* **Ready-made content `dream_bed`:**
  * a dreamy dusk-violet backdrop with a soft golden glow and five stars;
  * a cosy wooden bed (side view) with a big fluffy pillow and a periwinkle quilt with a
    turned-down fold;
  * three white z's floating up off the pillow (2.4 s loop).

  The static part is cached.
* **s06 "tempt":** `fx.daydream(ctx, 600, 430, 1.0, t, info.cue("tempt"), info.cue("look") - 0.4, fx.dream_bed, tail=(head_x + 60, head_top_y))`.
* **Cost 2.8 ms.** Previews `fx_ep2_dream.png`, `fx_ep2_dream_full.png`.

### 6.8 `phone_screen(ctx, x, y, w, h, t, messages, typing=None, contact="Embarrassment", t_on=None, clock="6:12", buzz=True, body=True)` and `phone_times(messages, typing=None)`
A phone, body plus messaging app, in rect (x, y, w, h) = the whole device. It is designed
at 500x1000, so everything scales with `w`.
* **Readable at phone size:** at w ≈ 580 the bubble text is ≈ 60 px in the 1080 frame. For
  the s08 insert use e.g. `(250, 150, 580, 1160)`: the device then ends at y = 1310, above
  the caption band.
* **UI:**
  * a status bar ("6:12", signal, battery) and a notch;
  * a header with a back chevron, a pink avatar (tiny Embarrassment: ginger tuft and
    glasses), the contact name and "mobile";
  * a day stamp;
  * the thread, then an input field with a send button.
* **`messages`** = `[(t, "in"|"out", text), ...]` (or dicts). An incoming bubble (grey, left)
  pops in at its t with a **BUZZ**: a 0.7 s decaying jitter of the whole phone (≥ 0.6 s, so
  it registers) plus ink buzz arcs on both sides. `buzz=False` skips it.
* **The screen** is dark glass before `t_on` (default: the first incoming message). It
  wakes over 0.2 s.
* **`typing`** = `(t_start, text[, char_dt=0.24[, t_send]])`.
  * The reply is typed letter by letter into the input field, with a blinking caret
    (1 s period); the send button turns blue.
  * At `t_send` (default last key + 0.5 s), the **send whoosh**: the bubble flies from the
    input bar up into the thread in 0.3 s with speed streaks, and the send button pulses.
  * "Delivered" fades in after 0.5 s.
* **`phone_times`** gives the SFX times: `{"buzz": [...], "keys": [...], "send": t}`.
* **s08 "phone":** `msgs = [(c, "in", "you ok?")]; typing = (c + 0.9, "zzz")` with
  `c = info.cue("phone") + 0.3`. Buzz at c, keys at c + 0.9 / 1.14 / 1.38, send at c + 1.88
  (fits the 2.4 s beat).
* **Cost 3.0 ms** (the first lit frame builds the UI cache). Previews `fx_ep2_phone.png`,
  `fx_ep2_phone_full.png`.

### 6.9 `monitor_feed(ctx, x, y, w, h, t, draw_feed, style="night", label="SHAFT CAM 03", t_on=None, rec=True, tc0=8027, cache_key=None, vignette_=0.65, res=0.5)`
A security-camera feed in rect (x, y, w, h). It is designed at 600 px wide, so the overlay
text scales with w.
* **The scene:** `draw_feed(ctx, x, y, w, h, t)` draws into the rect (clipped). It is then
  **night-vision tinted**:
  * an HSL colour tint: style `"night"` = teal-green, `"teal"` = HushCorp teal, `"mono"` =
    grey;
  * lifted blacks;
  * vignetted edges.
* **The overlay:**
  * static scanlines (6 px pitch);
  * corner brackets and a centre crosshair;
  * the camera `label` (top-left, mono);
  * **REC** with a softly blinking red dot (1 s, smooth, no strobe);
  * a running **timecode** `HH:MM:SS:FF` = tc0 + t (bottom-left);
  * "IR" (bottom-right).
* **`t_on`:** the feed powers on like a CRT, a bright line opening over 0.25 s. Nothing is
  drawn before t_on.
* **Rendering:** a live feed renders at `res` = 0.5 of the device resolution (a soft CCTV
  image, 4x fewer pixels to tint) and is scaled up; `res=1` gives full detail.
  `cache_key=...` caches a static tinted feed.
* **Cost:**

  | case | cost |
  |---|---|
  | live 900x640 | 4.3 ms |
  | live 430x300 | 1.3 ms |
  | cached | 1.4 ms |

  Plus your draw_feed (draw it from cached layers).
* **s01 control room:** `fx.monitor_feed(ctx, mx, my, mw, mh, t, draw_two_on_catwalk)` in a
  monitor of the wall.
* Previews `fx_ep2_feed_full.png`, `fx_ep2_ui.png`.

### 6.10 Small marks (Ep2 checklist)
| need | function | notes |
|---|---|---|
| bonk on the pipe (s02) | `bonk_star(ctx, x, y, s, t, t0, dur=0.7, word="BONK!", **kw)` | = `impact_star` with a 0.7 s hold (≥ 0.6 s, SPEC §0.8) and the BONK! word. Add `dizzy_stars`/`plaster_dust` for the settle. 1.3 ms |
| glass case smash (s07) | `props.shards(...)` (engine/props.py, exists) | ≤ 15 shards |
| lockdown shutter sparks (s07) | `sparks(ctx, x, y, t, t0, seed=0, s=1.0, n=10, angle=-π/2, spread=2.6, dur=0.8, speed=950, gravity=2300, color="#ffc23a", flash_=True)` | ≤ 12 hot streaks (orange halo, yellow body, white core) flying around `angle` ± spread/2 on ballistic arcs, shrinking and fading, plus a 0.14 s white burst at the source (local, not a full-frame flash). Use a new seed per shutter. 0.4 ms |
| a tear (s04 hurt) | `tear_drop(ctx, x, y, s, t, t0, dur=2.2, side=1, length=120, color="#bfe8ff")` | wells on the lower lid at (x, y) (0–0.6 s, r ≈ 10 px at s=1), clings, then rolls `length` px down the cheek curving toward `side`, leaving a faint wet trail; gone by t0+dur. 0.1 ms. The creature rig's own `wet` eyes give the glisten |
| floating zzz (s08 sleep) | `emote(ctx, "zzz", x, y, s, t, t0)` (exists) | three Z's drifting up-right, 1.8 s loop |
| red alarm (s07) | `alarm_wash(ctx, t, amount)` (exists) | ramp amount in over 0.3 s |
| Curiosity tag (s01) | `name_tag(..., color="curiosity")` | §1 |

Previews: `fx_ep2_misc.png` (shutter sparks, bonk, tear, zzz).

---------------------------------------------------------------------------

## Scene recipes (DIRECTION beats)

| beat | call(s) |
|---|---|
| s01/s02/s04/s08 intro tags | `name_tag(...)` (screen space, after camera) |
| s02 scurry + whip pan to the door | `motion_lines` behind the thing; `dx, inc = whip_pan_offset(t, t0)`, draw scene A/B shifted by dx, then `whip_pan(ctx, t, t0)` |
| s03 panic | `sweat_fly` (new seed per flick), `heat_squiggles(amount=blush)` |
| s04 gulp | `emote(ctx, "gulp", ...)` |
| s05 notes leaking | `music_notes` at the cup |
| s05 freeze | `flash(ctx, t, tf)` + `shock_lines(ctx, x, y, 1.0, t, tf, 1.0, rx, ry)` |
| s05 taps / ceiling / land | `tap_marks`; `impact_star(word="BONK!")` + `plaster_dust` at the ceiling line; `dust_puff` on landing; `dizzy_stars(layer="back"/"front")` |
| s06 teleport | `smear(ctx, floor_x, floor_y, desk_x, desk_y, t, t_teleport)` |
| s08 tablet | `tablet_screen(..., t_on=cue)` in an insert |
| s09 photo / gulp / sweat | `hologram_photo(..., t_on=info.cue("s09_l04")+0.4)`; `emote("sweatdrop")`, `emote("gulp")` |
| s10 search | `search_screen` (+ `type_times` for SFX) |
| s11 lab / label / alarm | `lab_screen(t_on=cue)`, `label_card(...)`, `alarm_wash(ctx, t, ramp)`, `emote("exclaim")` |
| s11 powers / impact | `time_slow(ctx, t, k)` + `power_aura(outline_fn=...)` + `eye_glint`; `flash` then `black` |
| s12 wake / sense / bond | `eyelid_wipe(ctx, t, 0.0, 1.3)`; `ripple_rings(outline_fn=shadow_path)`; `heartbeat_sync(sync=ramp)` |
| s13 title | `end_card(ctx, t, info.cue("title"))` |

### Episode 2 recipes
| beat | call(s) |
|---|---|
| s01 perk | `name_tag(ctx, "CURIOSITY", "specimen 00", t, t_in, t_out, color="curiosity")` |
| s01 control room monitor | `monitor_feed(ctx, mx, my, mw, mh, t, draw_feed)` (label "SHAFT CAM 03") |
| s01 click → dark | `pw = lights_out(ctx, t, info.cue("click") + 0.3, 6)` (screen space, after the camera; pass `pw` to the set's pods), `lights_out_times(...)` for the chunk SFX; then `eyes_in_dark(..., "curiosity")` and `eyes_in_dark(..., "tired")` |
| s02 eyes / nudge | `eyes_in_dark` (Curiosity's pair moves as it climbs; `amount` for its glow) |
| s02 ping / look / walk | `sense_reveal(ctx, t, pings, draw_lit, draw_dark, key=..., rect=...)` with pings from his head (follow the head: each ping keeps its own origin); characters on top; `sense_at` to light Curiosity's nod, or `live=` |
| s02 bonk | `bonk_star(...)` + `dizzy_stars` |
| s03 beams | `flashlight(...)` x2 over the dark lower level (same key); quiet pings `(t0, x, y, 0.45)`; `flicker=0.6` for the scared guard |
| s04 hurt | `tear_drop(...)` or the creature's `wet` eyes; bandage glow = `power_aura` |
| s06 tempt | `daydream(ctx, x, y, 1.0, t, t0, t1, dream_bed, tail=...)` |
| s07 shutters | `sparks(...)` per slamming shutter (new seed each); `props.shards` for the case; `alarm_wash` |
| s08 phone | `phone_screen(...)` insert + `phone_times(...)` for buzz/keys/whoosh SFX |
| s08 title | `end_card(ctx, t, info.cue("title"), subtitle="Episode 2: Lights Out")` |

## Test scripts
* `python3 preview/fx_test.py [phone tags marks emotes story full screens end]` renders the
  boards `preview/fx_*.png` over grey and busy backdrops.
* `python3 preview/fx_perf.py` prints the per-effect cost table at 720x1280.
* `python3 preview/fx_check.py` checks the timing contract (nothing before start or after
  end, deterministic, nothing at amount 0).
* Episode 2:
  * `python3 preview/fx_ep2_test.py [sense full shaft s02 flash lights eyes ui misc perf | all]`
    renders the boards `preview/fx_ep2_*.png`. Frames are rendered at 720x1280 on its own
    test catwalk and lower-level sets; `shaft` uses `sets.shaft` and is guarded.
  * `python3 preview/fx_ep2_test.py perf` prints the Ep2 cost table. It is robust: min of 3
    runs per frame.
  * `python3 preview/fx_ep2_check.py` checks the Ep2 contract:
    * timed effects draw nothing outside their window;
    * nothing at amount/power 0;
    * the sense draws only darkness when no ping is active;
    * determinism (also across a cleared bake cache);
    * the lights-out flicker is not a strobe.
  * `preview/fx_check.py` / `fx_perf.py` (copied from Ep1) still pass with 0 failures and 0
    over budget, so all Episode 1 effects are unchanged.
