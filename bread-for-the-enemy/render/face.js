// 2.5D anime head rig.
// Head space: x right, y down, z toward viewer. Unit = half the face width.
// Eye line at y=0, chin ~ y=1.33, skull top ~ y=-1.38.
'use strict';
const L = require('./lib');
const { clamp, lerp, mix, rgba, shade } = L;

// ------------------------------------------------------------------ projection
function makeProj(H) {
  const cy = Math.cos(H.yaw), sy = Math.sin(H.yaw);
  const cp = Math.cos(H.pitch), sp = Math.sin(H.pitch);
  const cr = Math.cos(H.roll), sr = Math.sin(H.roll);
  const s = H.s;
  const P = (x, y, z) => {
    const x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
    const y2 = y * cp + z1 * sp, z2 = -y * sp + z1 * cp;
    return [H.x + (x1 * cr - y2 * sr) * s, H.y + (x1 * sr + y2 * cr) * s, z2];
  };
  // silhouette-aware projection for contour points: far side wraps forward
  const Pc = (x, y, z) => {
    const far = Math.sign(x) === Math.sign(H.yaw) && Math.abs(H.yaw) > 0.001;
    const zz = far ? z + 0.55 * Math.abs(sy) : z;
    return P(x, y, zz);
  };
  return { P, Pc, s, H };
}

// default face geometry (can be overridden per character via style.geo)
const GEO = {
  eyeX: 0.45, eyeY: 0.02, eyeZ: 0.78, eyeW: 0.265, eyeH: 1.0, // eyeH scales lid heights
  browY: -0.32, browW: 0.075,
  noseY: 0.48, noseLen: 1.0,
  mouthY: 0.84, mouthW: 0.22,
  chinY: 1.33, jawW: 0.70, jawY: 0.92, cheekW: 0.97,
  craniumY: -0.38, craniumR: 1.0,
  neckW: 0.55,
};

// Face geometry for a character: the stock head plus its own overrides. Adults then get more lifelike
// proportions than a stock anime head: fuller cheeks, a broader jaw and chin, a slightly longer lower
// face (so the forehead reads smaller), smaller eyes and a bigger nose. The child keeps its round face.
function geoOf(st) {
  const G = Object.assign({}, GEO, st.geo || {});
  if (st.child) { G.jawW = Math.min(G.jawW, 0.74); G.cheekLow = 0.9; G.chinW = 0.5; return G; }
  const fem = st.fem || st.name === 'phoebe';
  G.jawW = Math.min(0.82, G.jawW * (fem ? 1.04 : 1.09));
  G.jawY += 0.04; G.chinY += fem ? 0.03 : 0.06; G.mouthY += fem ? 0.02 : 0.04; G.noseY += 0.02;
  G.eyeW *= fem ? 0.95 : 0.92; G.noseLen *= fem ? 1.1 : 1.15;
  G.cheekLow = fem ? 0.94 : 0.93; G.chinW = (st.geo && st.geo.chinW) || (fem ? 0.47 : 0.48);
  return G;
}

function faceContour(G, open) {
  // right side from temple to chin (x>0), then mirrored; z = depth
  const jd = open * 0.13; // jaw drop
  const cw = G.cheekW;
  const R = [
    [0.96 * cw, -0.62, 0.05],
    [0.98 * cw, -0.1, 0.18],
    [0.96 * cw, 0.28, 0.22],
    [(G.cheekLow || 0.88) * cw, 0.6, 0.2],
    [G.jawW, G.jawY + jd * 0.5, 0.24],
    [G.chinW || 0.44, G.chinY - 0.2 + jd * 0.9, 0.48],
    [(G.chinW || 0.44) * 0.5, G.chinY - 0.04 + jd, 0.64],
  ];
  const chin = [0, G.chinY + jd, 0.68];
  const left = R.map(([x, y, z]) => [-x, y, z]);
  return { R, left, chin };
}

// --------------------------------------------------------------- the head
function drawHead(ctx, H, st, F, Lt, extra = {}) {
  const pr = makeProj(H);
  const { P, Pc, s } = pr;
  const G = geoOf(st);
  const open = F.mouthOpen;
  pr.t = extra.t || 0;

  // colours (lighting)
  const pale = F.pale || 0;
  const skinBase = mix(st.skin, '#d8d0cc', pale * 0.45);
  const skin = L.mul(skinBase, Lt.key || '#ffffff');
  const skinSh = mix(skin, L.mul(mix(st.skinShadow, '#a89ca8', pale * 0.3), Lt.amb || '#ffffff'), 0.8);
  const line = st.line || '#3a2420';
  const lw = (Lt.lineW || 1) * s * 0.02;

  // contour
  const C = faceContour(G, open);
  const lowerR = C.R.map((p) => Pc(...p));
  const lowerL = C.left.map((p) => Pc(...p));
  const chinP = P(...C.chin);
  // face polygon: left temple -> down to chin -> up right side -> over forehead
  const facePoly = [...lowerL, chinP, ...lowerR.slice().reverse()];
  const crC = P(0, G.craniumY, -0.1);
  const crR = G.craniumR * s;

  // face polygon is traced counter-clockwise on screen; the cranium ellipse must
  // use the same winding so the nonzero union fills (and clips) both parts
  const faceClip = () => {
    ctx.beginPath();
    L.crPath(ctx, facePoly, false, 0.5);
    ctx.lineTo(facePoly[0][0], facePoly[0][1]);
    ctx.closePath();
    ctx.moveTo(crC[0] + crR, crC[1]);
    ctx.ellipse(crC[0], crC[1], crR, crR * 1.02, H.roll, 0, -L.TAU, true);
  };

  // ---------------- back hair / behind-head items
  if (st.hairBack) st.hairBack(ctx, pr, st, F, Lt, extra);

  // ---------------- neck, then the body/clothes over the neck base
  if (!extra.noNeck) drawNeck(ctx, pr, st, F, Lt, skin, skinSh, line, lw, G, extra);
  if (extra.drawBody) extra.drawBody(pr);

  // ---------------- ears
  drawEars(ctx, pr, st, skin, skinSh, line, lw);

  // ---------------- skin, with the head's silhouette outlined as ONE shape (face + skull), so no
  // part of the face contour can ever show as a stray line across the temple, cheek or scalp
  ctx.save();
  faceClip();
  if (!st.noFaceLine) {
    ctx.strokeStyle = line; ctx.lineWidth = lw * 2.2; ctx.lineJoin = 'round';
    ctx.stroke();
  }
  ctx.fillStyle = skin;
  ctx.fill('nonzero');
  ctx.restore();

  // cel shadow (side away from light)
  ctx.save();
  faceClip();
  ctx.clip('nonzero');
  drawCelShadow(ctx, pr, G, F, Lt, skinSh, st);
  // warm cheeks / blush
  const blush = (st.blush || 0.15) + (F.blush || 0) + (F.tears || 0) * 0.35;
  if (blush > 0.01) {
    for (const sd of [-1, 1]) {
      const c = P(sd * 0.55, 0.42, 0.7);
      ctx.fillStyle = L.radial(ctx, c[0], c[1], 0, s * 0.32, [[0, rgba(st.blushColor || '#e0707a', 0.28 * blush)], [1, rgba('#e0707a', 0)]]);
      ctx.fillRect(c[0] - s * 0.4, c[1] - s * 0.4, s * 0.8, s * 0.8);
    }
    // reddened nose when crying
    if ((F.tears || 0) > 0.3) {
      const n = P(0, 0.45, 1.05);
      ctx.fillStyle = L.radial(ctx, n[0], n[1], 0, s * 0.16, [[0, rgba('#e06a6a', 0.3 * F.tears)], [1, rgba('#e06a6a', 0)]]);
      ctx.fillRect(n[0] - s * 0.2, n[1] - s * 0.2, s * 0.4, s * 0.4);
    }
  }
  // cheekbones: soft light across the lit one, a soft hollow under the other (adults)
  if (!st.child) {
    const side = Lt.side || -1;
    const cb = P(side * 0.6, 0.16, 0.78);
    ctx.fillStyle = L.radial(ctx, cb[0], cb[1], 0, s * 0.34, [[0, rgba('#fff4ea', 0.13)], [1, rgba('#fff4ea', 0)]]);
    ctx.fillRect(cb[0] - s * 0.4, cb[1] - s * 0.4, s * 0.8, s * 0.8);
    const ho = P(-side * 0.66, 0.6, 0.7);
    ctx.fillStyle = L.radial(ctx, ho[0], ho[1], 0, s * 0.36, [[0, rgba(skinSh, 0.22 + 0.12 * (st.age || 0))], [1, rgba(skinSh, 0)]]);
    ctx.fillRect(ho[0] - s * 0.4, ho[1] - s * 0.4, s * 0.8, s * 0.8);
  }
  // ambient occlusion around eye sockets for older/weary faces
  const sock = (st.age || 0) * 0.5 + (F.weary || 0) * 0.3 + 0.12;
  for (const sd of [-1, 1]) {
    const c = P(sd * G.eyeX, -0.12, G.eyeZ);
    ctx.fillStyle = L.radial(ctx, c[0], c[1], s * 0.05, s * 0.38, [[0, rgba(skinSh, 0.0)], [0.55, rgba(skinSh, 0.35 * sock)], [1, rgba(skinSh, 0)]]);
    ctx.fillRect(c[0] - s * 0.45, c[1] - s * 0.45, s * 0.9, s * 0.9);
  }
  if (st.hairShadow) st.hairShadow(ctx, pr, st, F, Lt, skinSh);
  ctx.restore();

  // ---------------- age lines and expression lines
  drawLines(ctx, pr, G, st, F, skinSh, line, lw);


  // ---------------- beard base (under mouth)
  if (st.beard) st.beard(ctx, pr, st, F, Lt, 'base', G);

  // ---------------- nose
  drawNose(ctx, pr, G, st, F, Lt, skinSh, line, lw);

  // ---------------- mouth
  drawMouth(ctx, pr, G, st, F, Lt, skin, skinSh, line, lw);

  // ---------------- mustache
  if (st.beard) st.beard(ctx, pr, st, F, Lt, 'top', G);


  // ---------------- eyes
  for (const sd of [-1, 1]) drawEye(ctx, pr, G, st, F, Lt, sd, line, lw);
  // tears on cheeks
  if ((F.tearFlow || 0) > 0.01) drawTears(ctx, pr, G, F, extra.t || 0);
  if (F.tearDrop != null && F.tearDrop > -1) drawSingleTear(ctx, pr, G, F);

  // ---------------- brows
  for (const sd of [-1, 1]) drawBrow(ctx, pr, G, st, F, sd, line, lw);


  // ---------------- front hair, headwear
  if (st.hairFront) st.hairFront(ctx, pr, st, F, Lt, extra);

  return pr;
}

function drawCraniumLine(ctx, pr, G, line, lw) {
  // the outline of a bald head follows the same skull ellipse that is filled for the scalp, from
  // temple to temple over the top (never across the face, whatever the head turn)
  const { P, s, H } = pr;
  const c = P(0, G.craniumY, -0.1);
  const R = G.craniumR * s;
  const a = Math.asin(clamp((-0.62 - G.craniumY) / (G.craniumR * 1.02), -1, 1));
  ctx.save();
  ctx.strokeStyle = line; ctx.lineWidth = lw * 1.0; ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.ellipse(c[0], c[1], R, R * 1.02, H.roll, Math.PI - a, L.TAU + a, false);
  ctx.stroke();
  ctx.restore();
}

function drawNeck(ctx, pr, st, F, Lt, skin, skinSh, line, lw, G, extra = {}) {
  const { P, s, H } = pr;
  // The neck is a column standing on the body's own axis, straight under the head (it never leans
  // toward the front of the collar, which shifts as the body turns). Its two sides are built once
  // and used both to fill it and to outline it, so no line can stray off its edge.
  const PathC = require('@napi-rs/canvas').Path2D;
  const nw = G.neckW * s;
  const ax = H.x + (H.neckDX || 0);
  const by = extra.neckBase ? extra.neckBase[1] : H.y + s * 2.25;
  const top = P(0, 0.95, -0.25);
  const side = -(Lt.side || -1);
  const sideOf = (sd) => {
    const t0 = [top[0] + sd * nw * 0.95, top[1] - s * 0.35];
    const t1 = [ax + sd * nw * 1.0, by - s * 0.2];
    return {
      t0, t1,
      c1: [lerp(t0[0], t1[0], 0.35) - sd * nw * 0.05, lerp(t0[1], t1[1], 0.35)],
      c2: [lerp(t0[0], t1[0], 0.75) - sd * nw * 0.02, lerp(t0[1], t1[1], 0.75)],
      sh: [ax + sd * nw * 1.55, by + s * 0.42],
    };
  };
  const Ls = sideOf(-1), Rs = sideOf(1);
  const shape = new PathC();
  shape.moveTo(Ls.t0[0], Ls.t0[1]);
  shape.bezierCurveTo(Ls.c1[0], Ls.c1[1], Ls.c2[0], Ls.c2[1], Ls.t1[0], Ls.t1[1]);
  // below the collar line the skin runs out under the clothes along the slope of the shoulders
  // (just under the cloth's own shoulder line), so the collar opening never shows anything but
  // skin whichever way the body turns, and no skin pokes out above the shoulders
  const cL = extra.collar ? extra.collar[0] : [Ls.t1[0], Ls.t1[1]];
  const cR = extra.collar ? extra.collar[extra.collar.length - 1] : [Rs.t1[0], Rs.t1[1]];
  const xl = Math.min(cL[0], Ls.t1[0]), xr = Math.max(cR[0], Rs.t1[0]);
  const SL = extra.shoulderL, SR = extra.shoulderR;
  if (SL && SR) {
    // follow the clothes' own shoulder lines a little below them, whichever way the body turns
    shape.quadraticCurveTo(xl, cL[1] + s * 0.05, SL[1][0], SL[1][1] + s * 0.16);
    shape.lineTo(SL[2][0], SL[2][1] + s * 0.2);
    shape.lineTo(SL[2][0], by + s * 0.9);
    shape.lineTo(SR[2][0], by + s * 0.9);
    shape.lineTo(SR[2][0], SR[2][1] + s * 0.2);
    shape.lineTo(SR[1][0], SR[1][1] + s * 0.16);
  } else {
    shape.quadraticCurveTo(xl, cL[1] + s * 0.05, xl - s * 0.7, cL[1] + s * 0.44);
    shape.lineTo(xl - s * 0.7, by + s * 0.9);
    shape.lineTo(xr + s * 0.7, by + s * 0.9);
    shape.lineTo(xr + s * 0.7, cR[1] + s * 0.44);
  }
  shape.quadraticCurveTo(xr, cR[1] + s * 0.05, Rs.t1[0], Rs.t1[1]);
  shape.bezierCurveTo(Rs.c2[0], Rs.c2[1], Rs.c1[0], Rs.c1[1], Rs.t0[0], Rs.t0[1]);
  shape.closePath();
  if (extra.collar) {
    // the chest skin visible inside the neck hole (slightly larger than the hole, under its edge)
    const c = extra.collar, cx = (c[0][0] + c[c.length - 1][0]) / 2;
    const grown = c.map(([x, y]) => [cx + (x - cx) * 1.12, y + s * 0.06]);
    L.crPath(shape, grown, false, 0.5);
    shape.closePath();
  }
  ctx.save();
  ctx.fillStyle = skin;
  ctx.fill(shape, 'nonzero');
  ctx.clip(shape, 'nonzero');
  // shadow under the jaw: deepest right under it, softly falling off down the neck
  const ch = P(0, 1.12, 0.3);
  const gj = ctx.createLinearGradient(0, ch[1] - s * 0.1, 0, ch[1] + s * 0.62);
  gj.addColorStop(0, rgba(skinSh, 0.82)); gj.addColorStop(0.55, rgba(skinSh, 0.35)); gj.addColorStop(1, rgba(skinSh, 0));
  ctx.fillStyle = gj;
  ctx.fillRect(ax - nw * 3, ch[1] - s * 1.2, nw * 6, s * 1.85);
  // side shadow down the neck and onto the chest
  const g = ctx.createLinearGradient(ax - side * nw * 0.1, 0, ax + side * nw * 1.0, 0);
  g.addColorStop(0, rgba(skinSh, 0)); g.addColorStop(0.4, rgba(skinSh, 0.6)); g.addColorStop(1, rgba(skinSh, 0.75));
  ctx.fillStyle = g;
  ctx.fillRect(ax - nw * 3, top[1] - s * 0.5, nw * 6, s * 4);
  // the two neck muscles (sterno-cleido-mastoid): a soft V from behind each ear down to the notch
  // between the collarbones, a gentle shadow line with a little light beside it
  ctx.lineCap = 'round';
  for (const sd of [-1, 1]) {
    const m0 = P(sd * 0.6, 0.78, -0.18), m1 = [ax + sd * s * 0.1, by - s * 0.04];
    const mc = [lerp(m0[0], m1[0], 0.5) + sd * s * 0.05, lerp(m0[1], m1[1], 0.5)];
    const gm = ctx.createLinearGradient(m0[0], m0[1], m1[0], m1[1]);
    gm.addColorStop(0, rgba(skinSh, 0)); gm.addColorStop(0.3, rgba(skinSh, st.child ? 0.18 : 0.4)); gm.addColorStop(1, rgba(skinSh, 0.15));
    ctx.strokeStyle = gm; ctx.lineWidth = lw * 1.3;
    ctx.beginPath(); ctx.moveTo(m0[0], m0[1]); ctx.quadraticCurveTo(mc[0], mc[1], m1[0], m1[1]); ctx.stroke();
    const gl = ctx.createLinearGradient(m0[0], m0[1], m1[0], m1[1]);
    gl.addColorStop(0, rgba('#fff4ea', 0)); gl.addColorStop(0.4, rgba('#fff4ea', sd === -side ? 0.05 : 0.13)); gl.addColorStop(1, rgba('#fff4ea', 0));
    ctx.strokeStyle = gl; ctx.lineWidth = lw * 2.6;
    ctx.beginPath(); ctx.moveTo(m0[0] - sd * s * 0.07, m0[1]); ctx.quadraticCurveTo(mc[0] - sd * s * 0.08, mc[1], m1[0] - sd * s * 0.07, m1[1] - s * 0.04); ctx.stroke();
  }
  // soft shading at the notch between the collarbones
  ctx.fillStyle = L.radial(ctx, ax, by + s * 0.12, 0, s * 0.36, [[0, rgba(skinSh, 0.45)], [1, rgba(skinSh, 0)]]);
  ctx.fillRect(ax - s, by - s * 0.4, s * 2, s);
  ctx.restore();
  // outline: the same sides, fading in below the jaw so nothing pokes out from under it
  for (const S2 of [Ls, Rs]) {
    const go = ctx.createLinearGradient(S2.t0[0], S2.t0[1], S2.t1[0], S2.t1[1]);
    go.addColorStop(0, rgba(line, 0)); go.addColorStop(0.35, rgba(line, 0.9)); go.addColorStop(1, rgba(line, 0.9));
    ctx.strokeStyle = go; ctx.lineWidth = lw * 0.85;
    ctx.beginPath(); ctx.moveTo(S2.t0[0], S2.t0[1]); ctx.bezierCurveTo(S2.c1[0], S2.c1[1], S2.c2[0], S2.c2[1], S2.t1[0], S2.t1[1]); ctx.stroke();
  }
  if (st.adamsApple !== false && !st.child) {
    const a = [lerp(top[0], ax, 0.5), lerp(top[1], by, 0.42)];
    ctx.globalAlpha = 0.4;
    ctx.strokeStyle = line;
    ctx.beginPath();
    ctx.moveTo(a[0] - s * 0.04, a[1]);
    ctx.quadraticCurveTo(a[0], a[1] + s * 0.06, a[0] + s * 0.05, a[1] - s * 0.01);
    ctx.lineWidth = lw * 0.7;
    ctx.stroke();
    ctx.globalAlpha = 1;
  }
}

function drawEars(ctx, pr, st, skin, skinSh, line, lw) {
  const { P, s, H } = pr;
  if (st.noEars) return;
  for (const sd of [-1, 1]) {
    // hide the far ear when turned
    const far = Math.sign(sd) === Math.sign(H.yaw);
    const fade = far ? clamp((0.44 - Math.abs(H.yaw)) / 0.18) : 1;
    if (fade <= 0.01) continue;
    ctx.save();
    ctx.globalAlpha *= fade;
    const pts = [[sd * 0.95, -0.02, -0.02], [sd * 1.12, -0.06, -0.12], [sd * 1.16, 0.18, -0.15], [sd * 1.06, 0.42, -0.1], [sd * 0.94, 0.5, -0.02]].map((p) => P(...p));
    ctx.beginPath();
    L.crPath(ctx, pts, false);
    ctx.closePath();
    ctx.fillStyle = far ? skinSh : skin;
    ctx.fill();
    ctx.strokeStyle = line;
    ctx.lineWidth = lw * 0.9;
    ctx.stroke();
    const inner = [[sd * 1.03, 0.04, -0.1], [sd * 1.08, 0.2, -0.13], [sd * 1.0, 0.36, -0.08]].map((p) => P(...p));
    L.strokeSmooth(ctx, inner, rgba(line, 0.6), lw * 0.7);
    ctx.restore();
  }
}

function terminatorX(H, Lt) {
  const side = Lt.side || -1;
  const wrap = Lt.wrap == null ? 0.72 : Lt.wrap;
  return -side * Math.sin(wrap + side * H.yaw);
}
// fill the shadow side of the head (curved terminator) — used inside clipped hair/beard shapes
function shadowSide(ctx, pr, Lt, color, off = 0) {
  const { P, H } = pr;
  const side = Lt.side || -1;
  const xt = terminatorX(H, Lt) + off * -side;
  const ys = [-2.2, -1.42, -1.0, -0.5, 0, 0.6, 1.2, 2.0, 3.5];
  const pts = ys.map((y) => {
    const sk = y < -0.6 ? Math.sqrt(clamp(1 - Math.pow((y + 0.38) / 1.3, 2), 0.1, 1)) : 1;
    return P(clamp(xt * sk, -1.3, 1.3), y, 0.9);
  });
  const edge = side < 0 ? 4 : -4;
  ctx.save();
  ctx.filter = `blur(${(pr.s * 0.06).toFixed(3)}px)`;
  ctx.beginPath();
  L.crPath(ctx, pts, false);
  const e1 = P(edge, 3.5, 0), e2 = P(edge, -2.2, 0);
  ctx.lineTo(e1[0], e1[1]);
  ctx.lineTo(e2[0], e2[1]);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.restore();
}

function drawCelShadow(ctx, pr, G, F, Lt, skinSh, st) {
  const { P, s, H } = pr;
  const side = Lt.side || -1; // -1: light from screen-left
  const xt = terminatorX(H, Lt);
  const k = Lt.shadow == null ? 0.72 : Lt.shadow;
  // terminator path (head space): curves into the eye socket, around the
  // cheekbone and under it, then follows the jaw; wraps toward the crown
  const ys = [-1.45, -1.1, -0.75, -0.42, -0.12, 0.18, 0.42, 0.7, 1.0, 1.3, 1.7];
  const bump = [0.32, 0.16, 0.08, -0.04, -0.2, -0.04, 0.12, -0.06, 0.02, -0.02, -0.08];
  const term = (off) => ys.map((y, i) => {
    const sk = y < -0.75 ? Math.sqrt(clamp(1 - Math.pow((y + 0.38) / 1.15, 2), 0.05, 1)) : 1;
    const x = (xt + off + bump[i] * -side * 1.0) * sk + (y < -0.75 ? -side * (1 - sk) * 0.5 : 0);
    // keep a minimum band near the contour so the far cheek always reads as turned
    const lim = side < 0 ? Math.min(x, 0.78) : Math.max(x, -0.78);
    return [clamp(lim, -1.2, 1.2), y, 0.95 * Math.sqrt(Math.max(0, 1 - Math.pow(lim / 1.05, 2))) + 0.05];
  });
  const edge = side < 0 ? 1.6 : -1.6;
  // the shadow's edge is soft: the shape is laid down blurred, so the skin fades from light into shade
  // instead of stopping at a hard line (the face's outline still clips it)
  const tp = term(0).map((p) => P(...p));
  ctx.save();
  ctx.filter = `blur(${(s * 0.07).toFixed(3)}px)`;
  ctx.beginPath();
  L.crPath(ctx, tp, false);
  const e1 = P(edge, 1.8, 0), e2 = P(edge, -1.6, 0);
  ctx.lineTo(e1[0], e1[1]); ctx.lineTo(e2[0], e2[1]);
  ctx.closePath();
  ctx.fillStyle = rgba(skinSh, k);
  ctx.fill();
  ctx.restore();
  // soft core-shadow gradient along the terminator (painterly falloff)
  const tm = P(xt, 0.0, 0.95);
  const g = ctx.createLinearGradient(tm[0] + side * s * 0.3, 0, tm[0] - side * s * 0.02, 0);
  g.addColorStop(0, rgba(skinSh, 0));
  g.addColorStop(1, rgba(skinSh, 0.18 * k));
  ctx.fillStyle = g;
  ctx.fillRect(tm[0] - s * 1.5, tm[1] - s * 2, s * 3, s * 4);
  // nose cast shadow
  const nl = G.noseLen;
  const n0 = P(0, 0.2 * nl, 1.0), n1 = P(0, 0.52 * nl, 1.14), n2 = P(-side * 0.2, 0.6 * nl, 0.96);
  ctx.beginPath();
  ctx.moveTo(n0[0], n0[1]);
  ctx.lineTo(n1[0], n1[1]);
  ctx.lineTo(n2[0], n2[1]);
  ctx.closePath();
  ctx.fillStyle = rgba(skinSh, 0.6 * k);
  ctx.fill();
  // under-lip / chin shading
  const c = P(0, G.chinY - 0.25 + F.mouthOpen * 0.12, 0.7);
  ctx.fillStyle = L.radial(ctx, c[0], c[1], 0, s * 0.25, [[0, rgba(skinSh, 0.35 * k)], [1, rgba(skinSh, 0)]]);
  ctx.fillRect(c[0] - s * 0.3, c[1] - s * 0.3, s * 0.6, s * 0.6);
}

function drawLines(ctx, pr, G, st, F, skinSh, line, lw) {
  const { P, s } = pr;
  const age = st.age || 0;
  const lc = mix(skinSh, line, 0.45);
  ctx.save();
  ctx.lineCap = 'round';
  // forehead lines: age + worry
  const fh = clamp(age * 0.7 + Math.max(0, F.browInner) * 0.5 + Math.max(0, F.browHeight) * 0.4);
  if (fh > 0.05 && !st.noForehead) {
    for (let i = 0; i < 3; i++) {
      const y = -0.72 - i * 0.12;
      const w = 0.38 - i * 0.05;
      const pts = [P(-w, y + 0.03, 0.88), P(0, y - 0.02 * (F.browInner || 0), 0.95), P(w, y + 0.03, 0.88)];
      L.strokeSmooth(ctx, pts, rgba(lc, 0.55 * fh), lw * 0.6);
    }
  }
  // brow furrow verticals
  const fu = clamp(F.browFurrow || 0);
  if (fu > 0.1) {
    for (const sd of [-1, 1]) {
      const pts = [P(sd * 0.07, -0.42, 0.97), P(sd * 0.09, -0.27, 0.97), P(sd * 0.07, -0.18, 0.97)];
      L.strokeSmooth(ctx, pts, rgba(lc, 0.7 * fu), lw * 0.7);
    }
  }
  // under-eye bags, crow's feet
  if (age > 0.2) {
    for (const sd of [-1, 1]) {
      const ex = sd * G.eyeX;
      L.strokeSmooth(ctx, [P(ex - sd * 0.15, 0.2, 0.8), P(ex, 0.27, 0.8), P(ex + sd * 0.17, 0.2, 0.74)], rgba(lc, 0.5 * age), lw * 0.6);
      for (let i = 0; i < 3; i++) {
        const y0 = -0.04 + i * 0.07;
        L.strokeSmooth(ctx, [P(sd * (G.eyeX + 0.29), y0, 0.6), P(sd * (G.eyeX + 0.39), y0 + (i - 1) * 0.04, 0.5)], rgba(lc, 0.45 * age), lw * 0.5);
      }
    }
  }
  // nasolabial folds: age + smile + cry
  const nl = clamp(age * 0.6 + Math.max(0, F.mouthSmile) * 0.5 + (F.cheekRaise || 0) * 0.4 + (F.tears || 0) * 0.15) * (st.child ? 0.3 : 1);
  if (nl > 0.08 && !st.beardHidesFolds) {
    for (const sd of [-1, 1]) {
      const pts = [P(sd * 0.2, 0.42, 0.98), P(sd * 0.33, 0.62, 0.88), P(sd * (0.33 + 0.04 * F.mouthSmile), 0.82, 0.82)];
      L.strokeSmooth(ctx, pts, rgba(lc, 0.55 * nl), lw * 0.7);
    }
  }
  // cheek raise arcs (smiling eyes)
  const cr = clamp(F.cheekRaise || 0);
  if (cr > 0.15) {
    for (const sd of [-1, 1]) {
      const ex = sd * G.eyeX;
      L.strokeSmooth(ctx, [P(ex - sd * 0.12, 0.3, 0.82), P(ex + sd * 0.05, 0.34, 0.8), P(ex + sd * 0.2, 0.28, 0.74)], rgba(lc, 0.4 * cr), lw * 0.55);
    }
  }
  ctx.restore();
}

function drawNose(ctx, pr, G, st, F, Lt, skinSh, line, lw) {
  const { P, s, H } = pr;
  const nl = G.noseLen;
  const side = Lt.side || -1;
  const turn = clamp(Math.abs(H.yaw) * 2.6);
  const sd = H.yaw >= 0 ? 1 : -1; // the side the face turns toward: the profile of the nose shows there
  const kid = st.child ? 0.7 : 1;
  ctx.save();
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  // soft form shadow on the shadow side of the lower nose and under the tip
  const shSide = -side;
  const sh = P(shSide * 0.11, 0.42 * nl, 1.04);
  ctx.fillStyle = L.radial(ctx, sh[0], sh[1], 0, s * 0.13, [[0, rgba(skinSh, 0.3 * kid)], [1, rgba(skinSh, 0)]]);
  ctx.fillRect(sh[0] - s * 0.2, sh[1] - s * 0.2, s * 0.4, s * 0.4);
  const under = P(0, 0.6 * nl, 1.04);
  ctx.fillStyle = L.radial(ctx, under[0], under[1], 0, s * 0.13, [[0, rgba(skinSh, 0.38 * kid)], [1, rgba(skinSh, 0)]]);
  ctx.fillRect(under[0] - s * 0.2, under[1] - s * 0.2, s * 0.4, s * 0.4);
  // bridge: from the front only a faint line down the lower nose; when the head turns, the profile
  // line of the whole bridge
  const bx = turn > 0.05 ? sd : shSide;
  const y0 = lerp(0.24, -0.02, turn);
  const bridge = [P(bx * 0.07, y0 * nl, 1.0 + y0 * 0.2), P(bx * 0.065, (0.3 + y0 * 0.2) * nl, 1.08), P(bx * 0.045, 0.45 * nl, 1.14)];
  L.strokeSmooth(ctx, bridge, rgba(line, (0.2 + 0.45 * turn) * kid), lw * 0.75);
  // rounded tip: the underside curve from wing to wing (the near half stronger when turned)
  const tip = [P(-0.075, 0.545 * nl, 1.1), P(-0.03, 0.585 * nl, 1.15), P(0.03, 0.585 * nl, 1.15), P(0.075, 0.545 * nl, 1.1)];
  L.strokeSmooth(ctx, tip, rgba(line, 0.7), lw * 0.8);
  // nostril wings: a soft curve round each side of the tip (the far one fades as the head turns)
  for (const w of [-1, 1]) {
    const k = w === sd ? 1 - 0.85 * turn : 1;
    if (k < 0.05) continue;
    const wing = [P(w * 0.1, 0.43 * nl, 1.02), P(w * 0.14, 0.51 * nl, 1.01), P(w * 0.1, 0.575 * nl, 1.04)];
    L.strokeSmooth(ctx, wing, rgba(line, 0.5 * k * kid), lw * 0.7);
    const n = P(w * 0.055, 0.565 * nl, 1.09);
    ctx.fillStyle = rgba(line, 0.42 * k);
    L.ellipse(ctx, n[0], n[1], s * 0.026 * kid, s * 0.013 * kid, H.roll + w * 0.35);
    ctx.fill();
  }
  // light on the bridge and the tip
  const hl = P(side * 0.025, 0.32 * nl, 1.1);
  ctx.fillStyle = rgba('#ffffff', 0.13);
  L.ellipse(ctx, hl[0], hl[1], s * 0.02, s * 0.055, H.roll);
  ctx.fill();
  const ht = P(side * 0.02, 0.5 * nl, 1.15);
  ctx.fillStyle = rgba('#ffffff', 0.2);
  L.ellipse(ctx, ht[0], ht[1], s * 0.03, s * 0.022, H.roll);
  ctx.fill();
  ctx.restore();
}

// ------------------------------------------------------------------ mouth
function drawMouth(ctx, pr, G, st, F, Lt, skin, skinSh, line, lw) {
  const { P, s, t } = pr;
  const o = clamp(F.mouthOpen, 0, 1.2);
  const wide = clamp(F.mouthWide || 0, -1, 1);
  const smile = clamp(F.mouthSmile || 0, -1, 1);
  const press = clamp(F.mouthPress || 0);
  const asym = F.mouthAsym || 0;
  const trem = (F.mouthTremble || 0) * (F._trem || 0);
  const my = G.mouthY;
  let mw = G.mouthW * (1 + 0.28 * wide + 0.12 * Math.max(0, smile) - 0.12 * press);
  if (wide < 0) mw *= 1 + 0.15 * wide; // rounding narrows
  // talking without smiling: the corners sink as the jaw drops and the upper lip lifts a little, so the
  // open mouth is an oval and never the flat-topped crescent of a grin
  const neutral = clamp((0.2 - smile) / 0.4);
  const cy = (sd) => my - smile * 0.075 - asym * sd * 0.05 + trem * 0.012 * sd + o * 0.07 * neutral;
  const cL = P(-mw, cy(-1), 0.8 - mw * 0.3);
  const cR = P(mw, cy(1), 0.8 - mw * 0.3);
  const upY = my - o * (0.05 + 0.05 * neutral) - (wide < 0 ? -wide * o * 0.03 : 0) - smile * 0.02;
  const loY = my + o * 0.3 + (wide < 0 ? 0.02 * -wide : 0) + trem * 0.02;
  const roundness = wide < 0 ? -wide : 0;
  const upC = P(0, upY, 0.93);
  const loC = P(0, loY, 0.9);
  const upL = P(-mw * 0.55, upY + 0.01 - smile * 0.03, 0.88);
  const upR = P(mw * 0.55, upY + 0.01 - smile * 0.03, 0.88);
  const loL = P(-mw * (0.55 + 0.15 * roundness), lerp(my, loY, 0.85), 0.86);
  const loR = P(mw * (0.55 + 0.15 * roundness), lerp(my, loY, 0.85), 0.86);
  if (st.lips) {
    // soft lip colour (female characters)
    const lipC = L.mul(st.lips, Lt.key || '#ffffff');
    const uT = P(0, my - 0.06 - o * 0.05, 0.93), lB = P(0, my + 0.1 + o * 0.3, 0.9);
    ctx.save();
    ctx.globalAlpha = 0.55;
    ctx.fillStyle = lipC;
    ctx.beginPath();
    L.crPath(ctx, [cL, P(-mw * 0.5, my - 0.055 - o * 0.05, 0.9), uT, P(mw * 0.5, my - 0.055 - o * 0.05, 0.9), cR,
      P(mw * 0.5, my + 0.085 + o * 0.28, 0.88), lB, P(-mw * 0.5, my + 0.085 + o * 0.28, 0.88)], true, 0.5);
    ctx.fill();
    ctx.restore();
  }
  if (o < 0.06) {
    // closed: a single expressive line
    const mid = P(0, my + 0.008 - smile * 0.03 + press * 0.0, 0.93);
    const mL = P(-mw * 0.5, my - smile * 0.045 - asym * -0.025, 0.9);
    const mR = P(mw * 0.5, my - smile * 0.045 - asym * 0.025, 0.9);
    const pts = [cL, mL, mid, mR, cR];
    L.taperStroke(ctx, pts, line, lw * 0.6, lw * 0.6, lw * (1.25 + press * 0.4));
    // lower lip hint
    const ll = [P(-mw * 0.35, my + 0.11, 0.9), P(0, my + 0.13 + press * 0.0, 0.92), P(mw * 0.35, my + 0.11, 0.9)];
    L.strokeSmooth(ctx, ll, rgba(skinSh, 0.9), lw * 0.9);
    if (press > 0.3) {
      for (const c of [cL, cR]) {
        ctx.fillStyle = rgba(line, 0.35 * press);
        L.ellipse(ctx, c[0], c[1], lw * 0.7, lw * 0.7);
        ctx.fill();
      }
    }
    return;
  }
  // open mouth shape
  const shape = [cL, upL, upC, upR, cR, loR, loC, loL];
  ctx.save();
  ctx.beginPath();
  L.crPath(ctx, shape, true, 0.55);
  ctx.fillStyle = st.mouthIn || '#4a1a1c';
  ctx.fill();
  ctx.clip();
  // teeth (upper)
  if (o > 0.12) {
    const th = s * 0.07;
    ctx.fillStyle = '#f4ece6';
    ctx.beginPath();
    L.crPath(ctx, [P(-mw * 0.8, upY - 0.02, 0.9), P(0, upY - 0.02, 0.93), P(mw * 0.8, upY - 0.02, 0.9)], false);
    const b1 = P(mw * 0.8, upY + 0.06, 0.9), b2 = P(0, upY + 0.075, 0.93), b3 = P(-mw * 0.8, upY + 0.06, 0.9);
    ctx.lineTo(b1[0], b1[1]);
    ctx.quadraticCurveTo(b2[0], b2[1] + th * 0.1, b3[0], b3[1]);
    ctx.closePath();
    ctx.fill();
  }
  // tongue
  if (o > 0.3) {
    const tg = P(0, loY - 0.02, 0.88);
    ctx.fillStyle = '#b4545a';
    L.ellipse(ctx, tg[0], tg[1], mw * s * 0.65, s * 0.08 * o, pr.H.roll);
    ctx.fill();
  }
  ctx.restore();
  // outline: upper lip heavier
  L.taperStroke(ctx, [cL, upL, upC, upR, cR], line, lw * 0.6, lw * 0.6, lw * 1.3);
  ctx.beginPath();
  L.crPath(ctx, [cR, loR, loC, loL, cL], false, 0.55);
  ctx.strokeStyle = rgba(line, 0.75);
  ctx.lineWidth = lw * 0.75;
  ctx.stroke();
  // lower lip shadow
  const ll = [P(-mw * 0.32, loY + 0.09, 0.88), P(0, loY + 0.11, 0.9), P(mw * 0.32, loY + 0.09, 0.88)];
  L.strokeSmooth(ctx, ll, rgba(skinSh, 0.85), lw * 0.9);
}

// ------------------------------------------------------------------ eyes
function eyeShape(F, sd, st) {
  // canonical left-on-screen eye (sd=-1): inner corner at +u. We mirror for sd=+1.
  const o = clamp(F.lid * (sd < 0 ? F.lidL : F.lidR), 0, 1.4);
  const lower = clamp(F.lidLower || 0, 0, 1);
  const tilt = F.lidTilt || 0; // + angry (inner down), - sad (outer down)
  const eh = st.geo && st.geo.eyeH ? st.geo.eyeH : 1;
  // open lid
  const upOpen = [[-1.0, 0.1], [-0.62, -0.44 * eh], [0.0, -0.6 * eh], [0.56, -0.47 * eh], [1.0, -0.06]];
  const upWide = [[-1.0, 0.04], [-0.62, -0.58 * eh], [0.0, -0.78 * eh], [0.56, -0.62 * eh], [1.0, -0.12]];
  const closed = [[-1.0, 0.1], [-0.55, 0.22], [0.0, 0.26], [0.55, 0.2], [1.0, 0.04]];
  const loOpen = [[-1.0, 0.12], [-0.45, 0.42 * eh], [0.15, 0.48 * eh], [0.72, 0.32 * eh], [1.0, 0.02]];
  const up = upOpen.map((p, i) => {
    let v;
    if (o <= 1) v = lerp(closed[i][1], p[1], o);
    else v = lerp(p[1], upWide[i][1], (o - 1) / 0.4);
    // tilt: inner (u>0) / outer (u<0)
    const u = p[0];
    v += tilt * (u > 0 ? 0.32 * u : 0.12 * u) * clamp(o * 1.3);
    return [u, v];
  });
  const lo = loOpen.map((p, i) => {
    let v = p[1] - lower * (p[1] - 0.05) * 0.75;
    return [p[0], Math.max(v, up[i][1] + 0.02)];
  });
  return { up, lo, o };
}

function drawEye(ctx, pr, G, st, F, Lt, sd, line, lw) {
  const { P, s, H } = pr;
  const ex = sd * G.eyeX, ey = G.eyeY, ez = G.eyeZ;
  const E = P(ex, ey, ez);
  // local axes: u along surface (curving back toward the side), v down
  const d = 0.05;
  const slope = sd * -0.55; // dz/dx at eye
  const Pu = P(ex + d, ey, ez + slope * d);
  const Pv = P(ex, ey + d, ez + 0.0);
  let ux = (Pu[0] - E[0]) / d, uy = (Pu[1] - E[1]) / d;
  let vx = (Pv[0] - E[0]) / d, vy = (Pv[1] - E[1]) / d;
  const W = G.eyeW * (st.eyeScale || 1);
  // mirror so inner corner is +u for both eyes: for sd=-1 inner is +x already
  const mir = sd < 0 ? 1 : -1;
  ctx.save();
  ctx.transform(ux * W * mir, uy * W * mir, vx * W, vy * W, E[0], E[1]);
  const sh = eyeShape(F, sd, st);
  const { up, lo, o } = sh;
  const lwL = lw / (W * s); // line width in local units
  // gaze in local coords (mirror x)
  const gx = clamp(F.gazeX, -1.2, 1.2) * mir, gy = clamp(F.gazeY, -1, 1);
  if (o > 0.04) {
    // opening
    const openPts = [...L.sampleCR(up, 6), ...L.sampleCR(lo, 6).reverse()];
    ctx.save();
    ctx.beginPath();
    openPts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.closePath();
    ctx.fillStyle = st.sclera || '#fbf8f4';
    ctx.fill();
    ctx.clip();
    // iris
    const ir = st.irisR || 0.5;
    const ix = gx * 0.48, iy = 0.04 + gy * 0.3;
    const irisC = st.iris || '#5a3a26';
    const blind = F.blind || 0;
    ctx.fillStyle = L.linear(ctx, 0, iy - ir * 1.2, 0, iy + ir * 1.2, [[0, shade(irisC, 0.45)], [0.55, irisC], [1, shade(irisC, 1.35)]]);
    L.ellipse(ctx, ix, iy, ir, ir * 1.16);
    ctx.fill();
    // iris ring
    ctx.strokeStyle = rgba(shade(irisC, 0.35), 0.9);
    ctx.lineWidth = 0.07;
    ctx.stroke();
    // pupil
    const pr2 = (st.pupilR || 0.21) * (F.pupil || 1);
    ctx.fillStyle = rgba('#120807', 0.92 * (1 - blind * 0.7));
    L.ellipse(ctx, ix + gx * 0.03, iy + 0.02, pr2, pr2 * 1.18);
    ctx.fill();
    // blindness / glow haze
    if (blind > 0.01) {
      ctx.fillStyle = rgba('#e8eef4', 0.75 * blind);
      L.ellipse(ctx, ix, iy, ir * 1.05, ir * 1.2);
      ctx.fill();
    }
    // lid shadow band
    ctx.fillStyle = L.linear(ctx, 0, -0.7, 0, 0.2, [[0, rgba('#3a3050', 0.55)], [0.6, rgba('#3a3050', 0.12)], [1, rgba('#3a3050', 0)]]);
    ctx.beginPath();
    L.crPath(ctx, up.map(([u, v]) => [u, v - 0.1]), false);
    for (let i = up.length - 1; i >= 0; i--) ctx.lineTo(up[i][0], up[i][1] + 0.38);
    ctx.closePath();
    ctx.fill();
    // highlights
    const shake = F._irisShake || 0;
    const hx = ix - 0.2 - gx * 0.1 + shake * 0.03, hy = iy - 0.26;
    ctx.fillStyle = rgba('#ffffff', 0.95);
    L.ellipse(ctx, hx, hy, 0.16 + (F.tears || 0) * 0.04, 0.13 + (F.tears || 0) * 0.04, -0.4);
    ctx.fill();
    ctx.fillStyle = rgba('#ffffff', 0.8);
    L.ellipse(ctx, ix + 0.22, iy + 0.24, 0.07, 0.06);
    ctx.fill();
    if (st.twinkle && gy < -0.2) {
      // looking up (to the Father): a soft star of light in the pupil that gently breathes
      const k = clamp((-gy - 0.2) / 0.35) * (0.75 + 0.25 * Math.sin((pr.t || 0) * 2.6 + sd));
      const tx = ix + 0.13, ty = iy - 0.02, r = 0.26 * k;
      ctx.fillStyle = rgba('#ffffff', 0.9 * k);
      ctx.beginPath();
      for (let i = 0; i < 8; i++) {
        const a = i * Math.PI / 4 + 0.2, rr = i % 2 ? r * 0.22 : r;
        ctx.lineTo(tx + Math.cos(a) * rr, ty + Math.sin(a) * rr);
      }
      ctx.closePath(); ctx.fill();
      ctx.fillStyle = L.radial(ctx, tx, ty, 0, r * 0.9, [[0, rgba('#ffffff', 0.55 * k)], [1, rgba('#ffffff', 0)]]);
      ctx.fillRect(tx - r, ty - r, r * 2, r * 2);
    }
    if ((F.tears || 0) > 0.2) {
      // extra wet sparkles
      ctx.fillStyle = rgba('#ffffff', 0.7 * F.tears);
      L.ellipse(ctx, ix + 0.05, iy + 0.32, 0.12, 0.04);
      ctx.fill();
      L.ellipse(ctx, ix - 0.3, iy + 0.1, 0.05, 0.05);
      ctx.fill();
    }
    // wet lower rim
    if ((F.tears || 0) > 0.05) {
      ctx.strokeStyle = rgba('#a6d2f6', 0.75 * F.tears);
      ctx.lineWidth = 0.13;
      ctx.beginPath();
      L.crPath(ctx, lo.map(([u, v]) => [u, v - 0.05]), false);
      ctx.stroke();
    }
    ctx.restore();
  }
  // upper lid line (lash line)
  const lc = st.lashColor || line;
  const wMax = (st.lashW || 0.24);
  L.taperStroke(ctx, up, lc, wMax * (0.75 + 0.25 * clamp(o)), wMax * 0.28, wMax * 0.8);
  // outer flick
  if (o > 0.2) {
    const p0 = up[0], p1 = up[1];
    ctx.fillStyle = lc;
    ctx.beginPath();
    ctx.moveTo(p0[0] + 0.05, p0[1] - 0.12);
    ctx.lineTo(p0[0] - 0.16, p0[1] - 0.1);
    ctx.lineTo(p1[0] - 0.05, p1[1] + 0.02);
    ctx.closePath();
    ctx.fill();
  }
  // crease
  if (o > 0.3) {
    const cr = up.slice(0, 4).map(([u, v]) => [u * 0.92 - 0.02, v - 0.2 - (F.lidLower || 0) * 0.02]);
    L.strokeSmooth(ctx, cr, rgba(lc, 0.45), 0.06);
  }
  // lower lid line (outer part)
  if (o > 0.04) {
    L.taperStroke(ctx, lo.slice(0, 4), rgba(lc, 0.7), 0.1, 0.02, 0.08);
  } else {
    // closed: lashes downward hint
    L.strokeSmooth(ctx, lo.slice(0, 3).map(([u, v]) => [u, v + 0.05]), rgba(lc, 0.25), 0.05);
  }
  ctx.restore();
}

// Tear streaks down the cheeks: each is one whole streak that fades as a whole as the tears dry
// (never shortening in pieces), tinted a watery blue so it reads against skin and a white beard.
// A drop runs down it now and then, fading out before it leaves the cheek.
function drawTears(ctx, pr, G, F, t) {
  const { P, s } = pr;
  const fl = clamp(F.tearFlow);
  for (const sd of [-1, 1]) {
    const x0 = sd * (G.eyeX - 0.08);
    const pts = [P(x0, 0.2, 0.84), P(x0 + sd * 0.03, 0.45, 0.82), P(x0 + sd * 0.05, 0.75, 0.74), P(x0 + sd * 0.02, 1.02, 0.66)];
    const dense = L.sampleCR(pts, 6);
    const a = Math.min(1, fl * 1.6);
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    // the streak tapers off toward its end so it has no blunt tip
    const g = ctx.createLinearGradient(dense[0][0], dense[0][1], dense[dense.length - 1][0], dense[dense.length - 1][1]);
    g.addColorStop(0, rgba('#8ec4f2', 0.62 * a)); g.addColorStop(0.75, rgba('#8ec4f2', 0.45 * a)); g.addColorStop(1, rgba('#8ec4f2', 0));
    ctx.strokeStyle = g;
    ctx.lineWidth = s * 0.03;
    ctx.beginPath();
    dense.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.stroke();
    const g2 = ctx.createLinearGradient(dense[0][0], dense[0][1], dense[dense.length - 1][0], dense[dense.length - 1][1]);
    g2.addColorStop(0, rgba('#e8f6ff', 0.7 * a)); g2.addColorStop(0.7, rgba('#e8f6ff', 0.4 * a)); g2.addColorStop(1, rgba('#e8f6ff', 0));
    ctx.strokeStyle = g2;
    ctx.lineWidth = s * 0.009;
    ctx.stroke();
    // a drop travelling down, fading as it goes
    const ph = ((t * 0.32 + (sd > 0 ? 0.47 : 0)) % 1);
    const di = Math.floor(ph * (dense.length - 1));
    if (fl > 0.35) {
      const p = dense[di];
      const k = Math.min(1, (fl - 0.35) / 0.3) * (1 - ph);
      ctx.fillStyle = rgba('#a8d4fa', 0.85 * k);
      L.ellipse(ctx, p[0], p[1] + s * 0.01, s * 0.022, s * 0.03);
      ctx.fill();
      ctx.fillStyle = rgba('#ffffff', 0.9 * k);
      L.ellipse(ctx, p[0] - s * 0.006, p[1], s * 0.007, s * 0.009);
      ctx.fill();
    }
    ctx.restore();
  }
}

// One tear: it wells on the lower lid (tearDrop < 0), rolls down the cheek (0..1) leaving a thin wet
// trail, and the trail then dries (tearTrail fades to 0). tearSide picks the eye.
function smoothstep01(x) { const v = clamp(x); return v * v * (3 - 2 * v); }
function drawSingleTear(ctx, pr, G, F) {
  const { P, s } = pr;
  const sd = F.tearSide || 1, p = F.tearDrop, trail = F.tearTrail == null ? 1 : F.tearTrail;
  const x0 = sd * (G.eyeX - 0.04);
  const path = L.sampleCR([P(x0, 0.22, 0.86), P(x0 + sd * 0.03, 0.45, 0.83), P(x0 + sd * 0.06, 0.72, 0.76), P(x0 + sd * 0.04, 0.98, 0.68)], 8);
  ctx.save();
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (p < 0) {
    // welling on the lid: a growing bead of light
    const k = clamp(1 + p);
    const b = path[0];
    ctx.fillStyle = rgba('#b4dafa', 0.85 * k);
    L.ellipse(ctx, b[0], b[1] - s * 0.01, s * 0.02 * k + 0.5, s * 0.016 * k + 0.5); ctx.fill();
  } else {
    const n = Math.max(2, Math.round(clamp(p) * (path.length - 1)) + 1);
    const seg = path.slice(0, n);
    if (trail > 0.01) {
      ctx.strokeStyle = rgba('#8ec4f2', 0.5 * trail); ctx.lineWidth = s * 0.022;
      ctx.beginPath(); seg.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.stroke();
      ctx.strokeStyle = rgba('#ffffff', 0.55 * trail); ctx.lineWidth = s * 0.007; ctx.stroke();
    }
    if (p < 1) {
      const q = seg[seg.length - 1];
      const fade = 1 - smoothstep01((p - 0.7) / 0.3);
      ctx.globalAlpha *= fade;
      ctx.fillStyle = rgba('#a8d4fa', 0.9);
      L.ellipse(ctx, q[0], q[1] + s * 0.01, s * 0.022, s * 0.03); ctx.fill();
      ctx.fillStyle = rgba('#ffffff', 0.95);
      L.ellipse(ctx, q[0] - s * 0.006, q[1], s * 0.007, s * 0.009); ctx.fill();
    }
  }
  ctx.restore();
}

// ------------------------------------------------------------------ brows
function drawBrow(ctx, pr, G, st, F, sd, line, lw) {
  const { P, s } = pr;
  const side = sd < 0 ? 'L' : 'R';
  const inner = (F.browInner || 0) + (F['browInner' + side] || 0);
  const outer = (F.browOuter || 0) + (F['browOuter' + side] || 0);
  const hgt = (F.browHeight || 0) + (F['browH' + side] || 0);
  const fur = clamp(F.browFurrow || 0);
  const by = G.browY - hgt * 0.17;
  const pIn = [sd * (0.15 - fur * 0.035 - Math.max(0, -inner) * 0.02), by + 0.045 - inner * 0.2 + fur * 0.05, 0.92];
  const pMid = [sd * 0.43, by - 0.045 - inner * 0.06 - outer * 0.05 - hgt * 0.02, 0.9];
  const pOut = [sd * 0.74, by + 0.03 - outer * 0.15 + inner * 0.04, 0.72];
  const pts = [pIn, pMid, pOut].map((p) => P(...p));
  const bw = (st.browW || G.browW) * s;
  const col = st.browColor || line;
  L.taperStroke(ctx, pts, col, bw * 1.05, bw * 0.35, bw * 0.95);
  if (st.bushyBrows) {
    // hairs
    for (let i = 0; i < 7; i++) {
      const t = i / 6;
      const a = [lerp(pIn[0], pOut[0], t), lerp(pIn[1], pOut[1], t) - 0.03 * Math.sin(t * 3.1), 0.88];
      const b = [a[0] + sd * 0.06, a[1] - 0.05 + (i % 2) * 0.02, 0.86];
      L.strokeSmooth(ctx, [P(...a), P(...b)], rgba(col, 0.7), lw * 0.7);
    }
  }
}

function drawRim(ctx, pr, facePoly, crC, crR, Lt, s, st) {
  // thin bright rim along the contour on the rim side
  const side = Lt.rimSide || 1;
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.strokeStyle = rgba(Lt.rim, Lt.rimA);
  ctx.lineWidth = s * 0.03;
  ctx.lineCap = 'round';
  const pts = facePoly.filter((p) => (p[0] - pr.H.x) * side > s * 0.25);
  if (pts.length > 1) {
    ctx.beginPath();
    L.crPath(ctx, pts, false);
    ctx.stroke();
  }
  ctx.restore();
}

module.exports = { drawHead, makeProj, GEO, geoOf, shadowSide, terminatorX };
