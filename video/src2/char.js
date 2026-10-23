// ---------- character rig ----------
// Units: scale-1 pixels, origin at the suprasternal notch (between collarbones).
// Arms/hands are named by SCREEN side: L = screen-left, R = screen-right.

function spline(ctx, pts, closed = true, k = .5) {
  const n = pts.length; if (n < 2) return;
  const P = i => closed ? pts[(i + n) % n] : pts[clamp(i, 0, n - 1)];
  ctx.moveTo(pts[0][0], pts[0][1]);
  const last = closed ? n : n - 1;
  for (let i = 0; i < last; i++) {
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) * k / 3, p1[1] + (p2[1] - p0[1]) * k / 3,
      p2[0] - (p3[0] - p1[0]) * k / 3, p2[1] - (p3[1] - p1[1]) * k / 3, p2[0], p2[1]);
  }
  if (closed) ctx.closePath();
}
function capsule(ctx, x1, y1, x2, y2, r1, r2) { // tapered limb between two circles
  const a = Math.atan2(y2 - y1, x2 - x1), d = Math.hypot(x2 - x1, y2 - y1);
  const s = Math.asin(clamp((r1 - r2) / Math.max(d, 1e-3), -1, 1));
  ctx.moveTo(x1 + Math.cos(a + Math.PI / 2 + s) * r1, y1 + Math.sin(a + Math.PI / 2 + s) * r1);
  ctx.arc(x1, y1, r1, a + Math.PI / 2 + s, a + 3 * Math.PI / 2 - s);
  ctx.arc(x2, y2, r2, a - Math.PI / 2 - s, a + Math.PI / 2 + s);
  ctx.closePath();
}
function softStroke(ctx, path, color, w, a) { // a soft-edged line (no hard outlines)
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.strokeStyle = alpha(color, a * .35); ctx.lineWidth = w * 2.2; ctx.stroke(path);
  ctx.strokeStyle = alpha(color, a * .6); ctx.lineWidth = w; ctx.stroke(path);
  ctx.restore();
}
function P2(fn) { const p = new Path2D(); fn(p); return p; }

// ---------- hands ----------
const HAND_POSES = {
  relax: { c: [.35, .42, .48, .55], sp: .05, th: .55, tc: .2 },
  open: { c: [.04, .05, .08, .12], sp: .16, th: 1.0, tc: 0 },
  grip: { c: [.9, .92, .95, .95], sp: 0, th: .25, tc: .55 },
  point: { c: [0, .92, .95, .95], sp: .02, th: .3, tc: .5 },
  pen: { c: [.42, .62, .78, .85], sp: .02, th: .35, tc: .3 },
  hold: { c: [.22, .28, .32, .38], sp: .03, th: .5, tc: .1 },
  flat: { c: [.06, .08, .1, .14], sp: .05, th: .7, tc: 0 },
  cup: { c: [.3, .32, .35, .4], sp: .06, th: .8, tc: .15 },
};
// draws a hand; wrist at (0,0) pointing +x. flip=1 means thumb on +y side.
// layer: 'back' (palm+fingers) or 'front' (thumb) or 'all'
function drawHand(ctx, C, pose, flip, layer = 'all', fore = 1) {
  const P = typeof pose === 'string' ? HAND_POSES[pose] : pose;
  const skin = C.skin, line = shade(C.skin, -.38);
  const fingers = [[-15, 40, 11], [-4.5, 44, 11.5], [6, 41, 11], [15.5, 32, 9.5]]; // y, len, width (index first, nearest thumb)
  const shapes = [], front = [];
  // palm
  const palm = P2(p => { spline(p, [[-2, -14], [24, -20], [50, -20], [54, -6], [53, 8], [50, 21], [26, 23], [-2, 16]], true, .6); });
  const doPalm = layer === 'all' || layer === 'back' || layer === 'palm', doFing = layer === 'all' || layer === 'back' || layer === 'fingers', doThumb = layer === 'all' || layer === 'front' || layer === 'palm';
  if (doPalm) shapes.push(palm);
  if (doFing) fingers.forEach((f, i) => {
    const curl = P.c[i], y0 = f[0] * -flip + 0, L = f[1] * fore;
    const spread = (i - 1.5) * P.sp * -flip;
    const a1 = spread + curl * .55 * flip * 0, sh = 1 - .5 * curl;
    const bx = 50, by = y0 * 1;
    const x1 = bx + Math.cos(a1) * L * .55 * sh, y1 = by + Math.sin(a1) * L * .55 * sh;
    const a2 = a1 + curl * .6 * (i < 2 ? 1 : 1) * 0.0;
    const x2 = x1 + Math.cos(a2) * L * .45 * (1 - .75 * curl), y2 = y1 + Math.sin(a2) * L * .45 * (1 - .75 * curl);
    shapes.push(P2(p => { capsule(p, bx - 4, by, x1, y1, f[2] / 2, f[2] / 2 * .92); }));
    shapes.push(P2(p => { capsule(p, x1, y1, x2, y2, f[2] / 2 * .92, f[2] / 2 * .8); }));
  });
  const thumb = [];
  if (doThumb) {
    const ta = (.55 + P.th * .55) * -flip * -1; // angle away from palm on thumb side
    const bx = 14, by = 15 * flip;
    const ang = flip * (.35 + P.th * .6) - P.tc * flip * .9;
    const x1 = bx + Math.cos(ang) * 24, y1 = by + Math.sin(ang) * 24;
    const ang2 = ang - flip * (.25 + P.tc * .9);
    const x2 = x1 + Math.cos(ang2) * 20, y2 = y1 + Math.sin(ang2) * 20;
    thumb.push(P2(p => capsule(p, bx, by, x1, y1, 8.5, 6.8)));
    thumb.push(P2(p => capsule(p, x1, y1, x2, y2, 6.8, 5.4)));
    thumb.nail = [x2 - Math.cos(ang2) * 3, y2 - Math.sin(ang2) * 3, ang2];
  }
  const all = shapes.concat(thumb);
  ctx.save(); ctx.lineJoin = 'round';
  // outline pass then fill pass so interior joins vanish
  ctx.strokeStyle = line; ctx.lineWidth = 2.6;
  for (const s of shapes) ctx.stroke(s);
  ctx.fillStyle = skin; for (const s of shapes) ctx.fill(s);
  if (doFing) {
    // soft finger separations blending into skin
    ctx.globalAlpha = .22; ctx.strokeStyle = line; ctx.lineWidth = 1.4; ctx.lineCap = 'round';
    [-10, 0.8, 11].forEach(y => { ctx.beginPath(); ctx.moveTo(50, y * -flip); ctx.lineTo(58 + (1 - P.c[1]) * 10, y * -flip); ctx.stroke(); });
    ctx.globalAlpha = .12; ctx.fillStyle = shade(skin, .5);
    ctx.beginPath(); ctx.ellipse(32, -2 * flip, 14, 8, 0, 0, TAU); ctx.fill();
    ctx.globalAlpha = 1;
  }
  if (thumb.length) {
    ctx.strokeStyle = line; ctx.lineWidth = 2.6; for (const s of thumb) ctx.stroke(s);
    ctx.fillStyle = skin; for (const s of thumb) ctx.fill(s);
    const [nx, ny, na] = thumb.nail; ctx.fillStyle = shade(skin, .35, .7); ctx.beginPath(); ctx.ellipse(nx, ny, 3.6, 2.8, na, 0, TAU); ctx.fill();
      }
  ctx.restore();
}

// ---------- props held in hands ----------
function drawProp(ctx, kind, C, t) {
  if (kind === 'phone') {
    ctx.save(); ctx.rotate(-Math.PI / 2);
    ctx.fillStyle = '#16161c'; roundRect(ctx, -26, -6, 52, 100, 9); ctx.fill();
    const g = ctx.createLinearGradient(0, 0, 0, 92); g.addColorStop(0, '#9fd2ff'); g.addColorStop(1, '#5a86d6');
    ctx.fillStyle = g; roundRect(ctx, -22, -2, 44, 92, 6); ctx.fill();
    ctx.restore();
  } else if (kind === 'phoneBack') { // viewer sees the back of the phone; screen faces the holder
    const m = ctx.getTransform(), rot = Math.atan2(m.b, m.a);
    ctx.save(); ctx.translate(30, 0); ctx.rotate(-rot - .12);
    ctx.fillStyle = '#1b1d22'; roundRect(ctx, -27, -82, 54, 104, 9); ctx.fill();
    ctx.strokeStyle = 'rgba(140,190,255,.6)'; ctx.lineWidth = 2.5; roundRect(ctx, -27, -82, 54, 104, 9); ctx.stroke();
    ctx.fillStyle = '#30343c'; roundRect(ctx, -20, -75, 20, 22, 5); ctx.fill();
    ctx.fillStyle = '#0a0b0d'; ctx.beginPath(); ctx.arc(-10, -64, 5.5, 0, TAU); ctx.fill();
    ctx.restore();
  } else if (kind === 'stylus') {
    ctx.save(); ctx.strokeStyle = '#6b4a2a'; ctx.lineWidth = 4; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(30, 34); ctx.lineTo(96, -14); ctx.stroke();
    ctx.strokeStyle = '#2a1a10'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(30, 34); ctx.lineTo(22, 40); ctx.stroke();
    ctx.restore();
  }
}
function roundRect(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }

// ---------- state resolution ----------
const BASE_STATE = {
  x: 360, y: 700, s: 1, lean: 0, turn: 0, headYaw: 0, headPitch: 0, headRoll: 0, headX: 0,
  look: null, gaze: [0, 0], follow: .65, lid: .12, squint: 0, browIn: 0, browOut: 0, browY: 0, browL: 0, browR: 0, frown: 0,
  smile: 0, wide: 0, round: 0, open: 0, jaw: 0, sneer: 0,
  armL: [-70, 200], armR: [70, 200], handL: 'relax', handR: 'relax', angL: 0, angR: 0, foreL: 1, foreR: 1, holdL: null, holdR: null,
  elbowL: 1, elbowR: 1, armsBehind: false,
  breathe: 1, sway: 1, idle: 1, gest: 1, shrug: 0, tearful: 0, tears: [], blink: 1, nod: 1, alpha: 1, visible: 1,
};
function blinkAt(C, t) {
  if (!C._blinks) { const r = rng(C.seed * 991 + 7); const b = []; let x = r() * 2; while (x < 400) { b.push(x); x += 2.2 + r() * 3.4; if (r() < .12) { b.push(x); x += .35; } } C._blinks = b; }
  for (const b of C._blinks) { if (b > t) break; const d = t - b; if (d < .07) return d / .07; if (d < .1) return 1; if (d < .24) return 1 - (d - .1) / .14; }
  return 0;
}
function resolve(C, track, t) {
  const st = track.get(t);
  const seed = C.seed || 1;
  // speaking -> mouth + micro head motion
  const sp = speakAmt(C.voice, t);
  st.talk = 0;
  if (sp) {
    const o = Math.pow(sp.open, .8);
    st.talk = o;
    const w = sp.word.toLowerCase();
    const rnd = /[ouw]/.test(w) ? .5 : 0, wid = /[ei]/.test(w) ? .3 : 0;
    st.open = Math.max(st.open, o * .9);
    st.round = lerp(st.round, rnd, o); st.wide += wid * o;
    st.headPitch += (noise1(t * 3.1 + seed) * .05 + o * .04) * st.nod;
    st.headRoll += noise1(t * 1.7 + seed * 3) * .025 * st.nod;
    st.browIn += Math.max(0, noise1(t * 2.3 + seed)) * .25 * o * st.gest;
    st.armR = [st.armR[0] + noise1(t * 1.9 + seed) * 6 * st.gest, st.armR[1] - o * 6 * st.gest];
    st.armL = [st.armL[0] + noise1(t * 1.6 + seed + 4) * 5 * st.gest, st.armL[1] - o * 4 * st.gest];
  }
  // idle life
  const id = st.idle;
  st.headYaw += noise1(t * .37 + seed * 11) * .05 * id;
  st.headPitch += noise1(t * .29 + seed * 7) * .03 * id;
  st.headRoll += noise1(t * .23 + seed * 5) * .03 * id;
  st.swayX = noise1(t * .21 + seed * 2) * 3 * st.sway;
  st.br = Math.sin(t * TAU / (3.6 + (seed % 3) * .4) + seed) * st.breathe; // breathing -1..1
  st.armL = [st.armL[0] + noise1(t * .5 + seed * 9) * 2.5 * id, st.armL[1] + st.br * 1.5 + noise1(t * .4 + seed) * 2 * id];
  st.armR = [st.armR[0] + noise1(t * .45 + seed * 13) * 2.5 * id, st.armR[1] + st.br * 1.5 + noise1(t * .43 + seed * 2) * 2 * id];
  // look target -> head + eyes
  if (st.look) {
    let lx, ly;
    if (st.look === 'cam') { lx = st.x; ly = st.y - 110 * st.s; }
    else { lx = st.look[0]; ly = st.look[1]; }
    const hx = st.x, hy = st.y - 110 * st.s;
    const dx = (lx - hx) / Math.max(st.s, .3), dy = (ly - hy) / Math.max(st.s, .3);
    const yawT = clamp(dx / 420, -1, 1), pitT = clamp(dy / 520, -1, 1);
    st.headYaw += yawT * st.follow; st.headPitch += pitT * st.follow * .7;
    st.gaze = [clamp(yawT * (1 - st.follow) * 2.2 + st.gaze[0], -1, 1), clamp(pitT * (1 - st.follow * .7) * 2.2 + st.gaze[1], -1, 1)];
  }
  // tiny saccades
  st.gaze = [st.gaze[0] + (Math.round(noise1(t * .8 + seed * 31) * 2) / 2) * .05 * id, st.gaze[1] + (Math.round(noise1(t * .7 + seed * 17) * 2) / 2) * .04 * id];
  // blink
  st.blinkAmt = blinkAt(C, t) * st.blink;
  return st;
}

// ---------- drawing ----------
function drawChar(ctx, C, st, t) {
  ctx.save();
  ctx.translate(st.x + st.swayX * st.s, st.y);
  ctx.scale(st.s, st.s);
  ctx.rotate(st.lean);
  ctx.translate(0, -st.br * 1.2 - st.shrug * 6);
  const bw = (C.build || 1) * (C.child ? .78 : 1);
  const shW = 112 * bw, turn = st.turn;
  const shL = [-shW * (1 - .18 * Math.max(0, turn)) + turn * 10, 22 - st.shrug * 6];
  const shR = [shW * (1 - .18 * Math.max(0, -turn)) + turn * 10, 22 - st.shrug * 6];
  const neckTop = [st.headX + turn * 6, C.child ? -26 : -36];

  // hood / back hair behind everything
  if (C.cloth.type === 'hoodie') drawHoodBack(ctx, C, st, shL, shR);
  drawBackHair(ctx, C, st, neckTop);
  // arms behind body?
  const arms = armGeom(C, st, shL, shR, bw);
  if (st.armsBehind) { drawArm(ctx, C, st, arms.L, 'upper'); drawArm(ctx, C, st, arms.R, 'upper'); drawArm(ctx, C, st, arms.L, 'lower'); drawArm(ctx, C, st, arms.R, 'lower'); }
  drawNeck(ctx, C, st, neckTop);
  drawTorso(ctx, C, st, shL, shR, bw);
  if (!st.armsBehind) { drawArm(ctx, C, st, arms.L, 'upper'); drawArm(ctx, C, st, arms.R, 'upper'); }
  if (C.mantle) drawMantle(ctx, C, st, shL, shR, bw);
  // head
  ctx.save(); ctx.translate(neckTop[0], neckTop[1]); ctx.rotate(st.headRoll);
  drawHead(ctx, C, st, t);
  ctx.restore();
  if (C.cloth.type === 'hoodie') drawHoodStrings(ctx, C, st);
  if (!st.armsBehind) {
    drawArm(ctx, C, st, arms.L, 'lower', 'back'); drawArm(ctx, C, st, arms.R, 'lower', 'back');
    if (st.mid) st.mid(ctx, arms);
    drawArm(ctx, C, st, arms.L, 'hand-front'); drawArm(ctx, C, st, arms.R, 'hand-front');
  }
  if (st.top) st.top(ctx, arms);
  ctx.restore();
}

function armGeom(C, st, shL, shR, bw) {
  const k = C.child ? .74 : 1; let a = 150 * k, b = 132 * k;
  const mk = (sh, tgt, side, eb) => { let a = 150 * k, b = 132 * k;
    const sx = sh[0] + side * -8, sy = sh[1] + 14;
    const dx = tgt[0] - sx, dy = tgt[1] - sy; const d = Math.hypot(dx, dy);
    // preferred relaxed elbow: hanging beside the torso, slightly outward
    const E0 = [sx + side * (10 + 8 * eb), sy + a * .96];
    const d1 = Math.hypot(tgt[0] - E0[0], tgt[1] - E0[1]);
    let ex, ey;
    if (d1 <= b) { ex = E0[0]; ey = E0[1]; } // forearm points toward camera: foreshortened
    else {
      const dd = clamp(d, 30, a + b - 1), ang = Math.atan2(dy, dx);
      const A = Math.acos(clamp((a * a + dd * dd - b * b) / (2 * a * dd), -1, 1));
      const c1 = [sx + Math.cos(ang + A) * a, sy + Math.sin(ang + A) * a], c2 = [sx + Math.cos(ang - A) * a, sy + Math.sin(ang - A) * a];
      const score = c => Math.hypot(c[0] - E0[0], c[1] - E0[1]) - side * c[0] * .15 * eb;
      [ex, ey] = score(c1) < score(c2) ? c1 : c2;
    }
    let wx = tgt[0], wy = tgt[1];
    const fd = Math.hypot(wx - ex, wy - ey); if (fd > b) { wx = ex + (wx - ex) / fd * b; wy = ey + (wy - ey) / fd * b; }
    return { s: [sx, sy], e: [ex, ey], w: [wx, wy], side };
  };
  const L = mk(shL, st.armL, -1, st.elbowL), R = mk(shR, st.armR, 1, st.elbowR);
  L.pose = st.handL; R.pose = st.handR; L.ang = st.angL; R.ang = st.angR; L.hold = st.holdL; R.hold = st.holdR; L.fore = st.foreL; R.fore = st.foreR;
  return { L, R };
}
function drawArm(ctx, C, st, A, part, layer) {
  const cl = C.cloth, sleeveCol = cl.sleeve || cl.color, k = C.child ? .74 : 1;
  const [sx, sy] = A.s, [ex, ey] = A.e, [wx, wy] = A.w;
  if (part === 'upper') {
    ctx.save();
    const g = ctx.createLinearGradient(sx - 20, sy, sx + 20, sy);
    ctx.fillStyle = sleeveCol;
    const p = P2(p => capsule(p, sx, sy, ex, ey, 25 * k, 19 * k));
    if (cl.sleeveLen === 'short') { // bare upper arm partially
      ctx.fillStyle = C.skin; ctx.fill(P2(p => capsule(p, sx, sy, ex, ey, 21 * k, 16 * k)));
      const mx = lerp(sx, ex, .45), my = lerp(sy, ey, .45);
      ctx.fillStyle = sleeveCol; ctx.fill(P2(p => capsule(p, sx, sy, mx, my, 25 * k, 22 * k)));
    } else ctx.fill(p);
    // soft shading along arm
    ctx.globalAlpha = .18; ctx.strokeStyle = shade(sleeveCol, -.6); ctx.lineWidth = 8 * k; ctx.lineCap = 'round';
    const nx = (ey - sy), ny = -(ex - sx), nl = Math.hypot(nx, ny) || 1;
    ctx.beginPath(); ctx.moveTo(sx + nx / nl * 14 * A.side, sy + ny / nl * 14 * A.side); ctx.lineTo(ex + nx / nl * 10 * A.side, ey + ny / nl * 10 * A.side); ctx.stroke();
    ctx.restore();
    return;
  }
  const fa = Math.atan2(wy - ey, wx - ex);
  if (part === 'lower') {
    const sl = cl.sleeveLen === 'long' ? .9 : cl.sleeveLen === 'short' ? 0 : .5;
    const cx = lerp(ex, wx, sl), cy = lerp(ey, wy, sl);
    ctx.save();
    // forearm skin (drawn first; the sleeve tube covers its upper part)
    ctx.fillStyle = C.skin;
    ctx.fill(P2(p => capsule(p, lerp(ex, wx, Math.max(0, sl - .05)), lerp(ey, wy, Math.max(0, sl - .05)), wx, wy, 15 * k, 12 * k)));
    if (cl.sleeveLen === 'short') { ctx.fill(P2(p => capsule(p, ex, ey, wx, wy, 17 * k, 12 * k))); }
    if (sl > 0) {
      ctx.fillStyle = sleeveCol;
      ctx.fill(P2(p => capsule(p, ex, ey, cx, cy, 20 * k, 19 * k)));
      // cuff opening: dark interior then the wrist emerging from inside it
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(fa);
      ctx.fillStyle = shade(sleeveCol, -.55); ctx.beginPath(); ctx.ellipse(0, 0, 5 * k, 19 * k, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = C.skin; ctx.beginPath(); ctx.ellipse(1.5 * k, 0, 4.2 * k, 14 * k, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = C.skin; ctx.fill(P2(p => capsule(p, 1, 0, Math.hypot(wx - cx, wy - cy), 0, 14 * k, 12 * k)));
      // cuff rim highlight
      ctx.strokeStyle = shade(sleeveCol, .18); ctx.lineWidth = 3 * k; ctx.beginPath(); ctx.ellipse(-1, 0, 5 * k, 19.5 * k, 0, -Math.PI / 2, Math.PI / 2, true); ctx.stroke();
      ctx.restore();
      // fold at elbow
      ctx.globalAlpha = .25; ctx.strokeStyle = shade(sleeveCol, -.5); ctx.lineWidth = 3 * k; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(ex - 6, ey - 4); ctx.quadraticCurveTo(ex + 4, ey + 2, ex + 10 * Math.cos(fa), ey + 10 * Math.sin(fa) + 2); ctx.stroke();
      ctx.globalAlpha = 1;
    }
    ctx.restore();
    if (layer === 'back') { // palm + fingers (behind held props)
      ctx.save(); ctx.translate(wx, wy); ctx.rotate(fa + (A.ang || 0)); ctx.scale(k, k);
      const flip = A.side < 0 ? 1 : -1;
      if (A.hold === 'phoneBack') { drawHand(ctx, C, A.pose, flip, 'palm', A.fore || 1); drawProp(ctx, A.hold, C); drawHand(ctx, C, A.pose, flip, 'fingers', A.fore || 1); }
      else { drawHand(ctx, C, A.pose, flip * (A.flipT || 1), 'back', A.fore || 1); if (A.hold) drawProp(ctx, A.hold, C); }
      ctx.restore();
    }
    return;
  }
  if (part === 'hand-front') {
    ctx.save(); ctx.translate(wx, wy); ctx.rotate(fa + (A.ang || 0)); ctx.scale(k, k);
    const flip = A.side < 0 ? 1 : -1;
    if (A.hold !== 'phoneBack') drawHand(ctx, C, A.pose, flip, 'front', A.fore || 1);
    ctx.restore();
  }
}

function drawNeck(ctx, C, st, nt) {
  const k = C.child ? .8 : 1;
  ctx.save();
  const p = P2(p => {
    p.moveTo(-30 * k, 40); p.quadraticCurveTo(-24 * k + nt[0] * .3, nt[1] * .5, -23 * k + nt[0], nt[1] - 30);
    p.lineTo(23 * k + nt[0], nt[1] - 30); p.quadraticCurveTo(24 * k + nt[0] * .3, nt[1] * .5, 30 * k, 40); p.closePath();
  });
  ctx.fillStyle = C.skin; ctx.fill(p);
  // shadow under the jaw
  const g = ctx.createLinearGradient(0, nt[1] - 6, 0, nt[1] + 22);
  g.addColorStop(0, shade(C.skin, -.45, .55)); g.addColorStop(1, shade(C.skin, -.45, 0));
  ctx.fillStyle = g; ctx.fill(p);
  // sternocleidomastoids: subtle V from behind each ear down to the notch
  ctx.clip(p);
  const yaw = st.headYaw;
  for (const s of [-1, 1]) {
    const path = P2(q => { q.moveTo(s * 22 * k + nt[0] + yaw * 5, nt[1] - 4); q.quadraticCurveTo(s * 14 * k + nt[0] * .5, nt[1] * .45, s * 4, 2); });
    softStroke(ctx, path, shade(C.skin, -.45), 2.6, .2);
    const hl = P2(q => { q.moveTo(s * 17 * k + nt[0] + yaw * 5, nt[1] - 2); q.quadraticCurveTo(s * 9 * k + nt[0] * .5, nt[1] * .45, s * 1.5, 1); });
    softStroke(ctx, hl, shade(C.skin, .3), 2, .12);
  }
  ctx.restore();
}

function drawTorso(ctx, C, st, shL, shR, bw) {
  const cl = C.cloth, col = cl.color, k = C.child ? .8 : 1;
  const h = 330;
  ctx.save();
  const body = P2(p => spline(p, [[-28 * k, 4], [shL[0] * .55, 6], [shL[0] + 6, shL[1] + 2], [shL[0] - 6, shL[1] + 40], [shL[0] + 2, 150], [shL[0] * .86, h], [shR[0] * .86, h], [shR[0] + 2, 150], [shR[0] + 6, shR[1] + 40], [shR[0] - 6, shR[1] + 2], [shR[0] * .55, 6], [28 * k, 4], [0, 12 + (cl.neck || 0)]], true, .55));
  const g = ctx.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, shade(col, .06)); g.addColorStop(1, shade(col, -.25));
  ctx.fillStyle = g; ctx.fill(body);
  ctx.save(); ctx.clip(body);
  // soft shoulder shading (gradient, no hard lines)
  for (const s of [shL, shR]) {
    const rg = ctx.createRadialGradient(s[0] * 1.05, s[1] + 70, 5, s[0] * 1.05, s[1] + 70, 70);
    rg.addColorStop(0, shade(col, -.35, .35)); rg.addColorStop(1, shade(col, -.35, 0));
    ctx.fillStyle = rg; ctx.fillRect(s[0] - 80, s[1] - 10, 160, 170);
  }
  // neckline
  const nd = cl.neck || 0;
  if (cl.type === 'hoodie') {
    ctx.strokeStyle = shade(col, -.3); ctx.lineWidth = 9; ctx.beginPath(); ctx.ellipse(0, 0, 33, 16, 0, 0, Math.PI); ctx.stroke();
    ctx.strokeStyle = shade(col, .12); ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(0, 3, 33, 15, 0, .2, Math.PI - .2); ctx.stroke();
    // pocket hint + folds
    softStroke(ctx, P2(p => { p.moveTo(-70, 250); p.quadraticCurveTo(0, 236, 70, 250); }), shade(col, -.6), 3, .35);
  } else {
    // collarbones (tunic necklines show a little)
    if (nd > 6) for (const s of [-1, 1]) softStroke(ctx, P2(p => { p.moveTo(s * 6, 7); p.quadraticCurveTo(s * 26, 2, s * 50, 5); }), shade(C.skin, -.45), 2, .35);
    ctx.fillStyle = C.skin;
    ctx.beginPath(); ctx.moveTo(-30 * k, 0); ctx.quadraticCurveTo(0, 14 + nd * 1.6, 30 * k, 0); ctx.lineTo(28 * k, -6); ctx.lineTo(-28 * k, -6); ctx.fill();
    if (nd > 6) for (const s of [-1, 1]) softStroke(ctx, P2(p => { p.moveTo(s * 6, 7); p.quadraticCurveTo(s * 18, 4, s * 28, 6); }), shade(C.skin, -.45), 2, .3);
    ctx.strokeStyle = cl.trim || shade(col, -.25); ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(-32 * k, -1); ctx.quadraticCurveTo(0, 15 + nd * 1.6, 32 * k, -1); ctx.stroke();
  }
  if (cl.type === 'tunic' || cl.type === 'toga' || cl.type === 'dress') {
    // vertical folds
    for (const [x, a] of [[-50, .28], [-18, .2], [22, .22], [56, .26]]) softStroke(ctx, P2(p => { p.moveTo(x, 70); p.quadraticCurveTo(x + 8, 190, x - 4, 330); }), shade(col, -.55), 3, a);
    if (cl.stripe) for (const s of [-1, 1]) { ctx.fillStyle = cl.stripe; ctx.beginPath(); ctx.moveTo(s * 52, 8); ctx.lineTo(s * 60, 8); ctx.lineTo(s * 54, 330); ctx.lineTo(s * 47, 330); ctx.fill(); }
    if (cl.belt) { ctx.fillStyle = cl.belt; ctx.fillRect(-140, 236, 280, 14); ctx.fillStyle = shade(cl.belt, .3); ctx.fillRect(-140, 236, 280, 3); }
  }
  if (cl.type === 'armor') {
    // segmented chest plates over red tunic
    for (let i = 0; i < 5; i++) {
      const y = 70 + i * 34;
      const pg = ctx.createLinearGradient(0, y, 0, y + 32); pg.addColorStop(0, '#c9ccd2'); pg.addColorStop(.5, '#8d929b'); pg.addColorStop(1, '#5b6068');
      ctx.fillStyle = pg; ctx.beginPath(); ctx.moveTo(-104, y); ctx.quadraticCurveTo(0, y + 10, 104, y); ctx.lineTo(102, y + 30); ctx.quadraticCurveTo(0, y + 40, -102, y + 30); ctx.fill();
    }
    ctx.fillStyle = '#7a5530'; ctx.fillRect(-12, 20, 10, 60); ctx.fillRect(4, 20, 10, 60);
  }
  ctx.restore();
  ctx.restore();
}
function drawHoodBack(ctx, C, st, shL, shR) {
  const col = C.cloth.color;
  ctx.save(); ctx.fillStyle = shade(col, -.18);
  ctx.beginPath(); spline(ctx, [[-70, 10], [-58, -30], [-30, -46], [0, -50], [30, -46], [58, -30], [70, 10], [40, 4], [0, 0], [-40, 4]], true, .6); ctx.fill();
  for (const sx of [-1, 1]) softStroke(ctx, P2(p => { p.moveTo(sx * 60, 0); p.quadraticCurveTo(sx * 48, -34, sx * 18, -44); }), shade(col, -.6), 3, .35);
  softStroke(ctx, P2(p => { p.moveTo(-40, -30); p.quadraticCurveTo(0, -46, 40, -30); }), shade(col, .3), 3, .25);
  ctx.restore();
}
function drawHoodStrings(ctx, C, st) {
  ctx.save(); ctx.strokeStyle = '#d9d4c8'; ctx.lineWidth = 3.4; ctx.lineCap = 'round';
  for (const s of [-1, 1]) { const sw = noise1(st.br * .3 + s) * 2; ctx.beginPath(); ctx.moveTo(s * 14, 12); ctx.quadraticCurveTo(s * 15 + sw, 50, s * 13 + sw, 84); ctx.stroke(); ctx.fillStyle = '#bbb4a6'; ctx.fillRect(s * 13 + sw - 2.5, 82, 5, 9); }
  ctx.restore();
}
function drawMantle(ctx, C, st, shL, shR, bw) {
  const m = C.mantle, col = m.color;
  // cross-body drape from screen-right shoulder down to screen-left hip; the shoulder sits proud to hold it up
  ctx.save();
  const p = P2(p => spline(p, [[shR[0] * .35, 0], [shR[0] * .8, shR[1] - 12], [shR[0] + 16, shR[1] + 12], [shR[0] + 12, shR[1] + 70], [shR[0] * .4, 200], [shL[0] * .5, 340], [shL[0] * 1.02, 340], [shL[0] * .7, 250], [-20, 150], [shR[0] * .3, 40]], true, .5));
  const g = ctx.createLinearGradient(shR[0], 0, shL[0], 300); g.addColorStop(0, shade(col, .08)); g.addColorStop(1, shade(col, -.22));
  ctx.fillStyle = g; ctx.fill(p);
  ctx.save(); ctx.clip(p);
  if (m.tartan) { // plaid: crossing translucent bands
    ctx.save(); ctx.translate(shR[0], 0); ctx.rotate(.55);
    for (let k = -14; k < 14; k++) { ctx.fillStyle = alpha(m.tartan[k & 1], .45); ctx.fillRect(k * 26, -400, k % 3 === 0 ? 14 : 6, 900); ctx.fillRect(-400, k * 26, 900, k % 3 === 0 ? 14 : 6); }
    ctx.restore();
  }
  for (let i = 0; i < 4; i++) softStroke(ctx, P2(q => { q.moveTo(shR[0] * (.95 - i * .16), shR[1] + 10 + i * 22); q.quadraticCurveTo(shR[0] * .2 - i * 14, 170 + i * 10, shL[0] * (.5 + i * .12), 330); }), shade(col, -.5), 3, .16);
  softStroke(ctx, P2(q => { q.moveTo(shR[0] * .8, shR[1] - 6); q.quadraticCurveTo(shR[0] * .2, 120, shL[0] * .45, 300); }), shade(col, .5), 5, .12);
  ctx.restore();
  ctx.restore();
}

// ---------- head ----------
function faceOutline(C, st) {
  const fw = (C.faceW || 1) * (C.child ? .95 : 1), jw = C.jaw || 1, yaw = st.headYaw, o = st.open;
  const base = [[0, -74], [31, -68], [47, -45], [51, -14], [50, 8], [45 * jw, 31], [35 * jw, 49], [19 * jw, 60], [0, 65 * (C.chin || 1)]];
  const pts = [];
  const push = (x, y) => {
    let X = x * fw; if (X * yaw > 0) X *= 1 - .1 * Math.abs(yaw);
    X += yaw * 7; let Y = y; if (y > 30) Y += o * 8 * (y - 30) / 35;
    pts.push([X, Y]);
  };
  for (let i = 0; i < base.length; i++) push(base[i][0], base[i][1]);
  for (let i = base.length - 2; i > 0; i--) push(-base[i][0], base[i][1]);
  return pts;
}
function drawHead(ctx, C, st, t) {
  const yaw = st.headYaw, pit = st.headPitch;
  ctx.save();
  ctx.translate(0, -64 + pit * 6);
  const fo = faceOutline(C, st);
  const face = P2(p => spline(p, fo, true, .55));
  const fw = (C.faceW || 1);
  // far ear behind face, near ear in front
  for (const s of [-1, 1]) if (s * yaw > .15) drawEar(ctx, C, st, s, false);
  ctx.fillStyle = C.skin; ctx.fill(face);
  for (const s of [-1, 1]) if (s * yaw <= .15) drawEar(ctx, C, st, s, true);
  ctx.save(); ctx.clip(face);
  // face form shading: soft side shading + cheek warmth + chin shadow
  const sg = ctx.createLinearGradient(-60, 0, 60, 0);
  sg.addColorStop(0, shade(C.skin, -.3, .32 + Math.max(0, yaw) * .25)); sg.addColorStop(.3, shade(C.skin, 0, 0)); sg.addColorStop(.7, shade(C.skin, 0, 0)); sg.addColorStop(1, shade(C.skin, -.3, .32 + Math.max(0, -yaw) * .25));
  ctx.fillStyle = sg; ctx.fillRect(-70, -80, 140, 160);
  for (const s of [-1, 1]) {
    const cx = s * 30 * fw + yaw * 16, cy = 22;
    const rg = ctx.createRadialGradient(cx, cy, 2, cx, cy, 22); rg.addColorStop(0, `rgba(215,95,90,${.08 + Math.max(0, st.smile) * .05 + st.tearful * .1})`); rg.addColorStop(1, 'rgba(220,90,90,0)');
    ctx.fillStyle = rg; ctx.fillRect(cx - 24, cy - 24, 48, 48);
  }
  if (C.old) { // gentle age lines
    for (const s of [-1, 1]) softStroke(ctx, P2(p => { p.moveTo(s * 36 + yaw * 20, 2); p.quadraticCurveTo(s * 40 + yaw * 20, 8, s * 38 + yaw * 20, 14); }), shade(C.skin, -.5), 1.4, .25);
    softStroke(ctx, P2(p => { p.moveTo(-14 + yaw * 20, -34); p.quadraticCurveTo(yaw * 20, -36, 14 + yaw * 20, -34); }), shade(C.skin, -.45), 1.4, .2);
  }
  if (C.paint) { // woad-blue war paint band across the eyes, fading softly at its edges
    const py = -4 + st.headPitch * 9, g = ctx.createLinearGradient(0, py - 30, 0, py + 22);
    g.addColorStop(0, alpha(C.paint, 0)); g.addColorStop(.25, alpha(C.paint, .78)); g.addColorStop(.75, alpha(C.paint, .78)); g.addColorStop(1, alpha(C.paint, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-70, py - 30); ctx.lineTo(70, py - 22); ctx.lineTo(70, py + 22); ctx.lineTo(-70, py + 14); ctx.fill();
  }
  if (C.scar) softStroke(ctx, P2(p => { p.moveTo(28 + yaw * 18, -22); p.lineTo(36 + yaw * 18, 10); }), '#a0574a', 2, .5);
  if (C.stubble) { const sg2 = ctx.createRadialGradient(st.headYaw * 20, 62, 8, st.headYaw * 20, 52, 52); sg2.addColorStop(0, alpha(C.stubble, .2)); sg2.addColorStop(.6, alpha(C.stubble, .12)); sg2.addColorStop(1, alpha(C.stubble, 0)); ctx.fillStyle = sg2; ctx.fillRect(-60, 20, 120, 60); }
  ctx.restore();
  // features
  drawNose(ctx, C, st);
  for (const s of [-1, 1]) drawEye(ctx, C, st, s, t);
  if (C.beard) drawBeard(ctx, C, st);
  drawMouth(ctx, C, st);
  if (C.beard === 'full' || C.mustache) drawMustache(ctx, C, st);
  for (const s of [-1, 1]) drawBrow(ctx, C, st, s);
  drawTears(ctx, C, st, t);
  drawFrontHair(ctx, C, st, t);
  ctx.restore();
}
function drawEar(ctx, C, st, s, front) {
  const yaw = st.headYaw, fw = (C.faceW || 1);
  const x = s * 49 * fw + yaw * (front ? 12 : 4) - s * Math.abs(yaw) * (front ? 6 : 0), y = 8;
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = shade(C.skin, -.06);
  ctx.beginPath(); ctx.ellipse(s * 4, 0, 9, 17, s * .15, 0, TAU); ctx.fill();
  softStroke(ctx, P2(p => { p.moveTo(s * 2, -9); p.quadraticCurveTo(s * 9, -6, s * 7, 6); }), shade(C.skin, -.5), 1.6, .4);
  ctx.restore();
}
function eyeCenter(C, st, s) {
  const fw = (C.faceW || 1), yaw = st.headYaw;
  return [s * 21 * fw + yaw * 20 - s * Math.max(0, s * yaw) * 3, -4 + st.headPitch * 9 + (C.child ? 6 : 0)];
}
function drawEye(ctx, C, st, s, t) {
  const yaw = st.headYaw; const [ex, ey] = eyeCenter(C, st, s);
  const far = Math.max(0, s * yaw);
  const ew = 13.5 * (1 - .32 * far) * (C.child ? 1.08 : 1), eh = 7 * (C.child ? 1.15 : 1);
  const lid = clamp(st.lid + (s < 0 ? st.lidL || 0 : st.lidR || 0) + st.blinkAmt * (1 - st.lid) + st.squint * .25, -.2, 1);
  const lowR = clamp(st.squint * .5 + Math.max(0, st.smile) * .35, 0, 1);
  ctx.save(); ctx.translate(ex, ey);
  const inner = -s; // inner corner direction
  const up = -eh * 1.65, lo = eh * 1.1;
  const almond = P2(p => { p.moveTo(-ew, 0); p.bezierCurveTo(-ew * .5 + inner * 1, up, ew * .5 + inner * 1, up, ew, 0); p.bezierCurveTo(ew * .5, lo, -ew * .5, lo, -ew, 0); p.closePath(); });
  // socket shadow
  ctx.fillStyle = shade(C.skin, -.25, .35); ctx.beginPath(); ctx.ellipse(0, -3, ew * 1.45, eh * 2, 0, 0, TAU); ctx.fill();
  ctx.save(); ctx.clip(almond);
  ctx.fillStyle = '#efe7e1'; ctx.fillRect(-ew, -eh * 2, ew * 2, eh * 4);
  ctx.fillStyle = 'rgba(120,80,80,.25)'; ctx.fillRect(-ew, up * .6, ew * 2, 3);
  const gx = clamp(st.gaze[0] - yaw * .25, -1, 1), gy = clamp(st.gaze[1], -1, 1);
  const ix = gx * ew * .5, iy = gy * eh * .55 + lid * 2;
  const ir = 6.6 * (C.child ? 1.08 : 1);
  ctx.fillStyle = C.eye || '#3a2616'; ctx.beginPath(); ctx.ellipse(ix, iy, ir * (1 - .25 * far), ir, 0, 0, TAU); ctx.fill();
  ctx.fillStyle = shade(C.eye || '#3a2616', .35, .5); ctx.beginPath(); ctx.ellipse(ix, iy + 2, ir * .7 * (1 - .25 * far), ir * .55, 0, 0, Math.PI); ctx.fill();
  ctx.fillStyle = '#0b0705'; ctx.beginPath(); ctx.arc(ix, iy, 2.7, 0, TAU); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.9)'; ctx.beginPath(); ctx.arc(ix - 2.2, iy - 2.4, 1.6 + st.tearful * .6, 0, TAU); ctx.fill();
  if (st.tearful > .05) { ctx.fillStyle = `rgba(200,225,255,${.5 * st.tearful})`; ctx.beginPath(); ctx.ellipse(0, lo * .62, ew * .8, 2, 0, 0, TAU); ctx.fill(); }
  ctx.restore();
  // upper lid (skin) closing from the top
  const lidY = lerp(up, lo, lid);
  ctx.fillStyle = shade(C.skin, -.08);
  ctx.beginPath(); ctx.moveTo(-ew - 1, 0); ctx.bezierCurveTo(-ew * .5 + inner, up - 1, ew * .5 + inner, up - 1, ew + 1, 0);
  ctx.bezierCurveTo(ew * .5 + inner, lidY, -ew * .5 + inner, lidY, -ew - 1, 0); ctx.fill();
  // lower lid rising (smile/squint)
  const lowY = lerp(lo, 0, lowR);
  ctx.fillStyle = shade(C.skin, -.04);
  ctx.beginPath(); ctx.moveTo(-ew - 1, 0); ctx.bezierCurveTo(-ew * .5, lo + 1, ew * .5, lo + 1, ew + 1, 0);
  ctx.bezierCurveTo(ew * .5, lowY, -ew * .5, lowY, -ew - 1, 0); ctx.fill();
  // lash line on the lid edge (thicker at the outer corner)
  ctx.lineCap = 'round';
  ctx.strokeStyle = 'rgba(25,15,12,.9)'; ctx.lineWidth = 2.2;
  ctx.beginPath(); ctx.moveTo(-ew, .5); ctx.bezierCurveTo(-ew * .5 + inner, lidY * .98, ew * .5 + inner, lidY * .98, ew, .5); ctx.stroke();
  ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(s * ew * .6, lidY * .55); ctx.lineTo(s * (ew + 3), -2.5); ctx.stroke();
  if (C.lashes) { ctx.lineWidth = 1.3; for (let i = 0; i < 3; i++) { const x = s * ew * (.35 + i * .25); ctx.beginPath(); ctx.moveTo(x, lidY * (.85 - i * .2)); ctx.lineTo(x + s * 3, lidY * (.85 - i * .2) - 3); ctx.stroke(); } }
  ctx.strokeStyle = shade(C.skin, -.45, .35); ctx.lineWidth = 1.2;
  ctx.beginPath(); ctx.moveTo(-ew * .8, lowY * .9 + 1); ctx.quadraticCurveTo(0, lowY + 1.5, ew * .8, lowY * .9 + 1); ctx.stroke();
  // crease above the eye
  ctx.strokeStyle = shade(C.skin, -.45, .3 * (1 - lid * .6)); ctx.lineWidth = 1.3;
  ctx.beginPath(); ctx.moveTo(-ew * .8, up * .82); ctx.quadraticCurveTo(inner * 1, up * 1.35 - 1, ew * .85, up * .7); ctx.stroke();
  ctx.restore();
}
function drawBrow(ctx, C, st, s) {
  const [ex, ey] = eyeCenter(C, st, s);
  const far = Math.max(0, s * st.headYaw);
  const side = s < 0 ? st.browL : st.browR;
  const bi = st.browIn + side, bo = st.browOut + side, by = st.browY;
  const y0 = ey - 15 - by * 5 - st.frown * -2;
  const ix = ex - s * 10 * (1 - .3 * far) + s * st.frown * 2, ox = ex + s * 15 * (1 - .35 * far);
  const iy = y0 - bi * 6 + st.frown * 3, oy = y0 + 1 - bo * 5;
  const my = Math.min(iy, oy) - 4 - (bi + bo) * .8;
  const th = C.browW || 4.2;
  ctx.save();
  ctx.fillStyle = C.browCol || shade(C.hair, -.2);
  ctx.beginPath();
  ctx.moveTo(ix, iy - th * .6); ctx.quadraticCurveTo((ix + ox) / 2, my - th * .4, ox, oy - 1);
  ctx.quadraticCurveTo((ix + ox) / 2, my + th * .9, ix, iy + th * .6); ctx.closePath(); ctx.fill();
  // furrow lines between brows when frowning / sorrow
  if (s > 0 && (st.frown > .2 || bi > .5)) softStroke(ctx, P2(p => { p.moveTo(st.headYaw * 20 - 3, ey - 26); p.lineTo(st.headYaw * 20 - 2, ey - 16); }), shade(C.skin, -.5), 1.4, .35 * Math.max(st.frown, bi - .4));
  ctx.restore();
}
function drawNose(ctx, C, st) {
  const yaw = st.headYaw, pit = st.headPitch;
  const tx = yaw * 27, ty = 23 + pit * 9 + (C.child ? 4 : 0), nw = (C.noseW || 1);
  ctx.save();
  // bridge shading on the side away from the light
  softStroke(ctx, P2(p => { p.moveTo(yaw * 21 - 5, -2); p.quadraticCurveTo(tx - 7 * nw, ty - 10, tx - 8 * nw, ty - 1); }), shade(C.skin, -.45), 2.4, .28);
  // tip highlight
  ctx.fillStyle = shade(C.skin, .2, .4); ctx.beginPath(); ctx.ellipse(tx + 1, ty - 4, 4 * nw, 3, 0, 0, TAU); ctx.fill();
  // nostril base
  ctx.strokeStyle = shade(C.skin, -.5, .55); ctx.lineWidth = 1.8; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(tx - 9 * nw, ty + 1); ctx.quadraticCurveTo(tx - 5 * nw, ty + 5, tx, ty + 4); ctx.quadraticCurveTo(tx + 5 * nw, ty + 5, tx + 9 * nw, ty + 1); ctx.stroke();
  ctx.fillStyle = shade(C.skin, -.55, .45);
  for (const s of [-1, 1]) { ctx.beginPath(); ctx.ellipse(tx + s * 4.5 * nw, ty + 2.5, 2.4 + st.sneer, 1.4, 0, 0, TAU); ctx.fill(); }
  ctx.restore();
}
function drawMouth(ctx, C, st) {
  const yaw = st.headYaw, pit = st.headPitch;
  const mx = yaw * 22, my = 42 + pit * 8 + (C.child ? 2 : 0);
  const o = clamp(st.open, 0, 1), sm = st.smile, rd = clamp(st.round, 0, 1);
  const hw = 17 * (1 + Math.max(0, sm) * .22 + st.wide * .15 - rd * .35) * (C.mouthW || 1) * (1 - Math.abs(yaw) * .15);
  const cy = -sm * 4.5 + st.sneer * -2; // corner height
  const h = o * 15 * (1 + rd * .3);
  const lipC = C.lip || shade(C.skin, -.18);
  ctx.save(); ctx.translate(mx, my);
  // nasolabial folds when smiling
  if (sm > .2) for (const s of [-1, 1]) softStroke(ctx, P2(p => { p.moveTo(s * 16, -18); p.quadraticCurveTo(s * (hw + 6), -10, s * (hw + 4), cy + 2); }), shade(C.skin, -.4), 1.4, .16 * sm);
  if (h > 1.2) {
    const inner = P2(p => { p.moveTo(-hw, cy); p.bezierCurveTo(-hw * .5, -2 - o * 2, hw * .5, -2 - o * 2, hw, cy); p.bezierCurveTo(hw * .5, h + 2, -hw * .5, h + 2, -hw, cy); p.closePath(); });
    ctx.fillStyle = '#3b1416'; ctx.fill(inner);
    ctx.save(); ctx.clip(inner);
    ctx.fillStyle = '#f1ece4'; ctx.fillRect(-hw * .8, -4 - o * 2, hw * 1.6, 4 + o * 2);
    ctx.fillStyle = '#b5545a'; ctx.beginPath(); ctx.ellipse(0, h + 3, hw * .6, 6, 0, 0, TAU); ctx.fill();
    ctx.restore();
    // lips
    ctx.fillStyle = lipC;
    ctx.beginPath(); ctx.moveTo(-hw - 1, cy); ctx.bezierCurveTo(-hw * .55, -6.5, -3, -6, 0, -4.5); ctx.bezierCurveTo(3, -6, hw * .55, -6.5, hw + 1, cy);
    ctx.bezierCurveTo(hw * .5, -2 - o * 2, -hw * .5, -2 - o * 2, -hw - 1, cy); ctx.fill();
    ctx.fillStyle = shade(lipC, .06);
    ctx.beginPath(); ctx.moveTo(-hw, cy); ctx.bezierCurveTo(-hw * .5, h + 2, hw * .5, h + 2, hw, cy); ctx.bezierCurveTo(hw * .5, h + 9, -hw * .5, h + 9, -hw, cy); ctx.fill();
  } else {
    ctx.fillStyle = lipC;
    ctx.beginPath(); ctx.moveTo(-hw, cy); ctx.bezierCurveTo(-hw * .55, -6, -3, -5.5, 0, -4); ctx.bezierCurveTo(3, -5.5, hw * .55, -6, hw, cy);
    ctx.bezierCurveTo(hw * .5, 9, -hw * .5, 9, -hw, cy); ctx.fill();
    ctx.strokeStyle = shade(lipC, -.55); ctx.lineWidth = 1.8; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(-hw, cy); ctx.bezierCurveTo(-hw * .4, cy * .2 + 1.2, hw * .4, cy * .2 + 1.2, hw, cy); ctx.stroke();
  }
  // lower lip highlight + chin shadow
  ctx.fillStyle = 'rgba(255,255,255,.12)'; ctx.beginPath(); ctx.ellipse(0, h + 4, hw * .35, 1.6, 0, 0, TAU); ctx.fill();
  ctx.fillStyle = shade(C.skin, -.4, .18); ctx.beginPath(); ctx.ellipse(0, h + 12, hw * .5, 3, 0, 0, TAU); ctx.fill();
  ctx.restore();
}
function drawBeard(ctx, C, st) {
  const yaw = st.headYaw, o = st.open, fw = (C.faceW || 1), col = C.beardCol || C.hair;
  const full = C.beard === 'full', len = C.beardLen || (full ? 1 : .6);
  const mx = yaw * 22, my = 42 + st.headPitch * 8;
  const p = P2(p => {
    spline(p, [[-50 * fw + yaw * 7, -8], [-49 * fw + yaw * 6, 20], [-40 * fw + yaw * 6, 52 + o * 5], [-18 + yaw * 10, 66 + 20 * len + o * 8], [yaw * 12, 70 + 24 * len + o * 8], [18 + yaw * 10, 66 + 20 * len + o * 8], [40 * fw + yaw * 6, 52 + o * 5], [49 * fw + yaw * 6, 20], [50 * fw + yaw * 7, -8],
    [42 * fw + yaw * 12, 4], [36 + yaw * 16, 22], [mx + 22, my + 2], [mx + 16, my + 12 + o * 13], [mx, my + 15 + o * 14], [mx - 16, my + 12 + o * 13], [mx - 22, my + 2], [-36 + yaw * 16, 22], [-42 * fw + yaw * 12, 4]], true, .5);
  });
  const g = ctx.createLinearGradient(0, 0, 0, 100); g.addColorStop(0, shade(col, .05)); g.addColorStop(1, shade(col, -.25));
  ctx.fillStyle = g; ctx.fill(p);
  // strands
  ctx.save(); ctx.clip(p); ctx.lineCap = 'round';
  const r = rng(C.seed * 31);
  for (let i = 0; i < 46; i++) {
    const x = (r() * 2 - 1) * 48, y = r() * 80 + 5, l = 10 + r() * 14;
    ctx.strokeStyle = r() < .5 ? shade(col, .3, .35) : shade(col, -.4, .35); ctx.lineWidth = 1.3;
    ctx.beginPath(); ctx.moveTo(x + yaw * 8, y); ctx.quadraticCurveTo(x * .95 + yaw * 8, y + l * .6, x * .9 + yaw * 8, y + l); ctx.stroke();
  }
  ctx.restore();
}
function drawMustache(ctx, C, st) {
  const yaw = st.headYaw, col = C.beardCol || C.hair;
  const mx = yaw * 22, my = 42 + st.headPitch * 8, cy = -st.smile * 4;
  ctx.save(); ctx.translate(mx, my);
  ctx.fillStyle = shade(col, -.05);
  ctx.beginPath(); ctx.moveTo(-23, cy + 6); ctx.quadraticCurveTo(-14, -12, 0, -11); ctx.quadraticCurveTo(14, -12, 23, cy + 6);
  ctx.quadraticCurveTo(12, -3 - st.open * 2, 0, -4 - st.open * 2); ctx.quadraticCurveTo(-12, -3 - st.open * 2, -23, cy + 6); ctx.fill();
  ctx.strokeStyle = shade(col, .3, .35); ctx.lineWidth = 1.2;
  for (let i = -3; i <= 3; i++) { ctx.beginPath(); ctx.moveTo(i * 5, -10); ctx.lineTo(i * 6.5, -3); ctx.stroke(); }
  ctx.restore();
}
function drawTears(ctx, C, st, t) {
  for (const tr of st.tears || []) {
    const dur = tr.dur || 2.6, p = (t - tr.t0) / dur;
    if (p < 0 || p > 1) continue;
    const [ex, ey] = eyeCenter(C, st, tr.side);
    const sx = ex + tr.side * 3, sy = ey + 7;
    const a = p < .85 ? 1 : 1 - (p - .85) / .15; // whole tear fades out together
    const run = clamp((p - .22) / .6);
    const dx = sx + tr.side * 5 * run, dy = sy + run * 50;
    ctx.save(); ctx.globalAlpha = a;
    if (p < .25) { ctx.fillStyle = 'rgba(190,220,255,.6)'; ctx.beginPath(); ctx.ellipse(sx, sy, 2 + p * 10, 2.2, 0, 0, TAU); ctx.fill(); }
    else {
      ctx.strokeStyle = 'rgba(185,215,255,.45)'; ctx.lineWidth = 2.2; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.quadraticCurveTo(sx + tr.side * 1, (sy + dy) / 2, dx, dy - 3); ctx.stroke();
      const g = ctx.createRadialGradient(dx - 1, dy - 1, .5, dx, dy, 5); g.addColorStop(0, 'rgba(240,250,255,.95)'); g.addColorStop(.5, 'rgba(160,200,250,.75)'); g.addColorStop(1, 'rgba(120,170,240,.25)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(dx, dy - 8); ctx.quadraticCurveTo(dx + 4.5, dy, dx, dy + 4.5); ctx.quadraticCurveTo(dx - 4.5, dy, dx, dy - 8); ctx.fill();
    }
    ctx.restore();
  }
}
function hairStrands(ctx, clip, C, n, region, flow, seed) {
  ctx.save(); ctx.clip(clip); ctx.lineCap = 'round';
  const r = rng(seed);
  for (let i = 0; i < n; i++) {
    const x = region[0] + r() * (region[2] - region[0]), y = region[1] + r() * (region[3] - region[1]);
    const [fx, fy] = flow(x, y), l = 12 + r() * 22;
    ctx.strokeStyle = r() < .55 ? shade(C.hair, .35, .3) : shade(C.hair, -.45, .35); ctx.lineWidth = 1.2 + r() * 1.2;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + fx * l * .5 + fy * 3, y + fy * l * .5, x + fx * l, y + fy * l); ctx.stroke();
  }
  ctx.restore();
}
function drawBackHair(ctx, C, st, nt) {
  if (C.headwear && C.headwear.type === 'veil') {
    ctx.save(); ctx.translate(nt[0], nt[1]); ctx.rotate(st.headRoll); ctx.translate(st.headYaw * 9, -64);
    const col2 = C.headwear.color; const g = ctx.createLinearGradient(0, -90, 0, 200); g.addColorStop(0, shade(col2, -.1)); g.addColorStop(1, shade(col2, -.4));
    const p = P2(p => spline(p, [[-60, -40], [0, -90], [60, -40], [74, 60], [118, 150], [96, 210], [-96, 210], [-118, 150], [-74, 60]], true, .55));
    ctx.fillStyle = g; ctx.fill(p);
    ctx.save(); ctx.clip(p); for (let i = 0; i < 6; i++) softStroke(ctx, P2(q => { const x = -90 + i * 36; q.moveTo(x * .6, 0); q.quadraticCurveTo(x * .9, 100, x, 210); }), shade(col2, -.6), 3, .25); ctx.restore();
    ctx.restore();
  }
  if (!C.hairBack) return;
  ctx.save(); ctx.translate(nt[0], nt[1]); ctx.rotate(st.headRoll); ctx.translate(0, -64 + st.headPitch * 6);
  const yaw = st.headYaw;
  const p = P2(p => spline(p, [[-56 + yaw * 4, -40], [0, -84], [56 + yaw * 4, -40], [62, 40], [58, 110], [30, 124], [-30, 124], [-58, 110], [-62, 40]], true, .6));
  const g = ctx.createLinearGradient(0, -80, 0, 130); g.addColorStop(0, shade(C.hair, .05)); g.addColorStop(1, shade(C.hair, -.35));
  ctx.fillStyle = g; ctx.fill(p);
  hairStrands(ctx, p, C, 60, [-60, -40, 60, 120], (x, y) => [x * .004, 1], C.seed * 7);
  ctx.restore();
}
function drawFrontHair(ctx, C, st, t) {
  const yaw = st.headYaw, fw = C.faceW || 1, sty = C.hairStyle, col = C.hair;
  const X = x => x * fw + yaw * 9;
  ctx.save();
  const grad = (y0, y1) => { const g = ctx.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, shade(col, .12)); g.addColorStop(1, shade(col, -.15)); return g; };
  if (sty === 'curly' || sty === 'short') {
    const curly = sty === 'curly';
    const p = P2(p => spline(p, [[X(-52), 2], [X(-58), -38], [X(-38), -76], [X(0), -88 - (curly ? 6 : 0)], [X(40), -76], [X(58), -38], [X(52), 2], [X(47), -24], [X(30), -44], [X(4), -48], [X(-22), -46], [X(-44), -28]], true, .55));
    ctx.fillStyle = grad(-90, 0); ctx.fill(p);
    if (curly) { // coiled texture as short curved flicks, blended (not stamped circles)
      ctx.save(); ctx.clip(p); const r = rng(C.seed * 13); ctx.lineCap = 'round';
      for (let i = 0; i < 110; i++) { const x = X(-58 + r() * 116), y = -88 + r() * 90, a = r() * TAU; ctx.strokeStyle = r() < .5 ? shade(col, .35, .3) : shade(col, -.5, .35); ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, 3 + r() * 3, a, a + 2.2); ctx.stroke(); }
      ctx.restore();
    } else hairStrands(ctx, p, C, 70, [X(-58), -88, X(58), 0], (x, y) => [(x - yaw * 9) > 0 ? .6 : -.6, .55], C.seed * 5);
  } else if (sty === 'bald') { // receding: fringe of hair on sides/back, skin on top
    for (const s of [-1, 1]) {
      const p = P2(p => spline(p, [[X(s * 50), 22], [X(s * 58), -4], [X(s * 57), -34], [X(s * 46), -54], [X(s * 36), -50], [X(s * 46), -30], [X(s * 47), -4], [X(s * 44), 14]], true, .5));
      ctx.fillStyle = grad(-60, 14); ctx.fill(p);
      hairStrands(ctx, p, C, 18, [X(s * 60), -60, X(s * 40), 14], () => [0, 1], C.seed * 3 + s);
    }
    ctx.fillStyle = shade(C.skin, .25, .35); ctx.beginPath(); ctx.ellipse(X(-10), -62, 20, 8, -.2, 0, TAU); ctx.fill();
  } else if (sty === 'roman') {
    const p = P2(p => spline(p, [[X(-51), -4], [X(-56), -40], [X(-36), -74], [X(0), -82], [X(36), -74], [X(56), -40], [X(51), -4], [X(46), -36], [X(26), -48], [X(12), -45], [X(-2), -50], [X(-16), -45], [X(-30), -49], [X(-46), -34]], true, .5));
    ctx.fillStyle = grad(-85, 0); ctx.fill(p);
    hairStrands(ctx, p, C, 60, [X(-56), -82, X(56), -4], (x, y) => [0, 1], C.seed * 5);
    if (C.gray) { ctx.save(); ctx.clip(p); ctx.fillStyle = 'rgba(200,200,200,.35)'; ctx.fillRect(X(-60), -50, 18, 50); ctx.fillRect(X(42), -50, 18, 50); ctx.restore(); }
  } else if (sty === 'wavy') {
    const p = P2(p => spline(p, [[X(-53), 10], [X(-60), -36], [X(-40), -78], [X(0), -88], [X(42), -78], [X(60), -36], [X(53), 10], [X(48), -20], [X(34), -46], [X(10), -54], [X(-8), -44], [X(-30), -50], [X(-47), -24]], true, .55));
    ctx.fillStyle = grad(-90, 10); ctx.fill(p);
    hairStrands(ctx, p, C, 80, [X(-60), -88, X(60), 10], (x, y) => [x > yaw * 9 ? .5 : -.5, .7], C.seed * 5);
  } else if (sty === 'ponytail' || sty === 'bun') {
    const p = P2(p => spline(p, [[X(-52), 0], [X(-56), -40], [X(-36), -76], [X(0), -84], [X(36), -76], [X(56), -40], [X(52), 0], [X(45), -32], [X(20), -54], [X(-4), -58], [X(-28), -52], [X(-46), -30]], true, .55));
    ctx.fillStyle = grad(-90, 0); ctx.fill(p);
    hairStrands(ctx, p, C, 60, [X(-56), -84, X(56), 0], (x, y) => [x > 0 ? .8 : -.8, .3], C.seed * 5);
    if (sty === 'bun' && !C.headwear) { ctx.fillStyle = grad(-120, -80); ctx.beginPath(); ctx.ellipse(X(0) - yaw * 10, -92, 22, 16, 0, 0, TAU); ctx.fill(); }
  } else if (sty === 'afro') {
    const p = P2(p => spline(p, [[X(-56), 6], [X(-74), -40], [X(-58), -92], [X(0), -112], [X(58), -92], [X(74), -40], [X(56), 6], [X(50), -30], [X(30), -48], [X(0), -50], [X(-30), -48], [X(-50), -30]], true, .55));
    ctx.fillStyle = grad(-110, 0); ctx.fill(p);
    ctx.save(); ctx.clip(p); const r = rng(C.seed * 17);
    for (let i = 0; i < 140; i++) { const x = X(-74 + r() * 148), y = -112 + r() * 118, a = r() * TAU; ctx.strokeStyle = r() < .5 ? shade(col, .3, .28) : shade(col, -.5, .3); ctx.lineWidth = 1.4; ctx.beginPath(); ctx.arc(x, y, 2.5 + r() * 2.5, a, a + 2.4); ctx.stroke(); }
    ctx.restore();
  }
  // headwear
  const hw = C.headwear;
  if (hw && hw.type === 'veil') {
    const col2 = hw.color;
    const p = P2(p => spline(p, [[X(-57), 40], [X(-62), -30], [X(-44), -80], [X(0), -92], [X(44), -80], [X(62), -30], [X(57), 40], [X(64), 70], [X(48), 66], [X(49), 10], [X(46), -30], [X(30), -52], [X(0), -58], [X(-30), -52], [X(-46), -30], [X(-49), 10], [X(-48), 66], [X(-64), 70]], true, .45));
    const g = ctx.createLinearGradient(-70, -90, 70, 70); g.addColorStop(0, shade(col2, .14)); g.addColorStop(1, shade(col2, -.22));
    ctx.fillStyle = g; ctx.fill(p);
    ctx.save(); ctx.clip(p);
    for (let i = 0; i < 5; i++) softStroke(ctx, P2(q => { const x = X(-48 + i * 24); q.moveTo(x * .8, -92); q.quadraticCurveTo(x * 1.1, -60, x * 1.3, -40); }), shade(col2, -.5), 2.5, .22);
    for (const s2 of [-1, 1]) softStroke(ctx, P2(q => { q.moveTo(X(s2 * 54), -20); q.quadraticCurveTo(X(s2 * 57), 20, X(s2 * 56), 66); }), shade(col2, -.5), 3, .28);
    softStroke(ctx, P2(q => { q.moveTo(X(-40), -60); q.quadraticCurveTo(X(0), -70, X(40), -60); }), shade(col2, .45), 3, .3);
    ctx.restore();
  } else if (hw && hw.type === 'helmet') {
    const g = ctx.createLinearGradient(0, -100, 0, -20); g.addColorStop(0, '#d4d7dc'); g.addColorStop(.6, '#8a9099'); g.addColorStop(1, '#4f545c');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(X(-58), -26); ctx.bezierCurveTo(X(-62), -100, X(62), -100, X(58), -26); ctx.quadraticCurveTo(X(0), -40, X(-58), -26); ctx.fill();
    ctx.fillStyle = '#6f747c'; ctx.fillRect(X(-62), -30, 124 * fw, 8);
    ctx.fillStyle = 'rgba(255,255,255,.4)'; ctx.beginPath(); ctx.ellipse(X(-20), -72, 16, 6, -.4, 0, TAU); ctx.fill();
    for (const s of [-1, 1]) { ctx.fillStyle = '#7d828a'; ctx.beginPath(); ctx.moveTo(X(s * 56), -26); ctx.lineTo(X(s * 58), 30); ctx.lineTo(X(s * 46), 34); ctx.lineTo(X(s * 48), -24); ctx.fill(); }
  }
  ctx.restore();
}
