// face.mjs - pseudo-3D anime head rig (Keeper, Mira, Grandpa).
//
// Exports:
//   drawHead(g, style, p)   draw a head. style = STYLES.keeper | STYLES.mira | STYLES.grandpa.
//     p (all optional): x, y (between the eyes, px), s (1 -> crown-to-chin ~330px), yaw (-1..1, + turns to
//     screen-right), pitch (-1..1, + looks up), roll (rad); light (LIGHT.*), lightDir (-1 key from left..+1 right),
//     rim (0..1), lightK (0..1, default .6); eyeOpen (0..1.35), eyeOpenL/eyeOpenR (L = screen-left eye), lowerLid,
//     blink, gazeX, gazeY (+ = up), pupil, tears, tearDrop (0..1 progress), tearSide (-1|1 screen side);
//     browInner, browOuter, browRaise, browL, browR, browKnit; smile, mouthOpen, mouthWide, mouthRound,
//     mouthPress, mouthAsym (+ raises screen-right corner), lipTremble (needs t), teeth;
//     blush, wet, sweat, dirt, sand; glow, glowColor, seams (Keeper); t, wind, windDir, wetHair;
//     hood (Mira 0..1), cap (Grandpa, default true).
//   STYLES                  {keeper, mira, grandpa} style objects (proportion tables, colors, hair/extras drawers).
//   EXPR                    expression presets (neutral, worried, sad, hopeful, smile, laugh, surprised, determined,
//                           tender, tired, awe, relief, cryingSmile, sleep, wry, fond, focused, scared, shout,
//                           reading, wonder, pained, moved).
//   expr(name, overrides?)  -> fresh params object.
//   blend(a, b, k)          numeric lerp of two param objects (non-numbers taken from b when k>=.5).
//   blinkAt(t, seed, rate=1) -> 0..1 lid closure from natural blinking.
//   saccade(t, seed, amp=1) -> {x, y} small gaze offset.
//   lipsync(p, m)           apply ctx.mouth() result {open, wide, round, press} onto p (returns new object).
import { PAL, LIGHT, clamp, lerp, TAU, hash, noise1, rng, mix, rgba, lit, shade, splinePath, polyPath,
  taperStroke, glow } from './core.mjs';

// ------------------------------------------------------------------ math helpers
const interp = (ys, vs, y) => {
  if (y <= ys[0]) return vs[0]; const n = ys.length; if (y >= ys[n - 1]) return vs[n - 1];
  let i = 0; while (y > ys[i + 1]) i++;
  const u = (y - ys[i]) / (ys[i + 1] - ys[i]); const s = u * u * (3 - 2 * u);
  return lerp(vs[i], vs[i + 1], lerp(u, s, 0.5));
};
function hull(pts) {
  const p = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const q of p) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  for (let i = p.length - 1; i >= 0; i--) { const q = p[i];
    while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}
const fillPoly = (g, pts, color) => { g.beginPath(); polyPath(g, pts); g.fillStyle = color; g.fill(); };

// ------------------------------------------------------------------ the rig
function makeRig(st, p) {
  const k = (p.s ?? 1) * 165, X = p.x ?? 360, Y = p.y ?? 640;
  const a = (p.yaw ?? 0) * 1.0, b = (p.pitch ?? 0) * 0.45, r = p.roll ?? 0;
  const ca = Math.cos(a), sa = Math.sin(a), cb = Math.cos(b), sb = Math.sin(b), cr = Math.cos(r), sr = Math.sin(r);
  const pr = st.prof;
  const W = y => interp(pr.y, pr.w, y), DF = y => interp(pr.y, pr.df, y), DB = y => interp(pr.y, pr.db, y);
  const rot = (x, y, z) => { // yaw then pitch
    const x1 = x * ca + z * sa, z1 = -x * sa + z * ca;
    const y2 = y * cb - z1 * sb, z2 = y * sb + z1 * cb; return [x1, y2, z2];
  };
  const scr = (v) => [X + k * (v[0] * cr - v[1] * sr), Y + k * (v[0] * sr + v[1] * cr)];
  const P = (x, y, z) => scr(rot(x, y, z));
  const surfZ = (x, y) => { const w = W(y), d = DF(y); const u = clamp(Math.abs(x) / Math.max(w, 1e-3), 0, 1); return d * Math.sqrt(1 - u * u); };
  const S = (x, y, dz = 0) => P(x, y, surfZ(x, y) + dz);
  const normal = (x, y, z) => { const w = Math.max(W(y), .05), d = z >= 0 ? Math.max(DF(y), .05) : Math.max(-DB(y), .05);
    let nx = x / (w * w), nz = z / (d * d), ny = y > 0.55 ? (y - 0.55) * 2.2 : (y < -0.5 ? (y + 0.5) * 2.2 : 0);
    const L = Math.hypot(nx, ny, nz) || 1; return [nx / L, ny / L, nz / L]; };
  const vis = (x, y) => rot(...normal(x, y, surfZ(x, y)))[2];
  // light vector (view space) and colors
  const ld = p.lightDir ?? -0.5, light = p.light ?? LIGHT.day, lk = p.lightK ?? 0.6;
  const Lv = (() => { const v = [ld * 1.1, -0.35, 0.7]; const n = Math.hypot(...v); return v.map(c => c / n); })();
  const C = (c) => lit(c, light.key, lk);
  const CS = (c) => mix(lit(c, light.key, lk * 0.5).replace(/^#/, '#'), light.shadow, 0.3);
  const ink = PAL.ink;
  // cloud of head-surface points (rows) for silhouette
  const cloud = (y0, y1, sc = 1, rows = 22, cols = 20, cy = -0.1, back = true) => {
    const out = [];
    for (let i = 0; i <= rows; i++) {
      const yy = lerp(y0, y1, i / rows), w = W(yy) * sc, df = DF(yy) * sc, db = DB(yy) * sc;
      const ys = cy + (yy - cy) * sc;
      for (let j = 0; j < cols; j++) { const th = j / cols * TAU, s = Math.sin(th);
        if (!back && s < -0.2) continue;
        out.push(P(w * Math.cos(th), ys, s >= 0 ? s * df : s * -db)); }
    }
    return out;
  };
  const H = { k, X, Y, p, st, rot, scr, P, S, W, DF, DB, surfZ, normal, vis, Lv, ld, light, C, CS, ink, cloud,
    lw: Math.max(0.9, 0.0125 * k), t: p.t ?? 0, small: k < 0.25 * 165, cr, sr };
  H.shadeAt = (x, y, dz = 0) => { const n = rot(...normal(x, y, surfZ(x, y) + dz)); return n[0] * Lv[0] + n[1] * Lv[1] + n[2] * Lv[2]; };
  // screen-space helpers in head frame
  H.axisX = [cr, sr]; H.axisY = [-sr, cr];
  return H;
}

// cel shadow region of the head (terminator per row, extended to the far side)
function shadowPoly(H, y0 = -1.1, y1 = 1.05, thr = 0.12) {
  const { W, DF, rot, scr, normal, Lv, ld } = H; const side = ld >= 0 ? -1 : 1; // shadow side in view x
  const term = [];
  for (let i = 0; i <= 26; i++) {
    const y = lerp(y0, y1, i / 26), w = W(y), d = DF(y);
    const pts = [];
    for (let j = 0; j <= 30; j++) { const th = Math.PI * j / 30; const x = w * Math.cos(th), z = d * Math.sin(th);
      const v = rot(x, y, z); if (v[2] < -0.05) continue; const n = rot(...normal(x, y, z));
      pts.push({ v, l: n[0] * Lv[0] + n[1] * Lv[1] + n[2] * Lv[2] }); }
    if (!pts.length) continue;
    pts.sort((a, b) => (a.v[0] - b.v[0]) * side * -1); // from shadow side toward light
    let hit = pts.find(q => q.l > thr) || pts[pts.length - 1];
    term.push(hit.v);
  }
  const out = term.map(v => scr(v));
  const far = (v, dy) => scr([v[0] + side * 3, v[1] + dy, v[2]]);
  out.push(far(term[term.length - 1], 0.6)); out.unshift(far(term[0], -0.6));
  return out;
}

// ------------------------------------------------------------------ eyes
function eyeGeom(st, o, L, sleepy) {
  const ew = st.eye.w, eh = st.eye.h;
  const base = u => 0.01 - 0.028 * u * st.eye.tilt;
  const bump = u => Math.pow(Math.max(0, 1 - u * u), 0.62) * (1 + 0.12 * -u);
  const closedArc = u => eh * 0.22 * (1 - u * u) * (L > 0.45 ? -1 : 1);
  const top = u => base(u) + (o < 1 ? lerp(closedArc(u), -eh * bump(u), clamp(o)) : -eh * o * bump(u));
  const bot = u => Math.max(top(u), base(u) + eh * 0.6 * Math.pow(Math.max(0, 1 - u * u), 0.85) * (1 - L * 0.75));
  return { ew, eh, base, top, bot };
}
function drawEye(g, H, side) {
  const { p, st, k } = H; const E = st.eye;
  const ex = side * E.x, ey = E.y;
  if (H.vis(ex * 0.9, ey) < 0.05) return;
  const O = H.S(ex, ey, 0.01), e = 0.02;
  const a = H.S(ex + e, ey), b = H.S(ex - e, ey), c = H.S(ex, ey + e), d = H.S(ex, ey - e);
  const U = [(a[0] - b[0]) / (2 * e) * side, (a[1] - b[1]) / (2 * e) * side], V = [(c[0] - d[0]) / (2 * e), (c[1] - d[1]) / (2 * e)];
  const eo = (side < 0 ? p.eyeOpenL : p.eyeOpenR) ?? (p.eyeOpen ?? 1);
  const o = Math.max(0, eo * (1 - clamp(p.blink ?? 0))), L = clamp(p.lowerLid ?? 0);
  const G = eyeGeom(st, o, L); const { ew, eh, top, bot } = G;
  const N = 16, us = Array.from({ length: N + 1 }, (_, i) => -1 + 2 * i / N);
  g.save(); g.transform(U[0], U[1], V[0], V[1], O[0], O[1]);
  const lw = 1 / k; // local units per px
  const tears = clamp(p.tears ?? 0);
  const lashPts = us.map(u => [u * ew, top(u)]);
  lashPts.unshift([-ew * 1.04, top(-1) + eh * 0.04]);
  const flick = [[ew * 1.1, top(1) - eh * 0.08], [ew * 1.26, top(1) - eh * 0.3 * st.eye.flick]];
  if (o > 0.06) {
    const sclera = (gg) => { gg.moveTo(-ew, top(-1)); us.forEach(u => gg.lineTo(u * ew, top(u)));
      for (let i = N; i >= 0; i--) gg.lineTo(us[i] * ew, bot(us[i])); gg.closePath(); };
    g.save(); g.beginPath(); sclera(g); g.fillStyle = H.C(tears > 0 ? mix('#fbf6ef', '#eaf4ff', tears * 0.6) : '#fbf6ef'); g.fill(); g.clip();
    // lid shadow on sclera
    g.beginPath(); g.moveTo(-ew * 1.2, -eh * 2); us.forEach(u => g.lineTo(u * ew, top(u) + eh * 0.28)); g.lineTo(ew * 1.2, -eh * 2); g.closePath();
    g.fillStyle = rgba(st.skinShadow, 0.45); g.fill();
    // iris
    const gx = clamp(p.gazeX ?? 0, -1.2, 1.2) * side, gy = clamp(p.gazeY ?? 0, -1, 1);
    const ir = E.iris, cx = gx * ew * 0.5 + E.irisX, cy = -gy * eh * 0.32 + eh * 0.05;
    const gr = g.createLinearGradient(0, cy - ir, 0, cy + ir);
    gr.addColorStop(0, shade(st.iris, -0.6)); gr.addColorStop(0.35, shade(st.iris, -0.25));
    gr.addColorStop(0.7, st.iris); gr.addColorStop(1, shade(st.iris, 0.3));
    g.beginPath(); g.ellipse(cx, cy, ir, ir * 1.06, 0, 0, TAU); g.fillStyle = gr; g.fill();
    g.lineWidth = 1.2 * lw; g.strokeStyle = shade(st.iris, -0.7); g.stroke();
    // keeper luminous ring
    const gl = st.glowRing ? clamp(p.glow ?? 0.35) : 0;
    const gc = p.glowColor ?? PAL.kIrisRing;
    if (st.glowRing) {
      g.beginPath(); g.ellipse(cx, cy, ir * 0.74, ir * 0.78, 0, 0, TAU);
      g.strokeStyle = rgba(gc, 0.35 + 0.65 * gl); g.lineWidth = Math.max(1 * lw, ir * 0.13); g.stroke();
    }
    g.beginPath(); g.ellipse(cx, cy, ir * 0.4 * (p.pupil ?? 1), ir * 0.44 * (p.pupil ?? 1), 0, 0, TAU);
    g.fillStyle = shade(st.iris, -0.8); g.fill();
    if (gl > 0.02) glow(g, cx, cy, ir * 1.8, gc, 0.55 * gl);
    // highlights
    const ls = clamp(H.ld * side, -1, 1);
    const hk = 1 + tears * 0.5;
    g.fillStyle = 'rgba(255,255,255,0.95)';
    g.beginPath(); g.ellipse(cx + ls * ir * 0.38, cy - ir * 0.42, ir * 0.24 * hk, ir * 0.2 * hk, -0.4, 0, TAU); g.fill();
    if (!H.small) { g.beginPath(); g.ellipse(cx - ls * ir * 0.35, cy + ir * 0.42, ir * 0.1 * hk, ir * 0.08 * hk, 0, 0, TAU); g.fill(); }
    if (tears > 0) { // glassy pooled water line
      g.beginPath(); us.slice(2, N - 1).forEach((u, i) => (i ? g.lineTo : g.moveTo).call(g, u * ew, bot(u) - eh * 0.1));
      g.strokeStyle = `rgba(235,248,255,${(0.75 * tears).toFixed(3)})`; g.lineWidth = eh * 0.16; g.stroke();
      g.fillStyle = `rgba(255,255,255,${(0.8 * tears).toFixed(3)})`;
      g.beginPath(); g.ellipse(cx - ls * ir * 0.1, cy + ir * 0.62, ir * 0.35, ir * 0.06, 0, 0, TAU); g.fill();
    }
    g.restore();
    // crease (double eyelid) and lower lid
    if (!H.small && o > 0.3) {
      const cp = us.slice(3, N - 1).map(u => [u * ew * 1.02, top(u) - eh * 0.42 - eh * 0.05 * (1 - u * u)]);
      taperStroke(g, cp, 0.6 * lw, 0.4 * lw, rgba(PAL.inkSoft, 0.7), 1.6 * lw);
    }
    if (!H.small) {
      const lp = us.slice(Math.floor(N * 0.3)).map(u => [u * ew * 1.02, bot(u) + 0.004]);
      taperStroke(g, lp, 0.3 * lw, 1.6 * lw, rgba(PAL.inkSoft, 0.9), 1.4 * lw);
    }
  }
  // upper lash line (thick) with outer flick
  const lashW = E.lash * Math.max(1, Math.min(1.8, 0.55 / Math.max(.3, k / 165)));
  taperStroke(g, lashPts.concat(flick), 1.2 * lw, 0.6 * lw, H.ink, Math.max(2.2 * lw, lashW));
  if (st.eye.lashes && o > 0.2 && !H.small) {
    taperStroke(g, [[ew * 0.75, top(0.75)], [ew * 0.95, top(0.75) - eh * 0.28], [ew * 1.05, top(0.75) - eh * 0.36]], lashW * 0.6, 0.3 * lw, H.ink);
  }
  if (st.crowsFeet && !H.small) {
    for (let i = 0; i < 3; i++) { const ang = -0.45 + i * 0.4;
      taperStroke(g, [[ew * 1.18, eh * 0.05], [ew * 1.18 + Math.cos(ang) * eh * 0.9, eh * 0.05 + Math.sin(ang) * eh * 0.9]], 1.4 * lw, 0.3 * lw, rgba(PAL.inkSoft, 0.7)); }
    taperStroke(g, [[-ew * 0.4, eh * 1.0], [0, eh * 1.15], [ew * 0.6, eh * 0.95]], 0.3 * lw, 0.3 * lw, rgba(PAL.inkSoft, 0.5), 1.3 * lw);
  }
  g.restore();
}

function drawTearDrop(g, H) {
  const { p, st, k } = H; const pr = clamp(p.tearDrop ?? 0); if (pr <= 0) return;
  const side = p.tearSide ?? 1, x0 = side * (st.eye.x + 0.03);
  if (H.vis(x0, 0.3) < 0.1) return;
  const y0 = st.eye.y + 0.1, y1 = 0.78, y = lerp(y0, y1, pr), xx = x0 + side * 0.04 * pr;
  const a = H.S(x0, y0, 0.01), d = H.S(xx, y, 0.015), r = 0.026 * k;
  g.save(); g.beginPath(); g.moveTo(a[0], a[1]); g.quadraticCurveTo(lerp(a[0], d[0], .5) + side * r * .3, lerp(a[1], d[1], .5), d[0], d[1]);
  g.strokeStyle = 'rgba(225,242,255,0.55)'; g.lineWidth = r * 0.5; g.lineCap = 'round'; g.stroke();
  g.beginPath(); g.moveTo(d[0], d[1] - r * 1.6);
  g.bezierCurveTo(d[0] + r * 0.9, d[1] - r * 0.4, d[0] + r, d[1] + r, d[0], d[1] + r);
  g.bezierCurveTo(d[0] - r, d[1] + r, d[0] - r * 0.9, d[1] - r * 0.4, d[0], d[1] - r * 1.6);
  g.fillStyle = 'rgba(205,232,255,0.8)'; g.fill(); g.strokeStyle = rgba(PAL.inkSoft, 0.8); g.lineWidth = H.lw * 0.6; g.stroke();
  g.fillStyle = '#ffffff'; g.beginPath(); g.ellipse(d[0] - r * 0.3, d[1] - r * 0.1, r * 0.25, r * 0.35, 0, 0, TAU); g.fill();
  g.restore();
}

// ------------------------------------------------------------------ brows
function drawBrows(g, H) {
  const { p, st, k } = H; const B = st.brow;
  for (const side of [-1, 1]) {
    const per = side < 0 ? (p.browL ?? 0) : (p.browR ?? 0);
    const raise = (p.browRaise ?? 0) * 0.07 + per * 0.06, knit = clamp(p.browKnit ?? 0);
    const bi = p.browInner ?? 0, bo = p.browOuter ?? 0;
    const yi = B.y + 0.02 - bi * 0.075 - raise + knit * 0.03 + Math.max(0, -bi) * 0.02;
    const yo = B.y + 0.01 - bo * 0.06 - raise * 0.8 + bi * 0.02;
    const ym = (yi + yo) / 2 - B.arch - Math.max(0, bi) * 0.01;
    const xi = side * (B.xi - knit * 0.035), xo = side * B.xo;
    if (H.vis(side * 0.3, B.y) < -0.05) continue;
    const pts = [[xi, yi], [lerp(xi, xo, 0.35), lerp(yi, ym, 0.7)], [lerp(xi, xo, 0.7), ym + 0.004], [xo, yo]].map(([x, y]) => H.S(x, y, 0.025));
    const vs = clamp(H.vis(side * 0.3, B.y) * 1.3, 0.35, 1);
    if (B.outline) taperStroke(g, pts, B.w0 * k * 1.25 * vs + H.lw * 0.6, B.w1 * k * 1.5, B.edge ? H.C(B.edge) : H.ink, B.wm * k * 1.25 * vs + H.lw * 0.6);
    taperStroke(g, pts, B.w0 * k * vs, B.w1 * k * 0.6, H.C(B.color), B.wm * k * vs);
    if (B.bushy && !H.small) for (let i = 0; i < 4; i++) {
      const q = pts[1 + (i % 3)], ang = -1.2 - side * 0.5 + i * 0.25 * side;
      taperStroke(g, [q, [q[0] + side * 0.03 * k * (0.6 + i * 0.2), q[1] + Math.sin(ang) * 0.02 * k]], B.w0 * k * 0.35, 0.5, H.C(B.color));
    }
  }
}

// ------------------------------------------------------------------ nose & mouth
function drawNose(g, H) {
  const { st, k, p } = H; const N = st.nose; const sd = H.ld >= 0 ? -1 : 1;
  const tip = H.S(0, N.y, N.z), bridge = H.S(sd * 0.03, N.y - N.len, 0.02);
  const wing = H.S(sd * N.w, N.y + 0.035, 0.0), under = H.S(0, N.y + 0.05, N.z * 0.35);
  g.save();
  fillPoly(g, [bridge, tip, under, wing, H.S(sd * N.w * 0.8, N.y - N.len * 0.3, 0)], H.CS(st.skinShadow));
  // tip ink & nostril tick
  const yawA = Math.abs(p.yaw ?? 0);
  if (yawA > 0.12) {
    const fs = (p.yaw ?? 0) > 0 ? 1 : -1;
    const ridge = [H.S(0, N.y - N.len * 0.9, 0.02), H.S(0, N.y - N.len * 0.4, N.z * 0.55), tip];
    taperStroke(g, ridge, 0.2, H.lw * 0.9, rgba(H.ink, clamp((yawA - 0.12) * 3)));
  }
  const n1 = H.S(-N.w * 0.5, N.y + 0.04, N.z * 0.3), n2 = H.S(N.w * 0.5, N.y + 0.04, N.z * 0.3);
  taperStroke(g, [n1, under, n2], H.lw * 0.3, H.lw * 0.3, H.ink, H.lw * 1.1);
  if (N.big) { // bulbous outline
    const pts = [H.S(-N.w * 1.1, N.y + 0.02, 0.02), H.S(-N.w * 0.9, N.y + 0.06, N.z * .4), under, H.S(N.w * 0.9, N.y + 0.06, N.z * .4), H.S(N.w * 1.1, N.y + 0.02, 0.02)];
    taperStroke(g, pts, H.lw * 0.3, H.lw * 0.3, rgba(H.ink, 0.8), H.lw * 0.9);
    taperStroke(g, [H.S(sd * N.w * 1.15, N.y - 0.03, 0), H.S(sd * N.w * 1.2, N.y + 0.02, 0.01)], H.lw * 0.2, H.lw * 0.6, rgba(H.ink, 0.7));
  }
  // nose highlight
  const hi = H.S(-sd * 0.012, N.y - 0.02, N.z * 0.9);
  if (!H.small) { g.fillStyle = 'rgba(255,250,240,0.55)'; g.beginPath(); g.ellipse(hi[0], hi[1], 0.012 * k, 0.008 * k, 0, 0, TAU); g.fill(); }
  g.restore();
}

function drawMouth(g, H) {
  const { p, st, k } = H; const M = st.mouth;
  const sm = clamp(p.smile ?? 0, -1, 1), op = clamp(p.mouthOpen ?? 0), wd = clamp(p.mouthWide ?? 0, -1, 1);
  const rd = clamp(p.mouthRound ?? 0), pr = clamp(p.mouthPress ?? 0), as = clamp(p.mouthAsym ?? 0, -1, 1);
  const tr = clamp(p.lipTremble ?? 0), t = H.t;
  const y0 = M.y, mw = M.w * (1 + 0.28 * wd + 0.12 * sm - 0.35 * rd) * (1 - 0.06 * pr);
  const cy = sd => y0 - (sm + as * sd * 0.9) * 0.05 + (op * 0.02);
  const jit = i => tr * 0.008 * noise1(t * 13 + i * 2.7, 7);
  const oh = op * M.h * (1 - 0.7 * pr) * (1 + 0.3 * rd);
  const pt = (x, y) => H.S(x, y, 0.01);
  if (oh > 0.012) {
    const l = [-mw, cy(-1)], r = [mw, cy(1)];
    const upper = [l, [-mw * 0.55, y0 - oh * 0.12 + jit(1) - sm * 0.01], [0, y0 - oh * 0.18 + jit(2)], [mw * 0.55, y0 - oh * 0.12 + jit(3) - sm * 0.01], r];
    const lower = [r, [mw * (0.6 - rd * 0.15), y0 + oh * (0.85 + rd * 0.1) + jit(4)], [0, y0 + oh + jit(5)], [-mw * (0.6 - rd * 0.15), y0 + oh * (0.85 + rd * 0.1) + jit(6)]];
    const U = upper.map(([x, y]) => pt(x, y)), Lw = lower.map(([x, y]) => pt(x, y));
    const shape = gg => splinePath(gg, U.concat(Lw), true, 0.45);
    g.save(); g.beginPath(); shape(g); g.fillStyle = '#4a1d22'; g.fill(); g.clip();
    if ((p.teeth ?? true) && op > 0.12) { g.beginPath(); splinePath(g, U.concat(U.slice().reverse().map(([x, y]) => [x, y + oh * 0.24 * k])), true, 0.4);
      g.fillStyle = H.C('#f7f2ea'); g.fill(); }
    const tg = pt(0, y0 + oh * 0.95); g.beginPath(); g.ellipse(tg[0], tg[1], mw * 0.6 * k, oh * 0.38 * k, 0, 0, TAU); g.fillStyle = H.C('#b8564f'); g.fill();
    g.restore();
    g.save(); g.beginPath(); shape(g); g.strokeStyle = H.ink; g.lineWidth = H.lw * 0.9; g.lineJoin = 'round'; g.stroke(); g.restore();
    if (!H.small) { const a = pt(-mw * 0.35, y0 + oh + 0.05), b = pt(mw * 0.35, y0 + oh + 0.05), c = pt(0, y0 + oh + 0.055);
      taperStroke(g, [a, c, b], 0.3, 0.3, rgba(PAL.inkSoft, 0.45), H.lw * 0.8); }
  } else {
    const pts = [[-mw, cy(-1)], [-mw * 0.5, y0 - sm * 0.014 + jit(1) - pr * 0.004], [0, y0 + 0.004 * (1 - pr) + jit(2)], [mw * 0.5, y0 - sm * 0.014 + jit(3)], [mw, cy(1)]].map(([x, y]) => pt(x, y));
    taperStroke(g, pts, H.lw * 0.35, H.lw * 0.35, H.ink, H.lw * (1.05 + pr * 0.6));
    if (!H.small) { const a = pt(-mw * 0.32, y0 + 0.06), b = pt(mw * 0.32, y0 + 0.06), c = pt(0, y0 + 0.066);
      taperStroke(g, [a, c, b], 0.3, 0.3, rgba(PAL.inkSoft, 0.4 + pr * 0.3), H.lw * 0.85); }
  }
  if (sm > 0.35 && !H.small) for (const sd of [-1, 1]) { const c0 = pt(sd * mw, cy(sd)), c1 = pt(sd * (mw + 0.025), cy(sd) - 0.02);
    taperStroke(g, [c0, c1], H.lw * 0.6, 0.3, rgba(H.ink, 0.6 * (sm - 0.3))); }
}

// ------------------------------------------------------------------ ears & neck
function drawEars(g, H) {
  const { st } = H; const E = st.ear;
  for (const side of [-1, 1]) {
    const wb = H.W(0.15) * 0.92;
    const raw = [[0.0, -0.04, 0.0], [0.07, 0.0, -0.08], [0.1, 0.12, -0.13], [0.08, 0.27, -0.1], [0.03, 0.38, -0.04], [-0.01, 0.3, 0.02], [-0.01, 0.05, 0.02]];
    const pts = raw.map(([o, y, z]) => H.P(side * (wb + o * E.s), E.y + y * E.s, z * E.s - 0.05));
    const n = H.rot(side, 0, -0.2); const lit = n[0] * H.Lv[0] + n[2] * H.Lv[2];
    g.save(); g.beginPath(); splinePath(g, pts, true); g.fillStyle = lit > 0 ? H.C(st.skin) : H.CS(st.skinShadow); g.fill();
    g.strokeStyle = H.ink; g.lineWidth = H.lw * 0.9; g.stroke();
    const inner = [[0.05, 0.05, -0.06], [0.07, 0.15, -0.09], [0.04, 0.27, -0.05]].map(([o, y, z]) => H.P(side * (wb + o * E.s), E.y + y * E.s, z * E.s - 0.05));
    taperStroke(g, inner, H.lw * 0.3, H.lw * 0.3, rgba(H.ink, 0.6), H.lw * 0.8);
    g.restore();
  }
}
function neckPoly(H) {
  const nw = H.st.neck.w * 1.08, y0 = 0.35, y1 = 1.5, z = -0.18;
  return [H.P(-nw, y0, z), H.P(nw, y0, z), H.P(nw * 1.04, 1.25, z), H.P(nw * 1.3, y1, z), H.P(-nw * 1.3, y1, z), H.P(-nw * 1.04, 1.25, z)];
}

// ------------------------------------------------------------------ hair system
// clump: {r:[x,y], tip:[x,y], w, dz, tz, bend} on head surface; returns screen polygon
function clumpPoly(H, c, i, sc = 1) {
  const { p, k } = H; const t = H.t, wind = clamp(p.wind ?? 0), wdir = p.windDir ?? 1, wet = clamp(p.wetHair ?? 0);
  const n = c.pt ? 8 : 5, center = [];
  for (let j = 0; j <= n; j++) { const u = j / n;
    const x = lerp(c.r[0], c.tip[0], u) + (c.bend ?? 0) * Math.sin(u * Math.PI) * 0.12;
    const y = lerp(c.r[1], c.tip[1], u) * (1 - wet * 0.04 * u) + wet * 0.04 * u;
    const dz = lerp(c.dz ?? 0.05, c.tz ?? 0.03, u);
    let q = c.back ? H.P(x * sc, y, (c.z ?? -0.6) + dz) : H.S(x * sc, y, dz);
    const sway = (noise1(t * 0.9 + i * 0.37, i) * 0.5 + 0.5 * Math.sin(t * 2.1 + i)) * wind * 0.05 + wind * wdir * 0.05 + noise1(t * 0.4 + i, 3) * 0.006;
    q = [q[0] + sway * k * u * u * (c.flex ?? 1), q[1] - Math.abs(sway) * k * u * u * 0.3]; center.push(q);
  }
  const L = [], R = [];
  for (let j = 0; j <= n; j++) {
    const a = center[Math.max(0, j - 1)], b = center[Math.min(n, j + 1)]; let dx = b[0] - a[0], dy = b[1] - a[1];
    const u = j / n, prof = c.pt ? (u < 0.3 ? lerp(0.78, 1, u / 0.3) : Math.pow((1 - u) / 0.7, 0.9)) : Math.pow(1 - u, 0.55);
    const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l; const w = c.w * k * prof * (1 - wet * 0.3) / 2;
    L.push([center[j][0] - dy * w, center[j][1] + dx * w]); R.push([center[j][0] + dy * w, center[j][1] - dx * w]);
  }
  return L.concat(R.reverse().slice(1));
}
function drawClumps(g, H, clumps, fill, shadowC, lwk = 0.8, off = 0) {
  clumps.forEach((c, i) => {
    const poly = clumpPoly(H, c, i + off);
    const lt = c.back ? -1 : H.shadeAt(c.r[0], Math.max(c.r[1], -0.6));
    g.beginPath(); splinePath(g, poly, true, 0.35); g.fillStyle = lt > 0.25 ? fill : shadowC; g.fill();
    g.strokeStyle = H.ink; g.lineWidth = H.lw * lwk; g.lineJoin = 'round'; g.stroke();
  });
}
// cel-shaded pointed clumps: per-clump terminator from the head light, highlight chip along the clump, inner flow line
function drawClumpsCel(g, H, clumps, fill, shadowC, hiC, lwk = 0.8, off = 0, sp = null) {
  sp = sp || shadowPoly(H, -1.5, 1.4, 0.28);
  clumps.forEach((c, i) => {
    const poly = clumpPoly(H, c, i + off);
    g.save(); g.beginPath(); splinePath(g, poly, true, 0.3); g.fillStyle = c.back ? shadowC : fill; g.fill();
    if (!c.back) { g.save(); g.clip(); g.beginPath(); polyPath(g, sp); g.fillStyle = shadowC; g.fill();
      if (hiC && !H.small) { const n = poly.length, m = (n - 1) / 2, a = Math.round(m * 0.34), b = Math.round(m * 0.46);
        const L = poly.slice(a, b + 1), R = poly.slice(n - 1 - b, n - a).reverse();
        const ctr = L.map((q, j) => [lerp(q[0], R[j][0], 0.5), lerp(q[1], R[j][1], 0.5)]);
        const hp = L.map((q, j) => [lerp(q[0], ctr[j][0], 0.3), lerp(q[1], ctr[j][1], 0.3)]).concat(R.map((q, j) => [lerp(q[0], ctr[j][0], 0.6), lerp(q[1], ctr[j][1], 0.6)]).reverse());
        const lt = H.shadeAt(c.r[0], Math.max(c.r[1], -0.7));
        g.beginPath(); splinePath(g, hp, true, 0.3); g.fillStyle = rgba(hiC, lt > 0.2 ? 0.85 : 0.35); g.fill(); }
      g.restore(); }
    g.beginPath(); if (c.back) splinePath(g, poly, true, 0.3); else splinePath(g, poly.slice(2, -2), false, 0.3);
    g.strokeStyle = H.ink; g.lineWidth = H.lw * lwk; g.lineJoin = 'round'; g.lineCap = 'round'; g.stroke();
    if (!c.back && !H.small && c.w > 0.12) { const n = poly.length, m = (n - 1) / 2;
      const fl = [0.3, 0.5, 0.72].map(u => { const j = Math.round(m * u); const q = poly[j], r = poly[n - 1 - j]; return [lerp(q[0], r[0], 0.55 + 0.1 * (i % 2)), lerp(q[1], r[1], 0.55)]; });
      taperStroke(g, fl, 0.3, 0.3, rgba(H.ink, 0.55), H.lw * 0.6); }
    g.restore();
  });
}
// big hair volume (convex mass around the cranium)
function hairMass(H, y0, y1, sc, cy = -0.1) { return hull(H.cloud(y0, y1, sc, 14, 18, cy)); }

// ------------------------------------------------------------------ styles
const KEEPER_PROF = {
  y: [-1.0, -0.93, -0.78, -0.5, -0.2, 0.0, 0.2, 0.4, 0.58, 0.74, 0.88, 0.97, 1.0],
  w: [0.12, 0.42, 0.62, 0.73, 0.75, 0.73, 0.69, 0.62, 0.52, 0.4, 0.26, 0.13, 0.04],
  df: [0.2, 0.45, 0.66, 0.77, 0.8, 0.8, 0.78, 0.74, 0.69, 0.62, 0.55, 0.49, 0.42],
  db: [-0.2, -0.6, -0.85, -0.95, -0.95, -0.9, -0.62, -0.4, -0.25, -0.12, -0.05, 0, 0],
};
const MIRA_PROF = {
  y: [-1.06, -0.98, -0.8, -0.5, -0.2, 0.0, 0.2, 0.4, 0.58, 0.72, 0.84, 0.9],
  w: [0.12, 0.46, 0.7, 0.8, 0.81, 0.79, 0.75, 0.67, 0.55, 0.41, 0.22, 0.04],
  df: [0.22, 0.5, 0.72, 0.8, 0.83, 0.82, 0.8, 0.76, 0.7, 0.62, 0.54, 0.46],
  db: [-0.22, -0.65, -0.9, -0.98, -0.97, -0.9, -0.6, -0.38, -0.22, -0.1, -0.03, 0],
};
const GRANDPA_PROF = {
  y: [-1.0, -0.93, -0.78, -0.5, -0.2, 0.0, 0.2, 0.4, 0.58, 0.74, 0.88, 0.97, 1.0],
  w: [0.12, 0.44, 0.64, 0.75, 0.78, 0.77, 0.75, 0.7, 0.62, 0.5, 0.34, 0.18, 0.05],
  df: [0.2, 0.45, 0.66, 0.77, 0.8, 0.8, 0.78, 0.75, 0.7, 0.63, 0.56, 0.5, 0.44],
  db: [-0.2, -0.6, -0.85, -0.95, -0.95, -0.9, -0.62, -0.4, -0.25, -0.12, -0.05, 0, 0],
};

// --- Keeper hair
const K_FRINGE = [ // drawn in order: outer locks first, center on top; pt = pointed profile
  { r: [-0.42, -0.96], tip: [-0.8, 0.12], w: 0.2, bend: -0.22, pt: 1, dz: 0.09, tz: 0.07 },
  { r: [0.42, -0.96], tip: [0.79, 0.06], w: 0.2, bend: 0.2, pt: 1, dz: 0.09, tz: 0.07 },
  { r: [-0.23, -1.0], tip: [-0.64, -0.16], w: 0.27, bend: -0.28, pt: 1 },
  { r: [0.23, -1.0], tip: [0.66, -0.04], w: 0.26, bend: 0.26, pt: 1 },
  { r: [-0.16, -1.0], tip: [-0.46, -0.04], w: 0.3, bend: -0.22, pt: 1 },
  { r: [0.17, -1.0], tip: [0.48, -0.22], w: 0.28, bend: 0.26, pt: 1 },
  { r: [0.10, -1.0], tip: [0.28, -0.08], w: 0.3, bend: 0.2, pt: 1 },
  { r: [-0.09, -1.0], tip: [-0.26, -0.28], w: 0.28, bend: -0.12, pt: 1 },
  { r: [0.03, -1.0], tip: [0.12, -0.32], w: 0.28, bend: 0.18, pt: 1 },
  { r: [-0.03, -1.0], tip: [-0.1, -0.12], w: 0.3, bend: 0.1, pt: 1 },
  { r: [0.02, -0.8], tip: [0.05, 0.02], w: 0.06, bend: 0.55, pt: 1, dz: 0.07, tz: 0.06 }, // strands across forehead
  { r: [-0.18, -0.78], tip: [-0.24, -0.06], w: 0.05, bend: -0.45, pt: 1, dz: 0.07, tz: 0.06 },
];
const K_SIDE = [
  { r: [-0.5, -0.9], tip: [-0.8, 0.4], w: 0.2, bend: -0.1, dz: 0.1, tz: 0.08, pt: 1 },
  { r: [-0.48, -0.88], tip: [-0.72, 0.2], w: 0.13, dz: 0.11, tz: 0.08, pt: 1 },
  { r: [0.5, -0.9], tip: [0.8, 0.36], w: 0.2, bend: 0.1, dz: 0.1, tz: 0.08, pt: 1 },
  { r: [0.48, -0.88], tip: [0.72, 0.16], w: 0.13, dz: 0.11, tz: 0.08, pt: 1 },
];
const K_BACK = [ // locks flowing down behind the head; only their pointed tips clear the mass
  { back: true, r: [-0.6, -0.5], tip: [-0.92, 0.2], w: 0.36, z: -0.5, pt: 1, bend: -0.2 }, { back: true, r: [0.6, -0.5], tip: [0.92, 0.16], w: 0.36, z: -0.5, pt: 1, bend: 0.2 },
  { back: true, r: [-0.5, -0.2], tip: [-0.84, 0.5], w: 0.34, z: -0.55, pt: 1, bend: -0.15 }, { back: true, r: [0.5, -0.2], tip: [0.86, 0.46], w: 0.34, z: -0.55, pt: 1, bend: 0.15 },
  { back: true, r: [-0.66, -0.8], tip: [-0.96, -0.36], w: 0.32, z: -0.4, pt: 1, bend: -0.2 }, { back: true, r: [0.66, -0.8], tip: [0.97, -0.42], w: 0.32, z: -0.4, pt: 1, bend: 0.2 },
  { back: true, r: [-0.3, 0.0], tip: [-0.6, 0.66], w: 0.36, z: -0.6, pt: 1 }, { back: true, r: [0.3, 0.0], tip: [0.62, 0.62], w: 0.36, z: -0.6, pt: 1 },
  { back: true, r: [-0.3, -0.98], tip: [-0.62, -1.1], w: 0.3, z: -0.35, pt: 1, bend: -0.2 }, { back: true, r: [0.2, -1.0], tip: [0.5, -1.12], w: 0.28, z: -0.35, pt: 1, bend: 0.3 },
];
function capShading(H, poly, base, sh, hi, hiRow = -0.74) {
  const sp = shadowPoly(H, -1.3, 0.6, 0.3);
  const band = [];
  for (let i = 0; i <= 10; i++) band.push(H.S(lerp(-0.55, 0.55, i / 10), hiRow - 0.05 * Math.cos((i / 10 - 0.5) * 2) + 0.02, 0.12));
  for (let i = 10; i >= 0; i--) band.push(H.S(lerp(-0.5, 0.5, i / 10), hiRow + 0.05 + 0.02 * Math.sin(i * 1.7), 0.12));
  return { fill: base, shadow: sh, shadowFn: gg => polyPath(gg, sp), hi, hiFn: hi ? gg => polyPath(gg, band) : null };
}
const KEEPER = {
  name: 'keeper', prof: KEEPER_PROF, skin: PAL.kSkin, skinShadow: PAL.kSkinShadow, iris: PAL.kIris, glowRing: true,
  eye: { x: 0.31, y: 0, w: 0.165, h: 0.095, iris: 0.078, irisX: -0.005, tilt: 0.5, flick: 1, lash: 0.045, lashes: false },
  brow: { y: -0.2, xi: 0.1, xo: 0.46, arch: 0.025, w0: 0.045, wm: 0.035, w1: 0.008, color: '#9a96a2', outline: true, edge: '#4a4652' },
  nose: { y: 0.33, z: 0.11, len: 0.2, w: 0.055 }, mouth: { y: 0.62, w: 0.15, h: 0.16 }, ear: { y: -0.02, s: 1 }, neck: { w: 0.3 },
  hair: PAL.kHair, hairShadow: PAL.kHairShadow, hairHi: PAL.kHairHi,
  backHair(g, H) {
    const cs = H.CS(this.hairShadow);
    drawClumpsCel(g, H, K_BACK, cs, cs, null, 0.8, 20);
    const m = hairMass(H, -1.06, 0.3, 1.12);
    g.beginPath(); polyPath(g, m); g.fillStyle = cs; g.fill(); g.strokeStyle = H.ink; g.lineWidth = H.lw; g.stroke();
  },
  frontHair(g, H) {
    const c = H.C(this.hair), cs = H.CS(this.hairShadow), hi = this.hairHi;
    const cap = hull(H.cloud(-1.06, -0.72, 1.08, 10, 20, -0.1, false));
    cel(g, gg => polyPath(gg, cap), { fill: c, shadow: cs, shadowFn: gg => polyPath(gg, shadowPoly(H, -1.5, 1.4, 0.28)), line: H.ink, lw: H.lw });
    const sp = shadowPoly(H, -1.5, 1.4, 0.28);
    drawClumpsCel(g, H, K_SIDE, c, cs, hi, 0.8, 40, sp);
    drawClumpsCel(g, H, K_FRINGE, c, cs, hi, 0.65, 0, sp);
  },
  fringeShadow: K_FRINGE,
  extras(g, H) {
    if (H.p.seams === false || H.small) return;
    for (const sd of [-1, 1]) {
      if (H.vis(sd * 0.55, 0.5) > 0.3) {
        const pts = [[0.95, 0.32], [0.85, 0.52], [0.68, 0.68]].map(([u, y]) => H.S(sd * H.W(y) * u, y, 0.005));
        taperStroke(g, pts, H.lw * 0.6, 0.3, H.C(PAL.kSeam), H.lw * 0.6);
      }
      if (H.vis(sd * 0.62, -0.3) > 0.05) taperStroke(g, [H.S(sd * 0.62, -0.36, 0.005), H.S(sd * 0.65, -0.18, 0.005)], H.lw * 0.6, 0.3, H.C(PAL.kSeam));
    }
  },
};

// --- Mira hair (curly circles)
function curlBlob(g, H, pts, fill, hi, lwk = 1) {
  g.save(); g.strokeStyle = H.ink; g.lineWidth = H.lw * 2 * lwk;
  for (const [x, y, r] of pts) { g.beginPath(); g.arc(x, y, r, 0, TAU); g.stroke(); }
  g.fillStyle = fill;
  for (const [x, y, r] of pts) { g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); }
  if (hi && !H.small) { g.strokeStyle = hi; g.lineWidth = H.lw * 0.9; g.lineCap = 'round';
    pts.forEach(([x, y, r], i) => { if (i % 3) return; g.beginPath(); g.arc(x, y, r * 0.6, -2.4, -1.2); g.stroke(); }); }
  g.restore();
}
function sphereCurls(H, y0, y1, sc, rr, onlyFront, rows = 6, cols = 14) {
  const out = [];
  for (let i = 0; i <= rows; i++) { const y = lerp(y0, y1, i / rows), w = H.W(y) * sc, df = H.DF(y) * sc, db = H.DB(y) * sc;
    for (let j = 0; j < cols; j++) { const th = (j + (i % 2) * 0.5) / cols * TAU, s = Math.sin(th);
      const v = H.rot(w * Math.cos(th), -0.1 + (y + 0.1) * sc, s >= 0 ? s * df : s * -db);
      if (onlyFront && v[2] < 0.1) continue; if (!onlyFront && v[2] > 0.25) continue;
      const q = H.scr(v); out.push([q[0], q[1], rr * H.k * (0.85 + 0.3 * hash(i * 17 + j)), v[2]]); } }
  return out.sort((a, b) => a[3] - b[3]);
}
const MIRA = {
  name: 'mira', prof: MIRA_PROF, skin: PAL.mSkin, skinShadow: PAL.mSkinShadow, iris: PAL.mIris, glowRing: false,
  eye: { x: 0.32, y: 0.04, w: 0.165, h: 0.11, iris: 0.088, irisX: -0.005, tilt: 0.25, flick: 0.7, lash: 0.032, lashes: true },
  brow: { y: -0.17, xi: 0.11, xo: 0.45, arch: 0.03, w0: 0.032, wm: 0.026, w1: 0.006, color: '#2b1a14', outline: true, edge: '#120a07' },
  nose: { y: 0.33, z: 0.07, len: 0.13, w: 0.05 }, mouth: { y: 0.58, w: 0.13, h: 0.16 }, ear: { y: 0.02, s: 0.95 }, neck: { w: 0.27 },
  hair: PAL.mHair, hairShadow: '#1a0f0b', hairHi: PAL.mHairHi,
  hoodBack(g, H, hood) {
    const coat = H.C(PAL.mCoat), cs = H.CS(PAL.mCoatShadow);
    if (hood < 0.5) { const a = H.P(0, 1.05, -0.65), r = 0.55 * H.k;
      cel(g, gg => { gg.ellipse(a[0], a[1] + r * 0.2, r * 1.1, r * 0.55, 0, 0, TAU); }, { fill: cs, line: H.ink, lw: H.lw }); return; }
    const m = hull(H.cloud(-1.12, 1.1, 1.3, 14, 18, -0.1));
    cel(g, gg => polyPath(gg, m), { fill: coat, shadow: cs, shadowFn: gg => polyPath(gg, shadowPoly(H, -1.4, 1.4, 0.3)), line: H.ink, lw: H.lw });
  },
  hoodFront(g, H) {
    const coat = H.C(PAL.mCoat);
    const outer = hull(H.cloud(-1.12, 0.75, 1.3, 12, 18, -0.1, false));
    const inner = hull(H.cloud(-1.0, 0.75, 1.08, 12, 18, -0.1, false));
    g.save(); g.beginPath(); polyPath(g, outer); polyPath(g, inner.slice().reverse()); g.fillStyle = coat; g.fill('evenodd');
    g.strokeStyle = H.ink; g.lineWidth = H.lw; g.stroke(); g.restore();
  },
  backHair(g, H) {
    const p = H.p, hood = clamp(p.hood ?? 0); if (hood > 0) this.hoodBack(g, H, hood);
    if (hood >= 0.5) return;
    const fill = H.C(this.hair), hi = H.C(this.hairHi);
    // ponytail (high, puffy) behind the crown
    const wind = clamp(p.wind ?? 0), t = H.t, sw = noise1(t * 0.8, 9) * 0.06 + wind * (p.windDir ?? 1) * 0.12;
    const pts = [];
    for (let i = 0; i < 14; i++) { const a = i / 14 * TAU, rr = 0.24 + 0.08 * hash(i * 3.1);
      const v = H.rot(Math.cos(a) * rr + sw * (1 + Math.sin(a)), -1.05 + Math.sin(a) * rr * 0.9 - 0.12, -0.5 + Math.sin(a * 2) * 0.1);
      const q = H.scr(v); pts.push([q[0], q[1], (0.13 + 0.04 * hash(i)) * H.k, v[2]]); }
    curlBlob(g, H, pts, fill, hi);
    const m = sphereCurls(H, -1.0, 0.2, 1.1, 0.16, false, 6, 14);
    curlBlob(g, H, m, fill, null);
    g.beginPath(); polyPath(g, hairMass(H, -1.0, 0.15, 1.1)); g.fillStyle = fill; g.fill();
  },
  frontHair(g, H) {
    const p = H.p, hood = clamp(p.hood ?? 0), fill = H.C(this.hair), hi = H.C(this.hairHi), wet = clamp(p.wetHair ?? 0);
    const cap = hull(H.cloud(-1.06, -0.5, 1.1, 10, 20, -0.1, false));
    cel(g, gg => polyPath(gg, cap), { fill, shadow: H.CS(this.hairShadow), shadowFn: gg => polyPath(gg, shadowPoly(H, -1.3, 0.6, 0.3)), line: H.ink, lw: H.lw });
    // hairline curls
    const curls = [];
    for (let i = 0; i <= 9; i++) { const x = lerp(-0.66, 0.66, i / 9), y = -0.52 - 0.12 * (1 - Math.pow(x / 0.7, 2)) * 0.6 + 0.03 * hash(i * 7);
      if (H.vis(x, y) < 0) continue; const q = H.S(x, y, 0.08); curls.push([q[0], q[1], (0.1 + 0.03 * hash(i + 4)) * H.k * (1 - wet * 0.3), 0]); }
    curlBlob(g, H, curls, fill, hi);
    // temple ringlets: short chains of curls hanging in front of the ears
    if (!H.small) for (const sd of [-1, 1]) {
      if (H.vis(sd * 0.7, -0.1) < -0.1) continue;
      const sw = noise1(H.t * 1.1 + sd, 4) * 0.02 + clamp(p.wind ?? 0) * 0.04 * (p.windDir ?? 1), rl = [];
      for (let j = 0; j < 3; j++) { const u = j / 2, q = H.S(sd * (0.72 - 0.02 * u) + sw * u, -0.42 + u * 0.22, 0.12);
        rl.push([q[0], q[1], (0.11 - 0.025 * u) * H.k * (1 - wet * 0.3), 0]); }
      curlBlob(g, H, rl, fill, hi);
    }
    if (hood >= 0.5) this.hoodFront(g, H);
  },
  fringeShadow: null,
  extras(g, H) {
    if (H.small) return;
    const r = rng(42);
    for (const sd of [-1, 1]) for (let i = 0; i < 5; i++) {
      const x = sd * (0.28 + r() * 0.22), y = 0.2 + r() * 0.12; if (H.vis(x, y) < 0.15) continue;
      const q = H.S(x, y, 0.01); g.fillStyle = rgba('#5a2f20', 0.55); g.beginPath(); g.arc(q[0], q[1], H.k * 0.008, 0, TAU); g.fill(); }
  },
};

// --- Grandpa
const G_SIDE = [
  { r: [-0.7, -0.42], tip: [-0.78, -0.02], w: 0.14, dz: 0.06, tz: 0.04 }, { r: [-0.66, -0.32], tip: [-0.72, 0.1], w: 0.1, dz: 0.06, tz: 0.04 },
  { r: [0.7, -0.42], tip: [0.78, -0.02], w: 0.14, dz: 0.06, tz: 0.04 }, { r: [0.66, -0.32], tip: [0.72, 0.1], w: 0.1, dz: 0.06, tz: 0.04 },
];
const GRANDPA = {
  name: 'grandpa', prof: GRANDPA_PROF, skin: PAL.gSkin, skinShadow: PAL.gSkinShadow, iris: PAL.gIris, glowRing: false,
  eye: { x: 0.3, y: 0.02, w: 0.13, h: 0.06, iris: 0.058, irisX: 0, tilt: -0.1, flick: 0.3, lash: 0.024, lashes: false },
  brow: { y: -0.17, xi: 0.08, xo: 0.47, arch: 0.02, w0: 0.075, wm: 0.06, w1: 0.012, color: PAL.gBeard, outline: true, bushy: true },
  nose: { y: 0.36, z: 0.15, len: 0.24, w: 0.08, big: true }, mouth: { y: 0.66, w: 0.15, h: 0.14 }, ear: { y: -0.02, s: 1.12 }, neck: { w: 0.36 },
  hair: PAL.gBeard, hairShadow: PAL.gBeardShadow, crowsFeet: true,
  backHair(g, H) {
    const cs = H.CS(this.hairShadow);
    if (H.p.cap === false) return;
    const m = hull(H.cloud(-1.12, -0.42, 1.12, 10, 18, -0.1));
    cel(g, gg => polyPath(gg, m), { fill: H.CS(PAL.gCapShadow), line: H.ink, lw: H.lw });
  },
  frontHair(g, H) {
    const c = H.C(this.hair), cs = H.CS(this.hairShadow);
    drawClumps(g, H, G_SIDE, c, cs, 0.7, 60);
    if (H.p.cap === false) {
      const cap = hull(H.cloud(-1.02, -0.62, 1.03, 8, 20, -0.1, false));
      cel(g, gg => polyPath(gg, cap), { ...capShading(H, cap, c, cs, null), line: H.ink, lw: H.lw * 0.8 });
      return;
    }
    const cap = hull(H.cloud(-1.14, -0.5, 1.13, 10, 20, -0.1, false));
    cel(g, gg => polyPath(gg, cap), { ...capShading(H, cap, H.C(PAL.gCap), H.CS(PAL.gCapShadow), null), line: H.ink, lw: H.lw });
    // folded cuff
    const top = [], bot = [];
    for (let i = 0; i <= 16; i++) { const x = lerp(-1, 1, i / 16); const yT = -0.68, yB = -0.47;
      const wT = H.W(yT) * 1.16, wB = H.W(yB) * 1.14;
      top.push([x * wT, yT, Math.sqrt(Math.max(0, 1 - x * x)) * H.DF(yT) * 1.16]); bot.push([x * wB, yB, Math.sqrt(Math.max(0, 1 - x * x)) * H.DF(yB) * 1.14]); }
    const vt = top.map(v => H.rot(...v)), vb = bot.map(v => H.rot(...v));
    const cuff = vt.map(v => H.scr(v)).concat(vb.map(v => H.scr(v)).reverse());
    cel(g, gg => polyPath(gg, cuff), { fill: H.C(shade(PAL.gCap, 0.08)), shadow: H.CS(PAL.gCapShadow),
      shadowFn: gg => polyPath(gg, shadowPoly(H, -1.3, 0.6, 0.3)), line: H.ink, lw: H.lw });
    if (!H.small) for (let i = 1; i < 16; i++) { if (vt[i][2] < 0.15) continue;
      taperStroke(g, [H.scr(vt[i]), H.scr(vb[i])], H.lw * 0.5, H.lw * 0.5, rgba(PAL.gCapShadow, 0.8)); }
  },
  fringeShadow: null,
  preMouth(g, H) { // beard
    const c = H.C(PAL.gBeard), cs = H.CS(PAL.gBeardShadow);
    const outer = [], inner = [];
    for (let i = 0; i <= 12; i++) { const u = i / 12, y = lerp(0.12, 1.08, u);
      const w = H.W(Math.min(y, 0.98)) * (y > 0.98 ? 0.6 : 1.03); outer.push([w, y + 0.03 * Math.sin(i * 2.3) * u]); }
    const sil = outer.map(([w, y]) => { let lo = null, hi = null; const yy = Math.min(y, 1), d = H.DF(yy) * 1.04;
      for (let j = 0; j <= 24; j++) { const th = Math.PI * j / 24, v = H.rot(w * Math.cos(th), y, d * Math.sin(th) + 0.02);
        if (!lo || v[0] < lo[0]) lo = v; if (!hi || v[0] > hi[0]) hi = v; } return [H.scr(lo), H.scr(hi)]; });
    const L = sil.map(q => q[0]), R = sil.map(q => q[1]).reverse();
    const ins = [[0.6, 0.18], [0.5, 0.4], [0.32, 0.55], [0.18, 0.56], [0, 0.53], [-0.18, 0.56], [-0.32, 0.55], [-0.5, 0.4], [-0.6, 0.18]].map(([x, y]) => H.S(x, y, 0.03));
    const chin = [H.S(-0.2, 1.06, 0.05), H.S(0, 1.12, 0.06), H.S(0.2, 1.06, 0.05)];
    const poly = L.slice(0, -1).concat(chin, R.slice(1), ins);
    cel(g, gg => splinePath(gg, poly, true, 0.35), { fill: c, shadow: cs, shadowFn: gg => polyPath(gg, shadowPoly(H, -1, 1.4, 0.32)), line: H.ink, lw: H.lw });
    // mouth hole in beard
    const mh = [[-0.2, 0.64], [0, 0.6], [0.2, 0.64], [0.14, 0.76], [0, 0.79], [-0.14, 0.76]].map(([x, y]) => H.S(x, y, 0.02));
    g.beginPath(); splinePath(g, mh, true); g.fillStyle = H.C(this.skin); g.fill();
  },
  extras(g, H) { // mustache over mouth, nasolabial folds
    const c = H.C(PAL.gBeard);
    if (!H.small) for (const sd of [-1, 1]) if (H.vis(sd * 0.3, 0.45) > 0.1)
      taperStroke(g, [H.S(sd * 0.13, 0.4, 0.02), H.S(sd * 0.23, 0.5, 0.01), H.S(sd * 0.25, 0.58, 0.01)], H.lw * 0.8, 0.3, rgba(PAL.inkSoft, 0.6));
    const sm = clamp(H.p.smile ?? 0, -1, 1), op = clamp(H.p.mouthOpen ?? 0);
    const m = [[-0.27, 0.66 - sm * 0.05], [-0.15, 0.55], [0, 0.5], [0.15, 0.55], [0.27, 0.66 - sm * 0.05], [0.14, 0.62 - op * 0.02], [0, 0.6 - op * 0.03], [-0.14, 0.62 - op * 0.02]].map(([x, y]) => H.S(x, y, 0.05));
    cel(g, gg => splinePath(gg, m, true, 0.4), { fill: c, line: H.ink, lw: H.lw * 0.9 });
    if (!H.small) taperStroke(g, [H.S(-0.12, 0.57, 0.06), H.S(0, 0.55, 0.06), H.S(0.12, 0.57, 0.06)], 0.3, 0.3, rgba(PAL.gBeardShadow, 0.9), H.lw);
  },
};
function cel(g, shapeFn, o) { // local wrapper around core.cel semantics (keeps import list small)
  g.save(); g.beginPath(); shapeFn(g); g.fillStyle = o.fill; g.fill();
  if (o.shadow && o.shadowFn) { g.save(); g.beginPath(); shapeFn(g); g.clip(); g.beginPath(); o.shadowFn(g); g.fillStyle = o.shadow; g.fill();
    if (o.hi && o.hiFn) { g.beginPath(); o.hiFn(g); g.fillStyle = o.hi; g.fill(); } g.restore(); }
  if (o.line && o.lw > 0) { g.beginPath(); shapeFn(g); g.lineJoin = 'round'; g.strokeStyle = o.line; g.lineWidth = o.lw; g.stroke(); }
  g.restore();
}
export const STYLES = { keeper: KEEPER, mira: MIRA, grandpa: GRANDPA };

// ------------------------------------------------------------------ main draw
export function drawHead(g, style, p = {}) {
  const st = style || KEEPER; const H = makeRig(st, p);
  const skin = H.C(st.skin), skinSh = H.CS(st.skinShadow);
  g.save();
  st.backHair(g, H);
  // neck + chin shadow
  const neck = neckPoly(H);
  const face = hull(H.cloud(-1.0, st.prof.y[st.prof.y.length - 1], 1, 24, 22, -0.1));
  g.save(); g.beginPath(); polyPath(g, neck); g.fillStyle = skin; g.fill(); g.clip();
  g.beginPath(); polyPath(g, face.map(([x, y]) => [x + H.ld * -0.05 * H.k, y + 0.16 * H.k])); g.fillStyle = skinSh; g.fill();
  g.beginPath(); polyPath(g, shadowPoly(H, 0.4, 1.7, 0.35)); g.fill();
  g.restore();
  g.save(); g.beginPath(); polyPath(g, neck); g.strokeStyle = H.ink; g.lineWidth = H.lw; g.stroke(); g.restore();
  drawEars(g, H);
  // face
  g.save(); g.beginPath(); polyPath(g, face); g.fillStyle = skin; g.fill(); g.clip();
  g.beginPath(); polyPath(g, shadowPoly(H)); g.fillStyle = skinSh; g.fill();
  if (st.fringeShadow) { g.fillStyle = skinSh; st.fringeShadow.forEach((c, i) => { const poly = clumpPoly(H, c, i);
    g.beginPath(); splinePath(g, poly.map(([x, y]) => [x - H.ld * 0.03 * H.k, y + 0.06 * H.k]), true, 0.35); g.fill(); });
    const band = hull(H.cloud(-1.04, -0.6, 1.0, 8, 20, -0.1, false)); g.beginPath(); polyPath(g, band.map(([x, y]) => [x, y + 0.05 * H.k])); g.fill(); }
  // blush, dirt
  const bl = clamp(p.blush ?? 0);
  if (bl > 0) for (const sd of [-1, 1]) { if (H.vis(sd * 0.4, 0.25) < 0.1) continue; const q = H.S(sd * 0.4, 0.24, 0.01);
    const gr = g.createRadialGradient(q[0], q[1], 0, q[0], q[1], 0.13 * H.k); gr.addColorStop(0, rgba('#ff6f6a', 0.38 * bl)); gr.addColorStop(1, rgba('#ff6f6a', 0));
    g.fillStyle = gr; g.beginPath(); g.ellipse(q[0], q[1], 0.16 * H.k, 0.09 * H.k, 0, 0, TAU); g.fill(); }
  const dr = clamp(p.dirt ?? 0);
  if (dr > 0) { const q = H.S(-0.35, 0.45, 0.01); const gr = g.createRadialGradient(q[0], q[1], 0, q[0], q[1], 0.12 * H.k);
    gr.addColorStop(0, rgba('#6b4a32', 0.4 * dr)); gr.addColorStop(1, rgba('#6b4a32', 0)); g.fillStyle = gr; g.fillRect(q[0] - H.k * .15, q[1] - H.k * .15, H.k * .3, H.k * .3); }
  g.restore();
  g.save(); g.beginPath(); polyPath(g, face); g.strokeStyle = H.ink; g.lineWidth = H.lw * 1.1; g.lineJoin = 'round'; g.stroke(); g.restore();
  drawNose(g, H);
  if (st.preMouth) st.preMouth(g, H);
  drawMouth(g, H);
  for (const sd of [-1, 1]) drawEye(g, H, sd);
  drawTearDrop(g, H);
  drawBrows(g, H);
  st.frontHair(g, H);
  if (st.extras) st.extras(g, H);
  // fx: sand, wet, sweat
  const sa = clamp(p.sand ?? 0);
  if (sa > 0 && !H.small) { const r = rng(7); g.fillStyle = H.C('#d9b77f');
    for (let i = 0; i < 18 * sa; i++) { const x = -0.2 - r() * 0.4, y = 0.3 + r() * 0.4; if (H.vis(x, y) < 0.1) continue;
      const q = H.S(x, y, 0.01); g.beginPath(); g.arc(q[0], q[1], H.k * (0.004 + r() * 0.005), 0, TAU); g.fill(); } }
  const wt = Math.max(clamp(p.wet ?? 0), clamp(p.sweat ?? 0) * 0.5);
  if (wt > 0 && !H.small) { const r = rng(p.wet ? 11 : 13);
    const n = Math.round((p.wet ? 9 : 3) * wt);
    for (let i = 0; i < n; i++) { const x = (r() - 0.5) * 1.1, y = p.wet ? -0.35 + r() * 1.1 : -0.45 + r() * 0.15; if (H.vis(x, y) < 0.15) continue;
      const q = H.S(x, y, 0.02), rr = H.k * (0.01 + r() * 0.012);
      g.fillStyle = 'rgba(220,238,255,0.7)'; g.beginPath(); g.ellipse(q[0], q[1], rr * 0.7, rr, 0, 0, TAU); g.fill();
      g.fillStyle = '#ffffff'; g.beginPath(); g.arc(q[0] - rr * 0.2, q[1] - rr * 0.3, rr * 0.3, 0, TAU); g.fill(); } }
  // rim light on the side away from the key
  const rim = clamp(p.rim ?? 0);
  if (rim > 0) {
    const sd = H.ld >= 0 ? -1 : 1, rimC = H.light.rim;
    g.save(); g.beginPath(); polyPath(g, face); g.clip();
    g.beginPath(); const ax = H.axisX; g.rect(H.X + sd * 0.15 * H.k - (sd < 0 ? 4 * H.k : 0), H.Y - 3 * H.k, 4 * H.k, 6 * H.k); g.clip();
    g.beginPath(); polyPath(g, face); g.strokeStyle = rgba(rimC, 0.85 * rim); g.lineWidth = H.lw * 2.6; g.stroke(); g.restore();
  }
  g.restore();
}

// ------------------------------------------------------------------ expressions & helpers
const BASE = { eyeOpen: 1, lowerLid: 0, browInner: 0, browOuter: 0, browRaise: 0, browKnit: 0, smile: 0, mouthOpen: 0,
  mouthWide: 0, mouthRound: 0, mouthPress: 0, mouthAsym: 0, gazeX: 0, gazeY: 0, pupil: 1, tears: 0, tearDrop: 0, lipTremble: 0, blush: 0 };
export const EXPR = {
  neutral: {},
  worried: { browInner: 0.75, browOuter: -0.2, smile: -0.2, eyeOpen: 1.05, mouthPress: 0.2, browKnit: 0.2 },
  sad: { browInner: 0.85, browOuter: -0.45, eyeOpen: 0.68, smile: -0.45, gazeY: -0.35, lowerLid: 0.1 },
  hopeful: { browInner: 0.45, browRaise: 0.2, eyeOpen: 1.08, smile: 0.25, gazeY: 0.25 },
  smile: { smile: 0.7, lowerLid: 0.35, eyeOpen: 0.9, browRaise: 0.1, browInner: 0.1 },
  laugh: { smile: 1, mouthOpen: 0.6, mouthWide: 0.45, lowerLid: 0.85, eyeOpen: 0.4, browRaise: 0.25, browInner: 0.25 },
  surprised: { eyeOpen: 1.32, browRaise: 0.9, mouthOpen: 0.42, mouthRound: 0.6, pupil: 0.8 },
  determined: { browInner: -0.65, browOuter: 0.1, eyeOpen: 0.88, lowerLid: 0.25, smile: -0.05, mouthPress: 0.5, browKnit: 0.3 },
  tender: { smile: 0.4, eyeOpen: 0.75, lowerLid: 0.3, browInner: 0.4, gazeY: -0.15 },
  tired: { eyeOpen: 0.5, browInner: 0.2, browOuter: -0.3, smile: -0.1, gazeY: -0.2 },
  awe: { eyeOpen: 1.2, browRaise: 0.5, browInner: 0.3, mouthOpen: 0.2, mouthRound: 0.3, gazeY: 0.4, pupil: 1.25 },
  relief: { eyeOpen: 0.7, smile: 0.45, browInner: 0.45, browOuter: -0.2, mouthOpen: 0.1 },
  cryingSmile: { smile: 0.6, browInner: 0.9, browOuter: -0.3, eyeOpen: 0.7, lowerLid: 0.45, tears: 1, tearDrop: 0.5, lipTremble: 0.4, mouthOpen: 0.1 },
  sleep: { eyeOpen: 0, browInner: 0.1, smile: 0.05, browRaise: -0.1 },
  wry: { mouthAsym: 0.6, smile: 0.2, browL: 0.3, browR: -0.1, lowerLid: 0.2 },
  fond: { smile: 0.5, lowerLid: 0.4, eyeOpen: 0.8, browInner: 0.3 },
  focused: { browInner: -0.35, eyeOpen: 0.85, lowerLid: 0.3, mouthPress: 0.3, browKnit: 0.3 },
  scared: { eyeOpen: 1.3, browInner: 0.95, browRaise: 0.4, mouthOpen: 0.3, mouthWide: 0.3, pupil: 0.65, smile: -0.4 },
  shout: { mouthOpen: 1, mouthWide: 0.4, browInner: -0.75, browKnit: 0.5, eyeOpen: 1.1, lowerLid: 0.15 },
  reading: { gazeY: -0.6, eyeOpen: 0.72, browInner: 0.1 },
  wonder: { eyeOpen: 1.15, browRaise: 0.4, browInner: 0.2, smile: 0.2, mouthOpen: 0.15, pupil: 1.2, gazeY: 0.3 },
  pained: { browInner: 0.9, browKnit: 0.6, eyeOpen: 0.6, lowerLid: 0.4, smile: -0.5, mouthOpen: 0.2, mouthWide: 0.5 },
  moved: { browInner: 0.7, eyeOpen: 0.85, tears: 0.7, smile: 0.2, mouthPress: 0.3, lipTremble: 0.3 },
};
export function expr(name, overrides = {}) { return { ...BASE, ...(EXPR[name] || {}), ...overrides }; }
export function blend(a, b, k) {
  const out = { ...a };
  for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const va = a[key] ?? BASE[key] ?? 0, vb = b[key] ?? BASE[key] ?? 0;
    out[key] = (typeof va === 'number' && typeof vb === 'number') ? lerp(va, vb, k) : (k >= 0.5 ? (b[key] ?? a[key]) : (a[key] ?? b[key]));
  }
  return out;
}
export function blinkAt(t, seed = 1, rate = 1) {
  const per = 3.4 / Math.max(rate, 0.05), i0 = Math.floor(t / per); let v = 0;
  for (let i = i0 - 1; i <= i0 + 1; i++) {
    const c = (i + 0.5 + 0.7 * (hash(seed * 13.7 + i * 1.31) - 0.5)) * per;
    const d = Math.abs(t - c), half = 0.075 * (rate < 0.8 ? 1.5 : 1);
    if (d < half) v = Math.max(v, 1 - Math.pow(d / half, 2));
  }
  return clamp(v);
}
export function saccade(t, seed = 1, amp = 1) {
  const r = 0.55, i = Math.floor(t / r + hash(seed) * 3), f = clamp((t / r + hash(seed) * 3 - i) * 8);
  const at = j => [(hash(seed * 7.1 + j * 3.3) - 0.5) * 0.14, (hash(seed * 5.3 + j * 1.9) - 0.5) * 0.08];
  const a = at(i - 1), b = at(i);
  return { x: lerp(a[0], b[0], f) * amp, y: lerp(a[1], b[1], f) * amp };
}
export function lipsync(p, m) {
  if (!m) return { ...p };
  const o = clamp(m.open ?? 0), w = m.wide ?? 0, r = clamp(m.round ?? 0), pr = clamp(m.press ?? 0);
  return { ...p, mouthOpen: clamp(Math.max(p.mouthOpen ?? 0, o * 0.85)), mouthWide: clamp((p.mouthWide ?? 0) + w * 0.6, -1, 1),
    mouthRound: clamp(Math.max(p.mouthRound ?? 0, r)), mouthPress: clamp(Math.max(p.mouthPress ?? 0, pr) * (1 - o)) };
}
