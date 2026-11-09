// Shared helpers for the bonus climax scenes s20 (the kick), s21 (what's that noise?) and s22 (a moment with my
// fear). Not a scene module (the registry only loads sNN.js). Everything is a pure function of t built from beat
// refs / word times, so the three scenes agree on: the fingertip star, the Void's spot (+ the s21 shuffle), Fear at
// FOUT, the magician's flight + wreck, and the janitor-corner state (crash, bucket hat, mop wig, sign, broom, roll).
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { CTX } from '../core/context.js';
import { clamp, lerp, smooth, ease, fbm1, DEG } from '../core/util.js';
import { ROOM } from './marks.js';

// ------------------------------------------------------------------------------------------- word timings
let LINES = null;
export async function loadLines() {
  if (!LINES) { try { LINES = await (await fetch('/data/lines.json')).json(); } catch (e) { LINES = {}; } }
  return LINES;
}
const norm = (s) => String(s).toLowerCase().replace(/[^a-z']/g, '');
/** absolute time of a word in a line beat (start, or end with {end:true}); falls back to a fraction of the beat */
export function W(beat, word, { end = false, occ = 0, frac = 0.5, alt = [] } = {}) {
  const L = LINES && LINES[beat];
  const t0 = T(beat);
  if (L && L.words) {
    const names = [norm(word), ...alt.map(norm)];
    let n = 0;
    for (const w of L.words) if (names.includes(norm(w.w))) { if (n++ === occ) return t0 + (end ? w.end : w.start); }
  }
  return t0 + frac * (T(beat + '.end') - t0);
}

// ------------------------------------------------------------------------------------------- small math
export const V = (a) => (a.isVector3 ? a.clone() : new THREE.Vector3(a[0], a[1], a[2]));
export const A = (v) => (v.isVector3 ? [v.x, v.y, v.z] : v);
export const add = (a, b) => { const p = A(a), q = A(b); return [p[0] + q[0], p[1] + q[1], p[2] + q[2]]; };
export const sub = (a, b) => { const p = A(a), q = A(b); return [p[0] - q[0], p[1] - q[1], p[2] - q[2]]; };
export const mix3 = (a, b, u) => { const p = A(a), q = A(b); return [lerp(p[0], q[0], u), lerp(p[1], q[1], u), lerp(p[2], q[2], u)]; };
/** stage-local direction -> world direction */
export function LD(x, y, z) { const o = ROOM.W(0, 0, 0), p = ROOM.W(x, y, z); return [p[0] - o[0], p[1] - o[1], p[2] - o[2]]; }
/** eased pulse 0 -> 1 -> 0: up over [a, a+up], down over [b-down, b] */
export function pulse(t, a, b, up = 0.15, down = 0.25) {
  if (t <= a || t >= b) return 0;
  return Math.min(smooth((t - a) / Math.max(1e-4, up)), smooth((b - t) / Math.max(1e-4, down)));
}
/** a damped bounce/jiggle that starts at t0: amp * e^(-d*dt) * sin(w*dt) */
export function jiggle(t, t0, amp = 1, w = 14, d = 6) { const dt = t - t0; return dt <= 0 ? 0 : amp * Math.exp(-d * dt) * Math.sin(w * dt); }

// ------------------------------------------------------------------------------------------- leak guard
// Props live in the shared BACKROOM scene (s17..s22). Each scene stamps the frame it renders; its own props collapse
// in onBeforeRender when the stamp is stale (another scene is drawing the room).
const STAMPS = {};
export function stamp(id, t) { STAMPS[id] = t; }
export const live = (id) => CTX.t === STAMPS[id];
const ZERO = new THREE.Matrix4().makeScale(0, 0, 0);
export function own(id, obj) {
  obj.traverse((o) => {
    if (!o.isMesh && !o.isPoints && !o.isSprite) return;
    const prev = o.onBeforeRender;
    o.onBeforeRender = function (...a) { if (CTX.t !== STAMPS[id]) this.matrixWorld.copy(ZERO); if (prev) prev.apply(this, a); };
  });
  return obj;
}

// ------------------------------------------------------------------------------------------- two-pass solve
// pass 0: every rig without gaze/head-follow (fresh anchors, nothing depends on another frame); mid(): frame the
// camera from those anchors and applyShot; pass 1: the real poses (catchlights see the final camera).
export function solve(t, list, mid = null) {
  for (const [ch, fn] of list) {
    if (!ch) continue;
    const p = fn(0);
    if (!p) continue;
    const q = { ...p, gaze: null };
    if (q.head) q.head = { ...q.head, follow: 0, look: undefined, track: 0 };
    ch.update(t, q);
  }
  if (mid) mid();
  for (const [ch, fn] of list) { if (!ch) continue; const p = fn(1); if (p) ch.update(t, p); }
}

// ------------------------------------------------------------------------------------------- camera aim
/**
 * aim(pos, P, px, py, fov): a shot from `pos` (world) whose (roll-free) orientation puts world point P exactly at
 * pixel (px, py) of the 720x1280 frame. Analytic: pitch from the vertical component, then yaw.
 */
export function aim(pos, P, px, py, fov = 33, extra = {}) {
  const tv = Math.tan((fov * DEG) / 2), th = tv * (720 / 1280);
  const nx = px / 360 - 1, ny = 1 - py / 640;
  const c = new THREE.Vector3(nx * th, ny * tv, -1).normalize();
  const d = V(P).sub(V(pos)).normalize();
  // pitch: d.y = c.y cos(th) - c.z sin(th)  (rotation about X applied to c)
  const Aa = c.y, Bb = -c.z, R0 = Math.hypot(Aa, Bb), phi = Math.atan2(Bb, Aa);
  const ac = Math.acos(clamp(d.y / R0, -1, 1));
  const cand = [phi + ac, phi - ac];
  const pitch = Math.abs(cand[0]) < Math.abs(cand[1]) ? cand[0] : cand[1];
  const wx = c.x, wz = c.y * Math.sin(pitch) + c.z * Math.cos(pitch);
  const yaw = Math.atan2(d.x, d.z) - Math.atan2(wx, wz);
  // camera forward (0,0,-1) after Rx(pitch) then Ry(yaw)
  const f0 = new THREE.Vector3(0, Math.sin(pitch) * 1, -Math.cos(pitch));
  // Rx(pitch) of (0,0,-1): (0, sin(pitch)*... ) careful: Rx(a)*(0,0,-1) = (0, sin a, -cos a)
  const f = new THREE.Vector3(f0.x * Math.cos(yaw) + f0.z * Math.sin(yaw), f0.y, -f0.x * Math.sin(yaw) + f0.z * Math.cos(yaw));
  const p = A(pos);
  return { pos: p, look: [p[0] + f.x * 4, p[1] + f.y * 4, p[2] + f.z * 4], fov, drift: 0.15, ...extra };
}
/** blend two shots (pos/look/fov) */
export function blendShot(a, b, u) {
  return { pos: mix3(a.pos, b.pos, u), look: mix3(a.look, b.look, u), fov: lerp(a.fov, b.fov, u), drift: lerp(a.drift ?? 0.2, b.drift ?? 0.2, u), roll: lerp(a.roll || 0, b.roll || 0, u) };
}
/** screen pixel of a world point with the current camera (debug) */
export function pix(cam, p) {
  const v = V(p).project(cam);
  return [Math.round((v.x * 0.5 + 0.5) * 720), Math.round((1 - (v.y * 0.5 + 0.5)) * 1280)];
}

// ------------------------------------------------------------------------------------------- marks (world)
// Fear's facing at FOUT (stage-local yaw): toward the star, i.e. 3/4 toward the camera side (its face reads in the
// KICK wide and in every close-up from the camera side); the Void stands at its front-left.
export const FEAR_LYAW = 0.62;
// call after ROOM.fit(set)
export function marks() {
  const M = ROOM.M;
  const P = (n) => ROOM.W(M[n].p);
  return {
    V: P('V'), FOUT: P('FOUT'), FDOOR: P('FDOOR'), PEEK: P('PEEK'), LURK: P('LURK'), CRASH: P('CRASH'),
    // the magician leans out past the Void's CAMERA-side flank (in front of its silhouette in the KICK wide)
    PEEK2: ROOM.W(3.24, 0, 0.62),
    // Fear at FOUT faces the fingertip star, which the Void holds toward the camera side, away from the magician
    yV: -Math.PI / 4, yFOUT: ROOM.Y(FEAR_LYAW), yFOUTv: 3 * Math.PI / 4, yFDOOR: ROOM.Y(M.FDOOR.yaw), yPEEK: ROOM.Y(M.PEEK.yaw), yCRASH: -Math.PI / 4,
    COSMOS: ROOM.W(M.COSMOS.p),
  };
}

// ------------------------------------------------------------------------------------------- key times
// All derived from beat refs / word times (re-timed audio re-times the picture).
export function times() {
  if (times._c) return times._c;
  const c = {};
  // s20
  c.B1 = T('s20b01'); c.B2 = T('s20b02'); c.B3 = T('s20b03'); c.B4 = T('s20b04'); c.B5 = T('s20b05'); c.B6 = T('s20b06'); c.B7 = T('s20b07'); c.B8 = T('s20b08');
  c.shouting = W('s20b01', 'shouting', { end: true });
  c.making = W('s20b01', 'making');
  c.obvious = W('s20b01', 'obvious');
  c.stab = W('s20b02', 'stab');
  c.creepy = W('s20b02', 'creepy');
  c.kickFire = W('s20b04', 'kicks') + 0.03;        // the leg fires on "kicks"
  c.contact = c.kickFire + 0.15;                     // the foot lands mid-chest
  c.launch = c.contact + 0.05;                       // he folds round the foot for a couple of frames, then flies
  c.fat = W('s20b05', 'fat'); c.leg = W('s20b05', 'leg');
  c.flying = W('s20b06', 'flying');
  c.imp = W('s20b06', 'buckets') + 0.04;             // crash right under "buckets"
  c.resume = c.B6;                                   // the flight clock resumes on the cut into b06
  c.flightA = 0.3;                                   // seconds of flight seen in the kick wide
  c.F = c.flightA + Math.max(0.6, c.imp - c.resume); // total flight time
  c.fearCut0 = c.imp + 0.30; c.fearCut1 = c.fearCut0 + 0.6;   // the 0.6 s cutaway to Fear on the crash
  c.bonk = c.B7 + 0.14;                              // the hat bucket comes down: BONK
  c.wig0 = c.bonk + 0.32; c.wig1 = c.wig0 + 0.5;     // the mop flops onto it
  c.daggerLand = c.B7 + 0.95;                        // dagger thunks point-down into the floor
  c.puff = c.B7 + 1.35;                              // the pouch puffs grey dust on him
  c.sign0 = c.B7 + 1.72; c.sign1 = c.sign0 + 0.62;   // the wet-floor sign tips and lands on him
  c.rude = W('s20b08', 'rude');
  // s21
  c.broom1 = T('s21b01') + 0.24;                     // the last broom clatters flat (off-screen)
  c.shrug = W('s21b03', 'shrugs');
  c.roll0 = T('s21b04') - 0.7; c.roll1 = T('s21b05') + 2.2;
  // s22
  c.galRise = W('s22b01', 'showing');
  c.galaxies = W('s22b01', 'galaxies');
  c.lift0 = T('s22b09') + 0.15; c.lift1 = T('s22b09') + 0.45;  // the bucket lifts an inch
  c.sink0 = T('s22b09') + 1.75; c.clunk = T('s22b09') + 2.3;
  times._c = c;
  return c;
}

// ------------------------------------------------------------------------------------------- the Void's spot
// The Void stands at V facing Fear; in s21b03 it shuffles 0.25 m toward local +Z (camera side) during the shrug, which
// happens to fill Fear's line of sight to the corner — and keeps that spot through s22.
export function voidSpot(t) {
  const M = marks(), c = times();
  const u = k(t, [[c.shrug - 0.15, 0], [c.shrug + 0.55, 1, 'inOut']]);
  const off = LD(0, 0, 0.25 * u);
  return { pos: add(M.V, off), yaw: M.yV, shuffle: u };
}

// ------------------------------------------------------------------------------------------- fingertip star
// The star on the Void's LEFT (camera-side) index fingertip (s20b01 -> s21b03). Stage-local key points; returns world pos and
// brightness. It lights on "making", lures Fear out of the cage door, then is drawn gently screen-left (away from the
// magician) and sways slowly; in s21b03 it floats up off the opening hand and fades.
export function starAt(t) {
  const c = times();
  const S0 = [1.5, 0.95, 0.75], S1 = [0.74, 0.9, 0.66], S2 = [1.06, 1.18, 1.0], S3 = [0.98, 1.24, 1.1];
  const p = k(t, [[c.B1 + 0.75, S0], [c.making + 0.05, S1, 'inOut'], [c.obvious + 0.25, S1, 'inOut'], [c.B2 + 1.1, S2, 'inOut'],
    [c.B3 + 0.2, S2], [c.B4 + 0.9, S3, 'inOut']]);
  // slow sway (Fear's tuft sways with it)
  const sw = smooth(clamp((t - c.B3) / 1.2));
  const loc = [p[0] + 0.035 * sw * Math.sin((t - c.B3) * 1.6), p[1] + 0.02 * sw * Math.sin((t - c.B3) * 1.1 + 1), p[2] + 0.02 * sw * Math.cos((t - c.B3) * 1.6)];
  // s21b03: the hand opens into the shrug, the star floats up and away, fading
  const fl = smooth(clamp((t - (c.shrug - 0.1)) / 1.6));
  loc[1] += 0.55 * fl; loc[0] -= 0.12 * fl; loc[2] += 0.08 * fl;
  const lit = smooth(clamp((t - c.making) / 0.22)) * (1 - smooth(clamp((t - (c.shrug + 0.3)) / 1.1)));
  return { pos: ROOM.W(loc), lit, held: 1 - fl };
}
/** draw the star (a warm white sparkle with a soft halo, a slow twinkle — no flicker) */
export function drawStar(ps, t, s, CELL, scale = 1) {
  if (s.lit <= 0.01) return;
  const tw = 0.88 + 0.12 * Math.sin(t * 5.1) * Math.sin(t * 2.3 + 1);
  ps.add(s.pos, 0.085 * scale * (0.9 + 0.1 * tw), 0xfff6e0, 0.95 * s.lit, t * 0.4, CELL.star);
  ps.add(s.pos, 0.2 * scale, 0xffe2a8, 0.32 * s.lit * tw, 0, CELL.dot);
  ps.add(s.pos, 0.42 * scale, 0xb9a2ff, 0.1 * s.lit, 0, CELL.dot);
}

// ------------------------------------------------------------------------------------------- the magician's flight
/** flight clock (seconds of flight shown), null before contact */
export function flightTau(t) {
  const c = times();
  if (t < c.launch) return null;
  if (t < c.launch + c.flightA) return t - c.launch;
  if (t < c.resume) return c.flightA;
  return Math.min(c.F, c.flightA + (t - c.resume));
}
/** root position along the rubber-hose arc from the contact point (start) to the crash spot */
export function flightPos(tau, start, end, apex = 2.25) {
  const c = times();
  // horizontal progress: a hard launch (fast), then a floaty arc, then a quick drop into the pile
  const uA = 0.24;
  let u;
  if (tau <= c.flightA) u = uA * ease.out(tau / c.flightA) * 0.6 + uA * 0.4 * (tau / c.flightA);
  else { const s = (tau - c.flightA) / (c.F - c.flightA); u = uA + (1 - uA) * (0.85 * s + 0.15 * s * s); }
  u = clamp(u);
  const p = mix3(start, end, u);
  const h = 4 * apex * u * (1 - u);
  p[1] = start[1] + h + (end[1] - start[1]) * u;
  return { pos: p, u };
}

// ------------------------------------------------------------------------------------------- the wreck (corner)
/** the magician sitting in the wreckage (after the crash): his pose at t (s20 after impact, s21, s22) */
export function wreckPose(t, M, extra = {}) {
  const c = times();
  const dz = clamp((t - c.bonk) / 0.4);                      // dizzy after the bonk
  const rigid = pulse(t, c.sign1 - 0.02, c.sign1 + 0.5, 0.04, 0.3);
  const sag = smooth(clamp((t - (c.sign1 + 0.3)) / 0.5));
  return {
    pos: M.CRASH, yaw: M.yCRASH,
    body: { sit: 1, slump: 0.35 + 0.35 * sag - 0.3 * rigid, lean: -0.08 - 0.12 * rigid, tilt: 0.1 + 0.02 * Math.sin(t * 1.3) * dz, shrug: 0.5 * rigid, breathe: 0.6, sway: 0 },
    head: { roll: 0.14 + 0.06 * Math.sin(t * 1.7) * dz, pitch: 0.18 - 0.1 * rigid },
    face: 'dazed',
    armL: { preset: 'hang' }, armR: { preset: 'hang' },
    extra: { dizzy: dz, stars: dz, hatOff: 1, hatPos: hatRestPos(M), hatRot: [0.15, 0.6, 1.45], dagger: false, pouch: true, ...extra },
  };
}
/** where his top hat ends up: on its side on the floor beside him (world) */
export function hatRestPos(M) { const p = M.CRASH; return [p[0] - 0.62, 0.11, p[2] + 0.42]; }
/** where the dagger sticks point-down in the floorboards (world) */
export function daggerRestPos(M) { const p = M.CRASH; return [p[0] - 0.95, 0, p[2] + 0.62]; }

/** BACKROOM opts for the janitor corner at t (shared by s20..s22). `mag` = the magician rig (already updated). */
export function cornerOpts(t, mag, o = {}) {
  const c = times();
  const tc = t - c.imp;
  const out = {
    crash: 1, crashT: tc, latch: 1, cageDoor: 1,
    signFall: clamp((t - c.sign0) / (c.sign1 - c.sign0)), signOn: 0.42,
    broomSlide: clamp((t - (c.broom1 - 0.75)) / 0.75),
    rollBucket: smooth(clamp((t - c.roll0) / (c.roll1 - c.roll0))),
  };
  if (mag && t >= c.imp) {
    const lift = 0.075 + (o.lift ?? 0);              // rides high and askew: the moustache shows below the rim
    out.bucketHat = { pos: mag.anchor('headTop'), up: mag.anchor('headUp'), yaw: -0.35, at: c.bonk - c.imp, lift, tilt: 0.14 + (o.tilt ?? 0) };
    if (t < c.bonk) out.bucketHat.blend = 1;   // forced to its on-head pose: the scene moves it along its own fall
    out.mopWig = { blend: smooth(clamp((t - c.wig0) / (c.wig1 - c.wig0))), yaw: 0.9 };
    out.signToward = A(mag.anchor('chest'));
  }
  return out;
}
/** after set.update(): the hat bucket shoots up out of frame on impact, hangs out of sight, then drops onto his head */
export function placeHatBucket(t, set, base) {
  const c = times();
  if (t < c.imp || t >= c.bonk) return;
  const b = set.props.bucketHat;
  const on = b.position.clone();                    // its on-head pose (blend 1)
  const tc = t - c.imp, fallT = 0.42;
  let p;
  if (t < c.bonk - fallT) {
    const u = clamp(tc / 0.55);
    p = V(base).lerp(on, 0.35 * u); p.y = base[1] + 3.6 * ease.out(u);
  } else {
    const u = (t - (c.bonk - fallT)) / fallT;          // free fall onto the head
    p = on.clone(); p.y = on.y + 3.2 * (1 - u * u);
  }
  b.position.copy(p);
  const spin = (1 - smooth(clamp((t - (c.bonk - fallT)) / fallT))) * 6.0;
  b.rotateOnWorldAxis(new THREE.Vector3(0.3, 0, 1).normalize(), spin);
}
