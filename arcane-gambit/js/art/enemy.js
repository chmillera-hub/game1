/* Figurines for enemy units and bosses. See js/ui/pieces.js for the pen (P)
   and path helpers (D). */
(function (AG) {
  'use strict';
  const A = AG.Art.pieces;

  // A grinning head with ears like knife blades.
  A.goblin = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 55], [42, 56], [36.5, 61], [33.5, 70], [32.5, 80, 1], [50, 80]]));
    P.pair('M38.5,34C31,31 21,26.5 11.5,26C17,32.5 25,40 37.5,44.5Z', 'solid', { light: 0.7 });
    P.solid(D.lathe([[50, 21], [42.5, 22], [36.5, 28], [35, 37], [37.5, 46], [43.5, 52.5], [50, 54]]), { light: 0.6 });
    P.eye(D.poly([[39.5, 35], [47, 37.5], [46, 40], [40.5, 38.5]]));
    P.eye(D.poly([[60.5, 35], [53, 37.5], [54, 40], [59.5, 38.5]]));
    P.eyeLine('M41,45.5C45,48.5 55,48.5 59,45.5M45,46.8L46,49.3M50,47.6L50,50.2M55,46.8L54,49.3');
  };

  // A blob with a sheen and two dull eyes.
  A.slime = function (P, D) {
    P.base('dish');
    P.solid(D.curve([[27, 88, 1], [25, 79], [27.5, 68], [35, 58.5], [44, 53.5], [52, 52], [61, 54.5],
      [69.5, 61.5], [74, 72], [74.5, 81], [73, 88, 1]], true), { light: 0.62 });
    P.hi(D.ellipse(39, 63, 5.5, 3.2));
    P.eye(D.ellipse(44, 71, 3, 4.2));
    P.eye(D.ellipse(57, 71, 3, 4.2));
    P.line('M66,62C69,67 70,72 69.5,77');
  };

  // ------------------------------------------------------- shared motifs
  // The goblin's head and ears as on A.goblin (centred on 50,37.5), redrawn
  // centred on (cx, cy) at scale s. face: false leaves out the eyes and grin.
  // Returns the transform, so hats and masks can be drawn in A.goblin's frame.
  const G_EAR = 'M38.5,34C31,31 21,26.5 11.5,26C17,32.5 25,40 37.5,44.5Z';
  function goblinHead(P, D, cx, cy, s, face) {
    const T = (d) => D.shift(D.scale(d, s, 50, 37.5), cx - 50, cy - 37.5);
    P.solid(T(G_EAR), { light: 0.7 }).solid(T(D.mx(G_EAR)), { light: 0.7 });
    P.solid(T(D.lathe([[50, 21], [42.5, 22], [36.5, 28], [35, 37], [37.5, 46], [43.5, 52.5], [50, 54]])), { light: 0.6 });
    if (face !== false) {
      const eye = D.poly([[39.5, 35], [47, 37.5], [46, 40], [40.5, 38.5]]);
      P.eye(T(eye)).eye(T(D.mx(eye)));
      P.eyeLine(T('M41,45.5C45,48.5 55,48.5 59,45.5M45,46.8L46,49.3M50,47.6L50,50.2M55,46.8L54,49.3'));
    }
    return T;
  }
  // A goblin's cone of a body, its top at y0.
  const goblinBody = (D, y0) => D.lathe([[50, y0], [42, y0 + 1], [36.5, y0 + 6], [33.5, y0 + 15], [32.5, 80, 1], [50, 80]]);

  // An open arc round (cx, cy), angles in degrees (0 = right, -90 = up).
  const arc = (D, cx, cy, r, a0, a1) => D.curve(D.arcPts(cx, cy, r, r, a0, a1), false);
  // A lumpy stone of radius r.
  const rock = (D, cx, cy, r) => D.curve([[-1, 0.1], [-0.55, -0.8], [0.35, -1], [1, -0.3], [0.8, 0.6], [0.1, 1],
    [-0.7, 0.75]].map(([x, y]) => [cx + x * r, cy + y * r]), true, 0.8);
  // A tapering limb (leg, arm, staff, tail) along pts, w0 wide at the first
  // point and w1 at the last. A point written [x, y, 1] is a sharp joint.
  function limb(D, pts, w0, w1) {
    const n = pts.length, L = [], R = [];
    for (let i = 0; i < n; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
      const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, w = (w0 + (w1 - w0) * i / (n - 1)) / 2;
      const nx = -(b[1] - a[1]) / len * w, ny = (b[0] - a[0]) / len * w, c = i === 0 || i === n - 1 || pts[i][2] ? 1 : 0;
      L.push([pts[i][0] + nx, pts[i][1] + ny, c]);
      R.push([pts[i][0] - nx, pts[i][1] - ny, c]);
    }
    return D.curve(L.concat(R.reverse()), true);
  }

  // Path data turned by deg degrees (clockwise) about (cx, cy).
  function rot(d, deg, cx, cy) {
    const a = deg * Math.PI / 180, c = Math.cos(a), s = Math.sin(a), r1 = (v) => Math.round(v * 10) / 10;
    return d.replace(/(-?\d*\.?\d+),(-?\d*\.?\d+)/g, (m, x, y) =>
      r1(cx + (x - cx) * c - (y - cy) * s) + ',' + r1(cy + (x - cx) * s + (y - cy) * c));
  }

  // ---------------------------------------------------------------- act I
  // A goblin whirling a sling: the stone flies round its head.
  A.goblinSlinger = function (P, D) {
    P.base('std');
    P.heavy(arc(D, 50, 41, 32, -28, -100));
    P.heavy(arc(D, 50, 41, 24.5, -38, -96));
    P.solid(goblinBody(D, 56));
    goblinHead(P, D, 50, 41, 0.9);
    P.solid(rock(D, 32, 15.5, 7), { light: 0.55 });
  };

  // A goblin behind a long bone mask, leaning on a toadstool staff.
  A.goblinShaman = function (P, D) {
    P.base('std');
    P.flat(D.curve([[24, 87, 1], [28, 87, 1], [29, 55], [28, 20, 1], [24.5, 20, 1], [25, 55]], true));
    P.solid(D.curve([[12.5, 23, 1], [14.5, 15], [21, 10], [26.5, 9], [32.5, 10.5], [38, 15.5], [40.5, 23, 1]], true), { light: 0.6 });
    P.eye(D.circle(19.5, 17, 1.8)).eye(D.circle(27, 13.2, 1.6)).eye(D.circle(33, 18, 1.8));
    P.solid(goblinBody(D, 57));
    const T = goblinHead(P, D, 53, 41, 0.92, false);
    P.solid(T(D.lathe([[50, 26], [43, 27.5], [39.5, 33], [40, 41], [43.5, 50], [50, 60]])), { light: 0.6 });
    P.ink(T(D.ellipse(45.2, 37, 3.2, 3.8))).ink(T(D.ellipse(54.8, 37, 3.2, 3.8)));
    P.eye(T(D.circle(45.2, 37.6, 1.3))).eye(T(D.circle(54.8, 37.6, 1.3)));
    P.eyeLine(T('M50,28.5L50,33M44,46L56,46M45.5,50L54.5,50M47,54L53,54'));
  };

  // A wolf's head in profile, ruff bristling, jaws open.
  A.wolf = function (P, D) {
    P.base('std');
    P.solid(D.curve([
      [38, 80, 1], [36.5, 73], [31, 70, 1], [34.5, 66], [28.5, 62, 1], [32, 58], [26, 55], [19, 51.5, 1],
      [24, 49], [30, 47, 1], [22, 45], [13.5, 43, 1], [13, 39], [18, 36], [27, 32.5], [33, 27.5], [35.5, 22],
      [37, 10, 1], [43, 18], [47, 20.5, 1], [51, 11, 1], [54, 22], [60, 30], [65, 35, 1], [63, 41], [69, 47, 1],
      [66, 53], [71, 61, 1], [67, 67], [68, 80, 1],
    ], true), { light: 0.55 });
    P.ink(D.poly([[38.2, 14.5], [41.5, 20.5], [37.6, 22]]));
    P.eye(D.poly([[28, 33.5], [32, 30.8], [36.5, 30], [34, 33.5]]));
    P.ink(D.ellipse(14.6, 40, 2.3, 1.9));
    P.flat(D.poly([[19.5, 44.6], [23, 45.4], [21, 49]]));
    P.line('M39,27C46,31 50,39 52,48M56,35C60,43 61,51 61,60');
  };

  // A small droplet of slime with a curled tip.
  A.slimeling = function (P, D) {
    P.base('low');
    P.solid(D.curve([[36, 86, 1], [34, 80], [36, 73], [41.5, 67], [46, 62], [47.5, 57.5], [45, 53.5, 1], [51, 55.5],
      [56, 60], [61.5, 66], [65.5, 73], [66.5, 80], [64, 86, 1]], true), { light: 0.62 });
    P.hi(D.ellipse(42, 69, 2.6, 1.7));
    P.eye(D.ellipse(45.5, 75, 2.3, 3.2)).eye(D.ellipse(54.5, 75, 2.3, 3.2));
  };

  // A hooded thug, masked to the eyes, with a knife held up.
  A.bandit = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 56], [41, 57], [37, 63], [34.5, 71], [33, 80, 1], [50, 80]]));
    P.solid(D.lathe([[50, 12], [44, 14], [38, 20], [35, 29], [34.5, 39], [33, 48], [28.5, 56], [27, 61, 1], [38, 63.5], [50, 64]]), { light: 0.6 });
    P.ink(D.lathe([[50, 24], [44, 26], [40.5, 32], [40, 39], [42.5, 45.5], [50, 49]]));
    P.solid(D.curve([[39.5, 37.5, 1], [60.5, 37.5, 1], [58.5, 45], [50, 55, 1], [41.5, 45]], true), { light: 0.6 });
    P.eye(D.poly([[42, 31.5], [47.5, 33.5], [47, 35.5], [42.5, 34]])).eye(D.poly([[58, 31.5], [52.5, 33.5], [53, 35.5], [57.5, 34]]));
    P.flat(D.blade(64, 62, 77, 28, 6.5));
    P.flat(D.poly([[57.8, 59.3], [69.8, 63.9], [68.9, 66.3], [56.9, 61.7]]));
    P.flat(D.poly([[61.9, 64.5], [65, 65.6], [62.4, 72.6], [59.3, 71.4]]));
  };

  // A boar's head in profile: a long snout, a tusk curling up past it, the
  // ear laid back, and a hump of hooked thorns down its back.
  A.boar = function (P, D) {
    P.base('std');
    P.solid(D.curve([
      [34, 80, 1], [32.5, 71], [27, 65.5], [19.5, 62.5], [15.5, 62, 1], [17, 59, 1], [14, 57.5, 1], [12.5, 51.5],
      [14, 46, 1], [19, 43.5], [27, 39], [33, 32], [38.5, 27], [44, 24, 1], [52, 7, 1], [53.5, 20, 1], [64, 8, 1],
      [63, 22.5, 1], [75, 15.5, 1], [70.5, 30, 1], [82, 30, 1], [74, 41, 1], [75, 52], [73, 64], [69, 80, 1],
    ], true), { light: 0.55 });
    P.solid(D.leaf(35, 33, 50, 27.5, 7.5), { light: 0.5 });
    P.ink(D.ellipse(13.9, 51.8, 2.9, 5.5));
    P.solid(D.ellipse(13.9, 51.8, 2.4, 4.9), { shade: false, line: false });
    P.ink(D.ellipse(13.6, 49.6, 0.9, 1.3)).ink(D.ellipse(13.6, 54, 0.9, 1.3));
    P.eye(D.poly([[27, 43], [33.5, 39], [33, 43.2]]));
    P.line('M17,59C21,60 25.5,59.5 29,57.5M19.5,45.5C21,47.5 21,50 20,52');
    P.solid(D.curve([[21, 60.5, 1], [18, 53], [17.5, 44], [20.5, 35, 1], [22.5, 44], [24.5, 52], [27, 58.5, 1]], true), { light: 0.5 });
  };

  // A hulking troll, knuckles down, its head sunk between its shoulders:
  // a shelf of a brow over glinting eyes, a slab of a nose, and two tusks
  // jutting from an underbite.
  A.troll = function (P, D) {
    P.base('wide');
    P.solid(D.lathe([[50, 21], [36, 22], [24.5, 28], [17, 39], [14.5, 52], [16, 66], [21, 78, 1], [50, 78]]), { light: 0.62 });
    const fist = D.curve([[17, 79, 1], [15, 72], [17.5, 65], [24, 62], [31, 63.5], [34.5, 69], [33.5, 79, 1]], true);
    P.solid(fist).solid(D.mx(fist));
    P.line('M22,79L22.5,72M27.5,79L28,71.5M78,79L77.5,72M72.5,79L72,71.5');
    P.solid(D.lathe([[50, 17.5], [42, 18], [35.5, 20.5], [32.5, 25, 1], [36.5, 29.5], [37, 38], [40.5, 46.5], [50, 50]]), { light: 0.6 });
    P.ink(D.lathe([[50, 28], [40, 26.5], [37.5, 29.5, 1], [42, 33.5], [50, 32.5]]));
    P.eye(D.ellipse(43, 30, 1.9, 1.6)).eye(D.ellipse(57, 30, 1.9, 1.6));
    P.solid(D.curve([[50, 27, 1], [54.5, 35], [54, 40], [50, 41.5], [46, 40], [45.5, 35]], true), { light: 0.55 });
    P.ink(D.lathe([[50, 43.5], [41, 44.5, 1], [43.5, 46.8], [50, 47.8]]));
    const tusk = D.curve([[40.8, 47.5, 1], [40, 40.5], [41.8, 34, 1], [45, 40], [45.2, 47.8, 1]], true);
    P.flat(tusk).flat(D.mx(tusk));
  };

  // A goblin in a horned helmet, a cleaver raised behind it.
  A.goblinChief = function (P, D) {
    P.base('std');
    P.flat(limb(D, [[73, 30], [71, 52]], 4.4, 4.4));
    P.solid(D.curve([[70.5, 30.5, 1], [70, 9.5, 1], [84, 7], [86.5, 9.5, 1], [87.5, 27, 1], [78.5, 29.5]], true), { light: 0.6 });
    P.ink(D.circle(75, 13.5, 1.9));
    P.solid(goblinBody(D, 59));
    const T = goblinHead(P, D, 50, 44, 0.88);
    const horn = D.curve([[39, 27, 1], [32.5, 23], [29.5, 16], [31, 7, 1], [34.5, 15], [38.5, 19.5], [42.5, 20.5, 1]], true);
    P.solid(T(horn), { light: 0.5 }).solid(T(D.mx(horn)), { light: 0.5 });
    P.solid(T(D.lathe([[50, 16.5], [43, 17.5], [37.5, 22.5], [35, 29], [34.3, 33.5, 1], [50, 33.5]])), { light: 0.6 });
    P.flat(T(D.curve([[33.5, 30.5, 1], [50, 29.5], [66.5, 30.5, 1], [66.5, 34.5, 1], [50, 33.5], [33.5, 34.5, 1]], true)));
  };

  // The pack leader: the wolf grown huge, with a shaggy mane, bared fangs
  // and a scar across its eye.
  A.alphaWolf = function (P, D) {
    P.base('wide');
    P.solid(D.curve([
      [32, 78, 1], [29, 71], [21, 68, 1], [27, 63], [19, 58, 1], [26, 54.5], [21.5, 51.5], [16, 49, 1],
      [20.5, 46.5], [26, 45, 1], [19.5, 43.5], [13, 41.5, 1], [12.5, 37.5], [16.5, 34.5], [24.5, 31.5], [31, 26.5], [33.5, 21],
      [35, 8, 1], [41.5, 16.5], [45.5, 19, 1], [50, 9, 1], [53, 20], [58, 25], [67, 24, 1], [63, 31], [75, 33, 1],
      [69, 40], [81, 45, 1], [72, 50], [82, 59, 1], [73, 62], [79, 72, 1], [71, 73], [70, 78, 1],
    ], true), { light: 0.55 });
    P.ink(D.poly([[36.2, 12.5], [39.5, 18.5], [35.6, 20]]));
    P.eye(D.poly([[26, 32], [30, 29.3], [34.5, 28.5], [32, 32]]));
    P.ink(D.ellipse(14.4, 38.5, 2.3, 1.9));
    P.flat(D.poly([[18, 43.3], [21.5, 44.1], [19.5, 47.6]]));
    P.accLine('M27,25L35,36');
    P.line('M37,26C44,30 48,38 50,47M54,34C58,42 59,50 59,59M31,58C36,62 38,68 39,74');
  };

  // Eight long legs round a great round abdomen marked with an hourglass,
  // and a cluster of eyes over the fangs.
  A.broodMother = function (P, D) {
    P.base('wide');
    P.solid(D.ellipse(50, 33, 22, 19), { light: 0.6 });
    P.acc(D.poly([[45, 23], [55, 23], [50, 31.5]])).acc(D.poly([[50, 31.5], [55, 40], [45, 40]]));
    for (const leg of [
      [[41, 52], [23.5, 27, 1], [14, 53]], [[40, 56], [17.5, 41, 1], [13.5, 78]],
      [[41, 60], [22, 56, 1], [19, 83]], [[43, 63], [31, 65, 1], [29, 84]],
    ]) P.pair(limb(D, leg, 4.6, 1.8), 'solid', { light: 0.5 });
    P.solid(D.ellipse(50, 57, 13.5, 11), { light: 0.6 });
    const fang = D.curve([[45, 65, 1], [43, 70], [45.5, 75, 1], [47, 70.5], [49, 66, 1]], true);
    P.flat(fang).flat(D.mx(fang));
    P.eye(D.circle(45.5, 55, 2.5)).eye(D.circle(54.5, 55, 2.5));
    P.eye(D.circle(40.5, 51, 1.4)).eye(D.circle(59.5, 51, 1.4)).eye(D.circle(46, 49.5, 1.3)).eye(D.circle(54, 49.5, 1.3));
  };

  // A small spider squatting on its legs.
  A.spiderling = function (P, D) {
    P.base('low');
    P.ball(50, 57, 11.5);
    for (const leg of [
      [[44.5, 66], [29, 51, 1], [20, 70]], [[44, 69], [24, 62, 1], [18, 85]],
      [[44, 72], [29, 71, 1], [26, 88]], [[45, 74], [36, 77, 1], [34, 89]],
    ]) P.pair(limb(D, leg, 3.6, 1.4), 'solid', { light: 0.5 });
    P.solid(D.ellipse(50, 71, 9, 7.2), { light: 0.6 });
    P.eye(D.circle(46.8, 70, 1.9)).eye(D.circle(53.2, 70, 1.9));
    P.eye(D.circle(43.8, 67.3, 1.1)).eye(D.circle(56.2, 67.3, 1.1));
  };

  // King Grumblewart: a fat goblin in a big crown, before a high throne.
  A.goblinKing = function (P, D) {
    P.base('wide');
    P.solid(D.lathe([[50, 5.5], [40, 6.5], [31, 10.5], [25, 17.5], [22.5, 27.5], [22, 78, 1], [50, 78]]), { light: 0.6 });
    P.ball(50, 8, 3.6);
    P.ball(19, 48, 5).ball(81, 48, 5);
    P.flat(D.rect(15.5, 52, 7, 26)).flat(D.rect(77.5, 52, 7, 26));
    P.solid(D.lathe([[50, 45], [40, 46], [31, 52], [27, 62], [28.5, 72], [32, 78, 1], [50, 78]]), { light: 0.6 });
    P.line('M30,65C40,69 60,69 70,65');
    const T = goblinHead(P, D, 50, 41, 0.84);
    P.solid(T(D.curve([[36, 28.5, 1], [33.5, 8, 1], [42, 17], [50, 3, 1], [58, 17], [66.5, 8, 1], [64, 28.5, 1],
      [50, 26.5]], true)), { light: 0.6 });
    P.acc(T(D.circle(50, 21.5, 2.6))).acc(T(D.circle(41, 23.5, 1.8))).acc(T(D.circle(59, 23.5, 1.8)));
  };

  // --------------------------------------------------------------- act II
  // A zombie: a lolling, stitched head with a slack jaw, one arm reaching out.
  A.zombie = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 50], [42, 51], [37, 57], [34, 67], [33, 80, 1], [50, 80]]));
    P.solid(limb(D, [[42, 58], [31, 52.5], [21, 47.5]], 8.5, 6.5), { light: 0.5 });
    P.solid(D.curve([[22.5, 43.5, 1], [16.5, 43.5], [13.5, 46.5], [13, 52.5, 1], [15.5, 49.5], [16.5, 54.5, 1],
      [18.5, 50.5], [20.5, 54, 1], [21.5, 50], [23.5, 51.5, 1]], true), { light: 0.5 });
    const R = (d) => rot(d, 15, 52, 34);
    P.heavy(R('M46,20L44,13M53,19.5L55.5,12.5'));
    P.solid(R(D.curve([[47, 19], [53, 20.5, 1], [59, 19], [64, 24], [65.5, 32], [63.5, 40], [60, 46], [60.5, 52],
      [55.5, 55.5], [47.5, 54], [43, 47.5], [38.5, 41], [37.5, 31], [40.5, 23]], true)), { light: 0.6 });
    P.ink(R(D.circle(45.5, 33, 4.2))).eye(R(D.circle(45.5, 33.4, 2))).eye(R(D.circle(57, 34, 1.9)));
    P.ink(R(D.curve([[45.5, 43.5, 1], [57, 42.5, 1], [57.5, 48], [53, 51.5], [48, 50]], true)));
    P.line(R('M40.5,26L61,24M45,23.5L45.8,28.3M50,23L50.8,27.6M55,22.5L55.8,27M48.5,43.4L49.5,46.4M53,43.2L53.6,46'));
  };

  // A sheet ghost, arms up, trailing away in a wisp.
  A.ghost = function (P, D) {
    P.base('std');
    P.solid(D.curve([
      [50, 13], [41.5, 15], [35.5, 21.5], [33, 31], [32.5, 40], [27, 41.5], [20, 38, 1], [23.5, 45], [31, 50],
      [32, 57], [36, 64], [43, 70], [51, 74.5], [58, 79.5, 1], [60, 73], [64, 66.5], [67.5, 58], [69, 50],
      [76.5, 45], [80, 38, 1], [73, 41.5], [67.5, 40], [67, 31], [64.5, 21.5], [58.5, 15],
    ], true), { light: 0.6 });
    P.eye(D.ellipse(44, 30, 3, 4.6)).eye(D.ellipse(56, 30, 3, 4.6));
    P.eye(D.ellipse(50, 41.5, 2.6, 3.4));
    P.line('M40,58C44,63 48,66 53,68M61,55C62,61 61,66 59,71');
  };

  // A cultist: a deep cowl with nothing inside but two eyes, a candle held
  // up in both hands.
  A.cultist = function (P, D) {
    P.base('std');
    P.solid(D.lathe([[50, 46], [42, 48], [38, 56], [35, 66], [32, 80, 1], [50, 80]]));
    P.solid(D.lathe([[50, 12], [43, 13.5], [37.5, 18.5], [34.5, 26], [34, 35], [33, 44], [30, 51, 1], [40, 53], [50, 53.5]]), { light: 0.6 });
    P.ink(D.lathe([[50, 20.5], [44.5, 22.5], [42, 27.5], [42, 33.5], [44.5, 38], [50, 40]]));
    const eye = D.poly([[44, 28.5], [48.5, 30.2], [47.8, 32.4], [44.4, 31.2]]);
    P.eye(eye).eye(D.mx(eye));
    P.column(50, 54, 66, 7, 7);
    P.solid(D.curve([[36.5, 67, 1], [39.5, 62], [50, 63], [60.5, 62], [63.5, 67, 1], [60.5, 71.5], [50, 72], [39.5, 71.5]], true), { light: 0.6 });
    P.line('M50,63.5L50,71.5');
    P.flat(D.flame(50, 54.5, 10, 13.5, 1), 'e');
  };

  // A skeleton archer: a skull on a ribcage, a longbow at its side with an
  // arrow on the string.
  A.boneArcher = function (P, D) {
    P.base('std');
    P.column(50, 63, 79, 7, 19);
    P.solid(D.lathe([[50, 46], [42, 47], [37, 51.5], [36, 57.5], [39, 63], [44, 66], [50, 66.5]]), { light: 0.6 });
    P.line('M50,48L50,64M39.5,54C43,52 46,52 48,53.5M38.5,59C42,57 45.5,57 48,58.5M60.5,54C57,52 54,52 52,53.5M61.5,59C58,57 54.5,57 52,58.5');
    P.column(50, 41, 47.5, 6, 7);
    P.skull(50, 28.5, 1);
    P.solid(D.curve([[30, 12.5, 1], [20, 21.5], [14.5, 42], [20, 62.5], [30, 71.5, 1], [30.5, 68.5, 1], [23.5, 61],
      [19, 42], [23.5, 23], [30.5, 15.5, 1]], true), { light: 0.5 });
    P.line('M30.5,14L30.5,70');
    P.flat(D.rect(16.5, 41.1, 14.5, 1.8));
    P.flat(D.poly([[13, 42], [18.5, 38.8], [17.5, 42], [18.5, 45.2]]));
    P.flat(D.poly([[27, 41], [31.5, 37.5], [31.5, 41]])).flat(D.poly([[27, 43], [31.5, 46.5], [31.5, 43]]));
  };

  // A banshee: a gaunt face wailing, hair streaming up and away like smoke,
  // the rest of her a wisp curling down to the pedestal.
  A.banshee = function (P, D) {
    P.base('std');
    P.solid(limb(D, [[52, 48], [58, 59], [54, 70], [45, 79]], 18, 3), { light: 0.6 });
    P.solid(D.curve([[40, 44, 1], [36.5, 34], [37, 24], [42, 16.5], [50, 11], [61, 5, 1], [59, 12], [70, 10.5],
      [80, 12, 1], [73, 17], [82, 22.5], [87, 29, 1], [78, 29], [83, 38], [83, 45, 1], [75, 40.5], [66, 41],
      [58, 44, 1]], true), { light: 0.6 });
    P.solid(D.lathe([[50, 21], [44.5, 22], [41, 27.5], [40.5, 36], [42.5, 45], [46.5, 51], [50, 52.5]]), { light: 0.6 });
    const eye = D.poly([[42.5, 32.5], [47.5, 31], [47.8, 34.6], [43.5, 35.6]]);
    P.ink(eye).ink(D.mx(eye));
    P.eye(D.circle(45.6, 33.6, 1.1)).eye(D.circle(54.4, 33.6, 1.1));
    P.eye(D.ellipse(50, 44.5, 3.3, 5.3));
    P.accLine('M34,37.5C31.5,41.5 31.5,47.5 34,51.5M28,34.5C24.5,40.5 24.5,48.5 28,54.5');
  };

  // The gravecaller: a ragged cloak with a lantern for a head and a captive
  // soul burning inside it.
  A.gravecaller = function (P, D) {
    P.base('std');
    P.solid(D.curve([[50, 46, 1], [40, 47], [34, 52], [32, 62], [29.5, 72], [28, 80, 1], [33, 76.5, 1], [37.5, 80.5, 1],
      [42.5, 77, 1], [47.5, 81, 1], [52.5, 77, 1], [57.5, 81, 1], [62.5, 77, 1], [67, 80.5, 1], [72, 80, 1],
      [70.5, 72], [68, 62], [66, 52], [60, 47]], true));
    P.collar(50, 47.5, 11, 3);
    P.heavy(D.circle(50, 11.5, 3.2));
    P.solid(D.lathe([[50, 14.5], [46, 15.5], [41.5, 19.5], [38.5, 22.5, 1], [50, 22.5]]), { light: 0.6 });
    P.solid(D.lathe([[50, 24], [41, 24, 1], [40, 34], [41.5, 42.5, 1], [50, 42.5]]), { light: 0.6 });
    P.eye(D.flame(50, 40.5, 12, 15, 0));
    P.ink(D.circle(47.4, 34.8, 1.2)).ink(D.circle(52.6, 34.8, 1.2));
    P.flat(D.rect(38, 22, 24, 3)).flat(D.rect(38, 42, 24, 3));
    P.flat(D.rect(39, 25, 3.2, 17)).flat(D.rect(57.8, 25, 3.2, 17));
  };

  // A death knight: the chess knight's horse in a skull-faced helm, with a
  // horn swept back and a crest of blades down its neck.
  A.deathKnight = function (P, D) {
    P.base('wide');
    P.solid(D.curve([
      [30, 78, 1], [31.5, 66], [34.5, 58], [27, 55.5], [19, 53], [13.5, 49.5, 1], [12.5, 43], [15, 37.5, 1],
      [22, 32], [27, 25.5], [31, 19], [33, 4, 1], [41, 15, 1], [45, 15, 1], [52, 5, 1], [54, 16, 1], [64, 10, 1],
      [62, 24, 1], [73, 22, 1], [67, 34, 1], [79, 37, 1], [70, 45, 1], [78, 54, 1], [70.5, 57, 1], [71, 68], [70, 78, 1],
    ], true), { light: 0.55 });
    P.solid(D.curve([[31.5, 20, 1], [37.5, 24], [38, 33], [32, 40], [24, 46.5], [16, 48.5, 1], [14, 41.5],
      [19, 34.5], [25.5, 27.5]], true), { light: 0.6 });
    P.ink(D.poly([[25.5, 30.5], [33.5, 27.5], [34.5, 33], [28, 35]]));
    P.acc(D.circle(30.5, 31.3, 1.6));
    P.ink(D.poly([[15.5, 39.5], [19, 38.5], [18, 42]]));
    P.ink(D.poly([[14.5, 50], [28, 52.5], [27, 55], [15.5, 52.5]]));
    P.line('M38.5,27C46,31 51,40 53,52M52,22C59,29 63,39 64,50M21.5,50.5L21,53.2M25,51.2L24.6,54');
  };

  // The bone colossus: a great skull sunk between two shoulder joints, over
  // a barrel of ribs.
  A.boneColossus = function (P, D) {
    P.base('wide');
    P.solid(D.lathe([[50, 38], [39, 39], [31, 44], [28, 54], [30, 65], [36, 74], [41, 78, 1], [50, 78]]), { light: 0.6 });
    for (const y of [50, 58.5, 67]) P.pair(D.curve([[46, y, 1], [38, y - 1.8], [32.5, y + 1.5, 1], [38, y + 0.8], [46, y + 2.4, 1]], true), 'ink');
    P.flat(D.rect(46.5, 43, 7, 29));
    const spike = D.poly([[18, 38], [13, 25], [25, 33]]);
    P.solid(spike, { light: 0.5 }).solid(D.mx(spike), { light: 0.5 });
    const arm = limb(D, [[23, 50], [19.5, 64], [18.5, 78]], 8, 6.5);
    P.solid(arm, { light: 0.5 }).solid(D.mx(arm), { light: 0.5 });
    P.ball(24, 43, 11).ball(76, 43, 11);
    P.skull(50, 27, 1.3);
    P.acc(D.circle(44, 27.8, 1.8)).acc(D.circle(56, 27.8, 1.8));
  };

  // The vampire lord: bat wings spread behind a high-collared cape, a
  // widow's peak, fangs, and a blood-red stone at the throat.
  A.vampireLord = function (P, D) {
    P.base('wide');
    P.pair(D.batWing(41, 44, 29, 36, 3), 'solid', { light: 0.6 });
    P.solid(D.lathe([[50, 42], [42, 43], [37, 50], [33, 63], [28, 78, 1], [50, 78]]));
    P.pair(D.curve([[43.5, 46, 1], [37, 38], [35, 24, 1], [42, 31], [47.5, 40, 1]], true), 'solid', { light: 0.5 });
    P.solid(D.lathe([[50, 19], [44.5, 20], [41, 25], [40.5, 32], [43, 39], [47, 43], [50, 44]]), { light: 0.6 });
    P.pair(D.poly([[41.2, 28.5], [35, 23.5], [41.6, 33]]), 'flat');
    P.ink(D.curve([[40.8, 27, 1], [41.5, 21], [46, 17.5], [50, 17], [54, 17.5], [58.5, 21], [59.2, 27, 1], [56, 23.5],
      [50, 29, 1], [44, 23.5]], true));
    const eye = D.poly([[43.5, 31], [48.5, 32.5], [48, 34.5], [44, 33.5]]);
    P.eye(eye).eye(D.mx(eye));
    P.pair(D.poly([[46.2, 38.5], [48.6, 38.5], [47.4, 41.8]]), 'flat');
    P.acc(D.regular(50, 48.5, 3.4, 4));
  };

  // A bat, wings spread, perched on its pedestal.
  A.bat = function (P, D) {
    P.base('low');
    P.pair(D.batWing(45, 67, 31, 32, 3), 'solid', { light: 0.6 });
    P.solid(D.ellipse(50, 71, 7, 10), { light: 0.6 });
    P.pair(D.poly([[45.5, 53], [43.5, 43.5], [49.5, 51]]), 'solid', { light: 0.5 });
    P.solid(D.circle(50, 57, 6.5), { light: 0.6 });
    P.eye(D.circle(47.4, 56, 1.4)).eye(D.circle(52.6, 56, 1.4));
    P.pair(D.poly([[47.6, 60.4], [49.4, 60.4], [48.5, 63]]), 'flat');
  };

  // Morvane the Lich: a crowned skull in a spiked collar, robed, with a
  // staff that cradles a soul-orb.
  A.lich = function (P, D) {
    P.base('std');
    P.flat(D.rect(68.5, 22, 4, 64));
    P.solid(D.crescent(70.5, 15, 8, 0.9, -90), { light: 0.5 });
    P.flat(D.circle(70.5, 15.5, 5), 'a');
    P.solid(D.lathe([[50, 44], [41, 45], [36, 52], [33, 64], [31, 80, 1], [50, 80]]));
    P.solid(D.lathe([[50, 36], [45, 37], [41.5, 26, 1], [39, 37], [32, 30, 1], [33.5, 41], [28, 41, 1], [34, 47.5],
      [40, 50.5], [50, 51]]), { light: 0.6 });
    P.skull(50, 31, 0.95);
    P.solid(D.curve([[40, 24.5, 1], [38.5, 11, 1], [44, 17.5], [50, 7.5, 1], [56, 17.5], [61.5, 11, 1], [60, 24.5, 1],
      [50, 22.5]], true), { light: 0.6 });
    P.eye(D.circle(50, 18.5, 1.5)).eye(D.circle(43.5, 21.5, 1.1)).eye(D.circle(56.5, 21.5, 1.1));
  };

  // The phylactery: a skull-capped urn on a broken slab, a soul-gem set in
  // its belly.
  A.phylactery = function (P, D) {
    P.base('none');
    P.solid(D.curve([[19, 96, 1], [18.5, 91], [24, 87.5], [36, 85.5], [50, 85], [64, 85.5], [76, 87.5], [81.5, 91],
      [81, 96, 1]], true), { light: 0.62 });
    P.line('M33,87.5L36,92L34,95.5M66,87L63,91.5');
    P.solid(D.lathe([[50, 33], [42.5, 33, 1], [42.5, 35.5, 1], [44.5, 38.5], [40, 44], [33, 51], [30, 60], [32, 69],
      [38, 75.5], [41.5, 78], [38, 86, 1], [50, 86]]), { light: 0.6 });
    P.solid(D.lathe([[50, 22], [46, 23], [42, 27.5], [40.5, 33.5, 1], [50, 33.5]]), { light: 0.6 });
    P.skull(50, 16.5, 0.42);
    P.line('M33.5,51C44,54 56,54 66.5,51M33,69C44,72 56,72 67,69');
    P.flat(D.poly([[50, 50], [57, 60], [50, 70], [43, 60]]), 'e');
    P.line('M43,60L57,60M50,50L47,60L50,70M50,50L53,60L50,70');
  };
})(globalThis.AG = globalThis.AG || {});
