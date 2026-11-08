// App shell. Two modes:
//   film (default): scenes from src/scenes/index.js, placed in time by data/timeline.json
//   lab  (?lab=<name>): src/labs/<name>.js — a free test bench (turntables, expression sheets)
// window.renderAt(t, quality) renders a frame and returns a JPEG data URL. Pure function of t.
import * as THREE from 'three';
import { CTX, EYE_LIGHT } from './core/context.js';
import { GLOBAL } from './core/materials.js';
import { loadTimeline, TL } from './core/timeline.js';
import { loadLipsync } from './core/speech.js';
import { makePost } from './core/post.js';

const W = 720, H = 1280;
const params = new URLSearchParams(location.search);
const LAB = params.get('lab');
const DISSOLVE = 1.0;

const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
const out = document.createElement('canvas'); out.width = W; out.height = H;
const o2d = out.getContext('2d');

const camera = new THREE.PerspectiveCamera(35, W / H, 0.05, 400);
CTX.camera = camera; CTX.renderer = renderer; CTX.W = W; CTX.H = H;
const post = makePost(renderer, new THREE.Scene(), camera, W, H);

// --- shared registries (characters and sets are built once and reused across scenes)
const app = {
  THREE, renderer, camera, post, CTX, EYE_LIGHT, W, H,
  chars: {}, sets: {},
  async char(name) {
    if (!this.chars[name]) { const mod = await import('./chars/index.js'); this.chars[name] = await mod.CHARS[name](); }
    return this.chars[name];
  },
  async set(name) {
    if (!this.sets[name]) { const mod = await import('./sets/index.js'); this.sets[name] = await mod.SETS[name](); }
    return this.sets[name];
  },
};
window.app = app;

let scenes = [], lab = null;
const live = new Map();   // scene id -> { mod, state }

async function ensureScene(mod) {
  if (!live.has(mod.id)) {
    const state = (await mod.setup(app)) || {};
    if (!state.scene) throw new Error(`scene ${mod.id} setup() must return { scene }`);
    live.set(mod.id, { mod, state });
  }
  return live.get(mod.id);
}

function sceneWindow(t) {
  // active scene(s) at t: [{ mod, w }] with dissolve weights
  const sc = TL.data.scenes;
  let i = sc.findIndex((s, k) => t >= s.start && (k === sc.length - 1 || t < sc[k + 1].start));
  if (i < 0) i = t < sc[0].start ? 0 : sc.length - 1;
  const res = [{ i, w: 1 }];
  const nxt = sc[i + 1], cur = sc[i];
  if (nxt && nxt.transition_in === 'dissolve' && t > nxt.start - DISSOLVE / 2) {
    const u = (t - (nxt.start - DISSOLVE / 2)) / DISSOLVE; res.push({ i: i + 1, w: u });
  }
  if (i > 0 && cur.transition_in === 'dissolve' && t < cur.start + DISSOLVE / 2) {
    const u = (t - (cur.start - DISSOLVE / 2)) / DISSOLVE; res.unshift({ i: i - 1, w: 1 - u }); res[res.length - 1].w = u;
  }
  return res;
}

async function drawScene(entry, t) {
  const { mod, state } = entry;
  // a scene may lazily (re)attach shared characters in update(); keep it awaitable
  await mod.update(t, app, state);
  post.setScene(state.scene, camera);
  post.setLook(state.look || {});
  CTX.scene = state.scene;
  post.composer.render();
}

window.renderAt = async (t, quality = 0.93) => {
  CTX.t = t;
  GLOBAL.uTime.value = t;
  if (lab) {
    await lab.update(t, app, lab.state);
    post.setScene(lab.state.scene, camera);
    post.setLook(lab.state.look || {});
    post.composer.render();
    o2d.globalAlpha = 1; o2d.drawImage(renderer.domElement, 0, 0);
  } else {
    const win = sceneWindow(t);
    for (let k = 0; k < win.length; k++) {
      const { i, w } = win[k];
      const entry = await ensureScene(scenes[i]);
      await drawScene(entry, t);
      o2d.globalAlpha = k === 0 ? 1 : w;
      o2d.drawImage(renderer.domElement, 0, 0);
    }
    o2d.globalAlpha = 1;
  }
  return quality > 0 ? out.toDataURL('image/jpeg', quality) : null;
};

// Debug helper: which scene/beat is at t
window.whereAt = (t) => {
  const sc = TL.data.scenes.find((s, k, a) => t >= s.start && (k === a.length - 1 || t < a[k + 1].start));
  const b = TL.data.order.find((id) => t >= TL.data.beats[id].start && t < TL.data.beats[id].end);
  return { scene: sc && sc.id, beat: b || null };
};
window.prepareRange = async (t0, t1) => {   // build every scene touching [t0,t1] up front
  for (const s of TL.data.scenes) {
    const idx = TL.data.scenes.indexOf(s); const end = TL.data.scenes[idx + 1]?.start ?? TL.data.duration;
    if (end >= t0 - DISSOLVE && s.start <= t1 + DISSOLVE) await ensureScene(scenes[idx]);
  }
};

(async () => {
  try {
    if (LAB) {
      try { await loadTimeline('/data/timeline.json'); } catch (e) { TL.data = { scenes: [], beats: {}, order: [], fps: 24 }; }
      await loadLipsync('/data/lipsync.json');
      const mod = await import(`./labs/${LAB}.js`);
      lab = { mod, update: mod.update, state: (await mod.setup(app)) || {} };
    } else {
      await loadTimeline('/data/timeline.json');
      await loadLipsync('/data/lipsync.json');
      const mod = await import('./scenes/index.js');
      scenes = TL.data.scenes.map((s) => {
        const m = mod.SCENES[s.id];
        if (!m) throw new Error('no scene module for ' + s.id);
        return m;
      });
    }
    window.duration = TL.data?.duration || 0;
    window.ready = true;
  } catch (e) {
    console.error('INIT ERROR', e.stack || e.message);
    window.initError = String(e.stack || e.message);
    window.ready = true;
  }
})();
