// debug: perf breakdown of EDGE (temporary).
import * as THREE from 'three';
export async function setup(app) { const set = await app.set('EDGE');
  return { scene: set.scene, set, look: set.look, e: set.props.terrain.userData.material, basic: new THREE.MeshBasicMaterial({ vertexColors: true }) }; }
export async function update(t, app, s) {
  const st = Math.floor(t); const P = s.set.props;
  s.set.update(t, {});
  const E = st === 9;
  for (const o of s.scene.children) if (o.isMesh || o.isGroup) o.visible = !E;
  P.terrain.userData.inner.material = P.terrain.userData.outer.material = st === 1 ? s.basic : s.e;
  if (st === 2) P.terrain.visible = false;
  if (st === 3) P.path.visible = false;
  app.camera.position.set(0.1, 1.55, 5.2); app.camera.fov = 32; app.camera.updateProjectionMatrix(); app.camera.lookAt(0.1, 1.42, 0);
}
