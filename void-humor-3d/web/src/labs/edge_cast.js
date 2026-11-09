// Lab: SET 'EDGE' lighting check with the real JESUS + VOID rigs (faces must read). 2 s per shot.
//   node tools/render.js sheet --lab edge_cast --from 1 --to 27 --n 14 --cols 7 --out out/sheets/edge_cast.jpg
import { applyShot, framed as framedCore } from '../core/camera.js';
import { clamp, lerp } from '../core/util.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';

// core framed() lands the subject at 1 - screenY (see scenes/marks.js); compensate so screenY means "from the top"
const framed = (look, o) => framedCore(look, { ...o, screenY: 1 - (o.screenY ?? 0.38) });
const SEG = 2;
const JP = [-0.45, 0, 0.35], VP = [1.25, 0, -0.45];
// [label, shot(S), opts, mode]  mode: undefined = standing pair at JP/VP, 'walk' = walk-off, 'finale' = shots.finale recipe
const SHOTS = [
  ['two-shot tod0', () => framed([0.35, 1.75, 0], { dist: 5.2, yaw: 3, pitch: 2, fov: 32, screenY: 0.4 }), { tod: 0 }],
  ['jesus MCU tod0 (sunShift .12, sunGlow .6) rose-gold tree behind', () => framed([JP[0], 1.55, JP[2]], { dist: 1.5, yaw: 10, pitch: 1, fov: 30, screenY: 0.34 }), { tod: 0, sunShift: 0.12, sunGlow: 0.6, heroTreeGlow: 0.4 }],
  ['void low MCU voidSky .7', () => ({ pos: [0.6, 0.9, 3.4], look: [1.1, 2.15, -0.4], fov: 34 }), { tod: 0, voidSky: 0.7 }],
  ['jesus MCU tod1', () => framed([JP[0], 1.55, JP[2]], { dist: 1.5, yaw: -12, pitch: 1, fov: 30, screenY: 0.34 }), { tod: 1 }],
  ['reverse OTS tod.5', () => ({ pos: [1.6, 2.1, -3.6], look: [-0.5, 1.4, 0.9], fov: 32 }), { tod: 0.5 }],
  ['wide tod.3', () => ({ pos: [0.5, 1.6, 9.5], look: [0.0, 1.5, -10], fov: 38 }), { tod: 0.3 }],
  ['high on jesus kneel', () => ({ pos: [0.2, 3.2, 2.8], look: [-0.5, 0.6, 0.3], fov: 34 }), { tod: 0.2 }],
  ['walk-off tod1 (shots.walkoff.opts)', (S) => S.shots.walkoff, { tod: 1 }, 'walk'],
  ['FINALE recipe tod .85', (S) => S.shots.finale, { tod: 0.85 }, 'finale'],
  ['FINALE recipe tod 1', (S) => S.shots.finale, { tod: 1 }, 'finale'],
  ['finale WITHOUT recipe tod .9 (compare)', (S) => S.shots.finale, { tod: 0.9 }, 'finaleRaw'],
  ['medium two-shot voidSky .6', () => framed([0.4, 1.75, 0], { dist: 5.6, yaw: 2, pitch: 1, fov: 33, screenY: 0.38 }), { tod: 0.2, voidSky: 0.6 }],
  ['medium two-shot voidSky 1', () => framed([0.4, 1.75, 0], { dist: 5.6, yaw: 2, pitch: 1, fov: 33, screenY: 0.38 }), { tod: 0.2, voidSky: 1 }],
  ['OTS jesus->void, tree calm', () => ({ pos: [-1.3, 1.6, 1.9], look: [1.1, 2.0, -0.45], fov: 32 }), { tod: 0.3, voidSky: 0.5, heroTreeGlow: 0.35 }],
];
export const segments = SHOTS.map((s, i) => [i * SEG, (i + 1) * SEG, s[0]]);
export const DURATION = SHOTS.length * SEG;
export async function setup(app) {
  const set = await app.set('EDGE');
  const jesus = await app.char('JESUS');
  const vd = await app.char('VOID');
  set.scene.add(jesus.root, vd.root);
  return { scene: set.scene, set, jesus, vd, look: set.look };
}
export async function update(t, app, s) {
  const i = clamp(Math.floor(t / SEG), 0, SHOTS.length - 1), u = clamp((t - i * SEG) / SEG);
  const [, shot, o, mode] = SHOTS[i];
  const S = s.set, F = S.shots.finale;
  const sh = shot(S);
  applyShot(app.camera, sh, t);
  let post = {};
  if (mode) {
    // walk the pair along the path (finale: across the crest, in front of the sun disc)
    const s0 = mode === 'walk' ? 10 + u * 1.8 : lerp(F.walk[0] + 3, F.walk[0] + 7, u);
    const a = S.pathAt(s0), b = S.pathAt(s0 + 0.3);
    const side = [a.dir[2], 0, -a.dir[0]];
    const opts = mode === 'finale' ? { ...F.opts, tod: o.tod }
      : mode === 'finaleRaw' ? { ...o, sunShift: F.opts.sunShift, shadowAt: a.pos }      // aligned, but no recipe
      : { ...o, ...(sh.opts || {}), shadowAt: a.pos };
    if (mode === 'finale') post = F.post;
    S.update(t, opts);
    s.jesus.update(t, { pos: [a.pos[0] - side[0] * 0.5, a.pos[1], a.pos[2] - side[2] * 0.5], yaw: a.yaw, walk: { amount: 1, phase: t * 0.85 } });
    s.vd.update(t, { pos: [b.pos[0] + side[0] * 0.9, b.pos[1], b.pos[2] + side[2] * 0.9], yaw: b.yaw, walk: { amount: 1, phase: t * 1.0 } });
  } else {
    S.update(t, { ...o, voidPos: VP });
    const kneel = i === 6 ? 1 : 0;
    s.jesus.update(t, { pos: JP, yaw: 0.25, face: JX(i === 3 ? 'tender' : 'warm'), gaze: 'camera', body: { kneel } });
    s.vd.update(t, { pos: VP, yaw: -0.35, face: VX(i === 2 ? 'gentle' : 'calm'), gaze: i === 2 ? 'camera' : s.jesus });
  }
  s.look = { ...S.look, ...post };
}
