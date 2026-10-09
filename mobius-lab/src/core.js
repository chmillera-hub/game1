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
    return polyLength(mids);
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
    const p = project(points);
    const n = p.length;
    const box = segBoxes(p);
    const crossings = [];
    for (let i = 0; i < n; i++) {
      for (let j = i + 2; j < n; j++) {
        if (i === 0 && j === n - 1) continue;
        if (box[4 * i + 1] < box[4 * j] || box[4 * j + 1] < box[4 * i] || box[4 * i + 3] < box[4 * j + 2] || box[4 * j + 3] < box[4 * i + 2]) continue;
        const h = crossSegments(p[i], p[(i + 1) % n], p[j], p[(j + 1) % n]);
        if (!h) continue;
        const pi = i + h.t, pj = j + h.u;
        crossings.push(h.za > h.zb ? { over: pi, under: pj } : { over: pj, under: pi });
      }
    }
    const m = crossings.length;
    if (m < 3) return 1;
    const order = crossings.map((c, idx) => idx).sort((x, y) => crossings[x].under - crossings[y].under);
    const rank = new Int32Array(m);
    order.forEach((idx, r) => (rank[idx] = r));
    const sorted = order.map((idx) => crossings[idx].under);
    const arcAt = (pos) => {
      let lo = 0, hi = m - 1, ans = -1;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (sorted[mid] < pos) { ans = mid; lo = mid + 1; } else hi = mid - 1;
      }
      return ans < 0 ? m - 1 : ans;
    };
    const M = Array.from({ length: m }, () => new Float64Array(m));
    crossings.forEach((c, idx) => {
      const r = rank[idx];
      M[r][arcAt(c.over)] += 2;
      M[r][(r - 1 + m) % m] -= 1;
      M[r][r] -= 1;
    });
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
      p.linkedWith = links.filter((l) => l.a === i || l.b === i).map((l) => ({ piece: l.a === i ? l.b : l.a, lk: l.lk }));
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
    linkingNumber, knotDeterminant,
  };
});
