'use strict';
// Sparrow choreography: fly in along an arc, land, hop, peck, look around,
// and (optionally) take off again. Stateless in t.

const { clamp, lerp, smooth, rng, fbm } = require('./util');
const { sparrow } = require('./sets_day');

// spec: {land: t, from:[x,y], to:[x,y], size, flip, leave?: t, leaveTo:[x,y], seed}
function birdState(b, t) {
  const fly = 1.1;
  if (t < b.land - fly) return null;
  if (t < b.land) {
    const u = (t - (b.land - fly)) / fly;
    const e = smooth(u);
    const x = lerp(b.from[0], b.to[0], e);
    const y = lerp(b.from[1], b.to[1], e) - Math.sin(e * Math.PI) * 120;
    return { x, y, flap: t * 34, flying: true, flip: b.to[0] < b.from[0] };
  }
  if (b.leave !== undefined && t >= b.leave) {
    const u = (t - b.leave) / 1.4;
    if (u > 1) return null;
    const e = u * u;
    return { x: lerp(b.to[0], b.leaveTo[0], e), y: lerp(b.to[1], b.leaveTo[1], e) - Math.sin(u * Math.PI) * 80, flap: t * 36, flying: true, flip: b.leaveTo[0] < b.to[0] };
  }
  // on the ground: hops and pecks driven by seeded schedules
  const r = rng(b.seed || 1);
  let x = b.to[0], hop = 0, peck = 0;
  const dt = t - b.land;
  for (let k = 0; k < 12; k++) {
    const th = 0.8 + k * 1.3 + r() * 0.8;
    const dx = (r() - 0.5) * 60;
    if (dt > th + 0.25) x += dx;
    else if (dt > th) { x += dx * ((dt - th) / 0.25); hop = (dt - th) / 0.25; }
    const tp = th + 0.6;
    if (dt > tp && dt < tp + 0.35) peck = Math.sin(((dt - tp) / 0.35) * Math.PI);
  }
  const look = fbm(t * 0.9, b.seed || 1) * 1.5;
  return { x, y: b.to[1] + peck * 10, hop, look: peck ? 1.2 : look, flip: b.flip, flying: false, peck };
}

function drawBird(ctx, b, t) {
  const st = birdState(b, t);
  if (!st) return;
  ctx.save();
  if (st.peck) { ctx.translate(st.x, st.y); ctx.rotate((st.flip ? -1 : 1) * 0.35 * st.peck); ctx.translate(-st.x, -st.y); }
  sparrow(ctx, st.x, st.y, b.size, { hop: st.hop, look: st.look, flip: st.flip, flap: st.flying ? st.flap : null, flying: st.flying });
  ctx.restore();
}

module.exports = { birdState, drawBird };
