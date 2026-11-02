// ============================================================================
//  DRAW — reusable procedural primitives (sprites, light, figures, reaper)
// ============================================================================
const Draw = (() => {
  // ---- glow sprite cache: one soft radial dot per color, drawn with drawImage (fast)
  const spriteCache = new Map();
  function sprite(c, hard = 0) {
    const key = (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + '|' + hard;
    let s = spriteCache.get(key);
    if (s) return s;
    if (spriteCache.size > 512) spriteCache.delete(spriteCache.keys().next().value);
    s = document.createElement('canvas'); s.width = s.height = 128;
    const g = s.getContext('2d');
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    if (hard) {
      gr.addColorStop(0, rgba([255, 255, 255], 1));
      gr.addColorStop(0.18, rgba(mix(c, [255, 255, 255], 0.5), 0.9));
      gr.addColorStop(0.4, rgba(c, 0.35));
      gr.addColorStop(1, rgba(c, 0));
    } else {
      gr.addColorStop(0, rgba(c, 1));
      gr.addColorStop(0.25, rgba(c, 0.55));
      gr.addColorStop(0.6, rgba(c, 0.14));
      gr.addColorStop(1, rgba(c, 0));
    }
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    spriteCache.set(key, s);
    return s;
  }
  // additive glow at (x,y) radius r
  function glow(ctx, x, y, r, c, a = 1, hard = 0) {
    if (a <= 0.002 || r <= 0) return;
    const pa = ctx.globalAlpha, pc = ctx.globalCompositeOperation;
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = pa * clamp(a);
    ctx.drawImage(sprite(c, hard), x - r, y - r, r * 2, r * 2);
    ctx.globalAlpha = pa; ctx.globalCompositeOperation = pc;
  }
  function radial(ctx, x, y, r0, r1, stops) {
    const g = ctx.createRadialGradient(x, y, r0, x, y, r1);
    stops.forEach(([o, c]) => g.addColorStop(o, c));
    return g;
  }

  // ---- two-bone IK: returns elbow point. bend = +1 / -1 chooses elbow side
  function ik(sx, sy, tx, ty, l1, l2, bend = 1) {
    let dx = tx - sx, dy = ty - sy;
    let d = Math.hypot(dx, dy);
    const maxD = (l1 + l2) * 0.965;
    if (d > maxD) { dx *= maxD / d; dy *= maxD / d; d = maxD; }
    const a = Math.atan2(dy, dx);
    const cosA = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1);
    const ang = a + bend * Math.acos(cosA);
    return { ex: sx + Math.cos(ang) * l1, ey: sy + Math.sin(ang) * l1, hx: sx + dx, hy: sy + dy };
  }

  // tapered stroke along polyline pts (array of [x,y]), widths w0->w1
  function taper(ctx, pts, w0, w1) {
    if (pts.length < 2) return;
    const L = [], R = [];
    for (let i = 0; i < pts.length; i++) {
      const p = pts[i], q = pts[Math.min(pts.length - 1, i + 1)], o = pts[Math.max(0, i - 1)];
      let nx = -(q[1] - o[1]), ny = q[0] - o[0];
      const n = Math.hypot(nx, ny) || 1; nx /= n; ny /= n;
      const w = lerp(w0, w1, i / (pts.length - 1)) / 2;
      L.push([p[0] + nx * w, p[1] + ny * w]); R.push([p[0] - nx * w, p[1] - ny * w]);
    }
    ctx.beginPath();
    ctx.moveTo(L[0][0], L[0][1]);
    for (let i = 1; i < L.length; i++) ctx.lineTo(L[i][0], L[i][1]);
    const e = pts[pts.length - 1];
    ctx.arc(e[0], e[1], w1 / 2, Math.atan2(L[L.length - 1][1] - e[1], L[L.length - 1][0] - e[0]), Math.atan2(R[R.length - 1][1] - e[1], R[R.length - 1][0] - e[0]), true);
    for (let i = R.length - 1; i >= 0; i--) ctx.lineTo(R[i][0], R[i][1]);
    const s = pts[0];
    ctx.arc(s[0], s[1], w0 / 2, Math.atan2(R[0][1] - s[1], R[0][0] - s[0]), Math.atan2(L[0][1] - s[1], L[0][0] - s[0]), true);
    ctx.closePath();
  }
  // quadratic bezier sampled into points
  function qpts(x0, y0, cx, cy, x1, y1, n = 10) {
    const out = [];
    for (let i = 0; i <= n; i++) { const t = i / n, u = 1 - t; out.push([u * u * x0 + 2 * u * t * cx + t * t * x1, u * u * y0 + 2 * u * t * cy + t * t * y1]); }
    return out;
  }


  // ==========================================================================
  //  LUMINOUS FIGURE — a member of the emotional family
  //  f = { x, y (floor line), h (standing height), c (rgb), a (presence 0..1),
  //        lean (rad, + leans right), tilt (head, rad), face (-1 left / +1 right),
  //        kneel (0..1), hair ('bun'|'long'|'curls'|'short'|'veil'|'tuft'),
  //        hands: [{x,y,w,bend}], eyes (0 open .. 1 closed), t, seed }
  //  figureBody() draws behind the bed; figureArms() draws over the man.
  // ==========================================================================
  const WHITE = [255, 248, 236];
  function rot(px, py, a) { const c = Math.cos(a), s = Math.sin(a); return [px * c - py * s, px * s + py * c]; }
  function skeleton(f) {
    const h = f.h, t = f.t, s = f.seed || 0;
    const kneel = f.kneel || 0;
    const sway = Noise.n1(t * 0.21 + s * 10) * h * 0.008;
    const br = Math.sin(t * 1.15 + s * 2) * h * 0.004;
    const lean = (f.lean || 0) + Noise.n1(t * 0.17 + s * 3) * 0.015;
    const hip = [f.x + sway, f.y - h * lerp(0.5, 0.26, kneel)];
    const P = (lx, ly) => { const [rx, ry] = rot(lx * h, ly * h, lean); return [hip[0] + rx, hip[1] + ry]; };
    const neck = P(0, -0.345 + br / h);
    const tilt = (f.tilt || 0) + lean * 0.5;
    const [ox, oy] = rot(0, -h * 0.078, tilt);
    const head = [neck[0] + ox, neck[1] + oy];
    return { h, lean, tilt, hip, P, neck, head, shL: P(-0.112, -0.305 + br / h), shR: P(0.112, -0.305 + br / h), chest: P(0, -0.24) };
  }

  function figureBody(ctx, f) {
    const a = clamp(f.a) * (f.bodyA ?? 1);
    const S = f._sk = skeleton(f);   // arms need the skeleton even when the body is faded out
    if (a <= 0.003) return;
    const h = S.h, c = f.c, t = f.t, s = f.seed || 0;
    const lite = mix(c, WHITE, 0.45);
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    glow(ctx, S.chest[0], S.chest[1], h * 0.55, c, 0.1 * a);
    // torso silhouette (local coords, rotated by lean)
    const P = S.P;
    const body = new Path2D();
    const side = (k) => [
      P(k * 0.026, -0.352), P(k * 0.05, -0.33), P(k * 0.1, -0.318), P(k * 0.122, -0.29),
      P(k * 0.112, -0.24), P(k * 0.094, -0.17), P(k * 0.085, -0.11), P(k * 0.098, -0.03), P(k * 0.105, 0.06),
    ];
    const L = side(-1), R = side(1);
    body.moveTo(L[0][0], L[0][1]);
    for (let i = 1; i < L.length; i++) { const m = [(L[i - 1][0] + L[i][0]) / 2, (L[i - 1][1] + L[i][1]) / 2]; body.quadraticCurveTo(L[i - 1][0], L[i - 1][1], m[0], m[1]); }
    body.lineTo(L[L.length - 1][0], L[L.length - 1][1]);
    // dissolving hem
    const hem = 7;
    for (let i = 1; i < hem; i++) {
      const u = i / hem;
      const q = P(lerp(-0.105, 0.105, u), 0.06 + 0.03 * Noise.n2(u * 3 + s, t * 0.5));
      body.lineTo(q[0], q[1]);
    }
    body.lineTo(R[R.length - 1][0], R[R.length - 1][1]);
    for (let i = R.length - 2; i >= 0; i--) { const m = [(R[i + 1][0] + R[i][0]) / 2, (R[i + 1][1] + R[i][1]) / 2]; body.quadraticCurveTo(R[i + 1][0], R[i + 1][1], m[0], m[1]); }
    body.closePath();
    const top = S.neck[1] - h * 0.02, bot = S.hip[1] + h * 0.07;
    const fill = ctx.createLinearGradient(0, top, 0, bot);
    fill.addColorStop(0, rgba(lite, 0.36 * a)); fill.addColorStop(0.45, rgba(c, 0.2 * a)); fill.addColorStop(1, rgba(c, 0));
    ctx.fillStyle = fill; ctx.fill(body);
    // inner volume: heart-light
    ctx.save(); ctx.clip(body);
    const vol = ctx.createRadialGradient(S.chest[0], S.chest[1], 0, S.chest[0], S.chest[1], h * 0.2);
    vol.addColorStop(0, rgba(WHITE, 0.35 * a)); vol.addColorStop(1, rgba(lite, 0));
    ctx.fillStyle = vol; ctx.fillRect(S.chest[0] - h * 0.3, S.chest[1] - h * 0.3, h * 0.6, h * 0.6);
    ctx.restore();
    // rim light (fresnel-ish edge), fading toward the hem
    const rim = ctx.createLinearGradient(0, top, 0, bot);
    rim.addColorStop(0, rgba(lite, 0.75 * a)); rim.addColorStop(0.6, rgba(c, 0.3 * a)); rim.addColorStop(1, rgba(c, 0));
    ctx.strokeStyle = rim; ctx.lineWidth = Math.max(0.8, h * 0.004); ctx.stroke(body);
    ctx.globalAlpha = 0.18; ctx.lineWidth = h * 0.018; ctx.stroke(body); ctx.globalAlpha = 1;

    // head + hair silhouette
    const [hx, hy] = S.head, r = h * 0.062, tl = S.tilt, face = f.face || 0;
    const headP = new Path2D();
    headP.ellipse(hx, hy, r * 0.86, r * 1.05, tl, 0, TAU);
    const hair = new Path2D();
    const H = (lx, ly) => { const [rx, ry] = rot(lx * r, ly * r, tl); return [hx + rx, hy + ry]; };
    const style = f.hair || 'short';
    if (style === 'bun') { const b = H(-face * 0.55, -1.05); hair.arc(b[0], b[1], r * 0.42, 0, TAU); }
    else if (style === 'curls') { for (let i = 0; i < 9; i++) { const an = Math.PI * (1.05 + i / 8 * 0.95); const q = H(Math.cos(an) * 0.95, Math.sin(an) * 1.08); hair.moveTo(q[0] + r * 0.3, q[1]); hair.arc(q[0], q[1], r * 0.3, 0, TAU); } }
    else if (style === 'long') {
      const k = -face || 1; const a0 = H(-0.8 * k, -0.7), a1 = H(-1.25 * k, 0.9), a2 = H(-1.05 * k, 2.3), a3 = H(-0.2 * k, 1.6), a4 = H(0.1 * k, -1.05);
      hair.moveTo(a4[0], a4[1]); hair.quadraticCurveTo(a0[0], a0[1], a1[0], a1[1]); hair.quadraticCurveTo(a2[0], a2[1], a3[0], a3[1]); hair.quadraticCurveTo(H(-0.7 * k, 0)[0], H(-0.7 * k, 0)[1], a4[0], a4[1]);
    }
    else if (style === 'veil') {
      const v0 = H(0, -1.15), v1 = H(-1.3, 0.2), v2 = H(-1.6, 2.6), v3 = H(1.6, 2.6), v4 = H(1.3, 0.2);
      hair.moveTo(v0[0], v0[1]); hair.quadraticCurveTo(v1[0] - r * 0.2, v1[1] - r, v1[0], v1[1]); hair.quadraticCurveTo(v1[0] - r * 0.1, v1[1] + r, v2[0], v2[1]);
      hair.lineTo(v3[0], v3[1]); hair.quadraticCurveTo(v4[0] + r * 0.1, v4[1] + r, v4[0], v4[1]); hair.quadraticCurveTo(v4[0] + r * 0.2, v4[1] - r, v0[0], v0[1]);
    }
    else if (style === 'tuft') { const q = H(face * 0.2, -1.12); hair.moveTo(q[0], q[1]); hair.quadraticCurveTo(q[0] + r * 0.5, q[1] - r * 0.6, q[0] + r * 0.2 + Noise.n1(t + s) * r * 0.1, q[1] - r * 0.75); hair.quadraticCurveTo(q[0] + r * 0.1, q[1] - r * 0.3, q[0] - r * 0.3, q[1]); }
    else { const q0 = H(-0.95, -0.15), q1 = H(0, -1.32), q2 = H(0.95, -0.15); hair.moveTo(q0[0], q0[1]); hair.quadraticCurveTo(q1[0], q1[1], q2[0], q2[1]); hair.quadraticCurveTo(H(0, -0.7)[0], H(0, -0.7)[1], q0[0], q0[1]); }
    const hg = ctx.createRadialGradient(hx, hy - r * 0.4, r * 0.1, hx, hy, r * 1.6);
    hg.addColorStop(0, rgba(mix(c, WHITE, 0.65), 0.55 * a)); hg.addColorStop(1, rgba(c, 0.16 * a));
    ctx.fillStyle = hg; ctx.fill(headP);
    ctx.fillStyle = rgba(mix(c, WHITE, 0.25), (style === 'veil' ? 0.2 : 0.4) * a); ctx.fill(hair);
    ctx.strokeStyle = rgba(lite, 0.3 * a); ctx.lineWidth = Math.max(0.8, h * 0.003); ctx.stroke(headP);
    ctx.strokeStyle = rgba(lite, 0.35 * a); ctx.stroke(hair);
    glow(ctx, hx, hy, r * 3.2, lite, 0.15 * a);

    // eyes — quiet crescents; open = gaze, closed = smiling
    const ec = clamp(f.eyes || 0), ea = a * clamp((a - 0.35) / 0.4);
    if (ea > 0.01) {
      ctx.save(); ctx.translate(hx, hy); ctx.rotate(tl);
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = rgba(mix(c, [25, 18, 30], 0.82), 0.42 * ea);
      ctx.lineWidth = Math.max(0.7, r * 0.08); ctx.lineCap = 'round';
      const ew = r * 0.17;
      const xs = face ? [face * r * 0.12, face * r * 0.55] : [-r * 0.33, r * 0.33];
      for (const ex of xs) {
        ctx.beginPath();
        ctx.moveTo(ex - ew, r * 0.08); ctx.quadraticCurveTo(ex, r * 0.08 + lerp(-ew * 0.35, ew * 0.7, ec), ex + ew, r * 0.08); ctx.stroke();
        if (ec < 0.5) { ctx.fillStyle = rgba(mix(c, [25, 18, 30], 0.85), 0.6 * ea * (1 - 2 * ec)); ctx.beginPath(); ctx.arc(ex + (face || 0) * ew * 0.3, r * 0.03, r * 0.06, 0, TAU); ctx.fill(); }
      }
      ctx.restore();
    }

    // sparks drifting up from the shoulders and crown
    for (let i = 0; i < 9; i++) {
      const ph = (t * (0.11 + (i % 3) * 0.03) + i / 9 + s * 0.37) % 1;
      const sx = S.neck[0] + (((i * 37) % 19) / 19 - 0.5) * h * 0.3 + Noise.n2(i, t * 0.4 + s) * h * 0.05;
      const sy = S.neck[1] + h * 0.05 - ph * h * 0.55;
      glow(ctx, sx, sy, h * 0.012, lite, a * Math.sin(ph * Math.PI) * 0.8, 1);
    }
    ctx.restore();
  }

  function figureArms(ctx, f) {
    const a = clamp(f.a) * (f.armA ?? 1);
    if (a <= 0.003 || !f._sk) return;
    const S = f._sk, h = S.h, c = f.c, lite = mix(c, WHITE, 0.45);
    const hands = f.hands || [];
    const l1 = h * 0.19, l2 = h * 0.2;
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    [S.shL, S.shR].forEach((sh, i) => {
      const hd = hands[i];
      const wgt = hd ? clamp(hd.w) : 0;
      // rest: hands softly together in front of the body
      const rest = S.P(i ? 0.05 : -0.05, -0.2);   // idle hands fold at the heart
      const tx = lerp(rest[0], hd ? hd.x : rest[0], wgt), ty = lerp(rest[1], hd ? hd.y : rest[1], wgt);
      // elbows fall outward and down unless a bend is forced
      // elbows fall outward and down; blend the two IK solutions so an elbow never flips in one frame
      let k;
      if (hd && hd.bend) k = ik(sh[0], sh[1], tx, ty, l1, l2, hd.bend);
      else {
        const k1 = ik(sh[0], sh[1], tx, ty, l1, l2, 1), k2 = ik(sh[0], sh[1], tx, ty, l1, l2, -1);
        const out = i ? 1 : -1, cx = S.chest[0];
        const sc = q => q.ey * 0.6 + (q.ex - cx) * out;
        const m = smooth(0.5 + (sc(k1) - sc(k2)) / 80);
        k = { ex: lerp(k2.ex, k1.ex, m), ey: lerp(k2.ey, k1.ey, m), hx: k1.hx, hy: k1.hy };
      }
      const pts = qpts(sh[0], sh[1], k.ex, k.ey, k.hx, k.hy, 10);
      const armA = a * (0.55 + 0.45 * wgt) * (1 - (f.handOnly || 0));
      const ap = f.handOnly ? pts.slice(Math.floor(pts.length * 0.55 * f.handOnly)) : pts;
      ctx.fillStyle = rgba(c, 0.045 * armA); taper(ctx, ap, h * 0.075, h * 0.05); ctx.fill();
      ctx.fillStyle = rgba(c, 0.17 * armA); taper(ctx, ap, h * 0.05, h * 0.03); ctx.fill();
      ctx.fillStyle = rgba(lite, 0.2 * armA); taper(ctx, ap, h * 0.026, h * 0.016); ctx.fill();
      // hand: palm, a thumb, and four fanned fingers
      const ang = Math.atan2(k.hy - k.ey, k.hx - k.ex);
      ctx.save(); ctx.translate(k.hx, k.hy); ctx.rotate(ang);
      const ha = (f.handOnly > 0.5 ? 0.55 : 0.4) * a * (f.handGlow ?? 1);
      ctx.fillStyle = rgba(mix(c, WHITE, 0.5), ha);
      ctx.beginPath(); ctx.ellipse(h * 0.012, 0, h * 0.027, h * 0.02, 0, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.ellipse(h * 0.012, (i ? -1 : 1) * h * 0.021, h * 0.016, h * 0.006, (i ? -1 : 1) * 0.7, 0, TAU); ctx.fill();
      for (let j = -1.5; j <= 1.5; j++) {
        ctx.save(); ctx.translate(h * 0.03, j * h * 0.007); ctx.rotate(j * 0.28);
        ctx.beginPath(); ctx.ellipse(h * 0.016, 0, h * 0.02, h * 0.0052, 0, 0, TAU); ctx.fill(); ctx.restore();
      }
      ctx.restore();
      glow(ctx, k.hx, k.hy, h * (0.05 + 0.05 * wgt), lite, (0.15 + 0.22 * wgt) * a * (f.handGlow ?? 1), 1);
      f['_hand' + i] = [k.hx, k.hy];
    });
    ctx.restore();
  }
  function figure(ctx, f) { figureBody(ctx, f); figureArms(ctx, f); }

  // ==========================================================================
  //  REAPER — a presence made of smoke and absence, rimmed in cold light
  //  r = { x, y (floor), h, a, lean, reach:{x,y,w,curl}, t, eyes, scythe, smoke }
  // ==========================================================================
  function reaper(ctx, r) {
    const a = clamp(r.a);
    if (a <= 0.003) return;
    const h = r.h, t = r.t, x = r.x, y = r.y, lean = r.lean || 0;
    const cold = [150, 180, 230];
    const topX = x + Math.sin(lean) * h * 0.9, topY = y - h;
    ctx.save();
    // it drinks the light around it
    const dark = ctx.createRadialGradient(x, y - h * 0.5, h * 0.1, x, y - h * 0.5, h * 0.95);
    dark.addColorStop(0, `rgba(1,2,6,${0.6 * a})`); dark.addColorStop(1, 'rgba(1,2,6,0)');
    ctx.fillStyle = dark; ctx.beginPath(); ctx.arc(x, y - h * 0.5, h * 0.95, 0, TAU); ctx.fill();

    const hoodW = 0.075, shoulderW = 0.15, hemW = 0.24;
    const spine = u => [lerp(topX, x, u) + Noise.n2(u * 2, t * 0.3) * h * 0.02 * u, lerp(topY, y, u)];
    const widthAt = u => u < 0.08 ? lerp(0.02, hoodW, smooth(u / 0.08)) : u < 0.2 ? lerp(hoodW, shoulderW, smooth((u - 0.08) / 0.12)) : lerp(shoulderW, hemW, Math.pow((u - 0.2) / 0.8, 1.2));
    const build = (grow, ph) => {
      const pts = [], M = 26;
      for (let i = 0; i <= M; i++) { const u = i / M, [sx, sy] = spine(u), w = widthAt(u) * h * grow; pts.push([sx - w + Noise.n2(u * 4 + 9 + ph, t * 0.5) * h * 0.016 * u, sy]); }
      const HM = 16;
      for (let i = 0; i <= HM; i++) { const u = i / HM, [sx, sy] = spine(1), w = hemW * h * grow; pts.push([sx - w + u * 2 * w, sy - Math.abs(Noise.n2(u * 5 + 3 + ph, t * 0.8)) * h * 0.1]); }
      for (let i = M; i >= 0; i--) { const u = i / M, [sx, sy] = spine(u), w = widthAt(u) * h * grow; pts.push([sx + w + Noise.n2(u * 4 + 19 + ph, t * 0.5) * h * 0.016 * u, sy]); }
      const p = new Path2D(); p.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) p.lineTo(pts[i][0], pts[i][1]); p.closePath();
      return p;
    };
    // smoke halo layers (soft edge), then the body
    for (let k = 3; k >= 1; k--) {
      ctx.fillStyle = `rgba(4,5,10,${0.16 * a})`;
      ctx.fill(build(1 + k * 0.07, k * 5.3));
    }
    const path = build(1, 0);
    const robe = ctx.createLinearGradient(0, topY, 0, y);
    robe.addColorStop(0, `rgba(9,10,17,${0.98 * a})`);
    robe.addColorStop(0.7, `rgba(5,6,11,${0.95 * a})`);
    robe.addColorStop(1, `rgba(5,6,11,0)`);
    ctx.fillStyle = robe; ctx.fill(path);
    // cold rim light from the window side (left), soft, only on the upper body
    ctx.save(); ctx.clip(path);
    ctx.globalCompositeOperation = 'lighter';
    const rim = ctx.createLinearGradient(x - h * 0.25, 0, x + h * 0.02, 0);
    rim.addColorStop(0, rgba(cold, 0.2 * a)); rim.addColorStop(0.35, rgba(cold, 0.05 * a)); rim.addColorStop(1, rgba(cold, 0));
    ctx.fillStyle = rim; ctx.fillRect(x - h, topY, h * 2, h * 0.75);
    // broad soft folds
    for (let i = 0; i < 4; i++) {
      const fx = x + (i - 1.5) * h * 0.09 + Noise.n1(t * 0.2 + i) * h * 0.015;
      const g = ctx.createLinearGradient(fx - h * 0.03, 0, fx + h * 0.03, 0);
      g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.5, rgba(cold, 0.025 * a)); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(fx - h * 0.03, topY + h * 0.25, h * 0.06, h * 0.75);
    }
    ctx.restore();
    // hood opening: a deeper absence
    const [hx, hy] = spine(0.1);
    const hood = ctx.createRadialGradient(hx - h * 0.015, hy + h * 0.01, 0, hx - h * 0.015, hy + h * 0.01, h * 0.07);
    hood.addColorStop(0, `rgba(0,0,0,${a})`); hood.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = hood; ctx.beginPath(); ctx.ellipse(hx - h * 0.015, hy + h * 0.01, h * 0.06, h * 0.075, lean, 0, TAU); ctx.fill();
    const eye = (r.eyes ?? 0.5) * a;
    glow(ctx, hx - h * 0.033, hy + h * 0.008, h * 0.01, cold, 0.25 * eye, 1);
    glow(ctx, hx + h * 0.002, hy + h * 0.008, h * 0.01, cold, 0.25 * eye, 1);
    ctx.strokeStyle = rgba(cold, 0.14 * a); ctx.lineWidth = Math.max(0.8, h * 0.003);
    ctx.beginPath(); const hp0 = spine(0.0), hp1 = spine(0.2);
    ctx.moveTo(hp1[0] - h * 0.14, hp1[1]); ctx.quadraticCurveTo(hp0[0] - h * 0.09, hp0[1] + h * 0.03, hp0[0], hp0[1]); ctx.stroke();

    // scythe
    if (r.scythe !== false) {
      const sa = a * (r.scythe ?? 1);
      const sx0 = x + h * 0.21, sy0 = y - h * 0.02, sx1 = x + h * 0.13 + Math.sin(lean) * h * 0.6, sy1 = y - h * 1.08;
      ctx.strokeStyle = `rgba(16,18,26,${0.95 * sa})`; ctx.lineWidth = h * 0.011; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(sx0, sy0); ctx.lineTo(sx1, sy1); ctx.stroke();
      ctx.strokeStyle = rgba(cold, 0.14 * sa); ctx.lineWidth = Math.max(0.8, h * 0.0025); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(sx1, sy1);
      ctx.quadraticCurveTo(sx1 - h * 0.18, sy1 - h * 0.1, sx1 - h * 0.36, sy1 + h * 0.07);
      ctx.quadraticCurveTo(sx1 - h * 0.19, sy1 - h * 0.025, sx1 + h * 0.01, sy1 + h * 0.035);
      ctx.closePath();
      ctx.fillStyle = `rgba(12,14,22,${0.96 * sa})`; ctx.fill();
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(cold, 0.3 * sa); ctx.lineWidth = Math.max(0.8, h * 0.0025);
      ctx.beginPath(); ctx.moveTo(sx1 - h * 0.02, sy1 - h * 0.012); ctx.quadraticCurveTo(sx1 - h * 0.18, sy1 - h * 0.1, sx1 - h * 0.36, sy1 + h * 0.07); ctx.stroke();
      ctx.restore();
    }

    // reaching arm (sleeve + bony hand)
    if (r.reach && r.reach.w > 0.001) {
      const w = clamp(r.reach.w);
      const [sx, sy] = spine(0.24);
      const shx = sx - h * 0.1, shy = sy;
      const tx = lerp(shx - h * 0.05, r.reach.x, w), ty = lerp(shy + h * 0.35, r.reach.y, w);
      const k = ik(shx, shy, tx, ty, h * 0.27, h * 0.27, 1);
      const sleeve = qpts(shx, shy, k.ex, k.ey, k.hx, k.hy, 8);
      ctx.fillStyle = `rgba(7,8,14,${0.97 * a})`; taper(ctx, sleeve, h * 0.09, h * 0.05); ctx.fill();
      const ang = Math.atan2(k.hy - k.ey, k.hx - k.ex);
      ctx.save(); ctx.translate(k.hx, k.hy); ctx.rotate(ang);
      ctx.strokeStyle = rgba([190, 200, 218], 0.5 * a); ctx.lineWidth = Math.max(0.8, h * 0.0055); ctx.lineCap = 'round';
      const curl = r.reach.curl ?? 0.3;
      for (let j = -1.5; j <= 1.5; j++) {
        ctx.beginPath(); ctx.moveTo(0, j * h * 0.008);
        ctx.quadraticCurveTo(h * 0.035, j * h * 0.012, h * 0.06, j * h * 0.012 + curl * h * 0.03);
        ctx.stroke();
      }
      ctx.restore();
      r._hand = [k.hx, k.hy];
    }
    // smoke curling off the hem
    if (r.smoke !== 0) {
      for (let i = 0; i < 10; i++) {
        const ph = (t * 0.07 + i / 10) % 1;
        const sx = x + (i / 9 - 0.5) * h * 0.5 + Noise.n2(i * 3, t * 0.2) * h * 0.08;
        const sy = y - ph * h * 0.35;
        ctx.fillStyle = `rgba(3,4,8,${0.12 * a * Math.sin(ph * Math.PI)})`;
        ctx.beginPath(); ctx.arc(sx, sy, h * (0.03 + ph * 0.06), 0, TAU); ctx.fill();
      }
    }
    ctx.restore();
  }


  // ==========================================================================
  //  SPIRIT — his luminous self, with legs: stands, walks, runs.
  //  o = { x, y (feet), h, a, c, phase (stride), run (0 stand .. 1 run), dir (+1 right), t, trail, reach }
  // ==========================================================================
  // Catmull-Rom through points -> dense polyline
  function crPts(P, n = 6) {
    const out = [];
    for (let i = 0; i < P.length - 1; i++) {
      const p0 = P[Math.max(0, i - 1)], p1 = P[i], p2 = P[i + 1], p3 = P[Math.min(P.length - 1, i + 2)];
      for (let j = 0; j < n; j++) {
        const t = j / n, t2 = t * t, t3 = t2 * t;
        out.push([0, 1].map(k => 0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)));
      }
    }
    out.push(P[P.length - 1]);
    return out;
  }
  function spirit(ctx, o) {
    const a = clamp(o.a); if (a <= 0.003) return;
    const h = o.h, c = o.c || [255, 240, 214], dir = o.dir || 1, run = clamp(o.run || 0), ph = o.phase || 0, t = o.t || 0;
    const lite = mix(c, WHITE, 0.45);
    const bob = Math.abs(Math.sin(ph)) * h * 0.022 * run;
    const lean = 0.16 * run * dir;
    const hip = [o.x, o.y - h * 0.49 - bob];
    const P = (lx, ly) => { const [rx, ry] = rot(lx * h, ly * h, lean); return [hip[0] + rx, hip[1] + ry]; };
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    glow(ctx, hip[0], hip[1] - h * 0.18, h * 0.62, c, 0.18 * a);
    if (o.trail) for (let i = 1; i <= 7; i++) glow(ctx, hip[0] - dir * i * h * 0.075, hip[1] - h * 0.12 + Math.sin(i + t) * h * 0.02, h * (0.28 - i * 0.025), c, 0.07 * a * o.trail, 1);
    const limb = (pts, w0, w1) => {
      const L = crPts(pts, 6);
      ctx.fillStyle = rgba(c, 0.08 * a); taper(ctx, L, w0 * 2.2, w1 * 2.2); ctx.fill();
      ctx.fillStyle = rgba(lite, 0.26 * a); taper(ctx, L, w0, w1); ctx.fill();
    };
    // legs (one continuous spline each: hip -> knee -> ankle -> toe)
    for (const side of [-1, 1]) {
      const q = ph + (side > 0 ? 0 : Math.PI);
      const sw = Math.sin(q) * 0.62 * run;
      const kneeBend = (Math.max(0, -Math.cos(q)) * 1.1 * run) + 0.04;
      const hp = P(side * 0.02, 0);
      const [kx, ky] = rot(0, h * 0.245, -sw * dir); const knee = [hp[0] + kx, hp[1] + ky];
      const [fx, fy] = rot(0, h * 0.235, (-sw + kneeBend) * dir); const ank = [knee[0] + fx, knee[1] + fy];
      const toe = [ank[0] + dir * h * 0.05, ank[1] + h * 0.008];
      limb([hp, knee, ank, toe], h * 0.062, h * 0.022);
    }
    // torso: sloped shoulders, waist, hips
    const S = (k, x, y) => P(k * x, y);
    const body = new Path2D();
    const pts = [S(-1, 0.022, -0.335), S(-1, 0.06, -0.318), S(-1, 0.098, -0.3), S(-1, 0.1, -0.26), S(-1, 0.078, -0.17), S(-1, 0.07, -0.1), S(-1, 0.078, -0.02), S(-1, 0.06, 0.03),
      S(1, 0.06, 0.03), S(1, 0.078, -0.02), S(1, 0.07, -0.1), S(1, 0.078, -0.17), S(1, 0.1, -0.26), S(1, 0.098, -0.3), S(1, 0.06, -0.318), S(1, 0.022, -0.335)];
    const cr = crPts([...pts, pts[0]], 4);
    body.moveTo(cr[0][0], cr[0][1]); cr.forEach(p => body.lineTo(p[0], p[1])); body.closePath();
    const g = ctx.createLinearGradient(0, hip[1] - h * 0.34, 0, hip[1] + h * 0.04);
    g.addColorStop(0, rgba(lite, 0.42 * a)); g.addColorStop(1, rgba(c, 0.16 * a));
    ctx.fillStyle = g; ctx.fill(body);
    ctx.strokeStyle = rgba(lite, 0.22 * a); ctx.lineWidth = Math.max(0.8, h * 0.0035); ctx.stroke(body);
    // arms counter-swing (or reach toward someone)
    for (const side of [-1, 1]) {
      const s0 = P(side * 0.088, -0.292);
      let hx, hy;
      if (o.reach) { hx = o.reach.x + side * h * 0.035; hy = o.reach.y; }
      else {
        const sw = -Math.sin(ph + (side > 0 ? 0 : Math.PI)) * 0.66 * run;
        const [ex, ey] = rot(0, h * 0.165, sw * dir); const el = [s0[0] + ex, s0[1] + ey];
        const [wx, wy] = rot(0, h * 0.155, (sw - 1.1 * run) * dir); hx = el[0] + wx; hy = el[1] + wy;
      }
      const k = ik(s0[0], s0[1], hx, hy, h * 0.165, h * 0.155, side * dir > 0 ? -1 : 1);
      limb([s0, [k.ex, k.ey], [k.hx, k.hy]], h * 0.04, h * 0.022);
      glow(ctx, k.hx, k.hy, h * 0.035, lite, 0.45 * a, 1);
    }
    // neck + head
    const neck = P(0, -0.335), head = P(0.012 * dir, -0.405);
    limb([P(0, -0.3), neck, P(0.006 * dir, -0.36)], h * 0.034, h * 0.03);
    ctx.beginPath(); ctx.ellipse(head[0], head[1], h * 0.047, h * 0.058, lean, 0, TAU);
    const hg = ctx.createRadialGradient(head[0], head[1] - h * 0.02, 0, head[0], head[1], h * 0.065);
    hg.addColorStop(0, rgba(WHITE, 0.62 * a)); hg.addColorStop(1, rgba(lite, 0.22 * a));
    ctx.fillStyle = hg; ctx.fill(); ctx.strokeStyle = rgba(lite, 0.35 * a); ctx.lineWidth = Math.max(0.8, h * 0.0035); ctx.stroke();
    glow(ctx, head[0], head[1], h * 0.17, lite, 0.25 * a);
    const heart = P(0, -0.24);
    glow(ctx, heart[0], heart[1], h * 0.07, WHITE, 0.45 * a, 1);
    ctx.restore();
  }

  return { sprite, glow, radial, ik, taper, qpts, rot, figure, figureBody, figureArms, reaper, spirit, crPts };
})();
