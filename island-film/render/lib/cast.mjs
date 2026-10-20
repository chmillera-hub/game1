// cast.mjs - one call to draw a character (body.mjs puppet + face.mjs head) with consistent lighting.
//
//   figure(g, who, pose, o, face)
//     who  'keeper' | 'mira' | 'grandpa';  pose: POSES.x | walkPose(p) | blendPose(a,b,k)
//     o    body opts (x, y, s, facing, costume, t, chestOpen, cellOut, panelGlint, sand, vines, wet, hood, ...)
//          plus  light (LIGHT.* or name), lightX (-1 key light from screen-left .. +1 from right, default -0.5)
//     face drawHead params (expression, gaze, lipsync, glow, ...). Head x/y/s come from the body's head socket;
//          face.yaw is ADDED to the facing-derived yaw; face.roll is added to the neck roll.
//   head(g, who, face)   draw a bare head (CU/ECU shots) - face must include x, y, s; light/lightX like above.
//   Notes: facing -1 mirrors the body; the face is drawn unmirrored with yaw sign flipped so text/seams stay right.
import { LIGHT } from './core.mjs';
import { drawFigure, headSocket } from './body.mjs';
import { drawHead, STYLES } from './face.mjs';

const getLight = l => typeof l === 'string' ? (LIGHT[l] || LIGHT.day) : (l || LIGHT.day);

export function figure(g, who, pose, o = {}, face = {}) {
  const light = getLight(o.light), lx = o.lightX ?? -0.5, facing = o.facing ?? 1;
  drawFigure(g, who, pose, { ...o, light, lightDir: [lx, -0.8],
    head: (hg, hx, hy, hs, roll) => drawHead(hg, STYLES[who], {
      light, lightDir: lx, t: o.t ?? 0, wet: o.wet, ...face,
      x: hx, y: hy, s: hs, roll: roll + (face.roll ?? 0),
      // three-quarter body faces screen-right by default; turn head with it
      yaw: (face.yaw ?? 0) + 0.25 * facing,
    }) });
}

export function head(g, who, face = {}) {
  const light = getLight(face.light);
  drawHead(g, STYLES[who], { t: 0, ...face, light, lightDir: face.lightX ?? face.lightDir ?? -0.5 });
}

export { headSocket };
