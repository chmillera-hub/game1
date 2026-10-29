// Procedural Awassi-type sheep (the traditional breed of the land): lumpy wool body with
// sheen, brown face, long drooping ears, fat tail. Walk / graze / lie-down animation.
import * as THREE from 'three';
import { rng, fbm3, canvasTex, noise3 } from './util.js';

let woolMat = null, woolMatLight = null, faceMat = null, hoofMat = null, woolNormal = null;
function woolNormalTex() {
  if (woolNormal) return woolNormal;
  woolNormal = canvasTex(256, 256, (g, w, h) => {
    const img = g.createImageData(w, h);
    const H = (x, y) => 0.6 * noise3(x / 7, y / 7, 1) + 0.4 * noise3(x / 3, y / 3, 2);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const dx = H(x + 1, y) - H(x - 1, y), dy = H(x, y + 1) - H(x, y - 1);
      const i = (y * w + x) * 4;
      img.data[i] = 128 + dx * 160; img.data[i + 1] = 128 + dy * 160; img.data[i + 2] = 255; img.data[i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
  }, { srgb: false, repeat: [3, 3] });
  return woolNormal;
}
function mats() {
  if (woolMat) return;
  const base = { roughness: 1, sheen: 0.7, sheenRoughness: 0.5, normalMap: woolNormalTex(), normalScale: new THREE.Vector2(1.2, 1.2) };
  woolMat = new THREE.MeshPhysicalMaterial({ ...base, color: 0xbfb197, sheenColor: new THREE.Color(0xe8dcc4) });
  woolMatLight = new THREE.MeshPhysicalMaterial({ ...base, color: 0xd2c7b2, sheenColor: new THREE.Color(0xf0e6d4) });
  faceMat = new THREE.MeshStandardMaterial({ color: 0x4a3020, roughness: 0.8 });
  hoofMat = new THREE.MeshStandardMaterial({ color: 0x1e1612, roughness: 0.6 });
}

function woolBody(seed, rx, ry, rz, lump = 0.07) {
  const g = new THREE.SphereGeometry(1, 40, 28);
  const p = g.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const n = 1 + lump * fbm3(v.x * 3 + seed, v.y * 3, v.z * 3, 3) + lump * 0.6 * noise3(v.x * 9, v.y * 9 + seed, v.z * 9);
    // flatter belly, fuller back
    const belly = v.y < -0.3 ? 1 - 0.12 * (-v.y - 0.3) : 1;
    p.setXYZ(i, v.x * rx * n, v.y * ry * n * belly, v.z * rz * n);
  }
  g.computeVertexNormals();
  return g;
}

export function makeSheep({ seed = 1, scale = 1, lamb = false, lying = false } = {}) {
  mats();
  const r = rng(seed);
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  const s = scale * (lamb ? 0.55 : r.range(0.9, 1.08));
  root.scale.setScalar(s);
  const wm = lamb || r() < 0.25 ? woolMatLight : woolMat;
  const add = (geo, mat, parent = body) => { const m = new THREE.Mesh(geo, mat); m.castShadow = true; m.receiveShadow = true; parent.add(m); return m; };
  const by = lying ? 0.3 : 0.56;
  add(woolBody(seed, 0.26, 0.25, 0.5), wm).position.set(0, by, 0);
  add(woolBody(seed + 3, 0.15, 0.17, 0.13, 0.05), wm).position.set(0, by - 0.1, -0.44); // fat tail
  // neck + head
  const neck = new THREE.Group(); neck.position.set(0, by + 0.1, 0.42); body.add(neck);
  add(woolBody(seed + 5, 0.13, 0.15, 0.16, 0.06), wm, neck).position.set(0, 0.03, 0.06);
  const head = new THREE.Group(); head.position.set(0, 0.1, 0.2); neck.add(head);
  const hg = new THREE.SphereGeometry(1, 20, 14); hg.scale(0.085, 0.095, 0.17);
  add(hg, faceMat, head).position.set(0, 0, 0.09);
  const muzzle = new THREE.SphereGeometry(1, 14, 10); muzzle.scale(0.055, 0.06, 0.07);
  add(muzzle, faceMat, head).position.set(0, -0.025, 0.2);
  for (const sx of [-1, 1]) {
    const ear = new THREE.SphereGeometry(1, 12, 8); ear.scale(0.022, 0.09, 0.035);
    const em = add(ear, faceMat, head); em.position.set(sx * 0.075, -0.05, 0.03); em.rotation.set(0.2, 0, sx * 0.45);
    const eye = add(new THREE.SphereGeometry(0.012, 8, 6), hoofMat, head); eye.position.set(sx * 0.058, 0.02, 0.12);
  }
  head.rotation.x = 0.6;
  // legs
  const legs = [];
  if (!lying) {
    for (const [lx, lz, ph] of [[0.13, 0.28, 0], [-0.13, 0.28, Math.PI], [0.13, -0.28, Math.PI], [-0.13, -0.28, 0]]) {
      const hip = new THREE.Group(); hip.position.set(lx, 0.38, lz); body.add(hip);
      add(new THREE.CylinderGeometry(0.036, 0.024, 0.34, 8).translate(0, -0.17, 0), faceMat, hip);
      add(new THREE.CylinderGeometry(0.026, 0.028, 0.045, 8).translate(0, -0.355, 0), hoofMat, hip);
      legs.push({ hip, ph });
    }
  }
  const phase = r() * 10;
  root.userData = {
    head, neck, body, legs,
    walk(t, speed = 1) { // speed in strides per second
      const w = t * speed * Math.PI * 2 + phase;
      legs.forEach(({ hip, ph }) => { hip.rotation.x = 0.38 * Math.sin(w + ph) * Math.min(1, speed); });
      body.position.y = 0.012 * Math.abs(Math.sin(w)) * Math.min(1, speed);
      neck.rotation.x = 0.06 * Math.sin(w * 2) + (root.userData.graze || 0);
    },
    idle(t, graze = 0) {
      neck.rotation.x = graze * (0.9 + 0.1 * Math.sin(t * 0.7 + phase)) + 0.05 * Math.sin(t * 0.5 + phase);
      head.rotation.y = 0.2 * Math.sin(t * 0.31 + phase);
      legs.forEach(({ hip }) => { hip.rotation.x = 0; });
    },
  };
  return root;
}

// A flock that follows a leader along a path. path(s) -> Vector3 on the ground (s in metres).
export function makeFlock(scene, { count = 20, path, height, start = 0, spacing = 1.1, spread = 1.6, speed = 0.9, seed = 7, lambs = 3 }) {
  const r = rng(seed);
  const flock = [];
  for (let i = 0; i < count; i++) {
    const sh = makeSheep({ seed: seed * 100 + i, lamb: i >= count - lambs });
    scene.add(sh);
    flock.push({ sh, lag: i * spacing * r.range(0.6, 1.1) + r.range(0, 0.6), side: (r() - 0.5) * spread * (0.4 + Math.min(1, i / 6)), wob: r() * 10, sp: r.range(0.9, 1.1) });
  }
  const tmp = new THREE.Vector3(), ahead = new THREE.Vector3();
  return {
    flock,
    update(t) {
      for (const f of flock) {
        const sPos = start + t * speed * f.sp - f.lag;
        const p = path(sPos), q = path(sPos + 0.5);
        const dir = ahead.copy(q).sub(p).setY(0).normalize();
        const side = new THREE.Vector3(-dir.z, 0, dir.x);
        const off = f.side + 0.25 * Math.sin(t * 0.4 + f.wob);
        tmp.copy(p).addScaledVector(side, off);
        tmp.y = height ? height(tmp.x, tmp.z) : p.y;
        f.sh.position.copy(tmp);
        f.sh.lookAt(tmp.x + dir.x, tmp.y, tmp.z + dir.z);
        f.sh.userData.walk(t, 1.4 * speed * f.sp);
      }
    },
  };
}
