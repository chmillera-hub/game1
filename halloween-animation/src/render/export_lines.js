const { cast, items } = require('./script.js');
const out = [];
items.forEach((it, i) => { if (it.type === 'line') out.push({ idx: i, who: it.who, text: it.text, speed: it.speed ?? cast[it.who].speed, pitch: it.pitch ?? cast[it.who].pitch, voice: cast[it.who].voice, fx: cast[it.who].fx }); });
require('fs').writeFileSync('../work/lines_in.json', JSON.stringify(out, null, 1));
console.log(out.length, 'lines');
