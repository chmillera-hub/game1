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
  { mcp: [0.80, 0.205], len: [0.36, 0.215, 0.18], r: 0.1, splay: 0.1 },
  { mcp: [0.855, 0.07], len: [0.40, 0.24, 0.19], r: 0.103, splay: 0.02 },
  { mcp: [0.815, -0.068], len: [0.37, 0.23, 0.18], r: 0.097, splay: -0.06 },
  { mcp: [0.735, -0.198], len: [0.29, 0.18, 0.16], r: 0.083, splay: -0.15 },
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
const TH_ADD = [0.9, 0.42, 0.1], TH_ABD = [0.58, 0.78, 0.22], TH_OPP = [0.45, 0.05, 0.88];
const TH_BEND = V.norm([-0.15, -0.75, 0.62]);

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
  const fingers = FINGERS.map((fg, i) => {
    const c = clamp(sh.curl[i], 0, 1.05);
    const phi = fg.splay * (0.35 + 1.3 * sh.spread) * (1 - 0.75 * Math.min(1, c));
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
  const q1 = V.add(q0, V.mul(d0, 0.3)), q2 = V.add(q1, V.mul(d1, 0.22)), q3 = V.add(q2, V.mul(d2, 0.19));
  const thumb = { local: [q0, q1, q2, q3], radii: [0.16, 0.118, 0.104, 0.092] };
  // palm slab outline (both faces), knuckle line slightly arched
  const outline = [[0, -0.21], [0.3, -0.27], [0.56, -0.285], [0.745, -0.26], [0.82, -0.18], [0.87, -0.07], [0.89, 0.06], [0.855, 0.19],
    [0.77, 0.27], [0.52, 0.29], [0.26, 0.27], [0.04, 0.225]];
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
    ctx.save();
    if (o.noInk && o.noInk.length) {
      const c = new (require('@napi-rs/canvas').Path2D)();
      c.rect(-1e5, -1e5, 2e5, 2e5);
      for (const [x, y, r] of o.noInk) { c.moveTo(x + r, y); c.arc(x, y, r, 0, L.TAU, true); }
      ctx.clip(c, 'evenodd');
    }
    ctx.lineJoin = 'round';
    ctx.strokeStyle = o.line; ctx.lineWidth = o.lw * 2;
    ctx.stroke(p);
    ctx.restore();
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
// Returns { parts: [{depth, draw(ctx)}], grip: [x,y,z], palm: [x,y,z] } so callers can draw a held
// prop between the parts behind it and the parts in front of it.
function handParts(W, s, st, Lt, spec) {
  const g = build(W, s, spec);
  const { P, HS, N } = g;
  const lw = (Lt.lineW || 1) * s * 0.02 * 0.85;
  const key = Lt.key || '#ffffff';
  const skin = L.mul(st.skin, key);
  const skinSh = L.mul(st.skinShadow, Lt.amb || '#ffffff');
  const palmCol = mix(skin, '#f4c0b0', 0.12);
  const side = Lt.side || -1; // light from screen-left when -1
  const lightDir = [-side, 0]; // screen direction toward the light
  const facing = N[2]; // >0: palm toward the viewer
  const center = P(0.45, 0, 0);
  const parts = [];
  // shadow band along the edge of a capsule chain facing away from the light
  const bandShade = (pts, r, k) => (cx) => {
    cx.lineCap = 'round'; cx.lineJoin = 'round';
    for (let i = 0; i < pts.length - 1; i++) {
      const A = pts[i], B = pts[i + 1];
      let nx = -(B[1] - A[1]), ny = B[0] - A[0];
      const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
      if (nx * lightDir[0] + ny * lightDir[1] > 0) { nx = -nx; ny = -ny; }
      const off = r * 0.75;
      cx.strokeStyle = rgba(skinSh, 0.5 * k);
      cx.lineWidth = r * 0.9;
      cx.beginPath(); cx.moveTo(A[0] + nx * off, A[1] + ny * off); cx.lineTo(B[0] + nx * off, B[1] + ny * off); cx.stroke();
    }
  };
  // palm
  const ph = hull(g.palmPts);
  const wristCut = (() => { const a = P(-0.02, 0, 0); return [a[0], a[1], HS * 0.24]; })();
  parts.push({
    kind: 'palm', depth: center[2],
    draw: (ctx) => {
      inkPart(ctx, (p) => polyPath(p, ph), {
        fill: facing > 0.15 ? palmCol : skin, line: st.line, lw, noInk: [wristCut],
        shade: (cx) => {
          // form shadow across the palm, away from the light
          const c = P(0.42, 0, 0);
          const gr = cx.createLinearGradient(c[0] + lightDir[0] * HS * 0.2, c[1], c[0] - lightDir[0] * HS * 0.45, c[1]);
          gr.addColorStop(0, rgba(skinSh, 0)); gr.addColorStop(1, rgba(skinSh, 0.5));
          cx.fillStyle = gr; cx.fillRect(c[0] - HS * 2, c[1] - HS * 2, HS * 4, HS * 4);
          if (HS > 34) {
            cx.lineCap = 'round';
            if (facing > 0.25) {
              // palm creases: thenar line around the thumb base, heart line under the fingers
              L.strokeSmooth(cx, [P(0.12, 0.08, 0.07), P(0.32, 0.03, 0.07), P(0.56, 0.12, 0.07), P(0.7, 0.2, 0.07)].map((q) => [q[0], q[1]]), rgba(skinSh, 0.55 * facing), lw * 0.8);
              L.strokeSmooth(cx, [P(0.62, -0.25, 0.07), P(0.66, -0.08, 0.07), P(0.62, 0.08, 0.07)].map((q) => [q[0], q[1]]), rgba(skinSh, 0.45 * facing), lw * 0.7);
            } else if (facing < -0.25) {
              // back of the hand: faint tendons toward the knuckles
              for (const b of [0.15, 0.05, -0.07]) L.strokeSmooth(cx, [P(0.2, b * 0.6, -0.09), P(0.72, b, -0.09)].map((q) => [q[0], q[1]]), rgba(skinSh, 0.22), lw * 0.7);
            }
          }
        },
      });
    },
  });
  // fingers
  for (const f of g.fingers) {
    const pts = f.local.map((q) => P(...q));
    const radii = [f.r, f.r * 0.95, f.r * 0.88, f.r * 0.8].map((r) => r * HS);
    const mid = f.local[2];
    const sideSign = V.dot(V.sub(g.toW(...mid), g.toW(0.45, 0, 0)), N);
    // curled fingers are on the palm side: in front when the palm faces us, behind when the back does
    let depth = center[2] + (sideSign * Math.sign(facing || 1) > 0.02 ? HS * 0.2 : facing > 0 ? HS * 0.05 : -HS * 0.05);
    if (f.curl > 0.45 && facing < -0.1) depth = center[2] - HS * 0.2;
    depth += pts.reduce((a, q) => a + q[2], 0) / pts.length * 0.15 + f.i * 1e-3 * Math.sign(-facing || 1);
    parts.push({
      kind: 'finger', depth, i: f.i,
      draw: (ctx) => {
        inkPart(ctx, (p) => { for (let k = 0; k < 3; k++) capsule(p, pts[k], radii[k], pts[k + 1], radii[k + 1]); }, {
          fill: facing > 0.3 && f.curl < 0.3 ? palmCol : skin, line: st.line, lw, noInk: [[pts[0][0], pts[0][1], radii[0] * 1.05]],
          shade: bandShade(pts, radii[1], 1),
        });
        // fingernail on the dorsal side of the fingertip, when that side faces us
        const d = f.dirs[2];
        const dorsal = g.toW(Math.sin(d.th) * Math.cos(d.phi), Math.sin(d.th) * Math.sin(d.phi), -Math.cos(d.th));
        if (dorsal[2] > 0.18 && HS > 14) {
          const tip = pts[3], prev = pts[2];
          const ux = tip[0] - prev[0], uy = tip[1] - prev[1], ul = Math.hypot(ux, uy) || 1;
          const off = [dorsal[0] * radii[3] * 0.35, -dorsal[1] * radii[3] * 0.35];
          const nx = tip[0] - ux / ul * radii[3] * 0.55 + off[0], ny = tip[1] - uy / ul * radii[3] * 0.55 + off[1];
          const along = Math.max(radii[3] * 0.5, Math.min(radii[3] * 1.0, ul * 0.45));
          ctx.save();
          ctx.translate(nx, ny); ctx.rotate(Math.atan2(uy, ux));
          ctx.fillStyle = rgba(mix(skin, '#fff4f0', 0.45), 0.9);
          ctx.beginPath(); ctx.ellipse(0, 0, along * 0.62, radii[3] * 0.62 * clamp(dorsal[2] + 0.2, 0.4, 1), 0, 0, L.TAU); ctx.fill();
          ctx.strokeStyle = rgba(st.line, 0.35); ctx.lineWidth = lw * 0.6; ctx.stroke();
          ctx.restore();
        }
        // knuckle creases on the back of bent fingers (close-ups)
        if (HS > 40 && facing < 0.2 && f.curl > 0.15) {
          for (const k of [2]) {
            const c = pts[k], a = pts[k - 1], b = pts[k + 1];
            const ux = b[0] - a[0], uy = b[1] - a[1], ul = Math.hypot(ux, uy) || 1;
            const nx = -uy / ul, ny = ux / ul, r = radii[k] * 0.55;
            ctx.strokeStyle = rgba(skinSh, 0.32); ctx.lineWidth = lw * 0.55; ctx.lineCap = 'round';
            ctx.beginPath(); ctx.moveTo(c[0] - nx * r, c[1] - ny * r); ctx.quadraticCurveTo(c[0] + ux / ul * r * 0.3, c[1] + uy / ul * r * 0.3, c[0] + nx * r, c[1] + ny * r); ctx.stroke();
          }
        }
      },
    });
  }
  // thumb
  {
    const pts = g.thumb.local.map((q) => P(...q));
    const radii = g.thumb.radii.map((r) => r * HS);
    const tipW = g.toW(...g.thumb.local[3]), baseW = g.toW(0.45, 0, 0);
    const front = V.dot(V.sub(tipW, baseW), [0, 0, 1]);
    const depth = center[2] + (front > 0 ? HS * 0.25 : -HS * 0.25) + front * HS * 0.1;
    parts.push({
      kind: 'thumb', depth,
      draw: (ctx) => {
        inkPart(ctx, (p) => { for (let k = 0; k < 3; k++) capsule(p, pts[k], radii[k], pts[k + 1], radii[k + 1]); }, {
          fill: skin, line: st.line, lw, noInk: [[pts[0][0], pts[0][1], radii[0] * 1.1], wristCut],
          shade: bandShade(pts, radii[1], 1),
        });
        const d = V.sub(g.thumb.local[3], g.thumb.local[2]);
        const dorsal = g.toW(...V.norm(V.cross(d, [0, 0, 1]).map((v, i) => v + [0, 0.3, -0.6][i])));
        if (dorsal[2] > 0.2 && HS > 14) {
          const tip = pts[3], prev = pts[2];
          const ux = tip[0] - prev[0], uy = tip[1] - prev[1], ul = Math.hypot(ux, uy) || 1;
          ctx.save();
          ctx.translate(tip[0] - ux / ul * radii[3] * 0.5, tip[1] - uy / ul * radii[3] * 0.5); ctx.rotate(Math.atan2(uy, ux));
          ctx.fillStyle = rgba(mix(skin, '#fff4f0', 0.45), 0.9);
          ctx.beginPath(); ctx.ellipse(0, 0, radii[3] * 0.6, radii[3] * 0.6 * clamp(dorsal[2] + 0.2, 0.4, 1), 0, 0, L.TAU); ctx.fill();
          ctx.strokeStyle = rgba(st.line, 0.35); ctx.lineWidth = lw * 0.6; ctx.stroke();
          ctx.restore();
        }
      },
    });
  }
  parts.sort((a, b) => a.depth - b.depth);
  const gripLocal = [0.5, 0.02, 0.0];
  return { parts, g, center, P, HS, lw, skin, skinSh, N, palmFacing: facing, gripAt: (r) => P(gripLocal[0] + 0.05, gripLocal[1], 0.07 + r / HS) };
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
  for (const p of h.parts) p.draw(ctx);
  return h;
}

module.exports = { handParts, drawHand3D, drawWrist, build, PRESETS, preset, blendPreset, V, capsule, inkPart };
