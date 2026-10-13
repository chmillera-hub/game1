// Anatomical hands: a small 3D skeleton (palm slab, three-jointed fingers, thumb) projected
// orthographically and drawn as cel-shaded capsules with a single outline around each part.
//
// World axes for hands: x right, y UP, z toward the viewer (screen y = -world y).
// Hand-local axes: a = toward the fingertips, b = toward the thumb, c = out of the palm.
// The thumb side follows from handedness: right hand b = F x N, left hand b = N x F, so a
// right hand with its palm to the camera and fingers up has its thumb toward the body's
// midline, and with the back of the hand to the camera its thumb points away from the body.
'use strict';
const L = require('./lib');
const { clamp, lerp, mix, rgba } = L;

const V = {
  add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
  sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
  mul: (a, k) => [a[0] * k, a[1] * k, a[2] * k],
  dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
  cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
  len: (a) => Math.hypot(a[0], a[1], a[2]),
  norm: (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; },
  lerp: (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)],
};

// index, middle, ring, little: knuckle (MCP) position, phalanx lengths, base radius, natural splay
const FINGERS = [
  { mcp: [0.80, 0.21], len: [0.36, 0.215, 0.18], r: 0.093, splay: 0.1 },
  { mcp: [0.855, 0.072], len: [0.40, 0.24, 0.19], r: 0.096, splay: 0.02 },
  { mcp: [0.815, -0.07], len: [0.37, 0.23, 0.18], r: 0.09, splay: -0.06 },
  { mcp: [0.735, -0.205], len: [0.29, 0.18, 0.16], r: 0.078, splay: -0.15 },
];
// curl per finger (0 straight .. 1 fist); th = [abduction, opposition, flexion]; spread 0..1
const PRESETS = {
  relax: { curl: [0.3, 0.36, 0.42, 0.48], th: [0.32, 0.12, 0.2], spread: 0.12 },
  open: { curl: [0.06, 0.05, 0.08, 0.12], th: [0.72, 0.0, 0.08], spread: 0.38 },
  offer: { curl: [0.16, 0.19, 0.23, 0.29], th: [0.55, 0.1, 0.14], spread: 0.1 },
  cup: { curl: [0.32, 0.36, 0.4, 0.45], th: [0.42, 0.3, 0.18], spread: 0.06 },
  hold: { curl: [0.5, 0.55, 0.6, 0.64], th: [0.3, 0.45, 0.25], spread: 0.02 },
  pinch: { curl: [0.42, 0.38, 0.5, 0.58], th: [0.42, 0.55, 0.22], spread: 0.1 },
  grip: { curl: [0.7, 0.74, 0.78, 0.82], th: [0.15, 0.6, 0.38], spread: 0 },
  fist: { curl: [0.96, 1.0, 1.0, 1.0], th: [0.08, 0.72, 0.55], spread: 0 },
  pen: { curl: [0.4, 0.62, 0.82, 0.9], th: [0.32, 0.6, 0.3], spread: 0 },
};
PRESETS.knock = PRESETS.fist;
PRESETS.point = PRESETS.pen;

function preset(name) { return PRESETS[name] || PRESETS.relax; }
function blendPreset(a, b, k) {
  const A = typeof a === 'string' ? preset(a) : a, B = typeof b === 'string' ? preset(b) : b;
  return {
    curl: A.curl.map((v, i) => lerp(v, B.curl[i], k)),
    th: A.th.map((v, i) => lerp(v, B.th[i], k)),
    spread: lerp(A.spread, B.spread, k),
  };
}

// thumb metacarpal directions (hand-local a, b, c): along the index, out to the side, across the palm
const TH_ADD = [0.9, 0.42, 0.1], TH_ABD = [0.6, 0.79, 0.12], TH_OPP = [0.45, 0.05, 0.88];
const TH_BEND = V.norm([-0.15, -0.75, 0.62]);

// Keep a hand within a wrist's natural range relative to its forearm: it bends toward the palm up
// to about 60 degrees, back toward the forearm only about 25, and sideways about 20, so a hand is
// never folded back unnaturally against the wrist.
function limitWrist(fore, f, n) {
  const d = V.norm(fore);
  let np = V.sub(n, V.mul(d, V.dot(n, d)));
  if (V.len(np) < 1e-3) return V.norm(f);
  np = V.norm(np);
  const t = V.cross(d, np);
  const x = V.dot(f, d), y = V.dot(f, np), z = V.dot(f, t);
  const flex = clamp(Math.atan2(y, x), -0.44, 1.05);
  const dev = clamp(Math.atan2(z, Math.hypot(x, y)), -0.35, 0.35);
  const cd = Math.cos(dev);
  return V.norm(V.add(V.add(V.mul(d, Math.cos(flex) * cd), V.mul(np, Math.sin(flex) * cd)), V.mul(t, Math.sin(dev))));
}

// --------------------------------------------------------------------------- geometry
// spec: { f: finger direction (world), n: palm normal (world), right: bool, shape: preset object,
//         scale, wrist: [x,y] forearm unit direction on screen (for the wrist stub) }
function build(W, s, spec) {
  const HS = s * 1.0 * (spec.scale || 1);
  const F = V.norm(spec.f);
  let N = V.sub(spec.n, V.mul(F, V.dot(spec.n, F)));
  if (V.len(N) < 1e-3) N = Math.abs(F[2]) < 0.9 ? V.norm(V.cross(F, [0, 0, 1])) : [0, 1, 0];
  N = V.norm(N);
  const T = spec.right ? V.cross(F, N) : V.cross(N, F);
  const toW = (a, b, c) => [F[0] * a + T[0] * b + N[0] * c, F[1] * a + T[1] * b + N[1] * c, F[2] * a + T[2] * b + N[2] * c];
  const P = (a, b, c) => { const w = toW(a, b, c); return [W[0] + w[0] * HS, W[1] - w[1] * HS, w[2] * HS]; };
  const sh = spec.shape || PRESETS.relax;
  const fan = 0.6 * Math.abs(F[2]); // fingers pointing at the camera fan out so none hide behind another
  const fingers = FINGERS.map((fg, i) => {
    const c = clamp(sh.curl[i], 0, 1.05);
    const phi = fg.splay * (0.35 + 1.3 * sh.spread + fan) * (1 - 0.75 * Math.min(1, c));
    const th = [c * 1.38, c * (1.38 + 1.62), c * (1.38 + 1.62 + 1.05)];
    let p = [fg.mcp[0], fg.mcp[1], 0];
    const pts = [p], dirs = [];
    for (let k = 0; k < 3; k++) {
      const d = [Math.cos(th[k]) * Math.cos(phi), Math.cos(th[k]) * Math.sin(phi), Math.sin(th[k])];
      dirs.push({ d, th: th[k], phi });
      p = V.add(p, V.mul(d, fg.len[k]));
      pts.push(p);
    }
    return { i, local: pts, dirs, r: fg.r, curl: c };
  });
  // thumb
  const [abd, opp, tc] = sh.th;
  const tcurl = Math.max(0.12, tc); // a thumb is never perfectly straight
  const d0 = V.norm(V.add(V.mul(V.lerp(TH_ADD, TH_ABD, abd), 1 - opp), V.mul(TH_OPP, opp)));
  const d1 = V.norm(V.add(d0, V.mul(TH_BEND, tcurl * 0.85)));
  const d2 = V.norm(V.add(d1, V.mul(TH_BEND, tcurl * 1.2)));
  const q0 = [0.08, 0.13, 0.0];
  // metacarpal, proximal and distal phalanx: the thumb leaves the palm a little below its middle
  const q1 = V.add(q0, V.mul(d0, 0.35)), q2 = V.add(q1, V.mul(d1, 0.25)), q3 = V.add(q2, V.mul(d2, 0.21));
  const thumb = { local: [q0, q1, q2, q3], radii: [0.155, 0.112, 0.096, 0.09] };
  // palm slab outline (both faces), knuckle line slightly arched
  // the knuckle edge sits just under the finger roots, so the fingers always cover it
  const outline = [[0, -0.21], [0.3, -0.27], [0.56, -0.285], [0.7, -0.255], [0.74, -0.18], [0.77, -0.07], [0.785, 0.06], [0.76, 0.19],
    [0.7, 0.27], [0.52, 0.29], [0.26, 0.27], [0.04, 0.225]];
  const palmPts = [];
  for (const [a, b] of outline) { palmPts.push(P(a, b, -0.09)); palmPts.push(P(a, b, 0.065)); }
  // the thenar mound and the web between thumb and index belong to the palm silhouette
  const web = V.lerp(q0, q1, 0.85);
  palmPts.push(P(web[0], web[1], web[2] - 0.05), P(web[0], web[1], web[2] + 0.05));
  return { HS, F, N, T, P, toW, fingers, thumb, palmPts, sh, W };
}

// --------------------------------------------------------------------------- drawing helpers
function hull(pts) {
  const p = pts.map((q) => [q[0], q[1]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const q of p) { while (lo.length >= 2 && cross(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  for (let i = p.length - 1; i >= 0; i--) { const q = p[i]; while (up.length >= 2 && cross(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
  up.pop(); lo.pop();
  return lo.concat(up);
}
// tapered capsule, always wound the same way so several capsules union under nonzero fill
function capsule(path, A, rA, B, rB) {
  const dx = B[0] - A[0], dy = B[1] - A[1], d = Math.hypot(dx, dy);
  if (d < Math.abs(rA - rB) + 0.5) {
    const C = rA >= rB ? A : B, r = Math.max(rA, rB);
    path.moveTo(C[0] + r, C[1]); path.arc(C[0], C[1], r, 0, L.TAU, false); return;
  }
  const al = Math.atan2(dy, dx), be = Math.asin(clamp((rA - rB) / d, -0.99, 0.99));
  const a0 = al + Math.PI / 2 + be, a1 = al + Math.PI * 1.5 - be;
  path.moveTo(A[0] + rA * Math.cos(a0), A[1] + rA * Math.sin(a0));
  path.arc(A[0], A[1], rA, a0, a1, false);
  path.lineTo(B[0] + rB * Math.cos(a1), B[1] + rB * Math.sin(a1));
  path.arc(B[0], B[1], rB, a1, a0 + L.TAU, false);
  path.closePath();
}
function polyPath(path, pts) {
  // clockwise on screen
  let area = 0;
  for (let i = 0; i < pts.length; i++) { const a = pts[i], b = pts[(i + 1) % pts.length]; area += a[0] * b[1] - b[0] * a[1]; }
  const q = area < 0 ? pts.slice().reverse() : pts;
  L.crPath(path, q, true, 0.35);
}

// outline + fill + soft form shadow for one part (a union of shapes)
function inkPart(ctx, build_, o) {
  const p = new (require('@napi-rs/canvas').Path2D)();
  build_(p);
  // outline: drawn under the fill, so only the outer half of the stroke (the silhouette) survives
  if (o.lw > 0) {
    const PathC = require('@napi-rs/canvas').Path2D;
    const holes = (o.noInk || []).concat(o.fade ? [o.fade] : []);
    ctx.save();
    if (holes.length) {
      const c = new PathC();
      c.rect(-1e5, -1e5, 2e5, 2e5);
      for (const [x, y, r] of holes) { c.moveTo(x + r, y); c.arc(x, y, r, 0, L.TAU, true); }
      ctx.clip(c, 'evenodd');
    }
    ctx.lineJoin = 'round';
    ctx.strokeStyle = o.line; ctx.lineWidth = o.lw * 2;
    ctx.stroke(p);
    ctx.restore();
    // fade: the outline grows in gradually from a root (x, y) between radius r0 and r1, so a
    // finger or thumb never starts with an abrupt little tick of line where it meets the hand
    if (o.fade) {
      const [x, y, r1, r0] = o.fade;
      const steps = 5;
      for (let i = 0; i < steps; i++) {
        const a = r0 + (r1 - r0) * (i / steps), b = r0 + (r1 - r0) * ((i + 1) / steps);
        const ring = new PathC();
        ring.moveTo(x + b, y); ring.arc(x, y, b, 0, L.TAU, false);
        ring.moveTo(x + a, y); ring.arc(x, y, a, 0, L.TAU, true);
        ctx.save();
        ctx.clip(ring, 'evenodd');
        ctx.globalAlpha = (i + 0.5) / steps;
        ctx.lineJoin = 'round'; ctx.strokeStyle = o.line; ctx.lineWidth = o.lw * 2;
        ctx.stroke(p);
        ctx.restore();
      }
    }
  }
  ctx.fillStyle = o.fill;
  ctx.fill(p, 'nonzero');
  if (o.shade) {
    ctx.save();
    ctx.clip(p, 'nonzero');
    o.shade(ctx);
    ctx.restore();
  }
  return p;
}

// --------------------------------------------------------------------------- the hand
// Returns { parts, draw(ctx, pick), gripAt(r) }. Parts are drawn in groups: the palm and the fingers
// lying over it share ONE outline (their silhouette), and the lines between fingers are soft interior
// lines that fade out toward the knuckles, as in a drawn hand, rather than every piece being outlined
// like a jointed doll. Callers can draw the parts behind a held prop, then the prop, then the rest.
//
// The thumb's base (the thenar mound) is part of the palm, knuckles are soft bumps of light and shade
// (never lines), and each nail is an arch that fills the end of the fingertip.
function handParts(W, s, st, Lt, spec) {
  const g = build(W, s, spec);
  const { P, HS, N } = g;
  const lw = (Lt.lineW || 1) * s * 0.02 * 0.85;
  const key = Lt.key || '#ffffff';
  const skin = L.mul(st.skin, key);
  const skinSh = L.mul(st.skinShadow, Lt.amb || '#ffffff');
  const skinHi = mix(skin, '#fff2e8', 0.35);
  const palmCol = mix(skin, '#f4c0b0', 0.12);
  const nailCol = mix(skin, '#ffe6e2', 0.5);
  const side = Lt.side || -1; // light from screen-left when -1
  const lightDir = [-side, 0]; // screen direction toward the light
  const facing = N[2]; // >0: palm toward the viewer
  const center = P(0.45, 0, 0);
  const parts = [];
  const PathC = require('@napi-rs/canvas').Path2D;
  // form shadow along the side of a finger away from the light: ONE continuous stroke (no overlapping
  // caps, which would leave dark dots at the joints), on the same side along the whole finger
  const bandShade = (cx, pts, r, a = 0.32) => {
    if (pts.length < 2) return;
    const e = pts[pts.length - 1], b0 = pts[0];
    let gx = -(e[1] - b0[1]), gy = e[0] - b0[0];
    const sgn = gx * lightDir[0] + gy * lightDir[1] > 0 ? -1 : 1;
    const off = pts.map((q, i) => {
      const A = pts[Math.max(0, i - 1)], B = pts[Math.min(pts.length - 1, i + 1)];
      let nx = -(B[1] - A[1]), ny = B[0] - A[0];
      const l = Math.hypot(nx, ny) || 1;
      return [q[0] + sgn * nx / l * r * 0.72, q[1] + sgn * ny / l * r * 0.72];
    });
    cx.lineCap = 'round'; cx.lineJoin = 'round';
    cx.beginPath(); L.crPath(cx, off, false, 0.5);
    cx.strokeStyle = rgba(skinSh, a); cx.lineWidth = r * 0.95; cx.stroke();
  };
  const soft = (cx, x, y, r, col, a) => {
    cx.fillStyle = L.radial(cx, x, y, 0, r, [[0, rgba(col, a)], [1, rgba(col, 0)]]);
    cx.fillRect(x - r, y - r, r * 2, r * 2);
  };
  const tp = g.thumb.local.map((q) => P(...q));
  const tr = g.thumb.radii.map((r) => r * HS);
  const ph = hull(g.palmPts);
  const wristCut = (() => { const a = P(-0.04, 0, 0); return [a[0], a[1], HS * 0.25]; })();
  // palm + thenar mound
  parts.push({
    kind: 'palm', depth: center[2], fill: facing > 0.15 ? palmCol : skin, holes: [wristCut],
    build: (p) => { polyPath(p, ph); capsule(p, tp[0], tr[0], tp[1], tr[1] * 1.02); },
    shade: (cx) => {
      const c = P(0.42, 0, 0);
      const gr = cx.createLinearGradient(c[0] + lightDir[0] * HS * 0.2, c[1], c[0] - lightDir[0] * HS * 0.5, c[1]);
      gr.addColorStop(0, rgba(skinSh, 0)); gr.addColorStop(1, rgba(skinSh, 0.45));
      cx.fillStyle = gr; cx.fillRect(c[0] - HS * 2, c[1] - HS * 2, HS * 4, HS * 4);
      if (HS < 22) return;
      if (facing > 0.25) {
        const hol = P(0.48, -0.02, 0.07);
        soft(cx, hol[0], hol[1], HS * 0.3, skinSh, 0.28 * facing);
        const mound = P(0.22, 0.14, 0.08);
        soft(cx, mound[0], mound[1], HS * 0.22, skinHi, 0.45 * facing);
        if (HS > 40) {
          cx.lineCap = 'round';
          L.strokeSmooth(cx, [P(0.14, 0.08, 0.07), P(0.32, 0.03, 0.07), P(0.56, 0.12, 0.07), P(0.68, 0.2, 0.07)].map((q) => [q[0], q[1]]), rgba(skinSh, 0.3 * facing), lw * 0.75);
          L.strokeSmooth(cx, [P(0.62, -0.25, 0.07), P(0.65, -0.08, 0.07), P(0.61, 0.08, 0.07)].map((q) => [q[0], q[1]]), rgba(skinSh, 0.24 * facing), lw * 0.65);
        }
      } else if (facing < -0.15) {
        g.fingers.forEach((f, i) => {
          const k = P(FINGERS[i].mcp[0] - 0.04, FINGERS[i].mcp[1], -0.09);
          soft(cx, k[0], k[1], f.r * HS * 1.25, skinHi, 0.55 * -facing);
          if (i < 3) {
            const v = P((FINGERS[i].mcp[0] + FINGERS[i + 1].mcp[0]) / 2 - 0.07, (FINGERS[i].mcp[1] + FINGERS[i + 1].mcp[1]) / 2, -0.09);
            soft(cx, v[0], v[1], f.r * HS * 0.9, skinSh, 0.3 * -facing);
          }
        });
      }
    },
  });
  for (const f of g.fingers) {
    const base = V.sub(f.local[0], [0.14, 0, 0]);
    const pts = [base, ...f.local].map((q) => P(...q));
    const r0 = f.r * HS;
    const radii = [r0, r0, r0 * 0.95, r0 * 0.88, r0 * 0.8];
    const behind = facing < -0.1 && f.curl > 0.55;
    let depth = center[2] + (behind ? -HS * 0.2 : HS * 0.04 + (facing > 0.2 && f.curl > 0.4 ? HS * 0.16 : 0));
    depth += f.i * 1e-3 * (facing > 0 ? 1 : -1);
    const d2 = f.dirs[2], d1 = f.dirs[1];
    const dorsalTip = g.toW(Math.sin(d2.th) * Math.cos(d2.phi), Math.sin(d2.th) * Math.sin(d2.phi), -Math.cos(d2.th));
    const dorsalMid = g.toW(Math.sin(d1.th) * Math.cos(d1.phi), Math.sin(d1.th) * Math.sin(d1.phi), -Math.cos(d1.th));
    parts.push({
      kind: 'finger', behind, depth, i: f.i, fill: facing > 0.3 && f.curl < 0.3 ? palmCol : skin,
      holes: behind ? [] : [[pts[0][0], pts[0][1], r0 * 1.4]],
      root: behind ? null : [pts[1][0], pts[1][1], r0 * 3.6, r0 * 1.7],
      build: (p) => { for (let k = 0; k < 4; k++) capsule(p, pts[k], radii[k], pts[k + 1], radii[k + 1]); },
      // the soft line between fingers follows the finger from its knuckle on, never the buried base
      edge: (p) => { for (let k = 1; k < 4; k++) capsule(p, pts[k], radii[k], pts[k + 1], radii[k + 1]); },
      shade: (cx) => {
        bandShade(cx, pts.slice(1), radii[2]);
        if (!behind) soft(cx, pts[1][0], pts[1][1], r0 * 1.6, skinSh, 0.16);
        if (dorsalMid[2] > 0.15 && HS > 24 && f.curl > 0.1) soft(cx, pts[2][0], pts[2][1], radii[2] * 1.05, skinHi, 0.42 * dorsalMid[2]);
      },
      details: (ctx, path) => { if (dorsalTip[2] > 0.12 && HS > 14) drawNail(ctx, path, pts[4], pts[3], radii[4], dorsalTip, nailCol, st.line, lw); },
    });
  }
  {
    const tipW = g.toW(...g.thumb.local[3]), baseW = g.toW(0.45, 0, 0);
    const front = V.dot(V.sub(tipW, baseW), [0, 0, 1]);
    // the thumb's pad faces the way it flexes, so its nail faces the opposite way
    const dv = V.norm(V.sub(g.thumb.local[3], g.thumb.local[2]));
    const away = V.mul(TH_BEND, -1);
    const dorsal = g.toW(...V.norm(V.sub(away, V.mul(dv, V.dot(away, dv)))));
    parts.push({
      kind: 'thumb', depth: center[2] + (front > 0 ? HS * 0.25 : -HS * 0.25) + front * HS * 0.1, fill: skin,
      holes: [], root: [tp[1][0], tp[1][1], tr[1] * 2.4, tr[1] * 0.95],
      build: (p) => { capsule(p, tp[1], tr[1], tp[2], tr[2]); capsule(p, tp[2], tr[2], tp[3], tr[3]); },
      shade: (cx) => bandShade(cx, tp.slice(1), tr[2]),
      details: (ctx, path) => { if (dorsal[2] > 0.15 && HS > 14) drawNail(ctx, path, tp[3], tp[2], tr[3], dorsal, nailCol, st.line, lw); },
    });
  }
  parts.sort((a, b) => a.depth - b.depth);
  for (const q of parts) {
    q.path = new PathC(); q.build(q.path);
    if (q.edge) { q.edgePath = new PathC(); q.edge(q.edgePath); }
  }
  const gripLocal = [0.5, 0.02, 0.0];
  const ink = { line: st.line, soft: mix(skinSh, st.line, 0.35), lw };
  const draw = (ctx, pick) => drawHandGroups(ctx, parts.filter((q) => !pick || pick(q)), ink);
  // legacy per-part drawing (each part as its own group)
  for (const q of parts) q.draw = (ctx) => drawHandGroups(ctx, [q], ink);
  return { parts, draw, g, center, P, HS, lw, skin, skinSh, N, palmFacing: facing, gripAt: (r) => P(gripLocal[0] + 0.05, gripLocal[1], 0.07 + r / HS) };
}

// Draw hand parts back to front. Consecutive palm/finger parts on the same side of the palm form one
// group with one outline; the thumb is its own group. Inside a group, later parts get a soft interior
// line that fades in from the knuckle, so fingers read as separate without any doll-like seams.
function drawHandGroups(ctx, parts, ink) {
  const PathC = require('@napi-rs/canvas').Path2D;
  const groups = [];
  for (const q of parts) {
    const last = groups[groups.length - 1];
    const cat = q.kind === 'thumb' ? 'thumb' : q.behind ? 'behind' : 'front';
    if (last && last.cat === cat && cat !== 'thumb') last.items.push(q);
    else groups.push({ cat, items: [q] });
  }
  const clipHoles = (holes) => {
    const c = new PathC();
    c.rect(-1e5, -1e5, 2e5, 2e5);
    for (const [x, y, r] of holes) { c.moveTo(x + r, y); c.arc(x, y, r, 0, L.TAU, true); }
    ctx.clip(c, 'evenodd');
  };
  const fadeStroke = (path, root, style, width) => {
    const [x, y, r1, r0] = root;
    const steps = 5;
    for (let i = 0; i < steps; i++) {
      const a = r0 + (r1 - r0) * (i / steps), b = r0 + (r1 - r0) * ((i + 1) / steps);
      const ring = new PathC();
      ring.moveTo(x + b, y); ring.arc(x, y, b, 0, L.TAU, false);
      ring.moveTo(x + a, y); ring.arc(x, y, a, 0, L.TAU, true);
      ctx.save(); ctx.clip(ring, 'evenodd'); ctx.globalAlpha *= (i + 0.5) / steps;
      ctx.strokeStyle = style; ctx.lineWidth = width; ctx.stroke(path); ctx.restore();
    }
  };
  for (const gp of groups) {
    const union = new PathC();
    for (const q of gp.items) union.addPath(q.path);
    const holes = [].concat(...gp.items.map((q) => q.holes || []));
    // 1) silhouette outline under the fill
    ctx.save();
    ctx.lineJoin = 'round';
    if (gp.cat === 'thumb' && gp.items[0].root) {
      // the thumb grows out of the palm: its outline fades in from the root
      const root = gp.items[0].root;
      ctx.save(); clipHoles(holes.concat([[root[0], root[1], root[2]]])); ctx.strokeStyle = ink.line; ctx.lineWidth = ink.lw * 2; ctx.stroke(union); ctx.restore();
      fadeStroke(union, root, ink.line, ink.lw * 2);
    } else {
      if (holes.length) clipHoles(holes);
      ctx.strokeStyle = ink.line; ctx.lineWidth = ink.lw * 2; ctx.stroke(union);
    }
    ctx.restore();
    // 2) part by part: a soft edge line under each later part (fading in from its knuckle), then
    //    its fill and form shading. Drawing the line under the fill leaves only the part's own edge
    //    showing over the parts before it, never the joints inside it.
    gp.items.forEach((q, i) => {
      if (i > 0 && q.root && gp.cat !== 'thumb') {
        const root = q.root;
        ctx.save();
        ctx.clip(union, 'nonzero');
        const ep = q.edgePath || q.path;
        ctx.save(); clipHoles([[root[0], root[1], root[2]]]); ctx.strokeStyle = rgba(ink.soft, 0.8); ctx.lineWidth = ink.lw * 1.8; ctx.stroke(ep); ctx.restore();
        fadeStroke(ep, root, rgba(ink.soft, 0.8), ink.lw * 1.8);
        ctx.restore();
      }
      ctx.fillStyle = q.fill; ctx.fill(q.path, 'nonzero');
      ctx.save(); ctx.clip(q.path, 'nonzero'); q.shade(ctx); ctx.restore();
    });
    // 4) details (nails)
    for (const q of gp.items) if (q.details) q.details(ctx, q.path);
  }
}

// an arched nail on the end of a finger, clipped to the finger so it reaches its edges
function drawNail(ctx, fingerPath, tip, prev, r, dorsal, col, line, lw) {
  const ux0 = tip[0] - prev[0], uy0 = tip[1] - prev[1], ul = Math.hypot(ux0, uy0);
  if (ul < r * 0.15) return;
  const ux = ux0 / ul, uy = uy0 / ul, vx = -uy, vy = ux;
  const k = clamp(dorsal[2] * 1.1, 0.35, 1); // narrower when we see it at an angle
  const off = [dorsal[0] * r * 0.3 * (1 - k), -dorsal[1] * r * 0.3 * (1 - k)];
  const cx = tip[0] + off[0], cy = tip[1] + off[1];
  const w = r * 0.8 * k;
  const back = r * (0.55 + 0.5 * Math.min(1, ul / (r * 2)));
  const A = [cx - ux * back + vx * w, cy - uy * back + vy * w], Bp = [cx - ux * back - vx * w, cy - uy * back - vy * w];
  const arch = [cx - ux * (back + r * 0.35), cy - uy * (back + r * 0.35)];
  ctx.save();
  ctx.clip(fingerPath, 'nonzero');
  ctx.beginPath();
  ctx.moveTo(A[0], A[1]);
  ctx.quadraticCurveTo(arch[0], arch[1], Bp[0], Bp[1]);
  ctx.lineTo(cx + ux * r * 1.3 - vx * w, cy + uy * r * 1.3 - vy * w);
  ctx.lineTo(cx + ux * r * 1.3 + vx * w, cy + uy * r * 1.3 + vy * w);
  ctx.closePath();
  ctx.fillStyle = rgba(col, 0.92); ctx.fill();
  // the cuticle arch, and a little shine
  ctx.strokeStyle = rgba(line, 0.28); ctx.lineWidth = lw * 0.55;
  ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.quadraticCurveTo(arch[0], arch[1], Bp[0], Bp[1]); ctx.stroke();
  ctx.strokeStyle = rgba('#ffffff', 0.45); ctx.lineWidth = lw * 0.7; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(cx - ux * back * 0.6 + vx * w * 0.45, cy - uy * back * 0.6 + vy * w * 0.45); ctx.lineTo(cx + ux * r * 0.3 + vx * w * 0.45, cy + uy * r * 0.3 + vy * w * 0.45); ctx.stroke();
  ctx.restore();
}

// wrist stub from the cuff to the palm (drawn before the sleeve so the cuff overlaps it)
function drawWrist(ctx, W, dir, s, st, Lt) {
  const HS = s * 1.0;
  const skin = L.mul(st.skin, Lt.key || '#fff');
  const A = [W[0] - dir[0] * HS * 0.35, W[1] - dir[1] * HS * 0.35];
  const lw = (Lt.lineW || 1) * s * 0.02 * 0.85;
  inkPart(ctx, (p) => capsule(p, A, HS * 0.2, W, HS * 0.21), { fill: skin, line: st.line, lw, noInk: [] });
}

function drawHand3D(ctx, W, s, st, Lt, spec) {
  const h = handParts(W, s, st, Lt, spec);
  h.draw(ctx);
  return h;
}

module.exports = { handParts, drawHand3D, drawWrist, build, PRESETS, preset, blendPreset, V, capsule, inkPart, limitWrist, drawHandGroups };
