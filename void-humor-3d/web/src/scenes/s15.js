// s15 fair_enough — no hard feelings. Jesus gets up off his knee (half up, a bend and two swipes at the dusty right
// knee, then upright), turns — eyes first — and has to tip his head way back: the Void is RIGHT THERE (it got up and
// shuffled over while he wasn't looking), hands clasped at its middle, soft lids, brow-wisps up in the middle; one
// slow blink. Seen from its eyeline (over its shoulder, his face full in the lens): a big honest shrug ("eh: you win
// some"), a rueful smile up at it. Side two-shot: the Void reaches DOWN (elbow up and out, clear of his face) and
// pats the top of his right shoulder, pat, pat, its fingers over his back; he rocks with each pat. Close on it: the
// sad little smile (small, closed, pressed, a wobble; the eyes don't follow) — its eyes slide to the rise where the
// user vanished, and back; a slow blink: it has done this before. A long sigh, a lilac wisp leaving the hood, and
// (two-shot) Jesus lays his hand over the big one. Its eyeline again: "Too intense. Apparently." — deadpan, until the
// mouth corner gives him away. Its eyes widen; a surprised snort, one little star pops out of the hood, eyes crinkle
// into arcs, a big hand over its mouth.
// Staging (STAGING s15): K <-> V15 line, Jesus screen-left / Void screen-right in the side two-shots. Faces that must
// read (the look-up, the shrug, the deadpan + corner) play in JUP: over the Void's LEFT shoulder (camera side), down
// at his face; the Void's face in VCU over his head.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { EDGE, todAt, voidSkyAt, sy, lookFor, frame } from './marks.js';
import { loadLines, W, POS, SW, SV, add, arr, own, stamp, drawSkyGalaxy, solve, pulse, V3, toV, ramp, bump, aimXY } from './kit_s14_16.js';

const M = EDGE.M;
const KP = M.K.p, KY = M.K.yaw, VP = M.V15.p;
export const S15 = {
  JY1: 1.92,                                   // Jesus faces the Void, cheated ~28 deg open to the camera side
  VY: M.V15.yaw + 0.2,                         // the Void, cheated ~11 deg open (its eyes on him)
};
const JY1 = S15.JY1, VY = S15.VY;
/** the Void's LEFT hand (camera side) on the top of Jesus's RIGHT shoulder (s15 pat -> s16 lift-off): palm down,
 *  fingers over the back of his shoulder, the elbow UP and out to his right so the arm comes DOWN onto him from above
 *  — never across his face (side two-shot) nor between the lens and his face (over its shoulder). */
export function patHand(jesus, jYaw, lift = 0) {
  const shR = jesus.anchor('shoulderR');
  if (!shR) return null;
  const jf = [Math.sin(jYaw), 0, Math.cos(jYaw)], jr = [-Math.cos(jYaw), 0, Math.sin(jYaw)];
  return {
    target: add(arr(shR), [-jf[0] * 0.04 + jr[0] * 0.03, 0.02 + 0.12 * lift, -jf[2] * 0.04 + jr[2] * 0.03]),
    palm: V3(-jr[0] * 0.12 + jf[0] * 0.08, -1, -jr[2] * 0.12 + jf[2] * 0.08).normalize().toArray(),
    fingers: V3(-jf[0] * 0.75 + jr[0] * 0.25, -0.6, -jf[2] * 0.75 + jr[2] * 0.25).normalize().toArray(),
    pole: V3(jr[0] * 0.8 + jf[0] * 0.3, -0.45, jr[2] * 0.8 + jf[2] * 0.3).normalize().toArray(),
  };
}
/** the Void's feet: it takes one small shuffle toward him as it reaches down to pat (s16 starts from here) */
export function voidPos15(t) {
  const v = EDGE.W(M.V15.p), j = EDGE.W(M.K.p), d = Math.hypot(j[0] - v[0], j[2] - v[2]);
  const u = 0.4 * ramp(t, W('s15b03', 'pats', { alt: ['patts', 'pat'], frac: 0.25 }) - 0.95, W('s15b03', 'pats', { alt: ['patts', 'pat'], frac: 0.25 }) - 0.25);
  return [v[0] + (j[0] - v[0]) / d * u, 0, v[2] + (j[2] - v[2]) / d * u];
}

export default {
  id: 's15',
  async setup(app) {
    await loadLines();
    const set = await app.set('EDGE');
    const [jesus, vd, user] = await Promise.all([app.char('JESUS'), app.char('VOID'), app.char('USER')]);
    const fx = new Particles({ max: 32, intensity: 1.5 });
    own(fx.mesh, 's15');
    const wisp = new Particles({ max: 8, blending: 'add', intensity: 1.0 });
    own(wisp.mesh, 's15');
    return { scene: set.scene, set, jesus, vd, user, fx, wisp, look: lookFor('s15', set.look) };
  },

  async update(t, app, st) {
    stamp(t, 's15');
    const { set, jesus, vd, user, fx, wisp } = st;
    for (const o of [jesus.root, vd.root, fx.mesh, wisp.mesh]) st.scene.add(o);
    st.scene.remove(user.root);                                     // the user is gone over the rise
    jesus.root.visible = vd.root.visible = true;

    // ================================================================ timing
    const S = T('s15'), E = T('s15.end');
    const B3 = T('s15b03'), B4 = T('s15b04'), B5 = T('s15b05'), B5e = T('s15b05.end');
    const B6 = T('s15b06'), B7 = T('s15b07');
    const tLooks = W('s15b01', 'looks', { frac: 0.25 }), tBack = W('s15b01', 'back', { frac: 0.5 }), tVoid1 = W('s15b01', 'void', { alt: ['void.', 'void,'], frac: 0.8 });
    const tShrugs = W('s15b02', 'shrugs', { alt: ['shrugs.'], frac: 0.2 });
    const tPats = W('s15b03', 'pats', { alt: ['patts', 'pat'], frac: 0.25 });
    const tSad = W('s15b04', 'sad', { frac: 0.15 }), tSmile = W('s15b04', 'smile', { alt: ['smile.'], frac: 0.6 });
    const tAppEnd = W('s15b06', 'apparently', { alt: ['apparently.'], end: true, frac: 0.85 });
    // Jesus: half up -> brush the knee (two swipes) -> upright -> turn (eyes first) -> head way back
    const tUp0 = S + 0.12, tHalf = tUp0 + 0.55, tUp1 = Math.max(tHalf + 0.75, tBack - 0.05);
    const tBr1 = tHalf + 0.02, tBr2 = tBr1 + 0.27;
    const tTurn0 = Math.max(tUp1 - 0.15, tBack - 0.2), tTurn1 = tTurn0 + 0.6;
    const tFind = Math.max(tTurn1 - 0.08, tVoid1 - 0.1);                   // the head tips way back
    // shrug
    const tSh0 = tShrugs - 0.12, tSh1 = tSh0 + 0.22, tSh2 = tSh1 + 0.55, tSh3 = tSh2 + 0.3;
    // pats (contacts land on the pats)
    const tReach0 = tPats - 0.65, tReach1 = tPats - 0.04, patRate = 2.25;
    const tPatEnd = tReach1 + 2 / patRate - 0.02;
    // sad smile, the look to the rise, slow blink
    const tSS = tSad - 0.05, tSlide0 = tSmile + 0.05, tSlide1 = tSlide0 + 0.6;
    // sigh: shoulders up and settle, the wisp; hand over hand
    const tSigh = B5 + 0.05, tWisp = B5 + 0.12, tHand0 = B5 + 0.42, tHand1 = tHand0 + 0.5;
    // the corner, the widening, the snort
    const tCorner = tAppEnd + 0.04, tWiden = tAppEnd + 0.3;
    const tSnort = B7 + 0.04, tCover = tSnort + 0.08, tStar = tSnort + 0.1;

    // ================================================================ shots
    const cutJ = tTurn0 + 0.32, cutP = B3 - 0.25, cutV = B4 - 0.08, cutJ2 = B6 - 0.12, cutV2 = tWiden - 0.12;
    const SHOTS = [[S, 'RISE'], [cutJ, 'JUP'], [cutP, 'VPAT'], [cutV, 'VCU'], [cutJ2, 'JUP2'], [cutV2, 'VCU2']];
    let si = 0; for (let i = 0; i < SHOTS.length; i++) if (t >= SHOTS[i][0]) si = i;
    const shot = SHOTS[si][1], shotT0 = SHOTS[si][0], shotT1 = SHOTS[si + 1] ? SHOTS[si + 1][0] : E + 0.5;

    // ================================================================ JESUS
    const kneel = k(t, [['s15', 1], [tUp0, 1], [tHalf, 0.38, 'inOut'], [tBr2 + 0.18, 0.34], [tUp1, 0, 'inOut']]);
    const turn = ramp(t, tTurn0, tTurn1, (u) => { const s = smooth(u); return s + 0.05 * Math.sin(Math.PI * s) * (u > 0.6 ? 1 : 0); });
    const jYawL = lerp(KY, JY1, turn);
    const jYawW = EDGE.Y(jYawL);
    const jPos = EDGE.W(KP);
    const jPose = (pass) => {
      const ve = vd.anchor('eyes');
      const vE = ve ? arr(ve) : SW(VP[0], 2.0, VP[2]);
      const vh = vd.anchor('handL');
      // ---- face
      const Frue = JX('rueful', { mSmile: 0.42, mPress: 0.6, mAsym: 0.4, lidU: 0.7, lidL: 0.4, browIn: 0.45, browOut: 0.3 });
      const Fkind = JX('kind', { mSmile: 0.25, lidU: 0.95 });
      const Fcur = JX('curious', { lidU: 1.06, mSmile: 0.12 });
      const Foh = JX('surprised', { lidU: 1.3, browIn: 0.85, browOut: 0.95, mOpen: 0.2, mRound: 0.7, mSmile: 0.12, pupil: 1.15 });
      const Fwarm = JX('warm', { mSmile: 0.55, lidU: 0.95, browIn: 0.45 });
      const Fshrug = JX('shrug', { mSmile: -0.18, mPress: 0.65, mWide: 0.45, mAsym: 0.2, browIn: 0.95, browOut: 1.1, lidU: 1.04 });
      const FrueUp = JX('rueful', { mSmile: 0.48, mPress: 0.5, mAsym: 0.45, lidU: 0.9, lidL: 0.34, browIn: 0.62, browOut: 0.4 });
      const Fpat = JX('warm', { mSmile: 0.62, lidU: 0.84, lidL: 0.42, browIn: 0.5, wet: 0.35 });
      const Ften = JX('tender', { mSmile: 0.32, mPress: 0.35, browIn: 0.8, lidU: 0.88, wet: 0.5 });
      const Fdead = JX('kind', { mSmile: 0.0, mPress: 0.3, lidU: 0.95, lidL: 0.06, browIn: 0.65, browOut: 0.78 });
      const Fgive = JX('amused', { mSmile: 0.6, mAsym: 0.75, mPress: 0.45, lidU: 0.86, lidL: 0.4, browIn: 0.5, browOut: 0.65 });
      const Fgrin = JX('beam', { mSmile: 0.95, mOpen: 0.16, lidL: 0.6, lidU: 0.72 });
      const face = k(t, [['s15', Frue], [tUp0 + 0.2, Frue], [tUp1, Fkind, 'inOut'],
        [tTurn0, Fkind], [tTurn0 + 0.3, Fcur, 'inOut'], [tFind - 0.03, Fcur], [tFind + 0.12, Foh, 'out'], [tFind + 0.5, Foh], [tSh0 - 0.1, Fwarm, 'inOut'],
        [tSh0, Fwarm], [tSh1, Fshrug, 'out'], [tSh2, Fshrug], [tSh3 + 0.15, FrueUp, 'inOut'],
        [tReach1 - 0.1, FrueUp], [tReach1 + 0.25, Fpat, 'inOut'],
        [B5, Fpat], [tHand0 + 0.3, Ften, 'inOut'],
        [B6 - 0.3, Ften], [B6 - 0.05, Fdead, 'inOut'], [tCorner - 0.02, Fdead], [tCorner + 0.22, Fgive, 'out'],
        [tSnort + 0.05, Fgive], [tSnort + 0.3, Fgrin, 'out']]);
      face.autoBlink = 1;
      // the rock with each pat (contact moments)
      const rock = (t > tReach1 - 0.05 && t < tPatEnd + 0.3) ? Math.max(0, Math.cos(2 * Math.PI * patRate * (t - tReach1))) * pulse(t, tReach1 - 0.05, tPatEnd + 0.3, 0.05, 0.25) : 0;
      // ---- head: eyes lead the turn; the find = head way back
      const lookUp = ramp(t, tFind - 0.05, tFind + 0.25, (u) => 1 - Math.pow(1 - u, 3));
      const nodCorner = 0.05 * pulse(t, tCorner, tCorner + 0.5, 0.15, 0.3);
      const lead = -0.5 * pulse(t, tTurn0 - 0.25, tTurn1, 0.2, 0.35);            // the head leads the turn (to his right)
      // ---- arms: brush the knee on the way up; shrug; RIGHT hand over the big hand on his right shoulder
      const shrug = ramp(t, tSh0, tSh1, (u) => 1 - Math.pow(1 - u, 2.5)) * (1 - ramp(t, tSh2, tSh3));
      const handOn = ramp(t, tHand0, tHand1);
      let armR = { preset: [['rest', Math.max(1e-3, 1 - shrug)], ['shrug', Math.max(1e-3, shrug)]] };
      let armL = { preset: [['rest', Math.max(1e-3, 1 - shrug)], ['shrug', Math.max(1e-3, shrug)]] };
      const brush = pulse(t, tBr1 - 0.16, tBr2 + 0.28, 0.14, 0.2);
      if (kneel > 0.02) armL = { preset: [['knee_rest', Math.max(1e-3, kneel)], ['rest', Math.max(1e-3, 1 - kneel)]] };
      if (pass && brush > 0.001) {           // two swipes down the right (dusty) knee, bent over it
        const kn = jesus.anchor('kneeR');
        if (kn) {
          const fw = [Math.sin(jYawW), 0, Math.cos(jYawW)], rt = [-Math.cos(jYawW), 0, Math.sin(jYawW)];
          const u = t < tBr2 - 0.12 ? clamp((t - (tBr1 - 0.08)) / 0.24) : clamp((t - (tBr2 - 0.08)) / 0.24);
          armR = { preset: 'rest', target: add(arr(kn), [fw[0] * 0.08 + rt[0] * 0.03, 0.1 - 0.16 * smooth(u), fw[2] * 0.08 + rt[2] * 0.03]), reach: brush,
            palm: [-rt[0] * 0.3, -0.2, -rt[2] * 0.3], fingers: [fw[0] * 0.3, -1, fw[2] * 0.3], hand: { curl: 0.1, spread: 0.2, thumb: 0.3 } };
        }
      }
      if (handOn > 0.001 && pass && vh) {      // his RIGHT hand over the big hand on his right shoulder
        armR = { preset: 'shoulder', target: add(arr(vh), [0, 0.05, 0]), reach: handOn, palm: [0, -1, 0], hand: { curl: 0.3, spread: 0.12, cup: 0.45 } };
      }
      return {
        pos: jPos, yaw: jYawW,
        walk: { amount: 0.35 * pulse(t, tTurn0, tTurn1 + 0.1, 0.15, 0.2), phase: 0.6 * (t - tTurn0), style: 'walk' },
        body: { kneel, lean: 0.06 * kneel + 0.3 * brush - 0.03 * lookUp, shrug: 0.85 * shrug, bounce: -0.012 * rock, tilt: 0.02 * rock,
          recoil: 0.06 * pulse(t, tFind - 0.05, tFind + 0.5, 0.08, 0.3) + 0.03 * lookUp, breathe: 1 },
        head: { yaw: lead, look: pass && t > tTurn0 + 0.25 ? vE : undefined, follow: k(t, [[tTurn0 + 0.25, 0.3], [tFind, 0.85, 'out'], [tSh0, 0.72]]),
          roll: 0.1 * shrug - 0.04 * lookUp, pitch: nodCorner + 0.25 * brush, talk: 0.5 },
        gaze: pass ? (t < tTurn0 - 0.15 ? [EDGE.RISE_WORLD[0], EDGE.RISE_WORLD[1] + 1.1, EDGE.RISE_WORLD[2]] : brush > 0.3 ? add(arr(jesus.anchor('kneeR') || V3(...jPos)), [0, 0, 0]) : vE) : null,
        face,
        blinkAt: [tUp1 - 0.1, tTurn0 - 0.02, tSh3 + 0.1, tReach1 + 0.5, tHand1 + 0.1, B6 - 0.2, tSnort + 0.4],
        armL, armR,
      };
    };

    // ================================================================ VOID
    const vPose = (pass) => {
      const je = jesus.anchor('eyes');
      const jE = je ? arr(je) : SW(KP[0], 1.55, KP[2]);
      const rise = [EDGE.RISE_WORLD[0], EDGE.RISE_WORLD[1] + 1.2, EDGE.RISE_WORLD[2]];
      // ---- face (soft: lower lids up, inner brow-wisps up, no sly half-lids)
      const Fsoft = VX('gentle', { mSmile: 0.2, lidU: 0.8, lidL: 0.42, browIn: 0.75, browOut: -0.08, blush: 0.18 });
      const Fup = VX('gentle', { mSmile: 0.26, lidU: 0.84, lidL: 0.4, browIn: 0.9, browOut: -0.12, blush: 0.18 });
      const Fpat = VX('tender', { mSmile: 0.36, lidU: 0.82, lidL: 0.38, browIn: 0.72 });
      const Fsad = VX('sadSmile', { mSmile: 0.24, mWide: -0.45, mPress: 0.55, mDroop: 0.6, mWavy: 0.22, lidU: 0.78, lidL: 0.36, lidSad: 0.6, browIn: 1.2, browOut: -0.5, wet: 1 });
      const Fsigh = VX('sadSmile', { mSmile: 0.14, mWide: -0.35, mPress: 0.3, mDroop: 0.6, mWavy: 0.1, lidU: 0.55, lidL: 0.32, lidSad: 0.6, browIn: 1.0, browOut: -0.4, mOpen: 0.08, wet: 0.9 });
      const Ffond = VX('tender', { mSmile: 0.34, lidU: 0.84, lidL: 0.34, browIn: 0.62, wet: 0.6 });
      const Fwide = VX('surprised', { lidU: 1.36, browIn: 0.85, browOut: 0.8, mOpen: 0.05, mRound: 0.25, mSmile: 0.12 });
      const Fsnort = VX('laugh', { lidU: 0.2, lidL: 1, mOpen: 0.25, mSmile: 0.9, browIn: 0.6, browOut: 0.6, blush: 0.45 });
      const Fcrinkle = VX('giggle', { lidU: 0.3, lidL: 1, mOpen: 0.08, mSmile: 1, blush: 0.45 });
      const face = k(t, [['s15', Fsoft], [tFind, Fsoft], [tFind + 0.4, Fup, 'inOut'],
        [tReach1 - 0.2, Fup], [tReach1 + 0.2, Fpat, 'inOut'],
        [tSS, Fpat], [tSS + 0.45, Fsad, 'inOut'],                                 // the sad smile: mouth up, eyes don't follow
        [tSigh, Fsad], [tSigh + 0.35, Fsigh, 'inOut'], [B5e - 0.1, Fsigh], [B5e + 0.3, Ffond, 'inOut'],
        [tWiden - 0.02, Ffond], [tWiden + 0.12, Fwide, 'out'],
        [tSnort - 0.02, Fwide], [tSnort + 0.06, Fsnort, 'out'], [tSnort + 0.4, Fsnort], [tSnort + 0.75, Fcrinkle, 'inOut']]);
      face.autoBlink = 0;
      // ---- gaze: on Jesus's eyes; slides to the rise and back during the sad smile
      const slide = ramp(t, tSlide0, tSlide0 + 0.12) * (1 - ramp(t, tSlide1, tSlide1 + 0.14));
      const gaze = pass ? lerpA(jE, rise, slide) : null;
      // ---- body: bends toward him; leans in to pat; the sigh lifts and settles the shoulders
      const sigh = pulse(t, tSigh, B5e + 0.2, 0.5, 0.6);
      const patR = ramp(t, tReach0, tReach1, (u) => 1 - Math.pow(1 - u, 2));
      const snort = bump(t, tSnort - 0.02, 0.22);
      // ---- arms: hands clasped at the middle; LEFT (camera side) reaches DOWN onto his RIGHT shoulder, pats, stays;
      //      RIGHT covers the mouth on the snort
      const patAmt = pulse(t, tReach1 - 0.03, tPatEnd, 0.03, 0.12);
      const settle = ramp(t, tPatEnd + 0.2, tPatEnd + 1.3);                     // after the pats it straightens a little (hand stays)
      let armL = { preset: 'belly', hand: { curl: 0.42, spread: 0.04 } };
      if (patR > 0.001) {     // (Jesus is solved first in each pass, so his anchors are this frame's)
        const P = patHand(jesus, jYawW);
        if (P) {
          const arc = Math.sin(Math.PI * clamp(patR));
          armL = { preset: 'pat', target: P.target, reach: patR, pat: patAmt * 0.8, patRate, patPhase: tReach1, palm: P.palm, fingers: P.fingers, pole: P.pole,
            offset: [0, 0.18 * arc, 0], handScale: 0.52, hand: { curl: 0.25, cup: 0.6, spread: 0.12, thumb: 0.3 } };
        }
      }
      const cover = ramp(t, tCover - 0.06, tCover + 0.14, (u) => 1 - Math.pow(1 - u, 3));
      const armR = cover > 0.001 ? { preset: 'cover_mouth', from: 'belly', mix: cover, offset: [0, 0.16 * cover, 0] } : { preset: 'belly', hand: { curl: 0.42, spread: 0.04 } };
      return {
        pos: voidPos15(t), yaw: EDGE.Y(VY) - 0.08 * patR,
        walk: { amount: 0.7 * pulse(t, tReach0 - 0.35, tReach1 - 0.2, 0.15, 0.2), phase: 1.1 * (t - tReach0), style: 'waddle' },
        body: { lean: 0.13 + 0.26 * patR - 0.1 * settle, shrug: 0.35 * sigh + 0.12 * snort, breathe: 1 + 0.6 * sigh, breathRate: 0.2, recoil: 0.06 * snort, swell: 0.05 * sigh, twist: 0.1 - 0.32 * patR + 0.1 * settle, tilt: 0.05 * patR },
        head: { pitch: 0.24 + 0.02 * patR - 0.04 * sigh, yaw: 0.32 + 0.3 * patR + 0.06 * slide, roll: 0.04 * patR },
        gaze, face,
        blinkAt: [tFind + 0.45, tSlide1 + 0.3, B5e + 0.05],
        armL, armR,
        extra: { rim: 1.1, motes: 0.8 },
      };
    };

    // ================================================================ cameras (framed from pass-0 anchors)
    const cam = () => {
      let s;
      const ve = vd.anchor('eyes'), je = jesus.anchor('eyes');
      const vE = ve ? arr(ve) : SW(VP[0], 2.0, VP[2]), jE = je ? arr(je) : SW(KP[0], 1.5, KP[2]);
      const two = (dist, py, w = 0.45, fov = 40, yaw = 40) => frame(lerpA(jE, vE, w), { dist, yaw: EDGE.CY(yaw), pitch: 4, fov, screenY: sy(py), drift: 0.12 });
      // its eyeline: over its LEFT shoulder (camera side) / just off its eyes (once its arm is on him), down at his face
      const jup = (px, py, fov, back = 0, sideK = 0.72) => {
        const vdir = toV(jE).sub(toV(vE)).setY(0).normalize();
        const side = toV(SV(0.73, 0, 0.68)).normalize();
        let P = add(vE, [side.x * sideK + vdir.x * (0.32 - back), -0.12, side.z * sideK + vdir.z * (0.32 - back)]);
        const dv = toV(P).sub(toV(jE)), dl = dv.length();
        if (dl < 1.15) P = toV(jE).addScaledVector(dv.normalize(), 1.15).toArray();     // never closer than 1.15 m to his face
        return aimXY(P, jE, px, py, fov, { drift: 0.08 });
      };
      switch (shot) {
        case 'RISE': {   // front 3/4 on Jesus getting up (the Void looming above and behind him: we are in on it)
          const up = ramp(t, tUp0 + 0.2, tUp1 + 0.4);
          const jEk = SW(KP[0] + 0.12 * Math.sin(KY), lerp(1.2, 1.4, up), KP[2] + 0.12 * Math.cos(KY));
          s = EDGE.shot(EDGE.L(jEk), { dist: 2.9, yaw: -10, pitch: -4, fov: 44, screenY: sy(560), drift: 0.12 });
          break;
        }
        case 'JUP': s = jup(380, 430, 50, 0.25 + 0.1 * ramp(t, shotT0, shotT1)); break;
        case 'JUP2': s = jup(372, 420, 44, 0.1 + 0.1 * ramp(t, shotT0, shotT1), 0.34); break;
        case 'VPAT': {   // from behind Jesus (his back lower-left): the big hand reaching down onto his shoulder, its fingers
          //               over his shoulder and half his back; the Void's face above (it reads: its hood points here)
          const u = ramp(t, shotT0, tPatEnd + 0.4);
          s = frame(vE, { dist: lerp(4.1, 3.7, u), yaw: EDGE.CY(-24), pitch: 3, fov: 44, screenY: sy(260), drift: 0.1 });
          break;
        }
        case 'VCU': case 'VCU2': {   // close on the Void over his head, wide enough for its hand on his shoulder + his head
          const u = ramp(t, shotT0, shotT1);
          s = frame(vE, { dist: shot === 'VCU' ? lerp(3.1, 2.85, u) : 2.8, yaw: EDGE.CY(-24), pitch: 4, fov: 40, screenY: sy(shot === 'VCU' ? 300 : 320), drift: 0.1 });
          break;
        }
        default: s = two(4.6, 430);
      }
      applyShot(app.camera, s, t, 15);
    };

    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t) * (shot === 'VCU' || shot === 'VCU2' ? 1.0 : 0.85), voidPos: voidPos15(t),
      sunGlow: 0.9, seeds: shot === 'RISE' ? 0.6 : 0,
      clear: [[POS.V15[0], POS.V15[2], 1.3], [POS.K[0], POS.K[2], 0.7]],
    });
    solve(t, [[jesus, jPose], [vd, vPose]], cam);

    // ---- particles: the lilac sigh-wisp leaving the hood; the tiny star that pops out of the hood on the snort
    const mo = vd.anchor('mouth'), md = vd.mouthDir();
    fx.begin();
    drawSkyGalaxy(fx, t);
    if (mo) {
      fx.burst({ t, seed: 1507, at: tStar, count: 1, life: 0.9, jitter: 0, origin: add(arr(mo), [md.x * 0.12, 0.16, md.z * 0.12]),
        vel: [md.x * 0.35, 0.75, md.z * 0.35], spread: [0.04, 0.05, 0.04], gravity: [0, -0.35, 0], drag: 1.2, size: [0.09, 0.1], grow: 0.6,
        color: 0xfff1c8, alpha: 1, fade: [0.05, 0.5], cell: CELL.star, spin: 2 });
      fx.burst({ t, seed: 1508, at: tStar + 0.02, count: 3, life: 0.6, jitter: 0.05, origin: add(arr(mo), [md.x * 0.12, 0.12, md.z * 0.12]),
        vel: [md.x * 0.3, 0.4, md.z * 0.3], spread: [0.2, 0.15, 0.2], drag: 2, size: [0.02, 0.035], color: [0xd8c0ff, 0xbfe8ff], alpha: 0.8, fade: [0.05, 0.5], cell: CELL.dot });
    }
    fx.end();
    wisp.begin();
    if (mo) {   // out of the hood's upper rim, drifting up and out (never across the face)
      wisp.burst({ t, seed: 1509, at: tWisp, count: 3, life: 1.8, jitter: 0.25, origin: add(arr(mo), [md.x * 0.42, 0.42, md.z * 0.42]),
        vel: [md.x * 0.3, 0.32, md.z * 0.3], spread: [0.05, 0.03, 0.05], drag: 0.5, size: [0.18, 0.26], grow: 2.0,
        color: [0xc8a2ff, 0xd9b8ff], alpha: 0.3, fade: [0.3, 0.6], cell: CELL.nebula, spin: 0.4 });
    }
    wisp.end();
    st.look = lookFor('s15', set.look);
  },
};

function lerpA(a, b, u) { const A = arr(a), B = arr(b); return [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u]; }
