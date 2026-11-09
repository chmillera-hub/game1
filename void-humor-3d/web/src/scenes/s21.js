// s21 whats_that_noise — Fear hears it. The Void plays innocent with the world's most suspicious shrug (and a sideways
// shuffle that happens to fill Fear's view of the corner), a lone bucket rolls by behind it, and Fear, small and
// trusting, lets it go. Then the Void opens its hands like a book; a glow begins in its palms.
//
// Shots:
//   A  scene start -> s21b03     FEAR_CU from the Void side (the fingertip star at the top edge): the last broom
//                                clatters off-screen -> a second, smaller twitch; "What's... what's that noise?" on tiptoe,
//                                leaning to peek round the Void's bulk, eyes darting, a gulp between the two "what's"
//   B  s21b03 -> s21b04          medium two-shot: the SHRUG on "shrugs" (shoulders to the hood, palms up, eyes to the
//                                ceiling, tiny pressed line) + the shuffle that blocks Fear's peek; the star floats off
//   C  s21b04 -> s21b05          MASTER wide: "hm?" head tilt, blameless blink; a bucket rolls slowly across the back
//   D  s21b05 -> b05.end+0.2     FEAR_CU: two blinks, a last glance at the corner, back up at the Void, a tiny nod
//   E  -> end                    the two-shot: both big hands come together in front of Fear and open like a book
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { ROOM, sy, lookFor } from './marks.js';
import { ensureBonusDecals } from './kit_bonus.js';
import { loadLines, W, A, add, sub, mix3, LD, pulse, jiggle, stamp, own, solve, aim, pix, marks, times, voidSpot, starAt, heldStar, drawStar, wreckPose, cornerOpts, bookPoint, bookArms, fearCU, FEAR_TURN } from './kit_s20_22.js';

const ID = 's21';
// in b05 Fear turns from the star (camera side) toward the Void and keeps that facing into s22 (kit FEAR_TURN)
globalThis.DBG21 = 1; // TEMP

export default {
  id: ID,
  async setup(app) {
    await loadLines();
    const set = await app.set('BACKROOM');
    ROOM.fit(set);
    ensureBonusDecals(set);   // the magician's grey footprints + dust patch stay until the cosmos takes the floor
    const [vd, fear, mag] = await Promise.all([app.char('VOID'), app.char('FEAR'), app.char('MAGICIAN')]);
    const fx = new Particles({ max: 80, intensity: 1.5 });
    own(ID, fx.mesh);
    return { scene: set.scene, set, vd, fear, mag, fx, look: lookFor(ID, set.look) };
  },

  async update(t, app, st) {
    stamp(ID, t);
    const { set, vd, fear, mag, fx } = st;
    for (const o of [vd.root, fear.root, mag.root, fx.mesh]) st.scene.add(o);
    const c = times(), M = marks();
    const L = {
      B1: T('s21b01'), B2: T('s21b02'), B3: T('s21b03'), B4: T('s21b04'), B5: T('s21b05'), B6: T('s21b06'),
      what2: W('s21b02', "what's", { occ: 1 }), that: W('s21b02', 'that'), noise: W('s21b02', 'noise'),
      oh: W('s21b05', 'oh'), okay: W('s21b05', 'okay'), okayEnd: W('s21b05', 'okay', { end: true }),
    };
    L.gulp = (W('s21b02', "what's", { end: true }) + L.what2) / 2;
    L.cutE = T('s21b05.end') + 0.2;
    const shot = t < L.B3 ? 0 : t < L.B4 ? 1 : t < L.B5 ? 2 : t < L.cutE ? 3 : 4;
    const shotStart = [ID, 's21b03', 's21b04', 's21b05', L.cutE][shot];

    // ------------------------------------------------------------------ VOID
    const vs = voidSpot(t);
    const shrug = k(t, [[c.shrug - 0.3, 0], [c.shrug - 0.18, -0.08, 'inOut'], [c.shrug + 0.22, 1.06, 'out'], [c.shrug + 0.4, 1.0, 'inOut'],
      [L.B4 + 0.9, 0.95], [L.B5 + 0.6, 0.25, 'inOut'], [L.B6, 0.05, 'inOut']]);
    const bookU = k(t, [[L.B6 - 0.35, 0], [L.B6 + 0.35, 1, 'inOut']]);       // hands come together
    const openU = k(t, [[L.B6 + 0.3, 0], [L.B6 + 1.05, 1, 'inOut']]);        // ... and open like a book
    const vPose = (pass) => {
      const fe = pass ? fear.anchor('eyes') : null;
      const s = starAt(t);
      const fw = add(M.FOUT, [0, 0.62, 0]);
      const towardF = sub(fw, s.pos); const hz = Math.hypot(towardF[0], towardF[2]) || 1;
      const Fserene = VX('gentle', { lidU: 0.74, lidL: 0.5, mSmile: 0.56, browIn: 0.36, blush: 0.2 });
      // the suspicious innocent: eyes rolled up-and-aside to the ceiling, brows up, a tiny pressed line
      const Finno = VX('innocent', { lidU: 1.12, lidL: 0.08, mSmile: 0.16, mPress: 0.7, mWide: -0.35, mRound: 0, browIn: 0.75, browOut: 0.7, gazePitch: 0.55, gazeYaw: 0.45, saccade: 0 });
      const Fhm = VX('innocent', { lidU: 1.08, mSmile: 0.2, mPress: 0.55, mWide: -0.3, browIn: 0.7, browOut: 0.75, browAsym: 0.3, gazePitch: 0.45, gazeYaw: 0.3, saccade: 0 });
      const Fwarm = VX('gentle', { lidU: 0.8, lidL: 0.5, mSmile: 0.62, browIn: 0.38, blush: 0.25 });
      const face = k(t, [[ID, Fserene], [c.shrug - 0.25, Fserene], [c.shrug + 0.05, Finno, 'out'], [L.B4 + 0.1, Finno], [L.B4 + 0.35, Fhm, 'inOut'],
        [L.B5 + 0.3, Fhm], [L.B5 + 1.0, Fwarm, 'inOut']]);
      face.autoBlink = 0;
      const gazeOn = (t < c.shrug - 0.05 || t > L.B5 + 0.6);
      // arms: the LEFT fingertip holds the star (from s20) until the shrug releases it; the right rests on the belly;
      // both open into the shrug (palms up), settle, then come together in front of Fear and open like a book
      const reach = 1 - smooth(clamp((t - (c.shrug - 0.25)) / 0.35));
      const fing = [0.08 * towardF[0] / hz, 1, 0.08 * towardF[2] / hz + 0.18];
      const sh = clamp(shrug);
      let armL, armR;
      if (bookU > 0.001) {
        const bk = bookArms(vs, bookU, openU, 'rest', 'belly', st.camDir);
        armL = bk.armL; armR = bk.armR;
      } else if (reach >= 1) {
        armL = { preset: 'point', target: s.pos, tip: true, reach: 1, fingers: fing, palm: [towardF[0] / hz, 0.05, towardF[2] / hz], pole: [0.2, -1, -0.3], hand: { point: 1, curl: 1, thumb: 0, cup: 0.2 } };
        armR = { preset: 'belly', from: 'rest', mix: 1 };
      } else {
        armL = { preset: 'shrug', from: 'rest', mix: sh * (1 - reach), target: s.pos, reach: reach * reach, hand: { point: reach, curl: 0.2 + 0.8 * reach, thumb: 0.6 * (1 - reach) } };
        armR = { preset: 'shrug', from: 'belly', mix: sh };
      }
      // the shuffle: three little waddle steps under the hem
      const shuffle = pulse(t, c.shrug - 0.2, c.shrug + 0.6, 0.12, 0.15);
      const hmTilt = pulse(t, L.B4 + 0.05, L.B5 + 0.2, 0.3, 0.4);
      return {
        pos: vs.pos, yaw: vs.yaw,
        walk: { amount: shuffle * 0.8, phase: (t - (c.shrug - 0.2)) * 2.6, style: 'waddle' },
        body: { lean: 0.12 - 0.1 * clamp(shrug) + 0.12 * bookU, shrug: clamp(shrug), breathe: 0.8, tilt: 0.03 * hmTilt },
        head: { pitch: 0.25 - 0.18 * clamp(shrug), yaw: shot === 1 || shot === 4 ? 0.2 : 0.1, roll: 0.03 + 0.2 * hmTilt },
        gaze: pass && gazeOn ? fe : null,
        face,
        blinkAt: [c.shrug + 0.85, L.B4 + 0.5, L.okay + 0.15, L.B6 + 0.2],
        armR, armL,
        // FEAR_CU: the near hem is right beside Fear: a darker, soft velvet edge (less fresnel rim), not a lavender glare
        extra: { stars: 1.4 + 0.3 * smooth(clamp((t - L.B6) / 0.8)), motes: 0.8, rim: shot === 0 || shot === 3 ? 0.35 : 1 },
      };
    };

    // ------------------------------------------------------------------ FEAR
    const fearPose = (tt) => {
      const s = starAt(tt);
      const vEyes = vd.anchor('eyes');
      // looking "up at the Void" from 0.6 m tall: aim at its chest/collar (the head tips back, the eyes do little) so the
      // irises stay in the open eye instead of rolling up under the lids
      const vc = vd.anchor('chest');
      const ve = vc ? add(A(vc), [0, 0.22, 0]) : add(vs.pos, [0, 1.4, 0]);
      const okU = smooth(clamp((tt - (L.B4 + 0.4)) / 0.6));
      const corner = add(M.CRASH, [0, 0.5, 0]);
      const peekP = ROOM.W(2.75, 0.8, 0.62);   // round the Void's camera-side flank, toward the corner: screen-right in FEAR_CU
      // twitch 2 (smaller) at the broom clatter
      const tw = c.broom1 + 0.07;
      const startle = k(tt, [[tw, 0], [tw + 0.06, 0.55, 'out'], [tw + 0.55, 0, 'inOut']]);
      const peek = k(tt, [[L.B2 + 0.25, 0], [L.B2 + 0.85, 1, 'inOut'], [c.shrug + 0.1, 1], [c.shrug + 0.55, 0.35, 'inOut'], [L.B4 + 0.6, 0, 'inOut']]);
      const blocked = smooth(clamp((tt - (c.shrug + 0.1)) / 0.5));
      // eyes: the star -> dart toward the noise -> peek past the flank -> up at the Void (blocked) -> up at it -> corner glance -> Void -> palms
      const palms = bookPoint(vs);
      const g = k(tt, [[ID, s.pos], [tw + 0.04, s.pos], [tw + 0.12, mix3(s.pos, corner, 0.5), 'out'], [tw + 0.5, mix3(s.pos, corner, 0.5)],
        [L.B2 + 0.2, mix3(s.pos, corner, 0.35), 'inOut'], [L.B2 + 0.8, peekP, 'inOut'], [L.gulp, peekP], [L.gulp + 0.1, mix3(peekP, ve, 0.4), 'out'], [L.what2, peekP, 'out'],
        [c.shrug + 0.2, peekP], [c.shrug + 0.45, ve, 'inOut'], [L.B4 + 0.7, ve], [L.B4 + 0.85, corner, 'out'], [L.B5 - 0.05, corner], [L.B5 + 0.05, ve, 'out'],
        [L.okay - 0.45, ve], [L.okay - 0.35, corner, 'out'], [L.okay - 0.05, corner], [L.okay + 0.05, ve, 'out'], [L.B6 + 0.1, ve], [L.B6 + 0.45, palms, 'inOut']]);
      const Fstar = FX([['wonder', 0.55], ['shySmile', 0.45]], { mOpen: 0.08, mSmile: 0.3, mAsym: 0.2, pupil: 1.3, lidU: 1.0 });
      const Flisten = FX('listen', { lidU: 1.2 });
      const Fgulp = FX('gulp');
      const Fpeek = FX('listen', { lidU: 1.28, browIn: 0.9, mOpen: 0.06 });
      const Fup = FX('curious', { lidU: 1.2, browIn: 0.6, mRound: 0.3, mOpen: 0.06 });
      const Funsure = FX([['worried', 0.5], ['curious', 0.5]], { lidU: 1.18, lidSad: 0.15 });
      const Fokay = FX([['trust', 0.6], ['relieved', 0.4]], { mSmile: 0.2, lidU: 1.2, lidSad: 0.1, browIn: 0.7 });
      const Fdown = FX('wonder', { lidU: 1.0, mOpen: 0.12, pupil: 1.35, mSmile: 0.15 });
      let face = k(tt, [[ID, Fstar], [tw, Fstar], [tw + 0.06, FX('startle'), 'out'], [tw + 0.6, Flisten, 'inOut'], [L.gulp - 0.12, Flisten],
        [L.gulp, Fgulp, 'out'], [L.what2 - 0.04, Fgulp], [L.what2 + 0.12, Fpeek, 'out'], [c.shrug + 0.3, Fpeek], [c.shrug + 0.7, Fup, 'inOut'],
        [L.B4 + 0.6, Funsure, 'inOut'], [L.B5 + 0.1, Funsure], [L.okay + 0.1, Fokay, 'inOut'], [L.B6 + 0.2, Fokay], [L.B6 + 0.7, Fdown, 'inOut']]);
      face = { ...face, autoBlink: 0, talk: 0.9 };
      const nod = 0.13 * pulse(tt, L.okay + 0.05, L.okay + 0.6, 0.15, 0.3);
      return {
        pos: M.FOUT, yaw: M.yFOUT + FEAR_TURN * smooth(clamp((tt - (L.B5 + 0.05)) / 0.7)),   // turns toward the Void ("Oh... okay")
        body: { tiptoe: 1.0 * peek, tilt: 0.17 * peek * (1 - 0.6 * blocked), lean: 0.1 * peek, twist: 0.12 * peek, idle: 0.7, breathe: 0.9, recoil: 0.06 * startle },
        head: { look: g, track: lerp(0.55, 0.92, okU), yaw: -0.14 * (1 - peek), roll: -0.05 + 0.08 * peek, pitch: nod, up: 0.018 * peek, forward: 0.022 * peek },
        gaze: g,
        face,
        blinkAt: [tw + 0.02, c.shrug + 0.55, L.oh + 0.12, L.oh + 0.42, L.okay + 0.6],
        armL: { preset: 'clasp', mix: 1 - 0.6 * peek }, armR: { preset: 'clasp', mix: 1 - 0.6 * peek },
        extra: { tuftPerk: Math.max(0.8 * peek, startle, 0.3 * (1 - smooth(clamp((tt - L.okay) / 0.8)))), startle, glow: 1.1, tremble: 0.12 * (1 - smooth(clamp((tt - L.okay) / 1.0))) },
      };
    };
    const fPose = (pass) => (pass ? (tt) => fearPose(Math.max(tt, T(shotStart))) : fearPose(t));

    // ------------------------------------------------------------------ MAGICIAN (in the wreck, far back-right)
    const mPose = () => wreckPose(t, M);

    { const sh = frameShot(st, t, 4, L, c, M); st.camDir = sub(sh.pos, bookPoint(vs)); }
    solve(t, [[vd, vPose], [mag, mPose], [fear, fPose]], () => {
      applyShot(app.camera, frameShot(st, t, shot, L, c, M), t, 21);
    });
    // FEAR_CU: the Void's violet face light dimmed so its near hem reads as soft dark velvet, not a lavender glare
    set.update(t, { ...cornerOpts(t, mag), voidLight: { pos: add(vs.pos, [-0.71, 2.0, 0.21 + 0.5]), intensity: shot === 0 || shot === 3 ? 1.3 : 3.2 } });

    fx.begin();
    drawStar(fx, t, heldStar(vd, starAt(t)), CELL, shot === 0 || shot === 3 ? 1.2 : 1);
    // b06: a glow begins on its open palms (a soft core + a few slow sparks), carried straight into s22
    const bk = bookArms(vs, 1, openU);
    const palms = bk.palms;
    const glow = smooth(clamp((t - (L.B6 + 0.3)) / 0.35));
    if (glow > 0) {
      // a warm light ON each open palm (the anchors are the palm-surface centres) + a soft pool between them
      for (const h of [vd.anchor('handL'), vd.anchor('handR')]) if (h) {
        const p = add(A(h), [0, 0.03, 0]);
        fx.add(p, 0.2 * glow, 0xfff0d0, 0.85 * glow, 0, CELL.dot);
        fx.add(p, 0.08, 0xffffff, 0.9 * glow, 0, CELL.dot);
      }
      fx.add(palms, 0.22 + 0.06 * glow, 0xfff0d0, 0.55 * glow, 0, CELL.dot);
      fx.add(palms, 0.6, 0xb79cff, 0.3 * glow, 0, CELL.dot);
      fx.stream({ t, seed: 2101, t0: L.B6 + 0.5, t1: L.B6 + 3, rate: 5, life: 1.4, origin: palms, vel: [0, 0.16, 0], spread: [0.06, 0.04, 0.06], size: [0.025, 0.045],
        color: [0xfff1d0, 0xd9c8ff, 0xa9f0ff], alpha: 0.85 * glow, fade: [0.2, 0.5], cell: CELL.star, spin: 1 });
    }
    fx.end();

    if (globalThis.DBG21) {
      const cam = app.camera;
      const bb = new THREE.Vector3(); set.props.bucketB.getWorldPosition(bb);
      const cands = {}; for (const [x, z] of [[3.98, -4.18], [3.0, -3.8], [3.3, -2.8], [3.4, -1.8], [3.2, -1.0], [2.6, -1.6], [2.2, -2.6], [1.99, -4.07]]) cands[x + ',' + z] = pix(cam, [x, 0.15, z]);
      console.log('DBG21', t.toFixed(2), 'shot', shot, JSON.stringify({ cands, bucket: pix(cam, bb), bw: [bb.x.toFixed(2), bb.z.toFixed(2)], v: pix(cam, vd.anchor('eyes')), f: pix(cam, fear.anchor('eyes')), star: pix(cam, starAt(t).pos), m: pix(cam, mag.anchor('head')) }));
    }
    st.look = lookFor(ID, set.look);
  },
};

function rotY(v, yaw) { const c = Math.cos(yaw), s = Math.sin(yaw); return [v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c]; }

function frameShot(st, t, shot, L, c, M) {
  const { fear } = st;
  const fe = A(fear.anchor('eyes'));
  if (shot === 0) return fearCU(fe, smooth(clamp((t - L.B2) / (L.B3 - L.B2))));
  if (shot === 3) {   // "Oh... okay": from the Void side, a touch above Fear's eye line, so its upturned, trusting eyes read
    const push = smooth(clamp((t - L.B5) / 2.0));
    return ROOM.shot(ROOM.L(fe), { dist: 2.4 - 0.12 * push, yaw: 40, pitch: 8, fov: 40, screenY: sy(600), drift: 0.05 });
  }
  if (shot === 1 || shot === 4) {
    // locked on the PRE-shuffle spot, a little wider: the sideways shuffle and the palms-up shrug both read
    const vs = voidSpot(c.shrug - 0.3);
    return ROOM.shot(add(ROOM.L(vs.pos), [-0.67, 1.45, 0.35]), { dist: 5.6, yaw: -40, pitch: 6, fov: 50, screenY: sy(520), drift: 0.08 });
  }
  // MASTER shifted ~1.4 m camera-right (and a touch back) so the wrecked corner shows back-right of the Void and the
  // rolling bucket has open, bulb-lit floor to roll across
  const m = ROOM.cam('MASTER', { drift: 0.1 });
  return { ...m, pos: add(m.pos, LD(1.8, 0, 0.75)), look: add(m.look, LD(1.42, 0, 0)), fov: 44 };
}
