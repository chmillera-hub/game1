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
// Catmull-Rom resampling of a head-space (x, y, z) polyline
function sample3(pts, per) {
  const n = pts.length, out = [];
  const get = (i) => pts[Math.max(0, Math.min(n - 1, i))];
  for (let i = 0; i < n - 1; i++) {
    const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
    for (let k = 0; k < per; k++) {
      const t = k / per, t2 = t * t, t3 = t2 * t;
      out.push([0, 1, 2].map((j) => 0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)));
    }
  }
  out.push(pts[n - 1]);
  return out;
}

// lit/shadow variants of a colour under the shot light
function lit(c, Lt) { return L.mul(c, Lt.key || '#ffffff'); }
function shd(c, Lt) { return L.mul(shade(c, 0.62), Lt.amb || '#ffffff'); }
// hair and beards: the shadow side is the same colour, only a little darker, with a soft edge,
// so a white beard reads as one white beard in light and shadow (never two colours)
function softShade(ctx, pr, Lt, col, k = 0.5) {
  const { P, s, H } = pr;
  const side = Lt.side || -1;
  const xt = FACE.terminatorX(H, Lt);
  const a = P(xt + side * 0.25, 0.6, 0.9), b = P(xt - side * 0.75, 0.6, 0.9);
  const dark = mix(lit(col, Lt), shd(col, Lt), 0.55);
  const g = ctx.createLinearGradient(a[0], a[1], b[0], b[1]);
  g.addColorStop(0, rgba(dark, 0)); g.addColorStop(1, rgba(dark, k));
  ctx.fillStyle = g;
  ctx.fillRect(H.x - s * 4, H.y - s * 4, s * 8, s * 9);
  // a little occlusion under the jaw line and toward the bottom of the beard
  const c = P(0, 1.55, 0.6);
  ctx.fillStyle = L.radial(ctx, c[0], c[1] + s * 0.4, s * 0.2, s * 1.3, [[0, rgba(dark, 0.0)], [1, rgba(dark, k * 0.35)]]);
  ctx.fillRect(H.x - s * 4, H.y - s * 2, s * 8, s * 7);
}


// ------------------------------------------------------------ full hair cap
// Fills the whole projected skull (slightly enlarged for hair volume) EXCEPT the face
// region below the hairline, so no scalp can show through at any head angle.
// hairline: head-space points from the left temple across the forehead to the right temple.
function hairCap(ctx, pr, st, Lt, hairline, opt = {}) {
  const { P, Pc, s, H } = pr;
  const G = FACE.geoOf(st);
  const c = P(0, G.craniumY, -0.1);
  const R = G.craniumR * s * (opt.volume || 1.07);
  const col = opt.color || st.hair;
  // face area below the hairline (hole)
  const cw = G.cheekW;
  const right = [[0.96 * cw, -0.3, 0.12], [0.98 * cw, 0.2, 0.2], [(G.cheekLow + 0.02) * cw, 0.6, 0.2], [G.jawW, G.jawY, 0.24], [G.chinW, G.chinY - 0.2, 0.48], [0, G.chinY + 0.3, 0.68]];
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
  softShade(ctx, pr, Lt, col, 0.65);
  ctx.fillStyle = L.radial(ctx, c[0], c[1] - R * 0.6, R * 0.2, R * 1.4, [[0, rgba('#000000', 0)], [1, rgba('#000000', 0.28)]]);
  ctx.fillRect(c[0] - R * 2, c[1] - R * 2, R * 4, R * 4);
  if (opt.inner) opt.inner(ctx);
  ctx.restore();
  // silhouette edge over the top of the head (bumpy for curls)
  const lw = lwOf(pr, Lt);
  const a0 = opt.edgeFrom == null ? -2.1 : opt.edgeFrom, a1 = opt.edgeTo == null ? 2.1 : opt.edgeTo;
  if (opt.curls) {
    // clumps of curls of uneven size make a soft, lumpy edge (no regular row of little balls)
    const n = 72;
    const edge = [], base = [];
    for (let i = 0; i <= n; i++) {
      const a = a0 + (a1 - a0) * (i / n);
      const bump = 0.035 + 0.03 * Math.sin(a * 9.1 + 0.7) + 0.022 * Math.sin(a * 17.3 + 2.1) + 0.012 * Math.sin(a * 31.7 + 0.3);
      const k = Math.min(1, Math.min(i, n - i) / 6); // the clumps settle into the cap toward its ends
      const r = R * (0.985 + Math.max(0, bump) * k);
      const ar = a - H.roll;
      edge.push([c[0] + Math.sin(ar) * r, c[1] - Math.cos(ar) * r * 1.0]);
      base.push([c[0] + Math.sin(ar) * R * 0.86, c[1] - Math.cos(ar) * R * 0.86]);
    }
    ctx.beginPath();
    edge.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    for (let i = base.length - 1; i >= 0; i--) ctx.lineTo(base[i][0], base[i][1]);
    ctx.closePath();
    ctx.fillStyle = mix(lit(col, Lt), shd(col, Lt), 0.3);
    ctx.fill();
    ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw * 0.85; ctx.lineJoin = 'round';
    ctx.beginPath();
    edge.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.stroke();
  } else {
    ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw * 0.9;
    ctx.beginPath(); ctx.ellipse(c[0], c[1], R, R * 1.03, H.roll, -Math.PI / 2 + a0, -Math.PI / 2 + a1); ctx.stroke();
  }
  // hairline edge
  ctx.strokeStyle = rgba(st.hairLine, 0.8); ctx.lineWidth = lw * 0.8;
  ctx.beginPath(); L.crPath(ctx, hl, false); ctx.stroke();
  // the area the cap covers (for hair laid over it that should not show seams on top of it)
  const capArea = (p) => {
    p.rect(c[0] - R * 3, c[1] - R * 3, R * 6, R * 6);
    p.moveTo(c[0] + R, c[1]); p.ellipse(c[0], c[1], R, R * 1.03, H.roll, 0, L.TAU);
    L.crPath(p, face, true, 0.4);
  };
  return { c, R, hl, face, capArea };
}

// ======================================================================= JESUS
function jesusHairBack(ctx, pr, st, F, Lt, extra) {
  // long hair falling behind the shoulders as separate locks of different lengths, each tapering to
  // its own tip, with darker gaps between them (never one solid blob)
  const q = mk(pr, extra);
  const c = st.hair, lw = lwOf(pr, Lt);
  const base = mix(lit(c, Lt), shd(c, Lt), 0.55), deep = mix(lit(c, Lt), shd(c, Lt), 0.85);
  // the mass behind the head
  const top = [q([0, -1.42, -0.1]), q([0.85, -1.05, -0.2]), q([1.22, -0.2, -0.3]), q({ a: [1.1, 0.5, -0.3], d: [0.3, 0.7], k: 0.5 }),
    q({ a: [0, 0.5, -0.5], d: [0, 1.2], k: 0.6 }), q({ a: [-1.1, 0.5, -0.3], d: [-0.3, 0.7], k: 0.5 }), q([-1.22, -0.2, -0.3]), q([-0.85, -1.05, -0.2])];
  shape(ctx, top, deep, null, 0);
  // locks, outermost first: [root x, tip dx, tip dy, width]
  const locks = [[1.12, 0.55, 2.35, 0.34], [0.95, 0.4, 2.6, 0.32], [0.7, 0.25, 2.2, 0.3], [0.42, 0.12, 2.45, 0.3], [0.12, 0.04, 2.1, 0.28]];
  for (const sd of [-1, 1]) {
    for (const [x0, dx, dy, w] of locks) {
      const root = [sd * x0, 0.3, -0.35];
      const k = 0.6 + 0.4 * dy / 2.6;
      const pts = [
        q({ a: root, d: [sd * -w * 0.5, -0.2], k: 0.3 }),
        q({ a: root, d: [sd * (dx * 0.45 - w * 0.5), dy * 0.5], k: k * 0.6 }),
        q({ a: root, d: [sd * dx, dy], k }),
        q({ a: root, d: [sd * (dx * 0.5 + w * 0.6), dy * 0.55], k: k * 0.6 }),
        q({ a: root, d: [sd * w * 0.6, -0.15], k: 0.3 }),
      ];
      shape(ctx, pts, base, st.hairLine, lw * 0.8);
      // a few strands inside the lock
      ctx.save();
      ctx.beginPath(); L.crPath(ctx, pts, true); ctx.clip();
      for (const f of [-0.25, 0.1, 0.4]) {
        L.strokeSmooth(ctx, [q({ a: root, d: [sd * w * f, 0], k: 0.3 }), q({ a: root, d: [sd * (dx * 0.5 + w * f * 0.5), dy * 0.55], k: k * 0.6 }),
          q({ a: root, d: [sd * dx, dy * 0.92], k })], rgba(st.hairLine, 0.35), lw * 0.55);
      }
      ctx.restore();
    }
  }
}
function jesusHairFront(ctx, pr, st, F, Lt, extra) {
  const q = mk(pr, extra);
  const c = st.hair, lw = lwOf(pr, Lt);
  const side = Lt.side || -1;
  // full head of hair: centre-parted cap over the whole skull
  const cap = hairCap(ctx, pr, st, Lt, [[-0.98, -0.42, 0.3], [-0.78, -0.82, 0.58], [-0.42, -1.02, 0.82], [0, -1.08, 0.9], [0.42, -1.02, 0.82], [0.78, -0.82, 0.58], [0.98, -0.42, 0.3]], {
    volume: 1.09,
    inner: (cx) => {
      // flowing strands from the part toward the temples, and a soft sheen
      for (const sd of [-1, 1]) {
        for (let i = 0; i < 4; i++) {
          const k = i / 3;
          L.strokeSmooth(cx, [q([sd * 0.02, -1.42, 0.3]), q([sd * (0.3 + 0.25 * k), -1.25 + 0.05 * k, 0.6]), q([sd * (0.75 + 0.15 * k), -0.8 + 0.12 * k, 0.45])], rgba(st.hairLine, 0.35), lw * 0.6);
        }
        if (sd === side) {
          for (let i = 0; i < 3; i++) {
            const o = i * 0.07;
            L.strokeSmooth(cx, [q([sd * (0.12 + o), -1.37 + o * 0.3, 0.45]), q([sd * (0.42 + o), -1.2 + o * 0.4, 0.58]), q([sd * (0.68 + o * 0.6), -0.98 + o * 0.5, 0.5])], rgba(shade(lit(c, Lt), 1.5), 0.28), lw * 0.45);
          }
        }
      }
    },
  });
  // centre part: a soft line where the hair divides, fading out toward the crown
  {
    const a = q([0, -1.1, 0.9]), b = q([0, -1.42, 0.25]);
    const gp = ctx.createLinearGradient(a[0], a[1], b[0], b[1]);
    gp.addColorStop(0, rgba(shade(lit(c, Lt), 0.6), 0.7)); gp.addColorStop(1, rgba(shade(lit(c, Lt), 0.6), 0));
    L.strokeSmooth(ctx, [a, q([0, -1.3, 0.62]), b], gp, lw * 0.6);
  }
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
    // the locks are part of the same head of hair: no outline where they lie over the top of the
    // head (that read as separate pieces stuck on), only along their own edges below it
    shape(ctx, pts, isShadow ? mix(lit(c, Lt), shd(c, Lt), 0.5) : lit(c, Lt), null, 0);
    {
      const PathC = require('@napi-rs/canvas').Path2D;
      const outside = new PathC(); cap.capArea(outside);
      ctx.save(); ctx.clip(outside, 'evenodd');
      ctx.beginPath(); L.crPath(ctx, pts, true); ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.stroke();
      ctx.restore();
    }
    // inner shadow along face edge
    ctx.save();
    ctx.beginPath(); L.crPath(ctx, pts, true); ctx.clip();
    const inner = [q([sd * 0.3, -1.15, 0.72]), q([sd * 0.7, -0.8, 0.6]), q([sd * 0.95, -0.3, 0.38]), q([sd * 1.02, 0.4, 0.2]),
      q({ a: [sd * 1.0, 0.8, 0.1], d: [sd * 0.1, 0.8], k: 0.8 })];
    L.strokeSmooth(ctx, inner, rgba(shd(c, Lt), 0.9), pr.s * 0.16);
    // fine strands of light on the outer lock (lit side only)
    if (!isShadow) {
      for (let i = 0; i < 3; i++) {
        const o = i * 0.06;
        L.strokeSmooth(ctx, [q([sd * (0.84 + o), -0.75 + o, 0.42]), q([sd * (1.0 + o), -0.2, 0.22]), q([sd * (1.04 + o * 0.5), 0.3, 0.12])], rgba(shade(lit(c, Lt), 1.45), 0.25), lw * 0.45);
      }
    }
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
      // the beard covers the jaw whatever its width and length
      const jx = Math.max(1, G.jawW / 0.72), dy = G.chinY - 1.34;
      const outer = [
        [-0.97, ch, 0.15], [-0.96, 0.6, 0.17], [-0.76 * jx, 0.98 + dy * 0.5 + jd * 0.5, 0.27], [-0.5 * jx, 1.28 + dy + jd, 0.45],
        [-0.22 * jx, 1.42 + len + dy + jd, 0.62], [0, 1.47 + len + dy + jd, 0.68], [0.22 * jx, 1.42 + len + dy + jd, 0.62],
        [0.5 * jx, 1.28 + dy + jd, 0.45], [0.76 * jx, 0.98 + dy * 0.5 + jd * 0.5, 0.27], [0.96, 0.6, 0.17], [0.97, ch, 0.15],
      ];
      const qo = (p) => pr.Pc(p[0], p[1], p[2]);
      const my = G.mouthY;
      const inner = [
        [0.9, ch + 0.05, 0.3], [0.66, 0.58 * thick + 0.15, 0.62], [0.42, my - 0.02, 0.82], [0.3, my + 0.12 + jd * 0.6, 0.86],
        [0.14, my + 0.24 + jd, 0.9], [0, my + 0.21 + jd, 0.92], [-0.14, my + 0.24 + jd, 0.9],
        [-0.3, my + 0.12 + jd * 0.6, 0.86], [-0.42, my - 0.02, 0.82], [-0.66, 0.58 * thick + 0.15, 0.62], [-0.9, ch + 0.05, 0.3],
      ];
      // build path: outer smooth then inner smooth back
      const inn = inner.map((p) => q(p));
      const beardPath = () => {
        ctx.beginPath();
        L.crPath(ctx, outer.map((p) => qo(p)), false);
        ctx.lineTo(inn[0][0], inn[0][1]);
        L.crPath({ moveTo: () => {}, bezierCurveTo: (...a) => ctx.bezierCurveTo(...a), closePath() {} }, inn, false);
        ctx.closePath();
      };
      beardPath();
      ctx.fillStyle = lit(col, Lt);
      ctx.fill();
      ctx.save();
      ctx.clip();
      softShade(ctx, pr, Lt, col, 0.55);
      // hair texture strokes
      for (let i = 0; i < 9; i++) {
        const x = -0.8 + i * 0.2;
        const a = q([x, 0.75 + Math.abs(x) * -0.2, 0.6]);
        const b = q([x * 0.85, 1.3 + len + dy - Math.abs(x) * 0.35 + jd, 0.6]);
        L.strokeSmooth(ctx, [a, b], rgba(shade(col, 0.5), 0.45), lw * 0.6);
      }
      ctx.restore();
      beardPath(); // the strands replaced the current path; outline the beard itself
      ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw * 0.8; ctx.stroke();
    } else {
      // mustache: one colour; the side away from the light only slightly darker
      const my = G.mouthY;
      const sm = F.mouthSmile * 0.04;
      for (const sd of [-1, 1]) {
        const pts = [q([sd * 0.02, my - 0.17, 0.98]), q([sd * 0.2, my - 0.15 - sm, 0.94]), q([sd * 0.36, my - 0.02 - sm, 0.85]),
          q([sd * 0.42, my + 0.1, 0.8]), q([sd * 0.3, my - 0.05 - sm, 0.88]), q([sd * 0.12, my - 0.08, 0.95]), q([sd * 0.02, my - 0.09, 0.97])];
        shape(ctx, pts, sd === -side ? mix(lit(col, Lt), shd(col, Lt), 0.22) : lit(col, Lt), st.hairLine, lw * 0.7);
      }
    }
  };
}

// ========================================================================= PAUL
function paulHairBack(ctx, pr, st, F, Lt, extra) {
  // the hair that remains round the back of a bald head: it lies against the skull behind the ears
  // and down to the nape (seen only at the edge of the head and behind the ears)
  const q = mk(pr, extra);
  const c = st.hair, lw = lwOf(pr, Lt);
  for (const sd of [-1, 1]) {
    const pts = [q([sd * 0.97, -0.62, -0.12]), q([sd * 1.06, -0.25, -0.2]), q([sd * 1.08, 0.15, -0.28]), q([sd * 1.0, 0.58, -0.38]),
      q([sd * 0.78, 0.78, -0.55]), q([sd * 0.7, 0.3, -0.62]), q([sd * 0.82, -0.3, -0.55])];
    shape(ctx, pts, mix(lit(c, Lt), shd(c, Lt), 0.45), st.hairLine, lw * 0.7);
    strands(ctx, [[q([sd * 1.0, -0.45, -0.2]), q([sd * 1.05, 0.0, -0.3]), q([sd * 0.95, 0.5, -0.42])]], rgba(st.hairLine, 0.3), lw * 0.5);
  }
}
function paulHairFront(ctx, pr, st, F, Lt, extra) {
  const q = mk(pr, extra);
  const c = st.hair, lw = lwOf(pr, Lt);
  const side = Lt.side || -1;
  for (const sd of [-1, 1]) {
    // the far side's fringe lies on the back of the head, out of sight once he turns (the hair at the
    // head's silhouette is drawn behind it); it fades out as the head turns, never popping
    const far = Math.sign(sd) === Math.sign(pr.H.yaw);
    const vis = far ? clamp((0.2 - Math.abs(pr.H.yaw)) / 0.12) : 1;
    if (vis <= 0.01) continue;
    ctx.save(); ctx.globalAlpha *= vis;
    // the fringe left round a bald head: close-cropped hair lying against the skull from the temple,
    // over the top of the ear and down behind it to the nape, one soft band with no outline
    const pts = [q([sd * 0.93, -0.64, 0.02]), q([sd * 1.0, -0.42, -0.3]), q([sd * 0.98, 0.0, -0.56]), q([sd * 0.9, 0.45, -0.68]), q([sd * 0.78, 0.86, -0.7]),
      q([sd * 0.8, 0.86, -0.44]), q([sd * 0.94, 0.45, -0.4]), q([sd * 1.02, 0.05, -0.3]), q([sd * 1.05, -0.13, -0.12]),
      q([sd * 1.0, -0.2, 0.05]), q([sd * 0.95, -0.36, 0.08])];
    const col = sd === -side ? mix(lit(c, Lt), shd(c, Lt), 0.3) : lit(c, Lt);
    ctx.beginPath(); L.crPath(ctx, pts, true, 0.5);
    ctx.fillStyle = rgba(col, 0.9); ctx.fill();
    // fine strands combed back along the band, and a little shadow under its lower edge
    strands(ctx, [[q([sd * 0.95, -0.52, 0.0]), q([sd * 1.0, -0.25, -0.3]), q([sd * 0.97, 0.15, -0.5]), q([sd * 0.86, 0.66, -0.6])],
      [q([sd * 0.97, -0.3, -0.05]), q([sd * 1.02, -0.05, -0.32]), q([sd * 0.93, 0.4, -0.52])],
      [q([sd * 1.0, -0.22, 0.0]), q([sd * 1.03, -0.1, -0.2])]], rgba(st.hairLine, 0.22), lw * 0.4);
    strands(ctx, [[q([sd * 1.0, -0.19, 0.05]), q([sd * 1.04, -0.12, -0.14]), q([sd * 1.01, 0.06, -0.32]), q([sd * 0.93, 0.46, -0.42])]], rgba(shd(st.skin, Lt), 0.35), lw * 0.8);
    ctx.restore();
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
    const qo = (p) => pr.Pc(p[0], p[1], p[2]);
    const outer = [
      qo([-0.98, 0.22, 0.14]), qo([-0.96, 0.65, 0.15]), qo([-0.84, 1.1 + jd * 0.5, 0.22]),
      q({ a: [-0.6, 1.3, 0.4], d: [-0.05, 0.55 + jd], k: 0.4 }), q({ a: [-0.3, 1.4, 0.55], d: [0.0, 0.95 + jd], k: 0.6 }),
      q({ a: [0, 1.45, 0.6], d: [0.0, 1.12 + jd], k: 0.7 }), q({ a: [0.3, 1.4, 0.55], d: [0.0, 0.95 + jd], k: 0.6 }),
      q({ a: [0.6, 1.3, 0.4], d: [0.05, 0.55 + jd], k: 0.4 }), qo([0.84, 1.1 + jd * 0.5, 0.22]), qo([0.96, 0.65, 0.15]), qo([0.98, 0.22, 0.14]),
    ];
    const inner = [
      q([0.86, 0.28, 0.32]), q([0.66, 0.66, 0.62]), q([0.42, my, 0.82]), q([0.3, my + 0.14 + jd * 0.6, 0.86]),
      q([0.12, my + 0.25 + jd, 0.9]), q([0, my + 0.22 + jd, 0.92]), q([-0.12, my + 0.25 + jd, 0.9]),
      q([-0.3, my + 0.14 + jd * 0.6, 0.86]), q([-0.42, my, 0.82]), q([-0.66, 0.66, 0.62]), q([-0.86, 0.28, 0.32]),
    ];
    const beardPath = () => {
      ctx.beginPath();
      L.crPath(ctx, outer, false);
      ctx.lineTo(inner[0][0], inner[0][1]);
      L.crPath({ moveTo: () => {}, bezierCurveTo: (...a) => ctx.bezierCurveTo(...a), closePath() {} }, inner, false);
      ctx.closePath();
    };
    beardPath();
    ctx.fillStyle = lit(col, Lt);
    ctx.fill();
    ctx.save();
    ctx.clip();
    softShade(ctx, pr, Lt, col, 0.5);
    // wavy strands
    for (let i = 0; i < 11; i++) {
      const x = -0.85 + i * 0.17;
      const a = q([x, 0.9, 0.55]);
      const b = q({ a: [x * 0.7, 1.35, 0.5], d: [x * 0.05, 0.5 + 0.4 * (1 - Math.abs(x)) + jd], k: 0.5 });
      const m = [(a[0] + b[0]) / 2 + pr.s * 0.04 * Math.sin(i * 1.7), (a[1] + b[1]) / 2];
      L.strokeSmooth(ctx, [a, m, b], rgba(shade(col, 0.55), 0.5), lw * 0.6);
    }
    ctx.restore();
    beardPath();
    ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw * 0.8; ctx.stroke();
  } else {
    const sm = F.mouthSmile * 0.04;
    for (const sd of [-1, 1]) {
      const pts = [q([sd * 0.02, my - 0.18, 0.98]), q([sd * 0.22, my - 0.16 - sm, 0.94]), q([sd * 0.4, my + 0.0 - sm, 0.84]),
        q([sd * 0.46, my + 0.2, 0.78]), q([sd * 0.33, my + 0.02 - sm, 0.86]), q([sd * 0.12, my - 0.07, 0.95]), q([sd * 0.02, my - 0.08, 0.97])];
      shape(ctx, pts, sd === -side ? mix(lit(col, Lt), shd(col, Lt), 0.2) : lit(col, Lt), st.hairLine, lw * 0.7);
    }
  }
}

// ======================================================================== ASHER
function curlyCap(opts) {
  // short, tightly curled hair over the whole skull: an uneven, clumpy edge and hairline, light and
  // shade in clumps, and many small coils of different sizes for texture (never a row of balls)
  const hl0 = opts.hairline || -0.86;
  const key = [[-0.99, -0.12, 0.2], [-0.96, -0.46, 0.38], [-0.74, -0.74 - (hl0 + 0.86) * 0.5, 0.62], [-0.38, hl0 - 0.04, 0.84],
    [0, hl0 - 0.06, 0.9], [0.38, hl0 - 0.04, 0.84], [0.74, -0.74 - (hl0 + 0.86) * 0.5, 0.62], [0.96, -0.46, 0.38], [0.99, -0.12, 0.2]];
  // the hairline wavers a little: small tufts dip onto the forehead and temples
  const hairline = sample3(key, 3).map(([x, y, z], i, a) => {
    const k = Math.min(1, Math.min(i, a.length - 1 - i) / 3);
    return [x, y + k * (0.022 + 0.022 * Math.sin(i * 2.3 + 0.5) + 0.012 * L.hash(i * 13)), z];
  });
  // short wavy strands, scattered over the skull, each following the hair's growth out from the crown
  // with its own twist, length and wave
  const strands = [];
  for (let i = 0; i < 150; i++) {
    const u = -1.05 + 2.1 * L.hash01(i * 7 + 1), v = -1.5 + 1.0 * L.hash01(i * 11 + 3);
    strands.push({ u, v, len: 0.08 + 0.08 * L.hash01(i * 5 + 2), tw: (L.hash01(i * 3 + 9) - 0.5) * 1.3,
      amp: 0.01 + 0.012 * L.hash01(i * 17), ph: L.TAU * L.hash01(i * 23 + 4), al: 0.24 + 0.16 * L.hash01(i * 29 + 6), w: 0.5 + 0.35 * L.hash01(i * 31 + 8) });
  }
  return {
    back(ctx, pr, st, F, Lt, extra) {
      // volume at the back of the head (behind the neck), with the same uneven edge
      const q = mk(pr, extra);
      const pts = [];
      for (let i = 0; i <= 24; i++) {
        const a = -Math.PI * 0.62 + (i / 24) * Math.PI * 1.24;
        const r = 1.1 + 0.035 * Math.sin(i * 2.7) + 0.025 * Math.sin(i * 5.3 + 1);
        pts.push(q([Math.sin(a) * r, -0.38 - Math.cos(a) * r * 1.02, -0.25]));
      }
      pts.push(q([0.9, 0.25, -0.4]), q([0, 0.35, -0.6]), q([-0.9, 0.25, -0.4]));
      shape(ctx, pts, shd(st.hair, Lt), st.hairLine, lwOf(pr, Lt) * 0.8);
    },
    front(ctx, pr, st, F, Lt, extra) {
      const q = mk(pr, extra);
      const lw = lwOf(pr, Lt);
      const side = Lt.side || -1;
      const hiCol = shade(lit(st.hair, Lt), 1.9), loCol = shade(st.hairLine, 1.0);
      hairCap(ctx, pr, st, Lt, hairline, {
        volume: 1.08, curls: true, edgeFrom: -1.75, edgeTo: 1.75,
        inner: (cx) => {
          // clumps: soft darker hollows and lighter crowns on the lit side
          for (let i = 0; i < 9; i++) {
            const p = q([-0.9 + 0.22 * i + 0.05 * L.hash(i), -1.22 + 0.18 * Math.sin(i * 1.7), 0.6]);
            const lt = (i - 4) * side < 0;
            cx.fillStyle = L.radial(cx, p[0], p[1], 0, pr.s * 0.2, [[0, rgba(lt ? hiCol : loCol, lt ? 0.12 : 0.3)], [1, rgba(lt ? hiCol : loCol, 0)]]);
            cx.fillRect(p[0] - pr.s * 0.25, p[1] - pr.s * 0.25, pr.s * 0.5, pr.s * 0.5);
          }
          // the curl texture: short wavy strands laid on thinly, so they blend into the clumps (open
          // strokes only, never little rings), with a few catching the light on the lit side
          cx.lineCap = 'round'; cx.lineJoin = 'round';
          for (const k of strands) {
            const du = k.u, dv = k.v + 1.75, d = Math.hypot(du, dv) || 1;
            const ct = Math.cos(k.tw), sn = Math.sin(k.tw);
            const fu = (du * ct - dv * sn) / d, fv = (du * sn + dv * ct) / d;
            const pts = [];
            for (let j = 0; j <= 6; j++) {
              const tt = j / 6 - 0.5, w = Math.sin((j / 6) * L.TAU + k.ph) * k.amp;
              pts.push(q([k.u + fu * tt * k.len - fv * w, k.v + fv * tt * k.len + fu * w, 0.6]));
            }
            L.strokeSmooth(cx, pts, rgba(loCol, k.al), lw * k.w);
            if (k.u * side > 0.1 && k.v < -0.8) L.strokeSmooth(cx, pts.slice(1, 4), rgba(hiCol, 0.2), lw * 0.4);
          }
        },
      });
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
  // A head cloth that sits ON the head: it rests on the crown (only the thickness of the cloth above
  // the scalp), falls past the ears to the shoulders, and is held by a cord at the crown. It has a
  // hem along the face, soft folds following the drape and light on the raised folds.
  return {
    back(ctx, pr, st, F, Lt, extra) {
      const q = mk(pr, extra);
      const c = opts.color;
      const pts = [q([0, -1.47, -0.1]), q([1.08, -1.0, -0.2]), q([1.25, 0.0, -0.3]),
        q({ a: [1.15, 0.6, -0.3], d: [0.32, 1.3], k: 0.6 }), q({ a: [1.15, 0.6, -0.3], d: [0.5, 2.4], k: 0.9 }),
        q({ a: [0, 0.6, -0.5], d: [0, 2.5], k: 0.6 }),
        q({ a: [-1.15, 0.6, -0.3], d: [-0.5, 2.4], k: 0.9 }), q({ a: [-1.15, 0.6, -0.3], d: [-0.32, 1.3], k: 0.6 }),
        q([-1.25, 0.0, -0.3]), q([-1.08, -1.0, -0.2])];
      // the inside of the hood: in shadow, but still the same cloth
      shape(ctx, pts, mix(lit(c, Lt), shd(c, Lt), 0.68), st.hairLine, lwOf(pr, Lt));
    },
    front(ctx, pr, st, F, Lt, extra) {
      const q = mk(pr, extra);
      const c = opts.color, lw = lwOf(pr, Lt);
      const side = Lt.side || -1;
      const hi = shade(lit(c, Lt), 1.18), lo = shade(c, 0.55);
      // ONE piece of cloth over the head (no seam down the middle): its outline runs from the crown
      // down one side, round the hanging end, up the edge along the face, across the forehead and
      // down the other side; the light falls across it as one soft gradient
      const half = (sd) => [q([sd * 0.48, -1.04, 0.8]), q([sd * 0.88, -0.8, 0.55]), q([sd * 1.07, -0.4, 0.34]),
        q([sd * 1.11, 0.3, 0.2]), q({ a: [sd * 1.07, 0.7, 0.1], d: [sd * 0.1, 0.8], k: 0.6 }),
        q({ a: [sd * 1.07, 0.7, 0.1], d: [sd * 0.25, 1.6], k: 0.9 }), q({ a: [sd * 1.07, 0.7, 0.1], d: [sd * 0.62, 1.5], k: 0.9 }),
        q({ a: [sd * 1.07, 0.7, 0.1], d: [sd * 0.52, 0.6], k: 0.6 }), q([sd * 1.28, 0.0, -0.05]), q([sd * 1.22, -0.8, 0.0]),
        q([sd * 0.78, -1.4, 0.1])];
      const R = half(1), Lh = half(-1);
      const outline = [q([0, -1.52, 0.05]), ...R.slice().reverse(), q([0, -1.1, 0.9]), ...Lh];
      ctx.beginPath(); L.crPath(ctx, outline, true, 0.5);
      ctx.fillStyle = lit(c, Lt); ctx.fill();
      ctx.save(); ctx.clip();
      {
        const H = pr.H, s2 = pr.s;
        const xt = FACE.terminatorX(H, Lt);
        const ga = pr.P(xt + side * 0.35, -0.6, 0.9), gb = pr.P(xt - side * 0.9, -0.6, 0.9);
        const dark = mix(lit(c, Lt), shd(c, Lt), 0.62);
        const g = ctx.createLinearGradient(ga[0], ga[1], gb[0], gb[1]);
        g.addColorStop(0, rgba(dark, 0)); g.addColorStop(1, rgba(dark, 0.75));
        ctx.fillStyle = g; ctx.fillRect(H.x - s2 * 4, H.y - s2 * 4, s2 * 8, s2 * 9);
        // the drape darkens as it falls past the ears into the shadow of the head
        const d0 = pr.P(0, 0.1, 0.3), d1 = pr.P(0, 1.2, 0.3);
        const g2 = ctx.createLinearGradient(d0[0], d0[1], d1[0], d1[1]);
        g2.addColorStop(0, rgba(dark, 0)); g2.addColorStop(1, rgba(dark, 0.45));
        ctx.fillStyle = g2; ctx.fillRect(H.x - s2 * 4, H.y - s2 * 4, s2 * 8, s2 * 9);
        // light on the dome of the crown
        const cr = pr.P(-side * 0.25, -1.25, 0.7);
        ctx.fillStyle = L.radial(ctx, cr[0], cr[1], 0, s2 * 0.8, [[0, rgba(hi, 0.35)], [1, rgba(hi, 0)]]);
        ctx.fillRect(H.x - s2 * 4, H.y - s2 * 4, s2 * 8, s2 * 9);
      }
      ctx.lineCap = 'round';
      for (const sd of [-1, 1]) {
        // the hem along the face: the cloth's thickness turning under, in shadow
        const hem = [q([sd * 0.05, -1.07, 0.9]), q([sd * 0.48, -1.0, 0.8]), q([sd * 0.86, -0.77, 0.55]), q([sd * 1.04, -0.4, 0.35]),
          q([sd * 1.07, 0.3, 0.22]), q({ a: [sd * 1.07, 0.7, 0.1], d: [sd * 0.12, 0.85], k: 0.6 })];
        L.strokeSmooth(ctx, hem, rgba(lo, 0.45), pr.s * 0.07);
        // stripes woven into the cloth
        if (opts.stripe) {
          for (const off of [0.14, 0.22]) {
            const sp = [q([sd * (0.45 + off), -1.06 + off * 0.1, 0.78]), q([sd * (0.9 + off), -0.78, 0.5]), q([sd * (1.12 + off), -0.3, 0.2]),
              q([sd * (1.16 + off), 0.35, 0.1]), q({ a: [sd * 1.07, 0.7, 0.1], d: [sd * (0.22 + off), 1.0], k: 0.7 })];
            L.strokeSmooth(ctx, sp, rgba(opts.stripe, 0.8), pr.s * 0.045);
          }
        }
        // folds of the drape: a soft shadow with light on the raised side of each
        for (const [o, k] of [[0.3, 0.9], [0.55, 1.0], [0.8, 0.85]]) {
          const fp = [q([sd * (0.3 + o * 0.6), -1.25 + o * 0.25, 0.6]), q([sd * (0.95 + o * 0.22), -0.6, 0.3]),
            q([sd * (1.1 + o * 0.12), 0.2, 0.15]), q({ a: [sd * 1.07, 0.7, 0.1], d: [sd * (0.18 + o * 0.4), 0.7 + o * 0.6], k: 0.8 })];
          L.strokeSmooth(ctx, fp, rgba(st.hairLine, 0.2 * k), lw * 0.7);
          L.strokeSmooth(ctx, fp.map((p) => [p[0] - sd * pr.s * 0.05, p[1]]), rgba(hi, (sd === side ? 0.3 : 0.14) * k), pr.s * 0.035);
        }
      }
      // a soft crease where the cloth is pulled over the crown from the front
      L.strokeSmooth(ctx, [q([0, -1.12, 0.9]), q([0.02, -1.35, 0.6]), q([0, -1.5, 0.2])], rgba(st.hairLine, 0.12), lw * 0.8);
      ctx.restore();
      ctx.beginPath(); L.crPath(ctx, outline, true, 0.5);
      ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw; ctx.stroke();
      // the cord holding it on the head, at the crown
      if (opts.band) {
        const bp = [q([-1.0, -0.86, 0.45]), q([-0.5, -1.1, 0.8]), q([0, -1.16, 0.9]), q([0.5, -1.1, 0.8]), q([1.0, -0.86, 0.45])];
        L.strokeSmooth(ctx, bp, lit(opts.band, Lt), pr.s * 0.09);
        L.strokeSmooth(ctx, bp.map((p) => [p[0], p[1] - pr.s * 0.02]), rgba(shade(lit(opts.band, Lt), 1.6), 0.35), pr.s * 0.025);
        L.strokeSmooth(ctx, bp, rgba(st.hairLine, 0.5), lw * 0.5);
      }
    },
    shadow(ctx, pr, st, F, Lt, skinSh) {
      const q = mk(pr, null);
      const pts = [q([-1.02, -0.55, 0.4]), q([-0.5, -0.86, 0.8]), q([0, -0.92, 0.9]), q([0.5, -0.86, 0.8]), q([1.02, -0.55, 0.4]),
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
      ctx.beginPath(); L.crPath(ctx, [...dome, ...rim], true);
      ctx.strokeStyle = st.hairLine; ctx.lineWidth = lw; ctx.stroke();
      // brow guard ridge
      const br = [q([-1.15, -0.62, 0.3]), q([-0.6, -0.86, 0.9]), q([0, -0.93, 1.05]), q([0.6, -0.86, 0.9]), q([1.15, -0.62, 0.3])];
      L.strokeSmooth(ctx, br, lit(shade(m, 1.15), Lt), pr.s * 0.1);
      L.strokeSmooth(ctx, br, rgba(st.hairLine, 0.7), lw * 0.5);
      // crest ridge
      L.strokeSmooth(ctx, [q([0, -0.9, 1.0]), q([0, -1.3, 0.62]), q([0, -1.52, 0.1])], rgba(shade(m, 0.6), 0.9), lw * 1.2);
      // cheek guards
      for (const sd of [-1, 1]) {
        // the far guard turns away out of sight gradually (no popping)
        const far = Math.sign(sd) === Math.sign(pr.H.yaw);
        const vis = far ? clamp((0.52 - Math.abs(pr.H.yaw)) / 0.2) : 1;
        if (vis <= 0.01) continue;
        ctx.save(); ctx.globalAlpha *= vis;
        const cg = [q([sd * 1.08, -0.55, 0.4]), q([sd * 0.86, -0.4, 0.55]), q([sd * 0.8, 0.2, 0.55]), q([sd * 0.72, 0.85, 0.42]),
          q([sd * 0.92, 0.95, 0.25]), q([sd * 1.08, 0.5, 0.15]), q([sd * 1.14, -0.2, 0.2])];
        shape(ctx, cg, sd === -side ? shd(m, Lt) : lit(m, Lt), st.hairLine, lw);
        const rv = q([sd * 0.93, 0.25, 0.42]);
        ctx.fillStyle = rgba('#fff2d0', 0.6); L.ellipse(ctx, rv[0], rv[1], pr.s * 0.03, pr.s * 0.03); ctx.fill();
        ctx.restore();
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
  const jx = G.jawW / 0.76, dy = G.chinY - 1.36;
  const pts = [q([-0.98, 0.3, 0.15]), q([-0.85 * jx, 0.9 + dy * 0.5, 0.2]), q([-0.45 * jx, 1.25 + dy + jd, 0.48]), q([0, 1.35 + dy + jd, 0.68]), q([0.45 * jx, 1.25 + dy + jd, 0.48]),
    q([0.85 * jx, 0.9 + dy * 0.5, 0.2]), q([0.98, 0.3, 0.15]), q([0.6, 0.7, 0.65]), q([0.3, G.mouthY + 0.2 + jd, 0.86]), q([0, G.mouthY + 0.25 + jd, 0.9]),
    q([-0.3, G.mouthY + 0.2 + jd, 0.86]), q([-0.6, 0.7, 0.65])];
  shape(ctx, pts, rgba(st.beardColor || '#3a3030', 0.28), null, 0);
}

// ============================================================ styles
const C = {};
C.jesus = {
  name: 'jesus', skin: '#c99c7c', skinShadow: '#946a55', line: '#3b2219', iris: '#6a4126', browColor: '#3a2416', twinkle: true,
  hair: '#4a2e1e', hairLine: '#1e120c', beardColor: '#4a2e1e', lashW: 0.26, blush: 0.12,
  geo: { chinY: 1.36, jawW: 0.66, mouthW: 0.21 },
  hairBack: jesusHairBack, hairFront: jesusHairFront, hairShadow: jesusHairShadow, beard: beardFull({ len: 0.12, cheek: 0.25 }),
  beardHidesFolds: true,
  cloth: { tunic: '#efe5d3', mantle: '#8e2b2e', trim: '#a5804a', edge: '#d8b25c', neck: 'v', looseSleeves: 1 },
};
C.paul = {
  name: 'paul', skin: '#dfae8a', skinShadow: '#a9725a', line: '#3a221a', iris: '#4e3a2c', browColor: '#c9c1b6',
  hair: '#d6d0c8', hairLine: '#4a3a32', beardColor: '#dcd6ce', bald: true, age: 1, bushyBrows: true, browW: 0.095,
  // an old man's head sits a little lower and further forward on the neck
  neckLen: 1.95, headFwd: 0.12,
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
// young Paul (Saul) must never be mistaken for Asher: a white head cloth with blue stripes (a
// Pharisee's), a lean long face, heavy straight brows, a short trimmed beard that leaves the cheeks
// bare, and a blue tunic under a white mantle
const saulTravel = headCloth({ color: '#e4ddcc', stripe: '#2d4f8a', band: '#2a2020' });
C.saul = {
  name: 'saul', skin: '#d2a07c', skinShadow: '#9a6650', line: '#2e1c16', iris: '#3a2a20', browColor: '#140c0a',
  hair: '#17110f', hairLine: '#050303', beardColor: '#17110f', age: 0.1, browW: 0.1,
  geo: { chinY: 1.42, jawW: 0.64, mouthW: 0.21, cheekW: 0.93 },
  hairBack: saulTravel.back, hairFront: saulTravel.front, hairShadow: saulTravel.shadow, beard: beardFull({ len: -0.02, cheek: 0.62, thick: 0.8 }),
  beardHidesFolds: true,
  // a traveller's light linen tunic under the white mantle (no dark layer), blue woven trim
  cloth: { tunic: '#cdc3ad', mantle: '#e2dccd', trim: '#2d4f8a', neck: 'round', skirt: '#c6bca6' },
};
C.saul_travel = Object.assign({}, C.saul);
const childCap = curlyCap({ hairline: -0.62 });
C.child = {
  // a boy: the body smaller than a man's under a head of nearly adult size
  bodyScale: 0.8,
  name: 'child', skin: '#ecbf9c', skinShadow: '#b98068', line: '#3a241c', iris: '#4a3020', browColor: '#2a1c14',
  hair: '#2d1e16', hairLine: '#120a07', child: true, blush: 0.35, browW: 0.06, lashW: 0.3, eyeScale: 1.42, irisR: 0.6, neckLen: 1.8,
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
// the temple guards who arrested Yosef: dark head cloth, leather-banded tunic
const tgCloth = headCloth({ color: '#3a3430', stripe: '#7a2a22', band: '#1e1a16' });
C.temple_guard = {
  name: 'temple_guard', skin: '#d6a07c', skinShadow: '#9a6650', line: '#2a1a14', iris: '#3a2a20', browColor: '#1e1612',
  hair: '#1e1612', hairLine: '#0e0806', beardColor: '#241a14', metal: '#7a5a3a', age: 0.35, browW: 0.095,
  geo: { chinY: 1.36, jawW: 0.76, mouthW: 0.22 },
  hairBack: tgCloth.back, hairFront: tgCloth.front, hairShadow: tgCloth.shadow, beard: beardFull({ len: 0.08, cheek: 0.32 }),
  beardHidesFolds: true,
  cloth: { tunic: '#5a2a24', mantle: '#3a2e24', trim: '#2a2018', neck: 'round', armor: true },
};
// Saul's two travelling companions on the Damascus road (extras: no lines)
const compACloth = headCloth({ color: '#a88f6c', stripe: '#5a3a2a', band: '#2a2020' });
C.companion_a = {
  name: 'companion_a', skin: '#d6a27e', skinShadow: '#9c6a52', line: '#2e1c16', iris: '#3a2a20', browColor: '#1e1612',
  hair: '#241a14', hairLine: '#0e0806', beardColor: '#2a1e18', age: 0.35, browW: 0.09,
  geo: { chinY: 1.34, jawW: 0.74, mouthW: 0.22 },
  hairBack: compACloth.back, hairFront: compACloth.front, hairShadow: compACloth.shadow, beard: beardFull({ len: 0.2, cheek: 0.3 }),
  beardHidesFolds: true,
  cloth: { tunic: '#6e5a44', mantle: '#4a3a2c', trim: '#2a2018', neck: 'round' },
};
const compBCloth = headCloth({ color: '#56483a', stripe: '#8a6a3a', band: '#1e1a16' });
C.companion_b = {
  name: 'companion_b', skin: '#c99872', skinShadow: '#8e5e48', line: '#2a1a14', iris: '#3a2a20', browColor: '#1a1210',
  hair: '#1a1210', hairLine: '#0a0604', beardColor: '#1e1612', age: 0.2, browW: 0.09,
  geo: { chinY: 1.32, jawW: 0.72, mouthW: 0.22 },
  hairBack: compBCloth.back, hairFront: compBCloth.front, hairShadow: compBCloth.shadow, beard: beardFull({ len: 0.06, cheek: 0.34 }),
  beardHidesFolds: true,
  cloth: { tunic: '#7a6a52', mantle: '#3a3028', trim: '#2a2018', neck: 'round' },
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
  adamsApple: false, age: 0.15, neckLen: 1.92,
  geo: { chinY: 1.24, jawW: 0.74, jawY: 0.96, mouthW: 0.18, mouthY: 0.8, eyeH: 1.15, browY: -0.37, noseLen: 0.82, cheekW: 0.96 },
  hairBack: phoebeVeil.back,
  hairFront(ctx, pr, st, F, Lt, extra) {
    hairCap(ctx, pr, st, Lt, [[-0.96, -0.3, 0.3], [-0.72, -0.78, 0.6], [-0.36, -0.98, 0.84], [0, -1.04, 0.9], [0.36, -0.98, 0.84], [0.72, -0.78, 0.6], [0.96, -0.3, 0.3]], { volume: 1.06 });
    phoebeVeil.front(ctx, pr, st, F, Lt, extra);
  },
  hairShadow: phoebeVeil.shadow,
  cloth: { tunic: '#b49a72', mantle: '#3f6f86', trim: '#e8d9b4', neck: 'round' },
};

module.exports = { C, mk, shape, lit, shd, lwOf, hairCap, softShade };
