// s19 the_corner_of_its_eye — the Void knows. Only its eyes move; its face stays soft for Fear, and it hums.
//   b01 (silent)  low on the Void's face from Fear's side: a soft gaze down at Fear... then, the head perfectly still,
//        the eyes slide at a constant downward pitch (never through the lens) into the far corners toward screen-right,
//        where the magician's dented hat brim bobs back into view at the frame edge (he tiptoes back to PEEK); the upper
//        lids lower flat, the inner end of one brow-wisp twitches down, a tiny controlled breath.
//   b02 "And the void can see it."   hold: eyes parked in the corners, no blink, the rest of the face kept sweet.
//   b03 "Just, in the corner of its eye."   long-lens CU on its left eye and mouth corner, the hat brim + the raised
//        dagger's glint soft at the right edge: the iris quivers in the corner; on "eye" it glides back to Fear, the lids
//        lift soft, the small smile returns, held (the hum starts over it).
//   b05 VOID hum   pull back to the stacked dramatic-irony wide: Fear lower-left at the open door smiling up at the stars
//        (tuft lifts, nose wiped on the scarf), the Void bowed over it humming (hood stars pulse, hands folded on its
//        belly), the magician behind its shoulder rising on his toes, dagger high.
// The magician is CHEATED for the b01-b03 close shots only (shifted so his hat / dagger sit at the frame edge); in the
// b05 wide he is on his toes at PEEK, where s20 picks him up.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { ROOM, lookFor } from './marks.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { MX } from '../chars/magician.js';
import { V3, toV, loadWords, wordT, pulse, ramp, fitShot, mixShot, logDolly, project, cast, ownedGroup, bonusMarks, voidBowed,
  MAGPATH, magTiptoe, magSteps, ensureBonusDecals, BONUS_LIGHTS, bonusLook, clamp, smooth, lerp } from './kit_bonus.js';

let S = null;
const tb = (r) => T(r);
const DBG = () => globalThis.__S19 || {};          // review aid only (camera override); never set in normal renders

export default {
  id: 's19',
  async setup(app) {
    await loadWords();
    const set = await app.set('BACKROOM');
    const vd = await app.char('VOID'), fear = await app.char('FEAR'), mag = await app.char('MAGICIAN');
    const st = { scene: set.scene, set, vd, fear, mag };
    st.decals = ensureBonusDecals(set);
    st.own = ownedGroup(st, 's19own'); set.scene.add(st.own);
    st.glint = glintSprite(); st.own.add(st.glint);
    S = st.S = statics(st);
    console.log('s19 steps', JSON.stringify(magSteps(T('s19'), T('s19b05')).map((x) => [x, (x - T('s19b01')).toFixed(2)])));
    return st;
  },
  async update(t, app, st) {
    st.__t = t;
    S = st.S;
    const { set, vd, fear, mag } = st;
    cast(app, st.scene, ['VOID', 'FEAR', 'MAGICIAN']);
    if (st.own.parent !== st.scene) st.scene.add(st.own);
    const shot = DBG().cam || shotAt(t);
    applyShot(app.camera, shot, t, 19);
    set.update(t, { latch: 1, cageDoor: 1, lights: BONUS_LIGHTS });
    fear.update(t, fearPoseFn(t));
    vd.update(t, voidPose(t, st));
    mag.update(t, magPose(t, st));
    // the raised dagger's glint, soft at the frame edge in the eye CU ("corner")
    const g = t >= S.T.cut3 && t < S.T.cut5 ? pulse(t, S.T.corner - 0.05, 0.12, 0.15, 0.45) : 0;
    st.glint.visible = g > 0.01;
    if (st.glint.visible) { st.glint.position.copy(S.glintEcu); st.glint.material.opacity = 0.7 * g; st.glint.scale.setScalar(0.1 + 0.16 * g); st.glint.material.rotation = 0.5 * g; }
    // exposure: the eye ECU keeps its cosmic black (smaller boost); Fear's lavender CU the least
    st.look = bonusLook(lookFor('s19', set.look), t < S.T.cut3 ? 1.65 : t < S.T.cut5 ? 1.38 : t >= S.T.cutF && t < S.T.cutW ? 1.15 : 1.65);
  },
};

// ------------------------------------------------------------------------------------------------ times
function times() {
  const b1 = tb('s19b01'), b2 = tb('s19b02'), b3 = tb('s19b03'), b5 = tb('s19b05');
  const T0 = {
    s0: tb('s19'), end: tb('s19.end'), b1, b2, b3, b5,
    see: wordT('s19b02', 'see', { fallback: 0.55 }),
    corner: wordT('s19b03', 'corner', { fallback: 0.45 }),
    eye: wordT('s19b03', 'eye', { fallback: 0.85 }),
  };
  T0.slideA = b1 + 0.5; T0.slideB = b1 + 1.15;             // the eyes slide into the corners (head still)
  T0.backA = T0.eye - 0.12; T0.backB = T0.eye + 0.32;      // ...and glide back to Fear on "eye"
  T0.cut3 = b3 - 0.1;
  T0.cut5 = b5 + 0.12;                                     // the hum starts over the held eye CU, then the pull-back
  T0.cutF = b5 + 0.95; T0.cutW = b5 + 1.62;                // a short Fear CU for the nose-wipe + the wobbly smile, back to the wide
  return T0;
}

// ------------------------------------------------------------------------------------------------ statics
function statics(st) {
  const { set, vd, fear, mag } = st;
  const out = { T: times() };
  S = out;
  const B = out.B = bonusMarks(set), TT = out.T;
  out.PEEK = ROOM.W(MAGPATH.PEEK);
  out.off = [0, 0, 0];
  fear.update(TT.b2, fearPose(TT.b2));
  out.fEyes = fear.anchor('eyes');
  vd.update(TT.b2, voidPose0(TT.b2, out.fEyes, false));
  out.vEyes = vd.anchor('eyes'); out.vMouth = vd.anchor('mouth');
  const eyeL = vd.face.eyes.find((e) => e.sx > 0) || vd.face.eyes[0];
  out.vEyeL = eyeL.group.getWorldPosition(new THREE.Vector3());
  vd.update(TT.b5 + 1.0, voidPose0(TT.b5 + 1.0, out.fEyes, true));
  out.vEyes5 = vd.anchor('eyes');
  fear.update(TT.b5 + 0.4, fearPose(TT.b5 + 0.4));
  out.fEyes5 = fear.anchor('eyes');
  // the slide path (bearing / pitch about the eyes): from Fear's direction round toward its left (screen-right) at
  // Fear's constant downward pitch -- well below the lens -- and only near the far corner easing up toward the hat
  out.dFear = out.fEyes.clone().sub(out.vEyes);
  out.bF = Math.atan2(out.dFear.x, out.dFear.z); out.pF = Math.atan2(out.dFear.y, Math.hypot(out.dFear.x, out.dFear.z));
  out.bC = B.vYaw + 0.12 + 1.05; out.pC = -0.22; out.gR = out.dFear.length();
  // ---- cameras
  // b01/b02: low on its face from Fear's side, below Fear's eye line to the Void (the gaze passes above the lens)
  out.LOW = fitShot([[out.vEyes, 285, 420]], 44, ROOM.W(...DEF.lowPos), out.vEyes, { posReg: 10, free: [0, 0, 0] });
  out.LOW_B = { ...out.LOW, fov: out.LOW.fov - 1.5 };
  // b03: long-lens CU on its left eye + the mouth corner (tight enough to keep the hood collar out of frame)
  { const a = DEF.ecuBearing * Math.PI / 180, d = DEF.ecuDist;
    const ecuPos = out.vEyeL.clone().add(ROOM.V(Math.sin(a) * d, DEF.ecuDy, Math.cos(a) * d).sub(ROOM.V(0, 0, 0)));
    out.ECU = fitShot([[out.vEyeL, 250, 335], [out.vMouth, 230, 745, 0.3]], 14, ecuPos, out.vEyeL, { posReg: 10, free: [0, 0, 0] }); }
  // the cheat for the close shots: his own hat, freed from his head (he is hidden behind the Void at PEEK), hung on the
  // camera ray at the frame edge ~1 m beyond the Void's face, bobbing with his tiptoe steps
  out.hatLow = rayPoint(out.LOW, 690, 330, toV(out.LOW.pos).distanceTo(out.vEyes) + 1.2);
  out.hatEcu = rayPoint(out.ECU, 700, 105, toV(out.ECU.pos).distanceTo(out.vEyeL) + 2.4);
  out.glintEcu = rayPoint(out.ECU, 672, 170, toV(out.ECU.pos).distanceTo(out.vEyeL) + 2.4);
  mag.update(TT.b5 + 1.2, magPose(TT.b5 + 1.2, st, true));
  out.mEyes5 = mag.anchor('eyes');
  // b05: the stacked dramatic-irony wide (KICK family): Fear lower-left, the Void's 3/4 face, the magician behind it
  const kick = ROOM.cam('KICK');
  out.FCU = ROOM.shot(ROOM.L(out.fEyes5), { dist: 1.5, yaw: 42, pitch: -7, fov: 30, screenY: 400 / 1280, drift: 0.08 });
  out.WIDE = fitShot([[out.fEyes5, 175, 730], [out.vEyes5, 370, 470], [out.mEyes5, 560, 410, 0.5]], 45, ROOM.W(...DEF.widePos), kick.look, { posReg: 10, free: [0, 0, 0] });
  out.WIDE_A = { ...out.WIDE, pos: toV(out.WIDE.pos).lerp(toV(out.vEyes5), 0.3).toArray(), fov: 46 };
  const L3 = (p) => ROOM.L(p).map((v) => +v.toFixed(2));
  console.log('s19 statics', JSON.stringify({ low: out.LOW.err.toFixed(1), ecu: out.ECU.err.toFixed(1), wide: out.WIDE.err.toFixed(1), widePos: L3(out.WIDE.pos),
    wideProj: [project(out.WIDE, out.fEyes5), project(out.WIDE, out.vEyes5), project(out.WIDE, out.mEyes5)], hatLow: L3(out.hatLow), hatEcu: L3(out.hatEcu), ecuPos: L3(out.ECU.pos),
    lowFear: project(out.LOW, out.fEyes), vEyes: L3(out.vEyes), fEyes: L3(out.fEyes) }));
  return out;
}
const DEF = {
  lowPos: [-0.93, 0.5, 1.74],
  ecuBearing: -58, ecuDist: 3.5, ecuDy: 0.12,
  widePos: [1.2, 1.85, 8.2],
};
// the world point at distance d along the camera ray through pixel (px, py) of shot `sh`
function rayPoint(sh, px, py, d) {
  const cam = new THREE.PerspectiveCamera(sh.fov, 720 / 1280, 0.05, 400);
  cam.position.set(...sh.pos); cam.up.set(0, 1, 0); cam.lookAt(...sh.look); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
  const ndc = new THREE.Vector3(px / 720 * 2 - 1, 1 - py / 1280 * 2, 0.5).unproject(cam);
  return cam.position.clone().addScaledVector(ndc.sub(cam.position).normalize(), d);
}

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const TT = S.T;
  if (t < TT.cut3) return mixShot(S.LOW, S.LOW_B, ramp(t, TT.s0, TT.cut3, 'inOut'));
  if (t < TT.cut5) return { ...S.ECU, pos: toV(S.ECU.pos).lerp(toV(S.vEyeL), 0.03 * ramp(t, TT.cut3, TT.cut5, 'linear')).toArray() };
  if (t >= TT.cutF && t < TT.cutW) return { ...S.FCU, pos: toV(S.FCU.pos).lerp(toV(S.FCU.look), 0.04 * ramp(t, TT.cutF, TT.cutW, 'linear')).toArray() };
  if (t >= TT.cutW) return S.WIDE;
  const u = ramp(t, TT.cut5, TT.cutF + 0.1, 'inOut');
  const d0 = toV(S.WIDE_A.pos).distanceTo(toV(S.WIDE_A.look)), d1 = toV(S.WIDE.pos).distanceTo(toV(S.WIDE.look));
  return mixShot(S.WIDE_A, S.WIDE, logDolly(u, d0, d1));
}
function shotStart(t) { const TT = S.T; return t < TT.cut3 ? -1e9 : t < TT.cut5 ? TT.cut3 : t < TT.cutF ? TT.cut5 : t < TT.cutW ? TT.cutF : TT.cutW; }

// ------------------------------------------------------------------------------------------------ the Void
function voidPose0(t, gaze, wide) {
  const P = voidBowed(t, S.B, { gaze, head: wide ? { pitch: 0.5, yaw: 0.3 } : { pitch: 0.25, yaw: 0.12 }, body: wide ? { lean: 0.3 } : {} });
  return P;
}
function voidPose(t, st) {
  const TT = S.T;
  const slide = ramp(t, TT.slideA, TT.slideB, 'inOut');
  const back = ramp(t, TT.backA, TT.backB, 'inOut');                       // glides back to Fear on "eye"
  const watch = slide * (1 - back);
  const flat = ramp(t, TT.slideA + 0.1, TT.slideB) * (1 - back);
  const inB3 = t >= TT.cut3 && t < TT.backA;
  const quiver = inB3 ? 0.012 * Math.sin((t - TT.b3) * 2 * Math.PI * 4.5) * ramp(t, TT.b3, TT.b3 + 0.3) : 0;
  const twitch = pulse(t, TT.slideB + 0.06, 0.07, 0.1, 0.3);
  const hum = pulse(t, TT.b5 + 0.05, 0.3, Math.max(0.1, tb('s19b05.end') - TT.b5 - 0.6), 0.35);
  const wide = t >= TT.cut5;
  const bow = ramp(t, TT.cut5, TT.b5 + 1.2, 'inOut');
  const face = VX('gentle', {
    lidU: lerp(0.68, 0.56, flat) + 0.08 * back - 0.06 * hum, lidL: 0.38 + 0.06 * flat + 0.12 * hum, lidAngry: 0.18 * flat,
    browIn: 0.45 - 0.1 * flat, browInL: 0.45 - 0.1 * flat - 0.5 * twitch, browOut: 0.02,
    mSmile: lerp(0.38, 0.3, watch) + 0.1 * back + 0.06 * hum, mPress: 0.1 * watch + 0.08 * hum,
    blush: 0.15 + 0.1 * hum, saccade: 0, autoBlink: 0,
    gazeYaw: quiver,
    talk: 0, mOpen: 0,
  });
  const fe = st.fear.anchor('eyes');
  const ve = S.vEyes;                                                       // (the head does not move in b01-b03)
  const w = smooth(watch), bb = lerp(S.bF, S.bC, w), pp = S.pF + (S.pC - S.pF) * smooth(clamp((w - 0.6) / 0.4));
  const gz = watch > 0.001 ? ve.clone().add(V3(Math.cos(pp) * Math.sin(bb), Math.sin(pp), Math.cos(pp) * Math.cos(bb)).multiplyScalar(S.gR)) : fe;
  const pulseStars = hum * (0.5 + 0.5 * Math.sin((t - TT.b5) * 2 * Math.PI * 1.25));
  const P = voidBowed(t, S.B, {
    gaze: gz, face,
    head: { pitch: 0.25 + 0.25 * bow, yaw: wide ? 0.3 : 0.12 },
    body: { lean: 0.12 + 0.18 * bow, breathe: 0.45 + 0.6 * hum, swell: 0.03 * pulse(t, TT.slideB + 0.35, 0.25, 0.1, 0.5), tilt: 0.015 * hum * Math.sin((t - TT.b5) * 2 * Math.PI * 0.6) },
    armL: wide ? { preset: 'belly', from: 'rest', mix: bow } : { preset: 'rest' },
    armR: wide ? { preset: 'belly', from: 'rest', mix: ramp(t, TT.cut5 + 0.1, TT.b5 + 1.3, 'inOut') } : { preset: 'rest' },
    extra: { stars: 1.4 + 0.55 * pulseStars, cosmos: 0.12 + 0.12 * pulseStars, eyeGlow: (wide ? 1 : 0.78) + 0.08 * pulseStars },
    blinkAt: [TT.backB + 0.1, TT.b5 + 1.25],
  });
  P.speech = { open: 0.02 * hum, wide: 0, round: 0, close: 0.6 * hum };     // the hum: lips closed in the smile
  return P;
}

// ------------------------------------------------------------------------------------------------ the magician
function magPose(t, st, raw = false) {
  const TT = S.T, B = S.B;
  const fearE = S.fEyes5 || S.fEyes || toV(B.FDOOR).add(V3(0, 0.65, 0));
  const tip = magTiptoe(t);
  const atPeek = ramp(t, tip.tBack - 0.1, tip.tBack + 0.35);
  const faceFear = Math.atan2(fearE.x - S.PEEK[0], fearE.z - S.PEEK[2]);
  const endYaw = ROOM.Y(-0.95);                                              // = s20's opening yaw at PEEK
  const yaw = atPeek > 0 ? lerpAng(tip.yaw, endYaw, atPeek) : tip.yaw;
  const rise = ramp(t, TT.b5 + 0.2, TT.b5 + 1.0, 'inOut');                   // up on his toes, dagger high
  const quiv = rise * 0.01 * Math.sin(t * 2 * Math.PI * 4);
  const body = { tiptoe: lerp(0.6, 1.0, rise), crouch: 0.14 - 0.14 * rise, hunch: 0.25 - 0.6 * rise, lean: 0.08 + 0.1 * atPeek - 0.06 * rise, peek: 0.6 * atPeek, tilt: 0 };
  // b05: he has sidled from PEEK to behind the Void's left shoulder (B5) while we were on the eye
  const side = ramp(t, TT.b3, TT.cut5 - 0.1, 'inOut');
  const b5p = ROOM.W(...B5);
  let pos = [lerp(tip.pos[0], b5p[0], side), 0, lerp(tip.pos[2], b5p[2], side)];
  // the close shots: his hat, freed, hangs at the frame edge on the camera ray (bobbing with the tiptoe)
  const E = { tap: 0.6 * atPeek * (1 - rise) };
  if (!raw && t < TT.cut3) {
    const hp = (t < TT.cut3 ? S.hatLow : S.hatEcu).clone();
    const bob = tip.walk.amount * 0.03 * Math.abs(Math.sin(Math.PI * 2 * tip.phase)) + 0.008 * Math.sin(t * 2.1);
    hp.y += bob - 0.02 * (1 - atPeek);
    E.hatOff = 1; E.hatPos = hp.toArray(); E.hatRot = [0.1 + 0.05 * Math.sin(t * 1.7), yaw + 0.4, -0.12];
  }
  return {
    pos, yaw, walk: tip.walk, body,
    head: { follow: 0.3 + 0.2 * atPeek, look: fearE, roll: 0.06 * rise },
    gaze: fearE,
    face: MX(rise > 0.01 ? [['gloat', 0.5 + 0.5 * rise], ['lurk', 0.5 - 0.5 * rise]] : 'lurk', { lidU: 0.8 + 0.4 * rise, lidL: 0.15, pupil: 0.85 }),
    armR: { preset: 'dagger_ready', offset: [0, 0.1 + 0.28 * rise + quiv, 0] },
    armL: { preset: 'pouch' },
    extra: E,
    speech: false,
  };
}
const B5 = [2.95, 0, -0.55];
const lerpAng = (a, b, u) => { let d = b - a; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; return a + d * u; };

// ------------------------------------------------------------------------------------------------ Fear
function fearPoseFn(t) { const s0 = shotStart(t); return (tt) => fearPose(Math.max(tt, s0)); }
function fearPose(t) {
  const TT = S.T, B = S.B;
  const vE = S.vEyes5 || S.vEyes || V3(0, 2, 0);
  const hum = ramp(t, TT.b5 + 0.15, TT.b5 + 0.7);
  const wipe = pulse(t, TT.cutF + 0.05, 0.18, 0.3, 0.25);                       // nose wiped on the scarf
  const wig = wipe * Math.sin((t - TT.b5 - 0.75) * 2 * Math.PI * 2.4);
  const smile = ramp(t, TT.cutF + 0.45, TT.cutW - 0.05);
  let face = mixFace(FX([['wonder', 0.5], ['sniffle', 0.5]], { mOpen: 0.06, wet: 0.8, tearL: 0.55, tearR: 0.4, saccade: 0.1, lidU: 1.05 }),
    FX([['shySmile', 0.6], ['hopeful', 0.4]], { mTremble: 0.25, wet: 0.7, tearL: 0.4, tearR: 0.3, lidU: 0.9, lidL: 0.3 }), hum);
  face = mixFace(face, FX('happy', { lidU: 0.85, lidL: 0.45, mSmile: 0.75, mTremble: 0.2, wet: 0.7, tearL: 0.35 }), smile);
  if (wipe > 0) { face.lidU = lerp(face.lidU, 0.45, wipe); face.mPout = lerp(face.mPout || 0, 0.5, wipe); }
  return {
    pos: B.FDOOR, yaw: B.fdoorYaw,
    body: { lean: -0.05 + 0.12 * wipe, stretch: 0.02, breathe: 1.0 - 0.3 * hum, shrug: 0.45 * wipe, twist: 0.06 * wig },
    head: { look: vE, track: 0.6 * (1 - 0.7 * wipe), pitch: -0.12 + 0.62 * wipe, yaw: 0.22 * wig, roll: 0.07 * hum + 0.08 * wig },
    gaze: wipe > 0.5 ? null : vE,
    face,
    armL: { preset: 'clasp' }, armR: { preset: 'clasp' },
    extra: { cry: 0.3 * (1 - 0.5 * hum), tremble: 0.15 * (1 - 0.6 * hum), tuftPerk: 0.6 * hum, tuftDroop: 0.2 * (1 - hum), glow: 1.1 + 0.15 * hum },
    blinkAt: [TT.b2 + 0.4, TT.b5 + 0.6, TT.b5 + 1.7],
  };
}

// ------------------------------------------------------------------------------------------------ props
function glintSprite() {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.18, 'rgba(255,255,255,0.6)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.08)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  g.fillStyle = 'rgba(255,255,255,0.9)';
  for (const r of [0, Math.PI / 2]) { g.save(); g.translate(32, 32); g.rotate(r); g.beginPath(); g.moveTo(-31, 0); g.quadraticCurveTo(0, 2, 31, 0); g.quadraticCurveTo(0, -2, -31, 0); g.fill(); g.restore(); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.SpriteMaterial({ map: tex, color: 0xe8f0ff, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false });
  const s = new THREE.Sprite(m); s.renderOrder = 8;
  return s;
}
