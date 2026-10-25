// Background music, synthesized like the sound effects (no audio files): a handful of
// looping tracks in a medieval style. The game asks for a mood (camp, battle, boss) and
// each mood rotates through its tracks every couple of loops. Starts after the first tap.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const KEY = 'arena-gauntlet-music';
  // Loops of a track before the mood moves on to its next one (a track can set its own).
  const LOOPS = 2;

  // ------------------------------------------------------------ notation

  const PC = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
  // 'F#4' -> MIDI note number.
  function midi(name) {
    const m = /^([A-G])([#b]?)(\d)$/.exec(name);
    if (!m) return NaN;
    return 12 * (+m[3] + 1) + PC[m[1]] + (m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0);
  }
  const hz = (m) => 440 * Math.pow(2, (m - 69) / 12);

  // 'Dm' -> the chord's tones upward from its root, kept between G2 and F#3:
  // [root, third, fifth, root+8va, third+8va, fifth+8va, root+2 8va].
  function chord(sym) {
    const m = /^([A-G][#b]?)(m?)$/.exec(sym);
    if (!m) return null;
    let r = midi(m[1] + '3');
    if (r % 12 >= 7) r -= 12;
    const third = m[2] ? 3 : 4;
    return [r, r + third, r + 7, r + 12, r + 12 + third, r + 19, r + 24];
  }

  // A melody: bars split by '|', notes as 'A4:3' (pitch and length in steps), '-' a rest.
  function line(src) {
    return src.split('|').map((bar) =>
      bar
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .map((tok) => {
          const [n, l] = tok.split(':');
          return { m: n === '-' ? null : midi(n), len: +l || 1 };
        })
    );
  }

  // ------------------------------------------------------------ the tracks
  //
  // step: seconds per step (an eighth note). bar: steps per bar. chords: one per bar.
  // Parts: mel (a melody), arp (chord tones by index each step; an array strums them),
  // bass ('x' root, '5' fifth, '8' octave, '.' rest), pad (chord tones held each bar),
  // drum (pattern: 'x' hit, 'o' soft hit; fill replaces it in the loop's last bar).

  const TRACKS = {
    campfire: {
      name: 'Campfire',
      mood: 'Between battles: a lute and a wooden flute by the fire.',
      step: 60 / 80 / 2,
      bar: 8,
      chords: 'Dm C G Dm F C Am Dm',
      parts: [
        { pad: [0, 2, 3], inst: 'pad', vol: 0.035 },
        { arp: [0, 2, 3, 2, 4, 2, 3, 1], inst: 'pluck', oct: 12, vol: 0.06 },
        { bass: 'x...5...', inst: 'bass', vol: 0.048, len: 3.5 },
        {
          inst: 'flute',
          vol: 0.095,
          mel:
            'A4:3 G4:1 F4:2 E4:2 | E4:2 G4:2 C5:4 | B4:3 A4:1 G4:2 D5:2 | A4:8 |' +
            'A4:2 C5:2 F5:3 E5:1 | D5:2 C5:2 E5:4 | C5:3 B4:1 A4:2 E4:2 | D4:4 -:4 |' +
            'D5:3 E5:1 F5:2 A5:2 | G5:2 E5:2 C5:4 | D5:2 B4:2 G4:2 B4:2 | A4:6 -:2 |' +
            'F5:3 E5:1 D5:2 C5:2 | E5:4 G5:4 | A5:2 G5:2 E5:2 C5:2 | D5:8',
        },
        { drum: 'frame', pat: 'x.......', vol: 0.077 },
        { drum: 'shaker', pat: '..x...x.', vol: 0.011 },
      ],
    },
    tavern: {
      name: 'Tavern Jig',
      mood: 'Between battles: a fiddle jig over a strummed lute and a bodhrán.',
      step: 0.19,
      bar: 6,
      loops: 4,
      chords: 'G C G D G C D G',
      parts: [
        { arp: [[0, 1, 2, 3], null, null, [0, 1, 2], null, null], inst: 'pluck', oct: 12, strum: 0.012, vol: 0.035 },
        { bass: 'x..5..', inst: 'bass', vol: 0.054, len: 2.5 },
        {
          inst: 'fiddle',
          vol: 0.085,
          mel:
            'G4:1 B4:1 D5:1 G5:2 D5:1 | E5:1 D5:1 C5:1 E5:2 G5:1 | D5:1 B4:1 G4:1 B4:2 D5:1 | A4:1 B4:1 C5:1 D5:2 F#5:1 |' +
            'G5:1 F#5:1 E5:1 D5:2 B4:1 | C5:1 E5:1 G5:1 E5:2 C5:1 | D5:1 C5:1 A4:1 F#4:2 A4:1 | G4:3 -:3 |' +
            'B5:2 A5:1 G5:2 D5:1 | E5:2 G5:1 C6:2 G5:1 | D5:2 G5:1 B5:2 G5:1 | A5:2 F#5:1 D5:2 A4:1 |' +
            'B4:1 D5:1 G5:1 B5:2 A5:1 | G5:1 E5:1 C5:1 E5:2 G5:1 | F#5:1 A5:1 D6:1 A5:2 F#5:1 | G5:3 -:3',
        },
        { drum: 'frame', pat: 'x..o..', vol: 0.084 },
        { drum: 'tamb', pat: '.o.x.o', vol: 0.012 },
      ],
    },
    march: {
      name: 'March of Iron',
      mood: 'Battle: war drums, low strings and horns in A minor.',
      step: 60 / 100 / 2,
      bar: 8,
      chords: 'Am Am F G Am Am F E',
      parts: [
        { arp: [0, 0, 2, 0, 1, 0, 2, 0], inst: 'strings', vol: 0.045 },
        { bass: 'x.x.x.x.', inst: 'bass', vol: 0.054, len: 1.6 },
        { pad: [0, 2], inst: 'pad', vol: 0.03 },
        {
          inst: 'horn',
          vol: 0.081,
          mel:
            'A4:4 E4:4 | A4:2 B4:2 C5:2 B4:2 | A4:6 F4:2 | G4:4 B4:4 |' +
            'C5:4 E5:4 | D5:2 C5:2 B4:2 C5:2 | A4:4 C5:2 A4:2 | G#4:8 |' +
            'E5:4 A5:4 | G5:2 F5:2 E5:2 D5:2 | C5:4 F5:4 | D5:4 G5:4 |' +
            'E5:2 D5:2 C5:2 B4:2 | A4:2 C5:2 E5:4 | F5:2 E5:2 D5:2 C5:2 | B4:4 G#4:4',
        },
        { drum: 'taiko', pat: 'x..x..x.', vol: 0.14 },
        { drum: 'snare', pat: '....x..o', fill: '....xoxx', vol: 0.06 },
        { drum: 'shaker', pat: '.x.x.x.x', vol: 0.015 },
      ],
    },
    clash: {
      name: 'Clash of Steel',
      mood: 'Battle: a driving E minor charge, strings and horns over toms.',
      step: 60 / 128 / 2,
      bar: 8,
      chords: 'Em C D Em Em C D B',
      parts: [
        { arp: [0, 3, 2, 3, 0, 3, 2, 4], inst: 'strings', oct: 12, vol: 0.035 },
        { bass: 'xx8xxx8x', inst: 'bass', vol: 0.051, len: 0.9 },
        {
          inst: 'horn',
          vol: 0.081,
          mel:
            'E5:3 D5:1 B4:4 | C5:3 B4:1 G4:4 | A4:2 B4:2 D5:2 F#5:2 | E5:8 |' +
            'G5:3 F#5:1 E5:2 B4:2 | C5:2 E5:2 G5:4 | F#5:2 E5:2 D5:2 A4:2 | B4:4 D#5:4 |' +
            'B5:4 G5:4 | E5:4 C5:4 | D5:2 F#5:2 A5:4 | G5:2 F#5:2 E5:4 |' +
            'E5:2 G5:2 B5:2 G5:2 | E5:2 G5:2 C6:4 | A5:2 F#5:2 D5:2 F#5:2 | D#5:4 B4:4',
        },
        { drum: 'frame', pat: 'x...x.x.', vol: 0.112 },
        { drum: 'snare', pat: '..x...x.', fill: 'x.x.xxxx', vol: 0.06 },
        { drum: 'tom', pat: '.......o', fill: '....x.xx', vol: 0.08 },
        { drum: 'shaker', pat: 'oxoxoxox', vol: 0.012 },
      ],
    },
    tyrant: {
      name: 'The Ashen Tyrant',
      mood: 'Boss: a dark choir, low brass and great drums in C minor.',
      step: 60 / 88 / 2,
      bar: 8,
      chords: 'Cm Ab Fm G Cm Db Ab G',
      parts: [
        { pad: [0, 1, 2], inst: 'choir', oct: 12, vol: 0.042 },
        { arp: [0, 0, 0, 0, 0, 0, 2, 1], inst: 'strings', vol: 0.04 },
        { bass: 'x...x...', inst: 'horn', oct: -12, vol: 0.024, len: 3.6 },
        {
          inst: 'horn',
          vol: 0.081,
          mel:
            'C5:4 G4:4 | Ab4:2 G4:2 Eb4:4 | F4:2 Ab4:2 C5:4 | B4:4 D5:4 |' +
            'Eb5:4 D5:2 C5:2 | Db5:4 C5:2 Ab4:2 | C5:3 Bb4:1 Ab4:4 | G4:8 |' +
            'G5:4 Eb5:4 | Eb5:2 F5:2 Ab5:4 | F5:2 Eb5:2 C5:4 | D5:2 B4:2 G4:4 |' +
            'C5:2 Eb5:2 G5:4 | F5:2 Ab5:2 Db6:4 | C6:2 Bb5:2 Ab5:2 G5:2 | G5:4 B4:4',
        },
        { drum: 'taiko', pat: 'x..x..x.', fill: 'x.xx.xxx', vol: 0.168 },
        { drum: 'tom', pat: '.......o', vol: 0.07 },
      ],
    },
  };

  // Which tracks play where, in turn.
  const MOODS = { camp: ['campfire', 'tavern'], battle: ['march', 'clash'], boss: ['tyrant', 'clash'] };

  // Parse the tracks once: chords and melodies, with each melody note filed by bar and step.
  for (const T of Object.values(TRACKS)) {
    T.chordList = T.chords.split(/\s+/).map(chord);
    T.loopBars = T.chordList.length;
    for (const p of T.parts) {
      if (!p.mel) continue;
      p.bars = line(p.mel);
      p.at = new Map();
      p.bars.forEach((bar, b) => {
        let step = 0;
        for (const n of bar) {
          if (n.m != null) p.at.set(b * T.bar + step, n);
          step += n.len;
        }
      });
      T.loopBars = Math.max(T.loopBars, p.bars.length);
    }
  }

  // Problems in the notation (for the tests): bars of the wrong length, bad notes or chords.
  function check() {
    const bad = [];
    for (const [id, T] of Object.entries(TRACKS)) {
      T.chordList.forEach((c, i) => c || bad.push(`${id}: chord ${i + 1}`));
      for (const p of T.parts) {
        if (p.inst && !INST[p.inst]) bad.push(`${id}: instrument ${p.inst}`);
        if (p.drum && !DRUM[p.drum]) bad.push(`${id}: drum ${p.drum}`);
        if (!p.bars) continue;
        if (p.bars.length % T.chordList.length) bad.push(`${id}: melody bars ${p.bars.length}`);
        p.bars.forEach((bar, b) => {
          const n = bar.reduce((t, x) => t + x.len, 0);
          if (n !== T.bar) bad.push(`${id}: bar ${b + 1} has ${n} steps, not ${T.bar}`);
          if (bar.some((x) => Number.isNaN(x.m))) bad.push(`${id}: bad note in bar ${b + 1}`);
        });
      }
    }
    return bad;
  }

  // ------------------------------------------------------------ instruments

  let ctx = null; // the audio context the voices are built in
  let noiseBuf = null;

  function envGain(out, t, a, hold, r, vol) {
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + a);
    g.gain.setValueAtTime(vol, t + a + hold);
    g.gain.exponentialRampToValueAtTime(0.0001, t + a + hold + r);
    g.connect(out);
    return g;
  }

  function filter(type, f, q, dest) {
    const b = ctx.createBiquadFilter();
    b.type = type;
    b.frequency.value = f;
    b.Q.value = q;
    b.connect(dest);
    return b;
  }

  function osc(type, f, t, end, dest, detune, level) {
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(f, t);
    if (detune) o.detune.value = detune;
    let to = dest;
    if (level != null) {
      to = ctx.createGain();
      to.gain.value = level;
      to.connect(dest);
    }
    o.connect(to);
    o.start(t);
    o.stop(end);
    return o;
  }

  // A gentle vibrato that sets in once the note has started.
  function vibrato(oscs, f, t, end, rate, depth) {
    const lfo = ctx.createOscillator();
    lfo.frequency.value = rate;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(f * depth, t + 0.25);
    lfo.connect(g);
    for (const o of oscs) g.connect(o.frequency);
    lfo.start(t);
    lfo.stop(end);
  }

  // `att`: how fast it comes in. Snappy (2 ms) for drum skins; a rattle eases in, or it
  // ticks like a gas igniter.
  function noise(out, t, dur, vol, type, f, q, att) {
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf;
    const g = envGain(out, t, att || 0.002, 0, dur, vol);
    src.connect(filter(type, f, q || 0.8, g));
    src.start(t);
    src.stop(t + dur + 0.05);
  }

  // Each takes the track's output, a frequency, a start time, a length and a volume.
  const INST = {
    // A lute or harp: a bright pluck that dulls as it rings.
    pluck(out, f, t, d, v) {
      const ring = Math.max(0.6, d * 1.6);
      const fl = filter('lowpass', 3400, 1, envGain(out, t, 0.004, 0, ring, v));
      fl.frequency.setValueAtTime(3400, t);
      fl.frequency.exponentialRampToValueAtTime(800, t + 0.45);
      osc('triangle', f, t, t + ring + 0.05, fl);
      osc('sawtooth', f, t, t + ring + 0.05, fl, 5, 0.3);
    },
    // A wooden flute: soft attack, a little breath, vibrato as the note settles.
    flute(out, f, t, d, v) {
      const g = envGain(out, t, 0.07, Math.max(0, d - 0.12), 0.2, v);
      const end = t + d + 0.3;
      const a = osc('sine', f, t, end, g);
      const b = osc('triangle', f * 2, t, end, g, 0, 0.1);
      vibrato([a, b], f, t + 0.2, end, 5.2, 0.006);
      noise(out, t, 0.09, v * 0.25, 'bandpass', f * 2, 2);
    },
    // A fiddle: a bowed sawtooth, quick to speak, with a lively vibrato.
    fiddle(out, f, t, d, v) {
      const g = envGain(out, t, 0.025, Math.max(0, d - 0.06), 0.09, v);
      const end = t + d + 0.15;
      const fl = filter('lowpass', 2600, 1.4, g);
      const a = osc('sawtooth', f, t, end, fl);
      const b = osc('sawtooth', f, t, end, fl, 6, 0.5);
      vibrato([a, b], f, t + 0.08, end, 6.2, 0.007);
    },
    // A horn: brass that brightens as it swells.
    horn(out, f, t, d, v) {
      const g = envGain(out, t, 0.08, Math.max(0, d - 0.12), 0.22, v);
      const end = t + d + 0.3;
      const fl = filter('lowpass', 500, 1.1, g);
      fl.frequency.setValueAtTime(450, t);
      fl.frequency.exponentialRampToValueAtTime(1500, t + 0.12);
      fl.frequency.exponentialRampToValueAtTime(950, t + Math.max(0.2, d));
      osc('sawtooth', f, t, end, fl);
      osc('sawtooth', f, t, end, fl, 8, 0.8);
    },
    // Short bowed strings, for driving ostinatos.
    strings(out, f, t, d, v) {
      const g = envGain(out, t, 0.01, d * 0.35, d * 0.6, v);
      const end = t + d + 0.1;
      const fl = filter('lowpass', 1900, 0.9, g);
      osc('sawtooth', f, t, end, fl, -6);
      osc('sawtooth', f, t, end, fl, 6, 0.8);
    },
    // A soft held chord under everything.
    pad(out, f, t, d, v) {
      const g = envGain(out, t, 0.5, Math.max(0, d - 0.5), 0.9, v);
      const end = t + d + 1;
      const fl = filter('lowpass', 760, 0.6, g);
      osc('sawtooth', f, t, end, fl, -9);
      osc('sawtooth', f, t, end, fl, 9);
    },
    // A wordless choir: breathy, swelling, with a slow vibrato.
    choir(out, f, t, d, v) {
      const g = envGain(out, t, 0.6, Math.max(0, d - 0.6), 1, v);
      const end = t + d + 1.1;
      const fl = filter('bandpass', 750, 1.2, filter('lowpass', 1500, 0.7, g));
      const a = osc('sawtooth', f, t, end, fl, -7);
      const b = osc('sawtooth', f, t, end, fl, 7);
      vibrato([a, b], f, t + 0.3, end, 4.6, 0.004);
    },
    bass(out, f, t, d, v) {
      const g = envGain(out, t, 0.008, d * 0.6, 0.18, v);
      const end = t + d + 0.25;
      const fl = filter('lowpass', 650, 0.8, g);
      osc('triangle', f, t, end, fl);
      osc('sine', f, t, end, fl, 0, 0.7);
    },
  };

  function thump(out, t, f0, f1, dur, vol) {
    const g = envGain(out, t, 0.004, 0, dur, vol);
    const o = osc('sine', f0, t, t + dur + 0.05, g);
    o.frequency.exponentialRampToValueAtTime(f1, t + dur * 0.8);
  }

  const DRUM = {
    // A frame drum: a soft low thump.
    frame(out, t, v) {
      thump(out, t, 140, 55, 0.32, v);
      noise(out, t, 0.05, v * 0.3, 'lowpass', 900);
    },
    // A great war drum.
    taiko(out, t, v) {
      thump(out, t, 92, 40, 0.6, v);
      noise(out, t, 0.18, v * 0.5, 'lowpass', 320);
    },
    tom(out, t, v) {
      thump(out, t, 175, 95, 0.3, v);
    },
    snare(out, t, v) {
      noise(out, t, 0.16, v, 'bandpass', 1900, 0.8);
      thump(out, t, 230, 160, 0.07, v * 0.4);
    },
    // A soft rattle, not a tick: it eases in and stays below the sharpest highs.
    shaker(out, t, v) {
      noise(out, t, 0.07, v, 'highpass', 5200, 0.7, 0.015);
    },
    tamb(out, t, v) {
      noise(out, t, 0.12, v, 'highpass', 5800, 0.7, 0.015);
    },
  };

  // ------------------------------------------------------------ playing

  // Everything a playing track needs: where it is, and its own volume for fading.
  function newState(id, out) {
    const g = ctx.createGain();
    g.gain.value = 1;
    g.connect(out);
    return { id, T: TRACKS[id], gain: g, bar: 0, step: 0, loops: 0, t: 0 };
  }

  // Schedule one step of a track at time t.
  function playStep(st, t) {
    const T = st.T;
    const ch = T.chordList[st.bar % T.chordList.length];
    const last = st.bar === T.loopBars - 1;
    for (const p of T.parts) {
      if (p.drum) {
        const pat = p.fill && last ? p.fill : p.pat;
        const c = pat[st.step % pat.length];
        if (c === 'x') DRUM[p.drum](st.gain, t, p.vol);
        else if (c === 'o') DRUM[p.drum](st.gain, t, p.vol * 0.45);
      } else if (p.at) {
        const n = p.at.get((st.bar % p.bars.length) * T.bar + st.step);
        if (n) INST[p.inst](st.gain, hz(n.m + (p.oct || 0)), t, n.len * T.step * 0.95, p.vol);
      } else if (p.arp) {
        const k = p.arp[st.step % p.arp.length];
        if (k == null) continue;
        const ks = Array.isArray(k) ? k : [k];
        ks.forEach((i, j) => INST[p.inst](st.gain, hz(ch[i] + (p.oct || 0)), t + j * (p.strum || 0), T.step * (p.len || 1), p.vol));
      } else if (p.bass) {
        const c = p.bass[st.step % p.bass.length];
        if (c === '.') continue;
        const up = c === '5' ? 7 : c === '8' ? 12 : 0;
        INST[p.inst](st.gain, hz(ch[0] + up + (p.oct != null ? p.oct : -12)), t, T.step * (p.len || 1.8), p.vol);
      } else if (p.pad && st.step === 0) {
        for (const i of p.pad) INST[p.inst](st.gain, hz(ch[i] + (p.oct || 0)), t, T.step * T.bar, p.vol);
      }
    }
  }

  // Move a track on by one step; true when it has just finished a loop.
  function advance(st) {
    st.t += st.T.step;
    if (++st.step < st.T.bar) return false;
    st.step = 0;
    if (++st.bar < st.T.loopBars) return false;
    st.bar = 0;
    st.loops++;
    return true;
  }

  let on = true;
  try {
    on = root.localStorage.getItem(KEY) !== 'off';
  } catch (e) {
    on = true;
  }
  let mix = null; // the music bus, built on the live context
  let mood = null; // what the game asked for
  let cur = null; // the track playing
  let timer = null;
  const turn = { camp: 0, battle: 0, boss: 0 };

  function makeNoise(c) {
    const b = c.createBuffer(1, c.sampleRate, c.sampleRate);
    const d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    return b;
  }

  // The music bus: a little reverb, and a compressor so the tracks sit evenly under the
  // sound effects.
  function makeBus(c, dest) {
    const comp = c.createDynamicsCompressor();
    comp.threshold.value = -20;
    comp.ratio.value = 3;
    comp.connect(dest);
    // Phone speakers cannot play deep bass, and it would only pump the compressor.
    const hp = c.createBiquadFilter();
    hp.type = 'highpass';
    hp.frequency.value = 80;
    hp.connect(comp);
    const bus = c.createGain();
    bus.gain.value = 0.35;
    bus.connect(hp);
    const verb = c.createConvolver();
    const len = Math.floor(c.sampleRate * 2.2);
    const ir = c.createBuffer(2, len, c.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const d = ir.getChannelData(ch);
      for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2.8);
    }
    verb.buffer = ir;
    const send = c.createGain();
    send.gain.value = 0.22;
    bus.connect(send).connect(verb).connect(hp);
    return bus;
  }

  function live() {
    const c = AG.Audio && AG.Audio.context && AG.Audio.context(false);
    if (!c || c.state !== 'running') return null;
    if (ctx !== c) {
      ctx = c;
      noiseBuf = makeNoise(c);
      mix = makeBus(c, c.destination);
    }
    return c;
  }

  // Let a track go: faded out, or (moving on at the end of a loop) left to ring out.
  function release(st, fade) {
    if (!st) return;
    const g = st.gain;
    if (fade) {
      const t = ctx.currentTime;
      g.gain.cancelScheduledValues(t);
      g.gain.setValueAtTime(g.gain.value, t);
      g.gain.setTargetAtTime(0.0001, t, 0.35);
    }
    setTimeout(() => g.disconnect(), 4000);
  }

  // Start the mood's next track (or stop, with no mood). `at`: on the beat, ending a loop.
  function begin(at) {
    release(cur, at == null);
    cur = null;
    if (!mood || !on || !live()) return;
    const list = MOODS[mood];
    const id = list[turn[mood] % list.length];
    turn[mood]++;
    cur = newState(id, mix);
    cur.t = at != null ? at : ctx.currentTime + 0.35;
    cur.mood = mood;
    if (!timer) timer = setInterval(tick, 50);
  }

  function tick() {
    if (!cur || !ctx) {
      clearInterval(timer);
      timer = null;
      return;
    }
    if (ctx.state !== 'running') return;
    const now = ctx.currentTime;
    // Fell behind (the tab slept): pick up from here rather than play a burst of notes.
    if (cur.t < now - 0.1) cur.t = now + 0.05;
    while (cur && cur.t < now + 0.3) {
      try {
        playStep(cur, cur.t);
      } catch (e) {
        /* ignore audio errors */
      }
      const st = cur;
      // After a couple of loops the mood moves on to its next track, on the beat.
      if (advance(st) && st.loops >= (st.T.loops || LOOPS) && MOODS[st.mood].length > 1) begin(st.t);
    }
  }

  if (root.document) {
    root.document.addEventListener('visibilitychange', () => {
      if (!ctx) return;
      if (root.document.hidden) ctx.suspend();
      else ctx.resume();
    });
  }

  // Render `seconds` of a track offline (for previews and checks): an AudioBuffer promise.
  function render(id, seconds, rate) {
    const OAC = root.OfflineAudioContext || root.webkitOfflineAudioContext;
    const off = new OAC(2, Math.ceil((rate || 44100) * seconds), rate || 44100);
    const saved = [ctx, noiseBuf];
    ctx = off;
    noiseBuf = makeNoise(off);
    const st = newState(id, makeBus(off, off.destination));
    st.t = 0.05;
    while (st.t < seconds - 0.5) {
      playStep(st, st.t);
      advance(st);
    }
    [ctx, noiseBuf] = saved;
    return off.startRendering();
  }

  AG.Music = {
    // Ask for a mood ('camp', 'battle', 'boss'), or null for silence.
    set(name) {
      if (name === mood && (cur || !on)) return;
      mood = name || null;
      if (ctx || live()) begin();
    },
    // After the first tap: the audio context can start, so the music can too.
    kick() {
      const c = AG.Audio && AG.Audio.context && AG.Audio.context(true);
      if (!c) return;
      const go = () => {
        if (!cur && on && mood) begin();
      };
      if (c.state === 'running') go();
      else if (c.resume) c.resume().then(go, () => {});
    },
    get enabled() {
      return on;
    },
    get playing() {
      return cur ? cur.id : null;
    },
    toggle() {
      on = !on;
      try {
        root.localStorage.setItem(KEY, on ? 'on' : 'off');
      } catch (e) {
        /* storage unavailable */
      }
      if (on) this.kick();
      else if (ctx) begin();
      return on;
    },
    TRACKS,
    MOODS,
    check,
    render,
  };
})(typeof window !== 'undefined' ? window : globalThis);
