// ============================================================================
//  SCORE — chord parsing + event generators. Every event: {t, i, a, len?}
//  (t = film seconds, i = instrument name, a = args after `when`, len = sustain)
// ============================================================================
const Score = (() => {
  const NOTE = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
  const QUAL = {
    '': [0, 4, 7], 'm': [0, 3, 7], 'maj7': [0, 4, 7, 11], 'm7': [0, 3, 7, 10], '7': [0, 4, 7, 10],
    'add9': [0, 4, 7, 14], 'madd9': [0, 3, 7, 14], 'sus2': [0, 2, 7], 'sus4': [0, 5, 7], 'dim': [0, 3, 6], '6': [0, 4, 7, 9], 'm6': [0, 3, 7, 9],
  };
  const pc = s => { let n = NOTE[s[0]]; if (s[1] === '#') n++; if (s[1] === 'b') n--; return (n + 12) % 12; };
  // 'F#m/A' -> { bass: midi, tones: [midi...] } voiced around a centre pitch
  function chord(name, centre = 60) {
    const [main, slash] = name.split('/');
    const m = main.match(/^([A-G][#b]?)(.*)$/);
    const root = pc(m[1]);
    const ints = QUAL[m[2]] || QUAL[''];
    let base = centre - 6 + ((root - (centre - 6)) % 12 + 12) % 12;  // root nearest below centre
    const tones = ints.map(i => base + i);
    const bassPc = slash ? pc(slash) : root;
    const bass = 36 + ((bassPc - 36) % 12 + 12) % 12;                 // C2..B2
    return { bass, tones };
  }
  const mid = n => n; // passthrough for midi literals
  // name -> midi ('F#5' -> 78)
  function note(s) { const m = s.match(/^([A-G][#b]?)(-?\d)$/); return pc(m[1]) + (+m[2] + 1) * 12; }

  // ---- generators
  // voice-led pads: each chord's tones move to the nearest octave of the previous voicing
  function pads(t0, chords, dur, o = {}) {
    let prev = null;
    return chords.map((c, k) => {
      const ch = chord(c, o.centre ?? 60);
      let tones = ch.tones;
      if (prev) {
        tones = ch.tones.map(m => { let best = m, bd = 1e9; for (let oc = -2; oc <= 2; oc++) { const c2 = m + oc * 12; const d = Math.min(...prev.map(p => Math.abs(p - c2))); if (d < bd && c2 >= 52 && c2 <= 76) { bd = d; best = c2; } } return best; });
        tones = [...new Set(tones)].sort((a, b) => a - b);
      }
      prev = tones;
      const bassN = ch.bass + 12;
      const notes = o.noBass ? tones : (tones.includes(bassN) ? tones : [bassN, ...tones]);
      const len = dur * (o.overlap ?? 1.08);
      return { t: t0 + k * dur, i: 'pad', a: [notes, len, { vel: o.vel ?? 0.14, att: o.att ?? Math.min(2.5, dur * 0.5), rel: o.rel ?? Math.min(3, dur * 0.8), cut: o.cut ?? 900, pan: o.pan ?? 0, type: o.type }], len };
    });
  }
  function bass(t0, chords, dur, o = {}) {
    return chords.map((c, k) => ({ t: t0 + k * dur, i: 'bowed', a: [chord(c).bass + (o.oct ?? 0) * 12, dur * 0.95, o.vel ?? 0.09, 0], len: dur }));
  }
  function choir(t0, chords, dur, o = {}) {
    return chords.map((c, k) => ({ t: t0 + k * dur, i: 'choir', a: [chord(c, o.centre ?? 64).tones, dur * 1.05, o.vel ?? 0.08], len: dur }));
  }
  // arpeggio over chords; pattern indexes into [bass, ...tones, tones+12]
  function arp(t0, chords, dur, o = {}) {
    const out = [], step0 = o.step ?? dur / 8, pat = o.pattern ?? [0, 2, 3, 4, 5, 4, 3, 2];
    chords.forEach((c, k) => {
      const ch = chord(c, o.centre ?? 64);
      const pool = [ch.bass + 24, ...ch.tones, ...ch.tones.map(x => x + 12)];
      const n = Math.max(1, Math.round(dur / step0)), step = dur / n;
      for (let j = 0; j < n; j++) {
        const m = pool[pat[j % pat.length] % pool.length];
        const sw = (j % 2 ? (o.swing ?? 0) : 0) * step;
        out.push({ t: t0 + k * dur + j * step + sw, i: o.instr || 'piano', a: [m, (o.vel ?? 0.35) * (j % pat.length === 0 ? 1.15 : 1) * (0.85 + 0.15 * Math.sin(j)), o.ring ?? 2.6, (j % 2 ? 0.2 : -0.2)] });
      }
    });
    return out;
  }
  // melodic line: [[noteName|midi, startBeat, beats], ...] at bpm
  function line(t0, notes, bpm, o = {}) {
    const b = 60 / bpm;
    return notes.map(([n, s, d]) => {
      const m = typeof n === 'string' ? note(n) : n;
      const instr = o.instr || 'piano';
      const args = instr === 'bowed' ? [m, d * b, o.vel ?? 0.08, o.pan ?? 0] : instr === 'bell' ? [m, o.vel ?? 0.18, Math.max(1.5, d * b * 2), o.pan ?? 0] : [m, o.vel ?? 0.4, Math.max(2, d * b * 1.6), o.pan ?? 0];
      return { t: t0 + s * b, i: instr, a: args, len: instr === 'bowed' ? d * b : 0 };
    });
  }
  function heart(t0, t1, bpm, amp = 0.4, ampEnd = amp) {
    const out = []; const step = 60 / bpm;
    for (let t = t0; t < t1; t += step) out.push({ t, i: 'heart', a: [lerp(amp, ampEnd, (t - t0) / (t1 - t0))] });
    return out;
  }
  function ticks(t0, t1, bpm = 60, amp = 0.06) {
    const out = []; const step = 60 / bpm; let k = 0;
    for (let t = t0; t < t1; t += step, k++) out.push({ t, i: 'tick', a: [k % 2 === 1, amp] });
    return out;
  }
  // breaths follow a period track so the chest on screen moves with the sound
  function breaths(t0, t1, period, amp = 0.04) {
    const out = [];
    for (let t = t0; t < t1;) {
      const P = typeof period === 'function' ? period(t) : period;
      out.push({ t, i: 'breath', a: [P * 0.42, true, amp] });
      out.push({ t: t + P * 0.45, i: 'breath', a: [P * 0.52, false, amp * 1.1] });
      t += P;
    }
    return out;
  }
  const at = (t, i, ...a) => ({ t, i, a });
  return { chord, note, pads, bass, choir, arp, line, heart, ticks, breaths, at };
})();
