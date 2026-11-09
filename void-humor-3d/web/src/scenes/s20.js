// s20 the_kick — no fuss. The Void's top half is serene, steering Fear's gaze with a star on one fingertip; its bottom
// half is one fat leg and one perfect donkey kick into the bent-over magician's chest. Rubber-hose flight into the
// janitor corner: buckets, BONK (bucket hat), mop wig, birdies, the dagger thunks into the floor, a grey puff, and the
// wet-floor sign that teetered all along tips onto him last. "...How rude."
//
// Shots (all from beat refs / word times):
//   A  scene start -> "shouting"+   VOID_LOW close (serene face, slow blink: it does not shout)
//   B  -> s20b02                   low two-shot: the Void's fingertip rises, a star lights on "making"; Fear's eyes catch
//                                  it and it lures Fear out of the cage door (FDOOR -> FOUT, tiptoe)
//   C  s20b02 -> b03               MAG_MED: last tiptoe step in, dagger high on "stab", grin at max
//   D  s20b03 -> b05               KICK wide (locked): magician bent double over the hem, the Void blinks; chamber, KICK on
//                                  "kicks" (top half still), he launches out of frame right, his hat hangs a beat, then zips
//   E  s20b05 -> b06               floor insert: the fat leg retracts, the foot's satisfied wiggle on "leg", hem bounce
//   F  s20b06 -> impact            follow-pan on the flight (left -> right), limbs pinwheeling, hat + dagger behind
//   G  impact                      CORNER: he crashes in under "buckets"
//   H  +0.30 .. +0.90              0.6 s cutaway: Fear flinches (tuft up, scarf jumps), the star stays steady
//   I  -> end                      CORNER locked: BONK, mop wig, birdies, dagger thunk, grey puff, the sign, "...How rude."
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, ease, fbm1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { MX } from '../chars/magician.js';
import { ROOM, sy, lookFor } from './marks.js';
import {
  loadLines, W, V, A, add, sub, mix3, LD, pulse, jiggle, stamp, own, solve, aim, blendShot, pix, marks, times,
  voidSpot, starAt, drawStar, flightTau, flightPos, wreckPose, hatRestPos, daggerRestPos, cornerOpts, placeHatBucket,
} from './kit_s20_22.js';

const ID = 's20';
globalThis.DBG20 = true; // DEV

export default {
  id: ID,
  async setup(app) {
    await loadLines();
    const set = await app.set('BACKROOM');
    ROOM.fit(set);
    const [vd, fear, mag] = await Promise.all([app.char('VOID'), app.char('FEAR'), app.char('MAGICIAN')]);
    const fx = new Particles({ max: 160, intensity: 1.5 });
    const fxN = new Particles({ max: 40, blending: 'normal', intensity: 1.0 });
    own(ID, fx.mesh); own(ID, fxN.mesh);
    // the dagger that flies out of his hand (a clone of his prop: shares geometry + materials)
    const dagger = mag.dagger.clone(true);
    dagger.rotation.order = 'YXZ';
    own(ID, dagger);
    // where the hat bucket stands before the crash (its local transform in the corner group)
    set.update(0, {});
    const hatBase = A(set.props.bucketHat.position.clone());
    const st = { scene: set.scene, set, vd, fear, mag, fx, fxN, dagger, hatBase, look: lookFor(ID, set.look) };
    // contact geometry, measured once from the rigs (robust to rig refinements): the Void's fat leg at full extension
    // aims at his chest (inside its cone); slide the bent-over magician until his chest meets the foot.
    const c = times(), M = marks();
    st.magRoot = M.PEEK2.slice();
    let F = null;
    for (let i = 0; i < 4; i++) {
      mag.update(c.contact - 0.01, { ...magPose(st, c.contact - 0.01, 0) });
      const C = A(mag.anchor('chest'));
      vd.update(c.contact, { pos: M.V, yaw: M.yV, body: { lean: 0.12, pitch: -0.17 }, head: { pitch: 0.25, yaw: 0.3 }, extra: { kick: 1.0, kickSide: 'L', kickTarget: C, kickLevel: 1 } });
      F = A(vd.anchor('kickFoot'));
      st.magRoot = [st.magRoot[0] + 0.9 * (F[0] - C[0]), 0, st.magRoot[2] + 0.9 * (F[2] - C[2])];
      st.contactErr = Math.hypot(F[0] - C[0], F[1] - C[1], F[2] - C[2]);
    }
    mag.update(c.contact - 0.01, { ...magPose(st, c.contact - 0.01, 0) });
    st.chest0 = A(mag.anchor('chest'));
    st.foot0 = F;
    st.hat0 = A(mag.anchor('hat'));
    console.log('s20 contact: magician root', st.magRoot.map((x) => x.toFixed(2)).join(','), 'chest', st.chest0.map((x) => x.toFixed(2)).join(','), 'foot', F.map((x) => x.toFixed(2)).join(','), 'err', st.contactErr.toFixed(3));
    return st;
  },

  async update(t, app, st) {
    stamp(ID, t);
    const { set, vd, fear, mag, fx, fxN, dagger } = st;
    for (const o of [vd.root, fear.root, mag.root, fx.mesh, fxN.mesh, dagger]) st.scene.add(o);
    const c = times(), M = marks();
    const shot = shotId(t, c);
    st.shot = shot;

    // ------------------------------------------------------------------ VOID
    const vs = voidSpot(t);
    const kickV = k(t, [[c.B4 - 0.32, 0], [c.kickFire, -0.5, 'inOut'], [c.contact, 1.0, 'out'], [c.launch + 0.04, 1.1, 'out'], [c.launch + 0.2, 1.0, 'inOut'],
      [c.B5 - 0.05, 0.96, 'inOut'], [c.B5 + 0.3, 1.0, 'inOut'], [c.leg + 0.35, 1.0], [c.leg + 0.62, 0.0, 'in']]);
    const kP = Math.max(0, kickV);
    st.kv = kickV;
    // the kick target: frozen chest -> (insert) a spot just outside the back hem at floor level, where the foot wiggles
    const hemOut = add(vs.pos, add(LD(0, 0, 0), rotY([0.42, 0.2, -1.22], vs.yaw)));
    const wig = pulse(t, c.leg - 0.05, c.leg + 0.4, 0.06, 0.1);
    const kt = mix3(st.chest0, hemOut, k(t, [[c.B5, 0], [c.B5 + 0.32, 1, 'inOut']]));
    const kTarget = add(kt, rotY([0.05 * wig * Math.sin((t - c.leg) * 26), 0.02 * wig * Math.abs(Math.sin((t - c.leg) * 26)), 0], vs.yaw));
    const hemBounce = Math.max(0, jiggle(t, c.leg + 0.6, 0.18, 15, 5));
    const vPose = (pass) => {
      const fe = pass ? fear.anchor('eyes') : null;
      const s = starAt(t);
      const fw = add(fearWalk(t, c, M).pos, [0, 0.62, 0]);
      const Fserene = VX('gentle', { lidU: 0.8, lidL: 0.42, mSmile: 0.5, browIn: 0.3, blush: 0.15 });
      const Fsoft = VX('gentle', { lidU: 0.74, lidL: 0.5, mSmile: 0.56, browIn: 0.36, blush: 0.2 });
      const Fkick = VX('gentle', { lidU: 0.72, lidL: 0.52, mSmile: 0.6, browIn: 0.3, mPress: 0.2, blush: 0.2 });
      const face = k(t, [[ID, Fserene], [c.making, Fserene], [c.making + 0.6, Fsoft, 'inOut'], [c.B4 - 0.2, Fsoft], [c.contact, Fkick, 'out'], [c.contact + 0.6, Fsoft, 'inOut']]);
      face.autoBlink = 0;
      // the LEFT (camera-side) fingertip carries the star (index up, palm toward Fear); the right hand rests on its belly
      const reach = k(t, [[c.B1 + 0.7, 0], [c.making - 0.05, 1, 'inOut']]);
      const towardF = sub(fw, s.pos);
      const hz = Math.hypot(towardF[0], towardF[2]) || 1;
      const fdir = [towardF[0] / hz * 0.35, 1, towardF[2] / hz * 0.35];
      const down = [towardF[0] / hz * 0.3, -1, towardF[2] / hz * 0.3];
      const fing = mix3(down, fdir, smooth(reach));
      const head = { pitch: 0.25, yaw: shot >= 3 ? 0.3 : 0.08, roll: 0.03 };
      return {
        pos: vs.pos, yaw: vs.yaw,
        body: { lean: 0.12, pitch: -0.17 * Math.min(kP, 1), breathe: 0.9 - 0.6 * pulse(t, c.B3, c.contact + 0.2, 0.4, 0.3), breathRate: 0.2 },
        head,
        gaze: pass ? fe : null,
        face,
        blinkAt: [c.B1 + 0.42, c.B3 + 0.36, c.contact + 0.9],
        armL: { preset: 'point', target: s.pos, tip: true, reach, fingers: fing, palm: [towardF[0] / hz, 0.1, towardF[2] / hz], hand: { point: 1, curl: 0.55, thumb: 0.35 } },
        armR: { preset: 'belly', from: 'rest', mix: k(t, [[c.B2, 0], [c.B3 + 0.6, 1, 'inOut']]) },
        extra: { kick: kickV, kickSide: 'L', kickTarget: kTarget, kickLevel: 1, stars: 1.4, hem: hemBounce, motes: 0.8 },
      };
    };

    // ------------------------------------------------------------------ FEAR
    const fearPose = (tt) => fearPoseAt(st, tt, c, M);
    // ------------------------------------------------------------------ MAGICIAN
    const mPose = (pass) => magPose(st, t, pass);

    // ------------------------------------------------------------------ set
    // ------------------------------------------------------------------ solve (camera from pass-0 anchors)
    const shotStart = [ID, c.cutA, c.B2, c.B3, c.B5, c.B6, c.imp - 0.2, c.fearCut0, c.fearCut1][shot] ?? ID;
    solve(t, [[vd, vPose], [mag, mPose], [fear, (pass) => (pass ? (tt) => fearPose(Math.max(tt, T(shotStart))) : fearPose(t))]], () => {
      applyShot(app.camera, frameShot(st, t, shot, c, M), t, 20);
    });
    // the corner (after the rigs: the bucket hat sits on his final head anchors)
    set.update(t, { ...cornerOpts(t, t >= c.imp ? mag : null), broomSlide: 0, rollBucket: 0 });
    placeHatBucket(t, set, st.hatBase);
    mag.root.visible = shot !== 4;   // the insert: he is long gone

    // ------------------------------------------------------------------ props + particles
    placeDagger(st, t, c, M);
    fx.begin(); fxN.begin();
    drawStar(fx, t, starAt(t), CELL, shot === 7 ? 1.2 : 1);
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
    // the pouch flops into his lap and puffs his own grey dust up onto him
    const lap = A(mag.anchor('belly') || M.CRASH);
    fxN.burst({ t, at: c.puff, count: 10, seed: 2014, life: 1.5, jitter: 0.08, origin: [lap[0], lap[1] + 0.1, lap[2]], vel: [0, 0.45, 0], spread: [0.3, 0.25, 0.3], drag: 2.2,
      size: [0.14, 0.28], grow: 2.2, color: [0xa7a1b2, 0x948ea3], alpha: 0.42, fade: [0.12, 0.55], cell: CELL.puff, spin: 0.5 });
    fx.burst({ t, at: c.puff, count: 14, seed: 2015, life: 1.3, jitter: 0.1, origin: [lap[0], lap[1] + 0.15, lap[2]], vel: [0, 0.55, 0], spread: [0.35, 0.3, 0.35], drag: 1.8,
      size: [0.018, 0.03], color: [0xd6d2e0, 0xbab4c8], alpha: 0.7, fade: [0.1, 0.5], cell: CELL.dust, twinkle: true });
    // the sign slaps down: a little floor dust
    fxN.burst({ t, at: c.sign1, count: 6, seed: 2016, life: 0.9, origin: add(M.CRASH, LD(-0.55, 0.08, 0.35)), vel: [0, 0.25, 0], spread: [0.6, 0.12, 0.6], drag: 3,
      size: [0.12, 0.2], grow: 2, color: 0x948c9c, alpha: 0.3, fade: [0.08, 0.6], cell: CELL.puff });
    fx.end(); fxN.end();

    if (globalThis.DBG20) dbg(st, t, app);
    st.look = lookFor(ID, set.look);
  },
};

// ======================================================================================================== helpers
function rotY(v, yaw) { const c = Math.cos(yaw), s = Math.sin(yaw); return [v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c]; }

function shotId(t, c) {
  if (c.cutA === undefined) { c.cutA = c.shouting + 0.12; }
  if (t < c.cutA) return 0;          // A VOID_LOW
  if (t < c.B2) return 1;            // B low two-shot
  if (t < c.B3) return 2;            // C MAG_MED
  if (t < c.B5) return 3;            // D KICK wide
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
  const outYaw = Math.atan2(to[0] - from[0], to[2] - from[2]);
  const yaw = k(t, [[w0 - 0.4, M.yFDOOR], [w0 + 0.3, outYaw, 'inOut'], [w1 - 0.6, outYaw], [w1 + 0.3, M.yFOUT, 'inOut']]);
  const amount = pulse(t, w0 - 0.05, w1 + 0.1, 0.25, 0.3);
  return { pos, yaw, amount, phase: (pu * D) / (4 * 0.05), w0, w1 };
}
function fearPoseAt(st, t, c, M) {
  const s = starAt(t);
  const wk = fearWalk(t, c, M);
  const vEyes = st.vd.anchor('eyes');
  const look = s.lit > 0.2 ? s.pos : (vEyes ? A(vEyes) : add(M.V, [0, 2.1, 0]));
  // faces: hopeful up at the Void -> the star catches its eye (enchanted) -> the 'o' -> a tiny delighted smile
  const Fhope = FX('hopeful', { mSmile: 0.18, lidU: 1.04, browIn: 0.55 });
  const Fench = FX([['wonder', 0.6], ['hopeful', 0.4]], { mSmile: 0.12, mAsym: 0.18, pupil: 1.3 });
  const Fo = FX('wonder', { mOpen: 0.22, mRound: 0.7, mSmile: 0.05, pupil: 1.4, lidU: 1.12 });
  const Fdelight = FX([['wonder', 0.55], ['shySmile', 0.45]], { mOpen: 0.08, mSmile: 0.34, mAsym: 0.22, pupil: 1.35, lidU: 1.0 });
  const Fflinch = FX('startle', { pupil: 0.7 });
  let face = k(t, [[ID, Fhope], [c.making + 0.12, Fhope], [c.making + 0.45, Fench, 'inOut'], [c.B3 - 0.2, Fench], [c.B3 + 0.3, Fo, 'inOut'],
    [c.contact + 0.15, Fo], [c.contact + 0.7, Fdelight, 'inOut'], [c.fearCut0 + 0.04, Fdelight], [c.fearCut0 + 0.1, Fflinch, 'out'], [c.fearCut0 + 0.5, Fflinch],
    [c.fearCut0 + 1.2, mixFace(Fflinch, Fench, 0.6), 'inOut']]);
  face = { ...face, autoBlink: 0 };
  // the flinch at the crash
  const fl0 = c.fearCut0 + 0.05;    // Fear's flinch lands just inside the 0.6 s cutaway
  const startle = k(t, [[fl0, 0], [fl0 + 0.06, 1, 'out'], [fl0 + 0.6, 0, 'inOut']]);
  const dart = pulse(t, fl0 + 0.04, fl0 + 0.75, 0.05, 0.25);
  // gaze: the Void's eyes, then the star; at the crash the eyes dart toward the corner (past its right shoulder)
  const corner = add(M.CRASH, [0, 0.6, 0]);
  const gz = mix3(look, mix3(look, corner, 0.55), dart);
    return {
    pos: wk.pos, yaw: wk.yaw,
    walk: { amount: wk.amount, phase: wk.phase, style: 'sneak' },
    body: { tiptoe: 0.25 * pulse(t, c.B3, c.B4 + 0.5, 0.5, 0.5), idle: 0.6, breathe: 0.9 },
    head: { look, track: k(t, [[ID, 0.5], [c.making + 0.1, 0.5], [c.making + 0.5, 0.62, 'inOut']]), yaw: -0.16 * smooth(clamp((t - c.making) / 1.0)), roll: -0.06 + 0.05 * Math.sin((t - c.B3) * 1.6) * smooth(clamp((t - c.B3) / 1.2)) },
    gaze: gz,
    face,
    blinkAt: [c.making + 0.2, c.B3 + 0.75, c.fearCut0 + 0.06, c.imp + 1.6],
    armL: { preset: 'clasp', from: 'tiptoe', mix: 1 - wk.amount }, armR: { preset: 'clasp', from: 'tiptoe', mix: 1 - wk.amount },
    extra: { tuftPerk: Math.max(0.45 * smooth(clamp((t - c.making - 0.1) / 0.5)), startle), startle, glow: 1.25, tremble: 0.05 },
  };
}

// ---------------------------------------------------------------------------------------------- magician
function magPose(st, t, pass) {
  const { mag, fear } = st;
  const c = times(), M = marks();
  const fe = fear.anchor('eyes');
  const tau = flightTau(t);
  // --- before contact: lurking at PEEK -> last tiptoe step in -> dagger high -> folded deep over the hem
  if (tau === null) {
    const step = k(t, [[c.B2 + 0.05, 0], [c.B2 + 1.15, 1, 'inOut']]);
    const back = LD(0.34, 0, -0.16);
    const pos = add(st.magRoot || M.PEEK2, [back[0] * (1 - step), 0, back[2] * (1 - step)]);
    const walking = pulse(t, c.B2 + 0.0, c.B2 + 1.25, 0.15, 0.2);
    const fold = k(t, [[c.B3 - 0.05, 0], [c.B3 + 0.75, 1, 'inOut']]);
    const daggerUp = k(t, [[c.stab - 0.35, 0], [c.stab - 0.05, 1, 'out'], [c.B3 + 0.1, 1], [c.B3 + 0.6, 0, 'inOut']]);
    const uhoh = k(t, [[c.contact - 0.34, 0], [c.contact - 0.26, 1, 'out']]);
    const Flurk = MX('lurk', { pupil: 0.9 });
    const Fgloat = MX('gloat', { lidU: 0.95, lidL: 0.3, browOut: 0.9 });
    const Fglee = MX('gloat', { lidU: 1.22, lidL: 0.1, browIn: 0.35, browOut: 1, mTongue: 1, pupil: 0.75 });
    let face = k(t, [[ID, Flurk], [c.creepy, Flurk], [c.creepy + 0.35, Fgloat, 'inOut'], [c.stab - 0.2, Fgloat], [c.stab + 0.1, Fglee, 'out'], [c.contact - 0.34, Fglee]]);
    if (uhoh > 0) face = mixFlat(face, MX('uhoh'), uhoh);
    const hit = t >= c.contact;          // the foot lands: eyes bulge, cheeks puff, he folds round it
    if (hit) face = MX('popped', { mOpen: 0.12, mPout: 0.8, mWide: -0.2, mTeethU: 0, mTeethL: 0 });
    const head = A(mag.anchor('head') || add(M.PEEK2, [0, 1.7, 0]));
    return {
      pos, yaw: M.yPEEK,
      walk: { amount: walking, phase: (t - c.B2) * 1.25, style: 'sneak' },
      body: { tiptoe: 0.6 * (1 - fold) * (1 - walking), crouch: lerp(0.3, 0.22, fold) * (1 - 0.7 * walking), peek: lerp(0.65, 1.0, fold), lean: 1.05 * fold + 0.08 * Math.sin((t - c.B3) * 3) * fold, hunch: 0.25 * fold, recoil: 0.2 * uhoh },
      head: { follow: pass ? 0.5 : 0, pitch: -0.1 * uhoh },
      gaze: pass ? (uhoh > 0.5 ? add(M.V, [0.2, 0.5, 0.1]) : fe) : null,
      face,
      armR: daggerUp > 0.01 ? { preset: 'up', reach: daggerUp, target: add(head, add(LD(-0.22, 0.5, 0.18), [0, 0.04 * Math.sin(t * 9) * daggerUp, 0])) } : { preset: 'dagger_ready' },
      armL: { preset: 'pouch' },
      extra: { eyePop: hit ? 1 : 0.5 * smooth(clamp((t - c.stab) / 0.2)) * (1 - uhoh) + 0.6 * uhoh, tongueOut: 0.35 * fold * (1 - uhoh), tap: 0.4,
        hatOff: hit ? 0.25 : 0 },
    };
  }
  // --- flight
  const start = st.magRoot, end = [M.CRASH[0], -0.62, M.CRASH[2]];   // the pelvis comes down to sitting height
  const fp = flightPos(tau, start, end);
  const kicked = k(t, [[c.contact, 0], [c.launch, 0.35, 'out'], [c.launch + 0.06, 1, 'out']]);
  const land = k(t, [[c.imp + 0.1, 0], [c.imp + 0.5, 1, 'inOut']]);   // slammed into the pile (held), then slumps down
  // during the paused part of the flight (he is off screen) park him far away; the hat keeps its own world position
  const parked = t >= c.launch + c.flightA && t < c.resume;
  const hatP = hatPath(st, t, c, M, fp);
  if (land <= 0) {
    const flip = -(Math.PI * 2 + 0.55) * smooth(clamp(tau / c.F)) - 0.2 * Math.sin(tau * 3);
    const dir = sub(end, start); const dl = Math.hypot(dir[0], dir[2]);
    return {
      pos: parked ? [fp.pos[0], 60, fp.pos[2]] : fp.pos, yaw: M.yCRASH,
      face: t >= c.imp ? MX('ow') : MX('popped', { mOpen: 0.95 }),
      gaze: null,
      extra: { kicked, flip, flail: t >= c.imp ? 0.15 : 1.2, vel: [dir[0] / dl * 1.6, 0, dir[2] / dl * 1.6], hatOff: clamp((t - c.contact) / 0.12), hatPos: hatP.pos, hatRot: hatP.rot,
        dagger: false, pouch: true, eyePop: 1 },
    };
  }
  // --- landing -> wreck
  const w = wreckPose(t, M);
  w.extra.kicked = 1 - land;
  w.pos = [M.CRASH[0], -0.62 * (1 - land), M.CRASH[2]];
  w.body.bounce = 0.07 * jiggle(t, c.imp + 0.08, 1, 17, 6.5);
  w.body.slump += 0.3 * pulse(t, c.imp + 0.05, c.imp + 0.9, 0.08, 0.6);
  w.extra.hatPos = hatP.pos; w.extra.hatRot = hatP.rot;
  // between landing and the BONK: stunned, swaying ('ow' -> dazed)
  const preBonk = t < c.bonk;
  if (preBonk) w.face = MX([['ow', 0.6], ['dazed', 0.4]]);
  // after the sign: rigid, then sag; "...How rude." (lip-sync under the bucket rim), one finger lifts weakly and drops
  const rigid = pulse(t, c.sign1 - 0.02, c.sign1 + 0.5, 0.04, 0.3);
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
  const tz = c.contact + 0.85;                 // the hang ends; the hat zips after him
  if (t < tz) {
    const u = smooth(clamp((t - c.contact) / 0.35));
    return { pos: add(h0, [0, 0.32 * u + 0.015 * Math.sin((t - c.contact) * 9) * u, 0]), rot: [0.25 * u, 0.4 * u, -0.15 * u] };
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
  if (tau === null || (t >= c.resume - 1e-3 && t < c.resume && false)) { d.visible = false; return; }
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
  if (t < tl - 0.28) { d.visible = false; return; }
  // the drop: from above the frame straight down, point first, then the wobble
  const u = clamp((t - (tl - 0.28)) / 0.28);
  const y = 0.2 + 2.6 * (1 - u * u);
  const wob = t > tl ? 0.32 * Math.exp(-(t - tl) * 4.2) * Math.sin((t - tl) * 30) : 0;
  d.position.set(rest[0], y, rest[2]);
  d.rotation.set(0, 0.6, -Math.PI / 2 + wob + (1 - u) * 0.4);
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
    case 2: { // MAG_MED: 3/4 front on the magician from the camera side, high, the Void's hood soft in the left foreground
      const mh = A(mag.anchor('head'));
      const pos = add(mh, LD(-1.05, 0.55, 2.05));
      return aim(pos, mh, 420, 420, 38, { drift: 0.1 });
    }
    case 3: { // KICK wide, locked: the Void 3/4 (head cheat), Fear lower-left, the magician bent over the camera-side hem
      return aim(ROOM.W(1.85, 1.3, 7.0), ROOM.W(1.95, 2.0, 0.3), 372, 445, 50, { drift: 0 });
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
      const sh = ROOM.shot(ROOM.L(cc), { dist: 3.0, yaw: -8, pitch: 10, fov: 40, screenY: sy(560), drift: 0 });
      const sk = Math.exp(-Math.max(0, t - c.imp) * 9) * (t > c.imp ? 1 : 0);
      if (sk > 0.02) sh.shake = { amp: 0.012 * sk, freq: 11 };
      return sh;
    }
    case 7: { // FEAR_CU (the star at the top edge)
      return ROOM.shot(ROOM.L(fe), { dist: 1.9, yaw: 26, pitch: -2, fov: 44, screenY: sy(560), drift: 0.05 });
    }
  }
  return ROOM.cam('MASTER');
}

function dbg(st, t, app) {
  const cam = app.camera, o = {};
  const ps = { vEyes: st.vd.anchor('eyes'), fEyes: st.fear.anchor('eyes'), mHead: st.mag.anchor('head'), mChest: st.mag.anchor('chest'), kick: st.vd.anchor('kickFoot'), star: starAt(t).pos, handR: st.vd.anchor('handR') };
  for (const [n, p] of Object.entries(ps)) if (p) o[n] = pix(cam, p);
  console.log('DBG20', t.toFixed(2), 'shot', st.shot, JSON.stringify(o), 'kickErr', st.vd.anchor('kickFoot').distanceTo(V(st.foot0)).toFixed(3), 'foot', A(st.vd.anchor('kickFoot')).map((x) => x.toFixed(2)).join(','), 'tgt', st.chest0.map((x) => x.toFixed(2)).join(','), 'kv', (st.kv ?? 0).toFixed(3));
}
