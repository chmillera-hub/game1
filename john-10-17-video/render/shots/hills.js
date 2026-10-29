// Judean hills: shepherd and flock, pasture, sheepfold, crowds at sunrise, Gethsemane,
// Jerusalem establishing shots, and night scenes with many lamps.
import * as THREE from 'three';
import { makeSky, setFog } from '../lib/sky.js';
import { makeTerrain, hillsHeight, grassField, scatterModel, placeOn } from '../lib/terrain.js';
import { makeSheep, makeFlock } from '../lib/sheep.js';
import { jesusFigure, crowdFigure, makeFigure, shellGeometry, clothMat } from '../lib/figure.js';
import { staff, flame, dustField, lightBeam } from '../lib/props.js';
import { buildJerusalem } from '../lib/architecture.js';
import { loadGLTF } from '../lib/assets.js';
import { rng, v3, path, smooth, easeInOut, easeOut, noise2 } from '../lib/util.js';

const VARIANTS = {
  flock_follow: { hdri: 'kloppenheim_06_puresky', sun: [-1, 0.11, -0.55], skyExp: 0.8, fog: [0xb39878, 0.0032, 0.02], look: 'golden', tint: [0xcfae7c, 0x8c7656] },
  pasture: { hdri: 'kloofendal_28d_misty_puresky', sun: [1, 0.2, -0.35], skyExp: 0.85, fog: [0xc8b494, 0.006, 0.05], look: 'warm', tint: [0xb4ac74, 0x7c7a4c], texture: 'grass_ground',  },
  lamb: { hdri: 'belfast_sunset_puresky', sun: [-0.3, 0.07, -1], skyExp: 0.8, fog: [0xb09070, 0.006, 0.03], look: 'golden', ridge: true, tint: [0xc9a676, 0x87704f] },
  fold_night: { hdri: 'qwantani_moonrise_puresky', sun: [0.35, 0.22, -1], skyExp: 0.42, fog: [0x1c2433, 0.006, 0.03], look: 'night', night: true, stars: 1.0, tint: [0x7a7466, 0x4a463c] },
  glory_crowd: { hdri: 'table_mountain_2_puresky', sun: [0.0, 0.07, -1], skyExp: 0.8, fog: [0xc0a07c, 0.005, 0.02], look: 'golden', tint: [0xcaa878, 0x8a7253] },
  path_light: { hdri: 'scythian_tombs_puresky', sun: [0.05, 0.12, -1], skyExp: 0.95, fog: [0xd2bc9c, 0.006, 0.02], look: 'heaven', tint: [0xd2b486, 0x9a8260] },
  dawn_walk: { hdri: 'qwantani_dusk_2_puresky', sun: [0.25, 0.04, -1], skyExp: 0.9, fog: [0xa89888, 0.006, 0.03], look: 'warm', tint: [0xb8a07c, 0x7c6a54] },
  final_light: { hdri: 'table_mountain_2_puresky', sun: [0.02, 0.1, -1], skyExp: 0.85, fog: [0xc8a880, 0.004, 0.02], look: 'heaven', ridge: true, tint: [0xcfae7c, 0x8c7656] },
  end_flock: { hdri: 'kloppenheim_06_puresky', sun: [-0.8, 0.08, -1], skyExp: 0.82, fog: [0xb89c7a, 0.004, 0.02], look: 'golden', tint: [0xcfae7c, 0x8c7656] },
  title: { hdri: 'kloppenheim_06_puresky', sun: [0.12, 0.055, -1], skyExp: 0.62, fog: [0xa08468, 0.0009, 0.01], look: 'golden', tint: [0xb09468, 0x6c5a40], city: true, skyTint: 0xffd49a },
  chapter: { hdri: 'qwantani_night_puresky', sun: [0.4, 0.3, -1], skyExp: 0.35, fog: [0x141a26, 0.003, 0.012], look: 'night', night: true, stars: 1.2, tint: [0x6a665c, 0x3e3a34], city: true },
  gethsemane: { hdri: 'qwantani_moonrise_puresky', sun: [-0.6, 0.35, -0.8], skyExp: 0.4, fog: [0x1a2232, 0.012, 0.06], look: 'night', night: true, stars: 0.8, tint: [0x6a6658, 0x3c3a32] },
  lamps_many: { hdri: 'qwantani_night_puresky', sun: [0.4, 0.3, -1], skyExp: 0.42, fog: [0x121824, 0.004, 0.015], look: 'night', night: true, stars: 1.2, tint: [0x4a483e, 0x2e2c26] },
  baskets: { hdri: 'kloppenheim_06_puresky', sun: [-1, 0.13, -0.25], skyExp: 0.85, fog: [0xb89c7a, 0.004, 0.02], look: 'golden', tint: [0xb8a470, 0x7c6e48], texture: 'grass_ground' },
  lights_converge: { hdri: 'qwantani_night_puresky', sun: [0.4, 0.3, -1], skyExp: 0.36, fog: [0x121824, 0.004, 0.015], look: 'night', night: true, stars: 1.4, tint: [0x4a483e, 0x2e2c26] },
};

// Cheap instanced robed silhouettes for very large crowds.
function proxyCrowd(scene, positions, { color = 0x2a2420, seed = 3 } = {}) {
  const robe = shellGeometry([
    { y: 0, r: 0.26, sx: 1, sz: 0.85, fold: 0.015 }, { y: 0.9, r: 0.2, sx: 1.04, sz: 0.75, fold: 0.008 },
    { y: 1.38, r: 0.2, sx: 1.12, sz: 0.6, fold: 0.002 }, { y: 1.46, r: 0.1, sx: 1, sz: 1 },
  ], { seg: 18, seed, freq: 7 });
  const head = new THREE.SphereGeometry(0.115, 10, 8).translate(0, 1.6, 0);
  const merged = mergeTwo(robe, head);
  const im = new THREE.InstancedMesh(merged, new THREE.MeshStandardMaterial({ color, roughness: 1 }), positions.length);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), r = rng(seed);
  positions.forEach((p, i) => { q.setFromAxisAngle(v3(0, 1, 0), p.yaw ?? r() * 6.28); m4.compose(v3(p.x, p.y, p.z), q, v3(1, p.s ?? r.range(0.9, 1.08), 1)); im.setMatrixAt(i, m4); });
  im.castShadow = false; im.receiveShadow = true;
  scene.add(im);
  return im;
}
function mergeTwo(a, b) {
  const g = new THREE.BufferGeometry();
  const pa = a.attributes.position.array, pb = b.attributes.position.array;
  const na = a.attributes.normal.array, nb = b.attributes.normal.array;
  const pos = new Float32Array(pa.length + pb.length); pos.set(pa); pos.set(pb, pa.length);
  const nor = new Float32Array(na.length + nb.length); nor.set(na); nor.set(nb, na.length);
  const ia = Array.from(a.index.array), off = pa.length / 3, ib = Array.from(b.index.array).map((x) => x + off);
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  g.setIndex([...ia, ...ib]);
  return g;
}

// Additive glow points (lamp flames seen from afar), flickering.
function glowPoints(scene, pts, { size = 0.09, color = 0xffa040, seed = 1 } = {}) {
  const pos = new Float32Array(pts.length * 3), ph = new Float32Array(pts.length), sz = new Float32Array(pts.length);
  const r = rng(seed);
  pts.forEach((p, i) => { pos.set([p.x, p.y, p.z], i * 3); ph[i] = r() * 100; sz[i] = p.s ?? 1; });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('phase', new THREE.BufferAttribute(ph, 1));
  g.setAttribute('sz', new THREE.BufferAttribute(sz, 1));
  const m = new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 }, size: { value: size }, color: { value: new THREE.Color(color) }, reveal: { value: 1 }, total: { value: pts.length } },
    vertexShader: `uniform float time, size, reveal, total; attribute float phase, sz; varying float vA;
      void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0);
        float idx = phase / 100.0; float on = smoothstep(idx - 0.02, idx + 0.02, reveal);
        vA = on * (0.8 + 0.2 * sin(time * 9.0 + phase * 7.0));
        gl_PointSize = clamp(size * sz * 1280.0 / -mv.z, 1.5, 48.0) * on;
        gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform vec3 color; varying float vA;
      void main(){ vec2 c = gl_PointCoord - 0.5; float d = length(c);
        float core = smoothstep(0.18, 0.0, d); float halo = smoothstep(0.5, 0.0, d) * 0.35;
        gl_FragColor = vec4((color * halo + vec3(1.0, 0.85, 0.6) * core) * vA * 3.0, 1.0); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false,
  });
  const p = new THREE.Points(g, m); p.frustumCulled = false; p.userData.uniforms = m.uniforms;
  scene.add(p);
  return p;
}

export async function build({ params }) {
  const variant = params.variant || 'flock_follow';
  const V = VARIANTS[variant];
  const scene = new THREE.Scene();
  const R = rng(params.seed ?? 11);
  const sunDir = v3(...V.sun).normalize();
  const sky = await makeSky(scene, {
    hdri: V.hdri, sunAzimuth: Math.atan2(sunDir.x, sunDir.z), sunDir, exposure: V.skyExp, saturation: V.night ? 0.8 : 0.78,
    tint: V.skyTint || (V.night ? 0xc8d4ff : 0xffeedc), haze: V.fog[0], hazeAmount: V.night ? 0.2 : 0.32, hazeTop: 0.1, stars: V.stars || 0,
    sunGlow: V.night ? 0.4 : 1.3, sunGlowPow: V.night ? 60 : 20, sunDisk: V.night ? 6 : 14, sunSize: V.night ? 0.012 : 0.02,
    sunColor: V.night ? 0xc8d8ff : 0xffd8a8, envIntensity: V.night ? 0.25 : 0.55, clampMax: V.night ? 30 : 4.0,
  });
  setFog(scene, { color: V.fog[0], density: V.fog[1], falloff: V.fog[2], sunDir, sunHaze: V.night ? 0x101828 : 0x7a6044, sunHazePow: 9 });

  // Terrain shaped per variant.
  let ridge = null;
  if (V.ridge) ridge = (x, z) => 4.5 * Math.exp(-(((z + 14) / 7) ** 2)) - 1.5 * Math.exp(-((z / 10) ** 2));
  if (V.city) ridge = (x, z) => 55 * Math.exp(-((x - 30) ** 2 + (z + 620) ** 2) / (2 * 160 ** 2)) - 18 * Math.exp(-((z + 260) ** 2) / (2 * 90 ** 2));
  if (variant === 'path_light') ridge = (x, z) => 12 * smooth(-5, -70, z) + 2 * Math.sin(x * 0.05);
  if (variant === 'pond' || V.pond) ridge = (x, z) => -1.4 * Math.exp(-(((x + 2) ** 2) / 60 + ((z + 9) ** 2) / 30));
  const height = hillsHeight({ amp: V.city ? 12 : 11, scale: 200, flat: 18, flatH: 0, ridge, seed: (params.seed ?? 1) * 0.37 });
  await makeTerrain(scene, { height, texture: V.texture || 'dry_ground_rocks', tintA: V.tint[0], tintB: V.tint[1], texRepeat: 0.3 });

  const sun = new THREE.DirectionalLight(V.night ? 0x9fb4e0 : 0xffd6a8, V.night ? 0.8 : 4.2);
  sun.castShadow = true; sun.shadow.mapSize.set(window.QUALITY.shadow, window.QUALITY.shadow);
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.04;
  Object.assign(sun.shadow.camera, { left: -22, right: 22, top: 22, bottom: -22, near: 1, far: 220 });
  scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight(V.night ? 0x31405c : 0xffe2c0, V.night ? 0x0c0c10 : 0x3a2c20, V.night ? 0.25 : 0.32));

  const grassColor = V.night ? [0x1c1c18, 0x5a5a50] : (V.texture === 'grass_ground' ? [0x4a5228, 0xb8b878] : [0x5a4a2a, 0xdcc08a]);
  let grass = null;
  const center = params.center || [0, 0];
  let grass2 = null;
  if (!V.city && variant !== 'lights_converge') {
    grass = grassField(scene, { height, center: params.grassC || center, radius: params.grassR ?? 22, count: params.grassN ?? 30000, colorBase: grassColor[0], colorTip: grassColor[1], hMin: 0.06, hMax: 0.26, seed: 3,
      density: (x, z) => 0.35 + 0.65 * Math.max(0, noise2(x / 3.5, z / 3.5) + 0.3) });
  }

  // Scattered rocks & shrubs around the action.
  const rocks = [];
  for (let i = 0; i < 26; i++) {
    const a = R() * 6.28, d = R.range(4, 60);
    const x = center[0] + Math.cos(a) * d, z = center[1] + Math.sin(a) * d;
    rocks.push(placeOn(height, x, z, { scale: R.range(0.6, 2.4), yaw: R() * 6.28, sink: 0.15 }));
  }
  await scatterModel(scene, R() < 0.5 ? 'rock_07' : 'rock_09', rocks.slice(0, 13));
  await scatterModel(scene, 'rock_09', rocks.slice(13));
  if (!V.night) {
    const sh = [];
    for (let i = 0; i < 12; i++) { const a = R() * 6.28, d = R.range(6, 40); sh.push(placeOn(height, center[0] + Math.cos(a) * d, center[1] + Math.sin(a) * d, { scale: R.range(1.2, 2.2), yaw: R() * 6.28 })); }
    await scatterModel(scene, 'shrub_04', sh, { tint: 0x9a8a5a });
  }

  const cam = new THREE.PerspectiveCamera(params.fov ?? (V.city ? 26 : 34), 720 / 1280, 0.1, 5000);
  let camPath, lookPath, focus = null, godrays = false;
  const updaters = [];
  let exposure = params.exposure ?? 1.0;
  const G = (x, z) => v3(x, height(x, z), z);
  const C = (x, z, h) => v3(x, height(x, z) + h, z);

  const jesusWithStaff = (pose) => {
    const j = jesusFigure({ arms: pose || { r: { pitch: 0.42, roll: 0.42, elbow: 0.75, wristPitch: -0.3 }, l: { pitch: 0.1, elbow: 0.25 } } });
    const st = staff({}); st.position.set(-0.36, 0.0, 0.3); st.rotation.set(0.04, 0, 0.06);
    j.add(st);
    return j;
  };

  if (variant === 'flock_follow') {
    const ridgePath = (s) => G(6 - 0.42 * s, -27 + s);
    const j = jesusWithStaff(); scene.add(j);
    const flockObj = makeFlock(scene, { count: 18, path: ridgePath, height, start: 6.5, spacing: 0.75, spread: 2.0, speed: 0.62, seed: 21, lambs: 3 });
    updaters.push((t) => {
      const s = 8.2 + t * 0.62, p = ridgePath(s), q = ridgePath(s + 0.5);
      j.position.copy(p); j.position.y += 0.012 * Math.abs(Math.sin(t * 4.4));
      j.lookAt(q.x, p.y, q.z); j.userData.idle(t, 0.5);
      flockObj.update(t);
    });
    camPath = (p) => C(-2.2 + 0.5 * p, -8.5 - 0.6 * p, 0.75);
    lookPath = (p) => C(2.2 - 0.3 * p, -18.5 + 1.8 * p, 1.05);
    focus = { distance: 10, range: 8, bokeh: 1.2 };
    godrays = false;
  } else if (variant === 'pasture') {
    camPath = (p) => C(-2.6 + 1.6 * p, 7.5, 0.95);
    lookPath = (p) => C(-1.6 + 1.6 * p, -6, 0.35);
    const c0 = camPath(0.5), l0 = lookPath(0.5), dir = l0.clone().sub(c0).setY(0).normalize(), side = v3(-dir.z, 0, dir.x);
    for (let i = 0; i < 15; i++) {
      const d = 3.5 + i * 1.05 + R.range(-0.3, 0.3), off = R.range(-0.16, 0.16) * d;
      const pp = c0.clone().addScaledVector(dir, d).addScaledVector(side, off);
      const sh = makeSheep({ seed: 300 + i, lamb: i % 5 === 4 });
      sh.position.copy(G(pp.x, pp.z)); sh.rotation.y = R() * 6.28; scene.add(sh);
      const graze = R() < 0.7 ? 0.95 : 0.0;
      updaters.push((t) => sh.userData.idle(t, graze));
    }
    focus = { distance: 7, range: 6, bokeh: 1.4 };
    godrays = false;
  } else if (variant === 'lamb') {
    const j = jesusFigure({ arms: { l: { pitch: 0.95, roll: -0.1, elbow: 1.55, wristRoll: 0.2 }, r: { pitch: 0.95, roll: -0.12, elbow: 1.5 } }, headPitch: 0.35 });
    j.position.copy(G(0, -6)); j.lookAt(3, j.position.y, -4); scene.add(j);
    const lamb = makeSheep({ seed: 501, lamb: true }); lamb.scale.multiplyScalar(0.95);
    lamb.position.set(0.0, 1.0, 0.27); lamb.rotation.set(0, Math.PI / 2, 0); lamb.userData.neck.rotation.x = -0.4;
    j.add(lamb);
    for (let i = 0; i < 6; i++) { const sh = makeSheep({ seed: 520 + i }); sh.position.copy(G(R.range(-5, 4), R.range(-9, -3))); sh.rotation.y = R() * 6.28; scene.add(sh); const g = R() < 0.6 ? 0.9 : 0; updaters.push((t) => sh.userData.idle(t, g)); }
    updaters.push((t) => { j.userData.idle(t, 0.35); lamb.userData.head.rotation.y = 0.3 * Math.sin(t * 0.8); });
    camPath = (p) => C(-2.5 + 0.45 * p, -1.7 - 0.5 * p, 1.2);
    lookPath = () => C(0.1, -6, 1.3);
    focus = { distance: 5.2, range: 2.5, bokeh: 2.2 };
    godrays = true;
  } else if (variant === 'fold_night') {
    // circular sheepfold of stacked stones, opening toward the camera; shepherd sits in the gateway
    const ring = [];
    for (let k = 0; k < 2; k++) for (let i = 0; i < 46; i++) {
      const a = (i / 46) * Math.PI * 2 + k * 0.07;
      if (Math.abs(((a + Math.PI * 1.5) % (Math.PI * 2)) - Math.PI) > Math.PI - 0.35) continue;
      const x = Math.cos(a) * 4.6, z = -8 + Math.sin(a) * 4.6;
      const m = placeOn(height, x, z, { scale: R.range(1.7, 2.2), yaw: R() * 6.28, sink: -0.45 * k });
      ring.push(m);
    }
    await scatterModel(scene, 'rock_09', ring.filter((_, i) => i % 2 === 0));
    await scatterModel(scene, 'rock_07', ring.filter((_, i) => i % 2 === 1));
    for (let i = 0; i < 12; i++) {
      const a = R() * 6.28, d = R.range(0.5, 3.4);
      const sh = makeSheep({ seed: 600 + i, lying: true, lamb: i > 9 });
      sh.position.copy(G(Math.cos(a) * d, -8 + Math.sin(a) * d)); sh.rotation.y = R() * 6.28; scene.add(sh);
      updaters.push((t) => sh.userData.idle(t, 0));
    }
    const j = makeFigure({ seed: 33, pose: 'sit', robe: 0xd8cebe, mantle: 0x7a5a40, head: 'hair', hair: 0x2a1a10, arms: { r: { pitch: 0.8, elbow: 0.9 }, l: { pitch: 0.6, elbow: 1.3 } } });
    j.position.copy(G(0.2, -3.25)); j.lookAt(0, j.position.y, 4); scene.add(j);
    const st = staff({}); st.position.copy(G(0.75, -3.0)); st.rotation.set(-0.25, 0, -0.18); scene.add(st);
    const fire = flame({ size: 0.22, lightIntensity: 3.5, lightDistance: 14, seed: 4, shadow: false });
    fire.position.copy(G(-1.4, -2.2)).add(v3(0, 0.05, 0)); scene.add(fire);
    updaters.push((t) => { fire.userData.update(t); j.userData.idle(t, 0.3); });
    camPath = (p) => C(-1.6 + 0.9 * p, 4.5 - 1.4 * p, 3.2);
    lookPath = () => C(0, -7, 0.4);
    focus = { distance: 8.5, range: 6, bokeh: 1.0 };
  } else if (variant === 'glory_crowd') {
    for (let i = 0; i < 26; i++) {
      const x = R.range(-6, 6), z = R.range(-10, -2);
      const f = crowdFigure('people', 700 + i, { arms: R() < 0.2 ? { l: { pitch: 1.9, roll: 0.45, elbow: 0.45 }, r: { pitch: 1.9, roll: 0.45, elbow: 0.45 } } : undefined });
      f.position.copy(G(x, z)); f.lookAt(x * 0.8, f.position.y, -200); scene.add(f);
      updaters.push((t) => f.userData.idle(t));
    }
    camPath = (p) => C(0.4, 3.6 - 0.6 * p, 1.1 + 1.0 * p);
    lookPath = (p) => C(0, -14, 2.4 + 0.8 * p);
    focus = { distance: 9, range: 9, bokeh: 0.8 };
    godrays = true;
  } else if (variant === 'path_light') {
    const pathF = (s) => G(1.6 * Math.sin(s * 0.09), -2 - s);
    const pts = []; for (let s = -6; s < 90; s += 0.5) pts.push(pathF(s));
    const road = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 400, 0.7, 6, false), new THREE.MeshStandardMaterial({ color: 0xb8a07c, roughness: 1 }));
    road.scale.y = 0.08; road.position.y = 0.02; scene.add(road);
    const walkers = [];
    for (let i = 0; i < 5; i++) {
      const f = crowdFigure('people', 760 + i); scene.add(f);
      walkers.push({ f, s0: 3.2 + i * 1.25 + R.range(-0.3, 0.3), off: R.range(-0.45, 0.45) });
    }
    updaters.push((t) => walkers.forEach((w) => {
      const s = w.s0 + t * 0.7, p = pathF(s), q = pathF(s + 1);
      w.f.position.set(p.x + w.off, p.y + 0.012 * Math.abs(Math.sin(t * 4.4 + w.s0)), p.z); w.f.lookAt(q.x + w.off, p.y, q.z); w.f.userData.idle(t);
    }));
    camPath = (p) => { const c = pathF(-1.5 + 2.2 * p); return v3(c.x - 0.4, c.y + 1.3, c.z); };
    lookPath = () => C(0.5, -34, 3.0);
    focus = { distance: 9, range: 10, bokeh: 0.8 };
    godrays = true;
  } else if (variant === 'dawn_walk') {
    const pathF = (s) => G(-6 + s * 0.55, -6 - s * 0.85);
    const group = [jesusFigure()];
    for (let i = 0; i < 5; i++) group.push(crowdFigure('disciples', 800 + i));
    group.forEach((f, i) => { scene.add(f); f.userData.off = [(i % 3 - 1) * 0.75 + R.range(-0.1, 0.1), Math.floor(i / 3) * -1.1 + (i === 0 ? 0.9 : 0)]; });
    updaters.push((t) => group.forEach((f, i) => {
      const s = 2 + t * 0.62 + f.userData.off[1], p = pathF(s), q = pathF(s + 1);
      const dir = q.clone().sub(p).setY(0).normalize(); const side = v3(-dir.z, 0, dir.x);
      const pos = p.clone().addScaledVector(side, f.userData.off[0]); pos.y = height(pos.x, pos.z) + 0.012 * Math.abs(Math.sin(t * 4.3 + i));
      f.position.copy(pos); f.lookAt(pos.x + dir.x, pos.y, pos.z + dir.z); f.userData.idle(t);
    }));
    camPath = (p) => C(-8.2 + 1.4 * p, -1.5 - 1.0 * p, 1.5);
    lookPath = (p) => C(-3.5 + 2.0 * p, -10 - 1.4 * p, 1.3);
    focus = { distance: 8, range: 6, bokeh: 1.2 };
    godrays = true;
  } else if (variant === 'final_light') {
    const j = jesusFigure({ arms: { l: { pitch: 1.0, roll: 1.05, elbow: 0.25 }, r: { pitch: 1.0, roll: 1.05, elbow: 0.25 } }, headPitch: -0.12 });
    j.position.copy(G(0, -13.5)); j.lookAt(0, j.position.y, 10); scene.add(j);
    updaters.push((t) => j.userData.idle(t, 0.3));
    camPath = (p) => C(0.3, -3.0 - 2.5 * p, 0.7 + 0.3 * p);
    lookPath = () => C(0, -13.5, 1.9);
    focus = { distance: 11, range: 6, bokeh: 1.2 };
    godrays = true;
    exposure = params.exposure ?? 1.05;
  } else if (variant === 'end_flock') {
    const pathF = (s) => G(-14 + s, -18 + 2 * Math.sin(s * 0.12));
    const j = jesusWithStaff(); scene.add(j);
    const flockObj = makeFlock(scene, { count: 24, path: pathF, height, start: 4, spacing: 0.55, spread: 2.6, speed: 0.55, seed: 41, lambs: 4 });
    updaters.push((t) => {
      const s = 9 + t * 0.55, p = pathF(s), q = pathF(s + 0.5);
      j.position.copy(p); j.position.y += 0.01 * Math.abs(Math.sin(t * 4)); j.lookAt(q.x, p.y, q.z); j.userData.idle(t, 0.4);
      flockObj.update(t);
    });
    camPath = (p) => C(-3.2 + 1.0 * p, -4, 1.9);
    lookPath = (p) => C(-5.6 + 1.0 * p, -18, 1.3);
    focus = null;
    godrays = true;
  } else if (variant === 'title' || variant === 'chapter') {
    const cx = 30, cz = -620;
    const city = await buildJerusalem(scene, { x: cx, z: cz, scale: 1.0 });
    city.position.y = height(cx, cz) - 6;
    if (variant === 'chapter') {
      // warm lamplit windows across the city
      const lights = [];
      for (let i = 0; i < 260; i++) lights.push({ x: cx + R.range(-120, 120), y: city.position.y + R.range(8, 22), z: cz + R.range(-50, 45), s: R.range(0.6, 1.4) });
      glowPoints(scene, lights, { size: 0.9, color: 0xffa050, seed: 3 });
    }
    // olive trees in the foreground (Mount of Olives)
    const trees = [];
    for (let i = 0; i < 5; i++) trees.push(placeOn(height, R.range(-16, 16), R.range(-30, -8), { scale: R.range(0.9, 1.3), yaw: R() * 6.28 }));
    await scatterModel(scene, 'island_tree_02_lod', trees.slice(0, 3)).catch(() => {});
    await scatterModel(scene, 'island_tree_01_lod', trees.slice(3)).catch(() => {});
    camPath = (p) => C(-2 + 1.0 * p, 0 - 4 * p, 4.0 + 0.4 * p);
    lookPath = (p) => v3(cx - 25, city.position.y + 80 + 2 * p, cz);
    sun.shadow.camera.far = 600;
    focus = null;
    godrays = false;
  } else if (variant === 'gethsemane') {
    const trees = [
      placeOn(height, -3.8, -8.5, { scale: 1.15, yaw: 1.0 }), placeOn(height, 4.2, -11, { scale: 1.25, yaw: 2.2 }),
      placeOn(height, -1.0, -15, { scale: 1.0, yaw: 4.1 }), placeOn(height, 7.5, -5.5, { scale: 1.1, yaw: 0.4 }), placeOn(height, -9, -14, { scale: 1.2, yaw: 3.3 }),
    ];
    await scatterModel(scene, 'island_tree_03_lod', trees.slice(0, 2), { tint: 0x8a8a7a }).catch(() => {});
    await scatterModel(scene, 'island_tree_01_lod', trees.slice(2), { tint: 0x8a8a7a }).catch(() => {});
    await scatterModel(scene, 'namaqualand_boulder_05', [placeOn(height, 0.55, -6.1, { scale: 0.62, yaw: 0.8, sink: 0.2 })], { tint: 0x9a968a });
    const j = jesusFigure({ arms: { l: { pitch: 0.75, roll: 0.55, elbow: 0.55, wristPitch: -0.4 }, r: { pitch: 0.75, roll: 0.55, elbow: 0.55, wristPitch: -0.4 } }, headPitch: -0.5 });
    j.position.copy(G(0.45, -5.15)); j.lookAt(0.6, j.position.y, -12); scene.add(j);
    updaters.push((t) => j.userData.idle(t, 0.25));
    const rim = new THREE.SpotLight(0xa8c0ff, 18, 30, 0.35, 0.6, 1.5); rim.position.copy(G(-1, -16)).add(v3(0, 8, 0)); rim.target = j; scene.add(rim);
    camPath = (p) => { const a = -1.95 + 0.3 * p; return C(0.45 + Math.sin(a) * 4.4, -5.25 + Math.cos(a) * 4.4, 0.7); };
    lookPath = () => C(0.3, -5.25, 1.55);
    focus = { distance: 4.0, range: 2.2, bokeh: 2.0 };
  } else if (variant === 'baskets') {
    const g1 = await loadGLTF('wicker_basket_01'), g2 = await loadGLTF('wicker_basket_02'), gb = await loadGLTF('hamburger_buns');
    const buns = []; gb.scene.traverse((o) => { if (o.isMesh) buns.push(o); });
    const fishMat = new THREE.MeshPhysicalMaterial({ color: 0x8a8070, metalness: 0.35, roughness: 0.35, sheen: 0.4 });
    const fishGeo = (() => { const b = new THREE.SphereGeometry(1, 16, 10); b.scale(0.035, 0.026, 0.13); const t = new THREE.ConeGeometry(0.03, 0.06, 4); t.rotateX(-Math.PI / 2); t.scale(1, 0.25, 1); t.translate(0, 0, -0.15); return [b, t]; })();
    const row = [];
    for (let i = 0; i < 12; i++) {
      const x = -0.4 + (i % 2) * 0.55 + R.range(-0.08, 0.08), z = 1.2 - i * 0.62;
      const src = (i % 3 === 1 ? g2 : g1).scene.clone(true);
      src.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; if (o.name.toLowerCase().includes('lid')) o.visible = false; } });
      const box = new THREE.Box3().setFromObject(src); const sz = box.getSize(new THREE.Vector3());
      const sc = 0.55 / Math.max(sz.x, sz.z); src.scale.setScalar(sc);
      const gp = G(x, z); src.position.copy(gp); src.rotation.y = R.range(-0.4, 0.4); scene.add(src);
      const topY = gp.y + sz.y * sc * 0.82;
      for (let k = 0; k < 9; k++) {
        const b = buns[k % buns.length]; const m = new THREE.Mesh(b.geometry, b.material);
        m.scale.setScalar(1.25); m.position.set(x + R.range(-0.15, 0.15), topY + R.range(0, 0.06), z + R.range(-0.12, 0.12)); m.rotation.set(R.range(-0.4, 0.4), R() * 6.28, R.range(-0.4, 0.4));
        m.castShadow = true; m.receiveShadow = true; scene.add(m);
      }
      if (i % 2 === 0) for (let k = 0; k < 3; k++) {
        const fg = new THREE.Group(); fishGeo.forEach((gg) => { const mm = new THREE.Mesh(gg, fishMat); mm.castShadow = true; fg.add(mm); });
        fg.position.set(x + R.range(-0.12, 0.12), topY + 0.07, z + R.range(-0.1, 0.1)); fg.rotation.set(0.1, R() * 6.28, 0.2); scene.add(fg);
      }
      row.push(gp);
    }
    // the satisfied crowd resting on the hillside beyond
    const people = [];
    for (let i = 0; i < 260; i++) { const x = R.range(-40, 40), z = R.range(-30, -110); people.push({ x, y: height(x, z) - 0.6, z, s: R.range(0.55, 0.7) }); }
    proxyCrowd(scene, people, { color: 0x5a4a3a });
    camPath = (p) => C(0.85 - 0.25 * p, 2.4 - 1.5 * p, 0.55);
    lookPath = (p) => C(0.0, -3.5 - 1.5 * p, 0.25);
    focus = { distance: 1.6, range: 1.2, bokeh: 2.2 };
  } else if (variant === 'lamps_many' || variant === 'lights_converge') {
    const people = [], lamps = [];
    const N = variant === 'lamps_many' ? 900 : 600;
    for (let i = 0; i < N; i++) {
      const a = R.range(-1.2, 1.2) + Math.PI * 1.5, d = 6 + 160 * Math.pow(R(), 1.6);
      const x = Math.cos(a) * d, z = Math.sin(a) * d - 4;
      const y = height(x, z);
      people.push({ x, y, z, yaw: R() * 6.28 });
      lamps.push({ x: x + 0.25, y: y + 1.25, z: z + 0.15, s: 1 });
    }
    proxyCrowd(scene, people, { color: 0x1a1612 });
    const glow = glowPoints(scene, lamps, { size: 0.14, color: 0xff9a3c, seed: 5 });
    const near = [];
    for (let i = 0; i < 6; i++) {
      const p = people[i]; const fl = flame({ size: 0.06, lightIntensity: 2.2, lightDistance: 9, seed: i });
      fl.position.set(lamps[i].x, lamps[i].y, lamps[i].z); scene.add(fl); near.push(fl);
    }
    if (variant === 'lamps_many') {
      updaters.push((t, p) => { glow.userData.uniforms.time.value = t; glow.userData.uniforms.reveal.value = 0.15 + 1.0 * easeOut(p * 1.1); near.forEach((f) => f.userData.update(t)); });
      camPath = (p) => C(0.5, 4 + 4 * p, 4.5 + 6.0 * easeInOut(p));
      lookPath = (p) => C(0, -40, 1.0 - 2 * p);
      focus = null;
      exposure = 1.45;
    } else {
      // lights rise from the hills and gather into one radiant light
      const M = 700, pos = new Float32Array(M * 3), from = [], ph = new Float32Array(M);
      for (let i = 0; i < M; i++) { const l = lamps[i % lamps.length]; from.push(v3(l.x, l.y, l.z)); ph[i] = R(); }
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('phase', new THREE.BufferAttribute(ph, 1));
      const sparks = glowPoints(scene, from.map((f) => ({ x: f.x, y: f.y, z: f.z })), { size: 0.4, color: 0xffc070, seed: 9 });
      const target = v3(0, height(0, -40) + 26, -40);
      const star = new THREE.Mesh(new THREE.SphereGeometry(1.0, 24, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(4, 3.2, 2.2), fog: false }));
      star.position.copy(target); scene.add(star);
      const starLight = new THREE.PointLight(0xffd8a0, 0, 120, 1.2); starLight.position.copy(target); scene.add(starLight);
      const attr = sparks.geometry.attributes.position;
      updaters.push((t, p) => {
        glow.userData.uniforms.time.value = t; sparks.userData.uniforms.time.value = t;
        glow.userData.uniforms.reveal.value = 1.0;
        for (let i = 0; i < from.length; i++) {
          const k = easeInOut((p * 1.35 - ph[i] * 0.45));
          const f = from[i];
          const mid = f.clone().lerp(target, 0.5).add(v3(0, 12 * (1 - ph[i]), 0));
          const a = f.clone().lerp(mid, k), b = mid.clone().lerp(target, k);
          const q = a.lerp(b, k);
          attr.setXYZ(i, q.x, q.y, q.z);
        }
        attr.needsUpdate = true;
        const s = 0.4 + 3.2 * smooth(0.35, 1.0, p);
        star.scale.setScalar(s); starLight.intensity = 60 * smooth(0.3, 1.0, p);
        near.forEach((f) => f.userData.update(t));
      });
      camPath = (p) => C(0, 8 - 2 * p, 3.0 + 1.5 * p);
      lookPath = (p) => C(0, -40, 6 + 14 * easeInOut(p));
      focus = null;
      exposure = 1.0;
    }
  }

  if (grass && camPath && !params.noNearGrass) {
    const c0 = camPath(0.5), l0 = lookPath(0.5);
    const dir = l0.clone().sub(c0).setY(0).normalize();
    const nc = c0.clone().addScaledVector(dir, 3.2);
    grass2 = grassField(scene, { height, center: [nc.x, nc.z], radius: 4.2, count: 16000, colorBase: grassColor[0], colorTip: grassColor[1], hMin: 0.05, hMax: 0.2, seed: 5 });
  }

  let sunMesh = null;
  if (godrays && !V.night) {
    sunMesh = new THREE.Mesh(new THREE.SphereGeometry(30, 24, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(14, 11.5, 8), fog: false, transparent: true, depthWrite: false }));
    scene.add(sunMesh);
  }

  const tmp = new THREE.Vector3();
  return {
    scene, camera: cam,
    post: {
      look: V.look, dof: focus, exposure, bloom: { intensity: V.night ? 1.1 : 0.55, threshold: V.night ? 0.6 : 0.9 },
      godrays: sunMesh ? { source: sunMesh, density: 0.95, decay: 0.92, weight: 0.2, exposure: 0.26, samples: 60 } : null,
      vignette: { darkness: V.night ? 0.7 : 0.55 },
    },
    update(t, p) {
      const c = camPath(p), l = lookPath(p);
      cam.position.copy(c); cam.lookAt(l);
      tmp.copy(c).lerp(l, 0.3).setY(height(tmp.x, tmp.z));
      tmp.set((c.x + l.x) / 2, 0, (c.z + l.z) / 2); tmp.y = height(tmp.x, tmp.z);
      if (variant === 'title' || variant === 'chapter') tmp.set(c.x, height(c.x, c.z - 10), c.z - 14);
      sun.target.position.copy(tmp);
      sun.position.copy(tmp).addScaledVector(sunDir, 120);
      if (sunMesh) sunMesh.position.copy(c).addScaledVector(sunDir, 1800);
      if (grass) grass.userData.uniforms.uTime.value = t;
      if (grass2) grass2.userData.uniforms.uTime.value = t;
      sky.uniforms.time.value = t;
      updaters.forEach((u) => u(t, p));
    },
  };
}
