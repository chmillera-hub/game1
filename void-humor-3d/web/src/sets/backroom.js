// SET: BACKROOM (SETS.BACKROOM) — the back of the creator's mind (bonus scene).
// A dim, cavernous, cozy-creepy back room: smooth warm floorboards, walls dissolving into darkness, a far cool
// "screen of consciousness" glow (+Z, off-screen), soft dusty light shafts, a bare warm bulb on a cord, the little
// brass TIME-OUT cage and a janitor's corner that can be smashed slapstick-style.
// Full API (opts / anchors / props / layout / recipes): docs/sets/backroom.md.  Lab: web/src/labs/backroom.js.
// Every frame is a pure function of (t, opts): no state is carried between update() calls.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { CTX, EYE_LIGHT } from '../core/context.js';
import { glowTexture, contactShadow, GLOBAL } from '../core/materials.js';
import { Particles, CELL } from '../core/particles.js';
import { clamp, lerp, smooth, ease, fbm1, noise1, rng, DEG } from '../core/util.js';

const TAU = Math.PI * 2;
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const sm = (a, b, x) => smooth((x - a) / (b - a));
const UP = V(0, 1, 0);
const qAx = (ax, a) => new THREE.Quaternion().setFromAxisAngle(ax, a);
const _m4 = new THREE.Matrix4();
const ni = (g) => (g.index ? g.toNonIndexed() : g);   // RoundedBoxGeometry is already non-indexed
const merge = (arr) => (arr.every((g) => g.index) ? mergeGeometries(arr) : mergeGeometries(arr.map(ni)));
function qBasis(up, fwd) {            // quaternion mapping local +Y -> up and local +Z -> fwd (orthogonalised)
  const y = up.clone().normalize();
  let z = fwd.clone().addScaledVector(y, -fwd.dot(y));
  if (z.lengthSq() < 1e-8) { z = Math.abs(y.x) < 0.9 ? V(1, 0, 0) : V(0, 0, 1); z.addScaledVector(y, -z.dot(y)); }
  z.normalize();
  const x = new THREE.Vector3().crossVectors(y, z);
  return new THREE.Quaternion().setFromRotationMatrix(_m4.makeBasis(x, y, z));
}
const toV = (a) => (a instanceof THREE.Vector3 ? a.clone() : V(a[0], a[1], a[2]));
const yawDir = (yaw) => V(Math.sin(yaw), 0, Math.cos(yaw));

// ------------------------------------------------------------------------------------------------ layout
// The action runs on one diagonal: FEAR/cage (front-left) -> VOID -> MAGICIAN (behind it) -> janitor corner
// (back-right). The Void faces the cage at yaw -45 deg (3/4 to a camera on +Z), so its backward donkey-kick sends
// the magician straight along BACK into the corner where the back wall (z = -5) meets the right wall (x = 4.8).
const S2 = Math.SQRT1_2;
const FWD = V(-S2, 0, S2), BACK = V(S2, 0, -S2);
const VOID_SPOT = V(0.3, 0, -0.5);
const CAGE_POS = V(-1.6, 0, 0.02), CAGE_YAW = 60 * DEG;        // door faces the Void / fearOutside
const FEAR_OUT = VOID_SPOT.clone().addScaledVector(FWD, 1.45);   // (-0.73, 0, 0.53)
const LURK = VOID_SPOT.clone().addScaledVector(BACK, 1.6);       // (1.43, 0, -1.63)
const CRASH = LURK.clone().addScaledVector(BACK, 3.6);           // (3.98, 0, -4.18)
const BACK_Z = -5.0, RIGHT_X = 4.8, LEFT_X = -8.5, FRONT_Z = 24;
export const LAYOUT = {
  voidSpot: VOID_SPOT, voidYaw: -Math.PI / 4, cage: CAGE_POS, cageYaw: CAGE_YAW, fearOutside: FEAR_OUT,
  lurkSpot: LURK, crashSpot: CRASH, backZ: BACK_Z, rightX: RIGHT_X, leftX: LEFT_X, screenZ: FRONT_Z,
  fwd: FWD, back: BACK,
};
// cage dimensions (local: +Z = door centre, +X = hinge side)
const CAGE = { R: 0.45, base: 0.04, shoulder: 0.79, domeH: 0.2, n: 20, doorHalf: 36 * DEG, doorTop: 0.755, doorBot: 0.075,
  doorMax: 112 * DEG, latchY: 0.42, tagTh: -62 * DEG };
const FOG_COL = new THREE.Color(0x0b0a17);

// ------------------------------------------------------------------------------------------------ canvases
function cv(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
function ctex(c, { srgb = true, repeat = false } = {}) {
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}
const rgba = (r, g, b, a = 1) => `rgba(${r | 0},${g | 0},${b | 0},${a})`;

function floorTexture() {           // 4 m x 4 m tile: 12 wide boards (0.33 m) running along v (world Z), low contrast
  const S = 1024, c = cv(S, S), g = c.getContext('2d'), r = rng(77);
  const bw = S / 12;
  for (let i = 0; i < 12; i++) {
    let y0 = -r() * S * 0.6;
    while (y0 < S) {
      const len = S * (0.42 + r() * 0.4), tone = 0.9 + r() * 0.18, hue = r() * 10 - 5;
      const base = [108 * tone + hue, 82 * tone, 66 * tone - hue * 0.5];
      const gr = g.createLinearGradient(0, y0, 0, y0 + len);
      gr.addColorStop(0, rgba(base[0] * 0.97, base[1] * 0.97, base[2] * 0.97));
      gr.addColorStop(0.35 + r() * 0.3, rgba(base[0] * 1.04, base[1] * 1.03, base[2] * 1.02));
      gr.addColorStop(1, rgba(base[0] * 0.95, base[1] * 0.95, base[2] * 0.96));
      g.fillStyle = gr; g.fillRect(i * bw, y0, bw, len);
      for (let k = 0; k < 4; k++) {   // soft long grain streaks (very low contrast)
        g.fillStyle = r() < 0.5 ? 'rgba(255,225,200,0.035)' : 'rgba(40,20,20,0.04)';
        g.fillRect(i * bw + 4 + r() * (bw - 12), y0, 2 + r() * 5, len);
      }
      g.fillStyle = 'rgba(28,16,18,0.5)'; g.fillRect(i * bw, y0, bw, 3);      // butt joint
      y0 += len;
    }
    g.fillStyle = 'rgba(26,14,18,0.55)'; g.fillRect(i * bw, 0, 3, S);         // long seam
    g.fillStyle = 'rgba(255,220,200,0.05)'; g.fillRect(i * bw + 3, 0, 2, S);   // bevel catch
  }
  const t = ctex(c, { repeat: true }); t.anisotropy = 2; return t;
}

function plasterTexture() {         // 3 m tile, soft water stains (low contrast)
  const S = 512, c = cv(S, S), g = c.getContext('2d'), r = rng(19);
  g.fillStyle = '#8c8894'; g.fillRect(0, 0, S, S);
  for (let i = 0; i < 46; i++) {
    const x = r() * S, y = r() * S, rr = 30 + r() * 120, dark = r() < 0.6;
    for (const ox of [-S, 0, S]) for (const oy of [-S, 0, S]) {
      const gr = g.createRadialGradient(x + ox, y + oy, 0, x + ox, y + oy, rr);
      gr.addColorStop(0, dark ? 'rgba(60,45,55,0.12)' : 'rgba(170,150,160,0.10)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = gr; g.fillRect(x + ox - rr, y + oy - rr, rr * 2, rr * 2);
    }
  }
  return ctex(c, { repeat: true });
}

function rustTextures() {           // brass bars: x = along the bar (0 = bottom), y = around. Rust gathers low.
  const W = 512, H = 64, c = cv(W, H), g = c.getContext('2d'), cr = cv(W, H), gr2 = cr.getContext('2d'), r = rng(31);
  g.fillStyle = '#eec377'; g.fillRect(0, 0, W, H);
  gr2.fillStyle = '#6a6a6a'; gr2.fillRect(0, 0, W, H);
  const lg = g.createLinearGradient(0, 0, W, 0);
  lg.addColorStop(0, 'rgba(84,50,24,0.7)'); lg.addColorStop(0.18, 'rgba(84,50,24,0.3)'); lg.addColorStop(0.6, 'rgba(80,50,26,0.04)'); lg.addColorStop(1, 'rgba(255,230,180,0.08)');
  g.fillStyle = lg; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 110; i++) {
    const x = Math.pow(r(), 1.7) * W, y = r() * H, rr = 3 + r() * 14, a = 0.4 + r() * 0.4;
    const col = [128 + r() * 40, 58 + r() * 24, 22 + r() * 12];
    for (const oy of [-H, 0, H]) {
      const rg = g.createRadialGradient(x, y + oy, 0, x, y + oy, rr);
      rg.addColorStop(0, rgba(col[0], col[1], col[2], a)); rg.addColorStop(1, rgba(col[0], col[1], col[2], 0));
      g.fillStyle = rg; g.fillRect(x - rr, y + oy - rr, rr * 2, rr * 2);
      const rg2 = gr2.createRadialGradient(x, y + oy, 0, x, y + oy, rr);
      rg2.addColorStop(0, `rgba(235,235,235,${a})`); rg2.addColorStop(1, 'rgba(235,235,235,0)');
      gr2.fillStyle = rg2; gr2.fillRect(x - rr, y + oy - rr, rr * 2, rr * 2);
    }
  }
  const map = ctex(c, { repeat: true }), rough = ctex(cr, { srgb: false, repeat: true });
  return { map, rough };
}

function galvTexture() {            // galvanized spangle: soft crystalline patches
  const S = 256, c = cv(S, S), g = c.getContext('2d'), r = rng(57);
  g.fillStyle = '#c4cacd'; g.fillRect(0, 0, S, S);
  for (let i = 0; i < 90; i++) {
    const x = r() * S, y = r() * S, rr = 6 + r() * 22, l = r() < 0.5 ? 255 : 60, a = 0.05 + r() * 0.07;
    g.fillStyle = `rgba(${l},${l},${l + (l > 100 ? 0 : 10)},${a})`;
    g.beginPath();
    const k = 5 + Math.floor(r() * 3);
    for (let j = 0; j < k; j++) { const an = j / k * TAU + r() * 0.5, d = rr * (0.6 + r() * 0.5); j ? g.lineTo(x + Math.cos(an) * d, y + Math.sin(an) * d) : g.moveTo(x + Math.cos(an) * d, y + Math.sin(an) * d); }
    g.fill();
  }
  for (let i = 0; i < 14; i++) { const x = r() * S, y = r() * S, rr = 10 + r() * 30; const gr = g.createRadialGradient(x, y, 0, x, y, rr); gr.addColorStop(0, 'rgba(70,64,58,0.14)'); gr.addColorStop(1, 'rgba(70,64,58,0)'); g.fillStyle = gr; g.fillRect(x - rr, y - rr, rr * 2, rr * 2); }
  return ctex(c, { repeat: true });
}

// hand-lettered stroke font (marker look) for the TIME-OUT tag
const GLYPHS = {
  T: { w: 0.62, s: [[[0, 1], [0.62, 1]], [[0.31, 1], [0.31, 0]]] },
  I: { w: 0.16, s: [[[0.08, 1], [0.08, 0]]] },
  M: { w: 0.74, s: [[[0, 0], [0, 1], [0.37, 0.36], [0.74, 1], [0.74, 0]]] },
  E: { w: 0.52, s: [[[0.52, 1], [0, 1], [0, 0], [0.52, 0]], [[0, 0.52], [0.42, 0.52]]] },
  '-': { w: 0.36, s: [[[0.04, 0.48], [0.32, 0.48]]] },
  O: { w: 0.7, s: [Array.from({ length: 25 }, (_, i) => [0.35 + 0.35 * Math.sin(i / 24 * TAU), 0.5 + 0.5 * Math.cos(i / 24 * TAU)])] },
  U: { w: 0.6, s: [[[0, 1], [0, 0.34], ...Array.from({ length: 9 }, (_, i) => [0.3 - 0.3 * Math.cos(i / 8 * Math.PI), 0.34 - 0.34 * Math.sin(i / 8 * Math.PI)]), [0.6, 0.34], [0.6, 1]]] },
};
function drawStrokeText(g, text, x0, y0, h, gap, r, wob = 0.03) {
  let x = x0;
  for (const ch of text) {
    const G = GLYPHS[ch]; if (!G) { x += h * 0.4; continue; }
    const tilt = (r() - 0.5) * 0.08, dy = (r() - 0.5) * h * 0.06;
    for (const st of G.s) {
      g.beginPath();
      st.forEach(([u, v], i) => {
        const px = x + (u + (v - 0.5) * tilt) * h + (r() - 0.5) * wob * h, py = y0 + dy - v * h + (r() - 0.5) * wob * h;
        i ? g.lineTo(px, py) : g.moveTo(px, py);
      });
      g.stroke();
    }
    x += (G.w + gap) * h;
  }
  return x;
}
function textWidth(text, h, gap) { let w = 0; for (const ch of text) w += ((GLYPHS[ch]?.w ?? 0.4) + gap) * h; return w - gap * h; }

function tagTextures() {           // manila tag, clipped top corners, reinforced hole, marker "TIME-OUT"
  const W = 512, H = 256, r = rng(4);
  const shape = (g) => { g.beginPath(); g.moveTo(70, 6); g.lineTo(W - 70, 6); g.lineTo(W - 6, 70); g.lineTo(W - 6, H - 6); g.lineTo(6, H - 6); g.lineTo(6, 70); g.closePath(); };
  const paper = (g) => {
    g.save(); shape(g); g.clip();
    g.fillStyle = '#ead8ae'; g.fillRect(0, 0, W, H);
    const vg = g.createRadialGradient(W / 2, H / 2, 40, W / 2, H / 2, W * 0.62); vg.addColorStop(0, 'rgba(255,250,235,0.25)'); vg.addColorStop(1, 'rgba(120,90,50,0.35)');
    g.fillStyle = vg; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 18; i++) { const x = r() * W, y = r() * H, rr = 10 + r() * 40; const gr = g.createRadialGradient(x, y, 0, x, y, rr); gr.addColorStop(0, 'rgba(150,110,60,0.10)'); gr.addColorStop(1, 'rgba(150,110,60,0)'); g.fillStyle = gr; g.fillRect(x - rr, y - rr, rr * 2, rr * 2); }
    g.restore();
    // reinforcement ring + hole at top centre
    g.fillStyle = '#c9b48a'; g.beginPath(); g.arc(W / 2, 34, 22, 0, TAU); g.fill();
    g.globalCompositeOperation = 'destination-out'; g.beginPath(); g.arc(W / 2, 34, 9, 0, TAU); g.fill(); g.globalCompositeOperation = 'source-over';
  };
  const cf = cv(W, H), gf = cf.getContext('2d'); paper(gf);
  gf.strokeStyle = '#3a1f1a'; gf.lineCap = 'round'; gf.lineJoin = 'round'; gf.lineWidth = 15;
  const th = 84, gap = 0.2, tw = textWidth('TIME-OUT', th, gap);
  gf.save(); gf.translate(W / 2, 160); gf.rotate(-0.035);
  drawStrokeText(gf, 'TIME-OUT', -tw / 2, th / 2, th, gap, r, 0.035);
  gf.lineWidth = 6; gf.beginPath(); gf.moveTo(-tw / 2 + 6, th / 2 + 20); gf.quadraticCurveTo(0, th / 2 + 27, tw / 2 - 4, th / 2 + 14); gf.stroke();
  gf.restore();
  const cb = cv(W, H), gb = cb.getContext('2d'); paper(gb);
  return { front: ctex(cf), back: ctex(cb) };
}

function signTexture() {           // generic yellow wet-floor sign: CAUTION band, slipping figure in a triangle, WET FLOOR
  const W = 480, H = 1024, c = cv(W, H), g = c.getContext('2d');
  g.fillStyle = '#f3c419'; g.fillRect(0, 0, W, H);
  const sh = g.createLinearGradient(0, 0, 0, H); sh.addColorStop(0, 'rgba(255,255,230,0.12)'); sh.addColorStop(1, 'rgba(120,70,0,0.18)');
  g.fillStyle = sh; g.fillRect(0, 0, W, H);
  g.fillStyle = '#17130e';
  g.fillRect(36, 150, W - 72, 92);
  g.fillStyle = '#f3c419'; g.font = '900 70px Inter, "DejaVu Sans", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('CAUTION', W / 2, 198);
  // warning triangle
  const cx = W / 2, ty = 300, by = 640, hw = 190;
  g.lineJoin = 'round'; g.strokeStyle = '#17130e'; g.lineWidth = 30;
  g.beginPath(); g.moveTo(cx, ty); g.lineTo(cx + hw, by); g.lineTo(cx - hw, by); g.closePath(); g.stroke();
  // slipping figure (original stick pictogram): leaning back, one foot kicked up, arms flung
  g.fillStyle = '#17130e'; g.strokeStyle = '#17130e'; g.lineCap = 'round'; g.lineWidth = 26;
  g.beginPath(); g.arc(cx + 46, 432, 25, 0, TAU); g.fill();                    // head
  const line = (pts) => { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(cx + x, y) : g.moveTo(cx + x, y))); g.stroke(); };
  line([[30, 470], [-10, 548]]);                                                 // torso, leaning back
  line([[22, 486], [78, 470], [104, 432]]);                                      // arm flung up
  line([[18, 490], [-30, 476], [-62, 446]]);                                     // other arm
  line([[-10, 548], [44, 566], [88, 540]]);                                      // leg kicked up
  line([[-10, 548], [-34, 602], [-6, 612]]);                                     // standing leg slipping
  g.lineWidth = 12; line([[-92, 618], [60, 618]]);                               // floor line
  for (const [x, y] of [[-70, 590], [-100, 560], [64, 596]]) { g.beginPath(); g.ellipse(cx + x, y, 7, 11, 0.3, 0, TAU); g.fill(); }   // drops
  g.font = '900 86px Inter, "DejaVu Sans", sans-serif'; g.fillStyle = '#17130e';
  g.fillText('WET', W / 2, 748); g.fillText('FLOOR', W / 2, 846);
  return ctex(c);
}

function softRectTexture() {        // the far screen-of-consciousness glow (soft rounded rectangle)
  const W = 256, H = 160, c = cv(W, H), g = c.getContext('2d');
  g.filter = 'blur(14px)'; g.fillStyle = '#fff';
  g.beginPath(); g.roundRect(46, 40, W - 92, H - 80, 18); g.fill();
  g.filter = 'blur(34px)'; g.globalAlpha = 0.6; g.fillRect(24, 22, W - 48, H - 44);
  return ctex(c);
}

// ------------------------------------------------------------------------------------------------ env map (metal reflections)
function makeEnv() {
  const renderer = CTX.renderer;
  if (!renderer) return null;
  const es = new THREE.Scene();
  es.background = new THREE.Color(0x0d0b16);
  const add = (geo, col, pos, look) => { const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: col, side: THREE.DoubleSide })); m.position.copy(pos); if (look) m.lookAt(look); es.add(m); };
  add(new THREE.PlaneGeometry(14, 6), new THREE.Color(0.55, 0.68, 1.0).multiplyScalar(1.4), V(0, 3, 12), V(0, 1, 0));    // the far screen
  add(new THREE.SphereGeometry(0.7, 16, 8), new THREE.Color(5, 3, 1.3), V(-2.5, 4.5, 1.5));                              // the bulb
  add(new THREE.SphereGeometry(1.2, 16, 8), new THREE.Color(0.9, 0.6, 2.2), V(1.5, 3, -3));                              // void glow
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshBasicMaterial({ color: 0x2a1c1e })); fl.rotation.x = -Math.PI / 2; fl.position.y = -1.2; es.add(fl);
  const wall = new THREE.Mesh(new THREE.CylinderGeometry(14, 14, 8, 24, 1, true), new THREE.MeshBasicMaterial({ color: 0x1c1620, side: THREE.BackSide })); wall.position.y = 2.8; es.add(wall);
  const pm = new THREE.PMREMGenerator(renderer);
  const rt = pm.fromScene(es, 0.04);
  pm.dispose();
  return rt.texture;
}

// ------------------------------------------------------------------------------------------------ materials
function makeMaterials(env) {
  const rust = rustTextures();
  const galv = galvTexture();
  const std = (o) => new THREE.MeshStandardMaterial(o);
  const lam = (o) => new THREE.MeshLambertMaterial(o);
  const M = {
    floor: std({ color: 0xffffff, map: floorTexture(), roughness: 0.4, metalness: 0.0 }),
    // big matte surfaces use Lambert (much cheaper per pixel on SwiftShader with several lights)
    wall: lam({ color: 0x8e95ad, map: plasterTexture(), vertexColors: true, transparent: true }),
    wains: lam({ color: 0x4e3a2e, vertexColors: true, transparent: true }),
    pipe: std({ color: 0x6a5f62, roughness: 0.42, metalness: 0.75, vertexColors: true, transparent: true, envMap: env, envMapIntensity: 0.7 }),
    cardboard: lam({ color: 0x7e6349, transparent: true }),
    tape: lam({ color: 0xb49c76, transparent: true }),
    sheet: lam({ color: 0xa8a3b8, transparent: true }),
    doorway: new THREE.MeshBasicMaterial({ color: 0x030307, transparent: true }),
    brass: std({ color: 0xfff2d8, map: rust.map, roughnessMap: rust.rough, roughness: 0.62, metalness: 0.85, envMap: env, envMapIntensity: 1.0 }),
    brassBright: std({ color: 0xf2c878, roughness: 0.25, metalness: 0.95, envMap: env, envMapIntensity: 1.6, emissive: 0x2a1604 }),
    iron: std({ color: 0x3e3940, roughness: 0.55, metalness: 0.65, envMap: env, envMapIntensity: 0.7 }),
    galv: std({ color: 0xd4dade, map: galv, roughness: 0.4, metalness: 0.55, vertexColors: true, envMap: env, envMapIntensity: 1.3 }),
    galvDark: std({ color: 0x9aa1a6, roughness: 0.42, metalness: 0.6, envMap: env, envMapIntensity: 1.1 }),
    wood: std({ color: 0xa06d42, roughness: 0.6 }),
    woodPale: std({ color: 0xb08a62, roughness: 0.58 }),
    red: std({ color: 0xa8382e, roughness: 0.45 }),
    rubber: std({ color: 0x1c1a1c, roughness: 0.8 }),
    straw: std({ color: 0xffffff, roughness: 0.85, vertexColors: true }),
    bristle: std({ color: 0x2c2726, roughness: 0.9 }),
    plasticW: std({ color: 0xeae4d8, roughness: 0.32 }),
    sprayA: std({ color: 0xffffff, roughness: 0.28, vertexColors: true }),
    sprayB: std({ color: 0xffffff, roughness: 0.28, vertexColors: true }),
    label: std({ color: 0xe8e0cc, roughness: 0.7 }),
    sign: std({ color: 0xffffff, map: signTexture(), roughness: 0.42 }),
    signEdge: std({ color: 0xe0ac10, roughness: 0.45 }),
    cord: std({ color: 0x1a1618, roughness: 0.7 }),
    socket: std({ color: 0x5a4632, roughness: 0.4, metalness: 0.8, envMap: env }),
    puddle: std({ color: 0x40607e, roughness: 0.05, metalness: 0.35, envMap: env, envMapIntensity: 2.6, transparent: true, opacity: 0.62, depthWrite: false }),
    mop: std({ color: 0xe6dfcc, roughness: 0.92 }),
    mopCotton: std({ color: 0xc8bfa8, roughness: 0.95 }),
  };
  M.rag = [0x6e9896, 0xd8ccae, 0xb88680, 0x7a88a2, 0x9b8b6f].map((c) => std({ color: c, roughness: 0.96 }));
  M.fadeable = [M.wall, M.wains, M.pipe, M.cardboard, M.tape, M.sheet, M.doorway];
  return M;
}

// mop strands bend toward gravity (local-space uniform) and are pushed out of an optional capsule collider and the floor
function droopMaterial(base) {
  const U = { uGravL: { value: V(0, -1, 0) }, uDroop: { value: 1 }, uFloorY: { value: 0 }, uWig: { value: 0 },
    uColA: { value: V() }, uColB: { value: V() }, uColR: { value: 0 } };
  base.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>
        attribute float aS; attribute vec3 aRoot; attribute vec3 aC; attribute vec3 aW;
        uniform vec3 uGravL, uColA, uColB; uniform float uDroop, uFloorY, uColR, uWig;`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        vec3 mopO = transformed - aC;
        vec3 mopC;
        {
          vec3 d = aC - aRoot; float L = length(d);
          vec3 dn = d / max(L, 1e-4);
          float w = uDroop * smoothstep(0.0, 0.75, aS) * 0.94;
          vec3 nd = normalize(mix(dn, uGravL, w) + vec3(1e-4));
          mopC = mix(aRoot + nd * L, aW, uWig);
          transformed = mopC + mopO;
        }`)
      .replace('#include <project_vertex>', `
        // collisions are resolved on the strand CENTRE so cross-sections stay round
        vec4 cw = modelMatrix * vec4(mopC, 1.0);
        vec3 push = vec3(0.0);
        if (uColR > 0.0) {
          vec3 ab = uColB - uColA; float h = clamp(dot(cw.xyz - uColA, ab) / max(dot(ab, ab), 1e-6), 0.0, 1.0);
          vec3 cp = uColA + ab * h; vec3 dv = cw.xyz - cp; float dl = length(dv);
          if (dl < uColR) push = cp + dv / max(dl, 1e-4) * uColR - cw.xyz;
        }
        float fl = uFloorY + 0.014 + 0.01 * aS;
        push.y += max(0.0, fl - (cw.y + push.y));
        vec4 wpos = modelMatrix * vec4(transformed, 1.0);
        wpos.xyz += push;
        vec4 mvPosition = viewMatrix * wpos;
        gl_Position = projectionMatrix * mvPosition;`);
  };
  base.customProgramCacheKey = () => 'backroomMopDroop';
  base.userData.droop = U;
  return base;
}

// ------------------------------------------------------------------------------------------------ geometry helpers
function vcolFade(geo, f) {         // vertex colour by world-ish y of the geometry (after translation)
  const p = geo.attributes.position, c = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { const k = f(p.getX(i), p.getY(i), p.getZ(i)); c[i * 3] = c[i * 3 + 1] = c[i * 3 + 2] = k; }
  geo.setAttribute('color', new THREE.BufferAttribute(c, 3));
  return geo;
}
const wallFade = (x, y) => 1 - smooth((y - 0.8) / 5.2) * 0.97;
function planarUV(geo, ax, ay, scale) {   // metres-based UVs from two position axes
  const p = geo.attributes.position, uv = geo.attributes.uv;
  for (let i = 0; i < p.count; i++) uv.setXY(i, p.getComponent(i, ax) / scale, p.getComponent(i, ay) / scale);
  return geo;
}
// cutaway helper: drop triangles whose normal points along `dir` (faces turned toward the outside of the room),
// so cameras placed beyond the right/back walls see straight into the set (walls are single-sided planes).
function dropFaces(geo, dir, cos = 0.7) {
  const g = ni(geo), p = g.attributes.position, keep = [];
  const a = V(), b = V(), c = V(), n = V();
  for (let i = 0; i < p.count; i += 3) {
    a.fromBufferAttribute(p, i); b.fromBufferAttribute(p, i + 1); c.fromBufferAttribute(p, i + 2);
    n.subVectors(c, b).cross(V().subVectors(a, b)).normalize();
    if (n.dot(dir) < cos) keep.push(i, i + 1, i + 2);
  }
  const out = new THREE.BufferGeometry();
  for (const k of Object.keys(g.attributes)) {
    const at = g.attributes[k], arr = new at.array.constructor(keep.length * at.itemSize);
    keep.forEach((vi, j) => { for (let q = 0; q < at.itemSize; q++) arr[j * at.itemSize + q] = at.array[vi * at.itemSize + q]; });
    out.setAttribute(k, new THREE.BufferAttribute(arr, at.itemSize));
  }
  return out;
}
function tubeGeo(points, radius, segs = 24, radial = 6, closed = false) {
  const curve = new THREE.CatmullRomCurve3(points.map(toV), closed, 'centripetal');
  return new THREE.TubeGeometry(curve, segs, radius, radial, closed);
}
const cagePt = (th, y, R = CAGE.R) => V(R * Math.sin(th), y, R * Math.cos(th));
function arcPts(th0, th1, y, n, R = CAGE.R) { const a = []; for (let i = 0; i <= n; i++) a.push(cagePt(lerp(th0, th1, i / n), y, R)); return a; }
function shiftUV(geo, du, dv) { const uv = geo.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) + du, uv.getY(i) + dv); return geo; }

// ------------------------------------------------------------------------------------------------ ROOM
function buildRoom(M) {
  const g = new THREE.Group(); g.name = 'backroom.room';
  // floor
  const fg = new THREE.PlaneGeometry(46, 46); fg.rotateX(-Math.PI / 2);
  planarUV(fg, 0, 2, -4); // 4 m tile, boards along Z
  const floor = new THREE.Mesh(fg, M.floor); floor.position.set(-2, 0, 7); floor.receiveShadow = true; g.add(floor);
  // walls (vertex-colour fade to darkness upward)
  const H = 9;
  const mkWall = (w, cx, cz, rotY) => {
    const geo = new THREE.PlaneGeometry(w, H, 1, 14); geo.translate(0, H / 2, 0);
    planarUV(geo, 0, 1, 3); vcolFade(geo, wallFade);
    const m = new THREE.Mesh(geo, M.wall); m.rotation.y = rotY; m.position.set(cx, 0, cz); m.receiveShadow = true; g.add(m); return m;
  };
  mkWall(RIGHT_X - LEFT_X, (RIGHT_X + LEFT_X) / 2, BACK_Z, 0);
  mkWall(FRONT_Z - BACK_Z, RIGHT_X, (FRONT_Z + BACK_Z) / 2, -Math.PI / 2);
  mkWall(FRONT_Z - BACK_Z, LEFT_X, (FRONT_Z + BACK_Z) / 2, Math.PI / 2);
  // wainscot: panel band, stiles, chair rail, baseboard (back wall + right wall), with a gap for the doorway
  const DOOR_X = -5.6, DOOR_W = 1.25, DOOR_H = 2.35;
  const wg = [];
  const runs = [[LEFT_X, DOOR_X - DOOR_W / 2 - 0.08, 'b'], [DOOR_X + DOOR_W / 2 + 0.08, RIGHT_X, 'b'], [BACK_Z, 9, 'r']];
  for (const [a, b, side] of runs) {
    const len = b - a, mid = (a + b) / 2;
    const parts = [[len, 1.0, 0.03, 0.5, 0.015], [len, 0.055, 0.06, 1.02, 0.03], [len, 0.15, 0.045, 0.075, 0.022]];
    for (let s = a + 0.6; s < b - 0.3; s += 1.25) parts.push([0.07, 0.86, 0.05, 0.5, 0.025, s]);
    for (const [w, h, d, y, off, at] of parts) {
      const bx = new THREE.BoxGeometry(side === 'b' ? w : d, h, side === 'b' ? d : w);
      const c = at ?? mid;
      if (side === 'b') bx.translate(c, y, BACK_Z + off); else bx.translate(RIGHT_X - off, y, c);
      wg.push(dropFaces(bx, side === 'b' ? V(0, 0, -1) : V(1, 0, 0)));
    }
  }
  const wgeo = vcolFade(merge(wg), (x, y) => 0.9 + 0.1 * (y > 0.98 ? 1 : 0));
  const wains = new THREE.Mesh(wgeo, M.wains); wains.receiveShadow = true; g.add(wains);
  // pipes along the back wall + up the corner (industrial, cozy-creepy)
  const pg = [];
  const p1 = new THREE.CylinderGeometry(0.055, 0.055, RIGHT_X - LEFT_X, 14); p1.rotateZ(Math.PI / 2); p1.translate((RIGHT_X + LEFT_X) / 2 - 0.12, 2.62, BACK_Z + 0.16); pg.push(p1);
  const p2 = new THREE.CylinderGeometry(0.034, 0.034, RIGHT_X - LEFT_X, 10); p2.rotateZ(Math.PI / 2); p2.translate((RIGHT_X + LEFT_X) / 2, 2.86, BACK_Z + 0.12); pg.push(p2);
  const p3 = new THREE.CylinderGeometry(0.06, 0.06, H, 14); p3.translate(RIGHT_X - 0.16, H / 2, BACK_Z + 0.42); pg.push(p3);
  const el = new THREE.SphereGeometry(0.075, 14, 10); el.translate(RIGHT_X - 0.16, 2.62, BACK_Z + 0.16); pg.push(el);
  const jn = new THREE.CylinderGeometry(0.04, 0.04, 0.3, 10); jn.rotateX(Math.PI / 2); jn.translate(RIGHT_X - 0.16, 2.62, BACK_Z + 0.3); pg.push(jn);
  for (let x = LEFT_X + 0.8; x < RIGHT_X - 0.4; x += 1.6) {
    const b1 = new THREE.BoxGeometry(0.05, 0.36, 0.2); b1.translate(x, 2.74, BACK_Z + 0.1); pg.push(b1);
    const cl = new THREE.TorusGeometry(0.062, 0.012, 6, 16); cl.rotateY(Math.PI / 2); cl.translate(x, 2.62, BACK_Z + 0.16); pg.push(cl);
  }
  for (const y of [1.3, 3.4]) { const b = new THREE.BoxGeometry(0.2, 0.05, 0.05); b.translate(RIGHT_X - 0.08, y, BACK_Z + 0.42); pg.push(b); }
  const pipes = new THREE.Mesh(vcolFade(merge(pg), (x, y) => 1 - smooth((y - 2.5) / 4) * 0.9), M.pipe); g.add(pipes);
  // doorway into deeper darkness (back-left) with a rounded-top trim
  const sh = new THREE.Shape(); const dw = DOOR_W / 2;
  sh.moveTo(-dw, 0); sh.lineTo(-dw, DOOR_H - dw); sh.absarc(0, DOOR_H - dw, dw, Math.PI, 0, true); sh.lineTo(dw, 0); sh.closePath();
  const door = new THREE.Mesh(new THREE.ShapeGeometry(sh, 16), M.doorway); door.position.set(DOOR_X, 0, BACK_Z + 0.01); g.add(door);
  const trimPts = [[-dw - 0.05, 0, 0]]; for (let i = 0; i <= 14; i++) { const a = Math.PI - i / 14 * Math.PI; trimPts.push([Math.cos(a) * (dw + 0.05), DOOR_H - dw + Math.sin(a) * (dw + 0.05), 0]); }
  trimPts.push([dw + 0.05, 0, 0]);
  const trimG = tubeGeo([[-dw - 0.05, 0, 0], ...trimPts.slice(1, -1), [dw + 0.05, 0, 0]], 0.045, 60, 6); trimG.translate(DOOR_X, 0, BACK_Z + 0.04);
  const trim = new THREE.Mesh(vcolFade(trimG, () => 1), M.wains); g.add(trim);
  // pillars on the open left side + pilasters on the right wall (rise into darkness)
  const colG = [];
  for (const [x, z] of [[-6.3, -2.7], [-6.3, 3.4], [-6.3, 9.5], [-6.3, 15.6]]) {
    const c = new THREE.CylinderGeometry(0.38, 0.38, H, 28, 8, true); c.translate(x, H / 2, z); colG.push(c);
    const b = new THREE.CylinderGeometry(0.5, 0.54, 0.32, 28); b.translate(x, 0.16, z); colG.push(b);
    const b2 = new THREE.CylinderGeometry(0.44, 0.48, 0.1, 28); b2.translate(x, 0.37, z); colG.push(b2);
  }
  for (const z of [1.8, 8.4, 15.0]) { const p = new THREE.BoxGeometry(0.34, H, 0.8, 1, 8, 1); p.translate(RIGHT_X - 0.17, H / 2, z); colG.push(dropFaces(p, V(1, 0, 0))); }
  const cols = new THREE.Mesh(vcolFade(merge(colG.map((q) => ni(q))), wallFade), M.wall); cols.receiveShadow = true; g.add(cols);
  // storage: stacked cardboard boxes + a dust-sheet-draped armchair (pale ghostly lump) back-left
  const boxG = [], tapeG = [], r = rng(23);
  const boxes = [[-2.75, 0, -4.55, 0.62, 0.46, 0.5, 0.05], [-2.72, 0.46, -4.58, 0.52, 0.4, 0.44, -0.12], [-2.1, 0, -4.62, 0.46, 0.36, 0.4, 0.18], [-2.12, 0.36, -4.6, 0.34, 0.26, 0.3, 0.42], [-3.35, 0, -4.66, 0.4, 0.3, 0.36, -0.2]];
  for (const [x, y, z, w, h, d, ry] of boxes) {
    const b = new RoundedBoxGeometry(w, h, d, 2, 0.018); b.rotateY(ry); b.translate(x, y + h / 2, z); boxG.push(b);
    const tp = new THREE.BoxGeometry(w + 0.004, 0.004, 0.06); tp.rotateY(ry); tp.translate(x, y + h + 0.001, z); tapeG.push(tp);
    const tp2 = new THREE.BoxGeometry(0.06, h * 0.35, d + 0.004); tp2.translate(-w / 2 + 0.0, 0, 0); tp2.rotateY(ry); tp2.translate(x + Math.cos(ry) * 0, y + h * 0.82, z); tapeG.push(tp2);
  }
  const bxm = new THREE.Mesh(merge(boxG), M.cardboard); bxm.castShadow = true; bxm.receiveShadow = true; g.add(bxm);
  g.add(new THREE.Mesh(merge(tapeG), M.tape));
  // draped chair: lathe lump + folds + back corners
  const prof = [[0.001, 1.04], [0.22, 1.02], [0.36, 0.95], [0.44, 0.8], [0.47, 0.6], [0.5, 0.38], [0.54, 0.16], [0.59, 0.03], [0.6, 0.0]].map(([x, y]) => new THREE.Vector2(x, y));
  const cg = new THREE.LatheGeometry(prof, 48);
  { const p = cg.attributes.position;
    for (let i = 0; i < p.count; i++) {
      let x = p.getX(i), y = p.getY(i), z = p.getZ(i); const th = Math.atan2(x, z), lo = 1 - y;
      const fold = 1 + 0.075 * Math.sin(9 * th + 0.6 * Math.sin(3 * th)) * lo * lo * lo;
      x *= 1.02 * fold; z *= 0.86 * fold;
      const back = Math.max(0, -Math.cos(th)) ** 2, corner = Math.exp(-((Math.abs(th) - 2.45) ** 2) / 0.09);
      y += (0.12 * corner + 0.06 * back) * smooth((y - 0.55) / 0.45) - 0.18 * Math.max(0, Math.cos(th)) ** 3 * smooth((y - 0.5) / 0.5);
      p.setXYZ(i, x, y, z);
    } cg.computeVertexNormals(); }
  const chair = new THREE.Mesh(cg, M.sheet); chair.position.set(-4.2, 0, -4.3); chair.rotation.y = 0.35; chair.castShadow = true; g.add(chair);
  return { group: g, floor, doorX: DOOR_X };
}

// ------------------------------------------------------------------------------------------------ CAGE
function buildCage(M, tagTex) {
  const g = new THREE.Group(); g.name = 'backroom.cage';
  g.position.copy(CAGE_POS); g.rotation.y = CAGE_YAW;
  const { R, n } = CAGE, r = rng(91);
  const bars = [];
  const phiMax = Math.acos(0.045 / R);
  for (let i = 0; i < n; i++) {
    const th = i * TAU / n, rel = Math.atan2(Math.sin(th), Math.cos(th));
    const inDoor = Math.abs(rel) < CAGE.doorHalf - 0.02, jamb = Math.abs(Math.abs(rel) - CAGE.doorHalf) < 0.02;
    const pts = [];
    const y0 = inDoor ? CAGE.doorTop + 0.012 : CAGE.base;
    const steps = inDoor ? 1 : 5;
    for (let k = 0; k <= steps; k++) pts.push(cagePt(th, lerp(y0, CAGE.shoulder, k / steps)));
    for (let k = 1; k <= 8; k++) { const ph = k / 8 * phiMax; pts.push(cagePt(th, CAGE.shoulder + CAGE.domeH * Math.sin(ph), R * Math.cos(ph))); }
    bars.push(shiftUV(tubeGeo(pts, jamb ? 0.0125 : 0.0092, 40, 6), r() * 0.08, r()));
  }
  // rings: bottom, shoulder (full), mid band (gap at the door), lintel over the door
  bars.push(shiftUV(tubeGeo(arcPts(0, TAU, CAGE.base + 0.022, 40).slice(0, -1), 0.0115, 80, 6, true), 0, 0.3));
  bars.push(shiftUV(tubeGeo(arcPts(0, TAU, CAGE.shoulder, 40).slice(0, -1), 0.013, 80, 6, true), 0.4, 0.6));
  bars.push(shiftUV(tubeGeo(arcPts(CAGE.doorHalf, TAU - CAGE.doorHalf, CAGE.latchY, 30), 0.0095, 60, 6), 0.2, 0.1));
  bars.push(shiftUV(tubeGeo(arcPts(-CAGE.doorHalf, CAGE.doorHalf, CAGE.doorTop + 0.012, 8), 0.0105, 16, 6), 0.3, 0.7));
  const barMesh = new THREE.Mesh(merge(bars), M.brass); barMesh.castShadow = true; g.add(barMesh);
  // base plate, rim, little feet
  const baseG = [];
  const bp = new THREE.CylinderGeometry(R + 0.04, R + 0.055, CAGE.base, 48); bp.translate(0, CAGE.base / 2, 0); baseG.push(bp);
  const lip = new THREE.CylinderGeometry(R + 0.005, R + 0.04, 0.012, 48); lip.translate(0, CAGE.base + 0.006, 0); baseG.push(lip);
  const base = new THREE.Mesh(merge(baseG), M.iron); base.receiveShadow = true; base.castShadow = true; g.add(base);
  const rimT = new THREE.TorusGeometry(R + 0.05, 0.008, 6, 64); rimT.rotateX(Math.PI / 2); rimT.translate(0, CAGE.base - 0.004, 0);
  g.add(new THREE.Mesh(rimT, M.brass));
  // dome hub, finial and the hanging ring
  const topY = CAGE.shoulder + CAGE.domeH;
  const hubG = [];
  const hub = new THREE.SphereGeometry(0.05, 18, 12); hub.scale(1, 0.7, 1); hub.translate(0, topY, 0); hubG.push(hub);
  const nk = new THREE.CylinderGeometry(0.014, 0.024, 0.05, 12); nk.translate(0, topY + 0.045, 0); hubG.push(nk);
  const ball = new THREE.SphereGeometry(0.026, 14, 10); ball.translate(0, topY + 0.082, 0); hubG.push(ball);
  const ring = new THREE.TorusGeometry(0.058, 0.0085, 8, 36); ring.translate(0, topY + 0.104 + 0.058, 0); hubG.push(ring);
  const hubM = new THREE.Mesh(merge(hubG.map((q) => ni(q))), M.brass); hubM.castShadow = true; g.add(hubM);
  // hinge knuckles (hinge on the +X jamb)
  const hingeTh = CAGE.doorHalf, H = cagePt(hingeTh, 0);
  const kn = [];
  for (const y of [0.19, 0.62]) { const c = new THREE.CylinderGeometry(0.017, 0.017, 0.05, 10); c.translate(H.x, y, H.z); kn.push(c); }
  g.add(new THREE.Mesh(merge(kn), M.iron));
  // ---- door (pivot at the hinge line)
  const door = new THREE.Group(); door.position.set(H.x, 0, H.z); g.add(door);
  const dg = [];
  const D0 = -CAGE.doorHalf + 3 * DEG, D1 = CAGE.doorHalf - 3 * DEG;
  for (const th of [-18 * DEG, 0, 18 * DEG]) dg.push(shiftUV(tubeGeo([cagePt(th, CAGE.doorBot), cagePt(th, CAGE.doorTop)], 0.0092, 6, 6), r() * 0.1, r()));
  for (const th of [D0, D1]) dg.push(shiftUV(tubeGeo([cagePt(th, CAGE.doorBot - 0.01), cagePt(th, CAGE.doorTop + 0.006)], 0.011, 6, 6), r() * 0.1, r()));
  for (const y of [CAGE.doorBot, CAGE.latchY, CAGE.doorTop]) dg.push(shiftUV(tubeGeo(arcPts(D0, D1, y, 8), 0.0095, 16, 6), r(), r()));
  // little arched scroll in the door's top bay
  { const s = []; for (let k = 0; k <= 12; k++) { const u = k / 12; s.push(cagePt(lerp(-14 * DEG, 14 * DEG, u), CAGE.doorTop - 0.012 - 0.07 * Math.sin(u * Math.PI), CAGE.R + 0.001)); } dg.push(tubeGeo(s, 0.0055, 20, 4)); }
  const dgeo = merge(dg); dgeo.translate(-H.x, 0, -H.z);
  const doorMesh = new THREE.Mesh(dgeo, M.brass); doorMesh.castShadow = true; door.add(doorMesh);
  // latch on the free stile: plate + turning lever with a knob
  const latchTh = D0, lp = cagePt(latchTh, CAGE.latchY, CAGE.R + 0.014).sub(V(H.x, 0, H.z));
  const nrm = V(Math.sin(latchTh), 0, Math.cos(latchTh)), tan = V(-Math.cos(latchTh), 0, Math.sin(latchTh));   // tan -> toward the jamb
  const latch = new THREE.Group(); latch.position.copy(lp);
  latch.quaternion.setFromRotationMatrix(_m4.makeBasis(tan, UP, nrm)); door.add(latch);
  const plate = new THREE.Mesh(new RoundedBoxGeometry(0.036, 0.07, 0.006, 1, 0.003), M.brassBright); plate.position.set(-0.004, 0, -0.004); latch.add(plate);
  const lever = new THREE.Group(); latch.add(lever);
  const lg = [];
  const bar = new RoundedBoxGeometry(0.1, 0.02, 0.008, 1, 0.003); bar.translate(0.042, 0, 0.004); lg.push(bar);
  const knob = new THREE.SphereGeometry(0.014, 12, 8); knob.translate(0.09, 0, 0.009); lg.push(knob);
  const riv = new THREE.CylinderGeometry(0.008, 0.008, 0.012, 10); riv.rotateX(Math.PI / 2); riv.translate(0, 0, 0.006); lg.push(riv);
  lever.add(new THREE.Mesh(merge(lg), M.brassBright));
  const knobAnchor = new THREE.Object3D(); knobAnchor.position.set(0.09, 0, 0.014); lever.add(knobAnchor);
  // catch (hook) on the latch-side jamb
  const cp = cagePt(-CAGE.doorHalf - 1.5 * DEG, CAGE.latchY, CAGE.R + 0.013);
  const hook = new THREE.Mesh(new RoundedBoxGeometry(0.016, 0.034, 0.02, 1, 0.004), M.brassBright); hook.position.copy(cp); hook.rotation.y = -CAGE.doorHalf; g.add(hook);
  // ---- TIME-OUT tag on a string from the shoulder ring (faces the default camera)
  const tag = new THREE.Group(); tag.position.copy(cagePt(CAGE.tagTh, CAGE.shoulder - 0.01, CAGE.R + 0.016)); tag.rotation.y = CAGE.tagTh; g.add(tag);
  const swing = new THREE.Group(); tag.add(swing);
  const str = new THREE.Mesh(new THREE.CylinderGeometry(0.0016, 0.0016, 0.075, 4), M.cord); str.position.y = -0.0375; swing.add(str);
  const tw = 0.17, th = 0.085;
  const tagF = new THREE.Mesh(new THREE.PlaneGeometry(tw, th), new THREE.MeshStandardMaterial({ map: tagTex.front, alphaTest: 0.5, roughness: 0.9, emissive: 0xffffff, emissiveMap: tagTex.front, emissiveIntensity: 0.16 }));
  tagF.position.set(0, -0.075 - th / 2 + 0.012, 0.002); swing.add(tagF);
  const tagB = new THREE.Mesh(new THREE.PlaneGeometry(tw, th), new THREE.MeshStandardMaterial({ map: tagTex.back, alphaTest: 0.5, roughness: 0.9 }));
  tagB.position.copy(tagF.position).setZ(0.0005); tagB.rotation.y = Math.PI; swing.add(tagB);
  tagF.castShadow = true;
  const sh = contactShadow(1.25, 1.25, 0.5); sh.position.set(CAGE_POS.x, 0.004, CAGE_POS.z);
  return { group: g, door, lever, knobAnchor, swing, shadow: sh, tag };
}

// ------------------------------------------------------------------------------------------------ JANITOR CORNER props
function bucketProfile(rB, rT, h, ribs) {
  const rAt = (y) => lerp(rB, rT, y / h), P = [];
  P.push([0.001, 0.0], [rB - 0.012, 0.0], [rB - 0.002, 0.006], [rB + 0.0005, 0.016]);
  const ys = [0.03, ...ribs.flatMap((f) => [f * h - 0.012, f * h - 0.004, f * h + 0.004, f * h + 0.012]), h - 0.02];
  const bump = (y) => ribs.reduce((s, f) => s + 0.0055 * Math.max(0, 1 - Math.abs(y - f * h) / 0.011), 0);
  for (const y of ys) P.push([rAt(y) + bump(y), y]);
  P.push([rT + 0.006, h - 0.008], [rT + 0.009, h - 0.001], [rT + 0.004, h + 0.006], [rT - 0.003, h + 0.002], [rT - 0.006, h - 0.008]);
  P.push([rT - 0.008, h - 0.03], [rB - 0.006, 0.026], [rB - 0.016, 0.018], [0.001, 0.018]);
  return P.map(([x, y]) => new THREE.Vector2(x, y));
}
function makeBucket(M, { rB = 0.115, rT = 0.155, h = 0.285, ribs = [0.34, 0.68], seg = 32 } = {}) {
  const g = new THREE.Group();
  const geo = new THREE.LatheGeometry(bucketProfile(rB, rT, h, ribs), seg);
  { const p = geo.attributes.position, c = new Float32Array(p.count * 3);
    for (let i = 0; i < p.count; i++) {
      const y = p.getY(i), rr = Math.hypot(p.getX(i), p.getZ(i)), inner = rr < lerp(rB, rT, y / h) - 0.004 && y > 0.012;
      const k = (0.62 + 0.38 * smooth(y / h)) * (inner ? 0.55 : 1);
      c[i * 3] = k; c[i * 3 + 1] = k * 0.995; c[i * 3 + 2] = k * 0.985;
    }
    geo.setAttribute('color', new THREE.BufferAttribute(c, 3)); }
  const body = new THREE.Mesh(geo, M.galv); body.castShadow = true; body.receiveShadow = true; g.add(body);
  const ly = h - 0.035, lr = lerp(rB, rT, ly / h) + 0.005;
  const lug = new THREE.CylinderGeometry(0.013, 0.013, 0.01, 10); lug.rotateZ(Math.PI / 2);
  g.add(new THREE.Mesh(merge([lug.clone().translate(lr, ly, 0), lug.clone().translate(-lr, ly, 0)]), M.galvDark));
  const bail = new THREE.Group(); bail.position.y = ly; g.add(bail);
  const br = lr + 0.006;
  bail.add(new THREE.Mesh(new THREE.TorusGeometry(br, 0.0042, 5, 26, Math.PI), M.galvDark));
  const grip = new THREE.CylinderGeometry(0.0115, 0.0115, 0.085, 10); grip.rotateZ(Math.PI / 2); grip.translate(0, br, 0);
  bail.add(new THREE.Mesh(grip, M.wood));
  return { group: g, bail, h, rT, rB };
}
// gravity-hung bail (pure: from the bucket's current world orientation)
const _q = new THREE.Quaternion(), _g = new THREE.Vector3();
function hangBail(b, t, seed) {
  b.group.updateMatrixWorld(true);
  b.group.getWorldQuaternion(_q); _g.set(0, -1, 0).applyQuaternion(_q.invert());
  let th = Math.atan2(_g.z + 2e-3, _g.y);
  th = clamp(th, -1.8, 1.8) + 0.04 * fbm1(t * 0.6, seed);
  b.bail.rotation.x = th;
}

function makeWringerBucket(M) {
  const g = new THREE.Group();
  const b = makeBucket(M, { rB: 0.165, rT: 0.205, h: 0.32, ribs: [0.3, 0.62], seg: 36 });
  b.group.position.y = 0.06; g.add(b.group);
  const cg = [];
  const frame = new THREE.TorusGeometry(0.15, 0.012, 6, 24); frame.rotateX(Math.PI / 2); frame.translate(0, 0.055, 0); cg.push(frame);
  for (let i = 0; i < 4; i++) {
    const a = i / 4 * TAU + Math.PI / 4, x = Math.sin(a) * 0.15, z = Math.cos(a) * 0.15;
    const w = new THREE.SphereGeometry(0.026, 10, 8); w.translate(x, 0.026, z); cg.push(w);
    const st = new THREE.CylinderGeometry(0.007, 0.007, 0.03, 6); st.translate(x, 0.05, z); cg.push(st);
  }
  const casters = new THREE.Mesh(merge(cg.map((q) => ni(q))), M.rubber); g.add(casters);
  // wringer press sitting on the back half of the rim + a lever with a red grip
  const H = 0.06 + 0.32, wg = [];
  for (const x of [-0.13, 0.13]) { const p = new RoundedBoxGeometry(0.016, 0.17, 0.15, 1, 0.005); p.translate(x, H + 0.06, -0.1); wg.push(p); }
  const press = new RoundedBoxGeometry(0.25, 0.13, 0.014, 1, 0.005); press.translate(0, H + 0.065, -0.05); wg.push(press);
  const back = new RoundedBoxGeometry(0.25, 0.15, 0.012, 1, 0.004); back.translate(0, H + 0.05, -0.165); wg.push(back);
  const axle = new THREE.CylinderGeometry(0.012, 0.012, 0.3, 10); axle.rotateZ(Math.PI / 2); axle.translate(0, H + 0.13, -0.1); wg.push(axle);
  const lev = new THREE.CylinderGeometry(0.0125, 0.0125, 0.52, 10); lev.translate(0, 0.26, 0); lev.rotateX(-0.42); lev.translate(0.14, H + 0.13, -0.1); wg.push(lev);
  const wr = new THREE.Mesh(merge(wg), M.galvDark); wr.castShadow = true; g.add(wr);
  const gripG = new THREE.CylinderGeometry(0.019, 0.019, 0.13, 12); gripG.translate(0, 0.46, 0); gripG.rotateX(-0.42); gripG.translate(0.14, H + 0.13, -0.1);
  g.add(new THREE.Mesh(gripG, M.red));
  return { group: g, bucket: b };
}

// wig geometry, in mop-local space, for the canonical wig placement (clamp WIG_LIFT above the hat top along the hat
// axis; handle tilted WIG_TILT away from it). hupM = hat axis in mop space.
const WIG_TILT = 0.7, WIG_LIFT = 0.045, HAT = { rB: 0.115, rT: 0.155, h: 0.285 };
const hupM = V(0, Math.cos(WIG_TILT), Math.sin(WIG_TILT)), e1M = V(1, 0, 0), e2M = V().crossVectors(hupM, e1M);
function wigPoint(az, s, root, i) {
  const top = hupM.clone().multiplyScalar(-WIG_LIFT);                      // hat top centre
  const rad = V().addScaledVector(e1M, Math.cos(az)).addScaledVector(e2M, Math.sin(az));
  const r0 = 0.035, rEdge = HAT.rB + 0.02, Ltop = rEdge - r0 + 0.02;
  let p;
  if (s < 0.03) p = root.clone().lerp(top.clone().addScaledVector(rad, r0).addScaledVector(hupM, 0.03), s / 0.03);
  else if (s < 0.03 + Ltop) { const u = (s - 0.03) / Ltop; p = top.clone().addScaledVector(rad, lerp(r0, rEdge, u)).addScaledVector(hupM, 0.03 * (1 - u * u) + 0.012); }
  else {
    const d = s - 0.03 - Ltop, k = clamp(d / HAT.h);
    p = top.clone().addScaledVector(rad, lerp(rEdge, HAT.rT + 0.02, k) + 0.02 * d * d * 8).addScaledVector(hupM, 0.012 - d);
    p.addScaledVector(V().crossVectors(hupM, rad), 0.01 * Math.sin(d * 30 + i));     // a little wave
  }
  return p;
}
function makeMop(M) {             // origin at the clamp, +Y along the handle; strands spray out below (-Y)
  const g = new THREE.Group();
  const hg = new THREE.CylinderGeometry(0.0135, 0.0135, 1.42, 10); hg.translate(0, 0.06 + 0.71, 0);
  const handle = new THREE.Mesh(hg, M.woodPale); handle.castShadow = true; g.add(handle);
  const cap = new THREE.CylinderGeometry(0.016, 0.016, 0.07, 10); cap.translate(0, 1.47, 0);
  g.add(new THREE.Mesh(cap, M.red));
  const cl = new THREE.CylinderGeometry(0.03, 0.037, 0.08, 14); cl.translate(0, 0.03, 0);
  const clamp_ = new THREE.Mesh(cl, M.galvDark); clamp_.castShadow = true; g.add(clamp_);
  const r = rng(5), geos = [];
  const N = 48, TS = 8, RS = 5;
  for (let i = 0; i < N; i++) {
    const a = i / N * TAU * 2.0 + r() * 0.3, rr = 0.006 + r() * 0.03;
    const root = V(Math.cos(a) * rr, -0.012, Math.sin(a) * rr);
    const spread = 0.1 + Math.pow(r(), 0.8) * 1.45, dir = V(Math.cos(a) * Math.sin(spread), -Math.cos(spread), Math.sin(a) * Math.sin(spread));
    const L = 0.28 + r() * 0.15, side = V(-Math.sin(a), 0, Math.cos(a));
    const pts = [];
    for (let k = 0; k <= 4; k++) { const s = k / 4; pts.push(root.clone().addScaledVector(dir, L * s).addScaledVector(side, 0.014 * Math.sin(s * 5 + i) * s)); }
    const curve = new THREE.CatmullRomCurve3(pts);
    const tg = new THREE.TubeGeometry(curve, TS, 0.0135, RS, false);
    const n = tg.attributes.position.count, aS = new Float32Array(n), aR = new Float32Array(n * 3), aC = new Float32Array(n * 3);
    for (let v = 0; v < n; v++) {
      const ring = Math.floor(v / (RS + 1)), s = ring / TS, c = curve.getPointAt(s);
      aS[v] = s; aR.set([root.x, root.y, root.z], v * 3); aC.set([c.x, c.y, c.z], v * 3);
    }
    // art-directed WIG target: strand i drapes over the hat's top at azimuth az and hangs down its side
    const aW = new Float32Array(n * 3), az = (i + 0.5) / N * TAU + (r() - 0.5) * 0.12, Lw = 0.2 + r() * 0.17;
    for (let v = 0; v < n; v++) { const ring = Math.floor(v / (RS + 1)); const c = wigPoint(az, (ring / TS) * Lw, root, i); aW.set([c.x, c.y, c.z], v * 3); }
    tg.setAttribute('aW', new THREE.BufferAttribute(aW, 3));
    tg.setAttribute('aS', new THREE.BufferAttribute(aS, 1)); tg.setAttribute('aRoot', new THREE.BufferAttribute(aR, 3)); tg.setAttribute('aC', new THREE.BufferAttribute(aC, 3));
    geos.push(tg);
  }
  const mat = droopMaterial(M.mop);
  const head = new THREE.Mesh(merge(geos), mat); head.frustumCulled = false; g.add(head);
  const bunch = new THREE.SphereGeometry(0.058, 14, 10); bunch.scale(1, 0.7, 1); bunch.translate(0, -0.02, 0);
  g.add(new THREE.Mesh(bunch, M.mopCotton));
  return { group: g, head, droop: mat.userData.droop };
}

function makeCornBroom(M) {       // origin: centre of the straw's bottom edge; +Y = handle; fan wide along X, thin along Z
  const g = new THREE.Group();
  const geo = new THREE.BoxGeometry(1, 1, 1, 6, 10, 2), p = geo.attributes.position, c = new Float32Array(p.count * 3);
  const w = (t) => lerp(0.34, 0.075, Math.pow(t, 0.85)), d = (t) => lerp(0.06, 0.042, t);
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), t = p.getY(i) + 0.5, z = p.getZ(i);
    p.setXYZ(i, x * w(t), t * 0.42 + 0.035 * (2 * x) ** 2 * (1 - t), z * d(t) * (1 + 0.3 * (1 - t)));
    const k = lerp(0.55, 1.0, smooth(t / 0.35)) * (0.96 + 0.08 * Math.sin(x * 40));
    c[i * 3] = 0.86 * k; c[i * 3 + 1] = 0.64 * k; c[i * 3 + 2] = 0.3 * k;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(c, 3)); geo.computeVertexNormals();
  const head = new THREE.Mesh(geo, M.straw); head.castShadow = true; g.add(head);
  const bands = [];
  for (const t of [0.6, 0.8]) { const b = new THREE.BoxGeometry(w(t) + 0.008, 0.014, d(t) + 0.008); b.translate(0, t * 0.42, 0); bands.push(b); }
  const nk = new THREE.CylinderGeometry(0.02, 0.026, 0.06, 10); nk.translate(0, 0.43, 0); bands.push(nk);
  g.add(new THREE.Mesh(merge(bands.map((q) => ni(q))), M.red));
  const hd = new THREE.CylinderGeometry(0.0125, 0.0125, 1.16, 10); hd.translate(0, 0.42 + 0.58, 0);
  const handle = new THREE.Mesh(hd, M.wood); handle.castShadow = true; g.add(handle);
  const cap = new THREE.CylinderGeometry(0.014, 0.014, 0.06, 10); cap.translate(0, 1.56, 0); g.add(new THREE.Mesh(cap, M.red));
  return { group: g, len: 1.6, halfW: 0.17 };
}
function makePushBroom(M) {       // origin: centre of the bristle bottom; +Y = handle; block along X
  const g = new THREE.Group();
  const br = new THREE.BoxGeometry(0.42, 0.085, 0.056, 6, 1, 1); br.translate(0, 0.0425, 0);
  const bm = new THREE.Mesh(br, M.bristle); bm.castShadow = true; g.add(bm);
  const blk = new RoundedBoxGeometry(0.45, 0.05, 0.078, 2, 0.012); blk.translate(0, 0.11, 0);
  const bk = new THREE.Mesh(blk, M.wood); bk.castShadow = true; g.add(bk);
  const brk = new THREE.CylinderGeometry(0.02, 0.026, 0.05, 10); brk.translate(0, 0.155, 0); g.add(new THREE.Mesh(brk, M.galvDark));
  const hd = new THREE.CylinderGeometry(0.0125, 0.0125, 1.28, 10); hd.translate(0, 0.17 + 0.64, 0);
  const handle = new THREE.Mesh(hd, M.woodPale); handle.castShadow = true; g.add(handle);
  return { group: g, len: 1.45, halfW: 0.225 };
}
function makeSpray(M, mat, col) {  // origin at the bottle's centre (pivot for tumbling); bottle 0.25 m tall
  const g = new THREE.Group(), inner = new THREE.Group(); inner.position.y = -0.11; g.add(inner);
  const P = [[0.001, 0], [0.04, 0], [0.046, 0.008], [0.047, 0.13], [0.04, 0.16], [0.022, 0.18], [0.016, 0.19], [0.016, 0.205], [0.001, 0.205]].map(([x, y]) => new THREE.Vector2(x, y));
  const geo = new THREE.LatheGeometry(P, 24), p = geo.attributes.position, c = new Float32Array(p.count * 3), base = new THREE.Color(col);
  for (let i = 0; i < p.count; i++) { const k = p.getY(i) < 0.105 ? 0.72 : 1.08; c[i * 3] = base.r * k; c[i * 3 + 1] = base.g * k; c[i * 3 + 2] = base.b * k; }
  geo.setAttribute('color', new THREE.BufferAttribute(c, 3));
  const body = new THREE.Mesh(geo, mat); body.castShadow = true; inner.add(body);
  const lab = new THREE.CylinderGeometry(0.0478, 0.0478, 0.055, 24, 1, true); lab.translate(0, 0.068, 0);
  inner.add(new THREE.Mesh(lab, M.label));
  const hg = [];
  const head = new RoundedBoxGeometry(0.03, 0.04, 0.075, 2, 0.01); head.translate(0, 0.222, 0.016); hg.push(head);
  const noz = new THREE.CylinderGeometry(0.008, 0.009, 0.02, 8); noz.rotateX(Math.PI / 2); noz.translate(0, 0.226, 0.062); hg.push(noz);
  const trig = new RoundedBoxGeometry(0.014, 0.05, 0.012, 1, 0.004); trig.rotateX(0.35); trig.translate(0, 0.19, 0.04); hg.push(trig);
  const collar = new THREE.CylinderGeometry(0.02, 0.02, 0.02, 12); collar.translate(0, 0.205, 0); hg.push(collar);
  inner.add(new THREE.Mesh(merge(hg), M.plasticW));
  return { group: g };
}
function makeRag(M, i) {
  const r = rng(300 + i), w = 0.26 + r() * 0.06, d = 0.2 + r() * 0.04;
  const geo = new RoundedBoxGeometry(w, 0.034, d, 2, 0.014), p = geo.attributes.position;
  for (let k = 0; k < p.count; k++) { const x = p.getX(k), z = p.getZ(k); p.setY(k, p.getY(k) + 0.006 * Math.sin(x * 23 + i) * Math.cos(z * 19 - i) + 0.004 * Math.sin(x * 7 + z * 9)); }
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, M.rag[i % M.rag.length]); m.castShadow = true; m.receiveShadow = true;
  const g = new THREE.Group(); g.add(m);
  return { group: g, w, d };
}
function makeSign(M) {           // A-frame; origin on the floor under the hinge; panels open +-spread; front faces +Z
  const g = new THREE.Group();
  const W = 0.3, Hh = 0.64, sh = new THREE.Shape();
  const rr = 0.05;
  sh.moveTo(-W / 2, 0); sh.lineTo(W / 2, 0); sh.lineTo(W / 2 - 0.02, Hh - rr); sh.quadraticCurveTo(W / 2 - 0.02, Hh, W / 2 - 0.02 - rr, Hh);
  sh.lineTo(-W / 2 + 0.02 + rr, Hh); sh.quadraticCurveTo(-W / 2 + 0.02, Hh, -W / 2 + 0.02, Hh - rr); sh.closePath();
  const hole = new THREE.Path(); hole.absellipse(0, Hh - 0.055, 0.055, 0.017, 0, TAU, true); sh.holes.push(hole);
  const geo = new THREE.ExtrudeGeometry(sh, { depth: 0.012, bevelEnabled: true, bevelThickness: 0.003, bevelSize: 0.003, bevelSegments: 1, curveSegments: 6 });
  { const uv = geo.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) / W + 0.5, uv.getY(i) / Hh); }
  geo.translate(0, -Hh, 0);     // hinge at the top edge
  const feet = []; for (const x of [-W / 2 + 0.03, W / 2 - 0.03]) { const f = new RoundedBoxGeometry(0.05, 0.02, 0.025, 1, 0.006); f.translate(x, -Hh + 0.008, 0.006); feet.push(f); }
  const feetG = merge(feet);
  const hinge = new THREE.Group(); hinge.position.y = Hh * Math.cos(0.2) + 0.01; g.add(hinge);
  const panels = [];
  for (const s of [1, -1]) {
    const pv = new THREE.Group(); hinge.add(pv);
    const m = new THREE.Mesh(geo, M.sign); m.castShadow = true; pv.add(m);
    pv.add(new THREE.Mesh(feetG, M.rubber));
    panels.push({ pv, s });
  }
  const pin = new THREE.CylinderGeometry(0.01, 0.01, W - 0.06, 8); pin.rotateZ(Math.PI / 2);
  hinge.add(new THREE.Mesh(pin, M.signEdge));
  return { group: g, hinge, panels, W, H: Hh };
}

// ------------------------------------------------------------------------------------------------ crash helpers (analytic)
// ballistic flight with floor bounces (restitution e, horizontal damping per bounce) then sliding to rest
function bounce(p0, v0, t, rest = 0, e = 0.32, slide = 3.2, g = 9.8) {
  let x = p0.x, y = p0.y, z = p0.z, vx = v0.x, vy = v0.y, vz = v0.z, tt = Math.max(0, t), land = -1, acc = 0;
  for (let k = 0; k < 5; k++) {
    const s = (vy + Math.sqrt(Math.max(0, vy * vy + 2 * g * (y - rest)))) / g;
    if (tt < s) return { p: V(x + vx * tt, y + vy * tt - 0.5 * g * tt * tt, z + vz * tt), land, air: true };
    x += vx * s; z += vz * s; y = rest; tt -= s; acc += s; if (land < 0) land = acc;
    vy = -(vy - g * s) * e; vx *= 0.62; vz *= 0.62;
    if (vy < 0.35) break;
  }
  const sp = Math.hypot(vx, vz);
  if (sp < 1e-4) return { p: V(x, rest, z), land, air: false };
  const ts = sp / slide, s2 = Math.min(tt, ts), dd = sp * s2 - 0.5 * slide * s2 * s2;
  return { p: V(x + vx / sp * dd, rest, z + vz / sp * dd), land, air: false };
}
// fall/tip angle 0 -> 1 with gravity ease-in and a small clatter bounce after landing at `t1`
function fallU(t, t0, t1, b = 0.09) {
  if (t <= t0) return 0;
  if (t < t1) return ease.in((t - t0) / (t1 - t0));
  const u = t - t1;
  return 1 - b * Math.abs(Math.sin(u * 11)) * Math.exp(-u * 7);
}
const slerpQ = (a, b, u) => a.clone().slerp(b, clamp(u));

// ------------------------------------------------------------------------------------------------ CREATE
export async function create() {
  const scene = new THREE.Scene(); scene.name = 'BACKROOM';
  scene.background = FOG_COL.clone();
  scene.fog = new THREE.Fog(FOG_COL.clone(), 11, 40);
  const env = makeEnv();
  const M = makeMaterials(env);
  const tagTex = tagTextures();

  // --- sky dome (dark gradient + a cool lobe toward the far screen at +Z)
  const domeU = { uCos: { value: 0 } };
  const dome = new THREE.Mesh(new THREE.SphereGeometry(70, 32, 16), new THREE.ShaderMaterial({
    uniforms: domeU, side: THREE.BackSide, depthWrite: false, fog: false,
    vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `varying vec3 vD; uniform float uCos;
      void main(){ float h = vD.y; vec3 c = mix(vec3(0.045,0.04,0.085), vec3(0.012,0.01,0.03), smoothstep(-0.05, 0.6, h));
        float lobe = pow(max(dot(vD, normalize(vec3(-0.1, 0.12, 1.0))), 0.0), 5.0);
        c += vec3(0.10, 0.14, 0.26) * lobe * (1.0 - uCos);
        c = mix(c, vec3(0.03, 0.02, 0.07) + vec3(0.06,0.03,0.1)*smoothstep(0.3,-0.2,h), uCos);
        gl_FragColor = vec4(c, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  }));
  dome.renderOrder = -10; dome.position.set(0, 0, 4); scene.add(dome);

  // --- room
  const room = buildRoom(M); scene.add(room.group);

  // --- far screen-of-consciousness glow (only seen in reverse angles)
  const scrTex = softRectTexture();
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(13, 8), new THREE.MeshBasicMaterial({ map: scrTex, color: new THREE.Color(0.55, 0.68, 1.05), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
  screen.position.set((LEFT_X + RIGHT_X) / 2, 3.8, FRONT_Z - 0.3); screen.rotation.y = Math.PI; scene.add(screen);
  const screenHalo = new THREE.Mesh(new THREE.PlaneGeometry(30, 16), new THREE.MeshBasicMaterial({ map: glowTexture(), color: new THREE.Color(0.07, 0.1, 0.19), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
  screenHalo.position.set((LEFT_X + RIGHT_X) / 2, 3.5, FRONT_Z - 1.0); screenHalo.rotation.y = Math.PI; scene.add(screenHalo);

  // --- lights
  const hemi = new THREE.HemisphereLight(0x3a4270, 0x1e1418, 0.85); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xa9bcff, 1.25);                 // the far screen light (cool key, the one shadow caster)
  const KEY_DIR = V(-1.6, 5.2, 12).normalize();
  key.target.position.set(1.0, 0, -2.0); key.position.copy(key.target.position).addScaledVector(KEY_DIR, 16);
  key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -6.2, right: 6.2, top: 5.2, bottom: -5.2, near: 2, far: 34 });
  key.shadow.bias = -0.0006; key.shadow.normalBias = 0.02; key.shadow.radius = 3;
  scene.add(key, key.target);
  const makeBulb = (pos, cordLen, color, intensity, dist) => {
    const pivot = new THREE.Group(); pivot.position.set(pos.x, pos.y + cordLen, pos.z); scene.add(pivot);
    const cord = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, cordLen, 5), M.cord); cord.position.y = -cordLen / 2; pivot.add(cord);
    const sock = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.026, 0.075, 12), M.socket); sock.position.y = -cordLen - 0.03; pivot.add(sock);
    const bg = new THREE.SphereGeometry(0.042, 18, 12); bg.scale(1, 1.22, 1);
    const glass = new THREE.Mesh(bg, new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(5.0) })); glass.position.y = -cordLen - 0.11; pivot.add(glass);
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), color: new THREE.Color(color).multiplyScalar(0.55), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    halo.scale.setScalar(0.42); halo.position.copy(glass.position); pivot.add(halo);
    const light = new THREE.PointLight(color, intensity, dist, 2); light.position.copy(glass.position); pivot.add(light);
    return { pivot, light, glass, halo, base: intensity, cordLen };
  };
  const bulb = makeBulb(V(-1.15, 2.3, 0.5), 5.4, 0xffb468, 7.0, 11);
  const bulb2 = makeBulb(V(3.45, 2.15, -3.75), 5.6, 0xffa95e, 4.2, 8);
  const voidLight = new THREE.PointLight(0x9a7cff, 3.2, 7, 2); scene.add(voidLight);
  const VOID_LIGHT_POS = VOID_SPOT.clone().addScaledVector(FWD, 1.0).setY(2.0);
  voidLight.position.copy(VOID_LIGHT_POS);

  // --- light shafts (soft additive cones, top dissolves into the dark) + their floor pools
  const shafts = [];
  const shaftMat = (col) => new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(col) }, uI: { value: 1 }, uTime: GLOBAL.uTime, uSeed: { value: 0 } },
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false,
    vertexShader: `varying vec3 vN; varying vec3 vV; varying vec2 vUv; varying float vWy;
      void main(){ vUv = uv; vec4 wp = modelMatrix * vec4(position, 1.0); vWy = wp.y; vec4 mv = viewMatrix * wp; vV = -mv.xyz;
        vN = normalize(normalMatrix * normal); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform vec3 uColor; uniform float uI, uTime, uSeed; varying vec3 vN; varying vec3 vV; varying vec2 vUv; varying float vWy;
      void main(){
        float f = abs(dot(normalize(vN), normalize(vV)));
        float edge = f * f * (0.6 + 0.4 * f);
        float along = smoothstep(0.0, 0.1, vUv.y) * (1.0 - smoothstep(0.35, 0.98, vUv.y));
        float drift = 0.82 + 0.18 * sin(vUv.y * 6.0 - uTime * 0.22 + uSeed + 0.7 * sin(vUv.x * 18.8496 + uSeed));
        float nearFloor = 0.55 + 0.45 * smoothstep(0.0, 0.6, vWy);
        gl_FragColor = vec4(uColor * (uI * edge * along * drift * nearFloor), 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const SHAFTS = [   // floor point, top offset (direction the light comes from), bottom radius, colour, intensity
    { at: V(-1.62, 0, 0.0), from: V(-0.32, 1, -0.22), rb: 0.78, rt: 0.3, col: 0xbfc8ff, k: 0.13 },
    { at: V(-3.9, 0, -3.7), from: V(-0.25, 1, -0.12), rb: 0.9, rt: 0.36, col: 0x9fb0ff, k: 0.12 },
    { at: V(2.45, 0, -3.95), from: V(-0.18, 1, -0.2), rb: 0.62, rt: 0.24, col: 0xc6cdfa, k: 0.1 },
  ];
  const SH_LEN = 8.5;
  SHAFTS.forEach((s, i) => {
    const geo = new THREE.CylinderGeometry(s.rt, s.rb, SH_LEN, 28, 1, true); geo.translate(0, SH_LEN / 2, 0);
    const mat = shaftMat(s.col); mat.uniforms.uSeed.value = i * 2.3;
    const m = new THREE.Mesh(geo, mat); m.position.copy(s.at); m.quaternion.copy(qBasis(s.from, V(0, 0, 1))); m.renderOrder = 4; m.frustumCulled = false;
    scene.add(m);
    const pool = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: glowTexture(), color: new THREE.Color(s.col), transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false }));
    pool.rotation.x = -Math.PI / 2; pool.position.set(s.at.x, 0.006, s.at.z); pool.scale.set(s.rb * 3.0, s.rb * 2.6, 1); pool.renderOrder = 2; scene.add(pool);
    shafts.push({ ...s, mesh: m, mat, pool, dir: s.from.clone().normalize() });
  });

  // --- cage
  const cage = buildCage(M, tagTex); scene.add(cage.group); scene.add(cage.shadow);

  // --- janitor corner
  const corner = new THREE.Group(); corner.name = 'backroom.corner'; scene.add(corner);
  const W = makeWringerBucket(M); corner.add(W.group);
  const bA = makeBucket(M), bB = makeBucket(M, { rB: 0.11, rT: 0.15, h: 0.27, ribs: [0.3, 0.66] });
  corner.add(bA.group, bB.group);
  const mop = makeMop(M); corner.add(mop.group);
  const broom1 = makeCornBroom(M), broom2 = makePushBroom(M); corner.add(broom1.group, broom2.group);
  const spray1 = makeSpray(M, M.sprayA, 0x6fc9b8), spray2 = makeSpray(M, M.sprayB, 0xe892ad); corner.add(spray1.group, spray2.group);
  const rags = [0, 1, 2, 3, 4].map((i) => makeRag(M, i)); rags.forEach((rg) => corner.add(rg.group));
  const sign = makeSign(M); corner.add(sign.group);
  // puddle (blobby disc)
  const pg = new THREE.CircleGeometry(1, 48); { const p = pg.attributes.position; for (let i = 1; i < p.count; i++) { const a = Math.atan2(p.getY(i), p.getX(i)); const k = 1 + 0.16 * Math.sin(3 * a + 0.5) + 0.09 * Math.sin(5 * a + 2.0) + 0.05 * Math.sin(9 * a); p.setXY(i, p.getX(i) * k, p.getY(i) * k); } }
  pg.rotateX(-Math.PI / 2);
  const puddle = new THREE.Mesh(pg, M.puddle); puddle.renderOrder = 1; puddle.visible = false; corner.add(puddle);
  // contact shadows
  const shadowOf = (w, d, o) => { const s = contactShadow(w, d, o); corner.add(s); return s; };
  const shW = shadowOf(0.7, 0.7, 0.55), shA = shadowOf(0.5, 0.5, 0.5), shB = shadowOf(0.48, 0.48, 0.5), shSign = shadowOf(0.55, 0.5, 0.4), shRag = shadowOf(0.55, 0.45, 0.4);
  const shCorner = contactShadow(2.6, 2.0, 0.45); shCorner.position.set(RIGHT_X - 0.9, 0.0035, BACK_Z + 0.85); shCorner.rotation.z = Math.PI / 4; corner.add(shCorner);
  const furn = contactShadow(2.4, 1.0, 0.5); furn.position.set(-2.9, 0.0035, -4.45); scene.add(furn);
  const furn2 = contactShadow(1.5, 1.3, 0.45); furn2.position.set(-4.2, 0.0035, -4.3); scene.add(furn2);

  // --- particles: additive (motes, splash, stars) + normal (dust puffs)
  const fx = new Particles({ max: 520, blending: 'add', intensity: 1.4 }); scene.add(fx.mesh);
  const fxN = new Particles({ max: 80, blending: 'normal', intensity: 1.0 }); scene.add(fxN.mesh);
  const r0 = rng(808);
  const MOTES = [];
  SHAFTS.forEach((s, si) => { for (let i = 0; i < 18; i++) MOTES.push({ si, h: r0() * 4.2, a: r0() * TAU, d: Math.sqrt(r0()), sp: 0.03 + r0() * 0.05, ph: r0() * TAU, sz: 0.012 + r0() * 0.016 }); });
  const FLOAT = Array.from({ length: 26 }, () => ({ p: V(-4 + r0() * 8.5, 0.3 + r0() * 2.6, -4.6 + r0() * 6), ph: r0() * TAU, sp: 0.02 + r0() * 0.04, sz: 0.01 + r0() * 0.012 }));
  const STARS = Array.from({ length: 300 }, () => {
    const u = r0() * 2 - 1, a = r0() * TAU, rr = 14 + r0() * 14, s = Math.sqrt(1 - u * u);
    return { p: V(Math.cos(a) * s * rr, 1.5 + Math.abs(u) * rr * 0.7 - 2, Math.sin(a) * s * rr - 1), sz: 0.05 + r0() ** 3 * 0.22, ph: r0() * TAU, c: r0() };
  });
  const NEB = [[-6, 6, -12, 9, 0x6a4cc8], [7, 4.5, -10, 8, 0x2fa7b8], [0, 9, -16, 12, 0xc0508a], [-9, 3, 4, 8, 0x4a68d0]];

  // ---------------------------------------------------------------------------------------- intact layout of the corner
  const I = {};
  const setT = (obj, p, q) => { obj.position.copy(p); obj.quaternion.copy(q); };
  const wallN_R = V(-1, 0, 0);
  I.W = { p: V(4.22, 0, -4.45), q: qAx(UP, 0.12) };
  I.A = { p: V(3.56, 0, -4.66), q: qAx(UP, 0.4) };
  I.B = { p: V(3.04, 0.27 + 0.006, -4.68), q: qAx(UP, -0.3).multiply(qAx(V(1, 0, 0), Math.PI)) };   // upside down: a stool
  I.mop = (() => { const foot = V(4.22, 0.17, -4.39), top = V(4.66, 1.56, -4.86); return { p: foot, q: qBasis(top.clone().sub(foot), V(-1, 0, 1)) }; })();
  I.b1 = (() => { const foot = V(4.56, 0, -3.72), top = V(RIGHT_X - 0.03, 1.58, -3.98); return { p: foot, q: qBasis(top.clone().sub(foot), wallN_R), top }; })();
  I.b2 = (() => { const foot = V(4.52, 0, -3.02), top = V(RIGHT_X - 0.03, 1.42, -3.12); return { p: foot, q: qBasis(top.clone().sub(foot), wallN_R), top }; })();
  I.s1 = { p: V(3.0, 0.284 + 0.11, -4.64), q: qAx(UP, -0.6) };
  I.s2 = { p: V(3.14, 0.284 + 0.11, -4.74), q: qAx(UP, 0.9) };
  I.rags = rags.map((rg, i) => ({ p: V(2.46 + 0.012 * Math.sin(i * 2.1), 0.018 + i * 0.033, -4.7 + 0.01 * Math.cos(i * 1.7)), q: qAx(UP, 0.15 * Math.sin(i * 1.9 + 0.4)) }));
  I.sign = { p: V(3.22, 0, -3.5), yaw: -Math.PI / 4 + 0.22, roll: 0.025 };
  const SIGN_SPREAD = 0.2;

  // ---------------------------------------------------------------------------------------- anchors / props / api
  const anchors = {
    cageCenter: V(), cageDoor: V(), cageDoorOut: V(), cageInside: V(), cageLatch: V(), cageTop: V(), cageTag: V(),
    voidSpot: VOID_SPOT.clone(), lurkSpot: LURK.clone(), crashSpot: CRASH.clone(), fearOutside: FEAR_OUT.clone(),
    cornerCenter: V(3.9, 0.35, -4.2), bulb: V(), bulb2: V(), screenGlow: V((LEFT_X + RIGHT_X) / 2, 2.2, FRONT_Z),
    voidLight: VOID_LIGHT_POS.clone(), rollEnd: V(), mopHead: V(), bucketHat: V(),
  };
  const toWorldCage = (lp) => lp.clone().applyAxisAngle(UP, CAGE_YAW).add(CAGE_POS);
  anchors.cageCenter.copy(toWorldCage(V(0, 0.5, 0)));
  anchors.cageInside.copy(toWorldCage(V(0, CAGE.base, 0)));
  anchors.cageDoor.copy(toWorldCage(V(0, 0, CAGE.R)));
  anchors.cageDoorOut.copy(toWorldCage(V(0, 0, CAGE.R + 0.38)));
  anchors.cageTop.copy(toWorldCage(V(0, CAGE.shoulder + CAGE.domeH + 0.16, 0)));
  const yaws = {
    void: -Math.PI / 4,                 // faces the cage / fearOutside
    fear: 3 * Math.PI / 4,              // at fearOutside, facing the Void
    fearInCage: CAGE_YAW,               // inside the cage facing out of the door
    magicianLurk: -Math.PI / 4,         // behind the Void, facing its back (and Fear beyond it)
    magicianCrash: -Math.PI / 4,        // crashed composition: back to the corner, face to the room
    cage: CAGE_YAW,
  };
  const props = {
    cage: cage.group, cageDoor: cage.door, latch: cage.lever, tag: cage.tag,
    bucketHat: bA.group, bucketB: bB.group, wringer: W.group, mop: mop.group, broom1: broom1.group, broom2: broom2.group,
    spray1: spray1.group, spray2: spray2.group, rags: rags.map((r) => r.group), sign: sign.group, puddle,
    corner, room: room.group, voidLight, bulb: bulb.light, bulb2: bulb2.light, key, hemi, fx, fxN,
  };
  const look = { bloom: 0.72, bloomThreshold: 0.72, bloomRadius: 0.6, vignette: 0.36, sat: 1.08, warm: 0.02, lift: [0.008, 0.007, 0.02], exposure: 1.15 };

  /** world point on a fixed cage bar: angleDeg around the cage (0 = door centre, + toward the hinge side), height y */
  function cageBar(angleDeg, y) {
    let a = Math.round(angleDeg / 18) * 18;
    if (Math.abs(a) < 36) a = a < 0 || (a === 0 && angleDeg < 0) ? -36 : 36;
    return toWorldCage(cagePt(a * DEG, y));
  }
  /** suggested magician flight (root pos) from lurkSpot (u=0) to crashSpot (u=1), apex height `apex` */
  function flightPos(u, apex = 1.15) { const p = LURK.clone().lerp(CRASH, u); p.y = 4 * apex * u * (1 - u); return p; }

  // ---------------------------------------------------------------------------------------- UPDATE
  const tmpQ = new THREE.Quaternion();
  const BAR_ROT = new THREE.Quaternion();
  function update(t, o = {}) {
    const cosmos = clamp(o.cosmos ?? 0);
    const L = o.lights || {};
    // ---- eye light (cool far key) — set every frame (other sets share EYE_LIGHT)
    EYE_LIGHT.uKeyDir.value.copy(KEY_DIR);
    EYE_LIGHT.uKeyColor.value.setRGB(0.86, 0.9, 1.0);
    EYE_LIGHT.uAmbient.value.setRGB(lerp(0.34, 0.36, cosmos), lerp(0.31, 0.27, cosmos), lerp(0.44, 0.52, cosmos));

    // ---- lights
    const dimRoom = 1 - 0.55 * cosmos;
    hemi.intensity = 0.85 * (L.hemi ?? 1) * (1 - 0.3 * cosmos);
    hemi.color.setRGB(lerp(0.227, 0.32, cosmos), lerp(0.26, 0.2, cosmos), lerp(0.44, 0.6, cosmos));
    key.intensity = 1.25 * (L.screen ?? 1) * (1 - 0.6 * cosmos);
    const crashOn = (o.crash ?? 0) > 0;
    const tcRaw = typeof o.crashT === 'number' ? o.crashT : (o.crash ?? 0) * 6.0;
    const tc = crashOn ? Math.max(0, tcRaw) : 0, w = crashOn ? (typeof o.crashT === 'number' ? clamp(o.crash ?? 1) : 1) : 0;
    // bulbs: tiny breathing sway (+ the corner bulb swings after the crash)
    const sway1 = 0.006 * Math.sin(t * 0.61) + 0.003 * fbm1(t * 0.3, 3);
    bulb.pivot.rotation.set(0.004 * Math.cos(t * 0.53), 0, sway1);
    const kick = w * (tc > 0 ? 0.11 * Math.exp(-tc * 0.42) * Math.sin(tc * 2.7) : 0);
    bulb2.pivot.rotation.set(kick * 0.6 + 0.003 * Math.sin(t * 0.47), 0, kick + 0.004 * Math.sin(t * 0.58));
    bulb.light.intensity = bulb.base * (L.bulb ?? 1) * dimRoom;
    bulb2.light.intensity = bulb2.base * (L.bulb2 ?? 1) * dimRoom;
    bulb.glass.material.color.set(0xffb468).multiplyScalar(5 * (L.bulb ?? 1) * dimRoom); bulb.halo.material.opacity = (L.bulb ?? 1) * dimRoom;
    bulb2.glass.material.color.set(0xffa95e).multiplyScalar(5 * (L.bulb2 ?? 1) * dimRoom); bulb2.halo.material.opacity = (L.bulb2 ?? 1) * dimRoom;
    bulb.glass.getWorldPosition(anchors.bulb); bulb2.glass.getWorldPosition(anchors.bulb2);
    // the Void's starlight (scene-movable)
    const vl = o.voidLight;
    voidLight.position.copy(VOID_LIGHT_POS); voidLight.intensity = 3.2; voidLight.color.set(0x9a7cff); voidLight.distance = 7;
    if (typeof vl === 'number') voidLight.intensity = 3.2 * vl;
    else if (vl) { if (vl.pos) voidLight.position.copy(toV(vl.pos)); if (vl.intensity != null) voidLight.intensity = vl.intensity; if (vl.color != null) voidLight.color.set(vl.color); if (vl.distance != null) voidLight.distance = vl.distance; }
    voidLight.intensity *= 1 + 0.6 * cosmos;
    anchors.voidLight.copy(voidLight.position);

    // ---- fog / background / room fade (cosmos)
    scene.fog.color.copy(FOG_COL).lerp(new THREE.Color(0x0a0618), cosmos); scene.background.copy(scene.fog.color);
    scene.fog.far = lerp(40, 90, cosmos); scene.fog.near = lerp(11, 30, cosmos);
    domeU.uCos.value = cosmos;
    for (const m of M.fadeable) m.opacity = 1 - cosmos;
    room.group.visible = cosmos < 0.999;
    room.floor.visible = true;
    M.floor.color.setRGB(1, 1, 1).lerp(new THREE.Color(0.28, 0.24, 0.42), cosmos);
    screen.material.opacity = 1 - cosmos; screenHalo.material.opacity = 1 - cosmos;
    for (const m of [furn, furn2]) m.material.opacity = 0.5 * (1 - cosmos);
    // shafts
    const shK = (o.shafts ?? 1) * (1 - cosmos);
    for (const s of shafts) {
      s.mat.uniforms.uI.value = s.k * shK; s.mesh.visible = shK > 0.002;
      s.pool.material.opacity = 0.26 * shK * (0.9 + 0.1 * Math.sin(t * 0.3 + s.at.x));
    }

    // ---- cage door / latch / tag
    const lat = clamp(o.latch ?? 0), door = clamp(o.cageDoor ?? 0);
    const latA = (Math.PI / 2) * ease.inOut(lat) + 0.14 * Math.sin(Math.PI * sm(0.78, 1, lat)) * (lat < 1 ? 1 : 0);
    cage.lever.rotation.z = latA;
    const v = clamp(door - 0.55 * Math.sin(TAU * 3 * door) / (TAU * 3));     // creaky hitches (monotonic)
    const doorA = CAGE.doorMax * (1 - (1 - v) * (1 - v)) + 0.05 * Math.sin(Math.PI * sm(0.82, 1, door)) * (door < 1 ? 1 : 0);
    cage.door.rotation.y = doorA;
    cage.door.position.y = -0.004 * Math.sin(doorA * 0.5);                    // hinge play: the door sags a hair when open
    const tagK = 1 + (o.tagSwing ?? 0) + 2.5 * Math.sin(Math.PI * door) * (door > 0 && door < 1 ? 1 : 0);
    cage.swing.rotation.set(0.05 * tagK * fbm1(t * 0.55, 21) + 0.03, 0, 0.08 * tagK * fbm1(t * 0.47, 22));
    cage.group.visible = o.cage !== false;
    cage.shadow.visible = o.cage !== false;
    cage.group.updateMatrixWorld(true);
    cage.knobAnchor.getWorldPosition(anchors.cageLatch);
    cage.tag.getWorldPosition(anchors.cageTag); anchors.cageTag.y -= 0.12;

    // ---- janitor corner
    corner.visible = o.corner !== false;
    updateCorner(t, tc, w, o);

    // ---- particles
    fx.begin(); fxN.begin();
    // dust motes drifting in the shafts (wrap invisibly: alpha follows the shaft profile)
    if (shK > 0.01 && (o.dust ?? 1) > 0) {
      for (const m of MOTES) {
        const s = shafts[m.si];
        const h = ((m.h + t * m.sp) % 4.2 + 4.2) % 4.2 + 0.15;
        const rad = lerp(s.rb, s.rt, h / SH_LEN) * 0.8 * m.d;
        const a = m.a + 0.15 * Math.sin(t * 0.2 + m.ph);
        const c = s.at.clone().addScaledVector(s.dir, h / s.dir.y);
        const pos = [c.x + Math.cos(a) * rad + 0.04 * Math.sin(t * 0.3 + m.ph), c.y + 0.03 * Math.sin(t * 0.4 + m.ph * 2), c.z + Math.sin(a) * rad];
        const al = 0.55 * shK * (o.dust ?? 1) * sm(0.15, 0.6, h) * (1 - sm(3.0, 4.3, h)) * (0.7 + 0.3 * Math.sin(t * 0.9 + m.ph));
        fx.add(pos, m.sz, 0xdfe4ff, al, 0, CELL.dust);
      }
      for (const f of FLOAT) {
        const pos = [f.p.x + 0.12 * Math.sin(t * f.sp * 3 + f.ph), f.p.y + 0.08 * Math.sin(t * f.sp * 2.3 + f.ph * 1.3), f.p.z + 0.12 * Math.cos(t * f.sp * 2.7 + f.ph)];
        fx.add(pos, f.sz, 0xb8b0e0, 0.25 * (o.dust ?? 1) * (1 - cosmos) * (0.6 + 0.4 * Math.sin(t * 0.7 + f.ph)), 0, CELL.dust);
      }
    }
    // cosmos backdrop: far stars + faint nebulae
    if (cosmos > 0.002) {
      for (const s of STARS) fx.add([s.p.x, s.p.y, s.p.z], s.sz, s.c < 0.3 ? 0xbfd8ff : s.c < 0.55 ? 0xffe6c8 : s.c < 0.75 ? 0xd8c4ff : 0xffffff, cosmos * (0.55 + 0.45 * Math.sin(t * (0.6 + s.c) + s.ph)), 0, CELL.star);
      for (const [x, y, z, sz, col] of NEB) fx.add([x, y, z], sz, col, 0.22 * cosmos, 0.3 * Math.sin(t * 0.03 + x), CELL.nebula);
    }
    crashFX(t, tc, w);
    fx.end(); fxN.end();
  }

  // ---------------------------------------------------------------------------------------- crash choreography
  // tc = seconds since impact (magician hits the pile at crashSpot moving along BACK). w = blend intact -> crashed.
  const SIGN_FALL_T = 4.6, BROOM_SLIDE_T = 7.2;
  const P_A = { v0: V(-0.75, 4.4, 0.85), spin: 3 * Math.PI, land: 0.92 };
  const lyingBucketQ = (axisDir, roll, rT, rB, h) => {   // a bucket lying on its side: local +Y along axisDir (bottom -> rim)
    const tilt = Math.atan2(rT - rB, h);
    const ax = axisDir.clone().setY(0).normalize(); const side = V(-ax.z, 0, ax.x);
    const yDir = ax.clone().applyAxisAngle(side, -tilt);  // rim end slightly higher
    return qBasis(yDir, UP).multiply(qAx(V(0, 1, 0), roll));
  };
  // rolling path for bucket B: quadratic Bezier from beside the stool spot to `to` ([x,z]), bulging toward the back
  // wall; arc-length LUT so the roll speed/angle are exact. ROLL_S0 = metres it rolls during the crash itself.
  const ROLL_S0 = 0.75, ROLL_FROM = V(3.0, 0, -4.42), ROLL_TO = V(-1.25, 0, -3.35);
  const _paths = new Map();
  function rollPath(to) {
    const key = to ? to.join(',') : 'default';
    if (_paths.has(key)) return _paths.get(key);
    const P0 = ROLL_FROM.clone(), P1 = to ? V(to[0], 0, to[1]) : ROLL_TO.clone();
    const M = P0.clone().lerp(P1, 0.5), d = P1.clone().sub(P0), n = V(d.z, 0, -d.x).normalize();
    if (n.z > 0) n.negate();                                           // bulge toward the back wall (-Z)
    const Q = M.clone().addScaledVector(n, Math.min(0.9, d.length() * 0.22));
    const N = 64, pts = [], cum = [0];
    for (let i = 0; i <= N; i++) { const u = i / N; pts.push(P0.clone().multiplyScalar((1 - u) ** 2).addScaledVector(Q, 2 * (1 - u) * u).addScaledVector(P1, u * u)); if (i) cum.push(cum[i - 1] + pts[i].distanceTo(pts[i - 1])); }
    const path = { pts, cum, len: cum[N], n };
    _paths.set(key, path);
    return path;
  }
  function lyingOnPath(b, path, s, out) {
    const { pts, cum } = path, N = pts.length - 1;
    s = clamp(s, 0, path.len);
    let i = 1; while (i < N && cum[i] < s) i++;
    const f = (s - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]);
    const c = pts[i - 1].clone().lerp(pts[i], f), T = pts[i].clone().sub(pts[i - 1]).normalize();
    let ax = V(-T.z, 0, T.x); if (ax.dot(path.n) < 0) ax.negate();    // bottom -> rim points to the outside of the curve
    const rAvg = (b.rT + b.rB) / 2, omega = V().crossVectors(UP, T).normalize();
    out.ax = ax; out.c = c.clone().setY(rAvg);
    out.q = qAx(omega, s / rAvg).multiply(lyingBucketQ(ax, 0.7, b.rT, b.rB, b.h));
    out.p = c.clone().addScaledVector(ax, -b.h / 2).setY(b.rB + 0.004);
    return out;
  }
  const tmpB = { p: V(), q: new THREE.Quaternion() };
  const tmpA = { p: V(), q: new THREE.Quaternion() };
  function updateCorner(t, tc, w, o) {
    const on = w > 0;
    // ---- wringer bucket: tips over toward +Z (opening to the room), water spills
    {
      const tip = on ? fallU(tc, 0.04, 0.42, 0.08) : 0;
      const pivot = I.W.p.clone().add(V(0, 0, 0.2));
      const q = qAx(V(1, 0, 0), tip * (Math.PI / 2 - 0.08)).multiply(I.W.q);
      const rel = I.W.p.clone().sub(pivot).applyQuaternion(qAx(V(1, 0, 0), tip * (Math.PI / 2 - 0.08)));
      const p = pivot.add(rel).add(V(0.05 * sm(0, 0.3, tc) * (on ? 1 : 0), 0.035 * Math.sin(Math.PI * clamp(tc / 0.25)) * (on ? 1 : 0), 0));
      setT(W.group, I.W.p.clone().lerp(p, w), slerpQ(I.W.q, q, w));
      hangBail(W.bucket, t, 5);
      shW.position.set(W.group.position.x, 0.0035, W.group.position.z + 0.12 * tip * w); shW.scale.set(1 + 0.3 * tip * w, 1 + 0.5 * tip * w, 1);
    }
    // ---- puddle
    {
      const grow = on ? sm(0.38, 2.4, tc) : 0;
      puddle.visible = grow * w > 0.003;
      puddle.position.set(I.W.p.x - 0.12 * grow, 0.0032, I.W.p.z + 0.42 + 0.45 * grow);
      puddle.scale.set(0.12 + 0.5 * grow, 1, 0.16 + 0.72 * grow).multiplyScalar(w);
      puddle.rotation.y = 0.4;
    }
    // ---- mop: thrown out of the wringer, falls toward the room, lands flat (or becomes a wig on the bucket hat)
    {
      const u = on ? fallU(tc, 0.1, 0.78, 0.1) : 0;
      const head0 = I.mop.p, head1 = V(3.86, 0.03, -3.66);
      const lift = on ? 0.32 * Math.sin(Math.PI * clamp((tc - 0.1) / 0.55)) * (tc < 0.65 ? 1 : 0) : 0;
      const ph = head0.clone().lerp(head1, ease.out(clamp((tc - 0.1) / 0.6))).add(V(0, lift, 0));
      const dir1 = V(-0.72, 0.0, 0.69).normalize();
      const q1 = qBasis(dir1, UP).multiply(qAx(UP, 0.7));
      let p = I.mop.p.clone().lerp(ph, w), q = slerpQ(I.mop.q, slerpQ(I.mop.q, q1, u), w);
      let floorY = lerp(0.06 + 0.075, 0.0, on ? sm(0.05, 0.3, tc) * w : 0);
      mop.droop.uColR.value = 0; mop.droop.uWig.value = 0;
      const wig = clamp(typeof o.mopWig === 'number' ? o.mopWig : (o.mopWig?.blend ?? 0));
      if (wig > 0 && (o.bucketHat || o.mopWig?.pos)) {
        // the mop flops onto the hat like a wig: clamp just above the bucket's (upturned) bottom, handle sticking out
        // sideways-up, strands draped all round by a capsule collider along the hat bucket.
        const hat = o.bucketHat ? hatTransform(o.bucketHat, tc) : null;
        let hup = hat ? V(0, -1, 0).applyQuaternion(hat.q) : V(0, 1, 0);       // bucket's bottom side (top of the hat)
        let top = hat ? hat.p.clone() : toV(o.mopWig.pos);
        if (o.mopWig?.pos) top = toV(o.mopWig.pos);
        if (hup.y < 0.3) hup = V(0, 1, 0);                                        // hat upside-down (headstand): drape from above
        const yawW = o.mopWig?.yaw ?? 0.7;
        const side = V(1, 0, 0).applyQuaternion(qBasis(hup, V(0, 0, 1))).applyAxisAngle(hup, yawW);
        const hdir = hup.clone().multiplyScalar(Math.cos(WIG_TILT)).addScaledVector(side, -Math.sin(WIG_TILT)).normalize();
        const qw = qBasis(hdir, side);
        const pw = top.clone().addScaledVector(hup, WIG_LIFT);
        const arc = Math.sin(Math.PI * wig) * 0.4;
        p = p.clone().lerp(pw, ease.out(wig)).addScaledVector(UP, arc * (wig < 1 ? 1 : 0));
        q = slerpQ(q, qw, ease.inOut(wig));
        mop.droop.uWig.value = sm(0.55, 1, wig);   // strands morph into the draped wig as it lands
        floorY = -10;
      }
      setT(mop.group, p, q);
      mop.droop.uFloorY.value = floorY;
      mop.group.updateMatrixWorld(true);
      mop.group.getWorldQuaternion(tmpQ); mop.droop.uGravL.value.set(0, -1, 0).applyQuaternion(tmpQ.invert());
      anchors.mopHead.setFromMatrixPosition(mop.group.matrixWorld);
    }
    // ---- bucket A: flies up, spins, lands upside down (or onto the magician's head: opts.bucketHat)
    {
      let p, q;
      if (o.bucketHat) {
        const h = hatTransform(o.bucketHat, tc);
        p = h.p; q = h.q;
        if (!on) { p = I.A.p.clone().lerp(p, 1); }
      } else if (on) {
        const end = V(3.42, 0, -3.58);
        p = flyArc(I.A.p, end, tc, P_A.land, 1.45);
        const u = clamp(tc / P_A.land);
        const axis = V(1, 0, 0.35).normalize();
        q = qAx(axis, P_A.spin * ease.out(u)).multiply(I.A.q);
        if (tc > P_A.land) { const b = tc - P_A.land; p.y += 0.05 * Math.abs(Math.sin(b * 10)) * Math.exp(-b * 6); q = qAx(V(0, 0, 1), 0.06 * Math.sin(b * 9) * Math.exp(-b * 3)).multiply(q); }
        // landed upside down: lift origin to the rim height
        const flip = ease.out(u); p.y += bA.h * sm(0.45, 1, flip);
      } else { p = I.A.p.clone(); q = I.A.q.clone(); }
      setT(bA.group, I.A.p.clone().lerp(p, o.bucketHat ? 1 : w), o.bucketHat ? q : slerpQ(I.A.q, q, w));
      // bonk squash on landing
      const sq = on ? Math.exp(-Math.max(0, tc - (o.bucketHat?.at ?? P_A.land)) * 14) * (tc > (o.bucketHat?.at ?? P_A.land) ? 1 : 0) : 0;
      bA.group.scale.set(1 + 0.08 * sq, 1 - 0.12 * sq, 1 + 0.08 * sq);
      hangBail(bA, t, 7);
      bA.group.getWorldPosition(anchors.bucketHat);
      const air = clamp((bA.group.position.y - (o.bucketHat ? 0 : 0)) / 0.8);
      shA.position.set(bA.group.position.x, 0.0035, bA.group.position.z); shA.material.opacity = 0.5 * (1 - air) * (o.bucketHat ? 0 : 1);
    }
    // ---- bucket B (upturned stool with spray bottles): knocked onto its side, rolls a little along a lazy arc;
    //      opts.rollBucket 0..1 rolls it on, slowly, across the floor (rim toward the wall, so it curves into the room)
    {
      const roll = clamp(o.rollBucket ?? 0);
      const path = rollPath(o.rollTo);
      const knock = on ? sm(0.05, 0.36, tc) : 0;
      const s0 = on ? ROLL_S0 * ease.out(clamp((tc - 0.33) / 2.0)) : 0;
      const s = s0 + (path.len - ROLL_S0) * ease.inOut(roll) * (on ? 1 : 0);
      lyingOnPath(bB, path, s, tmpA);
      const settle = on && tc > 2.33 && roll === 0 ? 0.06 * Math.sin((tc - 2.33) * 7) * Math.exp(-(tc - 2.33) * 2.6) : 0;
      if (settle) tmpA.q.premultiply(qAx(tmpA.ax, settle));
      const pK = I.B.p.clone().lerp(tmpA.p, ease.inOut(knock)).add(V(0, 0.16 * Math.sin(Math.PI * knock), 0));
      const qK = slerpQ(I.B.q, tmpA.q, ease.inOut(knock));
      setT(bB.group, I.B.p.clone().lerp(pK, w), slerpQ(I.B.q, qK, w));
      hangBail(bB, t, 9);
      shB.position.set(bB.group.position.x, 0.0035, bB.group.position.z); shB.scale.set(1.2, 1, 1);
      lyingOnPath(bB, path, path.len, tmpB); anchors.rollEnd.copy(tmpB.c);
    }
    // ---- spray bottles
    {
      const s1 = tumble(I.s1, V(-1.7, 3.5, 1.95), tc, 0.047, V(0.3, 0, 1), 15, -0.9);
      setT(spray1.group, I.s1.p.clone().lerp(s1.p, w), slerpQ(I.s1.q, s1.q, w));
      const s2 = tumble({ p: I.s2.p.clone(), q: I.s2.q }, V(-0.55, 0.9, 0.75), Math.max(0, tc - 0.1), 0.047, V(1, 0, 0.2), 7, 2.1);
      setT(spray2.group, I.s2.p.clone().lerp(s2.p, w), slerpQ(I.s2.q, s2.q, w));
      if (!on) { setT(spray1.group, I.s1.p, I.s1.q); setT(spray2.group, I.s2.p, I.s2.q); }
    }
    // ---- rags flop over
    rags.forEach((rg, i) => {
      const t0 = 0.12 + 0.035 * i, u = on ? ease.outBack(clamp((tc - t0) / 0.42)) : 0, uu = clamp(u);
      const pEnd = V(2.46 - 0.07 - 0.085 * i, 0.018 + Math.max(0, 2 - i) * 0.028 + (i > 2 ? 0.012 : 0), -4.7 + 0.07 + 0.075 * i);
      const qEnd = qAx(UP, 0.4 * Math.sin(i * 2.3) + 0.3).multiply(qAx(V(0, 0, 1), (i > 2 ? 0.22 : 0.05) * (i % 2 ? 1 : -1))).multiply(qAx(V(1, 0, 0), i === 4 ? 0.3 : 0));
      const p = I.rags[i].p.clone().lerp(pEnd, u).add(V(0, 0.09 * Math.sin(Math.PI * uu) * (i / 4), 0));
      setT(rg.group, I.rags[i].p.clone().lerp(p, w), slerpQ(I.rags[i].q, slerpQ(I.rags[i].q, qEnd, uu), w));
    });
    shRag.position.set(2.32, 0.0035, -4.52);
    // ---- broom 1 (corn broom): topples into the room right away
    {
      const u = on ? fallU(tc, 0.06, 0.62, 0.1) : 0;
      const dir1 = V(-0.86, 0, 0.5).normalize();
      const q1 = qBasis(dir1, UP);
      const foot = I.b1.p.clone().add(V(-0.12, 0.035, 0.06).multiplyScalar(u));
      setT(broom1.group, I.b1.p.clone().lerp(foot, w), slerpQ(I.b1.q, slerpQ(I.b1.q, q1, u), w));
    }
    // ---- broom 2 (push broom): wobbles and stays... then slides down the wall later (opts.broomSlide)
    {
      const slide = typeof o.broomSlide === 'number' ? clamp(o.broomSlide) : (on ? clamp((tc - BROOM_SLIDE_T) / 0.75) : 0);
      const wob = on ? 0.075 * Math.sin(tc * 9.5) * Math.exp(-tc * 1.6) * sm(0.12, 0.2, tc) : 0;
      const qw = qAx(V(1, 0, 0), wob).multiply(I.b2.q);
      const dirEnd = V(0, 0, 1);
      const qEnd = qBasis(dirEnd, V(-1, 0, 0.0)).multiply(qAx(UP, -0.25));
      const su = slide < 1 ? ease.in(slide) : fallU(1 + (slide - 1), 0, 1, 0.1);
      const foot = I.b2.p.clone().add(V(-0.06 * su, 0.04 * su, 0));
      const q = slerpQ(qw, qEnd, su);
      setT(broom2.group, I.b2.p.clone().lerp(foot, w), slerpQ(I.b2.q, q, w));
    }
    // ---- wet-floor sign: clipped by the flying body, skids & spins, then teeters on one corner... and finally tips flat
    {
      const { p: sp, q: sq, spread } = signPose(tc, on, o);
      sign.group.position.copy(sp); sign.group.quaternion.copy(sq);
      sign.panels.forEach(({ pv, s }) => { pv.rotation.set(-spread, s > 0 ? 0 : Math.PI, 0, 'YXZ'); });
      shSign.position.set(sp.x, 0.0035, sp.z); shSign.material.opacity = 0.4;
    }
  }
  function flyArc(a, b, t, T, apex) {
    const u = clamp(t / T), p = a.clone().lerp(b, u); p.y = lerp(a.y, b.y, u) + 4 * apex * u * (1 - u); return p;
  }
  // a small object launched with velocity v0 at tc = 0: tumbles end over end, lands, skids, rests on its side
  function tumble(I0, v0, tc, rest, axis, spin, yawEnd) {
    const bb = bounce(I0.p, v0, tc, rest, 0.3, 2.6);
    const land = bb.land < 0 ? Infinity : bb.land;
    const ta = Math.min(tc, land);
    let q = qAx(axis.clone().normalize(), spin * ta).multiply(I0.q);
    if (tc > land) {
      const k = sm(0, 0.22, tc - land);
      const qRest = qAx(UP, yawEnd + 2.2 * (1 - Math.exp(-(tc - land) * 2.5))).multiply(qAx(V(0, 0, 1), Math.PI / 2));
      q = slerpQ(q, qRest, k);
    }
    return { p: bb.p, q };
  }
  // bucket-hat transform from opts.bucketHat = { pos (headTop), up (headUp), yaw, at, lift, tilt }
  function hatTransform(h, tc) {
    const top = toV(h.pos), up = h.up ? toV(h.up).normalize() : V(0, 1, 0);
    const q = qBasis(up.clone().negate(), V(Math.sin(h.yaw ?? 0), 0, Math.cos(h.yaw ?? 0)));   // bucket +Y -> -up (opening down)
    if (h.tilt) q.premultiply(qAx(V(1, 0, 0).applyQuaternion(q), h.tilt));
    // origin = the bucket's (outer) bottom centre, now on top: the inner bottom rests on the head top, the rim hangs over the face
    const pOn = top.clone().addScaledVector(up, 0.022 + (h.lift ?? 0));
    const at = h.at ?? P_A.land;
    if (h.blend == null && tc >= at) return { p: pOn, q };
    const u = h.blend != null ? clamp(h.blend) : clamp(tc / at);
    // fly from the pile to the head, flipping over on the way
    const p = flyArc(I.A.p.clone(), pOn, u * at, at, 1.0);
    const qq = slerpQ(I.A.q, q, ease.inOut(u));
    const spin = qAx(V(1, 0, 0.3).normalize(), TAU * (1 - ease.out(u)));
    return { p, q: spin.multiply(qq) };
  }
  // sign: pivot on one bottom corner (local (+W/2, 0, 0)); yaw spins; tilt = teeter; lean = forward fall
  const SIGN_TEETER_P = CRASH.clone().addScaledVector(FWD, 0.62).add(V(0.26, 0, 0.26));
  function signPose(tc, on, o) {
    const i0 = I.sign;
    let pos = i0.p.clone(), yaw = i0.yaw, tilt = i0.roll, lean = 0, spread = SIGN_SPREAD;
    if (on) {
      const k = clamp((tc + 0.05) / 0.55), ke = ease.out(k);
      const dirK = CRASH.clone().sub(SIGN_TEETER_P).setY(0).normalize();
      const yawT = Math.atan2(dirK.x, dirK.z) + Math.PI;         // local +Z points away from the magician; leans fall toward him
      pos = i0.p.clone().lerp(SIGN_TEETER_P, ke); pos.y += 0.14 * Math.sin(Math.PI * k);
      yaw = lerp(i0.yaw, yawT - TAU, ke);
      const tt = Math.max(0, tc - 0.45);
      tilt = lerp(i0.roll, 0.36, sm(0.2, 0.55, tc)) + (tc > 0.45 ? 0.09 * Math.exp(-tt * 0.45) * Math.sin(tt * 6.2) + 0.03 * Math.sin(tc * 2.1) : 0);
      const fall = typeof o.signFall === 'number' ? clamp(o.signFall) : clamp((tc - SIGN_FALL_T) / 0.62);
      const support = o.signOn ?? 0;
      const leanMax = Math.PI / 2 - Math.asin(clamp(support / 0.62, 0, 0.95));
      const fu = fall < 1 ? ease.in(fall) : 1;
      const after = typeof o.signFall === 'number' ? 0 : Math.max(0, tc - SIGN_FALL_T - 0.62);
      lean = -(leanMax * fu - (fall >= 1 ? 0.08 * Math.abs(Math.sin(after * 10)) * Math.exp(-after * 6) : 0));
      tilt *= 1 - fu;
      spread = SIGN_SPREAD * (1 - sm(0.15, 0.85, fall));
    }
    const q = qAx(UP, yaw).multiply(qAx(V(1, 0, 0), lean)).multiply(qAx(V(0, 0, 1), tilt));
    const pivotL = V(sign.W / 2, 0, 0);
    const p = pos.clone().add(pivotL.clone().applyQuaternion(qAx(UP, yaw))).sub(pivotL.clone().applyQuaternion(q));
    return { p, q, spread };
  }
  // particles for the crash: dust puffs, water splash, little debris
  function crashFX(t, tc, w) {
    if (w <= 0 || tc <= 0 || tc > 6) return;
    fxN.burst({ t: tc, at: 0.0, count: 12, seed: 41, life: 1.6, jitter: 0.12, origin: [CRASH.x + 0.1, 0.35, CRASH.z - 0.1], vel: [-0.3, 0.55, 0.3], spread: [0.9, 0.35, 0.9], drag: 2.2,
      size: [0.25, 0.45], grow: 2.2, color: [0x8d8494, 0x7e7488, 0x9a90a0], alpha: 0.32 * w, fade: [0.1, 0.6], cell: CELL.puff, spin: 0.6 });
    fx.burst({ t: tc, at: 0.38, count: 34, seed: 43, life: 0.62, jitter: 0.1, origin: [I.W.p.x - 0.02, 0.22, I.W.p.z + 0.36], vel: [-0.2, 1.7, 1.2], spread: [0.8, 0.9, 0.7], gravity: [0, -9.8, 0],
      size: [0.014, 0.03], color: [0xbfe4ff, 0xe6f4ff, 0x9fcfff], alpha: 0.85 * w, fade: [0.05, 0.35], cell: CELL.dot });
    fx.burst({ t: tc, at: 0.42, count: 10, seed: 44, life: 0.5, origin: [I.W.p.x - 0.05, 0.03, I.W.p.z + 0.55], vel: [0, 0.9, 0.6], spread: [0.7, 0.3, 0.6], gravity: [0, -7, 0],
      size: [0.03, 0.05], color: 0xd6ecff, alpha: 0.5 * w, fade: [0.05, 0.4], cell: CELL.dot });
    fx.burst({ t: tc, at: 0.0, count: 16, seed: 45, life: 1.0, origin: [CRASH.x, 0.5, CRASH.z], vel: [-0.6, 1.6, 0.6], spread: [1.4, 1.0, 1.4], gravity: [0, -6, 0],
      size: [0.012, 0.022], color: [0xd8d0c0, 0xbfb6a6], alpha: 0.7 * w, fade: [0.05, 0.4], cell: CELL.dust });
  }

  update(0, {});
  return { scene, update, anchors, props, look, yaws, layout: LAYOUT, cageBar, flightPos, name: 'BACKROOM' };
}
