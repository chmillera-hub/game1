/* Figurines for the third act: clockwork, elementals, the void, and the
   Mad Grandmaster's ebony chess army. See js/ui/pieces.js for the pen (P)
   and path helpers (D). */
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

  // A talon hooking over a rim: from its root at (x, y), reaching left and
  // curling down, turned by deg.
  function talon(D, x, y, deg) {
    return turn(D.curve([[x, y - 2.3, 1], [x - 5, y - 4], [x - 9.5, y - 2], [x - 11, y + 3.8, 1], [x - 8.2, y + 0.6],
      [x - 4.5, y + 0.6], [x, y + 2.3, 1]], true), deg, x, y);
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

  // Eyes and a grin in a portal ring, and talons gripping its rim from inside.
  A.voidStalker = function (P, D) {
    P.base('std');
    P.column(50, 63, 79, 10, 22, { pinch: 1.5 });
    P.solid(D.ellipse(50, 39, 19, 25), { light: 0.6 });
    P.flat(D.ellipse(50, 39, 12.5, 18), 'd');
    P.eye(D.poly([[40.5, 30.5], [48, 34.5], [47, 37.5], [41.5, 35]]));
    P.eye(D.poly([[59.5, 30.5], [52, 34.5], [53, 37.5], [58.5, 35]]));
    P.eye(D.curve([[41.5, 44, 1], [44, 46.5, 1], [46, 44.8, 1], [48, 47, 1], [50, 45.2, 1], [52, 47, 1], [54, 44.8, 1],
      [56, 46.5, 1], [58.5, 44, 1], [55.5, 49.5], [50, 51], [44.5, 49.5]], true));
    for (const [y, deg] of [[31, 14], [37.5, 0], [44, -14]]) P.pair(talon(D, 40.5, y, deg), 'solid', { light: 0.6 });
    P.collar(50, 64.5, 10, 2.6);
  };

  // A horned demon bust with a heavy, tusked jaw.
  A.demonBrute = function (P, D) {
    P.base('std');
    P.pair(D.curve([[41, 33, 1], [33, 32], [25.5, 27.5], [21.5, 19], [21, 9, 1], [25.5, 18.5], [31, 24.5],
      [38, 26.5], [43, 27, 1]], true), 'solid', { light: 0.6 });
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
  const arc = (D, cx, cy, rx, ry, a0, a1, deg) => turn(D.curve(D.arcPts(cx, cy, rx, ry, a0, a1, 18), false), deg, cx, cy);

  // A floating crystal core with an eye, inside two crossed rings.
  A.archon = function (P, D) {
    P.base('wide');
    P.column(50, 64, 79, 12, 26, { pinch: 2 });
    P.collar(50, 65, 14, 3.4);
    P.acc(D.ellipse(50, 62.5, 7, 1.8));
    const rings = [[-14, 36, 10.5], [36, 31, 9]];
    for (const [deg, rx, ry] of rings) {
      P.solid(band(D, 50, 36, rx, ry, 4.4, 180, 360, deg), { shade: false, rim: false });
    }
    crystal(P, D.poly([[50, 12], [63.5, 36], [50, 59], [36.5, 36]]),
      [D.poly([[50, 12], [63.5, 36], [50, 59], [53, 38]])], 'M36.5,36L53,38L63.5,36M50,12L53,38L50,59');
    P.eye(D.ellipse(48.5, 34, 4.2, 3.2));
    P.ink(D.circle(48.5, 34, 1.6));
    for (const [deg, rx, ry] of rings) {
      P.solid(band(D, 50, 36, rx, ry, 4.4, 0, 180, deg), { shade: false, rim: false });
      P.acc(turn(D.circle(50, 36 + ry - 2.2, 1.6), deg, 50, 36));
    }
  };

  // A drake's head spitting a fireball, one wing raised behind.
  A.infernalDrake = function (P, D) {
    P.base('wide');
    P.solid(D.mx(D.batWing(40, 48, 28, 50, 3)), { light: 0.5 });
    P.solid(D.curve([[56, 22, 1], [62, 14], [70, 8, 1], [65, 16], [60, 26, 1]], true), { light: 0.5 });
    for (const [x, y] of [[61, 38], [65, 51], [67, 64]]) P.solid(D.poly([[x - 3, y - 3], [x + 7, y - 1], [x - 1, y + 4]]));
    P.solid(D.curve([[41, 79, 1], [44, 69], [42, 58], [37, 50], [36, 44, 1], [50, 30], [55, 26, 1], [60, 36],
      [64, 50], [66, 63], [67, 79, 1]], true), { light: 0.55 });
    P.line('M45,48C48,56 50,64 50,76M40,52L50,50M42.5,59L52,57.5M44,66L53,65');
    P.solid(D.curve([[56, 24, 1], [47, 18], [39, 19.5], [30, 23], [19.5, 25.5, 1], [20.5, 29.5, 1], [30, 30.5],
      [38.5, 32.5, 1], [29, 36.5], [21.5, 38, 1], [23.5, 42, 1], [33, 44], [42, 44.5], [50, 40], [55, 32]], true),
      { light: 0.55 });
    P.solid(D.curve([[50, 21, 1], [57, 12], [66, 6, 1], [61, 14], [55, 26, 1]], true), { light: 0.5 });
    P.eye(D.poly([[37, 23.5], [44.5, 24], [42.5, 27], [38, 26]]));
    P.ink(D.ellipse(23.5, 26.5, 1, 1.2));
    const ball = turn(D.flame(13, 35, 17, 20, 0), 90, 13, 35);
    P.solid(ball, { light: 0.62 });
    P.acc(turn(D.flame(14.5, 35, 9, 11, 0), 90, 14.5, 35));
  };

  // A wisp from (x0, y0) to (x1, y1), w wide at the root, bowed by bend.
  function wisp(D, x0, y0, x1, y1, w, bend) {
    const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy), nx = -dy / L, ny = dx / L;
    const m = (t, b, s) => [x0 + dx * t + nx * (b + s), y0 + dy * t + ny * (b + s)];
    return D.curve([m(0, 0, -w / 2).concat(1), m(0.45, bend, -w * 0.32), m(0.8, -bend * 0.6, -w * 0.12), [x1, y1, 1],
      m(0.78, -bend * 0.6, w * 0.1), m(0.45, bend, w * 0.3), m(0, 0, w / 2).concat(1)], true);
  }

  // The Old Champion: a spectral horse's head with a streaming mane, its
  // neck fading into a wisp.
  A.ghostChampion = function (P, D) {
    P.base('wide');
    for (const [x0, y0, x1, y1, w, b] of [[52, 21, 76, 7, 11, -4], [59, 31, 87, 23, 12, -4], [63, 44, 88, 42, 12, -4],
      [62, 56, 84, 62, 11, -3]]) P.solid(wisp(D, x0, y0, x1, y1, w, b), { light: 0.4 });
    P.solid(D.curve([
      [45, 78, 1], [40.5, 72], [42, 65], [37, 59], [29, 55], [22, 51.5], [17.5, 46], [17, 40], [20, 34.5],
      [26, 28.5], [31, 21], [35, 11, 1], [40, 17], [47.5, 18], [56.5, 24], [62.5, 34], [65.5, 46], [63.5, 58],
      [57, 66], [51, 69], [53.5, 73], [49, 76],
    ], true), { light: 0.55 });
    P.line('M45,24C52,30 56,40 57,52M41,62C46,64 50,66 52,69');
    P.eye(D.ellipse(31, 31, 3.2, 4));
    P.ink(D.ellipse(20.5, 42, 1.2, 1.6));
    P.line('M18,47C22,49.5 27,49.5 31,48');
  };

  // TEMP variants for comparison
  A.vsB = function (P, D) {
    P.base('std');
    P.column(50, 64, 79, 9, 22, { pinch: 1.5 });
    const half = [[50, 8, 1], [46.5, 14], [40, 17, 1], [42, 22], [34, 28, 1], [37.5, 33], [30, 40, 1], [36, 44], [32, 53, 1], [39, 55], [41, 62, 1], [46, 63], [50, 69, 1]];
    const right = half.slice(1, -1).reverse().map((p) => [100 - p[0], p[1], p[2]]);
    P.solid(D.curve(half.concat(right), true), { light: 0.6 });
    P.flat(D.curve([[50, 16, 1], [55, 26], [58, 38], [56, 50], [50, 62, 1], [44, 50], [42, 38], [45, 26]], true), 'd');
    P.eye(D.poly([[43, 34], [49, 37], [48.3, 39.5], [44, 37.5]]));
    P.eye(D.poly([[57, 34], [51, 37], [51.7, 39.5], [56, 37.5]]));
    P.collar(50, 65.5, 9.5, 2.6);
  };
  A.vsC = function (P, D) {
    P.base('std');
    P.column(50, 63, 79, 10, 22, { pinch: 1.5 });
    P.solid(D.ellipse(50, 39, 19, 25), { light: 0.6 });
    P.flat(D.ellipse(50, 39, 12.5, 18), 'd');
    P.eye(D.poly([[40.5, 30.5], [48, 34.5], [47, 37.5], [41.5, 35]]));
    P.eye(D.poly([[59.5, 30.5], [52, 34.5], [53, 37.5], [58.5, 35]]));
    for (const [y, deg] of [[39, 8], [45, 0], [51, -10]]) P.solid(talon(D, 41, y, deg), { light: 0.6 });
    P.solid(D.mx(talon(D, 40.5, 25.5, 40)), { light: 0.6 });
    P.solid(D.mx(talon(D, 39, 30.5, 28)), { light: 0.6 });
    P.collar(50, 64.5, 10, 2.6);
  };
  A.vsD = function (P, D) {
    P.base('std');
    P.solid(D.curve([[44, 9, 1], [55, 13], [63, 22], [66, 35], [64, 48], [67, 62], [70, 80, 1], [30, 80, 1], [34, 64],
      [33, 50], [30, 38], [33, 24]], true), { light: 0.6 });
    P.flat(D.curve([[44.5, 22, 1], [52, 27], [56, 37], [54, 47], [47, 52], [40, 48], [37.5, 38], [39.5, 29]], true), 'd');
    P.eye(D.poly([[39.5, 35.5], [46, 38.5], [45.3, 41], [40.5, 39]]));
    P.eye(D.poly([[54.5, 35.5], [48, 38.5], [48.7, 41], [53.5, 39]]));
    P.solid(D.crescent(43, 63, 12, 0.7, -30), { light: 0.5 });
  };
})(globalThis.AG = globalThis.AG || {});
