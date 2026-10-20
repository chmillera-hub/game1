// Contact sheet for review:  node render/sheet.mjs s01a s01b --n 6 --out tests/sheet.png [--scale 0.42]
// Also accepts explicit times: node render/sheet.mjs s01a@0.5 s01a@3.2 --out tests/x.png
// Each tile is labelled with shot id, local time, and the line being spoken at that moment.
import fs from 'fs';
import path from 'path';
import { createCanvas } from '@napi-rs/canvas';
import { W, H } from './lib/core.mjs';
import { shotById, makeCtx, ROOT_DIR } from './lib/timeline.mjs';
import { drawFrameAt } from './lib/frame.mjs';

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const N = Number(opt('n', 6)), scale = Number(opt('scale', 0.42)), out = path.resolve(ROOT_DIR, opt('out', 'tests/sheet.png'));
const specs = argv.filter((a, i) => !a.startsWith('--') && !(argv[i - 1] || '').startsWith('--'));

const frames = [];
for (const s of specs) {
  if (s.includes('@')) { const [id, t] = s.split('@'); frames.push([shotById(id), Number(t)]); continue; }
  const shot = shotById(s); if (!shot) throw new Error('no shot ' + s);
  for (let i = 0; i < N; i++) frames.push([shot, (i + 0.5) / N * shot.dur]);
}
const tw = Math.round(W * scale), th = Math.round(H * scale), cols = Math.min(frames.length, 6);
const rows = Math.ceil(frames.length / cols), lab = 54;
const sheet = createCanvas(cols * tw, rows * (th + lab)); const sg = sheet.getContext('2d');
sg.fillStyle = '#111'; sg.fillRect(0, 0, sheet.width, sheet.height);
const cv = createCanvas(W, H); const g = cv.getContext('2d');
frames.forEach(([shot, t], k) => {
  drawFrameAt(g, shot, t);
  const x = (k % cols) * tw, y = Math.floor(k / cols) * (th + lab);
  sg.drawImage(cv, x, y, tw, th);
  const ctx = makeCtx(shot); const l = ctx.lines.find(l => t >= l.start && t <= l.end);
  sg.fillStyle = '#ddd'; sg.font = '13px UISans';
  sg.fillText(`${shot.id} t=${t.toFixed(2)}/${shot.dur.toFixed(1)}`, x + 4, y + th + 15);
  if (l) { sg.fillStyle = '#9cf'; const s = `${l.speaker}: ${l.text}`;
    sg.fillText(s.slice(0, 44), x + 4, y + th + 31); if (s.length > 44) sg.fillText(s.slice(44, 88), x + 4, y + th + 47); }
});
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, await sheet.encode('png')); console.log(out);
