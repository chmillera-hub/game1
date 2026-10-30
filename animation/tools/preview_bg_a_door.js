// close-up check of the door hinge side at several openings
const path = require('path'); const fs = require('fs');
const { createCanvas } = require('@napi-rs/canvas');
const P = require('../src/bg/porch.js');
for (const d of [0.9, 1]) {
  const cv = createCanvas(540, 960), ctx = cv.getContext('2d');
  ctx.scale(0.5, 0.5); ctx.translate(540, 960); ctx.scale(4, 4); ctx.translate(-480, -1000);
  P.drawBack(ctx, 0, { doorOpen: d }); P.drawFront(ctx, 0, {});
  fs.writeFileSync(path.join(__dirname, '../build/preview/p_hinge_' + d + '.png'), cv.toBuffer('image/png'));
}
