# MIND HQ set — `src/sets/hq.mjs`

The control room inside the mind: the console, the screen of consciousness, the fire-alarm station, the
exit door, and the deep BACK OF THE MIND where the Void stands. There are four views. Each view is its own
world-coordinate stage. Sheet: `node tools/sheet_hq.mjs [--full] [--clean] [--placeholders]` writes
`out/sheet_hq.png` (`--full` also writes `out/hq_<n>.png` at 720x1280) and prints draw timings.

```js
import { applyCamera, vignette, drift } from '../engine.mjs';
import { drawHQ, drawHQForeground, drawAlarmLight, HQ_VIEWS, HQ_PRESETS, HQ_STATIONS, hqScaleAt, ALARM_REACH } from '../sets/hq.mjs';

const st = { ...HQ_PRESETS.calm, t, alarm: S.k(t, [...]) };   // one state object per frame
g.save();
applyCamera(g, { ...HQ_VIEWS.front.cams.establish });
drawHQ(g, 'front', st);                       // 1. set (behind everyone)
/* 2. characters, back to front (sort by anchor y) */
drawHQForeground(g, 'front', st);             // 3. console / low mist IN FRONT of characters
drawAlarmLight(g, 'front', st);               // 4. soft red light over everything (no-op when alarm = 0)
g.restore();
vignette(g, 0.35);
```

## Exports

| export | signature | notes |
|---|---|---|
| `drawHQ` | `(g, view, state)` | Draws the set. `view` is `'front' \| 'back' \| 'alarm' \| 'backOfMind'`. It also paints a dark margin around the stage, so a camera that strays outside it shows no stale pixels. |
| `drawHQForeground` | `(g, view, state)` | **front:** the console (its back hull) plus the amber glow rising onto the operators. **Other views:** a low mist band over the feet. Always call it. |
| `drawAlarmLight` | `(g, view, state)` | A rotating-beacon sweep plus a gentle red wash pulsing at 1.2 Hz (multiply, max alpha 0.3) on **the alarm's side of the room only**, fading out across the frame. Never a full-frame flash. Call it after characters. |
| `drawScreenContent` | `(g, x, y, w, h, t, mode, radius?)` | What the screen of consciousness shows, clipped to a rounded rect. `mode` is `'room' \| 'calm' \| 'alarm'` (anything else falls back to `room`). Use it for close-ups of the screen. Cached at a canonical size, so animating `w`/`h` is fine. |
| `drawConsole` | `(g, x, y, w, scale, state)` | A standalone console. `(x,y)` is the centre of its base on the floor. See Props. |
| `drawAlarmStation` | `(g, x, y, scale, state)` | Pull station, conduit, bell and strobe. `(x,y)` is the **handle's rest centre**. Returns `{handle:[x,y], bell:[x,y], beacon:[x,y]}`; the returned handle moves with `alarmPulled`. |
| `consoleButtonPos` | `(x, y, w, scale, index, deck=1)` | World position of a console button, for hand targets. |
| `HQ_VIEWS` | `{view:{width,height,anchors,cams}}` | `anchors[name] = [x, y, charScale]` (the ground point for characters; scale 0 = a point, not a standing spot). Camera presets are `{x,y,zoom}` for `applyCamera`; every preset stays inside its stage. |
| `HQ_STATIONS` | `{JOY,SADNESS,ANGER,CALM}` | Which emotion works which console station: `{station, front, back, buttons}` — see Continuity. |
| `hqScaleAt` | `(view, y)` | Perspective character scale for a floor point at world `y`. Use it when walking characters around. |
| `HQ_PRESETS` | `calm, alarm, chaos, shadow, dawn` | State bundles. Spread them and add `t`. |
| `ALARM_REACH` | `[108, -176]` | FEAR's arm target (character-local) that puts its hand on the handle from `front.fearSpot` / `alarm.fearAtAlarm`. Add `26 * alarmPulled` to y to follow the handle down. |
| `HQ_COLORS` | palette | Set colours, if you need to tint things to match the set. |

## State (one object, every field optional)

| field | range / default | meaning |
|---|---|---|
| `t` | seconds | Drives mist drift, the beacon rotation, bell vibration, console twinkle, screen animation and motes. **Always pass it.** |
| `alarm` | 0..1 / 0 | Alarm intensity. The strobe dome lights and rotates (0.9 rev/s), the bell vibrates with ringing arcs, the big console buttons turn red, the niche glows red in `alarm` view, the distant light pulses red in `backOfMind`, and `drawAlarmLight` gets its strength from it. Ramp it over about 0.3 s, not a hard cut. |
| `alarmPulled` | 0..1 / 0 | Handle travel. 1 means pulled fully down (26 px × station scale). |
| `lightsDim` | 0..1 / 0 | Darkens the room (up to 62 %). Emissive things stay lit: the EXIT sign, the screen, console lights and daylight through an open door. **It does not darken characters.** If you want them dimmed, draw `rgba(6,5,14, 0.3*lightsDim)` over them yourself. |
| `screenMode` | `'room'` \| `'calm'` \| `'alarm'` / `'room'` | Screen of consciousness (`back` view). `room` is the narrator's night desk (lamp, mug, window with moon) seen through their eyes, with the SAME open notebook the real-room scenes show (`props.mjs` `drawNotebook`: the story page + the crayon drawing of Fear pulling the alarm and the dark hooded one), keystone-warped onto the desk. `calm` is a soft sunrise. `alarm` is the same desk tinted red, with a gently pulsing ⚠. The screen's light on the room follows the mode. |
| `screenModeB`, `screenBlend` | mode, 0..1 | Crossfade from `screenMode` to `screenModeB`. |
| `consoleGlow` | 0..1.5 / 1 | Brightness of the console lights, the warm halo along the console ridge and on the wall under the screen (`back`), and the amber spill on the operators (`front`). |
| `consolePress` | `{index: 0..1}` | A pressed button sinks and flares (back view / `drawConsole`); in `front` the matching operator gets a brighter amber spill. Indices 0..15, four per station (see `HQ_STATIONS`). |
| `voidShadow` | 0..1 / 0 | A dark shadow that grows out from the Void's feet across the floor (ease-out). At 1 it covers a large part of the room. It is drawn under characters and does not darken them. |
| `mist` | 0..1 / 0.35 | Slow drifting mist: in the cavern and at the threshold (front), and low over the floor (other views, plus the foreground layer). |
| `doorOpen` | 0..1 / 0 | Exit door (front view) swings open, showing warm outside light. |

Presets: `calm` (default look), `alarm` (bell ringing, handle down, red screen), `chaos` (alarm, dimmer,
door open, console glow low), `shadow` (Void shadow out, dimmer, more mist), `dawn` (calm sunrise screen,
console glowing a bit warmer: the ending).

## Continuity: which way is which

The `front` view looks from the screen into the room; the `back` view looks the other way, toward the
screen. Left and right swap between them:

| | `front` view | `back` view |
|---|---|---|
| exit door | left wall | right wall (off-frame) |
| fire alarm | right wall | left wall (off-frame; its red light comes from the left) |
| JOY / SADNESS / ANGER / CALM | `consoleSlot4 / 3 / 2 / 1` | `consoleBack1 / 2 / 3 / 4` |

`HQ_STATIONS[name]` gives `{ station, front, back, buttons }`, e.g. `HQ_STATIONS.JOY = { station: 0, front:
'consoleSlot4', back: 'consoleBack1', buttons: [0,1,2,3] }`. Each station's coloured button matches its
emotion, so always seat them this way:
`for (const n in HQ_STATIONS) drawEmotion(g, n, ...HQ_VIEWS.front.anchors[HQ_STATIONS[n].front], pose)`.
This order also keeps the shortest emotion next to the alarm in `front`, so FEAR at `fearSpot` stands clear of
the heads at the console.

Screenplay note: s02b01 asks for the alarm "on the right wall" in a shot looking at the screen. In this set the
alarm is on the right only in the `front` view (as s05b03 asks). For s02b01, either frame FEAR at the alarm in
`front`/`alarm` and use `back` for the console/screen, or accept the alarm off-frame left (its red light then
brushes the left side of the operators, as written in s02b02).

## Perspective

Every view except `alarm` is one-point perspective. Character scale grows linearly with floor y; use
`hqScaleAt(view, y)`.

- **front:** VP (450, 520). Scale = `0.000925 * (y - 520)`. Samples: y 850 → 0.31, 950 → 0.40, 1032 → 0.47, 1200 → 0.63, 1384 → 0.80.
- **back:** VP (450, 430). Scale = `0.001097 * (y - 430)`. Samples: y 900 → 0.52, 1100 → 0.74, 1300 → 0.95, 1500 → 1.17.
- **alarm:** wall faces the camera; the wall base is at y 1360. Scale = `1.8 * (y - 700) / 706`, which gives 1.8 at y 1406.
- **backOfMind:** horizon y 1040, VP at the distant light (380, 1032). Scale = `(y - 1040) / 620`. Samples: y 1400 → 0.58, 1600 → 0.90, 1700 → 1.06.

Character heights at scale 1: FEAR 330, CONSCIOUSNESS 600, emotions 394–523, the Void 1700.

## Views, anchors, cameras

### `front` — 900 × 1600. Establishing shot from the screen, looking into the room

The vaulted room has warm pendant lamps and sconces. A great rounded arch at the back opens onto the dark
cavern (BACK OF THE MIND), where the Void stands. The rounded EXIT door with its green sign is on the left
wall. The fire-alarm station (box, bell, strobe) is on the right wall. The floor has an emblem ring.
The console's back hull fills the bottom ~22 %; its top rim is at y ≈ 1247 (centre) to 1268 (ends).

| anchor | [x, y, scale] | use |
|---|---|---|
| `consoleSlot1..4` | [165 / 355 / 545 / 735, 1384, 0.80] | Emotions behind the console, facing camera: CALM, ANGER, SADNESS, JOY (see Continuity). Feet are hidden; the console covers everything below y ≈ 1250, so the head and shoulders show. |
| `consoleMid` | [450, 1384, 0.80] | The console's middle, on the floor: CONSCIOUSNESS working among the emotions (s17b02). Spread slots 2 and 3 by about ±40 px. |
| `consoleFear` | [450, 1328, 0.80] | FEAR at the console **on its step-stool** (s19): the feet are raised 70 px at scale 1 (hidden by the console) so its scarf and shoulders clear the rim. Spread slots 2 and 3 by ±40 px. |
| `fearSpot` | [734, 973, 0.42] | FEAR at the alarm. With `armR: {target: ALARM_REACH, bend: 1, hand: 'grip', front: true}` the hand lands on the handle. JOY's star tuft (slot 4) stays about 45 px below its feet. |
| `alarm` | [779, 899, 0.42] | Handle centre at rest. Pulled, it moves down 11 px. Bell at ≈ (779, 794), beacon at ≈ (779, 751). |
| `exitDoor` | [184, 936, 0.385] | Standing in the doorway. The door itself spans x ≈ 107–189 and y ≈ 640–936. |
| `ceoSpot` | [300, 1032, 0.474] | CONSCIOUSNESS looking around (on the floor ring's left edge). |
| `voidSpot` | [450, 830, 0.37] | The Void's feet just inside the arch. Its scale is deliberately larger than the perspective value (0.29) so it towers: top ≈ y 200; the arch top is at y 158. |
| `cageSpot` | [598, 846, 0.30] | Time-out cage beside the Void. FEAR in the cage uses the same point and scale. |

Cams: `wide` {450, 800, 0.8} (the whole stage), `establish` {450, 800, 0.9} (best thumbnail: Void, door,
alarm and all four emotions in frame), `console` {450, 1120, 1.35}, `alarm` {700, 880, 1.9},
`void` {450, 560, 1.25}, `door` {215, 820, 1.7}.

**Z-order:** `drawHQ` → Void → cage → FEAR / CEO → emotions (sort by y) → `drawHQForeground` (console +
amber spill) → anything nearer than the console → `drawAlarmLight`.
⚠ In `front`, the console exists **only** in `drawHQForeground`.

### `back` — 900 × 1600. From the back of the mind, looking toward the screen

The SCREEN OF CONSCIOUSNESS is at x 130, y 140, w 640, h 500 (corner radius 46) and fills the upper half
inside a plum-and-gold bezel. Its light (in the colour of the current mode) falls on the wall and floor. The
console is in the midground with its controls facing the camera: base y 899, front lip y ≈ 827, deck
y 771–827, ridge lights y ≈ 765; its warm light glows on the wall under the screen. The floor in the
foreground fades into the dark back of the mind.

| anchor | [x, y, scale] | use |
|---|---|---|
| `consoleBack1..4` | [141 / 347 / 554 / 759, 925, 0.543] | Emotions at the console, backs to the camera: JOY, SADNESS, ANGER, CALM. Heads land around y 690–790 just under the screen, and the default back-view `pressButton` hands rest on the console's front. |
| `consoleBackMid` | [450, 925, 0.543] | Between stations 2 and 3: CONSCIOUSNESS at the console facing the screen (s15b01), or FEAR on its stool (raise it ~50 px). |
| `button1..4` | [126 / 320 / 514 / 708, 802] | The big amber button of each station (indices 0, 4, 8, 12). They sit right behind each operator's head, so a hand reaching one is hidden. |
| `fearSpot` | [420, 1371, 1.03] | Foreground. |
| `cageSpot` | [150, 1453, 1.12] | Foreground left. The cage is cropped by the frame edge, which is intended. |
| `ceoSpot` | [640, 1288, 0.94] | Foreground. Any standing CONSCIOUSNESS in the foreground covers part of the console row (the camera is behind the operators); use `consoleBackMid` for the CEO at the console. |
| `voidEdge` | [1080, 1600, 0.90] | The Void at the right edge and nearest of all (draw it last). Only its dark left flank and rim show in frame. To show the hood, move x to ≤ 900; it then covers `consoleBack4`. |

Cams: `wide` {450, 800, 0.8}, `screen` {450, 640, 1.0} (screen + the whole console row; the look-back shot),
`console` {450, 760, 1.5} (stations 2 and 3), `foreground` {450, 960, 1.0}.
**Z-order:** `drawHQ` (room, screen, console) → emotions → foreground characters by y → Void →
`drawHQForeground` (low mist) → `drawAlarmLight` (the beacon is off-frame left, so the red light comes from
the left).

### `alarm` — 1000 × 1600. Side-wall close-up (alarm pulls, hand on the shoulder)

A frontal plum wall with a vault arch overhead, pilasters, a wainscot and a warm sconce (330, 600). An arched
niche (x 542–842) frames the station. A sticky note left of the niche, level with the bell, says *"only for
REAL emergencies!"* (centre (488, 700)). Wall base is at y 1360; the floor is below it.

| anchor | [x, y, scale] | use |
|---|---|---|
| `handle` | [692, 1089, 1.8] | Handle rest centre. Pulled, it is at y 1089 + 47 × `alarmPulled`. |
| `fearAtAlarm` | [498, 1406, 1.8] | FEAR facing right. `armR: {target: [108, -176 + 26*alarmPulled], bend: 1, hand: 'grip', front: true}` keeps the hand on the handle as it travels. FEAR's head just overlaps the box's left edge (with `lean` it can cover the "F" of FIRE). FEAR's shoulders: ≈ (449, 1165) on the CEO side and (547, 1165). |
| `ceoBeside` | [238, 1475, 1.976] | CONSCIOUSNESS standing beside FEAR, a little nearer the camera (draw it after FEAR). True 55 % ratio, ≈1186 tall: the head is cropped in `medium`. |
| `ceoKneel` | [135, 1520, 2.091] | CONSCIOUSNESS kneeling (`kneel: 1`, facing 1) in the foreground left for the hand on the shoulder. Its raised knee stays clear of FEAR's body, and `armR: {preset: 'onShoulder', target: selfLocal(135, 1520, 2.091, 1, 433, 1170)}` lays the hand on FEAR's near shoulder at a gentle downward angle. Draw FEAR first, then CONSCIOUSNESS. |
| `bell` | [692, 639] | Bell centre (r ≈ 76 px; the ringing arcs reach r ≈ 140). |
| `beacon` | [692, 455] | Strobe dome; the beams sweep from here. |

Cams: `wide` {500, 800, 0.8}, `medium` {445, 960, 1.0} (FEAR, the whole station, CEO beside),
`twoShot` {430, 1065, 1.2} (kneeling CEO + FEAR at FEAR's height; crops the station's right side),
`pull` {630, 1000, 1.45}, `bell` {660, 640, 1.6}.
**Z-order:** `drawHQ` → FEAR → CONSCIOUSNESS (nearer) → `drawHQForeground` → `drawAlarmLight`.

### `backOfMind` — 1000 × 1778. The deep, dim back of the mind

A near-black violet cavern. Huge faint vault ribs recede toward a **distant soft light**, the far-away HQ
(a tiny glowing screen above an amber console line) at (380, 1032). Faint glowing pathways on the floor
converge on it. This light is "the distance" the Void stares into. There are drifting motes and mist bands,
and a soft pool of light on the ground at the cage.

| anchor | [x, y, scale] | use |
|---|---|---|
| `void` | [700, 1600, 0.90] | The Void (≈1530 tall, top ≈ y 70). At the `ground` cam it towers out of the top of frame; at `wide` it is fully visible. It faces the distant light (screen-left). |
| `cage` | [270, 1630, 0.95] | Cage floor centre. |
| `fearInCage` | [270, 1622, 0.94] | FEAR inside the cage. |
| `fearOutside` | [468, 1668, 1.01] | FEAR out of the cage, between the cage and the Void (in front of its robe). |
| `ceo` | [105, 1735, 1.12] | CONSCIOUSNESS putting FEAR in the cage. |
| `distantLight` | [380, 1032] | Eyeline target for "staring into the distance" or "looking at the screen". |

Cams: `wide` {500, 889, 0.72} (the whole stage), `ground` {500, 1138, 1.0}, `cage` {360, 1335, 1.45},
`hood` {675, 520, 1.25} (the Void from the chest up; push in from here for the hood), `distance` {360, 1040, 1.6}.
**Z-order:** `drawHQ` → Void → cage / characters by y → `drawHQForeground` (low mist over the feet) →
`drawAlarmLight` (here only a small wash and a red pulse of the distant light, with no beams).

## Props

**Console** — `drawConsole(g, x, y, w, scale, state)`. Extra state: `consoleSide` and `consoleDeck`.
- `consoleSide: 'controls'` (the default) is seen from behind the operators. Heights above the base are
  multiplied by `scale`: the front face rises to the lip at 140, the slanted deck is 64 × `consoleDeck`
  deep, and a ridge with chasing indicator lights (and a soft warm halo) adds 26 more.
- There are 16 buttons, four per station (left to right as seen in `back`). In station *i*:
  - 4*i* is the big amber button
  - 4*i*+1 is the station-colour button (gold, blue, coral, mint = JOY, SADNESS, ANGER, CALM)
  - 4*i*+2 is amber
  - 4*i*+3 is peach
- Each station also has a lever and a small gauge.
- `consoleSide: 'back'` is seen from the screen side: a rounded machine hull 210 × `scale` tall, a warm rim
  lit by the buttons beyond, indicator dots and vent panels. Station 0 is on the right from this side.

**Alarm station** — `drawAlarmStation(g, x, y, scale, state)`.
- At scale 1 it is sized for FEAR at scale 1. Local coordinates, with the origin at the handle's rest centre:
  - box: x −42..42, y −84..64 ("FIRE" / "PULL DOWN")
  - handle: 56 × 22, travels +26
  - conduit: up to −214
  - bell: centre (0, −250), r 42; the ringing arcs reach r ≈ 78
  - strobe dome: base at −340, 26 × 32, top at −372 (returned `beacon` = (0, −352))
- `state.bell === false` draws only the box.

**Screen content** — `drawScreenContent(g, x, y, w, h, t, mode, radius)`.
- It works at any aspect ratio, laid out relative to `w`/`h` (designed for about 1.3:1).
- For a POV close-up of the room screen, draw it full frame:
  `drawScreenContent(g, 0, 0, 720, 1280, t, 'room', 0)`. It will be stretched; it is best at aspect ≥ 1.

## Gotchas

- **Draw cost** (set only: `drawHQ` + `drawHQForeground` + `drawAlarmLight`, 720x1280): about 3–13 ms at
  calm settings; with alarm + shadow + mist + dim + door all on, about 10–24 ms (the `front` console cam is
  the heaviest). Every static layer is one resampled full-frame `drawImage` (~4 ms), so the set never costs
  less than that. A full `front` frame with the real Void, cage, CEO, FEAR and four emotions measured
  ~29 ms calm and ~37 ms with the alarm on, close to the 40 ms budget: keep extra full-frame overlays light.
- **First-use stall:** static art is cached per view and per resolution level. Levels are picked from the
  current zoom: ≤0.82 → 0.8, ≤1.06 → 1, ≤1.56 → 1.5, else 2. The first frame at a new level paints the
  cache, which takes about 30–160 ms once per process (more at level 2).
- **Zoom limit:** zooms above about 2.2 upscale the 2× cache and look slightly soft.
- **Leftover state:** all draw functions save and restore. They also put back `fillStyle` and `strokeStyle`,
  which `@napi-rs/canvas`'s `restore()` does not do. Always set your own styles anyway.
- **Fonts:** Fraunces, Patrick Hand and Caveat are registered by the module itself.
- **Shadow and dimming don't touch characters:** `voidShadow` and `lightsDim` change only the set. Darken
  characters standing in the Void's shadow yourself if needed, for example by drawing them with a darker
  overlay clipped to their area.
- **The red wash is partial on purpose** (side wall / one side of the operators, as the screenplay asks). It
  is a multiply ramp, so characters on the alarm side are tinted red and the far side is not.
- **Exiting through the door:** `doorOpen` swings the door open. To have a character leave, walk it to
  `exitDoor`, scaling it with `hqScaleAt('front', y)`, and fade its `alpha` to 0 in the doorway.
- **Timing:** keep `alarm` changes eased. The beacon and bell are already animated by `t`; don't
  strobe-animate `alarm` itself.
- **Two Void shadows:** `drawVoid` can draw its own spreading floor shadow (`pose.shadowSpread`). Use
  either that or the set's `voidShadow`, not both at full strength; they would double up. In `backOfMind`
  the floor is already near-black, so the set's shadow is subtle there; `shadowSpread` reads more strongly.
- **Static `voidShadow`:** the shadow grows from the Void's feet. For "its shadow filling the room", ramp
  0 → 1 over 3–5 s.
