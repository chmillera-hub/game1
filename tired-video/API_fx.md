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
  `end_card`, and also `name_tag` (it slides off the frame edge).
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
"imp": "#f7b33a" (gold), "boss": "#5fdcc2" (mint)}`. Aliases are accepted:
`tiredness, embarrassment, impulsivity, the boss, periwinkle, pink, gold, mint, teal`.
Any `#rrggbb` or `PAL` key also works. The boss mint is deliberately *not* the special
`power` teal.

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
* Script cues: s01 `name_tag(ctx,"TIREDNESS","just wants to play his game",t,0.3,3.0)`;
  s02 `"EMBARRASSMENT","junior lab scientist", color="embar"`;
  s04 `"IMPULSIVITY","a tripwire that never goes off", color="imp"`;
  s08 `"THE BOSS","HushCorp", color="boss"`.
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

### `end_card(ctx, t, t0, title="TIREDNESS", cx=468, baseline=730, size=168, t_tbc=None, tbc="to be continued…", t_out=None)`
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
* Previews: `preview/fx_end.png` (timeline over teal), `fx_end_detail.png` (teal vs grey).

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

## Test scripts
* `python3 preview/fx_test.py [phone tags marks emotes story full screens end]` renders the
  boards `preview/fx_*.png` over grey and busy backdrops.
* `python3 preview/fx_perf.py` prints the per-effect cost table at 720x1280.
* `python3 preview/fx_check.py` checks the timing contract (nothing before start or after
  end, deterministic, nothing at amount 0).
