// s01 · the_old_notebook · REAL_ROOM · first frame of the film (the thumbnail)
// Shots (data/staging.md §3 s01):
//   A  0 → s01b02+3.04 ('the first story')  OPENING still {420,655,1.12} → 1.142, title fades out over b02−1.1 → b02−0.12 (before the first caption)
//   B  → s01b03                              INSERT on the open notebook (SELF's POV over the shoulder), hand smooths
//                                            the dog-eared corner, the eyes (camera) travel from Fear up to the hood
//   C  s01b03 → S.end+0.9                    EYE PUSH from the face close-up into the lamp-side eye → amber glow
import { W, H, clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette, TAU } from '../engine.mjs';
import { drawSelf, SELF_EXPR, selfPoseAnchors, selfLocal } from '../chars/self.mjs';
import { drawNotebook } from '../sets/props.mjs';
import { drawRealRoom, drawRealRoomForeground, drawLitByRoom, REALROOM } from '../sets/realroom.mjs';
import { drawHand, makeHandStyle, HUMAN, blendHand } from '../hand.mjs';

export const id = 's01';

export const sfx = [
  // the hand smooths the dog-eared corner in the insert (swish peak at 0.5 in the file)
  { at: 's01b02+3.2', name: 'paper_rustle', gain: -14 },
  // the lamp's reflection blooms into the amber glow; swell (0–1.0) lands as the lids close on 'mind'
  { at: 's01b03+3.3', name: 'shimmer', gain: -14 },
];

// ------------------------------------------------------------------ constants
const [SX, SY, SS] = REALROOM.anchors.selfSeated;       // 420, 905, 1
const NBK = REALROOM.anchors.notebook;                  // 430, 984, 0.6
const NB_ROT = -0.05;
const ROOM = { lamp: 1, fairy: 1, moon: 1, dusk: 0 };
const CAM_OPEN = REALROOM.cameras.opening;              // {420,655,1.12}
const CAM_FACE = REALROOM.cameras.face;                 // {424,680,2.2}

// right-page drawing coordinates (props.mjs buildRightPage: the drawing is scaled 0.8 about (119,16))
const pageArt = (x, y) => [119 + (x - 119) * 0.8, 16 + (y - 16) * 0.8];
// crayon Fear's lower-left body: the fingertip rests there and the hand lies to the left of it, so Fear's head and
// huge eyes stay clear on the thumbnail (at (104,196) the hand covered its left eye and half the head)
const P_FEAR = pageArt(82, 201);
const P_HOOD = pageArt(174, 92);     // the black crayon hood, just under the opening
// right page (0..220, 0..290) → world, for a notebook lying open (open 1)
function nbWorld(px, py, x = NBK[0], y = NBK[1], s = NBK[2], flat = 1, rot = NB_ROT) {
  const sy = s * lerp(1, 0.5, flat);
  const lx = px * s, ly = (py - 145) * sy;
  const c = Math.cos(rot), sn = Math.sin(rot);
  return [x + lx * c - ly * sn, y + lx * sn + ly * c];
}

// world position of the index fingertip of a 'point' hand → wrist target (local, facing 1, seated)
const HAND_S = 1.42;
function wristForTip(tipW, ang, thumb = 1) {
  const tx = 34 * HAND_S, ty = 5.6 * HAND_S * thumb;
  const c = Math.cos(ang), s = Math.sin(ang);
  const wx = tipW[0] - (tx * c - ty * s), wy = tipW[1] - (tx * s + ty * c);
  return selfLocal(SX, SY, SS, 1, wx, wy);
}

// where SELF's eyes are (world), incl. the iris for the given gaze
function eyeWorld(pose, side) {
  const a = selfPoseAnchors(SX, SY, SS, pose);
  const hc = a.headCenter, ht = a.headTop;
  const rot = Math.atan2(ht[0] - hc[0], -(ht[1] - hc[1]));
  const f = pose.face || {};
  const turn = clamp(pose.headTurn ?? 0, -1, 1);
  const at = Math.abs(turn);
  const squeeze = side * turn > 0 ? 1 - at * 0.38 : 1 + at * 0.06;
  const rx = 16 * squeeze, ry = 12.6;
  const ex = side * 27 * (1 - at * 0.3) + turn * 27 * 0.55;
  const ix = ex + clamp(f.lookX || 0, -1, 1) * rx * 0.42;
  const iy = 2 + clamp(f.lookY || 0, -1, 1) * ry * 0.36 + ry * 0.04;
  const c = Math.cos(rot), s = Math.sin(rot);
  const W_ = (x, y) => [hc[0] + (x * c - y * s) * SS, hc[1] + (x * s + y * c) * SS];
  return { eye: W_(ex, 2), iris: W_(ix, iy), rot };
}

// the lit layer only needs to cover what each pass draws (seated: nothing of the torso below the desk line)
const BOX_BODY = [150, 470, 560, 470], BOX_FRONT = [150, 760, 560, 330];
// SELF lit like the room, plus a soft rim of window-blue on the far (screen-right) cheek, hair and shoulder
function drawSelfLit(g, st, pose, layer, rim = 1) {
  // the arms/hands pass (on the desk, in the lamp pool) reads the same unlit while the lamp is fully on: saves a layer
  if (layer === 'front' && (st.lamp ?? 1) >= 0.999) { drawSelf(g, SX, SY, SS, { ...pose, layer }); return; }
  drawLitByRoom(g, st, (c) => {
    drawSelf(c, SX, SY, SS, { ...pose, layer });
    if (layer !== 'body' || rim <= 0) return;
    const a = selfPoseAnchors(SX, SY, SS, pose);
    const [hx, hy] = a.headCenter;
    c.globalCompositeOperation = 'source-atop';
    let gr = c.createRadialGradient(hx + 104, hy - 30, 30, hx + 104, hy - 30, 96);
    gr.addColorStop(0, `rgba(150,185,255,${0.42 * rim})`); gr.addColorStop(0.55, `rgba(130,165,255,${0.16 * rim})`); gr.addColorStop(1, 'rgba(130,165,255,0)');
    c.fillStyle = gr; c.fillRect(hx - 20, hy - 140, 240, 260);
    const [sx, sy] = a.shoulderR;
    gr = c.createRadialGradient(sx + 70, sy - 40, 20, sx + 70, sy - 40, 110);
    gr.addColorStop(0, `rgba(150,185,255,${0.3 * rim})`); gr.addColorStop(1, 'rgba(130,165,255,0)');
    c.fillStyle = gr; c.fillRect(sx - 60, sy - 160, 260, 280);
  }, layer === 'body' ? BOX_BODY : BOX_FRONT);
}

// ------------------------------------------------------------------ SELF's acting (shot A + C share it)
function selfPose(t, S) {
  const k = (keys) => S.k(t, keys);
  // --- gaze: on the crayon Fear, following the fingertip to the hood, then (C) losing focus past the page
  const lookX = k([['scene.start', 0.22], ['s01b01+1.3', 0.22], ['s01b01+2.0', 0.42], ['s01b02+1.6', 0.4], ['s01b02+2.4', 0.3],
    ['s01b03', 0.18], ['s01b03+2.2', 0.05], ['s01b03+3.6', -0.06]]) + fbm(t * 0.4, 11) * 0.03;
  const lookY = k([['scene.start', 0.62], ['s01b01+1.3', 0.62], ['s01b01+2.0', 0.5], ['s01b03', 0.55], ['s01b03+2.4', 0.34], ['s01b03+4.0', 0.28]])
    + fbm(t * 0.37, 12) * 0.025;
  // --- lids: soft 60 % open, then heavy (C)
  const lidU = k([['scene.start', 0.36], ['s01b02+1.6', 0.36], ['s01b02+2.1', 0.28], ['s01b02+3.2', 0.34],
    ['s01b03', 0.38], ['s01b03+3.0', 0.62], ['s01b03+4.4', 0.74]]);
  // --- the one-corner tender smile: deepens on 'memory' (fond surprise), fades into stillness in C
  const smile = k([['scene.start', 0.34], ['s01b02+1.8', 0.34], ['s01b02+2.3', 0.72], ['s01b02+3.2', 0.5],
    ['s01b03', 0.34], ['s01b03+2.4', 0.16], ['s01b03+4.2', 0.06]]);
  const browUp = k([['scene.start', 0], ['s01b02+1.7', 0], ['s01b02+2.0', 0.42], ['s01b02+3.0', 0.1], ['s01b03', 0.0]]);
  const browIn = k([['scene.start', 0.3], ['s01b02+1.7', 0.3], ['s01b02+2.1', 0.42], ['s01b03', 0.32], ['s01b03+3.0', 0.2]]);
  const lidL = k([['scene.start', 0.3], ['s01b02+1.8', 0.3], ['s01b02+2.3', 0.6], ['s01b02+3.2', 0.4], ['s01b03', 0.3], ['s01b03+3', 0.12]]);
  // --- deliberate blinks only (an intimate held portrait)
  let blink = Math.max(
    blinkAt(t, S.T('s01b01+0.8'), 0.5),          // the slow full blink (12 frames)
    blinkAt(t, S.T('s01b02+0.55'), 0.22),         // after 'So,'
    blinkAt(t, S.T('s01b02+2.6'), 0.3),           // after the fond breath on 'memory'
    blinkAt(t, S.T('s01b03+1.5'), 0.4),           // heavier
  );
  // the last slow blink that never reopens: lids close as we pass into the glow ('mind' +4.72)
  const close = S.k(t, [['s01b03+4.1', 0], ['s01b03+5.0', 1, 'inOut']]);
  blink = Math.max(blink, close);
  const face = {
    ...SELF_EXPR.tenderSmile, lookX, lookY, lidU, lidL, smile, browUp, browIn, blink, noAutoBlink: true,
    blush: 0.22 + 0.12 * S.k(t, [['s01b02+1.8', 0], ['s01b02+2.4', 1], ['s01b03', 0]]), pupil: lerp(1, 1.12, S.k(t, [['s01b03+1.5', 0], ['s01b03+3.5', 1]])), // unfocused, soft
  };
  // head: tilted down toward the page; tiny nod-like settle + the soft breath-laugh on 'memory'
  const laugh = Math.sin(clamp((t - S.T('s01b02+2.0')) / 0.5) * Math.PI); // one soft nasal exhale
  // on 'memory' the head lifts a hair (fond surprise) and settles back
  const lift = S.k(t, [['s01b02+1.7', 0], ['s01b02+2.1', 1], ['s01b02+3.4', 0]]);
  const headTilt = 0.15 - lift * 0.05 + fbm(t * 0.21, 14) * 0.012 + S.k(t, [['s01b03', 0], ['s01b03+4', -0.03]]);
  const headDY = 3 - lift * 3.5 + laugh * 2.6;
  const headTurn = -0.12 + fbm(t * 0.18, 15) * 0.02;
  // breathing: one visible slow breath in A; slower and deeper in C ("visible in the collar")
  const breathe = S.k(t, [['scene.start', 1.25], ['s01b03', 1.25], ['s01b03+1', 1.5]]);
  const breathRate = S.k(t, [['scene.start', 0.19], ['s01b03', 0.19], ['s01b03+2', 0.14]]);
  return { t, seated: true, outfit: 'sweater', bodyTurn: -0.12, headTurn, headTilt, headDY, face, breathe, breathRate, shrug: 0.05 + laugh * 0.2 };
}

// arms reaching forward onto the desk are foreshortened toward the camera: scale the bones so the arm is only
// slightly bent for the given wrist target (otherwise a near target folds the elbow up and out)
function foreshorten(t, S, target, side, bentK = 1.1) {
  const sh = selfPoseAnchors(SX, SY, SS, selfPose(t, S))[side > 0 ? 'shoulderR' : 'shoulderL'];
  const d = Math.hypot(SX + target[0] * SS - sh[0], SY + target[1] * SS - sh[1]) / SS;
  const r = clamp((d * bentK) / 192, 0.35, 1);
  return { reach1: r, reach2: r };
}

// the resting flat hand opens/closes into the pointing hand as one smooth blend (it used to switch shape in one frame
// at reach 0.55 / away 0.45). k = 0 is exactly the old 'flat' spec (thumb 1 ⇒ roll π − 0.1), so frame 1 is unchanged;
// k = 1 is the old 'point' spec (roll π − 0.95)
const sstep = (a, b, x) => { const q = clamp((x - a) / (b - a)); return q * q * (3 - 2 * q); };
function flatToPoint(k) {
  if (k <= 0) return { hand: 'flat', thumb: 1 };
  if (k >= 1) return { hand: 'point', thumb: 1 };
  return { hand: blendHand('flat', 'point', k), roll: Math.PI - lerp(0.1, 0.95, k) };
}

// arms in shot A: SELF's own right hand (armL, screen-left) has a fingertip on the crayon Fear and slides up to the
// hood; reaching across from the left keeps both crayon figures visible. The other hand holds the right page flat.
// After the fond half-laugh on 'memory' the pointing hand lifts off the hood and settles flat on the far part of the
// left page (outside the insert's frame), so the cut to the insert matches: the page hand, which holds the dog-eared
// bottom corner all along, is the one that smooths it there.
const L_REST_PALM = nbWorld(-150, 232);     // left page, outer half (≈ 341, 1013)
const R_CORNER_WRIST = [566, 976];          // the page hand at the bottom-right (dog-eared) corner
function armsA(t, S) {
  const slide = S.k(t, [['s01b01+1.3', 0], ['s01b01+2.2', 1, 'inOut']]);
  const away = S.k(t, [['s01b02+2.25', 0], ['s01b02+3.0', 1, 'inOut']]);
  const fear = nbWorld(...P_FEAR), hood = nbWorld(...P_HOOD);
  // tiny arc lift as the fingertip travels across the paper
  const tip = [lerp(fear[0], hood[0], slide), lerp(fear[1], hood[1], slide) - Math.sin(slide * Math.PI) * 3];
  const ang = lerp(0.3, 0.78, slide) + fbm(t * 0.3, 21) * 0.02;   // on the hood the wrist straightens: the hand lies above crayon Fear, not over it
  let target = wristForTip(tip, ang, 1);
  let armL = { target, bend: -1, front: true, hand: 'point', handAngle: ang, thumb: 1, ...foreshorten(t, S, target, -1) };
  // the relaxed hand at rest, flat on the outer half of the LEFT page
  const restAng = 1.25;
  const restW = [L_REST_PALM[0] - Math.cos(restAng) * 17 * HAND_S, L_REST_PALM[1] - Math.sin(restAng) * 17 * HAND_S];
  // THUMBNAIL: on the first frame this hand rests on the left page, so the crayon Fear-and-hood doodle on the right
  // page is completely clear (the only picture of the two title characters in the preview still). During the
  // silent beat it reaches over and sets a fingertip on the little crayon Fear (eyes are already there), then
  // traces up to the hood as before.
  const reach = S.k(t, [['s01b01+0.3', 0], ['s01b01+1.15', 1, 'inOut']]);
  if (reach < 1) {
    const toW = [SX + target[0] * SS, SY + target[1] * SS];
    const w = [lerp(restW[0], toW[0], reach), lerp(restW[1], toW[1], reach) - Math.sin(reach * Math.PI) * 14];
    target = selfLocal(SX, SY, SS, 1, w[0], w[1]);
    armL = { target, bend: -1, front: true, ...flatToPoint(sstep(0.3, 0.8, reach)), handAngle: lerp(restAng, ang, reach),
      ...foreshorten(t, S, target, -1) };
  }
  if (away > 0) {
    // the fingertip lifts off the page and the relaxed hand settles back on the left page
    const fromW = [SX + target[0] * SS, SY + target[1] * SS];
    const w = [lerp(fromW[0], restW[0], away), lerp(fromW[1], restW[1], away) - Math.sin(away * Math.PI) * 14];
    target = selfLocal(SX, SY, SS, 1, w[0], w[1]);
    armL = { target, bend: -1, front: true, ...flatToPoint(1 - sstep(0.2, 0.7, away)), handAngle: lerp(ang, restAng, away),
      ...foreshorten(t, S, target, -1) };
  }
  // the page hand holds the dog-eared bottom corner down; just before the cut it shifts onto the fold to smooth it
  const slideR = S.k(t, [['s01b02+2.3', 0], ['s01b02+2.95', 1, 'inOut']]);
  const rw = [R_CORNER_WRIST[0] - 6 + slideR * 6, R_CORNER_WRIST[1] - 8 + slideR * 8];
  const rest = selfLocal(SX, SY, SS, 1, rw[0], rw[1]);
  const armR = { target: rest, bend: 1, front: true, hand: 'flat', handAngle: 1.84 - slideR * 0.06, thumb: -1,
    ...foreshorten(t, S, rest, 1, 1.1) };
  return { armL, armR };
}

// ------------------------------------------------------------------ shot A: the opening still
function shotA(g, t, S) {
  const p = clamp((t - S.start) / (S.T('s01b02+3.04') - S.start));
  // camera life: a whisper of drift, exactly zero on frame 1 (the thumbnail framing)
  const d = drift(t, 1.6, 5), d0 = drift(0, 1.6, 5);
  const z = lerp(CAM_OPEN.zoom, 1.142, ease.sine(p));
  const cam = { x: CAM_OPEN.x + (d.dx - d0.dx) / z, y: CAM_OPEN.y + (d.dy - d0.dy) / z, zoom: z };
  g.save();
  applyCamera(g, cam);
  const st = { t, ...ROOM };
  drawRealRoom(g, st);
  const pose = { ...selfPose(t, S), ...armsA(t, S) };
  drawSelfLit(g, st, pose, 'body');
  drawRealRoomForeground(g, st);
  drawNotebook(g, NBK[0], NBK[1], NBK[2], { open: 1, flat: 1, rot: NB_ROT });
  drawSelfLit(g, st, pose, 'front');
  g.restore();
  // TITLE: opaque on frame 1 (the thumbnail), fades out over the last second of the silent beat so it is gone just
  // before the first burned-in caption fades in (play 3.52 = story 3.52, the time-warp is the identity before
  // s01b02): the two text layers never share the screen. It is drawn with the frame-1 camera, held: under the
  // drifting camera the glyphs snapped a whole pixel at a time (7 one-frame ticks of the title in 2.5 s), and the
  // push-in is only 0.6 % by the fade. Frame 1 is pixel-identical (that is the frame-1 camera).
  const ta = 1 - S.k(t, [['s01b02-1.1', 0], ['s01b02-0.12', 1, 'sine']]);
  if (ta > 0.003) {
    g.save();
    applyCamera(g, { x: CAM_OPEN.x, y: CAM_OPEN.y, zoom: CAM_OPEN.zoom });
    drawTitle(g, ta);
    g.restore();
  }
  vignette(g, 0.25);
}

function drawTitle(g, a) {
  g.save();
  g.globalAlpha = a;
  g.font = '60px "Caveat"';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.shadowColor = 'rgba(10,12,40,0.85)';
  g.shadowBlur = 14;
  g.fillStyle = '#fff3d6';
  g.fillText('The Void', 432, 203);
  g.fillText('and My Fear', 432, 282);
  g.restore();
}

// ------------------------------------------------------------------ shot B: the insert
const INS = [184, 690, 1.6, 0.15, -0.03];   // screen-space notebook: x, y, scale, flat, rot
function insWorld(px, py) { return nbWorld(px, py, INS[0], INS[1], INS[2], INS[3], INS[4]); }
function shotB(g, t, S) {
  const t0 = S.T('s01b02+3.04'), t1 = S.T('s01b03');
  const p = clamp((t - t0) / (t1 - t0));
  // the camera is SELF's eyes: the little lavender one first, then up the tall dark one, then down to the caption
  // (a tiny nod at the remembered sentence); slow push 1.12 → 1.2
  const P_CAP = [112, 246];
  // (follow factor 0.22, sine moves of 1.3–1.5 s: the drop to the caption was a 140 px/s pan over text)
  const focus = S.k(t, [['s01b02+3.04', { x: P_FEAR[0], y: P_FEAR[1] }], ['s01b02+3.5', { x: P_FEAR[0], y: P_FEAR[1] }],
    ['s01b02+5.0', { x: P_HOOD[0], y: P_HOOD[1] - 10 }, 'sine'], ['s01b02+5.3', { x: P_HOOD[0], y: P_HOOD[1] - 10 }],
    ['s01b02+6.6', { x: P_CAP[0], y: P_CAP[1] }, 'sine']]);
  const z = lerp(1.12, 1.2, ease.sine(p));
  const fS = insWorld(focus.x, focus.y);
  const dd = drift(t, 2, 6);
  const fx = (fS[0] - 360) * 0.22 + dd.dx, fy = (fS[1] - 640) * 0.22 + dd.dy;
  // tiny nod at the remembered sentence: a soft dip of the view
  const nod = Math.sin(clamp((t - S.T('s01b02+6.55')) / 0.6) * Math.PI) * 7;
  // background: the warm desk top in the lamp pool (dim, out of focus)
  g.save();
  g.fillStyle = '#5a3624'; g.fillRect(0, 0, W, H);
  const gd = g.createLinearGradient(0, 0, 0, H);
  gd.addColorStop(0, '#3a2318'); gd.addColorStop(0.5, '#7a4b30'); gd.addColorStop(1, '#4a2c1c');
  g.fillStyle = gd; g.fillRect(0, 0, W, H);
  const gl = g.createRadialGradient(-40, 560, 40, -40, 560, 900);
  gl.addColorStop(0, 'rgba(255,200,130,0.55)'); gl.addColorStop(0.5, 'rgba(240,150,90,0.18)'); gl.addColorStop(1, 'rgba(240,150,90,0)');
  g.fillStyle = gl; g.fillRect(0, 0, W, H);
  // soft wood grain streaks
  g.strokeStyle = 'rgba(40,20,10,0.12)'; g.lineWidth = 6;
  for (let i = 0; i < 7; i++) { g.beginPath(); g.moveTo(-20, 140 + i * 170); g.bezierCurveTo(240, 120 + i * 172, 480, 170 + i * 166, 760, 150 + i * 168); g.stroke(); }
  g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-W / 2 - fx, -H / 2 - fy + nod);
  drawNotebook(g, INS[0], INS[1], INS[2], { open: 1, flat: INS[3], rot: INS[4] });
  // the dog-eared bottom-right corner flattens as the thumb passes
  const smooth = S.k(t, [['s01b02+3.25', 0], ['s01b02+4.15', 1, 'inOut']]);
  drawDogEar(g, 1 - smooth);
  // warm lamp glow on the paper (from the left)
  g.save();
  g.globalCompositeOperation = 'soft-light';
  const gp = g.createRadialGradient(40, 520, 30, 40, 520, 620);
  gp.addColorStop(0, 'rgba(255,190,110,0.55)'); gp.addColorStop(1, 'rgba(255,190,110,0)');
  // (fill well past the gradient's radius: a smaller rect left a hard horizontal edge across the background)
  g.fillStyle = gp; g.fillRect(-700, -200, 1600, 1500);
  g.restore();
  drawInsertHand(g, t, S, smooth);
  g.restore();
  // rgba(20,10,4,0.35) at the edges: the frame stays on the page
  const ge = g.createRadialGradient(W / 2, H / 2, 300, W / 2, H / 2, 820);
  ge.addColorStop(0, 'rgba(20,10,4,0)'); ge.addColorStop(1, 'rgba(20,10,4,0.45)');
  g.fillStyle = ge; g.fillRect(0, 0, W, H);
  vignette(g, 0.3);
}

// the right page's outer bottom corner, curled up a little (dog-ear), flattening with k → 0
function drawDogEar(g, k) {
  if (k < 0.01) return;
  const c = insWorld(220, 290);           // the corner
  const a = insWorld(220, 290 - 46 * k), b = insWorld(220 - 46 * k, 290);
  g.save();
  // the paper under the fold is the desk (the corner is lifted): cover the corner triangle with the shadowed page edge
  g.fillStyle = 'rgba(70,40,20,0.9)';
  g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(c[0] + 4, c[1] + 4); g.lineTo(b[0], b[1]); g.closePath(); g.fill();
  // folded flap (back of the paper), lying toward the page centre
  const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const f = [m[0] - (c[0] - m[0]) * 0.92, m[1] - (c[1] - m[1]) * 0.92];
  g.fillStyle = '#efe4c8';
  g.strokeStyle = 'rgba(120,95,60,0.7)'; g.lineWidth = 1.6;
  g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(f[0], f[1]); g.lineTo(b[0], b[1]); g.closePath(); g.fill(); g.stroke();
  const gs = g.createLinearGradient(m[0], m[1], f[0], f[1]);
  gs.addColorStop(0, 'rgba(90,60,30,0.25)'); gs.addColorStop(1, 'rgba(90,60,30,0)');
  g.fillStyle = gs; g.fill();
  g.restore();
}

// SELF's page hand (screen-right in the wide, where it holds this bottom corner) is already on the dog-ear at the
// cut, seen from the back from the bottom-right of this POV; the thumb presses the fold and smooths it flat, then the
// hand withdraws. Only the hand and the sweater cuff are in frame. The hand is the shared articulated hand
// (hand.mjs HUMAN: palm, separate fingers, thumb, ONE outer outline, soft interior separations): the right hand
// seen from the back, fingers lying relaxed on the page, the thumb out to the side pressing the fold. (It used to
// be a local stubby five-stroke paw whose back-of-hand outline cut across the finger roots, with dotted knuckles.)
const POV_HAND = makeHandStyle(HUMAN, 125, { skin: '#d9a27e', light: '#f0c6a6', shade: '#bb7b5c', line: '#6e3b2e' }, 2.6);
const POV_POSE = { f: [[0.12, 0.18, 0.1], [0.1, 0.16, 0.1], [0.12, 0.18, 0.1], [0.16, 0.22, 0.12]], spread: 0.06, thumb: [0.75, 0.1, 0.12] };
const POV_THUMB = [43.3 * 1.25, -36.8 * 1.25];   // the thumb pad in hand-local px (ang 0, right hand, back to camera)
function drawInsertHand(g, t, S, smooth) {
  const enter = S.k(t, [['s01b02+3.04', 1], ['s01b02+5.5', 1], ['s01b02+6.5', 0, 'inOut']]);
  if (enter <= 0.001) return;
  const corner = insWorld(220, 290), fold = insWorld(186, 256);
  // thumb tip: on the fold, then sliding out over the corner as it flattens
  const e = ease.inOut(smooth);
  const tip = [lerp(fold[0], corner[0] - 14, e), lerp(fold[1], corner[1] - 10, e)];
  const ang = -2.2 + 0.08 * Math.sin(e * Math.PI) + fbm(t * 0.5, 41) * 0.015;
  const off = (1 - enter) * 330;
  // thumb pad in hand-local coords → wrist position
  const c = Math.cos(ang), sn = Math.sin(ang);
  const wx = tip[0] - (POV_THUMB[0] * c - POV_THUMB[1] * sn) - c * off, wy = tip[1] - (POV_THUMB[0] * sn + POV_THUMB[1] * c) - sn * off;
  // the thumb presses (a touch more bend while it pushes the fold flat), the fingers relax as the hand withdraws
  const press = Math.sin(e * Math.PI);
  const pose = { ...POV_POSE, thumb: [0.75, 0.1, 0.12 + 0.1 * press], f: POV_POSE.f.map(([a, b, d]) => [a + 0.12 * (1 - enter), b + 0.1 * (1 - enter), d]) };
  drawPOVHand(g, wx, wy, ang, pose);
}

function drawPOVHand(g, x, y, ang, pose) {
  const SW = '#4f8c8a', SWL = '#78b2ad', SWS = '#386a69', SWN = '#1c393b';
  g.save();
  g.translate(x, y); g.rotate(ang);
  g.lineJoin = 'round'; g.lineCap = 'round';
  // soft contact shadow on the paper/desk
  const gsh = g.createRadialGradient(56, 14, 12, 56, 14, 100);
  gsh.addColorStop(0, 'rgba(40,20,10,0.26)'); gsh.addColorStop(1, 'rgba(40,20,10,0)');
  g.fillStyle = gsh; g.beginPath(); g.ellipse(56, 14, 100, 62, 0, 0, TAU); g.fill();
  drawHand(g, POV_HAND, { ang: 0, shape: pose, roll: 0, chir: -1 });
  // sleeve (off-frame toward the body) + ribbed cuff over the wrist ("sweater paw")
  g.scale(1.25, 1.25);
  const sl = g.createLinearGradient(0, -40, 0, 40);
  sl.addColorStop(0, SWL); sl.addColorStop(0.45, SW); sl.addColorStop(1, SWS);
  g.fillStyle = sl; g.strokeStyle = SWN; g.lineWidth = 3.2;
  g.beginPath(); g.moveTo(-600, -44); g.lineTo(-26, -36); g.lineTo(-26, 36); g.lineTo(-600, 46); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = SWS;
  g.beginPath(); g.roundRect(-30, -33, 36, 66, 10); g.fill(); g.stroke();
  g.strokeStyle = 'rgba(28,57,59,0.55)'; g.lineWidth = 1.8;
  for (let i = -24; i <= 24; i += 8) { g.beginPath(); g.moveTo(-26, i); g.lineTo(2, i * 1.02); g.stroke(); }
  g.restore();
}

// ------------------------------------------------------------------ shot C: the eye push into the glow
function shotC(g, t, S) {
  const pose = { ...selfPose(t, S), armL: { preset: 'handsOnDesk', target: [-50, 34], reach2: 0.55 },
    armR: { preset: 'handsOnDesk', target: [62, 46], reach2: 0.6 } };
  const e = eyeWorld(pose, -1);   // lamp-side (screen-left) eye
  const t0 = S.T('s01b03'), t1 = S.end + 0.9;
  const p = clamp((t - t0) / (t1 - t0));
  const lz = lerp(Math.log(CAM_FACE.zoom), Math.log(14), ease.sine(p));
  const z = Math.exp(lz);
  const glint = [e.iris[0] - 2.2, e.iris[1] + 2.0];
  const w = (CAM_FACE.zoom / z) * (1 - ease.sine(clamp(p * 1.25)));
  const dc = drift(t, 2, 8);
  const cam = { x: glint[0] + (CAM_FACE.x - glint[0]) * w + dc.dx / z, y: glint[1] + (CAM_FACE.y - glint[1]) * w + dc.dy / z, zoom: z };
  g.save();
  applyCamera(g, cam);
  const st = { t, ...ROOM, motes: z < 4 };
  drawRealRoom(g, st);
  drawSelfLit(g, st, pose, 'body');
  if (cam.y + 660 / z > SY - 20) {        // the desk is still in frame
    drawRealRoomForeground(g, st);
    drawNotebook(g, NBK[0], NBK[1], NBK[2], { open: 1, flat: 1, rot: NB_ROT });
  }
  // the arms run from the shoulders down to the desk: they stay in frame after the desk has left it (skipping them
  // with the desk popped both sleeves off the shoulders in one frame, play 12.08)
  drawSelfLit(g, st, pose, 'front');
  // the lamp as a warm point of light in each iris (fades as the lids close)
  const lidOpen = 1 - clamp(pose.face.blink);
  for (const side of [-1, 1]) {
    const q = eyeWorld(pose, side).iris;
    const gx = q[0] - 2.2, gy = q[1] + 2.0;
    const a = 0.9 * clamp(1 - (1 - lidOpen) * 2.5);
    if (a > 0.01) {
      const gr = g.createRadialGradient(gx, gy, 0, gx, gy, 3.2);
      gr.addColorStop(0, `rgba(255,240,200,${a})`); gr.addColorStop(0.45, `rgba(255,196,110,${a * 0.75})`); gr.addColorStop(1, 'rgba(255,170,80,0)');
      g.fillStyle = gr; g.fillRect(gx - 4, gy - 4, 8, 8);
    }
  }
  g.restore();
  vignette(g, 0.35);
  // the amber glow: grows from the lamp's reflection to fill the frame (fully amber by S.end−0.3)
  const k = S.k(t, [['s01b03+3.6', 0], ['scene.end-0.3', 1, 'inOut']]);
  if (k > 0.001) {
    const sx = (glint[0] - cam.x) * z + W / 2, sy = (glint[1] - cam.y) * z + H / 2;
    const R = lerp(30, 1500, Math.pow(k, 1.6));
    g.save();
    g.globalCompositeOperation = 'screen';
    let gr = g.createRadialGradient(sx, sy, 0, sx, sy, R);
    gr.addColorStop(0, `rgba(255,226,168,${clamp(k * 2.2)})`); gr.addColorStop(0.45, `rgba(255,179,92,${clamp(k * 1.6) * 0.8})`);
    gr.addColorStop(1, 'rgba(194,106,40,0)');
    g.fillStyle = gr; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = 'source-over';
    const a2 = clamp((k - 0.35) / 0.65);
    if (a2 > 0) {
      gr = g.createRadialGradient(W / 2, H * 0.5, 0, W / 2, H * 0.5, 900);
      gr.addColorStop(0, `rgba(255,226,168,${a2})`); gr.addColorStop(0.5, `rgba(255,179,92,${a2})`); gr.addColorStop(1, `rgba(194,106,40,${a2})`);
      g.fillStyle = gr; g.fillRect(0, 0, W, H);
    }
    g.restore();
  }
}

// ------------------------------------------------------------------ render
export function render(g, t, S) {
  if (t < S.T('s01b02+3.04')) shotA(g, t, S);
  else if (t < S.T('s01b03')) shotB(g, t, S);
  else shotC(g, t, S);
}
