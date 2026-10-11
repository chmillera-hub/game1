// Shared facial rig. Every character face is drawn with drawFace(g, style, expr) in HEAD-LOCAL
// coordinates: (0,0) is the face centre, +y is down. The caller translates/rotates/scales first.
//
// EXPRESSION PARAMETERS (all optional; see DEFAULT_EXPR):
//   lookX, lookY   -1..1   gaze direction (eyes move independently of the head)
//   lidU           -0.4..1 upper lid closure (0 = relaxed open, 1 = closed, negative = shocked-wide)
//   lidL           0..1    lower lid raise (smile cheeks, squint, suspicion)
//   lidTilt        -1..1   + = sad droop (outer corners low), - = angry/determined (inner corners low)
//   blink          0..1    extra closure added on top of lidU (use autoBlink())
//   browUp         -1..1   both brows up/down;  browUpL / browUpR for asymmetric offsets
//   browIn         -1..1   + = inner ends raised (worried, sad, pleading), - = inner ends down (angry, stern)
//   browSquish     0..1    brows pulled together (concern, effort)
//   open           0..1    jaw open (speech / gasp)
//   wide           -1..1   mouth corners stretched (+) or pinched (-)
//   round          0..1    "oo"/"o" rounding
//   smile          -1..1   corners up (+) / down (-)
//   tremble        0..1    trembling lips (needs expr.t)
//   pressed        0..1    lips pressed tight (holding back tears / resolve)
//   teeth          0..1    show upper teeth when open
//   pupil          scale   pupil size (0.6 terror ... 1.4 wonder)
//   iris           scale   iris size multiplier
//   tears          0..1    tears welling along the lower lids (glossy)
//   tearL, tearR   0..1    progress of a tear drop running down that cheek (0 = none, 0.01..1 = falling)
//   stream         0..1    wet tear-streak opacity down both cheeks (wide wet body + specular edge; reads after compression)
//   blush          0..1
//   sparkle        0..1    starry reflections in the eyes (wonder)
//   sweat          0..1    a nervous sweat drop
//   turn           -1..1   head yaw: features slide toward the turned side, far eye narrows
//   t              seconds (drives tremble / sparkle animation)

import { clamp, lerp, TAU, noise1, rgba, shade, ellipse, circle } from './engine.mjs';

export const DEFAULT_EXPR = {
  lookX: 0, lookY: 0, lidU: 0, lidL: 0, lidTilt: 0, blink: 0,
  browUp: 0, browUpL: 0, browUpR: 0, browIn: 0, browSquish: 0,
  open: 0, wide: 0, round: 0, smile: 0, tremble: 0, pressed: 0, teeth: 0,
  pupil: 1, iris: 1, tears: 0, tearL: 0, tearR: 0, stream: 0, blush: 0, sparkle: 0, sweat: 0,
  turn: 0, t: 0,
};

/** Named starting points. Combine with mix() or spread overrides: {...EXPR.worried, lookX: .4} */
export const EXPR = {
  neutral: {},
  calm: { lidU: 0.12, smile: 0.1 },
  smile: { smile: 0.7, lidL: 0.35, browUp: 0.15, blush: 0.2 },
  softSmile: { smile: 0.4, lidL: 0.2, lidU: 0.1, browIn: 0.15 },
  beaming: { smile: 1, open: 0.3, teeth: 0.8, lidL: 0.55, browUp: 0.35, blush: 0.35 },
  worried: { browIn: 0.8, browUp: 0.2, lidTilt: 0.35, smile: -0.25, lidU: 0.05 },
  scared: { browIn: 0.9, browUp: 0.6, lidU: -0.25, pupil: 0.7, smile: -0.4, wide: 0.25, open: 0.1 },
  terrified: { browIn: 1, browUp: 0.9, lidU: -0.4, pupil: 0.55, smile: -0.6, open: 0.45, wide: 0.5, teeth: 0.5, tremble: 0.6 },
  sad: { browIn: 0.85, lidTilt: 0.7, lidU: 0.3, smile: -0.55, lookY: 0.35 },
  crying: { browIn: 1, browUp: 0.3, lidTilt: 0.8, lidU: 0.35, lidL: 0.35, smile: -0.8, open: 0.25, wide: 0.35, tremble: 0.8, tears: 1, stream: 0.7 },
  holdingBackTears: { browIn: 0.9, lidTilt: 0.6, lidU: 0.25, pressed: 0.8, smile: -0.35, tremble: 0.35, tears: 0.6 },
  stern: { browIn: -0.6, browSquish: 0.5, lidTilt: -0.3, lidU: 0.15, pressed: 0.4, smile: -0.15 },
  determined: { browIn: -0.35, browSquish: 0.3, lidTilt: -0.15, lidU: 0.1, smile: -0.05 },
  tender: { browIn: 0.45, lidU: 0.2, lidL: 0.15, smile: 0.3, lidTilt: 0.25 },
  surprised: { browUp: 0.8, lidU: -0.3, open: 0.4, round: 0.6, pupil: 0.85 },
  wonder: { browUp: 0.55, browIn: 0.35, lidU: -0.15, open: 0.28, round: 0.45, pupil: 1.35, sparkle: 1 },
  confused: { browUpL: 0.6, browUpR: -0.2, browIn: 0.2, smile: -0.2, wide: -0.2, lookX: 0.3, lookY: -0.2 },
  tired: { lidU: 0.45, lidTilt: 0.3, browIn: 0.25, smile: -0.1 },
  suspicious: { lidU: 0.35, lidL: 0.3, browUpL: -0.3, browUpR: 0.3, smile: -0.15, wide: -0.2 },
};

// device px per local unit (current transform)
function devScale(g) {
  const m = g.getTransform();
  return Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)) || 1;
}

export function makeExpr(...parts) {
  return Object.assign({}, DEFAULT_EXPR, ...parts);
}

/**
 * FACE STYLE fields (per character):
 *  eyeSpacing, eyeY, eyeRx, eyeRy, eyeShape ('round'|'almond'), white, irisColor, irisColor2,
 *  pupilColor, irisR (fraction of eyeRx), skin (lid colour), line (outline/lash colour), lineW,
 *  lash (0..1 lash-line thickness), restLid (0..1 resting upper lid), browY, browLen, browThick, browColor,
 *  browArch, mouthY, mouthW, mouthColor, tongue, teethColor, lipLine, blushColor, blushX, blushY,
 *  blushR, nose (fn(g, expr) or null), mouthLine (thickness)
 */
export function drawFace(g, style, exprIn) {
  const e = { ...DEFAULT_EXPR, ...exprIn };
  const s = style;
  if (globalThis.__FACE_LOG) logFace(g, s);
  const turn = clamp(e.turn, -1, 1);
  const shiftX = turn * s.eyeSpacing * 0.55;

  // blush first (under features)
  if (e.blush > 0.01 && s.blushColor) {
    for (const side of [-1, 1]) {
      const far = side * turn > 0 ? 1 - Math.abs(turn) * 0.45 : 1;
      const bx = side * (s.blushX ?? s.eyeSpacing * 1.05) * (1 - Math.abs(turn) * 0.25) + shiftX;
      const r = (s.blushR ?? s.eyeRx * 0.9);
      const gr = g.createRadialGradient(bx, s.blushY ?? s.eyeY + s.eyeRy * 1.4, 0, bx, s.blushY ?? s.eyeY + s.eyeRy * 1.4, r * far);
      gr.addColorStop(0, rgba(s.blushColor, 0.55 * e.blush));
      gr.addColorStop(1, rgba(s.blushColor, 0));
      g.fillStyle = gr;
      ellipse(g, bx, s.blushY ?? s.eyeY + s.eyeRy * 1.4, r * far, r * 0.62);
      g.fill();
    }
  }

  // tear streaks (under eyes, over skin). Built to survive the compressed film (4:2:0 chroma + quantisation
  // used to erase a thin translucent blue line): a wide wet body that brightens the skin, a soft darker fringe
  // on the shadow side, and a crisp near-white specular edge on the light (upper-left) side, so the streak
  // reads in LUMA, not only as a tint. Opacity rises a little faster than `stream` at the low end.
  if (e.stream > 0.01) {
    const sa = Math.pow(clamp(e.stream), 0.8);
    const k = devScale(g);
    const bw = Math.max(3, s.eyeRx * 0.24);                       // body width (1.5× the old streak)
    const sw = Math.max(1 / k, bw * 0.2);                         // specular edge: ≥ 1 device px
    g.save();
    g.lineCap = 'round'; g.lineJoin = 'round';
    // the streak ends on the cheek, never much below the mouth line: on big-eyed round heads (Fear) the old
    // 2.1·eyeRy run reached past the jaw outline and hung in the air beside the head (very visible once the
    // streak got its bright edge). Faces whose run already ends above that (Self) are unchanged.
    const y0 = s.eyeY + s.eyeRy * 0.85;
    const len0 = s.mouthY != null ? clamp(s.mouthY + s.eyeRy * 0.3 - y0, s.eyeRy, s.eyeRy * 2.1) : s.eyeRy * 2.1;
    for (const side of [-1, 1]) {
      const ex = side * s.eyeSpacing * (1 - Math.abs(turn) * 0.3) + shiftX;
      const x0 = ex + side * s.eyeRx * 0.35;
      // the features slide toward the side the head turns to, so the jaw is closer there: shorter run
      const len = len0 * (1 - 0.3 * Math.max(0, side * turn));
      const path = (dx) => {
        g.beginPath();
        g.moveTo(x0 + dx, y0);
        g.bezierCurveTo(x0 + dx + side * 3, y0 + len * 0.381, x0 + dx - side * 2, y0 + len * 0.667, x0 + dx + side * 2, y0 + len);
      };
      // each layer thins out toward the tail (the trail dries / runs off the cheek)
      const y1 = y0 + len;
      const fade = (rgb, a) => {
        const gr = g.createLinearGradient(0, y0, 0, y1);
        gr.addColorStop(0, `rgba(${rgb},${a})`); gr.addColorStop(0.68, `rgba(${rgb},${a})`);
        gr.addColorStop(1, `rgba(${rgb},${a * 0.25})`);
        return gr;
      };
      // shadow-side fringe (a hair of refraction shadow gives the wet line an edge on pale skin)
      g.strokeStyle = fade('70,95,150', 0.16 * sa);
      g.lineWidth = bw * 0.45;
      path(bw * 0.42); g.stroke();
      // the wet body
      g.strokeStyle = fade('200,232,255', 0.62 * sa);
      g.lineWidth = bw;
      path(0); g.stroke();
      // specular edge
      g.strokeStyle = fade('255,255,255', 0.88 * sa);
      g.lineWidth = sw;
      path(-(bw - sw) * 0.36); g.stroke();
    }
    g.restore();
  }

  // eyes
  for (const side of [-1, 1]) {
    const farSide = side * turn > 0; // eye on the side the head turns toward rotates toward the silhouette edge and foreshortens
    const squeeze = farSide ? 1 - Math.abs(turn) * 0.38 : 1 + Math.abs(turn) * 0.06;
    const ex = side * s.eyeSpacing * (1 - Math.abs(turn) * 0.3) + shiftX;
    drawEye(g, s, e, ex, s.eyeY, s.eyeRx * squeeze, s.eyeRy, side);
  }

  // brows
  for (const side of [-1, 1]) {
    const farSide = side * turn > 0;
    const squeeze = farSide ? 1 - Math.abs(turn) * 0.35 : 1;
    const bx = side * s.eyeSpacing * (1 - Math.abs(turn) * 0.3) + shiftX;
    drawBrow(g, s, e, bx, side, squeeze);
  }

  if (s.nose) s.nose(g, e, shiftX);

  drawMouth(g, s, e, turn * s.eyeSpacing * 0.45);

  if (e.sweat > 0.01) {
    const sx = -s.eyeSpacing * 1.45 + shiftX, sy = s.eyeY - s.eyeRy * 0.8 + e.sweat * 6;
    g.fillStyle = `rgba(200,235,255,${0.85 * clamp(e.sweat * 2)})`;
    g.strokeStyle = rgba(s.line, 0.5 * clamp(e.sweat * 2));
    g.lineWidth = 1.5;
    g.beginPath();
    g.moveTo(sx, sy - 9);
    g.quadraticCurveTo(sx + 6, sy + 2, sx, sy + 5);
    g.quadraticCurveTo(sx - 6, sy + 2, sx, sy - 9);
    g.fill(); g.stroke();
  }
}

function eyePath(g, s, cx, cy, rx, ry, side) {
  if (s.eyeShape === 'almond') {
    // almond: pointed outer corner, rounder inner corner
    const inner = -side, outer = side;
    g.beginPath();
    g.moveTo(cx + outer * rx, cy - ry * 0.12);
    g.bezierCurveTo(cx + outer * rx * 0.55, cy - ry * 1.05, cx + inner * rx * 0.6, cy - ry * 1.08, cx + inner * rx, cy - ry * 0.05);
    g.bezierCurveTo(cx + inner * rx * 0.75, cy + ry * 0.95, cx + outer * rx * 0.55, cy + ry * 0.9, cx + outer * rx, cy - ry * 0.12);
    g.closePath();
  } else {
    ellipse(g, cx, cy, rx, ry);
  }
}

// y of the eye's top/bottom boundary at horizontal offset dx (approximate for both shapes)
const boundary = (rx, ry, dx, top) => {
  const k = clamp(1 - (dx * dx) / (rx * rx), 0, 1);
  return (top ? -1 : 1) * ry * Math.sqrt(k);
};

function drawEye(g, s, e, cx, cy, rx, ry, side) {
  const rest = s.restLid ?? 0.08;
  let up = clamp(rest + e.lidU * (e.lidU < 0 ? 0.3 : 1) + e.blink * (1 - (rest + e.lidU)), -0.25, 1);
  if (e.lidU < 0) up = clamp(rest + e.lidU * 0.3 + e.blink * (1 - rest), -0.25, 1);
  const low = clamp(e.lidL, 0, 1) * (1 - clamp(up, 0, 1) * 0.5);
  const closed = up > 0.97;
  const lineW = s.lineW ?? 2.5;

  if (!closed) {
    g.save();
    eyePath(g, s, cx, cy, rx, ry, side);
    g.fillStyle = s.white || '#fbfaff';
    g.fill();
    g.clip();

    // iris + pupil
    const irisR = rx * (s.irisR ?? 0.6) * (e.iris ?? 1);
    const ix = cx + clamp(e.lookX, -1, 1) * rx * 0.42;
    const iy = cy + clamp(e.lookY, -1, 1) * ry * 0.36 + ry * 0.04;
    const gi = g.createRadialGradient(ix, iy - irisR * 0.4, irisR * 0.1, ix, iy, irisR);
    gi.addColorStop(0, s.irisColor2 || shade(s.irisColor, 0.25));
    gi.addColorStop(1, s.irisColor);
    g.fillStyle = gi;
    circle(g, ix, iy, irisR);
    g.fill();
    g.fillStyle = s.pupilColor || '#1a1020';
    circle(g, ix, iy, irisR * 0.52 * e.pupil);
    g.fill();
    // cosmic sparkle reflections
    if (e.sparkle > 0.01) {
      const tt = e.t || 0;
      for (let i = 0; i < 7; i++) {
        const a = i * 2.4 + tt * 0.25;
        const rr = irisR * (0.25 + 0.6 * ((i * 37) % 10) / 10);
        const px = ix + Math.cos(a) * rr, py = iy + Math.sin(a) * rr;
        const tw = 0.5 + 0.5 * Math.sin(tt * (2 + i * 0.7) + i);
        const col = ['#ffffff', '#ffe9a8', '#a8e1ff', '#ffb3e6'][i % 4];
        g.fillStyle = rgba(col, e.sparkle * (0.45 + 0.55 * tw));
        star(g, px, py, irisR * (0.07 + 0.06 * tw));
      }
      const gn = g.createRadialGradient(ix + irisR * 0.2, iy + irisR * 0.3, 0, ix, iy, irisR);
      gn.addColorStop(0, `rgba(160,120,255,${0.35 * e.sparkle})`);
      gn.addColorStop(1, 'rgba(160,120,255,0)');
      g.fillStyle = gn;
      circle(g, ix, iy, irisR);
      g.fill();
    }
    // highlights
    g.fillStyle = 'rgba(255,255,255,0.95)';
    circle(g, ix - irisR * 0.38, iy - irisR * 0.42, irisR * 0.3);
    g.fill();
    g.fillStyle = 'rgba(255,255,255,0.75)';
    circle(g, ix + irisR * 0.35, iy + irisR * 0.32, irisR * 0.13);
    g.fill();

    // tears welling: glossy band on lower lid
    if (e.tears > 0.01) {
      const gt = g.createLinearGradient(0, cy + ry * 0.2, 0, cy + ry);
      gt.addColorStop(0, 'rgba(200,235,255,0)');
      gt.addColorStop(1, `rgba(190,230,255,${0.75 * e.tears})`);
      g.fillStyle = gt;
      g.fillRect(cx - rx, cy, rx * 2, ry);
      g.fillStyle = `rgba(255,255,255,${0.8 * e.tears})`;
      ellipse(g, cx + side * rx * 0.1, cy + ry * 0.68, rx * 0.5, ry * 0.07);
      g.fill();
    }

    // upper lid
    const tilt = e.lidTilt;
    const lidEdge = (dx) => {
      const top = boundary(rx, ry, dx, true) - ry * 0.05;
      const closedY = ry * 0.3 + (dx * dx) / (rx * rx) * ry * -0.1;
      const k = clamp(up, -0.25, 1);
      let y = lerp(top, closedY, Math.max(0, k)) + (k < 0 ? k * ry * 0.35 : 0);
      // tilt: + sad (outer low), - angry (inner low). dx*side > 0 means outer.
      const outerness = (dx * side) / rx; // -1 inner .. +1 outer
      y += tilt * outerness * ry * 0.38 * Math.min(1, Math.max(0, k) + 0.6);
      return y;
    };
    g.fillStyle = s.skin;
    g.beginPath();
    g.moveTo(cx - rx - 2, cy - ry - 4);
    const N = 14;
    for (let i = 0; i <= N; i++) {
      const dx = -rx - 1 + (2 * rx + 2) * (i / N);
      g.lineTo(cx + dx, cy + lidEdge(dx));
    }
    g.lineTo(cx + rx + 2, cy - ry - 4);
    g.closePath();
    g.fill();
    // lash line
    g.strokeStyle = s.line;
    g.lineWidth = lineW * (1 + (s.lash ?? 0.6) * 1.2);
    g.lineCap = 'round';
    g.beginPath();
    for (let i = 0; i <= N; i++) {
      const dx = -rx * 0.98 + (2 * rx * 0.98) * (i / N);
      const y = cy + lidEdge(dx);
      if (i === 0) g.moveTo(cx + dx, y); else g.lineTo(cx + dx, y);
    }
    g.stroke();

    // lower lid
    if (low > 0.01) {
      const lowEdge = (dx) => {
        const bot = boundary(rx, ry, dx, false) + ry * 0.05;
        return lerp(bot, -ry * 0.05 + (dx * dx) / (rx * rx) * ry * 0.25, low * 0.75);
      };
      g.fillStyle = s.skin;
      g.beginPath();
      g.moveTo(cx - rx - 2, cy + ry + 4);
      for (let i = 0; i <= N; i++) {
        const dx = -rx - 1 + (2 * rx + 2) * (i / N);
        g.lineTo(cx + dx, cy + lowEdge(dx));
      }
      g.lineTo(cx + rx + 2, cy + ry + 4);
      g.closePath();
      g.fill();
      g.strokeStyle = rgba(s.line, 0.6);
      g.lineWidth = lineW * 0.8;
      g.beginPath();
      for (let i = 2; i <= N - 2; i++) {
        const dx = -rx + (2 * rx) * (i / N);
        const y = cy + lowEdge(dx);
        if (i === 2) g.moveTo(cx + dx, y); else g.lineTo(cx + dx, y);
      }
      g.stroke();
    }
    g.restore();

    // outline
    g.strokeStyle = rgba(s.line, s.eyeOutline ?? 0.9);
    g.lineWidth = lineW;
    eyePath(g, s, cx, cy, rx, ry, side);
    g.stroke();
  } else {
    // closed eye: curved lash line; happy-closed if lower lid raised
    g.strokeStyle = s.line;
    g.lineWidth = lineW * 1.6;
    g.lineCap = 'round';
    const tilt = e.lidTilt;
    const happy = e.lidL > 0.4 || e.smile > 0.6;
    g.beginPath();
    const yo = happy ? -ry * 0.05 : ry * 0.25;
    const curve = happy ? -ry * 0.45 : ry * 0.25; // happy = upward arch, otherwise gentle downward
    g.moveTo(cx - rx * 0.92, cy + yo + tilt * -side * ry * 0.3);
    g.quadraticCurveTo(cx, cy + yo + curve, cx + rx * 0.92, cy + yo + tilt * side * ry * 0.3);
    g.stroke();
  }

  // falling tear drop
  const prog = side < 0 ? e.tearL : e.tearR;
  if (prog > 0.001) {
    const k = clamp(prog);
    const tx = cx + side * rx * 0.45 + Math.sin(k * 5) * 2;
    const ty = cy + ry * 0.9 + k * ry * 2.6;
    const a = k < 0.85 ? 1 : 1 - (k - 0.85) / 0.15;
    const sz = rx * 0.17 * (0.7 + 0.5 * Math.min(1, k * 4));
    g.save();
    g.fillStyle = `rgba(212,240,255,${0.95 * a})`;
    g.strokeStyle = `rgba(110,160,215,${0.75 * a})`;
    g.lineWidth = 1.2;
    g.beginPath();
    g.moveTo(tx, ty - sz * 1.9);
    g.bezierCurveTo(tx + sz * 1.1, ty - sz * 0.2, tx + sz, ty + sz, tx, ty + sz);
    g.bezierCurveTo(tx - sz, ty + sz, tx - sz * 1.1, ty - sz * 0.2, tx, ty - sz * 1.9);
    g.fill(); g.stroke();
    // bright rim on the light (left) side, just inside the outline: the drop reads as glass in luma
    g.strokeStyle = `rgba(255,255,255,${0.85 * a})`;
    g.lineWidth = Math.max(1 / devScale(g), sz * 0.16);
    g.lineCap = 'round';
    g.beginPath();
    g.moveTo(tx - sz * 0.12, ty - sz * 1.45);
    g.bezierCurveTo(tx - sz * 0.75, ty - sz * 0.3, tx - sz * 0.82, ty + sz * 0.45, tx - sz * 0.3, ty + sz * 0.78);
    g.stroke();
    g.fillStyle = `rgba(255,255,255,${0.95 * a})`;
    circle(g, tx - sz * 0.35, ty, sz * 0.3);
    g.fill();
    g.restore();
  }
}

function drawBrow(g, s, e, bx, side, squeeze) {
  const up = e.browUp + (side < 0 ? e.browUpL : e.browUpR);
  const len = (s.browLen ?? s.eyeRx * 1.1) * squeeze;
  const by = s.browY ?? s.eyeY - s.eyeRy * 1.45;
  const lift = s.eyeRy * 0.45;
  const innerX = bx - side * len * 0.55 + side * e.browSquish * len * -0.12;
  const outerX = bx + side * len * 0.6;
  const innerY = by - up * lift - e.browIn * lift * 0.85 + e.browSquish * lift * 0.15;
  const outerY = by - up * lift * 0.8 + e.browIn * lift * 0.35;
  const arch = (s.browArch ?? 0.35) * lift * (1 - Math.max(0, e.browIn) * 0.6);
  const midX = (innerX + outerX) / 2, midY = (innerY + outerY) / 2 - arch;
  const th = s.browThick ?? 5;
  // tapered: draw as filled shape
  g.fillStyle = s.browColor || s.line;
  g.beginPath();
  g.moveTo(innerX, innerY - th * 0.55);
  g.quadraticCurveTo(midX, midY - th * 0.6, outerX, outerY - th * 0.15);
  g.quadraticCurveTo(outerX + side * th * 0.3, outerY + th * 0.1, outerX, outerY + th * 0.2);
  g.quadraticCurveTo(midX, midY + th * 0.55, innerX, innerY + th * 0.55);
  g.quadraticCurveTo(innerX - side * th * 0.4, innerY, innerX, innerY - th * 0.55);
  g.closePath();
  g.fill();
}

function drawMouth(g, s, e, mx) {
  const t = e.t || 0;
  const W0 = s.mouthW ?? 20;
  const my = s.mouthY ?? 30;
  const pressed = clamp(e.pressed);
  const open = clamp(e.open) * (1 - pressed * 0.9);
  const round = clamp(e.round);
  const smile = clamp(e.smile, -1, 1);
  let hw = W0 * (1 + 0.32 * e.wide - 0.42 * round + 0.12 * Math.abs(smile)) * (1 - pressed * 0.12);
  const cornerY = -smile * W0 * 0.32;
  const h = W0 * 1.3 * open * (1 + 0.35 * round);
  const trem = (k) => (e.tremble > 0 ? noise1(t * 14 + k * 3.1, 7) * e.tremble * W0 * 0.07 : 0);
  const lineCol = s.lipLine || s.line;
  const lw = s.mouthLine ?? (s.lineW ?? 2.5) * 1.15;

  g.save();
  g.translate(mx, my);
  if (h < 1.6) {
    // closed mouth line, polyline for tremble
    const dip = smile * W0 * 0.42;
    g.strokeStyle = lineCol;
    g.lineWidth = lw * (1 + pressed * 0.35);
    g.lineCap = 'round';
    g.beginPath();
    const N = 10;
    for (let i = 0; i <= N; i++) {
      const u = i / N;
      const x = lerp(-hw, hw, u);
      const bell = 1 - Math.pow(2 * u - 1, 2);
      const y = cornerY * (1 - bell) + (dip + cornerY) * bell * 0.5 + trem(i) + (pressed ? 0 : 0);
      if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
    }
    g.stroke();
    if (pressed > 0.3) {
      // small corner tucks
      g.lineWidth = lw * 0.7;
      for (const sd of [-1, 1]) {
        g.beginPath();
        g.moveTo(sd * hw, cornerY);
        g.lineTo(sd * (hw + 3), cornerY + 2.5);
        g.stroke();
      }
    }
  } else {
    const dip = smile * W0 * 0.5;
    const topY = -h * 0.28 + Math.max(0, smile) * W0 * 0.05 - round * h * 0.15;
    const botY = h * 0.72 + Math.max(0, smile) * W0 * 0.25 + dip * 0.2;
    const hwc = hw * (1 - round * 0.15);
    const path = () => {
      g.beginPath();
      g.moveTo(-hwc, cornerY + trem(1));
      g.bezierCurveTo(-hwc * 0.6, topY + trem(2), hwc * 0.6, topY + trem(3), hwc, cornerY + trem(4));
      g.bezierCurveTo(hwc * (0.75 - round * 0.2), botY + trem(5), -hwc * (0.75 - round * 0.2), botY + trem(6), -hwc, cornerY + trem(1));
      g.closePath();
    };
    path();
    g.fillStyle = s.mouthColor || '#4a1830';
    g.fill();
    g.save();
    path();
    g.clip();
    // tongue
    g.fillStyle = s.tongue || '#e07080';
    ellipse(g, 0, botY + h * 0.05, hwc * 0.62, h * 0.38);
    g.fill();
    // teeth
    if (e.teeth > 0.01) {
      g.fillStyle = s.teethColor || '#ffffff';
      g.globalAlpha = clamp(e.teeth);
      g.fillRect(-hwc, topY - 4, hwc * 2, Math.min(h * 0.28, W0 * 0.32) + 4);
      g.globalAlpha = 1;
    }
    g.restore();
    g.strokeStyle = lineCol;
    g.lineWidth = lw;
    g.lineJoin = 'round';
    path();
    g.stroke();
  }
  g.restore();
}

export function star(g, x, y, r) {
  g.beginPath();
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * TAU - Math.PI / 2;
    const rr = i % 2 === 0 ? r : r * 0.35;
    const px = x + Math.cos(a) * rr, py = y + Math.sin(a) * rr;
    if (i === 0) g.moveTo(px, py); else g.lineTo(px, py);
  }
  g.closePath();
  g.fill();
}

/**
 * Merge a lip-sync frame {open, wide, round} into an expression, keeping emotional mouth shape.
 * amount 0..1 scales the speech motion (e.g. 0.6 for a whisper).
 */
export function withSpeech(expr, lip, amount = 1) {
  if (!lip) return expr;
  return {
    ...expr,
    open: clamp((expr.open || 0) * 0.4 + lip.open * amount),
    wide: (expr.wide || 0) * 0.6 + (lip.wide || 0) * 0.5 * amount,
    round: clamp((expr.round || 0) * 0.5 + (lip.round || 0) * amount),
    pressed: (expr.pressed || 0) * (1 - clamp(lip.open * 3)),
  };
}

/** Record this face's screen-space box (used by `render.mjs --place-subs` so captions avoid faces).
 *  Only faces drawn onto a canvas registered in globalThis.__FACE_CANVASES (the frame, not offscreen caches). */
function logFace(g, s) {
  if (globalThis.__FACE_CANVASES && !globalThis.__FACE_CANVASES.has(g.canvas)) return;
  if (g.globalAlpha < 0.35) return;
  const hw = s.eyeSpacing + s.eyeRx * 1.35;
  const y0 = (s.browY ?? s.eyeY - s.eyeRy * 1.45) - s.eyeRy * 0.5;
  const y1 = (s.mouthY ?? 30) + (s.mouthW ?? 20) * 1.1;
  const m = g.getTransform();
  const pts = [[-hw, y0], [hw, y0], [-hw, y1], [hw, y1]].map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f]);
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  globalThis.__FACE_LOG.push({ x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys) });
}
