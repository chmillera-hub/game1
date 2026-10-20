/* body.mjs — full-figure puppet + detailed hands (keeper | mira | grandpa)
 *
 * drawFigure(g, who, pose, opts)
 *   who  : 'keeper' | 'mira' | 'grandpa'
 *   pose : a POSES entry, walkPose(phase) or blendPose(a,b,k)
 *   opts : x, y   ground point (pelvis x; lowest body point is placed on y — feet, knees, seat or side when lying)
 *          s      scale (s=1 -> Keeper 1000px tall, Mira 620, Grandpa 950)
 *          facing 1 (faces right) | -1 (mirrored)
 *          costume keeper:'new'|'worn'|'dormant'  mira/grandpa:'storm'|'island'
 *          light  LIGHT entry or key name (default LIGHT.day); lightDir radians (screen angle pointing TO the light)
 *                 or [dx,dy]; default upper-left
 *          t      seconds (breathing); breathe 0..1 (default 1)
 *          head   (g, hx, hy, hs, roll) => void  — called in draw order (over torso, under near arm)
 *          chestOpen 0..1, cellOut 0..1 (Keeper: middle cell travels into the near/right hand)
 *          panelGlint 0..1 (sparkle on near shoulder plate), sand 0..1, vines 0..1 (default 1 when 'dormant')
 *          wet 0..1, hood (Mira, default true in 'storm'), capInHand (Grandpa; default true in capChest pose)
 * headSocket(who, pose, opts) -> {x, y, s, roll}   screen point between the eyes; s = drawHead scale
 * handPos(who, pose, opts, side='R') -> {x, y}     screen position of a hand's palm centre (R = near arm)
 * POSES  : stand standLookUp standWind walk kneel crouch crouchCarve sitGround sitKneesUp sitRest sitDoorway
 *          lieSide pushUp reachDown cuppedHands holdUp chestOpen handsLook cling tiller drink brush point
 *          capChest holdHands
 *          pose fields (degrees): lean, neck, rot, shrug, aR/aL [shoulder, elbow, wrist] (from torso-down,
 *          +forward), lR/lL [hip, knee, ankle] (hip +forward, knee +bend), hR/hL hand shape names.
 *          R = near (camera-side) limbs, L = far limbs.
 * walkPose(phase 0..1), blendPose(a, b, k)
 * drawHand(g, o)  o: {x, y (wrist), s (1 -> 140px wrist-to-fingertip), rot (rad, 0 = fingers down),
 *          side 'R'|'L' (L mirrors), who, shape 'open'|'cupped'|'pinch'|'fist'|'point'|'relaxed'|'hold'|'brush',
 *          light, lightDir, costume}   Side view: palm faces +x (for side 'R'), thumb on the near side.
 */
import { PAL, LIGHT, TAU, clamp, lerp, hexToRgb, rgbStr, splinePath, taperStroke, glow, rng } from './core.mjs';

const R = Math.PI / 180;
const dir = a => [Math.sin(a), Math.cos(a)];
const add = (p, v, k = 1) => [p[0] + v[0] * k, p[1] + v[1] * k];

// ------------------------------------------------------------------ proportions (Keeper units, s=1)
const DIM = {
  keeper: { H: 1000, head: 143, torso: 310, neck: 45, thigh: 240, shin: 232, footH: 30, foot: 140, ua: 188, fa: 165,
    hand: 106, sw: 98, ww: 66, hw: 80, rUA: [27, 21], rFA: [22, 15], rTh: [42, 28], rSh: [29, 19], rNeck: 23 },
  mira: { H: 620, head: 113, torso: 180, neck: 24, thigh: 148, shin: 132, footH: 16, foot: 82, ua: 112, fa: 96,
    hand: 66, sw: 64, ww: 50, hw: 54, rUA: [18, 14], rFA: [15, 11], rTh: [27, 19], rSh: [19, 13], rNeck: 14 },
  grandpa: { H: 950, head: 136, torso: 296, neck: 36, thigh: 228, shin: 222, footH: 28, foot: 138, ua: 182, fa: 160,
    hand: 104, sw: 112, ww: 88, hw: 90, rUA: [32, 25], rFA: [26, 18], rTh: [44, 31], rSh: [31, 21], rNeck: 26 },
};

// ------------------------------------------------------------------ poses
const P = (o) => Object.assign({ lean: 2, neck: 0, rot: 0, shrug: 0, aR: [6, 10, 0], aL: [-4, 12, 0],
  lR: [3, 4, 0], lL: [-4, 2, 0], hR: 'relaxed', hL: 'relaxed' }, o);
export const POSES = {
  stand: P({}),
  standLookUp: P({ lean: -5, neck: -24, aR: [4, 8, 0], aL: [-6, 10, 0] }),
  standWind: P({ lean: 9, neck: 8, shrug: 6, aR: [-10, 35, 10], aL: [14, 40, 0], lR: [12, 4, 0], lL: [-12, 3, 0], hR: 'fist' }),
  walk: null, // filled below
  kneel: P({ lean: 8, neck: 10, lR: [-8, 100, -20], lL: [82, 88, 0], aR: [18, 20, 0], aL: [50, 40, 0], hL: 'open' }),
  crouch: P({ lean: 34, neck: -18, lR: [105, 150, 0], lL: [112, 148, 0], aR: [30, 30, 0], aL: [42, 35, 0] }),
  crouchCarve: P({ lean: 40, neck: -10, lR: [100, 145, 0], lL: [115, 150, 0], aR: [62, 25, -10], aL: [40, 55, 10],
    hR: 'hold', hL: 'open' }),
  sitGround: P({ lean: -8, neck: 6, lR: [84, 18, 0], lL: [80, 24, 0], aR: [-32, 6, -60], aL: [-26, 8, -60], hR: 'open', hL: 'open' }),
  sitKneesUp: P({ lean: 12, neck: 8, lR: [118, 132, 0], lL: [112, 128, 0], aR: [52, 70, 0], aL: [46, 76, 0], hR: 'hold', hL: 'hold' }),
  sitRest: P({ lean: 24, neck: 30, shrug: -6, lR: [78, 32, 0], lL: [70, 18, 0], aR: [10, 12, 0], aL: [18, 14, 0] }),
  sitDoorway: P({ lean: 4, neck: 4, lR: [108, 118, 0], lL: [82, 40, 0], aR: [48, 62, 0], aL: [-24, 8, -60], hL: 'open' }),
  lieSide: P({ rot: -90, lean: 0, neck: 8, lR: [28, 40, 0], lL: [16, 22, 0], aR: [58, 60, 0], aL: [70, 30, 0] }),
  pushUp: P({ rot: -52, lean: 6, neck: -14, lR: [126, 38, 0], lL: [118, 30, 0], aR: [54, -6, -70], aL: [44, 0, -70],
    hR: 'open', hL: 'open' }),
  reachDown: P({ lean: 46, neck: -22, lR: [-4, 14, 0], lL: [10, 18, 0], aR: [28, 8, 0], aL: [10, 25, 0], hR: 'open' }),
  cuppedHands: P({ lean: 6, neck: 16, aR: [14, 86, -10], aL: [20, 80, -10], hR: 'cupped', hL: 'cupped' }),
  holdUp: P({ lean: -3, neck: -16, aR: [150, 14, 10], aL: [4, 12, 0], hR: 'hold' }),
  chestOpen: P({ lean: 3, neck: 22, aR: [12, 100, 0], aL: [4, 16, 0] }),
  handsLook: P({ lean: 4, neck: 20, aR: [22, 112, 0], aL: [16, 118, 0], hR: 'open', hL: 'open' }),
  cling: P({ lean: 10, neck: -6, shrug: 8, aR: [112, 40, 0], aL: [124, 30, 0], lR: [12, 24, 0], lL: [-16, 10, 0], hR: 'hold', hL: 'hold' }),
  tiller: P({ lean: 6, neck: -4, aR: [-28, 34, 0], aL: [12, 30, 0], lR: [-14, 8, 0], lL: [20, 12, 0], hR: 'hold' }),
  drink: P({ lean: -4, neck: -12, aR: [36, 124, -20], aL: [8, 18, 0], hR: 'cupped' }),
  brush: P({ lean: 6, neck: 6, aR: [78, 18, -12], hR: 'brush' }),
  point: P({ lean: 3, neck: -4, aR: [84, 6, 0], hR: 'point' }),
  capChest: P({ lean: 6, neck: 18, aR: [8, 96, 0], aL: [8, 26, 0], hR: 'hold' }),
  holdHands: P({ lean: 4, neck: 10, aR: [24, 50, 0], aL: [26, 46, 0], hR: 'hold', hL: 'hold' }),
};
export function walkPose(ph) {
  const a = ph * TAU, sn = Math.sin(a), cs = Math.cos(a);
  const sw = (u) => { const s = Math.sin(u); return [s * 24, Math.max(0, Math.sin(u + 1.4)) * 42 + 4, Math.max(0, -Math.cos(u)) * -12]; };
  return P({ lean: 5, neck: -2 + Math.cos(a * 2) * 1.5, aR: [-sn * 20, 14 + Math.max(0, -sn) * 16, 0],
    aL: [sn * 20, 14 + Math.max(0, sn) * 16, 0], lR: sw(a), lL: sw(a + Math.PI), shrug: cs * 2 });
}
POSES.walk = walkPose(0);
export function blendPose(a, b, k) {
  const o = {};
  for (const key of Object.keys(a)) {
    const va = a[key], vb = b[key] ?? va;
    if (typeof va === 'number') o[key] = lerp(va, vb, k);
    else if (Array.isArray(va)) o[key] = va.map((v, i) => lerp(v, vb[i] ?? v, k));
    else o[key] = k < 0.5 ? va : vb;
  }
  return o;
}

// ------------------------------------------------------------------ shading helpers
function tones(F, c) {
  const A = hexToRgb(c), K = hexToRgb(F.L.key), S = hexToRgb(F.L.shadow), w = F.wet || 0;
  const base = A.map((v, i) => lerp(v, v * K[i] / 255, 0.4) * (1 - w * 0.22));
  const sh = A.map((v, i) => lerp(v * 0.62, S[i] * 0.8, 0.3) * (1 - w * 0.2));
  return [rgbStr(base), rgbStr(sh)];
}
// ink outline (stroke underneath) + shadow fill + lit fill shifted toward light. path() adds a path.
function celFill(g, F, path, c, off = 10, ink = true) {
  const [b, sd] = tones(F, c);
  if (ink) { g.beginPath(); path(); g.lineJoin = 'round'; g.lineCap = 'round'; g.strokeStyle = PAL.ink; g.lineWidth = F.lw * 2; g.stroke(); }
  g.beginPath(); path(); g.fillStyle = sd; g.fill();
  g.save(); g.clip(); g.translate(F.lx * off, F.ly * off); g.beginPath(); path(); g.fillStyle = b; g.fill(); g.restore();
}
function capsule(g, p0, r0, p1, r1) {
  const th = Math.atan2(p1[1] - p0[1], p1[0] - p0[0]);
  g.moveTo(p0[0] + Math.cos(th + Math.PI / 2) * r0, p0[1] + Math.sin(th + Math.PI / 2) * r0);
  g.arc(p0[0], p0[1], r0, th + Math.PI / 2, th + Math.PI * 1.5);
  g.arc(p1[0], p1[1], r1, th - Math.PI / 2, th + Math.PI / 2); g.closePath();
}
// muscle-ish tapered limb: bulge near 30%
function limb(g, p0, r0, p1, r1, bulge = 1.08) {
  const dx = p1[0] - p0[0], dy = p1[1] - p0[1], L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L;
  const rm = lerp(r0, r1, 0.3) * bulge, pm = [p0[0] + dx * 0.32, p0[1] + dy * 0.32];
  const th = Math.atan2(dy, dx);
  g.moveTo(p0[0] + nx * r0, p0[1] + ny * r0);
  g.quadraticCurveTo(pm[0] + nx * rm * 1.05, pm[1] + ny * rm * 1.05, p1[0] + nx * r1, p1[1] + ny * r1);
  g.arc(p1[0], p1[1], r1, th + Math.PI / 2, th - Math.PI / 2, true);
  g.quadraticCurveTo(pm[0] - nx * rm * 1.05, pm[1] - ny * rm * 1.05, p0[0] - nx * r0, p0[1] - ny * r0);
  g.arc(p0[0], p0[1], r0, th - Math.PI / 2, th + Math.PI / 2, true); g.closePath();
}
function fold(g, F, pts, w) { taperStroke(g, pts, 0.1, 0.1, PAL.ink, w * F.lw); }
function lightVec(o) {
  let d = o.lightDir;
  if (d == null) d = [-0.6, -0.8];
  if (typeof d === 'number') d = [Math.cos(d), Math.sin(d)];
  const L = Math.hypot(d[0], d[1]) || 1; return [d[0] / L, d[1] / L];
}
const getLight = (l) => typeof l === 'string' ? (LIGHT[l] || LIGHT.day) : (l || LIGHT.day);
const rotV = (v, a) => [v[0] * Math.cos(a) - v[1] * Math.sin(a), v[0] * Math.sin(a) + v[1] * Math.cos(a)];

// ------------------------------------------------------------------ colours per character/costume
function outfit(who, o) {
  const cos = o.costume || (who === 'keeper' ? 'new' : 'island');
  if (who === 'keeper') {
    const worn = cos !== 'new';
    return { cos, worn, dormant: cos === 'dormant', skin: PAL.kSkin, suit: worn ? '#4c6874' : PAL.kSuit,
      stripe: worn ? '#b98a5c' : PAL.kStripe, panel: cos === 'dormant' ? '#26303f' : PAL.kPanel,
      grid: cos === 'dormant' ? '#3c4a5e' : PAL.kPanelGrid, boot: '#2a2e36', under: '#1b2730' };
  }
  if (who === 'mira') return { cos, skin: PAL.mSkin, coat: PAL.mCoat, shirt: PAL.mShirt, pants: '#4f6a8f',
    boot: cos === 'storm' ? PAL.mCoat : null };
  return { cos, skin: PAL.gSkin, coat: PAL.gCoat, pants: '#2f3239', boot: '#3b2a20', cap: PAL.gCap };
}

// ------------------------------------------------------------------ skeleton
function solve(who, pose, o = {}) {
  const D = DIM[who], p = pose || POSES.stand, t = o.t || 0;
  const stoop = who === 'grandpa' ? 7 : 0;
  const rot = (p.rot || 0) * R, lean = rot + ((p.lean || 0) + stoop) * R;
  const br = (o.breathe ?? 1) * Math.sin(t * TAU / 4.2);
  const fx = [Math.cos(lean), Math.sin(lean)], up = [Math.sin(lean), -Math.cos(lean)];
  const T = (a, b) => [fx[0] * a + up[0] * b, fx[1] * a + up[1] * b];
  const Tt = D.torso, shrug = (p.shrug || 0) * D.H / 1000 + br * 2.5 * D.H / 1000;
  const J = { lean, rot, T, D, br };
  J.pel = [0, 0];
  J.shR = T(-D.sw * 0.7, Tt - 26 * D.H / 1000 + shrug); J.shL = T(D.sw * 0.6, Tt - 22 * D.H / 1000 + shrug);
  J.hpR = T(-D.hw * 0.5, -8); J.hpL = T(D.hw * 0.45, -4);
  J.nb = T(D.sw * 0.08, Tt - 4);
  const na = lean + (p.neck || 0) * R * 0.45, ha = lean + (p.neck || 0) * R;
  J.nt = add(J.nb, [Math.sin(na), -Math.cos(na)], D.neck);
  J.head = add(add(J.nt, [Math.sin(ha), -Math.cos(ha)], D.head * 0.42), [Math.cos(ha), Math.sin(ha)], D.head * 0.08);
  J.headRoll = ha;
  for (const sd of ['R', 'L']) {
    const a = p['a' + sd] || [0, 0, 0], sh = J['sh' + sd];
    const a1 = lean + a[0] * R, a2 = a1 + a[1] * R, a3 = a2 + (a[2] || 0) * R;
    const el = add(sh, dir(a1), D.ua), wr = add(el, dir(a2), D.fa);
    J['arm' + sd] = { sh, el, wr, a1, a2, a3, shape: p['h' + sd] || 'relaxed' };
    const l = p['l' + sd] || [0, 0, 0], hp = J['hp' + sd];
    const b1 = rot + l[0] * R, b2 = b1 - l[1] * R;
    const kn = add(hp, dir(b1), D.thigh), an = add(kn, dir(b2), D.shin);
    const ta = b2 + Math.PI / 2 + (l[2] || 0) * R;
    J['leg' + sd] = { hp, kn, an, b1, b2, ta };
  }
  // grounding: lowest point -> y = 0
  let low = -1e9;
  const pt = (q, r = 0) => { low = Math.max(low, q[1] + r); };
  for (const sd of ['R', 'L']) {
    const L = J['leg' + sd], dn = dir(L.b2), td = dir(L.ta);
    pt(add(L.an, dn, D.footH)); pt(add(add(L.an, td, D.foot * 0.75), dn, D.footH * 0.5));
    pt(L.kn, D.rTh[1]); pt(L.hp, D.rTh[0]);
    pt(J['arm' + sd].el, D.rUA[1]);
  }
  pt(T(0, -D.hw * 0.4), D.hw * 0.4); pt(J.shR, D.rUA[0] * 1.2); pt(J.shL, D.rUA[0]); pt(J.head, D.head * 0.5);
  J.dy = -low;
  return J;
}
function toScreen(J, o, q) {
  const s = o.s ?? 1, f = o.facing ?? 1;
  return [(o.x ?? 0) + f * s * q[0], (o.y ?? 0) + s * (q[1] + J.dy)];
}
export function headSocket(who, pose, o = {}) {
  const J = solve(who, pose, o), [x, y] = toScreen(J, o, J.head);
  return { x, y, s: (o.s ?? 1) * J.D.head / 330, roll: (o.facing ?? 1) * J.headRoll };
}
export function handPos(who, pose, o = {}, side = 'R') {
  const J = solve(who, pose, o), A = J['arm' + side];
  return Object.fromEntries(['x', 'y'].map((k, i) => [k, toScreen(J, o, add(A.wr, dir(A.a3), J.D.hand * 0.45))[i]]));
}

// ------------------------------------------------------------------ hands
const HANDS = { // curl per finger [index, middle, ring, pinky], spread (rad), thumb [base angle, curl1, curl2]
  open: { c: [0.04, 0.03, 0.05, 0.08], sp: 0.11, th: [0.95, 0.05, 0.05] },
  relaxed: { c: [0.22, 0.28, 0.34, 0.4], sp: 0.04, th: [0.45, 0.2, 0.2] },
  cupped: { c: [0.3, 0.32, 0.34, 0.36], sp: 0.0, th: [0.32, 0.12, 0.08], cup: 1 },
  pinch: { c: [0.42, 0.58, 0.68, 0.78], sp: 0.03, th: [0.62, 0.32, 0.25] },
  fist: { c: [1, 1, 1, 1], sp: 0.0, th: [1.05, 0.55, 0.35] },
  point: { c: [0.0, 0.95, 1, 1], sp: 0.04, th: [0.95, 0.5, 0.35] },
  hold: { c: [0.66, 0.68, 0.7, 0.72], sp: 0.0, th: [0.8, 0.35, 0.2] },
  brush: { c: [0.08, 0.1, 0.13, 0.18], sp: 0.05, th: [0.42, 0.1, 0.05] },
};
// draws in current transform; wrist at origin, fingers toward +y, palm toward +x. size 140 units.
function handLocal(g, F, who, shape) {
  const H = HANDS[shape] || HANDS.relaxed, skin = F.skin;
  const k = who === 'mira' ? { fl: 0.84, w: 1.12, pw: 1.05 } : who === 'grandpa' ? { fl: 0.96, w: 1.15, pw: 1.12 } : { fl: 1, w: 1, pw: 1 };
  const pl = 56, pw = 22 * k.pw; // palm length, half-thickness (3/4 view)
  const fingers = [ // base x, length, radius
    [-pw * 0.62, 46, 5.0], [-pw * 0.2, 58, 5.6], [pw * 0.22, 64, 6.0], [pw * 0.62, 60, 5.8],
  ]; // order: pinky .. index (far to near/front)
  const curls = [H.c[3], H.c[2], H.c[1], H.c[0]];
  const sps = [-1.6, -0.6, 0.4, 1.2];
  const chains = fingers.map(([bx, len, rad], i) => {
    const L = len * k.fl, r = rad * k.w, cu = curls[i];
    let a = sps[i] * H.sp + (H.cup ? 0.12 : 0), q = [bx, pl - 2 + Math.abs(i - 1.5) * -2.5];
    const pts = [q];
    [0.45, 0.31, 0.24].forEach((f, j) => { a += cu * [1.5, 1.75, 1.05][j]; q = add(q, dir(a), L * f); pts.push(q); });
    return { pts, r };
  });
  const drawFinger = (c) => celFill(g, F, () => { for (let j = 0; j < 3; j++) capsule(g, c.pts[j], c.r * (1 - j * 0.07), c.pts[j + 1], c.r * (0.93 - j * 0.08)); }, skin, c.r * 0.7);
  const curledBack = (H.c[1] > 0.6);
  // fingers behind palm when open-ish; in front (folded over palm) when curled
  if (!curledBack) chains.forEach(drawFinger);
  // palm
  const palm = () => splinePath(g, [[-pw * 0.6, 0], [-pw * 0.9, pl * 0.55], [-pw * 0.9, pl + 2], [0, pl + 6],
    [pw * 0.92, pl + 2], [pw * 1.05, pl * 0.5], [pw * 0.75, 4]], true);
  celFill(g, F, palm, skin, 9);
  if (curledBack) chains.forEach(drawFinger);
  // knuckle creases
  chains.forEach(c => { if (c.pts.length > 2) { const q = c.pts[1]; taperStroke(g, [add(q, [-c.r * 0.6, -1]), q, add(q, [c.r * 0.5, 1])], 0.2, 0.2, PAL.inkSoft, F.lw * 0.6); } });
  // nails at large scale
  if (F.big) chains.forEach(c => { const a = c.pts[2], b = c.pts[3], d = [b[0] - a[0], b[1] - a[1]], L = Math.hypot(...d) || 1;
    g.beginPath(); g.ellipse(b[0] - d[0] / L * c.r * 0.7 - d[1] / L * c.r * 0.35, b[1] - d[1] / L * c.r * 0.7 + d[0] / L * c.r * 0.35,
      c.r * 0.5, c.r * 0.32, Math.atan2(d[1], d[0]), 0, TAU); g.fillStyle = 'rgba(255,240,230,0.45)'; g.fill(); });
  if (H.cup) taperStroke(g, [[pw * 0.6, pl * 0.35], [pw * 0.15, pl * 0.7], [pw * 0.4, pl + 6]], 0.2, 0.2, PAL.inkSoft, F.lw * 0.8);
  // thumb
  const ta = H.th[0]; let q = [pw * 0.7, 18], a = ta * 0.8;
  const tp = [q]; [24, 19, 16].forEach((len, j) => { if (j) a += H.th[j] * 1.2; q = add(q, dir(a), len * k.fl); tp.push(q); });
  celFill(g, F, () => { capsule(g, tp[0], 9 * k.w, tp[1], 7 * k.w); capsule(g, tp[1], 7 * k.w, tp[2], 6 * k.w); capsule(g, tp[2], 6 * k.w, tp[3], 5 * k.w); }, skin, 6);
  taperStroke(g, [[pw * 0.1, pl * 0.18], [pw * 0.45, pl * 0.42], [pw * 0.5, pl * 0.62]], 0.2, 0.2, PAL.inkSoft, F.lw * 0.6);
  if (who === 'keeper') taperStroke(g, [[-pw * 0.7, 5], [0, 7], [pw * 0.75, 6]], 0.3, 0.3, PAL.kSeam, F.lw * 0.7);
  if (who === 'grandpa') taperStroke(g, [[-pw * 0.4, pl * 0.3], [-pw * 0.1, pl * 0.5]], 0.2, 0.2, PAL.gSkinShadow, F.lw * 0.6);
}
export function drawHand(g, o) {
  const s = o.s ?? 1, side = o.side || 'R', who = o.who || 'keeper';
  const lv = lightVec(o), mir = side === 'L' ? -1 : 1;
  const L0 = rotV([lv[0] * mir, lv[1]], -(o.rot || 0) * mir);
  g.save(); g.translate(o.x, o.y); g.rotate(o.rot || 0); g.scale(s * mir, s);
  const F = { L: getLight(o.light), lx: L0[0], ly: L0[1], lw: clamp(2.6 * s, 1, 3.5) / s, skin: outfit(who, o).skin, big: s > 0.5, wet: o.wet };
  handLocal(g, F, who, o.shape || 'relaxed');
  g.restore();
}

// ------------------------------------------------------------------ figure parts
function drawLeg(g, F, J, L, O, who) {
  const D = J.D, dn = dir(L.b2), td = dir(L.ta);
  const cloth = who === 'keeper' ? O.suit : O.pants;
  // foot
  const ft = () => {
    const heel = add(add(L.an, td, -D.foot * 0.22), dn, D.footH), toe = add(add(L.an, td, D.foot * 0.78), dn, D.footH * 0.75);
    splinePath(g, [add(L.an, td, -D.rSh[1] * 0.9), heel, add(heel, td, D.foot * 0.4), add(toe, dn, D.footH * 0.2),
      add(toe, dn, -D.footH * 0.55), add(add(L.an, td, D.foot * 0.35), dn, -D.footH * 0.35), add(L.an, td, D.rSh[1] * 0.9)], true);
  };
  const bare = who === 'mira' && !O.boot;
  celFill(g, F, ft, bare ? O.skin : (O.boot || '#333'), D.footH * 0.4);
  // shin + thigh
  if (who === 'mira') {
    const roll = lerp(0.55, 1, 0); const mid = add(L.kn, dn, D.shin * 0.55);
    celFill(g, F, () => limb(g, mid, D.rSh[1] * 1.05, L.an, D.rSh[1] * 0.85), O.boot ? O.boot : O.skin, 6);
    celFill(g, F, () => limb(g, L.kn, D.rSh[0], mid, D.rSh[1] * 1.05), cloth, 7);
    celFill(g, F, () => capsule(g, add(mid, dn, -6), D.rSh[1] * 1.25, add(mid, dn, 4), D.rSh[1] * 1.25), '#6d86a8', 4); // roll cuff
    void roll;
  } else {
    celFill(g, F, () => limb(g, L.kn, D.rSh[0], add(L.an, dn, -4), D.rSh[1] * 1.12), cloth, 9);
    const bootTop = add(L.an, dn, -D.shin * 0.2);
    celFill(g, F, () => capsule(g, bootTop, D.rSh[1] * 1.12, L.an, D.rSh[1] * 1.0), O.boot, 6);
  }
  celFill(g, F, () => limb(g, L.hp, D.rTh[0], L.kn, D.rTh[1] * 1.04, 1.04), cloth, 11);
  // folds
  const kn = L.kn, td2 = dir(L.b1);
  fold(g, F, [add(kn, td2, -D.thigh * 0.12), add(add(kn, [td2[1], -td2[0]], D.rTh[1] * 0.5), td2, -D.thigh * 0.05)], 0.9);
  fold(g, F, [add(L.hp, td2, D.thigh * 0.45), add(add(L.hp, td2, D.thigh * 0.6), [-td2[1], td2[0]], D.rTh[1] * 0.4)], 0.7);
}
function drawArm(g, F, J, A, O, who, side) {
  const D = J.D, cloth = who === 'keeper' ? O.suit : O.coat;
  celFill(g, F, () => limb(g, A.el, D.rFA[0], A.wr, D.rFA[1] * 1.15), cloth, 8);
  celFill(g, F, () => limb(g, A.sh, D.rUA[0], A.el, D.rUA[1] * 1.05), cloth, 9);
  const d = dir(A.a2), n = [-d[1], d[0]];
  // cuff
  const c0 = add(A.wr, d, -D.fa * 0.1);
  if (who === 'keeper' && O.worn) { // frayed edge
    g.fillStyle = tones(F, O.suit)[0];
    for (let i = -2; i <= 2; i++) { const b = add(A.wr, n, i * D.rFA[1] * 0.42); g.beginPath();
      g.moveTo(...add(b, n, -D.rFA[1] * 0.2)); g.lineTo(...add(add(b, d, D.rFA[1] * (0.5 + 0.3 * (i & 1))), n, 0)); g.lineTo(...add(b, n, D.rFA[1] * 0.2)); g.fill(); }
  } else fold(g, F, [add(c0, n, -D.rFA[1] * 1.05), add(add(c0, d, 2), n, 0), add(c0, n, D.rFA[1] * 1.05)], 0.8);
  // elbow fold
  const e = A.el, du = dir(A.a1);
  if (Math.abs(A.a2 - A.a1) > 0.3) fold(g, F, [add(e, du, -D.ua * 0.15), add(add(e, [-du[1], du[0]], D.rUA[1] * 0.5), du, -2)], 1);
  fold(g, F, [add(A.sh, du, D.ua * 0.5), add(add(A.sh, du, D.ua * 0.68), [du[1], -du[0]], D.rUA[1] * 0.5)], 0.7);
}
function handInFigure(g, F, J, A, who) {
  const s = J.D.hand / 140;
  g.save(); g.translate(A.wr[0], A.wr[1]); g.rotate(-A.a3); g.scale(s, s);
  const Lv = rotV([F.lx, F.ly], A.a3);
  const lw = F.lw; handLocal(g, { ...F, lx: Lv[0], ly: Lv[1], lw: lw / s, big: false }, who, A.shape);
  g.restore();
}
function shoulderPlate(g, F, J, A, O, glint) {
  const D = J.D, d = dir(A.a1), n = [-d[1], d[0]], c = add(A.sh, d, D.ua * 0.08), w = D.rUA[0] * 1.35, h = D.ua * 0.36;
  const pts = [add(add(c, n, -w), d, -h * 0.35), add(add(c, n, w), d, -h * 0.35), add(add(c, n, w * 0.95), d, h * 0.65), add(add(c, n, -w * 0.95), d, h * 0.65)];
  const path = () => { g.moveTo(...pts[0]); g.quadraticCurveTo(...add(c, d, -h * 0.7), ...pts[1]); g.lineTo(...pts[2]);
    g.quadraticCurveTo(...add(c, d, h * 0.8), ...pts[3]); g.closePath(); };
  celFill(g, F, path, O.panel, 6);
  g.save(); g.beginPath(); path(); g.clip(); g.strokeStyle = O.grid; g.lineWidth = F.lw * 0.6;
  for (let i = 1; i < 4; i++) { const u = -1 + i / 2; g.beginPath(); g.moveTo(...add(add(c, n, w * u), d, -h)); g.lineTo(...add(add(c, n, w * u), d, h)); g.stroke(); }
  for (let i = 0; i < 3; i++) { const v = -0.15 + i * 0.3; g.beginPath(); g.moveTo(...add(add(c, d, h * v), n, -w)); g.lineTo(...add(add(c, d, h * v), n, w)); g.stroke(); }
  g.fillStyle = 'rgba(160,200,255,0.18)'; g.beginPath(); g.moveTo(...pts[0]); g.lineTo(...add(c, n, -w * 0.2)); g.lineTo(...add(add(c, n, -w), d, h * 0.2)); g.fill();
  g.restore();
  if (glint > 0) { const q = add(add(c, n, -w * 0.4), d, -h * 0.1); sparkle(g, q, D.H * 0.06 * glint, glint); }
}
function sparkle(g, q, r, a) {
  glow(g, q[0], q[1], r * 1.2, '#cfe8ff', 0.6 * a);
  g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(255,255,255,${0.9 * a})`; g.beginPath();
  for (let i = 0; i < 8; i++) { const ang = i * Math.PI / 4, rr = i % 2 ? r * 0.12 : r; g.lineTo(q[0] + Math.cos(ang) * rr, q[1] + Math.sin(ang) * rr); }
  g.fill(); g.restore();
}
function powerCell(g, F, q, r, ang = 0, glowK = 1) {
  g.save(); g.translate(q[0], q[1]); g.rotate(ang);
  celFill(g, F, () => capsule(g, [0, -r * 1.3], r, [0, r * 1.3], r), PAL.cellGlow, r * 0.3);
  g.beginPath(); capsule(g, [0, -r * 0.8], r * 0.38, [0, r * 0.8], r * 0.38); g.fillStyle = PAL.hud; g.fill();
  g.fillStyle = '#fff6d8'; g.beginPath(); g.ellipse(-r * 0.45, -r * 0.6, r * 0.18, r * 0.6, 0, 0, TAU); g.fill();
  g.restore(); glow(g, q[0], q[1], r * 4, PAL.cellGlow, 0.55 * glowK); glow(g, q[0], q[1], r * 1.6, PAL.hud, 0.45 * glowK);
}
function drawTorso(g, F, J, O, who, o) {
  const D = J.D, Tt = D.torso, sw = D.sw, ww = D.ww, hw = D.hw;
  g.save(); g.rotate(J.lean);
  const Lv = rotV([F.lx, F.ly], -J.lean), FF = { ...F, lx: Lv[0], ly: Lv[1] };
  const br = 1 + J.br * 0.012;
  const skirt = who === 'mira' ? 70 : who === 'grandpa' ? 46 : 0;
  const pts = [[-sw * 0.96, -(Tt - 26)], [-sw * 0.62, -(Tt + 2)], [-sw * 0.28, -Tt - 8], [sw * 0.22, -Tt - 6], [sw * 0.56, -(Tt - 2)], [sw * 0.86, -(Tt - 22)],
    [sw * 0.88 * br, -Tt * 0.7], [ww * 0.85, -Tt * 0.36], [hw * 0.9 + skirt * 0.25, 4 + skirt], [hw * 0.15, hw * 0.45 + skirt * 1.1],
    [-hw * 1.0 - skirt * 0.25, 4 + skirt], [-ww * 1.0, -Tt * 0.36], [-sw * 0.94 * br, -Tt * 0.7]];
  const path = () => splinePath(g, pts, true);
  const main = who === 'keeper' ? O.suit : O.coat;
  celFill(g, FF, path, main, 22);
  g.save(); g.beginPath(); path(); g.clip();
  if (who === 'keeper') {
    // stripe
    g.fillStyle = tones(FF, O.stripe)[0]; g.beginPath(); g.moveTo(-sw * 1.2, -Tt * 0.8); g.lineTo(sw * 1.2, -Tt * 0.84);
    g.lineTo(sw * 1.2, -Tt * 0.77); g.lineTo(-sw * 1.2, -Tt * 0.73); g.fill();
    // collar
    celFill(g, FF, () => splinePath(g, [[-sw * 0.36, -Tt - 10], [sw * 0.3, -Tt - 8], [sw * 0.2, -Tt + 12], [sw * 0.02, -Tt + 18], [-sw * 0.26, -Tt + 12]], true), O.under, 3);
    fold(g, FF, [[-sw * 0.62, -Tt + 30], [-sw * 0.4, -Tt + 52], [-sw * 0.36, -Tt + 70]], 0.6);
    // zipper / seam lines
    fold(g, FF, [[sw * 0.05, -Tt + 22], [sw * 0.1, -Tt * 0.4], [sw * 0.05, 0]], 0.8);
    // H-7 stencil
    g.fillStyle = O.worn ? 'rgba(230,225,210,0.55)' : 'rgba(240,236,220,0.85)'; g.font = `bold ${Math.round(Tt * 0.06)}px sans-serif`;
    g.fillText('H-7', -sw * 0.72, -Tt * 0.64);
    // chest panel
    const px0 = sw * 0.2, px1 = sw * 0.72, py0 = -Tt * 0.7, py1 = -Tt * 0.44, pwid = px1 - px0;
    const op = clamp(o.chestOpen || 0);
    if (op > 0) {
      g.fillStyle = '#121822'; g.fillRect(px0, py0, pwid, py1 - py0);
      const co = clamp(o.cellOut || 0);
      [0, 1, 2].forEach(i => { if (i === 1 && co > 0) return; powerCell(g, FF, [px0 + pwid * (0.22 + i * 0.28), (py0 + py1) / 2], pwid * 0.09, 0, op); });
    }
    const ang = op * 115 * R, wd = pwid * Math.cos(ang);
    const door = () => { g.rect(Math.min(px0, px0 + wd), py0, Math.abs(wd) + 0.01, py1 - py0); };
    celFill(g, FF, door, wd >= 0 ? (O.worn ? '#56717c' : '#3a5d6e') : '#1f3440', 2, true);
    if (op < 0.05) { g.fillStyle = 'rgba(255,255,255,0.18)'; g.fillRect(px0 + 4, py0 + 4, pwid * 0.2, 3); }
  } else if (who === 'mira') {
    // open coat: shirt with stripes down the front
    const sp = () => splinePath(g, [[sw * 0.0, -Tt + 4], [sw * 0.5, -Tt + 2], [sw * 0.62, -Tt * 0.5], [ww * 0.45, 0], [-ww * 0.05, 0], [-sw * 0.1, -Tt * 0.5]], true);
    celFill(g, FF, sp, O.shirt, 10);
    g.save(); g.beginPath(); sp(); g.clip(); g.fillStyle = 'rgba(255,235,220,0.55)';
    for (let i = 0; i < 7; i++) g.fillRect(-sw, -Tt + 18 + i * Tt * 0.13, sw * 2, Tt * 0.04); g.restore();
    fold(g, FF, [[ww * 0.45, -Tt * 0.2], [ww * 0.4, 10]], 0.7);
    // toggles
    g.fillStyle = '#7a5530'; for (let i = 0; i < 3; i++) { g.fillRect(-sw * 0.2, -Tt * 0.7 + i * Tt * 0.22, sw * 0.14, Tt * 0.035); }
  } else {
    // grandpa jacket: zipper, pocket, collar
    fold(g, FF, [[sw * 0.22, -Tt + 6], [sw * 0.26, -Tt * 0.5], [sw * 0.2, 40]], 1.0);
    celFill(g, FF, () => splinePath(g, [[-ww * 0.7, -Tt * 0.32], [-ww * 0.05, -Tt * 0.34], [-ww * 0.02, -Tt * 0.12], [-ww * 0.72, -Tt * 0.1]], true), O.coat, 4);
    celFill(g, FF, () => splinePath(g, [[-sw * 0.5, -Tt - 10], [sw * 0.45, -Tt - 8], [sw * 0.35, -Tt + 30], [-sw * 0.1, -Tt + 18], [-sw * 0.45, -Tt + 26]], true), PAL.gCoatShadow, 3);
  }
  g.restore();
  // torso folds
  fold(g, FF, [[-ww * 0.7, -Tt * 0.3], [-ww * 0.3, -Tt * 0.22]], 0.8);
  fold(g, FF, [[ww * 0.3, -Tt * 0.12], [ww * 0.7, -Tt * 0.18]], 0.7);
  g.restore();
}
function moundPath(g, c, w, h, n) { // sand pile: wide flat mound along local x axis n=[dx,dy] normal-up
  const u = [-n[1], n[0]];
  splinePath(g, [add(c, u, -w), add(add(c, u, -w * 0.5), n, h * 0.6), add(add(c, u, w * 0.05), n, h), add(add(c, u, w * 0.55), n, h * 0.5), add(c, u, w)], true);
}

// ------------------------------------------------------------------ main
export function drawFigure(g, who, pose, o = {}) {
  const J = solve(who, pose, o), D = J.D, O = outfit(who, o);
  const s = o.s ?? 1, f = o.facing ?? 1, lv = lightVec(o);
  const F = { L: getLight(o.light), lx: lv[0] * f, ly: lv[1], lw: clamp(3 * s + 0.4, 1, 3.5) / s, skin: O.skin, wet: o.wet ?? (O.cos === 'storm' ? 0.7 : 0) };
  const dormant = O.dormant, sand = o.sand ?? (dormant ? 1 : 0), vines = o.vines ?? (dormant ? 1 : 0);
  const begin = () => { g.save(); g.translate(o.x ?? 0, (o.y ?? 0) + s * J.dy); g.scale(f * s, s); };
  begin();
  // far side
  drawArm(g, F, J, J.armL, O, who, 'L'); handInFigure(g, F, J, J.armL, who);
  if (who === 'keeper') shoulderPlate(g, F, J, J.armL, O, 0);
  drawLeg(g, F, J, J.legL, O, who); drawLeg(g, F, J, J.legR, O, who);
  // neck + hood back
  celFill(g, F, () => capsule(g, J.nb, D.rNeck * 1.1, J.nt, D.rNeck), O.skin, 6);
  const hood = who === 'mira' && (o.hood ?? O.cos === 'storm');
  drawTorso(g, F, J, O, who, o);
  if (hood) celFill(g, F, () => { g.ellipse(J.head[0] - D.head * 0.08, J.head[1] - D.head * 0.05, D.head * 0.62, D.head * 0.66, J.headRoll, 0, TAU); }, O.coat, 8);
  else if (who === 'mira') celFill(g, F, () => splinePath(g, [add(J.nb, [-D.sw * 0.9, 6]), add(J.nb, [-D.sw * 0.7, -14]), add(J.nb, [-D.sw * 0.1, -10]), add(J.nb, [-D.sw * 0.2, 12])], true), O.coat, 4);
  g.restore();
  if (o.head) { const h = headSocket(who, pose, o); o.head(g, h.x, h.y, h.s, h.roll); }
  begin();
  if (hood) { // hood rim over forehead
    const c = J.head, r = D.head * 0.6;
    g.save(); g.translate(c[0] - D.head * 0.04, c[1]); g.rotate(J.headRoll);
    g.beginPath(); g.arc(0, 0, r, -Math.PI * 0.95, -Math.PI * 0.08); g.strokeStyle = PAL.ink; g.lineWidth = F.lw * 2 + D.head * 0.12; g.stroke();
    g.strokeStyle = tones(F, O.coat)[0]; g.lineWidth = D.head * 0.12; g.stroke(); g.restore();
  }
  // near arm
  drawArm(g, F, J, J.armR, O, who, 'R');
  const co = clamp(o.cellOut || 0);
  const capHeld = who === 'grandpa' && (o.capInHand ?? pose === POSES.capChest);
  const hp = add(J.armR.wr, dir(J.armR.a3), D.hand * 0.5);
  if (who === 'keeper' && co > 0 && (o.chestOpen ?? 0) > 0) {
    const Tt = D.torso, slot = J.T(D.sw * 0.46, Tt * 0.57), q = [lerp(slot[0], hp[0], co), lerp(slot[1], hp[1], co) - Math.sin(co * Math.PI) * D.H * 0.05];
    powerCell(g, F, q, D.sw * 0.52 * 0.09, co * 0.8);
  }
  handInFigure(g, F, J, J.armR, who);
  if (capHeld) {
    const c = add(hp, [D.hand * 0.3, -D.hand * 0.1]);
    celFill(g, F, () => { g.ellipse(c[0], c[1], D.head * 0.42, D.head * 0.3, -0.3, 0, TAU); }, PAL.gCap, 8);
    for (let i = -2; i <= 2; i++) fold(g, F, [add(c, [i * D.head * 0.12, -D.head * 0.22]), add(c, [i * D.head * 0.13, D.head * 0.22])], 0.6);
    celFill(g, F, () => capsule(g, add(c, [-D.head * 0.38, D.head * 0.12]), D.head * 0.07, add(c, [D.head * 0.32, D.head * 0.2]), D.head * 0.07), PAL.gCapShadow, 2);
  }
  if (who === 'keeper') shoulderPlate(g, F, J, J.armR, O, dormant ? 0 : (o.panelGlint || 0));
  // dormant extras
  if (sand > 0) {
    const sh = [J.armR, J.armL];
    sh.forEach((A, i) => celFill(g, F, () => moundPath(g, add(A.sh, [0, -D.rUA[0] * 0.9]), D.rUA[0] * 1.5 * sand, D.rUA[0] * 0.9 * sand, [0, -1]), PAL.sand, 5));
    [J.legR, J.legL].forEach(L => { const dth = dir(L.b1); if (Math.abs(dth[0]) > 0.6) {
      const c = add(add(L.hp, dth, D.thigh * 0.45), [0, -D.rTh[0] * 0.85]);
      celFill(g, F, () => moundPath(g, c, D.thigh * 0.35 * sand, D.rTh[0] * 0.8 * sand, [0, -1]), PAL.sand, 6); } });
    celFill(g, F, () => moundPath(g, [J.legR.an[0] - D.foot * 0.2, J.legR.an[1] + D.footH], D.foot * 0.9 * sand, D.footH * 1.4 * sand, [0, -1]), PAL.sand, 5);
  }
  if (vines > 0) {
    const r = rng(7), path = [J.shL, J.T(0, D.torso * 0.6), J.T(-D.sw * 0.6, D.torso * 0.2), J.legR.hp, J.legR.kn, J.legR.an];
    const n = Math.max(2, Math.round(path.length * vines));
    const vp = path.slice(0, n).map((q, i) => add(q, [Math.sin(i * 2.1) * 12, Math.cos(i * 1.7) * 10]));
    g.beginPath(); splinePath(g, vp, false); g.strokeStyle = PAL.ink; g.lineWidth = F.lw * 2 + 7; g.stroke();
    g.strokeStyle = PAL.palm; g.lineWidth = 7; g.stroke();
    for (let i = 0; i < vp.length - 1; i++) for (let k = 0; k < 3; k++) {
      const u = (k + 0.5) / 3, q = [lerp(vp[i][0], vp[i + 1][0], u), lerp(vp[i][1], vp[i + 1][1], u)], a = r() * TAU;
      celFill(g, F, () => g.ellipse(q[0] + Math.cos(a) * 16, q[1] + Math.sin(a) * 16, 17, 8, a, 0, TAU), k % 2 ? PAL.palm : '#5c9a52', 3);
    }
  }
  if (F.wet > 0.3) { g.strokeStyle = `rgba(230,245,255,${0.5 * F.wet})`; g.lineWidth = 3; const r = rng(3);
    for (let i = 0; i < 6; i++) { const q = J.T((r() - 0.5) * D.sw * 1.4, D.torso * (0.2 + r() * 0.7)); g.beginPath(); g.moveTo(...q); g.lineTo(q[0] + 2, q[1] + 18); g.stroke(); } }
  g.restore();
}
