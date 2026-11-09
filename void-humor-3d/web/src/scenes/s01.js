// s01 running_from_the_void — the opening. Frame 0 (t = 0) is the social-media preview: a crying kid with a phone
// fleeing a huge, soft, hopeful Void down a pastel dusk path, title room in the sky (the title is burned in by the
// subtitle pass, y 110-300). Shots: A FRAME0 backward track (0 -> "Twitter") · B phone INSERT (-> s01b03) ·
// C CHASELOW 24 mm low wide (s01b03). Everything is timed from beat refs (word offsets from data/lines.json).
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, noise1, fbm1, hash1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, lookFor } from './marks.js';
import { VX } from '../chars/void.js';
import { UX } from '../chars/user.js';
import { ownedGroup, cast, G, bump, jiggle, V3, WD, fitCam } from './kit_s0102.js';

// ------------------------------------------------------------------------------------------------ constants
const D = [-0.2495, 0.9684];                    // travel direction (stage local): down the path toward the stage
const YAW_RUN = Math.atan2(D[0], D[1]);          // local facing while running (-0.252)
const SPD = 1.25;                                // cheated ground speed (m/s); the camera tracks at the same speed
const U_CPS = 1.32, V_CPS = 1.25;                // run / waddle cycles per second
const PH_W = 0.071, PH_H = 0.148, PH_D = 0.0085; // USER rig phone slab (web/src/chars/user.js)
const SW = PH_W - 0.007, SH = PH_H - 0.008;      // screen size

// beat-anchored times (word onsets from data/lines.json: "Twitter" +1.10, "crying" +0.0, "void" +1.36)
const tLook = () => T('s01b01+0.4');            // look back over the LEFT shoulder (~1.0 s)
const tIns = () => T('s01b02+1.08');            // cut to the phone insert on "Twitter"
const tC = () => T('s01b03');                   // cut to the low wide on "crying"
const tVoidWord = () => T('s01b03+1.33');       // "void" (frantic look back)

const add2 = (a, b, s = 1) => [a[0] + b[0] * s, a[1] + b[1] * s];
const U0 = [2.35, -6.4], V0 = [3.62, -13.3];     // frame-0 marks (stage local): user on the path, the Void on the crest

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
  if (kind === 'blob') {       // a tear lying on glass: milky lens, darker rim, a bright highlight
    let gr = g.createRadialGradient(64, 64, 0, 64, 64, 60);
    gr.addColorStop(0, 'rgba(236,242,252,0.62)'); gr.addColorStop(0.62, 'rgba(214,224,240,0.5)');
    gr.addColorStop(0.86, 'rgba(120,134,160,0.55)'); gr.addColorStop(0.95, 'rgba(250,252,255,0.75)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(64, 64, 60, 0, 7); g.fill();
    gr = g.createRadialGradient(46, 42, 0, 46, 42, 16); gr.addColorStop(0, 'rgba(255,255,255,0.95)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(46, 42, 16, 0, 7); g.fill();
  } else {                     // a falling tear (teardrop, point up)
    const gr = g.createLinearGradient(40, 0, 88, 0); gr.addColorStop(0, 'rgba(170,200,240,0.75)'); gr.addColorStop(0.5, 'rgba(240,248,255,0.95)'); gr.addColorStop(1, 'rgba(150,180,230,0.75)');
    g.fillStyle = gr; g.beginPath(); g.moveTo(64, 8); g.bezierCurveTo(70, 40, 96, 64, 96, 86); g.arc(64, 86, 32, 0, Math.PI); g.bezierCurveTo(32, 64, 58, 40, 64, 8); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.95)'; g.beginPath(); g.ellipse(54, 82, 6, 10, -0.3, 0, 7); g.fill();
  }
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; return tx;
}

// ------------------------------------------------------------------------------------------------ the scene
export default {
  id: 's01',
  async setup(app) {
    const set = await app.set('EDGE');
    const user = await app.char('USER'), vd = await app.char('VOID');
    const st = { set, scene: set.scene, user, vd, look: {} };
    st.own = ownedGroup(st, 's01.own');
    st.fx = new Particles({ max: 80, intensity: 1.5 }); st.own.add(st.fx.mesh);
    // phone insert overlay (follows the rig phone's matrixWorld; only drawn in the insert)
    const ov = st.ov = new THREE.Group(); ov.matrixAutoUpdate = false; st.own.add(ov);
    const mk = (geo, map, z, ro) => { const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map, transparent: true, depthWrite: false, toneMapped: true })); m.position.z = z; m.renderOrder = ro; ov.add(m); return m; };
    st.feed = feedCanvas();
    const hh = SH * 40 / (FEED.VIS * 256 / 256) * (256 / 256);   // header height (40 px of a 560 px tall screen)
    st.feedM = mk(new THREE.PlaneGeometry(SW, SH), st.feed, PH_D / 2 + 0.0009, 7);
    st.hdrM = mk(new THREE.PlaneGeometry(SW, hh), headerTex(), PH_D / 2 + 0.0011, 8); st.hdrM.position.y = SH / 2 - hh / 2;
    st.blob = mk(new THREE.CircleGeometry(0.5, 24), dropTex('blob'), PH_D / 2 + 0.0016, 9);
    st.drip = mk(new THREE.PlaneGeometry(1, 1), dropTex('drip'), PH_D / 2 + 0.006, 9);
    for (const m of [st.feedM, st.hdrM]) m.material.transparent = false;
    st.ovOff = new THREE.Matrix4();
    st.scene.add(st.own);
    // frame-0 composition: fit the shot-A camera so the user's eyes land at (285, 440) (left of centre, below the
    // title band) and the Void's eyes at (468, 352) (right of centre), camera ~1.2 m up on the path
    {
      const uW0 = G(set, ...U0), vW0 = G(set, ...V0);
      user.update(0, { pos: uW0, yaw: EDGE.Y(YAW_RUN + 0.16), walk: { amount: 1, style: 'run', phase: 0.18 } });
      vd.update(0, { pos: vW0, yaw: EDGE.Y(YAW_RUN + 0.02), walk: { amount: 1, style: 'waddle', phase: 0.05 } });
      const ue = user.anchor('eyes'), ve = vd.anchor('eyes'), vt = vd.anchor('hoodTop');
      const guessL = add2(U0, D, 3.45), cg = G(set, ...guessL); cg[1] += 0.98;
      const lk = [ue.x * 0.5 + ve.x * 0.5, ue.y + 0.2, ue.z * 0.5 + ve.z * 0.5];
      const f = fitCam([[ue, 290, 452, 1], [ve, 460, 382, 1], [vt, 462, 302, 0.6]], 44, cg, lk, { reg: 0.4, yMin: cg[1] - 0.14, yMax: cg[1] + 0.14 });
      st.camA = f;
      console.log(`s01 frame0 fit err ${f.err.toFixed(1)}px pos ${f.pos.map((v) => v.toFixed(2))} look ${f.look.map((v) => v.toFixed(2))}`);
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
    if (!shotC) {
      const s = SPD * t;
      uL = add2(U0, D, s);
      vL = add2(V0, D, s);
      const push = 0.3 * smooth((t - T('s01b02')) / 1.1);           // drift a touch closer on the narration
      const dw = WD(D[0], D[1]).multiplyScalar(s);
      const A = st.camA, cp = V3(...A.pos).add(dw), cl = V3(...A.look).add(dw);
      const toU = cl.clone().sub(cp).setY(0).normalize();
      cp.addScaledVector(toU, push); cp.y -= 0.05 * push;
      camPos = EDGE.L(cp); camLook = EDGE.L(cl);
      const c = { fov: 44 };
      fov = c.fov;
    } else {
      const s = SPD * (t - tC());
      uL = add2([2.38, -5.35], D, s);
      vL = add2(uL, [1.0, -2.05]);
      const c = EDGE.CAM.CHASELOW, sc = 0.78 * s;
      camPos = [c.pos[0] + D[0] * sc, c.pos[1], c.pos[2] + D[1] * sc];
      camLook = [c.look[0] + 0.55 + D[0] * sc, c.look[1] + 0.12, c.look[2] + D[1] * sc];
      fov = c.fov;
    }
    const uW = G(set, uL[0], uL[1]), vW = G(set, vL[0], vL[1]);
    const yawW = EDGE.Y(YAW_RUN + (shotC ? 0.05 : 0.16));
    const vel = WD(D[0], D[1]).multiplyScalar(SPD);                // world velocity of both runners

    if (!insert) applyShot(cam, { pos: EDGE.W(camPos), look: EDGE.W(camLook), fov, drift: t < 0.2 ? 0 : 0.3 }, t);

    // ---------------------------------------------------------------------------- USER
    const uPh = t * U_CPS + 0.18;
    const lookA = k(t, [[tLook() - 0.02, 0], [tLook() + 0.16, 0.86, 'out'], [tLook() + 0.42, 0.86], [tLook() + 0.6, 0, 'inOut']]);
    const lookC = k(t, [[tVoidWord() - 0.04, 0], [tVoidWord() + 0.12, 0.6, 'out'], [tVoidWord() + 0.42, 0.62], [tVoidWord() + 0.58, 0.08, 'inOut']]);
    const lookBack = shotC ? lookC : lookA;
    const phoneUp = shotC ? 0 : k(t, [['s01b02+0.55', 0], ['s01b02+0.95', 0.78, 'inOut'], [tIns(), 1]]);
    // provisional user update (no gaze) -> eye / phone anchors for this frame (pure: no previous-frame state)
    const posePre = { pos: uW, yaw: yawW, walk: { amount: 1, style: 'run', phase: uPh }, body: { lookBack }, extra: { phoneUp } };
    user.update(t, posePre);
    const userEyes0 = user.anchor('eyes');
    const phoneScr0 = user.anchor('phoneScreen');
    // eyes lead the head by ~3 frames
    const eyesBack = shotC ? (t > tVoidWord() - 0.12 && t < tVoidWord() + 0.5) : (t > tLook() - 0.14 && t < tLook() + 0.48);
    const glancePhone = !shotC && t > T('s01b02+0.5');
    // the face, beat by beat
    const EEK = UX([['terror', 0.6], ['nervous', 0.4]], { lidU: 1.48, lidL: 0.08, pupil: 0.42, browIn: 1.05, browOut: 0.95, browSq: 0.08, browMid: 0.3, mOpen: 0.26, mWide: 0.95, mSmile: -0.3, mClench: 0.55, mTeethU: 0.9, mTeethL: 0.75, mTremble: 0.5, wet: 1, autoBlink: 0, gazePitch: 0.12 });
    const SOBRUN = UX([['sob', 0.55], ['terror', 0.45]], { lidU: 0.85, mOpen: 0.45, autoBlink: 0 });
    let face;
    if (!shotC) {
      const hitch = Math.max(0, Math.sin(Math.PI * 2 * (uPh * 0.5))) ** 6;    // a hitched sob every second step
      face = k(t, [
        [0, EEK], [tLook() - 0.05, EEK],
        [tLook() + 0.06, UX('gasp', { lidU: 1.5, pupil: 0.38, autoBlink: 0 }), 'out'],
        [tLook() + 0.44, UX('gasp', { lidU: 1.5, pupil: 0.36, mOpen: 0.55, autoBlink: 0 })],
        [tLook() + 0.56, UX('terror', { lidU: 1.55, pupil: 0.34, autoBlink: 0 }), 'out'],      // snap forward, even wider
        [tLook() + 1.1, UX('terror', { lidU: 1.45, autoBlink: 0 })],
        ['s01b02', SOBRUN, 'inOut'],
        ['s01b02+0.5', SOBRUN],
        ['s01b02+0.9', UX([['sob', 0.45], ['scroll', 0.55]], { lidU: 0.62, autoBlink: 0 }), 'inOut'],
      ]);
      face = { ...face, mOpen: face.mOpen + 0.25 * hitch * smooth((t - T('s01b02') + 0.6) / 0.6), lidU: face.lidU };
    } else {
      const SCREAM = UX('scream', { pupil: 0.3, lidU: 1.5 });
      face = k(t, [
        [tC(), UX('sob', { lidU: 0.12 })], ['s01b03+0.45', UX('sob', { lidU: 0.14 })],
        ['s01b03+0.62', UX([['terror', 0.7], ['sob', 0.3]], { autoBlink: 0 }), 'inOut'],
        ['s01b03+0.95', UX([['terror', 0.6], ['gulp', 0.4]], { autoBlink: 0 }), 'inOut'],     // the sneaker scuff
        ['s01b03+1.08', UX('terror', { autoBlink: 0 }), 'inOut'],
        [tVoidWord() + 0.02, UX('terror', { lidU: 1.5, autoBlink: 0 })],
        [tVoidWord() + 0.1, SCREAM, 'out'], [tVoidWord() + 0.42, SCREAM],                    // eyes lock 6+ frames
        [tVoidWord() + 0.62, UX('terror', { lidU: 1.4, mOpen: 0.6, autoBlink: 0 }), 'inOut'],
      ]);
    }
    // sob shakes the shoulders on "crying"
    const sobShake = shotC ? bump(t, tC() - 0.05, T('s01b03+0.6'), 0.3) : 0;
    const shrug = (shotC ? 0.15 : 0.12) + 0.35 * sobShake * (0.5 + 0.5 * Math.sin((t - tC()) * 2 * Math.PI * 5.5));
    const scuff = shotC ? bump(t, T('s01b03+0.86'), T('s01b03+1.12'), 0.35) : 0;
    const flail = shotC ? lerp(0.55, 1.0, smooth((t - T('s01b03+0.55')) / 0.4)) : 0.6;
    // ---------------------------------------------------------------------------- VOID
    if (!insert) {
      const vPh = t * V_CPS + 0.05;
      const userEyes = userEyes0;
      // after the user screams at it (shot C): the wiggle freezes, outer wisps sink, lids sag a touch
      const hurt = shotC ? smooth((t - tVoidWord() - 0.28) / 0.45) : 0;
      const bright = shotC ? bump(t, tVoidWord() + 0.02, tVoidWord() + 0.9, 0.18) : bump(t, tLook(), tLook() + 1.0, 0.2) * 0.6;
      const wig = shotC && t > tVoidWord() + 0.05 ? Math.sin(Math.min(t - tVoidWord() - 0.05, 0.31) * 2 * Math.PI * 3.2) : 0;  // two wiggles, frozen mid-wiggle
      const face0 = VX('hopeful', { lidU: 1.16, browIn: 0.72, browOut: 0.12, mOpen: 0.12, mRound: 0.7, mSmile: 0.05, autoBlink: t < 0.3 ? 0 : 1 });
      const vface = { ...face0 };
      vface.lidU = lerp(face0.lidU, 0.92, hurt) + 0.12 * bright;
      vface.browOut = lerp(face0.browOut, -0.45, hurt); vface.browIn = lerp(face0.browIn, 0.85, hurt);
      vface.lidSad = 0.35 * hurt; vface.mRound = lerp(0.7, 0.35, hurt); vface.mOpen = lerp(0.12, 0.05, hurt);
      vface.mSmile = 0.05 + 0.2 * bright * (1 - hurt) - 0.15 * hurt;
      vd.update(t, {
        pos: vW, yaw: EDGE.Y(YAW_RUN + (shotC ? -0.06 : 0.02)),
        walk: { amount: 1, style: 'waddle', phase: vPh },
        body: { bounce: jiggle(vPh, V_CPS, 0.014), lean: 0.03, recoil: -0.04 },
        head: { pitch: 0.05, yaw: 0.04 },
        gaze: userEyes,
        face: vface,
        armL: { preset: 'wave', from: 'rest', mix: 0.58 + 0.06 * bright, offset: shotC ? WD(-0.75, 0.25).multiplyScalar(0.45).toArray() : undefined, hand: { spread: 0.5 + 0.2 * wig, curl: 0.12 + 0.28 * Math.max(0, wig), thumb: 0.6 } },
        armR: { preset: 'rest', offset: WD(0.2, 0.25).multiplyScalar(0.25).toArray(), hand: { curl: 0.75, thumb: 0.85, cup: 0.5, spread: 0.05 } },
        extra: { hem: 0.5, eyeGlow: 1 + 0.4 * bright, motes: 1.4, rim: 1.1 },
        blinkAt: shotC ? [tVoidWord() + 0.72] : [2.15],
      });
    }

    const vEyes = insert ? null : vd.anchor('eyes');
    const uPose = {
      pos: uW, yaw: yawW,
      walk: { amount: 1, style: 'run', phase: uPh, flail },
      body: { lookBack, shrug, tremble: 0.25 + 0.4 * sobShake, lean: 0.06 * scuff, bounce: -0.035 * scuff, flinch: 0.25 * scuff, pant: 0.6 },
      head: { pitch: glancePhone ? 0.16 * smooth((t - T('s01b02+0.5')) / 0.3) : 0 },
      gaze: eyesBack && vEyes ? vEyes : glancePhone ? phoneScr0 : (insert ? null : cam.position.clone().add(V3(0, 0.55, 0))),
      face,
      extra: { tears: 1, phone: 0.9, phoneUp, glassesTilt: 0.07 + 0.03 * Math.sin(uPh * Math.PI * 2), screen: 'feed', scroll: t * 0.15 },
      armL: insert ? { preset: 'look', palm: V3(0, 0.93, 0).addScaledVector(V3(Math.sin(yawW), 0, Math.cos(yawW)), -0.37).toArray(), fingers: V3(Math.sin(yawW), 0, Math.cos(yawW)).multiplyScalar(0.92).add(V3(0, 0.38, 0)).toArray(), offset: V3(Math.sin(yawW), 0, Math.cos(yawW)).multiplyScalar(0.04).toArray() } : shotC ? undefined : { preset: [['clutch', 0.55], ['hold', 0.45]] },   // phone hugged to the sternum, screen glowing up at the chin
    };
    if (insert) { uPose.gaze = null; uPose.extra = { ...uPose.extra, ...insertThumb(t).extra }; }
    let lag = null;
    if (insert) {   // lagged phone poses (for the insert camera), sampled BEFORE the final update at t
      lag = [];
      for (const [dt, w] of [[0.1, 0.2], [0.05, 0.3]]) {
        user.update(t - dt, { ...uPose, extra: { ...uPose.extra, ...insertThumb(t - dt).extra } });
        user.phone.updateWorldMatrix(true, false);
        lag.push([user.phone.matrixWorld.clone(), w]);
      }
    }
    user.update(t, uPose);

    // ---------------------------------------------------------------------------- insert camera + overlay
    st.ov.visible = insert;
    if (insert) {
      // camera on the phone's +Z axis, rolled with the phone; follows a slightly lagged phone pose so the run's
      // bob and the hand tremor read as the phone moving a little in frame
      user.phone.updateWorldMatrix(true, false);
      const P = [], Q = [];
      for (const [m, w] of [...lag, [user.phone.matrixWorld.clone(), 0.5]]) {
        P.push([new THREE.Vector3().setFromMatrixPosition(m), w]);
        Q.push([new THREE.Quaternion().setFromRotationMatrix(m), w]);
      }
      const pos = new THREE.Vector3(), q = Q[0][0].clone();
      for (const [p, w] of P) pos.addScaledVector(p, w);
      q.slerp(Q[1][0], 0.6).slerp(Q[2][0], 0.62);
      const n = new THREE.Vector3(0, 0, 1).applyQuaternion(q), up = new THREE.Vector3(0, 1, 0).applyQuaternion(q);
      const scr = pos.clone().addScaledVector(n, PH_D / 2).addScaledVector(up, -0.006);
      cam.position.copy(scr).addScaledVector(n, 0.235).addScaledVector(up, -0.02);
      cam.up.copy(up); cam.fov = 50; cam.updateProjectionMatrix();
      cam.lookAt(scr.clone().addScaledVector(up, -0.006)); cam.updateMatrixWorld();
      // overlay follows the (current) phone
      user.phone.updateWorldMatrix(true, false);
      st.ov.matrix.copy(user.phone.matrixWorld); st.ov.matrixWorldNeedsUpdate = true;
      const I = insertState(t);
      st.feed.offset.y = 1 - (I.scrollPx + FEED.VIS) / FEED.H;
      // the tear: falls, lands on the sad post, blooms; the second flick smears it upward
      const S = 0.0105;
      st.drip.visible = I.fall > 0 && I.fall < 1;
      if (st.drip.visible) {
        const u = I.fall;
        st.drip.position.set((I.dropU - 0.5) * SW, lerp(SH * 0.62, (0.5 - I.dropV) * SH, u * u), PH_D / 2 + lerp(0.02, 0.002, u));
        st.drip.scale.set(S * 0.7, S * 1.15, 1);
      }
      st.blob.visible = I.land > 0;
      if (st.blob.visible) {
        const r = S * (0.75 + 0.55 * smooth(I.land)) * (1 + 0.15 * Math.max(0, 1 - I.land * 3));
        st.blob.position.set((I.dropU - 0.5) * SW, (0.5 - I.dropV) * SH + 0.5 * SH * I.smearV, PH_D / 2 + 0.0016);
        st.blob.scale.set(r * (1 - 0.25 * I.smear), r * (1 + 2.2 * I.smear), 1);
        st.blob.material.opacity = 1 - 0.45 * I.smear;
      }
    }

    // ---------------------------------------------------------------------------- particles: tear glints, star breath
    st.fx.begin();
    if (!insert) {
      const ue = user.anchor('eyes');
      const yw = yawW, left = V3(Math.cos(yw), 0, -Math.sin(yw)), fwd = V3(Math.sin(yw), 0, Math.cos(yw));
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
      // star-breath motes from the Void's mouth on its steps (shot C), sparse and slow
      if (shotC) {
        const mo = vd.anchor('mouthOut') || vd.anchor('mouth');
        st.fx.stream({ t, seed: 77, t0: tC(), t1: T('s01.end'), rate: 6, life: 1.4,
          origin: (tb) => mo.clone().addScaledVector(vel, tb - t).toArray(),
          vel: [0, 0.35, 0], spread: [0.18, 0.12, 0.18], size: [0.03, 0.06], color: [0xd8c8ff, 0xbfefff, 0xffffff],
          alpha: 0.8, fade: [0.2, 0.5], cell: CELL.star, twinkle: true, drag: 1.2 });
      }
    }
    st.fx.end();

    // ---------------------------------------------------------------------------- set + look
    const mid = [(uW[0] + vW[0]) / 2, 0, (uW[2] + vW[2]) / 2];
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t), voidPos: vW, voidRadius: shotC ? 26 : 22, shadowAt: mid,
      seeds: 0.85, sunGlow: 1, keyMul: 1.0, fillMul: 1.12 });
    st.look = lookFor('s01', set.look);
    if (insert) st.look = { ...st.look, bloomThreshold: 0.98, bloom: 0.35, vignette: 0.2 };
  },
};

// ------------------------------------------------------------------------------------------------ insert timing
// Relative to the cut on "Twitter": flick 1 brings the sad post up; the tear falls and blooms on it; flick 2 drags
// through it (smear) and scrolls on.
function insertState(t) {
  const a = tIns();
  const r = (x) => a + x;
  const flick = (t0, t1, fromV, toV) => { const u = clamp((t - t0) / (t1 - t0)); return lerp(fromV, toV, smooth(u)); };
  // thumb touching windows
  const f1 = [r(0.12), r(0.42)], f2 = [r(0.98), r(1.28)];
  let tap = 0, tv = 0.72, tu = 0.56;
  tap = Math.max(bump(t, f1[0] - 0.06, f1[1] + 0.06, 0.2) > 0 ? clamp((t - f1[0] + 0.06) / 0.06) * clamp((f1[1] + 0.06 - t) / 0.06) : 0,
    bump(t, f2[0] - 0.06, f2[1] + 0.06, 0.2) > 0 ? clamp((t - f2[0] + 0.06) / 0.06) * clamp((f2[1] + 0.06 - t) / 0.06) : 0);
  if (t < f1[1] + 0.06) tv = flick(f1[0], f1[1], 0.78, 0.38);
  else if (t < f2[0] - 0.1) tv = lerp(0.38, 0.8, smooth((t - f1[1] - 0.06) / (f2[0] - 0.1 - f1[1] - 0.06)));
  else tv = flick(f2[0], f2[1], 0.8, 0.26);
  tu = 0.5 + 0.02 * Math.sin((t - a) * 3);
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
  return { tap, tu, tv, over, scrollPx, fall: t < r(0.7) ? fall : 1, land, smear, smearV, dropU: 0.45, dropV: 0.5 };
}
function insertThumb(t) { const I = insertState(t); return { extra: { tap: I.tap, thumb: I.over, thumbAt: [I.tu, I.tv] } }; }
