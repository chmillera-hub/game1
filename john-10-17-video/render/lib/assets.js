// Loaders for the CC0 Poly Haven assets (served under /assets/) with caching.
import * as THREE from 'three';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const texCache = new Map();
const hdrCache = new Map();
const gltfCache = new Map();
const texLoader = new THREE.TextureLoader();
const rgbe = new RGBELoader();
const gltfLoader = new GLTFLoader();

export function loadTexture(url, { srgb = false, repeat = null, aniso = 8 } = {}) {
  const key = url + (srgb ? '|s' : '');
  if (!texCache.has(key)) {
    texCache.set(key, new Promise((res, rej) => texLoader.load(url, (t) => {
      t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.anisotropy = aniso;
      res(t);
    }, undefined, rej)));
  }
  return texCache.get(key).then((t) => {
    if (!repeat) return t;
    const c = t.clone(); c.repeat.set(repeat[0], repeat[1]); c.needsUpdate = true; return c;
  });
}

export function loadHDR(id, res = '4k') {
  const url = `/assets/hdri/${id}_${res}.hdr`;
  if (!hdrCache.has(url)) {
    hdrCache.set(url, new Promise((ok, rej) => rgbe.load(url, (t) => {
      t.mapping = THREE.EquirectangularReflectionMapping;
      t.wrapS = THREE.RepeatWrapping;
      t.minFilter = THREE.LinearFilter; t.magFilter = THREE.LinearFilter; t.generateMipmaps = false;
      ok(t);
    }, undefined, rej)));
  }
  return hdrCache.get(url);
}

// PBR material from a Poly Haven texture set (diff / nor_gl / arm or rough+ao).
export async function pbr(id, { res = '2k', repeat = [1, 1], color = 0xffffff, roughness = 1, normalScale = 1, aoIntensity = 1, envMapIntensity = 1, physical = false, extra = {} } = {}) {
  const base = `/assets/tex/${id}`;
  const exists = async (u) => (await fetch(u, { method: 'HEAD' })).ok;
  const diff = await loadTexture(`${base}/diff_${res}.jpg`, { srgb: true, repeat });
  const nor = await loadTexture(`${base}/nor_gl_${res}.jpg`, { repeat });
  let arm = null, rough = null, ao = null;
  if (await exists(`${base}/arm_${res}.jpg`)) arm = await loadTexture(`${base}/arm_${res}.jpg`, { repeat });
  else {
    if (await exists(`${base}/rough_${res}.jpg`)) rough = await loadTexture(`${base}/rough_${res}.jpg`, { repeat });
    if (await exists(`${base}/ao_${res}.jpg`)) ao = await loadTexture(`${base}/ao_${res}.jpg`, { repeat });
  }
  const M = physical ? THREE.MeshPhysicalMaterial : THREE.MeshStandardMaterial;
  const m = new M({
    map: diff, normalMap: nor, normalScale: new THREE.Vector2(normalScale, normalScale),
    roughnessMap: arm || rough, aoMap: arm || ao, aoMapIntensity: aoIntensity,
    metalness: 0, roughness, color: new THREE.Color(color), envMapIntensity, ...extra,
  });
  return m;
}

export function loadGLTF(id) {
  const url = `/assets/models/${id}/${id}.gltf`;
  if (!gltfCache.has(url)) gltfCache.set(url, new Promise((ok, rej) => gltfLoader.load(url, ok, undefined, rej)));
  return gltfCache.get(url);
}

// Clone of a model's scene, with shadows enabled; optionally normalized to a target size.
export async function model(id, { castShadow = true, receiveShadow = true, height = null, envMapIntensity = null } = {}) {
  const g = await loadGLTF(id);
  const root = g.scene.clone(true);
  root.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = castShadow; o.receiveShadow = receiveShadow;
      if (envMapIntensity !== null && o.material) { o.material = o.material.clone(); o.material.envMapIntensity = envMapIntensity; }
    }
  });
  if (height) {
    const box = new THREE.Box3().setFromObject(root);
    const s = height / (box.max.y - box.min.y);
    root.scale.setScalar(s);
  }
  return root;
}

// Individual named meshes inside a multi-object glTF (e.g. the five stones in namaqualand_stones_01).
export async function modelParts(id) {
  const g = await loadGLTF(id);
  const parts = [];
  g.scene.traverse((o) => { if (o.isMesh) parts.push(o); });
  return parts;
}
