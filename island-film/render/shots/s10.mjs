// Scene 10 - dusk epilogue.
import { W, H, PAL, LIGHT, clamp, lerp, seg, ease, noise1, rgba, glow, vignette, handheld, titleCard, canvas } from '../lib/core.mjs';
import { figure } from '../lib/cast.mjs';
import { POSES } from '../lib/body.mjs';
import { cove, sea, beamCone } from '../lib/env.mjs';
import { crab } from '../lib/props.mjs';
import { shipLight } from '../lib/fx.mjs';

const SIL = '#2a2036';
// draw a figure into a scratch layer, then flatten to a silhouette with a thin warm rim
function silhouette(g, fn, rimCol = '#ffb37a') {
  const c = canvas('s10sil'), x = c.getContext('2d');
  x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W, H); fn(x);
  x.globalCompositeOperation = 'source-in'; x.fillStyle = SIL; x.fillRect(0, 0, W, H); x.globalCompositeOperation = 'source-over';
  g.save(); g.globalAlpha = 0.7; g.filter = 'blur(1.5px)'; g.globalCompositeOperation = 'lighter';
  g.drawImage(c, 1.5, -1); g.restore(); // faint rim (offset ghost)
  g.save(); g.fillStyle = rimCol; g.restore();
  g.drawImage(c, 0, 0);
}
const beamA = t => Math.PI + 0.35 + Math.sin(t * 0.35) * 0.9;

export default {
  s10a(g, t, ctx) {
    const hh = handheld(t, 1.2, 201), z = 1 + t * 0.006;
    cove(g, { tod: 18.9, t, beamAngle: beamA(t), boats: 3, camX: hh.x, camY: hh.y, zoom: z });
    // two silhouettes on the point beside the tower, Captain at their feet
    const bx = 520 + hh.x * 0.6, by = 606 + hh.y * 0.6;
    silhouette(g, x => {
      figure(x, 'keeper', POSES.stand, { x: bx, y: by, s: 0.105, t, costume: 'worn', facing: -1, light: 'dusk', breathe: 1 }, { eyeOpen: 1, t });
      figure(x, 'mira', POSES.standWind, { x: bx - 26, y: by + 1, s: 0.16, t, costume: 'island', facing: 1, light: 'dusk', breathe: 1 }, { t, wind: 0.6 });
      crab(x, { x: bx - 12, y: by + 1, s: 0.07, t, eyeYaw: Math.sin(t) * 0.5 });
    });
    vignette(g, 0.35);
  },

  s10b(g, t, ctx) {
    const last = ctx.line('s10b_4'), titleIn = ctx.word('s10b_4', 'someone').start;
    const push = seg(t, 0, ctx.dur, ease.inOutSine);
    const tod = 19.1 + t * 0.03;
    const hz = 560;
    sea(g, { tod, t, horizonY: hz, zoom: 1 + push * 0.5, camY: -push * 60, beam: { x: 360, a: 0.5 } });
    // beam sweeping out from behind/above camera across the sea
    const a = -Math.PI / 2 + 0.1 + Math.sin(t * 0.42 - 0.6) * 1.15;
    beamCone(g, 360 + Math.sin(t * 0.42) * 60, H + 220, a, 1700, 0.09, 0.55);
    // far boat light answers
    const ans = seg(t, ctx.word('s10b_3', 'light').start, ctx.word('s10b_3', 'light').start + 1.5);
    const by = lerp(hz + 8, hz - 10, push);
    shipLight(g, { x: 470, y: by, t, k: ans * (0.7 + 0.3 * Math.max(0, Math.sin(t * 2.4))) });
    glow(g, 360, hz, 300, '#ffc690', 0.25);
    // final title: appears on the last line and holds
    const ta = seg(t, titleIn - 0.1, titleIn + 1.6, ease.inOutSine);
    titleCard(g, 'FOR SOMEONE,', 360, ta, 44);
    titleCard(g, 'SOMEDAY', 420, seg(t, titleIn + 0.4, titleIn + 2.2, ease.inOutSine), 44);
    vignette(g, 0.35);
  },
};
