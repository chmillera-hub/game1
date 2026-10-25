/* Figurines for the third act: clockwork, elementals, the void, the Mad
   Grandmaster's ebony chess army, and Zugzwang with its Echoes. See
   js/ui/pieces.js for the pen (P) and path helpers (D). */
(function (AG) {
  'use strict';
  const A = AG.Art.pieces;
  const r1 = (v) => Math.round(v * 10) / 10;

  // Turn path data by deg degrees (clockwise on screen) about (ox, oy).
  function turn(d, deg, ox, oy) {
    const a = deg * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
    return d.replace(/(-?\d*\.?\d+),(-?\d*\.?\d+)/g, (m, x, y) => {
      const dx = +x - ox, dy = +y - oy;
      return r1(ox + dx * c - dy * s) + ',' + r1(oy + dx * s + dy * c);
    });
  }

  // A crystal: lit body, flat-shaded facets, facet edges, then the outline.
  function crystal(P, d, faces, edges) {
    P.solid(d, { shade: false, line: false });
    for (const f of faces || []) P.path(f, 's');
    if (edges) P.line(edges);
    P.heavy(d);
  }

  // The wind-up key in a clockwork piece's back: a shaft from (x, y) and a
  // two-lobed bow.
  function windKey(P, D, x, y) {
    P.flat(D.rect(x, y - 1.8, 9, 3.6));
    P.solid(D.curve([[x + 8, y, 1], [x + 9.5, y - 7], [x + 14, y - 10.5], [x + 18, y - 7.5], [x + 16.5, y, 1],
      [x + 18, y + 7.5], [x + 14, y + 10.5], [x + 9.5, y + 7]], true), { light: 0.5 });
  }

  // A pawn whose head is a cog, wound up by a key in its back.
  A.clockPawn = function (P, D) {
    P.base('std');
    windKey(P, D, 56, 64);
    P.solid(D.lathe([[50, 50], [44.5, 50, 1], [43.5, 57], [41, 66], [36.5, 74], [34, 80, 1], [50, 80]]));
    P.line('M38.5,70.5C44,72.5 56,72.5 61.5,70.5');
    for (const x of [41.5, 50, 58.5]) P.ink(D.circle(x, x === 50 ? 76 : 75.5, 1.2));
    P.column(50, 42, 50, 7, 9);
    P.collar(50, 51, 12.5, 3.2);
    P.solid(D.gear(50, 33, 11, 5.5, 7), { light: 0.58 });
    P.line(D.circle(50, 33, 7.4));
    P.flat(D.circle(50, 33, 4.4), 'd');
    P.eye(D.circle(50, 33, 2.1));
  };

  // The promoted pawn: a queen whose coronet is a fan of gear teeth.
  A.clockQueen = function (P, D) {
    P.base('std');
    windKey(P, D, 55, 61);
    P.solid(D.lathe([[50, 41], [45.5, 41, 1], [44.5, 49], [42.5, 60], [38, 71], [34, 80, 1], [50, 80]]));
    P.collar(50, 42, 12, 3);
    P.column(50, 15, 26, 3.5, 6);
    P.solid(D.ellipse(50, 26, 12, 5), { shade: false });
    P.ball(50, 13.5, 4.6);
    // The rim is an arc about (50, 61); each tooth points away from there.
    const C = [50, 60.8], R = 38.3, at = (deg, r, side) => {
      const a = deg * Math.PI / 180;
      return [C[0] + Math.sin(a) * r + Math.cos(a) * side, C[1] - Math.cos(a) * r + Math.sin(a) * side, 1];
    };
    const pts = [[44, 41, 1], [39.5, 35], [35.5, 29.5], at(-25, R, 0)];
    for (const deg of [-19, -9.5, 0, 9.5, 19]) {
      pts.push(at(deg, R, -2.1), at(deg, R + 6, -1.5), at(deg, R + 6, 1.5), at(deg, R, 2.1));
    }
    pts.push(at(25, R, 0), [64.5, 29.5], [60.5, 35], [56, 41, 1], [50, 41.6]);
    P.solid(D.curve(pts, true), { light: 0.58 });
    P.line('M36.5,29.5C43,32 57,32 63.5,29.5');
    P.flat(D.circle(50, 34.5, 3.5), 'd');
    P.eye(D.circle(50, 34.5, 1.7));
  };

  // A crystal obelisk on a heavy plinth, with a lens eye that fires along
  // its rank and file.
  A.turret = function (P, D) {
    P.base('std');
    P.solid(D.poly([[32.5, 80], [35, 69], [65, 69], [67.5, 80]]), { light: 0.62 });
    P.flat(D.poly([[35, 69], [38.5, 64.5], [61.5, 64.5], [65, 69]]));
    P.ink(D.circle(39, 75, 1.3));
    P.ink(D.circle(61, 75, 1.3));
    crystal(P, D.poly([[51, 8], [59, 19], [60.5, 66], [52.5, 67.5], [40, 66], [42, 19]]),
      [D.poly([[51, 8], [59, 19], [60.5, 66], [52.5, 67.5], [52, 21]])],
      'M42,19L52,21L59,19M52,21L52.5,67.5');
    P.accLine('M37.5,36L28,36M62.5,36L72,36');
    P.ball(50, 36, 9.5);
    P.eye(D.circle(50, 36, 5.2));
    P.ink(D.ellipse(50, 36, 1.5, 3.6));
  };

  // A living flame with an angry face.
  A.fireElemental = function (P, D) {
    P.base('std');
    P.solid(D.flame(50, 81, 52, 70, -5), { light: 0.58 });
    P.line('M41,26C37,33 37,40 40,45M60,31C64,37 64,43 62,47');
    P.eye(D.poly([[37.5, 54], [47, 58], [46, 61.5], [38.5, 59]]));
    P.eye(D.poly([[62.5, 54], [53, 58], [54, 61.5], [61.5, 59]]));
    P.eye(D.poly([[41.5, 66], [45, 68.5], [47.5, 66.5], [50, 69], [52.5, 66.5], [55, 68.5], [58.5, 66],
      [55.5, 72.5], [44.5, 72.5]]));
  };

  // A figure of ice shards: a tall crystal body with shard arms.
  A.frostElemental = function (P, D) {
    P.base('std');
    const shard = (x0, y0, x1, y1, w) => {
      P.solid(D.blade(x0, y0, x1, y1, w), { light: 0.5 });
      P.line('M' + x0 + ',' + y0 + 'L' + x1 + ',' + y1);
    };
    shard(46, 79, 27, 63, 9);
    shard(54, 79, 73, 65, 9);
    shard(41, 66, 19, 28, 11);
    shard(59, 66, 81, 31, 10);
    crystal(P, D.poly([[50, 8], [61, 21], [62.5, 58], [57, 80], [43, 80], [37.5, 58], [39, 21]]),
      [D.poly([[50, 8], [61, 21], [62.5, 58], [57, 80], [52.5, 80], [53.5, 58], [53, 21]])],
      'M39,21L53,21L61,21M53,21L50,8M53,21L53.5,58L52.5,80');
    P.eye(D.poly([[41, 33], [48.5, 36], [47.5, 39], [42, 37]]));
    P.eye(D.poly([[59.5, 33], [52.5, 36], [53.5, 39], [58.5, 37]]));
  };

  // A hooded shadow whose face is a hole into the void, with a crescent
  // clasp at its throat.
  A.voidStalker = function (P, D) {
    P.base('std');
    P.solid(D.curve([[33, 80, 1], [35, 68], [33.5, 57], [30.5, 46], [29, 34], [27.5, 22], [24, 10.5, 1], [34, 11],
      [45, 11], [56, 15], [63.5, 24], [66.5, 37], [65, 50], [67.5, 64], [70, 80, 1], [64.5, 76.5, 1], [59.5, 80.5, 1],
      [54.5, 76.5, 1], [49.5, 80.5, 1], [44.5, 76.5, 1], [39, 80.5, 1]], true), { light: 0.6 });
    P.line('M40.5,57C42,65 41.5,72 39.5,78M58,53C60,62 61,70 62,76');
    P.flat(D.curve([[31, 19, 1], [43, 21], [51.5, 28.5], [53.5, 39], [49, 48.5], [40, 50], [34, 43.5], [31.5, 31]], true),
      'd');
    P.eye(D.poly([[34, 31], [41.5, 34.5], [40.5, 37.5], [35, 35]]));
    P.eye(D.poly([[51, 31], [44.5, 34.5], [45.5, 37.5], [50, 35]]));
    P.eye(D.crescent(47, 60.5, 7, 0.75, -40));
  };

  // A horned demon bust with a heavy, tusked jaw.
  A.demonBrute = function (P, D) {
    P.base('std');
    P.pair(D.curve([[40.5, 35, 1], [32, 33.5], [24, 28.5], [19.5, 19.5], [20.5, 8.5, 1], [26, 17.5], [31.5, 23],
      [38, 24.5], [43, 25, 1]], true), 'solid', { light: 0.6 });
    P.solid(D.lathe([[50, 50], [40, 51.5], [30, 55.5], [26, 62], [26.5, 71], [31, 80, 1], [50, 80]]));
    P.solid(D.lathe([[50, 19], [43, 20.5], [38.5, 25], [37, 32], [37.5, 39], [35, 46], [35.5, 52, 1], [42, 57],
      [50, 58]]), { light: 0.6 });
    P.eye(D.poly([[39, 33.5], [47.5, 38], [46.5, 41], [40, 38.5]]));
    P.eye(D.poly([[61, 33.5], [52.5, 38], [53.5, 41], [60, 38.5]]));
    P.line('M47,40.5L45.5,46.5M53,40.5L54.5,46.5');
    P.ink(D.ellipse(47.5, 46.5, 1.3, 1.5));
    P.ink(D.ellipse(52.5, 46.5, 1.3, 1.5));
    P.eyeLine('M39.5,51.5C45,53.5 55,53.5 60.5,51.5');
    P.pair(D.poly([[39.5, 54], [41, 45], [44.5, 53.5]]), 'flat');
  };

  // A knight cut from mirror glass: a faceted horse head with a crystal mane.
  A.mirrorKnight = function (P, D) {
    P.base('std');
    const spike = (x0, y0, x1, y1, w) => {
      const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy), nx = -dy / L * w / 2, ny = dx / L * w / 2;
      P.solid(D.poly([[x0 + nx, y0 + ny], [x0 + dx * 0.5 + nx * 0.8, y0 + dy * 0.5 + ny * 0.8], [x1, y1],
        [x0 + dx * 0.5 - nx * 0.8, y0 + dy * 0.5 - ny * 0.8], [x0 - nx, y0 - ny]]), { light: 0.45 });
    };
    spike(54, 24, 66, 6, 9);
    spike(61, 32, 81, 20, 9);
    spike(66, 45, 86, 41, 9);
    spike(68, 59, 84, 63, 8);
    const head = D.poly([[37, 80], [39, 63], [31.5, 58], [22, 53], [19, 46], [24, 37], [31, 28], [34, 12],
      [41.5, 19.5], [52, 21], [62, 30], [67.5, 45], [68.5, 62], [66, 80]]);
    crystal(P, head, [
      D.poly([[52, 21], [62, 30], [67.5, 45], [68.5, 62], [66, 80], [56, 80], [50, 52], [46, 32]]),
      D.poly([[39, 63], [31.5, 58], [44, 52]]),
    ], 'M31,28L37,34L46,32L52,21M37,34L33,47L19,46M33,47L44,52L50,52L56,80M44,52L39,63M46,32L50,52M41.5,19.5L46,32');
    P.eye(D.poly([[28.5, 34.5], [36, 36], [31, 39.5]]));
    P.eye(D.star(30, 66, 5, 1.4, 4));
  };

  // A band of an ellipse between parameter angles a0 and a1 (degrees, 0 =
  // right, 90 = down), w thick, turned by deg about its centre.
  function band(D, cx, cy, rx, ry, w, a0, a1, deg) {
    const out = D.arcPts(cx, cy, rx, ry, a0, a1, 18), inn = D.arcPts(cx, cy, rx - w, ry - w * 0.6, a1, a0, 18);
    for (const p of [out[0], out[out.length - 1], inn[0], inn[inn.length - 1]]) p[2] = 1;
    return turn(D.curve(out.concat(inn), true), deg, cx, cy);
  }
  // A whole ring of that ellipse, hole included.
  function ring(D, cx, cy, rx, ry, w, deg) {
    const hole = D.curve(D.arcPts(cx, cy, rx - w, ry - w * 0.6, 360, 0, 24).slice(0, -1), true);
    return turn(D.ellipse(cx, cy, rx, ry) + hole, deg, cx, cy);
  }
  // Redraw the near half of a flat ring over what it passes in front of:
  // its fill and its two edges, with no seams at the ends.
  function ringFront(P, D, cx, cy, rx, ry, w, deg) {
    P.path(band(D, cx, cy, rx, ry, w, 0, 180, deg), 'b');
    P.heavy(turn(D.curve(D.arcPts(cx, cy, rx, ry, 0, 180, 18)), deg, cx, cy));
    P.heavy(turn(D.curve(D.arcPts(cx, cy, rx - w, ry - w * 0.6, 0, 180, 18)), deg, cx, cy));
  }

  // A floating crystal core with an eye, inside two crossed rings.
  A.archon = function (P, D) {
    P.base('wide');
    P.column(50, 64, 79, 12, 26, { pinch: 2 });
    P.collar(50, 65, 14, 3.4);
    P.acc(D.ellipse(50, 62.5, 7, 1.8));
    const rings = [[-22, 35, 10], [22, 35, 10]];
    for (const [deg, rx, ry] of rings) P.solid(ring(D, 50, 38, rx, ry, 6, deg), { shade: false, rim: false });
    crystal(P, D.poly([[50, 11], [63.5, 34], [50, 59], [36.5, 34]]),
      [D.poly([[50, 11], [63.5, 34], [50, 59], [53, 36]])], 'M36.5,34L53,36L63.5,34M50,11L53,36L50,59');
    P.eye(D.curve([[42, 30, 1], [46, 26.5], [50, 26], [54, 27.5], [57, 30, 1], [53.5, 33], [49, 34], [45, 33]], true));
    P.acc(D.circle(49.5, 30, 2.4));
    for (const [deg, rx, ry] of rings) {
      ringFront(P, D, 50, 38, rx, ry, 6, deg);
      P.acc(turn(D.circle(50, 38 + ry - 2.6, 1.9), deg, 50, 38));
    }
  };

  // A drake's head spitting a fireball, one wing raised behind.
  A.infernalDrake = function (P, D) {
    P.base('wide');
    P.solid(D.mx(D.batWing(40, 48, 28, 50, 3)), { light: 0.5 });
    P.solid(D.curve([[56, 22, 1], [62, 14], [70, 8, 1], [65, 16], [60, 26, 1]], true), { light: 0.5 });
    for (const [x, y] of [[57, 33], [62, 45], [65, 58]]) P.solid(D.poly([[x - 3, y - 1], [x + 9, y - 6], [x + 1, y + 5]]));
    P.solid(D.curve([[41, 79, 1], [44, 69], [42, 58], [37, 50], [36, 44, 1], [50, 30], [55, 26, 1], [60, 36],
      [64, 50], [66, 63], [67, 79, 1]], true), { light: 0.55 });
    P.line('M39.5,51.5C43,54 47,54 49.5,52M42.5,59.5C46,62 50,62 52.5,60M44,67.5C47.5,70 51.5,70 54,68');
    P.solid(D.curve([[56, 24, 1], [47, 18], [39, 19.5], [30, 23], [19.5, 25.5, 1], [20.5, 29.5, 1], [30, 30.5],
      [38.5, 32.5, 1], [29, 36.5], [21.5, 38, 1], [23.5, 42, 1], [33, 44], [42, 44.5], [50, 40], [55, 32]], true),
      { light: 0.55 });
    P.solid(D.curve([[50, 21, 1], [57, 12], [66, 6, 1], [61, 14], [55, 26, 1]], true), { light: 0.5 });
    P.eye(D.poly([[37, 23.5], [44.5, 24], [42.5, 27], [38, 26]]));
    P.ink(D.ellipse(23.5, 26.5, 1, 1.2));
    P.solid(turn(D.flame(13, 35, 17, 20, 0), 90, 13, 35), { light: 0.62 });
    P.acc(turn(D.flame(14.5, 35, 9, 11, 0), 90, 14.5, 35));
  };

  // A tapering wisp from (x0, y0) to (x1, y1), w wide at the root, bowed
  // one way by bend and back the other near the tip.
  function wisp(D, x0, y0, x1, y1, w, bend) {
    const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy), nx = -dy / L, ny = dx / L;
    const m = (t, b, s) => [x0 + dx * t + nx * (b + s), y0 + dy * t + ny * (b + s)];
    return D.curve([m(0, 0, -w / 2).concat(1), m(0.45, bend, -w * 0.32), m(0.8, -bend * 0.6, -w * 0.12), [x1, y1, 1],
      m(0.78, -bend * 0.6, w * 0.1), m(0.45, bend, w * 0.3), m(0, 0, w / 2).concat(1)], true);
  }

  // The Old Champion: a spectral knight. A horse's head with a mane of
  // streaming wisps, its neck flowing into a ragged sheet that hovers.
  A.ghostChampion = function (P, D) {
    P.base('wide');
    for (const [x0, y0, x1, y1, w, b] of [[62, 52, 85, 56, 10, -3], [61, 41, 88, 38, 11, -3.5],
      [57.5, 30, 87, 22, 11, -3.5], [51.5, 21, 80, 10, 11, -3.5], [44, 16, 69, 6.5, 10, -3]]) {
      P.solid(wisp(D, x0, y0, x1, y1, w, b), { light: 0.4 });
    }
    P.solid(D.curve([[31.5, 72, 1], [33.5, 64], [34.5, 57.5], [29.5, 54], [23.5, 51], [20, 48.5, 1], [23, 45.5, 1],
      [17.5, 43.5, 1], [17, 39.5], [19.5, 35], [24.5, 29.5], [29, 23], [31.5, 18.5], [34.5, 10, 1], [38, 14],
      [41, 15.5, 1], [48.5, 16], [55.5, 20], [61, 27.5], [64.5, 37.5], [66, 49.5], [67, 60], [69.5, 72, 1],
      [64.5, 69.5], [60, 74.5, 1], [55, 69.5], [50.5, 75, 1], [45.5, 69.5], [41, 74.5, 1], [36, 69.5]], true),
      { light: 0.55 });
    P.line('M44,18.5C52,21 57.5,29 60,40.5M28,52.5C34,50 38.5,45 38.5,38.5M46,58C47,63 47,66 46,69M58,56C59,61 59.5,65 59,69');
    P.eye(D.ellipse(31, 30.5, 2.8, 3.6));
    P.ink(D.ellipse(20.3, 40.5, 1.1, 1.5));
  };

  // ------------------------------------------- the Mad Grandmaster's army
  // Classic turned chessmen: a domed foot with a bead, and for most a
  // waisted stem rising to a collar at y (w wide under it, rc its radius).
  function foot(P, D, k) {
    k = k || 0;
    P.solid(D.lathe([[50, 69], [42.5 - k, 69, 1], [41 - k, 72.5], [37 - k, 76.5], [34.5 - k, 80, 1], [50, 80]]));
  }
  function stem(P, D, y, w, rc) {
    foot(P, D);
    P.column(50, y, 70, w, 15.5, { pinch: 1.8 });
    P.collar(50, 70.5, 11, 2.6);
    P.collar(50, y + 0.5, rc, 3);
  }

  A.ebonPawn = function (P, D) {
    P.base('std');
    stem(P, D, 51, 9, 12.5);
    P.ball(50, 39, 11);
  };

  A.ebonRook = function (P, D) {
    P.base('std');
    foot(P, D, 1);
    P.column(50, 42, 70, 18, 21, { pinch: 1 });
    P.collar(50, 70.5, 12.5, 2.6);
    P.collar(50, 43, 13.5, 3);
    P.solid(D.poly([[37.5, 41], [35.5, 22.5], [35.5, 15.5], [42, 15.5], [42, 21.5], [46.5, 21.5], [46.5, 15.5],
      [53.5, 15.5], [53.5, 21.5], [58, 21.5], [58, 15.5], [64.5, 15.5], [64.5, 22.5], [62.5, 41]]), { light: 0.6 });
    P.line('M36,27C42,28.5 58,28.5 64,27');
  };

  A.ebonBishop = function (P, D) {
    P.base('std');
    stem(P, D, 48, 8, 12);
    P.collar(50, 45, 8.5, 2.2);
    P.solid(D.lathe([[50, 16], [44.5, 18.5], [40, 25], [38.5, 33], [40.5, 40], [45, 44, 1], [50, 44.5]]), { light: 0.58 });
    P.flat(D.poly([[43, 23], [56.5, 33], [55.5, 35.5], [42, 25.5]]), 'd');
    P.ball(50, 13.5, 3.6);
  };

  A.ebonQueen = function (P, D) {
    P.base('std');
    stem(P, D, 41, 8.5, 12.5);
    P.solid(D.ellipse(50, 24.5, 11, 5), { shade: false });
    P.column(50, 14, 21, 3, 5);
    P.ball(50, 12, 4.4);
    P.solid(D.curve([[44, 40.5, 1], [39.5, 34.5], [35.5, 28], [33.5, 19, 1], [38, 24.5, 1], [42, 18, 1], [46, 24, 1],
      [50, 17.5, 1], [54, 24, 1], [58, 18, 1], [62, 24.5, 1], [66.5, 19, 1], [64.5, 28], [60.5, 34.5], [56, 40.5, 1],
      [50, 41]], true), { light: 0.58 });
    P.line('M36.5,29.5C43,32 57,32 63.5,29.5');
  };

  A.ebonKnight = function (P, D) {
    P.base('std');
    foot(P, D, 1);
    P.solid(D.curve([[38, 68, 1], [37.5, 62], [35, 57.5], [30, 54], [24, 51], [20.5, 48.5, 1], [23.5, 45.5, 1],
      [18, 43.5, 1], [17.5, 39.5], [20, 35], [25, 29.5], [29.5, 23], [32, 18.5], [35, 10.5, 1], [38.5, 14.5],
      [41.5, 16, 1], [49, 16.5], [56, 20.5], [61.5, 28], [65, 38], [66.5, 50], [65.5, 60], [63.5, 68, 1]], true),
      { light: 0.55 });
    P.line('M44,18.5C52,21 57.5,29 60,40.5C61,46 61,52 60,57M28,52.5C34,50 38.5,45 38.5,38.5');
    P.line('M55,23.5L59,21.5M58.5,31L63,29.5M60.5,39L65,38.5M61.5,47L66,47');
    P.eye(D.ellipse(31.5, 31.5, 2.2, 2.8));
    P.ink(D.ellipse(20.8, 40.5, 1.1, 1.5));
    P.collar(50, 69, 15.5, 3.4);
  };

  // The Mad Grandmaster: a king whose crown has slipped askew, its cross
  // knocked crooked and a glowing crack running through it.
  A.ebonKing = function (P, D) {
    P.base('wide');
    P.solid(D.lathe([[50, 66], [40.5, 66, 1], [39, 70], [33.5, 75], [30.5, 79, 1], [50, 79]]));
    P.column(50, 36, 67, 11, 19.5, { pinch: 2.4 });
    P.collar(50, 67.5, 13, 2.8);
    P.collar(50, 37, 15, 3.4);
    P.collar(50, 33.5, 11, 2.4);
    const tilt = (d) => turn(d, 9, 50, 34);
    P.solid(tilt(turn(D.poly([[47.8, 4], [52.2, 4], [51.3, 8], [57, 7], [57, 12.5], [51.3, 11.5], [52.2, 15.5],
      [47.8, 15.5], [48.7, 11.5], [43, 12.5], [43, 7], [48.7, 8]]), 14, 50, 15)), { light: 0.55 });
    P.solid(tilt(D.lathe([[50, 32.5], [44, 32.5, 1], [40.5, 28.5], [37, 24], [35, 20, 1], [50, 20]])), { light: 0.58 });
    P.solid(tilt(D.lathe([[50, 12.5], [44, 13.5], [39.5, 16.5], [38, 20.5, 1], [50, 20.5]])), { light: 0.58 });
    P.acc(tilt(D.poly([[47.2, 13.5], [49.4, 13.5], [48.6, 17.5], [51.6, 21.5], [49, 25.5], [52, 31.5], [50.6, 31.8],
      [47.2, 25.6], [49.6, 21.6], [46.6, 17.6]])));
  };

  // ------------------------------------------------------------ the mega boss
  // Zugzwang: a king carved out of the board itself, chequered from foot to
  // collar, with a single open eye under a broken ring of spikes.
  A.zugzwang = function (P, D) {
    P.base('wide');
    // The broken halo behind the head: eight spikes, two of them snapped off.
    const spikes = [];
    for (let i = 0; i < 8; i++) {
      if (i === 2 || i === 5) continue;
      const a = (-90 + i * 45) * Math.PI / 180, c = Math.cos(a), sn = Math.sin(a);
      const len = i % 2 ? 19 : 24;
      spikes.push([[50 + c * 9 - sn * 3.2, 18 + sn * 9 + c * 3.2], [50 + c * len, 18 + sn * len], [50 + c * 9 + sn * 3.2, 18 + sn * 9 - c * 3.2]]);
    }
    for (const sp of spikes) P.solid(D.poly(sp), { shade: false, light: 0.5 });
    P.solid(D.lathe([[50, 66], [39.5, 66, 1], [37.5, 70], [31.5, 75], [28.5, 79, 1], [50, 79]]));
    const body = D.curve([[42, 33, 1], [58, 33, 1], [59.5, 50], [62.5, 67, 1], [37.5, 67, 1], [40.5, 50]], true, 0.8);
    P.solid(body, { line: false });
    // The chequer, clipped to the body.
    const id = P.uid();
    P.raw('<clipPath id="' + id + '"><path d="' + body + '"/></clipPath>');
    let sq = '';
    for (let r = 0; r < 5; r++) {
      for (let c = 0; c < 4; c++) if ((r + c) % 2) sq += D.rect(36 + c * 7, 33 + r * 7, 7, 7);
    }
    P.path(sq, 'd', ' clip-path="url(#' + id + ')"');
    P.heavy(body);
    P.collar(50, 67.5, 14.5, 3);
    P.collar(50, 34, 16.5, 3.6);
    P.collar(50, 30.5, 12, 2.6);
    // The head: a smooth dome with one eye, the pupil lit.
    P.solid(D.lathe([[50, 29.5], [43.5, 29.5, 1], [39.5, 25], [38, 19], [40, 13], [44.5, 9.5], [50, 8.5]]), { light: 0.58 });
    P.eye(D.curve([[42, 19, 1], [46, 15.5], [50, 15], [54, 15.5], [58, 19, 1], [54, 22.5], [50, 23], [46, 22.5]], true));
    P.acc(D.circle(50, 19, 2.6));
    P.line('M45,27C48,28 52,28 55,27');
  };

  // An Echo: a pawn from an old game, fraying into wisps below the collar.
  A.echo = function (P, D) {
    P.base('low');
    P.solid(D.curve([[41, 52, 1], [59, 52, 1], [60, 60], [63.5, 67], [66, 74], [61, 71.5], [57.5, 78.5], [52.5, 73.5],
      [48, 80], [44.5, 73], [39, 77.5], [37.5, 70], [33.5, 72.5], [37, 64], [40, 58]], true), { light: 0.58 });
    P.collar(50, 52.5, 12, 2.8);
    P.ball(50, 40.5, 10.5);
    P.eye(D.ellipse(46, 40, 1.6, 2.4)).eye(D.ellipse(54, 40, 1.6, 2.4));
    P.line('M44,60C45,64 46,67 47,70M55.5,60C55.5,64 56,67 57.5,70');
  };
})(globalThis.AG = globalThis.AG || {});
