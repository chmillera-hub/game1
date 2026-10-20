// overlays.mjs - global overlays drawn on top of every shot.
// drawOverlays(g, shot, t, ctx): Directive HUD voice indicator (top center, 240x56 px, cyan brackets,
//   'DIRECTIVE' label in HUDMono, waveform moving only while a directive word is being spoken; 0.25 s fades).
// directiveLevel(ctx, t) -> 0..1 visibility envelope (exported so shots can tint Keeper's iris in sync).
import { W, PAL, clamp, noise1, rgba } from './core.mjs';

export function directiveLevel(ctx, t) {
  let a = 0;
  for (const l of ctx?.lines ?? []) if (l.speaker === 'directive')
    a = Math.max(a, clamp((t - l.start + 0.25) / 0.25) * clamp((l.end + 0.25 - t) / 0.25));
  return a;
}
function wordAct(ctx, t) {
  let v = 0;
  for (const l of ctx.lines) if (l.speaker === 'directive') for (const w of l.words)
    if (t > w.start - 0.03 && t < w.end + 0.06) v = Math.max(v, Math.sin(clamp((t - w.start + 0.03) / (w.end - w.start + 0.09)) * Math.PI));
  return v;
}
export function drawOverlays(g, shot, t, ctx) {
  if (!ctx) return; const a = directiveLevel(ctx, t); if (a <= 0) return;
  const act = wordAct(ctx, t), bw = 240, bh = 56, x = W / 2 - bw / 2, y = 44;
  g.save(); g.globalAlpha = a;
  g.fillStyle = 'rgba(4,20,28,0.35)'; g.fillRect(x, y, bw, bh);
  g.strokeStyle = rgba(PAL.hud, 0.9); g.lineWidth = 1.5; g.shadowColor = PAL.hud; g.shadowBlur = 8; const c = 10;
  g.beginPath(); g.moveTo(x + c, y); g.lineTo(x, y); g.lineTo(x, y + bh); g.lineTo(x + c, y + bh);
  g.moveTo(x + bw - c, y); g.lineTo(x + bw, y); g.lineTo(x + bw, y + bh); g.lineTo(x + bw - c, y + bh); g.stroke();
  g.font = '12px HUDMono'; g.letterSpacing = '4px'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = PAL.hud;
  g.fillText('DIRECTIVE', W / 2 + 2, y + 13);
  // waveform: 40 bars, mirrored
  const n = 40, cy = y + 36, ww = bw - 40, st = ww / n;
  g.shadowBlur = 6; g.fillStyle = PAL.hud;
  for (let i = 0; i < n; i++) { const u = i / (n - 1), env = Math.sin(u * Math.PI);
    const amp = 1.5 + act * env * (3 + 11 * Math.abs(noise1(i * 0.7 + t * 14, 3) + 0.4 * noise1(i * 1.9 - t * 21, 8)));
    g.fillRect(x + 20 + i * st, cy - amp, st * 0.55, amp * 2); }
  g.restore();
}
