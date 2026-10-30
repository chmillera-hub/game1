const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const C = require('./lib/chars');
const { drawCharacter, armsFor } = require('./lib/rig');
const { exprParams } = require('./lib/expr');
const which = process.argv[2] || 'human';
const ch = C[which.toUpperCase()];
const W = 1440, H = 1600;
const cv = createCanvas(W, H); const ctx = cv.getContext('2d');
ctx.fillStyle = '#20263a'; ctx.fillRect(0, 0, W, H);
const exprs = ['neutral','warm','smile','sad','grief','worried','awe','thoughtful','determined','surprised','tender','exhausted'];
const gestures = ['idle','open_palm','hand_chest','chin','both_palms','reach','clasp','hold_orb','wipe_tear','hands_together','shrug','fist'];
const light = { keyX: -0.6, rim: [140, 220, 255], rimX: 1, rimA: 0.6, amb: [40, 50, 90], ambA: 0.08 };
exprs.forEach((ex, i) => {
  const col = i % 4, row = Math.floor(i / 4);
  const x = 180 + col * 360, y = 330 + row * 520;
  const yaw = [0.55, -0.55, 0, 0.3][col];
  drawCharacter(ctx, ch, { x, y, s: 150, yaw, e: exprParams(ex, 1), gaze: { x: yaw > 0 ? 0.5 : yaw < 0 ? -0.5 : 0, y: 0 }, blink: 0,
    arms: armsFor(gestures[i], yaw >= 0 ? 1 : -1), light, t: 1, mouth: i === 9 ? { open: 0.5, wide: 0.3, round: 0, teeth: 0.5 } : null, tear: ex === 'grief' ? 0.5 : 0 });
  ctx.fillStyle = '#fff'; ctx.font = '22px sans-serif'; ctx.fillText(ex + ' / ' + gestures[i], x - 140, y + 230);
});
fs.writeFileSync(`../build/test/rig_${which}.png`, cv.toBuffer('image/png'));
console.log('ok');
// close-up sheet
{
  const cv2 = createCanvas(1400, 760); const c2 = cv2.getContext('2d');
  c2.fillStyle = '#20263a'; c2.fillRect(0, 0, 1400, 760);
  [['neutral',0.5],['smile',-0.5],['grief',0.25],['surprised',0]].forEach(([ex,yaw],i)=>{
    drawCharacter(c2, ch, { x: 180 + i*345, y: 610, s: 330, yaw, e: exprParams(ex,1), gaze:{x:yaw,y:0}, light, t:1, arms: armsFor('idle', yaw>=0?1:-1), mouth: ex==='surprised'?{open:0.4,wide:0.2,round:0.3,teeth:0.5}:null, tear: ex==='grief'?0.55:0 });
  });
  fs.writeFileSync(`../build/test/rigcu_${which}.png`, cv2.toBuffer('image/png'));
}
