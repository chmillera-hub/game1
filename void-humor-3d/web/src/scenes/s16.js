// s16 into_the_horizon — the Void lowers its hands; Jesus steps aside to its LEFT (the camera side), it waddles up
// beside him, his RIGHT arm goes round it (as far as it goes) with a little side-squeeze and a crooked grin up at it;
// no startle this time — it leans into him, lids lowering, its own big arm settling round his shoulders — and they
// walk off down the path toward the enormous low sun (wide from behind, the galaxy it laughed up floating ahead).
// Front-3/4 tracking: "So a neutron asks the bartender, how much for a drink?" (free LEFT hand ordering at a bar,
// brows wiggle on "neutron", eyes slide up to it) — the milked pause — "For you? No charge." (deadpan, open-palm
// ta-da, the corner breaks) — a beat, its eyes go wide, mouth falls open — a snort with a spray of stars, a hand
// slapped over its mouth (he points: see?), then giggles (he tips his head back laughing, two pats on his own chest);
// he keeps telling it dumb jokes, smiling a bit. Extreme wide: two silhouettes against the sinking sun, the Void
// giggling, little stars floating up; its head leans on his. Then, far off: the user alone on the lilac hill, hood
// cinched, the phone glow on their face — the 'Unblock' button: the thumb drifts, hovers, touches, lifts away. "Not
// yet." The thumb curls away, a long breath out. "But ^maybe." — the chin lifts; over their shoulder, the two tiny
// figures walking into the huge sun. (The last frame's sun disc sits where s17 opens on Fear's lavender glow.)
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, noise1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { UX } from '../chars/user.js';
import { EDGE, todAt, voidSkyAt, sy, lookFor, frame, galaxyAt } from './marks.js';
import { loadLines, W, POS, SW, SV, add, arr, own, stamp, drawSkyGalaxy, solve, pulse, V3, toV, ramp, bump, aim, aimXY, pathPose, pathS, rollFor } from './kit_s14_16.js';
import { S15 } from './s15.js';

const M = EDGE.M;
const KP = M.K.p, VP = M.V15.p;
// the pair on the path: Jesus on the Void's RIGHT (the east side, away from the lilac hill that hugs the path's west
// side, so the tracking camera has room), his LEFT arm round it, its RIGHT arm round his shoulders; 1.2 m apart.
const SIDE_V = 0.42, SIDE_J = -0.78;
const SUN_DIR = [Math.sin(-0.14), 0, -Math.cos(-0.14)];   // edge.js SUN_AZ (horizontal)
const OVER_SUNSHIFT = 0.15;                        // last shot: nudge the sun so the far crest (and the pair) sit in front of it

export default {
  id: 's16',
  async setup(app) {
    await loadLines();
    const set = await app.set('EDGE');
    const [jesus, vd, user] = await Promise.all([app.char('JESUS'), app.char('VOID'), app.char('USER')]);
    const fx = new Particles({ max: 40, intensity: 1.5 });
    own(fx.mesh, 's16');
    const sV15 = pathS(set, POS.V15);
    const hill = [EDGE.HILL_WORLD[0], set.groundAt(EDGE.HILL_WORLD[0], EDGE.HILL_WORLD[2]), EDGE.HILL_WORLD[2]];
    { const hs = []; for (let ss = 3; ss <= 17; ss += 2) { const sm = pathPose(set, ss, -0.18); const P = [sm.pos[0] - sm.left[0] * 2.75 + sm.dir[0] * 4.75, 0, sm.pos[2] - sm.left[2] * 2.75 + sm.dir[2] * 4.75]; hs.push([ss, +sm.pos[1].toFixed(2), +set.groundAt(P[0], P[2]).toFixed(2)]); } console.log('s16 track heights', JSON.stringify(hs)); }
    console.log('s16 static', JSON.stringify({ sV15: +sV15.toFixed(2), hill, p20: set.pathAt(20).pos.map((v) => +v.toFixed(2)), p30: set.pathAt(30).pos.map((v) => +v.toFixed(2)), p40: set.pathAt(40).pos.map((v) => +v.toFixed(2)) }));
    const sCrest = set.anchors.pathFarS ?? set.crestS ?? 41;
    return { scene: set.scene, set, jesus, vd, user, fx, sV15, hill, sCrest, look: lookFor('s16', set.look) };
  },

  async update(t, app, st) {
    stamp(t, 's16');
    const { set, jesus, vd, user, fx, sV15, hill } = st;
    for (const o of [jesus.root, vd.root, fx.mesh]) st.scene.add(o);
    jesus.root.visible = vd.root.visible = true;

    // ================================================================ timing
    const S = T('s16'), E = T('s16.end');
    const B1 = T('s16b01'), B2 = T('s16b02'), B3 = T('s16b03'), B4 = T('s16b04'), B5 = T('s16b05'), B6 = T('s16b06'), B6e = T('s16b06.end');
    const B10 = T('s16b10'), B11 = T('s16b11'), B13 = T('s16b13'), B7 = T('s16b07'), B8 = T('s16b08'), B9 = T('s16b09');
    const tArm = W('s16b01', 'arm', { frac: 0.22 }), tAround = W('s16b01', 'around', { frac: 0.28 }), tVoid1 = W('s16b01', 'void', { alt: ['void,'], frac: 0.4 });
    const tWalk = W('s16b01', 'walk', { frac: 0.6 }), tHorizon = W('s16b01', 'horizon', { alt: ['horizon.'], frac: 0.88 });
    const tNeutron = W('s16b02', 'neutron', { frac: 0.1 }), tBartender = W('s16b02', 'bartender', { frac: 0.3 }), tHow = W('s16b02', 'how', { frac: 0.5 }), tDrink = W('s16b02', 'drink', { alt: ['drink.', 'drink?'], frac: 0.85 });
    const tYou = W('s16b04', 'you', { alt: ['you?'], frac: 0.1 }), tNo = W('s16b04', 'no', { frac: 0.45 }), tCharge = W('s16b04', 'charge', { alt: ['charge.'], frac: 0.66 });
    const tChargeE = W('s16b04', 'charge', { alt: ['charge.'], end: true, frac: 0.8 });
    const tSmiling = W('s16b10', 'smiling', { frac: 0.25 }), tTelling = W('s16b10', 'telling', { frac: 0.55 }), tJokes = W('s16b10', 'jokes', { alt: ['jokes,', 'jokes.'], frac: 0.85 });
    const tNot = W('s16b09', 'not', { frac: 0.02 }), tBut = W('s16b09', 'but', { frac: 0.55 }), tMaybe = W('s16b09', 'maybe', { alt: ['maybe.'], frac: 0.7 });
    // b01 choreography
    const tRel = S + 0.05;                                         // the Void's hands come down
    const tStep0 = S + 0.22, tStep1 = Math.min(tArm - 0.05, tStep0 + 1.0);   // Jesus steps aside + turns down the path
    const tV0 = S + 0.5, tV1 = tArm + 0.1;                         // the Void waddles up beside him
    const tHug0 = tArm - 0.08, tHug1 = tAround + 0.25;             // his RIGHT arm goes round it
    const tSqueeze = tVoid1 - 0.05;                                // side-squeeze
    const tLean0 = tVoid1 + 0.05, tLean1 = tLean0 + 0.6;           // it leans into him, its arm round his shoulders
    const tW0 = Math.min(tWalk - 0.25, tLean1 + 0.1);              // they start walking
    // b04-b06 beats
    const tTada = tCharge - 0.05, tBreak = tChargeE + 0.12, tWide = tChargeE + 0.32, tDrop = tWide + 0.3;
    const tSnort = B5 + 0.03, tSlap = tSnort + 0.06, tPoint = tSnort + 0.18;
    const tLaugh = B6 + 0.05, tPat1 = B6 + 0.55, tPat2 = tPat1 + 0.3;

    // ================================================================ shot list
    const SHOTS = [[S, 'TWO'], [tWalk - 0.06, 'BACK'], [B2 - 0.12, 'TRACK'], [B11 - 0.1, 'FAR'], [B7, 'XWIDE'], [B8, 'PHONE'], [B9, 'UCU'], [tMaybe - 0.12, 'OVER']];
    let si = 0; for (let i = 0; i < SHOTS.length; i++) if (t >= SHOTS[i][0]) si = i;
    const shot = SHOTS[si][1], shotT0 = SHOTS[si][0], shotT1 = SHOTS[si + 1] ? SHOTS[si + 1][0] : E + 0.5;
    const userOn = shot === 'XWIDE' || shot === 'PHONE' || shot === 'UCU' || shot === 'OVER';
    if (userOn) { st.scene.add(user.root); user.root.visible = true; } else st.scene.remove(user.root);

    // ================================================================ the pair's walk (pure)
    const sStart = sV15 + 1.1;                                     // formation point (the Void's path station)
    const v = 1.0;
    // "...in the distance": at the cut to the extreme wide the walk jumps on (time has passed): from then on they walk
    // the far stretch up to the crest, in front of the sun (the set's finale alignment), at the same unhurried pace
    const tFar = B11 - 0.1;
    const speed = (x) => (x <= tW0 ? 0 : v * ramp(x, tW0, tW0 + 0.7));
    const base = (x) => { const tau = x - tW0; if (tau <= 0) return 0; if (tau < 0.7) { const u = tau / 0.7; return v * 0.7 * (u * u * u - 0.5 * u * u * u * u); } return v * (tau - 0.35); };
    const sFar0 = (st.sCrest - 8.2) - sStart;
    const travelled = (x) => (x < tFar ? base(x) : sFar0 + v * (x - tFar));
    const dist = travelled(t);
    const sNow = sStart + dist;
    const pV = pathPose(set, sNow, SIDE_V), pJ = pathPose(set, sNow, SIDE_J);
    const walkAmt = clamp(speed(t) / v);
    // pre-walk: from s15's marks into the formation
    const v15 = EDGE.W(VP), vYaw15 = EDGE.Y(S15.VY), jK = EDGE.W(KP), jYawK = EDGE.Y(S15.JY1);
    const fV = pathPose(set, sStart, SIDE_V), fJ = pathPose(set, sStart, SIDE_J);
    const unwrap = (a, ref) => { while (a - ref > Math.PI) a -= 2 * Math.PI; while (a - ref < -Math.PI) a += 2 * Math.PI; return a; };
    // Void: waddles 1.1 m forward into the formation
    const uV = ramp(t, tV0, tV1);
    const vPos = t < tW0 ? lerpA(v15, fV.pos, uV) : pV.pos;
    const vYaw = t < tW0 ? lerp(vYaw15, unwrap(fV.yaw, vYaw15), ramp(t, tV0, tV1 - 0.2)) : unwrap(pV.yaw, vYaw15);
    const vPhasePre = (uV * Math.hypot(fV.pos[0] - v15[0], fV.pos[2] - v15[2])) / 0.76;
    const vPhase = vPhasePre + dist / 0.76;
    const vAmt = Math.max(walkAmt, 0.85 * pulse(t, tV0, tV1 + 0.1, 0.2, 0.3));
    // Jesus: sidestep + turn (decreasing yaw: his face sweeps past the camera) into the formation
    const uJ = ramp(t, tStep0, tStep1);
    const jPos = t < tW0 ? lerpA(jK, fJ.pos, uJ) : pJ.pos;
    let jYaw1 = fJ.yaw; while (jYaw1 < jYawK) jYaw1 += 2 * Math.PI; while (jYaw1 > jYawK + 2 * Math.PI) jYaw1 -= 2 * Math.PI;
    const jYaw = t < tW0 ? lerp(jYawK, jYaw1, ramp(t, tStep0 - 0.05, tStep1 + 0.05)) : unwrap(pJ.yaw, jYaw1);
    const jPhasePre = (uJ * Math.hypot(fJ.pos[0] - jK[0], fJ.pos[2] - jK[2])) / 1.05;
    const jPhase = jPhasePre + dist / 1.05;
    const jAmt = Math.max(walkAmt, 0.6 * pulse(t, tStep0, tStep1 + 0.1, 0.2, 0.3));
    const mid = lerpA(vPos, jPos, 0.42);
    const fwd = t < tW0 ? fV.dir : pV.dir, left = t < tW0 ? fV.left : pV.left;

    // ================================================================ JESUS
    const jPose = (pass) => {
      const ve = vd.anchor('eyes');
      const vE = ve ? arr(ve) : add(vPos, [0, 2.0, 0]);
      // ---- face
      const Fgrin = JX('beam', { mSmile: 0.92, mOpen: 0.12, lidL: 0.55, lidU: 0.74 });
      const Fcrook = JX('amused', { mSmile: 0.75, mAsym: 0.6, lidU: 0.84, lidL: 0.42, browIn: 0.3, browOut: 0.45, browAsym: 0.4 });
      const Fwarm = JX('warm', { mSmile: 0.6, lidU: 0.86 });
      const Fsetup = JX('amused', { mSmile: 0.45, mAsym: 0.3, lidU: 0.95, browIn: 0.4, browOut: 0.55 });
      const Fwig = JX('amused', { mSmile: 0.5, mAsym: 0.3, lidU: 1.05, browIn: 0.85, browOut: 1.0 });
      const Fmilk = JX('pressed', { mPress: 0.9, mSmile: 0.3, browIn: 0.7, browOut: 0.85, lidU: 1.02, lidL: 0.2, blush: 0.05 });
      const Fdead = JX('kind', { mSmile: 0.05, mPress: 0.25, lidU: 0.78, lidL: 0.1, browIn: 0.3, browOut: 0.35 });
      const Fbreak = JX('pressed', { mPress: 0.6, mSmile: 0.62, mAsym: 0.55, lidU: 0.8, lidL: 0.4, browIn: 0.4, browOut: 0.5 });
      const Fsee = JX('beam', { mSmile: 1, mOpen: 0.2, lidL: 0.5, lidU: 0.9, browIn: 0.5, browOut: 0.7 });
      const Flaugh = JX('laugh', { mOpen: 0.6 });
      const Fsmile = JX('content', { mSmile: 0.55, mPress: 0.3, lidU: 0.72, lidL: 0.42, browIn: 0.2, browOut: 0.25 });
      const Fnext = JX('amused', { mSmile: 0.5, mPress: 0.25, lidU: 0.92, lidL: 0.3, browIn: 0.55, browOut: 0.7 });
      const face = k(t, [['s16', Fgrin], [tStep0 + 0.3, Fgrin], [tStep1, Fwarm, 'inOut'], [tSqueeze - 0.05, Fwarm], [tSqueeze + 0.15, Fcrook, 'out'],
        [tW0 + 0.6, Fcrook], [tW0 + 1.4, Fwarm, 'inOut'],
        [B2 - 0.2, Fwarm], [B2, Fsetup, 'inOut'], [tNeutron - 0.05, Fsetup], [tNeutron + 0.1, Fwig, 'out'], [tNeutron + 0.5, Fsetup, 'inOut'],
        [B3 - 0.05, Fsetup], [B3 + 0.15, Fmilk, 'out'], [B4 - 0.05, Fmilk], [B4 + 0.1, Fdead, 'inOut'],
        [tBreak - 0.02, Fdead], [tBreak + 0.2, Fbreak, 'out'],
        [tSnort, Fbreak], [tSnort + 0.12, Fsee, 'out'], [tLaugh, Fsee], [tLaugh + 0.15, Flaugh, 'out'], [B6e - 0.2, Flaugh], [B6e + 0.3, Fsmile, 'inOut'],
        [tTelling - 0.3, Fsmile], [tTelling - 0.1, Fnext, 'inOut'], [tJokes + 0.3, Fnext], [tJokes + 0.6, Fsmile, 'inOut']]);
      face.autoBlink = 1;
      // a quiet murmur while the narrator says "telling it more dumb jokes" (the next setup, sotto voce)
      const mur = pulse(t, tTelling - 0.2, tJokes + 0.45, 0.2, 0.25);
      const speech = mur > 0.01 ? { open: mur * (0.08 + 0.07 * Math.max(0, Math.sin(t * 11.3) * Math.sin(t * 3.7 + 1))), wide: 0.25, round: 0.2 * mur, close: 0 } : undefined;
      // ---- head: up at the Void; tips back for the laugh; toward its shoulder in the distance
      const laugh = pulse(t, tLaugh, B6e + 0.1, 0.15, 0.4);
      const wiggle = 0.06 * bump(t, tNeutron - 0.02, 0.3);
      const leanIn = ramp(t, B11 + 0.2, B13);
      const jab = 0.05 * bump(t, tTada - 0.05, 0.25);
      // ---- arms: LEFT round the Void; RIGHT (camera side) free: ordering at a bar, the ta-da, the point, two chest pats, sketching
      const hug = ramp(t, tHug0, tHug1);
      const squeeze = bump(t, tSqueeze, 0.35);
      const armL = { preset: hug > 0.001 ? 'around' : 'rest', surface: hug > 0.001 ? vd : undefined, reach: hug > 0.001 ? hug : 1,
        target: hug > 0.001 && pass ? add(arr(vd.anchor('backLow') || V3(...vPos)), [0, 0.42, 0]) : undefined, offset: [0, -0.02 * squeeze, 0] };
      const order = pulse(t, B2 + 0.1, tDrink + 0.35, 0.3, 0.35);            // palm out "ordering at a bar"
      const tada = pulse(t, tTada - 0.12, tTada + 0.7, 0.12, 0.35);
      const point = pulse(t, tPoint - 0.08, tPoint + 0.65, 0.1, 0.3);
      const chest = pulse(t, tPat1 - 0.18, tPat2 + 0.3, 0.15, 0.25);
      const sketch = pulse(t, tTelling - 0.4, tJokes + 0.5, 0.3, 0.4) + 0.8 * pulse(t, B11 + 0.6, B11 + 1.8, 0.3, 0.4);
      const busy = clamp(order + tada + point + chest + sketch);
      let armR = { preset: [['rest', Math.max(1e-3, 1 - busy)], ['explain', Math.max(1e-3, order + sketch)], ['open', Math.max(1e-3, tada)], ['point', Math.max(1e-3, point)], ['heart', Math.max(1e-3, chest)]],
        gesture: 1 + 0.5 * order, hand: tada > 0.5 ? { curl: 0.05, spread: 0.45, thumb: 0.7, splay: 0.1 } : undefined };
      if (pass && sketch > 0.01) {   // the free hand draws a little shape in the air mid-joke
        const a = (t - tTelling) * 4.2;
        armR.offset = SV(0.05 * Math.sin(a) * sketch, 0.04 * Math.sin(2 * a) * sketch, 0);
      }
      if (pass && point > 0.01) {    // point at the Void's face
        const hl = jesus.anchor('handR');
        if (hl) { const d = toV(vE).sub(hl).normalize(); armR.fingers = d.toArray(); }
      }
      if (chest > 0.01) armR.offset = [0, -0.025 * (bump(t, tPat1 - 0.06, 0.14) + bump(t, tPat2 - 0.06, 0.14)), 0];
      return {
        pos: jPos, yaw: jYaw,
        walk: { amount: jAmt, phase: jPhase, style: 'walk' },
        body: { lean: 0.02, tilt: 0.03 + 0.04 * leanIn + 0.05 * squeeze, shrug: 0.12 * laugh * (0.5 + 0.5 * Math.sin(t * 2 * Math.PI * 4.2)) + 0.05 * squeeze, recoil: 0.18 * laugh,
          bounce: 0.008 * laugh * Math.sin(t * 2 * Math.PI * 4.2), breathe: 1 },
        head: { look: pass ? vE : undefined, follow: 0.62 - 0.25 * laugh, pitch: -0.28 * laugh + jab - 0.02, roll: 0.06 + wiggle + 0.12 * leanIn, talk: 0.8 },
        gaze: pass ? (laugh > 0.5 ? add(vE, [0, 0.6, 0]) : vE) : null,
        face,
        speech,
        blinkAt: [tStep1 + 0.05, tSqueeze + 0.4, B3 + 0.1, tBreak + 0.35, B6e + 0.2, tTelling - 0.35, B11 + 0.5],
        armL, armR,
        glow: 1 + 0.2 * ramp(t, B11 - 0.2, B11 + 0.3),
      };
    };

    // ================================================================ VOID
    const vPose = (pass) => {
      const je = jesus.anchor('eyes');
      const jE = je ? arr(je) : add(jPos, [0, 1.55, 0]);
      const Fcrinkle = VX('giggle', { lidU: 0.3, lidL: 1, mOpen: 0.08, mSmile: 1, blush: 0.45 });
      const Fcontent = VX('gentle', { mSmile: 0.6, lidU: 0.5, lidL: 0.5, browIn: 0.55, blush: 0.35 });
      const Feager = VX('hopeful', { lidU: 1.18, lidL: 0.05, browIn: 0.8, browOut: 0.55, mSmile: 0.45, mOpen: 0.04, mRound: 0.15, pupil: 1.2 });
      const Fwait = VX('hopeful', { lidU: 1.2, browIn: 0.85, browOut: 0.65, mSmile: 0.2, mPress: 0.75, mWide: 0.35, pupil: 1.25 });
      const Fwide = VX('surprised', { lidU: 1.38, browIn: 0.85, browOut: 0.85, mOpen: 0.05, mRound: 0.2, mSmile: 0.15 });
      const Fopen = VX('surprised', { lidU: 1.3, browIn: 0.8, browOut: 0.8, mOpen: 0.55, mRound: 0.4, mSmile: 0.3 });
      const Fsnort = VX('laugh', { lidU: 0.15, lidL: 1, mOpen: 0.3, mSmile: 0.95, blush: 0.5 });
      const Fgig = VX('giggle', { lidU: 0.28, lidL: 1, mOpen: 0.35, mSmile: 1, blush: 0.5 });
      const Fbend = VX('happy', { mSmile: 0.75, lidU: 0.6, lidL: 0.7, browIn: 0.5, blush: 0.35 });
      const face = k(t, [['s16', Fcrinkle], [S + 0.6, Fcrinkle], [S + 1.2, Fcontent, 'inOut'], [tLean0, Fcontent], [tLean1, VX('gentle', { mSmile: 0.7, lidU: 0.42, lidL: 0.55, browIn: 0.5, blush: 0.4 }), 'inOut'],
        [B2 - 0.3, Fcontent], [B2 + 0.3, Feager, 'inOut'], [B3 - 0.05, Feager], [B3 + 0.15, Fwait, 'out'],
        [tChargeE + 0.05, Fwait], [tWide, Fwide, 'out'], [tDrop - 0.05, Fwide], [tDrop + 0.12, Fopen, 'out'],
        [tSnort - 0.03, Fopen], [tSnort + 0.06, Fsnort, 'out'], [B6, Fsnort], [B6 + 0.2, Fgig, 'inOut'],
        [B6e + 0.1, Fgig], [B6e + 0.6, Fbend, 'inOut'], [B11, Fbend], [B11 + 0.3, Fgig, 'inOut']]);
      face.autoBlink = 1;
      // ---- body: no startle — it leans into him; bends its hood toward him while he talks; giggles bob the shoulders
      const leanIn = ramp(t, tLean0, tLean1);
      const bend = ramp(t, B2 - 0.2, B2 + 0.8) * (1 - 0.4 * ramp(t, B11 - 0.5, B11 + 0.5));
      const gig = pulse(t, B6, B6e + 0.2, 0.15, 0.4) + 0.7 * pulse(t, B11 + 0.3, B13 + 0.3, 0.3, 0.6);
      const snort = bump(t, tSnort - 0.02, 0.24);
      const headOn = ramp(t, B13 - 0.4, B13 + 0.5);                                 // its head leans against his
      const handsDown = ramp(t, tRel, tRel + 0.4);
      // ---- arms: RIGHT round his shoulders (the 'around' contact on him; first down from s15's hand over the mouth);
      //      LEFT: s15's hand on his shoulder lifting off, later slapped over the mouth on the snort
      const around = ramp(t, tLean0, tLean1 + 0.1);
      const cov0 = 1 - handsDown;
      let armR = { preset: 'cover_mouth', from: 'rest', mix: cov0, offset: [0, 0.14 * cov0, 0] };
      if (around > 0.001) armR = { preset: 'around', on: jesus, reach: around, handScale: 0.62 };
      let armL = { preset: 'rest' };
      if (handsDown < 1) {                    // s15's hand on the outside of his right shoulder, lifting off
        const shR = jesus.anchor('shoulderR');
        if (shR) {
          const jr = [-Math.cos(jYaw), 0, Math.sin(jYaw)], jb = [-Math.sin(jYaw), 0, -Math.cos(jYaw)];
          const tg = add(arr(shR), [jr[0] * 0.07 + jb[0] * 0.02, -0.06 + 0.08 * handsDown, jr[2] * 0.07 + jb[2] * 0.02]);
          armL = { preset: 'pat', target: tg, reach: 1 - handsDown, palm: [-jr[0], -0.25, -jr[2]], fingers: V3(jb[0] * 0.9, 0.42, jb[2] * 0.9).normalize().toArray(),
            pole: [jr[0] * 0.3, -1, jr[2] * 0.3], handScale: 0.66, hand: { curl: 0.22, cup: 0.55, spread: 0.14, thumb: 0.3 } };
        }
      }
      const slap = ramp(t, tSlap - 0.05, tSlap + 0.08, (u) => 1 - Math.pow(1 - u, 3)) * (1 - ramp(t, B6e + 0.2, B6e + 0.7));
      if (slap > 0.001) armL = { preset: 'cover_mouth', from: 'rest', mix: slap, offset: [0, 0.14 * slap, 0] };
      return {
        pos: vPos, yaw: vYaw,
        walk: { amount: vAmt, phase: vPhase, style: 'waddle' },
        body: { lean: 0.08 + 0.08 * bend, tilt: -(0.12 * leanIn + 0.06 * bend + 0.05 * headOn), twist: -0.1 * bend, shrug: 0.22 * gig * (0.5 + 0.5 * Math.sin(t * 2 * Math.PI * 4.6)) + 0.15 * snort,
          recoil: 0.07 * snort, breathe: 1.05 },
        head: { yaw: -(0.35 + 0.15 * bend) * ramp(t, tV0, tLean1) + 0.45 * (1 - ramp(t, tV0, tLean1)), pitch: 0.18 + 0.1 * bend, roll: -(0.1 * leanIn + 0.12 * headOn), track: 0 },
        gaze: pass ? jE : null,
        face,
        blinkAt: [S + 0.8, B3 + 0.5, B6e + 0.4],
        armL, armR,
        extra: { rim: lerp(1.1, 1.8, ramp(t, B11 - 0.2, B11 + 0.2)), eyeGlow: lerp(1, 1.25, ramp(t, B11 - 0.2, B11 + 0.2)), motes: 1 + 0.6 * gig },
      };
    };

    // ================================================================ USER (on the lilac hill)
    const uYaw = Math.atan2(0.3, -0.95);
    const uPose = (pass) => {
      const pE = add(vPos, [0, 1.6, 0]);
      const phs = user.anchor('phoneScreen');
      const phS = phs ? arr(phs) : add(hill, [0.1, 0.8, -0.3]);
      const Fwatch = UX('notquite', { mSmile: 0.0, lidU: 0.9, browIn: 0.55, wet: 0.7 });
      const Fphone = UX('soften', { lidU: 0.86, mOpen: 0.02, mTremble: 0.15, wet: 0.8 });
      const Ftorn = UX('tremble', { mTremble: 0.4, wet: 0.9 });
      const Fexh = UX('guilt', { lidU: 0.6, mOpen: 0.06, wet: 0.8 });
      const Fmaybe = UX('notquite', { mSmile: 0.3, browIn: 0.65, lidU: 1.02, lidL: 0.3, wet: 0.95, mTremble: 0.3, pupil: 1.15 });
      const face = k(t, [['s16b07', Fwatch], [B7 + 0.7, Fwatch], [B7 + 1.1, Fphone, 'inOut'], [B8 + 0.6, Fphone], [B8 + 1.2, Ftorn, 'inOut'],
        [tNot + 0.2, Ftorn], [tNot + 0.6, Fexh, 'inOut'], [tBut - 0.15, Fexh], [tBut + 0.3, Fmaybe, 'inOut']]);
      face.autoBlink = 1;
      const look = ramp(t, B7 + 0.75, B7 + 1.05) * (1 - ramp(t, tBut - 0.25, tBut + 0.05));
      const gaze = pass ? lerpA(pE, phS, look) : null;
      // thumb: drifts toward Unblock, hovers trembling, touches lightly (4 frames), lifts away before it registers
      const hov = ramp(t, B8 + 0.3, B8 + 0.9) * (1 - ramp(t, tNot + 0.05, tNot + 0.4));
      const touch = bump(t, B8 + 1.35, 4 / 24) * 0.6;
      const lift = ramp(t, B8 + 1.55, B8 + 1.8);
      const tAt = [lerp(0.66, 0.5, ramp(t, B8 + 0.3, B8 + 1.1)) + 0.004 * Math.sin(t * 41) * hov, lerp(0.86, 0.745, ramp(t, B8 + 0.3, B8 + 1.1)) - 0.05 * lift + 0.003 * Math.sin(t * 37 + 1) * hov];
      const lower = ramp(t, tNot + 0.15, tNot + 0.65);
      const chin = ramp(t, tBut - 0.2, tBut + 0.35);
      const breath = pulse(t, tNot + 0.3, tBut, 0.3, 0.5);
      return {
        pos: hill, yaw: uYaw,
        body: { sit: 1, sitPath: 'plain', scoot: 1, scootPhase: 0.45, lean: 0.34 - 0.12 * chin, hunch: 0.45, slump: 0.25 + 0.15 * breath, breathe: 1 + 0.8 * breath, breathRate: 0.18 },
        head: { pitch: 0.18 + 0.12 * look - 0.22 * chin, yaw: 0, roll: 0 },
        gaze,
        face,
        blinkAt: [B7 + 0.62, B8 + 1.6, tNot + 0.35, tBut + 0.05],
        armL: { preset: [['hold', 1]], offset: [0, -0.06 * lower, 0] },
        armR: { preset: 'knee' },
        extra: { phone: 0.9, screen: 'blocked', phoneUp: 0.35 * (1 - lower), thumb: hov, tap: touch > 0.001 ? touch : undefined, thumbAt: tAt, hood: 1, glow: 1.15 },
      };
    };

    // ================================================================ cameras
    const cam = () => {
      let s;
      const ve = vd.anchor('eyes'), je = jesus.anchor('eyes');
      const vE = ve ? arr(ve) : add(vPos, [0, 2.0, 0]), jE = je ? arr(je) : add(jPos, [0, 1.55, 0]);
      switch (shot) {
        case 'TWO': {   // medium two-shot from the front (down the path, the low sun behind the lens lighting them)
          const fm = pathPose(set, sStart, -0.45);
          const P = add(fm.pos, [fm.dir[0] * 5.3 + fm.left[0] * 0.2, 1.45, fm.dir[2] * 5.3 + fm.left[2] * 0.2]);
          s = aim(P, add(fm.pos, [0, 1.85, 0]), 380, 36, { drift: 0.12 });
          break;
        }
        case 'BACK': {  // wide from behind them down the path to the huge low sun; they walk away from us
          const c0 = pathPose(set, sStart - 6.4, -1.6);
          const u = ramp(t, shotT0, shotT1);
          s = aimXY(add(c0.pos, [0, 2.15 + 0.1 * u, 0]), add(lerpA(vPos, jPos, 0.5), [0, 1.7, 0]), 280, 590, 50, { drift: 0.2 });
          break;
        }
        case 'TRACK': { // front-3/4 tracking medium from their left (camera side), the low sun lighting their faces
          const sm = pathPose(set, sNow, -0.18);
          const P = add(sm.pos, [-sm.left[0] * 2.75 + sm.dir[0] * 4.75, 1.45, -sm.left[2] * 2.75 + sm.dir[2] * 4.75]);
          P[1] = Math.max(P[1], set.groundAt(P[0], P[2]) + 1.25);       // (never inside the terrain)
          const L = add(sm.pos, [sm.left[0] * 0.05, 1.85, sm.left[2] * 0.05]);
          s = aim(P, L, 400, 37, { drift: 0.12 });
          break;
        }
        case 'FAR': {   // extreme wide from behind (the set's finale lens): two silhouettes in front of the low sun's disc,
          //              a very slow push that comes to rest
          const F = set.shots.finale;
          const u = ramp(t, shotT0, B13 + 0.4, (x) => 1 - Math.pow(1 - x, 2));
          if (F) s = { pos: F.pos.map((x, i) => lerp(x, F.look[i], 0.05 * u)), look: F.look, fov: F.fov, drift: 0.05 };
          else {
            const ref = pathPose(set, sNow, 0);
            const P = [ref.pos[0] - SUN_DIR[0] * 40, ref.pos[1] + 1.25, ref.pos[2] - SUN_DIR[2] * 40];
            s = aim(P, add(ref.pos, [0, 1.5, 0]), 540, 20, { drift: 0.05 });
          }
          break;
        }
        case 'XWIDE': s = { pos: [1.15, 2.1, 3.6], look: [-1.95, 1.05, -15.5], fov: 44, drift: 0 }; break;
        case 'PHONE': {
          const ph = user.anchor('phoneScreen');
          if (ph) {
            user.phone.updateWorldMatrix(true, false);
            const n = V3(0, 0, 1).transformDirection(user.phone.matrixWorld), up = V3(0, 1, 0).transformDirection(user.phone.matrixWorld);
            const xr = V3(1, 0, 0).transformDirection(user.phone.matrixWorld);
            const cp = ph.clone().addScaledVector(n, 0.25).addScaledVector(up, -0.035).addScaledVector(xr, 0.05);
            const look = ph.clone().addScaledVector(up, -0.012);
            s = { pos: cp.toArray(), look: look.toArray(), fov: 38, drift: 0, roll: rollFor(cp, look, up) };
          } else s = { pos: add(hill, [0, 1.2, -0.8]), look: add(hill, [0, 0.6, 0]), fov: 40 };
          break;
        }
        case 'UCU': {   // close on the user from the sunward side (front-lit by the low sun)
          const ue = user.anchor('eyes');
          const U = ue ? arr(ue) : add(hill, [0, 0.85, 0]);
          const fwU = [Math.sin(uYaw), 0, Math.cos(uYaw)];
          const P = add(U, [fwU[0] * 1.4 - fwU[2] * 0.22, -0.1, fwU[2] * 1.4 + fwU[0] * 0.22]);
          s = aim(P, U, 430, 33, { drift: 0.08 });
          break;
        }
        case 'OVER': {  // over the user's shoulder, down to the two tiny figures topping the far crest into the huge sun;
          //               the sun disc lands where s17 opens on Fear's lavender glow (~ (330, 610))
          const ue = user.anchor('eyes');
          const U = ue ? arr(ue) : add(hill, [0, 0.85, 0]);
          const fwU = [Math.sin(uYaw), 0, Math.cos(uYaw)], lfU = [Math.cos(uYaw), 0, -Math.sin(uYaw)];
          const P = add(U, [-fwU[0] * 0.72 + lfU[0] * 0.2, 0.12, -fwU[2] * 0.72 + lfU[2] * 0.2]);
          const el = lerp(6.2, 0.6, todAt(t)) * Math.PI / 180, az = -0.14 + OVER_SUNSHIFT;
          const sunPt = add(P, [Math.sin(az) * Math.cos(el) * 200, Math.sin(el) * 200, -Math.cos(az) * Math.cos(el) * 200]);
          s = aimXY(P, sunPt, 315, 610, 38, { drift: 0.03 });
          break;
        }
        default: s = EDGE.cam('MASTER');
      }
      applyShot(app.camera, s, t, 16);
    };

    const list = [[jesus, jPose], [vd, vPose]];
    if (userOn) list.push([user, uPose]);
    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t), voidPos: vPos,
      shadowAt: lerpA(vPos, jPos, 0.5),
      sunGlow: shot === 'FAR' || shot === 'OVER' ? 1 : shot === 'BACK' ? 0.9 : 1, sunShift: shot === 'OVER' ? OVER_SUNSHIFT : 0,
      keyYaw: shot === 'UCU' || shot === 'PHONE' ? -0.05 : undefined, fillMul: shot === 'UCU' ? 1.25 : 1,
      ...(shot === 'FAR' && set.shots.finale && set.shots.finale.opts ? { silhouette: 1, keyYaw: 0, keyElev: 5, seeds: 0.5, shadowAt: set.shots.finale.opts.shadowAt } : {}),
      clear: [[jPos[0], jPos[2], 0.6], [vPos[0], vPos[2], 1.2]],
    });
    solve(t, list, cam);
    if (shot === 'PHONE') cam();                 // the insert rides on the final phone pose

    // ---- particles: the snort's spray of stars; little stars floating up while it giggles in the distance
    const mo = vd.anchor('mouth'), md = vd.mouthDir(), top = vd.anchor('hoodTop');
    fx.begin();
    drawSkyGalaxy(fx, t);
    if (mo) {
      fx.burst({ t, seed: 1601, at: tSnort + 0.04, count: 7, life: 0.9, jitter: 0.06, origin: add(arr(mo), [md.x * 0.14, 0.12, md.z * 0.14]),
        vel: [md.x * 0.5, 0.55, md.z * 0.5], spread: [0.3, 0.25, 0.3], gravity: [0, -0.4, 0], drag: 1.6, size: [0.035, 0.07], grow: 0.5,
        color: [0xfff1c8, 0xd8c0ff, 0xbfe8ff], alpha: 0.95, fade: [0.05, 0.5], cell: CELL.star, spin: 2 });
    }
    if (top) {
      for (const [a, b, sd] of [[B6, B6e, 1602], [B11, B13 + 0.6, 1603]]) {
        fx.stream({ t, seed: sd, t0: a, t1: b, rate: 2.2, life: 2.6, origin: (tb) => add(arr(top), [0.25 * Math.sin(tb * 7.1), -0.25, 0.25 * Math.cos(tb * 5.3)]),
          vel: [0, 0.38, 0], spread: [0.08, 0.06, 0.08], drag: 0.2, size: [0.05, 0.09], grow: 0.6, color: [0xfff1c8, 0xd8c0ff], alpha: 0.85,
          fade: [0.15, 0.5], cell: CELL.star, spin: 0.8, wobble: 0.05, twinkle: true });
      }
    }
    fx.end();
    st.look = lookFor('s16', set.look);
    if (shot === 'FAR' && set.shots.finale && set.shots.finale.post) st.look = { ...st.look, ...set.shots.finale.post };
  },
};

function lerpA(a, b, u) { const A = arr(a), B = arr(b); return [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u]; }
