// s15 fair_enough — no hard feelings. Jesus gets up off his knee (a brush of the dusty knee), turns — eyes first —
// and has to tip his head way back: the Void is RIGHT THERE (it got up and shuffled over while he wasn't looking),
// hands clasped at its middle, lids at half, brow-wisps up in the middle; one slow blink. A big honest shrug ("eh:
// you win some"), and a rueful smile up at it. The Void reaches down and pats his shoulder, pat, pat, so gently its
// fingers cover his shoulder and half his back; the sad little smile (mouth up, eyes don't follow) — its eyes slide to
// the rise where the user vanished, and back; a slow blink: it has done this before. A long sigh, a lilac wisp from
// the hood, and Jesus lays his own hand over the big one. From the Void's eye-line, straight up at it: "Too intense.
// Apparently." — deadpan, until the mouth corner gives him away. Its eyes widen; a surprised snort, one little star
// pops out of the hood, eyes crinkle into arcs, a big hand over its mouth.
// Staging: the two face each other on the K <-> V15 line; both are CHEATED open to the camera side (Jesus ~20 deg,
// the Void ~30 deg + hood) so both faces read in the side two-shot (the Void's face only reads within ~50 deg of its
// hood). Shots: RISE (front 3/4 on Jesus, the Void looming behind) -> LOWUP (over his shoulder up at its face) ->
// TWO (cheated side two-shot, slow push: shrug + pat) -> VCU (sad smile) -> ease back to TWO (sigh, hand on hand)
// -> JUP (its eye-line down at him: the deadpan) -> VCU (widen, snort, star).
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { EDGE, todAt, voidSkyAt, sy, lookFor, frame } from './marks.js';
import { loadLines, W, POS, SW, SV, add, arr, own, stamp, drawSkyGalaxy, solve, pulse, V3, toV, ramp, bump, aim } from './kit_s14_16.js';

const M = EDGE.M;
const KP = M.K.p, KY = M.K.yaw, VP = M.V15.p;
export const S15 = {
  JY1: 1.92,                                   // Jesus faces the Void, cheated ~28 deg open to the camera side
  VY: M.V15.yaw + 0.2,                         // the Void, cheated ~11 deg open (+ its hood turned ~26 deg more; eyes on him)
};
const JY1 = S15.JY1, VY = S15.VY;

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
    const B1e = T('s15b01.end'), B3 = T('s15b03'), B4 = T('s15b04'), B5 = T('s15b05'), B5e = T('s15b05.end');
    const B6 = T('s15b06'), B7 = T('s15b07');
    const tBack = W('s15b01', 'back', { frac: 0.5 }), tVoid1 = W('s15b01', 'void', { alt: ['void.', 'void,'], frac: 0.8 });
    const tShrugs = W('s15b02', 'shrugs', { alt: ['shrugs.'], frac: 0.2 });
    const tPats = W('s15b03', 'pats', { alt: ['patts', 'pat'], frac: 0.25 });
    const tSad = W('s15b04', 'sad', { frac: 0.15 }), tSmile = W('s15b04', 'smile', { alt: ['smile.'], frac: 0.6 });
    const tAppEnd = W('s15b06', 'apparently', { alt: ['apparently.'], end: true, frac: 0.85 });
    // Jesus: up, brush, turn, look up
    const tUp0 = S + 0.15, tUp1 = tUp0 + 1.05;
    const tBrush = tUp1 - 0.32;
    const tTurn0 = Math.max(tUp1 - 0.08, tBack - 0.2), tTurn1 = tTurn0 + 0.62;
    const tFind = Math.max(tTurn1 - 0.05, tVoid1 - 0.12);                  // the head tips way back
    // shrug
    const tSh0 = tShrugs - 0.12, tSh1 = tSh0 + 0.22, tSh2 = tSh1 + 0.55, tSh3 = tSh2 + 0.3;
    // pats (contacts land on the pats)
    const tReach0 = tPats - 0.6, tReach1 = tPats - 0.04, patRate = 2.25;
    const tPatEnd = tReach1 + 2 / patRate - 0.02;
    // sad smile, the look to the rise, slow blink
    const tSS = tSad - 0.05, tSlide0 = tSmile + 0.05, tSlide1 = tSlide0 + 0.6;
    // sigh: shoulders up and settle, hand over hand
    const tSigh = B5 + 0.05, tHand0 = B5 + 0.4, tHand1 = tHand0 + 0.55;
    // the corner, the widening, the snort
    const tCorner = tAppEnd + 0.04, tWiden = tAppEnd + 0.3;
    const tSnort = B7 + 0.04, tCover = tSnort + 0.08, tStar = tSnort + 0.1;

    // ================================================================ shots
    const cutB = tFind + 0.12, cutD = B4 - 0.08, backE0 = tSigh + 0.45, backE1 = B6 - 0.1, cutF = tCorner + 0.32;
    const SHOTS = [[S, 'RISE'], [cutB, 'TWO'], [cutD, 'VCU'], [backE0, 'BACK'], [backE1, 'TWO2'], [cutF, 'VCU2']];
    let si = 0; for (let i = 0; i < SHOTS.length; i++) if (t >= SHOTS[i][0]) si = i;
    const shot = SHOTS[si][1];

    // ================================================================ JESUS
    const kneel = 1 - ramp(t, tUp0, tUp1);
    const turn = ramp(t, tTurn0, tTurn1, (u) => { const s = smooth(u); return s + 0.05 * Math.sin(Math.PI * s) * (u > 0.6 ? 1 : 0); });
    const jYawL = lerp(KY, JY1, turn);
    const jPos = EDGE.W(KP);
    const jPose = (pass) => {
      const ve = vd.anchor('eyes');
      const vE = ve ? arr(ve) : SW(VP[0], 2.0, VP[2]);
      const vh = vd.anchor('handL');
      // ---- face
      const Frue = JX('rueful', { mSmile: 0.42, mPress: 0.6, mAsym: 0.4, lidU: 0.6, lidL: 0.4, browIn: 0.45, browOut: 0.3 });
      const Fkind = JX('kind', { mSmile: 0.25 });
      const Fcur = JX('curious', { lidU: 1.04, mSmile: 0.15 });
      const Foh = JX('surprised', { lidU: 1.25, browIn: 0.8, browOut: 0.9, mOpen: 0.14, mRound: 0.6, mSmile: 0.12, pupil: 1.15 });
      const Fwarm = JX('warm', { mSmile: 0.5, lidU: 0.92, browIn: 0.45 });
      const Fshrug = JX('shrug', { mSmile: -0.1, mPress: 0.6, mWide: 0.4, browIn: 0.9, browOut: 1.05 });
      const FrueUp = JX('rueful', { mSmile: 0.42, mPress: 0.45, lidU: 0.86, lidL: 0.32, browIn: 0.6, browOut: 0.35 });
      const Fpat = JX('warm', { mSmile: 0.58, lidU: 0.8, lidL: 0.4, browIn: 0.5, wet: 0.35 });
      const Ften = JX('tender', { mSmile: 0.3, mPress: 0.35, browIn: 0.8, lidU: 0.84, wet: 0.5 });
      const Fdead = JX('kind', { mSmile: 0.0, mPress: 0.3, lidU: 0.9, lidL: 0.08, browIn: 0.6, browOut: 0.7 });
      const Fgive = JX('amused', { mSmile: 0.55, mAsym: 0.65, mPress: 0.45, lidU: 0.84, lidL: 0.38, browIn: 0.45, browOut: 0.6 });
      const Fgrin = JX('beam', { mSmile: 0.95, mOpen: 0.16, lidL: 0.6, lidU: 0.7 });
      const face = k(t, [['s15', Frue], [tUp0 + 0.2, Frue], [tUp1, Fkind, 'inOut'],
        [tTurn0, Fkind], [tTurn0 + 0.3, Fcur, 'inOut'], [tFind - 0.03, Fcur], [tFind + 0.12, Foh, 'out'], [tFind + 0.55, Foh], [tSh0 - 0.1, Fwarm, 'inOut'],
        [tSh0, Fwarm], [tSh1, Fshrug, 'out'], [tSh2, Fshrug], [tSh3 + 0.15, FrueUp, 'inOut'],
        [tReach1 - 0.1, FrueUp], [tReach1 + 0.25, Fpat, 'inOut'],
        [B5, Fpat], [tHand0 + 0.3, Ften, 'inOut'],
        [B6 - 0.3, Ften], [B6 - 0.05, Fdead, 'inOut'], [tCorner - 0.02, Fdead], [tCorner + 0.22, Fgive, 'out'],
        [tSnort + 0.05, Fgive], [tSnort + 0.3, Fgrin, 'out']]);
      face.autoBlink = 1;
      // the rock with each pat (contact moments)
      const rock = (t > tReach1 - 0.05 && t < tPatEnd + 0.3) ? Math.max(0, Math.cos(2 * Math.PI * patRate * (t - tReach1))) * pulse(t, tReach1 - 0.05, tPatEnd + 0.3, 0.05, 0.25) : 0;
      // ---- head: follows the Void's eyes (big look-ups need the head); the find = way back
      const lookUp = ramp(t, tFind - 0.05, tFind + 0.25, (u) => 1 - Math.pow(1 - u, 3));
      const nodCorner = 0.05 * pulse(t, tCorner, tCorner + 0.5, 0.15, 0.3);
      // ---- arms: brush the knee on the way up; shrug; LEFT hand over the big hand on his right shoulder
      const brush = pulse(t, tBrush - 0.15, tBrush + 0.45, 0.15, 0.2);
      const shrug = ramp(t, tSh0, tSh1, (u) => 1 - Math.pow(1 - u, 2.5)) * (1 - ramp(t, tSh2, tSh3));
      const handOn = ramp(t, tHand0, tHand1);
      let armR = { preset: [['rest', Math.max(1e-3, 1 - shrug)], ['shrug', Math.max(1e-3, shrug)]] };
      let armL = { preset: [['rest', Math.max(1e-3, 1 - shrug)], ['shrug', Math.max(1e-3, shrug)]] };
      if (kneel > 0.05 || brush > 0.001) {
        armL = { preset: [['knee_rest', Math.max(1e-3, kneel)], ['rest', Math.max(1e-3, 1 - kneel)]] };
        if (pass && brush > 0.001) {
          const kn = jesus.anchor('kneeR');
          if (kn) {
            const sw = Math.sin((t - tBrush) * 2 * Math.PI * 2.6);
            const fw = SV(Math.sin(jYawL), 0, Math.cos(jYawL));
            armR = { preset: 'rest', target: add(arr(kn), [fw[0] * 0.07, 0.06 + 0.035 * sw, fw[2] * 0.07]), reach: brush, palm: [0, -1, 0], hand: { curl: 0.1, spread: 0.2 } };
          }
        }
      }
      if (handOn > 0.001 && pass && vh) {
        armR = { preset: 'shoulder', target: add(arr(vh), [0, 0.045, 0]), reach: handOn, palm: [0, -1, 0], hand: { curl: 0.25, spread: 0.12, cup: 0.4 } };
      }
      return {
        pos: jPos, yaw: EDGE.Y(jYawL),
        walk: { amount: 0.35 * pulse(t, tTurn0, tTurn1 + 0.1, 0.15, 0.2), phase: 0.6 * (t - tTurn0), style: 'walk' },
        body: { kneel, lean: 0.05 * kneel - 0.03 * lookUp, shrug: 0.85 * shrug, bounce: -0.012 * rock, tilt: 0.02 * rock,
          recoil: 0.05 * pulse(t, tFind - 0.05, tFind + 0.5, 0.08, 0.3) + 0.03 * lookUp, breathe: 1 },
        head: { look: pass ? vE : undefined, follow: k(t, [['s15', 0.4], [tTurn0, 0.45], [tFind, 0.8]]), roll: 0.1 * shrug - 0.04 * lookUp, pitch: nodCorner, talk: 0.5 },
        gaze: pass ? (t < tTurn0 + 0.05 ? [EDGE.RISE_WORLD[0], EDGE.RISE_WORLD[1] + 1.1, EDGE.RISE_WORLD[2]] : vE) : null,
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
      // ---- face
      const Fsoft = VX('gentle', { mSmile: 0.18, lidU: 0.56, lidL: 0.34, browIn: 0.7, browOut: -0.08, blush: 0.15 });
      const Fup = VX('gentle', { mSmile: 0.24, lidU: 0.6, lidL: 0.32, browIn: 0.9, browOut: -0.12, blush: 0.15 });
      const Fpat = VX('tender', { mSmile: 0.34, lidU: 0.72, lidL: 0.36, browIn: 0.7 });
      const Fsad = VX('sadSmile', { mSmile: 0.4, mDroop: 0.55, lidU: 0.66, lidL: 0.3, lidSad: 0.55, browIn: 1.15, browOut: -0.5, wet: 0.95 });
      const Fsigh = VX('sadSmile', { mSmile: 0.22, mDroop: 0.6, lidU: 0.48, lidL: 0.3, lidSad: 0.55, browIn: 0.95, browOut: -0.38, mOpen: 0.06, wet: 0.85 });
      const Ffond = VX('tender', { mSmile: 0.32, lidU: 0.78, lidL: 0.3, browIn: 0.6, wet: 0.6 });
      const Fwide = VX('surprised', { lidU: 1.32, browIn: 0.8, browOut: 0.75, mOpen: 0.05, mRound: 0.25, mSmile: 0.12 });
      const Fsnort = VX('laugh', { lidU: 0.2, lidL: 1, mOpen: 0.25, mSmile: 0.9, browIn: 0.6, browOut: 0.6, blush: 0.45 });
      const Fcrinkle = VX('giggle', { lidU: 0.3, lidL: 1, mOpen: 0.08, mSmile: 1, blush: 0.45 });
      const face = k(t, [['s15', Fsoft], [tFind, Fsoft], [tFind + 0.4, Fup, 'inOut'],
        [tReach1 - 0.2, Fup], [tReach1 + 0.2, Fpat, 'inOut'],
        [tSS, Fpat], [tSS + 0.5, Fsad, 'inOut'],                                 // the sad smile: mouth up, eyes don't follow
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
      // ---- arms: hands clasped at the middle; LEFT (camera side) pats his RIGHT (camera-side) shoulder and stays;
      //      RIGHT covers the mouth on the snort
      const patAmt = pulse(t, tReach1 - 0.03, tPatEnd, 0.03, 0.12);
      // the hand cups the OUTSIDE of his shoulder (fingers up over it toward his back), forearm low: below his chin
      let armL = { preset: 'belly', hand: { curl: 0.42, spread: 0.04 } };
      const shR = jesus.anchor('shoulderR');
      if (patR > 0.001 && shR) {     // (Jesus is solved first in each pass, so his anchors are this frame's)
        const jy = EDGE.Y(jYawL), jr = [-Math.cos(jy), 0, Math.sin(jy)], jb = [-Math.sin(jy), 0, -Math.cos(jy)];
        const tg = add(arr(shR), [jr[0] * 0.07 + jb[0] * 0.02, -0.06, jr[2] * 0.07 + jb[2] * 0.02]);
        const fg = V3(jb[0] * 0.9, 0.42, jb[2] * 0.9).normalize();
        armL = { preset: 'pat', target: tg, reach: patR, pat: patAmt * 0.8, patRate, patPhase: tReach1, palm: [-jr[0], -0.25, -jr[2]], fingers: fg.toArray(),
          pole: [jr[0] * 0.3, -1, jr[2] * 0.3], handScale: 0.66, hand: { curl: 0.22, cup: 0.55, spread: 0.14, thumb: 0.3 } };
      } else if (patR > 0.001) armL = { preset: 'belly', hand: { curl: 0.42, spread: 0.04 } };
      const cover = ramp(t, tCover - 0.06, tCover + 0.14, (u) => 1 - Math.pow(1 - u, 3));
      const armR = cover > 0.001 ? { preset: 'cover_mouth', from: 'belly', mix: cover, offset: [0, 0.16 * cover, 0] } : { preset: 'belly', hand: { curl: 0.42, spread: 0.04 } };
      return {
        pos: EDGE.W(VP), yaw: EDGE.Y(VY),
        body: { lean: 0.13 + 0.09 * patR, shrug: 0.35 * sigh + 0.12 * snort, breathe: 1 + 0.6 * sigh, breathRate: 0.2, recoil: 0.06 * snort, swell: 0.05 * sigh, twist: 0.1, tilt: 0.04 * patR },
        head: { pitch: 0.24 + 0.05 * patR - 0.04 * sigh, yaw: 0.45 + 0.06 * slide, roll: 0.04 * patR },
        gaze,
        face,
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
      const two = (dist, py, w = 0.45, fov = 40) => {
        const mid = lerpA(jE, vE, w);
        return frame(mid, { dist, yaw: EDGE.CY(36), pitch: 4, fov, screenY: sy(py), drift: 0.12 });
      };
      switch (shot) {
        case 'RISE': {   // front 3/4 on Jesus getting up (the Void looming above and behind him: we are in on it)
          // a locked frame (only a slight tilt): he rises INTO it, so the getting-up reads
          const up = ramp(t, tUp0 + 0.2, tUp1 + 0.4);
          const jEk = SW(KP[0] + 0.12 * Math.sin(KY), lerp(1.2, 1.36, up), KP[2] + 0.12 * Math.cos(KY));
          s = EDGE.shot(EDGE.L(jEk), { dist: 2.9, yaw: -14, pitch: -5, fov: 44, screenY: sy(560), drift: 0.12 });
          break;
        }
        case 'TWO': {    // cheated side two-shot, a slow push from 4.6 to 3.7 over the shrug and the pats
          const u = ramp(t, cutB + 0.6, tPats + 0.7);
          s = two(lerp(4.6, 3.7, u), 430);
          break;
        }
        case 'TWO2': s = two(3.3, 430, 0.38, 46); break;   // tighter for the deadpan + the widening eyes
        case 'VCU': case 'VCU2': case 'BACK': {
          const cu = frame(vE, { dist: 2.4, yaw: EDGE.CY(-10), pitch: -5, fov: 33, screenY: sy(shot === 'VCU2' ? 340 : 360), drift: 0.1 });
          if (shot === 'BACK') {
            const u = ramp(t, backE0, backE1 - 0.05);
            const b = two(3.7, 430);
            s = { pos: cu.pos.map((x, i) => lerp(x, b.pos[i], u)), look: cu.look.map((x, i) => lerp(x, b.look[i], u)), fov: lerp(cu.fov, b.fov, u), drift: 0.1 };
          } else s = cu;
          break;
        }
        default: s = two(4.6, 430);
      }
      applyShot(app.camera, s, t, 15);
    };

    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t) * (shot === 'VCU' || shot === 'VCU2' ? 1.0 : 0.85), voidPos: EDGE.W(VP),
      sunGlow: 0.9,
      clear: [[POS.V15[0], POS.V15[2], 1.3], [POS.K[0], POS.K[2], 0.7]],
    });
    solve(t, [[jesus, jPose], [vd, vPose]], cam);

    // ---- particles: the lilac sigh-wisp; the tiny star that pops out of the hood on the snort
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
    if (mo) {
      wisp.burst({ t, seed: 1509, at: tSigh + 0.45, count: 3, life: 1.7, jitter: 0.3, origin: add(arr(mo), [md.x * 0.18, 0.02, md.z * 0.18]),
        vel: [md.x * 0.22, 0.22, md.z * 0.22], spread: [0.06, 0.04, 0.06], drag: 0.6, size: [0.22, 0.32], grow: 2.2,
        color: [0xc8a2ff, 0xd9b8ff], alpha: 0.32, fade: [0.25, 0.6], cell: CELL.nebula, spin: 0.4 });
    }
    wisp.end();
    st.look = lookFor('s15', set.look);
  },
};

function lerpA(a, b, u) { const A = arr(a), B = arr(b); return [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u]; }
