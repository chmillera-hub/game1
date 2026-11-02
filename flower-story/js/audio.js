/* ==========================================================================
   audio.js — the film's procedural score, ambience and sound effects.
   Global: FilmAudio
   Everything is synthesised live with the Web Audio API. No audio files.

   Signal flow
     mood bed (one per mood segment) ─┬ dry ──┐
       its own fade-in/out faders     ├ hall ─┤   shared spaces: hall + room convolvers
     sfx one-shots (own kill gains) ──┼ room ─┤   (generated impulse responses), soft echo
                                      └ echo ─┘
       → sum → DC block → glue compressor → trim → soft-knee ceiling (peak < −1 dBFS)
       → pause gain → mute gain → speakers

   The score is film-locked: a mood bed's bar grid starts where its mood segment
   starts on the film timeline, so the same note always lands on the same frame,
   and seeking lands mid-phrase deterministically. All randomness is seeded.

   The flower theme (3/4, D major) opens on scale degrees 1-2-3-5-8, the
   Fibonacci numbers: D E F# A | D' . C# B | A . F# | E . . (antecedent) and
   D E F# A | B . A G | F# . E | D . . (answer). The title states only the
   question; the answer arrives warm and full in the reflection.
   ========================================================================== */
(function (g) {
  'use strict';
  const AC = g.AudioContext || g.webkitAudioContext;
  const OAC = g.OfflineAudioContext || g.webkitOfflineAudioContext;
  const TAU = Math.PI * 2;
  const EPS = 1e-4;
  const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
  const mtof = (m) => 440 * Math.pow(2, (m - 69) / 12);
  const dB = (d) => Math.pow(10, d / 20);

  /* ---------------- mix levels (tune here; measure with FilmAudio.debug.renderMood/renderSfx/renderTimeline) ---------------- */
  const LEVEL = {
    music: 1.0,   // all mood beds
    sfx: 1.0,     // all one-shots
    hall: 0.42,   // hall reverb return
    room: 0.36,   // room reverb return
    echo: 0.34,   // echo return
    trim: 0.9,    // after the glue compressor (it adds its own make-up gain)
  };
  // per-mood bed gains (linear; +1 dB = ×1.122), set from measured K-weighted loudness so that title and reflection
  // are the fullest (≈ −17.5 LUFS in the film), the other moods sit 1–4 LU below, and silence is near-silent
  const MOOD_GAIN = {
    title: 0.58, forest: 1.02, wonder: 0.71, tender: 0.92, cosmic: 0.62, machine: 1.57, dusk: 0.72,
    comedy: 0.91, town: 1.27, shop: 1.06, parking: 0.62, reflection: 0.74, silence: 1,
  };
  const XFADE = 2.5;      // mood crossfade (seconds, centred on the cut)
  const PREROLL = 1.2;    // the next bed starts this long before its segment
  const LOOKAHEAD = 0.3;  // note scheduling horizon (seconds of audio clock)

  /* ---------------- deterministic randomness ---------------- */
  function hash() {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < arguments.length; i++) {
      const s = String(arguments[i]);
      for (let j = 0; j < s.length; j++) { h ^= s.charCodeAt(j); h = Math.imul(h, 16777619); }
      h ^= 0x9e3779b9; h = Math.imul(h ^ (h >>> 13), 2246822519);
    }
    return h >>> 0;
  }
  function Rng(seed) {
    let a = seed >>> 0 || 1;
    const r = () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    r.range = (lo, hi) => lo + (hi - lo) * r();
    r.int = (lo, hi) => Math.floor(lo + (hi - lo + 1) * r());
    r.pick = (arr) => arr[Math.floor(r() * arr.length) % arr.length];
    r.chance = (p) => r() < p;
    r.gauss = () => (r() + r() + r() - 1.5) / 1.5; // bell-shaped in [-1, 1]
    return r;
  }
  const rng = (...k) => Rng(hash(...k));

  /* ---------------- the sound kit: noise, waveforms, rooms ---------------- */
  // Seamlessly looping noise (the loop seam is crossfaded), normalised to RMS 0.25.
  function noiseBuffer(ac, seconds, color, channels, seed) {
    const sr = ac.sampleRate, n = Math.max(256, Math.floor(seconds * sr)), F = Math.floor(0.05 * sr);
    const buf = ac.createBuffer(channels, n, sr);
    for (let c = 0; c < channels; c++) {
      const R = Rng(seed * 977 + c * 131 + 7);
      const x = new Float32Array(n + F);
      let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0, last = 0;
      for (let i = 0; i < n + F; i++) {
        const w = R() * 2 - 1;
        if (color === 'pink') {
          b0 = 0.99886 * b0 + w * 0.0555179; b1 = 0.99332 * b1 + w * 0.0750759; b2 = 0.969 * b2 + w * 0.153852;
          b3 = 0.8665 * b3 + w * 0.3104856; b4 = 0.55 * b4 + w * 0.5329522; b5 = -0.7616 * b5 - w * 0.016898;
          x[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362; b6 = w * 0.115926;
        } else if (color === 'brown') { last = (last + 0.02 * w) / 1.02; x[i] = last; } else x[i] = w;
      }
      let mean = 0;
      for (let i = 0; i < n + F; i++) mean += x[i];
      mean /= n + F;
      const d = buf.getChannelData(c);
      for (let i = 0; i < n; i++) d[i] = x[i] - mean;
      for (let i = 0; i < F; i++) {
        const k = ((i + 0.5) / F) * (Math.PI / 2);
        d[i] = (x[i] - mean) * Math.sin(k) + (x[n + i] - mean) * Math.cos(k);
      }
      let ss = 0;
      for (let i = 0; i < n; i++) ss += d[i] * d[i];
      const k = 0.25 / Math.sqrt(ss / n || 1);
      for (let i = 0; i < n; i++) d[i] *= k;
    }
    return buf;
  }
  function periodic(ac, amps) {
    const n = amps.length + 1, re = new Float32Array(n), im = new Float32Array(n);
    for (let i = 1; i < n; i++) im[i] = amps[i - 1];
    return ac.createPeriodicWave(re, im);
  }
  const harm = (N, f) => Array.from({ length: N }, (_, i) => f(i + 1));
  // Stereo impulse response: pre-delay, early reflections, then a decaying noise
  // tail whose brightness falls over time (high frequencies die first).
  function impulse(ac, o) {
    const sr = ac.sampleRate, n = Math.floor(o.len * sr), pre = Math.floor(o.pre * sr);
    const buf = ac.createBuffer(2, n, sr);
    for (let c = 0; c < 2; c++) {
      const R = Rng(o.seed * 17 + c * 5 + 3), d = buf.getChannelData(c);
      let lp = 0, ss = 0;
      for (let i = pre; i < n; i++) {
        const tt = (i - pre) / sr;
        const fc = o.hf0 * Math.pow(o.hf1 / o.hf0, Math.min(1, tt / o.rt));
        const a = Math.exp((-TAU * fc) / sr);
        lp = a * lp + (1 - a) * (R() * 2 - 1);
        d[i] = lp * Math.pow(10, (-3 * tt) / o.rt);
      }
      for (const [ms, amp] of o.early) {
        const i = pre + Math.floor(((ms * (c ? 1.13 : 1)) / 1000) * sr);
        if (i < n) d[i] += amp * (R() < 0.5 ? -1 : 1) * 0.6;
      }
      const fi = Math.floor(0.002 * sr), fo = Math.floor(0.08 * sr);
      for (let i = 0; i < fi && pre + i < n; i++) d[pre + i] *= i / fi;
      for (let i = 0; i < fo; i++) d[n - 1 - i] *= i / fo;
      for (let i = 0; i < n; i++) ss += d[i] * d[i];
      const k = 1 / Math.sqrt(ss || 1);
      for (let i = 0; i < n; i++) d[i] *= k;
    }
    return buf;
  }
  function makeKit(ac) {
    const kit = { ac, sr: ac.sampleRate };
    kit.white = noiseBuffer(ac, 3, 'white', 1, 1);
    kit.whiteSt = noiseBuffer(ac, 3, 'white', 2, 2);
    kit.pinkSt = noiseBuffer(ac, 5, 'pink', 2, 3);
    kit.pink = noiseBuffer(ac, 4, 'pink', 1, 4);
    kit.brownSt = noiseBuffer(ac, 5, 'brown', 2, 5);
    kit.wave = {
      soft: periodic(ac, harm(24, (n) => 1 / Math.pow(n, 1.7))),
      string: periodic(ac, harm(32, (n) => Math.exp(-n / 18) / n)),
      reed: periodic(ac, harm(24, (n) => (n % 2 ? 1 : 0.55) / n)),
      piano: periodic(ac, [1, 0.5, 0.3, 0.17, 0.1, 0.06, 0.035, 0.02, 0.012, 0.007]),
      harp: periodic(ac, [1, 0.45, 0.22, 0.12, 0.07, 0.04, 0.025, 0.015]),
      hollow: periodic(ac, harm(15, (n) => (n % 2 ? 1 / Math.pow(n, 1.25) : 0))),
      flute: periodic(ac, [1, 0.18, 0.06, 0.025, 0.01]),
      horn: periodic(ac, [1, 0.75, 0.5, 0.32, 0.2, 0.12, 0.07, 0.04, 0.025, 0.015]),
      glass: periodic(ac, [1, 0, 0.12, 0, 0.04]),
    };
    kit.hallIR = impulse(ac, { len: 2.8, rt: 2.5, pre: 0.022, hf0: 7800, hf1: 1300, seed: 11,
      early: [[9, 0.5], [15, 0.42], [23, 0.36], [31, 0.3], [43, 0.26], [57, 0.2], [71, 0.16]] });
    kit.roomIR = impulse(ac, { len: 0.9, rt: 0.55, pre: 0.004, hf0: 6500, hf1: 2400, seed: 23,
      early: [[3, 0.6], [6, 0.5], [9, 0.42], [13, 0.34], [18, 0.26]] });
    return kit;
  }

  /* ---------------- node helpers ---------------- */
  const nyq = (ac, f) => Math.min(f, ac.sampleRate * 0.45);
  function Osc(ac, wave, f, t0, t1) {
    const o = ac.createOscillator();
    if (typeof wave === 'string') o.type = wave; else o.setPeriodicWave(wave);
    o.frequency.setValueAtTime(nyq(ac, f), t0);
    o.start(t0); o.stop(t1);
    return o;
  }
  function Gain(ac, v) { const n = ac.createGain(); n.gain.value = v == null ? 0 : v; return n; }
  function Filt(ac, type, f, q) { const n = ac.createBiquadFilter(); n.type = type; n.frequency.value = nyq(ac, f); n.Q.value = q == null ? 0.707 : q; return n; }
  function Noise(ac, buf, t0, t1, R, rate) {
    const s = ac.createBufferSource();
    s.buffer = buf; s.loop = true;
    if (rate) s.playbackRate.value = rate;
    s.start(t0, R ? R() * buf.duration * 0.9 : 0);
    s.stop(t1);
    return s;
  }
  function Pan(ac, p) {
    if (!ac.createStereoPanner) return Gain(ac, 1);
    const n = ac.createStereoPanner(); n.pan.value = clamp(p || 0, -1, 1); return n;
  }
  function chain() { for (let i = 0; i < arguments.length - 1; i++) arguments[i].connect(arguments[i + 1]); return arguments[arguments.length - 1]; }
  // Register a source with its owner (a bed or a one-shot) so it can be stopped
  // early, and disconnect its private nodes once it has finished.
  function own(owner, src, nodes) {
    owner.srcs.add(src);
    src.onended = () => {
      owner.srcs.delete(src);
      try { src.disconnect(); } catch (e) { /* already gone */ }
      if (nodes) for (const n of nodes) { try { if (typeof n === 'function') n(); else if (n) n.disconnect(); } catch (e) { /* already gone */ } }
    };
    return src;
  }
  function stopAll(owner, t) { for (const s of owner.srcs) { try { s.stop(t); } catch (e) { /* not started or already stopped */ } } }

  /* ---------------- envelopes (always ramps, never jumps) ---------------- */
  // percussive: linear attack, exponential decay to silence. returns end time
  function perc(p, t, peak, a, d) {
    peak = Math.max(2 * EPS, peak);
    p.setValueAtTime(0, t);
    p.linearRampToValueAtTime(peak, t + a);
    p.exponentialRampToValueAtTime(EPS, t + a + d);
    p.linearRampToValueAtTime(0, t + a + d + 0.01);
    return t + a + d + 0.02;
  }
  // sustained: attack, hold until t + hold, exponential release
  function sus(p, t, peak, a, hold, r) {
    peak = Math.max(2 * EPS, peak);
    const tr = t + Math.max(a + 0.001, hold);
    p.setValueAtTime(0, t);
    p.linearRampToValueAtTime(peak, t + a);
    p.setValueAtTime(peak, tr);
    p.exponentialRampToValueAtTime(EPS, tr + r);
    p.linearRampToValueAtTime(0, tr + r + 0.01);
    return tr + r + 0.02;
  }
  // a smooth 0→1 (or 1→0) curve for crossfades: equal-power sine shape
  function fadeCurve(up, n) {
    const c = new Float32Array(n || 32);
    for (let i = 0; i < c.length; i++) { const x = i / (c.length - 1); c[i] = up ? Math.sin((x * Math.PI) / 2) : Math.cos((x * Math.PI) / 2); }
    return c;
  }

  /* ---------------- the mixer ---------------- */
  // soft-knee ceiling: transparent below 0.55, saturates smoothly to 0.85 (−1.4 dBFS)
  function ceilingCurve() {
    const N = 4097, c = new Float32Array(N), knee = 0.55, room = 0.3;
    for (let i = 0; i < N; i++) {
      const s = ((i / (N - 1)) * 2 - 1) * 2; // the shaper sees the signal pre-scaled by 0.5
      const a = Math.abs(s);
      c[i] = Math.sign(s) * (a <= knee ? a : knee + room * Math.tanh((a - knee) / room));
    }
    return c;
  }
  function makeMixer(kit, dest) {
    const ac = kit.ac, M = { ac };
    M.dry = Gain(ac, LEVEL.music);
    M.sfx = Gain(ac, LEVEL.sfx);
    M.hallSend = Gain(ac, 1); M.roomSend = Gain(ac, 1); M.delaySend = Gain(ac, 1);
    const sum = Gain(ac, 1);
    const hall = ac.createConvolver(); hall.normalize = false; hall.buffer = kit.hallIR;
    const room = ac.createConvolver(); room.normalize = false; room.buffer = kit.roomIR;
    const hallRet = Gain(ac, LEVEL.hall), roomRet = Gain(ac, LEVEL.room);
    chain(M.hallSend, hall, hallRet, sum);
    chain(M.roomSend, room, roomRet, sum);
    // echo: a darkened feedback delay that also feeds the hall
    const dl = ac.createDelay(2); dl.delayTime.value = 0.43;
    const dlf = Filt(ac, 'lowpass', 2800, 0.5), dhp = Filt(ac, 'highpass', 260, 0.5), fb = Gain(ac, 0.34);
    chain(M.delaySend, dl, dlf, dhp, fb, dl);
    const echoRet = Gain(ac, LEVEL.echo); dhp.connect(echoRet); echoRet.connect(sum);
    const echoHall = Gain(ac, 0.35); dhp.connect(echoHall); echoHall.connect(M.hallSend);
    M.dry.connect(sum); M.sfx.connect(sum);
    // master chain
    const hp = Filt(ac, 'highpass', 26, 0.6);
    const comp = ac.createDynamicsCompressor();
    comp.threshold.value = -20; comp.knee.value = 12; comp.ratio.value = 2.4; comp.attack.value = 0.015; comp.release.value = 0.3;
    const trim = Gain(ac, LEVEL.trim), pre = Gain(ac, 0.5);
    const shaper = ac.createWaveShaper(); shaper.curve = ceilingCurve(); shaper.oversample = 'none';
    M.pause = Gain(ac, 0); M.mute = Gain(ac, 1);
    chain(sum, hp, comp, trim, pre, shaper, M.pause, M.mute, dest);
    M.comp = comp;
    return M;
  }
  // A channel strip into a set of outputs {dry, hall, room, delay}: input → pan → dry + sends.
  function makeStrip(ac, outs, o) {
    o = o || {};
    const input = Gain(ac, o.gain == null ? 1 : o.gain);
    let node = input;
    if (o.pan) { node = Pan(ac, o.pan); input.connect(node); }
    node.connect(outs.dry);
    const nodes = [input, node];
    for (const k of ['hall', 'room', 'delay']) {
      if (o[k] > 0 && outs[k]) { const s = Gain(ac, o[k]); node.connect(s); s.connect(outs[k]); nodes.push(s); }
    }
    return { input, nodes, o };
  }

  /* ---------------- harmony helpers ---------------- */
  const pc = (m) => ((m % 12) + 12) % 12;
  // choose n notes in [lo, hi] covering the chord's pitch classes, moving as
  // little as possible from the previous voicing (smooth voice leading)
  function voiceLead(pcs, prev, lo, hi, n) {
    const want = pcs.map(pc), cand = [];
    for (let m = lo; m <= hi; m++) if (want.includes(pc(m))) cand.push(m);
    const need = Math.min(n, new Set(want).size), mid = (lo + hi) / 2;
    const P = prev && prev.length ? prev : null;
    let best = null, bestCost = 1e9;
    const pick = [];
    // depth-first search with incremental spacing rules and a cost bound (prunes almost everything)
    const rec = (start, cost) => {
      const L = pick.length;
      if (L === n) {
        if (new Set(pick.map(pc)).size < need) return;
        const total = cost + 0.12 * (pick[n - 1] - pick[0]) + (P ? 0 : Math.abs((pick[0] + pick[n - 1]) / 2 - mid));
        if (total < bestCost) { bestCost = total; best = pick.slice(); }
        return;
      }
      for (let i = start; i <= cand.length - (n - L); i++) {
        const m = cand[i];
        if (L) { const q = pick[L - 1], iv = m - q; if (iv < 2 || (iv < 3 && q < 60) || (iv < 5 && q < 50)) continue; }
        const c = cost + (P ? Math.abs(m - P[Math.min(L, P.length - 1)]) : 0);
        if (c >= bestCost) continue;
        pick.push(m); rec(i + 1, c); pick.pop();
      }
    };
    rec(0, 0);
    return best || cand.slice(0, n);
  }

  /* ==========================================================================
     Instruments. ch = { ac, kit, input, owner, R }: every voice connects into
     ch.input and registers its sources with ch.owner (so it can be stopped).
     Oscillators are always filtered and enveloped (warm, never buzzy, no clicks).
     ========================================================================== */
  const I = {};

  // a stack of sine partials [ratio, amp, decay(, attack)] — bells, celesta, marimba
  I.partials = (ch, t, f, v, list, peak) => {
    const { ac } = ch;
    for (const [k, a, d, at] of list) {
      if (f * k > Math.min(15000, ac.sampleRate * 0.45)) continue;
      const o = Osc(ac, 'sine', f * k, t, t + (at || 0.002) + d + 0.05), gg = Gain(ac);
      perc(gg.gain, t, (peak || 0.2) * v * a, at || 0.002, d);
      chain(o, gg, ch.input); own(ch.owner, o, [gg]);
    }
  };
  I.celesta = (ch, t, m, v) => {
    const d = 1.1 + 1.5 * clamp((92 - m) / 30, 0, 1);
    I.partials(ch, t, mtof(m), v, [[1, 1, d], [2, 0.2, d * 0.4], [4, 0.06, 0.08]], 0.2);
  };
  I.glock = (ch, t, m, v) => {
    I.partials(ch, t, mtof(m), v, [[1, 1, 1.5], [2.76, 0.2, 0.32], [5.4, 0.07, 0.08]], 0.16);
  };
  I.marimba = (ch, t, m, v) => {
    const d = 0.85 - 0.5 * clamp((m - 48) / 36, 0, 1);
    I.partials(ch, t, mtof(m), v, [[1, 1, d, 0.0015], [4, 0.2, 0.055, 0.001], [9.9, 0.04, 0.02, 0.001]], 0.28);
  };
  // felt piano: two unison strings, darkening as it decays, damper on release
  I.keys = (ch, t, m, v, dur) => {
    const { ac, kit } = ch, f = mtof(m), lo = clamp((m - 36) / 60, 0, 1);
    const ring = 5 - 3.4 * lo, tr = t + Math.max(dur || 0.5, 0.36), rel = 0.28 + 0.5 * (1 - lo), end = tr + rel + 0.03;
    const o1 = Osc(ac, kit.wave.piano, f, t, end), o2 = Osc(ac, 'sine', f * 1.0011, t, end);
    const g2 = Gain(ac, 0.3), lp = Filt(ac, 'lowpass', 1000, 0.3), gg = Gain(ac);
    lp.frequency.setValueAtTime(nyq(ac, Math.min(9000, f * (2.4 + 4.6 * v) + 450)), t);
    lp.frequency.exponentialRampToValueAtTime(Math.max(f * 1.5, 240), t + 0.9 + 1.4 * (1 - lo));
    o1.connect(lp); chain(o2, g2, lp); chain(lp, gg, ch.input);
    const pk = 0.3 * v, p = gg.gain;
    p.setValueAtTime(0, t); p.linearRampToValueAtTime(pk, t + 0.007);
    p.exponentialRampToValueAtTime(pk * 0.42, t + 0.33);
    p.exponentialRampToValueAtTime(Math.max(2 * EPS, pk * 0.42 * Math.exp(-(tr - t - 0.33) / (ring / 3))), tr);
    p.exponentialRampToValueAtTime(EPS, tr + rel); p.linearRampToValueAtTime(0, tr + rel + 0.01);
    own(ch.owner, o1, [lp, gg, g2]); own(ch.owner, o2);
  };
  // plucked string (harp, nylon guitar): the filter closes as the string rings
  I.pluck = (ch, t, m, v, o) => {
    o = o || {};
    const { ac, kit } = ch, f = mtof(m), lo = clamp((m - 40) / 48, 0, 1);
    const dec = (o.decay || 2.2) * (1.25 - 0.75 * lo);
    const osc = Osc(ac, kit.wave.harp, f, t, t + dec + 0.05), lp = Filt(ac, 'lowpass', 1000, 0.6), gg = Gain(ac);
    lp.frequency.setValueAtTime(nyq(ac, Math.min(11000, f * (o.bright || 7))), t);
    lp.frequency.exponentialRampToValueAtTime(Math.max(f * 1.25, 180), t + Math.min(0.7, dec * 0.35));
    perc(gg.gain, t, 0.28 * v, 0.003, dec);
    chain(osc, lp, gg, ch.input); own(ch.owner, osc, [lp, gg]);
  };
  // pizzicato strings: a short bright snap settling into a woody body
  I.pizz = (ch, t, m, v, o) => {
    const { ac, kit } = ch, f = mtof(m);
    const dec = ((o && o.decay) || 0.42) * (1.35 - 0.7 * clamp((m - 36) / 48, 0, 1));
    const osc = Osc(ac, kit.wave.string, f, t, t + dec + 0.05), lp = Filt(ac, 'lowpass', 1000, 1.1), gg = Gain(ac);
    osc.detune.setValueAtTime(14, t); osc.detune.linearRampToValueAtTime(0, t + 0.04);
    lp.frequency.setValueAtTime(Math.min(7000, f * 7 + 300), t);
    lp.frequency.exponentialRampToValueAtTime(Math.max(f * 1.8, 250), t + 0.16);
    perc(gg.gain, t, 0.36 * v, 0.003, dec);
    chain(osc, lp, gg, ch.input); own(ch.owner, osc, [lp, gg]);
  };
  // the bassoon's formant body (shared by every bassoon note on a channel)
  function reedBody(ch) {
    if (ch.reed) return ch.reed;
    const { ac } = ch;
    const f1 = Filt(ac, 'peaking', 470, 1.4), f2 = Filt(ac, 'peaking', 1150, 2), lp = Filt(ac, 'lowpass', 2300, 0.6);
    f1.gain.value = 8; f2.gain.value = 3.5;
    chain(f1, f2, lp, ch.input);
    ch.reed = f1;
    return f1;
  }
  function vibrato(ch, osc, t, end, rate, cents, delay) {
    const { ac } = ch, lfo = Osc(ac, 'sine', rate, t, end), dg = Gain(ac, 0);
    dg.gain.setValueAtTime(0, t + delay); dg.gain.linearRampToValueAtTime(cents, t + delay + 0.35);
    chain(lfo, dg, osc.detune); own(ch.owner, lfo, [dg]);
  }
  function breath(ch, dest, t, dur, f, amp) {
    const { ac, kit } = ch, nz = Noise(ac, kit.white, t, t + dur + 0.08, ch.R), bp = Filt(ac, 'bandpass', f, 0.9), ng = Gain(ac);
    perc(ng.gain, t, amp, 0.012, dur + 0.04);
    chain(nz, bp, ng, dest); own(ch.owner, nz, [bp, ng]);
  }
  // bassoon: reedy scoop into the note, formant body, a little breath; o.bend droops the pitch
  I.bassoon = (ch, t, m, v, dur, o) => {
    o = o || {};
    const { ac, kit } = ch, f = mtof(m), body = reedBody(ch);
    const a = o.a || 0.03, r = o.r || 0.07, end = t + dur + r + 0.05;
    const osc = Osc(ac, kit.wave.reed, f, t, end), pre = Filt(ac, 'lowpass', Math.min(4200, f * 9), 0.5), gg = Gain(ac);
    osc.detune.setValueAtTime(-28, t); osc.detune.linearRampToValueAtTime(0, t + 0.045);
    if (o.bend) { const b0 = t + Math.max(0.06, dur * 0.45); osc.detune.setValueAtTime(0, b0); osc.detune.linearRampToValueAtTime(o.bend, t + dur + r); }
    sus(gg.gain, t, 0.21 * v, a, dur, r);
    chain(osc, pre, gg, body); own(ch.owner, osc, [pre, gg]);
    if (dur > 0.45 && !o.bend) vibrato(ch, osc, t, end, 5.1, 9, 0.18);
    breath(ch, body, t, Math.min(dur, 0.2), 1700, 0.045 * v);
  };
  // clarinet-ish hollow reed (odd harmonics), used for giggles and sly answers
  I.clarinet = (ch, t, m, v, dur, o) => {
    o = o || {};
    const { ac, kit } = ch, f = mtof(m), end = t + dur + 0.12;
    const osc = Osc(ac, kit.wave.hollow, f, t, end), lp = Filt(ac, 'lowpass', Math.min(4200, f * 5), 0.6), gg = Gain(ac);
    osc.detune.setValueAtTime(-16, t); osc.detune.linearRampToValueAtTime(0, t + 0.03);
    if (o.bend) { osc.detune.setValueAtTime(0, t + dur * 0.5); osc.detune.linearRampToValueAtTime(o.bend, t + dur + 0.06); }
    sus(gg.gain, t, 0.2 * v, 0.022, dur, 0.06);
    chain(osc, lp, gg, ch.input); own(ch.owner, osc, [lp, gg]);
    breath(ch, ch.input, t, Math.min(dur, 0.12), f * 2.2, 0.02 * v);
  };
  I.flute = (ch, t, m, v, dur) => {
    const { ac, kit } = ch, f = mtof(m), end = t + dur + 0.2;
    const osc = Osc(ac, kit.wave.flute, f, t, end), lp = Filt(ac, 'lowpass', Math.min(6000, f * 4), 0.5), gg = Gain(ac);
    sus(gg.gain, t, 0.2 * v, 0.06, dur, 0.14);
    chain(osc, lp, gg, ch.input); own(ch.owner, osc, [lp, gg]);
    if (dur > 0.4) vibrato(ch, osc, t, end, 5, 7, 0.25);
    breath(ch, ch.input, t, Math.min(dur, 0.3), f * 2, 0.025 * v);
  };
  // warm bass: sine + octave (so it reads on laptop speakers), gently filtered
  I.bass = (ch, t, m, v, dur, o) => {
    const { ac } = ch, f = mtof(m), r = (o && o.r) || 0.5, end = t + dur + r + 0.05;
    const o1 = Osc(ac, 'sine', f, t, end), o2 = Osc(ac, 'sine', f * 2, t, end);
    const g2 = Gain(ac, 0.5), lp = Filt(ac, 'lowpass', 800, 0.5), gg = Gain(ac);
    o1.connect(lp); chain(o2, g2, lp); chain(lp, gg, ch.input);
    sus(gg.gain, t, 0.12 * v, (o && o.a) || 0.05, dur, r);
    own(ch.owner, o1, [lp, gg, g2]); own(ch.owner, o2);
  };
  // french horn: the filter opens as the note speaks (brassy bloom), slow vibrato
  I.horn = (ch, t, m, v, dur) => {
    const { ac, kit } = ch, f = mtof(m), end = t + dur + 0.75;
    const osc = Osc(ac, kit.wave.horn, f, t, end), lp = Filt(ac, 'lowpass', f, 0.5), gg = Gain(ac);
    osc.detune.setValueAtTime(-12, t); osc.detune.linearRampToValueAtTime(0, t + 0.09);
    const open = Math.min(3000, f * (2 + 2.4 * v));
    lp.frequency.setValueAtTime(f * 1.1, t); lp.frequency.linearRampToValueAtTime(open, t + 0.28);
    lp.frequency.setValueAtTime(open, t + Math.max(0.3, dur)); lp.frequency.linearRampToValueAtTime(f * 1.2, t + dur + 0.7);
    sus(gg.gain, t, 0.26 * v, 0.14, dur, 0.6);
    chain(osc, lp, gg, ch.input); own(ch.owner, osc, [lp, gg]);
    if (dur > 0.6) vibrato(ch, osc, t, end, 4.6, 6, 0.4);
  };
  // bowed string melody: two detuned voices, a bow-swell inside the note, vibrato
  I.bow = (ch, t, m, v, dur) => {
    const { ac, kit } = ch, f = mtof(m), end = t + dur + 0.75;
    const o1 = Osc(ac, kit.wave.string, f, t, end), o2 = Osc(ac, kit.wave.string, f, t, end);
    o1.detune.value = 5; o2.detune.value = -5;
    const lp = Filt(ac, 'lowpass', Math.min(5200, f * 4 + 300), 0.5), gg = Gain(ac), pk = 0.16 * v, p = gg.gain;
    const a = Math.min(0.2, dur * 0.4);
    p.setValueAtTime(0, t); p.linearRampToValueAtTime(pk * 0.72, t + a);
    p.linearRampToValueAtTime(pk, t + a + (Math.max(dur, a + 0.02) - a) * 0.45);
    p.linearRampToValueAtTime(pk * 0.82, t + Math.max(dur, a + 0.04));
    p.exponentialRampToValueAtTime(EPS, t + Math.max(dur, a + 0.04) + 0.62); p.linearRampToValueAtTime(0, t + Math.max(dur, a + 0.04) + 0.64);
    o1.connect(lp); o2.connect(lp); chain(lp, gg, ch.input);
    own(ch.owner, o1, [lp, gg]); own(ch.owner, o2);
    if (dur > 0.5) {
      const lfo = Osc(ac, 'sine', 5.4, t, end), dg = Gain(ac, 0);
      dg.gain.setValueAtTime(0, t + 0.22); dg.gain.linearRampToValueAtTime(10, t + 0.57);
      lfo.connect(dg); dg.connect(o1.detune); dg.connect(o2.detune); own(ch.owner, lfo, [dg]);
    }
  };
  // cold synth pulse for the machine
  I.pulse = (ch, t, m, v, dur, o) => {
    const { ac, kit } = ch, f = mtof(m);
    const osc = Osc(ac, kit.wave.hollow, f, t, t + dur + 0.05), lp = Filt(ac, 'lowpass', Math.min(5000, f * ((o && o.bright) || 3)), 0.9), gg = Gain(ac);
    perc(gg.gain, t, 0.26 * v, 0.002, dur);
    chain(osc, lp, gg, ch.input); own(ch.owner, osc, [lp, gg]);
  };
  // pure cold beep (the fractured theme in the machine)
  I.beep = (ch, t, m, v, dur) => {
    const { ac } = ch, o = Osc(ac, 'triangle', mtof(m), t, t + dur + 0.08), lp = Filt(ac, 'lowpass', 2600, 0.5), gg = Gain(ac);
    sus(gg.gain, t, 0.16 * v, 0.004, dur, 0.05);
    chain(o, lp, gg, ch.input); own(ch.owner, o, [lp, gg]);
  };
  // woodblock / metronome / clock tick
  I.tick = (ch, t, f, v, d) => {
    const { ac, kit } = ch;
    d = d || 0.025;
    const nz = Noise(ac, kit.white, t, t + d + 0.05, ch.R), bp = Filt(ac, 'bandpass', f, 4), ng = Gain(ac);
    perc(ng.gain, t, 2.2 * v, 0.0008, d);
    chain(nz, bp, ng, ch.input); own(ch.owner, nz, [bp, ng]);
    const o = Osc(ac, 'sine', f * 0.62, t, t + d * 2 + 0.06), og = Gain(ac);
    perc(og.gain, t, 0.16 * v, 0.001, d * 1.8);
    chain(o, og, ch.input); own(ch.owner, o, [og]);
  };

  /* ---------------- pads: sustained chords with tied common tones ---------------- */
  class Pad {
    constructor(ch, o) {
      this.ch = ch;
      this.o = Object.assign({ wave: 'string', cut: 1400, q: 0.5, a: 1.2, r: 1.8, level: 0.07, det: 7, vib: 0, lfo: 0.06, lfoDepth: 280, spread: 0.6 }, o);
      const { ac } = ch, T0 = ac.currentTime, T1 = T0 + 4000;
      this.f = Filt(ac, 'lowpass', this.o.cut, this.o.q);
      this.f.connect(ch.input);
      if (this.o.lfoDepth) { const l = Osc(ac, 'sine', this.o.lfo, T0, T1), lg = Gain(ac, this.o.lfoDepth); chain(l, lg, this.f.frequency); own(ch.owner, l, [lg]); }
      if (this.o.vib) { const vo = Osc(ac, 'sine', 4.7, T0, T1); this.vib = Gain(ac, this.o.vib); chain(vo, this.vib); own(ch.owner, vo, [this.vib]); }
    }
    note(m, t0, t1, v, attack) {
      const { ac, kit } = this.ch, o = this.o, f = mtof(m), end = t1 + o.r + 0.05;
      const wave = kit.wave[o.wave] || kit.wave.string;
      const o1 = Osc(ac, wave, f, t0, end), o2 = Osc(ac, wave, f, t0, end);
      o1.detune.value = o.det; o2.detune.value = -o.det;
      const gg = Gain(ac), p = Pan(ac, (((pc(m) * 7) % 12) / 11 - 0.5) * o.spread);
      o1.connect(gg); o2.connect(gg); chain(gg, p, this.f);
      sus(gg.gain, t0, o.level * v, Math.min(attack || o.a, Math.max(0.05, (t1 - t0) * 0.8)), t1 - t0, o.r);
      const vib = this.vib;
      if (vib) { vib.connect(o1.detune); vib.connect(o2.detune); }
      own(this.ch.owner, o1, [gg, p, vib ? () => { try { vib.disconnect(o1.detune); vib.disconnect(o2.detune); } catch (e) { /* gone */ } } : null]);
      own(this.ch.owner, o2);
    }
  }

  /* ==========================================================================
     A bed is one mood segment: its music and ambience on private faders.
     Its bar grid is anchored to the segment's start on the film timeline.
     def = { key, bpm, meter, voicing:{lo,hi,n}, penta, chords(bed,b), setup(bed,p0), bar(bed,b) }
     ========================================================================== */
  const MOODS = {};

  class Bed {
    constructor(eng, seg, p0) {
      this.eng = eng; this.ac = eng.ac; this.kit = eng.kit;
      this.seg = seg; this.mood = seg.mood; this.def = MOODS[seg.mood];
      this.len = Math.max(0.5, seg.t1 - seg.t0);
      this.meter = this.def.meter || 4; this.beat = 60 / (this.def.bpm || 60); this.barDur = this.beat * this.meter;
      this.key = this.def.key || 62;
      this.srcs = new Set(); this.q = []; this.p0 = p0;
      this.bar = Math.max(0, Math.floor(p0 / this.barDur));
      this.R = rng(seg.mood, 'noise', Math.round(seg.t0 * 10));
      this.L = {}; this.dead = false; this.out = 0;
      const M = eng.mix;
      this.ins = {}; this.fIn = []; this.fOut = [];
      for (const k of ['dry', 'hall', 'room', 'delay']) {
        const a = Gain(this.ac, 0), b = Gain(this.ac, 1);
        a.connect(b); b.connect(k === 'dry' ? M.dry : M[k + 'Send']);
        this.ins[k] = a; this.fIn.push(a); this.fOut.push(b);
      }
      try { if (this.def.setup) this.def.setup(this, p0); } catch (e) { eng.err(e); }
    }
    fadeIn(t0, t1) {
      const k = (MOOD_GAIN[this.mood] == null ? 1 : MOOD_GAIN[this.mood]) * (this.eng.moodGain[this.mood] || 1);
      const c = fadeCurve(true).map((x) => x * k);
      for (const a of this.fIn) a.gain.setValueCurveAtTime(c, t0, Math.max(0.02, t1 - t0));
    }
    fadeOut(t0, t1) {
      if (this.out) return;
      this.out = t1;
      const c = fadeCurve(false);
      for (const b of this.fOut) b.gain.setValueCurveAtTime(c, t0, Math.max(0.02, t1 - t0));
    }
    strip(o) {
      const s = makeStrip(this.ac, this.ins, o);
      return { ac: this.ac, kit: this.kit, input: s.input, owner: this, R: this.R };
    }
    at(p, fn) { this.q.push({ p, fn }); }
    pos(b, x) { return (b * this.meter + x) * this.beat; }   // bed seconds of bar b, beat x
    dur(beats) { return (beats * this.beat) / this.eng.speed; } // audio seconds for a beat count
    // seeded humanisation (seconds) for note k of bar b
    hum(b, k, amt) { return rng(this.mood, 'hum', b, k).gauss() * (amt == null ? 0.012 : amt); }
    advance(untilCtx, now) {
      if (this.dead) return;
      const eng = this.eng, untilPos = eng.ctxToFilm(untilCtx) - this.seg.t0;
      let grew = false;
      while (!this.done && this.pos(this.bar, 0) <= untilPos + 0.15) {
        if (this.pos(this.bar, 0) > this.len + 2.5) { this.done = true; break; }
        try { this.def.bar(this, this.bar); } catch (e) { eng.err(e); }
        this.bar++; grew = true;
      }
      if (grew) this.q.sort((a, b) => a.p - b.p);
      while (this.q.length && this.q[0].p <= untilPos) {
        const ev = this.q.shift();
        if (ev.p < this.p0 - 1e-6) continue; // before this bed started (mid-segment start)
        let when = eng.filmToCtx(this.seg.t0 + ev.p);
        if (when < now) { if (now - when > 0.08) continue; when = now; }
        if (this.out && when > this.out) continue;
        try { ev.fn(when); } catch (e) { eng.err(e); }
      }
    }
    kill(t) {
      if (this.dead) return;
      this.dead = true;
      stopAll(this, t);
      const nodes = this.fIn.concat(this.fOut);
      const done = () => { for (const n of nodes) { try { n.disconnect(); } catch (e) { /* gone */ } } };
      if (this.eng.offline) return;
      setTimeout(done, Math.max(0, (t - this.ac.currentTime) * 1000) + 400);
    }
    // voiced chord segments of bar b: [{p0, p1, notes, bass}] (voice-led from bar 0, memoised)
    segs(b) {
      const memo = this._segs || (this._segs = []), def = this.def;
      if (!def.chords) return [];
      const vc = def.voicing || { lo: 50, hi: 74, n: 4 };
      for (let k = memo.length; k <= b; k++) {
        const raw = def.chords(this, k) || [], out = [];
        let prev = null;
        for (let j = k - 1; j >= 0 && !prev; j--) if (memo[j].length) prev = memo[j][memo[j].length - 1].notes;
        for (let i = 0; i < raw.length; i++) {
          const [bt, offs, bass] = raw[i], bt1 = i + 1 < raw.length ? raw[i + 1][0] : this.meter;
          const notes = voiceLead(offs.map((x) => this.key + x), prev, vc.lo, vc.hi, vc.n);
          out.push({ p0: this.pos(k, bt), p1: this.pos(k, bt1), notes, bass: bass == null ? offs[0] : bass, offs });
          prev = notes;
        }
        memo.push(out);
      }
      return memo[b];
    }
    // what is sounding at bed position p (used to keep one-shots in key)
    harmony(p) {
      const def = this.def, b = Math.max(0, Math.floor(p / this.barDur));
      let chord = null;
      if (def.chords) { const S = this.segs(b); for (const s of S) if (p >= s.p0 - 1e-6) chord = s; }
      return { key: this.key, penta: def.penta || [0, 2, 4, 7, 9], chord: chord ? chord.offs : [0, 4, 7] };
    }
  }

  /* ---------------- shared musical helpers ---------------- */
  // pad chords with tied common tones; starts mid-chord when the bed starts mid-bar
  function padBar(bed, pad, b, v) {
    const list = bed.segs(b);
    for (let si = 0; si < list.length; si++) {
      const s = list[si];
      if (s.p1 <= bed.p0 + 1e-6) continue;
      let prevSeg = si > 0 ? list[si - 1] : null;
      if (!prevSeg && b > 0) { const L = bed.segs(b - 1); prevSeg = L[L.length - 1] || null; }
      for (const n of s.notes) {
        if (prevSeg && prevSeg.notes.includes(n) && prevSeg.p1 > bed.p0 + 1e-6) continue; // still sounding
        let end = s.p1, bb = b, sj = si;
        for (let guard = 0; guard < 12; guard++) {
          let L = bed.segs(bb);
          sj++;
          if (sj >= L.length) { bb++; sj = 0; L = bed.segs(bb); }
          const nx = L[sj];
          if (nx && nx.notes.includes(n)) end = nx.p1; else break;
        }
        const ps = Math.max(s.p0, bed.p0), catchUp = ps > s.p0 + 1e-6 ? 0.45 : 0; // joining mid-chord (seek/resume): come in quickly
        bed.at(ps, (w) => pad.note(n, w, w + (end - ps) / bed.eng.speed, v, catchUp));
      }
    }
  }
  // bass: the root of each chord segment (held through repeats)
  function bassBar(bed, ch, b, v, o) {
    o = o || {};
    const list = bed.segs(b), lo = o.lo || 36;
    for (let si = 0; si < list.length; si++) {
      const s = list[si];
      if (s.p1 <= bed.p0 + 1e-6) continue;
      let m = bed.key + s.bass;
      while (m >= lo + 12) m -= 12;
      while (m < lo) m += 12;
      const ps = Math.max(s.p0, bed.p0);
      bed.at(ps + bed.hum(b, 90 + si, 0.006), (w) => I.bass(ch, w, m, v, (s.p1 - ps) / bed.eng.speed, o));
    }
  }
  // the flower theme: [beat, beats, semitones above the tonic] over 4 bars of 3/4
  const THEME_A = [[0, 0.5, 0], [0.5, 0.5, 2], [1, 1, 4], [2, 1, 7], [3, 1.5, 12], [4.5, 0.5, 11], [5, 1, 9], [6, 2, 7], [8, 1, 4], [9, 3, 2]];
  const THEME_B = [[0, 0.5, 0], [0.5, 0.5, 2], [1, 1, 4], [2, 1, 7], [3, 1.5, 9], [4.5, 0.5, 7], [5, 1, 5], [6, 2, 4], [8, 1, 2], [9, 3, 0]];
  // chords that carry the theme (offsets from the tonic; [beat, chord, bass])
  const I_ = [0, 4, 7], vi_ = [9, 0, 4], IV_ = [5, 9, 0], V_ = [7, 11, 2], Vs_ = [7, 0, 2], V7_ = [7, 11, 2, 5];
  const CH_A = [[[0, I_]], [[0, vi_]], [[0, IV_]], [[0, Vs_], [1.5, V_]]];
  const CH_B = [[[0, I_]], [[0, IV_]], [[0, I_, 7], [2, V7_]], [[0, I_]]];
  // emit the notes of bar i (0..3) of a phrase; fn(pos, beats, semis, beatInPhrase)
  function phraseBar(bed, b, phrase, i, fn) {
    for (const [bt, d, s] of phrase) if (bt >= i * 3 && bt < i * 3 + 3) fn(bed.pos(b, bt - i * 3), d, s, bt);
  }
  // a sung shape: higher notes a touch louder, the phrase peak a touch late
  const lift = (s) => 0.86 + 0.02 * s;
  const agogic = (bt) => (bt === 3 ? 0.035 : 0);

  /* ---------------- ambience layers ---------------- */
  function windLayer(bed, o) {
    const { ac, kit } = bed, t0 = ac.currentTime, t1 = t0 + 4000;
    const ch = bed.strip({ hall: o.hall || 0.04 });
    const src = Noise(ac, kit.pinkSt, t0, t1, bed.R, o.rate || 1);
    const hp = Filt(ac, 'highpass', o.hp || 80, 0.5), lp = Filt(ac, 'lowpass', o.f || 700, 0.5), gg = Gain(ac, o.level);
    chain(src, hp, lp, gg, ch.input); own(bed, src, [hp, lp, gg]);
    return { lp, gg, o };
  }
  function gusts(bed, L, b) {
    const R = rng(bed.mood, 'gust', b), n = R() < 0.5 ? 2 : 1, depth = L.o.gust == null ? 1 : L.o.gust;
    for (let i = 0; i < n; i++) {
      const p = bed.pos(b, R() * bed.meter), k = R();
      const f = L.o.f * (1 + depth * (k * 1.1 - 0.4)), lv = L.o.level * (1 + depth * (k * 0.9 - 0.35));
      bed.at(p, (w) => { L.lp.frequency.setTargetAtTime(f, w, 0.9); L.gg.gain.setTargetAtTime(lv, w, 1.1); });
    }
  }
  // leaves: bright noise with a slow random flutter
  function rustleLayer(bed, o) {
    const { ac, kit } = bed, t0 = ac.currentTime, t1 = t0 + 4000;
    const ch = bed.strip({ hall: 0.06 });
    const src = Noise(ac, kit.whiteSt, t0, t1, bed.R), hp = Filt(ac, 'highpass', 1700, 0.5), bp = Filt(ac, 'peaking', 4300, 0.8);
    bp.gain.value = 4;
    const lp = Filt(ac, 'lowpass', 7500, 0.5), gg = Gain(ac, o.level);
    chain(src, hp, bp, lp, gg, ch.input);
    const mod = Noise(ac, kit.brownSt, t0, t1, bed.R, 0.5), mlp = Filt(ac, 'lowpass', 7, 0.5), mg = Gain(ac, o.level * 5);
    chain(mod, mlp, mg, gg.gain);
    own(bed, src, [hp, bp, lp, gg]); own(bed, mod, [mlp, mg]);
    return { gg, o };
  }
  // birdsong: kinds 'warble' (robin), 'chirp' (sparrow), 'trill' (warbler), 'feebee' (chickadee), 'coo' (dove)
  function bird(ch, t, kind, R, v) {
    const { ac } = ch, o = ac.createOscillator(), gg = Gain(ac), p = gg.gain, F = o.frequency;
    o.type = 'sine';
    const pk = 0.07 * v;
    let tt = t;
    p.setValueAtTime(0, t);
    if (kind === 'feebee') {
      const f1 = R.range(3650, 4100), f2 = f1 * 0.84;
      F.setValueAtTime(f1, t); F.linearRampToValueAtTime(f1 * 0.99, t + 0.32);
      p.linearRampToValueAtTime(pk, t + 0.04); p.linearRampToValueAtTime(pk * 0.85, t + 0.3); p.linearRampToValueAtTime(0, t + 0.34);
      F.setValueAtTime(f2 * 1.01, t + 0.4); F.linearRampToValueAtTime(f2, t + 0.68);
      p.setValueAtTime(0, t + 0.4); p.linearRampToValueAtTime(pk * 0.9, t + 0.44); p.linearRampToValueAtTime(pk * 0.7, t + 0.63); p.linearRampToValueAtTime(0, t + 0.68);
      tt = t + 0.7;
    } else if (kind === 'chirp') {
      const n = R.int(2, 5);
      for (let i = 0; i < n; i++) {
        const fA = R.range(4200, 5600), fB = fA * R.range(0.55, 0.7);
        F.setValueAtTime(fA, tt); F.exponentialRampToValueAtTime(fB, tt + 0.045);
        p.setValueAtTime(0, tt); p.linearRampToValueAtTime(pk * R.range(0.7, 1), tt + 0.006); p.linearRampToValueAtTime(0, tt + 0.05);
        tt += R.range(0.09, 0.15);
      }
      tt += 0.06;
    } else if (kind === 'trill') {
      const f = R.range(4300, 5200), d = R.range(0.45, 0.9), rate = R.range(22, 32), n = Math.floor(d * rate);
      F.setValueAtTime(f, t); F.linearRampToValueAtTime(f * 0.9, t + d);
      for (let i = 0; i < n; i++) {
        const s = t + i / rate, a = pk * 0.8 * Math.sin((Math.PI * (i + 0.5)) / n);
        p.setValueAtTime(0, s); p.linearRampToValueAtTime(a, s + 0.35 / rate); p.linearRampToValueAtTime(0, s + 0.75 / rate);
      }
      tt = t + d + 0.05;
    } else if (kind === 'coo' || kind === 'owl') {
      const owl = kind === 'owl', f = owl ? R.range(360, 400) : R.range(480, 560);
      const notes = owl ? [[0, 0.5, 1, 0.96], [0.78, 0.22, 1.02, 0.98], [1.06, 0.62, 1, 0.94]] : [[0, 0.32, 1, 0.92], [0.42, 0.55, 1.12, 1.0], [1.1, 0.4, 0.98, 0.94]];
      for (const [s, d, k, k2] of notes) {
        F.setValueAtTime(f * k, t + s); F.linearRampToValueAtTime(f * k * k2, t + s + d);
        p.setValueAtTime(0, t + s); p.linearRampToValueAtTime(pk * 1.6, t + s + 0.08); p.linearRampToValueAtTime(pk * 1.2, t + s + d - 0.08); p.linearRampToValueAtTime(0, t + s + d);
      }
      tt = t + 1.6;
    } else {
      const n = R.int(4, 7);
      let f = R.range(2400, 3300);
      for (let i = 0; i < n; i++) {
        const d = R.range(0.07, 0.16), f2 = clamp(f * R.range(0.8, 1.3), 1900, 4600);
        F.setValueAtTime(f, tt); F.linearRampToValueAtTime(f2, tt + d);
        p.setValueAtTime(0, tt); p.linearRampToValueAtTime(pk, tt + 0.015); p.linearRampToValueAtTime(pk * 0.75, tt + d - 0.02); p.linearRampToValueAtTime(0, tt + d);
        tt += d + R.range(0.03, 0.08);
        f = clamp(f2 * R.range(0.85, 1.15), 2000, 4400);
      }
    }
    o.connect(gg); gg.connect(ch.input);
    o.start(t); o.stop(tt + 0.05);
    own(ch.owner, o, [gg]);
    return tt - t;
  }
  // three bird perches (left, right, far) so calls come from around the listener
  function birdPerches(bed, hall) {
    return [-0.65, 0.5, 0.05].map((pan, i) => bed.strip({ pan, hall: (hall || 0.12) * (1 + i * 0.8), gain: 1 - i * 0.35 }));
  }
  // schedule calls inside bar b; rate = mean calls per second
  function birdBar(bed, perches, b, rate, kinds, v) {
    const R = rng(bed.mood, 'bird', b), d = bed.barDur;
    let p = bed.pos(b, 0) + R.range(0, 1 / rate);
    while (p < bed.pos(b + 1, 0)) {
      const kind = R.pick(kinds), ch = R.pick(perches), RR = rng(bed.mood, 'call', b, Math.round(p * 100)), vv = v * R.range(0.55, 1);
      bed.at(p, (w) => bird(ch, w, kind, RR, vv));
      p += R.range(0.4, 1.6) / rate;
    }
    return d;
  }
  // crickets: persistent tones gated into chirps
  function crickets(bed, n, level) {
    const list = [];
    for (let i = 0; i < n; i++) {
      const R = rng(bed.mood, 'cricket', i);
      list.push({ pan: R.range(-0.85, 0.85), f: R.range(3900, 5100), gg: null, period: R.range(0.5, 0.95), pulses: R.int(2, 4), level: level * R.range(0.55, 1), phase: R() });
    }
    return list;
  }
  function cricketVoice(bed, c) {
    const { ac } = bed, t0 = ac.currentTime, t1 = t0 + 4000, ch = bed.strip({ pan: c.pan, hall: 0.1 });
    const o = Osc(ac, 'sine', c.f, t0, t1), o2 = Osc(ac, 'sine', c.f * 2.01, t0, t1), g2 = Gain(ac, 0.06), gg = Gain(ac, 0);
    o.connect(gg); chain(o2, g2, gg); gg.connect(ch.input);
    own(bed, o, [gg, g2]); own(bed, o2);
    c.gg = gg;
  }
  function cricketBar(bed, list, b, amt) {
    const p0 = bed.pos(b, 0), p1 = bed.pos(b + 1, 0);
    for (let i = 0; i < list.length; i++) {
      const c = list[i], R = rng(bed.mood, 'crk', i, b), lv = c.level * (amt == null ? 1 : amt);
      if (lv < 1e-4) continue;
      if (!c.gg) cricketVoice(bed, c);
      for (let p = c.period * (Math.ceil(p0 / c.period - c.phase) + c.phase); p < p1; p += c.period) {
        if (R() < 0.1) continue;
        bed.at(p + R.range(-0.01, 0.01), (w) => {
          for (let j = 0; j < c.pulses; j++) {
            const s = w + j * 0.034, P = c.gg.gain;
            P.setValueAtTime(0, s); P.linearRampToValueAtTime(lv, s + 0.005); P.setValueAtTime(lv, s + 0.014); P.linearRampToValueAtTime(0, s + 0.02);
          }
        });
      }
    }
  }
  // distant crowd murmur: pink noise through two vowel-like bands that flicker at syllable rate
  function murmur(bed, level, pan) {
    const { ac, kit } = bed, t0 = ac.currentTime, t1 = t0 + 4000;
    const ch = bed.strip({ hall: 0.22, pan });
    const src = Noise(ac, kit.pinkSt, t0, t1, bed.R);
    const b1 = Filt(ac, 'bandpass', 420, 1.1), b2 = Filt(ac, 'bandpass', 1250, 1.4), lp = Filt(ac, 'lowpass', 2300, 0.5);
    const g1 = Gain(ac, level), g2 = Gain(ac, level * 0.5);
    src.connect(b1); src.connect(b2); chain(b1, g1, lp); chain(b2, g2, lp); lp.connect(ch.input);
    own(bed, src, [b1, b2, lp, g1, g2]);
    return { g1, g2, b1, b2, level, id: pan };
  }
  function murmurBar(bed, Mm, b) {
    const R = rng(bed.mood, 'mm', b, Mm.id), p1 = bed.pos(b + 1, 0);
    for (let p = bed.pos(b, 0); p < p1; p += R.range(0.13, 0.32)) {
      const a = Mm.level * R.range(0.4, 1.15), a2 = a * R.range(0.3, 0.7), f1 = R.range(330, 560), f2 = R.range(1000, 1650);
      bed.at(p, (w) => { Mm.g1.gain.setTargetAtTime(a, w, 0.05); Mm.g2.gain.setTargetAtTime(a2, w, 0.05); Mm.b1.frequency.setTargetAtTime(f1, w, 0.08); Mm.b2.frequency.setTargetAtTime(f2, w, 0.08); });
    }
  }
  // a steady low room tone (shop, night air, silence)
  function roomTone(bed, level, f) {
    const { ac, kit } = bed, t0 = ac.currentTime, ch = bed.strip({});
    const src = Noise(ac, kit.brownSt, t0, t0 + 4000, bed.R), lp = Filt(ac, 'lowpass', f || 300, 0.5), hp = Filt(ac, 'highpass', 40, 0.5), gg = Gain(ac, level);
    chain(src, hp, lp, gg, ch.input); own(bed, src, [lp, hp, gg]);
    return gg;
  }
  // a sustained shimmer of sine partials with slow independent tremolo
  function shimmerLayer(bed, notes, level, o) {
    const { ac } = bed, t0 = ac.currentTime, t1 = t0 + 4000, ch = bed.strip(Object.assign({ hall: 0.5, delay: 0.1 }, o));
    notes.forEach((m, i) => {
      const R = rng(bed.mood, 'shim', i), osc = Osc(ac, 'sine', mtof(m), t0, t1), gg = Gain(ac, level * R.range(0.5, 1));
      osc.detune.value = R.range(-4, 4);
      const l = Osc(ac, 'sine', R.range(0.07, 0.23), t0, t1), lg = Gain(ac, level * 0.45);
      chain(l, lg, gg.gain); chain(osc, gg, ch.input);
      own(bed, osc, [gg]); own(bed, l, [lg]);
    });
    return ch;
  }

  /* ==========================================================================
     Moods, part one: title, forest, wonder, tender, cosmic.
     ========================================================================== */
  const segAt = (S, p) => { let s = S[0]; for (const x of S) if (p >= x.p0 - 1e-6) s = x; return s; };
  // six arpeggio tones for a chord segment: bass, the voicing, the voicing's 2nd note an octave up
  function arpTones(bed, s, lo) {
    let bass = bed.key + s.bass;
    while (bass >= (lo || 38) + 12) bass -= 12;
    while (bass < (lo || 38)) bass += 12;
    const v = s.notes.slice().sort((a, b) => a - b);
    return [bass].concat(v, [v[Math.min(1, v.length - 1)] + 12]);
  }

  /* ---- title: the theme's question, delicately (celesta + flute over harp and strings) ---- */
  MOODS.title = {
    key: 62, bpm: 69, meter: 3, voicing: { lo: 50, hi: 69, n: 4 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) {
      if (b === 0) return [[0, [0, 4, 7, 2]]];
      const i = (b - 1) % 8;
      return (i < 4 ? CH_A : CH_B)[i % 4];
    },
    setup(bed) {
      const L = bed.L;
      L.pad = new Pad(bed.strip({ hall: 0.55 }), { level: 0.055, cut: 2000, a: 2.2, r: 2.8, vib: 4 });
      L.cel = bed.strip({ hall: 0.5, delay: 0.14, pan: 0.1 });
      L.fl = bed.strip({ hall: 0.5, pan: -0.06 });
      L.harp = bed.strip({ hall: 0.42, pan: -0.2 });
      L.bass = bed.strip({ hall: 0.25 });
      shimmerLayer(bed, [86, 93, 98], 0.005, {});
      L.wind = windLayer(bed, { level: 0.012, f: 520, gust: 0.6 });
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key;
      padBar(bed, L.pad, b, 1);
      bassBar(bed, L.bass, b, 0.5, { lo: 38, a: 0.3, r: 1.2 });
      gusts(bed, L.wind, b);
      const S = bed.segs(b);
      if (b === 0) {
        // the first light: a slow rolled chord rising out of the dark
        const tones = arpTones(bed, S[0], 38).concat([74, 78, 81]);
        tones.forEach((m, j) => bed.at(bed.pos(0, 0.6 + j * 0.24), (w) => I.pluck(L.harp, w, m, 0.42 + 0.05 * j, { decay: 3 })));
        return;
      }
      for (let e = 0; e < 6; e++) {
        const p = bed.pos(b, e * 0.5), tones = arpTones(bed, segAt(S, p), 38), idx = [0, 2, 3, 4, 3, 2][e];
        bed.at(p + bed.hum(b, e, 0.01), (w) => I.pluck(L.harp, w, tones[idx], e === 0 ? 0.52 : 0.4, { decay: 2.6 }));
      }
      const i = (b - 1) % 8;
      phraseBar(bed, b, i < 4 ? THEME_A : THEME_B, i % 4, (p, d, s, bt) => {
        const at = p + agogic(bt) + bed.hum(b, 20 + bt * 2, 0.008);
        bed.at(at, (w) => I.celesta(L.cel, w, k + 12 + s, 1.0 * lift(s)));
        bed.at(at + 0.012, (w) => I.flute(L.fl, w, k + 12 + s, 0.5 * lift(s), bed.dur(d) * 0.94));
      });
    },
  };

  /* ---- forest: wind in the trees, birdsong, a light nylon-guitar arpeggio ---- */
  MOODS.forest = {
    key: 62, bpm: 88, meter: 4, voicing: { lo: 50, hi: 72, n: 4 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) {
      const i = b % 8;
      const P = [[0, 4, 7], [5, 9, 0], [9, 0, 4, 7], null, [0, 4, 7], [5, 9, 0, 4], [2, 5, 9, 0], [7, 11, 2]];
      const B = [0, 0, 9, 7, 0, 5, 2, 7];
      if (i === 3) return [[0, [7, 0, 2], 7], [2, [7, 11, 2], 7]];
      return [[0, P[i], B[i]]];
    },
    setup(bed) {
      const L = bed.L;
      L.wind = windLayer(bed, { level: 0.06, f: 650, gust: 1 });
      L.leaves = rustleLayer(bed, { level: 0.014 });
      L.perch = birdPerches(bed, 0.12);
      L.gtr = bed.strip({ hall: 0.26, room: 0.1, pan: -0.12 });
      L.pad = new Pad(bed.strip({ hall: 0.4 }), { level: 0.016, cut: 1300, a: 2, r: 2.4 });
      L.knock = bed.strip({ pan: 0.72, hall: 0.4, gain: 0.5 });
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, S = bed.segs(b), R = rng('forest', 'arp', b), i = b % 8;
      gusts(bed, L.wind, b);
      birdBar(bed, L.perch, b, 0.42, ['warble', 'chirp', 'feebee', 'trill', 'warble'], 2.2);
      padBar(bed, L.pad, b, 1);
      const pat = R.pick([[0, 2, 3, 4, 5, 4, 3, 2], [0, 3, 2, 4, 3, 5, 4, 3], [0, 2, 4, 3, 5, 3, 4, 2]]);
      const hint = i === 4 && b > 0; // the flower's opening notes, half-heard in the top voice
      const fade = b === 0 ? 0.7 : 1;
      for (let e = 0; e < 8; e++) {
        if (hint && (e === 2 || e === 3 || e === 4 || e === 6)) continue;
        if (e > 0 && R() < 0.1) continue;
        const p = bed.pos(b, e * 0.5), tones = arpTones(bed, segAt(S, p), 38);
        const v = (e === 0 ? 0.72 : e === 4 ? 0.6 : 0.48) * R.range(0.85, 1.1) * fade;
        bed.at(p + bed.hum(b, e, 0.011), (w) => I.pluck(L.gtr, w, tones[pat[e]], v, { decay: 1.6, bright: 5.5 }));
      }
      if (hint) [[1, 0], [1.5, 2], [2, 4], [3, 7]].forEach(([bt, s], j) =>
        bed.at(bed.pos(b, bt) + bed.hum(b, 40 + j, 0.01), (w) => I.pluck(L.gtr, w, k + 12 + s, 0.62, { decay: 2, bright: 6 })));
      if (i === 6 && b % 16 === 6) {
        const n = 9 + R.int(0, 4);
        for (let j = 0; j < n; j++) bed.at(bed.pos(b, 2) + j / 15.5, (w) => I.tick(L.knock, w, 1150, 0.3 * (1 - j / (n + 3)), 0.018));
      }
    },
  };

  /* ---- wonder: time slows. Lydian shimmer, harp sweeps, the motif on celesta ---- */
  MOODS.wonder = {
    key: 62, bpm: 56, meter: 4, voicing: { lo: 57, hi: 81, n: 4 }, penta: [0, 2, 4, 6, 9],
    chords(bed, b) {
      return [
        [[0, [0, 4, 7, 2]]], [[0, [5, 9, 0, 4], 0]], [[0, [0, 4, 7, 11]]], [[0, [2, 6, 9, 4], 0]],
        [[0, [9, 0, 4, 7]]], [[0, [5, 9, 0, 4]]], [[0, [2, 5, 9, 0]]], [[0, [7, 0, 2]], [2, [7, 11, 2, 9]]],
      ][b % 8];
    },
    setup(bed) {
      const L = bed.L;
      L.pad = new Pad(bed.strip({ hall: 0.6, delay: 0.04 }), { level: 0.042, cut: 2500, a: 2.6, r: 3.2, vib: 5, spread: 0.9 });
      shimmerLayer(bed, [86, 93, 100], 0.0042, {});
      L.cel = bed.strip({ hall: 0.55, delay: 0.22, pan: 0.12 });
      L.harp = bed.strip({ hall: 0.5, pan: -0.22 });
      L.bass = bed.strip({ hall: 0.35 });
      L.air = windLayer(bed, { level: 0.006, f: 1900, hp: 600, gust: 0.4 });
      L.perch = birdPerches(bed, 0.45);
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, S = bed.segs(b);
      padBar(bed, L.pad, b, 1);
      bassBar(bed, L.bass, b, 0.25, { lo: 38, a: 0.9, r: 2.2 });
      gusts(bed, L.air, b);
      birdBar(bed, L.perch, b, 0.07, ['feebee', 'warble'], 0.4);
      if (b % 2 === 0) {
        const tones = arpTones(bed, S[0], 50), up = tones.concat(tones.slice(1).map((m) => m + 12));
        up.forEach((m, j) => bed.at(bed.pos(b, 0.25) + j * 0.15 + bed.hum(b, j, 0.006), (w) => I.pluck(L.harp, w, m, 0.24 + 0.2 * Math.sin((Math.PI * (j + 0.5)) / up.length), { decay: 3.2 })));
      }
      const c = b % 4;
      if (c === 1) [[0, 0], [0.5, 2], [1, 4], [1.5, 7], [2.5, 12]].forEach(([bt, s], j) =>
        bed.at(bed.pos(b, bt) + bed.hum(b, 30 + j, 0.02), (w) => I.celesta(L.cel, w, k + 12 + s, 1.5 * lift(s))));
      // the answer: B G# F# E over the Lydian E/D; over the A chord it settles onto C# instead
      if (c === 3) (b % 8 === 7 ? [[0, 19], [1, 16], [1.5, 14], [2, 11]] : [[0, 21], [1, 18], [1.5, 16], [2, 14]]).forEach(([bt, s], j) =>
        bed.at(bed.pos(b, bt) + bed.hum(b, 50 + j, 0.02), (w) => I.celesta(L.cel, w, k + s, 1.15)));
    },
  };

  /* ---- tender: intimate felt piano. First lonely (minor colours), then warm ---- */
  const TENDER_FORM = (b) => {
    if (b === 0) return { s: 'intro', i: 0 };
    if (b <= 16) { const j = b - 1; return { s: ['Al', 'Bl', 'Aw', 'Bw'][Math.floor(j / 4)], i: j % 4 }; }
    const j = (b - 17) % 12;
    return { s: ['int', 'Ah', 'Bh'][Math.floor(j / 4)], i: j % 4 };
  };
  MOODS.tender = {
    key: 62, bpm: 66, meter: 3, voicing: { lo: 50, hi: 69, n: 3 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) {
      const f = TENDER_FORM(b), i = f.i;
      if (f.s === 'intro') return [[0, [5, 9, 0, 4]]];
      if (f.s === 'Al') return [[[0, [9, 0, 4]]], [[0, [2, 5, 9, 0]]], [[0, [4, 7, 11, 2]]], [[0, Vs_], [1.5, V_]]][i];
      if (f.s === 'Bl') return [[[0, [9, 0, 4]]], [[0, IV_]], [[0, [2, 5, 9, 0]], [2, V7_]], [[0, I_]]][i];
      if (f.s === 'int') return [[[0, [9, 0, 4, 7]]], [[0, [5, 9, 0, 4]]], [[0, I_, 4]], [[0, Vs_], [1.5, V_]]][i];
      return (f.s[0] === 'A' ? CH_A : CH_B)[i];
    },
    setup(bed) {
      const L = bed.L;
      L.pno = bed.strip({ hall: 0.34, room: 0.08, pan: 0.04 });
      L.pad = new Pad(bed.strip({ hall: 0.45 }), { level: 0.03, cut: 1250, a: 2.2, r: 2.6, vib: 3 });
      L.cello = bed.strip({ hall: 0.36, pan: -0.25 });
      L.air = windLayer(bed, { level: 0.008, f: 600, gust: 0.7 });
      L.perch = birdPerches(bed, 0.3);
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, S = bed.segs(b), f = TENDER_FORM(b);
      const lonely = f.s === 'Al' || f.s === 'Bl' || f.s === 'intro', warm = !lonely;
      gusts(bed, L.air, b);
      birdBar(bed, L.perch, b, 0.05, ['warble', 'feebee'], 0.35);
      if (warm) padBar(bed, L.pad, b, f.s === 'int' ? 0.8 : 1);
      // left hand: broken chord in 8ths (sparser while the flower is alone)
      const dyn = lonely ? 0.8 : 1;
      for (let e = 0; e < 6; e++) {
        if (lonely && (e === 1 || e === 5)) continue;
        const p = bed.pos(b, e * 0.5), tones = arpTones(bed, segAt(S, p), 41), idx = [0, 1, 2, 3, 2, 1][e];
        const v = [0.42, 0.28, 0.33, 0.3, 0.3, 0.26][e] * dyn;
        bed.at(p + bed.hum(b, e, 0.014), (w) => I.keys(L.pno, w, tones[idx], v, bed.dur(e === 0 ? 2.5 : 0.9)));
      }
      if (f.s === 'intro' || f.s === 'int') {
        if (f.s === 'int') { const s = S[0]; [1, 2].forEach((bt, j) => bed.at(bed.pos(b, bt) + bed.hum(b, 60 + j), (w) => I.keys(L.pno, w, s.notes[2] + 12, 0.24, bed.dur(1)))); }
        return;
      }
      const oct = f.s[1] === 'h' ? 12 : 0, phrase = f.s[0] === 'A' ? THEME_A : THEME_B;
      const vel = f.s[1] === 'l' ? 0.5 : f.s[1] === 'w' ? 0.62 : 0.56;
      phraseBar(bed, b, phrase, f.i, (p, d, s, bt) => {
        const at = p + agogic(bt) * 1.4 + bed.hum(b, 20 + bt * 2, 0.012);
        bed.at(at, (w) => I.keys(L.pno, w, k + oct + s, vel * lift(s), bed.dur(d)));
      });
      if (f.s === 'Bw' || f.s === 'Bh') {
        const s0 = S[0], m = s0.notes[0] - 12 + (s0.notes[0] - 12 < 45 ? 12 : 0);
        bed.at(bed.pos(b, 0) + 0.02, (w) => I.bow(L.cello, w, m, 0.5, bed.dur(2.9)));
      }
    },
  };

  /* ---- cosmic: vast. A drone, slow wide chords, the theme on horn in Fibonacci time ---- */
  const COS_RISE = [[0, 1, 0], [1, 1, 2], [2, 2, 4], [4, 3, 7], [7, 5, 12]];      // 1 1 2 3 5 beats
  const COS_FALL = [[0, 2, 11], [2, 1, 9], [3, 3, 7], [6, 2, 4], [8, 4, 2], [12, 4, -1]];   // …landing on the leading tone
  MOODS.cosmic = {
    key: 62, bpm: 50, meter: 4, voicing: { lo: 50, hi: 79, n: 5 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) {
      const i = Math.floor(b / 2) % 4;
      return [[[0, [0, 4, 7, 2, 9]]], [[0, [9, 0, 4, 2, 7]]], [[0, [5, 9, 0, 4, 11]]],
        b % 2 ? [[0, [7, 11, 2, 9, 4]]] : [[0, [7, 0, 2, 9, 4]]]][i];
    },
    setup(bed) {
      const L = bed.L, { ac } = bed, t0 = ac.currentTime, t1 = t0 + 4000;
      L.pad = new Pad(bed.strip({ hall: 0.7, delay: 0.05 }), { wave: 'soft', level: 0.034, cut: 1800, a: 3.5, r: 4.5, vib: 3, spread: 1 });
      L.horn = bed.strip({ hall: 0.62, pan: -0.06 });
      L.tw = [-0.7, 0, 0.7].map((pan) => bed.strip({ hall: 0.6, delay: 0.35, pan }));
      L.space = windLayer(bed, { level: 0.012, f: 260, hp: 40, gust: 0.8 });
      const dch = bed.strip({ hall: 0.3 }), dlp = Filt(ac, 'lowpass', 420, 0.5);
      dlp.connect(dch.input);
      [[38, 0.03, 0], [45, 0.02, 0.21], [50, 0.018, -0.17], [57, 0.008, 0.13]].forEach(([m, a, det]) => {
        const o = Osc(ac, 'sine', mtof(m) + det, t0, t1), gg = Gain(ac, a), l = Osc(ac, 'sine', 0.05 + a, t0, t1), lg = Gain(ac, a * 0.35);
        chain(l, lg, gg.gain); chain(o, gg, dlp); own(bed, o, [gg]); own(bed, l, [lg]);
      });
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, R = rng('cosmic', 'tw', b);
      padBar(bed, L.pad, b, 1);
      gusts(bed, L.space, b);
      const c = b % 8; // the horn's phrase spans the 8-bar chord cycle: rise (1-3), fall (4-7), home (0)
      const play = (list, base) => list.forEach(([bt, d, s], j) => {
        const rel = bt - base;
        if (rel >= 0 && rel < 4) bed.at(bed.pos(b, rel) + bed.hum(b, 10 + j, 0.015), (w) => I.horn(L.horn, w, k + s, 0.72 * lift(s), bed.dur(d) * 0.97));
      });
      if (c >= 1 && c <= 3) play(COS_RISE, (c - 1) * 4);
      if (c >= 4) play(COS_FALL, (c - 4) * 4);
      if (c === 0 && b > 0) play([[0, 4, 0]], 0);
      for (let bt = 0; bt < 4; bt += 0.5) {
        if (!R.chance(0.24)) continue;
        const s = R.pick(bed.def.penta) + 12 * R.int(2, 3), ch = R.pick(L.tw), v = R.range(0.6, 1.0);
        bed.at(bed.pos(b, bt) + R.range(0, 0.25), (w) => I.glock(ch, w, k + s, v));
      }
    },
  };

  /* ==========================================================================
     Moods, part two: machine, dusk, comedy, town, shop, parking, reflection, silence.
     ========================================================================== */

  /* ---- machine: cold, metronomic, quantised. The theme turns minor and never completes ---- */
  MOODS.machine = {
    key: 62, bpm: 104, meter: 4, voicing: { lo: 50, hi: 69, n: 3 }, penta: [0, 3, 5, 7, 10],
    chords(bed, b) { return [[[0, [0, 3, 7]]], [[0, [0, 3, 7]]], [[0, [8, 0, 3]]], [[0, [10, 2, 5]]]][b % 4]; },
    setup(bed) {
      const L = bed.L, { ac, kit } = bed, t0 = ac.currentTime, t1 = t0 + 4000;
      L.tick = bed.strip({ room: 0.12, pan: 0.18 });
      L.chug = bed.strip({ room: 0.08 });
      L.arp = bed.strip({ room: 0.1, pan: 0.28 });
      L.beep = bed.strip({ room: 0.18, delay: 0.08, pan: -0.2 });
      L.clank = bed.strip({ room: 0.32, pan: -0.45 });
      const hch = bed.strip({}), hlp = Filt(ac, 'lowpass', 300, 0.5);
      hlp.connect(hch.input);
      [[38, 0.011], [50, 0.007], [57, 0.003]].forEach(([m, a], j) => { const o = Osc(ac, 'sine', mtof(m) + j * 0.13, t0, t1), gg = Gain(ac, a); chain(o, gg, hlp); own(bed, o, [gg]); });
      const cch = bed.strip({ room: 0.1 }), src = Noise(ac, kit.brownSt, t0, t1, bed.R), bp = Filt(ac, 'bandpass', 150, 1.2);
      L.conv = Gain(ac, 0);
      chain(src, bp, L.conv, cch.input); own(bed, src, [bp, L.conv]);
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, S = bed.segs(b), s = S[0];
      const bass = arpTones(bed, s, 36)[0];
      // the machine stalls at the end of its segment: it winds down, then stops
      const stall = bed.len - 1.7;
      if (!L.down && bed.pos(b + 1, 0) > stall && stall > bed.p0) { L.down = true; bed.at(stall, (w) => machineStall(bed, w)); }
      const at = (p, fn) => { if (p < stall) bed.at(p, fn); };
      const v = s.notes.slice().sort((a, c) => a - c), pat = [0, 1, 2, 1];
      for (let e = 0; e < 8; e++) {
        const p = bed.pos(b, e * 0.5), on = e % 2 === 0;
        if (on) at(p, (w) => I.tick(L.tick, w, e === 0 ? 2100 : 1500, e === 0 ? 0.6 : 0.45, 0.02));
        else at(p, (w) => I.tick(L.tick, w, 5200, 0.14, 0.008));
        at(p, (w) => I.pulse(L.chug, w, bass, on ? 0.5 : 0.36, 0.13, { bright: 2.4 }));
        if (!on) { const m = v[pat[(e >> 1) % 4]]; at(p, (w) => I.pulse(L.arp, w, m, 0.36, 0.09, { bright: 4 })); }
        at(p, (w) => { const P = L.conv.gain; P.setValueAtTime(0.02, w); P.linearRampToValueAtTime(0.005, w + 0.2); });
      }
      const c = b % 4;
      const frag = c === 1 ? [[0, 0], [0.5, 2], [1, 3], [1.5, 7]] : c === 3 ? [[0, 0], [0.5, 2], [1, 3], [2, 0], [2.5, 2], [3, 3]] : [];
      frag.forEach(([bt, st]) => at(bed.pos(b, bt), (w) => I.beep(L.beep, w, k + 12 + st, 0.65, 0.2)));
      if (b % 2 === 0) at(bed.pos(b, 0), (w) => {
        I.partials(L.clank, w, 523, 0.5, [[1, 1, 0.25], [2.33, 0.6, 0.18], [3.71, 0.4, 0.12], [5.2, 0.25, 0.08]], 0.06);
        I.tick(L.clank, w, 900, 0.3, 0.04);
      });
    },
  };

  function machineStall(bed, w) {
    const { ac, kit } = bed, L = bed.L, ch = L.chug;
    const o = Osc(ac, kit.wave.hollow, mtof(50), w, w + 1.9), lp = Filt(ac, 'lowpass', 1400, 1.2), gg = Gain(ac);
    o.frequency.exponentialRampToValueAtTime(28, w + 1.7);
    lp.frequency.setValueAtTime(1400, w); lp.frequency.exponentialRampToValueAtTime(140, w + 1.7);
    gg.gain.setValueAtTime(0, w); gg.gain.linearRampToValueAtTime(0.07, w + 0.05); gg.gain.exponentialRampToValueAtTime(EPS, w + 1.8); gg.gain.linearRampToValueAtTime(0, w + 1.82);
    chain(o, lp, gg, ch.input); own(bed, o, [lp, gg]);
    [[0, 1500], [0.42, 1250], [0.98, 1000]].forEach(([dt, f], j) => I.tick(L.tick, w + dt, f, 0.4 - j * 0.1, 0.02));
    L.conv.gain.setTargetAtTime(0, w, 0.4);
  }

  /* ---- dusk: crickets, a warm low pad, a few evening piano notes, an owl far away ---- */
  MOODS.dusk = {
    key: 65, bpm: 60, meter: 4, voicing: { lo: 52, hi: 70, n: 4 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) {
      const i = Math.floor(b / 2) % 4;
      return [[[0, [0, 4, 7, 2]]], [[0, [9, 0, 4, 7]]], [[0, [5, 9, 0, 4]]], b % 2 ? [[0, [7, 11, 2, 5]]] : [[0, [7, 0, 2]]]][i];
    },
    setup(bed) {
      const L = bed.L;
      L.crk = crickets(bed, 4, 0.024);
      L.wind = windLayer(bed, { level: 0.012, f: 420, gust: 0.7 });
      L.pad = new Pad(bed.strip({ hall: 0.45 }), { level: 0.042, cut: 850, a: 2.6, r: 3, vib: 2 });
      L.pno = bed.strip({ hall: 0.5, delay: 0.1, pan: 0.15 });
      L.bass = bed.strip({ hall: 0.2 });
      L.owl = bed.strip({ pan: -0.6, hall: 0.65, gain: 0.7 });
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, R = rng('dusk', 'pno', b);
      padBar(bed, L.pad, b, 1);
      bassBar(bed, L.bass, b, 0.3, { lo: 41, a: 0.6, r: 1.6 });
      cricketBar(bed, L.crk, b);
      gusts(bed, L.wind, b);
      if (b % 8 === 4) {
        [[0, 0], [0.5, 2], [1, 4], [2, 7], [3, 12]].forEach(([bt, s], j) =>
          bed.at(bed.pos(b, bt) + bed.hum(b, j, 0.02), (w) => I.keys(L.pno, w, k + 12 + s, 0.56 * lift(s), bed.dur(j === 4 ? 3 : 1))));
      } else {
        const n = R.int(0, 2), seg = bed.segs(b)[0];
        for (let j = 0; j < n; j++) {
          const m = seg.notes[R.int(1, seg.notes.length - 1)] + 12 * R.int(1, 2);
          bed.at(bed.pos(b, R.pick([0.5, 1.5, 2, 3])) + R.range(0, 0.08), (w) => I.keys(L.pno, w, Math.min(m, 89), R.range(0.36, 0.5), bed.dur(2)));
        }
      }
      if (b % 6 === 3) { const RR = rng('dusk', 'owl', b); bed.at(bed.pos(b, 1), (w) => bird(L.owl, w, 'owl', RR, 0.8)); }
    },
  };

  /* ---- comedy: oom-pah pizzicato and a sly bassoon, answered by a perky clarinet ---- */
  const COM_BSN = [[0, 0.4, -5], [1, 0.3, -3], [1.5, 0.3, -1], [2, 0.4, 0], [3, 0.6, 4], [4, 0.3, 3], [4.5, 0.5, 4], [5.5, 0.3, 1], [6, 0.4, -3], [7, 0.4, -5],
    [8, 0.4, -7], [9, 0.4, -3], [10, 0.3, 0], [10.5, 0.3, -1], [11, 0.3, -2], [11.5, 0.3, -3], [12, 0.4, -5], [13.5, 0.3, -1], [14, 1.2, -1]];
  const COM_CLA = [[0, 0.22, 7], [0.5, 0.22, 9], [1, 0.22, 7], [1.5, 0.5, 4], [3, 0.3, 0], [4, 0.22, 5], [4.5, 0.22, 4], [5, 0.22, 2], [5.5, 0.5, 0],
    [8, 0.22, 7], [8.5, 0.22, 11], [9, 0.22, 12], [9.5, 0.6, 14], [11, 0.3, 12], [12, 0.25, 7], [12.5, 0.25, 4], [13, 0.25, 2], [13.5, 0.25, -1], [14, 0.8, 0]];
  MOODS.comedy = {
    key: 65, bpm: 116, meter: 4, voicing: { lo: 53, hi: 69, n: 3 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) { return [[[0, I_]], [[0, [9, 1, 4, 7]]], [[0, [2, 5, 9, 0]]], [[0, V7_]], [[0, I_]], [[0, IV_]], [[0, V7_]], [[0, I_]]][b % 8]; },
    setup(bed) {
      const L = bed.L;
      L.pz = bed.strip({ room: 0.28, hall: 0.08 });
      L.pzc = bed.strip({ room: 0.28, hall: 0.08, pan: 0.2 });
      L.bsn = bed.strip({ room: 0.22, hall: 0.1, pan: -0.15 });
      L.cla = bed.strip({ room: 0.22, hall: 0.12, pan: 0.3 });
      L.blk = bed.strip({ room: 0.3, pan: 0.45 });
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, s = bed.segs(b)[0], tones = arpTones(bed, s, 41), fifth = tones[0] + 7;
      bed.at(bed.pos(b, 0) + bed.hum(b, 0, 0.006), (w) => I.pizz(L.pz, w, tones[0], 0.8));
      bed.at(bed.pos(b, 2) + bed.hum(b, 1, 0.006), (w) => I.pizz(L.pz, w, fifth, 0.65));
      for (const bt of [1, 3]) s.notes.forEach((m, j) => bed.at(bed.pos(b, bt) + j * 0.008 + bed.hum(b, 4 + bt + j, 0.005), (w) => I.pizz(L.pzc, w, m, 0.38, { decay: 0.3 })));
      const c = b % 8, ph = c < 4 ? COM_BSN : COM_CLA, base = (c % 4) * 4;
      for (const [bt, d, st] of ph) {
        const rel = bt - base;
        if (rel < 0 || rel >= 4) continue;
        const p = bed.pos(b, rel) + bed.hum(b, 10 + bt * 2, 0.008);
        if (c < 4) bed.at(p, (w) => I.bassoon(L.bsn, w, 53 + st + (k - 65), 0.8, bed.dur(d), { bend: d > 1 ? -35 : 0 }));
        else bed.at(p, (w) => I.clarinet(L.cla, w, 65 + st + (k - 65), 0.6, bed.dur(d)));
      }
      if (c >= 4 && (c === 5 || c === 7)) bed.at(bed.pos(b, 2.5), (w) => I.bassoon(L.bsn, w, 41 + (k - 65) + 7, 0.6, bed.dur(0.35)));
      if (b % 2 === 1) bed.at(bed.pos(b, 3.5), (w) => I.tick(L.blk, w, 1250, 0.25, 0.03));
    },
  };

  /* ---- town: a distant murmur, sparrows, a light marimba in C ---- */
  MOODS.town = {
    key: 60, bpm: 108, meter: 4, voicing: { lo: 60, hi: 76, n: 3 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) { return [[[0, I_]], [[0, [9, 0, 4, 7]]], [[0, [5, 9, 0, 4]]], [[0, Vs_], [2, V_]]][b % 4]; },
    setup(bed) {
      const L = bed.L;
      L.mm = [murmur(bed, 0.1, -0.5), murmur(bed, 0.085, 0.55)];
      L.perch = birdPerches(bed, 0.15);
      L.mar = bed.strip({ room: 0.15, hall: 0.14, pan: -0.1 });
      L.mel = bed.strip({ room: 0.15, hall: 0.2, pan: 0.22 });
      L.pz = bed.strip({ room: 0.2 });
      L.shk = bed.strip({ room: 0.1, pan: 0.35 });
      L.bike = bed.strip({ pan: 0.75, hall: 0.4, gain: 0.5 });
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, S = bed.segs(b), R = rng('town', 'mel', b);
      L.mm.forEach((M) => murmurBar(bed, M, b));
      birdBar(bed, L.perch, b, 0.16, ['chirp', 'chirp', 'warble'], 0.9);
      const pat = [0, 2, 1, 2, 3, 2, 1, 2];
      for (let e = 0; e < 8; e++) {
        const p = bed.pos(b, e * 0.5), s = segAt(S, p), v = s.notes.slice().sort((a, c) => a - c), t4 = v.concat([v[0] + 12]);
        bed.at(p + bed.hum(b, e, 0.008), (w) => I.marimba(L.mar, w, t4[pat[e]], (e % 4 === 0 ? 0.6 : 0.44) * R.range(0.9, 1.08)));
        bed.at(p + 0.004, (w) => I.tick(L.shk, w, 7200, e % 2 ? 0.05 : 0.08, 0.014));
      }
      const tones = arpTones(bed, S[0], 36);
      bed.at(bed.pos(b, 0), (w) => I.pizz(L.pz, w, tones[0], 0.42, { decay: 0.5 }));
      bed.at(bed.pos(b, 2), (w) => I.pizz(L.pz, w, tones[0] + 7, 0.34, { decay: 0.5 }));
      if (b % 8 >= 4) {
        const rh = R.pick([[0, 1, 1.5, 2.5, 3], [0, 0.5, 1, 2, 3], [0.5, 1, 2, 2.5, 3.5]]), pen = bed.def.penta;
        let d = R.int(0, 4);
        rh.forEach((bt, j) => { d = clamp(d + R.pick([-1, 1, 1, -2, 2]), 0, 7); const m = k + 12 + pen[d % 5] + 12 * Math.floor(d / 5); bed.at(bed.pos(b, bt) + bed.hum(b, 30 + j, 0.01), (w) => I.marimba(L.mel, w, m, 0.55)); });
      }
      if (b % 7 === 5) [0, 0.22].forEach((dt) => bed.at(bed.pos(b, 1) + dt, (w) => I.partials(L.bike, w, 2350, 0.5, [[1, 1, 0.7], [2.1, 0.4, 0.3], [3.4, 0.2, 0.15]], 0.12)));
    },
  };

  /* ---- shop: cosy. A clock at 1 Hz, tiptoeing pizzicato, Embarrassment's deadpan bassoon ---- */
  const SHOP_S1 = [[0, 1.4, -8], [2, 0.8, -9], [3, 0.8, -10], [4, 2.6, -12, -45]];
  const SHOP_S2 = [[0, 0.4, -5], [0.5, 0.4, -3], [1, 0.4, -2], [1.5, 0.4, -1], [2, 1.2, 0], [4, 0.5, 2], [5, 0.5, -1], [6, 1.6, -5, -30]];
  MOODS.shop = {
    key: 65, bpm: 120, meter: 4, voicing: { lo: 53, hi: 70, n: 3 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) { return [[[0, I_]], [[0, [9, 0, 4, 7]]], [[0, [2, 5, 9, 0]]], [[0, V7_]]][b % 4]; },
    setup(bed) {
      const L = bed.L;
      roomTone(bed, 0.006, 300);
      L.mm = murmur(bed, 0.012, 0.7);
      L.clock = bed.strip({ pan: 0.55, room: 0.35 });
      L.pz = bed.strip({ room: 0.25, hall: 0.08 });
      L.bsn = bed.strip({ room: 0.2, hall: 0.12, pan: -0.2 });
      L.gl = bed.strip({ hall: 0.4, delay: 0.15, pan: 0.3 });
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, S = bed.segs(b), s = S[0], R = rng('shop', 'pz', b), tones = arpTones(bed, s, 41);
      murmurBar(bed, L.mm, b);
      bed.at(bed.pos(b, 0), (w) => I.tick(L.clock, w, 2700, 0.34, 0.03));
      bed.at(bed.pos(b, 2), (w) => I.tick(L.clock, w, 2150, 0.3, 0.03));
      bed.at(bed.pos(b, 0) + bed.hum(b, 0, 0.008), (w) => I.pizz(L.pz, w, tones[0], 0.6));
      bed.at(bed.pos(b, 2) + bed.hum(b, 1, 0.008), (w) => I.pizz(L.pz, w, tones[0] + 7, 0.5));
      if (R.chance(0.6)) s.notes.forEach((m, j) => bed.at(bed.pos(b, 3) + j * 0.01, (w) => I.pizz(L.pz, w, m, 0.2, { decay: 0.3 })));
      const c = b % 8, ph = c === 1 || c === 2 ? SHOP_S1 : c === 5 || c === 6 ? SHOP_S2 : null, base = c === 2 || c === 6 ? 4 : 0;
      if (ph) for (const [bt, d, st, bend] of ph) {
        const rel = bt - base;
        if (rel < 0 || rel >= 4) continue;
        bed.at(bed.pos(b, rel) + bed.hum(b, 10 + bt * 2, 0.01), (w) => I.bassoon(L.bsn, w, 53 + st + (k - 65), 0.48, bed.dur(d), { bend: bend || 0 }));
      }
      if (c === 4) [0, 0.5, 1.25].forEach((bt, j) => bed.at(bed.pos(b, 1 + bt), (w) => I.glock(L.gl, w, k + 24 + [7, 4, 9][j], 0.3)));
    },
  };

  /* ---- parking: flat wind and a deflating figure over a falling bass ---- */
  MOODS.parking = {
    key: 65, bpm: 66, meter: 4, voicing: { lo: 53, hi: 72, n: 3 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) {
      const i = b >= 8 ? 1 + ((b - 1) % 7) : b;
      return [[[0, I_]], [[0, V_, 11]], [[0, [0, 4, 7, 10], 10]], [[0, IV_, 9]], [[0, [5, 8, 0], 8]], [[0, I_, 7]], [[0, [7, 0, 2, 5]], [2, V7_]], [[0, V7_]]][i];
    },
    setup(bed) {
      const L = bed.L;
      L.wind = windLayer(bed, { level: 0.02, f: 600, gust: 0.2 });
      roomTone(bed, 0.008, 160);
      L.pad = new Pad(bed.strip({ hall: 0.4 }), { level: 0.04, cut: 1000, a: 2, r: 2.6, vib: 2 });
      L.bsn = bed.strip({ room: 0.15, hall: 0.18, pan: 0.12 });
      L.bass = bed.strip({ hall: 0.2 });
      L.car = bed.strip({ hall: 0.2 });
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, i = b >= 8 ? 1 + ((b - 1) % 7) : b;
      padBar(bed, L.pad, b, 1);
      bassBar(bed, L.bass, b, 0.32, { lo: 38, a: 0.4, r: 1.4 });
      gusts(bed, L.wind, b);
      const fig = [[[0.5, 0.5, 7], [1, 0.5, 4], [1.5, 1.4, 0, -30]], [[0.5, 0.5, 5], [1, 0.5, 2], [1.5, 1.4, -1, -40]], [[0.5, 0.5, 4], [1, 0.5, 0], [1.5, 1.4, -2, -45]],
        [[0.5, 0.5, 2], [1, 0.5, 0], [1.5, 1.4, -3, -50]], [[0.5, 0.5, 0], [1, 0.5, -4], [1.5, 1.6, -7, -60]], [[0.5, 0.6, 0], [1.2, 0.6, -3], [2, 1.8, -5, -70]], null, null][i];
      const v = Math.max(0.3, 0.66 - 0.06 * i);
      if (fig) fig.forEach(([bt, d, st, bend], j) => bed.at(bed.pos(b, bt) + bed.hum(b, j, 0.012), (w) => I.bassoon(L.bsn, w, 53 + st + (k - 65), v, bed.dur(d), { bend: bend || 0 })));
      bed.at(bed.pos(b, 0), (w) => L.pad.f.frequency.setTargetAtTime(Math.max(520, 1000 - 70 * i), w, 1.5));
      if (b % 3 === 1) {
        const R = rng('parking', 'car', b), dir = R() < 0.5 ? -1 : 1;
        bed.at(bed.pos(b, R.range(0, 2)), (w) => {
          const { ac, kit } = bed, src = Noise(ac, kit.pink, w, w + 3.4, R), bp = Filt(ac, 'bandpass', 300, 0.9), p = Pan(ac, -0.8 * dir), gg = Gain(ac);
          bp.frequency.setValueAtTime(300, w); bp.frequency.linearRampToValueAtTime(820, w + 1.6); bp.frequency.linearRampToValueAtTime(380, w + 3.2);
          if (p.pan) { p.pan.setValueAtTime(-0.8 * dir, w); p.pan.linearRampToValueAtTime(0.8 * dir, w + 3.2); }
          gg.gain.setValueAtTime(0, w); gg.gain.linearRampToValueAtTime(0.03, w + 1.6); gg.gain.linearRampToValueAtTime(0, w + 3.3);
          chain(src, bp, gg, p, L.car.input); own(bed, src, [bp, gg, p]);
        });
      }
    },
  };

  /* ---- reflection: the resolution. The whole theme, intimate, then warm and full ---- */
  const REFL = (b) => {
    if (b <= 4) return { s: 'intro', i: b };
    if (b <= 8) return { s: 'A1', i: b - 5 };
    if (b <= 12) return { s: 'B1', i: b - 9 };
    if (b <= 14) return { s: 'bridge', i: b - 13 };
    if (b <= 18) return { s: 'A2', i: b - 15 };
    if (b <= 22) return { s: 'B2', i: b - 19 };
    if (b === 23) return { s: 'amen', i: 0 };
    return { s: 'end', i: b - 24 };
  };
  MOODS.reflection = {
    key: 62, bpm: 69, meter: 3, voicing: { lo: 50, hi: 69, n: 4 }, penta: [0, 2, 4, 7, 9],
    chords(bed, b) {
      const f = REFL(b), i = f.i;
      if (f.s === 'intro') return [[[0, [0, 4, 7, 2]]], [[0, IV_, 0]], [[0, [0, 4, 7, 2]]], [[0, [9, 0, 4, 7]]], [[0, IV_], [1.5, Vs_]]][i];
      if (f.s === 'A1' || f.s === 'A2') return CH_A[i];
      if (f.s === 'B1') return CH_B[i];
      if (f.s === 'B2') return i === 1 ? [[0, [5, 8, 0]]] : CH_B[i];
      if (f.s === 'bridge') return i === 0 ? [[0, [5, 9, 0, 4]]] : [[0, Vs_], [1.5, V_]];
      if (f.s === 'amen') return [[0, IV_, 0]];
      return [[0, [0, 4, 7, 2]]];
    },
    setup(bed) {
      const L = bed.L;
      L.pad = new Pad(bed.strip({ hall: 0.55 }), { level: 0.046, cut: 1900, a: 2.4, r: 3.6, vib: 4 });
      const hi = new Pad(bed.strip({ hall: 0.6 }), { level: 0.024, cut: 2600, a: 2.2, r: 3.2, vib: 5, spread: 0.9 });
      L.pad2 = { note: (m, t0, t1, v, a) => hi.note(m + 12, t0, t1, v, a) };
      L.pno = bed.strip({ hall: 0.36, room: 0.06, pan: 0.06 });
      L.harp = bed.strip({ hall: 0.45, pan: -0.25 });
      L.bow = bed.strip({ hall: 0.5, pan: 0.08 });
      L.horn = bed.strip({ hall: 0.6, pan: -0.1 });
      L.bass = bed.strip({ hall: 0.25 });
      L.cel = bed.strip({ hall: 0.55, delay: 0.2, pan: 0.15 });
      L.cym = bed.strip({ hall: 0.4 });
      L.wind = windLayer(bed, { level: 0.01, f: 560, gust: 0.6 });
      L.perch = birdPerches(bed, 0.2);
      L.crk = crickets(bed, 3, 0.018);
    },
    bar(bed, b) {
      const L = bed.L, k = bed.key, S = bed.segs(b), f = REFL(b), p0 = bed.pos(b, 0);
      gusts(bed, L.wind, b);
      if (p0 < 48) birdBar(bed, L.perch, b, 0.12 * clamp(1 - p0 / 50, 0.1, 1), ['warble', 'feebee', 'chirp'], 0.6);
      cricketBar(bed, L.crk, b, clamp((p0 - 46) / 12, 0, 1));
      const full = f.s === 'A2' || f.s === 'B2';
      const padV = { intro: 0.8, A1: 0.9, B1: 0.95, bridge: 1.05, A2: 1.25, B2: [1.2, 1.0, 0.95, 0.9][f.i] || 1, amen: 0.9, end: 0.85 }[f.s];
      padBar(bed, L.pad, b, padV);
      if (full || f.s === 'bridge') padBar(bed, L.pad2, b, full ? 1 : 0.7);
      if (f.s === 'end') { if (f.i === 0) bed.at(p0, (w) => I.bass(L.bass, w, 38, 0.5, bed.dur(12), { a: 0.3, r: 3 })); }
      else if (b > 0) bassBar(bed, L.bass, b, full ? 0.4 : 0.3, { lo: 38, a: 0.12, r: 0.9 });
      // harp / piano accompaniment
      if (f.s === 'intro' || f.s === 'A1' || f.s === 'B1') {
        for (let e = 0; e < 6; e++) {
          const p = bed.pos(b, e * 0.5), tones = arpTones(bed, segAt(S, p), 38), idx = [0, 2, 3, 4, 3, 2][e];
          const v = (b === 0 ? 0.26 : 0.32) + (e === 0 ? 0.1 : 0);
          bed.at(p + bed.hum(b, e, 0.012), (w) => I.pluck(L.harp, w, tones[idx], v, { decay: 2.6 }));
        }
      } else if (full) {
        for (let e = 0; e < 6; e++) {
          const p = bed.pos(b, e * 0.5), tones = arpTones(bed, segAt(S, p), 41), idx = [0, 2, 3, 4, 3, 2][e];
          bed.at(p + bed.hum(b, e, 0.012), (w) => I.keys(L.pno, w, tones[idx], (e === 0 ? 0.4 : 0.3) * (padV / 1.2), bed.dur(e === 0 ? 2.5 : 0.9)));
        }
        const s0 = S[0], roll = arpTones(bed, s0, 50).slice(1);
        roll.forEach((m, j) => bed.at(p0 + j * 0.05, (w) => I.pluck(L.harp, w, m + 12, 0.24, { decay: 3 })));
      } else if (f.s === 'bridge' || f.s === 'amen' || (f.s === 'end' && f.i === 0)) {
        const tones = arpTones(bed, S[0], 38), up = tones.concat(tones.slice(1).map((m) => m + 12));
        up.forEach((m, j) => bed.at(p0 + 0.05 + j * (f.s === 'bridge' ? 0.09 : 0.14), (w) => I.pluck(L.harp, w, m, 0.3, { decay: 3.4 })));
      }
      // the theme
      if (f.s === 'A1' || f.s === 'B1') {
        phraseBar(bed, b, f.s === 'A1' ? THEME_A : THEME_B, f.i, (p, d, s, bt) =>
          bed.at(p + agogic(bt) * 1.3 + bed.hum(b, 20 + bt * 2, 0.012), (w) => I.keys(L.pno, w, k + 12 + s, 0.6 * lift(s), bed.dur(d))));
      }
      if (full) {
        const dyn = f.s === 'A2' ? 1 : [0.95, 0.8, 0.78, 0.72][f.i];
        phraseBar(bed, b, f.s === 'A2' ? THEME_A : THEME_B, f.i, (p, d, s, bt) => {
          const st = f.s === 'B2' && f.i === 1 && s === 9 ? 8 : s; // "not so much the summit": the borrowed minor
          const at = p + agogic(bt) + bed.hum(b, 20 + bt * 2, 0.01);
          bed.at(at, (w) => I.bow(L.bow, w, k + 12 + st, 0.9 * dyn * lift(st), bed.dur(d) * 0.98));
          if (d >= 1) bed.at(at + 0.015, (w) => I.horn(L.horn, w, k + st, 0.5 * dyn, bed.dur(d) * 0.95));
        });
      }
      if (f.s === 'bridge') {
        const call = f.i === 0 ? [[0, 1.5, 7], [1.5, 1.5, 9]] : [[0, 1.5, 7], [1.5, 1.5, 11]];
        call.forEach(([bt, d, s], j) => bed.at(bed.pos(b, bt) + bed.hum(b, 70 + j, 0.01), (w) => I.horn(L.horn, w, k + s, 0.62 + 0.08 * f.i, bed.dur(d) * 0.97)));
        if (f.i === 1) bed.at(p0, (w) => {
          const { ac, kit } = bed, D = bed.dur(3), src = Noise(ac, kit.pinkSt, w, w + D + 0.5, bed.R), hp = Filt(ac, 'highpass', 900, 0.5), bp = Filt(ac, 'bandpass', 1500, 0.7), gg = Gain(ac);
          bp.frequency.setValueAtTime(1500, w); bp.frequency.exponentialRampToValueAtTime(7000, w + D);
          gg.gain.setValueAtTime(0, w); gg.gain.linearRampToValueAtTime(0.004, w + D * 0.4); gg.gain.exponentialRampToValueAtTime(0.05, w + D);
          gg.gain.exponentialRampToValueAtTime(EPS, w + D + 0.4); gg.gain.linearRampToValueAtTime(0, w + D + 0.42);
          chain(src, hp, bp, gg, L.cym.input); own(bed, src, [hp, bp, gg]);
        });
      }
      if (f.s === 'end' && (f.i === 1 || f.i === 2)) {
        const notes = f.i === 1 ? [[0, 0], [0.5, 2], [1, 4], [2, 7]] : [[0, 12]];
        notes.forEach(([bt, s], j) => bed.at(bed.pos(b, bt) + bed.hum(b, 80 + j, 0.02), (w) => I.celesta(L.cel, w, k + 24 + s, (f.i === 2 ? 0.85 : 0.7) * lift(s))));
      }
    },
  };

  /* ---- silence: almost nothing — just air, so the cut to black never sounds digital ---- */
  MOODS.silence = { key: 62, bpm: 60, meter: 4, setup(bed) { roomTone(bed, 0.0016, 260); }, bar() {} };

  /* ==========================================================================
     Sound effects. FX[id](S, t, g, H) → length (s)
       S = { ac, kit, owner, R, strip(o) → channel }   t = start   g = cue gain
       H = what the score is playing { key, penta, chord } so magical effects stay in key.
     Human sounds are stylised (breath through vowel formants, doubled by a reed),
     matching a film whose voices are all written words.
     ========================================================================== */
  const FX = {};
  // per-effect level trims in dB (from measurement: momentary loudness and laptop audibility)
  const FX_TRIM_DB = { footsteps: 12, step: 12, tap: 8, clock: 9, squelch: 14, paper: 10, whisper: 10, scratch: 7, sigh: 5, breath: 6, pop: 3,
    whoosh: 5, swell: 3, petal: 3, chuckle: 2, ding: 2, cash: 0, wind: 2, shimmer: -2, engine: -4, register: -2, heartbeat: 2, thud: 2, 'car-door': 4 };
  const FX_TRIM = {};
  for (const k in FX_TRIM_DB) FX_TRIM[k] = dB(FX_TRIM_DB[k]);
  const inKey = (H, lo, hi) => { const out = []; for (let m = lo; m <= hi; m++) if (H.penta.includes(pc(m - H.key))) out.push(m); return out; };
  const third = (H) => (H.penta.includes(4) ? 4 : 3);

  function burst(ch, t, o) {
    const { ac, kit } = ch, src = Noise(ac, o.buf || kit.white, t, t + o.a + o.d + 0.06, ch.R);
    const fl = Filt(ac, o.type || 'bandpass', o.f, o.q || 1), gg = Gain(ac), nodes = [fl, gg];
    if (o.f1) { fl.frequency.setValueAtTime(o.f, t); fl.frequency.exponentialRampToValueAtTime(o.f1, t + o.a + o.d); }
    let last = fl;
    if (o.hp) { const h = Filt(ac, 'highpass', o.hp, 0.6); fl.connect(h); last = h; nodes.push(h); }
    perc(gg.gain, t, o.peak, o.a, o.d);
    src.connect(fl); chain(last, gg, ch.input); own(ch.owner, src, nodes);
  }
  function sweep(ch, t, f0, f1, dt, peak, a, d, type) {
    const { ac } = ch, o = Osc(ac, type || 'sine', f0, t, t + a + d + 0.05), gg = Gain(ac);
    o.frequency.exponentialRampToValueAtTime(f1, t + dt);
    perc(gg.gain, t, peak, a, d);
    chain(o, gg, ch.input); own(ch.owner, o, [gg]);
  }
  // breath through two vowel formants (+ an optional voiced buzz); returns the envelope param
  function voice(S, t, o) {
    const { ac, kit } = S, ch = S.strip({ room: o.room == null ? 0.22 : o.room, hall: o.hall || 0.08, pan: o.pan || 0 });
    const end = t + o.dur + 0.05;
    const mix = Gain(ac, 1), b1 = Filt(ac, 'bandpass', o.f1[0], o.q1 || 3), b2 = Filt(ac, 'bandpass', o.f2[0], o.q2 || 4);
    const g2 = Gain(ac, 0.7), sum = Gain(ac, 1), hp = Filt(ac, 'highpass', o.hp || 250, 0.6), env = Gain(ac);
    b1.frequency.setValueAtTime(o.f1[0], t); b1.frequency.linearRampToValueAtTime(o.f1[1], t + o.dur);
    b2.frequency.setValueAtTime(o.f2[0], t); b2.frequency.linearRampToValueAtTime(o.f2[1], t + o.dur);
    mix.connect(b1); mix.connect(b2); b1.connect(sum); chain(b2, g2, sum); chain(sum, hp, env, ch.input);
    const src = Noise(ac, kit.white, t, end, S.R);
    src.connect(mix);
    own(S.owner, src, [mix, b1, b2, g2, sum, hp, env]);
    if (o.voiced) {
      const vo = Osc(ac, kit.wave.soft, o.voiced.f0[0], t, end), vg = Gain(ac, o.voiced.amt);
      vo.frequency.exponentialRampToValueAtTime(o.voiced.f0[1], t + o.dur);
      chain(vo, vg, mix); own(S.owner, vo, [vg]);
    }
    return env.gain;
  }

  // magic: 5 → 8 (the theme's leap) and a quiet third, on a bell
  FX.chime = (S, t, g, H) => {
    const ch = S.strip({ hall: 0.6, delay: 0.22, pan: 0.12 }), k = H.key;
    [[19, 1, 0], [24, 0.85, 0.13], [24 + third(H), 0.38, 0.29]].forEach(([s, v, dt]) =>
      I.partials(ch, t + dt, mtof(k + s), g * v, [[1, 1, 3.2], [2, 0.3, 1.4], [3, 0.09, 0.6], [4.2, 0.04, 0.3]], 0.17));
    return 4;
  };
  // a string chord breathing in, with air rising underneath
  FX.swell = (S, t, g, H) => {
    const { ac, kit } = S, ch = S.strip({ hall: 0.55 }), k = H.key;
    const notes = voiceLead(H.chord.map((x) => k + x), null, 57, 76, 4);
    const lp = Filt(ac, 'lowpass', 500, 0.6);
    lp.frequency.setValueAtTime(500, t); lp.frequency.exponentialRampToValueAtTime(2600, t + 1.8); lp.frequency.exponentialRampToValueAtTime(900, t + 3.2);
    lp.connect(ch.input);
    let first = true;
    for (const m of notes) for (const det of [-6, 6]) {
      const o = Osc(ac, kit.wave.string, mtof(m), t, t + 3.4), gg = Gain(ac), P = gg.gain;
      o.detune.value = det;
      P.setValueAtTime(0, t); P.linearRampToValueAtTime(0.012 * g, t + 0.9); P.linearRampToValueAtTime(0.028 * g, t + 1.8);
      P.exponentialRampToValueAtTime(EPS, t + 3.3); P.linearRampToValueAtTime(0, t + 3.32);
      chain(o, gg, lp); own(S.owner, o, first ? [gg, lp] : [gg]); first = false;
    }
    const src = Noise(ac, kit.pinkSt, t, t + 2.6, S.R), bp = Filt(ac, 'bandpass', 600, 0.8), ng = Gain(ac), N = ng.gain;
    bp.frequency.setValueAtTime(600, t); bp.frequency.exponentialRampToValueAtTime(5200, t + 1.9);
    N.setValueAtTime(0, t); N.linearRampToValueAtTime(0.003 * g, t + 0.8); N.exponentialRampToValueAtTime(0.04 * g, t + 1.85);
    N.exponentialRampToValueAtTime(EPS, t + 2.5); N.linearRampToValueAtTime(0, t + 2.52);
    chain(src, bp, ng, ch.input); own(S.owner, src, [bp, ng]);
    return 3.6;
  };
  FX.whoosh = (S, t, g) => {
    const { ac, kit } = S, R = S.R, dir = R() < 0.5 ? -1 : 1, ch = S.strip({ hall: 0.14 });
    const src = Noise(ac, kit.pink, t, t + 1, R), hp = Filt(ac, 'highpass', 140, 0.6), bp = Filt(ac, 'bandpass', 350, 1.1), p = Pan(ac, -0.6 * dir), gg = Gain(ac), P = gg.gain;
    bp.frequency.setValueAtTime(350, t); bp.frequency.exponentialRampToValueAtTime(2400, t + 0.38); bp.frequency.exponentialRampToValueAtTime(520, t + 0.85);
    if (p.pan) { p.pan.setValueAtTime(-0.6 * dir, t); p.pan.linearRampToValueAtTime(0.6 * dir, t + 0.85); }
    P.setValueAtTime(0, t); P.linearRampToValueAtTime(0.5 * g, t + 0.32); P.linearRampToValueAtTime(0.36 * g, t + 0.45); P.linearRampToValueAtTime(0, t + 0.9);
    chain(src, hp, bp, gg, p, ch.input); own(S.owner, src, [hp, bp, gg, p]);
    return 1.1;
  };
  FX.sparkle = (S, t, g, H) => {
    const chs = [-0.6, 0, 0.6].map((pan) => S.strip({ hall: 0.5, delay: 0.3, pan })), notes = inKey(H, 86, 103), R = S.R;
    let tt = t, idx = notes.length - 1;
    for (let i = 0; i < 9; i++) {
      I.glock(R.pick(chs), tt, notes[clamp(idx, 0, notes.length - 1)], g * (1 - i * 0.07) * R.range(0.8, 1));
      idx -= R.pick([1, 1, 2, -1]); tt += R.range(0.045, 0.075);
    }
    return 2.2;
  };
  FX.pop = (S, t, g) => {
    const ch = S.strip({ room: 0.2 });
    sweep(ch, t, 320, 1250, 0.03, 0.4 * g, 0.002, 0.07);
    burst(ch, t, { f: 2500, q: 1.5, a: 0.0005, d: 0.006, peak: 0.15 * g });
    return 0.3;
  };
  FX.bird = (S, t, g) => {
    const R = S.R, ch = S.strip({ pan: R.range(-0.7, 0.7), hall: 0.2 });
    return bird(ch, t, R.pick(['warble', 'feebee', 'chirp', 'warble', 'trill']), R, 1.6 * g) + 0.3;
  };
  function step1(ch, t, v, R) {
    burst(ch, t, { buf: ch.kit.pink, type: 'lowpass', f: 340, q: 0.7, a: 0.003, d: 0.08, peak: 0.28 * v });
    burst(ch, t + 0.004, { buf: ch.kit.pink, f: 520, q: 1.2, a: 0.002, d: 0.05, peak: 0.3 * v });
    for (let j = 0; j < 4; j++) burst(ch, t + 0.012 + j * R.range(0.012, 0.022), { f: R.range(1700, 3200), q: 0.9, a: 0.001, d: R.range(0.015, 0.035), peak: 0.5 * v * R.range(0.6, 1) });
  }
  FX.footsteps = (S, t, g) => {
    const R = S.R, ch = S.strip({ room: 0.15, pan: R.range(-0.25, 0.25) });
    let tt = t;
    for (let i = 0; i < 5; i++) { step1(ch, tt, g * Math.pow(0.86, i) * R.range(0.85, 1.05), R); tt += R.range(0.44, 0.52); }
    return tt - t + 0.3;
  };
  FX.step = (S, t, g) => { step1(S.strip({ room: 0.18 }), t, g, S.R); return 0.4; };
  FX.heartbeat = (S, t, g) => {
    const ch = S.strip({ room: 0.12 });
    [[0, 1], [0.2, 0.62], [0.86, 0.9], [1.06, 0.55]].forEach(([dt, v]) => {
      sweep(ch, t + dt, 64, 42, 0.12, 0.4 * g * v, 0.005, 0.17);
      sweep(ch, t + dt, 165, 110, 0.12, 0.34 * g * v, 0.005, 0.1);
      burst(ch, t + dt, { buf: ch.kit.pink, f: 220, q: 1.2, a: 0.004, d: 0.07, peak: 0.9 * g * v });
    });
    return 1.6;
  };
  FX.tap = (S, t, g) => {
    const ch = S.strip({ room: 0.25 });
    burst(ch, t, { f: 2400, q: 2, a: 0.0008, d: 0.028, peak: 0.42 * g });
    sweep(ch, t, 880, 800, 0.05, 0.16 * g, 0.001, 0.07);
    return 0.3;
  };
  FX.thud = (S, t, g) => {
    const ch = S.strip({ room: 0.3 });
    sweep(ch, t, 95, 45, 0.18, 0.35 * g, 0.003, 0.26);
    sweep(ch, t, 190, 90, 0.12, 0.3 * g, 0.003, 0.12);
    burst(ch, t, { buf: ch.kit.pink, type: 'lowpass', f: 420, q: 0.7, a: 0.002, d: 0.12, peak: 0.45 * g });
    burst(ch, t, { buf: ch.kit.pink, f: 260, q: 1.3, a: 0.002, d: 0.09, peak: 1.6 * g });
    return 0.6;
  };
  // the shop's door bell: a small brass bell on a spring, struck a few times
  FX.bell = (S, t, g) => {
    const ch = S.strip({ room: 0.3, hall: 0.15, pan: 0.2 }), R = S.R;
    [[0, 1], [0.085, 0.72], [0.19, 0.55], [0.31, 0.4], [0.47, 0.28], [0.64, 0.17]].forEach(([dt, v]) => {
      I.partials(ch, t + dt, 1650 * R.range(0.997, 1.003), g * v, [[1, 1, 1.6], [2.32, 0.5, 0.8], [3.94, 0.25, 0.45], [5.4, 0.12, 0.22]], 0.13);
      burst(ch, t + dt, { f: 5200, q: 1.2, a: 0.0005, d: 0.006, peak: 0.08 * g * v });
    });
    return 2.4;
  };
  // the old brass register: keys, ka-CHING, the drawer rattling open
  FX.register = (S, t, g) => {
    const ch = S.strip({ room: 0.35, hall: 0.08, pan: -0.1 }), R = S.R, { ac, kit } = S;
    [0, 0.12].forEach((dt) => { burst(ch, t + dt, { f: 1800, q: 1.5, a: 0.001, d: 0.03, peak: 0.4 * g }); burst(ch, t + dt + 0.004, { f: 420, q: 2, a: 0.002, d: 0.06, peak: 0.35 * g }); });
    [[0.26, 1], [0.32, 0.45]].forEach(([dt, v]) => I.partials(ch, t + dt, 1760, g * v, [[1, 1, 1.3], [2, 0.32, 0.55], [2.76, 0.2, 0.35], [5.4, 0.05, 0.12]], 0.16));
    const src = Noise(ac, kit.white, t + 0.3, t + 0.64, R), bp = Filt(ac, 'bandpass', 900, 1.2), gg = Gain(ac), P = gg.gain;
    bp.frequency.setValueAtTime(900, t + 0.3); bp.frequency.linearRampToValueAtTime(1600, t + 0.56);
    P.setValueAtTime(0, t + 0.3);
    for (let i = 0; i < 9; i++) { const s = t + 0.3 + i * 0.028; P.linearRampToValueAtTime(0.12 * g * R.range(0.5, 1), s + 0.008); P.linearRampToValueAtTime(0.03 * g, s + 0.026); }
    P.linearRampToValueAtTime(0, t + 0.6);
    chain(src, bp, gg, ch.input); own(S.owner, src, [bp, gg]);
    sweep(ch, t + 0.6, 140, 70, 0.08, 0.5 * g, 0.003, 0.11);
    burst(ch, t + 0.6, { f: 700, q: 1, a: 0.002, d: 0.06, peak: 0.3 * g });
    return 1.8;
  };
  // bills slapped on the counter, a coin settling
  FX.cash = (S, t, g) => {
    const ch = S.strip({ room: 0.3 });
    [0, 0.16, 0.3].forEach((dt, i) => {
      burst(ch, t + dt, { f: 1400, q: 0.7, a: 0.002, d: 0.07, peak: 0.42 * g * (1 - i * 0.15), hp: 400 });
      sweep(ch, t + dt, 180, 110, 0.04, 0.22 * g, 0.002, 0.05);
    });
    I.partials(ch, t + 0.46, 3200, g, [[1, 1, 0.25], [2.7, 0.5, 0.15], [5.1, 0.25, 0.08]], 0.1);
    I.partials(ch, t + 0.53, 3550, g * 0.6, [[1, 1, 0.2], [2.7, 0.5, 0.12]], 0.1);
    return 1;
  };
  FX.sigh = (S, t, g) => {
    const P = voice(S, t, { dur: 1.4, f1: [760, 480], f2: [1250, 950], q1: 2.5, q2: 3, voiced: { f0: [150, 104], amt: 0.06 }, hp: 200 });
    P.setValueAtTime(0, t); P.linearRampToValueAtTime(0.5 * g, t + 0.2); P.exponentialRampToValueAtTime(0.18 * g, t + 0.65);
    P.exponentialRampToValueAtTime(EPS, t + 1.4); P.linearRampToValueAtTime(0, t + 1.42);
    return 1.6;
  };
  // a giggle: a clarinet tumbling down the scale, each note a breathy "ha"
  FX.laugh = (S, t, g, H) => {
    const ch = S.strip({ room: 0.22, hall: 0.1, pan: 0.05 }), k = H.key, sc = inKey(H, k + 7, k + 21).reverse();
    let tt = t;
    for (let i = 0; i < 6; i++) {
      const m = sc[Math.min(sc.length - 1, i)];
      I.clarinet(ch, tt, m, g * (0.75 - i * 0.07), 0.075);
      const f0 = mtof(m - 24), P = voice(S, tt, { dur: 0.1, f1: [820, 760], f2: [1300, 1220], voiced: { f0: [f0, f0 * 0.92], amt: 0.25 }, hp: 300 });
      P.setValueAtTime(0, tt); P.linearRampToValueAtTime(0.9 * g * (1 - i * 0.1), tt + 0.012); P.exponentialRampToValueAtTime(EPS, tt + 0.1); P.linearRampToValueAtTime(0, tt + 0.105);
      tt += 0.125 - i * 0.004;
    }
    return 1.2;
  };
  // Embarrassment's dry "heh-heh-heh": his bassoon, low
  FX.chuckle = (S, t, g, H) => {
    const ch = S.strip({ room: 0.22, hall: 0.08, pan: -0.1 }), k = H.key, lo = inKey(H, k - 12, k).reverse();
    [0, 0.17, 0.33].forEach((dt, i) => {
      const m = lo[Math.min(lo.length - 1, 1 + i)] - 12, f0 = mtof(m + 12);
      I.bassoon(ch, t + dt, m, g * (0.8 - i * 0.12), 0.09, { a: 0.012, r: 0.05 });
      const P = voice(S, t + dt, { dur: 0.09, f1: [600, 560], f2: [1700, 1600], voiced: { f0: [f0, f0 * 0.95], amt: 0.3 }, hp: 200 });
      P.setValueAtTime(0, t + dt); P.linearRampToValueAtTime(0.8 * g, t + dt + 0.01); P.exponentialRampToValueAtTime(EPS, t + dt + 0.09); P.linearRampToValueAtTime(0, t + dt + 0.095);
    });
    return 0.9;
  };
  FX.gasp = (S, t, g) => {
    const P = voice(S, t, { dur: 0.32, f1: [900, 1100], f2: [1800, 2300], q1: 1.5, q2: 2, hp: 700 });
    P.setValueAtTime(0, t); P.linearRampToValueAtTime(0.25 * g, t + 0.12); P.linearRampToValueAtTime(0.7 * g, t + 0.24); P.linearRampToValueAtTime(0, t + 0.3);
    const ch = S.strip({ room: 0.2, hall: 0.1 }), { ac, kit } = S, o = Osc(ac, kit.wave.flute, 620, t + 0.04, t + 0.4), gg = Gain(ac);
    o.frequency.exponentialRampToValueAtTime(1240, t + 0.25);
    gg.gain.setValueAtTime(0, t + 0.04); gg.gain.linearRampToValueAtTime(0.05 * g, t + 0.2); gg.gain.linearRampToValueAtTime(0, t + 0.34);
    chain(o, gg, ch.input); own(S.owner, o, [gg]);
    return 0.6;
  };
  // a cartoon spring: rising twang with a decaying wobble
  FX.boing = (S, t, g) => {
    const { ac } = S, ch = S.strip({ room: 0.15 }), end = t + 0.75;
    const o = Osc(ac, 'triangle', 170, t, end), lp = Filt(ac, 'lowpass', 1400, 5), gg = Gain(ac);
    o.frequency.exponentialRampToValueAtTime(340, t + 0.4);
    const lfo = Osc(ac, 'sine', 14, t, end), dg = Gain(ac), lg = Gain(ac);
    dg.gain.setValueAtTime(160, t); dg.gain.exponentialRampToValueAtTime(8, t + 0.7);
    lg.gain.setValueAtTime(700, t); lg.gain.exponentialRampToValueAtTime(40, t + 0.7);
    chain(lfo, dg, o.detune); lfo.connect(lg); lg.connect(lp.frequency);
    perc(gg.gain, t, 0.5 * g, 0.004, 0.62);
    chain(o, lp, gg, ch.input); own(S.owner, o, [lp, gg]); own(S.owner, lfo, [dg, lg]);
    return 0.9;
  };
  // a phone notification: two bell notes from the score's scale (a fan of dings makes a tune)
  FX.ding = (S, t, g, H) => {
    const R = S.R, ch = S.strip({ room: 0.15, hall: 0.12, pan: R.range(-0.3, 0.3) }), notes = inKey(H, H.key + 19, H.key + 31);
    const i = R.int(0, notes.length - 2);
    I.partials(ch, t, mtof(notes[i]), g, [[1, 1, 0.5], [2, 0.25, 0.2], [3, 0.08, 0.08]], 0.16);
    I.partials(ch, t + 0.1, mtof(notes[i + 1]), g * 0.9, [[1, 1, 0.65], [2, 0.25, 0.25], [3, 0.08, 0.08]], 0.16);
    return 0.9;
  };
  // muttered words: two whisperers, syllables of breath through shifting vowels
  FX.whisper = (S, t, g) => {
    const R = S.R;
    for (const [off, pan, amt] of [[0, -0.25, 1], [0.11, 0.3, 0.7]]) {
      let tt = t + off;
      for (let i = 0; i < 7; i++) {
        const d = R.range(0.09, 0.2), f1 = R.range(450, 900), f2 = R.range(1300, 2500), pk = 0.55 * g * amt * R.range(0.7, 1);
        const P = voice(S, tt, { dur: d, f1: [f1, f1 * R.range(0.85, 1.15)], f2: [f2, f2 * R.range(0.85, 1.15)], q1: 4, q2: 5, hp: 500, pan, room: 0.18, hall: 0.06 });
        P.setValueAtTime(0, tt); P.linearRampToValueAtTime(pk, tt + 0.025); P.linearRampToValueAtTime(pk * 0.7, tt + d - 0.03); P.linearRampToValueAtTime(0, tt + d);
        if (R() < 0.35) burst(S.strip({ pan, room: 0.15 }), tt, { type: 'highpass', f: 5200, q: 0.7, a: 0.01, d: 0.05, peak: 0.07 * g * amt });
        tt += d + R.range(0.03, 0.09);
      }
    }
    return 2;
  };
  FX['car-door'] = (S, t, g) => {
    const ch = S.strip({ room: 0.12, hall: 0.05, pan: 0.15 });
    burst(ch, t, { f: 3200, q: 2, a: 0.0005, d: 0.012, peak: 0.3 * g });
    sweep(ch, t + 0.012, 78, 50, 0.15, 0.18 * g, 0.003, 0.24);
    burst(ch, t + 0.012, { buf: ch.kit.pink, type: 'lowpass', f: 520, q: 0.7, a: 0.002, d: 0.14, peak: 0.6 * g });
    burst(ch, t + 0.012, { buf: ch.kit.pink, f: 240, q: 1.5, a: 0.002, d: 0.12, peak: 2.4 * g });
    burst(ch, t + 0.014, { buf: ch.kit.pink, f: 620, q: 1.4, a: 0.002, d: 0.06, peak: 1.2 * g });
    burst(ch, t + 0.003, { f: 1250, q: 1.6, a: 0.001, d: 0.02, peak: 0.4 * g });
    burst(ch, t + 0.075, { f: 1500, q: 1.2, a: 0.002, d: 0.03, peak: 0.12 * g });
    return 0.9;
  };
  FX.engine = (S, t, g) => {
    const { ac, kit } = S, ch = S.strip({ room: 0.1, hall: 0.06 }), end = t + 3.4;
    const st = Osc(ac, 'sawtooth', 36, t, t + 0.75), sl = Filt(ac, 'lowpass', 500, 0.8), sg = Gain(ac);
    sg.gain.setValueAtTime(0, t);
    for (let i = 0; i < 6; i++) { const s = t + i * 0.12; sg.gain.linearRampToValueAtTime(0.16 * g, s + 0.03); sg.gain.linearRampToValueAtTime(0.03 * g, s + 0.11); }
    sg.gain.linearRampToValueAtTime(0, t + 0.74);
    chain(st, sl, sg, ch.input); own(S.owner, st, [sl, sg]);
    const t1 = t + 0.72, o = Osc(ac, 'sawtooth', 30, t1, end), lp = Filt(ac, 'lowpass', 300, 0.9), hp = Filt(ac, 'highpass', 45, 0.6), gg = Gain(ac), P = gg.gain;
    o.frequency.linearRampToValueAtTime(58, t1 + 0.35); o.frequency.exponentialRampToValueAtTime(34, t1 + 1.1);
    lp.frequency.setValueAtTime(400, t1); lp.frequency.linearRampToValueAtTime(1300, t1 + 0.35); lp.frequency.exponentialRampToValueAtTime(600, t1 + 1.2);
    P.setValueAtTime(0, t1); P.linearRampToValueAtTime(0.32 * g, t1 + 0.08); P.linearRampToValueAtTime(0.22 * g, t1 + 1.2); P.setValueAtTime(0.22 * g, end - 0.8); P.linearRampToValueAtTime(0, end);
    chain(o, hp, lp, gg, ch.input); own(S.owner, o, [hp, lp, gg]);
    const nz = Noise(ac, kit.pink, t1, end, S.R), nl = Filt(ac, 'lowpass', 240, 0.6), ng = Gain(ac), N = ng.gain;
    N.setValueAtTime(0, t1); N.linearRampToValueAtTime(0.25 * g, t1 + 0.1); N.linearRampToValueAtTime(0.12 * g, t1 + 1.2); N.setValueAtTime(0.12 * g, end - 0.8); N.linearRampToValueAtTime(0, end);
    chain(nz, nl, ng, ch.input); own(S.owner, nz, [nl, ng]);
    return 3.6;
  };
  // a falling petal: air, and three soft notes drifting down
  FX.petal = (S, t, g, H) => {
    const ch = S.strip({ hall: 0.5, delay: 0.2, pan: 0.2 }), notes = inKey(H, H.key + 24, H.key + 36).reverse();
    burst(ch, t, { buf: S.kit.pink, f: 3000, q: 0.8, a: 0.25, d: 0.5, peak: 0.12 * g });
    [0, 0.22, 0.46].forEach((dt, i) => I.celesta(ch, t + 0.08 + dt, notes[Math.min(notes.length - 1, i * 2)], g * (0.42 - i * 0.1)));
    return 2.4;
  };
  // a page turning: a crinkle, then the flap
  FX.paper = (S, t, g) => {
    const { ac, kit } = S, R = S.R, ch = S.strip({ room: 0.2, pan: -0.1 });
    const src = Noise(ac, kit.white, t, t + 0.6, R), hp = Filt(ac, 'highpass', 1200, 0.6), bp = Filt(ac, 'bandpass', 3500, 0.6), gg = Gain(ac), P = gg.gain;
    P.setValueAtTime(0, t);
    let tt = t;
    for (let i = 0; i < 12; i++) { const a = 0.3 * g * R.range(0.3, 1) * Math.sin((Math.PI * (i + 0.5)) / 12); P.linearRampToValueAtTime(a, tt + 0.006); P.linearRampToValueAtTime(a * 0.25, tt + 0.026); tt += R.range(0.022, 0.034); }
    P.linearRampToValueAtTime(0, tt + 0.03);
    chain(src, hp, bp, gg, ch.input); own(S.owner, src, [hp, bp, gg]);
    burst(ch, tt + 0.02, { buf: kit.pink, type: 'lowpass', f: 900, q: 0.7, a: 0.003, d: 0.08, peak: 0.35 * g });
    return 0.8;
  };
  // a muddy boot: a wet resonance sliding down, a little bubble
  FX.squelch = (S, t, g) => {
    const { ac, kit } = S, ch = S.strip({ room: 0.15 }), src = Noise(ac, kit.pink, t, t + 0.3, S.R), bp = Filt(ac, 'bandpass', 900, 5), gg = Gain(ac);
    bp.frequency.setValueAtTime(950, t); bp.frequency.exponentialRampToValueAtTime(260, t + 0.18);
    perc(gg.gain, t, 0.9 * g, 0.004, 0.2);
    chain(src, bp, gg, ch.input); own(S.owner, src, [bp, gg]);
    sweep(ch, t + 0.01, 330, 150, 0.1, 0.1 * g, 0.002, 0.12);
    burst(ch, t + 0.14, { f: 1600, q: 3, a: 0.002, d: 0.03, peak: 0.12 * g });
    return 0.45;
  };
  FX.clock = (S, t, g) => {
    const ch = S.strip({ room: 0.3, hall: 0.1, pan: 0.3 });
    for (let i = 0; i < 6; i++) I.tick(ch, t + i * 0.3, i % 2 ? 2150 : 2700, 0.42 * g, 0.03);
    return 2.1;
  };
  // a pencil (or a broom): short rough strokes
  FX.scratch = (S, t, g) => {
    const { ac, kit } = S, R = S.R, ch = S.strip({ room: 0.15, pan: R.range(-0.2, 0.2) });
    let tt = t;
    const n = R.int(2, 3);
    for (let s = 0; s < n; s++) {
      const d = R.range(0.14, 0.22), src = Noise(ac, kit.white, tt, tt + d + 0.05, R), bp = Filt(ac, 'bandpass', 2600, 0.9), hp = Filt(ac, 'highpass', 1400, 0.6), gg = Gain(ac), P = gg.gain;
      bp.frequency.setValueAtTime(2600, tt); bp.frequency.linearRampToValueAtTime(3800, tt + d);
      P.setValueAtTime(0, tt);
      for (let j = 0; j * 0.012 < d - 0.012; j++) P.linearRampToValueAtTime(0.3 * g * R.range(0.4, 1) * Math.sin((Math.PI * (j * 0.012 + 0.006)) / d), tt + j * 0.012 + 0.006);
      P.linearRampToValueAtTime(0, tt + d);
      chain(src, bp, hp, gg, ch.input); own(S.owner, src, [bp, hp, gg]);
      tt += d + R.range(0.06, 0.12);
    }
    return tt - t + 0.2;
  };
  FX.breath = (S, t, g) => {
    const Pi = voice(S, t, { dur: 0.85, f1: [1100, 1500], f2: [2400, 2800], q1: 1.2, q2: 1.5, hp: 500, room: 0.15, hall: 0.12 });
    Pi.setValueAtTime(0, t); Pi.linearRampToValueAtTime(0.18 * g, t + 0.6); Pi.linearRampToValueAtTime(0, t + 0.85);
    const t2 = t + 0.95, Pe = voice(S, t2, { dur: 1.3, f1: [800, 600], f2: [1300, 1100], q1: 1.4, q2: 1.8, hp: 250, room: 0.15, hall: 0.12 });
    Pe.setValueAtTime(0, t2); Pe.linearRampToValueAtTime(0.32 * g, t2 + 0.14); Pe.exponentialRampToValueAtTime(EPS, t2 + 1.3); Pe.linearRampToValueAtTime(0, t2 + 1.31);
    return 2.6;
  };
  FX.wind = (S, t, g) => {
    const { ac, kit } = S, ch = S.strip({ hall: 0.1 }), src = Noise(ac, kit.pinkSt, t, t + 3, S.R), hp = Filt(ac, 'highpass', 90, 0.5), lp = Filt(ac, 'lowpass', 300, 0.7), gg = Gain(ac), P = gg.gain;
    lp.frequency.setValueAtTime(300, t); lp.frequency.exponentialRampToValueAtTime(1500, t + 1.2); lp.frequency.exponentialRampToValueAtTime(360, t + 2.8);
    P.setValueAtTime(0, t); P.linearRampToValueAtTime(0.35 * g, t + 1.1); P.linearRampToValueAtTime(0, t + 2.9);
    chain(src, hp, lp, gg, ch.input); own(S.owner, src, [hp, lp, gg]);
    return 3.1;
  };
  // high partials from the scale, each trembling at its own rate
  FX.shimmer = (S, t, g, H) => {
    const { ac } = S, notes = inKey(H, H.key + 24, H.key + 38), R = S.R;
    for (let i = 0; i < 7; i++) {
      const m = notes[(i * 2) % notes.length], ch = S.strip({ hall: 0.6, delay: 0.2, pan: (i / 6 - 0.5) * 1.4 }), st = t + i * 0.07;
      const o = Osc(ac, 'sine', mtof(m), st, st + 3.3), tr = Gain(ac, 1), lfo = Osc(ac, 'sine', R.range(4.5, 7), st, st + 3.3), lg = Gain(ac, 0.4), gg = Gain(ac);
      sus(gg.gain, st, 0.045 * g, 0.5, 1.4, 1.2);
      chain(lfo, lg, tr.gain); chain(o, tr, gg, ch.input);
      own(S.owner, o, [tr, gg]); own(S.owner, lfo, [lg]);
    }
    return 3.4;
  };
  // the flower opens: a harp sweeping up the scale into a bell chord, strings breathing in
  FX.bloom = (S, t, g, H) => {
    const ch = S.strip({ hall: 0.55, delay: 0.1, pan: -0.15 }), k = H.key, run = inKey(H, k - 12, k + 24);
    run.forEach((m, i) => I.pluck(ch, t + i * 0.045, m, g * (0.35 + (0.35 * i) / run.length), { decay: 2.8 }));
    const top = t + run.length * 0.045, bell = S.strip({ hall: 0.6, delay: 0.25, pan: 0.15 });
    [24, 24 + third(H), 31].forEach((s, i) => I.celesta(bell, top + i * 0.03, k + s, g * 0.6));
    FX.swell(S, t + 0.1, g * 0.7, H);
    return 4.2;
  };

  /* ==========================================================================
     The engine: film clock ↔ audio clock, the mood timeline, crossfades, cues.
     ========================================================================== */
  // contiguous mood segments [{mood, t0, t1, i, key}] from the scene list
  function moodTimeline(scenes) {
    const list = (scenes || []).filter((s) => s && typeof s.start === 'number' && isFinite(s.start)).slice().sort((a, b) => a.start - b.start);
    const raw = [];
    let total = 0;
    for (const sc of list) {
      const d = +sc.duration || 0;
      total = Math.max(total, sc.start + d);
      let ms = null;
      if (Array.isArray(sc.moods) && sc.moods.length) ms = sc.moods.filter((m) => Array.isArray(m) && typeof m[1] === 'string').map((m) => [sc.start + clamp(+m[0] || 0, 0, d), m[1]]).sort((a, b) => a[0] - b[0]);
      else if (typeof sc.mood === 'string') ms = [[sc.start, sc.mood]];
      if (ms) for (const p of ms) if (MOODS[p[1]]) raw.push(p); // unknown moods: ignored (the previous mood continues)
    }
    const pts = [];
    for (const p of raw) {
      if (pts.length && Math.abs(pts[pts.length - 1][0] - p[0]) < 1e-6) pts.pop();
      if (pts.length && pts[pts.length - 1][1] === p[1]) continue;
      pts.push([p[0], p[1]]);
    }
    if (!pts.length) pts.push([0, 'silence']);
    pts[0][0] = Math.min(0, pts[0][0]);
    return pts.map(([t, m], i) => ({ mood: m, t0: t, t1: i + 1 < pts.length ? pts[i + 1][0] : Math.max(total, t + 1), i, key: m + '@' + t.toFixed(3) }));
  }

  function Engine(ac, offline) {
    this.ac = ac; this.offline = !!offline;
    this.kit = makeKit(ac);
    this.mix = makeMixer(this.kit, ac.destination);
    this.beds = []; this.cur = null; this.fx = [];
    this.playing = false; this.muted = false; this.speed = 1;
    this.anchor = { c: 0, f: 0 };
    this.lastT = 0; this.seekAt = -1e9; this.prevSeekAt = -1e9; this.scrub = false; this.needSync = false; this.lastSync = -1e9;
    this.teardownAt = 0; this.sig = null; this.tl = moodTimeline([]);
    this.log = []; this.errors = []; this.moodGain = {};
  }
  const EP = Engine.prototype;
  EP.err = function (e) {
    if (this.errors.length < 30) this.errors.push(String((e && e.stack) || e));
    if (!this.offline && this.errors.length === 1) console.warn('[audio]', e);
  };
  EP.note = function (ev) { this.log.push(ev); if (this.log.length > 3000) this.log.splice(0, 1000); };
  EP.filmToCtx = function (T) { return this.anchor.c + (T - this.anchor.f) / this.speed; };
  EP.ctxToFilm = function (c) { return this.anchor.f + (c - this.anchor.c) * this.speed; };
  EP.reanchor = function (T, now) { this.anchor = { c: now, f: T }; };
  EP.timeline = function (scenes) {
    const last = scenes && scenes.length ? scenes[scenes.length - 1] : null;
    const sig = scenes ? scenes.length + ':' + (last ? last.start + '+' + last.duration : '') : '';
    if (sig !== this.sig) { this.sig = sig; this.tl = moodTimeline(scenes); }
    return this.tl;
  };
  EP.segAt = function (T) { let s = this.tl[0]; for (const x of this.tl) if (T >= x.t0 - 1e-9) s = x; return s; };
  EP.startBed = function (seg, T, now, fade) {
    const bed = new Bed(this, seg, T - seg.t0);
    bed.fadeIn(now, now + Math.max(0.05, fade));
    this.beds.push(bed); this.cur = bed;
    this.note({ type: 'bed', mood: seg.mood, T: +T.toFixed(3), p0: +(T - seg.t0).toFixed(3) });
    return bed;
  };
  EP.releaseBeds = function (now, fade) { for (const b of this.beds) if (!b.out) b.fadeOut(now, now + Math.max(0.02, fade)); this.cur = null; };
  EP.rebuild = function (T, now, fade) {
    this.releaseBeds(now, Math.min(0.3, fade));
    const seg = this.segAt(T);
    if (seg) this.startBed(seg, T, now, fade);
    this.lastSync = now;
  };
  // keep the right bed playing; plan the crossfade so it is centred on the cut
  EP.follow = function (T, now) {
    const seg = this.segAt(T);
    if (!seg) return;
    const nx = this.tl[seg.i + 1], pre = !!nx && T >= nx.t0 - PREROLL, want = pre ? nx : seg;
    if (this.cur && this.cur.seg.key === want.key) return;
    const live = this.beds.find((b) => !b.out && b.seg.key === want.key);
    if (live) { this.cur = live; return; }
    if (pre && this.cur && this.cur.seg.key === seg.key) {
      const d = Math.max(0.3, this.filmToCtx(nx.t0 + (XFADE - PREROLL)) - now);
      this.releaseBeds(now, d);
      this.startBed(nx, T, now, d);
    } else {
      this.releaseBeds(now, 1.2);
      this.startBed(want, T, now, 1.0);
    }
  };
  EP.reap = function (now) {
    if (this.beds.some((b) => b.out && now > b.out + 0.05)) {
      this.beds = this.beds.filter((b) => { if (b.out && now > b.out + 0.05) { b.kill(now + 0.02); return false; } return true; });
    }
    if (this.fx.length) this.fx = this.fx.filter((f) => { if (now > f.end && !f.owner.srcs.size) { f.done(); return false; } return true; });
  };
  EP.harmony = function () {
    const b = this.cur;
    if (!b) return { key: 62, penta: [0, 2, 4, 7, 9], chord: [0, 4, 7] };
    return b.harmony(this.ctxToFilm(this.ac.currentTime) - b.seg.t0);
  };
  EP.playFx = function (id, when, gain, seed) {
    const fn = FX[id];
    if (!fn) return 0;
    const g = clamp(+gain || 0, 0, 2) * (FX_TRIM[id] || 1);
    if (g < 0.005) return 0;
    const ac = this.ac, M = this.mix, owner = { srcs: new Set() };
    const outs = { dry: Gain(ac, 1), hall: Gain(ac, 1), room: Gain(ac, 1), delay: Gain(ac, 1) };
    outs.dry.connect(M.sfx); outs.hall.connect(M.hallSend); outs.room.connect(M.roomSend); outs.delay.connect(M.delaySend);
    const R = Rng(seed >>> 0 || hash(id, when)), kit = this.kit;
    const S = { ac, kit, owner, R, strip: (o) => ({ ac, kit, input: makeStrip(ac, outs, o).input, owner, R }) };
    let len = 1;
    try { len = fn(S, when, g, this.harmony()) || 1; } catch (e) { this.err(e); }
    const done = () => { for (const k in outs) { try { outs[k].disconnect(); } catch (e) { /* gone */ } } };
    this.fx.push({ id, owner, outs, end: when + len + 0.5, done });
    return len;
  };
  EP.killFx = function (now) {
    for (const f of this.fx) {
      if (f.killed) continue;
      f.killed = true;
      for (const k in f.outs) f.outs[k].gain.setTargetAtTime(0, now, 0.012);
      stopAll(f.owner, now + 0.08);
      f.end = Math.min(f.end, now + 0.12);
    }
  };
  // fire every cue whose film time lies in (T0, T1]
  EP.cues = function (T0, T1, now, scenes) {
    if (!(T1 > T0) || T1 - T0 > Math.max(0.5, 0.25 * this.speed)) return;
    for (const sc of scenes) {
      if (!sc || !Array.isArray(sc.sfx) || typeof sc.start !== 'number') continue;
      if (sc.start > T1 || sc.start + (+sc.duration || 0) + 5 < T0) continue;
      for (const c of sc.sfx) {
        if (!Array.isArray(c) || typeof c[1] !== 'string') continue;
        const ct = sc.start + +c[0];
        if (!(ct > T0 && ct <= T1) || !FX[c[1]]) continue;
        const gain = c[2] && typeof c[2].gain === 'number' ? c[2].gain : 1;
        const when = now + 0.01 + Math.max(-0.01, (ct - T1) / this.speed);
        this.playFx(c[1], when, gain, hash(c[1], ct.toFixed(3)));
        this.note({ type: 'cue', id: c[1], ct: +ct.toFixed(3), T: +T1.toFixed(4), gain });
      }
    }
  };
  EP.setMuted = function (m) {
    this.muted = !!m;
    this.mix.mute.gain.setTargetAtTime(this.muted ? 0 : 1, this.ac.currentTime, 0.12);
  };
  EP.update = function (a) {
    const now = this.ac.currentTime, T = +a.T || 0, playing = !!a.playing, speed = a.speed > 0 ? +a.speed : 1;
    const scenes = Array.isArray(a.scenes) ? a.scenes : a.scene ? [a.scene] : [];
    this.timeline(scenes);
    if (speed !== this.speed) { const f = this.ctxToFilm(now); this.speed = speed; this.reanchor(f, now); }
    let fresh = false;
    if (playing && !this.playing) { // play / resume: rebuild at the current position
      this.playing = true; this.teardownAt = 0;
      this.mix.pause.gain.setTargetAtTime(1, now, 0.08);
      this.reanchor(T, now);
      this.killFx(now);
      this.rebuild(T, now, 0.35);
      this.lastT = T; fresh = true;
      this.note({ type: 'play', T });
    } else if (!playing && this.playing) { // pause (or the end of the film: let it ring)
      this.playing = false;
      const end = this.tl.length ? this.tl[this.tl.length - 1].t1 : 0, atEnd = T >= end - 0.06, tau = atEnd ? 0.8 : 0.075;
      this.mix.pause.gain.setTargetAtTime(0, now, tau);
      this.teardownAt = now + tau * 6;
      this.note({ type: 'pause', T, atEnd });
    }
    if (a.seeked) {
      this.prevSeekAt = this.seekAt; this.seekAt = now;
      this.scrub = now - this.prevSeekAt < 0.3;
      this.killFx(now);
      this.lastT = T;
      this.note({ type: 'seek', T, scrub: this.scrub });
      if (this.playing && !fresh) {
        this.reanchor(T, now);
        if (!this.scrub && now - this.lastSync > 0.25) { this.needSync = false; this.rebuild(T, now, 0.5); }
        else { this.releaseBeds(now, 0.15); this.needSync = true; }
      }
      this.reap(now);
      return;
    }
    if (!this.playing) {
      if (this.teardownAt && now >= this.teardownAt) { this.releaseBeds(now, 0.02); this.killFx(now); this.teardownAt = 0; }
      this.lastT = T;
      this.reap(now);
      return;
    }
    // a live context the browser has suspended has a frozen clock: schedule nothing, rebuild once it runs again
    if (!this.offline && this.ac.state !== 'running') { this.stalled = true; this.lastT = T; return; }
    if (this.stalled) { this.stalled = false; this.mix.pause.gain.setTargetAtTime(1, now, 0.08); this.reanchor(T, now); this.killFx(now); this.rebuild(T, now, 0.35); }
    if (Math.abs(T - this.ctxToFilm(now)) > 0.15) this.reanchor(T, now); // the film clock lost time (a hitch)
    if (this.needSync) { if (now - this.seekAt > 0.12) { this.needSync = false; this.rebuild(T, now, 0.4); } }
    else this.follow(T, now);
    const horizon = now + LOOKAHEAD;
    for (const b of this.beds) b.advance(horizon, now);
    if (!(this.scrub && now - this.seekAt < 0.3)) this.cues(this.lastT, T, now, scenes);
    this.lastT = T;
    this.reap(now);
  };

  /* ==========================================================================
     Public API
     ========================================================================== */
  let ctx = null, eng = null, wantMuted = false, hidden = false, lastResume = 0;
  // a re-evaluated script (hot reload) must not leave the previous context playing
  try { if (g.FilmAudio && g.FilmAudio._ctx) g.FilmAudio._ctx.close(); } catch (e) { /* already closed */ }
  // browsers may suspend or interrupt the context (tab switch, phone call): any gesture revives it
  function kick() { try { if (ctx && !hidden && ctx.state !== 'running' && ctx.state !== 'closed') ctx.resume().catch(() => {}); } catch (e) { /* ignore */ } }
  function newContext() {
    try { return new AC({ latencyHint: 'interactive' }); } catch (e) { return new AC(); }
  }
  function onVisibility() {
    if (!ctx || !eng) return;
    hidden = document.hidden;
    try {
      if (hidden) { eng.mix.pause.gain.setTargetAtTime(0, ctx.currentTime, 0.04); setTimeout(() => { if (hidden && ctx.state === 'running') ctx.suspend().catch(() => {}); }, 400); }
      else if (ctx.state !== 'running') ctx.resume().catch(() => {});
    } catch (e) { /* ignore */ }
  }
  const FilmAudio = {
    init() {
      try {
        if (!AC) return Promise.resolve();
        if (!ctx) {
          ctx = newContext();
          eng = new Engine(ctx, false);
          eng.setMuted(wantMuted);
          try { const b = ctx.createBuffer(1, 1, ctx.sampleRate), s = ctx.createBufferSource(); s.buffer = b; s.connect(ctx.destination); s.start(0); } catch (e) { /* iOS unlock only */ }
          if (typeof document !== 'undefined') {
            document.addEventListener('visibilitychange', onVisibility);
            document.addEventListener('pointerdown', kick, true);
            document.addEventListener('keydown', kick, true);
          }
        }
        if (ctx.state !== 'running' && ctx.resume) {
          const r = ctx.resume();
          return Promise.race([Promise.resolve(r).catch(() => {}), new Promise((res) => setTimeout(res, 1500))]).then(() => {});
        }
      } catch (e) { try { console.warn('[audio] unavailable', e); } catch (e2) { /* ignore */ } }
      return Promise.resolve();
    },
    setMuted(m) { wantMuted = !!m; try { if (eng) eng.setMuted(wantMuted); } catch (e) { /* ignore */ } },
    get _ctx() { return ctx; },
    update(a) {
      if (!eng || !a) return;
      try {
        const wall = Date.now();
        if (ctx.state === 'suspended' && a.playing && !hidden && wall - lastResume > 2000) { lastResume = wall; ctx.resume().catch(() => {}); }
        eng.update(a);
      } catch (e) { eng.err(e); }
    },
  };

  /* ---------------- headless measurement hooks ---------------- */
  function offline(seconds, sr) {
    const oac = new OAC(2, Math.max(128, Math.ceil(seconds * sr)), sr);
    return { oac, e: new Engine(oac, true) };
  }
  function locate(scenes, T) {
    for (let i = 0; i < scenes.length; i++) if (T < scenes[i].start + scenes[i].duration || i === scenes.length - 1) return { i, lt: T - scenes[i].start };
    return { i: 0, lt: 0 };
  }
  FilmAudio.debug = {
    moods: Object.keys(MOODS), sfx: Object.keys(FX), LEVEL, FX_TRIM, MOOD_GAIN, MOODS, I, Pad,
    // one mood bed on its own, from bed position `from` (default 0)
    renderMood(name, seconds, opts) {
      opts = opts || {}; seconds = seconds || 10;
      const sr = opts.sampleRate || 44100, from = opts.from || 0, { oac, e } = offline(seconds, sr);
      e.mix.pause.gain.value = 1;
      if (MOODS[name]) {
        const seg = { mood: name, t0: 0, t1: opts.len || from + seconds, i: 0, key: name + '@0' };
        e.tl = [seg]; e.sig = 'debug';
        e.reanchor(from, 0);
        const bed = e.startBed(seg, from, 0, opts.fade == null ? 0.05 : opts.fade);
        bed.advance(seconds + 0.5, 0);
      }
      return oac.startRendering();
    },
    renderSfx(id, opts) {
      opts = opts || {};
      const sr = opts.sampleRate || 44100, { oac, e } = offline(opts.seconds || 6, sr);
      e.mix.pause.gain.value = 1;
      e.playFx(id, 0.05, opts.gain == null ? 1 : opts.gain, hash(id, 'debug'));
      return oac.startRendering();
    },
    // drive update() frame by frame through a synthetic transport, on an offline context.
    // opts: { scenes, from, duration, fps, sampleRate, speed, actions:[{at, type:'seek'|'pause'|'play', T}] }
    renderTimeline(opts) {
      opts = opts || {};
      const scenes = opts.scenes || (g.Film && g.Film.scenes) || [], fps = opts.fps || 30, dur = opts.duration || 20, sr = opts.sampleRate || 22050;
      const total = scenes.length ? scenes[scenes.length - 1].start + scenes[scenes.length - 1].duration : 0;
      const { oac, e } = offline(dur + 0.25, sr), speed = opts.speed || 1, acts = (opts.actions || []).slice().sort((a, b) => a.at - b.at);
      let T = opts.from || 0, playing = opts.playing !== false, seeked = true, ai = 0, prev = 0;
      const frames = [];
      const step = (k) => {
        const wall = k / fps;
        if (k > 0 && playing) T += (wall - prev) * speed;
        prev = wall;
        while (ai < acts.length && acts[ai].at <= wall + 1e-9) {
          const a = acts[ai++];
          if (a.type === 'seek') { T = clamp(a.T, 0, total || a.T); seeked = true; } else if (a.type === 'pause') playing = false; else if (a.type === 'play') playing = true;
        }
        if (total && T >= total) { T = total; playing = false; }
        const L = locate(scenes, T);
        frames.push({ wall, T, playing, seeked });
        e.update({ T, playing, i: L.i, lt: L.lt, scene: scenes[L.i], scenes, seeked, speed, dt: 1 / fps });
        seeked = false;
      };
      step(0);
      const n = Math.floor(dur * fps);
      let k = 1;
      const next = () => {
        if (k > n) return;
        const q = (Math.round(((k / fps) * sr) / 128) * 128) / sr;
        oac.suspend(q).then(() => { try { step(k); } catch (err) { e.err(err); } k++; next(); oac.resume(); });
      };
      next();
      return oac.startRendering().then((buffer) => ({ buffer, log: e.log, errors: e.errors, frames }));
    },
    timeline: (scenes) => moodTimeline(scenes || (g.Film && g.Film.scenes) || []),
    engine: () => eng,
    log: () => (eng ? eng.log : []),
    errors: () => (eng ? eng.errors : []),
  };

  g.FilmAudio = FilmAudio;
})(window);
