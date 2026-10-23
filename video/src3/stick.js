// ---------- stick-figure renderer (replaces drawChar; same state/keyframes) ----------
// Simple ink bodies, big expressive faces: eyes with tracking pupils, lids, blinks, brows, lip-synced mouths, tears.
const INK = '#1d1a22', PAPER = '#fff8ec';
function stroke2(ctx, path, col, w) { // halo + ink so lines read on any background
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.strokeStyle = 'rgba(255,250,240,.85)'; ctx.lineWidth = w + 6; ctx.stroke(path);
  ctx.strokeStyle = col; ctx.lineWidth = w; ctx.stroke(path);
}
function stickArms(C, st) {
  const k = C.child ? .78 : 1, a = 108 * k, b = 104 * k;
  const mk = (side, tgt, eb) => {
    const sx = side * 12, sy = 14 * k;
    let dx = tgt[0] - sx, dy = tgt[1] - sy, d = Math.hypot(dx, dy);
    const dd = clamp(d, 20, a + b - 1), ang = Math.atan2(dy, dx);
    const A = Math.acos(clamp((a * a + dd * dd - b * b) / (2 * a * dd), -1, 1));
    const c1 = [sx + Math.cos(ang + A) * a, sy + Math.sin(ang + A) * a], c2 = [sx + Math.cos(ang - A) * a, sy + Math.sin(ang - A) * a];
    const score = c => -side * c[0] + c[1] * .35; // elbows out and down
    const e = score(c1) < score(c2) ? c1 : c2;
    const w = [sx + Math.cos(ang) * dd, sy + Math.sin(ang) * dd];
    return { s: [sx, sy], e, w, side };
  };
  const L = mk(-1, st.armL, st.elbowL), R = mk(1, st.armR, st.elbowR);
  Object.assign(L, { pose: st.handL, ang: st.angL, hold: st.holdL }); Object.assign(R, { pose: st.handR, ang: st.angR, hold: st.holdR });
  return { L, R };
}
function stickHand(ctx, A, col) {
  const [wx, wy] = A.w, fa = Math.atan2(wy - A.e[1], wx - A.e[0]) + (A.ang || 0);
  const pose = typeof A.pose === 'string' ? A.pose : 'relax';
  if (A.hold === 'phoneBack') { ctx.save(); ctx.translate(wx, wy - 26); ctx.rotate(-.1); ctx.fillStyle = '#16161c'; roundRect(ctx, -18, -34, 36, 66, 7); ctx.fill(); ctx.strokeStyle = 'rgba(140,190,255,.8)'; ctx.lineWidth = 2.5; roundRect(ctx, -18, -34, 36, 66, 7); ctx.stroke(); ctx.restore(); }
  ctx.save(); ctx.translate(wx, wy); ctx.rotate(fa);
  const p = new Path2D();
  if (pose === 'open') for (let i = -2; i <= 2; i++) { const a = i * .38; p.moveTo(4, 0); p.lineTo(4 + Math.cos(a) * 24, Math.sin(a) * 24); }
  else if (pose === 'point') { p.moveTo(0, 0); p.lineTo(28, 0); }
  else if (pose === 'flat') { p.moveTo(0, 0); p.lineTo(22, 4); }
  if (pose === 'open' || pose === 'point' || pose === 'flat') stroke2(ctx, p, col, 5);
  ctx.fillStyle = 'rgba(255,250,240,.9)'; ctx.beginPath(); ctx.arc(2, 0, 12, 0, TAU); ctx.fill();
  ctx.fillStyle = col; ctx.beginPath(); ctx.arc(2, 0, pose === 'grip' || pose === 'hold' ? 9.5 : 8, 0, TAU); ctx.fill();
  ctx.restore();
}
function drawChar(ctx, C, st, t) {
  const k = C.child ? .78 : 1, col = C.ink || C.cloth.color, ink = INK;
  ctx.save();
  ctx.translate(st.x + st.swayX * st.s, st.y); ctx.scale(st.s, st.s); ctx.rotate(st.lean);
  ctx.translate(0, -st.br * 1.5 - st.shrug * 7);
  const arms = stickArms(C, st);
  const hip = [0, 190 * k];
  // hood / veil / long hair behind the head
  const hc = [st.headX + st.headYaw * 6, -104 * k + st.headPitch * 6], R = 78 * k;
  if (C.hairBack) { ctx.fillStyle = C.hair; ctx.beginPath(); ctx.ellipse(hc[0], hc[1] + 30, R * 1.1, R * 1.25, 0, 0, TAU); ctx.fill(); }
  if (C.headwear && C.headwear.type === 'veil') { ctx.fillStyle = C.headwear.color; ctx.beginPath(); ctx.ellipse(hc[0], hc[1] + 20, R * 1.2, R * 1.35, 0, 0, TAU); ctx.fill(); }
  if (C.cloth.type === 'hoodie') { ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(hc[0], hc[1] + 46, R * .95, R * .55, 0, 0, TAU); ctx.fill(); }
  // body + legs
  const body = new Path2D();
  body.moveTo(0, -24 * k); body.lineTo(hip[0], hip[1]);
  body.moveTo(hip[0], hip[1]); body.lineTo(-38 * k + st.turn * 10, 360 * k); body.moveTo(hip[0], hip[1]); body.lineTo(38 * k + st.turn * 10, 360 * k);
  stroke2(ctx, body, col, 11);
  // sash / mantle as a bold diagonal band
  if (C.mantle) { const m = new Path2D(); m.moveTo(26, 0); m.lineTo(-24, 150 * k); ctx.save(); stroke2(ctx, m, C.mantle.tartan ? C.mantle.tartan[0] : C.mantle.color, 10); if (C.mantle.tartan) { ctx.strokeStyle = C.mantle.tartan[1]; ctx.lineWidth = 3; ctx.setLineDash([6, 8]); ctx.stroke(m); } ctx.restore(); }
  if (C.cloth.belt) { const b = new Path2D(); b.moveTo(-16, 150 * k); b.lineTo(16, 150 * k); stroke2(ctx, b, C.cloth.belt, 7); }
  // arms
  for (const A of [arms.L, arms.R]) { const p = new Path2D(); p.moveTo(A.s[0], A.s[1]); p.lineTo(A.e[0], A.e[1]); p.lineTo(A.w[0], A.w[1]); stroke2(ctx, p, col, 9); }
  if (st.mid) st.mid(ctx, arms);
  stickHand(ctx, arms.L, col); stickHand(ctx, arms.R, col);
  // head
  ctx.save(); ctx.translate(hc[0], hc[1]); ctx.rotate(st.headRoll);
  stickFace(ctx, C, st, t, R);
  ctx.restore();
  if (st.top) st.top(ctx, arms);
  ctx.restore();
}
function stickFace(ctx, C, st, t, R) {
  const yaw = st.headYaw, pit = st.headPitch, fx = yaw * R * .32, fy = pit * R * .18;
  // head disc
  ctx.fillStyle = 'rgba(255,250,240,.9)'; ctx.beginPath(); ctx.arc(0, 0, R + 4, 0, TAU); ctx.fill();
  ctx.fillStyle = C.face || PAPER; ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.stroke();
  ctx.save(); ctx.beginPath(); ctx.arc(0, 0, R - 2, 0, TAU); ctx.clip();
  // skin tint (subtle, keeps identity) + war paint
  ctx.fillStyle = alpha(C.skin, .28); ctx.fillRect(-R, -R, 2 * R, 2 * R);
  if (C.paint) { ctx.fillStyle = alpha(C.paint, .7); ctx.fillRect(-R, -R * .42 + fy, 2 * R, R * .5); }
  // cheeks
  for (const s of [-1, 1]) { ctx.fillStyle = `rgba(240,110,110,${.18 + Math.max(0, st.smile) * .15 + st.tearful * .12})`; ctx.beginPath(); ctx.ellipse(s * R * .52 + fx, R * .32 + fy, R * .16, R * .1, 0, 0, TAU); ctx.fill(); }
  ctx.restore();
  // eyes
  for (const s of [-1, 1]) stickEye(ctx, C, st, s, R, fx, fy);
  // brows
  for (const s of [-1, 1]) {
    const side = s < 0 ? st.browL : st.browR, bi = st.browIn + side, bo = st.browOut + side;
    const ex = s * R * .36 + fx, by = -R * .5 + fy - st.browY * 8;
    const ix = ex - s * R * .2, ox = ex + s * R * .22;
    const iy = by - bi * 10 + st.frown * 8, oy = by - bo * 8 + 2;
    const p = new Path2D(); p.moveTo(ix, iy); p.quadraticCurveTo((ix + ox) / 2, Math.min(iy, oy) - 6, ox, oy);
    ctx.strokeStyle = INK; ctx.lineCap = 'round'; ctx.lineWidth = 7; ctx.stroke(p);
  }
  stickMouth(ctx, C, st, R, fx, fy);
  // beard scribble
  if (C.beard) { ctx.strokeStyle = C.beardCol || C.hair; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.beginPath(); const n = 9; for (let i = 0; i <= n; i++) { const a = Math.PI * (.15 + .7 * i / n), r = R * (1 + (i % 2) * .22 * (C.beard === 'full' ? 1 : .5)); const x = Math.cos(a) * r + fx * .4, y = Math.sin(a) * r; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); }
  // tears
  for (const tr of st.tears || []) {
    const dur = tr.dur || 2.6, p = (t - tr.t0) / dur; if (p < 0 || p > 1) continue;
    const sx = tr.side * R * .36 + fx, sy = -R * .05 + fy + R * .2, run = clamp((p - .2) / .62), a = p < .85 ? 1 : 1 - (p - .85) / .15;
    const dy = sy + run * R * .9;
    ctx.save(); ctx.globalAlpha *= a;
    ctx.strokeStyle = 'rgba(120,180,255,.55)'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(sx, dy - 4); ctx.stroke();
    ctx.fillStyle = 'rgba(110,170,255,.9)'; ctx.beginPath(); ctx.moveTo(sx, dy - 12); ctx.quadraticCurveTo(sx + 8, dy, sx, dy + 7); ctx.quadraticCurveTo(sx - 8, dy, sx, dy - 12); ctx.fill();
    ctx.restore();
  }
  stickHair(ctx, C, st, R, fx);
}
function stickEye(ctx, C, st, s, R, fx, fy) {
  const far = Math.max(0, s * st.headYaw);
  const ex = s * R * .36 + fx, ey = -R * .12 + fy, rx = R * .2 * (1 - .3 * far), ry = R * .26;
  const lid = clamp(st.lid + (s < 0 ? st.lidL || 0 : st.lidR || 0) + st.blinkAmt * (1 - st.lid) + st.squint * .25, -.25, 1);
  const lowR = clamp(st.squint * .45 + Math.max(0, st.smile) * .3, 0, .8);
  const wide = 1 + Math.max(0, -st.lid) * .6;
  ctx.save(); ctx.translate(ex, ey);
  const eye = new Path2D(); eye.ellipse(0, 0, rx * wide, ry * wide, 0, 0, TAU);
  ctx.fillStyle = '#ffffff'; ctx.fill(eye);
  ctx.save(); ctx.clip(eye);
  const gx = clamp(st.gaze[0] - st.headYaw * .25, -1, 1), gy = clamp(st.gaze[1], -1, 1);
  const px = gx * rx * .5, py = gy * ry * .45 + lid * 3, pr = rx * .62;
  ctx.fillStyle = INK; ctx.beginPath(); ctx.ellipse(px, py, pr * (1 - .2 * far), pr * 1.05, 0, 0, TAU); ctx.fill();
  ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(px - pr * .35, py - pr * .4, pr * .3 + st.tearful * 2, 0, TAU); ctx.fill();
  if (st.tearful > .05) { ctx.fillStyle = `rgba(140,190,255,${.5 * st.tearful})`; ctx.fillRect(-rx * 2, ry * .45 * wide, rx * 4, ry); }
  // upper lid drops from the top, lower lid rises
  const top = -ry * wide - 2, lidY = lerp(top, ry * wide, lid);
  ctx.fillStyle = C.face || PAPER; ctx.fillRect(-rx * 2, top - 4, rx * 4, lidY - top + 4);
  ctx.fillStyle = alpha(C.skin, .28); ctx.fillRect(-rx * 2, top - 4, rx * 4, lidY - top + 4);
  const lowY = lerp(ry * wide + 2, 0, lowR);
  ctx.fillStyle = C.face || PAPER; ctx.fillRect(-rx * 2, lowY, rx * 4, ry * 2);
  ctx.fillStyle = alpha(C.skin, .28); ctx.fillRect(-rx * 2, lowY, rx * 4, ry * 2);
  ctx.restore();
  // outlines: eye rim and the lid edge
  ctx.strokeStyle = INK; ctx.lineWidth = 3.5; ctx.stroke(eye);
  if (lid > .02) { ctx.lineWidth = 4.5; ctx.beginPath(); const hw = rx * wide * Math.sqrt(Math.max(0, 1 - (lidY / (ry * wide)) ** 2)); ctx.moveTo(-hw - 1, lidY); ctx.lineTo(hw + 1, lidY); ctx.stroke(); }
  if (lowR > .05) { ctx.lineWidth = 3.5; ctx.beginPath(); const hw = rx * wide * Math.sqrt(Math.max(0, 1 - (lowY / (ry * wide)) ** 2)); ctx.moveTo(-hw, lowY); ctx.lineTo(hw, lowY); ctx.stroke(); }
  if (C.lashes) { ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(s * rx * .7, lidY - 2); ctx.lineTo(s * rx * 1.2, lidY - 9); ctx.stroke(); }
  ctx.restore();
}
function stickMouth(ctx, C, st, R, fx, fy) {
  const mx = fx * 1.1, my = R * .48 + fy;
  const o = clamp(st.open, 0, 1), sm = st.smile, rd = clamp(st.round, 0, 1);
  const hw = R * .3 * (1 + Math.max(0, sm) * .35 + st.wide * .2 - rd * .45);
  const cy = -sm * 12 - st.sneer * 4, h = o * R * .42 * (1 + rd * .2);
  ctx.save(); ctx.translate(mx, my); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (h > 3) {
    const p = new Path2D(); p.moveTo(-hw, cy); p.bezierCurveTo(-hw * .5, -4 + sm * -2, hw * .5, -4 + sm * -2, hw, cy); p.bezierCurveTo(hw * .55, h + cy * .3 + 6, -hw * .55, h + cy * .3 + 6, -hw, cy); p.closePath();
    ctx.fillStyle = '#5a1a20'; ctx.fill(p);
    ctx.save(); ctx.clip(p); ctx.fillStyle = '#e56a72'; ctx.beginPath(); ctx.ellipse(0, h + 4, hw * .6, h * .45, 0, 0, TAU); ctx.fill(); if (sm > .2) { ctx.fillStyle = '#fff'; ctx.fillRect(-hw, -8, hw * 2, 8); } ctx.restore();
    ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke(p);
  } else {
    ctx.strokeStyle = INK; ctx.lineWidth = 5.5; ctx.beginPath(); ctx.moveTo(-hw, cy); ctx.quadraticCurveTo(0, -cy * .9 + 2, hw, cy); ctx.stroke();
  }
  ctx.restore();
}
function stickHair(ctx, C, st, R, fx) {
  const sty = C.hairStyle, col = C.hair, X = x => x + fx * .5;
  ctx.save(); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineCap = 'round'; ctx.lineWidth = 7;
  const tuft = (pts) => { ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(X(p[0]), p[1]) : ctx.moveTo(X(p[0]), p[1])); ctx.stroke(); };
  if (C.headwear && C.headwear.type === 'veil') { ctx.fillStyle = C.headwear.color; ctx.beginPath(); ctx.arc(X(0), 0, R + 6, Math.PI * 1.02, Math.PI * 1.98); ctx.quadraticCurveTo(X(0), -R * .55, -R - 6 + fx * .5, -4); ctx.fill(); }
  else if (sty === 'curly' || sty === 'afro') { const n = sty === 'afro' ? 11 : 8, rr = sty === 'afro' ? R * 1.12 : R * .98; for (let i = 0; i < n; i++) { const a = Math.PI * (1.08 + .84 * i / (n - 1)); ctx.beginPath(); ctx.arc(X(Math.cos(a) * rr), Math.sin(a) * rr, sty === 'afro' ? 16 : 11, 0, TAU); ctx.fill(); } }
  else if (sty === 'bald') { tuft([[-R * .95, -R * .2], [-R * 1.05, -R * .5]]); tuft([[R * .95, -R * .2], [R * 1.05, -R * .5]]); }
  else if (sty === 'roman' || sty === 'short') { ctx.beginPath(); ctx.arc(X(0), 0, R + 1, Math.PI * 1.1, Math.PI * 1.9); ctx.lineWidth = 12; ctx.stroke(); ctx.lineWidth = 6; for (let i = 0; i < 5; i++) tuft([[-R * .5 + i * R * .25, -R * .92], [-R * .58 + i * R * .25, -R * .72]]); if (C.gray) { ctx.strokeStyle = '#c8c4bc'; ctx.lineWidth = 6; tuft([[-R * .95, -R * .3], [-R * .85, -R * .6]]); tuft([[R * .95, -R * .3], [R * .85, -R * .6]]); } }
  else if (sty === 'wavy') { ctx.lineWidth = 10; ctx.beginPath(); ctx.arc(X(0), 0, R + 2, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke(); ctx.lineWidth = 7; for (const s of [-1, 1]) tuft([[s * R * .95, -R * .3], [s * R * 1.12, R * .2], [s * R * 1.02, R * .55]]); }
  else if (sty === 'ponytail' || sty === 'bun') { ctx.lineWidth = 10; ctx.beginPath(); ctx.arc(X(0), 0, R + 1, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke(); if (sty === 'bun') { ctx.beginPath(); ctx.arc(X(0), -R - 14, 18, 0, TAU); ctx.fill(); } else { ctx.lineWidth = 9; tuft([[R * .8, -R * .7], [R * 1.25, -R * .2], [R * 1.15, R * .45]]); } }
  // officials: a little gold laurel
  if (C.cloth.type === 'toga') { ctx.strokeStyle = '#e8b830'; ctx.fillStyle = '#e8b830'; ctx.lineWidth = 3; for (const s of [-1, 1]) for (let i = 0; i < 4; i++) { const a = Math.PI * (1.5 + s * (.12 + i * .1)); ctx.beginPath(); ctx.ellipse(X(Math.cos(a) * (R + 4)), Math.sin(a) * (R + 4), 9, 4, a + Math.PI / 2, 0, TAU); ctx.fill(); } }
  ctx.restore();
}
