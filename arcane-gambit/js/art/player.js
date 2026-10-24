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
    P.pair(D.curve([[47, 43, 1], [39, 35], [31, 25], [18, 12, 1], [26, 23.5], [21.5, 27, 1], [30, 31.5], [26.5, 36, 1],
      [35, 38], [33, 43, 1], [41, 45.5]], true, 0.8), 'solid', { light: 0.66 });
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
    P.solid(D.bolt(55, 33, 47.5, 63, 14), { light: 0.55 });
    P.solid(cloud([[31.5, 29, 7.5], [42.5, 21, 10], [57, 20, 10.5], [68.5, 28, 7.5]], 35.5), { light: 0.62 });
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

  // A drawn bow with a nocked arrow, aimed high, on a dome.
  A.ranger = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 46], [45, 47, 1], [44, 54], [41, 63], [37, 72], [34, 80, 1], [50, 80]]));
    P.collar(50, 48, 11, 2.6);
    const t = (d) => turn(d, 30, 46, 32);
    P.line(t('M44,10L64,32L44,54'));
    P.flat(t(D.rect(20, 30.6, 46, 2.8)));
    P.flat(t(D.poly([[14, 32], [22, 27.5], [21, 32], [22, 36.5]])));
    P.flat(t(D.poly([[60, 31], [66, 26], [71, 26], [66, 31]])));
    P.flat(t(D.poly([[60, 33], [66, 38], [71, 38], [66, 33]])));
    P.solid(t(D.curve([[44, 10, 1], [38, 16], [33.5, 25], [32, 32], [33.5, 39], [38, 48], [44, 54, 1], [40, 46], [37, 38],
      [36.5, 32], [37, 26], [40, 18]], true)));
  };

  // A grinning horned imp on bat wings.
  A.imp = function (P, D) {
    P.base('low');
    P.column(50, 64, 86, 7, 15);
    P.pair(D.batWing(45, 52, 30, 26, 3), 'solid', { light: 0.72 });
    P.solid(D.ellipse(50, 62, 9, 7.5), { light: 0.6 });
    P.pair(D.curve([[42, 36, 1], [38.5, 31], [37.5, 25], [39, 19, 1], [42.5, 25.5], [46.5, 31, 1]], true), 'solid');
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
    P.flat(D.rect(47.6, 20, 4.8, 30));
    P.solid(D.lathe([[50, 54], [44, 55, 1], [42, 62], [38, 70], [34, 80, 1], [50, 80]]));
    P.flat(D.rect(47.8, 10, 4.4, 10));
    P.ball(50, 9, 3.4);
    P.solid(D.curve([[34, 20, 1], [50, 22], [66, 20, 1], [66, 25, 1], [50, 26.5], [34, 25, 1]], true), { light: 0.7 });
    P.ball(50, 51, 17);
    P.line(D.circle(50, 51, 13.5));
    P.acc(D.star(50, 51, 11, 6, 12));
    P.eye(D.circle(50, 51, 4.6));
  };

  // A hood with a skull for a face, by a crooked staff.
  A.necromancer = function (P, D) {
    P.base('std');
    P.flat(D.rect(26.5, 22, 4, 57));
    P.solid(D.curve([[26.5, 24, 1], [25.5, 15], [31, 8.5], [39, 9], [42.5, 15], [39.5, 21.5, 1], [38, 15.5], [33.5, 13.5], [30.5, 17], [30.5, 24, 1]], true));
    P.acc(D.flame(39, 32, 7, 10, 0));
    P.solid(D.lathe([[50, 12, 1], [44, 15], [38.5, 22], [36.5, 32], [37.5, 42], [38.5, 50], [37, 60], [34.5, 70], [32.5, 80, 1], [50, 80]]), { light: 0.6 });
    P.ink(D.curve([[50, 21, 1], [56, 24], [58.5, 31], [58, 39], [54, 45], [50, 46], [46, 45], [42, 39], [41.5, 31], [44, 24]], true));
    P.skull(50, 33.5, 0.56);
    P.line('M50,48L50,78');
  };

  // A pointed head, fanged, in a high collar flaring into bat wings.
  A.vampire = function (P, D) {
    P.base('std');
    P.pair(D.batWing(45, 50, 33, 34, 3), 'solid', { light: 0.72 });
    P.solid(D.lathe([[50, 46], [45, 47, 1], [44, 56], [41, 66], [37, 74], [35, 80, 1], [50, 80]]));
    P.pair(D.curve([[49, 49, 1], [41, 44], [36, 34], [35, 23, 1], [42, 31], [48, 37, 1]], true), 'solid', { light: 0.8 });
    P.solid(D.lathe([[50, 17, 1], [46, 21], [41.5, 25], [40.5, 32], [42.5, 39], [46.5, 44], [50, 45.5]]), { light: 0.6 });
    P.eye(D.poly([[42.5, 30.5], [47.8, 32.8], [47, 35], [43, 33.5]]));
    P.eye(D.poly([[57.5, 30.5], [52.2, 32.8], [53, 35], [57, 33.5]]));
    P.eyeLine('M45.5,39C48,40.5 52,40.5 54.5,39');
    P.eye(D.poly([[46.5, 39.6], [48.2, 40.2], [47.4, 42.6]]));
    P.eye(D.poly([[53.5, 39.6], [51.8, 40.2], [52.6, 42.6]]));
    P.acc(D.regular(50, 49, 3, 4));
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

  // A diamond prism splitting into two mirrored echoes.
  A.illusionist = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 56], [46, 56, 1], [45, 63], [41.5, 71], [37, 80, 1], [50, 80]]));
    const gem = D.poly([[50, 10], [61, 31], [50, 54], [39, 31]]);
    for (const a of [-1, 1]) P.solid(turn(D.shift(D.scale(gem, 0.78, 50, 54), a * 13, 0), a * 18, 50 + a * 13, 54), { fill: 's' });
    P.solid(gem, { light: 0.5 });
    P.line('M39,31L61,31M50,10L50,54');
    P.acc(D.ellipse(50, 31, 4, 2.4));
    P.collar(50, 56.5, 10, 2.6);
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
})(globalThis.AG = globalThis.AG || {});
