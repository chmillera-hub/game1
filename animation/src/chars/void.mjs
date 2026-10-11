// THE VOID — an enormous hooded, cloaked presence of deep blue-black with a violet/cyan rim light.
// Its face is a hood opening of PURE DARKNESS (no eyes, ever) that can fill with the cosmos.
//
//   drawVoid(g, x, y, scale, pose)
//     x, y   : world position of the hem centre on the floor
//     scale  : 1 = ~1700 px tall (use ~0.45-0.6 in wide shots)
//   drawVoidShadow(g, x, y, scale, pose)   floor shadow only (drawVoid draws it too unless pose.shadow === false)
//   drawVoidArm(g, x, y, scale, pose, 'R'|'L')  one arm on its own (for a hand IN FRONT of another character)
//   drawVoidGlow(g, x, y, scale, pose)     soft light spill from the hood when pose.cosmos > 0 (screen blend)
//   voidRig(pose)                          live local anchors (face centre/radii, shoulders, hands) for staging
//
// POSE (all optional)
//   t            seconds — idle life: barely perceptible hem drift + rim shimmer
//   headTurn     -1..1   hood yaw. + = looks toward screen-right (+x), - = screen-left. 0 = facing camera/distance
//   headDown     0..1    hood bows to look at someone small at its feet (shoulders hunch slightly)
//   headTilt     radians extra hood roll
//   lean         radians whole-body lean, pivot at the hem centre on the floor
//   cosmos       0..1    0 = pure darkness; ~0.3 a few stars kindle; 1 = the full universe
//   cosmosOpts   { glyphs, seed, drift } passed through to drawCosmos
//   rim          0..1    rim-light strength (default 1)
//   silhouette   bool    cloak nearly invisible: only rim light + face read
//   alpha        0..1    overall opacity (composited through an offscreen layer, so overlaps don't show)
//   shadow       false to skip the floor shadow (draw it yourself earlier with drawVoidShadow)
//   shadowSpread 0..1    0 = contact shadow under the hem; 1 = dark shadow spilling across the room floor
//   handR, handL { show 0..1  hand emerges from inside the sleeve (0 = hidden)
//                  target [x,y] local coords (origin = hem centre on floor, y negative up). Where the PALM
//                         centre goes (or the middle fingertip if tip:true). Omit = arm hangs at rest.
//                  reach 0..1 (default 1) blend the arm from its rest position toward target
//                  open 0..1 relaxed → fingers spread;  gentle 0..1 palm softly curved (resting on a shoulder)
//                  angle radians: hand direction override (0 = fingers point +x, PI/2 = down)
//                  curl +1/-1 which side the fingers curl toward (default: the downward side)
//                  bend +1/-1 elbow side (default: outward); elbow 0..1 how bent (default 0.3 when reaching, 0 at rest)
//                  front false = draw this arm behind the body
//                  defer true = drawVoid skips this arm; draw it later with drawVoidArm() }
//   (handR = screen-right hand (+x side), handL = screen-left, same convention as Fear's armR/armL.)

import { createCanvas } from '@napi-rs/canvas';
import { clamp, lerp, TAU, ik, rgba, mixColor } from '../engine.mjs';
import { drawCosmos, vfbm } from '../fx/cosmos.mjs';

export const HEIGHT = 1700;

export const VOID_COLORS = {
  body: '#0a0914', bodyLight: '#17142f', bodyDeep: '#04030a', hood: '#0f0d21', hoodLight: '#1c1939',
  abyss: '#010004', abyssEdge: '#0a0917', rim: '#8a6cff', rimSoft: '#b9a8ff', rimCyan: '#5ad1ff',
  hand: '#14112a', handLight: '#25204a', shadow: '#030209',
};
const C = VOID_COLORS;

// ---- geometry (scale 1, origin = hem centre on the floor, y negative = up)
const NECK_Y = -1400;              // hood pivot
const FACE_DY = -108;              // face centre relative to the hood pivot
const FACE_RX = 80, FACE_RY = 112; // face opening half-size (facing camera)
const SH_X = 222, SH_Y = -1292;    // shoulder joints
const L1 = 450, L2 = 450;          // arm bones (sleeves stretch up to 30% beyond to make contact)
const REST = [262, -560];          // rest wrist (inside the sleeve), x mirrored per side
const PALM_C = 52, HAND_LEN = 196; // wrist → palm centre / middle fingertip

export const ANCHORS = {
  hoodTop: [0, -1715],
  face: [0, NECK_Y + FACE_DY], faceRx: FACE_RX, faceRy: FACE_RY,
  shoulderL: [-SH_X, SH_Y], shoulderR: [SH_X, SH_Y],
  chest: [0, -1180], waist: [0, -760],
  handRestL: [-REST[0], REST[1]], handRestR: [REST[0], REST[1]],
  hemL: [-450, 0], hemR: [450, 0], hemFront: [0, 32],
  width: 900,                // widest (hem pool / sleeve cuffs) at scale 1
  reach: Math.round((L1 + L2) * 1.3 + PALM_C), // max shoulder → palm distance
  handLength: HAND_LEN,
};

/** Hand presets: functions of a local target [x,y]. Spread/override fields as needed. */
export const VOID_HANDS = {
  hidden: () => ({ show: 0 }),
  out: () => ({ show: 1 }),
  // side: +1 when the touched character stands to the Void's screen-right (fingers drape down-right), -1 left
  shoulder: (target, side = 1) => ({ show: 1, target, tip: true, open: 0.12, gentle: 0.9, angle: side > 0 ? 0.5 : Math.PI - 0.5 }),
  unlock: (target) => ({ show: 1, target, open: 0.08, gentle: 0.35, tip: true }),
  // side: +1 pushes toward screen-right (hand sits on the pushed character's left/back), -1 toward screen-left
  push: (target, side = 1) => ({ show: 1, target, open: 0.32, gentle: 0.3, angle: side > 0 ? 0.8 : Math.PI - 0.8 }),
  offer: (target) => ({ show: 1, target, open: 0.75, gentle: 0.45 }),
};

/** Head presets (spread into pose). */
export const VOID_POSES = {
  still: { headTurn: 0, headDown: 0 },
  distance: { headTurn: -0.12, headDown: 0.02 },                 // staring off into the distance
  turnRight: { headTurn: 0.75, headDown: 0.1 },
  turnLeft: { headTurn: -0.75, headDown: 0.1 },
  lookDownRight: { headTurn: 0.5, headDown: 0.85 },              // looking at someone small at its feet (screen-right)
  lookDownLeft: { headTurn: -0.5, headDown: 0.85 },
};

// ------------------------------------------------------------------ helpers
const dir = (a) => [Math.cos(a), Math.sin(a)];
const rot = (p, a) => { const c = Math.cos(a), s = Math.sin(a); return [p[0] * c - p[1] * s, p[0] * s + p[1] * c]; };
const add = (a, b, k = 1) => [a[0] + b[0] * k, a[1] + b[1] * k];
const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
function lerpAngle(a, b, k) {
  const d = ((b - a + Math.PI) % TAU + TAU) % TAU - Math.PI;
  return a + d * k;
}
function devScale(g) {
  const m = g.getTransform();
  return Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)) || 1;
}

// ------------------------------------------------------------------ rig
/** Live local anchors for a pose (scale 1, origin hem centre, y up negative). */
export function voidRig(pose = {}) {
  const turn = clamp(pose.headTurn ?? 0, -1, 1);
  const down = clamp(pose.headDown ?? 0);
  const lean = pose.lean || 0;
  const hunch = down * 36;
  const pivot = [0, NECK_Y + hunch];
  const hoodDy = down * 40;
  const hoodRot = (pose.headTilt || 0) + turn * down * 0.12;
  const H = hoodGeom(turn, down);
  const fl = rot([H.ox, H.oy], hoodRot);
  const face = rot([pivot[0] + fl[0], pivot[1] + hoodDy + fl[1]], lean);
  const shoulderR = rot([SH_X, SH_Y + hunch], lean), shoulderL = rot([-SH_X, SH_Y + hunch], lean);
  const r = { turn, down, lean, hunch, pivot, hoodDy, hoodRot, H, face, faceRx: H.rw, faceRy: H.rh, shoulderL, shoulderR };
  r.armR = armRig(1, pose.handR || {}, r);
  r.armL = armRig(-1, pose.handL || {}, r);
  const hand = (A) => {
    const lt = handLocal(A.hp, A.side, A.ha, true), o = rot([lt[0], lt[1] * A.side], A.ha);
    return { wrist: A.W, palm: add(A.W, dir(A.ha), PALM_C), tip: [A.W[0] + o[0], A.W[1] + o[1]], angle: A.ha };
  };
  r.handR = hand(r.armR);
  r.handL = hand(r.armL);
  return r;
}

function armRig(side, hp, r) {
  const S = side > 0 ? r.shoulderR : r.shoulderL;
  const rest = rot([side * REST[0], REST[1] + r.hunch * 0.6], r.lean);
  const restA = Math.PI / 2 - side * 0.05;
  const show = clamp(hp.show ?? 0);
  let ha, W;
  if (hp.target) {
    const reach = clamp(hp.reach ?? 1);
    const a0 = Math.atan2(hp.target[1] - S[1], hp.target[0] - S[0]);
    const haT = hp.angle ?? lerpAngle(a0, Math.PI / 2, 0.3);
    const lp = handLocal(hp, side, haT, !!hp.tip);       // contact point in hand-local coords
    const off = rot([lp[0], lp[1] * side], haT);
    const Wt = [hp.target[0] - off[0], hp.target[1] - off[1]];
    ha = lerpAngle(restA, haT, reach);
    W = [lerp(rest[0], Wt[0], reach), lerp(rest[1], Wt[1], reach)];
  } else {
    ha = hp.angle ?? restA;
    W = rest;
  }
  // "soft" IK: cloth sleeves hide the bones, so they telescope — the elbow only ever bends gently,
  // and they stretch (up to 30%) when the target is farther than the arm.
  const d = Math.hypot(W[0] - S[0], W[1] - S[1]);
  const Ls = L1 + L2;
  // elbow softness: nearly straight at rest, a gentle organic bend while reaching (hp.elbow 0..1 overrides)
  const elbow = clamp(hp.elbow ?? (hp.target ? 0.3 * clamp(hp.reach ?? 1) : 0));
  const ratio = lerp(0.992, 0.88, elbow);
  let l = Math.max(L1 * 0.62, Math.min(L1, d / (2 * ratio)));
  if (d > Ls * ratio) l = L1 * Math.min(1.3, d / (Ls * ratio));
  const bend = hp.bend ?? side;
  const { a1, a2 } = ik(S[0], S[1], W[0], W[1], l, l, bend);
  const E = add(S, dir(a1), l);
  const fa = a1 + a2;
  const Wr = add(E, dir(fa), l);
  return { side, S, E, W: Wr, a1, fa, ha, show, hp, l };
}

// ------------------------------------------------------------------ shadow
export function drawVoidShadow(g, x, y, scale = 1, pose = {}) {
  const t = pose.t || 0;
  const spread = clamp(pose.shadowSpread ?? 0.3);
  g.save();
  if (pose.alpha != null) g.globalAlpha *= clamp(pose.alpha);
  g.translate(x, y);
  g.scale(scale, scale);
  const blob = (cx, cy, rx, ry, a, rotA = 0) => {
    g.save();
    g.translate(cx, cy);
    g.rotate(rotA);
    g.scale(1, ry / rx);
    const gr = g.createRadialGradient(0, 0, 0, 0, 0, rx);
    gr.addColorStop(0, rgba(C.shadow, a));
    gr.addColorStop(0.55, rgba(C.shadow, a * 0.62));
    gr.addColorStop(1, rgba(C.shadow, 0));
    g.fillStyle = gr;
    g.beginPath(); g.arc(0, 0, rx, 0, TAU); g.fill();
    g.restore();
  };
  // contact shadow under the pooled hem
  blob(0, 22, 600, 110, 0.75);
  if (spread > 0.001) {
    const br = 1 + vfbm(t * 0.08, 41) * 0.03;
    blob(0, lerp(50, 230, spread), lerp(700, 1700, spread) * br, lerp(140, 470, spread) * br, 0.66 * spread);
    // long soft lobes spilling toward the viewer
    for (const [k, ang, len] of [[0, 1.15, 1.0], [1, 1.62, 0.95], [2, 2.0, 0.85], [3, 0.8, 0.7], [4, 2.35, 0.7]]) {
      const L = lerp(300, 1250, spread) * len * (1 + vfbm(t * 0.06 + k * 3, 43 + k) * 0.05);
      const cx = Math.cos(ang) * L * 0.55, cy = 30 + Math.sin(ang) * L * 0.34;
      blob(cx, cy, L * 0.62, L * 0.12, 0.4 * spread, Math.atan2(Math.sin(ang) * 0.34, Math.cos(ang)));
    }
  }
  g.restore();
}

// ------------------------------------------------------------------ glow (for scenes)
export function drawVoidGlow(g, x, y, scale = 1, pose = {}) {
  const cos = clamp(pose.cosmos ?? 0) * (pose.glow ?? 1);
  if (cos <= 0.005) return;
  const r = voidRig(pose);
  const t = pose.t || 0;
  const fx = r.face[0], fy = r.face[1];
  const flick = 1 + vfbm(t * 0.4, 61) * 0.06;
  g.save();
  if (pose.alpha != null) g.globalAlpha *= clamp(pose.alpha);
  g.globalCompositeOperation = 'screen';
  g.translate(x, y);
  g.scale(scale, scale);
  // the light falls on everything around the Void, not on the Void itself (unless pose.glowOnVoid)
  if (!pose.glowOnVoid) excludeVoid(g, r, t);
  // broad violet/teal pool thrown where the Void looks (down + toward headTurn when it bows)
  const cx = fx + r.turn * (180 + r.down * 260), cy = fy + 300 + r.down * 680;
  g.save();
  g.translate(cx, cy);
  g.scale(1, 1.2);
  const RR = 900;
  const gr = g.createRadialGradient(0, 0, 0, 0, 0, RR);
  gr.addColorStop(0, rgba('#9a7cff', 0.28 * cos * flick));
  gr.addColorStop(0.4, rgba('#6a6cf0', 0.11 * cos * flick));
  gr.addColorStop(0.75, rgba('#3fb6d8', 0.04 * cos));
  gr.addColorStop(1, rgba('#3fb6d8', 0));
  g.fillStyle = gr;
  g.fillRect(-RR, -RR, RR * 2, RR * 2);
  g.restore();
  // a tighter bright core right at the hood
  const g2 = g.createRadialGradient(fx, fy, 0, fx, fy, 340);
  g2.addColorStop(0, rgba('#b8a4ff', 0.1 * cos));
  g2.addColorStop(1, rgba('#b8a4ff', 0));
  g.fillStyle = g2;
  g.fillRect(fx - 340, fy - 340, 680, 680);
  g.restore();
}

/** intersect the clip with "everything except the Void's silhouette" (current transform = Void local) */
function excludeVoid(g, R, t) {
  const ex = (build) => { g.beginPath(); g.rect(-9000, -9000, 18000, 18000); build(); g.clip('evenodd'); };
  g.rotate(R.lean);
  ex(() => bodyPath(g, R, t, false));
  ex(() => mantlePath(g, R.hunch, false));
  g.translate(R.pivot[0], R.pivot[1] + R.hoodDy); g.rotate(R.hoodRot);
  ex(() => hoodOuterPath(g, R.H, false));
  g.rotate(-R.hoodRot); g.translate(-R.pivot[0], -(R.pivot[1] + R.hoodDy));
  g.rotate(-R.lean);
  for (const A of [R.armL, R.armR]) { const sg = sleeveGeom(A); ex(() => sleeveSub(g, sg, A)); }
}

// ------------------------------------------------------------------ main
let layer = null;
export function drawVoid(g, x, y, scale = 1, pose = {}) {
  const alpha = pose.alpha == null ? 1 : clamp(pose.alpha);
  if (alpha <= 0.003) return;
  if (alpha < 0.997 && g.canvas && pose.layer !== false) {
    // draw through an offscreen layer so overlapping cloak parts fade as one
    const cw = g.canvas.width, ch = g.canvas.height;
    if (!layer || layer.width !== cw || layer.height !== ch) layer = createCanvas(cw, ch);
    const lg = layer.getContext('2d');
    lg.setTransform(1, 0, 0, 1, 0, 0);
    lg.clearRect(0, 0, cw, ch);
    lg.setTransform(g.getTransform());
    drawVoid(lg, x, y, scale, { ...pose, alpha: 1 });
    g.save();
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.globalAlpha *= alpha;
    g.drawImage(layer, 0, 0);
    g.restore();
    return;
  }
  const t = pose.t || 0;
  const rimK = clamp(pose.rim ?? 1);
  const sil = !!pose.silhouette;
  const bodyA = sil ? 0.1 : 1;
  const R = voidRig(pose);

  const SK = globalThis.__voidSkip || new Set();
  if (!SK.has('shadow') && pose.shadow !== false && !sil) drawVoidShadow(g, x, y, scale, { ...pose, alpha: undefined });

  g.save();
  g.translate(x, y);
  g.scale(scale, scale);
  g.lineCap = 'round'; g.lineJoin = 'round';
  const k = devScale(g);
  const ctx = mkCtx(R, t, rimK, bodyA, k, sil);

  const arms = [R.armL, R.armR];
  for (const A of arms) if (A.hp.front === false && A.hp.defer !== true) drawArm(g, A, ctx, A.hp.defer === 'hand' ? 'sleeve' : 'all');

  g.save();
  g.rotate(R.lean);
  if (!SK.has('body')) drawBody(g, ctx);
  g.restore();

  if (!SK.has('arms')) for (const A of arms) if (A.hp.front !== false && A.hp.defer !== true) drawArm(g, A, ctx, A.hp.defer === 'hand' ? 'sleeve' : 'all');

  g.save();
  g.rotate(R.lean);
  if (!SK.has('mantle')) drawMantle(g, ctx);
  if (!SK.has('hood')) drawHood(g, ctx, pose);
  g.restore();

  g.restore();
}

function mkCtx(R, t, rimK, bodyA, k, sil) {
  return {
    R, t, rimK, bodyA, k, sil,
    // rim shimmer: slow breathing per side + a faint glint that travels down the edges every ~25 s
    shim: (side) => rimK * (0.88 + 0.12 * vfbm(t * 0.3 + side * 5, 71 + side)),
    glint: ((t * 0.04 + 0.15) % 1.25) - 0.1,
  };
}

/**
 * Draw ONE arm (sleeve + hand) on its own — for staging a hand IN FRONT of another character:
 *   drawVoid(g, x, y, s, {...pose, handR: {...hand, defer: true}});   // body (skips the deferred arm)
 *   drawFear(...);                                                     // the character being touched
 *   drawVoidArm(g, x, y, s, pose, 'R');                                // the arm/hand on top
 * part: 'all' (default) | 'sleeve' (no hand) | 'hand' (hand only)
 */
export function drawVoidArm(g, x, y, scale = 1, pose = {}, side = 'R', part = 'all') {
  const R = voidRig(pose);
  const A = side === 'L' || side === -1 ? R.armL : R.armR;
  g.save();
  if (pose.alpha != null) g.globalAlpha *= clamp(pose.alpha);
  g.translate(x, y);
  g.scale(scale, scale);
  g.lineCap = 'round'; g.lineJoin = 'round';
  drawArm(g, A, mkCtx(R, pose.t || 0, clamp(pose.rim ?? 1), pose.silhouette ? 0.1 : 1, devScale(g), !!pose.silhouette), part);
  g.restore();
}
/**
 * Draw ONLY the hand of one arm — for a hand resting on a character standing IN FRONT of the Void
 * while the sleeve stays behind them:
 *   drawVoid(g, x, y, s, {...pose, handR: {...hand, defer: 'hand'}});  // body + sleeve, no hand
 *   drawFear(...);
 *   drawVoidHand(g, x, y, s, pose, 'R');                               // the hand on top of Fear
 */
export function drawVoidHand(g, x, y, scale = 1, pose = {}, side = 'R') {
  drawVoidArm(g, x, y, scale, pose, side, 'hand');
}

// ------------------------------------------------------------------ rim light
/** Soft rim along an open edge path (call while clipped to the shape → inner rim only).
 *  side -1 = violet, +1 = violet with a cyan hint. */
function rimEdge(g, pathFn, side, k, glint, strength = 1, yTop = -1700, yBot = 0) {
  if (k <= 0.005) return;
  const base = side > 0 ? mixColor(C.rim, C.rimCyan, 0.4) : C.rim;
  const hi = side > 0 ? mixColor(C.rimSoft, C.rimCyan, 0.3) : C.rimSoft;
  const mk = (a) => {
    const gr = g.createLinearGradient(0, yTop, 0, yBot);
    gr.addColorStop(0, rgba(hi, a));
    gr.addColorStop(0.4, rgba(base, a * 0.8));
    gr.addColorStop(1, rgba(base, a * 0.16));
    return gr;
  };
  pathFn();
  g.strokeStyle = mk(0.15 * k * strength); g.lineWidth = 36; g.stroke();
  g.strokeStyle = mk(0.36 * k * strength); g.lineWidth = 14; g.stroke();
  g.strokeStyle = mk(0.95 * k * strength); g.lineWidth = 5; g.stroke();
  if (glint > -0.05 && glint < 1.1) {
    const gr = g.createLinearGradient(0, yTop, 0, yBot);
    const p = clamp(glint, 0, 1);
    gr.addColorStop(clamp(p - 0.08), rgba(hi, 0));
    gr.addColorStop(p, rgba('#e6ddff', 0.45 * k * strength));
    gr.addColorStop(clamp(p + 0.08), rgba(hi, 0));
    g.strokeStyle = gr; g.lineWidth = 6; g.stroke();
  }
}
/** faint violet aura just outside an edge (stroke before the fill so the fill covers the inner half) */
function haloEdge(g, pathFn, k, a = 0.07) {
  if (k <= 0.005) return;
  pathFn();
  g.strokeStyle = rgba(C.rim, a * k);
  g.lineWidth = 44; g.stroke();
  g.strokeStyle = rgba(C.rim, a * 1.3 * k);
  g.lineWidth = 18; g.stroke();
}

// ------------------------------------------------------------------ body: tall cloak, pooled hem
const HEM_X = [450, 300, 150, 10, -140, -290, -450];
function hemPoints(t) {
  return HEM_X.map((x, i) => {
    const yb = 8 + 24 * (1 - (x / 450) ** 2);
    return [x + vfbm(t * 0.12 + i * 1.7, 80 + i) * 3, yb + vfbm(t * 0.1 + i * 2.3, 90 + i) * 2];
  });
}
function bodySide(g, side, h, move = true) {
  const s = side;
  if (move) g.moveTo(s * 130, -1416 + h);
  g.quadraticCurveTo(s * 196, -1404 + h, s * 234, -1312 + h);
  g.quadraticCurveTo(s * 250, -1270 + h, s * 250, -1196 + h);
  g.bezierCurveTo(s * 252, -1000, s * 255, -840, s * 262, -700);
  g.bezierCurveTo(s * 274, -470, s * 300, -270, s * 336, -140);
  g.quadraticCurveTo(s * 368, -26, s * 452, 8);
}
function hemPath(g, hp, t, dip = 18, from = true) {
  if (from) g.lineTo(hp[0][0], hp[0][1]);
  for (let i = 0; i < hp.length - 1; i++) {
    const a = hp[i], b = hp[i + 1], m = mid(a, b);
    g.quadraticCurveTo(m[0], m[1] + dip + vfbm(t * 0.14 + i, 99 + i) * 2.5, b[0], b[1]);
  }
}
function bodyPath(g, R, t, begin = true) {
  const h = R.hunch;
  if (begin) g.beginPath();
  g.moveTo(130, -1416 + h);
  // right side down (reverse of bodySide)
  g.quadraticCurveTo(196, -1404 + h, 234, -1312 + h);
  g.quadraticCurveTo(250, -1270 + h, 250, -1196 + h);
  g.bezierCurveTo(252, -1000, 255, -840, 262, -700);
  g.bezierCurveTo(274, -470, 300, -270, 336, -140);
  g.quadraticCurveTo(368, -26, 452, 8);
  hemPath(g, hemPoints(t), t);
  g.lineTo(-452, 8);
  g.quadraticCurveTo(-368, -26, -336, -140);
  g.bezierCurveTo(-300, -270, -274, -470, -262, -700);
  g.bezierCurveTo(-255, -840, -252, -1000, -250, -1196 + h);
  g.quadraticCurveTo(-250, -1270 + h, -234, -1312 + h);
  g.quadraticCurveTo(-196, -1404 + h, -130, -1416 + h);
  g.closePath();
}
const FOLDS = [[-300, -96, 0.9], [-118, -42, 1.1], [64, 22, 1.0], [262, 92, 0.85]];
function drawBody(g, X) {
  const { R, t, rimK, bodyA, sil } = X;
  const h = R.hunch;
  // outer aura along the cloak sides
  for (const side of [-1, 1]) haloEdge(g, () => { g.beginPath(); bodySide(g, side, h); }, rimK);
  g.save();
  bodyPath(g, R, t);
  const gr = g.createLinearGradient(-260, -1300, 220, 0);
  gr.addColorStop(0, rgba(C.bodyLight, bodyA));
  gr.addColorStop(0.32, rgba(C.body, bodyA));
  gr.addColorStop(1, rgba(C.bodyDeep, bodyA));
  g.fillStyle = gr;
  g.fill();
  g.clip();
  if (!sil) {
    // a few long, irregular folds fanning to the hem: soft lit ridge + dark crease
    FOLDS.forEach(([xb, xt, w], i) => {
      const yt = -1180 + h, yb = 22;
      const sway = vfbm(t * 0.09 + i, 120 + i) * 3;
      const ridge = g.createLinearGradient(0, yt, 0, yb);
      ridge.addColorStop(0, rgba(C.bodyLight, 0));
      ridge.addColorStop(0.4, rgba(C.bodyLight, 0.5));
      ridge.addColorStop(1, rgba(C.bodyLight, 0.3));
      g.strokeStyle = ridge; g.lineWidth = 34 * w;
      g.beginPath(); g.moveTo(xt - 10, yt); g.bezierCurveTo(xt * 1.3 - 12, -820, xb * 0.82 - 16 + sway, -380, xb - 20 + sway, yb); g.stroke();
      const crease = g.createLinearGradient(0, yt, 0, yb);
      crease.addColorStop(0, rgba(C.bodyDeep, 0));
      crease.addColorStop(0.35, rgba(C.bodyDeep, 0.8));
      crease.addColorStop(1, rgba(C.bodyDeep, 0.9));
      g.strokeStyle = crease; g.lineWidth = 8 * w;
      g.beginPath(); g.moveTo(xt + 10, yt + 60); g.bezierCurveTo(xt * 1.3 + 12, -800, xb * 0.82 + 14 + sway, -380, xb + 16 + sway, yb + 8); g.stroke();
    });
    // floor contact darkening (hem pooling)
    const gf = g.createLinearGradient(0, -150, 0, 40);
    gf.addColorStop(0, rgba(C.bodyDeep, 0));
    gf.addColorStop(1, rgba(C.bodyDeep, 0.8));
    g.fillStyle = gf;
    g.fillRect(-500, -150, 1000, 200);
  }
  for (const side of [-1, 1]) rimEdge(g, () => { g.beginPath(); bodySide(g, side, h); }, side, X.shim(side), X.glint, 1.0, -1400, 10);
  // faint rim on the hem lip
  if (rimK > 0.01) {
    g.strokeStyle = rgba(C.rim, 0.13 * rimK); g.lineWidth = 4;
    const hp = hemPoints(t);
    g.beginPath(); g.moveTo(hp[0][0], hp[0][1]); hemPath(g, hp, t, 18, false); g.stroke();
  }
  g.restore();
}

// ------------------------------------------------------------------ mantle (cowl drape over the shoulders)
function mantleSide(g, side, h) {
  const s = side;
  g.bezierCurveTo(s * 200, -1420 + h, s * 244, -1360 + h, s * 252, -1290 + h);
  g.quadraticCurveTo(s * 260, -1232 + h, s * 252, -1190 + h);
}
function mantlePath(g, h, begin = true) {
  if (begin) g.beginPath();
  g.moveTo(-140, -1452 + h);
  mantleSide(g, -1, h);
  g.bezierCurveTo(-190, -1150 + h, -70, -1112 + h, 0, -1104 + h);
  g.bezierCurveTo(70, -1112 + h, 190, -1150 + h, 252, -1190 + h);
  g.quadraticCurveTo(260, -1232 + h, 252, -1290 + h);
  g.bezierCurveTo(244, -1360 + h, 200, -1420 + h, 140, -1452 + h);
  g.closePath();
}
function drawMantle(g, X) {
  const { R, rimK, bodyA, sil } = X;
  const h = R.hunch;
  if (!sil) {
    // soft shadow the mantle casts on the chest/sleeves
    const gs = g.createRadialGradient(0, -1150 + h, 60, 0, -1150 + h, 330);
    gs.addColorStop(0, 'rgba(2,1,6,0.18)'); gs.addColorStop(1, 'rgba(2,1,6,0)');
    g.fillStyle = gs;
    g.beginPath(); g.ellipse(0, -1120 + h, 330, 90, 0, 0, TAU); g.fill();
  }
  for (const side of [-1, 1]) haloEdge(g, () => { g.beginPath(); g.moveTo(side * 140, -1452 + h); mantleSide(g, side, h); }, rimK);
  g.save();
  mantlePath(g, h);
  const gr = g.createLinearGradient(-120, -1450 + h, 60, -1110 + h);
  gr.addColorStop(0, rgba('#1b1836', bodyA));
  gr.addColorStop(0.55, rgba('#121029', bodyA));
  gr.addColorStop(1, rgba('#0c0a1b', bodyA));
  g.fillStyle = gr;
  g.fill();
  g.clip();
  if (!sil) {
    // cowl drape: nested U-folds under the hood
    for (const [w, d, a] of [[150, 1250, 0.3], [205, 1190, 0.24], [96, 1300, 0.22]]) {
      g.strokeStyle = `rgba(3,2,9,${a})`; g.lineWidth = 9;
      g.beginPath(); g.moveTo(-w, -1400 + h); g.quadraticCurveTo(0, -d + h - (1400 - d) * 0.35, w, -1400 + h); g.stroke();
      g.strokeStyle = rgba(C.bodyLight, a * 0.55); g.lineWidth = 14;
      g.beginPath(); g.moveTo(-w + 12, -1392 + h); g.quadraticCurveTo(0, -d + h - (1400 - d) * 0.35 + 16, w - 12, -1392 + h); g.stroke();
    }
  }
  if (!sil) {
    for (const side of [-1, 1]) {
      rimEdge(g, () => { g.beginPath(); g.moveTo(side * 140, -1452 + h); mantleSide(g, side, h); }, side, X.shim(side), -1, 1.1, -1460 + h, -1150 + h);
    }
    // lower hem of the mantle catches a whisper of light (layer separation)
    g.strokeStyle = rgba(C.rim, 0.12 * rimK); g.lineWidth = 4;
    g.beginPath(); g.moveTo(-252, -1190 + h);
    g.bezierCurveTo(-190, -1150 + h, -70, -1112 + h, 0, -1104 + h);
    g.bezierCurveTo(70, -1112 + h, 190, -1150 + h, 252, -1190 + h);
    g.stroke();
  }
  g.restore();
}

// ------------------------------------------------------------------ hood
function hoodGeom(turn, down) {
  const at = Math.abs(turn);
  const top = -318 + down * 46;
  const px = -turn * 22;
  const xr = 168 + 30 * Math.max(0, -turn) - 12 * Math.max(0, turn);
  const xl = -(168 + 30 * Math.max(0, turn) - 12 * Math.max(0, -turn));
  const ox = turn * 54, oy = FACE_DY + down * 52;
  const rw = FACE_RX * (1 - 0.28 * at), rh = FACE_RY * (1 - 0.3 * down);
  return { top, px, xr, xl, ox, oy, rw, rh, down, turn };
}
function hoodSide(g, H, side) {
  const xs = side > 0 ? H.xr : H.xl;
  const wy = -150 + H.down * 26;
  g.bezierCurveTo(H.px + side * 58, H.top + 4, xs, H.top + 78, xs, wy);
  g.bezierCurveTo(xs + side * 2, wy + 62, xs + side * 18, -28, xs + side * 62, 26);
}
function hoodOuterPath(g, H, begin = true) {
  if (begin) g.beginPath();
  g.moveTo(H.px, H.top);
  hoodSide(g, H, 1);
  g.quadraticCurveTo(0, 74, H.xl - 62, 26);
  const wy = -150 + H.down * 26;
  g.bezierCurveTo(H.xl - 18, -28, H.xl - 2, wy + 62, H.xl, wy);
  g.bezierCurveTo(H.xl, H.top + 78, H.px - 58, H.top + 4, H.px, H.top);
  g.closePath();
}
function openingPath(g, cx, cy, rw, rh, turn) {
  const w = rw, h = rh;
  const tx = cx + turn * 8;
  const wn = w * (1 - 0.12 * Math.abs(turn)); // turned-to side slightly flatter
  const wR = turn >= 0 ? wn : w, wL = turn >= 0 ? w : wn;
  // gothic arch: a soft point at the top, rounded chin
  g.beginPath();
  g.moveTo(tx, cy - h - 10);
  g.bezierCurveTo(tx + wR * 0.5, cy - h + 2, cx + wR, cy - h * 0.55, cx + wR, cy - h * 0.02);
  g.bezierCurveTo(cx + wR, cy + h * 0.55, cx + wR * 0.55, cy + h, cx, cy + h);
  g.bezierCurveTo(cx - wL * 0.55, cy + h, cx - wL, cy + h * 0.55, cx - wL, cy - h * 0.02);
  g.bezierCurveTo(cx - wL, cy - h * 0.55, tx - wL * 0.5, cy - h + 2, tx, cy - h - 10);
  g.closePath();
}

function drawHood(g, X, pose) {
  const { R, t, rimK, bodyA, sil } = X;
  const H = R.H;
  const cosmos = clamp(pose.cosmos ?? 0);
  g.save();
  g.translate(R.pivot[0], R.pivot[1] + R.hoodDy);
  g.rotate(R.hoodRot);

  if (!sil) {
    // shadow under the hood onto the mantle
    const gs = g.createRadialGradient(0, 30, 20, 0, 30, 240);
    gs.addColorStop(0, 'rgba(2,1,6,0.45)'); gs.addColorStop(1, 'rgba(2,1,6,0)');
    g.fillStyle = gs;
    g.beginPath(); g.ellipse(0, 36, 250, 84, 0, 0, TAU); g.fill();
  }
  const crown = (side) => () => { g.beginPath(); g.moveTo(H.px, H.top); hoodSide(g, H, side); };
  for (const side of [-1, 1]) haloEdge(g, crown(side), rimK, 0.08);

  // hood shell
  g.save();
  hoodOuterPath(g, H);
  const gr = g.createRadialGradient(-60 - R.turn * 40, -250, 10, 0, -120, 300);
  gr.addColorStop(0, rgba(C.hoodLight, bodyA));
  gr.addColorStop(0.55, rgba(C.hood, bodyA));
  gr.addColorStop(1, rgba(C.body, bodyA));
  g.fillStyle = gr;
  g.fill();
  g.clip();
  if (!sil) {
    // crown seam toward the peak + a soft fold beside the face on the far side (reads the turn)
    g.strokeStyle = 'rgba(3,2,9,0.28)'; g.lineWidth = 9;
    g.beginPath(); g.moveTo(H.px, H.top + 16); g.quadraticCurveTo(H.ox * 0.6 - R.turn * 26, H.oy - H.rh - 70, H.ox + R.turn * 8, H.oy - H.rh - 30); g.stroke();
    const fs = R.turn >= 0 ? -1 : 1;
    const fx = H.ox + fs * (H.rw + 46 + Math.abs(R.turn) * 18);
    g.strokeStyle = 'rgba(3,2,9,0.4)'; g.lineWidth = 8;
    g.beginPath(); g.moveTo(fx, H.oy - H.rh * 0.6); g.quadraticCurveTo(fx + fs * 16, H.oy + 10, fx - fs * 6, 30); g.stroke();
    g.strokeStyle = rgba(C.bodyLight, 0.5); g.lineWidth = 12;
    g.beginPath(); g.moveTo(fx - fs * 14, H.oy - H.rh * 0.5); g.quadraticCurveTo(fx + fs * 2, H.oy + 10, fx - fs * 22, 30); g.stroke();
  }
  for (const side of [-1, 1]) rimEdge(g, crown(side), side, X.shim(side), X.glint, 1.15, H.top, 30);
  g.restore();

  // ---- face opening
  const { ox, oy, rw, rh } = H;
  // brim: rolled fabric framing the opening — an elliptical gradient so it melts into the hood shell
  const ell = (cx, cy, sx, stops) => {
    // fill the current path with a radial gradient squashed horizontally by sx (elliptical falloff)
    g.save();
    g.translate(cx, cy); g.scale(sx, 1);
    const r = stops.r;
    const gr = g.createRadialGradient(0, 0, 0, 0, 0, r);
    for (const [o, c] of stops.s) gr.addColorStop(o, c);
    g.fillStyle = gr;
    g.fill();
    g.restore();
  };
  // lip: the hood fabric rolls inward around the opening — soft, directional (lit top-left, shadowed
  // bottom-right) strokes, no hard outer edge, so it reads as cloth at any size
  const lipY = oy - 3 - H.down * 7, lipH = rh + H.down * 7;
  const dirGrad = (a0, a1) => {
    const gr = g.createLinearGradient(ox - rw * 1.1, oy - rh * 1.1, ox + rw * 0.9, oy + rh * 1.1);
    gr.addColorStop(0, a0); gr.addColorStop(1, a1);
    return gr;
  };
  openingPath(g, ox, lipY, rw + 12, lipH + 12, R.turn);
  g.strokeStyle = dirGrad(rgba('#28234f', 0.8 * bodyA), rgba('#100e24', 0.45 * bodyA)); g.lineWidth = 28; g.stroke();
  if (rimK > 0.01) {
    openingPath(g, ox, lipY, rw + 10, lipH + 10, R.turn);
    g.strokeStyle = dirGrad(rgba(C.rimSoft, 0.34 * rimK), rgba(C.rimCyan, 0.06 * rimK)); g.lineWidth = 3;
    g.stroke();
  }
  // inner hood wall: falls off softly into the dark (seen on the far side when turned, at the top when bowed)
  openingPath(g, ox, oy, rw, rh, R.turn);
  ell(ox, oy, rw / rh, { r: rh * 1.02, s: [[0, C.abyss], [0.7, '#030209'], [0.88, '#090817'], [1, '#141129']] });

  // the abyss — shifted toward the turn, lower when bowed
  const ax = ox + R.turn * rw * 0.2, ay = oy + R.down * rh * 0.14 + 4;
  const aw = rw * (1 - 0.18 * Math.abs(R.turn)) - 7, ah = rh * (1 - 0.1 * R.down) - 7;
  g.save();
  openingPath(g, ax, ay, aw, ah, R.turn);
  const ga = g.createRadialGradient(ax, ay + ah * 0.1, 0, ax, ay, Math.max(aw, ah) * 1.05);
  ga.addColorStop(0, C.abyss);
  ga.addColorStop(0.55, '#030209');
  ga.addColorStop(0.85, '#050410');
  ga.addColorStop(1, '#080716');
  g.fillStyle = ga;
  g.fill();
  g.clip();
  if (cosmos > 0.002) {
    const co = pose.cosmosOpts || {};
    drawCosmos(g, ax, ay, aw * 1.04, ah * 1.04, t, { reveal: cosmos, clip: 'none', seed: co.seed ?? 7, glyphs: co.glyphs ?? 1, drift: co.drift ?? 1 });
  }
  // recess: inner shadow at the edge of the abyss + overhang shadow at the top
  const gi = g.createRadialGradient(ax, ay + ah * 0.12, Math.min(aw, ah) * 0.6, ax, ay, Math.max(aw, ah) * 1.05);
  gi.addColorStop(0, 'rgba(1,0,4,0)');
  gi.addColorStop(1, `rgba(1,0,4,${0.5 + 0.3 * cosmos})`);
  g.fillStyle = gi;
  g.fillRect(ax - aw * 1.2, ay - ah * 1.2, aw * 2.4, ah * 2.4);
  const go = g.createLinearGradient(0, ay - ah - 10, 0, ay - ah * 0.5 + R.down * ah * 0.3);
  go.addColorStop(0, 'rgba(1,0,4,0.85)'); go.addColorStop(1, 'rgba(1,0,4,0)');
  g.fillStyle = go;
  g.fillRect(ax - aw * 1.2, ay - ah * 1.2, aw * 2.4, ah * 1.3);
  g.restore();

  // cosmos light catching the inner brim + spilling onto the hood below the face
  if (cosmos > 0.01) {
    g.save();
    g.globalCompositeOperation = 'screen';
    openingPath(g, ox, oy, rw + 5, rh + 5, R.turn);
    const gl = g.createLinearGradient(ox - rw, oy - rh, ox + rw, oy + rh);
    gl.addColorStop(0, rgba('#9f86ff', 0.22 * cosmos));
    gl.addColorStop(1, rgba('#4fc6e6', 0.12 * cosmos));
    g.strokeStyle = gl; g.lineWidth = 6; g.stroke();
    const gsp = g.createRadialGradient(ox, oy + rh * 0.5, 0, ox, oy + rh * 0.5, 250);
    gsp.addColorStop(0, rgba('#8a74ff', 0.13 * cosmos));
    gsp.addColorStop(1, rgba('#8a74ff', 0));
    g.fillStyle = gsp;
    g.fillRect(ox - 250, oy + rh * 0.5 - 250, 500, 500);
    g.restore();
  }
  g.restore();
}

// ------------------------------------------------------------------ arms: bell sleeves + hands
function sleeveGeom(A) {
  const { S, E, W, a1, fa, side } = A;
  const u1 = dir(a1), u2 = dir(fa);
  const n1 = [-u1[1], u1[0]], n2 = [-u2[1], u2[0]];
  let nE = [n1[0] + n2[0], n1[1] + n2[1]];
  const nl = Math.hypot(nE[0], nE[1]) || 1;
  nE = [nE[0] / nl, nE[1] / nl];
  const Cc = add(W, u2, -14); // cuff centre, just before the wrist
  const hS = 58, hE = 60, hC = 88;
  const sag = 70 * Math.abs(Math.cos(fa)); // horizontal forearms droop like a bell sleeve
  // outer edge = the edge farther from the body centre line
  const outerSign = (add(E, nE, 1)[0] * side > add(E, nE, -1)[0] * side) ? 1 : -1;
  const P = (s) => {
    const dn = (n2[1] * s > 0) ? 1 : 0; // this edge faces down
    const longer = s === outerSign ? 30 : 0; // bell cuff cut on a slant: outer edge hangs longer
    return {
      A: add(S, n1, s * hS),
      E: add(add(E, nE, s * hE), [0, 1], dn * sag * 0.3),
      C: add(add(add(Cc, n2, s * hC), [0, 1], dn * sag), u2, longer),
    };
  };
  return { u1, u2, n1, n2, nE, Cc, plus: P(1), minus: P(-1), hS, outerSign };
}
function sleeveSub(g, sg, A) {
  const p = sg.plus, m = sg.minus;
  const mp = mid(p.E, p.C), mm = mid(m.E, m.C);
  g.moveTo(p.A[0], p.A[1]);
  g.quadraticCurveTo(p.E[0], p.E[1], mp[0], mp[1]);
  g.lineTo(p.C[0], p.C[1]);
  const cm = mid(p.C, m.C);
  g.quadraticCurveTo(cm[0] + sg.u2[0] * 16, cm[1] + sg.u2[1] * 16, m.C[0], m.C[1]);
  g.lineTo(mm[0], mm[1]);
  g.quadraticCurveTo(m.E[0], m.E[1], m.A[0], m.A[1]);
  const back = add(A.S, sg.u1, -sg.hS);
  g.quadraticCurveTo(back[0], back[1], p.A[0], p.A[1]);
  g.closePath();
}
function sleeveEdge(g, sg, s) {
  const e = s > 0 ? sg.plus : sg.minus;
  const mE = mid(e.E, e.C);
  g.beginPath(); g.moveTo(e.A[0], e.A[1]); g.quadraticCurveTo(e.E[0], e.E[1], mE[0], mE[1]); g.lineTo(e.C[0], e.C[1]);
}

function drawArm(g, A, X, part = 'all') {
  const { rimK, bodyA, sil, k } = X;
  const sg = sleeveGeom(A);
  const side = A.side, outerSign = sg.outerSign;
  const show = A.show;
  const ha = A.ha;
  const palm = add(A.W, dir(ha), PALM_C);
  if (part === 'hand') {
    if (show > 0.01) {
      if (rimK > 0.01) {
        const gr = g.createRadialGradient(palm[0], palm[1], 0, palm[0], palm[1], 200);
        gr.addColorStop(0, rgba(C.rim, 0.12 * show * rimK));
        gr.addColorStop(1, rgba(C.rim, 0));
        g.fillStyle = gr;
        g.fillRect(palm[0] - 200, palm[1] - 200, 400, 400);
      }
      g.save();
      g.beginPath(); g.rect(-6000, -6000, 12000, 12000); sleeveSub(g, sg, A); g.clip('evenodd');
      drawHand(g, add(A.W, dir(A.fa), -(1 - show) * (HAND_LEN + 30)), ha, side, A.hp, rimK, k);
      g.restore();
    }
    return;
  }
  const withHand = part !== 'sleeve';

  // violet light around an emerging hand
  if (withHand && show > 0.01 && rimK > 0.01) {
    const gr = g.createRadialGradient(palm[0], palm[1], 0, palm[0], palm[1], 200);
    gr.addColorStop(0, rgba(C.rim, 0.2 * show * rimK));
    gr.addColorStop(1, rgba(C.rim, 0));
    g.fillStyle = gr;
    g.fillRect(palm[0] - 200, palm[1] - 200, 400, 400);
  }
  haloEdge(g, () => sleeveEdge(g, sg, outerSign), rimK);

  // sleeve tube
  g.save();
  g.beginPath(); sleeveSub(g, sg, A);
  const lp = sg.plus.E, lm = sg.minus.E;
  const gr = g.createLinearGradient(lp[0], lp[1], lm[0], lm[1]);
  const litPlus = (lp[0] - lm[0]) * -0.7 + (lp[1] - lm[1]) * -0.7 > 0; // + edge faces the upper-left
  gr.addColorStop(0, rgba(litPlus ? C.bodyLight : C.bodyDeep, bodyA));
  gr.addColorStop(0.5, rgba(C.body, bodyA));
  gr.addColorStop(1, rgba(litPlus ? C.bodyDeep : C.bodyLight, bodyA));
  g.fillStyle = gr;
  g.fill();
  g.clip();
  if (!sil) {
    // one long crease + soft elbow wrinkles on the inner side
    const c0 = add(A.S, sg.n1, outerSign * 14), c1 = add(A.E, sg.nE, outerSign * 10), c2 = add(sg.Cc, sg.n2, outerSign * 34);
    g.strokeStyle = 'rgba(3,2,9,0.55)'; g.lineWidth = 7;
    g.beginPath(); g.moveTo(c0[0], c0[1]); g.quadraticCurveTo(c1[0], c1[1], c2[0], c2[1]); g.stroke();
    g.strokeStyle = rgba(C.bodyLight, 0.45); g.lineWidth = 16;
    const d0 = add(c0, sg.n1, -outerSign * 26), d1 = add(c1, sg.nE, -outerSign * 26), d2 = add(c2, sg.n2, -outerSign * 34);
    g.beginPath(); g.moveTo(d0[0], d0[1]); g.quadraticCurveTo(d1[0], d1[1], d2[0], d2[1]); g.stroke();
    const inner = -outerSign;
    for (const [o, l] of [[-24, 40], [16, 50]]) {
      const p0 = add(add(A.E, sg.u2, o), sg.nE, inner * 56);
      const p1 = add(p0, sg.nE, -inner * l);
      g.strokeStyle = 'rgba(3,2,9,0.42)'; g.lineWidth = 5;
      g.beginPath(); g.moveTo(p0[0], p0[1]);
      g.quadraticCurveTo(p0[0] + sg.u2[0] * 12 - sg.nE[0] * inner * l * 0.5, p0[1] + sg.u2[1] * 12 - sg.nE[1] * inner * l * 0.5, p1[0], p1[1]); g.stroke();
    }
  }
  // rims: outer edge strong, inner edge faint (separates the sleeve from the cloak behind it)
  for (const s of [1, -1]) {
    const e = s > 0 ? sg.plus : sg.minus;
    const strong = s === outerSign;
    if (!strong && sil) continue;
    rimEdge(g, () => sleeveEdge(g, sg, s), side, X.shim(side) * (strong ? 1 : 0.4), strong ? X.glint : -1, 0.95,
      Math.min(e.A[1], e.C[1]) - 60, Math.max(e.A[1], e.C[1]) + 60);
  }
  g.restore();

  // cuff opening
  const pc = sg.plus.C, mc = sg.minus.C;
  const cuffA = Math.atan2(mc[1] - pc[1], mc[0] - pc[0]);
  const cuffR = Math.hypot(mc[0] - pc[0], mc[1] - pc[1]) / 2;
  const cuffC = add(mid(pc, mc), sg.u2, 8);
  g.save();
  g.translate(cuffC[0], cuffC[1]); g.rotate(cuffA);
  g.fillStyle = rgba('#020106', Math.max(bodyA, 0.6));
  g.beginPath(); g.ellipse(0, 0, cuffR * 0.96, cuffR * 0.3, 0, 0, TAU); g.fill();
  g.restore();

  // hand — clipped so it only shows outside the sleeve tube (or through the opening)
  if (withHand && show > 0.01) {
    const back = (1 - show) * (HAND_LEN + 30);
    const hw = add(A.W, dir(A.fa), -back);
    g.save();
    g.beginPath();
    g.rect(-6000, -6000, 12000, 12000);
    sleeveSub(g, sg, A);
    g.clip('evenodd');
    drawHand(g, hw, ha, side, A.hp, rimK, k);
    g.restore();
  }

  // near lip of the cuff, over the wrist
  g.save();
  g.translate(cuffC[0], cuffC[1]); g.rotate(cuffA);
  // which half of the ellipse faces the hand direction (u2)? local +y = (-sin, cos) of cuffA
  const lipSign = (-Math.sin(cuffA) * sg.u2[0] + Math.cos(cuffA) * sg.u2[1]) >= 0 ? 1 : -1;
  const a0 = lipSign > 0 ? 0 : Math.PI, a1 = a0 + Math.PI;
  g.strokeStyle = rgba(C.body, Math.max(bodyA, 0.15)); g.lineWidth = 12;
  g.beginPath(); g.ellipse(0, 0, cuffR * 0.96, cuffR * 0.3, 0, a0, a1); g.stroke();
  if (rimK > 0.01) {
    g.strokeStyle = rgba(side > 0 ? mixColor(C.rim, C.rimCyan, 0.3) : C.rim, 0.55 * rimK); g.lineWidth = 3.5;
    g.beginPath(); g.ellipse(0, 0, cuffR * 0.98, cuffR * 0.31, 0, a0 + 0.12, a1 - 0.12); g.stroke();
    g.strokeStyle = rgba(C.rim, 0.25 * rimK); g.lineWidth = 2.5;
    g.beginPath(); g.ellipse(0, 0, cuffR * 0.9, cuffR * 0.25, 0, a1 + 0.3, a1 + Math.PI - 0.3); g.stroke();
  }
  g.restore();
}

/** local (x along hand, y toward thumb) position of the palm centre or the middle fingertip for a hand pose */
function handLocal(hp, side, ang, tip) {
  if (!tip) return [PALM_C, 2];
  const { curl, fore, open } = handParams(hp, side, ang);
  const [bx, by, ba, sp, lens] = FINGERS[2];
  const pts = fingerChain(bx, by, ba + sp * open, lens, curl, fore);
  return pts[pts.length - 1];
}
function handParams(hp, side, ang) {
  const open = clamp(hp.open ?? 0.15), gentle = clamp(hp.gentle ?? 0.2);
  // fingers curl toward whichever side faces down (they drape with gravity) unless specified
  const lyY = Math.cos(ang) * side; // screen-y of local +y
  const curlDir = hp.curl ?? (lyY < -0.25 ? -1 : 1);
  return { open, gentle, curl: curlDir * (0.06 + 0.26 * gentle), fore: 0.16 * gentle };
}

// fingers: [baseX, baseY, baseAngle, spread(open), lengths, widths] — local: x toward the fingertips, thumb on +y
const FINGERS = [
  [83, -25, -0.16, -0.36, [34, 24, 19], [15, 12.5, 10]],   // pinky
  [92, -9, -0.06, -0.13, [43, 30, 23], [17, 14, 11]],      // ring
  [97, 7, 0.02, 0.08, [47, 33, 25], [17.5, 14.5, 11.5]],   // middle
  [94, 23, 0.1, 0.3, [43, 30, 23], [17, 14, 11]],          // index
];
function fingerChain(x, y, a, lens, curl, fore) {
  const pts = [[x, y]];
  let ang = a;
  for (let j = 0; j < lens.length; j++) {
    const L = lens[j] * (1 - fore * (j + 1) / 3);
    x += Math.cos(ang) * L; y += Math.sin(ang) * L;
    pts.push([x, y]);
    ang += curl * (0.7 + j * 0.25);
  }
  return pts;
}
function drawHand(g, wpos, ang, side, hp, rimK, k) {
  const { open, curl, fore } = handParams(hp, side, ang);
  g.save();
  g.translate(wpos[0], wpos[1]);
  g.rotate(ang);
  g.scale(1, side);
  const fingers = FINGERS.map(([bx, by, ba, sp, lens, ws]) => ({ pts: fingerChain(bx, by, ba + sp * open, lens, curl, fore), ws }));
  const gentle = clamp(hp.gentle ?? 0.2);
  const thumb = { pts: fingerChain(24, 28, 0.6 + 0.5 * open - 0.22 * gentle, [38, 30, 24], curl * 0.5 + 0.1, fore * 0.5), ws: [21, 16.5, 12.5] };
  const all = [thumb, ...fingers];
  const palm = () => {
    g.beginPath();
    g.moveTo(-8, -22);
    g.bezierCurveTo(30, -33, 70, -34, 86, -27);
    g.quadraticCurveTo(99, -10, 98, 10);
    g.quadraticCurveTo(97, 28, 90, 31);
    g.bezierCurveTo(66, 40, 34, 40, 10, 28);
    g.quadraticCurveTo(-10, 14, -8, -22);
    g.closePath();
  };
  const strokeChain = (c, extra, color) => {
    g.strokeStyle = color;
    for (let j = 0; j < c.pts.length - 1; j++) {
      g.lineWidth = c.ws[j] + extra;
      g.beginPath(); g.moveTo(c.pts[j][0], c.pts[j][1]); g.lineTo(c.pts[j + 1][0], c.pts[j + 1][1]); g.stroke();
    }
  };
  g.lineCap = 'round'; g.lineJoin = 'round';
  // violet rim outline pass
  const rimCol = rgba(side > 0 ? mixColor(C.rim, C.rimCyan, 0.25) : C.rim, 0.9 * rimK);
  const ow = Math.max(5, 2.6 / k);
  palm(); g.strokeStyle = rimCol; g.lineWidth = ow; g.stroke();
  for (const c of all) strokeChain(c, ow, rimCol);
  // dark fill pass
  palm();
  const gp = g.createLinearGradient(0, -30, 110, 30);
  gp.addColorStop(0, C.hand); gp.addColorStop(1, C.handLight);
  g.fillStyle = gp; g.fill();
  for (const c of all) strokeChain(c, 0, C.handLight);
  if (rimK > 0.01) {
    // finger separation: thin violet line along each finger's pinky-side edge
    g.strokeStyle = rgba(C.rim, 0.34 * rimK); g.lineWidth = Math.max(1.6, 1 / k);
    for (let i = 1; i < fingers.length; i++) {
      const c = fingers[i].pts;
      g.beginPath();
      for (let j = 0; j < c.length; j++) {
        const nx = j < c.length - 1 ? c[j + 1][0] - c[j][0] : c[j][0] - c[j - 1][0];
        const ny = j < c.length - 1 ? c[j + 1][1] - c[j][1] : c[j][1] - c[j - 1][1];
        const l = Math.hypot(nx, ny) || 1;
        const w = fingers[i].ws[Math.min(j, 2)] * 0.5 - 1;
        const px = c[j][0] + (ny / l) * w, py = c[j][1] - (nx / l) * w;
        if (j === 0) g.moveTo(px + nx / l * 6, py + ny / l * 6); else g.lineTo(px, py);
      }
      g.stroke();
    }
    // knuckle glints + thumb-side highlight
    g.fillStyle = rgba(C.rimSoft, 0.16 * rimK);
    for (const f of fingers) { const p = f.pts[1]; g.beginPath(); g.ellipse(p[0], p[1], 7, 5, 0, 0, TAU); g.fill(); }
    g.strokeStyle = rgba(C.rimSoft, 0.35 * rimK); g.lineWidth = 2.2;
    g.beginPath(); g.moveTo(4, 26); g.bezierCurveTo(30, 40, 66, 40, 90, 31); g.stroke();
  }
  g.restore();
}
