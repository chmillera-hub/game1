# STAGING — director's notes for the scene animators

"The Void and My Fear" · 720×1280 · 24 fps · 339.07 s · 20 scenes.

You animate 1–3 scenes without seeing anyone else's. This file is what makes the cuts match. When it conflicts
with a module doc's default anchor or the screenplay's literal wording, **this file wins** (each deviation is
listed in §1.7 with its reason). Everything here was checked by rendering; the reference frames are
`out/staging_test_*.png` (listed in §1.8). Look at `staging_test_reference.png` before you start.
A script-supervisor pass re-rendered the hand contacts and the cuts (`out/staging_check_*.png`, §1.8) and
corrected this file in place; where an older test sheet disagrees with the text, the text wins.

Contents: §1 geography · §2 continuity table · §3 shot plan per scene · §4 light & colour script · §5 shared conventions.

---------------------------------------------------------------------------------------------------------------

## 1. GEOGRAPHY

### 1.1 The floor plan (seen from above, the screen at the top)

```
                          FRONT OF THE MIND (the screen of consciousness)
   ┌──────────────────────── SCREEN OF CONSCIOUSNESS ─────────────────────────┐
   │                  ╔══════════════ CONSOLE ══════════════╗                 │
   │                    JOY   SADNESS   ANGER   CALM   (seen from behind)      │
   │  ALARM WALL                  (CEO works at the middle)          EXIT WALL │
   │  🔔 FIRE ALARM ▣  ← Fear's post                          EXIT door ▯      │
   │                              floor ring                                  │
   └─────────────────────╮          GREAT ARCH           ╭──────────────────────┘
                         │      ▲ THE VOID      ▢ cage     │
                         │   (cage at the Void's own RIGHT foot = the EXIT side; the Void faces the screen)
                         │     the floor runs on into the dark cavern…        │
                            BACK OF THE MIND (from back here, the HQ is a far glow = "the distance")
```
(Plan = seen from above with the screen at the top, i.e. the `back` view's left/right: alarm wall west/left,
EXIT wall east/right. The Void faces north, so its own right hand is east, toward the EXIT wall. Both views that
show the Void look south at its front, so east = screen-left there: the cage reads screen-left of the Void.)

The Void stands just beyond the arch, **facing the screen of consciousness**. The cage stands at its feet, on
**the Void's own right-hand side**. Because the Void is drawn facing the camera in every view that shows it
(`front` and `backOfMind`), that makes one simple picture rule:

> **THE CAGE IS ALWAYS SCREEN-LEFT OF THE VOID, IN EVERY SHOT. The Void always uses its screen-left hand
> (`handL`) on the cage and on Fear.**

`backOfMind` is a storybook cheat: we look at the Void's front, yet the far HQ glow sits in the background.
Picture rules beat compass rules. Never flip the cage (`flip` stays 1): **the padlock is on the cage's right jamb
(the Void's side) and the door swings open to the left (away from the Void)** in every view.

### 1.2 Screen-direction rules (memorise this table)

| view | camera looks… | screen-LEFT is | screen-RIGHT is | "the distance" / screen of consciousness | the Void is… |
|---|---|---|---|---|---|
| `front` (900×1600) | from the screen into the room | EXIT door wall; the cage (at the Void's screen-left foot = its own right foot) | ALARM wall; Fear's post | **toward the camera** (Void `STARE_F` = looking at us) | centre, in the arch, facing us |
| `back` (900×1600) | from the back of the room to the screen | ALARM wall (off-frame; its red light comes from the left) | EXIT wall (off-frame) | straight ahead: the big screen | **never drawn** (it and the cage are behind the camera), not even in Fear's POV s15b01 (§1.3) |
| `alarm` (1000×1600) | at the alarm wall | **the back of the mind: the Void, the cage** | the console / screen | screen-right | off-frame left. Fear at the alarm looks **up-left** to see it |
| `backOfMind` (1000×1778) | at the Void and cage, the far HQ behind | the cage; the way back to the HQ (characters arrive from and leave to the left) | deeper dark; the Void | **the distant glow (380,1032) on the horizon**: left of and below the Void's hood (Void `STARE_B`), almost straight above the cage (Fear looks UP to it) | right half, facing us, hood turned left to the glow |
| REAL_ROOM (840×1280) | at SELF at the desk | lamp | mug, books | the window above SELF (moon upper-right) | (s20: the star-hood stands in the window) |

Movement directions:
* **Toward the back** (alarm → cage): `alarm` view right→left; `front` view away from camera (up-screen);
  `backOfMind` enter from frame-left.
* **Toward the front** (cage → console): `backOfMind` exit frame-left along the floor (the way the CEO and Fear
  came in, s08); `alarm` view left→right (s17b01); `front` view toward camera. Note: the far glow (380,1032) is
  almost straight ABOVE the cage on screen (cage x 430), not to its left. Walking "toward the glow" from
  FEAR_STOP_B (x 250) would be up-RIGHT, so never describe the s16 exit as "toward the glow".
* The `backOfMind` → `alarm` cuts reverse the on-screen direction by construction (BoM: toward the front = left;
  alarm: toward the front = right). s07→s08 is safe (nobody moves across the cut). s16→s17 is bridged with a
  clean exit and a clean entrance (empty frames on both sides of the cut, see s16/s17 in §3 and §1.7-9).
* **Evacuation**: `front` view right→left to the EXIT door (left wall).

Eyelines (keep them identical in every shot):

| who → what | where they look on screen |
|---|---|
| Fear at the alarm → the Void | **up-left** (`lookX −0.5…−0.7, lookY −0.6…−0.8`), in `front`, `alarm` and backdrop shots |
| Fear at the alarm → CEO (kneeling/beside, to its left) | left, slightly up (`lookX −0.6, lookY −0.2…−0.3`): flatter than to the Void |
| CEO at the alarm → Fear | right and down (`lookX 0.6, lookY 0.45`) |
| CEO at the alarm → the Void | up-left / back over the left shoulder (`headTurn −0.5…−0.7, lookY −0.7`) |
| Fear in/at the cage → the Void's hood | **up-right** (`lookX 0.3…0.5, lookY −1`) |
| Fear at the cage → the console / the glow / the emotions | **up, a touch left** (body `facing −1` = back to the Void; `headTilt` back, `lookX −0.1…−0.3, lookY −0.7…−0.9`). The glow is nearly straight above the cage on screen (verified: `staging_check_bom.png` cells 7–8; the old `lookX −0.5, lookY −0.45` looks well left of it) |
| Emotions in `back` view → Fear (Fear's POV = camera) | `lookBack`, `lookSide`: JOY & SADNESS **+1**, ANGER & CALM **−1** (faces turn to the centre) |
| Void → the screen | `front`: `STARE_F`; `backOfMind`: `STARE_B` |
| Void → Fear (on the threshold) | `backOfMind`: `LOOK_FEAR` |

### 1.3 Views, what is where, which anchors

**`front`** (drawHQ 'front'): vaulted room, warm lamps; the great arch at the back with the Void inside it (top of
hood y≈200, face (450,277)); EXIT door on the left wall (x 107–189, y 640–936); FIRE ALARM on the right wall
(handle (779,899), bell (779,794), beacon (779,751)); the console hull fills the bottom ≈22 % (rim y≈1247). The
screen of consciousness is behind the camera: it is never seen in this view. Anchors used: `voidSpot` (=VOID_F),
`consoleSlot1..4` (CALM, ANGER, SADNESS, JOY, left→right), `consoleMid`, `consoleFear`, `fearSpot`, `exitDoor`.
**Overridden:** `cageSpot` → `CAGE_F` (302,846) and `ceoSpot` → `CEO_SPOT_F` (400,1040) (the old ceoSpot hid the cage).

**`back`**: the big SCREEN (x 130–770, y 140–640) with the console row under it, emotions with their backs to
us: `consoleBack1..4` = JOY, SADNESS, ANGER, CALM (left→right, the mirror of `front`); the CEO at `consoleBackMid`.
**Do not draw** the back view's `cageSpot` / `voidEdge` (they would put a giant cage in the foreground; see
`staging_test_back_room.png`, cell 1). No exception: in s15b01 (Fear's POV) the Void is behind-LEFT of Fear in
the real layout (it stands west of the cage) but on Fear's right in every back-of-mind picture, so either edge
contradicts something — leave `voidEdge` out.

**`alarm`**: the alarm wall facing the camera. Fear at `fearAtAlarm` (498,1406, 1.8) facing right onto the handle;
CEO at `ceoBeside` (238,1475, 1.976) standing or `ceoKneel` (135,1520, 2.091) kneeling, always **left of Fear**.

**`backOfMind`**: the cavern; the far HQ glow at (380,1032). Anchors used: `void` (=VOID_B). **Overridden:**
the cage → `CAGE_B` (430,1630) — in front of the Void's left robe, under its left sleeve, so that (a) Fear in the
cage can turn its back to the Void (`facing −1`) and look up at the glow, and (b) the Void's hand reaches the lock,
the threshold and the push zone with exact contact. The anchors `cage`, `fearInCage`, `fearOutside`, `ceo` are not used.

**REAL_ROOM**: use `REALROOM.anchors` and `REALROOM.cameras` as documented (`opening`, `desk`, `face`, `full`).

### 1.4 STAGING CONSTANTS — paste this block into your scene, do not invent other values

```js
import { cagePoint } from '../sets/props.mjs';
// --- the Void
const VOID_F = [450, 830, 0.37];                    // front view (= HQ anchor voidSpot)
const VOID_B = [700, 1600, 0.9];                    // backOfMind (= HQ anchor void)
const STARE_F   = { headTurn: 0,     headDown: 0.1  }; // front: staring at the screen of consciousness (= at us)
const STARE_B   = { headTurn: -0.65, headDown: 0.12 }; // backOfMind: staring into the distance (the far glow, screen-left)
const LOOK_FEAR = { headTurn: -0.3,  headDown: 0.8  }; // backOfMind: looking down at Fear on the threshold
const COSMOS_RESIDUE = 0.5;                          // from s14b10 on: faint stars + first galaxies
const COSMOS_OPTS = { seed: 7, glyphs: 1 };          // s14 only; afterwards { seed: 7, glyphs: 0 }
// --- the cage (NEVER flip; lock on the right jamb = Void side; door opens to the left)
const CAGE_F = [302, 846, 0.3];                     // front: at the Void's screen-left foot (overrides cageSpot 598)
const CAGE_B = [430, 1630, 0.952];                  // backOfMind: in front of the Void's left robe (overrides anchor 270)
// --- people, front view
const CEO_SPOT_F     = [400, 1040, 0.481];          // CEO "looking around", clear of the cage
const CEO_AT_ALARM_F = [640, 1000, 0.444];          // CEO kneeling (kneel 1) beside Fear at the alarm
const FEAR_ALARM_F   = [734, 973, 0.42];            // = fearSpot
const FEAR_TIPTOE_F  = [532, 1350, 0.8];            // Fear on tiptoe behind the console: mouth clears the rim (s17)
const CEO_ASIDE_F    = [640, 1300, 0.722];          // CEO stepped aside, behind SADNESS/JOY (s17b05)
const ROW_S19 = { CALM: 205, ANGER: 330, FEAR: 450, SADNESS: 570, JOY: 695 }; // x at y 1384 (Fear: consoleFear y 1328)
// --- people, backOfMind
const THRESH      = [440, 1648, 0.97];              // Fear on the cage threshold, "half in, half out" (s12b07–s16b02)
const FEAR_STOP_B = [250, 1700, 1.065];             // where Fear stops and looks back (s16b03–b04)
const CEO_B_DOOR  = [300, 1730, 1.12];              // CEO kneels here, swings the gate shut and locks it (s08b01 + insert)
const CEO_B_BARS  = [140, 1735, 1.12];              // CEO kneeling → rising, hand on the leftmost bar, body off-frame (s08b02;
                                                    //   at the old x 180 the kneeling CEO's head showed at the left edge)
// --- verified Void hand settings (contact error 0.00, re-checked in out/staging_check_final.png cells 1–7)
// handL ALWAYS carries bend: 1 in backOfMind from s11's dream shot to the end of s16 (also while hidden: show 0),
// so the resting left sleeve has one shape across the matched cuts s11→s12→s13 (bend changes it ~85 px).
// elbow is RAMPED with reach (elbow = 0.8 * reach): 0 at rest, so nothing changes until the hand moves.
const VOID_ARM_B  = { bend: 1 };                    // + elbow 0.8*reach: the sleeve comes down outside the cage's right bars
const UNLOCK_ANGLE = 2.3;                           // (±0.08 wobble OK) the hand enters the lock diagonally from the upper
                                                    // right and the sleeve clears the TIME-OUT sign
const PUSH_ANGLE = Math.PI - 0.55;                  // VOID_HANDS.push default angle cannot reach; this one can
const APPROACH_SHOULDER = [120, -40];               // Fear-local offset (× Fear scale) of the approach point: the hand
const APPROACH_PUSH     = [110, -10];               //   descends beside Fear, never over its head, then slides in (§1.5)
const SLEEVE_CLIP_Y = 1100;                         // world y (backOfMind): the second sleeve pass is clipped below this,
                                                    //   i.e. under the mantle and just above the cage top (y 1173)
// Fear points (backOfMind): cagePoint(name, ...CAGE_B, cageState)
//   occupant (430,1611) occupantFront (430,1630) occupantBack (430,1598) occupantSide (363,1619)
//   gripL (355,1453) gripR (505,1453) lockHang (510,1516) lock (510,1545) doorway (430,1642) outside (430,1697)
//   doorHandle: door 0 (510,1515) · 0.3 (467,1537) · 0.9 (255,1538) · 1 (229,1532)
// Front cage points: occupantFront (302,846) gripL (278,790) gripR (326,790) lockHang (327,810)
```

Scales: Fear **inside** the cage uses the cage scale (0.952 / 0.3); Fear **on the threshold** uses 0.97 (the
doorway's scale: it stands on the plinth lip; `hqScaleAt` at y 1648 would give 0.98 — keep 0.97, the hand recipes
are verified with it); Fear **outside** uses `hqScaleAt('backOfMind', y)` (outside 1.06, STOP 1.065); everything in `front` uses
`hqScaleAt('front', y)` except the Void (0.37) and the cage (0.3).

### 1.5 The Void's hand contacts — verified recipes (contact error 0.0 local units)

All three use `handL` (screen-left hand) and one layering scheme. Re-verified by the script supervisor
(`out/staging_check_final.png` cells 1–7; contact error 0.00 at every contact pose, incl. the ±0.08 unlock wobble,
crouch 1 / 0.3 and Fear's first push step). What changed from the director's first version, and why:
* **Two-pass sleeve instead of `defer:true` / sleeve-behind-the-cage.** `defer:true` + `drawVoidArm` draws the
  whole sleeve after the mantle, so its top lies OVER the cape (and pops there the moment `defer` switches on).
  `defer:'hand'` alone drew the sleeve behind the cage with the hand in front of it: the arm went through the bars.
  Now: `defer:'hand'` (drawVoid draws the sleeve under the mantle as usual), then after the cage's front layer a
  second sleeve pass clipped to world y ≥ SLEEVE_CLIP_Y puts the forearm in front of the cage, then the hand.
* **`bend: 1` on all three** keeps the sleeve outside the cage's right bars and off the TIME-OUT sign (the old
  unlock hold covered the sign's right half: "TIME" only). Ramp `elbow` with `reach`; keep `bend` constant (see §1.4).
* **Approach from the side.** The rest cuff hangs right above the cage (world ≈ (464,1096)), so a plain `reach`
  0→1 to Fear drags the hand straight down over Fear's head and face (it reads as grabbing its head). Shoulder and
  push: `reach` 0→1 to an APPROACH point beside Fear, then `settle` 0→1 slides the target in. Withdraw in reverse:
  `settle` 1→0 (the hand lifts off sideways), `reach` 1→0, `show` 1→0.

```js
const sleeveFront = (g, pose) => { g.save(); g.beginPath(); g.rect(-1e4, SLEEVE_CLIP_Y, 2e4, 2e4); g.clip();
  drawVoidArm(g, ...VOID_B, pose, 'L', 'sleeve'); g.restore(); };       // call under the same camera transform
```

**Unlock (s11b02)** — index fingertip on the staple; the sleeve passes right of the TIME-OUT sign and of Fear's face:
```js
const cst = { t, door: 0, locked: S.k(t, [...1→0 at the click]) };
const lockV = toVoidLocal(...VOID_B, ...cagePoint('lockHang', ...CAGE_B, cst));
const pose = { t, ...STARE_B, idle: 0, shadowSpread: 1, handL: { ...VOID_HANDS.unlock(lockV), ...VOID_ARM_B,
  elbow: 0.8 * reach, angle: UNLOCK_ANGLE + wobble, show, reach, point, defer: 'hand' } };
drawVoid → drawCage back → drawFear(occupantSide…) → drawCage front → sleeveFront → drawVoidHand(..,'L')
```
(With `angle 2.3` the hand only crosses the sign's right end on the way down and is clear of it from reach ≈ 0.6.)

**Hand on the shoulder (s13b04–s14b09)** — Fear at THRESH, any crouch 0…1, with `LOOK_FEAR` or `STARE_B`:
```js
const [fx, fy, fs] = THRESH;
const sh = [fx + 36 * fs, fy - (130 - 20 * crouch) * fs];          // Fear's near (right) shoulder
const ap = [sh[0] + APPROACH_SHOULDER[0] * fs, sh[1] + APPROACH_SHOULDER[1] * fs];
const tgt = [lerp(ap[0], sh[0], settle), lerp(ap[1], sh[1], settle)];
const pose = { t, ...LOOK_FEAR, cosmos, handL: { ...VOID_HANDS.shoulder(toVoidLocal(...VOID_B, ...tgt), -1),
  ...VOID_ARM_B, elbow: 0.8 * reach, show, reach, defer: 'hand' } };
drawVoid → drawCage back → drawCage front → sleeveFront → drawFear(THRESH) → drawVoidGlow → drawVoidHand(..,'L')
```

**Push (s16b02)** — Fear anywhere in x 360…440, y 1640…1710 (walking left, `facing −1`):
```js
const back = [fx + 34 * fs, fy - 112 * fs];                          // Fear's back = its right edge
const ap = [back[0] + APPROACH_PUSH[0] * fs, back[1] + APPROACH_PUSH[1] * fs];
const tgt = [lerp(ap[0], back[0], settle), lerp(ap[1], back[1], settle)];
const pose = { t, ...STARE_B, cosmos: COSMOS_RESIDUE, handL: { ...VOID_HANDS.push(toVoidLocal(...VOID_B, ...tgt), -1),
  ...VOID_ARM_B, elbow: 0.8 * reach, angle: PUSH_ANGLE, show, reach, defer: 'hand' } };
drawVoid → drawCage back → drawCage front → sleeveFront → drawVoidHand(..,'L') → drawFear   // hand BEHIND Fear
```
Nudge = move the target 8 local units left and back over 1 s. Never use `handR`, never move VOID_B / CAGE_B for a
shot — move the camera instead.

The CEO's hand on Fear's shoulder (s06) is the `alarm`-view recipe from hq.md (`ceoKneel` + `onShoulder` on
Fear's near shoulder `[fx − 36·fs, fy − (131 − 20·crouch)·fs]`, Fear `facing −1`), verified in
`staging_test_reference.png` cell 7 and at crouch 0 and 1 in `staging_check_alarm.png`.

### 1.6 The BACKDROP technique (Void behind the alarm-side two-shots, s04 / s06b06)

The `alarm` view has no Void in it; the `front` view has it but the characters are tiny there. For shots where
the screenplay wants the hood "out of focus" behind the CEO and Fear: draw the `front` set (+Void, +cage) with a
background camera, a dark haze, then the characters **in `alarm`-view coordinates** with a foreground camera.
```js
g.save(); applyCamera(g, BG); drawHQ(g,'front',st); drawVoid(g, ...VOID_F, {t, ...STARE_F, idle:0, shadow:false});
drawCage(g, ...CAGE_F, {t, door:1, locked:0}); drawHQForeground(g,'front',st); g.restore();
g.fillStyle = `rgba(13,11,28,${HAZE})`; g.fillRect(0,0,720,1280);              // "out of focus"
g.save(); applyCamera(g, FG);
drawAlarmStation(g, 692, 1089, 1.8, {t, alarm, alarmPulled});                  // the station travels with Fear
/* CEO at ceoKneel / ceoBeside, Fear at fearAtAlarm — exactly as in the alarm view */
drawHQForeground(g,'alarm',{...st, lightsDim:0});                              // low mist grounds their feet
g.restore();
```
| shot | BG cam | HAZE | FG cam |
|---|---|---|---|
| two-shot (s04b01-wide, s04b04) | {519, 552, 1.6} | 0.16 | {400, 950, 0.75} |
| close two-shot (s06b06) | {530, 520, 1.75} | 0.18 | {360, 940, 0.95} |
| CEO close, hood above-left (s04b02, s04b06) | {550, 477, 1.9} | 0.2 | {215, 640, 1.5} |

These keep the hood **upper-left, above/behind the CEO** (the Void is screen-left of the alarm corner) and keep the
front view's own little alarm station off-frame (no duplicate). Verified with exactly these numbers:
`staging_check_front.png` cells 7–9 (`staging_test_backdrop3.png` was rendered with older two-shot numbers; its
labels do not match this table). In the two-shots the empty open cage (CAGE_F) peeks in at the left frame edge
behind the CEO's knee at a tiny scale: keep it cropped there (never let a camera move bring it further in).

### 1.7 Deliberate deviations from the screenplay's literal wording

1. s02b01 "on the right wall, the FIRE ALARM and tiny FEAR": the establishing shot must show the screen, so it is
   the `back` view, where the alarm is off-frame **left**. Fear is introduced by the pan/cut in s02b02.
2. s02b03 "the door at right": the EXIT door is **screen-left** in the `front` view (its only on-screen view).
   The CEO's entrance moves left→right, into the red wash, toward the alarm.
3. Fear has no back view. "Fear's back to us" shots are restaged: s06b03 over-the-shoulder uses Fear's crown and
   tuft cropped by the frame bottom; s10b02/s11 Fear turns **left** (`facing −1`, its back to the Void on its right,
   face to us) and lifts its face UP to the glow; s12 "from behind Fear" = from its left-rear, Fear in 3/4 facing right.
4. s04 "the Void between them": the hood looms **upper-left, behind the CEO** (consistent with the alarm view,
   where the Void is screen-left of both).
5. s08b03 "walking away from the cage toward the console, facing camera" is a `front` view shot (the only view
   where walking toward the console means walking toward us).
6. s17b02/b05, s19b01 "the back of the mind out of frame": the hood is out of frame; the lower robe and the
   little cage may show at the top under the TOP SHADE (§5.9). The full Void returns in s19b02.
7. s19 contact gestures: Fear's neighbours at the console are ANGER (left) and SADNESS (right); JOY and CALM sit
   one seat away (the station order must not change). JOY's shoulder-bump becomes a lean-in past SADNESS with a
   beaming look; CALM's guiding finger becomes a point + nod at the next button; in s19b03 Fear leans its head on
   **SADNESS's** shoulder and CALM answers with the slow blink from its seat.
8. s18b01 "the hem of the cloak at the top edge": the cage stands in front of the robe, so the robe fills the
   background and its left sleeve cuff shows at the top edge.
9. s16→s17 screen direction: Fear leaves the back of the mind frame-LEFT and walks the alarm corridor left→RIGHT
   (each view's own "toward the front"). The reversal is bridged by a clean exit (s16 holds the empty frame for
   the last 0.5 s) and a clean entrance (s17 opens on the empty alarm wall for 0.3 s).
10. s12b02/b04 closes on Fear inside the cage: with the gate at 0.3 the door stiles (x 353/395/464) and the lock
   jamb (505) are spaced closer than Fear's eyes, so at least one bar always crosses an eye. These two lip-synced
   closes are "shot from inside the cage": draw the cage `layer:'back'` only (back bars behind Fear, no front
   bars). The wides and the side medium keep the full cage.
11. s08: the screenplay's "insert on the lock" + "hand still on the bars" are staged with the CEO KNEELING (the
   padlock is at the CEO's knee height; standing, the arm crossed Fear's face in the insert) and the hand sliding
   from the lock to the leftmost bar between the insert and the close (see §3 s08).

### 1.8 Reference renders (look at them)

`out/staging_test_reference.png` (the definitive layouts), `…_front_views.png`, `…_bom_act.png`,
`…_bom_act2.png`, `…_act3.png`, `…_reach_bom.png`, `…_unlock_zoom.png`, `…_shoulder_zoom.png`,
`…_void_heads_bom.png` (head poses), `…_backdrop3.png`, `…_back_room.png` (back view + REAL_ROOM + title),
`…_grades.png` (colour grades), `…_scenes_check.png`. Note: some early test sheets use the old cage x 270;
`reference`, `act3`, `bom_act2` and `backdrop3` show the final layout.
Script-supervisor checks (these supersede the test sheets where they differ): `out/staging_check_final.png`
(**the corrected recipes**: 1–2 unlock, 3–5 shoulder with approach, 6–7 push with approach, 8–9 s08 insert old vs
new, 10–12 s08b03, 13 s09 first frame, 14 s11→s12 and 15 s12→s13 matched cuts, 16 s12b02 inside-cage close,
17 s08b02 close); `out/staging_check_bom.png` (the director's ORIGINAL recipes: contact OK but the unlock sleeve
covers the sign and the shoulder/push hands come through the bars; cells 7–8 = s10 eyeline old vs new);
`out/staging_check_front.png` (cells 1 and 3–4 = the ORIGINAL s08b03/s09 blocking: cell 1 shows the CEO hiding
Fear; cells 5–6 s17b02/s19b03; 7–9 the three BACKDROP set-ups with §1.6's numbers; 10–11 s03 first / s05 last);
`out/staging_check_alarm.png` (s06 hand on the shoulder at crouch 0/1, s07 low angle, s05b01 with the CEO still
kneeling).

---------------------------------------------------------------------------------------------------------------

## 2. CONTINUITY TABLE

### 2.1 Master state track (value at the scene's first frame → last frame)

| sc | t | cage (occupant · door · locked · rust · dim) | alarm / pulled | emotions | Void head · cosmos · hands · idle | CEO | Fear |
|---|---|---|---|---|---|---|---|
| s01 | 0–17.0 | — | — | — | — | (SELF, sweater) | — |
| s02 | 17.0–35.77 | empty · 1 · 0 · 0 · 0 (only if in frame) | 0 → pull at s02b02+2.40 → 1/1 → bell winds down to 0 by s02b04+2.2; handle up when Fear points | at console. EXIT door: opens for the CEO (s02b03), swings shut again by s02b03+2.8 | STARE_F · 0 · hidden · 1 | enters by the door, ends **kneeling** (kneel 1) beside Fear | at the alarm, pointing past the CEO |
| s03 | 35.77–50.59 | empty · 1 · 0 · 0 · 0 | 0 / 0 | at console (out of frame) | STARE_F · 0 · hidden · **0** | kneeling at the alarm, back to us | first frame still pointing (facing 1) → shrinks against the station (crouch 0.6, facing −1), staring |
| s04 | 50.59–66.94 | empty · 1 · 0 · 0 · 0 | 0 / 0 | at console (out of frame) | STARE_F · 0 · hidden · 0 | kneeling at `ceoKneel` (no touch) | by the station |
| s05 | 66.94–79.31 | empty · 1 · 0 · 0 · 0 | pull at s05b01+0.25 → 1/1; fades 1→0 over s05b04; handle up at s05b04 | **evacuated** (b01–b02), door shut at s05b02.end+0.3 | STARE_F · 0 · hidden · 0 | still kneeling at s05 start (as s04 ended) → rises (b01) → alone centre (b03–b04) | slid down under the alarm |
| s06 | 79.31–105.42 | empty · 1 · 0 · 0 · 0 | 0/0 → pull at s06b08+0.6 → 1/1 | **back at the console** (they fade in with the dissolve: "one day"); leave again off-screen with the b08 alarm (sfx only) | STARE_F · 0 · hidden · 0 | kneels, hand on shoulder, ends kneeling, fist on knee | slumped → yanks alarm, hanging on it |
| s07 | 105.42–112.61 | empty · 1 · 0 · 0 · 0 | 1/1 → 0 over s07b01; handle up at s07b02+0.15 | gone (not in frame) | — (not in frame) | rises to standing | turns to face the CEO |
| s08 | 112.61–123.07 | empty · 1 · 0 → **Fear in · 0 · 1** (door shut s08b01+2.4, locked at **s08b02−0.2**, inside the insert) | 0 | gone | STARE_B → (b03 front) STARE_F · 0 · hidden · 0 | guides Fear, kneels, shuts + locks the gate, rises (b02), walks toward camera on the cage's LEFT (front) | caged, gripping the front bars |
| s09 | 123.07–132.6 | Fear · 0 · 1 · 0 · 0 | 0 | **filing back in** (door closing behind CALM, first 1.2 s) → at console (ANGER spread to x 315, SADNESS at the CEO's elbow 530) | STARE_F · 0 · hidden · 0 | from the left foreground (190,1170) → consoleMid, clipboard | in the cage (background) |
| s10 | 132.6–142.99 | Fear · 0 · 1 · 0 · 0 | 0 | (at console, not in frame) | STARE_B · 0 · hidden · 0 | (at console) | curled left side → back to the Void (`facing −1`), face up to the glow, gripping gripL |
| s11 | 142.99–157.79 | Fear · 0 → **0.3** · 1 → **0** · 0 · 0 | 0 | at console (b01) | STARE_B · 0 · **handL unlock** (b02) → hidden · 0 | at consoleBackMid, rubbing eyes (b01) | crying at gripL → frozen, looking up at the hood |
| s12 | 157.79–188.64 | Fear → empty · 0.3 → **0.9** · 0 · 0 · 0 | 0 | — | STARE_B · 0 · hidden · 0 | — | occupantSide (as s11 ended) → shuffles back to the back bars on screen → steps out → sits on THRESH (crouch 1) |
| s13 | 188.64–214.9 | empty · 0.9 · 0 · 0 · 0 | 0 | — | STARE_B → **LOOK_FEAR** · 0 · handL on shoulder from s13b04 · 0 | — | crouch 1 (as s12 ended) → stiffens to 0.8 → hides (1) → peeks → uncurls to 0.3, looks up |
| s14 | 214.9–256.84 | empty · 0.9 · 0 · 0 · 0 | 0 | — | LOOK_FEAR → STARE_B (b09) · **0 → 1 → 0.6** · hand lifts in b09 · 0.5 | — | wonder → stands, looks to the glow |
| s15 | 256.84–268.74 | (not in frame) | 0 | **look back, smile, back to work** | — (not in frame; no `voidEdge`, §1.3) | at consoleBackMid, clipboard + pen | at THRESH, clasped hands |
| s16 | 268.74–285.63 | empty · 0.9 · 0 · 0 · 0 | 0 | — | STARE_B · **0.5** · handL push (b02) → hidden · 0.5 | — | pushed → stops, looks back, smiles, leaves frame left (gone by S.end−0.5) |
| s17 | 285.63–296.77 | empty · 0.9 · 0 · 0 · 0 (tiny, top of frame) | 0 / 0 (Fear does NOT pull) | at console (ANGER 315, SADNESS 625 around the CEO) → ROW_S19 | STARE_F · 0.5 (hood out of frame) | at consoleMid → steps aside to CEO_ASIDE_F | enters the empty alarm wall at S.start+0.3, walks under the alarm → console → on the stool |
| s18 | 296.77–307.11 | empty · 0.93 → **1** · 0 · **1** · 0 (+flake) | 0 | — | STARE_B · (hood out of frame) · foldStar 1 in b03 | — | — |
| s19 | 307.11–322.81 | empty · 1 · 0 · 1 · **0.85** (barely visible) | 0 | at console, Fear among them | STARE_F · 0.5 (+ single star twinkle b03) · hidden · 0.5 | POV (not in frame) | on its stool between ANGER & SADNESS |
| s20 | 322.81–339.07 | — | — | — | (s20b04 star-hood in the window) | (SELF, sweater) | — |

Rust timeline: rust 0 through s17; **rust 1 from s18** (time has passed across the s18 dissolve); s19 dim 0.85.
The cage door is **never closed again after s11**. The Void's hands are visible ONLY in s11b02–b03 (unlock),
s13b04–s14b09 (shoulder) and s16b02–b03 (push).

### 2.2 First / last frame of every scene

Positions are world coordinates of the named view. "cam" = `{x, y, zoom}` for `applyCamera`.

**s01 · REAL_ROOM** — first: `REALROOM.cameras.opening` {420,655,1.12}; SELF at `selfSeated` (sweater), head
tilted down to the open notebook (`notebook` anchor, open 1, flat 1, rot −0.05), tender smile, eyes open (no
blink on frame 1); lamp 1, fairy 1, moon 1, dusk 0; TITLE fully opaque. Last (and the 0.9 s after S.end): extreme
close on SELF's lamp-side eye, lids closed, the frame filled by warm amber glow (#ffcf7a centre → #e59a4a edges).

**s02 · MIND_HQ** — first: `back` view cam {450,800,2.0} (the console's ridge lights fill the frame,
consoleGlow 1.35) under the dissolve; emotions at `consoleBack1..4`, backs to us; screenMode 'room'. Last: `alarm`
view {400,1040,1.3}; CEO kneeling at `ceoKneel` (CEO_AT_ALARM_F in front), head turning over the left shoulder;
Fear at `fearAtAlarm`, `facing 1`, one arm pointing up-left past the CEO; alarm 0, handle up; Void STARE_F;
the room already dimmed to s03's values (lightsDim 0.35, cold 0.35, warm 0, vignette 0.45 — §4.2).

**s03 · (front view)** — first: `front` {560,760,1.5}; CEO kneeling at CEO_AT_ALARM_F, `view:'back'` (the body
completes the turn begun on s02's last frame: match on action), clipboard at hip; Fear at FEAR_ALARM_F exactly as
s02 ended — `facing 1`, crouch 0, one arm still pointing up-left — then it lowers the arm and shrinks against the
station (crouch 0→0.6, `facing −1`) during s03b01; voidShadow 0.15 rising; lightsDim 0.35 / cold 0.35 (= s02's
last frame, §4.2). Last: `front` {450,277,8.5} inside the hood's darkness (the opening fills 70 % of the frame
width); Void STARE_F, idle 0, cosmos 0.

**s04** — first: `alarm` {560,1000,1.9}: Fear at `fearAtAlarm`, `facing −1`, eyes up-left at the hood. Last:
BACKDROP CEO close (bg {550,477,1.9}, fg {215,640,1.5}→1.6), CEO kneeling at `ceoKneel`, eyes up-left at the hood,
lips pressed. Alarm 0.

**s05** — first: `alarm` 'medium' {445,960,1.0}: Fear at `fearAtAlarm` lunging; CEO still **kneeling at `ceoKneel`**
(as s04 ended; s04→s05 is a cut with no time skip). Last: `front`
{500,860,1.3}: CEO alone at (450,1060, 0.5), hands lowered, staring at the empty console; Fear at FEAR_ALARM_F,
crouch 1 hugging itself (right edge); door 0; alarm 0; console empty.

**s06** — first: `front` {560,960,1.05} (dissolve: the emotions appear at their slots during it); CEO already
crossing at (560,1150, 0.583) toward Fear, clipboard left on the console; Fear slumped at FEAR_ALARM_F, crouch 1,
`armR` raised toward the handle. Last: `alarm` {230,770,1.9}: CEO kneeling at `ceoKneel`, hand a loose fist on the
knee, eyes on the floor, red pulse on; Fear (off-frame right) hanging on the handle, alarm 1 / pulled 1.

**s07** — first: `alarm` {420,860,0.8}: CEO kneeling at `ceoKneel` starting to rise; Fear at `fearAtAlarm` facing the
handle, peeking back; alarm 1. Last: `alarm` {520,1000,1.9}: Fear `facing −1` toward the CEO, hands dropped,
mouth open; alarm 0, handle up; CEO standing at `ceoKneel` x (off-frame left).

**s08** — first: `backOfMind` {440,1020,0.85}; cage CAGE_B empty, door 1, unlocked; CEO entering from frame-left
with Fear ahead of them (CEO's hands on its shoulders). Last: `front` {330,740,1.6}: CEO walking toward camera
on the cage's LEFT, leaving frame bottom-left at ≈(190,1170, 0.601); Fear in CAGE_F at occupantFront, gripping
gripL/gripR, sobbing; door 0, locked 1.

**s09** — first: `front` {400,1060,1.2}: door closing (0.6→0) behind CALM, CALM (120,1262,0.69) walking to slot 1;
CEO at (190,1170, 0.601) (= s08's last position) walking toward consoleMid; ANGER at x 315, SADNESS walking to
(530,1384), JOY at slot 4; cage (background, sx≈242) with Fear. Last: `front` close {470,1010,2.15}: CEO at
consoleMid, head low, lids heavy; SADNESS at (530,1384) with a hand on the CEO's sleeve.

**s10** — first: `backOfMind` {560,1000,0.9}; Fear curled at occupantSide (363,1619), crouch 1, `facing 1`,
peeking up-right at the hood; shadowSpread 0.4. Last: locked two-shot {545,958,0.8}: Fear `facing −1` at the left
bars (grips ['gripL']) looking UP at the glow (lookX −0.15, lookY −0.85), crying; shadowSpread 1.

**s11** — first: `back` {450,640,1.0}: CEO at consoleBackMid `view:'back'`, rubEyes, shrug 0.4, clipboard on the
console. Last: `backOfMind` low angle {560,900,0.8}: Fear inside at occupantSide turned `facing 1`, frozen,
looking up at the hood; door 0.3, lock open; hand withdrawn; Void STARE_B idle 0.

**s12** — first: `backOfMind` {560,900,0.8} (= s11's last frame; the shot continues across the cut): Fear at
occupantSide (363,1619) `facing 1`, frozen, looking up at the hood, then shuffles back to occupantBack (430,1598)
by s12b01+0.6. Last: wide {500,889,0.72}: Fear sitting on THRESH (crouch 1), looking down; door 0.9.

**s13** — first: `backOfMind` LOCKED wide {500,889,0.72} (= s12's last frame: the stillness runs on unbroken
across the cut; the turn starts inside the same frame): STARE_B, Fear on THRESH crouch 1. Last: {640,590,1.1}
on the bowed hood (LOOK_FEAR, darkness); the hand on Fear's shoulder; Fear (off-frame below) head tilted back.

**s14** — first: hood POV {679,336,4.5} (LOOK_FEAR face), pure darkness, cosmos 0. Last: over the Void's
shoulder {360,1200,1.3}: Void STARE_B, cosmos 0.6, hand hidden; Fear standing on THRESH `facing −1` looking at
the glow; starlight 0.5 on Fear.

**s15** — first: `back` 'wide' {450,800,0.8}: emotions already looking back (lookBack 1); CEO at consoleBackMid
`view:'back'`, clipboard, pen paused. Last: `back` {450,640,1.0}: everyone back at work (lookBack 0), JOY's button
lit; CEO nodding, pen moving.

**s16** — first: `backOfMind` {440,1420,1.8}: Fear on THRESH `facing −1`, wiping tears with the scarf end;
cosmos 0.5. Last: close {255,1470,2.8}, EMPTY for the last 0.5 s: Fear has skipped out of frame left from
FEAR_STOP_B (the way back to the HQ); only the robe and the starlight remain; Void STARE_B, hand hidden.

**s17** — first: `alarm` {380,960,1.0}: the EMPTY alarm wall (handle up, bell still, sticky note), alarm 0; Fear
enters from frame-left at S.start+0.3 at floor y 1406 (scale 1.8), `facing 1`. Last: `front` {450,1120,1.35}: Fear on its stool at `consoleFear` (450,1328) pressing its first button,
eyes lit; ROW_S19 positions; CEO at CEO_ASIDE_F smiling.

**s18** — first: `backOfMind` {420,1400,1.6}: CAGE_B rust 1, door 0.93, sign askew. Last: {400,1150,1.25}
(drifting up-left toward the glow), foldStar 1.

**s19** — first: `front` {420,1150,1.45}: ROW_S19, Fear at consoleFear, dawn. Last: `front` 'wide' {450,800,0.8}
with the warm screen-bloom rising from the bottom; Void STARE_F cosmos 0.5; cage barely visible.

**s20** — first: `REALROOM.cameras.desk` {424,760,1.5}: SELF at the desk, notebook open on the drawing, lamp 1.
Last: `REALROOM.cameras.opening` {420,655,1.12} — **the mirror of frame 1**: same camera and desk; lamp 0,
fairy 0.3, the title gone and the star-hood faded (only stars); notebook closed under SELF's palm; SELF looking up
toward the moon (upper-right), contented smile.

---------------------------------------------------------------------------------------------------------------

## 3. PER-SCENE SHOT PLAN

Times are beat anchors (absolute seconds in brackets for orientation; always key to anchors). "→" = camera move
over the given span, ease `inOut`/`sine` unless stated. Face-safe area: face centres x 72…648, y ≤ 1088 on screen.
Pans ≤ ~100 px/s on screen; prefer zoom-led moves. Camera life: `drift(t, 2–3)` on all shots except LOCKED ones.

### s01 · the_old_notebook · REAL_ROOM · 0–17.0 (first frame of the film)
| span | shot |
|---|---|
| 0 → s01b02+3.04 ('the first story') | **THUMBNAIL / OPENING** `REALROOM.cameras.opening` {420,655,1.12} → {420,655,1.142} (imperceptible push, ends at the cut). SELF `selfSeated` per the self.md opening recipe but looking DOWN at the open, flat notebook (`notebook` anchor, open 1, flat 1, rot −0.05): headTilt 0.17, lookY 0.6, lids ≈0.4, tender one-corner smile. Right fingertip on the crayon Fear; at +1.3 it slides to the hood. Frame 1: eyes open (`noAutoBlink` until 0.8 s), slow blink at 0.8 s. Lamp 1, fairy 1, moon 1, dusk 0. Vignette 0.25. TITLE: see below. |
| s01b02+3.04 → s01b03 | **INSERT (OTS)** — screen-space: the room behind at `REALROOM.cameras.desk` with an overlay rgba(20,10,4,0.35); `drawNotebook(g, 184, 690, 1.6, {open:1, flat:0.15, rot:-0.03})` so the RIGHT page (crayon drawing + "Why does it just stand there??") is centred at x≈360; push 1.00 → 1.04. SELF's sleeve/hand may enter from the bottom-left (drawSelf `seated`, `layer:'front'`, body off-frame) smoothing the page corner. paper_rustle. |
| s01b03 → S.end+0.9 | **EYE PUSH** cut to `REALROOM.cameras.face` {424,680,2.2}, then push exponentially into SELF's lamp-side (screen-left) eye (centre from `selfPoseAnchors(...).eyes` minus half the eye spacing): zoom 2.2 → 9 by s01b03+4.72 ('mind'), → 14 by S.end+0.9. Lids close on 'mind'. From s01b03+3.6 an amber radial glow centred on the iris grows to fill the frame (screen comp. then source-over; #ffe2a8 → #ffb35c → #c26a28); fully amber by S.end−0.3 and held through the dissolve. |

**TITLE (first frame):** text "The Void" / "and My Fear", font **Caveat 60 px in world units** (≈67 px on screen),
fill **#fff3d6**, shadow rgba(10,12,40,0.85) blur 14, `textAlign:'center'`, `textBaseline:'middle'`, drawn under
the camera at **x 432, y 203** and **x 432, y 282** (centre of `REALROOM.titleBox` {266,132,332,214}, the clean
upper window pane; on screen ≈ y 134 and 222). Opaque from frame 1; alpha 1 → 0 over s01b02 → s01b02+1.5 (sine);
gone before the cut. Composition check: title upper third, face middle third (y≈668), notebook lower third above
y 1088 — `staging_test_back_room.png` cell 5.

### s02 · headquarters_and_alarm · 17.0–35.77 (dissolve in)
| span | view · cam | staging |
|---|---|---|
| S.start → s02b01.end | `back` {450,800,2.0} → 'screen' {450,640,1.0} (cubic) | Under the dissolve the ridge lights match s01's amber; consoleGlow 1.35 → 1.0. JOY/SADNESS/ANGER/CALM at `consoleBack1..4`, `view:'back'`, small `dy` taps, per-character time offsets. No Void, no cage in this view. |
| s02b02 → +1.0 | `back` pan {450,640,1.0} → {330,700,1.12} | Toward the alarm wall (left). |
| s02b02+1.0 → s02b02.end−0.4 | `alarm` 'pull' {630,1000,1.45} | Fear at `fearAtAlarm`, `facing 1`, head turned back up-left (the Void) while reaching blindly: `armR {target:[108, −176+26·pulled], bend 1, hand 'grip', front}`. **Pull on 'alarm' (s02b02+2.40)**: alarmPulled 0→1 / 0.25 s, alarm 0→1 / 0.3 s. Eyes squeeze shut. |
| s02b02.end−0.4 → s02b03 | `back` 'console' {450,760,1.5} → {450,740,1.45} | Red wash from the left (drawAlarmLight 'back'); screen blends to 'alarm' (`screenModeB:'alarm', screenBlend: 0.6·alarm`). Reactions per screenplay (CALM's hand to "the evacuation lever" = its right lever). |
| s02b03 → +4.70 ('looking') | `front` 'door' {215,820,1.7} → {260,840,1.6} | doorOpen 0→1 over 0.8 s, then 1→0 over s02b03+2.0 → +2.8 (it swings shut behind the CEO; s05 needs it shut). CEO steps in from `exitDoor` (184,936) walking **screen-right** (`facing 1`, walk ≈0.85 cycles/s, scale = hqScaleAt) to (400,1000,0.444) with one stop to tug the lapels, clipboard hugged. The front red wash is on the right: they walk into it. |
| +4.70 → s02b04 | `front` {430,900,1.25} → {640,900,1.6} | Camera drifts right with the CEO's gaze (console → alarm). JOY (slot 4) turns toward the door (headTurn −0.6) and shrugs; ANGER points up-right at Fear (behind him). CEO walks on (≈1.1 cycles/s) to **CEO_AT_ALARM_F** and goes down on one knee there (kneel 0→1 over s02b03.end−0.8 → s02b03.end; the alarm two-shot that follows needs kneel 1 — a half crouch here would jump on the cut). Fear at FEAR_ALARM_F hanging on the handle, glancing up-left again and again. |
| s02b04 → S.end | `alarm` 'twoShot' {430,1065,1.2} → push {400,1040,1.3} in the pause | CEO at `ceoKneel` (kneel 1). Fear at `fearAtAlarm`, hand on the handle; alarm 1→0 by s02b04+2.2 (bell winds down). As the bell dies the room dims and cools to s03's values (s02b04+2.2 → S.end, §4.2). At s02b04.end+0.2 Fear lets go (alarmPulled 1→0) and points up-left past the CEO's shoulder. **Cut on the CEO's head turn**: headTurn → −0.7 over S.end−0.8 → S.end. |

### s03 · the_void · 35.77–50.59 · `front` view
| span | cam | staging |
|---|---|---|
| S.start → s03b02 | {560,760,1.5} → {470,520,1.5} (inOut) | Tilt from the floor to the hood. voidShadow 0.15 → 0.7 (S.start → s03b02−0.6): the shadow spills toward camera. CEO small at the bottom: CEO_AT_ALARM_F, kneel 1, `view:'back'`, headTurn −0.25, head tipping back; clipboard lowered to the hip. Fear at FEAR_ALARM_F: starts as s02 ended (`facing 1`, arm pointing), lowers the arm and shrinks against the station (crouch 0→0.6, `facing −1` by s03b02−0.5), eyes up-left. Void STARE_F, **idle 0**. One 2-px soft mote drifts across the hood and vanishes into it (s03b01+1.5 → +3.0). |
| s03b02 → s03b03 | **LOCKED** {560,690,1.25} | Nothing moves (Void idle 0, no blinks on CEO or Fear for the beat; CEO leans back half an inch, a hand to the floor). No drift. |
| s03b03 → S.end | {450,400,1.6} → {450,277,8.5} (exponential zoom, sine) | Push into the STARE_F hood until the opening fills ≈70 % of the frame width (opening half-width 80 × 0.37 = 29.6 world px → zoom 8.5; the old 7.0 gives 57 %). Darkness only. |

### s04 · not_safe · 50.59–66.94 · `alarm` closes + BACKDROP (§1.6)
| span | shot |
|---|---|
| S.start → s04b01.end+0.3 | `alarm` close on Fear {560,1000,1.9} → 2.0: Fear `facing −1`, pressed against the wall left of the station, eyes up-left on the hood (optional: a tiny dark hood shape in each iris). |
| → s04b02 | BACKDROP two-shot (bg {519,552,1.6}, haze 0.16, fg {400,950,0.75}): CEO at `ceoKneel` an arm's length from Fear, not touching; the hand starts toward Fear and returns to the knee. Hood upper-left above the CEO. |
| s04b02 → s04b03 | BACKDROP CEO close (bg {550,477,1.9}, haze 0.2, fg {215,640,1.5}): half-smile; quick glance **up-left** at the hood mid-line. |
| s04b03 → s04b04 | `alarm` close on Fear {560,1000,1.95}: first look at the CEO (left, flatter), back up-left to the hood on 'not safe'. |
| s04b04 → s04b05 | BACKDROP two-shot tighter (bg {530,520,1.75}, haze 0.18, fg {360,940,0.95}); CEO's eye-flick up-left on 'Nothing'. |
| s04b05 → s04b06 | `alarm` close on Fear {560,1000,2.0}. |
| s04b06 → S.end | BACKDROP CEO close, fg zoom 1.5 → 1.6 (slow push); the hood looms behind/above-left; eyes drift up-left and stay. |

### s05 · chaos · 66.94–79.31
| span | view · cam | staging |
|---|---|---|
| S.start → s05b01+1.3 | `alarm` 'medium' {445,960,1.0} | Fear lunges and yanks at s05b01+0.25 (alarmPulled 0→1 / 0.25 s; alarm 0→1 / 0.3 s), spins and scurries **right** (toward the console), out of frame by +1.3. CEO still kneeling at `ceoKneel` (as s04 ended — not `ceoBeside`, that would teleport them across the cut) reaches out too late (armR 'reachOut' at +0.8, silent 'wait'), starts to rise (kneel 1→0.4, +0.9 → +1.3). Verified: `staging_check_alarm.png` cell 4. |
| s05b01+1.3 → s05b02 | `front` 'console' {450,1120,1.35} | Fear behind the console row on tiptoe (y 1350, scale 0.8), scurrying right→left shooing; emotions in PANIC_FACE leave their slots moving **left** (toward the door side). CEO in the background at CEO_AT_ALARM_F finishing the rise (kneel 0.4→0), turning to watch them. doorOpen 0→1 from s05b01+1.5 (door_whoosh). (The CEO walks to the room's centre off-screen during s05b02.) |
| s05b02 → s05b03 | `front` 'door' {215,820,1.7} | CALM guiding SADNESS already in the doorway (`exitDoor`, fading alpha); ANGER at the threshold glancing back right; JOY last in the doorway (≈(200,930,0.38)), red tint on her right cheek, speaks, goes (alpha 1→0 / 0.3 s at s05b02.end+0.2). doorOpen 1→0 over 0.6 s from s05b02.end+0.3. |
| s05b03 → s05b04 | `front` 'establish' {450,800,0.9} | Empty console. CEO alone at (450,1060,0.5), clipboard hanging (armL 'rest' + clipboard), slow half-circle (bodyTurn −0.4 → 0.4). Fear at FEAR_ALARM_F clinging (pulled 1). Alarm 1, red on the right wall. A few small pages drift down near the console (optional). |
| s05b04 → S.end | {450,800,0.9} → {500,860,1.3} | alarm 1→0 over s05b04 → s05b04.end (silence rushes in after 'chaos.' at +0.54). CEO's palms to the ears (raw arm targets), eyes shut, then hands lower, shoulders sag. Fear slides down the wall (crouch 0→1), lets go (pulled 1→0), hugs itself at the right edge (sx≈664), eyes up-left on the Void. |

### s06 · a_hand_on_the_shoulder · 79.31–105.42 (dissolve in = "one day")
| span | view · cam | staging |
|---|---|---|
| S.start → s06b01+2.28 ('hand') | `front` {560,960,1.05} | The emotions are at their slots when the dissolve resolves (= they came back). Clipboard lying on the console. CEO already crossing from (560,1150,0.583) up-right to CEO_AT_ALARM_F and kneels (kneel 0→1 / 0.8 s ending at 'hand'). Fear at FEAR_ALARM_F crouch 1 (slumped), armR raised toward the handle. JOY (slot 4) glances back over her right shoulder toward Fear (Fear is behind and above her in this view: headTurn 0.5, lookX 0.6, lookY −0.5), smile fading, finger hovering. Red light off. |
| → s06b02 | `alarm` 'twoShot' {430,1065,1.2} | CEO at `ceoKneel`, hand hovers then settles on 'shoulder' (s06b01+3.96): onShoulder target [fx − 36·fs, fy − (131 − 20·crouch)·fs]. Fear `facing −1` (toward the CEO), flinch at the touch. |
| s06b02 → s06b03 | `alarm` {440,1180,2.4} → {250,780,1.7} | Insert on the hand on the shoulder (`shake` 0.4 on the CEO's hand), tilt up to the CEO's face. |
| s06b03 → s06b04 | `alarm` OTS {260,800,1.6} → {250,780,1.75} | CEO face centre-left. **Foreground Fear crown**: screen-space `drawFear(g, 600, 1940, 3.0, {facing:-1, …})` — only the crown and tuft show at the bottom-right (eyes below the frame); tuft droops on 'stop' (s06b03+0.52). |
| s06b04 → s06b06 | `alarm` close on Fear {520,1000,2.0} → 2.1 | Over the CEO's shoulder (the CEO's arm/hand at the left). |
| s06b06 → s06b07 | BACKDROP close two-shot (bg {530,520,1.75}, haze 0.18, fg {360,940,0.95}) | Very still; the Void far behind, upper-left. Fear's eyes slide up-left to it; tiny head shake. |
| s06b07 → s06b08 | `alarm` close on Fear {520,1000,2.0} | CEO's shoulder soft at the left. |
| s06b08 → s06b09 | `alarm` 'twoShot' {430,1065,1.2} | Fear twists out (`facing −1 → 1`), yanks at s06b08+0.6 (pulled 0→1, alarm 0→1 / 0.3 s). CEO's hand left in the air → loose fist → knee. |
| s06b09 → S.end | `alarm` close on CEO {230,770,1.9} | Red pulse on the face. Off-screen: the emotions leave again (sfx crowd_murmur −24 dB, door_whoosh −22 dB at s06b09+0.5; owned by s06). |

### s07 · time_out · 105.42–112.61 · `alarm` view
| span | cam | staging |
|---|---|---|
| S.start → s07b02 | {420,860,0.8} (low, locked-ish) | CEO rises from `ceoKneel` (kneel 1→0 over s07b01 → +1.2) and stands there (scale 2.091), tugs the blazer, chin up, eyes wet. Fear at `fearAtAlarm` clinging (pulled 1), peeking back. alarm 1→0 over S.start → s07b02. |
| s07b02 → s07b03 | close on Fear {520,1000,1.9} | Fear turns fully around (`facing 1 → −1` in ≈0.3 s), hands off the handle (pulled 1→0 at s07b02+0.15), tuft rigid. |
| s07b03 → s07b03.end | close on CEO {190,560,1.4} | Standing, looking down-right at Fear; eyes flick down on 'time-out'. |
| s07b03.end → S.end | close on Fear {520,1000,1.9} | Reaction (mouth open, head shake, palms up then drop). |

### s08 · the_cage · 112.61–123.07
| span | view · cam | staging |
|---|---|---|
| S.start → s08b01+2.2 | `backOfMind` {440,1020,0.85} (the hood towers out of the top) | Void STARE_B idle 0, shadowSpread 0.7. Fear walks in from frame-left (60,1712) → doorway (430,1642) by +1.4 → occupantFront (430,1630) by +1.7, head craned up-right at the Void; turns to camera and grips gripL/gripR (+2.0; the jamb bars, which do not move with the door). CEO behind it, hands on its shoulders, from (−40,1735) to CEO_B_DOOR (300,1730) by +1.2; lets go as Fear steps in and goes down on one knee (kneel 0→1, +1.2 → +1.8, `facing 1`; the front foot lands at x≈394, in front of the plinth); swings the gate shut from the knee: door 1→0 over +1.8 ('cage') → +2.4, the hand on the hasp (`cagePoint('doorHandle', …, {door})`, all within reach of the kneeling CEO; pass door 0.5–0.65 quickly). |
| s08b01+2.2 → s08b02 | `backOfMind` INSERT {505,1540,3.2} | The padlock. The gate's free edge swings into the insert and shuts at +2.4 (cage_close). Only the CEO's hand + forearm (CEO still kneeling at CEO_B_DOOR; its head is at x≈332, left of the insert frame; armR `reachOut` with a `selfLocal` target, `hand:'grip'`): the hand drops from the hasp to the padlock, a tiny gold key (local helper) in the fingers: hesitate +2.5 → s08b02−0.6, turn s08b02−0.6 → s08b02−0.2 (key_turn); **locked 0→1 at s08b02−0.2** (lock_click) — inside the insert (the old `s08b01.end+1.3` fell 0.1 s after the cut). The fingers leave the key and slide left along the door's middle rail out of frame (s08b02−0.15 → s08b02). Kneeling, the forearm passes under Fear's chin (the CEO's raised knee may show at the bottom-left: fine); standing, the sleeve crossed Fear's face — `staging_check_final.png` cell 8 (old) vs 9 (new). |
| s08b02 → s08b03 | `backOfMind` close {430,1430,2.2} | Fear at occupantFront, face between two bars (cage `grips:['gripL','gripR']`), a tear spills, then another; eyes roll up-right to the Void on 'with it' (+1.50 'with' → +1.74 'it'). The CEO's hand on the leftmost bar at the left frame edge (CEO at CEO_B_BARS (140,1735), kneeling, body and head off-frame; target ≈ (282,1490); the CEO shuffled back-left from CEO_B_DOOR while its hand trailed out of the insert); the CEO stands up during the line (kneel 1→0, +0.1 → +0.9) so the hand slides UP the bar to ≈(282,1440) — Fear's "Please don't leave me" answers that movement; the hand tightens on 'leave' (+1.10) and lets go at s08b02.end. |
| s08b03 → S.end | `front` {330,740,1.6} | Two planes, side by side: Fear in CAGE_F at occupantFront facing us, gripping the front bars, shake 0.6 pulses (cage_creak), sobbing; Void STARE_F idle 0 above (hood out of the top). The CEO starts on the cage's LEFT (as in the back of the mind), standing at (215,912, 0.362) `view:'back'`, hand on the cage's left bars; takes it off and turns to camera (+0 → +0.5); two steps toward camera to (210,1040, 0.481) by +1.2, stops (+1.2 → +2.6: in-breath, wet eyes, clenched hands; flinches at each rattle; face at screen x≈168, Fear's face at ≈315 — never overlapping), walks on toward camera and leaves frame bottom-left at ≈(190,1170, 0.601) by S.end. (The old start (330,900) put the CEO's back exactly over Fear and the cage; the old path to (430,1200) crossed in front of Fear's face.) Verified: `staging_check_final.png` cells 10–12 (and cell 13 for s09's first frame). |

### s09 · responsible · 123.07–132.6 · `front`
| span | cam | staging |
|---|---|---|
| S.start → s09b02 | {400,1060,1.2} → {420,1060,1.3} | **The emotions are back:** the door (left edge) swinging shut 0.6→0 over S.start → +1.0 behind CALM, who finishes its walk from (120,1262,0.69) to slot 1 (165,1384) by +1.2; ANGER at x 315 (slot 2 spread −40 for the CEO at consoleMid, as hq.md asks and as in s17), JOY (slot 4) in place; SADNESS walks from slot 3 to the CEO's elbow (530,1384). CEO enters from the left foreground at (190,1170,0.601) (= s08's exit point; it is behind CALM in depth, their paths diverge) → consoleMid by +1.6 (back to the cage), picks up the clipboard (+2.0), stares at it. The cage with Fear is visible small in the background (sx≈242, sy≈383). |
| s09b02 → S.end | close {480,1020,2.0} → {470,1010,2.15} | CEO face (450,994); SADNESS face lower-right. Hand to the mouth, single tear on 'sadness' (+0.64). |

### s10 · stone_faced · 132.6–142.99 (dissolve in) · `backOfMind`
| span | cam | staging |
|---|---|---|
| S.start → s10b02 | {560,1000,0.9} → wide {500,889,0.72} (sine, very slow) | shadowSpread 0.4 → 1.0 (ease out) as the frame widens. Void STARE_B idle 0. Fear curled at occupantSide (363,1619), crouch 1, `facing 1`, peeking up-right at the hood, hiccups. Lavender Fear = the only warm colour near the Void. |
| s10b02 → S.end | **LOCKED** two-shot {545,958,0.8} | Hood at the top (sy≈79), cage at the bottom. Fear watches the hood (one blink), then turns around in place (`facing 1 → −1` at s10b02+1.2), grips gripL with both hands (cage `grips:['gripL']`), face lifted UP toward the glow (head tilted back, lookX −0.15, lookY −0.85: the glow is straight above the cage on screen), tears spill. Only Fear moves. |

### s11 · the_unlocking · 142.99–157.79
| span | view · cam | staging |
|---|---|---|
| S.start → s11b01+3.44 ('image') | `back` {450,640,1.0} → {450,700,1.2} | CEO at consoleBackMid `view:'back'`, rubEyes both arms, shrug 0.4, clipboard on the console. JOY lookBack 0.35 lookSide +1 (at the CEO) then back; SADNESS lookBack 0.6 lookSide +1 (toward the cage, which is behind the camera, right of centre — the same side SADNESS uses to look at Fear-at-the-cage in s15) then down; ANGER works a lever; CALM lookBack 0.3 lookSide −1 then back. |
| 'image' → +1.2 | scene-internal crossfade (render both, blend) | into the dream. |
| → s11b02 | `backOfMind` {490,1250,1.3} | **Dream look**: cold 0.5 + warm 0.15, vignette 0.45 in '#2a1408'. Fear at occupantSide `facing −1`, gripL, forehead between two bars, eyes squeezed, crying; Void STARE_B idle 0, shadowSpread 1; handL carries VOID_ARM_B (`bend:1`, show 0) from this shot's first frame on — and keeps it through s16 (§1.4) — so the resting sleeve never changes shape mid-shot or across the matched cuts. (Nudge Fear's x ±8 px so no bar crosses an eye.) |
| s11b02 → s11b03 | {490,1250,1.3} → {490,1300,1.4} | **The unlock** (§1.5): show 0→1 (s11b02 → +1.2, out of the sleeve), reach 0→1 (+0.4 → +3.4, inOut), point 0→1 (+2.6 → +3.4); the hand descends in front of the TIME-OUT sign's right end (reach ≈0.2–0.5) and is clear of it from reach ≈0.6, entering the lock diagonally from the upper right; locked 1→0 at +3.8 (lock_click) with shake 0.15 → 0 over 0.4 s, angle 2.3 ± 0.08 wobble for "turns" (+3.4 → +3.9). Hood never moves. |
| s11b03 → +1.4 | close on Fear {400,1420,2.2} | door 0→0.3 over s11b03 → +2.0 (outCubic, cage_creak; the gate's free edge sweeps past Fear's face as it opens — let it pass, but do not stop it on an eye: re-nudge Fear's x once the gate settles). The sob stops, eyes snap open, a tear hangs; head turns to the gate. |
| +1.4 → S.end | {400,1420,2.2} → low angle {560,900,0.8} | Eyes travel up the withdrawing hand (reach 1→0 over +0.8 → +2.8, show 1→0 +2.8 → +3.4; `bend:1` stays on), up the cloak, to the hood; the body turns `facing 1` (+2.0). Frozen; the hanging tear falls at S.end−0.5. The dream grade eases back to s12's values (cold 0.6, warm 0, vignette 0.5 black) over this span, so the s11→s12 cut matches (§4.2). |

### s12 · why_are_you_doing_this · 157.79–188.64 · `backOfMind`
Void: STARE_B, idle 0, cosmos 0, shadowSpread 1, handL `{ bend: 1, show: 0 }` (§1.4) for the whole scene — it never moves.

| span | cam | staging |
|---|---|---|
| S.start → s12b02 | low angle {560,900,0.8} (= s11's last frame) → {560,940,0.8} | Fear starts exactly where s11 left it (occupantSide, `facing 1`, frozen) and shuffles backward on screen to occupantBack (430,1598) by s12b01+0.6 (two small steps, eyes never leaving the hood), pressed to the far bars, chin up at the hood (up-right) on 'this' (+0.90). (Starting at occupantBack on {560,980} made a jump cut: near-identical framing, Fear teleported 70 px.) |
| s12b02 → s12b03 | close {440,1400,2.2}, **inside-cage cheat**: cage `layer:'back'` only (§1.7-10) | Fear's face (≈(430,1402)); back bars and the dark robe behind. With the full cage the gate's free edge (x 464) and centre stile (395) cross both eyes. |
| s12b03 → s12b04 | side medium {470,1300,1.3} | Fear, the gate ajar (0.3), the dark fold above (the Void's left sleeve). Full cage here (the gate must read); the mouth stays clear of the rails (middle rail y≈1516 is below it). |
| s12b04 → s12b05 | close {440,1400,2.2}, inside-cage cheat as b02 | |
| s12b05 → s12b06 | **LOCKED** wide {500,889,0.72} | Near-profile STARE_B, tiny Fear. |
| s12b06 → s12b07 | medium {450,1380,1.6} | Fear steps to occupantFront (+1.0) and grips the door's free edge (doorHandle at door 0.3 = (467,1537)) at +1.4. |
| s12b07 → s12b08 | low angle from Fear's left-rear {560,980,0.8} | Fear pushes the door (0.3 → 0.9 over +0 → +0.6) and steps out onto THRESH (440,1648,0.97) by +1.0, `facing 1`; tiny stamp on 'hurt' (+0.96). |
| s12b08 → s12b09 | close from above {450,1430,2.0} | Neck craned straight up; the dark robe edges the top. |
| s12b09 → s12b10 | {450,1430,2.0} → 2.15 | Fear sinks down on THRESH (crouch 0→1 around 'forever' +1.68). |
| s12b10 → S.end | **LOCKED** wide {500,889,0.72} | The longest stillness. |

### s13 · the_turn · 188.64–214.9 · `backOfMind` (handL `bend:1` throughout, §1.4)
| span | cam | staging |
|---|---|---|
| S.start → s13b02 | **LOCKED** wide {500,889,0.72} (= s12's last frame, so the cut is invisible and the stillness runs on; the old {560,900,0.78} was a jump cut from a near-identical wide) | **THE TURN** (idle 0): headTurn −0.65 → −0.3 and headDown 0.12 → 0.3 over s13b01 → +3.8 (sine; "almost imperceptible"), then headDown 0.3 → 0.8 over +3.8 → +5.0. Cosmos 0. Fear on THRESH: crouch 1 as s12 ended; the instant the turn starts it stiffens (crouch 1 → 0.8 over s13b01+0.1 → +0.4; face ≈ sy 1054), tremble 0 (frozen). |
| s13b02 → s13b03 | ECU on Fear's eyes {440,1450,5.0} | Inner voice, lips still. |
| s13b03 → s13b04 | high angle (hood POV) {450,1560,1.6} | Fear hides its head in its hands (crouch 1, handsOnFace), tremble 0.9. Hold through the silence. |
| s13b04 → s13b05 | side close {470,1480,2.0} | **The hand** (§1.5 shoulder, LOOK_FEAR; handL has carried `bend:1` since s11): show 0→1 (s13b04 → +0.8), reach 0→1 to the APPROACH point beside Fear (+0.4 → +2.0: it descends into frame top-right, outside the cage's right bars, never over Fear's head), settle 0→1 (+2.0 → +2.7: the fingertips slide in over the shoulder, 'hand' +2.32), contact at +2.7; flinch at +2.75; at rest by 'shoulder' (+3.12). |
| s13b05 → s13b06 | hold close {460,1470,2.2} | Tremble 0.9 → 0 over 2 s; one eye peeks (armL 'peek'), hands lower, gaze travels up the arm. From +2.0 Fear uncurls: crouch 1 → 0.3 by s13b06+1.0 (the shoulder target follows crouch, contact stays exact) — s14b05 picks it up at crouch 0.3. |
| s13b06 → S.end | tilt {450,1450,2.0} → {640,590,1.1} | From the upturned face to the bowed hood (LOOK_FEAR face (679,336)); 'face' at +1.98. Darkness. |

### s14 · the_universe_inside · 214.9–256.84
| span | shot |
|---|---|
| S.start → s14b02+0.5 | Fear's POV into the hood: `backOfMind` {679,336,4.5} → {679,336,7.0}, LOOK_FEAR, hand still on the shoulder (off-frame). Cosmos per §4.3 (first star at s14b01+0.8). Grade starts at s13's values (cold 0.65, vignette 0.55) and eases to cold 0.3 / vignette 0.4 as the stars kindle (s14b01 → s14b02.end): the first light is the cosmos itself. |
| s14b02−0.5 → s14b05 | crossfade (1.0 s) to full-screen `drawCosmos(g, 360, 640, 380, 660, t, {reveal, seed:7, glyphs:1})`; drift by translating the rect ≈0.3 px/frame and scaling 1.00 → 1.06 over b02–b04 (b04: glyphs; 'meaning' at +2.72). |
| s14b05 → s14b06 | reverse: close on Fear `backOfMind` {450,1430,3.0}: THRESH, crouch 0.3, headTilt −0.15, headTurn 0.25, lookX 0.35, lookY −1, sparkle 1, tears; starlight k 1 (§5.4) + drawVoidGlow (glow 1.2). |
| s14b06 → s14b07 | pull-back {450,1430,3.0} → {560,1000,0.85} (exponential): the two-shot from the side, the starry hood bowed above (top), the hand on the shoulder. |
| s14b07 → s14b09 | close on Fear {450,1430,3.0}. |
| s14b09 → s14b10 | two-shot {560,1000,0.85}: hand lifts (settle 1→0 over s14b09 → +0.6: off the shoulder, up and to the right; reach 1→0 +0.5 → +1.8; show 1→0 +1.8 → +2.3; the sleeve stays outside the cage's right bars; keep `bend:1` on handL (show 0) — dropping it would re-shape the resting sleeve on screen); Fear leans after it; hood LOOK_FEAR → STARE_B over +1.4 → +3.4. |
| s14b10 → S.end | over the Void's shoulder {360,1200,1.3}: the glow top-centre, the Void's left sleeve/robe at the right edge; Fear stands up on THRESH, `facing −1`, turns to look at the glow ('screen' +1.78): head tilts back, eyes UP (lookX −0.2, lookY −0.8; on screen the glow is above Fear, slightly left), narrow, then widen. |

### s15 · looking_back · 256.84–268.74
| span | shot |
|---|---|
| S.start → s15b01+1.9 | Fear's POV: `back` 'wide' {450,800,0.8} → {450,760,0.9}; no Void flank (see §1.3). Emotions already turned: lookBack 1, lookSide JOY/SADNESS +1, ANGER/CALM −1, faces per screenplay; CEO at consoleBackMid `view:'back'`, clipboard + pen paused, headTurn 0 → 0.2 (heard something; doesn't look). Screen 'room', bright. |
| +1.9 → s15b02 | reverse: `backOfMind` close {440,1430,3.0}: Fear on THRESH `facing −1`, hands clasped at the scarf (FEAR_ARMS `wringHands`; Fear has no `clasp` preset), lookX −0.2, lookY −0.8 (the emotions = the glow, up); starlight k 0.5 on its right cheek. |
| s15b02 → s15b03 | `back` 'console' drift {320,760,1.35} → {580,760,1.35} (until s15b03+0.6): JOY → SADNESS → ANGER → CALM, one smile each as the camera passes. |
| s15b03 → +2.76 ('then') | `backOfMind` close on Fear {440,1430,3.0}: wobbly smile; eyes fill. |
| +2.76 → S.end | `back` 'screen' {450,640,1.0}: lookBack 1→0 staggered 0.15–0.3 s (JOY last); JOY presses (consolePress {0:1}); CALM eases a lever; ANGER nudges the CEO and points at the screen; CEO nods, pen moving. |

### s16 · the_gentle_push · 268.74–285.63 · `backOfMind` (cosmos COSMOS_RESIDUE, STARE_B, handL `bend:1` from S.start)
| span | cam | staging |
|---|---|---|
| S.start → s16b02 | medium {440,1420,1.8} | Fear on THRESH `facing −1`, wipes one eye then the other with the scarf end (armL/armR 'wipeEye'), big sniff. Robe behind; hood out of frame. |
| s16b02 → s16b03 | side view {420,1330,1.25} | **The push** (§1.5, with the approach): show 0→1 (s16b02−0.2 → +0.4), reach 0→1 to APPROACH_PUSH (+0 → +1.2: the hand comes down to the right of the cage, behind Fear, never over its head), settle 0→1 (+1.2 → +1.8: two fingertips meet Fear's back); nudge on 'push' (+1.94): target 8 units left and back over 1 s. Fear tips forward one step (to (390,1665,1.01) at +2.0, arms out), a second on its own (to (330,1680,1.035) at +2.8). The open hand stays where Fear's back was; withdraws s16b03+1.0 → +2.2 (settle 1→0 then reach 1→0, show 1→0). |
| s16b03 → +3.0 | front medium {300,1300,1.25} | Fear walks on to FEAR_STOP_B (by +1.0), stops, looks back over its scarf: headTurn +0.55, lookX 0.7, lookY −0.9. |
| +3.0 → s16b04 | over Fear's shoulder {600,720,0.85} | The Void tall, still, hood dark with faint twinkling galaxies (COSMOS_RESIDUE). Fear's head soft in the lower-left foreground (screen-space, scale ≈2.6, `facing 1`, headTurn 0.5), eyes glistening. |
| s16b04 → S.end | close {255,1470,2.8} | Starlight k 0.5 on the right cheek. The smile arrives (eyes first), last tear, small nod up-right; then (from ≈S.end−1.7) it turns `facing −1` and skips off **frame-left** along the floor — the way back to the HQ, the way it came in with the CEO in s08 (y 1700 → 1680, scale via hqScaleAt) — out of frame by S.end−0.5. Hold the EMPTY frame (robe, starlight) for the last 0.5 s: a clean exit, so s17 can enter left→right (§1.7-9). (Not "toward the glow": from x 250 the glow is up-RIGHT.) |

### s17 · can_i_help · 285.63–296.77
| span | view · cam | staging |
|---|---|---|
| S.start → s17b02 | `alarm` {380,960,1.0} → {560,960,1.0} (slow track ≈50 px/s, starting at S.start+0.3) | Clean entrance: the EMPTY alarm wall for S.start → +0.3 (§1.7-9). Fear trots in from x −60 at S.start+0.3, floor y 1406 (scale 1.8), `facing 1`, walking **left→right** (toward the console, ≈570 px/s ≈ 1 body height/s: a trot). Slows under the handle (≈x 600 at s17b01+1.0), looks up at it, one hand lifts ~20 local px (+1.3), lowers (+1.9), walks on, lighter, tuft up. alarm 0. |
| s17b02 → s17b03 | `front` {450,1150,1.45} | CEO at consoleMid with clipboard + pen. Fear enters behind the row from the right and pops up on tiptoe at FEAR_TIPTOE_F by +1.0 (between the CEO and SADNESS at x 625; JOY 735, ANGER 315, CALM 165). TOP SHADE on. |
| s17b03 → s17b04 | close on CEO {450,1000,2.2} | Looking down-right at Fear; a quick glance back over the shoulder toward the back of the mind (it is BEHIND the CEO in this view, the cage behind-left: headTurn −0.35, lookX −0.8, lookY −0.2 for ≈0.4 s) and back to Fear. |
| s17b04 → s17b05 | close on Fear {535,1200,2.6} | Fear's mouth clears the rim (sy≈663) for the line; console lights in its eyes (sparkle 0.6). |
| s17b05 → S.end | `front` 'console' {450,1120,1.35} | CEO steps aside to CEO_ASIDE_F (+0.8 → +2.0). The row scoots to ROW_S19 (SADNESS 625→570, JOY 735→695, ANGER 315→330, CALM 165→205). Fear climbs onto its stool: FEAR_TIPTOE_F → consoleFear (450,1328) by +2.6; presses its first button at +3.0 (consolePress, console_beeps); eyes light up. |

### s18 · the_rusted_cage · 296.77–307.11 (dissolve in) · `backOfMind`
| span | cam | staging |
|---|---|---|
| S.start → s18b02 | close {420,1400,1.6} | CAGE_B `rustedOpen`: rust 1, door 0.93 → 1.0 over s18b01+0.1 → +1.6 (outBack, rust_creak), sign askew. Robe behind, sleeve cuff at the top edge. No characters. |
| s18b02 → s18b03 | drift {420,1400,1.6} → {520,1400,1.6} | flake 0→1 over s18b02+0.5 → +4.0. |
| s18b03 → S.end+0.9 | {520,1400,1.6} → (from +1.2) {400,1150,1.25} | foldStar 0→1 at s18b03+0.3 (0.6 s) on the fold at (586,1388) (sx≈466); then the camera rises up-left toward the far glow ("toward the front of the mind") into the dissolve. |

### s19 · the_scene_changed · 307.11–322.81 (dissolve in) · `front`
| span | cam | staging |
|---|---|---|
| S.start → s19b02 | {420,1150,1.45} → {490,1150,1.45} | ROW_S19 at y 1384, Fear at consoleFear (450,1328). Dawn. TOP SHADE on. Fear presses with concentration (tongue tip), proud wiggle; SADNESS rests its head on Fear's shoulder; JOY leans in past SADNESS beaming → Fear's silent giggle (hand over mouth); ANGER hides a smile; CALM points/nods at the next button (see §1.7-7). |
| s19b02 → s19b03 | 'establish' {450,800,0.9} → (continuing) | The CEO's POV from the screen: the five at the console, faces lit by the buttons; the Void STARE_F with COSMOS_RESIDUE (glyphs 0) "like a mountain behind a village"; CAGE_F `barelyVisible` (rust 1, door 1, dim 0.85) at its left foot. Fear glances back over its shoulder, up at the Void (it stands straight behind Fear's seat in this view: headTurn −0.4, lookY −0.9) once (+0.6 → +1.4), small smile. |
| s19b03 → S.end+0.9 | → 'wide' {450,800,0.8} by s19b03+3.0, hold | 'cage' at +2.06 (the speck). A single 4-point star twinkles in the hood at s19b03+1.5 (0.8 s). Fear leans its head on SADNESS's shoulder (CALM's slow blink). JOY glances up toward camera and smiles. From S.end−2.0: **screen bloom** (§5.10) rising from the bottom → into the dissolve. |

### s20 · a_tear_or_two · 322.81–339.07 (dissolve in) · REAL_ROOM
| span | cam | staging |
|---|---|---|
| S.start → s20b02 | `desk` {424,760,1.5} | Lamp 1. SELF seated, notebook open (flat) on the drawing. Gold pencil in the right hand; draws one tiny gold star (4-point `star()` from face.mjs, growing over s20b01+0.8 → +2.4) inside the black crayon hood on the right page. |
| s20b02 → s20b03.end | {424,760,1.5} → {424,690,2.1} | Push on the face; tear wells (b02), spills, soft laugh, wipe with the sweater sleeve (wipeTear), smile down at the page (b03). |
| s20b04 → S.end | {424,690,2.1} → `opening` {420,655,1.12} by s20b04+2.6 | Notebook closes (open 1→0 over +0 → +1.2), palm rests on the cover (+1.2 → +2.0); lamp click at +2.4 (lamp 1→0 in 0.25 s, fairy 1→0.3 over 1 s); chin lifts, eyes up toward the moon/window (lookY −0.85, lookX 0.3, headTurn 0.2, sparkle); starHood 0→0.8 (+2.8 → +4.3) → 0 (+5.5 → +6.8); starWink at +4.0 (0.8 s). Hold the mirror composition to the end. |

---------------------------------------------------------------------------------------------------------------

## 4. LIGHT & COLOUR SCRIPT

### 4.1 The arc
Warm memory (s01) → cozy-but-interrupted HQ (s02) → **cold and dimming from the reveal (s03) to the turn (s13)**,
darkest at s10 and s13 → **the first light is the cosmos itself (s14)** → **warming from s15** (the emotions'
smiles) → warmest dawn at the console (s19) → the real room: warm lamp, then a calm moonlit blue whose stars
rhyme with the Void's face (s20). The alarm red is the only saturated colour in the cold stretch, and it never
appears after s07.

### 4.2 Per-scene settings (set state · grade · vignette)

`cold`/`warm` are the GRADE amounts (§5.3). Set fields are drawHQ state; BoM = backOfMind.

| sc | lightsDim | consoleGlow | mist | shadow (front `voidShadow` / BoM `shadowSpread`) | alarm | screenMode | cold | warm | vignette | special |
|---|---|---|---|---|---|---|---|---|---|---|
| s01 | — (lamp 1, fairy 1, moon 1, dusk 0) | | | | | | 0 | 0 | 0.25 → 0.35 (b03) | amber eye-glow out |
| s02 | 0.05 → 0.35 (s02b04+2.2 → S.end) | 1.35 → 1.0 (b01), → 0.8 (s02b04+2.2 → S.end) | 0.35 → 0.6 (same span) | 0.15 | per §2.1 | room (+alarm blend) | 0.1 → 0.35 (same span) | 0.1 → 0 (same span) | 0.35 → 0.45 (same span) | the room dims and cools as the bell dies, so the s02→s03 cut (same room, same instant) matches |
| s03 | 0.35 | 0.8 | 0.6 | 0.15 → 0.7 | 0 | | 0.35 | 0 | 0.45 | |
| s04 | 0.35 | 0.8 | 0.6 | 0.7 | 0 | | 0.4 | 0 | 0.45 | backdrop haze 0.16–0.2 |
| s05 | 0.35 | 0.6 | 0.6 | 0.7 | 1 → 0 (b04) | | 0.4 | 0 | 0.45 | |
| s06 | 0.3 | 0.8 | 0.4 | 0.5 | 0 → 1 (b08) | | 0.45 | 0 | 0.4 | |
| s07 | 0.35 | 0.8 | 0.4 | — | 1 → 0 (b01) | | 0.5 | 0 | 0.45 | |
| s08 | BoM 0.3 · front 0.4 | 0.7 | BoM 0.6 · front 0.45 | BoM 0.7 · front 0.6 | 0 | | 0.55 | 0 | 0.5 | |
| s09 | 0.4 | 0.7 | 0.45 | 0.6 | 0 | | 0.6 | 0 | 0.45 | |
| s10 | 0.35 | — | 0.65 | 0.4 → 1.0 | 0 | | 0.65 | 0 | 0.55 | darkest wide |
| s11 | back 0.4 · BoM 0.35 | 0.7 | 0.6 | 1.0 | 0 | room | 0.6 → BoM 0.5 → 0.6 (s11b03+1.4 → S.end) | 0 → BoM 0.15 → 0 (same span) | 0.45 ('#2a1408') → 0.5 black (same span) | dream, eased out before the cut to s12 |
| s12 | 0.35 | — | 0.6 | 1.0 | 0 | | 0.6 | 0 | 0.5 | |
| s13 | 0.4 | — | 0.6 | 1.0 | 0 | | 0.65 | 0 | 0.55 | darkest close |
| s14 | 0.35 | — | 0.5 | 1.0 → 0.8 | 0 | | 0.65 → 0.3 (s14b01 → s14b02.end) | 0 | 0.55 → 0.4 (same span) | cosmos light, glow 1.2, starlight k=cosmos |
| s15 | back 0.15 | 1.0 | 0.3 | — | 0 | room | 0 (BoM closes 0.2) | 0.2 | 0.35 | starlight 0.5 on Fear |
| s16 | 0.25 | — | 0.45 | 0.6 | 0 | | 0.15 | 0.15 | 0.4 | glow 0.6, starlight 0.45 |
| s17 | 0.1 | 1.1 | 0.3 | 0.1 | 0 | room | 0 | 0.4 | 0.35 | TOP SHADE |
| s18 | 0.2 | — | 0.45 | 0.4 | 0 | | 0 | 0.25 | 0.4 | foldStar |
| s19 | 0 (`HQ_PRESETS.dawn`) | 1.15 | 0.25 | 0.1 | 0 | calm | 0 | 0.8 → 0.9 | 0.3 | TOP SHADE (b01), screen bloom (end) |
| s20 | lamp 1 → 0 at s20b04+2.4, fairy 1 → 0.3 | | | | | | 0 | 0.1 → 0 at the click | 0.3 | starHood |

Across a cut that stays in the same place and moment (s02→s03, s03→s04, s04→s05, s06→s07, s08→s09, s11→s12,
s12→s13, s13→s14), lightsDim / consoleGlow / cold / warm / vignette match the neighbour's last/first frame within
±0.05 and mist / shadow within ±0.1 (the values above were corrected so that they do: s02's end, s04/s05, s08's
front mist, s11's dream exit and s14's start had jumps of 0.1–0.35). A cut to another place (back of the mind ↔
HQ, the `back` view's warm room) may change the grade. Inside a scene ease grade changes over ≥ 1.5 s, never on a
cut you don't own.

### 4.3 The cosmos track (Void `cosmos` = `drawCosmos` reveal)
| time | value |
|---|---|
| everything before s14 | **0** (pure darkness — no eyes, ever) |
| s14.start | 0 |
| s14b01+0.8 | 0.05 (the single first star) |
| s14b01.end | 0.3 ("a few stars kindle") |
| s14b02.end | 0.62 |
| s14b03.end | 0.85 |
| s14b04+1.5 → s14b09 | 1.0 (glyphs on) |
| s14b10+2.0 → s14 end | 0.6 |
| s16, s17 (if the hood shows), s19 | **0.5** = COSMOS_RESIDUE, cosmosOpts `{seed:7, glyphs:0}` |
| s19b03+1.5 | + one 4-point star glint in the hood centre (0.8 s), separate from the cosmos |

---------------------------------------------------------------------------------------------------------------

## 5. SHARED CONVENTIONS

### 5.1 Standard character scales
| view | Void | cage | Fear | CEO | emotions |
|---|---|---|---|---|---|
| front | 0.37 at VOID_F (fixed) | 0.3 at CAGE_F | at the alarm 0.42; in the cage 0.3; behind the console 0.8 (tiptoe / stool anchors) | hqScaleAt (0.481 at CEO_SPOT_F, 0.444 at the alarm, 0.8 at consoleMid) | 0.8 at the slots |
| back | not drawn | not drawn | (POV) | 0.543 at consoleBackMid | 0.543 at consoleBack1..4 |
| alarm | — | — | 1.8 | 1.976 standing / 2.091 kneeling | — |
| backOfMind | 0.9 at VOID_B | 0.952 at CAGE_B | inside 0.952; outside hqScaleAt (THRESH 0.97, STOP 1.065) | 1.12 (y 1730) | — |
| REAL_ROOM | — | — | — | SELF 1 at `selfSeated` | — |

Height ratio rule when you scale freely (backdrops, foreground cheats): **Fear's scale = 0.91 × the CEO's scale at
the same depth**; the Void is ≥ 4.6 × Fear's height at the same depth (in `front`, Fear at the alarm stands nearer
the camera than the Void: 629 / 139 px = 4.5×, which is correct perspective, not an error).

### 5.2 Draw order per view
* `front`: drawHQ → Void → cage back → (Fear in cage) → cage front → CEO/Fear by y → emotions by y →
  drawHQForeground (console) → anything nearer → drawAlarmLight → TOP SHADE → grade → vignette.
* `back`: drawHQ → emotions + CEO by y → drawHQForeground → drawAlarmLight → grade → vignette.
* `alarm`: drawHQ → Fear → CEO → drawHQForeground → drawAlarmLight → grade → vignette. With the hand on Fear's
  shoulder (s06): CEO `layer:'body'` → Fear → CEO `layer:'front'` (self.md recipe; verified
  `staging_check_alarm.png`).
* `backOfMind`: drawHQ → drawVoid (handL `defer:'hand'` when a hand is out) → cage back → Fear inside → cage
  front → `sleeveFront` (§1.5) → push hand → Fear outside / CEO by y → drawVoidGlow → starlight → unlock /
  shoulder hand (`drawVoidHand`) → drawHQForeground → drawAlarmLight → grade → vignette.

### 5.3 GRADE (paste; one or two full-frame fills, ~0.3 ms)
```js
function grade(g, cold, warm) {            // call after everything except the vignette
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply';   g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`;  g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
```
Then `vignette(g, strength)` from engine.mjs (strengths in §4.2: 0.25 thumbnail, 0.3–0.35 warm, 0.45 cold,
0.5–0.55 the darkest backOfMind). Characters are NOT dimmed separately (readability): the grade tints them with
the set. See `staging_test_grades.png`.

### 5.4 Lighting Fear with the Void's glow (s14–s16)
1. `drawVoidGlow(g, ...VOID_B, pose)` after the characters (pose.glow: s14 1.2, s16 0.6, s19 0.3).
2. A soft starlight pool on Fear's face, on the side toward the hood (up-right), after Fear:
```js
function starlight(g, x, y, r, k) {        // world coords of the current camera
  if (k <= 0) return;
  g.save(); g.globalCompositeOperation = 'screen';
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, `rgba(176,150,255,${0.30 * k})`); gr.addColorStop(0.55, `rgba(110,200,255,${0.12 * k})`);
  gr.addColorStop(1, 'rgba(110,200,255,0)');
  g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); g.restore();
}
// Fear at (fx, fy, fs): starlight(g, fx + 25 * fs, fy - 250 * fs, 190 * fs, k)   k: s14 = cosmos, s15 0.5, s16 0.45
```
3. Fear's face `sparkle` = cosmos while it looks at the hood (stars in its irises), tears catch the light.
Never light the Void's hood shell; the hood stays dark around the cosmos.

### 5.5 The alarm
* Only Fear pulls it, only at: s02b02+2.40, s05b01+0.25, s06b08+0.6. `alarmPulled` 0→1 in 0.25 s and stays 1 while
  Fear hangs on it; `alarm` 0→1 in 0.3 s. Never strobe `alarm` itself (the beacon/bell animate from `t`).
* Fades: s02 1→0 by s02b04+2.2; s05 1→0 over s05b04; s07 1→0 over s07b01. No alarm after s07 (s17: not pulled).
* Always call `drawAlarmLight(g, view, st)` after the characters. Red falls: `front` right side; `back` from the
  left; `alarm` on the station; `backOfMind` only the distant light pulses red.
* Backdrop/foreground cheats: tint characters on the alarm side yourself with a `multiply` linear gradient from the
  alarm side, colour `#ff6472`, alpha `alarm * (0.2 + 0.2 * pulse) * 0.75`, where
  **`pulse = 0.5 + 0.5 * Math.sin(t * 2 * Math.PI * 1.2 - Math.PI / 2)`** (the set's exact pulse, so it stays in sync).
* Back view screen: `screenMode:'room', screenModeB:'alarm', screenBlend: 0.6 * alarm`.

### 5.6 The Void
* Positions/poses only from §1.4. `idle: 0` in s03–s13 (and in every beat where the screenplay says nothing
  moves); `idle: 0.5` from s14 on. Head moves happen only in s13b01 (the turn) and s14b09 (turning back).
* `shadowSpread` (BoM) **or** the set's `voidShadow` (front) — never both at full strength.
* Head pose changes: animate slowly (each 1/64 step builds a hood sprite; that is fine).

### 5.7 Faces, frames, cameras
* Face centres in x 72…648 and y ≤ 1088 on screen; lip-synced mouths must be visible (in `front`, the console rim
  is y≈1247 world: use FEAR_TIPTOE_F / consoleFear for Fear's lines).
* Keep `front`/`back` zoom ≤ 2.2 when the set matters (beyond, the set softens: fine only inside the hood).
* LOCKED shots (no drift): s03b02, s10b02, s12b05, s12b10–b11, s13b01. All others: `drift(t, 2–3)`.
* The stage edges: REAL_ROOM keep x within 360/z…840−360/z; HQ stages paint a dark margin, but keep it off-frame.

### 5.8 Transitions
* Dissolve-in scenes: s02, s06, s10, s18, s19, s20 (0.9 s, done by render.mjs). The OUTGOING scene (s01, s05, s09,
  s17, s18, s19) must keep rendering sensibly to **S.end + 0.9**: let the last move continue gently, start no new
  action, keep all `S.k` keys clamped. The incoming scene's first 0.9 s is half-visible: no key action there.
* Scene-internal crossfades (s11 'image', s14b02 cosmos): render both into an offscreen canvas and blend; the
  outgoing image fades over 1.0–1.2 s.
* Cuts: hard, on a look or on an action (§3 says which). Match eyelines across them (§1.2).

### 5.9 TOP SHADE (s17b02–b05, s19b01): keeps "the back of the mind" quiet when the robe/cage peek in at the top
```js
const gr = g.createLinearGradient(0, 0, 0, 300); gr.addColorStop(0, 'rgba(8,6,20,0.55)'); gr.addColorStop(1, 'rgba(8,6,20,0)');
g.save(); g.setTransform(1,0,0,1,0,0); g.fillStyle = gr; g.fillRect(0, 0, 720, 300); g.restore();
```

### 5.10 Screen bloom (s19 end → s20): the screen of consciousness (behind the camera) brightens
```js
const k = S.k(t, [['scene.end-2.0', 0], ['scene.end+0.9', 1]]);
const gr = g.createLinearGradient(0, 1280, 0, 300); gr.addColorStop(0, `rgba(255,236,200,${0.55 * k})`); gr.addColorStop(1, 'rgba(255,236,200,0)');
g.save(); g.setTransform(1,0,0,1,0,0); g.globalCompositeOperation = 'screen'; g.fillStyle = gr; g.fillRect(0, 0, 720, 1280); g.restore();
```

### 5.11 Character continuity details
* **CEO outfit** 'ceo' in every HQ shot; SELF 'sweater' in REAL_ROOM. **Clipboard** (in time order): hugged
  (s02b03) → at the hip (s03) → on the floor by the CEO's back knee (s04) → picked up as they rise, hanging, pages
  slipping (s05) → **left on the console (s06–s08)** → picked up (s09b01) → on the console again while they rub
  their eyes (s11b01) → in hand with a pen (s15, s17b02–b04) → put down when stepping aside (s17b05).
* **Props no module draws** (write a small local helper, same in every scene that shows it): the CEO's pen (s15,
  s17), the tiny gold key (s08 insert), SELF's gold pencil (s20). Fear's "tongue tip" (s19b01) has no face
  parameter either: a tiny local shape or skip it.
* **Fear tremble**: s02 0.6 · s03 0.8 (frozen 0 in b02) · s04 0.6–0.9 · s05 0.9 · s06 0.7 · s07 0.5 (0 for one beat
  in b01) · s08 0.6 · s10 0.5 · s11 0.6 → 0 at the creak · s12 0.4–0.6 · s13 0 → 0.9 → 0 · **0 from s14 on**.
* **Fear tears** at cuts: s06 welling (b05) → one on the lid (b06); s08 spilling → streams through s10–s11; the
  hanging tear falls at s11 end; s12 well and spill (b06+); s14 tears of wonder; s16 wiped (b01), one last (b04);
  dry from s17.
* **Fear's scarf** always on; wiping uses its end (s12b10, s16b01).
* Each character keeps one `t` offset for idle life (e.g. JOY t+1.3, SADNESS t+2.9, ANGER t+4.1, CALM t+5.7) in
  every scene, so blinks and breaths never sync — use these exact offsets.

### 5.12 Housekeeping
* Do not edit shared modules; write helpers locally. Key all timing to beat anchors.
* Check your scene with `node src/render.mjs --sheet sNN --n 16` and with `--times` at your first and last frames,
  and compare them with the neighbouring scenes' entries in §2.2.
