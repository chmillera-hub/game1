// Shot library: camera framing, lighting, character placement, gaze targets.
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const L = require('./lib');
const { clamp, lerp, mix, rgba, shade, smooth } = L;
const BG = require('./backgrounds');
const B = require('./body');
const { drawCharacter, poseBlend } = require('./actor');
const { drawHead } = require('./face');
const { C } = require('./characters');

const VW = 1080, VH = 1920;

// ---------------------------------------------------------------- lighting presets
const LIGHT = {
  lamp: { side: -1, key: '#fff0de', amb: '#987f72', shadow: 0.68, rim: '#ffb060', rimA: 0.35, rimSide: 1, wrap: 0.75 },
  lampR: { side: 1, key: '#fff0de', amb: '#987f72', shadow: 0.68, rim: '#ffb060', rimA: 0.3, rimSide: -1, wrap: 0.75 },
  street: { side: -1, key: '#ffe7ce', amb: '#616880', shadow: 0.78, rim: '#a8c0ff', rimA: 0.5, rimSide: 1, wrap: 0.65 },
  church: { side: 1, key: '#ffeed8', amb: '#8a7067', shadow: 0.7, rim: '#ffb060', rimA: 0.4, rimSide: -1, wrap: 0.7 },
  cellL: { side: -1, key: '#f2f4ff', amb: '#6e6f80', shadow: 0.72, rim: '#ffa860', rimA: 0.45, rimSide: 1, wrap: 0.7 },
  cellR: { side: -1, key: '#f4f6ff', amb: '#6e6f80', shadow: 0.72, rim: '#ffa860', rimA: 0.35, rimSide: 1, wrap: 0.8 },
  cellWarm: { side: -1, key: '#fff0dc', amb: '#8a7480', shadow: 0.62, rim: '#ffd090', rimA: 0.5, rimSide: 1, wrap: 0.85 },
  jer: { side: 1, key: '#ffdfc2', amb: '#454c67', shadow: 0.82, rim: '#ff9a50', rimA: 0.45, rimSide: -1, wrap: 0.6 },
  jerCool: { side: -1, key: '#e4eaff', amb: '#40465c', shadow: 0.8, rim: '#ff9a50', rimA: 0.5, rimSide: 1, wrap: 0.6 },
  desert: { side: 1, key: '#fff4e2', amb: '#b88c84', shadow: 0.55, rim: '#ffffff', rimA: 0.25, rimSide: -1, wrap: 0.8 },
  divine: { side: -1, key: '#fffaf0', amb: '#e8cfb0', shadow: 0.32, rim: '#ffffff', rimA: 0.85, rimSide: 1, wrap: 1.0 },
  lightUp: { side: 1, key: '#fff8e8', amb: '#c8a890', shadow: 0.45, rim: '#ffffff', rimA: 0.7, rimSide: -1, wrap: 0.9 },
  dawn: { side: 1, key: '#ffead2', amb: '#716070', shadow: 0.62, rim: '#ffcc80', rimA: 0.65, rimSide: 1, wrap: 0.7 },
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
  // Sitting sideways along the stone ledge: the far leg lies folded on the ledge (knee out ahead of
  // him, shin tucked back under the other thigh); the near leg hangs over the front edge with its
  // foot on the floor. The robe covers both; it is shaded as cloth over the forms underneath.
  const X = (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s];
  const col = st.cloth.tunic, shC = B.clothShadow(col, Lt), lit = L.mul(col, Lt.key || '#fff');
  const lw = (Lt.lineW || 1) * s * 0.02;
  const fy = o.floor || 7.25;
  const fold = (pts, k) => L.strokeSmooth(ctx, pts, rgba(shade(col, 0.45), 0.5 * (k || 1)), lw * 0.8);
  const shape = (pts, shadeFn) => {
    ctx.beginPath(); L.crPath(ctx, pts, true, 0.42); ctx.fillStyle = lit; ctx.fill();
    ctx.save(); ctx.clip(); shadeFn(); ctx.restore();
    ctx.beginPath(); L.crPath(ctx, pts, true, 0.42); ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.stroke();
  };
  const vgrad = (y0, y1, a0, a1) => {
    const g = ctx.createLinearGradient(...X(0, y0), ...X(0, y1));
    g.addColorStop(0, rgba(shC, a0)); g.addColorStop(1, rgba(shC, a1)); ctx.fillStyle = g; ctx.fillRect(Bn[0] - 12 * s, Bn[1], 24 * s, 10 * s);
  };
  // 1. the far leg folded on the ledge, a little further back (higher on screen), in deeper shade
  shape([X(-0.2, 3.9), X(1.4, 3.74), X(2.9, 3.76), X(3.55, 3.98), X(3.62, 4.32), X(3.25, 4.55), X(1.6, 4.6), X(0.0, 4.55)], () => {
    vgrad(3.8, 4.6, 0.25, 0.75);
    // the knee's round end catches a little light; the shin folded back along the front of the thigh
    const kp = X(3.25, 4.0);
    ctx.fillStyle = L.radial(ctx, kp[0], kp[1], 0, s * 0.6, [[0, rgba('#ffffff', 0.08)], [1, rgba('#ffffff', 0)]]);
    ctx.fillRect(kp[0] - s, kp[1] - s, 2 * s, 2 * s);
  });
  fold([X(3.35, 4.2), X(2.4, 4.25), X(1.3, 4.3)], 1.1);
  fold([X(2.6, 3.86), X(1.6, 3.92)], 0.6);
  // the crossed leg ends in its ankle and sandalled foot, past his hand on the knee: the foot is held
  // upright, heel down and toes pointing up to the ceiling, the sole facing away from him
  foot(ctx, X, s, st, Lt, [3.48, 4.52], [3.7, 3.5], { h: 0.36 });
  // 2. the near leg: shin hanging down the front of the ledge, the foot on the floor before it
  foot(ctx, X, s, st, Lt, [1.75, fy + 0.12], [2.95, fy + 0.26]);
  shape([X(1.45, 4.95), X(2.55, 4.85), X(2.78, 5.5), X(2.72, fy - 0.2), X(2.3, fy - 0.08), X(1.72, fy - 0.18), X(1.55, 5.7)], () => {
    vgrad(5.0, fy, 0.15, 0.55);
    const g = ctx.createLinearGradient(...X(1.5, 6), ...X(2.8, 6));
    g.addColorStop(0, rgba(shC, 0.0)); g.addColorStop(0.55, rgba('#ffffff', 0.05)); g.addColorStop(1, rgba(shC, 0.4)); ctx.fillStyle = g; ctx.fillRect(Bn[0] - 12 * s, Bn[1], 24 * s, 10 * s);
  });
  fold([X(2.15, 5.3), X(2.05, 6.2), X(2.2, fy - 0.3)], 0.8);
  fold([X(2.5, 5.6), X(2.45, 6.6)], 0.6);
  // 3. the lap: the robe over the hips and the near thigh, out to the knee at the ledge's edge
  shape([X(-1.95, 4.05), X(-0.4, 3.96), X(1.1, 4.06), X(2.2, 4.32), X(2.78, 4.72), X(2.7, 5.12), X(1.8, 5.22), X(0.2, 5.08), X(-1.9, 4.95)], () => {
    vgrad(4.0, 5.2, 0.0, 0.65);
    const kp = X(2.35, 4.7);
    ctx.fillStyle = L.radial(ctx, kp[0], kp[1], 0, s * 0.7, [[0, rgba('#ffffff', 0.08)], [1, rgba('#ffffff', 0)]]);
    ctx.fillRect(kp[0] - s, kp[1] - s, 2 * s, 2 * s);
  });
  fold([X(0.0, 4.3), X(1.1, 4.5), X(2.1, 4.6)], 0.9);
  fold([X(0.5, 4.7), X(1.6, 4.85), X(2.3, 4.95)], 0.7);
  fold([X(-1.2, 4.4), X(-0.2, 4.6)], 0.6);
}
// the stone ledge a prisoner sits on (drawn before the character)
function stoneBench(ctx, Bn, s, fc, Lt, o = {}) {
  const X = (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s];
  const fy = o.floor || 7.25;
  const a = X(-3.4, 4.6), b = X(o.right || 4.1, fy);
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
function legsBlend(ctx, Bn, s, fc, st, Lt, k, FY, o = {}) {
  const X = (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s];
  const fy = (FY - Bn[1]) / s;
  const col = st.cloth.skirt || mix(st.cloth.tunic, st.cloth.mantle || st.cloth.tunic, 0.2), shC = B.clothShadow(col, Lt);
  const lw = (Lt.lineW || 1) * s * 0.02;
  const kk = smooth(k);
  const P = (a, b) => [lerp(a[0], b[0], kk), lerp(a[1], b[1], kk)];
  // standing, the robe hangs straight from the waist the torso actually has (turned as the body is
  // turned), only a little fuller at the hem: no wider than the hips, centred under the body
  let stand = [[-2.0, 4.1], [1.75, 4.15], [1.95, lerp(4.15, fy, 0.5)], [1.85, fy - 0.05], [0.3, fy + 0.08], [-1.85, fy - 0.02], [-2.05, fy - 0.3], [-2.1, lerp(4.1, fy, 0.5)]];
  if (o.by != null) {
    const c = Math.cos(o.by), sn = Math.sin(o.by), z = 0.67;
    const e1 = (-1.73 * c + z * sn) / fc, e2 = (1.73 * c + z * sn) / fc;
    const a = Math.min(e1, e2), b = Math.max(e1, e2);
    const map = (x) => a - 0.05 + (x + 2.1) / 4.05 * (b - a + 0.2);
    stand = stand.map(([x, y]) => [map(x), y]);
  }
  const kneel = [[-2.0, 4.1], [1.75, 4.15], [2.2, fy - 0.45], [2.0, fy - 0.08], [0.6, fy + 0.02], [-1.45, fy - 0.02], [-2.15, fy - 0.35], [-2.3, 5.6]];
  const robe = stand.map((q, i) => X(...P(q, kneel[i])));
  // feet: standing, both point out toward us (turned a little the way he faces) under the hem;
  // kneeling, they are behind him with the toes tucked under
  // kneeling, the feet are tucked under behind him and hidden by the robe
  ctx.beginPath(); L.crPath(ctx, robe, true, 0.42);
  ctx.fillStyle = L.mul(col, Lt.key || '#fff'); ctx.fill();
  ctx.save(); ctx.clip();
  const g = ctx.createLinearGradient(...X(0, 4.2), ...X(0, fy));
  g.addColorStop(0, rgba(shC, 0.1)); g.addColorStop(1, rgba(shC, 0.6)); ctx.fillStyle = g; ctx.fillRect(Bn[0] - 10 * s, Bn[1], 20 * s, 14 * s);
  const sa = 1 - kk; // standing: the cloth hangs over two legs
  if (sa > 0.02) {
    // the gap between the legs in shadow, the front of each leg catching the light down to the shin,
    // the relaxed leg's knee pushing the cloth forward
    const band = (x, y0, y1, w, c, a) => {
      const p0 = X(x, y0), p1 = X(x, y1);
      const gr = ctx.createLinearGradient(p0[0] - w * s, 0, p0[0] + w * s, 0);
      gr.addColorStop(0, rgba(c, 0)); gr.addColorStop(0.5, rgba(c, a * sa)); gr.addColorStop(1, rgba(c, 0));
      ctx.fillStyle = gr; ctx.fillRect(Math.min(p0[0], p1[0]) - w * s, p0[1], 2 * w * s + Math.abs(p1[0] - p0[0]), p1[1] - p0[1]);
    };
    band(-0.12, 5.4, fy, 0.45, shC, 0.55);
    band(-1.05, 4.9, fy - 0.2, 0.55, '#ffffff', 0.07);
    band(0.85, 4.9, fy - 0.2, 0.55, '#ffffff', 0.09);
    const kp = X(0.85, lerp(4.1, fy, 0.55));
    ctx.fillStyle = L.radial(ctx, kp[0], kp[1], 0, s * 0.75, [[0, rgba('#ffffff', 0.1 * sa)], [1, rgba('#ffffff', 0)]]);
    ctx.fillRect(kp[0] - s, kp[1] - s, 2 * s, 2 * s);
    const yk = lerp(4.1, fy, 0.55);
    for (const [pts, a] of [
      [[[-0.1, 5.3], [-0.12, 6.6], [-0.08, fy - 0.15]], 0.6], // between the legs
      [[[1.2, 4.5], [0.9, yk - 0.6], [0.55, yk + 0.1]], 0.45], // drape from the hip over the knee
      [[[0.85, yk + 0.25], [0.95, fy - 0.6], [0.8, fy - 0.1]], 0.4], // down the front of the shin
      [[[-1.15, 5.0], [-1.05, 6.8], [-1.2, fy - 0.15]], 0.35], // the weight leg, straight
      [[[-1.7, 5.6], [-1.75, fy - 0.3]], 0.3],
    ]) L.strokeSmooth(ctx, pts.map((q) => X(...q)), rgba(shade(col, 0.45), a * sa), lw * 0.8);
  }
  if (kk > 0.3) {
    // soft light on the front of the knee (a gradient, never a hard-edged spot)
    const kp = X(1.55, fy - 0.75);
    ctx.fillStyle = L.radial(ctx, kp[0], kp[1], 0, s * 0.7, [[0, rgba('#ffffff', 0.07 * kk)], [1, rgba('#ffffff', 0)]]);
    ctx.fillRect(kp[0] - s * 0.8, kp[1] - s * 0.8, s * 1.6, s * 1.6);
    for (const [a, b] of [[0.6, 1.6], [-0.2, 1.1], [-1.2, 0.2]]) L.strokeSmooth(ctx, [X(a, 4.4), X((a + b) / 2 + 0.2, lerp(4.4, fy, 0.5)), X(b, fy - 0.2)], rgba(shade(col, 0.45), 0.5 * kk), lw * 0.8);
    // the cloth drawn tight from the hip over the thigh to the knee, and pooling on the ground
    // round the knees in soft folds
    L.strokeSmooth(ctx, [X(-1.4, 4.6), X(0.2, 5.0), X(1.5, fy - 0.9)], rgba(shade(col, 0.45), 0.45 * kk), lw * 0.9);
    L.strokeSmooth(ctx, [X(-1.6, 5.3), X(-0.2, 5.8), X(1.1, fy - 0.45)], rgba(shade(col, 0.45), 0.35 * kk), lw * 0.8);
    for (const u of [-1.8, -1.1, -0.4, 0.4, 1.2, 1.8]) {
      L.strokeSmooth(ctx, [X(u, fy - 0.45), X(u + 0.12, fy - 0.12)], rgba(shade(col, 0.45), 0.4 * kk), lw * 0.7);
    }
    const g2 = ctx.createLinearGradient(...X(0, fy - 0.5), ...X(0, fy + 0.05));
    g2.addColorStop(0, rgba(shC, 0)); g2.addColorStop(1, rgba(shC, 0.35 * kk)); ctx.fillStyle = g2; ctx.fillRect(Bn[0] - 10 * s, Bn[1], 20 * s, 14 * s);
  }
  ctx.restore();
  ctx.beginPath(); L.crPath(ctx, robe, true, 0.42); ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.stroke();
  if (kk <= 0.5) {
    // the hem breaks over the feet: the back foot a little higher and smaller, both toes toward us
    const turn = 0.35;
    const a = X(-0.95, fy - 0.02), b = X(0.8, fy + 0.12);
    frontFoot(ctx, a[0], a[1], 0.46 * s, 0.6 * s, st, Lt, turn * fc);
    frontFoot(ctx, b[0], b[1], 0.5 * s, 0.64 * s, st, Lt, turn * fc);
    // the hem over the tops of the feet
    ctx.fillStyle = mix(L.mul(col, Lt.key || '#fff'), shC, 0.5);
    for (const q of [a, b]) { ctx.beginPath(); ctx.ellipse(q[0], q[1] - s * 0.3, s * 0.48, s * 0.14, 0, 0, Math.PI); ctx.fill(); }
  }
}
function kneelLegs(ctx, Bn, s, fc, st, Lt, o = {}) {
  legsBlend(ctx, Bn, s, fc, st, Lt, 1, Bn[1] + (o.floor || 7.0) * s, o);
}
// standing still, turned three-quarters toward us: both feet point the way the body faces (out toward
// the viewer and a little to the side the figure turns to), the back foot a touch higher and smaller
function standFeet(ctx, Bn, s, fc, len, Lt, st, turn = 0.45) {
  const style = st || C.asher;
  const fy = len + 0.12;
  const a = [Bn[0] - 0.85 * s * fc, Bn[1] + fy * s], b = [Bn[0] + 0.75 * s * fc, Bn[1] + (fy + 0.14) * s];
  frontFoot(ctx, a[0], a[1], 0.44 * s, 0.58 * s, style, Lt, turn * fc);
  frontFoot(ctx, b[0], b[1], 0.48 * s, 0.62 * s, style, Lt, turn * fc);
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
// a sandalled foot seen from the front (toes toward us), turned a little toward `turn` (-1..1)
function frontFoot(ctx, x, y, w, h, st, Lt, turn = 0) {
  const skin = L.mul(st.skin, Lt.key || '#fff'), skinSh = L.mul(st.skinShadow, Lt.amb || '#fff');
  const leather = L.mul('#5a3a22', Lt.key || '#fff'), sole = L.mul('#2e1c10', Lt.key || '#fff');
  const sk = turn * w * 0.35; // the toes swing toward the side the foot turns to
  ctx.save();
  // sole, then the foot on it (ankle at the top, toes toward us at the bottom)
  ctx.fillStyle = sole;
  ctx.beginPath(); ctx.ellipse(x + sk * 0.8, y + h * 0.42, w * (0.62 + 0.12 * Math.abs(turn)), h * 0.2, turn * 0.25, 0, L.TAU); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(x - w * 0.3, y - h * 0.5);
  ctx.quadraticCurveTo(x - w * 0.62 + sk * 0.5, y + h * 0.1, x - w * 0.5 + sk, y + h * 0.38);
  ctx.quadraticCurveTo(x + sk, y + h * 0.56, x + w * 0.5 + sk, y + h * 0.38);
  ctx.quadraticCurveTo(x + w * 0.62 + sk * 0.5, y + h * 0.1, x + w * 0.3, y - h * 0.5);
  ctx.closePath();
  ctx.fillStyle = skin; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = rgba(skinSh, 0.45); ctx.fillRect(x + w * 0.05 * -(Lt.side || -1), y - h, w, h * 2);
  ctx.fillStyle = L.linear(ctx, 0, y - h * 0.5, 0, y, [[0, rgba(skinSh, 0.5)], [1, rgba(skinSh, 0)]]); ctx.fillRect(x - w, y - h, w * 2, h);
  ctx.restore();
  ctx.strokeStyle = st.line; ctx.lineWidth = w * 0.07; ctx.stroke();
  // toes and straps
  for (const u of [-0.18, 0.06, 0.26]) L.strokeSmooth(ctx, [[x + u * w + sk, y + h * 0.3], [x + u * w * 1.05 + sk, y + h * 0.42]], rgba(st.line, 0.45), w * 0.05);
  L.strokeSmooth(ctx, [[x - w * 0.5 + sk * 0.4, y + h * 0.05], [x + sk * 0.4, y + h * 0.14], [x + w * 0.5 + sk * 0.4, y + h * 0.05]], leather, w * 0.14);
  L.strokeSmooth(ctx, [[x - w * 0.28 + sk * 0.8, y + h * 0.4], [x - w * 0.1 + sk * 0.5, y + h * 0.12]], leather, w * 0.11);
  ctx.restore();
}
// sandalled feet of a figure walking toward the camera, seen from the front: the leading foot lower
// and nearer, the trailing foot higher and mostly under the hem, the swinging foot lifting a little
function frontWalkFeet(ctx, Bn, s, len, Lt, st, ph) {
  const feet = [[-1, ph], [1, ph + Math.PI]].map(([side, p]) => ({ side, fwd: Math.sin(p), lift: Math.max(0, Math.cos(p)) * 0.22 }));
  feet.sort((a, b) => a.fwd - b.fwd);
  for (const f of feet) {
    const k = 0.9 + 0.1 * f.fwd;
    frontFoot(ctx, Bn[0] + f.side * 0.62 * s, Bn[1] + (len + 0.05 + 0.32 * f.fwd - f.lift) * s, 0.42 * s * k, 0.55 * s * k, st, Lt, 0);
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
  // He sits behind the supper table: its top hides Him from the waist down, His forearms rest on it, and
  // the cup stands on it
  const T0 = 1630, T1 = 1790;
  actor(ctx, W, 'jesus', t, { x: 540, y: 1150, s: 170, facing: 1, by: 0.05, len: 3.4 }, LIGHT.lamp, lk,
    { afterTorso: () => supperTable(ctx, T0, T1, true) });
  // the table's front edge comes in front of the sleeves that hang below it
  supperTable(ctx, T0, T1, false);
};
// the supper table seen from across it: a worn plank top lit by the lamp (back edge y0, front edge y1), and
// its front board below; withTop = false draws only the front board
function supperTable(ctx, y0, y1, withTop) {
  const Lt = LIGHT.lamp;
  if (withTop) {
    ctx.fillStyle = L.linear(ctx, 0, y0, 0, y1, [[0, '#5a3418'], [0.5, '#7a4a24'], [1, '#8a5a30']]);
    ctx.beginPath(); ctx.moveTo(-60, y0); ctx.lineTo(VW + 60, y0); ctx.lineTo(VW + 120, y1); ctx.lineTo(-120, y1); ctx.closePath(); ctx.fill();
    // the joins between the planks run away from us, and the lamp catches the top
    ctx.strokeStyle = rgba('#2a160a', 0.45); ctx.lineWidth = 3;
    for (const x of [140, 420, 700, 960]) { ctx.beginPath(); ctx.moveTo(540 + (x - 540) * 0.9, y0); ctx.lineTo(540 + (x - 540) * 1.08, y1); ctx.stroke(); }
    ctx.fillStyle = L.radial(ctx, 240, y0 + 40, 10, 520, [[0, rgba('#ffd9a0', 0.22)], [1, rgba('#ffd9a0', 0)]]);
    ctx.fillRect(0, y0, VW, y1 - y0);
    ctx.fillStyle = rgba('#1a0c04', 0.35); ctx.fillRect(0, y0, VW, 6);
    B.drawCup(ctx, 935, y0 + 92, 70, Lt);
  }
  // front board, in shadow under the edge, with the lamp's light along the edge itself
  ctx.fillStyle = L.linear(ctx, 0, y1, 0, VH, [[0, '#4a2a12'], [0.25, '#2e1a0c'], [1, '#1c0e06']]);
  ctx.fillRect(-120, y1, VW + 240, VH - y1 + 120);
  ctx.fillStyle = rgba('#ffcf8a', 0.35); ctx.fillRect(-120, y1 - 2, VW + 240, 6);
  ctx.fillStyle = rgba('#000000', 0.3); ctx.fillRect(-120, y1 + 4, VW + 240, 10);
}

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
  // Asher stands in the street a few steps from the prison door, body and feet facing us, the loaf
  // resting on his palm, looking at the door; at the end he turns to it and walks up to knock
  const f = 0.85 + 0.15 * L.fbm1(t * 3.3, 2);
  const sil = { key: mix('#a8968c', '#bca594', f), amb: '#44465a', side: -1, shadow: 0.78, rim: '#ffb070', rimA: 0.75, rimSide: -1, wrap: 0.45 };
  const lk = looks({ gx: -0.6, gy: -0.1, yaw: -0.55, pitch: -0.05 }, { door: { gx: -0.65, gy: -0.15, yaw: -0.55, pitch: -0.06 } });
  const tTurn = dur - 4.4, tWalk = dur - 3.7;
  const turn = smooth(clamp((lt - tTurn) / 0.8));
  const walk = smooth(clamp((lt - tWalk) / 3.3));
  const moving = clamp((lt - tWalk) / 0.3) * (1 - smooth(clamp((lt - (dur - 0.7)) / 0.5)));
  const footY = lerp(1720, 1575, walk), sc = lerp(64, 57, walk), x0 = lerp(850, 712, walk);
  const ph = (lt - tWalk) * L.TAU / 1.05;
  const bob = Math.abs(Math.cos(ph)) * 0.08 * sc * moving;
  const y0 = footY - 9.2 * sc;
  floorShadow(ctx, x0, footY + 0.3 * sc, 3.4 * sc, 0.6);
  actor(ctx, W, 'asher', t, { x: x0, y: y0 - bob, s: sc, facing: -1, by: lerp(0.02, -0.5, turn), len: 9.2, swing: moving > 0.05 ? [0.2 * moving, ph] : null }, sil, lk, {
    afterTorso: (o) => (lt > tWalk ? stepFeet(ctx, o.neck, o.s, -1, 9.2, sil, C.asher, ph, moving)
      : standFeet(ctx, o.neck, o.s, -1, 9.2, sil, C.asher, lerp(0.06, 0.45, turn))),
  });
};

S.street_asher_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 850]);
  drawCached(ctx, bgView('street', (x) => BG.streetNight(x), { z: 1.8, cx: 360, cy: 800 }, 14));
  const f = 0.85 + 0.15 * L.fbm1(t * 3.3, 2);
  const Lt = Object.assign({}, LIGHT.street, { key: mix('#ffd6b0', '#ffeedc', f * 0.6) });
  const lk = looks({ gx: -0.4, gy: -0.15, yaw: -0.3, pitch: -0.08 }, {
    door: { gx: -0.35, gy: -0.25, yaw: -0.26, pitch: -0.1 }, door_low: { gx: -0.2, gy: 0.3, yaw: -0.2, pitch: 0.08 },
    bread: { gx: -0.05, gy: 0.9, yaw: -0.12, pitch: 0.28 }, down: { gx: 0, gy: 0.8, yaw: -0.1, pitch: 0.25 },
  });
  actor(ctx, W, 'asher', t, { x: 560, y: 1300, s: 185, facing: -1, by: -0.25, len: 5 }, Lt, lk);
  // torch glow from left
  L.glow(ctx, -60, 700, 700, '#ff8a30', 0.25 * f);
  BG.vignette(ctx, 0.45, '#02030a');
};

// members of the house church listening to the letter: real faces, breathing and blinking, all turned
// toward the reader (each looks the way its own seat needs to look to see her).
// list: [style, x, neck y, scale, facing, look (gx toward the reader), seed]
function listeners(ctx, t, list, Lt) {
  for (const [style, x, y, s, fc, gx, seed] of list) {
    const F = extraF(t, seed, { yaw: 0.42 * fc, gx, gy: 0.06, pitch: 0.03, glance: 0.1, pose: 'rest',
      F: { browInner: 0.12, mouthSmile: 0.0, lid: 0.9 * F0(t, seed) } });
    // now and then a slow nod at what is read
    F.pitch += 0.05 * Math.max(0, Math.sin(t * 0.45 + seed * 1.7) - 0.6);
    drawCharacter(ctx, style, F, { x, y, s, facing: fc, by: 0.4 * fc, len: 6, style }, Lt, t, { sway: [0, 0] });
  }
}
const churchDim = Object.assign({}, LIGHT.church, { key: mix(LIGHT.church.key, '#5a4436', 0.3), amb: mix(LIGHT.church.amb, '#2a1e18', 0.3), rimA: 0.25 });

S.church_reader = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.03] }, [540, 900]);
  drawCached(ctx, cached('church', (x) => BG.houseChurch(x, { lampX: 620, lampY: 980 }), 0));
  const Lt = LIGHT.church;
  // the listeners seated behind her, turned to her and looking at her as she reads
  blurredLayer(ctx, 1.5, (o) => listeners(o, t, [
    ['listener_m1', 125, 1215, 64, 1, 0.55, 3], ['listener_w1', 300, 1190, 56, 1, 0.5, 5],
    ['listener_w2', 822, 1185, 54, -1, -0.5, 8], ['listener_m2', 985, 1210, 63, -1, -0.55, 11],
  ], churchDim));
  // Phoebe reading Paul's letter from an open scroll held in both hands; now and then she lets a
  // little more of it unroll from the near roller and lifts it to the light
  const lk = looks({ gx: 0.05, gy: 0.75, yaw: 0.22, pitch: 0.24 }, { scroll: { gx: 0.05, gy: 0.8, yaw: 0.22, pitch: 0.26 } });
  const ph = (t * 0.21) % 1, roll = Math.sin(Math.PI * smooth(clamp((ph - 0.55) / 0.35)));
  const lift = 0.5 + 0.5 * Math.sin(t * 0.37 + 1.1);
  const off = { n: [-0.22 * roll + 0.05 * L.noise1(t * 0.5, 3), -0.12 * roll - 0.1 * lift], f: [0.04 * L.noise1(t * 0.45, 9), -0.1 * lift + 0.04 * roll] };
  actor(ctx, W, 'phoebe', t, { x: 560, y: 1010, s: 120, facing: 1, by: 0.3, len: 7.4, armOffset: off }, Lt, lk,
    { mod: (F) => { F.pose = 'read_scroll'; F.poseTo = 'read_scroll'; F.poseFrom = 'read_scroll'; F.poseK = 1; } });
  // the table in front of her, and a clay oil lamp on it below the scroll
  ctx.fillStyle = L.linear(ctx, 0, 1700, 0, 1800, [[0, '#5a3a22'], [0.15, '#3a2414'], [1, '#1a0e06']]);
  ctx.beginPath(); ctx.moveTo(250, 1712); ctx.lineTo(930, 1700); ctx.lineTo(950, 1930); ctx.lineTo(230, 1930); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = rgba('#e8a050', 0.35); ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(252, 1713); ctx.lineTo(928, 1701); ctx.stroke();
  B.drawLamp(ctx, 600, 1712, 46, LIGHT.church);
  B.drawFlame(ctx, 628, 1676, 22, t, 2);
  L.glow(ctx, 628, 1660, 340, '#ffb050', 0.38);
  // foreground listeners (backs)
  BG.silhouettes(ctx, [[160, 1560, 120, 0.4], [900, 1600, 130, -0.4]], '#0c0604', '#ffb060', 0.45, t);
};

S.church_asher = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 860]);
  drawCached(ctx, bgView('church', (x) => BG.houseChurch(x, { lampX: 620, lampY: 980 }), { z: 1.6, cx: 540, cy: 900 }, 14));
  // the room around him, out of focus: everyone faces the same way he does, toward the reader (off to
  // the right), so we see their faces turned to her
  blurredLayer(ctx, 9, (o) => listeners(o, t, [
    ['listener_m3', 250, 985, 50, 1, 0.6, 13], ['listener_w2', 800, 965, 48, 1, 0.45, 17],
  ], churchDim));
  blurredLayer(ctx, 6, (o) => listeners(o, t, [
    ['listener_w1', 115, 1150, 76, 1, 0.62, 19], ['listener_m2', 965, 1130, 72, 1, 0.42, 23],
  ], churchDim));
  const lk = looks({ gx: 0.45, gy: -0.05, yaw: 0.28, pitch: -0.02 }, {
    reader: { gx: 0.5, gy: -0.05, yaw: 0.3, pitch: -0.03 }, down: { gx: 0.1, gy: 0.85, yaw: 0.12, pitch: 0.24 },
  });
  actor(ctx, W, 'asher', t, { x: 520, y: 1300, s: 180, facing: 1, by: 0.25, len: 5 }, LIGHT.church, lk);
};

// The prison door's leaf (planks, iron bands, studs, the grille), hinged on its left edge and
// swung inward by angle a (0 = shut), drawn through a background view {z, cx, cy}. The far edge
// recedes in perspective and the leaf darkens as it turns from the torchlight; its thickness shows
// along the free edge. o.grille: 0..1 how far the grille's iron slot has slid open; o.eyes(ctx,
// rect) draws whoever looks out through it.
function doorLeaf(ctx, view, a, o = {}) {
  const dx = 540, dy = 1020, dw = 400, dh = 700, rr = 180;
  const S = (bx, by) => [(bx - view.cx) * view.z + VW / 2, (by - view.cy) * view.z + VH / 2];
  const ca = Math.cos(a), sa = Math.sin(a);
  const M = (u, y) => { const f = 1 / (1 + (u * sa) / 1800); return S(dx - dw / 2 + u * ca, dy + (y - dy) * f); };
  const topY = (u) => { const e = Math.min(u, dw - u); return e >= rr ? dy - dh / 2 : dy - dh / 2 + rr - Math.sqrt(Math.max(0, rr * rr - (rr - e) * (rr - e))); };
  const leaf = [];
  for (let i = 0; i <= 20; i++) { const u = dw * i / 20; leaf.push(M(u, topY(u))); }
  leaf.push(M(dw, dy + dh / 2), M(0, dy + dh / 2));
  const shadeK = 1 - 0.55 * sa;
  const wood = (c) => L.mul(c, mix('#ffffff', '#40384a', 1 - shadeK));
  ctx.save();
  // the leaf's thickness, seen along the free edge once it turns
  if (sa > 0.04) {
    const th = 28 * sa;
    const e0 = M(dw, topY(dw - 1)), e1 = M(dw, dy + dh / 2);
    ctx.fillStyle = wood('#1e120a');
    ctx.beginPath(); ctx.moveTo(e0[0], e0[1]); ctx.lineTo(e0[0] + th * view.z * 0.6, e0[1] + 4); ctx.lineTo(e1[0] + th * view.z * 0.6, e1[1] - 4); ctx.lineTo(e1[0], e1[1]); ctx.closePath(); ctx.fill();
  }
  ctx.beginPath(); leaf.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
  const l0 = M(0, dy), l1 = M(dw, dy);
  ctx.fillStyle = L.linear(ctx, l0[0], 0, l1[0], 0, [[0, wood('#4a3020')], [0.5, wood('#3a2416')], [1, wood('#2a180e')]]);
  ctx.fill();
  ctx.save(); ctx.clip();
  // planks
  ctx.strokeStyle = rgba('#140a04', 0.8); ctx.lineWidth = 5 * view.z * 0.8;
  for (let i = 1; i < 5; i++) { const u = dw * i / 5; const a0 = M(u, topY(u) + 10), a1 = M(u, dy + dh / 2); ctx.beginPath(); ctx.moveTo(a0[0], a0[1]); ctx.lineTo(a1[0], a1[1]); ctx.stroke(); }
  // grain and weathering
  const rw = L.rng(23);
  for (let i = 0; i < 46; i++) {
    const u = rw() * dw, y = dy - dh / 2 + rw() * dh, len = 30 + rw() * 90;
    const p0 = M(u, y), p1 = M(u + (rw() - 0.5) * 6, y + len);
    ctx.strokeStyle = rgba(rw() < 0.5 ? '#0e0804' : '#6a4a32', 0.25); ctx.lineWidth = (1 + rw() * 2) * view.z * 0.8;
    ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke();
  }
  // iron bands and studs
  for (const by of [dy - dh * 0.28, dy + dh * 0.05, dy + dh * 0.36]) {
    const b = [M(0, by - 16), M(dw, by - 16), M(dw, by + 16), M(0, by + 16)];
    ctx.fillStyle = L.mul('#1c1c20', mix('#ffffff', '#50505a', 1 - shadeK));
    ctx.beginPath(); b.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath(); ctx.fill();
    const h0 = M(0, by - 16), h1 = M(dw, by - 16), h2 = M(dw, by - 10), h3 = M(0, by - 10);
    ctx.fillStyle = rgba('#9aa6c8', 0.25 * shadeK);
    ctx.beginPath(); ctx.moveTo(h0[0], h0[1]); ctx.lineTo(h1[0], h1[1]); ctx.lineTo(h2[0], h2[1]); ctx.lineTo(h3[0], h3[1]); ctx.closePath(); ctx.fill();
    for (let i = 0; i < 7; i++) { const c = M(30 + i * (dw - 60) / 6, by); ctx.fillStyle = '#2c2c30'; ctx.beginPath(); ctx.ellipse(c[0], c[1], 9 * view.z * Math.max(0.3, ca), 9 * view.z, 0, 0, L.TAU); ctx.fill(); }
  }
  // the grille in the door
  const gx0 = dw / 2 - 60, gx1 = dw / 2 + 60, gy0 = dy - dh * 0.42, gy1 = gy0 + 70;
  const G = [M(gx0, gy0), M(gx1, gy0), M(gx1, gy1), M(gx0, gy1)];
  ctx.fillStyle = '#050403';
  ctx.beginPath(); G.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath(); ctx.fill();
  if (o.eyes && (o.grille || 0) > 0) {
    ctx.save(); ctx.beginPath(); G.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath(); ctx.clip();
    o.eyes(ctx, { x0: G[0][0], y0: G[0][1], x1: G[2][0], y1: G[2][1] });
    ctx.restore();
  }
  // the iron slot cover sliding aside
  const gs = o.grille || 0;
  if (gs < 1) {
    const C0 = M(gx0 + 120 * gs, gy0), C1 = M(gx1 + 120 * gs, gy0), C2 = M(gx1 + 120 * gs, gy1), C3 = M(gx0 + 120 * gs, gy1);
    ctx.fillStyle = L.linear(ctx, 0, C0[1], 0, C3[1], [[0, '#2c2c30'], [1, '#18181c']]);
    ctx.beginPath(); ctx.moveTo(C0[0], C0[1]); ctx.lineTo(C1[0], C1[1]); ctx.lineTo(C2[0], C2[1]); ctx.lineTo(C3[0], C3[1]); ctx.closePath(); ctx.fill();
  }
  ctx.strokeStyle = '#2a2a2e'; ctx.lineWidth = 7 * view.z * 0.8;
  for (let i = 0; i < 4; i++) { const p0 = M(gx0 + 15 + i * 30, gy0), p1 = M(gx0 + 15 + i * 30, gy1); ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke(); }
  // grime toward the bottom
  const g0 = M(0, dy + dh * 0.2), g1 = M(0, dy + dh / 2);
  ctx.fillStyle = L.linear(ctx, 0, g0[1], 0, g1[1], [[0, rgba('#0a0604', 0)], [1, rgba('#0a0604', 0.5)]]);
  ctx.fillRect(0, g0[1], VW, g1[1] - g0[1] + 10);
  ctx.restore();
  ctx.beginPath(); leaf.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
  ctx.strokeStyle = rgba('#0a0604', 0.9); ctx.lineWidth = 3 * view.z; ctx.stroke();
  ctx.restore();
  return { doorway: () => { const p = []; for (let i = 0; i <= 20; i++) { const u = dw * i / 20; p.push(S(dx - dw / 2 + u, topY(u))); } p.push(S(dx + dw / 2, dy + dh / 2), S(dx - dw / 2, dy + dh / 2)); return p; } };
}
function viewDyn(ctx, view, fn) {
  ctx.save(); ctx.translate(VW / 2, VH / 2); ctx.scale(view.z, view.z); ctx.translate(-view.cx, -view.cy); fn(); ctx.restore();
}
// side-view sandalled feet that step while walking (amt = how much the figure is walking, 0..1)
function stepFeet(ctx, Bn, s, fc, len, Lt, st, ph, amt) {
  const fy = len + 0.25;
  const X = (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s];
  const feet = [[-0.9, 0.35, 0, ph], [0.25, 1.45, 0.1, ph + Math.PI]];
  for (const [a, b, dy, p] of feet) {
    const fwd = Math.sin(p) * 0.55 * amt, lift = Math.max(0, Math.cos(p)) * 0.3 * amt;
    foot(ctx, X, s, st, Lt, [a + fwd, fy + dy - lift], [b + fwd, fy + dy + 0.15 - lift * 0.6], { h: 0.34 });
  }
}

S.street_knock = (ctx, W, t, lt, dur, p) => {
  // outside the prison: Asher walks the last steps along the wall to the door, raises his fist and
  // knocks three times on the planks (the door shudders and dust falls from the lintel); then the
  // grille slides open on the guard's eyes. He stands on the street at the door's sill, at the
  // door's scale, so his fist lands on the wood.
  const view = { z: 1.6, cx: 620, cy: 1020 };
  const kn = [1.9, 2.35, 2.8];
  let hit = 0, pulse = 0;
  for (const k of kn) {
    const d = lt - k;
    if (d >= 0 && d < 0.22) hit = Math.max(hit, 1 - d / 0.22);
    if (d > -0.2 && d <= 0) pulse = Math.max(pulse, 1 + d / 0.2);
    else if (d > 0 && d < 0.16) pulse = Math.max(pulse, 1 - d / 0.16);
  }
  const S2 = (x, y) => [(x - view.cx) * view.z + VW / 2, (y - view.cy) * view.z + VH / 2];
  drawCached(ctx, bgView('streetnd', (x) => BG.streetNight(x, { noDoor: true }), view, 2));
  viewDyn(ctx, view, () => BG.streetNightDyn(ctx, t));
  const f = 0.85 + 0.15 * L.fbm1(t * 3.3, 2);
  const sil = { side: -1, key: mix('#b4a094', '#c8b2a2', f), amb: '#44465a', shadow: 0.74, rim: '#ffb070', rimA: 0.7, rimSide: -1, wrap: 0.5 };
  // the door (shuddering under each knock) and, at the end, the guard's eyes in the grille
  const gr = smooth((lt - 3.35) / 0.4);
  ctx.save();
  ctx.translate(Math.sin(lt * 90) * 3 * hit, Math.cos(lt * 70) * 1.5 * hit);
  doorLeaf(ctx, view, 0, {
    grille: gr,
    eyes: (c, r) => {
      c.fillStyle = '#1a0e08'; c.fillRect(r.x0, r.y0, r.x1 - r.x0, r.y1 - r.y0);
      c.fillStyle = L.radial(c, (r.x0 + r.x1) / 2, r.y1, 0, (r.x1 - r.x0), [[0, rgba('#ff9a50', 0.5)], [1, rgba('#ff9a50', 0)]]);
      c.fillRect(r.x0, r.y0, r.x1 - r.x0, r.y1 - r.y0);
      const Lg = { side: 1, key: '#ffb070', amb: '#3a2a3a', shadow: 0.8, wrap: 0.6 };
      const F = W.state('guard', t, { default: { gx: 0.3, gy: 0.35, yaw: 0.15, pitch: 0.12 } });
      const hs = (r.x1 - r.x0) * 0.36;
      drawHead(c, { x: (r.x0 + r.x1) / 2 + hs * 0.1, y: r.y0 + (r.y1 - r.y0) * 0.95, s: hs, yaw: 0.15, pitch: 0.12, roll: 0 }, C.guard, Object.assign({}, F, { mouthOpen: 0 }), Lg, { t, noNeck: true });
    },
  });
  ctx.restore();
  // dust and grit shaken loose from the lintel and the planks
  for (let i = 0; i < 30; i++) {
    const k = kn[i % 3], tt = lt - k - L.hash01(i) * 0.1;
    if (tt < 0 || tt > 1.4) continue;
    const q = S2(360 + L.hash01(i * 7) * 380, 690 + L.hash01(i * 3) * 40);
    const x = q[0] + Math.sin(i + tt * 3) * 6, y = q[1] + tt * tt * 900;
    ctx.fillStyle = rgba('#d8c8a8', 0.55 * (1 - tt / 1.4));
    ctx.beginPath(); ctx.arc(x, y, 1.5 + 2 * L.hash01(i * 5), 0, L.TAU); ctx.fill();
  }
  // Asher walks in along the wall from the right, stops at the door, and knocks
  const walk = smooth(clamp(lt / 1.35));
  const moving = 1 - smooth(clamp((lt - 1.0) / 0.4));
  const sB = 47, footY = 1398;
  const bx = lerp(1180, 792, walk);
  const nk = S2(bx, footY - 9.45 * sB), sc = sB * view.z;
  const ph = lt * L.TAU / 1.05;
  const bob = Math.abs(Math.cos(ph)) * 0.08 * sc * moving;
  floorShadow(ctx, nk[0] + sc * 0.3, S2(0, footY)[1] + sc * 0.2, sc * 2.4, 0.5);
  const lk = looks({ gx: -0.6, gy: -0.1, yaw: -0.5, pitch: -0.05 }, {
    door: { gx: -0.65, gy: -0.12, yaw: -0.52, pitch: -0.05 }, grille: { gx: -0.5, gy: -0.62, yaw: -0.45, pitch: -0.2 },
  });
  actor(ctx, W, 'asher', t, { x: nk[0], y: nk[1] - bob, s: sc, facing: -1, by: -0.55, len: 9.2, swing: moving > 0.05 ? [0.22 * moving, ph] : null, armOffset: { f: [0.32 * pulse, -0.04 * pulse] } }, sil, lk,
    { afterTorso: (o) => stepFeet(ctx, o.neck, o.s, -1, 9.2, sil, C.asher, ph, moving) });
  BG.vignette(ctx, 0.5, '#02030a');
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
  // the bolt slides, the heavy door swings inward on its hinges, and the guard steps up into the
  // torchlit doorway
  const view = { z: 1.7, cx: 540, cy: 900 };
  drawCached(ctx, bgView('streetnd', (x) => BG.streetNight(x, { noDoor: true }), view, 4));
  const a = 1.32 * smooth((lt - 0.3) / 1.4);
  // the doorway: dark inside, warm with the guard's torch
  const dw = [];
  {
    const S = (bx, by) => [(bx - view.cx) * view.z + VW / 2, (by - view.cy) * view.z + VH / 2];
    const rr = 180;
    for (let i = 0; i <= 20; i++) {
      const u = 400 * i / 20, e = Math.min(u, 400 - u);
      const y = e >= rr ? 670 : 670 + rr - Math.sqrt(Math.max(0, rr * rr - (rr - e) * (rr - e)));
      dw.push(S(340 + u, y));
    }
    dw.push(S(740, 1370), S(340, 1370));
  }
  ctx.save();
  ctx.beginPath(); dw.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.closePath();
  ctx.fillStyle = '#070503'; ctx.fill();
  ctx.clip();
  const f = 0.85 + 0.15 * L.fbm1(t * 3, 6);
  ctx.fillStyle = L.radial(ctx, 760, 1080, 20, 700, [[0, rgba('#ff9a50', 0.45 * f)], [1, rgba('#ff9a50', 0)]]);
  ctx.fillRect(0, 0, VW, VH);
  const Lt = { side: 1, key: mix('#ffd2a8', '#ffe6cc', f), amb: '#4e4656', shadow: 0.78, rim: '#a8c0ff', rimA: 0.3, rimSide: -1, wrap: 0.6 };
  // he steps up out of the dark to the threshold: his whole figure stands in the doorway, at the door's
  // scale, feet on the sill
  const step = smooth((lt - 0.25) / 1.5);
  const lk = looks({ gx: 0.4, gy: 0.15, yaw: 0.25, pitch: 0.08 }, { asher: { gx: 0.45, gy: 0.2, yaw: 0.28, pitch: 0.1 } });
  const S1 = (bx, by) => [(bx - view.cx) * view.z + VW / 2, (by - view.cy) * view.z + VH / 2];
  // adult proportions (about seven and a half heads tall): a smaller head and body scale with full-length
  // legs, so he stands in the doorway like a man and not like a close-up on short legs
  const GL = 13.4;
  const sB = lerp(32, 35.5, step), footY = lerp(1318, 1350, step);
  const nk = S1(lerp(566, 548, step), footY - GL * sB), sc = sB * view.z;
  B.drawTorch(ctx, ...S1(712, 960), 34, t, Lt, { size: 1.1, seed: 3 });
  floorShadow(ctx, nk[0], S1(0, footY)[1] + 0.2 * sc, 2.6 * sc, 0.5);
  actor(ctx, W, 'guard', t, { x: nk[0], y: nk[1], s: sc, facing: 1, by: 0.3, len: GL }, Lt, lk,
    { afterTorso: (o) => standFeet(ctx, o.neck, o.s, 1, GL, Lt, C.guard) });
  ctx.restore();
  doorLeaf(ctx, view, a, { grille: 1 });
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
  recall: { gx: 0.25, gy: 0.45, yaw: 0.22, pitch: 0.12 },
  away: { gx: -0.5, gy: 0.2, yaw: -0.1, pitch: 0.05 },
}, ex || {}));
const asherLook = (ex) => looks({ gx: -0.4, gy: 0.35, yaw: -0.3, pitch: 0.12 }, Object.assign({
  paul: { gx: -0.58, gy: 0.22, yaw: -0.36, pitch: 0.08 }, bread: { gx: -0.2, gy: 0.9, yaw: -0.2, pitch: 0.3 },
  away: { gx: 0.55, gy: 0.1, yaw: 0.25, pitch: 0.02 }, away_down: { gx: 0.45, gy: 0.7, yaw: 0.2, pitch: 0.22 },
  guard: { gx: 0.75, gy: -0.1, yaw: 0.4, pitch: -0.03 }, down: { gx: -0.1, gy: 0.85, yaw: -0.15, pitch: 0.26 },
}, ex || {}));

// ---- the cell's small rough table: three warped planks on four splayed legs, a stretcher between
// them, the wood worn grey at the edges and stained where the jug stands. In the cell's background
// coordinates: centre x, floor line under the front legs, k = px per metre.
const TABLE = { x: 588, fy: 1512, k: 416 };
function roughTable(ctx, cx, fy, k, Lt) {
  const Wd = 0.5 * k, Ht = 0.46 * k, D = 0.1 * k, T = 0.05 * k, lg = 0.05 * k;
  const wood = L.mul('#6e4c30', Lt.key || '#fff'), woodD = L.mul('#3a2414', Lt.amb || '#fff'), woodL = mix(wood, '#e8d0b0', 0.18);
  const top = fy - Ht, x0 = cx - Wd / 2, x1 = cx + Wd / 2;
  ctx.save();
  ctx.lineJoin = 'round';
  // contact shadow on the floor
  ctx.fillStyle = L.radial(ctx, cx, fy - D * 0.4, 0, Wd * 0.7, [[0, rgba('#000000', 0.5)], [1, rgba('#000000', 0)]]);
  ctx.save(); ctx.translate(cx, fy - D * 0.4); ctx.scale(1, 0.22); ctx.beginPath(); ctx.arc(0, 0, Wd * 0.7, 0, L.TAU); ctx.restore(); ctx.fill();
  const leg = (xa, ya, xb, yb, w, c) => {
    ctx.fillStyle = c;
    ctx.beginPath(); ctx.moveTo(xa - w / 2, ya); ctx.lineTo(xa + w / 2, ya); ctx.lineTo(xb + w * 0.45, yb); ctx.lineTo(xb - w * 0.45, yb); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = rgba('#140a04', 0.8); ctx.lineWidth = k * 0.006; ctx.stroke();
  };
  // back legs (further away: higher feet, in shade), the back stretcher
  leg(x0 + 0.07 * k, top - D + T, x0 + 0.05 * k, fy - D * 0.85, lg * 0.9, woodD);
  leg(x1 - 0.07 * k, top - D + T, x1 - 0.05 * k, fy - D * 0.85, lg * 0.9, woodD);
  ctx.fillStyle = woodD; ctx.fillRect(x0 + 0.06 * k, fy - D * 0.85 - 0.16 * k, Wd - 0.12 * k, 0.03 * k);
  // front legs, splayed a little and not quite straight
  leg(x0 + 0.05 * k, top + T, x0 + 0.02 * k, fy, lg, mix(wood, woodD, 0.35));
  leg(x1 - 0.05 * k, top + T, x1 - 0.015 * k, fy + 0.01 * k, lg, mix(wood, woodD, 0.5));
  ctx.fillStyle = mix(wood, woodD, 0.45); ctx.fillRect(x0 + 0.04 * k, fy - 0.15 * k, Wd - 0.08 * k, 0.035 * k);
  ctx.strokeStyle = rgba('#140a04', 0.7); ctx.lineWidth = k * 0.005; ctx.strokeRect(x0 + 0.04 * k, fy - 0.15 * k, Wd - 0.08 * k, 0.035 * k);
  // the top: its upper face seen a little from above, then the front edge of the boards
  const tp = [[x0 + 0.02 * k, top - D], [x1 - 0.025 * k, top - D - 0.004 * k], [x1 + 0.004 * k, top], [x0 - 0.006 * k, top + 0.003 * k]];
  ctx.beginPath(); tp.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.closePath();
  ctx.fillStyle = L.linear(ctx, 0, top - D, 0, top, [[0, mix(wood, woodD, 0.25)], [1, woodL]]); ctx.fill();
  ctx.save(); ctx.clip();
  // three boards with dark gaps, grain, a knot, scuffs and the jug's old wet ring
  for (const v of [0.34, 0.68]) { ctx.strokeStyle = rgba('#1a0e06', 0.85); ctx.lineWidth = k * 0.006; ctx.beginPath(); ctx.moveTo(x0, top - D * (1 - v)); ctx.lineTo(x1, top - D * (1 - v) - 0.002 * k); ctx.stroke(); }
  const r = L.rng(41);
  for (let i = 0; i < 18; i++) { const y = top - D * r(), xa = x0 + r() * Wd; ctx.strokeStyle = rgba(r() < 0.5 ? '#2a1808' : '#a8805a', 0.25); ctx.lineWidth = k * 0.003; ctx.beginPath(); ctx.moveTo(xa, y); ctx.lineTo(xa + (0.05 + 0.15 * r()) * k, y + (r() - 0.5) * 0.004 * k); ctx.stroke(); }
  ctx.fillStyle = rgba('#1a0e06', 0.5); ctx.beginPath(); ctx.ellipse(x0 + Wd * 0.7, top - D * 0.5, 0.02 * k, 0.008 * k, 0, 0, L.TAU); ctx.fill();
  ctx.strokeStyle = rgba('#1a0e06', 0.22); ctx.lineWidth = k * 0.006; ctx.beginPath(); ctx.ellipse(x0 + Wd * 0.25, top - D * 0.5, 0.06 * k, 0.025 * k, 0, 0, L.TAU); ctx.stroke();
  ctx.restore();
  ctx.strokeStyle = rgba('#140a04', 0.85); ctx.lineWidth = k * 0.006; ctx.stroke();
  // front edge of the top: three board ends, the corner chipped
  ctx.fillStyle = L.linear(ctx, 0, top, 0, top + T, [[0, mix(wood, woodD, 0.2)], [1, woodD]]);
  ctx.beginPath(); ctx.moveTo(x0 - 0.006 * k, top + 0.003 * k); ctx.lineTo(x1 + 0.004 * k, top); ctx.lineTo(x1, top + T); ctx.lineTo(x0 + 0.02 * k, top + T + 0.004 * k); ctx.lineTo(x0, top + T * 0.5); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = rgba('#140a04', 0.85); ctx.lineWidth = k * 0.006; ctx.stroke();
  ctx.strokeStyle = rgba('#e8c8a0', 0.25); ctx.lineWidth = k * 0.004; ctx.beginPath(); ctx.moveTo(x0, top + 0.004 * k); ctx.lineTo(x1, top + 0.001 * k); ctx.stroke();
  ctx.restore();
  return { x0, x1, y: top - D * 0.45 };
}
// the table and what stands on it, through a view of the cell; o.bread: 0..1 = there (or a function
// drawing it), o.jug (default true)
function cellTable(ctx, view, Lt, o = {}) {
  const S2 = (x, y) => [(x - view.cx) * view.z + VW / 2, (y - view.cy) * view.z + VH / 2];
  const f = S2(TABLE.x, TABLE.fy), k = TABLE.k * view.z;
  const top = roughTable(ctx, f[0], f[1], k, Lt);
  const jh = 0.2 * k;
  if (o.jug !== false) B.drawJar(ctx, top.x0 + (top.x1 - top.x0) * 0.72, top.y - 0.42 * jh, jh, Lt);
  if (o.bread) B.drawBread(ctx, top.x0 + (top.x1 - top.x0) * 0.32, top.y - 0.06 * k * 0.9, 0.09 * k, Lt, { rot: 0.06 });
  return { top, k, S2 };
}

// The cell door's leaf (drawn by the background, see BG.cellDoorLeaf) swung in toward us by angle a, seen
// through a view of the cell: the vanishing point is the middle of the view
function cellDoorLeaf(ctx, view, a) {
  const S2 = (x, y) => [(x - view.cx) * view.z + VW / 2, (y - view.cy) * view.z + VH / 2];
  BG.cellDoorLeaf(ctx, a, S2, view.z, view.cx, view.cy);
}
// The open doorway: the dark recess of its frame, the corridor beyond (its far wall of rough stone warm with
// torchlight, its floor catching the light) and the light it throws into the cell; k fades the light in
// as the door opens
function cellDoorway(ctx, view, t, k = 1) {
  viewDyn(ctx, view, () => {
    const f = 0.85 + 0.15 * L.fbm1(t * 3, 6);
    ctx.fillStyle = '#060504'; ctx.fillRect(780, 480, 300, 1000);
    ctx.fillStyle = '#0c0907'; ctx.fillRect(800, 500, 260, 980);
    ctx.save(); ctx.beginPath(); ctx.rect(800, 500, 260, 980); ctx.clip();
    const r = L.rng(91);
    for (let y = 500, row = 0; y < 1420; y += 76, row++) {
      for (let x = 770 - (row % 2) * 58; x < 1060; x += 116) {
        const w = 108 + r() * 8, h = 68 + r() * 4;
        ctx.fillStyle = rgba(r() < 0.5 ? '#2e2018' : '#261a14', 0.75);
        ctx.beginPath(); ctx.roundRect(x + 4, y + 4, w - 8, h - 8, 7); ctx.fill();
        ctx.fillStyle = rgba('#0a0604', 0.35); ctx.fillRect(x + 4, y + h - 12, w - 8, 4);
      }
    }
    ctx.fillStyle = L.linear(ctx, 0, 1400, 0, 1480, [[0, '#1a120c'], [1, '#2a1c12']]); ctx.fillRect(800, 1410, 260, 70);
    ctx.restore();
    ctx.fillStyle = L.radial(ctx, 960, 860, 30, 560, [[0, rgba('#ff9a50', (0.3 + 0.2 * k) * f)], [0.6, rgba('#ff8a40', (0.1 + 0.08 * k) * f)], [1, rgba('#ff8a40', 0)]]);
    ctx.fillRect(800, 500, 260, 980);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = L.linear(ctx, 0, 1480, 0, 1900, [[0, rgba('#ff9a50', 0.22 * f * k)], [1, rgba('#ff9a50', 0)]]);
    ctx.beginPath(); ctx.moveTo(800, 1480); ctx.lineTo(1060, 1480); ctx.lineTo(1080, 1900); ctx.lineTo(620, 1900); ctx.closePath(); ctx.fill();
    ctx.restore();
  });
}
// the torch on the corridor's far wall, seen through the doorway (smaller: it is further off than the door)
function doorTorch(ctx, view, t, Lt) {
  viewDyn(ctx, view, () => B.drawTorch(ctx, 1028, 900, 26, t, Lt, { size: 1.15, seed: 5 }));
}
// draw fn clipped to the door opening (it gets the background-to-canvas mapping): whoever stands beyond the
// threshold is hidden by the wall and the frame around it, and by the door's foot while it is shut
function inDoorway(ctx, view, fn, foot = 1484) {
  const S2 = (x, y) => [(x - view.cx) * view.z + VW / 2, (y - view.cy) * view.z + VH / 2];
  const a = S2(800, 500), b = S2(1060, foot);
  ctx.save(); ctx.beginPath(); ctx.rect(a[0], a[1], b[0] - a[0], b[1] - a[1]); ctx.clip();
  fn(S2);
  ctx.restore();
}

S.cell_wide = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.0, cx: 540, cy: 960 };
  drawCached(ctx, cellBG(view, 0, { door: false }));
  // the door swings in on its hinges (the creak), and Asher is standing in the torchlit doorway
  const op = smooth(lt / 1.3);
  cellDoorway(ctx, view, t, op);
  BG.cellDyn(ctx, t, {});
  // Asher on the threshold: lit from behind by the corridor torch (a warm rim all down his right side)
  // and dimly from the front by the cell's window and lamp, so his face, clothes and the loaf still read
  const sil = { side: 1, key: '#a8968e', amb: '#3a3848', shadow: 0.72, rim: '#ffb070', rimA: 0.85, rimSide: 1, wrap: 0.35 };
  floorShadow(ctx, 905, 1481, 90, 0.5 * op);
  inDoorway(ctx, view, () => {
    doorTorch(ctx, view, t, sil);
    actor(ctx, W, 'asher', t, { x: 900, y: 688, s: 56, facing: -1, by: -0.4, len: 13.6 }, sil, asherLook(),
      { afterTorso: (o) => standFeet(ctx, o.neck, o.s, -1, 13.6, sil, C.asher) });
  }, lerp(1480, 1500, op));
  cellDoorLeaf(ctx, view, 1.5 * op);
  // the table with the jug, then Paul seated on his ledge
  cellTable(ctx, view, LIGHT.cellL, {});
  floorShadow(ctx, 330, 1560, 260, 0.5);
  B.drawChain(ctx, [150, 1150], [210, 1520], 30, LIGHT.cellL, 2.5, 12);
  const pl = Object.assign({}, cellPaul);
  stoneBench(ctx, [pl.x, pl.y], pl.s, 1, LIGHT.cellL, { right: 3.6 });
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
  // close on his face, but with the neck and the top of his robe in frame (never a floating head)
  actor(ctx, W, 'paul', t, { x: 520, y: 1700, s: 345, facing: 1, by: 0.3, len: 3, noArms: true }, LIGHT.cellL, paulLook(), { });
  BG.vignette(ctx, 0.55, '#020305');
};

S.cell_asher_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 820]);
  const F = W.state('asher', t, asherLook());
  const kneel = /kneel/.test(F.poseTo) ? 1 : 0;
  const view = kneel ? { z: 2.0, cx: 760, cy: 1100 } : { z: 2.0, cx: 760, cy: 560 };
  drawCached(ctx, cellBG(view, 12));
  cellDynView(ctx, t, view, {});
  if (t >= shotStart(W, 'cell_door_guard')) blurredLayer(ctx, 9, (o) => doorwayGuard(o, W, t, view));
  actor(ctx, W, 'asher', t, { x: 560, y: 1310, s: 185, facing: -1, by: -0.45, len: 5, lean: 0.03 }, LIGHT.cellR, asherLook(), {});
  BG.vignette(ctx, 0.4, '#020305');
};

// draw fn into a scratch layer the size of the frame (same transform) and lay it down blurred, for
// figures in an out-of-focus background
let scratch = null;
function blurredLayer(ctx, px, fn) {
  const cw = ctx.canvas.width, ch = ctx.canvas.height;
  if (!scratch || scratch.width !== cw || scratch.height !== ch) scratch = createCanvas(cw, ch);
  const o = scratch.getContext('2d');
  o.setTransform(1, 0, 0, 1, 0, 0); o.clearRect(0, 0, cw, ch);
  o.setTransform(ctx.getTransform());
  fn(o);
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.filter = `blur(${px * (global.RENDER_SCALE || 1)}px)`;
  ctx.drawImage(scratch, 0, 0);
  ctx.restore();
}
function shotStart(W, id) {
  W._starts = W._starts || {};
  if (!(id in W._starts)) { const q = W.tl.shots.find((x) => x.id === id); W._starts[id] = q ? q.start : 1e9; }
  return W._starts[id];
}
// After "Time's up" the cell door stands open and the guard waits in the doorway, spear in hand, watching
// them: torchlight from the corridor behind him. Drawn through the cell's view.
const guardInDoor = { side: 1, key: '#9a8a80', amb: '#34303e', shadow: 0.75, rim: '#ffb070', rimA: 0.8, rimSide: 1, wrap: 0.35 };
function doorwayGuard(ctx, W, t, view) {
  cellDoorway(ctx, view, t, 1);
  const Lg = guardInDoor;
  viewDyn(ctx, view, () => floorShadow(ctx, 922, 1481, 90, 0.5));
  inDoorway(ctx, view, (S2) => {
    doorTorch(ctx, view, t, Lg);
    const g = S2(922, 735);
    const lk = looks({ gx: -0.45, gy: 0.35, yaw: -0.3, pitch: 0.12 });
    actor(ctx, W, 'guard', t, { x: g[0], y: g[1], s: 56 * view.z, facing: -1, by: -0.35, len: 13.4 }, Lg, lk,
      { noTag: true, mod: (F) => { F.pose = 'guard_spear'; F.poseTo = 'guard_spear'; F.poseFrom = 'guard_spear'; F.poseK = 1; F.mouthOpen = 0; },
        afterTorso: (o) => standFeet(ctx, o.neck, o.s, -1, 13.4, Lg, C.guard) });
  }, 1500);
  cellDoorLeaf(ctx, view, 1.5);
}
// when the loaf leaves Asher's hand (tossed onto the table) and when he takes it up again
function breadTimes(W) {
  if (W._breadT) return W._breadT;
  const kf = W.actors.asher.kfs.find((k) => k.state.pose === 'drop_bread');
  const br = W.tl.shots.find((q) => q.id === 'cell_break_insert');
  W._breadT = { rel: kf ? kf.t + 0.3 : 1e9, land: kf ? kf.t + 0.72 : 1e9, gone: br ? br.start : 1e9 };
  return W._breadT;
}
function twoShot(ctx, W, t, lt, dur, p, warmK = 0) {
  const view = { z: 1.25, cx: 540, cy: 1000 };
  drawCached(ctx, cellBG(view, 4));
  cellDynView(ctx, t, view, { shaftA: 0.22 + warmK * 0.25, shaftColor: warmK > 0 ? '#fff0d0' : '#cfe0ff' });
  const Lp = warmK > 0 ? LIGHT.cellWarm : LIGHT.cellL;
  const FA = W.state('asher', t, asherLook());
  const kf = /kneel/.test(FA.poseFrom) ? 1 : 0, kt = /kneel/.test(FA.poseTo) ? 1 : 0;
  const kneel = lerp(kf, kt, smooth(FA.poseK));
  const FY = 1850;
  const pA = { x: 905, y: lerp(FY - 9.65 * 92, FY - 7.0 * 92, smooth(kneel)), s: 92, facing: -1, by: -0.45, len: 4.2 };
  // the rough table against the back wall between them, the jug on it; the loaf lands there when
  // Asher tosses it down and stays until he kneels to take it up again
  const bt = breadTimes(W);
  const onTable = t >= bt.land && t < bt.gone;
  if (t >= shotStart(W, 'cell_door_guard')) doorwayGuard(ctx, W, t, view);
  const tb = cellTable(ctx, view, Lp, { bread: onTable && p.breadOnFloor !== false });
  // Paul low-left, on the stone ledge
  floorShadow(ctx, 330, 1860, 300, 0.5);
  B.drawChain(ctx, [80, 1080], [215, 1560], 32, Lp, 2.5, 12);
  const pPaul = { x: 235, y: 1150, s: 100, facing: 1, by: 0.35, len: 4.4 };
  stoneBench(ctx, [pPaul.x, pPaul.y], pPaul.s, 1, Lp, { right: 3.75 });
  actor(ctx, W, 'paul', t, pPaul, Lp, paulLook({ asher: { gx: 0.55, gy: lerp(-0.6, -0.1, kneel), yaw: 0.35, pitch: lerp(-0.18, -0.02, kneel) } }),
    { afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, Lp) });
  // Asher right: standing or kneeling, well clear of Paul's feet
  floorShadow(ctx, 905, FY, 220, 0.45);
  actor(ctx, W, 'asher', t, pA, Lp, asherLook({ paul: { gx: -0.5, gy: lerp(0.6, 0.15, kneel), yaw: -0.35, pitch: lerp(0.2, 0.04, kneel) } }),
    { afterTorso: (o) => legsBlend(ctx, o.neck, o.s, -1, C.asher, Lp, kneel, FY, { by: o.by }), hideProps: t >= bt.rel ? ['bread'] : null });
  if (t >= bt.rel && t < bt.land) {
    // the toss: from his hand (where the pose had it at the moment he let go) in a low arc to the table
    const Fr = W.state('asher', bt.rel, asherLook());
    const w = poseBlend(Fr).n.w;
    const p0 = [pA.x - w[0] * pA.s, (FY - 9.65 * 92) + w[1] * pA.s - 0.25 * pA.s];
    const p1 = [tb.top.x0 + (tb.top.x1 - tb.top.x0) * 0.32, tb.top.y - 0.06 * tb.k * 0.9];
    const u = (t - bt.rel) / (bt.land - bt.rel);
    const x = lerp(p0[0], p1[0], u), y = lerp(p0[1], p1[1], u * u) - 70 * 4 * u * (1 - u);
    B.drawBread(ctx, x, y, lerp(0.78 * 92, 0.09 * tb.k, u), Lp, { rot: 0.06 - 0.9 * u * (1 - u) });
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
  cellTable(ctx, view, LIGHT.cellR, { bread: true });
  actor(ctx, W, 'asher', t, pA, LIGHT.cellR, asherLook({ bread: { gx: -0.3, gy: 0.95, yaw: -0.22, pitch: 0.35 } }),
    { afterTorso: (o) => legsBlend(ctx, o.neck, o.s, -1, C.asher, LIGHT.cellR, k, FY, { by: o.by }) });
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
  cellTable(ctx, view, Lt, {});
  B.drawChain(ctx, [60, 840], [240, 1400], 34, Lt, 2.5, 12);
  const pPaul = { x: 280, y: 900, s: 118, facing: 1, by: 0.35, len: 4.4 };
  stoneBench(ctx, [pPaul.x, pPaul.y], pPaul.s, 1, Lt, { right: 3.6 });
  actor(ctx, W, 'paul', t, pPaul, Lt, paulLook({ asher: { gx: 0.55, gy: -0.05, yaw: 0.35, pitch: -0.02 }, bread: { gx: 0.5, gy: 0.5, yaw: 0.3, pitch: 0.12 } }),
    { afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, Lt) });
  const pA = { x: 840, y: 1745 - 7.0 * 112, s: 112, facing: -1, by: -0.45, len: 4.2 };
  actor(ctx, W, 'asher', t, pA, Lt, asherLook({ paul: { gx: -0.55, gy: 0.1, yaw: -0.35, pitch: 0.02 } }),
    { afterTorso: (o) => kneelLegs(ctx, o.neck, o.s, -1, C.asher, Lt) });
  BG.vignette(ctx, 0.45, '#020305');
};

S.cell_door_guard = (ctx, W, t, lt, dur, p) => {
  // the guard flings the door open from the corridor (the bang) and stands on the threshold, framed by the
  // doorway and lit from behind by the corridor torch; we push in on him slowly
  camera(ctx, lt, dur, { zoom: [1.0, 1.12] }, [540, 720]);
  const view = { z: 2.4, cx: 930, cy: 810 };
  drawCached(ctx, cellBG(view, 5, { door: false }));
  // the door swings in fast, knocks against its stop and settles
  const u = clamp(lt / 0.34);
  const open = u < 1 ? smooth(u) * 1.62 : 1.62 - 0.12 * Math.sin(Math.min(1, (lt - 0.34) / 0.5) * Math.PI) * Math.exp(-(lt - 0.34) * 3);
  cellDoorway(ctx, view, t, Math.min(1, open / 0.8));
  const f = 0.85 + 0.15 * L.fbm1(t * 3, 6);
  const Lt = Object.assign({}, guardInDoor, { key: mix('#a89a90', '#b8aaa0', f), amb: '#3a3646', shadow: 0.72, rimA: 0.85 });
  const lk = looks({ gx: -0.4, gy: 0.4, yaw: -0.3, pitch: 0.15 }, { paul: { gx: -0.5, gy: 0.5, yaw: -0.32, pitch: 0.18 } });
  inDoorway(ctx, view, (S2) => {
    doorTorch(ctx, view, t, Lt);
    const g = S2(922, 735);
    // his free hand has just shoved the door: it comes back down to his side
    actor(ctx, W, 'guard', t, { x: g[0], y: g[1], s: 56 * view.z, facing: -1, by: -0.35, len: 13.4 }, Lt, lk,
      { mod: (F) => { F.pose = 'guard_spear'; F.poseFrom = 'guard_push'; F.poseTo = 'guard_spear'; F.poseK = smooth(clamp((lt - 0.3) / 0.9)); } });
  }, lerp(1480, 1500, Math.min(1, open)));
  cellDoorLeaf(ctx, view, open);
  BG.vignette(ctx, 0.5, '#020305');
};

S.cell_hands_grip = (ctx, W, t, lt, dur, p) => {
  // tight two-shot at eye level: Paul reaches across and takes Asher's hand; Asher's hand comes up off
  // his knee to meet it and Paul's closes round it (drawn over it)
  const view = { z: 1.9, cx: 560, cy: 1120 };
  drawCached(ctx, cellBG(view, 9));
  cellDynView(ctx, t, view, { shaftA: 0.3 });
  const Lt = LIGHT.cellWarm;
  const pA = { x: 875, y: 1150, s: 122, facing: -1, by: -0.4, len: 4.2 };
  const pPaul = { x: 215, y: 1170, s: 128, facing: 1, by: 0.4, len: 4.4 };
  const kP = smooth(clamp(lt / 1.2)), kA = smooth(clamp((lt - 0.25) / 0.95));
  const meet = [646, 1676];
  stoneBench(ctx, [pPaul.x, pPaul.y], pPaul.s, 1, Lt);
  actor(ctx, W, 'asher', t, Object.assign({}, pA, { reach: { f: [meet[0] + 18, meet[1] + 12, 'relax', kA] } }),
    Lt, asherLook({ paul: { gx: -0.62, gy: 0.05, yaw: -0.42, pitch: 0.02 } }), {
      mod: (F) => { F.poseFrom = 'kneel'; F.poseTo = 'kneel'; F.poseK = 1; },
      afterTorso: (o) => kneelLegs(ctx, o.neck, o.s, -1, C.asher, Lt),
    });
  actor(ctx, W, 'paul', t, Object.assign({}, pPaul, { reach: { f: [meet[0], meet[1], 'grip', kP] } }),
    Lt, paulLook({ asher: { gx: 0.62, gy: 0.0, yaw: 0.42, pitch: 0.0 } }), {
      mod: (F) => { F.poseFrom = 'rest'; F.poseTo = 'grip'; F.poseK = kP; },
      afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, Lt),
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

// temple guards standing behind Yosef, each with his inner hand closed round one of Yosef's upper
// arms (their own arms: the reach is from each guard's shoulder) and a spear in the other hand. Tired,
// irritated men doing a job they don't care for. y: Yosef's place, so the grips land on his arms.
// where the guards' hands rest: on top of Yosef's shoulders, one each side
function yosefGrips(y) {
  const sj = B.shoulderJoints([y.x, y.y], y.s, y.by, 0);
  return [[sj.L[0] + y.s * 0.12, sj.L[1] - y.s * 0.1], [sj.R[0] - y.s * 0.12, sj.R[1] - y.s * 0.1]];
}
function guardsBehind(ctx, W, t, yp, Lt, o = {}) {
  const dark = Object.assign({}, Lt, { key: mix(Lt.key || '#ffffff', '#40404a', 0.35) });
  const grips = yosefGrips(yp);
  const res = [];
  const spots = o.spots || [[-2.7, 1, 0.35], [2.9, -1, -0.38]];
  spots.forEach(([dx, fc, yaw]) => {
    const ys = yp.s;
    const pl = { x: yp.x + dx * ys, y: yp.y - 0.35 * ys, s: ys * 0.96, facing: fc, by: 0.3 * fc, len: 6, style: 'temple_guard' };
    const seed = dx > 0 ? 3 : 7;
    const F = extraF(t, seed, { yaw, gx: 0.3 * fc, gy: 0.2, pitch: 0.06, glance: 0.3, pose: 'guard_spear',
      F: { browFurrow: 0.62, browInner: -0.3, browHeight: -0.08, lid: 0.64 * F0(t, seed), lidLower: 0.22, mouthSmile: -0.42, mouthPress: 0.42 } });
    // the inner arm goes round behind Yosef: the shot draws only its forearm and hand, over him
    drawCharacter(ctx, 'guard', F, pl, dark, t, { sway: [0, 0], hideFar: true });
    res.push({ grip: grips[fc > 0 ? 0 : 1], out: -fc, ys, dark });
  });
  return res;
}
// blinks for the extras' heavy-lidded faces (keeps the lid value from extraF's blink)
function F0(t, seed) { const ph = (t * 0.27 + seed * 0.37) % 1; return ph < 0.04 ? 1 - Math.sin(ph / 0.04 * Math.PI) : 1; }
// each guard lays his inner hand on Yosef's shoulder (the left-hand guard his left hand, the right-hand
// guard his right): the forearm rises from the elbow at the guard's side, the palm rests on top of the
// shoulder and the fingers fall over its front, the back of the hand toward us
function guardGrips(ctx, gres) {
  if (!gres) return;
  const st = C.temple_guard;
  for (const { grip, out, ys, dark } of gres) {
    const E = [grip[0] + out * 1.3 * ys, grip[1] + 1.15 * ys];
    const f = [-out * 0.45, -0.5, 0.74], n = [-out * 0.1, -0.85, -0.5];
    closeArm(ctx, E, grip, ys * 0.92, st, dark, { hand: 'cup', f, n, right: out > 0, sleeve: st.cloth.tunic });
  }
}

// a hand gripping the edge of a door plank from behind it: the back of the hand shows in the gap,
// and the fingers come round the plank's edge (at x) and lie on its face, fingertips pointing away from
// the gap with their nails at the far ends (dir: -1 when the plank is to the right of the gap)
function edgeFingers(ctx, x, y, s, st, Lt, dir, pov = false) {
  const H = require('./hands');
  const skin = L.mul(st.skin, Lt.key || '#fff'), skinSh = L.mul(st.skinShadow, Lt.amb || '#fff');
  const lw = s * 0.022;
  const sizes = [0.95, 1.0, 0.96, 0.8];
  if (pov) {
    // seen from the gripping side (the boy's own view): the back of the hand on the plank, the fingers
    // reaching to its edge and bending round it out of sight, so no fingertip or nail shows
    const back = -dir;
    ctx.save();
    ctx.beginPath(); ctx.rect(dir > 0 ? x - s * 3 : x, y - s, s * 3, s * 3); ctx.clip();
    H.inkPart(ctx, (pp) => { H.capsule(pp, [x + back * s * 0.5, y - s * 0.02], s * 0.18, [x + back * s * 0.56, y + 0.9 * s + s * 0.06], s * 0.16); }, {
      fill: skin, line: st.line, lw,
      shade: (c) => { c.fillStyle = rgba(skinSh, 0.35); c.fillRect(x + back * s * 0.5 - s, y + s * 0.1, s * 2, s * 2); },
    });
    for (let i = 0; i < 4; i++) {
      const k = sizes[i], r = s * 0.12 * k, y0 = y + i * s * 0.3;
      const A = [x + back * s * 0.36, y0], Bp = [x + back * s * 0.1, y0 + s * 0.01], Cp = [x + dir * s * 0.06, y0 + s * 0.09];
      H.inkPart(ctx, (pp) => { H.capsule(pp, A, r, Bp, r * 0.95); H.capsule(pp, Bp, r * 0.95, Cp, r * 0.85); }, {
        fill: skin, line: st.line, lw,
        shade: (c) => { c.fillStyle = rgba(skinSh, 0.5); c.fillRect(Math.min(A[0], Cp[0]) - s, y0 + r * 0.3, s * 2, s); },
      });
      // the middle knuckle as light and shade, where the finger bends over the edge
      ctx.fillStyle = rgba(mix(skin, '#fff4ea', 0.4), 0.5);
      ctx.beginPath(); ctx.ellipse(Bp[0], Bp[1] - r * 0.25, r * 0.4, r * 0.28, 0, 0, L.TAU); ctx.fill();
    }
    ctx.restore();
    return;
  }
  const out = -dir; // the way the fingertips point, along the plank's face
  // the back of the hand, behind the plank, seen in the gap (mostly in shadow)
  const y1 = y + 3 * s * 0.3 + s * 0.12;
  H.inkPart(ctx, (pp) => { H.capsule(pp, [x - out * s * 0.2, y - s * 0.02], s * 0.17, [x - out * s * 0.24, y1 - s * 0.06], s * 0.15); }, {
    fill: mix(skin, skinSh, 0.45), line: st.line, lw,
    shade: (c) => { c.fillStyle = rgba(skinSh, 0.55); c.fillRect(x - out * s * 0.6 - s, y - s, s * 2, s * 3); },
  });
  for (let i = 0; i < 4; i++) {
    const k = sizes[i], r = s * 0.12 * k;
    const y0 = y + i * s * 0.3;
    // knuckle at the plank's edge, the finger along the face, the tip curling very slightly into it
    const A = [x - out * s * 0.05, y0], Bp = [x + out * s * 0.17 * k, y0 + s * 0.015], Cp = [x + out * s * 0.31 * k, y0 + s * 0.05];
    H.inkPart(ctx, (pp) => { H.capsule(pp, A, r, Bp, r * 0.92); H.capsule(pp, Bp, r * 0.92, Cp, r * 0.8); }, {
      fill: skin, line: st.line, lw,
      shade: (c) => { c.fillStyle = rgba(skinSh, 0.45); c.fillRect(Math.min(A[0], Cp[0]) - s, y0 + r * 0.35, s * 2, s); },
    });
    // the nail on the back of the fingertip, at the far end
    ctx.fillStyle = rgba(mix(skin, '#fff4f0', 0.45), 0.9);
    ctx.beginPath(); ctx.ellipse(Cp[0] - out * r * 0.25, Cp[1] - r * 0.12, r * 0.42, r * 0.34, 0, 0, L.TAU); ctx.fill();
    ctx.strokeStyle = rgba(st.line, 0.3); ctx.lineWidth = lw * 0.5; ctx.stroke();
    // the knuckle crease where the finger turns round the edge
    ctx.strokeStyle = rgba(skinSh, 0.6); ctx.lineWidth = lw * 0.7;
    ctx.beginPath(); ctx.moveTo(A[0] + out * r * 0.5, y0 - r * 0.55); ctx.quadraticCurveTo(A[0] + out * r * 0.8, y0, A[0] + out * r * 0.5, y0 + r * 0.55); ctx.stroke();
  }
}

S.jer_crack = (ctx, W, t, lt, dur, p) => {
  // the child's point of view: peeking through the gap of a half-open door at the torchlit street
  const gx = 400, gw = 280;
  ctx.save();
  ctx.beginPath(); ctx.rect(gx, 0, gw, VH); ctx.clip();
  drawCached(ctx, cached('jer', (x) => BG.jerusalemNight(x)));
  BG.jerusalemDyn(ctx, t, { torches: [[540, 740, 1]] });
  // a guard leading, Yosef with his hands bound being pulled along, Saul following with his warrant:
  // all walking (feet stepping, bodies bobbing and swaying, arms swinging where they are free)
  const sx = lerp(760, 200, lt / dur);
  const sil = { side: 1, key: '#a8968c', amb: '#40384c', shadow: 0.78, rim: '#ff9a50', rimA: 0.8, rimSide: 1, wrap: 0.35 };
  const walker = (who, x, y, s, ph, lk, o = {}) => {
    const bob = Math.abs(Math.cos(ph)) * 0.09 * s;
    const pl = Object.assign({ x, y: y - bob, s, facing: -1, by: -0.4, len: 9.5, swing: o.swing ? [0.25, ph] : null, lean: 0.03 * Math.sin(ph) }, o.place || {});
    const opt = { noTag: who === 'guard', afterTorso: (q) => stepFeet(ctx, q.neck, q.s, -1, 9.15, sil, C[o.style || who], ph, 1) };
    if (o.F) opt.mod = o.F;
    actor(ctx, W, who, t, pl, sil, lk, opt);
  };
  const ph = lt * L.TAU / 0.95;
  walker('guard', sx - 170, 968, 50, ph + 1.6, looks({ gx: -0.4, gy: 0, yaw: -0.4, pitch: 0 }),
    { swing: true, place: { style: 'temple_guard' }, style: 'temple_guard', F: (F) => { F.pose = 'walk'; F.poseTo = 'walk'; F.poseFrom = 'walk'; F.poseK = 1; F.browFurrow = 0.6; F.mouthSmile = -0.4; } });
  walker('yosef', sx, 973, 50, ph, looks({ gx: 0.5, gy: 0, yaw: 0.4, pitch: 0 }));
  walker('saul', sx + 190, 948, 52, ph + 2.6, looks({ gx: -0.5, gy: 0, yaw: -0.4, pitch: 0 }));
  ctx.restore();
  doorPlanks(ctx, 0, gx, t);
  doorPlanks(ctx, gx + gw, VW, t);
  gapGlow(ctx, gx, -1, t);
  gapGlow(ctx, gx + gw, 1, t);
  // a small hand gripping the door edge
  edgeFingers(ctx, gx - 6, 1150, 150, C.child, { key: '#d8a070', amb: '#5a4060' }, 1, true);
  BG.vignette(ctx, 0.45, '#010205');
};

S.jer_child = (ctx, W, t, lt, dur, p) => {
  // the boy behind the door, his face caught in the strip of torchlight from the gap
  ctx.fillStyle = '#0c0a0e'; ctx.fillRect(0, 0, VW, VH);
  const gx = 330, gw = 470;
  const Lt = { side: 1, key: '#ffe0c0', amb: '#4e4a62', shadow: 0.8, rim: '#ffa060', rimA: 0.5, rimSide: 1, wrap: 0.6 };
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
  const yp = { x: 560, y: 1110, s: 150, facing: 1, by: 0.55, len: 7 };
  // the guards stand close behind him; their inner arms are out of sight behind his back
  guardsBehind(ctx, W, t, yp, LIGHT.jer);
  actor(ctx, W, 'yosef', t, yp, LIGHT.jer, lk);
  BG.vignette(ctx, 0.5, '#010205');
};

S.jer_saul = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('jer', (x) => BG.jerusalemNight(x), { z: 1.6, cx: 360, cy: 800 }, 12));
  const f = 0.8 + 0.2 * L.fbm1(t * 3, 3);
  const Lt = Object.assign({}, LIGHT.jer, { key: mix('#ffcfa6', '#ffe4c8', f * 0.6) });
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
  const lk = looks({ gx: -0.3, gy: 0.05, yaw: -0.16, pitch: 0.02 }, { paul: { gx: -0.32, gy: 0.06, yaw: -0.18, pitch: 0.03 },
    away: { gx: 0.5, gy: 0.1, yaw: 0.35, pitch: 0.04 }, son: { gx: -0.7, gy: 0.12, yaw: -0.45, pitch: 0.05 } });
  const yp = { x: 660, y: 1330, s: 190, facing: -1, by: -0.15, len: 5 };
  guardsBehind(ctx, W, t, yp, LIGHT.jer, { spots: [[-2.6, 1, 0.3], [2.5, -1, -0.32]] });
  actor(ctx, W, 'yosef', t, yp, LIGHT.jer, lk);
  // young Paul from behind, out of focus in the foreground: his balding head with its dark fringe, the
  // white mantle with its blue stripe over the olive tunic
  ctx.save();
  ctx.filter = 'blur(5px)';
  // shoulders: the olive tunic, the white mantle over the near shoulder, its blue stripe
  ctx.fillStyle = '#4e4f2e';
  ctx.beginPath(); ctx.moveTo(-220, 1920); ctx.quadraticCurveTo(-140, 1200, 110, 1140); ctx.quadraticCurveTo(400, 1130, 500, 1920); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#c4bba8';
  ctx.beginPath(); ctx.moveTo(-60, 1920); ctx.quadraticCurveTo(40, 1300, 300, 1180); ctx.quadraticCurveTo(420, 1300, 470, 1920); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#2d4f8a'; ctx.lineWidth = 26;
  ctx.beginPath(); ctx.moveTo(40, 1920); ctx.quadraticCurveTo(120, 1420, 300, 1210); ctx.stroke();
  // the neck and the back of the head: bare crown, a dark fringe of hair round the back and over the ear
  ctx.fillStyle = '#8a6450';
  ctx.beginPath(); ctx.moveTo(30, 1180); ctx.lineTo(60, 1010); ctx.lineTo(230, 1010); ctx.lineTo(250, 1180); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#a77a60';
  ctx.beginPath(); ctx.ellipse(135, 860, 205, 245, 0.15, 0, L.TAU); ctx.fill();
  ctx.fillStyle = L.radial(ctx, 230, 760, 10, 220, [[0, rgba('#e8c0a0', 0.55)], [1, rgba('#e8c0a0', 0)]]);
  ctx.beginPath(); ctx.ellipse(135, 860, 205, 245, 0.15, 0, L.TAU); ctx.fill();
  ctx.fillStyle = '#2a1d16';
  ctx.beginPath(); ctx.moveTo(-60, 880); ctx.quadraticCurveTo(-40, 1080, 130, 1100); ctx.quadraticCurveTo(300, 1090, 335, 900);
  ctx.quadraticCurveTo(300, 1000, 135, 1015); ctx.quadraticCurveTo(-10, 1000, -60, 880); ctx.closePath(); ctx.fill();
  // the ear, and the torch's warm rim along his head
  ctx.fillStyle = '#9a6a52';
  ctx.beginPath(); ctx.ellipse(330, 905, 34, 62, 0.2, 0, L.TAU); ctx.fill();
  ctx.strokeStyle = rgba('#ff9a50', 0.55); ctx.lineWidth = 10;
  ctx.beginPath(); ctx.ellipse(135, 860, 210, 250, 0.15, -1.2, 0.4); ctx.stroke();
  ctx.restore();
  BG.vignette(ctx, 0.5, '#010205');
};

// They march Yosef away down the street, out of the town: a guard leading, Yosef with his bound hands, a
// guard at his back, and young Paul following. The boy stands in the doorway of their house with his face
// in his hands; Paul looks back at him over his shoulder as he walks.
S.jer_walk = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.3, cx: 620, cy: 1250 };
  const S2 = (x, y) => [(x - view.cx) * view.z + VW / 2, (y - view.cy) * view.z + VH / 2];
  drawCached(ctx, bgView('jer', (x) => BG.jerusalemNight(x), view, 3));
  viewDyn(ctx, view, () => BG.jerusalemDyn(ctx, t, { torches: [[540, 740, 1]] }));
  const sil = { side: 1, key: '#b4a298', amb: '#463e52', shadow: 0.74, rim: '#ff9a50', rimA: 0.8, rimSide: 1, wrap: 0.4 };
  // the boy in the doorway (the house door), lit from inside
  const dz = S2(870, 1440), cs = 36 * view.z;
  ctx.save();
  const dr = [S2(752, 885), S2(992, 1440)];
  ctx.fillStyle = '#0c0a10'; ctx.fillRect(dr[0][0], dr[0][1], dr[1][0] - dr[0][0], dr[1][1] - dr[0][1]);
  ctx.fillStyle = L.radial(ctx, dz[0], dz[1] - 200, 20, 360, [[0, rgba('#ffa860', 0.35)], [1, rgba('#ffa860', 0)]]);
  ctx.fillRect(dr[0][0], dr[0][1], dr[1][0] - dr[0][0], dr[1][1] - dr[0][1]);
  ctx.beginPath(); ctx.rect(dr[0][0], dr[0][1], dr[1][0] - dr[0][0], dr[1][1] - dr[0][1] + 4); ctx.clip();
  actor(ctx, W, 'child', t, { x: dz[0], y: dz[1] - 9.0 * cs, s: cs / 0.8, facing: -1, by: -0.25, len: 9.0 }, sil,
    looks({ gx: -0.2, gy: 0.7, yaw: -0.12, pitch: 0.3 }), { noTag: true, afterTorso: (o) => standFeet(ctx, o.neck, o.s, -1, 9.0, sil, C.child) });
  ctx.restore();
  // the procession walks left along the street, a little away from us
  const ph = lt * L.TAU / 1.0;
  const walker = (who, bx, by0, bs, phase, lk, o = {}) => {
    const k = lt / dur;
    const x = bx - 470 * k, y = by0 - 40 * k, sB = bs * (1 - 0.08 * k);
    const nk = S2(x, y - 9.4 * sB), sc = sB * view.z;
    const bob = Math.abs(Math.cos(phase)) * 0.08 * sc;
    floorShadow(ctx, nk[0], S2(0, y)[1] + 0.2 * sc, 2.4 * sc, 0.45);
    const opt = { noTag: true, afterTorso: (q) => stepFeet(ctx, q.neck, q.s, -1, 9.15, sil, C[o.style || who], phase, 1) };
    if (o.F) opt.mod = o.F;
    actor(ctx, W, who, t, Object.assign({ x: nk[0], y: nk[1] - bob, s: sc, facing: -1, by: -0.52, len: 9.4, swing: o.swing ? [0.22, phase] : null }, o.place || {}), sil, lk, opt);
  };
  const guardF = (F) => { F.pose = 'walk'; F.poseTo = 'walk'; F.poseFrom = 'walk'; F.poseK = 1; F.browFurrow = 0.6; F.mouthSmile = -0.4; };
  // in single file, a stride or two apart (the far ones a little further back on the street)
  walker('guard', 330, 1668, 47, ph + 1.6, looks({ gx: -0.5, gy: 0, yaw: -0.45, pitch: 0 }), { swing: true, style: 'temple_guard', place: { style: 'temple_guard' }, F: guardF });
  walker('yosef', 545, 1680, 48, ph, looks({ gx: -0.35, gy: 0.35, yaw: -0.35, pitch: 0.12 }));
  walker('guard', 745, 1694, 49, ph + 0.8, looks({ gx: -0.5, gy: 0, yaw: -0.45, pitch: 0 }), { swing: true, style: 'temple_guard', place: { style: 'temple_guard' }, F: guardF });
  // Paul behind them, looking back over his shoulder at the boy
  walker('saul', 955, 1730, 51, ph + 2.4, looks({ gx: -0.5, gy: 0.05, yaw: -0.45, pitch: 0.02 }, { ahead: { gx: -0.5, gy: 0.05, yaw: -0.45, pitch: 0.02 }, back: { gx: 0.8, gy: 0.15, yaw: 0.55, pitch: 0.05 } }), { swing: true });
  BG.vignette(ctx, 0.5, '#010205');
};

// Closer, travelling with Paul as he walks behind the guards: his head turned back over his shoulder to
// the house, his face sad; then he looks down and walks on
// young Paul, as in his first close shot: he raises his free hand and waves Yosef away to the guards
S.jer_saul_order = (ctx, W, t, lt, dur, p) => S.jer_saul(ctx, W, t, lt, dur, p);

S.jer_saul_walk = (ctx, W, t, lt, dur, p) => {
  // the wall slides by behind him as we travel with him (one blurred background, panned)
  const img = bgView('jer', (x) => BG.jerusalemNight(x), { z: 1.7, cx: 690, cy: 1050 }, 10);
  ctx.drawImage(img, lerp(-70, 70, lt / dur) - 0.07 * VW, -0.07 * VH, VW * 1.14, VH * 1.14);
  const f = 0.8 + 0.2 * L.fbm1(t * 3, 3);
  const Lt = Object.assign({}, LIGHT.jer, { key: mix('#ffcfa6', '#ffe4c8', f * 0.6) });
  const ph = lt * L.TAU / 1.0;
  const bob = Math.abs(Math.cos(ph)) * 0.06 * 170;
  const lk = looks({ gx: -0.5, gy: 0.1, yaw: -0.4, pitch: 0.04 }, { back: { gx: 0.75, gy: 0.15, yaw: 0.5, pitch: 0.05 }, down: { gx: -0.2, gy: 0.75, yaw: -0.25, pitch: 0.24 } });
  actor(ctx, W, 'saul', t, { x: 560, y: 1240 - bob, s: 170, facing: -1, by: -0.3, len: 5, swing: [0.18, ph] }, Lt, lk, { noTag: true });
  BG.vignette(ctx, 0.45, '#010205');
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
  actor(ctx, W, 'saul', t, pS, Lt, looks({ gx: 0, gy: 0.7, yaw: 0.1, pitch: 0.28 }, { down: { gx: 0, gy: 0.8, yaw: 0.1, pitch: 0.3 }, up: { gx: 0.1, gy: -0.7, yaw: 0.14, pitch: -0.16 } }),
    { afterTorso: (o) => kneelLegs(ctx, o.neck, o.s, 1, C.saul, Lt, { noFeet: true }) });
  BG.dust(ctx, t, { x: 100, y: 900, w: 880, h: 900 }, 24, '#fff4d0', 33, 0.6, 3.5);
};

S.dam_jesus = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 760]);
  BG.heavenLight(ctx, t, { x: 540, y: 560 });
  const Lt = LIGHT.divine;
  const lk = looks({ gx: 0, gy: 0.6, yaw: 0.0, pitch: 0.22 }, { down: { gx: 0.0, gy: 0.65, yaw: 0.02, pitch: 0.24 }, cam: { gx: 0, gy: 0.1, yaw: 0, pitch: 0.05 },
    sky: { gx: 0.08, gy: -0.85, yaw: 0.06, pitch: -0.3 } });
  halo(ctx, 540, 1120 - 2.2 * 128 - 36, 128, 1);
  actor(ctx, W, 'jesus', t, { x: 540, y: 1120, s: 128, facing: 1, by: 0.0, len: 8.8 }, Lt, lk);
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
  // Saul's right hand reaches up from below, palm up; Jesus' right hand reaches down from above, palm
  // down over it, as if to take hold of it and lift him. They draw closer through the whole of Paul's
  // words, slower and slower, and the shot ends with the smallest gap still between them: they never
  // touch. (Saul's olive sleeve, Jesus' cream one.)
  const u = clamp(lt / dur), k = 1 - Math.pow(1 - u, 1.7);
  // the light gathers where the hands are about to meet (behind them, so both hands stay clear)
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 560, 1090, 300 + 140 * k, '#ffffff', 0.14 + 0.22 * k);
  ctx.restore();
  closeArm(ctx, [-60, 1960], [lerp(240, 272, k), lerp(1570, 1280, k)], 200, C.saul, LIGHT.lightUp,
    { hand: 'offer', f: [0.93, 0.32, 0.15], n: [-0.3, 0.94, -0.05], right: true, sleeve: C.saul.cloth.tunic });
  closeArm(ctx, [1140, 200], [lerp(880, 838, k), lerp(630, 895, k)], 200, C.jesus, Lt,
    { hand: 'relax', f: [-0.94, -0.25, 0.2], n: [-0.24, 0.97, 0.05].map((v) => -v), right: true, sleeve: C.jesus.cloth.tunic, loose: 1 });
};

// ---------------------------------------------------------- DAWN
S.dawn_road = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.04] }, [600, 1050]);
  drawCached(ctx, cached('dawn', (x) => BG.dawnRoad(x)));
  BG.dawnDyn(ctx, t);
  // the soldiers leading Paul away down the road into the sunrise: they start near and walk away,
  // growing smaller, all through the narration
  const hz = 1080, u = clamp(lt / dur);
  const group = [[-0.9, 0.0, 1.0], [0.85, 0.15, 1.0], [0.0, 0.35, 0.92, true], [-0.6, 0.9, 1.0], [0.7, 1.05, 1.0], [-0.15, 1.6, 0.97], [0.45, 1.9, 1.0]];
  const fig = [];
  for (let i = 0; i < group.length; i++) {
    const [lat, back, hk, paul] = group[i];
    const d = 3.6 + back + u * 13;
    fig.push({ i, lat, d, hk, paul });
  }
  fig.sort((a, b) => b.d - a.d);
  for (const f of fig) {
    const y = hz + 820 / f.d, h = 330 / f.d * f.hk, x = 600 + f.lat * 260 / f.d;
    const ph = lt * 5.0 + f.i * 1.3;
    const bob = Math.abs(Math.cos(ph)) * h * 0.03;
    const body = f.paul ? '#5a4440' : '#3a2826', rim = rgba('#ffc070', 0.6);
    ctx.fillStyle = body;
    // head (Paul bare-headed and bowed; the soldiers helmeted)
    ctx.beginPath(); ctx.ellipse(x, y - h - bob, h * 0.15, h * 0.18, 0, 0, L.TAU); ctx.fill();
    if (!f.paul) { ctx.beginPath(); ctx.ellipse(x, y - h * 1.06 - bob, h * 0.17, h * 0.09, 0, Math.PI, 0); ctx.fill(); }
    // robe to the shins over legs stepping under it (walking away: the planted foot is the lower one)
    ctx.beginPath(); ctx.moveTo(x - h * 0.19, y - h * 0.84 - bob); ctx.lineTo(x + h * 0.19, y - h * 0.84 - bob); ctx.lineTo(x + h * 0.24, y - h * 0.18 - bob); ctx.lineTo(x - h * 0.24, y - h * 0.18 - bob); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = body; ctx.lineCap = 'round'; ctx.lineWidth = Math.max(1.5, h * 0.085);
    for (const sd of [-1, 1]) {
      const st2 = Math.sin(ph) * sd, lift = Math.max(0, -Math.cos(ph) * sd) * h * 0.07;
      ctx.beginPath(); ctx.moveTo(x + sd * h * 0.08, y - h * 0.22 - bob); ctx.lineTo(x + sd * h * 0.09, y - st2 * h * 0.045 - lift); ctx.stroke();
      if (!(f.paul)) { ctx.beginPath(); ctx.moveTo(x + sd * h * 0.2, y - h * 0.78 - bob); ctx.lineTo(x + sd * h * 0.26, y - h * 0.42 - bob + st2 * h * 0.05); ctx.stroke(); }
    }
    if (f.paul) {
      // Paul's hands bound in front; his white hair and beard catch the dawn
      ctx.fillStyle = rgba('#d8d0c8', 0.75); ctx.beginPath(); ctx.ellipse(x, y - h * 0.96 - bob, h * 0.1, h * 0.07, 0, 0, Math.PI); ctx.fill();
    } else {
      // a spear over the shoulder
      ctx.strokeStyle = body; ctx.lineWidth = Math.max(1, h * 0.03);
      ctx.beginPath(); ctx.moveTo(x + h * 0.22, y - h * 0.5 - bob); ctx.lineTo(x + h * 0.32, y - h * 1.55 - bob); ctx.stroke();
    }
    ctx.strokeStyle = rim; ctx.lineWidth = Math.max(1, h * 0.03);
    ctx.beginPath(); ctx.ellipse(x, y - h - bob, h * 0.15, h * 0.18, 0, -1.7, 0.2); ctx.stroke();
    // long shadows falling back toward us down the road
    ctx.fillStyle = rgba('#140a08', 0.35);
    ctx.beginPath(); ctx.moveTo(x - h * 0.15, y); ctx.lineTo(x + h * 0.15, y); ctx.lineTo(x + h * 0.25, y + h * 0.9); ctx.lineTo(x - h * 0.25, y + h * 0.9); ctx.closePath(); ctx.fill();
  }
  // Asher in the foreground, turned three-quarters toward the road so his face shows in profile,
  // watching them go; the half loaf rests in his palm
  const FY = 1895, s0 = 78;
  const pA = { x: 345, y: FY - 9.65 * s0, s: s0, facing: 1, by: 0.5, len: 4.2 };
  floorShadow(ctx, 375, FY, 230, 0.5);
  actor(ctx, W, 'asher', t, pA, LIGHT.dawn, looks({ gx: 0.6, gy: -0.05, yaw: 0.55, pitch: -0.02 }, { far: { gx: 0.62, gy: -0.02, yaw: 0.58, pitch: -0.03 } }),
    { afterTorso: (o) => legsBlend(ctx, o.neck, o.s, 1, C.asher, LIGHT.dawn, 0, FY, { by: o.by }) });
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
    ctx.globalCompositeOperation = 'color'; ctx.fillStyle = rgba('#b08050', 0.13); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'soft-light'; ctx.fillStyle = rgba('#ffcc88', 0.28); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'source-over'; BG.vignette(ctx, 0.5, '#1a0c04', 0.4);
  } else if (name === 'memory_blue') {
    ctx.globalCompositeOperation = 'color'; ctx.fillStyle = rgba('#5a6a9a', 0.15); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'source-over'; BG.vignette(ctx, 0.55, '#02040a', 0.38);
    // soft edge haze
    ctx.globalCompositeOperation = 'screen';
    ctx.fillStyle = L.radial(ctx, VW / 2, VH / 2, VH * 0.35, VH * 0.75, [[0, rgba('#8aa0d0', 0)], [1, rgba('#8aa0d0', 0.12)]]);
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
