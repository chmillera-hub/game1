// Character drawing. Every character is drawn at its feet (x, y) with scale s.
// Expression fields shared by everyone (all optional, 0 by default):
//   mouth (0..1 open), smile (-1..1), blink, lid (resting droop), wide (surprise),
//   gx/gy (gaze -1..1), browIn (sad inner-up), browAngry, browUp, squint, tear
const TAU = Math.PI * 2;
const OUT = '#3d2b1f';

function ell(c, x, y, rx, ry, rot = 0) { c.beginPath(); c.ellipse(x, y, Math.max(.1, rx), Math.max(.1, ry), rot, 0, TAU); }
function fs(c, fill, lw = 4, stroke = OUT) {
  if (fill) { c.fillStyle = fill; c.fill(); }
  if (lw) { c.lineWidth = lw; c.strokeStyle = stroke; c.lineJoin = 'round'; c.lineCap = 'round'; c.stroke(); }
}
function radial(c, x, y, r, inner, outer) {
  const g = c.createRadialGradient(x - r * .35, y - r * .45, r * .1, x, y, r * 1.15);
  g.addColorStop(0, inner); g.addColorStop(1, outer); return g;
}
function capsule(c, x, y, ang, len, w, fill, lw = 4) {
  c.save(); c.translate(x, y); c.rotate(ang);
  c.beginPath(); c.moveTo(-w / 2, 0); c.lineTo(-w / 2, len); c.arc(0, len, w / 2, Math.PI, 0, true);
  c.lineTo(w / 2, 0); c.arc(0, 0, w / 2, 0, Math.PI, true); c.closePath();
  fs(c, fill, lw); c.restore();
}

function drawEye(c, x, y, rx, ry, e, inner, lidColor, opt = {}) {
  const wide = e.wide || 0;
  rx *= 1 + wide * .14; ry *= 1 + wide * .22;
  c.save();
  ell(c, x, y, rx, ry); c.fillStyle = '#fffdf4'; c.fill(); c.clip();
  const px = x + (e.gx || 0) * rx * .5, py = y + (e.gy || 0) * ry * .42;
  const pr = (opt.pr || rx * .62) * (1 - wide * .12);
  c.fillStyle = opt.iris || '#2a1c12'; c.beginPath(); c.arc(px, py, pr, 0, TAU); c.fill();
  c.fillStyle = 'rgba(255,255,255,.95)'; c.beginPath(); c.arc(px - pr * .32, py - pr * .38, pr * .32, 0, TAU); c.fill();
  if (e.sparkle) {
    c.globalAlpha = e.sparkle; c.beginPath(); c.arc(px + pr * .35, py + pr * .3, pr * .18, 0, TAU); c.fill(); c.globalAlpha = 1;
  }
  if (e.tearShine) { // glassy, welling eyes
    c.fillStyle = `rgba(160,200,255,${.35 * e.tearShine})`; c.fillRect(x - rx, y + ry * .25, rx * 2, ry);
  }
  // upper lid
  const cov = clamp(Math.max(e.blink || 0, (e.lid || 0) * (1 - wide)));
  if (cov > 0.01) {
    const tilt = ((e.browAngry || 0) - (e.browIn || 0)) * .45 * ry * Math.min(1, cov * 2.2);
    const yEdge = y - ry + 2 * ry * cov;
    const yIn = yEdge + tilt, yOut = yEdge - tilt;
    const xi = x + inner * (rx + 2), xo = x - inner * (rx + 2);
    c.fillStyle = lidColor;
    c.beginPath(); c.moveTo(xo, y - ry - 3); c.lineTo(xi, y - ry - 3); c.lineTo(xi, yIn);
    c.quadraticCurveTo(x, (yIn + yOut) / 2 + ry * .3 * cov, xo, yOut); c.closePath(); c.fill();
    c.beginPath(); c.moveTo(xi, yIn); c.quadraticCurveTo(x, (yIn + yOut) / 2 + ry * .3 * cov, xo, yOut);
    c.lineWidth = 3; c.strokeStyle = OUT; c.stroke();
  }
  // lower lid: happy squint / suspicious squint
  const low = clamp((e.smile || 0) - .35) * .5 + (e.squint || 0) * .45;
  if (low > .01 && (e.blink || 0) < .9) {
    const yb = y + ry - 2 * ry * low;
    c.fillStyle = lidColor;
    c.beginPath(); c.moveTo(x - rx - 2, y + ry + 3); c.lineTo(x - rx - 2, yb + ry * .2);
    c.quadraticCurveTo(x, yb - ry * .35 * low, x + rx + 2, yb + ry * .2); c.lineTo(x + rx + 2, y + ry + 3); c.fill();
  }
  c.restore();
  ell(c, x, y, rx, ry); c.lineWidth = opt.olw || 3; c.strokeStyle = OUT; c.stroke();
  if (e.tear) { // a tear running down
    const ty = y + ry + 6 + e.tear * ry * 2.5;
    c.fillStyle = 'rgba(150,200,255,.9)';
    c.beginPath(); c.moveTo(x - inner * rx * .3, ty - 10); c.quadraticCurveTo(x - inner * rx * .3 + 6, ty + 2, x - inner * rx * .3, ty + 6);
    c.quadraticCurveTo(x - inner * rx * .3 - 6, ty + 2, x - inner * rx * .3, ty - 10); c.fill();
  }
  if (opt.brow === false) return;
  const bw = opt.bw || 4;
  const by = y - ry * (1.32 + .3 * (e.browUp || 0) + .3 * wide) - 3;
  const lift = ((e.browIn || 0) - (e.browAngry || 0)) * ry * .6;
  const ix = x + inner * rx * .95, ox = x - inner * rx * .95;
  c.beginPath(); c.moveTo(ox, by + lift * .25);
  c.quadraticCurveTo(x, by - ry * .28, ix, by - lift);
  c.lineWidth = bw; c.strokeStyle = opt.browColor || OUT; c.lineCap = 'round'; c.stroke();
}

function drawMouth(c, x, y, w, smile, open, opt = {}) {
  const k = smile || 0;
  if (open > .06) {
    const h = open * w * (opt.openScale || .55);
    const ey = y - k * w * .14;
    const m = new Path2D(); m.moveTo(x - w / 2, ey);
    m.quadraticCurveTo(x, y + k * w * .18, x + w / 2, ey);
    m.quadraticCurveTo(x, Math.max(y + k * w * .18 + 4, y + h * 2 + k * w * .1), x - w / 2, ey);
    m.closePath();
    c.save(); c.fillStyle = '#5a2320'; c.fill(m); c.clip(m);
    c.fillStyle = '#d9707a'; ell(c, x, Math.max(y + k * w * .18 + 4, y + h * 2 + k * w * .1) * .5 + y * .5 + h * .35, w * .3, h * .55 + 3); c.fill();
    if (opt.teeth) { c.fillStyle = '#fff'; c.fillRect(x - 7, ey - 2, 6.5, 9 + h * .2); c.fillRect(x + .5, ey - 2, 6.5, 9 + h * .2); }
    c.restore();
    c.lineWidth = 3; c.strokeStyle = OUT; c.stroke(m);
  } else {
    c.beginPath(); c.moveTo(x - w / 2, y - k * w * .2);
    c.quadraticCurveTo(x, y + k * w * .32, x + w / 2, y - k * w * .2);
    c.lineWidth = opt.lw || 3.5; c.strokeStyle = OUT; c.lineCap = 'round'; c.stroke();
    if (opt.teeth && k > .2) { c.fillStyle = '#fff'; c.fillRect(x - 6, y + k * w * .05, 12, 7); c.strokeRect(x - 6, y + k * w * .05, 12, 7); }
  }
}

function blush(c, x, y, r, a = .28) {
  c.fillStyle = `rgba(235,110,110,${a})`; ell(c, x, y, r, r * .6); c.fill();
}

// ---------------------------------------------------------------- honey pot
function drawHoneyPot(c, x, y, s = 1, label = true) {
  c.save(); c.translate(x, y); c.scale(s, s);
  c.beginPath(); c.moveTo(-34, -70); c.quadraticCurveTo(-62, -40, -40, 0); c.lineTo(40, 0);
  c.quadraticCurveTo(62, -40, 34, -70); c.closePath();
  fs(c, radial(c, -5, -40, 60, '#e2a35a', '#a8682e'));
  ell(c, 0, -72, 38, 9); fs(c, '#7d4a1f', 3.5);
  c.fillStyle = '#f2b632'; ell(c, 0, -72, 30, 6); c.fill();
  c.beginPath(); c.moveTo(20, -70); c.quadraticCurveTo(26, -55, 22, -48); c.quadraticCurveTo(18, -55, 14, -69); c.fillStyle = '#f2b632'; c.fill();
  if (label) {
    c.save(); c.rotate(-.05); c.fillStyle = '#f6ecd2'; c.fillRect(-30, -48, 60, 24); c.strokeStyle = OUT; c.lineWidth = 2; c.strokeRect(-30, -48, 60, 24);
    c.fillStyle = '#3d2b1f'; c.font = '600 17px Fredoka'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('HUNNY', 0, -35); c.restore();
  }
  c.restore();
}

function drawUmbrella(c, x, y, s, ang = 0) {
  c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s);
  c.beginPath(); c.moveTo(0, 0); c.lineTo(0, 210); c.lineWidth = 6; c.strokeStyle = OUT; c.stroke();
  c.beginPath(); c.arc(-10, 210, 10, 0, Math.PI); c.stroke();
  c.beginPath(); c.moveTo(-150, 30);
  c.quadraticCurveTo(-140, -70, 0, -80); c.quadraticCurveTo(140, -70, 150, 30);
  for (let i = 0; i < 4; i++) { const x0 = 150 - i * 75; c.quadraticCurveTo(x0 - 37, 5, x0 - 75, 30); }
  c.closePath(); fs(c, '#4f7fa6');
  c.restore();
}

// ---------------------------------------------------------------- Pooh
const POOH = { fur: '#e2a640', furD: '#c4862a', light: '#f5d48c', belly: '#efc272' };
function drawPooh(c, st) {
  const s = st.s || 1, f = st.facing || 1;
  c.save(); c.translate(st.x, st.y + (st.bob || 0)); c.rotate(st.tilt || 0); c.scale(s * f, s);
  // legs
  ell(c, -40, -24, 38, 26, -.15); fs(c, POOH.fur); ell(c, 40, -24, 38, 26, .15); fs(c, POOH.fur);
  const armR = st.armR ?? .25, armL = st.armL ?? .25;
  // far-side arm drawn under body when lowered
  ell(c, 0, -125, 94 * (st.puff || 1), 108); fs(c, radial(c, 0, -125, 110, POOH.fur, POOH.furD));
  c.fillStyle = POOH.belly; ell(c, 0, -108, 60, 70); c.fill();
  capsule(c, -80, -178, armL, 86, 36, POOH.fur);
  capsule(c, 80, -178, -armR, 86, 36, POOH.fur);
  if (st.honey) drawHoneyPot(c, 80 + Math.sin(armR) * 92 + 8, -178 + Math.cos(armR) * 92 + 40, .85);
  // head
  c.save(); c.translate(0, -262); c.rotate(st.headTilt || 0);
  const fx = (st.headTurn || 0) * 18;
  for (const sx of [-1, 1]) { ell(c, sx * 56 + fx * .3, -58, 27, 26); fs(c, POOH.fur); ell(c, sx * 56 + fx * .3, -56, 14, 13); c.fillStyle = POOH.furD; c.fill(); }
  ell(c, 0, 0, 82, 78); fs(c, radial(c, 0, 0, 82, '#ecb453', POOH.fur));
  ell(c, fx, 24, 46, 33); c.fillStyle = POOH.light; c.fill();
  blush(c, fx - 50, 22, 17, .22 + (st.blushA || 0)); blush(c, fx + 50, 22, 17, .22 + (st.blushA || 0));
  drawEye(c, fx - 30, -16, 12, 14, st, 1, POOH.fur, { bw: 4.5 });
  drawEye(c, fx + 30, -16, 12, 14, st, -1, POOH.fur, { bw: 4.5 });
  ell(c, fx, 6, 18, 12); fs(c, '#3a2618', 2.5); c.fillStyle = 'rgba(255,255,255,.5)'; ell(c, fx - 5, 2, 6, 3); c.fill();
  c.beginPath(); c.moveTo(fx, 17); c.lineTo(fx, 24); c.lineWidth = 3; c.strokeStyle = OUT; c.stroke();
  drawMouth(c, fx, 34, 36, st.smile ?? .4, st.mouth || 0);
  c.restore();
  c.restore();
}

// ---------------------------------------------------------------- Piglet
const PIG = { skin: '#f4c0bf', skinD: '#e0999a', jumper: '#7aa35f', jumperD: '#5d8547' };
function drawPiglet(c, st) {
  const s = st.s || 1, f = st.facing || 1;
  const tr = (st.tremble || 0) * Math.sin((st.t || 0) * 70) * 2.2;
  c.save(); c.translate(st.x + tr, st.y + (st.bob || 0)); c.rotate(st.tilt || 0); c.scale(s * f, s);
  capsule(c, -16, -46, 0, 36, 15, PIG.skin, 3.5); capsule(c, 16, -46, 0, 36, 15, PIG.skin, 3.5);
  ell(c, -16, -6, 10, 6); fs(c, '#6d4a3a', 3); ell(c, 16, -6, 10, 6); fs(c, '#6d4a3a', 3);
  ell(c, 0, -76, 44, 48); fs(c, radial(c, 0, -76, 48, PIG.jumper, PIG.jumperD));
  c.strokeStyle = 'rgba(40,70,30,.35)'; c.lineWidth = 3;
  for (const yy of [-92, -72, -52]) { c.beginPath(); c.moveTo(-38, yy); c.quadraticCurveTo(0, yy + 6, 38, yy); c.stroke(); }
  const armR = st.armR ?? .3, armL = st.armL ?? .3;
  capsule(c, -36, -100, armL, 44, 16, PIG.jumper, 3.5); capsule(c, 36, -100, -armR, 44, 16, PIG.jumper, 3.5);
  c.save(); c.translate(0, -150); c.rotate(st.headTilt || 0);
  const fx = (st.headTurn || 0) * 10;
  const ed = st.earsDown || 0;
  for (const sx of [-1, 1]) {
    c.save(); c.translate(sx * 24, -32); c.rotate(sx * (.35 + ed * .9));
    c.beginPath(); c.moveTo(-13, 6); c.lineTo(0, -34); c.lineTo(13, 6); c.closePath(); fs(c, PIG.skin, 3.5);
    c.beginPath(); c.moveTo(-6, 2); c.lineTo(0, -20); c.lineTo(6, 2); c.closePath(); c.fillStyle = PIG.skinD; c.fill();
    c.restore();
  }
  ell(c, 0, 0, 46, 44); fs(c, radial(c, 0, 0, 46, '#f9d2d0', PIG.skin));
  blush(c, fx - 30, 14, 10, .3); blush(c, fx + 30, 14, 10, .3);
  drawEye(c, fx - 19, -10, 8.5, 10, st, 1, PIG.skin, { bw: 3.2, olw: 2.5 });
  drawEye(c, fx + 19, -10, 8.5, 10, st, -1, PIG.skin, { bw: 3.2, olw: 2.5 });
  ell(c, fx, 9, 17, 12); fs(c, PIG.skinD, 3);
  c.fillStyle = '#9b5b5c'; ell(c, fx - 6, 9, 3, 4.5); c.fill(); ell(c, fx + 6, 9, 3, 4.5); c.fill();
  drawMouth(c, fx, 29, 18, st.smile ?? .3, st.mouth || 0);
  c.restore();
  c.restore();
}

// ---------------------------------------------------------------- Rabbit
const RAB = { fur: '#c9a47a', furD: '#a98256', light: '#f1e3c8', ear: '#e6b0a4' };
function drawRabbit(c, st) {
  const s = st.s || 1, f = st.facing || 1;
  c.save(); c.translate(st.x, st.y + (st.bob || 0)); c.rotate(st.tilt || 0); c.scale(s * f, s);
  ell(c, -34, -12, 42, 14); fs(c, RAB.fur); ell(c, 34, -12, 42, 14); fs(c, RAB.fur);
  const p = st.puff || 1;
  ell(c, 0, -112, 62 * p, 92); fs(c, radial(c, 0, -112, 92, RAB.fur, RAB.furD));
  c.fillStyle = RAB.light; ell(c, 0, -98, 40 * p, 62); c.fill();
  const armR = st.armR ?? .2, armL = st.armL ?? .2;
  capsule(c, -52 * p, -162, armL, 74, 22, RAB.fur); capsule(c, 52 * p, -162, -armR, 74, 22, RAB.fur);
  if (st.clipboard) {
    c.save(); c.translate(70, -150); c.rotate(-.15);
    c.fillStyle = '#b07a46'; c.fillRect(-30, -42, 60, 80); c.strokeStyle = OUT; c.lineWidth = 3; c.strokeRect(-30, -42, 60, 80);
    c.fillStyle = '#fbf6e8'; c.fillRect(-24, -34, 48, 66);
    c.strokeStyle = '#8a8a8a'; c.lineWidth = 2; for (let i = 0; i < 4; i++) { c.beginPath(); c.moveTo(-18, -22 + i * 15); c.lineTo(16, -22 + i * 15); c.stroke(); }
    c.restore();
  }
  c.save(); c.translate(0, -238); c.rotate(st.headTilt || 0);
  const fx = (st.headTurn || 0) * 12, flop = st.earFlop || 0;
  for (const sx of [-1, 1]) {
    c.save(); c.translate(sx * 20, -36); c.rotate(sx * (.14 + flop * .5) + (st.earTwitch || 0) * (sx > 0 ? 1 : 0));
    ell(c, 0, -60, 17, 64); fs(c, RAB.fur); ell(c, 0, -56, 8, 48); c.fillStyle = RAB.ear; c.fill();
    c.restore();
  }
  ell(c, 0, 0, 56, 50); fs(c, radial(c, 0, 0, 56, '#d8b88d', RAB.fur));
  drawEye(c, fx - 22, -12, 10, 12, st, 1, RAB.fur, { bw: 4 });
  drawEye(c, fx + 22, -12, 10, 12, st, -1, RAB.fur, { bw: 4 });
  c.fillStyle = RAB.light; ell(c, fx - 13, 18, 16, 13); c.fill(); ell(c, fx + 13, 18, 16, 13); c.fill();
  c.strokeStyle = 'rgba(61,43,31,.7)'; c.lineWidth = 1.8;
  for (const sx of [-1, 1]) for (const k of [-6, 0, 6]) { c.beginPath(); c.moveTo(fx + sx * 22, 18 + k * .4); c.lineTo(fx + sx * 66, 12 + k * 1.6); c.stroke(); }
  c.beginPath(); c.moveTo(fx - 7, 6); c.lineTo(fx + 7, 6); c.lineTo(fx, 14); c.closePath(); fs(c, '#d98b8b', 2.5);
  drawMouth(c, fx, 32, 18, st.smile ?? .2, st.mouth || 0, { teeth: true, openScale: .7 });
  c.restore();
  c.restore();
}

// ---------------------------------------------------------------- Owl
const OWL = { body: '#8b6643', bodyD: '#6a4a2e', chest: '#ccab7c', face: '#e5d1a8', beak: '#e09a3c' };
function drawOwl(c, st) {
  const s = st.s || 1, f = st.facing || 1;
  c.save(); c.translate(st.x, st.y + (st.bob || 0)); c.rotate(st.tilt || 0); c.scale(s * f, s);
  for (const sx of [-1, 1]) { c.beginPath(); c.moveTo(sx * 22 - 14, -4); c.lineTo(sx * 22, -18); c.lineTo(sx * 22 + 14, -4); c.closePath(); fs(c, OWL.beak, 3); }
  ell(c, 0, -142, 88, 138); fs(c, radial(c, 0, -142, 138, '#9c7650', OWL.bodyD));
  c.fillStyle = OWL.chest; ell(c, 0, -100, 58, 86); c.fill();
  c.strokeStyle = 'rgba(106,74,46,.55)'; c.lineWidth = 2.5;
  for (let r = 0; r < 4; r++) for (let k = -1; k <= 1; k++) {
    const xx = k * 26 + (r % 2) * 13, yy = -150 + r * 28; c.beginPath(); c.moveTo(xx - 8, yy); c.lineTo(xx, yy + 7); c.lineTo(xx + 8, yy); c.stroke();
  }
  const wR = st.wingR || 0, wL = st.wingL || 0;
  c.save(); c.translate(-74, -200); c.rotate(wL); ell(c, -8, 70, 30, 86, .12); fs(c, OWL.bodyD); c.restore();
  c.save(); c.translate(74, -200); c.rotate(-wR); ell(c, 8, 70, 30, 86, -.12); fs(c, OWL.bodyD); c.restore();
  const fx = (st.headTurn || 0) * 10;
  for (const sx of [-1, 1]) { c.beginPath(); c.moveTo(sx * 40, -255); c.lineTo(sx * 74, -300); c.lineTo(sx * 68, -246); c.closePath(); fs(c, OWL.body); }
  c.fillStyle = OWL.face; ell(c, fx - 33, -205, 42, 42); c.fill(); ell(c, fx + 33, -205, 42, 42); c.fill();
  drawEye(c, fx - 33, -205, 22, 22, st, 1, OWL.face, { bw: 6, browColor: OWL.bodyD, pr: 12 });
  drawEye(c, fx + 33, -205, 22, 22, st, -1, OWL.face, { bw: 6, browColor: OWL.bodyD, pr: 12 });
  const sl = st.specSlip || 0;
  c.strokeStyle = '#2f2219'; c.lineWidth = 4;
  ell(c, fx - 33, -203 + sl, 29, 28); c.stroke(); ell(c, fx + 33, -203 + sl, 29, 28); c.stroke();
  c.beginPath(); c.moveTo(fx - 5, -207 + sl); c.quadraticCurveTo(fx, -213 + sl, fx + 5, -207 + sl); c.stroke();
  const m = st.mouth || 0;
  c.beginPath(); c.moveTo(fx - 11, -182); c.lineTo(fx + 11, -182); c.lineTo(fx, -160); c.closePath(); fs(c, OWL.beak, 3);
  if (m > .05) { c.beginPath(); c.moveTo(fx - 8, -170 + m * 4); c.lineTo(fx + 8, -170 + m * 4); c.lineTo(fx, -156 + m * 12); c.closePath(); fs(c, '#c27f2a', 3); }
  if (st.magnify) {
    c.save(); c.globalAlpha = st.magnify;
    const lx = fx + 33 + 4, ly = -205;
    capsule(c, lx + 30, ly + 30, -.75, 70, 14, '#6b4a2b', 3);
    c.save(); ell(c, lx, ly, 48, 48); c.fillStyle = 'rgba(220,240,255,.35)'; c.fill(); c.clip();
    c.translate(lx, ly); c.scale(1.9, 1.9); c.translate(-lx, -ly); c.fillStyle = OWL.face; ell(c, lx, ly, 42, 42); c.fill();
    drawEye(c, fx + 33, -205, 22, 22, st, -1, OWL.face, { brow: false, pr: 12 });
    c.restore();
    ell(c, lx, ly, 48, 48); c.lineWidth = 7; c.strokeStyle = '#5a3f24'; c.stroke();
    c.restore();
  }
  c.restore();
}

// ---------------------------------------------------------------- Eeyore
const EEY = { body: '#8f96a4', dark: '#6b7180', light: '#c5c9d1', mane: '#3b3e49', ear: '#5e6370' };
// gait: returns leg angles [backFar, frontFar, backNear, frontNear], knee bends, bob, pitch
function eeyoreGait(st) {
  const legs = [0, 0, 0, 0], knees = [0, 0, 0, 0];
  let bob = 0, pitch = 0;
  const w = st.walk || 0, g = st.gallop || 0, p = st.phase || 0;
  if (w > 0) {
    const off = [0, .25, .5, .75];
    for (let i = 0; i < 4; i++) {
      const ph = (p + off[i]) * TAU;
      legs[i] += Math.sin(ph) * .32 * w; knees[i] += Math.max(0, Math.cos(ph)) * .55 * w;
    }
    bob += -Math.abs(Math.sin(p * TAU * 2)) * 5 * w;
  }
  if (g > 0) {
    const off = [0, .55, .08, .63];
    for (let i = 0; i < 4; i++) {
      const ph = (p + off[i]) * TAU;
      legs[i] += Math.sin(ph) * .75 * g; knees[i] += Math.max(0, Math.cos(ph)) * 1.0 * g;
    }
    bob += -Math.abs(Math.sin(p * TAU)) * 34 * g; pitch += Math.sin(p * TAU + .6) * .07 * g;
  }
  return { legs, knees, bob, pitch };
}
function eeyLeg(c, x, y, a, knee, fill, front) {
  c.save(); c.translate(x, y); c.rotate(-a);
  c.beginPath(); c.moveTo(-23, -14); c.quadraticCurveTo(-24, 30, -17, 58); c.lineTo(17, 58); c.quadraticCurveTo(24, 30, 23, -14); c.closePath(); fs(c, fill);
  c.translate(0, 56); c.rotate(front ? knee : -knee);
  c.beginPath(); c.moveTo(-17, 0); c.lineTo(-15, 46); c.lineTo(15, 46); c.lineTo(17, 0); c.closePath(); fs(c, fill);
  ell(c, 0, 0, 18, 12); c.fillStyle = fill; c.fill();
  c.beginPath(); c.moveTo(-17, 42); c.lineTo(-19, 60); c.lineTo(19, 60); c.lineTo(16, 42); c.closePath(); fs(c, '#3b3a40', 3.5);
  c.restore();
}
function drawEeyore(c, st) {
  const s = st.s || 1, f = st.facing || 1;
  const gait = eeyoreGait(st);
  const sag = st.sag || 0; // whole-body slump
  c.save(); c.translate(st.x, st.y + gait.bob + (st.bob || 0)); c.scale(s * f * (st.turnSquash ?? 1), s);
  c.save(); c.translate(0, -140); c.rotate(gait.pitch + (st.tilt || 0)); c.translate(0, 140);
  if (st.desat) c.filter = `saturate(${1 - st.desat}) brightness(${1 - st.desat * .25})`;
  // far legs
  eeyLeg(c, -70, -116, gait.legs[0], gait.knees[0], EEY.dark, false);
  eeyLeg(c, 88, -116, gait.legs[1], gait.knees[1], EEY.dark, true);
  // tail
  const wag = (st.tailWag || 0) * Math.sin((st.t || 0) * 9) * .5 + (st.tail || 0);
  const tx = -128, ty = -176 + sag * 4;
  const ex = tx - 40 - Math.sin(wag) * 30 - (st.gallop || 0) * 40, ey = ty + 70 - Math.cos(wag) * 8 - (st.gallop || 0) * 52 - (st.tailUp || 0) * 60;
  c.beginPath(); c.moveTo(tx, ty); c.quadraticCurveTo(tx - 28, ty + 10 - (st.tailUp || 0) * 30, ex, ey);
  c.lineWidth = 9; c.strokeStyle = OUT; c.lineCap = 'round'; c.stroke(); c.lineWidth = 5; c.strokeStyle = EEY.body; c.stroke();
  c.save(); c.translate(ex, ey); c.rotate(Math.atan2(ey - ty - 10, ex - tx + 28) - Math.PI / 2);
  c.beginPath(); c.moveTo(-6, -4); c.quadraticCurveTo(-16, 18, -2, 34); c.quadraticCurveTo(4, 24, 8, 34); c.quadraticCurveTo(16, 14, 6, -4); c.closePath(); fs(c, EEY.mane, 3);
  c.restore();
  // body
  ell(c, 0, -160 + sag * 6, 132, 74); fs(c, radial(c, 0, -170, 132, '#a0a6b3', EEY.body));
  c.save(); ell(c, 0, -160 + sag * 6, 132, 74); c.clip(); c.fillStyle = EEY.light; ell(c, 10, -96 + sag * 6, 108, 28); c.fill(); c.restore();
  // near legs
  eeyLeg(c, -88, -114, gait.legs[2], gait.knees[2], EEY.body, false);
  eeyLeg(c, 70, -114, gait.legs[3], gait.knees[3], EEY.body, true);
  // neck
  const hd = st.headDrop ?? .5;
  c.beginPath(); c.moveTo(58, -208 + sag * 5); c.quadraticCurveTo(92, -246 + hd * 18, 122, -262 + hd * 34);
  c.lineTo(156, -214 + hd * 32); c.quadraticCurveTo(122, -160, 100, -124); c.closePath();
  fs(c, EEY.body);
  c.fillStyle = EEY.body; ell(c, 90, -170, 30, 40); c.fill();
  // mane
  c.fillStyle = EEY.mane;
  c.beginPath(); c.moveTo(56, -206 + sag * 5);
  for (let i = 0; i <= 6; i++) {
    const k = i / 6, mx = lerp(56, 124, k), my = lerp(-206 + sag * 5, -262 + hd * 34, k) + k * (1 - k) * -40;
    c.lineTo(mx - 4, my - 12 - (i % 2) * 5); c.lineTo(mx + 6, my + 2);
  }
  c.lineTo(122, -250 + hd * 34); c.quadraticCurveTo(90, -232, 62, -198); c.closePath(); fs(c, EEY.mane, 2.5);
  // head
  c.save(); c.translate(132, -244 + hd * 32); c.rotate(-.12 + hd * .5 + (st.headTilt || 0)); c.scale(1.22, 1.22);
  const ears = st.ears ?? 0, flap = (st.earFlap || 0) * Math.sin((st.t || 0) * 18);
  const earAng = ears >= 0 ? lerp(-2.2, -.3, ears) : lerp(-2.2, -1.5, Math.min(1, -ears * 2));
  const drawEar = (x, y, extra, fill) => {
    c.save(); c.translate(x, y); c.rotate(earAng + extra + flap * .25);
    c.beginPath(); c.moveTo(-14, 0); c.quadraticCurveTo(-24, -54, -2, -98); c.quadraticCurveTo(22, -54, 14, 0); c.closePath(); fs(c, fill);
    c.beginPath(); c.moveTo(-6, -8); c.quadraticCurveTo(-12, -50, -1, -84); c.quadraticCurveTo(10, -50, 6, -8); c.closePath(); c.fillStyle = EEY.ear; c.fill();
    c.restore();
  };
  drawEar(10, -38, .18, EEY.dark);
  // skull + muzzle with merged outline (stroke first, then fill)
  c.lineWidth = 8; c.strokeStyle = OUT;
  ell(c, 18, -6, 54, 46); c.stroke(); ell(c, 84, 22, 50, 37, .18); c.stroke();
  c.fillStyle = EEY.body; ell(c, 18, -6, 54, 46); c.fill(); ell(c, 84, 22, 50, 37, .18); c.fill();
  c.fillStyle = EEY.light; ell(c, 96, 26, 37, 30, .2); c.fill();
  c.fillStyle = '#3a3d47'; ell(c, 120, 14, 5, 8, .5); c.fill();
  drawEar(-6, -38, 0, EEY.body);
  // forelock
  c.beginPath(); c.moveTo(2, -44); c.quadraticCurveTo(22, -66, 30, -40); c.quadraticCurveTo(38, -58, 46, -34); c.quadraticCurveTo(28, -30, 6, -36); c.closePath(); fs(c, EEY.mane, 2.5);
  const e = Object.assign({}, st, { lid: st.lid ?? .45 });
  drawEye(c, 60, -14, 10, 13, e, -1, EEY.body, { bw: 4, pr: 7 });
  drawEye(c, 30, -8, 15, 17, e, 1, EEY.body, { bw: 4.5, pr: 9.5 });
  c.save(); c.translate(92, 50); c.rotate(-.12);
  drawMouth(c, 0, 0, 52, st.smile ?? -.35, st.mouth || 0, { openScale: .5 });
  c.restore();
  if (st.blushA) blush(c, 50, 22, 16, st.blushA);
  c.restore();
  c.restore();
  c.restore();
}

// ---------------------------------------------------------------- Bird
function drawBird(c, st) {
  const s = st.s || 1, f = st.facing || 1;
  c.save(); c.translate(st.x, st.y); c.scale(s * f, s);
  const fl = st.flap ? Math.sin((st.t || 0) * 38) : -.3;
  c.save(); c.translate(-6, -26); c.rotate(-.6 - fl * .9); ell(c, -18, 0, 26, 11); fs(c, '#3f6fa8', 3); c.restore();
  c.beginPath(); c.moveTo(-26, -24); c.lineTo(-52, -34); c.lineTo(-50, -18); c.closePath(); fs(c, '#3f6fa8', 3);
  ell(c, 0, -22, 28, 22); fs(c, radial(c, 0, -22, 26, '#78a9de', '#4a7fbd'), 3);
  c.fillStyle = '#f4e3c3'; ell(c, 6, -14, 16, 12); c.fill();
  ell(c, 20, -44, 18, 17); fs(c, '#5a8fcc', 3);
  const m = st.mouth || 0;
  c.beginPath(); c.moveTo(34, -48); c.lineTo(52, -44 - m * 3); c.lineTo(35, -40); c.closePath(); fs(c, '#efa43a', 2.5);
  if (m > .05) { c.beginPath(); c.moveTo(34, -40); c.lineTo(50, -38 + m * 6); c.lineTo(34, -36); c.closePath(); fs(c, '#d68a28', 2.5); }
  drawEye(c, 26, -48, 5, 6, st, 1, '#5a8fcc', { brow: false, olw: 2, pr: 3.6 });
  if (!st.flap) { c.strokeStyle = '#d68a28'; c.lineWidth = 3; c.beginPath(); c.moveTo(-4, 0); c.lineTo(-4, 8); c.moveTo(6, 0); c.lineTo(6, 8); c.stroke(); }
  c.restore();
}

// ---------------------------------------------------------------- props
function thoughtBubble(c, x, y, w, h, a, tailTo) {
  c.save(); c.globalAlpha = a;
  c.fillStyle = 'rgba(255,253,245,.96)'; c.strokeStyle = OUT; c.lineWidth = 4;
  const n = 11;
  c.beginPath();
  for (let i = 0; i < n; i++) {
    const a0 = i / n * TAU, a1 = (i + 1) / n * TAU, am = (a0 + a1) / 2;
    const p0 = [x + Math.cos(a0) * w / 2, y + Math.sin(a0) * h / 2];
    const p1 = [x + Math.cos(a1) * w / 2, y + Math.sin(a1) * h / 2];
    if (i === 0) c.moveTo(...p0);
    c.quadraticCurveTo(x + Math.cos(am) * w * .62, y + Math.sin(am) * h * .66, ...p1);
  }
  c.closePath(); c.fill(); c.stroke();
  if (tailTo) {
    for (let i = 0; i < 3; i++) {
      const k = (i + 1) / 4, r = 16 - i * 4.5;
      ell(c, lerp(x, tailTo[0], k + .1), lerp(y + h * .45, tailTo[1], k + .1), r, r * .8); c.fill(); c.stroke();
    }
  }
  c.restore();
}

function rainCloud(c, x, y, s, dark = .5, rain = 0, t = 0) {
  c.save(); c.translate(x, y); c.scale(s, s);
  if (rain > 0) {
    c.strokeStyle = `rgba(120,150,190,${.7 * rain})`; c.lineWidth = 3;
    for (let i = 0; i < 14; i++) {
      const xx = -80 + i * 12, yy = ((t * 420 + i * 53) % 160);
      c.beginPath(); c.moveTo(xx, 20 + yy); c.lineTo(xx - 3, 34 + yy); c.stroke();
    }
  }
  const col = `rgb(${lerp(200, 105, dark)},${lerp(205, 110, dark)},${lerp(215, 125, dark)})`;
  c.fillStyle = col; c.strokeStyle = 'rgba(61,43,31,.6)'; c.lineWidth = 3;
  c.beginPath(); c.arc(-50, 0, 34, Math.PI * .5, Math.PI * 1.5); c.arc(-10, -26, 40, Math.PI, 0); c.arc(40, -10, 34, Math.PI * 1.3, Math.PI * .5); c.closePath(); c.fill(); c.stroke();
  c.restore();
}
