// Assemble a full character: head (face rig) + torso + posed arms + props.
'use strict';
const L = require('./lib');
const { clamp, lerp } = L;
const { drawHead } = require('./face');
const B = require('./body');
const { C } = require('./characters');
const { POSES } = require('./engine');

function poseBlend(F) {
  const a = POSES[F.poseFrom] || POSES.default, b = POSES[F.poseTo] || POSES.default;
  const k = F.poseK == null ? 1 : F.poseK;
  const arm = (x, y) => ({
    w: [lerp(x.w[0], y.w[0], k), lerp(x.w[1], y.w[1], k)],
    hand: k < 0.5 ? x.hand : y.hand,
    rot: lerp(x.rot || 0, y.rot || 0, k),
    mirror: k < 0.5 ? (x.mirror || 1) : (y.mirror || 1),
  });
  const pick = (key) => (k < 0.5 ? a[key] : b[key]);
  return {
    n: arm(a.n, b.n), f: arm(a.f, b.f),
    front: k < 0.5 ? !!a.front : !!b.front,
    bread: pick('bread'), halves: pick('halves'), half: pick('half'), half2: pick('half2'), jar: pick('jar'),
    scroll: pick('scroll'), shackles: a.shackles || b.shackles, fidget: pick('fidget'), sway: lerp(a.sway || 0, b.sway || 0, k),
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
  // nervous fidget: the hand pats the tunic in short bursts; the body shifts its weight
  if (pb.fidget) {
    const fd = pb.fidget;
    const ph = (t + 1.3) % fd.period;
    const patLen = 0.34;
    let dy = 0, dx = 0;
    if (ph < fd.pats * patLen) {
      const u = (ph % patLen) / patLen;
      dy = Math.sin(Math.PI * u) * fd.amp[1];
      dx = Math.sin(Math.PI * u) * fd.amp[0];
    }
    // smooth idle drift between bursts so the hand never stops dead
    dx += 0.06 * L.noise1(t * 0.9, 31);
    dy += 0.05 * L.noise1(t * 1.1, 37);
    const arm = pb[fd.arm];
    arm.w = [arm.w[0] + dx, arm.w[1] + dy];
  }
  const swayLean = pb.sway ? pb.sway * Math.sin(t * 1.7) + pb.sway * 0.6 * L.noise1(t * 0.5, 41) : 0;
  const lean = (place.lean || 0) + pb.lean + (F.lean || 0) + swayLean;
  const breathe = F.breathV || 0;
  const Bx = place.x, By = place.y + breathe * s * 0.04;
  const neck = [Bx, By];
  const headX = Bx + Math.sin(lean) * s * 2.2 * fc + (F.headDX || 0) * s;
  const headY = By - s * 2.2 * Math.cos(lean) + (F.headDY || 0) * s - breathe * s * 0.02;
  const H = { x: headX, y: headY, s, yaw: F.yaw, pitch: F.pitch, roll: F.roll * fc + lean * 0.25 * fc, neckDX: Bx - headX };
  const by = (place.by == null ? 0.3 * fc : place.by) + 0.2 * (F.yaw - (place.by || 0));
  const sh = (F.shoulder || 0) + breathe * 0.05;
  const toScreen = (p) => [Bx + p[0] * fc * s, By + p[1] * s];

  let torso = null;
  const arms = () => {
    if (place.noArms) return;
    // far arm first, then props, then near arm
    const shoulderN = fc > 0 ? torso.shoulderL : torso.shoulderR;
    const shoulderF = fc > 0 ? torso.shoulderR : torso.shoulderL;
    const armF = B.drawArm(ctx, shoulderF, toScreen(pb.f.w), s, st, Lt, { hand: pb.f.hand, mirror: pb.f.mirror * fc, bend: -fc, handRot: pb.f.rot * fc, shackle: pb.shackles, dark: true, sleeve: st.cloth.sleeve });
    // props
    if (pb.bread && pb.bread.arm === 'f') {
      const w = armF.W;
      B.drawBread(ctx, w[0] + Math.cos(armF.ang) * s * 0.55, w[1] + Math.sin(armF.ang) * s * 0.35 - s * 0.2, pb.bread.r * s, Lt, { rot: 0.05 * fc });
    } else if (pb.bread) {
      const p = toScreen(pb.bread.at);
      B.drawBread(ctx, p[0], p[1], pb.bread.r * s, Lt, { rot: 0.05 * fc });
    }
    if (pb.half && pb.half.arm === 'f') {
      const w = armF.W;
      B.drawHalfBread(ctx, w[0] + Math.cos(armF.ang) * s * 1.1, w[1] + Math.sin(armF.ang) * s * 1.1, pb.half.r * s, Lt, { face: -fc, rot: armF.ang * 0.3 });
    } else if (pb.half && pb.half.at) {
      const p = toScreen(pb.half.at);
      B.drawHalfBread(ctx, p[0], p[1], pb.half.r * s, Lt, { face: -fc });
    }
    if (pb.scroll) {
      const w = armF.W;
      B.drawScroll(ctx, w[0] + fc * s * 0.6, w[1] - s * 0.4, s * 1.4, s * 2.0, Lt, { rot: 0.2 * fc });
    }
    const armN = B.drawArm(ctx, shoulderN, toScreen(pb.n.w), s, st, Lt, { hand: pb.n.hand, mirror: pb.n.mirror * fc, bend: fc, handRot: pb.n.rot * fc, shackle: pb.shackles, sleeve: st.cloth.sleeve });
    if (pb.halves) {
      const l = toScreen(pb.halves.l), r = toScreen(pb.halves.r);
      B.drawHalfBread(ctx, l[0], l[1], pb.halves.r0 * s, Lt, { face: 1, rot: -0.1 });
      B.drawHalfBread(ctx, r[0], r[1], pb.halves.r0 * s, Lt, { face: -1, rot: 0.1 });
    }
    if (pb.jar) {
      const w = armN.W;
      B.drawJar(ctx, w[0], w[1] + s * 1.7, pb.jar.h * s, Lt);
    }
    if (pb.half2) {
      const w = armN.W;
      B.drawHalfBread(ctx, w[0] + Math.cos(armN.ang) * s * 0.9, w[1] + Math.sin(armN.ang) * s * 0.9, pb.half2.r * s, Lt, { face: fc, rot: 0.2 });
    }
    if (opt.afterArms) opt.afterArms({ armN, armF, toScreen });
  };

  const drawBody = () => {
    if (place.headOnly) return;
    torso = B.drawTorso(ctx, neck, s, st, Lt, { by, shoulder: sh, len: place.len || 9, mantleSide: place.mantleSide || -fc, belt: place.belt });
    if (opt.afterTorso) opt.afterTorso({ neck, s, fc, st });
    if (!pb.front) arms();
  };

  const sway = opt.sway || [0, 0];
  drawHead(ctx, H, st, F, Lt, { drawBody, t, sway, noNeck: place.noNeck });
  if (!place.headOnly && pb.front) arms();
  return { H, neck };
}

module.exports = { drawCharacter, poseBlend };
