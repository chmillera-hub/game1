// Shared face parts: eyes with lids, brows, mouths, hands, pumpkins.
const { TAU, clamp, lerp, ellipse, rgba, smoothPath, noise } = require('./lib');

const INK = '#1c1726';

// Expression presets. Keys: bU brow raise, bA brow angle (+ inner up), bAsym, lidU, lidL,
// pup pupil size, smile, mOpen, mW, blush, tear, tongue, tilt, squash, sparkle
const EX_DEFAULT = { bU: 0, bA: 0, bAsym: 0, lidU: 0, lidL: 0, pup: 1, smile: 0, mOpen: 0, mW: 1, blush: 0, tear: 0, tongue: 0, tilt: 0, squash: 0, sparkle: 0 };
const EX = {
  neutral: {},
  happy: { smile: 0.7, lidL: 0.25, bU: 0.15 },
  joy: { smile: 1, lidL: 0.45, bU: 0.4, mOpen: 0.25, sparkle: 0.5 },
  sad: { smile: -0.45, bA: 0.7, lidU: 0.3, bU: 0.05, squash: 0.15 },
  verysad: { smile: -0.7, bA: 1, lidU: 0.42, squash: 0.35, tilt: 0.08 },
  wistful: { smile: 0.1, bA: 0.45, lidU: 0.3, sparkle: 0.2 },
  worried: { smile: -0.25, bA: 0.85, bU: 0.3 },
  surprised: { bU: 0.9, lidU: -0.3, mOpen: 0.35, pup: 0.85 },
  shock: { bU: 1, lidU: -0.45, mOpen: 0.6, pup: 0.7, squash: -0.3 },
  curious: { bU: 0.35, bAsym: 0.5, tilt: 0.12, smile: 0.1 },
  tender: { smile: 0.5, lidU: 0.28, bA: 0.35, tilt: 0.08, blush: 0.2 },
  amused: { smile: 0.65, lidL: 0.35, bAsym: 0.3, bU: 0.15 },
  sheepish: { smile: 0.4, bA: 0.5, bU: 0.3, tilt: -0.06, blush: 0.35 },
  smug: { smile: 0.55, lidU: 0.38, bAsym: 0.7, tilt: 0.08 },
  indignant: { smile: -0.35, bA: -0.75, bU: -0.1, mOpen: 0.12 },
  pain: { smile: -0.45, bA: 0.6, lidU: 0.6, lidL: 0.45, mOpen: 0.4 },
  laugh: { smile: 1, lidU: 0.5, lidL: 0.55, mOpen: 0.55, bU: 0.35 },
  giggle: { smile: 0.95, lidU: 0.45, lidL: 0.55, bU: 0.3, blush: 0.6 },
  concentrate: { bA: -0.55, bU: -0.2, lidU: 0.32, tongue: 1, smile: 0.05 },
  wonder: { bU: 0.7, lidU: -0.18, pup: 1.45, sparkle: 1, mOpen: 0.2, smile: 0.2 },
  teary: { bA: 0.95, lidU: 0.22, tear: 1, smile: -0.3, sparkle: 0.9 },
  sleepy: { lidU: 0.55, smile: 0.55, tilt: 0.12, blush: 0.25 },
  warm: { smile: 0.6, lidU: 0.15, lidL: 0.2, bA: 0.2, bU: 0.1 },
  thoughtful: { bA: 0.3, bU: 0.1, lidU: 0.28, bAsym: 0.2 },
  wry: { smile: 0.3, bAsym: 0.5, lidU: 0.25, bA: 0.3 },
  fond: { smile: 0.45, lidU: 0.22, bA: 0.25 },
  dreamy: { smile: 0.35, lidU: 0.42, bU: 0.2, bA: 0.2 },
  vulnerable: { smile: -0.1, bA: 0.85, lidU: 0.32, bU: 0.2 },
  sadsmile: { smile: 0.25, bA: 0.75, lidU: 0.35 },
  distant: { smile: -0.05, lidU: 0.4, bA: 0.35 },
  hopeful: { bU: 0.45, bA: 0.5, smile: 0.15, pup: 1.15, sparkle: 0.5 },
  proud: { smile: 0.7, bU: 0.2, lidL: 0.2, tilt: -0.05 },
  beam: { smile: 1, lidL: 0.5, lidU: 0.25, bU: 0.35, blush: 0.3 },
  playful: { smile: 0.65, bAsym: 0.6, lidL: 0.2, bU: 0.2 },
  concerned: { smile: -0.15, bA: 0.7, bU: 0.25 },
  gentle: { smile: 0.4, bA: 0.4, lidU: 0.25 },
  encouraging: { smile: 0.55, bU: 0.35, bA: 0.2, tilt: 0.07 },
  knowing: { smile: 0.5, lidU: 0.32, lidL: 0.25, bAsym: 0.2 },
  shy: { smile: 0.2, bA: 0.45, lidU: 0.22, tilt: -0.08, blush: 0.5 },
  grin: { smile: 1, lidL: 0.4, bU: 0.25, bAsym: 0.3, mOpen: 0.12 },
  remember: { bU: 0.5, bA: 0.35, lidU: 0.12, smile: 0.3, pup: 1.3, sparkle: 0.8 },
  content: { smile: 0.55, lidU: 0.45, lidL: 0.2, bA: 0.15 },
  moved: { smile: 0.35, bA: 0.6, lidU: 0.25, sparkle: 0.7 },
  tearsmile: { smile: 0.55, bA: 0.6, lidU: 0.3, lidL: 0.3, tear: 0.85, sparkle: 0.8 },
  humming: { lidU: 1, smile: 0.5, tilt: 0.1, blush: 0.3 },
  shush: { smile: 0.2, bU: 0.3, lidU: 0.2 },
  effort: { bA: -0.4, lidU: 0.3, smile: -0.2, mOpen: 0.2 },
  frozen: { bU: 0.75, lidU: -0.25, smile: -0.3, mW: 0.7, pup: 0.6 },
};
const exParams = (name) => ({ ...EX_DEFAULT, ...(EX[name] || {}) });

function eye(ctx, o) {
  const closure = clamp(o.lidU + (1 - Math.max(0, o.lidU)) * (o.blink || 0), -1, 1);
  const wide = Math.max(0, -closure);
  const lu = Math.max(0, closure);
  const rx = o.rx, ry = o.ry * (1 + wide * 0.22);
  ctx.save();
  ctx.translate(o.x, o.y);
  if (o.rot) ctx.rotate(o.rot);
  if (lu > 0.93) {
    // closed: just the lash curve (happy arc when smiling)
    ctx.beginPath();
    if (o.smile > 0.25) {
      ctx.moveTo(-rx * 0.95, ry * 0.25);
      ctx.quadraticCurveTo(0, -ry * 0.6, rx * 0.95, ry * 0.25);
    } else {
      ctx.moveTo(-rx * 0.95, ry * 0.1);
      ctx.quadraticCurveTo(0, ry * 0.6, rx * 0.95, ry * 0.1);
    }
    ctx.strokeStyle = o.line || INK;
    ctx.lineWidth = o.lw * 1.1;
    ctx.lineCap = 'round';
    ctx.stroke();
    ctx.restore();
    return;
  }
  ctx.beginPath();
  ellipse(ctx, 0, 0, rx, ry);
  ctx.fillStyle = o.sclera || '#fbfcff';
  ctx.fill();
  ctx.save();
  ctx.clip();
  const lx = clamp(o.look[0], -1, 1), ly = clamp(o.look[1], -1, 1);
  const ir = o.irisR;
  const ix = lx * (rx - ir * 0.75) * 0.8, iy = ly * (ry - ir * 0.75) * 0.65;
  ctx.beginPath();
  ellipse(ctx, ix, iy, ir, ir * 1.04);
  ctx.fillStyle = o.iris;
  ctx.fill();
  if (o.irisRing) {
    ctx.beginPath(); ellipse(ctx, ix, iy, ir * 0.78, ir * 0.8);
    ctx.strokeStyle = o.irisRing; ctx.lineWidth = ir * 0.18; ctx.stroke();
  }
  ctx.beginPath();
  ellipse(ctx, ix, iy, o.pupR * o.pup, o.pupR * o.pup * 1.04);
  ctx.fillStyle = o.pupil || '#0c0a14';
  ctx.fill();
  const sp = o.sparkle || 0;
  ctx.fillStyle = '#ffffff';
  ctx.beginPath(); ellipse(ctx, ix - ir * 0.32, iy - ir * 0.38, ir * (0.3 + sp * 0.08), ir * (0.3 + sp * 0.08)); ctx.fill();
  ctx.beginPath(); ellipse(ctx, ix + ir * 0.35, iy + ir * 0.33, ir * 0.13 + sp * ir * 0.06, ir * 0.13 + sp * ir * 0.06); ctx.fill();
  if (sp > 0.05) {
    ctx.globalAlpha = sp * 0.85;
    ctx.beginPath(); ellipse(ctx, ix + ir * 0.1, iy - ir * 0.62, ir * 0.12, ir * 0.12); ctx.fill();
    ctx.globalAlpha = 1;
  }
  if (o.warm) {
    ctx.globalAlpha = o.warm * 0.5;
    ctx.beginPath(); ellipse(ctx, ix, iy + ir * 0.5, ir * 0.7, ir * 0.35);
    ctx.fillStyle = '#ffb347'; ctx.fill(); ctx.globalAlpha = 1;
  }
  // upper lid
  if (lu > 0.01) {
    const yy = -ry + 2 * ry * lu;
    ctx.beginPath();
    ctx.moveTo(-rx - 4, -ry - 4);
    ctx.lineTo(rx + 4, -ry - 4);
    ctx.lineTo(rx + 4, yy - ry * 0.18);
    ctx.quadraticCurveTo(0, yy + ry * 0.3, -rx - 4, yy - ry * 0.18);
    ctx.closePath();
    ctx.fillStyle = o.lid;
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(rx + 4, yy - ry * 0.18);
    ctx.quadraticCurveTo(0, yy + ry * 0.3, -rx - 4, yy - ry * 0.18);
    ctx.strokeStyle = o.line || INK; ctx.lineWidth = o.lw * 0.9; ctx.stroke();
  }
  const ll = clamp(o.lidL || 0);
  if (ll > 0.01) {
    const yy = ry - ry * 0.95 * ll;
    ctx.beginPath();
    ctx.moveTo(-rx - 4, ry + 4);
    ctx.lineTo(rx + 4, ry + 4);
    ctx.lineTo(rx + 4, yy + ry * 0.2);
    ctx.quadraticCurveTo(0, yy - ry * 0.25, -rx - 4, yy + ry * 0.2);
    ctx.closePath();
    ctx.fillStyle = o.lid;
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(rx + 4, yy + ry * 0.2);
    ctx.quadraticCurveTo(0, yy - ry * 0.25, -rx - 4, yy + ry * 0.2);
    ctx.strokeStyle = rgba('#1c1726', 0.45); ctx.lineWidth = o.lw * 0.6; ctx.stroke();
  }
  if (o.tear > 0.02) {
    // wet shine along lower lid
    ctx.globalAlpha = o.tear * 0.75;
    ctx.beginPath();
    ctx.ellipse(0, ry * 0.78, rx * 0.8, ry * 0.2, 0, 0, Math.PI);
    ctx.strokeStyle = '#d9f1ff'; ctx.lineWidth = o.lw * 0.9; ctx.stroke();
    ctx.globalAlpha = 1;
  }
  ctx.restore();
  ctx.beginPath();
  ellipse(ctx, 0, 0, rx, ry);
  ctx.strokeStyle = o.line || INK;
  ctx.lineWidth = o.lw;
  ctx.stroke();
  ctx.restore();
}

// side: -1 for the eye on screen-left (its inner end points +x), +1 for screen-right
function brow(ctx, o) {
  const { x, y, w, th, side, raise, angle, color } = o;
  const inner = side < 0 ? 1 : -1; // direction of inner end
  const k = o.k || 1;
  const yi = y - raise * 14 * k - angle * 10 * k;
  const yo = y - raise * 14 * k + angle * 6 * k;
  const xi = x + inner * w * 0.5, xo = x - inner * w * 0.5;
  const arch = (o.arch ?? 6) * k * (1 - Math.max(0, angle) * 0.5);
  ctx.beginPath();
  ctx.moveTo(xo, yo);
  ctx.quadraticCurveTo(x, Math.min(yi, yo) - arch, xi, yi);
  ctx.strokeStyle = color;
  ctx.lineWidth = th;
  ctx.lineCap = 'round';
  ctx.stroke();
}

function mouth(ctx, o) {
  const w = o.w * (o.mW || 1) * (1 - (o.round || 0) * 0.3);
  const hw = w / 2;
  const sm = clamp(o.smile, -1, 1);
  const cy = -sm * w * 0.2;
  const ctrl = sm * w * 0.38;
  const open = clamp(o.open);
  ctx.save();
  ctx.translate(o.x, o.y);
  if (o.rot) ctx.rotate(o.rot);
  if (open < 0.05) {
    ctx.beginPath();
    ctx.moveTo(-hw, cy);
    ctx.quadraticCurveTo(0, ctrl, hw, cy);
    ctx.strokeStyle = o.line || INK;
    ctx.lineWidth = o.lw;
    ctx.lineCap = 'round';
    ctx.stroke();
  } else {
    const oh = open * w * 0.62 * (1 + (o.round || 0) * 0.45);
    const top = ctrl - oh * 0.22;
    const bot = Math.max(ctrl, cy) + oh * 0.95;
    const mpath = () => {
      ctx.beginPath();
      ctx.moveTo(-hw, cy);
      ctx.quadraticCurveTo(0, top, hw, cy);
      ctx.bezierCurveTo(hw * 1.02, cy + oh * 0.75, hw * 0.55, bot, 0, bot);
      ctx.bezierCurveTo(-hw * 0.55, bot, -hw * 1.02, cy + oh * 0.75, -hw, cy);
      ctx.closePath();
    };
    mpath();
    ctx.fillStyle = o.inside || '#3a1830';
    ctx.fill();
    ctx.save();
    ctx.clip();
    if (o.teeth) {
      ctx.fillStyle = o.teeth;
      ctx.beginPath();
      ctx.moveTo(-hw, cy - 2);
      ctx.quadraticCurveTo(0, top - 2, hw, cy - 2);
      ctx.lineTo(hw, cy + oh * 0.28);
      ctx.quadraticCurveTo(0, top + oh * 0.3, -hw, cy + oh * 0.28);
      ctx.closePath();
      ctx.fill();
    }
    ctx.fillStyle = o.tongueColor || '#ff8fa3';
    ctx.beginPath();
    ellipse(ctx, 0, bot - oh * 0.12, hw * 0.55, oh * 0.38);
    ctx.fill();
    ctx.restore();
    mpath();
    ctx.strokeStyle = o.line || INK;
    ctx.lineWidth = o.lw;
    ctx.lineJoin = 'round';
    ctx.stroke();
  }
  if (o.tongueOut > 0.05) {
    ctx.beginPath();
    ellipse(ctx, hw * 0.55, cy + 3 + o.lw, hw * 0.32 * o.tongueOut, hw * 0.3 * o.tongueOut);
    ctx.fillStyle = o.tongueColor || '#ff8fa3';
    ctx.fill();
    ctx.strokeStyle = o.line || INK; ctx.lineWidth = o.lw * 0.7; ctx.stroke();
  }
  // dimples / cheek creases on big smiles
  if (o.creases && sm > 0.45) {
    ctx.globalAlpha = (sm - 0.45) * 1.6;
    ctx.beginPath();
    ctx.arc(-hw - 4, cy - 4, 7, Math.PI * 0.6, Math.PI * 1.25);
    ctx.moveTo(hw + 4 + 7 * Math.cos(-Math.PI * 0.25), cy - 4 + 7 * Math.sin(-Math.PI * 0.25));
    ctx.arc(hw + 4, cy - 4, 7, -Math.PI * 0.25, Math.PI * 0.4);
    ctx.strokeStyle = o.line || INK; ctx.lineWidth = o.lw * 0.6; ctx.stroke();
    ctx.globalAlpha = 1;
  }
  ctx.restore();
}

function tearDrop(ctx, x, y, r, a) {
  if (a <= 0.02) return;
  ctx.save();
  ctx.globalAlpha = clamp(a);
  ctx.beginPath();
  ctx.moveTo(x, y - r * 1.6);
  ctx.quadraticCurveTo(x + r, y - r * 0.2, x + r * 0.9, y + r * 0.3);
  ctx.arc(x, y + r * 0.3, r * 0.9, 0, Math.PI);
  ctx.quadraticCurveTo(x - r, y - r * 0.2, x, y - r * 1.6);
  ctx.fillStyle = '#9fdcff';
  ctx.fill();
  ctx.strokeStyle = '#2a4a6a'; ctx.lineWidth = r * 0.22; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, x - r * 0.3, y + r * 0.1, r * 0.22, r * 0.3); ctx.fillStyle = '#fff'; ctx.fill();
  ctx.restore();
}

// A cartoon hand: palm + fingers pointing along angle `ang`.
function hand(ctx, x, y, ang, r, fill, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(ang);
  const line = o.line || INK, lw = o.lw || r * 0.14;
  const fingers = o.fingers ?? 4;
  const wig = o.wiggle || 0;
  const t = o.t || 0;
  const fl = r * (o.long ? 0.95 : 0.55);
  ctx.lineCap = 'round';
  for (let i = 0; i < fingers; i++) {
    const off = (i - (fingers - 1) / 2) * r * 0.36;
    const a = (i - (fingers - 1) / 2) * 0.12 + Math.sin(t * 13 + i * 1.7) * 0.22 * wig;
    const curl = o.fist ? 0.4 : 1;
    const len = (r * 0.5 + fl * curl) * (i === 0 || i === fingers - 1 ? 0.85 : 1);
    const ex = r * 0.2 + Math.cos(a) * len, ey = off + Math.sin(a) * len;
    ctx.beginPath(); ctx.moveTo(r * 0.2, off); ctx.lineTo(ex, ey);
    ctx.strokeStyle = line; ctx.lineWidth = r * 0.42 + lw * 2; ctx.stroke();
    ctx.strokeStyle = fill; ctx.lineWidth = r * 0.42; ctx.stroke();
  }
  // thumb
  const ts = o.thumbSide ?? 1;
  ctx.beginPath(); ctx.moveTo(-r * 0.1, ts * r * 0.2); ctx.lineTo(r * 0.45, ts * r * 0.8);
  ctx.strokeStyle = line; ctx.lineWidth = r * 0.45 + lw * 2; ctx.stroke();
  ctx.strokeStyle = fill; ctx.lineWidth = r * 0.45; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, 0, 0, r * 0.78, r * 0.72);
  ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.stroke();
  // cover finger roots
  ctx.beginPath(); ellipse(ctx, r * 0.05, 0, r * 0.6, r * 0.55); ctx.fillStyle = fill; ctx.fill();
  if (o.stitch) {
    ctx.beginPath(); ctx.moveTo(-r * 0.75, -r * 0.6); ctx.lineTo(-r * 0.75, r * 0.6);
    ctx.strokeStyle = o.stitch; ctx.lineWidth = lw * 0.8; ctx.stroke();
    for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(-r * 0.9, i * r * 0.22); ctx.lineTo(-r * 0.6, i * r * 0.22); ctx.stroke(); }
  }
  ctx.restore();
}

// Limb drawn as outlined thick polyline (sleeve / sheet arm / bone)
function limb(ctx, pts, w, fill, line = INK, lw = 5) {
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  ctx.strokeStyle = line; ctx.lineWidth = w + lw * 2; ctx.stroke();
  ctx.strokeStyle = fill; ctx.lineWidth = w; ctx.stroke();
}

// ── Pumpkins ──
const FACES = {
  // features in face-plane coords: u in [-1,1] across, v in [-1,1] down
  patch: {
    holes: [
      [[-0.62, -0.18], [-0.45, -0.42], [-0.22, -0.18], [-0.42, -0.26]],
      [[0.22, -0.18], [0.45, -0.42], [0.62, -0.18], [0.42, -0.26]],
      [[-0.12, 0.02], [0, -0.14], [0.12, 0.02]],
      [[-0.66, 0.12], [-0.3, 0.42], [0, 0.48], [0.3, 0.42], [0.66, 0.12], [0.3, 0.27], [0, 0.3], [-0.3, 0.27]],
    ],
    stitches: [[-0.36, 0.2, 0.5], [0, 0.26, 0.5], [0.36, 0.2, 0.5]],
  },
  pip: {
    holes: [
      'circle:-0.36:-0.22:0.2',
      [[0.2, -0.08], [0.38, -0.42], [0.55, -0.08]],
      [[-0.58, 0.18], [-0.35, 0.36], [-0.05, 0.44], [0.12, 0.38], [0.2, 0.5], [0.3, 0.36], [0.5, 0.1], [0.28, 0.24], [-0.05, 0.28], [-0.32, 0.25]],
    ],
  },
};

function drawPumpkin(ctx, o) {
  const { x, y, r } = o;
  const rx = r * 1.15, ry = r * 0.92;
  const th = (o.turn || 0) * Math.PI; // 0 = face toward camera
  const lit = clamp(o.lit || 0);
  const t = o.t || 0;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot);
  // glow behind
  if (lit > 0.01 && o.glow !== false) {
    const fl = 1 + 0.06 * noise(t * 7 + x);
    const g = ctx.createRadialGradient(0, 0, r * 0.4, 0, 0, r * 3.2 * fl);
    g.addColorStop(0, rgba('#ffb347', 0.45 * lit));
    g.addColorStop(1, rgba('#ff8a2a', 0));
    ctx.fillStyle = g;
    ctx.beginPath(); ellipse(ctx, 0, 0, r * 3.2 * fl, r * 3.2 * fl); ctx.fill();
  }
  const body = ctx.createRadialGradient(-rx * 0.3, -ry * 0.35, r * 0.1, 0, 0, rx * 1.1);
  body.addColorStop(0, o.light ? '#ffb15a' : '#f39a45');
  body.addColorStop(0.6, '#e2742a');
  body.addColorStop(1, '#a9471a');
  ctx.beginPath();
  // slightly lumpy body
  const pts = [];
  for (let i = 0; i < 24; i++) {
    const a = (i / 24) * TAU;
    const bump = 1 + 0.035 * Math.cos(a * 6 + th * 6);
    pts.push([Math.cos(a) * rx * bump, Math.sin(a) * ry * bump * (Math.sin(a) < 0 ? 0.97 : 1)]);
  }
  smoothPath(ctx, pts, true, 0.9);
  ctx.fillStyle = body;
  ctx.fill();
  ctx.save();
  ctx.clip();
  // ribs rotate with the turn
  ctx.lineWidth = r * 0.05;
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * TAU + th;
    const c = Math.cos(a);
    if (c < 0.05) continue;
    const sx = Math.sin(a) * rx;
    ctx.beginPath();
    ctx.moveTo(0, -ry * 0.92);
    ctx.quadraticCurveTo(sx * 1.25, 0, 0, ry * 0.95);
    ctx.strokeStyle = rgba('#8f3a12', 0.55 * c);
    ctx.stroke();
  }
  // face
  const face = o.face && FACES[o.face];
  if (face) {
    const carve = o.carve ?? 1;
    const proj = (u, v) => {
      const a = u * 0.95 + th;
      return [Math.sin(a) * rx * 0.97, v * ry * 0.95 + v * v * 0 - Math.abs(u) * 0.0, Math.cos(a)];
    };
    const order = face.holes;
    order.forEach((h, hi) => {
      let prog;
      if (o.face === 'pip') prog = hi === 0 ? clamp((carve - 0.05) / 0.2) : hi === 1 ? clamp((carve - 0.3) / 0.2) : clamp((carve - 0.55) / 0.4);
      else prog = 1;
      if (prog <= 0) return;
      ctx.beginPath();
      let vis = 0, n = 0;
      if (typeof h === 'string') {
        const [, cu, cv, cr] = h.split(':').map(Number);
        const P = [];
        for (let i = 0; i < 18; i++) { const a = (i / 18) * TAU; P.push(proj(cu + Math.cos(a) * cr * prog, cv + Math.sin(a) * cr * 1.1 * prog)); }
        P.forEach((p, i) => { vis += p[2]; n++; i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); });
      } else {
        let pts2 = h;
        if (prog < 1 && h.length > 3) {
          // reveal the mouth from left to right
          const maxU = lerp(-0.7, 0.7, prog);
          pts2 = h.map(([u, v]) => [Math.min(u, maxU), v]);
        }
        const P = pts2.map(([u, v]) => proj(u, v));
        P.forEach((p, i) => { vis += p[2]; n++; i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); });
      }
      ctx.closePath();
      if (vis / n < 0.12) return;
      ctx.globalAlpha = clamp((vis / n - 0.12) * 4);
      if (lit > 0.01) {
        const g = ctx.createRadialGradient(0, 0, 0, 0, 0, rx);
        g.addColorStop(0, mixHex('#5a2610', '#fff4b0', lit));
        g.addColorStop(1, mixHex('#40200f', '#ffab3a', lit));
        ctx.fillStyle = g;
      } else ctx.fillStyle = '#3a1a0d';
      ctx.fill();
      ctx.strokeStyle = rgba('#5c240b', 0.9); ctx.lineWidth = r * 0.035; ctx.stroke();
      ctx.globalAlpha = 1;
    });
    if (face.stitches) {
      for (const [u, v, h] of face.stitches) {
        const p1 = proj(u, v - h * 0.35), p2 = proj(u, v + h * 0.35);
        if (p1[2] < 0.2) continue;
        ctx.beginPath(); ctx.moveTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]);
        ctx.strokeStyle = '#d9692a'; ctx.lineWidth = r * 0.07; ctx.stroke();
      }
    }
  }
  // shading
  const sh = ctx.createLinearGradient(0, -ry, 0, ry);
  sh.addColorStop(0, 'rgba(255,220,160,0.12)');
  sh.addColorStop(1, 'rgba(60,10,30,0.28)');
  ctx.fillStyle = sh; ctx.fillRect(-rx * 1.2, -ry * 1.2, rx * 2.4, ry * 2.4);
  ctx.restore();
  smoothPath(ctx, pts, true, 0.9);
  ctx.strokeStyle = INK; ctx.lineWidth = r * 0.06; ctx.stroke();
  // curly stem
  ctx.beginPath();
  const sx0 = Math.sin(th) * r * 0.05;
  ctx.moveTo(sx0 - r * 0.09, -ry * 0.88);
  ctx.quadraticCurveTo(sx0 - r * 0.05, -ry * 1.25, sx0 + r * 0.12, -ry * 1.35);
  ctx.quadraticCurveTo(sx0 + r * 0.36, -ry * 1.42, sx0 + r * 0.3, -ry * 1.22);
  ctx.quadraticCurveTo(sx0 + r * 0.22, -ry * 1.12, sx0 + r * 0.16, -ry * 1.24);
  ctx.strokeStyle = INK; ctx.lineWidth = r * 0.16; ctx.lineCap = 'round'; ctx.stroke();
  ctx.strokeStyle = '#5f6b2c'; ctx.lineWidth = r * 0.1; ctx.stroke();
  ctx.restore();
}

function mixHex(a, b, t) {
  const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
  const c = [16, 8, 0].map((s) => Math.round(lerp((pa >> s) & 255, (pb >> s) & 255, clamp(t))));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

module.exports = { INK, EX, EX_DEFAULT, exParams, eye, brow, mouth, tearDrop, hand, limb, drawPumpkin, mixHex };
