// Shared helpers for s05 / s06 / s07 (the title line, "what the actual", the Void's whisper). Not a scene module (the
// registry only loads sNN.js). Pure functions of t built from beat/word refs; no state carried between frames.
//   - the three characters' base blocking at JV / V / U (continuity with s04's end and s08's start)
//   - Jesus's LEFT arm around the Void (palm on its real velvet surface, recomputed every frame)
//   - the seated user's raised RIGHT "defend" hand (s04's target, blended to s08's plain preset by s07's end)
//   - props: the galaxy reflected in the user's irises (s05b03), a falling tear drop (s05b05), a star sprite
import * as THREE from 'three';
import { T } from '../core/timeline.js';
import { CTX } from '../core/context.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { speechAt } from '../core/speech.js';
import { EDGE, galaxyAt, galaxySpin } from './marks.js';
import { V3, toV, voidSurface, scopeVisible } from './edgeprops.js';

export const M = EDGE.M;
export const W = (p) => EDGE.W(p);
export const L3 = (x, y, z) => V3(...EDGE.W(x, y, z));
/** stage-local direction (x, z) as a world unit Vector3 */
export const WDIR = (x, z) => { const a = EDGE.W(x, 0, z), o = EDGE.W(0, 0, 0); return V3(a[0] - o[0], 0, a[2] - o[2]).normalize(); };

/** speechAt with NaNs scrubbed (several envelopes in data/lipsync.json end in NaN) */
export function speechSafe(spk, t) {
  const sp = speechAt(spk, t);
  if (!sp) return null;
  for (const kk of ['open', 'wide', 'round', 'close']) if (!Number.isFinite(sp[kk])) sp[kk] = 0;
  return sp;
}

/** Jesus's left palm on the Void's right flank (s04's search: ~0.42 m from his shoulder, on its velvet curve). */
export function aroundTarget(vd, jesus, hgt = 1.32, out = 0.015) {
  const sh = jesus.anchor('shoulderL');
  let best = null, bd = 1e9;
  for (let a = -1.6; a <= -0.5; a += 0.04) {
    const p = voidSurface(vd, hgt, a, out);
    const d = Math.abs(p.distanceTo(sh) - 0.42) + 0.6 * Math.abs(a + 1.0);
    if (d < bd) { bd = d; best = p; }
  }
  return best;
}

/** the user's raised RIGHT hand target exactly as s04 (from the shoulder reference computed in setup) */
export function defendTarget(R) {
  const sh = R.userShoulderR, a = EDGE.Y(M.U.yaw) - 0.95;
  return sh.clone().add(V3(Math.sin(a) * 0.3, 0.2, Math.cos(a) * 0.3));
}

/** world wrist of the user's plain 'defend' preset (s08's), read once in setup */
export function plainDefendWrist(user, t, base) {
  user.update(t, { ...base, armR: { preset: 'defend' } });
  return user.root.localToWorld(user.arms.R.wrist.clone());
}

/** the user's seat (U) — s07b05's 2.5 cm scoot back is kept to the end of s07 */
export function userPosAt(t, scootT = null) {
  const p = W(M.U.p);
  if (scootT == null) return p;
  const y = EDGE.Y(M.U.yaw);
  const u = smooth(clamp((t - scootT) / 0.22));
  return [p[0] - Math.sin(y) * 0.025 * u, 0, p[2] - Math.cos(y) * 0.025 * u];
}

// ---------------------------------------------------------------------------------------------- the iris galaxy
let _galTex = null;
function galaxyTex() {
  if (_galTex) return _galTex;
  const S = 128, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d'); g.translate(S / 2, S / 2);
  const gr = g.createRadialGradient(0, 0, 0, 0, 0, 60); gr.addColorStop(0, 'rgba(255,245,225,1)'); gr.addColorStop(0.2, 'rgba(230,200,255,0.7)'); gr.addColorStop(0.6, 'rgba(170,140,255,0.2)'); gr.addColorStop(1, 'rgba(150,120,255,0)');
  g.fillStyle = gr; g.beginPath(); g.arc(0, 0, 60, 0, 7); g.fill();
  g.lineCap = 'round';
  for (let arm = 0; arm < 2; arm++) {
    g.beginPath();
    for (let k = 0; k < 50; k++) { const a = arm * Math.PI + k * 0.12, r = 4 + k * 1.05; const x = Math.cos(a) * r, y = Math.sin(a) * r; k ? g.lineTo(x, y) : g.moveTo(x, y); }
    g.strokeStyle = 'rgba(255,240,255,0.9)'; g.lineWidth = 6; g.stroke();
  }
  _galTex = new THREE.CanvasTexture(c); _galTex.colorSpace = THREE.SRGBColorSpace;
  return _galTex;
}
/**
 * A tiny turning spiral galaxy highlight on each of the user's corneas (the sky galaxy, reflected), visible only in
 * [a, b). Placed like a real specular reflection (half-vector of camera and galaxy directions), pulled toward the
 * iris so it reads; call update(t, alpha) after user.update() each frame.
 */
export function makeIrisGalaxy(user, a, b) {
  const meshes = user.face.eyes.map((eye) => {
    const m = new THREE.Mesh(new THREE.CircleGeometry(eye.r * 0.17, 20), new THREE.MeshBasicMaterial({
      map: galaxyTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false, color: new THREE.Color(1.3, 1.15, 1.5), opacity: 0 }));
    m.renderOrder = 4;
    eye.inner.add(m);
    scopeVisible(m, a, b);
    return m;
  });
  return {
    meshes,
    update(t, alpha = 1, pull = 0.55) {
      const cam = CTX.camera, gp = galaxyAt(t);
      user.face.eyes.forEach((eye, i) => {
        const m = meshes[i];
        if (!cam || !gp || alpha <= 0) { m.material.opacity = 0; return; }
        eye.inner.updateWorldMatrix(true, false);
        const inv = new THREE.Matrix4().copy(eye.inner.matrixWorld).invert();
        const Lg = toV(gp).applyMatrix4(inv).normalize(), Vc = cam.position.clone().applyMatrix4(inv).normalize();
        // where the eyeball's iris points (ball rotation), so the highlight sits on the iris
        const ir = V3(0, 0, 1).applyEuler(eye.ball.rotation);
        // a reflection of the sky: upper part of the iris, toward the camera (never on the pinpoint pupil)
        const up = V3(0, 1, 0).addScaledVector(ir, -ir.y).normalize();
        const n = Lg.clone().add(Vc).normalize().lerp(ir, pull).normalize().addScaledVector(up, 0.2).normalize();
        m.position.copy(n).multiplyScalar(eye.r * 1.02);
        m.lookAt(eye.inner.localToWorld(n.clone().multiplyScalar(eye.r * 3)));
        m.rotateZ(galaxySpin(t) * 3);
        m.material.opacity = 0.85 * alpha;
      });
    },
  };
}

// ---------------------------------------------------------------------------------------------- a tear drop
/** One glossy tear that gathers at the chin and drips off (s05b05). update(t, user) after user.update(). */
export function makeTearDrop(scene, a, b) {
  const mat = new THREE.MeshStandardMaterial({ color: 0xdff0ff, roughness: 0.05, metalness: 0.0, transparent: true, opacity: 0.85, emissive: 0x4a6a8a, emissiveIntensity: 0.6 });
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.0055, 14, 10), mat);
  m.renderOrder = 4;
  scene.add(m);
  scopeVisible(m, a, b);
  return {
    mesh: m,
    /** t0: the drop starts sliding from the jaw; tf: it lets go of the chin */
    update(t, user, t0, tf, side = 1) {
      if (t < t0) { m.scale.setScalar(1e-4); return; }
      const mouth = user.anchor('mouth'), head = user.anchor('head');
      const down = mouth.clone().sub(head).normalize();
      const right = user.anchor('earL').sub(user.anchor('earR')).normalize();
      const fwd = mouth.clone().sub(head); fwd.addScaledVector(down, -fwd.dot(down)).normalize();
      const chin = mouth.clone().addScaledVector(down, 0.045).addScaledVector(fwd, -0.006);
      const jaw = chin.clone().addScaledVector(right, side * 0.028).addScaledVector(down, -0.02).addScaledVector(fwd, -0.012);
      let p, s = 1;
      if (t < tf) {
        const u = smooth(clamp((t - t0) / Math.max(0.05, tf - t0)));
        p = jaw.clone().lerp(chin, u);
        s = 0.6 + 0.6 * u;                                     // gathers as it slides to the chin point
        p.addScaledVector(down, 0.004 * s);
      } else {
        const dt = t - tf;
        p = chin.clone().addScaledVector(down, 0.004 * 1.2).add(V3(0, -4.9 * dt * dt, 0));
        s = 1.2 * (1 - smooth(clamp((dt - 0.25) / 0.15)));
      }
      m.position.copy(p);
      m.scale.set(s, s * 1.25, s);
    },
  };
}
