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
//   toVoidLocal(x, y, scale, wx, wy)       world point → Void-local coords (for hand targets)
//
// PERFORMANCE: the cloak body, the mantle and the hood shell are rendered once into cached sprites at the
// current on-screen resolution and redrawn with drawImage (body: keyed by quantized scale; mantle: by scale
// only — a bow just translates it; hood: by scale + quantized head pose). The face (abyss/cosmos), moving
// arms, hands, glint, shimmer and hem drift are live. A new head pose costs one hood build (~2 ms at scale
// 0.55, ~4 ms at 1, ~16 ms at 2.3), a new scale ~5-30 ms once. pose.cache = false forces live vector drawing.
//
// POSE (all optional)
//   t            seconds — idle life: barely perceptible hem drift + rim shimmer + a slow travelling glint
//   idle         0..1    (default 1) scales all idle cloak motion; 0 = perfectly frozen (rim light steady)
//   headTurn     -1..1   hood yaw. + = looks toward screen-right (+x), - = screen-left. 0 = facing camera/distance
//                        (the rim light migrates to the back edge of the hood as it turns)
//   headDown     0..1    hood bows to look at someone small at its feet (the mantle settles; shoulders fixed)
//   headTilt     radians extra hood roll
//   lean         radians whole-body lean, pivot at the hem centre on the floor
//   cosmos       0..1    0 = pure darkness; ~0.3 a few stars kindle; 1 = the full universe
//   cosmosOpts   { glyphs, seed, drift } passed through to drawCosmos
//   rim          0..1    rim-light strength (default 1)
//   silhouette   bool    cloak nearly invisible: only rim light + face read
//   alpha        0..1    overall opacity (composited through an offscreen layer, so overlaps don't show)
//   shadow       false to skip the floor shadow (draw it yourself earlier with drawVoidShadow)
//   foldStar     0..1    a single faint star glinting in a fold of the cloth near the hem
//   layer        false = with alpha < 1, skip the offscreen layer (cheaper; overlaps show through)
//   shadowSpread 0..1    0 = contact shadow under the hem; 1 = dark shadow spilling across the room floor
//   handR, handL { show 0..1  hand emerges from inside the sleeve (0 = hidden)
//                  target [x,y] local coords (origin = hem centre on floor, y negative up). Where the PALM
//                         centre goes (or the fingertip if tip:true: middle → index as point → 1). Omit = rest.
//                  reach 0..1 (default 1) blend the arm from its rest position toward target
//                  open 0..1 relaxed → fingers spread;  gentle 0..1 palm softly curved (resting on a shoulder)
//                  point 0..1 index finger extended, the others folded (tip target slides to the index fingertip)
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
  shoulder: (target, side = 1) => ({ show: 1, target, tip: true, open: 0.12, gentle: 0.9, angle: side > 0 ? 0.38 : Math.PI - 0.38 }),
  // one fingertip (index, extended; the other fingers tucked) on the latch — "turns the tiny lock"
  unlock: (target) => ({ show: 1, target, tip: true, point: 1, open: 0.1, gentle: 0.4 }),
  // two fingertips nudge between the shoulder blades; the hand stays open behind the character.
  // side: +1 pushes toward screen-right (hand at the pushed character's left/back), -1 toward screen-left.
  // Draw the hand BEHIND the character (no defer) so the fingertips meet its back edge.
  push: (target, side = 1) => ({ show: 1, target, tip: true, open: 0.4, gentle: 0.2, angle: side > 0 ? 0.12 : Math.PI - 0.12 }),
  // open, softly curved hand held out to the side, fingers forward (side: +1 screen-right hand)
  offer: (target, side = 1) => ({ show: 1, target, open: 0.75, gentle: 0.45, angle: side > 0 ? -0.15 : Math.PI + 0.15 }),
  // index finger extended toward `target` (fingertip contact if it is within reach)
  point: (target) => ({ show: 1, target, tip: true, point: 1, open: 0.05, gentle: 0.2 }),
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

/** world point → Void-local coords (origin = hem centre on the floor, scale 1), e.g. for hand targets */
export const toVoidLocal = (x, y, scale, wx, wy) => [(wx - x) / scale, (wy - y) / scale];

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
  // the shoulder JOINTS never move with a bow (only the mantle settles over them): "the shoulders do not
  // move, only the head" — and it keeps the baked rest sleeves identical to the live ones (no pop when a
  // hand starts to emerge while the hood is bowed)
  const shoulderR = rot([SH_X, SH_Y], lean), shoulderL = rot([-SH_X, SH_Y], lean);
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
  const rest = rot([side * REST[0], REST[1]], r.lean);
  const restA = Math.PI / 2 - side * 0.05;
  const show = clamp(hp.show ?? 0);
  let ha, W;
  if (hp.target) {
    const reach = clamp(hp.reach ?? 1);
    const a0 = Math.atan2(hp.target[1] - S[1], hp.target[0] - S[0]);
    // relaxed hands droop 30% toward the floor; a pointing hand follows the arm line
    const haT = hp.angle ?? lerpAngle(a0, Math.PI / 2, 0.3 * (1 - 0.75 * clamp(hp.point ?? 0)));
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
  let l = Math.max(L1 * 0.42, Math.min(L1, d / (2 * ratio))); // near targets: the sleeve bunches up instead of folding sharply
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
  const spread = Math.round(clamp(pose.shadowSpread ?? 0.3) * 20) / 20;
  const spr = shadowSprite(spread);
  const br = 1 + vfbm(t * 0.08, 41) * 0.025 * spread * clamp(pose.idle ?? 1); // the spill breathes, very slowly
  g.save();
  if (pose.alpha != null) g.globalAlpha *= clamp(pose.alpha);
  g.translate(x, y);
  g.scale(scale, scale);
  g.drawImage(spr, SB.x0 * br, SB.y0, SB.w * br, SB.h * (0.6 + 0.4 * br));
  g.restore();
}
// floor shadow baked once per spread step into a small soft sprite (6 local units per pixel)
const SB = { x0: -1900, y0: -180, w: 3800, h: 900, px: 6 };
const shadowCache = new Map();
function shadowSprite(spread) {
  let c = shadowCache.get(spread);
  if (c) return c;
  c = createCanvas(Math.round(SB.w / SB.px), Math.round(SB.h / SB.px));
  const g = c.getContext('2d');
  g.scale(1 / SB.px, 1 / SB.px);
  g.translate(-SB.x0, -SB.y0);
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
  blob(0, 22, 600, 110, 0.75); // contact shadow under the pooled hem
  if (spread > 0.001) {
    blob(0, lerp(50, 230, spread), lerp(700, 1700, spread), lerp(140, 470, spread), 0.66 * spread);
    // long soft lobes spilling toward the viewer
    for (const [k, ang, len] of [[0, 1.2, 1.0], [1, 1.95, 0.9], [2, 0.8, 0.72], [3, 1.6, 0.8]]) {
      const L = lerp(300, 1250, spread) * len;
      const cx = Math.cos(ang) * L * 0.55, cy = 30 + Math.sin(ang) * L * 0.34;
      blob(cx, cy, L * 0.62, L * 0.12, 0.4 * spread, Math.atan2(Math.sin(ang) * 0.34, Math.cos(ang)));
    }
  }
  shadowCache.set(spread, c);
  return c;
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
  if (pose.glowExcludeHood) excludeVoid(g, r);
  // where the gaze lands: forward/down, toward headTurn as the Void bows to look at someone small
  const lx = fx + r.turn * (260 + r.down * 320);
  // (1) a cone of light falling from the face toward the floor (fades out before the hood, so the
  //     face itself is never washed out)
  // looking straight ahead the light falls forward onto the floor/foreground (low cone); as the Void bows
  // the cone reaches up toward its face
  const top = lerp(-760, fy + r.faceRy + 70, clamp(r.down * 1.4));
  const cy = (top + 40) / 2, ry = (40 - top) / 2 + 60;
  const cxm = (fx + lx) / 2;
  g.save();
  g.translate(cxm, cy);
  g.scale(1, ry / 560);
  let gr = g.createRadialGradient(0, 120, 0, 0, 0, 560);
  const ck = 0.35 + 0.65 * clamp(r.down * 1.5); // the cone mostly matters when it bows toward someone
  gr.addColorStop(0, rgba('#9a7cff', 0.2 * cos * flick * ck));
  gr.addColorStop(0.45, rgba('#6a6cf0', 0.11 * cos * flick * ck));
  gr.addColorStop(0.8, rgba('#3fb6d8', 0.04 * cos * ck));
  gr.addColorStop(1, rgba('#3fb6d8', 0));
  g.fillStyle = gr;
  g.fillRect(-560, -560, 1120, 1120);
  g.restore();
  // (2) a pool on the floor where the light lands
  g.save();
  g.translate(lx, 70);
  g.scale(1, 0.3);
  gr = g.createRadialGradient(0, 0, 0, 0, 0, 900);
  gr.addColorStop(0, rgba('#a58cff', 0.2 * cos * flick));
  gr.addColorStop(0.5, rgba('#5f7cf0', 0.08 * cos));
  gr.addColorStop(1, rgba('#3fb6d8', 0));
  g.fillStyle = gr;
  g.fillRect(-900, -900, 1800, 1800);
  g.restore();
  g.restore();
}

/** intersect the clip with "everything except the hood" (current transform = Void local) — one clip mask */
function excludeVoid(g, R) {
  g.rotate(R.lean);
  g.translate(R.pivot[0], R.pivot[1] + R.hoodDy); g.rotate(R.hoodRot);
  g.beginPath(); g.rect(-9000, -9000, 18000, 18000); hoodOuterPath(g, R.H, false); g.clip('evenodd');
  g.rotate(-R.hoodRot); g.translate(-R.pivot[0], -(R.pivot[1] + R.hoodDy));
  g.rotate(-R.lean);
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
  const idle = clamp(pose.idle ?? 1);
  const R = voidRig(pose);
  const directA = alpha < 0.997 ? alpha : 1; // only when pose.layer === false (overlaps then show)

  if (pose.shadow !== false && !sil) drawVoidShadow(g, x, y, scale, { ...pose, alpha: directA < 1 ? directA : undefined });

  g.save();
  if (directA < 1) g.globalAlpha *= directA;
  g.translate(x, y);
  g.scale(scale, scale);
  g.lineCap = 'round'; g.lineJoin = 'round';
  const k = devScale(g);
  const ctx = mkCtx(R, t, rimK, bodyA, k, sil, idle);
  // hem drift: the bottom of the skirt (below HEM_CUT) sways a few units at the floor — a shear anchored at
  // HEM_CUT, applied to a separate slice of the cached body sprite. Barely perceptible; pose.idle = 0 freezes it.
  const sway = useCacheFor(pose) ? idle * 3 * vfbm(t * 0.07 + 2.3, 33) / -HEM_CUT : 0;

  const arms = [R.armL, R.armR];
  for (const A of arms) if (A.hp.front === false && A.hp.defer !== true) drawArm(g, A, ctx, A.hp.defer === 'hand' ? 'sleeve' : 'all');

  // cloak body (+ arms hanging at rest): cached sprite at the current on-screen resolution in wide/medium
  // shots — the Void's stillness is its character, so the big static silhouette is rendered once.
  const useCache = useCacheFor(pose);                           // body sprite (res capped at 1.6)
  const useHeadCache = useCacheFor(pose);                       // mantle + hood shell sprites (res capped at 2.4)
  const rest = arms.map((A) => useCache && isRest(A.hp));
  g.save();
  g.rotate(R.lean);
  const hemShear = () => g.transform(1, 0, sway, 1, -sway * HEM_CUT, 0);
  if (useCache) {
    // beyond 1.6x the cloak is only seen in close-ups (lower foreground) where a softer upscale reads fine
    const kq = Math.min(1.6, 2 ** (Math.round(Math.log2(k) * 6) / 6));
    const spr = bodySprite(kq, sil, Math.round(rimK * 20) / 20, rest[0], rest[1]);
    if (Math.abs(sway) > 1e-5) {
      // upper part axis-aligned (fast blit); lower slice sheared. The upper part overlaps the slice by a few
      // px (opaque cloth there) so no seam can open between them.
      const sy = Math.round((HEM_CUT - CB.y0) * kq), ov = Math.ceil(3 * kq);
      g.drawImage(spr, 0, 0, spr.width, sy + ov, CB.x0, CB.y0, spr.width / kq, (sy + ov) / kq);
      g.save();
      hemShear();
      g.drawImage(spr, 0, sy, spr.width, spr.height - sy, CB.x0, CB.y0 + sy / kq, spr.width / kq, (spr.height - sy) / kq);
      if (pose.foldStar > 0.005 && !sil) drawFoldStar(g, ctx, clamp(pose.foldStar));
      g.restore();
    } else {
      g.drawImage(spr, CB.x0, CB.y0, spr.width / kq, spr.height / kq);
      if (pose.foldStar > 0.005 && !sil) drawFoldStar(g, ctx, clamp(pose.foldStar));
    }
    drawBodyGlint(g, ctx);
  } else {
    drawBody(g, ctx);
    if (pose.foldStar > 0.005 && !sil) drawFoldStar(g, ctx, clamp(pose.foldStar));
  }
  g.restore();

  arms.forEach((A, i) => { if (!rest[i] && A.hp.front !== false && A.hp.defer !== true) drawArm(g, A, ctx, A.hp.defer === 'hand' ? 'sleeve' : 'all'); });

  g.save();
  g.rotate(R.lean);
  if (useHeadCache) {
    // mantle sprite (pose-independent: a bow only translates it down by the hunch) + hood shell sprite
    // cached per (resolution, quantized head pose); the face is drawn live between them
    const q = (v, n) => Math.round(v * n) / n;
    const Rq = voidRig({ headTurn: q(R.turn, 64), headDown: q(R.down, 64), headTilt: q(pose.headTilt || 0, 256) });
    const kq = Math.min(2.4, 2 ** (Math.round(Math.log2(k) * 6) / 6)); // soft fabric: upscaling beyond 2.4x is fine
    const rimQ = Math.round(rimK * 20) / 20;
    const msp = mantleSprite(kq, sil, rimQ);
    g.drawImage(msp, MB.x0, MB.y0 + Rq.hunch, msp.width / kq, msp.height / kq);
    const spr = headSprite(kq, Rq, sil, rimQ);
    const Xq = mkCtx(Rq, t, rimK, bodyA, k, sil, idle);
    // the hood sprite has a soft hole where the face is: paint the abyss (+ cosmos) first, unclipped, and let
    // the hood's inner wall (baked, fading into the hole) frame and recess it — no per-frame clip masks
    if (!sil) drawFaceUnder(g, Xq, pose);
    g.drawImage(spr, HB.x0, HB.y0, spr.width / kq, spr.height / kq);
    drawHeadShimmer(g, Xq);
    if (sil) drawHood(g, Xq, pose, 'face');
    else drawBrimLight(g, Xq, clamp(pose.cosmos ?? 0));
  } else {
    drawMantle(g, ctx);
    drawHood(g, ctx, pose);
  }
  g.restore();

  g.restore();
}

const HB = { x0: -340, y0: -1790, w: 680, h: 640 }; // hood shell sprite bounds (local units, any head pose)
const MB = { x0: -370, y0: -1490, w: 740, h: 520 }; // mantle sprite bounds at hunch 0 (drawn offset by hunch)
const mantleCache = new Map();
function mantleSprite(kq, sil, rimQ) {
  const key = `${kq.toFixed(4)}|${sil ? 1 : 0}|${rimQ}`;
  let c = mantleCache.get(key);
  if (c) { mantleCache.delete(key); mantleCache.set(key, c); return c; }
  c = createCanvas(Math.ceil(MB.w * kq), Math.ceil(MB.h * kq));
  const x = c.getContext('2d');
  x.scale(kq, kq);
  x.translate(-MB.x0, -MB.y0);
  x.lineCap = 'round'; x.lineJoin = 'round';
  const X = mkCtx({ hunch: 0 }, 0, rimQ, sil ? 0.1 : 1, kq, sil);
  X.shim = () => rimQ * 0.94;
  X.glint = -1;
  drawMantle(x, X);
  mantleCache.set(key, c);
  evict(mantleCache, 8e6);
  return c;
}
const headCache = new Map();
function headSprite(kq, Rq, sil, rimQ) {
  const key = `${kq.toFixed(4)}|${Rq.turn}|${Rq.down}|${Rq.hoodRot.toFixed(4)}|${sil ? 1 : 0}|${rimQ}`;
  let c = headCache.get(key);
  if (c) { headCache.delete(key); headCache.set(key, c); return c; }
  c = createCanvas(Math.ceil(HB.w * kq), Math.ceil(HB.h * kq));
  const x = c.getContext('2d');
  x.scale(kq, kq);
  x.translate(-HB.x0, -HB.y0);
  x.lineCap = 'round'; x.lineJoin = 'round';
  const X = mkCtx(Rq, 0, rimQ, sil ? 0.1 : 1, kq, sil);
  X.shim = () => rimQ * 0.94;
  X.glint = -1;
  drawHood(x, X, {}, 'shell');
  if (!sil) {
    // cut a soft hole through the inner hood wall where the abyss is (its fading edge = the recess)
    const R = Rq, H = R.H;
    const { hx, hy, aw, ah } = holeGeom(R);
    x.save();
    x.translate(R.pivot[0], R.pivot[1] + R.hoodDy);
    x.rotate(R.hoodRot);
    x.globalCompositeOperation = 'destination-out';
    x.translate(hx, hy);
    x.scale(aw / ah, 1);
    const gr = x.createRadialGradient(0, 0, 0, 0, 0, ah * 1.12);
    gr.addColorStop(0, 'rgba(0,0,0,1)');
    gr.addColorStop(0.5, 'rgba(0,0,0,1)');
    gr.addColorStop(0.78, 'rgba(0,0,0,0.55)');
    gr.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = gr;
    x.fillRect(-ah * 1.2, -ah * 1.2, ah * 2.4, ah * 2.4);
    x.restore();
    void H;
  }
  headCache.set(key, c);
  evict(headCache, 12e6);
  return c;
}
function abyssGeom(R) {
  const H = R.H;
  return {
    ax: H.ox + R.turn * H.rw * 0.2, ay: H.oy + R.down * H.rh * 0.14 + 4,
    aw: H.rw * (1 - 0.18 * Math.abs(R.turn)) - 7, ah: H.rh * (1 - 0.1 * R.down) - 7,
  };
}
/** y of the hood shell's lower edge at hood-local x (the quadratic closing hoodOuterPath) */
function hoodBottomAt(H, x) {
  const x0 = H.xr + 62, x2 = H.xl - 62;
  let a = 0, b = 1;
  for (let i = 0; i < 20; i++) { const m = (a + b) / 2; if ((1 - m) * (1 - m) * x0 + m * m * x2 > x) a = m; else b = m; }
  const u = (a + b) / 2;
  return 26 * (1 - u) * (1 - u) + 2 * u * (1 - u) * 74 + 26 * u * u;
}
/** the soft hole cut through the hood sprite's inner wall (hood-local): the abyss must cover exactly this */
function holeGeom(R) {
  const { ax, ay, aw, ah } = abyssGeom(R);
  return { hx: ax, hy: ay + ah * (0.2 + 0.1 * R.down), hrx: aw * 1.14, hry: ah * 1.14, ax, ay, aw, ah };
}
/** abyss backdrop + cosmos, painted under the hood sprite (which frames it through its soft hole). Painted
 *  only inside the hole ellipse, so nothing can show on the mantle or past the hood edge at extreme poses. */
function drawFaceUnder(g, X, pose) {
  const { R, t } = X;
  const H = R.H;
  const cosmos = clamp(pose.cosmos ?? 0);
  const { hx, hy, hrx, hry, ax, ay, aw, ah } = holeGeom(R);
  g.save();
  g.translate(R.pivot[0], R.pivot[1] + R.hoodDy);
  g.rotate(R.hoodRot);
  g.beginPath();
  g.ellipse(hx, hy, hrx, hry, 0, 0, TAU);
  if (cosmos > 0.002) {
    g.fillStyle = C.abyss;
    g.fill();
    // cosmos rect = the hole's bounding box, its bottom kept above the hood's lower edge so no corner can
    // show below the hood (no clip mask: clipping every star stamp costs 5-10 ms in close-ups)
    const top = hy - hry;
    const bot = Math.min(hy + hry, hoodBottomAt(H, hx - hrx) - 2, hoodBottomAt(H, hx + hrx) - 2);
    const co = pose.cosmosOpts || {};
    drawCosmos(g, hx, (top + bot) / 2, hrx, (bot - top) / 2, t, { reveal: cosmos, clip: 'none', seed: co.seed ?? 7, glyphs: co.glyphs ?? 1, drift: co.drift ?? 1 });
  } else {
    // pure darkness: an abyss a shade darker than the cloak, with a subtle depth gradient
    g.save();
    g.translate(ax, ay + ah * 0.1);
    g.scale(aw / ah, 1);
    const ga = g.createRadialGradient(0, 0, 0, 0, 0, ah * 1.05);
    ga.addColorStop(0, C.abyss);
    ga.addColorStop(0.6, '#030209');
    ga.addColorStop(1, '#070614');
    g.fillStyle = ga;
    g.fill(); // the path was built in hood space; the gradient is read in this scaled space (elliptical)
    g.restore();
  }
  g.restore();
}
/** cosmos light catching the inner brim + spilling onto the hood just below the face */
function drawBrimLight(g, X, cosmos) {
  if (cosmos <= 0.01) return;
  const { R } = X;
  const { ox, oy, rw, rh } = R.H;
  g.save();
  g.translate(R.pivot[0], R.pivot[1] + R.hoodDy);
  g.rotate(R.hoodRot);
  g.globalCompositeOperation = 'screen';
  openingPath(g, ox, oy, rw + 2, rh + 2, R.turn); // glow on the same inner edge as the rim (no extra ring)
  const gl = g.createLinearGradient(ox - rw, oy - rh, ox + rw, oy + rh);
  gl.addColorStop(0, rgba('#9f86ff', 0.2 * cosmos));
  gl.addColorStop(1, rgba('#4fc6e6', 0.11 * cosmos));
  g.strokeStyle = gl; g.lineWidth = 9; g.stroke();
  const gsp = g.createRadialGradient(ox, oy + rh * 0.6, 0, ox, oy + rh * 0.6, 190);
  gsp.addColorStop(0, rgba('#8a74ff', 0.14 * cosmos));
  gsp.addColorStop(1, rgba('#8a74ff', 0));
  g.fillStyle = gsp;
  g.fillRect(ox - 190, oy + rh * 0.6 - 190, 380, 380);
  g.restore();
}
/** live rim shimmer on the hood crown (a faint breathing highlight over the cached rim) */
function drawHeadShimmer(g, X) {
  const { R, rimK, t } = X;
  if (rimK <= 0.01) return;
  const H = R.H;
  g.save();
  g.translate(R.pivot[0], R.pivot[1] + R.hoodDy);
  g.rotate(R.hoodRot);
  for (const side of [-1, 1]) {
    const a = 0.22 * rimK * rimTurn(R.turn, side) * clamp(0.5 + X.idle * vfbm(t * 0.35 + side * 3.7, 77 + side));
    if (a < 0.01) continue;
    const gr = g.createLinearGradient(0, H.top, 0, 30);
    gr.addColorStop(0, `rgba(225,215,255,${a})`); gr.addColorStop(1, 'rgba(225,215,255,0)');
    g.strokeStyle = gr; g.lineWidth = 4;
    g.beginPath(); g.moveTo(H.px, H.top); hoodSide(g, H, side); g.stroke();
  }
  g.restore();
}

/** LRU eviction by total pixel budget (Map keeps insertion order; hits are re-inserted) */
function evict(cache, maxPx) {
  let px = 0;
  for (const c of cache.values()) px += c.width * c.height;
  for (const [key, c] of cache) {
    if (px <= maxPx || cache.size <= 1) break;
    px -= c.width * c.height;
    cache.delete(key);
  }
}
const isRest = (hp) => !hp.target && (hp.show ?? 0) <= 0.001 && hp.front !== false && !hp.defer && hp.angle == null && hp.elbow == null && hp.bend == null;
const CB = { x0: -520, y0: -1480, w: 1040, h: 1560 }; // body sprite bounds (local units)
const HEM_CUT = -330;                                    // hem drift slice: the cloak below this sways
const useCacheFor = (pose) => pose.cache !== false;
const bodyCache = new Map();
function bodySprite(kq, sil, rimQ, restL, restR) {
  const key = `${kq.toFixed(4)}|${sil ? 1 : 0}|${rimQ}|${restL ? 1 : 0}${restR ? 1 : 0}`;
  let c = bodyCache.get(key);
  if (c) { bodyCache.delete(key); bodyCache.set(key, c); return c; }
  c = createCanvas(Math.ceil(CB.w * kq), Math.ceil(CB.h * kq));
  const x = c.getContext('2d');
  x.scale(kq, kq);
  x.translate(-CB.x0, -CB.y0);
  x.lineCap = 'round'; x.lineJoin = 'round';
  const R0 = voidRig({});
  const X = mkCtx(R0, 0, rimQ, sil ? 0.1 : 1, kq, sil);
  X.shim = () => rimQ * 0.94;
  X.glint = -1;
  drawBody(x, X);
  if (restL) drawArm(x, R0.armL, X);
  if (restR) drawArm(x, R0.armR, X);
  bodyCache.set(key, c);
  evict(bodyCache, 14e6);
  return c;
}
/** the slow travelling glint along the cloak's edges (live overlay on the cached body) */
function drawBodyGlint(g, X) {
  const p = X.glint;
  if (p <= -0.05 || p >= 1.1 || X.rimK <= 0.01) return;
  const pc = clamp(p, 0, 1);
  g.save();
  const yb = -1400 + 1410 * (pc - 0.09), ye = -1400 + 1410 * (pc + 0.09);
  g.beginPath(); g.rect(-600, yb, 1200, ye - yb); g.clip();
  for (const side of [-1, 1]) {
    const gr = g.createLinearGradient(0, -1400, 0, 10);
    gr.addColorStop(clamp(pc - 0.08), 'rgba(230,221,255,0)');
    gr.addColorStop(pc, `rgba(230,221,255,${0.4 * X.shim(side) * X.glintA})`);
    gr.addColorStop(clamp(pc + 0.08), 'rgba(230,221,255,0)');
    g.strokeStyle = gr; g.lineWidth = 6;
    g.beginPath(); bodySide(g, side, 0); g.stroke();
  }
  g.restore();
}

function mkCtx(R, t, rimK, bodyA, k, sil, idle = 1) {
  return {
    R, t, rimK, bodyA, k, sil, idle,
    // rim shimmer: slow breathing per side (centred on the baked sprite's 0.94) + a faint glint that
    // travels down the edges every ~30 s. idle scales both (0 = rim light perfectly steady).
    shim: (side) => rimK * (0.94 + 0.08 * idle * vfbm(t * 0.3 + side * 5, 71 + side)),
    glint: idle > 0.01 ? ((t * 0.04 + 0.15) % 1.25) - 0.1 : -1,
    glintA: idle,
  };
}
/** "a single faint star glints in a fold of the cloth" (pose.foldStar 0..1) — live, tiny, slow twinkle */
function drawFoldStar(g, X, amt) {
  const [x, y] = [-127, -236];
  const tw = 0.6 + 0.4 * Math.sin(X.t * 1.7 + 0.8);
  const a = amt * tw;
  g.save();
  g.globalCompositeOperation = 'lighter';
  const gr = g.createRadialGradient(x, y, 0, x, y, 40);
  gr.addColorStop(0, `rgba(200,190,255,${0.35 * a})`); gr.addColorStop(0.3, `rgba(138,108,255,${0.12 * a})`); gr.addColorStop(1, 'rgba(138,108,255,0)');
  g.fillStyle = gr; g.fillRect(x - 40, y - 40, 80, 80);
  g.fillStyle = `rgba(240,236,255,${0.9 * a})`;
  const L = 16 + 8 * tw, w = 2.2;
  g.beginPath();
  g.moveTo(x - L, y); g.lineTo(x, y - w); g.lineTo(x + L, y); g.lineTo(x, y + w); g.closePath();
  g.moveTo(x, y - L); g.lineTo(x + w, y); g.lineTo(x, y + L); g.lineTo(x - w, y); g.closePath();
  g.fill();
  g.beginPath(); g.arc(x, y, 3, 0, TAU); g.fill();
  g.restore();
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
  drawArm(g, A, mkCtx(R, pose.t || 0, clamp(pose.rim ?? 1), pose.silhouette ? 0.1 : 1, devScale(g), !!pose.silhouette, clamp(pose.idle ?? 1)), part);
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
function rimEdge(g, pathFn, side, k, glint, strength = 1, yTop = -1700, yBot = 0, glintA = 1) {
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
    gr.addColorStop(p, rgba('#e6ddff', 0.45 * k * strength * glintA));
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
  const h = 0;
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
  const h = 0; // static silhouette: the mantle (which does hunch) always covers the shoulder line
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
  for (const side of [-1, 1]) rimEdge(g, () => { g.beginPath(); bodySide(g, side, h); }, side, X.shim(side), X.glint, 1.0, -1400, 10, X.glintA);
  // faint rim on the hem lip
  if (rimK > 0.01) {
    g.strokeStyle = rgba(C.rim, 0.13 * rimK); g.lineWidth = 4;
    const hp = hemPoints(t);
    g.beginPath(); g.moveTo(hp[0][0], hp[0][1]); hemPath(g, hp, t, 18, false); g.stroke();
  }
  g.restore();
}

// ------------------------------------------------------------------ mantle (cowl drape over the shoulders)
// the mantle is a little wider than the sleeves' shoulder caps so the sleeves emerge from UNDER it
// (no sleeve top ever pokes out beside the shoulders, at rest or reaching)
function mantleSide(g, side, h) {
  const s = side;
  g.bezierCurveTo(s * 214, -1426 + h, s * 282, -1374 + h, s * 298, -1292 + h);
  g.quadraticCurveTo(s * 310, -1236 + h, s * 300, -1186 + h);
}
function mantleHem(g, h) {
  g.bezierCurveTo(-226, -1144 + h, -76, -1110 + h, 0, -1102 + h);
  g.bezierCurveTo(76, -1110 + h, 226, -1144 + h, 300, -1186 + h);
}
function mantlePath(g, h, begin = true) {
  if (begin) g.beginPath();
  g.moveTo(-140, -1452 + h);
  mantleSide(g, -1, h);
  mantleHem(g, h);
  g.quadraticCurveTo(310, -1236 + h, 298, -1292 + h);
  g.bezierCurveTo(282, -1374 + h, 214, -1426 + h, 140, -1452 + h);
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
  g.save();
  mantlePath(g, h);
  const gr = g.createLinearGradient(-120, -1450 + h, 60, -1110 + h);
  gr.addColorStop(0, rgba('#1b1836', bodyA));
  gr.addColorStop(0.55, rgba('#121029', bodyA));
  gr.addColorStop(1, rgba('#0c0a1b', bodyA));
  g.fillStyle = gr;
  g.fill();
  if (!sil) {
    // cowl drape: nested U-folds under the hood (their ends tuck under the hood)
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
    g.beginPath(); g.moveTo(-300, -1186 + h); mantleHem(g, h);
    g.stroke();
  }
  g.restore();
}

// ------------------------------------------------------------------ hood
function hoodGeom(turn, down) {
  const at = Math.abs(turn);
  const top = -318 + down * 46;
  const px = -turn * 30;
  const xr = 168 + 30 * Math.max(0, -turn) - 12 * Math.max(0, turn);
  const xl = -(168 + 30 * Math.max(0, turn) - 12 * Math.max(0, -turn));
  const ox = turn * 72, oy = FACE_DY + down * 52;
  const rw = FACE_RX * (1 - 0.4 * at), rh = FACE_RY * (1 - 0.3 * down);
  return { top, px, xr, xl, ox, oy, rw, rh, down, turn };
}
/** per-side hood rim weight: the edge on the far side from where the hood looks catches more light */
const rimTurn = (turn, side) => 1 - 0.38 * turn * side;
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

function drawHood(g, X, pose, part = 'all') {
  const { R, t, rimK, bodyA, sil } = X;
  const H = R.H;
  const cosmos = clamp(pose.cosmos ?? 0);
  const shell = part !== 'face', face = part !== 'shell';
  g.save();
  g.translate(R.pivot[0], R.pivot[1] + R.hoodDy);
  g.rotate(R.hoodRot);

  if (shell && !sil) {
    // shadow under the hood onto the mantle
    const gs = g.createRadialGradient(0, 30, 20, 0, 30, 240);
    gs.addColorStop(0, 'rgba(2,1,6,0.45)'); gs.addColorStop(1, 'rgba(2,1,6,0)');
    g.fillStyle = gs;
    g.beginPath(); g.ellipse(0, 36, 250, 84, 0, 0, TAU); g.fill();
  }
  const crown = (side) => () => { g.beginPath(); g.moveTo(H.px, H.top); hoodSide(g, H, side); };

  // hood shell
  if (shell) {
  g.save();
  hoodOuterPath(g, H);
  const gr = g.createRadialGradient(-60 - R.turn * 40, -250, 10, 0, -120, 300);
  gr.addColorStop(0, rgba(C.hoodLight, bodyA));
  gr.addColorStop(0.55, rgba(C.hood, bodyA));
  gr.addColorStop(1, rgba(C.body, bodyA));
  g.fillStyle = gr;
  g.fill();
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
  // the rim light migrates to the BACK edge of the hood as it turns (the face side falls into shadow)
  for (const side of [-1, 1]) rimEdge(g, crown(side), side, X.shim(side), X.glint, 1.15 * rimTurn(R.turn, side), H.top, 30, X.glintA);
  g.restore();
  }

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
  if (shell) {
  const lipY = oy - 3 - H.down * 7, lipH = rh + H.down * 7;
  const dirGrad = (a0, a1) => {
    const gr = g.createLinearGradient(ox - rw * 1.1, oy - rh * 1.1, ox + rw * 0.9, oy + rh * 1.1);
    gr.addColorStop(0, a0); gr.addColorStop(1, a1);
    return gr;
  };
  // one soft roll of fabric (stacked strokes → soft outer falloff, no hard outer contour)
  openingPath(g, ox, lipY, rw + 14, lipH + 14, R.turn);
  for (const [w, a] of [[46, 0.26], [30, 0.45], [15, 0.6]]) {
    g.strokeStyle = dirGrad(rgba('#28234f', a * bodyA), rgba('#100e24', a * 0.55 * bodyA)); g.lineWidth = w; g.stroke();
  }
  if (rimK > 0.01) {
    // a single lit edge where the fabric turns inward (the only crisp line around the opening)
    openingPath(g, ox, oy, rw + 2, rh + 2, R.turn);
    g.strokeStyle = dirGrad(rgba(C.rimSoft, 0.34 * rimK), rgba(C.rimCyan, 0.06 * rimK)); g.lineWidth = 3;
    g.stroke();
  }
  // inner hood wall: falls off softly into the dark (seen on the far side when turned, at the top when bowed)
  openingPath(g, ox, oy, rw, rh, R.turn);
  ell(ox, oy, rw / rh, { r: rh * 1.02, s: [[0, C.abyss], [0.7, '#030209'], [0.88, '#090817'], [1, '#141129']] });
  }
  if (!face) { g.restore(); return; }

  // the abyss — shifted toward the turn, lower when bowed
  const ax = ox + R.turn * rw * 0.2, ay = oy + R.down * rh * 0.14 + 4;
  const aw = rw * (1 - 0.18 * Math.abs(R.turn)) - 7, ah = rh * (1 - 0.1 * R.down) - 7;
  g.save();
  openingPath(g, ax, ay, aw, ah, R.turn);
  if (cosmos <= 0.002) {
    // pure darkness: an abyss a shade darker than the cloak, with a subtle depth gradient
    const ga = g.createRadialGradient(ax, ay + ah * 0.1, 0, ax, ay, Math.max(aw, ah) * 1.05);
    ga.addColorStop(0, C.abyss);
    ga.addColorStop(0.55, '#030209');
    ga.addColorStop(0.85, '#040310');
    ga.addColorStop(1, '#070614');
    g.fillStyle = ga;
    g.fill();
    g.restore(); g.restore();
    return;
  }
  g.clip();
  {
    const co = pose.cosmosOpts || {};
    drawCosmos(g, ax, ay, aw * 1.04, ah * 1.04, t, { reveal: cosmos, clip: 'none', seed: co.seed ?? 7, glyphs: co.glyphs ?? 1, drift: co.drift ?? 1 });
  }
  // recess: inner shadow at the edge of the abyss + overhang shadow at the top
  // (one radial pass, centred low so the top — under the hood's overhang — sinks deepest)
  g.save();
  g.translate(ax, ay + ah * (0.22 + 0.1 * R.down));
  g.scale(aw / ah, 1);
  const gi = g.createRadialGradient(0, 0, ah * 0.55, 0, 0, ah * 1.3);
  gi.addColorStop(0, 'rgba(1,0,4,0)');
  gi.addColorStop(0.55, `rgba(1,0,4,${0.35 + 0.2 * cosmos})`);
  gi.addColorStop(1, 'rgba(1,0,4,0.92)');
  g.fillStyle = gi;
  g.fillRect(-ah * 1.4, -ah * 1.6, ah * 2.8, ah * 2.8);
  g.restore();
  g.restore();

  // cosmos light catching the inner brim + spilling onto the hood below the face
  if (cosmos > 0.01) {
    g.save();
    g.globalCompositeOperation = 'screen';
    openingPath(g, ox, oy, rw + 2, rh + 2, R.turn);
    const gl = g.createLinearGradient(ox - rw, oy - rh, ox + rw, oy + rh);
    gl.addColorStop(0, rgba('#9f86ff', 0.2 * cosmos));
    gl.addColorStop(1, rgba('#4fc6e6', 0.11 * cosmos));
    g.strokeStyle = gl; g.lineWidth = 9; g.stroke();
    const gsp = g.createRadialGradient(ox, oy + rh * 0.6, 0, ox, oy + rh * 0.6, 190);
    gsp.addColorStop(0, rgba('#8a74ff', 0.14 * cosmos));
    gsp.addColorStop(1, rgba('#8a74ff', 0));
    g.fillStyle = gsp;
    g.fillRect(ox - 190, oy + rh * 0.6 - 190, 380, 380);
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
      if (show < 0.999) { g.beginPath(); g.rect(-6000, -6000, 12000, 12000); sleeveSub(g, sg, A); g.clip('evenodd'); }
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
      Math.min(e.A[1], e.C[1]) - 60, Math.max(e.A[1], e.C[1]) + 60, X.glintA ?? 1);
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
    if (show < 0.999) { g.beginPath(); g.rect(-6000, -6000, 12000, 12000); sleeveSub(g, sg, A); g.clip('evenodd'); }
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
  // contact = middle fingertip, sliding to the index fingertip as the hand points (continuous in `point`)
  const { fingers, point } = handShape(hp, side, ang);
  const m = fingers[2].pts.at(-1), ix = fingers[3].pts.at(-1);
  return [lerp(m[0], ix[0], point), lerp(m[1], ix[1], point)];
}
function handParams(hp, side, ang) {
  const open = clamp(hp.open ?? 0.15), gentle = clamp(hp.gentle ?? 0.2), point = clamp(hp.point ?? 0);
  // fingers curl toward whichever side faces down (they drape with gravity) unless specified
  const lyY = Math.cos(ang) * side; // screen-y of local +y
  const curlDir = hp.curl ?? (lyY < -0.25 ? -1 : 1);
  return { open, gentle, point, curlDir, curl: curlDir * (0.06 + 0.26 * gentle), fore: 0.16 * gentle };
}
/** finger + thumb chains for a hand pose (hand-local: x toward the fingertips, thumb on +y) */
function handShape(hp, side, ang) {
  const P = handParams(hp, side, ang);
  const { open, curl, fore, point, gentle } = P;
  const fingers = FINGERS.map(([bx, by, ba, sp, lens, ws], i) => {
    if (i === 3) {
      // index: straightens and reaches a touch further as the hand points
      return { pts: fingerChain(bx, by, ba + sp * open * (1 - point) + 0.04 * point, lens, curl * (1 - point), fore * (1 - point)), ws };
    }
    // pinky/ring/middle: fold away under the palm (foreshortened knuckles, bent away from the index)
    const c = lerp(curl, -0.42 + (i - 1) * 0.05, point);
    return { pts: fingerChain(bx - point * 6, by, ba + sp * open * (1 - point) - 0.1 * point, lens, c, lerp(fore, 0.72, point)), ws };
  });
  const thumb = { pts: fingerChain(24, 28, 0.6 + 0.5 * open * (1 - point) - 0.22 * gentle - 0.25 * point, [38, 30, 24], (curl * 0.5 + 0.1) * (1 - point) - 0.12 * point, lerp(fore * 0.5, 0.35, point)), ws: [21, 16.5, 12.5] };
  return { ...P, fingers, thumb };
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
/** closed tapered outline around a finger chain (round tip) — `grow` expands it (for the rim pass) */
function fingerOutline(g, pts, ws, grow) {
  const n = pts.length;
  const wAt = (i) => (i === 0 ? ws[0] : i === n - 1 ? ws[n - 2] * 0.82 : (ws[i - 1] + ws[i]) / 2) / 2 + grow;
  const nrm = [];
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
    const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
    nrm.push([-dy / l, dx / l]);
  }
  g.moveTo(pts[0][0] + nrm[0][0] * wAt(0), pts[0][1] + nrm[0][1] * wAt(0));
  for (let i = 1; i < n; i++) g.lineTo(pts[i][0] + nrm[i][0] * wAt(i), pts[i][1] + nrm[i][1] * wAt(i));
  const e = pts[n - 1], an = Math.atan2(nrm[n - 1][1], nrm[n - 1][0]);
  g.arc(e[0], e[1], wAt(n - 1), an, an + Math.PI, true);
  for (let i = n - 1; i >= 0; i--) g.lineTo(pts[i][0] - nrm[i][0] * wAt(i), pts[i][1] - nrm[i][1] * wAt(i));
  g.closePath();
}
function drawHand(g, wpos, ang, side, hp, rimK, k) {
  const { fingers, thumb } = handShape(hp, side, ang);
  g.save();
  g.translate(wpos[0], wpos[1]);
  g.rotate(ang);
  g.scale(1, side);
  const all = [thumb, ...fingers];
  const palm = () => {
    g.moveTo(-8, -22);
    g.bezierCurveTo(30, -33, 70, -34, 86, -27);
    g.quadraticCurveTo(99, -10, 98, 10);
    g.quadraticCurveTo(97, 28, 90, 31);
    g.bezierCurveTo(66, 40, 34, 40, 10, 28);
    g.quadraticCurveTo(-10, 14, -8, -22);
    g.closePath();
  };
  g.lineCap = 'round'; g.lineJoin = 'round';
  // violet rim: one expanded silhouette (palm stroke + grown finger outlines in a single fill)
  const ow = Math.max(2.6, 1.3 / k);
  const rimCol = rgba(side > 0 ? mixColor(C.rim, C.rimCyan, 0.25) : C.rim, 0.9 * rimK);
  if (rimK > 0.01) {
    g.beginPath(); palm(); g.strokeStyle = rimCol; g.lineWidth = ow * 2; g.stroke();
    g.beginPath(); for (const c of all) fingerOutline(g, c.pts, c.ws, ow); g.fillStyle = rimCol; g.fill();
  }
  // dark hand
  g.beginPath(); palm();
  const gp = g.createLinearGradient(0, -30, 110, 30);
  gp.addColorStop(0, C.hand); gp.addColorStop(1, C.handLight);
  g.fillStyle = gp; g.fill();
  g.beginPath(); for (const c of all) fingerOutline(g, c.pts, c.ws, 0); g.fillStyle = C.handLight; g.fill();
  if (rimK > 0.01) {
    // finger separation: thin violet line along each finger's pinky-side edge (one stroke for all)
    g.strokeStyle = rgba(C.rim, 0.34 * rimK); g.lineWidth = Math.max(1.6, 1 / k);
    g.beginPath();
    for (let i = 1; i < fingers.length; i++) {
      const c = fingers[i].pts;
      for (let j = 0; j < c.length; j++) {
        const nx = j < c.length - 1 ? c[j + 1][0] - c[j][0] : c[j][0] - c[j - 1][0];
        const ny = j < c.length - 1 ? c[j + 1][1] - c[j][1] : c[j][1] - c[j - 1][1];
        const l = Math.hypot(nx, ny) || 1;
        const w = fingers[i].ws[Math.min(j, 2)] * 0.5 - 1;
        const px = c[j][0] + (ny / l) * w, py = c[j][1] - (nx / l) * w;
        if (j === 0) g.moveTo(px + nx / l * 6, py + ny / l * 6); else g.lineTo(px, py);
      }
    }
    g.stroke();
    // knuckle glints + thumb-side highlight
    g.fillStyle = rgba(C.rimSoft, 0.16 * rimK);
    g.beginPath();
    for (const f of fingers) { const p = f.pts[1]; g.moveTo(p[0] + 7, p[1]); g.ellipse(p[0], p[1], 7, 5, 0, 0, TAU); }
    g.fill();
    g.strokeStyle = rgba(C.rimSoft, 0.35 * rimK); g.lineWidth = 2.2;
    g.beginPath(); g.moveTo(4, 26); g.bezierCurveTo(30, 40, 66, 40, 90, 31); g.stroke();
  }
  g.restore();
}
