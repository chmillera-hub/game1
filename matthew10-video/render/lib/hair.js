'use strict';
// Hairstyles. Each style returns point lists in head units; points are
// projected with an approximate depth so hair turns with the head, and the
// lower strands lag behind head motion (sway) for secondary animation.

const { clamp, lerp, col, shade, rgbStr, rng } = require('./util');
const { proj } = require('./face');

// Depth estimate for a hair point. Hair rotates as if on a cylinder at least as
// wide as the point itself, so strands at the silhouette never pop outward.
function hz(x, y, layer) {
  const r = Math.max(Math.abs(x), 0.52);
  const z = Math.sqrt(Math.max(0, r * r - x * x));
  const hang = clamp(1 - (y - 0.05) * 1.6, 0.25, 1); // hanging strands sit nearer the silhouette
  return layer === 'back' ? -z * 0.6 : z * 0.85 * hang;
}
function place(pts, R, layer, sway) {
  return pts.map(([x, y]) => {
    const hang = clamp((y + 0.15) / 0.9, 0, 1.4); // lower strands swing more
    const q = proj([x, y, hz(x, y, layer)], R);
    return [q[0] + sway.x * hang * 0.09, q[1] + sway.y * hang * 0.03];
  });
}
// Path through points where each segment bulges outward (curls / clumps).
function bumpy(ctx, pts, amount, closed = true, seed = 1) {
  const r = rng(seed);
  const n = pts.length;
  // Winding decides which side is "outward" (positive area = clockwise on screen).
  let area = 0;
  for (let i = 0; i < n; i++) {
    const a = pts[i], b = pts[(i + 1) % n];
    area += a[0] * b[1] - b[0] * a[1];
  }
  const sgn = area >= 0 ? 1 : -1;
  ctx.moveTo(pts[0][0], pts[0][1]);
  const segs = closed ? n : n - 1;
  for (let i = 0; i < segs; i++) {
    const a = pts[i], b = pts[(i + 1) % n];
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const k = amount * (0.7 + r() * 0.6) * sgn;
    ctx.quadraticCurveTo(mx + dy * k, my - dx * k, b[0], b[1]);
  }
  if (closed) ctx.closePath();
}
function smooth(ctx, pts, closed = true) {
  const n = pts.length;
  const get = (i) => (closed ? pts[(i + n) % n] : pts[Math.max(0, Math.min(n - 1, i))]);
  ctx.moveTo(pts[0][0], pts[0][1]);
  const last = closed ? n : n - 1;
  for (let i = 0; i < last; i++) {
    const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
    ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
      p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1]);
  }
  if (closed) ctx.closePath();
}
function sheen(ctx, A, pts, alpha = 0.35, width = 0.03) {
  ctx.save();
  ctx.strokeStyle = rgbStr(shade(A.hair, 0.3), alpha);
  ctx.lineWidth = width; ctx.lineCap = 'round';
  ctx.beginPath(); smooth(ctx, pts, false); ctx.stroke();
  ctx.restore();
}
function strands(ctx, A, list, R, layer, sway, alpha = 0.5, width = 0.008) {
  ctx.save();
  ctx.strokeStyle = rgbStr(shade(A.hair, -0.35), alpha);
  ctx.lineWidth = width; ctx.lineCap = 'round';
  for (const s of list) {
    const p = place(s, R, layer, sway);
    ctx.beginPath(); smooth(ctx, p, false); ctx.stroke();
  }
  ctx.restore();
}

// Small lighter arcs scattered over the hair mass so curls read at close range.
function curlTexture(ctx, A, R, sway) {
  const r = rng(42);
  ctx.save();
  ctx.lineCap = 'round';
  const spots = [[-0.5, -0.3], [-0.55, -0.02], [-0.52, 0.16], [-0.4, -0.52], [-0.18, -0.63], [0.06, -0.67], [0.28, -0.62],
    [0.46, -0.44], [0.54, -0.2], [0.55, 0.05], [0.53, 0.2], [-0.3, -0.6], [0.4, -0.56], [-0.46, -0.42], [0.5, -0.32]];
  for (const [x, y] of spots) {
    const p = place([[x + (r() - 0.5) * 0.04, y + (r() - 0.5) * 0.04]], R, 'front', sway)[0];
    const rad = 0.028 + r() * 0.018;
    const a0 = r() * Math.PI * 2;
    ctx.strokeStyle = rgbStr(shade(A.hair, 0.2), 0.22 + r() * 0.1);
    ctx.lineWidth = 0.009;
    ctx.beginPath(); ctx.arc(p[0], p[1], rad, a0, a0 + Math.PI * (0.55 + r() * 0.35)); ctx.stroke();
  }
  ctx.restore();
}

const STYLES = {
  // Maya: voluminous dark curls to the shoulders, soft side part.
  curls: {
    back(ctx, A, R, sway) {
      const base = [[0, -0.74], [0.36, -0.66], [0.58, -0.38], [0.66, -0.05], [0.66, 0.3], [0.6, 0.62], [0.42, 0.8],
        [0.2, 0.7], [-0.2, 0.7], [-0.42, 0.8], [-0.6, 0.62], [-0.66, 0.3], [-0.66, -0.05], [-0.58, -0.38], [-0.36, -0.66]];
      const p = place(base, R, 'back', sway);
      ctx.fillStyle = col(shade(A.hair, -0.12));
      ctx.beginPath(); bumpy(ctx, p, 0.28, true, 7); ctx.fill();
    },
    front(ctx, A, R, sway) {
      const L = [[0.07, -0.6], [-0.06, -0.47], [-0.25, -0.37], [-0.39, -0.2], [-0.45, 0.02], [-0.47, 0.22], [-0.53, 0.3],
        [-0.61, 0.12], [-0.63, -0.18], [-0.56, -0.47], [-0.36, -0.66], [0.05, -0.72]];
      const Rt = [[0.07, -0.6], [0.2, -0.47], [0.36, -0.3], [0.44, -0.08], [0.47, 0.18], [0.54, 0.26], [0.62, 0.08],
        [0.63, -0.22], [0.54, -0.5], [0.32, -0.68], [0.05, -0.72]];
      ctx.fillStyle = col(A.hair);
      for (const [pts, seed] of [[L, 3], [Rt, 5]]) {
        const p = place(pts, R, 'front', sway);
        ctx.beginPath(); bumpy(ctx, p, 0.16, true, seed); ctx.fill();
      }
      // curl texture
      strands(ctx, A, [
        [[-0.12, -0.6], [-0.3, -0.5], [-0.42, -0.3]], [[-0.5, -0.1], [-0.55, 0.05], [-0.5, 0.2]],
        [[0.2, -0.6], [0.38, -0.48], [0.5, -0.25]], [[0.52, -0.05], [0.56, 0.1], [0.52, 0.2]],
        [[-0.3, -0.64], [-0.46, -0.52]], [[0.0, -0.66], [0.14, -0.62]],
      ], R, 'front', sway, 0.45, 0.01);
      if (!A.hairShadowPass) {
        curlTexture(ctx, A, R, sway);
        sheen(ctx, A, place([[-0.38, -0.5], [-0.26, -0.6], [-0.12, -0.65]], R, 'front', sway), 0.1, 0.03);
        sheen(ctx, A, place([[0.16, -0.66], [0.3, -0.6], [0.4, -0.5]], R, 'front', sway), 0.08, 0.026);
      }
    },
  },
  // Mom: chin-length bob, side-swept fringe, a silver streak.
  bob: {
    back(ctx, A, R, sway) {
      const p = place([[0, -0.7], [0.4, -0.6], [0.56, -0.3], [0.58, 0.05], [0.56, 0.3], [0.62, 0.42], [0.42, 0.42],
        [0, 0.36], [-0.42, 0.42], [-0.62, 0.42], [-0.56, 0.3], [-0.58, 0.05], [-0.56, -0.3], [-0.4, -0.6]], R, 'back', sway);
      ctx.fillStyle = col(shade(A.hair, -0.15));
      ctx.beginPath(); smooth(ctx, p, true); ctx.fill();
    },
    front(ctx, A, R, sway) {
      const p = place([[-0.16, -0.62], [-0.02, -0.43], [0.18, -0.35], [0.36, -0.24], [0.45, -0.02], [0.47, 0.22],
        [0.52, 0.38], [0.6, 0.4], [0.6, 0.0], [0.56, -0.38], [0.36, -0.64], [0.0, -0.73], [-0.36, -0.66],
        [-0.55, -0.42], [-0.6, 0.0], [-0.6, 0.38], [-0.52, 0.38], [-0.46, 0.2], [-0.45, -0.12], [-0.37, -0.36]], R, 'front', sway);
      ctx.fillStyle = col(A.hair);
      ctx.beginPath(); smooth(ctx, p, true); ctx.fill();
      strands(ctx, A, [[[-0.12, -0.6], [0.1, -0.5], [0.34, -0.36], [0.46, -0.1]], [[-0.3, -0.62], [-0.48, -0.4], [-0.52, -0.05]],
        [[0.0, -0.66], [0.3, -0.56], [0.5, -0.3]]], R, 'front', sway, 0.4, 0.008);
      // silver streak
      ctx.save();
      ctx.strokeStyle = 'rgba(214,210,205,0.38)'; ctx.lineWidth = 0.024; ctx.lineCap = 'round';
      ctx.beginPath(); smooth(ctx, place([[-0.18, -0.64], [0.05, -0.52], [0.28, -0.42], [0.44, -0.2]], R, 'front', sway), false); ctx.stroke();
      ctx.restore();
      sheen(ctx, A, place([[-0.4, -0.5], [-0.15, -0.64], [0.15, -0.65], [0.38, -0.55]], R, 'front', sway), 0.3, 0.03);
    },
  },
  // Dad: short, greying, receding; the top of the head shows.
  receding: {
    noShadow: true,
    back(ctx, A, R, sway) {
      const p = place([[-0.47, -0.22], [-0.42, -0.5], [-0.2, -0.64], [0.2, -0.64], [0.42, -0.5], [0.47, -0.22],
        [0.47, 0.12], [0.4, 0.2], [-0.4, 0.2], [-0.47, 0.12]], R, 'back', sway);
      ctx.fillStyle = col(shade(A.hair, -0.1));
      ctx.beginPath(); smooth(ctx, p, true); ctx.fill();
    },
    front(ctx, A, R, sway) {
      ctx.fillStyle = col(A.hair);
      for (const s of [-1, 1]) {
        const p = place([[s * 0.36, -0.42], [s * 0.45, -0.3], [s * 0.47, -0.05], [s * 0.46, 0.08], [s * 0.42, 0.05],
          [s * 0.41, -0.15], [s * 0.38, -0.3]], R, 'front', sway);
        ctx.beginPath(); smooth(ctx, p, true); ctx.fill();
      }
      // close-cropped hair over the crown, thinning toward the front
      const crown = place([[-0.42, -0.36], [-0.36, -0.52], [-0.18, -0.6], [0.05, -0.62], [0.28, -0.58], [0.4, -0.48],
        [0.43, -0.36], [0.3, -0.46], [0.08, -0.52], [-0.15, -0.5], [-0.32, -0.44]], R, 'front', sway);
      ctx.save();
      ctx.fillStyle = rgbStr(A.hair, 0.5);
      ctx.beginPath(); smooth(ctx, crown, true); ctx.fill();
      ctx.restore();
    },
  },
  // Jordan: messy short dark hair with a fringe.
  messy: {
    back(ctx, A, R, sway) {
      const p = place([[0, -0.7], [0.4, -0.6], [0.52, -0.3], [0.5, 0.05], [0.42, 0.18], [-0.42, 0.18], [-0.5, 0.05],
        [-0.52, -0.3], [-0.4, -0.6]], R, 'back', sway);
      ctx.fillStyle = col(shade(A.hair, -0.15));
      ctx.beginPath(); bumpy(ctx, p, 0.12, true, 11); ctx.fill();
    },
    front(ctx, A, R, sway) {
      const p = place([[-0.47, -0.08], [-0.42, -0.28], [-0.27, -0.3], [-0.12, -0.27], [0.04, -0.31], [0.2, -0.27],
        [0.36, -0.3], [0.47, -0.12], [0.53, -0.32], [0.48, -0.55], [0.3, -0.7], [0.0, -0.76], [-0.3, -0.7],
        [-0.5, -0.55], [-0.53, -0.3]], R, 'front', sway);
      ctx.fillStyle = col(A.hair);
      ctx.beginPath(); bumpy(ctx, p, 0.2, true, 13); ctx.fill();
      strands(ctx, A, [[[-0.2, -0.66], [-0.1, -0.5], [-0.15, -0.32]], [[0.15, -0.68], [0.18, -0.5], [0.1, -0.33]],
        [[0.35, -0.6], [0.4, -0.45], [0.36, -0.3]]], R, 'front', sway, 0.5, 0.009);
      sheen(ctx, A, place([[-0.3, -0.6], [0.0, -0.69], [0.28, -0.62]], R, 'front', sway), 0.25, 0.03);
    },
  },
  // Greg: neat side part with a combed quiff.
  neat: {
    back(ctx, A, R, sway) {
      const p = place([[0, -0.68], [0.4, -0.58], [0.5, -0.3], [0.49, 0.02], [0.42, 0.12], [-0.42, 0.12], [-0.49, 0.02],
        [-0.5, -0.3], [-0.4, -0.58]], R, 'back', sway);
      ctx.fillStyle = col(shade(A.hair, -0.18));
      ctx.beginPath(); smooth(ctx, p, true); ctx.fill();
    },
    front(ctx, A, R, sway) {
      const p = place([[-0.46, -0.08], [-0.45, -0.32], [-0.28, -0.38], [-0.06, -0.42], [0.16, -0.44], [0.34, -0.38],
        [0.45, -0.24], [0.47, -0.06], [0.5, -0.3], [0.48, -0.56], [0.3, -0.74], [0.0, -0.8], [-0.24, -0.75],
        [-0.42, -0.62], [-0.5, -0.4]], R, 'front', sway);
      ctx.fillStyle = col(A.hair);
      ctx.beginPath(); smooth(ctx, p, true); ctx.fill();
      strands(ctx, A, [[[-0.22, -0.7], [0.0, -0.62], [0.25, -0.5], [0.42, -0.3]], [[-0.3, -0.62], [-0.05, -0.52], [0.2, -0.44]]],
        R, 'front', sway, 0.35, 0.008);
      sheen(ctx, A, place([[-0.15, -0.74], [0.1, -0.7], [0.3, -0.6]], R, 'front', sway), 0.35, 0.03);
    },
  },
  // Priya: sleek centre part, pulled back (braid is drawn with the body).
  sleek: {
    back(ctx, A, R, sway) {
      const p = place([[0, -0.68], [0.42, -0.58], [0.54, -0.25], [0.52, 0.2], [0.44, 0.5], [0.2, 0.55], [-0.2, 0.55],
        [-0.44, 0.5], [-0.52, 0.2], [-0.54, -0.25], [-0.42, -0.58]], R, 'back', sway);
      ctx.fillStyle = col(shade(A.hair, -0.15));
      ctx.beginPath(); smooth(ctx, p, true); ctx.fill();
    },
    front(ctx, A, R, sway) {
      ctx.fillStyle = col(A.hair);
      for (const s of [-1, 1]) {
        const p = place([[0, -0.62], [s * 0.18, -0.48], [s * 0.36, -0.3], [s * 0.44, -0.05], [s * 0.45, 0.12],
          [s * 0.53, 0.05], [s * 0.55, -0.3], [s * 0.42, -0.6], [s * 0.15, -0.72], [0, -0.73]], R, 'front', sway);
        ctx.beginPath(); smooth(ctx, p, true); ctx.fill();
      }
      sheen(ctx, A, place([[-0.38, -0.5], [-0.18, -0.64], [0.0, -0.68]], R, 'front', sway), 0.3, 0.03);
      sheen(ctx, A, place([[0.05, -0.68], [0.25, -0.62], [0.4, -0.45]], R, 'front', sway), 0.22, 0.025);
    },
  },
};

module.exports = { STYLES, place, smooth, bumpy };
