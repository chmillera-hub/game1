const { createCanvas } = require('@napi-rs/canvas');
const cv = createCanvas(1080, 1920), ctx = cv.getContext('2d');
const big = createCanvas(2750,3375); big.getContext('2d').fillStyle='#888'; big.getContext('2d').fillRect(0,0,2750,3375);
function T(name, zoom, f){ const run=()=>{ctx.setTransform(1,0,0,1,0,0);ctx.translate(540,960);ctx.scale(zoom,zoom);ctx.translate(-430,-1000);f();ctx.getImageData(0,0,1,1);};
 run(); let t0=process.hrtime.bigint(); for(let i=0;i<8;i++)run(); console.log(name, zoom, (Number(process.hrtime.bigint()-t0)/8e6).toFixed(1)); }
for (const z of [0.75,3]) {
T('blit', z, ()=>ctx.drawImage(big,-300,-400,2200,2700));
T('blit alpha', z, ()=>{ctx.globalAlpha=0.5;ctx.drawImage(big,-300,-400,2200,2700);ctx.globalAlpha=1});
T('evenodd mult', z, ()=>{ctx.save();ctx.beginPath();ctx.rect(-310,-410,2220,2720);ctx.rect(144,384,229,288);ctx.clip('evenodd');ctx.globalCompositeOperation='multiply';ctx.fillStyle='#eee';ctx.fillRect(-310,-410,2220,2720);ctx.restore();});
T('mult', z, ()=>{ctx.save();ctx.globalCompositeOperation='multiply';ctx.fillStyle='#eee';ctx.fillRect(-310,-410,2220,2720);ctx.restore();});
T('screen glow', z, ()=>{ctx.save();ctx.globalCompositeOperation='screen';const g=ctx.createRadialGradient(380,760,0,380,760,620);g.addColorStop(0,'rgba(255,200,100,.3)');g.addColorStop(1,'rgba(255,200,100,0)');ctx.fillStyle=g;ctx.fillRect(-240,140,1240,1240);ctx.restore();});
}
