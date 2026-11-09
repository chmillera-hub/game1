// s22 a_moment_with_my_fear — the whole point. A galaxy rises from the Void's open hands, splits into more, nebulae pour
// from its sleeves and the back room dissolves into the cosmos (COSMOS set inside BACKROOM). Fear's tears of awe; "Why
// are you showing me this?"; the silent two-layer answer (a guilty flick of the eyes to the corner, then a soft smile and
// a big hand resting on Fear's shoulder). The pull-back reveals the evidence in the far corner. A little galaxy settles
// in Fear's palm; a last star lands on its scarf. BUTTON: the bucket lifts an inch, the Void's flat look, the bucket
// sinks. The Void looks into the lens and winks. "Tee-hee." Pull back to the end-title wide in the nebula.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { CTX } from '../core/context.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, ease, fbm1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { MX } from '../chars/magician.js';
import { ROOM, sy, lookFor } from './marks.js';
import { ensureBonusDecals } from './kit_bonus.js';
import { loadLines, W, A, V, add, sub, mix3, LD, pulse, jiggle, stamp, own, live, solve, aim, blendShot, pix, marks, times, voidSpot, wreckPose, cornerOpts, bookPoint, BOOK_FING } from './kit_s20_22.js';

const ID = 's22';

export default {
  id: ID,
  async setup(app) {
    await loadLines();
    const set = await app.set('BACKROOM');
    ROOM.fit(set);
    ensureBonusDecals(set);   // the magician's grey footprints + dust patch stay until the cosmos takes the floor
    const cos = await app.set('COSMOS');
    const [vd, fear, mag] = await Promise.all([app.char('VOID'), app.char('FEAR'), app.char('MAGICIAN')]);
    const fx = new Particles({ max: 140, intensity: 1.5 });
    const fxS = new Particles({ max: 60, intensity: 1.0, blending: 'add' });      // soft nebula smoke
    own(ID, fx.mesh); own(ID, fxS.mesh);
    // the cosmos group lives in the shared BACKROOM scene only while this scene draws it
    const prev = set.scene.onBeforeRender;
    set.scene.onBeforeRender = function (...a) {
      if (cos.group.parent === set.scene) cos.group.visible = live(ID);
      if (prev) prev.apply(this, a);
    };
    return { scene: set.scene, set, cos, vd, fear, mag, fx, fxS, look: lookFor(ID, set.look) };
  },

  async update(t, app, st) {
    stamp(ID, t);
    const { set, cos, vd, fear, mag, fx, fxS } = st;
    for (const o of [vd.root, fear.root, mag.root, fx.mesh, fxS.mesh]) st.scene.add(o);
    cos.attach(set.scene);
    const c = times(), M = marks(), L = beats();
    const shot = shotId(t, L);
    st.shot = shot;
    const vs = voidSpot(t);
    const fwd = rotY([0, 0, 1], vs.yaw);
    const palms = bookPoint(vs);
    const reveal = k(t, [[c.galRise - 0.2, 0], [c.galaxies, 0.12, 'inOut'], [L.B2, 0.3, 'linear'], [L.B3, 0.8, 'linear'], [L.B3 + 1.8, 1, 'out']]);
    const corner = add(M.CRASH, [0, 0.55, 0]);
    const lg = littleGalaxy(t, L, M, fear);

    // ------------------------------------------------------------------ VOID
    const vPose = (pass) => {
      const fe = pass ? fear.anchor('eyes') : null;
      const sh = pass ? fear.anchor('shoulderR') : null;
      // faces
      const Fsoft = VX('gentle', { lidU: 0.76, lidL: 0.5, mSmile: 0.55, browIn: 0.4, blush: 0.22 });
      const Fwarm = VX('tender', { lidU: 0.74, lidL: 0.52, mSmile: 0.6, browIn: 0.55, browOut: 0.0, blush: 0.3, wet: 0.4 });
      const Flisten = VX('tender', { lidU: 1.04, lidL: 0.46, mSmile: 0.3, mPress: 0.3, browIn: 0.72, browOut: 0.1, wet: 0.7, tearL: 0.28, blush: 0.25 });
      const Fguilty = VX('tender', { lidU: 0.92, lidL: 0.4, mSmile: 0.25, mPress: 0.5, browIn: 0.6, wet: 0.6, tearL: 0.28 });
      const Fcres = VX('gentle', { lidU: 0.7, lidL: 0.62, mSmile: 0.66, mPress: 0.25, browIn: 0.58, browOut: -0.02, blush: 0.35, wet: 0.6, tearL: 0.22 });
      const Fhalf = VX('tender', { lidU: 0.6, lidL: 0.5, mSmile: 0.55, mPress: 0.2, browIn: 0.55, browOut: -0.05, wet: 0.85, blush: 0.3 });
      const Fflat = VX('neutral', { lidU: 0.5, lidL: 0.32, lidAngry: 0.12, mSmile: -0.05, mPress: 0.55, mWide: 0.2, browIn: -0.18, browSq: 0.3, browOut: 0.1, saccade: 0 });
      const Fwink = VX('happy', { lidU: 0.86, lidL: 0.55, mSmile: 0.82, mAsym: 0.42, mOpen: 0.02, browIn: 0.3, browOut: 0.42, browAsym: 0.3, blush: 0.4, saccade: 0 });
      let face = k(t, [[ID, Fsoft], [L.B2, Fsoft], [L.B2 + 0.6, Fwarm, 'inOut'], [L.B4 - 0.1, Fwarm], [L.B4 + 0.5, Flisten, 'inOut'],
        [L.flick - 0.02, Flisten], [L.flick + 0.05, Fguilty, 'out'], [L.flick + 0.45, Fguilty], [L.flick + 0.95, Fcres, 'inOut'],
        [L.B6 + 1.0, Fcres], [L.B7 - 0.3, Fhalf, 'inOut'], [L.B9 + 0.85, Fhalf], [L.B9 + 1.05, Fflat, 'out'], [L.B9 + 2.4, Fflat], [L.B9 + 2.75, Fhalf, 'inOut'],
        [L.B10 + 0.15, Fhalf], [L.B10 + 0.6, Fwink, 'inOut'], [L.B12, Fwink], [L.B12 + 1.2, Fhalf, 'inOut']]);
      // the wink: the character's LEFT lid closes slow and reopens on "Tee-hee"
      const wink = k(t, [[L.wink0, 0], [L.wink0 + 0.28, 1, 'inOut'], [L.wink1, 1], [L.wink1 + 0.3, 0, 'inOut']]);
      if (wink > 0) face = { ...face, lidUL: lerp(face.lidU, 0.0, wink), lidLL: lerp(face.lidL, 0.75, wink), mAsym: face.mAsym + 0.15 * wink };
      // the late lids close slowly at the very end (safe)
      face.autoBlink = 0;
      face.tearL = Math.max(face.tearL || 0, 0.25 * smooth(clamp((t - L.B4) / 1.2)));
      // gaze: Fear's face; the guilty flick to the corner (B5); the corner (B9 flat look); the lens (B10)
      let gaze = fe;
      if (pass) {
        if (t >= L.flick && t < L.flick + 0.38) gaze = corner;
        else if (t >= L.B9 + 0.85 && t < L.B9 + 2.45) gaze = corner;
        else if (t >= L.lens0 && t < L.lens1) gaze = 'camera';
      }
      // arms: palms up "book" -> the galaxy rises -> arms lift slowly ('open') pouring nebulae -> LEFT hand onto Fear's
      // RIGHT shoulder (contact) and stays; the right hand rests on its belly
      const bookL = add(palms, rotY([0.05, 0, 0.06], vs.yaw)), bookR = add(palms, rotY([-0.05, 0, 0.06], vs.yaw));
      const palmUp = rotY([0, 1, 0.1], vs.yaw);
      const open = k(t, [[L.B2 - 0.3, 0], [L.B3 - 0.2, 1, 'inOut'], [L.B4, 1], [L.B5 - 0.2, 0.55, 'inOut']]);
      const onSh = k(t, [[L.hand0, 0], [L.hand1, 1, 'inOut']]);
      // the palm settles on top of Fear's (camera-side) shoulder, the big fingers draping down its back (not over its face)
      const fy = fearYaw(t, L, c, M), fback = [-Math.sin(fy), 0, -Math.cos(fy)];
      const shT = sh ? add(A(sh), [fback[0] * 0.09, 0.075 + 0.012 * Math.sin(t * 1.2) * smooth(clamp((t - L.B12) / 1)), fback[2] * 0.09]) : add(M.FOUT, [0, 0.55, 0]);
      const cup = 1 - smooth(clamp((t - (L.B2 - 0.4)) / 0.8));
      const armBook = (side) => ({ preset: 'hold', target: side > 0 ? bookL : bookR, reach: 1, palm: palmUp, fingers: rotY(BOOK_FING, vs.yaw), hand: { curl: 0.2, cup: 0.5, spread: 0.15, thumb: 0.5 } });
      let armL, armR;
      if (cup > 0.001) {
        armL = { ...armBook(1), reach: 1 };
        armR = { ...armBook(-1), reach: 1 };
        if (cup < 1) { armL = { preset: 'open', target: bookL, reach: cup, hand: { curl: 0.15, spread: 0.4, thumb: 0.7 } }; armR = { preset: 'open', target: bookR, reach: cup, hand: { curl: 0.15, spread: 0.4, thumb: 0.7 } }; }
      } else {
        armL = { preset: 'open', from: 'rest', mix: Math.max(open, 0.25) };
        armR = { preset: 'open', from: 'belly', mix: Math.max(open, 0.0) };
        if (open < 0.5 && t > L.B4) armR = { preset: 'belly', from: 'open', mix: 1 - open * 2 };
      }
      if (onSh > 0.001) armL = { preset: 'pat', from: 'open', mix: onSh, target: shT, reach: onSh, palm: [fback[0] * 0.3, -1, fback[2] * 0.3], fingers: [fback[0] * 0.75, -0.65, fback[2] * 0.75], hand: { curl: 0.3, cup: 0.45, spread: 0.12, thumb: 0.3 } };
      const hum = pulse(t, L.B12, T(ID + '.end') + 1, 0.6, 0.6);
      return {
        pos: vs.pos, yaw: vs.yaw,
        body: { lean: 0.16 + 0.06 * onSh, breathe: 1, tilt: 0.02 * Math.sin(t * 1.4) * hum + 0.04 * onSh, twist: 0.1 * onSh },
        head: { pitch: 0.3 + 0.05 * onSh, yaw: 0.12 + 0.1 * onSh, roll: 0.04 + 0.03 * Math.sin(t * 1.4) * hum },
        gaze: pass ? gaze : null,
        face,
        blinkAt: [L.B1 + 0.6, L.B4 + 0.9, L.flick + 0.6, L.B8 + 1.9, L.B9 + 2.55, T(ID + '.end') - 1.4],
        armL, armR,
        extra: { cosmos: smooth(clamp(reveal * 1.2)), stars: 1.4 + 0.5 * reveal + 0.25 * Math.sin(t * 2.6) * hum, motes: 0.9, eyeGlow: 1 + 0.15 * reveal },
      };
    };

    // ------------------------------------------------------------------ FEAR
    const fearPose = (tt) => fearPoseAt(st, tt, L, c, M, vs, palms, corner);
    const shotStart = L.starts[shot];
    const fPose = (pass) => (pass ? (tt) => fearPose(Math.max(tt, shotStart)) : fearPose(t));

    // ------------------------------------------------------------------ MAGICIAN (in the wreck)
    const lift = k(t, [[c.lift0, 0], [c.lift1, 1, 'out'], [c.sink0, 1], [c.clunk, 0, 'in']]);
    const mPose = (pass) => {
      const w = wreckPose(t, M);
      // still dazed in s22 (birdies keep circling), but for the button the swirl fades so a real eye can peek
      const dz = 1 - pulse(t, L.B9 - 0.6, L.B9 + 2.9, 0.4, 0.4);
      w.extra.dizzy = dz; w.extra.stars = 0.75;
      const twitch = pulse(t, L.chest, L.chest + 0.35, 0.05, 0.2);
      w.body.bounce = 0.02 * twitch; w.body.recoil = 0.06 * twitch;
      if (lift > 0 || (t > L.B9 - 0.3 && t < L.B9 + 3)) {
        const see = smooth(clamp((t - (L.B9 + 1.55)) / 0.12));
        w.face = MX([['curious', 0.6 * (1 - see)], ['startled', see], ['dazed', 0.4 * (1 - see)]], { lidU: 0.9 + 0.45 * see });
        w.gaze = pass ? A(vd.anchor('eyes')) : null;
        w.head = { ...w.head, roll: 0.08, pitch: 0.05 };
      }
      return w;
    };

    solve(t, [[vd, vPose], [mag, mPose], [fear, fPose]], () => {
      applyShot(app.camera, frameShot(st, t, shot, L, c, M, vs), t, 22);
    });

    // ------------------------------------------------------------------ set + cosmos
    const cosV = smooth(clamp(reveal / 0.8));
    set.update(t, { ...cornerOpts(t, mag, { lift: 0.06 * lift }), cosmos: cosV, voidLight: { pos: add(vs.pos, [-0.62, 1.95, 0.85]), intensity: 3.2 } });
    if (set.props.bucketHat && lift > 0) set.props.bucketHat.rotateX(-0.22 * lift);
    const center = mix3(vs.pos, M.FOUT, 0.5); center[1] = 0;
    cos.update(t, { reveal, center, source: reveal < 0.3 ? palms : A(vd.anchor('chest')), radius: 11, height: 8, lift: 1.5, drift: 1, glyphs: shot === 9 ? 0.4 : 1 });

    // ------------------------------------------------------------------ particles
    fx.begin(); fxS.begin();
    drawGalaxies(fx, t, L, c, palms, lg, vs);
    // nebulae pour from its sleeves and the cloak like slow luminous smoke (b02-b03), then a faint ongoing breath
    const hl = vd.anchor('handL'), hr = vd.anchor('handR');
    const smokeA = 0.13 * (1 - 0.6 * smooth(clamp((t - (L.B3 + 2)) / 2)));
    for (const [i, h] of [[0, hl], [1, hr]]) {
      if (!h) continue;
      const o = A(h);
      fxS.stream({ t, seed: 2201 + i, t0: L.B2 - 0.25, t1: L.B4, rate: 4, life: 3.2, origin: o, vel: [0, 0.35, 0], spread: [0.35, 0.15, 0.35], drag: 0.6,
        size: [0.35, 0.6], grow: 2.6, color: [0x9a6cff, 0x58d6e8, 0xff8fc6, 0x7f8cff], alpha: smokeA, fade: [0.25, 0.55], cell: CELL.nebula, spin: 0.25 });
    }
    fxS.stream({ t, seed: 2203, t0: L.B2 - 0.1, t1: L.B4, rate: 3, life: 3.5, origin: (tb) => add(vs.pos, rotY([Math.sin(tb * 7.1) * 0.9, 0.7, 0.55], vs.yaw)), vel: [0, 0.3, 0],
      spread: [0.45, 0.12, 0.45], drag: 0.5, size: [0.45, 0.7], grow: 2.4, color: [0x7a5cff, 0x3fc2d6, 0xe27bd0], alpha: smokeA * 0.9, fade: [0.25, 0.55], cell: CELL.nebula, spin: 0.2 });
    // b08: one last star drifts down and settles on Fear's scarf
    const ls = lastStar(t, L, fear);
    if (ls) { fx.add(ls.pos, 0.07 * ls.s, 0xfff3d6, 0.95 * ls.a, t * 0.5, CELL.star); fx.add(ls.pos, 0.16 * ls.s, 0xffe0a0, 0.3 * ls.a, 0, CELL.dot); }
    fx.end(); fxS.end();

    if (globalThis.DBG22) {
      const cam = app.camera;
      console.log('DBG22', t.toFixed(2), 'shot', shot, 'rev', reveal.toFixed(2), JSON.stringify({ v: pix(cam, vd.anchor('eyes')), f: pix(cam, fear.anchor('eyes')), palms: pix(cam, palms), m: pix(cam, mag.anchor('head')), crash: pix(cam, M.CRASH), lg: pix(cam, lg.pos) }));
    }
    // look: s21's look -> the cosmos look as the room dissolves
    const a = lookFor('s21', set.look), b = cos.blendLook(lookFor(ID, set.look), 0.5);
    const w = smooth(reveal);
    const look = {};
    for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) {
      const x = a[key], y = b[key];
      look[key] = typeof x === 'number' && typeof y === 'number' ? lerp(x, y, w) : (w < 0.5 ? (x ?? y) : (y ?? x));
    }
    st.look = look;
  },
};

// ======================================================================================================== timing
function beats() {
  if (beats._c) return beats._c;
  const L = {};
  for (let i = 1; i <= 13; i++) L['B' + i] = T(`s22b${String(i).padStart(2, '0')}`);
  L.S = T(ID); L.E = T(ID + '.end');
  L.B4e = T('s22b04.end'); L.B5e = T('s22b05.end');
  L.cutC = L.B4e + 0.15;
  L.flick = L.B5 + 0.32;
  L.hand0 = L.B5 + 0.75; L.hand1 = L.B5 + 1.55;
  L.lean0 = L.B5 + 1.45;
  L.chest = W('s22b06', 'chest');
  L.kick = W('s22b06', 'kick');
  L.lens0 = L.B10 + 0.12; L.lens1 = L.B11 + 0.32;
  L.wink0 = L.B10 + 0.75; L.wink1 = L.B11 + 0.08;
  L.cutJ = T('s22b11.end') + 0.05;
  L.starts = [L.S, L.B3, L.cutC, L.B7, L.B8, L.B9, L.B9 + 0.8, L.B9 + 1.6, L.B9 + 2.4, L.B10, L.cutJ];
  beats._c = L;
  return L;
}
function shotId(t, L) {
  const s = L.starts;
  for (let i = s.length - 1; i >= 0; i--) if (t >= s[i]) return i;
  return 0;
}
function rotY(v, yaw) { const c = Math.cos(yaw), s = Math.sin(yaw); return [v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c]; }

// ======================================================================================================== Fear
function fearYaw(t, L, c, M) {
  return k(t, [[c.galaxies + 0.1, M.yFOUT], [L.B3 - 0.15, 1.02, 'inOut'], [L.B3 + 0.3, 1.1, 'inOut'], [L.B5 + 0.2, 1.1], [L.B5 + 1.3, 1.8, 'inOut']]);
}
function fearPoseAt(st, t, L, c, M, vs, palms, corner) {
  const { vd, fear } = st;
  const ve = vd.anchor('eyes') ? A(vd.anchor('eyes')) : add(vs.pos, [0, 2.0, 0]);
  const lg = littleGalaxy(t, L, M, fear);
  const yaw = fearYaw(t, L, c, M);
  // where to look: the rising galaxy -> all around (the cosmos) -> the Void's face (b04 search, two eyes) -> eyes shut on
  // the hand -> the little galaxy -> up at the Void -> the star on the scarf -> up -> the galaxy held up
  const up1 = ROOM.W(add(ROOM.M.FOUT.p, [0.5, 1.55, 1.4]));   // up and out toward the FEAR_CU lens side: the upturned face reads
  const up2 = add(M.FOUT, [1.6, 2.6, 1.8]);
  const galRise = add(palms, [0, 0.25 + 0.3 * smooth(clamp((t - c.galRise) / 1.4)), 0]);
  const ls = lastStar(t, L, fear);
  const g = k(t, [[L.S, palms], [c.galRise, palms], [c.galRise + 0.4, galRise, 'inOut'], [c.galaxies, galRise], [c.galaxies + 0.5, up2, 'inOut'], [L.B2 + 0.9, up1, 'inOut'],
    [L.B3 + 1.1, up1], [L.B3 + 2.2, up2, 'inOut'], [L.B4 - 0.25, up2], [L.B4 + 0.05, ve, 'inOut'], [L.B6 + 0.3, ve], [L.B6 + 1.4, up1, 'inOut'], [L.B6 + 2.4, lg.pos, 'inOut'],
    [L.B7 + 0.5, lg.pos], [L.B8 - 0.15, ve, 'inOut'], [L.B8 + 1.0, ve], [L.B8 + 1.35, ls ? ls.pos : ve, 'inOut'], [L.B9 - 0.2, ls ? ls.pos : ve], [L.B9 + 0.2, ve, 'inOut'],
    [L.B12 - 0.2, ve], [L.B12 + 0.6, lg.pos, 'inOut']]);
  // micro search between the Void's two eyes during the question
  const search = pulse(t, L.B4 + 0.1, L.B4e, 0.1, 0.1) * 0.06 * Math.sign(Math.sin((t - L.B4) * 5.5));
  const gaze = add(g, [search, 0, 0]);
  // faces
  const Fwide = FX('wonder', { lidU: 1.3, pupil: 1.5, mOpen: 0.3, wet: 0.9 });
  const Fdown = FX('wonder', { lidU: 1.05, mOpen: 0.12, pupil: 1.35, mSmile: 0.12 });
  const Fawe = FX('awe', { lidU: 1.12, mOpen: 0.26, mRound: 0.25, mSmile: 0.22, browIn: 0.5, browOut: 0.32, lidSad: 0.05, wet: 1, tearL: 0.6, tearR: 0.55 });
  const Flaugh = FX('awe', { lidU: 0.9, lidL: 0.35, mOpen: 0.22, mSmile: 0.55, browIn: 0.55, wet: 1, tearL: 0.7, tearR: 0.65 });
  const Fask = FX('awe', { lidU: 1.08, mSmile: 0.08, browIn: 0.75, browOut: 0.25, wet: 1, tearL: 0.75, tearR: 0.75, talk: 0.85 });
  const Fclosed = FX('trust', { lidU: 0.08, lidL: 0.4, mSmile: 0.4, browIn: 0.45, wet: 0.8, tearL: 0.6, tearR: 0.6 });
  const Fhold = FX('wonder', { lidU: 1.0, mOpen: 0.1, mSmile: 0.3, pupil: 1.4, wet: 0.9, tearL: 0.5, tearR: 0.5 });
  const Fsmile = FX([['wonder', 0.4], ['shySmile', 0.6]], { mSmile: 0.45, lidU: 0.92, wet: 0.9, tearL: 0.45, tearR: 0.45, pupil: 1.3 });
  const Fdelight = FX('happy', { mSmile: 0.7, mOpen: 0.06, lidL: 0.5, lidU: 0.8, wet: 0.8, tearL: 0.4, tearR: 0.4, blush: 0.5 });
  const Fsafe = FX('trust', { lidU: 0.32, lidL: 0.42, mSmile: 0.38, browIn: 0.4, wet: 0.6, tearL: 0.35, tearR: 0.35 });
  let face = k(t, [[L.S, Fdown], [c.galRise + 0.1, Fdown], [c.galRise + 0.6, Fwide, 'inOut'], [L.B3 + 0.2, Fwide], [L.B3 + 1.3, Fawe, 'inOut'],
    [L.B3 + 1.75, Fawe], [L.B3 + 1.95, Flaugh, 'out'], [L.B3 + 2.3, Fawe, 'inOut'], [L.B4 - 0.05, Fawe], [L.B4 + 0.2, Fask, 'inOut'], [L.B5 + 1.3, Fask],
    [L.lean0 + 0.3, Fclosed, 'inOut'], [L.lean0 + 1.2, Fclosed], [L.B6 + 0.6, Fhold, 'inOut'], [L.B8 - 0.2, Fhold], [L.B8 + 0.3, Fsmile, 'inOut'],
    [L.B8 + 1.3, Fsmile], [L.B8 + 1.6, Fdelight, 'inOut'], [L.B12 - 0.3, Fdelight], [L.B12 + 0.8, Fsmile, 'inOut'], [L.E - 1.6, Fsmile], [L.E - 0.2, Fsafe, 'inOut']]);
  face = { ...face, autoBlink: 0 };
  // the breathless little laugh (b03)
  const laugh = pulse(t, L.B3 + 1.75, L.B3 + 2.35, 0.08, 0.3);
  // leans its cheek against the big hand on its RIGHT shoulder (head rolls toward it), body leans into the Void's hem
  const lean = k(t, [[L.lean0, 0], [L.lean0 + 0.6, 1, 'inOut'], [L.B6 + 0.5, 1], [L.B6 + 1.2, 0.25, 'inOut'], [L.B8 + 0.2, 0.25], [L.B8 + 0.8, 0.5, 'inOut']]);
  const reachG = k(t, [[L.B6 + 1.4, 0], [L.B6 + 2.4, 1, 'inOut']]);
  const holdG = k(t, [[L.B6 + 3.4, 0], [L.B7 - 0.1, 1, 'inOut']]);
  const raiseG = k(t, [[L.B12 + 0.2, 0], [L.B12 + 1.4, 1, 'inOut']]);
  const lgp = lg.pos;
  const hold = add(lgp, [0, -0.045, 0]);
  let armL = { preset: 'clasp', mix: 0.7 };
  let armR = { preset: 'clasp', mix: 0.7 };
  if (reachG > 0 && holdG < 1) armL = { preset: 'reach', target: hold, reach: reachG * (1 - holdG), hand: { spread: 0.5, curl: 0.12, thumb: 0.6 } };
  if (holdG > 0) {
    armL = { preset: 'hold', target: add(hold, rotY([0.035, 0, 0], yaw)), reach: holdG, palm: [0, 1, 0], hand: { curl: 0.35, cup: 0.7, spread: 0.1, thumb: 0.5 } };
    armR = { preset: 'hold', target: add(hold, rotY([-0.035, 0, 0], yaw)), reach: holdG, palm: [0, 1, 0], hand: { curl: 0.35, cup: 0.7, spread: 0.1, thumb: 0.5 } };
  }
  const look = k(t, [[L.S, 0.5], [L.B3, 0.42], [L.B4, 0.42], [L.B5, 0.5, 'inOut']]);
  const nodDown = k(t, [[L.B8 + 1.0, 0], [L.B8 + 1.4, 0.35, 'inOut'], [L.B9 - 0.3, 0.35], [L.B9 + 0.2, 0, 'inOut']]);
  return {
    pos: M.FOUT, yaw,
    body: { lean: -0.05 + 0.05 * lean, tilt: -0.08 * lean, idle: 0.6, breathe: 0.9 + 0.3 * laugh, bounce: 0.01 * laugh * Math.abs(Math.sin((t - L.B3) * 22)), stretch: 0.01 * laugh },
    head: { look: gaze, track: look, roll: -0.2 * lean - 0.08 * pulse(t, L.B4 + 0.2, L.B5, 0.3, 0.4), pitch: nodDown },
    gaze,
    face,
    blinkAt: [c.galRise + 0.5, L.B3 + 0.6, L.B6 + 1.3, L.B7 + 0.9, L.B8 + 1.65, L.B9 + 1.2, L.B11 + 0.4],
    armL, armR,
    extra: { glow: 1.35, cry: k(t, [[L.B3 + 0.6, 0], [L.B3 + 1.5, 0.42, 'inOut'], [L.B5 + 1.0, 0.42], [L.B6 + 2, 0.15, 'inOut']]), tremble: 0.1 * (1 - smooth(clamp((t - L.B3) / 2))),
      tuftWobble: 1.3, tuftPerk: 0.2 * pulse(t, c.galRise, L.B4, 0.4, 0.6) },
  };
}

// the little galaxy that becomes Fear's: one of the four that split off; drifts near Fear, Fear reaches for it (b06),
// it settles into Fear's cupped palms (b07); Fear holds it up to the light at the end (b12)
function littleGalaxy(t, L, M, fear) {
  const c = times();
  const yaw = fearYaw(t, L, c, M);
  const fwd = rotY([0, 0, 1], yaw);
  const chest = add(M.FOUT, [fwd[0] * 0.2, 0.42, fwd[2] * 0.2]);
  const held = add(M.FOUT, [fwd[0] * 0.17, 0.5, fwd[2] * 0.17]);
  const raised = add(M.FOUT, [fwd[0] * 0.22, 0.66, fwd[2] * 0.22]);
  const drift = add(M.FOUT, add(rotY([0.25, 0, 0.3], 2.0), [0, 1.05 + 0.08 * Math.sin(t * 0.9), 0]));
  const p = k(t, [[c.galaxies + 0.2, add(M.FOUT, [0.5, 1.2, -0.3])], [L.B3, drift, 'inOut'], [L.B6 + 1.2, drift], [L.B6 + 2.6, add(chest, [0, 0.25, 0]), 'inOut'], [L.B7 - 0.1, held, 'inOut'],
    [L.B12 + 0.2, held], [L.B12 + 1.4, raised, 'inOut']]);
  return { pos: p, size: k(t, [[c.galaxies, 0.14], [L.B6, 0.12], [L.B7, 0.1]]) };
}

// one last star drifts down onto Fear's scarf in the b08 pause, and stays there twinkling
function lastStar(t, L, fear) {
  const t0 = L.B8 + 0.2, t1 = L.B8 + 1.35;
  if (t < t0) return null;
  const sc = fear.anchor('scarf');
  if (!sc) return null;
  const knot = add(A(sc), [0.0, 0.035, 0.03]);
  const u = clamp((t - t0) / (t1 - t0));
  const e = ease.out(u);
  const p = add(knot, [0.12 * Math.sin(u * 5) * (1 - e), 0.9 * (1 - e), 0.06 * (1 - e)]);
  return { pos: p, a: smooth(clamp((t - t0) / 0.3)) * (0.85 + 0.15 * Math.sin(t * 4)), s: 1 };
}

// the galaxy rising from the palms, splitting into more on "galaxies", then small galaxies turning around the pair
function drawGalaxies(ps, t, L, c, palms, lg, vs) {
  const g0 = c.galRise - 0.15;
  if (t < g0) {
    // the glow in the palms carried over from s21b06
    ps.add(add(palms, [0, 0.06, 0]), 0.3, 0xffe9c0, 0.55, 0, CELL.dot);
    ps.add(add(palms, [0, 0.06, 0]), 0.6, 0xb79cff, 0.22, 0, CELL.dot);
    return;
  }
  const u = smooth(clamp((t - g0) / (c.galaxies - g0)));
  const split = smooth(clamp((t - c.galaxies) / 0.9));
  const core = add(palms, [0, 0.08 + 0.42 * u, 0]);
  const spin = t * 0.9;
  if (split < 1) {
    const a = 1 - split;
    ps.add(core, (0.16 + 0.26 * u) * (1 - 0.4 * split), 0xe8d6ff, 0.95 * a, spin, CELL.galaxy);
    ps.add(core, 0.5 + 0.2 * u, 0xb498ff, 0.25 * a, 0, CELL.dot);
    ps.add(add(palms, [0, 0.05, 0]), 0.3, 0xffe9c0, 0.4 * (1 - u), 0, CELL.dot);
  }
  if (split > 0) {
    // four drift up and away, slowly orbiting the pair; the fifth is Fear's little galaxy
    const centre = add(mix3(vs.pos, add(palms, [0, 0, 0]), 0.6), [0, 0, 0]);
    const cols = [0xd8c4ff, 0xa8e8ff, 0xffc4e4, 0xfff0c8];
    for (let i = 0; i < 4; i++) {
      const ang = i * 1.7 + 0.4 + 0.08 * (t - c.galaxies);
      const r = lerp(0.05, 1.5 + 0.35 * i, ease.out(split));
      const h = lerp(core[1], 1.9 + 0.35 * i + 0.1 * Math.sin(t * 0.6 + i), ease.out(split));
      const p = [centre[0] + r * Math.cos(ang), h, centre[2] + r * Math.sin(ang)];
      const fade = 1 - smooth(clamp((t - (L.B3 + 3.0 + i * 0.6)) / 2.5)) * 0.45;
      ps.add(p, (0.2 + 0.05 * i) * lerp(0.6, 1, split), cols[i], 0.85 * fade, spin * (0.6 + 0.15 * i) + i, CELL.galaxy);
    }
    // Fear's little galaxy
    const a = Math.max(split, 0);
    ps.add(lg.pos, lg.size * 1.4, 0xf2e0ff, 0.95 * a, -t * 1.1, CELL.galaxy);
    ps.add(lg.pos, lg.size * 3.2, 0xc4a8ff, 0.22 * a, 0, CELL.dot);
  }
}

// ======================================================================================================== cameras
function frameShot(st, t, shot, L, c, M, vs) {
  const { vd, fear, mag } = st;
  const ve = A(vd.anchor('eyes')), fe = A(fear.anchor('eyes'));
  const mid = (a, b, u = 0.5) => mix3(a, b, u);
  const wideOf = (dist, y0 = 614) => { const w = ROOM.shot([1.3, 1.3, 0.35], { dist, yaw: -45, pitch: 6, fov: 54, screenY: y0 / 1280 }); return w; };
  switch (shot) {
    case 0: { // close two-shot from low beside the Void's open hands, Fear's face just beyond -> on "galaxies" pull back to the wide
      const u = k(t, [[c.galaxies - 0.15, 0], [L.B3, 1, 'inOut']]);
      const wide = wideOf(6.5);
      const pos = mix3(ROOM.W(0.55, 0.9, 3.25), wide.pos, u);
      const subj = mix3(mix3(fe, bookPoint(vs), 0.4), ROOM.W(1.3, 1.3, 0.35), u);
      return aim(pos, subj, lerp(330, 360, u), lerp(610, 614, u), lerp(46, 54, u), { drift: 0.1 });
    }
    case 1: { // FEAR_CU from the Void side (face ~y 470, nebula light): tears of awe, the question
      const push = smooth(clamp((t - L.B3) / (L.B4e - L.B3)));
      return ROOM.shot(ROOM.L(fe), { dist: 1.5 - 0.12 * push, yaw: 15, pitch: 10, fov: 40, screenY: sy(470), drift: 0.06 });
    }
    case 2: { // close on the Void -> widen to the two-shot (hand on the shoulder) -> pull back until the corner shows (b06)
      const closeV = ROOM.shot(ROOM.L(ve), { dist: 3.8, yaw: -28, pitch: -6, fov: 36, screenY: sy(330), drift: 0.08 });
      const two = aim(ROOM.W(0.3, 1.5, 4.7), mid(ve, fe), 330, 490, 44, { drift: 0.1 });
      const far = aim(ROOM.W(-0.6, 2.0, 8.2), ve, 228, 340, 52, { drift: 0.1 });
      const u1 = k(t, [[L.B5 + 0.6, 0], [L.B5 + 1.8, 1, 'inOut']]);
      const u2 = k(t, [[L.B6 + 0.4, 0], [T('s22b06.end') + 0.2, 1, 'inOut']]);
      return blendShot(blendShot(closeV, two, u1), far, u2);
    }
    case 3: // VOID_LOW from beside Fear (its tuft and the little galaxy in its palms at the lower edge)
      return aim(ROOM.W(-1.15, 0.62, 2.55), ve, 380, 330, 46, { drift: 0.06 });
    case 4: { // two-shot, a slow 3-4 degree orbit through the long pause
      const o = k(t, [[L.B8, -0.2], [L.B9, 0.15]]);
      return aim(ROOM.W(0.3 + o, 1.5, 4.6 - 0.1 * o), mid(ve, fe), 330, 500, 44, { drift: 0.05 });
    }
    case 5: case 7: { // the corner: the bucket on the magician's head
      const ht = A(mag.anchor('headTop') || add(M.CRASH, [0, 1, 0]));
      return ROOM.shot(ROOM.L(ht), { dist: 2.1, yaw: -8, pitch: 6, fov: 36, screenY: sy(460), drift: 0 });
    }
    case 6: case 8: // the Void close, head perfectly still; Fear's tuft at the lower edge
      return ROOM.shot(ROOM.L(ve), { dist: 4.1, yaw: -24, pitch: -9, fov: 36, screenY: sy(340), drift: 0 });
    case 9: // straight down its hood axis: it looks into the lens; wink; "Tee-hee."
      return ROOM.shot(ROOM.L(ve), { dist: 4.0, yaw: -58, pitch: -3, fov: 34, screenY: sy(370), drift: 0.04 });
    case 10: { // pull back to the cosmos wide for the end title (the title band y 150-310 stays calm nebula)
      const u = k(t, [[L.cutJ, 0], [L.B12 + 1.6, 0.7, 'inOut'], [L.E, 1, 'out']]);
      const start = ROOM.shot(ROOM.L(ve), { dist: 4.0, yaw: -58, pitch: -3, fov: 34, screenY: sy(370), drift: 0.04 });
      const end = ROOM.shot([1.3, 1.1, 0.35], { dist: 9.0, yaw: -45, pitch: 4, fov: 54, screenY: sy(560), drift: 0.12 });
      return blendShot(start, end, u);
    }
  }
  return wideOf(6.5);
}
