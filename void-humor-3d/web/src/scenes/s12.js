// s12 a_hand_on_the_shoulder — the tenderest beat of Part One. The grimace melts on an exhale, Jesus walks round
// the downstage side of the sulking, seated Void and lays his RIGHT palm flat on its RIGHT shoulder (no pat).
// It stiffens, then eases under his hand; it looks back over that shoulder (eyes first) — the hand, then him —
// and gives him a small closed crescent smile with soft rounded lids, then a slow blink (high over his shoulder);
// reverse: Jesus's slight nod, a thumb stroke on the velvet, a breath in, his eyes slide toward the user: one more
// try — and in the last half second he is already going (palm off, turning, first step: s13 cuts in mid-walk).
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { UX } from '../chars/user.js';
import { EDGE, todAt, voidSkyAt, sy, lookFor } from './marks.js';
import { loadLines, W, POS, YAW, SW, SV, add, arr, own, stamp, drawSkyGalaxy, makeLittleGalaxy, solve, pulse, walkPath, VTURN, VGENTLE } from './kit_s11_13.js';

const M = EDGE.M;
// JM -> round the downstage side of the seated Void (keeps ~1.2 m off its centre) -> JS
const PATH = [M.JM.p, [0.2, 0, 0.16], [0.95, 0, 0.1], [1.5, 0, -0.2], M.JS.p];

export default {
  id: 's12',
  async setup(app) {
    await loadLines();
    const set = await app.set('EDGE');
    const [jesus, vd, user] = await Promise.all([app.char('JESUS'), app.char('VOID'), app.char('USER')]);
    const fx = new Particles({ max: 48, intensity: 1.5 });
    own(fx.mesh, 's12');
    const gal = makeLittleGalaxy();
    return { scene: set.scene, set, jesus, vd, user, fx, gal, look: lookFor('s12', set.look) };
  },

  async update(t, app, st) {
    stamp(t, 's12');
    const { set, jesus, vd, user, fx, gal } = st;
    for (const o of [jesus.root, vd.root, user.root, fx.mesh, gal]) st.scene.add(o);

    // ---------------------------------------------------------------- timing
    const tHand = W('s12b01', 'hand'), tVoids = W('s12b01', "void's", { alt: ['voids'] }), tShoulder = W('s12b01', 'shoulder', { frac: 0.85 });
    // the walk is anchored to the END of the narrator's line (fixed 2.33 s, so data/cues/s12.json can give its
    // footfalls as 's12b01.end-x' refs that move with re-timed audio); the palm lands on "shoulder", its last word
    const wEnd = T('s12b01.end') - 0.58, wStart = wEnd - 2.33;
    const tTouch = Math.max(wEnd + 0.02, tShoulder + 0.02);
    const B2 = T('s12b02'), B3 = T('s12b03');
    const tTurn0 = B2 - 0.85, tTurn1 = B2 + 0.95;                         // the hood turns over its RIGHT shoulder
    const tSmile = B2 + 0.95, tBlinkV = B2 + 1.62;
    const tNod = B3 + 0.25, tThumb = B3 + 0.55, tBreath = B3 + 0.7, tSlide = B3 + 0.85;
    // the last half second: he is already going (cut on action into s13's walk) — the palm lifts off the velvet, he
    // turns toward the user, weight forward and the first step down the same path s13 continues (STAGING s12->s13)
    const tLeave = T('s12.end') - 0.5;
    const lift = smooth(clamp((t - tLeave) / 0.34)), turnJ = smooth(clamp((t - tLeave) / 0.5)), step = smooth(clamp((t - tLeave - 0.18) / 0.32));
    const DEP = SV(-0.883 * 0.15 * step, 0, 0.469 * 0.15 * step);                 // first step toward K (stage dir JS -> WALK[1])
    const shotA = t < B2, shotB = t >= B2 && t < B3, shotC = t >= B3;

    const wk = walkPath(t, PATH, wStart, wEnd, { ta: 0.45, td: 0.55, stride: 1.05, phase0: 0.25, yaw0: M.JM.yaw, yaw1: M.JS.yaw, turnIn: 0.4, turn: 0.55 });

    // ---------------------------------------------------------------- JESUS
    const jPose = (pass) => {
      const vEyes = vd.anchor('eyes'), vSh = vd.anchor('shoulderR');
      const ue = user.anchor('eyes');
      // the grimace melts on the exhale, then tenderness
      const Fawk = JX('awkward', { mSmile: -0.5, mOpen: 0.56, mWide: 1, mAsym: 0.08, mTeethU: 1, mTeethL: 1, browIn: 1.3, browOut: 0.3, browMid: 0.2, lidSad: 0.1, lidU: 1.22 });   // = s11's held grimace
      const Fmelt = JX('concerned', { mSmile: 0.05, lidU: 0.86, browIn: 0.45 });
      const Ften = JX('tender', { mSmile: 0.28, mPress: 0.3, lidU: 0.82 });
      const Fsoft = JX('tender', { mSmile: 0.4, mPress: 0.45, mOpen: 0, lidU: 0.78, lidL: 0.38, browIn: 0.5, wet: 0.35 });
      const Fhope = JX('tender', { mSmile: 0.34, mPress: 0.4, lidU: 0.92, browIn: 0.6, browOut: 0.14 });
      const face = k(t, [['s12', Fawk], [T('s12') + 0.05, Fawk], [T('s12') + 0.55, Fmelt, 'inOut'], [tTouch - 0.4, Fmelt], [tTouch + 0.3, Ften, 'inOut'],
        [tSmile - 0.2, Ften], [tSmile + 0.5, Fsoft, 'inOut'], [tBreath, Fsoft], [tSlide + 0.25, Fhope, 'inOut']]);
      face.autoBlink = shotC ? 0 : 1;
      // body: the exhale (shoulders drop), a breath in before "one more try"
      const shrug = k(t, [['s12', 0.42], [T('s12') + 0.06, 0.44], [T('s12') + 0.6, 0.0, 'inOut'], [tBreath, 0], [tBreath + 0.35, 0.12, 'inOut']]);
      const slumpEx = pulse(t, T('s12') + 0.05, T('s12') + 0.9, 0.3, 0.5);
      // right palm: rises late in the walk, overshoots above the velvet, settles flat onto the shoulder
      const reach = k(t, [['s12', 0], [tTouch - 0.6, 0], [tTouch - 0.05, 1, 'inOut']]) * (1 - lift);
      const hover = k(t, [['s12', 0.1], [tTouch - 0.2, 0.08], [tTouch + 0.02, 0.0, 'out'], [tTouch + 0.12, -0.012, 'inOut'], [tTouch + 0.3, 0.0, 'inOut']]);
      const thumb = 0.35 + 0.4 * pulse(t, tThumb, tThumb + 0.55, 0.25, 0.3);
      // (the palm snaps onto the velvet itself — `surface: vd` raycasts the Void's shoulder — so it stays in contact while
      //  the Void twists round under it; the landing overshoot and the lift-off ride on top as an offset)
      const shT = vSh ? add(add(vSh, [0, 0.012, 0]), SV(...(shotC ? SH_OFF : [0, 0, 0]))) : null;
      // gaze: the Void as he walks round to it; its eyes when it turns; the user (eyes slide) at the end
      const vE = vEyes ? arr(vEyes) : SW(1.15, 1.8, -1.35);
      const uE = ue ? arr(ue) : SW(-1.3, 0.8, 1.4);
      const gHand = jesus.anchor('handR') ? arr(jesus.anchor('handR')) : vE;
      const gaze = k(t, [['s12', vE], [tTouch - 0.5, vE], [tTouch - 0.3, gHand, 'out'], [tTouch + 0.5, gHand], [tTurn0 + 0.6, vE, 'inOut'],
        [tSlide, vE], [tSlide + 0.22, uE, 'inOut']]);
      const nod = 0.12 * pulse(t, tNod, tNod + 0.9, 0.4, 0.45);
      return {
        pos: add(wk.pos, DEP), yaw: wk.yaw + 0.42 * turnJ,
        walk: { amount: Math.max(wk.amount, 0.6 * step), phase: wk.phase + 0.32 * step, style: 'walk' },
        body: { shrug, slump: 0.12 * slumpEx, breathe: shotC ? 0.7 : 1, lean: 0.05 * reach + 0.05 * step, sway: shotC ? 0.3 : 1 },
        head: { look: k(t, [['s12', vE], [tSlide + 0.1, vE], [tLeave + 0.35, uE, 'inOut']]), follow: k(t, [['s12', 0.15], [wStart + 0.5, 0.55], [tSlide, 0.6], [tSlide + 0.35, 0.3, 'inOut'], [tLeave + 0.4, 0.45, 'inOut']]), pitch: nod, roll: k(t, [['s12', 0], [tSmile, 0], [tSmile + 0.6, -0.06]]) },
        gaze: pass ? gaze : null,
        face,
        blinkAt: [T('s12') + 0.62, tTouch + 0.55, tNod + 0.3, tSlide - 0.06],
        armR: shT && reach > 0.001 ? { preset: 'shoulder', target: shT, surface: vd, offset: [0, hover + 0.07 * lift, 0], reach, hand: { curl: 0.28, spread: 0.3, thumb, cup: 0.12 } } : { preset: 'rest' },
        armL: { preset: 'rest' },
        glow: 1.05,
      };
    };

    // ---------------------------------------------------------------- VOID: seated sulk -> stiffens -> eases -> looks back
    const stiff = pulse(t, tTouch, tTouch + 0.55, 0.08, 0.4);
    const turn = smooth(clamp((t - tTurn0) / (tTurn1 - tTurn0)));
    const vPose = (pass) => {
      const jh = jesus.anchor('handR'), je = jesus.anchor('eyes');
      const gHand = jh ? arr(jh) : SW(1.8, 1.25, -0.9), gJ = je ? arr(je) : SW(1.74, 1.55, -0.37);
      const eyes = k(t, [['s12', gHand], [tTurn0 + 0.15, gHand], [B2 + 0.55, gHand], [B2 + 0.85, gJ, 'inOut']]);
      const Fsulk = VX('sad', { lidU: 0.7, lidArc: 0 });
      const Fsoft = VX('calm', { lidArc: 0.4, lidU: 0.8, lidL: 0.42, browIn: 0.5, browOut: -0.12, mSmile: 0.1 });
      const Fgentle = VX('gentle', VGENTLE);
      const face = k(t, [['s12', Fsulk], [tTouch, Fsulk], [tTouch + 0.8, Fsoft, 'inOut'], [tSmile - 0.1, Fsoft], [tSmile + 0.6, Fgentle, 'inOut']]);
      face.autoBlink = 0;
      // the slow blink after the smile lands (soft close, a held beat, a slower open)
      face.blink = k(t, [[tBlinkV, 0], [tBlinkV + 0.22, 1, 'inOut'], [tBlinkV + 0.38, 1], [tBlinkV + 0.8, 0, 'inOut']]);
      return {
        pos: POS.VSIT, yaw: YAW.VSIT,
        body: { sit: 1, slump: k(t, [['s12', 0.32], [tTouch + 0.3, 0.32], [tTouch + 1.3, 0.44, 'inOut']]) - 0.2 * stiff,
          shrug: 0.62 * stiff, bounce: 0.03 * stiff, breathe: 1 - 0.8 * stiff, twist: VTURN.twist * turn, tilt: VTURN.tilt * turn },
        head: { yaw: VTURN.yaw * turn, pitch: lerp(0.3, -0.04, turn) - 0.16 * stiff, roll: -0.08 * turn + 0.06 * (1 - turn) },
        armL: { preset: 'crossed' }, armR: { preset: 'crossed' },
        // in the 3/4 close the eyeline is cheated part-way toward the lens (no eyes pinned in the corners)
        gaze: pass && t > tTurn0 ? (shotB ? mixP(eyes, app.camera.position, VCHEAT) : eyes) : null,
        face,
        blinkAt: [B2 + 0.85],
        extra: { stars: 1.1 + 0.25 * smooth(clamp((t - tSmile) / 0.8)), rim: shotA ? 1 + 0.9 * smooth(clamp((t - (tTouch - 0.9)) / 0.6)) : 1 },
      };
    };

    // ---------------------------------------------------------------- USER (off to the side, arms crossed, phone)
    const uPose = (pass) => ({
      pos: POS.USEAT, yaw: YAW.U,
      body: { sit: 1, sitPath: 'plain', hunch: 0.3 },
      head: { pitch: 0.28, yaw: -0.08 },
      armL: { preset: 'crossed' }, armR: { preset: 'crossed' },
      face: UX('glare', { lidU: 0.62 }),
      gaze: pass ? user.anchor('phoneScreen') : null,
      extra: { phone: 0.85, glisten: 0.3 },
    });

    // ---------------------------------------------------------------- camera (framed from the pass-0 anchors)
    const frameCam = () => {
      let shot;
      if (shotA) {
        // BEHINDJ follow: it opens wider and further back with the seated Void's back already at frame-right (the walk
        // has a visible destination), dollies in behind Jesus as he rounds it, and lands on BEHINDJ well before the touch
        const C = EDGE.CAM.BEHINDJ;
        const land = smooth(clamp((wk.u - 0.66) / 0.3)), dolly = smooth(clamp(wk.u / 0.95));
        const back = [C.pos[0] + (C.pos[0] - C.look[0]) * CAMA.back, C.pos[1] + CAMA.up, C.pos[2] + (C.pos[2] - C.look[2]) * CAMA.back];
        const jl = wk.local;
        const vw = CAMA.vw * (1 - 0.85 * dolly);                                // the nearer the camera, the more it holds on him
        const aim = [lerp(jl[0], CAMA.v[0], vw), 1.3, lerp(jl[2], CAMA.v[2], vw)];   // Jesus + his destination
        const lk = [lerp(aim[0], C.look[0], land), lerp(aim[1], C.look[1], land), lerp(aim[2], C.look[2], land)];
        shot = EDGE.at([lerp(back[0], C.pos[0], dolly), lerp(back[1], C.pos[1], dolly), lerp(back[2], C.pos[2], dolly)], lk, lerp(CAMA.fov, 33, dolly), { drift: 0.2 });
      } else if (shotB) {
        // 3/4 close as the hood comes round: aimed between both eyes (a touch toward the far eye), the mouth clear of the
        // shoulder ridge, his hand in the lower-left foreground
        const CB = CAMB;
        // high over HIS shoulder (the back of his head soft in the lower third, his hand on its shoulder hidden below it):
        // the hood comes round toward him — and us — and the gentle smile lands on him; a slow push in. (From the front-
        // side this close was a capelet plate across the mouth and a stump of sleeve with a hooked finger.)
        const arcB = smooth(clamp((t - B2 - CB.a0) / (CB.a1 - CB.a0)));
        shot = EDGE.shot(CB.look, { dist: k(t, [['s12b02', CB.d0], [B2 + 1.5, CB.d1, 'inOut'], ['s12b02.end', CB.d1 - 0.08, 'inOut']]), yaw: lerp(CB.yaw, CB.yaw1, arcB), pitch: lerp(CB.pitch, CB.pitch1, arcB), fov: 33,
          screenY: sy(k(t, [['s12b02', CB.sy0], [B2 + 1.5, CB.sy1, 'inOut']])), drift: 0.15 });
      } else {
        const CC = CAMC;
        const dl = EDGE.L(add(SW(0, 0, 0), DEP));                            // follow half of his first step
        shot = EDGE.shot([JEYE_JS[0] - 0.03 + 0.5 * dl[0], JEYE_JS[1], JEYE_JS[2] - 0.03 + 0.5 * dl[2]], { dist: k(t, [['s12b03', CC.d0], ['s12b03.end', CC.d1, 'inOut']]), yaw: CC.yaw, pitch: CC.pitch, fov: 33, screenY: sy(CC.sy), drift: 0.12 });
      }
      applyShot(app.camera, shot, t, 12);
    };

    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t), voidPos: POS.VSIT,
      sunGlow: shotC ? 0.7 : 1, keyYaw: shotC ? -0.62 + 0.12 : undefined,
      clear: [[POS.U[0], POS.U[2], 0.8], [POS.VSIT[0], POS.VSIT[2], 1.4]],
    });
    solve(t, [[vd, vPose], [user, uPose], [jesus, jPose]], frameCam);

    // ---------------------------------------------------------------- particles: a star mote drifts up past his hand
    fx.begin();
    drawSkyGalaxy(fx, t);
    const sh = jesus.anchor('handR');                                    // it rises off the velvet right beside his hand
    if (sh) {
      const t0m = B2 + 0.45;
      const u = (t - t0m) / 2.6;
      if (u > 0 && u < 1) {
        const p = [sh.x + 0.05 * Math.sin(u * 5), sh.y + 0.04 + 0.75 * u, sh.z + 0.04 * Math.cos(u * 4)];
        const a = smooth(u / 0.15) * smooth((1 - u) / 0.3);
        fx.add(p, 0.04 + 0.01 * Math.sin(t * 7), 0xe8e0ff, 0.9 * a, t * 0.6, CELL.star);
        fx.add(p, 0.08, 0x9f8cff, 0.3 * a, 0, CELL.dot);
      }
    }
    fx.end();
    gal.userData.update(t);

    st.look = lookFor('s12', set.look);
  },
};

// The Void's eyes (stage-local) when its hood has turned over its right shoulder (measured from the rig; used to
// steady the b02 framing), and the b02 camera: high over Jesus's shoulder, inside +-50 deg of where the hood points.
// VCHEAT: the share of its eyeline cheated toward the lens in b02.
const VEYE_END = [1.33, 1.78, -1.12];
const CAMA = { back: 0.45, up: 0.15, fov: 42, v: [1.15, 0, -1.35], vw: 0.26 };
const CAMB = { look: [VEYE_END[0] + 0.055, VEYE_END[1] - 0.06, VEYE_END[2] - 0.2], yaw: 24, yaw1: 22, pitch: 33, pitch1: 35, a0: 0.1, a1: 1.1, d0: 3.1, d1: 2.8, sy0: 380, sy1: 370 };
const VCHEAT = 0.45;
// on the reverse (b03) the palm is cheated a little up and back onto the shoulder's crown (stage offset from the anchor), so it
// reads as lying ON the velvet instead of hanging off the slope's far side (b01/b02 keep the true anchor)
const SH_OFF = [0.05, 0.03, -0.12];
const mixP = (a, b, u) => { const A = arr(a), B = arr(b); return [lerp(A[0], B[0], u), lerp(A[1], B[1], u), lerp(A[2], B[2], u)]; };
// (yaw 118: the seated user stays hidden behind the Void's shoulder for the whole shot — no tangent with his forearm,
// and no visible flip of the user to screen-right in this cut-round)
const CAMC = { yaw: 118, pitch: 3, d0: 1.8, d1: 1.68, sy: 400 };
// Jesus's eyes at JS with his hand on its shoulder (stage-local, measured) — the steady look point of b03
const JEYE_JS = [1.72, 1.55, -0.53];
