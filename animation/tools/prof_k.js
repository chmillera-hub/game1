const { createCanvas } = require('@napi-rs/canvas');
const K = require('../src/bg/kitchen.js');
const cv = createCanvas(1080, 1920), ctx = cv.getContext('2d');
K.drawBack(ctx,0,{});
function T(name, cam, f){ const run=()=>{ctx.setTransform(1,0,0,1,0,0);ctx.translate(540,960);ctx.scale(cam.zoom,cam.zoom);ctx.translate(-cam.x,-cam.y);f();ctx.getImageData(0,0,1,1);};
 run(); let t0=process.hrtime.bigint(); for(let i=0;i<8;i++)run(); console.log(name, cam.zoom, (Number(process.hrtime.bigint()-t0)/8e6).toFixed(1)); }
for (const cam of [{x:800,y:950,zoom:0.75},{x:430,y:1000,zoom:3}]) {
  T('back', cam, ()=>K.drawBack(ctx,1,{}));
  T('front', cam, ()=>K.drawFront(ctx,1,{}));
  T('nothing', cam, ()=>{});
  T('fill', cam, ()=>{ctx.fillStyle='#888';ctx.fillRect(-300,-400,2200,2700)});
}
