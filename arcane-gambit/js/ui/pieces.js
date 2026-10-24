/* Piece figurines, after Chess Evolved Online: every unit is a small statue
   on a pedestal, white for your side and black for the enemy, ink-outlined
   and cel-shaded, with coloured flares at the base for rarity.

   Each figure is drawn once into an SVG <symbol>; board tokens, cards and
   chips all <use> it. Colours come from custom properties set on the outer
   <svg class="pc"> (see .pc in style.css), so one drawing serves both sides
   and every glow. Inline styles carry the var() references because class
   rules do not reach into a <use> clone.

   Art files register drawings: AG.Art.pieces[id] = function (P, D) { ... }.
   P is a pen that collects shapes; D builds path data. The box is 100×100:
   the pedestal stands on y≈96 and the figure rises above it. Light comes
   from the upper left, so P.solid shades the right-hand side. */
(function (AG) {
  'use strict';
  const UI = (AG.UI = AG.UI || {});
  const Art = (AG.Art = AG.Art || {});
  const pieces = (Art.pieces = Art.pieces || {});
  Art.alias = Art.alias || {};
  const NS = 'http://www.w3.org/2000/svg';
  const r1 = (v) => Math.round(v * 10) / 10;
  const pt = (x, y) => r1(x) + ',' + r1(y);

  // ------------------------------------------------------------ path data
  // Every helper writes absolute M/L/C/Z commands with "x,y" pairs, so the
  // transforms at the end (mirror, shift, scale) work on any of them.
  const D = (Art.D = {});

  // Smooth curve through points (Catmull-Rom as cubic Béziers). A point
  // written [x, y, 1] is a sharp corner. k < 1 tightens the curve.
  D.curve = function (pts, closed, k) {
    k = k == null ? 1 : k;
    const n = pts.length;
    const at = (i) => (closed ? pts[(i + n) % n] : pts[Math.max(0, Math.min(n - 1, i))]);
    let d = 'M' + pt(pts[0][0], pts[0][1]);
    const segs = closed ? n : n - 1;
    for (let i = 0; i < segs; i++) {
      const p0 = at(i - 1), p1 = at(i), p2 = at(i + 1), p3 = at(i + 2);
      const s1 = p1[2] ? 0 : k / 6, s2 = p2[2] ? 0 : k / 6;
      d += 'C' + pt(p1[0] + (p2[0] - p0[0]) * s1, p1[1] + (p2[1] - p0[1]) * s1) + ' ' +
        pt(p2[0] - (p3[0] - p1[0]) * s2, p2[1] - (p3[1] - p1[1]) * s2) + ' ' + pt(p2[0], p2[1]);
    }
    return closed ? d + 'Z' : d;
  };
  // A symmetric outline from its left half, like a piece turned on a lathe:
  // points run from the top of the centre line, down the left side, to the
  // bottom of the centre line (x = 50 at both ends).
  D.lathe = function (half, k) {
    const right = half.slice(1, -1).reverse().map((p) => [100 - p[0], p[1], p[2]]);
    return D.curve(half.concat(right), true, k);
  };
  D.poly = (pts) => 'M' + pts.map((p) => pt(p[0], p[1])).join('L') + 'Z';
  D.line = (pts) => 'M' + pts.map((p) => pt(p[0], p[1])).join('L');
  D.ellipse = function (cx, cy, rx, ry) {
    const k = 0.5523;
    return 'M' + pt(cx - rx, cy) +
      'C' + pt(cx - rx, cy - ry * k) + ' ' + pt(cx - rx * k, cy - ry) + ' ' + pt(cx, cy - ry) +
      'C' + pt(cx + rx * k, cy - ry) + ' ' + pt(cx + rx, cy - ry * k) + ' ' + pt(cx + rx, cy) +
      'C' + pt(cx + rx, cy + ry * k) + ' ' + pt(cx + rx * k, cy + ry) + ' ' + pt(cx, cy + ry) +
      'C' + pt(cx - rx * k, cy + ry) + ' ' + pt(cx - rx, cy + ry * k) + ' ' + pt(cx - rx, cy) + 'Z';
  };
  D.circle = (cx, cy, r) => D.ellipse(cx, cy, r, r);
  D.rect = (x, y, w, h) => D.poly([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]);
  // Points along an elliptical arc, angles in degrees (0 = right, 90 = down).
  D.arcPts = function (cx, cy, rx, ry, a0, a1, steps) {
    steps = steps || Math.max(3, Math.ceil(Math.abs(a1 - a0) / 15));
    const out = [];
    for (let i = 0; i <= steps; i++) {
      const a = (a0 + (a1 - a0) * i / steps) * Math.PI / 180;
      out.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]);
    }
    return out;
  };
  D.regular = function (cx, cy, r, n, rot) {
    const pts = [];
    rot = rot == null ? -90 : rot;
    for (let i = 0; i < n; i++) {
      const a = (rot + i * 360 / n) * Math.PI / 180;
      pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
    }
    return D.poly(pts);
  };
  D.star = function (cx, cy, ro, ri, n, rot) {
    const pts = [];
    rot = rot == null ? -90 : rot;
    for (let i = 0; i < n * 2; i++) {
      const a = (rot + i * 180 / n) * Math.PI / 180, r = i % 2 ? ri : ro;
      pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
    }
    return D.poly(pts);
  };
  // A flame standing on (cx, yb): a round belly, a tall curling tip and a
  // smaller tongue each side. lean shifts the tip sideways.
  D.flame = function (cx, yb, w, hgt, lean) {
    lean = lean || 0;
    return D.curve([
      [cx + lean, yb - hgt, 1],
      [cx + w * 0.06 + lean * 0.7, yb - hgt * 0.8],
      [cx + w * 0.2 + lean * 0.3, yb - hgt * 0.6],
      [cx + w * 0.26, yb - hgt * 0.52],
      [cx + w * 0.42 + lean * 0.15, yb - hgt * 0.64, 1],
      [cx + w * 0.48, yb - hgt * 0.4],
      [cx + w * 0.44, yb - hgt * 0.16],
      [cx + w * 0.24, yb - hgt * 0.02],
      [cx, yb],
      [cx - w * 0.26, yb - hgt * 0.03],
      [cx - w * 0.46, yb - hgt * 0.18],
      [cx - w * 0.5, yb - hgt * 0.42],
      [cx - w * 0.42 + lean * 0.15, yb - hgt * 0.56, 1],
      [cx - w * 0.28, yb - hgt * 0.47],
      [cx - w * 0.18 + lean * 0.3, yb - hgt * 0.58],
      [cx - w * 0.1 + lean * 0.7, yb - hgt * 0.78],
    ], true, 1);
  };
  // A lightning bolt from (x0, y0) down to (x1, y1), w wide.
  D.bolt = function (x0, y0, x1, y1, w) {
    const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy), nx = -dy / L, ny = dx / L;
    const at = (t, s) => [x0 + dx * t + nx * w * s, y0 + dy * t + ny * w * s];
    return D.poly([at(0, -0.5), at(0, 0.5), at(0.42, 0.05), at(0.4, 0.62), at(1, 0), at(0.58, -0.05), at(0.6, -0.62)]);
  };
  // A drop hanging from its point at (cx, y0).
  D.drop = (cx, y0, w, hgt) => D.curve([[cx, y0, 1], [cx + w * 0.3, y0 + hgt * 0.42], [cx + w * 0.5, y0 + hgt * 0.72],
    [cx, y0 + hgt], [cx - w * 0.5, y0 + hgt * 0.72], [cx - w * 0.3, y0 + hgt * 0.42]], true);
  // A leaf from its stem at (x0, y0) to its tip at (x1, y1).
  D.leaf = function (x0, y0, x1, y1, w) {
    const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy), nx = -dy / L * w, ny = dx / L * w;
    return D.curve([[x0, y0, 1], [x0 + dx * 0.35 + nx * 0.5, y0 + dy * 0.35 + ny * 0.5], [x1, y1, 1],
      [x0 + dx * 0.35 - nx * 0.5, y0 + dy * 0.35 - ny * 0.5]], true);
  };
  // A cog: n teeth round a wheel of radius r (teeth reach r + t).
  D.gear = function (cx, cy, r, t, n) {
    const pts = [];
    for (let i = 0; i < n; i++) {
      const a = i * 360 / n - 90, s = 360 / n;
      for (const [da, rr] of [[-s * 0.5, r], [-s * 0.22, r], [-s * 0.14, r + t], [s * 0.14, r + t], [s * 0.22, r]]) {
        const q = (a + da) * Math.PI / 180;
        pts.push([cx + Math.cos(q) * rr, cy + Math.sin(q) * rr]);
      }
    }
    return D.poly(pts);
  };
  // A sword or knife blade from the hilt at (x0, y0) to the point (x1, y1).
  D.blade = function (x0, y0, x1, y1, w) {
    const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy), nx = -dy / L * w / 2, ny = dx / L * w / 2;
    return D.poly([[x0 + nx, y0 + ny], [x0 + dx * 0.82 + nx, y0 + dy * 0.82 + ny], [x1, y1],
      [x0 + dx * 0.82 - nx, y0 + dy * 0.82 - ny], [x0 - nx, y0 - ny]]);
  };
  // A feathered wing reaching left from the shoulder at (x0, y0): the
  // leading edge sweeps up to the tip, n feathers step back underneath.
  D.featherWing = function (x0, y0, span, hgt, n) {
    n = n || 4;
    const pts = [[x0, y0, 1], [x0 - span * 0.45, y0 - hgt * 0.5], [x0 - span, y0 - hgt * 0.62, 1]];
    for (let i = 0; i < n; i++) {
      const t = (i + 1) / n;
      const tipX = x0 - span * (1 - t * 0.78), tipY = y0 - hgt * 0.62 + hgt * (0.55 + t * 0.4);
      pts.push([tipX + span * 0.1 / n, tipY - hgt * 0.22]);
      pts.push([tipX, tipY, 1]);
    }
    pts.push([x0 - span * 0.12, y0 + hgt * 0.12]);
    return D.curve(pts, true, 0.9);
  };
  // A bat's wing reaching left from (x0, y0): fingers to the tip, with the
  // membrane scalloped between them.
  D.batWing = function (x0, y0, span, hgt, n) {
    n = n || 3;
    const tip = [x0 - span, y0 - hgt * 0.35, 1];
    const pts = [[x0, y0 - hgt * 0.12, 1], [x0 - span * 0.5, y0 - hgt * 0.62], tip];
    for (let i = 1; i <= n; i++) {
      const t = i / n;
      const fx = x0 - span * (1 - t * 0.85), fy = y0 - hgt * 0.35 + hgt * (0.55 + 0.1 * t);
      const prev = pts[pts.length - 1];
      pts.push([(prev[0] + fx) / 2, (prev[1] + fy) / 2 - hgt * 0.18]);
      pts.push([fx, fy, 1]);
    }
    pts.push([x0 - span * 0.06, y0 + hgt * 0.12]);
    return D.curve(pts, true, 0.9);
  };
  // A moon: a disc with a bite taken out toward angle ang (degrees).
  // bite is how far the biting disc sits from the centre, as a fraction of r
  // (0.4 leaves a thin sliver, 1.2 a fat crescent).
  D.crescent = function (cx, cy, r, bite, ang) {
    const deg = ang || 0, a = deg * Math.PI / 180;
    const bx = cx + Math.cos(a) * r * bite, by = cy + Math.sin(a) * r * bite;
    // The two discs cross at ±span from the line between their centres.
    const span = Math.acos(Math.min(1, bite / 2)) * 180 / Math.PI;
    const outer = D.arcPts(cx, cy, r, r, deg + span, deg + 360 - span, 24);
    const inner = D.arcPts(bx, by, r, r, deg + 180 + span, deg + 180 - span, 16).slice(1, -1);
    outer[0] = [outer[0][0], outer[0][1], 1];
    outer[outer.length - 1] = [outer[outer.length - 1][0], outer[outer.length - 1][1], 1];
    return D.curve(outer.concat(inner), true);
  };
  D.mx = (d) => d.replace(/(-?\d*\.?\d+),(-?\d*\.?\d+)/g, (m, x, y) => r1(100 - +x) + ',' + y);
  D.shift = (d, dx, dy) => d.replace(/(-?\d*\.?\d+),(-?\d*\.?\d+)/g, (m, x, y) => pt(+x + dx, +y + dy));
  D.scale = (d, s, ox, oy) => d.replace(/(-?\d*\.?\d+),(-?\d*\.?\d+)/g,
    (m, x, y) => pt(ox + (+x - ox) * s, oy + (+y - oy) * s));
  D.bbox = function (d) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    d.replace(/(-?\d*\.?\d+),(-?\d*\.?\d+)/g, (m, x, y) => {
      x = +x; y = +y;
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      return m;
    });
    return { x0, y0, x1, y1, w: x1 - x0, h: y1 - y0 };
  };

  // ------------------------------------------------------------------ pen
  const LINE = ';stroke-linejoin:round;stroke-linecap:round';
  const ST = {
    b: 'fill:var(--pb)', // body
    s: 'fill:var(--ps)', // shade
    d: 'fill:var(--pd)', // deep shade
    h: 'fill:var(--ph)', // rim light
    i: 'fill:var(--pk)', // ink
    e: 'fill:var(--pe)', // contrast detail (eyes, runes): dark on white, light on black
    a: 'fill:var(--pa)', // accent: ink, or the rarity colour when the piece glows
    k: 'fill:none;stroke:var(--pk);stroke-width:var(--psw)' + LINE, // outline
    l: 'fill:none;stroke:var(--pk);stroke-width:var(--plw);opacity:var(--pdet,1)' + LINE, // detail line
    el: 'fill:none;stroke:var(--pe);stroke-width:var(--plw);opacity:var(--pdet,1)' + LINE,
    al: 'fill:none;stroke:var(--pa);stroke-width:var(--plw)' + LINE,
    f: 'fill:none;stroke:var(--pg);stroke-width:2.4;opacity:var(--pon)' + LINE, // flare
    fa: 'fill:var(--pg);opacity:calc(var(--pon) * .2)', // flare haze
  };

  function Pen(id) { this.id = id; this.parts = []; this.n = 0; }
  Pen.prototype.uid = function () { return this.id + '-' + (++this.n); };
  Pen.prototype.path = function (d, cls, extra) {
    this.parts.push('<path style="' + ST[cls] + '"' + (extra || '') + ' d="' + d + '"/>');
    return this;
  };
  Pen.prototype.raw = function (s) { this.parts.push(s); return this; };
  Pen.prototype.ink = function (d) { return this.path(d, 'i'); };
  Pen.prototype.eye = function (d) { return this.path(d, 'e'); };
  Pen.prototype.acc = function (d) { return this.path(d, 'a'); };
  Pen.prototype.hi = function (d) { return this.path(d, 'h'); };
  Pen.prototype.line = function (d) { return this.path(d, 'l'); };
  Pen.prototype.heavy = function (d) { return this.path(d, 'k'); };
  Pen.prototype.eyeLine = function (d) { return this.path(d, 'el'); };
  Pen.prototype.accLine = function (d) { return this.path(d, 'al'); };
  // Filled and outlined, without shading: small parts, flat trims.
  Pen.prototype.flat = function (d, fill) { return this.path(d, fill || 'b').path(d, 'k'); };
  /* A solid: filled, cel-shaded beyond a curved terminator on the right,
     rim-lit on the left (visible on black pieces), then outlined.
     o.light: fraction of the width that is lit (0.6); o.fill: 'b' | 's' |
     'd' for the base tone; o.shade / o.rim: false to leave them out. */
  Pen.prototype.solid = function (d, o) {
    o = o || {};
    const fill = o.fill || 'b';
    this.path(d, fill);
    const bb = D.bbox(d);
    const R = Math.max(bb.w, bb.h) * 1.7;
    const shade = o.shade !== false && fill === 'b';
    const rim = o.rim !== false;
    if (shade || rim) {
      const id = this.uid();
      this.parts.push('<clipPath id="' + id + '"><path d="' + d + '"/></clipPath>');
      const clip = ' clip-path="url(#' + id + ')"';
      if (shade) {
        const xt = bb.x0 + bb.w * (o.light == null ? 0.6 : o.light);
        this.path(D.circle(xt + R, bb.y0 + bb.h * 0.3, R), 's', clip);
      }
      if (rim) {
        const xr = bb.x0 + Math.max(1.2, bb.w * 0.09);
        const hole = D.circle(xr + R, bb.y0 + bb.h * 0.45, R);
        const frame = D.rect(bb.x0 - 2, bb.y0 - 2, bb.w + 4, bb.h + 4);
        this.path(frame + hole, 'h', clip + ' fill-rule="evenodd"');
      }
    }
    if (o.line !== false) this.path(d, 'k');
    return this;
  };
  // A shaded sphere with a glint.
  Pen.prototype.ball = function (cx, cy, r, o) {
    this.solid(D.circle(cx, cy, r), o);
    return this.path(D.ellipse(cx - r * 0.38, cy - r * 0.42, r * 0.2, r * 0.13), 'h');
  };
  // Draw a shape and its mirror image across the centre line.
  Pen.prototype.pair = function (d, method, o) {
    this[method || 'solid'](d, o);
    this[method || 'solid'](D.mx(d), o);
    return this;
  };
  // A disc seen from slightly above: a curved front band with an oval top.
  Pen.prototype.tier = function (cx, y, rx, ry, hgt) {
    const c = ry * 4 / 3;
    this.solid('M' + pt(cx - rx, y) + 'L' + pt(cx - rx, y + hgt) +
      'C' + pt(cx - rx, y + hgt + c) + ' ' + pt(cx + rx, y + hgt + c) + ' ' + pt(cx + rx, y + hgt) +
      'L' + pt(cx + rx, y) + 'Z', { light: 0.64 });
    return this.solid(D.ellipse(cx, y, rx, ry), { shade: false });
  };
  // A narrowing column from yTop down to yBot, like the stem of a chess piece.
  Pen.prototype.column = function (cx, yTop, yBot, wTop, wBot, o) {
    const t = wTop / 2, b = wBot / 2, m = (yTop + yBot) / 2;
    const pinch = (o && o.pinch) || 0;
    return this.solid(D.curve([
      [cx - t, yTop, 1], [cx + t, yTop, 1],
      [cx + (t + b) / 2 - pinch, m], [cx + b, yBot, 1], [cx - b, yBot, 1], [cx - (t + b) / 2 + pinch, m],
    ], true, 0.8), o);
  };
  // A flattened ring around a stem (the collar under a chess piece's head).
  Pen.prototype.collar = function (cx, y, rx, ry) {
    return this.tier(cx, y - ry * 0.6, rx, ry, ry * 0.8);
  };
  // Rarity flares: wisps rising round the base, shown only when the piece glows.
  Pen.prototype.flares = function (rx) {
    rx = rx || 31;
    this.path(D.ellipse(50, 92, rx + 10, 8.5), 'fa');
    const x = 50 - rx;
    const wisps = [
      'M' + pt(x + 3, 93) + 'C' + pt(x - 6, 90) + ' ' + pt(x - 10, 84) + ' ' + pt(x - 10, 74),
      'M' + pt(x + 9, 88) + 'C' + pt(x + 4, 82) + ' ' + pt(x + 3, 75) + ' ' + pt(x + 6, 65),
      'M' + pt(x - 2, 96) + 'C' + pt(x - 10, 96) + ' ' + pt(x - 15, 93) + ' ' + pt(x - 18, 87),
      'M' + pt(x + 15, 85) + 'C' + pt(x + 13, 80) + ' ' + pt(x + 14, 75) + ' ' + pt(x + 17, 70),
    ];
    for (const w of wisps) { this.path(w, 'f'); this.path(D.mx(w), 'f'); }
    return this;
  };
  /* The pedestal, flares included. kind: 'std' (two tiers, the figure
     stands at y≈79), 'low' (one tier, y≈85, for summons and small fry),
     'wide' (big units, y≈78), 'dish' (a saucer for blobs, y≈88), 'none'. */
  Pen.prototype.base = function (kind) {
    kind = kind || 'std';
    if (kind === 'none') return this.flares(26);
    if (kind === 'low') return this.flares(26).tier(50, 86, 25, 4.6, 5);
    if (kind === 'dish') return this.flares(34).tier(50, 88.5, 35, 5, 3.5);
    if (kind === 'wide') return this.flares(40).tier(50, 85, 40, 6, 6).tier(50, 78.5, 29, 4.6, 5);
    return this.flares(31).tier(50, 85, 31, 5.6, 6).tier(50, 79, 21, 4, 4.6);
  };
  // A skull centred on (cx, cy), s = 1 for a head about 22 wide.
  Pen.prototype.skull = function (cx, cy, s) {
    s = s || 1;
    const q = (x, y) => [r1(cx + x * s), r1(cy + y * s)];
    this.solid(D.curve([q(0, -12), q(9, -10), q(11.5, -2), q(10, 5), q(6.5, 7.5, 1), q(6, 12), q(2, 13.5),
      q(-2, 13.5), q(-6, 12), q(-6.5, 7.5, 1), q(-10, 5), q(-11.5, -2), q(-9, -10)], true), { light: 0.62 });
    this.ink(D.ellipse(cx - 4.6 * s, cy + 0.5 * s, 3.4 * s, 3.8 * s));
    this.ink(D.ellipse(cx + 4.6 * s, cy + 0.5 * s, 3.4 * s, 3.8 * s));
    this.ink(D.poly([q(0, 4.5), q(1.6, 8), q(-1.6, 8)]));
    return this.line('M' + q(-3.5, 10.5).join(',') + 'L' + q(-3.5, 13.2).join(',') + 'M' + q(0, 11).join(',') + 'L' +
      q(0, 13.6).join(',') + 'M' + q(3.5, 10.5).join(',') + 'L' + q(3.5, 13.2).join(','));
  };
  Pen.prototype.out = function () { return this.parts.join(''); };
  Art.Pen = Pen;

  // A plain pawn with a question mark: shown for any unit without its own art.
  pieces._fallback = function (P) {
    P.base('std');
    P.column(50, 46, 79, 12, 26);
    P.collar(50, 47, 15, 3.4);
    P.ball(50, 32, 14);
    P.eyeLine('M45.5,28.5C45.5,23.5 54.5,23.5 54.5,28.5C54.5,32 50,32 50,35.5');
    P.eye(D.circle(50, 39.5, 1.6));
  };

  // --------------------------------------------------------- rendering
  Art.artId = function (u) {
    const id = (u && typeof u === 'object' ? u.art || u.def : u) || '_fallback';
    if (pieces[id]) return id;
    if (Art.alias[id] && pieces[Art.alias[id]]) return Art.alias[id];
    return '_fallback';
  };
  // Rarity glow: blue for uncommon, purple for rare, red for the enemy's
  // big hitters and gold for bosses.
  Art.glowFor = function (def) {
    const d = AG.Units[def];
    if (!d) return '';
    if (d.boss) return 'g-gold';
    if (d.pool === 'player') return d.rarity === 'rare' ? 'g-purple' : d.rarity === 'uncommon' ? 'g-blue' : '';
    if (d.pool === 'enemy' && d.big) return 'g-red';
    return '';
  };

  let sprite = null;
  const built = Object.create(null);
  function symbolFor(id) {
    if (built[id]) return 'pc-' + id;
    if (!sprite) {
      sprite = document.createElementNS(NS, 'svg');
      sprite.setAttribute('aria-hidden', 'true');
      sprite.setAttribute('width', '0');
      sprite.setAttribute('height', '0');
      sprite.style.position = 'absolute';
      sprite.style.overflow = 'hidden';
      document.body.appendChild(sprite);
    }
    let P = new Pen('pc-' + id);
    try { pieces[id](P, D); } catch (e) {
      if (globalThis.console) console.error('piece art ' + id + ': ' + e.message);
      P = new Pen('pc-' + id);
      pieces._fallback(P, D);
    }
    const sym = document.createElementNS(NS, 'symbol');
    sym.setAttribute('id', 'pc-' + id);
    sym.setAttribute('viewBox', '0 0 100 100');
    sym.setAttribute('overflow', 'visible');
    sym.innerHTML = P.out();
    sprite.appendChild(sym);
    built[id] = true;
    return 'pc-' + id;
  }

  /* An <svg> figurine for a unit (a battle unit or a unit id).
     opts.side overrides the side (0 white, 1 black); opts.glow overrides the
     rarity glow ('' for none); opts.cls adds classes ('sm' thickens lines
     for small sizes). */
  UI.piece = function (u, opts) {
    opts = opts || {};
    const isObj = u && typeof u === 'object';
    const def = isObj ? u.def : u;
    const d = AG.Units[def] || {};
    const side = opts.side != null ? opts.side : isObj && u.side != null ? u.side : d.pool === 'enemy' ? 1 : 0;
    const glow = opts.glow != null ? opts.glow : Art.glowFor(def);
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('class', 'pc ' + (side === 0 ? 'pw' : 'pb') + (glow ? ' ' + glow : '') + (opts.cls ? ' ' + opts.cls : ''));
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    const use = document.createElementNS(NS, 'use');
    use.setAttribute('href', '#' + symbolFor(Art.artId(isObj ? u : def)));
    svg.appendChild(use);
    return svg;
  };
})(globalThis.AG = globalThis.AG || {});
