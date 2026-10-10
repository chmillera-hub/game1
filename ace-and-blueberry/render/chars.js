// Characters: Ace (head, bust, hands), Blueberry (hamster + purple ball), baby brother.
const L = require('./lib');
const { clamp, lerp, ellipse, fillStroke, rng, sparkle, star } = L;

const SKIN = '#FFEFE6', SKIN_LINE = '#E3AE98';
const HAIR = '#F2803E', HAIR_DARK = '#D4561F', HAIR_LIGHT = '#FFA868';
const EYE_LINE = '#2C5BC4', PUPIL = '#1A2370';

// ---------------------------------------------------------------- Ace ----
// precomputed curl positions (deterministic)
const CURLS_BACK = (() => {
  const r = rng(42), arr = [];
  for (let i = 0; i <= 26; i++) {
    const a = Math.PI * 0.86 + (i / 26) * Math.PI * 1.28;
    arr.push({ x: Math.cos(a) * 112, y: Math.sin(a) * 112 - 4, r: 30 + r() * 8, s: r() * 6 });
  }
  for (const side of [-1, 1]) {
    for (let j = 0; j < 4; j++) {
      arr.push({ x: side * (108 + r() * 14 - j * 3), y: 30 + j * 26, r: 27 + r() * 6, s: r() * 6 });
    }
  }
  for (let i = 0; i < 9; i++) {
    const a = Math.PI * 1.08 + (i / 8) * Math.PI * 0.84;
    arr.push({ x: Math.cos(a) * 80, y: Math.sin(a) * 86 - 10, r: 30, s: r() * 6 });
  }
  return arr;
})();
const CURLS_FRONT = (() => {
  const r = rng(7), arr = [];
  for (let i = 0; i < 8; i++) {
    const x = -84 + i * 24;
    arr.push({ x, y: -78 + Math.abs(x) * 0.25 + r() * 4, r: 21 + r() * 4, s: r() * 6 });
  }
  return arr;
})();

function curl(ctx, c, bounce) {
  const y = c.y + bounce * (c.r / 30);
  ellipse(ctx, c.x, y, c.r, c.r * 0.95); ctx.fillStyle = HAIR; ctx.fill();
  // little spiral curl lines (like the pencil curls in the drawings)
  ctx.beginPath();
  const rr = c.r * 0.55;
  for (let k = 0; k <= 18; k++) {
    const a = c.s + k * 0.55, rad = rr * (1 - k / 22);
    const px = c.x + Math.cos(a) * rad, py = y + Math.sin(a) * rad * 0.9;
    k ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
  }
  ctx.strokeStyle = HAIR_DARK; ctx.lineWidth = 2.6; ctx.stroke();
}

function aceHairBack(ctx, bounce) {
  for (const c of CURLS_BACK) curl(ctx, c, bounce);
}
function aceHairFront(ctx, bounce) {
  for (const c of CURLS_FRONT) curl(ctx, c, bounce * 0.6);
}

function aceEye(ctx, side, e) {
  const cx = side * 38, cy = -2, rx = 29, ry = 33;
  const closed = Math.max(e.closed || 0, 0);
  const lid = clamp(Math.max(e.blink || 0, e.lid || 0));
  if (e.squint > 0.5) { // happy ^^ eyes
    ctx.beginPath(); ctx.moveTo(cx - 24, cy + 8); ctx.quadraticCurveTo(cx, cy - 26, cx + 24, cy + 8);
    ctx.strokeStyle = EYE_LINE; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.stroke();
    return;
  }
  if (e.wince > 0.5) { // squeezed > <
    ctx.beginPath();
    ctx.moveTo(cx - side * 20, cy - 16); ctx.lineTo(cx + side * 16, cy + 1); ctx.lineTo(cx - side * 20, cy + 16);
    ctx.strokeStyle = EYE_LINE; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
    return;
  }
  if (closed > 0.5 || lid > 0.45) { // closed: gentle downward arc with lashes
    ctx.beginPath(); ctx.moveTo(cx - 25, cy + 4); ctx.quadraticCurveTo(cx, cy + 22, cx + 25, cy + 4);
    ctx.strokeStyle = EYE_LINE; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.stroke();
    for (let k = -1; k <= 1; k++) {
      const px = cx + k * 13 + side * 4, py = cy + 12 + (k === 0 ? 2 : 0);
      ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px + side * 5 + k * 3, py + 9);
      ctx.lineWidth = 3.5; ctx.stroke();
    }
    return;
  }
  const wide = e.wide || 0;
  const ery = ry * (1 + wide * 0.12);
  ellipse(ctx, cx, cy, rx, ery); ctx.fillStyle = '#fff'; ctx.fill();
  // pupil
  ctx.save(); ellipse(ctx, cx, cy, rx - 2, ery - 2); ctx.clip();
  const lx = (e.look ? e.look[0] : 0), ly = (e.look ? e.look[1] : 0);
  const px = cx + lx * 12 + side * 1, py = cy + 7 + ly * 12;
  const pr = 13 * (1 - wide * 0.15);
  ellipse(ctx, px, py, pr, pr * 1.12); ctx.fillStyle = PUPIL; ctx.fill();
  ellipse(ctx, px - 4, py - 5, 4.2, 4.2); ctx.fillStyle = '#fff'; ctx.fill();
  ellipse(ctx, px + 4.5, py + 4, 2, 2); ctx.fill();
  if (e.sparkle > 0) { sparkle(ctx, px - 3, py - 4, 9 * e.sparkle, '#fff'); sparkle(ctx, px + 6, py + 6, 4 * e.sparkle, '#BFE3FF'); }
  // eyelid
  if (lid > 0.02) {
    const ly2 = cy - ery + lid * ery * 2.05;
    ctx.fillStyle = SKIN; ctx.fillRect(cx - rx - 4, cy - ery - 4, rx * 2 + 8, ly2 - (cy - ery - 4));
    ctx.beginPath(); ctx.moveTo(cx - rx, ly2); ctx.quadraticCurveTo(cx, ly2 + 6, cx + rx, ly2);
    ctx.strokeStyle = EYE_LINE; ctx.lineWidth = 4; ctx.stroke();
  }
  ctx.restore();
  ellipse(ctx, cx, cy, rx, ery); ctx.strokeStyle = EYE_LINE; ctx.lineWidth = 4.5; ctx.stroke();
  // lashes on the upper lid
  const lidY = lid > 0.02 ? (cy - ery + lid * ery * 2.05) : null;
  ctx.lineCap = 'round'; ctx.strokeStyle = EYE_LINE; ctx.lineWidth = 4.5;
  const angs = [-2.15, -1.75, -1.35, -0.95].map(a => side > 0 ? a : -Math.PI - a);
  for (const a of angs) {
    let x0 = cx + Math.cos(a) * rx, y0 = cy + Math.sin(a) * ery;
    if (lidY !== null) y0 += lidY - (cy - ery);
    const dx = Math.cos(a) * 15 + side * 4, dy = Math.sin(a) * 17 - 3;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(x0 + dx * 0.4, y0 + dy * 0.8, x0 + dx, y0 + dy); ctx.stroke();
  }
}

function aceBrow(ctx, side, e) {
  const b = e.brow || {};
  const raise = b.raise || 0, worry = b.worry || 0, angry = b.angry || 0;
  const cx = side * 38, y = -56 - raise * 9;
  const inner = -worry * 9 + angry * 9, outer = worry * 3 - angry * 3;
  ctx.beginPath();
  ctx.moveTo(cx - side * 4 + side * -14, y + inner);
  ctx.quadraticCurveTo(cx, y - 7 - raise * 3, cx + side * 20, y + outer + 2);
  ctx.strokeStyle = '#B9461A'; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.stroke();
}

function aceMouth(ctx, e) {
  const smile = e.smile === undefined ? 0.6 : e.smile;
  const open = clamp(e.open || 0, 0, 1.1), round = e.round || 0;
  const cy = 58;
  const hw = (19 + Math.max(0, smile) * 5 + (e.teeth ? 6 : 0)) * (1 - round * 0.45);
  const cyC = cy - smile * 7;
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (e.wavy) { // wobbly uncomfortable mouth
    ctx.beginPath(); ctx.moveTo(-18, cy);
    for (let i = 1; i <= 6; i++) ctx.lineTo(-18 + i * 6, cy + (i % 2 ? -4 : 3));
    ctx.strokeStyle = '#C9485F'; ctx.lineWidth = 4; ctx.stroke();
    return;
  }
  if (open < 0.06 && !e.teeth) {
    ctx.beginPath(); ctx.moveTo(-hw, cyC); ctx.quadraticCurveTo(0, cy + smile * 14 + 1, hw, cyC);
    ctx.strokeStyle = '#D04F6B'; ctx.lineWidth = 4.2; ctx.stroke();
    if (smile > 0.2) { // little lower lip
      ctx.beginPath(); ctx.moveTo(-8, cy + smile * 12 + 6); ctx.quadraticCurveTo(0, cy + smile * 12 + 10, 8, cy + smile * 12 + 6);
      ctx.strokeStyle = 'rgba(232,130,150,0.8)'; ctx.lineWidth = 3; ctx.stroke();
    }
    return;
  }
  const o = Math.max(open, e.teeth ? 0.55 : 0);
  const top = cy - smile * 3 - o * 3, bot = cy + smile * 9 + o * 30 + round * 6;
  ctx.beginPath(); ctx.moveTo(-hw, cyC);
  ctx.quadraticCurveTo(0, top, hw, cyC);
  ctx.quadraticCurveTo(hw * 0.8, bot, 0, bot);
  ctx.quadraticCurveTo(-hw * 0.8, bot, -hw, cyC);
  ctx.closePath();
  ctx.fillStyle = '#8E2436'; ctx.fill();
  ctx.save(); ctx.clip();
  ellipse(ctx, 0, bot + 2, hw * 0.75, 10 + o * 5); ctx.fillStyle = '#F07A8A'; ctx.fill();
  if (e.teeth) { ctx.fillStyle = '#fff'; ctx.fillRect(-hw, top - 6, hw * 2, 10 + o * 3); }
  ctx.restore();
  ctx.beginPath(); ctx.moveTo(-hw, cyC);
  ctx.quadraticCurveTo(0, top, hw, cyC);
  ctx.quadraticCurveTo(hw * 0.8, bot, 0, bot);
  ctx.quadraticCurveTo(-hw * 0.8, bot, -hw, cyC);
  ctx.closePath();
  ctx.strokeStyle = '#C9485F'; ctx.lineWidth = 3.2; ctx.stroke();
}

// Ace's head. Origin = face centre, unscaled face is ~185 x 205.
function aceHead(ctx, e = {}, t = 0) {
  const bounce = (e.hairBounce || 0) + Math.sin(t * 2.1) * 1.2;
  ctx.save();
  ctx.rotate(e.tilt || 0);
  aceHairBack(ctx, bounce);
  // ears + earrings
  for (const s of [-1, 1]) {
    ellipse(ctx, s * 89, 14, 12, 18); fillStroke(ctx, SKIN, SKIN_LINE, 2);
    ctx.beginPath(); ctx.arc(s * 91, 40, 7, 0, Math.PI * 2); ctx.strokeStyle = '#5B5B6E'; ctx.lineWidth = 2.5; ctx.stroke();
  }
  // face
  ctx.beginPath();
  ctx.moveTo(0, -100);
  ctx.bezierCurveTo(60, -100, 92, -62, 92, -8);
  ctx.bezierCurveTo(92, 52, 52, 102, 0, 104);
  ctx.bezierCurveTo(-52, 102, -92, 52, -92, -8);
  ctx.bezierCurveTo(-92, -62, -60, -100, 0, -100);
  ctx.closePath();
  ctx.fillStyle = SKIN; ctx.fill();
  if (e.flush) { ctx.save(); ctx.clip(); ctx.globalAlpha = 0.28 * e.flush; ctx.fillStyle = '#FF5A4E'; ctx.fillRect(-100, -110, 200, 220); ctx.restore(); }
  if (e.green) { ctx.save(); ctx.clip(); ctx.globalAlpha = 0.25 * e.green; ctx.fillStyle = '#7BD36B'; ctx.fillRect(-100, -110, 200, 220); ctx.restore(); }
  ctx.strokeStyle = SKIN_LINE; ctx.lineWidth = 2.5; ctx.stroke();
  // cheeks
  const bl = 0.32 + (e.blush || 0) * 0.35;
  for (const s of [-1, 1]) { ellipse(ctx, s * 57, 32, 17, 10); ctx.fillStyle = `rgba(255,118,140,${bl})`; ctx.fill(); }
  ctx.beginPath(); ctx.moveTo(-92, -40); ctx.bezierCurveTo(-90, -96, -50, -112, 0, -112);
  ctx.bezierCurveTo(50, -112, 90, -96, 92, -40); ctx.quadraticCurveTo(0, -84, -92, -40); ctx.closePath();
  ctx.fillStyle = HAIR; ctx.fill();
  aceHairFront(ctx, bounce);
  for (const s of [-1, 1]) aceEye(ctx, s, { ...e, squint: (e.squint || 0) + (e.wink && s > 0 ? 1 : 0) });
  if (e.brow) for (const s of [-1, 1]) aceBrow(ctx, s, e);
  // nose
  ctx.beginPath(); ctx.moveTo(-4, 18); ctx.quadraticCurveTo(6, 26, -2, 31);
  ctx.strokeStyle = '#D9957C'; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.stroke();
  aceMouth(ctx, e);
  ctx.restore();
}

// neck + shirt (drawn before the head). Origin = face centre.
function aceBody(ctx, shirt = '#39C3C6') {
  ctx.fillStyle = SKIN; ctx.fillRect(-24, 70, 48, 70);
  ctx.beginPath();
  ctx.moveTo(-60, 120); ctx.bezierCurveTo(-150, 130, -170, 190, -175, 320);
  ctx.lineTo(175, 320); ctx.bezierCurveTo(170, 190, 150, 130, 60, 120);
  ctx.quadraticCurveTo(0, 165, -60, 120); ctx.closePath();
  ctx.fillStyle = shirt; ctx.fill();
  ctx.strokeStyle = 'rgba(0,0,0,0.15)'; ctx.lineWidth = 3; ctx.stroke();
  // collar
  ctx.beginPath(); ctx.moveTo(-60, 120); ctx.quadraticCurveTo(0, 168, 60, 120);
  ctx.strokeStyle = 'rgba(255,255,255,0.55)'; ctx.lineWidth = 7; ctx.stroke();
}

// --------------------------------------------------------------- hands ----
const HAND_SKIN = '#FFE4D6', HAND_LINE = '#D9A58F';
// fingers: [x at palm top, length, angle]
const FINGERS = [[-33, 70, -0.16], [-11, 80, -0.05], [11, 75, 0.06], [32, 58, 0.19]];

function nail(ctx, len, state, colour, fillAmt, sore, t) {
  // drawn in finger-local space: fingertip at (0,0), finger runs down +y
  const w = 13;
  if (sore > 0) {
    ellipse(ctx, 0, 6, 14, 12); ctx.fillStyle = `rgba(255,80,80,${0.35 * sore})`; ctx.fill();
  }
  const top = 3, bottom = 3 + len;
  ctx.beginPath();
  if (state === 'bitten') {
    ctx.moveTo(-w / 2, bottom); ctx.lineTo(-w / 2, top + 3);
    ctx.lineTo(-3, top + 1); ctx.lineTo(-1, top + 4); ctx.lineTo(2, top + 1); ctx.lineTo(4, top + 3); ctx.lineTo(w / 2, top + 2);
    ctx.lineTo(w / 2, bottom);
    ctx.quadraticCurveTo(0, bottom + 4, -w / 2, bottom);
  } else {
    ctx.roundRect(-w / 2, top, w, len, [6, 6, 4, 4]);
  }
  ctx.closePath();
  ctx.fillStyle = '#FFD3D8'; ctx.fill();
  if (colour && fillAmt > 0) {
    ctx.save(); ctx.clip();
    ctx.fillStyle = colour;
    ctx.fillRect(-w, bottom - (len + 6) * fillAmt, w * 2, (len + 6) * fillAmt + 2);
    ctx.fillStyle = 'rgba(255,255,255,0.55)';
    ctx.fillRect(-3.5, top + 3, 2.6, len * 0.6);
    ctx.restore();
  }
  ctx.strokeStyle = '#D79AA0'; ctx.lineWidth = 1.6; ctx.stroke();
}

// Back of an open hand, fingers up. Origin = wrist. flip=-1 mirrors (left hand).
// o: {flip, spread, nails: {state, len, colours[5], fill[5], sore}, glove, hot, t}
function hand(ctx, o = {}) {
  const flip = o.flip || 1, t = o.t || 0;
  ctx.save(); ctx.scale(flip, 1);
  const glove = o.glove;
  const skin = glove ? '#F59BBF' : (o.hot ? L.lerpColor('#FFE4D6', '#FF8A78', o.hot) : HAND_SKIN);
  const line = glove ? '#D7709A' : HAND_LINE;
  const gw = glove ? 5 : 0;
  const nails = o.nails || {};
  const spread = o.spread === undefined ? 1 : o.spread;
  if (o.arm) { // forearm / sleeve going down from the wrist
    ctx.beginPath(); ctx.roundRect(-34, -10, 68, o.arm, 20); fillStroke(ctx, skin, line, 2.5);
    if (o.sleeve) { ctx.beginPath(); ctx.roundRect(-44, o.armSleeveY || 60, 88, o.arm, 22); fillStroke(ctx, o.sleeve, 'rgba(0,0,0,0.15)', 3); }
  }
  // thumb (on the left for a right hand seen from the back)
  ctx.save(); ctx.translate(-36, -26); ctx.rotate(-0.62 - spread * 0.12);
  ctx.beginPath(); ctx.roundRect(-11 - gw, -58 - gw, 22 + gw * 2, 70 + gw, 11 + gw);
  fillStroke(ctx, skin, line, 2.5);
  if (!glove) { ctx.save(); ctx.translate(0, -58); nail(ctx, nails.len || 15, nails.state, nails.colours && nails.colours[0], nails.fill ? nails.fill[0] : 0, nails.sore || 0, t); ctx.restore(); }
  ctx.restore();
  // fingers
  FINGERS.forEach(([x, len, a], i) => {
    ctx.save(); ctx.translate(x, -72); ctx.rotate(a * spread + (o.wiggle ? Math.sin(t * 9 + i * 1.3) * 0.06 * o.wiggle : 0));
    ctx.beginPath(); ctx.roundRect(-11 - gw, -len - gw, 22 + gw * 2, len + 22, 11 + gw);
    fillStroke(ctx, skin, line, 2.5);
    // knuckle crease
    ctx.beginPath(); ctx.moveTo(-6, -len * 0.45); ctx.quadraticCurveTo(0, -len * 0.45 + 3, 6, -len * 0.45);
    ctx.strokeStyle = glove ? 'rgba(180,70,120,0.5)' : 'rgba(200,140,120,0.6)'; ctx.lineWidth = 1.8; ctx.stroke();
    if (!glove) { ctx.save(); ctx.translate(0, -len); nail(ctx, nails.len || 15, nails.state, nails.colours && nails.colours[i + 1], nails.fill ? nails.fill[i + 1] : 0, nails.sore || 0, t); ctx.restore(); }
    ctx.restore();
  });
  // palm
  ctx.beginPath();
  ctx.moveTo(-46 - gw, -78); ctx.quadraticCurveTo(-52 - gw, -20, -36, 6);
  ctx.lineTo(36, 6); ctx.quadraticCurveTo(52 + gw, -30, 46 + gw, -80);
  ctx.quadraticCurveTo(0, -92, -46 - gw, -78); ctx.closePath();
  fillStroke(ctx, skin, line, 2.5);
  // cover the seams of finger bases
  ctx.fillStyle = skin; ctx.fillRect(-40, -84, 80, 20);
  if (glove) { // cuff + stitches
    ctx.beginPath(); ctx.roundRect(-44, -6, 88, 26, 8); fillStroke(ctx, '#E9749F', line, 2.5);
    ctx.setLineDash([5, 5]); ctx.beginPath(); ctx.moveTo(-30, -50); ctx.quadraticCurveTo(0, -40, 30, -50);
    ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 2; ctx.stroke(); ctx.setLineDash([]);
  }
  ctx.restore();
  if (o.hot > 0.05) handSteam(ctx, t, o.hot);
}

// nail centres (hand-local, before scaling) for thumb, index, middle, ring, pinky
function handTips(o = {}) {
  const flip = o.flip || 1, spread = o.spread === undefined ? 1 : o.spread, off = 11;
  const out = [];
  const th = -0.62 - spread * 0.12;
  out.push({ x: flip * (-36 + Math.sin(th) * (58 - off)), y: -26 - Math.cos(th) * (58 - off) });
  for (const [x, len, a0] of FINGERS) {
    const a = a0 * spread;
    out.push({ x: flip * (x + Math.sin(a) * (len - off)), y: -72 - Math.cos(a) * (len - off) });
  }
  return out;
}

function handSteam(ctx, t, amt) {
  ctx.save(); ctx.lineCap = 'round';
  for (let i = 0; i < 4; i++) {
    const x0 = -36 + i * 24, ph = (t * 0.9 + i * 0.27) % 1;
    const y0 = -150 - ph * 70;
    ctx.globalAlpha = amt * Math.sin(ph * Math.PI) * 0.8;
    ctx.beginPath();
    for (let k = 0; k <= 10; k++) {
      const yy = y0 - k * 5, xx = x0 + Math.sin(k * 0.8 + t * 5 + i) * 6;
      k ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy);
    }
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 6; ctx.stroke();
  }
  // sweat drops
  ctx.globalAlpha = amt;
  for (const [x, y, s] of [[-58, -120, 1], [60, -100, 0.8]]) {
    const yy = y + ((t * 40 * s) % 30);
    ctx.beginPath(); ctx.moveTo(x, yy - 12); ctx.quadraticCurveTo(x + 8, yy, x, yy + 5); ctx.quadraticCurveTo(x - 8, yy, x, yy - 12);
    ctx.fillStyle = '#8FD8FF'; ctx.fill();
  }
  ctx.restore();
}

// pointing hand seen from the side, finger pointing +x. Origin = wrist.
function pointHand(ctx, o = {}) {
  const nails = o.nails || {};
  ctx.save();
  // sleeve
  ctx.beginPath(); ctx.roundRect(-140, -40, 140, 80, 20); fillStroke(ctx, o.sleeve || '#39C3C6', 'rgba(0,0,0,0.15)', 3);
  // index finger
  const bend = o.bend || 0;
  ctx.save(); ctx.translate(48, -16); ctx.rotate(-bend);
  ctx.beginPath(); ctx.roundRect(-10, -12, 92, 24, 12); fillStroke(ctx, HAND_SKIN, HAND_LINE, 2.5);
  // nail on top side of fingertip
  ctx.save(); ctx.translate(80, -9); ctx.rotate(Math.PI / 2);
  const len = (nails.len || 14) * 0.9;
  if (nails.sore) { ellipse(ctx, 0, 4, 14, 14); ctx.fillStyle = `rgba(255,80,80,${0.4 * nails.sore})`; ctx.fill(); }
  ctx.beginPath(); ctx.roundRect(-len + 2, -2, len, 7, 3);
  ctx.fillStyle = nails.colour || '#FFD3D8'; ctx.fill(); ctx.strokeStyle = '#D79AA0'; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.restore();
  ctx.restore();
  // fist
  ctx.beginPath(); ctx.roundRect(-8, -34, 74, 70, 26); fillStroke(ctx, HAND_SKIN, HAND_LINE, 2.5);
  for (let i = 0; i < 3; i++) {
    ctx.beginPath(); ctx.arc(52, -2 + i * 15, 9, -Math.PI / 2, Math.PI / 2); ctx.strokeStyle = HAND_LINE; ctx.lineWidth = 2.2; ctx.stroke();
  }
  // thumb
  ctx.beginPath(); ctx.roundRect(10, -40, 52, 18, 9); fillStroke(ctx, HAND_SKIN, HAND_LINE, 2.5);
  ctx.restore();
}

// ----------------------------------------------------------- Blueberry ----
const BB_FUR = '#EEEBF1', BB_GREY = '#BDB7C6', BB_DARK = '#5E5866', BB_BELLY = '#FFEFD0', BB_PINK = '#F6B3C6';

function bbBodyPath(ctx, squash) {
  ctx.beginPath();
  const n = 30;
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * Math.PI * 2;
    const fl = 1 + (i % 2 ? 0.035 : 0); // fluffy scallops
    const rx = 54 * fl * (1 + squash * 0.08), ry = 60 * fl * (1 - squash * 0.08);
    const px = Math.cos(a) * rx, py = Math.sin(a) * ry + 4 + (Math.sin(a) > 0 ? Math.sin(a) * 6 : 0);
    i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
  }
  ctx.closePath();
}

// Blueberry the hamster. Origin = body centre; ~110 wide, ~130 tall.
// e: {look, blink, happy, wide, worry, think, open, pose, run, wave, t, squash, brush, bottle}
function hamster(ctx, e = {}) {
  const t = e.t || 0;
  const squash = e.squash || 0;
  ctx.save();
  // feet
  const run = e.run || 0;
  for (const s of [-1, 1]) {
    const lift = run ? Math.max(0, Math.sin(t * 22 + (s > 0 ? Math.PI : 0))) * 9 * run : 0;
    ellipse(ctx, s * 20, 62 - lift, 13, 7); fillStroke(ctx, '#F4C2CF', '#C98A9C', 2);
  }
  // tail
  ellipse(ctx, 44, 44, 7, 5); fillStroke(ctx, BB_PINK, null);
  // ears
  for (const s of [-1, 1]) {
    const wig = Math.sin(t * 3 + s) * 0.05;
    ctx.save(); ctx.translate(s * 31, -50); ctx.rotate(s * 0.3 + wig);
    ellipse(ctx, 0, 0, 13, 12); fillStroke(ctx, '#D9D3DE', BB_DARK, 2.2);
    ellipse(ctx, 0, 1, 7, 6.5); ctx.fillStyle = BB_PINK; ctx.fill();
    ctx.restore();
  }
  // body
  bbBodyPath(ctx, squash);
  ctx.fillStyle = BB_FUR; ctx.fill();
  ctx.save(); ctx.clip();
  for (const s of [-1, 1]) { ellipse(ctx, s * 52, -2, 26, 62); ctx.fillStyle = BB_GREY; ctx.fill(); }
  ellipse(ctx, 0, -48, 40, 18); ctx.fillStyle = 'rgba(189,183,198,0.7)'; ctx.fill();
  ellipse(ctx, 0, 30, 36, 34); ctx.fillStyle = BB_BELLY; ctx.fill();
  // fur stripes on the sides (like the pencil marks in the drawings)
  ctx.strokeStyle = BB_DARK; ctx.lineWidth = 2.2; ctx.lineCap = 'round';
  for (const s of [-1, 1]) for (let k = 0; k < 6; k++) {
    const y = -36 + k * 15, x = s * (50 - Math.abs(k - 2.5) * 2);
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - s * 9, y + 3); ctx.stroke();
  }
  ctx.restore();
  bbBodyPath(ctx, squash); ctx.strokeStyle = BB_DARK; ctx.lineWidth = 2.6; ctx.stroke();

  // cheeks
  for (const s of [-1, 1]) { ellipse(ctx, s * 29, -12, 9, 6); ctx.fillStyle = 'rgba(255,140,170,0.55)'; ctx.fill(); }
  // eyes
  const lx = e.look ? e.look[0] * 2.5 : 0, ly = e.look ? e.look[1] * 2.5 : 0;
  const lid = clamp(e.blink || 0);
  for (const s of [-1, 1]) {
    const cx = s * 17, cy = -27;
    ctx.lineCap = 'round';
    if (e.happy > 0.5) {
      ctx.beginPath(); ctx.moveTo(cx - 8, cy + 3); ctx.quadraticCurveTo(cx, cy - 9, cx + 8, cy + 3);
      ctx.strokeStyle = '#1D1A22'; ctx.lineWidth = 4; ctx.stroke(); continue;
    }
    if (e.squeeze > 0.5) {
      ctx.beginPath(); ctx.moveTo(cx - s * 7, cy - 6); ctx.lineTo(cx + s * 5, cy); ctx.lineTo(cx - s * 7, cy + 6);
      ctx.strokeStyle = '#1D1A22'; ctx.lineWidth = 4; ctx.stroke(); continue;
    }
    if (lid > 0.8 || e.sleep) {
      ctx.beginPath(); ctx.moveTo(cx - 7, cy); ctx.quadraticCurveTo(cx, cy + 6, cx + 7, cy);
      ctx.strokeStyle = '#1D1A22'; ctx.lineWidth = 3.5; ctx.stroke(); continue;
    }
    const r = 9.2 * (1 + (e.wide || 0) * 0.3);
    ellipse(ctx, cx + lx, cy + ly, r, r * 1.08); ctx.fillStyle = '#1D1A22'; ctx.fill();
    ellipse(ctx, cx + lx - 2.8, cy + ly - 3.2, 3.3, 3.3); ctx.fillStyle = '#fff'; ctx.fill();
    ellipse(ctx, cx + lx + 2.5, cy + ly + 2.5, 1.3, 1.3); ctx.fill();
    if (e.sparkle) sparkle(ctx, cx + lx - 2, cy + ly - 2, 6 * e.sparkle, '#fff');
    if (lid > 0.02) {
      ctx.save(); ellipse(ctx, cx + lx, cy + ly, r + 1, r * 1.1 + 1); ctx.clip();
      ctx.fillStyle = BB_FUR; ctx.fillRect(cx - 12, cy - 12, 24, lid * 21);
      ctx.restore();
    }
  }
  // brows
  if (e.worry || e.think || e.raise) {
    for (const s of [-1, 1]) {
      const cx = s * 17, y = -42 - (e.raise || 0) * 4;
      const inner = (e.worry || 0) * -5 + (e.think && s > 0 ? -4 : 0);
      ctx.beginPath(); ctx.moveTo(cx - s * 7, y + inner); ctx.lineTo(cx + s * 6, y + 1);
      ctx.strokeStyle = BB_DARK; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.stroke();
    }
  }
  // nose
  const nw = Math.sin(t * 13) * (Math.sin(t * 0.9) > 0.4 ? 1.2 : 0.2);
  ctx.beginPath(); ctx.moveTo(-4.5, -16 + nw); ctx.quadraticCurveTo(0, -19 + nw, 4.5, -16 + nw); ctx.quadraticCurveTo(0, -9 + nw, -4.5, -16 + nw);
  ctx.fillStyle = '#F07C9C'; ctx.fill();
  // mouth
  const open = clamp(e.open || 0, 0, 1.1);
  if (open > 0.06) {
    ellipse(ctx, 0, -4, 4.5 + open * 2, 2 + open * 6); ctx.fillStyle = '#7A2034'; ctx.fill();
    ellipse(ctx, 0, -1 + open * 3, 3 + open, 1.5 + open * 2); ctx.fillStyle = '#F08AA0'; ctx.fill();
  } else {
    ctx.beginPath(); ctx.moveTo(-7, -9); ctx.quadraticCurveTo(-3.5, -5, 0, -10); ctx.quadraticCurveTo(3.5, -5, 7, -9);
    ctx.strokeStyle = BB_DARK; ctx.lineWidth = 2; ctx.stroke();
  }
  if (e.tongue) {
    ctx.beginPath(); ctx.ellipse(1, -2, 4, 6, 0, 0, Math.PI); ctx.fillStyle = '#F08AA0'; ctx.fill();
  }
  // whiskers
  ctx.strokeStyle = 'rgba(80,72,90,0.75)'; ctx.lineWidth = 1.4;
  for (const s of [-1, 1]) for (let k = -1; k <= 1; k++) {
    const tw = Math.sin(t * 6 + k + s) * 0.04;
    const a = (s > 0 ? 0 : Math.PI) + s * (k * 0.22 + tw);
    ctx.beginPath(); ctx.moveTo(s * 9, -13 + k * 2); ctx.lineTo(s * 9 + Math.cos(a) * 34, -13 + k * 2 + Math.sin(a) * 34 * 0.6);
    ctx.stroke();
  }
  // paws
  const pose = e.pose || 'rest';
  const paws = {
    rest: [[-20, 10], [20, 10]],
    wave: [[-20, 10], [40, -22 + Math.sin(t * 12) * 5]],
    up: [[-44, -30 + Math.sin(t * 10) * 4], [44, -30 - Math.sin(t * 10) * 4]],
    chin: [[-20, 10], [10, -2]],
    hold: [[-16, 2], [16, 2]],
    point: [[-20, 10], [46, -6]],
  }[pose] || [[-20, 10], [20, 10]];
  for (const [x, y] of paws) { ellipse(ctx, x, y, 8.5, 9.5); fillStroke(ctx, '#F7D3D6', '#C98A9C', 2); }
  ctx.restore();
}

// purple hamster ball. layer 'back' (glassy fill) or 'front' (bands + outline). Origin = centre.
function ballBack(ctx, R) {
  const g = ctx.createRadialGradient(-R * 0.3, -R * 0.35, R * 0.1, 0, 0, R);
  g.addColorStop(0, 'rgba(238,224,255,0.55)'); g.addColorStop(1, 'rgba(196,160,236,0.55)');
  ctx.beginPath(); ctx.arc(0, 0, R, 0, Math.PI * 2); ctx.fillStyle = g; ctx.fill();
}
function ballFront(ctx, R, ang) {
  ctx.save(); ctx.rotate(ang);
  ctx.lineCap = 'round';
  ctx.strokeStyle = 'rgba(150,96,208,0.75)'; ctx.lineWidth = Math.max(2, R * 0.035);
  for (const s of [-1, 1]) {
    ctx.beginPath(); ctx.moveTo(s * R * 0.3, -R * 0.94); ctx.quadraticCurveTo(s * R * 0.06, 0, s * R * 0.3, R * 0.94); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(s * R * 0.72, -R * 0.68); ctx.quadraticCurveTo(s * R * 0.42, 0, s * R * 0.72, R * 0.68); ctx.stroke();
  }
  for (const s of [-1, 1]) {
    ellipse(ctx, 0, s * R * 0.93, R * 0.24, R * 0.07); ctx.fillStyle = 'rgba(214,120,200,0.85)'; ctx.fill();
  }
  ctx.restore();
  ctx.beginPath(); ctx.arc(0, 0, R, 0, Math.PI * 2);
  ctx.strokeStyle = '#9B6BD3'; ctx.lineWidth = Math.max(3, R * 0.05); ctx.stroke();
  // shine
  ctx.beginPath(); ctx.arc(0, 0, R * 0.84, Math.PI * 1.08, Math.PI * 1.38);
  ctx.strokeStyle = 'rgba(255,255,255,0.75)'; ctx.lineWidth = R * 0.06; ctx.stroke();
  ellipse(ctx, -R * 0.62, -R * 0.62, R * 0.04, R * 0.04); ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.fill();
}
// hamster inside ball; o: {R, ang, e}
function hamsterInBall(ctx, o) {
  const R = o.R;
  ballBack(ctx, R);
  ctx.save();
  const s = R / 112;
  ctx.translate(0, R * 0.32); ctx.scale(s, s); ctx.translate(0, -0);
  hamster(ctx, o.e || {});
  ctx.restore();
  ballFront(ctx, R, o.ang || 0);
}

// -------------------------------------------------------- baby brother ----
const BABY_SKIN = '#FFE0CC', BABY_LINE = '#D69B83';
function babyHead(ctx, e = {}) {
  const t = e.t || 0;
  ctx.save(); ctx.rotate(e.tilt || 0);
  // ears
  for (const s of [-1, 1]) { ellipse(ctx, s * 70, 6, 14, 18); fillStroke(ctx, BABY_SKIN, BABY_LINE, 2.5); }
  // face
  ellipse(ctx, 0, 0, 72, 68); ctx.fillStyle = e.green ? L.lerpColor('#FFE0CC', '#C6EBA8', e.green) : BABY_SKIN; ctx.fill();
  ctx.strokeStyle = BABY_LINE; ctx.lineWidth = 3; ctx.stroke();
  // hair spikes
  ctx.beginPath(); ctx.moveTo(-66, -18);
  const spikes = [[-60, -66], [-40, -44], [-28, -92], [-10, -56], [6, -100], [18, -58], [36, -88], [44, -46], [64, -62], [68, -16]];
  for (const [x, y] of spikes) ctx.lineTo(x, y + Math.sin(t * 4 + x) * 2);
  ctx.quadraticCurveTo(0, -52, -66, -18); ctx.closePath();
  ctx.fillStyle = '#35B9CC'; ctx.fill(); ctx.strokeStyle = '#1E8BA0'; ctx.lineWidth = 3; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-20, -60); ctx.lineTo(-8, -82); ctx.moveTo(14, -62); ctx.lineTo(28, -80);
  ctx.strokeStyle = '#7FE0EA'; ctx.lineWidth = 3; ctx.stroke();
  // freckles
  ctx.fillStyle = '#C98E6E';
  for (const [x, y] of [[-44, 16], [-36, 22], [-50, 24], [44, 16], [36, 22], [50, 24]]) { ellipse(ctx, x, y, 2.2, 2.2); ctx.fill(); }
  // eyes
  const mood = e.mood || 'mischief';
  for (const s of [-1, 1]) {
    const cx = s * 25, cy = -8;
    if (mood === 'yuck') {
      ctx.beginPath(); ctx.moveTo(cx - s * 12, cy - 9); ctx.lineTo(cx + s * 9, cy); ctx.lineTo(cx - s * 12, cy + 9);
      ctx.strokeStyle = '#2B2340'; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
      continue;
    }
    ellipse(ctx, cx, cy, 13, 15); fillStroke(ctx, '#fff', '#2B2340', 3);
    const lk = e.look || [0, 0];
    ellipse(ctx, cx + lk[0] * 5, cy + 3 + lk[1] * 5, mood === 'huh' ? 5 : 7, mood === 'huh' ? 5 : 8); ctx.fillStyle = '#2B2340'; ctx.fill();
    ellipse(ctx, cx + lk[0] * 5 - 2, cy + lk[1] * 5, 2.2, 2.2); ctx.fillStyle = '#fff'; ctx.fill();
    const lid = mood === 'mischief' ? 0.4 : (e.blink || 0);
    if (lid > 0.02) {
      ctx.save(); ellipse(ctx, cx, cy, 14, 16); ctx.clip();
      ctx.fillStyle = BABY_SKIN; ctx.fillRect(cx - 16, cy - 18, 32, lid * 32);
      ctx.beginPath(); ctx.moveTo(cx - 14, cy - 15 + lid * 30); ctx.lineTo(cx + 14, cy - 15 + lid * 30 + s * (mood === 'mischief' ? 3 : 0));
      ctx.strokeStyle = '#2B2340'; ctx.lineWidth = 3; ctx.stroke();
      ctx.restore();
    }
    // brows
    ctx.beginPath();
    if (mood === 'huh') { ctx.moveTo(cx - 12, cy - 26 - (s > 0 ? 8 : 0)); ctx.lineTo(cx + 12, cy - 28 - (s > 0 ? 8 : 0)); }
    else if (mood === 'mischief') { ctx.moveTo(cx - s * 14, cy - 24); ctx.lineTo(cx + s * 12, cy - 30); }
    else { ctx.moveTo(cx - 12, cy - 26); ctx.lineTo(cx + 12, cy - 26); }
    ctx.strokeStyle = '#1E8BA0'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.stroke();
  }
  // nose
  ellipse(ctx, 0, 10, 6, 4); ctx.fillStyle = '#F2A98E'; ctx.fill();
  // mouth
  if (mood === 'yuck') {
    ctx.beginPath(); ctx.moveTo(-30, 34);
    for (let i = 1; i <= 8; i++) ctx.lineTo(-30 + i * 7.5, 34 + (i % 2 ? -5 : 4));
    ctx.strokeStyle = '#8E2436'; ctx.lineWidth = 4; ctx.stroke();
    ctx.beginPath(); ctx.ellipse(8, 38, 12, 18 + Math.sin(t * 10) * 2, 0, 0, Math.PI);
    ctx.fillStyle = '#F07A8A'; ctx.fill(); ctx.strokeStyle = '#C9485F'; ctx.lineWidth = 2.5; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(8, 40); ctx.lineTo(8, 52); ctx.stroke();
  } else if (mood === 'huh') {
    ellipse(ctx, 6, 36, 8, 9); ctx.fillStyle = '#8E2436'; ctx.fill();
  } else {
    // big toothy grin; chomp opens/closes it
    const ch = e.chomp || 0;
    const top = 22, bot = 50 + ch * 12;
    ctx.beginPath(); ctx.moveTo(-46, top - 6);
    ctx.quadraticCurveTo(0, top + 10 - ch * 4, 46, top - 6);
    ctx.quadraticCurveTo(30, bot + 8, 0, bot + 6);
    ctx.quadraticCurveTo(-30, bot + 8, -46, top - 6); ctx.closePath();
    ctx.fillStyle = '#7A1F2B'; ctx.fill();
    ctx.save(); ctx.clip();
    ctx.fillStyle = '#fff';
    for (let i = -4; i <= 4; i++) { ctx.beginPath(); ctx.roundRect(i * 10 - 4.5, top - 8 + Math.abs(i) * 0.6, 9, 13, 3); ctx.fill(); ctx.strokeStyle = '#ccc'; ctx.lineWidth = 1; ctx.stroke(); }
    for (let i = -3; i <= 3; i++) { ctx.beginPath(); ctx.roundRect(i * 10 - 4.5, bot - 6, 9, 12, 3); ctx.fill(); ctx.stroke(); }
    ctx.restore();
    ctx.beginPath(); ctx.moveTo(-46, top - 6);
    ctx.quadraticCurveTo(0, top + 10 - ch * 4, 46, top - 6);
    ctx.quadraticCurveTo(30, bot + 8, 0, bot + 6);
    ctx.quadraticCurveTo(-30, bot + 8, -46, top - 6); ctx.closePath();
    ctx.strokeStyle = '#2B2340'; ctx.lineWidth = 3; ctx.stroke();
  }
  ctx.restore();
}

module.exports = { aceHead, aceBody, hand, handTips, pointHand, hamster, hamsterInBall, ballBack, ballFront, babyHead, SKIN };
