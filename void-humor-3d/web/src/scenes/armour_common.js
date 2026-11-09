// Story-specific shared poses for s08 / s09 / s10 (the Void's folded-arm armour, the seated user, the frozen mote).
// Pure functions of t built from beat/word refs; the scene modules call them so the cuts s08 -> s09 -> s10 match.
// Not a scene module.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { speechAt } from '../core/speech.js';
import { VX } from '../chars/void.js';
import { EDGE, lookFor } from './marks.js';
import { V3, toV, wordT, pulse, ramp, wobble, W, WY, MARKS as M } from './armour_shared.js';

// ------------------------------------------------------------------------------------------------ key times
export const moteFreezeT = () => wordT('s08b01', 'scowls', { off: 0.55, fallback: 0.72 });
export const scaryT = () => wordT('s09b03', 'scary', { fallback: 0.52 });
/** s09b03 is split: USER_CU holds through the wobble at the start of "scary", the three-shot cuts in here */
export const scaryCutT = () => scaryT() + 0.12;
/** the Void's reaction to "scary" starts as the three-shot cuts in (two fast blinks, then 8 frames of hurt) */
export const slipT = () => scaryCutT() + 0.03;

/**
 * Fail loudly if lip-sync data did not load (core/speech.js falls back to {} silently, e.g. when data/lipsync.json has
 * a bare NaN): every on-screen line of s08-s09 would then play with a shut mouth.
 */
export function assertLipsync(scene) {
  const probes = [['JESUS', 's08b03'], ['USER', 's09b02']];
  for (const [spk, b] of probes) {
    const bt = TLb(b);
    if (!speechAt(spk, bt + 0.5 * (TLe(b) - bt))) {
      const msg = `[${scene}] lip-sync missing for ${spk} in ${b}: data/lipsync.json failed to load or parse (NaN?)`;
      console.error(msg);
      throw new Error(msg);
    }
  }
}
const TLb = (b) => T(b), TLe = (b) => T(b + '.end');

// ------------------------------------------------------------------------------------------------ folded arms
/**
 * Folded arms that read as folded arms from the front (the rig's `crossed` preset points both cuffs into the lens):
 * forearms stacked across the belly (LEFT lower, RIGHT on top), elbows out at the flanks, cuffs side-on, the mitts out
 * of the cuffs lying over the other forearm. Body-relative: built from the Void's own anchors, so call it after a
 * first `vd.update()` of the same frame (the body may lean, swell, turn or sit), then update again with the result.
 * mixL / mixR 0..1 blend from `rest` (arms crossing on "crosses"), arcing out in front of the belly.
 * Returns { armL, armR }.
 */
export function foldedArms(vd, { mixL = 1, mixR = 1, o = {} } = {}) {
  const C = vd.anchor('chest'), SL = vd.anchor('sideL'), SR = vd.anchor('sideR');
  const up = V3(0, 1, 0);
  const lft = SL.clone().sub(SR).setY(0).normalize();
  const fwd = V3().crossVectors(lft, up).normalize();
  const O = SL.clone().add(SR).multiplyScalar(0.5);
  const d0 = fwd.dot(C.clone().sub(O));
  const base = C.clone().addScaledVector(fwd, -d0);                        // body axis at chest height
  const P = (x, y, z) => base.clone().addScaledVector(lft, x).addScaledVector(up, y).addScaledVector(fwd, d0 + z);
  const D = (x, y, z) => V3(0, 0, 0).addScaledVector(lft, x).addScaledVector(up, y).addScaledVector(fwd, z).normalize().toArray();
  const q = { lx: -0.38, ly: -0.24, lz: 0.12, rx: 0.38, ry: -0.08, rz: 0.22, hs: 0.72, pl: [0.5, -0.3, 0.85], pr: [-0.5, -0.25, 0.85], ...o };
  const hand = { curl: 0.42, spread: 0.08, thumb: 0.3, cup: 0.5, ...(o.hand || {}) };
  const arc = (m) => { const a = Math.sin(Math.PI * clamp(m)); return V3(0, 0, 0).addScaledVector(fwd, 0.32 * a).addScaledVector(up, 0.1 * a).toArray(); };
  const pl = q.pl, pr = q.pr;
  const armL = { preset: 'crossed', from: 'rest', mix: mixL, reach: mixL, target: P(q.lx, q.ly, q.lz), offset: arc(mixL), handScale: q.hs,
    pole: D(...pl), fingers: D(-0.9, -0.25, -0.2), palm: D(-0.15, -0.6, -0.75), hand };
  const armR = { preset: 'crossed', from: 'rest', mix: mixR, reach: mixR, target: P(q.rx, q.ry, q.rz), offset: arc(mixR), handScale: q.hs,
    pole: D(...pr), fingers: D(0.9, -0.3, -0.15), palm: D(0.15, -0.65, -0.7), hand };
  return { armL, armR };
}
/**
 * Update the Void with folded arms: pose P carries `fold: { mixL, mixR, armL?, armR? }` (armL/armR = overrides merged
 * over the folded arm, e.g. a grass-picking target). Two passes: the first places the body (anchors), the second the arms.
 */
export function updateVoid(vd, t, P) {
  vd.update(t, P);
  if (!P.fold) return;
  const f = foldedArms(vd, P.fold);
  const A = P.fold.armL ? (typeof P.fold.armL === 'function' ? P.fold.armL(f.armL) : { ...f.armL, ...P.fold.armL }) : f.armL;
  const B = P.fold.armR ? (typeof P.fold.armR === 'function' ? P.fold.armR(f.armR) : { ...f.armR, ...P.fold.armR }) : f.armR;
  vd.update(t, { ...P, armL: A, armR: B });
}

// ------------------------------------------------------------------------------------------------ the Void (s08-s09)
/**
 * The Void at V through s08 and s09: arms fold on "crosses its arms" (L then R 4 frames later), chin up, the scowl on
 * "scowls" with its tell (inner brow tips up a hair) and a held breath; "important" -> chin up a notch, scowl deeper;
 * s09 "scary" -> two fast blinks + an 8-frame mask slip, breath out, then the scowl clamps back harder.
 */
export function voidArmour(t, { gaze = null } = {}) {
  const b1 = T('s08b01');
  const cr = wordT('s08b01', 'crosses', { fallback: 0.14 });
  const arms = wordT('s08b01', 'arms', { fallback: 0.32 });
  const sc = wordT('s08b01', 'scowls', { fallback: 0.57 });
  const imp = wordT('s08b04', 'important', { fallback: 0.4 });
  const slip = slipT();
  // ---- arms (L first, R 4 frames later)
  const uL = ramp(t, cr + 0.02, cr + 0.42, 'inOut'), uR = ramp(t, cr + 0.19, cr + 0.6, 'inOut');
  const land = cr + 0.6;
  // ---- body
  const antic = pulse(t, cr - 0.18, 0.18, 0.04, 0.3);                     // shoulders rise as the arms lift
  const whump = wobble(t, land, 2.4, 6.5) * ramp(t, land, land + 0.03);  // velvet water-balloon settle
  const inhale = ramp(t, sc - 0.12, sc + 0.25, 'out');                    // the breath it then holds
  const deflate = pulse(t, slip + 0.2, 0.18, 0.2, 0.9);
  const held = inhale * (1 - ramp(t, slip + 0.18, slip + 0.45)) + 0.6 * ramp(t, slip + 0.6, slip + 0.95);
  const body = {
    shrug: 0.22 * antic + 0.05 * inhale - 0.12 * deflate,
    bounce: -0.035 * whump - 0.02 * deflate,
    swell: 0.18 * inhale * (1 - deflate) + 0.06 * Math.max(0, whump),
    lean: -0.05 * ramp(t, arms, arms + 0.4) - 0.02 * inhale + 0.05 * deflate,
    slump: 0.25 * deflate,
    breathe: 1 - 0.95 * held,
    recoil: 0.25 * pulse(t, slip + 0.02, 0.06, 0.08, 0.3),
  };
  // ---- head: chin lifts on "arms", another notch on "important"; flinch back on "scary"
  const head = {
    pitch: -0.08 * ramp(t, arms + 0.05, arms + 0.45, 'out') - 0.06 * ramp(t, imp + 0.02, imp + 0.3, 'out') + 0.06 * deflate
      - 0.04 * ramp(t, slip + 0.55, slip + 0.9),
    yaw: 0.02 * Math.sin(t * 0.3),
    roll: 0.03 * ramp(t, arms + 0.05, arms + 0.45) - 0.02 * deflate,
  };
  // ---- face
  const F = (name, o) => VX(name, o);
  const hurt = (lidU) => F('sad', { lidU, lidSad: 0.55, lidAngry: 0, browIn: 1.1, browOut: -0.35, browSq: 0.25, mSmile: -0.3, mOpen: 0.1, mRound: 0.55, mWide: -0.25, mPress: 0, mPout: 0, pupil: 0.9, wet: 0.7, saccade: 0 });
  const keys = [
    ['s08', F('hopeful', { lidU: 1.0, mSmile: 0.15, wet: 0.2 })],                        // "you'll ask?"
    [b1 + 0.25, F([['neutral', 1], ['determined', 0.3]], { lidU: 0.92 })],             // eyes to the user: settle
    [cr + 0.1, F([['neutral', 1], ['determined', 0.55]], { lidU: 0.85, mPress: 0.6 })],  // arms going: setting its face
    [sc - 0.12, F([['neutral', 1], ['determined', 0.5]], { lidU: 1.04, browIn: 0.05, mPress: 0.5 })],   // wind-up
    [sc + 0.16, F('scowl', { lidAngry: 1.55, lidU: 0.58, browIn: -1.1, mSmile: -0.95, mPress: 0.7 })],  // SCOWL (overshoot)
    [sc + 0.42, F('scowl', { lidU: 0.64 })],
    [sc + 0.8, F('scowl', { lidU: 0.64, browIn: -0.72, browInL: -0.7, browInR: -0.7 })],                  // the tell: inner tips up a hair
    [imp - 0.02, F('scowl', { lidU: 0.64, browIn: -0.72 })],
    [imp + 0.22, F('scowl', { lidAngry: 1.5, lidU: 0.56, browIn: -0.95, mSmile: -0.9, mPress: 0.65 })],  // deeper on "important"
    [slip + 0.16, F('scowl', { lidAngry: 1.5, lidU: 0.56, browIn: -0.9, mSmile: -0.9, mPress: 0.65 })],
    [slip + 0.22, hurt(1.14)],                                                                            // unhinged: hurt (8 frames)
    [slip + 0.5, hurt(1.08)],
    [slip + 0.6, F('scowl', { lidAngry: 1.65, lidU: 0.5, browIn: -1.15, mSmile: -1.0, mPress: 0.8 })],  // clamped back on, harder
    [slip + 0.95, F('scowl', { lidAngry: 1.55, lidU: 0.55, browIn: -1.0, mSmile: -0.95, mPress: 0.75, browInL: -0.85 })],
  ];
  const face = k(t, keys);
  face.autoBlink = t > sc && t < slip + 2.5 ? 0 : 1;                      // the held stare: no idle blinks
  face.blink = Math.max(face.blink || 0, pulse(t, slip + 0.0, 0.035, 0.02, 0.045), pulse(t, slip + 0.1, 0.035, 0.02, 0.05));   // two fast blinks
  face.saccade = t > sc ? 0.15 : 0.6;
  const blinkAt = [b1 + 0.22];
  return { pos: W(M.V), yaw: WY(M.V), body, head, armL: { preset: 'crossed', from: 'rest', mix: uL }, armR: { preset: 'crossed', from: 'rest', mix: uR },
    fold: { mixL: uL, mixR: uR }, face, gaze, blinkAt, extra: { motes: t > sc && t < slip ? 0.4 : 1 } };
}

// ------------------------------------------------------------------------------------------------ the frozen mote
/**
 * The mote's frozen WORLD point (STAGING §1.6), shared by s08 and s09. It lifts off the capelet of the Void's left
 * shoulder (screen-right in every front angle) and drifts up and out; the STAGING offset (0.15, 0.35, 0.10) lands
 * inside the hood's side bulge (invisible), so it hangs just outside the shoulder silhouette, a little in front.
 * Poses the (shared) Void rig once (setup only).
 */
export function computeMote(vd, gaze) {
  const tf = moteFreezeT();
  vd.update(tf, voidArmour(tf, { gaze }));
  const vy = WY(M.V), vl = V3(Math.cos(vy), 0, -Math.sin(vy)), vf = V3(Math.sin(vy), 0, Math.cos(vy));
  const sh = vd.anchor('shoulderL');
  const start = sh.clone().addScaledVector(vf, 0.16).addScaledVector(vl, -0.04).add(V3(0, 0.03, 0));   // on the capelet
  const p = sh.clone().addScaledVector(vl, 0.16).addScaledVector(vf, 0.42).add(V3(0, 0.38, 0));       // its hang point
  return { p, start, tf };
}
/** { p: Vector3, a: alpha 0..1, s: scale mult } — rises off the shoulder, stops dead at the breath hold, falls on "scary". */
export function moteState(t, MOTE) {
  const tf = MOTE.tf, tb = tf - 2.1;
  if (t < tb) return { p: MOTE.start.clone(), a: 0, s: 1 };
  if (t < tf) {                     // steady drift up and out (no ease-out: it STOPS dead when the breath is held)
    const u = (t - tb) / (tf - tb);
    const p = MOTE.start.clone().lerp(MOTE.p, u);
    p.x += 0.02 * Math.sin(t * 2.3) * u; p.z += 0.015 * Math.sin(t * 1.7 + 1) * u;
    p.y += 0.03 * Math.sin(Math.PI * u);
    return { p, a: 0.95 * smooth((t - tb) / 0.4), s: 0.75 + 0.25 * u + 0.08 * Math.sin(t * 3.1) };
  }
  const p = MOTE.p.clone();
  p.x += 0.02 * Math.sin(tf * 2.3); p.z += 0.015 * Math.sin(tf * 1.7 + 1);   // exactly where the drift left it
  const td = slipT() + 0.22;        // the held breath goes out with the 8-frame hurt: it drops
  if (t < td) {
    const freezePop = Math.exp(-(t - tf) * 6) * (1 - Math.exp(-(t - tf) * 60));
    return { p, a: 0.95, s: 1 + 0.45 * freezePop + 0.05 * Math.sin((t - tf) * 2.2) };
  }
  const u = clamp((t - td) / 0.42);
  p.y -= 0.55 * u * u;
  return { p, a: 0.95 * (1 - smooth((u - 0.6) / 0.4)), s: 1 - 0.5 * smooth((u - 0.6) / 0.4) };
}

// ------------------------------------------------------------------------------------------------ the seated user
/** The user's seat: U minus s07b05's 2.5 cm scoot, then 2.5 cm more on "thing" (s09b03): U - 5 cm = s11's USEAT. */
export function userPos(t) {
  const th = wordT('s09b03', 'thing', { fallback: 0.7 });
  const u = ramp(t, th + 0.02, th + 0.3, 'out');
  const y = WY(M.U), p = W(M.U);
  const d = 0.025 + 0.025 * u;
  return [p[0] - Math.sin(y) * d, 0, p[2] - Math.cos(y) * d];
}
/**
 * The raised RIGHT hand ("defend"): s07 ends on the plain preset; during s08b05's waiting it draws back to a wrist
 * target out at the right-front below the chin (face-clear in s09's USER_CU), where it stays until the jab.
 * R = { plain: world wrist of the plain preset, clear: world wrist target, toVoid: palm dir } (computed in setup).
 */
export function defendArm(t, R, tremble = 0.35) {
  const b5 = T('s08b05');
  const w = ramp(t, b5 + 0.45, b5 + 1.25);
  if (!R || w <= 0) return { preset: 'defend', tremble };
  return { preset: 'defend', tremble, target: R.plain.clone().lerp(R.clear, w), reach: 1, palm: R.toVoid };
}
/** setup helper: R for defendArm() (plain-preset wrist, face-clear target, palm toward the Void) */
export function defendRef(user, t) {
  const base = { pos: W(M.U), yaw: WY(M.U), body: { sit: 1, sitPath: 'plain', tremble: 0, hunch: 0.3, shrug: 0.15 } };
  user.update(t, { ...base, armR: { preset: 'defend' } });
  const plain = user.root.localToWorld(user.arms.R.wrist.clone());
  const sh = user.anchor('shoulderR');
  const uy = WY(M.U), a = uy - 0.95;
  const clear = sh.clone().add(V3(Math.sin(a) * 0.3, 0.17, Math.cos(a) * 0.3));
  const toVoid = toV(W(M.V)).add(V3(0, 1.9, 0)).sub(clear).normalize();
  return { plain, clear, toVoid };
}
/** Seated at U (since s02): RIGHT hand up (defend), phone in the LEFT hand glowing on the chin, guarded. */
export function userSeated(t, { gaze = null, R = null } = {}) {
  return {
    pos: userPos(t), yaw: WY(M.U),
    body: { sit: 1, sitPath: 'plain', tremble: 0.12, hunch: 0.3, shrug: 0.15 },
    armR: defendArm(t, R),
    armL: { preset: 'hold' },
    head: { follow: 0.35, look: gaze || undefined },
    gaze, extra: { phone: 0.85, screen: 'feed' },
  };
}
/**
 * s09b03 "thing" -> s10: the huffy chin-up turn-away: a look away over the RIGHT shoulder (USER rig `lookBack` < 0),
 * i.e. toward the master camera, so the pout and the folded arms read in 3/4 in the three-shot; it eases back toward
 * the Void while s10b01-b03 hold on the Void. Returns { lookBack, chin }.
 */
export function userTurnAway(t) {
  const th = wordT('s09b03', 'thing', { fallback: 0.7 });
  const on = ramp(t, th + 0.04, th + 0.34, 'out') * (1 - ramp(t, T('s10b01') + 0.2, T('s10b03') + 0.6));
  const ov = 0.06 * pulse(t, th + 0.28, 0.06, 0.04, 0.25);              // overshoot, settle
  return { lookBack: -0.72 * on - ov, chin: on };
}

// ------------------------------------------------------------------------------------------------ props
/** The scene's post look (marks.js lookFor) — kept constant within the scene. */
export function sceneLook(id, setLook, t) { return lookFor(id, setLook); }
