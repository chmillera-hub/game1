// ============================================================================
//  AUDIO — fully procedural score + foley (Web Audio API)
//  The audio clock drives the film clock, so picture and sound never drift.
// ============================================================================
const Sound = (() => {
  let ac = null, master, comp, verb, epochBus, musicBus, sfxBus, verbSend, noiseBuf, duck, heartBus;
  // narration: its own bus past the gates, and a duck that lowers the score under every line
  let vduck, voiceBus, voiceOut, voiceEpoch, vbuf = null, voiceReady = Promise.resolve(false);
  // with narration the score sits 2 dB lower and dips a further 7.5 dB under each line,
  // so the voice sits about 10 dB over the music
  const SCORE_TRIM = (typeof VOICE !== 'undefined' && VOICE.mp3) ? 0.8 : 1;
  const VOICE_DUCK = 0.42 * SCORE_TRIM;
  let drone = null, warmth = null, wind = null, cold = null;
  let muted = false, ok = false;

  function makeIR(seconds, decay) {
    const rate = ac.sampleRate, len = Math.floor(rate * seconds);
    const buf = ac.createBuffer(2, len, rate);
    for (let ch = 0; ch < 2; ch++) {
      const d = buf.getChannelData(ch);
      let lp = 0;
      for (let i = 0; i < len; i++) {
        const t = i / len;
        // pre-delay + soft early reflections + smooth exponential tail, gently low-passed
        const early = i < rate * 0.08 ? (Math.random() < 0.004 ? (Math.random() * 2 - 1) * 0.6 : 0) : 0;
        const tail = (Math.random() * 2 - 1) * Math.pow(1 - t, decay);
        lp += (tail - lp) * (0.25 + 0.6 * (1 - t));
        d[i] = i < rate * 0.012 ? 0 : lp * 0.9 + early;
      }
    }
    return buf;
  }

  function init(offline) {
    if (ac && !offline) return ok;
    try {
      ac = offline || new (window.AudioContext || window.webkitAudioContext)({ latencyHint: 'playback' });
    } catch (e) { ac = null; return (ok = false); }
    epochBus = null;
    comp = ac.createDynamicsCompressor();
    comp.threshold.value = -16; comp.knee.value = 14; comp.ratio.value = 3.2;
    comp.attack.value = 0.02; comp.release.value = 0.35;
    master = ac.createGain(); master.gain.value = 0.0;
    // duck: a gate for the film's true silences (the freeze, 'When they die, I die'); the heartbeat bypasses it
    duck = ac.createGain(); duck.gain.value = 1;
    vduck = ac.createGain(); vduck.gain.value = SCORE_TRIM;
    // a brick-wall safety on the sum of score and voice
    const lim = ac.createDynamicsCompressor();
    lim.threshold.value = -2; lim.knee.value = 0; lim.ratio.value = 20; lim.attack.value = 0.002; lim.release.value = 0.12;
    master.connect(duck); duck.connect(vduck); vduck.connect(comp); comp.connect(lim); lim.connect(ac.destination);
    heartBus = ac.createGain(); heartBus.gain.value = 1; heartBus.connect(vduck);
    // the narrator: close and warm, with a little of a small room around him
    voiceOut = ac.createGain(); voiceOut.gain.value = 0; voiceOut.connect(lim);
    voiceBus = ac.createGain(); voiceBus.gain.value = (typeof VOICE !== 'undefined' && VOICE.gain) || 1; voiceBus.connect(voiceOut);
    const vverb = ac.createConvolver(); vverb.buffer = makeIR(1.6, 3.4);
    const vsend = ac.createGain(); vsend.gain.value = 0.16; voiceBus.connect(vsend); vsend.connect(vverb); vverb.connect(voiceOut);
    voiceReady = loadVoice();
    verb = ac.createConvolver(); verb.buffer = makeIR(5.5, 2.6);
    const verbRet = ac.createGain(); verbRet.gain.value = 0.85;
    verb.connect(verbRet); verbRet.connect(master);
    verbSend = ac.createGain(); verbSend.gain.value = 1; verbSend.connect(verb);
    noiseBuf = ac.createBuffer(1, ac.sampleRate * 3, ac.sampleRate);
    const nd = noiseBuf.getChannelData(0);
    for (let i = 0; i < nd.length; i++) nd[i] = Math.random() * 2 - 1;
    newEpoch();
    buildBeds();
    ok = true;
    return ok;
  }

  // An "epoch" bus holds every scheduled voice. Seeking fades the old epoch out
  // (killing pending notes) and opens a fresh one.
  function newEpoch() {
    const now = ac.currentTime;
    if (epochBus) {
      const old = epochBus;
      old.gain.cancelScheduledValues(now);
      old.gain.setValueAtTime(old.gain.value, now);
      old.gain.linearRampToValueAtTime(0, now + 0.12);
      setTimeout(() => { try { old.disconnect(); } catch (e) { } }, 400);
    }
    epochBus = ac.createGain(); epochBus.gain.value = 1;
    musicBus = ac.createGain(); musicBus.gain.value = 1.8;
    sfxBus = ac.createGain(); sfxBus.gain.value = 1;
    const mv = ac.createGain(); mv.gain.value = 0.6;
    const sv = ac.createGain(); sv.gain.value = 0.35;
    musicBus.connect(epochBus); musicBus.connect(mv); mv.connect(verbSend);
    sfxBus.connect(epochBus); sfxBus.connect(sv); sv.connect(verbSend);
    epochBus.connect(master);
    if (duck) { duck.gain.cancelScheduledValues(now); duck.gain.setValueAtTime(1, now); }
    if (voiceEpoch) {
      const oldV = voiceEpoch;
      oldV.gain.cancelScheduledValues(now); oldV.gain.setValueAtTime(oldV.gain.value, now); oldV.gain.linearRampToValueAtTime(0, now + 0.12);
      setTimeout(() => { try { oldV.disconnect(); } catch (e) { } }, 400);
    }
    voiceEpoch = ac.createGain(); voiceEpoch.gain.value = 1; voiceEpoch.connect(voiceBus);
    if (vduck) { vduck.gain.cancelScheduledValues(now); vduck.gain.setValueAtTime(vduck.gain.value, now); vduck.gain.setTargetAtTime(SCORE_TRIM, now, 0.1); }
  }

  // ---------- narration
  // VOICE.mp3 is one recording of every line, laid end to end; VOICE.clips[i] = { o: offset, d: duration }
  let voiceBytes = null;
  function loadVoice() {
    if (typeof VOICE === 'undefined' || !VOICE.mp3) return Promise.resolve(false);
    if (!voiceBytes) {
      const bin = atob(VOICE.mp3); voiceBytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) voiceBytes[i] = bin.charCodeAt(i);
    }
    const ctx = ac, copy = voiceBytes.slice(0).buffer;
    return new Promise(res => {
      try {
        const p = ctx.decodeAudioData(copy, b => { if (ac === ctx) vbuf = b; res(true); }, () => res(false));
        if (p && p.catch) p.catch(() => res(false));
      } catch (e) { res(false); }
    });
  }
  // speak line idx at context time `when`, starting `off` seconds into it (after a seek)
  function voice(when, idx, off = 0) {
    const c = VOICE.clips[idx];
    if (!vbuf || !c || off >= c.d - 0.08) return;
    const s = ac.createBufferSource(); s.buffer = vbuf;
    const g = ac.createGain();
    g.gain.setValueAtTime(0, when); g.gain.linearRampToValueAtTime(1, when + (off > 0 ? 0.08 : 0.004));
    s.connect(g); g.connect(voiceEpoch);
    s.start(when, VOICE.pre + c.o + off, c.d - off);
    const end = when + c.d - off;
    vduck.gain.setTargetAtTime(VOICE_DUCK, Math.max(ac.currentTime, when - 0.3), 0.09);
    vduck.gain.setTargetAtTime(SCORE_TRIM, end + 0.15, 0.4);
  }

  // Continuous beds whose levels follow the picture every frame
  function buildBeds() {
    // Reaper drone: two beating low sines + growling filtered noise
    drone = { g: ac.createGain() };
    drone.g.gain.value = 0;
    const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 260; lp.Q.value = 0.7;
    [36.7, 38.1, 55.0].forEach((f, i) => {
      const o = ac.createOscillator(); o.type = i === 2 ? 'triangle' : 'sine'; o.frequency.value = f;
      const g = ac.createGain(); g.gain.value = i === 2 ? 0.08 : 0.12;
      o.connect(g); g.connect(lp); o.start();
    });
    { const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = 73.4;
      const gl = ac.createBiquadFilter(); gl.type = 'lowpass'; gl.frequency.value = 320; gl.Q.value = 1.5;
      const g = ac.createGain(); g.gain.value = 0.16; o.connect(gl); gl.connect(g); g.connect(drone.g); o.start(); }
    const n = ac.createBufferSource(); n.buffer = noiseBuf; n.loop = true;
    const nb = ac.createBiquadFilter(); nb.type = 'bandpass'; nb.frequency.value = 190; nb.Q.value = 1.2;
    const ng = ac.createGain(); ng.gain.value = 1.4;
    const lfo = ac.createOscillator(); lfo.frequency.value = 0.07;
    const lfoG = ac.createGain(); lfoG.gain.value = 60;
    lfo.connect(lfoG); lfoG.connect(nb.frequency); lfo.start();
    n.connect(nb); nb.connect(ng); ng.connect(lp); n.start();
    lp.connect(drone.g); drone.g.connect(master);
    const dv = ac.createGain(); dv.gain.value = 0.4; drone.g.connect(dv); dv.connect(verbSend);

    // Room tone / night wind: very soft, airy
    wind = { g: ac.createGain() }; wind.g.gain.value = 0;
    const wn = ac.createBufferSource(); wn.buffer = noiseBuf; wn.loop = true; wn.playbackRate.value = 0.7;
    const wf = ac.createBiquadFilter(); wf.type = 'bandpass'; wf.frequency.value = 500; wf.Q.value = 0.6;
    const wl = ac.createOscillator(); wl.frequency.value = 0.05;
    const wlg = ac.createGain(); wlg.gain.value = 260; wl.connect(wlg); wlg.connect(wf.frequency); wl.start();
    wn.connect(wf); wf.connect(wind.g); wind.g.connect(master); wn.start();

    // Warmth: a sustained, slowly breathing chord of sines (family presence)
    warmth = { g: ac.createGain(), oscs: [] };
    warmth.g.gain.value = 0;
    const wlp = ac.createBiquadFilter(); wlp.type = 'lowpass'; wlp.frequency.value = 1600;
    [50, 57, 64, 69].forEach((m, i) => {
      const o = ac.createOscillator(); o.type = 'sine'; o.frequency.value = mtof(m);
      const o2 = ac.createOscillator(); o2.type = 'triangle'; o2.frequency.value = mtof(m) * 1.003;
      const g = ac.createGain(); g.gain.value = 0.05 / (1 + i * 0.25);
      const trem = ac.createOscillator(); trem.frequency.value = 0.11 + i * 0.037;
      const tg = ac.createGain(); tg.gain.value = 0.025 / (1 + i * 0.25);
      trem.connect(tg); tg.connect(g.gain); trem.start();
      o.connect(g); o2.connect(g); g.connect(wlp); o.start(); o2.start();
      warmth.oscs.push(o, o2);
    });
    wlp.connect(warmth.g); warmth.g.connect(master);
    const wv = ac.createGain(); wv.gain.value = 0.7; warmth.g.connect(wv); wv.connect(verbSend);

    // Cold cluster: death's high glassy shimmer; its lowpass closes when it is 'behind the glass'
    cold = { g: ac.createGain(), lp: ac.createBiquadFilter() };
    cold.g.gain.value = 0; cold.lp.type = 'lowpass'; cold.lp.frequency.value = 9000; cold.lp.Q.value = 0.5;
    [1318.5, 1396.9, 1480.0].forEach((f, i) => {
      const o = ac.createOscillator(); o.type = 'sine'; o.frequency.value = f;
      const v = ac.createOscillator(); v.frequency.value = 0.27 + i * 0.05;
      const vg = ac.createGain(); vg.gain.value = f * 0.0035; v.connect(vg); vg.connect(o.frequency);
      const g = ac.createGain(); g.gain.value = 0.33;
      o.connect(g); g.connect(cold.lp); o.start(); v.start();
    });
    cold.lp.connect(cold.g); cold.g.connect(master);
    const cv_ = ac.createGain(); cv_.gain.value = 0.8; cold.g.connect(cv_); cv_.connect(verbSend);
  }

  function setBeds(dr, wa, wi, co = 0, cut = 9000) {
    if (!ok) return;
    bedsAt(ac.currentTime, dr, wa, wi, co, cut);
  }

  // offline export: bed levels addressed by absolute context time
  function bedsAt(time, dr, wa, wi, co = 0, cut = 9000) {
    drone.g.gain.setTargetAtTime(dr * 0.55, time, 0.25);
    warmth.g.gain.setTargetAtTime(wa * 0.28, time, 0.4);
    wind.g.gain.setTargetAtTime(wi * 0.05, time, 0.5);
    cold.g.gain.setTargetAtTime(co * 0.05, time, 0.3);
    cold.lp.frequency.setTargetAtTime(Math.max(200, cut), time, 0.35);
  }

  // ---------- helpers
  function envGain(when, peak, a, d, sustainLevel, holdEnd, r) {
    const g = ac.createGain();
    g.gain.setValueAtTime(0.0001, when);
    g.gain.linearRampToValueAtTime(peak, when + a);
    if (d > 0) g.gain.setTargetAtTime(peak * sustainLevel, when + a, d / 3);
    g.gain.setValueAtTime(peak * sustainLevel, Math.max(when + a + 0.001, holdEnd));
    g.gain.exponentialRampToValueAtTime(0.0001, holdEnd + r);
    return g;
  }
  const pan = v => { const p = ac.createStereoPanner ? ac.createStereoPanner() : ac.createGain(); if (p.pan) p.pan.value = v; return p; };

  // ---------- instruments
  // Felt piano: triangle/sine partials with hammer softness and a closing filter
  function piano(when, midi, vel = 0.5, dur = 4, p = 0) {
    const f = mtof(midi);
    const out = pan(p); out.connect(musicBus);
    const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.Q.value = 0.4;
    lp.frequency.setValueAtTime(Math.min(9000, f * 9), when);
    lp.frequency.exponentialRampToValueAtTime(Math.max(380, f * 1.6), when + Math.min(dur, 3.5));
    const g = ac.createGain();
    g.gain.setValueAtTime(0.0001, when);
    g.gain.linearRampToValueAtTime(vel * 0.22, when + 0.012);
    g.gain.exponentialRampToValueAtTime(vel * 0.07, when + 0.6);
    g.gain.exponentialRampToValueAtTime(0.0001, when + dur);
    [[1, 1, 'triangle'], [2, 0.32, 'sine'], [3, 0.1, 'sine'], [4.02, 0.05, 'sine']].forEach(([m, a, type]) => {
      const o = ac.createOscillator(); o.type = type; o.frequency.value = f * m;
      o.detune.value = (Math.random() - 0.5) * 4;
      const og = ac.createGain(); og.gain.value = a;
      o.connect(og); og.connect(lp); o.start(when); o.stop(when + dur + 0.1);
    });
    // soft hammer felt
    const n = ac.createBufferSource(); n.buffer = noiseBuf;
    const nf = ac.createBiquadFilter(); nf.type = 'bandpass'; nf.frequency.value = f * 3; nf.Q.value = 1;
    const ng = ac.createGain(); ng.gain.setValueAtTime(vel * 0.05, when); ng.gain.exponentialRampToValueAtTime(0.0001, when + 0.05);
    n.connect(nf); nf.connect(ng); ng.connect(lp); n.start(when, Math.random() * 2); n.stop(when + 0.08);
    lp.connect(g); g.connect(out);
  }

  // Warm pad: detuned saws -> breathing lowpass, long attack and release
  function pad(when, midis, dur, o = {}) {
    const vel = o.vel ?? 0.16, att = o.att ?? 2.5, rel = o.rel ?? 3.5, cut = o.cut ?? 900;
    const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.Q.value = 0.9;
    lp.frequency.setValueAtTime(cut * 0.5, when);
    lp.frequency.linearRampToValueAtTime(cut, when + att);
    lp.frequency.linearRampToValueAtTime(cut * 0.6, when + dur + rel);
    const g = envGain(when, vel, att, 0, 1, when + dur, rel);
    const out = pan(o.pan ?? 0);
    lp.connect(g); g.connect(out); out.connect(musicBus);
    midis.forEach((m, i) => {
      const f = mtof(m);
      [-7, 6].forEach(c => {
        const osc = ac.createOscillator(); osc.type = o.type || 'sawtooth'; osc.frequency.value = f; osc.detune.value = c + (Math.random() - .5) * 3;
        const og = ac.createGain(); og.gain.value = 0.11 / Math.sqrt(midis.length);
        osc.connect(og); og.connect(lp); osc.start(when); osc.stop(when + dur + rel + 0.2);
      });
      if (i === 0 && !o.noSub) {
        const s = ac.createOscillator(); s.type = 'sine'; s.frequency.value = f / 2;
        const sg = ac.createGain(); sg.gain.value = 0.18;
        s.connect(sg); sg.connect(g); s.start(when); s.stop(when + dur + rel + 0.2);
      }
    });
  }

  // Strings-ish swell (bowed): saw + vibrato, slow bow
  function bowed(when, midi, dur, vel = 0.12, p = 0) {
    const f = mtof(midi);
    const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = Math.min(3200, f * 5); lp.Q.value = 0.5;
    const g = envGain(when, vel, Math.min(1.8, dur * 0.4), 0, 1, when + dur, Math.min(2.5, dur * 0.6));
    const out = pan(p);
    const vib = ac.createOscillator(); vib.frequency.value = 4.8 + Math.random() * 0.6;
    const vg = ac.createGain(); vg.gain.setValueAtTime(0, when); vg.gain.linearRampToValueAtTime(f * 0.004, when + dur * 0.5);
    vib.connect(vg);
    [0, 5].forEach(c => {
      const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = f; o.detune.value = c;
      vg.connect(o.frequency);
      const og = ac.createGain(); og.gain.value = 0.5;
      o.connect(og); og.connect(lp); o.start(when); o.stop(when + dur + 3);
    });
    vib.start(when); vib.stop(when + dur + 3);
    lp.connect(g); g.connect(out); out.connect(musicBus);
  }

  // Choir "ah": saw through formant filters, gentle vibrato
  function choir(when, midis, dur, vel = 0.1) {
    const formants = [[750, 1, 0.9], [1150, 0.5, 0.9], [2800, 0.18, 1.2]];
    const g = envGain(when, vel, 2.4, 0, 1, when + dur, 3.5);
    g.connect(musicBus);
    midis.forEach((m, i) => {
      const f = mtof(m);
      const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = f;
      const vib = ac.createOscillator(); vib.frequency.value = 5 + i * 0.13;
      const vg = ac.createGain(); vg.gain.value = f * 0.006; vib.connect(vg); vg.connect(o.frequency);
      const p = pan((i / Math.max(1, midis.length - 1) - 0.5) * 0.8);
      formants.forEach(([ff, a, q]) => {
        const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = ff; bp.Q.value = ff / 90 * q;
        const bg = ac.createGain(); bg.gain.value = a * 0.6 / Math.sqrt(midis.length);
        o.connect(bp); bp.connect(bg); bg.connect(p);
      });
      p.connect(g);
      o.start(when); o.stop(when + dur + 4); vib.start(when); vib.stop(when + dur + 4);
    });
  }

  // Celesta / glass bell: FM sine
  function bell(when, midi, vel = 0.15, dur = 3, p = 0) {
    const f = mtof(midi);
    const c = ac.createOscillator(); c.type = 'sine'; c.frequency.value = f;
    const m = ac.createOscillator(); m.type = 'sine'; m.frequency.value = f * 3.5;
    const mg = ac.createGain(); mg.gain.setValueAtTime(f * 2.2, when); mg.gain.exponentialRampToValueAtTime(f * 0.05, when + dur * 0.5);
    m.connect(mg); mg.connect(c.frequency);
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, when); g.gain.linearRampToValueAtTime(vel * 0.25, when + 0.005); g.gain.exponentialRampToValueAtTime(0.0001, when + dur);
    const out = pan(p);
    c.connect(g); g.connect(out); out.connect(musicBus);
    c.start(when); m.start(when); c.stop(when + dur + 0.1); m.stop(when + dur + 0.1);
  }

  // Heartbeat: lub-dub with pitch drop
  function heart(when, amp = 0.5) {
    const out = ac.createGain(); out.gain.value = 1; out.connect(heartBus);
    const rv = ac.createGain(); rv.gain.value = 0.25; out.connect(rv); rv.connect(verbSend);
    [[0, 1], [0.24, 0.62]].forEach(([dt, a]) => {
      const t = when + dt;
      const o = ac.createOscillator(); o.type = 'sine';
      o.frequency.setValueAtTime(78, t); o.frequency.exponentialRampToValueAtTime(36, t + 0.14);
      const g = ac.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(amp * a, t + 0.008); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.3);
      const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 160;
      o.connect(lp); lp.connect(g); g.connect(out); o.start(t); o.stop(t + 0.35);
      // a body an octave up, and a soft knock, so small speakers hear it
      const o2 = ac.createOscillator(); o2.type = 'triangle';
      o2.frequency.setValueAtTime(156, t); o2.frequency.exponentialRampToValueAtTime(72, t + 0.14);
      const g2 = ac.createGain(); g2.gain.setValueAtTime(0.0001, t); g2.gain.linearRampToValueAtTime(amp * a * 0.35, t + 0.008); g2.gain.exponentialRampToValueAtTime(0.0001, t + 0.22);
      o2.connect(g2); g2.connect(out); o2.start(t); o2.stop(t + 0.26);
      const n = ac.createBufferSource(); n.buffer = noiseBuf;
      const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 220; bp.Q.value = 1.2;
      const ng = ac.createGain(); ng.gain.setValueAtTime(amp * a * 0.25, t); ng.gain.exponentialRampToValueAtTime(0.0001, t + 0.025);
      n.connect(bp); bp.connect(ng); ng.connect(out); n.start(t, (t * 7.3) % 2); n.stop(t + 0.04);
    });
  }

  // Breath: filtered noise swell (inhale brighter, exhale darker and longer)
  function breath(when, dur, inhale, amp = 0.05) {
    const n = ac.createBufferSource(); n.buffer = noiseBuf; n.loop = true;
    const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.Q.value = 0.8;
    bp.frequency.setValueAtTime(inhale ? 700 : 1100, when);
    bp.frequency.linearRampToValueAtTime(inhale ? 1500 : 500, when + dur);
    const hp = ac.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 280;
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, when);
    g.gain.linearRampToValueAtTime(amp, when + dur * (inhale ? 0.6 : 0.25));
    g.gain.linearRampToValueAtTime(0.0001, when + dur);
    n.connect(bp); bp.connect(hp); hp.connect(g); g.connect(sfxBus);
    n.start(when, Math.random() * 1.5); n.stop(when + dur + 0.05);
  }

  // Clock: tick / tock
  function tick(when, tock = false, amp = 0.08) {
    const n = ac.createBufferSource(); n.buffer = noiseBuf;
    const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = tock ? 1900 : 2600; bp.Q.value = 9;
    const g = ac.createGain(); g.gain.setValueAtTime(amp, when); g.gain.exponentialRampToValueAtTime(0.0001, when + 0.045);
    n.connect(bp); bp.connect(g); g.connect(sfxBus); n.start(when, Math.random()); n.stop(when + 0.06);
  }

  // Whoosh / transition swell
  function whoosh(when, dur = 2.5, amp = 0.12, up = true) {
    const n = ac.createBufferSource(); n.buffer = noiseBuf; n.loop = true;
    const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.Q.value = 1.4;
    bp.frequency.setValueAtTime(up ? 180 : 3200, when);
    bp.frequency.exponentialRampToValueAtTime(up ? 3200 : 180, when + dur);
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, when);
    g.gain.linearRampToValueAtTime(amp, when + dur * 0.7); g.gain.linearRampToValueAtTime(0.0001, when + dur);
    n.connect(bp); bp.connect(g); g.connect(sfxBus); n.start(when); n.stop(when + dur + 0.1);
  }

  // Low boom (impact / tug)
  function boom(when, amp = 0.5) {
    const o = ac.createOscillator(); o.type = 'sine';
    o.frequency.setValueAtTime(90, when); o.frequency.exponentialRampToValueAtTime(28, when + 0.9);
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, when); g.gain.linearRampToValueAtTime(amp, when + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, when + 1.6);
    o.connect(g); g.connect(sfxBus); o.start(when); o.stop(when + 1.7);
    const n = ac.createBufferSource(); n.buffer = noiseBuf;
    const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 260; bp.Q.value = 0.9;
    const ng = ac.createGain(); ng.gain.setValueAtTime(0.0001, when); ng.gain.linearRampToValueAtTime(amp * 0.6, when + 0.003); ng.gain.exponentialRampToValueAtTime(0.0001, when + 0.09);
    n.connect(bp); bp.connect(ng); ng.connect(sfxBus); n.start(when, (when * 3.1) % 2); n.stop(when + 0.12);
    const o2 = ac.createOscillator(); o2.type = 'triangle'; o2.frequency.setValueAtTime(160, when); o2.frequency.exponentialRampToValueAtTime(60, when + 0.12);
    const g2 = ac.createGain(); g2.gain.setValueAtTime(0.0001, when); g2.gain.linearRampToValueAtTime(amp * 0.4, when + 0.005); g2.gain.exponentialRampToValueAtTime(0.0001, when + 0.16);
    o2.connect(g2); g2.connect(sfxBus); o2.start(when); o2.stop(when + 0.2);
  }

  // Rain: bright hiss with soft fades
  function rain(when, dur = 5, amp = 0.05) {
    const n = ac.createBufferSource(); n.buffer = noiseBuf; n.loop = true;
    const hp = ac.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 2500;
    const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 6000; bp.Q.value = 0.4;
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, when); g.gain.linearRampToValueAtTime(amp, when + 0.6); g.gain.setValueAtTime(amp, when + dur - 0.6); g.gain.linearRampToValueAtTime(0.0001, when + dur);
    n.connect(hp); hp.connect(bp); bp.connect(g); g.connect(sfxBus); n.start(when); n.stop(when + dur + 0.1);
  }

  // Gate: true silence (everything but the heartbeat), with quick clean fades
  function gate(when, dur, down = 0.012, up = 0.03, floor = 0.0001) {
    duck.gain.cancelScheduledValues(when);
    duck.gain.setValueAtTime(1, when);
    duck.gain.linearRampToValueAtTime(floor, when + down);
    duck.gain.setValueAtTime(floor, when + dur);
    duck.gain.linearRampToValueAtTime(1, when + dur + up);
  }

  // Cloth / creak: short filtered noise rub
  function rub(when, dur = 0.6, amp = 0.05, freq = 900, att = 0.3) {
    const n = ac.createBufferSource(); n.buffer = noiseBuf; n.loop = true;
    const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = freq; bp.Q.value = 2;
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, when); g.gain.linearRampToValueAtTime(amp, when + Math.min(dur * att, 0.4)); g.gain.linearRampToValueAtTime(0.0001, when + dur);
    n.connect(bp); bp.connect(g); g.connect(sfxBus); n.start(when, Math.random() * 2); n.stop(when + dur + 0.05);
  }

  // Wave wash (sea)
  function wave(when, dur = 4, amp = 0.08) {
    const n = ac.createBufferSource(); n.buffer = noiseBuf; n.loop = true;
    const lp = ac.createBiquadFilter(); lp.type = 'lowpass';
    lp.frequency.setValueAtTime(300, when); lp.frequency.linearRampToValueAtTime(1400, when + dur * 0.45); lp.frequency.linearRampToValueAtTime(250, when + dur);
    const g = ac.createGain(); g.gain.setValueAtTime(0.0001, when); g.gain.linearRampToValueAtTime(amp, when + dur * 0.45); g.gain.linearRampToValueAtTime(0.0001, when + dur);
    n.connect(lp); lp.connect(g); g.connect(sfxBus); n.start(when, Math.random() * 2); n.stop(when + dur + 0.1);
  }

  const INSTR = { piano, pad, bowed, choir, bell, heart, breath, tick, whoosh, boom, rub, wave, rain, gate, voice };

  function play(ev, when, offset = 0) {
    if (!ok) return;
    const f = INSTR[ev.i];
    if (!f) return;
    const a = ev.a || [];
    if (offset > 0) {
      // joining a sustained event mid-way: shorten its duration (arg index 2 is dur for pad/choir, 1 for bowed)
      if (ev.i === 'voice') { voice(when, a[0], offset); return; }
      const b = a.slice();
      if (ev.i === 'pad') { b[1] = Math.max(0.5, b[1] - offset); b[2] = Object.assign({}, b[2], { att: 0.8 }); }
      else if (ev.i === 'choir') { b[1] = Math.max(0.5, b[1] - offset); }
      else if (ev.i === 'bowed') { b[1] = Math.max(0.5, b[1] - offset); }
      f(when, ...b);
      return;
    }
    f(when, ...a);
  }

  return {
    init, play, setBeds, bedsAt, newEpoch,
    get ok() { return ok; },
    get ctx() { return ac; },
    get time() { return ac ? ac.currentTime : 0; },
    resume() { if (ac && ac.state !== 'running') return ac.resume(); return Promise.resolve(); },
    suspend() { if (ac && ac.state === 'running') return ac.suspend(); return Promise.resolve(); },
    setMuted(m) { muted = m; if (ok) { master.gain.setTargetAtTime(m ? 0 : 0.95, ac.currentTime, 0.08); voiceOut.gain.setTargetAtTime(m ? 0 : 1, ac.currentTime, 0.08); } },
    fadeIn() { if (ok && !muted) { master.gain.setTargetAtTime(0.95, ac.currentTime, 0.3); voiceOut.gain.setTargetAtTime(1, ac.currentTime, 0.3); } },
    setMaster(v) { if (ok) { master.gain.value = v; voiceOut.gain.value = v / 0.95; } },
    get voiceReady() { return voiceReady; },
    get muted() { return muted; },
  };
})();
