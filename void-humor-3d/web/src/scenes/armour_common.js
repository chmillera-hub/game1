// Story-specific shared poses for s08 / s09 (the Void's crossed-arm armour, the seated user, the frozen mote, the
// little galaxy at the user's sneaker). Pure functions of t built from beat/word refs; both scene modules call them so
// the cut s08 -> s09 matches exactly. Not a scene module.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { VX } from '../chars/void.js';
import { EDGE, lookFor } from './marks.js';
import { V3, toV, wordT, pulse, ramp, wobble, W, WY, MARKS as M } from './armour_shared.js';

// ------------------------------------------------------------------------------------------------ key times
export const moteFreezeT = () => wordT('s08b01', 'scowls', { off: 0.55, fallback: 0.72 });
export const scaryT = () => wordT('s09b03', 'scary', { fallback: 0.52 });

// ------------------------------------------------------------------------------------------------ the Void (s08-s09)
/**
 * The Void at V through s08 and s09: arms cross on "crosses its arms" (L then R 4 frames later), chin up, the scowl on
 * "scowls" with its tell (inner brow tips up a hair) and a held breath; "important" -> chin up a notch, scowl deeper;
 * s09 "scary" -> two fast blinks + an 8-frame mask slip, breath out, then the scowl clamps back harder.
 */
export function voidArmour(t, { gaze = null } = {}) {
  const b1 = T('s08b01');
  const cr = wordT('s08b01', 'crosses', { fallback: 0.14 });
  const arms = wordT('s08b01', 'arms', { fallback: 0.32 });
  const sc = wordT('s08b01', 'scowls', { fallback: 0.57 });
  const imp = wordT('s08b04', 'important', { fallback: 0.4 });
  const scary = scaryT();
  // ---- arms (L first, R 4 frames later)
  const uL = ramp(t, cr + 0.02, cr + 0.42, 'inOut'), uR = ramp(t, cr + 0.19, cr + 0.6, 'inOut');
  const land = cr + 0.6;
  const armL = { preset: 'crossed', from: 'rest', mix: uL };
  // the elbow on Jesus's side tucks forward-down (the default pole swings it out ~1 m sideways, into his head)
  const vy = WY(M.V), fw = [Math.sin(vy), 0, Math.cos(vy)], lf = [Math.cos(vy), 0, -Math.sin(vy)];
  const armR = { preset: 'crossed', from: 'rest', mix: uR, pole: [fw[0] * 0.9 - lf[0] * 0.25, -0.9, fw[2] * 0.9 - lf[2] * 0.25] };
  // ---- body
  const antic = pulse(t, cr - 0.18, 0.18, 0.04, 0.3);                     // shoulders rise as the arms lift
  const whump = wobble(t, land, 2.4, 6.5) * ramp(t, land, land + 0.03);  // velvet water-balloon settle
  const inhale = ramp(t, sc - 0.12, sc + 0.25, 'out');                    // the breath it then holds
  const slip = pulse(t, scary + 0.1, 0.08, 0.25, 0.25);                   // the mask slip (s09)
  const deflate = pulse(t, scary + 0.12, 0.18, 0.2, 0.9);
  const held = inhale * (1 - ramp(t, scary + 0.1, scary + 0.4)) + 0.6 * ramp(t, scary + 0.55, scary + 0.9);
  const body = {
    shrug: 0.22 * antic + 0.05 * inhale - 0.12 * deflate,
    bounce: -0.035 * whump - 0.02 * deflate,
    swell: 0.18 * inhale * (1 - deflate) + 0.06 * Math.max(0, whump),
    lean: -0.05 * ramp(t, arms, arms + 0.4) - 0.02 * inhale + 0.05 * deflate,
    slump: 0.25 * deflate,
    breathe: 1 - 0.95 * held,
    recoil: 0.25 * pulse(t, scary + 0.02, 0.06, 0.08, 0.3),
  };
  // ---- head: chin lifts on "arms", another notch on "important"; flinch back on "scary"
  const head = {
    pitch: -0.08 * ramp(t, arms + 0.05, arms + 0.45, 'out') - 0.06 * ramp(t, imp + 0.02, imp + 0.3, 'out') + 0.06 * deflate
      - 0.04 * ramp(t, scary + 0.5, scary + 0.85),
    yaw: 0.02 * Math.sin(t * 0.3),
    roll: 0.03 * ramp(t, arms + 0.05, arms + 0.45) - 0.02 * deflate,
  };
  // ---- face
  const F = (name, o) => VX(name, o);
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
    [scary - 0.02, F('scowl', { lidAngry: 1.5, lidU: 0.56, browIn: -0.9, mSmile: -0.9, mPress: 0.65 })],
    [scary + 0.12, F('flinch', { lidU: 1.18, browIn: 0.85, browOut: 0.25, mSmile: -0.05, mOpen: 0.13, mRound: 0.15, mPress: 0, pupil: 0.85, wet: 0.5, saccade: 0 })], // unhinged: hurt
    [scary + 0.44, F('flinch', { lidU: 1.14, browIn: 0.8, browOut: 0.2, mSmile: -0.05, mOpen: 0.11, mRound: 0.15, mPress: 0, pupil: 0.85, wet: 0.5, saccade: 0 })],
    [scary + 0.56, F('scowl', { lidAngry: 1.65, lidU: 0.5, browIn: -1.15, mSmile: -1.0, mPress: 0.8 })],  // clamped back on, harder
    [scary + 0.9, F('scowl', { lidAngry: 1.55, lidU: 0.55, browIn: -1.0, mSmile: -0.95, mPress: 0.75, browInL: -0.85 })],
  ];
  const face = k(t, keys);
  face.autoBlink = t > sc && t < scary + 2.5 ? 0 : 1;                     // the held stare: no idle blinks
  face.saccade = t > sc ? 0.15 : 0.6;
  void slip;
  const blinkAt = [b1 + 0.22, scary + 0.0, scary + 0.13];
  return { pos: W(M.V), yaw: WY(M.V), body, head, armL, armR, face, gaze, blinkAt, extra: { motes: t > sc && t < scary ? 0.4 : 1 } };
}

// ------------------------------------------------------------------------------------------------ the frozen mote
/** { p: Vector3, a: alpha 0..1, s: scale mult } — rises off the shoulder, stops dead at the breath hold, falls on "scary". */
export function moteState(t, MOTE) {
  const tf = MOTE.tf, rise = 0.15, tb = tf - 2.2;
  const p = MOTE.p.clone();
  if (t < tb) return { p, a: 0, s: 1 };
  if (t < tf) {
    const d = tf - t;
    p.y -= rise * d; p.x += 0.012 * Math.sin(t * 2.3); p.z += 0.01 * Math.sin(t * 1.7 + 1);
    return { p, a: 0.95 * smooth((t - tb) / 0.5), s: 0.9 + 0.1 * Math.sin(t * 3.1) };
  }
  const td = scaryT() + 0.08;
  if (t < td) {
    const freezePop = Math.exp(-(t - tf) * 6) * (1 - Math.exp(-(t - tf) * 60));
    return { p, a: 0.95, s: 1 + 0.35 * freezePop + 0.06 * Math.sin((t - tf) * 2.2) };
  }
  const u = clamp((t - td) / 0.42);
  p.y -= 0.55 * u * u;
  return { p, a: 0.95 * (1 - smooth((u - 0.6) / 0.4)), s: 1 - 0.5 * smooth((u - 0.6) / 0.4) };
}

// ------------------------------------------------------------------------------------------------ the seated user
/** The user's seat: U, minus the 5 cm scoot back on "thing" (s09b03), kept through s10+. */
export function userPos(t) {
  const th = wordT('s09b03', 'thing', { fallback: 0.7 });
  const u = ramp(t, th + 0.02, th + 0.3, 'out');
  const y = WY(M.U), p = W(M.U);
  return [p[0] - Math.sin(y) * 0.05 * u, 0, p[2] - Math.cos(y) * 0.05 * u];
}
/** Seated at U (since s02): RIGHT hand up (defend), phone in the LEFT hand glowing on the chin, guarded. */
export function userSeated(t, { gaze = null } = {}) {
  return {
    pos: userPos(t), yaw: WY(M.U),
    body: { sit: 1, sitPath: 'plain', tremble: 0.12, hunch: 0.3, shrug: 0.15 },
    armR: { preset: 'defend', tremble: 0.35 },
    armL: { preset: 'hold' },
    head: { follow: 0.35, look: gaze || undefined },
    gaze, extra: { phone: 0.85, screen: 'feed' },
  };
}

// ------------------------------------------------------------------------------------------------ props
/** The little galaxy coughed up in s04b09, lying flat by the user's sneaker (stage ≈ (-0.85, 0.02, 0.85)), twinkling. */
export function galaxyFloor(ps) {
  const tex = ps.mat.uniforms.map.value;                                  // the particles atlas (galaxy = cell 2)
  const g = new THREE.PlaneGeometry(1, 1);
  const uv = g.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, 0.5 + uv.getX(i) * 0.25, 0.5 + uv.getY(i) * 0.5);
  const mat = new THREE.MeshBasicMaterial({ map: tex, color: 0xd8c0ff, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false, opacity: 0.85 });
  const mesh = new THREE.Mesh(g, mat);
  mesh.rotation.order = 'YXZ';
  const p = EDGE.W(-0.85, 0.025, 0.85);
  mesh.position.set(p[0], p[1], p[2]);
  mesh.renderOrder = 4;
  return { mesh, update(t) { mesh.rotation.set(-Math.PI / 2, 0, 0); mesh.rotateZ(t * 0.35); const s = 0.16 * (1 + 0.05 * Math.sin(t * 1.3)); mesh.scale.set(s, s * 0.9, s); mat.opacity = 0.75 + 0.15 * Math.sin(t * 2.1); } };
}

/** The scene's post look (marks.js lookFor) — kept constant within the scene. */
export function sceneLook(id, setLook, t) { return lookFor(id, setLook); }
