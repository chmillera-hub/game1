// Logs the shot active on every frame -> shots.json (frame-accurate shot list source)
const C = require('./core'); const TL = require('./timeline.json'); const { SC } = require('./render');
const SCENES = require('./scenes2'); const FPS = TL.fps;
const cv = C.createCanvas(72, 128), g = cv.getContext('2d');
const N = Math.ceil(TL.duration * FPS); const segs = [];
for (let f = 0; f < N; f++) {
  const t = f / FPS; let i = SC.findIndex(s => t < s.sc.end); if (i < 0) i = SC.length - 1;
  const { sc, S } = SC[i]; globalThis.__shot = sc.id;
  g.save(); g.scale(0.1, 0.1); SCENES[sc.id](g, t - sc.start, S); g.restore();
  const key = sc.id + ':' + globalThis.__shot; const last = segs[segs.length - 1];
  if (last && last.key === key) last.f1 = f; else segs.push({ key, scene: sc.id, shot: globalThis.__shot, f0: f, f1: f });
}
require('fs').writeFileSync('shots.json', JSON.stringify(segs, null, 1));
console.log(segs.length, 'shots,', N, 'frames');
