#!/usr/bin/env python3
"""THE STONE AND THE BREAD -- the film's score and source music (SPEC section 5; motif.py is the DNA).

    from film.audio import music
    hold = music.hold_music(ctx3)          # S3: the four-note music box through the speaking stone
    band = music.tavern_band(ctx4)         # S4: the rowdy jig, with perspective (outside/inside) + the swell
    score, events = music.score()          # S6-S9: piano / harp / celesta, global time, stereo
    python3 film/audio/music.py            # renders all three to film/build/audio/music_*.wav

1. HOLD MUSIC (scene 3, cold and mechanical).  motif.hold_music_events() -- MUSIC_BOX_MOTIF B5 A5 F#5 E5,
   rhythm e e e q., HOLD_TEMPO (loop = 1.5 s), dead-even, no harmony, never resolving -- from beat s3_hold to
   the scene's hard cut.  A tinny music box: free-free tine partials 1 : 2.76 : 5.40 : 8.93 with short decays,
   each comb tooth a few cents out of tune (fixed per note), a pin click per note, the cylinder's faint
   ratchet.  Every note is rendered ONCE and re-used, so each loop is sample-identical before transmission:
   it loops EXACTLY.  Then the speaking stone: band-pass ~400-3000 Hz, a little saturation, a slight warble
   (wow 0.7 Hz + flutter 5.5 Hz), faint channel hiss.

2. TAVERN BAND (scene 4, A Knight's Tale bravado).  An original jig in D mixolydian (the film's key with its
   bVII colour), 6/8 at 120 dotted-quarter bpm (one bar = 1 s), the bar grid locked so the SWELL lands on a
   downbeat at beat s4_swell.  Fiddle (additive bowed string: sawtooth spectrum, bow attacks and changes,
   delayed vibrato, bow noise, violin-body modal filter, cuts), crumhorn (capped double reed: odd harmonics,
   nasal formants) doubling an octave below, a hurdy-gurdy drone on D/A with trompette buzz in the swell,
   lute strumming (song.py's Karplus-Strong lute), frame drum + tambourine (song.py's drum hits), and in
   the swell the whole room stomping and clapping (BOOM - BOOM CLAP).  Form: ... A7 A8 | B (outside, then
   inside at s4_inside) | A1 A2 = a 2-bar BREAK (fiddle tacet, the room quiets: "Can I tell you
   something?") | B at fortissimo = THE SWELL (drum roll into it, +5 dB, stomps, claps; buries "Lately I-")
   | A ... (normal; ducked under the troll's line by the mix).  Perspective, exactly like the tavern
   ambience (sfx.perspective_gain): outside -> muffled (low-pass ~600 Hz, -13 dB), hard switch inside at
   s4_inside, and muffled again the instant the door closes (s4's door_close cue, else s4_exit + 2.6 s).

3. SCORE (scenes 6-9: the stone turned into bread).  The same four notes, slow, warm and harmonized with
   motif.WARM_HARMONY (Gmaj7 - D/F# - Bm7 - Asus4), never resolving until the very end:
     S6  at the laugh (beat s6_laugh): the bare motif once, high and soft, rubato (harp, celesta 8va).
     S7  statement 1 when she hands him the bread (harp + a whisper of piano); the sus4 opens to A when the
         teen sits; statement 2 as the bench fills (piano melody on each arrival: driver, worker, full,
         then E over Asus4 through the bench drag), sparse held chords under the dialogue, a rising harp
         arpeggio into S8.
     S8  full bloom under the voice-over: each motif note lands just AFTER a voice-over line, as if the
         music finishes his thought; Asus4 opens to A (E stays on top -- unresolved) as the picture fades.
     S9  the A chord rings out into the end card; the reprise (voice + lute) carries the melodic resolution
         (E -> D on "you"); at its final chord (beat s9_final_chord) the score blooms on motif.FINAL_CHORD,
         D(add9), held under the fade.
   Instruments are additive: PIANO (inharmonic partials f_k = k f0 sqrt(1 + B k^2), hammer-position comb,
   two-stage decay, two detuned strings per partial, hammer noise + soundboard knock, damper release),
   HARP (pluck-position spectrum, long low decays, finger noise, tension glide), CELESTA (bar partials with
   a felt hammer, resonator-boosted fundamental).  A warm hall around all three.
All deterministic (fixed seeds).
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass

import numpy as np
from scipy.signal import fftconvolve, lfilter

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
ROOT = os.path.dirname(FILM)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from film.audio import motif as M  # noqa: E402
from film.audio import song as SONG  # noqa: E402
from film.audio import sfx as FX  # noqa: E402
from film.audio.sfx import (SR, bp, burst, fade, fit, hp, hump, lp, modes, ns, peq, place, smooth_rand,  # noqa: E402
                            stereo, tvec, white)


def hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, float) - 69.0) / 12.0)


# ================================================================================================
# 1. HOLD MUSIC
# ================================================================================================
TOOTH_CENTS = {83: +6.0, 81: -5.0, 78: +4.0, 76: -8.0}      # each comb tooth a few cents out (fixed)
TINE = ((1.0, 1.0, 0.24), (2.756, 0.42, 0.085), (5.404, 0.2, 0.04), (8.933, 0.09, 0.02))


def music_box_note(midi, seed=0, dur=1.6):
    rng = np.random.default_rng(seed)
    f0 = float(hz(midi)) * 2 ** (TOOTH_CENTS.get(int(midi), 0.0) / 1200)
    n = ns(dur)
    t = tvec(n)
    y = np.zeros(n)
    for r, a, tau in TINE:
        y += a * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6.28)) * np.exp(-t / tau)
    y *= np.clip(t / 0.0008, 0, 1)
    pin = bp(burst(rng, ns(0.006), 0.0007), 2500, 9000) * 0.35          # the pin lets go of the tooth
    place(y, pin, 0)
    box = modes(rng, [(1530, 0.012, 1.0), (2470, 0.008, 0.6), (890, 0.02, 0.5)], ns(0.08)) * 0.05
    place(y, box, 0)
    return fade(y, 0.0, 0.05)


def stone_phone(x, seed=3, lo=400.0, hi=3000.0, warble=1.0, hiss_db=-52.0):
    """Heard through the speaking stone: band-pass, a little grit, a slight warble, faint channel hiss."""
    rng = np.random.default_rng(seed)
    n = len(x)
    t = tvec(n)
    # warble: modulated delay (wow 0.7 Hz ~0.18 %, flutter 5.5 Hz ~0.05 %)
    d = warble * (0.0018 / (2 * np.pi * 0.7) * np.sin(2 * np.pi * 0.7 * t) +
                  0.0005 / (2 * np.pi * 5.5) * np.sin(2 * np.pi * 5.5 * t + 1.0))
    pos = np.arange(n) - (d + 0.002) * SR
    y = np.interp(pos, np.arange(n), x, left=0.0, right=0.0)
    y = bp(y, lo, hi, 4)
    pk = np.abs(y).max() + 1e-9
    y = np.tanh(1.6 * y / pk) / np.tanh(1.6) * pk
    y = peq(y, 1700, 3.0, 1.2)
    hiss = bp(white(rng, n), lo, hi) * 10 ** (hiss_db / 20) * pk
    return y + hiss


def hold_music(ctx, verbose=False):
    """Scene-3 music-box loop through the stone; scene-local array over [-pre, dur + post] (mono -> stereo).
    Returns (stereo, events) with events = [(t_local, dur, midi)]."""
    dur, pre, post = ctx["dur"], ctx.get("pre", 0.5), ctx.get("post", 0.5)
    t0 = ctx.get("beats", {}).get("s3_hold", (10.0, None))[0]
    t1 = dur                                                     # plays until the hard cut to S4
    ev = M.hold_music_events(t1 - t0, t0=t0)
    notes = {m: music_box_note(m, seed=1000 + m) for m in set(e[2] for e in ev)}
    n = ns(dur + pre + post)
    y = np.zeros(n)
    for st, d, m in ev:
        place(y, notes[m], ns(pre + st))
    # the cylinder's faint ratchet (one tick per eighth, identical each time)
    rng = np.random.default_rng(77)
    tick = FX.excite(burst(rng, ns(0.001), 0.0003), modes(rng, [(3100, 0.003, 1), (4700, 0.002, 0.5)], ns(0.01)))
    e = M.eighth_seconds(M.HOLD_TEMPO)
    k = 0
    while t0 + k * e < t1:
        place(y, 0.05 * tick, ns(pre + t0 + k * e))
        k += 1
    y = stone_phone(y)
    # hard stop at the scene cut (5 ms), silence before the hold
    tt = tvec(n) - pre
    gate = np.clip((t1 - tt) / 0.005, 0, 1) * np.clip((tt - t0 + 0.01) / 0.005, 0, 1)
    y *= gate
    st = stereo(y, 0.12) * 1.0
    return st, ev


# ================================================================================================
# 2. TAVERN BAND
# ================================================================================================
TAVERN_TEMPO = 120.0                       # dotted-quarter bpm: one 6/8 bar = 1.0 s
# (midi, eighths) per bar; D mixolydian (C natural)
JIG_A = [[(74, 2), (69, 1), (66, 2), (69, 1)], [(74, 2), (76, 1), (78, 1), (76, 1), (74, 1)],
         [(72, 2), (67, 1), (64, 2), (67, 1)], [(72, 2), (74, 1), (76, 1), (74, 1), (72, 1)],
         [(74, 2), (69, 1), (66, 2), (69, 1)], [(74, 2), (76, 1), (78, 1), (79, 1), (81, 1)],
         [(79, 1), (78, 1), (76, 1), (74, 1), (72, 1), (69, 1)], [(74, 3), (74, 1), (72, 1), (69, 1)]]
JIG_A_CHORDS = [("D", "D"), ("D", "D"), ("C", "C"), ("C", "C"), ("D", "D"), ("D", "D"), ("G", "C"), ("D", "D")]
JIG_B = [[(78, 2), (79, 1), (81, 2), (78, 1)], [(79, 2), (81, 1), (83, 1), (81, 1), (79, 1)],
         [(78, 2), (79, 1), (81, 2), (78, 1)], [(76, 1), (74, 1), (72, 1), (72, 2), (76, 1)],
         [(78, 2), (79, 1), (81, 2), (78, 1)], [(79, 2), (81, 1), (83, 2), (84, 1)],
         [(86, 1), (84, 1), (81, 1), (79, 1), (76, 1), (72, 1)], [(74, 3), (74, 1), (72, 1), (69, 1)]]
JIG_B_CHORDS = [("D", "D"), ("G", "G"), ("D", "D"), ("C", "C"), ("D", "D"), ("G", "G"), ("D", "C"), ("D", "D")]

VIOLIN_BODY = [(275, 0.012, 1.0), (460, 0.010, 0.8), (540, 0.010, 0.9), (700, 0.008, 0.6), (1050, 0.006, 0.6),
               (1450, 0.005, 0.55), (2200, 0.004, 0.75), (2900, 0.003, 0.6), (3600, 0.0025, 0.4),
               (4400, 0.002, 0.25)]


def _body_ir(spec, seed, direct=1.0, modal=0.08, dur=0.06):
    """Instrument body: a unit direct path plus the body's modes `modal` x (unit energy).  A unit-energy
    modal IR alone peaks ~27 dB above a flat path (each note's level then depends on where it falls
    between the modes: a 28 dB note-to-note spread on the fiddle).  At modal ~0.08 the body gives gentle
    formants (1/3-octave spread ~3 dB, fundamentals within ~+2/-6 dB) -- it colours, it does not pick notes."""
    rng = np.random.default_rng(seed)
    ir = modes(rng, spec, ns(dur), jitter=0.01, amp_jit=0.1)
    ir *= modal / (np.sqrt(np.sum(ir * ir)) + 1e-12)
    ir[0] += direct
    return ir


def _note_tracks(notes, n, att=0.018, rel=0.03, dip=0.25, vib_cents=16.0, vib_rate=5.8, rng=None, cuts=()):
    """Per-sample frequency and amplitude tracks for a monophonic line. notes: [(t, dur, midi, vel)]."""
    f = np.zeros(n)
    a = np.zeros(n)
    vib = np.zeros(n)
    for j, (t, d, m, v) in enumerate(notes):
        i0, i1 = ns(t), min(n, ns(t + d))
        if i1 <= i0:
            continue
        L = i1 - i0
        f[i0:i1] = float(hz(m))
        env = np.ones(L)
        ka, kr = min(L // 2, ns(att)), min(L // 2, ns(rel))
        env[:ka] = np.sin(0.5 * np.pi * np.linspace(0, 1, ka)) * (1 - dip) + dip if j else \
            np.sin(0.5 * np.pi * np.linspace(0, 1, ka))
        env[L - kr:] *= np.linspace(1, dip, kr)
        env *= 1.0 + 0.08 * hump(L, 0.35, 1.0)                     # a little swell in the bow stroke
        a[i0:i1] = np.maximum(a[i0:i1], env * v)
        if d > 0.3 and vib_cents > 0:
            tt = tvec(L)
            ph = rng.uniform(0, 6.28) if rng is not None else 0.0
            vib[i0:i1] = vib_cents * np.clip((tt - 0.12) / 0.15, 0, 1) * np.sin(2 * np.pi * vib_rate * tt + ph)
    # fill silent gaps with the previous pitch (no glide to 0 Hz), then a short portamento
    idx = np.where(f > 0, np.arange(n), 0)
    np.maximum.accumulate(idx, out=idx)
    f = f[idx]
    first = np.argmax(f > 0) if np.any(f > 0) else 0
    f[:first] = f[first] if n else 0
    g = math.exp(-1 / (0.012 * SR))
    f = lfilter([1 - g], [1, -g], f - f[0]) + f[0]
    for (tc, mc) in cuts:                                        # grace-note 'cuts' (Irish/medieval ornament)
        i0, i1 = ns(tc), min(n, ns(tc + 0.035))
        if 0 <= i0 < n:
            f[i0:i1] = float(hz(mc))
    return f * 2 ** (vib / 1200), a


def _additive(f, a, harm, fmax=10000.0, rng=None):
    """sum_k harm[k] sin(k phi) with harmonics above fmax muted (per sample)."""
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.zeros(len(f))
    for k, h in enumerate(harm, start=1):
        if h == 0:
            continue
        mask = (k * f < fmax).astype(float)
        if not mask.any():
            break
        y += h * np.sin(k * ph + (rng.uniform(0, 6.28) if rng is not None else 0)) * mask
    return y * a


def fiddle(notes, total, seed=11, bright=0.7, cuts=()):
    rng = np.random.default_rng(seed)
    n = ns(total)
    f, a = _note_tracks(notes, n, att=0.02, rel=0.035, dip=0.3, vib_cents=17, vib_rate=5.9, rng=rng, cuts=cuts)
    a = lp(a, 60)
    p = 1.0 + 0.35 * (1 - bright)
    harm = [1.0 / k ** p for k in range(1, 24)]
    y = _additive(f * (1 + 0.0012 * smooth_rand(rng, n, 9, -1, 1)), a, harm, 9500, rng)
    ph = 2 * np.pi * np.cumsum(f) / SR
    bow = bp(white(rng, n), 1800, 7000) * a * (0.6 + 0.4 * np.sin(ph)) * 0.05
    scr = np.zeros(n)
    for t, d, m, v in notes:                                      # bow 'scratch' at each attack
        k = ns(0.025)
        place(scr, bp(white(rng, k), 2000, 6500) * np.exp(-tvec(k) / 0.008) * 0.12 * v, ns(t))
    y = fftconvolve(y + bow + scr, _body_ir(VIOLIN_BODY, seed))[:n]
    y = peq(y, 1250, 3.0, 1.0)                                    # vielle nasal
    y = peq(y, 2600, 2.0, 1.2)                                    # the bridge hill: bite for the jig
    return hp(y, 180)


def reed(notes, total, seed=13, odd_only=0.12, formants=((1150, 9, 2.5), (2700, 6, 3.0)), vib=0.0):
    """Crumhorn / reed: odd-harmonic buzz through nasal formants; organ-like envelopes."""
    rng = np.random.default_rng(seed)
    n = ns(total)
    f, a = _note_tracks(notes, n, att=0.012, rel=0.02, dip=0.0, vib_cents=vib, rng=rng)
    a = lp(a, 80)
    harm = [(1.0 / k) if k % 2 == 1 else odd_only / k for k in range(1, 30)]
    y = _additive(f * (1 + 0.002 * smooth_rand(rng, n, 4, -1, 1)), a, harm, 8000, rng)
    for fc, g, q in formants:
        y = peq(y, fc, g, q)
    y = lp(y, 5000)
    y += 0.02 * bp(white(rng, n), 1500, 5000) * a
    return hp(y, 120)


def hurdy_drone(total, pitches=(50, 57), seed=17, buzz_times=()):
    """Hurdy-gurdy drone on D/A: bowed by the wheel (sawtooth spectrum), wheel noise, trompette buzz."""
    rng = np.random.default_rng(seed)
    n = ns(total)
    t = tvec(n)
    y = np.zeros(n)
    for m in pitches:
        f = np.full(n, float(hz(m))) * (1 + 0.0015 * smooth_rand(rng, n, 3, -1, 1))
        a = 0.85 + 0.15 * smooth_rand(rng, n, 4.0, -1, 1)
        y += _additive(f, a, [1.0 / k ** 1.1 for k in range(1, 40)], 7000, rng)
    y = peq(peq(y, 420, 4.0, 1.2), 1800, 5.0, 1.5)
    y += 0.03 * bp(white(rng, n), 900, 4000)
    if buzz_times:                                                 # the 'dog' rattles on the beats
        bz = np.zeros(n)
        car = np.sign(np.sin(2 * np.pi * float(hz(62)) * t))
        for tb, v in buzz_times:
            k = ns(0.09)
            seg = car[ns(tb): ns(tb) + k]
            if len(seg) == k:
                place(bz, seg * hump(k, 0.15, 0.8) * v, ns(tb))
        y += 0.5 * bp(bz, 600, 5000)
    return hp(y, 60)


def stomp(rng):
    n = ns(0.35)
    t = tvec(n)
    f = rng.uniform(62, 80) * (1 + 0.35 * np.exp(-t / 0.008))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 2 * np.pi)) * np.exp(-t / 0.05)   # random phase:
    y *= np.clip(t / 0.002, 0, 1)                                                                # no coherent sum
    y += 0.4 * burst(rng, n, 0.0035, hi=700)
    body = FX.excite(burst(rng, ns(0.004), 0.0015, hi=1500), modes(rng, FX.WOOD_FLOOR[:4], ns(0.2)))
    y += 0.4 * fit(body, n)
    return lp(y, 2500)


def clap(rng):
    n = ns(0.12)
    y = burst(rng, n, rng.uniform(0.004, 0.009), 700, 6000)
    y = FX.reson(y, rng.uniform(900, 2400), 3.0) * 0.6 + y
    return y


def crowd_hits(times, rng, maker, people=12, jitter=0.016, pan=0.85):
    """Many people hitting together (stomps / claps): jittered, panned, varied."""
    span = max(t for t, v in times) + 0.6
    out = np.zeros((ns(span), 2))
    for t, v in times:
        for _ in range(people):
            h = maker(rng) * v * rng.uniform(0.5, 1.0)
            place(out, stereo(h, rng.uniform(-pan, pan)), ns(t + rng.normal(0, jitter)))
    return out


LUTE_CHORDS_EXTRA = {}


def tavern_band(ctx, verbose=False):
    """Scene-4 jig with perspective + swell; scene-local stereo over [-pre, dur + post]."""
    dur, pre, post = ctx["dur"], ctx.get("pre", 0.5), ctx.get("post", 0.5)
    beats = ctx.get("beats", {})
    t_sw = beats.get("s4_swell", (10.8, None))[0]
    bar = 6 * M.eighth_seconds(TAVERN_TEMPO)
    T0 = t_sw - 10 * bar                              # bar b starts at T0 + b*bar (b may be negative)
    b_first = int(math.floor((-pre - T0) / bar)) + 1               # first bar fully inside the pre-roll
    b_last = int(math.ceil((dur + post - T0) / bar)) + 1
    total = dur + pre + post
    off = pre                                         # array time = local time + pre
    # --- form ---------------------------------------------------------------------------------------
    form = {}
    for b in range(b_first, b_last + 1):
        if b < 0:
            form[b] = ("A", 8 + b)                    # A7, A8 ... (bars 6, 7 zero-based)
        elif b < 8:
            form[b] = ("B", b)
        elif b < 10:
            form[b] = ("A", b - 8)                    # the break: A1 A2
        elif b < 18:
            form[b] = ("B", b - 10)
        else:
            form[b] = ("A", (b - 18) % 8)
    energy = {b: ("break" if b in (8, 9) else "swell" if b in (10, 11, 12) else "ease" if b == 13 else "normal")
              for b in form}
    # --- melody notes ---------------------------------------------------------------------------------
    mel, cuts = [], []
    rng = np.random.default_rng(404)
    for b, (part, k) in sorted(form.items()):
        tb = T0 + b * bar + off
        notes = (JIG_A if part == "A" else JIG_B)[k]
        pos = 0
        e = energy[b]
        for j, (m, ln) in enumerate(notes):
            v = {"normal": 0.75, "break": 0.0, "swell": 1.0, "ease": 0.85}[e]
            v *= 1.0 if pos in (0, 3) else 0.82                   # jig accents on the beats
            t = tb + pos * bar / 6
            d = ln * bar / 6 * (0.92 if ln == 1 else 0.96)
            if v > 0:
                mel.append((t, d, m, v))
                if ln >= 2 and pos in (0, 3) and rng.uniform() < (0.6 if part == "B" else 0.35):
                    cuts.append((t, m + (2 if m % 12 not in (4, 11) else 1)))
            pos += ln
    fid = fiddle(mel, total, seed=11, bright=0.75, cuts=cuts)
    crum_notes = [(t, d, m - 12, v * (0.55 if energy_at(t - off, T0, bar, energy) == "normal" else 1.0))
                  for (t, d, m, v) in mel]
    # in the break the crumhorn carries a soft melody alone (A1 A2)
    for b in (8, 9):
        tb = T0 + b * bar + off
        pos = 0
        for m, ln in JIG_A[b - 8]:
            crum_notes.append((tb + pos * bar / 6, ln * bar / 6 * 0.95, m - 12, 0.7))
            pos += ln
    crum = reed(sorted(crum_notes), total, seed=13)
    # --- lute ----------------------------------------------------------------------------------------
    S = SONG.Strokes()
    chords = {}
    g = SONG.Grid(T0 + b_first * bar + off, TAVERN_TEMPO, b_last - b_first + 2)
    for b, (part, k) in sorted(form.items()):
        chords[b - b_first] = (JIG_A_CHORDS if part == "A" else JIG_B_CHORDS)[k]
    for b in sorted(form):
        e = energy[b]
        vel = {"normal": 0.62, "break": 0.42, "swell": 0.9, "ease": 0.75}[e]
        SONG.lute_bar(S, g, chords, b - b_first, "strum", vel=vel, rng=rng)
    S.plucks = [p_ for p_ in S.plucks if 0.0 <= p_.t < total]
    S.damp_all(total)
    changes = [(g.t(bb, 3 * h), SONG.chord_at(chords, bb, h)) for bb in sorted(chords) for h in (0, 1)]
    SONG._damp_on_changes(S, changes)
    lute = fit(SONG.render_lute(S.plucks, total), ns(total))
    # --- drone ---------------------------------------------------------------------------------------
    buzz = []
    for b in (10, 11, 12):
        for p in (0, 3):
            buzz.append((T0 + b * bar + p * bar / 6 + off, 1.0 if p == 0 else 0.7))
    drone = hurdy_drone(total, seed=17, buzz_times=buzz)
    # --- percussion ----------------------------------------------------------------------------------
    hits = []
    for b in sorted(form):
        tb = T0 + b * bar + off
        e8 = bar / 6
        e = energy[b]
        if e in ("normal", "ease"):
            hits += [(tb, "doum", 0.8), (tb + 2 * e8, "tek", 0.35), (tb + 3 * e8, "doum", 0.6),
                     (tb + 5 * e8, "tek", 0.35)]
            hits += [(tb + i * e8, "jingle", 0.3 if i in (0, 3) else 0.15) for i in range(6)]
        elif e == "break":
            hits += [(tb, "doum", 0.55), (tb + 3 * e8, "doum", 0.35), (tb, "jingle", 0.15),
                     (tb + 3 * e8, "jingle", 0.12)]
            if b == 9:                                                   # roll into the swell
                for i in range(12):
                    hits.append((tb + 3 * e8 + i * e8 / 4, "tek", 0.2 + 0.5 * i / 11))
        else:
            hits += [(tb, "doum", 1.0), (tb + e8, "tek", 0.5), (tb + 2 * e8, "tek", 0.6), (tb + 3 * e8, "doum", 0.9),
                     (tb + 4 * e8, "tek", 0.5), (tb + 5 * e8, "tek", 0.6)]
            hits += [(tb + i * e8, "jingle", 0.45 if i in (0, 3) else 0.3) for i in range(6)]
    hits = [h_ for h_ in hits if 0.0 <= h_[0] < total]
    drum, tamb = SONG.render_hits(hits, total, seed=41)
    drum, tamb = fit(drum, ns(total)), fit(tamb, ns(total))
    # --- the room stomps and claps in the swell: BOOM - BOOM CLAP --------------------------------------
    st_times, cl_times = [], []
    for b in (10, 11, 12, 13):
        tb = T0 + b * bar + off
        v = 1.0 if b < 13 else 0.5
        st_times += [(tb, v), (tb + 2 * bar / 6, 0.8 * v)]
        cl_times += [(tb + 3 * bar / 6, v)]
    stomps = fit(crowd_hits(st_times, rng, stomp, 12, 0.018), ns(total))
    claps = fit(crowd_hits(cl_times, rng, clap, 16, 0.014), ns(total))
    # --- band mix (inside, at the 'normal' reference) ----------------------------------------------------
    def norm(x, db):
        """RMS over the ACTIVE part only (sparse layers are not boosted for their silences)."""
        e = np.abs(x) if x.ndim == 1 else np.abs(x).max(axis=1)
        env = np.convolve(e, np.ones(4800) / 4800, "same")
        act = env > env.max() * 10 ** (-40 / 20)
        r = np.sqrt(np.mean(x[act] ** 2)) + 1e-12
        return x / r * 10 ** (db / 20)

    def pnorm(x, db):
        return x / (np.abs(x).max() + 1e-12) * 10 ** (db / 20)
    drum, tamb = lp(drum, 10000, 4), lp(tamb, 14000, 4)          # soften the noise-burst onsets
    band = (stereo(norm(fid, -16.0), -0.35) + stereo(norm(crum, -24.0), 0.3) + stereo(norm(drone, -31.0), 0.12)
            + stereo(norm(lute, -22.0), -0.12) + stereo(pnorm(drum, -9.0), 0.05) + stereo(pnorm(tamb, -19.0), 0.45))
    band += pnorm(stomps, -11.0) + pnorm(claps, -14.0)
    band = band + 0.22 * FX.reverb(band, "tavern")[: len(band)]
    # --- automation: break -6 dB, swell +5 dB (fast up, held, eased back) ---------------------------------
    t = tvec(len(band)) - off
    g_db = np.zeros(len(band))
    tb8, tb10, tb13, tb14 = (T0 + k * bar for k in (8, 10, 13, 14))
    g_db += -3.0 * np.clip((t - tb8 + 0.3) / 0.3, 0, 1) * np.clip((tb10 - t) / 0.06, 0, 1)
    g_db += 5.0 * np.clip((t - tb10 + 0.02) / 0.12, 0, 1) * np.clip((tb14 - t) / (tb14 - tb13 + 0.4), 0, 1)
    band *= (10 ** (g_db / 20))[:, None]
    # --- perspective (shared with the tavern ambience) --------------------------------------------------
    g_in = FX.perspective_gain(ctx, len(band), off, True)
    g_out = FX.perspective_gain(ctx, len(band), off, False)
    out = band * g_in[:, None] + FX.muffle(band) * g_out[:, None]
    gate = np.clip(np.minimum((t + 0.004) / 0.008, (dur - t) / 0.008), 0, 1)   # hard cuts in and out
    out *= gate[:, None]
    info = dict(T0=T0, bar=bar, form={int(b): f"{p}{k + 1}" for b, (p, k) in form.items()},
                energy={int(b): e for b, e in energy.items()})
    return out, info


def energy_at(t, T0, bar, energy):
    b = int(math.floor((t - T0) / bar + 1e-9))
    return energy.get(b, "normal")


# ================================================================================================
# 3. SCORE: piano / harp / celesta
# ================================================================================================
@dataclass
class Ev:
    t: float          # global seconds
    dur: float        # key held (pedal) seconds
    midi: int
    vel: float        # 0..1
    inst: str         # piano | harp | celesta


def piano_note(midi, vel, dur, rng, release=0.18):
    f0 = float(hz(midi))
    B = float(np.clip(3.8e-4 * 2 ** ((midi - 60) / 19.0), 6e-5, 3e-3))
    x0 = 0.12 + 0.01 * rng.standard_normal()
    tau0 = 2.6 * (261.6 / f0) ** 0.62
    alpha = 1.25 - 0.45 * vel
    fc = 1100 + 5200 * vel ** 1.5
    tail = release * 6
    n = ns(dur + tail)
    t = tvec(n)
    damp = np.where(t < dur, 1.0, np.exp(-(t - dur) / release))
    y = np.zeros(n)
    kmax = int(min(28, 12000 / f0))
    for k in range(1, kmax + 1):
        fk = k * f0 * math.sqrt(1 + B * k * k)
        if fk > 16000:
            break
        ak = abs(math.sin(math.pi * k * x0)) * k ** (-alpha) * math.exp(-(fk / fc) ** 1.3)
        if ak < 1e-4:
            continue
        t1 = tau0 / (1 + 0.09 * (k - 1) ** 1.25)
        t2 = 3.6 * t1
        L = min(n, ns(min(dur + tail, 7 * t2)))
        env = 0.7 * np.exp(-t[:L] / t1) + 0.3 * np.exp(-t[:L] / t2)
        strings = (-1, 1) if k <= 10 else (0,)
        for s in strings:
            det = 1 + s * rng.uniform(0.25, 0.9) / 1731.0
            y[:L] += ak / len(strings) * np.sin(2 * np.pi * fk * det * t[:L] + rng.uniform(0, 6.28)) * env
    y *= damp
    att = ns(0.0025 - 0.0012 * vel)
    y[:att] *= np.sin(0.5 * np.pi * np.linspace(0, 1, att))
    ham = lp(burst(rng, ns(0.03), 0.004), 2500 + 2500 * vel) * (0.015 + 0.05 * vel)
    knock = np.sin(2 * np.pi * 95 * tvec(ns(0.08))) * np.exp(-tvec(ns(0.08)) / 0.018) * 0.03 * vel
    place(y, ham, 0)
    place(y, knock, 0)
    return y * vel ** 1.5


def harp_note(midi, vel, dur, rng):
    f0 = float(hz(midi))
    p = 0.45 + 0.04 * rng.standard_normal()
    tau0 = min(3.0, 3.0 * (220.0 / f0) ** 0.6)
    n = ns(min(dur, 1.8 * tau0) + 0.6)
    t = tvec(n)
    y = np.zeros(n)
    glide = 1 + 0.0009 * np.exp(-t / 0.03)
    ph = 2 * np.pi * np.cumsum(f0 * glide) / SR
    for k in range(1, 16):
        if k * f0 > 9000:
            break
        ak = abs(math.sin(math.pi * k * p)) / k ** 1.15 * math.exp(-k * f0 / (1800 + 3500 * vel))
        tk = tau0 / k ** 0.75
        L = min(n, ns(7 * tk))
        y[:L] += ak * np.sin(k * ph[:L] + rng.uniform(0, 6.28)) * np.exp(-t[:L] / tk)
    y *= np.clip(t / 0.0015, 0, 1)
    rel = np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.35))       # (harpist damps when told to)
    y *= rel
    place(y, lp(burst(rng, ns(0.01), 0.0015), 2200) * 0.05 * vel, 0)
    return fade(y * vel ** 1.3, 0.0, 0.05)


def celesta_note(midi, vel, dur, rng):
    f0 = float(hz(midi))
    tau = 1.5 * (523.0 / f0) ** 0.5
    n = ns(min(dur, 3 * tau) + 0.5)
    t = tvec(n)
    y = np.zeros(n)
    for r, a, tk in ((1.0, 1.0, tau), (2.76, 0.09, 0.16), (5.40, 0.04, 0.06), (4.0, 0.03, 0.25)):
        if f0 * r > 15000:
            continue
        y += a * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6.28)) * np.exp(-t / tk)
    y *= np.clip(t / 0.002, 0, 1)
    y *= np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.3))
    place(y, lp(burst(rng, ns(0.01), 0.002), 1600) * 0.04 * vel, 0)
    return fade(y * vel ** 1.2, 0.0, 0.05)


INSTR = {"piano": piano_note, "harp": harp_note, "celesta": celesta_note}


def _roll(ev, t, notes, vel, inst, dur, spread=0.07, accent_top=0.0):
    for i, m in enumerate(sorted(notes)):
        ev.append(Ev(t + i * spread, max(0.2, dur - i * spread), int(m), vel * (1 + accent_top * (i == len(notes) - 1)),
                     inst))


def _open_sus(ev, t_open, pc=2, lead=0.12):
    """Asus4 -> A: the suspended D must give way to the C# -- every D still held when the third enters is
    damped just before it (a D ringing on under C#4 is a minor-second rub, not warmth)."""
    for e in ev:
        if e.midi % 12 == pc and e.t < t_open < e.t + e.dur:
            e.dur = max(0.12, t_open - lead - e.t)


def _arp(ev, t0, t1, notes, vel, inst, step=0.3, pattern=(0, 1, 2, 3, 2, 1)):
    i = 0
    t = t0
    ns_ = sorted(notes)
    while t < t1 - 0.05:
        m = ns_[pattern[i % len(pattern)] % len(ns_)]
        ev.append(Ev(t, max(0.6, t1 - t + 0.4), int(m), vel * (1.0 if i % 3 == 0 else 0.85), inst))
        t += step
        i += 1


def score_events(tl=None):
    """The score as a list of Ev in GLOBAL seconds, placed from timeline beats / lines (follows retiming)."""
    if tl is None:
        from film.lib import timeline as tl
    sc = {k: tl.scene(k) for k in (6, 7, 8, 9)}

    def G(s, t):
        return sc[s].start + t

    def bt(bid, d):
        return tl.beat(bid).t if tl.has_beat(bid) else d

    def be(bid, d):
        b = tl.beat(bid) if tl.has_beat(bid) else None
        return d if (b is None or b.end is None) else b.end

    def ln(lid, d):
        return tl.line(lid) if tl.has_line(lid) else d

    mel = M.motif(12)                                   # B4 A4 F#4 E4
    ev = []
    # ---- S6: at the laugh, the bare motif, high and soft, rubato ---------------------------------------
    L = bt("s6_laugh", 27.19)
    for k, dt in enumerate((0.30, 1.12, 1.95, 2.95)):
        ev.append(Ev(G(6, L + dt), 2.6 if k < 3 else 5.0, mel[k], 0.40 if k < 3 else 0.44, "harp"))
        ev.append(Ev(G(6, L + dt + 0.015), 1.6 if k < 3 else 3.0, mel[k] + 12, 0.20, "celesta"))
    # ---- S7 statement 1: harp, a whisper of piano ---------------------------------------------------------
    t1 = bt("s7_hand", 1.8) + 0.4
    gap = 2.35
    for i, ch in enumerate(M.WARM_HARMONY):
        t = G(7, t1 + i * gap)
        v = M.voicing(ch, low=38, high=69, n=4)
        _roll(ev, t, v[1:], 0.26, "harp", gap + 1.0, spread=0.09)
        ev.append(Ev(t + 0.30, gap + 0.9, mel[i], 0.44, "harp"))
        ev.append(Ev(t, gap + 0.3, v[0], 0.18, "piano"))
        if i >= 1:
            for m in v[1:]:
                ev.append(Ev(t + 0.05, gap + 0.2, m, 0.13, "piano"))
    t_ts = G(7, bt("s7_teensit", 9.8) + 0.35)                          # the sus4 opens when the teen sits
    _open_sus(ev, t_ts)
    ev.append(Ev(t_ts, 1.8, 61, 0.26, "harp"))
    ev.append(Ev(t_ts + 0.02, 1.5, 61, 0.14, "piano"))
    # ---- S7 statement 2: piano melody on each arrival, harp arpeggios, celesta echoes ---------------------
    times = [bt("s7_driver", 11.5), bt("s7_worker", 13.5), bt("s7_full", 15.0), bt("s7_drag", 15.5) + 1.0]
    t_A = be("s7_drag", 18.0)
    for i, ch in enumerate(M.WARM_HARMONY):
        a = times[i]
        b = times[i + 1] if i < 3 else t_A
        v = M.voicing(ch, low=38, high=69, n=4)
        ev.append(Ev(G(7, a), b - a + 0.5, mel[i], 0.50, "piano"))
        ev.append(Ev(G(7, a), b - a + 0.3, v[0], 0.30, "piano"))
        for j, m in enumerate(v[1:]):
            ev.append(Ev(G(7, a) + 0.03 * (j + 1), b - a + 0.2, m, 0.19, "piano"))
        _arp(ev, G(7, a) + 0.3, G(7, b), list(v[1:]) + [v[1] + 12], 0.17, "harp", step=0.46,
             pattern=(0, 1, 2, 3, 2, 1))
        ev.append(Ev(G(7, a) + 1.0, 1.4, mel[i] + 12, 0.16, "celesta"))
    va = M.voicing("A", low=38, high=69, n=4)                          # sus4 -> 3 at the end of the drag
    _open_sus(ev, G(7, t_A))
    for j, m in enumerate(va):
        ev.append(Ev(G(7, t_A) + 0.03 * j, 2.4, m, 0.22 if j else 0.26, "piano"))
    # ---- S7 under the dialogue: sparse held chords between lines; rising harp into S8 ---------------------
    l1, l2, l3 = ln("s7_l1", None), ln("s7_l2", None), ln("s7_l3", None)
    e1 = l1.end if l1 else 19.8
    e2 = l2.end if l2 else 23.3
    e3 = l3.end if l3 else 27.1
    s2_ = l2.start if l2 else 20.6
    gm = M.voicing("Gmaj7", low=38, high=69, n=4)
    _roll(ev, G(7, e1 + 0.3), gm[1:], 0.2, "harp", (e2 + 0.3) - (e1 + 0.3) + 0.6, spread=0.1)
    for m in gm[1:]:
        ev.append(Ev(G(7, e1 + 0.35), (e2 + 0.3) - (e1 + 0.35), m, 0.13, "piano"))
    dfs = M.voicing("D/F#", low=38, high=69, n=4)
    _roll(ev, G(7, e2 + 0.3), dfs[1:], 0.2, "harp", (e3 + 0.35) - (e2 + 0.3) + 0.6, spread=0.1)
    ev.append(Ev(G(7, e2 + 0.55), 2.0, mel[1], 0.2, "harp"))           # a hint of the melody (A4)
    for m in dfs[1:]:
        ev.append(Ev(G(7, e2 + 0.35), (e3 + 0.35) - (e2 + 0.35), m, 0.13, "piano"))
    t_up = e3 + 0.35
    for i, m in enumerate((54, 57, 62, 66, 69, 74)):
        ev.append(Ev(G(7, t_up + i * 0.36), 2.2, m, 0.22 + 0.025 * i, "harp"))
    del s2_
    # ---- S8 statement 3: full bloom; each motif note answers a voice-over line ----------------------------
    v1, v2, v3 = ln("s8_l1", None), ln("s8_l2", None), ln("s8_l3", None)
    tb_ = [0.35, (v1.end if v1 else 4.45) + 0.35, (v2.end if v2 else 9.55) + 0.30, (v3.end if v3 else 14.8) + 0.30]
    tA8 = min(tb_[3] + 1.7, sc[8].duration - 3.0)
    for i, ch in enumerate(M.WARM_HARMONY):
        a = tb_[i]
        b = tb_[i + 1] if i < 3 else tA8
        v = M.voicing(ch, low=36, high=69, n=5)
        ev.append(Ev(G(8, a), b - a + 0.6, mel[i], 0.55, "piano"))
        ev.append(Ev(G(8, a) + 0.01, b - a + 0.6, mel[i] + 12, 0.30, "piano"))
        ev.append(Ev(G(8, a), b - a + 0.4, v[0], 0.34, "piano"))
        for j, m in enumerate(v[1:]):
            ev.append(Ev(G(8, a) + 0.03 * (j + 1), b - a + 0.3, m, 0.2, "piano"))
        # five DISTINCT chord tones (v[1] + 12 duplicated v[3] or v[4]: the harp re-plucked D4-D4, F#4-F#4)
        arp = sorted(set(list(v[2:]) + [v[1] + 12, v[2] + 12, v[3] + 12]))[:5]
        _arp(ev, G(8, a) + 0.35, G(8, b), arp, 0.16, "harp", step=0.42, pattern=(0, 1, 2, 3, 4, 3, 2, 1))
        ev.append(Ev(G(8, a) + 1.1, 1.6, mel[i] + 12, 0.17, "celesta"))
        if i < 3:                                         # an echo falling to a tone of the chord, never to D:
            ev.append(Ev(G(8, a) + 1.6, 1.6, mel[i] + 12 - (2, 3, 2)[i], 0.13, "celesta"))   # B-A, A-F#, F#-E
    va = M.voicing("A", low=36, high=69, n=5)
    _open_sus(ev, G(8, tA8))
    tail = sc[8].duration - tA8 + 4.0                     # ring through the fade into the end card
    for j, m in enumerate(va):
        ev.append(Ev(G(8, tA8) + 0.04 * j, tail, m, 0.3 if j == 0 else 0.22, "piano"))
    ev.append(Ev(G(8, tA8), tail, mel[3], 0.34, "piano"))  # E4 stays on top: unresolved
    _roll(ev, G(8, tA8) + 0.2, [v_ + 12 for v_ in va[1:]], 0.18, "harp", tail, spread=0.12)
    # ---- S9: the final chord blooms with the reprise's last chord ----------------------------------------
    tf = bt("s9_final_chord", 14.147)
    tend = sc[9].duration + 0.2
    d9 = [38, 45, 50, 54, 57, 64]                         # D2 A2 D3 F#3 A3 E4 = D(add9)
    for j, m in enumerate(d9):
        ev.append(Ev(G(9, tf) + 0.035 * j, tend - tf, m, 0.30 if j == 0 else 0.22, "piano"))
    _roll(ev, G(9, tf) + 0.12, [62, 66, 69, 76], 0.2, "harp", tend - tf, spread=0.11)
    ev.append(Ev(G(9, tf) + 0.55, tend - tf, 78, 0.14, "celesta"))
    ev.append(Ev(G(9, tf) + 1.05, tend - tf, 81, 0.11, "celesta"))
    return sorted(ev, key=lambda e: e.t)


PAN = {"piano": 0.0, "harp": -0.28, "celesta": 0.32}
LEVEL_DB = {"piano": 0.0, "harp": -1.0, "celesta": -4.0}


def render_score(events, total, seed=61):
    """Events (global time) -> stereo array of length `total` seconds, with the warm hall."""
    rng = np.random.default_rng(seed)
    n = ns(total)
    out = np.zeros((n, 2))
    for e in events:
        y = INSTR[e.inst](e.midi, e.vel, e.dur, rng)
        p = PAN[e.inst] + (0.35 * (e.midi - 60) / 24.0 if e.inst == "piano" else 0.0)
        place(out, stereo(y * 10 ** (LEVEL_DB[e.inst] / 20), float(np.clip(p, -0.8, 0.8))), ns(e.t))
    wet = FX.reverb(out, "far" if False else "nook")[:n] * 0.0
    hall = _score_hall()
    wet = np.stack([fftconvolve(out[:, 0], hall[:, 0])[:n], fftconvolve(out[:, 1], hall[:, 1])[:n]], 1)
    out = out + 0.32 * wet * (np.sqrt(np.mean(out ** 2)) / (np.sqrt(np.mean(wet ** 2)) + 1e-12))
    return out


_HALL = None


def _score_hall():
    global _HALL
    if _HALL is None:
        h = SONG.hall_ir(2.1, 0.022, seed=63)
        h = lp(h, 6500)
        _HALL = h / np.sqrt(np.sum(h * h, axis=0, keepdims=True))
    return _HALL


# The score's dynamic arc (dB relative to the S8 bloom), applied as smooth fader moves measured on the render:
# pp at the laugh, p for the first harmonized statement, mp as the bench fills, held back under the S7 lines,
# full bloom under the voice-over, p for the final chord under the reprise.
SCORE_ARC = (("entry", -8.0), ("st1", -5.0), ("st2", -2.5), ("under", -4.5), ("bloom", 0.0), ("final", -3.0))


def score_sections(tl):
    """[(name, t_from, t_to)] in global seconds (each section's fader zone)."""
    sc = {k: tl.scene(k) for k in (6, 7, 8, 9)}

    def bt(bid, d):
        return tl.beat(bid).t if tl.has_beat(bid) else d
    l1 = tl.line("s7_l1").start if tl.has_line("s7_l1") else 18.6
    t1 = bt("s7_hand", 1.8) + 0.4
    z = [sc[6].start + bt("s6_laugh", 27.19), sc[7].start + t1 - 0.4, sc[7].start + bt("s7_driver", 11.5) - 0.4,
         sc[7].start + l1 - 0.6, sc[8].start - 0.2, sc[9].start + bt("s9_final_chord", 14.147) - 0.4, tl.total()]
    return [(name, z[i], z[i + 1]) for i, (name, _) in enumerate(SCORE_ARC)]


def score_arc_gain(x, tl, ramp=0.7):
    """Per-sample gain giving each section its SCORE_ARC level (measured, BS.1770), smooth 0.7 s fader moves."""
    secs = score_sections(tl)
    lv = {}
    for name, a, b in secs:
        seg = x[ns(a): ns(b)]
        lv[name] = FX.lufs(seg) if len(seg) > ns(0.5) and np.any(seg) else -70.0
    ref = lv["bloom"]
    target = dict(SCORE_ARC)
    g_db = {name: (ref + target[name] - lv[name]) if lv[name] > -69 else 0.0 for name, _, _ in secs}
    n = len(x)
    t = tvec(n)
    g = np.full(n, g_db[secs[0][0]])
    for (name, a, b), (nxt, a2, _) in zip(secs[:-1], secs[1:]):
        w = np.clip((t - (a2 - ramp)) / ramp, 0, 1)
        w = 0.5 - 0.5 * np.cos(np.pi * w)
        g = g * (1 - w) + g_db[nxt] * w
    return 10 ** (g / 20), {k: round(v, 2) for k, v in g_db.items()}, {k: round(v, 2) for k, v in lv.items()}


def score(tl=None, info=None):
    """-> (stereo float64 array over the WHOLE film (global time), events).  The arc (SCORE_ARC) is applied;
    the 'bloom' section keeps its rendered level (the mix sets the absolute level from it)."""
    if tl is None:
        from film.lib import timeline as tl
    ev = score_events(tl)
    total = tl.total()
    x = render_score(ev, total + 0.5)[: ns(total)]
    x = FX.shelf(x, 160, -2.5, high=False)                   # lighter low end: tender, not syrupy
    g, gdb, lv = score_arc_gain(x, tl)
    if info is not None:
        info.update(arc_gain_db=gdb, arc_raw_lufs=lv, sections=[(n_, round(a, 3), round(b, 3))
                                                                for n_, a, b in score_sections(tl)])
    return x * g[:, None], ev


# ================================================================================================
if __name__ == "__main__":
    import soundfile as sf
    import time as _time
    from film.lib import timeline as TL
    out_dir = os.path.join(FILM, "build", "audio")
    os.makedirs(out_dir, exist_ok=True)

    def ctx_for(s):
        sc = TL.scene(s)
        return {"dur": sc.duration, "pre": 0.5, "post": 0.5,
                "beats": {b.id: (b.t, b.end) for b in TL.beats_in(s)},
                "lines": [(l.id, l.start, l.end, l.speaker) for l in TL.lines_in(s)]}
    t0 = _time.time()
    h, ev = hold_music(ctx_for(3))
    sf.write(os.path.join(out_dir, "music_hold.wav"), np.clip(h / (np.abs(h).max() + 1e-9) * 0.5, -1, 1), SR,
             subtype="PCM_24")
    print(f"hold music {len(ev)} notes, {_time.time() - t0:.1f}s")
    t0 = _time.time()
    b, info = tavern_band(ctx_for(4))
    sf.write(os.path.join(out_dir, "music_tavern.wav"), np.clip(b / (np.abs(b).max() + 1e-9) * 0.7, -1, 1), SR,
             subtype="PCM_24")
    print(f"tavern band {len(b) / SR:.1f}s, {_time.time() - t0:.1f}s; form {info['form']}")
    t0 = _time.time()
    s, ev = score()
    a = ns(TL.scene(6).start)
    sf.write(os.path.join(out_dir, "music_score.wav"), np.clip(s[a:] / (np.abs(s).max() + 1e-9) * 0.7, -1, 1), SR,
             subtype="PCM_24")
    print(f"score {len(ev)} events, {_time.time() - t0:.1f}s")
