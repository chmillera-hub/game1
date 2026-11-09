// s14 blocked — the user's exit: up in one scramble, two angry swipes at the backside, an about-face, and stomping
// off down the path toward the sun, eyes on the phone ("Way. Too. Intense."). Insert: a six-frame trembling hover
// over Block, a stab, and a second entirely unnecessary stab. Over Jesus's shoulder the user holds the phone up over
// their shoulder ("You blocked Jesus.") without looking back — and a cheerful ding answers from inside his sash.
// He pats it, pulls out his plain little phone (insert: "@definitely_fine_lol blocked you."), reads it again, the
// brows climb, a small round 'oh'. Cutaway: on the crest of the rise the user stops, glances back once, and is gone.
// Back on Jesus: a wince-smile, the phone tucked away, the sash smoothed with great dignity, a rueful nose-exhale.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, noise1 } from '../core/util.js';
import { Particles } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { UX } from '../chars/user.js';
import { EDGE, todAt, voidSkyAt, sy, lookFor } from './marks.js';
import { loadLines, W, POS, YAW, SW, SV, add, arr, own, stamp, drawSkyGalaxy, makeLittleGalaxy, solve, pulse,
  V3, toV, ramp, bump, pathPose, pathS, rollFor, aim, aimXY, makeJesusPhone, glowSprite, fblend, hideDuring } from './kit_s14_16.js';

const M = EDGE.M;
const KP = M.K.p, KY = M.K.yaw;
const FWD_K = [Math.sin(KY), 0, Math.cos(KY)];                 // Jesus's facing at K (stage-local)
const JEYE = [KP[0] + 0.17 * FWD_K[0], 1.05, KP[2] + 0.17 * FWD_K[2]];   // his eyes, kneeling (s13 measured)
const STRIDE = 0.8;                                             // USER stomp stride (m per cycle)

export default {
  id: 's14',
  async setup(app) {
    await loadLines();
    const set = await app.set('EDGE');
    const [jesus, vd, user] = await Promise.all([app.char('JESUS'), app.char('VOID'), app.char('USER')]);
    const fx = new Particles({ max: 24, intensity: 1.5 });
    own(fx.mesh, 's14');
    const gal = makeLittleGalaxy();
    const phone = makeJesusPhone(); own(phone.group, 's14');
    const ding = glowSprite(0xffe2b0, 0.2); own(ding, 's14');
    // path stations (metres along the EDGE path from pathStart): the user's seat, the crest of the rise
    const sU = pathS(set, POS.USEAT), sRise = pathS(set, EDGE.RISE_WORLD);
    // the phone insert's camera sits at the user's chest: cheat the hoodie drawstrings out of the lens for that shot
    const insW = [T('s14b03') - 0.1, Math.max(T('s14b03') + 1.67, T('s14b03.end') - 0.95)];
    if (user.strings) for (const sg of user.strings) { hideDuring(sg.tb.mesh, [insW]); hideDuring(sg.ag, [insW]); }
    return { scene: set.scene, set, jesus, vd, user, fx, gal, phone, ding, sU, sRise, look: lookFor('s14', set.look) };
  },

  async update(t, app, st) {
    stamp(t, 's14');
    const { set, jesus, vd, user, fx, gal, phone, ding, sU, sRise } = st;
    for (const o of [jesus.root, vd.root, user.root, fx.mesh, gal, phone.group, ding]) st.scene.add(o);
    jesus.root.visible = vd.root.visible = user.root.visible = true;

    // ================================================================ timing (beats + words)
    const S = T('s14'), E = T('s14.end');
    const B1 = T('s14b01'), B2 = T('s14b02'), B3 = T('s14b03'), B3e = T('s14b03.end'), B5 = T('s14b05'), B6 = T('s14b06'), B6e = T('s14b06.end');
    const tUser = W('s14b01', 'user'), tStorms = W('s14b01', 'storms');
    const tWay = W('s14b02', 'way'), tToo = W('s14b02', 'too', { alt: ['to'], frac: 0.15 }), tInt = W('s14b02', 'intense', { frac: 0.45 });
    const tBlocks = W('s14b03', 'blocks', { frac: 0.05 }), tTwit = W('s14b03', 'twitter', { frac: 0.8 });
    const tVoid6 = W('s14b06', 'void', { alt: ['void,'], frac: 0.35 }), tToo6 = W('s14b06', 'too', { frac: 0.6 });
    // the user
    const tRise0 = tUser - 0.12, tRise1 = tRise0 + 1.0;            // up in one scramble
    const tBr1 = tRise1 - 0.18, tBr2 = tRise1 + 0.14;              // two angry swipes at the backside
    const tPiv0 = tRise1 + 0.02, tPiv1 = tPiv0 + 0.5;              // about-face (face sweeps past the wide camera)
    const tGo = Math.min(tPiv1 - 0.12, tStorms + 0.1);             // first stomp
    const tHover = tBlocks - 0.02, tStab1 = tHover + 0.27, tStab2 = tStab1 + 0.3;   // 6 trembling frames, stab, stab
    const cutD = Math.max(tStab2 + 0.95, B3e - 0.95);              // over Jesus's shoulder ("...On Twitter.")
    const tShow0 = cutD + 0.12, tShow1 = B5 + 0.35;                // phone held up over the shoulder, screen back
    const tDing = B5 + 0.14;                                       // the cheerful ding from the sash
    const tVoidE = W('s14b06', 'void', { alt: ['void,'], end: true, frac: 0.42 });
    const tCrest = tVoidE - 0.2, tLook0 = tVoidE + 0.08, tLook1 = tLook0 + 0.36, tOver = tLook1 + 0.02;
    // Jesus
    const tPat1 = tDing + 0.3, tPat2 = tPat1 + 0.22, tPull0 = tPat2 + 0.16, tPull1 = tPull0 + 0.38;
    const cutR = tVoidE + 0.05, cutJ3 = Math.max(cutR + 0.6, tToo6 + 0.3);   // the glance-back cutaway, inside b06
    const tTuck0 = cutJ3 + 0.32, tTuck1 = tTuck0 + 0.3, tSmooth0 = tTuck1 - 0.02, tSmooth1 = tSmooth0 + 0.5, tExhale = tSmooth1 + 0.04;

    // ================================================================ shot list (cut times)
    const SHOTS = [[S, 'WIDE'], [B2 - 0.12, 'TRACK'], [B3 - 0.1, 'UINS'], [cutD, 'OVER'], [tDing + 0.1, 'JST'],
      [tPull1 + 0.06, 'JINS'], [B6 + 0.28, 'JST'], [cutR, 'RISE'], [cutJ3, 'JST']];
    let si = 0; for (let i = 0; i < SHOTS.length; i++) if (t >= SHOTS[i][0]) si = i;
    const shot = SHOTS[si][1], shotT0 = SHOTS[si][0], shotT1 = SHOTS[si + 1] ? SHOTS[si + 1][0] : E;

    // ================================================================ the user's exit along the path (pure)
    // speed profile: stomp off, slow to a crawl while blocking, stomp on, stop on the crest, glance back, go over
    const vC = 1.02;
    const speed = (x) => {
      if (x < tGo || (x > tCrest && x < tOver)) return 0;
      let v = vC * ramp(x, tGo, tGo + 0.35);
      v *= 1 - 0.75 * ramp(x, tHover - 0.45, tHover - 0.05) * (1 - ramp(x, cutD - 0.05, cutD + 0.4));   // slows right down while blocking
      if (x <= tCrest) v *= 1 - ramp(x, tCrest - 0.5, tCrest);
      else v = vC * 0.85 * ramp(x, tOver, tOver + 0.3);
      return v;
    };
    const travelled = (x) => { if (x <= tGo) return 0; const n = Math.max(8, Math.ceil((x - tGo) * 24)); let s = 0; const h = (x - tGo) / n; for (let i = 0; i < n; i++) s += speed(tGo + (i + 0.5) * h) * h; return s; };
    // scale so the crest stop lands exactly on the rise
    const dCrest = travelled(tCrest);
    const sc = Math.max(0.6, (sRise - sU) / Math.max(0.5, dCrest));
    const dist = travelled(t) * sc;
    const uWalk = pathPose(set, sU + dist, 0);
    const uAmt = clamp(speed(t) / vC) * (t < tGo + 0.1 ? ramp(t, tGo - 0.05, tGo + 0.15) : 1);
    const uPhase = (dist / STRIDE) + 0.25;

    // ================================================================ JESUS (kneeling at K the whole scene)
    const jPose = (pass) => {
      const ue = user.anchor('eyes'), uph = user.anchor('phone');
      const uE = ue ? arr(ue) : SW(-1.3, 0.9, 1.4);
      const face = (() => {
        const Fgive = JX('rueful', { mSmile: 0.22, mPress: 0.55, browIn: 0.55, browOut: 0.1, lidU: 0.86, lidL: 0.3 });
        const Fhope = JX('hopeful', { mSmile: 0.34, mOpen: 0.03, mTeethU: 0, browIn: 0.7, browOut: 0.45, lidU: 1.1, lidL: 0.1 });
        const Foh = JX('oh', { mOpen: 0.15, mRound: 0.7, mSmile: 0.0, browIn: 0.95, browOut: 0.2, browSq: 0.1, lidU: 1.08, lidL: 0.05, lidSad: 0.2 });
        const Fsoft = JX('concerned', { mSmile: 0.04, mPress: 0.2, browIn: 0.7, lidU: 1.0 });
        const Fsquint = JX('reading', { lidU: 0.92, lidL: 0.36, browSq: 0.2, mPress: 0.2, mSmile: 0.06, browIn: 0.3, browOut: 0.15 });
        const Fding = JX('surprised', { lidU: 1.2, browIn: 0.85, browOut: 0.95, mOpen: 0.08, mRound: 0.55, mSmile: 0.12 });
        const Fcur = JX('curious', { lidU: 1.08, browIn: 0.6, browOut: 0.7, mSmile: 0.18, mRound: 0.2, mOpen: 0.03 });
        const Fread = JX('reading', { lidU: 0.96, lidL: 0.2, browSq: 0.1, browIn: 0.42, browOut: 0.3, mPress: 0.18, mSmile: 0.08 });
        const Fclimb = JX('reading', { lidU: 0.98, lidL: 0.15, browSq: 0.1, browIn: 0.55, browOut: 0.6, mPress: 0.15 });
        const Foh2 = JX('oh', { mOpen: 0.16, mRound: 0.75, browIn: 0.78, browOut: 0.78, lidU: 1.14, pupil: 1.1 });
        const Fwince = JX([['awkward', 0.65], ['wince', 0.35]], { mSmile: 0.3, mClench: 1, mOpen: 0.3, mWide: 1, mAsym: 0.2, mTeethU: 1, lidU: 0.82, lidL: 0.72, browIn: 1.15, browOut: 0.1, browSq: 0.3, lidSad: 0.3, saccade: 0 });
        const Fdign = JX('serene', { mSmile: 0.28, mPress: 0.5, lidU: 0.55, lidL: 0.3, browIn: 0.35, browOut: 0.1 });
        const Fexh = JX('rueful', { mSmile: 0.42, mPress: 0.6, mAsym: 0.4, lidU: 0.5, lidL: 0.45, browIn: 0.45, browOut: 0.3 });
        return k(t, [
          ['s14', Fgive], [tRise0 + 0.1, Fgive], [tRise0 + 0.45, Fhope, 'inOut'],      // a flicker of hope: are they coming?
          [tPiv0 + 0.05, Fhope], [tPiv0 + 0.4, Foh, 'inOut'],                         // ...no. The smile fades to a small 'oh'
          [B2 + 0.4, Foh], [B2 + 1.2, Fsoft, 'inOut'],
          [tShow0 + 0.1, Fsoft], [tShow0 + 0.5, Fsquint, 'inOut'],                    // squints at the far little screen
          [tDing - 0.02, Fsquint], [tDing + 0.12, Fding, 'out'],                      // DING: brows up
          [tPat1, Fding], [tPat1 + 0.3, Fcur, 'inOut'],
          [tPull1, Fcur], [tPull1 + 0.25, Fread, 'inOut'],
          [B6 + 0.4, Fread], [tVoid6 - 0.32, Fclimb, 'inOut'], [tVoid6 - 0.06, Foh2, 'out'],   // brows climb, a small round 'oh'
          [tToo6 - 0.2, Foh2], [tToo6 + 0.1, Fwince, 'out'],                          // "too ^intensely": the wince-smile
          [tTuck0 + 0.2, Fwince], [tSmooth0 + 0.12, Fdign, 'inOut'], [tExhale - 0.02, Fdign], [tExhale + 0.14, Fexh, 'out'],
        ]);
      })();
      // ---- gaze: the user (eyes) -> the far little screen -> his chest (the ding) -> his phone -> scanning the card
      const hR = pass ? jesus.anchor('handR') : null;                 // (pass 1: this frame's pass-0 hand)
      const jph = hR && t > tPull0 ? add(arr(hR), [0, 0.04, 0]) : null;
      const chest = jesus.anchor('chest');
      const chestP = chest ? add(arr(chest), [0, -0.02, 0]) : SW(KP[0], 0.75, KP[2]);
      const phoneP = jph || add(chestP, [0, 0.25, 0]);
      const uPhone = uph ? arr(uph) : uE;
      const scan = (x) => [0.03 * Math.sin(x * 9.5), -0.006 * Math.floor(((x - B6) * 1.6) % 3), 0];   // a few saccades along the line
      const gz = (() => {
        if (t < tShow0 + 0.1) return uE;
        if (t < tDing + 0.05) return lerpA(uE, uPhone, ramp(t, tShow0 + 0.1, tShow0 + 0.35) * (1 - ramp(t, tShow1 - 0.1, tShow1 + 0.1)));
        if (t < tPull0) return lerpA(uE, chestP, ramp(t, tDing + 0.05, tDing + 0.15));
        const aside = [EDGE.RISE_WORLD[0] - 2.5, 2.2, EDGE.RISE_WORLD[2]];
        const upOff = jesus.anchor('eyes') ? add(arr(jesus.anchor('eyes')), SV(FWD_K[0] * 3 - 0.4, 0.25, FWD_K[2] * 3)) : aside;
        const take = pulse(t, tVoid6 - 0.06, tToo6 - 0.12, 0.08, 0.14);
        if (t < tTuck0 + 0.1) return lerpA(lerpA(lerpA(chestP, add(phoneP, scan(t)), ramp(t, tPull0 + 0.05, tPull0 + 0.3)), upOff, take), aside, pulse(t, tToo6 - 0.08, tTuck0 + 0.12, 0.06, 0.12));
        const riseP = [EDGE.RISE_WORLD[0], EDGE.RISE_WORLD[1] + 1.2, EDGE.RISE_WORLD[2]];
        return lerpA(lerpA(phoneP, add(chestP, [0, -0.05, 0]), ramp(t, tTuck0 + 0.1, tTuck0 + 0.3)), riseP, ramp(t, tSmooth1 - 0.1, tSmooth1 + 0.15));
      })();
      const look = t < tDing + 0.05 ? uE : gz;
      // ---- head: follows the user out (eyes lead); the ding tips the chin to the chest; reading posture
      const follow = k(t, [['s14', 0.6], [tDing, 0.6], [tDing + 0.3, 0.35], [cutJ3, 0.35], [tSmooth1, 0.3]]);
      const nod = 0.06 * pulse(t, tExhale - 0.05, tExhale + 0.5, 0.1, 0.3) - 0.1 * pulse(t, tVoid6 - 0.04, tToo6 - 0.1, 0.1, 0.16);
      const tilt = k(t, [['s14', 0.06], [tDing, 0.06], [tDing + 0.2, 0.13, 'out'], [tPull1, 0.1], [B6 + 0.6, 0.04], [tVoid6, 0.1], [B6e + 0.3, -0.04], [tSmooth1, 0.03]]);
      // ---- arms: from s13's open palms -> hands settle on the thigh/knee; the aborted little reach ("wait—")
      const settle = ramp(t, tRise0 + 0.2, tPiv1 + 0.4);
      const wait = pulse(t, tPiv0 + 0.05, tGo + 0.95, 0.25, 0.45);
      const armL = { preset: [['knee_rest', 0.65 + 0.35 * settle], ['open', 0.35 * (1 - settle) + 1e-3]], hand: { splay: 0.05, cup: 0.4, curl: 0.12 + 0.3 * ramp(t, tDing, tDing + 0.6) },
      palm: ramp(t, tPiv1, tPiv1 + 0.8) > 0.5 ? [0, -1, 0.15] : undefined };          // (relaxed on the knee, palm down)
      let armR = { preset: [['open', Math.max(1e-3, 1 - settle)], ['rest', Math.max(1e-3, settle)]], hand: { splay: 0.06, cup: 0.4 } };
      if (wait > 0.001) armR = { preset: [['open', Math.max(1e-3, (1 - settle) * (1 - wait))], ['rest', Math.max(1e-3, settle * (1 - wait))], ['offer', wait * 0.6 + 1e-3]], hand: { curl: 0.08, spread: 0.32, splay: 0.08, thumb: 0.55, cup: 0.2 } };
      // the ding: pat-pat on the sash (right hand flat on the chest), pull the phone out and hold it up
      const toChest = ramp(t, tDing + 0.1, tPat1 - 0.02) * (1 - ramp(t, tPull0, tPull0 + 0.2));
      const hold = ramp(t, tPull0, tPull1) * (1 - ramp(t, tTuck0, tTuck0 + 0.25));
      const back = ramp(t, tTuck0 + 0.15, tTuck1) * (1 - ramp(t, tSmooth1 - 0.05, tSmooth1 + 0.3));
      const jHead = jesus.anchor('eyes');
      if (toChest + hold + back > 0.001) {
        const patOff = -0.03 * (bump(t, tPat1 - 0.05, 0.16) + bump(t, tPat2 - 0.05, 0.16));
        const pr = [['rest', Math.max(1e-3, settle * (1 - toChest - hold - back))], ['heart', Math.max(1e-3, toChest + back)]];
        armR = { preset: pr, hand: { curl: 0.1, spread: 0.12, thumb: 0.35, cup: 0.2 } };
        if (pass && chest) {
          const fw = SV(...FWD_K);
          if (toChest + back > 0.001) armR.offset = [fw[0] * patOff, 0.01 + patOff * 0.2, fw[2] * patOff];
          // smoothing the sash: the flat hand slides DOWN along the band (from his left chest toward his right hip), twice
          if (back > 0.001 && t > tSmooth0 - 0.05) {
            const u = clamp((t - tSmooth0) / (tSmooth1 - tSmooth0));
            const st1 = smooth(clamp(u / 0.55)), st2 = smooth(clamp((u - 0.55) / 0.45));
            const rt = SV(-Math.cos(KY), 0, Math.sin(KY)), lf = [-rt[0], 0, -rt[2]];
            const c = arr(chest);
            const A = add(c, [lf[0] * 0.075 + fw[0] * 0.02, 0.07, lf[2] * 0.075 + fw[2] * 0.02]);
            const B = add(c, [-lf[0] * 0.085 + fw[0] * 0.03, -0.17, -lf[2] * 0.085 + fw[2] * 0.03]);
            const A2 = lerpA(A, B, 0.3);
            const lift = 0.025 * Math.sin(Math.PI * clamp((u - 0.5) / 0.1));               // off the cloth between strokes
            const P = u < 0.55 ? lerpA(A, B, st1) : lerpA(lerpA(B, A2, smooth(clamp((u - 0.55) / 0.08))), B, st2);
            const dir = toV(B).sub(toV(A)).normalize();
            armR = { preset: 'heart', target: add(P, [fw[0] * lift, 0, fw[2] * lift]), at: 'palm', reach: back,
              palm: [-fw[0], 0.05, -fw[2]], fingers: dir.toArray(), hand: { curl: 0.04, spread: 0.06, thumb: 0.3, cup: 0.05 } };
          }
        }
        if (hold > 0.001 && pass && jHead) {
          // holding the phone up the way people do: palm toward his eyes, ~30 cm out, a little below eye level
          const fw = SV(...FWD_K), rt = SV(-Math.cos(KY), 0, Math.sin(KY));
          const P = add(arr(jHead), [fw[0] * 0.3 + rt[0] * 0.02, -0.25, fw[2] * 0.3 + rt[2] * 0.02]);
          const pn = toV(arr(jHead)).sub(toV(P)).normalize();
          const lf = V3(-rt[0], 0.15, -rt[2]);                                     // fingers across the phone's back (to his left)
          const fu = lf.addScaledVector(pn, -lf.dot(pn)).normalize();
          const hand = jesus.anchor('handR');
          armR = { preset: [['heart', Math.max(1e-3, 1 - hold)], ['offer', Math.max(1e-3, hold)]], hand: { curl: shot === 'JINS' ? 0.12 : 0.55, spread: 0.0, thumb: 0.15, cup: shot === 'JINS' ? 0.05 : 0.3, splay: 0.0 },   // (the insert cheats the fingers behind the phone)
            target: hand ? arr(toV(arr(hand)).lerp(toV(P), hold)) : P, at: 'palm', palm: pn.toArray(), fingers: fu.toArray() };
        }
      }
      const exhale = pulse(t, tExhale, tExhale + 0.6, 0.15, 0.4);
      const eek = pulse(t, tToo6 - 0.1, tTuck1 + 0.05, 0.14, 0.3);
      return {
        pos: EDGE.W(KP), yaw: EDGE.Y(KY),
        body: { kneel: 1, lean: 0.08 + 0.05 * ramp(t, tRise0, tRise0 + 0.4) * (1 - ramp(t, tPiv0, tPiv1)) + 0.04 * hold, shrug: 0.05 * pulse(t, tDing, tDing + 0.35, 0.06, 0.25) - 0.04 * exhale + 0.22 * eek,
          breathe: 1 + 0.6 * exhale, sway: 0.5, recoil: 0.04 * pulse(t, tDing, tDing + 0.4, 0.06, 0.3) },
        head: { look: look, follow, pitch: 0.04 * hold + nod, roll: -tilt + 0.12 * eek + (shot === 'OVER' ? 0.12 : 0), talk: 0 },   // (OVER: a hair cheat off his right shoulder)
        gaze: pass ? gz : null,
        face: { ...face, autoBlink: shot === 'JINS' ? 0 : 1 },
        blinkAt: [tPiv0 + 0.3, B2 + 0.75, tDing + 0.45, tPull1 + 0.05, tVoid6 + 0.45, tTuck0 + 0.05, tExhale + 0.02],
        armL, armR,
        speech: false,
      };
    };

    // ================================================================ USER
    const lookBackW = (x) => 0.95 * ramp(x, tLook0, tLook0 + 0.18) * (1 - ramp(x, tLook1 - 0.12, tLook1 + 0.14));
    const uPose = (pass) => {
      const je = jesus.anchor('eyes');
      const jE = je ? arr(je) : SW(...JEYE);
      const phs = user.anchor('phoneScreen');
      const phS = phs ? arr(phs) : add(uWalk.pos, [0, 1.0, 0]);
      // ---- facing: seated toward the Void (U yaw) -> about-face (decreasing yaw: the face sweeps past the wide
      //      camera) -> along the path
      const yU = YAW.U;
      let yPath = uWalk.yaw; while (yPath > yU) yPath -= 2 * Math.PI; while (yPath < yU - 2 * Math.PI) yPath += 2 * Math.PI;
      const pv = ramp(t, tPiv0, tPiv1, (u) => { const s = smooth(u); return s + 0.06 * Math.sin(Math.PI * s) * (u > 0.7 ? 1 : 0); });
      const yaw = lerp(yU, yPath, pv) + 0.55 * lookBackW(t);
      const sit = 1 - ramp(t, tRise0, tRise1);
      // over the crest: the far side drops away (from the low long lens the legs, then the body sink behind the rise)
      const sink = 0.75 * ramp(t, tOver + 0.02, tOver + 0.34, (u) => u * u);
      const pos = t < tGo ? POS.USEAT : [uWalk.pos[0], uWalk.pos[1] - sink, uWalk.pos[2]];
      // ---- face
      const Fnope = UX([['hellno', 0.45], ['deadpan', 0.55]], { wet: 0.5 });
      const Fstorm = UX('storm', { wet: 0.4 });
      const Fmutter = UX([['storm', 0.7], ['glare', 0.3]], { wet: 0.4, mPout: 0.3 });
      const Fstab = UX('glare', { lidU: 0.5, lidL: 0.45, mPress: 0.85 });
      const Fsmug = UX([['smirk', 0.5], ['storm', 0.5]], { wet: 0.3 });
      const Fguilt = UX('guilt', { wet: 0.6, lidU: 0.92 });
      const face = k(t, [['s14', Fnope], [tRise0 - 0.1, Fnope], [tRise0 + 0.15, Fstorm, 'out'],
        [B2 - 0.2, Fstorm], [B2, Fmutter, 'inOut'], [tHover - 0.3, Fmutter], [tHover, Fstab, 'inOut'],
        [tStab2 + 0.3, Fstab], [tShow0 + 0.1, Fsmug, 'inOut'], [tShow1 + 0.4, Fsmug], [tShow1 + 0.9, Fstorm, 'inOut'],
        [tLook0, Fstorm], [tLook0 + 0.15, Fguilt, 'out'], [tLook1 - 0.05, Fguilt], [tLook1 + 0.2, Fstorm, 'inOut']]);
      face.autoBlink = 1;
      // ---- head: chin jab on each word ("Way." "Too." "Intense."), head down over the phone while walking
      const jab = 0.11 * (bump(t, tWay - 0.02, 0.2) + bump(t, tToo - 0.02, 0.2) + 1.2 * bump(t, tInt - 0.02, 0.24));
      const read = ramp(t, tGo - 0.2, tGo + 0.3);
      const lookBack = lookBackW(t);
      // ---- arms / phone
      const phoneUp = read * (1 - ramp(t, tShow0 - 0.2, tShow0 + 0.1)) * (1 - 0.5 * pulse(t, B3 - 0.35, cutD + 0.3, 0.25, 0.25)) + ramp(t, tShow1 + 0.2, tShow1 + 0.6) * (1 - lookBack);
      const show = ramp(t, tShow0, tShow0 + 0.35, (u) => 1 - Math.pow(1 - u, 3)) * (1 - ramp(t, tShow1, tShow1 + 0.35));
      const screen = t < tStab1 + 0.02 ? (t < B2 - 0.3 ? 'feed' : 'profile') : 'blocked';
      const tap = Math.max(bump(t, tStab1 - 0.04, 0.12), 0.85 * bump(t, tStab2 - 0.04, 0.12), 0.55 * bump(t, tInt + 0.1, 0.12), 0.5 * bump(t, tWay + 0.25, 0.1));
      const hov = clamp(ramp(t, tHover - 0.25, tHover) * (1 - ramp(t, cutD + 0.05, cutD + 0.3)));
      // hover trembling just BELOW the Block button (the label reads), each stab lands on its lower-left edge; then the
      // thumb drops clear to the bottom corner so "You blocked Jesus." reads
      const stabbing = Math.max(bump(t, tStab1 - 0.09, 0.2), bump(t, tStab2 - 0.09, 0.2));
      const clear = ramp(t, tStab2 + 0.05, tStab2 + 0.22);
      const trem = 1 - clear;
      const thumbAt = [lerp(lerp(0.42, 0.36, stabbing), 0.26, clear) + 0.006 * Math.sin(t * 47) * hov * trem, lerp(lerp(0.86, 0.69, stabbing), 0.97, clear) + 0.005 * Math.sin(t * 39 + 1) * hov * trem];
      let armL = sit > 0.4 ? { preset: 'hold' } : { preset: 'hold' };
      if (show > 0.001) armL = { preset: [['hold', Math.max(1e-3, 1 - show)], ['show', Math.max(1e-3, show)]] };
      // right hand: pushes off the ground (prop) during the scramble, swipes the backside twice, then stomps
      let armR = { preset: sit > 0.5 ? [['prop', Math.max(1e-3, ramp(t, tRise0 - 0.2, tRise0 + 0.2))], ['knee', Math.max(1e-3, 1 - ramp(t, tRise0 - 0.2, tRise0 + 0.2))]] : 'rest' };
      const sw1 = bump(t, tBr1 - 0.08, 0.26), sw2 = bump(t, tBr2 - 0.08, 0.26), swipe = Math.max(sw1, sw2);
      if (pass && (swipe > 0.001 || pulse(t, tBr1 - 0.2, tBr2 + 0.2, 0.12, 0.15) > 0.001)) {
        const hip = user.anchor('hip');
        if (hip) {
          const f = [Math.sin(yaw), 0, Math.cos(yaw)], rt = [-Math.cos(yaw), 0, Math.sin(yaw)];
          const env = pulse(t, tBr1 - 0.2, tBr2 + 0.2, 0.12, 0.15);
          const u = (t < tBr2 - 0.1 ? clamp((t - (tBr1 - 0.08)) / 0.26) : clamp((t - (tBr2 - 0.08)) / 0.26));
          const P = add(arr(hip), [-f[0] * 0.19 + rt[0] * 0.09, 0.02 - 0.2 * u, -f[2] * 0.19 + rt[2] * 0.09]);
          armR = { preset: 'rest', target: P, reach: env, palm: [f[0], -0.2, f[2]], fingers: [0, -1, 0], hand: { curl: 0.15, spread: 0.2, thumb: 0.3 } };
        }
      }
      // stomp: the free fist pumps (preset rest swings with the stomp); the phone hand reads
      return {
        pos: t < tGo ? POS.USEAT : pos, yaw,
        body: { sit, sitPath: 'rise', hunch: 0.25 + 0.15 * read, shrug: 0.25 * read + 0.12 * pulse(t, tRise0 - 0.3, tRise0 + 0.1, 0.12, 0.2) + 0.15 * pulse(t, B2, B2 + 2.0, 0.3, 0.4),
          lean: 0.04 * read, lookBack, breathe: 1.2 },
        walk: { amount: uAmt, phase: uPhase, style: 'stomp' },
        head: { pitch: 0.12 * read + jab - 0.18 * lookBack, yaw: 0, roll: 0, talk: 0.6 },
        gaze: pass ? (lookBack > 0.3 ? jE : (read > 0.5 && show < 0.5 ? phS : jE)) : null,
        face,
        blinkAt: [tRise0 - 0.05, tPiv1 - 0.1, tStab2 + 0.35, tLook0 + 0.05],
        armL, armR,
        extra: { phone: 0.85 + 0.25 * show, phoneUp: clamp(phoneUp), screen, tap: tap > 0.001 ? tap : undefined, thumb: Math.max(hov, tap > 0.001 ? 1 : 0),
          thumbAt: hov > 0.01 || tap > 0.001 ? thumbAt : undefined, hood: 1, glow: 1 + 0.6 * show },
      };
    };

    // ================================================================ VOID: still sulking at VSIT, back to everyone
    const vPose = () => {
      const perk = pulse(t, tDing + 0.05, tDing + 1.6, 0.25, 0.8);
      const listen = ramp(t, B6 + 0.4, B6 + 1.4) ;
      return {
        pos: POS.VSIT, yaw: YAW.VSIT,
        body: { sit: 1, slump: 0.4 - 0.08 * perk, breathe: 1.15, breathRate: 0.19 },
        head: { yaw: 0.1 * perk + 0.22 * listen, pitch: 0.26 - 0.1 * perk - 0.06 * listen, roll: 0 },
        armL: { preset: 'crossed' }, armR: { preset: 'crossed' },
        face: VX('sad', { lidU: 0.72 }),
      };
    };

    // ================================================================ cameras
    const cam = () => {
      const u = clamp((t - shotT0) / Math.max(0.01, shotT1 - shotT0));
      let s;
      switch (shot) {
        case 'WIDE': {   // low side two-shot (the s13 profile line, wider): user rises at left, storms toward the lens
          const a = EDGE.at([-1.42, 0.92, 5.2], [-0.98, 0.84, 1.05], 36, { drift: 0.2 });
          const b = EDGE.at([-1.5, 1.0, 5.32], [-1.12, 1.0, 1.15], 36, { drift: 0.2 });
          s = { ...a, pos: a.pos.map((x, i) => lerp(x, b.pos[i], smooth(u))), look: a.look.map((x, i) => lerp(x, b.look[i], smooth(u))) };
          break;
        }
        case 'TRACK': {  // ahead of the user on the path, dollying back with them; Jesus small behind, screen-right
          const ahead = pathPose(set, sU + dist + 2.3, 1.15);
          s = aim(add(ahead.pos, [0, 1.15, 0]), add(uWalk.pos, [0, 1.34, 0]), 400, 40, { drift: 0.15 });
          break;
        }
        case 'OVER': {   // over Jesus's RIGHT shoulder, looking down the path after the user
          const fw = SV(...FWD_K), rt = SV(-Math.cos(KY), 0, Math.sin(KY));
          const head = SW(...JEYE);
          const p = add(head, [-fw[0] * 1.45 + rt[0] * 0.42, 0.2, -fw[2] * 1.45 + rt[2] * 0.42]);
          const tgt = add(uWalk.pos, [0, 1.1, 0]);
          const L = lerpA(add(head, [fw[0] * 4, 0.1, fw[2] * 4]), tgt, 0.6);
          s = aimXY(p, L, 405, 500, 40, { drift: 0.12 });
          break;
        }
        case 'JST': s = EDGE.shot(JEYE, { dist: 1.5, yaw: -30, pitch: -10, fov: 34, screenY: sy(390), drift: 0.15 }); break;
        case 'RISE': {   // long lens over Jesus's shoulder toward the sun: the user tiny on the crest of the rise
          const fw = SV(...FWD_K), rt = SV(-Math.cos(KY), 0, Math.sin(KY));
          const head = SW(...JEYE);
          const p = add(head, [-fw[0] * 0.9 + rt[0] * 0.3, -0.42, -fw[2] * 0.9 + rt[2] * 0.3]);
          const R = set.pathAt(sRise).pos;
          s = aimXY(p, [R[0], R[1] + 0.9, R[2]], 400, 560, 21, { drift: 0.05 });
          break;
        }
        default: s = EDGE.cam('MASTER');
      }
      applyShot(app.camera, s, t, 14);
    };

    const insertCam = () => {
      if (shot === 'UINS') {
        const ph = user.anchor('phoneScreen');
        user.phone.updateWorldMatrix(true, false);
        const n = V3(0, 0, 1).transformDirection(user.phone.matrixWorld), up = V3(0, 1, 0).transformDirection(user.phone.matrixWorld);
        const xr = V3(1, 0, 0).transformDirection(user.phone.matrixWorld);
        const cp = ph.clone().addScaledVector(n, 0.2).addScaledVector(up, -0.025).addScaledVector(xr, -0.04);
        const look = ph.clone().addScaledVector(up, -0.012);
        applyShot(app.camera, { pos: cp.toArray(), look: look.toArray(), fov: 50, drift: 0, roll: rollFor(cp, look, up) }, t, 14);
      } else if (shot === 'JINS') {
        const P = phone.update(jesus, { show: 1, glow: 1, up: [0, 1, 0], slide: 0 });
        if (P) {
          const card = P.center.clone().addScaledVector(P.up, -0.004);
          const cp = card.clone().addScaledVector(P.normal, 0.235).addScaledVector(P.up, -0.012);
          const s = aim(cp, card, 520, 30, { drift: 0 });
          applyShot(app.camera, { ...s, roll: rollFor(cp, toV(s.look), P.up) }, t, 14);
        }
      }
    };

    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t), voidPos: POS.VSIT,
      sunGlow: shot === 'RISE' ? 0.85 : shot === 'TRACK' ? 0.8 : shot === 'OVER' ? 0.6 : 1, sunShift: shot === 'OVER' ? 0.13 : 0,
      shadowAt: shot === 'RISE' ? lerpA([0, 0, 0], uWalk.pos, 0.5) : [0, 0, 0],
      clear: [[POS.U[0], POS.U[2], 0.9], [POS.VSIT[0], POS.VSIT[2], 1.4], [POS.K[0], POS.K[2], 0.7]],
    });
    solve(t, [[vd, vPose], [user, uPose], [jesus, jPose]], cam);
    // Jesus's phone: tucked in the sash until he pulls it out; back in at the tuck
    const showPh = t >= tPull0 + 0.06 && t < tTuck1 - 0.04;
    phone.update(jesus, { show: showPh ? 1 : 0, glow: 1, up: [0, 1, 0], slide: 0 });
    insertCam();

    // the ding: a warm little glint at the sash
    const dg = bump(t, tDing - 0.02, 0.45);
    const ch = jesus.anchor('chest');
    ding.material.opacity = 0.55 * dg;
    if (ch) { const fwd = SV(...FWD_K), rtw = SV(-Math.cos(KY), 0, Math.sin(KY)); ding.position.copy(ch).add(V3(rtw[0] * 0.09 + fwd[0] * 0.06, -0.12, rtw[2] * 0.09 + fwd[2] * 0.06)); }
    ding.visible = dg > 0.001;

    fx.begin();
    drawSkyGalaxy(fx, t);
    fx.end();
    gal.userData.update(t);
    st.look = lookFor('s14', set.look);
  },
};

function lerpA(a, b, u) { const A = arr(a), B = arr(b); return [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u]; }
