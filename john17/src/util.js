// Shared helpers: seeded randomness, easing, colour maths and SVG path builders.
(function () {
  const U = {};

  U.rng = function (seed) {
    let a = (seed * 2654435761) >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  U.clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  U.lerp = (a, b, t) => a + (b - a) * t;
  U.smooth = (t) => { t = U.clamp(t); return t * t * (3 - 2 * t); };
  U.easeInOut = (t) => { t = U.clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  U.easeOut = (t) => 1 - Math.pow(1 - U.clamp(t), 3);
  U.ramp = (t, a, b) => U.smooth((t - a) / (b - a));

  // Smooth 1-D value noise in [-1, 1], used for idle sway and flicker.
  U.noise = function (t, seed = 0) {
    const i = Math.floor(t), f = t - i;
    const h = (n) => { const x = Math.sin((n + seed * 131.7) * 127.1) * 43758.5453; return (x - Math.floor(x)) * 2 - 1; };
    const s = f * f * (3 - 2 * f);
    return h(i) * (1 - s) + h(i + 1) * s;
  };

  U.hex = function (h) {
    h = h.replace('#', '');
    if (h.length === 3) h = h.split('').map((c) => c + c).join('');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  };
  U.toHex = (c) => '#' + c.map((v) => Math.round(U.clamp(v, 0, 255)).toString(16).padStart(2, '0')).join('');
  U.mix = (a, b, t) => { const A = U.hex(a), B = U.hex(b); return U.toHex(A.map((v, i) => v + (B[i] - v) * t)); };
  U.shade = (c, amt) => (amt >= 0 ? U.mix(c, '#ffffff', amt) : U.mix(c, '#000000', -amt));

  const f = (n) => (Math.round(n * 10) / 10).toString();
  U.f = f;

  // Catmull-Rom spline through points -> cubic Bezier path.
  U.spline = function (pts, closed = false, tension = 0.5) {
    if (pts.length < 2) return '';
    const P = closed ? [pts[pts.length - 1], ...pts, pts[0], pts[1]] : [pts[0], ...pts, pts[pts.length - 1]];
    let d = `M${f(P[1][0])},${f(P[1][1])}`;
    const n = closed ? pts.length : pts.length - 1;
    for (let i = 1; i <= n; i++) {
      const p0 = P[i - 1], p1 = P[i], p2 = P[i + 1], p3 = P[i + 2];
      const k = tension / 3;
      const c1 = [p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k];
      const c2 = [p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k];
      d += `C${f(c1[0])},${f(c1[1])} ${f(c2[0])},${f(c2[1])} ${f(p2[0])},${f(p2[1])}`;
    }
    return closed ? d + 'Z' : d;
  };

  // Sample a polyline densely (for hair/beard edges).
  U.resample = function (pts, step) {
    const out = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      const [x0, y0] = pts[i - 1], [x1, y1] = pts[i];
      const len = Math.hypot(x1 - x0, y1 - y0), n = Math.max(1, Math.round(len / step));
      for (let k = 1; k <= n; k++) out.push([x0 + ((x1 - x0) * k) / n, y0 + ((y1 - y0) * k) / n]);
    }
    return out;
  };

  // Hairy / tufted edge: pushes alternate samples outward along the normal.
  U.tufts = function (pts, amp, step, seed, sharp = 0.6) {
    const r = U.rng(seed);
    const s = U.resample(pts, step);
    const out = [];
    for (let i = 0; i < s.length; i++) {
      const a = s[Math.max(0, i - 1)], b = s[Math.min(s.length - 1, i + 1)];
      let nx = b[1] - a[1], ny = -(b[0] - a[0]);
      const L = Math.hypot(nx, ny) || 1; nx /= L; ny /= L;
      const k = i % 2 === 0 ? amp * (0.55 + r() * 0.9) : -amp * sharp * r() * 0.5;
      out.push([s[i][0] + nx * k, s[i][1] + ny * k]);
    }
    return out;
  };

  // Polyline path (straight segments) for jagged tufts.
  U.poly = (pts, closed) => 'M' + pts.map((p) => `${f(p[0])},${f(p[1])}`).join('L') + (closed ? 'Z' : '');

  U.mirror = (pts) => pts.map(([x, y]) => [-x, y]);

  // Natural blinking: returns 0..1 (1 = fully closed) at time t for a given character seed.
  U.blink = function (t, seed) {
    const r = U.rng(seed * 7 + 1);
    let bt = r() * 2;
    while (bt < t + 1) {
      const d = t - bt;
      if (d >= 0 && d < 0.2) return d < 0.07 ? d / 0.07 : U.clamp(1 - (d - 0.07) / 0.13);
      bt += 2.4 + r() * 3.4;
    }
    return 0;
  };

  // Linear/radial gradient helpers for SVG defs.
  U.lg = function (id, stops, x1 = 0, y1 = 0, x2 = 0, y2 = 1, extra = '') {
    return `<linearGradient id="${id}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" ${extra}>` +
      stops.map(([o, c, a]) => `<stop offset="${o}" stop-color="${c}"${a !== undefined ? ` stop-opacity="${a}"` : ''}/>`).join('') + '</linearGradient>';
  };
  U.rg = function (id, stops, cx = 0.5, cy = 0.5, r = 0.5, extra = '') {
    return `<radialGradient id="${id}" cx="${cx}" cy="${cy}" r="${r}" ${extra}>` +
      stops.map(([o, c, a]) => `<stop offset="${o}" stop-color="${c}"${a !== undefined ? ` stop-opacity="${a}"` : ''}/>`).join('') + '</radialGradient>';
  };

  // Escape for text inserted into SVG/HTML.
  U.esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  window.U = U;
})();
