// TEMP perf probe for the BACKROOM set (mode = floor(t / 100)); delete when done.
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { SETS } from '../sets/index.js';
export async function setup(app) { const set = await SETS.BACKROOM(); app.camera.layers.enableAll(); return { scene: set.scene, set, look: set.look }; }
export async function update(t, app, S) {
  const mode = Math.floor(t / 100), set = S.set, sc = set.scene;
  set.update(t % 100, {});
  const find = (fn) => { const a = []; sc.traverse((o) => { if (fn(o)) a.push(o); }); return a; };
  if (mode === 1) find((o) => o.material && o.material.type === 'ShaderMaterial' && o.material.blending === THREE.AdditiveBlending && o.geometry?.type === 'CylinderGeometry').forEach((o) => (o.visible = false));
  set.props.key.castShadow = mode !== 2;
  if (mode === 3) { set.props.bulb2.visible = false; set.props.voidLight.visible = false; } else { set.props.bulb2.visible = true; set.props.voidLight.visible = true; }
  if (mode === 4) set.props.room.visible = false;
  if (mode === 5) { set.props.fx.mesh.visible = false; set.props.fxN.mesh.visible = false; }
  if (mode === 6) { set.props.corner.visible = false; set.props.cage.visible = false; }
  applyShot(app.camera, framed([-0.5, 1.25, -0.9], { dist: 11, yaw: 6, pitch: 4, fov: 35, screenY: 0.47, drift: 0 }), t);
  S.look = set.look;
}
