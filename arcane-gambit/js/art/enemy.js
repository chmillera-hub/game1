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
    P.flat(D.curve([[22.5, 87, 1], [26.5, 87, 1], [27.5, 55], [26.5, 20, 1], [23, 20, 1], [23.5, 55]], true));
    P.solid(D.curve([[11, 23, 1], [13, 15], [19.5, 10], [25, 9], [31, 10.5], [36.5, 15.5], [39, 23, 1]], true), { light: 0.6 });
    P.eye(D.circle(18, 17, 1.8)).eye(D.circle(25.5, 13.2, 1.6)).eye(D.circle(31.5, 18, 1.8));
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
      [34, 80, 1], [32.5, 71], [27, 65.5], [19.5, 62.5], [14, 61.5, 1], [15.5, 58.5, 1], [11.5, 57.5, 1], [10, 51.5],
      [11.5, 46, 1], [19, 43.5], [27, 39], [33, 32], [38.5, 27], [44, 24, 1], [52, 7, 1], [53.5, 20, 1], [64, 8, 1],
      [63, 22.5, 1], [75, 15.5, 1], [70.5, 30, 1], [82, 30, 1], [74, 41, 1], [75, 52], [73, 64], [69, 80, 1],
    ], true), { light: 0.55 });
    P.solid(D.leaf(35, 33, 50, 27.5, 7.5), { light: 0.5 });
    P.ink(D.ellipse(11.4, 51.8, 2.9, 5.5));
    P.solid(D.ellipse(11.4, 51.8, 2.4, 4.9), { shade: false, line: false });
    P.ink(D.ellipse(11.1, 49.6, 0.9, 1.3)).ink(D.ellipse(11.1, 54, 0.9, 1.3));
    P.eye(D.poly([[27, 43], [33.5, 39], [33, 43.2]]));
    P.line('M15.5,58.5C20,59.5 25,59 29,57M17,45.5C18.5,47.5 18.5,50 17.5,52');
    P.solid(D.curve([[21, 60.5, 1], [18, 53], [17.5, 44], [20.5, 35, 1], [22.5, 44], [24.5, 52], [27, 58.5, 1]], true), { light: 0.5 });
  };

  // A hulking troll, knuckles down, its head sunk between its shoulders:
  // a shelf of a brow over glinting eyes, a slab of a nose, and two tusks
  // jutting from an underbite.
  A.troll = function (P, D) {
    P.base('wide');
    P.solid(D.lathe([[50, 27], [37, 28], [25.5, 33], [18, 43], [15, 55], [16.5, 67], [21, 78, 1], [50, 78]]), { light: 0.62 });
    const fist = D.curve([[17, 79, 1], [15, 72], [17.5, 65], [24, 62], [31, 63.5], [34.5, 69], [33.5, 79, 1]], true);
    P.solid(fist).solid(D.mx(fist));
    P.line('M22,79L22.5,72M27.5,79L28,71.5M78,79L77.5,72M72.5,79L72,71.5');
    P.solid(D.lathe([[50, 22.5], [42, 23], [35.5, 25.5], [32.5, 30, 1], [36.5, 34.5], [37, 43], [40.5, 51.5], [50, 55]]), { light: 0.6 });
    P.ink(D.lathe([[50, 33], [40, 31.5], [37.5, 34.5, 1], [42, 38.5], [50, 37.5]]));
    P.eye(D.ellipse(43, 35, 1.9, 1.6)).eye(D.ellipse(57, 35, 1.9, 1.6));
    P.solid(D.curve([[50, 32, 1], [54.5, 40], [54, 45], [50, 46.5], [46, 45], [45.5, 40]], true), { light: 0.55 });
    P.ink(D.lathe([[50, 48.5], [41, 49.5, 1], [43.5, 51.8], [50, 52.8]]));
    const tusk = D.curve([[40.8, 52.5, 1], [40, 45.5], [41.8, 39, 1], [45, 45], [45.2, 52.8, 1]], true);
    P.flat(tusk).flat(D.mx(tusk));
  };

  // A goblin in a horned helmet, a cleaver raised behind it.
  A.goblinChief = function (P, D) {
    P.base('std');
    P.flat(limb(D, [[74.5, 30], [72.5, 52]], 4.4, 4.4));
    P.solid(D.curve([[72, 30.5, 1], [71.5, 9.5, 1], [85.5, 7], [88, 9.5, 1], [89, 27, 1], [80, 29.5]], true), { light: 0.6 });
    P.ink(D.circle(76.5, 13.5, 1.9));
    P.solid(goblinBody(D, 59));
    const T = goblinHead(P, D, 50, 44, 0.88);
    const horn = D.curve([[39, 27, 1], [32.5, 23], [29.5, 16], [31, 7, 1], [34.5, 15], [38.5, 19.5], [42.5, 20.5, 1]], true);
    P.solid(T(horn), { light: 0.5 }).solid(T(D.mx(horn)), { light: 0.5 });
    P.solid(T(D.lathe([[50, 16.5], [43, 17.5], [37.5, 22.5], [35, 29], [34.3, 33.5, 1], [50, 33.5]])), { light: 0.6 });
    P.flat(T(D.curve([[33.5, 30.5, 1], [50, 29.5], [66.5, 30.5, 1], [66.5, 34.5, 1], [50, 33.5], [33.5, 34.5, 1]], true)));
  };

  // The pack leader, howling: a bigger wolf with its muzzle thrown back, a
  // great mane, and a scar across its eye.
  A.alphaWolf = function (P, D) {
    P.base('wide');
    P.solid(D.curve([
      [31, 78, 1], [28, 70], [21.5, 66, 1], [27.5, 61.5], [21, 55, 1], [27.5, 51], [27.5, 44], [23.5, 37],
      [12.5, 25, 1], [21, 26.5], [31, 31.5, 1], [23, 20], [16, 10.5, 1], [17.5, 5.5], [21.5, 5], [28, 10], [35, 14],
      [39.5, 13.5], [45, 3.5, 1], [46.5, 13], [55.5, 8, 1], [53, 18], [56, 25], [65, 25, 1], [61, 31.5],
      [73, 36, 1], [67, 43], [79, 51, 1], [70.5, 55], [77.5, 66, 1], [70.5, 69], [70, 78, 1],
    ], true), { light: 0.55 });
    P.ink(D.poly([[45.3, 8], [45.5, 14], [42, 14.5]]));
    P.ink(D.ellipse(18.4, 7.6, 2.2, 1.9));
    P.eye(D.poly([[29.5, 17.5], [36.5, 17], [35, 19.8]]));
    P.accLine('M29,12L36.5,24');
    P.flat(D.poly([[22.8, 20.5], [26.4, 23.4], [22.6, 24.6]]));
    P.line('M41,20C45,28 47,36 49,45M53,27C57,35 59,44 59,54M34,49C38,55 40,62 40,70');
  };
  A.alphaWolfB = function (P, D) {
    P.base('wide');
    P.solid(D.curve([
      [32, 78, 1], [29, 71], [21, 68, 1], [27, 63], [19, 58, 1], [26, 54.5], [21, 51.5], [14.5, 49, 1],
      [19.5, 46.5], [26, 45, 1], [18, 43.5], [10.5, 41.5, 1], [10, 37.5], [15, 34.5], [24.5, 31.5], [31, 26.5], [33.5, 21],
      [35, 8, 1], [41.5, 16.5], [45.5, 19, 1], [50, 9, 1], [53, 20], [58, 25], [67, 24, 1], [63, 31], [75, 33, 1],
      [69, 40], [81, 45, 1], [72, 50], [82, 59, 1], [73, 62], [79, 72, 1], [71, 73], [70, 78, 1],
    ], true), { light: 0.55 });
    P.ink(D.poly([[36.2, 12.5], [39.5, 18.5], [35.6, 20]]));
    P.eye(D.poly([[26, 32], [30, 29.3], [34.5, 28.5], [32, 32]]));
    P.ink(D.ellipse(12, 38.5, 2.3, 1.9));
    P.flat(D.poly([[16.5, 43], [20, 43.8], [18, 47.4]]));
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
      [[41, 52], [23, 27, 1], [12, 52]], [[40, 56], [16, 42, 1], [11, 78]],
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
    P.solid(D.lathe([[50, 4], [40, 5], [31, 9], [25, 16], [22.5, 26], [22, 78, 1], [50, 78]]), { light: 0.6 });
    P.ball(50, 6.5, 4);
    P.ball(19, 48, 5).ball(81, 48, 5);
    P.flat(D.rect(15.5, 52, 7, 26)).flat(D.rect(77.5, 52, 7, 26));
    P.solid(D.lathe([[50, 45], [40, 46], [31, 52], [27, 62], [28.5, 72], [32, 78, 1], [50, 78]]), { light: 0.6 });
    P.line('M30,65C40,69 60,69 70,65');
    const T = goblinHead(P, D, 50, 41, 0.84);
    P.solid(T(D.curve([[36, 28.5, 1], [33.5, 8, 1], [42, 17], [50, 3, 1], [58, 17], [66.5, 8, 1], [64, 28.5, 1],
      [50, 26.5]], true)), { light: 0.6 });
    P.acc(T(D.circle(50, 21.5, 2.6))).acc(T(D.circle(41, 23.5, 1.8))).acc(T(D.circle(59, 23.5, 1.8)));
  };
})(globalThis.AG = globalThis.AG || {});
