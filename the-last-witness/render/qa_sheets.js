// Renders QA contact sheets: one still per distinct vignette + a spread of character shots.
'use strict';
const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('@napi-rs/canvas');
const { renderFrame, segments } = require('./render');
const outDir = path.join(__dirname, '..', 'build', 'qa');
fs.mkdirSync(outDir, { recursive: true });
const picks = [];
const seenV = new Set();
for (const s of segments) {
  if (s.vignette && !seenV.has(s.vignette + JSON.stringify(s.vparams))) { seenV.add(s.vignette + JSON.stringify(s.vparams)); picks.push({ t: s.start + 0.45 * (s.end - s.start), what: `${s.shot} / ${s.vignette}` }); }
}
const charSegs = segments.filter((s) => !s.vignette);
const want = 50;
for (let i = 0; i < want; i++) {
  const s = charSegs[Math.floor((i + 0.5) * charSegs.length / want)];
  picks.push({ t: s.start + 0.5 * (s.end - s.start), what: s.shot });
}
picks.sort((a, b) => a.t - b.t);
const per = 6, cw = 360, chh = 640;
const index = [];
for (let k = 0; k * per < picks.length; k++) {
  const sheet = createCanvas(cw * 3, chh * 2 + 0);
  const sc = sheet.getContext('2d');
  picks.slice(k * per, k * per + per).forEach((p, i) => {
    const frame = renderFrame(p.t);
    sc.drawImage(frame, (i % 3) * cw, Math.floor(i / 3) * chh, cw, chh);
    sc.fillStyle = 'rgba(0,0,0,0.7)'; sc.fillRect((i % 3) * cw, Math.floor(i / 3) * chh, cw, 26);
    sc.fillStyle = '#ff0'; sc.font = '16px sans-serif';
    sc.fillText(`#${i + 1} t=${p.t.toFixed(1)} ${p.what}`, (i % 3) * cw + 6, Math.floor(i / 3) * chh + 18);
    index.push({ sheet: k, cell: i + 1, ...p });
  });
  fs.writeFileSync(path.join(outDir, `sheet_${String(k).padStart(2, '0')}.png`), sheet.toBuffer('image/png'));
}
fs.writeFileSync(path.join(outDir, 'index.json'), JSON.stringify(index, null, 1));
console.log(picks.length, 'stills', Math.ceil(picks.length / per), 'sheets');
