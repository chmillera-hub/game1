// Rolling Judean hills: a polar-grid heightfield (dense near the action, coarse far away),
// vertex-tinted PBR ground, wind-swayed grass blades and scattered photoscanned rocks.
import * as THREE from 'three';
import { pbr, loadGLTF } from './assets.js';
import { rng, fbm2, noise2, smooth } from './util.js';
import { addFogUniforms } from './sky.js';

export function hillsHeight({ amp = 18, scale = 260, center = [0, 0], flat = 25, flatH = 0, ridge = null, seed = 0 } = {}) {
  return (x, z) => {
    const dx = x - center[0], dz = z - center[1];
    const d = Math.hypot(dx, dz);
    let h = amp * fbm2(x / scale + seed, z / scale - seed, 5, 2.0, 0.5) + amp * 0.55 * fbm2(x / (scale * 3) + 7 + seed, z / (scale * 3) + 3, 3);
    h += 0.6 * fbm2(x / 9, z / 9, 3);
    if (ridge) h += ridge(x, z);
    // distant hills rise toward the horizon
    h += Math.max(0, d - 300) * 0.05 + 55 * smooth(250, 1100, d) * (0.55 + 0.45 * fbm2(x / 500 + 3, z / 500, 3));
    const k = smooth(flat * 0.6, flat * 1.6, d);
    return flatH * (1 - k) + h * k + (1 - k) * 0.25 * fbm2(x / 6, z / 6, 2);
  };
}

export async function makeTerrain(scene, {
  height, center = [0, 0], rings = 140, segs = 240, r0 = 0.5, rMax = 2400,
  texture = 'dry_ground_rocks', texRepeat = 0.25, tintA = 0xc9a878, tintB = 0x8a7458, tintNoise = 90, slopeDark = 0.5,
  roughness = 1, normalScale = 1,
} = {}) {
  const pos = [], uv = [], col = [], idx = [];
  const k = Math.log(rMax / r0 + 1) / rings;
  const A = new THREE.Color(tintA), B = new THREE.Color(tintB), c = new THREE.Color();
  pos.push(center[0], height(center[0], center[1]), center[1]); uv.push(center[0] * texRepeat, center[1] * texRepeat); col.push(A.r, A.g, A.b);
  for (let i = 1; i <= rings; i++) {
    const r = r0 * (Math.exp(k * i) - 1);
    for (let j = 0; j < segs; j++) {
      const a = (j / segs) * Math.PI * 2;
      const x = center[0] + Math.cos(a) * r, z = center[1] + Math.sin(a) * r;
      const y = height(x, z);
      pos.push(x, y, z); uv.push(x * texRepeat, z * texRepeat);
      const n = 0.5 + 0.5 * noise2(x / tintNoise, z / tintNoise) + 0.15 * noise2(x / 13, z / 13);
      c.copy(A).lerp(B, Math.min(1, Math.max(0, n)));
      col.push(c.r, c.g, c.b);
    }
  }
  for (let j = 0; j < segs; j++) idx.push(0, 1 + ((j + 1) % segs), 1 + j);
  for (let i = 1; i < rings; i++) {
    const a0 = 1 + (i - 1) * segs, a1 = 1 + i * segs;
    for (let j = 0; j < segs; j++) {
      const j1 = (j + 1) % segs;
      idx.push(a0 + j, a0 + j1, a1 + j, a0 + j1, a1 + j1, a1 + j);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  // darken steep slopes a little (rockier)
  const nrm = g.attributes.normal, cl = g.attributes.color;
  for (let i = 0; i < nrm.count; i++) {
    const s = 1 - slopeDark * (1 - nrm.getY(i));
    cl.setXYZ(i, cl.getX(i) * s, cl.getY(i) * s, cl.getZ(i) * s);
  }
  const mat = await pbr(texture, { repeat: [1, 1], roughness, normalScale });
  mat.vertexColors = true;
  const mesh = new THREE.Mesh(g, mat);
  mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
}

// Instanced grass blades with wind sway, placed on the terrain around a centre.
export function grassField(scene, { height, center = [0, 0], radius = 30, count = 30000, seed = 2, colorBase = 0x5a4a2a, colorTip = 0xd8bc84, hMin = 0.18, hMax = 0.55, avoid = null, density = null }) {
  const r = rng(seed);
  const blade = new THREE.BufferGeometry();
  blade.setAttribute('position', new THREE.Float32BufferAttribute([-0.007, 0, 0, 0.007, 0, 0, 0, 1, 0], 3));
  blade.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 1, 0, 0.5, 1], 2));
  blade.setIndex([0, 1, 2]);
  blade.computeVertexNormals();
  const geo = new THREE.InstancedBufferGeometry().copy(blade);
  const offs = new Float32Array(count * 4), rot = new Float32Array(count * 2);
  let n = 0, guard = 0;
  while (n < count && guard++ < count * 8) {
    const a = r() * Math.PI * 2, rr = radius * Math.sqrt(r());
    const x = center[0] + Math.cos(a) * rr, z = center[1] + Math.sin(a) * rr;
    if (avoid && avoid(x, z)) continue;
    if (density && r() > density(x, z)) continue;
    offs.set([x, height(x, z) - 0.02, z, r.range(hMin, hMax) * (0.7 + 0.6 * Math.max(0, noise2(x / 4, z / 4)))], n * 4);
    rot.set([r() * Math.PI * 2, r.range(-0.35, 0.35)], n * 2);
    n++;
  }
  geo.instanceCount = n;
  geo.setAttribute('offset', new THREE.InstancedBufferAttribute(offs, 4));
  geo.setAttribute('rot', new THREE.InstancedBufferAttribute(rot, 2));
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.9, side: THREE.DoubleSide });
  const uniforms = { uTime: { value: 0 }, uBase: { value: new THREE.Color(colorBase) }, uTip: { value: new THREE.Color(colorTip) } };
  mat.onBeforeCompile = (shader) => {
    addFogUniforms(shader);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec4 offset; attribute vec2 rot; uniform float uTime; varying float vH;')
      .replace('#include <begin_vertex>', `
        vec3 transformed = position;
        float hgt = offset.w;
        vH = position.y;
        transformed.y *= hgt;
        float c = cos(rot.x), s = sin(rot.x);
        transformed.xz = vec2(c * transformed.x - s * transformed.z, s * transformed.x + c * transformed.z);
        float sway = sin(uTime * 1.6 + offset.x * 0.35 + offset.z * 0.27) * 0.12 + sin(uTime * 3.1 + offset.x * 1.3) * 0.04;
        transformed.x += (rot.y + sway) * position.y * hgt;
        transformed.z += (sway * 0.6) * position.y * hgt;
        transformed += offset.xyz;`)
      .replace('#include <beginnormal_vertex>', 'vec3 objectNormal = vec3(0.0, 1.0, 0.0);');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec3 uBase; uniform vec3 uTip; varying float vH;')
      .replace('vec4 diffuseColor = vec4( diffuse, opacity );', 'vec4 diffuseColor = vec4( mix(uBase, uTip, smoothstep(0.0, 1.0, vH)), opacity );');
  };
  const mesh = new THREE.Mesh(geo, mat);
  mesh.frustumCulled = false;
  mesh.receiveShadow = true;
  mesh.castShadow = false;
  mesh.userData.uniforms = uniforms;
  scene.add(mesh);
  return mesh;
}

// Instance a (multi-mesh) glTF model at many transforms.
export async function scatterModel(scene, id, transforms, { castShadow = true, receiveShadow = true, tint = null } = {}) {
  const g = await loadGLTF(id);
  const meshes = [];
  g.scene.updateMatrixWorld(true);
  g.scene.traverse((o) => { if (o.isMesh) meshes.push(o); });
  const out = [];
  const m4 = new THREE.Matrix4();
  for (const src of meshes) {
    let mat = src.material;
    if (tint) { mat = mat.clone(); mat.color = new THREE.Color(tint); }
    const im = new THREE.InstancedMesh(src.geometry, mat, transforms.length);
    transforms.forEach((t, i) => im.setMatrixAt(i, m4.copy(t).multiply(src.matrixWorld)));
    im.castShadow = castShadow; im.receiveShadow = receiveShadow;
    im.instanceMatrix.needsUpdate = true;
    scene.add(im); out.push(im);
  }
  return out;
}
export function placeOn(height, x, z, { scale = 1, yaw = 0, sink = 0, tilt = 0 } = {}) {
  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(tilt, yaw, tilt * 0.5));
  m.compose(new THREE.Vector3(x, height(x, z) - sink, z), q, new THREE.Vector3(scale, scale, scale));
  return m;
}
