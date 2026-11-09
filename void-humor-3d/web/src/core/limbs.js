// Procedural limbs: swept tubes (updated in place every frame), 2-bone IK and cartoon hands.
import * as THREE from 'three';
import { clamp, lerp } from './util.js';

const _v = new THREE.Vector3(), _a = new THREE.Vector3(), _b = new THREE.Vector3(), _c = new THREE.Vector3();

/**
 * SweepTube — a tube swept along a smooth curve through control points, with a per-sample radius and
 * rounded (hemispherical) end caps. Geometry is preallocated and rewritten in place by update().
 *   const t = new SweepTube({ material, segments: 20, radial: 10, capRings: 4 });
 *   parent.add(t.mesh);
 *   t.update(points, radius, { up, flatten, capStart, capEnd });
 * points: Vector3[] (>=2) in the parent's space.  radius: number | number[] (per control point, interpolated)
 *   | (s in 0..1) => number.  up: Vector3 reference for the elliptical cross-section orientation (or fn(s)).
 * flatten: 0..1 squashes the cross-section along `up` (brows, lips...).  capStart/capEnd: bool (default true).
 */
export class SweepTube {
  constructor({ material, segments = 20, radial = 10, capRings = 4, castShadow = false } = {}) {
    this.S = segments; this.R = radial; this.C = capRings;
    this.rings = segments + 1 + 2 * capRings;
    const nv = this.rings * radial + 2;
    const g = new THREE.BufferGeometry();
    this.pos = new Float32Array(nv * 3);
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(nv * 3), 3).setUsage(THREE.DynamicDrawUsage));
    const idx = [];
    for (let r = 0; r < this.rings - 1; r++) {
      for (let j = 0; j < radial; j++) {
        const a = r * radial + j, b = r * radial + ((j + 1) % radial), c = (r + 1) * radial + j, d = (r + 1) * radial + ((j + 1) % radial);
        idx.push(a, b, c, b, d, c);
      }
    }
    const tipA = this.rings * radial, tipB = tipA + 1;
    for (let j = 0; j < radial; j++) {
      idx.push(tipA, (j + 1) % radial, j);
      const last = (this.rings - 1) * radial;
      idx.push(tipB, last + j, last + ((j + 1) % radial));
    }
    g.setIndex(idx);
    this.geo = g;
    this.mesh = new THREE.Mesh(g, material);
    this.mesh.frustumCulled = false;
    this.mesh.castShadow = castShadow;
    this.curve = new THREE.CatmullRomCurve3([new THREE.Vector3(), new THREE.Vector3(0, 1, 0)], false, 'centripetal');
  }

  update(points, radius, opts = {}) {
    const { S, R, C } = this;
    const pts = points.map((p) => (p instanceof THREE.Vector3 ? p : new THREE.Vector3(...p)));
    if (pts.length === 2) pts.splice(1, 0, pts[0].clone().lerp(pts[1], 0.5));
    this.curve.points = pts;
    this.curve.needsUpdate = true;   // invalidate the cached arc-length table (else getPointAt() uses the previous frame's)
    const rad = typeof radius === 'function' ? radius
      : Array.isArray(radius) ? (s) => { const f = s * (radius.length - 1); const i = Math.min(radius.length - 2, Math.floor(f)); return lerp(radius[i], radius[i + 1], f - i); }
      : () => radius;
    const flatten = opts.flatten ?? 0;
    const upFn = typeof opts.up === 'function' ? opts.up : null;
    const up0 = opts.up && !upFn ? opts.up.clone().normalize() : null;
    // sample centreline
    const P = [], Tn = [], Rr = [];
    for (let i = 0; i <= S; i++) {
      const s = i / S;
      P.push(this.curve.getPointAt(s));
      Tn.push(this.curve.getTangentAt(s).normalize());
      Rr.push(Math.max(1e-5, rad(s)));
    }
    // frames: parallel transport, seeded by `up`
    const N = [], B = [];
    let n0 = up0 ? up0.clone() : (upFn ? upFn(0).clone().normalize() : null);
    if (!n0 || Math.abs(n0.dot(Tn[0])) > 0.98) { n0 = Math.abs(Tn[0].y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0); }
    n0.sub(_v.copy(Tn[0]).multiplyScalar(n0.dot(Tn[0]))).normalize();
    N.push(n0); B.push(new THREE.Vector3().crossVectors(Tn[0], n0).normalize());
    for (let i = 1; i <= S; i++) {
      let n;
      if (upFn || up0) {
        n = (upFn ? upFn(i / S).clone() : up0.clone());
        n.sub(_v.copy(Tn[i]).multiplyScalar(n.dot(Tn[i])));
        if (n.lengthSq() < 1e-8) n = N[i - 1].clone(); else n.normalize();
      } else {
        n = N[i - 1].clone().sub(_v.copy(Tn[i]).multiplyScalar(N[i - 1].dot(Tn[i]))).normalize();
      }
      N.push(n); B.push(new THREE.Vector3().crossVectors(Tn[i], n).normalize());
    }
    const pos = this.pos;
    let k = 0;
    const capStart = opts.capStart !== false, capEnd = opts.capEnd !== false;
    const writeRing = (c, n, b, r, sq) => {
      for (let j = 0; j < R; j++) {
        const a = (j / R) * Math.PI * 2;
        const cx = Math.cos(a) * r * (1 - flatten * 0.7) * sq, cy = Math.sin(a) * r * sq;
        pos[k++] = c.x + n.x * cx + b.x * cy; pos[k++] = c.y + n.y * cx + b.y * cy; pos[k++] = c.z + n.z * cx + b.z * cy;
      }
    };
    // start cap rings (from tip toward the body)
    for (let i = 0; i < C; i++) {
      const ang = (Math.PI / 2) * (1 - (i + 1) / (C + 1));
      const off = capStart ? Math.sin(ang) * Rr[0] : 0;
      const sq = capStart ? Math.cos(ang) : 1;
      _a.copy(P[0]).addScaledVector(Tn[0], -off);
      writeRing(_a, N[0], B[0], Rr[0], sq);
    }
    for (let i = 0; i <= S; i++) writeRing(P[i], N[i], B[i], Rr[i], 1);
    for (let i = 0; i < C; i++) {
      const ang = (Math.PI / 2) * ((i + 1) / (C + 1));
      const off = capEnd ? Math.sin(ang) * Rr[S] : 0;
      const sq = capEnd ? Math.cos(ang) : 1;
      _a.copy(P[S]).addScaledVector(Tn[S], off);
      writeRing(_a, N[S], B[S], Rr[S], sq);
    }
    // tips
    _a.copy(P[0]).addScaledVector(Tn[0], capStart ? -Rr[0] : 0);
    pos[k++] = _a.x; pos[k++] = _a.y; pos[k++] = _a.z;
    _a.copy(P[S]).addScaledVector(Tn[S], capEnd ? Rr[S] : 0);
    pos[k++] = _a.x; pos[k++] = _a.y; pos[k++] = _a.z;
    this.geo.attributes.position.needsUpdate = true;
    this.geo.computeVertexNormals();
    this.geo.attributes.normal.needsUpdate = true;
    this.geo.computeBoundingSphere();
    return this;
  }
}

/**
 * Two-bone IK. root, target: Vector3. l1, l2: bone lengths. pole: Vector3 direction hint (where the
 * elbow/knee should point). Returns { mid, end } (end is clamped to reach).
 */
export function solveIK2(root, target, l1, l2, pole) {
  const d = _a.copy(target).sub(root);
  let dist = d.length();
  const maxR = (l1 + l2) * 0.999, minR = Math.abs(l1 - l2) * 1.001 + 1e-4;
  const dir = d.clone().normalize();
  dist = clamp(dist, minR, maxR);
  const end = root.clone().addScaledVector(dir, dist);
  const cosA = clamp((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist), -1, 1);
  const a = Math.acos(cosA);
  const p = pole.clone().sub(_b.copy(dir).multiplyScalar(pole.dot(dir)));
  if (p.lengthSq() < 1e-8) p.set(0, 0, 1).sub(_b.copy(dir).multiplyScalar(dir.z));
  p.normalize();
  const mid = root.clone().addScaledVector(dir, Math.cos(a) * l1).addScaledVector(p, Math.sin(a) * l1);
  return { mid, end };
}

/** Orient an Object3D so its local +Y points along `yDir` and local +Z is as close as possible to `zHint`. */
export function orientYZ(obj, yDir, zHint) {
  const y = _a.copy(yDir).normalize();
  const x = _b.crossVectors(y, zHint).normalize();
  if (x.lengthSq() < 1e-8) x.set(1, 0, 0);
  const z = _c.crossVectors(x, y).normalize();
  const m = new THREE.Matrix4().makeBasis(x, y, z);
  obj.quaternion.setFromRotationMatrix(m);
  return obj;
}

/**
 * Hand — cartoon hand made of a palm and capsule fingers (no per-frame geometry rebuild).
 *   const h = new Hand({ size: 0.09, fingers: 4, side: 'R', material, nailColor })
 *   parent.add(h.root)
 *   h.root.position.copy(wrist); h.aim(fingerDir, palmNormal)   // world-or-parent-space directions
 *   h.pose({ curl, spread, point, thumb, fist, cup, splay })    // all 0..1
 * Local frame: wrist at origin, fingers extend along +Y, palm faces -Z, thumb on the +X side for a RIGHT
 * hand (mirrored for 'L'). size = wrist→middle fingertip length.
 */
export class Hand {
  constructor({ size = 0.1, fingers = 4, side = 'R', material, palmMaterial, thick = 1, fingerLen = 1, castShadow = false } = {}) {
    this.size = size; this.side = side; this.nF = fingers;
    const s = side === 'L' ? -1 : 1;
    this.root = new THREE.Group();
    this.palmGroup = new THREE.Group();
    this.root.add(this.palmGroup);
    const palmL = size * 0.46, palmW = size * (fingers >= 4 ? 0.42 : 0.46) * thick, palmT = size * 0.16 * thick;
    const palm = new THREE.Mesh(new THREE.SphereGeometry(0.5, 20, 14), palmMaterial || material);
    palm.scale.set(palmW, palmL, palmT * 1.6); palm.position.y = palmL * 0.48;
    palm.castShadow = castShadow;
    this.palmGroup.add(palm);
    this.palm = palm;
    this.fingers = [];
    const fr = size * 0.062 * thick;
    const lens = fingers === 4 ? [0.92, 1.0, 0.95, 0.78] : fingers === 3 ? [0.95, 1.0, 0.88] : [1, 1, 1, 1, 1].slice(0, fingers);
    for (let i = 0; i < fingers; i++) {
      const u = fingers === 1 ? 0 : (i / (fingers - 1) - 0.5);
      const base = new THREE.Group();
      base.position.set(s * u * palmW * 0.82, palmL * 0.95, 0);
      this.palmGroup.add(base);
      const L = size * 0.5 * lens[i] * fingerLen;
      const segs = [];
      let parent = base;
      const segLen = [0.42, 0.33, 0.25].map((f) => f * L);
      for (let j = 0; j < 3; j++) {
        const g = new THREE.Group();
        if (j > 0) g.position.y = segLen[j - 1];
        const r = fr * (1 - j * 0.1);
        const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, Math.max(1e-4, segLen[j] - r * 0.6), 4, 10), material);
        m.position.y = segLen[j] / 2; m.castShadow = castShadow;
        g.add(m); parent.add(g); parent = g; segs.push(g);
      }
      this.fingers.push({ base, segs, u });
    }
    // thumb
    const tb = new THREE.Group();
    tb.position.set(s * palmW * 0.45, palmL * 0.2, -palmT * 0.2);
    this.palmGroup.add(tb);
    const tsegs = []; let par = tb;
    const tl = [0.26, 0.2].map((f) => f * size);
    for (let j = 0; j < 2; j++) {
      const g = new THREE.Group();
      if (j > 0) g.position.y = tl[j - 1];
      const r = fr * 1.12;
      const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, Math.max(1e-4, tl[j] - r * 0.5), 4, 10), material);
      m.position.y = tl[j] / 2; m.castShadow = castShadow;
      g.add(m); par.add(g); par = g; tsegs.push(g);
    }
    this.thumb = { base: tb, segs: tsegs };
    this.pose({});
  }

  /** Aim: fingers along fingerDir, palm facing palmNormal (both in the PARENT's space). */
  aim(fingerDir, palmNormal) {
    // local -Z = palm normal -> local +Z = -palmNormal
    return orientYZ(this.root, fingerDir, _v.copy(palmNormal).multiplyScalar(-1));
  }

  /**
   * pose params (0..1 unless noted):
   *  curl   all fingers curl (0 straight .. 1 fist)        point  index straight, others curled
   *  spread fingers fan out                                 thumb  0 alongside .. 1 thumb out/up
   *  cup    palm cups slightly (gentle hold)                splay  hyper-extend (startled/hands up) 0..1
   *  grip   wrap around a cylinder (phone/handle)           perFinger: [c0,c1,c2,c3] optional curl overrides
   */
  pose({ curl = 0.15, point = 0, spread = 0.15, thumb = 0.3, cup = 0.1, splay = 0, grip = 0, perFinger = null } = {}) {
    const s = this.side === 'L' ? -1 : 1;
    this.fingers.forEach((f, i) => {
      const isIndex = i === 0;
      let c = perFinger ? perFinger[i] : curl;
      c = lerp(c, isIndex ? 0 : 1, point);
      c = lerp(c, 0.55, grip);
      const bend = c * 1.45 + cup * 0.25 - splay * 0.25;
      f.base.rotation.set(-bend * 0.9, 0, -s * f.u * spread * 0.9);
      f.segs[1].rotation.x = -bend * 1.0;
      f.segs[2].rotation.x = -bend * 0.8;
    });
    const tOut = thumb;
    this.thumb.base.rotation.set(-0.3 - curl * 0.5 * (1 - tOut) - grip * 0.4, s * (0.2 + tOut * 0.5), -s * (0.5 + tOut * 0.6));
    this.thumb.segs[1].rotation.x = -(curl * 0.9 + grip * 0.5) * (1 - tOut * 0.7);
    return this;
  }
}

/**
 * Limb — IK arm/leg drawn as one swept tube (shoulder→elbow→wrist), optional sleeve flare, plus Hand.
 *   const arm = new Limb({ material, upper: 0.3, lower: 0.28, radius: [0.05, 0.045, 0.04], hand: Hand|null })
 *   arm.update(shoulder, target, pole, { bendExtra })   // parent-space Vector3s
 * Returns the solved points; the hand (if any) is positioned at the wrist and aimed along the forearm by
 * default (call arm.hand.aim() afterwards to override). `soft` adds rubber-hose curvature (0..1).
 */
export class Limb {
  constructor({ material, upper = 0.3, lower = 0.28, radius = [0.05, 0.045, 0.04], segments = 16, radial = 10, hand = null, soft = 0.25, castShadow = false }) {
    this.tube = new SweepTube({ material, segments, radial, castShadow });
    this.l1 = upper; this.l2 = lower; this.radius = radius; this.soft = soft;
    this.group = new THREE.Group();
    this.group.add(this.tube.mesh);
    this.hand = hand;
    if (hand) this.group.add(hand.root);
  }
  update(root, target, pole, { radius = null, palmNormal = null, fingerDir = null, reach = 1, capEnd = true } = {}) {
    const tgt = reach < 1 ? root.clone().lerp(target, reach) : target;
    const { mid, end } = solveIK2(root, tgt, this.l1, this.l2, pole);
    // rubber-hose softening: pull the elbow point toward the chord a little, add intermediate points
    const chordMid = root.clone().lerp(end, 0.5);
    const m2 = mid.clone().lerp(chordMid, this.soft * 0.35);
    const p1 = root.clone().lerp(m2, 0.55), p2 = m2.clone().lerp(end, 0.45);
    this.tube.update([root, p1, m2, p2, end], radius || this.radius, { capEnd });
    this.mid = mid; this.end = end;
    if (this.hand) {
      this.hand.root.position.copy(end);
      const fd = fingerDir ? fingerDir.clone() : end.clone().sub(m2).normalize();
      const pn = palmNormal ? palmNormal.clone() : _v.set(0, -1, 0).clone();
      this.hand.aim(fd, pn);
    }
    return { root, mid, end };
  }
}
