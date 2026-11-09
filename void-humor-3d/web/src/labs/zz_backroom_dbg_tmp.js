// TEMP: time BACKROOM update() on the CPU (deleted after use)
import * as THREE from 'three';
export async function setup(app) {
  const set = await app.set('BACKROOM');
  const opts = (t) => ({ crash: 1, crashT: t % 6, latch: 1, cageDoor: 0.5, bucketHat: { pos: [3.9, 1.1, -4.0] }, mopWig: 0.7, rollBucket: 0.3 });
  for (let i = 0; i < 50; i++) set.update(i * 0.04, opts(i * 0.04));
  let a = performance.now();
  for (let i = 0; i < 400; i++) set.update(i * 0.0417, opts(i * 0.0417));
  const crash = (performance.now() - a) / 400;
  a = performance.now();
  for (let i = 0; i < 400; i++) set.update(i * 0.0417, {});
  const quiet = (performance.now() - a) / 400;
  a = performance.now();
  for (let i = 0; i < 400; i++) set.update(i * 0.0417, { cosmos: 0.5 });
  const cos = (performance.now() - a) / 400;
  console.log(`update ms: crash ${crash.toFixed(3)} quiet ${quiet.toFixed(3)} cosmos ${cos.toFixed(3)}`);
  let tris = 0, draws = 0;
  set.update(1, opts(1));
  set.scene.traverseVisible((o) => { if (o.isMesh) { draws++; const g = o.geometry; tris += (g.index ? g.index.count : g.attributes.position.count) / 3 * (o.isInstancedMesh ? o.count : 1); } });
  console.log(`visible meshes ${draws}, triangles ${Math.round(tris)}`);
  return { scene: set.scene, look: set.look };
}
export async function update(t, app, S) {}
