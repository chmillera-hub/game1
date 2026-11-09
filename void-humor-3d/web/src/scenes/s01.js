// s01 running_from_the_void — the opening. Frame 0 (t = 0) is the social-media preview: a crying kid hugging a glowing
// phone runs at us over the top of a little rise (cut at the hips), fleeing a huge, soft, hopeful Void on the crest behind
// them, warm golden dusk, title room in the sky (the title is burned in by the subtitle pass, y 110-300).
// Shots: A FRAME0 backward track (0 -> "Twitter") · B phone INSERT (-> s01b03) · C CHASELOW 24 mm low wide (s01b03).
// Everything is timed from beat refs (word offsets from data/lines.json).
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, noise1, fbm1, hash1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, lookFor } from './marks.js';
import { VX } from '../chars/void.js';
import { UX } from '../chars/user.js';
import { ownedGroup, cast, G, bump, jiggle, V3, WD, fitCam, footfalls } from './kit_s0102.js';

// ------------------------------------------------------------------------------------------------ constants
const D = [-0.2495, 0.9684];                    // travel direction (stage local): down the path toward the stage
const YAW_RUN = Math.atan2(D[0], D[1]);          // local facing while running (-0.252)
const SPD = 1.25;                                // cheated ground speed (m/s); the camera tracks at the same speed
const U_CPS = 1.32, V_CPS = 1.25;                // run / waddle cycles per second
const U_PH0 = 0.18, V_PH0 = 0.05;                // phase offsets (frame 0 = mid-stride, both)
const PH_W = 0.071, PH_H = 0.148, PH_D = 0.0085; // USER rig phone slab (web/src/chars/user.js)
const SW = PH_W - 0.007, SH = PH_H - 0.008;      // screen size

// beat-anchored times (word onsets from data/lines.json: "Twitter" +1.10, "crying" +0.0, "void" +1.36)
const tLook = () => T('s01b01+0.4');            // look back over the LEFT shoulder (~1.0 s)
const tIns = () => T('s01b02+1.08');            // cut to the phone insert on "Twitter"
const tC = () => T('s01b03');                   // cut to the low wide on "crying"
const tVoidWord = () => T('s01b03+1.33');       // "void" (frantic look back)
const tScream = () => T('s01b03+1.37');         // the scream-grimace peak (on "void"); the Void's hand freezes here

const add2 = (a, b, s = 1) => [a[0] + b[0] * s, a[1] + b[1] * s];
const U0 = [2.35, -6.4], V0 = [4.35, -13.4];     // frame-0 marks (stage local): user on the path, the Void on the crest
const UC0 = [2.24, -5.35], VC_OFF = [1.3, -1.75];// shot C: user at tC, the Void relative to the user (screen-right, close)

/** footfall times of the user's run / the Void's waddle (both shots share the phase functions) — for the cue file */
export function footfallsS01() {
  return { user: footfalls(T('s01'), T('s01.end'), 0, U_CPS, U_PH0), void: footfalls(T('s01'), T('s01.end'), 0, V_CPS, V_PH0) };
}
export const S01_TIMES = { tLook, tIns, tC, tVoidWord, tScream };

// ------------------------------------------------------------------------------------------------ phone feed
// The insert's screen: a generic social feed (plain white speech-bubble icon, no logo, no text), grey posts with
// little storm-cloud icons and ONE clearly sad grey post (big grey frowning face beside a storm cloud).
const FEED = { W: 256, H: 1024, VIS: Math.round(256 * SH / SW) };   // visible rows ~560 of a 1024 tall strip
const SAD = { y: 560, h: 236 };                                      // the sad post's rows in the strip
function rr(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
function cloud(g, x, y, s, col, rain) {
  g.fillStyle = col;
  for (const [dx, dy, r] of [[-0.55, 0.15, 0.42], [-0.05, -0.18, 0.55], [0.5, 0.08, 0.45], [0.1, 0.25, 0.42], [-0.35, 0.3, 0.35]]) { g.beginPath(); g.arc(x + dx * s, y + dy * s, r * s, 0, 7); g.fill(); }
  if (rain) { g.strokeStyle = col; g.lineWidth = s * 0.12; g.lineCap = 'round'; for (const dx of [-0.45, 0, 0.45]) { g.beginPath(); g.moveTo(x + dx * s, y + 0.75 * s); g.lineTo(x + dx * s - 0.12 * s, y + 1.05 * s); g.stroke(); } }
}
function feedCanvas() {
  const { W, H } = FEED, c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  g.fillStyle = '#dfe3ea'; g.fillRect(0, 0, W, H);
  const av = ['#b8bfcc', '#a9b4c6', '#c4c0cc', '#b0bac4'];
  const card = (y, h, k) => {
    g.fillStyle = '#f4f5f8'; rr(g, 8, y, W - 16, h, 12); g.fill();
    g.fillStyle = av[k % av.length]; g.beginPath(); g.arc(34, y + 28, 15, 0, 7); g.fill();
    g.fillStyle = '#5a6170'; rr(g, 58, y + 18, 70 + 30 * hash1(k * 3), 10, 5); g.fill();
    g.fillStyle = '#b7bdc8'; rr(g, 58, y + 33, 44 + 22 * hash1(k * 5), 7, 3.5); g.fill();
    cloud(g, W - 44, y + 30, 15, '#8a93a3', k % 2 === 0);
    g.fillStyle = '#c5cad3';
    for (let i = 0; i < 2; i++) { rr(g, 20, y + 56 + i * 16, (W - 48) * (i ? 0.55 : 0.9), 8, 4); g.fill(); }
    g.fillStyle = '#d0d4dc'; for (let i = 0; i < 4; i++) { g.beginPath(); g.arc(30 + i * 58, y + h - 14, 5, 0, 7); g.fill(); }
  };
  let y = 10, k = 0;
  while (y + (k % 2 ? 128 : 112) < SAD.y - 8) { const h = k % 2 ? 128 : 112; card(y, h, k); y += h + 10; k++; }
  if (y < SAD.y - 30) { card(y, SAD.y - 10 - y, k); k++; }
  // the sad post
  const sy = SAD.y, sh = SAD.h;
  g.fillStyle = '#eceef2'; rr(g, 8, sy, W - 16, sh, 14); g.fill();
  g.fillStyle = '#a3aab8'; g.beginPath(); g.arc(34, sy + 28, 15, 0, 7); g.fill();
  g.fillStyle = '#5a6170'; rr(g, 58, sy + 18, 92, 10, 5); g.fill();
  g.fillStyle = '#b7bdc8'; rr(g, 58, sy + 33, 52, 7, 3.5); g.fill();
  g.fillStyle = '#c9ced8'; rr(g, 20, sy + 52, W - 40, sh - 92, 12); g.fill();
  const fx = 92, fy = sy + 52 + (sh - 92) / 2, fr = 50;          // big grey frowning face
  g.fillStyle = '#9aa1ae'; g.beginPath(); g.arc(fx, fy, fr, 0, 7); g.fill();
  g.fillStyle = '#5c6372';
  for (const s of [-1, 1]) { g.beginPath(); g.ellipse(fx + s * 17, fy - 10, 6, 8, 0, 0, 7); g.fill(); }
  g.strokeStyle = '#5c6372'; g.lineWidth = 6; g.lineCap = 'round';
  g.beginPath(); g.arc(fx, fy + 30, 20, Math.PI * 1.18, Math.PI * 1.82); g.stroke();
  for (const s of [-1, 1]) { g.beginPath(); g.moveTo(fx + s * 8, fy - 31); g.lineTo(fx + s * 26, fy - 23); g.stroke(); }   // sad brows (inner ends up)
  g.fillStyle = '#c8dcf2'; g.beginPath(); g.ellipse(fx + 21, fy + 8, 4.5, 7, 0, 0, 7); g.fill();                               // a painted tear
  cloud(g, 186, fy - 8, 30, '#7d8696', true);                       // storm cloud
  g.fillStyle = '#e8d27a'; g.beginPath(); g.moveTo(190, fy + 14); g.lineTo(178, fy + 34); g.lineTo(188, fy + 33); g.lineTo(180, fy + 52); g.lineTo(200, fy + 26); g.lineTo(190, fy + 27); g.closePath(); g.fill();
  g.fillStyle = '#d0d4dc'; for (let i = 0; i < 4; i++) { g.beginPath(); g.arc(30 + i * 58, sy + sh - 16, 5, 0, 7); g.fill(); }
  y = sy + sh + 10; k = 7;
  while (y < H - 8) { const h = Math.min(k % 2 ? 128 : 112, H - 4 - y); card(y, h, k); y += h + 10; k++; }
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.wrapT = THREE.RepeatWrapping; tx.anisotropy = 4;
  tx.repeat.set(1, FEED.VIS / H);
  return tx;
}
function headerTex() {
  const c = document.createElement('canvas'); c.width = 256; c.height = 40;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 256, 40);
  g.fillStyle = '#9aa3b4'; rr(g, 12, 13, 22, 14, 3); g.fill();
  // plain speech-bubble icon (generic)
  g.fillStyle = '#6f8fd8'; rr(g, 112, 8, 32, 21, 8); g.fill();
  g.beginPath(); g.moveTo(119, 27); g.lineTo(116, 35); g.lineTo(127, 28); g.fill();
  g.fillStyle = '#c7cdd8'; g.beginPath(); g.arc(234, 20, 9, 0, 7); g.fill();
  g.fillStyle = '#e3e6ec'; g.fillRect(0, 38, 256, 2);
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; return tx;
}
function dropTex(kind) {
  const S = 128, c = document.createElement('canvas'); c.width = S; c.height = S;
  const g = c.getContext('2d');
  if (kind === 'blob') {       // a tear spread on the glass: a soft blurred wet spot, darker in the middle, a lens rim
    let gr = g.createRadialGradient(64, 64, 0, 64, 64, 62);
    gr.addColorStop(0, 'rgba(150,162,188,0.5)'); gr.addColorStop(0.45, 'rgba(176,188,210,0.46)');
    gr.addColorStop(0.78, 'rgba(206,216,234,0.34)'); gr.addColorStop(0.9, 'rgba(236,242,252,0.3)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(64, 64, 62, 0, 7); g.fill();
    gr = g.createRadialGradient(44, 40, 0, 44, 40, 18); gr.addColorStop(0, 'rgba(255,255,255,0.85)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(44, 40, 18, 0, 7); g.fill();
  } else {                     // a falling tear (teardrop, point up)
    const gr = g.createLinearGradient(40, 0, 88, 0); gr.addColorStop(0, 'rgba(170,200,240,0.75)'); gr.addColorStop(0.5, 'rgba(240,248,255,0.95)'); gr.addColorStop(1, 'rgba(150,180,230,0.75)');
    g.fillStyle = gr; g.beginPath(); g.moveTo(64, 8); g.bezierCurveTo(70, 40, 96, 64, 96, 86); g.arc(64, 86, 32, 0, Math.PI); g.bezierCurveTo(32, 64, 58, 40, 64, 8); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.95)'; g.beginPath(); g.ellipse(54, 82, 6, 10, -0.3, 0, 7); g.fill();
  }
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; return tx;
}

// ------------------------------------------------------------------------------------------------ foreground rise
// The rise the user runs over in shot A (it cuts them at the hips): a smooth mound in front of the lens that travels
// with the camera (untextured pastel ground: its motion can't read), path cream in the middle, mint at the sides.
// Uses the EDGE terrain's own material so it shades, hazes and grades exactly like the real ground.
function buildRise(set, Hc, uc, vPath) {
  const NU = 30, NV = 64, U0r = 0.08, U1r = uc + 0.9, V1 = 1.3;
  const pos = [], col = [], idx = [];
  const cream = new THREE.Color(0xf4e0c6), creamE = new THREE.Color(0xe9cfae), mint = new THREE.Color(0x7fd6ad), mintL = new THREE.Color(0xa6e6c4), mintD = new THREE.Color(0x6cc79f);
  const hAt = (u, v) => {
    const front = u <= uc ? 0.5 - 0.5 * Math.cos(Math.PI * clamp((u - U0r) / (uc - U0r))) : 1;
    const back = u > uc ? 0.5 + 0.5 * Math.cos(Math.PI * clamp((u - uc) / (U1r - uc))) : 1;
    const side = 1 - 0.55 * (v - vPath) * (v - vPath);                        // a convex crest: it falls away at the sides
    const tuft = 0.006 * (Math.sin(v * 61 + 1.3) + 0.6 * Math.sin(v * 137 + 0.4)) * smooth(clamp((Math.abs(v - vPath) - 0.12) / 0.1));
    return (Hc * (0.62 + 0.38 * front) * side + tuft * front) * back;
  };
  // the path runs from the bottom centre of the frame up over the crest to the kid
  const pc = (u) => lerp(0.3 * vPath, vPath, smooth(clamp(u / uc))), pw = (u) => 0.04 + 0.025 * clamp(u / uc);
  for (let i = 0; i <= NU; i++) for (let j = 0; j <= NV; j++) {
    const u = U0r + (U1r - U0r) * (i / NU), v = -V1 + 2 * V1 * (j / NV), dv = Math.abs(v - pc(u));
    pos.push(v, hAt(u, v), u);
    const path = 1 - smooth(clamp((dv - pw(u)) / 0.07));
    const near = 1 - smooth(clamp((u - 0.3) / Math.max(0.1, uc - 0.3)));          // toward the lens: deeper, greener
    const c = mint.clone().lerp(mintL, 0.3 + 0.3 * Math.sin(u * 7.1 + v * 5.3) * Math.sin(v * 3.1 - u * 2.2)).lerp(mintD, 0.45 * near)
      .lerp(creamE, path * 0.9).lerp(cream, path * smooth(clamp((pw(u) - dv) / 0.05)));
    c.multiplyScalar(0.94 + 0.08 * smooth(clamp((u - uc + 0.35) / 0.35)));          // the crest catches the light
    col.push(c.r, c.g, c.b);
  }
  for (let i = 0; i < NU; i++) for (let j = 0; j < NV; j++) { const a = i * (NV + 1) + j, b = a + 1, c = a + NV + 1, d = c + 1; idx.push(a, b, c, b, d, c); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx); g.computeVertexNormals();
  if (g.attributes.normal.array[1] < 0) { g.index.array.reverse(); g.computeVertexNormals(); }
  const mat = (set.props.terrain && set.props.terrain.userData.material) || new THREE.MeshLambertMaterial({ vertexColors: true });
  const m = new THREE.Mesh(g, mat); m.name = 's01.rise'; m.renderOrder = -20; m.frustumCulled = false;
  // a fringe of grass tufts and a few tiny pastel flowers along the crest (not on the bare path): an organic edge
  const N = 230, blade = new THREE.BufferGeometry();
  blade.setAttribute('position', new THREE.Float32BufferAttribute([-0.5, 0, 0, 0.5, 0, 0, 0.05, 1, 0.0], 3)); blade.computeVertexNormals();
  const gm = new THREE.InstancedMesh(blade, new THREE.MeshLambertMaterial({ color: 0xffffff, side: THREE.DoubleSide }), N);
  const fl = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), 24);
  const M4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), cc = new THREE.Color();
  let nf = 0;
  for (let i = 0; i < N; i++) {
    const slope = i % 5 === 4;                                         // a few scattered down the near slope
    const u = slope ? lerp(0.45, uc - 0.2, hash1(i * 7 + 2)) : uc - 0.22 * hash1(i * 7 + 2) ** 1.5;
    let v = -0.75 + 1.5 * hash1(i * 3 + 1); const gap = pw(u) + 0.05; if (Math.abs(v - pc(u)) < gap) v = pc(u) + Math.sign(v - pc(u) || 1) * (gap + 0.03);
    const h = (slope ? 0.012 : 0.03) + (slope ? 0.018 : 0.045) * hash1(i * 11 + 3), w = (slope ? 0.004 : 0.007) + 0.004 * hash1(i * 13 + 5);
    e.set(-0.25 + 0.5 * hash1(i * 17 + 7), 6.28 * hash1(i * 19 + 11), -0.35 + 0.7 * hash1(i * 23 + 13)); q.setFromEuler(e);
    M4.compose(new THREE.Vector3(v, hAt(u, v) - 0.004, u), q, new THREE.Vector3(w, h, w)); gm.setMatrixAt(i, M4);
    gm.setColorAt(i, cc.copy(mintD).lerp(mintL, hash1(i * 29 + 17)));
    if (!slope && i % 7 === 0 && nf < 24) {
      M4.compose(new THREE.Vector3(v, hAt(u, v) + h * 0.85, u + 0.002), q.identity(), new THREE.Vector3(0.007, 0.007, 0.007)); fl.setMatrixAt(nf, M4);
      fl.setColorAt(nf, cc.set([0xffd9b8, 0xe6d2ff, 0xfff4d6, 0xffc7dc][nf % 4])); nf++;
    }
  }
  fl.count = nf;
  m.add(gm, fl);
  return m;
}
/** a soft warm wash over the upper sky (peach-gold), drawn behind everything within 150 m */
function buildSkyWash() {
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, 'rgba(255,196,140,0.62)'); gr.addColorStop(0.28, 'rgba(255,206,150,0.42)'); gr.addColorStop(0.5, 'rgba(255,214,165,0.12)'); gr.addColorStop(0.62, 'rgba(255,214,165,0)'); gr.addColorStop(1, 'rgba(255,214,165,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: tx, transparent: true, depthWrite: false, fog: false, toneMapped: true }));
  m.renderOrder = 2; m.frustumCulled = false; m.name = 's01.skywash';
  return m;
}

// ------------------------------------------------------------------------------------------------ the scene
export default {
  id: 's01',
  async setup(app) {
    const set = await app.set('EDGE');
    const user = await app.char('USER'), vd = await app.char('VOID');
    const st = { set, scene: set.scene, user, vd, look: {} };
    st.own = ownedGroup(st, 's01.own');
    st.fx = new Particles({ max: 90, intensity: 1.5 }); st.own.add(st.fx.mesh);
    // phone insert overlay (follows the rig phone's matrixWorld; only drawn in the insert)
    const ov = st.ov = new THREE.Group(); ov.matrixAutoUpdate = false; st.own.add(ov);
    const mk = (geo, map, z, ro) => { const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map, transparent: true, depthWrite: false, toneMapped: true })); m.position.z = z; m.renderOrder = ro; ov.add(m); return m; };
    st.feed = feedCanvas();
    const hh = SH * 40 / FEED.VIS;                                  // header height (40 px of a ~560 px tall screen)
    st.feedM = mk(new THREE.PlaneGeometry(SW, SH), st.feed, PH_D / 2 + 0.0009, 7);
    st.hdrM = mk(new THREE.PlaneGeometry(SW, hh), headerTex(), PH_D / 2 + 0.0011, 8); st.hdrM.position.y = SH / 2 - hh / 2;
    st.blob = mk(new THREE.CircleGeometry(0.5, 32), dropTex('blob'), PH_D / 2 + 0.0016, 9);
    st.drip = mk(new THREE.PlaneGeometry(1, 1), dropTex('drip'), PH_D / 2 + 0.006, 9);
    for (const m of [st.feedM, st.hdrM]) m.material.transparent = false;
    st.scene.add(st.own);
    // ---- frame-0 composition: the user's eyes at (250, 430) left of centre, hips at the crest line (~840), the Void's
    // eyes at (520, 425) right of centre with clear sky between the kid's hair and its hood, hood top below the title
    {
      const uW0 = G(set, ...U0), vW0 = G(set, ...V0);
      user.update(0, { pos: uW0, yaw: EDGE.Y(YAW_RUN + 0.16), walk: { amount: 1, style: 'run', phase: U_PH0 } });
      vd.update(0, { pos: vW0, yaw: EDGE.Y(YAW_RUN + 0.02), walk: { amount: 1, style: 'waddle', phase: V_PH0 } });
      const ue = user.anchor('eyes'), uh = user.anchor('hip'), ve = vd.anchor('eyes'), vt = vd.anchor('hoodTop');
      const guessL = add2(U0, D, 2.5), cg = G(set, ...guessL); cg[1] += 0.8;
      const lk = [ue.x * 0.5 + ve.x * 0.5, ue.y + 0.2, ue.z * 0.5 + ve.z * 0.5];
      const f = fitCam([[ue, 222, 458, 1], [uh, 232, 850, 0.6], [ve, 530, 440, 1], [vt, 534, 330, 0.7]], 44, cg, lk, { reg: 0.1, yMin: cg[1] - 0.15, yMax: cg[1] + 0.2 });
      st.camA = f;
      console.log(`s01 frame0 fit err ${f.err.toFixed(1)}px pos ${EDGE.L(f.pos).map((v) => v.toFixed(2))} look ${EDGE.L(f.look).map((v) => v.toFixed(2))}`);
      // the rise: its crest line lands at y ~842 (the hips) 1.05 m in front of the lens
      const cam = new THREE.PerspectiveCamera(44, 720 / 1280, 0.05, 400); cam.position.set(...f.pos); cam.lookAt(...f.look); cam.updateMatrixWorld();
      const dir = V3(...f.look).sub(V3(...f.pos)).setY(0).normalize(), uc = 1.05;
      const ray = new THREE.Vector3(0, 1 - 2 * 856 / 1280, 0.5).unproject(cam).sub(cam.position).normalize();
      const s = uc / Math.max(1e-3, ray.clone().setY(0).dot(dir));
      const g0 = set.groundAt(f.pos[0], f.pos[2]);
      st.riseH = f.pos[1] + ray.y * s - g0; st.riseU = uc;
      // the path on the rise runs up to where the kid is (their lateral offset projected back to the crest distance)
      const camG = V3(f.pos[0], g0, f.pos[2]), rel = uh.clone().sub(camG), along = rel.dot(dir), xL = V3(dir.z, 0, -dir.x);
      st.riseV = rel.dot(xL) * uc / Math.max(0.5, along);
      st.rise = buildRise(set, st.riseH, uc, st.riseV); st.own.add(st.rise);
      console.log(`s01 rise crest ${st.riseH.toFixed(2)} m at ${uc} m (cam ${(f.pos[1] - g0).toFixed(2)} m up)`);
    }
    // thought-seeds drifting in the light (the set's seed sprite), and the warm wash on the upper sky
    const smap = set.props.seeds && set.props.seeds.mat ? set.props.seeds.mat.uniforms.uMap.value : null;
    st.seeds = [0, 1, 2].map(() => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: smap, color: 0xfff0d8, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); st.own.add(s); return s; });
    st.wash = buildSkyWash(); st.own.add(st.wash);
    // ---- shot C (CHASELOW, 24 mm): fitted at the "void" moment — the kid small lower-left (head ~y 600), the Void
    // towering at right, hood up to ~y 170; the camera a little to the kid's left-front so the look back over the LEFT
    // shoulder turns the face TOWARD the lens (3/4), not away
    {
      const tr = tVoidWord(), s = SPD * (tr - tC());
      const uL = add2(UC0, D, s), vL = add2(uL, VC_OFF);
      user.update(tr, { pos: G(set, ...uL), yaw: EDGE.Y(YAW_RUN - 0.3), walk: { amount: 1, style: 'run', phase: tr * U_CPS + U_PH0 } });
      vd.update(tr, { pos: G(set, ...vL), yaw: EDGE.Y(YAW_RUN - 0.12), walk: { amount: 1, style: 'waddle', phase: tr * V_CPS + V_PH0 } });
      const ue = user.anchor('eyes'), ve = vd.anchor('eyes'), vt = vd.anchor('hoodTop');
      const c = EDGE.CAM.CHASELOW, sc = 0.78 * s;
      const g = EDGE.W(c.pos[0] + 0.3 + D[0] * sc, c.pos[1], c.pos[2] + D[1] * sc);
      const f = fitCam([[ue, 235, 615, 1], [ve, 470, 335, 1], [vt, 470, 175, 0.8]], 60, g, ve.toArray(), { reg: 0.5, yMin: 0.45, yMax: 0.9 });
      st.camC = f; st.camCt = tr;
      console.log(`s01 CHASELOW fit err ${f.err.toFixed(1)}px pos ${EDGE.L(f.pos).map((v) => v.toFixed(2))}`);
    }
    return st;
  },

  async update(t, app, st) {
    st.__t = t;
    const { set, user, vd } = st;
    const cam = app.camera;
    const insert = t >= tIns() && t < tC();
    const shotC = t >= tC();
    cast(app, st.scene, insert ? ['USER'] : ['USER', 'VOID']);

    // ---------------------------------------------------------------------------- blocking (stage local)
    let uL, vL, camPos, camLook, fov;
    const dwC = WD(D[0], D[1]);
    if (!shotC) {
      const s = SPD * t;
      uL = add2(U0, D, s);
      vL = add2(V0, D, s);
      const push = 0.3 * smooth((t - T('s01b02')) / 1.1);           // drift a touch closer on the narration
      const A = st.camA, cp = V3(...A.pos).addScaledVector(dwC, s), cl = V3(...A.look).addScaledVector(dwC, s);
      const toU = cl.clone().sub(cp).setY(0).normalize();
      cp.addScaledVector(toU, push); cp.y -= 0.03 * push;
      camPos = cp; camLook = cl; fov = 44;
    } else {
      const s = SPD * (t - tC());
      uL = add2(UC0, D, s);
      vL = add2(uL, VC_OFF);
      const C = st.camC, sc = 0.78 * SPD * (t - st.camCt);
      camPos = V3(...C.pos).addScaledVector(dwC, sc); camLook = V3(...C.look).addScaledVector(dwC, sc); fov = 60;
    }
    const uW = G(set, uL[0], uL[1]), vW = G(set, vL[0], vL[1]);
    const yawW = EDGE.Y(YAW_RUN + (shotC ? -0.3 : 0.16));
    const vel = WD(D[0], D[1]).multiplyScalar(SPD);                // world velocity of both runners
    const fwd = V3(Math.sin(yawW), 0, Math.cos(yawW)), left = V3(Math.cos(yawW), 0, -Math.sin(yawW)), up = V3(0, 1, 0);

    if (!insert) applyShot(cam, { pos: camPos.toArray(), look: camLook.toArray(), fov, drift: t < 0.2 ? 0 : shotC ? 0.3 : 0.2 }, t);

    // ---------------------------------------------------------------------------- USER
    const uPh = t * U_CPS + U_PH0;
    // look back over the LEFT shoulder: <= 0.58 so the face stays a readable 3/4 (eye + gasp visible)
    const lookA = k(t, [[tLook() - 0.02, 0], [tLook() + 0.16, 0.58, 'out'], [tLook() + 0.42, 0.58], [tLook() + 0.56, 0, 'inOut']]);
    const lookC = k(t, [[tScream() - 0.2, 0], [tScream() - 0.02, 0.56, 'out'], [tScream() + 0.4, 0.58], [tScream() + 0.6, 0.06, 'inOut']]);
    const lookBack = shotC ? lookC : lookA;
    const phoneUp = shotC ? 0 : k(t, [['s01b02+0.55', 0], ['s01b02+0.95', 0.78, 'inOut'], [tIns(), 1]]);
    // provisional user update (no gaze) -> eye / phone anchors for this frame (pure: no previous-frame state)
    const posePre = { pos: uW, yaw: yawW, walk: { amount: 1, style: 'run', phase: uPh }, body: { lookBack }, extra: { phoneUp } };
    user.update(t, posePre);
    const userEyes0 = user.anchor('eyes');
    const phoneScr0 = user.anchor('phoneScreen');
    // eyes lead the head by ~3 frames
    const eyesBack = shotC ? (t > tScream() - 0.3 && t < tScream() + 0.5) : (t > tLook() - 0.14 && t < tLook() + 0.48);
    const glancePhone = !shotC && t > T('s01b02+0.5');
    // the face, beat by beat
    const EEK = UX([['terror', 0.6], ['nervous', 0.4]], { lidU: 1.48, lidL: 0.08, pupil: 0.42, browIn: 1.05, browOut: 0.95, browSq: 0.08, browMid: 0.3, mOpen: 0.26, mWide: 0.95, mSmile: -0.3, mClench: 0.55, mTeethU: 0.9, mTeethL: 0.75, mTremble: 0.5, wet: 1, autoBlink: 0, gazePitch: -0.02 });
    const SOBRUN = UX([['sob', 0.55], ['terror', 0.45]], { lidU: 0.85, mOpen: 0.45, autoBlink: 0 });
    let face;
    if (!shotC) {
      const hitch = Math.max(0, Math.sin(Math.PI * 2 * (uPh * 0.5))) ** 6;    // a hitched sob every second step
      const WIDE = UX('terror', { lidU: 1.58, lidL: 0, pupil: 0.3, browIn: 1.15, browOut: 1.0, mOpen: 0.42, autoBlink: 0 });
      face = k(t, [
        [0, EEK], [tLook() - 0.05, EEK],
        [tLook() + 0.06, UX('gasp', { lidU: 1.5, pupil: 0.38, autoBlink: 0 }), 'out'],
        [tLook() + 0.44, UX('gasp', { lidU: 1.5, pupil: 0.36, mOpen: 0.62, autoBlink: 0 })],
        [tLook() + 0.56, WIDE, 'out'], [tLook() + 0.78, WIDE],             // snap forward, even wider: held 5 frames
        [tLook() + 1.1, UX('terror', { lidU: 1.45, autoBlink: 0 }), 'inOut'],
        ['s01b02', SOBRUN, 'inOut'],
        ['s01b02+0.5', SOBRUN],
        ['s01b02+0.9', UX([['sob', 0.45], ['scroll', 0.55]], { lidU: 0.62, autoBlink: 0 }), 'inOut'],
      ]);
      face = { ...face, mOpen: face.mOpen + 0.25 * hitch * smooth((t - T('s01b02') + 0.6) / 0.6) };
    } else {
      // "crying": chin crumples, eyes squeezed; "void": a frantic look back into a silent scream-grimace (teeth, lids
      // sky-high, pinned pupils) held 9 frames, then a terrified face forward again
      const SCREAM = UX('scream', { lidU: 1.6, lidL: 0, lidDrop: 1, pupil: 0.22, mOpen: 0.95, mWide: 1, mTeethU: 1, mTeethL: 1, mClench: 0.25, browIn: 1.2, browOut: 1.05, mTremble: 0.5, autoBlink: 0 });
      face = k(t, [
        [tC(), UX('sob', { lidU: 0.12 })], ['s01b03+0.45', UX('sob', { lidU: 0.14 })],
        ['s01b03+0.62', UX([['terror', 0.7], ['sob', 0.3]], { autoBlink: 0 }), 'inOut'],
        ['s01b03+0.95', UX([['terror', 0.6], ['gulp', 0.4]], { autoBlink: 0 }), 'inOut'],     // the sneaker scuff
        [tScream() - 0.2, UX('terror', { lidU: 1.5, autoBlink: 0 }), 'inOut'],
        [tScream() - 0.05, SCREAM, 'out'], [tScream() + 0.36, SCREAM],                      // locked 9+ frames
        [tScream() + 0.6, UX('terror', { lidU: 1.42, mOpen: 0.55, autoBlink: 0 }), 'inOut'],
      ]);
    }
    // sob shakes the shoulders on "crying"
    const sobShake = shotC ? bump(t, tC() - 0.05, T('s01b03+0.6'), 0.3) : 0;
    const shrug = (shotC ? 0.15 : 0.12) + 0.35 * sobShake * (0.5 + 0.5 * Math.sin((t - tC()) * 2 * Math.PI * 5.5)) + (shotC ? 0.35 * bump(t, tScream() - 0.1, tScream() + 0.6, 0.2) : 0);
    const scuff = shotC ? bump(t, T('s01b03+0.86'), T('s01b03+1.12'), 0.35) : 0;
    const flail = shotC ? lerp(0.55, 1.0, smooth((t - T('s01b03+0.55')) / 0.4)) : 0.45;
    // ---------------------------------------------------------------------------- VOID
    if (!insert) {
      const vPh = t * V_CPS + V_PH0;
      const userEyes = userEyes0;
      // shot C: it sees the kid start to turn -> eyes brighten, two finger-wiggles (a tiny hopeful wave) -> the kid's
      // scream peaks -> the hand freezes mid-wiggle (held), the outer brow-wisps sink, the lids sag
      const tw0 = tScream() - 0.3;
      const hurt = shotC ? smooth((t - tScream() - 0.06) / 0.45) : 0;
      const bright = shotC ? smooth((t - tw0 + 0.08) / 0.12) * (1 - 0.6 * hurt) : bump(t, tLook(), tLook() + 1.0, 0.2) * 0.6;
      const wu = clamp((t - tw0) / 0.3);                                  // 2 wiggles over 0.3 s, frozen at the scream peak
      const wig = shotC && t > tw0 ? Math.sin(Math.min(wu, 0.9) * 2 * Math.PI * 2) : 0;
      const face0 = VX('hopeful', { lidU: 1.16, browIn: 0.72, browOut: 0.12, mOpen: 0.12, mRound: 0.7, mSmile: 0.05, autoBlink: t < 0.3 ? 0 : 1 });
      const vface = { ...face0 };
      vface.lidU = lerp(face0.lidU, 0.9, hurt) + 0.14 * bright;
      vface.browOut = lerp(face0.browOut, -0.5, hurt); vface.browIn = lerp(face0.browIn, 0.9, hurt);
      vface.lidSad = 0.4 * hurt; vface.mRound = lerp(0.7, 0.3, hurt); vface.mOpen = lerp(0.12, 0.04, hurt);
      vface.mSmile = 0.05 + 0.25 * bright * (1 - hurt) - 0.15 * hurt;
      vd.update(t, {
        pos: vW, yaw: EDGE.Y(YAW_RUN + (shotC ? -0.12 : 0.02)),
        walk: { amount: 1, style: 'waddle', phase: vPh },
        body: { bounce: jiggle(vPh, V_CPS, 0.014), lean: 0.03, recoil: -0.04 + 0.05 * hurt },
        head: { pitch: 0.05, yaw: shotC ? -0.1 : 0.04 },
        gaze: userEyes,
        face: vface,
        // the half-raised "wait" hand: in frame 0 its LEFT (screen-right, clear of the kid); in shot C its RIGHT, raised
        // high enough to show over the kid's hair, so the wiggle and the freeze read in the gap between them
        ...(shotC ? {
          armR: { preset: 'wave', from: 'rest', mix: 0.74 + 0.06 * bright * (1 - hurt), offset: WD(-0.25, 0.35).multiplyScalar(0.3).toArray(), hand: { spread: 0.5 + 0.25 * wig, curl: 0.12 + 0.3 * Math.max(0, wig), thumb: 0.6 } },
          armL: { preset: 'rest', offset: WD(-0.2, 0.25).multiplyScalar(0.25).toArray(), hand: { curl: 0.75, thumb: 0.85, cup: 0.5, spread: 0.05 } },
        } : {
          armL: { preset: 'wave', from: 'rest', mix: 0.58 + 0.07 * bright, hand: { spread: 0.55, curl: 0.12, thumb: 0.6 } },
          armR: { preset: 'rest', offset: WD(0.2, 0.25).multiplyScalar(0.25).toArray(), hand: { curl: 0.75, thumb: 0.85, cup: 0.5, spread: 0.05 } },
        }),
        extra: { hem: 0.5, eyeGlow: 1 + 0.45 * bright, motes: 1.2, rim: 1.1 },
        blinkAt: shotC ? [tScream() + 0.75] : [2.15],
      });
    }

    const vEyes = insert ? null : vd.anchor('eyes');
    // the phone hugged to the sternum, screen tipped up so its cool glow lights the chin (LEFT hand, never pumping);
    // the RIGHT arm pumps with a closed fist
    const phonePalm = up.clone().multiplyScalar(0.62).addScaledVector(fwd, -0.72).addScaledVector(left, -0.18).normalize();
    const phoneFing = fwd.clone().multiplyScalar(0.72).addScaledVector(up, 0.55).addScaledVector(left, -0.3).normalize();
    const uPose = {
      pos: uW, yaw: yawW,
      walk: { amount: 1, style: 'run', phase: uPh, flail },
      body: { lookBack, shrug, tremble: 0.25 + 0.4 * sobShake, lean: 0.06 * scuff, bounce: -0.035 * scuff, flinch: 0.25 * scuff, pant: 0.6 },
      head: { pitch: glancePhone ? 0.16 * smooth((t - T('s01b02+0.5')) / 0.3) : 0 },
      gaze: eyesBack && vEyes ? vEyes : glancePhone ? phoneScr0 : (insert ? null : cam.position.clone().add(V3(0, shotC ? 0.3 : 0.08, 0))),
      face,
      extra: { tears: 1, phone: 0.95, phoneUp, glassesTilt: 0.07 + 0.03 * Math.sin(uPh * Math.PI * 2), screen: 'feed', scroll: t * 0.15 },
      armL: insert ? { preset: 'look', palm: V3(0, 0.93, 0).addScaledVector(fwd, -0.37).toArray(), fingers: fwd.clone().multiplyScalar(0.92).add(V3(0, 0.38, 0)).toArray(), offset: fwd.clone().multiplyScalar(0.04).add(V3(0, -0.02, 0)).toArray() }
        : shotC ? undefined : { preset: 'clutch', palm: phonePalm.toArray(), fingers: phoneFing.toArray(), offset: fwd.clone().multiplyScalar(0.06).add(V3(0, 0.07, 0)).toArray(), hand: { curl: 0.35 } },
      armR: { hand: { curl: 1, point: 0, thumb: 0.3, spread: 0, cup: 0.3, thumbTo: [-0.008, 0.045, -0.034], thumbW: 1 } },   // a real fist: thumb over the fingers
    };
    if (insert) { uPose.gaze = null; uPose.extra = { ...uPose.extra, ...insertThumb(t).extra }; }
    let lag = null;
    if (insert) {   // lagged phone poses (for the insert camera), sampled BEFORE the final update at t
      lag = [];
      for (const [dt, w] of [[0.07, 0.45]]) {
        user.update(t - dt, { ...uPose, extra: { ...uPose.extra, ...insertThumb(t - dt).extra } });
        user.phone.updateWorldMatrix(true, false);
        lag.push([user.phone.matrixWorld.clone(), w]);
      }
    }
    user.update(t, uPose);

    // ---------------------------------------------------------------------------- insert camera + overlay
    st.ov.visible = insert;
    if (insert) {
      // camera off the phone's +Z axis, rolled with the phone, a little ABOVE and to the right of the screen normal (the
      // cradling forearm/cuff sits in front of the lower-left corner: from up here it drops below the glass); it
      // follows a slightly lagged phone pose so the run's bob and the hand tremor read as the phone moving in frame
      user.phone.updateWorldMatrix(true, false);
      const P = [], Q = [];
      for (const [m, w] of [...lag, [user.phone.matrixWorld.clone(), 0.55]]) {
        P.push([new THREE.Vector3().setFromMatrixPosition(m), w]);
        Q.push([new THREE.Quaternion().setFromRotationMatrix(m), w]);
      }
      const pos = new THREE.Vector3(), q = Q[0][0].clone();
      for (const [p, w] of P) pos.addScaledVector(p, w);
      q.slerp(Q[1][0], 0.55);
      const n = new THREE.Vector3(0, 0, 1).applyQuaternion(q), upP = new THREE.Vector3(0, 1, 0).applyQuaternion(q), rgt = upP.clone().cross(n).normalize();
      const scr = pos.clone().addScaledVector(n, PH_D / 2).addScaledVector(upP, 0.012);
      const R = 0.215, el = 0.34, az = 0.36;
      cam.position.copy(scr).addScaledVector(n, R * Math.cos(el) * Math.cos(az)).addScaledVector(upP, R * Math.sin(el)).addScaledVector(rgt, R * Math.sin(az) * Math.cos(el));
      cam.up.copy(upP); cam.fov = 46; cam.updateProjectionMatrix();
      cam.lookAt(scr.clone().addScaledVector(upP, 0.012).addScaledVector(rgt, 0.004)); cam.updateMatrixWorld();
      // overlay follows the (current) phone
      user.phone.updateWorldMatrix(true, false);
      st.ov.matrix.copy(user.phone.matrixWorld); st.ov.matrixWorldNeedsUpdate = true;
      const I = insertState(t);
      st.feed.offset.y = 1 - (I.scrollPx + FEED.VIS) / FEED.H;
      // the tear: falls, lands on the sad post, blooms into a soft blur; the second flick smears it upward
      const S = 0.0105;
      st.drip.visible = I.fall > 0 && I.fall < 1;
      if (st.drip.visible) {
        const u = I.fall;
        st.drip.position.set((I.dropU - 0.5) * SW, lerp(SH * 0.62, (0.5 - I.dropV) * SH, u * u), PH_D / 2 + lerp(0.02, 0.002, u));
        st.drip.scale.set(S * 0.8, S * 1.3, 1);
      }
      st.blob.visible = I.land > 0;
      if (st.blob.visible) {
        const r = S * 2 * (0.7 + 0.6 * smooth(I.land)) * (1 + 0.15 * Math.max(0, 1 - I.land * 3));
        st.blob.position.set((I.dropU - 0.5) * SW, (0.5 - I.dropV) * SH + 0.5 * SH * I.smearV, PH_D / 2 + 0.0016);
        st.blob.scale.set(r * (1 - 0.22 * I.smear), r * (1 + 1.8 * I.smear), 1);
        st.blob.material.opacity = 1 - 0.4 * I.smear;
      }
    }

    // ---------------------------------------------------------------------------- frame-A dressing: rise, wash, seeds
    const shotA = !insert && !shotC;
    st.rise.visible = shotA; st.wash.visible = shotA;
    for (const s of st.seeds) s.visible = shotA;
    if (shotA) {
      const dir = camLook.clone().sub(camPos).setY(0).normalize();
      st.rise.position.set(camPos.x, set.groundAt(camPos.x, camPos.z), camPos.z);
      st.rise.rotation.set(0, Math.atan2(dir.x, dir.z), 0);
      // the wash: a 150 m-away card filling the frame (its gradient tops out over the title and fades by mid-frame)
      const cf = camLook.clone().sub(camPos).normalize(), Dd = 150, hgt = 2 * Dd * Math.tan(22 * Math.PI / 180) * 1.08;
      st.wash.position.copy(camPos).addScaledVector(cf, Dd); st.wash.quaternion.copy(cam.quaternion); st.wash.scale.set(hgt * 0.62, hgt, 1);
      // three thought-seeds drifting across in the light (screen-anchored: they ride the same breeze as the chase)
      const seedDef = [[95, 560, 3.6, 0.2, 0.15], [655, 690, 4.4, 0.24, -0.1], [330, 352, 11, 0.5, 0.08]];
      seedDef.forEach(([x, y, d, sz, dx], i) => {
        const xs = x + 60 * dx * t + 10 * Math.sin(t * 0.9 + i * 2), ys = y + 14 * Math.sin(t * 1.1 + i * 1.7) - 8 * t;
        const p = new THREE.Vector3(xs / 360 - 1, 1 - ys / 640, 0.5).unproject(cam).sub(cam.position).normalize();
        st.seeds[i].position.copy(cam.position).addScaledVector(p, d);
        st.seeds[i].scale.setScalar(sz * (1 + 0.06 * Math.sin(t * 2.3 + i)));
        st.seeds[i].material.opacity = 0.85;
        st.seeds[i].material.rotation = 0.3 * Math.sin(t * 0.8 + i);
      });
    }

    // ---------------------------------------------------------------------------- particles: tear glints, star breath
    st.fx.begin();
    if (!insert) {
      const ue = user.anchor('eyes');
      // two tears flying off sideways as bright glints (one pair already in flight on frame 0)
      const glints = [-0.16, -0.1, 0.42, 0.95, 1.55, 2.2, 2.75, 5.12, 5.3, 5.6, 6.2, 6.7, 7.1];
      glints.forEach((tb, i) => {
        const age = t - tb, L = 0.5;
        if (age < 0 || age > L) return;
        const s = i % 2 ? 1 : -1;
        // a flung tear keeps the runner's velocity (minus a little air drag): it peels off sideways from the eye
        const o = ue.clone().addScaledVector(left, s * 0.075).add(V3(0, -0.01, 0)).addScaledVector(fwd, 0.03);
        const p = o.addScaledVector(left, s * 0.85 * age).addScaledVector(vel, -0.6 * age * age).add(V3(0, 0.45 * age - 2.4 * age * age, 0));
        const a = smooth(age / 0.05) * smooth((L - age) / 0.18);
        st.fx.add(p.toArray(), 0.075 + 0.02 * hash1(i), 0xf2f8ff, a, i, CELL.star);
      });
      // star-breath: a little puff of 3-4 motes from its mouth on each footfall (shot C)
      if (shotC) {
        const mo = vd.anchor('mouthOut') || vd.anchor('mouth'), mm = vd.anchor('mouth');
        const md = mo.clone().sub(mm).normalize();
        footfalls(tC() - 1.2, t + 0.01, 0, V_CPS, V_PH0).forEach((tf, i) => {
          if (t - tf > 1.3) return;
          st.fx.burst({ t, seed: 70 + i, at: tf, count: 3 + (i % 2), jitter: 0.03, life: 1.25,
            origin: mm.clone().addScaledVector(md, 0.2).addScaledVector(vel, tf - t).toArray(),
            vel: [md.x * 0.35, 0.42, md.z * 0.35], spread: [0.22, 0.14, 0.22], drag: 1.4, size: [0.07, 0.11],
            color: [0xd8c8ff, 0xbfefff, 0xffffff], alpha: 0.9, fade: [0.08, 0.5], cell: CELL.star, twinkle: true, spin: 0.6 });
        });
      }
    }
    st.fx.end();

    // ---------------------------------------------------------------------------- set + look
    const mid = [(uW[0] + vW[0]) / 2, 0, (uW[2] + vW[2]) / 2];
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t), voidPos: vW, voidRadius: shotC ? 24 : 17, shadowAt: mid,
      seeds: 0.85, sunGlow: shotA ? 1.2 : 1, keyMul: shotA ? 1.2 : 1.08, fillMul: 1.12 });
    st.look = lookFor('s01', set.look);
    if (shotA) st.look = { ...st.look, warm: (st.look.warm || 0) + 0.04 };
    if (insert) st.look = { ...st.look, bloomThreshold: 0.98, bloom: 0.35, vignette: 0.2 };
  },
};

// ------------------------------------------------------------------------------------------------ insert timing
// Relative to the cut on "Twitter": flick 1 brings the sad post up; the tear falls and blooms on it; flick 2 drags
// through it (smear) and scrolls on. The thumb stays in the lower half of the glass (no over-stretch).
function insertState(t) {
  const a = tIns();
  const r = (x) => a + x;
  const flick = (t0, t1, fromV, toV) => { const u = clamp((t - t0) / (t1 - t0)); return lerp(fromV, toV, smooth(u)); };
  const f1 = [r(0.12), r(0.42)], f2 = [r(0.98), r(1.28)];
  const press = (w) => clamp((t - w[0] + 0.06) / 0.06) * clamp((w[1] + 0.06 - t) / 0.06);
  const tap = Math.max(press(f1), press(f2));
  let tv;
  if (t < f1[1] + 0.06) tv = flick(f1[0], f1[1], 0.78, 0.5);
  else if (t < f2[0] - 0.1) tv = lerp(0.5, 0.78, smooth((t - f1[1] - 0.06) / (f2[0] - 0.1 - f1[1] - 0.06)));
  else tv = flick(f2[0], f2[1], 0.78, 0.48);
  const tu = 0.52 + 0.02 * Math.sin((t - a) * 3);
  // the thumb comes over the glass only for the flicks (between them it rests off the screen edge)
  const over = Math.max(bump(t, f1[0] - 0.12, f1[1] + 0.14, 0.4), bump(t, f2[0] - 0.12, f2[1] + 0.14, 0.4));
  // content scroll in canvas px: the sad post starts just under the fold, flick 1 centres it, flick 2 throws it up
  const P = FEED.VIS;
  const s0 = SAD.y - 0.92 * P, s1 = SAD.y + SAD.h / 2 - 0.47 * P, s2 = s1 + 0.62 * P;
  let scrollPx;
  if (t < f1[0]) scrollPx = s0;
  else if (t < f1[1] + 0.2) scrollPx = lerp(s0, s1, smooth(clamp((t - f1[0]) / (f1[1] + 0.2 - f1[0]))));
  else if (t < f2[0]) scrollPx = s1;
  else scrollPx = lerp(s1, s2, 1 - Math.pow(1 - clamp((t - f2[0]) / 0.5), 2.2));
  const fall = clamp((t - r(0.5)) / 0.2);
  const land = t >= r(0.7) ? clamp((t - r(0.7)) / 0.25) : 0;
  const smear = clamp((t - (f2[0] + 0.08)) / 0.2);
  const smearV = 0.25 * smooth(smear);
  return { tap, tu, tv, over, scrollPx, fall: t < r(0.7) ? fall : 1, land, smear, smearV, dropU: 0.42, dropV: 0.5 };
}
function insertThumb(t) { const I = insertState(t); return { extra: { tap: I.tap, thumb: I.over, thumbAt: [I.tu, I.tv] } }; }
export const S01_INSERT = { insertState };
