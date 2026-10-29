// Procedural robed figures (Jesus, disciples, Pharisees, shepherd, crowd).
// Built from draped shells with meandering folds, posable sleeves and hands, and
// head variants (long hair + beard, headcloth, turban). Shots frame them mostly
// backlit, from behind or in silhouette, in keeping with reverent depictions.
import * as THREE from 'three';
import { rng, noise3, canvasTex } from './util.js';
import { loadTexture } from './assets.js';

// ---------- shared textures / materials ----------
let clothNoise = null, stripeTex = null, hairTex = null, linenNormal = null;
function getClothNoise() {
  if (clothNoise) return clothNoise;
  clothNoise = canvasTex(512, 512, (g, w, h) => {
    const img = g.createImageData(w, h);
    const r = rng(77);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const n = 0.5 + 0.22 * noise3(x / 60, y / 60, 1.3) + 0.12 * noise3(x / 13, y / 13, 4.1) + 0.06 * (r() - 0.5)
        + 0.05 * Math.sin(x * 1.7) * Math.sin(y * 1.9);
      const v = Math.max(0, Math.min(255, 200 + 70 * (n - 0.5)));
      const i = (y * w + x) * 4; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
  }, { repeat: [1, 1] });
  return clothNoise;
}
function getStripeTex() {
  if (stripeTex) return stripeTex;
  // Prayer-shawl stripes: bands near the lower edge (v small).
  stripeTex = canvasTex(64, 512, (g, w, h) => {
    g.fillStyle = '#eee8dc'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#1d2433';
    const band = (v0, v1) => g.fillRect(0, h - v1 * h, w, (v1 - v0) * h);
    band(0.08, 0.13); band(0.16, 0.18); band(0.21, 0.26);
    band(0.74, 0.79); band(0.82, 0.84); band(0.87, 0.92);
  });
  stripeTex.wrapS = THREE.RepeatWrapping;
  return stripeTex;
}
function getHairTex() {
  if (hairTex) return hairTex;
  hairTex = canvasTex(256, 512, (g, w, h) => {
    g.fillStyle = '#7a7a7a'; g.fillRect(0, 0, w, h);
    const r = rng(9);
    for (let i = 0; i < 900; i++) {
      const x = r() * w, c = 60 + r() * 140;
      g.strokeStyle = `rgba(${c},${c},${c},0.35)`; g.lineWidth = 0.6 + r() * 1.6;
      g.beginPath(); g.moveTo(x, 0);
      g.bezierCurveTo(x + (r() - 0.5) * 30, h * 0.33, x + (r() - 0.5) * 30, h * 0.66, x + (r() - 0.5) * 20, h);
      g.stroke();
    }
  });
  hairTex.wrapS = hairTex.wrapT = THREE.RepeatWrapping;
  return hairTex;
}
export async function preloadFigureTextures() {
  linenNormal = await loadTexture('/assets/tex/rough_linen/nor_gl_2k.jpg', { repeat: [3, 3] });
}

const matCache = new Map();
export function clothMat(color, { stripes = false, sheen = 0.55, rough = 0.92, side = THREE.FrontSide } = {}) {
  const key = `${color}|${stripes}|${sheen}|${rough}|${side}`;
  if (matCache.has(key)) return matCache.get(key);
  const c = new THREE.Color(color);
  const m = new THREE.MeshPhysicalMaterial({
    color: c, roughness: rough, metalness: 0, sheen, sheenRoughness: 0.75,
    sheenColor: c.clone().lerp(new THREE.Color(1, 0.95, 0.88), 0.5), side,
    map: stripes ? getStripeTex() : getClothNoise(),
    normalMap: linenNormal || null, normalScale: new THREE.Vector2(0.6, 0.6),
  });
  matCache.set(key, m);
  return m;
}
export function skinMat(color = 0xa8785a) {
  const key = 'skin' + color;
  if (!matCache.has(key)) matCache.set(key, new THREE.MeshPhysicalMaterial({ color, roughness: 0.62, sheen: 0.35, sheenColor: new THREE.Color(0xffb090), sheenRoughness: 0.5 }));
  return matCache.get(key);
}
// Subtle painted shading for the face (eye sockets, brows, lips, beard shadow) on the sphere UVs.
export function faceMat(skin = 0xa8785a, beard = true) {
  const key = 'face' + skin + beard;
  if (matCache.has(key)) return matCache.get(key);
  const c = new THREE.Color(skin);
  const tex = canvasTex(512, 256, (g, w, h) => {
    const css = (col, a = 1) => `rgba(${Math.round(col.r * 255)},${Math.round(col.g * 255)},${Math.round(col.b * 255)},${a})`;
    const base = c.clone().convertLinearToSRGB();
    g.fillStyle = css(base); g.fillRect(0, 0, w, h);
    const fx = 0.25 * w; // face centre (u = 0.25 is +Z)
    const blob = (x, y, rx, ry, col, a) => {
      const gr = g.createRadialGradient(x, y, 0, x, y, Math.max(rx, ry));
      gr.addColorStop(0, css(col, a)); gr.addColorStop(1, css(col, 0));
      g.save(); g.translate(x, y); g.scale(rx / Math.max(rx, ry), ry / Math.max(rx, ry)); g.translate(-x, -y);
      g.fillStyle = gr; g.beginPath(); g.arc(x, y, Math.max(rx, ry), 0, Math.PI * 2); g.fill(); g.restore();
    };
    const dark = base.clone().multiplyScalar(0.45), red = base.clone().lerp(new THREE.Color(0.55, 0.22, 0.2), 0.45);
    for (const sgn of [-1, 1]) {
      blob(fx + sgn * 0.052 * w, 0.405 * h, 0.03 * w, 0.03 * h, dark, 0.75);   // eye socket
      blob(fx + sgn * 0.052 * w, 0.41 * h, 0.012 * w, 0.012 * h, new THREE.Color(0.05, 0.04, 0.03), 0.9); // eye
      g.strokeStyle = css(new THREE.Color(0.1, 0.07, 0.05), 0.8); g.lineWidth = 0.012 * h;   // brow
      g.beginPath(); g.moveTo(fx + sgn * 0.025 * w, 0.355 * h); g.quadraticCurveTo(fx + sgn * 0.055 * w, 0.335 * h, fx + sgn * 0.085 * w, 0.36 * h); g.stroke();
    }
    blob(fx, 0.6 * h, 0.03 * w, 0.012 * h, red, 0.6); // lips
    blob(fx, 0.5 * h, 0.01 * w, 0.05 * h, dark, 0.25); // nose shadow
    if (beard) blob(fx, 0.66 * h, 0.12 * w, 0.14 * h, new THREE.Color(0.08, 0.05, 0.035), 0.55);
  });
  const m = new THREE.MeshPhysicalMaterial({ map: tex, roughness: 0.62, sheen: 0.35, sheenColor: new THREE.Color(0xffb090), sheenRoughness: 0.5 });
  matCache.set(key, m);
  return m;
}
export function hairMat(color = 0x2a1b12) {
  const key = 'hair' + color;
  if (!matCache.has(key)) matCache.set(key, new THREE.MeshStandardMaterial({ color, roughness: 0.6, map: getHairTex(), side: THREE.DoubleSide }));
  return matCache.get(key);
}

// ---------- geometry helpers ----------
// A draped shell: rings of ellipses with radial fold displacement.
// rings: [{y, r, sx, sz, fold, dz}] bottom to top. arc: [thetaStart, thetaLen] (front is +Z = PI/2).
export function shellGeometry(rings, { seg = 64, seed = 1, freq = 9, arc = null, uvScale = [1.6, 1.6], hemNoise = 0.02, curl = 0, hem = null, hemRings = 6 } = {}) {
  const r = rng(seed);
  const ph1 = r() * 10, ph2 = r() * 10, ph3 = r() * 10;
  const th0 = arc ? arc[0] : 0, thL = arc ? arc[1] : Math.PI * 2;
  const closed = !arc;
  const cols = closed ? seg : seg + 1;
  const pos = [], uv = [], idx = [];
  // resample rings densely along y for smooth folds
  const dense = [];
  const steps = 4;
  for (let i = 0; i < rings.length - 1; i++) {
    for (let s = 0; s < steps; s++) {
      const t = s / steps, a = rings[i], b = rings[i + 1];
      const L = (k, d = 0) => (a[k] ?? d) + ((b[k] ?? d) - (a[k] ?? d)) * t;
      dense.push({ y: L('y'), r: L('r'), sx: L('sx', 1), sz: L('sz', 1), fold: L('fold', 0), dz: L('dz', 0), dx: L('dx', 0) });
    }
  }
  const last = rings[rings.length - 1];
  dense.push({ y: last.y, r: last.r, sx: last.sx ?? 1, sz: last.sz ?? 1, fold: last.fold ?? 0, dz: last.dz ?? 0, dx: last.dx ?? 0 });
  for (let i = 0; i < dense.length; i++) {
    const d = dense[i];
    for (let j = 0; j < cols; j++) {
      const th = th0 + thL * (j / seg);
      const meander = 1.4 * noise3(d.y * 1.5, ph1, 0.3) + 0.6 * noise3(d.y * 4.0, ph2, th * 0.5);
      const f = d.fold * (0.62 * Math.sin(freq * th + meander + ph3) + 0.38 * Math.sin(freq * 2.13 * th - meander * 1.7 + ph1));
      const rr = d.r + f + d.r * 0.04 * noise3(Math.cos(th) * 2, Math.sin(th) * 2, d.y * 3 + ph2);
      let x = Math.cos(th) * rr * d.sx + d.dx, z = Math.sin(th) * rr * d.sz + d.dz;
      let y = d.y;
      if (i === 0) y += hemNoise * noise3(Math.cos(th) * 3, Math.sin(th) * 3, ph3);
      if (hem && i < hemRings) y += hem(th) * (1 - i / hemRings);
      if (curl && arc) { // open edges roll inward slightly
        const e = Math.min(j, cols - 1 - j) / cols;
        const k = Math.max(0, 1 - e * 12);
        x *= 1 - curl * k; z *= 1 - curl * k;
      }
      pos.push(x, y, z);
      uv.push((j / seg) * uvScale[0] * (thL / (Math.PI * 2)) * 4, d.y * uvScale[1]);
    }
  }
  for (let i = 0; i < dense.length - 1; i++) {
    for (let j = 0; j < seg; j++) {
      const a = i * cols + j, b = i * cols + ((j + 1) % cols), c = (i + 1) * cols + j, e = (i + 1) * cols + ((j + 1) % cols);
      idx.push(a, c, b, b, c, e);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

// Tapered sleeve along -Y from the joint, length L, radius r0 -> r1.
function sleeveGeometry(L, r0, r1, seed, fold = 0.008) {
  return shellGeometry([
    { y: -L, r: r1, sx: 1, sz: 0.92, fold: fold * 1.6 },
    { y: -L * 0.5, r: (r0 + r1) / 2, sx: 1, sz: 0.92, fold: fold },
    { y: 0, r: r0, sx: 1, sz: 0.92, fold: fold * 0.4 },
  ], { seg: 24, seed, freq: 5, hemNoise: 0.006 });
}

function handGeometry() {
  // Palm + fingers as a soft mitten, thumb separate. Built along -Y.
  const palm = new THREE.SphereGeometry(1, 16, 12);
  palm.scale(0.042, 0.052, 0.018); palm.translate(0, -0.045, 0);
  const fingers = new THREE.CapsuleGeometry(0.018, 0.05, 4, 10);
  fingers.scale(1.9, 1, 0.75); fingers.translate(0, -0.115, 0.004);
  const thumb = new THREE.CapsuleGeometry(0.011, 0.035, 4, 8);
  thumb.rotateZ(0.6); thumb.translate(0.04, -0.06, 0.012);
  return mergeGeoms([palm, fingers, thumb]);
}
function mergeGeoms(geoms) {
  let total = 0; geoms.forEach((g) => { total += g.attributes.position.count; });
  const pos = new Float32Array(total * 3), nor = new Float32Array(total * 3), uv = new Float32Array(total * 2);
  const idx = []; let off = 0;
  for (const g0 of geoms) {
    const g = g0.index ? g0 : g0;
    pos.set(g.attributes.position.array, off * 3);
    nor.set(g.attributes.normal.array, off * 3);
    if (g.attributes.uv) uv.set(g.attributes.uv.array, off * 2);
    const ii = g.index.array; for (let k = 0; k < ii.length; k++) idx.push(ii[k] + off);
    off += g.attributes.position.count;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  out.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  out.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  out.setIndex(idx);
  return out;
}

function headGeometry(seed) {
  const g = new THREE.SphereGeometry(0.1, 40, 32);
  const p = g.attributes.position;
  const v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).normalize();
    let s = 1;
    const front = Math.max(0, v.z);
    // nose
    s += 0.2 * Math.exp(-((v.x / 0.13) ** 2) - (((v.y + 0.12) / 0.2) ** 2)) * front ** 3;
    // brow ridge and cheek bones
    s += 0.05 * Math.exp(-(((v.y - 0.12) / 0.08) ** 2)) * front ** 2;
    s += 0.035 * Math.exp(-(((v.y + 0.1) / 0.12) ** 2) - (((Math.abs(v.x) - 0.45) / 0.18) ** 2)) * front;
    // eye sockets
    s -= 0.045 * Math.exp(-(((Math.abs(v.x) - 0.32) / 0.13) ** 2) - (((v.y - 0.04) / 0.08) ** 2)) * front ** 2;
    // jaw: narrower and longer at the bottom front
    if (v.y < -0.2) s *= 1 - 0.18 * (-v.y - 0.2) * (0.6 + 0.4 * front);
    s += 0.06 * Math.exp(-(((v.y + 0.62) / 0.14) ** 2) - ((v.x / 0.25) ** 2)) * front ** 2; // chin
    p.setXYZ(i, v.x * 0.1 * s * 0.86, v.y * 0.1 * s * 1.08, v.z * 0.1 * s * 0.96);
  }
  g.computeVertexNormals();
  return g;
}

// ---------- the figure ----------
const DEFAULTS = {
  seed: 1, height: 1.76, robe: 0xd8cfbf, mantle: null, mantleArc: 'right', head: 'hair', hair: 0x2b1b12, skin: 0xa8785a,
  beard: true, stripes: false, pose: 'stand', headgear: 0xe6dfd2, band: 0x3a2a1c, girth: 1, sash: null,
};

export function makeFigure(o = {}) {
  o = { ...DEFAULTS, ...o };
  const r = rng(o.seed);
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  const s = o.height / 1.76;
  body.scale.setScalar(s);
  const G = o.girth;
  const robeMat = clothMat(o.robe);
  const add = (geo, mat, parent = body) => { const m = new THREE.Mesh(geo, mat); m.castShadow = true; m.receiveShadow = true; parent.add(m); return m; };

  let shoulderY = 1.42, neckY = 1.47, shoulderX = 0.2;
  if (o.pose === 'stand' || o.pose === 'walk') {
    add(shellGeometry([
      { y: 0.0, r: 0.29 * G, sx: 1.0, sz: 0.9, fold: 0.022 },
      { y: 0.3, r: 0.25 * G, sx: 1.0, sz: 0.82, fold: 0.018 },
      { y: 0.7, r: 0.215 * G, sx: 1.02, sz: 0.76, fold: 0.012 },
      { y: 0.96, r: 0.2 * G, sx: 1.04, sz: 0.74, fold: 0.008 },
      { y: 1.04, r: 0.172 * G, sx: 1.06, sz: 0.74, fold: 0.006 },
      { y: 1.22, r: 0.19 * G, sx: 1.08, sz: 0.68, fold: 0.006 },
      { y: 1.34, r: 0.205 * G, sx: 1.12, sz: 0.6, fold: 0.004 },
      { y: 1.395, r: 0.19 * G, sx: 1.12, sz: 0.6, fold: 0.003 },
      { y: 1.435, r: 0.135, sx: 1.12, sz: 0.66, fold: 0.002 },
      { y: 1.462, r: 0.085, sx: 1.05, sz: 0.85, fold: 0 },
      { y: 1.48, r: 0.058, sx: 1, sz: 1, fold: 0 },
    ], { seed: o.seed, freq: 8 + r.int(0, 3) }), robeMat);
    if (o.sash) {
      add(shellGeometry([{ y: 1.0, r: 0.192 * G, sx: 1.05, sz: 0.75, fold: 0.004 }, { y: 1.09, r: 0.182 * G, sx: 1.06, sz: 0.74, fold: 0.004 }], { seed: o.seed + 3, freq: 14 }), clothMat(o.sash));
    }
  } else {
    // kneeling or seated: low wide base with legs folded under, upright torso.
    const kneel = o.pose === 'kneel';
    const top = kneel ? 1.08 : 0.92;
    const k = (y) => y * (top - 0.0) / 1.475;
    shoulderY = k(1.42); neckY = k(1.475);
    const lowRings = kneel ? [
      { y: 0.0, r: 0.31, sx: 1.02, sz: 1.5, fold: 0.022, dz: -0.17 },
      { y: 0.09, r: 0.29, sx: 1.02, sz: 1.42, fold: 0.018, dz: -0.15 },
      { y: 0.22, r: 0.25, sx: 1.03, sz: 1.15, fold: 0.014, dz: -0.1 },
      { y: 0.42, r: 0.205, sx: 1.04, sz: 0.85, fold: 0.01, dz: -0.04 },
    ] : [
      { y: 0.0, r: 0.44, sx: 1.18, sz: 0.95, fold: 0.024, dz: 0.08 },
      { y: 0.08, r: 0.4, sx: 1.15, sz: 0.88, fold: 0.02, dz: 0.06 },
      { y: 0.18, r: 0.3, sx: 1.08, sz: 0.8, fold: 0.014, dz: 0.02 },
      { y: 0.3, r: 0.205, sx: 1.04, sz: 0.78, fold: 0.01, dz: 0.0 },
    ];
    add(shellGeometry([
      ...lowRings,
      { y: k(1.04), r: 0.172 * G, sx: 1.06, sz: 0.74, fold: 0.006 },
      { y: k(1.22), r: 0.19 * G, sx: 1.08, sz: 0.68, fold: 0.006 },
      { y: k(1.36), r: 0.205 * G, sx: 1.12, sz: 0.6, fold: 0.004 },
      { y: k(1.42), r: 0.16, sx: 1.1, sz: 0.62, fold: 0.002 },
      { y: k(1.475), r: 0.062, sx: 1, sz: 1, fold: 0 },
    ], { seed: o.seed, freq: 9, hemNoise: 0.03 }), robeMat);
  }

  // Mantle / shawl over the shoulders.
  if (o.mantle !== null || o.stripes) {
    const mm = o.stripes ? clothMat(0xffffff, { stripes: true }) : clothMat(o.mantle, { side: THREE.DoubleSide });
    const low = o.pose === 'stand' || o.pose === 'walk' ? (o.stripes ? 0.92 : 0.55) : shoulderY - 0.45;
    const sy = shoulderY;
    const arc = o.mantleArc === 'cape' ? [Math.PI * 0.7, Math.PI * 1.6] : o.mantleArc === 'right' ? [Math.PI * 0.62, Math.PI * 1.62] : [Math.PI * 0.68, Math.PI * 1.64];
    const diag = o.stripes ? 0 : (o.mantleArc === 'right' ? 0.16 : 0.1);
    const mg = shellGeometry([
      { y: low, r: 0.262 * G, sx: 1.05, sz: 0.88, fold: 0.024 },
      { y: low + (sy - low) * 0.35, r: 0.245 * G, sx: 1.07, sz: 0.8, fold: 0.018 },
      { y: low + (sy - low) * 0.7, r: 0.232 * G, sx: 1.1, sz: 0.72, fold: 0.011 },
      { y: sy - 0.03, r: 0.222 * G, sx: 1.13, sz: 0.66, fold: 0.006 },
      { y: sy + 0.02, r: 0.17, sx: 1.12, sz: 0.68, fold: 0.003 },
      { y: neckY + 0.01, r: 0.078, sx: 1.05, sz: 1.0, fold: 0 },
    ], { seed: o.seed + 11, freq: 7, arc, curl: 0.06, uvScale: [0.5, 1.0], hemNoise: 0.03,
      hem: diag ? (th) => -diag * Math.sin(th) + diag * 0.6 * Math.cos(th) : null });
    if (o.stripes) { // v coordinate runs along height; stripes texture expects 0..1 over the shawl
      const uvA = mg.attributes.uv;
      for (let i = 0; i < uvA.count; i++) uvA.setY(i, (uvA.getY(i) - low) / (neckY + 0.01 - low));
    }
    add(mg, mm);
  }

  // Head.
  const head = new THREE.Group();
  head.position.set(0, neckY, 0.0);
  body.add(head);
  add(new THREE.CylinderGeometry(0.043, 0.05, 0.12, 16, 1, true).translate(0, 0.04, 0), skinMat(o.skin), head);
  const skull = add(headGeometry(o.seed), faceMat(o.skin, o.beard), head);
  skull.position.set(0, 0.155, 0.012);
  if (o.head === 'hair' || o.head === 'hairshort') {
    const hm = hairMat(o.hair);
    const cap = new THREE.SphereGeometry(0.1, 32, 24, 0, Math.PI * 2, 0, Math.PI * 0.6);
    cap.rotateX(-0.5); cap.scale(0.95, 1.12, 1.04);
    add(cap, hm, head).position.set(0, 0.158, -0.004);
    if (o.head === 'hair') {
      // long hair: follows the skull ellipsoid, parts around the face, falls behind the shoulders
      add(shellGeometry([
        { y: -0.34, r: 0.09, sx: 1.2, sz: 0.4, fold: 0.012, dz: -0.075 },
        { y: -0.25, r: 0.098, sx: 1.17, sz: 0.47, fold: 0.012, dz: -0.06 },
        { y: -0.15, r: 0.104, sx: 1.12, sz: 0.6, fold: 0.01, dz: -0.04 },
        { y: -0.065, r: 0.104, sx: 1.05, sz: 0.88, fold: 0.007, dz: -0.012 },
        { y: 0.0, r: 0.1, sx: 0.98, sz: 1.06, fold: 0.004 },
        { y: 0.05, r: 0.088, sx: 1.0, sz: 1.1, fold: 0.003 },
        { y: 0.088, r: 0.055, sx: 1.0, sz: 1.1, fold: 0.0 },
      ], { seed: o.seed + 21, freq: 13, arc: [Math.PI * 0.8, Math.PI * 1.4], uvScale: [2, 3], hemNoise: 0.025 }), hm, head).position.set(0, 0.155, -0.004);
    }
    if (o.beard) {
      const bg = new THREE.SphereGeometry(0.07, 24, 16, Math.PI * 0.08, Math.PI * 0.84, Math.PI * 0.5, Math.PI * 0.42);
      bg.scale(1.0, 1.15, 0.9);
      add(bg, hairMat(new THREE.Color(o.hair).lerp(new THREE.Color(0x5a3e2a), 0.35).getHex()), head).position.set(0, 0.128, 0.034);
    }
  } else if (o.head === 'headcloth' || o.head === 'hood') {
    const cm = clothMat(o.headgear, { side: THREE.DoubleSide });
    add(shellGeometry([
      { y: -0.36, r: 0.15, sx: 1.25, sz: 0.62, fold: 0.016, dz: -0.08 },
      { y: -0.24, r: 0.17, sx: 1.22, sz: 0.66, fold: 0.014, dz: -0.05 },
      { y: -0.15, r: 0.165, sx: 1.18, sz: 0.7, fold: 0.012, dz: -0.03 },
      { y: -0.06, r: 0.135, sx: 1.08, sz: 0.88, fold: 0.01, dz: -0.012 },
      { y: 0.04, r: 0.119, sx: 1.0, sz: 1.0, fold: 0.007 },
      { y: 0.12, r: 0.112, sx: 1.0, sz: 1.02, fold: 0.004 },
      { y: 0.18, r: 0.085, sx: 1, sz: 1, fold: 0.002 },
      { y: 0.215, r: 0.02, sx: 1, sz: 1, fold: 0 },
    ], { seed: o.seed + 31, freq: 9, arc: [Math.PI * 0.74, Math.PI * 1.52], hemNoise: 0.03, hem: (th) => 0.06 * Math.sin(th) }), cm, head).position.set(0, 0.155, 0);
    if (o.head === 'headcloth') {
      const band = new THREE.TorusGeometry(0.128, 0.012, 8, 40); band.rotateX(Math.PI / 2); band.rotateX(-0.12);
      add(band, clothMat(o.band), head).position.set(0, 0.222, -0.006);
    }
    if (o.beard) {
      const bg = new THREE.SphereGeometry(0.075, 20, 12, Math.PI * 0.05, Math.PI * 0.9, Math.PI * 0.45, Math.PI * 0.5);
      bg.scale(1.05, 1.25, 0.95);
      add(bg, hairMat(o.hair), head).position.set(0, 0.125, 0.032);
    }
  } else if (o.head === 'turban') {
    const tm = clothMat(o.headgear);
    for (let i = 0; i < 4; i++) {
      const t = new THREE.TorusGeometry(0.098 - i * 0.008, 0.024, 10, 36);
      t.rotateX(Math.PI / 2); t.rotateZ((r() - 0.5) * 0.12);
      add(t, tm, head).position.set(0, 0.205 + i * 0.03, -0.01);
    }
    add(new THREE.SphereGeometry(0.085, 20, 12, 0, Math.PI * 2, 0, Math.PI / 2), tm, head).position.set(0, 0.29, -0.01);
    // dark hair below the turban and a beard
    const hm = hairMat(o.hair);
    add(new THREE.SphereGeometry(0.104, 24, 16, Math.PI * 0.7, Math.PI * 1.6, Math.PI * 0.35, Math.PI * 0.3), hm, head).position.set(0, 0.155, 0);
    if (o.beard) {
      const bg = new THREE.SphereGeometry(0.078, 20, 12, Math.PI * 0.05, Math.PI * 0.9, Math.PI * 0.45, Math.PI * 0.55);
      bg.scale(1.05, 1.35, 0.95);
      add(bg, hm, head).position.set(0, 0.12, 0.03);
    }
  }

  // Arms: shoulder -> elbow -> hand. Rest pose hangs along -Y.
  const arms = {};
  for (const side of ['l', 'r']) {
    const sgn = side === 'l' ? 1 : -1;
    const sh = new THREE.Group(); sh.position.set(sgn * shoulderX * G, shoulderY - 0.035, -0.01);
    body.add(sh);
    const sl = o.sleeve ?? o.robe;
    add(sleeveGeometry(0.3, 0.066 * G, 0.072 * G, o.seed + (side === 'l' ? 41 : 43)), clothMat(sl), sh);
    add(new THREE.SphereGeometry(0.068 * G, 16, 12), clothMat(sl), sh);
    const el = new THREE.Group(); el.position.set(0, -0.29, 0); sh.add(el);
    add(new THREE.SphereGeometry(0.07 * G, 14, 10), clothMat(sl), el);
    add(sleeveGeometry(0.25, 0.07 * G, 0.092 * G, o.seed + (side === 'l' ? 51 : 53), 0.01), clothMat(sl), el);
    const wr = new THREE.Group(); wr.position.set(0, -0.255, 0); el.add(wr);
    const hand = add(handGeometry(), skinMat(o.skin), wr);
    hand.scale.set(sgn, 1, 1);
    add(new THREE.CylinderGeometry(0.026, 0.03, 0.06, 10).translate(0, 0.01, 0), skinMat(o.skin), wr);
    arms[side] = { shoulder: sh, elbow: el, wrist: wr, sgn };
  }

  const base = { lean: 0, tilt: 0, headYaw: 0, headPitch: 0 };
  // Pose control. Angles in radians. pitch>0 swings the arm forward, roll>0 lifts it sideways.
  const pose = (p = {}) => {
    for (const side of ['l', 'r']) {
      const a = arms[side], q = p[side] || {};
      a.shoulder.rotation.set(-(q.pitch ?? 0.05), q.yaw ?? 0, a.sgn * (q.roll ?? 0.08), 'YXZ');
      a.elbow.rotation.set(-(q.elbow ?? 0.15), 0, 0);
      a.wrist.rotation.set(-(q.wristPitch ?? 0), q.wristYaw ?? 0, a.sgn * (q.wristRoll ?? 0));
    }
    head.rotation.set(p.headPitch ?? 0, p.headYaw ?? 0, p.headRoll ?? 0, 'YXZ');
    body.rotation.set(p.lean ?? 0, 0, p.tilt ?? 0);
    Object.assign(base, { lean: p.lean ?? 0, tilt: p.tilt ?? 0, headYaw: p.headYaw ?? 0, headPitch: p.headPitch ?? 0 });
  };
  pose(o.arms ? { ...o.arms } : {});

  // Idle motion: breathing sway and small head drift, deterministic per seed.
  const phase = r() * 100;
  root.userData = {
    arms, head, body, pose, base, seed: o.seed,
    idle(t, amt = 1) {
      body.rotation.x = base.lean + amt * 0.012 * Math.sin(t * 0.9 + phase);
      body.rotation.z = base.tilt + amt * 0.01 * Math.sin(t * 0.63 + phase * 1.7);
      head.rotation.y = base.headYaw + amt * 0.05 * Math.sin(t * 0.37 + phase * 0.3);
      head.rotation.x = base.headPitch + amt * 0.015 * Math.sin(t * 0.5 + phase * 0.7);
    },
  };
  return root;
}

// Palettes for crowds.
export const PALETTES = {
  pharisee: { robe: [0xe9e2d4, 0xe2dacb, 0xd9d0c0], headgear: [0xf0ebe0, 0xe8e0d0], mantle: [0x1c2230] },
  people: { robe: [0x7a5a3c, 0x8b6b48, 0x5e4a38, 0x9a7b56, 0x6b5844, 0x4d4a48, 0x8a7560, 0x6e3f2c, 0x54616b], mantle: [0x5a3d28, 0x3f3a36, 0x7a6248, 0x2e3a44, 0x6a4a30, null, null], headgear: [0xcfc2a8, 0xb9a88a, 0x8f7a60, 0xd8ccb4] },
  disciples: { robe: [0x8a6d4e, 0x6f5a46, 0x9c8462, 0x5d4c3c, 0x7d6a58, 0xa38d70], mantle: [0x5a4030, 0x45403a, 0x6e5640, 0x3a3f46, null] },
};

export function crowdFigure(kind, seed, extra = {}) {
  const r = rng(seed * 7 + 3);
  const P = PALETTES[kind] || PALETTES.people;
  if (kind === 'pharisee') {
    return makeFigure({ seed, height: r.range(1.68, 1.84), robe: r.pick(P.robe), head: r() < 0.7 ? 'turban' : 'headcloth', headgear: r.pick(P.headgear),
      stripes: true, hair: r.pick([0x1e1610, 0x2a2018, 0x4a4038, 0x6a6058]), skin: r.pick([0x9c6e50, 0xa8785a, 0x8f6448]), girth: r.range(0.98, 1.12), ...extra });
  }
  return makeFigure({ seed, height: r.range(1.62, 1.82), robe: r.pick(P.robe), mantle: r.pick(P.mantle), head: r() < 0.65 ? 'headcloth' : 'hair',
    headgear: r.pick(PALETTES.people.headgear), hair: r.pick([0x1e1610, 0x2a2018, 0x3a2a1e]), skin: r.pick([0x9c6e50, 0xa8785a, 0x8f6448, 0xb0805e]),
    girth: r.range(0.94, 1.08), beard: r() < 0.8, sash: r() < 0.4 ? r.pick([0x5a3d28, 0x8a6a40, 0x3a3030]) : null, ...extra });
}

// Jesus: off-white tunic, warm beige-brown mantle over the shoulder, long dark hair, beard.
export function jesusFigure(extra = {}) {
  return makeFigure({ seed: 33, height: 1.8, robe: 0xe6dccb, mantle: 0x9b6f4a, mantleArc: 'right', head: 'hair', hair: 0x2a1a10, skin: 0xa47456, beard: true, sash: 0x7a5636, ...extra });
}
