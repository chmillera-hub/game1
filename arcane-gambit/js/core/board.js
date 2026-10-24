/* Board geometry: parsing ASCII maps, terrain, line of sight, distance fields. */
(function (AG) {
  'use strict';

  const FLOOR = 0, WALL = 1, PIT = 2, VOID = 3;
  AG.TER = { FLOOR, WALL, PIT, VOID };

  /* Map legend:
       .  floor            p  floor you may deploy on
       #  wall/pillar      ~  chasm (flyers cross it, line of sight passes over it)
       (space) off-board   any other letter: an enemy from the encounter's legend */
  AG.parseBoard = function (rows, legend) {
    legend = legend || {};
    const h = rows.length;
    let w = 0;
    for (const r of rows) w = Math.max(w, r.length);
    const n = w * h;
    const terr = new Uint8Array(n).fill(VOID);
    const deploy = new Uint8Array(n);
    const spawns = [];
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const ch = rows[y][x] || ' ';
        const i = y * w + x;
        if (ch === '.') terr[i] = FLOOR;
        else if (ch === 'p') { terr[i] = FLOOR; deploy[i] = 1; }
        else if (ch === '#') terr[i] = WALL;
        else if (ch === '~') terr[i] = PIT;
        else if (ch === ' ') terr[i] = VOID;
        else {
          terr[i] = FLOOR;
          const spec = legend[ch];
          if (!spec) throw new Error('Map letter "' + ch + '" has no legend entry');
          spawns.push(Object.assign({ x, y }, typeof spec === 'string' ? { def: spec } : spec));
        }
      }
    }
    const board = { w, h, n, terr, deploy };
    computeFar(board);
    computeLOS(board);
    return { board, spawns };
  };

  // Promotion rows: the enemy's back rank (topmost rank with floor) for the
  // player, and the player's back rank (bottommost) for the enemy.
  function computeFar(b) {
    b.farP = new Uint8Array(b.n);
    b.farE = new Uint8Array(b.n);
    let top = -1, bot = -1;
    for (let i = 0; i < b.n; i++) {
      if (b.terr[i] !== FLOOR) continue;
      const y = (i / b.w) | 0;
      if (top < 0 || y < top) top = y;
      if (y > bot) bot = y;
    }
    for (let x = 0; x < b.w; x++) {
      if (top >= 0 && b.terr[top * b.w + x] === FLOOR) b.farP[top * b.w + x] = 1;
      if (bot >= 0 && b.terr[bot * b.w + x] === FLOOR) b.farE[bot * b.w + x] = 1;
    }
  }

  // Line of sight between square centres. Only walls block sight; units and
  // chasms do not. Sampling at k/N from both ends makes it symmetric.
  function computeLOS(b) {
    const n = b.n, w = b.w;
    const los = new Uint8Array(n * n);
    for (let a = 0; a < n; a++) {
      if (b.terr[a] === WALL) continue;
      los[a * n + a] = 1;
      const ax = a % w, ay = (a / w) | 0;
      for (let c = a + 1; c < n; c++) {
        if (b.terr[c] === WALL) continue;
        const cx = c % w, cy = (c / w) | 0;
        const steps = Math.max(Math.abs(cx - ax), Math.abs(cy - ay)) * 4;
        let clear = true;
        for (let k = 1; k < steps; k++) {
          const t = k / steps;
          const px = Math.floor(ax + 0.5 + (cx - ax) * t);
          const py = Math.floor(ay + 0.5 + (cy - ay) * t);
          const i = py * w + px;
          if (i !== a && i !== c && b.terr[i] === WALL) { clear = false; break; }
        }
        if (clear) { los[a * n + c] = 1; los[c * n + a] = 1; }
      }
    }
    b.los = los;
  }

  AG.inBounds = function (b, x, y) { return x >= 0 && y >= 0 && x < b.w && y < b.h; };

  // Can a unit stand on square i? Flyers may hover over chasms.
  AG.standable = function (b, i, flying) {
    const t = b.terr[i];
    return t === FLOOR || (t === PIT && flying);
  };

  // Can a walker/flyer step from (x,y) by (dx,dy)? Diagonal steps may not
  // squeeze between two walls.
  AG.canStep = function (b, x, y, dx, dy) {
    const nx = x + dx, ny = y + dy;
    if (!AG.inBounds(b, nx, ny)) return false;
    if (dx !== 0 && dy !== 0) {
      const t1 = b.terr[y * b.w + nx], t2 = b.terr[ny * b.w + x];
      if ((t1 === WALL || t1 === VOID) && (t2 === WALL || t2 === VOID)) return false;
    }
    return true;
  };

  // Steps-to-reach field (8-directional) from a square, ignoring units.
  AG.distField = function (b, from, flying) {
    const d = new Int16Array(b.n).fill(999);
    const q = new Int16Array(b.n);
    let qh = 0, qt = 0;
    d[from] = 0; q[qt++] = from;
    while (qh < qt) {
      const i = q[qh++];
      const x = i % b.w, y = (i / b.w) | 0;
      for (const [dx, dy] of AG.DIRS8) {
        if (!AG.canStep(b, x, y, dx, dy)) continue;
        const j = (y + dy) * b.w + (x + dx);
        if (d[j] !== 999) continue;
        const t = b.terr[j];
        if (t === WALL || t === VOID) continue;
        // Targets can stand on chasm squares only if they fly; we still let the
        // field pass through for flyers, and mark chasms reachable-but-costly.
        if (t === PIT && !flying) continue;
        d[j] = d[i] + 1;
        q[qt++] = j;
      }
    }
    return d;
  };
})(globalThis.AG = globalThis.AG || {});
