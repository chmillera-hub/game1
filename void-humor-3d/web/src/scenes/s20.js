// s20 the_kick — no fuss. The Void's top half is serene and does not move, steering Fear's gaze with a star on one
// fingertip; its bottom half is one fat leg and one perfect donkey kick into the bent-double magician's chest.
// Rubber-hose flight into the janitor corner: buckets, BONK (bucket hat), mop wig, birdies, the dagger thunks into the
// floor, a grey puff, and the wet-floor sign that teetered all along tips onto him last. "...How rude."
//
// Shots (all from beat refs / word times):
//   A  scene start -> "shouting"+   VOID_LOW close (serene face, slow blink: it does not shout)
//   B  -> s20b02                   low two-shot: the Void's index finger rises, a star lights on its tip on "making";
//                                  Fear's eyes catch it and it lures Fear out of the cage door (FDOOR -> FOUT, tiptoe)
//   C  s20b02 -> b03               MAG_MED: last tiptoe step in, dagger high on "stab", toothy grin, eyes popping
//   D  s20b03 -> b05               KICK wide (locked): magician bent double at the Void's flank, the Void blinks; chamber,
//                                  KICK on "kicks" (top half locked: the rig's forward tip is cancelled), he launches out
//                                  of frame right, his hat hangs a beat, then zips; the leg lowers toward the hem
//   E  s20b05 -> b06               floor insert: the fat leg retracts, the foot's satisfied wiggle on "leg", hem bounce
//   F  s20b06 -> impact            follow-pan on the flight (left -> right), limbs pinwheeling, hat + dagger behind
//   G  impact -> +0.85             CORNER: he slams back-first into the pile, props fly, short shake, he crumples
//   H  +0.85 .. +1.45              0.6 s cutaway: Fear flinches (tuft up, eyes dart to the corner), the star stays steady
//   I  -> end                      CORNER locked: BONK, mop wig, birdies, dagger thunk, grey puff, the sign, "...How rude."
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, ease, DEG } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { MX } from '../chars/magician.js';
import { ROOM, sy, lookFor } from './marks.js';
import { ensureBonusDecals, MAGPATH } from './kit_bonus.js';
import {
  loadLines, V, A, add, sub, mix3, LD, pulse, jiggle, stamp, own, solve, aim, pix, marks, times,
  voidSpot, starAt, heldStar, drawStar, fearCU, flightTau, flightPos, wreckPose, hatRestPos, daggerRestPos, cornerOpts, placeHatBucket,
  brighten, ROOM_LIGHTS, starHand,
} from './kit_s20_22.js';

const ID = 's20';
// the magician's kick pose: bent double just past the Void's back-left flank (screen-right of its silhouette in the
// KICK wide), in profile toward Fear (screen-left), leaning out toward the camera side; the leg is stretched a little
// (rubber hose, `kickReach`) so his head stays clear of the Void's body
const KP = { yaw: -1.05, lean: 1.25, crouch: 0.18, peek: 0.7, hunch: 0.2 };
const REACH = 1.4;

export default {
  id: ID,
  async setup(app) {
    await loadLines();
    const set = await app.set('BACKROOM');
    ROOM.fit(set);
    ensureBonusDecals(set);   // the magician's grey footprints + dust patch (s18) stay on the floor
    times().plate = set.anchors.cageInside ? set.anchors.cageInside.y : 0.04;
    const [vd, fear, mag] = await Promise.all([app.char('VOID'), app.char('FEAR'), app.char('MAGICIAN')]);
    const fx = new Particles({ max: 170, intensity: 1.5 });
    const fxN = new Particles({ max: 48, blending: 'normal', intensity: 1.0 });
    own(ID, fx.mesh); own(ID, fxN.mesh);
    // the dagger that flies out of his hand (a clone of his prop: shares geometry + materials)
    const dagger = mag.dagger.clone(true);
    dagger.rotation.order = 'YXZ';
    dagger.scale.multiplyScalar(1.7);   // cartoon-readable once it has left his hand (a tiny prop at corner distance)
    own(ID, dagger);
    // where the hat bucket stands before the crash (its local transform in the corner group)
    set.update(0, {});
    const hatBase = A(set.props.bucketHat.position.clone());
    const st = { scene: set.scene, set, vd, fear, mag, fx, fxN, dagger, hatBase, look: lookFor(ID, set.look) };
    // contact geometry, solved from the rigs (robust to rig refinements). The magician is posed FIRST (bent double at
    // the flank); the leg's aim point is solved so the sole lands on his chest (the leg aims inside a cone, so the aim
    // overshoots a little); if the chest is out of the leg's reach he is slid toward the foot.
    const c = times(), M = marks(), tc = c.contact - 0.01;
    st.magRoot = add(M.V, [1.72, 0, -0.38]);
    st.aim0 = [1.45, 0.92, -0.85];
    let C = null, F = null;
    for (let o = 0; o < 4; o++) {
      mag.update(tc, magPose(st, tc, 0));
      C = A(mag.anchor('chest'));
      st.aim0 = C.slice();
      for (let i = 0; i < 6; i++) {
        vd.update(c.contact, kickVoid(M, 1.0, st.aim0, REACH));
        F = A(vd.anchor('kickFoot'));
        st.aim0 = add(st.aim0, sub(C, F));
      }
      vd.update(c.contact, kickVoid(M, 1.0, st.aim0, REACH));
      F = A(vd.anchor('kickFoot'));
      const r = sub(F, C);
      st.contactErr = Math.hypot(...r);
      if (st.contactErr < 0.012) break;
      st.magRoot = [st.magRoot[0] + r[0], 0, st.magRoot[2] + r[2]];
    }
    mag.update(tc, magPose(st, tc, 0));
    st.chest0 = A(mag.anchor('chest'));
    st.foot0 = F;
    st.hat0 = A(mag.anchor('hat'));
    // the squash hold: slide his root so the folded chest stays exactly on the sole
    st.sqOff = [0, 0, 0];
    { const th = c.contact + 0.1; mag.update(th, magPose(st, th, 0)); st.sqOff = sub(st.chest0, A(mag.anchor('chest'))); }
    vd.update(c.contact, kickVoid(M, 0, st.aim0));
    st.hip0 = A(vd.anchor('hip'));
    console.log('s20 contact: magician root', st.magRoot.map((x) => x.toFixed(2)).join(','), 'chest', st.chest0.map((x) => x.toFixed(2)).join(','), 'foot', F.map((x) => x.toFixed(2)).join(','), 'aim', st.aim0.map((x) => x.toFixed(2)).join(','), 'err', st.contactErr.toFixed(3));
    return st;
  },

  async update(t, app, st) {
    stamp(ID, t);
    const { set, vd, fear, mag, fx, fxN, dagger } = st;
    for (const o of [vd.root, fear.root, mag.root, fx.mesh, fxN.mesh, dagger]) st.scene.add(o);
    const c = times(), M = marks();
    const shot = shotId(t, c);
    st.shot = shot;
    st.cam = app.camera;

    // ------------------------------------------------------------------ VOID
    const vs = voidSpot(t);
    // chamber on "kicks" -0.30, fire, contact, a 4-frame overshoot, hold, then the leg lowers toward the back hem (it is
    // already there when the insert cuts in), the wiggle on "leg", and it tucks back under the hem
    const kickV = k(t, [[c.B4 - 0.32, 0], [c.kickFire, -0.5, 'inOut'], [c.contact, 1.0, 'out'], [c.launch + 0.04, 1.1, 'out'], [c.launch + 0.2, 1.0, 'inOut'],
      [c.B5 - 0.4, 1.0], [c.B5, 0.97, 'inOut'], [c.leg + 0.35, 1.0, 'inOut'], [c.leg + 0.62, 0.0, 'in']]);
    st.kv = kickV;
    // the kick target: the solved aim point -> (lowering in the wide, before the insert) a spot just outside the back hem
    const hemOut = add(vs.pos, rotY([0.42, 0.2, -1.22], vs.yaw));
    const wig = pulse(t, c.leg - 0.05, c.leg + 0.4, 0.06, 0.1);
    const kt = mix3(st.aim0, hemOut, k(t, [[c.B5 - 0.4, 0], [c.B5 - 0.02, 1, 'inOut']]));
    const kTarget = add(kt, rotY([0.05 * wig * Math.sin((t - c.leg) * 26), 0.02 * wig * Math.abs(Math.sin((t - c.leg) * 26)), 0], vs.yaw));
    const hemBounce = Math.max(0, jiggle(t, c.leg + 0.6, 0.18, 15, 5));
    const KB = kickBody(kickV, kTarget[1]);
    // the fat leg snaps out a little longer than it is (rubber hose) and is its own size again by the insert
    const kReach = k(t, [[c.kickFire, 1.0], [c.contact, REACH, 'out'], [c.B5 - 0.4, REACH], [c.B5 - 0.02, 1.0, 'inOut']]);
    const vPose = (pass) => {
      const fe = pass ? fear.anchor('eyes') : null;
      const s = starAt(t);
      const fw = add(fearWalk(t, c, M).pos, [0, 0.62, 0]);
      const Fserene = VX('gentle', { lidU: 0.8, lidL: 0.42, mSmile: 0.5, browIn: 0.3, blush: 0.15 });
      const Fsoft = VX('gentle', { lidU: 0.74, lidL: 0.5, mSmile: 0.56, browIn: 0.36, blush: 0.2 });
      const Fkick = VX('gentle', { lidU: 0.72, lidL: 0.52, mSmile: 0.6, browIn: 0.3, mPress: 0.2, blush: 0.2 });
      const face = k(t, [[ID, Fserene], [c.making, Fserene], [c.making + 0.6, Fsoft, 'inOut'], [c.B4 - 0.2, Fsoft], [c.contact, Fkick, 'out'], [c.contact + 0.6, Fsoft, 'inOut']]);
      face.autoBlink = 0;
      // the LEFT (camera-side) index finger points straight UP, palm toward Fear, thumb curled in: the star sits on the
      // tip; the right hand rests on its belly
      const reach = k(t, [[c.B1 + 0.7, 0], [c.making - 0.05, 1, 'inOut']]);
      const towardF = sub(fw, s.pos);
      const hz = Math.hypot(towardF[0], towardF[2]) || 1;
      const fh = [towardF[0] / hz, 0, towardF[2] / hz];
      const up = [0.08 * fh[0], 1, 0.08 * fh[2] + 0.18];
      const down = [fh[0] * 0.3, -1, fh[2] * 0.3];
      const fing = mix3(down, up, smooth(reach));
      const head = { pitch: 0.25 + KB.headPitch, yaw: shot >= 3 ? 0.3 : 0.08, roll: 0.03 };
      return {
        pos: vs.pos, yaw: vs.yaw,
        body: { lean: 0.12 + KB.lean, hunch: KB.hunch, pitch: KB.pitch, breathe: 0.9 - 0.6 * pulse(t, c.B3, c.contact + 0.2, 0.4, 0.3), breathRate: 0.2 },
        head,
        gaze: pass ? fe : null,
        face,
        blinkAt: [c.B1 + 0.42, c.B3 + 0.36, c.contact + 0.9],
        armL: { preset: 'point', from: 'rest', mix: reach, target: s.pos, tip: true, reach, fingers: fing, ...starHand(fh), pole: [0.2, -1, -0.3] },
        armR: { preset: 'belly', from: 'rest', mix: k(t, [[c.B2, 0], [c.B3 + 0.6, 1, 'inOut']]) },
        extra: { kick: kickV, kickSide: 'L', kickTarget: kTarget, kickLevel: 1, kickReach: kReach, stars: 1.4, hem: hemBounce, motes: 0.8 },
      };
    };

    // ------------------------------------------------------------------ FEAR
    const fearPose = (tt) => fearPoseAt(st, tt, c, M);
    // ------------------------------------------------------------------ MAGICIAN
    const mPose = (pass) => magPose(st, t, pass);

    // ------------------------------------------------------------------ solve (camera from pass-0 anchors)
    const shotStart = [ID, c.cutA, c.B2, c.B3, c.B5, c.B6, c.imp - 0.2, c.fearCut0, c.fearCut1, c.kmed][shot] ?? ID;
    solve(t, [[vd, vPose], [mag, mPose], [fear, (pass) => (pass ? (tt) => fearPose(Math.max(tt, T(shotStart))) : fearPose(t))]], () => {
      applyShot(app.camera, frameShot(st, t, shot, c, M), t, 20);
    });
    // the corner (after the rigs: the bucket hat sits on his final head anchors)
    // the KICK wide / medium: a cool fill low over the floor in front of the action (the Void's starlight, moved down
    // and toward the camera side) so the boards around the kick don't crush to black
    const kickFill = shot === 3 || shot === 9 ? { voidLight: { pos: add(M.V, [1.0, 0.55, 1.5]), intensity: 6.5, distance: 6.5, color: 0x8c9cff } } : {};
    set.update(t, { ...cornerOpts(t, t >= c.imp ? mag : null), broomSlide: 0, rollBucket: 0, lights: ROOM_LIGHTS, ...(shot === 7 ? { voidLight: 0.5 } : {}), ...kickFill });
    placeHatBucket(t, set, st.hatBase);
    // the tipped wringer is nudged back a hand's width so his flopped right arm doesn't sink into it
    if (t > c.imp && set.props.wringer) set.props.wringer.position.add(V(LD(0.12, 0, -0.12)).multiplyScalar(smooth(clamp((t - c.imp - 0.3) / 0.5))));
    mag.root.visible = shot !== 4;   // the insert: he is long gone

    // ------------------------------------------------------------------ props + particles
    placeDagger(st, t, c, M);
    fx.begin(); fxN.begin();
    drawStar(fx, t, heldStar(vd, starAt(t)), CELL, shot === 7 ? 1.25 : 1);
    // contact: a soft grey "poof" off his tailcoat + a couple of tiny star glints
    fxN.burst({ t, at: c.contact, count: 6, seed: 2011, life: 0.7, jitter: 0.03, origin: st.chest0, vel: [0.5, 0.3, -0.5], spread: [0.4, 0.35, 0.4], drag: 3,
      size: [0.12, 0.22], grow: 2.0, color: [0x9890a6, 0x8a8298], alpha: 0.4, fade: [0.08, 0.6], cell: CELL.puff, spin: 0.8 });
    fx.burst({ t, at: c.contact, count: 5, seed: 2012, life: 0.45, origin: st.chest0, vel: [0, 0.4, 0], spread: [0.9, 0.7, 0.9], drag: 4,
      size: [0.04, 0.07], color: [0xfff1c8, 0xd8ccff], alpha: 0.9, fade: [0.05, 0.6], cell: CELL.star, spin: 2 });
    // flight: a sparse grey dust trail from the pouch
    const tau = flightTau(t);
    if (tau !== null && tau < c.F) {
      fxN.stream({ t, seed: 2013, t0: c.contact, t1: c.imp, rate: 9, life: 0.9, origin: (tb) => add(flightPos(flightTau(tb) ?? 0, st.magRoot, M.CRASH).pos, [0, 0.85, 0]),
        vel: [0, -0.15, 0], spread: [0.15, 0.1, 0.15], size: [0.025, 0.045], color: [0xb0aabb, 0x8f8a9c], alpha: 0.55, fade: [0.1, 0.5], cell: CELL.dust });
    }
    // the slam: a dust burst out of the pile
    fxN.burst({ t, at: c.imp, count: 9, seed: 2017, life: 1.1, jitter: 0.04, origin: add(M.CRASH, [0, 0.45, 0]), vel: [0, 0.35, 0], spread: [0.9, 0.4, 0.9], drag: 2.5,
      size: [0.18, 0.32], grow: 2.2, color: [0x9d97aa, 0x8b8598], alpha: 0.42, fade: [0.06, 0.6], cell: CELL.puff, spin: 0.6 });
    // the pouch flops into his lap and puffs his own grey dust up onto him: a dense, slow mushroom
    const lap = A(mag.anchor('belly') || M.CRASH);
    fxN.burst({ t, at: c.puff, count: 16, seed: 2014, life: 1.9, jitter: 0.06, origin: [lap[0], lap[1] + 0.08, lap[2]], vel: [0, 0.6, 0], spread: [0.28, 0.3, 0.28], drag: 2.0,
      size: [0.16, 0.3], grow: 2.4, color: [0xa7a1b2, 0x948ea3, 0xb9b3c4], alpha: 0.62, fade: [0.08, 0.6], cell: CELL.puff, spin: 0.5 });
    fx.burst({ t, at: c.puff, count: 16, seed: 2015, life: 1.5, jitter: 0.08, origin: [lap[0], lap[1] + 0.15, lap[2]], vel: [0, 0.6, 0], spread: [0.35, 0.3, 0.35], drag: 1.8,
      size: [0.022, 0.036], color: [0xd6d2e0, 0xbab4c8], alpha: 0.75, fade: [0.1, 0.5], cell: CELL.dust, twinkle: true });
    // the sign slaps down: a little floor dust
    fxN.burst({ t, at: c.sign1, count: 7, seed: 2016, life: 0.9, origin: add(M.CRASH, LD(-0.4, 0.15, 0.3)), vel: [0, 0.25, 0], spread: [0.6, 0.12, 0.6], drag: 3,
      size: [0.12, 0.22], grow: 2, color: 0x948c9c, alpha: 0.35, fade: [0.08, 0.6], cell: CELL.puff });
    // birdies: five readable little stars circling the bucket rim (the rig's own are tiny; switched off in magPose)
    drawBirdies(fx, t, c, set, mag);
    fx.end(); fxN.end();

    if (globalThis.DBG20) dbg(st, t, app);
    // per-shot lift (cut points only): the dark velvet wides need the most, the bright corner + close-ups the least
    const ev = [0.3, 0.38, 0.3, 0.55, 0.45, 0.5, 0.32, 0.35, 0.32, 0.55][shot] ?? 0.45;
    st.look = brighten(lookFor(ID, set.look), ev);
  },
};

// ======================================================================================================== helpers
function rotY(v, yaw) { const c = Math.cos(yaw), s = Math.sin(yaw); return [v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c]; }

/**
 * Body fields that cancel the rig's kick posture so the Void's TOP HALF stays exactly where it was: the rig tips the
 * whole body forward about its front-bottom (kP * (0.42 + ...)), leans it (+0.1 kP) and hunches/tips it back a touch
 * in the wind-up. We subtract all of it; only the leg, the hem curtain and the foot move.
 */
function kickBody(kickV, aimY) {
  const kick = clamp(kickV, -0.5, 1.25), kP = Math.max(0, kick), kM = Math.max(0, -kick) / 0.5;
  const tip = kP * (0.42 + 0.16 * clamp((aimY - 1.1) / 0.6)) - kM * 0.05;
  return { lean: -0.1 * kP + 0.05 * kM, hunch: -0.1 * kM, pitch: -tip, headPitch: -0.05 * kM };
}
/** the Void's kick pose used by the contact solve (must match vPose at the contact frame) */
function kickVoid(M, kickV, aimP, reach = 1) {
  const KB = kickBody(kickV, aimP[1]);
  return { pos: M.V, yaw: M.yV, body: { lean: 0.12 + KB.lean, hunch: KB.hunch, pitch: KB.pitch, breathe: 0.3, breathRate: 0.2 }, head: { pitch: 0.25 + KB.headPitch, yaw: 0.3, roll: 0.03 },
    extra: { kick: kickV, kickSide: 'L', kickTarget: aimP, kickLevel: 1, kickReach: reach } };
}

function shotId(t, c) {
  if (c.cutA === undefined) { c.cutA = c.shouting + 0.12; }
  if (t < c.cutA) return 0;          // A VOID_LOW
  if (t < c.B2) return 1;            // B low two-shot
  if (c.kmed === undefined) { c.kmed = c.B4; }
  if (t < c.B3) return 2;            // C MAG_MED
  if (t < c.kmed) return 3;          // D KICK wide (the set-up + the wind-up)
  if (t < c.B5) return 9;            // D2 KICK medium, side-on: the contact hold, the launch, the hanging hat
  if (t < c.B6) return 4;            // E floor insert
  if (t < c.imp - 0.2) return 5;     // F flight follow
  if (t < c.fearCut0) return 6;      // G corner (impact)
  if (t < c.fearCut1) return 7;      // H Fear cutaway
  return 8;                          // I corner hold
}

// ---------------------------------------------------------------------------------------------- Fear
function fearWalk(t, c, M) {
  const w0 = c.obvious + 0.12, dur = 2.5, w1 = w0 + dur;
  const from = M.FDOOR, to = M.FOUT;
  const D = Math.hypot(to[0] - from[0], to[2] - from[2]);
  const u = clamp((t - w0) / dur);
  const pu = smooth(u) * 0.75 + u * 0.25;
  const pos = mix3(from, to, pu);
  pos[1] = (c.plate ?? 0.04) * (1 - smooth(clamp((pu - 0.25) / 0.2)));   // steps down off the cage's base plate
  const outYaw = Math.atan2(to[0] - from[0], to[2] - from[2]);
  const yaw = k(t, [[w0 - 0.4, M.yFDOOR], [w0 + 0.3, outYaw, 'inOut'], [w1 - 0.6, outYaw], [w1 + 0.3, M.yFOUT, 'inOut']]);
  const amount = pulse(t, w0 - 0.05, w1 + 0.1, 0.25, 0.3);
  return { pos, yaw, amount, phase: (pu * D) / (4 * 0.05), w0, w1 };
}
function fearPoseAt(st, t, c, M) {
  const s = heldStar(st.vd, starAt(t));   // the star where it really is: on the Void's fingertip
  const wk = fearWalk(t, c, M);
  const vEyes = st.vd.anchor('eyes');
  const look = s.lit > 0.2 ? s.pos : (vEyes ? A(vEyes) : add(M.V, [0, 2.1, 0]));
  // faces: hopeful up at the Void -> the star catches its eye (enchanted: lids wide, inner brows up, big pupils) ->
  // the 'o' -> a tiny delighted smile -> the flinch
  const Fhope = FX('hopeful', { mSmile: 0.18, lidU: 1.04, browIn: 0.55 });
  const Fench = FX([['wonder', 0.55], ['hopeful', 0.45]], { mOpen: 0.06, mRound: 0.25, mSmile: 0.16, mAsym: 0.14, lidU: 1.26, lidL: 0, browIn: 0.85, browOut: 0.45, lidSad: 0, pupil: 1.5, wet: 0.7 });
  const Fo = FX('wonder', { mOpen: 0.22, mRound: 0.7, mSmile: 0.05, pupil: 1.45, lidU: 1.24, lidSad: 0, browIn: 0.8 });
  const Fdelight = FX([['wonder', 0.55], ['shySmile', 0.45]], { mOpen: 0.08, mSmile: 0.34, mAsym: 0.22, pupil: 1.4, lidU: 1.1, lidSad: 0, gazePitch: 0, gazeYaw: 0 });
  const Fflinch = FX('startle', { pupil: 0.7 });
  let face = k(t, [[ID, Fhope], [c.making + 0.12, Fhope], [c.making + 0.45, Fench, 'inOut'], [c.B3 - 0.2, Fench], [c.B3 + 0.3, Fo, 'inOut'],
    [c.contact + 0.15, Fo], [c.contact + 0.7, Fdelight, 'inOut'], [c.fearCut0 - 0.02, Fdelight], [c.fearCut0 + 0.06, Fflinch, 'out'], [c.fearCut0 + 0.5, Fflinch],
    [c.fearCut0 + 1.2, mixFace(Fflinch, Fench, 0.6), 'inOut']]);
  face = { ...face, autoBlink: 0 };
  // the flinch at the crash (lands just inside the 0.6 s cutaway)
  const fl0 = c.fearCut0 + 0.02;
  const startle = k(t, [[fl0, 0], [fl0 + 0.06, 1, 'out'], [fl0 + 0.6, 0, 'inOut']]);
  const dart = pulse(t, fl0 + 0.05, fl0 + 0.9, 0.05, 0.3);
  // gaze: the Void's eyes, then the star; at the crash the eyes dart hard toward the corner (screen-right)
  const corner = add(M.CRASH, [0, 0.6, 0]);
  const gz = mix3(look, mix3(look, corner, 0.92), dart);
  return {
    pos: wk.pos, yaw: wk.yaw,
    walk: { amount: wk.amount, phase: wk.phase, style: 'sneak' },
    body: { tiptoe: 0.25 * pulse(t, c.B3, c.B4 + 0.5, 0.5, 0.5), idle: 0.6, breathe: 0.9, recoil: 0.08 * startle },
    head: { look: mix3(look, corner, 0.25 * dart), track: k(t, [[ID, 0.5], [c.making + 0.1, 0.5], [c.making + 0.5, 0.78, 'inOut']]), yaw: -0.16 * smooth(clamp((t - c.making) / 1.0)), roll: -0.06 + 0.05 * Math.sin((t - c.B3) * 1.6) * smooth(clamp((t - c.B3) / 1.2)) },
    gaze: gz,
    face,
    blinkAt: [c.making + 0.2, c.B3 + 0.75, c.fearCut0 + 0.04, c.imp + 2.0],
    armL: { preset: 'clasp', from: 'tiptoe', mix: 1 - wk.amount }, armR: { preset: 'clasp', from: 'tiptoe', mix: 1 - wk.amount },
    extra: { tuftPerk: Math.max(0.45 * smooth(clamp((t - c.making - 0.1) / 0.5)), startle), startle, glow: 1.1, tremble: 0.05,
      cry: 0.15 * (1 - smooth(clamp((t - T(ID)) / 2.5))) },
  };
}

// ---------------------------------------------------------------------------------------------- magician
function magPose(st, t, pass) {
  const { mag, fear } = st;
  const c = times(), M = marks();
  const fe = fear.anchor('eyes');
  const tau = flightTau(t);
  // --- before contact: s19's last spot (on his toes at PEEK, dagger high) -> last tiptoe step in -> dagger right up on
  // "stab" (toothy grin, popping eyes) -> folded double at the Void's flank, dagger cocked by his ear, tongue out
  if (tau === null) {
    const step = k(t, [[c.B2 + 0.1, 0], [c.B2 + 1.1, 1, 'inOut']]);
    const p0 = ROOM.W(MAGPATH.PEEK), y0 = M.yPEEK + 0.5;
    const pos = mix3(p0, st.magRoot, step);
    const yaw = lerp(y0, KP.yaw, smooth(clamp((t - c.B2 - 0.1) / 0.9)));
    const walking = pulse(t, c.B2 + 0.05, c.B2 + 1.2, 0.15, 0.2);
    const fold = k(t, [[c.B3 + 0.02, 0], [c.B3 + 0.62, 1.06, 'out'], [c.B3 + 0.9, 1, 'inOut']]);
    const daggerUp = k(t, [[c.stab - 0.3, 0], [c.stab - 0.04, 1, 'out'], [c.B3 + 0.05, 1], [c.B3 + 0.55, 0, 'inOut']]);
    const uhoh = k(t, [[c.contact - 0.34, 0], [c.contact - 0.27, 1, 'out']]);
    const Fgloat = MX('gloat', { lidU: 1.0, lidL: 0.25, lidAngry: 0, browOut: 0.85 });
    // "grin at maximum, eyes popping with glee": the widest toothy grin, lids wide, tiny pupils
    const Fglee = MX('gloat', { mSmile: 1, mWide: 1, mOpen: 0.5, mTeethU: 1, mTeethL: 1, lidU: 1.4, lidL: 0, lidAngry: 0, browIn: 0.7, browOut: 1, browSq: 0, browAsym: 0.1, pupil: 0.5 });
    const Fbent = MX('gloat', { mSmile: 1, mWide: 0.9, mOpen: 0.24, mTeethU: 1, mTeethL: 0.8, lidU: 1.2, lidL: 0.05, lidAngry: 0, browOut: 0.95, pupil: 0.6 });
    let face = k(t, [[ID, Fgloat], [c.creepy, Fgloat], [c.stab - 0.25, Fgloat], [c.stab + 0.06, Fglee, 'out'], [c.B3 + 0.1, Fglee], [c.B3 + 0.6, Fbent, 'inOut']]);
    if (uhoh > 0) face = mixFlat(face, MX('uhoh'), uhoh);
    face = { ...face, autoBlink: 0 };
    const hit = t >= c.contact;          // the foot lands: eyes bulge, cheeks puff, he folds round it
    // the 5-frame hold on the foot (contact -> launch): the body folds round the sole (back rounds, hips + head come
    // forward over it, arms fly up), eyes bulge, cheeks puff, the hat lifts; the root slides so the chest stays ON the foot
    const sq = hit ? k(t, [[c.contact, 0], [c.contact + 0.05, 1, 'out'], [c.launch - 0.02, 1], [c.launch + 0.04, 0.4, 'in']]) : 0;
    if (hit) face = MX('popped', { mOpen: 0.1 + 0.06 * sq, mPout: 0.95, mWide: -0.3, mRound: 0.3, mTeethU: 0, mTeethL: 0, lidU: 1.5, pupil: 0.36, autoBlink: 0 });
    const head = A(mag.anchor('head') || add(M.PEEK2, [0, 1.7, 0]));
    const glee = smooth(clamp((t - (c.stab - 0.25)) / 0.3));
    const lean = lerp(0.25, KP.lean, fold) + 0.06 * Math.sin((t - c.B3) * 3) * smooth(clamp(fold)) * (1 - uhoh) - 0.42 * sq;
    const hatP = hit ? hatPath(st, t, c, M, null) : null;
    const camP = pass && sq > 0 && st.cam ? A(st.cam.position) : null;
    const sqOff = st.sqOff || [0, 0, 0];
    return {
      pos: add(pos, sqOff.map((x) => x * sq)), yaw,
      walk: { amount: walking, phase: 0.75 + (t - c.B2) * 1.1, style: 'sneak' },
      body: { tiptoe: lerp(1, 0.35, fold) * (1 - walking), crouch: lerp(0.04, KP.crouch, fold) + 0.1 * sq, peek: lerp(1.0, KP.peek, fold), lean, hunch: lerp(0.15, KP.hunch, fold) + 0.65 * sq, recoil: 0.2 * uhoh },
      // bent double he cranes his neck up so the face reads, turned toward Fear; on the foot the face whips to the lens
      head: { follow: pass ? lerp(lerp(0.3, 0.55, smooth(clamp(fold))), 0.75, sq) : 0, look: (camP && sq > 0.5 ? camP : fe) || undefined, pitch: -0.42 * smooth(clamp(fold)) - 0.1 * uhoh - 0.22 * glee * (1 - smooth(clamp(fold))) - 0.3 * sq },
      blinkAt: [c.creepy + 0.05, c.B3 + 0.45],
      gaze: pass ? (sq > 0.5 ? 'camera' : uhoh > 0.5 ? add(st.hip0 || M.V, [0.3, 0.2, 0]) : fe) : null,
      face,
      // the arms fling up and out above his folded back (world targets: readable whatever his fold)
      armR: sq > 0.01 ? { preset: [['dagger_ready', 1 - sq], ['up', sq]], target: add(st.chest0, [0.2, 0.72, 0.42]), reach: sq, hand: { spread: 0.6, curl: 0.1, splay: 0.4 } }
        : daggerUp > 0.01
          ? { preset: [['dagger_ready', 1 - daggerUp], ['up', daggerUp]], offset: [0, 0.36 * (1 - daggerUp) + 0.03 * Math.sin(t * 9) * daggerUp, 0] }
          : { preset: 'dagger_ready', offset: [0, 0.22 + 0.14 * (1 - smooth(clamp((t - c.B3) / 0.5))), 0] },
      armL: sq > 0.01 ? { preset: [['pouch', 1 - sq], ['up', sq]], target: add(st.chest0, [0.5, 0.66, -0.3]), reach: sq } : { preset: 'pouch' },
      extra: { eyePop: hit ? 1 : glee * (1 - 0.4 * smooth(clamp(fold))) * (1 - uhoh) + 0.7 * uhoh, tongueOut: 0.45 * smooth(clamp(fold)) * (1 - uhoh) * (1 - sq), tap: 0.4 * (1 - glee),
        hatOff: hit ? 1 : 0, ...(hatP ? { hatPos: hatP.pos, hatRot: hatP.rot } : {}), stars: 0 },
    };
  }
  // --- flight
  const start = st.magRoot, end = [M.CRASH[0], -0.62, M.CRASH[2]];   // the pelvis comes down to sitting height
  const fp = flightPos(tau, start, end);
  const kicked = k(t, [[c.launch - 0.02, 0], [c.launch + 0.06, 1, 'out']]);
  const parked = t >= c.launch + c.flightA && t < c.resume;
  const hatP = hatPath(st, t, c, M, fp);
  const dir = sub(end, start); const dl = Math.hypot(dir[0], dir[2]);
  const flipF = -(Math.PI * 2 + 0.55) * smooth(clamp(tau / c.F)) - 0.2 * Math.sin(tau * 3);
  if (t < c.imp) {
    return {
      pos: parked ? [fp.pos[0], 60, fp.pos[2]] : fp.pos, yaw: M.yCRASH,
      face: MX('popped', { mOpen: 0.95 }),
      gaze: null,
      extra: { kicked, flip: flipF, flail: 1.2, vel: [dir[0] / dl * 1.6, 0, dir[2] / dl * 1.6], hatOff: clamp((t - c.contact) / 0.12), hatPos: hatP.pos, hatRot: hatP.rot,
        dagger: false, pouch: true, eyePop: 1, stars: 0 },
    };
  }
  // --- the slam: back-first into the pile, tipped over onto his back, legs up (a squashy bounce), held a beat;
  // then he slides down into a crumpled sit (the bucket hat comes later)
  const flipEnd = -(Math.PI * 2 + 0.55) - 0.2 * Math.sin(c.F * 3);
  const slam = smooth(clamp((t - c.imp) / 0.12));
  const land = k(t, [[c.imp + 0.42, 0], [c.imp + 0.95, 1, 'inOut']]);
  const w = wreckPose(t, M);
  w.extra = { ...w.extra, stars: 0 };
  if (land < 1) {
    const bounce = 0.06 * jiggle(t, c.imp + 0.02, 1, 16, 6);
    w.extra.kicked = 1 - land;
    w.extra.flip = flipEnd - 0.5 * slam + 0.12 * jiggle(t, c.imp + 0.03, 1, 14, 5);
    w.extra.flail = 0.25 * (1 - slam) + 0.06;
    w.extra.vel = [0, 0, 0];
    w.pos = [M.CRASH[0], -0.62 * (1 - land) - 0.08 * slam * (1 - land) + bounce * (1 - land), M.CRASH[2]];
    w.face = MX([['ow', 0.7], ['popped', 0.3]]);
  } else {
    w.extra.kicked = 0;
    w.pos = [M.CRASH[0], 0, M.CRASH[2]];
  }
  w.body.bounce = 0.05 * jiggle(t, c.imp + 0.95, 1, 15, 6);
  w.body.slump += 0.3 * pulse(t, c.imp + 0.9, c.imp + 1.7, 0.1, 0.6);
  w.extra.hatPos = hatP.pos; w.extra.hatRot = hatP.rot;
  // between landing and the BONK: stunned, swaying ('ow' -> dazed)
  if (land >= 1 && t < c.bonk) w.face = MX([['ow', 0.6], ['dazed', 0.4]]);
  // after the sign: rigid (shoulders up, back straight), then the sag; "...How rude." (lip-sync under the bucket rim),
  // one finger lifts weakly and drops
  const rigid = pulse(t, c.sign1 - 0.02, c.sign1 + 0.55, 0.04, 0.3);
  if (rigid > 0) w.face = mixFlat(MX('dazed'), MX('startled'), rigid);
  const finger = pulse(t, c.rude + 0.05, c.rude + 0.75, 0.22, 0.25);
  if (t > c.B8 - 0.2) {
    w.face = MX('dazed', { talk: 0.55, mAsym: -0.3 + 0.12 * Math.sin(t * 9) * pulse(t, c.B8, c.B8 + 1.0, 0.1, 0.2) });
    const knee = A(mag.anchor('kneeR') || add(M.CRASH, [0, 0.5, 0]));
    w.armR = { preset: 'hang', target: add(knee, [0, 0.06 + 0.1 * finger, 0]), reach: 0.7 * finger, hand: { point: finger, curl: 0.6 } };
  }
  return w;
}
function mixFlat(a, b, u) {
  const o = { ...a };
  for (const key in b) if (typeof b[key] === 'number') o[key] = lerp(typeof a[key] === 'number' ? a[key] : 0, b[key], u);
  return o;
}
// the top hat: lifts off on contact, hangs a beat in the air, zips off after him, follows his arc a beat behind, lands
function hatPath(st, t, c, M, fp) {
  const h0 = st.hat0;
  const tz = c.launch + 0.66;                  // the hang ends; the hat zips after him
  if (t < tz) {
    // pops up off his head on the impact (most of the rise inside the 5-frame hold), then hangs in the air
    const u = ease.out(clamp((t - c.contact) / 0.3));
    return { pos: add(h0, [0, 0.36 * u + 0.015 * Math.sin((t - c.contact) * 9) * u, 0]), rot: [0.25 * u, 0.4 * u, -0.15 * u] };
  }
  const tau = flightTau(t) ?? 0;
  if (t < c.resume) {
    const u = ease.in(clamp((t - tz) / 0.25));
    const p = flightPos(c.flightA, st.magRoot, M.CRASH).pos;
    return { pos: mix3(add(h0, [0, 0.32, 0]), add(p, [0.2, 1.4, 0]), u), rot: [1.2 * u, 0.4, -0.15] };
  }
  const lag = Math.max(c.flightA, tau - 0.32);
  const p = flightPos(lag, st.magRoot, M.CRASH).pos;
  const rest = hatRestPos(M);
  const landU = smooth(clamp((t - (c.imp + 0.1)) / 0.45));
  const air = add(p, [0.1, 1.45, 0.05]);
  const pos = mix3(air, rest, landU);
  pos[1] += 0.3 * Math.sin(Math.PI * landU) + Math.max(0, jiggle(t, c.imp + 0.55, 0.05, 18, 7));
  return { pos, rot: [lerp(-2.5 * tau, 0.15, landU), lerp(0.4 + tau, 0.6, landU), lerp(-0.15, 1.45, landU)] };
}

// the dagger: in his fist until contact; spins away with him; falls out of the dark onto the floor point-down, wobbles
function placeDagger(st, t, c, M) {
  const d = st.dagger;
  const tau = flightTau(t);
  if (tau === null) { d.visible = false; return; }
  d.visible = true;
  const rest = daggerRestPos(M);
  const tl = c.daggerLand;
  if (t < c.imp) {
    if (t >= c.launch + c.flightA && t < c.resume) { d.visible = false; return; }
    const lag = Math.max(0, tau - 0.12);
    const p = flightPos(lag, st.magRoot, M.CRASH).pos;
    const pos = add(p, [0.25 + 0.08 * Math.sin(tau * 5), 1.9 + 0.25 * Math.sin(tau * 2.2), 0.3]);
    d.position.set(pos[0], pos[1], pos[2]);
    d.rotation.set(0.3, tau * 2.0, tau * 13.0);
    return;
  }
  if (t < tl - 0.3) { d.visible = false; return; }
  // the drop: from above the frame straight down, point first, THUNK, then a springy wobble
  const u = clamp((t - (tl - 0.3)) / 0.3);
  const y = 0.18 + 2.4 * (1 - u * u);
  const wob = t > tl ? 0.38 * Math.exp(-(t - tl) * 3.6) * Math.sin((t - tl) * 28) : 0;
  d.position.set(rest[0], y, rest[2]);
  d.rotation.set(0, 0.35, -Math.PI / 2 + wob + (1 - u) * 0.35);
}

// readable birdies: five little stars (and two tiny ones) orbiting the bucket rim at ~0.25 m, from the BONK
function drawBirdies(fx, t, c, set, mag) {
  if (t < c.bonk) return;
  const b = set.props.bucketHat;
  if (!b) return;
  const on = smooth(clamp((t - c.bonk) / 0.3));
  const p = new THREE.Vector3(); b.getWorldPosition(p);
  const h = A(mag.anchor('headTop') || p);
  const ctr = [h[0], h[1] + 0.06, h[2]];
  for (let i = 0; i < 5; i++) {
    const a = t * 2.6 + (i / 5) * Math.PI * 2;
    const q = [ctr[0] + Math.cos(a) * 0.27, ctr[1] + 0.04 * Math.sin(a * 2 + i), ctr[2] + Math.sin(a) * 0.2];
    fx.add(q, 0.075 + 0.01 * Math.sin(t * 5 + i), i % 2 ? 0xfff0b0 : 0xe8ecff, 0.95 * on, t * 2 + i, CELL.star);
  }
}

// ---------------------------------------------------------------------------------------------- cameras
function frameShot(st, t, shot, c, M) {
  const { vd, fear, mag } = st;
  const ve = A(vd.anchor('eyes')), fe = A(fear.anchor('eyes'));
  switch (shot) {
    case 0: { // VOID_LOW close from beside Fear at the cage door, up at the serene face; slow push
      const pos = ROOM.W(-0.95, 0.95, 3.35);
      const push = smooth(clamp((t - T(ID)) / (c.cutA - T(ID))));
      return aim(mix3(pos, ve, 0.08 * push), ve, 360, 380, 38, { drift: 0.1 });
    }
    case 1: { // low two-shot: the fingertip star / big hand upper-mid, Fear's upturned face lower-left (pans with Fear)
      const pos = ROOM.W(1.2, 0.5, 3.15);
      return aim(pos, fe, 225, 640, 42, { drift: 0.1 });
    }
    case 2: { // MAG_MED: 3/4 front on the magician from the camera side, the Void's hood soft in the left foreground
      const mh = A(mag.anchor('head'));
      return ROOM.shot(ROOM.L(mh), { dist: 2.45, yaw: -24, pitch: -4, fov: 36, screenY: sy(400), drift: 0.1 });
    }
    case 3: { // KICK wide, locked: Fear lower-left, the Void 3/4 (head cheat), the magician bent double at its right flank
      return aim(ROOM.W(2.55, 1.3, 7.6), ROOM.W(0.8, 0.62, 0.8), 98, 730, 50, { drift: 0 });
    }
    case 9: { // KICK medium, side-on, cut on "kicks": the sole lands mid-chest at y~640, the folded magician large at
      // right (his face reads), the Void's serene hood + smile + the fingertip star upper-left; locked (a tiny bump on
      // the impact)
      // (3/4 front on the kicking side, low: the leg clears the hem curtain; the Void's eyes land at x~85, y~375)
      const a = 12 * DEG, D = 8.0;
      const P = st.chest0, T0 = [P[0] - 1.0, 1.2, P[2] + 0.35];
      const pos = [T0[0] + D * Math.sin(a), 0.8, T0[2] + D * Math.cos(a)];
      const sh = aim(pos, P, 615, 650, 36, { drift: 0 });
      const sk = Math.exp(-Math.max(0, t - c.contact) * 10) * (t > c.contact ? 1 : 0);
      if (sk > 0.02) sh.shake = { amp: 0.01 * sk, freq: 12 };
      return sh;
    }
    case 4: { // the floor insert at the back hem: the retracting fat leg, the foot's wiggle, the hem bounce
      const vs = voidSpot(t);
      const p = add(vs.pos, rotY([0.42, 0.24, -1.15], vs.yaw));
      const pos = add(p, add(LD(1.8, 0, 1.6), [0, 0.1, 0]));
      return aim(pos, p, 380, 500, 36, { drift: 0.05 });
    }
    case 5: { // the flight: from the camera side inside the room, panning with him toward the corner
      const pos = ROOM.W(3.0, 1.45, 3.9);
      const mp = A(mag.anchor('hip') || M.CRASH);
      return aim(pos, mp, 380, 470, 46, { drift: 0.05 });
    }
    case 6: case 8: { // CORNER medium, locked (a short shake on the impact)
      const cc = add(M.CRASH, [0, 0.62, 0]);
      const sh = ROOM.shot(ROOM.L(cc), { dist: 3.7, yaw: -8, pitch: 10, fov: 40, screenY: sy(560), drift: 0 });
      const sk = Math.exp(-Math.max(0, t - c.imp) * 9) * (t > c.imp ? 1 : 0);
      if (sk > 0.02) sh.shake = { amp: 0.014 * sk, freq: 11 };
      return sh;
    }
    case 7: // FEAR_CU from the Void side, the fingertip star at the top edge (= s21's opening setup)
      return fearCU(fe, 0);
  }
  return ROOM.cam('MASTER');
}
function dbg(st, t, app) {
  const cam = app.camera, o = {};
  const ps = { mDag: st.mag.anchor('dagger'), mHat: st.mag.anchor('hat'), vEyes: st.vd.anchor('eyes'), hood: st.vd.anchor('hoodTop'), fEyes: st.fear.anchor('eyes'), mHead: st.mag.anchor('head'), mEyes: st.mag.anchor('eyes'), mChest: st.mag.anchor('chest'), kick: st.vd.anchor('kickFoot'), star: starAt(t).pos, held: heldStar(st.vd, starAt(t)).pos, dagger: st.dagger.visible ? st.dagger.position : null };
  for (const [n, p] of Object.entries(ps)) if (p) o[n] = pix(cam, p);
  console.log('DBG20', t.toFixed(2), 'shot', st.shot, JSON.stringify(o), 'foot-chest', st.vd.anchor('kickFoot').distanceTo(V(st.chest0)).toFixed(3), 'kv', (st.kv ?? 0).toFixed(3));
}
