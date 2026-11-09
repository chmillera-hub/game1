// s13 talk_to_me — the heart of Part One. Jesus kneels to the user's level and offers something real: not the
// Void, just them. Every lean-in is met by a lean-back of exactly the same size (the profile two-shot shows it);
// the walls come down an inch (phone face-down, the cold glow leaves the face, glistening eyes, a hand on the
// chest, a tear), a true sentence starts ("I just...") and stalls, the hand sinks, the phone turns face-up, the
// glow comes back — "Nope." — and the hood strings get yanked. Jesus's hopeful smile slowly gives up.
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, noise1 } from '../core/util.js';
import { Particles } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { UX, headShake } from '../chars/user.js';
import { EDGE, todAt, voidSkyAt, sy, lookFor } from './marks.js';
import { loadLines, W, POS, YAW, SW, SV, add, arr, own, stamp, drawSkyGalaxy, makeLittleGalaxy, solve, pulse, walkPath } from './kit_s11_13.js';

const M = EDGE.M;
const KP = M.K.p, KY = M.K.yaw;
const FWD_K = [Math.sin(KY), 0, Math.cos(KY)];                     // Jesus's facing at K (stage-local)
// steady look points (stage-local; measured on the rigs): Jesus's eyes kneeling at K, the seated user's eyes
const JEYE = [KP[0] + 0.17 * FWD_K[0], 1.05, KP[2] + 0.17 * FWD_K[2]];
const UEYE = [-1.41, 0.72, 1.57];
const MID = [(JEYE[0] + UEYE[0]) / 2, (JEYE[1] + UEYE[1]) / 2 + 0.02, (JEYE[2] + UEYE[2]) / 2];
const PMID = [MID[0] + 0.04 * (JEYE[0] - UEYE[0]), MID[1] - 0.04, MID[2] + 0.04 * (JEYE[2] - UEYE[2])];
const LINE_YAW = Math.atan2(JEYE[0] - UEYE[0], JEYE[2] - UEYE[2]);  // user -> Jesus
const PERP_DEG = (LINE_YAW - Math.PI / 2) / (Math.PI / 180);         // camera on the downstage-right side
const PROF_ROT = 0;                                                   // favour the user's face (3/4), Jesus a 3/4 back

// no flowers between the profile camera and the pair (they read as giant blobs in the foreground)
const PROF_CLEAR = (() => {
  const c = EDGE.shot(PMID, { dist: 5.2, yaw: PERP_DEG + PROF_ROT, pitch: 3, fov: 33, screenY: sy(470) }).pos, m = EDGE.W(PMID);
  const at = (u) => [c[0] + (m[0] - c[0]) * u, c[2] + (m[2] - c[2]) * u];
  return [[...at(0.2), 1.3], [...at(0.45), 1.6], [...at(0.7), 1.5], [EDGE.W(-1.3, 0, 1.4)[0], EDGE.W(-1.3, 0, 1.4)[2], 0.9]];
})();
// Jesus's last steps: the time cheat across the cut (STAGING s12->s13): mid-walk -> K
const WALK = [[-0.02, 0, 0.5], [-0.35, 0, 0.62], KP];

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
    const tArrive = T('s13b01') + 0.32, tKneel0 = tArrive - 0.1, tKneel1 = tKneel0 + 1.15;
    const tHey = T('s13b02'), tOkay = W('s13b02', "it's", { frac: 0.6 });
    const tDont = W('s13b03', "don't", { frac: 0.1 }), tVoid3 = W('s13b03', 'void', { frac: 0.75 });
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

    // ================================================================ shot list (cut times)
    const SHOTS = [
      [S, 'WIDE'], [tHey - 0.25, 'OTSK'], [tDont - 0.25, 'OTSJ'], [tFair - 0.15, 'OTSK2'], [B10, 'OTSJL'],
      [B10e - 0.7, 'OTSKW'], [B06 - 0.1, 'PROF'], [B08 - 0.1, 'PUSHU'], [B13 - 0.15, 'JST'], [B14 - 0.15, 'PROF'],
      [B15 - 0.15, 'JST'], [B12 - 0.1, 'OTSJ'], [B16, 'PROF'], [B17 - 0.1, 'OTSJL'], [B19, 'JST'],
    ];
    let si = 0; for (let i = 0; i < SHOTS.length; i++) if (t >= SHOTS[i][0]) si = i;
    const shotName = SHOTS[si][1], shotT0 = SHOTS[si][0], shotT1 = SHOTS[si + 1] ? SHOTS[si + 1][0] : E;

    // ================================================================ Jesus: walk -> kneel
    const wk = walkPath(t, WALK, S - 0.25, tArrive, { ta: 0.01, td: 0.5, stride: 1.05, phase0: 0.62, yaw1: KY, turn: 0.55 });
    const kneel = k(t, [[tKneel0, 0], [tKneel1, 1, 'inOut']]);

    // the lean gag: Jesus leans in (#1 "me", #2 "you", #3 "emotions!"), the user leans back the same amount
    const jLean = k(t, [['s13', 0.03], [B06 + 0.1, 0.03], [B06 + 0.5, 0.19, 'out'], [B06 + 0.7, 0.18, 'inOut'],
      [B08 + 0.05, 0.18], [B08 + 0.4, 0.31, 'out'], [B08 + 0.55, 0.3, 'inOut'],
      [B13 + 0.15, 0.3], [B13 + 0.5, 0.43, 'out'], [B13 + 0.65, 0.42, 'inOut'],
      [B18 + 0.05, 0.42], [B18 + 0.7, 0.05, 'inOut']]);
    const lag = 0.14;
    // the user leans back by exactly the same angle, a few frames late (the gag reads in the profile two-shot)
    const uLeanBack = k(t, [['s13', 0], [B06 + 0.1 + lag, 0], [B06 + 0.5 + lag, 0.16, 'out'], [B06 + 0.7 + lag, 0.15, 'inOut'],
      [B08 + 0.05 + lag, 0.15], [B08 + 0.4 + lag, 0.28, 'out'], [B08 + 0.55 + lag, 0.27, 'inOut'],
      [B13 + 0.15 + lag, 0.27], [B13 + 0.5 + lag, 0.4, 'out'], [B13 + 0.65 + lag, 0.39, 'inOut'],
      [B12 - 0.05, 0.39], [B12 + 0.35, 0.3, 'inOut'], [B16 + 0.6, 0.3], [B16 + 1.3, 0.2, 'inOut'], [B17 + 0.1, 0.2], [B17 + 0.5, 0.12, 'inOut']]);
    const uBack = k(t, [['s13', 0], [tKneel0 + 0.1, 0], [tKneel0 + 0.6, 0.6, 'inOut'], [tHey, 0.6], [tHey + 1.2, 0.25, 'inOut']]);

    // ================================================================ JESUS pose
    const jPose = (pass) => {
      const ue = user.anchor('eyes');
      const uE = ue ? arr(ue) : SW(...UEYE);
      const uPh = user.anchor('phone');
      const ph = uPh ? arr(uPh) : SW(-1.25, 0.75, 1.3);
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
      const Fgive = JX('rueful', { mSmile: 0.22, mPress: 0.55, browIn: 0.55, browOut: 0.1, lidU: 0.86, lidL: 0.3 });
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
        [B19 + 0.1, Fgo], [B19 + 0.45, JX('hopeful', { mSmile: 0.55, mOpen: 0.04, browIn: 0.6, browOut: 0.25 }), 'inOut'], [B19 + 0.95, Fgive, 'inOut'],
      ]);
      // the nose-laugh on "Fair." (eye crinkle) and the brightening on "emotions"
      const snort = pulse(t, tFair - 0.02, tFair + 0.35, 0.06, 0.25);
      face.lidL += 0.35 * snort; face.mSmile += 0.2 * snort;
      face.autoBlink = (shotName === 'JST' || shotName === 'OTSK' || shotName === 'OTSK2') ? 0 : 1;
      // ---- gaze: hands-check moment (the user looks at HIS hands), his eyes stay on the user's eyes;
      //      a slight nod down toward the phone on "you know"; nothing else pulls him away
      const gPh = add(ph, [0, 0.02, 0]);
      const gaze = k(t, [['s13', uE], [tCrying + 1.0, uE], [tCrying + 1.25, gPh, 'inOut'], [tKnow + 0.25, gPh], [tKnow + 0.5, uE, 'inOut']]);
      // ---- head: small "no" shake on "don't have to", concession nod on "Fair", nods, the 'go on' nod, the 'mm'
      const shake = 0.07 * Math.sin(2 * Math.PI * 2.4 * (t - tDont)) * pulse(t, tDont, tDont + 0.85, 0.15, 0.25);
      const nods = 0.12 * pulse(t, tFair + 0.05, tFair + 0.55, 0.18, 0.3)
        + 0.1 * pulse(t, tKnow - 0.35, tKnow + 0.45, 0.25, 0.4)                 // nod down toward the phone
        + 0.13 * pulse(t, tMean + 0.05, tMean + 1.0, 0.4, 0.45)                 // one slow nod
        + 0.08 * pulse(t, tSound - 0.25, tSound + 0.05, 0.12, 0.14) + 0.08 * pulse(t, tSound + 0.1, tSound + 0.42, 0.12, 0.16)   // two small nods
        + 0.07 * pulse(t, B16 + 0.25, B16 + 0.85, 0.22, 0.3)                    // 'go on'
        + 0.07 * pulse(t, B19 + 0.6, B19 + 1.1, 0.2, 0.25);                     // tiny 'mm'
      const tilt = k(t, [['s13', 0], [tKneel1, 0.06], [B06 + 0.3, 0.06], [B06 + 0.7, 0.1, 'inOut'], [B13, 0.08], [B13 + 0.5, 0.02, 'inOut'], [B15, 0.02], [B15 + 0.4, 0.08, 'inOut']]);
      // ---- arms
      const open = smooth(clamp((t - (tKneel0 + 0.45)) / 0.7));
      const restL = [['knee_rest', 0.65], ['open', 0.35]];
      const heart1 = pulse(t, tMe - 0.25, B07 + 0.1, 0.25, 0.4);              // fingertips to his chest on "me"
      const flick = pulse(t, tVoid7 - 0.3, tVoid7 + 0.45, 0.22, 0.3);         // small flick back toward the Void
      const offer = pulse(t, tYou - 0.35, B11 + 1.6, 0.35, 0.5);              // open palm toward them on "you"
      const clasp = pulse(t, B13 + 0.15, B14 + 0.25, 0.3, 0.3);               // hands clasped at the chest
      const heart2 = pulse(t, tMean - 0.2, B15 + 0.1, 0.2, 0.35);             // hand on his heart on "meaningful"
      // gestures with the LEFT hand (the camera side in the profile two-shot; the right hand rests palm-up on the
      // thigh). The flick = the usual preset blend + an offset toward a point over his left shoulder (pass 1 only,
      // measured from the pass-0 hand, so it starts and ends exactly on the preset pose).
      const g = Math.max(0, 1 - heart1 - offer - clasp - heart2);
      const prL = [['knee_rest', Math.max(0.001, 0.65 * g)], ['open', 0.35 * g], ['heart', heart1 + heart2], ['offer', offer * 0.85], ['clasp_chest', clasp]];
      const armL = { preset: flick > 0.001 ? [...prL.map(([n, w]) => [n, w * (1 - 0.6 * flick)]), ['explain', 0.6 * flick + 1e-3]] : prL, reach: open, hand: { splay: 0.05, cup: 0.4 } };
      const shL = jesus.anchor('shoulderL'), hl = jesus.anchor('handL');
      if (pass && flick > 0.001 && shL && hl) {
        const back = SV(-FWD_K[0], 0, -FWD_K[2]);
        const tgt = add(arr(shL), [back[0] * 0.14, 0.1, back[2] * 0.14]);
        armL.offset = [(tgt[0] - hl.x) * flick, (tgt[1] - hl.y) * flick, (tgt[2] - hl.z) * flick];
        armL.hand = { curl: 0.25, spread: 0.2, thumb: 0.75, cup: 0.3 };
      }
      const armR = { preset: [['open', Math.max(0.001, 1 - clasp)], ['clasp_chest', clasp]], reach: open, hand: { splay: 0.06, cup: 0.4 } };
      const settle = pulse(t, B18 + 0.05, B18 + 1.6, 0.6, 0.6);
      return {
        pos: wk.amount > 0.001 || t < tArrive ? wk.pos : EDGE.W(KP), yaw: t < tArrive + 0.1 ? wk.yaw : EDGE.Y(KY),
        walk: { amount: wk.amount, phase: wk.phase, style: 'walk' },
        body: { kneel, lean: jLean + 0.05 * kneel, tilt: 0, shrug: 0.06 * pulse(t, tFair - 0.02, tFair + 0.3, 0.05, 0.2), bounce: -0.01 * settle,
          breathe: shotName === 'JST' ? 0.8 : 1, sway: kneel > 0.9 ? 0.5 : 1 },
        head: { follow: k(t, [['s13', 0.3], [tKneel1, 0.55]]), pitch: nods, yaw: shake, roll: -tilt, talk: 0.7 },
        gaze: pass ? gaze : null,
        face,
        blinkAt: [tKneel1 - 0.1, tOkay - 0.3, tCrying - 0.35, B10 + 0.75, B06 + 0.05, tYou + 0.5, B13 + 0.05, B18 + 0.45, B16 + 0.1, B19 + 0.12],
        armL, armR,
        glow: 1 + 0.25 * smooth(clamp((t - tMean) / 0.5)) * (1 - smooth(clamp((t - B15 - 0.3) / 0.8))),
      };
    };

    // ================================================================ USER pose
    const uPose = (pass) => {
      const je = jesus.anchor('eyes'), jhL = jesus.anchor('handL'), jhR = jesus.anchor('handR');
      const jE = je ? arr(je) : SW(...JEYE);
      const jHands = jhL && jhR ? [(jhL.x + jhR.x) / 2, (jhL.y + jhR.y) / 2, (jhL.z + jhR.z) / 2] : SW(KP[0], 0.7, KP[2]);
      const vb = vd.anchor('back');
      const vB = vb ? arr(vb) : SW(1.0, 1.5, -1.1);
      const phs = user.anchor('phoneScreen');
      const phS = phs ? arr(phs) : SW(-1.2, 0.6, 1.3);
      // eye targets for the search on "emotions": his left eye, right eye, mouth (left = his +X)
      const jl = SV(Math.cos(KY), 0, -Math.sin(KY));
      const eyeL = add(jE, [jl[0] * 0.035, 0, jl[2] * 0.035]), eyeR = add(jE, [-jl[0] * 0.035, 0, -jl[2] * 0.035]), mouth = add(jE, [0, -0.09, 0]);
      const aside = add(jE, [-jl[0] * 0.9, 0.35, -jl[2] * 0.9]);              // the eye-roll aside on "Wasn't planning on it"
      const gaze = k(t, [
        ['s13', jE], [tKneel0 + 0.35, jE], [tKneel0 + 0.5, jHands, 'out'], [tKneel1 - 0.2, jHands], [tKneel1 + 0.05, jE, 'inOut'],
        [tVoid3 - 0.55, jE], [tVoid3 - 0.45, vB, 'out'], [tVoid3 - 0.12, vB], [tVoid3 - 0.02, jE, 'out'],
        [tWasnt + 0.05, jE], [tWasnt + 0.3, aside, 'inOut'], [T('s13b04.end') - 0.05, aside], [T('s13b04.end') + 0.2, jE, 'inOut'],
        [B10 + 0.3, jE], [B10 + 0.42, phS, 'out'], [B10 + 0.75, phS], [B10 + 0.95, jE, 'inOut'],
        [tEmo1 + 0.45, jE], [tEmo1 + 0.5, eyeL, 'out'], [tEmo1 + 0.8, eyeL], [tEmo1 + 0.85, eyeR, 'out'], [tEmo1 + 1.1, eyeR], [tEmo1 + 1.16, mouth, 'out'], [tEmo1 + 1.4, mouth], [tEmo1 + 1.48, jE, 'out'],
        [B16 + 0.55, jE], [B16 + 0.75, phS, 'inOut'],
      ]);
      // ---- face
      const Fwary = UX([['suspicious', 0.45], ['idle', 0.55]], { glisten: 0, wet: 0.35 });
      const Fsusp = UX('suspicious', { wet: 0.5 });
      const Fsmirk = UX('smirk', { wet: 0.5 });
      const Fcaught = UX('idle', { lidU: 1.12, browIn: 0.45, mPress: 0.3, wet: 0.5 });
      const Ftrem = UX('tremble', { wet: 0.5 });
      const Fdawn = UX('dawning', { wet: 0.5 });
      const Fsoft = UX('soften', { wet: 0.5 });
      const Fsoft2 = UX([['soften', 0.6], ['tremble', 0.4]], { wet: 0.5 });
      const Fstall = UX([['tremble', 0.55], ['soften', 0.45]], { wet: 0.5 });
      const Fwall = UX([['idle', 0.5], ['deadpan', 0.5]], { wet: 0.5, mPress: 0.5 });
      const Fnope = UX([['hellno', 0.45], ['deadpan', 0.55]], { wet: 0.5 });
      const face = k(t, [
        ['s13', Fwary], [tVoid3 - 0.1, Fwary], [tVoid3 + 0.15, Fsusp, 'inOut'],
        [tWasnt - 0.05, Fsusp], [tWasnt + 0.25, Fsmirk, 'inOut'], [T('s13b04.end') + 0.4, Fsmirk], [tFair + 0.2, Fwary, 'inOut'],
        [tCrying, Fwary], [tCrying + 0.25, Fcaught, 'out'],
        [B10 + 0.6, Fcaught], [B10 + 1.1, Ftrem, 'inOut'],
        [B06 + 0.2, Ftrem], [tMe + 0.05, Fdawn, 'inOut'],
        [B07 + 0.5, Fdawn], [B08, Fsoft2, 'inOut'], [tYou, Fsoft2], [tYou + 0.3, Fsoft, 'out'],
        [tEmo1 + 0.3, Fsoft], [tEmo1 + 0.7, Fstall, 'inOut'], [tFeel + 0.4, Fstall], [B13, Fsoft, 'inOut'],
        [B12 - 0.2, Fsoft], [B12, Fstall, 'inOut'],
        [B16 + 0.5, Fstall], [B16 + 1.1, Fwall, 'inOut'], [B17, Fwall], [B17 + 0.12, Fnope, 'out'],
      ]);
      // flinches (#1 on "emotions": 3-frame squeeze; #2 smaller), the swallow, the catches of breath
      const sq1 = pulse(t, tEmo1, tEmo1 + 0.16, 0.03, 0.06), sq2 = pulse(t, tEmo2, tEmo2 + 0.12, 0.03, 0.05);
      const squeeze = Math.max(sq1, 0.55 * sq2);
      if (squeeze > 0) { const sc = UX('scrunch'); for (const kk of ['lidU', 'lidL', 'squint', 'browIn', 'browSq']) face[kk] = lerp(face[kk], sc[kk], squeeze); }
      const gulp = pulse(t, tFeel + 0.45, tFeel + 0.85, 0.1, 0.2);
      if (gulp > 0) { face.mPress = lerp(face.mPress, 0.95, gulp); face.mWide = lerp(face.mWide, -0.3, gulp); }
      face.autoBlink = 1;
      const flinch = 0.6 * pulse(t, tEmo1 - 0.02, tEmo1 + 0.4, 0.08, 0.3) + 0.3 * pulse(t, tEmo2 - 0.02, tEmo2 + 0.32, 0.07, 0.25);
      const catches = 0.22 * pulse(t, tEmo1 + 0.55, tEmo1 + 0.8, 0.06, 0.18) + 0.22 * pulse(t, tEmo1 + 0.95, tEmo1 + 1.2, 0.06, 0.18);
      const sniff = 0.2 * pulse(t, tHey + 0.45, tHey + 0.75, 0.06, 0.2);
      const relief = k(t, [['s13', 0.3], [tDont + 0.3, 0.3], [tDont + 0.8, 0.22, 'inOut'], [B10, 0.22], [B10 + 0.4, 0.12, 'inOut']]);
      // ---- arms: crossed -> phone face-down in the lap -> both hands on it -> hand on heart -> reach -> sink -> face-up -> strings
      const loosen = smooth(clamp((t - (B10 + 0.08)) / 0.5));
      const flipDown = smooth(clamp((t - (B10 + 0.45)) / 0.35));
      const both = smooth(clamp((t - (B07 + 0.35)) / 0.7));
      const hHeart = smooth(clamp((t - (tYou + 0.05)) / 0.65)) * (1 - smooth(clamp((t - (B16 + 0.25)) / 0.6)));
      const reach = pulse(t, B12 + 0.08, B16 + 0.6, 0.35, 0.55);
      const flipUp = smooth(clamp((t - (B16 + 0.85)) / 0.4));
      const yank = smooth(clamp((t - (B17 + 0.2)) / 0.14)) * (1 - smooth(clamp((t - (B17 + 0.85)) / 0.45)));
      const pull = pulse(t, B17 + 0.3, B17 + 0.7, 0.1, 0.25);                 // the yank itself: hands snap down/out
      const after = smooth(clamp((t - (B17 + 0.85)) / 0.45));
      const phoneLvl = k(t, [['s13', 0.85], [B10 + 0.55, 0.85], [B10 + 0.75, 0, 'inOut'], [B16 + 1.05, 0], [B16 + 1.2, 0.85, 'inOut']]);
      const palmDown = [0, -1, 0];
      let armL;
      if (t < B10 + 0.08) armL = { preset: 'crossed' };
      else if (after > 0.001) armL = { preset: [['strings', Math.max(0.001, yank)], ['hold', Math.max(0.001, after)]] };
      else if (yank > 0.001) armL = { preset: [['lap', 1 - yank], ['strings', Math.max(0.001, yank)]], offset: SV(0, -0.07 * pull, 0) };
      else armL = { preset: [['crossed', 1 - loosen], ['lap', Math.max(0.001, loosen)]], palm: flipDown > 0.5 && flipUp < 0.5 ? palmDown : undefined };
      let armR;
      const uch = user.anchor('chest'), uhR = user.anchor('handR');
      const baseR = [['crossed', Math.max(0.001, 1 - loosen * 0.5 - both * 0.5 - hHeart)], ['lap', Math.max(0.001, both * (1 - hHeart))], ['heart', Math.max(0.001, hHeart)]];
      if (t < B10 + 0.08) armR = { preset: 'crossed' };
      else if (after > 0.001) armR = { preset: [['strings', Math.max(0.001, yank)], ['knee', Math.max(0.001, after)]] };
      else if (yank > 0.001) armR = { preset: [['lap', 1 - yank], ['strings', Math.max(0.001, yank)]], offset: SV(0, -0.07 * pull, 0) };
      else {
        // "I just..." — the hand on the chest lifts toward him (palm turning up, fingers loosely curled) and stops mid-air
        armR = { preset: reach > 0.001 ? [...baseR.map(([n, w]) => [n, w * (1 - 0.55 * reach)]), ['shrug', 0.55 * reach]] : baseR };
        if (reach > 0.001) armR.hand = { curl: 0.3, spread: 0.15, thumb: 0.45, cup: 0.4 };
        if (pass && reach > 0.001 && uch && uhR) {
          const tgt = [lerp(uch.x, jE[0], 0.3), uch.y - 0.04, lerp(uch.z, jE[2], 0.3)];
          armR.offset = [(tgt[0] - uhR.x) * 0.85 * reach, (tgt[1] - uhR.y) * 0.85 * reach, (tgt[2] - uhR.z) * 0.85 * reach];
        }
      }
      // thumb rubbing along the phone edge (b07)
      if (both > 0.5 && hHeart < 0.5 && yank <= 0.001 && after <= 0.001) armR.offset = SV(0.012 * Math.sin(t * 2 * Math.PI * 1.6) * both, 0, 0);
      const hs = headShake(t, B17 + 0.02, { count: 2, dur: 0.38, amp: 0.13 });
      return {
        pos: POS.USEAT, yaw: YAW.U,
        body: { sit: 1, sitPath: 'plain', hunch: relief, lean: 0.16 - uLeanBack, recoil: uBack * 0.3, flinch, shrug: sniff + catches + 0.12 * yank, breathe: 1 + 0.4 * catches },
        head: { pitch: k(t, [['s13', 0.08], [B16 + 0.6, 0.08], [B16 + 0.9, 0.24, 'inOut']]), yaw: hs.yaw, roll: 0 },
        gaze: pass ? gaze : null,
        face,
        blinkAt: [tKneel1 + 0.1, tCrying + 0.6, tMe + 0.12, tMe + 0.36, tYou + 0.2, B12 - 0.3, B16 + 0.6],
        armL, armR,
        extra: { phone: phoneLvl, screen: 'feed', glisten: k(t, [['s13', 0.25], [B10 + 0.9, 0.25], [B10 + 1.6, 0.45, 'inOut']]),
          tears: k(t, [['s13', 0], [tEmo1 + 0.6, 0], [tEmo1 + 1.8, 0.4, 'inOut']]), hairSwing: hs.hairSwing,
          hood: k(t, [[B17 + 0.3, 0], [B17 + 0.42, 0.6, 'out'], [B17 + 0.62, 1, 'out']]) },
      };
    };

    // ================================================================ VOID: turns back to upstage; peeks over its LEFT shoulder in b10
    const back = smooth(clamp((t - (S - 0.1)) / (tArrive + 0.35 - S)));
    const peek = pulse(t, B10e - 0.78, B06 + 1.3, 0.38, 0.8);
    const vPose = (pass) => {
      const je = jesus.anchor('eyes');
      const Fsulk = VX('sad', { lidU: 0.72 }), Fgentle = VX('gentle', { lidU: 0.6, lidL: 0.48, mSmile: 0.55 });
      const Fpeek = VX('curious', { lidU: 1.18, browIn: 0.7, browOut: 0.5, mSmile: 0.1 });
      const face = k(t, [['s13', Fgentle], [S + 0.6, Fgentle], [S + 1.3, Fsulk, 'inOut'], [B10e - 0.6, Fsulk], [B10e - 0.4, Fpeek, 'out'], [B06 + 0.9, Fpeek], [B06 + 1.5, Fsulk, 'inOut']]);
      return {
        pos: POS.VSIT, yaw: YAW.VSIT,
        body: { sit: 1, slump: 0.4 - 0.08 * peek, twist: -0.35 * (1 - back) + 0.3 * peek, breathe: 1.15, breathRate: 0.19 },
        head: { yaw: -1.75 * (1 - back) + 1.8 * peek, pitch: lerp(-0.04, 0.26, back) - 0.18 * peek, roll: -0.08 * (1 - back) },
        armL: { preset: 'crossed' }, armR: { preset: 'crossed' },
        gaze: pass && peek > 0.05 && je ? arr(je) : null,
        face,
      };
    };

    // ================================================================ camera (framed between the passes)
    // the user's eyes as the keyed lean-back moves them (stage-local; ignores flinches so the camera never twitches)
    const UB = [-Math.sin(M.U.yaw), 0, -Math.cos(M.U.yaw)];
    const uEyeL = (lb) => [UEYE[0] + UB[0] * 0.42 * lb, UEYE[1] - 0.05 * lb, UEYE[2] + UB[2] * 0.42 * lb];
    const UE_T = uEyeL(uLeanBack);
    const PM_T = [PMID[0] + UB[0] * 0.2 * uLeanBack, PMID[1], PMID[2] + UB[2] * 0.2 * uLeanBack];
    const cam = () => {
      const u = clamp((t - shotT0) / Math.max(0.01, shotT1 - shotT0));
      let shot;
      switch (shotName) {
        case 'WIDE': shot = EDGE.shot([KP[0] + 0.1, 0.85, KP[2] - 0.05], { dist: lerp(3.35, 3.1, smooth(u)), yaw: -27, pitch: -1, fov: 44, screenY: sy(560), drift: 0.3 }); break;
        case 'OTSK': shot = EDGE.shot(JEYE, { dist: 2.25, yaw: -30, pitch: 6, fov: 33, screenY: sy(400), drift: 0.2 }); break;
        case 'OTSK2': shot = EDGE.shot(JEYE, { dist: k(t, [[tFair, 2.2], [T('s13b09'), 2.15], [B10, 1.8, 'inOut']]), yaw: -28, pitch: 6, fov: 33, screenY: sy(400), drift: 0.2 }); break;
        case 'OTSKW': shot = EDGE.shot(JEYE, { dist: 3.1, yaw: -30, pitch: 8, fov: 44, screenY: sy(600), drift: 0.2 }); break;
        case 'OTSJL': shot = EDGE.shot(UE_T, { dist: 1.9, yaw: 104, pitch: 20, fov: 33, screenY: sy(340), drift: 0.2 }); break;
        case 'OTSJ': shot = EDGE.shot(UE_T, { dist: 1.5, yaw: 116, pitch: 15, fov: 33, screenY: sy(420), drift: 0.2 }); break;
        case 'PROF': shot = EDGE.shot(PM_T, { dist: 5.3, yaw: PERP_DEG + PROF_ROT, pitch: 3, fov: 33, screenY: sy(470), drift: 0.15 }); break;
        case 'PUSHU': {
          const a = EDGE.shot(PM_T, { dist: 5.3, yaw: PERP_DEG + PROF_ROT, pitch: 3, fov: 33, screenY: sy(470) });
          const b = EDGE.shot(uEyeL(0.27), { dist: 1.3, yaw: 116, pitch: 7, fov: 33, screenY: sy(430) });
          const w = smooth(clamp((t - shotT0) / (B11 + 0.3 - shotT0)));
          const wl = smooth(clamp(w * 1.7));                                  // the aim reaches the face first
          shot = { pos: a.pos.map((x, i) => lerp(x, b.pos[i], w)), look: a.look.map((x, i) => lerp(x, b.look[i], wl)), fov: 33, drift: 0.12 };
          break;
        }
        case 'JST': shot = EDGE.shot(JEYE, { dist: 1.45, yaw: -31, pitch: 1, fov: 33, screenY: sy(400), drift: 0.15 }); break;
        default: shot = EDGE.cam('MASTER');
      }
      applyShot(app.camera, shot, t, 13);
    };

    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t), voidPos: POS.VSIT,
      sunGlow: shotName === 'OTSJ' || shotName === 'PUSHU' ? 0.7 : 1,
      clear: shotName === 'PROF' || shotName === 'PUSHU' ? PROF_CLEAR : [[POS.U[0], POS.U[2], 0.8], [POS.VSIT[0], POS.VSIT[2], 1.4], [POS.K[0], POS.K[2], 0.6]],
    });
    solve(t, [[vd, vPose], [user, uPose], [jesus, jPose]], cam);

    fx.begin();
    drawSkyGalaxy(fx, t);
    fx.end();
    gal.userData.update(t);
    st.look = lookFor('s13', set.look);
  },
};
