// SELF / CONSCIOUSNESS — the narrator. Same person, two outfits:
//   outfit 'sweater' (REAL_ROOM, default)  — oversized dusty-teal sweater
//   outfit 'ceo'     (MIND_HQ)             — slightly-too-big charcoal blazer over the sweater + gold "CEO" badge
//
//   drawSelf(g, x, y, scale, pose)
//     x, y   : world position of the ground point between the feet (standing / kneeling / walking)
//              SEATED (pose.seated): the point where the DESK TOP meets the body (centre of the waist line);
//              nothing of the torso below that line is drawn (the desk occludes it).
//     scale  : 1 = ~600px tall standing
//
// POSE fields (all optional; full reference with ranges in docs/self.md)
//   t, face, facing, headTilt, headTurn, headDX, headDY, lean, crouch, tremble, breathe, breathRate,
//   armL, armR, walk {phase}, shadow, alpha                          — same semantics as fear.mjs
//   outfit 'sweater'|'ceo', clipboard (bool), view 'front'|'back', bodyTurn -1..1, kneel 0..1,
//   seated (bool), shrug 0..1, hairWind -1..1, layer 'all'|'body'|'front', notebook {tilt}

import { clamp, lerp, TAU, fbm, noise1, autoBlink, ik, ellipse, circle, groundShadow, rgba, shade } from '../engine.mjs';
import { drawFace, makeExpr } from '../face.mjs';

export const SELF_COLORS = {
  skin: '#d9a27e', skinLight: '#f0c6a6', skinShade: '#bb7b5c', skinLine: '#6e3b2e',
  hair: '#2f2433', hairLight: '#6b5875', hairShade: '#1f1723', hairLine: '#150d17',
  sweater: '#4f8c8a', sweaterLight: '#78b2ad', sweaterShade: '#386a69', sweaterLine: '#1c393b',
  blazer: '#3a3d4a', blazerLight: '#5a5f72', blazerShade: '#2a2c37', blazerLine: '#14151c',
  badge: '#e8c25a', badgeLight: '#fbe7a4', badgeShade: '#a9832c',
  pants: '#4a4058', pantsCeo: '#43435a', pantsLight: '#61577a', pantsLine: '#1d1826',
  shoe: '#8a5a44', shoeLine: '#36211a', sole: '#e8d9c6',
  iris: '#6a3f22', iris2: '#bd8a52', blush: '#e2786a',
};
const C = SELF_COLORS;

export const HEIGHT = 600;

// ---- skeleton (px at scale 1, origin = ground point between the feet, y up = negative) ----
const HIP_Y = -250, HIP_W = 21;
const THIGH = 116, SHIN = 110, ANKLE_Y = -22;
const SH_REL = -132, SX = 58;            // shoulder joints, relative to hip (torso frame)
const NECK_REL = -150, PIVOT_REL = -166; // neck base / head pivot, relative to hip
const HEAD_UP = 72;                      // pivot -> face centre
const UPPER = 100, FORE = 92;            // arm bones (wrist = IK target)
const HAND_S = 1.42;                     // hand drawing scale (hand ≈ 46px long)
const SEAT_HIP = 40;                     // seated: hip sits 40px below the desk line
const KNEEL_HIP = [-24, -136];
const TORSO_D = 30;                      // torso half-depth (for bodyTurn projection)

const rotP = (x, y, a) => { const c = Math.cos(a), s = Math.sin(a); return [x * c - y * s, x * s + y * c]; };
const sstep = (a, b, x) => { const q = clamp((x - a) / (b - a)); return q * q * (3 - 2 * q); };

/** Face style for drawFace (head-local: (0,0) = face centre, +y down). */
export const SELF_FACE = {
  eyeSpacing: 27, eyeY: 2, eyeRx: 16, eyeRy: 12.6, eyeShape: 'almond',
  white: '#fffaf4', irisColor: C.iris, irisColor2: C.iris2, irisR: 0.6, pupilColor: '#24130d',
  skin: '#d9a07c', line: '#3f2421', lineW: 2.3, lash: 0.9, restLid: 0.15, eyeOutline: 0.55,
  browY: -19, browLen: 23, browThick: 6.2, browColor: '#33242f', browArch: 0.42,
  mouthY: 37, mouthW: 14, mouthColor: '#6b2631', tongue: '#d8707a', teethColor: '#fffaf2',
  lipLine: '#74342f', mouthLine: 2.6,
  blushColor: C.blush, blushX: 39, blushY: 24, blushR: 14,
  nose: drawNose,
};

/** Expression presets tuned for this face (same parameter vocabulary as face.mjs EXPR — mix freely). */
export const SELF_EXPR = {
  neutral: { lidU: 0.04, smile: 0.04 },
  calm: { lidU: 0.16, smile: 0.14, browIn: 0.1 },
  worried: { browIn: 0.85, browUp: 0.12, browSquish: 0.25, lidTilt: 0.32, lidU: 0.06, smile: -0.25 },
  sternKind: { browIn: -0.45, browSquish: 0.5, browUp: -0.05, lidU: 0.22, lidL: 0.16, lidTilt: -0.1, pressed: 0.3, smile: 0.1 },
  holdingBackTears: { browIn: 1, browUp: 0.12, browSquish: 0.3, lidTilt: 0.5, lidU: 0.26, lidL: 0.22, pressed: 0.85, smile: -0.4, tremble: 0.45, tears: 0.75 },
  singleTear: { browIn: 0.8, browUp: 0.1, lidTilt: 0.45, lidU: 0.3, lidL: 0.18, pressed: 0.45, smile: -0.12, tears: 0.85, tearR: 0.55, tremble: 0.15 },
  tenderSmile: { smile: 0.6, lidL: 0.4, lidU: 0.18, browIn: 0.35, lidTilt: 0.15, blush: 0.25 },
  tired: { lidU: 0.5, lidTilt: 0.28, browIn: 0.3, browUp: -0.12, smile: -0.12, lookY: 0.12 },
  wonder: { browUp: 0.75, browIn: 0.3, lidU: -0.22, open: 0.22, round: 0.55, pupil: 1.3, sparkle: 0.85, lookY: -0.25 },
  sad: { browIn: 0.9, lidTilt: 0.6, lidU: 0.32, smile: -0.45, lookY: 0.3 },
  smile: { smile: 0.8, lidL: 0.42, browUp: 0.15, blush: 0.15 },
  laughSoft: { smile: 0.85, open: 0.2, teeth: 0.6, lidL: 0.55, lidU: 0.3, browIn: 0.25, blush: 0.3 },
  surprised: { browUp: 0.85, lidU: -0.3, open: 0.32, round: 0.55, pupil: 0.9 },
  focused: { lidU: 0.3, browIn: -0.15, browSquish: 0.35, lookY: 0.45, smile: -0.05 },
  sheepish: { browIn: 0.55, browUp: 0.2, lidU: 0.15, smile: 0.35, wide: -0.1, lookX: -0.4, lookY: 0.2, blush: 0.4 },
  resolve: { browIn: -0.25, browSquish: 0.3, lidU: 0.12, pressed: 0.55, smile: -0.05 },
  dread: { browIn: 0.9, browUp: 0.5, lidU: -0.18, pupil: 0.78, smile: -0.3, open: 0.08 },
};

// brows travel only ~0.45*eyeRy in the shared rig; a human face this size needs a little more range.
const BROW_GAIN = 1.3;

// ---------------------------------------------------------------- skeleton
function skeleton(pose) {
  const t = pose.t || 0;
  const facing = pose.facing === -1 ? -1 : 1;
  const seated = !!pose.seated;
  const back = pose.view === 'back';
  const kneel = seated ? 0 : clamp(pose.kneel || 0);
  const kE = kneel * kneel * (3 - 2 * kneel);
  const walk = !seated && kneel < 0.01 && pose.walk ? pose.walk : null;
  const ph = walk ? walk.phase || 0 : 0;
  const btScreen = pose.bodyTurn ?? (walk ? 0.4 : kE * 0.45) * facing;
  const bt = clamp(btScreen * facing, -1, 1); // local (mirrored) space: + = toward the facing direction
  const th = bt * 0.9;
  const trem = clamp(pose.tremble || 0);
  const breathe = pose.breathe ?? 1;
  const br = Math.sin(t * TAU * (pose.breathRate || 0.2 + trem * 0.35)) * breathe;
  const shiver = [trem * noise1(t * 37, 1) * 1.8, trem * noise1(t * 41, 2) * 1.2];
  const crouch = clamp(pose.crouch || 0);
  let hip;
  if (seated) hip = [0, SEAT_HIP];
  else {
    const bob = walk ? -Math.cos(2 * ph) * 4 : 0;
    hip = [lerp(0, KNEEL_HIP[0], kE), lerp(HIP_Y + bob + crouch * 36, KNEEL_HIP[1], kE)];
  }
  const sway = seated ? fbm(t * 0.17, 31) * 0.006 : fbm(t * 0.19, 31) * 0.01;
  const lean = (pose.lean || 0) + kE * 0.2 + crouch * 0.12 + (walk ? 0.045 : 0) + sway + trem * noise1(t * 29, 3) * 0.008;
  const tp = (x, y) => {
    const [rx, ry] = rotP(x, y, lean);
    return [hip[0] + rx + shiver[0], hip[1] + ry + shiver[1]];
  };
  const fshift = Math.sin(th) * TORSO_D; // how far the front centre line slides with bodyTurn
  const shrug = clamp(pose.shrug || 0);
  const shY = SH_REL - br * 1.3 - shrug * 14;
  const sh = {};
  for (const side of [-1, 1]) {
    const phi = side * Math.PI / 2 + th;
    const p = tp(SX * Math.sin(phi), shY);
    sh[side] = { x: p[0], y: p[1], z: Math.cos(phi) };
  }
  const neck = tp(fshift * 0.5, NECK_REL - br * 1.4 - shrug * 6);
  const piv = tp(fshift * 0.55, PIVOT_REL - br * 1.5 - shrug * 8);
  piv[0] += pose.headDX || 0;
  piv[1] += pose.headDY || 0;
  const headRot = lean * 0.45 + (pose.headTilt || 0) + kE * 0.08 + trem * noise1(t * 26, 6) * 0.012;
  const hc = [piv[0] + Math.sin(headRot) * HEAD_UP, piv[1] - Math.cos(headRot) * HEAD_UP];
  const hp = (x, y) => { const [rx, ry] = rotP(x, y, headRot); return [hc[0] + rx, hc[1] + ry]; };
  return { t, facing, seated, back, kneel, kE, walk, ph, bt, th, trem, br, hip, lean, tp, sh, shY, neck, piv, headRot, hc, hp, fshift, crouch, shiver };
}

let DEFAULT_SK = null;
const defSk = () => (DEFAULT_SK ||= skeleton({}));

// ---------------------------------------------------------------- arm presets
// Each preset is (side, sk) => spec. side -1 = armL (screen-left when facing 1), +1 = armR.
// sk = skeleton of the current pose, so presets follow lean / kneel / seated / head motion automatically.
// spec: { target:[x,y] (WRIST, character-local), bend, front, layer, hand, handAngle, wrist, thumb,
//         prop, board, palm, reach1, reach2, shake }
export const SELF_ARMS = {
  rest: (side, k = defSk()) => ({ target: [k.sh[side].x + side * 12, k.sh[side].y + 184], bend: side, hand: 'open' }),
  onShoulder: (side, k = defSk()) => ({ target: [k.sh[side].x + side * 110, k.sh[side].y + 130], bend: -side, front: true, hand: 'drape', palm: true, wrist: side * 0.75, thumb: -side }),
  handOnHeart: (side, k = defSk()) => {
    const p = k.tp(12 + k.fshift, -96);
    return { target: [p[0] - side * 4 - 6, p[1] + 20], bend: side, front: true, hand: 'flat', handAngle: side > 0 ? -2.25 : -0.95, thumb: -1, reach2: 0.85 };
  },
  palmOut: (side, k = defSk()) => ({ target: [k.sh[side].x + side * 92, k.sh[side].y + 100], bend: -side, front: true, hand: 'palm', handAngle: -Math.PI / 2 + side * 0.22, thumb: -side }),
  reachOut: (side, k = defSk()) => ({ target: [k.sh[side].x + side * 150, k.sh[side].y + 112], bend: -side, front: true, hand: 'open', wrist: -side * 0.25, thumb: -side }),
  holdClipboard: (side, k = defSk()) => {
    const p = k.tp(side * 40 + k.fshift, -40);
    return { target: p, bend: side, front: true, hand: 'grip', handAngle: side > 0 ? Math.PI + 0.25 : -0.25, thumb: -1, prop: 'clipboard', board: [-side * 24, -38, -side * 0.12], reach2: 0.55 };
  },
  pointing: (side, k = defSk()) => ({ target: [k.sh[side].x + side * 172, k.sh[side].y + 26], bend: -side, front: true, hand: 'point', thumb: -side }),
  rubNeck: (side, k = defSk()) => {
    const p = k.hp(side * 34, 40); // behind the jaw: the hand disappears behind the head
    return { target: p, bend: -side, layer: 'side', hand: 'open', handAngle: side > 0 ? Math.PI + 0.9 : -0.9, thumb: 1 };
  },
  wipeTear: (side, k = defSk()) => {
    const e = k.hp(side * 30, 28);
    return { target: [e[0] + side * 8, e[1] + 22], bend: side, front: true, hand: 'fist', handAngle: side > 0 ? -2.05 : -1.09, thumb: -side };
  },
  rubEyes: (side, k = defSk()) => {
    const e = k.hp(side * 28, 22);
    // elbows forward (upper arm foreshortened toward camera), forearms up, heels of the hands on the eyes
    return { target: [e[0] + side * 8, e[1] + 12], bend: side, front: true, hand: 'fist', handAngle: side > 0 ? -1.85 : -1.29, thumb: -side, reach1: 0.5, reach2: 1.25 };
  },
  clasped: (side, k = defSk()) => {
    const p = k.tp(k.fshift * 0.8 + side * 12, -22);
    return { target: p, bend: side, front: true, hand: 'open', handAngle: side > 0 ? 2.4 : 0.74, thumb: 1, reach2: 0.8 };
  },
  coverMouth: (side, k = defSk()) => {
    const m = k.hp(side * 6, 62);
    return { target: [m[0] + side * 16, m[1] + 22], bend: side, front: true, hand: 'flat', handAngle: side > 0 ? -2.3 : -0.84, thumb: -1 };
  },
  // ---- seated (desk line = local y 0, the desk surface extends toward the viewer, y > 0)
  handsOnDesk: (side, k = defSk()) => ({ target: [side * 42 + (k.fshift || 0), 30], bend: side, front: true, hand: 'flat', handAngle: side > 0 ? Math.PI - 0.32 : 0.32, thumb: -1, reach2: 0.52 }),
  holdNotebook: (side, k = defSk()) => {
    const p = k.seated ? [side * 54 + k.fshift, -36] : k.tp(side * 54 + k.fshift, -60);
    return { target: p, bend: side, front: true, hand: 'grip', handAngle: side > 0 ? -1.8 : -1.34, thumb: -side, prop: 'notebook', reach2: 0.62 };
  },
  showNotebook: (side, k = defSk()) => {
    const p = k.seated ? [side * 38 + k.fshift, -14] : k.tp(side * 38 + k.fshift, -40);
    return { target: p, bend: side, front: true, hand: 'grip', handAngle: side > 0 ? -2.0 : -1.14, thumb: -side, prop: 'notebookCover', reach2: 0.55 };
  },
  chinInHand: (side, k = defSk()) => {
    const c = k.hp(side * 8, 88);
    return { target: c, bend: side, front: true, hand: 'cup', handAngle: -Math.PI / 2 - side * 0.3, thumb: -side, reach2: 1.22 };
  },
};

function resolveArm(a, side, k, def) {
  if (!a) a = def;
  if (typeof a === 'string') return { ...(SELF_ARMS[a] || SELF_ARMS.rest)(side, k), name: a };
  if (a.preset) {
    const base = (SELF_ARMS[a.preset] || SELF_ARMS.rest)(side, k);
    return { ...base, ...a, name: a.preset };
  }
  return { bend: side, hand: 'open', ...a };
}

/**
 * Convert a WORLD point into this character's local arm-target coords (for onShoulder etc.).
 * (x, y, scale, facing) are the same values you pass to drawSelf.
 */
export function selfLocal(x, y, scale, facing, wx, wy) {
  return [((wx - x) / scale) * (facing === -1 ? -1 : 1), (wy - y) / scale];
}

/** Where things are for a given pose, in WORLD coords (eyelines, props, camera targets). */
export function selfPoseAnchors(x, y, scale, pose = {}) {
  const k = skeleton(pose);
  const f = k.facing;
  const W = (p) => [x + p[0] * scale * f, y + p[1] * scale];
  return {
    headCenter: W(k.hc), headTop: W(k.hp(0, -110)), eyes: W(k.hp(0, 2)), mouth: W(k.hp(0, 37)),
    chin: W(k.hp(0, 62)), neck: W(k.neck), shoulderL: W([k.sh[-1].x, k.sh[-1].y]), shoulderR: W([k.sh[1].x, k.sh[1].y]),
    chest: W(k.tp(k.fshift, -92)), hip: W(k.hip),
  };
}

// static anchors (scale 1, facing 1, neutral, t=0, no breath); see docs/self.md
export const ANCHORS = (() => {
  const a = (pose) => {
    const k = skeleton({ t: 0, breathe: 0, ...pose });
    const r = (p) => p.map((v) => Math.round(v));
    return {
      headTop: r(k.hp(0, -110)), headCenter: r(k.hc), eyes: r(k.hp(0, 2)), mouth: r(k.hp(0, 37)), chin: r(k.hp(0, 62)),
      neck: r(k.neck), shoulderL: r([k.sh[-1].x, k.sh[-1].y]), shoulderR: r([k.sh[1].x, k.sh[1].y]),
      chest: r(k.tp(k.fshift, -92)), hip: r(k.hip), armReach: UPPER + FORE, handLen: Math.round(34 * HAND_S),
    };
  };
  return { ...a({}), seated: a({ seated: true }), kneel: a({ kneel: 1 }) };
})();

// ---------------------------------------------------------------- main
export function drawSelf(g, x, y, scale = 1, pose = {}) {
  const k = skeleton(pose);
  const facing = k.facing;
  const outfit = pose.outfit === 'ceo' ? 'ceo' : 'sweater';
  const layer = pose.layer || 'all';
  const back = k.back;

  g.save();
  if (pose.alpha != null) g.globalAlpha = clamp(pose.alpha);
  g.translate(x, y);
  g.scale(scale, scale);
  if (pose.shadow !== false && !k.seated && layer !== 'front') groundShadow(g, k.hip[0] * facing * 0.4, 0, 96 + k.kE * 40, 0.3);
  g.scale(facing, 1);
  g.lineCap = 'round';
  g.lineJoin = 'round';

  // ---- arms
  const defL = k.seated ? 'handsOnDesk' : pose.clipboard ? 'holdClipboard' : 'rest';
  const defR = k.seated ? 'handsOnDesk' : 'rest';
  const arms = [resolveArm(pose.armL, -1, k, defL), resolveArm(pose.armR, 1, k, defR)];
  if (k.walk) {
    for (const side of [-1, 1]) {
      const a = arms[side < 0 ? 0 : 1];
      if (a.name === 'rest' && !a.noSwing) {
        const sw = side * Math.sin(k.ph);
        a.target = [a.target[0] + sw * 30, a.target[1] - Math.abs(sw) * 6];
      }
    }
  }
  if (pose.clipboard && !arms[0].prop) arms[0].prop = 'clipboard';
  const geo = arms.map((a, i) => armGeom(a, i ? 1 : -1, k));
  // layer per arm: 'back' (behind torso), 'side' (after torso, before head), 'front' (after head)
  const lay = geo.map((q) => {
    const a = q.a;
    let L = a.layer || (a.front ? 'front' : k.sh[q.side].z < -0.2 ? 'back' : 'side');
    if (back) L = L === 'front' || L === 'back' ? 'back' : 'side';
    return L;
  });
  const ctx = { k, outfit, pose, back, sil: silhouette(k, outfit) };

  if (layer !== 'front') {
    if (back) {
      // seen from behind, arms raised in front of the body (to the face, a console, a notebook) are hidden by
      // the head and shoulders: only what pokes out below the shoulder line (elbows) can show
      g.save();
      g.beginPath();
      g.rect(-600, Math.min(k.sh[-1].y, k.sh[1].y) - 6, 1200, 1200);
      g.clip();
      drawArmGroup(g, geo.filter((_, i) => lay[i] === 'back' && arms[i].front), ctx, false);
      g.restore();
      drawArmGroup(g, geo.filter((_, i) => lay[i] === 'back' && !arms[i].front), ctx, false);
    } else drawArmGroup(g, geo.filter((_, i) => lay[i] === 'back'), ctx, false);
    if (!k.seated) drawLegs(g, k, outfit);
    withDeskClip(g, k, () => {
      if (back) {
        drawNeck(g, k, true);
        drawTorsoBody(g, ctx);
      } else {
        drawTorsoBody(g, ctx);
        drawNeck(g, k, false);
        drawTorsoFront(g, ctx);
      }
    });
    drawArmGroup(g, geo.filter((_, i) => lay[i] === 'side'), ctx, true);
    drawHead(g, k, pose, back);
  }
  if (layer !== 'body') drawArmGroup(g, geo.filter((_, i) => lay[i] === 'front'), ctx, true);
  g.restore();
}

function withDeskClip(g, k, fn) {
  if (!k.seated) return fn();
  g.save();
  g.beginPath();
  g.rect(-500, -1000, 1000, 1000);
  g.clip();
  fn();
  g.restore();
}

// ---------------------------------------------------------------- torso silhouettes (torso-local coords)
function emit(g, cmds, map) {
  for (const c of cmds) {
    if (c[0] === 'M') { const p = map(c[1], c[2]); g.moveTo(p[0], p[1]); }
    else if (c[0] === 'L') { const p = map(c[1], c[2]); g.lineTo(p[0], p[1]); }
    else if (c[0] === 'Q') { const a = map(c[1], c[2]), b = map(c[3], c[4]); g.quadraticCurveTo(a[0], a[1], b[0], b[1]); }
    else if (c[0] === 'C') { const a = map(c[1], c[2]), b = map(c[3], c[4]), d = map(c[5], c[6]); g.bezierCurveTo(a[0], a[1], b[0], b[1], d[0], d[1]); }
    else g.closePath();
  }
}
const ID = (x, y) => [x, y];

function projections(k) {
  const th = k.th;
  const sxs = Math.sqrt(Math.cos(th) ** 2 + (TORSO_D / 72) ** 2 * Math.sin(th) ** 2);
  const sgn = k.back ? -1 : 1;
  const F = (x, w = 74) => x * Math.cos(th) + Math.sqrt(Math.max(0, 1 - (x / w) ** 2)) * TORSO_D * Math.sin(th) * sgn;
  const S = (x) => x * sxs;
  return { F, S };
}

function sweaterCmds(F, S, shY) {
  return [
    ['M', F(-24), shY - 24],
    ['C', S(-40), shY - 22, S(-54), shY - 20, S(-63), shY - 16],
    ['C', S(-74), shY - 11, S(-79), shY + 2, S(-79), shY + 22],
    ['C', S(-79), shY + 62, S(-77), -32, S(-70), -8],
    ['L', S(-66), 14],
    ['Q', F(0), 21, S(66), 14],
    ['L', S(70), -8],
    ['C', S(77), -32, S(79), shY + 62, S(79), shY + 22],
    ['C', S(79), shY + 2, S(74), shY - 11, S(63), shY - 16],
    ['C', S(54), shY - 20, S(40), shY - 22, F(24), shY - 24],
    ['Q', F(0), shY - 29, F(-24), shY - 24],
    ['Z'],
  ];
}
function blazerCmds(F, S, shY) {
  return [
    ['M', F(-27), shY - 27],
    ['C', S(-44), shY - 25, S(-60), shY - 23, S(-70), shY - 19],
    ['C', S(-80), shY - 14, S(-83), shY - 2, S(-82), shY + 18],
    ['C', S(-81), shY + 64, S(-79), -16, S(-77), 30],
    ['Q', F(-40), 37, F(0), 34],
    ['Q', F(40), 37, S(77), 30],
    ['C', S(79), -16, S(81), shY + 64, S(82), shY + 18],
    ['C', S(83), shY - 2, S(80), shY - 14, S(70), shY - 19],
    ['C', S(60), shY - 23, S(44), shY - 25, F(27), shY - 27],
    ['Q', F(0), shY - 34, F(-27), shY - 27],
    ['Z'],
  ];
}
function silhouette(k, outfit) {
  const { F, S } = projections(k);
  return outfit === 'ceo' ? blazerCmds(F, S, k.shY) : sweaterCmds(F, S, k.shY);
}

function torsoFrame(g, k) {
  g.translate(k.hip[0] + k.shiver[0], k.hip[1] + k.shiver[1]);
  g.rotate(k.lean);
}

function clothGrad(g, k, outfit, map = ID) {
  const ceo = outfit === 'ceo';
  const lx = -40 * k.facing; // light stays upper-left on screen when mirrored
  const a = map(lx, k.shY + 18), b = map(-6 * k.facing, -40);
  const gr = g.createRadialGradient(a[0], a[1], 10, b[0], b[1], ceo ? 165 : 155);
  gr.addColorStop(0, ceo ? C.blazerLight : C.sweaterLight);
  gr.addColorStop(0.45, ceo ? C.blazer : C.sweater);
  gr.addColorStop(1, ceo ? C.blazerShade : C.sweaterShade);
  return gr;
}
function sweaterGrad(g, k, map = ID) { return clothGrad(g, k, 'sweater', map); }

function drawTorsoBody(g, ctx) {
  const { k, outfit, back } = ctx;
  const { F, S } = projections(k);
  const shY = k.shY;
  g.save();
  torsoFrame(g, k);
  // sweater
  g.beginPath();
  emit(g, sweaterCmds(F, S, shY), ID);
  g.fillStyle = sweaterGrad(g, k);
  g.fill();
  g.strokeStyle = C.sweaterLine;
  g.lineWidth = 3;
  g.stroke();
  if (outfit !== 'ceo') sweaterDetails(g, F, S, shY, back);
  if (outfit === 'ceo') blazerBody(g, k, F, S, shY, back);
  if (back) backCollar(g, F, shY, outfit);
  g.restore();
}

function sweaterDetails(g, F, S, shY, back) {
  // ribbed hem band
  g.save();
  g.beginPath();
  g.moveTo(S(-69), -8);
  g.lineTo(S(-66), 14);
  g.quadraticCurveTo(F(0), 21, S(66), 14);
  g.lineTo(S(69), -8);
  g.quadraticCurveTo(F(0), -1, S(-69), -8);
  g.closePath();
  g.fillStyle = rgba(C.sweaterShade, 0.8);
  g.fill();
  g.strokeStyle = C.sweaterLine;
  g.lineWidth = 2.4;
  g.stroke();
  g.clip();
  g.strokeStyle = rgba(C.sweaterLine, 0.25);
  g.lineWidth = 1.6;
  for (let i = -6; i <= 6; i++) {
    const xx = S(i * 10.5);
    g.beginPath(); g.moveTo(xx, -8); g.lineTo(xx, 20); g.stroke();
  }
  g.restore();
  // soft folds where the oversized knit bunches above the hem
  g.strokeStyle = rgba(C.sweaterLine, 0.32);
  g.lineWidth = 2.2;
  for (const s of [-1, 1]) {
    g.beginPath(); g.moveTo(S(s * 62), -34); g.quadraticCurveTo(S(s * 50), -22, S(s * 40), -14); g.stroke();
    g.beginPath(); g.moveTo(S(s * 70), -66); g.quadraticCurveTo(S(s * 62), -54, S(s * 58), -42); g.stroke();
  }
  if (!back) {
    g.beginPath(); g.moveTo(F(-8), -40); g.quadraticCurveTo(F(0), -30, F(10), -24); g.stroke();
  }
}

function backCollar(g, F, shY, outfit) {
  const ceo = outfit === 'ceo';
  g.fillStyle = ceo ? C.blazerShade : C.sweaterShade;
  g.strokeStyle = ceo ? C.blazerLine : C.sweaterLine;
  g.lineWidth = 2.6;
  g.beginPath();
  g.moveTo(F(-27), shY - 21);
  g.quadraticCurveTo(F(0), shY - 12, F(27), shY - 21);
  g.lineTo(F(23), shY - (ceo ? 34 : 29));
  g.quadraticCurveTo(F(0), shY - (ceo ? 27 : 23), F(-23), shY - (ceo ? 34 : 29));
  g.closePath();
  g.fill(); g.stroke();
}

const V_BOTTOM = -64; // blazer button / bottom of the V (torso-local)
function vOpening(g, F, shY) {
  g.moveTo(F(-17), shY - 22);
  g.lineTo(F(0), V_BOTTOM);
  g.lineTo(F(12), -6);
  g.lineTo(F(26), 40);
  g.lineTo(F(-20), 40);
  g.lineTo(F(-8), -6);
  g.lineTo(F(0), V_BOTTOM);
  g.lineTo(F(17), shY - 22);
  g.closePath();
}

function blazerBody(g, k, F, S, shY, back) {
  const gr = clothGrad(g, k, 'ceo');
  g.save();
  if (!back) {
    g.beginPath();
    g.rect(-300, -400, 600, 500);
    vOpening(g, F, shY);
    g.clip('evenodd');
  }
  g.beginPath();
  emit(g, blazerCmds(F, S, shY), ID);
  g.fillStyle = gr;
  g.fill();
  g.strokeStyle = C.blazerLine;
  g.lineWidth = 3;
  g.stroke();
  g.restore();
  if (back) {
    g.strokeStyle = rgba(C.blazerLine, 0.7);
    g.lineWidth = 2;
    g.beginPath(); g.moveTo(F(0), shY - 8); g.quadraticCurveTo(F(2), -60, F(0), 33); g.stroke();
    g.beginPath(); g.moveTo(F(5), -2); g.lineTo(F(5), 32); g.stroke();
    g.strokeStyle = rgba(C.blazerLine, 0.35);
    for (const s of [-1, 1]) { g.beginPath(); g.moveTo(F(s * 56), shY + 42); g.quadraticCurveTo(F(s * 42), shY + 54, F(s * 26), shY + 52); g.stroke(); }
    return;
  }
  // opening edges
  g.strokeStyle = C.blazerLine;
  g.lineWidth = 2.6;
  g.beginPath(); g.moveTo(F(0), V_BOTTOM); g.lineTo(F(12), -6); g.quadraticCurveTo(F(19), 14, F(26), 33); g.stroke();
  g.beginPath(); g.moveTo(F(-8), -6); g.quadraticCurveTo(F(-13), 14, F(-20), 33); g.stroke();
  // pocket flaps + a fold
  g.strokeStyle = rgba(C.blazerLine, 0.85);
  g.lineWidth = 2.2;
  for (const s of [-1, 1]) { g.beginPath(); g.moveTo(F(s * 32), -6); g.lineTo(F(s * 60), -8); g.stroke(); }
  g.strokeStyle = rgba(C.blazerLine, 0.35);
  g.beginPath(); g.moveTo(F(-62), shY + 66); g.quadraticCurveTo(F(-54), shY + 78, F(-42), shY + 82); g.stroke();
}

function drawTorsoFront(g, ctx) {
  const { k, outfit } = ctx;
  const { F } = projections(k);
  const shY = k.shY;
  g.save();
  torsoFrame(g, k);
  // ribbed crew neck (visible in both outfits)
  g.fillStyle = C.sweaterShade;
  g.strokeStyle = C.sweaterLine;
  g.lineWidth = 2.6;
  g.beginPath();
  g.moveTo(F(-29), shY - 22);
  g.quadraticCurveTo(F(0), shY + 2, F(29), shY - 22);
  g.quadraticCurveTo(F(24), shY - 27, F(19), shY - 25);
  g.quadraticCurveTo(F(0), shY - 9, F(-19), shY - 25);
  g.quadraticCurveTo(F(-24), shY - 27, F(-29), shY - 22);
  g.closePath();
  g.fill(); g.stroke();
  g.strokeStyle = rgba(C.sweaterLine, 0.3);
  g.lineWidth = 1.4;
  for (let i = -3; i <= 3; i++) {
    const x0 = F(i * 7.5), y0 = shY - 19 + Math.abs(i) * -1.2 + (3 - Math.abs(i)) * 3.2;
    g.beginPath(); g.moveTo(x0, y0 - 3); g.lineTo(x0 * 1.06, y0 + 4); g.stroke();
  }
  if (outfit === 'ceo') {
    g.strokeStyle = C.blazerLine;
    g.lineWidth = 2.6;
    // lapels
    for (const s of [-1, 1]) {
      g.fillStyle = s * k.facing < 0 ? C.blazerLight : C.blazer;
      g.beginPath();
      g.moveTo(F(s * 17), shY - 22);
      g.lineTo(F(s * 29), shY - 25);
      g.quadraticCurveTo(F(s * 40), shY + 2, F(s * 45), shY + 24);
      g.lineTo(F(s * 35), shY + 27);
      g.lineTo(F(s * 39), shY + 36);
      g.quadraticCurveTo(F(s * 18), V_BOTTOM - 14, F(s * 1), V_BOTTOM);
      g.closePath();
      g.fill(); g.stroke();
    }
    g.fillStyle = C.blazerShade;
    circle(g, F(-2), V_BOTTOM + 9, 4.4);
    g.fill(); g.stroke();
    // CEO badge on the wearer's left lapel (screen right when facing 1); text stays readable when mirrored
    g.save();
    g.translate(F(33), shY + 14);
    g.rotate(-0.32);
    g.scale(k.facing, 1);
    drawBadge(g);
    g.restore();
  }
  g.restore();
}

function drawBadge(g) {
  const w = 25, h = 11.5;
  g.fillStyle = C.badge;
  g.strokeStyle = C.badgeShade;
  g.lineWidth = 1.6;
  g.beginPath();
  g.roundRect(-w / 2, -h / 2, w, h, 3);
  g.fill(); g.stroke();
  g.fillStyle = rgba(C.badgeLight, 0.85);
  g.fillRect(-w / 2 + 2.5, -h / 2 + 1.6, w - 5, 2);
  // "CEO" in vector strokes (no font dependency)
  g.strokeStyle = '#5a3e10';
  g.lineWidth = 1.3;
  g.lineCap = 'round';
  g.beginPath(); g.arc(-6.8, 0.3, 2.7, Math.PI * 0.28, Math.PI * 1.72); g.stroke();
  g.beginPath(); g.moveTo(1.7, -2.5); g.lineTo(-1.6, -2.5); g.lineTo(-1.6, 3); g.lineTo(1.7, 3); g.moveTo(-1.6, 0.3); g.lineTo(1.1, 0.3); g.stroke();
  g.beginPath(); g.ellipse(6.6, 0.3, 2.5, 2.8, 0, 0, TAU); g.stroke();
}

// ---------------------------------------------------------------- neck
function drawNeck(g, k, back) {
  const [nx, ny] = k.neck;
  const [px, py] = k.piv;
  const [cx, cy] = k.hp(0, 58);
  g.strokeStyle = C.skinLine;
  const nb = back ? 6 : -8; // front: keep the rounded neck end inside the collar opening
  g.lineWidth = 36;
  g.beginPath(); g.moveTo(nx, ny + nb); g.lineTo(px, py - 8); g.stroke();
  // jaw shadow falls on the upper neck
  const gr = g.createLinearGradient(cx, cy, nx, ny);
  gr.addColorStop(0, back ? shade(C.skin, -0.04) : C.skinShade);
  gr.addColorStop(0.55, back ? shade(C.skin, -0.08) : shade(C.skin, -0.03));
  gr.addColorStop(1, shade(C.skin, -0.1));
  g.strokeStyle = gr;
  g.lineWidth = 31;
  g.beginPath(); g.moveTo(nx, ny + nb); g.lineTo(px, py - 8); g.stroke();
}

// ---------------------------------------------------------------- legs
function drawLegs(g, k, outfit) {
  const { hip, kE, walk, ph, th } = k;
  const legs = [];
  const fwd = th >= 0 ? 1 : -1;
  const turnAmt = Math.min(1, Math.abs(Math.sin(th)) * 1.6 + (walk ? 0.45 : 0) + kE);
  for (const side of [-1, 1]) {
    const phi = side * Math.PI / 2 + th;
    const hx = hip[0] + HIP_W * Math.sin(phi), hy = hip[1] + 4;
    const z = Math.cos(phi);
    // standing: ankle placed so the leg is just short of straight
    let ax = hip[0] * 0.2 + side * 25 * Math.cos(th), ay = hy + THIGH + SHIN - 3;
    ay = Math.min(ay, ANKLE_Y);
    let kneeDir = Math.abs(th) > 0.05 ? fwd : side;
    let shoeRot = 0;
    if (walk) {
      const st = (side < 0 ? 1 : -1) * Math.sin(ph);
      const lift = Math.max(0, (side < 0 ? 1 : -1) * Math.cos(ph));
      ax = hx * 1.15 + st * 38 * fwd;
      ay = ANKLE_Y - lift * 22;
      kneeDir = fwd;
      shoeRot = -st * 0.14 * fwd - lift * 0.18 * fwd;
    }
    if (kE > 0) {
      // the leg on the facing side plants its foot forward (knee up); the other kneels (knee on the ground)
      const front = side === fwd;
      const kx = front ? hip[0] + 108 * fwd : hip[0] - 100 * fwd;
      const ky = front ? ANKLE_Y : -40;
      ax = lerp(ax, kx, kE);
      ay = lerp(ay, ky, kE);
      kneeDir = fwd;
      if (!front) shoeRot = lerp(0, fwd * 1.75, kE);
    }
    legs.push({ side, hx, hy, ax, ay, kneeDir, z, shoeRot });
  }
  legs.sort((a, b) => a.z - b.z);
  for (const L of legs) drawLeg(g, L, outfit, turnAmt, fwd, legs.indexOf(L) === 0 && Math.abs(th) > 0.05);
}

function drawLeg(g, L, outfit, turnAmt, fwd, far) {
  const { a1, a2 } = ik(L.hx, L.hy, L.ax, L.ay, THIGH, SHIN, L.kneeDir);
  const kx = L.hx + Math.cos(a1) * THIGH, ky = L.hy + Math.sin(a1) * THIGH;
  const ax = kx + Math.cos(a1 + a2) * SHIN, ay = ky + Math.sin(a1 + a2) * SHIN;
  let pants = outfit === 'ceo' ? C.pantsCeo : C.pants;
  if (far) pants = shade(pants, -0.12);
  const W1 = 50, W2 = 44;
  drawShoe(g, ax, ay, L.side, turnAmt, fwd, L.shoeRot, far);
  const ux = Math.cos(a1 + a2), uy = Math.sin(a1 + a2);
  const cx = ax - ux * 1, cy = ay - uy * 1; // trouser hem: a flat edge at the ankle, over the shoe top
  g.strokeStyle = C.pantsLine;
  g.lineCap = 'butt';
  g.lineWidth = W2 + 5.5;
  g.beginPath(); g.moveTo(kx - ux * 10, ky - uy * 10); g.lineTo(cx + ux * 2.5, cy + uy * 2.5); g.stroke();
  g.lineCap = 'round';
  g.lineWidth = W1 + 5.5;
  g.beginPath(); g.moveTo(L.hx, L.hy); g.lineTo(kx, ky); g.stroke();
  g.strokeStyle = pants;
  g.lineCap = 'butt';
  g.lineWidth = W2;
  g.beginPath(); g.moveTo(kx - ux * 10, ky - uy * 10); g.lineTo(cx, cy); g.stroke();
  g.lineCap = 'round';
  g.lineWidth = W1;
  g.beginPath(); g.moveTo(L.hx, L.hy); g.lineTo(kx, ky); g.stroke();
  // rounded knee joint fill (covers the butt end of the shin)
  g.beginPath(); g.arc(kx, ky, W2 / 2, 0, TAU); g.fillStyle = pants; g.fill();
  // soft light along the lit side
  g.strokeStyle = rgba(C.pantsLight, far ? 0.25 : 0.5);
  g.lineWidth = 9;
  const off = (x0, y0, x1, y1, w) => {
    const l = Math.hypot(x1 - x0, y1 - y0) || 1;
    let nx = -(y1 - y0) / l, ny = (x1 - x0) / l;
    if (nx > 0) { nx = -nx; ny = -ny; }
    return [x0 + nx * w, y0 + ny * w, x1 + nx * w, y1 + ny * w];
  };
  const o1 = off(L.hx, L.hy + 14, kx, ky, W1 * 0.26), o2 = off(kx, ky, cx, cy - 4, W2 * 0.26);
  g.beginPath(); g.moveTo(o1[0], o1[1]); g.lineTo(o1[2], o1[3]); g.lineTo(o2[2], o2[3]); g.stroke();
  // knee crease when bent
  const bendAmt = Math.abs(a2);
  if (bendAmt > 0.3) {
    g.strokeStyle = rgba(C.pantsLine, Math.min(0.55, bendAmt * 0.45));
    g.lineWidth = 2.4;
    const n = a1 + a2 / 2 + (a2 > 0 ? Math.PI / 2 : -Math.PI / 2);
    g.beginPath();
    g.arc(kx + Math.cos(n) * 4, ky + Math.sin(n) * 4, 13, n + Math.PI - 0.6, n + Math.PI + 0.6);
    g.stroke();
  }
  // trouser hem fold
  g.strokeStyle = rgba(C.pantsLine, 0.55);
  g.lineWidth = 2;
  const nx = -uy, ny = ux;
  g.beginPath();
  g.moveTo(cx + nx * (W2 / 2 - 2) - ux * 9, cy + ny * (W2 / 2 - 2) - uy * 9);
  g.quadraticCurveTo(cx - ux * 6, cy - uy * 6, cx - nx * (W2 / 2 - 2) - ux * 9, cy - ny * (W2 / 2 - 2) - uy * 9);
  g.stroke();
}

function drawShoe(g, ax, ay, side, turnAmt, fwd, rot, far) {
  g.save();
  g.translate(ax, ay);
  g.rotate(rot);
  // blend a front-on rounded toe cap with a side-on profile (toe toward the facing direction)
  const m = clamp(turnAmt), d = fwd;
  const off = side * 3 * (1 - m);
  const P = (fx, fy, sx, sy) => [lerp(fx + off, sx * d, m), lerp(fy, sy, m)];
  const p0 = P(-25, 21, -15, 21), c1 = P(-29, 0, -19, 2), c2 = P(-16, -12, -13, -10), p1 = P(0, -12, 0, -10);
  const c3 = P(16, -12, 15, -8), c4 = P(29, 0, 37, 2), p2 = P(25, 21, 34, 21);
  g.fillStyle = far ? shade(C.shoe, -0.14) : C.shoe;
  g.strokeStyle = C.shoeLine;
  g.lineWidth = 2.8;
  g.beginPath();
  g.moveTo(p0[0], p0[1]);
  g.bezierCurveTo(c1[0], c1[1], c2[0], c2[1], p1[0], p1[1]);
  g.bezierCurveTo(c3[0], c3[1], c4[0], c4[1], p2[0], p2[1]);
  g.closePath();
  g.fill();
  g.stroke();
  // sole
  const x0 = Math.min(p0[0], p2[0]), x1 = Math.max(p0[0], p2[0]);
  g.fillStyle = C.sole;
  g.beginPath();
  g.roundRect(x0 - 1.5, 16, x1 - x0 + 3, 7, 3);
  g.fill();
  g.stroke();
  // toe highlight
  const hx = lerp(off - 6, d * 18, m);
  g.fillStyle = 'rgba(255,228,205,0.3)';
  ellipse(g, hx, 2, 8, 4);
  g.fill();
  g.restore();
}

// ---------------------------------------------------------------- head
function drawHead(g, k, pose, back) {
  const t = k.t, facing = k.facing;
  const btScreen = pose.bodyTurn ?? (k.walk ? 0.4 : k.kE * 0.45) * facing;
  const defTurn = pose.bodyTurn != null || k.walk || k.kE > 0 ? btScreen * 0.5 : 0;
  const turnScreen = clamp(pose.headTurn ?? defTurn, -1, 1);
  const u = turnScreen * facing; // geometric (mirrored-space) turn
  const sway = fbm(t * 0.55, 21) * 0.16 - (pose.headTilt || 0) * 0.7 - k.lean * 0.5 + (pose.hairWind || 0) * 0.5 +
    (k.walk ? Math.sin(k.ph * 2) * 0.12 : 0) + k.trem * noise1(t * 22, 9) * 0.2;
  g.save();
  g.translate(k.hc[0], k.hc[1]);
  g.rotate(k.headRot);
  if (back) {
    // back view: 0..~0.55 = back of head with an emerging lost profile;
    // beyond that the head swings into a 3/4 "looking back over the shoulder" face (short crossfade)
    const m = sstep(0.56, 0.68, Math.abs(u));
    if (m < 1) drawHeadBack(g, k, pose, u, sway);
    if (m > 0) {
      const s = u >= 0 ? 1 : -1;
      const uf = s * (0.62 + 0.3 * sstep(0.6, 1, Math.abs(u)));
      if (m < 1) { g.save(); g.globalAlpha *= m; }
      drawHeadFront(g, k, pose, uf, sway, uf * facing, true);
      if (m < 1) g.restore();
    }
  } else drawHeadFront(g, k, pose, u, sway, turnScreen, false);
  g.restore();
}

function headPath(g, u) {
  const kx = (x) => x * (x * u > 0 ? 1 + 0.04 * Math.abs(u) : 1 - 0.08 * Math.abs(u)) + u * 3;
  g.beginPath();
  g.moveTo(kx(0) + u * 8, 61);
  g.bezierCurveTo(kx(-28) + u * 5, 62, kx(-50), 50, kx(-57), 26);
  g.bezierCurveTo(kx(-62), 6, kx(-62), -36, kx(-55), -58);
  g.bezierCurveTo(kx(-46), -82, kx(-24), -90, kx(0), -90);
  g.bezierCurveTo(kx(24), -90, kx(46), -82, kx(55), -58);
  g.bezierCurveTo(kx(62), -36, kx(62), 6, kx(57), 26);
  g.bezierCurveTo(kx(50), 50, kx(28) + u * 5, 62, kx(0) + u * 8, 61);
  g.closePath();
}

function earPos(side, yaw) {
  const phi = side * 1.68 + yaw;
  return { x: 58 * Math.sin(phi), z: Math.cos(phi), w: 0.5 + 0.5 * Math.abs(Math.sin(phi)) };
}

function drawEar(g, x, side, w, backSide) {
  g.save();
  g.translate(x, 6);
  g.scale(w * 0.9, 0.92);
  g.fillStyle = backSide ? shade(C.skin, -0.1) : C.skin;
  g.strokeStyle = C.skinLine;
  g.lineWidth = 2.6;
  g.beginPath();
  g.moveTo(side * -2, -12);
  g.bezierCurveTo(side * 12, -20, side * 17, -4, side * 12, 6);
  g.bezierCurveTo(side * 9, 13, side * 4, 17, side * -2, 14);
  g.closePath();
  g.fill(); g.stroke();
  g.strokeStyle = rgba(C.skinLine, 0.5);
  g.lineWidth = 2;
  g.beginPath();
  if (!backSide) { g.moveTo(side * 2, -8); g.bezierCurveTo(side * 10, -10, side * 11, 2, side * 5, 6); }
  else { g.moveTo(side * 3, -10); g.quadraticCurveTo(side * 1, 2, side * 3, 12); }
  g.stroke();
  g.restore();
}

function hairGrad(g, lx) {
  const gr = g.createRadialGradient(lx, -92, 4, 0, -56, 104);
  gr.addColorStop(0, C.hairLight);
  gr.addColorStop(0.45, C.hair);
  gr.addColorStop(1, C.hairShade);
  return gr;
}

/** pointed hair lock from root (rx,ry) to tip (tx,ty); w = width at root; bend = sideways curvature */
function lock(g, rx, ry, tx, ty, w, bend) {
  const dx = tx - rx, dy = ty - ry, L = Math.hypot(dx, dy) || 1;
  const nx = -dy / L, ny = dx / L;
  const mx = rx + dx * 0.5 + nx * bend * L, my = ry + dy * 0.5 + ny * bend * L;
  // wound the same way as the cap shapes so a nonzero fill unions them without holes
  g.moveTo(rx - nx * w / 2, ry - ny * w / 2);
  g.quadraticCurveTo(mx - nx * w * 0.42, my - ny * w * 0.42, tx, ty);
  g.quadraticCurveTo(mx + nx * w * 0.42, my + ny * w * 0.42, rx + nx * w / 2, ry + ny * w / 2);
  g.closePath();
}

/** draw a union of hair shapes with one clean outer outline (stroke pass, then fill pass) */
function hairMass(g, build, fill) {
  g.beginPath();
  build();
  g.strokeStyle = C.hairLine;
  g.lineWidth = 5.6;
  g.stroke();
  g.fillStyle = fill;
  g.fill('nonzero');
}

function drawHeadFront(g, k, pose, u, sway, turnScreen, overShoulder) {
  const t = k.t, facing = k.facing;
  const yaw = u * 0.62;
  const lx = -24 * facing; // keep the light upper-left on screen even when mirrored
  // back hair (behind head)
  g.fillStyle = C.hairShade;
  g.strokeStyle = C.hairLine;
  g.lineWidth = 3;
  ellipse(g, u * 4, -62, 64, 44);
  g.fill(); g.stroke();

  const ears = [-1, 1].map((s) => ({ s, ...earPos(s, yaw) }));
  for (const e of ears) if (e.z < 0.05) drawEar(g, e.x, e.s, e.w, false);

  // head
  const gr = g.createRadialGradient(lx + u * 16, -32, 8, u * 6, -4, 96);
  gr.addColorStop(0, C.skinLight);
  gr.addColorStop(0.5, C.skin);
  gr.addColorStop(1, C.skinShade);
  headPath(g, u);
  g.fillStyle = gr;
  g.fill();
  g.strokeStyle = C.skinLine;
  g.lineWidth = 3;
  g.stroke();
  // gentle cheek warmth (always a little)
  for (const s of [-1, 1]) {
    const cx = s * 37 * (1 - Math.abs(u) * 0.2) + u * 14, cy = 26;
    const gc = g.createRadialGradient(cx, cy, 1, cx, cy, 17);
    gc.addColorStop(0, 'rgba(232,128,110,0.2)');
    gc.addColorStop(1, 'rgba(232,128,110,0)');
    g.fillStyle = gc;
    g.fillRect(cx - 18, cy - 18, 36, 36);
  }
  for (const e of ears) if (e.z >= 0.05) drawEar(g, e.x, e.s, e.w, false);

  // face (drawn in screen orientation)
  g.save();
  g.scale(facing, 1);
  const face = makeExpr(pose.face || {});
  face.t = t;
  face.turn = turnScreen;
  face.browUp *= BROW_GAIN; face.browIn *= BROW_GAIN; face.browUpL *= BROW_GAIN; face.browUpR *= BROW_GAIN;
  if (!face.noAutoBlink) face.blink = clamp((face.blink || 0) + autoBlink(t, 23, 0.26 + k.trem * 0.2));
  drawFace(g, SELF_FACE, face);
  g.restore();

  drawFrontHair(g, u, lx, sway);
}

function drawFrontHair(g, u, lx, sway) {
  const p = u * 10; // fringe slides with yaw
  const o = u * 4;
  const sw = sway;
  const farL = Math.max(0, u), farR = Math.max(0, -u); // sideburn on the far side tucks in
  hairMass(g, () => {
    // crown cap with an arched hairline
    g.moveTo(-60 + o + farL * 6, -18);
    g.quadraticCurveTo(-72 + o, -86, -22 + o, -106);
    g.quadraticCurveTo(4 + o, -114, 30 + o, -104);
    g.quadraticCurveTo(74 + o, -86, 60 + o - farR * 6, -18);
    g.quadraticCurveTo(44 + p, -56, 8 + p, -60);
    g.quadraticCurveTo(-36 + p, -60, -60 + o + farL * 6, -18);
    g.closePath();
    // fringe locks sweeping toward screen-left from a parting on the right
    lock(g, 36 + p, -82, 52 + p * 0.6, -30, 26, 0.06);
    lock(g, 22 + p, -90, 14 + p, -38, 28, -0.1);
    lock(g, 4 + p, -92, -18 + p, -40, 30, -0.09);
    lock(g, -16 + p, -88, -42 + p, -36, 28, -0.07);
    lock(g, -36 + p * 0.7, -80, -60 + o, -26, 24, -0.05);
    // sideburns
    lock(g, -56 + o + farL * 7, -46, -56 + o + farL * 8, -10, 15, 0.05);
    lock(g, 56 + o - farR * 7, -46, 56 + o - farR * 8, -10, 15, -0.05);
    // tousled top — breaks the silhouette
    lock(g, -22 + o, -94, -50 + o + sw * 6, -112, 26, 0.14);
    lock(g, 22 + o, -98, 46 + o + sw * 6, -112, 24, -0.12);
    lock(g, -42 + o, -82, -72 + o + sw * 4, -86, 24, 0.12);
    lock(g, 44 + o, -84, 70 + o + sw * 4, -78, 22, -0.1);
  }, hairGrad(g, lx));
  // lock separations
  g.strokeStyle = rgba(C.hairLine, 0.75);
  g.lineWidth = 2.2;
  g.beginPath(); g.moveTo(30 + p, -88); g.quadraticCurveTo(22 + p, -62, 18 + p, -44); g.stroke();
  g.beginPath(); g.moveTo(12 + p, -94); g.quadraticCurveTo(0 + p, -66, -10 + p, -46); g.stroke();
  g.beginPath(); g.moveTo(-6 + p, -92); g.quadraticCurveTo(-24 + p, -66, -34 + p, -42); g.stroke();
  g.beginPath(); g.moveTo(-26 + p, -86); g.quadraticCurveTo(-46 + p, -60, -54 + p, -34); g.stroke();
  g.beginPath(); g.moveTo(40 + p, -82); g.quadraticCurveTo(50 + p, -60, 50 + p * 0.6, -40); g.stroke();
  // sheen
  g.strokeStyle = rgba(C.hairLight, 0.6);
  g.lineWidth = 5;
  g.beginPath(); g.moveTo(-46 + o, -82); g.quadraticCurveTo(-26 + o, -100, 8 + o, -100); g.stroke();
  g.lineWidth = 3.4;
  g.beginPath(); g.moveTo(-8 + p, -80); g.quadraticCurveTo(-18 + p, -66, -24 + p, -54); g.stroke();
  g.beginPath(); g.moveTo(14 + p, -84); g.quadraticCurveTo(10 + p, -72, 6 + p, -60); g.stroke();

  // loose strands (secondary motion)
  strand(g, 22 + p, -60, sw * 1.3, [[-10, 12], [-4, 28]], 5);
  strand(g, -2 + o, -106, sw * 0.8 - 0.1, [[4, -14], [14, -22]], 5);
  strand(g, 8 + o, -106, sw * 0.9 + 0.2, [[10, -10], [22, -10]], 3.8);
}

/** tapered hair strand from (x,y), curve through control/tip (relative), rotated by ang */
function strand(g, x, y, ang, [[cx, cy], [tx, ty]], w) {
  g.save();
  g.translate(x, y);
  g.rotate(ang);
  const N = 9;
  const pts = [];
  for (let i = 0; i <= N; i++) {
    const s = i / N;
    const px = 2 * (1 - s) * s * cx + s * s * tx, py = 2 * (1 - s) * s * cy + s * s * ty;
    const dx = 2 * (1 - s) * cx + 2 * s * (tx - cx), dy = 2 * (1 - s) * cy + 2 * s * (ty - cy);
    const l = Math.hypot(dx, dy) || 1;
    pts.push([px, py, -dy / l, dx / l, (w / 2) * (1 - s * 0.92)]);
  }
  g.beginPath();
  pts.forEach(([px, py, nx, ny, hw], i) => (i ? g.lineTo(px + nx * hw, py + ny * hw) : g.moveTo(px + nx * hw, py + ny * hw)));
  for (let i = N; i >= 0; i--) { const [px, py, nx, ny, hw] = pts[i]; g.lineTo(px - nx * hw, py - ny * hw); }
  g.closePath();
  g.fillStyle = C.hair;
  g.strokeStyle = C.hairLine;
  g.lineWidth = 1.8;
  g.stroke();
  g.fill();
  g.restore();
}

function backSkullPath(g) {
  // cranium + nape tapering into the neck (seen from behind there is no chin)
  g.moveTo(0, -90);
  g.bezierCurveTo(-24, -90, -46, -82, -55, -58);
  g.bezierCurveTo(-62, -36, -62, -6, -56, 6);
  g.quadraticCurveTo(-46, 20, 0, 22);
  g.quadraticCurveTo(46, 20, 56, 6);
  g.bezierCurveTo(62, -6, 62, -36, 55, -58);
  g.bezierCurveTo(46, -82, 24, -90, 0, -90);
  g.closePath();
}

function drawHeadBack(g, k, pose, u, sway) {
  const t = k.t, facing = k.facing;
  const yawB = u * 1.25;            // in back view, headTurn turns the face toward that screen side
  const s = u >= 0 ? 1 : -1;
  const lp = sstep(0.12, 0.62, Math.abs(yawB)); // lost-profile amount
  const ears = [-1, 1].map((sd) => ({ sd, ...earPos(sd, Math.PI - yawB) }));
  const face = makeExpr(pose.face || {});
  const blink = face.noAutoBlink ? face.blink : clamp(face.blink + autoBlink(t, 23, 0.26));
  const lx = -24 * facing;
  for (const e of ears) if (e.z < -0.05) drawEar(g, e.x, e.sd, e.w * 0.95, true);

  // skull/nape + lost-profile cheek & jaw on the turned side (merged outline: stroke pass, then fill pass)
  const shapes = (pass) => {
    g.beginPath();
    backSkullPath(g);
    g.rect(-15.5, 10, 31, 66); // top of the neck, merged so no seam shows under the hair
    if (lp > 0.01) {
      // cheek + jaw sweeping toward the (hidden) chin on the turned side
      const o = lp * 10;
      g.moveTo(s * 36, -24);
      g.quadraticCurveTo(s * (56 + o), -14, s * (57 + o), 8);
      g.quadraticCurveTo(s * (57 + o), 28, s * (44 + o), 40);
      g.quadraticCurveTo(s * (30 + o * 0.6), 50, s * 10, 44);
      g.lineTo(s * 10, 0);
      g.closePath();
    }
    pass();
  };
  g.strokeStyle = C.skinLine;
  g.lineWidth = 6;
  shapes(() => g.stroke());
  const gr = g.createRadialGradient(lx + s * lp * 40, 0, 8, 0, 20, 92);
  gr.addColorStop(0, shade(C.skin, 0.02));
  gr.addColorStop(1, C.skinShade);
  g.fillStyle = gr;
  shapes(() => g.fill('nonzero'));

  // lost-profile eyelash + brow peeking past the cheek
  if (lp > 0.3) {
    const a = clamp((lp - 0.3) / 0.4);
    const ex = s * (53 + lp * 10), ey = -4;
    g.strokeStyle = rgba(SELF_FACE.line, a);
    g.lineWidth = 3;
    const lidDrop = clamp(face.lidU + blink, -0.3, 1) * 5;
    g.beginPath(); g.moveTo(ex - s * 4, ey + lidDrop); g.quadraticCurveTo(ex + s * 4, ey - 1 + lidDrop, ex + s * 9, ey - 6 + lidDrop * 1.4); g.stroke();
    const bUp = (face.browUp * 6 + face.browIn * 2) * BROW_GAIN;
    g.fillStyle = rgba(SELF_FACE.browColor, a);
    g.beginPath();
    g.moveTo(ex - s * 8, ey - 15 - bUp);
    g.quadraticCurveTo(ex + s * 2, ey - 21 - bUp, ex + s * 10, ey - 18 - bUp * 0.8);
    g.lineTo(ex + s * 9, ey - 14 - bUp * 0.8);
    g.quadraticCurveTo(ex, ey - 16 - bUp, ex - s * 8, ey - 11 - bUp);
    g.closePath();
    g.fill();
  }

  // back hair: crown cap + short tapered nape locks
  const rec = lp * 12; // hairline lifts on the turned side to reveal the cheek
  const R = (side) => (side === s ? rec : 0);
  hairMass(g, () => {
    g.moveTo(-62 + R(-1), 8 - R(-1) * 1.5);
    g.quadraticCurveTo(-74, -78, -24, -106);
    g.quadraticCurveTo(4, -116, 30, -106);
    g.quadraticCurveTo(76, -78, 62 - R(1), 8 - R(1) * 1.5);
    g.quadraticCurveTo(36, 20, 0, 22);
    g.quadraticCurveTo(-36, 20, -62 + R(-1), 8 - R(-1) * 1.5);
    g.closePath();
    lock(g, -50 + R(-1), -12, -54 + R(-1) * 0.8, 20 - R(-1), 20, -0.08);
    lock(g, -32, 6, -34, 32, 22, -0.06);
    lock(g, -12, 10, -12, 40, 22, -0.02);
    lock(g, 8, 10, 10, 40, 22, 0.03);
    lock(g, 28, 6, 32, 32, 22, 0.06);
    lock(g, 50 - R(1), -12, 54 - R(1) * 0.8, 20 - R(1), 20, 0.08);
    // tousled top (mirror of the front tufts)
    lock(g, 22, -94, 50 + sway * 6, -112, 26, -0.14);
    lock(g, -22, -98, -46 + sway * 6, -112, 24, 0.12);
    lock(g, 42, -82, 72 + sway * 4, -86, 24, -0.12);
    lock(g, -44, -84, -70 + sway * 4, -78, 22, 0.1);
  }, hairGrad(g, lx));
  // whorl + lock lines
  g.strokeStyle = rgba(C.hairLine, 0.65);
  g.lineWidth = 2.2;
  const wx = 6, wy = -76;
  for (const [ex, ey, cx2] of [[-40, 16, -30], [-14, 30, -10], [16, 30, 12], [40, 16, 32], [-58, -24, -46], [58, -24, 50]]) {
    g.beginPath(); g.moveTo(wx + ex * 0.12, wy + 6); g.quadraticCurveTo(cx2, (wy + ey) / 2 - 10, ex, ey); g.stroke();
  }
  g.beginPath(); g.arc(wx, wy - 2, 7, 0.3, 4.4); g.stroke();
  g.strokeStyle = rgba(C.hairLight, 0.55);
  g.lineWidth = 5;
  g.beginPath(); g.moveTo(-50, -66); g.quadraticCurveTo(-34, -96, 0, -100); g.stroke();
  g.lineWidth = 3.4;
  g.beginPath(); g.moveTo(-34, -40); g.quadraticCurveTo(-40, -20, -40, 0); g.stroke();

  for (const e of ears) if (e.z >= -0.05) drawEar(g, e.x, e.sd, e.w * 0.95, true);

  strand(g, -2, -106, sway * 0.8 - 0.1, [[4, -14], [14, -22]], 5);
  strand(g, 10, -104, sway * 0.9 + 0.2, [[10, -10], [22, -8]], 3.8);
  strand(g, -2, 36, -sway * 0.6, [[-2, 6], [2, 12]], 3.4);
}

// ---------------------------------------------------------------- nose (face style hook)
function drawNose(g, e, shiftX) {
  const nx = shiftX * 1.3, ny = 20;
  const gr = g.createRadialGradient(nx + 3, ny + 3, 0, nx + 3, ny + 3, 10);
  gr.addColorStop(0, 'rgba(160,82,60,0.26)');
  gr.addColorStop(1, 'rgba(160,82,60,0)');
  g.fillStyle = gr;
  g.fillRect(nx - 8, ny - 8, 22, 22);
  g.strokeStyle = 'rgba(112,58,44,0.85)';
  g.lineWidth = 2.2;
  g.lineCap = 'round';
  g.beginPath();
  g.moveTo(nx - 5.5, ny + 3);
  g.quadraticCurveTo(nx - 1, ny + 7.5, nx + 4.5, ny + 3.5);
  g.quadraticCurveTo(nx + 7, ny + 1, nx + 4, ny - 4);
  g.stroke();
  g.fillStyle = 'rgba(255,236,220,0.35)';
  ellipse(g, nx - 1.5, ny - 1, 2.6, 1.8);
  g.fill();
}

// ---------------------------------------------------------------- arms
function armGeom(a, side, k) {
  const s = k.sh[side];
  let [tx, ty] = a.target;
  const shake = Math.max(k.trem, a.shake || 0);
  if (shake > 0) { tx += shake * noise1(k.t * 31 + side * 7, 12) * 2.5; ty += shake * noise1(k.t * 27 + side * 5, 13) * 2.5; }
  const L1 = UPPER * (a.reach1 || 1), L2 = FORE * (a.reach2 || 1);
  if (a.palm) {
    // target is where the palm should land: pull the wrist back along the approach direction
    const d = Math.hypot(tx - s.x, ty - s.y) || 1;
    tx -= ((tx - s.x) / d) * 17 * HAND_S;
    ty -= ((ty - s.y) / d) * 17 * HAND_S;
  }
  const { a1, a2 } = ik(s.x, s.y, tx, ty, L1, L2, a.bend ?? side);
  const ex = s.x + Math.cos(a1) * L1, ey = s.y + Math.sin(a1) * L1;
  const wx = ex + Math.cos(a1 + a2) * L2, wy = ey + Math.sin(a1 + a2) * L2;
  const fa = a1 + a2;
  const handAng = a.handAngle != null ? a.handAngle : fa + (a.wrist || 0);
  return { a, side, sx: s.x, sy: s.y, ex, ey, wx, wy, a1, a2, fa, handAng };
}

function drawArmGroup(g, geos, ctx, merge) {
  if (!geos.length) return;
  const { k, pose, outfit } = ctx;
  // props first (hands grip over them)
  const nb = geos.filter((q) => q.a.prop === 'notebook' || q.a.prop === 'notebookCover');
  const cover = nb.length && nb[0].a.prop === 'notebookCover';
  if (nb.length) {
    const cx = nb.reduce((s, q) => s + q.wx, 0) / nb.length + (nb.length === 1 ? -nb[0].side * 40 : 0);
    const cy = nb.reduce((s, q) => s + q.wy, 0) / nb.length + (cover ? -24 : -12);
    const tilt = (pose.notebook && pose.notebook.tilt) || 0;
    const sc = cover ? 0.95 : 0.82;
    // closed book shown to camera: the hands hold it from behind, only the thumbs wrap the front edges
    if (cover) for (const q of nb) drawHand(g, q);
    g.save();
    g.translate(cx, cy);
    g.rotate(tilt);
    g.scale(k.facing, 1); // keep the cover art readable
    drawSelfNotebook(g, 0, 0, sc, { mode: cover ? 'closed' : 'heldOpen', t: k.t });
    g.restore();
    if (cover) {
      for (const q of nb) {
        const ex = cx + q.side * 35 * sc * Math.cos(tilt), ey = q.wy - 12;
        g.save();
        g.translate(ex, ey);
        g.rotate(q.side * 0.25 + tilt);
        g.fillStyle = C.skin;
        g.strokeStyle = C.skinLine;
        g.lineWidth = 2.6;
        g.beginPath();
        g.roundRect(-q.side * 9 - 5, -13, 10, 22, 5);
        g.fill(); g.stroke();
        g.restore();
      }
    }
  }
  for (const q of geos) if (q.a.prop === 'clipboard') drawClipboardAt(g, q, k);
  for (const q of geos) if (!(cover && nb.includes(q))) drawHand(g, q);
  for (const q of geos) drawSleeve(g, q, ctx, merge && !ctx.back);
}

function strokeOutsideShoulder(g, q, ctx, r, strokeFn) {
  // region 1: outside a circle around the shoulder joint
  g.save();
  g.beginPath();
  g.rect(-3000, -3000, 6000, 6000);
  g.moveTo(q.sx + r, q.sy);
  g.arc(q.sx, q.sy, r, 0, TAU);
  g.clip('evenodd');
  strokeFn();
  g.restore();
  // region 2: outside the torso silhouette
  g.save();
  g.beginPath();
  g.rect(-3000, -3000, 6000, 6000);
  emit(g, ctx.sil, ctx.k.tp);
  g.clip('evenodd');
  strokeFn();
  g.restore();
  if (ctx.k.seated) {
    // region 3: below the desk line (torso not drawn there)
    g.save();
    g.beginPath();
    g.rect(-3000, 0, 6000, 3000);
    g.clip();
    strokeFn();
    g.restore();
  }
}

function drawSleeve(g, q, ctx, merge) {
  const { sx, sy, ex, ey, wx, wy } = q;
  const k = ctx.k;
  const ceo = ctx.outfit === 'ceo';
  const light = ceo ? C.blazerLight : C.sweaterLight, line = ceo ? C.blazerLine : C.sweaterLine;
  const W1 = ceo ? 33 : 32, W2 = ceo ? 29 : 29;
  const fl = Math.hypot(wx - ex, wy - ey) || 1;
  const ux = (wx - ex) / fl, uy = (wy - ey) / fl;
  // sleeve end: the sweater cuff covers the wrist ("sweater paw"); the blazer stops short to show the teal cuff
  const endBack = ceo ? 21 : 2;
  const fx = wx - ux * endBack, fy = wy - uy * endBack;
  if (ceo) cuff(g, wx - ux * 16, wy - uy * 16, wx + ux * 5, wy + uy * 5, 27, C.sweater, C.sweaterLine, true);
  const outline = () => {
    g.strokeStyle = line;
    g.lineWidth = W1 + 5.5;
    g.beginPath(); g.moveTo(sx, sy); g.lineTo(ex, ey); g.stroke();
    g.lineWidth = W2 + 5.5;
    g.beginPath(); g.moveTo(ex, ey); g.lineTo(fx, fy); g.stroke();
  };
  g.lineCap = 'round';
  if (merge) strokeOutsideShoulder(g, q, ctx, W1 / 2 + 5, outline);
  else outline();
  // fill with the same lighting as the torso so the shoulder seam disappears
  const toLocalTorso = k.tp;
  g.strokeStyle = clothGrad(g, k, ctx.outfit, toLocalTorso);
  g.lineWidth = W2;
  g.beginPath(); g.moveTo(ex, ey); g.lineTo(fx, fy); g.stroke();
  g.lineWidth = W1;
  g.beginPath(); g.moveTo(sx, sy); g.lineTo(ex, ey); g.stroke();
  // light along the upper-left edge (starts below the shoulder)
  const hl = (x0, y0, x1, y1, w) => {
    const l = Math.hypot(x1 - x0, y1 - y0) || 1;
    let nx = -(y1 - y0) / l, ny = (x1 - x0) / l;
    if (nx * k.facing + ny > 0) { nx = -nx; ny = -ny; }
    g.beginPath();
    g.moveTo(x0 + nx * w * 0.27, y0 + ny * w * 0.27);
    g.lineTo(x1 + nx * w * 0.27, y1 + ny * w * 0.27);
    g.stroke();
  };
  g.strokeStyle = rgba(light, 0.45);
  g.lineWidth = 6;
  hl(lerp(sx, ex, 0.35), lerp(sy, ey, 0.35), ex, ey, W1);
  hl(ex, ey, fx - ux * 8, fy - uy * 8, W2);
  // elbow crease
  if (Math.abs(q.a2) > 0.45) {
    g.strokeStyle = rgba(line, 0.5);
    g.lineWidth = 2.2;
    const inner = q.a1 + q.a2 / 2 + Math.PI / 2 * Math.sign(q.a2);
    const cxp = ex + Math.cos(inner) * 6, cyp = ey + Math.sin(inner) * 6;
    g.beginPath();
    g.arc(cxp, cyp, 9, inner + Math.PI - 0.7, inner + Math.PI + 0.7);
    g.stroke();
  }
  if (!ceo) cuff(g, wx - ux * 12, wy - uy * 12, wx + ux * 3, wy + uy * 3, 32, C.sweaterShade, C.sweaterLine, true);
  else {
    // blazer sleeve hem
    g.strokeStyle = rgba(line, 0.9);
    g.lineWidth = 2.4;
    const nx = -uy, ny = ux;
    g.beginPath(); g.moveTo(fx + ux * 2 + nx * 14, fy + uy * 2 + ny * 14); g.lineTo(fx + ux * 2 - nx * 14, fy + uy * 2 - ny * 14); g.stroke();
  }
}

function cuff(g, x0, y0, x1, y1, w, col, line, ribs) {
  const l = Math.hypot(x1 - x0, y1 - y0) || 1;
  const ux = (x1 - x0) / l, uy = (y1 - y0) / l, nx = -uy, ny = ux;
  const hw = w / 2;
  g.beginPath();
  g.moveTo(x0 + nx * hw, y0 + ny * hw);
  g.lineTo(x1 + nx * (hw - 1.5), y1 + ny * (hw - 1.5));
  g.quadraticCurveTo(x1 + ux * 3, y1 + uy * 3, x1 - nx * (hw - 1.5), y1 - ny * (hw - 1.5));
  g.lineTo(x0 - nx * hw, y0 - ny * hw);
  g.closePath();
  g.fillStyle = col;
  g.fill();
  g.strokeStyle = line;
  g.lineWidth = 2.4;
  g.stroke();
  if (ribs) {
    g.strokeStyle = rgba(line, 0.3);
    g.lineWidth = 1.5;
    for (let i = -2; i <= 2; i++) {
      const o = i * hw * 0.36;
      g.beginPath();
      g.moveTo(x0 + nx * o + ux * 2, y0 + ny * o + uy * 2);
      g.lineTo(x1 + nx * o - ux * 2, y1 + ny * o - uy * 2);
      g.stroke();
    }
  }
}

// hand shapes: fingers [baseY, len, curl], spread (rad across the fan), thumb [angle, len]
const HANDS = {
  open: { f: [[5.2, 14, 0.4], [1.7, 15.5, 0.32], [-1.8, 14.5, 0.36], [-5.2, 12, 0.45]], spread: 0.08, thumb: [0.85, 12.5] },
  rest: { f: [[5.2, 15, 0.6], [1.7, 16, 0.55], [-1.8, 15, 0.6], [-5.2, 12.5, 0.65]], spread: 0.05, thumb: [0.6, 12.5] },
  drape: { f: [[5, 16, 0.22], [1.7, 17.5, 0.18], [-1.7, 16.5, 0.2], [-5, 13.5, 0.26]], spread: 0.05, thumb: [0.45, 12.5] },
  palm: { f: [[5.4, 15, 0.02], [1.8, 17, 0], [-1.9, 16, 0], [-5.4, 13, 0.05]], spread: 0.24, thumb: [1.15, 13] },
  flat: { f: [[5, 15.5, 0.05], [1.7, 17, 0.04], [-1.7, 16, 0.05], [-5, 13, 0.08]], spread: 0.04, thumb: [0.55, 12.5] },
  cup: { f: [[5, 15, 0.25], [1.7, 16.5, 0.2], [-1.7, 15.5, 0.22], [-5, 13, 0.3]], spread: 0.06, thumb: [1.35, 13.5] },
  point: { f: [[5, 19, 0], [1.7, 9, 1], [-1.7, 8.5, 1], [-5, 7.5, 1]], spread: 0.02, thumb: [0.55, 10] },
  fist: { f: [[5, 9, 1], [1.7, 9.5, 1], [-1.7, 9, 1], [-5, 8, 1]], spread: 0, thumb: [0.35, 10.5], fist: true },
  grip: { f: [[5, 10, 0.9], [1.7, 10.5, 0.9], [-1.7, 10, 0.9], [-5, 9, 0.9]], spread: 0, thumb: [0.12, 13], fist: true },
};

function drawHand(g, q) {
  const a = q.a;
  const H = HANDS[a.hand] || HANDS.open;
  const th = a.thumb ?? q.side; // thumb on +y (th=1) or -y (th=-1) of the hand frame
  g.save();
  g.translate(q.wx, q.wy);
  g.rotate(q.handAng);
  g.scale(HAND_S, HAND_S * th);
  const OL = 1.9, FW = 6.6;
  const fingers = H.f.map(([by, len, curl]) => {
    const ang = (by / 5.4) * H.spread;
    const l = len * (1 - 0.42 * curl);
    const x0 = 15, y0 = by * 1.05;
    const mx = x0 + Math.cos(ang) * l * 0.55, my = y0 + Math.sin(ang) * l * 0.55;
    const a2 = ang - curl * 1.1;
    return [x0, y0, mx, my, mx + Math.cos(a2) * l * 0.45, my + Math.sin(a2) * l * 0.45];
  });
  const palm = () => {
    g.beginPath();
    g.moveTo(-1, -8);
    g.bezierCurveTo(6, -11, 14, -11, 18, -8.5);
    g.bezierCurveTo(H.fist ? 26 : 22, -3.5, H.fist ? 26 : 22, 3.5, 18, 8.5);
    g.bezierCurveTo(13, 11.5, 6, 11, -1, 8.5);
    g.closePath();
  };
  const fingerPaths = () => {
    g.beginPath();
    for (const [x0, y0, mx, my, tx, ty] of fingers) { g.moveTo(x0, y0); g.lineTo(mx, my); g.lineTo(tx, ty); }
  };
  // pass 1: outlines
  g.strokeStyle = C.skinLine;
  g.lineCap = 'round';
  g.lineJoin = 'round';
  g.lineWidth = FW + OL * 2;
  fingerPaths(); g.stroke();
  g.lineWidth = OL * 2;
  palm(); g.stroke();
  // pass 2: fills
  const gr = g.createLinearGradient(0, -10, 0, 10);
  gr.addColorStop(0, C.skinLight);
  gr.addColorStop(1, C.skin);
  g.fillStyle = gr;
  palm(); g.fill();
  g.strokeStyle = C.skin;
  g.lineWidth = FW;
  fingerPaths(); g.stroke();
  // finger separations
  g.strokeStyle = rgba(C.skinLine, 0.5);
  g.lineWidth = 1.3;
  for (let i = 0; i < fingers.length - 1; i++) {
    const f0 = fingers[i], f1 = fingers[i + 1];
    const mx = (f0[2] + f1[2]) / 2, my = (f0[3] + f1[3]) / 2;
    g.beginPath(); g.moveTo((f0[0] + f1[0]) / 2 + 3, (f0[1] + f1[1]) / 2); g.lineTo(mx, my); g.stroke();
  }
  // thumb (in front)
  const [ta, tl] = H.thumb;
  const t0x = 7, t0y = 6.5, t1x = t0x + Math.cos(ta) * tl, t1y = t0y + Math.sin(ta) * tl;
  g.strokeStyle = C.skinLine;
  g.lineWidth = 7.4 + OL * 2;
  g.beginPath(); g.moveTo(t0x, t0y); g.lineTo(t1x, t1y); g.stroke();
  g.strokeStyle = C.skin;
  g.lineWidth = 7.4;
  g.beginPath(); g.moveTo(t0x - 1.5, t0y - 2); g.lineTo(t1x, t1y); g.stroke();
  g.restore();
}

// ---------------------------------------------------------------- props
function drawClipboardAt(g, q, k) {
  const [dx, dy, rot] = q.a.board || [-q.side * 6, 40, q.side * 0.08];
  g.save();
  g.translate(q.wx + dx, q.wy + dy);
  g.rotate(rot);
  g.scale(k.facing, 1);
  drawClipboard(g);
  g.restore();
}

/** Clipboard prop, centred at (0,0), 62x84 at scale 1. */
export function drawClipboard(g) {
  const w = 62, h = 84;
  g.fillStyle = '#a8764e';
  g.strokeStyle = '#4a2c1c';
  g.lineWidth = 2.6;
  g.beginPath(); g.roundRect(-w / 2, -h / 2, w, h, 5); g.fill(); g.stroke();
  g.fillStyle = '#f7f0e2';
  g.strokeStyle = 'rgba(80,60,40,0.45)';
  g.lineWidth = 1.4;
  g.beginPath(); g.roundRect(-w / 2 + 5, -h / 2 + 9, w - 10, h - 14, 2); g.fill(); g.stroke();
  g.strokeStyle = 'rgba(70,90,130,0.55)';
  g.lineWidth = 1.6;
  for (let i = 0; i < 6; i++) {
    const yy = -h / 2 + 24 + i * 9;
    g.strokeRect(-w / 2 + 10, yy - 3.5, 5, 5);
    g.beginPath(); g.moveTo(-w / 2 + 19, yy - 1); g.lineTo(w / 2 - 10 - (i % 3) * 6, yy - 1); g.stroke();
  }
  // a couple of ticks
  g.strokeStyle = 'rgba(200,70,70,0.85)';
  g.lineWidth = 1.8;
  for (const i of [0, 1, 3]) {
    const yy = -h / 2 + 24 + i * 9;
    g.beginPath(); g.moveTo(-w / 2 + 10, yy - 1.5); g.lineTo(-w / 2 + 12.5, yy + 1); g.lineTo(-w / 2 + 17, yy - 5); g.stroke();
  }
  // clip
  g.fillStyle = '#c9ccd6';
  g.strokeStyle = '#4b4e5c';
  g.lineWidth = 2;
  g.beginPath(); g.roundRect(-14, -h / 2 - 4, 28, 13, 3); g.fill(); g.stroke();
  g.fillStyle = 'rgba(255,255,255,0.6)';
  g.fillRect(-11, -h / 2 - 2, 22, 2.5);
}

/**
 * The old notebook ("my first story") — childlike crayon cover: a tiny lavender bean with huge eyes beside a
 * tall dark hooded figure dotted with gold star stickers.
 *   mode 'closed'   : front cover facing camera, 70x92 at scale 1, centred at (x,y)
 *   mode 'heldOpen' : open, held up facing its reader — the viewer sees both outer covers (140x92)
 *   mode 'pages'    : lying open, pages up (pencil handwriting + doodle), 150x96
 */
export function drawSelfNotebook(g, x, y, scale = 1, opts = {}) {
  const mode = opts.mode || 'closed';
  g.save();
  g.translate(x, y);
  g.scale(scale, scale);
  if (opts.angle) g.rotate(opts.angle);
  const cover = '#f2d488', coverShade = '#d9b464', line = '#6a4a2a';
  g.lineJoin = 'round';
  g.lineCap = 'round';
  if (mode === 'pages') {
    for (const s of [-1, 1]) {
      g.fillStyle = '#f6eedb';
      g.strokeStyle = '#7d6446';
      g.lineWidth = 2;
      g.beginPath();
      g.moveTo(0, -46);
      g.quadraticCurveTo(s * 36, -52, s * 74, -46);
      g.lineTo(s * 74, 46);
      g.quadraticCurveTo(s * 36, 40, 0, 46);
      g.closePath();
      g.fill(); g.stroke();
    }
    const gs = g.createLinearGradient(-14, 0, 14, 0);
    gs.addColorStop(0, 'rgba(120,90,50,0)'); gs.addColorStop(0.5, 'rgba(120,90,50,0.3)'); gs.addColorStop(1, 'rgba(120,90,50,0)');
    g.fillStyle = gs; g.fillRect(-14, -46, 28, 92);
    g.strokeStyle = 'rgba(70,70,90,0.6)';
    g.lineWidth = 1.6;
    for (let i = 0; i < 7; i++) {
      const yy = -32 + i * 10;
      g.beginPath();
      g.moveTo(-66, yy);
      for (let xx = -66; xx < -10 - (i % 3) * 8; xx += 4) g.lineTo(xx, yy + Math.sin(xx * 0.9 + i) * 1.6);
      g.stroke();
    }
    drawCoverArt(g, 42, 4, 0.62, opts.t || 0, true);
    g.restore();
    return;
  }
  const panel = (cx, art) => {
    const w = 70, h = 92;
    g.fillStyle = cover;
    g.strokeStyle = line;
    g.lineWidth = 2.6;
    g.beginPath(); g.roundRect(cx - w / 2, -h / 2, w, h, 4); g.fill(); g.stroke();
    // worn corners
    g.fillStyle = rgba(coverShade, 0.8);
    for (const [px, py] of [[cx - w / 2 + 5, -h / 2 + 5], [cx + w / 2 - 5, h / 2 - 5]]) { circle(g, px, py, 5); g.fill(); }
    if (art) drawCoverArt(g, cx, 4, 1, opts.t || 0, false);
    else {
      g.fillStyle = '#ffd34d';
      g.strokeStyle = '#b8862a';
      g.lineWidth = 1.2;
      star5(g, cx + 14, -26, 6); g.fill(); g.stroke();
    }
  };
  if (mode === 'heldOpen') {
    // page edges peeking over the top
    g.fillStyle = '#fbf5e6';
    g.strokeStyle = '#8a7356';
    g.lineWidth = 1.6;
    g.beginPath(); g.roundRect(-68, -50, 136, 10, 3); g.fill(); g.stroke();
    panel(-36, false);
    panel(36, true);
    g.fillStyle = '#c99d4e';
    g.strokeStyle = line;
    g.lineWidth = 2.2;
    g.beginPath(); g.roundRect(-4, -47, 8, 94, 3); g.fill(); g.stroke();
  } else {
    // closed: spine strip on the left
    panel(0, true);
    g.fillStyle = '#c99d4e';
    g.strokeStyle = line;
    g.lineWidth = 2.2;
    g.beginPath(); g.roundRect(-37, -46, 9, 92, 3); g.fill(); g.stroke();
  }
  g.restore();
}

function star5(g, x, y, r) {
  g.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = (i / 10) * TAU - Math.PI / 2;
    const rr = i % 2 ? r * 0.45 : r;
    const px = x + Math.cos(a) * rr, py = y + Math.sin(a) * rr;
    if (i) g.lineTo(px, py); else g.moveTo(px, py);
  }
  g.closePath();
}

function drawCoverArt(g, cx, cy, s, t, pencil) {
  g.save();
  g.translate(cx, cy);
  g.scale(s, s);
  // crayon title (handwriting font if the renderer registered one; plain fallback otherwise)
  g.fillStyle = pencil ? 'rgba(70,70,90,0.75)' : '#d0584a';
  g.font = 'bold 15px Caveat, "Patrick Hand", sans-serif';
  g.textAlign = 'center';
  g.textBaseline = 'alphabetic';
  g.save();
  g.rotate(-0.06);
  g.fillText('My Story', 0, -31);
  g.restore();
  g.textAlign = 'start';
  // tall dark hooded figure
  g.fillStyle = pencil ? 'rgba(60,60,80,0.35)' : '#2b2a4a';
  g.strokeStyle = pencil ? 'rgba(60,60,80,0.8)' : '#16152a';
  g.lineWidth = 2;
  g.beginPath();
  g.moveTo(6, 40);
  g.quadraticCurveTo(4, -6, 12, -18);
  g.quadraticCurveTo(18, -27, 24, -18);
  g.quadraticCurveTo(32, -6, 30, 40);
  g.closePath();
  g.fill(); g.stroke();
  g.fillStyle = pencil ? 'rgba(30,30,40,0.6)' : '#0c0b18';
  ellipse(g, 18, -12, 4.5, 5.5);
  g.fill();
  if (!pencil) {
    for (const [sx, sy, r] of [[12, 4, 3.2], [22, 14, 2.6], [15, 26, 3], [25, 0, 2.2]]) {
      const tw = 0.85 + 0.15 * Math.sin(t * 2 + sx);
      g.fillStyle = '#ffd34d';
      g.strokeStyle = '#b8862a';
      g.lineWidth = 0.9;
      star5(g, sx, sy, r * tw); g.fill(); g.stroke();
    }
  }
  // tiny lavender bean with huge eyes
  g.fillStyle = pencil ? 'rgba(150,130,200,0.35)' : '#b9a6ea';
  g.strokeStyle = pencil ? 'rgba(60,60,80,0.8)' : '#5a4890';
  g.lineWidth = 2;
  g.beginPath();
  g.ellipse(-14, 28, 9, 12, 0, 0, TAU);
  g.fill(); g.stroke();
  g.fillStyle = '#ffffff';
  for (const ex of [-17.5, -10.5]) { circle(g, ex, 25, 3.4); g.fill(); g.stroke(); }
  g.fillStyle = '#2a1f4a';
  for (const ex of [-17, -10]) { circle(g, ex, 25.6, 1.5); g.fill(); }
  g.strokeStyle = pencil ? 'rgba(60,60,80,0.8)' : '#5a4890';
  g.beginPath(); g.moveTo(-14, 16); g.quadraticCurveTo(-16, 11, -12, 10); g.stroke();
  // crayon sun in the corner
  if (!pencil) {
    g.strokeStyle = '#f08a3c';
    g.fillStyle = '#ffb347';
    circle(g, -22, -16, 5); g.fill(); g.stroke();
    g.lineWidth = 1.6;
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * TAU;
      g.beginPath(); g.moveTo(-22 + Math.cos(a) * 7.5, -16 + Math.sin(a) * 7.5); g.lineTo(-22 + Math.cos(a) * 10.5, -16 + Math.sin(a) * 10.5); g.stroke();
    }
  }
  g.restore();
}
