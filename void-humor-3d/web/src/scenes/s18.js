// s18 the_magician_lurks — the danger only we can see, right behind the Void's big body.
//   b01 "that right behind the big body of the void,"   slow orbit round the Void's flank from Fear's side toward its
//        back: velvet slides through the foreground; in its shadow a dented top hat rises like a periscope.
//   b02 "the ~depression magician was lurking."   push to the magician pressed against the back of the cloak, one glove
//        on its silhouette edge, peeking round it: sunken eyes slide toward Fear on "magician", the too-wide grin
//        spreads on "lurking", moustache twitches.
//   b03 "With its dagger, and its numbing dust, ready."   low medium: dagger up + admired on "dagger" (glint), pouch up on
//        "numbing", shaken on "dust" (grey glitter falls, the floor goes grey where it lands), fingers wiggle on "ready".
//   b04 "And it's, like, licking its lips, going,"   close: eyes slide to Fear, lids droop with relish, the grey tongue
//        slides along the top lip under the moustache on "licking".
//   b05 MAGICIAN "Ooh. Fear looks very juicy."   hold: slithery whisper, a pinch twirls the moustache tip, eyes half
//        close and head tilts on "juicy".
//   b06 MAGICIAN "Can't wait to knock Fear out."   LAYERED from behind him: he hunches with glee, pinch of dust, dagger
//        higher; tiny Fear far left, unaware, sniffling up at the Void.
//   b07 (silent)   wide along the Void's back: the high-kneed stage tiptoe toward its camera-side flank, a pause on one
//        foot (listening), on again; tilt down to the grey, colour-drained footprints he leaves.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { ROOM, lookFor, sy } from './marks.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { MX } from '../chars/magician.js';
import { V3, toV, loadWords, wordT, pulse, ramp, wobble, gazeSched, fitShot, mixShot, project, cast, ownedGroup, bonusMarks, voidBowed,
  MAGPATH, magTiptoe, magSteps, ensureBonusDecals, clamp, smooth, lerp } from './kit_bonus.js';

let S = null;
const tb = (r) => T(r);

export default {
  id: 's18',
  async setup(app) {
    await loadWords();
    const set = await app.set('BACKROOM');
    const vd = await app.char('VOID'), fear = await app.char('FEAR'), mag = await app.char('MAGICIAN');
    const st = { scene: set.scene, set, vd, fear, mag };
    st.own = ownedGroup(st, 's18own'); set.scene.add(st.own);
    st.glint = glintSprite(); st.own.add(st.glint);
    S = st.S = statics(st);
    console.log('s18 steps', JSON.stringify(magSteps(T('s18b07'), T('s19b05')).map((x) => [x, (x - T('s18b07')).toFixed(2), (x - T('s19b01')).toFixed(2)])));
    st.decals = ensureBonusDecals(set);
    console.log('s18 decals', JSON.stringify(st.decals.items.map((i) => [i.kind, i.pos.map((v) => +v.toFixed(2)), +i.t0.toFixed(2)])));
    return st;
  },
  async update(t, app, st) {
    st.__t = t;
    const { set, vd, fear, mag } = st;
    cast(app, st.scene, ['VOID', 'FEAR', 'MAGICIAN']);
    if (st.own.parent !== st.scene) st.scene.add(st.own);
    const shot = shotAt(t);
    applyShot(app.camera, shot, t, 18);
    set.update(t, { latch: 1, cageDoor: 1 });
    // his close shots: the far key grazes the eye whites into glowing slits; soften it so the sunken irises read
    if (t >= S.T.cut2 && t < S.T.cut6) EYE_LIGHT.uKeyColor.value.multiplyScalar(0.55);
    fear.update(t, fearPoseFn(t));
    vd.update(t, voidPose(t, st));
    mag.update(t, magPose(t, st));
    // the dagger's glint on "dagger"
    const g = pulse(t, S.T.dagger + 0.12, 0.08, 0.06, 0.35);
    st.glint.visible = g > 0.01;
    if (st.glint.visible) { st.glint.position.copy(mag.anchor('dagger')); st.glint.material.opacity = g; st.glint.scale.setScalar(0.05 + 0.14 * g); st.glint.material.rotation = 0.6 * g; }
    st.look = lookFor('s18', set.look);
  },
};

// ------------------------------------------------------------------------------------------------ times
function times() {
  const b1 = tb('s18b01'), b2 = tb('s18b02'), b3 = tb('s18b03'), b4 = tb('s18b04'), b5 = tb('s18b05'), b6 = tb('s18b06'), b7 = tb('s18b07');
  return {
    s0: tb('s18'), end: tb('s18.end'), b1, b2, b3, b4, b5, b6, b7,
    big: wordT('s18b01', 'big', { fallback: 0.45 }),
    void1: wordT('s18b01', 'void', { fallback: 0.9 }),
    magician: wordT('s18b02', 'magician', { fallback: 0.25 }),
    lurking: wordT('s18b02', 'lurking', { fallback: 0.8 }),
    dagger: wordT('s18b03', 'dagger', { fallback: 0.12 }),
    numbing: wordT('s18b03', 'numbing', { fallback: 0.55 }),
    dust: wordT('s18b03', 'dust', { fallback: 0.72 }),
    ready: wordT('s18b03', 'ready', { fallback: 0.85 }),
    licking: wordT('s18b04', 'licking', { fallback: 0.25 }),
    going: wordT('s18b04', 'going', { fallback: 0.75 }),
    juicy: wordT('s18b05', 'juicy', { fallback: 0.8 }),
    fearW: wordT('s18b05', 'fear', { fallback: 0.45 }),
    knock: wordT('s18b06', 'knock', { fallback: 0.45 }),
    out: wordT('s18b06', 'out', { fallback: 0.8 }),
    cut2: b2 + 0.0, cut3: b3 - 0.12, cut4: b4 + 0.3, cut6: b6 - 0.15, cut7: b7 - 0.12,
  };
}

// ------------------------------------------------------------------------------------------------ statics
function statics(st) {
  const { set, vd, fear, mag } = st;
  const out = { T: times() };
  S = out;
  const B = out.B = bonusMarks(set), TT = out.T;
  out.PEEK = ROOM.W(MAGPATH.PEEK); out.FAR = ROOM.W(MAGPATH.FAR);
  vd.update(TT.b3, voidBowed(TT.b3, B, { gaze: toV(B.FDOOR).add(V3(0, 0.6, 0)) }));
  out.vEyes = vd.anchor('eyes'); out.vChest = vd.anchor('chest'); out.vHood = vd.anchor('hoodTop'); out.vBack = vd.anchor('back');
  out.vC = toV(B.V).setY(1.3);
  fear.update(TT.b3, fearPose(TT.b3));
  out.fEyes = fear.anchor('eyes');
  const vy = B.vYaw, vf = V3(Math.sin(vy), 0, Math.cos(vy)), vl = V3(Math.cos(vy), 0, -Math.sin(vy));
  out.vf = vf; out.vl = vl;
  // his glove on the velvet: a point on the Void's back-left surface beside him (silhouette edge from the front-left)
  const toM = toV(out.PEEK).sub(toV(B.V)).setY(0).normalize();
  out.edge = toV(B.V).addScaledVector(toM, 0.72).addScaledVector(vl, 0.22).setY(1.42);
  out.flank = toV(B.V).addScaledVector(vl, 0.86).addScaledVector(vf, -0.1).setY(1.45);     // the Void's left flank silhouette
  // representative magician poses -> anchors
  const at = (tt) => { mag.update(tt, magPose(tt, st)); return { head: mag.anchor('head'), eyes: mag.anchor('eyes'), hip: mag.anchor('hip'), pouch: mag.anchor('pouch'), dagger: mag.anchor('dagger'), handL: mag.anchor('handL') }; };
  out.m2 = at(TT.lurking + 0.3); out.m3 = at(TT.dust); out.m5 = at(TT.b5 + 0.5); out.m6 = at(TT.knock);
  // ---- cameras
  // b01 orbit: centre the Void (y 1.3), radius 4.2, height 1.3, local yaw -30 -> +35 deg (from Fear's side round its flank)
  const vL = ROOM.L(B.V);
  out.orbit = (deg) => { const a = deg * Math.PI / 180; return ROOM.W(vL[0] + 4.2 * Math.sin(a), 1.3, vL[2] + 4.2 * Math.cos(a)); };
  // b02 MAG_MED: from the camera side at his depth: the Void's flank fills the left, his face peeks out past it
  out.MED = fitShot([[out.m2.eyes, 440, 350]], 33, ROOM.W(3.5, 1.62, 2.45), out.m2.eyes, { posReg: 10, free: [0, 0, 0] });
  // b03 low medium (face y~330, hands ~500)
  const ml = ROOM.L(out.m3.eyes);
  out.LOW = fitShot([[out.m3.eyes, 390, 330], [out.m3.pouch, 470, 560, 0.5]], 40, ROOM.W(ml[0] + 0.25, 0.95, ml[2] + 1.75), out.m3.eyes, { posReg: 0.3, yMin: 0.85, yMax: 1.1 });
  // b04/b05 close on his face (3/4 front, from the camera side)
  const cu0 = toV(out.m5.head).add(ROOM.V(-0.15, 0, 1.35).sub(ROOM.V(0, 0, 0))).setY(out.m5.eyes.y - 0.04);
  out.CU_A = fitShot([[out.m5.eyes, 390, 390]], 31, cu0, out.m5.eyes, { posReg: 10, free: [0, 0, 0] });
  out.CU_B = fitShot([[out.m5.eyes, 385, 395]], 28, toV(out.CU_A.pos).lerp(toV(out.m5.eyes), 0.1), out.m5.eyes, { posReg: 10, free: [0, 0, 0] });
  // b06 LAYERED from behind-left of him: he is foreground right, the Void's flank middle, tiny Fear far left
  // (the Void hides Fear from anything behind it: the dramatic irony reads from the camera side, wide)
  out.LAY = fitShot([[out.m6.head, 590, 390], [out.fEyes, 120, 650]], 52, ROOM.W(5.25, 1.3, 4.35), out.fEyes, { posReg: 10, free: [0, 0, 0] });
  // b07 wide tracking from behind-left (his tiptoe along its back), then tilt down to the prints
  out.WIDE_POS = toV(out.PEEK).lerp(toV(out.FAR), 0.5).addScaledVector(vl, 2.9).addScaledVector(vf, -1.1).setY(1.7);
  const L2 = (n) => { const a = vd.anchor(n); return a ? ROOM.L(a).map((v) => +v.toFixed(2)) : null; };
  console.log('s18 void', JSON.stringify({ sideL: L2('sideL'), sideR: L2('sideR'), shL: L2('shoulderL'), shR: L2('shoulderR'), back: L2('back'), backLow: L2('backLow'), handL: L2('handL'), handR: L2('handR'), V: ROOM.L(B.V).map((v) => +v.toFixed(2)) }));
  console.log('s18 statics', JSON.stringify({ med: out.MED.err.toFixed(1), low: out.LOW.err.toFixed(1), lay: out.LAY.err.toFixed(1), layPos: ROOM.L(out.LAY.pos).map((v) => +v.toFixed(2)), pouch3: out.m3.pouch && out.m3.pouch.toArray().map((v) => +v.toFixed(2)), pouch3L: out.m3.pouch && ROOM.L(out.m3.pouch).map((v) => +v.toFixed(2)), patch: ROOM.W(MAGPATH.PATCH).map((v) => +v.toFixed(2)) }));
  return out;
}

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const TT = S.T;
  if (t < TT.cut2) {                                           // b01 orbit
    const u = ramp(t, TT.s0 - 0.1, TT.cut2 + 0.2, 'inOut');
    const deg = lerp(-30, 70, u);
    const look = S.vC.clone().lerp(S.fEyes, 0.3 * (1 - smooth(clamp(u / 0.4)))).lerp(toV(S.PEEK).setY(1.35), smooth(clamp((u - 0.25) / 0.75)) * 0.8);
    return { pos: S.orbit(deg), look: look.toArray(), fov: 44, drift: 0.2 };
  }
  if (t < TT.cut3) return mixShot(S.MED, { ...S.MED, pos: toV(S.MED.pos).lerp(toV(S.MED.look), 0.08).toArray() }, ramp(t, TT.cut2, TT.cut3, 'inOut'));
  if (t < TT.cut4) return mixShot(S.LOW, { ...S.LOW, pos: toV(S.LOW.pos).lerp(toV(S.LOW.look), 0.06).toArray() }, ramp(t, TT.cut3, TT.cut4, 'linear'));
  if (t < TT.cut6) return mixShot(S.CU_A, S.CU_B, ramp(t, TT.cut4, TT.cut6, 'inOut'));
  if (t < TT.cut7) return { ...S.LAY, pos: toV(S.LAY.pos).lerp(toV(S.LAY.look), 0.05 * ramp(t, TT.cut6, TT.cut7, 'linear')).toArray() };
  // b07: track the tiptoe, then tilt down to the prints
  const m = magTiptoe(t);
  const hip = toV(m.pos).setY(1.0);
  const trail = toV(S.PEEK).lerp(toV(S.FAR), 0.45).setY(0.0);
  const down = ramp(t, m.tOut - 0.15, TT.end + 0.1, 'inOut');
  const look = hip.lerp(trail, 0.72 * down);
  const pos = toV(S.WIDE_POS).add(toV(m.pos).sub(toV(S.PEEK)).multiplyScalar(0.4)).add(V3(0, -0.15 * down, 0));
  return { pos: pos.toArray(), look: look.toArray(), fov: 50 - 6 * down, drift: 0.2 };
}
function shotStart(t) {
  const TT = S.T;
  return t < TT.cut2 ? -1e9 : t < TT.cut3 ? TT.cut2 : t < TT.cut4 ? TT.cut3 : t < TT.cut6 ? TT.cut4 : t < TT.cut7 ? TT.cut6 : TT.cut7;
}

// ------------------------------------------------------------------------------------------------ Fear (at the open door, looking up)
function fearPoseFn(t) { const s0 = shotStart(t); return (tt) => fearPose(Math.max(tt, s0)); }
function fearPose(t) {
  const TT = S.T, B = S.B;
  const vE = S.vEyes || V3(0, 2, 0);
  const sn1 = pulse(t, TT.b1 + 0.9, 0.12, 0.05, 0.3), sn2 = pulse(t, TT.knock - 0.1, 0.12, 0.05, 0.35), sn3 = pulse(t, TT.b7 + 0.9, 0.12, 0.05, 0.3);
  const sniff = sn1 + sn2 + sn3;
  const face = mixFace(FX([['wonder', 0.45], ['sniffle', 0.55]], { mOpen: 0.08, wet: 0.9, tearL: 0.6, tearR: 0.45, saccade: 0.12 }),
    FX('sniffle', { mPout: 0.6, lidU: 0.7 }), clamp(sniff));
  return {
    pos: B.FDOOR, yaw: B.fdoorYaw,
    body: { lean: -0.05, stretch: 0.02, breathe: 1.1, shrug: 0.25 * sniff },
    head: { look: vE, track: 0.6, pitch: -0.12 + 0.08 * sniff },
    gaze: vE,
    face,
    armL: { preset: 'clasp' }, armR: { preset: 'clasp' },
    extra: { cry: 0.35, tremble: 0.18, tuftDroop: 0.2, glow: 1.1 },
    blinkAt: [TT.b2 + 0.5, TT.b5 + 1.0, TT.knock + 0.15, TT.b7 + 1.6],
  };
}

// ------------------------------------------------------------------------------------------------ the Void (still, bowed, soft)
function voidPose(t, st) {
  const TT = S.T;
  const face = VX('gentle', { lidU: 0.66, lidL: 0.4, browIn: 0.45, mSmile: 0.34, blush: 0.15, saccade: 0.15, autoBlink: 0.6 });
  return voidBowed(t, S.B, { gaze: st.fear, face, blinkAt: [TT.b4 + 0.4, TT.b7 + 1.2], extra: { stars: 1.4, cosmos: 0.12 } });
}

// ------------------------------------------------------------------------------------------------ the magician
function magPose(t, st) {
  const TT = S.T, B = S.B;
  const fearE = S.fEyes || toV(B.FDOOR).add(V3(0, 0.65, 0));
  // ---- where / which way
  const rise = k(t, [[TT.big - 0.2, 0], [TT.void1 + 0.2, 0.45, 'inOut'], [TT.magician, 0.6, 'inOut'], [TT.lurking + 0.1, 1, 'inOut']]);   // periscope
  const side = ramp(t, TT.magician - 0.25, TT.lurking + 0.25, 'inOut');                                           // leans out round the flank
  let pos = S.PEEK;
  const faceFear = Math.atan2(fearE.x - pos[0], fearE.z - pos[2]);
  let yaw = faceFear + 0.55;          // body cheated 3/4 to the camera side; the eyes slide sideways to Fear
  let walk = { amount: 0 };
  const inB7 = t >= TT.b7 - 0.05;
  let tip = null;
  if (inB7) {
    tip = magTiptoe(t);
    pos = tip.pos;
    yaw = lerp(faceFear + 0.55, tip.yaw, ramp(t, TT.b7 - 0.05, tip.tA + 0.3));
    walk = tip.walk;
  }
  // ---- body
  const glee = pulse(t, TT.b6 + 0.05, 0.25, TT.out - TT.b6 + 0.2, 0.5);
  const listen = inB7 ? ramp(t, tip.tOut - 0.1, tip.tOut + 0.2) : 0;
  const body = {
    crouch: lerp(1.0, 0.12, rise) + 0.05 * glee,
    peek: (0.7 * side + 0.15 * ramp(t, TT.cut3, TT.cut3 + 0.3)) * (1 - 0.6 * ramp(t, TT.b6 - 0.2, TT.b6)) * (inB7 ? 0.2 : 1),
    hunch: 0.25 + 0.2 * glee - 0.1 * rise,
    lean: 0.08 + 0.05 * glee,
    shrug: 0.45 * glee,
    snicker: 0.75 * glee,
    tiptoe: inB7 ? 0.6 : 0.25 * rise,
    tilt: -0.12 * listen,
  };
  // ---- head / gaze
  const admire = pulse(t, TT.dagger + 0.05, 0.18, 0.55, 0.3);           // looks at his own dagger
  const gaze = gazeSched(t, [
    [TT.s0 - 1, toV(S.vBack || B.V).setY(1.4)],                         // nose to the velvet
    [TT.magician + 0.12, fearE, 0.35],                                 // the sunken eyes slide toward Fear
    [TT.dagger + 0.08, () => (st.mag.anchor('dagger') || fearE), 0.12],
    [TT.dagger + 0.85, fearE, 0.18],
  ]);
  const head = {
    follow: 0.15 + 0.15 * side, look: fearE,
    roll: 0.12 * pulse(t, TT.juicy - 0.1, 0.25, 0.5, 0.6) + 0.22 * listen + 0.05 * admire,
    pitch: -0.05 * rise + 0.12 * admire,
    yaw: 0.2 * admire,
  };
  // ---- arms
  const daggerUp = ramp(t, TT.dagger - 0.12, TT.dagger + 0.22, 'out');
  const pouchUp = ramp(t, TT.numbing - 0.1, TT.numbing + 0.25, 'out');
  const shake = (t > TT.dust - 0.05 && t < TT.dust + 0.5) ? Math.sin((t - TT.dust) * 2 * Math.PI * 6.5) * (1 - (t - TT.dust) / 0.55) : 0;
  const twirl = pulse(t, TT.fearW - 0.35, 0.3, TT.juicy - TT.fearW + 0.5, 0.35);
  const higher = ramp(t, TT.b6 + 0.1, TT.knock + 0.1, 'inOut');
  const armR = daggerUp < 0.001
    ? { preset: [['dagger_low', 1]] }
    : { preset: [['dagger_low', 1 - daggerUp + 1e-4], ['dagger_ready', daggerUp]], offset: [0, 0.14 * higher + 0.06 * (inB7 ? 1 : 0), 0] };
  let armL;
  if (t < TT.numbing - 0.1) armL = { preset: 'creep', reach: clamp(rise * 1.2) };
  else armL = { preset: [['pouch', 1 - twirl + 1e-4], ['chin', twirl]], offset: [0, (0.16 * pouchUp + 0.04 * shake) * (1 - twirl) + 0.04 * twirl, 0.025 * shake] };
  if (t >= TT.cut6 - 0.05 && !inB7) armL = { preset: 'pouch', offset: [0, 0.05 * glee, 0] };
  if (inB7) armL = { preset: 'pouch' };
  // ---- face
  const face = k(t, [
    [TT.s0 - 1, MX('lurk', { lidU: 0.7 })],
    [TT.magician + 0.1, MX('lurk', { lidU: 0.62, lidL: 0.4 })],                                   // eyes slide to Fear (lids heavy)
    [TT.lurking, MX([['lurk', 0.5], ['gloat', 0.5]], { mOpen: 0.0, mTeethU: 0.7 })],            // the too-wide grin spreads
    [TT.dagger + 0.1, MX('gloat', { lidU: 0.85, browOut: 0.85 })],                              // ooh, shiny
    [TT.dust, MX('scheme', { mTeethU: 0.6 })],
    [TT.ready, MX('scheme', { mTeethU: 0.8, mSmile: 1 })],
    [TT.licking - 0.25, MX('hungry', { lidU: 0.42, mTongue: 0.4 })],                             // relish
    [TT.going, MX('hungry', { lidU: 0.4 })],
    [TT.b5 - 0.05, MX('whisper', { talk: 0.6 })],
    [TT.juicy - 0.05, MX('whisper', { talk: 0.6, lidU: 0.28, lidL: 0.55, mSmile: 0.75 })],      // eyes half-close on "juicy"
    [TT.b5 + 3.2, MX('whisper', { talk: 0.6, lidU: 0.5 })],
    [TT.b6 - 0.05, MX([['snicker', 0.55], ['whisper', 0.45]], { talk: 0.55 })],
    [TT.out + 0.2, MX('snicker', { talk: 0.5 })],
    [TT.b7 - 0.05, MX('lurk', { lidU: 0.85 })],
  ]);
  if (inB7) {          // listening on one foot: eyes wide, brows up
    const L = listen;
    face.lidU = lerp(face.lidU, 1.15, L); face.browOut = lerp(face.browOut, 0.9, L); face.browIn = lerp(face.browIn, 0.3, L); face.mPress = 0.4 * L;
  }
  // moustache twitch: two quick smirk flicks after "lurking"
  face.mAsym = (face.mAsym || 0) + 0.35 * pulse(t, TT.lurking + 0.45, 0.05, 0.03, 0.08) - 0.3 * pulse(t, TT.lurking + 0.62, 0.05, 0.03, 0.1);
  const speech = t > TT.b5 - 0.2 && t < TT.b6 + 3.0 ? undefined : false;
  const extra = {
    lick: ramp(t, TT.licking, TT.licking + 1.2, 'linear') * (t < TT.b5 ? 1 : 0),
    dust: 0.85 * pulse(t, TT.dust - 0.05, 0.12, 0.25, 0.3) + 0.35 * pulse(t, TT.knock - 0.2, 0.15, 0.2, 0.3),
    tap: Math.max(pulse(t, TT.ready, 0.1, 0.6, 0.25), 0.6 * pulse(t, TT.b1 + 0.0, 0.2, 2.0, 0.3) * 0),
  };
  return { pos, yaw, body, walk, head, gaze, face, armL, armR, extra, speech, blinkAt: [TT.magician + 0.05, TT.b4 + 0.1, TT.b6 + 0.2] };
}

// ------------------------------------------------------------------------------------------------ props
function glintSprite() {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.18, 'rgba(255,255,255,0.7)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.12)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  g.fillStyle = 'rgba(255,255,255,0.95)';
  for (const r of [0, Math.PI / 2]) { g.save(); g.translate(32, 32); g.rotate(r); g.beginPath(); g.moveTo(-31, 0); g.quadraticCurveTo(0, 2, 31, 0); g.quadraticCurveTo(0, -2, -31, 0); g.fill(); g.restore(); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.SpriteMaterial({ map: tex, color: 0xe8f0ff, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false });
  const s = new THREE.Sprite(m); s.renderOrder = 8;
  return s;
}
