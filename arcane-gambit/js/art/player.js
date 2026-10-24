/* Figurines for the player's units, their summons and alternate forms.
   See js/ui/pieces.js for the pen (P) and path helpers (D). */
(function (AG) {
  'use strict';
  const A = AG.Art.pieces;
  const D = AG.Art.D;
  const NUM = /(-?\d*\.?\d+),(-?\d*\.?\d+)/g;
  const r1 = (v) => Math.round(v * 10) / 10;

  // ------------------------------------------------------------ helpers
  // Rotate path data by deg (clockwise on screen) about (ox, oy).
  const turn = (d, deg, ox, oy) => {
    const a = deg * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
    return d.replace(NUM, (m, x, y) => {
      const dx = +x - ox, dy = +y - oy;
      return r1(ox + dx * c - dy * s) + ',' + r1(oy + dx * s + dy * c);
    });
  };
  // An elliptical band: the inner edge runs the other way round, so the
  // middle stays open (and P.solid clips to the band).
  const band = (cx, cy, rx, ry, irx, iry) => D.ellipse(cx, cy, rx, ry) + D.mx(D.ellipse(100 - cx, cy, irx, iry));
  // A cross from its top at (cx, y0), h tall, arms w wide, bars t thick.
  const cross = (cx, y0, h, w, t) => {
    const y1 = y0 + h * 0.3 - t / 2, y2 = y1 + t, a = t / 2, b = w / 2;
    return D.poly([[cx - a, y0], [cx + a, y0], [cx + a, y1], [cx + b, y1], [cx + b, y2], [cx + a, y2],
      [cx + a, y0 + h], [cx - a, y0 + h], [cx - a, y2], [cx - b, y2], [cx - b, y1], [cx - a, y1]]);
  };
  // Upper crossing point of two circles [cx, cy, r].
  const meet = (p, q) => {
    const dx = q[0] - p[0], dy = q[1] - p[1], d = Math.hypot(dx, dy);
    const l = (p[2] * p[2] - q[2] * q[2] + d * d) / (2 * d), h = Math.sqrt(Math.max(0, p[2] * p[2] - l * l));
    const mx = p[0] + dx * l / d, my = p[1] + dy * l / d;
    const u = [mx + dy * h / d, my - dx * h / d], v = [mx - dy * h / d, my + dx * h / d];
    return u[1] < v[1] ? u : v;
  };
  // A cloud: round puffs [cx, cy, r] from left to right over a flat underside at yb.
  const cloud = (puffs, yb) => {
    const deg = (v) => v * 180 / Math.PI;
    const pts = [];
    puffs.forEach((c, i) => {
      const sink = deg(Math.asin(Math.max(-1, Math.min(1, (yb - c[1]) / c[2]))));
      const ang = (p) => deg(Math.atan2(p[1] - c[1], p[0] - c[0]));
      const a0 = i === 0 ? -180 - sink : ang(meet(puffs[i - 1], c));
      const a1 = i === puffs.length - 1 ? sink : ang(meet(c, puffs[i + 1]));
      const arc = D.arcPts(c[0], c[1], c[2], c[2], a0, a1);
      if (i > 0) arc.shift();
      arc[arc.length - 1] = arc[arc.length - 1].concat(1);
      if (i === 0) arc[0] = arc[0].concat(1);
      pts.push(...arc);
    });
    return D.curve(pts, true);
  };
  // The front (lower) half of the same band, drawn again over whatever the
  // ring passes in front of.
  const halfBand = (cx, cy, rx, ry, irx, iry) => {
    const o = D.arcPts(cx, cy, rx, ry, 0, 180, 12), i = D.arcPts(cx, cy, irx, iry, 180, 0, 12);
    for (const a of [o, i]) { a[0].push(1); a[a.length - 1].push(1); }
    return D.curve(o.concat(i), true);
  };
  // A bone centred on (cx, cy), len long and w across the knuckles, turned deg.
  const bone = (cx, cy, len, w, deg) => {
    const h = len / 2, r = w / 3.5, k = 0.75 * r, t = w * 0.2;
    const arc = (x, y, a0, a1) => {
      const p = D.arcPts(cx + x, cy + y, r, r, a0, a1, 6);
      p[0].push(1); p[p.length - 1].push(1);
      return p;
    };
    const pts = [[cx - h + 1.9 * r, cy - t, 1], [cx + h - 1.9 * r, cy - t, 1]].concat(
      arc(h - r, -k, 200, 405), arc(h - r, k, -45, 160),
      [[cx + h - 1.9 * r, cy + t, 1], [cx - h + 1.9 * r, cy + t, 1]],
      arc(-h + r, k, 20, 225), arc(-h + r, -k, 135, 340));
    return turn(D.curve(pts, true), deg || 0, cx, cy);
  };
  // A six-armed snowflake centred on (cx, cy), arms r long and w (× r) wide.
  const flake = (cx, cy, r, w) => {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const a = (i * 60 - 90) * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
      const at = (u, v) => [cx + (c * u - s * v) * r, cy + (s * u + c * v) * r];
      for (const [u, v] of [[0.2, -w], [0.46, -w], [0.66, -0.27], [0.6, -w], [0.8, -w], [1, 0],
        [0.8, w], [0.6, w], [0.66, 0.27], [0.46, w], [0.2, w]]) pts.push(at(u, v));
    }
    return D.poly(pts);
  };

  // A pawn holding a kite shield.
  A.squire = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 50], [43, 50, 1], [42, 58], [39, 68], [34, 76], [33, 80, 1], [50, 80]]));
    P.collar(50, 51, 12, 3);
    P.ball(50, 37, 12);
    P.solid(D.curve([[41, 57, 1], [59, 57, 1], [59, 64], [50, 75, 1], [41, 64]], true), { light: 0.55 });
    P.line('M50,58L50,72M43.5,63L56.5,63');
  };

  // The horse's head, as on any chessboard.
  A.knight = function (P, D) {
    P.base('std');
    P.solid(D.curve([
      [37, 80, 1], [38, 68], [40, 59], [34, 56], [26, 54], [21.5, 49.5], [21, 44], [23.5, 39, 1],
      [29, 33.5], [33, 27], [37.5, 20], [41, 12, 1], [45, 18.5], [50, 21], [57, 25.5], [63, 34],
      [67, 47], [67.5, 62], [66, 80, 1],
    ], true), { light: 0.55 });
    P.ink(D.ellipse(34.5, 35, 2.4, 2.9));
    P.ink(D.ellipse(25.2, 45.2, 1.3, 1.6));
    P.line('M22,48.5C26,49.5 30,49 33,47.5');
    P.line('M47,24C55,30 59,40 60,52M53,25C61,33 64,43 64.5,56');
  };

  // A flame rising from a robed cone.
  A.pyromancer = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 46], [45, 46, 1], [43.5, 54], [40, 63], [35.5, 72], [33, 80, 1], [50, 80]]));
    P.solid(D.flame(50, 48, 34, 42, 2), { light: 0.56 });
    P.acc(D.flame(50.5, 46, 15, 21, 1));
    P.collar(50, 48.5, 11, 2.8);
  };

  // An hourglass held between two posts.
  A.chronomancer = function (P, D) {
    P.base('std');
    P.column(50, 66, 79, 9, 16);
    P.flat(D.rect(32.5, 15, 4, 50));
    P.flat(D.rect(63.5, 15, 4, 50));
    P.solid(D.lathe([[50, 17], [36.5, 17, 1], [37, 23], [40.5, 30.5], [46.5, 37], [47.8, 40], [46.5, 43],
      [40.5, 49.5], [37, 57], [36.5, 63, 1], [50, 63]]), { light: 0.58 });
    P.acc(D.curve([[50, 47.5, 1], [57, 55.5], [61, 62, 1], [39, 62, 1], [43, 55.5]], true));
    P.acc(D.curve([[39.5, 24, 1], [60.5, 24, 1], [56, 30], [50, 36, 1], [44, 30]], true));
    P.accLine('M50,37L50,52');
    P.tier(50, 13, 19, 3, 3.2);
    P.tier(50, 63.5, 19, 3, 3.2);
  };

  // A winged arrowhead on a slim stem.
  A.scout = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 50], [46.5, 50, 1], [46, 58], [44, 67], [39.5, 75], [37, 80, 1], [50, 80]]));
    P.pair(D.curve([[47, 43, 1], [42, 33.5], [33, 22], [17, 12, 1], [26, 21.5], [19.5, 25.5, 1], [29, 29.5], [24, 34.5, 1],
      [33, 36.5], [30.5, 42, 1], [40, 44.5]], true, 0.8), 'solid', { light: 0.66 });
    P.pair('M44,40C38,35 32,30 27,25.5M44.5,42C39,39 34,36 30,33.5', 'line');
    P.solid(D.poly([[50, 8], [61, 35], [55, 31.5], [52.6, 33], [52.6, 50], [47.4, 50], [47.4, 33], [45, 31.5], [39, 35]]), { light: 0.5 });
    P.line('M50,12L50,31');
    P.collar(50, 51, 9.5, 2.4);
  };

  // A mitre cut with a cross, under a floating halo.
  A.cleric = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 52], [45.5, 52, 1], [44.5, 59], [41, 67], [36, 75], [34, 80, 1], [50, 80]]));
    P.collar(50, 53, 11.5, 2.8);
    P.solid(D.lathe([[50, 20, 1], [44, 26.5], [40.2, 35], [40.2, 44], [44, 49.5], [50, 51]]), { light: 0.58 });
    P.eye(cross(50, 28, 17, 12, 3.4));
    P.solid(band(50, 12.5, 13, 4.6, 8.4, 2.1), { light: 0.62 });
  };

  // A pointed hat, its tip bent over to a star, on a small orb.
  A.apprentice = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 63], [45.5, 63, 1], [44, 68], [40, 74], [36.5, 80, 1], [50, 80]]));
    P.collar(50, 63.5, 10.5, 2.5);
    P.ball(50, 52.5, 10.5);
    P.solid(D.ellipse(50, 44, 17.5, 4.4), { light: 0.62 });
    P.solid(D.curve([[39, 44, 1], [41.5, 36], [43, 29], [40.5, 22], [33.5, 16.5, 1], [44, 19.5], [51.5, 25.5], [57, 34],
      [61, 44, 1], [50, 46.5]], true), { light: 0.6 });
    P.acc(D.star(32.5, 15, 6.5, 2.7, 5));
  };

  // A rook of stacked stone with two rune eyes.
  A.golem = function (P, D) {
    P.base('std');
    P.solid(D.curve([[36, 31, 1], [64, 31, 1], [63, 50], [65, 68], [67, 80, 1], [33, 80, 1], [35, 68], [37, 50]], true), { light: 0.6 });
    P.line('M36.5,44L63.5,44M35.5,57L64.5,57M34.5,69L65.5,69M46,31L46,44M56,44L56,57M43,57L43,69M54,69L54,80');
    P.solid(D.poly([[31, 13], [39.5, 13], [39.5, 18.5], [45.5, 18.5], [45.5, 13], [54.5, 13], [54.5, 18.5], [60.5, 18.5],
      [60.5, 13], [69, 13], [69, 29], [65, 33], [35, 33], [31, 29]]), { light: 0.62 });
    P.eye(D.poly([[38, 25], [42.5, 21.5], [47, 25], [42.5, 28.5]]));
    P.eye(D.poly([[53, 25], [57.5, 21.5], [62, 25], [57.5, 28.5]]));
    P.acc(D.poly([[40.5, 25], [42.5, 23.4], [44.5, 25], [42.5, 26.6]]));
    P.acc(D.poly([[55.5, 25], [57.5, 23.4], [59.5, 25], [57.5, 26.6]]));
  };

  // A snowflake crown on a slim robe.
  A.frostWitch = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 46], [46.2, 46, 1], [45.5, 54], [43.5, 63], [39.5, 72], [36, 80, 1], [50, 80]]));
    P.solid(flake(50, 27, 18, 0.1), { light: 0.6 });
    P.acc(D.regular(50, 27, 4, 6));
    P.collar(50, 47, 10, 2.6);
  };

  // A storm cloud striking its own pedestal with a bolt.
  A.stormCaller = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 63], [45, 63, 1], [42.5, 68], [38, 74], [35.5, 80, 1], [50, 80]]));
    P.collar(50, 63.5, 10.5, 2.6);
    const bolt = D.bolt(55, 33, 47.5, 63, 14);
    P.solid(bolt, { light: 0.55 });
    P.acc(D.scale(bolt, 0.5, 51.5, 47));
    P.solid(cloud([[34.5, 28.5, 7.5], [45, 22, 10.5], [57.5, 21.5, 10], [66.5, 28.5, 7.5]], 35.5), { light: 0.62 });
  };

  // A horned head before two crossed axes.
  A.berserker = function (P, D) {
    P.base('std');
    const t = (d) => turn(d, -30, 50, 54);
    const axe = [t(D.rect(48.2, 12, 3.6, 58)), t(D.curve([[48.5, 14, 1], [42, 11], [34, 7, 1], [31, 15], [30, 22], [31.5, 29],
      [35, 35, 1], [41, 28], [48.5, 26, 1]], true)), t(D.poly([[51.5, 16.5], [57, 20], [51.5, 23.5]]))];
    for (const m of [(d) => d, D.mx]) {
      P.flat(m(axe[0]));
      P.flat(m(axe[2]));
      P.solid(m(axe[1]), { light: 0.62 });
    }
    P.solid(D.lathe([[50, 50], [44, 51, 1], [42, 58], [38, 68], [34, 76], [33, 80, 1], [50, 80]]));
    P.collar(50, 51, 12, 2.8);
    P.pair(D.curve([[43, 36, 1], [37.5, 33], [34.5, 27.5], [35.5, 21, 1], [39, 26.5], [44.5, 29.5, 1]], true), 'solid');
    P.ball(50, 40, 9.5);
    P.eye(D.poly([[42.5, 38], [48, 40.5], [47.5, 42.5], [43, 41]]));
    P.eye(D.poly([[57.5, 38], [52, 40.5], [52.5, 42.5], [57, 41]]));
  };

  // A drawn bow with a nocked arrow, aimed high.
  A.ranger = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 47], [45, 48, 1], [44, 55], [41, 64], [37, 72.5], [34, 80, 1], [50, 80]]));
    P.collar(50, 49, 11, 2.6);
    const t = (d) => D.shift(turn(d, 40, 40, 31), 9, -1);
    P.line(t('M46,9L62,31L46,53'));
    P.flat(t(D.rect(16, 29.5, 46, 3)));
    P.flat(t(D.poly([[9, 31], [19.5, 25], [17.5, 31], [19.5, 37]])));
    P.flat(t(D.poly([[53, 29.5], [59, 23.5], [66, 23.5], [62, 29.5]])));
    P.flat(t(D.poly([[53, 32.5], [59, 38.5], [66, 38.5], [62, 32.5]])));
    P.solid(t(D.curve([[49, 5, 1], [45, 8], [38.5, 12.5], [34, 21], [32.2, 31], [34, 41], [38.5, 49.5], [45, 54], [49, 57, 1],
      [47, 52], [42, 46.5], [38.8, 40], [38, 31], [38.8, 22], [42, 15.5], [47, 10]], true)));
  };

  // A grinning horned imp on bat wings.
  A.imp = function (P, D) {
    P.base('low');
    P.column(50, 64, 86, 7, 15);
    P.pair(D.batWing(45, 52, 30, 26, 3), 'solid', { light: 0.72 });
    P.solid(D.ellipse(50, 62, 9, 7.5), { light: 0.6 });
    P.pair(D.curve([[40.5, 37, 1], [35.5, 32], [33.5, 25.5], [35, 18.5, 1], [37.5, 24.5], [40.5, 29.5], [45.5, 33, 1]], true), 'solid', { light: 0.7 });
    P.ball(50, 44, 12.5);
    P.eye(D.poly([[41.5, 40.5], [47.5, 43], [46.5, 45.5], [42, 44]]));
    P.eye(D.poly([[58.5, 40.5], [52.5, 43], [53.5, 45.5], [58, 44]]));
    P.eyeLine('M42.5,49C46,53.5 54,53.5 57.5,49');
  };

  // A raised fist in a ring of prayer beads.
  A.monk = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 50], [45, 50, 1], [44, 58], [41, 67], [36, 75], [34, 80, 1], [50, 80]]));
    const beads = D.arcPts(50, 52, 13, 4.2, 0, 360, 12).slice(0, 12);
    beads.filter((b) => b[1] < 52).forEach((b) => P.ball(b[0], b[1], 2.6));
    P.solid(D.curve([[44, 54, 1], [44.5, 46], [43, 42], [56, 42], [55.5, 46], [56, 54, 1]], true));
    P.solid(D.curve([[37, 44, 1], [36, 34], [36.2, 24], [38, 19.5], [41.5, 19, 1], [44.5, 17.5], [47.5, 18.5, 1], [50.5, 17],
      [53.5, 18.5, 1], [56.5, 17.5], [59.5, 19, 1], [62.5, 21], [63.5, 27], [63, 36], [61, 43], [55, 46.5], [44, 46.5]], true), { light: 0.6 });
    P.line('M41.5,19.5L42,27M47.5,19L47.8,27M53.5,19L53.3,27');
    P.solid(D.curve([[37, 37, 1], [38, 32], [45, 30], [55, 30.5], [57.5, 33], [55.5, 36], [46, 37.5], [40, 40]], true), { light: 0.7 });
    beads.filter((b) => b[1] >= 52).forEach((b) => P.ball(b[0], b[1], 2.6));
  };

  // A sun shield before a planted sword.
  A.paladin = function (P, D) {
    P.base('std');
    P.flat(D.rect(47.6, 22, 4.8, 28));
    P.solid(D.lathe([[50, 54], [44, 55, 1], [42, 62], [38, 70], [34, 80, 1], [50, 80]]));
    P.flat(D.rect(47.8, 12.5, 4.4, 10));
    P.ball(50, 11.5, 3.4);
    P.solid(D.curve([[34, 22, 1], [50, 24], [66, 22, 1], [66, 27, 1], [50, 28.5], [34, 27, 1]], true), { light: 0.7 });
    P.ball(50, 51, 17);
    P.line(D.circle(50, 51, 13.5));
    P.acc(D.star(50, 51, 11, 6, 12));
    P.eye(D.circle(50, 51, 4.6));
  };

  // A hood with a skull for a face, by a crooked staff.
  A.necromancer = function (P, D) {
    P.base('std');
    P.flat(D.rect(25.5, 22, 4, 57));
    P.solid(D.curve([[25.5, 24, 1], [24.5, 15], [30, 8.5], [38, 9], [41.5, 15], [38.5, 21.5, 1], [37, 15.5], [32.5, 13.5], [29.5, 17], [29.5, 24, 1]], true));
    P.acc(D.flame(38, 32, 7, 10, 0));
    P.solid(D.lathe([[50, 38], [41, 41], [35.5, 47], [35, 56], [34.5, 67], [32.5, 80, 1], [50, 80]]));
    P.line('M50,50L50,78');
    P.solid(D.lathe([[50, 12.5, 1], [44.5, 14.5], [39.5, 20], [37.5, 28], [38, 36], [40.5, 43], [45, 47], [50, 48]]), { light: 0.6 });
    P.ink(D.curve([[50, 20.5, 1], [56, 23.5], [58.5, 30.5], [58, 38.5], [54, 44], [50, 45], [46, 44], [42, 38.5], [41.5, 30.5], [44, 23.5]], true));
    P.skull(50, 33, 0.56);
  };

  // A fanged head in a high collar, the cape flaring into bat wings.
  A.vampire = function (P, D) {
    P.base('std');
    P.pair(D.batWing(45, 50, 33, 34, 3), 'solid', { light: 0.72 });
    P.solid(D.lathe([[50, 46], [45, 47, 1], [44, 56], [41, 66], [37, 74], [35, 80, 1], [50, 80]]));
    P.pair(D.curve([[49, 50, 1], [41, 45.5], [35, 37], [32.5, 23, 1], [39.5, 29], [45, 33], [49, 37, 1]], true), 'solid', { fill: 's' });
    P.solid(D.lathe([[50, 17.5], [45, 19], [41.5, 24], [40.5, 32], [42.5, 39], [46.5, 44], [50, 45.5]]), { light: 0.6 });
    P.ink(D.curve([[50, 26.5, 1], [45, 22.5], [41.2, 26.5, 1], [41.8, 21.5], [45.5, 18.6], [50, 17.5], [54.5, 18.6], [58.2, 21.5], [58.8, 26.5, 1], [55, 22.5]], true));
    P.eye(D.poly([[42.5, 30.5], [47.8, 32.3], [47, 34.5], [43, 33.2]]));
    P.eye(D.poly([[57.5, 30.5], [52.2, 32.3], [53, 34.5], [57, 33.2]]));
    P.eyeLine('M45.5,38.6C48,40 52,40 54.5,38.6');
    P.eye(D.poly([[46.4, 39.2], [48.4, 39.9], [47.2, 42.6]]));
    P.eye(D.poly([[53.6, 39.2], [51.6, 39.9], [52.8, 42.6]]));
    P.acc(D.regular(50, 49, 3.2, 4));
  };

  // An empty, ragged hood with two eyes, and a dagger.
  A.shade = function (P, D) {
    P.base('std');
    P.solid(D.blade(66, 52, 74, 17, 5.5), { light: 0.5 });
    P.solid(D.curve([[60, 11, 1], [61.5, 19], [63, 30], [62.5, 42], [64, 54], [66, 66], [68, 79, 1], [62, 74, 1], [57.5, 80, 1],
      [53, 74.5, 1], [48, 80, 1], [43.5, 74.5, 1], [38.5, 80, 1], [34, 73, 1], [35.5, 62], [36.5, 50], [36.5, 38], [38.5, 26], [45, 16]], true), { light: 0.62 });
    P.ink(D.curve([[47, 21, 1], [53, 24], [55.5, 31], [54.5, 39], [49.5, 44], [43.5, 43], [40, 37], [40.5, 28]], true));
    P.hi(D.poly([[42, 31], [47.5, 33], [46.8, 35], [42.5, 33.6]]));
    P.hi(D.poly([[53.5, 31.5], [49.8, 33.2], [50.4, 35.1], [53.4, 33.9]]));
    P.flat(turn(D.rect(61, 50, 11, 3.4), -76, 66.5, 51.7));
    P.ball(64.5, 59, 3);
  };

  // Two masks on a slender stem, each the mirror of the other.
  A.illusionist = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 54], [46, 54, 1], [45, 62], [41.5, 71], [37, 80, 1], [50, 80]]));
    const mask = D.curve([[50, 12, 1], [57.5, 14], [61.5, 22], [60.5, 33], [55.5, 43], [50, 46.5], [44.5, 43], [39.5, 33], [38.5, 22], [42.5, 14]], true);
    const eye = D.poly([[41, 24], [47, 25.5], [46.5, 28.5], [41.5, 27.5]]);
    const back = (d) => turn(D.shift(d, 9, -3), 16, 59, 26), front = (d) => turn(D.shift(d, -7, 0), -14, 43, 29);
    P.solid(back(mask), { fill: 's' });
    P.eye(back(D.mx(eye)));
    P.eyeLine(back('M51,39C53,37.5 56,37.5 58,39'));
    P.solid(front(mask), { light: 0.6 });
    P.eye(front(eye));
    P.eye(front(D.mx(eye)));
    P.eyeLine(front('M45,36C48,38.5 52,38.5 55,36'));
    P.acc(D.star(26, 15, 6, 1.8, 4));
    P.collar(50, 54.5, 10, 2.6);
  };

  // One great eye between curling horns.
  A.warlock = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 50], [45.5, 50, 1], [44.5, 58], [41, 67], [36.5, 75], [34, 80, 1], [50, 80]]));
    P.collar(50, 51, 11.5, 2.8);
    P.pair(D.curve([[41, 44, 1], [32, 39], [26.5, 30], [27, 19], [32.5, 11.5], [39.5, 10.5], [42.5, 15, 1], [37, 15.5], [33.5, 20],
      [33.5, 28], [37.5, 34], [43, 36.5, 1]], true), 'solid', { light: 0.6 });
    P.ball(50, 35, 12.5);
    P.line('M38,35C43,28 57,28 62,35C57,42 43,42 38,35Z');
    P.eye(D.circle(50, 35, 5.2));
    P.acc(D.curve([[50, 30.8, 1], [51.6, 35], [50, 39.2, 1], [48.4, 35]], true));
    P.hi(D.circle(47.6, 33, 1.1));
  };

  // A sapling branching into antlers, a new leaf between them.
  A.druid = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 50], [45.5, 50, 1], [44.5, 58], [41, 67], [36.5, 75], [34, 80, 1], [50, 80]]));
    P.pair(D.leaf(30, 22, 17, 16, 7), 'solid', { light: 0.7 });
    P.pair(D.leaf(38, 33, 27, 38, 6), 'solid', { light: 0.7 });
    P.pair(D.curve([[49.5, 47, 1], [44, 40], [37.5, 34], [32, 28], [28.5, 21], [28, 11, 1], [31.6, 19], [35, 24.5], [37.5, 27.5, 1],
      [37.5, 20], [39.5, 12.5, 1], [41.4, 20], [41.2, 28.5], [45, 33.5], [50.5, 37.5, 1]], true), 'solid', { light: 0.6 });
    P.acc(D.leaf(50, 42, 50, 19, 9));
    P.collar(50, 51, 11, 2.8);
  };

  // A mortar tipped back, a fused shell leaving its mouth.
  A.cannoneer = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 60], [44, 60, 1], [42.5, 66], [38.5, 73], [35, 80, 1], [50, 80]]));
    const t = (d) => turn(d, -35, 50, 55);
    P.solid(t(D.lathe([[50, 27], [40, 27, 1], [41.5, 35], [40.5, 44], [42, 52], [45.5, 57.5], [50, 59]])), { light: 0.6 });
    P.line(t('M41,36L59,36M40.8,46L59.2,46'));
    P.solid(t(D.ellipse(50, 27.5, 11.5, 3.8)), { shade: false });
    P.ink(t(D.ellipse(50, 27.5, 7.5, 2.2)));
    P.collar(50, 60.5, 13, 3);
    P.ball(23, 19.5, 7.5);
    P.eyeLine('M27,14C28,10.5 31,9 34,10');
    P.acc(D.star(35, 10, 4.6, 1.8, 6));
  };

  // A swallow-tailed pennant on a tall spear.
  A.bannerman = function (P, D) {
    P.base('std');
    P.flat(D.rect(48, 16, 4, 35));
    P.solid(D.curve([[52, 17, 1], [60, 14.5], [68, 17], [76, 17.5], [85, 15, 1], [77.5, 24], [83.5, 33, 1], [73, 31.5], [64, 34.5],
      [52, 35.5, 1]], true), { light: 0.7 });
    P.line('M56,17L56,35');
    P.acc(D.star(66, 25, 5.2, 2.2, 5));
    P.solid(D.poly([[50, 7], [54, 13.5], [50, 17.5], [46, 13.5]]), { light: 0.5 });
    P.solid(D.lathe([[50, 50], [45, 50, 1], [44, 58], [40.5, 67], [36, 75], [33.5, 80, 1], [50, 80]]));
    P.collar(50, 51, 11, 2.8);
  };

  // A queen's crown of points and a star, girdled by an orbiting ring.
  A.archmage = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 46], [45.5, 46, 1], [45, 53], [43, 61], [39.5, 69], [35.5, 76], [33.5, 80, 1], [50, 80]]));
    P.collar(50, 47, 11.5, 2.8);
    const tilt = (d) => turn(d, -12, 50, 35);
    P.solid(tilt(band(50, 35, 25.5, 8, 18.5, 3.6)), { light: 0.7 });
    P.solid(D.curve([[44, 46, 1], [56, 46, 1], [58, 40], [62, 33], [67, 22, 1], [60.5, 29], [57.5, 19.5, 1], [53.5, 28.5], [50, 21, 1],
      [46.5, 28.5], [42.5, 19.5, 1], [39.5, 29], [33, 22, 1], [38, 33], [42, 40]], true));
    P.solid(tilt(halfBand(50, 35, 25.5, 8, 18.5, 3.6)), { light: 0.7 });
    P.acc(D.star(50, 15, 7.5, 3.2, 5));
  };

  // A firebird rising, wings raised, out of its own flame.
  A.phoenix = function (P, D) {
    P.base('std');
    for (const [x0, y0, x1, y1, w] of [[44, 54, 19, 46, 8], [43, 50, 13, 30, 10], [44, 46, 17, 11, 11]]) {
      P.pair(D.leaf(x0, y0, x1, y1, w), 'solid', { light: 0.66 });
    }
    P.solid(D.curve([[52, 70, 1], [44.5, 62], [42, 52], [43.5, 43], [44.5, 36], [42.5, 29], [38, 25.5], [31, 22, 1], [37, 19],
      [40.5, 14.5], [46, 12.5], [51, 15], [53, 22], [54, 31], [58, 41], [59.5, 52], [57.5, 62]], true), { light: 0.6 });
    P.solid(D.curve([[47, 13.5, 1], [52, 8.5], [59, 6, 1], [55.5, 10.5], [63.5, 10.5, 1], [57.5, 14], [62, 18.5, 1], [55.5, 18], [52.5, 22, 1]], true), { light: 0.7 });
    P.eye(D.circle(42.5, 19.5, 1.7));
    P.solid(D.flame(50, 80, 30, 26, 0), { light: 0.56 });
    P.acc(D.flame(50, 79, 14, 15, 0));
  };

  // ------------------------------------------------------------- summons
  // A skull on a ribcage.
  A.skeleton = function (P, D) {
    P.base('low');
    P.column(50, 66, 86, 6, 12);
    P.solid(D.lathe([[50, 49], [42, 50], [37, 54.5], [35.5, 61], [37, 67.5], [42.5, 71.5], [50, 72.5]]), { light: 0.62 });
    for (const y of [55, 60.5, 66]) {
      P.pair(D.curve([[47, y - 0.8, 1], [42, y - 1.2], [39.2, y + 0.6], [38.8, y + 2.2, 1], [42.2, y + 1.2], [47, y + 1.3, 1]], true), 'ink');
    }
    P.skull(50, 39, 0.82);
  };

  // A spirit wolf howling, its body trailing away into a wisp.
  A.spiritWolf = function (P, D) {
    P.base('low');
    P.solid(D.curve([[58, 56, 1], [68, 60], [73, 68], [69, 76, 1], [69.5, 69], [64, 64]], true, 0.9), { light: 0.6 });
    P.solid(D.shift(D.curve([[18, 19, 1], [23, 15.5], [30, 13.5], [36, 12], [39, 7.5], [41.5, 1.5, 1], [45.5, 7], [49.5, 2.5, 1], [52, 10],
      [56, 16], [60, 24], [67, 30, 1], [62.5, 32.5], [67, 39.5, 1], [61.5, 41.5], [61, 51], [57.5, 61], [52, 69], [47, 75], [38, 80.5, 1],
      [47, 70.5], [50, 63], [49.5, 55], [43, 52, 1], [45, 47], [38, 44, 1], [37, 38], [31, 31], [22, 26, 1], [30.5, 23.5, 1]], true, 0.9), 0, 5), { light: 0.6 });
    P.eye(D.poly([[30.5, 23.5], [37.5, 22], [36.5, 25], [31.5, 25.5]]));
    P.line('M44,12.5L45,18M51,30C54.5,38 55.5,46 54,56');
  };

  // A cracked egg sitting in its own fire, on a bed of embers.
  A.emberEgg = function (P, D) {
    P.base('none');
    P.solid(D.ellipse(50, 89.5, 30, 6.5), { light: 0.62 });
    P.solid(D.lathe([[50, 22], [42, 25.5], [36, 35], [33, 48], [33.5, 62], [38, 74], [44, 80.5], [50, 82]]), { light: 0.6 });
    P.eye(D.poly([[47, 23], [50.5, 31], [45.5, 37], [51, 45], [48.5, 46.4], [42.8, 37.4], [48, 31.4], [45.2, 23.4]]));
    for (const [x, w, h, lean] of [[33, 20, 27, -3], [67, 20, 27, 3], [50, 22, 33, 1]]) {
      P.solid(D.flame(x, 91, w, h, lean), { light: 0.58 });
      P.acc(D.flame(x + lean * 0.2, 90, w * 0.42, h * 0.45, lean * 0.4));
    }
  };




  // A heap of bones with a skull on top.
  A.bonePile = function (P, D) {
    P.base('none');
    P.solid(bone(60, 69.5, 36, 10, -58), { light: 0.6 });
    P.solid(bone(46, 81.5, 44, 11, -14), { light: 0.6 });
    P.solid(bone(56, 83.5, 42, 11, 18), { light: 0.6 });
    P.solid(bone(50, 89.5, 50, 11, 2), { light: 0.6 });
    P.skull(42, 63.5, 0.9);
  };

  // ------------------------------------------------------ alternate forms
  // The promoted squire: a taller pawn, crowned, with a raised sword.
  A.champion = function (P, D) {
    P.base('std');
    P.solid(D.blade(67, 50, 67, 9, 6.5), { light: 0.5 });
    P.solid(D.lathe([[50, 46], [43.5, 46, 1], [42.5, 54], [39.5, 64], [35, 73], [33, 80, 1], [50, 80]]));
    P.flat(D.rect(65.2, 52, 3.6, 9));
    P.flat(D.rect(59.5, 48.5, 15, 3.6));
    P.ball(67, 63, 2.8);
    P.collar(50, 47, 13, 3.2);
    P.ball(50, 33, 11.5);
    P.solid(D.curve([[39.5, 28.5, 1], [38, 17, 1], [44, 22.5, 1], [50, 12.5, 1], [56, 22.5, 1], [62, 17, 1], [60.5, 28.5, 1], [50, 30]], true), { light: 0.6 });
    P.acc(D.regular(50, 25, 2.6, 4));
  };

  // The druid in bear form: a bear's head with a leaf on its brow.
  A.druidBear = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 54], [44, 54, 1], [42.5, 60], [38.5, 68], [34, 76], [33, 80, 1], [50, 80]]));
    P.collar(50, 55, 12, 3);
    for (const x of [36, 64]) { P.ball(x, 23, 6.5); P.solid(D.circle(x, 23.5, 3), { fill: 's', rim: false }); }
    P.solid(D.lathe([[50, 21.5], [41, 23], [35.5, 29], [34, 37], [36, 45], [42, 50.5], [50, 52]]), { light: 0.62 });
    P.solid(D.ellipse(50, 44.5, 8, 6.2), { shade: false });
    P.ink(D.curve([[45.5, 40.5, 1], [54.5, 40.5, 1], [50, 45]], true));
    P.line('M50,45L50,47.5M46.5,48.2C48.5,49.8 51.5,49.8 53.5,48.2');
    P.eye(D.poly([[39.5, 32], [46, 34.5], [45, 36.8], [40.5, 35]]));
    P.eye(D.poly([[60.5, 32], [54, 34.5], [55, 36.8], [59.5, 35]]));
    P.acc(D.leaf(50, 31.5, 50, 23.5, 4.6));
  };

  AG.Art.alias.imp_summon = 'imp';
})(globalThis.AG = globalThis.AG || {});
