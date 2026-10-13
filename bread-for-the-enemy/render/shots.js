// Shot library: camera framing, lighting, character placement, gaze targets.
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const L = require('./lib');
const { clamp, lerp, mix, rgba, shade, smooth } = L;
const BG = require('./backgrounds');
const B = require('./body');
const { drawCharacter } = require('./actor');
const { drawHead } = require('./face');
const { C } = require('./characters');

const VW = 1080, VH = 1920;

// ---------------------------------------------------------------- lighting presets
const LIGHT = {
  lamp: { side: -1, key: '#ffe2bc', amb: '#a87a62', shadow: 0.68, rim: '#ffb060', rimA: 0.35, rimSide: 1, wrap: 0.75 },
  lampR: { side: 1, key: '#ffe2bc', amb: '#a87a62', shadow: 0.68, rim: '#ffb060', rimA: 0.3, rimSide: -1, wrap: 0.75 },
  street: { side: -1, key: '#ffcf9e', amb: '#5a6894', shadow: 0.78, rim: '#a8c0ff', rimA: 0.5, rimSide: 1, wrap: 0.65 },
  church: { side: 1, key: '#ffdcb0', amb: '#9a6a5a', shadow: 0.7, rim: '#ffb060', rimA: 0.4, rimSide: -1, wrap: 0.7 },
  cellL: { side: -1, key: '#e4eaff', amb: '#6c6e8c', shadow: 0.72, rim: '#ffa860', rimA: 0.45, rimSide: 1, wrap: 0.7 },
  cellR: { side: -1, key: '#e8ecff', amb: '#6c6e8c', shadow: 0.72, rim: '#ffa860', rimA: 0.35, rimSide: 1, wrap: 0.8 },
  cellWarm: { side: -1, key: '#fff0dc', amb: '#8a7480', shadow: 0.62, rim: '#ffd090', rimA: 0.5, rimSide: 1, wrap: 0.85 },
  jer: { side: 1, key: '#ffbf86', amb: '#3e4c7c', shadow: 0.82, rim: '#ff9a50', rimA: 0.45, rimSide: -1, wrap: 0.6 },
  jerCool: { side: -1, key: '#c8d4ff', amb: '#3a466e', shadow: 0.8, rim: '#ff9a50', rimA: 0.5, rimSide: 1, wrap: 0.6 },
  desert: { side: 1, key: '#fff4e2', amb: '#b88c84', shadow: 0.55, rim: '#ffffff', rimA: 0.25, rimSide: -1, wrap: 0.8 },
  divine: { side: -1, key: '#fffaf0', amb: '#e8cfb0', shadow: 0.32, rim: '#ffffff', rimA: 0.85, rimSide: 1, wrap: 1.0 },
  lightUp: { side: 1, key: '#fff8e8', amb: '#c8a890', shadow: 0.45, rim: '#ffffff', rimA: 0.7, rimSide: -1, wrap: 0.9 },
  dawn: { side: 1, key: '#ffd6a6', amb: '#7a5a78', shadow: 0.62, rim: '#ffcc80', rimA: 0.65, rimSide: 1, wrap: 0.7 },
};

// ---------------------------------------------------------------- look maps
function looks(base, extra) { return Object.assign({ default: base }, extra || {}); }

// ---------------------------------------------------------------- caching
const cache = new Map();
function cached(key, painter, blur = 0, scale = 1) {
  if (cache.has(key)) return cache.get(key);
  const R = global.RENDER_SCALE || 1;
  const c = createCanvas(Math.round(VW * R), Math.round(VH * R));
  const x = c.getContext('2d');
  x.scale(R, R);
  painter(x);
  let out = c;
  if (blur > 0) {
    const c2 = createCanvas(c.width, c.height);
    const x2 = c2.getContext('2d');
    x2.filter = `blur(${blur * R}px)`;
    x2.drawImage(c, 0, 0);
    out = c2;
  }
  if (cache.size > 24) cache.delete(cache.keys().next().value);
  cache.set(key, out);
  return out;
}
function drawCached(ctx, img) { ctx.drawImage(img, 0, 0, VW, VH); }
// paint a background through a zoom/offset window (for close-ups) then blur
function bgView(key, painter, view, blur) {
  return cached(key + JSON.stringify(view) + blur, (x) => {
    x.translate(VW / 2, VH / 2); x.scale(view.z, view.z); x.translate(-view.cx, -view.cy);
    painter(x);
  }, blur);
}

// ---------------------------------------------------------------- helpers
function actor(ctx, W, who, t, place, Lt, look, opt = {}) {
  const F = W.state(who, t, look);
  if (opt.mod) opt.mod(F);
  const sway = W.headLag(who, t, look);
  const res = drawCharacter(ctx, who, F, place, Lt, t, Object.assign({ sway }, opt));
  if (!opt.noTag && res && res.H) {
    // remember where this character's head landed on screen (for name tags)
    const m = ctx.getTransform();
    const R = global.RENDER_SCALE || 1;
    const X = (m.a * res.H.x + m.c * res.H.y + m.e) / R, Y = (m.b * res.H.x + m.d * res.H.y + m.f) / R;
    global.HEADPOS = global.HEADPOS || {};
    global.HEADPOS[who] = { x: X, y: Y, s: res.H.s * Math.hypot(m.a, m.b) / R };
  }
  return res;
}
// a soft golden halo behind a head: warm glow plus a fine gold ring that reads on light or dark skies
function halo(ctx, x, y, s, a = 1) {
  const R = s * 1.78;
  ctx.save();
  // soft light behind the head
  ctx.fillStyle = L.radial(ctx, x, y, s * 0.6, R * 1.25, [[0, rgba('#fff2c8', 0.55 * a)], [0.7, rgba('#ffd884', 0.35 * a)], [1, rgba('#ffd884', 0)]]);
  ctx.beginPath(); ctx.arc(x, y, R * 1.25, 0, L.TAU); ctx.fill();
  // the disc
  ctx.fillStyle = L.radial(ctx, x, y, s * 0.4, R, [[0, rgba('#ffe9a8', 0.3 * a)], [0.85, rgba('#f6c45a', 0.42 * a)], [1, rgba('#e8a838', 0.55 * a)]]);
  ctx.beginPath(); ctx.arc(x, y, R, 0, L.TAU); ctx.fill();
  // ring: dark bronze edge for contrast, gold band, bright inner line
  ctx.strokeStyle = rgba('#7a4a12', 0.75 * a); ctx.lineWidth = s * 0.11;
  ctx.beginPath(); ctx.arc(x, y, R, 0, L.TAU); ctx.stroke();
  ctx.strokeStyle = rgba('#f0b840', 0.95 * a); ctx.lineWidth = s * 0.07;
  ctx.beginPath(); ctx.arc(x, y, R, 0, L.TAU); ctx.stroke();
  ctx.strokeStyle = rgba('#fff4cc', 0.9 * a); ctx.lineWidth = s * 0.022;
  ctx.beginPath(); ctx.arc(x, y, R - s * 0.035, 0, L.TAU); ctx.stroke();
  ctx.restore();
}
function camera(ctx, lt, dur, p, focus = [VW / 2, VH * 0.45]) {
  const z = p.zoom ? lerp(p.zoom[0], p.zoom[1], smooth(lt / Math.max(0.01, dur))) : 1;
  ctx.translate(focus[0], focus[1]); ctx.scale(z, z); ctx.translate(-focus[0], -focus[1]);
}
// ---- legs. Units are head units from the neck base; x points the way the character faces.
function robeShape(ctx, pts, st, Lt, col, shadeFn) {
  const lw = (Lt.lineW || 1) * 0.02;
  ctx.beginPath(); L.crPath(ctx, pts, true, 0.42);
  ctx.fillStyle = L.mul(col, Lt.key || '#fff'); ctx.fill();
  ctx.save(); ctx.clip();
  if (shadeFn) shadeFn();
  ctx.restore();
}
function foot(ctx, X, s, st, Lt, heel, toe, o = {}) {
  // a sandalled foot seen from the side: a leather sole with visible thickness, the foot with its
  // ankle, instep, heel and toes (the big toe in front, the smaller toes stepping back behind it),
  // a toenail, and the straps: a thong from between the toes, a strap over the instep, one round
  // the ankle
  const skin = L.mul(st.skin, Lt.key || '#fff'), skinSh = L.mul(st.skinShadow, Lt.amb || '#fff');
  const H = X(...heel), T = X(...toe);
  const dx = T[0] - H[0], dy = T[1] - H[1], d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d, nx = -uy, ny = ux;
  const up = o.up == null ? -1 : o.up; // which side of the foot faces up on screen
  const h = s * (o.h || 0.32);
  const P = (a, b) => [H[0] + ux * d * a + nx * h * b * up, H[1] + uy * d * a + ny * h * b * up];
  const lw = s * 0.02;
  const leather = L.mul('#5a3a22', Lt.key || '#fff'), leatherD = L.mul('#3a2414', Lt.key || '#fff'), soleEdge = L.mul('#8a6440', Lt.key || '#fff');
  // sole: a thick leather slab under the whole foot
  const sole = [P(-0.06, 0.06), P(0.5, 0.02), P(1.07, 0.04), P(1.09, -0.14), P(0.5, -0.16), P(-0.07, -0.12)];
  ctx.beginPath(); L.crPath(ctx, sole, true, 0.35); ctx.fillStyle = leatherD; ctx.fill();
  ctx.strokeStyle = st.line; ctx.lineWidth = lw * 0.9; ctx.stroke();
  L.strokeSmooth(ctx, [P(-0.04, -0.01), P(0.5, -0.04), P(1.06, -0.02)], rgba(soleEdge, 0.8), lw * 0.9);
  // the foot: heel, ankle, instep, then the big toe with the smaller toes just behind it
  const top = [P(-0.02, 0.06), P(-0.04, 0.42), P(0.06, 0.92), P(0.34, 1.02), P(0.58, 0.72), P(0.8, 0.46),
    P(0.95, 0.34), P(1.05, 0.22), P(1.06, 0.1), P(1.0, 0.05)];
  ctx.beginPath(); L.crPath(ctx, top, true, 0.45); ctx.fillStyle = skin; ctx.fill();
  ctx.save(); ctx.clip();
  // form: the sole side of the foot in shade, a soft light along the instep, the ankle bone
  ctx.fillStyle = rgba(skinSh, 0.5); ctx.beginPath(); ctx.moveTo(...P(-0.1, 0.0)); ctx.lineTo(...P(1.1, 0.0)); ctx.lineTo(...P(1.1, 0.26)); ctx.lineTo(...P(-0.1, 0.36)); ctx.fill();
  const ins = P(0.55, 0.62);
  ctx.fillStyle = L.radial(ctx, ins[0], ins[1], 0, h * 0.6, [[0, rgba('#fff4ea', 0.18)], [1, rgba('#fff4ea', 0)]]);
  ctx.fillRect(ins[0] - h, ins[1] - h, h * 2, h * 2);
  const ank = P(0.18, 0.72);
  ctx.fillStyle = L.radial(ctx, ank[0], ank[1], 0, h * 0.22, [[0, rgba(skinSh, 0.35)], [1, rgba(skinSh, 0)]]);
  ctx.fillRect(ank[0] - h * 0.3, ank[1] - h * 0.3, h * 0.6, h * 0.6);
  // the smaller toes stepping back behind the big toe
  for (const [a, b] of [[0.86, 0.36], [0.8, 0.42]]) L.strokeSmooth(ctx, [P(a, b), P(a + 0.035, b - 0.12), P(a + 0.02, b - 0.26)], rgba(st.line, 0.4), lw * 0.7);
  ctx.restore();
  ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.lineJoin = 'round';
  ctx.beginPath(); L.crPath(ctx, top, true, 0.45); ctx.stroke();
  // big toe: its joint crease and nail
  L.strokeSmooth(ctx, [P(0.93, 0.32), P(0.95, 0.2), P(0.94, 0.08)], rgba(st.line, 0.45), lw * 0.7);
  const n0 = P(0.99, 0.27), n1 = P(1.05, 0.17);
  ctx.strokeStyle = rgba(L.mix(skin, '#fff0ea', 0.5), 0.95); ctx.lineWidth = h * 0.07; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(...n0); ctx.lineTo(...n1); ctx.stroke();
  // straps: a thong from between the toes, over the instep, and round the ankle
  const strap = (pts, w) => { L.strokeSmooth(ctx, pts, leather, w); L.strokeSmooth(ctx, pts, rgba(leatherD, 0.6), w * 0.3); };
  strap([P(0.9, 0.06), P(0.82, 0.4), P(0.62, 0.7)], h * 0.09);
  strap([P(0.48, 0.04), P(0.56, 0.45), P(0.6, 0.76)], h * 0.12);
  strap([P(0.02, 0.62), P(0.2, 0.78), P(0.4, 0.9)], h * 0.1);
  ctx.fillStyle = leatherD; L.ellipse(ctx, ...P(0.6, 0.73), h * 0.07, h * 0.07, 0); ctx.fill();
}
// seated on a low stone ledge: thighs forward under the robe, knees, shins down, feet on the floor
function seatedLegs(ctx, Bn, s, fc, st, Lt, o = {}) {
  const X = (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s];
  const col = st.cloth.tunic, shC = B.clothShadow(col, Lt);
  const side = Lt.side || -1;
  const lw = (Lt.lineW || 1) * s * 0.02;
  const fy = o.floor || 7.25;
  // far leg first (a little higher and further back)
  const leg = (dx, dy, dark) => {
    const Q = (x, y) => X(x + dx, y + dy);
    foot(ctx, Q, s, st, Lt, [2.75, fy - 0.12], [3.95, fy - 0.02]);
    const shin = [Q(2.25, 4.75), Q(3.45, 4.62), Q(3.72, 5.4), Q(3.82, fy - 0.45), Q(3.4, fy - 0.32), Q(2.5, fy - 0.38), Q(2.3, 5.6)];
    ctx.beginPath(); L.crPath(ctx, shin, true, 0.42); ctx.fillStyle = L.mul(col, Lt.key || '#fff'); ctx.fill();
    ctx.save(); ctx.clip();
    ctx.fillStyle = rgba(shC, dark ? 0.7 : 0.25); ctx.fillRect(Bn[0] - 10 * s, Bn[1], 20 * s, 10 * s);
    const g = ctx.createLinearGradient(...Q(3.1, 5.0), ...Q(3.1, fy - 0.3));
    g.addColorStop(0, rgba(shC, 0.55)); g.addColorStop(0.3, rgba(shC, 0)); ctx.fillStyle = g; ctx.fillRect(Bn[0] - 10 * s, Bn[1], 20 * s, 10 * s);
    for (const [a, b] of [[2.7, 3.0], [3.15, 3.45], [3.5, 3.65]]) L.strokeSmooth(ctx, [Q(a, 5.0), Q(b, fy - 0.4)], rgba(shade(col, 0.45), 0.55), lw * 0.8);
    ctx.restore();
    ctx.beginPath(); L.crPath(ctx, shin, true, 0.42); ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.stroke();
  };
  leg(-0.6, -0.1, true);
  leg(0, 0, false);
  // lap: the robe over both thighs, from the hips to the knees
  const lap = [X(-1.95, 4.05), X(-0.4, 3.9), X(1.6, 4.0), X(3.2, 4.12), X(3.62, 4.45), X(3.55, 4.85), X(2.6, 5.05), X(0.4, 5.0), X(-1.9, 4.95)];
  ctx.beginPath(); L.crPath(ctx, lap, true, 0.45);
  ctx.fillStyle = L.mul(col, Lt.key || '#fff'); ctx.fill();
  ctx.save(); ctx.clip();
  const g = ctx.createLinearGradient(...X(1.5, 4.0), ...X(1.5, 5.05));
  g.addColorStop(0, rgba(shC, 0)); g.addColorStop(1, rgba(shC, 0.7)); ctx.fillStyle = g; ctx.fillRect(Bn[0] - 10 * s, Bn[1], 20 * s, 10 * s);
  const gs = ctx.createLinearGradient(...X(-1.0 * side * fc, 4.5), ...X(1.6 * side * fc, 4.5));
  gs.addColorStop(0, rgba(shC, 0)); gs.addColorStop(1, rgba(shC, 0.35)); ctx.fillStyle = gs; ctx.fillRect(Bn[0] - 10 * s, Bn[1], 20 * s, 10 * s);
  for (const [a, b] of [[0.2, 2.8], [0.6, 3.3], [-0.6, 1.6]]) L.strokeSmooth(ctx, [X(a, 4.3), X((a + b) / 2, 4.55), X(b, 4.6)], rgba(shade(col, 0.45), 0.5), lw * 0.8);
  ctx.restore();
  ctx.beginPath(); L.crPath(ctx, lap, true, 0.45); ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.stroke();
}
// the stone ledge a prisoner sits on (drawn before the character)
function stoneBench(ctx, Bn, s, fc, Lt, o = {}) {
  const X = (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s];
  const fy = o.floor || 7.25;
  const a = X(-3.4, 4.6), b = X(2.5, fy);
  const x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]);
  const top = Bn[1] + 4.6 * s, bot = Bn[1] + fy * s;
  ctx.save();
  const base = L.mul('#3a3f48', Lt.amb || '#888');
  ctx.fillStyle = L.linear(ctx, 0, top, 0, bot, [[0, L.mul('#5a606a', Lt.key || '#fff')], [0.12, base], [1, shade(base, 0.6)]]);
  ctx.beginPath(); ctx.roundRect(x0, top, x1 - x0, bot - top, s * 0.12); ctx.fill();
  // block joints and grime
  ctx.strokeStyle = 'rgba(10,10,14,0.55)'; ctx.lineWidth = s * 0.05;
  const mid = (x0 + x1) / 2 + s * 0.4 * fc;
  ctx.beginPath(); ctx.moveTo(mid, top + s * 0.25); ctx.lineTo(mid + s * 0.05, bot); ctx.moveTo(x0, top + (bot - top) * 0.5); ctx.lineTo(x1, top + (bot - top) * 0.52); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(x0 + s * 0.1, top + s * 0.04, x1 - x0 - s * 0.2, s * 0.08);
  for (let i = 0; i < 14; i++) {
    ctx.fillStyle = rgba(i % 3 ? '#0a0806' : '#2a3020', 0.18 + 0.12 * L.hash01(i * 3));
    ctx.beginPath(); ctx.ellipse(x0 + (x1 - x0) * L.hash01(i * 7 + 1), top + (bot - top) * (0.2 + 0.8 * L.hash01(i * 11)), s * (0.15 + 0.35 * L.hash01(i * 5)), s * (0.06 + 0.12 * L.hash01(i * 13)), 0, 0, L.TAU); ctx.fill();
  }
  ctx.strokeStyle = '#0c0d10'; ctx.lineWidth = s * 0.025;
  ctx.beginPath(); ctx.roundRect(x0, top, x1 - x0, bot - top, s * 0.12); ctx.stroke();
  ctx.restore();
}
// Legs from standing (k=0) to kneeling (k=1) as one continuous shape, so kneeling down never pops.
// The torso is drawn to the hips (len 4.2); FY is the floor on screen. Kneeling: thighs down to the
// knees on the floor, shins along the floor behind, toes tucked under.
function legsBlend(ctx, Bn, s, fc, st, Lt, k, FY) {
  const X = (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s];
  const fy = (FY - Bn[1]) / s;
  const col = st.cloth.skirt || mix(st.cloth.tunic, st.cloth.mantle || st.cloth.tunic, 0.2), shC = B.clothShadow(col, Lt);
  const lw = (Lt.lineW || 1) * s * 0.02;
  const kk = smooth(k);
  const P = (a, b) => [lerp(a[0], b[0], kk), lerp(a[1], b[1], kk)];
  const stand = [[-2.0, 4.1], [1.75, 4.15], [1.95, lerp(4.15, fy, 0.5)], [1.95, fy - 0.05], [0.3, fy + 0.05], [-1.9, fy - 0.05], [-2.05, fy - 0.3], [-2.1, lerp(4.1, fy, 0.5)]];
  const kneel = [[-2.0, 4.1], [1.75, 4.15], [2.2, fy - 0.45], [2.0, fy - 0.08], [0.6, fy + 0.02], [-1.45, fy - 0.02], [-2.15, fy - 0.35], [-2.3, 5.6]];
  const robe = stand.map((q, i) => X(...P(q, kneel[i])));
  // feet: under the hem when standing, behind with toes tucked when kneeling
  const f1 = [P([-0.9, fy + 0.02], [-1.55, fy - 0.15]), P([0.35, fy + 0.15], [-2.55, fy - 0.05])];
  const f2 = [P([0.25, fy + 0.1], [-1.1, fy - 0.23]), P([1.45, fy + 0.25], [-2.05, fy - 0.13])];
  if (kk > 0.5) { foot(ctx, X, s, st, Lt, f1[0], f1[1], { h: 0.3 }); foot(ctx, X, s, st, Lt, f2[0], f2[1], { h: 0.3 }); }
  ctx.beginPath(); L.crPath(ctx, robe, true, 0.42);
  ctx.fillStyle = L.mul(col, Lt.key || '#fff'); ctx.fill();
  ctx.save(); ctx.clip();
  const g = ctx.createLinearGradient(...X(0, 4.2), ...X(0, fy));
  g.addColorStop(0, rgba(shC, 0.1)); g.addColorStop(1, rgba(shC, 0.7)); ctx.fillStyle = g; ctx.fillRect(Bn[0] - 10 * s, Bn[1], 20 * s, 14 * s);
  if (kk > 0.3) {
    // soft light on the front of the knee (a gradient, never a hard-edged spot)
    const kp = X(1.55, fy - 0.75);
    ctx.fillStyle = L.radial(ctx, kp[0], kp[1], 0, s * 0.7, [[0, rgba('#ffffff', 0.07 * kk)], [1, rgba('#ffffff', 0)]]);
    ctx.fillRect(kp[0] - s * 0.8, kp[1] - s * 0.8, s * 1.6, s * 1.6);
  }
  for (const [a, b] of [[0.6, 1.6], [-0.2, 1.1], [-1.2, 0.2]]) L.strokeSmooth(ctx, [X(a, 4.4), X((a + b) / 2 + 0.2 * kk, lerp(4.4, fy, 0.5)), X(lerp(a, b, kk), fy - 0.2)], rgba(shade(col, 0.45), 0.5), lw * 0.8);
  ctx.restore();
  ctx.beginPath(); L.crPath(ctx, robe, true, 0.42); ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.stroke();
  if (kk <= 0.5) { foot(ctx, X, s, st, Lt, f1[0], f1[1], { h: 0.34 }); foot(ctx, X, s, st, Lt, f2[0], f2[1], { h: 0.34 }); }
}
function kneelLegs(ctx, Bn, s, fc, st, Lt, o = {}) {
  legsBlend(ctx, Bn, s, fc, st, Lt, 1, Bn[1] + (o.floor || 7.0) * s);
}
function standFeet(ctx, Bn, s, fc, len, Lt, st) {
  const style = st || C.asher;
  const fy = len + 0.25;
  foot(ctx, (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s], s, style, Lt, [-0.9, fy], [0.35, fy + 0.15], { h: 0.34 });
  foot(ctx, (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s], s, style, Lt, [0.25, fy + 0.1], [1.45, fy + 0.25], { h: 0.34 });
}
// a neutral, quietly alive state for an extra (a background figure with no lines): blinks, breath,
// a pose, and a look that can drift
function extraF(t, seed, o = {}) {
  const ph = (t * 0.27 + seed * 0.37) % 1;
  const blink = ph < 0.04 ? Math.sin(ph / 0.04 * Math.PI) : 0;
  const yaw = (o.yaw || 0) + (o.glance ? o.glance * L.noise1(t * 0.35, seed * 7) : 0);
  return Object.assign({
    browInner: 0, browOuter: 0, browHeight: 0, browFurrow: 0.12, browInnerL: 0, browInnerR: 0, browHL: 0, browHR: 0,
    lid: 0.86 * (1 - blink), lidL: 1, lidR: 1, lidLower: 0.1, lidTilt: 0, pupil: 1,
    mouthSmile: -0.05, mouthBase: 0, mouthOpen: 0, mouthWide: 0, mouthPress: 0.2, mouthAsym: 0, mouthTremble: 0,
    cheekRaise: 0, tears: 0, tearFlow: 0, blush: 0, pale: 0, tremble: 0, lean: 0, shoulder: 0,
    gazeX: (o.gx || 0) + yaw * 0.6, gazeY: o.gy || 0, yaw, yawLook: yaw, pitch: o.pitch || 0, roll: 0,
    breathV: Math.sin(t * 1.5 + seed), poseFrom: o.pose || 'default', poseTo: o.pose || 'default', poseK: 1,
  }, o.F || {});
}
// sandalled feet of a figure walking toward the camera, seen from the front: the leading foot lower
// and nearer, the trailing foot higher and mostly under the hem, the swinging foot lifting a little
function frontWalkFeet(ctx, Bn, s, len, Lt, st, ph) {
  const skin = L.mul(st.skin, Lt.key || '#fff'), skinSh = L.mul(st.skinShadow, Lt.amb || '#fff');
  const leather = L.mul('#5a3a22', Lt.key || '#fff'), sole = L.mul('#2e1c10', Lt.key || '#fff');
  const feet = [[-1, ph], [1, ph + Math.PI]].map(([side, p]) => ({ side, fwd: Math.sin(p), lift: Math.max(0, Math.cos(p)) * 0.22 }));
  feet.sort((a, b) => a.fwd - b.fwd);
  for (const f of feet) {
    const k = 0.9 + 0.1 * f.fwd;
    const x = Bn[0] + f.side * 0.62 * s, y = Bn[1] + (len + 0.05 + 0.32 * f.fwd - f.lift) * s;
    const w = 0.42 * s * k, h = 0.55 * s * k;
    // sole, then the foot on it (ankle at the top, toes toward us at the bottom)
    ctx.fillStyle = sole;
    ctx.beginPath(); ctx.ellipse(x, y + h * 0.42, w * 0.62, h * 0.2, 0, 0, L.TAU); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(x - w * 0.3, y - h * 0.5);
    ctx.quadraticCurveTo(x - w * 0.62, y + h * 0.1, x - w * 0.5, y + h * 0.38);
    ctx.quadraticCurveTo(x, y + h * 0.56, x + w * 0.5, y + h * 0.38);
    ctx.quadraticCurveTo(x + w * 0.62, y + h * 0.1, x + w * 0.3, y - h * 0.5);
    ctx.closePath();
    ctx.fillStyle = skin; ctx.fill();
    ctx.save(); ctx.clip();
    ctx.fillStyle = rgba(skinSh, 0.45); ctx.fillRect(x + w * 0.05 * -(Lt.side || -1), y - h, w, h * 2);
    ctx.restore();
    ctx.strokeStyle = st.line; ctx.lineWidth = s * 0.03; ctx.stroke();
    // toes and straps
    for (const u of [-0.18, 0.06, 0.26]) L.strokeSmooth(ctx, [[x + u * w, y + h * 0.3], [x + u * w * 1.05, y + h * 0.42]], rgba(st.line, 0.45), s * 0.02);
    L.strokeSmooth(ctx, [[x - w * 0.5, y + h * 0.05], [x, y + h * 0.14], [x + w * 0.5, y + h * 0.05]], leather, s * 0.06);
    L.strokeSmooth(ctx, [[x - w * 0.28, y + h * 0.4], [x - w * 0.1, y + h * 0.12]], leather, s * 0.045);
  }
}
function floorShadow(ctx, x, y, w, a = 0.45) {
  ctx.fillStyle = L.radial(ctx, x, y, 0, w, [[0, rgba('#000000', a)], [1, rgba('#000000', 0)]]);
  ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.2); ctx.translate(-x, -y);
  ctx.fillRect(x - w, y - w, w * 2, w * 2); ctx.restore();
}

// ================================================================== SHOTS
const S = {};

// ---------------------------------------------------------- PROLOGUE
S.upper_jesus = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 820]);
  drawCached(ctx, bgView('upper', (x) => BG.upperRoom(x, { tableY: 1560 }), { z: 1.15, cx: 540, cy: 900 }, 7));
  BG.upperRoomDyn(ctx, t, { tableY: 1560 });
  const lk = looks({ gx: 0, gy: 0.1, yaw: 0.05, pitch: 0.05 }, {
    bread: { gx: 0.05, gy: 0.95, yaw: 0.05, pitch: 0.3 }, cam: { gx: -0.05, gy: 0.0, yaw: 0.06, pitch: 0.02 },
    cam_l: { gx: -0.55, gy: 0.05, yaw: -0.2, pitch: 0.03 },
  });
  // table behind the hands
  ctx.fillStyle = L.linear(ctx, 0, 1640, 0, VH, [[0, '#6a3e1e'], [1, '#2a160a']]);
  ctx.fillRect(0, 1640, VW, VH);
  ctx.fillStyle = rgba('#ffcf8a', 0.3); ctx.fillRect(0, 1640, VW, 8);
  B.drawCup(ctx, 930, 1680, 70, LIGHT.lamp);
  actor(ctx, W, 'jesus', t, { x: 540, y: 1150, s: 170, facing: 1, by: 0.05, len: 3.4 }, LIGHT.lamp, lk);
};

S.upper_hands = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('upper', (x) => BG.upperRoom(x, { tableY: 1560 }), { z: 1.5, cx: 540, cy: 1250 }, 12));
  BG.upperRoomDyn(ctx, t, { tableY: 1500 });
  const Lt = LIGHT.lamp;
  ctx.fillStyle = L.linear(ctx, 0, 1250, 0, VH, [[0, '#6a3e20'], [1, '#2a160a']]);
  ctx.fillRect(0, 1250, VW, VH);
  bokehTable(ctx);
  const k = smooth(lt / 2.4);
  // Jesus' hand from the right offers a morsel on His open palm; a hand in a dark sleeve reaches in from the left
  const wJ = [lerp(760, 700, k), lerp(900, 880, k)];
  const k2 = smooth((lt - 0.5) / 2.2);
  const wD = [lerp(-120, 215, k2), lerp(1150, 1080, k2)];
  closeArm(ctx, [-380, 1380], wD, 215, { skin: '#d8a888', skinShadow: '#9a6a58', line: '#2a1a14', cloth: { tunic: '#2a2228' } }, Lt,
    { hand: 'cup', f: [0.85, 0.33, 0.25], n: [-0.15, 0.6, 0.8], right: true, sleeve: '#2a2228' });
  // seen from a little above the table, so both open palms read clearly (thumbs on the near side)
  closeArm(ctx, [1380, 640], wJ, 215, C.jesus, Lt, {
    hand: 'offer', f: [-0.95, -0.1, 0.25], n: [0, 0.6, 0.8], right: false, sleeve: C.jesus.cloth.tunic, loose: 1,
    prop: { depth: -999, draw: () => {} },
    after: null,
  });
  // the morsel rests on His open palm
  B.drawHalfBread(ctx, wJ[0] - 150, wJ[1] - 70, 78, Lt, { face: 1, rot: -0.12 });
  BG.vignette(ctx, 0.5);
};
function bokehTable(ctx) { BG.bokeh(ctx, [[160, 1180, 80], [900, 1120, 110], [520, 1300, 60]], '#ffb35a', 0.3); }

S.upper_jesus_door = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 820]);
  drawCached(ctx, bgView('upper', (x) => BG.upperRoom(x, { tableY: 1560 }), { z: 1.4, cx: 300, cy: 700 }, 10));
  BG.upperRoomDyn(ctx, t, { tableY: 1560 });
  const lk = looks({ gx: -0.6, gy: 0.05, yaw: -0.38, pitch: 0.02 }, {
    door: { gx: -0.75, gy: 0.0, yaw: -0.4, pitch: 0.0 }, door_down: { gx: -0.6, gy: 0.45, yaw: -0.36, pitch: 0.16 },
  });
  // a single tear as He watches the door Judas has gone through: it wells, rolls, and dries
  actor(ctx, W, 'jesus', t, { x: 560, y: 1290, s: 200, facing: -1, by: -0.2, len: 5 }, LIGHT.lampR, lk, {
    mod: (F) => {
      F.tearSide = 1;
      F.tearDrop = lt < 0.9 ? -1 + smooth((lt - 0.3) / 0.6) : smooth((lt - 0.9) / 1.6);
      F.tearTrail = 1 - smooth((lt - 2.4) / 0.9);
      F.tears = 0.25 * (1 - smooth((lt - 2.2) / 1.0)) * smooth((lt - 0.2) / 0.5);
    },
  });
  BG.vignette(ctx, 0.35);
};

// ---------------------------------------------------------- ACT 1 STREET
S.street_wide = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.04] }, [540, 1000]);
  drawCached(ctx, cached('street', (x) => BG.streetNight(x)));
  BG.streetNightDyn(ctx, t);
  // Asher from behind, silhouette with torch rim
  const st = C.asher;
  const x0 = 760, y0 = 1080;
  floorShadow(ctx, x0, 1750, 240, 0.6);
  ctx.save();
  const f = 0.85 + 0.15 * L.fbm1(t * 3.3, 2);
  const sil = { key: mix('#9a7a6a', '#b08a72', f), amb: '#3a3e5a', side: -1, shadow: 0.8, rim: '#ffb070', rimA: 0.75, rimSide: -1, wrap: 0.45 };
  const lk = looks({ gx: -0.6, gy: -0.1, yaw: -0.55, pitch: -0.05 }, { door: { gx: -0.65, gy: -0.15, yaw: -0.55, pitch: -0.06 } });
  actor(ctx, W, 'asher', t, { x: x0, y: y0, s: 70, facing: -1, by: -0.5, len: 9.2 }, sil, lk);
  standFeet(ctx, [x0, y0], 70, -1, 9.2, sil);
  ctx.restore();
};

S.street_asher_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 850]);
  drawCached(ctx, bgView('street', (x) => BG.streetNight(x), { z: 1.8, cx: 360, cy: 800 }, 14));
  const f = 0.85 + 0.15 * L.fbm1(t * 3.3, 2);
  const Lt = Object.assign({}, LIGHT.street, { key: mix('#ffb070', '#ffe0c0', f * 0.6) });
  const lk = looks({ gx: -0.4, gy: -0.15, yaw: -0.3, pitch: -0.08 }, {
    door: { gx: -0.35, gy: -0.25, yaw: -0.26, pitch: -0.1 }, door_low: { gx: -0.2, gy: 0.3, yaw: -0.2, pitch: 0.08 },
    bread: { gx: -0.05, gy: 0.9, yaw: -0.12, pitch: 0.28 }, down: { gx: 0, gy: 0.8, yaw: -0.1, pitch: 0.25 },
  });
  actor(ctx, W, 'asher', t, { x: 560, y: 1300, s: 185, facing: -1, by: -0.25, len: 5 }, Lt, lk);
  // torch glow from left
  L.glow(ctx, -60, 700, 700, '#ff8a30', 0.25 * f);
  BG.vignette(ctx, 0.45, '#02030a');
};

S.church_reader = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.03] }, [540, 900]);
  drawCached(ctx, cached('church', (x) => BG.houseChurch(x, { lampX: 620, lampY: 980 }), 0));
  const Lt = LIGHT.church;
  // background listeners
  BG.silhouettes(ctx, [[120, 980, 70], [300, 1010, 64], [980, 990, 72]], '#1a0e08', '#ffb060', 0.35, t);
  // Phoebe reading Paul's letter, scroll in hands
  const lk = looks({ gx: 0.0, gy: 0.75, yaw: 0.25, pitch: 0.22 }, { scroll: { gx: 0.0, gy: 0.8, yaw: 0.25, pitch: 0.24 } });
  actor(ctx, W, 'phoebe', t, { x: 560, y: 1140, s: 120, facing: 1, by: 0.3, len: 6 }, Lt, lk, { mod: (F) => { F.pose = 'scroll'; F.poseTo = 'scroll'; F.poseFrom = 'scroll'; F.poseK = 1; } });
  // lamp on table
  B.drawFlame(ctx, 620, 1520, 24, t, 2);
  L.glow(ctx, 620, 1500, 300, '#ffb050', 0.35);
  // foreground listeners (backs)
  BG.silhouettes(ctx, [[160, 1560, 120, 0.4], [900, 1600, 130, -0.4]], '#0c0604', '#ffb060', 0.45, t);
};

S.church_asher = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 860]);
  drawCached(ctx, bgView('church', (x) => BG.houseChurch(x, { lampX: 620, lampY: 980 }), { z: 1.6, cx: 540, cy: 900 }, 14));
  BG.silhouettes(ctx, [[120, 760, 90], [960, 800, 96]], '#1a0e08', '#ffb060', 0.25, t);
  const lk = looks({ gx: 0.45, gy: -0.05, yaw: 0.28, pitch: -0.02 }, {
    reader: { gx: 0.5, gy: -0.05, yaw: 0.3, pitch: -0.03 }, down: { gx: 0.1, gy: 0.85, yaw: 0.12, pitch: 0.24 },
  });
  actor(ctx, W, 'asher', t, { x: 520, y: 1300, s: 180, facing: 1, by: 0.25, len: 5 }, LIGHT.church, lk);
  BG.silhouettes(ctx, [[60, 1500, 150, 0.3], [1010, 1480, 140, -0.3]], '#0a0503', '#ffb060', 0.3, t);
};

S.street_knock = (ctx, W, t, lt, dur, p) => {
  // door close-up: each knock shudders the frame and shakes dust loose; then the grille opens on a pair of eyes
  const kn = [0.3, 0.75, 1.2];
  let hit = 0;
  for (const k of kn) { const d = lt - k; if (d >= 0 && d < 0.25) hit = Math.max(hit, 1 - d / 0.25); }
  ctx.save();
  ctx.translate(Math.sin(lt * 90) * 5 * hit, Math.cos(lt * 70) * 3 * hit);
  drawCached(ctx, bgView('street', (x) => BG.streetNight(x), { z: 3.0, cx: 540, cy: 760 }, 0));
  // grille slot sliding open (after the knocks)
  const op = smooth((lt - 1.6) / 0.35);
  const gx = 540, gy = 880;
  ctx.fillStyle = '#050403'; ctx.fillRect(gx - 175, gy - 105, 350, 210);
  if (op > 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(gx - 175, gy - 105, 350 * op, 210); ctx.clip();
    // torchlit eyes of the guard inside
    ctx.fillStyle = '#1a0e08'; ctx.fillRect(gx - 175, gy - 105, 350, 210);
    const Lt = { side: 1, key: '#ffb070', amb: '#3a2a3a', shadow: 0.8, wrap: 0.6 };
    const F = W.state('guard', t, { default: { gx: 0.05, gy: 0.05, yaw: 0.05, pitch: 0.02 } });
    drawHead(ctx, { x: gx + 10, y: gy + 25, s: 230, yaw: 0.05, pitch: 0.02, roll: 0 }, C.guard, Object.assign({}, F, { mouthOpen: 0 }), Lt, { t });
    ctx.restore();
  }
  // slot cover (iron plate sliding right)
  ctx.fillStyle = L.linear(ctx, 0, gy - 105, 0, gy + 105, [[0, '#2c2c30'], [1, '#18181c']]);
  ctx.fillRect(gx - 175 + 350 * op, gy - 105, 350, 210);
  ctx.strokeStyle = '#0c0c0e'; ctx.lineWidth = 10; ctx.strokeRect(gx - 180, gy - 110, 360, 220);
  ctx.restore();
  // dust shaken loose
  for (let i = 0; i < 26; i++) {
    const k = kn[i % 3], tt = lt - k - L.hash01(i) * 0.1;
    if (tt < 0 || tt > 1.6) continue;
    const x = 200 + L.hash01(i * 7) * 680, y = 300 + tt * tt * 700 + L.hash01(i * 3) * 80;
    ctx.fillStyle = rgba('#d8c8a8', 0.6 * (1 - tt / 1.6));
    ctx.beginPath(); ctx.arc(x, y, 2 + 2 * L.hash01(i * 5), 0, L.TAU); ctx.fill();
  }
  const f = 0.85 + 0.15 * L.fbm1(t * 3.3, 2);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, -100, 600, 800, '#ff8a30', 0.28 * f);
  ctx.restore();
  BG.vignette(ctx, 0.55, '#02030a');
};

// forearm + hand for extreme close-ups. o: { hand: preset, f: finger dir (world, y up), n: palm normal,
// right: which hand, sleeve, shackle, prop: { depth, draw } drawn between the hand's back and front }
function closeArm(ctx, E, Wr, s, st, Lt, o = {}) {
  const H = require('./hands');
  const dx = Wr[0] - E[0], dy = Wr[1] - E[1], d = Math.hypot(dx, dy) || 1;
  const dir = [dx / d, dy / d];
  const C = [Wr[0] - dir[0] * s * 0.16, Wr[1] - dir[1] * s * 0.16];
  const g = { S: E, E, W: Wr, C, dir, rS: 0.5 * s, rE: 0.45 * s, rC: (0.38 + 0.14 * (o.loose || 0)) * s, cap: 0.01, s, ang: Math.atan2(dir[1], dir[0]) };
  const f = o.f || [dir[0], -dir[1], 0];
  const h = H.handParts(Wr, s, st, Lt, { f, n: o.n || [0, 0, 1], right: o.right !== false, shape: H.preset(o.hand || 'relax') });
  H.drawWrist(ctx, Wr, dir, s, st, Lt);
  B.drawSleeve(ctx, g, st, Lt, { part: 'lower', sleeve: o.sleeve });
  if (o.shackle) B.drawShackle(ctx, Wr, g.ang, s, Lt);
  if (o.defer) return h;
  if (o.prop) {
    h.draw(ctx, (p) => p.depth < o.prop.depth);
    o.prop.draw(h);
    h.draw(ctx, (p) => p.depth >= o.prop.depth);
  } else h.draw(ctx);
  return h;
}

S.street_door_guard = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('street', (x) => BG.streetNight(x), { z: 1.7, cx: 540, cy: 900 }, 4));
  // door opening reveals interior darkness + guard
  const open = smooth(lt / 0.9);
  ctx.fillStyle = '#050403';
  ctx.fillRect(340, 330, 400 * open + 10, 1500);
  const lk = looks({ gx: 0.4, gy: 0.15, yaw: 0.25, pitch: 0.08 }, { asher: { gx: 0.45, gy: 0.2, yaw: 0.28, pitch: 0.1 } });
  ctx.save();
  ctx.beginPath(); ctx.rect(330, 300, 420 * open + 20, 1700); ctx.clip();
  const f = 0.85 + 0.15 * L.fbm1(t * 3, 6);
  const Lt = { side: 1, key: mix('#ffb070', '#ffd8b0', f), amb: '#4a3a5a', shadow: 0.8, rim: '#a8c0ff', rimA: 0.3, rimSide: -1, wrap: 0.6 };
  actor(ctx, W, 'guard', t, { x: 520, y: 1250, s: 150, facing: 1, by: 0.3, len: 5 }, Lt, lk);
  B.drawTorch(ctx, 760, 1080, 40, t, Lt, { size: 1.2, seed: 3 });
  ctx.restore();
  // door leaf
  ctx.fillStyle = L.linear(ctx, 0, 0, 400, 0, [[0, '#3a2416'], [1, '#22140a']]);
  ctx.fillRect(330 + 420 * open, 300, 420 * (1 - open) + 300, 1700);
  BG.vignette(ctx, 0.5, '#02030a');
};

// ---------------------------------------------------------- CELL
const cellPaul = { x: 300, y: 1130, s: 92, facing: 1, by: 0.35, len: 4.4 };
function cellBG(view, blur, opt = {}) {
  return bgView('cell' + JSON.stringify(opt), (x) => BG.cell(x, opt), view, blur);
}
function cellDynView(ctx, t, view, opt = {}) {
  ctx.save();
  ctx.translate(VW / 2, VH / 2); ctx.scale(view.z, view.z); ctx.translate(-view.cx, -view.cy);
  BG.cellDyn(ctx, t, opt);
  ctx.restore();
}
const paulLook = (ex) => looks({ gx: 0.45, gy: -0.35, yaw: 0.3, pitch: -0.1 }, Object.assign({
  parchment: { gx: 0.25, gy: 0.9, yaw: 0.2, pitch: 0.3 }, door: { gx: 0.75, gy: -0.25, yaw: 0.42, pitch: -0.08 },
  asher: { gx: 0.5, gy: -0.45, yaw: 0.32, pitch: -0.14 }, bread: { gx: 0.35, gy: 0.75, yaw: 0.25, pitch: 0.22 },
  down: { gx: 0.1, gy: 0.85, yaw: 0.18, pitch: 0.26 }, far: { gx: 0.05, gy: -0.1, yaw: 0.12, pitch: -0.05 },
  hands: { gx: 0.15, gy: 0.95, yaw: 0.12, pitch: 0.3 }, guard: { gx: 0.85, gy: -0.3, yaw: 0.5, pitch: -0.1 },
  away: { gx: -0.5, gy: 0.2, yaw: -0.1, pitch: 0.05 },
}, ex || {}));
const asherLook = (ex) => looks({ gx: -0.4, gy: 0.35, yaw: -0.3, pitch: 0.12 }, Object.assign({
  paul: { gx: -0.45, gy: 0.4, yaw: -0.32, pitch: 0.14 }, bread: { gx: -0.2, gy: 0.9, yaw: -0.2, pitch: 0.3 },
  away: { gx: 0.55, gy: 0.1, yaw: 0.25, pitch: 0.02 }, away_down: { gx: 0.45, gy: 0.7, yaw: 0.2, pitch: 0.22 },
  guard: { gx: 0.75, gy: -0.1, yaw: 0.4, pitch: -0.03 }, down: { gx: -0.1, gy: 0.85, yaw: -0.15, pitch: 0.26 },
}, ex || {}));

S.cell_wide = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.0, cx: 540, cy: 960 };
  drawCached(ctx, cellBG(view, 0));
  // door opening light
  const op = smooth(lt / 1.2);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#ffb070', 0.35 * op);
  ctx.beginPath(); ctx.moveTo(800, 500); ctx.lineTo(1080, 500); ctx.lineTo(1080, 1900); ctx.lineTo(600, 1900); ctx.closePath(); ctx.fill();
  ctx.restore();
  BG.cellDyn(ctx, t, {});
  // Asher silhouette in doorway
  const sil = { side: 1, key: '#2a2a36', amb: '#101018', shadow: 0.9, rim: '#ffb070', rimA: 0.7 * op, rimSide: 1, wrap: 0.2 };
  // he stands on the threshold: the robe reaches down to his sandalled feet
  ctx.save(); ctx.globalAlpha = op;
  floorShadow(ctx, 905, 1485, 90, 0.5);
  actor(ctx, W, 'asher', t, { x: 900, y: 700, s: 56, facing: -1, by: -0.4, len: 13.6 }, sil, asherLook(),
    { afterTorso: (o) => standFeet(ctx, o.neck, o.s, -1, 13.6, sil, C.asher) });
  ctx.restore();
  // Paul seated
  floorShadow(ctx, 330, 1560, 260, 0.5);
  B.drawChain(ctx, [150, 1150], [210, 1520], 30, LIGHT.cellL, 2.5, 12);
  const pl = Object.assign({}, cellPaul);
  stoneBench(ctx, [pl.x, pl.y], pl.s, 1, LIGHT.cellL);
  actor(ctx, W, 'paul', t, pl, LIGHT.cellL, paulLook(), { afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, LIGHT.cellL) });
};

S.cell_paul_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [520, 820]);
  const view = { z: 2.2, cx: 300, cy: 760 };
  drawCached(ctx, cellBG(view, 12));
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 60, 300, 700, '#c8d8ff', 0.18);
  ctx.restore();
  const warm = W.tl && p.warm ? 1 : 0;
  actor(ctx, W, 'paul', t, { x: 500, y: 1300, s: 190, facing: 1, by: 0.3, len: 5 }, LIGHT.cellL, paulLook());
  BG.dust(ctx, t, { x: 0, y: 0, w: 500, h: 1400 }, 8, '#e8f0ff', 11, 0.35, 3);
  BG.vignette(ctx, 0.4, '#020305');
};

S.cell_paul_ecu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.06] }, [540, 800]);
  drawCached(ctx, cellBG({ z: 3.0, cx: 300, cy: 700 }, 16));
  actor(ctx, W, 'paul', t, { x: 520, y: 2050, s: 470, facing: 1, by: 0.3, len: 3 }, LIGHT.cellL, paulLook(), { });
  BG.vignette(ctx, 0.55, '#020305');
};

S.cell_asher_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 820]);
  const F = W.state('asher', t, asherLook());
  const kneel = /kneel/.test(F.poseTo) ? 1 : 0;
  const view = kneel ? { z: 2.0, cx: 760, cy: 1100 } : { z: 2.0, cx: 760, cy: 560 };
  drawCached(ctx, cellBG(view, 12));
  cellDynView(ctx, t, view, {});
  actor(ctx, W, 'asher', t, { x: 560, y: 1310, s: 185, facing: -1, by: -0.45, len: 5, lean: 0.03 }, LIGHT.cellR, asherLook(), {});
  BG.vignette(ctx, 0.4, '#020305');
};

function twoShot(ctx, W, t, lt, dur, p, warmK = 0) {
  const view = { z: 1.25, cx: 540, cy: 1000 };
  drawCached(ctx, cellBG(view, 4));
  cellDynView(ctx, t, view, { shaftA: 0.22 + warmK * 0.25, shaftColor: warmK > 0 ? '#fff0d0' : '#cfe0ff' });
  const Lp = warmK > 0 ? LIGHT.cellWarm : LIGHT.cellL;
  const FA = W.state('asher', t, asherLook());
  const kf = /kneel/.test(FA.poseFrom) ? 1 : 0, kt = /kneel/.test(FA.poseTo) ? 1 : 0;
  const kneel = lerp(kf, kt, smooth(FA.poseK));
  // Paul low-left, on the stone ledge
  floorShadow(ctx, 360, 1860, 300, 0.5);
  B.drawChain(ctx, [100, 1080], [250, 1560], 32, Lp, 2.5, 12);
  const pPaul = { x: 270, y: 1150, s: 100, facing: 1, by: 0.35, len: 4.4 };
  stoneBench(ctx, [pPaul.x, pPaul.y], pPaul.s, 1, Lp);
  actor(ctx, W, 'paul', t, pPaul, Lp, paulLook({ asher: { gx: 0.55, gy: lerp(-0.6, -0.1, kneel), yaw: 0.35, pitch: lerp(-0.18, -0.02, kneel) } }),
    { afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, Lp) });
  // Asher right: standing or kneeling, well clear of Paul's feet
  const FY = 1850;
  const pA = { x: 850, y: lerp(FY - 9.65 * 92, FY - 7.0 * 92, smooth(kneel)), s: 92, facing: -1, by: -0.45, len: 4.2 };
  floorShadow(ctx, 850, FY, 220, 0.45);
  actor(ctx, W, 'asher', t, pA, Lp, asherLook({ paul: { gx: -0.5, gy: lerp(0.6, 0.15, kneel), yaw: -0.35, pitch: lerp(0.2, 0.04, kneel) } }),
    { afterTorso: (o) => legsBlend(ctx, o.neck, o.s, -1, C.asher, Lp, kneel, FY) });
  // dropped bread on floor
  if (p.breadOnFloor !== false) {
    const fa = W.state('asher', t, asherLook());
    const dropped = fa.poseTo === 'drop_bread' ? smooth((fa.poseK - 0.3) / 0.7) : (['hold', 'default'].includes(fa.poseTo) ? 0 : 1);
    if (dropped > 0) {
      const y = lerp(1100, 1600, Math.min(1, dropped * 1.2));
      B.drawBread(ctx, 600, y, 70, Lp, { rot: 0.1 });
      B.drawJar(ctx, 700, 1640, 90, Lp);
    }
  }
  BG.vignette(ctx, 0.45, '#020305');
}
S.cell_two = (ctx, W, t, lt, dur, p) => twoShot(ctx, W, t, lt, dur, p, 0);
S.cell_two_light = (ctx, W, t, lt, dur, p) => {
  twoShot(ctx, W, t, lt, dur, Object.assign({ breadOnFloor: false }, p), smooth(lt / 3));
  ctx.save(); ctx.globalCompositeOperation = 'soft-light';
  ctx.fillStyle = rgba('#ffd8a0', 0.35 * smooth(lt / 3)); ctx.fillRect(0, 0, VW, VH);
  ctx.restore();
};

S.cell_memory = (ctx, W, t, lt, dur, p) => {
  S.cell_asher_cu(ctx, W, t, lt, dur, { zoom: [1.04, 1.1] });
  // ghost overlays: Yosef then Jesus
  const ghost = (who, a, x, y, s, look, Lt) => {
    if (a <= 0.01) return;
    const R = global.RENDER_SCALE || 1;
    const c = createCanvas(Math.round(VW * R), Math.round(VH * R));
    const g = c.getContext('2d'); g.scale(R, R);
    actor(g, W, who, t, { x, y, s, facing: 1, by: 0, len: 4, headOnly: false }, Lt, look, { noTag: true });
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = a * 0.55; ctx.globalCompositeOperation = 'screen'; ctx.filter = `blur(${2 * R}px)`;
    ctx.drawImage(c, 0, 0); ctx.restore();
  };
  const sh = W.tl.shots.find((x) => x.id === 'cell_memory');
  const ln = W.tl.lines.find((l) => l.who === 'jesus' && l.start >= sh.start - 0.1 && l.start < sh.end);
  const t0 = ln ? ln.start : sh.start, t1 = ln ? ln.end : sh.end;
  ghost('jesus', clamp(Math.min((t - t0 + 0.8) / 0.8, (t1 + 1.0 - t) / 0.9)), 700, 660, 140, looks({ gx: -0.2, gy: 0.2, yaw: -0.15, pitch: 0.05 }), LIGHT.lamp);
};

S.cell_kneel = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.6, cx: 720, cy: 1100 };
  drawCached(ctx, cellBG(view, 8));
  cellDynView(ctx, t, view, {});
  const k = smooth(lt / 2.2);
  const FY = 1730;
  const pA = { x: 560, y: lerp(FY - 9.65 * 120, FY - 7.0 * 120, k), s: 120, facing: -1, by: -0.4, len: 4.2 };
  floorShadow(ctx, 560, FY, 300, 0.5);
  B.drawBread(ctx, 330, FY - 25, 90, LIGHT.cellR, { rot: 0.1 });
  actor(ctx, W, 'asher', t, pA, LIGHT.cellR, asherLook({ bread: { gx: -0.3, gy: 0.95, yaw: -0.22, pitch: 0.35 } }),
    { afterTorso: (o) => legsBlend(ctx, o.neck, o.s, -1, C.asher, LIGHT.cellR, k, FY) });
  BG.vignette(ctx, 0.45, '#020305');
};

S.cell_break_insert = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, cellBG({ z: 2.6, cx: 560, cy: 1500 }, 16));
  const Lt = LIGHT.cellWarm;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 540, 700, 800, '#ffe8c0', 0.25 * smooth(lt / 2));
  ctx.restore();
  const st = C.asher;
  const br = smooth((lt - 0.9) / 0.5);
  const sep = br * 150;
  const cy = 960 - smooth(lt / 1.0) * 60;
  const R0 = 250;
  // each hand holds an end of the loaf: palm against the end, fingers wrapped round behind it, thumb
  // over the top pressing toward the middle. As the loaf tears the hands roll outward.
  const Hm = require('./hands');
  const tw = 0.4 * br;
  const fL = Hm.V.norm([0.12 - tw * 0.5, 0.66, -0.74]), nL = Hm.V.norm([1, -0.12 - tw * 0.6, -0.32]);
  const hL = closeArm(ctx, [-260, cy + 900], [236 - sep * 0.9, cy + 95 + 20 * br], 230, st, Lt,
    { hand: 'hold', f: fL, n: nL, right: false, defer: true });
  const hR = closeArm(ctx, [1340, cy + 900], [844 + sep * 0.9, cy + 95 + 20 * br], 230, st, Lt,
    { hand: 'hold', f: [-fL[0], fL[1], fL[2]], n: [-nL[0], nL[1], nL[2]], right: true, defer: true });
  hL.draw(ctx, (q) => q.kind !== 'thumb'); hR.draw(ctx, (q) => q.kind !== 'thumb');
  if (br < 0.05) B.drawBread(ctx, 540, cy, R0, Lt, { rot: 0.0 });
  else {
    B.drawHalfBread(ctx, 470 - sep, cy, R0 * 0.92, Lt, { face: 1, rot: -0.15 * br });
    B.drawHalfBread(ctx, 610 + sep, cy, R0 * 0.92, Lt, { face: -1, rot: 0.15 * br });
  }
  hL.draw(ctx, (q) => q.kind === 'thumb'); hR.draw(ctx, (q) => q.kind === 'thumb');
  if (br >= 0.05) {
    for (let i = 0; i < 18; i++) {
      const tt = lt - 1.0 - L.hash01(i) * 0.3;
      if (tt < 0) continue;
      const x = 540 + L.hash(i * 7) * 120 + L.hash(i * 3) * tt * 80, y = cy + tt * tt * 900 + L.hash(i * 5) * 20;
      if (y > VH) continue;
      ctx.fillStyle = rgba(i % 2 ? '#e8cfa0' : '#b87a3a', 0.9);
      ctx.beginPath(); ctx.arc(x, y, 5 + 6 * L.hash01(i * 11), 0, L.TAU); ctx.fill();
    }
  }
  BG.dust(ctx, t, { x: 100, y: 200, w: 880, h: 1400 }, 20, '#fff0d0', 21, 0.35, 3);
  BG.vignette(ctx, 0.5, '#020305');
};

S.cell_offer = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.45, cx: 520, cy: 1060 };
  drawCached(ctx, cellBG(view, 7));
  cellDynView(ctx, t, view, { shaftA: 0.3 });
  const Lt = LIGHT.cellL;
  B.drawChain(ctx, [60, 840], [240, 1400], 34, Lt, 2.5, 12);
  const pPaul = { x: 280, y: 900, s: 118, facing: 1, by: 0.35, len: 4.4 };
  stoneBench(ctx, [pPaul.x, pPaul.y], pPaul.s, 1, Lt);
  actor(ctx, W, 'paul', t, pPaul, Lt, paulLook({ asher: { gx: 0.55, gy: -0.05, yaw: 0.35, pitch: -0.02 }, bread: { gx: 0.5, gy: 0.5, yaw: 0.3, pitch: 0.12 } }),
    { afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, Lt) });
  const pA = { x: 840, y: 1745 - 7.0 * 112, s: 112, facing: -1, by: -0.45, len: 4.2 };
  actor(ctx, W, 'asher', t, pA, Lt, asherLook({ paul: { gx: -0.55, gy: 0.1, yaw: -0.35, pitch: 0.02 } }),
    { afterTorso: (o) => kneelLegs(ctx, o.neck, o.s, -1, C.asher, Lt) });
  BG.vignette(ctx, 0.45, '#020305');
};

S.cell_door_guard = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.7, cx: 900, cy: 900 };
  drawCached(ctx, cellBG(view, 5));
  const open = smooth(lt / 0.5);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#ff9a50', 0.3 * open); ctx.fillRect(250, 0, 600, VH);
  ctx.restore();
  const f = 0.85 + 0.15 * L.fbm1(t * 3, 6);
  const Lt = { side: 1, key: mix('#ffb070', '#ffd8b0', f), amb: '#4a3a5a', shadow: 0.8, rim: '#ffb070', rimA: 0.4, rimSide: -1, wrap: 0.6 };
  const lk = looks({ gx: -0.4, gy: 0.4, yaw: -0.3, pitch: 0.15 }, { paul: { gx: -0.5, gy: 0.5, yaw: -0.32, pitch: 0.18 } });
  actor(ctx, W, 'guard', t, { x: 540, y: 1250, s: 150, facing: -1, by: -0.3, len: 6 }, Lt, lk);
  B.drawTorch(ctx, 830, 1100, 40, t, Lt, { size: 1.2, seed: 5 });
  BG.vignette(ctx, 0.5, '#020305');
};

S.cell_hands_grip = (ctx, W, t, lt, dur, p) => {
  // tight two-shot at eye level: Paul reaches across and grips Asher's hands
  const view = { z: 1.9, cx: 560, cy: 1120 };
  drawCached(ctx, cellBG(view, 9));
  cellDynView(ctx, t, view, { shaftA: 0.3 });
  const Lt = LIGHT.cellWarm;
  const pA = { x: 875, y: 1150, s: 122, facing: -1, by: -0.4, len: 4.2 };
  const pPaul = { x: 215, y: 1170, s: 128, facing: 1, by: 0.4, len: 4.4 };
  stoneBench(ctx, [pPaul.x, pPaul.y], pPaul.s, 1, Lt);
  actor(ctx, W, 'paul', t, pPaul, Lt, paulLook({ asher: { gx: 0.62, gy: 0.0, yaw: 0.42, pitch: 0.0 } }), {
    mod: (F) => { F.poseFrom = 'rest'; F.poseTo = 'grip'; F.poseK = smooth(lt / 1.2); },
    afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, Lt),
  });
  actor(ctx, W, 'asher', t, pA, Lt, asherLook({ paul: { gx: -0.62, gy: 0.05, yaw: -0.42, pitch: 0.02 } }), {
    mod: (F) => { F.poseFrom = 'kneel'; F.poseTo = 'kneel'; F.poseK = 1; },
    afterTorso: (o) => kneelLegs(ctx, o.neck, o.s, -1, C.asher, Lt),
  });
  BG.vignette(ctx, 0.45, '#020305');
};

S.cell_window = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.08] }, [400, 600]);
  drawCached(ctx, cellBG({ z: 1.5, cx: 380, cy: 700 }, 2, { lamp: false, door: false, winX: 380, winY: 520 }));
  cellDynView(ctx, t, { z: 1.5, cx: 380, cy: 700 }, { lamp: false, winX: 380, winY: 520, shaftA: 0.4, shaftX: 620, shaftY: 1900 });
  B.drawChain(ctx, [700, 1250], [920, 1900], 40, LIGHT.cellL, 3, 12);
  BG.vignette(ctx, 0.4, '#020305');
};

// ---------------------------------------------------------- JERUSALEM
function doorPlanks(ctx, x0, x1, t, lit = 1) {
  // dark wooden door planks with grain, catching torchlight on the edge nearest the gap
  ctx.fillStyle = L.linear(ctx, x0, 0, x1, 0, [[0, '#1c120c'], [1, '#2e1e12']]);
  ctx.fillRect(x0, 0, x1 - x0, VH);
  ctx.strokeStyle = rgba('#120a06', 0.9); ctx.lineWidth = 7;
  for (let x = x0 + 70; x < x1; x += 120) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + 6, VH); ctx.stroke(); }
  ctx.strokeStyle = rgba('#3a2818', 0.6); ctx.lineWidth = 3;
  for (let i = 0; i < 14; i++) {
    const x = x0 + 20 + ((i * 53) % Math.max(40, x1 - x0 - 40));
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.bezierCurveTo(x + 14, VH * 0.3, x - 10, VH * 0.6, x + 8, VH); ctx.stroke();
  }
  ctx.fillStyle = '#141416'; // iron band
  ctx.fillRect(x0, 520, x1 - x0, 36); ctx.fillRect(x0, 1460, x1 - x0, 36);
}
function gapGlow(ctx, edgeX, dir, t, a = 1) {
  const f = 0.8 + 0.2 * L.fbm1(t * 3, 9);
  ctx.fillStyle = L.linear(ctx, edgeX, 0, edgeX + dir * 90, 0, [[0, rgba('#ff9a50', 0.45 * f * a)], [1, rgba('#ff9a50', 0)]]);
  ctx.fillRect(Math.min(edgeX, edgeX + dir * 90), 0, 90, VH);
}

// temple guards standing behind Yosef, each gripping one of his arms
function guardsBehind(ctx, W, t, yx, yy, ys, Lt, o = {}) {
  const dark = Object.assign({}, Lt, { key: mix(Lt.key || '#ffffff', '#40404a', 0.35) });
  const res = [];
  for (const [dx, fc, yaw] of o.spots || [[-2.7, 1, 0.35], [2.9, -1, -0.38]]) {
    const pl = { x: yx + dx * ys, y: yy - 0.35 * ys, s: ys * 0.96, facing: fc, by: 0.3 * fc, len: 6, style: 'temple_guard' };
    const seed = dx > 0 ? 3 : 7;
    res.push(drawCharacter(ctx, 'guard', extraF(t, seed, { yaw, gx: 0.3 * fc, gy: 0.2, pitch: 0.06, glance: 0.3, pose: 'guard_spear',
      F: { browFurrow: 0.35 + 0.15 * seed / 7, mouthPress: 0.35 } }), pl, dark, t, { sway: [0, 0] }));
  }
  return res;
}
// their hands closing around Yosef's upper arms (drawn over him)
function guardGrips(ctx, yres, ys, Lt) {
  if (!yres || !yres.arms) return;
  const st = C.temple_guard;
  const sides = [[yres.arms.near, -yres.fc], [yres.arms.far, yres.fc]];
  for (const [g, out] of sides) {
    const grip = [lerp(g.S[0], g.E[0], 0.42) + out * ys * 0.42, lerp(g.S[1], g.E[1], 0.42)];
    const E = [grip[0] + out * ys * 1.15, grip[1] - ys * 0.55];
    const f = [-out * 0.45, -0.05, 0.9], n = [-out * 0.9, 0.05, -0.3];
    closeArm(ctx, E, grip, ys * 0.92, st, Lt, { hand: 'grip', f, n, right: out < 0, sleeve: st.cloth.tunic });
  }
}

function edgeFingers(ctx, x, y, s, st, Lt, dir) {
  const H = require('./hands');
  const skin = L.mul(st.skin, Lt.key || '#fff'), skinSh = L.mul(st.skinShadow, Lt.amb || '#fff');
  const lw = s * 0.022;
  const sizes = [0.95, 1.0, 0.96, 0.8];
  for (let i = 0; i < 4; i++) {
    const k = sizes[i], r = s * 0.13 * k;
    const y0 = y + i * s * 0.3;
    const A = [x - dir * s * 0.2, y0], Bp = [x + dir * s * 0.18 * k, y0 + s * 0.02], Cp = [x + dir * s * 0.24 * k, y0 + s * 0.22 * k];
    H.inkPart(ctx, (pp) => { H.capsule(pp, A, r, Bp, r * 0.95); H.capsule(pp, Bp, r * 0.95, Cp, r * 0.85); }, {
      fill: skin, line: st.line, lw,
      shade: (c) => { c.fillStyle = rgba(skinSh, 0.5); c.fillRect(Math.min(A[0], Cp[0]) - s, y0 + r * 0.25, s * 2, s); },
    });
    ctx.fillStyle = rgba(mix(skin, '#fff4f0', 0.5), 0.9);
    ctx.beginPath(); ctx.ellipse(Cp[0] + dir * r * 0.15, Cp[1] - r * 0.1, r * 0.45, r * 0.6, 0, 0, L.TAU); ctx.fill();
    ctx.strokeStyle = rgba(st.line, 0.35); ctx.lineWidth = lw * 0.6; ctx.stroke();
  }
}

S.jer_crack = (ctx, W, t, lt, dur, p) => {
  // the child's point of view: peeking through the gap of a half-open door at the torchlit street
  const gx = 400, gw = 280;
  ctx.save();
  ctx.beginPath(); ctx.rect(gx, 0, gw, VH); ctx.clip();
  drawCached(ctx, cached('jer', (x) => BG.jerusalemNight(x)));
  BG.jerusalemDyn(ctx, t, { torches: [[540, 740, 1]] });
  const sx = lerp(760, 300, smooth(lt / dur));
  const sil = { side: 1, key: '#9a7a6a', amb: '#3a3048', shadow: 0.8, rim: '#ff9a50', rimA: 0.8, rimSide: 1, wrap: 0.35 };
  actor(ctx, W, 'yosef', t, { x: sx, y: 930, s: 50, facing: -1, by: -0.4, len: 9.5 }, sil, looks({ gx: 0.5, gy: 0, yaw: 0.4, pitch: 0 }), { noTag: true });
  actor(ctx, W, 'saul', t, { x: sx + 190, y: 905, s: 52, facing: -1, by: -0.4, len: 9.5 }, sil, looks({ gx: -0.5, gy: 0, yaw: -0.4, pitch: 0 }), { noTag: true });
  ctx.restore();
  doorPlanks(ctx, 0, gx, t);
  doorPlanks(ctx, gx + gw, VW, t);
  gapGlow(ctx, gx, -1, t);
  gapGlow(ctx, gx + gw, 1, t);
  // a small hand gripping the door edge
  edgeFingers(ctx, gx - 6, 1150, 150, C.child, { key: '#d8a070', amb: '#5a4060' }, 1);
  BG.vignette(ctx, 0.45, '#010205');
};

S.jer_child = (ctx, W, t, lt, dur, p) => {
  // the boy behind the door, his face caught in the strip of torchlight from the gap
  ctx.fillStyle = '#0c0a0e'; ctx.fillRect(0, 0, VW, VH);
  const gx = 330, gw = 470;
  const Lt = { side: 1, key: '#ffcc98', amb: '#4a4266', shadow: 0.8, rim: '#ffa060', rimA: 0.5, rimSide: 1, wrap: 0.6 };
  ctx.save();
  ctx.beginPath(); ctx.rect(gx, 0, gw, VH); ctx.clip();
  ctx.fillStyle = L.linear(ctx, gx, 0, gx + gw, 0, [[0, '#2a1c18'], [1, '#14100e']]);
  ctx.fillRect(gx, 0, gw, VH);
  actor(ctx, W, 'child', t, { x: 570, y: 1290, s: 190, facing: 1, by: 0.2, len: 5 }, Lt, looks({ gx: 0.5, gy: 0.0, yaw: 0.2, pitch: 0.0 }, { out: { gx: 0.55, gy: 0.05, yaw: 0.22, pitch: 0.02 } }));
  const f = 0.8 + 0.2 * L.fbm1(t * 3, 9);
  ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 860, 700, 600, '#ff8a30', 0.2 * f);
  ctx.restore();
  doorPlanks(ctx, 0, gx, t);
  doorPlanks(ctx, gx + gw, VW, t);
  gapGlow(ctx, gx, -1, t, 0.7);
  gapGlow(ctx, gx + gw, 1, t, 0.7);
  // his fingers curled around the door edge
  edgeFingers(ctx, gx + gw + 4, 1130, 165, C.child, { key: '#ffcc98', amb: '#5a4a6a' }, -1);
  BG.vignette(ctx, 0.4, '#010205');
};

S.jer_yosef = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('jer', (x) => BG.jerusalemNight(x), { z: 1.4, cx: 540, cy: 900 }, 8));
  BG.jerusalemDyn(ctx, t, { torches: [[220, 700, 1], [900, 640, 2]] });
  const lk = looks({ gx: -0.6, gy: 0.0, yaw: -0.42, pitch: 0.0 }, { back: { gx: -0.75, gy: 0.05, yaw: -0.48, pitch: 0.02 }, away: { gx: 0.4, gy: 0, yaw: 0.3, pitch: 0 } });
  guardsBehind(ctx, W, t, 560, 1220, 150, LIGHT.jer);
  const yres = actor(ctx, W, 'yosef', t, { x: 560, y: 1220, s: 150, facing: 1, by: 0.55, len: 6 }, LIGHT.jer, lk);
  guardGrips(ctx, yres, 150, LIGHT.jer);
  BG.vignette(ctx, 0.5, '#010205');
};

S.jer_saul = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('jer', (x) => BG.jerusalemNight(x), { z: 1.6, cx: 360, cy: 800 }, 12));
  const f = 0.8 + 0.2 * L.fbm1(t * 3, 3);
  const Lt = Object.assign({}, LIGHT.jer, { key: mix('#ff9a50', '#ffd0a0', f * 0.6) });
  const lk = looks({ gx: 0.45, gy: 0.1, yaw: 0.3, pitch: 0.04 }, {
    yosef: { gx: 0.5, gy: 0.1, yaw: 0.32, pitch: 0.04 }, away_down: { gx: -0.5, gy: 0.6, yaw: -0.15, pitch: 0.2 },
  });
  actor(ctx, W, 'saul', t, { x: 520, y: 1300, s: 182, facing: 1, by: 0.25, len: 5 }, Lt, lk);
  B.drawTorch(ctx, 120, 1150, 44, t, Lt, { size: 1.3, seed: 7 });
  BG.vignette(ctx, 0.45, '#010205');
};

S.jer_yosef_look = (ctx, W, t, lt, dur, p) => {
  // over young Paul's shoulder: Yosef, bound, turns and looks at him without hatred
  camera(ctx, lt, dur, p, [640, 840]);
  drawCached(ctx, bgView('jer', (x) => BG.jerusalemNight(x), { z: 1.8, cx: 700, cy: 800 }, 14));
  const lk = looks({ gx: -0.3, gy: 0.05, yaw: -0.16, pitch: 0.02 }, { paul: { gx: -0.32, gy: 0.06, yaw: -0.18, pitch: 0.03 } });
  guardsBehind(ctx, W, t, 660, 1330, 190, LIGHT.jer, { spots: [[-2.6, 1, 0.3], [2.5, -1, -0.32]] });
  const yres = actor(ctx, W, 'yosef', t, { x: 660, y: 1330, s: 190, facing: -1, by: -0.15, len: 5 }, LIGHT.jer, lk);
  guardGrips(ctx, yres, 190, LIGHT.jer);
  // young Paul from behind, out of focus in the foreground: dark curls, white mantle with its blue stripe
  ctx.save();
  ctx.filter = 'blur(5px)';
  ctx.fillStyle = '#1a1420';
  ctx.beginPath(); ctx.moveTo(-220, 1920); ctx.quadraticCurveTo(-140, 1200, 110, 1140); ctx.quadraticCurveTo(400, 1130, 500, 1920); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#8a8478';
  ctx.beginPath(); ctx.moveTo(-60, 1920); ctx.quadraticCurveTo(40, 1300, 300, 1180); ctx.quadraticCurveTo(420, 1300, 470, 1920); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#2d4f8a'; ctx.lineWidth = 26;
  ctx.beginPath(); ctx.moveTo(40, 1920); ctx.quadraticCurveTo(120, 1420, 300, 1210); ctx.stroke();
  ctx.fillStyle = '#0d0a0c';
  ctx.beginPath(); ctx.ellipse(130, 900, 220, 262, 0.15, 0, L.TAU); ctx.fill();
  for (let i = 0; i < 11; i++) { const a = -2.6 + i * 0.3; ctx.beginPath(); ctx.arc(130 + Math.cos(a) * 214, 900 + Math.sin(a) * 255, 34, 0, L.TAU); ctx.fill(); }
  ctx.fillStyle = '#a07858';
  ctx.beginPath(); ctx.ellipse(330, 930, 34, 70, 0.1, 0, L.TAU); ctx.fill();
  ctx.strokeStyle = rgba('#ff9a50', 0.55); ctx.lineWidth = 10;
  ctx.beginPath(); ctx.ellipse(130, 900, 226, 268, 0.15, -1.2, 0.4); ctx.stroke();
  ctx.restore();
  BG.vignette(ctx, 0.5, '#010205');
};

// ---------------------------------------------------------- DAMASCUS
S.dam_wide = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.05] }, [540, 1100]);
  drawCached(ctx, cached('desert', (x) => BG.desert(x)));
  const sil = Object.assign({}, LIGHT.desert);
  // Saul and two companions walking toward us down the road: real strides (one foot planted while the
  // other swings and lifts), arms swinging against the legs, a small rise and fall with each step
  const prog = lt / Math.max(1, dur);
  const walkers = [
    { style: 'companion_a', dx: -128, dz: -0.08, ph: 2.2, yaw: 0.25 },
    { style: 'companion_b', dx: 132, dz: -0.05, ph: 4.1, yaw: -0.2 },
    { style: 'saul_travel', dx: 0, dz: 0, ph: 0.0, saul: true },
  ];
  const len = 11.2;
  for (const w of walkers) {
    const sc = (31 + 5 * prog) * (1 + w.dz);
    const x = 560 + w.dx * (1 + 0.12 * prog), y = 1150 + 70 * prog + w.dz * 260;
    const ph = lt * (L.TAU / 1.1) + w.ph;
    const bob = Math.abs(Math.cos(ph)) * 0.1 * sc;
    const place = { x, y: y - bob, s: sc, facing: w.dx > 0 ? -1 : 1, by: w.dx > 0 ? -0.12 : 0.12, len, style: w.style, swing: [0.3, ph], belt: true };
    floorShadow(ctx, x, y + (len + 0.4) * sc, sc * 2.0, 0.35);
    const feet = { beforeTorso: (o) => frontWalkFeet(ctx, o.neck, o.s, len, sil, C[w.style], ph) };
    if (w.saul) {
      actor(ctx, W, 'saul', t, place, sil, looks({ gx: 0.1, gy: 0, yaw: 0.08, pitch: 0 }),
        Object.assign({ mod: (F) => { F.poseFrom = F.poseTo = 'walk'; F.poseK = 1; } }, feet));
    } else {
      drawCharacter(ctx, w.style, extraF(t, w.ph * 10, { yaw: w.yaw, glance: 0.25, pose: 'walk' }), place, sil, t, Object.assign({ sway: [0, 0] }, feet));
    }
  }
};

S.dam_saul_cu = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('desert', (x) => BG.desert(x), { z: 1.6, cx: 600, cy: 700 }, 10));
  const glowK = clamp((lt - 1.2) / 1.4);
  const Lt = Object.assign({}, LIGHT.desert, { key: mix('#fff4e2', '#ffffff', glowK), shadow: lerp(0.55, 0.2, glowK) });
  const lk = looks({ gx: 0.3, gy: 0, yaw: 0.25, pitch: 0 }, { ahead: { gx: 0.35, gy: 0.0, yaw: 0.28, pitch: 0.0 }, up: { gx: 0.15, gy: -0.85, yaw: 0.15, pitch: -0.35 } });
  const bob = Math.abs(Math.sin(lt * 4.2)) * 10 * (1 - glowK);
  actor(ctx, W, 'saul', t, { x: 540, y: 1300 - bob, s: 180, facing: 1, by: 0.25, len: 5, style: 'saul_travel' }, Lt, lk);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#ffffff', glowK * 0.9); ctx.fillRect(0, 0, VW, VH);
  ctx.restore();
};

S.dam_flash = (ctx, W, t, lt, dur, p) => {
  BG.heavenLight(ctx, t, { x: 540, y: 600 });
  ctx.fillStyle = rgba('#ffffff', 1 - smooth(lt / dur) * 0.4); ctx.fillRect(0, 0, VW, VH);
};

S.dam_saul_kneel = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.05] }, [540, 1100]);
  drawCached(ctx, bgView('desert', (x) => BG.desert(x), { z: 1.3, cx: 540, cy: 1300 }, 6));
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#fff8e0', 0.55); ctx.fillRect(0, 0, VW, VH);
  ctx.restore();
  BG.heavenLightOverlay && BG.heavenLightOverlay(ctx, t);
  // light shaft from above onto Saul
  BG.lightShaft(ctx, [540, -200], [560, 1700], 500, 900, '#fffbe8', 0.75);
  const Lt = LIGHT.lightUp;
  const pS = { x: 560, y: 1140, s: 110, facing: 1, by: 0.3, len: 4.2, style: 'saul_travel' };
  const shake = 4 * L.noise1(t * 1.4, 3);
  pS.x += shake;
  actor(ctx, W, 'saul', t, pS, Lt, looks({ gx: 0, gy: 0.7, yaw: 0.1, pitch: 0.28 }, { down: { gx: 0, gy: 0.8, yaw: 0.1, pitch: 0.3 } }),
    { afterTorso: (o) => kneelLegs(ctx, o.neck, o.s, 1, C.saul, Lt) });
  BG.dust(ctx, t, { x: 100, y: 900, w: 880, h: 900 }, 24, '#fff4d0', 33, 0.6, 3.5);
};

S.dam_jesus = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 760]);
  BG.heavenLight(ctx, t, { x: 540, y: 560 });
  const Lt = LIGHT.divine;
  const lk = looks({ gx: 0, gy: 0.6, yaw: 0.0, pitch: 0.22 }, { down: { gx: 0.0, gy: 0.65, yaw: 0.02, pitch: 0.24 }, cam: { gx: 0, gy: 0.1, yaw: 0, pitch: 0.05 } });
  halo(ctx, 540, 1150 - 2.2 * 160 - 45, 160, 1);
  actor(ctx, W, 'jesus', t, { x: 540, y: 1150, s: 160, facing: 1, by: 0.0, len: 7 }, Lt, lk);
  // radiance over the figure
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 540, 600, 700, '#fff6dc', 0.35);
  ctx.restore();
  BG.dust(ctx, t, { x: 0, y: 0, w: VW, h: VH }, 22, '#ffffff', 17, 0.55, 3);
};

S.dam_saul_up = (ctx, W, t, lt, dur, p) => {
  camera(ctx, { zoom: [1.0, 1.06] } && lt, dur, { zoom: [1.0, 1.06] }, [540, 820]);
  drawCached(ctx, bgView('desert', (x) => BG.desert(x), { z: 2.0, cx: 540, cy: 1400 }, 14));
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#fff8e0', 0.4); ctx.fillRect(0, 0, VW, VH);
  L.glow(ctx, 540, -100, 1100, '#ffffff', 0.8);
  ctx.restore();
  const lk = looks({ gx: 0, gy: -0.7, yaw: 0.05, pitch: -0.3 }, { up: { gx: 0.0, gy: -0.75, yaw: 0.05, pitch: -0.32 } });
  actor(ctx, W, 'saul', t, { x: 540, y: 1360, s: 190, facing: 1, by: 0.1, len: 5, style: 'saul_travel' }, LIGHT.lightUp, lk);
  BG.dust(ctx, t, { x: 0, y: 0, w: VW, h: VH }, 16, '#fff4d0', 41, 0.5, 3);
};

S.dam_hands = (ctx, W, t, lt, dur, p) => {
  BG.heavenLight(ctx, t, { x: 540, y: 300 });
  const Lt = LIGHT.divine;
  const k = smooth(lt / 2.0);
  // Saul's right hand reaches up, palm open toward the light; Jesus' right hand reaches down to meet it
  closeArm(ctx, [250, 2100], [lerp(420, 455, k), lerp(1380, 1210, k)], 200, C.saul, LIGHT.lightUp,
    { hand: 'offer', f: [0.18, 1, -0.2], n: [0.1, 0.35, 0.93], right: true, sleeve: '#2c2838' });
  closeArm(ctx, [860, -300], [lerp(690, 640, k), lerp(560, 690, k)], 200, C.jesus, Lt,
    { hand: 'offer', f: [-0.25, -1, 0.2], n: [0.1, -0.35, 0.93], right: true, sleeve: C.jesus.cloth.tunic, loose: 1 });
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 540, 960, 420 + 60 * k, '#ffffff', 0.55 * k);
  ctx.restore();
};

// ---------------------------------------------------------- DAWN
S.dawn_road = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.04] }, [600, 1050]);
  drawCached(ctx, cached('dawn', (x) => BG.dawnRoad(x)));
  BG.dawnDyn(ctx, t);
  // a small group walking away down the road, into the sunrise
  for (let i = 0; i < 7; i++) {
    const depth = 1 - lt / dur * 0.12;
    const x = 560 + (i - 3) * 13 * depth + (i % 2) * 4, y = 1112 - lt * 0.9 + (i % 3) * 3;
    const h = (24 + (i % 3) * 3) * depth;
    const ph = lt * 5.4 + i * 1.3;
    const bob = Math.abs(Math.cos(ph)) * 1.2;
    ctx.fillStyle = '#1e1016';
    ctx.beginPath(); ctx.ellipse(x, y - h - bob, h * 0.17, h * 0.2, 0, 0, L.TAU); ctx.fill();
    // robe to the shins, legs stepping under it (walking away: the planted foot is the lower one)
    ctx.beginPath(); ctx.moveTo(x - h * 0.2, y - h * 0.82 - bob); ctx.lineTo(x + h * 0.2, y - h * 0.82 - bob); ctx.lineTo(x + h * 0.25, y - h * 0.16 - bob); ctx.lineTo(x - h * 0.25, y - h * 0.16 - bob); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = '#1e1016'; ctx.lineCap = 'round'; ctx.lineWidth = Math.max(1.2, h * 0.09);
    for (const sd of [-1, 1]) {
      const st2 = Math.sin(ph) * sd, lift = Math.max(0, -Math.cos(ph) * sd) * h * 0.08;
      ctx.beginPath(); ctx.moveTo(x + sd * h * 0.08, y - h * 0.2 - bob); ctx.lineTo(x + sd * h * 0.09, y - st2 * h * 0.05 - lift); ctx.stroke();
      // arms swinging against the legs
      ctx.beginPath(); ctx.moveTo(x + sd * h * 0.2, y - h * 0.78 - bob); ctx.lineTo(x + sd * h * 0.27, y - h * 0.42 - bob + st2 * h * 0.06); ctx.stroke();
    }
    ctx.strokeStyle = rgba('#ffc070', 0.5); ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.ellipse(x, y - h - bob, h * 0.17, h * 0.2, 0, -1.6, 0.2); ctx.stroke();
  }
  // Asher from behind, watching them go: hopeful, the half loaf in his hand
  const sil = { side: 1, key: '#6a4a52', amb: '#24161e', shadow: 0.85, rim: '#ffc070', rimA: 0.9, rimSide: 1, wrap: 0.2 };
  floorShadow(ctx, 380, 1890, 210, 0.5);
  backFigure(ctx, 380, 1225, 70, C.asher, sil, t, { turn: 0.3, len: 9.3, half: true });
};

// a figure seen from behind: back of the head, shoulders, arms at the sides, robe to the feet
function backFigure(ctx, x, y, s, st, Lt, t, o = {}) {
  const H = require('./hands');
  const turn = o.turn || 0;
  const len = o.len || 9.4;
  const lw = (Lt.lineW || 1) * s * 0.02;
  const X = (u, v) => [x + u * s, y + v * s];
  const col = st.cloth.tunic, cS = B.clothShadow(col, Lt);
  const litC = L.mul(col, Lt.key || '#fff');
  const breathe = Math.sin(t * 1.6) * 0.03;
  // robe
  const robe = [X(-0.62, -0.2), X(-1.4, 0.15), X(-1.95, 0.65), X(-2.05, 1.4), X(-1.9, 3.0), X(-1.78, 4.6), X(-1.98, len), X(1.98, len), X(1.78, 4.6), X(1.9, 3.0), X(2.05, 1.4), X(1.95, 0.65), X(1.4, 0.15), X(0.62, -0.2)];
  ctx.beginPath(); L.crPath(ctx, robe, true, 0.45); ctx.fillStyle = litC; ctx.fill();
  ctx.save(); ctx.clip();
  const g = ctx.createLinearGradient(x + s * 2, 0, x - s * 1.2, 0);
  g.addColorStop(0, rgba(cS, 0.2)); g.addColorStop(1, rgba(cS, 0.75)); ctx.fillStyle = g; ctx.fillRect(x - 4 * s, y - s, 8 * s, (len + 2) * s);
  // mantle across the back, from the left shoulder to the right hip
  const m = [X(-1.6, 0.3), X(-0.4, 0.0), X(0.9, 1.6), X(1.95, 3.6), X(1.9, 5.6), X(0.6, 4.6), X(-1.0, 2.4), X(-2.0, 1.2)];
  ctx.beginPath(); L.crPath(ctx, m, true, 0.4); ctx.fillStyle = L.mul(st.cloth.mantle || col, Lt.key || '#fff'); ctx.fill();
  for (let i = 0; i < 4; i++) L.strokeSmooth(ctx, [X(-1.2 + i * 0.5, 0.6 + i * 0.3), X(0.2 + i * 0.4, 2.6 + i * 0.3), X(1.0 + i * 0.2, 4.4)], rgba(shade(col, 0.4), 0.5), lw * 0.8);
  L.strokeSmooth(ctx, [X(-1.9, 4.05), X(0, 4.2), X(1.9, 4.05)], L.mul(st.cloth.trim || '#2a2018', Lt.key || '#fff'), s * 0.3);
  ctx.restore();
  ctx.beginPath(); L.crPath(ctx, robe, true, 0.45); ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.stroke();
  // rim light from the sunrise on the right edge
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.strokeSmooth(ctx, robe.slice(8, 13).reverse(), rgba(Lt.rim || '#ffc070', 0.55), s * 0.08);
  ctx.restore();
  // arms hanging at the sides; seen from behind, the right arm is on screen-right
  const by = Math.PI + turn;
  const actorMod = require('./actor');
  for (const sd of [-1, 1]) {
    const S = X(sd * 1.5, 0.95 + breathe);
    const Wt = X(sd * 1.95, 5.15);
    const g2 = B.armGeom(S, Wt, s, { bend: -sd });
    const right = sd > 0;
    const shape = o.half && right ? H.preset('cup') : H.preset('relax');
    const palm = o.half && right ? { in: 0.8, up: 0.4 } : { in: 1, back: 0.3 };
    const f = H.V.norm([g2.dir[0], -g2.dir[1], 0]);
    const h = H.handParts(g2.W, s, st, Lt, { f, n: actorMod.bodyVec(palm, by, right), right, shape });
    H.drawWrist(ctx, g2.W, g2.dir, s, st, Lt);
    B.drawSleeve(ctx, g2, st, Lt, { part: 'all', torso: robe });
    h.draw(ctx);
    if (o.half && right) { const gp = h.gripAt(s * 0.6); B.drawHalfBread(ctx, gp[0] + s * 0.3, gp[1] + s * 0.2, s * 0.8, Lt, { face: -1, rot: 0.3 }); }
  }
  // neck and the back of the head (hair all over), ears, a sliver of cheek on the side he turns to
  const hx = x + turn * s * 0.35, hy = y - 2.2 * s;
  ctx.fillStyle = L.mul(st.skin, Lt.key || '#fff');
  ctx.beginPath(); ctx.moveTo(x - s * 0.55, y + s * 0.1); ctx.lineTo(hx - s * 0.5, hy + s * 1.0); ctx.lineTo(hx + s * 0.5, hy + s * 1.0); ctx.lineTo(x + s * 0.55, y + s * 0.1); ctx.closePath(); ctx.fill();
  ctx.fillStyle = rgba(L.mul(st.skinShadow, Lt.amb || '#fff'), 0.8);
  ctx.fillRect(x - s * 0.6, hy + s * 0.9, s * 1.2, s * 0.35);
  for (const sd of [-1, 1]) {
    const ex = hx + sd * s * 0.98 + turn * s * 0.15, ey = hy + s * 0.15;
    ctx.fillStyle = L.mul(st.skin, Lt.key || '#fff');
    ctx.beginPath(); ctx.ellipse(ex, ey, s * 0.17, s * 0.27, sd * 0.2, 0, L.TAU); ctx.fill();
    ctx.strokeStyle = st.line; ctx.lineWidth = lw * 0.8; ctx.stroke();
  }
  const cheek = turn > 0 ? 1 : -1;
  ctx.fillStyle = L.mul(st.skin, Lt.key || '#fff');
  ctx.beginPath(); ctx.ellipse(hx + cheek * s * 0.86, hy + s * 0.55, s * 0.18, s * 0.55, cheek * 0.15, 0, L.TAU); ctx.fill();
  ctx.fillStyle = L.mul(st.beardColor || st.hair, Lt.key || '#fff');
  ctx.beginPath(); ctx.ellipse(hx + cheek * s * 0.82, hy + s * 0.85, s * 0.2, s * 0.35, cheek * 0.15, 0, L.TAU); ctx.fill();
  const hairC = L.mul(st.hair, Lt.key || '#fff');
  ctx.fillStyle = hairC;
  ctx.beginPath(); ctx.ellipse(hx, hy - s * 0.32, s * 1.05, s * 1.12, 0, 0, L.TAU); ctx.fill();
  ctx.beginPath(); ctx.ellipse(hx, hy + s * 0.45, s * 0.86, s * 0.55, 0, 0, Math.PI); ctx.fill();
  for (let i = 0; i < 24; i++) {
    const a = -Math.PI * 0.05 + (i / 24) * Math.PI * 2.1;
    const r = s * (1.04 + 0.05 * Math.sin(i * 2.3));
    const px = hx + Math.cos(a) * r, py = hy - s * 0.32 + Math.sin(a) * r * 1.06;
    if (py > hy + s * 0.75) continue;
    ctx.fillStyle = hairC; ctx.beginPath(); ctx.arc(px, py, s * 0.12, 0, L.TAU); ctx.fill();
    ctx.strokeStyle = rgba(st.hairLine, 0.6); ctx.lineWidth = lw * 0.6;
    ctx.beginPath(); ctx.arc(px, py, s * 0.12, a - 1.2, a + 1.2); ctx.stroke();
  }
  for (let i = 0; i < 14; i++) {
    const u = -0.7 + (i % 5) * 0.35, v = -1.0 + Math.floor(i / 5) * 0.45;
    ctx.strokeStyle = rgba(st.hairLine, 0.4); ctx.lineWidth = lw * 0.6;
    ctx.beginPath(); ctx.arc(hx + u * s, hy + v * s, s * 0.09, i, i + 4); ctx.stroke();
  }
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.strokeStyle = rgba(Lt.rim || '#ffc070', 0.6); ctx.lineWidth = s * 0.06;
  ctx.beginPath(); ctx.ellipse(hx, hy - s * 0.32, s * 1.08, s * 1.15, 0, -1.3, 0.5); ctx.stroke();
  ctx.restore();
}

S.dawn_asher_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 820]);
  drawCached(ctx, bgView('dawn', (x) => BG.dawnRoad(x), { z: 1.8, cx: 620, cy: 1000 }, 14));
  BG.dawnDyn(ctx, t);
  const lk = looks({ gx: 0.4, gy: -0.3, yaw: 0.3, pitch: -0.1 }, { up: { gx: 0.25, gy: -0.7, yaw: 0.25, pitch: -0.24 }, far: { gx: 0.5, gy: -0.1, yaw: 0.35, pitch: -0.03 } });
  actor(ctx, W, 'asher', t, { x: 540, y: 1310, s: 185, facing: 1, by: 0.3, len: 5 }, LIGHT.dawn, lk);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 900, 500, 700, '#ffc070', 0.25);
  ctx.restore();
};

S.dawn_jesus = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 760]);
  drawCached(ctx, cached('dawnsky', (x) => { BG.dawnRoad(x, { horizon: 1500 }); }, 18));
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 540, 640, 1000, '#ffe0a0', 0.55);
  ctx.restore();
  const Lt = Object.assign({}, LIGHT.divine, { key: '#fff2dc', amb: '#e8c0a0', rim: '#ffe0a0' });
  const lk = looks({ gx: 0, gy: 0.05, yaw: 0.0, pitch: 0.03 }, { cam: { gx: 0.0, gy: 0.0, yaw: 0.0, pitch: 0.02 } });
  halo(ctx, 540, 1120 - 2.2 * 150 - 42, 150, 1);
  actor(ctx, W, 'jesus', t, { x: 540, y: 1120, s: 150, facing: 1, by: 0.0, len: 7 }, Lt, lk);
  BG.dust(ctx, t, { x: 0, y: 0, w: VW, h: VH }, 18, '#fff0c0', 51, 0.5, 3);
};

S.end_card = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, cached('dawnsky2', (x) => { BG.dawnRoad(x, { horizon: 1300 }); }, 26));
  ctx.fillStyle = rgba('#0a0608', 0.35); ctx.fillRect(0, 0, VW, VH);
  BG.dawnDyn(ctx, t, { horizon: 1300 });
  B.drawBread(ctx, 470, 1330, 190, LIGHT.dawn, { rot: -0.04 });
  B.drawHalfBread(ctx, 760, 1390, 105, LIGHT.dawn, { face: -1, rot: 0.25 });
};

// ------------------------------------------------------------------ grades
function grade(ctx, name, lt) {
  if (!name) return;
  ctx.save();
  if (name === 'memory_warm') {
    ctx.globalCompositeOperation = 'color'; ctx.fillStyle = rgba('#b08050', 0.35); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'soft-light'; ctx.fillStyle = rgba('#ffcc88', 0.35); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'source-over'; BG.vignette(ctx, 0.5, '#1a0c04', 0.4);
  } else if (name === 'memory_blue') {
    ctx.globalCompositeOperation = 'color'; ctx.fillStyle = rgba('#5a6a9a', 0.4); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'source-over'; BG.vignette(ctx, 0.55, '#02040a', 0.38);
    // soft edge haze
    ctx.globalCompositeOperation = 'screen';
    ctx.fillStyle = L.radial(ctx, VW / 2, VH / 2, VH * 0.35, VH * 0.75, [[0, rgba('#8aa0d0', 0)], [1, rgba('#8aa0d0', 0.18)]]);
    ctx.fillRect(0, 0, VW, VH);
  } else if (name === 'memory_gold') {
    ctx.globalCompositeOperation = 'soft-light'; ctx.fillStyle = rgba('#ffc070', 0.4); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'screen';
    ctx.fillStyle = L.radial(ctx, VW / 2, VH / 2, VH * 0.3, VH * 0.75, [[0, rgba('#fff0c0', 0)], [1, rgba('#fff0c0', 0.25)]]);
    ctx.fillRect(0, 0, VW, VH);
  }
  ctx.restore();
}

module.exports = { SHOTS: S, grade, LIGHT, VW, VH, cache };
