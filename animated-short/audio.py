"""Score + sound design + final mix.

usage: python3 audio.py <workdir>
Reads <workdir>/timeline.json and <workdir>/audio/dialogue.wav,
writes <workdir>/audio/mix.wav (48 kHz stereo).
"""
import json, os, subprocess, sys

import mido
import numpy as np
import soundfile as sf

WORK = sys.argv[1]
SR = 48000
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
OUT = os.path.join(WORK, "audio")
rng = np.random.default_rng(7)

tl = json.load(open(os.path.join(WORK, "timeline.json")))
L = {l["id"]: l for l in tl["lines"] + tl["vocals"]}
MK = tl["marks"]
DUR = tl["duration"]
N = int((DUR + 1.0) * SR)


def S(i):
    return L[i]["start"]


def E(i):
    return L[i]["end"]


# ------------------------------------------------------------------ helpers
def mixs(*sigs):
    """Sum mono signals of different lengths."""
    out = np.zeros(max(len(x) for x in sigs))
    for x in sigs:
        out[:len(x)] += x
    return out


def db(x):
    return 10 ** (x / 20)


def place(buf, sig, t, gain=1.0, pan=0.0):
    """Add mono or stereo `sig` into stereo `buf` at time t."""
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], axis=1)
    s = int(t * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += sig[: e - s] * gain


def fft_filter(x, lo=None, hi=None, slope=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    if slope:  # pinkish tilt
        g *= (np.maximum(f, 20) / 1000) ** slope
    return np.fft.irfft(X * g, len(x))


def env_adsr(n, a=0.002, d=0.05, s=0.0, r=0.05):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-6), np.exp(-(t - a) / max(d, 1e-6)) * (1 - s) + s)
    tail = int(r * SR)
    if tail and n > tail:
        e[-tail:] *= np.linspace(1, 0, tail)
    return e


def reverb_ir(sec=0.9, damp=3000):
    n = int(sec * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * (6.9 / sec))
    ir = fft_filter(ir, hi=damp)
    ir[0] = 1.0
    return ir / np.sqrt(np.sum(ir ** 2))


def convolve(x, ir):
    n = len(x) + len(ir) - 1
    nf = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[:n]


# ------------------------------------------------------------------ MIDI score
class Score:
    def __init__(self, programs):
        self.programs = programs  # channel -> program
        self.notes = []
        self.cc = []

    def note(self, t, d, p, v, ch):
        self.notes.append((t, d, int(p), int(max(1, min(127, v))), ch))

    def chord(self, t, d, ps, v, ch, strum=0.0):
        for i, p in enumerate(ps):
            self.note(t + i * strum, d - i * strum, p, v, ch)

    def render(self, name, gain=0.6):
        mid = mido.MidiFile(ticks_per_beat=480)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000, time=0))  # 1 beat = 1 s
        ev = []
        for ch, prog in self.programs.items():
            ev.append((0, 0, mido.Message("program_change", channel=ch, program=prog)))
            ev.append((0, 0, mido.Message("control_change", channel=ch, control=91, value=70)))
            ev.append((0, 0, mido.Message("control_change", channel=ch, control=93, value=20)))
        for t, d, p, v, ch in self.notes:
            ev.append((int(round(t * 480)), 1, mido.Message("note_on", channel=ch, note=p, velocity=v)))
            ev.append((int(round((t + d) * 480)), 0, mido.Message("note_off", channel=ch, note=p, velocity=0)))
        ev.sort(key=lambda e: (e[0], e[1]))
        last = 0
        for tick, _, msg in ev:
            msg.time = tick - last
            last = tick
            tr.append(msg)
        mp = os.path.join(OUT, f"{name}.mid")
        wp = os.path.join(OUT, f"{name}.wav")
        mid.save(mp)
        subprocess.run(["fluidsynth", "-ni", "-q", "-g", str(gain), "-r", str(SR), "-F", wp, SF2, mp],
                       check=True, capture_output=True)
        a, sr = sf.read(wp, dtype="float32")
        assert sr == SR
        return a


def fade(a, fin=0.0, fout=0.0, total=None):
    a = a.copy()
    if total is not None:
        a = a[: int(total * SR)]
    if fin:
        n = min(len(a), int(fin * SR))
        a[:n] *= np.linspace(0, 1, n)[:, None]
    if fout:
        n = min(len(a), int(fout * SR))
        a[-n:] *= np.linspace(1, 0, n)[:, None]
    return a


# --- 1. game-night groove (Electric piano, bass, soft kit) ----------------
def groove(length):
    sc = Score({0: 4, 1: 33, 2: 11})
    bpm = 92
    b = 60 / bpm
    prog = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]  # Fmaj7 Em7 Dm7 Cmaj7
    roots = [41, 40, 38, 36]
    t, bar = 0.0, 0
    while t < length:
        ch = prog[bar % 4]
        for off, dd in [(0, 1.4), (1.5, 0.45), (2.5, 1.3)]:
            sc.chord(t + off * b, dd * b, ch, 46 + (8 if off == 0 else 0), 0, strum=0.012)
        r = roots[bar % 4]
        for off, p in [(0, r), (1.5, r), (2, r + 7), (3, r + 12), (3.5, r + 7)]:
            sc.note(t + off * b, 0.42 * b, p, 70, 1)
        for off, p in [(0.5, 76), (2.75, 79)]:  # vibraphone sparkle
            sc.note(t + off * b, 0.3 * b, p + (bar % 2) * 2, 34, 2)
        for k in range(8):  # drums
            tt = t + k * 0.5 * b
            sc.note(tt, 0.1, 42, 34 if k % 2 else 44, 9)
            if k in (0, 5):
                sc.note(tt, 0.2, 36, 72, 9)
            if k in (2, 6):
                sc.note(tt, 0.15, 37, 50, 9)
        t += 4 * b
        bar += 1
    return sc.render("m_groove", 0.55)


# --- 2. a held, uneasy string pad under the narration ----------------------
def pad_uneasy(length):
    sc = Score({0: 49, 1: 42})
    sc.chord(0, length, [50, 57, 62, 64], 38, 0)  # Dadd9-ish, unresolved
    sc.note(0, length, 38, 34, 1)
    return sc.render("m_pad", 0.55)


# --- 3. soft piano (D minor) for Marcus's story ----------------------------
def piano_soft(length):
    sc = Score({0: 0, 1: 49, 2: 42})
    bar = 60 / 62 * 4
    chords = [
        (38, [50, 57, 62, 65, 69]),  # Dm
        (34, [46, 53, 58, 62, 65]),  # Bb
        (41, [48, 53, 57, 60, 65]),  # F
        (36, [48, 55, 60, 64, 67]),  # C
    ]
    cyc = chords * 6
    cyc[12] = (43, [50, 55, 58, 62, 67])  # Gm
    t, i = 0.0, 0
    e8 = bar / 8
    melody = {4: [(0, 69, 2), (4, 67, 2)], 5: [(0, 65, 4)], 6: [(0, 64, 2), (4, 65, 2)], 7: [(0, 67, 4)],
              8: [(0, 69, 2), (4, 72, 2)], 9: [(0, 70, 4)], 10: [(0, 69, 2), (4, 65, 2)], 11: [(0, 67, 4)],
              13: [(0, 70, 2), (4, 69, 2)], 14: [(0, 72, 4)], 15: [(0, 67, 6)]}
    while t < length:
        root, ch = cyc[i % len(cyc)]
        grow = min(1.0, i / 10)
        sc.note(t, bar * 0.95, root, 44 + 8 * grow, 0)
        pat = [ch[0], ch[1], ch[2], ch[3], ch[4], ch[3], ch[2], ch[1]]
        for k, p in enumerate(pat):
            sc.note(t + k * e8, e8 * 2.2, p, 30 + 10 * grow + (6 if k == 0 else 0), 0)
        for off, p, d in melody.get(i, []):
            sc.note(t + off * e8, d * e8, p + 12, 44 + 6 * grow, 0)
        sc.chord(t, bar, ch[1:4], 26 + 14 * grow, 1)
        if i >= 4:
            sc.note(t, bar, root, 30 + 10 * grow, 2)
        t += bar
        i += 1
    return sc.render("m_soft", 0.6)


# --- 4. warmer, major (F) as they find each other --------------------------
def piano_warm(length, swell_at):
    sc = Score({0: 0, 1: 49, 2: 42, 3: 45})
    bar = 60 / 66 * 4
    chords = [
        (41, [53, 57, 60, 65, 69]),  # F
        (40, [52, 55, 60, 64, 67]),  # C/E
        (38, [50, 57, 62, 65, 69]),  # Dm
        (34, [46, 53, 58, 62, 65]),  # Bb
        (45, [48, 53, 57, 60, 65]),  # F/A
        (43, [50, 55, 58, 62, 65]),  # Gm7
        (36, [48, 55, 60, 64, 67]),  # C
        (41, [53, 57, 60, 65, 69]),  # F
    ]
    e8 = bar / 8
    mel = [[(0, 72, 3), (4, 69, 4)], [(0, 67, 6)], [(0, 69, 3), (4, 72, 4)], [(0, 70, 6)],
           [(0, 72, 3), (4, 77, 4)], [(0, 74, 3), (4, 70, 3)], [(0, 72, 6)], [(0, 69, 8)]]
    t, i = 0.0, 0
    while t < length:
        root, ch = chords[i % 8]
        near = np.exp(-((t - swell_at) / 9.0) ** 2)
        v = 40 + 14 * near
        sc.note(t, bar * 0.95, root, v + 4, 0)
        for k, p in enumerate([ch[0], ch[2], ch[3], ch[4], ch[3], ch[2], ch[1], ch[2]]):
            sc.note(t + k * e8, e8 * 2.0, p, v - 8 + (6 if k == 0 else 0), 0)
        if i >= 2:
            for off, p, d in mel[i % 8]:
                sc.note(t + off * e8, d * e8, p + 12, v, 0)
        sc.chord(t, bar, ch[1:4], 30 + 22 * near, 1)
        sc.note(t, bar, root, 34 + 18 * near, 2)
        if 2 <= i < 8:  # a little pizzicato lift during the laughter
            for k in (0, 3, 6):
                sc.note(t + k * e8, e8, ch[1] + 12, 34, 3)
        t += bar
        i += 1
    return sc.render("m_warm", 0.6)


# --- 5. morning: light, playful ---------------------------------------------
def morning(length):
    sc = Score({0: 24, 1: 45, 2: 9, 3: 0})
    bpm = 96
    b = 60 / bpm
    chords = [(48, [60, 64, 67, 72]), (47, [59, 62, 67, 71]), (45, [57, 60, 64, 69]), (41, [57, 60, 65, 69])]
    glock = [[(0, 79), (1, 76), (2, 79), (3.5, 81)], [(0, 79), (2, 74)], [(0, 76), (1, 72), (2, 76), (3, 79)], [(0, 77), (2, 72)]]
    t, bar = 0.0, 0
    while t < length:
        root, ch = chords[bar % 4]
        for k in range(8):
            p = ch[[0, 2, 1, 3, 2, 1, 3, 2][k]]
            sc.note(t + k * 0.5 * b, 0.9 * b, p, 48 + (8 if k % 4 == 0 else 0), 0)
        for off in (0, 2):
            sc.note(t + off * b, 0.4 * b, root, 60, 1)
        sc.note(t + 3 * b, 0.4 * b, root + 7, 50, 1)
        if bar % 2 == 0 or bar > 6:
            for off, p in glock[bar % 4]:
                sc.note(t + off * b, 0.6 * b, p, 40, 2)
        t += 4 * b
        bar += 1
    sc.chord(t, 4.0, [48, 55, 60, 64, 67, 72], 44, 3)  # final ring
    return sc.render("m_morning", 0.55)


# ------------------------------------------------------------------ sound design
def rain(length):
    n = int(length * SR)
    x = rng.standard_normal(n)
    x = fft_filter(x, lo=400, hi=7000, slope=-0.5)
    x /= np.abs(x).max()
    lfo = 0.85 + 0.15 * np.sin(np.arange(n) / SR * 2 * np.pi * 0.07)
    x *= lfo
    # occasional drips on the sill
    for t in rng.uniform(0, length, int(length * 2.2)):
        d = int(0.04 * SR)
        s = int(t * SR)
        if s + d < n:
            f = rng.uniform(1800, 3800)
            x[s:s + d] += 0.35 * np.sin(2 * np.pi * f * np.arange(d) / SR) * np.exp(-np.arange(d) / SR * 90)
    xs = np.stack([x, np.roll(x, 911)], axis=1)
    return xs * 0.5


def click(f=2400, dur=0.035, decay=120):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * decay)
    s += 0.5 * rng.standard_normal(n) * np.exp(-t * 600)
    return s


def thump(f=70, dur=0.25, decay=18, noise=0.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t * (1 - 0.3 * t)) * np.exp(-t * decay)
    s += noise * fft_filter(rng.standard_normal(n), hi=900) * np.exp(-t * 40)
    return s


def swish(dur=0.45, lo=300, hi=3000):
    n = int(dur * SR)
    x = fft_filter(rng.standard_normal(n), lo=lo, hi=hi)
    e = np.sin(np.pi * np.arange(n) / n) ** 2
    return x / np.abs(x).max() * e


def square(f, dur, vol=1.0, sweep=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f * (1 + sweep * t / dur)) / SR
    s = np.sign(np.sin(ph)) * 0.6 + 0.4 * np.sin(ph)
    return s * vol * env_adsr(n, 0.004, dur * 0.7, 0.3, 0.02)


def game_sfx(length, die_at):
    buf = np.zeros(int((length + 2) * SR))
    t = 0.15
    while t < die_at - 0.2:
        kind = rng.integers(0, 3)
        if kind == 0:  # pew
            s = square(rng.uniform(900, 1400), 0.12, 0.5, sweep=-0.6)
        elif kind == 1:  # coin
            s = np.concatenate([square(988, 0.06, 0.45), square(1319, 0.14, 0.45)])
        else:  # boop
            s = square(rng.uniform(300, 500), 0.08, 0.5)
        buf[int(t * SR):int(t * SR) + len(s)] += s
        t += rng.uniform(0.18, 0.45)
    # explosions on the TV flashes
    for et in (0.55, 1.5):
        n = int(0.4 * SR)
        x = fft_filter(rng.standard_normal(n), hi=1500) * np.exp(-np.arange(n) / SR * 9)
        buf[int(et * SR):int(et * SR) + n] += x * 0.6
    # game over jingle
    tt = die_at
    for f, d in [(784, 0.16), (740, 0.16), (698, 0.16), (659, 0.5)]:
        s = square(f, d, 0.55)
        buf[int(tt * SR):int(tt * SR) + len(s)] += s
        tt += d
    buf = fft_filter(buf, lo=250, hi=5000)  # it's coming out of a TV
    return buf[: int(length * SR)]


def birds(length):
    buf = np.zeros(int(length * SR))
    t = 0.6
    while t < length - 1:
        for k in range(rng.integers(2, 5)):
            d = rng.uniform(0.05, 0.12)
            n = int(d * SR)
            tt = np.arange(n) / SR
            f0 = rng.uniform(3200, 4600)
            f = f0 + rng.uniform(-900, 900) * np.sin(np.pi * tt / d)
            s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / d) ** 2
            st = int((t + k * 0.13) * SR)
            buf[st:st + n] += s * 0.5
        t += rng.uniform(1.5, 4.0)
    return buf


# ------------------------------------------------------------------ build
def main():
    mus = np.zeros((N, 2))
    sfx = np.zeros((N, 2))

    # music
    t_cut = S("T2")
    g = groove(t_cut + 0.5)
    place(mus, fade(g, fin=0.0, fout=0.06, total=t_cut), 0.0, db(-3))

    pad_t0, pad_t1 = S("N2"), MK["tv_off"] + 1.0
    place(mus, fade(pad_uneasy(pad_t1 - pad_t0 + 1), fin=3.0, fout=3.0, total=pad_t1 - pad_t0), pad_t0, db(-6))

    soft_t0, soft_t1 = MK["music_soft"], MK["music_warm"] + 1.5
    place(mus, fade(piano_soft(soft_t1 - soft_t0 + 2), fin=2.5, fout=3.0, total=soft_t1 - soft_t0), soft_t0, db(1.5))

    warm_t0, warm_t1 = MK["music_warm"], MK["s3"]
    swell = (S("T21") - warm_t0)
    place(mus, fade(piano_warm(warm_t1 - warm_t0 + 3, swell), fin=2.5, fout=2.2, total=warm_t1 - warm_t0 + 0.4), warm_t0, db(1.5))

    morn_t0 = MK["s3"]
    mlen = DUR - morn_t0 + 0.6
    place(mus, fade(morning(mlen), fin=0.4, fout=2.5, total=mlen), morn_t0, db(-1))

    # sound design
    r = rain(MK["s3"] + 0.2)
    rg = np.ones(len(r))
    tt = np.arange(len(r)) / SR
    rg *= np.where(tt < S("T2"), 0.55, 1.0)  # under the music it sits back
    rg *= np.where(tt > MK["s2"], 0.8, 1.0)
    r = r * rg[:, None]
    r[-int(0.2 * SR):] *= np.linspace(1, 0, int(0.2 * SR))[:, None]
    place(sfx, r, 0.0, db(-27))

    # clock ticks in the silence
    for k, t in enumerate(np.arange(np.ceil(S("T2") + 0.6), E("N4") + 1.0, 1.0)):
        place(sfx, click(2600 if k % 2 else 2100, 0.04, 140), t, db(-27), pan=0.35)

    gs = game_sfx(S("T1") + 1.6, S("T1") - 0.3)
    place(sfx, gs, 0.0, db(-17))

    ir = reverb_ir(0.7, 2500)
    def roomy(x):
        return mixs(x, 0.35 * convolve(x, ir))

    # controllers set down on the table
    for t in (S("N3") + 0.85, S("P2") + 0.6, MK["tv_off"] + 0.95):
        place(sfx, roomy(mixs(thump(180, 0.12, 40, 0.8), 0.6 * click(1500, 0.03, 200))), t, db(-14))
    # Priya stands, walks out, door
    place(sfx, swish(0.6, 200, 2500), E("P2") - 0.2, db(-24), pan=0.0)
    for k in range(7):
        place(sfx, roomy(thump(90, 0.16, 28, 0.3)), MK["priya_exit"] + 0.4 + k * 0.29, db(-17 - k * 0.8), pan=min(1, 0.1 + k * 0.15))
    place(sfx, roomy(thump(55, 0.5, 9, 0.6)), MK["door"], db(-10), pan=0.8)
    place(sfx, click(1800, 0.05, 80), MK["door"] + 0.06, db(-18), pan=0.8)
    # TV off
    place(sfx, click(3000, 0.03, 300), MK["tv_off"], db(-16))
    n = int(0.5 * SR)
    whine = np.sin(2 * np.pi * 9000 * np.arange(n) / SR) * np.exp(-np.arange(n) / SR * 8)
    place(sfx, whine, MK["tv_off"] + 0.01, db(-36))
    # scoot + fist bump
    place(sfx, swish(0.6, 150, 1800), MK["fistbump"] - 0.1, db(-24))
    place(sfx, thump(120, 0.12, 45, 0.5), MK["fistbump"] + 0.86, db(-15))
    # morning: footsteps in, sit down, birds
    for k in range(6):
        place(sfx, roomy(thump(95, 0.15, 30, 0.3)), MK["s3"] + 0.45 + k * 0.3, db(-18 - (5 - k) * 0.6), pan=max(0.0, 0.9 - k * 0.16))
    place(sfx, swish(0.5, 150, 2000), MK["s3"] + 2.25, db(-25))
    b = birds(DUR - MK["s3"])
    place(sfx, b, MK["s3"], db(-31), pan=-0.6)
    # faint room tone so the morning isn't digitally dead
    rt = fft_filter(rng.standard_normal(int((DUR - MK["s3"] + 1) * SR)), lo=80, hi=600)
    place(sfx, rt / np.abs(rt).max(), MK["s3"], db(-48))

    # dialogue + ducking
    dia, sr = sf.read(os.path.join(OUT, "dialogue.wav"), dtype="float32")
    assert sr == SR
    dia = dia[:N] if len(dia) >= N else np.pad(dia, (0, N - len(dia)))
    env = np.abs(dia)
    k = int(0.03 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    talking = (env > 0.01).astype(float)
    # attack ~80 ms, release ~600 ms
    sm = np.zeros_like(talking)
    a_up, a_dn = 1 - np.exp(-1 / (0.08 * SR)), 1 - np.exp(-1 / (0.6 * SR))
    hop = 48
    cur = 0.0
    for i in range(0, N, hop):
        tgt = talking[i]
        cur += (tgt - cur) * (1 - (1 - (a_up if tgt > cur else a_dn)) ** hop)
        sm[i:i + hop] = cur
    duck = db(-7) ** sm
    mus *= duck[:, None]

    mix = mus * db(0) + sfx + np.stack([dia, dia], axis=1) * db(-1)
    peak = np.abs(mix).max()
    mix *= 0.89 / peak
    sf.write(os.path.join(OUT, "mix_raw.wav"), mix.astype(np.float32), SR)
    if os.environ.get("STEMS"):
        sf.write(os.path.join(OUT, "stem_mus.wav"), (mus * 0.89 / peak).astype(np.float32), SR)
        sf.write(os.path.join(OUT, "stem_sfx.wav"), (sfx * 0.89 / peak).astype(np.float32), SR)
    print("mixed", round(len(mix) / SR, 2), "s, pre-norm peak", round(float(peak), 3))


if __name__ == "__main__":
    main()
