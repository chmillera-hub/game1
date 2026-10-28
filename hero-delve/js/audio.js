// Small synthesized sound effects (no audio files). Starts after the first user gesture.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const KEY = 'arena-gauntlet-sound';

  let ctx = null;
  let master = null;
  let noiseBuf = null;
  let enabled = true;
  try {
    enabled = root.localStorage.getItem(KEY) !== 'off';
  } catch (e) {
    enabled = true;
  }

  function ensure() {
    if (ctx) {
      if (ctx.state === 'suspended') ctx.resume();
      return true;
    }
    const AC = root.AudioContext || root.webkitAudioContext;
    if (!AC) return false;
    try {
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = 0.42;
      master.connect(ctx.destination);
      noiseBuf = ctx.createBuffer(1, ctx.sampleRate * 0.6, ctx.sampleRate);
      const d = noiseBuf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    } catch (e) {
      ctx = null;
      return false;
    }
    return true;
  }

  function tone(type, f0, f1, dur, vol, delay) {
    const t = ctx.currentTime + (delay || 0);
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f0, t);
    if (f1) o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(master);
    o.start(t);
    o.stop(t + dur + 0.02);
  }

  function noise(dur, vol, filterType, freq, delay, q) {
    const t = ctx.currentTime + (delay || 0);
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf;
    const f = ctx.createBiquadFilter();
    f.type = filterType || 'lowpass';
    f.frequency.value = freq || 1200;
    f.Q.value = q || 0.8;
    const g = ctx.createGain();
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(f).connect(g).connect(master);
    src.start(t);
    src.stop(t + dur + 0.02);
  }

  const SFX = {
    click: () => tone('triangle', 660, 520, 0.06, 0.12),
    select: () => tone('triangle', 520, 780, 0.08, 0.14),
    step: () => noise(0.06, 0.12, 'lowpass', 500),
    swing: () => noise(0.14, 0.18, 'bandpass', 1800, 0, 1.2),
    hit: () => {
      noise(0.12, 0.35, 'lowpass', 900);
      tone('square', 160, 70, 0.12, 0.12);
    },
    magichit: () => {
      tone('sine', 880, 330, 0.18, 0.12);
      noise(0.1, 0.12, 'highpass', 2500);
    },
    block: () => {
      tone('square', 1400, 900, 0.08, 0.1);
      tone('sine', 2100, 1600, 0.18, 0.08, 0.01);
    },
    bow: () => {
      tone('triangle', 300, 120, 0.12, 0.12);
      noise(0.2, 0.1, 'highpass', 3000, 0.03);
    },
    throw: () => noise(0.12, 0.12, 'highpass', 2500),
    fireball: () => noise(0.4, 0.22, 'lowpass', 700),
    boom: () => {
      noise(0.5, 0.4, 'lowpass', 400);
      tone('sine', 120, 40, 0.4, 0.25);
    },
    zap: () => {
      noise(0.25, 0.2, 'highpass', 3500);
      tone('sawtooth', 900, 200, 0.2, 0.06);
    },
    breath: () => noise(0.6, 0.28, 'bandpass', 600, 0, 0.6),
    heal: () => {
      tone('sine', 523, 0, 0.25, 0.1);
      tone('sine', 659, 0, 0.25, 0.1, 0.08);
      tone('sine', 784, 0, 0.35, 0.1, 0.16);
    },
    charm: () => {
      tone('sine', 988, 0, 0.12, 0.08);
      tone('sine', 1319, 0, 0.12, 0.08, 0.07);
      tone('sine', 1760, 0, 0.2, 0.07, 0.14);
    },
    poison: () => {
      tone('sine', 220, 330, 0.12, 0.08);
      tone('sine', 260, 180, 0.15, 0.06, 0.08);
    },
    grow: () => tone('triangle', 200, 500, 0.25, 0.1),
    slam: () => {
      noise(0.35, 0.4, 'lowpass', 250);
      tone('sine', 90, 35, 0.35, 0.3);
    },
    splash: () => {
      noise(0.45, 0.3, 'lowpass', 900);
      tone('sine', 420, 160, 0.18, 0.08, 0.05);
    },
    sizzle: () => {
      noise(0.6, 0.22, 'highpass', 2600);
      tone('sawtooth', 120, 60, 0.3, 0.06);
    },
    death: () => tone('triangle', 300, 70, 0.4, 0.12),
    horn: () => {
      tone('sawtooth', 147, 140, 0.55, 0.06);
      tone('sawtooth', 220, 210, 0.5, 0.045, 0.14);
    },
    crumble: () => noise(0.7, 0.28, 'lowpass', 380),
    turn: () => {
      tone('triangle', 392, 0, 0.12, 0.1);
      tone('triangle', 523, 0, 0.18, 0.1, 0.1);
    },
    enemyturn: () => {
      tone('triangle', 330, 0, 0.12, 0.1);
      tone('triangle', 262, 0, 0.2, 0.1, 0.1);
    },
    coin: () => {
      tone('square', 1320, 0, 0.06, 0.06);
      tone('square', 1760, 0, 0.12, 0.06, 0.06);
    },
    levelup: () => [659, 784, 988, 1319].forEach((f, i) => tone('triangle', f, 0, 0.18, 0.11, i * 0.07)),
    victory: () => [523, 659, 784, 1047].forEach((f, i) => tone('triangle', f, 0, 0.3, 0.12, i * 0.12)),
    defeat: () => [392, 330, 262, 196].forEach((f, i) => tone('triangle', f, 0, 0.35, 0.12, i * 0.16)),
  };

  AG.Audio = {
    play(name) {
      if (!enabled || !ensure() || !SFX[name]) return;
      try {
        SFX[name]();
      } catch (e) {
        /* ignore audio errors */
      }
    },
    unlock() {
      if (enabled) ensure();
    },
    // The shared audio context, for the music: made now when `make` (during a tap), else
    // only if it already exists.
    context(make) {
      if (make && !ensure()) return null;
      return ctx;
    },
    get enabled() {
      return enabled;
    },
    toggle() {
      enabled = !enabled;
      try {
        root.localStorage.setItem(KEY, enabled ? 'on' : 'off');
      } catch (e) {
        /* storage unavailable */
      }
      if (enabled) ensure();
      return enabled;
    },
  };
})(typeof window !== 'undefined' ? window : globalThis);
