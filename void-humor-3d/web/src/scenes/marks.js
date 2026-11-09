// Shared staging constants — the code half of docs/STAGING.md. Import from every scene so cuts match:
//   import { EDGE, ROOM, todAt, voidSkyAt, galaxyAt, LENS, LOOK } from './marks.js';
// Pure data + pure helpers (no state, no Math.random). Not a scene module (the registry only loads sNN.js).
//
// Each location has a STAGE FRAME: local metres, y up, ground 0, where the action line runs along local X
// (screen-left -> screen-right), and the "camera side" is local +Z. In stage coordinates the camera is
// (almost) always at +Z looking toward -Z, exactly like a theatre audience. frame.W() converts to world.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { DEG, clamp, smooth, lerp } from '../core/util.js';

/**
 * frame(look, { dist, yaw, pitch, fov, screenY, drift, roll }) -> shot. Like core/camera.js framed(), but the
 * subject really lands at screenY (0 = top, 1 = bottom of the 1280 px frame; e.g. sy(420) for a face at y=420).
 * NOTE: core framed() shifts the aim the wrong way (the subject lands at 1 - screenY). Use this one (or pass
 * 1 - y to core framed). yaw/pitch in degrees, WORLD (yaw 0 = camera on +Z looking -Z, pitch + = camera above).
 */
export function frame(look, { dist = 2, yaw = 0, pitch = 0, fov = 35, screenY = 0.38, drift = 0.4, roll = 0 } = {}) {
  const y = yaw * DEG, p = pitch * DEG;
  const pos = new THREE.Vector3(look[0] + dist * Math.sin(y) * Math.cos(p), look[1] + dist * Math.sin(p), look[2] + dist * Math.cos(y) * Math.cos(p));
  const L = new THREE.Vector3(...look);
  const v = L.clone().sub(pos).normalize();
  const up = new THREE.Vector3(0, 1, 0).addScaledVector(v, -v.y).normalize();
  const fh = 2 * dist * Math.tan((fov * DEG) / 2);
  const d = (0.5 - screenY) * fh;                       // move camera + aim DOWN by d to raise the subject
  pos.addScaledVector(up, -d); L.addScaledVector(up, -d);
  return { pos: pos.toArray(), look: L.toArray(), fov, drift, roll };
}

function makeFrame(origin, yaw) {
  const c = Math.cos(yaw), s = Math.sin(yaw);
  const F = {
    origin, yaw,
    /** local [x,y,z] -> world [x,y,z] */
    W: (x, y = 0, z = 0) => (Array.isArray(x) ? F.W(...x) : [origin[0] + x * c + z * s, origin[1] + y, origin[2] - x * s + z * c]),
    /** local position as THREE.Vector3 (world) */
    V: (x, y = 0, z = 0) => new THREE.Vector3(...F.W(x, y, z)),
    /** world [x,y,z] | Vector3 -> local [x,y,z] */
    L: (p) => { const P = p.isVector3 ? [p.x, p.y, p.z] : p; const dx = P[0] - origin[0], dz = P[2] - origin[2]; return [dx * c - dz * s, P[1] - origin[1], dx * s + dz * c]; },
    /** local facing yaw (rad; 0 = facing local +Z = toward the camera side) -> world yaw */
    Y: (ly) => ly + yaw,
    /** local camera yaw in DEGREES (for framed(): 0 = camera on local +Z) -> world degrees */
    CY: (deg) => deg + yaw / DEG,
    /** frame() with a LOCAL look point + LOCAL yaw (deg; 0 = camera on local +Z). screenY is correct (0 = top). */
    shot: (look, o = {}) => frame(F.W(look), { ...o, yaw: F.CY(o.yaw ?? 0) }),
    /** explicit shot from local pos/look */
    at: (pos, look, fov = 34, extra = {}) => ({ pos: F.W(pos), look: F.W(look), fov, drift: 0.4, ...extra }),
    /** true if a world camera position is on the camera side of the action line (local z > zLine) */
    sideOK: (camWorld, zLine = 0) => F.L(camWorld)[2] > zLine,
  };
  return F;
}

// ------------------------------------------------------------------------------------------------ THE_EDGE
// World (what the EDGE set builds): the path runs along world -Z from the stage to the horizon and the huge low
// sun (sun at world -Z); upstream (nightward) it curves away to the north-east (+X,+Z), where the Void came from.
// The STAGE frame is rotated so that its camera side (local +Z) is world (-0.8, 0, -0.6): the master camera
// stands south-west of the stage with the low sun BEHIND-LEFT of it, so Jesus and the Void (who face the user,
// i.e. sunward) are front/3-4 lit, the user (facing nightward) is golden-backlit, and reverse angles on the user
// look into the sunset. In stage coordinates the user sits downstage-left, the Void + Jesus stand upstage-right.
//   local +X = world (-0.6, 0, 0.8)    local +Z = world (-0.8, 0, -0.6)    sun = local (-0.8, *, +0.6)
//   world -> local: x = -0.6 wx + 0.8 wz ... use EDGE.L(); local -> world: EDGE.W()
const EF = makeFrame([0, 0, 0], -Math.PI + Math.atan2(4, 3));   // -2.2143 rad (-126.87 deg)
export const EDGE = Object.assign(EF, {
  SUN_LOCAL: [-0.8, 0, 0.6],
  // marks: p = [x, y, z] local, yaw = local facing (rad; 0 faces the camera side +Z, +PI/2 faces screen-right +X)
  M: {
    U:     { p: [-1.3, 0, 1.4],   yaw: 2.45,  note: 'user sits on the path, faces the Void (back 3/4 to the master) s02b04..s14b01' },
    USKID: { p: [-0.55, 0, 0.6],  yaw: -0.74, note: 'user trips here (running downstage-left), slides to U, twists round' },
    J0:    { p: [-2.25, 0, 2.44], yaw: 2.4,   note: 'Jesus appears on "Now." (s02b02) at the bend, strolling upstage' },
    J1:    { p: [-1.64, 0, 1.77], yaw: 2.4,   note: 'Jesus after two stroll steps; the user lands with their back at his shins' },
    V:     { p: [1.0, 0, -1.1],   yaw: -0.52, note: 'the Void stands (s02b05..s10b04), faces the user cheated 12 deg to camera' },
    JV:    { p: [0.0, 0, -0.65],  yaw: -0.5,  note: 'Jesus at the Void\'s front-right = screen-left of it, 1.1 m from its centre (s03..s09); his LEFT arm goes around it; the Void whispers into his LEFT ear (whisperPose(-1, 1.25) lands its mouth 6 cm above his earL)' },
    JM:    { p: [-0.45, 0, -0.2], yaw: 0.05,  note: 'Jesus caught in the middle (s09b04, s10b05..s11): faces camera; Void at his left, user at his right' },
    VSIT:  { p: [1.15, 0, -1.35], yaw: 2.62,  note: 'the Void turned its back (3 shuffle steps) and sits (s10b05..s13), facing upstage-right' },
    JS:    { p: [1.74, 0, -0.37], yaw: -3.04, note: 'Jesus at the seated Void\'s RIGHT shoulder (camera side), back to the master (s12)' },
    K:     { p: [-0.65, 0, 0.7],  yaw: -0.74, note: 'Jesus kneels (right knee down) facing the user, arm\'s length (s13..s15b01)' },
    V15:   { p: [0.34, 0, -0.37], yaw: -0.74, note: 'the Void, standing right behind kneeling Jesus, faces him (s15)' },
  },
  // verified camera setups (LOCAL stage coords; vertical fov). EDGE.cam('MASTER') -> world shot. Lab: labs/staging.js
  CAM: {
    FRAME0:   { pos: [2.46, 0.69, -3.26], look: [2.66, 1.40, -7.70], fov: 44, note: 'user at (2.35,-6.4) face y~430, Void on the crest (3.3,-12.4) eyes y~400 on the real EDGE terrain (move it 1 m upstage / up the crest for ~360); feet y = set.groundAt' },
    CHASELOW: { pos: [2.18, 0.70, -1.85], look: [2.58, 1.31, -8.03], fov: 60, note: 's01b03 24mm low wide' },
    BEND:     { pos: [1.2, 1.15, -2.6],   look: [-2.25, 0.8, 2.44],  fov: 40, note: 's02b01-02 empty bend / Jesus appears: low sun at frame right behind the bend, path + pastel hills, eyes y~414' },
    ARRIVE:   { pos: [1.59, 0.60, 5.06],  look: [-0.73, 0.80, 2.00], fov: 44, note: 's02b03-04 low side 2-shot: Jesus frame-LEFT, user bursts in from frame-RIGHT' },
    MASTER:   { pos: [-1.70, 2.45, 7.89], look: [-0.25, 0.20, -0.83], fov: 44, note: 'high wide: user lower-left (back 3/4), Jesus centre, Void upper-right' },
    OTS:      { pos: [-2.92, 1.80, 5.57], look: [0.30, 0.56, -1.33], fov: 44, note: 'over the user\'s right shoulder onto Jesus + Void' },
    WHISPER:  { pos: [-1.09, 1.40, 3.30], look: [0.23, 1.22, -0.95], fov: 33, note: 'front 3/4 on the two heads (Void bent to Jesus\'s left ear); push to 80 %' },
    KNEEL2:   { pos: [-2.40, 0.70, 4.74], look: [-0.88, 0.68, 0.65], fov: 33, note: 's13 two-shot: user left (back 3/4), kneeling Jesus right, seated Void behind him' },
    BEHINDJ:  { pos: [3.72, 1.48, 1.67],  look: [1.46, 1.18, -0.84], fov: 33, note: 's12b01 behind Jesus, his hand on the seated Void\'s right shoulder' },
  },
  cam(name, over = {}) { const c = EDGE.CAM[name]; return { pos: EDGE.W(c.pos), look: EDGE.W(c.look), fov: c.fov, drift: 0.35, ...over }; },
  // the user's exit (s14) and the pair's walk-off (s16) follow the path downstage-left toward the sun
  EXIT_LOCAL: [[-1.3, 0, 1.4], [-2.25, 0, 2.44], [-5.0, 0, 4.4], [-9.0, 0.6, 7.5]],
  // the big laughed-up galaxy: launched in s04b11, it HANGS at `from` (high over the stage, a little upstage;
  // tiny bob only) until s16 starts, then floats ahead of the walkers down the path to `to` by s16b07. WORLD.
  GALAXY: { from: [1.2, 6.2, 0.9], to: [-1.5, 8.5, -24], size: 1.1 },
  // world-space set features the staging needs (see STAGING.md §0)
  PATH_WORLD: [[14, 0, 18], [8.8, 0, 11.6], [4.2, 0, 6.1], [1.6, 0, 2.8], [0.3, 0, 1.5], [-0.3, 0, -1.9], [-0.6, 0, -3.3],
    [-0.5, 0, -6.6], [-0.6, 0, -11.7], [-1.5, 0, -18], [-2.5, 0, -26], [-1, 0, -36], [0, 0, -50], [0, 0, -80]],
  TREE_WORLD: [2.0, 0, -5.2],           // rose-gold crystal tree beside the bend (s02b01), RIGHT of the path looking sunward
  CREST_WORLD: [7.4, 1.2, 10.3],        // s01: crest of the peach hill the Void plods over (path runs over it)
  RISE_WORLD: [-0.8, 0.5, -11.0],       // s14: the path crests a gentle rise (the lilac hill's shoulder); the user vanishes over it
  HILL_WORLD: [-3.6, 2.6, -10.0],       // s16b07: top of the lilac hill right beside the path (left looking sunward): the user sits there
});

// ------------------------------------------------------------------------------------------- MIND_BACKROOM
// Matches the BACKROOM set (web/src/sets/backroom.js LAYOUT): the action runs on one diagonal, cage/Fear front-left ->
// Void -> magician behind it -> janitor corner back-right (where the back wall z=-5 meets the right wall x=4.8).
// The screen-of-consciousness glow is far away at world +Z (behind the master camera: it lights faces from the front).
// Stage frame: origin = cage centre (world (-1.6, 0, 0.02)), local +X = toward the Void spot, local +Z = camera side.
// ROOM.fit(set) re-derives the frame from set.anchors.cageCenter / voidSpot (call it once in setup()).
const RF = makeFrame([-1.6, 0, 0.02], Math.atan2(0.52, 1.9));   // 0.2671 rad: local +X = world (0.965, 0, -0.264)
export const ROOM = Object.assign(RF, {
  // p = local [x,y,z]; yaw = local facing (add ROOM.yaw for world; the set's own yaws are given as wyaw)
  M: {
    C:     { p: [0, 0, 0],          note: 'cage centre (R 0.45, ~1.15 m tall to the ring); door faces local (0.70, 0.70): toward the Void and the camera side; set.anchors.cageLatch / cageDoor / cageInside' },
    FIN:   { p: [-0.1, 0, 0.12],    yaw: -0.55, note: 'Fear at the front bars (camera side), facing camera-left, its back roughly to the Void (s17b01-b03)' },
    FDOOR: { p: [0.2, 0, 0.2],      yaw: 0.78,  note: 'Fear turned round, just inside the open door, facing out toward the Void (s17b04 .. s20b01)' },
    FOUT:  { p: [0.70, 0, 0.72],    yaw: 2.09,  wyaw: 3 * Math.PI / 4, note: 'set.anchors.fearOutside: Fear in front of the Void, facing it (s20b01 .. s22)' },
    V:     { p: [1.97, 0, 0],       yaw: -1.05, wyaw: -Math.PI / 4, note: 'set.anchors.voidSpot: the Void faces Fear/the cage, 3/4 to a camera on world +Z' },
    LURK:  { p: [3.36, 0, -0.79],   yaw: -1.05, wyaw: -Math.PI / 4, note: 'set.anchors.lurkSpot: magician 1.6 m straight behind the Void (its default kick target distance)' },
    PEEK:  { p: [3.2, 0, 0.0],      yaw: -1.45,  note: 'magician leaning out past the Void\'s camera-side edge (s18b02, s19, s20b02-b03), still ~1.5 m behind it' },
    CRASH: { p: [6.49, 0, -2.58],   yaw: -1.05, wyaw: -Math.PI / 4, note: 'set.anchors.crashSpot: the bucket pile; crashed pose back to the corner, face to the room' },
    COSMOS:{ p: [1.3, 1.3, 0.35],   note: 'cosmos reveal centre (between the Void\'s hands and Fear), radius ~7' },
  },
  // the donkey kick sends the magician straight back along the Void's BACK axis: world (0.707, 0, -0.707) = local
  // (0.87, 0, -0.49), from LURK/PEEK to CRASH (3.6 m). Use set.flightPos(u, apex) for the root path.
  KICK_DIR_WORLD: [Math.SQRT1_2, 0, -Math.SQRT1_2],
  SCREEN_GLOW_WORLD: [-1.85, 2.2, 24],
  CAM: {
    MASTER:  { pos: [-4.28, 2.04, 5.80], look: [1.54, 0.43, -0.32], fov: 44, note: 's17b02 end / s21b04: cage + Fear left, Void face 3/4, corner back-right, magician hidden (crouched at LURK)' },
    KICK:    { pos: [1.7, 1.0, 7.8],     look: [1.55, 1.2, 0.1],    fov: 50, note: 's20b03-04: Void face 3/4 top-left (head.yaw +0.35 cheat), Fear lower-left, magician at PEEK bent over its back at right, kick leg into his chest' },
    LAYERED: { pos: [7.92, 1.10, 2.86],  look: [5.71, 0.89, 1.84],  fov: 44, note: 's18b06 from behind the magician (foreground right) past the Void\'s flank toward Fear (far left)' },
    OPEN:    { pos: [-9.09, 1.20, 9.01], look: [1.98, 0.58, -1.16], fov: 44, note: 's17b01 drift start from the screen side: cage + Void small, far ahead; drift ~2 m toward the cage' },
  },
  cam(name, over = {}) { const c = ROOM.CAM[name]; return { pos: ROOM.W(c.pos), look: ROOM.W(c.look), fov: c.fov, drift: 0.3, ...over }; },
  fit(set) {
    const a = set && set.anchors; if (!a || !a.cageCenter || !a.voidSpot) return ROOM;
    const c = a.cageCenter.isVector3 ? a.cageCenter : new THREE.Vector3(...a.cageCenter);
    const v = a.voidSpot.isVector3 ? a.voidSpot : new THREE.Vector3(...a.voidSpot);
    Object.assign(ROOM, makeFrame([c.x, 0, c.z], Math.atan2(-(v.z - c.z), v.x - c.x))); return ROOM;
  },
});

// -------------------------------------------------------------------------------------------- time of day
// EDGE opts.tod: continuous across every Part One cut (golden dusk -> late dusk -> sunset).
export function todAt(t) {
  return k(t, [['s01', 0.0], ['s08', 0.32, 'linear'], ['s16', 0.55, 'linear'], ['s16b11', 0.88, 'linear'], ['s16.end', 1.0, 'linear']]);
}
// EDGE opts.voidSky: how strongly the Void's indigo star-pocket bleeds into the sky around it (compact in s01).
export function voidSkyAt(t) {
  return k(t, [['s01', 0.5], ['s02', 0.6, 'linear'], ['s08', 0.62, 'linear'], ['s08b01.end', 0.78], ['s10b05', 0.72, 'linear'],
    ['s12', 0.6, 'linear'], ['s15.end', 0.6, 'linear'], ['s16', 0.7, 'linear'], ['s16.end', 0.9, 'linear']]);
}
/** world position of the laughed-up sky galaxy at t (null before it is coughed up). */
export function galaxyAt(t) {
  if (t < T('s04b11.end')) return null;   // before that, s04 flies it out of the Void's mouth up to GALAXY.from
  const u = smooth(clamp((t - T('s16b01')) / (T('s16b07') - T('s16b01'))));
  const a = EDGE.GALAXY.from, b = EDGE.GALAXY.to, bob = 0.12 * Math.sin(t * 0.4);
  return [lerp(a[0], b[0], u), lerp(a[1], b[1], u) + bob, lerp(a[2], b[2], u)];
}
/** spin (rad) of the sky galaxy sprite at t — use as the particle rotation so every scene matches. */
export const galaxySpin = (t) => t * 0.15;

// ----------------------------------------------------------------------------------- lens + frame layout
// fov is VERTICAL degrees (720x1280). "mm feel" as named in the screenplay -> fov to use.
export const LENS = { 18: 72, 24: 60, 28: 54, 35: 44, 50: 33, 85: 21 };
export const SAFE = { uiTop: 90, faceTop: 110, faceBottom: 850, subTop: 880, subBottom: 1060, titleTop: 110, titleBottom: 300 };
/** screenY (0..1 of frame height) for a pixel row, for framed({screenY}) */
export const sy = (px) => px / 1280;

// --------------------------------------------------------------------------------------------- post looks
// Per-scene look = the SET's look (it already ramps exposure/warm with tod) + these deltas:
//   st.look = lookFor('s05', st.set.look);
// Keep a scene's look constant across its own cuts unless a beat calls for it (then ease over >= 0.5 s).
export const LOOK = {
  s01: { bloom: 0.55, vignette: 0.14, sat: 1.1, exposureMul: 1.06, warmAdd: 0.08 },   // frame 0: bright, inviting
  s02: { bloom: 0.55, vignette: 0.16, sat: 1.08, exposureMul: 1.04, warmAdd: 0.06 },
  s03: { bloom: 0.55, vignette: 0.18, sat: 1.08, exposureMul: 1.02, warmAdd: 0.04 },
  s04: { bloom: 0.68, vignette: 0.18, sat: 1.1, exposureMul: 1.02, warmAdd: 0.04, bloomThreshold: 0.85 }, // stars + galaxies bloom
  s05: { bloom: 0.58, vignette: 0.2, sat: 1.08, exposureMul: 1.0, warmAdd: 0.03 },
  s06: { bloom: 0.58, vignette: 0.2, sat: 1.08, exposureMul: 1.0, warmAdd: 0.02 },
  s07: { bloom: 0.55, vignette: 0.22, sat: 1.06, exposureMul: 1.0, warmAdd: 0.0 },
  s08: { bloom: 0.55, vignette: 0.25, sat: 1.04, exposureMul: 0.98, warmAdd: -0.02 },  // armour on: a touch cooler
  s09: { bloom: 0.52, vignette: 0.26, sat: 1.04, exposureMul: 0.98, warmAdd: -0.02 },
  s10: { bloom: 0.58, vignette: 0.26, sat: 1.04, exposureMul: 0.98, warmAdd: -0.01 },
  s11: { bloom: 0.52, vignette: 0.27, sat: 1.04, exposureMul: 0.98, warmAdd: 0.0 },
  s12: { bloom: 0.6, vignette: 0.24, sat: 1.06, exposureMul: 1.0, warmAdd: 0.04 },     // tenderness warms back up
  s13: { bloom: 0.58, vignette: 0.24, sat: 1.06, exposureMul: 1.0, warmAdd: 0.05 },
  s14: { bloom: 0.55, vignette: 0.24, sat: 1.06, exposureMul: 0.99, warmAdd: 0.04 },
  s15: { bloom: 0.6, vignette: 0.24, sat: 1.08, exposureMul: 0.99, warmAdd: 0.06 },
  s16: { bloom: 0.72, vignette: 0.22, sat: 1.12, exposureMul: 1.0, warmAdd: 0.08 },    // sunset: richest
  s17: { bloom: 0.72, vignette: 0.36, sat: 1.04, exposureMul: 1.0, warmAdd: -0.06 },   // cool backroom
  s18: { bloom: 0.68, vignette: 0.38, sat: 0.98, exposureMul: 0.97, warmAdd: -0.1 },   // the magician: desaturate
  s19: { bloom: 0.7, vignette: 0.36, sat: 1.0, exposureMul: 0.98, warmAdd: -0.08 },
  s20: { bloom: 0.7, vignette: 0.32, sat: 1.04, exposureMul: 1.0, warmAdd: -0.05 },
  s21: { bloom: 0.72, vignette: 0.32, sat: 1.04, exposureMul: 1.0, warmAdd: -0.04 },
  s22: { bloom: 0.9, vignette: 0.24, sat: 1.15, exposureMul: 1.04, warmAdd: 0.04, bloomThreshold: 0.62, bloomRadius: 0.7 }, // cosmos
};
export function lookFor(id, setLook = {}) {
  const d = LOOK[id] || {};
  const o = { ...setLook, ...d };
  o.exposure = (setLook.exposure ?? 1) * (d.exposureMul ?? 1);
  o.warm = (setLook.warm ?? 0) + (d.warmAdd ?? 0);
  delete o.exposureMul; delete o.warmAdd;
  return o;
}

/** quick numeric check helper for labs/scenes: screen [x, y] of a world point with a camera. */
export function px(cam, p) {
  const v = (p.isVector3 ? p.clone() : new THREE.Vector3(...p)).project(cam);
  return [Math.round((v.x * 0.5 + 0.5) * 720), Math.round((1 - (v.y * 0.5 + 0.5)) * 1280)];
}
export { smooth };
