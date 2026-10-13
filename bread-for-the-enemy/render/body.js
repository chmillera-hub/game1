// Bodies, arms, hands and props. Units: s = head unit (half face width) in px.
'use strict';
const L = require('./lib');
const { clamp, lerp, mix, rgba, shade, smooth } = L;

const lit = (c, Lt) => L.mul(c, Lt.key || '#ffffff');
const shd = (c, Lt) => L.mul(shade(c, 0.6), Lt.amb || '#ffffff');

// ---------------------------------------------------------------- torso
// B: neck base (screen). by: body yaw (-0.6..0.6), sh: shoulder raise (units)
// X() follows the curved front of the chest; Xc() is a flatter projection used for the collar,
// the neck base and the joints inside the body, so the neck always sits in the neck hole.
function torsoPts(B, s, by, sh, len = 9) {
  const c = Math.cos(by), sn = Math.sin(by);
  const X = (x, y) => {
    const z = 0.9 * Math.sqrt(Math.max(0, 1 - Math.pow(x / 2.6, 2)));
    return [B[0] + (x * c + z * sn) * s, B[1] + y * s];
  };
  const Xc = (x, y, z = 0.5) => [B[0] + (x * c + z * sn) * s, B[1] + y * s];
  const R = [[1.3, 0.16 - sh * 0.5], [1.9, 0.6 - sh], [2.02, 1.3 - sh * 0.6], [1.88, 2.3], [1.68, 3.7], [1.8, 4.9], [2.05, len]];
  const right = [Xc(0.62, -0.22), ...R.map(([x, y]) => X(x, y))];
  const left = [Xc(-0.62, -0.22), ...R.map(([x, y]) => X(-x, y))];
  return { X, Xc, right, left };
}
// the opening of the neckline (screen points, clockwise from the left collar corner)
function collarPts(B, s, by, kind) {
  const c = Math.cos(by), sn = Math.sin(by);
  const Xc = (x, y) => [B[0] + (x * c + 0.5 * sn) * s, B[1] + y * s];
  if (kind === 'v') return [Xc(-0.62, -0.22), Xc(-0.36, 0.55), Xc(0, 1.55), Xc(0.36, 0.55), Xc(0.62, -0.22)];
  return [Xc(-0.62, -0.22), Xc(-0.5, 0.2), Xc(0, 0.46), Xc(0.5, 0.2), Xc(0.62, -0.22)];
}
function neckBase(B, s, by) { return [B[0] + 0.5 * Math.sin(by) * s, B[1]]; }

const clothShadow = (c, Lt) => mix(lit(c, Lt), shd(c, Lt), 0.78);

function drawTorso(ctx, B, s, st, Lt, o) {
  const by = o.by || 0, sh = o.shoulder || 0, len = o.len || 9;
  const cl = st.cloth;
  const { X, Xc, right, left } = torsoPts(B, s, by, sh, len);
  const lw = (Lt.lineW || 1) * s * 0.02;
  const side = Lt.side || -1;
  const outline = [...left.slice().reverse(), ...right];
  const collar = collarPts(B, s, by, cl.neck);
  // the neck hole is cut out of the cloth (the neck and chest drawn underneath show through it);
  // the hole reaches up past the collar corners so no sliver of cloth can cross the neck
  const PathC = require('@napi-rs/canvas').Path2D;
  const hole = new PathC();
  hole.rect(-1e5, -1e5, 2e5, 2e5);
  const up = [Xc(0.8, -1.6), Xc(-0.8, -1.6)];
  L.crPath(hole, collar, false, 0.5);
  hole.lineTo(up[0][0], up[0][1]); hole.lineTo(up[1][0], up[1][1]); hole.closePath();
  ctx.save();
  ctx.clip(hole, 'evenodd');
  ctx.save();
  ctx.beginPath();
  L.crPath(ctx, outline, false, 0.45);
  ctx.closePath();
  ctx.fillStyle = lit(cl.tunic, Lt);
  ctx.fill();
  ctx.clip();
  // shadow side: a soft form shadow, not a second colour
  const mid = X(-side * 1.1, 0);
  const g = ctx.createLinearGradient(mid[0] + side * s * 0.4, 0, mid[0] - side * s * 1.4, 0);
  g.addColorStop(0, rgba(clothShadow(cl.tunic, Lt), 0));
  g.addColorStop(1, rgba(clothShadow(cl.tunic, Lt), 0.82));
  ctx.fillStyle = g;
  ctx.fillRect(B[0] - 20 * s, B[1] - 4 * s, 40 * s, 30 * s);
  // chin/head shadow on the chest
  ctx.fillStyle = L.radial(ctx, Xc(0, 0.2)[0], B[1] + s * 0.25, 0, s * 1.3, [[0, rgba(clothShadow(cl.tunic, Lt), 0.5)], [1, rgba(clothShadow(cl.tunic, Lt), 0)]]);
  ctx.fillRect(B[0] - s * 2.5, B[1] - s, s * 5, s * 3);
  // the chest is full, not sunken: soft light across the lit side of the chest
  const pc = X(side * 0.95, 1.7);
  ctx.fillStyle = L.radial(ctx, pc[0], pc[1], 0, s * 1.5, [[0, rgba(shade(lit(cl.tunic, Lt), 1.12), 0.35)], [1, rgba(shade(lit(cl.tunic, Lt), 1.12), 0)]]);
  ctx.fillRect(pc[0] - s * 1.6, pc[1] - s * 1.6, s * 3.2, s * 3.2);
  // armor (guard)
  if (cl.armor) {
    const m = st.metal || '#8a8d92';
    for (let i = 0; i < 5; i++) {
      const y = 1.0 + i * 0.75;
      const band = [X(-2.4, y), X(-1.2, y + 0.18), X(0, y + 0.22), X(1.2, y + 0.18), X(2.4, y)];
      const band2 = [X(2.4, y + 0.7), X(1.2, y + 0.88), X(0, y + 0.92), X(-1.2, y + 0.88), X(-2.4, y + 0.7)];
      ctx.beginPath(); L.crPath(ctx, band, false); ctx.lineTo(...band2[0]); L.crPath({ moveTo() {}, bezierCurveTo: (...a) => ctx.bezierCurveTo(...a) }, band2, false); ctx.closePath();
      ctx.fillStyle = i % 2 ? lit(m, Lt) : lit(shade(m, 0.85), Lt); ctx.fill();
      ctx.strokeStyle = rgba(st.line, 0.8); ctx.lineWidth = lw * 0.8; ctx.stroke();
    }
  }
  // mantle draped over one shoulder (screen side o.mantleSide)
  if (cl.mantle && !cl.armor) {
    const ms = o.mantleSide || 1;
    const pts = [Xc(ms * 0.66, -0.2), X(ms * 1.7, 0.15), X(ms * 2.45, 0.8), X(ms * 2.5, 2.4), X(ms * 2.2, 5.0), X(ms * 1.2, 6.2),
      X(-ms * 0.4, 6.0), X(-ms * 1.2, 5.2), X(-ms * 1.9, 4.6), X(-ms * 1.0, 3.6), X(ms * 0.2, 2.2), Xc(ms * 0.55, 0.45)];
    ctx.beginPath(); L.crPath(ctx, pts, true, 0.45);
    ctx.fillStyle = lit(cl.mantle, Lt); ctx.fill();
    ctx.save(); ctx.clip();
    const gm = ctx.createLinearGradient(X(0, 0)[0] + side * s * 0.6, 0, X(0, 0)[0] - side * s * 2.2, 0);
    gm.addColorStop(0, rgba(clothShadow(cl.mantle, Lt), 0)); gm.addColorStop(1, rgba(clothShadow(cl.mantle, Lt), 0.85));
    ctx.fillStyle = gm; ctx.fillRect(B[0] - 20 * s, B[1] - 4 * s, 40 * s, 30 * s);
    // fold lines
    for (let i = 0; i < 4; i++) {
      const a = X(ms * (0.9 + i * 0.35), 0.5 + i * 0.3), b = X(ms * (0.2 - i * 0.5), 3.4 + i * 0.6), m2 = X(ms * (0.9 - i * 0.1), 2.0 + i * 0.4);
      L.strokeSmooth(ctx, [a, m2, b], rgba(shade(cl.mantle, 0.45), 0.6), lw * 0.8);
    }
    ctx.restore();
    ctx.beginPath(); L.crPath(ctx, pts, true, 0.45); // the folds replaced the path: outline the mantle itself
    ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.stroke();
    if (cl.edge) {
      // a thin gold edge along the mantle, from the waist up to the shoulder
      const ep = [X(-ms * 1.85, 4.55), X(-ms * 0.9, 3.6), X(ms * 0.25, 2.2), Xc(ms * 0.58, 0.5), Xc(ms * 0.66, -0.12)];
      L.strokeSmooth(ctx, ep, lit(cl.edge, Lt), s * 0.055);
      L.strokeSmooth(ctx, ep.map((p) => [p[0] - s * 0.012, p[1]]), rgba(shade(lit(cl.edge, Lt), 1.25), 0.5), s * 0.015);
    }
  }
  // tunic folds
  for (let i = 0; i < 5; i++) {
    const x = -1.6 + i * 0.8;
    const a = X(x * 0.6, 1.2 + (i % 2) * 0.4), b = X(x, 4.5 + (i % 3) * 0.6);
    L.strokeSmooth(ctx, [a, b], rgba(shade(cl.tunic, 0.5), 0.4), lw * 0.7);
  }
  // belt
  if (o.belt !== false && len > 4.5) {
    const bp = [X(-1.95, 4.0), X(0, 4.2), X(1.95, 4.0)];
    L.strokeSmooth(ctx, bp, lit(cl.trim || '#3a2a20', Lt), s * 0.32);
  }
  ctx.restore();
  ctx.restore();
  // collar: a soft fabric edge around the neck hole (the neck sits inside it)
  L.strokeSmooth(ctx, collar, rgba(clothShadow(cl.tunic, Lt), 0.55), lw * 2.4);
  L.strokeSmooth(ctx, collar, rgba(st.line, 0.85), lw * 0.85);
  // outline of the sides and shoulders only (never across the neck)
  ctx.lineJoin = 'round';
  ctx.beginPath(); L.crPath(ctx, left, false, 0.45);
  ctx.strokeStyle = st.line; ctx.lineWidth = lw * 1.1; ctx.stroke();
  ctx.beginPath(); L.crPath(ctx, right, false, 0.45); ctx.stroke();
  // rim light on the body: a fine line of light that fades in and out along the edge (never a
  // band of colour sitting on the shoulder)
  if (Lt.rim && (Lt.rimA || 0) > 0) {
    const pts = (Lt.rimSide > 0 ? right : left).slice(1, 6);
    const a = pts[0], b = pts[pts.length - 1];
    const g = ctx.createLinearGradient(a[0], a[1], b[0], b[1]);
    g.addColorStop(0, rgba(Lt.rim, 0)); g.addColorStop(0.3, rgba(Lt.rim, Lt.rimA * 0.45)); g.addColorStop(0.7, rgba(Lt.rim, Lt.rimA * 0.45)); g.addColorStop(1, rgba(Lt.rim, 0));
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    L.strokeSmooth(ctx, pts, g, s * 0.03);
    ctx.restore();
  }
  const poly = outline.concat([left[0]]);
  return { X, Xc, right, left, poly, collar };
}
// shoulder joints sit inside the body (no curved-front offset), so the far arm tucks behind the chest
function shoulderJoints(B, s, by, sh) {
  const c = Math.cos(by), sn = Math.sin(by);
  const J = (x, y) => [B[0] + (x * c + 0.25 * sn) * s, B[1] + y * s];
  return { L: J(-1.52, 0.98 - sh), R: J(1.52, 0.98 - sh) };
}

// ---------------------------------------------------------------- arms
function ik(S, W, l1, l2, bend) {
  let dx = W[0] - S[0], dy = W[1] - S[1];
  let d = Math.hypot(dx, dy);
  const maxd = (l1 + l2) * 0.999;
  if (d > maxd) { W = [S[0] + dx / d * maxd, S[1] + dy / d * maxd]; dx = W[0] - S[0]; dy = W[1] - S[1]; d = maxd; }
  const a = Math.atan2(dy, dx);
  const cosA = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1);
  const A = Math.acos(cosA) * bend;
  const E = [S[0] + Math.cos(a + A) * l1, S[1] + Math.sin(a + A) * l1];
  return { E, W };
}

function armJoint(S, W, l1, l2, side, out = 0) {
  // Two solutions blended smoothly: a "hanging elbow" (forearm foreshortens toward the
  // camera) for hands held near the body, and plain IK for reaching/raised arms.
  // The blend weight is continuous, so breathing or small target changes never make
  // the elbow jump between solutions.
  const dx = W[0] - S[0], dy = W[1] - S[1];
  const d = Math.hypot(dx, dy) || 1;
  const sol = ik(S, W, l1, l2, side);
  const dir = [dx / d, dy / d];
  let ux = lerp(0, dir[0], 0.42) + side * (0.04 + out), uy = lerp(1, dir[1], 0.42);
  const ul = Math.hypot(ux, uy); ux /= ul; uy /= ul;
  let E = [S[0] + ux * l1 * 0.92, S[1] + uy * l1 * 0.92];
  const fd = Math.hypot(sol.W[0] - E[0], sol.W[1] - E[1]);
  if (fd > l2) {
    const k = (fd - l2) / fd;
    E = [E[0] + (sol.W[0] - E[0]) * k, E[1] + (sol.W[1] - E[1]) * k];
  }
  const wReach = smooth((d - (l1 + l2 * 0.4)) / (l2 * 0.35));
  const wRaise = smooth((-dy / l1 - 0.05) / 0.3);
  const w = Math.max(wReach, wRaise);
  return { E: [lerp(E[0], sol.E[0], w), lerp(E[1], sol.E[1], w)], W: sol.W };
}

// sleeve geometry: shoulder cap + upper arm + elbow + forearm, as one union of round shapes
function armGeom(S, Wt, s, o = {}) {
  const l1 = 2.85 * s, l2 = 2.5 * s;
  const { E, W } = armJoint(S, Wt, l1, l2, o.bend == null ? 1 : o.bend, o.out || 0);
  const u = [W[0] - E[0], W[1] - E[1]], ul = Math.hypot(u[0], u[1]) || 1;
  const dir = [u[0] / ul, u[1] / ul];
  const loose = o.loose || 0;
  const rS = 0.5 * s, rE = 0.42 * s, rC = (0.37 + 0.16 * loose) * s;
  // the cuff stops just short of the wrist
  const C = [W[0] - dir[0] * s * 0.16, W[1] - dir[1] * s * 0.16];
  return { S, E, W, C, dir, rS, rE, rC, cap: 0.56 * s, s, ang: Math.atan2(dir[1], dir[0]), loose };
}
// A limb segment from A to B whose radius follows prof (radii spaced evenly along it), wound like
// hands.capsule so several segments union cleanly under nonzero fill.
function limbPath(p, A, B, prof) {
  const dx = B[0] - A[0], dy = B[1] - A[1], d = Math.hypot(dx, dy);
  const rA = prof[0], rB = prof[prof.length - 1];
  if (d < 1e-3) { const r = Math.max(rA, rB); p.moveTo(A[0] + r, A[1]); p.arc(A[0], A[1], r, 0, L.TAU, false); return; }
  const nx = -dy / d, ny = dx / d, al = Math.atan2(dy, dx), n = 14;
  const r = (t) => {
    const f = t * (prof.length - 1), i = Math.min(prof.length - 2, Math.floor(f)), k = f - i;
    return lerp(prof[i], prof[i + 1], k * k * (3 - 2 * k));
  };
  p.moveTo(A[0] + nx * rA, A[1] + ny * rA);
  p.arc(A[0], A[1], rA, al + Math.PI / 2, al + Math.PI * 1.5, false);
  for (let i = 1; i <= n; i++) { const t = i / n, rr = r(t); p.lineTo(A[0] + dx * t - nx * rr, A[1] + dy * t - ny * rr); }
  p.arc(B[0], B[1], rB, al + Math.PI * 1.5, al + Math.PI * 2.5, false);
  for (let i = n - 1; i >= 0; i--) { const t = i / n, rr = r(t); p.lineTo(A[0] + dx * t + nx * rr, A[1] + dy * t + ny * rr); }
  p.closePath();
}
// the upper arm swells at the deltoid and narrows to the elbow; the forearm swells just below the
// elbow and tapers to the wrist (a loose sleeve flares toward the cuff instead)
function upperProf(g) { return [g.rS, g.rS * 1.07, lerp(g.rS, g.rE, 0.55), g.rE * 0.97, g.rE]; }
function foreProf(g) {
  return g.rC > g.rE ? [g.rE, lerp(g.rE, g.rC, 0.35), lerp(g.rE, g.rC, 0.75), g.rC]
    : [g.rE, g.rE * 1.05, lerp(g.rE, g.rC, 0.55), g.rC * 1.02, g.rC];
}
function sleevePath(g, part) {
  const p = new (require('@napi-rs/canvas').Path2D)();
  if (part !== 'lower') {
    p.moveTo(g.S[0] + g.cap, g.S[1]); p.arc(g.S[0], g.S[1], g.cap, 0, L.TAU, false);
    limbPath(p, g.S, g.E, upperProf(g));
  }
  if (part !== 'upper') {
    limbPath(p, g.E, g.C, foreProf(g));
    if (part === 'lower') { p.moveTo(g.E[0] + g.rE, g.E[1]); p.arc(g.E[0], g.E[1], g.rE, 0, L.TAU, false); }
  }
  return p;
}
// o: { part: 'all'|'upper'|'lower', torso: polygon (screen) for blending the shoulder, far: bool, sleeve }
function drawSleeve(ctx, g, st, Lt, o = {}) {
  const s = g.s;
  const col = o.sleeve || st.cloth.tunic;
  const lw = (Lt.lineW || 1) * s * 0.02;
  const part = o.part || 'all';
  const path = sleevePath(g, part);
  const PathC = require('@napi-rs/canvas').Path2D;
  // outline (stroked under the fill). Around the shoulder only where the arm leaves the body,
  // so the sleeve grows out of the shoulder instead of sitting on it like a pad.
  ctx.save();
  ctx.lineJoin = 'round'; ctx.strokeStyle = st.line; ctx.lineWidth = lw * 2.1;
  const zone = new PathC(); zone.rect(-1e5, -1e5, 2e5, 2e5);
  zone.moveTo(g.S[0] + g.cap * 1.25, g.S[1]); zone.arc(g.S[0], g.S[1], g.cap * 1.25, 0, L.TAU, true);
  if (part === 'lower') {
    // a forearm drawn on its own never outlines its elbow end over its own upper arm (no seam)
    const notUpper = new PathC(); notUpper.rect(-1e5, -1e5, 2e5, 2e5);
    limbPath(notUpper, g.S, g.E, upperProf(g).map((r) => r * 0.98));
    ctx.save(); ctx.clip(zone, 'evenodd'); ctx.clip(notUpper, 'evenodd'); ctx.stroke(path); ctx.restore();
  } else { ctx.save(); ctx.clip(zone, 'evenodd'); ctx.stroke(path); ctx.restore(); }
  if (o.torso && part !== 'lower') {
    const inZone = new PathC(); inZone.moveTo(g.S[0] + g.cap * 1.25, g.S[1]); inZone.arc(g.S[0], g.S[1], g.cap * 1.25, 0, L.TAU, false);
    const outTorso = new PathC(); outTorso.rect(-1e5, -1e5, 2e5, 2e5);
    L.crPath(outTorso, o.torso, true, 0.45);
    ctx.save(); ctx.clip(inZone); ctx.clip(outTorso, 'evenodd'); ctx.stroke(path); ctx.restore();
  } else if (part === 'lower' || !o.torso) {
    ctx.save();
    const inZone = new PathC(); inZone.moveTo(g.S[0] + g.cap * 1.25, g.S[1]); inZone.arc(g.S[0], g.S[1], g.cap * 1.25, 0, L.TAU, false);
    ctx.clip(inZone); if (part === 'lower') ctx.stroke(path); ctx.restore();
  }
  ctx.restore();
  // an arm lying across the body casts a soft shadow onto the tunic beside it (away from the light),
  // so a sleeve of the tunic's own cloth still reads as an arm in front of the chest
  if (o.torso) {
    const side0 = Lt.side || -1;
    const off = [-side0 * s * 0.13, s * 0.17];
    const pts = part === 'lower' ? [g.E, g.C] : part === 'upper' ? [g.S, g.E] : [g.S, g.E, g.C];
    const shp = pts.map((q) => [q[0] + off[0], q[1] + off[1]]);
    const outT = new PathC(); L.crPath(outT, o.torso, true, 0.45);
    ctx.save(); ctx.clip(outT);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const [w, a] of [[1.5, 0.08], [1.25, 0.1], [1.02, 0.12]]) {
      ctx.strokeStyle = rgba('#05040a', a); ctx.lineWidth = (g.rE + g.rC) * w;
      ctx.beginPath(); shp.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.stroke();
    }
    ctx.restore();
  }
  // fill: the same lit cloth colour on both arms; the far arm only sits a little deeper in shadow
  ctx.fillStyle = lit(col, Lt);
  ctx.fill(path, 'nonzero');
  ctx.save();
  ctx.clip(path, 'nonzero');
  const side = Lt.side || -1;
  const shadowC = clothShadow(col, Lt);
  if (o.far) { ctx.fillStyle = rgba(shadowC, 0.35); ctx.fillRect(g.S[0] - 8 * s, g.S[1] - 4 * s, 16 * s, 14 * s); }
  // form shadow on the side of each segment that faces away from the light
  // each segment's shading stops at the elbow plane, so no round end of it shows as a ball joint
  const halfPlane = (P0, u, keepAhead) => {
    const q = new PathC(), k = keepAhead ? 1 : -1, n = [-u[1], u[0]], R = 60 * s;
    q.moveTo(P0[0] + n[0] * R, P0[1] + n[1] * R);
    q.lineTo(P0[0] + n[0] * R + u[0] * R * k, P0[1] + n[1] * R + u[1] * R * k);
    q.lineTo(P0[0] - n[0] * R + u[0] * R * k, P0[1] - n[1] * R + u[1] * R * k);
    q.lineTo(P0[0] - n[0] * R, P0[1] - n[1] * R);
    q.closePath();
    return q;
  };
  const band = (A, B2, r, prof, clipQ) => {
    if (clipQ) { ctx.save(); ctx.clip(clipQ); }
    let nx = -(B2[1] - A[1]), ny = B2[0] - A[0];
    const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
    if (nx * -side < 0) { nx = -nx; ny = -ny; } // n points toward the light
    const m = [(A[0] + B2[0]) / 2, (A[1] + B2[1]) / 2];
    const gr = ctx.createLinearGradient(m[0] + nx * r * 0.2, m[1] + ny * r * 0.2, m[0] - nx * r * 1.05, m[1] - ny * r * 1.05);
    gr.addColorStop(0, rgba(shadowC, 0)); gr.addColorStop(1, rgba(shadowC, 0.72));
    ctx.fillStyle = gr;
    const q = new PathC(); limbPath(q, A, B2, prof.map((x) => x * 1.03));
    ctx.fill(q);
    if (clipQ) ctx.restore();
  };
  const u1 = [g.E[0] - g.S[0], g.E[1] - g.S[1]], l1 = Math.hypot(u1[0], u1[1]) || 1;
  const u2 = [g.C[0] - g.E[0], g.C[1] - g.E[1]], l2 = Math.hypot(u2[0], u2[1]) || 1;
  // the shading of each segment narrows into the elbow, so neither a round end (a ball joint) nor a
  // straight cut shows there
  const taperEnd = (pr) => pr.map((r, i) => r * (i < pr.length - 2 ? 1 : i === pr.length - 2 ? 0.8 : 0.42));
  const taperStart = (pr) => pr.map((r, i) => r * (i === 0 ? 0.42 : i === 1 ? 0.8 : 1));
  if (part !== 'lower') band(g.S, g.E, g.rS, taperEnd(upperProf(g)), null);
  if (part !== 'upper') band(g.E, g.C, Math.max(g.rE, g.rC), taperStart(foreProf(g)), null);
  // occlusion where the upper arm meets the body
  if (part !== 'lower') {
    ctx.fillStyle = L.radial(ctx, g.S[0], g.S[1] + s * 0.7, 0, s * 1.0, [[0, rgba(shadowC, 0.35)], [1, rgba(shadowC, 0)]]);
    ctx.fillRect(g.S[0] - s * 1.2, g.S[1] - s * 0.4, s * 2.4, s * 2.4);
  }
  // cloth folds at the inner elbow
  if (part !== 'upper') {
    const a = [g.E[0] - g.dir[0] * s * 0.1, g.E[1] - g.dir[1] * s * 0.1];
    const nx = -g.dir[1], ny = g.dir[0];
    for (const k of [-0.25, 0.1]) {
      L.strokeSmooth(ctx, [[a[0] + nx * g.rE * 0.8 + g.dir[0] * s * k, a[1] + ny * g.rE * 0.8 + g.dir[1] * s * k],
        [a[0] + g.dir[0] * s * (k + 0.18), a[1] + g.dir[1] * s * (k + 0.18)],
        [a[0] - nx * g.rE * 0.5 + g.dir[0] * s * (k + 0.05), a[1] - ny * g.rE * 0.5 + g.dir[1] * s * (k + 0.05)]], rgba(shade(col, 0.45), 0.5), lw * 0.8);
    }
  }
  // light catching the sleeve along its lit side: a soft band hugging the silhouette edge (the stroke
  // is centred on the edge and clipped to the sleeve), tapering out at both ends
  if (!o.far || o.torso) {
    const segs = [];
    if (part !== 'lower') segs.push([g.S, g.E, upperProf(g), 0.3]);
    if (part !== 'upper') segs.push([g.E, g.C, foreProf(g), 0.05]);
    for (const [A, B2, prof, t0] of segs) {
      const dx = B2[0] - A[0], dy = B2[1] - A[1], d = Math.hypot(dx, dy) || 1;
      let nx = -dy / d, ny = dx / d;
      if (nx * -side < 0 || (Math.abs(nx) < 0.2 && ny > 0)) { nx = -nx; ny = -ny; }
      const rr = (t) => { const f = t * (prof.length - 1), i = Math.min(prof.length - 2, Math.floor(f)), k = f - i; return lerp(prof[i], prof[i + 1], k * k * (3 - 2 * k)); };
      const pts = [];
      for (let i = 0; i <= 8; i++) { const t = t0 + (0.95 - t0) * i / 8, r = rr(t); pts.push([A[0] + dx * t + nx * r, A[1] + dy * t + ny * r]); }
      const gr = ctx.createLinearGradient(pts[0][0], pts[0][1], pts[8][0], pts[8][1]);
      const hc = mix(lit(col, Lt), '#ffffff', 0.3);
      gr.addColorStop(0, rgba(hc, 0)); gr.addColorStop(0.25, rgba(hc, 0.3)); gr.addColorStop(0.75, rgba(hc, 0.3)); gr.addColorStop(1, rgba(hc, 0));
      L.strokeSmooth(ctx, pts, gr, s * 0.13);
    }
  }
  ctx.restore();
  // cuff: the opening of the sleeve around the wrist
  if (part !== 'upper') {
    const nx = -g.dir[1], ny = g.dir[0];
    ctx.strokeStyle = rgba(shade(shadowC, 0.8), 0.9); ctx.lineWidth = s * 0.08; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(g.C[0] + nx * g.rC * 0.9, g.C[1] + ny * g.rC * 0.9); ctx.quadraticCurveTo(g.C[0] + g.dir[0] * s * 0.08, g.C[1] + g.dir[1] * s * 0.08, g.C[0] - nx * g.rC * 0.9, g.C[1] - ny * g.rC * 0.9); ctx.stroke();
  }
}

// The end of a mantle worn over the far shoulder: it caps the shoulder and hangs over the top of the
// upper arm, its hem curving round the arm; below it the sleeve continues to the elbow.
function drawMantleDrape(ctx, g, st, Lt) {
  const s = g.s, col = st.cloth.mantle;
  const lw = (Lt.lineW || 1) * s * 0.02;
  const u = [g.E[0] - g.S[0], g.E[1] - g.S[1]], l = Math.hypot(u[0], u[1]) || 1;
  const d = [u[0] / l, u[1] / l], n = [-d[1], d[0]];
  const at = (t, w) => [g.S[0] + u[0] * t + n[0] * w, g.S[1] + u[1] * t + n[1] * w];
  const r = g.rS * 1.12, hem = 0.42;
  const pts = [at(-0.05, -r * 1.05), at(-0.12, 0), at(-0.05, r * 1.05), at(hem * 0.6, r * 1.12), at(hem + 0.04, r * 1.05),
    at(hem + 0.1, r * 0.2), at(hem + 0.02, -r * 0.7), at(hem * 0.6, -r * 1.1)];
  ctx.save();
  ctx.beginPath(); L.crPath(ctx, pts, true, 0.45);
  ctx.fillStyle = lit(col, Lt); ctx.fill();
  ctx.save(); ctx.clip();
  const sh = clothShadow(col, Lt);
  const gr = ctx.createLinearGradient(...at(0, 0), ...at(hem + 0.1, 0));
  gr.addColorStop(0, rgba(sh, 0.15)); gr.addColorStop(1, rgba(sh, 0.6)); ctx.fillStyle = gr; ctx.fillRect(g.S[0] - 4 * s, g.S[1] - 4 * s, 8 * s, 8 * s);
  for (const k of [-0.5, 0.15, 0.6]) L.strokeSmooth(ctx, [at(0.05, k * r), at(hem * 0.55, k * r * 1.05), at(hem + 0.02, k * r * 0.9)], rgba(shade(col, 0.45), 0.5), lw * 0.8);
  ctx.restore();
  // outline only round the hem and the outer edge (it merges with the mantle on the body above)
  ctx.strokeStyle = st.line; ctx.lineWidth = lw;
  ctx.beginPath(); L.crPath(ctx, pts.slice(2), false, 0.45); ctx.stroke();
  ctx.restore();
}
// compatibility wrapper: a whole arm with its hand (used by simple callers)
function drawArm(ctx, S, W, s, st, Lt, o) {
  const g = armGeom(S, W, s, o);
  const H = require('./hands');
  H.drawWrist(ctx, g.W, g.dir, s, st, Lt);
  drawSleeve(ctx, g, st, Lt, o);
  if (o.handSpec) H.drawHand3D(ctx, g.W, s, st, Lt, o.handSpec);
  if (o.shackle) drawShackle(ctx, g.W, g.ang, s, Lt);
  return { E: g.E, W: g.W, ang: g.ang, g };
}

// hand without an arm (legacy name kept for callers): forearm direction ang, mirror picks the hand
function drawHand(ctx, W, ang, s, st, Lt, pose, mirror = 1) {
  const H = require('./hands');
  const f = [Math.cos(ang), -Math.sin(ang), 0];
  return H.drawHand3D(ctx, W, s, st, Lt, { f, n: [0, 0, 1], right: mirror > 0, shape: H.preset(pose) });
}
function drawShackle(ctx, W, ang, s, Lt) {
  const c = lit('#5d5a58', Lt);
  ctx.save();
  ctx.translate(W[0], W[1]); ctx.rotate(ang);
  ctx.fillStyle = c; ctx.strokeStyle = '#1a1614'; ctx.lineWidth = s * 0.04;
  ctx.beginPath(); ctx.ellipse(-s * 0.2, 0, s * 0.2, s * 0.5, 0, 0, L.TAU); ctx.fill(); ctx.stroke();
  ctx.fillStyle = rgba('#ffffff', 0.25);
  ctx.beginPath(); ctx.ellipse(-s * 0.25, -s * 0.26, s * 0.06, s * 0.14, 0, 0, L.TAU); ctx.fill();
  ctx.restore();
}

// ---------------------------------------------------------------- props
// round country loaf: domed crust, three baked score cuts (clipped to the loaf), flour dust
function loafPath(ctx, r) {
  ctx.beginPath();
  ctx.moveTo(-r, r * 0.12);
  ctx.bezierCurveTo(-r * 1.02, -r * 0.42, -r * 0.55, -r * 0.72, 0, -r * 0.72);
  ctx.bezierCurveTo(r * 0.55, -r * 0.72, r * 1.02, -r * 0.42, r, r * 0.12);
  ctx.bezierCurveTo(r * 0.92, r * 0.42, -r * 0.92, r * 0.42, -r, r * 0.12);
  ctx.closePath();
}
function drawBread(ctx, x, y, r, Lt, o = {}) {
  const amb = Lt.amb || '#fff';
  const crustTop = L.mul('#c98a3e', Lt.key || '#fff'), crust = L.mul('#a8642a', Lt.key || '#fff'), crustD = L.mul('#6e3a16', amb);
  ctx.save();
  ctx.translate(x, y); ctx.rotate(o.rot || 0);
  // contact shadow
  ctx.fillStyle = rgba('#000000', 0.25);
  L.ellipse(ctx, 0, r * 0.36, r * 0.95, r * 0.12); ctx.fill();
  loafPath(ctx, r);
  ctx.fillStyle = L.linear(ctx, 0, -r * 0.75, 0, r * 0.4, [[0, crustTop], [0.55, crust], [1, crustD]]);
  ctx.fill();
  ctx.save();
  loafPath(ctx, r);
  ctx.clip();
  // soft dome highlight
  ctx.fillStyle = L.radial(ctx, -r * 0.3, -r * 0.45, r * 0.05, r * 0.9, [[0, rgba('#ffe2a8', 0.55)], [1, rgba('#ffe2a8', 0)]]);
  ctx.fillRect(-r * 1.2, -r, r * 2.4, r * 1.6);
  // baked score cuts: torn-open slashes showing paler crumb, with darker scorched lips
  for (const [cx, cy, ang, len] of [[-0.42, -0.22, -0.55, 0.62], [0.0, -0.32, -0.55, 0.7], [0.42, -0.22, -0.55, 0.62]]) {
    ctx.save();
    ctx.translate(cx * r, cy * r);
    ctx.rotate(ang);
    const L2 = len * r, W2 = r * 0.075;
    ctx.fillStyle = L.mul('#f0d39a', Lt.key || '#fff');
    ctx.beginPath(); ctx.ellipse(0, 0, L2 / 2, W2, 0, 0, L.TAU); ctx.fill();
    ctx.strokeStyle = rgba(L.mul('#7a4018', amb), 0.85);
    ctx.lineWidth = r * 0.035;
    ctx.beginPath(); ctx.ellipse(0, -W2 * 0.35, L2 / 2, W2 * 0.9, 0, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke();
    ctx.restore();
  }
  // flour dusting
  for (let i = 0; i < 26; i++) {
    const px = (L.hash01(i * 7 + 3) - 0.5) * 1.6 * r, py = -r * 0.62 + L.hash01(i * 13 + 1) * r * 0.55;
    ctx.fillStyle = rgba('#fff6e6', 0.28 + 0.25 * L.hash01(i * 5));
    ctx.beginPath(); ctx.arc(px, py, r * (0.012 + 0.018 * L.hash01(i * 11)), 0, L.TAU); ctx.fill();
  }
  ctx.restore();
  loafPath(ctx, r);
  ctx.strokeStyle = '#3a1e0c'; ctx.lineWidth = r * 0.035; ctx.stroke();
  ctx.restore();
}
// half of a torn loaf: crust shell with a score cut, and a soft, holey crumb face where it tore
function drawHalfBread(ctx, x, y, r, Lt, o = {}) {
  const f = o.face || 1;
  const amb = Lt.amb || '#fff';
  const crustTop = L.mul('#c98a3e', Lt.key || '#fff'), crust = L.mul('#a8642a', Lt.key || '#fff'), crustD = L.mul('#6e3a16', amb);
  const crumb = L.mul('#f2dfb6', Lt.key || '#fff'), crumbD = L.mul('#d2b47e', amb);
  ctx.save();
  ctx.translate(x, y); ctx.rotate(o.rot || 0); ctx.scale(f, 1);
  // irregular torn edge along x ~ 0
  const tear = [];
  for (let i = 0; i <= 9; i++) {
    const t = i / 9;
    tear.push([r * (0.06 + 0.07 * Math.sin(i * 2.1 + 0.5) + 0.04 * L.hash(i * 17)), -r * 0.68 + t * r * 1.04]);
  }
  // crust shell (left half of a dome)
  const shell = () => {
    ctx.beginPath();
    ctx.moveTo(tear[0][0], tear[0][1]);
    ctx.bezierCurveTo(-r * 0.55, -r * 0.74, -r * 1.02, -r * 0.42, -r, r * 0.12);
    ctx.bezierCurveTo(-r * 0.92, r * 0.4, -r * 0.3, r * 0.42, tear[tear.length - 1][0], tear[tear.length - 1][1]);
    for (let i = tear.length - 1; i >= 0; i--) ctx.lineTo(tear[i][0], tear[i][1]);
    ctx.closePath();
  };
  shell();
  ctx.fillStyle = L.linear(ctx, 0, -r * 0.75, 0, r * 0.4, [[0, crustTop], [0.55, crust], [1, crustD]]);
  ctx.fill();
  ctx.save();
  shell(); ctx.clip();
  ctx.fillStyle = L.radial(ctx, -r * 0.45, -r * 0.45, r * 0.05, r * 0.8, [[0, rgba('#ffe2a8', 0.5)], [1, rgba('#ffe2a8', 0)]]);
  ctx.fillRect(-r * 1.2, -r, r * 1.4, r * 1.6);
  // one score cut on the crust
  ctx.translate(-r * 0.45, -r * 0.3); ctx.rotate(-0.55);
  ctx.fillStyle = L.mul('#f0d39a', Lt.key || '#fff');
  ctx.beginPath(); ctx.ellipse(0, 0, r * 0.3, r * 0.07, 0, 0, L.TAU); ctx.fill();
  ctx.strokeStyle = rgba(L.mul('#7a4018', amb), 0.85); ctx.lineWidth = r * 0.035;
  ctx.beginPath(); ctx.ellipse(0, -r * 0.025, r * 0.3, r * 0.065, 0, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke();
  ctx.restore();
  shell();
  ctx.strokeStyle = '#3a1e0c'; ctx.lineWidth = r * 0.035; ctx.stroke();
  // crumb face, seen slightly from the side: a soft lens bulging out of the tear
  const face = () => {
    ctx.beginPath();
    ctx.moveTo(tear[0][0], tear[0][1]);
    ctx.bezierCurveTo(r * 0.42, -r * 0.5, r * 0.44, r * 0.18, tear[tear.length - 1][0], tear[tear.length - 1][1]);
    for (let i = tear.length - 1; i >= 0; i--) ctx.lineTo(tear[i][0], tear[i][1]);
    ctx.closePath();
  };
  face();
  ctx.fillStyle = L.linear(ctx, 0, -r * 0.6, r * 0.3, r * 0.3, [[0, crumb], [1, crumbD]]);
  ctx.fill();
  ctx.save();
  face(); ctx.clip();
  // airy crumb holes and torn fibres
  for (let i = 0; i < 16; i++) {
    const hx = r * (0.1 + 0.26 * L.hash01(i * 7 + 2)), hy = -r * 0.55 + r * 0.85 * L.hash01(i * 3 + 9);
    ctx.fillStyle = rgba(L.mul('#b8935a', amb), 0.55);
    ctx.beginPath(); ctx.ellipse(hx, hy, r * (0.018 + 0.03 * L.hash01(i * 5)), r * (0.012 + 0.02 * L.hash01(i * 9)), 0.4, 0, L.TAU); ctx.fill();
  }
  ctx.restore();
  face();
  ctx.strokeStyle = rgba('#7a5a30', 0.9); ctx.lineWidth = r * 0.03; ctx.stroke();
  // thin crust rim visible along the tear
  ctx.strokeStyle = crustD; ctx.lineWidth = r * 0.045;
  ctx.beginPath(); ctx.moveTo(tear[0][0], tear[0][1]); for (const p of tear) ctx.lineTo(p[0], p[1]); ctx.stroke();
  ctx.restore();
}
function drawJar(ctx, x, y, h, Lt) {
  const c = lit('#a4583a', Lt), d = L.mul('#6a321e', Lt.amb || '#fff');
  ctx.save(); ctx.translate(x, y);
  const pts = [[-0.18, -1], [-0.22, -0.82], [-0.45, -0.55], [-0.5, -0.1], [-0.36, 0.3], [-0.2, 0.42], [0.2, 0.42], [0.36, 0.3], [0.5, -0.1], [0.45, -0.55], [0.22, -0.82], [0.18, -1]].map(([a, b]) => [a * h, b * h]);
  ctx.beginPath(); L.crPath(ctx, pts, true, 0.4); ctx.fillStyle = c; ctx.fill();
  ctx.save(); ctx.clip(); ctx.fillStyle = d; ctx.fillRect(h * 0.1, -h * 1.2, h, h * 2); ctx.restore();
  ctx.strokeStyle = '#2a140c'; ctx.lineWidth = h * 0.025; ctx.stroke();
  ctx.strokeStyle = rgba('#e0b090', 0.5); ctx.lineWidth = h * 0.03;
  ctx.beginPath(); ctx.ellipse(0, -h * 0.35, h * 0.47, h * 0.06, 0, 0, Math.PI); ctx.stroke();
  ctx.fillStyle = '#2a140c'; L.ellipse(ctx, 0, -h, h * 0.18, h * 0.05); ctx.fill();
  ctx.restore();
}
function drawChain(ctx, a, b, s, Lt, sag = 1.0, links = 14) {
  const c = lit('#4e4a48', Lt);
  ctx.save();
  ctx.strokeStyle = c; ctx.lineWidth = s * 0.06;
  for (let i = 0; i < links; i++) {
    const t = (i + 0.5) / links;
    const x = lerp(a[0], b[0], t), y = lerp(a[1], b[1], t) + Math.sin(t * Math.PI) * sag * s;
    const t2 = (i + 1.5) / links;
    const x2 = lerp(a[0], b[0], t2), y2 = lerp(a[1], b[1], t2) + Math.sin(t2 * Math.PI) * sag * s;
    const ang = Math.atan2(y2 - y, x2 - x);
    ctx.beginPath();
    ctx.ellipse(x, y, s * 0.2, i % 2 ? s * 0.05 : s * 0.11, ang, 0, L.TAU);
    ctx.stroke();
  }
  ctx.restore();
}
function drawScroll(ctx, x, y, w, h, Lt, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0);
  const paper = lit('#e8d9b5', Lt);
  ctx.fillStyle = paper;
  ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.fillStyle = rgba(L.mul('#b49a6e', Lt.amb || '#fff'), 0.5);
  ctx.fillRect(-w / 2, -h / 2, w * 0.08, h);
  ctx.fillRect(w / 2 - w * 0.08, -h / 2, w * 0.08, h);
  // text lines
  ctx.strokeStyle = rgba('#3a2a1a', 0.55); ctx.lineWidth = h * 0.02;
  for (let i = 0; i < 9; i++) {
    const yy = -h * 0.38 + i * h * 0.09;
    ctx.beginPath();
    let xx = -w * 0.36;
    while (xx < w * 0.36) { const ww = w * (0.03 + 0.05 * L.hash01(i * 31 + Math.floor(xx))); ctx.moveTo(xx, yy); ctx.lineTo(Math.min(xx + ww, w * 0.36), yy); xx += ww + w * 0.025; }
    ctx.stroke();
  }
  // rollers
  for (const sx of [-1, 1]) {
    ctx.fillStyle = lit('#6a4428', Lt);
    ctx.fillRect(sx * w / 2 - w * 0.05, -h * 0.6, w * 0.1, h * 1.2);
    ctx.strokeStyle = '#2a1a10'; ctx.lineWidth = w * 0.01; ctx.strokeRect(sx * w / 2 - w * 0.05, -h * 0.6, w * 0.1, h * 1.2);
  }
  ctx.restore();
}
// an open scroll held up between two hands: GN, GF = the two grips (screen), one roller in each;
// the parchment between them is seen from the back (the writing faces the reader, its ink showing
// faintly through), sagging a little, with the rolled-up ends wound round each roller
function drawOpenScroll(ctx, GN, GF, s, o, Lt, fc) {
  const h = (o.h || 1.6) * s;
  const paper = lit('#e6d6b0', Lt), paperSh = mix(paper, L.mul('#8a7450', Lt.amb || '#fff'), 0.55);
  const hN = h, hF = h * 0.9;
  const top = (u) => [lerp(GN[0], GF[0], u), lerp(GN[1] - hN * 0.5, GF[1] - hF * 0.5, u) + Math.sin(u * Math.PI) * h * 0.05];
  const bot = (u) => [lerp(GN[0], GF[0], u), lerp(GN[1] + hN * 0.5, GF[1] + hF * 0.5, u) + Math.sin(u * Math.PI) * h * 0.08];
  ctx.save();
  ctx.beginPath();
  for (let i = 0; i <= 12; i++) { const p = top(i / 12); i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); }
  for (let i = 12; i >= 0; i--) { const p = bot(i / 12); ctx.lineTo(p[0], p[1]); }
  ctx.closePath();
  const t0 = top(0.5), b0 = bot(0.5);
  ctx.fillStyle = L.linear(ctx, 0, t0[1], 0, b0[1], [[0, mix(paper, '#fff6e0', 0.15)], [0.6, paper], [1, paperSh]]);
  ctx.fill();
  ctx.save(); ctx.clip();
  // the ink of the columns of writing, faint and mirrored from the other side
  ctx.strokeStyle = rgba('#3a2a1a', 0.13); ctx.lineWidth = h * 0.022;
  for (let c = 0; c < 2; c++) {
    for (let i = 0; i < 9; i++) {
      const v = 0.14 + i * 0.085;
      const u0 = 0.1 + c * 0.45, u1 = u0 + 0.34 - 0.08 * L.hash01(i * 13 + c * 7);
      const a = top(u0), b = bot(u0), a2 = top(u1), b2 = bot(u1);
      ctx.beginPath(); ctx.moveTo(lerp(a[0], b[0], v), lerp(a[1], b[1], v)); ctx.lineTo(lerp(a2[0], b2[0], v), lerp(a2[1], b2[1], v)); ctx.stroke();
    }
  }
  // the sheet curves: a soft shadow down its middle, light on the far half
  const m0 = top(0.5);
  ctx.fillStyle = L.linear(ctx, GN[0], 0, GF[0], 0, [[0, rgba(paperSh, 0.35)], [0.35, rgba(paperSh, 0)], [0.7, rgba('#fff4d8', 0.12)], [1, rgba(paperSh, 0.3)]]);
  ctx.fillRect(Math.min(GN[0], GF[0]) - s, m0[1] - h, Math.abs(GF[0] - GN[0]) + 2 * s, h * 3);
  ctx.restore();
  ctx.strokeStyle = rgba('#4a3420', 0.7); ctx.lineWidth = s * 0.025; ctx.stroke();
  // the rolled ends and the rollers through them
  for (const [G, hh, k] of [[GN, hN, 0], [GF, hF, 1]]) {
    const rw = s * 0.17, x = G[0] + (k ? 1 : -1) * rw * 0.2 * Math.sign(GF[0] - GN[0]);
    // the wooden roller, longer than the sheet, with turned knobs
    ctx.fillStyle = lit('#6a4428', Lt);
    ctx.beginPath(); ctx.roundRect(x - s * 0.05, G[1] - hh * 0.5 - s * 0.32, s * 0.1, hh + s * 0.64, s * 0.04); ctx.fill();
    for (const e of [-1, 1]) {
      ctx.beginPath(); ctx.ellipse(x, G[1] + e * (hh * 0.5 + s * 0.3), s * 0.085, s * 0.06, 0, 0, L.TAU); ctx.fill();
      ctx.strokeStyle = '#2a1a10'; ctx.lineWidth = s * 0.015; ctx.stroke();
    }
    // the roll of parchment wound round it
    ctx.fillStyle = L.linear(ctx, x - rw, 0, x + rw, 0, [[0, paperSh], [0.4, mix(paper, '#fff6e0', 0.2)], [1, paperSh]]);
    ctx.beginPath(); ctx.roundRect(x - rw, G[1] - hh * 0.5 - s * 0.02, rw * 2, hh + s * 0.04, rw * 0.5); ctx.fill();
    ctx.strokeStyle = rgba('#4a3420', 0.7); ctx.lineWidth = s * 0.022; ctx.stroke();
    ctx.strokeStyle = rgba('#4a3420', 0.25); ctx.lineWidth = s * 0.012;
    for (const f of [-0.45, 0.1, 0.55]) { ctx.beginPath(); ctx.moveTo(x + f * rw, G[1] - hh * 0.45); ctx.lineTo(x + f * rw, G[1] + hh * 0.45); ctx.stroke(); }
  }
  ctx.restore();
}
// a small clay oil lamp seen from the side: the round body, a filling hole, the spout to the right
// (the flame is drawn at its tip by the caller), a loop handle on the left
function drawLamp(ctx, x, y, s, Lt) {
  ctx.save();
  const clay = lit('#9a5a32', Lt), clayD = L.mul('#4a2614', Lt.amb || '#fff');
  ctx.fillStyle = L.linear(ctx, 0, y - s * 0.55, 0, y, [[0, mix(clay, '#ffd8a0', 0.25)], [1, clayD]]);
  ctx.beginPath();
  ctx.moveTo(x - s * 0.75, y - s * 0.12);
  ctx.bezierCurveTo(x - s * 0.8, y - s * 0.55, x + s * 0.25, y - s * 0.62, x + s * 0.45, y - s * 0.4);
  ctx.lineTo(x + s * 0.68, y - s * 0.62); ctx.quadraticCurveTo(x + s * 0.78, y - s * 0.62, x + s * 0.72, y - s * 0.5);
  ctx.lineTo(x + s * 0.45, y - s * 0.12); ctx.quadraticCurveTo(x, y + s * 0.02, x - s * 0.75, y - s * 0.12);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#2a140a'; ctx.lineWidth = s * 0.04; ctx.stroke();
  ctx.fillStyle = '#1a0c06';
  ctx.beginPath(); ctx.ellipse(x - s * 0.15, y - s * 0.47, s * 0.16, s * 0.05, 0, 0, L.TAU); ctx.fill();
  ctx.strokeStyle = clay; ctx.lineWidth = s * 0.09;
  ctx.beginPath(); ctx.arc(x - s * 0.82, y - s * 0.3, s * 0.13, Math.PI * 0.5, Math.PI * 1.5); ctx.stroke();
  ctx.restore();
}
function drawTorch(ctx, x, y, s, t, Lt, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  ctx.fillStyle = lit('#4a3020', Lt);
  ctx.beginPath(); ctx.moveTo(-s * 0.12, 0); ctx.lineTo(s * 0.12, 0); ctx.lineTo(s * 0.08, s * 2.2); ctx.lineTo(-s * 0.08, s * 2.2); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#2a1a10'; ctx.fillRect(-s * 0.2, -s * 0.15, s * 0.4, s * 0.35);
  drawFlame(ctx, 0, -s * 0.1, s * (o.size || 1), t, o.seed || 0);
  ctx.restore();
}
function drawFlame(ctx, x, y, s, t, seed = 0) {
  ctx.save();
  ctx.translate(x, y);
  const n1 = L.fbm1(t * 3.1 + seed, seed + 3), n2 = L.fbm1(t * 4.3 + seed * 2, seed + 7);
  ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 0, -s * 0.5, s * 3.2, '#ff8a2a', 0.35 + 0.08 * n1);
  const layers = [['#ff5a10', 1.0], ['#ffa030', 0.75], ['#fff0b0', 0.42]];
  for (const [c, k] of layers) {
    const h = s * (1.5 + 0.35 * n1) * k, w = s * 0.42 * k * (1 + 0.1 * n2);
    ctx.fillStyle = rgba(c, 0.85);
    ctx.beginPath();
    ctx.moveTo(-w, 0);
    ctx.quadraticCurveTo(-w * 1.1, -h * 0.45, n2 * s * 0.15, -h);
    ctx.quadraticCurveTo(w * 1.1, -h * 0.45, w, 0);
    ctx.quadraticCurveTo(0, w * 0.6, -w, 0);
    ctx.fill();
  }
  ctx.restore();
}
function drawCup(ctx, x, y, h, Lt) {
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = lit('#9a6a3a', Lt);
  ctx.beginPath(); ctx.moveTo(-h * 0.45, -h); ctx.quadraticCurveTo(-h * 0.4, -h * 0.2, -h * 0.1, -h * 0.1); ctx.lineTo(-h * 0.08, h * 0.3); ctx.lineTo(-h * 0.3, h * 0.42); ctx.lineTo(h * 0.3, h * 0.42); ctx.lineTo(h * 0.08, h * 0.3); ctx.lineTo(h * 0.1, -h * 0.1); ctx.quadraticCurveTo(h * 0.4, -h * 0.2, h * 0.45, -h); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#2a1a10'; ctx.lineWidth = h * 0.03; ctx.stroke();
  ctx.fillStyle = '#4a1a24'; L.ellipse(ctx, 0, -h, h * 0.45, h * 0.1); ctx.fill(); ctx.stroke();
  ctx.restore();
}

module.exports = {
  drawOpenScroll, drawLamp, drawMantleDrape, limbPath, armJoint, armGeom, drawSleeve, drawTorso, drawArm, drawHand, drawBread, drawHalfBread, drawJar, drawChain, drawScroll, drawTorch, drawFlame, drawCup, drawShackle, ik, torsoPts, collarPts, neckBase, shoulderJoints, clothShadow };
