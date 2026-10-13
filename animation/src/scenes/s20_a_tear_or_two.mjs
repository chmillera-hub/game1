// s20 · a_tear_or_two · REAL_ROOM · the last scene (dissolve in from s19's screen bloom)
// Shots (data/staging.md §3 s20):
//   S.start → s20b02         desk {424,760,1.5}: SELF picks up a gold pencil and draws one tiny star in the black hood
//   s20b02 → s20b03.end      push {424,760,1.5} → {424,690,2.1}: tear wells, spills, soft laugh, sleeve wipe, smile down
//   s20b03.end+0.3 → S.end   pull back to the opening composition {420,655,1.12} by s20b04+2.6 (arcing through the desk
//                            framing so the closing book stays clear of the bottom 15 %): the cover is lifted to vertical
//                            (+0.8 → +1.45) and laid down (→ +2.0), palm on the cover, lamp click (+2.4), the room goes
//                            blue, eyes up to the window with stars in them, star-hood + wink
// Last frame = the mirror of the film's first frame (same camera and desk, lamp off, notebook closed under the palm).
import { W, H, clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette, TAU, ik } from '../engine.mjs';
import { star, drawTear } from '../face.mjs';
import { blendHand } from '../hand.mjs';
import { drawSelf, SELF_EXPR, SELF_FACE, selfPoseAnchors, selfLocal } from '../chars/self.mjs';
import { drawNotebook } from '../sets/props.mjs';
import { drawRealRoom, drawRealRoomForeground, drawLitByRoom, REALROOM } from '../sets/realroom.mjs';

export const id = 's20';

export const sfx = [
  // the sweater sleeve wipes the cheek (swishes at 0.0 / 0.28: the arm rising / the stroke over the drop)
  { at: 's20b03+2.65', name: 'cloth_rustle', gain: -18 },
  // the notebook closes: the cover is lifted (+0.8), stands up (+1.45) and is laid down (+2.0); swish peak at 0.5
  { at: 's20b04+0.85', name: 'paper_rustle', gain: -16 },
  // reaching over to the lamp (+1.5 → +2.25)
  { at: 's20b04+1.5', name: 'cloth_rustle', gain: -20 },
  // the lamp click (press at 0.02 in the file)
  { at: 's20b04+2.38', name: 'lamp_click', gain: -12 },
  // one star twinkles in the hood of stars (first note at 0.02)
  { at: 's20b04+3.96', name: 'twinkle', gain: -14 },
];

// ------------------------------------------------------------------ constants
const [SX, SY, SS] = REALROOM.anchors.selfSeated;        // 420, 905, 1
const NBK = REALROOM.anchors.notebook;                   // 430, 984, 0.6
const NB_ROT = -0.05;
const CAM_DESK = REALROOM.cameras.desk;                  // {424,760,1.5}
const CAM_OPEN = REALROOM.cameras.opening;               // {420,655,1.12}
// the tear close-up: the face fills ~41 % of the width (centre ≈ screen y 655), so the welling, the drop and its wet
// trail survive the encoder (at the old 2.1 the streak vanished in the compressed film)
const CAM_CLOSE = { x: 428, y: 704, zoom: 2.4 };
const LEAF_RISE = 220 * 0.866;                           // a standing cover's height on screen (page units)
const HAND_S = 1.42;
const PENCIL_LEN = 52;
const PENCIL_REST = { tip: [574, 1021], ang: -0.12 };   // lying on the desk in front of the mug (ang: tip → eraser)

const pageArt = (x, y) => [119 + (x - 119) * 0.8, 16 + (y - 16) * 0.8];
const P_STAR = pageArt(174, 86);                         // inside the black crayon hood's face
// right page (0..220, 0..290) → world for the notebook lying open
function nbWorld(px, py, s = NBK[2], rot = NB_ROT) {
  const lx = px * s, ly = (py - 145) * s * 0.5;
  const c = Math.cos(rot), sn = Math.sin(rot);
  return [NBK[0] + lx * c - ly * sn, NBK[1] + lx * sn + ly * c];
}

function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, W, H); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, W, H); }
  g.restore();
}

// ------------------------------------------------------------------ timing tracks
function tracks(t, S) {
  const k = (keys) => S.k(t, keys);
  const lampOff = k([['s20b04+2.4', 0], ['s20b04+2.65', 1, 'inOut']]);
  return {
    lamp: 1 - lampOff,
    fairy: k([['s20b04+2.4', 1], ['s20b04+3.4', 0.3]]),
    starHood: k([['s20b04+2.8', 0], ['s20b04+4.3', 0.8], ['s20b04+5.5', 0.8], ['s20b04+6.8', 0]]),
    starWink: Math.sin(clamp((t - S.T('s20b04+4.0')) / 0.8) * Math.PI),
    // the notebook: open 1 → 0.5 (armL lifts the cover up to vertical) → 0 (armR takes it and lays it down)
    open: k([['s20b04+0.8', 1], ['s20b04+1.45', 0.5, 'inOut'], ['s20b04+2.0', 0, 'inOut']]),
    star: k([['s20b01+0.8', 0], ['s20b01+2.4', 1, 'linear']]),
    lampOff,
    // THE tear — one, from the lamp-lit near eye (screen-left), drawn with face.mjs drawTear (one translucent,
    // slightly blue drop with its own short wet trail): the eyes well on 'After that,' (b02), the drop gathers on the
    // lower lid on 'shed' and spills around the line's middle, on 'tear' (+1.25 story ≈ 47 % of the played line); it slides slowly
    // down the cheek with one small hesitation and is still there when the sleeve comes up (+2.85), under which it
    // fades out as a whole (drop and trail together). drawTear progress: 0..0.16 gathering, then the run.
    tear: k([['s20b03+0.75', 0], ['s20b03+1.25', 0.16, 'sine'], ['s20b03+1.55', 0.29, 'in'], ['s20b03+1.8', 0.33, 'out'],
      ['s20b03+2.75', 0.6, 'inOut'], ['s20b03+3.1', 0.64]]),
    wiped: k([['s20b03+2.88', 0], ['s20b03+3.05', 1, 'inOut']]),
  };
}

// ------------------------------------------------------------------ the gold pencil (local prop)
function drawPencil(g, tip, ang, alpha = 1) {
  // tip = world point of the lead; ang = direction tip → eraser end
  g.save();
  g.globalAlpha *= alpha;
  g.translate(tip[0], tip[1]); g.rotate(ang);
  const L = PENCIL_LEN, w = 2.9;
  g.lineJoin = 'round';
  // soft shadow on the desk/page
  g.fillStyle = 'rgba(40,20,10,0.22)';
  g.beginPath(); g.roundRect(2, -w + 3, L, w * 2, w); g.fill();
  // sharpened wood cone + gold lead
  g.fillStyle = '#e8c79a'; g.strokeStyle = '#6a4a2a'; g.lineWidth = 0.9;
  g.beginPath(); g.moveTo(0.5, 0); g.lineTo(9, -w); g.lineTo(9, w); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#c99a2a';
  g.beginPath(); g.moveTo(0, 0); g.lineTo(3.4, -1.1); g.lineTo(3.4, 1.1); g.closePath(); g.fill();
  // gold-painted body with a highlight stripe
  const gb = g.createLinearGradient(0, -w, 0, w);
  gb.addColorStop(0, '#fbe7a4'); gb.addColorStop(0.45, '#e8c25a'); gb.addColorStop(1, '#a9832c');
  g.fillStyle = gb;
  g.beginPath(); g.rect(9, -w, L - 17, w * 2); g.fill(); g.stroke();
  // ferrule + eraser
  g.fillStyle = '#c9ccd2'; g.beginPath(); g.rect(L - 8, -w, 4, w * 2); g.fill(); g.stroke();
  g.fillStyle = '#e88a8a'; g.beginPath(); g.roundRect(L - 4.5, -w, 5, w * 2, [0, 2, 2, 0]); g.fill(); g.stroke();
  g.restore();
}

// the tiny gold star in the black crayon hood, drawn on the page plane (squashed with the notebook)
function drawPageStar(g, k, glow) {
  if (k <= 0.001) return;
  g.save();
  g.translate(NBK[0], NBK[1]); g.rotate(NB_ROT); g.scale(NBK[2], NBK[2] * 0.5);
  const x = P_STAR[0], y = P_STAR[1] - 145;
  const r = 7.5 * Math.min(1, k * 1.25);
  if (glow > 0) {
    const gg = g.createRadialGradient(x, y, 0, x, y, 22);
    gg.addColorStop(0, `rgba(255,214,120,${0.45 * glow})`); gg.addColorStop(1, 'rgba(255,214,120,0)');
    g.fillStyle = gg; g.fillRect(x - 22, y - 22, 44, 44);
  }
  g.fillStyle = '#f2c53d';
  star(g, x, y, r);
  g.strokeStyle = 'rgba(168,120,15,0.9)'; g.lineWidth = 1.1; g.stroke();
  g.fillStyle = 'rgba(255,248,220,0.9)';
  star(g, x - r * 0.12, y - r * 0.12, r * 0.38);
  g.restore();
}
// the pencil tip while drawing: a 4-point star traced point by point, growing (page units → world)
function starTip(k) {
  const pts = [];
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * TAU - Math.PI / 2;
    const rr = i % 2 === 0 ? 7.5 : 2.6;
    pts.push([P_STAR[0] + Math.cos(a) * rr, P_STAR[1] + Math.sin(a) * rr]);
  }
  pts.push(pts[0]);
  const f = clamp(k) * 8, i = Math.min(7, Math.floor(f)), u = f - i;
  const p = [lerp(pts[i][0], pts[i + 1][0], u), lerp(pts[i][1], pts[i + 1][1], u)];
  return nbWorld(...p);
}

// ------------------------------------------------------------------ arms
function foreshorten(pose, target, side, bentK = 1.1, max = 1.12) {
  const sh = selfPoseAnchors(SX, SY, SS, pose)[side > 0 ? 'shoulderR' : 'shoulderL'];
  const d = Math.hypot(SX + target[0] * SS - sh[0], SY + target[1] * SS - sh[1]) / SS;
  const r = clamp((d * bentK) / 192, 0.35, max);
  return { reach1: r, reach2: r };
}
// world point where the fist's centre should be → wrist (local), for a hand angle
function wristForGrip(gW, ang, k = 1) {
  // k blends the fist-centre offset (1) toward the palm offset (0) so hand changes never jump
  const gx = lerp(17, 20, k) * HAND_S, gy = 1.5 * HAND_S * k;
  const c = Math.cos(ang), s = Math.sin(ang);
  return selfLocal(SX, SY, SS, 1, gW[0] - (gx * c - gy * s), gW[1] - (gx * s + gy * c));
}
function wristForPalm(pW, ang) {
  const px = 17 * HAND_S;
  return selfLocal(SX, SY, SS, 1, pW[0] - Math.cos(ang) * px, pW[1] - Math.sin(ang) * px);
}
const toW = (l) => [SX + l[0] * SS, SY + l[1] * SS];

// Palm directions (hand.mjs palmDir: x right, y down, z toward camera). Every hand gets one explicitly: the old specs
// only named the thumb's side (thumb: ±1), which turned the PALM to the camera on the hands resting flat on the page,
// desk and cover; and they switched hand shapes in one frame (flat → grip, grip → flat, flat → point), which popped
// the fingers and rolled the wrist. Shapes and palm directions now blend.
const P_DOWN = [0, 0.8, -0.6];                  // flat on the page / desk / cover: the back of the hand to camera
const P_PENCIL = [-0.5, 0.55, -0.65];          // writing: palm down and in, knuckles to camera
const P_WIPE = [0.45, 0, -0.9];                 // the knuckle at the cheek: palm toward the face (self.mjs wipeTear)
const P_COVER = [0.1, 0.75, -0.65];             // lifting the cover: palm down on its page side, the thumb under its edge
const mixP = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
const sm = (k) => ease.inOut(clamp(k));

// armR: rests by the pencil → picks it up → draws the star → lays it down → takes the cover → palm on the cover
// returns { arm, pencil: {tip, ang} | null }
function armRight(t, S, pose, tr) {
  const T = (a) => S.T(a);
  const restPalm = [560, 968];
  const restHandAng = 2.0;
  // pencil states
  const pRestTip = PENCIL_REST.tip;
  const restAngP = PENCIL_REST.ang;
  // writing: the pencil stands up from the tip, leaning back up-left out of the fist so its gold body and eraser show
  // above the knuckles (straight up, -1.5, it ran under the sleeve's cuff and the gold pencil never showed)
  const drawAngP = -1.85;
  const starK = tr.star;
  const writeTip = starTip(starK);
  // phases
  const pick = S.k(t, [['s20b01', 0], ['s20b01+0.35', 1, 'inOut']]);        // hand to the pencil
  const lift = S.k(t, [['s20b01+0.35', 0], ['s20b01+0.8', 1, 'inOut']]);     // pencil to the hood
  const look = S.k(t, [['s20b01+2.4', 0], ['s20b01+2.7', 1, 'inOut']]);      // lifts the pencil a hair to look
  const putDown = S.k(t, [['s20b03.end-0.4', 0], ['s20b03.end+0.25', 1, 'inOut']]);
  const release = S.k(t, [['s20b03.end+0.25', 0], ['s20b03.end+0.45', 1]]);
  let pencil = null, arm;
  if (t < T('s20b01+0.35') || t >= T('s20b03.end+0.25')) {
    // resting beside the pencil (start) / after laying it down
    const after = t >= T('s20b03.end+0.25');
    const gripRest = [pRestTip[0] + Math.cos(restAngP) * 18, pRestTip[1] + Math.sin(restAngP) * 18];
    pencil = { tip: pRestTip, ang: restAngP };
    if (!after) {
      // the fingers close round the pencil as the hand arrives (flat → grip, palm turning in)
      const p = [lerp(restPalm[0], gripRest[0], pick), lerp(restPalm[1], gripRest[1], pick)];
      const ang = lerp(restHandAng, 2.3, pick), g = sm((pick - 0.35) / 0.65);
      const target = wristForGrip(p, ang, g);
      arm = { target, bend: 1, front: true, hand: blendHand('flat', 'grip', g), palmDir: mixP(P_DOWN, P_PENCIL, g), handAngle: ang, ...foreshorten(pose, target, 1) };
    } else {
      // pencil released; the hand rests, rises to meet the standing cover's top edge, lays it down and rests on it
      const nb = notebookDraw(tr);
      const meet = S.k(t, [['s20b04+0.95', 0], ['s20b04+1.45', 1, 'inOut']]);     // up to the cover's edge
      const settle = S.k(t, [['s20b04+2.0', 0], ['s20b04+2.45', 1, 'inOut']]);   // palm settles flat on the cover
      const restP = [restPalm[0] - 4, restPalm[1] + 4];
      let p, ang;
      let grip = 0;
      if (meet <= 0) {
        // fingers open off the pencil and the hand settles beside it
        p = [lerp(gripRest[0], restP[0], release), lerp(gripRest[1], restP[1], release)];
        ang = lerp(2.3, 2.1, release); grip = 1 - sm(release);
      } else if (t < T('s20b04+1.45')) {
        // rising to the cover's top edge as it comes up to vertical (fingers toward the spine)
        const e = [nb.edge[0] + 12, nb.edge[1] + 6];
        p = [lerp(restP[0], e[0], meet), lerp(restP[1], e[1], meet) - Math.sin(meet * Math.PI) * 10];
        ang = lerp(2.1, 2.75, meet);
      } else {
        // the palm rides the free edge down as the cover closes, then settles flat on it
        const e = [nb.edge[0] + 12, nb.edge[1] + 6];
        const onCover = [NBK[0] + 54, 984];       // left of the cover's hooded figure, which stays in view
        p = [lerp(e[0], onCover[0], settle), lerp(e[1], onCover[1], settle)];
        ang = lerp(2.75, 1.7, ease.inOut(clamp((t - T('s20b04+1.6')) / 0.75)));
      }
      const target = grip > 0 ? wristForGrip(p, ang, grip) : wristForPalm(p, ang);
      arm = { target, bend: 1, front: true, hand: blendHand('flat', 'grip', grip), palmDir: mixP(P_DOWN, P_PENCIL, grip), handAngle: ang, ...foreshorten(pose, target, 1) };
      pencil = { tip: pRestTip, ang: restAngP };
    }
    return { arm, pencil };
  }
  // holding the pencil: lift → draw → look → (b02/b03 rests holding it on the page) → put down
  const liftTipFrom = pRestTip;
  let tip;
  if (lift < 1) tip = [lerp(liftTipFrom[0], writeTip[0], lift), lerp(liftTipFrom[1], writeTip[1], lift) - Math.sin(lift * Math.PI) * 14];
  else tip = [writeTip[0] + look * 3, writeTip[1] - look * 7];
  // after the star (b02/b03) the pencil hand settles a little lower on the page, then lays the pencil down
  const settleB = S.k(t, [['s20b01+2.8', 0], ['s20b02+0.8', 1, 'inOut']]);
  tip = [tip[0] + settleB * 8, tip[1] + settleB * 12];
  if (putDown > 0) tip = [lerp(tip[0], pRestTip[0], putDown), lerp(tip[1], pRestTip[1], putDown) - Math.sin(putDown * Math.PI) * 12];
  const aFrom = restAngP, aTo = drawAngP;
  let pang = lerp(aFrom, aTo, ease.inOut(lift));
  if (putDown > 0) pang = lerp(aTo, aFrom, ease.inOut(putDown));
  pang += look * 0.12;
  // tiny writing tremor / pressure
  const writing = starK > 0 && starK < 1 ? 1 : 0;
  const grip = [tip[0] + Math.cos(pang) * 18, tip[1] + Math.sin(pang) * 18];
  const hAng = 2.3 + writing * fbm(t * 3, 51) * 0.04;
  const target = wristForGrip(grip, hAng);
  arm = { target, bend: 1, front: true, hand: 'grip', palmDir: P_PENCIL, handAngle: hAng, ...foreshorten(pose, target, 1) };
  pencil = { tip, ang: pang };
  return { arm, pencil };
}

// armL: rests on the left page → wipes the cheek with the sleeve (b03) → lifts the cover → reaches to the lamp →
// clicks → back to the desk
function armLeft(t, S, pose, tr) {
  const T = (a) => S.T(a);
  const restPalm = [356, 962];
  const rest = { target: wristForPalm(restPalm, 1.25), bend: -1, front: true, hand: 'flat', handAngle: 1.25, palmDir: P_DOWN };
  rest.reach1 = rest.reach2 = foreshorten(pose, rest.target, -1).reach1;
  // after the hold on the drop: up to the cheek, one stroke over the drop, back down to the page just before
  // the hand takes the cover (b04+0.5)
  const wipe = S.k(t, [['s20b03+2.5', 0], ['s20b03+2.92', 1, 'inOut'], ['s20b03+3.18', 1], ['s20b04+0.46', 0, 'inOut']]);
  if (t < T('s20b04+0.5')) {
    if (wipe <= 0) return rest;
    // the sweater-paw knuckle under the lamp-side eye (self.mjs wipeTear geometry), one small stroke outward
    const ref = selfPoseAnchors(SX, SY, SS, pose);
    const hc = ref.headCenter, ht = ref.headTop;
    const rot = Math.atan2(ht[0] - hc[0], -(ht[1] - hc[1]));
    const stroke = S.k(t, [['s20b03+2.82', 0], ['s20b03+3.18', 1, 'inOut']]);
    const hx = lerp(-34, -44, stroke), hy = lerp(44, 50, stroke);
    const c = Math.cos(rot), sn = Math.sin(rot);
    const wT = selfLocal(SX, SY, SS, 1, hc[0] + hx * c - hy * sn, hc[1] + hx * sn + hy * c);
    // the hand lifts off the page and rises in front of the chest to the cheek. In 2D the hand passes right over the
    // shoulder, where any fixed pair of bone lengths folds the arm flat and swings the elbow out to the frame edge, so
    // the elbow is steered instead: it glides from where the resting arm has it to tucked in front of the chest, and
    // the two bone lengths (foreshortening) are solved from shoulder–elbow–wrist every frame.
    const u = wipe, P0 = rest.target, P1 = [lerp(P0[0], wT[0], 0.75), lerp(P0[1], wT[1], 0.3)];
    const target = [0, 1].map((i) => (1 - u) * (1 - u) * P0[i] + 2 * u * (1 - u) * P1[i] + u * u * wT[i]);
    const shW = selfPoseAnchors(SX, SY, SS, pose).shoulderL, sh = [(shW[0] - SX) / SS, (shW[1] - SY) / SS];
    const ir = ik(sh[0], sh[1], P0[0], P0[1], 100 * rest.reach1, 92 * rest.reach2, -1);
    const eRest = [sh[0] + Math.cos(ir.a1) * 100 * rest.reach1, sh[1] + Math.sin(ir.a1) * 100 * rest.reach1];
    const eTuck = [sh[0] + 14, sh[1] + 52];
    const ek = ease.inOut(clamp(wipe / 0.7));
    const el = [lerp(eRest[0], eTuck[0], ek), lerp(eRest[1], eTuck[1], ek)];
    const l1 = Math.hypot(el[0] - sh[0], el[1] - sh[1]), l2 = Math.hypot(target[0] - el[0], target[1] - el[1]);
    const cross = (target[0] - sh[0]) * (el[1] - sh[1]) - (target[1] - sh[1]) * (el[0] - sh[0]);
    const f = sm((wipe - 0.25) / 0.5);              // the fingers curl into the sweater-paw fist on the way up
    return { target, bend: cross > 0 ? -1 : 1, front: true, hand: blendHand('flat', 'fist', f), palmDir: mixP(P_DOWN, P_WIPE, f),
      handAngle: lerp(1.25, rot - Math.PI / 2 + 0.32, ease.inOut(wipe)), reach1: (l1 + 0.02) / 100, reach2: (l2 + 0.02) / 92 };
  }
  // take the cover's free edge (the left page's outer edge) and lift it up to vertical (open 1 → 0.5); let go there
  // and reach straight on to the lamp (the right hand lays the cover down meanwhile); click; back to the desk
  const take = S.k(t, [['s20b04+0.5', 0], ['s20b04+0.72', 1, 'inOut']]);
  const toLamp = S.k(t, [['s20b04+1.5', 0], ['s20b04+2.25', 1, 'inOut'], ['s20b04+2.6', 1], ['s20b04+3.5', 0, 'inOut']]);
  const press = Math.sin(clamp((t - T('s20b04+2.3')) / 0.2) * Math.PI);
  const back = S.k(t, [['s20b04+2.6', 0], ['s20b04+3.5', 1, 'inOut']]);
  if (take <= 0 || back >= 1) return rest;
  // the hand slides along the page to the cover's free edge and takes it: palm and fingers on the page side, the thumb
  // under the edge (palm down, the 'hold' thumb is hidden behind the hand: it never shows on the page); it lifts the
  // cover with the fingers along it toward the spine; frozen at vertical once released. (The old grip sat on the page
  // with its thumb on top, fingers and thumb on the same side.)
  const nbH = notebookDraw({ ...tr, open: Math.max(tr.open, 0.5) });
  const ax = Math.atan2(NBK[1] - nbH.edge[1], NBK[0] - nbH.edge[0]);   // free edge → spine, along the leaf
  const holdAng = lerp(1.25, ax, take);
  const e = [nbH.edge[0] + Math.cos(ax) * 24, nbH.edge[1] + Math.sin(ax) * 24];   // grip centre 24 px in from the edge
  const holdP = [lerp(restPalm[0], e[0], take), lerp(restPalm[1], e[1], take) - Math.sin(take * Math.PI) * 6];
  const hk = sm(take);
  const holdHand = blendHand('flat', 'hold', hk), holdPalm = mixP(P_DOWN, P_COVER, hk);
  if (toLamp <= 0) {
    const target = wristForGrip(holdP, holdAng, hk);
    return { target, bend: -1, front: true, hand: holdHand, palmDir: holdPalm, handAngle: holdAng, ...foreshorten(pose, target, -1) };
  }
  // out to the lamp shade from where it let go of the cover (the hand flattens, then points at the switch); back to
  // the bare desk afterwards (the book has closed)
  const from = back > 0 ? restPalm : holdP;
  const lampP = [196, 806 + press * 3];
  const u = toLamp;
  const p = [lerp(from[0], lampP[0], u), lerp(from[1], lampP[1], u) - Math.sin(u * Math.PI) * 14];
  // (on the way out the wrist turns toward the lamp early, so the hand that held the cover's top edge — fingers down
  // along it — does not trail drooping behind the rising arm)
  const ang = lerp(back > 0 ? 1.25 : holdAng, Math.PI - 0.2, back > 0 ? u : sm(u / 0.5));
  const gk = back > 0 ? 0 : 1 - sm(u / 0.35);      // the grip offset fades out as the hand leaves the cover
  const target = gk > 0 ? wristForGrip(p, ang, gk) : wristForPalm(p, ang);
  const hand = back > 0 ? blendHand('flat', 'point', sm((u - 0.5) / 0.4)) : blendHand(blendHand('flat', 'hold', gk), 'point', sm((u - 0.5) / 0.4));
  const palmDir = back > 0 ? P_DOWN : mixP(P_DOWN, P_COVER, gk);
  return { target, bend: -1, front: true, hand, palmDir, handAngle: ang, ...foreshorten(pose, target, -1) };
}

// the notebook's draw position (the right half stays put while it closes) and its free edge (world)
function notebookDraw(tr) {
  const k = ease.sine(tr.open);
  const spineL = lerp(-110, 0, k);                   // drawNotebook's spine (local, scale 1)
  const s = NBK[2], c = Math.cos(NB_ROT), sn = Math.sin(NB_ROT);
  // shift so the spine stays at the open book's spine (NBK[0], NBK[1])
  const x = NBK[0] - spineL * s * c, y = NBK[1] - spineL * s * sn;
  const cw = Math.cos(tr.open * Math.PI);
  // the leaf rises toward camera: standing up it is 220 × cos 30° tall on screen (the desk is seen from 30° up)
  const ex = (spineL + 220 * cw) * s, ey = -Math.sin(tr.open * Math.PI) * LEAF_RISE * s;
  return { x, y, spineX: NBK[0], edge: [x + ex * c, y + ex * sn + ey] };
}

// 2×3 affine matrices [a, b, c, d, e, f] (canvas order)
const mmul = (A, B) => [A[0] * B[0] + A[2] * B[1], A[1] * B[0] + A[3] * B[1], A[0] * B[2] + A[2] * B[3], A[1] * B[2] + A[3] * B[3],
  A[0] * B[4] + A[2] * B[5] + A[4], A[1] * B[4] + A[3] * B[5] + A[5]];
const minv = (A) => {
  const det = A[0] * A[3] - A[1] * A[2];
  const a = A[3] / det, b = -A[1] / det, c = -A[2] / det, d = A[0] / det;
  return [a, b, c, d, -(a * A[4] + c * A[5]), -(b * A[4] + d * A[5])];
};
// The notebook lying on the desk, closing about its spine. drawNotebook draws a turning leaf as a flat strip that only
// narrows (right for a camera looking straight down), so a cover lifted to vertical vanished. Here the book is drawn in
// two passes: the right half as it lies (page block, right page — `onPage` draws on it), then the leaf alone, sheared so
// its free edge rises toward camera by sin(angle) × LEAF_RISE: the cover visibly stands up and comes down over the page.
function drawBook(g, tr, dim, onPage) {
  const s = NBK[2], open = tr.open, st = { flat: 1, rot: NB_ROT, dim };
  if (open >= 0.999) { drawNotebook(g, NBK[0], NBK[1], s, { ...st, open: 1 }); onPage(); return; }
  const nb = notebookDraw(tr);
  if (open <= 0.001) { drawNotebook(g, nb.x, nb.y, s, { ...st, open: 0 }); return; }
  // pass 1: the right half (the open book clipped at the spine)
  g.save();
  g.translate(NBK[0], NBK[1]); g.rotate(NB_ROT);
  g.beginPath(); g.rect(-1.5, -400, 1000, 800); g.clip();
  g.rotate(-NB_ROT); g.translate(-NBK[0], -NBK[1]);
  drawNotebook(g, NBK[0], NBK[1], s, { ...st, open: 1 });
  g.restore();
  onPage();
  // pass 2: the leaf, sheared about the spine
  const a = open * Math.PI, cw = Math.cos(a), lw = Math.abs(cw) * 220;
  const u0 = lerp(-110, 0, ease.sine(open));                      // drawNotebook's local spine x
  const R = Math.sin(a) * LEAF_RISE / 0.5;                        // rise in local y units (the book is squashed ×0.5)
  const c = Math.cos(NB_ROT), sn = Math.sin(NB_ROT);
  const M = [s * c, s * sn, -s * 0.5 * sn, s * 0.5 * c, nb.x, nb.y];
  g.save();
  if (lw < 3) {
    // edge-on: just the board's thickness, standing up from the spine
    g.transform(...M);
    g.fillStyle = dim > 0.01 ? '#5a4a3a' : '#c99a4a';
    g.strokeStyle = 'rgba(60,35,20,0.8)'; g.lineWidth = 2;
    g.beginPath(); g.rect(u0 - 3, -145 - R, 6, 290 + R); g.fill(); g.stroke();
    g.restore();
    return;
  }
  if (cw < 0) {
    // the left half's drop shadow (pass 1 clipped it away) fades as the leaf lifts off the desk
    g.save(); g.transform(...M);
    g.fillStyle = `rgba(30,15,10,${0.28 * (1 - dim * 0.5) * (1 - Math.sin(a))})`;
    g.beginPath(); g.roundRect(u0 - 220 * -cw - 3, -145 + 14, 220 * -cw + 3, 294, 12); g.fill();
    g.restore();
  }
  const k = (cw < 0 ? R : -R) / lw;
  const Sh = [1, k, 0, 1, 0, -k * u0];
  g.transform(...mmul(M, Sh));
  g.beginPath();
  if (cw < 0) g.rect(u0 - lw - 8, -160, lw + 8.5, 320); else g.rect(u0 - 0.5, -160, lw + 2, 320);
  g.clip();
  g.transform(...minv(M));
  drawNotebook(g, nb.x, nb.y, s, { ...st, open, shadow: false });
  g.restore();
}

// ------------------------------------------------------------------ SELF's face and body
function selfPose(t, S, tr) {
  const k = (keys) => S.k(t, keys);
  const T = (a) => S.T(a);
  // gaze: the drawing (follows the pencil) → the star → (b02/b03) soft, inward → the page → the closing book →
  // the lamp → up to the window
  // (during the tear the gaze stays soft and inward, a little down-right — the eyes stay open on the camera's side;
  // after the wipe they come back down to the page)
  const lookX = k([['scene.start', 0.42], ['s20b01+0.8', 0.5], ['s20b01+2.4', 0.55], ['s20b02', 0.5], ['s20b02+1.0', 0.3],
    ['s20b03+1.6', 0.2], ['s20b03+2.8', 0.24], ['s20b03+3.35', 0.4], ['s20b04+0.4', 0.3], ['s20b04+0.75', -0.15], ['s20b04+1.25', 0.05],
    ['s20b04+1.55', -0.75], ['s20b04+2.5', -0.75], ['s20b04+2.9', 0.0], ['s20b04+3.5', 0.55]]) + fbm(t * 0.4, 61) * 0.03;
  const lookY = k([['scene.start', 0.66], ['s20b01+2.4', 0.62], ['s20b02', 0.55], ['s20b02+1.0', 0.4], ['s20b03+1.6', 0.34],
    ['s20b03+2.8', 0.38], ['s20b03+3.35', 0.62], ['s20b04+0.75', 0.7], ['s20b04+1.25', 0.5], ['s20b04+1.55', 0.15], ['s20b04+2.5', 0.15], ['s20b04+2.9', -0.4],
    ['s20b04+3.6', -1.0]]) + fbm(t * 0.37, 62) * 0.025;
  // brows inner-up (moved) → softening as they laugh at themselves → raised gently at the stars
  const browIn = k([['scene.start', 0.55], ['s20b02', 0.62], ['s20b03+0.9', 0.75], ['s20b03+2.0', 0.45], ['s20b03.end', 0.35],
    ['s20b04+2.6', 0.3], ['s20b04+3.6', 0.15]]);
  const browUp = k([['scene.start', 0.05], ['s20b03+2.0', 0.12], ['s20b03.end', 0.05], ['s20b04+2.8', 0.05], ['s20b04+3.8', 0.38]]);
  // lids: glistening, lower lids lifted; the laugh squeezes the lower lids; wide-soft at the stars
  const lidU = k([['scene.start', 0.2], ['s20b02', 0.24], ['s20b03', 0.3], ['s20b03+2.0', 0.36], ['s20b03.end', 0.22],
    ['s20b04+2.7', 0.18], ['s20b04+3.8', -0.08]]);
  // (looking up at the window the lower lids drop so white shows under the irises: with them raised the up-gaze read as
  // looking into the lens)
  const lidL = k([['scene.start', 0.42], ['s20b03+1.9', 0.42], ['s20b03+2.3', 0.62], ['s20b03.end', 0.45], ['s20b04+2.7', 0.3],
    ['s20b04+3.6', 0.08], ['s20b04+5.6', 0.16]]);
  // mouth: lips lightly together in a small moved smile (pressed stays < 0.3 there: above it the rig tucks the corners
  // down and the smile read as a frown) → the smile wavers and the lips press as the tear wells → the soft laugh (open a
  // hair) → smile down at the page → settled smile
  const laugh = Math.sin(clamp((t - T('s20b03+1.95')) / 0.6) * Math.PI);
  const smile = k([['scene.start', 0.4], ['s20b01+2.4', 0.42], ['s20b02', 0.36], ['s20b02+1.4', 0.26], ['s20b03+0.9', 0.1], ['s20b03+1.9', 0.3], ['s20b03+2.4', 0.62],
    ['s20b03.end', 0.5], ['s20b04+2.6', 0.42], ['s20b04+4.0', 0.5]]);
  const pressed = k([['scene.start', 0.2], ['s20b02+0.6', 0.26], ['s20b02+1.4', 0.42], ['s20b03+0.9', 0.7], ['s20b03+1.9', 0.6], ['s20b03+2.2', 0.1], ['s20b03.end', 0.2],
    ['s20b04+2.6', 0.25], ['s20b04+3.6', 0.05]]);
  // tears: glistening → welling on 'After that,' (the rig's band + drawWetEyes' bright water line) → the one drop
  // (drawWetEyes, tracks.tear) spills around the middle of the next line → the eyes stay wet through the hold → wiped →
  // dry-ish. No `stream`: the rig's sustained-cry tears would add more drops, alternating eyes; one tear reads best.
  const tears = k([['scene.start', 0.42], ['s20b02', 0.45], ['s20b02+1.2', 0.9], ['s20b03+0.8', 1], ['s20b03+2.8', 0.85],
    ['s20b03+3.25', 0.45], ['s20b04+0.4', 0.3], ['s20b04+2.6', 0.28], ['s20b04+4', 0.4]]);
  const tremble = k([['s20b02+0.8', 0], ['s20b03+0.6', 0.18], ['s20b03+1.9', 0.12], ['s20b03+2.2', 0]]);
  const sparkle = k([['s20b04+2.7', 0], ['s20b04+3.8', 0.75]]);
  // deliberate blinks (auto-blink off: an intimate held portrait)
  const blink = Math.max(
    blinkAt(t, T('s20b01+1.0'), 0.2),          // concentrating
    blinkAt(t, T('s20b01+2.55'), 0.32),         // looks at the finished star
    blinkAt(t, T('s20b02+0.15'), 0.48),         // the slow blink on 'After that,'
    blinkAt(t, T('s20b03+0.5'), 0.42),          // a slow squeeze: the tear spills as the eyes reopen (+0.85)
    blinkAt(t, T('s20b04+0.9'), 0.22),
    blinkAt(t, T('s20b04+2.75'), 0.25),         // as the room goes blue
    blinkAt(t, T('s20b04+5.1'), 0.62),          // one slow, contented blink
  ) + laugh * 0.25;
  const face = { ...SELF_EXPR.tenderSmile, lookX, lookY, browIn, browUp, lidU, lidL, smile, pressed, tears,
    tremble, sparkle, blink, noAutoBlink: true, blush: 0.28, pupil: 1 + sparkle * 0.15, open: laugh * 0.08 };
  // head: inclined toward the page; on the laugh a soft double bob; the chin lifts to the window at the end
  const up = k([['s20b04+2.7', 0], ['s20b04+3.8', 1, 'inOut']]);
  const toLamp = k([['s20b04+1.4', 0], ['s20b04+2.0', 1, 'inOut'], ['s20b04+2.6', 1], ['s20b04+3.2', 0, 'inOut']]);
  const headTilt = lerp(0.13, -0.1, up) + fbm(t * 0.21, 63) * 0.012 - toLamp * 0.05;
  const headTurn = lerp(0.04, 0.24, up) - toLamp * 0.3 + fbm(t * 0.18, 64) * 0.02;
  const bob = laugh * (0.6 + 0.4 * Math.sin((t - T('s20b03+1.95')) * TAU * 3.2));
  const headDY = lerp(4, -4, up) + bob * 2.2;
  // breathing: a slow breath in after the star (b01+2.4 → +2.8); slower and settled at the end
  const breathIn = Math.sin(clamp((t - T('s20b01+2.3')) / 1.4) * Math.PI);
  const breathe = 1.1 + breathIn * 0.6;
  return { t, seated: true, outfit: 'sweater', bodyTurn: lerp(-0.06, 0.05, up) - toLamp * 0.12, headTurn, headTilt, headDY,
    face, breathe, breathRate: lerp(0.19, 0.15, up), shrug: 0.04 + breathIn * 0.1 + laugh * 0.1,
    lean: -toLamp * 0.035 };
}

// world position of SELF's iris (side −1 = screen-left eye) for a pose — same geometry as the face rig (SELF_FACE)
function irisWorld(pose, side) {
  const a = selfPoseAnchors(SX, SY, SS, pose);
  const hc = a.headCenter, ht = a.headTop;
  const rot = Math.atan2(ht[0] - hc[0], -(ht[1] - hc[1]));
  const f = pose.face || {};
  const turn = clamp(pose.headTurn ?? 0, -1, 1), at = Math.abs(turn);
  const squeeze = side * turn > 0 ? 1 - at * 0.38 : 1 + at * 0.06;
  const rx = 16 * squeeze, ry = 12.6;
  const ix = side * 27 * (1 - at * 0.3) + turn * 27 * 0.55 + clamp(f.lookX || 0, -1, 1) * rx * 0.42;
  const iy = 2 + clamp(f.lookY || 0, -1, 1) * ry * 0.36 + ry * 0.04;
  const c = Math.cos(rot), sn = Math.sin(rot);
  return { p: [hc[0] + (ix * c - iy * sn) * SS, hc[1] + (ix * sn + iy * c) * SS], r: rx * 0.6 * SS };
}
// "the stars reflect in the eyes": the rig's sparkle is painted under the night-blue room light and is lost in the dark
// ending, so a small twinkling 4-point glint per iris is drawn on top of the lit pass
function drawEyeStars(g, pose, k, t) {
  if (k <= 0.01) return;
  const open = 1 - clamp((pose.face.blink || 0) * 1.6);
  if (open <= 0.02) return;
  for (const side of [-1, 1]) {
    const { p, r } = irisWorld(pose, side);
    const tw = 0.75 + 0.25 * Math.sin(t * 3.1 + side * 1.7);
    const x = p[0] + r * 0.32, y = p[1] - r * 0.3;
    const a = k * open;
    const gl = g.createRadialGradient(x, y, 0, x, y, r * 0.9);
    gl.addColorStop(0, `rgba(200,220,255,${0.5 * a})`); gl.addColorStop(1, 'rgba(200,220,255,0)');
    g.fillStyle = gl; g.fillRect(x - r, y - r, r * 2, r * 2);
    g.fillStyle = `rgba(255,252,235,${0.95 * a})`;
    star(g, x, y, r * 0.42 * tw);
    g.fillStyle = `rgba(255,255,255,${0.8 * a})`;
    g.beginPath(); g.arc(p[0] - r * 0.35, p[1] + r * 0.25, r * 0.12, 0, TAU); g.fill();
  }
}

// ---- the wet eyes and the tear (drawn over the lit body pass, under the wiping sleeve). The rig's welling band sits
// under SELF's raised lower lids, so after the encoder it did not read: here the water pools ON the lower lid (a bright
// line with a specular stripe and a catch-light on the iris), and the one tear (face.mjs drawTear, the film's tear)
// gathers on the near eye's lower lid, spills, runs down the cheek and fades out as a whole under the sleeve.
// Geometry mirrors face.mjs drawEye (SELF_FACE: eyeSpacing 27, eyeY 2, eyeRx 16, eyeRy 12.6, restLid 0.15).
function eyeGeom(pose, side) {
  const f = pose.face, turn = clamp(pose.headTurn ?? 0, -1, 1), at = Math.abs(turn);
  const squeeze = side * turn > 0 ? 1 - at * 0.38 : 1 + at * 0.06;
  const rx = 16 * squeeze, ry = 12.6, cx = side * 27 * (1 - at * 0.3) + turn * 27 * 0.55, cy = 2;
  const rest = 0.15, lidU = f.lidU || 0, blink = clamp(f.blink || 0);
  let up = clamp(rest + lidU * (lidU < 0 ? 0.3 : 1) + blink * (1 - (rest + lidU)), -0.25, 1);
  if (lidU < 0) up = clamp(rest + lidU * 0.3 + blink * (1 - rest), -0.25, 1);
  const low = clamp(f.lidL || 0) * (1 - clamp(up, 0, 1) * 0.5);
  const bnd = (dx) => ry * Math.sqrt(clamp(1 - (dx * dx) / (rx * rx)));
  const lowY = (dx) => cy + lerp(bnd(dx) + ry * 0.05, -ry * 0.05 + (dx * dx) / (rx * rx) * ry * 0.25, low * 0.75);
  const upY = (dx) => {
    const k = clamp(up, -0.25, 1), tilt = f.lidTilt || 0, outer = (dx * side) / rx;
    return cy + lerp(-bnd(dx) - ry * 0.05, ry * 0.3 - (dx * dx) / (rx * rx) * ry * 0.1, Math.max(0, k)) + (k < 0 ? k * ry * 0.35 : 0) +
      tilt * outer * ry * 0.38 * Math.min(1, Math.max(0, k) + 0.6);
  };
  const ix = cx + clamp(f.lookX || 0, -1, 1) * rx * 0.42, iy = cy + clamp(f.lookY || 0, -1, 1) * ry * 0.36 + ry * 0.04;
  return { cx, cy, rx, ry, up, lowY, upY, ix, iy, irisR: rx * 0.6 };
}
function drawWetEyes(g, pose, tr, well) {
  const tear = tr.tear, alive = 1 - tr.wiped;
  const tearOn = tear > 0 && tear < 1 && alive > 0.01;
  if (well <= 0.01 && !tearOn) return;
  const a = selfPoseAnchors(SX, SY, SS, pose);
  const hc = a.headCenter, ht = a.headTop;
  const rot = Math.atan2(ht[0] - hc[0], -(ht[1] - hc[1]));
  g.save();
  g.translate(hc[0], hc[1]); g.rotate(rot); g.scale(SS, SS);
  g.lineCap = 'round'; g.lineJoin = 'round';
  for (const side of [-1, 1]) {
    const e = eyeGeom(pose, side);
    const open = clamp(1 - e.up) / 0.85;
    // water pooled on the lower lid: a glossy band just above the lash line, a white specular stripe on it
    if (well > 0.01) {
      const line = (from, to, off) => {
        g.beginPath();
        for (let i = 0; i <= 10; i++) {
          const dx = lerp(from, to, i / 10) * e.rx;
          const y = e.lowY(dx) + off;
          if (i === 0) g.moveTo(e.cx + dx, y); else g.lineTo(e.cx + dx, y);
        }
      };
      g.strokeStyle = `rgba(196,230,255,${0.6 * well})`; g.lineWidth = 2.8;
      line(-0.8, 0.8, -1.1); g.stroke();
      g.strokeStyle = `rgba(255,255,255,${0.92 * well})`; g.lineWidth = 1.3;
      line(side > 0 ? -0.5 : -0.1, side > 0 ? 0.1 : 0.5, -1.5); g.stroke();
      // the bright catch-light on the wet iris (the lamp), only where the upper lid leaves the iris open
      const hx = e.ix - e.irisR * 0.36, hy = e.iy - e.irisR * 0.38;
      const vis = clamp((hy - e.upY(hx - e.cx) - 1.5) / 2.5) * open;
      if (vis > 0.01) {
        const ka = well * vis;
        const gl = g.createRadialGradient(hx, hy, 0, hx, hy, e.irisR * 0.62);
        gl.addColorStop(0, `rgba(255,255,255,${0.5 * ka})`); gl.addColorStop(1, 'rgba(255,255,255,0)');
        g.fillStyle = gl; g.fillRect(hx - e.irisR, hy - e.irisR, e.irisR * 2, e.irisR * 2);
        g.fillStyle = `rgba(255,255,255,${ka})`;
        g.beginPath(); g.arc(hx, hy, e.irisR * 0.27, 0, TAU); g.fill();
        g.fillStyle = `rgba(255,255,255,${0.8 * ka})`;
        g.beginPath(); g.arc(e.ix + e.irisR * 0.34, e.iy + e.irisR * 0.3, e.irisR * 0.12, 0, TAU); g.fill();
      }
    }
    if (side > 0 || !tearOn) continue;
    // ---- the near eye's one tear, in the film's tear style (face.mjs drawTear: a translucent, slightly blue drop with
    // its own short trail; gathers on the lid, runs down the cheek, and the whole of it fades with `alive` under the
    // sleeve). Sized up from the rig's SELF tear (×1.3) so it survives the encoder in this close-up.
    const dx0 = side * e.rx * 0.45, x0 = e.cx + dx0, y0 = e.lowY(dx0) + 0.8;
    drawTear(g, x0, y0, SELF_FACE.tearRun, tear, SELF_FACE.tearSize * 1.3, side, alive);
  }
  g.restore();
}

// the lit layer only needs to cover what each pass draws (seated: nothing of the torso below the desk line)
const BOX_BODY = [150, 470, 560, 470], BOX_FRONT = [140, 600, 570, 490];   // front: the sleeve wipe reaches the cheek
// SELF lit like the room (+ the window-blue rim on the far cheek while the lamp is on)
function drawSelfLit(g, st, pose, layer) {
  // the arms/hands pass (on the desk, in the lamp pool) reads the same unlit while the lamp is fully on: saves a layer
  if (layer === 'front' && (st.lamp ?? 1) >= 0.999) { drawSelf(g, SX, SY, SS, { ...pose, layer }); return; }
  drawLitByRoom(g, st, (c) => {
    drawSelf(c, SX, SY, SS, { ...pose, layer });
    const rim = st.lamp;
    if (layer !== 'body' || rim <= 0.01) return;
    const a = selfPoseAnchors(SX, SY, SS, pose);
    const [hx, hy] = a.headCenter;
    c.globalCompositeOperation = 'source-atop';
    let gr = c.createRadialGradient(hx + 104, hy - 30, 30, hx + 104, hy - 30, 96);
    gr.addColorStop(0, `rgba(150,185,255,${0.45 * rim})`); gr.addColorStop(0.55, `rgba(130,165,255,${0.16 * rim})`); gr.addColorStop(1, 'rgba(130,165,255,0)');
    c.fillStyle = gr; c.fillRect(hx - 20, hy - 140, 240, 260);
    const [sx, sy] = a.shoulderR;
    gr = c.createRadialGradient(sx + 70, sy - 40, 20, sx + 70, sy - 40, 110);
    gr.addColorStop(0, `rgba(150,185,255,${0.3 * rim})`); gr.addColorStop(1, 'rgba(130,165,255,0)');
    c.fillStyle = gr; c.fillRect(sx - 60, sy - 160, 260, 280);
  }, layer === 'body' ? BOX_BODY : BOX_FRONT);
}

// ------------------------------------------------------------------ render
export function render(g, t, S) {
  const tr = tracks(t, S);
  // camera
  let cam;
  // the push arrives while the drop slides down the cheek (+2.3); a held close-up on the drop and the wipe;
  // the pull-back starts once the sleeve has left the face
  const tPullA = S.T('s20b03+3.15'), tPullB = S.T('s20b04+2.6');
  if (t < S.T('s20b02')) cam = { ...CAM_DESK };
  else if (t < tPullA) {
    const p = S.k(t, [['s20b02', 0], ['s20b03+2.3', 1, 'inOut']]);
    cam = { x: lerp(CAM_DESK.x, CAM_CLOSE.x, p), y: lerp(CAM_DESK.y, CAM_CLOSE.y, p), zoom: Math.exp(lerp(Math.log(CAM_DESK.zoom), Math.log(CAM_CLOSE.zoom), p)) };
  } else {
    // the pull-back to the opening composition starts in the pause after the line and arcs through the desk framing
    // (a quadratic curve through `desk` at its middle), so the book and both hands are well clear of the bottom 15 %
    // while it closes; a straight pull kept them at the frame's bottom edge until the cover was down
    const u = ease.sine(clamp((t - tPullA) / (tPullB - tPullA)));
    const P0 = [CAM_CLOSE.x, CAM_CLOSE.y, Math.log(CAM_CLOSE.zoom)], P2 = [CAM_OPEN.x, CAM_OPEN.y, Math.log(CAM_OPEN.zoom)];
    const PM = [CAM_DESK.x, CAM_DESK.y, Math.log(CAM_DESK.zoom)];
    const q = [0, 1, 2].map((i) => {
      const P1 = 2 * PM[i] - (P0[i] + P2[i]) / 2;
      return (1 - u) * (1 - u) * P0[i] + 2 * u * (1 - u) * P1 + u * u * P2[i];
    });
    cam = { x: q[0], y: q[1], zoom: Math.exp(q[2]) };
  }
  // gentle life (fades out in the final hold: the mirror still)
  const dAmp = 2.2 * (1 - S.k(t, [['s20b04+2.0', 0], ['s20b04+3.5', 0.7]]));
  const d = drift(t, dAmp, 7);
  cam.x += d.dx / cam.zoom; cam.y += d.dy / cam.zoom;
  // keep inside the stage
  const zx = 360 / cam.zoom, zy = 640 / cam.zoom;
  cam.x = clamp(cam.x, zx, REALROOM.width - zx); cam.y = clamp(cam.y, zy, REALROOM.height - zy);

  const st = { t, lamp: tr.lamp, fairy: tr.fairy, moon: 1, dusk: 0, starHood: tr.starHood, starWink: tr.starWink };
  const base = selfPose(t, S, tr);
  const R = armRight(t, S, base, tr);
  const L = armLeft(t, S, base, tr);
  const pose = { ...base, armL: L, armR: R.arm };

  g.save();
  applyCamera(g, cam);
  drawRealRoom(g, st);
  drawSelfLit(g, st, pose, 'body');
  // the wet eyes and THE tear (b02 → the wipe), unlit on top: they catch the lamp
  drawWetEyes(g, pose, tr, clamp((pose.face.tears - 0.5) / 0.4) * (1 - tr.lampOff));
  drawEyeStars(g, pose, pose.face.sparkle, t);
  drawRealRoomForeground(g, st);
  const dim = 0.5 * tr.lampOff;
  // the star lives on the right page (the cover comes down over it)
  drawBook(g, tr, dim, () => drawPageStar(g, tr.star, S.k(t, [['s20b01+2.2', 0], ['s20b01+2.6', 1], ['s20b02+1.0', 0.35]])));
  if (R.pencil) drawPencil(g, R.pencil.tip, R.pencil.ang);
  drawSelfLit(g, st, pose, 'front');
  g.restore();

  grade(g, 0, 0.1 * (1 - tr.lampOff));
  vignette(g, 0.3);
}
