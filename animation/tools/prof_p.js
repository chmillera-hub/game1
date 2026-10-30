const { createCanvas } = require('@napi-rs/canvas');
const P = require('../src/bg/porch.js');
const cv = createCanvas(1080, 1920), ctx = cv.getContext('2d');
P.drawBack(ctx,0,{});
function T(name, cam, f){ const run=()=>{ctx.setTransform(1,0,0,1,0,0);ctx.translate(540,960);ctx.scale(cam.zoom,cam.zoom);ctx.translate(-cam.x,-cam.y);f();ctx.getImageData(0,0,1,1);};
 run(); let t0=process.hrtime.bigint(); for(let i=0;i<10;i++)run(); console.log(name, cam.zoom, (Number(process.hrtime.bigint()-t0)/10e6).toFixed(1)); }
for (const cam of [{x:700,y:1100,zoom:0.75},{x:735,y:1100,zoom:3}]) {
  for (const d of [0,0.6]) T('back d'+d, cam, ()=>P.drawBack(ctx,1,{doorOpen:d}));
  T('front', cam, ()=>P.drawFront(ctx,1,{}));
}
