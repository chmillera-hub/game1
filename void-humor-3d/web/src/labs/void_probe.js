// Probe (dev only): robust in-page perf breakdown (interleaved variants, min of N, forced GPU sync).
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { CTX } from '../core/context.js';
import { GLOBAL } from '../core/materials.js';
import { VX } from '../chars/void.js';
export async function setup(app) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x806090);
  scene.add(new THREE.HemisphereLight(0xffe2cc, 0x4a3a66, 1.1));
  const key = new THREE.DirectionalLight(0xffd9b8, 2.4); key.position.set(4, 6, 5); scene.add(key);
  const vd = await app.char('VOID'); scene.add(vd.root);
  const gl = app.renderer.getContext(); const px = new Uint8Array(4);
  const shots = { full: framed([0, 1.5, 0], { dist: 8, fov: 32, screenY: 0.46, drift: 0 }), close: framed([0, 2.0, 0.35], { dist: 3.6, fov: 30, screenY: 0.36, drift: 0 }) };
  app.post.setScene(scene, app.camera); app.post.setLook({ bloom: 0.6 });
  const all = () => [vd.arms.L.merged.mesh, vd.arms.R.merged.mesh, vd.body, vd.cape, vd.hood, vd.faceField, vd.fx.mesh, vd.shadow, vd.hoodGlow, ...vd.halos, ...vd.browHalo.map((b) => b.mesh), ...vd.face.brows.map((b) => b.tube.mesh), vd.face.decal.mesh, ...vd.face.eyes.map((e) => e.group), ...['L', 'R'].flatMap((k) => [vd.arms[k].tube.mesh, vd.legs[k].mesh, vd.feet[k].group])];
  const V = {
    none: () => { vd.root.visible = false; },
    all: () => {},
    noBodyCapeHood: () => { vd.body.visible = vd.cape.visible = vd.hood.visible = false; },
    noHands: () => { vd.arms.L.merged.mesh.visible = vd.arms.R.merged.mesh.visible = false; },
    noArmsLegs: () => { for (const k of ['L', 'R']) { vd.arms[k].tube.mesh.visible = false; vd.legs[k].mesh.visible = false; vd.feet[k].group.visible = false; } },
    noFaceStuff: () => { vd.faceField.visible = false; vd.face.decal.mesh.visible = false; vd.face.eyes.forEach((e) => e.group.visible = false); vd.face.brows.forEach((b) => b.tube.mesh.visible = false); vd.browHalo.forEach((b) => b.mesh.visible = false); vd.halos.forEach((h) => h.visible = false); vd.hoodGlow.visible = false; },
    basicBody: () => { vd.body.material = vd.cape.material = basic; vd.hood.material = [basic, vd.faceMat]; },
    stdBody: () => { vd.body.material = vd.cape.material = std; vd.hood.material = [std, vd.faceMat]; },
    noFx: () => { vd.fx.mesh.visible = false; vd.shadow.visible = false; },
  };
  const extra = new THREE.Group(); scene.add(extra); extra.visible = false;
  for (let i = 0; i < 30; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.02, 8, 6), vd.velvet); m.position.set(-1 + i * 0.07, 0.3, 2); extra.add(m); }
  const basic = new THREE.MeshBasicMaterial({ color: 0x302050 }), std = new THREE.MeshStandardMaterial({ color: 0x302050, roughness: 0.8 });
  const restoreM = () => { vd.body.material = vd.cape.material = vd.velvet; vd.hood.material = [vd.velvet, vd.faceMat]; };
  const res = {};
  for (const sh of ['full']) {
    applyShot(app.camera, shots[sh], 0);
    for (let rep = 0; rep < 10; rep++) for (const [n, f] of Object.entries(V)) {
      vd.root.visible = true; extra.visible = false; restoreM(); for (const o of all()) o.visible = true;
      vd.update(1 + rep / 24, { face: VX('laugh'), extra: { laugh: 0.5 } });
      f();
      GLOBAL.uTime.value = 1;
      const t0 = performance.now(); app.post.composer.render(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
      const dt = performance.now() - t0; const key = sh + ':' + n; res[key] = Math.min(res[key] ?? 1e9, dt);
    }
  }
  for (const [k, v] of Object.entries(res)) console.log(k.padEnd(22), v.toFixed(0), 'ms');
  const tu = performance.now(); for (let i = 0; i < 30; i++) vd.update(2 + i / 24, { face: VX('laugh'), extra: { laugh: 0.5 } }); console.log('update() ms', ((performance.now() - tu) / 30).toFixed(1));
  return { scene, vd, look: { bloom: 0.6 } };
}
export async function update(t, app, s) { applyShot(app.camera, framed([0, 1.5, 0], { dist: 8, fov: 32, screenY: 0.46, drift: 0 }), t); }
