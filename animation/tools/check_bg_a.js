// determinism + lightAt sanity for kitchen/porch
const { createCanvas } = require('@napi-rs/canvas');
const crypto = require('crypto');
for (const name of ['kitchen', 'porch']) {
  const M = require('../src/bg/' + name + '.js');
  const h = (o, t) => { const cv = createCanvas(270, 480), ctx = cv.getContext('2d'); ctx.scale(0.25, 0.25); ctx.translate(540, 960); ctx.scale(0.8, 0.8); ctx.translate(-700, -1000);
    M.drawBack(ctx, t, o); M.drawFront(ctx, t, o); return crypto.createHash('md5').update(cv.toBuffer('image/png')).digest('hex'); };
  const o = name === 'kitchen' ? { dusk: 0.37, lamp: 0.8 } : { doorOpen: 0.42 };
  console.log(name, h(o, 5.5), h(o, 5.5), h(name === 'kitchen' ? {} : { doorOpen: 0 }, 5.5));
  for (const [k, a] of Object.entries(M.ENV.anchors)) {
    const L = M.lightAt(a.x, a.y, 1, o);
    const bad = Object.entries(L).filter(([kk, v]) => (typeof v === 'number' && !isFinite(v)) || (typeof v === 'string' && !/^#[0-9a-f]{6}$/.test(v)));
    if (bad.length) console.log('BAD', k, bad);
  }
  console.log(JSON.stringify(M.lightAt(M.ENV.anchors[name === 'kitchen' ? 'eliLean' : 'mayaAtDoor'].x, M.ENV.anchors[name === 'kitchen' ? 'eliLean' : 'mayaAtDoor'].y, 0, name === 'kitchen' ? {} : { doorOpen: 1 })));
}
