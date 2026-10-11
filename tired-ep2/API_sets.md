# API — `engine/sets.py` (locations) and `engine/props.py` (props)

Flat-colour, plum-ink (`PAL["ink"]`) backgrounds and props for TIREDNESS.
Everything is procedural and deterministic. Static parts are cached with
`core.cached` (through `sets.static_layer` / `sets.cached_or_live` /
`sets.layer_blit` / `sets.sprite`); only small sparse details animate (game
screen, drips, motes, shimmer, beacons, bird, leaf, pod pulse, bubbles).

**Episode 2 sets** (sections 13-17): `catwalk` (side-on shaft catwalk with
nameplated pods), `shaft_lower`, `service_tunnel`, `control_room`, `pod_pov`
(frame-0 thumbnail), plus `shaft` (power / cascade / shutters / plates) and
`bedroom` (`light="dawn"`, nightstand + phone, stageable bed) upgrades. All
Episode 1 calls and looks are unchanged (pixel-checked).

```python
from engine import core, sets, props

M = sets.BEDROOM_MARKS
with core.camera(ctx, *M["cam"]["s01_open"]):          # (cx, cy, zoom)
    sets.bedroom(ctx, t, layer="bg", chair_spin=0.0)
    sx, sy = M["chair_seat"]                            # place people with MARKS
    human.draw_tired(ctx, sx, sy, s=0.75, ...)          # (other agent's rig)
    sets.bedroom(ctx, t, layer="fg", parts=("desk",))
```

## 0. Conventions (read once)

* **World coordinates.** Each set has a nominal world (`<SET>_MARKS["size"]`)
  and most interiors draw an *extended* margin (ceiling, side walls, floor
  continue ~500-800 px beyond the edges) plus flat overscan beyond that, so
  framings down to zoom ~0.5 never show void.
* **Zoom vs character scale.** At zoom 1 the frame shows 1080 x 1920 world
  px. On-screen scale = character `s` x zoom. Every set lists its intended
  `char_scale` (a standing adult at that `s` matches doors/furniture).
* **Stage depth is flat.** Feet lines (`stand_y`, `*_feet`) are a little in
  front of the furniture; people are not perspective-scaled (except in the
  corridor: use `corridor_scale`).
* **Layers.** `layer="bg"` draws everything behind people (each set is a
  complete picture with bg alone). `layer="fg"` draws only what must
  overlap people; choose pieces with `parts=(...)` (default parts listed per
  set). Sets with a doorway also have a **"back"** layer (what is seen
  through the open door) and a **"room"/"hall"/"house"** layer (bg minus
  back) so a person can stand *behind* the wall: `back -> person -> room
  -> fg`.
* **Every state kwarg has a default**; `fn(ctx)` alone draws the default set.
* **Safe zones**: suggested `cam` framings in each `MARKS["cam"]` keep faces
  and key props inside x 60..930 / y 120..1330 of the frame (checked with
  stand-ins in the preview boards).
* **Teal glow (`power`)** is used only in the shaft pods, `containment_pod`,
  the sewer side-tunnel glow (`teal_glow_end`) and the shaft tunnel mouth.
  HushCorp branding uses `hush` / `hush_dk` (not glowing).
* **Light, darkness and cascades (Episode 2).** Dark sets take `power` 0..1
  (room lights) and, where it matters, `power_sections` (one value per
  horizontal light band, TOP first; `<SET>_MARKS["sections"]` /
  `["n_sections"]`) plus `pod_glow` 0..1 (None = follows power: full when lit,
  `sets.EMBER` = 0.14 faint embers when dark). Darkness is the same everywhere:
  a `sets.DARK` (#03070b) wash at `sets.DARK_A` = 0.86 ("almost black but
  readable"), with emissive bits (pod embers, LEDs, grate glow, exit sign)
  drawn on top. `lit=True` forces the lit surfaces, `lit=False` the dark
  version: fx draws `lit=True` inside a sense ring / flashlight cone (clip to
  it, call the set again) over the dark set. **Cache-friendly:** a steady
  state (every section fully on or off) is ONE precomposed bake; only the
  ~0.16 s transition frames mix cached layers by opacity.
  * Hook-up with fx (they bake `draw_lit` once per key):
    `fx.sense_reveal(ctx, t, pings, draw_lit=lambda c: sets.catwalk(c, 0, lit=True),
    draw_dark=lambda c: sets.catwalk(c, 0, lit=False), key="cw_lit", ...)` and
    `fx.flashlight(ctx, x, y, ang, L, spread, t, draw_lit=lambda c:
    sets.shaft_lower(c, 0, lit=True), key="sl_lit")` over `sets.shaft_lower(ctx,
    t)` (dark). Inside the camera block pass a world-space `rect` around the
    FRAMING (the visible region), not the whole drawable: fx bakes that rect
    once (a whole-drawable rect took ~3.5 s; then 3.6 ms/frame, tested:
    `preview/sets_ep2_lower_fxcone.png`).
  * `sets.shaft_power_at(section, t, t0, step=0.55, dur=0.16)` -> power of a
    section in a lights-out cascade starting at t0 (section k cuts out at
    t0 + k*step with one heavy "chunk": dip, catch, off; no strobing);
    `shaft_power_sections(t, t0, n, step, dur)` -> the list for
    `power_sections=`; `shaft_power_times(t0, n, step)` -> the cut-out times
    (for the "chunk" SFX).
* **Characters in the set's light: `layer="shade"` + `sets.shaded`.**
  ```python
  sets.catwalk(ctx, t, power=p)                       # bg
  with sets.shaded(ctx, sets.catwalk, t, layer="shade", power=p):
      human.draw_tired(ctx, ...); creatures.draw_specimen(ctx, ...)
  sets.catwalk(ctx, t, layer="fg", power=p)
  ```
  Everything drawn in the block goes into a group and the set's "shade"
  layer (darkness per section, teal pod / cool monitor / warm lamp / dawn
  light) is composited ATOP it, so characters darken with the room without
  darkening the background twice. Draw glowing eyes / auras AFTER the block
  so they stay bright. ~1-2 ms (one frame-sized group).
* **Caching notes.** Cache keys include state (e.g. `("house", broken)`,
  `("sewer", variant, hole)`). Opaque layers are tiled automatically when a
  bitmap would exceed 12 MP (only visible tiles are rendered/blitted, no
  seams). Translucent overlays fall back to live drawing in extreme
  close-ups (`cached_or_live`). A continuous zoom re-renders the static
  layer every 1/8 octave (core's quantisation): a slow push-in costs
  ~15 ms/frame on average instead of ~5.

Helpers exported by `sets`:

| name | what |
|---|---|
| `static_layer(ctx, key, x0, y0, w, h, fn, max_mp=None, tile_px=2040)` | `core.cached` with auto-tiling + visibility culling (opaque layers) |
| `cached_or_live(ctx, key, x0, y0, w, h, fn)` | `core.cached` for small translucent layers; draws live when huge |
| `layer_blit(ctx, key, x0, y0, w, h, fn, alpha=1, clip=None, max_mp=None, tile_px=2040)` | big cached layer, opaque OR translucent, with opacity and an optional clip rect; tiles are blitted with pixel-aligned clips (no seams) |
| `blit(ctx, key, x0, y0, w, h, fn, alpha=1, pad=4, clip=None)` | `core.cached` with opacity (same LRU); the key ignores x0/y0, so a drawing around a translated origin is a reusable sprite |
| `sprite(ctx, key, x0, y0, w, h, fn, alpha=1, max_mp=4)` | small cached drawing in its OWN 64-entry LRU (animated live pieces cache per state without evicting set tiles) |
| `dimmed(ctx, bbox, dim, fn)` / `dim_sprite(ctx, key, bbox, dim, fn)` | draw a piece darkened ATOP by `dim` (live / sprite-cached per (key, dim)) |
| `shaded(ctx, set_fn, *args, **kw)` | context manager: characters lit by a set's `layer="shade"` (see above) |
| `shaft_power_at`, `shaft_power_sections`, `shaft_power_times` | lights-out cascade helpers (see above) |
| `tunnel_depth(k, lane=0)` | `(x, y_feet, scale)` walking into the service tunnel's dark side tunnel |
| `DARK`, `DARK_A`, `EMBER` | darkness colour / strength, default ember glow |
| `view_rect(ctx)` | visible region `(x0, y0, x1, y1)` in user coords |
| `door_quad(hinge_x, top, bottom, width, opening, vp, D, toward, hinge_left)` | 4 points of a swinging door in perspective |
| `wonky_rect(...)` | slightly hand-made quad |
| `bedroom_monitor_space(ctx, W=640, H=400)` | context manager: draw a flat 640x400 screen onto the bedroom monitor |
| `corridor_scale(z, lane=0)` | `(x, y_feet, s)` for a runner at depth z |
| `C` | the set palette (dict of hex colours) |

---------------------------------------------------------------------------

## 1. `bedroom(ctx, t=0, layer="bg", **state)` — s01, s05–s07, s10

World **2400 x 1920**, people at **s = 0.75**. Sage striped wallpaper, honey
floor, string lights, glow-in-the-dark ceiling stars, warm afternoon sun
patch (right of the window, in the s01 framing) + a second one on the
closet, warm lamp glow, monitor glow. Left to right: door to the hallway
(opens inward), sliding closet, unmade bed (headboard left) with the laundry
heap in front, window onto the sunny street, picture frame, gaming desk
(speaker, RGB keyboard, 3/4-turned monitor, chips, cans, lamp, PC tower) and
the gaming chair. Shelf with books, plant and a vinyl figurine above the desk.

States

| kwarg | default | meaning |
|---|---|---|
| `door_open` | 0 | 0..1, door swings INTO the room (toward the viewer), hinge on the left |
| `closet_open` | 0 | 0..1, front sliding panel moves right, revealing clothes/boxes on the left half |
| `laundry` | 0 | 0..1, top bundle of the heap lifts ~270 px (sleeves dangle); jeans stay on the floor |
| `laundry_scattered` | False | clothes scattered around the heap spot instead |
| `chair_spin` | 0 | radians; 0 = facing right (toward the desk), pi/2 = facing camera, -pi/2 = back to camera |
| `chair_empty` | False | True: chair drawn complete (incl. near armrest) in bg. False: the armrest post goes to fg part "chair" so a sitter is *in* the chair |
| `chair_dx` | 0 | nudge the chair horizontally |
| `shake` | 0 | 0..1: posters tilt, figurine wobbles, hanging lamp swings, dust (<= 10 motes) sifts from the lamp |
| `frame_fallen` | False | False on the wall; True face-down on the floor (pale patch + nail remain); a float 0..1 animates the fall |
| `screen_fn` | None | `screen_fn(ctx, t)` draws into the monitor in a 640x400 space; default `props.monitor_game_screen` |
| `screen_on` | True | False = dark monitor |
| `game_speed` | 1 | scroll speed of the default game |
| `light_on` | True | hanging-lamp glow |
| `parts` | ("door","desk","chair") | fg pieces: "door" = casing (+ panel when open), "desk" = front-left leg (knees of the sitter go behind it), "chair" = armrest post |
| **`light`** | "day" | **"dawn"** (Episode 2 s08): soft gold-pink sunrise in the window (low sun, pink clouds, backlit houses), a slightly dim cool room, hanging lamp / desk lamp / string lights off, warm sun beams across the bed and floor. The grade is baked into every cached piece |
| `sunrise` | 0 | 0..1 grows the dawn light (final hold); quantised to 0.1 (one re-bake per step) |
| `nightstand` | None | None = only at dawn. Nightstand by the head of the bed (in front of the closet's right edge) with a little lamp (off), an alarm clock "6:02" and the phone docked upright, screen to camera |
| `phone_fn` | None | `phone_fn(ctx, x, y, w, h, t)` draws the docked phone's screen (props.phone screen space, 112 x 220 local units; e.g. `props.phone_chat_screen([...])`); default lock screen "6:02" |
| `phone_on` / `phone_buzz` | True / 0 | screen on; 0..1 buzz shiver + buzz marks |
| `bed_squash` | 0 | 0..1 dips the mattress/blanket ~22 px (animate with a bounce for the flop) |
| `frame_fallen` | **True** | (default unchanged: the picture frame stays fallen) |

Layers: `"bg"`, `"back"` (hallway through the doorway), `"room"` (bg without
back), `"fg"`, `"shade"` (dawn light on characters, with `sets.shaded`).

`BEDROOM_MARKS` (world px)

| key | value | notes |
|---|---|---|
| ceiling_y / floor_y / stand_y | 300 / 1330 / 1520 | back-wall top, wall base, feet line in the room |
| door | (110, 505, 400, 825) | doorway x, top, w, h; `door_hinge_x` 110, `door_knob` (468, 960) |
| doorway_feet / hall_feet | (312, 1334) / (312, 1300) | someone in the doorway / in the hallway behind it |
| closet / closet_open_rect | (590, 560, 410, 770) / left half | `closet_rummage_feet` (700, 1530) |
| bed | (1030, 1120, 560, 340) | `under_bed_head` (1300, 1415), `under_bed_feet` (1300, 1560) |
| laundry / laundry_hands | (1000, 1585) / (1000, 1450) | heap base / where hands grab to lift |
| window | (1100, 470, 400, 410) | |
| picture_nail / picture_floor | (1668, 752) / (1560, 1560) | |
| shelf_figurine / ceiling_light | (2020, 642) / (1440, 268) | |
| desk / desk_top_y | (1700, 1100, 640, 350) / 1104 | `keyboard` (1878, 1104), `desk_critter` + `sweater_spot` (1985, 1100) |
| monitor_quad / monitor_rect | 4 corners / (1832, 790, 248, 228) | draw via `bedroom_monitor_space(ctx)` (640 x 400) |
| chair_floor / chair_seat | (1625, 1590) / (1625, 1392) | hip point of the sitter; `seated_faces` "right" |
| behind_chair_feet / desk_lean_feet | (1460, 1560) / (1880, 1520) | |
| tug_left_feet / tug_right_feet | (560, 1540) / (1080, 1540) | s07 tug-of-war spots |
| cam | s01_open (1735, 980, 1.12), desk_medium (1760, 1010, 1.7), s05_wide (1180, 1010, 0.56), door_wide (520, 1000, 1.0), closet_bed (980, 1050, 1.0), tug (760, 1030, 0.85) | |
| **bed_top_y** | 1165 | top of the blanket: a body lying on the bed rests on this line (bed x 1070..1590; feet may hang past the footboard post at 1560) |
| **pillow** / **lie_head** | (1165, 1150) / (1170, 1128) | pillow centre / head of a face-down sleeper (face turned to camera) |
| **lie_hips** / **lie_feet** | (1390, 1168) / (1600, 1176) | |
| **bed_entry_feet** | (1460, 1530) | where he stands before the flop |
| **nightstand** / **nightstand_top_y** | (945, 1360) / 1150 | floor centre / top surface |
| **phone** / **phone_screen** | (985, 1112) / (961, 1066, 47, 92) | docked phone centre (props.phone s=0.42) / its screen rect in world px |
| cam (dawn) | dawn_wide (1180, 1040, 0.62), flop (1300, 1080, 1.25), pillow_close (1105, 1100, 2.8) (his face on the pillow + the phone), phone (985, 1110, 5.0) | |

Notes: the s05 "door on the left, him at the desk on the right" shot needs
the whole room: use `cam["s05_wide"]` (zoom 0.56, people ~0.42 on screen;
ceiling/floor continue). For the s05 ceiling bonk use `ceiling_y` (300) as
the bump line.

## 2a. `bedroom_window_exterior(ctx, t=0, layer="bg", light=1.0)` — s01 "window"

World **1080 x 1920**, a medium shot of him leaning to the glass:
character **s = 1.45** with feet at `lean_feet` (540, 2100) puts the face at
~(540, 800). `"bg"` = dim room behind the glass + the siding wall;
`"fg"` = the same wall with the glass cut out, frame, low meeting rail
(y 1020, below the face), sill, flower box and glass reflection streaks.
Draw `fg` over him: only what is behind the glass shows. `light` < 1 dims
the interior. MARKS: `glass` (190, 430, 700, 730), `sill_y` 1180,
`meeting_rail_y` 1020, cam default (540, 960, 1) / close (540, 800, 1.35).

## 2b. `street_view(ctx, t=0, layer="bg", frame=True, leaf=True, bird=True)` — s01 "nothing", s07 run-out

World **1080 x 1920**, his POV from the upstairs window: sky + sun, three
houses across the street, big tree, telephone pole, parked orange car, his
picket fence and lawn. `frame=True` wraps it in his interior window trim,
curtains and sill (no central mullion). Animated: a leaf drifting from the
tree (7 s loop) and a bird hopping/pecking on the lawn (3.2 s ping-pong).
MARKS: lawn run `lawn_feet_y` 1450 (x 120..960) at **s = 0.3**,
`sidewalk_y` 1272, `street_y` 1205, `bird` (660, 1420), `sill_y` 1530.

## 3. `house_exterior(ctx, t=0, layer="bg", **state)` — s02, s03, s08, s10

World **2600 x 2300** (street included), people at **s = 0.45**. Yellow
two-storey house with a front gable, blue roof, chimney, red front door with
a gap at the bottom, porch (roof, posts, rails, 2 steps), three ground-floor
windows over foundation hedges, his upstairs window (shutters + flower box,
monitor glow inside), picket fence with a gate, stone path, lawn with
flowers, mailbox, driveway with two trash cans, streetlight, sidewalk and
street. The **left end (x 0..640) is the shaded side wall** (siding, gable,
gas meter, downspout, hose reel) for the s02 opening.

| kwarg | default | meaning |
|---|---|---|
| `broken` | None | index 0..2 of the smashed ground-floor window (static jagged hole) |
| `door_open` | 0 | front door opens inward (away from us); hall glow visible ("back" layer) |
| `damage` | 0 | 0..1: cans knocked over + spilled, streetlight shattered & leaning (sparks), debris, lawn divots |
| `dent` | 0 | 0..1 body-shaped splat dent in the side wall with cracks + popped board |
| `porch_light` | False | warm porch lamp glow |
| `rock` | True | the lawn rock at `MARKS["rock"]` (False once picked up; `props.rock(..., s=0.6)` matches) |
| `parts` | ("fence","door") | fg: "fence" (people on the lawn are behind it), "door" (casing + panel), "hedge" (foundation hedges) |

Layers: `"bg"`, `"back"` (hall behind the door), `"house"`, `"fg"`.

`HOUSE_MARKS`: ground_y 1500, lawn_feet_y 1600, windows
[(760,1020,230,250), (1100,1020,230,250), (1870,1020,230,250)] (all within
1340 px), `window_push` feet spots [(875,1580), (1215,1580), (1985,1580)],
window_sill_y 1270, door (1480, 990, 220, 440), `door_gap` (1486, 1424,
208, 6) (the thing scurries under it), porch_feet_y 1452, porch_x
(1400, 1780), doormat (1590, 1458), doorway_feet (1590, 1432), steps
[(1590,1508), (1590,1538)], path_feet (1590, 1660), gate (1590, 1800),
fence_y 1800, sidewalk_y 1840, street_y 2150 (van wheels), van_spots
[(860,2150), (1980,2150)] with van_scale 0.45, boss_feet (1420, 2210),
bedroom_window (1085, 560, 260, 300), side_wall (0, 440, 640, 1060), dent
(330, 1200), side_feet (330, 1560), rock (1880, 1690), trash_cans
[(2300,1790), (2440,1796)], streetlight (2520, 1850), hedge_trip (1210,
1520). cam: wide (1300, 1150, 0.62), s02_side (380, 1150, 1.25),
s03_windows (1430, 1240, 1.15), win1/win2/win3 (875|1215|1985, 1250, 1.6),
porch (1590, 1240, 2.3), s08_vans (1420, 1640, 0.9).

## 4. `living_room(ctx, t=0, layer="bg", drawer_open=0, broken=True, plates=True, plates_lift=0, parts=None)` — s04

World **2800 x 1920**, people at **s = 0.75**. Periwinkle damask wallpaper
over cream wainscoting, warm floor lamp, slightly dim warm vignette (static).
Left to right: broken front window (glass teeth, yard outside, sun patch and
14 glass bits on the floor), Impulsivity's giant round pet bed (bone, ball,
"IMP" bowl), couch + coffee table on a red rug (plates), kitchen counter with
upper cabinets, tiled backsplash, kettle and fruit (`drawer_open` = top
middle drawer slides out with utensils), dining table you can see under
(+2 chairs, vase), staircase rising to the right to a landing wall.

`plates=False` lets a scene draw its own `props.plates_stack` at
`MARKS["plates"]` (s=0.62). fg parts: "table" (table top, front legs, near
chair), "stairs" (banister + balusters). Default parts: both.

`LIVING_MARKS`: ceiling_y 300, floor_y 1330, stand_y 1520, window (90, 470,
360, 470), heap_feet (300, 1500), imp_sit (640, 1560), pet_bed (700,
1560), couch (960, 990, 520, 460), coffee_table_top (1220, 1408), plates
(1220, 1404), counter (1560, 1050, 420, 390), drawer (1712, 1086, 128, 66),
drawer_hands (1776, 1130), counter_feet (1776, 1520), table (2000, 1265,
360, 335), under_table (2180, 1450), table_crouch_feet (2080, 1600),
stairs_bottom (2250, 1330), stairs_top (2754, 601), **landing_wall
(2560, 160, 700, 441)** = free wall for the sliding tail shadow,
landing_floor_y 601. cam: low_heap (420, 1250, 1.5), reveal_up (560, 1000,
1.15), tiptoe_wide (1250, 1060, 0.62), plates (1220, 1180, 1.5), drawer
(1776, 1100, 1.5), table (2150, 1250, 1.3), stairs (2470, 820, 1.1).

## 5. `hallway_upstairs(ctx, t=0, layer="bg", door_open=0, burst=0, parts=None)` — s05

World **1500 x 1920**, people at **s = 0.75**. Warm-dim landing (lights off)
with the wallpaper/wainscot of downstairs, a framed photo, sconce, hall
table + plant, runner rug; stairs coming up from the lower left (white
stringer, wood treads, carpet runner); the bedroom door on the right with a
"GAMING zZz" knob sign and a **glowing light gap** under it (+ warm floor
glow). The door opens away from us (hinge on the RIGHT) into the bright
bedroom ("back" layer). `burst` 0..1 = progress of a slam-open: door
rattles, impact lines and a dust puff fade out.

Layers: `"bg"`, `"back"`, `"hall"`, `"fg"` (parts "railing" = banister in
front of the stairs (default), "door" = casing + panel for someone in the
doorway).

`HALL_MARKS`: floor_y 1330, stand_y 1480, door (860, 505, 400, 825),
door_hinge_x 1260, light_gap (868, 1314, 384, 16), tail_slip (1060, 1324),
doorway_feet (1060, 1334), stair_top (700, 1330), **steps** = tread centres
from the top `[(760,1330), (645,1400), (535,1470), (425,1540), (315,1610),
(205,1680), (95,1750), (-15,1820), ...]` (rise 70, run 110), stair_slope
0.567 rad (stairs descend to the left), landing_feet (790, 1480). cam:
crawl (640, 1320, 1.0), door (1060, 1050, 1.15), door_close (1060, 1150, 1.7).

## 6. `office(ctx, t=0, layer="bg", parts=None)` — s09

World **1400 x 1920**, people at **s = 0.75**, staged side-on. Floor-to-
ceiling glass with a cool city skyline, a white wall with the HushCorp logo
+ wordmark behind the Boss, a huge minimalist white desk (pedestal right,
thin steel leg left), the Boss's very tall white chair (she faces LEFT), the
comically LOW guest chair (Emb faces RIGHT), grey carpet. fg part "desk"
(default) = the whole desk, drawn over the Boss's legs; draw sliding
devices after it on `desk_top_y`.

`OFFICE_MARKS`: floor_y 1300, stand_y 1500, desk (500, 1140, 760, 360),
desk_top_y 1140, desk_slide ((1110, 1140) -> (600, 1140)), boss_seat (1175,
1225), boss_chair (1190, 1500), guest_seat (330, 1452), guest_chair (330,
1500), sweat_floor (372, 1508), **glass_rect (110, 420, 560, 470)** for the
photo/hologram, logo (1200, 455). cam: wide (700, 1060, 0.95), two_shot
(740, 1120, 1.0), emb_low (420, 1230, 1.9), boss (1130, 1000, 1.9),
desk_slide (850, 1150, 1.6).

## 7. `lobby(ctx, t=0, layer="bg", turnstile_open=0, turnstile_light="red", parts=None)` — s11

World **1800 x 1920**, people at **s = 0.75**. Glass entrance (left), a
backlit logo wall with the wordmark and tagline "We keep secrets so you
don't have to.", white curved reception counter (teal stripe, logo,
"RECEPTION", bell, tablet), tall potted plant, two turnstile lanes (posts
with card readers and a lamp: `turnstile_light` "red" | "green" | None;
glass flaps fold into the posts with `turnstile_open`), guard post (monitor,
coffee) under a SECURITY sign, polished floor with static reflections.

fg parts: "counter" (default; the receptionist sits behind it),
"turnstiles", "guard". `LOBBY_MARKS`: floor_y 1300, stand_y 1500, counter
(330, 1070, 650, 430), counter_top_y 1070, recep_seat (760, 1260) (hips,
faces LEFT), visitor_feet (250, 1500) (faces RIGHT), turnstiles [(1090,
1500), (1270, 1500), (1450, 1500)], lanes [(1180, 1500), (1360, 1500)],
guard_feet (1640, 1500), plant (1010, 1500), logo (650, 470). cam: wide
(900, 1060, 0.85), counter_two (520, 1080, 1.35), recep_close (720, 1000,
2.0), turnstiles (1330, 1150, 1.2).

## 8. `lab(ctx, t=0, layer="bg", alarm=0, button_pressed=0, critters_fn=None, screen_fn=None, door_open=0, parts=None)` — s11

World **2400 x 1920**, people at **s = 0.75**. Three specimen tanks (green
liquid, vague dim shapes, SPEC-03..05 labels, <= 8 slow bubbles in total),
beaker shelf, "AUTHORIZED STAFF ONLY" sign, terrarium on a bench (wheel,
water dish, bedding) with the **"CARRIER / BITE TRANSFERS TRAITS"** placard,
a big wall screen, the red-button console (`props.red_button_console`,
s=0.75, with a "DO NOT LEAN ON CONSOLE" label) and a sliding "LAB 7" door.

* `critters_fn(ctx, x, y, w, h, t)` draws inside `MARKS["terrarium"]`
  (clipped; glass + lid drawn over it). Default: 3 simple violet critters.
* `screen_fn(ctx, x, y, w, h, t)` draws the wall-screen UI into
  `MARKS["screen"]` (clipped). Default: dark grid + dim logo.
* `alarm` 0..1: red wash pulsing at 0.8 Hz between ~55% and 100% of its
  strength (never strobing) + 3 rotating beacon beams. fg (any parts) adds a
  faint wash over the characters too.
* fg parts: "console" (draw it over a hand that is behind it).

`LAB_MARKS`: floor_y 1300, stand_y 1500, tanks [(220|480|740, 560, 200,
700)], terrarium (930, 840, 380, 250), label (1120, 1146), terrarium_feet
(1000, 1500), **screen (1380, 360, 640, 440)**, console (1700, 1500),
**button (1812.5, 1147.5)**, console_lean_feet (1560, 1500), door (2090,
520, 280, 780), door_feet (2230, 1500), beacons. cam: wide (1200, 1060,
0.62), tanks (480, 1000, 1.1), terrarium (1110, 1000, 1.6), label_close
(1120, 1080, 2.6), screen (1700, 800, 1.0), console (1700, 1180, 1.5), door
(2100, 1050, 1.1).

## 9. `corridor(ctx, t=0, layer="bg", alarm=0, window_broken=0)` + `corridor_scale(z, lane=0)` — s11 chase

World **1080 x 1920**, fixed camera, one-point perspective (VP (540, 820)):
white walls with doors, teal accent stripe, ceiling light panels, tiled
floor, warm dusk light spilling from the tall end window (dusk sky + city
inside it). `window_broken`: 0 intact, (0, 1) spider cracks growing, 1
shattered (only jagged teeth). `alarm` like the lab.

`corridor_scale(z, lane)` -> `(x, y_feet, s)`: z = 0 near (feet y 1760,
s 1.03) .. z = 1 at the window (feet y 1080, s 0.28); lane -1..+1 = left..right
wall (runners ~ +-0.4). Depth is linear in real distance (the scale falls as
1/(1 + 2.6 z)). Draw runners far-to-near. MARKS: window (420, 590, 240, 470),
window_sill_y 1060, end_wall (380, 560, 320, 520).

## 10a. `tower_exterior(ctx, t=0, layer="bg")` — s11 fall

World **1080 x 1920**. Static dusk gradient (violet -> magenta -> orange),
11 stars, pink cloud streaks, a lit city far below, and the glass tower face
(right side, mullions converging downward, sky reflection) with the broken
window showing the red-lit corridor. `"fg"` = jagged glass teeth + hole frame
(someone leaving the hole is drawn between bg and fg). Use
`props.shards(..., x, y)` from `MARKS["shard_origin"]`. MARKS: hole (600,
560, 260, 360), hole_center (730, 740), facade_x 560 (open sky left of it),
fall_from (700, 760), fall_path [(700,760), (480,900), (360,1150)],
char_scale 0.45. cam default / hole (700, 780, 1.6).

## 10b. `city_fall(ctx, t=0, layer="bg", approach=0)` — s11 impact

World **1080 x 1920**, looking straight DOWN at a dusk city grid (rooftops in
violet/slate/brick with AC boxes and water tanks, two parks, street lights
and car lights as dots). `approach` 0..1 scales the fixed plan exponentially
(0.35 -> 4.2) about the landing manhole at `MARKS["centre"]` (540, 1000);
taller buildings' roofs grow faster (pseudo-3D side faces). Drawn live with
culling and batched fills; not cached (the scale changes every frame).

## 11a. `sewer(ctx, t=0, layer="bg", hole=None, light=1, teal_glow_end=0, variant=0, drips=True, motes=True)` — s12, s13

World **2600 x 1920**, people at **s = 0.75**. Teal-green brick tunnel seen
side-on: vault band with arch ribs, pipes (flanges, red valve wheel,
outflows), moss, a walkway over the water channel, a dark arched side
tunnel mouth, a chalk X, static dark ends (never black).

* `hole` (default True for variant 0): broken hole in the vault (sky, a
  streetlight pole), a soft daylight shaft with <= 10 drifting dust motes,
  the shallow crater on the walkway with rubble, light on the water.
* Animated: <= 9 shimmer lines on the water, 2 drips per variant (falling +
  ripple), motes.
* `light` 0..1: overall light level (dark-teal overlay). `layer="fg"`
  optionally applies the same overlay over the characters.
* `teal_glow_end` 0..1: the side tunnel mouth glows `power` teal (s13).
* `variant` 0..3: montage junctions ("every junction looks the same"):
  pipe heights, valve, rib phase, chalk mark, drips and tunnel mouth move.

`SEWER_MARKS`: walk_feet_y 1282 (x 80..2520), wall_lean_x 640, hole
(1300, 90), crater (1300, 1276), lie_hips (1300, 1262), water_y 1385,
**side_tunnel[variant]** = (x, top, w, h): 0 (2150, 690, 300, 560), 1
(1700, ...), 2 (900, ...), 3 (2050, ...); dark_ends (600, 2000),
eyes_in_dark (300, 980) (good spot for teal slits). cam: wide (1300, 1000,
0.75), crater (1300, 1050, 1.5), walk (900, 1000, 1.0), side_tunnel (2250,
1000, 1.0).

## 11b. `sewer_hole_pov(ctx, t=0, layer="bg", drip_t0=0.4)` — s12 "eyesOpen"

World **1080 x 1920**: looking straight up the brick vault at the ragged
daylight hole (`SEWER_POV_MARKS["hole"]` (540, 760)), soft glow, dark rim.
From `drip_t0` a drop falls toward the camera (2.2 s loop). fx draws the
eyelid wipe/blur on top.

## 12. `shaft(ctx, t=0, layer="bg", sleeper_fn=None, sleeper_key=None, pulse=True, glow=1)` — s13

World **1080 x 3600**, drawable x **-700..1780** (so the camera can pull out
to zoom ~0.56). A true cylinder projection from a camera on the near
catwalk (eye level `horizon_y` 2350): ~400 glowing pods on 38 tiers ring the
wall (near pods big at the frame sides, far pods small), meridian ribs,
tier ledges, a giant logo + wordmark on the far wall, static light beams
from above and teal haze bands, a bridge below, the near catwalk with the
glowing side-tunnel mouth they come out of. People on the catwalk are tiny:
**s = 0.22**.

* `sleeper_fn(ctx, x, y, s, t, seed)` is called for each pod with w > 10
  px (clipped to the capsule; s = pod width / 300, so a ~300 px wide
  creature fills it). **Sleepers are baked into the cached layer at t=0**;
  pass `sleeper_key` (any hashable, e.g. "spec") so the cache knows the
  drawing. Without it pods show a dim curled silhouette.
* Per frame only a cheap shared **glow pulse** is drawn: 3 phase groups at
  0.25 Hz (one fill per group over visible pods). `glow` scales it,
  `pulse=False` disables it. Breathing of individual sleepers is not
  animated in the wide (use `props.containment_pod` with a live sleeper for
  close-ups).
* `"fg"` = the catwalk front railing (draw over the characters).
* **Episode 2 kwargs** (defaults = the Episode 1 look):
  `power`, `power_sections` (6 bands, top first: SHAFT_MARKS["sections"]
  = y <600, 600-1200, 1200-1800, 1800-2300, 2300-2900 (the near catwalk),
  >2900; use `shaft_power_sections(t, t0, n=6)`), `pod_glow` (glow left in
  dark bands; None = EMBER), `lit`, `labels` {pod index: "TEXT"}
  (nameplates on the bottom caps: near pods show "SPECIMEN nn", the tiny
  pod at the bottom centre SHAFT_MARKS["joy_pod"] reads "JOY"; baked, so
  changing labels re-renders), `shutters` 0..1 or a list per section
  (steel shutters slide down over every pod, amber lip; s07 lockdown on a
  monitor/window feed) with `shutters_except` (pod indices left open, e.g.
  `[SHAFT_MARKS["joy_pod"]]`), `layer="shade"`.
  SHAFT_MARKS also has `pods` (x, y, w, h per index), `pods_near` (indices
  with w > 90), `joy_pod`, `n_sections`, `sections`.

`SHAFT_MARKS`: horizon_y 2350, catwalk_feet_y 2400, catwalk_x (-520, 640),
tunnel_mouth (-380, 2400), tired_feet (300, 2400), creature_feet (390,
2400), logo (540, 1560). cam: arrive (60, 2250, 2.2), two_close (340, 2300,
3.2), reveal_wide (540, 1900, 0.56), title_wide (420, 2150, 0.75), look_up
(540, 1300, 0.9). For the eyes-wide close-up, frame the shaft at zoom 1.2-2
and draw Tiredness in screen space at s 2.4-3 (don't zoom the world to 10x).


## 13. `catwalk(ctx, t=0, layer="bg", **state)` — Episode 2 s01, s02

**The shaft catwalk side-on at human scale.** World **3600 x 1920** (drawable
x -800..4400, y -1400..2720, so zoom 0.56 wides work), people at **s = 0.75**.
The pod wall right behind the catwalk: a main tier of pods standing on the
deck, each with a readable brushed-steel nameplate on its base cap; two more
tiers above on ledges (railings, strip lights, "SPECIMEN 12.." plates)
fading into darkness; caged lamps under the ledges; a wall security camera
(red LED); the grated deck with the void below (distant pod glows, haze);
at the left end a short steel stair (6 steps) down to a lower walkway where
a LOW PIPE dips to face height (hazard bands, a MIND YOUR HEAD sign); a
LEVEL B2 / SHAFT A sign. Teal / dark-teal palette consistent with `shaft`.

Main tier, left to right (x = pod centre): **CURIOSITY** 1000 (SPECIMEN 00,
**empty**: door ajar on its right hinge, latch hanging open, drained lit
interior with drip lines and old claw scratches, **dusty plate**), **JOY**
1500 (a **tiny** pod), **COURAGE** 1990, **CALM** 2480, **WONDER** 2970,
**HOPE** 3460, **TRUST** 3950 (SPECIMEN 01..06).

| kwarg | default | meaning |
|---|---|---|
| `power` / `power_sections` | 1 / None | room lights; 4 sections top first: (-, -280) top tier, (-280, 600) upper tier, (600, 1380) main tier wall + lamps + camera, (1380, -) deck, stair, void. `shaft_power_sections(t, t0, n=4)` |
| `pod_glow` | None | 0..1 pod glow (None = follows power per section: 1 .. EMBER) |
| `lit` | None | True = lit surfaces (no lamps, no wash), False = dark (fx: draw lit=True inside a sense ring) |
| `labels` | None | `{index or default text: "TEXT" or ("TEXT", "SUB")}` or a callable `(i, (text, sub)) -> ...`; renames main-tier plates (baked) |
| `sleeper_fn` | None | `sleeper_fn(ctx, x, y, s, t, seed)` at each pod's floor **ground point** (s 0.75; tiny pod 0.45), e.g. `creatures.draw_specimen_pod_sleeper` |
| `sleeper_fns` | None | `{index or label: fn}` per pod, e.g. `{"JOY": lambda c,x,y,s,t,sd: CR.draw_specimen_pod_sleeper(c,x,y,s*1.6,t,sd,baby=True)}` |
| `sleeper_key` | None | hashable: pass it whenever you pass sleeper fns (sleepers are baked at t=0) |
| `door_open` | 0.12 | Curiosity's pod door (0 shut .. 1 wide open, swings toward the viewer) |
| `plate_dust` / `plate_wipe` | 0.85 / 0 | its nameplate's dust and thumb-wipe progress (the insert itself: `props.nameplate`) |
| `cam_angle` / `cam_face` / `cam_led` | 0.25 / 0 / 0 | security camera tilt (rad), swivel toward the viewer 0..1, LED 0..1 (None = 1 Hz blink; it stays bright in the dark) |
| `pipe_wobble` / `pipe_wobble_t0` | 0 / 0 | the low pipe shivers after the bonk (~1 s) and its sign swings (~2 s) |
| `pulse` / `bubbles` | True / True | slow shared glow breathing over the main pods (cheap fills); <= 12 rising bubbles |
| `parts` | ("rail", "stair") | fg: "rail" = deck front railing (only covers feet at the feet line; skip it for creature close-ups), "stair" = stair front stringer + handrail, "pipe" = the low pipe again OVER the characters |

Layers: `"bg"`, `"fg"`, `"shade"` (darkness per section + teal light near the
main pods, with `sets.shaded`).

`CATWALK_MARKS` (world px): feet_y 1500 (main deck x 640..4400), wall_y 1380,
front_y 1720, `pods` = list of {x, label, sub, kind ("empty" / "tiny" / "pod"),
glass (x, y, w, h), plate (rect), plate_c, ground (sleeper ground point),
sleeper_s}, **empty_glass (835, 720, 330, 560)**, **empty_plate (872, 1293, 255,
73)**, paw_spot (1120, 1236) (on its glass at creature paw height),
fog_spot (1070, 1170), creature_at_pod (1222, 1500) (faces LEFT to the
glass), tired_at_pod (1450, 1500), sec_cam (1250, 650) (wall mount), lamps,
stair_top (640, 1500), stair_steps (tread centres top first, rise 45, run
86, descending LEFT), stair_bottom (124, 1770), landing_feet_y 1770 (x
-800..124), **bonk_pipe = bonk_face (-90, 1150)** (props.low_pipe contact
point: the face touches it walking LEFT), bonk_feet (-44, 1770),
n_sections 4, sections. cam: pod_close (1170, 1290, 3.0), pod_two (1290,
1140, 1.75), plate (1000, 1330, 4.2), plates_pan_a (1500, 1180, 1.6) ->
plates_pan_b (3460, 1180, 1.6) (plates stay above y 1300 on screen; text
~33 world px = readable at 1.6), cam_up (1250, 760, 2.4), wide (1700, 900,
0.62), cascade (1500, 640, 0.56), eyes_dark (1180, 1180, 1.8), stair (400,
1360, 1.25), bonk (-20, 1300, 1.7).

Notes: Frame 0 can be `pod_close` (bright, lit) or `pod_pov` (section 17).
For the lights-out beat use `cascade` with `power_sections=
shaft_power_sections(t, t0, 4)`; the final "two pairs of eyes" is `power=0,
pod_glow≈0.03` (near-black, faint shapes).

## 14. `shaft_lower(ctx, t=0, layer="bg", power=0, lit=None, parts=None)` — s03

World **2600 x 1920** (drawable x -900..3300, y -1000..2620), people at
**s = 0.75**. The bottom of the shaft: a long steel stair (15 steps, rise 72,
run 70) coming down from a catwalk platform at the top left; three big
horizontal pipes (r 125 / 80 / 46) with flanges and saddles, a red valve
wheel, a gauge, vertical risers and a big elbow into the floor; a big wood
crate to hide beside (A), a crate stack to perch on (B), a barrel, a pallet
with a coiled hose; two floor grates glowing faint teal from below; the
SERVICE TUNNEL doorway (right) with a faint green sign; girders + darkness
overhead; a big "B3" stencil.

* `power` 0..1: work lamps (default **0**: dark in s03). `lit=True`: the
  surfaces as if lit, lamps off = **the flashlight-cone version**; `lit=False`
  (or power 0) = the dark version. Each is ONE cached bake; power in (0, 1)
  mixes two.
* Flashlight cones (fx): draw `shaft_lower(ctx, t)` (dark), then for each cone
  `ctx.save(); <cone path>; ctx.clip(); shaft_lower(ctx, t, lit=True); <beam
  haze>; ctx.restore()`. Do the same for `layer="fg"` pieces.
* fg parts: "stair" (front stringer + handrail, default), "crate" (crate A
  again, over someone standing BEHIND it in depth). They follow power/lit.
* `layer="shade"`: character darkness (sets.shaded); inside cones draw the
  characters unshaded (or shade with lit=True = nothing).

`SHAFT_LOWER_MARKS`: feet_y 1500, wall_y 1300, stair_top (-150, 420),
stair_steps (tread centres, top first, descending RIGHT), stair_bottom
(900, 1500), crate_a (1120, 1030, 560, 470), **hide_feet (980, 1500)** /
hide_feet2 (790, 1500) (crouched left of crate A; heads stay below its top
1030 at s 0.75 crouch), crate_b (2060, 1100, 460, 400), **perch (2400, 1100)**
(sit on the lower crate, head level with a guard's head), guard_a (2120,
1500) (in front of the stack), guard_b (1830, 1500), puddle (2150, 1506),
grates, exit (2470, 640, 300, 660), exit_feet (2620, 1340), pipes, lamps.
cam: wide (1300, 1000, 0.6), stair (420, 1000, 0.95), hide (1180, 1170, 1.7),
troll (2190, 1060, 1.9), sneak (1650, 1120, 1.15), exit (2380, 1100, 1.3).

## 15. `service_tunnel(ctx, t=0, layer="bg", door_open=0, reader="red", drip=True, parts=None)` — s04, s05, s06 doors

World **2400 x 1920** (drawable x -700..3100), people at **s = 0.75**. A quiet
concrete HushCorp service corridor, side-on: ceiling pipes, form-tie
concrete with a teal stripe and S-14 / S-15 stencils, **dim warm-orange
emergency lamps in cages** (x 700, 1330, 1960; static light pools on wall
and floor), darkness at both ends, a slow **drip** into a puddle (s04
"alone"), the low crate he sits on (+ a bigger one behind), the **dark side
tunnel** at the left that recedes into blackness (the far end Curiosity
walks off into) with a SHAFT A / CONTROL junction sign, and the heavy
**CONTROL keycard door** (LVL 9, hazard edges) with its reader.

* `door_open` 0..1 slides the panels apart; through it ("back") the dark
  control room: monitor glow and the tall chair's silhouette (s06 "doors");
  a cool light wedge spills on the floor. `reader` "red" | "green" | None.
* `tunnel_depth(k, lane=0)` -> `(x, y_feet, scale)`: k 0 = at the mouth
  (s x 1) .. 1 = deep in the dark (s x 0.17). Multiply the character's s by
  scale (its glow shrinks with it). TUNNEL_MARKS["far_path"] samples it.
* Layers: "bg", "back", "room" (bg minus back: back -> someone in the
  doorway -> room), "fg" (parts: "crate" = the seat crate over someone behind
  it), "shade" (warm lamp light + the dark ends on characters).

`TUNNEL_MARKS`: feet_y 1500, wall_y 1300, ceiling_y 300, **seat (1080, 1350)**
(hips on the crate: `human.ground_from_seat`), seat_feet (1080, 1500),
seat_crate, beside_seat (1380, 1500) (Curiosity tugging his sleeve), lamps,
mouth (90, 560, 420, 740), mouth_feet (300, 1500), far_end (300, 1010),
far_path, junction_sign (330, 430), door (1990, 520, 340, 780), door_feet
(2160, 1500), doorway_feet (2160, 1320), reader (2400, 960), reader_feet
(2250, 1500), drip (860, 1570). cam: wide (1200, 1020, 0.62), sit (1130,
1160, 1.6), sit_close (1080, 1160, 2.5), leave (560, 1150, 1.15), junction
(520, 1130, 1.4), alone (980, 1150, 1.25), door (2170, 1050, 1.15), reader
(2360, 1000, 2.6).

## 16. `control_room(ctx, t=0, layer="bg", **state)` — s01 (Boss), s06, s07

World **2100 x 1920** (drawable x -700..2800; a little wider than 1800 so the
hatch, doors, release console and chair have room), people at **s = 0.75**.
Dark navy room lit cool blue-teal by a **wall of 11 monitors** (default
static security feeds with CAM labels + REC dots) and an **observation
window onto the shaft**; console desk; CONTROL sign. Left to right: the
**side HATCH** (MAINT., 290 x 600: duck through, no crawling), the heavy
**sliding entrance doors** + keycard reader, the window with the **MASTER
RELEASE console** in front of it, the **LOCKDOWN pedestal** (big button +
SHAFT POWER switch), the Boss's **tall chair** facing the monitors, the
monitor wall.

| kwarg | default | meaning |
|---|---|---|
| `doors_open` / `reader` | 0 / "red" | sliding doors 0..1 (warm tunnel light spills in) / reader "red" \| "green" \| None |
| `hatch_open` | 0 | 0..1 swings the hatch toward the viewer (hinge left); its open panel is fg part "hatch" |
| `case_broken` / `lever` | 0 / 0 | the release case (see props.release_case); throw `props.shards(ctx, t, t0, *CONTROL_MARKS["release_impact"], floor_y=CONTROL_MARKS["release_floor_y"], s=0.75, dir=1)` at the smash |
| `pressed` | 0 | LOCKDOWN button 0..1 (+ red glow once pressed) |
| `switch` | 1 | SHAFT POWER toggle: 1 = ON (up, green) .. 0 = OFF (down, red) |
| `alarm` / `alarm_tint` | 0 / True | 0..1 three sweeping red ceiling beacons + the fx.alarm_wash tint (#9a0c1c, 1.2 s pulse). If the scene calls `fx.alarm_wash` too, pass `alarm_tint=False` (beacons only) |
| `monitor_fns` | None | `{index: fn(ctx, x, y, w, h, t)}`: draw a feed into CONTROL_MARKS["monitors"][index] (clipped); index 3 = the big main monitor (s01 "shows the two of them") |
| `window_fn` / `window_shutters` | None / 0 | draw your own view into CONTROL_MARKS["window"] (e.g. `sets.shaft(..., shutters=...)` under a camera), or the default curved tiers of pods with shutters 0..1 (the tiny JOY pod bottom-centre stays open) |
| `chair` / `chair_turn` | True / 0 | draw props.boss_chair at "chair": 0 = facing the monitors (its back hides her completely) .. 1 = facing camera |
| `parts` | ("chair",) | fg: "chair" (the chair pieces in front of the sitter), "hatch" (open panel, over someone going through), "release" (case glass/teeth + frame over hands) |

Layers: "bg", "back" (tunnel behind the doors + the crawlway behind the
hatch), "room" (bg minus back), "fg", "shade" (monitor light: cool glow from
the monitor wall + window, room darkness, alarm red).

`CONTROL_MARKS`: feet_y 1500, wall_y 1300, ceiling_y 260, **monitors** (11
rects; 3 = main (1500, 380, 400, 280)), **window (905, 380, 400, 420)**, doors
(430, 480, 360, 820), doorway_feet (610, 1330), door_feet (610, 1500),
reader (845, 940), hatch (40, 700, 290, 600), hatch_feet (185, 1500) (running
through), hatch_hold_feet (480, 1500) + hatch_hold (370, 960) (Emb holding it
open), **release (1105, 1500)** (props.release_console, s 0.75),
release_handle_up (1105, 861) / release_handle_down (1105, 1035) (T-handle
centre for hand IK; any lever: `props.release_console_handle(*release,
0.75, lever)`), release_impact (1095, 918), release_floor_y 1500, smash_feet
(855, 1500) / haul_feet (940, 1500) (Tiredness LEFT of the case facing
right, far from the Boss), **chair (1700, 1500)**, **boss_seat (1700, 1320)**
(hips: `human.ground_from_seat`), pedestal (1450, 1140), lockdown (1480,
1140), power_switch (1410, 1290) (panel centre; the toggle tip is ~24 px
above at ON), beacons. cam: wide (1050, 1000, 0.55), s01_boss (1640, 960,
1.15), monitor_main (1700, 520, 2.6), switch (1420, 1260, 3.0), doors (610,
1000, 0.95), chair (1640, 1060, 1.35), release (1020, 1000, 1.45),
release_close (1105, 900, 2.6), button (1450, 1230, 2.6), hatch (300, 1080,
1.1), two_shot (1350, 1060, 0.85).

## 17. `pod_pov(ctx, t=0, layer="bg", fog=0, fog_xy=None, glow=1)` — s01 frame 0 / thumbnail

World **1080 x 1920** = the frame at zoom 1. Looking OUT from inside
Curiosity's empty pod through its glass: bg = the bright lit shaft beyond
(soft far tiers of pods like depth of field, the logo, haze, the catwalk
railing and deck behind the creature); fg = the glass (teal tint, glare
streaks, faint old claw scratches) framed by the pod's capsule rim. Draw
Curiosity BETWEEN bg and fg, facing camera (`face=0`), ~s 2.4-3: its head
at POD_POV_MARKS["face"] (540, 890) (`draw_specimen(pose="sit", s=2.6,
face=0)` at creature_sit_feet (368, 1500)), paw on the glass at "paw" (770,
1080). `fog` 0..1 = breath fog on the glass at `fog_xy` (default "fog" (630,
975)): animate up then fade. `layer="shade"` = the pod's teal front light on
its face (sets.shaded). cam: default (540, 960, 1.0), push (560, 900, 1.12).
Bright and readable at frame 0.

---------------------------------------------------------------------------

## Props (`engine/props.py`)

All `name(ctx, x, y, s=1.0, ...)`; sizes at s = 1 (an adult is ~1000 px).
Board: `preview/sets_props.png`.

| prop | signature | size @ s=1 | anchor | states / notes |
|---|---|---|---|---|
| **cage** | `cage(ctx, x, y, s=1, t=0, door=0, latch="closed", rattle=0, inside_fn=None, rot=0, empty=None, label=True)` | 300 x 280 (+handle) | **top of the handle** (hands / Impulsivity's teeth) | `door` 0..1 barred front swings open toward the viewer (hinge left); `latch` "open"/"half" (wiggles with t)/"closed"; `rattle` 0..1 shakes about the handle + rattle marks; `inside_fn(ctx)` drawn behind the bars, origin = interior floor centre, interior ~224 x 168 (y negative is up), clipped; `empty=True` shows only bedding |
| rock | `rock(ctx, x, y, s=1, rot=0, seed=3)` | 92 x 70 | centre | lawn rock: `s=0.6` in the house set |
| recorder | `recorder(ctx, x, y, s=1, t=0, led=None, glow=0, rot=0, only_led=False, button=0)` | 96 x 58 | centre | black, HushCorp logo, red LED (`led` 0..1 / False = off / True = on, None = 1 Hz blink); `glow` red halo; `only_led=True` = LED + halo only (through the coat pocket); `button` 0..1 pushes the top button down (the off "click", local pos `RECORDER_BUTTON`) |
| pink_slip | `pink_slip(ctx, x, y, s=1, rot=0, curl=0)` | 190 x 220 | centre | "TERMINATION NOTICE" in bold ui; readable on a phone at s >= 1.2 on screen |
| tablet | `tablet(ctx, x, y, s=1, rot=0, t=0, screen_fn=None, glow=0, portrait=False, on=True)` | 300 x 200 | centre | `screen_fn(ctx, sx, sy, sw, sh, t)` into the clipped screen (default logo); `glow` cool halo |
| clipboard | `clipboard(ctx, x, y, s=1, rot=0)` | 190 x 276 | centre | "WORK ORDER" checklist (printer disguise) |
| picture_frame | `picture_frame(ctx, x, y, s=1, rot=0, face_down=False, cracked=False, wire=True)` | 120 x 140 | the nail (frame hangs 28 px below) | photo of the two as kids; `face_down` shows the back |
| plates_stack | `plates_stack(ctx, x, y, s=1, lift=0, n=4, t=0)` | 190 wide | bottom centre | `lift` 0..1 raises the top plate ~70 px with a careful tilt |
| shards | `shards(ctx, t, t0, x, y, seed=0, n=12, s=1, floor_y=None, dir=1, spread=1, power=1)` | 20-40 px each | burst origin | <= 15 glass shards fly from t0 (gravity, spin), land on `floor_y` (default y + 320 s), tiny settle hop, then rest. `dir` +1 right, -1 left, 0 both |
| black_van | `black_van(ctx, x, y, s=1, door=0, facing=1, tint=0.75, t=0, layer="all", bounce=0)` | 2700 x 1180 (use s 0.45 by the house) | ground under the middle | side view, HushCorp logo + wordmark, tinted windows (`tint`), sliding door `door` 0..1 rearward; `layer` "interior" (dark opening only) -> person climbing in -> "body"; `facing` -1 flips; body cached |
| trash_can | `trash_can(ctx, x, y, s=1, knocked=0, spill=True, dir=1, seed=0, lid_on=True, dent=0)` | 260 x 420 | bottom centre | `knocked` 0..1 tips it over sideways toward `dir` (pivot on the bottom corner; it then lies to that side), lid rolls off, trash spills |
| streetlight | `streetlight(ctx, x, y, s=1, t=0, broken=0, on=False, lean=None, seed=1)` | ~2700 tall | base centre | `broken` 0..1: shattered head, glass bits, leaning pole, rare short spark flicker (> 0.5); `on` dusk glow |
| debris | `debris(ctx, x, y, s=1, kind="plank", rot=0, seed=0)` | 80-200 | centre | kinds: plank, brick, paper, can, chunk, shard, bolt |
| sock | `sock(ctx, x, y, s=1, rot=0, color, stripe)` | 120 x 70 | centre | |
| shirt | `shirt(ctx, x, y, s=1, rot=0, color, flap=0, t=0, print_=True)` | 240 x 220 | centre | `flap` 0..1 waves it in flight |
| sweater | `sweater(ctx, x, y, s=1, state="folded", lump=0, wiggle=0, t=0, rot=0, color)` | folded 200 x 90 / flat 380 x 300 / draped 380 x 130 | bottom centre | knit chevrons; "draped": `lump` 0..1 mound height, `wiggle` 0..1 makes it shift with t (s06) |
| fly | `fly(ctx, x, y, s=1, t=0, rot=0)` | 26 px | centre | wings buzz with t |
| leaf | `leaf(ctx, x, y, s=1, rot=0, color)` | 70 x 40 | centre | |
| red_button_console | `red_button_console(ctx, x, y, s=1, pressed=0, t=0, alarm=0, label=True)` | 620 x 560 | bottom centre (floor) | big red dome at `BUTTON_OFFSET` (150, -470) x s; `pressed` 0..1 squashes it; `alarm` turns the lamps red |
| containment_pod | `containment_pod(ctx, x, y, s=1, t=0, sleeper_fn=None, seed=0, glow=1, pulse=None, lit=True, label=None, sub=None, dust=0)` | 420 x 760 | centre of the glass | teal liquid glow, caps, tubes, 5 bubbles, glass sheen; `sleeper_fn(ctx, x, y, s, t, seed)` called at the sleeper centre with s = 0.9 (clipped); `pulse` None = 0.25 Hz; `label` (+ sub, dust) = a nameplate on the bottom cap |
| sleeper_silhouette | `sleeper_silhouette(ctx, x, y, s=1, t=0, seed=0, color)` | 260 x 240 | centre | default curled creature shape (fin ears, tail), faint breathing |
| doormat | `doormat(ctx, x, y, s=1, rot=0, bunch=0, text="GO AWAY", t=0)` | 540 x 150 | centre | `bunch` 0..1 rumples it + flips a corner (the s10 trip) |
| **monitor_game_screen** | `monitor_game_screen(ctx, x, y, w, h, t, speed=1, seed=0, hud=True, scanlines=True)` | any rect | rect | 48 x 30 chunky-pixel platformer: parallax clouds/hills, scrolling ground, ? blocks, spinning coins, a blob enemy, the hero hopping every 1.3 s, score + hearts HUD. ~1 ms. Used by the bedroom monitor; works full-screen for a close-up |
| hush_logo | `hush_logo(ctx, x, y, r, color=None, hole="#ffffff", lw=None, wordmark=False, word_color=None, word_size=None, ring=True)` | radius r | circle centre | teal circle + keyhole; `wordmark=True` adds the wide-spaced "HUSHCORP" (font ui) below; returns bottom y |
| **nameplate** | `nameplate(ctx, x, y, s=1, text="CURIOSITY", sub="SPECIMEN 00", dust=0, wipe=0, rot=0, seed=0, size=44, light=1)` | ~300 x 100 (width follows the text: `nameplate_size(text, sub)`) | centre | brushed-steel pod plate, rivets, engraved text (sub line small mono, main line big ui). `dust` 0..1 grey-brown film (0.85+ hides the text); `wipe` 0..1 clears it left -> right behind a ragged front with a faint smear (**the thumb-wipe insert**: animate wipe with the thumb's x; s ~3-4 for the insert). Returns its rect |
| **security_camera** | `security_camera(ctx, x, y, s=1, t=0, cam_angle=0.35, led=None, face=0, flip=False, glow=1, only_led=False)` | ~330 x 200 | wall mount plate | arm out to a pivot; white body + hood + lens; `cam_angle` tilt (rad, + = down), `face` 0..1 swivels the lens toward the viewer (round lens shows), `led` red LED 0..1 (None = 1 Hz blink), `only_led` = LED + halo only. Returns the lens centre |
| **low_pipe** | `low_pipe(ctx, x, y, s=1, r=46, rise=300, span=300, reach=(700, 500), t=0, wobble=0, wobble_t0=0, hazard=True, sign=True, side=1)` | ~1500 x 400 | **the contact point** (outer side of the descending bend at face height) | a ceiling pipe that DIPS to face height (hazard bands, flanges, hangers, a MIND YOUR HEAD sign beyond the dip). Walking LEFT the face meets (x, y) (`side=-1` mirrors). `wobble` after the bonk: shiver ~1 s, sign swings ~2 s (>= 0.6 s reaction, LESSON 8) |
| **keycard** | `keycard(ctx, x, y, s=1, rot=0, photo=True, glint=0, back=False)` | 340 x 216 | centre | white card, teal HUSHCORP band + logo, Emb's tiny ID photo (orange tuft, round glasses, blush), "ACCESS LEVEL / **LVL 9** / RESEARCH", barcode. Readable in an insert at on-screen s >= ~1.4. `glint` 0..1 sweeps a light streak; `back` = plain back |
| **flashlight** | `flashlight(ctx, x, y, s=1, rot=0, on=True, glow=1, t=0, flip=False)` | 250 x 72 | middle of the grip (the fist) | side view; lens points along +x rotated by rot (`flip` = -x). `on` 0..1: bright lens face + small halo (the beam is fx). Returns `{"lens": (x, y), "angle": a}` (`FLASHLIGHT_LENS` = (116, 0) local) |
| **phone** | `phone(ctx, x, y, s=1, rot=0, t=0, screen_fn=None, on=True, buzz=0, glow=0)` | 128 x 250 | centre | front view; `screen_fn(ctx, sx, sy, sw, sh, t)` into `PHONE_SCREEN` (-56, -110, 112, 220) local, clipped; default lock screen "6:02"; `buzz` 0..1 shiver + buzz marks; `glow` screen halo |
| phone_chat_screen | `phone_chat_screen(msgs=(("them", "you ok?", 0.0),), avatar=True, typing=None)` | — | — | returns a screen_fn: header with Emb's little avatar (no name), bubbles that pop in at their times (`"them"` grey left, `"me"` blue right), optional `typing=(t0, t1)` dots. E.g. `[("them", "you ok?", 0), ("me", "zzz", t_reply)]` |
| **release_case** | `release_case(ctx, x, y, s=1, t=0, case_broken=0, lever=0, label=True, glow=1, part="all", seed=0, light=1)` | 260 x 470 | bottom centre of the base plate | MASTER RELEASE lever in a glass case (red label plate, LOCK / RELEASE marks, slot). `case_broken`: 0 intact, (0, 1) cracks spread from `release_impact(x, y, s)`, 1 smashed (jagged teeth + bits; throw `props.shards` from release_impact). `lever` 0 = UP (locked) .. 1 = DOWN (released), swinging toward the viewer (T-handle grows mid-swing); `release_handle(x, y, s, lever)` = grip point. `part` "back" / "front" (hands between) |
| **release_console** | `release_console(ctx, x, y, s=1, t=0, case_broken=0, lever=0, alarm=0, part="all", seed=0)` | 380 x 1010 | floor under the middle | pedestal (hazard band, status lamps, "SHAFT A — ALL PODS") carrying the case at y - 540 s: handle at shoulder height UP, waist DOWN. `release_console_handle(x, y, s, lever)`, `release_console_impact(x, y, s)` |
| **lockdown_button** | `lockdown_button(ctx, x, y, s=1, pressed=0, t=0, glow=0, label=True)` | 200 x 150 (+ label) | base centre on its surface | red mushroom button in a hazard collar, "LOCKDOWN" plate; `pressed` 0..1 sinks it; `glow` red halo |
| **power_switch** | `power_switch(ctx, x, y, s=1, on=1, label="SHAFT POWER", t=0)` | 200 x 280 | panel centre | labelled panel with a big toggle (ON up / OFF down, green / red lamp); `on` animates the flip. Returns the lever tip (fingertip spot) |
| **boss_chair** | `boss_chair(ctx, x, y, s=1, turn=0, part="all", t=0, rim=None, dir=1, rim_a=0.85)` | ~400 x 1010 | floor under the seat | tall high-backed swivel chair (dark leather, tufted front, embossed logo on the back, disc base). `turn` 0 = facing away (hides a sitter) .. 0.5 profile (screen-right for dir=+1) .. 1 = facing camera; `part` "behind" (before the sitter) / "front" (after); `rim` rim-light colour (None = cool teal, False = none). Seat at `BOSS_CHAIR_SEAT`*s = 240 s, back top `BOSS_CHAIR_TOP`*s |
| crate | `crate(ctx, x, y, s=1, w=420, h=360, kind="wood", stencil="HUSHCORP", seed=0, top=True, light=1)` | w x h | bottom centre | wood (X braces) or "steel" crate with a lid sliver; returns the top y |
| cage_lamp | `cage_lamp(ctx, x, y, s=1, on=1, color="#ffb35a", down=True, halo=True)` | 80 x 180 | wall bracket | caged emergency / work lamp; `on` lights the bulb (+ halo) |
| hazard_band | `hazard_band(ctx, x, y, w, h, step=None, col1, col2, lw=3, slant=1)` | rect | rect | yellow/ink diagonal stripes |

Drawing helpers also exported by props (used by sets): `fs`, `rect`, `ell`,
`polyf`, `blob`, `line`, `curve`, `spaced_text`, `keyhole_path`. Episode 2 board:
`preview/sets_ep2_props.png` (`python3 preview/sets_ep2_props.py`).

---------------------------------------------------------------------------

## Per-frame cost (720 x 1280, `ctx.scale(720/1080)`, 48 frames after caching, bg + fg)

Measured with `python3 preview/sets_perf.py` (first = cold cache render).

| case | first frame | per frame |
|---|---|---|
| bedroom s01 framing (game screen running) | 83 ms | **5.3 ms** |
| bedroom during `shake` (posters/lamp/figurine/dust live) | 73 ms | 7.8 ms (only while shaking) |
| bedroom s05 wide (zoom 0.56) | 29 ms | 4.7 ms |
| window exterior | 24 ms | 3.5 ms |
| street view (leaf + bird) | 16 ms | 1.8 ms |
| house wide, damage=1 | 26 ms | 3.9 ms |
| house porch (zoom 2.3) | 47 ms | 3.6 ms |
| living room wide / low heap z1.5 | 50 / 116 ms | 2.1 / 0.7 ms |
| hallway crawl / burst | 35 / 39 ms | 3.7 / 3.7 ms |
| office two-shot | 29 ms | 2.8 ms |
| lobby wide | 21 ms | 3.9 ms |
| lab alarm (wide) / console | 13 / 40 ms | 4.7 / 3.3 ms |
| corridor alarm | 9 ms | 3.2 ms |
| tower exterior | 21 ms | 1.7 ms |
| city fall approach 0 / 0.8 | — | 8.3 / 2.4 ms (live, no cache) |
| sewer wide (drips + motes) / teal end | 17 / 33 ms | 1.4 / 2.7 ms |
| sewer POV | 45 ms | 1.6 ms |
| shaft reveal wide (zoom 0.56) / arrive z2.2 | 115 / 147 ms | **7.6 / 3.5 ms** (target < 25) |

**Episode 2** (`python3 preview/sets_ep2_test.py --perf`, same method, bg +
fg; "first" = cold bake). Target < 6 ms per held framing: met everywhere;
the starred rows are transitions that last only a few frames.

| case | first | per frame |
|---|---|---|
| catwalk pod_two / plates pan / wide | 195 / 171 / 200 ms | **3.8 / 4.5 / 2.7 ms** |
| catwalk dark (power 0) / pod_close z3 | 204 / 387 ms | 3.7 / 1.8 ms |
| catwalk cascade mid-transition [0, .5, 1, 1] * | 143 ms | 6.4 ms (only during a 0.16 s section cut) |
| shaft reveal wide (EP1 framing, faster pulse) / cascade / dark | 124 / 5 / 122 ms | 5.5 / 4.2 / 1.0 ms |
| shaft shutters 0.6 (zoom 1.4) | 114 ms | 6.0 ms |
| shaft_lower wide lit / hide dark / troll dark | 29 / 57 / 96 ms | 1.9 / 2.2 / 1.7 ms |
| shaft_lower power 0.5 (lamp fade) * | 105 ms | 7.0 ms |
| service_tunnel sit / wide / door opening | 114 / 27 / 65 ms | 1.9 / 1.7 / 2.7 ms |
| control_room s01 boss / wide / chair turning | 70 / 31 / 95 ms | 3.1 / 2.5 / 3.5 ms |
| control_room release + alarm 1 | 114 ms | 5.8 ms |
| bedroom dawn wide / flop (bed_squash) / pillow z2.8 | 102 / 176 / 551 ms | 2.6 / 5.2 / 4.0 ms |
| bedroom EP1 s01 (unchanged) | 52 ms | 5.4 ms |
| pod_pov (+ fog) | 73 ms | 3.9 ms |

Add ~1-2 ms per `sets.shaded(...)` block. A flashlight cone costs one extra
clipped blit of the lit bake (~0.5-1.5 ms per cone, by its area). Changing a
baked state (labels, sleepers, `sunrise` step, a new power-section
combination) re-bakes once (100-550 ms).

Zoom moves: every 1/8 octave of zoom re-renders the visible static (core's
quantisation). The bedroom 1.0 -> 1.7 push-in averages ~15 ms/frame; the
s13 shaft pull-out 3.2 -> 0.56 over 46 frames averages ~62 ms/frame (worst
~180 ms), about 3 s of extra render time once. Holding a framing is cheap.

## Previews

* Boards (whole world + phone framings with grey stand-ins and the UI
  safe zones shaded): `preview/sets_<name>.png` for bedroom, window_ext,
  street, house, living, hall, office, lobby, lab, corridor, tower,
  cityfall, sewer, sewerpov, shaft; props: `preview/sets_props.png`.
* Larger single shots: `preview/sets_bedroom_shot0.png` (s01 opening),
  `preview/sets_shaft_shot2.png` (shaft reveal), `preview/sets_sewer_shot0.png`,
  `preview/sets_bedroom_tilecheck.png` (zoom 3.6 tiled close-up).
* Regenerate: `python3 preview/sets_test.py [name ...]`,
  `python3 preview/sets_test.py --one <name> <shot index>`,
  `python3 preview/sets_props_test.py`, `python3 preview/sets_perf.py [name]`.
* **Episode 2 boards** (world + phone framings with grey stand-ins and the
  UI zones shaded; dark framings use `sets.shaded`; flashlight cones are
  simulated as fx would draw them): `preview/sets_ep2_catwalk.png`,
  `sets_ep2_shaft.png`, `sets_ep2_lower.png`, `sets_ep2_tunnel.png`,
  `sets_ep2_control.png`, `sets_ep2_bedroom.png`, `sets_ep2_podpov.png`,
  props `sets_ep2_props.png`; with the real creature rig:
  `sets_ep2_catwalk_sleepers.png`, `sets_ep2_podpov_real.png`.
  Regenerate: `python3 preview/sets_ep2_test.py [catwalk shaft lower tunnel
  control bedroom podpov]`, one framing big: `python3
  preview/sets_ep2_shot.py <board> <shot index ...>`, timings: `python3
  preview/sets_ep2_test.py --perf [name]`, seam/hole check (renders every
  framing on two backgrounds and diffs): `python3 preview/sets_ep2_seams.py`.
