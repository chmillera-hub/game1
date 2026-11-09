# STAGING — "The Void Has a Sense of Humor" (binding staging plan for all scene animators)

The single source of truth for **where everyone stands, where the camera goes, and what carries across every cut**.
Code half: **`web/src/scenes/marks.js`** (import it in every scene: marks, camera presets, tod/voidSky ramps, the
sky galaxy, looks). Verification bench: **`web/src/labs/staging.js`** (real VOID / JESUS / FEAR / MAGICIAN rigs,
a capsule USER stand-in, the real EDGE and BACKROOM sets):
`node tools/render.js stills --lab staging --t 0,4,5,6,10,11,12 --out out/staging` (HUD lines: red = phone UI 90,
yellow = title band 110–300, cyan = subtitle band 880–1060). Contact sheet of all setups:
`out/staging/staging_contact.jpg`, real-set versions `out/staging/staging_realsets.jpg`.

Times quoted below are from the **estimated** timeline (`data/timeline.txt`, ESTIMATED). They will move when the real
audio lands. **Never use absolute seconds: anchor everything to beat refs** (`T('s05b04')`, `T('s05b04.end-0.3')`, `k()`).

---------------------------------------------------------------------------------------------------------------------

## 0. Read this first (rules that prevent 90 % of continuity bugs)

1. **Stage frames.** Each location has a stage frame (`EDGE`, `ROOM` in marks.js) in which **the camera side is local
   +Z, the action line runs along local X, screen-left = local −X, screen-right = local +X**. Write marks and
   cameras in stage coords, convert with `EDGE.W(x,y,z)` (position), `EDGE.Y(localYaw)` (facing), `EDGE.shot(look,
   {dist, yaw, pitch, fov, screenY})` (yaw in local degrees, 0 = camera on local +Z), `EDGE.at(pos, look, fov)`,
   `EDGE.cam('MASTER')` (verified presets). Same API on `ROOM` (call `ROOM.fit(set)` once in setup()).
2. **`core/camera.js framed()` puts the subject at `1 − screenY`** (its sign is inverted vs its doc). Do not use it
   for placement. Use `frame()` / `EDGE.shot()` / `ROOM.shot()` from marks.js (correct: `screenY: sy(420)` puts the
   look point at y = 420 px), or explicit pos/look.
3. **fov is VERTICAL degrees.** "mm feel" in the screenplay → `LENS` in marks.js: 18→72, 24→60, 28→54, 35→44,
   50→33, 85→21. Portrait frames are narrow: at fov 44 the frame is only ±12.8° wide. **Stack the action in depth
   and height, never side by side across the frame.**
4. **Frame layout:** faces and key action in y ≈ 110–850 px; the subtitle band 880–1060 never holds a face/eyes;
   nothing important above y 90 (phone UI). Title (s01 frame 0, s22 end) sits in y 110–300 over calm sky.
5. **The Void's face lives inside a deep hood.** It reads only when the camera is within **±50° of where its hood
   points**. Beyond that you see velvet. Cheat its body/hood toward the camera (yaw or `head.yaw` ≤ 0.35 rad) and
   let the eyes (`gaze`) do the looking. Every Void face beat must pass this test.
6. **Screen direction (Part One):** the USER is always screen-LEFT, the VOID always screen-RIGHT, Jesus between them
   or screen-left of the Void. Cameras stay on the camera side (local z > line). The only allowed crossings are the
   axial shots listed per beat (POVs, reverse along the line) and the "cut round" in s10b06 / s12b02, which are
   isolated singles. **Bonus:** Fear/cage screen-left → Void → magician → janitor corner screen-right.
7. **Purity:** every pose is a function of t built from beat refs; cross-scene props (the sky galaxy, the little
   rolling galaxy, the frozen star mote) use the shared helpers/positions below so neighbouring scenes agree.
8. **Feet on the ground:** EDGE clearing is flat (y = 0, r < 7.5 m). Outside it use `set.groundAt(x, z)` for every
   foot (s01 chase, the s14 exit, the s16 walk-off, the user on the hill). Hide flowers under seated/fallen
   characters with `opts.clear: [[x, z, r]]`.
9. **Apply the camera BEFORE rig updates** (eye catchlights read `CTX.camera` during update).
10. Mirroring vs the screenplay text: where the script's left/right contradicts these rules, this doc wins (listed
    explicitly as **MIRRORED**). Hands: the USER's phone is in the LEFT hand, the RIGHT hand is the raised "defend"
    hand (USER rig defaults). Jesus's arm around the Void in s03–s07 is his LEFT arm (he stands at its right);
    in s16 he walks on its left with his RIGHT arm around it.

---------------------------------------------------------------------------------------------------------------------

## 1. THE_EDGE — world map (Part One, s01–s16)

### 1.1 World vs stage

The EDGE set (`web/src/sets/edge.js`) builds the world: the low sun ~8° left of world −Z (`SUN_AZ = −0.14`), the
pale path running **through the stage along world −Z** toward the sun (it follows `EDGE.PATH_WORLD`), coming in
upstream from the north-east (+X,+Z) over the peach crest where the Void came from. Set key light comes from world
(−0.69, *, −0.72) (back-left for a +Z camera), the warm fill from world (0.5, 0.42, 0.76).

The **EDGE stage frame** is rotated −126.87°: local +X = world (−0.6, 0, 0.8), local +Z = world (−0.8, 0, −0.6).
In stage terms: **the user sits downstage-left, the Void and Jesus stand upstage-right, the master camera is
downstage (local +Z) looking upstage**. Consequences (all verified in the lab with the real set):
- The set key falls from almost exactly the master camera's direction → Jesus's and the Void's faces (they face
  the user, i.e. sunward) are warmly front-lit in every master/OTS/single on them.
- The user faces upstage (nightward): golden-backlit by the key, front-filled by the set fill in their singles;
  reverse angles on the user look toward the sunset (warm haze behind them, phone glow on the face).
- The anti-sun sky (pink belt-of-Venus → lilac → indigo) sits behind the Void in the master: its `voidSky` pocket
  belongs there.
- The path near the stage = the user↔Void line (world x ≈ 0). Downstage-left in stage coords = down the path toward
  the sun = where the user flees (s14) and where the pair walk off (s16).

### 1.2 Top view (stage coords, metres; camera side at the bottom)

```
 local z
 -12   .                                   CREST (3.8,-12.1)  peach hill; the Void plods over it in s01
  -8   .                         s01 user ~(2.35,-6.4) running downstage   |path from the crest
  -1.4 .          JV(0,-0.65)            V(1.0,-1.1)  VSIT(1.15,-1.35)    (Void stands / sulks seated)
  -0.4 .     JM(-0.45,-0.2)      V15(0.34,-0.37)                          JS(1.74,-0.37) (hand on shoulder)
   0   +----------------------------------------------------------------------- local x
  +0.6 .           USKID(-0.55,0.6)
  +0.7 .       K(-0.65,0.7)  (Jesus kneels)
  +1.4 .   U(-1.3,1.4)  (user sits)
  +1.8 .  J1(-1.64,1.77)
  +2.4 . J0(-2.25,2.44)  the bend           path -> sun: local (-0.8,*,+0.6) = world -Z
  +5.6 .              OTS cam (-2.9,1.8,5.6)
  +7.9 .                 MASTER cam (-1.7,2.45,7.9)  looking upstage-right, high
```

### 1.3 Marks (`EDGE.M`; yaw = local facing, 0 faces the camera side; world values for reference)

| mark | local (x,z) | local yaw | world (x,z) | who / when |
|---|---|---|---|---|
| `U` | (−1.30, 1.40) | 2.45 | (−0.34, −1.88) | USER sits on the path facing the Void (back 3/4 to the master), s02b04 → s14b01 |
| `USKID` | (−0.55, 0.60) | −0.74 | (−0.15, −0.80) | user trips (running downstage-left), skids/slides 0.9 m to U, twists round (yaw increasing, face passes the camera) |
| `J0` | (−2.25, 2.44) | 2.40 | (−0.60, −3.26) | Jesus appears at the bend on "Now." (s02b02), strolling upstage |
| `J1` | (−1.64, 1.77) | 2.40 | (−0.43, −2.37) | Jesus after two stroll steps; the scooting user's back meets his shins (s02b04–b06) |
| `V` | (1.00, −1.10) | −0.52 | (0.28, 1.46) | VOID stands, faces the user cheated 12° to camera (s02b05 → s10b04) |
| `JV` | (0.00, −0.65) | −0.50 | (0.52, 0.39) | Jesus at the Void's front-right = screen-left of it, 1.1 m from its centre (s03 → s08b02). Whisper-verified: with the Void at V in `whisperPose(-1, 1.25)` its mouth lands 6 cm above Jesus's `earL` |
| `JM` | (−0.45, −0.20) | 0.05 | (0.43, −0.24) | Jesus "in the middle", faces camera: the Void at his left, the user at his right (s08b03 → s11) |
| `VSIT` | (1.15, −1.35) | 2.62 | (0.39, 1.73) | the Void turned its back (3 shuffles, yaw −0.52 → 2.62 through 0, i.e. the face sweeps past camera) and sits (s10b05 → s14) |
| `JS` | (1.74, −0.37) | −3.04 | (−0.75, 1.61) | Jesus at the seated Void's RIGHT shoulder (camera side), back to the master (s12) |
| `K` | (−0.65, 0.70) | −0.74 | (−0.17, −0.94) | Jesus kneels (right knee down) facing the user, arm's length (s13 → s15b01) |
| `V15` | (0.34, −0.37) | −0.74 | (0.09, 0.49) | the Void standing right behind kneeling Jesus, facing him (s15 → s16b01) |

Heights for framing: Jesus eyes 1.55 (kneeling ≈ 1.05), mouth 1.46, ears 1.52; USER standing eyes 1.43, seated eyes
≈ 0.85–0.95; VOID eyes 2.16 / hood tip 3.07 standing, seated shoulders ≈ 1.25, whisper-bent mouth ≈ 1.55.

### 1.4 Paths and far features (world)

- **The path** `EDGE.PATH_WORLD`: (14,18) → (8.8,11.6) → (4.2,6.1) → (1.6,2.8) → (0.3,1.5) → (−0.3,−1.9) → (−0.6,−3.3)
  → (−0.5,−6.6) → (−0.6,−11.7) → (−1.5,−18) → (−2.5,−26) → … toward the sun. The set follows it.
- **s01 chase**: upstream on the path below the peach crest. User ~ local (2.35, −6.4) = world (3.7, 5.7); Void on the
  crest ~ local (3.3, −12.4) = world (7.9, 10.1); both moving down the path toward the stage (local ≈ (−0.2, +1)
  direction). Ground speed is cheated slow (≈ 1.1 m/s) with full run/waddle cycles; the camera dollies back with them.
- **Crystal / puff tree at the bend** (s02b01): any set tree right of the path at world ≈ (2.0, −5.2) — keep it out
  of the master/OTS cameras (downstage-left of the stage is camera territory).
- **User's exit** (s14): `EDGE.EXIT_LOCAL` U → J0 → (−5, 4.4) → over the gentle rise at world (−0.8, ~0.5, −11)
  (`RISE_WORLD`), feet on `groundAt`.
- **The user's hill** (s16b07–b09): top of the lilac rise just left of the path (looking sunward) at world
  (−3.6, groundAt, −10) (`HILL_WORLD`), sitting hugging knees, facing down the path toward the sun (world yaw ≈ 2.84,
  i.e. facing world (0.3, −0.95)). If the set's terrain there is flat, use the nearest raised ground left of the path
  between z −8 and −14; the camera numbers in §3 assume it reads at upper-left of the walk-off wide.
- **Walk-off**: Jesus + Void walk the path from V15 down through U, J0 and on (`set.pathAt(s)`), ~0.85 m/s
  (Jesus `walk` 0.85 cyc/s, the Void `waddle` 1.1 cyc/s), passing the foot of the user's hill ~t = s16b07 and reaching
  world z ≈ −20 at s16b07, z ≈ −26 at the end; move `shadowAt` with them. The set's `shots.finale` (22° from behind,
  crest in front of the sun) is the right lens for the final silhouettes.

### 1.5 Sun, time of day, voidSky

All Part One scenes call `set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t), voidPos: void.root.position… })`.
`todAt` is **continuous across every cut** (never key tod per shot):

| scene start | s01 | s02 | s03 | s04 | s05 | s06 | s07 | s08 | s09 | s10 | s11 | s12 | s13 | s14 | s15 | s16 | s16b11 | end |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tod (est.) | 0.00 | 0.03 | 0.08 | 0.14 | 0.19 | 0.25 | 0.26 | 0.32 | 0.35 | 0.36 | 0.39 | 0.41 | 0.42 | 0.50 | 0.52 | 0.55 | 0.88 | 1.00 |

Golden dusk (s01–s07) → late dusk (s08–s15) → sunset (s16, the sun visibly sinks during the walk-off).
`voidSkyAt`: 0.5 compact in s01 (keep the pocket hugging the hood, never behind the title), ~0.6 through s07,
0.62 → 0.78 on the s08 scowl, ~0.72 through the sulk, 0.6 for s12–s15 (softening), 0.7 → 0.9 in s16 ("fuller of
stars than before"). The set advises ≤ 0.6 in two-shots: scenes may scale it ×0.8 in tight two-shots and up to 1.0
on low angles at the Void — **but keep the value continuous across a cut between two angles of the same moment**.
Per-shot cheats allowed by the set: `sunShift` (±0.15, keep the sun disc out from behind Jesus's head — no halo),
`sunGlow` 0.5–0.7 in close-ups toward the sun, `keyYaw`, `fillMul`. Never more than ±0.15 rad of key cheat between
two cuts of the same moment.

### 1.6 Cross-scene props in the EDGE

- **The big sky galaxy** (laughed up in s04b11): `galaxyAt(t)` (world) + `galaxySpin(t)`, size 1.1 m,
  `Particles` CELL.galaxy, colour 0xd8c0ff, alpha 0.9. It hangs high over the stage (world (1.2, 6.2, 0.9)) from
  s04b11.end until s16, then floats ahead of the walkers down the path. Draw it in **every** Part One shot from
  s04b11.end on where that point is in frame (wides, low angles, the walk-off). s04b11 animates the launch from the
  Void's mouth to `GALAXY.from`.
- **The little rolling galaxy** (s04b09): coughed out, bounces at stage (0.4, ·, −0.2), rolls down to the user's
  sneaker at stage ≈ (−0.85, 0.02, 0.85) during s04b09–s04b13, lies flat twinkling there until the user stands up in
  s14b01 (then it stays on the path; drop it after s14).
- **The frozen star mote** (s08b01 → s09b03 "scary"): one star mote that rose off the Void's left shoulder stops in
  mid-air at `T('s08b01')+3.2` and hangs at a fixed WORLD point = Void `shoulderL` (at that moment) + (0.15, 0.35, 0.10);
  every shot of s08–s09 that sees that point draws it; on "scary" it drops (0.4 s, ease in) and winks out.
- **The phone** (USER rig): screen `feed` with glow ~0.85 from s01 through s13b10 (cool glow on the chin); s13b10 it
  goes face-down in the lap, `phone: 0` (lit only by dusk); s13b16 face-up again (glow back); s14b03 `profile` →
  `block` → `blocked`; s16b08 `blocked` screen with the Unblock button (thumb hovers/touches/lifts).
- **Hood**: down (half fallen back by s05b02) until s13b17, then cinched tight for s14 and the hill.

### 1.7 Line / eyeline rules (Part One)

- The main line runs **U → V** (and U → JV/JM). Camera-side test: `EDGE.sideOK(camWorld, lineZ)` is not enough on the
  diagonal; use: camera stage coords (x,z) must satisfy `0.74·(x+1.3) + 0.68·(z−1.4) > −0.3` (the half-plane on the
  downstage-right of the U→V line). All Part-One presets in §3 satisfy it except `FRAME0`, `CHASELOW` and `BEND`,
  which come before the line exists (the chase and the empty bend; `BEND` is the deliberate reverse toward the sun).
- Eyelines: the user looks **screen-right and up** at the pair; the pair look **screen-left and down** at the user.
  Jesus↔Void two-shots: Jesus looks screen-right (up), the Void looks screen-left (down). In s15–s16 the line is
  Jesus (K) ↔ Void (V15): Jesus screen-left, Void screen-right, same side.
- s16 travel line: walking toward the sun = **screen-left** in the side tracking shots (camera on their left, the
  camera side); from behind Jesus is screen-left. The front → back cut on "walk off" is the one accepted axial flip.

---------------------------------------------------------------------------------------------------------------------

## 2. MIND_BACKROOM — world map (Bonus, s17–s22)

The BACKROOM set (`web/src/sets/backroom.js`, `LAYOUT`) is authoritative; `ROOM` in marks.js mirrors it
(`ROOM.fit(set)` snaps the frame to `anchors.cageCenter` → `anchors.voidSpot`). The action runs on one diagonal:
**cage/Fear (front-left) → Void → magician (straight behind it) → janitor corner (back-right, back wall z = −5,
right wall x = 4.8)**. The screen-of-consciousness glow is far away at world +Z (behind the master camera: it
front-lights faces); a bare warm bulb on a cord and dusty shafts give practicals. The Void faces the cage at world
yaw −45° (3/4 to a camera on +Z).

| mark (`ROOM.M`) | local (x,z) | world (x,z) | world yaw | who / when |
|---|---|---|---|---|
| `C` cage | (0, 0) | (−1.60, 0.02) | door faces 60° | brass TIME-OUT cage, R 0.45; door + latch face the Void/camera side (`anchors.cageLatch`, `cageDoor`, `cageInside`, `cageBar(angle, y)` for grips) |
| `FIN` | (−0.10, 0.12) | (−1.66, 0.16) | −0.28 | Fear at the front bars (camera side) facing camera-left, its back roughly to the Void (s17b01–b03) |
| `FDOOR` | (0.20, 0.20) | (−1.35, 0.16) | 1.05 | Fear turned round, just inside the open door, facing the Void (s17b04 → s20b01) |
| `FOUT` | (0.70, 0.72) | (−0.73, 0.53) | 2.36 (3π/4) | `anchors.fearOutside`: Fear in front of the Void facing it (s20b01 → end); it follows the fingertip star out of the cage in s20b01 |
| `V` | (1.97, 0) | (0.30, −0.50) | −0.79 (−π/4) | `anchors.voidSpot`: the Void beside the cage, faces Fear (hood 3/4 to the master) |
| `LURK` | (3.36, −0.79) | (1.43, −1.63) | −0.79 | `anchors.lurkSpot`: the magician 1.6 m straight behind the Void (= the Void's default kick-target distance), crouched = hidden from Fear and from the master |
| `PEEK` | (3.20, 0.00) | (≈1.6, −1.2) | −1.18 | the magician leaning out past the Void's camera-side edge (s18b02, s19, s20b02–b04): `body.peek` 0.8–1, `lean` 0.5–0.6 |
| `CRASH` | (6.49, −2.58) | (3.98, −4.18) | −0.79 | `anchors.crashSpot`: bucket pile; `crashed` pose with its back to the corner, face to the room |
| `COSMOS` | (1.30, 0.35) y 1.3 | (≈−0.25, 0.01) | – | cosmos reveal centre between the Void's hands and Fear, radius ~7 |

- **Kick trajectory** (s20b04 → b06): contact = `mag.anchor('chest')` with `void extra.kickTarget` set to it
  (verified: foot lands within 3 cm). The magician leaves along the Void's BACK axis world (0.707, 0, −0.707) and
  must end at `anchors.crashSpot`: use `set.flightPos(u, apex≈2.2)` re-based to start at the contact point (lerp the
  start from PEEK to LURK over the first 20 % of u). Hat flies on its own higher arc (`hatPos/hatRot`). See s20 for
  the screen-time split of the flight.
- **The screen glow** sits behind the master camera; for the s16→s17 dissolve match the **sun disc of the last s16
  frame to Fear's small lavender glow** in the first s17 frame (same screen position, ±40 px).
- **Cosmos** (s22): `COSMOS` set `group` added to the BACKROOM scene, `update(t, { reveal, center: ROOM.W(COSMOS),
  source: void chest, radius: 7 })`, and the BACKROOM `opts.cosmos` fades the room in step (walls and cage fade to
  stars, the open cage stays faintly visible for s22b12).
- Backroom line: Fear/cage screen-left, the Void, then the magician/corner screen-right. Cameras on the camera side
  (local z > 0); the only planned exceptions: s18b01 orbit ends at most at local yaw +85° (still z > 0), s18b06
  LAYERED (behind the magician, looking back toward Fear — an isolated reveal), and s22b10 (the Void looks into the
  lens).

---------------------------------------------------------------------------------------------------------------------

## 3. Camera library (verified unless marked ◇)

`EDGE.cam(name)` / `ROOM.cam(name)` return world shots; values below are STAGE-local (pos / look / fov). Screen
positions are what the lab measured with the real sets (◇ = composed from the verified ones, not separately rendered).

### EDGE
| name | pos | look | fov | measured / use |
|---|---|---|---|---|
| `FRAME0` | (2.46, 0.69, −3.26) | (2.66, 1.40, −7.70) | 44 | s01b01: user face y≈430 left of centre, Void on the crest right of centre eyes y≈400 (aim ~360: move the Void 1 m further up the crest), sky clear 110–300 |
| `CHASELOW` | (2.18, 0.70, −1.85) | (2.58, 1.31, −8.03) | 60 | s01b03 24 mm low wide: user small mid-frame, Void towering behind (hood ~y 260 → push the Void closer/bigger for y≈170) |
| `BEND` | (1.20, 1.15, −2.60) | (−2.25, 0.80, 2.44) | 40 | s02b01–b08 locked reverse toward the sunset: the bend at J0, the huge low sun at frame-right behind it, pastel hills + puff trees; Jesus's eyes y≈414 (never put the sun disc directly behind his head) |
| `ARRIVE` | (1.59, 0.60, 5.06) | (−0.73, 0.80, 2.00) | 44 | s02b03–b04 low side two-shot: Jesus frame-LEFT (eyes y≈405), user bursts in from frame-RIGHT (head y≈406) |
| `MASTER` | (−1.70, 2.45, 7.89) | (−0.25, 0.20, −0.83) | 44 | high wide: user head y≈652 lower-left (back 3/4), Jesus eyes y≈422 centre, Void eyes y≈291 upper-right, hood tip y≈122 |
| `OTS` | (−2.92, 1.80, 5.57) | (0.30, 0.56, −1.33) | 44 | over the user's right shoulder: user head y≈750 (soft), Jesus eyes y≈444, Void eyes y≈302 |
| `WHISPER` | (−1.09, 1.40, 3.30) | (0.23, 1.22, −0.95) | 33 | Void bent to Jesus's left ear: Jesus eyes y≈474, Void eyes y≈265; push in to ~80 % for the close two-shot |
| `KNEEL2` | (−2.40, 0.70, 4.74) | (−0.88, 0.68, 0.65) | 33 | s13: user head y≈562 left (back 3/4), kneeling Jesus eyes y≈406 right, seated Void looming behind him |
| `BEHINDJ` | (3.72, 1.48, 1.67) | (1.46, 1.18, −0.84) | 33 | s12b01: Jesus's back mid-frame (head y≈402), his right hand on the seated Void's right shoulder (y≈692) |

Common singles (◇, use `EDGE.shot(lookPoint, {...})`, yaw in local degrees):
- `JESUS_CU` (Jesus at JV/JM, facing the user): `EDGE.shot(jesus.eyes, {dist: 1.5, yaw: −25, pitch: 0, fov: 33, screenY: sy(410)})`;
  straight-on 85 mm (s11): `{dist: 2.6, yaw: 0…+5 (he faces the camera at JM), fov: 21, screenY: sy(420)}`.
- `VOID_CU` (face, from the user side): `EDGE.shot(void.eyes, {dist: 2.8, yaw: −35, pitch: −4, fov: 33, screenY: sy(380)})`
  (its hood points at local yaw −30°: stay within −80…+20).
- `USER_CU` (reverse, backlit by the sunset, user looks screen-right): `EDGE.shot(user.eyes, {dist: 1.5, yaw: 105,
  pitch: 3, fov: 33, screenY: sy(420)})`; camera stage pos ≈ (0.15, 1.0, 1.0) — on the camera side of the line.
- `USER_LOST` (user's lost profile at frame-left with the pair small at right, s03b02/s04b13/s06b01/s10b07):
  camera ≈ 1.3 m behind-right of the user's head at head height, fov 44: pos ≈ (−1.65, 1.0, 2.75), look ≈ (0.2, 1.4, −1.2).
  The user's face is a lost profile here (cheek, lashes, nose tip). **Any line the user SPEAKS uses `USER_CU`**
  (lip-sync must read); keep `USER_LOST` for silent reactions.
- `LOWUP` (from the user's low eyeline up at the pair, s05b04 / s08b01): OTS lowered to y 0.9 and aimed +0.6 m higher,
  fov 44–54.
- `JPOV` (Jesus's POV down at the user, s05b02–b03, axial): pos ≈ JV + (−0.25, 1.58, 0.25), look = user.eyes, fov 33;
  push to dist 0.45 for the eyes ECU.
- `SIDE15` (s15 side two-shot, K ↔ V15): `EDGE.shot([−0.15, 2.0, 0.17], {dist: 4.4, yaw: 47, pitch: 2, fov: 44,
  screenY: sy(330)})` → Jesus screen-left, Void screen-right.
- `XWIDE` (s16b07, WORLD): pos (−1.63, 1.20, 4.18), look (−1.68, 0.70, −13.99), fov 44: user on the hill upper-left
  (y≈350), pair tiny on the path (y≈530–565). For the sunset silhouettes use `set.shots.finale`.

### BACKROOM (`ROOM.fit(set)` first)
| name | pos | look | fov | measured / use |
|---|---|---|---|---|
| `MASTER` | (−4.28, 2.04, 5.80) | (1.54, 0.43, −0.32) | 44 | cage + Fear left (Fear eyes y≈681), Void face 3/4 (eyes y≈354), corner back-right, magician hidden behind the Void |
| `KICK` | (1.70, 1.00, 7.80) | (1.55, 1.20, 0.10) | 50 | s20b03–b04: Fear lower-left (eyes y≈730), cage + TIME-OUT tag left, Void face 3/4 (eyes y≈460, `head.yaw +0.35` cheat), magician at PEEK bent over its back at right, kick foot on his chest (y≈649) |
| `LAYERED` | (7.92, 1.10, 2.86) | (5.71, 0.89, 1.84) | 44 | s18b06 from behind the magician (foreground right, hat), the Void's flank middle, Fear far left |
| `OPEN` | (−9.09, 1.20, 9.01) | (1.98, 0.58, −1.16) | 44 | s17b01 drift start: cage + Void small, far ahead (Fear y≈655, Void eyes y≈485); drift 2 m toward the cage |

Singles (◇): `FEAR_CU` `ROOM.shot(fear.eyes, {dist: 1.2, yaw: 60 (from the Void side) … −40 (from the front), pitch: 2,
fov: 33, screenY: sy(450)})`; `VOID_LOW` from Fear's eye height (0.65) beside Fear looking up: pos ≈ FOUT + (0.15, 0.65, 0.35),
look = void.eyes, fov 33–44; `MAG_MED` `ROOM.shot(mag.head, {dist: 2.3, yaw: 20…40, pitch: −6, fov: 33, screenY: sy(340)})`
(he faces Fear/screen-left, 3/4 to camera); `CORNER` `ROOM.shot(ROOM.M.CRASH.p + y 0.6, {dist: 3.2, yaw: −15, pitch: 8,
fov: 44, screenY: 0.5})`; `COSMOS_WIDE` `ROOM.shot([1.3, 1.3, 0.35], {dist: 6.5, yaw: −45, pitch: 6, fov: 54, screenY: 0.48})`.

---------------------------------------------------------------------------------------------------------------------

## 4. Per scene, per beat

Notation: **CAM** camera (preset / numbers, move), **BLOCK** positions/facing/posture, **ACT** the acting moment to
land, **⏱** timing anchors. "→" = move/ease. Faces must sit in the y ranges given (the script's numbers).

### s01 running_from_the_void (0.0–9.2) — golden dusk, tod 0 → 0.03, voidSky 0.5, look s01
Chase on the upstream path; the user (phone in LEFT hand, RIGHT arm pumping) runs downstage toward camera; the Void
plods 5–6 m behind, down the crest; ground speed ≈ 1.1 m/s for both (cycles at full run / waddle), camera dollies back
at the same speed from `FRAME0`.
- **b01 (0.0–2.6, silent; frame 0 = t 0)** CAM `FRAME0`, dolly back with them, no drift on frame 0. BLOCK user at
  (2.35,−6.4) running, Void on the crest (3.3,−12.4), feet on `groundAt`; Void's RIGHT hand half-raised "wait", LEFT
  pinching the hem (`extra.hem` 0.5). ACT frame 0: user mid-stride, eyes OPEN (no blink within ±4 frames of t=0), sob
  face, tears flying; Void hopeful (lids high, brow-wisps up in the middle, small 'o'). ⏱ `T('s01b01')+0.4` (≈1.0 s)
  look back over the LEFT shoulder (`body.lookBack` 0.85; eyes lead, head 3 frames later), gasp, eyes snap forward.
  Title over the sky y 110–300 (burned in by subtitles) — keep that band free of the hood and of bright seeds.
- **b02 (2.6–5.5) "So, let's say there's a Twitter user..."** CAM continue the dolly, drift 0.3 m closer (face y≈420).
  Title fades over `T('s01b02')`…`+1.0`. ⏱ insert from `T('s01b02.end')-1.4` to `T('s01b03')` (≈1.5 s): phone
  INSERT (camera on `user.phone` +Z axis 0.24 m, rolled with the phone, screen y 300–800): `screen: 'feed'`, a tear lands
  on the sad grey post and blurs it (scene overlay), the thumb flicks the feed twice (`scroll`, `tap` pulses).
- **b03 (6.1–8.7) "crying, and running from the ~void."** CUT CAM `CHASELOW` (24 mm low wide; push the Void 1 m closer
  so its hood reaches y≈170). ACT on "crying" a sob shakes the shoulders (`face: 'sob'`, eyes squeezed); on "void"
  (≈ `T('s01b03.end')-0.5`) the frantic look back: eyes lock 6 frames, `scream` face; the Void brightens, two finger
  wiggles of its hand, then freezes mid-wiggle as the user screams; outer brow-wisps sink; star-breath motes per step.

### s02 and_jesus_appears (9.2–25.4) — tod 0.03 → 0.08
- **b01 (9.5–11.7 + 1.3 pause) "And let's say Jesus appears..."** CAM `BEND` locked (camera upstage looking sunward,
  sun behind the bend; `sunShift` so the disc is right of where Jesus will stand). Empty; one thought-seed floats down,
  bobs, drifts off. Off-screen footsteps/sobs pan from frame **right** (MIRRORED: the user approaches from upstage =
  camera-right).
- **b02 (13.0–13.7) "^Now."** Jesus is simply there at J0 on the first frame of the word (3-frame golden shimmer + a
  small puff of warm sparkles, no flash, no halo). Mid-stroll: `walk.style 'stroll'`, both arms `behind`, head pitch
  −0.2 (up at the sky), `face 'content'`, half lids. Face y≈386.
- **b08 (14.0–15.2, silent)** same frame: two stroll steps J0 → J1 (≈0.9 m), slow breath, one slow blink, smile constant.
- **b03 (15.2–16.0) USER scream** CUT CAM `ARRIVE` (low side two-shot). BLOCK Jesus at J1 frame-LEFT (cheat his yaw
  +0.5 toward camera), the user bursts in from frame-RIGHT running toward him (from stage (0.5, −0.6) to USKID).
  ACT user: head snaps forward, pinpoint pupils, tall O mouth, body jolts upright, phone pops up and is caught (LEFT
  hand). Jesus: small surprised blink, brows lift, polite head tilt — no step back.
- **b04 (16.0–18.2, silent)** hold `ARRIVE`, tilt down with the fall (user face settles y≈620). User: `sit` 0→1 over
  0.75 s from USKID (`sitPath 'fall'`, phone held up high), slide 0.5 m to U, twist round to face the Void (yaw
  −0.74 → 2.45 increasing — the face passes the lens), scoot back twice (`scoot`) until the back meets Jesus's shins,
  RIGHT hand shoots up `defend` palm out (tremble), LEFT `clutch`. Jesus looks down, brows lift (inner up), soft 'oh',
  hands come out from behind his back, open. The Void lumbers in from upstage toward V (offscreen until b05).
- **b05 (18.2–19.9, silent)** CUT reverse, axial: low angle from just behind the user's raised RIGHT hand (hand soft
  in the foreground y≈700) up to the Void (eyes y≈260): pos ≈ U + (0.25, 0.95, 0.15) stage, look = void.eyes, fov 44.
  The Void arrives and stops on one foot at V−0.15 (toward the user), wobbles, settles, slow blink at the palm, outer
  brow-wisps sink, lids to 70 %, lower lids up a touch, hand back into the sleeve, one tiny half-step back to V.
- **b06 (19.9–22.4 + 1.4) "And he sees all of this."** CUT `JESUS_CU` at J1: `EDGE.shot(jesus.eyes, {dist 1.6 → 1.35,
  yaw 70, fov 33, screenY sy(420)})` slow push. ACT gaze to the user 12 f (inner brows up), flick to the phone 6 f,
  saccade up to the Void, recognition (outer brows lift, eye crinkle, mouth corner), back to the user; **blink on
  "this"** (thought change), eyes open bright, mouth corner tucks: an idea; small nod.
- **b07 (23.8–25.4, silent)** CUT medium wide at the seated user's eye height = `OTS` lowered to y 0.95: user lower-left
  foreground, Jesus steps past them on the camera side (J1 → (−0.6, 1.4) → (−0.1, 0.4)), RIGHT palm-down "one sec" + nod
  in passing without breaking stride. The Void (upper-middle, eyes y≈240) glances over its LEFT shoulder (toward
  camera side) for someone behind it — nobody — eyes back, round; hands knot at its middle. User: eyes follow him, the
  raised hand bends at the wrist, mouth closes then falls open.

### s03 the_whisper (25.4–43.8) — tod 0.08 → 0.14
- **b01 "So Jesus walks right up to the void,"** CAM pair two-shot from the camera side ◇
  `EDGE.shot([0.5,1.7,−0.9], {dist 5.0, yaw −5, pitch 3, fov 44, screenY sy(420)})`. Jesus walks in from frame-left
  (continuing his s02b07 walk; same walk phase function) to JV with a little hop on the last step, looks up beaming.
  The Void recoils a touch (`recoil`), eyes wide, brow-wisps up and apart, small 'o'; a star mote pops off its shoulder.
- **b02 USER "Uh. Sir? That's the void."** CUT `USER_CU` (speaking → readable face; MIRROR of the script's
  "three-quarter profile": the pair are off-frame right, the user's eyes dart frame-right). Leans forward on the propped
  LEFT hand, eyes flick Jesus/Void ×2, feeble `flap` of the raised hand, on "void" mouth wide, two tiny head shakes.
- **b03 "puts his arm around it,"** back to the two-shot, tighter (dist 3.6). Jesus's **LEFT arm** `around`, target =
  void `sideR` + (0, 0.35, 0) (palm on its velvet curve, ≤ 0.5 m from his shoulder), settles with a pat, eyebrow bounce.
  Void freezes: eyes drop to the arm, to his face, to the arm; two quick blinks; hands float up 4 cm and sink; shoulders
  up (`shrug` 0.4).
- **b04 "and starts whispering in its ear."** slow push to `WHISPER` (heads y≈330–420). The Void lowers its hood toward
  him (`whisperPose(-1, 0.8…1.0)` bends toward its right = toward Jesus) so its `earR` comes within 0.15 m of Jesus's
  mouth; Jesus on tiptoe (0.8), **RIGHT hand cupped** (`armR 'whisper'` = whispers to his left), conspiratorial brow hops.
- **b05 JESUS[whisper] (3.4 s)** CUT `VOID_CU` close on the bent Void (eyes y≈380), Jesus's cupped hand + beard soft at
  frame-left; very slow push. ACT the staged read at +0.0 / 0.8 (one outer brow-wisp up) / 1.4 (eyes slide to him,
  narrow) / 2.0 (lower lids push up, mouth pressed flat) / 2.6 (crescent corners twitch twice) / 3.2 (eyes squeeze to
  upturned arcs). Jesus presses his lips between phrases, one tiny shoulder shake.
- **b06 "Nobody knows what he said. I have ^theories."** pull back to `OTS` (user small, soft lower-left). Void: hand
  clamped over its mouth (`cover_mouth`), whole body jelly-quiver (`extra.laugh` 0.12 + `bounce` noise ≤ 1 cm), eyes wet
  arcs, `extra.stars` ×1.6, feet shuffle-dance under the hem (`hem` 0.3). Jesus back on his heels, LEFT arm still
  around it, RIGHT hand at his belt, innocent smile, one "wait for it" nod. User: phone held up in front of the face
  (`shield`), one slow blink.

### s04 cosmic_laughter (43.8–60.4) — tod 0.14 → 0.19, look s04 (more bloom for stars)
- **b01 (0.9 s silent)** CAM close two-shot of the heads, locked ◇ `EDGE.shot([0.45, 1.85, −0.8], {dist 2.4, yaw −20,
  fov 33, screenY sy(380)})`. Everything stops; the Void dead still behind its hand, eyes round, slow blink, lower lids
  twitch. Jesus still, lips pressed.
- **b02 VOID snort** same frame: shoulders jolt once; ONE star pops between its fingers (`Particles` burst count 1 at
  `T('s04b02')+0.1`, from void `mouth`), arcs up, twinkles out.
- **b03 VOID giggle** slight push (dist −10 %): body bobs per giggle; TWO stars squeeze out (two births at +0.3, +0.75).
  Jesus giggles silently, hand on chest.
- **b04 VOID laugh_maniacal "(HA!)"** **CUT ON THE FIRST FRAME OF THE BURST** to ◇ low angle at Jesus's chest height,
  28 mm: `EDGE.shot([0.55, 1.95, −0.85], {dist 4.2, yaw −28, pitch −10, fov 54, screenY sy(340)})` (Void eyes y≈220,
  Jesus face y≈470 frame-left, star pocket above). Hand flies off, hood snaps back, huge starry crescent (`VX('laugh')`,
  `extra.laugh` 1), arms `belly`.
- **b05 + b06** hold, 5° orbit (yaw −28 → −23). Rocks, one fat leg stamps (`walk` blip), slaps its cloak. Jesus wipes an
  eye (`wipe_eye`).
- **b07 + b08 "So hard, it's coughing up stars..."** CUT `VOID_CU` on the mouth (mouth y≈430). `extra.cough {t0:
  T('s04b07')+0.3, t1: T('s04b08.end'), rate 10}`; eyes pop open at the first puff, it looks at the stars, laughs harder.
- **b09 + b10 "and little ^galaxies."** medium on both (◇ the b04 low angle at dist 3.4) then a quick follow-pan down:
  the dinner-plate galaxy (0.3 m) pops out on the big hiccup (eyes cross for 4 f, hand misses it), bounces once at stage
  (0.4, ·, −0.2) and rolls toward the user, out of frame left-low. Jesus leans back to let it pass his nose, 'ooh'.
- **b11 VOID laugh_maniacal (peak)** CUT wide 28 mm = `OTS` with fov 54 (user head y≈680 lower foreground). The Void
  rears to full height (`stretch` 0.06), arms wide, the big cough → the beach-ball galaxy launches from the mouth and
  sails up and over toward camera-top, settling at `EDGE.GALAXY.from` (world (1.2, 6.2, 0.9)) by `T('s04b11.end')`
  (from then on `galaxyAt`). Then it doubles over, LEFT hand on Jesus's shoulder for support, squeaky wheezes. Jesus
  pats its back in rhythm (`pat`), laughing (b12 laugh_soft overlap), one glance up at the galaxy. User flattens back on
  the elbows, eyes track the galaxy up, jaw drops.
- **b13 (1.7 s silent)** CUT `USER_LOST` at sneaker height (camera y 0.25, sneaker in the foreground y≈800, user face
  y≈400 looking frame-right/up, the pair small soft upper-right). The little galaxy rolls in from frame-right, spirals to
  a stop against the sneaker (stage ≈ (−0.85, 0.02, 0.85)), wobbles like a coin, lies flat. User looks down at it, then
  slowly back up at the pair; one slow blink; brows can't decide (`browAsym`).

### s05 a_pretty_good_sense_of_humor (60.4–77.8) — tod 0.19 → 0.25
- **b01 "Then Jesus looks at the Twitter user,"** `JESUS_CU` medium (dist 2.4, face y≈400), his left arm still around
  the Void (soft, chuckling aftershocks behind). Knuckle wipes one eye; head turns to the user, eyes first; contented
  exhale.
- **b02 "who's, like, on their ass, with their hand up,"** CUT `JPOV` (axial high angle, user face y≈460, the little
  galaxy by the sneaker). User: legs splayed, toes up, leaning back on the LEFT (phone) hand (`prop`), RIGHT hand up
  trembling, hood half fallen back, cowlick up, `pant` 1.
- **b03 "and terror in their eyes."** slow push on the same axis to the eyes ECU (eyes y 360–520, dist ≈ 0.45): whites all
  round, pinpoint pupils, lower lids quivering, a tear; the big galaxy as a small turning highlight in each iris (scene
  overlay), NO blink.
- **b04 JESUS "The void's got a pretty good sense of ^humor."** CUT `LOWUP` (user's low angle: Jesus face y≈380, Void
  eyes y≈200, both looking down screen-left). Jesus: sheepish smile first, then RIGHT open palm toward the Void on "the
  void's", head tilts to it, big warm smile + nod on "humor". Void: straightens, brow-wisps lift, modest crescent,
  one "oh stop it" hand flap.
- **b05 (silent)** CUT `USER_CU` (face y≈420): nothing but one slow blink; a tear drips off the chin.
- **b06 JESUS "Tee-hee."** CUT `JESUS_CU` (face y≈400): `face 'teehee'`, `body.giggle` 1, `armR 'teehee'` (fingertips to
  lips, reach 0→1 in 0.3 s), bounce on the toes. Then (held into the cut) the smile stays a beat too long: one tiny eye
  dart, corners stiffen, slow blink.

### s06 what_the_actual (77.8–82.3) — tod 0.25 → 0.26
- **b01 USER "What the actual f***?!" + b02 Void giggle** CUT `USER_CU` (the script wants the pair in frame — a speaking
  user needs the readable angle; the giggles are heard). `body.jut` 1 + lean on "What", RIGHT hand `flap` on "actual",
  `face 'scrunch'` + `flinch` 0.5 on the bleep (3 f squeeze), glasses slip, pushed up (`armR 'glasses'`), glare.
- **b03 VOID cough** CUT `VOID_CU` medium (eyes y≈320): one tiny star 'pip' from the mouth, four fingers over the mouth,
  eyes slide sideways (excuse me).
- **b04 (1.6 s silent)** first 0.7 s CUT `USER_CU` locked: deadpan half-mast lids; the hiccup star rises into frame from
  lower-right and out the top, only the eyes follow it. Then CUT pair two-shot (s03b01 framing): Jesus brows rise, 'o' →
  pressed amused line, fair-enough nod; the Void, hand over mouth, eyes Jesus → user → narrow at the user (idea forming).

### s07 the_void_whispers (82.3–100.4) — tod 0.26 → 0.32
- **b01 + b02 + b03 "Now the void whispers into Jesus's ear."** CAM `WHISPER`, slow push to ~80 % over b01–b02.
  The Void at V bends `whisperPose(-1, 1.25)` (toward its right = Jesus) and its RIGHT hand cups beside its mouth
  (set by whisperPose); mouth makes small soft shapes (`speech` from VOID whisper vocal). Jesus at JV tilts his LEFT ear
  up toward it (`head.roll −0.12, yaw 0.25`), eyes up-and-aside, brows raised; mm-hm nods `head.pitch = 0.1·max(0,
  sin(2π·1.3·t))`. ⏱ at `T('s07b02')+1.0` the Void's eyes slide deliberately toward the user (screen-left/camera-left,
  `gazeYaw` toward the user, ~0.6 s ease) and park; upper lids flatten across the irises; hold. ⏱ `+2.2` Jesus's eyes
  flick to the user and back.
- **b04 "And the whole time,"** CUT ECU of the Void's eye nearest the user (eye y≈400, dist 0.8, fov 21): iris parked in
  the corner, the lid lowers 2 mm more, no blink.
- **b05 "it's side-eyeing the Twitter user."** CUT over-the-hood shot ◇ — **MIRRORED**: the glowing edge of the Void's
  eye in the upper-RIGHT foreground, the user beyond at left in focus (face y≈560): camera just behind/above the Void's
  head on the camera side, pos ≈ void.eyes + stage (0.25, 0.10, 0.35), look = user.eyes, fov 33. User meets the
  side-eye, flinches, scoots back 2.5 cm (`scoot` pulse); the iris tracks exactly 2.5 cm (gaze on user.eyes) and the lid
  lowers a hair. User fake-scrolls (`phoneUp` 1, fast `scroll`), peeks over the glasses once.
- **b06 + b07 "And Jesus is just nodding along."** CUT `OTS` (user small lower-left), then slow push on Jesus (face
  y≈400). Jesus: steady nods, "oh really?" brow lift, polite glance down at the user, back; small reassuring pat on the
  Void's sleeve (RIGHT hand `pat`), sympathetic wince, slow nod. Void keeps whispering, eyes locked on the user; when the
  user peeks, one brow-wisp lowers further. User shrinks behind the phone.
- **b08 VOID whisper (slower)** CUT `WHISPER` (profile-ish heads, y≈360): the whisper slows; the side-eye softens to hurt
  (outer lids droop, brow-wisps up in the middle, `extra.stars` 0.7, cupped hand sags). Jesus's suppressed smile fades,
  brows draw together, eyes lift to the Void's, slower nod.
- **b09 JESUS "No, I know. That ~hurts."** CUT `JESUS_CU` with the Void's hood edge soft in the right foreground; barely
  above a murmur; inner brows up, eyes glisten; RIGHT hand rises and rests flat on the Void's velvet (target = void
  `chest` side surface, contact!). Void (hood edge): one slow nod.
- **b10 (1 s silent)** CUT `USER_CU` closer (face y≈400): the flicker — squint drops, brows lift, two blinks (thought
  change), lips part, thumb stops; eyes slide away, mouth sets.
- **b11 JESUS "I'll ask."** CUT `JESUS_CU`; small inhale, eyes to the user and back, quick tight smile; the Void unbends
  (whisperPose amount 1 → 0 over 0.9 s) and its hood rises out of the top of frame.

### s08 do_you_have_a_moment (100.4–116.0) — late dusk, tod 0.32 → 0.35, voidSky → 0.78
- **b01 "Then the void crosses its arms, and ~scowls at the Twitter user."** CAM `LOWUP` 28 mm (Void eyes y≈220, Jesus
  face y≈450), slow push on the Void's face. ⏱ on "crosses its arms" (≈ `T('s08b01')+1.2`) arms `crossed` (L first, R
  4 f later, soft velvet whump), chin lifts (`head.pitch −0.08`); on "scowls" (≈ +3.0) `VX('scowl')` + the tell: inner
  brow-wisp tips up a hair, breath held (`breathe` 0). The rising star mote freezes at `+3.2` (§1.6). Jesus glances up at
  it, "okay, here goes" breath.
- **b02 (1 s silent)** CUT `JESUS_CU` medium (face y≈400), the scowling Void soft beside him, the frozen mote by its
  shoulder. Throat-clear (chin dips, chest lifts), two tugs on the sash, `clasp_chest`, bright formal smile.
- **b03 JESUS "The void says it wants to talk to you,"** same; Jesus takes one step toward the user: JV → JM (0.5 m),
  hands loosely together, on "the void says" a tilt of the head back toward it.
- **b04 "about something important."** CUT `VOID_CU` (eyes y≈330): on "important" chin up another notch, scowl deepens;
  its eyes flick down to the user's raised hand and back (a check). Jesus off-screen.
- **b05 "Do you have a moment?"** CUT `OTS` (back of the user's head + raised hand soft lower-left y 620–820). Jesus
  `clasp_chest`, head tilt, hopeful closed smile, wince on "moment", then still. Void: arms crossed, one slow blink; the
  mote still hangs. User: tiny backward lean.

### s09 hell_no (116.0–124.1) — tod 0.35 → 0.36
- **b01 (1.6 s silent)** `USER_CU` (face y≈420, phone glow on the chin): slow blink; eyes Jesus → the Void's scowl →
  Jesus; mouth opens, closes; jaw sets.
- **b02 USER "Hell no."** hold: `headShake(t, T('s09b02')+0.1)` → head.yaw + hairSwing, `face 'hellno'`, lips pressed after.
- **b03 USER "I'm not talking to that ~scary thing."** CUT `MASTER` (user y≈652, Jesus y≈422 at JM, Void y≈291). On
  "that" `armL 'jab'` (phone screen-first) toward the Void with tremble; on "thing" both arms `crossed` (phone tucked),
  chin up, scoot back 5 cm. ⏱ on "scary": the Void's 8-frame mask slip (lids lift, inner brow-wisps rise, crescent
  flattens and parts; breath out) and the frozen mote drops and winks out; then the scowl clamps back harder. Jesus's
  eyes close slowly on "scary", open; his head turns to the Void.
- **b04 (1.6 s silent)** hold `MASTER` (or the same with fov 40 for the "deliberately symmetrical" read): user lower-left
  arms crossed, lower lip out; the Void upper-right arms crossed, chin up — the same pose ten times bigger; Jesus at JM
  facing camera, eyes left (user) → right (Void) → left, eyes first, head follows, brows climbing each time.

### s10 rolls_its_eyes (124.1–139.1) — tod 0.36 → 0.39
- **b01 "So the void rolls its eyes,"** CUT `VOID_CU` (eyes y≈380): `VX('annoyed', eyeRoll(u))` with u over the whole
  line (~2.5 s, slow and theatrical), hood lolls back with it, mouth pressed sideways.
- **b02 + b03 "huffs, and puffs,"** hold, easing back to include the hood top and a thought-seed: two huffs
  (`extra.puff` 0→1→0 twice, `VX('huff')`, `body.swell`), each a violet nebula puff from the top of the hood; the second
  blows the seed away (scene seed sprite pushed by the puff).
- **b04 "and turns its back on the Twitter user."** CUT `MASTER`: three shuffling fat-legged steps V → VSIT, yaw −0.52 →
  2.62 increasing (face sweeps past camera, then profile, then its broad starry back), arms stay crossed, hood tilted up
  and away. Jesus (JM) mouth slightly open; user flinches at each stomp.
- **b05 (1.1 s silent)** same: it plops onto its backside (`sit` 0→1 in 0.35 s + squash/settle), hood droops forward,
  star motes lift off its back; ground thump; Jesus's eyebrow bounce; user blinks.
- **b06 "In fairness to the void, it hears that a ~lot."** CUT ROUND to the front of the seated Void (the side nobody
  sees), ◇ `EDGE.shot(void.eyes, {dist 2.2, yaw 120, pitch 2, fov 33, screenY sy(380)})` — still on the camera side of
  the U→V line (its hood points at local yaw 150°). Eyes downcast, outer lids droop, brow-wisps up in the middle, small
  sad pout; one star mote drifts down from the hood edge like a tear; one big finger picks at the grass.
- **b07 (1 s silent)** CUT `USER_LOST` (the Void's back soft at the right edge): six-frame guilt flicker (`face 'guilt'`),
  then jaw sets, eyes slide away, phone check. In the soft background the Void's shoulders sink a few cm; one last
  nebula puff.

### s11 oh_boy (139.1–150.0) — tod 0.39 → 0.41
- **b01 "And Jesus gets that look on his face."** CUT centred straight-on close of Jesus at JM (85 mm): `EDGE.shot(
  jesus.eyes, {dist 2.6, yaw 3, fov 21, screenY sy(420)})`, background melted (sunGlow 0.6). The look assembles over
  the line: brows up (inner highest) → lips stretch, teeth clench (`face 'awkward'`) → chin tucks.
- **b02 (2.4 s silent)** absolutely locked (drift 0). Only the eyes: dart to HIS LEFT = screen-right (the Void's back),
  hold 8 f; to his right = screen-left (the user), hold 8 f; **into the lens 12 f**; up to the sky 24 f. Slow inhale
  through clenched teeth lifts the shoulders (`shrug` 0.5). Use explicit gaze targets, not `dart` noise.
- **b03 JESUS "Oh, boy."** hold; through the clench (teeth stay together; `mClench` with lip-sync `talk` 0.4), one more
  left-right dart on "boy".
- **b04 "This is kind of ~awkward."** CUT `MASTER` (symmetrical): the Void's seated back at right, the user lower-left,
  Jesus middle. Grimace held; brows bob on "awkward", smile widens a notch; rocks heel-to-toe; hands clasp, unclasp,
  clasp. One nebula puff from the hood; user glares at the phone.

### s12 a_hand_on_the_shoulder (150.0–158.2) — tod 0.41 → 0.42, warms back up
- **b01 "So Jesus puts his hand on the void's shoulder."** CAM `BEHINDJ` (from behind Jesus; his head y≈400–520, the
  seated Void's back fills the upper frame). Exhale (grimace melts: shoulders drop), walk JM → JS (≈2.2 m, ~2.4 s) around
  the downstage side of the Void, lay the RIGHT palm flat on its RIGHT shoulder (target = void `shoulderR` + (0,0.03,0),
  `palm: [0,−1,0]` — must touch). No pat. The Void stiffens, then its shoulders ease under the hand.
- **b02 (2.5 s silent)** CUT AROUND to a 3/4 close on the Void's face as it turns over its RIGHT shoulder toward him:
  ◇ `EDGE.shot(void.eyes, {dist 2.0, yaw 41, pitch 0, fov 33, screenY sy(360)})` (its face turns toward the camera
  side; head.yaw −1.9 with body.twist −0.35 per the Void doc). Eyes arrive a beat before the hood; look at the hand,
  then at Jesus; scowl gone, lids half and soft, gentle closed crescent; slow blink; a mote drifts up past his hand
  (his hand in the lower foreground).
- **b03 (1.5 s silent)** CUT reverse on Jesus (face y≈380) from just over the Void's right shoulder (its shoulder edge soft
  in the foreground), ◇ pos ≈ void `shoulderR` + (0.15, 0.30, −0.20) stage, look = jesus.eyes, fov 33; side-lit warm rim
  (`keyYaw` cheat ≤ 0.15 to rim his hair). Soft eyes, small smile, one slow nod; thumb moves once on the velvet; a breath
  in and his eyes slide toward the user: one more try.

### s13 talk_to_me (158.2–203.8) — tod 0.42 → 0.50 (the heart; let it breathe)
- **b01 (1.6 s silent)** CAM medium wide at the seated user's eye height ◇ `EDGE.shot([−0.95, 0.85, 1.0], {dist 4.0,
  yaw 25, pitch 0, fov 44, screenY sy(500)})`. TIME CHEAT across the cut: at s13 start Jesus is already mid-walk at
  stage (−0.1, 0, 0.55) heading to K; arrives `+0.6`, kneels (`kneel` 0→1 over 1.1 s, right knee down), LEFT forearm on
  the raised knee (`knee_rest`), palms open. The Void's head turns back to face upstage by `+0.8`. User leans back,
  checks his hands, then his face.
- **b02 JESUS "Hey. It's okay."** CUT over the user's shoulder onto Jesus ◇ ("OTS-K"): pos ≈ (−1.65, 0.95, 2.05), look ≈
  (−0.55, 1.0, 0.45), fov 33 (cowlick soft lower-left above y 850; Jesus face y≈400; the seated Void's back soft behind
  him). Soft lids, inner brows up, tiny smile. User's shoulders: one sniff.
- **b03 "You don't have to talk to the void."** reverse: CUT over Jesus's LEFT shoulder onto the user ◇ ("OTS-J"):
  pos ≈ K + (0.30, 1.12, −0.10) stage, look = user.eyes, fov 33 (user face y≈420). Arms crossed, shoulders drop 1 cm;
  eyes flick past him to the Void's back and back; suspicious squint. Jesus (shoulder): small head shake.
- **b04 USER "Wasn't planning on it."** hold OTS-J: eye roll aside, one-sided `smirk` that doesn't reach the eyes.
- **b05 JESUS "Fair."** CUT OTS-K: nose laugh, eye crinkle, concession nod.
- **b09 JESUS "You were ~crying before it ever showed up, you know."** OTS-K tighter (user's blurred shoulder in the
  foreground): eyes soft, brows inner-up, slight nod down toward the phone under their arm.
- **b10 (1.8 s silent)** CUT OTS-J: the flicker — arms loosen, phone slides out and turns face-down in the lap
  (`armL 'lap'`, `palm [0,−1,0]`, `phone` 1 → 0 over 0.3 s: the cold glow leaves the face), lips press, chin dimples and
  trembles, eyes fill (`glisten`). Last 0.7 s: CUT OTS-K wider so the seated Void is visible small behind Jesus
  (y 250–350): its hood turns a few degrees, one eye peeks over its LEFT shoulder (lid high, brows lift: is it working?).
- **b06 JESUS "But what about talking to me?"** CUT `KNEEL2` (profile-ish two-shot, Jesus right, user left, Void behind
  him). Lean #1 (`body.lean` +0.10); fingertips to his own chest on "me" (`heart`). User leans back the same distance,
  double blink, brows lift, lips part (`face 'dawning'`).
- **b07 "And it doesn't have to be about the void."** hold `KNEEL2`: small backward flick of his hand toward the Void;
  user's arms uncross, both hands on the face-down phone, a thumb rubbing its edge.
- **b08 "It can be about ^you,"** slow push toward the user's face from KNEEL2 (to ~60 %, user face y≈430). Lean #2
  (+0.06), open palm toward them (`offer`, not touching). On "you" the user's eyes widen and go wet, inner brows up,
  RIGHT hand drifts to their own chest (`heart`).
- **b11 "and the emotions that you're feeling."** hold close on the user (lit only by dusk): flinch #1 on "emotions"
  (`flinch` 0.6 + 3 f squeeze), lip trembles, breath catches twice, a tear wells and rolls (`tears` 0.5), eyes search
  his face (L eye, R eye, mouth), tiny swallow.
- **b13 "Because I want to talk to you more about emotions!"** CUT straight-on close of Jesus (OTS-K with the camera
  moved onto the user↔K axis: pos ≈ (−1.45, 1.0, 1.95)): lean #3 (+0.06, closer than he realises), sparkly eager grin,
  `clasp_chest`; bright but unhurried. User (foreground edge): flinch #2, smaller; eyes stay on him.
- **b14 "Because that's ^meaningful to me!"** CUT `KNEEL2`: `heart` on "meaningful", eyes shining, one slow nod (`glow`
  1.2). User leans back exactly as far; tear rolls on; face goes still and soft; lips part: listening.
- **b15 "How does that sound?"** CUT straight-on Jesus close: the biggest all-teeth hopeful smile, two small nods, then
  still.
- **b18 (1 s silent)** hold: smile holds, nods stop, he settles back on his heel (give them room), one slow blink.
- **b12 USER "I just..."** CUT OTS-J (face y≈420): voice catches, lower lip trembles, the RIGHT hand lifts from the chest
  toward him and stops mid-air (`reach` 0.4). Jesus (edge of frame): completely still.
- **b16 (1.5 s silent)** CUT `KNEEL2`: Jesus still, one small "go on" nod. Nothing comes: the hand sinks on its own, eyes
  drop to the phone, the thumb turns it face-up — the cold glow returns (`phone` 0 → 0.85).
- **b17 USER "Nope."** CUT OTS-J (glow on the face): eyes on the phone, tight head shake, both hands yank the hood strings
  (`strings` preset): hood cinches tight (state change, holds to the end of Part One).
- **b19 (1.2 s silent)** CUT straight-on Jesus close: the hopeful smile slowly gives up (one blink, outer brows sink, smile
  shrinks to closed lips, tiny 'mm' nod).

### s14 blocked (203.8–217.8) — tod 0.50 → 0.52
- **b01 "And then the Twitter user gets up, and storms off."** CAM ◇ medium wide at kneeling height from behind-right of
  Jesus (axial to the path): pos ≈ (0.4, 1.0, −0.45), look ≈ (−3.6, 1.0, 3.9), fov 44 — Jesus kneeling in the lower
  foreground turning to watch (face y≈380–520), the user rising (`sit` 1→0 `sitPath 'rise'` 1.6 s), two angry brush-offs,
  then `stomp` away down the path toward the sun (EXIT_LOCAL), elbows out, hood cinched, eyes on the phone. Jesus's smile
  fades to a small open 'oh'.
- **b02 USER "Way. Too. Intense."** CUT tracking from the front: camera 2.2 m ahead of the user on the path, dollying back
  at the stomp speed (0.8 m/s), look = user.eyes, fov 44, face y≈400; Jesus small and kneeling behind them (screen-right of
  centre). Chin jab per word, thumbs stabbing the screen.
- **b03 "And blocks Jesus. On Twitter."** INSERT on `user.phone` (screen y 200–800, roll with the phone): `screen 'profile'`
  (bio "Would love to hear about your feelings.") → thumb hovers over Block 6 frames trembling → two stabs (`tap` pulses at
  `+0.9`, `+1.15`) → `'blocked'` ("You blocked Jesus.").
- **b05 (1.7 s silent)** CUT over Jesus's right shoulder (his profile frame-left, face y≈420; camera behind-right of him
  looking down the path): a cheerful ding from his sash; brows lift, he pats the sash, pulls out a small plain phone, holds
  it up. Then a 1.0 s full INSERT of his phone (scene prop): generic notification card with a plain speech-bubble icon,
  "@definitely_fine_lol blocked you." (card y 250–750), his thumb at the edge.
- **b06 "For talking about the void, too ^intensely."** CUT `JESUS_CU` at K from the front (face y≈420; the seated Void
  soft in the background — it is still seated at VSIT here): reads it once more, brows climb, small round 'oh', wince-smile,
  tucks the phone away and smooths the sash with great dignity, rueful nose exhale. RESTAGED: the user's last glance back
  from the rise is its own 1.0 s cutaway at `T('s14b06.end')-1.0`: ◇ `XWIDE`-style long lens over Jesus's shoulder toward the
  sun, the user tiny on the crest of the rise (`RISE_WORLD`), stops, glances back once, gone.

### s15 fair_enough (217.8–233.2) — tod 0.52 → 0.55
Between s14 and s15 (offscreen) the Void has risen and shuffled from VSIT to V15 — at s15 start it stands at V15.
- **b01 "And Jesus looks back at the void,"** CAM medium on Jesus rising (face y≈460) ◇ `EDGE.shot(jesus.eyes, {dist 2.2,
  yaw 15, fov 33, screenY sy(460)})` — the Void is visible soft behind him (the audience is in on it); `kneel` 1→0 with a
  dust-brush of the knee, turns (yaw −0.74 → 2.4) eyes first, tips his head way back. Then CUT `SIDE15`: the Void right
  there (eyes y≈230), hands clasped in front of its middle, lids at half, brow-wisps up in the middle, one slow blink.
- **b02 "and shrugs."** hold `SIDE15`: big honest shrug (`body.shrug` 0.85, both `shrug`, `face 'shrug'`), hold, drop, rueful
  smile up at it.
- **b03 "And the void pats him on the shoulder,"** `SIDE15` closer (dist 3.4): the Void's LEFT hand (camera side) pats
  Jesus's RIGHT shoulder (camera side): `armL {preset 'pat', target: jesus.shoulderR + (0,0.06,0), pat: 1}` — fingers cover
  his shoulder and half his back; he rocks slightly with each pat.
- **b04 "with a ~sad little smile."** CUT `VOID_CU` from in front of it over Jesus's head ◇ `EDGE.shot(void.eyes, {dist 2.6,
  yaw −20, pitch −6, fov 33, screenY sy(360)})`, its hand on his shoulder at the lower edge. The sad smile (mouth up, eyes
  don't follow); eyes slide toward the rise where the user disappeared (screen-left/camera-left) and back; slow blink.
- **b05 VOID sigh** hold, ease back to `SIDE15`: shoulders rise and settle, a lilac wisp from the hood; Jesus lays his RIGHT
  hand over the big hand on his shoulder (target = void `handL`, contact).
- **b06 JESUS "Too intense. Apparently."** `SIDE15` (face y≈440, eyes y≈240): deadpan looking straight up at it, brows up;
  the mouth corner gives him away. Void's eyes widen.
- **b07 VOID snort** CUT `VOID_CU` (eyes y≈340): surprised snort, a tiny star pops from the hood, eyes crinkle, hand over the
  mouth. Jesus at the frame edge grins up at it.

### s16 into_the_horizon (233.2–264.2) — sunset, tod 0.55 → 1.0, voidSky 0.7 → 0.9, look s16
- **b01 "So Jesus puts his arm around the void, and they walk off, toward the ^horizon."** First half: hold `SIDE15`-style
  side two-shot: Jesus steps round to the Void's LEFT (camera side), **RIGHT arm around it** (target = void `backLow` /
  `sideL` + 0.35 up), side-squeeze, crooked grin up; the Void leans into him (no startle), lids lower, its LEFT arm settles
  round his shoulders; both turn to face down the path (toward the sun) and start walking (screen-left). ⏱ on "walk off"
  (≈ `T('s16b01')+3.4`) CUT wide from behind them, 35 mm ◇ (camera 6–7 m behind on the path, y 1.6, looking down the path
  at the sun; heads y 420–480; Jesus screen-left): the path winding to the enormous sun, the sky galaxy (`galaxyAt`) over
  the path, the indigo pocket blending into the sunset.
- **b02 JESUS "So a neutron asks the bartender, how much for a drink?"** CUT side-on tracking medium from their left
  (camera side): camera = mid(t) + 3.0·(their left) + y 1.55, look = mid(t) + 0.6·forward + y 1.85, fov 33; faces y 330–430;
  they walk screen-LEFT, the sun glow at the left edge ahead of them. Jesus nearer the lens: free LEFT hand `explain`
  (palm out "ordering at a bar"), brows wiggle on "neutron", eyes slide up to the Void. Void bends its hood toward him,
  eager.
- **b03 (0.8 s)** hold: Jesus milks the pause (brows up, lips pressed); the Void waits, mouth pressed in an eager line.
- **b04 "For you? No ^charge."** hold: deadpan, little open-palm ta-da on "charge", mouth corner breaks. Void: beat, eyes
  wide, mouth falls open.
- **b05 VOID snort / b06 giggle** hold: snort with a little spray of stars from the hood, hand slaps over its mouth;
  giggle, eyes in arcs, shoulders bobbing. Jesus points at it (see?), then head back, open laugh, pats his own chest twice.
- **b10 "Jesus, smiling a bit, telling it more dumb jokes,"** stay on the tracking medium: the closed-mouth smile visible,
  free hand sketching the next setup in the air; the Void bending in.
- **b11 + b12 "and the void, slightly giggling, in the distance."** CUT extreme wide down the path from behind (silhouettes
  against the sun, y≈520), very slow push; `set.shots.finale` lens (22°) or the walk-off camera; `extra.rim` 1.6–2 on the
  Void so its eyes/edge read; little stars float up from its hood.
- **b13 (1 s)** hold; the push comes to rest; the Void's head leans against Jesus's.
- **b07 (1.3 s)** CUT `XWIDE` locked: pair tiny far down the path (y≈560), the USER tiny on the lilac hill upper-left
  (y≈330) hugging knees, hood cinched, phone glow on the face, looking at them, then down at the phone.
- **b08 (2 s)** INSERT over the knees: `screen 'blocked'` with the Unblock button large mid-screen (y 480–680); thumb drifts,
  hovers trembling, touches down lightly (`tap` 0.6 for 4 f), lifts away before it registers.
- **b09 "Not yet. But ^maybe."** CUT close on the user on the hill (face y≈420, chin on knees), camera on the sunward side
  looking back at them (front-lit by the low sun). "Not yet": thumb curls away, phone lowers, long breath out. ⏱ on "But
  maybe" CUT over their shoulder down to the two tiny figures walking into the huge sun (`notquite` face before the cut;
  no wave). **The last frame of s16: note the sun disc's screen position — s17 opens with Fear's lavender glow there.**

### s17 bonus_scene (264.2–273.9) — MIND_BACKROOM, dissolve in (1.0 s)
- **b01 "Okay. ^Bonus scene."** CAM `OPEN`, drifting ~2 m toward the cage over the beat (ease in/out, drift 0.3). Match
  Fear's small lavender glow (Fear at FIN, `extra.glow` 1.5) to the sun's position in the last s16 frame (move the drift
  start ±0.5 m to land it). Void: huge dark round shape beside the cage, rim-lit violet-teal, two soft starlight eyes
  (`extra.rim` 1.4). Magician crouched at LURK (hidden).
- **b02 "Now I'm imagining, when the void opened up the cage,"** CUT close on the latch with the Void's big hand coming down
  (◇ `ROOM.shot(anchors.cageLatch, {dist 1.0, yaw −30, pitch 6, fov 33, screenY sy(520)})`), then dolly OUT to `MASTER`
  (cage at left y≈420–760, Void eyes ≈ 230–350; the janitor corner back-right established — setup for the payoff).
  ⏱ hand down `+0.3 → +1.6` (`armR 'tip'`, `tip: true`, target `anchors.cageLatch`, `lean` 0.3, `crouch` 0.3); `opts.latch`
  0→1 over `+1.7 → +2.1` (click); `opts.cageDoor` 0→1 over `+2.2 → +3.2` (creak). The Void's eyes on Fear throughout.
  Fear at FIN gripping two front bars (`cageBar(±54°, 0.47)`), sobbing (`sob` 0.8), tuft drooping; at the click the
  sobbing stops dead (sob 0 in 2 f).
- **b03 "to my fear..."** CUT `FEAR_CU` from the front (face y≈470): Fear turns its head over its shoulder to the open door
  (toward the Void); eyes widen, heavy lids lift, a tear hangs on the lower lid; no breath; trembling.
- **b04 (1.2 s silent)** slow tilt up from Fear's face (ends y≈640) to the Void's face far above (eyes y≈220): camera at
  Fear's head height beside the cage door, fov 44, tilt pitch 0 → +38°. Fear has turned fully to FDOOR facing the Void;
  its eyes travel up the cloak, head a beat behind; the tear falls. Void: lids half, tiny gentle smile, utterly still; a
  few stars kindle in the hood (`extra.stars` 1 → 1.4).

### s18 the_magician_lurks (273.9–295.8) — look s18 (desaturated)
- **b01 "that right behind the big body of the void,"** CAM slow orbit around the Void's flank from Fear's side to its back
  at 1.2 m height: centre = void (y 1.4), radius 3.0, local yaw −30° → +85° over b01 (ease in-out; never past +85°). The
  velvet slides through the foreground (stars in the fabric); in its shadow the dented top hat rises like a periscope
  (magician at LURK, `crouch` 0.75 → 0.45).
- **b02 "the ~depression magician was lurking."** end of the orbit = `MAG_MED` (face y≈350): magician pressed against the
  back of the cloak, `armL 'edge'` on the Void's silhouette edge, peeking round it (moving LURK → PEEK, `body.peek` 0.6),
  sunken eyes slide toward Fear, too-wide grin, moustache twitch. Void still, bowed toward Fear.
- **b03 "With its dagger, and its numbing dust, ready."** `MAG_MED` slight low angle (face y≈330, hands y≈500): dagger up on
  "dagger" (`dagger_ready`), pouch shake on "numbing dust" (`pouch`, `extra.dust` pulse; grey glitter falls and a grey,
  desaturated floor patch grows where it lands — scene decal), fingers wiggle on "ready" (`tap`).
- **b04 "And it's, like, licking its lips, going,"** CUT close on the magician's face (3/4 front, dist 1.4, face y≈380):
  `face 'hungry'`, `speech false`, `extra.lick` 0→1 over 1.2 s starting on "licking", then `gloat`.
- **b05 MAGICIAN "Ooh. Fear looks very juicy."** hold: `face 'whisper'` with lip-sync (`talk` 0.6), eyes half-close on
  "juicy", head tilt, one gloved finger strokes the moustache.
- **b06 "Can't wait to knock Fear out."** CUT `LAYERED` (magician foreground right face y≈350, the Void's flank middle,
  tiny Fear at FDOOR far left y≈560, unaware, sniffling): pinch of dust, dagger higher, shoulders hunch with glee.
- **b07 (2.2 s silent)** CUT wide tracking behind the Void: the magician's high-kneed stage tiptoe (`walk.style 'sneak'`,
  0.40 m/s) along its back from PEEK a step toward its far side and back (pause on one foot, listening), coat-tails
  twitching, dagger by the ear; then tilt down to the floor (y 500–800): each step leaves a grey, colour-drained footprint
  decal. The Void: still, eyes soft on Fear, not a flicker.

### s19 the_corner_of_its_eye (295.8–305.7)
- **b01 (1.5 s silent)** CAM `VOID_LOW` from Fear's low angle (eyes y≈380); the grey hat brim bobs at the very right edge
  (magician at PEEK, out of focus). ACT without the head moving a degree, the eyes slide into the far corners toward
  screen-right (the magician): `face.gazeYaw` toward its left/the camera side (≈ ±0.65 per the Void doc, choose the sign
  that moves the irises screen-right), upper lids flatten, one inner brow-wisp twitches down, a tiny controlled breath.
- **b02 "And the void can see it."** hold: eyes parked, no blink, face kept sweet.
- **b03 "Just, in the corner of its eye."** CUT ECU on one Void eye in the LEFT foreground (eye y≈380), the hat brim + dagger
  glint soft at the right edge (camera beside the Void's head on the camera side, looking past its eye toward PEEK).
  Iris quivers in the corner; as the line ends it glides back toward Fear, lids lift soft, small smile returns.
- **b05 VOID hum** slow pull back to a held wide of the dramatic irony: `KICK` framing (fov 50→54): tiny Fear (face y≈650,
  at FDOOR) smiling up at the stars; the Void bowed over it humming (hood stars pulse with the hum); the magician at PEEK
  rising on his toes behind its shoulder, dagger high (face y≈250). Fear: tuft lifts, lids relax, tiny wobbly smile, wipes
  its nose on the scarf.

### s20 the_kick (305.7–331.2)
- **b01 "But instead of shouting, or making it obvious to my fear,"** CUT `VOID_LOW` close (eyes y≈360) for "instead of
  shouting"; then CUT a low two-shot: the Void's big hand mid-frame (y≈480) and Fear's upturned face lower-left (y≈640).
  The Void raises its RIGHT fingertip slowly in front of Fear; a star lights on it (glow sprite at the fingertip,
  `handR` + 0.12 along the finger); it draws the finger gently AWAY from the magician (toward screen-left / local −X+Z).
  Fear follows the star with its eyes, then — enchanted — two timid steps out of the cage: FDOOR → FOUT
  (`walk.style 'sneak'`, ~2 s), tuft perking.
- **b02 "that there's a creepy magician trying to stab it,"** CUT `MAG_MED` from the camera side (face y≈350, the Void's
  hood soft in the left foreground): last tiptoe step to PEEK, dagger high over his head, grin at maximum, eyes popping.
- **b03 "the void just..."** CUT `KICK` (locked): the magician at PEEK bent deep at the waist (`lean` 0.55, `peek` 1,
  `crouch` 0.15) leaning out over the Void's back toward Fear, dagger cocked by his ear, tongue out, coat-tails up. The
  Void: one slow serene blink (`head.yaw` +0.35 cheat keeps the face 3/4), fingertip star steady. Fear: eyes on the star,
  'o' mouth, tuft swaying with it. ⏱ chamber `extra.kick` 0 → −0.5 over `T('s20b04')-0.30 → T('s20b04')`.
- **b04 "kicks the magician in the chest,"** same `KICK`: ⏱ on "kicks" (`T('s20b04')+0.05`) kick −0.5 → 1.1 in 0.15 s
  (`ease.out`), `kickTarget = mag.anchor('chest')` (contact y≈649), hold 1.0 for 0.4 s, retract over 0.7 s. Top half does
  not move (kickLevel 1, smile + star steady). Magician: `face 'uhoh'` 0.3 s before contact, `kicked` 0→1 in 0.06 s at
  contact, launched along the Void's BACK axis; hat off and hanging a beat; he exits frame right within ~0.25 s
  (**flight clock pauses offscreen**, see b06). Fear: still on the star, tiny delighted smile.
- **b05 "with its ^fat leg."** INSERT at floor level (frame centre y≈500): ◇ `ROOM.shot(void.kickFoot rest point, {dist 1.4,
  yaw 40, pitch 2, fov 33, screenY 0.39})` — the fat leg retracts under the hem, the foot does a satisfied wiggle, the hem
  settles with a bounce.
- **b06 "And the magician goes flying, right into the buckets and the cleaning supplies,"** CUT wide following the arc,
  picking him up already in the air (y 300–500), limbs pinwheeling, mouth 'O', dagger and pouch flying, hat a beat behind.
  The flight resumes from where b04 left it and lands in `crashSpot` on "buckets" (≈ `T('s20b06')+2.9`; total screen
  flight ≈ 3.1 s — floaty rubber-hose arc, apex ~2.3 m). ⏱ impact `T_IMP` = the landing frame: CUT to `CORNER` medium
  (y 350–800) as he crashes in; set `opts.crash 1, crashT: t − T_IMP`; magician `kicked → crashed` over 0.2 s, then
  `dizzy`. On the crash a **0.6 s cutaway to `FEAR_CU`** from the Void side (face y≈430, the fingertip star at the top
  edge): flinch (tuft stiffens straight up, scarf ends jump, eyes dart to the sound); the star stays perfectly steady.
  Then back to `CORNER`.
- **b07 (2.9 s silent)** hold `CORNER` locked: bucket lands upside down on his head (BONK; `props.bucketHat` via
  `opts.bucketHat` on `mag.headTop`/`headUp`), mop flops over it, birdies (`dizzy` 1, `stars` 1), a bucket stops rolling,
  the dagger lands point-down and wobbles, the pouch puffs grey dust on him; silence; then the wet-floor sign (teetering all
  along) tips and lands flat on top of him: he goes rigid, then sags.
- **b08 MAGICIAN "...^Rude."** hold: lip-sync hidden under the bucket, moustache twitches below the rim, one gloved finger
  lifts weakly and drops.

### s21 whats_that_noise (331.2–340.9)
- **b01 (0.8 s)** `FEAR_CU` (face y≈430): offscreen a last broom slides and clatters (`opts.broomSlide`); second, smaller
  twitch (`startle` 0.5, tuft perk).
- **b02 FEAR "What's... what's that noise?"** hold: tiptoe, lean sideways to peek around the Void's bulk toward the corner
  (screen-right), eyes dart, brows up in worry (`listen`).
- **b03 "And the void just shrugs."** CUT medium two-shot ◇ `ROOM.shot([1.3, 1.45, 0.35], {dist 3.6, yaw −40, pitch 4,
  fov 44, screenY sy(470)})` (Void eyes y≈330, Fear face y≈620): the shrug (`shrug` 1, arms `shrug`, eyes up to the ceiling,
  tiny innocent pressed line, brow-wisps up) and, at the same time, a little sideways shuffle (0.25 m toward local +Z) that
  happens to fill Fear's line of sight to the corner. Fear's peek is blocked by velvet; it looks up.
- **b04 VOID hum "hm?"** CUT `MASTER` (wide): Fear peering up, the Void mid-shrug, head tilt, blameless blink; in the far
  background a single bucket rolls slowly across the floor from the corner (`opts.rollBucket` 0→1).
- **b05 FEAR "Oh. ...Okay."** `FEAR_CU`: two blinks, a last glance at the dark corner, looks up at the Void, tiny nod, tuft
  settles.
- **b06 (1.1 s)** the b03 two-shot: the Void brings both hands together in front of Fear and opens them slowly like a book;
  a glow begins in its palms. Fear looks down into them.

### s22 a_moment_with_my_fear (340.9–381.1) — look s22 (cosmos)
- **b01 "And then it goes right back to showing my fear the ^galaxies."** CAM close two-shot from low behind the Void's
  hands (hands y≈520, Fear's face just beyond y≈450): ◇ pos ≈ FOUT + stage (0.75, 0.75, 0.55), look = fear.eyes, fov 33. A
  spiral galaxy rises from the palms and turns; then splits into more drifting up (COSMOS `reveal` 0 → 0.3). Void's eyes on
  Fear's face, not the galaxy; Fear's eyes widen and fill with its light (`wonder`).
- **b02 "And the nebulae."** pull back to `COSMOS_WIDE` (both faces y 220–640): nebulae pour from its sleeves and cloak like
  slow luminous smoke (`reveal` 0.3 → 1 over b02–b03; BACKROOM `opts.cosmos` 0 → 1 in step: walls and cage fade to stars).
  Void lifts its arms slowly (`open`); Fear turns slowly in place, mouth open.
- **b03 (2.5 s)** CUT `FEAR_CU` from the Void side (face y≈430, nebula light, stars in its irises): brows un-knot and lift,
  heavy lids rise softly, mouth falls open, tears gather and one spills (`awe`, `extra.cry` 0.4), a breathless little
  laugh, trembling stops completely.
- **b04 FEAR "Why are you showing me this?"** hold: eyes search the Void's face, head tilt, a tear on each cheek. Void (soft
  above): lids lift to full, lower lids rise into soft crescents, brow-wisps up in the middle, one star-tear gathers.
- **b05 (2.1 s)** CUT close on the Void (eyes y≈330) → widen to the two-shot (Void eyes y≈250, Fear y≈600): the guilty flick
  of its eyes toward the corner (screen-right) and back, quick as a hiccup; soft crescents; gentle closed smile; its LEFT
  hand (camera side) comes down and rests weightless on Fear's RIGHT shoulder (camera side; contact). Fear leans its
  cheek against the big hand, eyes close for a moment.
- **b06 "To distract my fear, from the fact that the void had to kick the depression magician in the chest,"** slow pull
  back from the two-shot (eyes y≈250, face y≈560) until, far off in the dark corner beyond them (y≈700, screen-right), the
  evidence: the magician under bucket, mop and sign, birdies circling, one grey shoe twitches once. Camera on Fear's side
  of the room drawing back along local −X+Z; the Void's body between Fear and the corner "as if by accident"; Fear reaches
  toward a tiny drifting galaxy, back to the corner.
- **b07 "Just so it could have a moment,"** CUT `VOID_LOW` close (eyes y≈330), the little galaxy glowing in Fear's palm at
  the lower edge: lids soft at half, eyes wet with starlight, gentle smile, brow-wisps relaxed up in the middle.
- **b08 "with my ^fear."** CUT two-shot: Fear looks up, the Void down; galaxies turn; through the long pause a slow 3–4°
  orbit; one last star drifts down and settles on Fear's scarf; Fear notices it, delighted small smile, slow contented
  blink; the Void watches it find the star.
- **b09 (3.0 s) BUTTON** cuts at `+0.0` `CORNER` (bucket lifts an inch, a sunken eye peeks at the cosmos) · `+0.8` Void close
  (eyes y≈340, Fear's tuft at the lower edge): head perfectly still, one eye slides to the corner (screen-right), lid
  lowers to a flat unimpressed line, hold 10 frames · `+1.6` `CORNER`: the eye widens, the bucket sinks slowly back down,
  clunk at `+2.3` · `+2.4` Void: eye slides back to Fear, softens, slow blink.
- **b10 (1.7 s)** close on the Void straight down its hood axis (it looks into the lens): ◇ `ROOM.shot(void.eyes, {dist 2.4,
  yaw −60 (its hood direction), pitch −2, fov 33, screenY sy(360)})`: eyes slide from Fear out to the lens, slow wink,
  crescent curls up at one corner.
- **b11 "Tee-hee."** hold: the wink reopens, smile stays, gaze back down to Fear.
- **b12 + b13 (2.4 s) + TAIL (2.5 s)** pull back to the cosmos wide (`COSMOS_WIDE` from dist 6.5 → 9): the Void and Fear
  small at centre (y 450–650), the open cage faintly behind; keep y 150–310 calm dark nebula for the end title (burned in by
  subtitles). Void hand on Fear's shoulder, swaying slightly with its hum; Fear holds its little galaxy up; eyes close
  slowly, safe.

---------------------------------------------------------------------------------------------------------------------

## 5. Continuity table (state that must match across each cut between scenes)

| cut | positions | posture / arms / face | props, particles, light |
|---|---|---|---|
| s01→s02 | (chase upstream) → empty bend; user & Void offscreen | user running, sobbing, phone in LEFT fist; Void hem lifted, hand half-raised | title gone by s01b02+1.0; tod 0.03 continuous; seeds from the set |
| s02→s03 | Jesus mid-walk ≈ (−0.1, 0.4) → JV; user at U; Void at V | user seated, RIGHT hand up (`defend`), phone clutched LEFT; Void hands knotted at its middle; Jesus same walk phase function across the cut | phone glow on (feed); no galaxies yet |
| s03→s04 | Jesus JV, Void V (unbent), user U | Void's hand over its mouth, quivering; Jesus LEFT arm around it (stays until s05 end), heels down; user phone raised as a shield | `extra.stars` 1.6 on the Void → keep at start of s04 |
| s04→s05 | same | Void doubled over → wheezy aftershocks; Jesus laughing, hand on its back; user flattened on elbows, jaw open | big galaxy at `GALAXY.from` (galaxyAt); little galaxy flat at the user's sneaker; drifting stars from the laugh still fading (ease alpha to 0 by s05b02) |
| s05→s06 | same | Jesus "tee-hee" smile stiffening; Void giggly; user staring, RIGHT hand up, tear | little galaxy at sneaker |
| s06→s07 | same | Jesus amused pressed line; Void hand over mouth, eyes narrowed at the user | — |
| s07→s08 | Jesus JV, Void V full height | Jesus "I'll ask" tight smile looking at the user; Void unbent, hands lowering | tod 0.32 (s08 "late dusk") is the same ramp: no jump |
| s08→s09 | Jesus JM, Void V, user U | Jesus `clasp_chest` waiting; Void arms crossed + scowl, breath held; user RIGHT hand still up | frozen star mote hanging at its world point |
| s09→s10 | same | user arms crossed (phone tucked), chin up; Void arms crossed; Jesus facing camera at JM | mote gone (dropped on "scary") |
| s10→s11 | Void seated at VSIT (back to everyone) | Void arms crossed, hood drooping; user arms crossed checking the phone; Jesus JM | — |
| s11→s12 | Jesus JM → walking to JS | Jesus's grimace melts on the s12 exhale | — |
| s12→s13 | Jesus at JS (hand on the Void's RIGHT shoulder) → s13 starts with Jesus mid-walk at (−0.1, 0.55) | Void's head over its right shoulder (gentle smile) → turns back to upstage by s13b01+0.8 | — |
| s13→s14 | Jesus kneeling at K; user at U; Void seated VSIT | user hood CINCHED, phone face-up glowing; Jesus small closed smile | little galaxy still at the sneaker |
| s14→s15 | Jesus kneeling K; user gone (over the rise); Void seated VSIT in s14 → standing at V15 at s15 start (offscreen move) | Jesus phone tucked in the sash, sash smoothed | — |
| s15→s16 | Jesus standing at K facing the Void (yaw 2.4); Void at V15 facing him | Void's hand over its mouth after the snort, eyes crinkled | tod 0.55 continuous; galaxy starts its drift at s16b01 |
| s16→s17 | (dissolve) | — | **sun disc screen position (last s16 frame) = Fear's lavender glow position (first s17 frame)** |
| s17→s18 | Fear at FDOOR (inside, at the open door) looking up; Void at V bowed (lean 0.12, head pitch 0.25); magician crouched at LURK | Void small gentle smile; Fear tear just fallen | cage door open (`cageDoor` 1, `latch` 1) from here on; hood stars 1.4 |
| s18→s19 | magician at PEEK area, on his toes | magician dagger by ear, pouch ready | grey footprints on the floor persist (decals) through s22 |
| s19→s20 | same | Void humming, eyes back on Fear; Fear tuft lifted, small smile | — |
| s20→s21 | magician crashed at CRASH under bucket/mop/sign; Fear at FOUT; Void at V | Void's fingertip star still up (lower it during s21b03 shrug); Fear startled, tuft stiff | corner props in final wrecked state (`crash` 1, large `crashT`); birdies circling |
| s21→s22 | same (Void shuffled 0.25 m toward camera side in s21b03 — keep it) | Void's hands open like a book, glow in the palms; Fear looking down into them | glow in palms continues into the galaxy rise |

---------------------------------------------------------------------------------------------------------------------

## 6. Look and colour script

`st.look = lookFor(sceneId, st.set.look)` (marks.js): the set's look (EDGE ramps exposure/warm with tod; BACKROOM is
cool and dim) plus per-scene deltas:

| scenes | bloom | vignette | sat | exposure × | warm + | note |
|---|---|---|---|---|---|---|
| s01 | 0.55 | 0.14 | 1.10 | 1.06 | +0.08 | frame 0: bright, inviting peach-gold; ≥ 60 % warm pastel, dark Void ≤ 25 % of the frame |
| s02–s03 | 0.55 | 0.16–0.18 | 1.08 | 1.02–1.04 | +0.04–0.06 | golden dusk |
| s04 | 0.68 (threshold 0.85) | 0.18 | 1.10 | 1.02 | +0.04 | stars + galaxies bloom |
| s05–s07 | 0.55–0.58 | 0.20–0.22 | 1.06–1.08 | 1.0 | 0…+0.03 | |
| s08–s11 | 0.52–0.58 | 0.25–0.27 | 1.04 | 0.98 | −0.02…0 | late dusk; the armour/awkward stretch is a touch cooler and tighter |
| s12–s15 | 0.55–0.60 | 0.24 | 1.06–1.08 | 0.99–1.0 | +0.04…+0.06 | tenderness warms back up |
| s16 | 0.72 | 0.22 | 1.12 | 1.0 | +0.08 | deep sunset, richest colour, silhouettes with HDR rims |
| s17 | 0.72 | 0.36 | 1.04 | 1.0 | −0.06 | cool, cavernous; warm bulb + Fear's lavender as the only warmth |
| s18–s19 | 0.68–0.70 | 0.36–0.38 | 0.98–1.0 | 0.97–0.98 | −0.10…−0.08 | the magician drains colour (dust patches desaturate the floor) |
| s20–s21 | 0.70–0.72 | 0.32 | 1.04 | 1.0 | −0.05 | slapstick: slightly brighter, readable motion |
| s22 | 0.90 (threshold 0.62, radius 0.7) | 0.24 | 1.15 | 1.04 | +0.04 | cosmic violet / teal / rose with gold star cores; the warmest the bonus gets |

Colour script: **warm golden dusk** (peach, gold, mint, lilac; the Void a compact indigo pocket) → **late dusk**
(deeper rose and lilac, the pocket larger and starrier during the armour beats) → **sunset** (red-gold sun sinking, violet
blending with the Void's pocket, silhouettes) → dissolve → **cool backroom** (blue-violet dark, warm bulb, lavender Fear,
grey-blue magician) → **cosmic** (violet/teal nebulae, rose and gold accents, the room dissolving into stars).
Compression: no full-frame sparkle; particles sparse and slow (≤ ~40 visible sprites, alpha fades, no 1-frame pops
except the scripted single star pops); avoid large flat-black areas with fine noise.

---------------------------------------------------------------------------------------------------------------------

## 7. Animation principles for this film

1. **Face first.** Every beat has one face that tells the story — frame it, light it, hold it. Eyes lead every head turn
   by 2–4 frames; the head follows with a soft overshoot (~3 %), then settles.
2. **Blink on thought changes** (a new idea, a realisation, a decision), not on a timer: add `blinkAt` at those frames;
   suppress auto-blinks during held stares (terror, side-eye, the wink setup) and around frame 0.
3. **Saccades and holds.** Eye darts are fast (2–3 frames) with holds of 6–12 frames between; looks at a partner target
   the partner's eyes (`gaze: char`), not their head centre. Gaze changes on the Void are eye-only unless the script says
   the hood turns.
4. **Lids and brows carry the subtext.** Inner vs outer brows: worry = inner up; sadness = inner up + outer down; scowl =
   inner down; the Void's "tell" = inner tips up under a scowl. Lids: half-mast = disbelief/contentment, flat top lid =
   side-eye/scowl, lower lids up = smile reaching the eyes. Mouth corners move before the mouth opens.
5. **Anticipation → action → overshoot → settle** on every body move (sit, stand, kneel, cross arms, shrug, kick, turn).
   Anticipation 3–6 frames in the opposite direction; overshoot ≤ 10 %; settle over 6–10 frames. Big characters
   (the Void) move slower and settle longer (jiggle like a water balloon: squash 2–4 %, 2 damped wobbles).
6. **Holds let faces read.** After a punchline or a reaction, hold ≥ 12 frames with only breathing and a blink. Comedy
   needs the beat before and the beat after; honour every silent beat in the timeline.
7. **Secondary motion** lags the primary by 2–6 frames: Jesus's hair curtain and robe hem, the USER's cowlick, bob ends,
   hoodie strings (`hairSwing`), Fear's tuft and scarf ends (pass Fear a pose FUNCTION, clamped to the shot start), the
   magician's coat-tails and comb-over, the Void's hem and capelet. Never let secondary motion whip across a cut.
8. **Contact must touch.** Hands on shoulders, the arm around the Void, pats, the fingertip on the latch, the kick foot on
   the chest, Fear's cheek on the big hand: target the partner's anchor (+ a small surface offset) every frame and check a
   still at the contact frame. No floating hands, no hands sunk into velvet by more than 1–2 cm.
9. **Lip-sync is automatic** for on-screen speakers; shape it with `face.talk` (0.4 through clenched teeth, 0.6 for the
   magician's gloating whisper) and keep the face's emotion layered underneath. Narrator lines are voice-over: show the
   described action ON the described word.
10. **Compression-friendly motion:** no jitter or high-frequency noise on cameras (drift ≤ 0.4, slow fbm only), no
    per-frame random flicker on lights/particles, tremble ≤ 3 mm amplitude, particles born on a schedule and faded in/out
    over ≥ 4 frames.

---------------------------------------------------------------------------------------------------------------------

## 8. Set notes and risks (for the director / reviewers)

- **Verified with the real sets** (lab `staging`, ids 0,4,5,6,10–14): frame-0 composition, the Part-One master, the OTS, the
  whisper two-shot (Jesus at JV, Void at V with `whisperPose(-1,1.25)` → mouth 6 cm above his ear), the walk-off extreme
  wide, the backroom master, the kick wide (kick foot within 3 cm of the magician's chest), the layered shot, the opening.
  Shots marked ◇ were composed from these but not rendered.
- **USER was a capsule stand-in** in the lab (the rig landed during staging): re-check the seated user's head height
  (~0.85–0.95) in `MASTER`/`OTS`/`KNEEL2` (the user head y in those presets assumes ~0.95).
- **framed() bug** in core/camera.js (subject at 1 − screenY): the USER builder flagged it too; scenes must use marks.js
  `frame()` / `EDGE.shot()`. If core is ever fixed, marks.js is unaffected.
- **Hooded Void readability** is the main staging constraint: any camera > 50° off its hood direction loses the face. All
  presets respect it; `KICK` needs `head.yaw +0.35`.
- **Portrait width**: wide horizontal compositions do not fit; the script's "user at left, pair at right, both faces
  readable" side shots become `USER_LOST` (silent) or `USER_CU` (speaking). s07b05 and s02b03 are MIRRORED vs the script;
  s14b06's crest glance is a separate cutaway; the kick wide shows the Void's face at 3/4 rather than frontal.
- **Whisper proximity**: Jesus stands 1.1 m from the Void's centre at JV (inside its 1.1 m hem radius at floor level):
  check the robe/hem in wides; if they clip, move Jesus 0.1 m out and bend the Void slightly deeper (depth 1.35).
- **The flight in s20** is split across the leg insert (b05): the magician's flight clock pauses offscreen and resumes in b06
  so "goes flying ... into the buckets" happens on the words.
- **Timeline is ESTIMATED**: beat lengths will change with real audio; everything here is anchored to beat refs, but holds
  that depend on silent-beat durations (e.g. s11b02 dart counts, s20b07 slapstick sequence) must be re-fit to the real
  durations.
- **EDGE sky toward the anti-sun side** reads pink-lilac (belt of Venus) at tod 0 — warm enough for frame 0 with the s01
  look deltas; keep the Void's pocket compact (`voidSky` 0.5, `voidRadius` ~30) so the title sky stays warm.
