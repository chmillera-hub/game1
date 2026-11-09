// Temporary probe: COSMOS set alone (init time / perf). Safe to delete.
import { applyShot } from '../core/camera.js';
import { create } from '../sets/cosmos.js';
export async function setup(app) { const cos = await create(); return { cos, scene: cos.scene, look: cos.look }; }
export async function update(t, app, s) {
  applyShot(app.camera, { pos: [0.35, 1.35, 6.6], look: [0.3, 1.95, 0], fov: 50, drift: 0 }, t);
  if (t >= 9000) { s.cos.group.visible = false; return; }
  s.cos.group.visible = true;
  const v = Math.floor(t / 1000); t = t % 1000;
  s.cos.attach(s.cos.scene);
  s.cos.update(t, { reveal: t >= 100 ? 0.55 : 1, center: [0.1, 0, 0.05], source: [0.95, 2.05, 0.55], puffs: v === 1 ? 0 : 1, stars: v === 3 ? 0 : 1, galaxies: v === 3 ? 0 : 1, glyphs: v === 3 ? 0 : 1, blendShell: v === 5 });
  if (v === 2) s.cos.props.dome.visible = false;

  if (v === 4) { s.cos.props.dome.visible = false; s.cos.props.floor.visible = false; s.cos.props.puffs.visible = false; }
}
