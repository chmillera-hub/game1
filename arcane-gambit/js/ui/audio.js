/* Sound: effects and background music, all synthesised with the Web Audio
   API (no audio files). Effects are short envelopes on oscillators and
   noise. Music is generative: a slow chord progression played by a pad, a
   plucked arpeggio, a bass line, light percussion and the odd melody note,
   with a mood per screen (the tower of each act, battle, boss, the Heart,
   victory). Nothing plays until the first click or key press, as browsers
   require; volumes and mute come from the app's preferences. */
(function (AG) {
  'use strict';
  const UI = AG.UI;
  const Snd = (UI.Sound = {});

  let ctx = null, out = null, musicBus = null, sfxBus = null, noiseBuf = null;
  let track = null, wanted = null, timer = 0;
  const vol = { music: 0.5, sfx: 0.7, muted: false };
  const LOOKAHEAD = 0.3;

  const midi = (m) => 440 * Math.pow(2, (m - 69) / 12);

  // --------------------------------------------------------------- set-up
  function unlock() {
    if (ctx) {
      if (ctx.state === 'suspended' && ctx.resume) ctx.resume();
      return;
    }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    try { ctx = new AC(); } catch (e) { ctx = null; return; }
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -12;
    comp.knee.value = 10;
    comp.ratio.value = 3;
    comp.attack.value = 0.004;
    comp.release.value = 0.25;
    comp.connect(ctx.destination);
    out = ctx.createGain();
    out.connect(comp);
    // A small generated room so the music and effects sit in the same space.
    const verb = ctx.createConvolver();
    verb.buffer = impulse(1.9, 2.6);
    const wet = ctx.createGain();
    wet.gain.value = 0.9;
    verb.connect(wet);
    wet.connect(out);
    musicBus = ctx.createGain();
    sfxBus = ctx.createGain();
    for (const [bus, send] of [[musicBus, 0.3], [sfxBus, 0.12]]) {
      bus.connect(out);
      const g = ctx.createGain();
      g.gain.value = send;
      bus.connect(g);
      g.connect(verb);
    }
    noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const d = noiseBuf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    applyVolumes();
    timer = setInterval(tick, 40);
    if (wanted) Snd.music(wanted);
  }
  function impulse(secs, decay) {
    const n = Math.floor(ctx.sampleRate * secs);
    const buf = ctx.createBuffer(2, n, ctx.sampleRate);
    for (let c = 0; c < 2; c++) {
      const d = buf.getChannelData(c);
      for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, decay);
    }
    return buf;
  }
  function applyVolumes() {
    if (!ctx) return;
    const t = ctx.currentTime;
    out.gain.setTargetAtTime(vol.muted ? 0 : 1, t, 0.05);
    musicBus.gain.setTargetAtTime(vol.music * 0.9, t, 0.05);
    sfxBus.gain.setTargetAtTime(vol.sfx * 1.6, t, 0.05);
  }
  // Start listening for the first gesture; volumes from prefs ({music, sfx, muted}).
  Snd.init = function (prefs) {
    Snd.configure(prefs || {});
    const go = function () { unlock(); };
    window.addEventListener('pointerdown', go, true);
    window.addEventListener('keydown', go, true);
    // A soft tick for every button press.
    document.addEventListener('click', function (e) {
      const b = e.target.closest && e.target.closest('button');
      if (b && !b.disabled) Snd.fx('click');
    }, true);
  };
  Snd.configure = function (p) {
    if (p.music != null) vol.music = p.music;
    if (p.sfx != null) vol.sfx = p.sfx;
    vol.muted = !!p.muted;
    applyVolumes();
  };
  Snd.ready = function () { return !!ctx; };

  // -------------------------------------------------------------- voices
  // An oscillator through an optional filter and an envelope into a bus.
  // o: {t, type, f, f2 (glide to), glide, dur, a (attack), peak, filter: {type, f, f2, q}, bus, detune, vib}
  function tone(o) {
    const t = o.t;
    const osc = ctx.createOscillator();
    osc.type = o.type || 'sine';
    osc.frequency.setValueAtTime(o.f, t);
    if (o.f2) osc.frequency.exponentialRampToValueAtTime(Math.max(1, o.f2), t + (o.glide || o.dur));
    if (o.detune) osc.detune.value = o.detune;
    if (o.vib) {
      const lfo = ctx.createOscillator(), lg = ctx.createGain();
      lfo.frequency.value = 5.2;
      lg.gain.value = o.vib;
      lfo.connect(lg);
      lg.connect(osc.detune);
      lfo.start(t);
      lfo.stop(t + o.dur + 0.1);
    }
    return voice(osc, o, t);
  }
  function noise(o) {
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf;
    src.loop = true;
    return voice(src, o, o.t, Math.random() * 0.8);
  }
  function voice(src, o, t, offset) {
    let node = src;
    if (o.filter) {
      const bq = ctx.createBiquadFilter();
      bq.type = o.filter.type || 'lowpass';
      bq.frequency.setValueAtTime(o.filter.f, t);
      if (o.filter.f2) bq.frequency.exponentialRampToValueAtTime(o.filter.f2, t + o.dur);
      bq.Q.value = o.filter.q || 0.7;
      node.connect(bq);
      node = bq;
    }
    const g = ctx.createGain();
    const a = o.a || 0.004, peak = o.peak || 0.2;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + a);
    if (o.hold) g.gain.setValueAtTime(peak, t + a + o.hold);
    g.gain.exponentialRampToValueAtTime(0.0001, t + o.dur);
    node.connect(g);
    g.connect(o.bus || sfxBus);
    src.start(t, offset || 0);
    src.stop(t + o.dur + 0.05);
    return src;
  }
  const chime = (t, notes, gap, o) => notes.forEach((f, i) => tone(Object.assign({ t: t + i * gap, type: 'triangle', f, dur: 0.35, peak: 0.06 }, o)));

  // ------------------------------------------------------------- effects
  const FX = {
    click: (t) => tone({ t, type: 'triangle', f: 900, f2: 700, dur: 0.05, peak: 0.035 }),
    place: (t) => { tone({ t, f: 220, f2: 110, dur: 0.14, peak: 0.22 }); noise({ t, dur: 0.05, peak: 0.04, filter: { f: 1400 } }); },
    pickup: (t) => { tone({ t, type: 'triangle', f: 330, f2: 660, glide: 0.09, dur: 0.16, peak: 0.12 }); tone({ t: t + 0.07, f: 990, dur: 0.12, peak: 0.05 }); },
    remove: (t) => tone({ t, f: 150, f2: 230, dur: 0.12, peak: 0.14 }),
    deploy: (t) => { for (let i = 0; i < 4; i++) tone({ t: t + i * 0.05, f: 240 - i * 20, f2: 120, dur: 0.12, peak: 0.13 }); },
    walk: (t) => noise({ t, dur: 0.07, peak: 0.05, filter: { type: 'bandpass', f: 650, q: 1.4 } }),
    slide: (t) => noise({ t, dur: 0.24, a: 0.06, peak: 0.07, filter: { type: 'bandpass', f: 380, f2: 1500, q: 1.6 } }),
    leap: (t) => { tone({ t, f: 240, f2: 520, glide: 0.11, dur: 0.24, peak: 0.1 }); noise({ t: t + 0.18, dur: 0.06, peak: 0.05, filter: { f: 900 } }); },
    blink: (t) => { tone({ t, f: 1320, dur: 0.12, peak: 0.05 }); tone({ t: t + 0.06, f: 1975, dur: 0.18, peak: 0.045 }); },
    slash: (t) => noise({ t, dur: 0.13, peak: 0.14, filter: { type: 'highpass', f: 3200, f2: 900, q: 0.9 } }),
    smash: (t) => { tone({ t, f: 130, f2: 55, dur: 0.18, peak: 0.24 }); noise({ t, dur: 0.12, peak: 0.1, filter: { f: 1800, f2: 300 } }); },
    arrow: (t) => { tone({ t, f: 1500, f2: 650, dur: 0.16, peak: 0.05 }); noise({ t, dur: 0.1, peak: 0.035, filter: { type: 'highpass', f: 3500 } }); },
    bolt: (t) => { tone({ t, type: 'square', f: 700, f2: 230, dur: 0.22, peak: 0.045, filter: { f: 2600, f2: 700 } }); tone({ t, f: 1050, f2: 350, dur: 0.22, peak: 0.04 }); },
    fire: (t) => { noise({ t, dur: 0.38, a: 0.02, peak: 0.13, filter: { f: 2400, f2: 260 } }); tone({ t, type: 'sawtooth', f: 110, f2: 70, dur: 0.3, peak: 0.04, filter: { f: 500 } }); },
    frost: (t) => { chime(t, [1568, 2093, 2637], 0.035, { type: 'sine', dur: 0.4, peak: 0.04 }); noise({ t, dur: 0.2, peak: 0.03, filter: { type: 'highpass', f: 5200 } }); },
    lightning: (t) => { for (let i = 0; i < 4; i++) noise({ t: t + i * 0.03, dur: 0.06, peak: 0.1, filter: { type: 'bandpass', f: 1400 + Math.random() * 3200, q: 2.2 } }); tone({ t, f: 80, f2: 40, dur: 0.3, peak: 0.08 }); },
    beam: (t) => tone({ t, type: 'sawtooth', f: 280, f2: 1250, dur: 0.38, a: 0.02, peak: 0.05, filter: { f: 3200 } }),
    boom: (t) => { noise({ t, dur: 0.65, peak: 0.2, filter: { f: 1000, f2: 110 } }); tone({ t, f: 95, f2: 34, dur: 0.55, peak: 0.28 }); },
    holy: (t) => { tone({ t, f: 880, dur: 0.7, a: 0.01, peak: 0.06 }); tone({ t, f: 1318.5, dur: 0.7, a: 0.01, peak: 0.04 }); tone({ t, f: 1760, dur: 0.5, peak: 0.02 }); },
    shadow: (t) => { for (const f of [110, 113.5]) tone({ t, type: 'sawtooth', f, f2: f * 0.75, dur: 0.45, a: 0.08, peak: 0.055, filter: { f: 650 } }); },
    nature: (t) => { noise({ t, dur: 0.1, peak: 0.05, filter: { type: 'bandpass', f: 2600, q: 1.5 } }); noise({ t: t + 0.09, dur: 0.12, peak: 0.045, filter: { type: 'bandpass', f: 3100, q: 1.5 } }); },
    goo: (t) => { [300, 420, 340].forEach((f, i) => tone({ t: t + i * 0.06, f, f2: f * 1.4, dur: 0.08, peak: 0.06 })); },
    rally: (t) => { tone({ t, type: 'sawtooth', f: 220, dur: 0.22, a: 0.03, peak: 0.05, filter: { f: 1300 } }); tone({ t: t + 0.18, type: 'sawtooth', f: 330, dur: 0.35, a: 0.03, peak: 0.055, filter: { f: 1500 } }); },
    hit: (t, amt) => {
      const k = Math.min(1, 0.45 + (amt || 1) / 10);
      tone({ t, f: 160, f2: 60, dur: 0.12, peak: 0.2 * k });
      noise({ t, dur: 0.06, peak: 0.07 * k, filter: { f: 2600 } });
    },
    death: (t) => { tone({ t, type: 'triangle', f: 330, f2: 70, dur: 0.55, peak: 0.1 }); noise({ t: t + 0.05, dur: 0.4, peak: 0.05, filter: { f: 1300, f2: 200 } }); },
    heal: (t) => chime(t, [523.3, 659.3, 784], 0.06, { dur: 0.32, peak: 0.05 }),
    shield: (t) => { tone({ t, type: 'square', f: 1180, dur: 0.18, peak: 0.03, filter: { type: 'bandpass', f: 2000, q: 6 } }); tone({ t, f: 2360, dur: 0.28, peak: 0.025 }); },
    summon: (t) => { noise({ t, dur: 0.42, a: 0.22, peak: 0.05, filter: { type: 'bandpass', f: 380, f2: 2400, q: 2 } }); chime(t + 0.1, [392, 523.3, 659.3], 0.07, { type: 'sine', dur: 0.28, peak: 0.045 }); },
    promote: (t) => chime(t, [523.3, 659.3, 784, 1046.5], 0.08, { dur: 0.4, peak: 0.07 }),
    status: (t) => tone({ t, f: 620, f2: 480, dur: 0.14, peak: 0.04 }),
    round: (t) => { tone({ t, f: 392, dur: 1.3, a: 0.004, peak: 0.06 }); tone({ t, f: 588, dur: 1.0, peak: 0.035 }); tone({ t, f: 785, dur: 0.8, peak: 0.02 }); },
    storm: (t) => { noise({ t, dur: 1.3, a: 0.3, peak: 0.14, filter: { f: 320, f2: 110 } }); tone({ t, f: 55, dur: 1.1, a: 0.25, peak: 0.1 }); },
    negate: (t) => tone({ t, f: 1000, f2: 1700, dur: 0.12, peak: 0.04 }),
    coin: (t) => { tone({ t, type: 'square', f: 1318.5, dur: 0.07, peak: 0.035, filter: { f: 4200 } }); tone({ t: t + 0.07, type: 'square', f: 1760, dur: 0.2, peak: 0.035, filter: { f: 4200 } }); },
    relic: (t) => chime(t, [784, 987.8, 1174.7, 1568], 0.07, { type: 'sine', dur: 0.5, peak: 0.045 }),
    victory: (t) => { chime(t, [523.3, 659.3, 784, 1046.5], 0.11, { dur: 0.5, peak: 0.08 }); for (const f of [523.3, 659.3, 784]) tone({ t: t + 0.48, type: 'triangle', f, dur: 1.4, a: 0.02, peak: 0.05 }); },
    defeat: (t) => { chime(t, [440, 349.2, 293.7], 0.22, { dur: 0.6, peak: 0.07 }); tone({ t: t + 0.66, f: 146.8, dur: 1.4, a: 0.02, peak: 0.08 }); },
    error: (t) => tone({ t, type: 'square', f: 150, dur: 0.16, peak: 0.04, filter: { f: 700 } }),
  };
  // Which effect an attack or ability makes, by its visual.
  const VFX_SOUND = {
    slash: 'slash', stab: 'slash', claw: 'slash', lance: 'slash', pierce: 'slash', bite: 'slash',
    smash: 'smash', gore: 'smash', fist: 'smash', cleave: 'smash', whirl: 'smash', rock: 'smash', bone: 'smash',
    dart: 'arrow', arrow: 'arrow', bolt: 'bolt', arcane: 'bolt', psychic: 'bolt', time: 'bolt',
    beam: 'beam', fire: 'fire', meteor: 'boom', blast: 'boom', shell: 'boom', frost: 'frost',
    lightning: 'lightning', storm: 'lightning', shadow: 'shadow', holy: 'holy', smite: 'holy',
    nature: 'nature', thorn: 'nature', goo: 'goo', heal: 'heal', rally: 'rally', taunt: 'rally',
  };
  Snd.forVfx = function (vfx) { return VFX_SOUND[vfx] || 'bolt'; };

  // Recently played effects, so a burst of hits does not become a roar.
  const last = {};
  let recent = [];
  // Play an effect now (or `when` seconds from now).
  Snd.fx = function (name, arg, when) {
    if (!ctx || vol.muted || vol.sfx <= 0 || !FX[name]) return;
    const now = ctx.currentTime;
    if (!when) {
      if (last[name] && now - last[name] < 0.035) return;
      recent = recent.filter((x) => now - x < 0.25);
      if (recent.length >= 14) return;
      recent.push(now);
      last[name] = now;
    }
    try { FX[name](now + (when || 0) + 0.005, arg); } catch (e) { /* never let sound break the game */ }
  };

  // --------------------------------------------------------------- music
  const SCALES = {
    dorian: [0, 2, 3, 5, 7, 9, 10], aeolian: [0, 2, 3, 5, 7, 8, 10], phrygian: [0, 1, 3, 5, 7, 8, 10],
    ionian: [0, 2, 4, 5, 7, 9, 11], lydian: [0, 2, 4, 6, 7, 9, 11], harmonic: [0, 2, 3, 5, 7, 8, 11],
  };
  // bars: bars per chord; arp, bass and perc name the patterns below; cut is the pad's brightness.
  const TRACKS = {
    menu: { bpm: 68, root: 50, scale: 'dorian', prog: [0, 3, 5, 4], bars: 2, arp: 'slow', bass: 'roots', perc: null, cut: 1300, lead: 0.45 },
    tower1: { bpm: 76, root: 50, scale: 'dorian', prog: [0, 6, 3, 4], bars: 2, arp: 'flow', bass: 'roots', perc: 'soft', cut: 1600, lead: 0.35 },
    tower2: { bpm: 70, root: 45, scale: 'aeolian', prog: [0, 5, 3, 6], bars: 2, arp: 'flow', bass: 'roots', perc: 'soft', cut: 1200, lead: 0.35 },
    tower3: { bpm: 72, root: 52, scale: 'lydian', prog: [0, 1, 5, 4], bars: 2, arp: 'flow', bass: 'roots', perc: 'soft', cut: 1900, lead: 0.35 },
    battle: { bpm: 102, root: 45, scale: 'aeolian', prog: [0, 5, 6, 4], bars: 1, arp: 'run', bass: 'pulse', perc: 'drive', cut: 2100, lead: 0.2 },
    boss: { bpm: 110, root: 40, scale: 'phrygian', prog: [0, 1, 0, 6], bars: 1, arp: 'run', bass: 'pulse', perc: 'heavy', cut: 1700, lead: 0.15 },
    mega: { bpm: 64, root: 36, scale: 'harmonic', prog: [0, 1, 5, 4], bars: 2, arp: 'sparse', bass: 'beat', perc: 'heartbeat', cut: 1000, lead: 0.12 },
    victory: { bpm: 90, root: 48, scale: 'ionian', prog: [0, 4, 5, 3], bars: 1, arp: 'run', bass: 'roots', perc: 'light', cut: 2500, lead: 0.45 },
  };
  const ARP = { slow: [0, 4, 8, 12], flow: [0, 3, 6, 8, 11, 14], run: [0, 2, 4, 6, 8, 10, 12, 14], sparse: [0, 10] };
  const BASS = { roots: [0, 8], pulse: [0, 3, 6, 8, 11, 14], beat: [0, 3] };
  const PERC = {
    soft: { hat: [4, 12] },
    light: { kick: [0, 8], hat: [4, 12] },
    drive: { kick: [0, 8, 10], snare: [4, 12], hat: [2, 6, 10, 14] },
    heavy: { kick: [0, 3, 8, 11], snare: [4, 12], hat: [0, 2, 4, 6, 8, 10, 12, 14] },
    heartbeat: { heart: [0, 3] },
  };
  // The chord on a scale degree: root, third, fifth and seventh, as MIDI notes.
  function chordOf(sp, deg) {
    const sc = SCALES[sp.scale];
    return [0, 2, 4, 6].map((k) => {
      const d = deg + k;
      return sp.root + sc[d % 7] + 12 * Math.floor(d / 7);
    });
  }
  function scaleNote(sp, d) {
    const sc = SCALES[sp.scale];
    const oct = Math.floor(d / 7);
    return sp.root + sc[((d % 7) + 7) % 7] + 12 * oct;
  }

  Snd.TRACKS = Object.keys(TRACKS);
  // Change the background music (crossfading); null for silence.
  Snd.music = function (name) {
    wanted = name;
    if (!ctx) return;
    if (track && track.name === name) return;
    const t = ctx.currentTime;
    if (track) {
      const old = track;
      old.dead = true;
      old.gain.gain.cancelScheduledValues(t);
      old.gain.gain.setTargetAtTime(0.0001, t, 0.5);
      setTimeout(function () { try { old.gain.disconnect(); } catch (e) { /* gone */ } }, 4000);
    }
    track = null;
    if (!name || !TRACKS[name]) return;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.setTargetAtTime(1, t + 0.2, 0.7);
    g.connect(musicBus);
    track = { name, sp: TRACKS[name], gain: g, step: 0, next: t + 0.25, arp: 0, mel: 14 };
  };
  Snd.current = function () { return track ? track.name : null; };

  function tick() { fill(LOOKAHEAD); }
  // Schedule the music up to `ahead` seconds from now.
  function fill(ahead) {
    if (!ctx || !track) return;
    const T = track;
    const s16 = 60 / T.sp.bpm / 4;
    // After a long pause (a hidden tab), start again from now.
    if (T.next < ctx.currentTime - 1) T.next = ctx.currentTime + 0.05;
    // Muted, it keeps time without making any notes.
    const silent = vol.muted || vol.music <= 0.001;
    while (T.next < ctx.currentTime + ahead) {
      if (!silent) step(T, T.step, T.next, s16);
      T.step++;
      T.next += s16;
    }
  }
  // For tests that render offline: schedule this many seconds at once.
  Snd.prime = function (secs) { fill(secs); };
  function step(T, n, t, s16) {
    const sp = T.sp;
    const bar = Math.floor(n / 16), k = n % 16;
    const chord = chordOf(sp, sp.prog[Math.floor(bar / sp.bars) % sp.prog.length]);
    const bus = T.gain;
    if (k === 0 && bar % sp.bars === 0) pad(chord, t, sp.bars * 16 * s16, sp.cut, bus);
    if (ARP[sp.arp].indexOf(k) >= 0) {
      const up = [0, 1, 2, 3, 2, 1];
      const note = chord[up[T.arp++ % up.length]] + 12;
      tone({ t, type: 'triangle', f: midi(note), dur: Math.min(0.5, s16 * 3), peak: 0.05, filter: { f: 2600 }, bus });
    }
    if (BASS[sp.bass].indexOf(k) >= 0) {
      const len = sp.bass === 'roots' ? 7 * s16 : 2 * s16;
      tone({ t, f: midi(chord[0] - 12), dur: len, a: 0.01, peak: 0.12, bus });
      tone({ t, type: 'triangle', f: midi(chord[0] - 12), dur: len, a: 0.01, peak: 0.04, filter: { f: 700 }, bus });
    }
    const P = sp.perc ? PERC[sp.perc] : null;
    if (P) {
      if (P.kick && P.kick.indexOf(k) >= 0) tone({ t, f: 120, f2: 42, glide: 0.1, dur: 0.16, peak: 0.22, bus });
      if (P.heart && P.heart.indexOf(k) >= 0) tone({ t, f: 70, f2: 38, glide: 0.12, dur: 0.3, peak: k ? 0.2 : 0.28, bus });
      if (P.snare && P.snare.indexOf(k) >= 0) noise({ t, dur: 0.14, peak: 0.05, filter: { type: 'bandpass', f: 1800, q: 0.8 }, bus });
      if (P.hat && P.hat.indexOf(k) >= 0) noise({ t, dur: 0.035, peak: 0.018, filter: { type: 'highpass', f: 7500 }, bus });
    }
    // Now and then a melody note, wandering by step from the last one.
    if ((k === 0 || k === 6 || k === 10) && Math.random() < sp.lead) {
      T.mel = Math.max(9, Math.min(19, T.mel + [-2, -1, -1, 1, 1, 2, 0][Math.floor(Math.random() * 7)]));
      const len = s16 * (k === 0 ? 6 : 4);
      tone({ t, f: midi(scaleNote(sp, T.mel)), dur: len, a: 0.06, hold: len * 0.4, peak: 0.04, vib: 7, bus });
      tone({ t, type: 'triangle', f: midi(scaleNote(sp, T.mel)), dur: len, a: 0.06, peak: 0.02, bus });
    }
  }
  // A soft chord: two slightly detuned saws per note through a low-pass.
  function pad(chord, t, len, cut, bus) {
    chord.forEach(function (m, i) {
      for (const det of [-7, 7]) {
        tone({ t, type: 'sawtooth', f: midi(m), detune: det, dur: len + 0.6, a: 0.7, hold: Math.max(0, len - 1.2), peak: i === 3 ? 0.012 : 0.02, filter: { f: cut, q: 0.5 }, bus });
      }
    });
  }
})(globalThis.AG = globalThis.AG || {});
