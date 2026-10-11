"""Score: synthesized music cues, rendered to a stereo bed."""
import numpy as np
import audio_lib as A
from audio_lib import n, midi_hz, SR


class Buf:
    def __init__(self, dur):
        self.b = np.zeros((int((dur + 4.0) * SR), 2))

    def add(self, clip, t, gain=1.0, pan=0.0):
        A.place(self.b, clip, t, gain, pan)


def humanize(rng, t, amt=0.012):
    return t + rng.normal(0, amt)


# ------------------------------------------------------------------ cues
def cue_clock(d, ctx):
    B = Buf(d)
    t = 0.3
    k = 0
    while t < d:
        B.add(A.sfx_tick(1.0, tock=(k % 2 == 1)), t, 0.8, 0.3)
        t += 1.0
        k += 1
    return B.b, -27


MOTIF_C = [  # (bar, beat, note, beats)
    (0, 0, "G4", 1), (0, 1, "C5", 1), (0, 2, "D5", 1), (0, 3, "E5", 1),
    (1, 0, "E5", 2), (1, 2, "D5", 1), (1, 3, "C5", 1),
    (2, 0, "A4", 1), (2, 1, "C5", 1), (2, 2, "D5", 1), (2, 3, "F5", 1),
    (3, 0, "E5", 3), (3, 3, "D5", 1),
    (4, 0, "G4", 1), (4, 1, "C5", 1), (4, 2, "D5", 1), (4, 3, "E5", 1),
    (5, 0, "G5", 2), (5, 2, "E5", 1), (5, 3, "C5", 1),
    (6, 0, "D5", 1), (6, 1, "C5", 1), (6, 2, "A4", 1), (6, 3, "C5", 1),
    (7, 0, "C5", 4),
]
CHORDS_C = [["C3", "E3", "G3", "C4"], ["A2", "E3", "A3", "C4"], ["F2", "C3", "F3", "A3"], ["G2", "D3", "G3", "B3"]]


def cue_burst(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(1)
    # playful pizzicato run
    run = ["C4", "E4", "G4", "C5", "E5", "G5", "C6"]
    for i, nm in enumerate(run):
        B.add(A.pizz(midi_hz(n(nm)), 0.7, 0.9, seed=i), 0.05 + i * 0.075, 0.9, -0.3 + 0.1 * i)
    B.add(A.pizz(midi_hz(n("C3")), 1.0, 1.0, seed=99), 0.05, 0.8)
    # gentle class theme
    beat = 60 / 84
    bar = 4 * beat
    t0 = 1.6
    nbars = int((d - t0) / bar) + 1
    for b in range(nbars):
        tb = t0 + b * bar
        ch = CHORDS_C[b % 4] if b < 8 else CHORDS_C[0]
        if b >= 8:
            if b > 9:
                break
        freqs = [midi_hz(n(x)) for x in ch]
        B.add(A.pad(freqs, bar + 1.0, a=0.8, r=1.2, bright=900, seed=b), tb, 0.55)
        B.add(A.pizz(midi_hz(n(ch[0]) - 12 if n(ch[0]) > 45 else n(ch[0])), 1.0, 0.7, seed=b), tb, 0.6)
    for bar_i, bt, nm, beats in MOTIF_C:
        tt = t0 + bar_i * bar + bt * beat
        if tt < d:
            B.add(A.musicbox(midi_hz(n(nm)), 2.5, 0.6), humanize(rng, tt, 0.006), 0.55, 0.15)
    return B.b, -29


GUITAR = {
    "G": ["G2", "B2", "D3", "G3", "B3", "G4"],
    "Em": ["E2", "B2", "E3", "G3", "B3", "E4"],
    "C": ["C3", "E3", "G3", "C4", "E4"],
    "D": ["D3", "A3", "D4", "F#4"],
    "Am": ["A2", "E3", "A3", "C4", "E4"],
    "Dsus": ["D3", "A3", "D4", "G4"],
}


def strum(B, chord, t, down=True, vel=0.8, rng=None, ring=1.4, bright=0.45, gain=1.0):
    notes = GUITAR[chord]
    if not down:
        notes = notes[-4:][::-1]
        vel *= 0.6
    for i, nm in enumerate(notes):
        f = midi_hz(n(nm))
        y = A.ks_pluck(f, ring, bright=bright, decay=0.996, seed=int(rng.integers(1e6)))
        y = A.lowpass(y, 4500)
        B.add(y * vel * (0.85 + 0.3 * rng.random()), t + i * 0.011, 0.22 * gain, -0.2 + 0.08 * i)


def groove(B, d, rng, t0=0.0, gain=1.0, claps=False, prog=("G", "Em", "C", "D"), bpm=92):
    beat = 60 / bpm
    bar = 4 * beat
    pattern = [(0, True, 1.0), (1, True, 0.7), (1.5, False, 0.6), (2.5, False, 0.6), (3, True, 0.8), (3.5, False, 0.6)]
    nb = int((d - t0) / bar) + 1
    for b in range(nb):
        ch = prog[b % len(prog)]
        tb = t0 + b * bar
        for bt, dn, v in pattern:
            tt = tb + bt * beat
            if tt > d:
                break
            strum(B, ch, humanize(rng, tt, 0.008), dn, v, rng, ring=beat * 1.6, gain=gain)
        root = GUITAR[ch][0]
        r = n(root)
        if r > 45:
            r -= 12
        B.add(A.bass(midi_hz(r), beat * 1.8, 0.8), tb, 0.35 * gain)
        B.add(A.bass(midi_hz(r + 7), beat * 1.8, 0.7), tb + 2 * beat, 0.3 * gain)
        # shaker
        for k in range(8):
            tt = tb + k * beat / 2
            if tt > d:
                break
            nz = A.highpass(rng.normal(0, 1, int(0.06 * SR)), 5000) * np.exp(-np.arange(int(0.06 * SR)) / (0.012 * SR))
            B.add(nz * (0.5 if k % 2 else 0.8), humanize(rng, tt, 0.005), 0.05 * gain, 0.4)
        if claps:
            for bt in (1, 3):
                tt = tb + bt * beat
                L = int(0.12 * SR)
                c = A.bandpass(rng.normal(0, 1, L), 900, 3500) * np.exp(-np.arange(L) / (0.02 * SR))
                B.add(c, humanize(rng, tt, 0.006), 0.12 * gain, -0.2)


def cue_yard(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(2)
    groove(B, d, rng)
    out = B.b
    tf = ctx.get("fade_at")
    if tf is not None:
        tt = np.arange(len(out)) / SR
        g = np.clip(1 - (tt - tf) / 4.0, 0, 1)
        out = out * g[:, None]
    return out, -27


def cue_bridge(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(3)
    beat = 60 / 116
    bar = 4 * beat
    bassline = [["F2", "A2", "C3", "A2"], ["Bb2", "D3", "F3", "D3"], ["C3", "E3", "G3", "E3"], ["F2", "C3", "A2", "C3"]]
    mel = [
        [(0, "C5", .5), (1, "A4", .5), (1.5, "Bb4", .5), (2, "C5", 1)],
        [(0, "D5", .5), (0.5, "C5", .5), (1, "Bb4", .5), (2, "A4", 1)],
        [(0, "G4", .5), (0.5, "A4", .5), (1, "Bb4", .5), (1.5, "C5", .5), (2, "E5", 1)],
        [(0, "F5", 1.5), (2, "C5", .5), (3, "F4", .5)],
    ]
    nb = int(d / bar) + 1
    for b in range(nb):
        tb = b * bar
        for k, nm in enumerate(bassline[b % 4]):
            tt = tb + k * beat
            if tt < d:
                B.add(A.pizz(midi_hz(n(nm)), 0.5, 0.9, seed=int(rng.integers(1e6))), humanize(rng, tt, 0.006), 0.8, -0.15)
        for k in (1, 3):
            tt = tb + k * beat
            if tt < d:
                tw = A.t_axis(0.06)
                wb = np.sin(2 * np.pi * 1250 * tw) * np.exp(-tw * 70)
                B.add(wb, tt, 0.18, 0.35)
        if b >= 1:
            for bt, nm, bts in mel[b % 4]:
                tt = tb + bt * beat
                if tt < d:
                    B.add(A.clarinet(midi_hz(n(nm)), bts * beat * 0.75 + 0.1, 0.7), humanize(rng, tt, 0.008), 0.35, 0.2)
    return B.b, -29


def cue_flip(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(4)
    bar = 3.0
    prog = ["C", "D", "Em", "C", "Am", "D", "Dsus", "D"]
    pads = {"C": ["C3", "G3", "E4"], "D": ["D3", "A3", "F#4"], "Em": ["E3", "B3", "G4"],
            "Am": ["A2", "E3", "C4"], "Dsus": ["D3", "A3", "G4"]}
    nb = int(d / bar) + 1
    for b in range(nb):
        tb = b * bar
        ch = prog[min(b, len(prog) - 1)]
        prog_frac = min(1.0, b / max(1, nb - 1))
        B.add(A.pad([midi_hz(n(x)) for x in pads[ch]], bar + 1.2, a=1.0, r=1.0, bright=700 + 900 * prog_frac, seed=b), tb, 0.5 + 0.3 * prog_frac)
        tones = GUITAR[ch][-4:] if ch in GUITAR else pads[ch]
        steps = 6 if b < 3 else 8
        for k in range(steps):
            tt = tb + k * bar / steps
            if tt >= d:
                break
            nm = tones[k % len(tones)]
            f = midi_hz(n(nm) + 12)
            y = A.ks_pluck(f, 0.9, bright=0.5, decay=0.994, seed=int(rng.integers(1e6)))
            B.add(y, humanize(rng, tt, 0.006), 0.12 * (0.6 + 0.6 * prog_frac), 0.3 * np.sin(k))
    return B.b, -29


def cue_yard_bright(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(5)
    # big resolving G strum first
    strum(B, "G", 0.0, True, 1.0, rng, ring=2.5, bright=0.6, gain=1.3)
    groove(B, d, rng, t0=60 / 92 * 2, gain=1.0, claps=True)
    out = B.b
    tt = np.arange(len(out)) / SR
    g = np.clip(1 - (tt - (d - 1.5)) / 2.5, 0, 1)
    return out * g[:, None], -27


PORCH1 = [("B1", ["B2", "F#3", "A3", "D4", "F#4"]), ("G1", ["G2", "D3", "F#3", "B3", "D4"]),
          ("D2", ["D3", "A3", "D4", "F#4", "A4"]), ("A1", ["A2", "E3", "A3", "C#4", "E4"])]
PORCH2 = [("D2", ["D3", "A3", "D4", "F#4", "A4"]), ("C#2", ["A2", "E3", "A3", "C#4", "E4"]),
          ("B1", ["B2", "F#3", "B3", "D4", "F#4"]), ("G1", ["G2", "D3", "G3", "B3", "D4"])]


def piano_bed(B, d, prog, rng, t0=0.0, bpm=64, vel=0.45, melody=None, padgain=0.25):
    beat = 60 / bpm
    bar = 4 * beat
    nb = int((d - t0) / bar) + 1
    for b in range(nb):
        tb = t0 + b * bar
        if tb >= d:
            break
        root, tones = prog[b % len(prog)]
        B.add(A.piano(midi_hz(n(root) + 12), bar + 1.5, vel * 0.9, gate=bar * 0.95), humanize(rng, tb, 0.01), 0.5, -0.1)
        pattern = [0, 1, 2, 3, 4, 3, 2, 1]
        for k, pi in enumerate(pattern):
            tt = tb + k * beat / 2
            if tt >= d:
                break
            nm = tones[pi]
            B.add(A.piano(midi_hz(n(nm)), beat * 2.2, vel * (0.8 if k % 2 else 0.95) * rng.uniform(0.85, 1.05), gate=beat * 1.6),
                  humanize(rng, tt, 0.012), 0.42, 0.1 + 0.05 * pi)
        B.add(A.pad([midi_hz(n(x)) for x in tones[:3]], bar + 1.5, a=1.5, r=1.5, bright=800, seed=b), tb, padgain)
    if melody:
        for bar_i, bt, nm, beats in melody:
            tt = t0 + bar_i * bar + bt * beat
            if tt < d:
                B.add(A.piano(midi_hz(n(nm)), beats * beat + 1.5, vel * 1.1, gate=beats * beat), humanize(rng, tt, 0.01), 0.5, 0.0)


def cue_porch(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(6)
    mel = [(2, 0, "F#5", 2), (2, 2, "E5", 2), (3, 0, "E5", 3), (6, 0, "D5", 2), (6, 2, "C#5", 1), (6, 3, "D5", 1), (7, 0, "E5", 4),
           (10, 0, "F#5", 2), (10, 2, "A5", 2), (11, 0, "E5", 4)]
    piano_bed(B, d, PORCH1, rng, melody=mel)
    return B.b, -28


def cue_fortress(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(7)
    seg = 6.0
    prog = [["D2", "A2", "F3"], ["Bb1", "F2", "D3"], ["G1", "D2", "Bb2"], ["A1", "E2", "C#3"]]
    nb = int(d / seg) + 1
    for b in range(nb):
        tb = b * seg
        for k, nm in enumerate(prog[b % 4]):
            B.add(A.cello(midi_hz(n(nm)), seg + 1.5, 0.6, a=1.2, r=1.4), tb + k * 0.05, 0.35, -0.3 + 0.3 * k)
    # slow heartbeat
    t = 0.5
    while t < d:
        for off, g in ((0, 1.0), (0.28, 0.6)):
            tw = A.t_axis(0.25)
            hb = np.sin(2 * np.pi * 52 * tw * (1 - 0.3 * tw)) * np.exp(-tw * 16)
            B.add(hb, t + off, 0.5 * g)
        t += 1.35
    return B.b, -29


def cue_fortress_warm(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(8)
    B.add(A.pad([midi_hz(n(x)) for x in ["D3", "A3", "F#4", "A4"]], d + 1.0, a=2.0, r=2.0, bright=1300, seed=3), 0.0, 0.8)
    B.add(A.cello(midi_hz(n("D2")), d + 1.0, 0.6, a=1.5, r=2.0), 0.0, 0.3)
    beat = 60 / 72
    motif = [(0, "A4", 1), (1, "D5", 1), (2, "E5", 1), (3, "F#5", 1), (4, "F#5", 2), (6, "E5", 1), (7, "D5", 1),
             (8, "B4", 1), (9, "D5", 1), (10, "E5", 1), (11, "A5", 1), (12, "F#5", 4)]
    for bt, nm, bts in motif:
        tt = 0.8 + bt * beat
        if tt < d:
            B.add(A.musicbox(midi_hz(n(nm)), 3.0, 0.6), humanize(rng, tt, 0.006), 0.45, 0.2)
    return B.b, -28


def cue_porch2(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(9)
    mel = [(1, 0, "E5", 2), (1, 2, "C#5", 2), (2, 0, "D5", 2), (2, 2, "F#5", 2), (3, 0, "D5", 4)]
    piano_bed(B, d, PORCH2, rng, vel=0.5, melody=mel, padgain=0.32)
    return B.b, -28


def cue_ending(d, ctx):
    B = Buf(d)
    rng = np.random.default_rng(10)
    prog = [("G1", ["G2", "D3", "G3", "B3", "D4"]), ("A1", ["A2", "E3", "A3", "C#4", "E4"]),
            ("F#1", ["F#2", "C#3", "F#3", "A3", "C#4"]), ("B1", ["B2", "F#3", "B3", "D4", "F#4"]),
            ("G1", ["G2", "D3", "G3", "B3", "D4"]), ("A1", ["A2", "E3", "A3", "C#4", "E4"])]
    bpm = 64
    beat = 60 / bpm
    bar = 4 * beat
    final_t = ctx.get("final_at", d - 4.0)
    nb = max(1, int(final_t / bar))
    # stretch bars so the final D lands exactly at final_t
    bar_s = final_t / nb
    bpm_s = 240 / bar_s
    piano_bed(B, final_t, prog[:nb] if nb <= len(prog) else prog, rng, bpm=bpm_s, vel=0.5, padgain=0.35)
    beat_s = bar_s / 4
    motif = [(0, 0, "A4", 1), (0, 1, "D5", 1), (0, 2, "E5", 1), (0, 3, "F#5", 1), (1, 0, "E5", 3),
             (2, 0, "A4", 1), (2, 1, "D5", 1), (2, 2, "E5", 1), (2, 3, "F#5", 1), (3, 0, "B5", 3)]
    for bi, bt, nm, bts in motif:
        tt = (nb - 4 + bi) * bar_s + bt * beat_s if nb >= 4 else bi * bar_s + bt * beat_s
        if 0 <= tt < final_t:
            B.add(A.musicbox(midi_hz(n(nm)), 3.0, 0.55), humanize(rng, tt, 0.006), 0.4, 0.2)
    # final chord
    for k, nm in enumerate(["D2", "A2", "D3", "F#3", "A3", "D4", "F#4"]):
        B.add(A.piano(midi_hz(n(nm)), 6.0, 0.55, gate=5.0), final_t + k * 0.03, 0.42, -0.2 + 0.06 * k)
    B.add(A.pad([midi_hz(n(x)) for x in ["D3", "A3", "F#4", "A4", "D5"]], 6.0, a=0.8, r=2.5, bright=1400, seed=12), final_t, 0.45)
    B.add(A.musicbox(midi_hz(n("D6")), 4.0, 0.5), final_t + 0.4, 0.35, 0.2)
    B.add(A.musicbox(midi_hz(n("A5")), 4.0, 0.4), final_t + 0.8, 0.3, -0.2)
    return B.b, -27


CUES = {"clock": cue_clock, "burst": cue_burst, "yard": cue_yard, "bridge": cue_bridge, "flip": cue_flip,
        "yard_bright": cue_yard_bright, "porch": cue_porch, "fortress": cue_fortress, "fortress_warm": cue_fortress_warm,
        "porch2": cue_porch2, "ending": cue_ending}


def render_cues(cues, total, marks):
    nS = int((total + 3) * SR)
    out = np.zeros((nS, 2))
    seq = [c for c in cues]
    i = 0
    while i < len(seq):
        name, t0 = seq[i]
        ctx = {}
        j = i + 1
        if name == "yard":
            # yard continues through yard_fade
            while j < len(seq) and seq[j][0] == "yard_fade":
                ctx["fade_at"] = seq[j][1] - t0
                j += 1
        t1 = seq[j][1] if j < len(seq) else total
        if name in ("silence", "yard_fade"):
            i = j
            continue
        d = t1 - t0
        if name == "ending":
            ctx["final_at"] = marks.get("title_start", total - 3.6) - t0
        if name == "ending":
            d = total - t0
        clip, target_db = CUES[name](d, ctx)
        # normalize cue loudness over its main span
        span = clip[: int(d * SR)]
        r = np.sqrt((span ** 2).mean()) + 1e-9
        clip = clip * (10 ** (target_db / 20) / r)
        clip = A.reverb(clip, wet=0.22, decay=2.2, tone=4500, predelay=0.02)
        # fade tail after the cue's end (except clock: stop quick)
        tt = np.arange(len(clip)) / SR
        if name == "clock":
            g = np.clip(1 - (tt - d) / 0.08, 0, 1)
        elif name == "ending":
            g = np.ones_like(tt)
        else:
            g = np.clip(1 - (tt - d) / 1.8, 0, 1)
        clip = clip * g[:, None]
        A.place(out, clip, t0)
        i = j
    # final fade-out at very end
    tt = np.arange(nS) / SR
    out *= np.clip((total + 0.2 - tt) / 1.5, 0, 1)[:, None]
    return out
