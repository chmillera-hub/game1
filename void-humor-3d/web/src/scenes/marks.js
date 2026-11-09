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
    FRAME0:   { pos: [2.46, 0.69, -3.26], look: [2.66, 1.40, -7.70], fov: 44, note: 'user (2.35,-6.4) face y440, Void on crest (3.3,-12.4) eyes y360; stand-in terrain' },
    CHASELOW: { pos: [2.18, 0.70, -1.85], look: [2.58, 1.31, -8.03], fov: 60, note: 's01b03 24mm low wide' },
    BEND:     { pos: [0.01, 1.08, -3.14], look: [-2.24, 0.88, 2.42], fov: 33, note: 's02b01-02 empty bend / Jesus appears, sun behind (reverse angle, set hero direction)' },
    ARRIVE:   { pos: [1.59, 0.60, 5.06],  look: [-0.73, 0.80, 2.00], fov: 44, note: 's02b03-04 low side 2-shot: Jesus frame-LEFT, user bursts in from frame-RIGHT' },
    MASTER:   { pos: [-1.70, 2.45, 7.89], look: [-0.25, 0.20, -0.83], fov: 44, note: 'high wide: user lower-left (back 3/4), Jesus centre, Void upper-right' },
    OTS:      { pos: [-2.92, 1.80, 5.57], look: [0.30, 0.56, -1.33], fov: 44, note: 'over the user\'s right shoulder onto Jesus + Void' },
    WHISPER:  { pos: [-1.09, 1.40, 3.30], look: [0.23, 1.22, -0.95], fov: 33, note: 'front 3/4 on the two heads (Void bent to Jesus\'s left ear); push to 80 %' },
    KNEEL2:   { pos: [-2.40, 0.70, 4.74], look: [-0.88, 0.68, 0.65], fov: 33, note: 's13 two-shot: user left (back 3/4), kneeling Jesus right, seated Void behind him' },
    BEHINDJ:  { pos: [2.78, 1.62, 0.52],  look: [1.45, 1.03, -1.09], fov: 33, note: 's12b01 behind Jesus, his hand on the seated Void\'s right shoulder' },
  },
  cam(name, over = {}) { const c = EDGE.CAM[name]; return { pos: EDGE.W(c.pos), look: EDGE.W(c.look), fov: c.fov, drift: 0.35, ...over }; },
  // the user's exit (s14) and the pair's walk-off (s16) follow the path downstage-left toward the sun
  EXIT_LOCAL: [[-1.3, 0, 1.4], [-2.25, 0, 2.44], [-5.0, 0, 4.4], [-9.0, 0.6, 7.5]],
  // the big laughed-up galaxy (s04b11 -> end of s16): hangs high above/behind the pair, then drifts very slowly
  // sunward along the path (~0.15 m/s) so it hangs over the path ahead of them in the walk-off. WORLD coords.
  GALAXY: { from: [3.1, 6.5, 4.2], to: [-1.5, 8.5, -24], size: 1.1 },
  // world-space set features the staging needs (see STAGING.md §0)
  PATH_WORLD: [[14, 0, 18], [8.8, 0, 11.6], [4.2, 0, 6.1], [1.6, 0, 2.8], [0.3, 0, 1.5], [-0.3, 0, -1.9], [-0.6, 0, -3.3],
    [-0.5, 0, -6.6], [-0.6, 0, -11.7], [-1.5, 0, -18], [-2.5, 0, -26], [-1, 0, -36], [0, 0, -50], [0, 0, -80]],
  TREE_WORLD: [2.0, 0, -5.2],           // rose-gold crystal tree beside the bend (s02b01), RIGHT of the path looking sunward
  CREST_WORLD: [7.4, 1.2, 10.3],        // s01: crest of the peach hill the Void plods over (path runs over it)
  RISE_WORLD: [-0.8, 0.5, -11.0],       // s14: the path crests a gentle rise (the lilac hill's shoulder); the user vanishes over it
  HILL_WORLD: [-3.6, 2.6, -10.0],       // s16b07: top of the lilac hill right beside the path (left looking sunward): the user sits there
});

// ------------------------------------------------------------------------------------------- MIND_BACKROOM
// Stage frame: origin = the cage centre, local +X = cage -> Void -> magician -> janitor corner (screen-right),
// local +Z = camera side, the screen-of-consciousness glow far away at local (-?, 3, -30) behind the Void.
// World yaw chosen so the master (camera at world +Z looking -Z) sees the line running back-right.
// If the BACKROOM set's anchors differ, call ROOM.fit(set) once in setup(): the frame snaps its origin to
// anchors.cageCenter and its +X axis toward anchors.voidSpot, so every mark below follows the set.
const RF = makeFrame([0, 0, 0], Math.atan2(2, 1));  // 1.1071 rad: local +X = world (0.447, 0, -0.894)
export const ROOM = Object.assign(RF, {
  M: {
    C:     { p: [0, 0, 0],        note: 'cage centre (radius ~0.42, 1.1 m tall, door faces +X toward the Void)' },
    LATCH: { p: [0.44, 0.6, 0.06], note: 'latch on the door edge, Void side' },
    FIN:   { p: [-0.12, 0, 0.1],  yaw: -0.45, note: 'Fear inside at the front bars, back to the Void, facing camera-left' },
    FOUT:  { p: [0.66, 0, 0.0],   yaw: Math.PI / 2, note: 'Fear just outside the open door, faces the Void (s18..s22)' },
    V:     { p: [1.95, 0, 0],     yaw: -1.02, note: 'the Void beside the cage, faces Fear cheated ~30 deg toward the camera side' },
    LURK:  { p: [3.15, 0, -0.75], yaw: -1.25, note: 'magician right behind the Void, hidden from Fear and the master' },
    FLANK: { p: [3.15, 0, 0.3],   yaw: -1.6, note: 'magician at the Void\'s back-left flank (camera side), bent over the hem toward Fear: kick contact' },
    LAND:  { p: [6.3, 0, 0.9],    yaw: -2.6, note: 'magician crash-landing spot in the janitor corner (crashed pose, head to the wall)' },
    CORNER:{ p: [7.0, 0, 1.1],    note: 'janitor corner: buckets, mop wringer, brooms, sign (walls behind at local +X/-Z)' },
    COSMOS:{ p: [1.2, 1.4, 0.1],  note: 'cosmos reveal centre (between the Void\'s hands and Fear), radius ~7' },
  },
  CAM: {
    MASTER: { pos: [-5.56, 1.77, 2.71], look: [2.24, 0.39, 0.10], fov: 44, note: 'world ~(0,1.8,6.2) looking -Z: cage+Fear left, Void beside/behind, janitor corner right edge, magician hidden' },
    KICK:   { pos: [-2.88, 0.70, 4.46], look: [2.86, 0.80, -1.09], fov: 44, note: 's20b03-04: Fear lower-left, Void face top, magician bent at its back-left flank (right); kick foot lands on his chest' },
    OPEN:   { pos: [-9.0, 1.6, 5.5],    look: [1.5, 1.4, -0.4],   fov: 44, note: 's17b01 far start of the drift: cage + Void tiny, the far screen glow right behind them' },
  },
  cam(name, over = {}) { const c = ROOM.CAM[name]; return { pos: ROOM.W(c.pos), look: ROOM.W(c.look), fov: c.fov, drift: 0.3, ...over }; },
  // kick: contact at FLANK chest (~1.0-1.1 m, the magician bent over), flight along KICK_DIR, apex ~2.3 m, ~0.85 s, lands at LAND
  KICK_DIR: [0.98, 0, 0.2],
  fit(set) {
    const a = set && set.anchors; if (!a || !a.cageCenter || !a.voidSpot) return ROOM;
    const c = a.cageCenter.isVector3 ? a.cageCenter : new THREE.Vector3(...a.cageCenter);
    const v = a.voidSpot.isVector3 ? a.voidSpot : new THREE.Vector3(...a.voidSpot);
    const yaw = Math.atan2(-(v.z - c.z), v.x - c.x);
    Object.assign(ROOM, makeFrame([c.x, 0, c.z], yaw)); return ROOM;
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
  const t0 = T('s04b11.end'), t1 = T('s16.end');
  if (t < t0) return null;              // before that, s04 flies it out of the Void's mouth to GALAXY.from
  const u = clamp((t - t0) / (t1 - t0));
  const a = EDGE.GALAXY.from, b = EDGE.GALAXY.to;
  return [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
}

// ----------------------------------------------------------------------------------- lens + frame layout
// fov is VERTICAL degrees (720x1280). "mm feel" as named in the screenplay -> fov to use.
export const LENS = { 18: 72, 24: 60, 28: 54, 35: 44, 50: 33, 85: 21 };
export const SAFE = { uiTop: 90, faceTop: 110, faceBottom: 850, subTop: 880, subBottom: 1060, titleTop: 110, titleBottom: 300 };
/** screenY (0..1 of frame height) for a pixel row, for framed({screenY}) */
export const sy = (px) => px / 1280;

// --------------------------------------------------------------------------------------------- post looks
// Per-scene base looks (st.look). Animators may modulate inside a scene (e.g. exposure +-0.05 on a cut)
// but keep the scene's values at its first and last frame so neighbouring cuts match.
const DUSK = { bloomRadius: 0.55, bloomThreshold: 0.8, sat: 1.08 };
export const LOOK = {
  s01: { ...DUSK, bloom: 0.55, vignette: 0.16, warm: 0.32, exposure: 1.08, lift: [0.035, 0.02, 0.045] },
  s02: { ...DUSK, bloom: 0.55, vignette: 0.18, warm: 0.3, exposure: 1.06, lift: [0.03, 0.02, 0.04] },
  s03: { ...DUSK, bloom: 0.58, vignette: 0.2, warm: 0.28, exposure: 1.04 },
  s04: { ...DUSK, bloom: 0.7, vignette: 0.2, warm: 0.26, exposure: 1.04, bloomThreshold: 0.75 },
  s05: { ...DUSK, bloom: 0.6, vignette: 0.22, warm: 0.26, exposure: 1.03 },
  s06: { ...DUSK, bloom: 0.6, vignette: 0.22, warm: 0.24, exposure: 1.02 },
  s07: { ...DUSK, bloom: 0.58, vignette: 0.24, warm: 0.22, exposure: 1.0 },
  s08: { ...DUSK, bloom: 0.58, vignette: 0.26, warm: 0.2, exposure: 0.98, sat: 1.06 },
  s09: { ...DUSK, bloom: 0.56, vignette: 0.26, warm: 0.2, exposure: 0.98, sat: 1.06 },
  s10: { ...DUSK, bloom: 0.58, vignette: 0.26, warm: 0.22, exposure: 0.98, sat: 1.06 },
  s11: { ...DUSK, bloom: 0.55, vignette: 0.27, warm: 0.22, exposure: 0.98, sat: 1.05 },
  s12: { ...DUSK, bloom: 0.62, vignette: 0.26, warm: 0.3, exposure: 0.99 },
  s13: { ...DUSK, bloom: 0.6, vignette: 0.26, warm: 0.3, exposure: 0.99 },
  s14: { ...DUSK, bloom: 0.58, vignette: 0.26, warm: 0.3, exposure: 0.98 },
  s15: { ...DUSK, bloom: 0.62, vignette: 0.26, warm: 0.34, exposure: 0.98 },
  s16: { ...DUSK, bloom: 0.75, vignette: 0.24, warm: 0.42, exposure: 1.0, sat: 1.12, bloomThreshold: 0.72 },
  s17: { bloom: 0.7, bloomRadius: 0.6, bloomThreshold: 0.7, vignette: 0.34, warm: -0.18, exposure: 1.02, sat: 1.05, lift: [0.02, 0.02, 0.04] },
  s18: { bloom: 0.65, bloomRadius: 0.6, bloomThreshold: 0.72, vignette: 0.36, warm: -0.24, exposure: 1.0, sat: 0.98, lift: [0.02, 0.02, 0.035] },
  s19: { bloom: 0.7, bloomRadius: 0.6, bloomThreshold: 0.7, vignette: 0.34, warm: -0.2, exposure: 1.0, sat: 1.0, lift: [0.02, 0.02, 0.04] },
  s20: { bloom: 0.68, bloomRadius: 0.6, bloomThreshold: 0.72, vignette: 0.3, warm: -0.14, exposure: 1.03, sat: 1.04, lift: [0.025, 0.022, 0.04] },
  s21: { bloom: 0.7, bloomRadius: 0.6, bloomThreshold: 0.7, vignette: 0.32, warm: -0.12, exposure: 1.02, sat: 1.04, lift: [0.02, 0.02, 0.04] },
  s22: { bloom: 0.9, bloomRadius: 0.7, bloomThreshold: 0.62, vignette: 0.24, warm: 0.06, exposure: 1.06, sat: 1.15, lift: [0.025, 0.015, 0.045] },
};

/** quick numeric check helper for labs/scenes: screen [x, y] of a world point with a camera. */
export function px(cam, p) {
  const v = (p.isVector3 ? p.clone() : new THREE.Vector3(...p)).project(cam);
  return [Math.round((v.x * 0.5 + 0.5) * 720), Math.round((1 - (v.y * 0.5 + 0.5)) * 1280)];
}
export { smooth };
