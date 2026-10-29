// Solomon's Colonnade in the temple courts (John 10:23). Variants cover the
// confrontation, the stones, the accusers and Jesus slipping away.
// Backlit variants are staged in a "sun frame": F points toward the low sun,
// so figures between camera and court read as silhouettes against the light.
import * as THREE from 'three';
import { makeSky, setFog } from '../lib/sky.js';
import { buildColonnade } from '../lib/architecture.js';
import { lightBeam, dustField, stoneSet, placeStone } from '../lib/props.js';
import { jesusFigure, crowdFigure } from '../lib/figure.js';
import { path, v3, rng, easeInOut, smooth } from '../lib/util.js';

const SUN = new THREE.Vector3(0.75, 0.3, -0.6).normalize();

export async function build({ params }) {
  const variant = params.variant || 'confront';
  const backlit = !['confront', 'turnaway', 'father_in_me'].includes(variant);
  const scene = new THREE.Scene();
  const sunDir = SUN.clone();
  const sky = await makeSky(scene, {
    hdri: params.hdri || 'kloppenheim_06_puresky', sunAzimuth: Math.atan2(sunDir.x, sunDir.z), sunDir,
    exposure: params.skyExposure ?? (backlit ? 0.78 : 1.1), saturation: 0.72, tint: 0xffead2, haze: 0xeed6b4, hazeAmount: backlit ? 0.4 : 0.55, hazeTop: 0.22,
    sunGlow: backlit ? 1.6 : 3.0, sunGlowPow: 22, sunDisk: backlit ? 18 : 40, sunSize: 0.018, sunColor: 0xffdcae, envIntensity: backlit ? 0.14 : 0.5,
  });
  setFog(scene, { color: backlit ? 0xa89076 : 0xc4ab8c, density: params.fog ?? (backlit ? 0.009 : 0.016), falloff: 0.045, sunDir, sunHaze: backlit ? 0x9a7a54 : 0xffcc94, sunHazePow: 8 });

  const col = await buildColonnade(scene, {});
  const sun = new THREE.DirectionalLight(0xffd6aa, params.sunIntensity ?? 5.0);
  sun.castShadow = true;
  sun.shadow.mapSize.set(window.QUALITY.shadow, window.QUALITY.shadow);
  sun.shadow.bias = -0.0003; sun.shadow.normalBias = 0.03;
  Object.assign(sun.shadow.camera, { left: -24, right: 24, top: 24, bottom: -24, near: 1, far: 160 });
  scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight(0xffe4c4, 0x4a3424, backlit ? 0.1 : 0.4));
  const bounce = new THREE.DirectionalLight(0xffb878, backlit ? 0.12 : 0.55);
  bounce.position.copy(sunDir.clone().multiplyScalar(-30).setY(-10)); scene.add(bounce);

  // Light shafts through the gaps of the inner row.
  const d = sunDir.clone().negate();
  const beams = [];
  for (const zc of col.columnZ) {
    if (zc < -60 || zc > 20) continue;
    const from = v3(1.5, 4.6, zc + 2).addScaledVector(d, -2.5);
    const b = lightBeam({ from, to: from.clone().addScaledVector(d, 22), width: 2.5, height: 8.6, intensity: params.beam ?? 0.07, color: 0xffd6a4, fadeStart: 0.12, fadeEnd: 0.62, softness: 0.4 });
    beams.push(b); scene.add(b);
  }
  const dust = dustField({ count: 2600, box: [[-10.5, 0.2, -36], [0.5, 8.5, 14]], size: 0.022, opacity: 0.55, color: 0xffe8c8 });
  scene.add(dust);

  // Sun frame: S(u, v, h) = O + right*u + F*v + up*h. Looking along F from O you see a gap in the inner row.
  const F = v3(sunDir.x, 0, sunDir.z).normalize();
  const RT = v3(-F.z, 0, F.x);
  const O = v3(-3, 0, 0);
  const S = (u, v, h = 0) => O.clone().addScaledVector(RT, u).addScaledVector(F, v).setY(h);

  const R = rng(params.seed ?? 3);
  const jesus = jesusFigure();
  scene.add(jesus);
  const crowd = [];
  const stones = await stoneSet();
  const face = (f, target) => f.lookAt(target.x, 0, target.z);
  const addPharisee = (p, faceTo, extra = {}, seed = R.int(1, 999)) => {
    const f = crowdFigure('pharisee', seed, extra);
    f.position.set(p.x, 0, p.z); face(f, faceTo);
    scene.add(f); crowd.push(f);
    return f;
  };
  const holdStone = (f, side = 'r', size = 0.13) => {
    const s = placeStone(stones[R.int(0, stones.length - 1)], { size, seed: R.int(1, 99) });
    s.position.set(0, -0.13, 0.03);
    f.userData.arms[side].wrist.add(s);
    return s;
  };
  const raise = (f, side, k, other = {}) => f.userData.pose({ ...other, [side]: { pitch: 0.4 + 2.3 * k, roll: 0.25, elbow: 0.9 - 0.5 * k } });

  const cam = new THREE.PerspectiveCamera(params.fov ?? 34, 720 / 1280, 0.1, 4000);
  let camPath, lookPath, focus = null, godrays = false;
  let anim = () => {};

  if (variant === 'confront') {
    jesus.position.set(-2.95, 0, -3.2); face(jesus, v3(-3.0, 0, 6));
    jesus.userData.pose({ r: { pitch: 0.35, roll: 0.25, elbow: 0.7 }, l: { pitch: 0.1, elbow: 0.25 }, headPitch: -0.04 });
    addPharisee(v3(-3.78, 0, 2.3), jesus.position, {}, 11);
    addPharisee(v3(-2.28, 0, 2.7), jesus.position, { arms: { r: { pitch: 1.0, elbow: 0.9 } } }, 12);
    addPharisee(v3(-4.0, 0, -2.4), jesus.position, {}, 13);
    addPharisee(v3(-1.9, 0, -2.2), jesus.position, {}, 14);
    addPharisee(v3(-4.6, 0, -0.4), jesus.position, {}, 15);
    camPath = path([[-3.1, 1.62, 6.3], [-3.0, 1.6, 5.3]]);
    lookPath = path([[-2.95, 1.45, -3.2], [-2.95, 1.47, -3.2]]);
    focus = { distance: 8.8, range: 4.0, bokeh: 1.8 };
    anim = (t) => { jesus.userData.idle(t, 0.8); crowd.forEach((f) => f.userData.idle(t)); };
  } else if (variant === 'turnaway') {
    jesus.visible = false;
    const walkers = [];
    for (let i = 0; i < 6; i++) {
      const p = v3(-3.6 + (i % 3) * 0.75 + R.range(-0.15, 0.15), 0, 0.6 - Math.floor(i / 3) * 1.5 - R.range(0, 0.5));
      const f = addPharisee(p, v3(p.x, 0, -50), {}, 30 + i);
      walkers.push({ f, z0: p.z, speed: R.range(0.5, 0.7), delay: R.range(0, 0.7) });
    }
    camPath = path([[-2.9, 1.45, 6.4], [-2.95, 1.45, 5.8]]);
    lookPath = path([[-3.1, 1.5, -14], [-3.1, 1.5, -14]]);
    focus = { distance: 7.5, range: 6, bokeh: 1.2 };
    anim = (t) => walkers.forEach((w) => { const k = Math.max(0, t - w.delay); w.f.position.z = w.z0 - k * w.speed; w.f.position.y = 0.012 * Math.abs(Math.sin(k * 4.2)); w.f.userData.idle(t); });
  } else if (variant === 'one_light') {
    const jp = S(0, 1.1); jesus.position.copy(jp); face(jesus, S(0, 9));
    jesus.userData.pose({ l: { pitch: 0.2, roll: 0.45, elbow: 0.3 }, r: { pitch: 0.2, roll: 0.45, elbow: 0.3 }, headPitch: -0.28 });
    const hb = lightBeam({ from: jp.clone().setY(0).addScaledVector(d, -12), to: jp.clone().setY(0).addScaledVector(d, 1.0), width: 1.7, height: 2.8, intensity: 0.0, color: 0xffe6bc, fadeStart: 0.05, fadeEnd: 0.92, softness: 0.48, noise: 0.3 });
    scene.add(hb); beams.push(hb);
    camPath = (p) => S(0.25, -2.7 + 0.45 * p, 1.05 + 0.1 * p);
    lookPath = () => S(0, 1.1, 1.85);
    focus = { distance: 3.8, range: 3.0, bokeh: 1.4 };
    godrays = true;
    anim = (t, p) => { hb.userData.uniforms.intensity.value = 0.04 + 0.2 * smooth(0.0, 0.75, p); jesus.userData.idle(t, 0.35); };
  } else if (variant === 'stones') {
    jesus.visible = false;
    for (let i = 0; i < 10; i++) {
      const s = placeStone(stones[i % stones.length], { size: R.range(0.1, 0.17), seed: i + 5 });
      s.position.copy(S(R.range(-0.9, 0.9), R.range(-1.4, 0.4), 0.05)); scene.add(s);
    }
    const men = [];
    for (let i = 0; i < 7; i++) {
      const f = addPharisee(S(-1.5 + i * 0.5 + R.range(-0.1, 0.1), 1.3 + (i % 2) * 0.9 + R.range(-0.2, 0.2)), S(0, -10), {}, 50 + i);
      holdStone(f, 'r', R.range(0.1, 0.15));
      men.push({ f, delay: R.range(0.0, 0.5) });
    }
    camPath = (p) => S(0.1, -2.3 + 0.2 * p, 0.32 + 0.4 * p);
    lookPath = (p) => S(0, 2.0, 1.0 + 0.45 * p);
    focus = { distance: 4.2, range: 3.2, bokeh: 2.2 };
    godrays = true;
    anim = (t, p) => men.forEach(({ f, delay }) => { raise(f, 'r', easeInOut((p - delay * 0.6) * 1.6)); f.userData.idle(t); });
  } else if (variant === 'faces_crowd') {
    jesus.position.copy(S(-0.18, -2.0)); face(jesus, S(-0.1, 5));
    jesus.userData.pose({ r: { pitch: 0.5, roll: 0.3, elbow: 0.6 }, l: { pitch: 0.1, elbow: 0.2 } });
    for (let i = 0; i < 7; i++) {
      const f = addPharisee(S(-1.5 + i * 0.5 + R.range(-0.1, 0.1), 0.6 + (i % 3) * 0.7 + R.range(-0.2, 0.2)), jesus.position, {}, 70 + i);
      if (i % 2 === 0) { holdStone(f); raise(f, 'r', R.range(0.55, 0.9)); }
    }
    camPath = (p) => S(-0.5 + 0.06 * p, -3.3 + 0.35 * p, 1.74);
    lookPath = () => S(0.1, 1.2, 1.55);
    focus = { distance: 3.8, range: 2.6, bokeh: 2.0 };
    godrays = true;
    anim = (t) => { jesus.userData.idle(t, 0.6); crowd.forEach((f) => f.userData.idle(t)); };
  } else if (variant === 'accusers' || variant === 'accusers2') {
    const two = variant === 'accusers2';
    jesus.visible = false;
    const pts = two ? [[-0.2, 0.4], [0.5, 0.9], [-0.9, 1.1], [1.0, 1.6], [0.1, 1.8]] : [[0.1, 0.2], [-0.6, 0.8], [0.75, 0.9], [-1.1, 1.6], [0.3, 1.7], [1.2, 2.0]];
    pts.forEach(([u, v], i) => {
      const f = addPharisee(S(u, v), S(0, -10), {}, (two ? 120 : 90) + i);
      if (i === 0) f.userData.pose({ r: { pitch: 1.45, roll: 0.1, elbow: 0.15 }, l: { pitch: 0.2, elbow: 0.9 } });
      else if (i % 2) { holdStone(f); raise(f, 'r', 0.75); }
    });
    camPath = two ? (p) => S(-0.7 + 0.25 * p, -1.7, 1.05) : (p) => S(0.4 - 0.3 * p, -2.6 + 0.2 * p, 1.5);
    lookPath = two ? () => S(0.1, 1.0, 1.65) : () => S(0.0, 0.9, 1.55);
    focus = { distance: two ? 2.4 : 3.0, range: 2.4, bokeh: 2.2 };
    godrays = true;
    anim = (t) => crowd.forEach((f) => f.userData.idle(t, 1.2));
  } else if (variant === 'low_angle') {
    jesus.position.copy(S(0, 0.6)); face(jesus, S(0, -8));
    jesus.userData.pose({ r: { pitch: 0.65, roll: 0.25, elbow: 0.5 }, l: { pitch: 0.15, elbow: 0.3 }, headPitch: 0.05 });
    const a = addPharisee(S(-0.95, -1.0), jesus.position, {}, 141); holdStone(a); raise(a, 'r', 0.7);
    const b = addPharisee(S(1.0, -0.8), jesus.position, {}, 142); holdStone(b); raise(b, 'r', 0.6);
    camPath = (p) => S(0.3 - 0.1 * p, -2.7 + 0.2 * p, 0.5);
    lookPath = () => S(0, 0.6, 1.5);
    focus = { distance: 2.6, range: 1.8, bokeh: 1.8 };
    godrays = true;
    params.exposure = params.exposure ?? 0.8;
    anim = (t) => { jesus.userData.idle(t, 0.5); crowd.forEach((f) => f.userData.idle(t)); };
  } else if (variant === 'father_in_me') {
    const jp = S(0, 1.0); jesus.position.copy(jp); face(jesus, S(0, 9));
    jesus.userData.pose({ l: { pitch: 0.55, roll: 0.55, elbow: 0.6 }, r: { pitch: 0.55, roll: 0.55, elbow: 0.6 }, headPitch: -0.22 });
    const hb = lightBeam({ from: jp.clone().setY(0).addScaledVector(d, -12), to: jp.clone().setY(0).addScaledVector(d, 1.5), width: 1.8, height: 3.0, intensity: 0.12, color: 0xffe6bc, fadeStart: 0.05, fadeEnd: 0.92, softness: 0.48, noise: 0.3 });
    scene.add(hb); beams.push(hb);
    camPath = (p) => S(-3.6 + 0.3 * p, -0.2 + 1.0 * p, 1.4);
    lookPath = () => S(0, 1.0, 1.45);
    focus = { distance: 3.8, range: 2.6, bokeh: 1.8 };
    anim = (t, p) => { hb.userData.uniforms.intensity.value = 0.1 + 0.12 * smooth(0.2, 0.9, p); jesus.userData.idle(t, 0.4); };
  } else if (variant === 'escape') {
    face(jesus, S(0, 12));
    const surge = [];
    for (let i = 0; i < 8; i++) {
      const p0 = S(-1.4 + (i % 4) * 0.9 + R.range(-0.15, 0.15), -2.6 - Math.floor(i / 4) * 0.9 + R.range(-0.2, 0.2));
      const f = addPharisee(p0, S(0, 10), {}, 160 + i);
      f.userData.pose({ r: { pitch: 1.35, roll: 0.1, elbow: 0.25 }, l: { pitch: i % 2 ? 1.15 : 0.3, elbow: 0.4 } });
      surge.push({ f, p0, sp: R.range(0.35, 0.5) });
    }
    camPath = (p) => S(0.15, -5.4 + 0.3 * p, 1.6);
    lookPath = () => S(0, 3.0, 1.55);
    focus = { distance: 6.5, range: 6, bokeh: 1.0 };
    godrays = true;
    anim = (t) => {
      const w = Math.max(0, t - 0.3);
      const jp = S(0.05, 0.4 + w * 0.85, 0.012 * Math.abs(Math.sin(w * 4)));
      jesus.position.copy(jp);
      surge.forEach((s) => { const k = Math.max(0, t - 0.2) * s.sp; s.f.position.copy(s.p0).addScaledVector(F, k).setY(0.014 * Math.abs(Math.sin(k * 9))); s.f.userData.idle(t, 1.5); });
    };
  }

  // Sun disc for god rays (kept far along the sun direction from the camera).
  let sunMesh = null;
  if (godrays) {
    sunMesh = new THREE.Mesh(new THREE.SphereGeometry(28, 24, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(14, 11.5, 8), fog: false, transparent: true, depthWrite: false }));
    scene.add(sunMesh);
  }

  const tmp = new THREE.Vector3();
  return {
    scene, camera: cam,
    post: {
      look: 'golden', dof: params.dof === false ? null : focus, bloom: { intensity: backlit ? 0.6 : 0.85, threshold: 0.85 }, exposure: params.exposure ?? (backlit ? 0.9 : 1.0), vignette: { darkness: 0.6 },
      godrays: sunMesh ? { source: sunMesh, density: 0.96, decay: 0.93, weight: 0.24, exposure: 0.32, samples: 60 } : null,
      grade: backlit ? { contrast: 1.16, saturation: 0.82 } : {},
    },
    update(t, p) {
      const c = camPath(p), l = lookPath(p);
      cam.position.copy(c); cam.lookAt(l);
      tmp.copy(l).setY(0);
      sun.target.position.copy(tmp);
      sun.position.copy(tmp).addScaledVector(sunDir, 80);
      if (sunMesh) sunMesh.position.copy(c).addScaledVector(sunDir, 1500);
      beams.forEach((b) => { b.userData.uniforms.time.value = t; });
      dust.userData.uniforms.time.value = t;
      sky.uniforms.time.value = t;
      anim(t, p);
    },
  };
}
