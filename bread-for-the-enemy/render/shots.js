// Shot library: camera framing, lighting, character placement, gaze targets.
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const L = require('./lib');
const { clamp, lerp, mix, rgba, shade, smooth } = L;
const BG = require('./backgrounds');
const B = require('./body');
const { drawCharacter } = require('./actor');
const { drawHead } = require('./face');
const { C } = require('./characters');

const VW = 1080, VH = 1920;

// ---------------------------------------------------------------- lighting presets
const LIGHT = {
  lamp: { side: -1, key: '#ffe2bc', amb: '#a87a62', shadow: 0.68, rim: '#ffb060', rimA: 0.35, rimSide: 1, wrap: 0.75 },
  lampR: { side: 1, key: '#ffe2bc', amb: '#a87a62', shadow: 0.68, rim: '#ffb060', rimA: 0.3, rimSide: -1, wrap: 0.75 },
  street: { side: -1, key: '#ffcf9e', amb: '#5a6894', shadow: 0.78, rim: '#a8c0ff', rimA: 0.5, rimSide: 1, wrap: 0.65 },
  church: { side: 1, key: '#ffdcb0', amb: '#9a6a5a', shadow: 0.7, rim: '#ffb060', rimA: 0.4, rimSide: -1, wrap: 0.7 },
  cellL: { side: -1, key: '#e4eaff', amb: '#6c6e8c', shadow: 0.72, rim: '#ffa860', rimA: 0.45, rimSide: 1, wrap: 0.7 },
  cellR: { side: -1, key: '#e8ecff', amb: '#6c6e8c', shadow: 0.72, rim: '#ffa860', rimA: 0.35, rimSide: 1, wrap: 0.8 },
  cellWarm: { side: -1, key: '#fff0dc', amb: '#8a7480', shadow: 0.62, rim: '#ffd090', rimA: 0.5, rimSide: 1, wrap: 0.85 },
  jer: { side: 1, key: '#ffbf86', amb: '#3e4c7c', shadow: 0.82, rim: '#ff9a50', rimA: 0.45, rimSide: -1, wrap: 0.6 },
  jerCool: { side: -1, key: '#c8d4ff', amb: '#3a466e', shadow: 0.8, rim: '#ff9a50', rimA: 0.5, rimSide: 1, wrap: 0.6 },
  desert: { side: 1, key: '#fff4e2', amb: '#b88c84', shadow: 0.55, rim: '#ffffff', rimA: 0.25, rimSide: -1, wrap: 0.8 },
  divine: { side: -1, key: '#fffaf0', amb: '#e8cfb0', shadow: 0.32, rim: '#ffffff', rimA: 0.85, rimSide: 1, wrap: 1.0 },
  lightUp: { side: 1, key: '#fff8e8', amb: '#c8a890', shadow: 0.45, rim: '#ffffff', rimA: 0.7, rimSide: -1, wrap: 0.9 },
  dawn: { side: 1, key: '#ffd6a6', amb: '#7a5a78', shadow: 0.62, rim: '#ffcc80', rimA: 0.65, rimSide: 1, wrap: 0.7 },
};

// ---------------------------------------------------------------- look maps
function looks(base, extra) { return Object.assign({ default: base }, extra || {}); }

// ---------------------------------------------------------------- caching
const cache = new Map();
function cached(key, painter, blur = 0, scale = 1) {
  if (cache.has(key)) return cache.get(key);
  const R = global.RENDER_SCALE || 1;
  const c = createCanvas(Math.round(VW * R), Math.round(VH * R));
  const x = c.getContext('2d');
  x.scale(R, R);
  painter(x);
  let out = c;
  if (blur > 0) {
    const c2 = createCanvas(c.width, c.height);
    const x2 = c2.getContext('2d');
    x2.filter = `blur(${blur * R}px)`;
    x2.drawImage(c, 0, 0);
    out = c2;
  }
  if (cache.size > 24) cache.delete(cache.keys().next().value);
  cache.set(key, out);
  return out;
}
function drawCached(ctx, img) { ctx.drawImage(img, 0, 0, VW, VH); }
// paint a background through a zoom/offset window (for close-ups) then blur
function bgView(key, painter, view, blur) {
  return cached(key + JSON.stringify(view) + blur, (x) => {
    x.translate(VW / 2, VH / 2); x.scale(view.z, view.z); x.translate(-view.cx, -view.cy);
    painter(x);
  }, blur);
}

// ---------------------------------------------------------------- helpers
function actor(ctx, W, who, t, place, Lt, look, opt = {}) {
  const F = W.state(who, t, look);
  if (opt.mod) opt.mod(F);
  const sway = W.headLag(who, t, look);
  return drawCharacter(ctx, who, F, place, Lt, t, Object.assign({ sway }, opt));
}
function camera(ctx, lt, dur, p, focus = [VW / 2, VH * 0.45]) {
  const z = p.zoom ? lerp(p.zoom[0], p.zoom[1], smooth(lt / Math.max(0.01, dur))) : 1;
  ctx.translate(focus[0], focus[1]); ctx.scale(z, z); ctx.translate(-focus[0], -focus[1]);
}
function seatedLegs(ctx, Bn, s, fc, st, Lt, o = {}) {
  // folded knees in front of a seated figure
  const col = st.cloth.tunic;
  const lit = L.mul(col, Lt.key || '#fff'), sh = L.mul(shade(col, 0.6), Lt.amb || '#fff');
  const X = (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s];
  const pts = [X(-1.8, 4.2), X(-0.6, 3.6), X(1.6, 3.2), X(3.4, 3.4), X(4.2, 4.2), X(4.0, 5.6), X(2.6, 6.6), X(-1.0, 6.8), X(-2.2, 6.0)];
  ctx.beginPath(); L.crPath(ctx, pts, true, 0.5);
  ctx.fillStyle = lit; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = sh; ctx.beginPath(); ctx.ellipse(...X(1.5, 6.6), s * 3.5, s * 1.4, 0, 0, L.TAU); ctx.fill();
  L.strokeSmooth(ctx, [X(0.2, 4.0), X(1.6, 4.6), X(3.0, 5.4)], rgba(shade(col, 0.4), 0.6), s * 0.05);
  ctx.restore();
  ctx.strokeStyle = st.line; ctx.lineWidth = s * 0.022; ctx.stroke();
}
function kneelLegs(ctx, Bn, s, fc, st, Lt) {
  const col = mix(st.cloth.tunic, st.cloth.mantle || st.cloth.tunic, 0.35);
  const lit = L.mul(col, Lt.key || '#fff'), sh = L.mul(shade(col, 0.6), Lt.amb || '#fff');
  const X = (x, y) => [Bn[0] + x * s * fc, Bn[1] + y * s];
  const pts = [X(-2.0, 4.0), X(1.8, 4.0), X(2.6, 5.4), X(2.8, 7.0), X(1.0, 7.4), X(-2.6, 7.3), X(-3.0, 6.0)];
  ctx.beginPath(); L.crPath(ctx, pts, true, 0.5);
  ctx.fillStyle = lit; ctx.fill();
  ctx.save(); ctx.clip(); ctx.fillStyle = sh; ctx.fillRect(...X(-3, 6.4), s * 6 * fc, s * 2); ctx.restore();
  ctx.strokeStyle = st.line; ctx.lineWidth = s * 0.022; ctx.stroke();
}
function standFeet(ctx, Bn, s, fc, len, Lt) {
  for (const dx of [-0.8, 0.8]) {
    const p = [Bn[0] + dx * s * fc + s * 0.3 * fc, Bn[1] + len * s + s * 0.15];
    ctx.fillStyle = L.mul('#5a3a24', Lt.key || '#fff');
    ctx.beginPath(); ctx.ellipse(p[0], p[1], s * 0.75, s * 0.28, 0, 0, L.TAU); ctx.fill();
  }
}
function floorShadow(ctx, x, y, w, a = 0.45) {
  ctx.fillStyle = L.radial(ctx, x, y, 0, w, [[0, rgba('#000000', a)], [1, rgba('#000000', 0)]]);
  ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.2); ctx.translate(-x, -y);
  ctx.fillRect(x - w, y - w, w * 2, w * 2); ctx.restore();
}

// ================================================================== SHOTS
const S = {};

// ---------------------------------------------------------- PROLOGUE
S.upper_jesus = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 820]);
  drawCached(ctx, bgView('upper', (x) => BG.upperRoom(x, { tableY: 1560 }), { z: 1.15, cx: 540, cy: 900 }, 7));
  BG.upperRoomDyn(ctx, t, { tableY: 1560 });
  const lk = looks({ gx: 0, gy: 0.1, yaw: 0.05, pitch: 0.05 }, {
    bread: { gx: 0.05, gy: 0.95, yaw: 0.05, pitch: 0.3 }, cam: { gx: -0.05, gy: 0.0, yaw: 0.06, pitch: 0.02 },
    cam_l: { gx: -0.55, gy: 0.05, yaw: -0.2, pitch: 0.03 },
  });
  // table behind the hands
  ctx.fillStyle = L.linear(ctx, 0, 1640, 0, VH, [[0, '#6a3e1e'], [1, '#2a160a']]);
  ctx.fillRect(0, 1640, VW, VH);
  ctx.fillStyle = rgba('#ffcf8a', 0.3); ctx.fillRect(0, 1640, VW, 8);
  B.drawCup(ctx, 930, 1680, 70, LIGHT.lamp);
  actor(ctx, W, 'jesus', t, { x: 540, y: 1150, s: 170, facing: 1, by: 0.05, len: 3.4 }, LIGHT.lamp, lk);
};

S.upper_hands = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('upper', (x) => BG.upperRoom(x, { tableY: 1560 }), { z: 1.5, cx: 540, cy: 1250 }, 12));
  BG.upperRoomDyn(ctx, t, { tableY: 1500 });
  const Lt = LIGHT.lamp;
  ctx.fillStyle = L.linear(ctx, 0, 1250, 0, VH, [[0, '#6a3e20'], [1, '#2a160a']]);
  ctx.fillRect(0, 1250, VW, VH);
  bokehTable(ctx);
  const k = smooth(lt / 2.4);
  // Jesus' hand from the right offers a morsel; a hand in a dark sleeve reaches from the left and takes it
  const wJ = [lerp(700, 640, k), lerp(900, 880, k)];
  const k2 = smooth((lt - 0.5) / 2.2);
  const wD = [lerp(-40, 330, k2), lerp(1010, 930, k2)];
  closeArm(ctx, [-300, 1300], wD, 170, { skin: '#d8a888', skinShadow: '#9a6a58', line: '#2a1a14', cloth: { tunic: '#2a2228' } }, Lt, { hand: 'open', mirror: -1, sleeve: '#2a2228' });
  B.drawHalfBread(ctx, wJ[0] - 175, wJ[1] - 30, 80, Lt, { face: 1, rot: -0.2 });
  closeArm(ctx, [1300, 700], wJ, 170, C.jesus, Lt, { hand: 'offer', mirror: 1, sleeve: C.jesus.cloth.tunic });
  BG.vignette(ctx, 0.5);
};
function bokehTable(ctx) { BG.bokeh(ctx, [[160, 1180, 80], [900, 1120, 110], [520, 1300, 60]], '#ffb35a', 0.3); }

S.upper_jesus_door = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 820]);
  drawCached(ctx, bgView('upper', (x) => BG.upperRoom(x, { tableY: 1560 }), { z: 1.4, cx: 300, cy: 700 }, 10));
  BG.upperRoomDyn(ctx, t, { tableY: 1560 });
  const lk = looks({ gx: -0.6, gy: 0.05, yaw: -0.38, pitch: 0.02 }, {
    door: { gx: -0.75, gy: 0.0, yaw: -0.4, pitch: 0.0 }, door_down: { gx: -0.6, gy: 0.45, yaw: -0.36, pitch: 0.16 },
  });
  actor(ctx, W, 'jesus', t, { x: 560, y: 1290, s: 200, facing: -1, by: -0.2, len: 5 }, LIGHT.lampR, lk);
  BG.vignette(ctx, 0.35);
};

// ---------------------------------------------------------- ACT 1 STREET
S.street_wide = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.04] }, [540, 1000]);
  drawCached(ctx, cached('street', (x) => BG.streetNight(x)));
  BG.streetNightDyn(ctx, t);
  // Asher from behind, silhouette with torch rim
  const st = C.asher;
  const x0 = 760, y0 = 1080;
  floorShadow(ctx, x0, 1750, 240, 0.6);
  ctx.save();
  const f = 0.85 + 0.15 * L.fbm1(t * 3.3, 2);
  const sil = { key: mix('#9a7a6a', '#b08a72', f), amb: '#3a3e5a', side: -1, shadow: 0.8, rim: '#ffb070', rimA: 0.75, rimSide: -1, wrap: 0.45 };
  const lk = looks({ gx: -0.6, gy: -0.1, yaw: -0.55, pitch: -0.05 }, { door: { gx: -0.65, gy: -0.15, yaw: -0.55, pitch: -0.06 } });
  actor(ctx, W, 'asher', t, { x: x0, y: y0, s: 70, facing: -1, by: -0.5, len: 9.2 }, sil, lk);
  standFeet(ctx, [x0, y0], 70, -1, 9.2, sil);
  ctx.restore();
};

S.street_asher_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 850]);
  drawCached(ctx, bgView('street', (x) => BG.streetNight(x), { z: 1.8, cx: 360, cy: 800 }, 14));
  const f = 0.85 + 0.15 * L.fbm1(t * 3.3, 2);
  const Lt = Object.assign({}, LIGHT.street, { key: mix('#ffb070', '#ffe0c0', f * 0.6) });
  const lk = looks({ gx: -0.4, gy: -0.15, yaw: -0.3, pitch: -0.08 }, {
    door: { gx: -0.35, gy: -0.25, yaw: -0.26, pitch: -0.1 }, door_low: { gx: -0.2, gy: 0.3, yaw: -0.2, pitch: 0.08 },
    bread: { gx: -0.05, gy: 0.9, yaw: -0.12, pitch: 0.28 }, down: { gx: 0, gy: 0.8, yaw: -0.1, pitch: 0.25 },
  });
  actor(ctx, W, 'asher', t, { x: 560, y: 1300, s: 185, facing: -1, by: -0.25, len: 5 }, Lt, lk);
  // torch glow from left
  L.glow(ctx, -60, 700, 700, '#ff8a30', 0.25 * f);
  BG.vignette(ctx, 0.45, '#02030a');
};

S.church_reader = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.03] }, [540, 900]);
  drawCached(ctx, cached('church', (x) => BG.houseChurch(x, { lampX: 620, lampY: 980 }), 0));
  const Lt = LIGHT.church;
  // background listeners
  BG.silhouettes(ctx, [[120, 980, 70], [300, 1010, 64], [980, 990, 72]], '#1a0e08', '#ffb060', 0.35);
  // the elder reading, 3/4 to the left, scroll in hands
  const lk = looks({ gx: 0.0, gy: 0.75, yaw: 0.25, pitch: 0.22 }, { scroll: { gx: 0.0, gy: 0.8, yaw: 0.25, pitch: 0.24 } });
  actor(ctx, W, 'elder', t, { x: 560, y: 1140, s: 120, facing: 1, by: 0.3, len: 6 }, Lt, lk, { mod: (F) => { F.pose = 'scroll'; F.poseTo = 'scroll'; F.poseFrom = 'scroll'; F.poseK = 1; } });
  // lamp on table
  B.drawFlame(ctx, 620, 1520, 24, t, 2);
  L.glow(ctx, 620, 1500, 300, '#ffb050', 0.35);
  // foreground listeners (backs)
  BG.silhouettes(ctx, [[160, 1560, 120, 0.4], [900, 1600, 130, -0.4]], '#0c0604', '#ffb060', 0.45);
};

S.church_asher = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 860]);
  drawCached(ctx, bgView('church', (x) => BG.houseChurch(x, { lampX: 620, lampY: 980 }), { z: 1.6, cx: 540, cy: 900 }, 14));
  BG.silhouettes(ctx, [[120, 760, 90], [960, 800, 96]], '#1a0e08', '#ffb060', 0.25);
  const lk = looks({ gx: 0.45, gy: -0.05, yaw: 0.28, pitch: -0.02 }, {
    reader: { gx: 0.5, gy: -0.05, yaw: 0.3, pitch: -0.03 }, down: { gx: 0.1, gy: 0.85, yaw: 0.12, pitch: 0.24 },
  });
  actor(ctx, W, 'asher', t, { x: 520, y: 1300, s: 180, facing: 1, by: 0.25, len: 5 }, LIGHT.church, lk);
  BG.silhouettes(ctx, [[60, 1500, 150, 0.3], [1010, 1480, 140, -0.3]], '#0a0503', '#ffb060', 0.3);
};

S.street_knock = (ctx, W, t, lt, dur, p) => {
  // door close-up: each knock shudders the frame and shakes dust loose; then the grille opens on a pair of eyes
  const kn = [0.3, 0.75, 1.2];
  let hit = 0;
  for (const k of kn) { const d = lt - k; if (d >= 0 && d < 0.25) hit = Math.max(hit, 1 - d / 0.25); }
  ctx.save();
  ctx.translate(Math.sin(lt * 90) * 5 * hit, Math.cos(lt * 70) * 3 * hit);
  drawCached(ctx, bgView('street', (x) => BG.streetNight(x), { z: 3.0, cx: 540, cy: 760 }, 0));
  // grille slot sliding open (after the knocks)
  const op = smooth((lt - 1.6) / 0.35);
  const gx = 540, gy = 880;
  ctx.fillStyle = '#050403'; ctx.fillRect(gx - 175, gy - 105, 350, 210);
  if (op > 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(gx - 175, gy - 105, 350 * op, 210); ctx.clip();
    // torchlit eyes of the guard inside
    ctx.fillStyle = '#1a0e08'; ctx.fillRect(gx - 175, gy - 105, 350, 210);
    const Lt = { side: 1, key: '#ffb070', amb: '#3a2a3a', shadow: 0.8, wrap: 0.6 };
    const F = W.state('guard', t, { default: { gx: 0.05, gy: 0.05, yaw: 0.05, pitch: 0.02 } });
    drawHead(ctx, { x: gx + 10, y: gy + 25, s: 230, yaw: 0.05, pitch: 0.02, roll: 0 }, C.guard, Object.assign({}, F, { mouthOpen: 0 }), Lt, { t });
    ctx.restore();
  }
  // slot cover (iron plate sliding right)
  ctx.fillStyle = L.linear(ctx, 0, gy - 105, 0, gy + 105, [[0, '#2c2c30'], [1, '#18181c']]);
  ctx.fillRect(gx - 175 + 350 * op, gy - 105, 350, 210);
  ctx.strokeStyle = '#0c0c0e'; ctx.lineWidth = 10; ctx.strokeRect(gx - 180, gy - 110, 360, 220);
  ctx.restore();
  // dust shaken loose
  for (let i = 0; i < 26; i++) {
    const k = kn[i % 3], tt = lt - k - L.hash01(i) * 0.1;
    if (tt < 0 || tt > 1.6) continue;
    const x = 200 + L.hash01(i * 7) * 680, y = 300 + tt * tt * 700 + L.hash01(i * 3) * 80;
    ctx.fillStyle = rgba('#d8c8a8', 0.6 * (1 - tt / 1.6));
    ctx.beginPath(); ctx.arc(x, y, 2 + 2 * L.hash01(i * 5), 0, L.TAU); ctx.fill();
  }
  const f = 0.85 + 0.15 * L.fbm1(t * 3.3, 2);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, -100, 600, 800, '#ff8a30', 0.28 * f);
  ctx.restore();
  BG.vignette(ctx, 0.55, '#02030a');
};

// forearm + hand for extreme close-ups: soft sleeve with folds
function closeArm(ctx, E, Wr, s, st, Lt, o = {}) {
  const col = o.sleeve || st.cloth.tunic;
  const lit = L.mul(col, Lt.key || '#fff'), dk = L.mul(shade(col, 0.6), Lt.amb || '#fff');
  const dx = Wr[0] - E[0], dy = Wr[1] - E[1], d = Math.hypot(dx, dy) || 1;
  const nx = -dy / d, ny = dx / d;
  const w0 = s * 0.75, w1 = s * 0.55;
  const cuff = [Wr[0] - dx / d * s * 0.35, Wr[1] - dy / d * s * 0.35];
  const pts = [[E[0] + nx * w0, E[1] + ny * w0], [cuff[0] + nx * w1, cuff[1] + ny * w1], [cuff[0] - nx * w1, cuff[1] - ny * w1], [E[0] - nx * w0, E[1] - ny * w0]];
  // wrist / forearm skin peeking from the cuff
  B.drawHand(ctx, Wr, Math.atan2(dy, dx), s, st, Lt, o.hand || 'relax', o.mirror || 1);
  ctx.beginPath(); ctx.moveTo(...pts[0]); ctx.lineTo(...pts[1]);
  ctx.quadraticCurveTo(cuff[0] + dx / d * s * 0.12, cuff[1] + dy / d * s * 0.12, pts[2][0], pts[2][1]);
  ctx.lineTo(...pts[3]); ctx.closePath();
  ctx.fillStyle = lit; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = dk;
  ctx.beginPath(); ctx.moveTo(pts[2][0], pts[2][1]); ctx.lineTo(pts[3][0], pts[3][1]); ctx.lineTo(pts[3][0] + nx * s * 0.5, pts[3][1] + ny * s * 0.5); ctx.lineTo(pts[2][0] + nx * s * 0.45, pts[2][1] + ny * s * 0.45); ctx.fill();
  for (let i = 1; i < 4; i++) {
    const q = [lerp(E[0], cuff[0], i / 4), lerp(E[1], cuff[1], i / 4)];
    L.strokeSmooth(ctx, [[q[0] + nx * w0 * 0.9, q[1] + ny * w0 * 0.9], [q[0] + dx / d * s * 0.15, q[1] + dy / d * s * 0.15], [q[0] - nx * w0 * 0.7, q[1] - ny * w0 * 0.7]], rgba(shade(col, 0.4), 0.55), s * 0.025);
  }
  ctx.restore();
  ctx.strokeStyle = st.line; ctx.lineWidth = s * 0.022; ctx.stroke();
  if (o.shackle) B.drawShackle(ctx, [cuff[0] + dx / d * s * 0.2, cuff[1] + dy / d * s * 0.2], Math.atan2(dy, dx), s, Lt);
}

S.street_door_guard = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('street', (x) => BG.streetNight(x), { z: 1.7, cx: 540, cy: 900 }, 4));
  // door opening reveals interior darkness + guard
  const open = smooth(lt / 0.9);
  ctx.fillStyle = '#050403';
  ctx.fillRect(340, 330, 400 * open + 10, 1500);
  const lk = looks({ gx: 0.4, gy: 0.15, yaw: 0.25, pitch: 0.08 }, { asher: { gx: 0.45, gy: 0.2, yaw: 0.28, pitch: 0.1 } });
  ctx.save();
  ctx.beginPath(); ctx.rect(330, 300, 420 * open + 20, 1700); ctx.clip();
  const f = 0.85 + 0.15 * L.fbm1(t * 3, 6);
  const Lt = { side: 1, key: mix('#ffb070', '#ffd8b0', f), amb: '#4a3a5a', shadow: 0.8, rim: '#a8c0ff', rimA: 0.3, rimSide: -1, wrap: 0.6 };
  actor(ctx, W, 'guard', t, { x: 520, y: 1250, s: 150, facing: 1, by: 0.3, len: 5 }, Lt, lk);
  B.drawTorch(ctx, 760, 1080, 40, t, Lt, { size: 1.2, seed: 3 });
  ctx.restore();
  // door leaf
  ctx.fillStyle = L.linear(ctx, 0, 0, 400, 0, [[0, '#3a2416'], [1, '#22140a']]);
  ctx.fillRect(330 + 420 * open, 300, 420 * (1 - open) + 300, 1700);
  BG.vignette(ctx, 0.5, '#02030a');
};

// ---------------------------------------------------------- CELL
const cellPaul = { x: 300, y: 1130, s: 92, facing: 1, by: 0.35, len: 4.4 };
function cellBG(view, blur, opt = {}) {
  return bgView('cell' + JSON.stringify(opt), (x) => BG.cell(x, opt), view, blur);
}
function cellDynView(ctx, t, view, opt = {}) {
  ctx.save();
  ctx.translate(VW / 2, VH / 2); ctx.scale(view.z, view.z); ctx.translate(-view.cx, -view.cy);
  BG.cellDyn(ctx, t, opt);
  ctx.restore();
}
const paulLook = (ex) => looks({ gx: 0.45, gy: -0.35, yaw: 0.3, pitch: -0.1 }, Object.assign({
  parchment: { gx: 0.25, gy: 0.9, yaw: 0.2, pitch: 0.3 }, door: { gx: 0.75, gy: -0.25, yaw: 0.42, pitch: -0.08 },
  asher: { gx: 0.5, gy: -0.45, yaw: 0.32, pitch: -0.14 }, bread: { gx: 0.35, gy: 0.75, yaw: 0.25, pitch: 0.22 },
  down: { gx: 0.1, gy: 0.85, yaw: 0.18, pitch: 0.26 }, far: { gx: 0.05, gy: -0.1, yaw: 0.12, pitch: -0.05 },
  hands: { gx: 0.15, gy: 0.95, yaw: 0.12, pitch: 0.3 }, guard: { gx: 0.85, gy: -0.3, yaw: 0.5, pitch: -0.1 },
  away: { gx: -0.5, gy: 0.2, yaw: -0.1, pitch: 0.05 },
}, ex || {}));
const asherLook = (ex) => looks({ gx: -0.4, gy: 0.35, yaw: -0.3, pitch: 0.12 }, Object.assign({
  paul: { gx: -0.45, gy: 0.4, yaw: -0.32, pitch: 0.14 }, bread: { gx: -0.2, gy: 0.9, yaw: -0.2, pitch: 0.3 },
  away: { gx: 0.55, gy: 0.1, yaw: 0.25, pitch: 0.02 }, away_down: { gx: 0.45, gy: 0.7, yaw: 0.2, pitch: 0.22 },
  guard: { gx: 0.75, gy: -0.1, yaw: 0.4, pitch: -0.03 }, down: { gx: -0.1, gy: 0.85, yaw: -0.15, pitch: 0.26 },
}, ex || {}));

S.cell_wide = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.0, cx: 540, cy: 960 };
  drawCached(ctx, cellBG(view, 0));
  // door opening light
  const op = smooth(lt / 1.2);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#ffb070', 0.35 * op);
  ctx.beginPath(); ctx.moveTo(800, 500); ctx.lineTo(1080, 500); ctx.lineTo(1080, 1900); ctx.lineTo(600, 1900); ctx.closePath(); ctx.fill();
  ctx.restore();
  BG.cellDyn(ctx, t, {});
  // Asher silhouette in doorway
  const sil = { side: 1, key: '#2a2a36', amb: '#101018', shadow: 0.9, rim: '#ffb070', rimA: 0.7 * op, rimSide: 1, wrap: 0.2 };
  ctx.save(); ctx.globalAlpha = op;
  actor(ctx, W, 'asher', t, { x: 900, y: 700, s: 56, facing: -1, by: -0.4, len: 9.6 }, sil, asherLook());
  ctx.restore();
  // Paul seated
  floorShadow(ctx, 330, 1560, 260, 0.5);
  B.drawChain(ctx, [150, 1150], [210, 1520], 30, LIGHT.cellL, 2.5, 12);
  const pl = Object.assign({}, cellPaul);
  actor(ctx, W, 'paul', t, pl, LIGHT.cellL, paulLook(), { afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, LIGHT.cellL) });
};

S.cell_paul_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [520, 820]);
  const view = { z: 2.2, cx: 300, cy: 760 };
  drawCached(ctx, cellBG(view, 12));
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 60, 300, 700, '#c8d8ff', 0.18);
  ctx.restore();
  const warm = W.tl && p.warm ? 1 : 0;
  actor(ctx, W, 'paul', t, { x: 500, y: 1300, s: 190, facing: 1, by: 0.3, len: 5 }, LIGHT.cellL, paulLook());
  BG.dust(ctx, t, { x: 0, y: 0, w: 500, h: 1400 }, 14, '#e8f0ff', 11, 0.35, 3);
  BG.vignette(ctx, 0.4, '#020305');
};

S.cell_paul_ecu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.06] }, [540, 800]);
  drawCached(ctx, cellBG({ z: 3.0, cx: 300, cy: 700 }, 16));
  actor(ctx, W, 'paul', t, { x: 520, y: 2050, s: 470, facing: 1, by: 0.3, len: 3 }, LIGHT.cellL, paulLook(), { });
  BG.vignette(ctx, 0.55, '#020305');
};

S.cell_asher_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 820]);
  const F = W.state('asher', t, asherLook());
  const kneel = /kneel/.test(F.poseTo) ? 1 : 0;
  const view = kneel ? { z: 2.0, cx: 760, cy: 1100 } : { z: 2.0, cx: 760, cy: 560 };
  drawCached(ctx, cellBG(view, 12));
  cellDynView(ctx, t, view, {});
  actor(ctx, W, 'asher', t, { x: 560, y: 1310, s: 185, facing: -1, by: -0.3, len: 5 }, LIGHT.cellR, asherLook(), {});
  BG.vignette(ctx, 0.4, '#020305');
};

function twoShot(ctx, W, t, lt, dur, p, warmK = 0) {
  const view = { z: 1.25, cx: 540, cy: 1000 };
  drawCached(ctx, cellBG(view, 4));
  cellDynView(ctx, t, view, { shaftA: 0.22 + warmK * 0.25, shaftColor: warmK > 0 ? '#fff0d0' : '#cfe0ff' });
  const Lp = warmK > 0 ? LIGHT.cellWarm : LIGHT.cellL;
  const FA = W.state('asher', t, asherLook());
  const kneel = /kneel/.test(FA.poseTo) ? smooth(FA.poseK) * 1 : (/kneel/.test(FA.poseFrom) ? 1 - smooth(FA.poseK) : 0);
  // Paul low-left
  floorShadow(ctx, 330, 1640, 300, 0.5);
  B.drawChain(ctx, [100, 1080], [250, 1560], 32, Lp, 2.5, 12);
  const pPaul = { x: 290, y: 1150, s: 100, facing: 1, by: 0.35, len: 4.4 };
  actor(ctx, W, 'paul', t, pPaul, Lp, paulLook({ asher: { gx: 0.55, gy: lerp(-0.6, -0.1, kneel), yaw: 0.35, pitch: lerp(-0.18, -0.02, kneel) } }),
    { afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, Lp) });
  // Asher right: standing or kneeling
  const ay = lerp(560, 1010, kneel);
  const pA = { x: 800, y: ay, s: 92, facing: -1, by: -0.35, len: lerp(9.4, 4.2, kneel) };
  if (kneel <= 0.5) standFeet(ctx, [pA.x, pA.y], pA.s, -1, pA.len, Lp);
  floorShadow(ctx, 820, 1640, 220, 0.45);
  actor(ctx, W, 'asher', t, pA, Lp, asherLook({ paul: { gx: -0.5, gy: lerp(0.6, 0.15, kneel), yaw: -0.35, pitch: lerp(0.2, 0.04, kneel) } }),
    { afterTorso: (o) => { if (kneel > 0.5) kneelLegs(ctx, o.neck, o.s, -1, C.asher, Lp); } });
  // dropped bread on floor
  if (p.breadOnFloor !== false) {
    const fa = W.state('asher', t, asherLook());
    const dropped = fa.poseTo === 'drop_bread' ? smooth((fa.poseK - 0.3) / 0.7) : (['hold', 'default'].includes(fa.poseTo) ? 0 : 1);
    if (dropped > 0) {
      const y = lerp(1100, 1600, Math.min(1, dropped * 1.2));
      B.drawBread(ctx, 600, y, 70, Lp, { rot: 0.1 });
      B.drawJar(ctx, 700, 1640, 90, Lp);
    }
  }
  BG.vignette(ctx, 0.45, '#020305');
}
S.cell_two = (ctx, W, t, lt, dur, p) => twoShot(ctx, W, t, lt, dur, p, 0);
S.cell_two_light = (ctx, W, t, lt, dur, p) => {
  twoShot(ctx, W, t, lt, dur, Object.assign({ breadOnFloor: false }, p), smooth(lt / 3));
  ctx.save(); ctx.globalCompositeOperation = 'soft-light';
  ctx.fillStyle = rgba('#ffd8a0', 0.35 * smooth(lt / 3)); ctx.fillRect(0, 0, VW, VH);
  ctx.restore();
};

S.cell_memory = (ctx, W, t, lt, dur, p) => {
  S.cell_asher_cu(ctx, W, t, lt, dur, { zoom: [1.04, 1.1] });
  // ghost overlays: Yosef then Jesus
  const ghost = (who, a, x, y, s, look, Lt) => {
    if (a <= 0.01) return;
    const R = global.RENDER_SCALE || 1;
    const c = createCanvas(Math.round(VW * R), Math.round(VH * R));
    const g = c.getContext('2d'); g.scale(R, R);
    actor(g, W, who, t, { x, y, s, facing: 1, by: 0, len: 4, headOnly: false }, Lt, look);
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = a * 0.55; ctx.globalCompositeOperation = 'screen'; ctx.filter = `blur(${2 * R}px)`;
    ctx.drawImage(c, 0, 0); ctx.restore();
  };
  const lineY = W.tl.lines.find((l) => l.who === 'yosef' && l.start > W.tl.shots.find((s) => s.id === 'cell_memory').start - 0.5);
  const tY = lineY ? lineY.start : 0;
  ghost('yosef', clamp(Math.min((t - tY + 0.6) / 0.6, (tY + 2.6 - t) / 0.6)), 300, 700, 120, looks({ gx: 0.3, gy: 0.2, yaw: 0.2, pitch: 0.05 }), LIGHT.jer);
  ghost('jesus', clamp(Math.min((t - tY - 1.6) / 0.8, (tY + 5.4 - t) / 0.9)), 780, 640, 130, looks({ gx: -0.2, gy: 0.2, yaw: -0.15, pitch: 0.05 }), LIGHT.lamp);
};

S.cell_kneel = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.6, cx: 720, cy: 1100 };
  drawCached(ctx, cellBG(view, 8));
  cellDynView(ctx, t, view, {});
  const k = smooth(lt / 2.2);
  const pA = { x: 560, y: lerp(560, 1060, k), s: 120, facing: -1, by: -0.3, len: lerp(9.4, 4.2, k) };
  if (k <= 0.55) standFeet(ctx, [pA.x, pA.y], pA.s, -1, pA.len, LIGHT.cellR);
  floorShadow(ctx, 560, 1720, 300, 0.5);
  B.drawBread(ctx, 380, 1700, 90, LIGHT.cellR, { rot: 0.1 });
  actor(ctx, W, 'asher', t, pA, LIGHT.cellR, asherLook({ bread: { gx: -0.3, gy: 0.95, yaw: -0.22, pitch: 0.35 } }),
    { afterTorso: (o) => { if (k > 0.55) kneelLegs(ctx, o.neck, o.s, -1, C.asher, LIGHT.cellR); } });
  BG.vignette(ctx, 0.45, '#020305');
};

S.cell_break_insert = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, cellBG({ z: 2.6, cx: 560, cy: 1500 }, 16));
  const Lt = LIGHT.cellWarm;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 540, 700, 800, '#ffe8c0', 0.25 * smooth(lt / 2));
  ctx.restore();
  const st = C.asher;
  const br = smooth((lt - 0.9) / 0.5);
  const sep = br * 150;
  const cy = 960 - smooth(lt / 1.0) * 60;
  const R0 = 250;
  closeArm(ctx, [-200, 1700], [250 - sep * 0.8, cy + 70], 190, st, Lt, { hand: 'hold' });
  closeArm(ctx, [1280, 1700], [830 + sep * 0.8, cy + 70], 190, st, Lt, { hand: 'hold', mirror: -1 });
  if (br < 0.05) B.drawBread(ctx, 540, cy, R0, Lt, { rot: 0.0 });
  else {
    B.drawHalfBread(ctx, 470 - sep, cy, R0 * 0.92, Lt, { face: 1, rot: -0.15 * br });
    B.drawHalfBread(ctx, 610 + sep, cy, R0 * 0.92, Lt, { face: -1, rot: 0.15 * br });
    for (let i = 0; i < 18; i++) {
      const tt = lt - 1.0 - L.hash01(i) * 0.3;
      if (tt < 0) continue;
      const x = 540 + L.hash(i * 7) * 120 + L.hash(i * 3) * tt * 80, y = cy + tt * tt * 900 + L.hash(i * 5) * 20;
      if (y > VH) continue;
      ctx.fillStyle = rgba(i % 2 ? '#e8cfa0' : '#b87a3a', 0.9);
      ctx.beginPath(); ctx.arc(x, y, 5 + 6 * L.hash01(i * 11), 0, L.TAU); ctx.fill();
    }
  }
  BG.dust(ctx, t, { x: 100, y: 200, w: 880, h: 1400 }, 20, '#fff0d0', 21, 0.35, 3);
  BG.vignette(ctx, 0.5, '#020305');
};

S.cell_offer = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.45, cx: 520, cy: 1060 };
  drawCached(ctx, cellBG(view, 7));
  cellDynView(ctx, t, view, { shaftA: 0.3 });
  const Lt = LIGHT.cellL;
  B.drawChain(ctx, [60, 840], [240, 1400], 34, Lt, 2.5, 12);
  const pPaul = { x: 280, y: 900, s: 118, facing: 1, by: 0.35, len: 4.4 };
  actor(ctx, W, 'paul', t, pPaul, Lt, paulLook({ asher: { gx: 0.55, gy: -0.05, yaw: 0.35, pitch: -0.02 }, bread: { gx: 0.5, gy: 0.5, yaw: 0.3, pitch: 0.12 } }),
    { afterTorso: (o) => seatedLegs(ctx, o.neck, o.s, 1, C.paul, Lt) });
  const pA = { x: 820, y: 845, s: 112, facing: -1, by: -0.35, len: 4.2 };
  actor(ctx, W, 'asher', t, pA, Lt, asherLook({ paul: { gx: -0.55, gy: 0.1, yaw: -0.35, pitch: 0.02 } }),
    { afterTorso: (o) => kneelLegs(ctx, o.neck, o.s, -1, C.asher, Lt) });
  BG.vignette(ctx, 0.45, '#020305');
};

S.cell_door_guard = (ctx, W, t, lt, dur, p) => {
  const view = { z: 1.7, cx: 900, cy: 900 };
  drawCached(ctx, cellBG(view, 5));
  const open = smooth(lt / 0.5);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#ff9a50', 0.3 * open); ctx.fillRect(250, 0, 600, VH);
  ctx.restore();
  const f = 0.85 + 0.15 * L.fbm1(t * 3, 6);
  const Lt = { side: 1, key: mix('#ffb070', '#ffd8b0', f), amb: '#4a3a5a', shadow: 0.8, rim: '#ffb070', rimA: 0.4, rimSide: -1, wrap: 0.6 };
  const lk = looks({ gx: -0.4, gy: 0.4, yaw: -0.3, pitch: 0.15 }, { paul: { gx: -0.5, gy: 0.5, yaw: -0.32, pitch: 0.18 } });
  actor(ctx, W, 'guard', t, { x: 540, y: 1250, s: 150, facing: -1, by: -0.3, len: 6 }, Lt, lk);
  B.drawTorch(ctx, 830, 1100, 40, t, Lt, { size: 1.2, seed: 5 });
  BG.vignette(ctx, 0.5, '#020305');
};

S.cell_hands_grip = (ctx, W, t, lt, dur, p) => {
  // tight two-shot at eye level: Paul reaches across and grips Asher's hands
  const view = { z: 1.9, cx: 560, cy: 1120 };
  drawCached(ctx, cellBG(view, 9));
  cellDynView(ctx, t, view, { shaftA: 0.3 });
  const Lt = LIGHT.cellWarm;
  const pPaul = { x: 260, y: 1210, s: 150, facing: 1, by: 0.4, len: 4.4 };
  actor(ctx, W, 'paul', t, pPaul, Lt, paulLook({ asher: { gx: 0.6, gy: 0.0, yaw: 0.4, pitch: 0.0 } }), {
    mod: (F) => { F.poseFrom = 'rest'; F.poseTo = 'grip'; F.poseK = smooth(lt / 1.2); },
  });
  const pA = { x: 860, y: 1180, s: 140, facing: -1, by: -0.4, len: 4.2 };
  actor(ctx, W, 'asher', t, pA, Lt, asherLook({ paul: { gx: -0.6, gy: 0.05, yaw: -0.4, pitch: 0.02 } }), {
    mod: (F) => { F.poseFrom = 'kneel'; F.poseTo = 'kneel'; F.poseK = 1; },
  });
  BG.vignette(ctx, 0.45, '#020305');
};

S.cell_window = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.08] }, [400, 600]);
  drawCached(ctx, cellBG({ z: 1.5, cx: 380, cy: 700 }, 2, { lamp: false, door: false, winX: 380, winY: 520 }));
  cellDynView(ctx, t, { z: 1.5, cx: 380, cy: 700 }, { lamp: false, winX: 380, winY: 520, shaftA: 0.4, shaftX: 620, shaftY: 1900 });
  B.drawChain(ctx, [700, 1250], [920, 1900], 40, LIGHT.cellL, 3, 12);
  BG.vignette(ctx, 0.4, '#020305');
};

// ---------------------------------------------------------- JERUSALEM
S.jer_crack = (ctx, W, t, lt, dur, p) => {
  // dark door with a vertical slit view of the street
  ctx.fillStyle = '#050403'; ctx.fillRect(0, 0, VW, VH);
  const slitX = 470, slitW = 150;
  ctx.save();
  ctx.beginPath(); ctx.rect(slitX, 0, slitW, VH); ctx.clip();
  drawCached(ctx, cached('jer', (x) => BG.jerusalemNight(x)));
  BG.jerusalemDyn(ctx, t, { torches: [[560, 760, 1]] });
  // figures crossing: guards dragging Yosef
  const sx = lerp(820, 300, smooth(lt / dur));
  const sil = { side: 1, key: '#3a3040', amb: '#141018', shadow: 0.9, rim: '#ff9a50', rimA: 0.7, rimSide: 1, wrap: 0.2 };
  actor(ctx, W, 'yosef', t, { x: sx, y: 900, s: 46, facing: -1, by: -0.4, len: 9.5 }, sil, looks({ gx: 0.5, gy: 0, yaw: 0.4, pitch: 0 }));
  actor(ctx, W, 'saul', t, { x: sx + 170, y: 880, s: 48, facing: -1, by: -0.4, len: 9.5 }, sil, looks({ gx: -0.5, gy: 0, yaw: -0.4, pitch: 0 }));
  ctx.restore();
  // wood grain
  ctx.strokeStyle = rgba('#20140c', 0.8); ctx.lineWidth = 6;
  for (let i = 0; i < 12; i++) { ctx.beginPath(); ctx.moveTo(i * 40, 0); ctx.lineTo(i * 40 + 10, VH); ctx.stroke(); }
  ctx.fillStyle = L.linear(ctx, slitX - 60, 0, slitX, 0, [[0, rgba('#000000', 0)], [1, rgba('#2a1a10', 0.9)]]);
  ctx.fillRect(slitX - 60, 0, 60, VH);
};

S.jer_child = (ctx, W, t, lt, dur, p) => {
  ctx.fillStyle = '#040302'; ctx.fillRect(0, 0, VW, VH);
  const slitX = 420, slitW = 300;
  ctx.save();
  ctx.beginPath(); ctx.rect(slitX, 0, slitW, VH); ctx.clip();
  // torchlit face in the slit
  ctx.fillStyle = '#100c10'; ctx.fillRect(0, 0, VW, VH);
  const Lt = { side: 1, key: '#ffc890', amb: '#3a3456', shadow: 0.85, rim: '#ffa060', rimA: 0.5, rimSide: 1, wrap: 0.55 };
  actor(ctx, W, 'child', t, { x: 560, y: 1310, s: 205, facing: 1, by: 0.2, len: 5 }, Lt, looks({ gx: 0.5, gy: 0.0, yaw: 0.2, pitch: 0.0 }, { out: { gx: 0.55, gy: 0.05, yaw: 0.22, pitch: 0.02 } }));
  const f = 0.8 + 0.2 * L.fbm1(t * 3, 9);
  ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 900, 700, 600, '#ff8a30', 0.18 * f);
  ctx.restore();
  // door edges
  ctx.fillStyle = L.linear(ctx, slitX - 80, 0, slitX + 10, 0, [[0, '#050403'], [1, rgba('#050403', 0)]]);
  ctx.fillRect(slitX - 80, 0, 90, VH);
  ctx.fillStyle = L.linear(ctx, slitX + slitW - 10, 0, slitX + slitW + 80, 0, [[0, rgba('#050403', 0)], [1, '#050403']]);
  ctx.fillRect(slitX + slitW - 10, 0, 90, VH);
};

S.jer_yosef = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('jer', (x) => BG.jerusalemNight(x), { z: 1.4, cx: 540, cy: 900 }, 8));
  BG.jerusalemDyn(ctx, t, { torches: [[220, 700, 1], [900, 640, 2]] });
  const lk = looks({ gx: -0.6, gy: 0.0, yaw: -0.42, pitch: 0.0 }, { back: { gx: -0.75, gy: 0.05, yaw: -0.48, pitch: 0.02 }, away: { gx: 0.4, gy: 0, yaw: 0.3, pitch: 0 } });
  actor(ctx, W, 'yosef', t, { x: 560, y: 1220, s: 150, facing: 1, by: 0.55, len: 6 }, LIGHT.jer, lk);
  // soldiers' arms reach in from both frame edges and grip his shoulders
  for (const [sx, sy, hx, hy, dir] of [[1180, 1180, 850, 1290, -1], [-100, 1240, 290, 1320, 1]]) {
    ctx.save();
    ctx.strokeStyle = '#120c0c'; ctx.lineCap = 'round'; ctx.lineWidth = 120;
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.quadraticCurveTo((sx + hx) / 2, hy - 90, hx + dir * 40, hy); ctx.stroke();
    ctx.strokeStyle = rgba('#ff9a50', 0.35); ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(sx, sy - 60); ctx.quadraticCurveTo((sx + hx) / 2, hy - 150, hx + dir * 40, hy - 58); ctx.stroke();
    ctx.fillStyle = '#1e1414';
    ctx.beginPath(); ctx.ellipse(hx, hy + 10, 78, 52, dir * 0.4, 0, L.TAU); ctx.fill();
    for (let k = 0; k < 4; k++) { ctx.beginPath(); ctx.ellipse(hx - dir * 40 + k * dir * 24, hy + 52, 13, 26, 0, 0, L.TAU); ctx.fill(); }
    ctx.restore();
  }
  BG.vignette(ctx, 0.5, '#010205');
};

S.jer_saul = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('jer', (x) => BG.jerusalemNight(x), { z: 1.6, cx: 360, cy: 800 }, 12));
  const f = 0.8 + 0.2 * L.fbm1(t * 3, 3);
  const Lt = Object.assign({}, LIGHT.jer, { key: mix('#ff9a50', '#ffd0a0', f * 0.6) });
  const lk = looks({ gx: 0.45, gy: 0.1, yaw: 0.3, pitch: 0.04 }, {
    yosef: { gx: 0.5, gy: 0.1, yaw: 0.32, pitch: 0.04 }, away_down: { gx: -0.5, gy: 0.6, yaw: -0.15, pitch: 0.2 },
  });
  actor(ctx, W, 'saul', t, { x: 520, y: 1300, s: 182, facing: 1, by: 0.25, len: 5 }, Lt, lk);
  B.drawTorch(ctx, 120, 1150, 44, t, Lt, { size: 1.3, seed: 7 });
  BG.vignette(ctx, 0.45, '#010205');
};

S.jer_yosef_look = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 840]);
  drawCached(ctx, bgView('jer', (x) => BG.jerusalemNight(x), { z: 1.8, cx: 700, cy: 800 }, 14));
  const lk = looks({ gx: 0.0, gy: 0.0, yaw: 0.0, pitch: 0.0 }, { cam: { gx: 0.02, gy: -0.02, yaw: 0.04, pitch: -0.02 } });
  actor(ctx, W, 'yosef', t, { x: 540, y: 1330, s: 200, facing: 1, by: 0.1, len: 5 }, LIGHT.jer, lk);
  BG.vignette(ctx, 0.5, '#010205');
};

// ---------------------------------------------------------- DAMASCUS
S.dam_wide = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.05] }, [540, 1100]);
  drawCached(ctx, cached('desert', (x) => BG.desert(x)));
  const sil = Object.assign({}, LIGHT.desert);
  // Saul and two companions small on the road
  const k = lt * 12;
  actor(ctx, W, 'saul', t, { x: 600 + k * 0.5, y: 1240 - k * 0.2, s: 34, facing: 1, by: 0.2, len: 9.5, style: 'saul_travel' }, sil, looks({ gx: 0.4, gy: 0, yaw: 0.2, pitch: 0 }));
  // two travelling companions in hooded cloaks, walking with Saul
  for (const [dx, dy, s2, ph] of [[-120, 46, 30, 0.0], [140, 60, 31, 1.7]]) {
    const x = 600 + dx + k * 0.5, y = 1240 + dy;
    const bob = Math.abs(Math.sin(lt * 4.4 + ph)) * 3;
    const lit = '#7a5a40', dark = '#4a3424', rim = '#ffe8c0';
    ctx.save();
    ctx.translate(x, y - bob);
    // cloak body
    ctx.fillStyle = dark;
    ctx.beginPath();
    ctx.moveTo(-s2 * 0.55, -s2 * 0.2);
    ctx.quadraticCurveTo(-s2 * 1.5, s2 * 1.0, -s2 * 1.45, s2 * 7.6);
    ctx.lineTo(s2 * 1.45, s2 * 7.6);
    ctx.quadraticCurveTo(s2 * 1.5, s2 * 1.0, s2 * 0.55, -s2 * 0.2);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = lit;
    ctx.beginPath(); ctx.moveTo(s2 * 0.1, -s2 * 0.1); ctx.quadraticCurveTo(s2 * 1.4, s2 * 1.1, s2 * 1.35, s2 * 7.6); ctx.lineTo(s2 * 0.4, s2 * 7.6); ctx.closePath(); ctx.fill();
    // hooded head
    ctx.fillStyle = dark;
    ctx.beginPath(); ctx.ellipse(0, -s2 * 0.9, s2 * 0.85, s2 * 1.05, 0, 0, L.TAU); ctx.fill();
    ctx.fillStyle = '#c89a78';
    ctx.beginPath(); ctx.ellipse(s2 * 0.18, -s2 * 0.75, s2 * 0.42, s2 * 0.6, 0, 0, L.TAU); ctx.fill();
    // staff
    ctx.strokeStyle = '#3a2618'; ctx.lineWidth = s2 * 0.14;
    ctx.beginPath(); ctx.moveTo(s2 * 1.2, -s2 * 1.4); ctx.lineTo(s2 * 1.6, s2 * 7.8); ctx.stroke();
    // sun rim
    ctx.strokeStyle = rgba(rim, 0.7); ctx.lineWidth = s2 * 0.1;
    ctx.beginPath(); ctx.ellipse(0, -s2 * 0.9, s2 * 0.85, s2 * 1.05, 0, -1.9, -0.2); ctx.stroke();
    ctx.restore();
    // shadow on the sand
    floorShadow(ctx, x + 20, y + s2 * 7.6, s2 * 2.2, 0.35);
  }
};

S.dam_saul_cu = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, bgView('desert', (x) => BG.desert(x), { z: 1.6, cx: 600, cy: 700 }, 10));
  const glowK = clamp((lt - 1.2) / 1.4);
  const Lt = Object.assign({}, LIGHT.desert, { key: mix('#fff4e2', '#ffffff', glowK), shadow: lerp(0.55, 0.2, glowK) });
  const lk = looks({ gx: 0.3, gy: 0, yaw: 0.25, pitch: 0 }, { ahead: { gx: 0.35, gy: 0.0, yaw: 0.28, pitch: 0.0 }, up: { gx: 0.15, gy: -0.85, yaw: 0.15, pitch: -0.35 } });
  const bob = Math.abs(Math.sin(lt * 4.2)) * 10 * (1 - glowK);
  actor(ctx, W, 'saul', t, { x: 540, y: 1300 - bob, s: 180, facing: 1, by: 0.25, len: 5, style: 'saul_travel' }, Lt, lk);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#ffffff', glowK * 0.9); ctx.fillRect(0, 0, VW, VH);
  ctx.restore();
};

S.dam_flash = (ctx, W, t, lt, dur, p) => {
  BG.heavenLight(ctx, t, { x: 540, y: 600 });
  ctx.fillStyle = rgba('#ffffff', 1 - smooth(lt / dur) * 0.4); ctx.fillRect(0, 0, VW, VH);
};

S.dam_saul_kneel = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.05] }, [540, 1100]);
  drawCached(ctx, bgView('desert', (x) => BG.desert(x), { z: 1.3, cx: 540, cy: 1300 }, 6));
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#fff8e0', 0.55); ctx.fillRect(0, 0, VW, VH);
  ctx.restore();
  BG.heavenLightOverlay && BG.heavenLightOverlay(ctx, t);
  // light shaft from above onto Saul
  BG.lightShaft(ctx, [540, -200], [560, 1700], 500, 900, '#fffbe8', 0.75);
  const Lt = LIGHT.lightUp;
  const pS = { x: 560, y: 1140, s: 110, facing: 1, by: 0.3, len: 4.2, style: 'saul_travel' };
  const shake = 6 * L.noise1(t * 14, 3);
  pS.x += shake;
  actor(ctx, W, 'saul', t, pS, Lt, looks({ gx: 0, gy: 0.7, yaw: 0.1, pitch: 0.28 }, { down: { gx: 0, gy: 0.8, yaw: 0.1, pitch: 0.3 } }),
    { afterTorso: (o) => kneelLegs(ctx, o.neck, o.s, 1, C.saul, Lt) });
  BG.dust(ctx, t, { x: 100, y: 900, w: 880, h: 900 }, 40, '#fff4d0', 33, 0.6, 3.5);
};

S.dam_jesus = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 760]);
  BG.heavenLight(ctx, t, { x: 540, y: 560 });
  const Lt = LIGHT.divine;
  const lk = looks({ gx: 0, gy: 0.6, yaw: 0.0, pitch: 0.22 }, { down: { gx: 0.0, gy: 0.65, yaw: 0.02, pitch: 0.24 }, cam: { gx: 0, gy: 0.1, yaw: 0, pitch: 0.05 } });
  actor(ctx, W, 'jesus', t, { x: 540, y: 1150, s: 160, facing: 1, by: 0.0, len: 7 }, Lt, lk);
  // radiance over the figure
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 540, 600, 700, '#fff6dc', 0.35);
  ctx.restore();
  BG.dust(ctx, t, { x: 0, y: 0, w: VW, h: VH }, 40, '#ffffff', 17, 0.55, 3);
};

S.dam_saul_up = (ctx, W, t, lt, dur, p) => {
  camera(ctx, { zoom: [1.0, 1.06] } && lt, dur, { zoom: [1.0, 1.06] }, [540, 820]);
  drawCached(ctx, bgView('desert', (x) => BG.desert(x), { z: 2.0, cx: 540, cy: 1400 }, 14));
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba('#fff8e0', 0.4); ctx.fillRect(0, 0, VW, VH);
  L.glow(ctx, 540, -100, 1100, '#ffffff', 0.8);
  ctx.restore();
  const lk = looks({ gx: 0, gy: -0.7, yaw: 0.05, pitch: -0.3 }, { up: { gx: 0.0, gy: -0.75, yaw: 0.05, pitch: -0.32 } });
  actor(ctx, W, 'saul', t, { x: 540, y: 1360, s: 190, facing: 1, by: 0.1, len: 5, style: 'saul_travel' }, LIGHT.lightUp, lk);
  BG.dust(ctx, t, { x: 0, y: 0, w: VW, h: VH }, 26, '#fff4d0', 41, 0.5, 3);
};

S.dam_hands = (ctx, W, t, lt, dur, p) => {
  BG.heavenLight(ctx, t, { x: 540, y: 300 });
  const Lt = LIGHT.divine;
  const k = smooth(lt / 2.0);
  closeArm(ctx, [380, 2050], [lerp(470, 520, k), lerp(1240, 1050, k)], 190, C.saul, LIGHT.lightUp, { hand: 'open', mirror: -1, sleeve: '#2c2838' });
  closeArm(ctx, [760, -250], [lerp(610, 560, k), lerp(720, 860, k)], 190, C.jesus, Lt, { hand: 'open', mirror: 1, sleeve: C.jesus.cloth.tunic });
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 540, 960, 420 + 60 * k, '#ffffff', 0.55 * k);
  ctx.restore();
};

// ---------------------------------------------------------- DAWN
S.dawn_road = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, { zoom: [1.0, 1.04] }, [600, 1050]);
  drawCached(ctx, cached('dawn', (x) => BG.dawnRoad(x)));
  BG.dawnDyn(ctx, t);
  // tiny procession far down the road
  ctx.fillStyle = '#1a0e12';
  for (let i = 0; i < 6; i++) {
    const x = 590 + i * 9 - lt * 1.5, y = 1100 + (i % 2) * 2;
    ctx.beginPath(); ctx.ellipse(x, y - 14, 3.2, 4, 0, 0, L.TAU); ctx.fill();
    ctx.fillRect(x - 3.5, y - 10, 7, 18);
  }
  // Asher foreground from behind (rim lit)
  const sil = { side: 1, key: '#4a3040', amb: '#1a1018', shadow: 0.85, rim: '#ffc070', rimA: 0.9, rimSide: 1, wrap: 0.2 };
  const pA = { x: 300, y: 1260, s: 64, facing: 1, by: 0.55, len: 9.4 };
  floorShadow(ctx, 330, 1880, 200, 0.5);
  actor(ctx, W, 'asher', t, pA, sil, looks({ gx: 0.6, gy: -0.1, yaw: 0.55, pitch: -0.02 }, { far: { gx: 0.6, gy: -0.1, yaw: 0.55, pitch: -0.04 } }));
};

S.dawn_asher_cu = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 820]);
  drawCached(ctx, bgView('dawn', (x) => BG.dawnRoad(x), { z: 1.8, cx: 620, cy: 1000 }, 14));
  BG.dawnDyn(ctx, t);
  const lk = looks({ gx: 0.4, gy: -0.3, yaw: 0.3, pitch: -0.1 }, { up: { gx: 0.25, gy: -0.7, yaw: 0.25, pitch: -0.24 }, far: { gx: 0.5, gy: -0.1, yaw: 0.35, pitch: -0.03 } });
  actor(ctx, W, 'asher', t, { x: 540, y: 1310, s: 185, facing: 1, by: 0.3, len: 5 }, LIGHT.dawn, lk);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 900, 500, 700, '#ffc070', 0.25);
  ctx.restore();
};

S.dawn_jesus = (ctx, W, t, lt, dur, p) => {
  camera(ctx, lt, dur, p, [540, 760]);
  drawCached(ctx, cached('dawnsky', (x) => { BG.dawnRoad(x, { horizon: 1500 }); }, 18));
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 540, 640, 1000, '#ffe0a0', 0.55);
  ctx.restore();
  const Lt = Object.assign({}, LIGHT.divine, { key: '#fff2dc', amb: '#e8c0a0', rim: '#ffe0a0' });
  const lk = looks({ gx: 0, gy: 0.05, yaw: 0.0, pitch: 0.03 }, { cam: { gx: 0.0, gy: 0.0, yaw: 0.0, pitch: 0.02 } });
  actor(ctx, W, 'jesus', t, { x: 540, y: 1120, s: 150, facing: 1, by: 0.0, len: 7 }, Lt, lk);
  BG.dust(ctx, t, { x: 0, y: 0, w: VW, h: VH }, 30, '#fff0c0', 51, 0.5, 3);
};

S.end_card = (ctx, W, t, lt, dur, p) => {
  drawCached(ctx, cached('dawnsky2', (x) => { BG.dawnRoad(x, { horizon: 1300 }); }, 26));
  ctx.fillStyle = rgba('#0a0608', 0.35); ctx.fillRect(0, 0, VW, VH);
  BG.dawnDyn(ctx, t, { horizon: 1300 });
  B.drawHalfBread(ctx, 470, 1300, 110, LIGHT.dawn, { face: 1, rot: -0.1 });
  B.drawHalfBread(ctx, 610, 1300, 110, LIGHT.dawn, { face: -1, rot: 0.1 });
};

// ------------------------------------------------------------------ grades
function grade(ctx, name, lt) {
  if (!name) return;
  ctx.save();
  if (name === 'memory_warm') {
    ctx.globalCompositeOperation = 'color'; ctx.fillStyle = rgba('#b08050', 0.35); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'soft-light'; ctx.fillStyle = rgba('#ffcc88', 0.35); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'source-over'; BG.vignette(ctx, 0.5, '#1a0c04', 0.4);
  } else if (name === 'memory_blue') {
    ctx.globalCompositeOperation = 'color'; ctx.fillStyle = rgba('#5a6a9a', 0.4); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'source-over'; BG.vignette(ctx, 0.55, '#02040a', 0.38);
    // soft edge haze
    ctx.globalCompositeOperation = 'screen';
    ctx.fillStyle = L.radial(ctx, VW / 2, VH / 2, VH * 0.35, VH * 0.75, [[0, rgba('#8aa0d0', 0)], [1, rgba('#8aa0d0', 0.18)]]);
    ctx.fillRect(0, 0, VW, VH);
  } else if (name === 'memory_gold') {
    ctx.globalCompositeOperation = 'soft-light'; ctx.fillStyle = rgba('#ffc070', 0.4); ctx.fillRect(0, 0, VW, VH);
    ctx.globalCompositeOperation = 'screen';
    ctx.fillStyle = L.radial(ctx, VW / 2, VH / 2, VH * 0.3, VH * 0.75, [[0, rgba('#fff0c0', 0)], [1, rgba('#fff0c0', 0.25)]]);
    ctx.fillRect(0, 0, VW, VH);
  }
  ctx.restore();
}

module.exports = { SHOTS: S, grade, LIGHT, VW, VH, cache };
