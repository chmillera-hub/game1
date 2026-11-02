// evaluate the film module just enough to extract narration timing
import fs from 'fs';
const src = fs.readFileSync(process.argv[2], 'utf8');
const s = src.indexOf('const DUR'), e = src.indexOf('// ------------------------------------------------------------------ cast');
const code = src.slice(s, e) + '\nreturn narration;';
const narration = new Function(code)();
const out = narration.map((n, i) => ({ i, t: +n.t.toFixed(3), win: +((narration[i+1]?.t ?? n.t + 8) - n.t).toFixed(2), d: +n.d.toFixed(2), text: n.text }));
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
for (const o of out) console.log(String(o.i).padStart(2), o.t.toFixed(2).padStart(7), o.win.toFixed(2).padStart(6), o.text.length.toString().padStart(4), (o.text.length/o.win).toFixed(1).padStart(5), o.text.slice(0, 60));
