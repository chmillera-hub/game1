// Lists every spoken line in who-saves-the-hero.html as JSON, for tools/build-voices.py.
// Usage: node tools/extract-lines.js > tools/lines.json   (needs Playwright)
const path=require('path');
let pw;try{pw=require('playwright');}catch(e){pw=require('/opt/node22/lib/node_modules/playwright');}
(async()=>{
  const b=await pw.chromium.launch();const pg=await b.newPage();
  await pg.goto('file://'+path.resolve(__dirname,'..','who-saves-the-hero.html'));
  const lines=await pg.evaluate(()=>{const out=[];window.__film.PARTS.forEach((p,pi)=>p.shots.forEach((sh,si)=>sh.lines.forEach((l,li)=>{if(l.t&&l.s)out.push({part:pi+1,shot:si,line:li,speaker:l.s,text:l.t,key:window.__film.vkey(l)});})));return out;});
  process.stdout.write(JSON.stringify(lines,null,1));await b.close();
})();
