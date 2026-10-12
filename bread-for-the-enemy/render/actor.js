// Assemble a full character: head (face rig) + torso + posed arms + anatomical hands + props.
'use strict';
const L = require('./lib');
const { clamp, lerp } = L;
const { drawHead } = require('./face');
const B = require('./body');
const H = require('./hands');
const { C } = require('./characters');
const { POSES } = require('./engine');

const HANG = { in: 1, back: 0.3 };
const KEYS = ['fwd', 'back', 'up', 'down', 'in', 'out'];

// body-relative direction spec -> world vector (x right, y up, z toward the viewer)
function bodyVec(spec, by, right) {
  const Fb = [Math.sin(by), 0, Math.cos(by)];
  const Rb = [-Math.cos(by), 0, Math.sin(by)]; // the person's right
  const inV = right ? [-Rb[0], -Rb[1], -Rb[2]] : Rb;
  const basis = { fwd: Fb, back: [-Fb[0], 0, -Fb[2]], up: [0, 1, 0], down: [0, -1, 0], in: inV, out: [-inV[0], -inV[1], -inV[2]] };
  const v = [0, 0, 0];
  for (const k of KEYS) {
    const w = spec[k] || 0;
    if (!w) continue;
    v[0] += basis[k][0] * w; v[1] += basis[k][1] * w; v[2] += basis[k][2] * w;
  }
  return H.V.len(v) < 1e-4 ? [0, 0, 1] : H.V.norm(v);
}
function blendSpec(a, b, k) {
  const out = {};
  for (const key of KEYS) {
    const v = lerp((a && a[key]) || 0, (b && b[key]) || 0, k);
    if (Math.abs(v) > 1e-4) out[key] = v;
  }
  return out;
}

function poseBlend(F) {
  const a = POSES[F.poseFrom] || POSES.default, b = POSES[F.poseTo] || POSES.default;
  const k = F.poseK == null ? 1 : F.poseK;
  const arm = (x, y) => {
    const fkx = x.fdir ? (x.fk == null ? 0.6 : x.fk) : 0, fky = y.fdir ? (y.fk == null ? 0.6 : y.fk) : 0;
    return {
      w: [lerp(x.w[0], y.w[0], k), lerp(x.w[1], y.w[1], k)],
      shape: H.blendPreset(x.hand || 'relax', y.hand || 'relax', k),
      palm: blendSpec(x.palm || HANG, y.palm || HANG, k),
      fdir: (x.fdir || y.fdir) ? blendSpec(x.fdir || {}, y.fdir || {}, k) : null,
      fk: lerp(fkx, fky, k),
      fz: lerp(x.fz || 0, y.fz || 0, k),
    };
  };
  // props cannot blend: they appear as soon as a pose that holds them starts, and stay until the
  // next pose has nearly taken over, so nothing pops in or out halfway through a gesture
  const pick = (key) => {
    if (a[key] && b[key]) return k < 0.5 ? a[key] : b[key];
    if (b[key]) return k > 0.02 ? b[key] : null;
    if (a[key]) return k < 0.97 ? a[key] : null;
    return null;
  };
  return {
    n: arm(a.n, b.n), f: arm(a.f, b.f),
    front: k < 0.5 ? !!a.front : !!b.front,
    bread: pick('bread'), halves: pick('halves'), half: pick('half'), half2: pick('half2'), jar: pick('jar'),
    scroll: pick('scroll'), parchment: pick('parchment'), rope: pick('rope'), spear: pick('spear'),
    shackles: a.shackles || b.shackles, fidget: pick('fidget'), sway: lerp(a.sway || 0, b.sway || 0, k),
    lean: lerp(a.lean || 0, b.lean || 0, k),
    k, from: F.poseFrom, to: F.poseTo,
  };
}

// place: {x, y, s, facing, by, len, style, mantleSide, noArms, headOnly, lean}
function drawCharacter(ctx, who, F, place, Lt, t, opt = {}) {
  const st = C[place.style || who];
  const s = place.s;
  const fc = place.facing || 1;
  const pb = poseBlend(F);
  // nervous fidget: the hand shifts its grip on the loaf in short bursts; the body shifts its weight
  if (pb.fidget) {
    const fd = pb.fidget;
    const ph = (t + 1.3) % fd.period;
    const patLen = 0.42;
    let dy = 0, dx = 0;
    if (ph < fd.pats * patLen) {
      const u = (ph % patLen) / patLen;
      dy = Math.sin(Math.PI * u) * fd.amp[1];
      dx = Math.sin(Math.PI * u) * fd.amp[0];
    }
    dx += 0.05 * L.noise1(t * 0.7, 31);
    dy += 0.04 * L.noise1(t * 0.8, 37);
    const arm = pb[fd.arm];
    arm.w = [arm.w[0] + dx, arm.w[1] + dy];
    arm.shape = Object.assign({}, arm.shape, { curl: arm.shape.curl.map((c, i) => c + 0.12 * Math.max(0, Math.sin(t * 2.1 + i * 0.7))) });
  }
  const swayLean = pb.sway ? pb.sway * Math.sin(t * 1.3) + pb.sway * 0.6 * L.noise1(t * 0.4, 41) : 0;
  const lean = (place.lean || 0) + pb.lean + (F.lean || 0) + swayLean;
  const breathe = F.breathV || 0;
  const Bx = place.x, By = place.y + breathe * s * 0.035;
  const neck = [Bx, By];
  const headX = Bx + Math.sin(lean) * s * 2.2 * fc + (F.headDX || 0) * s;
  const headY = By - s * 2.2 * Math.cos(lean) + (F.headDY || 0) * s - breathe * s * 0.015;
  const Hd = { x: headX, y: headY, s, yaw: F.yaw, pitch: F.pitch, roll: F.roll * fc + lean * 0.25 * fc, neckDX: Bx - headX };
  // the body turns a little with the gaze (from the look target only, never from speech wobble)
  const yawBody = F.yawLook == null ? F.yaw : F.yawLook;
  const by = (place.by == null ? 0.3 * fc : place.by) + 0.2 * (yawBody - (place.by || 0));
  const sh = (F.shoulder || 0) + breathe * 0.03;
  const toScreen = (p) => [Bx + p[0] * fc * s, By + p[1] * s];
  const loose = st.cloth.looseSleeves || 0;

  // ---- arm and hand geometry
  let arms = null;
  if (!place.noArms && !place.headOnly) {
    const sj = B.shoulderJoints(neck, s, by, sh);
    const SN = fc > 0 ? sj.L : sj.R, SF = fc > 0 ? sj.R : sj.L;
    const gN = B.armGeom(SN, toScreen(pb.n.w), s, { bend: fc, loose });
    const gF = B.armGeom(SF, toScreen(pb.f.w), s, { bend: -fc, loose });
    const spec = (arm, g, right) => {
      let f = H.V.norm([g.dir[0], -g.dir[1], arm.fz || 0]);
      if (arm.fdir && arm.fk > 0.01) f = H.V.norm(H.V.lerp(f, bodyVec(arm.fdir, by, right), arm.fk));
      return { f, n: bodyVec(arm.palm, by, right), right, shape: arm.shape };
    };
    // near arm is the character's right arm when facing screen-right
    const hN = H.handParts(gN.W, s, st, Lt, spec(pb.n, gN, fc > 0));
    const hF = H.handParts(gF.W, s, st, Lt, spec(pb.f, gF, fc < 0));
    arms = { gN, gF, hN, hF };
  }
  const nb = B.neckBase(neck, s, by);
  const collar = B.collarPts(neck, s, by, st.cloth.neck);

  // ---- props held in the hands
  const props = [];
  const attach = (which, depthBase, r, draw) => {
    const h = which === 'f' ? arms.hF : arms.hN;
    const g = h.gripAt(r);
    props.push({ arm: which, depth: depthBase + g[2], draw: () => draw(g, which === 'f' ? arms.gF : arms.gN) });
  };
  const FAR = -s * 0.6; // the far hand sits a little deeper than the near one
  if (arms) {
    if (pb.bread && pb.bread.arm) attach(pb.bread.arm, pb.bread.arm === 'f' ? FAR : 0, pb.bread.r * s * 0.95, (g) => B.drawBread(ctx, g[0], g[1], pb.bread.r * s, Lt, { rot: 0.05 * fc }));
    if (pb.half && pb.half.arm) attach(pb.half.arm, pb.half.arm === 'f' ? FAR : 0, pb.half.r * s * 0.7, (g, ag) => B.drawHalfBread(ctx, g[0], g[1], pb.half.r * s, Lt, { face: -fc, rot: clamp(ag.ang - Math.PI / 2, -0.5, 0.5) * 0.4 }));
    if (pb.half2 && pb.half2.arm) attach(pb.half2.arm, pb.half2.arm === 'f' ? FAR : 0, pb.half2.r * s * 0.7, (g) => B.drawHalfBread(ctx, g[0], g[1], pb.half2.r * s, Lt, { face: fc, rot: 0.15 * fc }));
    if (pb.halves) {
      attach('n', 0, pb.halves.r0 * s * 0.7, (g) => B.drawHalfBread(ctx, g[0], g[1], pb.halves.r0 * s, Lt, { face: fc, rot: -0.1 * fc }));
      attach('f', FAR, pb.halves.r0 * s * 0.7, (g) => B.drawHalfBread(ctx, g[0], g[1], pb.halves.r0 * s, Lt, { face: -fc, rot: 0.1 * fc }));
    }
    if (pb.jar) attach(pb.jar.arm, pb.jar.arm === 'f' ? FAR : 0, s * 0.18, (g) => B.drawJar(ctx, g[0], g[1] + pb.jar.h * s * 0.98, pb.jar.h * s, Lt));
    if (pb.scroll) attach('f', FAR, s * 0.3, (g) => B.drawScroll(ctx, g[0], g[1], s * 0.75, s * 2.1, Lt, { rot: 0.15 * fc }));
    if (pb.spear) attach(pb.spear.arm, pb.spear.arm === 'f' ? FAR : 0, s * 0.12, (g) => drawSpear(ctx, g, s, Lt));
    if (pb.bread && pb.bread.at) {
      const p = toScreen(pb.bread.at);
      props.push({ arm: null, depth: (arms.hN.gripAt(0)[2] + FAR + arms.hF.gripAt(0)[2]) / 2 + s * 0.05, draw: () => B.drawBread(ctx, p[0], p[1], pb.bread.r * s, Lt, { rot: 0.05 * fc }) });
    }
  }

  const drawSleeveAndWrist = (which, part, torso) => {
    const g = which === 'f' ? arms.gF : arms.gN;
    if (part !== 'upper') H.drawWrist(ctx, g.W, g.dir, s, st, Lt);
    B.drawSleeve(ctx, g, st, Lt, { part, torso: torso && torso.poly, far: which === 'f', sleeve: st.cloth.sleeve });
    if (part !== 'upper' && pb.shackles) B.drawShackle(ctx, g.W, g.ang, s, Lt);
  };
  // hand parts and props of the given arms, back to front
  const drawHandsAndProps = (which) => {
    const items = [];
    for (const w of which) {
      const h = w === 'f' ? arms.hF : arms.hN;
      const base = w === 'f' ? FAR : 0;
      for (const p of h.parts) items.push({ depth: base + p.depth, draw: () => p.draw(ctx) });
    }
    for (const p of props) if (p.arm === null ? which.length === 2 : which.includes(p.arm)) items.push(p);
    items.sort((x, y) => x.depth - y.depth);
    for (const it of items) it.draw();
  };
  const drawRope = () => {
    if (!pb.rope) return;
    const a = arms.gN.W, b = arms.gF.W;
    ctx.save();
    ctx.lineCap = 'round';
    ctx.strokeStyle = L.mul('#7a6440', Lt.key || '#fff'); ctx.lineWidth = s * 0.16;
    ctx.beginPath(); ctx.moveTo(a[0], a[1] - s * 0.15); ctx.lineTo(b[0], b[1] - s * 0.15); ctx.stroke();
    for (const p of [a, b]) {
      for (const dy of [-0.3, -0.05]) { ctx.beginPath(); ctx.ellipse(p[0], p[1] + dy * s, s * 0.32, s * 0.12, 0, 0, L.TAU); ctx.stroke(); }
    }
    ctx.strokeStyle = 'rgba(30,20,10,0.6)'; ctx.lineWidth = s * 0.03;
    ctx.beginPath(); ctx.moveTo(a[0], a[1] - s * 0.15); ctx.lineTo(b[0], b[1] - s * 0.15); ctx.stroke();
    ctx.restore();
  };

  let torso = null;
  const drawBody = () => {
    if (place.headOnly) return;
    // the far arm hangs behind the chest (its forearm comes forward later if the pose needs it)
    if (arms) {
      if (pb.front) drawSleeveAndWrist('f', 'upper', null);
      else { drawSleeveAndWrist('f', 'all', null); drawHandsAndProps(['f']); }
    }
    torso = B.drawTorso(ctx, neck, s, st, Lt, { by, shoulder: sh, len: place.len || 9, mantleSide: place.mantleSide || fc, belt: place.belt });
    if (opt.afterTorso) opt.afterTorso({ neck, s, fc, st, by });
    if (arms && pb.parchment) drawParchment(ctx, toScreen([0.55, 4.55]), s, Lt, fc);
    if (arms && !pb.front) { drawSleeveAndWrist('n', 'all', torso); drawHandsAndProps(['n']); }
  };

  const sway = opt.sway || [0, 0];
  drawHead(ctx, Hd, st, F, Lt, { drawBody, t, sway, noNeck: place.noNeck, neckBase: nb, collar });
  if (arms && pb.front) {
    drawSleeveAndWrist('f', 'lower', torso);
    drawSleeveAndWrist('n', 'all', torso);
    drawRope();
    drawHandsAndProps(['f', 'n']);
  }
  if (arms && opt.afterArms) opt.afterArms({ armN: { W: arms.gN.W, ang: arms.gN.ang }, armF: { W: arms.gF.W, ang: arms.gF.ang }, toScreen });
  return { H: Hd, neck, arms: arms ? { near: arms.gN, far: arms.gF } : null, s, fc };
}

// a spear held upright through the fist
function drawSpear(ctx, g, s, Lt) {
  ctx.save();
  ctx.lineCap = 'round';
  ctx.strokeStyle = L.mul('#5a3a22', Lt.key || '#fff'); ctx.lineWidth = s * 0.16;
  ctx.beginPath(); ctx.moveTo(g[0] - s * 0.25, g[1] + s * 6); ctx.lineTo(g[0] + s * 0.35, g[1] - s * 7.5); ctx.stroke();
  ctx.strokeStyle = 'rgba(20,10,5,0.7)'; ctx.lineWidth = s * 0.03; ctx.stroke();
  const tip = [g[0] + s * 0.35, g[1] - s * 7.5];
  ctx.fillStyle = L.mul('#9a9690', Lt.key || '#fff');
  ctx.beginPath(); ctx.moveTo(tip[0] - s * 0.22, tip[1] + s * 0.1); ctx.lineTo(tip[0] + s * 0.08, tip[1] - s * 1.1); ctx.lineTo(tip[0] + s * 0.25, tip[1] + s * 0.05); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#1a1614'; ctx.lineWidth = s * 0.025; ctx.stroke();
  ctx.restore();
}
// a sheet of parchment on the lap (Paul writing)
function drawParchment(ctx, p, s, Lt, fc) {
  ctx.save();
  ctx.translate(p[0], p[1]); ctx.rotate(0.12 * fc);
  ctx.fillStyle = L.mul('#e6d6b0', Lt.key || '#fff');
  ctx.beginPath(); ctx.moveTo(-s * 1.1, -s * 0.35); ctx.lineTo(s * 1.0, -s * 0.45); ctx.lineTo(s * 1.15, s * 0.3); ctx.lineTo(-s * 1.0, s * 0.42); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(60,40,20,0.8)'; ctx.lineWidth = s * 0.03; ctx.stroke();
  ctx.strokeStyle = 'rgba(60,40,30,0.45)'; ctx.lineWidth = s * 0.02;
  for (let i = 0; i < 5; i++) { const y = -s * 0.22 + i * s * 0.12; ctx.beginPath(); ctx.moveTo(-s * 0.85, y + s * 0.02); ctx.lineTo(s * (0.4 + 0.4 * ((i * 37) % 7) / 7), y - s * 0.03); ctx.stroke(); }
  ctx.restore();
}

module.exports = { drawCharacter, poseBlend, bodyVec };
