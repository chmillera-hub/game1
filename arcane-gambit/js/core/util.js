/* Arcane Gambit — shared helpers. Every file attaches to the global AG namespace
   so the engine runs both in the browser and headless under Node for tests. */
(function (AG) {
  'use strict';

  // Small, fast, seedable PRNG (mulberry32). Combat itself is deterministic;
  // this drives map generation, rewards, shops and events.
  function RNG(seed) {
    this.s = (seed >>> 0) || 1;
  }
  RNG.prototype.next = function () {
    let t = (this.s = (this.s + 0x6d2b79f5) >>> 0);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  RNG.prototype.int = function (lo, hi) {
    return lo + Math.floor(this.next() * (hi - lo + 1));
  };
  RNG.prototype.chance = function (p) {
    return this.next() < p;
  };
  RNG.prototype.pick = function (arr) {
    return arr[Math.floor(this.next() * arr.length)];
  };
  RNG.prototype.shuffle = function (arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(this.next() * (i + 1));
      const t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  };
  RNG.prototype.weighted = function (items, weightOf) {
    let total = 0;
    for (const it of items) total += Math.max(0, weightOf(it));
    if (total <= 0) return items[0];
    let r = this.next() * total;
    for (const it of items) {
      r -= Math.max(0, weightOf(it));
      if (r <= 0) return it;
    }
    return items[items.length - 1];
  };
  AG.RNG = RNG;

  AG.clamp = function (v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; };
  AG.cheb = function (ax, ay, bx, by) { return Math.max(Math.abs(ax - bx), Math.abs(ay - by)); };
  AG.manh = function (ax, ay, bx, by) { return Math.abs(ax - bx) + Math.abs(ay - by); };
  AG.sign = function (v) { return v > 0 ? 1 : v < 0 ? -1 : 0; };

  AG.DIRS8 = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]];
  AG.DIRS4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  AG.DIAG = [[1, 1], [1, -1], [-1, 1], [-1, -1]];
  AG.KNIGHT = [[1, 2], [2, 1], [-1, 2], [-2, 1], [1, -2], [2, -1], [-1, -2], [-2, -1]];

  AG.dirsFor = function (kind) {
    if (kind === 'orth') return AG.DIRS4;
    if (kind === 'diag') return AG.DIAG;
    return AG.DIRS8;
  };

  // Chess-style square names: files a.. from the left, ranks 1.. from the
  // player's (bottom) edge.
  AG.squareName = function (board, x, y) {
    return String.fromCharCode(97 + x) + (board.h - y);
  };

  AG.plural = function (n, word) { return n + ' ' + word + (n === 1 ? '' : 's'); };

  AG.deepCopy = function (o) { return o == null ? o : JSON.parse(JSON.stringify(o)); };
})(globalThis.AG = globalThis.AG || {});
