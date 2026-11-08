// Shared render context (set by main.js). Rigs read CTX.camera for catchlights / facing.
export const CTX = { camera: null, renderer: null, scene: null, t: 0, W: 720, H: 1280 };

// Eye lighting shared by all eyeball shaders (set per set/scene for mood): key direction in WORLD space.
import * as THREE from 'three';
export const EYE_LIGHT = {
  uKeyDir: { value: new THREE.Vector3(0.4, 0.6, 0.7).normalize() },  // world space, toward the light
  uKeyColor: { value: new THREE.Color(1.0, 0.95, 0.88) },
  uAmbient: { value: new THREE.Color(0.55, 0.55, 0.62) },
};
