// Skies of heaven: clouds parting with sun rays (the Father "greater than all") and a light
// descending from heaven to the hills at night (the Son "sent into the world").
import * as THREE from 'three';
import { makeSky, setFog } from '../lib/sky.js';
import { makeTerrain, hillsHeight } from '../lib/terrain.js';
import { lightBeam } from '../lib/props.js';
import { v3, smooth, easeInOut, rng } from '../lib/util.js';

export async function build({ params }) {
  const variant = params.variant || 'clouds_up';
  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(params.fov ?? 40, 720 / 1280, 0.1, 6000);
  const updaters = [];
  let camPath, lookPath, exposure = 1.0, look = 'heaven', godrays = null;
  const height = hillsHeight({ amp: 14, scale: 260, flat: 10 });

  if (variant === 'clouds_up') {
    const sunDir = v3(0.15, 0.55, -1).normalize();
    const sky = await makeSky(scene, { hdri: 'table_mountain_2_puresky', sunAzimuth: Math.atan2(sunDir.x, sunDir.z), exposure: 0.5, saturation: 0.8, tint: 0xffe8d0,
      haze: 0xc8b090, hazeAmount: 0.15, hazeTop: 0.05, sunGlow: 0.9, sunGlowPow: 18, sunDisk: 16, sunSize: 0.025, sunColor: 0xffe0b0, envIntensity: 0.6, clampMax: 5 });
    setFog(scene, { color: 0xb8a080, density: 0.0025, falloff: 0.01 });
    await makeTerrain(scene, { height, texture: 'dry_ground_rocks', tintA: 0x8a7458, tintB: 0x5a4a38 });
    const sd = sky.sunDir.clone();
    const beams = [];
    const r = rng(4);
    for (let i = 0; i < 7; i++) {
      const from = sd.clone().multiplyScalar(900).add(v3(r.range(-120, 120), r.range(-40, 40), r.range(-80, 80)));
      const to = v3(r.range(-260, 260), 0, r.range(-900, -200));
      const b = lightBeam({ from, to, width: r.range(30, 70), height: r.range(30, 70), intensity: 0.05, color: 0xffe2b8, fadeStart: 0.2, fadeEnd: 0.9, softness: 0.45, noise: 0.4 });
      scene.add(b); beams.push(b);
    }
    const sun = new THREE.Mesh(new THREE.SphereGeometry(30, 24, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(14, 11.5, 8), fog: false, transparent: true, depthWrite: false }));
    scene.add(sun);
    godrays = { source: sun, density: 0.95, decay: 0.93, weight: 0.24, exposure: 0.3, samples: 60 };
    updaters.push((t, p) => { beams.forEach((b) => { b.userData.uniforms.time.value = t; b.userData.uniforms.intensity.value = 0.035 + 0.05 * smooth(0.0, 0.8, p); }); sun.position.copy(cam.position).addScaledVector(sd, 1800); sky.uniforms.time.value = t; });
    camPath = (p) => v3(0, height(0, 0) + 2.0, 0);
    lookPath = (p) => { const a = THREE.MathUtils.lerp(0.08, 0.62, easeInOut(p)); return v3(Math.sin(0.15) * 100, height(0, 0) + 2.0 + Math.tan(a) * 100, -100); };
  } else if (variant === 'descend') {
    look = 'night';
    const sky = await makeSky(scene, { hdri: 'qwantani_night_puresky', sunAzimuth: 0.4, exposure: 0.4, saturation: 0.8, tint: 0xc8d4ff, haze: 0x182030, hazeAmount: 0.25, stars: 1.3,
      sunGlow: 0.0, sunDisk: 0, envIntensity: 0.25, clampMax: 30 });
    setFog(scene, { color: 0x121a28, density: 0.003, falloff: 0.012 });
    await makeTerrain(scene, { height, texture: 'dry_ground_rocks', tintA: 0x4a483e, tintB: 0x2e2c26 });
    const moon = new THREE.DirectionalLight(0x9fb4e0, 0.6); moon.position.set(200, 300, -100); scene.add(moon);
    scene.add(new THREE.HemisphereLight(0x31405c, 0x0c0c10, 0.25));
    // little town (Bethlehem) with lamplit windows on a distant hill
    const town = v3(40, 0, -520); town.y = height(town.x, town.z);
    const pts = [], r = rng(8);
    for (let i = 0; i < 90; i++) pts.push(new THREE.Vector3(town.x + r.range(-40, 40), town.y + r.range(2, 12), town.z + r.range(-25, 25)));
    const g = new THREE.BufferGeometry().setFromPoints(pts);
    const lights = new THREE.Points(g, new THREE.PointsMaterial({ color: new THREE.Color(3, 1.8, 0.8), size: 2.2, sizeAttenuation: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
    scene.add(lights);
    // the descending light
    const star = new THREE.Mesh(new THREE.SphereGeometry(3, 24, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(12, 10, 7), fog: false }));
    scene.add(star);
    const beam = lightBeam({ from: town.clone().add(v3(0, 600, 0)), to: town.clone().add(v3(0, -5, 0)), width: 14, height: 14, intensity: 0, color: 0xfff0d0, fadeStart: 0.05, fadeEnd: 0.98, softness: 0.48, noise: 0.25, up: v3(0, 0, 1) });
    scene.add(beam);
    const glowL = new THREE.PointLight(0xffe0b0, 0, 400, 1.2); scene.add(glowL);
    updaters.push((t, p) => {
      const k = easeInOut(p * 1.15);
      star.position.copy(town).add(v3(0, 420 - 380 * k, 0));
      glowL.position.copy(star.position); glowL.intensity = 4000 * smooth(0.2, 1.0, p);
      beam.userData.uniforms.intensity.value = 0.28 * smooth(0.1, 0.7, p); beam.userData.uniforms.time.value = t;
      star.scale.setScalar(1 + 1.2 * smooth(0.5, 1.0, p));
      sky.uniforms.time.value = t;
    });
    camPath = (p) => v3(-6 + 4 * p, height(-6, 30) + 12, 30 - 10 * p);
    lookPath = (p) => v3(30, height(30, -500) + 120 - 60 * easeInOut(p), -500);
    exposure = 1.2;
  }

  return {
    scene, camera: cam,
    post: { look, dof: null, exposure, bloom: { intensity: 0.9, threshold: 0.75 }, godrays, vignette: { darkness: 0.55 } },
    update(t, p) { cam.position.copy(camPath(p)); cam.lookAt(lookPath(p)); updaters.forEach((u) => u(t, p)); },
  };
}
