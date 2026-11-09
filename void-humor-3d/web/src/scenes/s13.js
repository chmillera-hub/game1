// s13 talk_to_me — the heart of Part One. Jesus kneels to the user's level and offers something real: not the
// Void, just them. Every lean-in is met by a lean-back of exactly the same angle (the stacked two-shot shows it);
// the walls come down an inch (the phone turns face-down in the lap and its cold glow leaves the face, glistening
// eyes, a palm over the heart, a tear), a true sentence starts ("I just...") and the reaching hand stalls mid-air,
// sinks, the thumb turns the phone face-up, the glow comes back — "Nope." — and one hand yanks the hood strings.
// Jesus's hopeful smile slowly gives up.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { UX, headShake } from '../chars/user.js';
import { EDGE, todAt, voidSkyAt, sy, lookFor } from './marks.js';
import { loadLines, W, POS, YAW, SW, SV, add, arr, own, stamp, drawSkyGalaxy, makeLittleGalaxy, solve, pulse, walkPath } from './kit_s11_13.js';

const M = EDGE.M;
const KP = M.K.p, KY = M.K.yaw;
const FWD_K = [Math.sin(KY), 0, Math.cos(KY)];                     // Jesus's facing at K (stage-local)
const LEFT_K = [Math.cos(KY), 0, -Math.sin(KY)];                   // his left (stage-local)
// steady look points (stage-local; measured on the rigs): Jesus's eyes kneeling at K, the seated user's eyes at
// lean 0.30 (sitting up, hunched toward the lap) — the lean-back moves them along UB (see uEyeL)
const JEYE = [-0.75, 1.11, 0.80];
const UEYE = [-1.381, 0.70, 1.495];
const UB = [-Math.sin(M.U.yaw), 0, -Math.cos(M.U.yaw)];             // the user's "backward" (stage-local)
const uEyeL = (lean) => { const b = 0.30 - lean; return [UEYE[0] + UB[0] * 0.44 * b, UEYE[1] + 0.065 * b, UEYE[2] + UB[2] * 0.44 * b]; };
const LINE_YAW = Math.atan2(JEYE[0] - UEYE[0], JEYE[2] - UEYE[2]);  // user -> Jesus (stage-local, rad)
const PERP_DEG = (LINE_YAW - Math.PI / 2) / (Math.PI / 180);         // the pure-profile camera yaw (downstage-right side)
// Jesus's last steps: the time cheat across the cut (STAGING s12->s13): mid-walk at (-0.1, 0.55) -> K
const WALK = [[0.12, 0, 0.47], [-0.1, 0, 0.55], [-0.38, 0, 0.64], KP];

// ------------------------------------------------------------------------------------------------ small vector kit
const V3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const nrm = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const mix = (a, b, u) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
const sc = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
const sum = (...vs) => vs.reduce((o, v) => [o[0] + v[0], o[1] + v[1], o[2] + v[2]], [0, 0, 0]);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
/** rotate v about the unit axis a by angle th (Rodrigues) */
const rot = (v, a, th) => { const c = Math.cos(th), s = Math.sin(th), d = dot(a, v), x = cross(a, v); return [v[0] * c + x[0] * s + a[0] * d * (1 - c), v[1] * c + x[1] * s + a[1] * d * (1 - c), v[2] * c + x[2] * s + a[2] * d * (1 - c)]; };
const _m = new THREE.Matrix4(), _v = new THREE.Vector3();
/** world frame of an Object3D: [pos, +X, +Y, +Z] */
function frameOf(o) {
  o.updateWorldMatrix(true, false); _m.copy(o.matrixWorld);
  const p = _v.setFromMatrixPosition(_m).toArray();
  const ax = (i) => nrm(new THREE.Vector3().setFromMatrixColumn(_m, i).toArray());
  return [p, ax(0), ax(1), ax(2)];
}
/** the seated user's body frame (world) from anchors: left, up, fwd, chest, collar */
function bodyFrame(u) {
  const sl = u.anchor('shoulderL'), sr = u.anchor('shoulderR'), ch = u.anchor('chest'), hd = u.anchor('head');
  if (!sl || !sr || !ch || !hd) return null;
  const left = nrm([sl.x - sr.x, sl.y - sr.y, sl.z - sr.z]);
  let up = [hd.x - ch.x, hd.y - ch.y, hd.z - ch.z];
  up = nrm(sum(up, sc(left, -dot(up, left))));
  const fwd = nrm(cross(left, up));
  const mid = [(sl.x + sr.x) / 2, (sl.y + sr.y) / 2, (sl.z + sr.z) / 2];
  return { left, up, fwd, chest: arr(ch), mid };
}

export default {
  id: 's13',
  async setup(app) {
    await loadLines();
    const set = await app.set('EDGE');
    const [jesus, vd, user] = await Promise.all([app.char('JESUS'), app.char('VOID'), app.char('USER')]);
    const fx = new Particles({ max: 32, intensity: 1.5 });
    own(fx.mesh, 's13');
    const gal = makeLittleGalaxy();
    return { scene: set.scene, set, jesus, vd, user, fx, gal, look: lookFor('s13', set.look) };
  },

  async update(t, app, st) {
    stamp(t, 's13');
    const { set, jesus, vd, user, fx, gal } = st;
    for (const o of [jesus.root, vd.root, user.root, fx.mesh, gal]) st.scene.add(o);

    // ================================================================ timing (beats + words)
    const S = T('s13');
    const tArrive = S + 0.5, tKneel0 = S + 0.28, tKneel1 = tKneel0 + 0.95;
    const tHey = T('s13b02'), tOkay = W('s13b02', "it's", { frac: 0.6 });
    const B03 = T('s13b03'), tDont = W('s13b03', "don't", { frac: 0.1 }), tTalk3 = W('s13b03', 'talk', { frac: 0.5 }), tVoid3 = W('s13b03', 'void', { frac: 0.75 });
    const tWasnt = T('s13b04'), tFair = T('s13b05');
    const tCrying = W('s13b09', 'crying', { frac: 0.1 }), tKnow = W('s13b09', 'know', { frac: 0.85 });
    const B10 = T('s13b10'), B10e = T('s13b10.end');
    const tMe = W('s13b06', 'me', { frac: 0.8 }), B06 = T('s13b06');
    const tVoid7 = W('s13b07', 'void', { frac: 0.75 }), B07 = T('s13b07');
    const tYou = W('s13b08', 'you', { frac: 0.55 }), B08 = T('s13b08');
    const tEmo1 = W('s13b11', 'emotions', { frac: 0.1 }), tFeel = W('s13b11', 'feeling', { frac: 0.7 }), B11 = T('s13b11');
    const B13 = T('s13b13'), tEmo2 = W('s13b13', 'emotions', { frac: 0.7 });
    const B14 = T('s13b14'), tMean = W('s13b14', 'meaningful', { frac: 0.35 });
    const B15 = T('s13b15'), tSound = W('s13b15', 'sound', { frac: 0.45 });
    const B18 = T('s13b18'), B12 = T('s13b12'), B16 = T('s13b16'), B17 = T('s13b17'), B19 = T('s13b19'), E = T('s13.end');
    const tFlipU = B16 + 0.8;                                            // the thumb turns the phone face-up (b16)
    const tPk = B10e - 0.6;                                              // b10's last cut: the Void peeks

    // ================================================================ shot list (cut times)
    const SHOTS = [
      [S, 'WIDE'], [tHey - 0.1, 'OTSK'], [tTalk3 - 0.06, 'OTSJ'], [tFair - 0.15, 'OTSK2'],
      [B10, 'OTSJL'], [B10 + 0.42, 'INS'], [B10 + 0.95, 'OTSJL'], [tPk, 'OTSKW'],                 // b10: the flicker
      [B06 + 0.05, 'PROF'], [tMe + 0.03, 'OTSJ'], [B07 - 0.08, 'PROF'], [B08 - 0.1, 'PUSHU'], [B13 - 0.15, 'JST'], [B14 - 0.15, 'PROF'],
      [B15 - 0.15, 'JST'], [B12 - 0.1, 'OTSJ'], [B16, 'PROF'], [tFlipU - 0.08, 'INS'], [tFlipU + 0.38, 'OTSJL'], [B19, 'JST'],
    ];
    let si = 0; for (let i = 0; i < SHOTS.length; i++) if (t >= SHOTS[i][0]) si = i;
    const shotName = SHOTS[si][1], shotT0 = SHOTS[si][0], shotT1 = SHOTS[si + 1] ? SHOTS[si + 1][0] : E;

    // ================================================================ Jesus: last steps -> kneel (overshoot, settle)
    const wk = walkPath(t, WALK, S - 0.35, tArrive, { ta: 0.01, td: 0.42, stride: 1.05, phase0: 0.62, yaw1: KY, turn: 0.5 });
    const kneel = k(t, [[tKneel0, 0], [tKneel1, 1, 'inOut']]);
    const kneelDip = -0.022 * pulse(t, tKneel1 - 0.12, tKneel1 + 0.34, 0.1, 0.24);   // lands a touch deep, settles

    // ================================================================ the lean gag (same ANGLE, the user ~3 frames late)
    // Jesus leans in (#1 "me", #2 "you", #3 "emotions!", #4 a little on "meaningful"); the user, sitting up and hunched
    // over the face-down phone (lean 0.30), leans back by exactly the same angle each time.
    const L1 = 0.16, L2 = 0.12, L3 = 0.12, L4 = 0.07;
    const leanKeys = (o, lag) => [['s13', o], [B06 + 0.1 + lag, o], [B06 + 0.45 + lag, o + L1 * 1.06, 'out'], [B06 + 0.65 + lag, o + L1, 'inOut'],
      [B08 + 0.05 + lag, o + L1], [B08 + 0.38 + lag, o + (L1 + L2) * 1.03, 'out'], [B08 + 0.55 + lag, o + L1 + L2, 'inOut'],
      [B13 + 0.15 + lag, o + L1 + L2], [B13 + 0.5 + lag, o + (L1 + L2 + L3) * 1.03, 'out'], [B13 + 0.65 + lag, o + L1 + L2 + L3, 'inOut'],
      [tMean - 0.15 + lag, o + L1 + L2 + L3], [tMean + 0.2 + lag, o + L1 + L2 + L3 + L4, 'inOut']];
    const jLean = k(t, [...leanKeys(0.03, 0), [B18 + 0.05, 0.03 + L1 + L2 + L3 + L4], [B18 + 0.75, 0.06, 'inOut']]);
    const LAG = 0.125;
    const uBackOf = (tt) => k(tt, leanKeys(0, LAG));
    const uBackLean = uBackOf(t);
    // the user's own forward lean: wary (0.12) -> hunched over the lap for the phone (0.30) -> minus the lean-backs;
    // forward with the "I just..." reach; back with the sink; hunched over the phone for "Nope."
    const uBaseAt = (tt) => k(tt, [['s13', 0.1], [tKneel0 + 0.05, 0.1], [tKneel0 + 0.45, -0.02, 'out'], [tHey + 0.4, -0.02], [tHey + 1.2, 0.12, 'inOut'],
      [B10 + 0.1, 0.12], [B10 + 0.6, 0.30, 'inOut'],
      [B12 + 0.05, 0.30], [B12 + 0.4, 0.38, 'inOut'], [B16 + 0.2, 0.38], [B16 + 0.8, 0.30, 'inOut'], [B17 + 0.1, 0.30], [B17 + 0.5, 0.40, 'inOut']]);
    const uLeanAt = (tt) => uBaseAt(tt) - uBackOf(tt) + k(tt, [[B16 + 0.8, 0], [B17 + 0.5, uBackOf(B16 + 0.8) * 0.6, 'inOut']]);
    const uBase = uBaseAt(t), uLean = uLeanAt(t);

    // ================================================================ JESUS pose
    const jPose = (pass) => {
      const ue = user.anchor('eyes');
      const uE = ue ? arr(ue) : SW(...UEYE);
      const uPh = user.anchor('phone');
      const ph = uPh ? arr(uPh) : SW(-1.25, 0.45, 1.3);
      // ---- face
      const Fkind = JX('kind', { mSmile: 0.22, lidU: 0.9 });
      const Ften = JX('tender', { mSmile: 0.26, browIn: 0.5, lidU: 0.86 });
      const Flist = JX('listening', { mSmile: 0.2, browIn: 0.4 });
      const Famu = JX('amused', { mSmile: 0.6, lidL: 0.55, lidU: 0.72 });
      const Fcomp = JX('compassion', { mSmile: 0.12, browIn: 0.78, lidU: 0.88, wet: 0.3 });
      const Fenc = JX('tender', { mSmile: 0.3, mPress: 0.2, browIn: 0.55, lidU: 0.9, wet: 0.3 });
      const Fhope = JX('hopeful', { mSmile: 0.45, browIn: 0.6, browOut: 0.38 });
      const Fwarm = JX('warm', { mSmile: 0.55, browIn: 0.4 });
      const Feager = JX('eager', { mSmile: 1, lidU: 1.22, wet: 0.7 });
      const Fglow = JX('beam', { mSmile: 0.85, lidL: 0.55, lidU: 0.8, wet: 0.65, browIn: 0.5 });
      const Fbig = JX('eager', { mSmile: 1, mOpen: 0.3, mTeethU: 1, mTeethL: 0.45, browIn: 0.85, browOut: 0.75, lidU: 1.25, lidL: 0.22, wet: 0.6, pupil: 1.25 });
      const Fwait = JX('eager', { mSmile: 0.95, mOpen: 0.22, mTeethU: 1, mTeethL: 0.3, browIn: 0.7, browOut: 0.6, lidU: 1.16, lidL: 0.25, wet: 0.5 });
      const Fgo = JX('hopeful', { mSmile: 0.8, mOpen: 0.14, mTeethU: 1, browIn: 0.75, browOut: 0.55, lidU: 1.12, wet: 0.5 });
      // b19: the hopeful smile gives up — outer brows sink, inner stay a touch up, smile shrinks to closed lips;
      // soft (not heavy) lids, nearly symmetric (no smirk)
      const Fdim = JX('hopeful', { mSmile: 0.5, mOpen: 0.03, mTeethU: 0.3, browIn: 0.62, browOut: 0.22, lidU: 1.0, wet: 0.45 });
      const Fgive = JX('kind', { mSmile: 0.2, mPress: 0.5, mAsym: 0.06, mWide: -0.05, browIn: 0.5, browOut: -0.16, browAsym: 0, lidU: 0.9, lidL: 0.16, lidSad: 0.22, wet: 0.4 });
      const face = k(t, [
        ['s13', Fkind], [tKneel0, Fkind], [tKneel1, Ften, 'inOut'],
        [tWasnt + 0.3, Ften], [tWasnt + 0.7, Flist, 'inOut'],
        [tFair - 0.08, Flist], [tFair + 0.08, Famu, 'out'], [tFair + 0.5, Famu],
        [tCrying - 0.3, Famu], [tCrying + 0.1, Fcomp, 'inOut'],
        [B10, Fcomp], [B10 + 0.6, Fenc, 'inOut'],
        [B06, Fenc], [B06 + 0.4, Fhope, 'inOut'], [B07 + 0.2, Fhope], [B07 + 0.6, Fwarm, 'inOut'],
        [B08, Fwarm], [tYou, Ften, 'inOut'], [B11, Ften], [tEmo1, Fwarm, 'inOut'], [tFeel, Ften, 'inOut'],
        [B13, Ften], [B13 + 0.4, Feager, 'out'],
        [B14, Feager], [tMean, Fglow, 'inOut'],
        [B15 - 0.1, Fglow], [B15 + 0.3, Fbig, 'out'],
        [B18 + 0.1, Fbig], [B18 + 0.6, Fwait, 'inOut'],
        [B12 + 0.1, Fwait], [B12 + 0.5, Fgo, 'inOut'],
        [B19 + 0.1, Fgo], [B19 + 0.4, Fdim, 'inOut'], [B19 + 0.85, Fgive, 'inOut'],
      ]);
      // the nose-laugh on "Fair." (eye crinkle)
      const snort = pulse(t, tFair - 0.02, tFair + 0.35, 0.06, 0.25);
      face.lidL += 0.35 * snort; face.mSmile += 0.2 * snort;
      face.autoBlink = (shotName === 'JST' || shotName === 'OTSK' || shotName === 'OTSK2') ? 0 : 1;
      // ---- gaze: on the user's eyes; a slight nod down toward the phone on "you know"
      const gPh = add(ph, [0, 0.02, 0]);
      let gaze = k(t, [['s13', uE], [tCrying + 1.0, uE], [tCrying + 1.25, gPh, 'inOut'], [tKnow + 0.25, gPh], [tKnow + 0.5, uE, 'inOut']]);
      // in his close-ups the eyeline is cheated toward the lens (the camera sits just beside the user's head)
      if (pass && shotName === 'JST') { const c = app.camera.position; gaze = mix(gaze, [c.x, c.y, c.z], 0.6); }
      // ---- head: small "no" shake on "don't have to" (OTSK), concession nod on "Fair", nods, 'go on', 'mm'
      const shake = 0.075 * Math.sin(2 * Math.PI * 2.3 * (t - tDont)) * pulse(t, tDont - 0.02, tDont + 0.72, 0.12, 0.22);
      const nods = 0.12 * pulse(t, tFair + 0.05, tFair + 0.55, 0.18, 0.3)
        + 0.1 * pulse(t, tKnow - 0.35, tKnow + 0.45, 0.25, 0.4)
        + 0.13 * pulse(t, tMean + 0.05, tMean + 1.0, 0.4, 0.45)
        + 0.08 * pulse(t, tSound - 0.25, tSound + 0.05, 0.12, 0.14) + 0.08 * pulse(t, tSound + 0.1, tSound + 0.42, 0.12, 0.16)
        + 0.07 * pulse(t, B16 + 0.2, B16 + 0.8, 0.22, 0.3)
        + 0.06 * pulse(t, B19 + 0.62, B19 + 1.12, 0.2, 0.26);
      const tilt = k(t, [['s13', 0], [tKneel1, 0.06], [B06 + 0.3, 0.06], [B06 + 0.7, 0.1, 'inOut'], [B13, 0.08], [B13 + 0.5, 0.02, 'inOut'], [B15, 0.02], [B15 + 0.4, 0.08, 'inOut'], [B19, 0.08], [B19 + 0.8, 0.03, 'inOut']]);
      // ---- arms. Gestures with the LEFT hand (the camera side of the stacked two-shot); the right rests on the thigh.
      const open = smooth(clamp((t - (tKneel0 + 0.4)) / 0.6));
      const heart1 = pulse(t, tMe - 0.28, B07 + 0.12, 0.26, 0.4);             // fingertips to his chest on "me"
      const flick = pulse(t, tVoid7 - 0.32, tVoid7 + 0.42, 0.2, 0.3);          // a small backward flick toward the Void
      const offer = pulse(t, tYou - 0.35, B11 + 1.6, 0.35, 0.5);               // open palm toward them on "you"
      const clasp = pulse(t, B13 + 0.15, B14 + 0.25, 0.3, 0.3);                // hands clasped at the chest
      const heart2 = pulse(t, tMean - 0.22, B15 + 0.1, 0.2, 0.35);             // hand on his heart on "meaningful"
      // over-the-shoulder shots onto the user: the near (left) hand rests low on the knee, out of the frame
      const lowL = shotName === 'OTSJ' || shotName === 'OTSJL' ? 1 : 0;
      const kneeL = shotName === 'WIDE' ? 0.35 : 0;                          // the wide: forearm on the raised knee
      const g = Math.max(0, 1 - heart1 - offer - clasp - heart2);
      const prL = [['knee_rest', Math.max(0.001, (0.65 + kneeL) * g * (1 - lowL))], ['rest', g * lowL], ['open', (0.35 - kneeL) * g * (1 - lowL)], ['heart', heart1 + heart2], ['offer', offer * 0.85], ['clasp_chest', clasp]];
      const armL = { preset: flick > 0.001 ? [...prL.map(([n, w]) => [n, w * (1 - 0.7 * flick)]), ['explain', 0.7 * flick + 1e-3]] : prL, reach: open, hand: { splay: 0.05, cup: 0.4 } };
      const shL = jesus.anchor('shoulderL'), hl = jesus.anchor('handL');
      if (pass && flick > 0.001 && shL && hl) {
        // a small dismissive back-hand flick in front of his chest (never near the head): the hand rises to chest height,
        // then the wrist snaps the fingers back toward the Void behind him — "not that, never mind that"
        const back = SV(-FWD_K[0], 0, -FWD_K[2]), lft = SV(...LEFT_K), fwdW = SV(...FWD_K);
        const ch = jesus.anchor('chest');
        const tgt = ch ? add(arr(ch), [fwdW[0] * 0.22 + lft[0] * 0.2, -0.16, fwdW[2] * 0.22 + lft[2] * 0.2]) : add(arr(shL), [0, -0.3, 0]);
        armL.offset = [(tgt[0] - hl.x) * flick, (tgt[1] - hl.y) * flick, (tgt[2] - hl.z) * flick];
        const fl = pulse(t, tVoid7 - 0.06, tVoid7 + 0.3, 0.08, 0.18);           // the wrist snap itself
        // palm down, the fingers brush from forward to back past his left hip toward the Void: a brush-off
        armL.palm = nrm(sum([0, -0.85, 0], sc(back, 0.25 + 0.3 * fl), sc(lft, -0.2)));
        armL.fingers = nrm(sum(sc(lft, 0.75), sc(fwdW, 0.55 - 1.1 * fl), [0, 0.08, 0]));
        armL.hand = { curl: 0.18, spread: 0.25, thumb: 0.6, cup: 0.15 };
      }
      const armR = { preset: [['open', Math.max(0.001, (1 - clasp) * (1 - 0.6 * lowL))], ['knee_rest', 0.6 * lowL * (1 - clasp) + 1e-3], ['clasp_chest', clasp]], reach: open, hand: { splay: 0.06, cup: 0.4 } };
      const settle = pulse(t, B18 + 0.05, B18 + 1.6, 0.6, 0.6);
      return {
        pos: wk.amount > 0.001 || t < tArrive ? wk.pos : EDGE.W(KP), yaw: t < tArrive + 0.1 ? wk.yaw : EDGE.Y(KY),
        walk: { amount: wk.amount, phase: wk.phase, style: 'walk' },
        body: { kneel, lean: jLean + 0.05 * kneel, tilt: 0, shrug: 0.06 * pulse(t, tFair - 0.02, tFair + 0.3, 0.05, 0.2), bounce: -0.01 * settle + kneelDip,
          breathe: shotName === 'JST' ? 0.8 : 1, sway: kneel > 0.9 ? 0.5 : 1 },
        head: { follow: k(t, [['s13', 0.3], [tKneel1, 0.55]]), pitch: nods, yaw: shake, roll: -tilt, talk: 0.7 },
        gaze: pass ? gaze : null,
        face,
        blinkAt: [tKneel1 - 0.1, tOkay - 0.3, tCrying - 0.35, B10 + 0.75, B06 + 0.05, tYou + 0.5, B13 + 0.05, B18 + 0.45, B16 + 0.1, B19 + 0.3],
        armL, armR,
        glow: 1 + 0.25 * smooth(clamp((t - tMean) / 0.5)) * (1 - smooth(clamp((t - B15 - 0.3) / 0.8))),
      };
    };

    // ================================================================ USER pose
    // arm keys (time-ordered): [t, dur, state]; state = preset name | 'heart' | 'reach' | 'onphone' | 'strings' | 'pull'
    const R_KEYS = [
      [-1e9, 0, 'crossed'],
      [B10 + 0.05, 0.5, 'knee'],                  // arms loosen: the right hand drops onto the knee
      [B06 + 0.12, 0.42, 'prop'],                 // lean-back #1: the right hand plants behind the hip
      [B07 + 0.35, 0.65, 'onphone'],              // both hands on the face-down phone, a thumb rubbing its edge
      [tYou + 0.02, 0.6, 'heart'],                // palm flat over the heart
      [B12 + 0.06, 0.42, 'reach'],                // "I just..." reaches toward him, stalls
      [B16 + 0.12, 0.7, 'onphone'],               // the hand sinks back to the lap on its own
      [B17 + 0.12, 0.2, 'strings'],               // grabs both strings at the collar
      [B17 + 0.36, 0.15, 'pull'],                 // yanks them down and out
      [B19 + 0.25, 0.6, 'knee'],
    ];
    let ri = 0; for (let i = 0; i < R_KEYS.length; i++) if (t >= R_KEYS[i][0]) ri = i;
    const rFrom = ri > 0 ? R_KEYS[ri - 1][2] : R_KEYS[0][2], rTo = R_KEYS[ri][2];
    const rU = ri > 0 ? smooth(clamp((t - R_KEYS[ri][0]) / Math.max(1e-3, R_KEYS[ri][1]))) : 1;
    const PRESETS = new Set(['crossed', 'knee', 'prop', 'lap', 'rest']);
    // phone hand: crossed -> lap (screen up, lit) -> face-down -> (b16) face-up -> held
    const loosen = smooth(clamp((t - (B10 + 0.05)) / 0.45));
    const flipD = smooth(clamp((t - (B10 + 0.52)) / 0.32));
    const flipUp = smooth(clamp((t - tFlipU) / 0.3));
    const flip = flipD * (1 - flipUp);                                        // 0 screen up .. 1 face-down
    const phoneLvl = 0.85 * (1 - smooth(clamp((flip - 0.3) / 0.45)));
    const holdUp = smooth(clamp((t - (tFlipU + 0.4)) / 0.5));                  // after the flip: phone lifts to reading
    const lapW = smooth(clamp((t - (B10 + 0.18)) / 0.32)) * (1 - holdUp);       // world lap pose over the preset
    // the phone lying on the thighs: top pointing away from the user, screen tilted up toward their face; `fl` turns
    // it over about its long axis (toward the user's right = the camera side of the OTS-J angles) and lifts it a touch
    const lapPose = (bf, fl) => {
      const hp = user.anchor('hip'), ey = user.anchor('eyes');
      const fwdH = [Math.sin(YAW.U), 0, Math.cos(YAW.U)], leftH = [Math.cos(YAW.U), 0, -Math.sin(YAW.U)];
      let pos = sum(arr(hp), sc(fwdH, 0.25), [0, 0.105, 0], sc(leftH, 0.03));
      const top = nrm(sum(sc(fwdH, 0.95), [0, 0.12, 0], sc(leftH, 0.12)));
      const toE = nrm([ey.x - pos[0], ey.y - pos[1], ey.z - pos[2]]);
      let n0 = nrm(sum([0, 0.55, 0], sc(toE, 0.45)));
      n0 = nrm(sum(n0, sc(top, -dot(n0, top))));
      const sg = dot(rot(n0, top, Math.PI / 2), leftH) > 0 ? -1 : 1;           // turn toward the user's right
      const n = rot(n0, top, sg * Math.PI * fl);
      pos = sum(pos, [0, 0.05 * Math.sin(Math.PI * fl) + 0.012 * fl, 0]);
      return { pos, top, n };
    };
    const uPose = (pass) => {
      const je = jesus.anchor('eyes');
      const jE = je ? arr(je) : SW(...JEYE);
      const jhL = jesus.anchor('handL'), jhR = jesus.anchor('handR');
      const jHands = jhL && jhR ? [(jhL.x + jhR.x) / 2, (jhL.y + jhR.y) / 2, (jhL.z + jhR.z) / 2] : SW(KP[0], 0.7, KP[2]);
      const vb = vd.anchor('back');
      const vB = vb ? arr(vb) : SW(1.0, 1.5, -1.1);
      const bf = pass ? bodyFrame(user) : null;
      const LP = bf ? lapPose(bf, flip) : null;                               // where the phone lies in the lap
      const phs = user.anchor('phone');
      const phS = LP ? LP.pos : phs ? arr(phs) : SW(-1.2, 0.45, 1.3);
      const jl = SV(...LEFT_K);
      const eyeL = add(jE, sc(jl, 0.035)), eyeR = add(jE, sc(jl, -0.035)), mouth = add(jE, [0, -0.09, 0]);
      const aside = add(jE, [-jl[0] * 0.9, 0.35, -jl[2] * 0.9]);
      const gaze = k(t, [
        ['s13', jE], [tKneel0 + 0.3, jE], [tKneel0 + 0.42, jHands, 'out'], [tKneel1 - 0.15, jHands], [tKneel1 + 0.05, jE, 'inOut'],
        [tVoid3 - 0.55, jE], [tVoid3 - 0.45, vB, 'out'], [tVoid3 - 0.12, vB], [tVoid3 - 0.02, jE, 'out'],
        [tWasnt + 0.05, jE], [tWasnt + 0.3, aside, 'inOut'], [T('s13b04.end') - 0.05, aside], [T('s13b04.end') + 0.2, jE, 'inOut'],
        [B10 + 0.12, jE], [B10 + 0.24, phS, 'out'], [B10 + 0.86, phS], [B10 + 1.02, jE, 'inOut'],
        [tEmo1 + 0.45, jE], [tEmo1 + 0.5, eyeL, 'out'], [tEmo1 + 0.8, eyeL], [tEmo1 + 0.85, eyeR, 'out'], [tEmo1 + 1.1, eyeR], [tEmo1 + 1.16, mouth, 'out'], [tEmo1 + 1.4, mouth], [tEmo1 + 1.48, jE, 'out'],
        [B16 + 0.5, jE], [B16 + 0.62, phS, 'out'],
      ]);
      // ---- face
      const Fwary = UX([['suspicious', 0.45], ['idle', 0.55]], { glisten: 0, wet: 0.35 });
      const Fsusp = UX('suspicious', { wet: 0.5 });
      const Fsmirk = UX('smirk', { wet: 0.5 });
      const Fcaught = UX('idle', { lidU: 1.12, browIn: 0.45, mPress: 0.3, wet: 0.5 });
      const Ftrem = UX('tremble', { wet: 0.6, lidU: 1.06, lidSad: 0.3, lidL: 0.18 });
      const Fdawn = UX('dawning', { wet: 0.55 });
      const Fsoft = UX('soften', { wet: 0.6 });
      const Fsoft2 = UX([['soften', 0.6], ['tremble', 0.4]], { wet: 0.6 });
      const Fstall = UX([['tremble', 0.55], ['soften', 0.45]], { wet: 0.65, lidU: 1.12, lidSad: 0.22, lidL: 0.14, browIn: 0.7 });
      const Fwall = UX([['idle', 0.5], ['deadpan', 0.5]], { wet: 0.5, mPress: 0.5 });
      const Fnope = UX([['hellno', 0.45], ['deadpan', 0.55]], { wet: 0.5 });
      const face = k(t, [
        ['s13', Fwary], [tVoid3 - 0.1, Fwary], [tVoid3 + 0.15, Fsusp, 'inOut'],
        [tWasnt - 0.05, Fsusp], [tWasnt + 0.25, Fsmirk, 'inOut'], [T('s13b04.end') + 0.4, Fsmirk], [tFair + 0.2, Fwary, 'inOut'],
        [tCrying, Fwary], [tCrying + 0.25, Fcaught, 'out'],
        [B10 + 0.7, Fcaught], [B10 + 1.1, Ftrem, 'inOut'],
        [B06 + 0.2, Ftrem], [tMe + 0.05, Fdawn, 'inOut'],
        [B07 + 0.5, Fdawn], [B08, Fsoft2, 'inOut'], [tYou, Fsoft2], [tYou + 0.3, Fsoft, 'out'],
        [tEmo1 + 0.3, Fsoft], [tEmo1 + 0.7, Fstall, 'inOut'], [tFeel + 0.4, Fstall], [B13, Fsoft, 'inOut'],
        [B12 - 0.2, Fsoft], [B12, Fstall, 'inOut'],
        [B16 + 0.5, Fstall], [B16 + 1.1, Fwall, 'inOut'], [B17, Fwall], [B17 + 0.12, Fnope, 'out'],
      ]);
      // the b06 "...you?": a surprised double blink, brows lift, lips part
      const dawn = pulse(t, tMe - 0.05, B07 + 0.2, 0.18, 0.4);
      face.browIn += 0.18 * dawn; face.browOut += 0.14 * dawn; face.mOpen = Math.max(face.mOpen, 0.12 * dawn);
      // flinches (#1 on "emotions": 3-frame squeeze; #2 smaller), the swallow
      const sq1 = pulse(t, tEmo1, tEmo1 + 0.16, 0.03, 0.06), sq2 = pulse(t, tEmo2, tEmo2 + 0.12, 0.03, 0.05);
      const squeeze = Math.max(sq1, 0.55 * sq2);
      if (squeeze > 0) { const scr = UX('scrunch'); for (const kk of ['lidU', 'lidL', 'squint', 'browIn', 'browSq']) face[kk] = lerp(face[kk], scr[kk], squeeze); }
      const gulp = pulse(t, tFeel + 0.45, tFeel + 0.85, 0.1, 0.2);
      if (gulp > 0) { face.mPress = lerp(face.mPress, 0.95, gulp); face.mWide = lerp(face.mWide, -0.3, gulp); }
      // the flicker (b10): lips press, chin trembles
      const flick10 = pulse(t, B10 + 0.75, B06 + 0.4, 0.3, 0.4);
      face.mPress = Math.max(face.mPress, 0.6 * flick10); face.mTremble = Math.max(face.mTremble || 0, 0.7 * flick10);
      face.autoBlink = 1;
      const flinch = 0.6 * pulse(t, tEmo1 - 0.02, tEmo1 + 0.4, 0.08, 0.3) + 0.35 * pulse(t, tEmo2 - 0.02, tEmo2 + 0.32, 0.07, 0.25);
      const catches = 0.22 * pulse(t, tEmo1 + 0.55, tEmo1 + 0.8, 0.06, 0.18) + 0.22 * pulse(t, tEmo1 + 0.95, tEmo1 + 1.2, 0.06, 0.18);
      const sniff = 0.2 * pulse(t, tHey + 0.45, tHey + 0.75, 0.06, 0.2);
      const relief = k(t, [['s13', 0.3], [tDont + 0.3, 0.3], [tDont + 0.8, 0.22, 'inOut'], [B10, 0.22], [B10 + 0.4, 0.14, 'inOut']]);
      const uBack = k(t, [['s13', 0], [tKneel0 + 0.1, 0], [tKneel0 + 0.6, 0.5, 'inOut'], [tHey, 0.5], [tHey + 1.2, 0.1, 'inOut'], [B10, 0.1], [B10 + 0.5, 0, 'inOut']]);

      // ---- arms (world-space gestures blended over the pass-0 preset pose)
      const wrist0 = (side) => { const [p, , y, z] = frameOf(user.arms[side].hand.root); return { wrist: p, fing: y, palm: sc(z, -1) }; };
      const stateR = (name) => {
        if (PRESETS.has(name) || !bf) return null;
        const { left, up, fwd, chest } = bf;
        const right = sc(left, -1);
        if (name === 'heart') {
          // palm flat on the LEFT side of the chest, fingers angled across toward the left collarbone, beside the string
          const f = nrm(sum(sc(up, 0.62), sc(left, 0.78)));
          const palmC = sum(chest, sc(left, 0.075), sc(up, 0.025), sc(fwd, 0.028));
          return { wrist: sum(palmC, sc(f, -0.06), sc(fwd, 0.008)), palm: sc(fwd, -1), fing: f, pole: nrm(sum(sc(up, -1), sc(right, 0.7), sc(fwd, 0.15))),
            hand: { curl: 0.1, spread: 0.14, thumb: 0.35, cup: 0.18 } };
        }
        if (name === 'reach') {
          // forearm forward toward him at chest height, palm up, fingers loosely curled, wrist leading
          const toJ = nrm([jE[0] - chest[0], 0, jE[2] - chest[2]]);
          const st = pulse(t, B12 + 0.25, B16 + 0.2, 0.12, 0.3);             // the stall: a tiny pull back
          const wr = sum(chest, sc(toJ, 0.3 - 0.025 * st), sc(up, 0.03), sc(right, 0.06));
          return { wrist: wr, palm: [0, 1, 0], fing: nrm(sum(toJ, [0, 0.05, 0], sc(left, 0.2))), pole: nrm(sum(sc(up, -1), sc(right, 0.8))),
            hand: { curl: 0.34 + 0.08 * st, spread: 0.12, thumb: 0.5, cup: 0.4 } };
        }
        if (name === 'onphone') {
          // resting on the back of the face-down phone beside the left hand; the thumb rubs its edge
          // the right hand rests on the far half of the face-down phone (its dark back + coral edge stay visible
          // round it), fingertips over its far edge; the thumb rubs nervously along its side
          const L2 = lapPose(bf, 1);
          const rH = sc(nrm(cross(L2.top, [0, 1, 0])), -1);                    // the user's right, in the lap plane
          const f = nrm(sum(sc(L2.top, 0.55), sc(rH, -0.75), [0, -0.12, 0]));
          const rub = Math.sin(2 * Math.PI * 1.4 * t) * smooth(clamp((t - (B07 + 0.9)) / 0.4)) * (1 - smooth(clamp((t - (tYou - 0.2)) / 0.2)));
          const pc2 = sum(L2.pos, sc(L2.top, 0.045), sc(rH, 0.075), [0, 0.03, 0]);
          return { wrist: sum(pc2, sc(f, -0.065), sc(L2.top, 0.006 * rub)), palm: [0, -1, 0], fing: f, pole: nrm(sum(sc(right, 1), [0, -0.3, 0], sc(fwd, -0.3))),
            hand: { curl: 0.3, spread: 0.08, thumb: 0.5 + 0.3 * rub, cup: 0.3 } };
        }
        if (name === 'strings' || name === 'pull') {
          // grab both strings at the collar, then yank them down and out (the hood cinches)
          const collar = sum(bf.mid, sc(up, -0.13), sc(fwd, 0.09));
          const p = name === 'strings' ? sum(collar, sc(right, 0.025), sc(fwd, 0.03)) : sum(collar, sc(up, -0.26), sc(right, 0.1), sc(fwd, 0.1));
          const f = nrm(sum(sc(left, 1), sc(up, -0.25), sc(fwd, -0.1)));
          return { wrist: sum(p, sc(f, -0.05)), palm: sc(fwd, -1), fing: f, pole: nrm(sum(sc(right, 1), [0, -0.6, 0], sc(fwd, -0.2))),
            hand: { curl: 0.82, spread: 0.04, thumb: 0.6, cup: 0.3 } };
        }
        return null;
      };
      // right arm
      const presetOf = (n) => (PRESETS.has(n) ? n : n === 'onphone' ? 'lap' : 'rest');
      let armR;
      if (PRESETS.has(rFrom) && PRESETS.has(rTo)) armR = { preset: rU >= 1 ? rTo : [[rFrom, 1 - rU], [rTo, Math.max(1e-3, rU)]] };
      else {
        const basePreset = PRESETS.has(rFrom) ? rFrom : PRESETS.has(rTo) ? rTo : presetOf(rTo);
        armR = { preset: basePreset };
        if (pass) {
          const p0 = wrist0('R');
          const A = stateR(rFrom) || p0, B = stateR(rTo) || p0;
          armR = { preset: basePreset, target: mix(A.wrist, B.wrist, rU), palm: nrm(mix(A.palm, B.palm, rU)), fingers: nrm(mix(A.fing, B.fing, rU)),
            pole: A.pole && B.pole ? nrm(mix(A.pole, B.pole, rU)) : (B.pole || A.pole), hand: B.hand && A.hand ? Object.fromEntries(Object.keys(B.hand).map((kk) => [kk, lerp(A.hand[kk] ?? B.hand[kk], B.hand[kk], rU)])) : (B.hand || A.hand) };
        }
      }
      // left (phone) arm: crossed -> the phone flat on the thighs (screen up to the face, lit) -> it turns over about
      // its long axis, face-down (the cold glow leaves the face) -> (b16) face-up again -> lifted to reading
      let armL = { preset: holdUp > 0 ? [['lap', 1 - holdUp], ['hold', Math.max(1e-3, holdUp)]] : loosen < 1 ? [['crossed', 1 - loosen], ['lap', Math.max(1e-3, loosen)]] : 'lap' };
      if (pass && lapW > 0.001 && LP) {
        const [, , Y0, Z0] = frameOf(user.phone);
        const [wr0] = frameOf(user.arms.L.hand.root);
        const X1 = cross(LP.top, LP.n);
        const wr1 = sum(LP.pos, sc(X1, PH_OFF[0]), sc(LP.top, PH_OFF[1]), sc(LP.n, PH_OFF[2]));
        armL = { ...armL, grip: 'flat', target: mix(wr0, wr1, lapW), palm: nrm(mix(Z0, LP.n, lapW)), fingers: nrm(mix(Y0, LP.top, lapW)) };
      }
      const hs = headShake(t, B17 + 0.0, { count: 2, dur: 0.4, amp: 0.13 });
      const pull = pulse(t, B17 + 0.36, B17 + 0.75, 0.06, 0.3);
      return {
        pos: POS.USEAT, yaw: YAW.U,
        body: { sit: 1, sitPath: 'plain', hunch: relief, lean: uLean, recoil: uBack * 0.3, flinch, shrug: sniff + catches + 0.1 * pull, breathe: 1 + 0.4 * catches },
        head: { pitch: k(t, [['s13', 0.08], [B10 + 0.1, 0.08], [B10 + 0.35, 0.22, 'inOut'], [B10 + 0.9, 0.22], [B10 + 1.2, 0.08, 'inOut'],
          [B16 + 0.45, 0.08], [B16 + 0.75, 0.26, 'inOut'], [B17 + 0.5, 0.26], [B17 + 0.7, 0.32, 'out']]) + 0.06 * pull, yaw: hs.yaw, roll: 0 },
        gaze: pass ? gaze : null,
        face,
        blinkAt: [tKneel1 + 0.1, tCrying + 0.6, tMe + 0.1, tMe + 0.33, tYou + 0.2, B12 - 0.3, B16 + 0.58],
        armL, armR,
        extra: { phone: phoneLvl, screen: 'feed', glisten: k(t, [['s13', 0.25], [B10 + 0.8, 0.25], [B10 + 1.5, 0.55, 'inOut']]),
          tears: k(t, [['s13', 0], [tEmo1 + 0.6, 0], [tEmo1 + 1.8, 0.4, 'inOut']]), hairSwing: hs.hairSwing,
          hood: k(t, [[B17 + 0.36, 0], [B17 + 0.5, 0.6, 'out'], [B17 + 0.7, 1, 'out']]) },
      };
    };

    // ================================================================ VOID: back to upstage; peeks over its LEFT shoulder (b10 end)
    const back = smooth(clamp((t - (S - 0.1)) / (tArrive + 0.35 - S)));
    // the hood comes round mostly off-screen (it starts 0.5 s before the cut), arrives ~4 frames after it with a slow
    // ease-out, holds while the brow-wisps lift, then eases back over 0.8 s (seen soft at the edge of the two-shot)
    const peek = k(t, [[tPk - 0.5, 0], [tPk + 0.17, 1, 'inOut'], [B06 + 0.45, 1], [B06 + 1.25, 0, 'inOut']]);
    const vPose = (pass) => {
      const je = jesus.anchor('eyes');
      const Fsulk = VX('sad', { lidU: 0.72 }), Fgentle = VX('gentle', { lidU: 0.6, lidL: 0.48, mSmile: 0.55 });
      const Fpeek = VX('curious', { lidU: 1.18, browIn: 0.75, browOut: 0.55, mSmile: 0.1 });
      const face = k(t, [['s13', Fgentle], [S + 0.6, Fgentle], [S + 1.3, Fsulk, 'inOut'], [tPk - 0.2, Fsulk], [tPk + 0.2, Fpeek, 'out'], [B06 + 0.4, Fpeek], [B06 + 1.0, Fsulk, 'inOut']]);
      const lift = pulse(t, tPk + 0.18, tPk + 0.62, 0.12, 0.2);               // brow-wisps lift: is it working?
      face.browIn += 0.25 * lift; face.browOut += 0.2 * lift;
      face.autoBlink = 0;
      return {
        pos: POS.VSIT, yaw: YAW.VSIT,
        body: { sit: 1, slump: 0.4 - 0.06 * peek, twist: -0.35 * (1 - back) + PEEK_TWIST * peek, breathe: 1.15, breathRate: 0.19 },
        head: { yaw: -1.75 * (1 - back) + PEEK_YAW * peek, pitch: lerp(-0.04, 0.26, back) - 0.14 * peek, roll: -0.08 * (1 - back) + 0.05 * peek },
        armL: { preset: 'crossed' }, armR: { preset: 'crossed' },
        gaze: pass && peek > 0.05 && je ? arr(je) : null,
        face,
      };
    };

    // ================================================================ camera (framed between the passes)
    const UE_T = uEyeL(uLean);
    const profLook = (tt) => {
      const u = uEyeL(uLeanAt(tt)), Y = (PERP_DEG + PROF.rot) * Math.PI / 180;
      return [(JEYE[0] + u[0]) / 2 + Math.cos(Y) * PROF.shift, (JEYE[1] + u[1]) / 2 + PROF.dy, (JEYE[2] + u[2]) / 2 - Math.sin(Y) * PROF.shift];
    };
    const cam = () => {
      const u = clamp((t - shotT0) / Math.max(0.01, shotT1 - shotT0));
      let shot;
      switch (shotName) {
        case 'WIDE': shot = EDGE.shot(WIDE.look, { dist: lerp(WIDE.dist, WIDE.dist - 0.25, smooth(u)), yaw: WIDE.yaw, pitch: WIDE.pitch, fov: WIDE.fov, screenY: sy(WIDE.sy), drift: 0.3 }); break;
        case 'OTSK': shot = EDGE.shot(JEYE, { dist: 2.25, yaw: -30, pitch: 6, fov: 33, screenY: sy(400), drift: 0.2 }); break;
        case 'OTSK2': shot = EDGE.shot(JEYE, { dist: k(t, [[tFair, 2.2], [T('s13b09'), 2.15], [B10, 1.8, 'inOut']]), yaw: -28, pitch: 6, fov: 33, screenY: sy(400), drift: 0.2 }); break;
        case 'OTSKW': shot = EDGE.shot(JEYE, { dist: OTSKW.dist, yaw: OTSKW.yaw, pitch: OTSKW.pitch, fov: 44, screenY: sy(OTSKW.sy), drift: 0.15 }); break;
        case 'OTSJL': {
          // face + lap in one frame: the phone (lit screen -> the turn -> the dark back) and the glow on the chin
          const lk = sum(UE_T, [0, -OTSJL.drop, 0]);
          const dd = t < B16 ? k(t, [[B10, OTSJL.dist], [B10e - 0.62, OTSJL.dist - 0.12, 'inOut']]) : k(t, [[tFlipU - 0.12, OTSJL.dist], [B17 + 0.3, OTSJL.dist - 0.25, 'inOut']]);
          shot = EDGE.shot(lk, { dist: dd, yaw: OTSJL.yaw, pitch: OTSJL.pitch, fov: 33, screenY: sy(OTSJL.sy), drift: 0.15 });
          break;
        }
        case 'INS': {
          // insert: the user's own view down onto the lap — the lit feed, the turn, the dark coral back (and back again)
          const ey = user.anchor('eyes'), L0 = user.anchor('hip') ? lapPose(null, 0) : null;
          if (ey && L0) {
            const E3 = arr(ey), rH = [-Math.cos(YAW.U), 0, Math.sin(YAW.U)];
            const pos = sum(E3, sc(sum(L0.pos, sc(E3, -1)), INS.fwd), [0, INS.up, 0], sc(rH, INS.side));
            shot = { pos, look: sum(L0.pos, sc(L0.top, INS.ahead)), fov: INS.fov, drift: 0.05 };
          } else shot = EDGE.cam('MASTER');
          break;
        }
        case 'OTSJ': {
          // genuinely over his LEFT shoulder: his hair/shoulder a soft edge at frame-right, the user's face y~420
          const sh = jesus.anchor('shoulderL');
          const sL = sh ? EDGE.L(sh) : [KP[0] + 0.17 * LEFT_K[0], 0.95, KP[2] + 0.17 * LEFT_K[2]];
          const p = [sL[0] - FWD_K[0] * OTSJ.back + LEFT_K[0] * OTSJ.side, sL[1] + OTSJ.up, sL[2] - FWD_K[2] * OTSJ.back + LEFT_K[2] * OTSJ.side];
          const dl = Math.hypot(UE_T[0] - p[0], UE_T[1] - p[1], UE_T[2] - p[2]);
          shot = EDGE.at(p, [UE_T[0], UE_T[1] - dl * 0.102, UE_T[2]], 33, { drift: 0.15 });
          break;
        }
        case 'PROF': {
          // stacked two-shot (STAGING rule 3): the user near the lens lower-left (back 3/4), Jesus behind upper-right
          // (face + chest 3/4 to camera), the seated Void's back looming soft at the right. The look point is fixed
          // per shot (from the lean at the cut) so the lean gag reads against a locked frame.
          shot = EDGE.shot(profLook(shotT0), { dist: PROF.dist, yaw: PERP_DEG + PROF.rot, pitch: PROF.pitch, fov: PROF.fov, screenY: sy(PROF.sy), drift: 0.1 });
          break;
        }
        case 'PUSHU': {
          // a slow push from the side toward the user's face (Jesus's offered palm at the frame edge)
          const w = smooth(clamp((t - shotT0) / (B11 + 0.4 - shotT0)));
          shot = EDGE.shot(UE_T, { dist: lerp(PUSH.d0, PUSH.d1, w), yaw: lerp(PUSH.y0, PUSH.y1, w), pitch: PUSH.pitch, fov: 33, screenY: sy(lerp(470, 430, w)), drift: 0.12 });
          break;
        }
        case 'JST': {
          // on the K -> user-eye axis, at the user's eye height, just behind the user's head (their hair + glasses rim
          // a soft edge lower-left): his eyeline lands next to the lens
          const ue = uEyeL(uLeanAt(shotT0 + 0.7));
          const sideOff = shotT0 >= B19 ? JSTC.side + 0.12 : JSTC.side;    // the cinched hood is bigger: give it room
          const ax = nrm([ue[0] - JEYE[0], 0, ue[2] - JEYE[2]]);
          const sideV = [ax[2], 0, -ax[0]];                                    // screen-right of the axis (seen from the camera)
          const p = sum(ue, sc(ax, JSTC.back), sc(sideV, sideOff), [0, JSTC.up, 0]);
          const dl = Math.hypot(JEYE[0] - p[0], JEYE[1] - p[1], JEYE[2] - p[2]);
          const lk = sum(JEYE, [0, -dl * 0.111 + JSTC.dy, 0], sc(sideV, JSTC.lookSide));
          shot = EDGE.at(p, lk, 33, { drift: 0.1 });
          break;
        }
        default: shot = EDGE.cam('MASTER');
      }
      applyShot(app.camera, shot, t, 13);
    };

    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t), voidPos: POS.VSIT,
      sunGlow: shotName === 'OTSJ' || shotName === 'OTSJL' || shotName === 'PUSHU' ? 0.7 : 1,
      clear: CLEAR,
    });
    solve(t, [[vd, vPose], [user, uPose], [jesus, jPose]], cam);

    fx.begin();
    drawSkyGalaxy(fx, t);
    fx.end();
    gal.userData.update(t);
    st.look = lookFor('s13', set.look);
  },
};

// ------------------------------------------------------------------------------------------------ camera numbers
// (stage-local degrees / metres; tuned against the real rigs with stills)
const WIDE = { look: [-1.05, 0.72, 1.13], yaw: 22, pitch: 3, dist: 5.4, fov: 35, sy: 700 };
const OTSKW = { yaw: -36, pitch: 6, dist: 3.3, sy: 515 };
const OTSJL = { yaw: 97, pitch: 12, dist: 2.3, drop: 0.2, sy: 560 };
const OTSJ = { back: 0.45, side: 0.24, up: 0.3 };
const PROF = { rot: -66, pitch: 4, dist: 3.4, fov: 32, sy: 430, dy: 0.05, shift: -0.03 };
const PUSH = { y0: 100, y1: 106, d0: 2.4, d1: 1.35, pitch: 7 };
const JSTC = { back: 0.6, side: 0.36, up: 0.05, dy: 0, lookSide: 0 };
const PEEK_YAW = 1.38, PEEK_TWIST = 0.18;
const INS = { fwd: 0.22, up: 0.2, side: 0.2, ahead: 0.0, fov: 38 };
const PH_OFF = [-0.0434, -0.0461, -0.0227];                         // the wrist in the phone's frame (flat grip, measured)
const CLEAR = [[...EDGE.W(-1.3, 0, 1.4).filter((_, i) => i !== 1), 0.9], [...EDGE.W(1.15, 0, -1.35).filter((_, i) => i !== 1), 1.4], [...EDGE.W(-0.65, 0, 0.7).filter((_, i) => i !== 1), 0.7]];
