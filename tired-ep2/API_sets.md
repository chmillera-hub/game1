# API — `engine/sets.py` (locations) and `engine/props.py` (props)

Flat-colour, plum-ink (`PAL["ink"]`) backgrounds and props for TIREDNESS.
Everything is procedural and deterministic. Static parts are cached with
`core.cached` (through `sets.static_layer` / `sets.cached_or_live`); only
small sparse details animate (game screen, drips, motes, shimmer, beacons,
bird, leaf, pod pulse).

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

Layers: `"bg"`, `"back"` (hallway through the doorway), `"room"` (bg without
back), `"fg"`.

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

`SHAFT_MARKS`: horizon_y 2350, catwalk_feet_y 2400, catwalk_x (-520, 640),
tunnel_mouth (-380, 2400), tired_feet (300, 2400), creature_feet (390,
2400), logo (540, 1560). cam: arrive (60, 2250, 2.2), two_close (340, 2300,
3.2), reveal_wide (540, 1900, 0.56), title_wide (420, 2150, 0.75), look_up
(540, 1300, 0.9). For the eyes-wide close-up, frame the shaft at zoom 1.2-2
and draw Tiredness in screen space at s 2.4-3 (don't zoom the world to 10x).

---------------------------------------------------------------------------

## Props (`engine/props.py`)

All `name(ctx, x, y, s=1.0, ...)`; sizes at s = 1 (an adult is ~1000 px).
Board: `preview/sets_props.png`.

| prop | signature | size @ s=1 | anchor | states / notes |
|---|---|---|---|---|
| **cage** | `cage(ctx, x, y, s=1, t=0, door=0, latch="closed", rattle=0, inside_fn=None, rot=0, empty=None, label=True)` | 300 x 280 (+handle) | **top of the handle** (hands / Impulsivity's teeth) | `door` 0..1 barred front swings open toward the viewer (hinge left); `latch` "open"/"half" (wiggles with t)/"closed"; `rattle` 0..1 shakes about the handle + rattle marks; `inside_fn(ctx)` drawn behind the bars, origin = interior floor centre, interior ~224 x 168 (y negative is up), clipped; `empty=True` shows only bedding |
| rock | `rock(ctx, x, y, s=1, rot=0, seed=3)` | 92 x 70 | centre | lawn rock: `s=0.6` in the house set |
| recorder | `recorder(ctx, x, y, s=1, t=0, led=None, glow=0, rot=0, only_led=False)` | 96 x 58 | centre | black, HushCorp logo, red LED (`led` 0..1, None = 1 Hz blink); `glow` red halo; `only_led=True` = LED + halo only (through the coat pocket) |
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
| containment_pod | `containment_pod(ctx, x, y, s=1, t=0, sleeper_fn=None, seed=0, glow=1, pulse=None, lit=True)` | 420 x 760 | centre of the glass | teal liquid glow, caps, tubes, 5 bubbles, glass sheen; `sleeper_fn(ctx, x, y, s, t, seed)` called at the sleeper centre with s = 0.9 (clipped); `pulse` None = 0.25 Hz |
| sleeper_silhouette | `sleeper_silhouette(ctx, x, y, s=1, t=0, seed=0, color)` | 260 x 240 | centre | default curled creature shape (fin ears, tail), faint breathing |
| doormat | `doormat(ctx, x, y, s=1, rot=0, bunch=0, text="GO AWAY", t=0)` | 540 x 150 | centre | `bunch` 0..1 rumples it + flips a corner (the s10 trip) |
| **monitor_game_screen** | `monitor_game_screen(ctx, x, y, w, h, t, speed=1, seed=0, hud=True, scanlines=True)` | any rect | rect | 48 x 30 chunky-pixel platformer: parallax clouds/hills, scrolling ground, ? blocks, spinning coins, a blob enemy, the hero hopping every 1.3 s, score + hearts HUD. ~1 ms. Used by the bedroom monitor; works full-screen for a close-up |
| hush_logo | `hush_logo(ctx, x, y, r, color=None, hole="#ffffff", lw=None, wordmark=False, word_color=None, word_size=None, ring=True)` | radius r | circle centre | teal circle + keyhole; `wordmark=True` adds the wide-spaced "HUSHCORP" (font ui) below; returns bottom y |

Drawing helpers also exported by props (used by sets): `fs`, `rect`, `ell`,
`polyf`, `blob`, `line`, `curve`, `spaced_text`, `keyhole_path`.

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
