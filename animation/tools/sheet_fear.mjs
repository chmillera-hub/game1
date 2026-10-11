import { createCanvas } from '@napi-rs/canvas';
import fs from 'fs';
import { drawFear } from '../src/chars/fear.mjs';
import { EXPR } from '../src/face.mjs';
const cells = [
  ['neutral', {}, {}], ['worried', EXPR.worried, {armL:'wringHands', armR:'wringHands'}], ['scared', EXPR.scared, {tremble:.6, armL:'hugSelf', armR:'hugSelf'}],
  ['terrified', EXPR.terrified, {tremble:1, crouch:.5, armL:'coverMouth'}], ['crying', {...EXPR.crying, tearL:.5}, {headTilt:-.1}], ['sad', EXPR.sad, {headTilt:.12}],
  ['wonder', {...EXPR.wonder, t:3}, {headTilt:-.08, headDY:-4}], ['softSmile', {...EXPR.softSmile, tears:.6}, {}], ['handsOnFace', EXPR.terrified, {armL:'handsOnFace', armR:'handsOnFace', crouch:.6, tremble:.7}],
  ['peek', {...EXPR.scared, lookY:-.6}, {armL:'peek', armR:'handsOnFace', crouch:.4}], ['look left turn', {...EXPR.suspicious, lookX:-.8}, {headTurn:-.6}], ['pull alarm', {...EXPR.terrified, lookX:.7}, {armR:'reachUp', lean:.1}],
];
const cw=360, ch=420, cols=3, rows=Math.ceil(cells.length/cols);
const c=createCanvas(cw*cols, ch*rows), g=c.getContext('2d');
g.fillStyle='#2b2440'; g.fillRect(0,0,c.width,c.height);
cells.forEach(([name, face, pose], i)=>{
  const x=(i%cols)*cw, y=Math.floor(i/cols)*ch;
  g.fillStyle=(i%2)?'#342b4f':'#30284a'; g.fillRect(x,y,cw,ch);
  drawFear(g, x+cw/2, y+ch-30, 1.08, {t:1.3+i*0.37, face:{...face, noAutoBlink:true}, ...pose});
  g.fillStyle='#fff'; g.font='20px sans-serif'; g.fillText(name, x+10, y+26);
});
fs.writeFileSync(process.argv[2]||'out/sheet_fear.png', c.toBuffer('image/png'));
