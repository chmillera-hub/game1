// s16 into_the_horizon — STAGING side: Jesus walks on the Void's LEFT (the hill side of the path), his RIGHT arm round
// its flank (as far as it goes), its LEFT arm round his shoulders (the forearm draped behind his neck, the big palm on
// top of his far shoulder, fingers over its front).
//   TWO   front-3/4 two-shot from Jesus's open side (down the path, the hill side), a little high, orbiting in and
//         pushing: its hand comes down from its snort-covered mouth; Jesus turns and steps round to its left; "arm
//         around": his RIGHT arm reaches round its flank (the forearm and hand show past his back), a side-squeeze
//         (its body squishes a few %, his head tilts into it), a crooked grin up at it; no startle: it leans in, lids
//         lowering, its arm settles round him; on "walk off" they step off toward the lens and screen-left (the
//         camera backs down the path at half their pace). Every walk-and-talk angle is from the front / camera side
//         (Jesus screen-right); FAR is the one front -> back flip, into the sunset silhouettes.
//   TRACK dead-front tracking medium (camera backing up the path ahead of them; no hill in the way): "So a neutron
//         asks the bartender..." (free LEFT hand ordering at a bar, brows wiggle on "neutron", eyes slide up to it;
//         the Void bends its hood toward him) — the milked pause: they slow to a stop.
//   JCU   standing, half-turned to it: "For you? No ^charge." deadpan, a little open-palm ta-da, the corner breaks.
//   REACT tighter two-shot: its eyes go wide, mouth falls open; a snort with a spray of stars, a hand slapped over its
//         mouth; he points (see?), head back laughing, two pats on his own chest; giggles.
//   TRACK2 they walk on: the closed-mouth smile, the free hand sketching the next setup, a murmur under the narration.
//   FAR   the set's finale recipe (all of it): silhouettes crossing the sun disc at the crest, the galaxy above them,
//         stars floating up from the giggling hood; its head leans against his; the push comes to rest.
//   XWIDE the user tiny on the lilac hill (upper left), the pair tiny on the far crest in front of the sun.
//   PHONE the Unblock insert (a big central button): the thumb drifts, hovers below it, touches for 4 frames, lifts.
//   UCU   front-lit close: "Not yet." the phone lowers, a long breath out; "But ^maybe." the chin lifts into the
//         not-quite smile, held; then OVER: over their hood down to the two tiny figures walking into the huge sun
//         (the disc where s17 opens on Fear's lavender glow).
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';
import { UX } from '../chars/user.js';
import { EDGE, todAt, voidSkyAt, lookFor, galaxyAt, galaxySpin } from './marks.js';
import { loadLines, W, add, arr, own, stamp, solve, pulse, V3, toV, ramp, bump, aimXY, pathPose, pathS, rollFor, hideDuring } from './kit_s14_16.js';
import { S15, voidPos15 } from './s15.js';

const M = EDGE.M;
const SIDE_J = 0.62, SIDE_V = -0.62;          // metres left (+) of the path: Jesus on the hill side, the Void on the other
const S0 = 0.3;                                // formation path station (pair midpoint)
const V_WALK = 0.62;                           // an easy stroll (m/s)
const UHILL = [-3.0, 0, -10.5];                // the user's seat on the lilac hill's broad top (x, -, z)
const OVER_SHIFT = 0.15;                       // sun azimuth cheat in the user's shots (the pair walks into the disc)

// unblock screen (generic social app, no logos): a large central Unblock button (canvas 320 x 690 like the rig's screens)
function unblockCanvas() {
  const Wc = 320, Hc = 690, c = document.createElement('canvas'); c.width = Wc; c.height = Hc;
  const g = c.getContext('2d');
  const rr = (x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
  g.fillStyle = '#eef1f5'; g.fillRect(0, 0, Wc, Hc);
  g.fillStyle = '#f7f8fb'; g.fillRect(0, 0, Wc, 70);
  g.fillStyle = '#6f8fd8'; rr(Wc / 2 - 15, 34 - 11, 30, 20, 8); g.fill();
  g.beginPath(); g.moveTo(Wc / 2 - 7, 41); g.lineTo(Wc / 2 - 10, 50); g.lineTo(Wc / 2, 42); g.fill();
  g.fillStyle = '#d8dde5'; g.fillRect(0, 68, Wc, 2);
  // small avatar + name
  g.fillStyle = '#ffffff'; g.beginPath(); g.arc(Wc / 2, 112, 34, 0, 7); g.fill();
  g.save(); g.beginPath(); g.arc(Wc / 2, 112, 30, 0, 7); g.clip();
  g.fillStyle = '#f3dfb8'; g.fillRect(Wc / 2 - 30, 82, 60, 60);
  g.fillStyle = '#4a2c1b'; g.beginPath(); g.ellipse(Wc / 2, 110, 19, 24, 0, 0, 7); g.fill();
  g.fillStyle = '#c99872'; g.beginPath(); g.ellipse(Wc / 2, 113, 13, 15, 0, 0, 7); g.fill();
  g.fillStyle = '#4a2c1b'; g.beginPath(); g.ellipse(Wc / 2, 121, 13, 9, 0, 0, Math.PI); g.fill();
  g.restore();
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillStyle = '#1e2430'; g.font = 'bold 26px sans-serif'; g.fillText('Jesus', Wc / 2, 168);
  g.fillStyle = '#5d6573'; g.font = '19px sans-serif'; g.fillText('You blocked Jesus.', Wc / 2, 200);
  // THE button: big, filled, in the upper middle (the thumb hovers below it, so the word stays readable)
  g.fillStyle = '#3d7be0'; rr(24, 232, Wc - 48, 96, 30); g.fill();
  g.fillStyle = '#ffffff'; g.font = 'bold 44px sans-serif'; g.fillText('Unblock', Wc / 2, 281);
  g.fillStyle = '#dfe3ea'; for (let i = 0; i < 4; i++) { rr(18, 380 + i * 62, Wc - 36, 46, 12); g.fill(); }
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 4;
  return tx;
}

export default {
  id: 's16',
  async setup(app) {
    await loadLines();
    const set = await app.set('EDGE');
    const [jesus, vd, user] = await Promise.all([app.char('JESUS'), app.char('VOID'), app.char('USER')]);
    const fx = new Particles({ max: 72, intensity: 1.6 });
    own(fx.mesh, 's16');
    const crestS = set.anchors.pathFarS ?? 41;
    const hill = [UHILL[0], set.groundAt(UHILL[0], UHILL[2]) - 0.03, UHILL[2]];
    // the Unblock screen overlay (rides on the user's phone screen in b07-b09)
    const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.071 - 0.007, 0.148 - 0.008), new THREE.MeshBasicMaterial({ map: unblockCanvas(), color: 0xffffff }));
    scr.matrixAutoUpdate = false; scr.renderOrder = 2;
    own(scr, 's16');
    // the phone insert's camera sits at the knees: cheat the hoodie drawstrings out of the lens for that shot
    const insW = [T('s16b08'), T('s16b09')];
    if (user.strings) for (const sg of user.strings) { hideDuring(sg.tb.mesh, [insW]); hideDuring(sg.ag, [insW]); }
    // the galaxy's route in this scene: from its s04-s15 hanging point out over the path ahead of the walkers (G1,
    // en route, off screen), then on to hang above the far crest (G2: in the finale lens, XWIDE and over the user)
    const F = set.shots.finale;
    const fd = toV(F.look).sub(toV(F.pos)).normalize();
    const G2 = toV(F.pos).addScaledVector(fd, 44).add(V3(0, 4.7, 0)).toArray();
    const G1 = [-0.9, 7.2, -17.5];
    return { scene: set.scene, set, jesus, vd, user, fx, scr, crestS, hill, G1, G2, look: lookFor('s16', set.look) };
  },

  async update(t, app, st) {
    stamp(t, 's16');
    const { set, jesus, vd, user, fx, scr, crestS, hill } = st;
    for (const o of [jesus.root, vd.root, fx.mesh, scr]) st.scene.add(o);
    jesus.root.visible = vd.root.visible = true;

    // ================================================================ timing
    const S = T('s16'), E = T('s16.end');
    const B2 = T('s16b02'), B3 = T('s16b03'), B4 = T('s16b04'), B5 = T('s16b05'), B6 = T('s16b06'), B6e = T('s16b06.end');
    const B10 = T('s16b10'), B11 = T('s16b11'), B13 = T('s16b13'), B7 = T('s16b07'), B8 = T('s16b08'), B9 = T('s16b09');
    const tArm = W('s16b01', 'arm', { frac: 0.22 }), tAround = W('s16b01', 'around', { frac: 0.28 }), tVoid1 = W('s16b01', 'void', { alt: ['void,'], frac: 0.4 });
    const tWalk = W('s16b01', 'walk', { frac: 0.6 }), tHorizon = W('s16b01', 'horizon', { alt: ['horizon.'], frac: 0.88 });
    const tNeutron = W('s16b02', 'neutron', { frac: 0.1 }), tBartender = W('s16b02', 'bartender', { frac: 0.3 }), tHow = W('s16b02', 'how', { frac: 0.5 });
    const tDrink = W('s16b02', 'drink', { alt: ['drink.', 'drink?'], frac: 0.85 });
    const tYou = W('s16b04', 'you', { alt: ['you?'], frac: 0.1 }), tNo = W('s16b04', 'no', { frac: 0.45 });
    const tCharge = W('s16b04', 'charge', { alt: ['charge.'], frac: 0.66 }), tChargeE = W('s16b04', 'charge', { alt: ['charge.'], end: true, frac: 0.8 });
    const tSmiling = W('s16b10', 'smiling', { frac: 0.25 }), tTelling = W('s16b10', 'telling', { frac: 0.55 }), tJokes = W('s16b10', 'jokes', { alt: ['jokes,', 'jokes.'], frac: 0.85 });
    const tNot = W('s16b09', 'not', { frac: 0.02 }), tYet = W('s16b09', 'yet', { alt: ['yet,', 'yet.'], frac: 0.15 });
    const tBut = W('s16b09', 'but', { frac: 0.55 }), tMaybe = W('s16b09', 'maybe', { alt: ['maybe.'], frac: 0.7 });
    // b01 choreography
    const tTurn0 = S - 0.2, tTurn1 = S + 0.9;                      // Jesus turns (decreasing yaw: face round to the lens)
    const tStep0 = S + 0.3, tStep1 = S + 1.1;                      // ...and steps round to its left (holding at its side
                                                                   // until "So", then a brisk crossing: never parked in
                                                                   // front of its belly)
    const tV0 = S + 0.25, tV1 = tArm - 0.05;                       // it waddles into the formation
    const tHug0 = tArm - 0.12, tHug1 = tAround + 0.3;              // his RIGHT arm round it
    const tSqueeze = tVoid1 - 0.08;                                // side-squeeze
    const tLean0 = tVoid1 + 0.05, tLean1 = tLean0 + 0.7;           // it leans in, its arm settles round his shoulders
    const tW0 = tWalk - 0.08;                                      // step off on "walk"
    // walk-and-talk
    const tSl0 = B3 - 0.1, tStop = B4 + 0.3;                       // slow down through the milked pause; stopped for it
    const tGo2 = B6e - 0.1;                                        // walk on
    const tTada = tCharge - 0.04, tBreak = tChargeE + 0.12, tWide = tChargeE + 0.3, tDrop = tWide + 0.28;
    const tSnort = B5 + 0.03, tSlap = tSnort + 0.06, tPoint = tSnort + 0.2;
    const tLaugh = B6 + 0.08, tPat1 = B6 + 0.6, tPat2 = tPat1 + 0.32;
    // the user's close: "maybe" lands and holds >= 12 frames before the cut over their shoulder
    const tFm = tBut - 0.12, tMaybeIn = Math.max(tFm + 0.3, W('s16b09', 'maybe', { alt: ['maybe.'], frac: 0.7 }) - 0.02);
    const cutOver = Math.max(tMaybeIn + 0.55, W('s16b09', 'maybe', { alt: ['maybe.'], end: true, frac: 0.9 }) + 0.18);

    // ================================================================ shot list
    const tFar = B11 - 0.1;
    const SHOTS = [[S, 'TWO'], [B2 - 0.15, 'TRACK'], [B4 - 0.08, 'JCU'], [tChargeE + 0.15, 'REACT'],
      [B6e + 0.25, 'TRACK2'], [tFar, 'FAR'], [B7, 'XWIDE'], [B8, 'PHONE'], [B9, 'UCU'], [cutOver, 'OVER']];
    let si = 0; for (let i = 0; i < SHOTS.length; i++) if (t >= SHOTS[i][0]) si = i;
    const shot = SHOTS[si][1], shotT0 = SHOTS[si][0], shotT1 = SHOTS[si + 1] ? SHOTS[si + 1][0] : E + 0.5;
    const userOn = shot === 'XWIDE' || shot === 'PHONE' || shot === 'UCU' || shot === 'OVER';
    if (userOn) { st.scene.add(user.root); user.root.visible = true; } else st.scene.remove(user.root);
    scr.visible = userOn;

    // ================================================================ the pair's walk (pure)
    const vAt = (x) => {
      if (x < tW0) return 0;
      if (x < tStop) return V_WALK * ramp(x, tW0, tW0 + 0.75) * (1 - ramp(x, tSl0, tStop));
      return V_WALK * ramp(x, tGo2, tGo2 + 0.7);
    };
    const distAt = (x) => {                                        // midpoint integration from the step-off (pure)
      if (x <= tW0) return 0;
      const n = Math.max(6, Math.ceil((x - tW0) * 12)), h = (x - tW0) / n;
      let d = 0; for (let i = 0; i < n; i++) d += vAt(tW0 + (i + 0.5) * h) * h;
      return d;
    };
    // "...in the distance": at the cut to the finale lens time has passed: from then on they cross the aligned station
    // (crest - 2.5) at mid-shot, at the same easy pace
    const sF = crestS - 2.5, tFm0 = (tFar + B7) / 2;
    const dist = t < tFar ? distAt(t) : 0;
    const sMid = t < tFar ? S0 + dist : sF + V_WALK * (t - tFm0);
    const walkAmt = t < tFar ? clamp(vAt(t) / V_WALK) : 1;
    const LEAD_J = 0.36, LAG_V = -0.24;                              // Jesus half a step ahead (their faces level)
    const fV = pathPose(set, S0 + LAG_V, SIDE_V), fJ = pathPose(set, S0 + LEAD_J, SIDE_J);   // the formation marks
    const farK = t < tFar ? 0 : 1;                                 // in the finale lens: a little air between the silhouettes
    const cheatU = shot === 'XWIDE' || shot === 'OVER' ? 0.45 : 0;  // (a lateral cheat in the user's long lens)
    const pV = pathPose(set, sMid + LAG_V, SIDE_V + 0.1 * farK + cheatU), pJ = pathPose(set, sMid + LEAD_J, SIDE_J + 0.3 * farK + cheatU);
    const unwrap = (a, ref) => { while (a - ref > Math.PI) a -= 2 * Math.PI; while (a - ref < -Math.PI) a += 2 * Math.PI; return a; };
    // the stop: half-turned toward each other for the punchline and the laugh
    const faceIn = pulse(t, tStop - 0.6, tGo2 + 0.45, 0.55, 0.5);
    // ---- the Void: from V15 into the formation (a few waddle steps), then the path
    const v15 = voidPos15(S), vYaw15 = EDGE.Y(S15.VY);
    const uV = ramp(t, tV0, tV1);
    const vPos = t < tW0 ? lerpA(v15, fV.pos, uV) : pV.pos;
    const vYawPath = unwrap(pV.yaw, vYaw15);
    const vYaw = (t < tW0 ? lerp(vYaw15, unwrap(fV.yaw, vYaw15), ramp(t, tV0, tV1 - 0.1)) : vYawPath) + 0.22 * faceIn;
    const vStepD = Math.hypot(fV.pos[0] - v15[0], fV.pos[2] - v15[2]);
    const vPhase = (uV * vStepD + dist) / 0.76 + 0.1;
    const vAmt = Math.max(walkAmt, 0.8 * pulse(t, tV0, tV1 + 0.05, 0.2, 0.3));
    // ---- Jesus: turn (decreasing yaw) + a side-step round to its left
    const jK = EDGE.W(M.K.p), jYaw15 = EDGE.Y(S15.JY1);
    const uJ = ramp(t, tStep0, tStep1);
    const jPos = t < tW0 ? lerpA(jK, fJ.pos, uJ) : pJ.pos;
    let jYawF = fJ.yaw; while (jYawF > jYaw15) jYawF -= 2 * Math.PI;
    const uTurn = ramp(t, tTurn0, tTurn1, (u) => { const s = smooth(u); return s + 0.04 * Math.sin(Math.PI * s) * (u > 0.65 ? 1 : 0); });
    const jYaw = (t < tW0 ? lerp(jYaw15, jYawF, uTurn) : unwrap(pJ.yaw, jYawF)) - 0.42 * faceIn;
    const jStepD = Math.hypot(fJ.pos[0] - jK[0], fJ.pos[2] - jK[2]);
    const jPhase = (uJ * jStepD + dist) / 0.9 + 0.3;
    const jAmt = Math.max(walkAmt, 0.55 * pulse(t, tStep0, tStep1 + 0.05, 0.2, 0.3));
    const fwd = t < tW0 ? fJ.dir : pJ.dir, left = t < tW0 ? fJ.left : pJ.left;

    // ================================================================ JESUS
    const jPose = (pass) => {
      const ve = vd.anchor('eyes');
      const vE = ve ? arr(ve) : add(vPos, [0, 2.0, 0]);
      // ---- face
      const Fgrin = JX('beam', { mSmile: 0.92, mOpen: 0.12, lidL: 0.55, lidU: 0.78 });
      const Fturn = JX('warm', { mSmile: 0.62, lidU: 0.92, browIn: 0.35, browOut: 0.3 });
      const Fcrook = JX('amused', { mSmile: 0.8, mAsym: 0.75, mOpen: 0.04, lidU: 0.86, lidL: 0.46, browIn: 0.35, browOut: 0.62, browAsym: 0.55 });
      const Fwarm = JX('warm', { mSmile: 0.6, lidU: 0.9 });
      const Fsetup = JX('amused', { mSmile: 0.45, mAsym: 0.3, lidU: 0.98, browIn: 0.42, browOut: 0.58 });
      const Fwig = JX('amused', { mSmile: 0.52, mAsym: 0.35, lidU: 1.08, browIn: 0.95, browOut: 1.1 });
      const Fmilk = JX('pressed', { mPress: 0.95, mSmile: 0.28, browIn: 0.8, browOut: 0.95, lidU: 1.04, lidL: 0.18, blush: 0.05 });
      const Fdead = JX('kind', { mSmile: 0.0, mPress: 0.35, lidU: 0.84, lidL: 0.08, browIn: 0.36, browOut: 0.42 });
      const Fbreak = JX('pressed', { mPress: 0.55, mSmile: 0.7, mAsym: 0.7, lidU: 0.8, lidL: 0.42, browIn: 0.45, browOut: 0.6 });
      const Fsee = JX('beam', { mSmile: 1, mOpen: 0.24, lidL: 0.5, lidU: 0.92, browIn: 0.55, browOut: 0.75 });
      const Flaugh = JX('laugh', { mOpen: 0.62 });
      const Fsmile = JX('content', { mSmile: 0.62, mPress: 0.35, lidU: 0.74, lidL: 0.45, browIn: 0.22, browOut: 0.28 });
      const Fnext = JX('amused', { mSmile: 0.55, mPress: 0.3, lidU: 0.95, lidL: 0.3, browIn: 0.6, browOut: 0.78 });
      const face = k(t, [['s16', Fgrin], [S + 0.25, Fgrin], [tStep1 - 0.1, Fturn, 'inOut'], [tSqueeze - 0.05, Fturn], [tSqueeze + 0.18, Fcrook, 'out'],
        [tW0 + 0.4, Fcrook], [tW0 + 1.3, Fwarm, 'inOut'],
        [B2 - 0.25, Fwarm], [B2, Fsetup, 'inOut'], [tNeutron - 0.05, Fsetup], [tNeutron + 0.1, Fwig, 'out'], [tNeutron + 0.55, Fsetup, 'inOut'],
        [B3 - 0.05, Fsetup], [B3 + 0.18, Fmilk, 'out'], [B4 - 0.05, Fmilk], [B4 + 0.12, Fdead, 'inOut'],
        [tBreak - 0.02, Fdead], [tBreak + 0.22, Fbreak, 'out'],
        [tSnort, Fbreak], [tSnort + 0.12, Fsee, 'out'], [tLaugh, Fsee], [tLaugh + 0.15, Flaugh, 'out'], [B6e - 0.2, Flaugh], [B6e + 0.35, Fsmile, 'inOut'],
        [tTelling - 0.3, Fsmile], [tTelling - 0.1, Fnext, 'inOut'], [tJokes + 0.3, Fnext], [tJokes + 0.6, Fsmile, 'inOut']]);
      face.autoBlink = 1;
      const mur = pulse(t, tTelling - 0.2, tJokes + 0.45, 0.2, 0.25);   // the next setup, sotto voce (under the narration)
      const speech = mur > 0.01 ? { open: mur * (0.07 + 0.07 * Math.max(0, Math.sin(t * 11.3) * Math.sin(t * 3.7 + 1))), wide: 0.25, round: 0.2 * mur, close: 0 } : undefined;
      // ---- head: leads the turn; up at it; back for the laugh; toward its shoulder in the distance
      const lead = -0.75 * pulse(t, tTurn0, tTurn1 + 0.15, 0.25, 0.45);            // head turns ahead of the body (to his right)
      const laugh = pulse(t, tLaugh, B6e + 0.05, 0.15, 0.4);
      const wiggle = 0.07 * bump(t, tNeutron - 0.02, 0.32);
      const leanIn = ramp(t, B11 + 0.3, B13 + 0.2);
      const jab = 0.06 * bump(t, tTada - 0.05, 0.28);
      const looking = ramp(t, tStep1 - 0.3, tStep1 + 0.2);
      // ---- arms: RIGHT round the Void's flank; LEFT free (ordering at a bar, ta-da, see?, chest pats, sketching)
      const hug = ramp(t, tHug0, tHug1);
      const squeeze = bump(t, tSqueeze, 0.4);
      let armR;
      // (span 0.6: the hand walks round its flank toward its back, far enough to show past his back in TWO)
      if (hug > 0.001) armR = { preset: 'around', surface: vd, reach: hug, height: jPos[1] + 1.18, span: 0.6, hand: { curl: 0.3 + 0.15 * squeeze, cup: 0.45, spread: 0.3 } };
      else armR = { preset: 'rest' };
      const order = pulse(t, B2 + 0.12, tDrink + 0.35, 0.3, 0.35);
      const tada = pulse(t, tTada - 0.14, tTada + 0.75, 0.12, 0.35);
      const point = pulse(t, tPoint - 0.1, tPoint + 0.6, 0.1, 0.25);
      const chest = pulse(t, tPat1 - 0.2, tPat2 + 0.3, 0.15, 0.25);
      const sketch = pulse(t, tTelling - 0.4, tJokes + 0.5, 0.3, 0.4) + 0.8 * pulse(t, B11 + 0.6, B11 + 1.8, 0.3, 0.4);
      const busy = clamp(order + tada + point + chest + sketch);
      const armL = { preset: [['rest', Math.max(1e-3, 1 - busy)], ['explain', Math.max(1e-3, order + sketch)], ['open', Math.max(1e-3, tada)], ['point', Math.max(1e-3, point)], ['heart', Math.max(1e-3, chest)]],
        gesture: 1 + 0.5 * order, hand: tada > 0.5 ? { curl: 0.05, spread: 0.45, thumb: 0.7, splay: 0.12 } : undefined };
      if (pass && tada > 0.01) {              // the little ta-da: the palm opens up and out to his side, toward the camera
        const sh = jesus.anchor('shoulderL');
        if (sh) { armL.target = add(arr(sh), [left[0] * 0.06 + fwd[0] * 0.4, -0.3 + 0.06 * tada, left[2] * 0.06 + fwd[2] * 0.4]); armL.reach = tada; armL.palm = [fwd[0] * 0.25 + left[0] * 0.2, 0.95, fwd[2] * 0.25 + left[2] * 0.2]; }
      }
      if (pass && point > 0.01) {             // see? — the index finger toward its face (across, up)
        const hl = jesus.anchor('handL');
        if (hl) armL.fingers = toV(vE).sub(hl).normalize().toArray();
      }
      if (pass && sketch > 0.01) { const a = (t - tTelling) * 4.2; armL.offset = [0.05 * Math.sin(a) * sketch * left[0], 0.04 * Math.sin(2 * a) * sketch, 0.05 * Math.sin(a) * sketch * left[2]]; }
      if (chest > 0.01) armL.offset = [0, -0.028 * (bump(t, tPat1 - 0.06, 0.15) + bump(t, tPat2 - 0.06, 0.15)), 0];
      return {
        pos: jPos, yaw: jYaw,
        walk: { amount: jAmt, phase: jPhase, style: 'stroll' },
        body: { lean: 0.02, tilt: -(0.03 + 0.05 * leanIn + 0.06 * squeeze), shrug: 0.12 * laugh * (0.5 + 0.5 * Math.sin(t * 2 * Math.PI * 4.2)) + 0.08 * squeeze,
          recoil: 0.2 * laugh, bounce: 0.008 * laugh * Math.sin(t * 2 * Math.PI * 4.2) + 0.006 * leanIn * Math.max(0, Math.sin((t - B11) * 2 * Math.PI * 1.1)), breathe: 1 },
        head: { yaw: lead * (1 - looking), look: pass && looking > 0.01 ? vE : undefined, follow: (0.32 + 0.3 * faceIn - 0.22 * laugh) * looking, pitch: -0.3 * laugh + jab - 0.03,
          roll: -(0.06 + wiggle + 0.14 * leanIn + 0.16 * squeeze), talk: 0.8 },   // (- = toward his right: into it)
        gaze: pass ? (looking < 0.5 ? add(arr(jesus.anchor('eyes') || V3(...jPos)), [fwd[0] * 3 - left[0] * 1.5, 0.1, fwd[2] * 3 - left[2] * 1.5]) : laugh > 0.5 ? add(vE, [0, 0.7, 0]) : vE) : null,
        face, speech,
        blinkAt: [tStep1 + 0.05, tSqueeze + 0.45, B3 + 0.1, tBreak + 0.4, B6e + 0.2, tTelling - 0.35, B11 + 0.5],
        armL, armR,
        glow: 1 + 0.2 * ramp(t, B11 - 0.2, B11 + 0.3),
      };
    };

    // ================================================================ VOID
    const vPose = (pass) => {
      const je = jesus.anchor('eyes');
      const jE = je ? arr(je) : add(jPos, [0, 1.55, 0]);
      const Fcrinkle = VX('giggle', { lidU: 0.3, lidL: 1, mOpen: 0.08, mSmile: 1, blush: 0.45 });
      const Fwatch = VX('gentle', { mSmile: 0.55, lidU: 0.8, lidL: 0.4, browIn: 0.5, blush: 0.3 });
      const Fcontent = VX('gentle', { mSmile: 0.72, lidU: 0.45, lidL: 0.55, browIn: 0.5, blush: 0.42 });
      const Feager = VX('hopeful', { lidU: 1.18, lidL: 0.05, browIn: 0.8, browOut: 0.55, mSmile: 0.45, mOpen: 0.04, mRound: 0.15, pupil: 1.2 });
      const Fwait = VX('hopeful', { lidU: 1.2, browIn: 0.85, browOut: 0.65, mSmile: 0.2, mPress: 0.75, mWide: 0.35, pupil: 1.25 });
      const Fwide = VX('surprised', { lidU: 1.4, browIn: 0.9, browOut: 0.9, mOpen: 0.05, mRound: 0.2, mSmile: 0.15 });
      const Fopen = VX('surprised', { lidU: 1.32, browIn: 0.85, browOut: 0.85, mOpen: 0.62, mRound: 0.45, mSmile: 0.3 });
      const Fsnort = VX('laugh', { lidU: 0.15, lidL: 1, mOpen: 0.3, mSmile: 0.95, blush: 0.5 });
      const Fgig = VX('giggle', { lidU: 0.28, lidL: 1, mOpen: 0.35, mSmile: 1, blush: 0.5 });
      const Fbend = VX('happy', { mSmile: 0.75, lidU: 0.62, lidL: 0.7, browIn: 0.5, blush: 0.35 });
      const face = k(t, [['s16', Fcrinkle], [S + 0.35, Fcrinkle], [S + 0.9, Fwatch, 'inOut'], [tLean0, Fwatch], [tLean1, Fcontent, 'inOut'],
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
      const headOn = ramp(t, B13 - 0.5, B13 + 0.4);                         // its head leans against his
      const squish = bump(t, tSqueeze - 0.03, 0.5);                           // his side-squeeze: its plush body squishes ~4 %
      // ---- arms: LEFT (home since s15b06) settles round his shoulders: the forearm drapes behind his neck, the big
      //      palm comes to rest on top of his FAR shoulder with the fingers over its front (the rig's own `on` contact),
      //      so from the front / 3-4 angles it reads as a hand on his shoulder, never as a ball in a ring (the old
      //      cupped grip on the outside of his shoulder pointed the forearm at the lens);
      //      RIGHT: from the covered mouth down to its belly, slapped over the mouth again on the snort
      const around = ramp(t, tLean0 - 0.1, tLean1 + 0.15);
      let armL = { preset: 'rest' };
      const jfw = [Math.sin(jYaw), 0, Math.cos(jYaw)];
      if (around > 0.001) {
        const r = around, arc = Math.sin(Math.PI * clamp(r));
        armL = { preset: 'around', on: jesus, reach: r, handScale: 0.62,
          offset: [-jfw[0] * 0.45 * arc, 0.1 * arc, -jfw[2] * 0.45 * arc] };                 // the hand travels round behind him
      }
      // RIGHT: down from the snort-covered mouth (its LEFT came home from his shoulder in s15b06)
      const down = ramp(t, S, S + 0.45);
      let armR = down < 1 ? { preset: 'cover_mouth', from: 'belly', mix: 1 - down, offset: [0, 0.14 * (1 - down), 0] } : { preset: 'rest' };
      const slap = ramp(t, tSlap - 0.05, tSlap + 0.08, (u) => 1 - Math.pow(1 - u, 3)) * (1 - ramp(t, B6e + 0.15, B6e + 0.65));
      if (slap > 0.001) armR = { preset: 'cover_mouth', from: 'rest', mix: slap, offset: [0, 0.14 * slap, 0] };
      return {
        pos: vPos, yaw: vYaw,
        walk: { amount: vAmt, phase: vPhase, style: 'waddle' },
        body: { lean: 0.08 + 0.1 * bend, tilt: 0.1 * leanIn + 0.06 * bend + 0.06 * headOn - 0.03 * squish, twist: 0.08 * bend,
          shrug: 0.22 * gig * (0.5 + 0.5 * Math.sin(t * 2 * Math.PI * 4.6)) + 0.15 * snort + 0.12 * squish, recoil: 0.07 * snort, breathe: 1.05,
          swell: -0.5 * squish, stretch: 0.022 * squish },
        head: { yaw: 0.28 * leanIn + 0.08 * bend + 0.3 * (1 - ramp(t, S, tV1)), pitch: 0.14 + 0.12 * bend + 0.05 * leanIn, roll: 0.1 * leanIn + 0.14 * headOn, track: 0 },
        gaze: pass ? jE : null,
        face,
        blinkAt: [S + 0.8, tLean0 + 0.3, B3 + 0.5, B6e + 0.4],
        armL, armR,
        extra: { rim: lerp(1.1, 1.8, ramp(t, B11 - 0.2, B11 + 0.2)), eyeGlow: lerp(1, 1.25, ramp(t, B11 - 0.2, B11 + 0.2)), motes: 1 + 0.6 * gig },
      };
    };

    // ================================================================ USER (on the lilac hill)
    const uYaw = 3.05;                                                          // facing down the path toward the sun
    const uPose = (pass) => {
      const pE = add(lerpA(vPos, jPos, 0.5), [0, 1.8, 0]);
      const phs = user.anchor('phoneScreen');
      const phS = phs ? arr(phs) : add(hill, [0.1, 0.8, -0.3]);
      const Fwatch = UX('notquite', { mSmile: 0.0, lidU: 0.92, browIn: 0.55, wet: 0.7 });
      const Fphone = UX('soften', { lidU: 0.88, mOpen: 0.02, mTremble: 0.15, wet: 0.8 });
      const Ftorn = UX('tremble', { mTremble: 0.4, wet: 0.9 });
      const Fexh = UX('soften', { lidU: 0.9, lidL: 0.2, mOpen: 0.07, mSmile: 0.05, wet: 0.9, browIn: 0.7, browOut: -0.1 });
      const Fmaybe = UX('notquite', { mSmile: 0.42, mAsym: 0.3, browIn: 0.8, browOut: 0.12, lidU: 0.88, lidL: 0.46, wet: 1, mTremble: 0.1, pupil: 1.12 });
      const face = k(t, [['s16b07', Fwatch], [B7 + 0.7, Fwatch], [B7 + 1.1, Fphone, 'inOut'], [B8 + 0.6, Fphone], [B8 + 1.2, Ftorn, 'inOut'],
        [tNot + 0.2, Ftorn], [tNot + 0.6, Fexh, 'inOut'], [tFm, Fexh], [tMaybeIn, Fmaybe, 'inOut']]);
      face.autoBlink = 1;
      // eyes: the pair -> the phone -> (after the breath out) back up toward the pair on "maybe"
      const look = ramp(t, B7 + 0.75, B7 + 1.05) * (1 - ramp(t, tFm - 0.1, tMaybeIn - 0.1));
      const gaze = pass ? lerpA(pE, phS, look) : null;
      // thumb: drifts toward Unblock, hovers trembling just BELOW it, touches lightly (4 frames), lifts away
      const hov = ramp(t, B8 + 0.3, B8 + 0.9) * (1 - ramp(t, tNot + 0.05, tNot + 0.4));
      const tTouch = B8 + 1.3;
      const touch = bump(t, tTouch, 4 / 24) * 0.6;
      const near = ramp(t, tTouch - 0.25, tTouch) * (1 - ramp(t, tTouch + 0.17, tTouch + 0.4));
      const lift = ramp(t, tTouch + 0.2, tTouch + 0.5);
      const tAt = [lerp(0.7, 0.56, ramp(t, B8 + 0.3, B8 + 1.0)) + 0.004 * Math.sin(t * 41) * hov,
        lerp(0.85, 0.66, ramp(t, B8 + 0.3, B8 + 1.0)) - 0.17 * near + 0.12 * lift + 0.003 * Math.sin(t * 37 + 1) * hov];
      const lower = ramp(t, tNot + 0.15, tYet + 0.55);
      const chin = ramp(t, tFm - 0.1, tMaybeIn + 0.1);
      const breath = pulse(t, tNot + 0.3, tFm + 0.1, 0.3, 0.5);
      return {
        pos: hill, yaw: uYaw,
        body: { sit: 1, sitPath: 'plain', scoot: 1, scootPhase: 0.45, lean: 0.34 - 0.14 * chin, hunch: 0.45 - 0.1 * chin, slump: 0.25 + 0.15 * breath - 0.1 * chin, breathe: 1 + 0.9 * breath, breathRate: 0.18 },
        head: { pitch: 0.16 + 0.14 * look - 0.24 * chin, yaw: 0, roll: 0.04 * chin },
        gaze, face,
        blinkAt: [B7 + 0.62, B8 + 1.6, tNot + 0.35, tFm - 0.05],
        armL: { preset: [['hold', 1]], offset: [0, -0.07 * lower, 0] },
        armR: { preset: 'knee' },
        extra: { phone: 0.9, screen: 'blocked', phoneUp: 0.35 * (1 - lower), thumb: hov, tap: touch > 0.001 ? touch : undefined, thumbAt: tAt, hood: 0.86, glow: 1.15 },
      };
    };

    // ================================================================ cameras
    const cam = () => {
      let s;
      const ve = vd.anchor('eyes'), je = jesus.anchor('eyes');
      const vE = ve ? arr(ve) : add(vPos, [0, 2.0, 0]), jE = je ? arr(je) : add(jPos, [0, 1.55, 0]);
      const faces = lerpA(jE, vE, 0.45);
      const u = ramp(t, shotT0, shotT1);
      switch (shot) {
        case 'TWO': {   // front-3/4 from Jesus's open side (the hill side), a little high: orbits in (60 -> 50 deg off the
          //             path axis) and pushes while he steps round, so his RIGHT forearm reaching round its flank shows past his
          //             back by "around"; Jesus screen-right, the Void screen-left (its face 3/4 in its hood); after "walk"
          //             the camera backs down the path at half their pace (they come toward the lens and screen-left)
          const m = pathPose(set, S0, 0);
          const fw = [m.dir[0] * dist, 0, m.dir[2] * dist];             // the pair's walk so far (0 before the step-off)
          const th = (lerp(60, 50, ramp(t, S + 0.15, tAround + 0.25)) - 5 * ramp(t, tW0, tW0 + 1.6)) * Math.PI / 180;
          const D = lerp(5.9, 5.0, ramp(t, S, tW0 + 0.4));
          const C = lerpA(fJ.pos, fV.pos, 0.5);
          const P = add(C, [0.5 * fw[0] + (m.dir[0] * Math.cos(th) + m.left[0] * Math.sin(th)) * D, 0, 0.5 * fw[2] + (m.dir[2] * Math.cos(th) + m.left[2] * Math.sin(th)) * D]);
          P[1] = Math.max(set.groundAt(P[0], P[2]), C[1]) + lerp(2.45, 2.15, ramp(t, tW0, shotT1));
          const fJe = add(fJ.pos, [fw[0], 1.56, fw[2]]), fVe = add(fV.pos, [fw[0] + fJ.left[0] * 0.3, 2.02, fw[2] + fJ.left[2] * 0.3]);   // the formation faces
          s = aimXY(P, lerpA(fJe, fVe, 0.5), 372, 370, 44, { drift: 0.1 });
          break;
        }
        case 'TRACK': case 'TRACK2': {   // front-3/4 tracking medium from Jesus's side: backing up the path ahead of them
          const m = pathPose(set, sMid, 0);
          const k2 = shot === 'TRACK2' ? 1 : 0;
          const P = add(m.pos, [m.dir[0] * (4.0 + 0.3 * k2) + m.left[0] * (1.6 - 0.35 * k2), 0, m.dir[2] * (4.0 + 0.3 * k2) + m.left[2] * (1.6 - 0.35 * k2)]);
          P[1] = Math.max(set.groundAt(P[0], P[2]) + 0.25 * k2, m.pos[1]) + 1.62 - 0.25 * k2;
          s = aimXY(P, lerpA(jE, vE, 0.5), 360 - 25 * k2, 370, 42, { drift: 0.1 });
          break;
        }
        case 'JCU': {   // Jesus, half-turned toward it: the deadpan, the ta-da, the corner breaking
          const jf = [Math.sin(jYaw), 0, Math.cos(jYaw)], jl = [Math.cos(jYaw), 0, -Math.sin(jYaw)];
          const P = add(jE, [jf[0] * 2.25 + jl[0] * 0.95, -0.16, jf[2] * 2.25 + jl[2] * 0.95]);
          s = aimXY(P, jE, 320, 420, 40, { drift: 0.08 });
          break;
        }
        case 'REACT': { // tighter two-shot for its reaction + his laugh
          const m = pathPose(set, sMid, 0);
          const P = add(m.pos, [m.dir[0] * 3.4 + m.left[0] * 1.45, 0, m.dir[2] * 3.4 + m.left[2] * 1.45]);
          P[1] = Math.max(set.groundAt(P[0], P[2]), m.pos[1]) + 1.68;
          s = aimXY(P, lerpA(jE, vE, 0.5), 360, 390, 44, { drift: 0.08 });
          break;
        }
        case 'FAR': {   // the set's finale lens; a very slow push that comes to rest
          const F = set.shots.finale;
          const w = ramp(t, shotT0, B13 + 0.3, (x) => 1 - Math.pow(1 - x, 2));
          s = { pos: F.pos.map((x, i) => lerp(x, F.look[i], 0.05 * w)), look: F.look, fov: F.fov, drift: 0.04 };
          break;
        }
        case 'XWIDE': s = { pos: [-1.2, 2.3, 4.4], look: [-1.55, 1.55, -14.5], fov: 44, drift: 0 }; break;
        case 'PHONE': {
          const ph = user.anchor('phoneScreen');
          if (ph) {
            user.phone.updateWorldMatrix(true, false);
            const n = V3(0, 0, 1).transformDirection(user.phone.matrixWorld), up = V3(0, 1, 0).transformDirection(user.phone.matrixWorld);
            const xr = V3(1, 0, 0).transformDirection(user.phone.matrixWorld);
            const cp = ph.clone().addScaledVector(n, 0.24).addScaledVector(up, 0.03).addScaledVector(xr, 0.02);
            const lk = ph.clone().addScaledVector(up, -0.01);
            s = { pos: cp.toArray(), look: lk.toArray(), fov: 40, drift: 0, roll: rollFor(cp, lk, up) };
          } else s = { pos: add(hill, [0, 1.2, -0.8]), look: add(hill, [0, 0.6, 0]), fov: 40 };
          break;
        }
        case 'UCU': {   // close on the user from the sunward side (front-lit by the low sun)
          const ue = user.anchor('eyes');
          const U = ue ? arr(ue) : add(hill, [0, 0.85, 0]);
          const fU = [Math.sin(uYaw), 0, Math.cos(uYaw)], lU = [Math.cos(uYaw), 0, -Math.sin(uYaw)];
          const P = add(U, [fU[0] * 1.45 + lU[0] * 0.2, -0.24, fU[2] * 1.45 + lU[2] * 0.2]);
          s = aimXY(P, U, 370, 420, 33, { drift: 0.06 });
          break;
        }
        case 'OVER': {  // over their right shoulder (the hood soft at the left edge), down to the pair walking into the sun
          const uh = user.anchor('head');
          const U = uh ? arr(uh) : add(hill, [0, 0.85, 0]);
          const fU = [Math.sin(uYaw), 0, Math.cos(uYaw)], lU = [Math.cos(uYaw), 0, -Math.sin(uYaw)];
          const P = add(U, [-fU[0] * 0.85 - lU[0] * 0.32, 0.2, -fU[2] * 0.85 - lU[2] * 0.32]);
          const el = lerp(6.2, 0.6, todAt(t)) * Math.PI / 180, az = -0.14 + OVER_SHIFT;
          const sunPt = add(P, [Math.sin(az) * Math.cos(el) * 300, Math.sin(el) * 300, -Math.cos(az) * Math.cos(el) * 300]);
          s = aimXY(P, sunPt, 316, 616, 36, { drift: 0.02 });
          break;
        }
        default: s = EDGE.cam('MASTER');
      }
      applyShot(app.camera, s, t, 16);
    };

    // ================================================================ set + solve
    const far = shot === 'FAR' ? set.shots.finale : null;
    const userShot = shot === 'XWIDE' || shot === 'OVER';
    set.update(t, {
      tod: todAt(t), voidSky: voidSkyAt(t), voidPos: vPos,
      shadowAt: lerpA(vPos, jPos, 0.5),
      sunGlow: shot === 'FAR' || shot === 'OVER' || shot === 'XWIDE' ? 1.1 : 0.9,
      sunShift: userShot ? OVER_SHIFT : 0,
      keyYaw: shot === 'UCU' || shot === 'PHONE' ? -0.05 : undefined, fillMul: shot === 'UCU' ? 1.35 : 1,
      seeds: shot === 'TWO' || shot === 'XWIDE' ? 0.5 : 0,
      ...(far ? { ...far.opts, tod: todAt(t), seeds: 0 } : {}),
      clear: [[jPos[0], jPos[2], 0.6], [vPos[0], vPos[2], 1.2], [hill[0], hill[2], 0.9]],
    });
    const list = [[vd, vPose], [jesus, jPose], [vd, vPose]];
    if (userOn) list.push([user, uPose]);
    solve(t, list, cam);
    if (shot === 'PHONE') cam();                 // the insert rides on the final phone pose
    // the Unblock screen overlay rides on the phone's screen
    if (userOn && user.phone) {
      user.phone.updateWorldMatrix(true, false);
      scr.matrix.copy(user.phone.matrixWorld).multiply(new THREE.Matrix4().makeTranslation(0, 0, 0.0085 / 2 + 0.0009));
      scr.matrixWorldNeedsUpdate = true;
      if (user.screenMat) scr.material.color.copy(user.screenMat.color);
    }

    // ---- particles: the galaxy; the snort's spray of stars; little stars floating up from the giggling hood
    const mo = vd.anchor('mouth'), md = vd.mouthDir(), top = vd.anchor('hoodTop');
    fx.begin();
    const g = galaxy16(t, st, S, tWalk, tFar);
    if (g) fx.add(g, EDGE.GALAXY.size * (shot === 'FAR' ? 1.6 : 1), 0xd8c0ff, 0.9, galaxySpin(t), CELL.galaxy);
    if (mo) {
      fx.burst({ t, seed: 1601, at: tSnort + 0.04, count: 14, life: 1.6, jitter: 0.12, origin: add(arr(mo), [md.x * 0.2, 0.12, md.z * 0.2]),
        vel: [md.x * 0.9, 0.75, md.z * 0.9], spread: [0.75, 0.45, 0.75], gravity: [0, -0.3, 0], drag: 1.4, size: [0.06, 0.11], grow: 0.5,
        color: [0xfff1c8, 0xd8c0ff, 0xbfe8ff], alpha: 0.85, fade: [0.14, 0.45], cell: CELL.star, spin: 1.5 });
    }
    if (top) {
      for (const [a, b, sd, rate, sz] of [[B6, B6e, 1602, 3.0, [0.06, 0.1]], [B11, B13 + 0.8, 1603, 2.6, [0.3, 0.42]]]) {
        fx.stream({ t, seed: sd, t0: a, t1: b, rate, life: 2.6, origin: (tb) => add(arr(top), [0.25 * Math.sin(tb * 7.1), -0.25, 0.25 * Math.cos(tb * 5.3)]),
          vel: [0, 0.4 + 0.25 * (sd === 1603 ? 1 : 0), 0], spread: [0.08, 0.06, 0.08], drag: 0.2, size: sz, grow: 0.6, color: sd === 1603 ? [0xd8c0ff, 0xbfe8ff] : [0xfff1c8, 0xd8c0ff], alpha: 0.9,
          fade: [0.15, 0.5], cell: CELL.star, spin: 0.8, wobble: 0.05, twinkle: true });
      }
    }
    fx.end();
    st.look = lookFor('s16', set.look);
    if (far && far.post) st.look = { ...st.look, ...far.post };
  },
};

// the laughed-up galaxy in s16: from where it has hung since s04 (galaxyAt) out over the path ahead of the walkers
// (G1, en route), then on to hang above the far crest (G2). Off screen while it travels (TWO looks back
// up the path; the tracking shots look back at the pair).
function galaxy16(t, st, S, tWalk, tFar) {
  const g0 = galaxyAt(S);
  if (!g0) return null;
  const bob = 0.12 * Math.sin(t * 0.4) - 0.12 * Math.sin(S * 0.4);
  const a = smooth(clamp((t - S) / Math.max(0.1, tWalk - 0.1 - S)));
  const b = smooth(clamp((t - tWalk - 2) / Math.max(0.1, tFar - 0.5 - tWalk - 2)));
  const p = lerpA(lerpA(g0, st.G1, a), st.G2, b);
  return [p[0], p[1] + bob, p[2]];
}
function lerpA(a, b, u) { const A = arr(a), B = arr(b); return [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u]; }
