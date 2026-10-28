// Seeded random numbers so runs, maps and battles are reproducible and saveable.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});

  class RNG {
    constructor(seed) {
      this.s = seed >>> 0 || 0x9e3779b9;
    }
    // mulberry32
    next() {
      let t = (this.s = (this.s + 0x6d2b79f5) >>> 0);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }
    int(n) {
      return Math.floor(this.next() * n);
    }
    range(a, b) {
      return a + this.int(b - a + 1);
    }
    chance(p) {
      return this.next() < p;
    }
    pick(arr) {
      return arr[this.int(arr.length)];
    }
    shuffle(arr) {
      for (let i = arr.length - 1; i > 0; i--) {
        const j = this.int(i + 1);
        const t = arr[i];
        arr[i] = arr[j];
        arr[j] = t;
      }
      return arr;
    }
    // entries: [[item, weight], ...]
    weighted(entries) {
      let total = 0;
      for (const e of entries) total += e[1];
      let r = this.next() * total;
      for (const e of entries) {
        r -= e[1];
        if (r < 0) return e[0];
      }
      return entries[entries.length - 1][0];
    }
  }

  function hashStr(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  // A fresh generator derived from a seed and a label, e.g. derive(run.seed, 'map:1').
  function derive(seed, label) {
    return new RNG(hashStr(seed + ':' + label));
  }

  AG.RNG = RNG;
  AG.hashStr = hashStr;
  AG.derive = derive;
})(typeof window !== 'undefined' ? window : globalThis);
