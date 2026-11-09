// s11 oh_boy — Jesus, caught between two crossed-arm grumps he loves, gets the most awkward face in the world.
// b01 the look assembles on the narrator's words (brows on "gets", clench on "look", chin tuck on "face");
// b02 locked close-up, eyes only: Void's back -> the user -> INTO THE LENS -> the sky (help?), inhale through
// the teeth lifts the shoulders; b03 "Oh, boy." through the clench + one more dart on "boy"; b04 the
// symmetrical master: the Void's sulking back, the user glaring at the phone, Jesus stuck in the middle.
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, fbm1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { UX } from '../chars/user.js';
import { EDGE, todAt, voidSkyAt, sy, lookFor } from './marks.js';
import { loadLines, W, POS, YAW, SW, dirPoint, add, own, stamp, drawSkyGalaxy, makeLittleGalaxy, solve, pulse } from './kit_s11_13.js';

const JM = EDGE.M.JM;
// Jesus's eyes at JM (static estimate: the camera is applied BEFORE the rigs update)
const EYE_JM_L = [JM.p[0] + 0.14 * Math.sin(JM.yaw), 1.545, JM.p[2] + 0.14 * Math.cos(JM.yaw)];
const EYE_JM = SW(...EYE_JM_L);
// the b04 wide (stage-local; MASTER's direction: yaw -9.4, pitch 14.3)
const MW = { look: [-0.55, 1.2, -0.05], yaw: -9.4, pitch: 13, fov: 33, sy: 520, d0: 6.4, d1: 5.2, d2: 4.7 };

export default {
  id: 's11',
  async setup(app) {
    await loadLines();
    const set = await app.set('EDGE');
    const [jesus, vd, user] = await Promise.all([app.char('JESUS'), app.char('VOID'), app.char('USER')]);
    const fx = new Particles({ max: 48, intensity: 1.5 });
    own(fx.mesh, 's11');
    const gal = makeLittleGalaxy();
    return { scene: set.scene, set, jesus, vd, user, fx, gal, look: lookFor('s11', set.look) };
  },

  async update(t, app, st) {
    stamp(t, 's11');
    const { set, jesus, vd, user, fx, gal } = st;
    for (const o of [jesus.root, vd.root, user.root, fx.mesh, gal]) st.scene.add(o);

    // ---------------------------------------------------------------- timing (all from the timeline / words)
    const tGets = W('s11b01', 'gets'), tLook = W('s11b01', 'look'), tFace = W('s11b01', 'face');
    const D0 = T('s11b01.end') + 0.06;                    // first dart (b02 is a 2.4 s locked hold)
    const tOh = T('s11b03'), tBoy = W('s11b03', 'boy', { alt: ['bye'], frac: 0.2 });
    const tAwk = W('s11b04', 'awkward', { frac: 0.55 });
    const tCut = T('s11b04') - 0.06;                      // pull back to the symmetrical wide on the line
    const wide = t >= tCut;

    // ---------------------------------------------------------------- camera (before the rigs: catchlights)
    let shot;
    if (!wide) {
      const d = k(t, [['s11', 2.08], ['s11b01.end', 1.92, 'inOut']]);   // the faintest push while the look builds
      shot = EDGE.shot(EYE_JM_L, { dist: d, yaw: 3, pitch: 0.5, fov: 21, screenY: sy(420), drift: 0 });
    } else {
      // the symmetrical wide, tightened: MASTER's direction on a longer lens, the look lowered toward Jesus (knee-up at
      // centre), the Void's seated back filling the right, the user's head + shoulders lower-left. It creeps in from the
      // cut (a third of the way by "awkward"), then keeps creeping through the held silence.
      const d = k(t, [[tCut, MW.d0], [tAwk + 0.1, MW.d1, 'inOut'], ['s11.end', MW.d2, 'inOut']]);
      shot = EDGE.shot(MW.look, { dist: d, yaw: MW.yaw, pitch: MW.pitch, fov: MW.fov, screenY: sy(MW.sy), drift: 0.25 });
    }
    applyShot(app.camera, shot, t, 11);

    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t), voidPos: POS.VSIT,
      sunGlow: wide ? 1 : 0.6,
      clear: [[POS.U[0], POS.U[2], 0.8], [POS.VSIT[0], POS.VSIT[2], 1.4]],
    });

    // ---------------------------------------------------------------- JESUS
    const lens = [app.camera.position.x, app.camera.position.y, app.camera.position.z];
    const G = {
      mid: dirPoint(EYE_JM, JM.yaw, -0.03, -0.03, 4),
      vside: dirPoint(EYE_JM, JM.yaw, 0.62, 0.0, 3),       // HIS left = screen-right: the Void's back
      sky: dirPoint(EYE_JM, JM.yaw, 0.06, 0.62, 3),
    };
    const jPose = (pass) => {
      const ue = pass ? user.anchor('eyes') : null;
      const U = ue ? [ue.x, ue.y, ue.z] : SW(-1.3, 0.92, 1.4);
      // gaze: the user -> front (realisation) -> darts (hold 8 f / 8 f / lens 12 f / sky) -> "boy" darts
      const gaze = k(t, [
        ['s11', U], [tGets - 0.02, U], [tGets + 0.16, G.mid, 'inOut'],
        [D0, G.mid], [D0 + 0.08, G.vside, 'out'],
        [D0 + 0.413, G.vside], [D0 + 0.493, U, 'out'],
        [D0 + 0.826, U], [D0 + 0.906, lens, 'out'],
        [D0 + 1.406, lens], [D0 + 1.56, G.sky, 'inOut'],
        [tOh - 0.04, G.sky], [tOh + 0.08, G.mid, 'inOut'],
        [tBoy, G.mid], [tBoy + 0.07, G.vside, 'out'], [tBoy + 0.2, G.vside], [tBoy + 0.28, U, 'out'], [tBoy + 0.45, U], [tBoy + 0.6, G.mid, 'inOut'],
        [tCut, U], [tAwk - 0.25, U], [tAwk - 0.05, G.vside, 'out'], [tAwk + 0.5, G.vside], [tAwk + 0.62, U, 'out'],
      ]);
      // the face assembles on the words
      // the look: WORRIED brows (inner tips way up, outer ends a touch down), a flat strained rectangle of clenched
      // teeth with the corners pulled OUT and DOWN (never a grin), a little lower-lid tension
      const F0 = JX('listening', { browIn: 0.22, mSmile: 0.08 });
      const F1 = JX('listening', { browIn: 1.0, browOut: 0.12, browMid: 0.1, browSq: 0.12, lidU: 1.14, mSmile: -0.05, mPress: 0.3, lidSad: 0.3 });
      const F1b = JX('awkward', { mClench: 0.0, mOpen: 0.06, mWide: 0.7, mSmile: -0.3, mAsym: 0.06, mPress: 0.55, browIn: 1.1, browOut: 0.0, lidSad: 0.36 });   // corners stretch out + down first
      const AWK = { mSmile: -0.36, mWide: 1.2, mOpen: 0.3, mAsym: 0.1, browIn: 1.22, browOut: -0.12, browMid: 0.06, browSq: 0.22, browAsym: 0.1, lidSad: 0.46, lidU: 1.16, lidL: 0.24 };
      const F2o = JX('awkward', { ...AWK, mWide: 1.3, mSmile: -0.42, browIn: 1.32, lidU: 1.24 });
      const F2 = JX('awkward', AWK);
      const F3 = JX('awkward', { ...AWK, mWide: 1.32, mSmile: -0.4, mOpen: 0.33, browIn: 1.28 });   // "a notch wider" (still down-turned)
      const face = k(t, [
        ['s11', F0], [tGets, F0], [tGets + 0.5, F1, 'inOut'],
        [tLook - 0.1, F1], [tLook + 0.05, F1b, 'inOut'], [tLook + 0.24, F2o, 'out'], [tLook + 0.5, F2, 'inOut'],
        [tAwk - 0.05, F2], [tAwk + 0.18, F3, 'out'],
      ]);
      // brow bob on "awkward" (up and back), held grimace
      const bob = pulse(t, tAwk - 0.02, tAwk + 0.42, 0.12, 0.3);
      face.browIn += 0.38 * bob; face.browOut += 0.3 * bob; face.lidU += 0.12 * bob;
      face.autoBlink = wide ? 1 : 0; face.saccade = 0;
      face.talk = 0.4;
      // posture: neck draws into the shoulders, the slow inhale through the teeth lifts them, exhale-hold
      const shrug = k(t, [['s11', 0.05], [tFace, 0.08], [tFace + 0.35, 0.24, 'out'], [D0 + 0.45, 0.24], [D0 + 1.9, 0.56, 'inOut'],
        [tOh + 0.6, 0.5], [tCut + 0.3, 0.42, 'inOut']]);
      const hp = k(t, [['s11', 0.06], [tGets + 0.05, 0.06], [tGets + 0.45, 0.0, 'inOut'], [tFace - 0.02, 0.0], [tFace + 0.22, 0.13, 'out'], [tFace + 0.45, 0.11, 'inOut'],
        [D0 + 1.5, 0.11], [D0 + 1.75, 0.07, 'inOut'], [tOh, 0.07], [tOh + 0.25, 0.1, 'inOut']]);
      const hy = k(t, [['s11', -0.14], [tGets + 0.04, -0.14], [tGets + 0.45, 0, 'inOut'],
        [tAwk - 0.2, 0], [tAwk + 0.05, 0.1, 'inOut'], [tAwk + 0.55, 0.1], [tAwk + 0.8, -0.06, 'inOut']]);
      // heel-to-toe rock once after "awkward", hands clasp / unclasp / clasp
      const rock = pulse(t, tAwk + 0.35, tAwk + 0.85, 0.2, 0.25);
      const rockB = pulse(t, tAwk + 0.8, tAwk + 1.3, 0.2, 0.3);
      const clasp = k(t, [['s11', 1], [tCut + 0.3, 1], [tCut + 0.5, 0.25, 'inOut'], [tAwk - 0.15, 0.25], [tAwk + 0.1, 1, 'out'],
        [tAwk + 0.7, 1], [tAwk + 0.9, 0.4, 'inOut'], [tAwk + 1.15, 1, 'out']]);
      const arm = { preset: [['clasp', clamp(clasp)], ['side', 1 - clamp(clasp)]] };
      return {
        pos: POS.JM, yaw: YAW.JM,
        body: { shrug, breathe: wide ? 1 : 0.35, sway: wide ? 0.8 : 0.08, tiptoe: 0.8 * rock, recoil: 0.14 * rockB },
        head: { yaw: hy, pitch: hp, roll: k(t, [['s11', 0], [tFace, 0], [tFace + 0.4, -0.03]]), talk: 0.3 },
        gaze: pass ? gaze : null,
        face,
        blinkAt: [tGets - 0.03, D0 + 1.43, tBoy + 0.62],
        armL: arm, armR: arm,
      };
    };

    // ---------------------------------------------------------------- VOID: seated, its sulking back, one puff
    const puff = pulse(t, tAwk + 0.15, tAwk + 1.05, 0.25, 0.55);
    const vPose = () => ({
      pos: POS.VSIT, yaw: YAW.VSIT,
      body: { sit: 1, slump: 0.32, swell: 0.25 * puff, breathe: 1.1 },
      head: { pitch: 0.3 - 0.08 * puff, yaw: 0.05, roll: 0.06 },
      armL: { preset: 'crossed' }, armR: { preset: 'crossed' },
      face: VX('sad', { lidU: 0.7 }),
      extra: { puff: 0.7 * puff, stars: 1.1 },
    });

    // ---------------------------------------------------------------- USER: arms crossed, glaring at the phone
    const uPose = (pass) => {
      const ph = pass ? user.anchor('phoneScreen') : null;
      return {
        pos: POS.USEAT, yaw: YAW.U,
        body: { sit: 1, sitPath: 'plain', hunch: 0.32, breathe: 1 },
        head: { pitch: 0.3, yaw: -0.08, roll: -0.04 },
        armL: { preset: 'crossed' }, armR: { preset: 'crossed' },
        face: UX('glare', { lidU: 0.6 }),
        gaze: ph,
        extra: { phone: 0.85, screen: 'feed', glisten: 0.3 },
      };
    };

    solve(t, [[vd, vPose], [user, uPose], [jesus, jPose]]);

    // ---------------------------------------------------------------- particles: the hood puff, the sky galaxy
    fx.begin();
    drawSkyGalaxy(fx, t);
    const ht = vd.anchor('hoodTop');
    if (ht) {
      fx.burst({ t, seed: 1103, at: tAwk + 0.35, count: 3, jitter: 0.25, life: 2.2, origin: [ht.x, ht.y - 0.05, ht.z],
        vel: [0, 0.32, 0], spread: [0.08, 0.06, 0.08], size: [0.35, 0.55], grow: 2.2, color: [0xa98cff, 0x8fd8ff],
        alpha: 0.4, fade: [0.2, 0.6], cell: CELL.nebula, spin: 0.3 });
    }
    fx.end();
    gal.userData.update(t);

    st.look = lookFor('s11', set.look);
  },
};
