/* Render every sound effect and a stretch of each music track offline in
   Chromium and report their levels, so nothing is silent, clipped or far
   louder than the rest. node tools/audio-check.js [out.wav-dir] */
'use strict';
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const outDir = process.argv[2] || null;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  // Swap the live audio context for an offline one we can render.
  await page.addInitScript(() => {
    window.AudioContext = function () { return (window.__offline = new OfflineAudioContext(2, 44100 * 60, 44100)); };
  });
  await page.goto('file://' + path.join(__dirname, '..', 'index.html'));
  await page.waitForTimeout(500);
  const res = await page.evaluate(async () => {
    const S = AG.UI.Sound;
    const stats = (buf, a, b) => {
      const L = buf.getChannelData(0), R = buf.getChannelData(1);
      let peak = 0, sum = 0, n = 0;
      for (let i = Math.floor(a * buf.sampleRate); i < Math.min(L.length, Math.floor(b * buf.sampleRate)); i++) {
        const v = Math.max(Math.abs(L[i]), Math.abs(R[i]));
        peak = Math.max(peak, v);
        sum += L[i] * L[i];
        n++;
      }
      return { peak: +peak.toFixed(3), rms: +Math.sqrt(sum / Math.max(1, n)).toFixed(4) };
    };
    // 1. Every effect, one second apart.
    window.dispatchEvent(new Event('pointerdown'));
    const names = ['click', 'place', 'pickup', 'remove', 'deploy', 'walk', 'slide', 'leap', 'blink', 'slash', 'smash', 'arrow', 'bolt', 'fire', 'frost', 'lightning', 'beam', 'boom', 'holy', 'shadow', 'nature', 'goo', 'rally', 'hit', 'death', 'heal', 'shield', 'summon', 'promote', 'status', 'round', 'storm', 'negate', 'coin', 'relic', 'victory', 'defeat', 'error'];
    names.forEach((n, i) => S.fx(n, 6, i * 1.2));
    const fxBuf = await window.__offline.startRendering();
    const fx = names.map((n, i) => Object.assign({ name: n }, stats(fxBuf, i * 1.2, i * 1.2 + 1.15)));
    return { fx, rate: fxBuf.sampleRate };
  });
  const tracks = await page.evaluate(() => AG.UI.Sound.TRACKS);
  const music = [];
  for (const t of tracks) {
    const p2 = await browser.newPage();
    p2.on('pageerror', (e) => errors.push(e.message));
    await p2.addInitScript(() => {
      window.AudioContext = function () { return (window.__offline = new OfflineAudioContext(2, 44100 * 14, 44100)); };
    });
    await p2.goto('file://' + path.join(__dirname, '..', 'index.html'));
    await p2.waitForTimeout(300);
    music.push(await p2.evaluate(async (name) => {
      window.dispatchEvent(new Event('pointerdown'));
      const S = AG.UI.Sound;
      S.music(name);
      S.prime(13);
      const buf = await window.__offline.startRendering();
      const L = buf.getChannelData(0);
      let peak = 0, sum = 0;
      for (let i = buf.sampleRate * 2; i < L.length; i++) { peak = Math.max(peak, Math.abs(L[i])); sum += L[i] * L[i]; }
      return { name, peak: +peak.toFixed(3), rms: +Math.sqrt(sum / (L.length - buf.sampleRate * 2)).toFixed(4) };
    }, t));
    await p2.close();
  }
  await browser.close();
  console.log('effects (peak / rms):');
  for (const f of res.fx) console.log('  ' + f.name.padEnd(10) + String(f.peak).padStart(7) + String(f.rms).padStart(9) + (f.rms < 0.002 ? '  QUIET' : '') + (f.peak > 0.95 ? '  CLIPS' : ''));
  console.log('music (peak / rms):');
  for (const m of music) console.log('  ' + m.name.padEnd(10) + String(m.peak).padStart(7) + String(m.rms).padStart(9) + (m.rms < 0.005 ? '  QUIET' : '') + (m.peak > 0.95 ? '  CLIPS' : ''));
  if (errors.length) { console.log('ERRORS:\n' + errors.join('\n')); process.exit(1); }
  if (outDir) fs.mkdirSync(outDir, { recursive: true });
})().catch((e) => { console.error(e); process.exit(1); });
