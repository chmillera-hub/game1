// Character base class: the contract every rig in src/chars/ follows. See docs/ENGINE.md §Characters.
import * as THREE from 'three';
import { speechAt } from './speech.js';
import { fbm1, clamp } from './util.js';

export class Character {
  /**
   * @param {object} o  { name: 'JESUS', speaker: 'JESUS' (lip-sync key, or null), height (m), seed }
   */
  constructor(o) {
    this.name = o.name;
    this.speaker = o.speaker ?? o.name;
    this.height = o.height ?? 1.7;
    this.seed = o.seed ?? 1;
    this.root = new THREE.Group();          // feet on the ground at the origin, faces +Z when yaw = 0
    this.root.name = o.name;
    this.face = null;                       // core/face.js Face (set by subclass)
    this.headGroup = null;                  // Object3D whose origin is the head centre (set by subclass)
    this._anch = {};
  }

  /** Place the character: pos [x,y,z] (feet), yaw (rad; 0 faces +Z / the default camera). */
  place(pos = [0, 0, 0], yaw = 0) {
    this.root.position.set(pos[0], pos[1] ?? 0, pos[2] ?? 0);
    this.root.rotation.set(0, yaw, 0);
  }

  /** Breathing helper: returns 0..1 phase-continuous breath for rate (breaths/s) */
  breath(t, rate = 0.25) { return 0.5 + 0.5 * Math.sin(t * rate * Math.PI * 2 + this.seed); }

  /** Subtle idle sway in radians (small, seeded) */
  sway(t, amp = 0.012) { return amp * fbm1(t * 0.35, this.seed * 11); }

  /** The lip-sync sample for this character at t (null if not speaking) unless pose.speech === false. */
  speech(t, pose) {
    if (pose && pose.speech === false) return null;
    if (pose && pose.speech && typeof pose.speech === 'object') return pose.speech;
    return this.speaker ? speechAt(this.speaker, t) : null;
  }

  /** World-space anchors (valid after update()). Subclasses fill this._anch with Object3D markers. */
  anchor(name) {
    const o = this._anch[name];
    if (!o) return null;
    o.updateWorldMatrix(true, false);
    return new THREE.Vector3().setFromMatrixPosition(o.matrixWorld);
  }
  /** Add a named anchor marker under `parent` at local position p. */
  addAnchor(name, parent, p = [0, 0, 0]) {
    const o = new THREE.Object3D(); o.position.set(...p); parent.add(o); this._anch[name] = o; return o;
  }
  headWorld() { return this.anchor('head'); }
  eyesWorld() { return this.anchor('eyes'); }

  /** Subclasses implement update(t, pose). Must be a pure function of (t, pose). */
  update(t, pose) { throw new Error('update() not implemented for ' + this.name); }
}

/** Resolve a gaze spec to a world point: Vector3 | [x,y,z] | Character (its eyes) | 'camera' | null */
export function gazePoint(g, camera) {
  if (!g) return null;
  if (g === 'camera') return camera.position.clone();
  if (g instanceof THREE.Vector3) return g.clone();
  if (Array.isArray(g)) return new THREE.Vector3(...g);
  if (g.eyesWorld) return g.eyesWorld();
  return null;
}
