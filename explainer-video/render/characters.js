// Character rig: heads with blinking eyelids, wandering gaze, eyebrows, lip-synced
// mouths, tears/blush, simple bodies with posable arms, plus the little helper bot.
const U = require('./util');
const { TAU, clamp, lerp, hash, noise, circle, ellipse, mix, rgba } = U;

const PEOPLE = {
  riley: {
    skin: '#b07650', shade: '#93603f', hair: '#2b1d17', hairHi: '#47322a', hairStyle: 'curly',
    shirt: '#3e8c98', shirtShade: '#2f6f79', top: 'hoodie', iris: '#3a2416', brow: '#24170f', lip: '#7a3f30',
  },
  alex: {
    skin: '#f0c6a0', shade: '#d9a982', hair: '#a1502a', hairHi: '#c0693c', hairStyle: 'beanie', beanie: '#e2674b', beanieShade: '#c4523a',
    shirt: '#e8b04a', shirtShade: '#cc9532', top: 'sweater', iris: '#3f7451', brow: '#80391b', lip: '#b8644f', glasses: true,
  },
  grandma: {
    skin: '#b98260', shade: '#9c6a4c', hair: '#e2ddd8', hairHi: '#f5f2ef', hairStyle: 'bun',
    shirt: '#b3808c', shirtShade: '#986774', top: 'apron', apron: '#f3e3c3', iris: '#3a2416', brow: '#c9c2ba', lip: '#80493a', wrinkles: true,
  },
  kid: {
    skin: '#b07650', shade: '#93603f', hair: '#2b1d17', hairHi: '#47322a', hairStyle: 'puffs',
    shirt: '#f2a65a', shirtShade: '#d98c43', top: 'tee', iris: '#3a2416', brow: '#24170f', lip: '#7a3f30', eyeScale: 1.18,
  },
};

// natural blinking: one blink every ~3.4s with jitter, sometimes a double blink
function blinkAmt(t, seed) {
  const period = 3.4, d = 0.16, k = Math.floor(t / period);
  let a = 0;
  for (let j = k - 1; j <= k; j++) {
    const bt = j * period + hash(j * 7.31 + seed * 13.7) * 2.3;
    const starts = hash(j * 3.17 + seed * 5.3) > 0.78 ? [bt, bt + 0.3] : [bt];
    for (const s of starts) if (t >= s && t < s + d) a = Math.max(a, Math.sin(Math.PI * (t - s) / d));
  }
  return a;
}
// tiny discrete eye darts so the eyes never look frozen
function saccade(t, seed) {
  const k = Math.floor(t * 0.9 + hash(seed) * 3), f = clamp((t * 0.9 + hash(seed) * 3 - k) / 0.08);
  const px = (hash(k * 1.7 + seed) - 0.5) * 0.22, py = (hash(k * 2.3 + seed * 3) - 0.5) * 0.16;
  const qx = (hash((k - 1) * 1.7 + seed) - 0.5) * 0.22, qy = (hash((k - 1) * 2.3 + seed * 3) - 0.5) * 0.16;
  return [lerp(qx, px, f), lerp(qy, py, f)];
}

function drawEye(ctx, P, cx, cy, side, f) {
  const es = P.eyeScale || 1;
  const rx = 19 * es, ry = 23 * es;
  const open = clamp(f.open), lidCol = mix(P.skin, P.shade, 0.35);
  ctx.save();
  ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, TAU);
  ctx.fillStyle = '#fbfaf7'; ctx.fill();
  ctx.save(); ctx.clip();
  const ix = cx + f.gx * 8 * es, iy = cy + f.gy * 8 * es + 2;
  circle(ctx, ix, iy, 13.5 * es, P.iris);
  circle(ctx, ix, iy, 7.5 * es, '#130d0a');
  circle(ctx, ix + 4.5 * es, iy - 5 * es, 4.2 * es, '#ffffff');
  circle(ctx, ix - 4 * es, iy + 4.5 * es, 1.8 * es, 'rgba(255,255,255,0.85)');
  if (f.shine > 0) { // watery eyes
    circle(ctx, ix - 5 * es, iy - 2 * es, 3.2 * es, `rgba(255,255,255,${0.9 * f.shine})`);
    ctx.beginPath(); ctx.ellipse(cx, cy + ry * 0.78, rx * 0.85, ry * 0.22, 0, 0, Math.PI);
    ctx.fillStyle = `rgba(190,225,255,${0.55 * f.shine})`; ctx.fill();
  }
  // upper lid
  const lidY = cy - ry + (1 - open) * 2.05 * ry;
  ctx.beginPath();
  ctx.moveTo(cx - rx - 3, cy - ry - 4); ctx.lineTo(cx + rx + 3, cy - ry - 4); ctx.lineTo(cx + rx + 3, lidY);
  ctx.quadraticCurveTo(cx, lidY + 7 * (1 - open) + 2, cx - rx - 3, lidY);
  ctx.closePath(); ctx.fillStyle = lidCol; ctx.fill();
  // lower lid (cheeks pushing up when smiling / squinting)
  if (f.squint > 0) {
    const ly = cy + ry - f.squint * ry * 0.9;
    ctx.beginPath(); ctx.moveTo(cx - rx - 3, cy + ry + 4); ctx.lineTo(cx + rx + 3, cy + ry + 4); ctx.lineTo(cx + rx + 3, ly + 4);
    ctx.quadraticCurveTo(cx, ly - 6, cx - rx - 3, ly + 4); ctx.closePath(); ctx.fillStyle = P.skin; ctx.fill();
  }
  ctx.restore();
  ctx.lineCap = 'round';
  if (open < 0.12) { // closed eye: a soft arc (curves up into ^ when smiling)
    const happy = f.squint > 0.4 ? -1 : 1;
    ctx.beginPath(); ctx.moveTo(cx - rx, cy + 3); ctx.quadraticCurveTo(cx, cy + 3 + 10 * happy, cx + rx, cy + 3);
    ctx.strokeStyle = '#2a1a14'; ctx.lineWidth = 4.5; ctx.stroke();
  } else {
    ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, TAU); ctx.strokeStyle = rgba('#3a2418', 0.35); ctx.lineWidth = 2; ctx.stroke();
    // lash line along the lid edge
    ctx.save(); ctx.beginPath(); ctx.ellipse(cx, cy, rx + 3, ry + 3, 0, 0, TAU); ctx.clip();
    ctx.beginPath(); ctx.moveTo(cx - rx - 3, lidY); ctx.quadraticCurveTo(cx, lidY + 7 * (1 - open) + 2, cx + rx + 3, lidY);
    ctx.strokeStyle = '#2a1a14'; ctx.lineWidth = 4.5; ctx.stroke(); ctx.restore();
    // little outer lash flick
    ctx.beginPath(); ctx.moveTo(cx + side * rx * 0.85, lidY + 2); ctx.lineTo(cx + side * (rx + 7), lidY - 5);
    ctx.strokeStyle = '#2a1a14'; ctx.lineWidth = 3.5; ctx.stroke();
  }
  ctx.restore();
}

function drawBrow(ctx, P, side, f) {
  const x0 = side * 15, x1 = side * 58;
  const base = -44 - f.brow * 12;
  const yi = base - f.browTilt * 10, yo = base + f.browTilt * 5 + 4;
  ctx.beginPath(); ctx.moveTo(x0, yi); ctx.quadraticCurveTo((x0 + x1) / 2, Math.min(yi, yo) - 7, x1, yo);
  ctx.strokeStyle = P.brow; ctx.lineWidth = 8; ctx.lineCap = 'round'; ctx.stroke();
}

function drawMouth(ctx, P, f) {
  const y = 52, smile = f.smile, open = clamp(f.open), O = clamp(f.mouthO || 0);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (O > 0.05) {
    const rx = 11 + O * 5 + open * 3, ry = 12 + O * 9 + open * 6;
    ellipse(ctx, 0, y + 4, rx, ry, '#4a1d1a');
    ellipse(ctx, 0, y + 4 + ry * 0.5, rx * 0.6, ry * 0.35, '#c86566');
    ctx.beginPath(); ctx.ellipse(0, y + 4, rx, ry, 0, 0, TAU); ctx.strokeStyle = P.lip; ctx.lineWidth = 3.5; ctx.stroke();
    return;
  }
  const w = 22 + f.width * 9 + Math.max(0, smile) * 8;
  const cy = y - smile * 8;
  if (open < 0.07) {
    ctx.beginPath(); ctx.moveTo(-w, cy); ctx.quadraticCurveTo(0, y + smile * 15, w, cy);
    ctx.strokeStyle = P.lip; ctx.lineWidth = 5; ctx.stroke();
    return;
  }
  const up = y + smile * 7 - open * 3, lo = y + smile * 9 + 6 + open * 32;
  ctx.beginPath(); ctx.moveTo(-w, cy); ctx.quadraticCurveTo(0, up, w, cy); ctx.quadraticCurveTo(0, lo, -w, cy); ctx.closePath();
  ctx.fillStyle = '#4a1d1a'; ctx.fill();
  ctx.save(); ctx.clip();
  if (open > 0.3) { ctx.fillStyle = '#fbf7ef'; ctx.fillRect(-w, Math.min(up, cy) - 10, w * 2, (up - Math.min(up, cy)) * 0.5 + 15); }
  ellipse(ctx, 0, lo - 4, w * 0.62, 11, '#c86566');
  ctx.restore();
  ctx.beginPath(); ctx.moveTo(-w, cy); ctx.quadraticCurveTo(0, up, w, cy); ctx.quadraticCurveTo(0, lo, -w, cy); ctx.closePath();
  ctx.strokeStyle = P.lip; ctx.lineWidth = 3.5; ctx.stroke();
}

function backHair(ctx, P) {
  ctx.fillStyle = P.hair;
  if (P.hairStyle === 'curly') {
    for (let i = 0; i <= 12; i++) {
      const a = Math.PI * (0.92 + i * 0.105);
      circle(ctx, Math.cos(a) * 92, Math.sin(a) * 92 - 18, 40 + (i % 3) * 4, P.hair);
    }
    circle(ctx, 0, -40, 98, P.hair);
  } else if (P.hairStyle === 'bun') {
    circle(ctx, 0, -114, 40, P.hair);
    ctx.beginPath(); ctx.arc(0, -114, 22, 0.5, 5.2); ctx.strokeStyle = rgba('#9a938c', 0.7); ctx.lineWidth = 4; ctx.stroke();
    circle(ctx, 0, -20, 104, P.hair);
  } else if (P.hairStyle === 'puffs') {
    circle(ctx, -82, -72, 42, P.hair); circle(ctx, 82, -72, 42, P.hair);
    circle(ctx, 0, -30, 100, P.hair);
  } else if (P.hairStyle === 'beanie') {
    ellipse(ctx, -84, 4, 26, 60, P.hair); ellipse(ctx, 84, 4, 26, 60, P.hair);
  }
}

function frontHair(ctx, P) {
  if (P.hairStyle === 'curly') {
    const curls = [[-62, -78, 32], [-26, -96, 34], [14, -98, 33], [50, -84, 31], [80, -58, 26], [-86, -52, 26], [-6, -112, 26], [34, -112, 22]];
    for (const [x, y, r] of curls) circle(ctx, x, y, r, P.hair);
    for (const [x, y, r] of [[-30, -104, 10], [20, -108, 9], [56, -90, 8], [-66, -84, 8]]) circle(ctx, x, y, r, P.hairHi);
  } else if (P.hairStyle === 'bun') {
    ctx.beginPath(); ctx.moveTo(-100, -10); ctx.bezierCurveTo(-104, -96, -40, -112, 4, -104);
    ctx.bezierCurveTo(-30, -84, -60, -60, -100, -10); ctx.fillStyle = P.hair; ctx.fill();
    ctx.beginPath(); ctx.moveTo(100, -10); ctx.bezierCurveTo(104, -96, 40, -112, -4, -104);
    ctx.bezierCurveTo(30, -84, 60, -60, 100, -10); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-70, -70); ctx.quadraticCurveTo(-40, -92, -6, -100); ctx.strokeStyle = rgba('#a59e97', 0.6); ctx.lineWidth = 3; ctx.stroke();
  } else if (P.hairStyle === 'puffs') {
    ctx.beginPath(); ctx.moveTo(-99, -14); ctx.bezierCurveTo(-104, -146, 104, -146, 99, -14);
    ctx.bezierCurveTo(70, -62, -70, -62, -99, -14); ctx.fillStyle = P.hair; ctx.fill();
    circle(ctx, -82, -72, 42, P.hair); circle(ctx, 82, -72, 42, P.hair);
    circle(ctx, -90, -84, 10, P.hairHi); circle(ctx, 74, -88, 10, P.hairHi);
  } else if (P.hairStyle === 'beanie') {
    ctx.beginPath(); ctx.moveTo(-98, -30); ctx.bezierCurveTo(-60, -40, -30, -50, 10, -48); ctx.lineTo(-30, -20);
    ctx.quadraticCurveTo(-70, -10, -98, -30); ctx.fillStyle = P.hair; ctx.fill();
    ctx.beginPath(); ctx.moveTo(-106, -36); ctx.bezierCurveTo(-106, -150, 106, -150, 106, -36); ctx.closePath(); ctx.fillStyle = P.beanie; ctx.fill();
    U.fillRR(ctx, -110, -60, 220, 40, 18, P.beanieShade);
    for (let i = -4; i <= 4; i++) U.line(ctx, i * 24, -56, i * 24, -24, rgba('#8f3a28', 0.35), 4);
    circle(ctx, 0, -138, 20, P.beanieShade); circle(ctx, -5, -143, 8, rgba('#ffffff', 0.2));
  }
}

function glasses(ctx) {
  ctx.lineWidth = 5; ctx.strokeStyle = '#3a2a22';
  for (const s of [-1, 1]) {
    ctx.beginPath(); U.rrect(ctx, s * 38 - 28, -27, 56, 50, 18); ctx.fillStyle = 'rgba(255,255,255,0.10)'; ctx.fill(); ctx.stroke();
  }
  ctx.beginPath(); ctx.moveTo(-10, -8); ctx.quadraticCurveTo(0, -16, 10, -8); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-66, -8); ctx.lineTo(-96, -12); ctx.moveTo(66, -8); ctx.lineTo(96, -12); ctx.stroke();
}

const POSES = {
  down:  [[[-140, 180], [-180, 380], [-176, 600]], [[140, 180], [180, 380], [176, 600]]],
  phone: [[[-140, 180], [-168, 390], [-46, 330]], [[140, 180], [168, 390], [46, 330]]],
  chin:  [[[-140, 180], [-178, 360], [-168, 540]], [[140, 180], [190, 300], [58, 112]]],
  point: [[[-140, 180], [-178, 360], [-168, 540]], [[140, 180], [236, 150], [292, 34]]],
  wave:  [[[-140, 180], [-178, 360], [-168, 540]], [[140, 180], [236, 120], [262, -26]]],
  palm:  [[[-140, 180], [-178, 360], [-168, 540]], [[140, 180], [206, 340], [188, 250]]],
  gasp:  [[[-140, 180], [-186, 300], [-100, 58]], [[140, 180], [186, 300], [100, 58]]],
  desk:  [[[-140, 180], [-180, 340], [-70, 380]], [[140, 180], [180, 340], [70, 380]]],
  fist:  [[[-140, 180], [-178, 360], [-168, 540]], [[140, 180], [220, 200], [196, 70]]],
  counter: [[[-140, 180], [-188, 300], [-72, 336]], [[140, 180], [188, 300], [72, 336]]],
  counterHigh: [[[-140, 180], [-180, 250], [-72, 228]], [[140, 180], [180, 250], [72, 228]]],
};
function resolvePose(o) {
  const a = o.arms || 'down';
  if (typeof a === 'string') return POSES[a] || POSES.down;
  const A = POSES[a.a], B = POSES[a.b], k = clamp(a.k);
  return A.map((arm, i) => arm.map((p, j) => [lerp(p[0], B[i][j][0], k), lerp(p[1], B[i][j][1], k)]));
}

function drawBody(ctx, P, o) {
  // torso
  ctx.beginPath();
  ctx.moveTo(-46, 112); ctx.bezierCurveTo(-112, 116, -162, 140, -170, 214);
  ctx.lineTo(-196, 1000); ctx.lineTo(196, 1000); ctx.lineTo(170, 214);
  ctx.bezierCurveTo(162, 140, 112, 116, 46, 112); ctx.closePath();
  ctx.fillStyle = P.shirt; ctx.fill();
  if (P.top === 'hoodie') {
    ctx.beginPath(); ctx.moveTo(-96, 116); ctx.quadraticCurveTo(0, 190, 96, 116); ctx.quadraticCurveTo(0, 150, -96, 116);
    ctx.fillStyle = P.shirtShade; ctx.fill();
    for (const s of [-1, 1]) { U.line(ctx, s * 24, 150, s * 28, 238, '#ece5d8', 5); circle(ctx, s * 28, 242, 6, '#ece5d8'); }
    U.fillRR(ctx, -70, 420, 140, 70, 20, P.shirtShade);
  } else if (P.top === 'sweater') {
    ctx.beginPath(); ctx.arc(0, 104, 52, 0.15 * Math.PI, 0.85 * Math.PI); ctx.strokeStyle = P.shirtShade; ctx.lineWidth = 14; ctx.stroke();
  } else if (P.top === 'apron') {
    ctx.beginPath(); ctx.moveTo(-104, 250); ctx.quadraticCurveTo(0, 230, 104, 250); ctx.lineTo(126, 1000); ctx.lineTo(-126, 1000); ctx.closePath();
    ctx.fillStyle = P.apron; ctx.fill();
    U.line(ctx, -88, 252, -46, 120, P.apron, 12); U.line(ctx, 88, 252, 46, 120, P.apron, 12);
    U.fillRR(ctx, -50, 330, 100, 60, 12, mix(P.apron, '#d8c09c', 0.6));
    for (let i = -3; i <= 3; i++) circle(ctx, i * 13, 128 + Math.abs(i) * -3 + 10, 5, '#f6f0e6');
  } else if (P.top === 'tee') {
    ctx.beginPath(); ctx.arc(0, 104, 46, 0.15 * Math.PI, 0.85 * Math.PI); ctx.strokeStyle = P.shirtShade; ctx.lineWidth = 9; ctx.stroke();
  }
}

function drawArms(ctx, P, o, pose, beforeHands) {
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (let ai = 0; ai < pose.length; ai++) {
    const [sh, el, hd] = pose[ai];
    const off = ai === 1 && o.armOffset ? o.armOffset : [0, 0];
    ctx.save(); ctx.translate(off[0], off[1]);
    ctx.beginPath(); ctx.moveTo(...sh); ctx.quadraticCurveTo(el[0], el[1], hd[0], hd[1]);
    ctx.strokeStyle = P.shirtShade; ctx.lineWidth = 60; ctx.stroke();
    ctx.strokeStyle = P.shirt; ctx.lineWidth = 50; ctx.stroke();
    if (off[0] || off[1]) { ctx.beginPath(); ctx.arc(sh[0], sh[1], 25, 0, TAU); ctx.fillStyle = P.shirtShade; ctx.fill(); }
    ctx.restore();
  }
  if (beforeHands) beforeHands();
  const pname = typeof o.arms === 'string' ? o.arms : (o.arms && (o.arms.k > 0.5 ? o.arms.b : o.arms.a));
  pose.forEach((arm, i) => {
    let [x, y] = arm[2];
    if (i === 1 && o.armOffset) { x += o.armOffset[0]; y += o.armOffset[1]; }
    if (pname === 'phone' && o.typing) y -= Math.abs(Math.sin(o.t * 13 + i * 1.9)) * 9;
    circle(ctx, x, y, 27, P.shade); circle(ctx, x, y - 2, 25, P.skin);
    if (pname === 'point' && i === 1) { ctx.save(); ctx.translate(x, y); ctx.rotate(-1.0); U.fillRR(ctx, -7, -52, 15, 40, 8, P.skin); ctx.restore(); }
  });
}

function drawPhoneInHands(ctx, o) {
  ctx.save(); ctx.translate(0, 300); ctx.rotate(o.phoneTilt || 0);
  U.fillRR(ctx, -56, -96, 112, 192, 18, '#1d1d26');
  U.fillRR(ctx, -48, -86, 96, 172, 12, o.phoneScreen || '#9fc4ff');
  ctx.restore();
}

/*
 * drawPerson(ctx, name, o)
 *   o.x, o.y: head center; o.s: scale (head radius = 100*s); o.t: time
 *   face:  lids, gx, gy, brow, browTilt, smile, open, width, mouthO, squint, blush, tear, shine
 *   body:  tilt, arms (pose name, {a,b,k}, or 'none'), typing, phoneScreen, noBody, noHead, bob
 */
function drawPerson(ctx, name, o) {
  const P = PEOPLE[name];
  const t = o.t || 0, seed = o.seed != null ? o.seed : name.length * 17;
  const bob = o.bob !== false ? Math.sin(t * 1.7 + seed) * 2.5 : 0;
  ctx.save();
  ctx.translate(o.x, o.y); ctx.scale(o.s || 1, o.s || 1);
  if (o.flip) ctx.scale(-1, 1);
  const pose = resolvePose(o);
  if (!o.noBody) {
    ctx.save(); ctx.translate(0, bob * 0.6);
    // neck
    ctx.fillStyle = P.shade; ctx.fillRect(-28, 60, 56, 70);
    drawBody(ctx, P, o);
    ctx.restore();
  }
  // head (tilts around the neck)
  if (!o.noHead) {
  ctx.save(); ctx.translate(0, bob + 90); ctx.rotate(o.tilt || 0); ctx.translate(0, -90);
  backHair(ctx, P);
  for (const s of [-1, 1]) { circle(ctx, s * 96, 10, 19, P.skin); ctx.beginPath(); ctx.arc(s * 96, 10, 9, s > 0 ? -1.2 : 1.9, s > 0 ? 1.2 : 4.3); ctx.strokeStyle = P.shade; ctx.lineWidth = 4; ctx.stroke(); }
  ctx.beginPath(); ctx.ellipse(0, 0, 97, 104, 0, 0, TAU); ctx.fillStyle = P.skin; ctx.fill();
  // soft chin shadow
  ctx.beginPath(); ctx.ellipse(0, 86, 52, 14, 0, 0, Math.PI); ctx.fillStyle = rgba(P.shade, 0.35); ctx.fill();

  const [sx, sy] = saccade(t, seed);
  const blink = o.noBlink ? 0 : blinkAmt(t, seed);
  const f = {
    open: clamp((o.lids != null ? o.lids : 0.9) * (1 - blink)),
    gx: clamp((o.flip ? -1 : 1) * (o.gx || 0) + sx, -1, 1), gy: clamp((o.gy || 0) + sy, -1, 1),
    brow: o.brow || 0, browTilt: o.browTilt || 0, smile: o.smile || 0,
    open_m: o.open || 0, squint: o.squint || 0, shine: o.shine || 0,
  };
  if (o.blush > 0) { ellipse(ctx, -60, 34, 18, 10, rgba('#ff6f6f', 0.32 * o.blush)); ellipse(ctx, 60, 34, 18, 10, rgba('#ff6f6f', 0.32 * o.blush)); }
  if (P.wrinkles) {
    ctx.strokeStyle = rgba(P.shade, 0.8); ctx.lineWidth = 3; ctx.lineCap = 'round';
    for (const s of [-1, 1]) {
      ctx.beginPath(); ctx.moveTo(s * 62, -6); ctx.lineTo(s * 72, -12); ctx.moveTo(s * 62, 2); ctx.lineTo(s * 73, 4); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(s * 30, 30); ctx.quadraticCurveTo(s * 40, 48, s * 36, 64); ctx.stroke();
    }
  }
  drawEye(ctx, P, -37, -4, -1, f);
  drawEye(ctx, P, 37, -4, 1, f);
  drawBrow(ctx, P, -1, f); drawBrow(ctx, P, 1, f);
  // nose
  ctx.beginPath(); ctx.moveTo(-9, 24); ctx.quadraticCurveTo(0, 33, 9, 24); ctx.strokeStyle = P.shade; ctx.lineWidth = 4.5; ctx.lineCap = 'round'; ctx.stroke();
  drawMouth(ctx, P, { smile: f.smile, open: o.open || 0, width: o.width || 0.4, mouthO: o.mouthO || 0 });
  if (o.tear > 0 && o.tear < 1) {
    const ty = 22 + o.tear * 92, a = 1 - U.prog(o.tear, 0.75, 1);
    ctx.beginPath(); ctx.moveTo(48, 20); ctx.quadraticCurveTo(52, ty * 0.6 + 8, 50, ty - 6); ctx.strokeStyle = `rgba(170,215,255,${0.55 * a})`; ctx.lineWidth = 4; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(50, ty - 13); ctx.bezierCurveTo(57, ty - 2, 57, ty + 6, 50, ty + 7); ctx.bezierCurveTo(43, ty + 6, 43, ty - 2, 50, ty - 13);
    ctx.fillStyle = `rgba(150,205,255,${0.95 * a})`; ctx.fill(); circle(ctx, 48, ty + 1, 2.2, `rgba(255,255,255,${a})`);
  }
  frontHair(ctx, P);
  if (P.glasses) glasses(ctx);
  ctx.restore();
  }

  if (!o.noBody && o.arms !== 'none') {
    ctx.save(); ctx.translate(0, bob * 0.6);
    const a = o.arms;
    const hasPhone = a === 'phone' || (a && typeof a === 'object' && ((a.a === 'phone' && a.k < 0.5) || (a.b === 'phone' && a.k >= 0.5)));
    drawArms(ctx, P, o, pose, hasPhone ? () => drawPhoneInHands(ctx, o) : null);
    ctx.restore();
  }
  ctx.restore();
}

// The helper bot: a soft rounded "screen" creature. Deliberately generic (not any company's logo).
function drawBot(ctx, x, y, s, t, m = {}) {
  ctx.save(); ctx.translate(x, y + Math.sin(t * 2.4) * 6 * (m.still ? 0 : 1)); ctx.scale(s, s);
  if (m.glow) { ctx.fillStyle = U.rgrad(ctx, 0, 0, 150, [[0, rgba('#b9a8ff', 0.55 * m.glow)], [1, rgba('#b9a8ff', 0)]]); ctx.fillRect(-150, -150, 300, 300); }
  // antenna
  U.line(ctx, 0, -62, 0, -86, '#6f5fd6', 6);
  circle(ctx, 0, -92, 10 + Math.sin(t * 5) * 1.5, m.working ? '#ffd166' : '#c7bbff');
  // nub arms
  const wave = m.wave ? Math.sin(t * 9) * 0.6 : 0;
  ctx.save(); ctx.translate(66, 10); ctx.rotate(-0.4 - (m.wave ? 1.2 : 0) + wave); U.fillRR(ctx, -10, -8, 46, 20, 10, '#7c6ae6'); ctx.restore();
  ctx.save(); ctx.translate(-66, 10); ctx.rotate(0.4); U.fillRR(ctx, -36, -8, 46, 20, 10, '#7c6ae6'); ctx.restore();
  U.fillRR(ctx, -70, -64, 140, 128, 38, '#8f7cf7');
  U.fillRR(ctx, -54, -48, 108, 84, 26, '#f1edff');
  const bl = blinkAmt(t, 99);
  const look = m.look || [0, 0];
  for (const sd of [-1, 1]) {
    const ex = sd * 22 + look[0] * 6, ey = -8 + look[1] * 5;
    if (m.happy) {
      ctx.beginPath(); ctx.moveTo(ex - 10, ey + 4); ctx.quadraticCurveTo(ex, ey - 9, ex + 10, ey + 4);
      ctx.strokeStyle = '#2b2350'; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.stroke();
    } else {
      ellipse(ctx, ex, ey, 9, 13 * (1 - bl) + 1.5, '#2b2350');
      if (bl < 0.5) circle(ctx, ex + 3, ey - 5, 3, '#ffffff');
    }
  }
  ctx.beginPath(); ctx.moveTo(-12, 16); ctx.quadraticCurveTo(0, m.talk ? 28 + Math.sin(t * 20) * 4 : 24, 12, 16);
  ctx.strokeStyle = '#2b2350'; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.stroke();
  if (m.blush !== false) { ellipse(ctx, -38, 14, 8, 5, rgba('#ff8fa3', 0.6)); ellipse(ctx, 38, 14, 8, 5, rgba('#ff8fa3', 0.6)); }
  ctx.restore();
}

module.exports = { PEOPLE, drawPerson, drawBot, blinkAmt };
