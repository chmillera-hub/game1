// Character reference sheets: locked designs + expression range
const C = require('./core'); const fs = require('fs');
const V = (b, o) => Object.assign({}, C.CH[b], o);
const cast = [['noa', 'NOA'], ['teo', 'TEO'], ['ami', 'AMI'], ['davidY', 'DAVID (young)'], ['davidK', 'DAVID (king)'], ['davidO', 'DAVID (old)'], ['saul', 'SAUL'], ['jonathan', 'JONATHAN'], ['abigail', 'ABIGAIL'], ['uriah', 'URIAH'], ['solC', 'SOLOMON (child)'], ['sol', 'SOLOMON (king)'], ['solO', 'SOLOMON (old)'], ['jesus', 'JESUS'], ['peter', 'PETER'], ['rich', 'RICH YOUNG MAN'], ['leper', 'LEPER'], ['disc1', 'DISCIPLE A'], ['disc2', 'DISCIPLE B']];
let cv = C.createCanvas(1500, 1650), g = cv.getContext('2d');
g.fillStyle = '#ece6da'; g.fillRect(0, 0, 1500, 1650);
cast.forEach(([k, n], i) => { const x = 150 + (i % 5) * 300, y = 120 + Math.floor(i / 5) * 400; C.drawChar(g, C.CH[k], { x, y, s: 42, t: 0.5, seed: 1, ex: C.ex('neutral') }); g.fillStyle = '#222'; g.font = '22px InterB'; g.textAlign = 'center'; g.fillText(n, x, y + 260); });
fs.writeFileSync('prod/cast_lineup.png', cv.toBuffer('image/png'));
const exs = ['neutral', 'happy', 'joy', 'sad', 'grief', 'angry', 'cold', 'worried', 'surprised', 'tender', 'hollow', 'pleading', 'teary', 'jealous'];
const who = ['noa', 'teo', 'davidK', 'solO', 'jesus'];
cv = C.createCanvas(exs.length * 140, who.length * 170 + 40); g = cv.getContext('2d');
g.fillStyle = '#ece6da'; g.fillRect(0, 0, cv.width, cv.height);
exs.forEach((e, i) => { g.fillStyle = '#222'; g.font = '18px InterB'; g.textAlign = 'center'; g.fillText(e, 70 + i * 140, 26); });
who.forEach((k, j) => exs.forEach((e, i) => { g.save(); g.beginPath(); g.rect(i * 140, 40 + j * 170, 140, 170); g.clip(); C.drawChar(g, C.CH[k], { x: 70 + i * 140, y: 130 + j * 170, s: 50, t: 0.5, seed: 1, half: true, ex: C.resolve(e) }); g.restore(); }));
fs.writeFileSync('prod/expression_sheet.png', cv.toBuffer('image/png'));
