'use strict';
// Assembles a full character from face, hair and body parts in draw order.

const { clamp, lerp, col, shade, rgbStr } = require('./util');
const F = require('./face');
const { STYLES } = require('./hair');
const B = require('./body');

const HEAD_Y = -0.77;     // head centre relative to the neck base
const PIVOT = 0.42;       // roll pivot (top of neck) in head-local y

// Every numeric pose parameter with its rest value, so partial poses never produce NaN.
const POSE_DEFAULTS = {
  yaw: 0, pitch: 0, roll: 0, headX: 0, headY: 0, bodyYaw: 0, lean: 0, slump: 0, shoulderUp: 0, breath: 0,
  gazeX: 0, gazeY: 0, blink: 0, lid: 0, lidL: 0, lidR: 0, squint: 0, squintL: 0, squintR: 0, wide: 0, wet: 0, pupil: 0,
  browIn: 0, browOut: 0, browKnit: 0, browAsym: 0, browInL: 0, browInR: 0, browOutL: 0, browOutR: 0, browTalk: 0,
  smile: 0, open: 0, wide2: 0, round: 0, press: 0, asym: 0, jawOpen: 0, teeth: 0, blush: 0, tired: 0,
};
function normalizePose(P) {
  const out = { ...POSE_DEFAULTS };
  for (const k in P) if (P[k] !== undefined && !(typeof P[k] === 'number' && Number.isNaN(P[k]))) out[k] = P[k];
  return out;
}

function headPlacement(A, P, T) {
  const slump = P.slump || 0;
  return {
    x: T.cx + (P.headX || 0) + (P.lean || 0) * 0.08,
    y: HEAD_Y + (P.headY || 0) + slump * 0.09 - (P.breath || 0) * 0.008 + T.sy * 0.4,
  };
}

// Draw a character. P.x/P.y = neck base in pixels, P.scale = pixels per head unit.
// opts.parts: 'all' | 'base' (everything except front arms) | 'front' (front arms only)
function drawCharacter(ctx, A, P0, opts = {}) {
  const P = normalizePose(P0);
  const parts = opts.parts || 'all';
  const light = opts.light || { x: -0.6, y: -0.8 };
  const S = P.scale;
  ctx.save();
  ctx.translate(P.x, P.y);
  ctx.scale(S, S);
  const T = B.torsoGeom(A, P);
  const H = headPlacement(A, P, T);
  const yaw = clamp(P.yaw || 0, -1.2, 1.2);
  const pitch = clamp((P.pitch || 0) + (P.slump || 0) * 0.35, -1, 1.2);
  const R = F.rotation(yaw, pitch);
  const roll = P.roll || 0;
  const sway = P.sway || { x: 0, y: 0 };
  const style = STYLES[A.hairStyle];
  const arms = [['armL', -1], ['armR', 1]];

  const withHead = (fn) => {
    ctx.save();
    ctx.translate(H.x, H.y + PIVOT);
    ctx.rotate(roll);
    ctx.translate(0, -PIVOT);
    if (A.headScale) ctx.scale(A.headScale, A.headScale);
    fn();
    ctx.restore();
  };

  if (parts !== 'front') {
    // 1. hair behind everything
    if (style && style.back) withHead(() => style.back(ctx, A, R, sway));
    // 2. arms tucked behind the torso
    for (const [k, s] of arms) {
      const arm = P[k];
      if (arm && !arm.front && arm.hx !== undefined) B.drawArm(ctx, A, P, T, armSpec(arm), s, light);
    }
    // 3. neck + torso
    B.drawNeck(ctx, A, P, { x: H.x + Math.sin(roll) * 0.1, y: H.y + PIVOT - 0.1 });
    B.drawTorso(ctx, A, P, light);
    if (A.extraBody) A.extraBody(ctx, A, P, T, 'afterTorso');
    if (A.headphones) {
      // headphones resting around the neck
      ctx.save();
      ctx.strokeStyle = '#26272c'; ctx.lineWidth = 0.05; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.ellipse(T.cx, 0.02, 0.27, 0.13, 0, Math.PI * 0.05, Math.PI * 0.95); ctx.stroke();
      for (const s of [-1, 1]) {
        ctx.fillStyle = '#2f3036';
        ctx.beginPath(); ctx.ellipse(T.cx + s * 0.27, 0.08, 0.075, 0.1, s * 0.3, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#4a4c55';
        ctx.beginPath(); ctx.ellipse(T.cx + s * 0.27, 0.08, 0.045, 0.065, s * 0.3, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
    }
    // 4. head
    withHead(() => drawHead(ctx, A, P, R, light, style, sway));
  }
  if (parts !== 'base') {
    for (const [k, s] of arms) {
      const arm = P[k];
      if (arm && arm.front && arm.hx !== undefined) B.drawArm(ctx, A, P, T, armSpec(arm), s, light);
    }
  }
  ctx.restore();
  return { T, H, R };
}

function armSpec(a) {
  return { ...a, hand: [a.hx, a.hy] };
}

function drawHead(ctx, A, P, R, light, style, sway) {
  const skin = A.skin;
  // ears that sit behind the head silhouette
  for (const s of [-1, 1]) { const e = F.earInfo(R, s); if (!e.front) F.drawEar(ctx, A, R, s); }
  // skull + face shape
  const outline = F.headOutline(A, P, R);
  ctx.beginPath();
  F.smoothPath(ctx, outline, true, 0.9);
  ctx.fillStyle = col(skin);
  ctx.fill();
  ctx.save();
  ctx.clip();
  // form shading across the face
  const lx = light.x;
  const g = ctx.createLinearGradient(-0.5 * Math.sign(lx || -1) * -1, 0, 0.5 * Math.sign(lx || -1) * -1, 0);
  g.addColorStop(0, rgbStr(shade(skin, 0.06), 0.0));
  g.addColorStop(0.55, rgbStr(shade(skin, -0.25), 0.0));
  g.addColorStop(1, rgbStr(shade(skin, -0.35), 0.42));
  ctx.fillStyle = g;
  ctx.fillRect(-0.7, -0.8, 1.4, 1.6);
  // jaw/underside shadow
  const jg = ctx.createLinearGradient(0, 0.3, 0, 0.56);
  jg.addColorStop(0, rgbStr(shade(skin, -0.3), 0));
  jg.addColorStop(1, rgbStr(shade(skin, -0.3), 0.3));
  ctx.fillStyle = jg;
  ctx.fillRect(-0.7, 0.3, 1.4, 0.4);
  // warmth in the cheeks + emotional flush
  const blush = clamp(0.1 + (A.blushBase || 0) + (P.blush || 0) * 0.5);
  for (const s of [-1, 1]) {
    const c = F.pf(s * 0.245, 0.185, R, -0.02);
    const bg = ctx.createRadialGradient(c[0], c[1], 0.005, c[0], c[1], 0.11);
    bg.addColorStop(0, rgbStr(A.blushColor || [214, 110, 100], blush));
    bg.addColorStop(1, rgbStr(A.blushColor || [214, 110, 100], 0));
    ctx.fillStyle = bg;
    ctx.beginPath(); ctx.arc(c[0], c[1], 0.11, 0, Math.PI * 2); ctx.fill();
  }
  // age lines
  if ((A.age || 0) > 0.3) {
    ctx.strokeStyle = rgbStr(shade(skin, -0.32), 0.35 * A.age);
    ctx.lineWidth = 0.006; ctx.lineCap = 'round';
    for (const s of [-1, 1]) { // nasolabial folds
      const a = F.pf(s * 0.07, 0.2, R, 0.02), b = F.pf(s * 0.13, 0.27, R, 0.0), c = F.pf(s * 0.125, 0.33, R, 0.0);
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.quadraticCurveTo(b[0], b[1], c[0], c[1]); ctx.stroke();
    }
    if ((P.browIn || 0) + (P.browOut || 0) > 0.3 || A.age > 0.6) { // forehead lines
      const k = clamp(((P.browIn || 0) + (P.browOut || 0)) * 0.6 + (A.age - 0.6));
      ctx.strokeStyle = rgbStr(shade(skin, -0.3), 0.3 * k);
      for (const y of [-0.24, -0.29]) {
        const a = F.pf(-0.15, y, R, 0.02), b = F.pf(0, y - 0.012, R, 0.03), c = F.pf(0.15, y, R, 0.02);
        ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.quadraticCurveTo(b[0], b[1], c[0], c[1]); ctx.stroke();
      }
    }
  }
  ctx.restore();
  // shadow cast by the front hair onto the forehead
  if (style && style.front && !style.noShadow) {
    ctx.save();
    ctx.beginPath(); F.smoothPath(ctx, outline, true, 0.9); ctx.clip();
    ctx.translate(0.0, 0.03);
    ctx.globalAlpha = 0.28;
    const hairShadow = { ...A, hair: shade(skin, -0.45), hairShadowPass: true };
    style.front(ctx, hairShadow, R, sway);
    ctx.restore();
  }
  // rim light on one side (backlight from the scene): soft layered strokes,
  // faded in horizontally so it hugs the cheek and temple only
  if (opts_rim(P)) {
    const rim = P.rim;
    const side = rim.side || 1;
    ctx.save();
    ctx.beginPath(); F.smoothPath(ctx, outline, true, 0.9); ctx.clip();
    ctx.globalCompositeOperation = 'lighter';
    const c = rim.color, a = rim.a ?? 0.5;
    const gx = ctx.createLinearGradient(side * 0.12, 0, side * 0.48, 0);
    for (const [w, k] of [[0.11, 0.22], [0.06, 0.35], [0.025, 0.55]]) {
      const g = ctx.createLinearGradient(side * 0.12, 0, side * 0.48, 0);
      g.addColorStop(0, rgbStr(c, 0));
      g.addColorStop(1, rgbStr(c, a * k));
      ctx.strokeStyle = g;
      ctx.lineWidth = w;
      ctx.beginPath(); F.smoothPath(ctx, outline, true, 0.9); ctx.stroke();
    }
    ctx.restore();
  }
  // a crisp but soft outline
  ctx.beginPath();
  F.smoothPath(ctx, outline, true, 0.9);
  ctx.strokeStyle = rgbStr(shade(skin, -0.45), 0.55);
  ctx.lineWidth = 0.008;
  ctx.stroke();

  // features
  for (const s of [-1, 1]) F.drawEye(ctx, A, P, R, s);
  // frown lines between the brows
  const knit = clamp(P.browKnit || 0);
  if (knit > 0.25) {
    ctx.save();
    ctx.strokeStyle = rgbStr(shade(skin, -0.35), 0.45 * (knit - 0.25) / 0.75);
    ctx.lineWidth = 0.006; ctx.lineCap = 'round';
    for (const s of [-1, 1]) {
      const a = F.pf(s * 0.03, -0.1, R, 0.03), b = F.pf(s * 0.036, -0.045, R, 0.03);
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    }
    ctx.restore();
  }
  for (const s of [-1, 1]) F.drawBrow(ctx, A, P, R, s);
  F.drawNose(ctx, A, P, R, light);
  F.drawMouth(ctx, A, P, R);
  if (A.mustache) drawMustache(ctx, A, P, R);
  F.drawTears(ctx, A, P, R);
  for (const s of [-1, 1]) { const e = F.earInfo(R, s); if (e.front) F.drawEar(ctx, A, R, s); }
  if (style && style.front) style.front(ctx, A, R, sway);
  if (A.glasses) drawGlasses(ctx, A, P, R);
}

function opts_rim(P) { return P.rim && P.rim.color; }

// Character seen from behind (over-the-shoulder foregrounds). P.yaw turns the
// head so a sliver of cheek and ear shows on the side they look toward.
function drawBack(ctx, A, P0) {
  const P = normalizePose(P0);
  const S = P.scale;
  ctx.save();
  ctx.translate(P.x, P.y);
  ctx.scale(S, S);
  const T = B.torsoGeom(A, { ...P, bodyYaw: -P.bodyYaw });
  const main = (A.outfit && A.outfit.main) || '#555';
  B.torsoPath(ctx, T);
  ctx.fillStyle = col(shade(main, -0.12));
  ctx.fill();
  ctx.save(); B.torsoPath(ctx, T); ctx.clip();
  const g = ctx.createLinearGradient(-T.sw, 0, T.sw, 0);
  g.addColorStop(0, rgbStr(shade(main, -0.5), 0.35)); g.addColorStop(0.5, rgbStr(main, 0)); g.addColorStop(1, rgbStr(shade(main, -0.5), 0.45));
  ctx.fillStyle = g; ctx.fillRect(-2, -1, 4, 4);
  ctx.restore();
  const hx = T.cx + P.headX, hy = HEAD_Y + P.headY + P.slump * 0.09;
  ctx.fillStyle = col(shade(A.skin, -0.15));
  ctx.fillRect(hx - 0.12, hy + 0.3, 0.24, 0.5);
  ctx.save();
  ctx.translate(hx, hy + PIVOT); ctx.rotate(-(P.roll || 0)); ctx.translate(0, -PIVOT);
  // cheek / ear sliver on the side the head turns toward
  const yaw = clamp(P.yaw, -1, 1);
  if (Math.abs(yaw) > 0.05) {
    const s = Math.sign(yaw);
    ctx.fillStyle = col(A.skin);
    ctx.beginPath();
    ctx.ellipse(s * (0.36 - Math.abs(yaw) * 0.05), 0.12, 0.09 + Math.abs(yaw) * 0.06, 0.3, 0, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.fillStyle = col(A.hair);
  ctx.beginPath(); ctx.ellipse(0, -0.08, 0.47, 0.55, 0, 0, Math.PI * 2); ctx.fill();
  const style = STYLES[A.hairStyle];
  const R = F.rotation(0, 0);
  if (style) {
    const back = { ...A, hair: A.hair };
    style.back(ctx, back, R, P.sway || { x: 0, y: 0 });
    ctx.save(); ctx.globalAlpha = 0.9; ctx.fillStyle = col(A.hair);
    ctx.beginPath(); ctx.ellipse(0, -0.15, 0.5, 0.52, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  // a little sheen across the crown
  ctx.strokeStyle = rgbStr(shade(A.hair, 0.25), 0.25); ctx.lineWidth = 0.04; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(0, -0.05, 0.4, -2.4, -0.9); ctx.stroke();
  ctx.restore();
  ctx.restore();
}

function drawMustache(ctx, A, P, R) {
  const M = F.mouthGeom(A, P, R);
  const y = M.my - 0.035 - M.open * 0.15;
  const pts = [[-0.1, y + 0.03], [-0.07, y - 0.012], [0, y - 0.022], [0.07, y - 0.012], [0.1, y + 0.03], [0.05, y + 0.012], [0, y + 0.018], [-0.05, y + 0.012]]
    .map(([x, yy]) => F.pf(x, yy, R, 0.02));
  ctx.save();
  ctx.fillStyle = col(A.mustache);
  ctx.beginPath();
  F.smoothPath(ctx, pts, true, 0.8);
  ctx.fill();
  ctx.restore();
}

function drawGlasses(ctx, A, P, R) {
  ctx.save();
  ctx.strokeStyle = col(A.glasses);
  ctx.lineWidth = 0.014; ctx.lineJoin = 'round';
  const centers = [];
  for (const s of [-1, 1]) {
    const c = F.pf(s * 0.172, 0.04, R, 0.05);
    const inner = F.pf(s * 0.07, 0.04, R, 0.05), outer = F.pf(s * 0.29, 0.03, R, 0.0);
    const w = Math.abs(outer[0] - inner[0]) / 2;
    const cx = (outer[0] + inner[0]) / 2;
    centers.push([cx, c[1], w]);
    ctx.beginPath();
    roundedRect(ctx, cx - w, c[1] - 0.075, w * 2, 0.15, 0.04);
    ctx.stroke();
    // lens glare
    ctx.save();
    ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 0.012;
    ctx.beginPath(); ctx.moveTo(cx - w * 0.5, c[1] + 0.04); ctx.lineTo(cx - w * 0.1, c[1] - 0.05); ctx.stroke();
    ctx.restore();
  }
  // bridge
  ctx.beginPath();
  ctx.moveTo(centers[0][0] + centers[0][2], centers[0][1] - 0.02);
  ctx.quadraticCurveTo((centers[0][0] + centers[1][0]) / 2, centers[0][1] - 0.05, centers[1][0] - centers[1][2], centers[1][1] - 0.02);
  ctx.stroke();
  ctx.restore();
}
function roundedRect(ctx, x, y, w, h, r) {
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
}

module.exports = { drawCharacter, drawBack, headPlacement, normalizePose, POSE_DEFAULTS, HEAD_Y, PIVOT };
