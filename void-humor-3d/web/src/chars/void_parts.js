// Building blocks for the Void rig (chars/void.js): a merged one-draw-call mitt hand with smooth swept fingers,
// a flared open sleeve cuff (with a dark lining) the hand comes out of, and a small in-place tube writer.
// All geometry is preallocated and rewritten in place; normals are analytic (no computeVertexNormals per frame).
import * as THREE from 'three';
import { orientYZ } from '../core/limbs.js';
import { clamp, lerp } from '../core/util.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const _a = V(), _b = V(), _c = V(), _t = V(), _n = V(), _bn = V();

/** Uniform Catmull-Rom through pts (array of Vector3), u in 0..1 -> out */
function crPoint(pts, u, out) {
  const n = pts.length - 1, f = clamp(u, 0, 1) * n, i = Math.min(n - 1, Math.floor(f)), s = f - i;
  const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(n, i + 2)];
  const s2 = s * s, s3 = s2 * s;
  const a = -0.5 * s3 + s2 - 0.5 * s, b = 1.5 * s3 - 2.5 * s2 + 1, c = -1.5 * s3 + 2 * s2 + 0.5 * s, d = 0.5 * s3 - 0.5 * s2;
  return out.set(p0.x * a + p1.x * b + p2.x * c + p3.x * d, p0.y * a + p1.y * b + p2.y * c + p3.y * d, p0.z * a + p1.z * b + p2.z * c + p3.z * d);
}

/**
 * TubeWriter — writes a capped tube (open start buried inside something, rounded end cap) into a slice of
 * shared position/normal arrays. rings = S+1 body rings + C cap rings, R verts each, + 1 tip vertex.
 */
export class TubeWriter {
  constructor(S, R, C, offset) {
    this.S = S; this.R = R; this.C = C; this.off = offset;
    this.count = (S + 1 + C) * R + 1;
    this.P = Array.from({ length: S + 1 }, () => V()); this.T = Array.from({ length: S + 1 }, () => V());
    this.cos = Float32Array.from({ length: R }, (_, j) => Math.cos(j / R * Math.PI * 2));
    this.sin = Float32Array.from({ length: R }, (_, j) => Math.sin(j / R * Math.PI * 2));
  }
  indices(idx) {
    const { R, off } = this, rings = this.S + 1 + this.C;
    for (let r = 0; r < rings - 1; r++) for (let j = 0; j < R; j++) {
      const a = off + r * R + j, b = off + r * R + (j + 1) % R, c = off + (r + 1) * R + j, d = off + (r + 1) * R + (j + 1) % R;
      idx.push(a, b, c, b, d, c);
    }
    const tip = off + rings * R, last = off + (rings - 1) * R;
    for (let j = 0; j < R; j++) idx.push(last + j, last + (j + 1) % R, tip);
  }
  /** pts: control points (Vector3[]), rad(s) radius function, up: seed normal (Vector3) */
  write(pos, nrm, pts, rad, up) {
    const { S, R, C } = this, P = this.P, T = this.T;
    for (let i = 0; i <= S; i++) crPoint(pts, i / S, P[i]);
    for (let i = 0; i <= S; i++) T[i].subVectors(P[Math.min(S, i + 1)], P[Math.max(0, i - 1)]).normalize();
    _n.copy(up).addScaledVector(T[0], -up.dot(T[0]));
    if (_n.lengthSq() < 1e-8) _n.set(1, 0, 0).addScaledVector(T[0], -T[0].x);
    _n.normalize();
    let k = this.off * 3;
    const ring = (c, t, r, sq, nOff) => {
      _bn.crossVectors(t, _n);
      for (let j = 0; j < R; j++) {
        const cx = this.cos[j], cy = this.sin[j];
        const dx = _n.x * cx + _bn.x * cy, dy = _n.y * cx + _bn.y * cy, dz = _n.z * cx + _bn.z * cy;
        pos[k] = c.x + dx * r * sq; pos[k + 1] = c.y + dy * r * sq; pos[k + 2] = c.z + dz * r * sq;
        const nx = dx * sq + t.x * nOff, ny = dy * sq + t.y * nOff, nz = dz * sq + t.z * nOff, l = Math.hypot(nx, ny, nz) || 1;
        nrm[k] = nx / l; nrm[k + 1] = ny / l; nrm[k + 2] = nz / l;
        k += 3;
      }
    };
    for (let i = 0; i <= S; i++) {
      if (i > 0) { _n.addScaledVector(T[i], -_n.dot(T[i])).normalize(); }   // parallel transport
      ring(P[i], T[i], rad(i / S), 1, 0);
    }
    const rE = rad(1), tE = T[S], pE = P[S];
    for (let i = 0; i < C; i++) {
      const ang = (Math.PI / 2) * ((i + 1) / (C + 1));
      _c.copy(pE).addScaledVector(tE, Math.sin(ang) * rE);
      ring(_c, tE, rE, Math.cos(ang), Math.sin(ang));
    }
    _c.copy(pE).addScaledVector(tE, rE);
    pos[k] = _c.x; pos[k + 1] = _c.y; pos[k + 2] = _c.z; nrm[k] = tE.x; nrm[k + 1] = tE.y; nrm[k + 2] = tE.z;
  }
}

/**
 * VoidHand — big soft mitt: wide pillowy palm + wrist stub, 3 fat fingers + thumb as smooth swept tubes, all in
 * ONE mesh (one draw call). Same API as core Hand: root, aim(fingerDir, palmNormal), pose({curl, point, spread,
 * thumb, cup, splay, grip, perFinger}). Local frame: wrist at the origin, fingers +Y, palm faces -Z, thumb on
 * the anatomically correct side (LEFT hand +X, RIGHT hand -X).
 */
export class VoidHand {
  constructor({ size = 0.44, side = 'R', material }) {
    this.size = size; this.side = side;
    const ts = this.ts = side === 'L' ? 1 : -1;
    this.root = new THREE.Group();
    const pl = this.pl = size * 0.47, pw = this.pw = size * 0.9, pt = this.pt = size * 0.3;
    // static parts: palm pillow + wrist stub (baked once)
    const palm = new THREE.SphereGeometry(1, 22, 14);
    { const p = palm.attributes.position;
      for (let i = 0; i < p.count; i++) {
        let x = p.getX(i), y = p.getY(i), z = p.getZ(i);
        if (z < 0) z *= 0.72;                                    // flatter palm side, rounder back
        x *= 1 + 0.12 * y;                                       // wider at the knuckles than at the heel
        p.setXYZ(i, x * pw * 0.5, y * pl * 0.58 + pl * 0.52, z * pt * 0.5);
      }
      palm.computeVertexNormals(); }
    const wrist = new THREE.SphereGeometry(1, 16, 10);
    wrist.scale(size * 0.26, size * 0.34, size * 0.2); wrist.translate(0, -size * 0.04, size * 0.01);
    const statics = [palm, wrist];
    const nStatic = statics.reduce((s, g) => s + g.attributes.position.count, 0);
    // fingers: index (thumb side), middle, outer
    const lens = [0.92, 1.0, 0.86];
    const fr = size * 0.14;
    this.fingers = [0, 1, 2].map((i) => {
      const u = i - 1;                                           // -1 thumb side .. +1
      return { i, u, base: V(-ts * u * pw * 0.3, pl * 0.86, -pt * 0.02), segs: [0.44, 0.31, 0.25].map((f) => f * size * 0.5 * lens[i]), r: fr * (i === 2 ? 0.93 : 1), pts: [V(), V(), V(), V(), V()] };
    });
    this.thumb = { base: V(ts * pw * 0.36, pl * 0.3, -pt * 0.12), segs: [0.17, 0.16, 0.13].map((f) => f * size), r: fr * 1.1, pts: [V(), V(), V(), V()] };
    let off = nStatic;
    for (const f of [...this.fingers, this.thumb]) { f.w = new TubeWriter(8, 10, 3, off); off += f.w.count; }
    const nv = off;
    this.pos = new Float32Array(nv * 3); this.nrm = new Float32Array(nv * 3);
    const idx = [];
    let vo = 0;
    for (const g of statics) {
      this.pos.set(g.attributes.position.array, vo * 3); this.nrm.set(g.attributes.normal.array, vo * 3);
      for (const k of g.index.array) idx.push(k + vo);
      vo += g.attributes.position.count;
    }
    for (const f of [...this.fingers, this.thumb]) f.w.indices(idx);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage));
    geo.setAttribute('normal', new THREE.BufferAttribute(this.nrm, 3).setUsage(THREE.DynamicDrawUsage));
    geo.setIndex(idx);
    this.geo = geo;
    this.mesh = new THREE.Mesh(geo, material);
    this.mesh.frustumCulled = false;
    this.root.add(this.mesh);
    this.palmCentre = V(0, pl * 0.52, -pt * 0.36);              // on the palm surface (contact point)
    this.indexTip = V();
    this._key = '';
    this.pose({});
  }
  aim(fingerDir, palmNormal) { return orientYZ(this.root, fingerDir, palmNormal.clone().multiplyScalar(-1)); }
  pose({ curl = 0.15, point = 0, spread = 0.15, thumb = 0.3, cup = 0.1, splay = 0, grip = 0, perFinger = null } = {}) {
    const key = [curl, point, spread, thumb, cup, splay, grip].map((v) => v.toFixed(3)).join(',') + (perFinger ? perFinger.join(',') : '');
    if (key === this._key) return this;
    this._key = key;
    const ts = this.ts, pn = _a.set(0, 0, -1), up = V(0, 0, 1);
    for (const f of this.fingers) {
      let c = perFinger ? perFinger[f.i] : curl;
      c = lerp(c, f.i === 0 ? 0 : 1, point);
      c = lerp(c, 0.55, grip);
      const mcp = c * 1.25 + cup * 0.32 - splay * 0.38 + f.i * 0.04 * c;
      const pip = c * 1.5 + cup * 0.12 - splay * 0.1;
      const dip = c * 0.9 + cup * 0.06;
      const fan = ts * f.u * (spread * 0.32 + 0.06);
      const fd = V(-Math.sin(fan), Math.cos(fan), 0);
      const dirAt = (a) => fd.clone().multiplyScalar(Math.cos(a)).addScaledVector(pn, Math.sin(a));
      const P = f.pts;
      P[0].copy(f.base).addScaledVector(fd, -f.r * 1.4);
      P[1].copy(f.base);
      P[2].copy(P[1]).addScaledVector(dirAt(mcp), f.segs[0]);
      P[3].copy(P[2]).addScaledVector(dirAt(mcp + pip), f.segs[1]);
      P[4].copy(P[3]).addScaledVector(dirAt(mcp + pip + dip), f.segs[2] - f.r * 0.6);
      const r = f.r;
      f.w.write(this.pos, this.nrm, P, (s) => r * (1.04 - 0.14 * s), up);
      if (f.i === 0) this.indexTip.copy(P[4]).addScaledVector(_b.subVectors(P[4], P[3]).normalize(), r * 0.9);
    }
    const T = this.thumb, P = T.pts;
    const across = clamp(curl * 0.8 + grip * 0.6 + cup * 0.35);
    const d0 = V(ts * lerp(0.42, 0.95, thumb), lerp(0.85, 0.35, thumb), -0.3).normalize();
    d0.lerp(V(-ts * 0.1, 0.55, -0.85), across * 0.6).normalize();
    const bendAx = V(-ts * 0.45, 0, -0.9).normalize();
    const d1 = d0.clone().addScaledVector(bendAx, 0.22 + across * 0.6).normalize();
    const d2 = d1.clone().addScaledVector(bendAx, 0.18 + across * 0.8).normalize();
    P[0].copy(T.base).addScaledVector(d0, -T.r * 1.2);
    P[1].copy(P[0]).addScaledVector(d0, T.segs[0] + T.r * 1.2);
    P[2].copy(P[1]).addScaledVector(d1, T.segs[1]);
    P[3].copy(P[2]).addScaledVector(d2, T.segs[2] - T.r * 0.6);
    T.w.write(this.pos, this.nrm, P, (s) => T.r * (1.08 - 0.2 * s), up);
    this.geo.attributes.position.needsUpdate = true; this.geo.attributes.normal.needsUpdate = true;
    return this;
  }
}

/**
 * Cuff — a wide, flared, open sleeve end (velvet outside, dark lining inside) around the forearm at the wrist.
 * update(wrist, dir, ref, down, k): root-space wrist point, forearm direction (toward the hand), a reference
 * vector for the seam, world-down in the same space, scale k. The hem hangs a little lower on the gravity side.
 */
export class Cuff {
  constructor(outer, lining) {
    // profile [radial, axial]: outer shell (back -> lip), rolled lip, lining going back inside
    this.prof = [[0.158, -0.4], [0.163, -0.3], [0.176, -0.2], [0.195, -0.12], [0.215, -0.05], [0.229, 0.0], [0.236, 0.02],
      [0.231, 0.038], [0.217, 0.043], [0.203, 0.03], [0.192, 0.0], [0.176, -0.08], [0.156, -0.2]];
    this.NL = 9;                                   // rows [0, NL] are velvet; the rest is lining
    const NP = this.prof.length, NC = this.NC = 26;
    this.pos = new Float32Array(NP * (NC + 1) * 3);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(this.pos.length), 3).setUsage(THREE.DynamicDrawUsage));
    const idx = [];
    for (let r = 0; r < NP - 1; r++) for (let j = 0; j < NC; j++) {
      const a = r * (NC + 1) + j, b = a + 1, c = a + NC + 1, d = c + 1;
      idx.push(a, b, c, b, d, c);
    }
    g.setIndex(idx);
    g.addGroup(0, this.NL * NC * 6, 0);
    g.addGroup(this.NL * NC * 6, (NP - 1 - this.NL) * NC * 6, 1);
    this.geo = g;
    this.mesh = new THREE.Mesh(g, [outer, lining]);
    this.mesh.frustumCulled = false;
  }
  update(wrist, dir, ref, down, k = 1) {
    const ax = _t.copy(dir).normalize();
    const e1 = _a.copy(ref).addScaledVector(ax, -ref.dot(ax));
    if (e1.lengthSq() < 1e-6) e1.set(1, 0, 0).addScaledVector(ax, -ax.x);
    e1.normalize();
    const e2 = _b.crossVectors(ax, e1).normalize();
    const gp = _c.copy(down).addScaledVector(ax, -down.dot(ax));   // gravity across the sleeve
    const gl = gp.length(); if (gl > 1e-6) gp.multiplyScalar(1 / gl);
    const NP = this.prof.length, NC = this.NC, pos = this.pos;
    for (let j = 0; j <= NC; j++) {
      const a = (j / NC) * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a);
      const dx = e1.x * ca + e2.x * sa, dy = e1.y * ca + e2.y * sa, dz = e1.z * ca + e2.z * sa;
      const gw = Math.max(0, dx * gp.x + dy * gp.y + dz * gp.z) * gl;
      const sag = gw * gw;
      for (let r = 0; r < NP; r++) {
        const [rr, aa] = this.prof[r];
        const lip = clamp((aa + 0.3) / 0.33);              // 0 at the back of the cuff .. 1 at the lip
        const R = (rr + 0.022 * sag * lip) * k, A = (aa + 0.065 * sag * lip) * k;
        const kk = (r * (NC + 1) + j) * 3;
        pos[kk] = wrist.x + ax.x * A + dx * R + gp.x * 0.02 * sag * lip * k;
        pos[kk + 1] = wrist.y + ax.y * A + dy * R + gp.y * 0.02 * sag * lip * k;
        pos[kk + 2] = wrist.z + ax.z * A + dz * R + gp.z * 0.02 * sag * lip * k;
      }
    }
    this.geo.attributes.position.needsUpdate = true;
    this.geo.computeVertexNormals();
    // close the seam
    const n = this.geo.attributes.normal.array;
    for (let r = 0; r < NP; r++) {
      const a = r * (NC + 1) * 3, b = (r * (NC + 1) + NC) * 3;
      for (let q = 0; q < 3; q++) { const m = (n[a + q] + n[b + q]) / 2; n[a + q] = n[b + q] = m; }
    }
  }
}
