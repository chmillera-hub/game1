// s12 a_hand_on_the_shoulder — the tenderest beat of Part One. The grimace melts on an exhale, Jesus walks round
// the downstage side of the sulking, seated Void and lays his RIGHT palm flat on its RIGHT shoulder (no pat).
// It stiffens, then eases under his hand; it looks back over that shoulder (eyes first) — the hand, then him —
// and gives him a small closed crescent smile; reverse: Jesus's slight nod, a thumb stroke on the velvet, a breath
// in, and his eyes slide toward the user: one more try.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { UX } from '../chars/user.js';
import { EDGE, todAt, voidSkyAt, sy, lookFor } from './marks.js';
import { loadLines, W, POS, YAW, SW, SV, add, arr, own, stamp, drawSkyGalaxy, makeLittleGalaxy, solve, pulse, walkPath } from './kit_s11_13.js';

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
    own(fx.mesh);
    const gal = makeLittleGalaxy();
    return { scene: set.scene, set, jesus, vd, user, fx, gal, look: lookFor('s12', set.look) };
  },

  async update(t, app, st) {
    stamp(t);
    const { set, jesus, vd, user, fx, gal } = st;
    for (const o of [jesus.root, vd.root, user.root, fx.mesh, gal]) st.scene.add(o);

    // ---------------------------------------------------------------- timing
    const tHand = W('s12b01', 'hand'), tVoids = W('s12b01', "void's", { alt: ['voids'] }), tShoulder = W('s12b01', 'shoulder', { frac: 0.85 });
    const wStart = T('s12') + 0.12, wEnd = tShoulder - 0.08;          // the walk; the palm lands on "shoulder"
    const tTouch = tShoulder + 0.02;
    const B2 = T('s12b02'), B3 = T('s12b03');
    const tTurn0 = B2 - 0.45, tTurn1 = B2 + 1.0;                         // the hood turns over its RIGHT shoulder
    const tSmile = B2 + 1.2, tBlinkV = B2 + 1.85;
    const tNod = B3 + 0.25, tThumb = B3 + 0.55, tBreath = B3 + 0.8, tSlide = B3 + 1.0;
    const shotA = t < B2, shotB = t >= B2 && t < B3, shotC = t >= B3;

    const wk = walkPath(t, PATH, wStart, wEnd, { ta: 0.45, td: 0.55, stride: 1.05, phase0: 0.25, yaw0: M.JM.yaw, yaw1: M.JS.yaw, turnIn: 0.4, turn: 0.55 });

    // ---------------------------------------------------------------- JESUS
    const jPose = (pass) => {
      const vEyes = vd.anchor('eyes'), vSh = vd.anchor('shoulderR');
      const ue = user.anchor('eyes');
      // the grimace melts on the exhale, then tenderness
      const Fawk = JX('awkward', { mSmile: 0.08, mAsym: 0.18, browIn: 1.2, browOut: 0.45, lidSad: 0.28, lidU: 1.16, mWide: 1.1 });
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
      const reach = k(t, [['s12', 0], [tTouch - 0.6, 0], [tTouch - 0.05, 1, 'inOut']]);
      const hover = k(t, [['s12', 0.1], [tTouch - 0.2, 0.08], [tTouch + 0.02, 0.0, 'out'], [tTouch + 0.12, -0.012, 'inOut'], [tTouch + 0.3, 0.0, 'inOut']]);
      const thumb = 0.35 + 0.4 * pulse(t, tThumb, tThumb + 0.55, 0.25, 0.3);
      const shT = vSh ? add(vSh, [0, 0.012 + hover, 0]) : null;
      // gaze: the Void as he walks round to it; its eyes when it turns; the user (eyes slide) at the end
      const vE = vEyes ? arr(vEyes) : SW(1.15, 1.8, -1.35);
      const uE = ue ? arr(ue) : SW(-1.3, 0.8, 1.4);
      const gHand = jesus.anchor('handR') ? arr(jesus.anchor('handR')) : vE;
      const gaze = k(t, [['s12', vE], [tTouch - 0.5, vE], [tTouch - 0.3, gHand, 'out'], [tTouch + 0.5, gHand], [tTurn0 + 0.6, vE, 'inOut'],
        [tSlide, vE], [tSlide + 0.22, uE, 'inOut']]);
      const nod = 0.12 * pulse(t, tNod, tNod + 0.9, 0.4, 0.45);
      return {
        pos: wk.pos, yaw: wk.yaw,
        walk: { amount: wk.amount, phase: wk.phase, style: 'walk' },
        body: { shrug, slump: 0.12 * slumpEx, breathe: shotC ? 0.7 : 1, lean: 0.05 * reach, sway: shotC ? 0.3 : 1 },
        head: { look: vE, follow: k(t, [['s12', 0.15], [wStart + 0.5, 0.55], [tSlide, 0.6], [tSlide + 0.35, 0.25, 'inOut']]), pitch: nod, roll: k(t, [['s12', 0], [tSmile, 0], [tSmile + 0.6, -0.06]]) },
        gaze: pass ? gaze : null,
        face,
        blinkAt: [T('s12') + 0.62, tTouch + 0.55, tNod + 0.3, tSlide - 0.06],
        armR: shT && reach > 0 ? { preset: 'shoulder', target: shT, palm: PALM, fingers: FING, reach, hand: { curl: 0.12, spread: 0.1, thumb, cup: 0.25 } } : { preset: 'rest' },
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
      const eyes = k(t, [['s12', gHand], [tTurn0 + 0.15, gHand], [tTurn0 + 0.75, gHand], [tTurn0 + 1.05, gJ, 'inOut']]);
      const Fsulk = VX('sad', { lidU: 0.7 });
      const Fsoft = VX('calm', { lidU: 0.62, lidL: 0.36, browIn: 0.42, browOut: -0.08, mSmile: 0.1 });
      const Fgentle = VX('gentle', { lidU: 0.6, lidL: 0.48, browIn: 0.5, mSmile: 0.62, blush: 0.3 });
      const face = k(t, [['s12', Fsulk], [tTouch, Fsulk], [tTouch + 0.8, Fsoft, 'inOut'], [tSmile - 0.1, Fsoft], [tSmile + 0.6, Fgentle, 'inOut']]);
      face.autoBlink = 0;
      return {
        pos: POS.VSIT, yaw: YAW.VSIT,
        body: { sit: 1, slump: k(t, [['s12', 0.32], [tTouch + 0.3, 0.32], [tTouch + 1.3, 0.42, 'inOut']]) - 0.12 * stiff,
          shrug: 0.32 * stiff, breathe: 1 - 0.8 * stiff, twist: -0.35 * turn, tilt: 0.05 * turn },
        head: { yaw: -1.75 * turn, pitch: lerp(0.3, -0.04, turn) - 0.08 * stiff, roll: -0.08 * turn + 0.06 * (1 - turn) },
        armL: { preset: 'crossed' }, armR: { preset: 'crossed' },
        gaze: pass && t > tTurn0 ? eyes : null,
        face,
        blinkAt: [tTurn0 + 0.7, tBlinkV],
        extra: { stars: 1.1 + 0.25 * smooth(clamp((t - tSmile) / 0.8)) },
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
        // BEHINDJ: a follow-pan from Jesus at JM (the exhale) to his back at the Void's shoulder
        const C = EDGE.CAM.BEHINDJ;
        const jl = wk.local, lead = smooth(clamp((wk.u - 0.8) / 0.22));
        const follow = [jl[0], 1.3, jl[2]];
        const lk = [lerp(follow[0], C.look[0], lead), lerp(follow[1], C.look[1], lead), lerp(follow[2], C.look[2], lead)];
        shot = EDGE.at(C.pos, lk, 33, { drift: 0.25 });
        if (globalThis.DBGA) console.log('DBGA', t.toFixed(2), JSON.stringify({ jl: jl.map((x) => +x.toFixed(2)), lk: lk.map((x) => +x.toFixed(2)), u: +wk.u.toFixed(2) }));
      } else if (shotB) {
        const lk = [VEYE_END[0] + 0.05, VEYE_END[1] - 0.04, VEYE_END[2] - 0.09];   // centre between both eyes
        shot = EDGE.shot(lk, { dist: k(t, [['s12b02', 2.75], [B2 + 1.5, 2.15, 'inOut'], ['s12b02.end', 2.05, 'inOut']]), yaw: CAMB_YAW, pitch: 4, fov: 33,
          screenY: sy(k(t, [['s12b02', 400], [B2 + 1.5, 380, 'inOut']])), drift: 0.15 });
      } else {
        shot = EDGE.shot([JEYE_JS[0] - 0.03, JEYE_JS[1], JEYE_JS[2] - 0.03], { dist: k(t, [['s12b03', 1.8], ['s12b03.end', 1.68, 'inOut']]), yaw: 137, pitch: 3, fov: 33, screenY: sy(400), drift: 0.12 });
      }
      applyShot(app.camera, shot, t, 12);
    };

    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t), voidPos: POS.VSIT,
      sunGlow: shotC ? 0.7 : 1, keyYaw: shotC ? -0.62 + 0.12 : undefined,
      clear: [[POS.U[0], POS.U[2], 0.8], [POS.VSIT[0], POS.VSIT[2], 1.4]],
    });
    solve(t, [[vd, vPose], [user, uPose], [jesus, jPose]], frameCam);
    if (globalThis.DBG12) console.log('DBG', t.toFixed(2), JSON.stringify({ ve: EDGE.L(vd.anchor('eyes')).map(x=>+x.toFixed(2)), vsh: EDGE.L(vd.anchor('shoulderR')).map(x=>+x.toFixed(2)), je: EDGE.L(jesus.anchor('eyes')).map(x=>+x.toFixed(2)), jh: EDGE.L(jesus.anchor('handR')).map(x=>+x.toFixed(2)), cam: EDGE.L(app.camera.position).map(x=>+x.toFixed(2)) }));

    // ---------------------------------------------------------------- particles: a star mote drifts up past his hand
    fx.begin();
    drawSkyGalaxy(fx, t);
    const sh = vd.anchor('shoulderR');
    if (sh) {
      const t0m = B2 + 0.55;
      const u = (t - t0m) / 2.6;
      if (u > 0 && u < 1) {
        const p = [sh.x + 0.05 * Math.sin(u * 5), sh.y + 0.08 + 0.75 * u, sh.z + 0.04 * Math.cos(u * 4)];
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
// steady the b02 framing), and the camera yaw for the 3/4 close (inside +-50 deg of where the hood points).
const VEYE_END = [1.33, 1.78, -1.12];
const CAMB_YAW = 62;
// Jesus's eyes at JS with his hand on its shoulder (stage-local, measured) — the steady look point of b03
const JEYE_JS = [1.72, 1.55, -0.53];
// the hand on the shoulder: palm down into the velvet (tilted with its slope), fingers forward over the shoulder
const PALM = (() => { const a = EDGE.W(-0.2, -0.92, -0.12), o = EDGE.W(0, 0, 0); return [a[0] - o[0], a[1] - o[1], a[2] - o[2]]; })();
const FING = (() => { const a = EDGE.W(-0.12, -0.22, -0.97), o = EDGE.W(0, 0, 0); return [a[0] - o[0], a[1] - o[1], a[2] - o[2]]; })();
