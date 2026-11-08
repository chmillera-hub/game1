// Scene registry: every timeline scene id maps to ./<id>.js (default export { id, setup, update }).
// A missing/broken module falls back to a placeholder so the rest of the film still renders.
import * as THREE from 'three';
import { TL } from '../core/timeline.js';

function placeholder(id, err) {
  return {
    id,
    async setup() {
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x30283c);
      const c = document.createElement('canvas'); c.width = 512; c.height = 256;
      const g = c.getContext('2d'); g.fillStyle = '#fff'; g.font = 'bold 40px sans-serif'; g.textAlign = 'center';
      g.fillText(`scene ${id}`, 256, 110); g.font = '20px sans-serif'; g.fillText(err ? 'ERROR: ' + String(err).slice(0, 40) : '(not animated yet)', 256, 160);
      const tex = new THREE.CanvasTexture(c);
      const m = new THREE.Mesh(new THREE.PlaneGeometry(2, 1), new THREE.MeshBasicMaterial({ map: tex }));
      m.position.set(0, 1.5, 0); scene.add(m);
      return { scene };
    },
    async update(t, app) { app.camera.position.set(0, 1.5, 3.2); app.camera.fov = 35; app.camera.updateProjectionMatrix(); app.camera.lookAt(0, 1.5, 0); },
  };
}

export const SCENES = new Proxy({}, {
  get(_, id) {
    if (typeof id !== 'string' || !/^s\d+/.test(id)) return undefined;
    let real = null;
    return {
      id,
      async setup(app) {
        try { real = (await import(`./${id}.js`)).default; }
        catch (e) { console.log(`scene ${id}: ${e.message}`); real = placeholder(id, /Failed to fetch|not found|404/i.test(e.message) ? null : e.message); }
        try { return await real.setup(app); }
        catch (e) { console.log(`scene ${id} setup error: ${e.stack || e.message}`); real = placeholder(id, e.message); return real.setup(app); }
      },
      async update(t, app, st) { return real.update(t, app, st); },
    };
  },
});
