// Probe (dev only): API sanity sweep — every preset / extreme pose; reports NaNs and anchor sanity.
import * as THREE from 'three';
import { VX, VOID_EXPR, ARM, eyeRoll, whisperPose } from '../chars/void.js';
export async function setup(app) {
  const scene = new THREE.Scene();
  const vd = await app.char('VOID'); scene.add(vd.root);
  app.camera.position.set(0, 2, 8); app.camera.lookAt(0, 1.5, 0); app.camera.updateMatrixWorld();
  const bad = [];
  const chk = (label) => {
    for (const g of [vd.bodyGeo, vd.capeGeo, vd.arms.L.tube.geo, vd.arms.R.tube.geo, vd.legs.L.geo, vd.legs.R.geo, vd.arms.L.merged.mesh.geometry]) {
      const a = g.attributes.position.array; for (let i = 0; i < a.length; i++) if (!Number.isFinite(a[i])) { bad.push(label + ' geo'); return; }
    }
    for (const n of ['head', 'eyes', 'mouth', 'mouthDir', 'whisper', 'earL', 'earR', 'chest', 'back', 'backLow', 'shoulderL', 'shoulderR', 'sideL', 'sideR', 'hip', 'handL', 'handR', 'footL', 'footR', 'kickFoot', 'hoodTop']) {
      const v = vd.anchor(n); if (!v || !Number.isFinite(v.x + v.y + v.z)) bad.push(label + ' anchor ' + n);
    }
  };
  let n = 0;
  for (const p of Object.keys(ARM)) for (const side of ['L', 'R']) { vd.update(1, { ['arm' + side]: { preset: p, target: [1.5, 1.4, 0.8] } }); chk('arm ' + p + side); vd.update(1.3, { ['arm' + side]: { preset: p, from: 'rest', mix: 0.5 } }); chk('mix ' + p); n += 2; }
  for (const e of Object.keys(VOID_EXPR)) { vd.update(2, { face: VX(e) }); chk('expr ' + e); n++; }
  const extremes = [
    { body: { sit: 1 }, extra: { kick: 1 } }, { body: { kneel: 1, lean: 0.8 } }, { body: { crouch: 1, shrug: 1, slump: 1 } }, { extra: { kick: -0.5, kickSide: 'L' } }, { extra: { kick: 1.25 } },
    { walk: { amount: 1, phase: 0.37, style: 'run' } }, { walk: { amount: 1, phase: 0.8, style: 'stomp' } }, { walk: { amount: 1, phase: 0.1, style: 'sneak' } },
    { head: { yaw: 2.5, pitch: 0.8, roll: 0.5, track: 1 }, gaze: [3, 1, 2] }, { gaze: 'camera', head: { track: 0.5 } }, { extra: { puff: 1, laugh: 1, cosmos: 1, cough: { t0: 0, t1: 5 } } },
    { ...whisperPose(-1, 1.3, 1) }, { face: VX('annoyed', eyeRoll(0.5)) }, { body: { recoil: 1, bounce: 0.2, swell: 1, stretch: 0.1, pitch: 0.3 }, extra: { hem: 1 } },
    { armL: { preset: 'tip', target: [0.5, 1.2, 1.1], tip: true, fingers: [0, 0, 1] }, armR: { preset: 'pat', target: [-1.5, 1.5, 0.5], pat: 1 } },
  ];
  extremes.forEach((p, i) => { vd.update(3 + i * 0.1, p); chk('extreme ' + i); n++; });
  const pos = vd.solvePos(4, { ...whisperPose(1, 0.9) }, 'whisper', new THREE.Vector3(1, 1.6, 1.2));
  console.log('solvePos', pos.map((v) => v.toFixed(2)), 'err', pos.err.toFixed(3), 'whisper now', vd.anchor('whisper').toArray().map((v) => v.toFixed(2)));
  vd.update(5, { gaze: vd });   // Character as gaze (its own eyes: degenerate but must not NaN)
  chk('gaze char');
  console.log('checked', n, 'poses; problems:', bad.length ? bad.slice(0, 20).join(' | ') : 'none');
  return { scene, look: {} };
}
export async function update(t, app, s) { app.camera.position.set(0, 2, 8); app.camera.lookAt(0, 1.5, 0); }
