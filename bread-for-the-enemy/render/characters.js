// Character designs: colours, face geometry, hair / beard / headwear painters.
'use strict';
const L = require('./lib');
const FACE = require('./face');
const { clamp, lerp, mix, rgba, shade } = L;

// ------------------------------------------------------------ point helpers
// pt spec: [x,y,z] head-space point, or {a:[x,y,z], d:[dx,dy], k:sway} hanging point
function mk(pr, extra) {
  const sw = (extra && extra.sway) || [0, 0];
  const s = pr.s;
  return (spec) => {
    if (Array.isArray(spec)) return pr.P(spec[0], spec[1], spec[2]);
    const a = pr.P(...spec.a);
    const k = spec.k == null ? 1 : spec.k;
    // hanging hair ignores most of the head roll: gravity
    return [a[0] + spec.d[0] * s + sw[0] * k * s, a[1] + spec.d[1] * s + sw[1] * k * s];
  };
}
function shape(ctx, pts, fill, stroke, lw, tension = 0.5) {
  ctx.beginPath();
  L.crPath(ctx, pts, true, tension);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.stroke(); }
}
function strands(ctx, list, col, lw) {
  for (const pts of list) L.strokeSmooth(ctx, pts, col, lw);
}
const lwOf = (pr, Lt) => (Lt.lineW || 1) * pr.s * 0.02;

// lit/shadow variants of a colour under the shot light
function lit(c, Lt) { return L.mul(c, Lt.key || '#ffffff'); }
function shd(c, Lt) { return L.mul(shade(c, 0.62), Lt.amb || '#ffffff'); }


// ------------------------------------------------------------ full hair cap
// Fills the whole projected skull (slightly enlarged for hair volume) EXCEPT the face
// region below the hairline, so no scalp can show through at any head angle.
// hairline: head-space points from the left temple across the forehead to the right temple.
function hairCap(ctx, pr, st, Lt, hairline, opt = {}) {
  const { P, Pc, s, H } = pr;
  const G = Object.assign({}, FACE.GEO, st.geo || {});
  const c = P(0, G.craniumY, -0.1);
  const R = G.craniumR * s * (opt.volume || 1.07);
  const col = opt.color || st.hair;
  // face area below the hairline (hole)
  const cw = G.cheekW;
  const right = [[0.96 * cw, -0.3, 0.12], [0.98 * cw, 0.2, 0.2], [0.9 * cw, 0.6, 0.2], [G.jawW, G.jawY, 0.24], [0.44, G.chinY - 0.2, 0.48], [0, G.chinY + 0.3, 0.68]];
  const left = right.slice(0, -1).reverse().map(([x, y, z]) => [-x, y, z]);
  const hl = hairline.map((p) => P(...p));
  const face = [...hl, ...right.map((p) => Pc(...p)), ...left.map((p) => Pc(...p))];
  const disk = () => { ctx.beginPath(); ctx.ellipse(c[0], c[1], R, R * 1.03, H.roll, 0, L.TAU); };
  ctx.save();
  disk();
  ctx.clip();
  ctx.beginPath();
  ctx.rect(c[0] - R * 2, c[1] - R * 2, R * 4, R * 4);
  L.crPath(ctx, face, true, 0.4);
  ctx.fillStyle = lit(col, Lt);
  ctx.fill('evenodd');
  // shadow side + under-volume shading follow the head form
  ctx.beginPath();
  ctx.rect(c[0] - R * 2, c[1] - R * 2, R * 4, R * 4);
  L.crPath(ctx, face, true, 0.4);
  ctx.clip('evenodd');
  FACE.shadowSide(ctx, pr, Lt, shd(col, Lt), -0.15);
  ctx.fillStyle = L.radial(ctx, c[0], c[1] - R * 0.6, R * 0.2, R * 1.4, [[0, rgba('#000000', 0)], [1, rgba('#000000', 0.28)]]);
  ctx.fillRect(c[0] - R * 2, c[1] - R * 2, R * 4, R * 4);
  if (opt.inner) opt.inner(ctx);
  ctx.restore();
  // silhouette edge over the top of the head (bumpy for curls)
  const lw = lwOf(pr, Lt);
  const a0 = opt.edgeFrom == null ? -2.1 : opt.edgeFrom, a1 = opt.edgeTo == null ? 2.1 : opt.edgeTo;
  if (opt.curls) {
    const n = 26;
    for (let i = 0; i <= n; i++) {
      const a = a0 + (a1 - a0) * (i / n) - H.roll;
      const x = c[0] + Math.sin(a) * R * 0.97, y = c[1] - Math.cos(a) * R * 1.0;
      const r = R * (0.07 + 0.015 * Math.sin(i * 2.3));
      ctx.fillStyle = mix(lit(col, Lt), shd(col, Lt), 0.35);
      ctx.beginPath(); ctx.arc(x, y, r, 0, L.TAU); ctx.fill();
      ctx.strokeStyle = rgba(st.hairLine, 0.55); ctx.lineWidth = lw * 0.6;
      ctx.beginPath(); ctx.arc(x, y, r, Math.PI + a - 1.2, Math.PI + a + 1.2, true); ctx.stroke();
    }
  } else {
    ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw * 0.9;
    ctx.beginPath(); ctx.ellipse(c[0], c[1], R, R * 1.03, H.roll, -Math.PI / 2 + a0, -Math.PI / 2 + a1); ctx.stroke();
  }
  // hairline edge
  ctx.strokeStyle = rgba(st.hairLine, 0.8); ctx.lineWidth = lw * 0.8;
  ctx.beginPath(); L.crPath(ctx, hl, false); ctx.stroke();
  return { c, R, hl };
}

// ======================================================================= JESUS
function jesusHairBack(ctx, pr, st, F, Lt, extra) {
  const q = mk(pr, extra);
  const c = st.hair;
  const pts = [
    q([0, -1.42, -0.1]), q([0.85, -1.05, -0.2]), q([1.22, -0.2, -0.3]),
    q({ a: [1.1, 0.5, -0.3], d: [0.35, 0.9], k: 0.5 }), q({ a: [1.1, 0.5, -0.3], d: [0.55, 2.0], k: 0.9 }),
    q({ a: [1.1, 0.5, -0.3], d: [0.35, 2.55], k: 1.1 }), q({ a: [0, 0.5, -0.5], d: [0, 2.2], k: 0.8 }),
    q({ a: [-1.1, 0.5, -0.3], d: [-0.35, 2.55], k: 1.1 }), q({ a: [-1.1, 0.5, -0.3], d: [-0.55, 2.0], k: 0.9 }),
    q({ a: [-1.1, 0.5, -0.3], d: [-0.35, 0.9], k: 0.5 }), q([-1.22, -0.2, -0.3]), q([-0.85, -1.05, -0.2]),
  ];
  shape(ctx, pts, mix(lit(c, Lt), shd(c, Lt), 0.55), st.hairLine, lwOf(pr, Lt));
  ctx.save();
  ctx.beginPath(); L.crPath(ctx, pts, true); ctx.clip();
  for (let i = 0; i < 9; i++) {
    const x = -1.2 + i * 0.3;
    L.strokeSmooth(ctx, [q([x * 0.7, -0.6, -0.3]), q({ a: [x, 0.5, -0.3], d: [x * 0.2, 1.2], k: 0.8 }), q({ a: [x, 0.5, -0.3], d: [x * 0.3, 2.3], k: 1.0 })],
      rgba(st.hairLine, 0.4), lwOf(pr, Lt) * 0.7);
  }
  ctx.restore();
}
function jesusHairFront(ctx, pr, st, F, Lt, extra) {
  const q = mk(pr, extra);
  const c = st.hair, lw = lwOf(pr, Lt);
  const side = Lt.side || -1;
  // full head of hair: centre-parted cap over the whole skull
  hairCap(ctx, pr, st, Lt, [[-0.98, -0.42, 0.3], [-0.78, -0.82, 0.58], [-0.42, -1.02, 0.82], [0, -1.08, 0.9], [0.42, -1.02, 0.82], [0.78, -0.82, 0.58], [0.98, -0.42, 0.3]], {
    volume: 1.09,
    inner: (cx) => {
      // flowing strands from the part toward the temples, and a soft sheen
      for (const sd of [-1, 1]) {
        for (let i = 0; i < 4; i++) {
          const k = i / 3;
          L.strokeSmooth(cx, [q([sd * 0.02, -1.42, 0.3]), q([sd * (0.3 + 0.25 * k), -1.25 + 0.05 * k, 0.6]), q([sd * (0.75 + 0.15 * k), -0.8 + 0.12 * k, 0.45])], rgba(st.hairLine, 0.35), lw * 0.6);
        }
        L.strokeSmooth(cx, [q([sd * 0.15, -1.38, 0.45]), q([sd * 0.45, -1.22, 0.58]), q([sd * 0.7, -1.0, 0.5])], rgba(shade(lit(c, Lt), 1.35), 0.35), pr.s * 0.07);
      }
    },
  });
  // centre part
  L.strokeSmooth(ctx, [q([0, -1.1, 0.9]), q([0, -1.32, 0.55]), q([0, -1.45, 0.15])], rgba(shade(lit(c, Lt), 0.55), 0.9), lw * 0.9);
  for (const sd of [-1, 1]) {
    const pts = [
      q([sd * 0.02, -1.36, 0.42]),
      q([sd * 0.32, -1.18, 0.7]), q([sd * 0.66, -0.9, 0.62]), q([sd * 0.9, -0.5, 0.42]),
      q([sd * 1.0, -0.05, 0.3]), q([sd * 1.02, 0.45, 0.2]),
      q({ a: [sd * 1.0, 0.8, 0.1], d: [sd * 0.08, 0.55], k: 0.6 }),
      q({ a: [sd * 1.0, 0.8, 0.1], d: [sd * 0.22, 1.4], k: 1.0 }),
      q({ a: [sd * 1.0, 0.8, 0.1], d: [sd * 0.12, 1.95], k: 1.2 }),
      q({ a: [sd * 1.0, 0.8, 0.1], d: [sd * 0.45, 1.75], k: 1.15 }),
      q({ a: [sd * 1.0, 0.8, 0.1], d: [sd * 0.62, 1.0], k: 0.9 }),
      q([sd * 1.3, 0.2, -0.05]), q([sd * 1.22, -0.55, 0.05]), q([sd * 0.98, -1.08, 0.1]), q([sd * 0.5, -1.4, 0.15]),
    ];
    const isShadow = sd === -side; // side away from light
    shape(ctx, pts, isShadow ? shd(c, Lt) : lit(c, Lt), st.hairLine, lw);
    // inner shadow along face edge
    ctx.save();
    ctx.beginPath(); L.crPath(ctx, pts, true); ctx.clip();
    const inner = [q([sd * 0.3, -1.15, 0.72]), q([sd * 0.7, -0.8, 0.6]), q([sd * 0.95, -0.3, 0.38]), q([sd * 1.02, 0.4, 0.2]),
      q({ a: [sd * 1.0, 0.8, 0.1], d: [sd * 0.1, 0.8], k: 0.8 })];
    L.strokeSmooth(ctx, inner, rgba(shd(c, Lt), 0.9), pr.s * 0.16);
    // soft sheen on the outer lock
    const hb = [q([sd * 0.86, -0.75, 0.42]), q([sd * 1.02, -0.2, 0.22]), q([sd * 1.05, 0.3, 0.12])];
    L.strokeSmooth(ctx, hb, rgba(shade(lit(c, Lt), 1.25), 0.22), pr.s * 0.08);
    // strands
    strands(ctx, [
      [q([sd * 0.1, -1.3, 0.5]), q([sd * 0.6, -0.95, 0.55]), q([sd * 1.08, -0.1, 0.2]), q({ a: [sd * 1.0, 0.8, 0.1], d: [sd * 0.3, 1.2], k: 1 })],
      [q([sd * 0.3, -1.3, 0.4]), q([sd * 1.0, -0.7, 0.2]), q([sd * 1.2, 0.2, 0.0]), q({ a: [sd * 1.0, 0.8, 0.1], d: [sd * 0.5, 1.5], k: 1.1 })],
    ], rgba(st.hairLine, 0.55), lw * 0.7);
    ctx.restore();
  }
}
function jesusHairShadow(ctx, pr, st, F, Lt, skinSh) {
  // shadow cast by hair onto forehead and temples
  const q = mk(pr, null);
  const pts = [q([-1.0, -0.45, 0.4]), q([-0.62, -0.78, 0.75]), q([-0.25, -1.0, 0.9]), q([0, -1.06, 0.95]),
    q([0.25, -1.0, 0.9]), q([0.62, -0.78, 0.75]), q([1.0, -0.45, 0.4]), q([1.1, -1.6, 0]), q([-1.1, -1.6, 0])];
  shape(ctx, pts, rgba(skinSh, 0.9), null, 0);
}
function beardFull(opts) {
  // generic beard: o.len (how far below chin), o.cheek (how high on cheeks), o.wave, colours from style
  return function (ctx, pr, st, F, Lt, layer, G) {
    const q = mk(pr, null);
    const lw = lwOf(pr, Lt);
    const jd = F.mouthOpen * 0.13;
    const len = opts.len || 0.15, ch = opts.cheek || 0.3, thick = opts.thick || 1;
    const col = st.beardColor || st.hair;
    const side = Lt.side || -1;
    if (layer === 'base') {
      const outer = [
        [-1.0, ch, 0.15], [-0.98, 0.6, 0.15], [-0.78, 0.98 + jd * 0.5, 0.25], [-0.5, 1.28 + jd, 0.45],
        [-0.22, 1.42 + len + jd, 0.62], [0, 1.47 + len + jd, 0.68], [0.22, 1.42 + len + jd, 0.62],
        [0.5, 1.28 + jd, 0.45], [0.78, 0.98 + jd * 0.5, 0.25], [0.98, 0.6, 0.15], [1.0, ch, 0.15],
      ];
      const my = G.mouthY;
      const inner = [
        [0.9, ch + 0.05, 0.3], [0.66, 0.58 * thick + 0.15, 0.62], [0.42, my - 0.02, 0.82], [0.3, my + 0.12 + jd * 0.6, 0.86],
        [0.14, my + 0.24 + jd, 0.9], [0, my + 0.21 + jd, 0.92], [-0.14, my + 0.24 + jd, 0.9],
        [-0.3, my + 0.12 + jd * 0.6, 0.86], [-0.42, my - 0.02, 0.82], [-0.66, 0.58 * thick + 0.15, 0.62], [-0.9, ch + 0.05, 0.3],
      ];
      const P = [...outer.map((p) => q(p)), ...inner.map((p) => q(p))];
      // build path: outer smooth then inner smooth back
      ctx.beginPath();
      L.crPath(ctx, outer.map((p) => q(p)), false);
      const inn = inner.map((p) => q(p));
      ctx.lineTo(inn[0][0], inn[0][1]);
      L.crPath({ moveTo: () => {}, bezierCurveTo: (...a) => ctx.bezierCurveTo(...a), closePath() {} }, inn, false);
      ctx.closePath();
      ctx.fillStyle = lit(col, Lt);
      ctx.fill();
      ctx.save();
      ctx.clip();
      // shadow half
      FACE.shadowSide(ctx, pr, Lt, shd(col, Lt));
      // hair texture strokes
      for (let i = 0; i < 9; i++) {
        const x = -0.8 + i * 0.2;
        const a = q([x, 0.75 + Math.abs(x) * -0.2, 0.6]);
        const b = q([x * 0.85, 1.3 + len - Math.abs(x) * 0.35 + jd, 0.6]);
        L.strokeSmooth(ctx, [a, b], rgba(shade(col, 0.5), 0.45), lw * 0.6);
      }
      ctx.restore();
      ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw * 0.8; ctx.stroke();
    } else {
      // mustache
      const my = G.mouthY;
      const sm = F.mouthSmile * 0.04;
      for (const sd of [-1, 1]) {
        const pts = [q([sd * 0.02, my - 0.17, 0.98]), q([sd * 0.2, my - 0.15 - sm, 0.94]), q([sd * 0.36, my - 0.02 - sm, 0.85]),
          q([sd * 0.42, my + 0.1, 0.8]), q([sd * 0.3, my - 0.05 - sm, 0.88]), q([sd * 0.12, my - 0.08, 0.95]), q([sd * 0.02, my - 0.09, 0.97])];
        shape(ctx, pts, sd === -side ? shd(col, Lt) : lit(col, Lt), st.hairLine, lw * 0.7);
      }
    }
  };
}

// ========================================================================= PAUL
function paulHairBack(ctx, pr, st, F, Lt, extra) {
  // beard hangs behind nothing; fringe behind ears
  const q = mk(pr, extra);
  const c = st.hair;
  for (const sd of [-1, 1]) {
    const pts = [q([sd * 0.9, -0.55, -0.1]), q([sd * 1.1, -0.2, -0.2]), q([sd * 1.14, 0.25, -0.25]),
      q([sd * 0.95, 0.65, -0.35]), q([sd * 0.7, 0.4, -0.6]), q([sd * 0.85, -0.3, -0.5])];
    shape(ctx, pts, shd(c, Lt), st.hairLine, lwOf(pr, Lt) * 0.8);
  }
}
function paulHairFront(ctx, pr, st, F, Lt, extra) {
  const q = mk(pr, extra);
  const c = st.hair, lw = lwOf(pr, Lt);
  const side = Lt.side || -1;
  for (const sd of [-1, 1]) {
    if (Math.sign(sd) === Math.sign(pr.H.yaw) && Math.abs(pr.H.yaw) > 0.4) continue;
    // wispy fringe above/behind the ear
    const pts = [q([sd * 0.86, -0.72, 0.18]), q([sd * 1.02, -0.5, 0.08]), q([sd * 1.1, -0.15, 0.0]), q([sd * 1.06, 0.12, -0.02]),
      q([sd * 1.17, -0.05, -0.12]), q([sd * 1.18, -0.4, -0.1]), q([sd * 1.08, -0.68, -0.05])];
    shape(ctx, pts, sd === -side ? shd(c, Lt) : lit(c, Lt), st.hairLine, lw * 0.8);
    strands(ctx, [[q([sd * 0.95, -0.6, 0.1]), q([sd * 1.1, -0.2, 0.0]), q([sd * 1.1, 0.05, -0.05])]], rgba(st.hairLine, 0.4), lw * 0.5);
  }
  // scalp shine
  const sh = q([-(Lt.side || -1) * -0.35, -1.0, 0.6]);
  ctx.fillStyle = rgba('#ffffff', 0.18);
  L.ellipse(ctx, sh[0], sh[1], pr.s * 0.22, pr.s * 0.1, -0.5);
  ctx.fill();
}
function paulBeard(ctx, pr, st, F, Lt, layer, G) {
  const q = mk(pr, null);
  const lw = lwOf(pr, Lt);
  const jd = F.mouthOpen * 0.13;
  const col = st.beardColor;
  const side = Lt.side || -1;
  const my = G.mouthY;
  if (layer === 'base') {
    // long flowing beard: attached along the jaw, hanging to chest
    const outer = [
      q([-1.02, 0.22, 0.12]), q([-1.0, 0.65, 0.12]), q([-0.86, 1.1 + jd * 0.5, 0.2]),
      q({ a: [-0.6, 1.3, 0.4], d: [-0.05, 0.55 + jd], k: 0.4 }), q({ a: [-0.3, 1.4, 0.55], d: [0.0, 0.95 + jd], k: 0.6 }),
      q({ a: [0, 1.45, 0.6], d: [0.0, 1.12 + jd], k: 0.7 }), q({ a: [0.3, 1.4, 0.55], d: [0.0, 0.95 + jd], k: 0.6 }),
      q({ a: [0.6, 1.3, 0.4], d: [0.05, 0.55 + jd], k: 0.4 }), q([0.86, 1.1 + jd * 0.5, 0.2]), q([1.0, 0.65, 0.12]), q([1.02, 0.22, 0.12]),
    ];
    const inner = [
      q([0.86, 0.28, 0.32]), q([0.66, 0.66, 0.62]), q([0.42, my, 0.82]), q([0.3, my + 0.14 + jd * 0.6, 0.86]),
      q([0.12, my + 0.25 + jd, 0.9]), q([0, my + 0.22 + jd, 0.92]), q([-0.12, my + 0.25 + jd, 0.9]),
      q([-0.3, my + 0.14 + jd * 0.6, 0.86]), q([-0.42, my, 0.82]), q([-0.66, 0.66, 0.62]), q([-0.86, 0.28, 0.32]),
    ];
    ctx.beginPath();
    L.crPath(ctx, outer, false);
    ctx.lineTo(inner[0][0], inner[0][1]);
    L.crPath({ moveTo: () => {}, bezierCurveTo: (...a) => ctx.bezierCurveTo(...a), closePath() {} }, inner, false);
    ctx.closePath();
    ctx.fillStyle = lit(col, Lt);
    ctx.fill();
    ctx.save();
    ctx.clip();
    FACE.shadowSide(ctx, pr, Lt, shd(col, Lt));
    // wavy strands
    for (let i = 0; i < 11; i++) {
      const x = -0.85 + i * 0.17;
      const a = q([x, 0.9, 0.55]);
      const b = q({ a: [x * 0.7, 1.35, 0.5], d: [x * 0.05, 0.5 + 0.4 * (1 - Math.abs(x)) + jd], k: 0.5 });
      const m = [(a[0] + b[0]) / 2 + pr.s * 0.04 * Math.sin(i * 1.7), (a[1] + b[1]) / 2];
      L.strokeSmooth(ctx, [a, m, b], rgba(shade(col, 0.55), 0.5), lw * 0.6);
    }
    ctx.restore();
    ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw * 0.8; ctx.stroke();
  } else {
    const sm = F.mouthSmile * 0.04;
    for (const sd of [-1, 1]) {
      const pts = [q([sd * 0.02, my - 0.18, 0.98]), q([sd * 0.22, my - 0.16 - sm, 0.94]), q([sd * 0.4, my + 0.0 - sm, 0.84]),
        q([sd * 0.46, my + 0.2, 0.78]), q([sd * 0.33, my + 0.02 - sm, 0.86]), q([sd * 0.12, my - 0.07, 0.95]), q([sd * 0.02, my - 0.08, 0.97])];
      shape(ctx, pts, sd === -side ? shd(col, Lt) : lit(col, Lt), st.hairLine, lw * 0.7);
    }
  }
}

// ======================================================================== ASHER
function curlyCap(opts) {
  // short curly hair covering the whole skull, curls along the silhouette and hairline
  const hl0 = opts.hairline || -0.86;
  const hairline = [[-0.99, -0.12, 0.2], [-0.96, -0.46, 0.38], [-0.74, -0.74 - (hl0 + 0.86) * 0.5, 0.62], [-0.38, hl0 - 0.04, 0.84],
    [0, hl0 - 0.06, 0.9], [0.38, hl0 - 0.04, 0.84], [0.74, -0.74 - (hl0 + 0.86) * 0.5, 0.62], [0.96, -0.46, 0.38], [0.99, -0.12, 0.2]];
  return {
    back(ctx, pr, st, F, Lt, extra) {
      // volume at the back of the head (behind the neck)
      const q = mk(pr, extra);
      const pts = [];
      for (let i = 0; i <= 16; i++) {
        const a = -Math.PI * 0.62 + (i / 16) * Math.PI * 1.24;
        const r = 1.1 + 0.05 * Math.sin(i * 2.7);
        pts.push(q([Math.sin(a) * r, -0.38 - Math.cos(a) * r * 1.02, -0.25]));
      }
      pts.push(q([0.9, 0.25, -0.4]), q([0, 0.35, -0.6]), q([-0.9, 0.25, -0.4]));
      shape(ctx, pts, shd(st.hair, Lt), st.hairLine, lwOf(pr, Lt) * 0.8);
    },
    front(ctx, pr, st, F, Lt, extra) {
      const q = mk(pr, extra);
      const lw = lwOf(pr, Lt);
      const cap = hairCap(ctx, pr, st, Lt, hairline, {
        volume: 1.08, curls: true, edgeFrom: -1.75, edgeTo: 1.75,
        inner: (cx) => {
          // curl swirls spread over the cap
          for (let i = 0; i < 22; i++) {
            const u = -0.85 + (i % 8) * 0.24 + (Math.floor(i / 8) % 2) * 0.12, v = -1.3 + Math.floor(i / 8) * 0.2;
            const p = q([u, v, 0.55]);
            cx.strokeStyle = rgba(st.hairLine, 0.45);
            cx.lineWidth = lw * 0.6;
            cx.beginPath(); cx.arc(p[0], p[1], pr.s * 0.07, 0.3 + i, 0.3 + i + 4.2); cx.stroke();
          }
          L.strokeSmooth(cx, [q([-0.5, -1.2, 0.6]), q([-0.1, -1.32, 0.62]), q([0.3, -1.27, 0.55])], rgba(shade(lit(st.hair, Lt), 1.5), 0.2), pr.s * 0.12);
        },
      });
      // curls along the forehead hairline
      for (let i = 2; i < hairline.length - 2; i++) {
        const p = q(hairline[i]);
        ctx.fillStyle = lit(st.hair, Lt);
        ctx.beginPath(); ctx.arc(p[0], p[1] + pr.s * 0.02, pr.s * 0.075, 0, L.TAU); ctx.fill();
        ctx.strokeStyle = rgba(st.hairLine, 0.55); ctx.lineWidth = lw * 0.6;
        ctx.beginPath(); ctx.arc(p[0], p[1] + pr.s * 0.02, pr.s * 0.075, 0.2, 2.9); ctx.stroke();
      }
    },
    shadow(ctx, pr, st, F, Lt, skinSh) {
      const q = mk(pr, null);
      const pts = hairline.map(([x, y, z]) => q([x, y + 0.14, z]));
      pts.push(q([1.2, -1.9, 0]), q([-1.2, -1.9, 0]));
      shape(ctx, pts, rgba(skinSh, 0.8), null, 0);
    },
  };
}

// ============================================================ HEAD CLOTH (Yosef, Elder, Saul travel)
function headCloth(opts) {
  return {
    back(ctx, pr, st, F, Lt, extra) {
      const q = mk(pr, extra);
      const c = opts.color;
      const pts = [q([0, -1.55, -0.1]), q([1.15, -1.0, -0.2]), q([1.32, 0.0, -0.3]),
        q({ a: [1.2, 0.6, -0.3], d: [0.35, 1.3], k: 0.6 }), q({ a: [1.2, 0.6, -0.3], d: [0.55, 2.4], k: 0.9 }),
        q({ a: [0, 0.6, -0.5], d: [0, 2.5], k: 0.6 }),
        q({ a: [-1.2, 0.6, -0.3], d: [-0.55, 2.4], k: 0.9 }), q({ a: [-1.2, 0.6, -0.3], d: [-0.35, 1.3], k: 0.6 }),
        q([-1.32, 0.0, -0.3]), q([-1.15, -1.0, -0.2])];
      shape(ctx, pts, shd(c, Lt), st.hairLine, lwOf(pr, Lt));
    },
    front(ctx, pr, st, F, Lt, extra) {
      const q = mk(pr, extra);
      const c = opts.color, lw = lwOf(pr, Lt);
      const side = Lt.side || -1;
      for (const sd of [-1, 1]) {
        const pts = [q([0, -1.5, 0.25]), q([sd * 0.5, -1.4, 0.45]), q([sd * 0.95, -1.0, 0.45]), q([sd * 1.12, -0.4, 0.3]),
          q([sd * 1.14, 0.3, 0.2]), q({ a: [sd * 1.1, 0.7, 0.1], d: [sd * 0.1, 0.8], k: 0.6 }),
          q({ a: [sd * 1.1, 0.7, 0.1], d: [sd * 0.25, 1.6], k: 0.9 }), q({ a: [sd * 1.1, 0.7, 0.1], d: [sd * 0.65, 1.5], k: 0.9 }),
          q({ a: [sd * 1.1, 0.7, 0.1], d: [sd * 0.55, 0.6], k: 0.6 }), q([sd * 1.38, 0.0, -0.05]), q([sd * 1.3, -0.8, 0.0]),
          q([sd * 0.8, -1.5, 0.1]), q([0, -1.68, 0.05])];
        shape(ctx, pts, sd === -side ? shd(c, Lt) : lit(c, Lt), st.hairLine, lw);
        // stripes
        if (opts.stripe) {
          ctx.save();
          ctx.beginPath(); L.crPath(ctx, pts, true); ctx.clip();
          for (const off of [0.12, 0.2]) {
            const sp = [q([sd * (0.5 + off), -1.45 + off * 0.2, 0.4]), q([sd * (1.0 + off), -0.95, 0.35]), q([sd * (1.18 + off), -0.3, 0.2]),
              q([sd * (1.2 + off), 0.35, 0.1]), q({ a: [sd * 1.1, 0.7, 0.1], d: [sd * (0.22 + off), 1.0], k: 0.7 })];
            L.strokeSmooth(ctx, sp, rgba(opts.stripe, 0.85), pr.s * 0.05);
          }
          ctx.restore();
        }
        // folds
        strands(ctx, [[q([sd * 0.6, -1.3, 0.45]), q([sd * 1.05, -0.6, 0.3]), q([sd * 1.15, 0.2, 0.15])]], rgba(st.hairLine, 0.35), lw * 0.6);
      }
      // band / cord over forehead
      if (opts.band) {
        const bp = [q([-1.05, -0.95, 0.4]), q([-0.5, -1.22, 0.75]), q([0, -1.28, 0.82]), q([0.5, -1.22, 0.75]), q([1.05, -0.95, 0.4])];
        L.strokeSmooth(ctx, bp, lit(opts.band, Lt), pr.s * 0.09);
        L.strokeSmooth(ctx, bp, rgba(st.hairLine, 0.5), lw * 0.5);
      }
    },
    shadow(ctx, pr, st, F, Lt, skinSh) {
      const q = mk(pr, null);
      const pts = [q([-1.05, -0.6, 0.4]), q([-0.5, -0.98, 0.8]), q([0, -1.05, 0.9]), q([0.5, -0.98, 0.8]), q([1.05, -0.6, 0.4]),
        q([1.2, -1.8, 0]), q([-1.2, -1.8, 0])];
      shape(ctx, pts, rgba(skinSh, 0.9), null, 0);
      for (const sd of [-1, 1]) {
        const p2 = [q([sd * 1.0, -0.6, 0.3]), q([sd * 0.86, 0.1, 0.4]), q([sd * 0.9, 0.7, 0.3]), q([sd * 1.3, 0.7, 0]), q([sd * 1.3, -0.6, 0])];
        shape(ctx, p2, rgba(skinSh, 0.7), null, 0);
      }
    },
  };
}

// ================================================================ GUARD helmet
function helmet() {
  return {
    back(ctx, pr, st, F, Lt, extra) {
      const q = mk(pr, extra);
      const pts = [q([-1.1, -0.5, -0.2]), q([-0.9, -1.25, -0.2]), q([0, -1.5, -0.2]), q([0.9, -1.25, -0.2]), q([1.1, -0.5, -0.2]),
        q([1.2, 0.35, -0.5]), q([0, 0.55, -0.7]), q([-1.2, 0.35, -0.5])];
      shape(ctx, pts, shd(st.metal, Lt), st.hairLine, lwOf(pr, Lt));
    },
    front(ctx, pr, st, F, Lt, extra) {
      const q = mk(pr, extra);
      const lw = lwOf(pr, Lt);
      const m = st.metal;
      const side = Lt.side || -1;
      // dome
      const dome = [];
      for (let i = 0; i <= 18; i++) {
        const a = -Math.PI * 0.55 + (i / 18) * Math.PI * 1.1;
        dome.push(q([Math.sin(a) * 1.1, -0.42 - Math.cos(a) * 1.12, 0.08 + Math.cos(a) * 0.5]));
      }
      const rim = [q([1.12, -0.62, 0.35]), q([0.6, -0.82, 0.85]), q([0, -0.88, 1.0]), q([-0.6, -0.82, 0.85]), q([-1.12, -0.62, 0.35])];
      ctx.beginPath(); L.crPath(ctx, [...dome, ...rim], true); ctx.fillStyle = lit(m, Lt); ctx.fill();
      ctx.save(); ctx.clip();
      FACE.shadowSide(ctx, pr, Lt, shd(m, Lt));
      const hl = [q([side * 0.55, -1.25, 0.5]), q([side * 0.25, -1.4, 0.6]), q([side * -0.1, -1.42, 0.6])];
      L.strokeSmooth(ctx, hl, rgba('#ffffff', 0.55), pr.s * 0.06);
      ctx.restore();
      ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw; ctx.stroke();
      // brow guard ridge
      const br = [q([-1.15, -0.62, 0.3]), q([-0.6, -0.86, 0.9]), q([0, -0.93, 1.05]), q([0.6, -0.86, 0.9]), q([1.15, -0.62, 0.3])];
      L.strokeSmooth(ctx, br, lit(shade(m, 1.15), Lt), pr.s * 0.1);
      L.strokeSmooth(ctx, br, rgba(st.hairLine, 0.7), lw * 0.5);
      // crest ridge
      L.strokeSmooth(ctx, [q([0, -0.9, 1.0]), q([0, -1.3, 0.62]), q([0, -1.52, 0.1])], rgba(shade(m, 0.6), 0.9), lw * 1.2);
      // cheek guards
      for (const sd of [-1, 1]) {
        if (Math.sign(sd) === Math.sign(pr.H.yaw) && Math.abs(pr.H.yaw) > 0.45) continue;
        const cg = [q([sd * 1.08, -0.55, 0.4]), q([sd * 0.86, -0.4, 0.55]), q([sd * 0.8, 0.2, 0.55]), q([sd * 0.72, 0.85, 0.42]),
          q([sd * 0.92, 0.95, 0.25]), q([sd * 1.08, 0.5, 0.15]), q([sd * 1.14, -0.2, 0.2])];
        shape(ctx, cg, sd === -side ? shd(m, Lt) : lit(m, Lt), st.hairLine, lw);
        const rv = q([sd * 0.93, 0.25, 0.42]);
        ctx.fillStyle = rgba('#fff2d0', 0.6); L.ellipse(ctx, rv[0], rv[1], pr.s * 0.03, pr.s * 0.03); ctx.fill();
      }
    },
    shadow(ctx, pr, st, F, Lt, skinSh) {
      const q = mk(pr, null);
      const pts = [q([-1.1, -0.45, 0.35]), q([-0.6, -0.62, 0.85]), q([0, -0.66, 1.0]), q([0.6, -0.62, 0.85]), q([1.1, -0.45, 0.35]),
        q([1.2, -1.8, 0]), q([-1.2, -1.8, 0])];
      shape(ctx, pts, rgba(skinSh, 0.95), null, 0);
    },
  };
}
function stubble(ctx, pr, st, F, Lt, layer, G) {
  if (layer !== 'base') return;
  const q = mk(pr, null);
  const jd = F.mouthOpen * 0.13;
  const pts = [q([-0.98, 0.3, 0.15]), q([-0.85, 0.9, 0.2]), q([-0.45, 1.25 + jd, 0.48]), q([0, 1.35 + jd, 0.68]), q([0.45, 1.25 + jd, 0.48]),
    q([0.85, 0.9, 0.2]), q([0.98, 0.3, 0.15]), q([0.6, 0.7, 0.65]), q([0.3, G.mouthY + 0.2 + jd, 0.86]), q([0, G.mouthY + 0.25 + jd, 0.9]),
    q([-0.3, G.mouthY + 0.2 + jd, 0.86]), q([-0.6, 0.7, 0.65])];
  shape(ctx, pts, rgba(st.beardColor || '#3a3030', 0.28), null, 0);
}

// ============================================================ styles
const C = {};
C.jesus = {
  name: 'jesus', skin: '#efc6a2', skinShadow: '#c58f74', line: '#3b2219', iris: '#6a4126', browColor: '#3a2416',
  hair: '#4a2e1e', hairLine: '#1e120c', beardColor: '#4a2e1e', lashW: 0.26, blush: 0.12,
  geo: { chinY: 1.36, jawW: 0.66, mouthW: 0.21 },
  hairBack: jesusHairBack, hairFront: jesusHairFront, hairShadow: jesusHairShadow, beard: beardFull({ len: 0.12, cheek: 0.25 }),
  beardHidesFolds: true,
  cloth: { tunic: '#efe5d3', mantle: '#8e2b2e', trim: '#c9a050', neck: 'v' },
};
C.paul = {
  name: 'paul', skin: '#dfae8a', skinShadow: '#a9725a', line: '#3a221a', iris: '#4e3a2c', browColor: '#c9c1b6',
  hair: '#d6d0c8', hairLine: '#4a3a32', beardColor: '#dcd6ce', bald: true, age: 1, bushyBrows: true, browW: 0.095,
  geo: { chinY: 1.3, jawW: 0.7, mouthW: 0.21, craniumR: 1.03 },
  hairBack: paulHairBack, hairFront: paulHairFront, beard: paulBeard, beardHidesFolds: false,
  cloth: { tunic: '#7d6b57', mantle: '#4f4336', trim: '#5f5244', neck: 'round' },
};
const asherCap = curlyCap({ hairline: -0.82 });
C.asher = {
  name: 'asher', skin: '#e2b08c', skinShadow: '#ae775d', line: '#33201a', iris: '#4a2f22', browColor: '#22160f',
  hair: '#2b1d16', hairLine: '#120a07', beardColor: '#2b1d16', age: 0.25, browW: 0.085,
  geo: { chinY: 1.34, jawW: 0.72, mouthW: 0.22 },
  hairBack: asherCap.back, hairFront: asherCap.front, hairShadow: asherCap.shadow, beard: beardFull({ len: 0.04, cheek: 0.35, thick: 1.05 }),
  beardHidesFolds: true,
  cloth: { tunic: '#3f4a5c', mantle: '#6a4a33', trim: '#2c2a2a', neck: 'round' },
};
const yosefCloth = headCloth({ color: '#d9cdb4', stripe: '#6a5440', band: '#3a2a22' });
C.yosef = {
  name: 'yosef', skin: '#e0ad88', skinShadow: '#a8725a', line: '#33201a', iris: '#3d2a1e', browColor: '#2a1d16',
  hair: '#2e211a', hairLine: '#140c08', beardColor: '#3a2c24', age: 0.4, browW: 0.08,
  geo: { chinY: 1.34, jawW: 0.7 },
  hairBack: yosefCloth.back, hairFront: yosefCloth.front, hairShadow: yosefCloth.shadow, beard: beardFull({ len: 0.22, cheek: 0.3 }),
  beardHidesFolds: true,
  cloth: { tunic: '#8b6f4f', mantle: '#5a4632', trim: '#3a2c22', neck: 'round' },
};
const saulCap = curlyCap({ hairline: -0.9 });
C.saul = {
  name: 'saul', skin: '#dcaa86', skinShadow: '#a26c55', line: '#2e1c16', iris: '#3a2a20', browColor: '#140c0a',
  hair: '#17110f', hairLine: '#050303', beardColor: '#17110f', age: 0.1, browW: 0.095,
  geo: { chinY: 1.32, jawW: 0.72, mouthW: 0.22 },
  hairBack: saulCap.back, hairFront: saulCap.front, hairShadow: saulCap.shadow, beard: beardFull({ len: 0.16, cheek: 0.28 }),
  beardHidesFolds: true,
  cloth: { tunic: '#2c2838', mantle: '#d8d2c2', trim: '#2d4f8a', neck: 'round' },
};
const saulTravel = headCloth({ color: '#c8b79a', stripe: '#2d4f8a', band: '#2a2020' });
C.saul_travel = Object.assign({}, C.saul, { hairBack: saulTravel.back, hairFront: saulTravel.front, hairShadow: saulTravel.shadow });
const childCap = curlyCap({ hairline: -0.62 });
C.child = {
  name: 'child', skin: '#ecbf9c', skinShadow: '#b98068', line: '#3a241c', iris: '#4a3020', browColor: '#2a1c14',
  hair: '#2d1e16', hairLine: '#120a07', child: true, blush: 0.35, browW: 0.06, lashW: 0.3, eyeScale: 1.42, irisR: 0.6,
  geo: { chinY: 1.08, jawW: 0.8, jawY: 0.78, mouthY: 0.7, mouthW: 0.14, eyeY: 0.12, eyeH: 1.35, eyeX: 0.47, noseY: 0.4, noseLen: 0.7, cheekW: 1.0 },
  hairBack: childCap.back, hairFront: childCap.front, hairShadow: childCap.shadow,
  cloth: { tunic: '#c7b08a', mantle: '#8a6e50', trim: '#6a5440', neck: 'round' },
};
const gh = helmet();
C.guard = {
  name: 'guard', skin: '#d9a582', skinShadow: '#9e6a52', line: '#2e1c16', iris: '#3a3a30', browColor: '#2a2018',
  hair: '#2a2018', hairLine: '#160e0a', beardColor: '#2a2018', metal: '#8a8d92', age: 0.35, browW: 0.09,
  geo: { chinY: 1.36, jawW: 0.76, mouthW: 0.22 },
  hairBack: gh.back, hairFront: gh.front, hairShadow: gh.shadow, beard: stubble,
  cloth: { tunic: '#8a2a22', mantle: '#5a3a2a', trim: '#8a8d92', neck: 'round', armor: true },
};
const elderCloth = headCloth({ color: '#eee6d6', stripe: '#2f3a66', band: null });
C.elder = {
  name: 'elder', skin: '#dcac8c', skinShadow: '#a3735e', line: '#3a241c', iris: '#40342c', browColor: '#e0dad2',
  hair: '#e6e0d8', hairLine: '#5a4a40', beardColor: '#ece6de', age: 0.9, bushyBrows: true, browW: 0.08,
  hairBack: elderCloth.back, hairFront: elderCloth.front, hairShadow: elderCloth.shadow, beard: beardFull({ len: 0.4, cheek: 0.28 }),
  beardHidesFolds: true,
  cloth: { tunic: '#e4dccb', mantle: '#b8a888', trim: '#2f3a66', neck: 'round' },
};

const phoebeVeil = headCloth({ color: '#3f6f86', stripe: '#e8d9b4', band: null });
C.phoebe = {
  name: 'phoebe', skin: '#e9bb98', skinShadow: '#bb826a', line: '#3a241c', iris: '#5a3a22', browColor: '#2a1a12',
  hair: '#2c1b14', hairLine: '#140a08', lashW: 0.34, eyeScale: 1.12, irisR: 0.56, browW: 0.05, blush: 0.34, lips: '#c76a64',
  adamsApple: false, age: 0.15,
  geo: { chinY: 1.22, jawW: 0.6, jawY: 0.86, mouthW: 0.18, mouthY: 0.8, eyeH: 1.15, browY: -0.37, noseLen: 0.82, cheekW: 0.95 },
  hairBack: phoebeVeil.back,
  hairFront(ctx, pr, st, F, Lt, extra) {
    hairCap(ctx, pr, st, Lt, [[-0.96, -0.3, 0.3], [-0.72, -0.78, 0.6], [-0.36, -0.98, 0.84], [0, -1.04, 0.9], [0.36, -0.98, 0.84], [0.72, -0.78, 0.6], [0.96, -0.3, 0.3]], { volume: 1.06 });
    phoebeVeil.front(ctx, pr, st, F, Lt, extra);
  },
  hairShadow: phoebeVeil.shadow,
  cloth: { tunic: '#b49a72', mantle: '#3f6f86', trim: '#e8d9b4', neck: 'round' },
};

module.exports = { C, mk, shape, lit, shd, lwOf, hairCap };
