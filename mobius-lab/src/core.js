/*
 * Mobius Lab core: builds paper strips as a mesh, tapes them together,
 * cuts them, and measures what comes out.
 *
 * Nothing in here knows about rendering. It runs in the browser (as the global
 * `MobiusCore`) and in Node (`require('./core.js')`) so it can be tested.
 *
 * How it works
 * ------------
 * 1. Every strip is a loop of paper laid out as a "stadium" (two straight
 *    pieces joined by two half-circles). The straight pieces are flat and
 *    untwisted; all half-twists live on the curved parts. The straight pieces
 *    are exactly one strip-width long, so two strips crossed at right angles
 *    overlap in a perfect square, like a piece of tape holding them.
 * 2. Strips are stacked upward. Strip i's top straight is taped to strip i+1's
 *    bottom straight, either crossed ("orthogonal") or lying along it
 *    ("parallel"). Taping merges the two overlapping patches of mesh into one.
 * 3. A cut is a line a fraction of the way across a strip. On a one-sided strip
 *    that line comes back around on the other side (a 1/3 cut also runs along
 *    2/3), exactly like scissors would. Cut edges are split, which separates
 *    the faces on either side.
 * 4. The pieces are the connected parts of what is left. For each piece we
 *    count faces, edges and vertices (Euler characteristic), edges of the
 *    paper (boundary loops), and check one-sided vs two-sided. Twists come
 *    from the linking number of a paper edge with a copy of itself pushed
 *    slightly into the paper. Interlocking comes from linking numbers between
 *    pieces, and knots from the determinant of the knot diagram.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.MobiusCore = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const WIDTH = 1;
  const RADIUS = 1.25;
  const STRAIGHT = WIDTH;
  const HALF_CIRCLE = Math.PI * RADIUS;
  const LOOP_LENGTH = 2 * STRAIGHT + 2 * HALF_CIRCLE;
  const MAX_STRIPS = 4;
  const MAX_TWISTS = 6;

  // ---------------------------------------------------------------- input --

  function parseFraction(text) {
    const t = String(text).trim();
    let m;
    if ((m = t.match(/^(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)$/))) {
      const d = Number(m[2]);
      return d ? Number(m[1]) / d : null;
    }
    if ((m = t.match(/^(\d+(?:\.\d+)?)\s*%$/))) return Number(m[1]) / 100;
    if (/^\d*\.?\d+$/.test(t)) return Number(t);
    return null;
  }

  function isValidCut(c) {
    return typeof c === 'number' && isFinite(c) && c >= 0.03 && c <= 0.97;
  }

  // Clean up a config: clamp twists, drop bad or duplicate cuts. On a
  // one-sided strip a cut at c and a cut at 1-c are the same cut.
  function normalizeConfig(raw) {
    const strips = (raw.strips || []).slice(0, MAX_STRIPS).map((s) => {
      const k = Math.max(-MAX_TWISTS, Math.min(MAX_TWISTS, Math.round(Number(s.halfTwists) || 0)));
      const odd = Math.abs(k) % 2 === 1;
      const cuts = [];
      for (const c0 of s.cuts || []) {
        if (!isValidCut(c0)) continue;
        const c = odd ? Math.min(c0, 1 - c0) : c0;
        if (!cuts.some((x) => Math.abs(x - c) < 1e-6)) cuts.push(c);
      }
      cuts.sort((a, b) => a - b);
      return { halfTwists: k, cuts };
    });
    if (!strips.length) strips.push({ halfTwists: 1, cuts: [] });
    const joints = [];
    for (let i = 0; i < strips.length - 1; i++) {
      joints.push((raw.joints || [])[i] === 'parallel' ? 'parallel' : 'orthogonal');
    }
    return { strips, joints };
  }

  // ------------------------------------------------------------- geometry --

  // Positions across the strip (0 = one edge, 1 = the other). Shared by every
  // strip so taped patches line up vertex for vertex. Always symmetric, so a
  // patch still lines up when a strip runs the other way through it.
  function acrossSamples(config) {
    const base = 8;
    const special = [0, 1];
    for (const s of config.strips) for (const c of s.cuts) special.push(c, 1 - c);
    const pts = [];
    const add = (x) => {
      if (!pts.some((p) => Math.abs(p - x) < 1e-6)) pts.push(x);
    };
    special.forEach(add);
    const minGap = 0.4 / base;
    for (let i = 1; i < base; i++) {
      const x = i / base;
      if (special.every((p) => Math.abs(p - x) > minGap)) add(x);
    }
    pts.sort((a, b) => a - b);
    const n = pts.length;
    for (let j = 0; j < n / 2; j++) pts[n - 1 - j] = 1 - pts[j];
    return pts;
  }

  // e1: direction of the straight pieces, e2: up, w: across the strip.
  // w = -(e1 x e2) in both planes so a "+1" twist has the same handedness in each.
  function stripFrame(index, plane) {
    const z0 = index * 2 * RADIUS;
    if (plane === 'xz') return { e1: [1, 0, 0], e2: [0, 0, 1], w: [0, 1, 0], z0, plane };
    return { e1: [0, 1, 0], e2: [0, 0, 1], w: [-1, 0, 0], z0, plane };
  }

  function ramp(t) {
    const x = Math.min(1, Math.max(0, (t - 0.12) / 0.76));
    return x * x * (3 - 2 * x);
  }

  // Point on strip at arc length s along the centre line, v across (0..1).
  // Twisting is reversed in sign so that positive half-twists come out
  // right-handed (checked by the tests via linking numbers).
  function stripPoint(frame, k, s, v) {
    const S = STRAIGHT, R = RADIUS, P = HALF_CIRCLE;
    const m = Math.trunc(k / 2);
    let a, b, na, nb, theta;
    if (s < S) {
      a = -S / 2 + s; b = 2 * R; na = 0; nb = -1; theta = 0;
    } else if (s < S + P) {
      const phi = (s - S) / R;
      a = S / 2 + R * Math.sin(phi); b = R + R * Math.cos(phi);
      na = -Math.sin(phi); nb = -Math.cos(phi);
      theta = m * Math.PI * ramp(phi / Math.PI);
    } else if (s < 2 * S + P) {
      a = S / 2 - (s - S - P); b = 0; na = 0; nb = 1; theta = m * Math.PI;
    } else {
      const phi = (s - 2 * S - P) / R;
      a = -S / 2 - R * Math.sin(phi); b = R - R * Math.cos(phi);
      na = Math.sin(phi); nb = Math.cos(phi);
      theta = m * Math.PI + (k - m) * Math.PI * ramp(phi / Math.PI);
    }
    theta = -theta;
    const off = (v - 0.5) * WIDTH;
    const c = Math.cos(theta), sn = Math.sin(theta);
    const { e1, e2, w, z0 } = frame;
    const out = [0, 0, 0];
    for (let i = 0; i < 3; i++) {
      out[i] = a * e1[i] + b * e2[i] + off * (c * w[i] + sn * (na * e1[i] + nb * e2[i]));
    }
    out[2] += z0;
    return out;
  }

  // Positions along a strip. The straight pieces reuse the across samples so
  // a crossed patch is the same grid in both directions.
  function alongSamples(V, k) {
    const S = STRAIGHT, P = HALF_CIRCLE;
    const nArc = 48 + 14 * Math.abs(k);
    const list = [];
    for (let j = 0; j < V.length - 1; j++) list.push({ s: S * V[j], seg: 'top' });
    for (let i = 0; i < nArc; i++) list.push({ s: S + (P * i) / nArc, seg: i === 0 ? 'top' : 'arc' });
    for (let j = 0; j < V.length - 1; j++) list.push({ s: S + P + S * V[j], seg: 'bottom' });
    for (let i = 0; i < nArc; i++) list.push({ s: 2 * S + P + (P * i) / nArc, seg: i === 0 ? 'bottom' : 'arc' });
    return list;
  }

  const edgeKey = (a, b) => (a < b ? a + ',' + b : b + ',' + a);

  class UnionFind {
    constructor(n) {
      this.p = new Int32Array(n);
      for (let i = 0; i < n; i++) this.p[i] = i;
    }
    find(x) {
      const p = this.p;
      while (p[x] !== x) { p[x] = p[p[x]]; x = p[x]; }
      return x;
    }
    union(a, b) {
      a = this.find(a); b = this.find(b);
      if (a !== b) this.p[a] = b;
    }
  }

  // Build the uncut paper: one mesh for all strips, taped patches merged.
  function buildModel(rawConfig) {
    const config = normalizeConfig(rawConfig);
    const V = acrossSamples(config);
    const nV = V.length;
    const N = config.strips.length;
    const pos = [];
    const patch = [];
    const rawFaces = [];
    const rawFaceStrip = [];
    const rawCuts = [];
    const strips = [];
    const cutPaths = [];
    let plane = 'xz';

    config.strips.forEach((st, si) => {
      if (si > 0 && config.joints[si - 1] === 'orthogonal') plane = plane === 'xz' ? 'yz' : 'xz';
      const frame = stripFrame(si, plane);
      const k = st.halfTwists;
      const odd = Math.abs(k) % 2 === 1;
      const U = alongSamples(V, k);
      const nU = U.length;
      const base = pos.length;
      const tapedTop = si < N - 1, tapedBottom = si > 0;
      for (let iu = 0; iu < nU; iu++) {
        const seg = U[iu].seg;
        const inPatch = (seg === 'top' && tapedTop) || (seg === 'bottom' && tapedBottom);
        for (let j = 0; j < nV; j++) {
          pos.push(stripPoint(frame, k, U[iu].s, V[j]));
          patch.push(inPatch);
        }
      }
      const cutIdx = [];
      for (let j = 0; j < nV; j++) {
        if (st.cuts.some((c) => Math.abs(V[j] - c) < 1e-6 || (odd && Math.abs(V[j] - (1 - c)) < 1e-6))) cutIdx.push(j);
      }
      const id = (iu, j) => base + iu * nV + j;
      for (let iu = 0; iu < nU; iu++) {
        const iu2 = (iu + 1) % nU;
        const flip = iu2 === 0 && odd;
        for (let j = 0; j < nV - 1; j++) {
          const j0 = flip ? nV - 1 - j : j;
          const j1 = flip ? nV - 2 - j : j + 1;
          rawFaces.push([id(iu, j), id(iu2, j0), id(iu2, j1), id(iu, j + 1)]);
          rawFaceStrip.push(si);
        }
        for (const j of cutIdx) rawCuts.push([id(iu, j), id(iu2, flip ? nV - 1 - j : j)]);
      }
      for (const c of st.cuts) {
        const pts = U.map((u) => stripPoint(frame, k, u.s, c));
        if (odd && Math.abs(c - 0.5) > 1e-6) for (const u of U) pts.push(stripPoint(frame, k, u.s, 1 - c));
        pts.push(pts[0].slice());
        cutPaths.push({ strip: si, c, points: pts });
      }
      strips.push({ index: si, plane, halfTwists: k, cuts: st.cuts.slice(), odd });
    });

    // Tape: merge patch vertices that sit in the same place.
    const uf = new UnionFind(pos.length);
    const seen = new Map();
    for (let i = 0; i < pos.length; i++) {
      if (!patch[i]) continue;
      const p = pos[i];
      const key = Math.round(p[0] * 1e5) + ':' + Math.round(p[1] * 1e5) + ':' + Math.round(p[2] * 1e5);
      if (seen.has(key)) uf.union(i, seen.get(key));
      else seen.set(key, i);
    }
    const remap = new Int32Array(pos.length).fill(-1);
    const positions = [];
    const faces = [];
    const faceStrip = [];
    const faceKeys = new Set();
    rawFaces.forEach((f, fi) => {
      const g = f.map((v) => {
        const r = uf.find(v);
        if (remap[r] < 0) {
          remap[r] = positions.length;
          positions.push(pos[r]);
        }
        return remap[r];
      });
      const key = g.slice().sort((a, b) => a - b).join(',');
      if (faceKeys.has(key)) return;
      faceKeys.add(key);
      faces.push(g);
      faceStrip.push(rawFaceStrip[fi]);
    });
    const cutEdges = new Set();
    for (const [a, b] of rawCuts) cutEdges.add(edgeKey(remap[uf.find(a)], remap[uf.find(b)]));

    return { config, V, positions, faces, faceStrip, cutEdges, strips, cutPaths, bounds: boundsOf(positions) };
  }

  function boundsOf(points) {
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    for (const p of points) for (let i = 0; i < 3; i++) {
      if (p[i] < min[i]) min[i] = p[i];
      if (p[i] > max[i]) max[i] = p[i];
    }
    return { min, max };
  }

  // ----------------------------------------------------------------- cut --

  function cutModel(model) {
    const { faces, cutEdges, positions } = model;
    const nF = faces.length;
    const edgeFaces = new Map();
    faces.forEach((f, fi) => {
      for (let k = 0; k < f.length; k++) {
        const a = f[k], b = f[(k + 1) % f.length];
        const key = edgeKey(a, b);
        let e = edgeFaces.get(key);
        if (!e) edgeFaces.set(key, (e = { a: Math.min(a, b), b: Math.max(a, b), list: [] }));
        e.list.push(fi);
      }
    });
    // Corners (face, vertex) that stay attached across uncut edges become one vertex.
    const cornerOf = (fi, v) => fi * 4 + faces[fi].indexOf(v);
    const uf = new UnionFind(nF * 4);
    for (const [key, e] of edgeFaces) {
      if (cutEdges.has(key)) continue;
      const f0 = e.list[0];
      for (let i = 1; i < e.list.length; i++) {
        uf.union(cornerOf(f0, e.a), cornerOf(e.list[i], e.a));
        uf.union(cornerOf(f0, e.b), cornerOf(e.list[i], e.b));
      }
    }
    const newId = new Map();
    const origOf = [];
    const newFaces = faces.map((f, fi) => f.map((v, k) => {
      const r = uf.find(fi * 4 + k);
      let id = newId.get(r);
      if (id === undefined) {
        id = origOf.length;
        newId.set(r, id);
        origOf.push(v);
      }
      return id;
    }));
    const nNew = origOf.length;
    const copies = new Int32Array(positions.length);
    for (const v of origOf) copies[v]++;

    const faceCentroid = (f, P) => {
      const c = [0, 0, 0];
      for (const v of f) for (let i = 0; i < 3; i++) c[i] += P[v][i];
      return c.map((x) => x / f.length);
    };
    const basePos = origOf.map((v) => positions[v]);
    const centroids = newFaces.map((f) => faceCentroid(f, basePos));
    const vertFaces = Array.from({ length: nNew }, () => []);
    newFaces.forEach((f, fi) => f.forEach((v) => vertFaces[v].push(fi)));

    // Vertices on a cut: the direction from the cut into their own side.
    const split = new Uint8Array(nNew);
    const inward = new Array(nNew).fill(null);
    for (let v = 0; v < nNew; v++) {
      if (copies[origOf[v]] < 2) continue;
      split[v] = 1;
      const c = [0, 0, 0];
      for (const fi of vertFaces[v]) for (let i = 0; i < 3; i++) c[i] += centroids[fi][i];
      for (let i = 0; i < 3; i++) c[i] = c[i] / vertFaces[v].length - basePos[v][i];
      inward[v] = c;
    }
    // Geometry used for measuring: cut sides nudged apart so pieces don't touch.
    const measurePos = basePos.map((p, v) => (split[v] ? [p[0] + 0.3 * inward[v][0], p[1] + 0.3 * inward[v][1], p[2] + 0.3 * inward[v][2]] : p));

    // Pieces = faces connected through shared vertices.
    const pf = new UnionFind(nF);
    for (let v = 0; v < nNew; v++) for (let i = 1; i < vertFaces[v].length; i++) pf.union(vertFaces[v][0], vertFaces[v][i]);
    const pieceIndex = new Map();
    const pieceFaces = [];
    for (let fi = 0; fi < nF; fi++) {
      const r = pf.find(fi);
      if (!pieceIndex.has(r)) { pieceIndex.set(r, pieceFaces.length); pieceFaces.push([]); }
      pieceFaces[pieceIndex.get(r)].push(fi);
    }
    pieceFaces.sort((a, b) => b.length - a.length);
    const facePiece = new Int32Array(nF);
    pieceFaces.forEach((list, pi) => list.forEach((fi) => (facePiece[fi] = pi)));

    const pieces = pieceFaces.map((list, pi) => analyzePiece(pi, list, newFaces, measurePos));
    const links = [];
    for (let i = 0; i < pieces.length; i++) {
      for (let j = i + 1; j < pieces.length; j++) {
        const lk = pieceLinking(pieces[i], pieces[j]);
        if (lk !== 0) links.push({ a: i, b: j, lk });
        else if (pieces[i].repLoop !== null && pieces[j].repLoop !== null && linkDeterminant([pieceCore(pieces[i]), pieceCore(pieces[j])]) !== 0) {
          links.push({ a: i, b: j, lk: 0, tangled: true });
        }
      }
    }
    const offsets = gapField(newFaces, basePos, split, inward, nNew);
    const result = {
      vertexCount: nNew,
      origOf,
      basePos,
      faces: newFaces,
      faceStrip: model.faceStrip,
      facePiece,
      offsets,
      measurePos,
      pieces,
      links,
    };
    result.summary = describe(result);
    return result;
  }

  // Smooth field that opens the cuts for display: vertices on a cut move into
  // their own side, free paper edges stay put, everything else is interpolated.
  function gapField(faces, P, split, inward, n) {
    const nbr = Array.from({ length: n }, () => new Set());
    const boundaryCount = new Map();
    for (const f of faces) for (let k = 0; k < f.length; k++) {
      const a = f[k], b = f[(k + 1) % f.length];
      nbr[a].add(b); nbr[b].add(a);
      const key = edgeKey(a, b);
      boundaryCount.set(key, (boundaryCount.get(key) || 0) + 1);
    }
    const pinned = new Uint8Array(n);
    const D = new Float64Array(n * 3);
    for (let v = 0; v < n; v++) {
      if (split[v]) {
        const d = inward[v];
        const len = Math.hypot(d[0], d[1], d[2]) || 1;
        D[3 * v] = d[0] / len; D[3 * v + 1] = d[1] / len; D[3 * v + 2] = d[2] / len;
        pinned[v] = 1;
      }
    }
    for (const [key, c] of boundaryCount) {
      if (c !== 1) continue;
      const [a, b] = key.split(',').map(Number);
      if (!split[a]) pinned[a] = 1;
      if (!split[b]) pinned[b] = 1;
    }
    const lists = nbr.map((s) => Array.from(s));
    let next = new Float64Array(n * 3);
    for (let it = 0; it < 140; it++) {
      for (let v = 0; v < n; v++) {
        if (pinned[v]) { next[3 * v] = D[3 * v]; next[3 * v + 1] = D[3 * v + 1]; next[3 * v + 2] = D[3 * v + 2]; continue; }
        let x = 0, y = 0, z = 0;
        const L = lists[v];
        for (const u of L) { x += D[3 * u]; y += D[3 * u + 1]; z += D[3 * u + 2]; }
        next[3 * v] = x / L.length; next[3 * v + 1] = y / L.length; next[3 * v + 2] = z / L.length;
      }
      const t = D; D.set(next); next = t;
    }
    return D;
  }

  // ------------------------------------------------------------ measuring --

  function analyzePiece(index, faceIds, faces, P) {
    const verts = new Set();
    const edges = new Map();
    for (const fi of faceIds) {
      const f = faces[fi];
      for (let k = 0; k < f.length; k++) {
        verts.add(f[k]);
        const a = f[k], b = f[(k + 1) % f.length];
        const key = edgeKey(a, b);
        let e = edges.get(key);
        if (!e) edges.set(key, (e = { a, b, faces: [] }));
        e.faces.push(fi);
      }
    }
    let branched = 0;
    const boundary = [];
    for (const e of edges.values()) {
      if (e.faces.length === 1) boundary.push(e);
      else if (e.faces.length > 2) branched++;
    }
    const chi = verts.size - edges.size + faceIds.length;
    const loops = boundaryLoops(boundary);

    // One-sided or two-sided: try to give every face a consistent orientation.
    let orientable = true;
    const orient = new Map([[faceIds[0], 1]]);
    const queue = [faceIds[0]];
    const dir = (fi, a, b) => {
      const f = faces[fi];
      for (let k = 0; k < f.length; k++) {
        if (f[k] === a && f[(k + 1) % f.length] === b) return 1;
        if (f[k] === b && f[(k + 1) % f.length] === a) return -1;
      }
      return 0;
    };
    const faceEdges = new Map();
    for (const e of edges.values()) {
      if (e.faces.length !== 2) continue;
      for (const fi of e.faces) {
        if (!faceEdges.has(fi)) faceEdges.set(fi, []);
        faceEdges.get(fi).push(e);
      }
    }
    while (queue.length) {
      const fi = queue.pop();
      for (const e of faceEdges.get(fi) || []) {
        const g = e.faces[0] === fi ? e.faces[1] : e.faces[0];
        const want = -orient.get(fi) * dir(fi, e.a, e.b) * dir(g, e.a, e.b);
        if (!orient.has(g)) { orient.set(g, want); queue.push(g); }
        else if (orient.get(g) !== want) orientable = false;
      }
    }

    const centroid = (fi) => {
      const c = [0, 0, 0];
      for (const v of faces[fi]) for (let i = 0; i < 3; i++) c[i] += P[v][i];
      return c.map((x) => x / faces[fi].length);
    };
    const boundaryFace = new Map();
    for (const e of boundary) boundaryFace.set(edgeKey(e.a, e.b), e.faces[0]);
    const loopPoints = loops.map((L) => L.map((v) => P[v]));
    const pushedIn = (L) => L.map((v, i) => {
      const prev = L[(i - 1 + L.length) % L.length], next = L[(i + 1) % L.length];
      const c1 = centroid(boundaryFace.get(edgeKey(prev, v)));
      const c2 = centroid(boundaryFace.get(edgeKey(v, next)));
      const p = P[v];
      return [0, 1, 2].map((k) => p[k] + 0.35 * ((c1[k] + c2[k]) / 2 - p[k]));
    });

    const piece = {
      index,
      faceCount: faceIds.length,
      faceIds,
      chi,
      edgeCount: loops.length,
      orientable,
      branched: branched > 0,
      loops,
      type: 'surface',
      repLoop: null,
      repDivisor: 1,
    };
    const b = loops.length;
    if (piece.branched) {
      piece.type = 'compound';
    } else if (chi === 1 && b === 1 && orientable) {
      piece.type = 'disk';
    } else if (chi === 0 && b === 2 && orientable) {
      piece.type = 'band';
      const L = loops[0];
      piece.halfTwists = 2 * linkingNumber(loopPoints[0], pushedIn(L));
      piece.lengthRatio = middleLength(loopPoints[0], loopPoints[1]) / LOOP_LENGTH;
      piece.knot = knotInfo(loopPoints[0]);
      piece.repLoop = 0;
    } else if (chi === 0 && b === 1 && !orientable) {
      piece.type = 'mobius';
      const L = loops[0];
      piece.halfTwists = linkingNumber(loopPoints[0], pushedIn(L)) / 2;
      piece.lengthRatio = middleLength(loopPoints[0], null) / LOOP_LENGTH;
      piece.edgeKnot = knotInfo(loopPoints[0]);
      piece.repLoop = 0;
      piece.repDivisor = 2;
    } else if (orientable) {
      piece.genus = (2 - chi - b) / 2;
    } else {
      piece.crosscaps = 2 - chi - b;
    }
    piece.loopPoints = loopPoints;
    return piece;
  }

  function boundaryLoops(boundary) {
    const adj = new Map();
    boundary.forEach((e, i) => {
      for (const v of [e.a, e.b]) {
        if (!adj.has(v)) adj.set(v, []);
        adj.get(v).push(i);
      }
    });
    const used = new Uint8Array(boundary.length);
    const loops = [];
    for (let i = 0; i < boundary.length; i++) {
      if (used[i]) continue;
      used[i] = 1;
      const start = boundary[i].a;
      const loop = [start];
      let cur = boundary[i].b;
      while (cur !== start) {
        loop.push(cur);
        const nextEdge = (adj.get(cur) || []).find((ei) => !used[ei]);
        if (nextEdge === undefined) break;
        used[nextEdge] = 1;
        const e = boundary[nextEdge];
        cur = e.a === cur ? e.b : e.a;
      }
      if (loop.length >= 3) loops.push(loop);
    }
    return loops;
  }

  function polyLength(pts) {
    let s = 0;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length];
      s += Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
    }
    return s;
  }

  // Length along the middle of a band: walk one edge and step to the midpoint
  // between it and the nearest point of the opposite edge. A Mobius band has
  // one edge that runs around twice, so its opposite side is the other lap.
  function middleLength(A, B) {
    return polyLength(middleCurve(A, B));
  }

  function middleCurve(A, B) {
    const n = A.length;
    const mids = [];
    const laps = B ? 1 : 2;
    const count = Math.floor(n / laps);
    for (let i = 0; i < count; i++) {
      const p = A[i];
      let best = Infinity, q = null;
      const other = B || A;
      for (let j = 0; j < other.length; j++) {
        if (!B) {
          const d = Math.abs(j - i);
          if (Math.min(d, n - d) < n / 4) continue;
        }
        const r = other[j];
        const d2 = (p[0] - r[0]) ** 2 + (p[1] - r[1]) ** 2 + (p[2] - r[2]) ** 2;
        if (d2 < best) { best = d2; q = r; }
      }
      mids.push([(p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2]);
    }
    return mids;
  }

  function pieceCore(p) {
    return middleCurve(p.loopPoints[0], p.type === 'band' ? p.loopPoints[1] : null);
  }

  // How many times two pieces wind around each other.
  function pieceLinking(A, B) {
    if (A.repLoop !== null && B.repLoop !== null) {
      const lk = linkingNumber(A.loopPoints[A.repLoop], B.loopPoints[B.repLoop]);
      return Math.round(Math.abs(lk) / (A.repDivisor * B.repDivisor));
    }
    // General shapes: interlocked if any edge of one links any edge of the other.
    let best = 0;
    for (const a of A.loopPoints) for (const b of B.loopPoints) best = Math.max(best, Math.abs(linkingNumber(a, b)));
    return best;
  }

  // Generic viewing direction, so no straight piece of paper projects edge-on.
  const ROT = (() => {
    const ax = 0.6137, ay = 0.4291, az = 0.2718;
    const cx = Math.cos(ax), sx = Math.sin(ax), cy = Math.cos(ay), sy = Math.sin(ay), cz = Math.cos(az), sz = Math.sin(az);
    const Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]];
    const Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]];
    const Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]];
    const mul = (A, B) => A.map((r) => [0, 1, 2].map((j) => r[0] * B[0][j] + r[1] * B[1][j] + r[2] * B[2][j]));
    return mul(Rz, mul(Ry, Rx));
  })();

  function project(points) {
    return points.map((p) => [
      ROT[0][0] * p[0] + ROT[0][1] * p[1] + ROT[0][2] * p[2],
      ROT[1][0] * p[0] + ROT[1][1] * p[1] + ROT[1][2] * p[2],
      ROT[2][0] * p[0] + ROT[2][1] * p[1] + ROT[2][2] * p[2],
    ]);
  }

  function crossSegments(p1, p2, q1, q2) {
    const dax = p2[0] - p1[0], day = p2[1] - p1[1];
    const dbx = q2[0] - q1[0], dby = q2[1] - q1[1];
    const den = dax * dby - day * dbx;
    if (Math.abs(den) < 1e-15) return null;
    const rx = q1[0] - p1[0], ry = q1[1] - p1[1];
    const t = (rx * dby - ry * dbx) / den;
    const u = (rx * day - ry * dax) / den;
    if (t < 0 || t >= 1 || u < 0 || u >= 1) return null;
    return { t, u, za: p1[2] + t * (p2[2] - p1[2]), zb: q1[2] + u * (q2[2] - q1[2]), cross: den };
  }

  function segBoxes(p) {
    const n = p.length;
    const box = new Float64Array(n * 4);
    for (let i = 0; i < n; i++) {
      const a = p[i], b = p[(i + 1) % n];
      box[4 * i] = Math.min(a[0], b[0]); box[4 * i + 1] = Math.max(a[0], b[0]);
      box[4 * i + 2] = Math.min(a[1], b[1]); box[4 * i + 3] = Math.max(a[1], b[1]);
    }
    return box;
  }

  // Linking number of two closed polylines, from signed crossings in a
  // projection (right-hand rule: positive for a right-handed twist).
  function linkingNumber(A, B) {
    const a = project(A), b = project(B);
    const ba = segBoxes(a), bb = segBoxes(b);
    let sum = 0;
    for (let i = 0; i < a.length; i++) {
      for (let j = 0; j < b.length; j++) {
        if (ba[4 * i + 1] < bb[4 * j] || bb[4 * j + 1] < ba[4 * i] || ba[4 * i + 3] < bb[4 * j + 2] || bb[4 * j + 3] < ba[4 * i + 2]) continue;
        const h = crossSegments(a[i], a[(i + 1) % a.length], b[j], b[(j + 1) % b.length]);
        if (!h) continue;
        // sign of (over x under); viewer looks down from +z
        sum += (h.za > h.zb ? 1 : -1) * Math.sign(h.cross);
      }
    }
    return Math.round(sum / 2);
  }

  // Knot determinant |Alexander polynomial at -1| from Fox colouring matrix.
  // 1 for the unknot, 3 for a trefoil, 5 for a figure-eight or cinquefoil.
  function knotDeterminant(points) {
    return diagramDeterminant([points], 1);
  }

  // Determinant of a link made of several closed curves. 0 for curves that
  // lie apart; anything else proves they can't be pulled apart, even when
  // their linking number is 0 (the Whitehead link has determinant 16).
  function linkDeterminant(curves) {
    return diagramDeterminant(curves, 0);
  }

  function diagramDeterminant(curves, empty) {
    const comps = curves.map(project);
    const segs = [];
    comps.forEach((p, c) => {
      const box = segBoxes(p);
      for (let i = 0; i < p.length; i++) segs.push({ c, i, p, box });
    });
    const crossings = [];
    for (let x = 0; x < segs.length; x++) {
      const A = segs[x];
      for (let y = x + 1; y < segs.length; y++) {
        const B = segs[y];
        if (A.c === B.c) {
          const n = A.p.length, d = Math.abs(A.i - B.i);
          if (d < 2 || d === n - 1) continue;
        }
        const a = A.box, b = B.box, i = A.i, j = B.i;
        if (a[4 * i + 1] < b[4 * j] || b[4 * j + 1] < a[4 * i] || a[4 * i + 3] < b[4 * j + 2] || b[4 * j + 3] < a[4 * i + 2]) continue;
        const h = crossSegments(A.p[i], A.p[(i + 1) % A.p.length], B.p[j], B.p[(j + 1) % B.p.length]);
        if (!h) continue;
        const pa = { c: A.c, pos: i + h.t }, pb = { c: B.c, pos: j + h.u };
        crossings.push(h.za > h.zb ? { over: pa, under: pb } : { over: pb, under: pa });
      }
    }
    const m = crossings.length;
    if (m === 0) return comps.length === 1 ? 1 : empty;
    // Arcs run between undercrossings on each curve.
    const arcBase = [];
    const unders = comps.map(() => []);
    crossings.forEach((cr, idx) => unders[cr.under.c].push({ pos: cr.under.pos, idx }));
    let arcs = 0;
    for (let c = 0; c < comps.length; c++) {
      unders[c].sort((x, y) => x.pos - y.pos);
      arcBase.push(arcs);
      arcs += Math.max(1, unders[c].length);
    }
    // A curve that never passes under anything sits on top and lifts away.
    if (arcs !== m) return comps.length === 1 ? 1 : 0;
    const arcAt = (c, pos) => {
      const list = unders[c];
      let lo = 0, hi = list.length - 1, ans = -1;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (list[mid].pos < pos) { ans = mid; lo = mid + 1; } else hi = mid - 1;
      }
      return arcBase[c] + (ans < 0 ? list.length - 1 : ans);
    };
    const M = Array.from({ length: m }, () => new Float64Array(m));
    crossings.forEach((cr, row) => {
      const c = cr.under.c, list = unders[c];
      const r = list.findIndex((u) => u.idx === row);
      M[row][arcAt(cr.over.c, cr.over.pos)] += 2;
      M[row][arcBase[c] + ((r - 1 + list.length) % list.length)] -= 1;
      M[row][arcBase[c] + r] -= 1;
    });
    if (m < 2) return comps.length === 1 ? 1 : empty;
    return Math.round(Math.abs(determinant(M, m - 1)));
  }

  function determinant(M, n) {
    const A = M.slice(0, n).map((row) => Array.from(row.slice(0, n)));
    let det = 1;
    for (let c = 0; c < n; c++) {
      let piv = c;
      for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[piv][c])) piv = r;
      if (Math.abs(A[piv][c]) < 1e-12) return 0;
      if (piv !== c) { const t = A[piv]; A[piv] = A[c]; A[c] = t; det = -det; }
      det *= A[c][c];
      for (let r = c + 1; r < n; r++) {
        const f = A[r][c] / A[c][c];
        if (!f) continue;
        for (let k = c; k < n; k++) A[r][k] -= f * A[c][k];
      }
    }
    return det;
  }

  function knotInfo(points) {
    const det = knotDeterminant(points);
    let name;
    if (det === 1) name = 'no knot';
    else if (det === 3) name = 'trefoil knot';
    else if (det === 5) name = 'cinquefoil or figure-eight knot';
    else if (det % 2 === 1) name = 'knot (determinant ' + det + ')';
    else name = 'tangle that could not be identified';
    return { det, knotted: det !== 1, name };
  }


  // ----------------------------------------------------------- pull apart --
  //
  // Turns each loop-shaped piece into a flexible ribbon (a chain of points
  // along its middle) and pulls the pieces away from each other. Strands are
  // kept a minimum distance apart and move in small steps, so they can never
  // pass through each other: loose pieces slide free, linked pieces catch,
  // and knots stay knotted. Other pieces (flat sheets, taped bundles) move
  // as stiff bodies without rotating.

  const PULL_THICKNESS = 0.28;

  function resampleClosed(pts, N) {
    const n = pts.length;
    const cum = [0];
    for (let i = 0; i < n; i++) {
      const a = pts[i], b = pts[(i + 1) % n];
      cum.push(cum[i] + Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]));
    }
    const L = cum[n];
    const out = [];
    let seg = 0;
    for (let k = 0; k < N; k++) {
      const t = (k * L) / N;
      while (seg < n - 1 && cum[seg + 1] < t) seg++;
      const a = pts[seg], b = pts[(seg + 1) % n];
      const len = cum[seg + 1] - cum[seg] || 1;
      const f = (t - cum[seg]) / len;
      out.push([a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]), a[2] + f * (b[2] - a[2])]);
    }
    return out;
  }

  // Closest points between segments p1-q1 and p2-q2 (Ericson, Real-Time Collision Detection).
  function closestSegSeg(p1, q1, p2, q2) {
    const d1 = [q1[0] - p1[0], q1[1] - p1[1], q1[2] - p1[2]];
    const d2 = [q2[0] - p2[0], q2[1] - p2[1], q2[2] - p2[2]];
    const r = [p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2]];
    const a = d1[0] * d1[0] + d1[1] * d1[1] + d1[2] * d1[2];
    const e = d2[0] * d2[0] + d2[1] * d2[1] + d2[2] * d2[2];
    const f = d2[0] * r[0] + d2[1] * r[1] + d2[2] * r[2];
    let s, t;
    const clamp = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
    if (a <= 1e-12 && e <= 1e-12) { s = 0; t = 0; }
    else if (a <= 1e-12) { s = 0; t = clamp(f / e); }
    else {
      const c = d1[0] * r[0] + d1[1] * r[1] + d1[2] * r[2];
      if (e <= 1e-12) { t = 0; s = clamp(-c / a); }
      else {
        const b = d1[0] * d2[0] + d1[1] * d2[1] + d1[2] * d2[2];
        const den = a * e - b * b;
        s = den > 1e-12 ? clamp((b * f - c * e) / den) : 0;
        t = (b * s + f) / e;
        if (t < 0) { t = 0; s = clamp(-c / a); }
        else if (t > 1) { t = 1; s = clamp((b - c) / a); }
      }
    }
    const c1 = [p1[0] + d1[0] * s, p1[1] + d1[1] * s, p1[2] + d1[2] * s];
    const c2 = [p2[0] + d2[0] * t, p2[1] + d2[1] * t, p2[2] + d2[2] * t];
    return { s, t, c1, c2 };
  }

  function createPullSim(result) {
    const bodies = result.pieces.map((p, i) => {
      if (p.type === 'band' || p.type === 'mobius') {
        const core = middleCurve(p.loopPoints[0], p.type === 'band' ? p.loopPoints[1] : null);
        const L = polyLength(core);
        const N = Math.max(36, Math.min(220, Math.round(L / 0.13)));
        return { kind: 'rope', piece: i, X: resampleClosed(core, N), N, rest: L / N, halfTwists: p.halfTwists };
      }
      // one point per 0.08-wide box is plenty to collide with
      const seen = new Set();
      const pts = [];
      for (const fi of p.faceIds) for (const v of result.faces[fi]) {
        const q = result.measurePos[v];
        const key = Math.floor(q[0] / 0.08) + ',' + Math.floor(q[1] / 0.08) + ',' + Math.floor(q[2] / 0.08);
        if (seen.has(key)) continue;
        seen.add(key);
        pts.push(q);
      }
      return { kind: 'rigid', piece: i, P0: pts, offset: [0, 0, 0], N: pts.length };
    });

    // Elements that collide: rope segments, and points of stiff pieces.
    const elems = [];
    bodies.forEach((b, bi) => {
      for (let k = 0; k < b.N; k++) elems.push({ body: bi, k });
    });
    const ends = (el) => {
      const b = bodies[el.body];
      if (b.kind === 'rope') return [b.X[el.k], b.X[(el.k + 1) % b.N]];
      const p = b.P0[el.k], o = b.offset;
      const q = [p[0] + o[0], p[1] + o[1], p[2] + o[2]];
      return [q, q];
    };
    const skipPair = (A, B) => {
      if (A.body !== B.body) return false;
      const b = bodies[A.body];
      if (b.kind === 'rigid') return true;
      const d = Math.abs(A.k - B.k);
      return Math.min(d, b.N - d) < 4;
    };

    // Calls fn for every pair of elements whose closest points could be
    // within `reach`. The grid cell also covers the longest segment, so a
    // stretched rope can't slip a pair past the check.
    function forEachClosePair(reach, fn) {
      let longest = 0;
      for (const b of bodies) {
        if (b.kind !== 'rope') continue;
        for (let i = 0; i < b.N; i++) {
          const p = b.X[i], q = b.X[(i + 1) % b.N];
          longest = Math.max(longest, Math.hypot(q[0] - p[0], q[1] - p[1], q[2] - p[2]));
        }
      }
      const cell = reach + longest;
      const grid = new Map();
      const geo = new Array(elems.length);
      const K = 2048, H = K / 2;
      for (let i = 0; i < elems.length; i++) {
        const [a, b] = ends(elems[i]);
        const ix = Math.floor((a[0] + b[0]) / 2 / cell) + H;
        const iy = Math.floor((a[1] + b[1]) / 2 / cell) + H;
        const iz = Math.floor((a[2] + b[2]) / 2 / cell) + H;
        geo[i] = { a, b, ix, iy, iz };
        const key = (ix * K + iy) * K + iz;
        const list = grid.get(key);
        if (list) list.push(i); else grid.set(key, [i]);
      }
      for (let i = 0; i < elems.length; i++) {
        const g = geo[i];
        for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) {
          const list = grid.get(((g.ix + dx) * K + g.iy + dy) * K + g.iz + dz);
          if (!list) continue;
          for (const j of list) {
            if (j <= i || skipPair(elems[i], elems[j])) continue;
            fn(i, j, g, geo[j]);
          }
        }
      }
    }

    let seed = 12345;
    const rand = () => ((seed = (seed * 1103515245 + 12345) >>> 0) / 4294967296);

    // Start thin enough that nothing overlaps, then thicken.
    let minDist = Infinity;
    forEachClosePair(0.3, (i, j, g, h) => {
      const r = closestSegSeg(g.a, g.b, h.a, h.b);
      minDist = Math.min(minDist, Math.hypot(r.c1[0] - r.c2[0], r.c1[1] - r.c2[1], r.c1[2] - r.c2[2]));
    });
    const linked = new Set(result.links.map((l) => l.a + '-' + l.b));
    const sim = {
      bodies,
      iteration: 0,
      done: false,
      shaking: bodies.length > 1,
      quiet: 0,
      pairs: [],
      thickness: Math.max(0.004, Math.min(PULL_THICKNESS, 0.8 * minDist)),
      step,
      centroid,
      separation,
    };

    function centroid(b) {
      const c = [0, 0, 0];
      if (b.kind === 'rope') {
        for (const x of b.X) for (let i = 0; i < 3; i++) c[i] += x[i];
        return c.map((v) => v / b.N);
      }
      for (const x of b.P0) for (let i = 0; i < 3; i++) c[i] += x[i];
      return c.map((v, i) => v / b.N + b.offset[i]);
    }
    function radius(b, c) {
      let r = 0;
      const pts = b.kind === 'rope' ? b.X : b.P0;
      const o = b.kind === 'rope' ? [0, 0, 0] : b.offset;
      for (const x of pts) r = Math.max(r, Math.hypot(x[0] + o[0] - c[0], x[1] + o[1] - c[1], x[2] + o[2] - c[2]));
      return r;
    }
    // Smallest gap between two pieces.
    function separation(ai, bi) {
      let best = Infinity;
      const A = bodies[ai], B = bodies[bi];
      const pa = A.kind === 'rope' ? A.X : A.P0.map((p) => [p[0] + A.offset[0], p[1] + A.offset[1], p[2] + A.offset[2]]);
      const pb = B.kind === 'rope' ? B.X : B.P0.map((p) => [p[0] + B.offset[0], p[1] + B.offset[1], p[2] + B.offset[2]]);
      for (const p of pa) for (const q of pb) best = Math.min(best, (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2);
      return Math.sqrt(best);
    }

    const moveBody = (b, d) => {
      if (b.kind === 'rope') for (const x of b.X) { x[0] += d[0]; x[1] += d[1]; x[2] += d[2]; }
      else { b.offset[0] += d[0]; b.offset[1] += d[1]; b.offset[2] += d[2]; }
    };

    function step(iterations) {
      for (let it = 0; it < iterations && !sim.done; it++) oneStep();
      return sim;
    }

    function oneStep() {
      const d0 = sim.thickness;
      const maxStep = Math.min(0.03, 0.3 * d0);
      const before = bodies.map((b) => (b.kind === 'rope' ? b.X.map((x) => x.slice()) : b.offset.slice()));

      // 1. Pull overlapping pieces away from each other.
      if (bodies.length > 1) {
        const cs = bodies.map(centroid);
        const rs = bodies.map((b, i) => radius(b, cs[i]));
        for (let a = 0; a < bodies.length; a++) {
          for (let b = a + 1; b < bodies.length; b++) {
            let d = [cs[a][0] - cs[b][0], cs[a][1] - cs[b][1], cs[a][2] - cs[b][2]];
            let len = Math.hypot(d[0], d[1], d[2]);
            if (len < 1e-6) { d = [0.3, 1, 0.2]; len = Math.hypot(0.3, 1, 0.2); }
            if (len > rs[a] + rs[b] + 0.6) continue;
            const k = 0.006 / len;
            moveBody(bodies[a], [d[0] * k, d[1] * k, d[2] * k]);
            moveBody(bodies[b], [-d[0] * k, -d[1] * k, -d[2] * k]);
          }
        }
        // A little shaking helps pieces that are loose but snagged slide free.
        if (sim.shaking) for (const b of bodies) {
          moveBody(b, [(rand() - 0.5) * 0.02, (rand() - 0.5) * 0.02, (rand() - 0.5) * 0.02]);
        }
      }

      // 2. Ropes: open up into round loops, smooth out kinks, keep their length.
      for (const b of bodies) {
        if (b.kind !== 'rope') continue;
        const X = b.X, N = b.N;
        const c = centroid(b);
        for (const x of X) {
          const dx = x[0] - c[0], dy = x[1] - c[1], dz = x[2] - c[2];
          const len = Math.hypot(dx, dy, dz) || 1;
          x[0] += (0.004 * dx) / len; x[1] += (0.004 * dy) / len; x[2] += (0.004 * dz) / len;
        }
        const sm = X.map((x, i) => {
          const p = X[(i - 1 + N) % N], q = X[(i + 1) % N];
          return [x[0] + 0.08 * ((p[0] + q[0]) / 2 - x[0]), x[1] + 0.08 * ((p[1] + q[1]) / 2 - x[1]), x[2] + 0.08 * ((p[2] + q[2]) / 2 - x[2])];
        });
        for (let i = 0; i < N; i++) X[i] = sm[i];
        for (let pass = 0; pass < 6; pass++) {
          for (let i = 0; i < N; i++) {
            const p = X[i], q = X[(i + 1) % N];
            const dx = q[0] - p[0], dy = q[1] - p[1], dz = q[2] - p[2];
            const len = Math.hypot(dx, dy, dz) || 1e-9;
            const c = (0.5 * (len - b.rest)) / len;
            p[0] += dx * c; p[1] += dy * c; p[2] += dz * c;
            q[0] -= dx * c; q[1] -= dy * c; q[2] -= dz * c;
          }
        }
      }

      // 3. Keep strands apart.
      clampMoves(before, maxStep);
      const rigidPush = bodies.map(() => ({ d: [0, 0, 0], n: 0 }));
      forEachClosePair(d0, (i, j, g, h) => {
        const r = closestSegSeg(g.a, g.b, h.a, h.b);
        let n = [r.c1[0] - r.c2[0], r.c1[1] - r.c2[1], r.c1[2] - r.c2[2]];
        const dist = Math.hypot(n[0], n[1], n[2]);
        if (dist >= d0) return;
        if (dist < 1e-9) n = [0, 0, 1];
        else n = [n[0] / dist, n[1] / dist, n[2] / dist];
        const corr = d0 - dist;
        push(elems[i], r.s, n, corr * 0.5, rigidPush);
        push(elems[j], r.t, n, -corr * 0.5, rigidPush);
      });
      bodies.forEach((b, i) => {
        const rp = rigidPush[i];
        if (rp.n) moveBody(b, [rp.d[0] / rp.n, rp.d[1] / rp.n, rp.d[2] / rp.n]);
      });
      const moved = clampMoves(before, maxStep);

      sim.iteration++;
      if (sim.thickness < PULL_THICKNESS) sim.thickness = Math.min(PULL_THICKNESS, sim.thickness + 0.0015);
      if (sim.iteration % 100 === 0) checkPairs();
      if (!sim.shaking && sim.thickness >= PULL_THICKNESS) {
        sim.quiet++;
        if ((sim.quiet > 200 && moved < 4e-4) || sim.quiet > 1500) { checkPairs(); sim.done = true; }
      }
    }

    // Which pieces still touch. Keep shaking while a pair that the maths says
    // is free is still caught; give up after a while.
    function checkPairs() {
      sim.pairs = [];
      let stuck = false;
      for (let a = 0; a < bodies.length; a++) {
        for (let b = a + 1; b < bodies.length; b++) {
          const gap = separation(a, b);
          const isLinked = linked.has(a + '-' + b);
          const touching = gap < 1.6 * PULL_THICKNESS;
          sim.pairs.push({ a, b, linked: isLinked, touching, gap });
          if (!isLinked && touching) stuck = true;
        }
      }
      sim.shaking = stuck && sim.iteration < 7000 && sim.thickness >= PULL_THICKNESS ? true : sim.thickness < PULL_THICKNESS && bodies.length > 1;
    }

    function push(el, s, n, amount, rigidPush) {
      const b = bodies[el.body];
      if (b.kind === 'rigid') {
        const rp = rigidPush[el.body];
        rp.d[0] += n[0] * amount; rp.d[1] += n[1] * amount; rp.d[2] += n[2] * amount;
        rp.n++;
        return;
      }
      const w = (1 - s) * (1 - s) + s * s;
      const p = b.X[el.k], q = b.X[(el.k + 1) % b.N];
      const fp = ((1 - s) * amount) / w, fq = (s * amount) / w;
      p[0] += n[0] * fp; p[1] += n[1] * fp; p[2] += n[2] * fp;
      q[0] += n[0] * fq; q[1] += n[1] * fq; q[2] += n[2] * fq;
    }

    // No point may move further than maxStep in one step, so nothing tunnels.
    function clampMoves(before, maxStep) {
      let most = 0;
      bodies.forEach((b, bi) => {
        const pairs = b.kind === 'rope' ? b.X.map((x, i) => [x, before[bi][i]]) : [[b.offset, before[bi]]];
        for (const [x, o] of pairs) {
          const dx = x[0] - o[0], dy = x[1] - o[1], dz = x[2] - o[2];
          const len = Math.hypot(dx, dy, dz);
          if (len > maxStep) {
            const k = maxStep / len;
            x[0] = o[0] + dx * k; x[1] = o[1] + dy * k; x[2] = o[2] + dz * k;
          }
          most = Math.max(most, Math.min(len, maxStep));
        }
      });
      return most;
    }

    return sim;
  }

  function writhe(X) {
    const N = X.length;
    const mid = [], tan = [];
    for (let i = 0; i < N; i++) {
      const a = X[i], b = X[(i + 1) % N];
      mid.push([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]);
      tan.push([b[0] - a[0], b[1] - a[1], b[2] - a[2]]);
    }
    let s = 0;
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
      if (i === j) continue;
      const r = [mid[i][0] - mid[j][0], mid[i][1] - mid[j][1], mid[i][2] - mid[j][2]];
      const t = tan[i], u = tan[j];
      const cx = t[1] * u[2] - t[2] * u[1], cy = t[2] * u[0] - t[0] * u[2], cz = t[0] * u[1] - t[1] * u[0];
      const d = Math.hypot(r[0], r[1], r[2]);
      s += (r[0] * cx + r[1] * cy + r[2] * cz) / (d * d * d);
    }
    return s / (4 * Math.PI);
  }

  const rotateAbout = (v, axis, ang) => {
    const c = Math.cos(ang), s = Math.sin(ang);
    const d = axis[0] * v[0] + axis[1] * v[1] + axis[2] * v[2];
    const cx = axis[1] * v[2] - axis[2] * v[1], cy = axis[2] * v[0] - axis[0] * v[2], cz = axis[0] * v[1] - axis[1] * v[0];
    return [v[0] * c + cx * s + axis[0] * d * (1 - c), v[1] * c + cy * s + axis[1] * d * (1 - c), v[2] * c + cz * s + axis[2] * d * (1 - c)];
  };
  const norm = (v) => { const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / l, v[1] / l, v[2] / l]; };
  const crossV = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const dotV = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

  // Directions across a ribbon laid along closed curve X with the given
  // number of half-twists. Uses Lk = Tw + Wr so the ribbon carries the same
  // twist as the paper piece, whatever shape the curve has taken.
  function ribbonFrame(X, halfTwists) {
    const N = X.length;
    const T = X.map((x, i) => {
      const p = X[(i - 1 + N) % N], q = X[(i + 1) % N];
      return norm([q[0] - p[0], q[1] - p[1], q[2] - p[2]]);
    });
    const transport = (u, t0, t1) => {
      const ax = crossV(t0, t1);
      const s = Math.hypot(ax[0], ax[1], ax[2]);
      if (s < 1e-12) return u;
      return rotateAbout(u, [ax[0] / s, ax[1] / s, ax[2] / s], Math.atan2(s, dotV(t0, t1)));
    };
    let seed = Math.abs(T[0][0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
    seed = norm(crossV(T[0], seed));
    const U = [seed];
    for (let i = 1; i <= N; i++) {
      let u = transport(U[i - 1], T[i - 1], T[i % N]);
      const t = T[i % N];
      const d = dotV(u, t);
      u = norm([u[0] - d * t[0], u[1] - d * t[1], u[2] - d * t[2]]);
      U.push(u);
    }
    // angle that turns the transported frame back onto the start
    const back = Math.atan2(dotV(crossV(U[N], U[0]), T[0]), dotV(U[N], U[0]));
    const odd = Math.abs(halfTwists) % 2 === 1;
    const want = Math.PI * (halfTwists - 2 * writhe(X));
    const base = back + (odd ? Math.PI : 0);
    const phi = base + 2 * Math.PI * Math.round((want - base) / (2 * Math.PI));
    const cum = [0];
    for (let i = 1; i < N; i++) cum.push(cum[i - 1] + Math.hypot(X[i][0] - X[i - 1][0], X[i][1] - X[i - 1][1], X[i][2] - X[i - 1][2]));
    const total = cum[N - 1] + Math.hypot(X[0][0] - X[N - 1][0], X[0][1] - X[N - 1][1], X[0][2] - X[N - 1][2]);
    return { W: X.map((x, i) => rotateAbout(U[i], T[i], (phi * cum[i]) / total)), flipped: odd };
  }

  // ------------------------------------------------------------ describing --

  const plural = (n, one, many) => n + ' ' + (Math.abs(n) === 1 ? one : many || one + 's');

  function twistText(h) {
    if (h === 0) return 'no twist';
    return plural(Math.abs(h), 'half-twist') + (h > 0 ? ', right-handed' : ', left-handed');
  }

  function lengthText(r) {
    const x = Math.round(r * 2) / 2;
    if (x === 1) return 'as long as one strip';
    if (x === 2) return 'twice as long as one strip';
    return 'about ' + x + '× as long as one strip';
  }

  function pieceTitle(p) {
    switch (p.type) {
      case 'mobius': return p.halfTwists === 1 || p.halfTwists === -1 ? 'Möbius strip' : 'One-sided loop';
      case 'band': return p.halfTwists === 0 ? 'Plain loop' : 'Twisted loop';
      case 'disk': return 'Flat sheet';
      case 'compound': return 'Taped bundle';
      default:
        if (p.orientable && p.genus === 0 && p.edgeCount === 3) return 'Three-edged sheet';
        return p.orientable ? 'Two-sided sheet' : 'One-sided sheet';
    }
  }

  function pieceFacts(p) {
    const f = [];
    if (p.type === 'compound') {
      f.push('layers still taped together and branching apart');
      f.push(plural(p.edgeCount, 'edge loop'));
      return f;
    }
    f.push(p.orientable ? 'two-sided' : 'one-sided');
    f.push(plural(p.edgeCount, 'edge'));
    if (p.type === 'band' || p.type === 'mobius') {
      f.push(twistText(p.halfTwists));
      f.push(lengthText(p.lengthRatio));
      if (p.type === 'band') f.push(p.knot.knotted ? 'tied in a ' + p.knot.name : 'no knot');
      if (p.type === 'mobius' && p.edgeKnot.knotted) f.push('its edge is a ' + p.edgeKnot.name);
    } else if (p.type === 'surface') {
      if (p.orientable && p.genus > 0) f.push(plural(p.genus, 'handle'));
      f.push('Euler characteristic ' + p.chi);
    }
    return f;
  }

  function describe(result) {
    const { pieces, links } = result;
    const names = pieces.map((p) => pieceTitle(p));
    pieces.forEach((p, i) => {
      p.title = names[i];
      p.facts = pieceFacts(p);
      p.linkedWith = links.filter((l) => l.a === i || l.b === i).map((l) => ({ piece: l.a === i ? l.b : l.a, lk: l.lk, tangled: !!l.tangled }));
    });
    let headline;
    const n = pieces.length;
    if (n === 1) {
      const p = pieces[0];
      headline = 'One piece: ' + article(p.title) + ' ' + p.title.toLowerCase();
      if (p.type === 'band' || p.type === 'mobius') headline += ' with ' + twistText(p.halfTwists).replace(/, (right|left)-handed/, '') + ', ' + lengthText(p.lengthRatio);
      if (p.type === 'band' && p.knot.knotted) headline += ', tied in a knot';
      headline += '.';
    } else {
      const counts = {};
      names.forEach((t) => (counts[t] = (counts[t] || 0) + 1));
      const parts = Object.keys(counts).map((t) => (counts[t] === 1 ? article(t) + ' ' + t.toLowerCase() : numberWord(counts[t]) + ' ' + pluralTitle(t)));
      headline = cap(numberWord(n)) + ' pieces: ' + joinList(parts) + '.';
      if (links.length) {
        const chain = isChain(n, links);
        if (links.length === 1 && n === 2) headline += ' They are interlocked and can’t be pulled apart.';
        else if (chain) headline += ' They hang together as a chain, like Olympic rings.';
        else headline += ' Some of them are interlocked.';
      } else {
        headline += n === 2 ? ' They come apart freely.' : ' They all come apart freely.';
      }
    }
    return headline.replace('möbius', 'Möbius');
  }

  function isChain(n, links) {
    if (links.length !== n - 1 || n < 3) return false;
    const deg = new Array(n).fill(0);
    for (const l of links) { deg[l.a]++; deg[l.b]++; }
    return deg.every((d) => d >= 1 && d <= 2);
  }

  const article = (t) => (/^(one|uni|eu)/i.test(t) ? 'a' : /^[aeiou]/i.test(t) ? 'an' : 'a');
  const cap = (s) => s[0].toUpperCase() + s.slice(1);
  const numberWord = (n) => ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'][n] || String(n);
  const pluralTitle = (t) => t.toLowerCase().replace(/strip$/, 'strips').replace(/loop$/, 'loops').replace(/sheet$/, 'sheets').replace(/bundle$/, 'bundles');
  const joinList = (a) => (a.length <= 1 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1]);

  return {
    WIDTH, RADIUS, LOOP_LENGTH, MAX_STRIPS, MAX_TWISTS,
    parseFraction, isValidCut, normalizeConfig,
    buildModel, cutModel,
    linkingNumber, knotDeterminant, linkDeterminant,
    createPullSim, ribbonFrame, PULL_THICKNESS,
  };
});
