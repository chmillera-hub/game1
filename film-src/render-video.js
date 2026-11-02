// Export the film to a YouTube-ready MP4.
// usage: node render-video.js <html> <outdir> [--fps 30] [--workers 3] [--w 1920] [--h 1080] [--from 0] [--to dur] [--name film] [--noaudio]
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');

const args = process.argv.slice(2);
const html = path.resolve(args[0]), out = path.resolve(args[1]);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const FPS = +opt('fps', 30), WORKERS = +opt('workers', 3), W = +opt('w', 1920), H = +opt('h', 1080);
const NAME = opt('name', 'film'), NOAUDIO = args.includes('--noaudio');
fs.mkdirSync(out, { recursive: true });

async function openPage() {
  const b = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb'] });
  const p = await b.newPage({ viewport: { width: Math.min(W, 1920), height: Math.min(H, 1920) }, deviceScaleFactor: 1 });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + html + '#render');
  await p.waitForFunction(() => window.__render);
  await p.evaluate(() => window.__render.fonts());
  await p.evaluate(([w, h]) => window.__render.setSize(w, h), [W, H]);
  return { b, p, errs };
}

async function renderSegment(k, f0, f1) {
  const { b, p, errs } = await openPage();
  const file = path.join(out, `seg_${String(k).padStart(2, '0')}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-vcodec', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', '10M', '-bufsize', '20M', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-r', String(FPS), '-g', String(FPS * 2), file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  // warm-up frame so lazily-built caches (sprites, plants) exist
  await p.evaluate(([t]) => window.__render.frame(t, 0, 30, 0), [f0 / FPS]);
  for (let f = f0; f < f1; f++) {
    const url = await p.evaluate(([t, i, fps]) => window.__render.frame(t, i, fps, 0.94), [f / FPS, f, FPS]);
    const buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 150 === 0) console.log(`[w${k}] frame ${f - f0}/${f1 - f0}  ${((Date.now() - t0) / Math.max(1, f - f0)).toFixed(0)}ms/frame`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log(`[w${k}] done ${f1 - f0} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s (${((Date.now() - t0) / (f1 - f0)).toFixed(0)}ms/frame)`);
  await b.close();
  if (errs.length) console.log(`[w${k}] page errors:`, errs.slice(0, 5));
  return file;
}

async function renderAudio() {
  const { b, p, errs } = await openPage();
  const info = await p.evaluate(() => window.__render.audio());
  console.log('[audio]', info);
  const parts = [];
  for (let i = 0; i < info.chunks; i++) parts.push(Buffer.from(await p.evaluate(i => window.__render.audioChunk(i), i), 'base64'));
  const file = path.join(out, 'score.wav');
  fs.writeFileSync(file, Buffer.concat(parts));
  await b.close();
  if (errs.length) console.log('[audio] page errors:', errs.slice(0, 5));
  return file;
}

(async () => {
  const probe = await openPage();
  const dur = await probe.p.evaluate(() => window.__render.duration);
  await probe.b.close();
  const from = +opt('from', 0), to = +opt('to', dur);
  const F0 = Math.round(from * FPS), F1 = Math.round(to * FPS);
  console.log(`rendering ${F1 - F0} frames @${FPS}fps ${W}x${H} with ${WORKERS} workers (t=${from}..${to}s)`);
  const per = Math.ceil((F1 - F0) / WORKERS);
  const jobs = [];
  for (let k = 0; k < WORKERS; k++) {
    const a = F0 + k * per, b = Math.min(F1, a + per);
    if (a < b) jobs.push(renderSegment(k, a, b));
  }
  const audioJob = NOAUDIO ? Promise.resolve(null) : renderAudio();
  const segs = await Promise.all(jobs);
  const wav = await audioJob;
  const list = path.join(out, 'segments.txt');
  fs.writeFileSync(list, segs.map(s => `file '${s}'`).join('\n'));
  const final = path.join(out, `${NAME}.mp4`);
  const len = (to - from);
  const a = ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list];
  if (wav) {
    // master for YouTube: measure integrated loudness, then high-pass, gain to about -15 LUFS, true-peak limit, fade out under the picture fade
    let I = null;
    try { const err = require('child_process').spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-ss', String(from), '-t', String(len), '-i', wav, '-af', 'highpass=f=30:poles=2,equalizer=f=38:t=q:w=0.8:g=-5,acompressor=threshold=-26dB:ratio=2.5:attack=15:release=250:knee=6:makeup=1,ebur128', '-f', 'null', '-'], { encoding: 'utf8' }).stderr; const m = [...err.matchAll(/I:\s+(-?[\d.]+) LUFS/g)]; if (m.length) I = parseFloat(m[m.length - 1][1]); } catch (e) { }
    const gain = I == null ? 10 : Math.max(-6, Math.min(14, -15 - I));
    console.log(`[master] measured ${I} LUFS -> gain ${gain.toFixed(2)} dB`);
    const af = `highpass=f=30:poles=2,equalizer=f=38:t=q:w=0.8:g=-5,acompressor=threshold=-26dB:ratio=2.5:attack=15:release=250:knee=6:makeup=1,volume=${gain.toFixed(2)}dB,alimiter=limit=0.75:attack=4:release=80:level=false:asc=1,afade=t=out:st=${(len - 2.6).toFixed(2)}:d=2.5`;
    a.push('-ss', String(from), '-t', String(len), '-i', wav, '-map', '0:v', '-map', '1:a', '-af', af, '-c:a', 'aac', '-b:a', '320k', '-ar', '48000');
  }
  a.push('-c:v', 'copy', '-t', String(len), '-movflags', '+faststart', final);
  execFileSync('ffmpeg', a, { stdio: 'inherit' });
  console.log('done ->', final);
})();
