# MIND HQ set — `src/sets/hq.mjs`

The control room inside the mind: the console, the screen of consciousness, the fire-alarm station, the
exit door, and the deep BACK OF THE MIND where the Void stands. There are four views. Each view is its own
world-coordinate stage. Sheet: `node tools/sheet_hq.mjs [--full] [--clean]` writes `out/sheet_hq.png`
(and `--full` also writes `out/hq_<n>.png` at 720x1280).

```js
import { applyCamera, vignette } from '../engine.mjs';
import { drawHQ, drawHQForeground, drawAlarmLight, HQ_VIEWS, HQ_PRESETS, hqScaleAt, ALARM_REACH } from '../sets/hq.mjs';

const st = { ...HQ_PRESETS.calm, t, alarm: S.k(t, [...]) };   // one state object per frame
g.save();
applyCamera(g, { ...HQ_VIEWS.front.cams.wide, ...drift(t) });
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
| `drawHQForeground` | `(g, view, state)` | **front:** the console (back panel) plus the amber glow rising onto the operators. **Other views:** a low mist band over the feet. Always call it. |
| `drawAlarmLight` | `(g, view, state)` | A rotating-beacon sweep plus a gentle red wash that pulses at 1.2 Hz (multiply ≤0.3, soft additive near the beacon). It never makes a hard full-frame flash. Call it after characters. |
| `drawScreenContent` | `(g, x, y, w, h, t, mode, radius?)` | What the screen of consciousness shows, clipped to a rounded rect. `mode` is `'room' \| 'calm' \| 'alarm'`. Use it for close-ups of the screen. Cached at a canonical size, so animating `w`/`h` is fine. |
| `drawConsole` | `(g, x, y, w, scale, state)` | A standalone console. `(x,y)` is the centre of its base on the floor. See the Console section. |
| `drawAlarmStation` | `(g, x, y, scale, state)` | Pull station, conduit, bell and strobe. `(x,y)` is the **handle's rest centre**. Returns `{handle:[x,y], bell:[x,y], beacon:[x,y]}` and the returned handle moves with `alarmPulled`. |
| `consoleButtonPos` | `(x, y, w, scale, index, deck=1)` | World position of a console button, for hand targets. |
| `HQ_VIEWS` | `{view:{width,height,anchors,cams}}` | `anchors[name] = [x, y, charScale]` (the ground point for characters). Camera presets are `{x,y,zoom}`, ready for `applyCamera`. |
| `hqScaleAt` | `(view, y)` | Perspective character scale for a floor point at world `y`. Use it when walking characters around. |
| `HQ_PRESETS` | `calm, alarm, chaos, shadow, dawn` | State bundles. Spread them and add `t`. |
| `ALARM_REACH` | `[108, -176]` | FEAR's arm target (character-local) that puts its hand on the handle from `fearSpot` / `fearAtAlarm`. |
| `HQ_COLORS` | palette | Set colours, if you need to tint things to match the set. |

## State (one object, every field optional)

| field | range / default | meaning |
|---|---|---|
| `t` | seconds | Drives mist drift, the beacon rotation, bell vibration, console twinkle, screen animation and motes. **Always pass it.** |
| `alarm` | 0..1 / 0 | Alarm intensity. The strobe dome lights and rotates (0.9 rev/s), the bell vibrates with ringing arcs, the big console buttons turn red, the niche glows red in `alarm` view, and `drawAlarmLight` gets its strength from it. Ramp it over about 0.3 s, not a hard cut. |
| `alarmPulled` | 0..1 / 0 | Handle travel. 1 means pulled fully down (26 px × station scale). |
| `lightsDim` | 0..1 / 0 | Darkens the room (up to 62 %). Emissive things stay lit: the EXIT sign, the screen, console lights and daylight through an open door. **It does not darken characters.** If you want them dimmed, draw `rgba(6,5,14, 0.3*lightsDim)` over them yourself. |
| `screenMode` | `'room'` \| `'calm'` \| `'alarm'` / `'room'` | Screen of consciousness (`back` view). `room` is the narrator's night desk (lamp, open "my feelings" notebook, window with moon) seen through their eyes. `calm` is a soft sunrise. `alarm` is the same desk tinted red, with a gently pulsing ⚠. The screen's light on the room follows the mode. |
| `screenModeB`, `screenBlend` | mode, 0..1 | Crossfade from `screenMode` to `screenModeB`. |
| `consoleGlow` | 0..1.5 / 1 | Brightness of the console lights and of the amber spill on the operators. |
| `consolePress` | `{index: 0..1}` | A pressed button sinks and flares. Indices are 0..15, four per station (see Console). |
| `voidShadow` | 0..1 / 0 | A dark shadow that grows out from the Void's feet across the floor (ease-out). At 1 it covers a large part of the room. It is drawn under characters and does not darken them. |
| `mist` | 0..1 / 0.35 | Slow drifting mist: in the cavern and at the threshold (front), and low over the floor (other views, plus the foreground layer). |
| `doorOpen` | 0..1 / 0 | Exit door (front view) swings open, showing warm outside light. |

Presets: `calm` (default look), `alarm` (bell ringing, handle down, red screen), `chaos` (alarm, dimmer,
door open, console glow low), `shadow` (Void shadow out, dimmer, more mist), `dawn` (calm sunrise screen,
console glowing a bit warmer: the ending).

## Perspective

Every view except `alarm` is one-point perspective. Character scale grows linearly with floor y; use
`hqScaleAt(view, y)`.

- **front:** VP (450, 520). Scale = `0.000925 * (y - 520)`. Samples: y 850 → 0.31, 950 → 0.40, 1032 → 0.47, 1200 → 0.63, 1384 → 0.80.
- **back:** VP (450, 430). Scale = `0.001097 * (y - 430)`. Samples: y 900 → 0.52, 1100 → 0.74, 1300 → 0.95, 1500 → 1.17.
- **alarm:** wall faces the camera; the wall base is at y 1360. Scale = `1.8 * (y - 700) / 706`, which gives 1.8 at y 1406.
- **backOfMind:** horizon y 1040, VP at the distant light (380, 1032). Scale = `(y - 1040) / 620`. Samples: y 1400 → 0.58, 1600 → 0.90, 1700 → 1.06.

Character heights at scale 1: FEAR 330, CONSCIOUSNESS 600, emotions 400–520, the Void 1700.

## Views, anchors, cameras

### `front` — 900 × 1600. Establishing shot from the screen, looking into the room

The vaulted room has warm pendant lamps and sconces. A great rounded arch at the back opens onto the dark
cavern (BACK OF THE MIND), where the Void stands. The rounded EXIT door with its green sign is on the left
wall. The fire-alarm station (box, bell, strobe) is on the right wall. The floor has an emblem ring.
The console's back panel fills the bottom ~25 %, and its top rim is at y ≈ 1247 (centre) to 1268 (ends).

| anchor | [x, y, scale] | use |
|---|---|---|
| `consoleSlot1..4` | [165 / 355 / 545 / 735, 1384, 0.80] | Emotions behind the console, facing camera. Feet are hidden; the console covers everything below y ≈ 1250, so the upper ~55–70 % of each emotion shows (head, shoulders and arms). |
| `consoleFear` | [450, 1384, 0.80] | FEAR joining the console at the end. Spread slots 2 and 3 by about ±40 px to make room. |
| `fearSpot` | [734, 973, 0.42] | FEAR at the alarm. With `armR: {target: ALARM_REACH, bend: 1, hand: 'grip', front: true}` the hand lands on the handle. |
| `alarm` | [779, 899, 0.42] | Handle centre at rest. Pulled, it moves down 11 px. Bell at ≈ (779, 794) and beacon at ≈ (779, 753). |
| `exitDoor` | [184, 936, 0.385] | Standing in the doorway. The door itself spans x ≈ 107–189 and y ≈ 640–936. |
| `ceoSpot` | [300, 1032, 0.474] | CONSCIOUSNESS looking around (on the floor ring's left edge). |
| `voidSpot` | [450, 830, 0.37] | The Void's feet just inside the arch. Its scale is deliberately larger than the perspective value (0.29) so it towers: top ≈ y 200, and the arch top is at y 158. |
| `cageSpot` | [598, 846, 0.30] | Time-out cage beside the Void. FEAR in the cage uses the same point and scale. |

Cams: `wide` {450, 800, 0.8} (the whole stage), `establish` {450, 790, 0.95} (best thumbnail framing),
`console` {450, 1150, 1.35}, `alarm` {700, 880, 1.9}, `void` {450, 560, 1.25}, `door` {200, 820, 1.7}.

**Z-order:** `drawHQ` → Void → cage → FEAR / CEO → emotions (sort by y) → `drawHQForeground` (console +
amber spill) → anything nearer than the console → `drawAlarmLight`.
⚠ In `front`, the console exists **only** in `drawHQForeground`.

### `back` — 900 × 1600. From the back of the mind, looking toward the screen

The SCREEN OF CONSCIOUSNESS is at x 130, y 140, w 640, h 500 (corner radius 46) and fills the upper half
inside a plum-and-gold bezel. Its light (in the colour of the current mode) falls on the wall and floor. The
console is in the midground with its controls facing the camera: base y 899, front lip y ≈ 827, deck
y 771–827, ridge lights y ≈ 765. The floor in the foreground fades into the dark back of the mind.

| anchor | [x, y, scale] | use |
|---|---|---|
| `consoleBack1..4` | [141 / 347 / 554 / 759, 925, 0.543] | Emotions at the console, backs to the camera. Their heads land around y 640–710, just under the screen, and their hands reach the deck. |
| `button1..4` | [126 / 320 / 514 / 708, 802] | The big amber button of each station (indices 0, 4, 8, 12), as hand targets. |
| `fearSpot` | [420, 1371, 1.03] | Foreground. |
| `cageSpot` | [150, 1453, 1.12] | Foreground left. The cage is cropped by the frame edge, which is intended. |
| `ceoSpot` | [640, 1288, 0.94] | Foreground. A standing CONSCIOUSNESS here covers `consoleBack3`/`4`, so use it only in shots about the CEO. |
| `voidEdge` | [1080, 1600, 0.90] | The Void at the right edge and nearest of all (draw it last). Only its dark left flank and rim show in frame. To show the hood, move x to ≤ 900; it then covers `consoleBack4`. |

Cams: `wide` {450, 800, 0.8}, `screen` {450, 520, 1.0}, `console` {450, 760, 1.5}, `foreground` {450, 1080, 1.0}.
**Z-order:** `drawHQ` (room, screen, console) → emotions → foreground characters by y → Void →
`drawHQForeground` (low mist) → `drawAlarmLight` (the beacon is off-frame left, so the red light comes from
the left).

### `alarm` — 900 × 1600. Side-wall close-up (alarm pulls, hand on the shoulder)

A frontal plum wall with a vault arch overhead, pilasters, a wainscot and a warm sconce at upper left
(250, 600). An arched niche frames the station. There is a sticky note: *"only for REAL emergencies!"*.
Wall base is at y 1360; the floor is below it.

| anchor | [x, y, scale] | use |
|---|---|---|
| `handle` | [592, 1089, 1.8] | Handle rest centre. Pulled, it is at y 1089 + 47 × `alarmPulled`. |
| `fearAtAlarm` | [398, 1406, 1.8] | FEAR facing right. `armR: {target: [108, -176 + 26*alarmPulled], bend: 1, hand: 'grip', front: true}` keeps the hand on the handle as it travels. FEAR's head overlaps the box's left edge slightly, which is intended. |
| `ceoBeside` | [205, 1475, 1.98] | CONSCIOUSNESS beside FEAR (true 55 % ratio, ≈1186 tall). Use `crouch` or kneel for the hand on the shoulder. FEAR's shoulders in world coords are ≈ (349, 1165) on the CEO side and (447, 1165). |
| `bell` | [592, 639] | Bell centre (r ≈ 76 px). |
| `beacon` | [592, 468] | Strobe dome; the beams sweep from here. |

Cams: `wide` {450, 800, 0.8}, `medium` {450, 960, 1.0}, `pull` {540, 1000, 1.45}, `bell` {560, 640, 1.6}.
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

Cams: `wide` {500, 889, 0.72} (the whole stage), `ground` {500, 1140, 1.0}, `cage` {360, 1360, 1.45},
`hood` {680, 420, 1.1} (the Void's face), `distance` {360, 1040, 1.6}.
**Z-order:** `drawHQ` → Void → cage / characters by y → `drawHQForeground` (low mist over the feet) →
`drawAlarmLight` (here it is only a wash and a red pulse of the distant light, with no beams).

## Props

**Console** — `drawConsole(g, x, y, w, scale, state)`. Extra state: `consoleSide` and `consoleDeck`.
- `consoleSide: 'controls'` (the default) is seen from behind the operators. Heights above the base are
  multiplied by `scale`: the front face rises to the lip at 140, the slanted deck is 64 × `consoleDeck`
  deep, and a ridge with chasing indicator lights adds 26 more.
- There are 16 buttons, four per station (left to right as seen in `back`). In station *i*:
  - 4*i* is the big amber button
  - 4*i*+1 is the station-colour button (gold, blue, coral, mint)
  - 4*i*+2 is amber
  - 4*i*+3 is peach
- Each station also has a lever and a small gauge.
- `consoleSide: 'back'` is seen from the screen side: a rounded machine hull 210 × `scale` tall, a warm rim
  lit by the buttons beyond, indicator dots and vent panels.

**Alarm station** — `drawAlarmStation(g, x, y, scale, state)`.
- At scale 1 it is sized for FEAR at scale 1. Local coordinates, with the origin at the handle's rest centre:
  - box: x −42..42, y −84..64 ("FIRE" / "PULL DOWN")
  - handle: 56 × 22, travels +26
  - conduit: up to −214
  - bell: centre (0, −250), r 42; the ringing arcs reach r ≈ 78
  - strobe dome: centre (0, −340), 26 × 32, so its top is at −372
- `state.bell === false` draws only the box.

**Screen content** — `drawScreenContent(g, x, y, w, h, t, mode, radius)`.
- It works at any aspect ratio, laid out relative to `w`/`h` (designed for about 1.3:1).
- For a POV close-up of the room screen, draw it full frame:
  `drawScreenContent(g, 0, 0, 720, 1280, t, 'room', 0)`. It will be stretched; it is best at aspect ≥ 1.

## Gotchas

- **Draw cost:** `drawHQ` + `drawHQForeground` + `drawAlarmLight` take about 5–12 ms per frame at typical
  settings. The worst case (alarm, shadow and mist all on, zoom 1.5) is about 18 ms.
- **First-use stall:** static art is cached per view and per resolution level. Levels are picked from the
  current zoom: 0.8 / 1 / 1.5 / 2. The first frame at a new level paints the cache, which takes
  100–400 ms once per process.
- **Zoom limit:** zooms above about 2.2 upscale the 2× cache and look slightly soft.
- **Leftover state:** all draw functions save and restore. They also put back `fillStyle` and `strokeStyle`,
  which `@napi-rs/canvas`'s `restore()` does not do. Always set your own styles anyway.
- **Fonts:** Fraunces, Patrick Hand and Caveat are registered by the module itself.
- **Shadow and dimming don't touch characters:** `voidShadow` and `lightsDim` change only the set. Darken
  characters standing in the Void's shadow yourself if needed, for example by drawing them with a darker
  overlay clipped to their area.
- **Front-view overlap:** FEAR at `fearSpot` stands right behind the tallest emotion in `consoleSlot4`.
  Put CALM (the tallest) in slot 1 or 2.
- **Exiting through the door:** `doorOpen` swings the door open. To have a character leave, walk it to
  `exitDoor`, scaling it with `hqScaleAt('front', y)`, and fade its `alpha` to 0 in the doorway.
- **Timing:** keep `alarm` changes eased. The beacon and bell are already animated by `t`; don't
  strobe-animate `alarm` itself.
- **Two Void shadows:** `drawVoid` can draw its own spreading floor shadow (`pose.shadowSpread`). Use
  either that or the set's `voidShadow`, not both at full strength; they would double up.
- **Static `voidShadow`:** the shadow grows from the Void's feet. For "its shadow filling the room", ramp
  0 → 1 over 3–5 s.
