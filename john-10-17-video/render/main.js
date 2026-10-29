// In-page engine: builds one shot at a time and renders frames on request.
import * as THREE from 'three';
import { makeComposer } from './lib/post.js';
import { preloadFigureTextures } from './lib/figure.js';
import { FOG } from './lib/sky.js';

const W = 720, H = 1280;
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance', stencil: false });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
window.__renderer = renderer;
window.THREE = THREE;

let current = null;

window.QUALITY = { shadow: 2048, msaa: 0, scale: 0.75 };
window.setupShot = async (spec) => {
  if (spec.quality) Object.assign(window.QUALITY, spec.quality);
  const sc = window.QUALITY.scale || 1; renderer.setSize(Math.round(W * sc), Math.round(H * sc));
  if (window.QUALITY.shadowType) renderer.shadowMap.type = { pcf: THREE.PCFShadowMap, pcfsoft: THREE.PCFSoftShadowMap, basic: THREE.BasicShadowMap, vsm: THREE.VSMShadowMap }[window.QUALITY.shadowType];
  await preloadFigureTextures();
  const mod = await import(`/render/shots/${spec.module}.js`);
  const shot = await mod.build({ renderer, W, H, spec, params: spec.params || {}, duration: spec.duration });
  const { composer, handles } = makeComposer(renderer, shot.scene, shot.camera, shot.post || {});
  current = { shot, composer, handles, spec };
  shot.camera.aspect = W / H;
  shot.camera.updateProjectionMatrix();
  // Prime shaders and shadow maps with a first frame.
  shot.update(0, 0, handles);
  composer.render(1 / 24);
  return { ok: true, fog: FOG.uFogDensity.value };
};

window.renderFrame = (tLocal, quality = 0.94) => {
  if (window.QUALITY.noCapture) { const { shot, composer, spec } = current; shot.update(tLocal, tLocal / spec.duration, current.handles); composer.render(1 / 24); return ''; }
  const { shot, composer, handles, spec } = current;
  const p = tLocal / spec.duration;
  shot.update(tLocal, p, handles);
  composer.render(1 / 24);
  return renderer.domElement.toDataURL('image/jpeg', quality);
};

window.ready = true;
