// Character designs (built on the shared rig from the-last-witness) plus the spider and the sun.
'use strict';
const path = require('path');
const LW = path.join(__dirname, '../../../the-last-witness/render/lib');
const U = require(path.join(LW, 'util'));
const R = require(path.join(LW, 'rig'));
const C = require(path.join(LW, 'chars'));
const { rgba, mix, shade, lerp, clamp, smooth, TAU } = U;

const base = C.HUMAN;
function person(over) { return { ...base, grey: 0, stubble: 0, age: 0.1, torsoDetail: null, ...over }; }

// glasses that sit on the nose bridge and follow the eyes
function glasses(ctx, ch, st, k, a, fy) {
  ctx.save();
  ctx.strokeStyle = rgba([60, 50, 46], 0.9); ctx.lineWidth = 0.012;
  const eyes = [-1, 1].map((sgn) => { const th = sgn * 0.48 + a; return { f: Math.cos(th), x: 0.37 * Math.sin(th) + k * 0.035 }; });
  for (const e of eyes) {
    if (e.f < 0.1) continue;
    ctx.beginPath(); ctx.ellipse(e.x, -0.02 + fy, 0.085 * Math.pow(e.f, 0.8), 0.058, 0, 0, TAU); ctx.stroke();
    ctx.fillStyle = rgba([220, 235, 245], 0.08); ctx.fill();
  }
  ctx.beginPath(); ctx.moveTo(eyes[0].x + 0.06 * eyes[0].f, -0.035 + fy); ctx.quadraticCurveTo(k * 0.08, -0.06 + fy, eyes[1].x - 0.06 * eyes[1].f, -0.035 + fy); ctx.stroke();
  ctx.restore();
}

const PASSENGERS = {
  elder: person({ name: 'elder', skin: [226, 190, 166], skinShadow: [150, 110, 96], lip: [176, 112, 108], hair: [200, 196, 192], brow: [170, 164, 158], iris: [90, 110, 120],
    age: 0.85, headW: 0.72, jaw: 0.72, cloth: { base: [104, 124, 92], shadow: [56, 70, 48], collar: [86, 104, 76] }, collar: 'vneck',
    hairFront: C.shortHair({ volume: 0.1, hairline: -0.3, seed: 51, wave: 0.03, strands: 18 }) }),
  suit: person({ name: 'suit', skin: [168, 118, 92], skinShadow: [100, 66, 50], lip: [140, 90, 80], hair: [30, 26, 26], brow: [30, 26, 26], iris: [60, 40, 30],
    jaw: 0.86, stubble: 0.12, cloth: { base: [46, 54, 82], shadow: [22, 26, 44], collar: [228, 228, 232] }, collar: 'vneck',
    hairFront: C.shortHair({ volume: 0.035, hairline: -0.33, seed: 61, wave: 0.006, strands: 16 }) }),
  teen: person({ name: 'teen', skin: [238, 204, 182], skinShadow: [170, 124, 110], lip: [190, 120, 116], hair: [120, 80, 52], brow: [100, 66, 44], iris: [70, 110, 80],
    headW: 0.7, jaw: 0.7, cloth: { base: [158, 56, 50], shadow: [86, 26, 24], collar: [140, 48, 44] }, collar: 'crew',
    hairFront: C.shortHair({ volume: 0.09, hairline: -0.25, seed: 71, wave: 0.03, strands: 22 }) }),
  woman: person({ name: 'woman', skin: [124, 84, 64], skinShadow: [70, 44, 34], lip: [120, 66, 62], hair: [24, 18, 18], brow: [24, 18, 18], iris: [50, 32, 22], lashes: true,
    headW: 0.7, jaw: 0.68, chinW: 0.27, cloth: { base: [108, 74, 136], shadow: [56, 36, 74], collar: [92, 62, 118] }, collar: 'crew',
    ...C.longHair({ seed: 81, length: 1.3, hairline: -0.33 }) }),
  beard: person({ name: 'beard', skin: [204, 156, 120], skinShadow: [130, 90, 66], lip: [150, 96, 84], hair: [86, 60, 40], brow: [80, 56, 38], iris: [80, 60, 40],
    jaw: 0.84, stubble: 0.55, stubbleColor: [86, 60, 40], cloth: { base: [114, 84, 58], shadow: [60, 42, 28], collar: [96, 70, 48] }, collar: 'crew',
    hairFront: C.shortHair({ volume: 0.05, hairline: -0.3, seed: 91, wave: 0.01 }) }),
};
// the child: shorter neck and torso, bigger eyes, a yellow raincoat-coloured sweater
const CHILD = person({ name: 'child', prop: { head: 1.16, neck: 0.6, body: 0.74 }, skin: [196, 138, 102], skinShadow: [124, 80, 58], lip: [170, 100, 92],
  hair: [40, 28, 24], brow: [40, 28, 24], iris: [70, 46, 30], eyeSize: 1.22, irisScale: 1.08, lashes: true, headW: 0.78, jaw: 0.74, chinW: 0.34, noseSize: 0.8, mouthW: 0.9,
  cloth: { base: [226, 180, 58], shadow: [140, 100, 26], collar: [206, 160, 46] }, collar: 'crew', armW: 0.19,
  hairFront: C.shortHair({ volume: 0.1, hairline: -0.32, seed: 101, wave: 0.035, strands: 24 }) });
const THERAPIST = person({ name: 'therapist', skin: [232, 198, 174], skinShadow: [160, 120, 104], lip: [180, 110, 106], hair: [176, 172, 168], brow: [130, 124, 120],
  iris: [80, 100, 90], age: 0.55, headW: 0.71, jaw: 0.7, lashes: true, cloth: { base: [66, 118, 118], shadow: [30, 64, 66], collar: [56, 104, 104] }, collar: 'vneck',
  hairFront: C.shortHair({ volume: 0.085, hairline: -0.31, seed: 111, wave: 0.02, strands: 20 }), headOverlay: glasses });

// ---------------------------------------------------------------- spider
// x,y = centre of the head; size = head radius px. st: {lid, browIn, browOut, smile, open, gaze{x,y},
// blink, legPhase, climb, tear, burden, angle, numb, wet}
function spider(ctx, x, y, size, st = {}) {
  const s = size;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(st.angle || 0);
  const body = [52, 40, 38], fuzz = [120, 100, 90];
  // legs: four per side, three segments each, alternating gait when climbing
  const legs = [];
  for (const side of [-1, 1]) {
    for (let i = 0; i < 4; i++) {
      const ph = (st.legPhase || 0) * TAU + i * Math.PI * 0.5 + (side > 0 ? Math.PI : 0);
      const swing = st.climb ? Math.sin(ph) * 0.22 : Math.sin((st.t || 0) * 1.3 + i + side) * 0.03;
      const lift = st.climb ? Math.max(0, Math.cos(ph)) * 0.25 : 0;
      const a0 = side * (0.55 + i * 0.32) + swing * side - Math.PI / 2 + (st.legSpread || 0) * side;
      const p0 = [Math.cos(a0) * s * 0.75, Math.sin(a0) * s * 0.55 + s * 0.6];
      const k1 = [p0[0] + Math.cos(a0) * s * 1.1, p0[1] + Math.sin(a0) * s * 1.1 - s * (0.7 + lift)];
      const k2 = [k1[0] + Math.cos(a0) * s * 0.9, k1[1] + s * (1.2 - lift * 0.5)];
      legs.push([p0, k1, k2]);
    }
  }
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const [p0, k1, k2] of legs) {
    ctx.strokeStyle = rgba(shade(body, -0.25)); ctx.lineWidth = s * 0.15;
    ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(k1[0], k1[1]); ctx.lineTo(k2[0], k2[1]); ctx.stroke();
    ctx.strokeStyle = rgba(fuzz, 0.35); ctx.lineWidth = s * 0.04;
    ctx.beginPath(); ctx.moveTo(p0[0], p0[1] - s * 0.03); ctx.lineTo(k1[0], k1[1] - s * 0.03); ctx.stroke();
    ctx.fillStyle = rgba(shade(body, -0.1)); ctx.beginPath(); ctx.arc(k1[0], k1[1], s * 0.09, 0, TAU); ctx.fill();
  }
  // abdomen behind the head, with the burden bundle tied on
  const ab = [0, s * 1.45];
  const g = ctx.createRadialGradient(ab[0] - s * 0.3, ab[1] - s * 0.3, s * 0.1, ab[0], ab[1], s * 1.2);
  g.addColorStop(0, rgba(shade(body, 0.25))); g.addColorStop(1, rgba(shade(body, -0.2)));
  ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(ab[0], ab[1], s * 1.05, s * 1.15, 0, 0, TAU); ctx.fill();
  ctx.strokeStyle = rgba(fuzz, 0.4); ctx.lineWidth = s * 0.05; ctx.stroke();
  if (st.burden) {
    const bx = s * 0.15, by = s * 1.9;
    ctx.fillStyle = rgba([40, 36, 48]);
    ctx.beginPath(); ctx.ellipse(bx, by, s * 0.75, s * 0.6, 0.2, 0, TAU); ctx.fill();
    ctx.strokeStyle = rgba([150, 130, 110], 0.8); ctx.lineWidth = s * 0.06;
    ctx.beginPath(); ctx.moveTo(-s * 0.9, s * 1.2); ctx.quadraticCurveTo(bx, by - s * 0.2, s * 1.0, s * 1.3); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(bx - s * 0.1, by - s * 0.6); ctx.lineTo(bx + s * 0.1, by - s * 0.75); ctx.stroke();
    ctx.fillStyle = rgba([80, 70, 100], 0.4); ctx.beginPath(); ctx.ellipse(bx - s * 0.2, by - s * 0.2, s * 0.3, s * 0.15, 0.2, 0, TAU); ctx.fill();
  }
  // head
  const hg = ctx.createRadialGradient(-s * 0.3, -s * 0.35, s * 0.1, 0, 0, s * 1.05);
  hg.addColorStop(0, rgba(shade(body, 0.3))); hg.addColorStop(1, rgba(shade(body, -0.15)));
  ctx.fillStyle = hg; ctx.beginPath(); ctx.ellipse(0, 0, s, s * 0.92, 0, 0, TAU); ctx.fill();
  // fuzzy rim
  ctx.strokeStyle = rgba(fuzz, 0.45); ctx.lineWidth = s * 0.05;
  for (let i = 0; i < 26; i++) {
    const a = (i / 26) * TAU; const r1 = s * 0.95, r2 = s * (1.06 + 0.04 * Math.sin(i * 3.1));
    ctx.beginPath(); ctx.moveTo(Math.cos(a) * r1, Math.sin(a) * r1 * 0.92); ctx.lineTo(Math.cos(a) * r2, Math.sin(a) * r2 * 0.92); ctx.stroke();
  }
  if (st.wet) { ctx.fillStyle = rgba([180, 210, 240], 0.25 * st.wet); ctx.beginPath(); ctx.ellipse(-s * 0.35, -s * 0.45, s * 0.25, s * 0.12, -0.5, 0, TAU); ctx.fill(); }
  // four tiny secondary eyes
  ctx.fillStyle = rgba([20, 14, 14]);
  for (const [ex, ey] of [[-0.42, -0.62], [-0.15, -0.72], [0.15, -0.72], [0.42, -0.62]]) { ctx.beginPath(); ctx.arc(ex * s, ey * s, s * 0.06, 0, TAU); ctx.fill(); }
  // two big expressive eyes with lids, brows, catch-lights
  const blink = clamp(st.blink || 0);
  const lid = clamp((st.lid ?? 1) * (1 - blink), 0, 1.25);
  for (const sgn of [-1, 1]) {
    const ex = sgn * s * 0.38, ey = -s * 0.12, er = s * 0.3;
    ctx.save();
    ctx.beginPath(); ctx.ellipse(ex, ey, er, er * 1.08, 0, 0, TAU); ctx.fillStyle = rgba([245, 240, 230]); ctx.fill();
    ctx.clip();
    const gx = (st.gaze?.x || 0) * er * 0.38, gy = (st.gaze?.y || 0) * er * 0.4;
    ctx.fillStyle = rgba([110, 70, 40]); ctx.beginPath(); ctx.arc(ex + gx, ey + gy, er * 0.62, 0, TAU); ctx.fill();
    ctx.fillStyle = rgba([18, 10, 8]); ctx.beginPath(); ctx.arc(ex + gx, ey + gy, er * (st.numb ? 0.24 : 0.36), 0, TAU); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.9)'; ctx.beginPath(); ctx.arc(ex + gx - er * 0.2, ey + gy - er * 0.22, er * 0.15, 0, TAU); ctx.fill();
    // upper lid comes down from the top
    const lidY = ey - er * 1.08 + (1 - Math.min(1, lid)) * er * 2.1;
    ctx.fillStyle = rgba(shade(body, 0.12));
    ctx.beginPath(); ctx.rect(ex - er * 1.2, ey - er * 1.3, er * 2.4, lidY - (ey - er * 1.3)); ctx.fill();
    ctx.strokeStyle = rgba([20, 12, 10]); ctx.lineWidth = s * 0.05;
    ctx.beginPath(); ctx.moveTo(ex - er, lidY); ctx.quadraticCurveTo(ex, lidY + er * 0.12, ex + er, lidY); ctx.stroke();
    ctx.restore();
    ctx.strokeStyle = rgba(shade(body, -0.4)); ctx.lineWidth = s * 0.04;
    ctx.beginPath(); ctx.ellipse(ex, ey, er, er * 1.08, 0, 0, TAU); ctx.stroke();
    // brow: inner end rises with worry/sadness, drops with determination
    const bi = (st.browIn || 0), bo = (st.browOut || 0);
    ctx.strokeStyle = rgba([24, 16, 14]); ctx.lineWidth = s * 0.08;
    ctx.beginPath();
    ctx.moveTo(ex - sgn * er * 0.9, ey - er * 1.3 - bi * er * 0.45 + (st.furrow || 0) * er * 0.3);
    ctx.quadraticCurveTo(ex, ey - er * 1.55 - (bi + bo) * er * 0.2, ex + sgn * er * 0.95, ey - er * 1.3 - bo * er * 0.4);
    ctx.stroke();
  }
  // mouth
  const sm = st.smile || 0, op = st.open || 0;
  ctx.strokeStyle = rgba([20, 10, 10]); ctx.lineWidth = s * 0.06;
  if (op > 0.05) {
    ctx.fillStyle = rgba([70, 20, 26]);
    ctx.beginPath(); ctx.ellipse(0, s * 0.42, s * 0.16, s * 0.08 + op * s * 0.14, 0, 0, TAU); ctx.fill();
  } else {
    ctx.beginPath(); ctx.moveTo(-s * 0.18, s * 0.42 - sm * s * 0.06); ctx.quadraticCurveTo(0, s * 0.42 + sm * s * 0.12, s * 0.18, s * 0.42 - sm * s * 0.06); ctx.stroke();
  }
  // fangs (tiny)
  ctx.fillStyle = rgba([60, 44, 40]);
  for (const sgn of [-1, 1]) { ctx.beginPath(); ctx.moveTo(sgn * s * 0.1, s * 0.62); ctx.lineTo(sgn * s * 0.04, s * 0.78); ctx.lineTo(sgn * s * 0.16, s * 0.66); ctx.fill(); }
  // a single tear from one eye, running down and fading as a whole
  if (st.tear > 0 && st.tear < 1) {
    const p = st.tear, ty = -s * 0.1 + p * s * 0.9, tx = s * 0.6 + Math.sin(p * 4) * s * 0.02;
    ctx.globalAlpha *= 1 - smooth((p - 0.7) / 0.3);
    const tg = ctx.createRadialGradient(tx, ty, 0, tx, ty, s * 0.09);
    tg.addColorStop(0, 'rgba(235,248,255,0.95)'); tg.addColorStop(1, 'rgba(120,180,240,0.5)');
    ctx.fillStyle = tg; ctx.beginPath(); ctx.moveTo(tx, ty - s * 0.12); ctx.quadraticCurveTo(tx + s * 0.08, ty, tx, ty + s * 0.07); ctx.quadraticCurveTo(tx - s * 0.08, ty, tx, ty - s * 0.12); ctx.fill();
  }
  ctx.restore();
}
const SPIDER_MOODS = {
  shy: { lid: 0.85, browIn: 0.3, smile: 0.15 },
  hopeful: { lid: 1.05, browIn: 0.35, browOut: 0.35, smile: 0.35, gaze: { x: 0, y: -0.8 } },
  sad: { lid: 0.7, browIn: 0.8, smile: -0.6, gaze: { x: 0.2, y: 0.5 } },
  strain: { lid: 0.85, browIn: 0.6, furrow: 0.4, smile: -0.3, open: 0.15 },
  worried: { lid: 1.1, browIn: 0.9, smile: -0.4, gaze: { x: 0, y: -0.85 } },
  panic: { lid: 1.25, browIn: 1, browOut: 0.6, open: 0.6 },
  dazed: { lid: 0.6, browIn: 0.4, smile: -0.1, gaze: { x: 0.3, y: -0.5 } },
  numb: { lid: 0.45, browIn: 0, smile: 0.05, numb: true },
  unsure: { lid: 0.95, browIn: 0.5, browOut: 0.2, smile: -0.1, gaze: { x: -0.6, y: -0.3 } },
  determined: { lid: 0.9, browIn: -0.2, furrow: 0.5, smile: -0.15, gaze: { x: 0, y: -0.7 } },
  final: { lid: 0.85, browIn: 0.7, smile: -0.25, gaze: { x: 0, y: -0.8 } },
};

// ---------------------------------------------------------------- sun
// st: {smile, lid, browUp, gaze, t, beam: [x,y] target}
function sun(ctx, x, y, r, st = {}) {
  const t = st.t || 0;
  ctx.save();
  ctx.translate(x, y);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const halo = ctx.createRadialGradient(0, 0, r * 0.8, 0, 0, r * 3.2);
  halo.addColorStop(0, 'rgba(255,214,120,0.45)'); halo.addColorStop(1, 'rgba(255,214,120,0)');
  ctx.fillStyle = halo; ctx.fillRect(-r * 3.2, -r * 3.2, r * 6.4, r * 6.4);
  ctx.restore();
  // soft tapered rays rotating slowly
  ctx.fillStyle = 'rgba(255,200,90,0.85)';
  for (let i = 0; i < 14; i++) {
    const a = i / 14 * TAU + t * 0.08, L = r * (1.45 + 0.12 * Math.sin(t * 1.2 + i * 1.7));
    ctx.beginPath();
    ctx.moveTo(Math.cos(a - 0.1) * r * 0.95, Math.sin(a - 0.1) * r * 0.95);
    ctx.quadraticCurveTo(Math.cos(a) * L * 0.9, Math.sin(a) * L * 0.9, Math.cos(a) * L, Math.sin(a) * L);
    ctx.quadraticCurveTo(Math.cos(a) * L * 0.9, Math.sin(a) * L * 0.9, Math.cos(a + 0.1) * r * 0.95, Math.sin(a + 0.1) * r * 0.95);
    ctx.fill();
  }
  const g = ctx.createRadialGradient(-r * 0.3, -r * 0.35, r * 0.1, 0, 0, r);
  g.addColorStop(0, '#fff2b8'); g.addColorStop(0.6, '#ffd060'); g.addColorStop(1, '#f2a83a');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fill();
  // cheeks
  for (const sgn of [-1, 1]) {
    const cg = ctx.createRadialGradient(sgn * r * 0.5, r * 0.22, 0, sgn * r * 0.5, r * 0.22, r * 0.25);
    cg.addColorStop(0, 'rgba(240,120,90,0.45)'); cg.addColorStop(1, 'rgba(240,120,90,0)');
    ctx.fillStyle = cg; ctx.fillRect(sgn * r * 0.5 - r * 0.3, r * 0.22 - r * 0.3, r * 0.6, r * 0.6);
  }
  // eyes: kindly half-moons or open, brows raised (benign, patronising)
  const lid = clamp((st.lid ?? 0.55) * (1 - (st.blink || 0)), 0, 1);
  for (const sgn of [-1, 1]) {
    const ex = sgn * r * 0.35, ey = -r * 0.12, er = r * 0.13;
    ctx.save();
    ctx.beginPath(); ctx.ellipse(ex, ey, er, er * 1.15, 0, 0, TAU); ctx.fillStyle = '#fffaf0'; ctx.fill(); ctx.clip();
    ctx.fillStyle = '#5a3a20'; ctx.beginPath(); ctx.arc(ex + (st.gaze?.x || 0) * er * 0.4, ey + (st.gaze?.y || 0) * er * 0.4, er * 0.6, 0, TAU); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(ex - er * 0.25 + (st.gaze?.x || 0) * er * 0.4, ey - er * 0.3, er * 0.18, 0, TAU); ctx.fill();
    const lidY = ey - er * 1.15 + (1 - lid) * er * 2.3;
    ctx.fillStyle = '#f7c050'; ctx.fillRect(ex - er * 1.3, ey - er * 1.4, er * 2.6, lidY - (ey - er * 1.4));
    ctx.restore();
    ctx.strokeStyle = '#7a4a1e'; ctx.lineWidth = r * 0.03;
    ctx.beginPath(); ctx.moveTo(ex - er, ey - er * 1.15 + (1 - lid) * er * 2.3); ctx.quadraticCurveTo(ex, ey - er * 0.9 + (1 - lid) * er * 2.3, ex + er, ey - er * 1.15 + (1 - lid) * er * 2.3); ctx.stroke();
    ctx.lineWidth = r * 0.035; ctx.lineCap = 'round';
    const bu = st.browUp ?? 0.5;
    ctx.beginPath(); ctx.moveTo(ex - er * 1.1, ey - er * 1.7 - bu * er * 0.5); ctx.quadraticCurveTo(ex, ey - er * 2.2 - bu * er * 0.6, ex + er * 1.1, ey - er * 1.7 - bu * er * 0.5); ctx.stroke();
  }
  // broad closed smile
  const sm = st.smile ?? 0.8;
  ctx.strokeStyle = '#7a3a1a'; ctx.lineWidth = r * 0.045; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(-r * 0.36, r * 0.3); ctx.quadraticCurveTo(0, r * (0.3 + 0.35 * sm), r * 0.36, r * 0.3); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-r * 0.4, r * 0.26); ctx.lineTo(-r * 0.33, r * 0.33); ctx.moveTo(r * 0.4, r * 0.26); ctx.lineTo(r * 0.33, r * 0.33); ctx.stroke();
  ctx.restore();
}

module.exports = { PASSENGERS, CHILD, THERAPIST, spider, SPIDER_MOODS, sun, R, U, C };
