// Character designs: palettes, proportions, hair and special overlays.
'use strict';
const U = require('./util');
const { rgba, shade, mix, lerp, clamp, smooth } = U;
const R = require('./rig');

// ---- hair builders --------------------------------------------------------
// Short hair: a mass hugging the skull above a hairline, wavy top edge, soft strands.
function shortHair(opts) {
  return function hairFront(ctx, ch, k, pitch, L, st, outline) {
    const vol = opts.volume ?? 0.055;
    const hairlineY = opts.hairline ?? -0.3;
    const templeY = opts.temple ?? -0.12;
    const backY = opts.backY ?? -0.02;  // the turned-away side covers down to just above the ear
    const facingRight = k >= 0;
    const half = outline.length / 2;
    // outline: first half runs down the right side (top → chin), second half up the left side
    const rightLim = facingRight ? templeY : backY, leftLim = facingRight ? backY : templeY;
    const right = outline.slice(0, half).filter((p) => p[1] < rightLim);
    const left = outline.slice(half).filter((p) => p[1] < leftLim);
    const edge = [];
    const seed = opts.seed || 0;
    const push = (p, i) => {
      const ny = p[1];
      const up = smooth((-ny - 0.05) / 0.45);
      const v = vol * (0.35 + 0.65 * up) + (opts.wave ?? 0.012) * Math.sin(i * 1.9 + seed) * up;
      const sx = Math.sign(p[0] - k * 0.05) || 1;
      edge.push([p[0] + sx * v * (0.6 + 0.4 * (1 - up)), p[1] - v * up * 1.1]);
    };
    right.slice().reverse().forEach((p, i) => push(p, i));
    left.slice().reverse().forEach((p, i) => push(p, i + 40));
    // hairline across the forehead (left temple → right temple), slight recession at the temples
    const lx = edge[edge.length - 1], rx = edge[0];
    const hl = [];
    const N = 12;
    for (let i = 0; i <= N; i++) {
      const u = i / N;
      const x = lerp(lx[0] + 0.012, rx[0] - 0.012, u);
      const arch = Math.sin(u * Math.PI);
      const recede = (opts.recede ?? 0.02) * (Math.exp(-Math.pow((u - 0.2) / 0.1, 2)) + Math.exp(-Math.pow((u - 0.8) / 0.1, 2)));
      const y = lerp(lerp(lx[1], rx[1], u), hairlineY, Math.pow(arch, 0.5)) - recede + Math.sin(u * 11 + seed) * 0.005 * arch;
      hl.push([x, y]);
    }
    const shape = edge.concat(hl);
    ctx.save();
    ctx.beginPath(); R.smoothPath(ctx, shape);
    const g = ctx.createLinearGradient(0, -0.66, 0, 0.0);
    g.addColorStop(0, rgba(shade(ch.hair, 0.1))); g.addColorStop(0.55, rgba(ch.hair)); g.addColorStop(1, rgba(shade(ch.hair, -0.2)));
    ctx.fillStyle = g; ctx.fill();
    ctx.save(); ctx.clip();
    if (L.amb && L.ambA) { ctx.fillStyle = rgba(L.amb, L.ambA * 0.8); ctx.fillRect(-1, -1, 2, 2); }
    ctx.fillStyle = R.lightGrad(ctx, -0.45, 0.45, L, ch.hair, shade(ch.hair, -0.6), 0.8); ctx.fillRect(-1, -1, 2, 2);
    if (ch.grey) {
      for (const sgn of [-1, 1]) {
        const gx = sgn * 0.3 + k * 0.05;
        const gg = ctx.createRadialGradient(gx, -0.12, 0, gx, -0.12, 0.2);
        gg.addColorStop(0, rgba(ch.greyColor || [190, 188, 184], ch.grey)); gg.addColorStop(1, rgba(ch.greyColor || [190, 188, 184], 0));
        ctx.fillStyle = gg; ctx.fillRect(gx - 0.2, -0.35, 0.4, 0.4);
      }
    }
    // strands swept back from the hairline toward the crown: roughly parallel, ordered so they never cross
    const rnd = U.rng(seed + 7);
    const topEdge = edge.filter((p) => p[1] < -0.2);
    ctx.lineCap = 'round';
    const nStr = opts.strands ?? 22;
    for (let i = 0; i < nStr; i++) {
      const u = (i + 0.5 + (rnd() - 0.5) * 0.6) / nStr;
      const h = hl[Math.min(hl.length - 1, Math.round(u * (hl.length - 1)))];
      // matching point on the top edge (edge runs right→left over the top)
      const e = topEdge[Math.min(topEdge.length - 1, Math.round((1 - u) * (topEdge.length - 1)))] || edge[0];
      const sx0 = h[0], sy0 = h[1] - 0.015;
      const ex = lerp(sx0, e[0], 0.88), ey = lerp(sy0, e[1], 0.88);
      const cx = lerp(sx0, ex, 0.5) + (facingRight ? -1 : 1) * 0.03, cy = lerp(sy0, ey, 0.5) - 0.05;
      const light = (i % 3) === 0;
      ctx.strokeStyle = rgba(light ? shade(ch.hair, 0.3) : shade(ch.hair, -0.3), 0.18 + rnd() * 0.1);
      ctx.lineWidth = 0.007 + rnd() * 0.004;
      ctx.beginPath(); ctx.moveTo(sx0, sy0); ctx.quadraticCurveTo(cx, cy, ex, ey); ctx.stroke();
    }
    const sg = ctx.createRadialGradient(-0.06 + k * 0.08, -0.5, 0, -0.06 + k * 0.08, -0.5, 0.22);
    sg.addColorStop(0, rgba(shade(ch.hair, 0.45), 0.3)); sg.addColorStop(1, rgba(shade(ch.hair, 0.45), 0));
    ctx.fillStyle = sg; ctx.fillRect(-0.4, -0.75, 0.8, 0.5);
    ctx.restore();
    // soft shadow the hair casts on the forehead
    ctx.save();
    ctx.beginPath(); R.smoothPath(ctx, outline); ctx.clip();
    ctx.strokeStyle = rgba(ch.skinShadow, 0.3); ctx.lineWidth = 0.03; ctx.lineJoin = 'round';
    ctx.beginPath(); R.poly(ctx, hl.map((p) => [p[0], p[1] + 0.012])); ctx.stroke();
    ctx.restore();
    ctx.beginPath(); R.smoothPath(ctx, shape);
    R.rimStroke(ctx, L, 0.018, 0.7);
    ctx.restore();
  };
}

// Long hair: back mass falling past the shoulders + front cap with side locks lying on the head.
function longHair(opts) {
  const front = shortHair({ ...opts, volume: opts.volume ?? 0.05, hairline: opts.hairline ?? -0.31, temple: 0.12 });
  return {
    hairBack(ctx, ch, k, pitch, L, st) {
      // falls behind the neck and shoulders, slightly wider than the head, tapering at the ends
      const len = opts.length ?? 1.25;
      const w = ch.headW / 2 + 0.05;
      const sway = Math.sin((st.t || 0) * 0.5) * 0.012;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(-w + k * 0.03, -0.3);
      ctx.bezierCurveTo(-w - 0.05, 0.25, -w - 0.1 + sway, len * 0.55, -w * 0.75 + sway * 2, len);
      ctx.quadraticCurveTo(k * 0.05 + sway * 2, len + 0.1, w * 0.75 + sway * 2, len);
      ctx.bezierCurveTo(w + 0.1 + sway, len * 0.55, w + 0.05, 0.25, w + k * 0.03, -0.3);
      ctx.quadraticCurveTo(0, -0.74, -w + k * 0.03, -0.3);
      const g = ctx.createLinearGradient(0, -0.6, 0, len);
      g.addColorStop(0, rgba(shade(ch.hair, -0.1))); g.addColorStop(1, rgba(shade(ch.hair, -0.35)));
      ctx.fillStyle = g; ctx.fill();
      ctx.save(); ctx.clip();
      const rnd = U.rng(opts.seed || 11);
      ctx.lineCap = 'round';
      for (let i = 0; i < 18; i++) {
        const x0 = lerp(-w, w, (i + 0.5) / 18);
        ctx.strokeStyle = rgba(i % 3 === 0 ? shade(ch.hair, 0.22) : shade(ch.hair, -0.45), 0.22);
        ctx.lineWidth = 0.008 + rnd() * 0.004;
        ctx.beginPath(); ctx.moveTo(x0 * 0.7, -0.35); ctx.bezierCurveTo(x0 * 1.05, 0.3, x0 * 1.1 + sway, len * 0.7, x0 * 0.8 + sway * 2, len);
        ctx.stroke();
      }
      ctx.restore();
      ctx.beginPath(); ctx.moveTo(-w + k * 0.03, -0.3);
      ctx.bezierCurveTo(-w - 0.05, 0.25, -w - 0.1 + sway, len * 0.55, -w * 0.75 + sway * 2, len);
      R.rimStroke(ctx, L, 0.02, 0.6);
      ctx.restore();
    },
    hairFront(ctx, ch, k, pitch, L, st, outline) {
      front(ctx, ch, k, pitch, L, st, outline);
      // side locks: attached at the temple, lying against the cheek/jaw contour (never floating over the ears)
      ctx.save();
      for (const sgn of [-1, 1]) {
        const vis = Math.cos(sgn * 1.2 + k * 0.62 * 1.6);
        const x0 = (sgn * (ch.headW / 2) * 0.98) + k * (sgn === Math.sign(k) ? 0.09 : 0.02);
        ctx.beginPath();
        ctx.moveTo(x0 - sgn * 0.06, -0.24);
        ctx.bezierCurveTo(x0 + sgn * 0.01, -0.05, x0 + sgn * 0.03, 0.2, x0 + sgn * 0.0, 0.42);
        ctx.lineTo(x0 + sgn * 0.065, 0.44);
        ctx.bezierCurveTo(x0 + sgn * 0.075, 0.2, x0 + sgn * 0.06, -0.08, x0 + sgn * 0.03, -0.26);
        ctx.closePath();
        ctx.fillStyle = rgba(shade(ch.hair, -0.05), clamp(0.35 + vis));
        ctx.fill();
        ctx.strokeStyle = rgba(shade(ch.hair, 0.25), 0.25); ctx.lineWidth = 0.006;
        ctx.beginPath(); ctx.moveTo(x0 - sgn * 0.02, -0.2); ctx.bezierCurveTo(x0 + sgn * 0.03, 0.0, x0 + sgn * 0.04, 0.2, x0 + sgn * 0.03, 0.4); ctx.stroke();
      }
      ctx.restore();
    },
  };
}

// ---- designs ---------------------------------------------------------------
const HUMAN = {
  name: 'human',
  skin: [205, 150, 116], skinShadow: [128, 78, 62], blush: [214, 110, 96], blushA: 0.16,
  lip: [172, 98, 88], iris: [104, 66, 38], lash: [44, 28, 22],
  hair: [64, 44, 34], brow: [58, 40, 32], grey: 0.45, greyColor: [170, 165, 160],
  headW: 0.74, jaw: 0.8, chinW: 0.3, eyeSize: 1.0, browThick: 1.15, noseSize: 1.08, mouthW: 1.05, lipFull: 0.9,
  stubble: 0.22, stubbleColor: [80, 62, 54],
  shoulderW: 0.86, neckW: 1.12, armW: 0.24,
  cloth: { base: [196, 132, 52], shadow: [112, 64, 26], collar: [170, 108, 40] }, // ochre knit sweater
  collar: 'knit', age: 0.2,
  torsoDetail(ctx, ch, shL, shR, bk) { // knit ribbing texture, very subtle
    ctx.strokeStyle = rgba(ch.cloth.shadow, 0.12); ctx.lineWidth = 0.012;
    for (let i = -6; i <= 6; i++) { ctx.beginPath(); ctx.moveTo(i * 0.13 + bk * 0.05, 0.3); ctx.lineTo(i * 0.14 + bk * 0.05, 2.6); ctx.stroke(); }
  },
};
HUMAN.hairFront = shortHair({ volume: 0.075, hairline: -0.31, seed: 3, wave: 0.016, recede: 0.03 });

const LAST_HUMAN = {
  ...HUMAN, name: 'last_human',
  skin: [196, 146, 118], skinShadow: [118, 76, 64], lip: [160, 104, 98], blushA: 0.08,
  hair: [196, 192, 186], brow: [170, 165, 158], grey: 0, stubble: 0.3, stubbleColor: [175, 170, 165],
  age: 0.95, jaw: 0.74, cloth: { base: [150, 110, 64], shadow: [86, 58, 30], collar: [126, 90, 50] }, collar: 'flight',
  blanket: [92, 98, 112],
  torsoDetail(ctx, ch, shL, shR, bk, L, st) {
    // grey wool blanket over the shoulders, draped with folds
    ctx.fillStyle = rgba(ch.blanket);
    ctx.beginPath();
    ctx.moveTo(shL[0] - 0.1, shL[1] + 0.05); ctx.quadraticCurveTo(-0.5, 0.05, -0.32 + bk * 0.05, 0.2);
    ctx.lineTo(-0.2 + bk * 0.05, 2.6); ctx.lineTo(-1.2, 2.6); ctx.closePath(); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(shR[0] + 0.1, shR[1] + 0.05); ctx.quadraticCurveTo(0.5, 0.05, 0.32 + bk * 0.05, 0.2);
    ctx.lineTo(0.2 + bk * 0.05, 2.6); ctx.lineTo(1.2, 2.6); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = rgba(shade(ch.blanket, -0.35), 0.45); ctx.lineWidth = 0.025;
    for (const sgn of [-1, 1]) for (let i = 0; i < 3; i++) {
      ctx.beginPath(); ctx.moveTo(sgn * (0.45 + i * 0.15), 0.35 + i * 0.1); ctx.quadraticCurveTo(sgn * (0.5 + i * 0.16), 1.2, sgn * (0.42 + i * 0.18), 2.4); ctx.stroke();
    }
  },
};
LAST_HUMAN.hairFront = shortHair({ volume: 0.045, hairline: -0.26, seed: 5, wave: 0.012, strands: 20, recede: 0.05 });

// The AI: a seated humanoid hologram of soft cyan light; androgynous, gentle.
const AI = {
  name: 'ai', holo: true,
  skin: [126, 206, 228], skinShadow: [38, 98, 140], blush: [170, 236, 255], blushA: 0.12,
  lip: [96, 168, 204], iris: [70, 210, 250], pupil: [12, 52, 86], eyeWhite: [206, 240, 250], eyeGlow: [120, 230, 255],
  lash: [24, 74, 108], hair: [92, 176, 214], brow: [60, 130, 170], lashes: true,
  headW: 0.7, jaw: 0.66, chinW: 0.26, eyeSize: 1.08, browThick: 0.85, noseSize: 0.85, mouthW: 0.95, lipFull: 0.9,
  shoulderW: 0.8, neckW: 1.0, armW: 0.21, waistW: 0.68,
  cloth: { base: [70, 150, 190], shadow: [24, 70, 110], collar: [120, 210, 240] }, collar: 'crew',
  handSkin: [140, 214, 234], handOutline: [36, 96, 136], mouthIn: [20, 60, 90], tongue: [70, 140, 180], teeth: [210, 245, 255],
  torsoDetail(ctx, ch, shL, shR, bk, L, st) {
    // circuitry-like seams of light on the garment
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = rgba([150, 240, 255], 0.07); ctx.lineWidth = 0.01;
    const t = st.t || 0;
    for (let i = 0; i < 5; i++) {
      const x = -0.5 + i * 0.25 + bk * 0.05;
      ctx.beginPath(); ctx.moveTo(x, 0.35); ctx.lineTo(x, 0.8 + (i % 2) * 0.2); ctx.lineTo(x + 0.08, 1.0 + (i % 2) * 0.2); ctx.lineTo(x + 0.08, 2.4); ctx.stroke();
      const py = 0.35 + ((t * 0.35 + i * 0.37) % 1) * 2.0;
      const g = ctx.createRadialGradient(x, py, 0, x, py, 0.08);
      g.addColorStop(0, rgba([200, 250, 255], 0.22)); g.addColorStop(1, rgba([200, 250, 255], 0));
      ctx.fillStyle = g; ctx.fillRect(x - 0.08, py - 0.08, 0.16, 0.16);
    }
    ctx.restore();
  },
  overlay(ctx, ch, st, geo) {
    // inner shimmer: a few slow motes of light rising through the figure
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    const t = st.t || 0;
    for (let i = 0; i < 5; i++) {
      const u = ((t * 0.05 + U.hash(i * 7)) % 1);
      const x = (U.hash(i * 13) - 0.5) * 1.3;
      const y = 2.2 - u * 3.2;
      const a = Math.sin(u * Math.PI) * 0.35;
      const g = ctx.createRadialGradient(x, y, 0, x, y, 0.035);
      g.addColorStop(0, rgba([220, 255, 255], a)); g.addColorStop(1, rgba([220, 255, 255], 0));
      ctx.fillStyle = g; ctx.fillRect(x - 0.04, y - 0.04, 0.08, 0.08);
    }
    ctx.restore();
  },
};
AI.hairFront = shortHair({ volume: 0.05, hairline: -0.33, seed: 9, wave: 0.008, strands: 16, part: 0.68 });

// Suffering: small, child-proportioned, dark plum skin, raw red cracks that later turn gold,
// jagged shards on the shoulders, big expressive eyes, a tattered cloak.
const SUFFERING = {
  name: 'suffering',
  prop: { head: 1.18, neck: 0.62, body: 0.72 },
  skin: [118, 84, 136], skinShadow: [62, 38, 80], blush: [180, 80, 120], blushA: 0.2,
  lip: [120, 60, 96], iris: [236, 168, 80], lash: [20, 10, 26], hair: [40, 26, 52], brow: [30, 18, 40], lashes: true,
  headW: 0.8, jaw: 0.76, chinW: 0.36, eyeSize: 1.4, irisScale: 1.15, browThick: 0.8, noseSize: 0.7, mouthW: 0.85, lipFull: 0.9,
  shoulderW: 0.62, neckW: 0.85, armW: 0.17, waistW: 0.55, handScale: 0.85,
  cloth: { base: [78, 56, 94], shadow: [36, 22, 48], collar: [60, 42, 76] }, collar: 'crew',
  mouthIn: [40, 14, 28],
  cracks: 0, // 0 = raw red, 1 = gold (meaning)
  faceDetail(ctx, ch, st, k) {
    const gold = st.cracks ?? 0;
    const col = mix([214, 48, 72], [255, 196, 90], gold);
    ctx.save();
    ctx.strokeStyle = rgba(col, 0.7); ctx.lineWidth = 0.008; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(0.22 + k * 0.05, -0.42); ctx.lineTo(0.17 + k * 0.05, -0.33); ctx.lineTo(0.2 + k * 0.05, -0.26); ctx.lineTo(0.15 + k * 0.05, -0.2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-0.27 + k * 0.05, 0.12); ctx.lineTo(-0.22 + k * 0.05, 0.2); ctx.lineTo(-0.25 + k * 0.05, 0.27); ctx.stroke();
    if (gold > 0.05) {
      ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba([255, 200, 110], 0.35 * gold); ctx.lineWidth = 0.02;
      ctx.beginPath(); ctx.moveTo(0.22 + k * 0.05, -0.42); ctx.lineTo(0.17 + k * 0.05, -0.33); ctx.lineTo(0.2 + k * 0.05, -0.26); ctx.stroke();
    }
    ctx.restore();
  },
  torsoDetail(ctx, ch, shL, shR, bk, L, st) {
    const gold = st.cracks ?? 0;
    const col = mix([214, 48, 72], [255, 196, 90], gold);
    ctx.strokeStyle = rgba(col, 0.6); ctx.lineWidth = 0.014; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(-0.2, 0.4); ctx.lineTo(-0.12, 0.62); ctx.lineTo(-0.18, 0.85); ctx.lineTo(-0.08, 1.1); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0.25, 0.5); ctx.lineTo(0.2, 0.7); ctx.lineTo(0.3, 0.9); ctx.stroke();
    // tattered cloak hem
    ctx.fillStyle = rgba(ch.cloth.shadow, 0.6);
    for (let i = 0; i < 7; i++) { ctx.beginPath(); ctx.moveTo(-0.7 + i * 0.22, 2.2); ctx.lineTo(-0.6 + i * 0.22, 2.5); ctx.lineTo(-0.5 + i * 0.22, 2.2); ctx.fill(); }
  },
  overlay(ctx, ch, st, geo) {
    // jagged shards jutting from the shoulders: sharp edges, cold highlights
    const s = st.shardScale ?? 1;
    ctx.save();
    for (const [sh, sgn] of [[geo.shL, -1], [geo.shR, 1]]) {
      const shards = [[0.0, -0.36, 0.06], [0.12, -0.26, 0.05], [-0.1, -0.22, 0.045]];
      for (const [dx, h, w] of shards) {
        const bx = sh[0] - sgn * 0.08 + dx * sgn, by = sh[1] + 0.02;
        ctx.beginPath(); ctx.moveTo(bx - w, by); ctx.lineTo(bx + sgn * 0.04, by + h * s); ctx.lineTo(bx + w, by); ctx.closePath();
        const g = ctx.createLinearGradient(bx - w, by, bx + w, by + h);
        g.addColorStop(0, rgba([70, 46, 96])); g.addColorStop(0.5, rgba([140, 110, 170])); g.addColorStop(1, rgba([46, 26, 64]));
        ctx.fillStyle = g; ctx.fill();
        ctx.strokeStyle = rgba([200, 180, 230], 0.5); ctx.lineWidth = 0.006; ctx.stroke();
      }
    }
    ctx.restore();
  },
};
SUFFERING.hairFront = shortHair({ volume: 0.07, hairline: -0.36, seed: 21, wave: 0.02, strands: 14 });

// Boredom: tall, lanky, slouched, ash-sage skin, heavy-lidded, long cardigan, messy fringe.
const BOREDOM = {
  name: 'boredom',
  prop: { head: 0.95, neck: 1.0, body: 1.0 },
  skin: [168, 176, 160], skinShadow: [96, 104, 92], blush: [190, 160, 150], blushA: 0.1,
  lip: [140, 126, 120], iris: [110, 130, 96], lash: [50, 54, 46], hair: [92, 86, 96], brow: [80, 76, 84],
  headW: 0.68, jaw: 0.7, chinW: 0.3, eyeSize: 0.95, browThick: 1.0, noseSize: 1.15, mouthW: 1.08, lipFull: 0.8,
  shoulderW: 0.8, neckW: 0.9, armW: 0.19, waistW: 0.7, reach: 1.1,
  cloth: { base: [128, 104, 132], shadow: [70, 54, 76], collar: [110, 88, 116] }, collar: 'vneck',
};
BOREDOM.hairFront = shortHair({ volume: 0.08, hairline: -0.26, seed: 33, wave: 0.03, strands: 22, part: 0.2 });

// Loneliness: slender, pale blue, gentle; long dark-blue hair; soft robe.
const LONELINESS = {
  name: 'loneliness',
  prop: { head: 0.97, neck: 0.95, body: 0.92 },
  skin: [176, 200, 230], skinShadow: [96, 120, 164], blush: [200, 170, 210], blushA: 0.12,
  lip: [140, 136, 180], iris: [70, 100, 160], lash: [30, 40, 70], hair: [44, 62, 110], brow: [40, 54, 96], lashes: true,
  headW: 0.69, jaw: 0.66, chinW: 0.26, eyeSize: 1.08, browThick: 0.8, noseSize: 0.85, mouthW: 0.92,
  shoulderW: 0.68, neckW: 0.85, armW: 0.17, waistW: 0.6,
  cloth: { base: [214, 226, 244], shadow: [140, 156, 190], collar: [196, 210, 236] }, collar: 'crew',
};
Object.assign(LONELINESS, longHair({ seed: 41, length: 1.45, hairline: -0.33 }));

// A gentle, non-human being from the far future (vignette use).
const ALIEN = {
  name: 'alien',
  skin: [150, 196, 170], skinShadow: [70, 120, 104], blush: [190, 220, 200], blushA: 0.1,
  lip: [110, 160, 140], iris: [40, 30, 80], lash: [30, 50, 50], hair: [80, 140, 120], brow: [80, 140, 120],
  headW: 0.78, jaw: 0.55, chinW: 0.2, eyeSize: 1.6, irisScale: 1.35, pupilScale: 0.6, browThick: 0.4, noseSize: 0.5, mouthW: 0.7,
  shoulderW: 0.6, neckW: 0.7, armW: 0.15, waistW: 0.5, earSize: 0.01,
  cloth: { base: [90, 110, 140], shadow: [40, 56, 80] }, collar: 'crew',
};

module.exports = { HUMAN, LAST_HUMAN, AI, SUFFERING, BOREDOM, LONELINESS, ALIEN, shortHair, longHair };
