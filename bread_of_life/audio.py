"""Ambience, dialogue processing and the final mix.

Layers: dialogue (per-scene reverb, per-line loudness), music (ducked under
speech), ambience (lake, wind, birds, crowd murmur, synagogue room, uproar,
crickets, footsteps, bread crackle). Master: loudness normalisation to
-16 LUFS with a peak limiter.
"""
import os

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.signal import butter, fftconvolve, resample_poly, sosfilt, sosfiltfilt

from config import SR, WORK
import script
from music import hall_ir
from timeline import Timeline

T = Timeline()
VOICE = os.path.join(WORK, "voice")
OUT = os.path.join(WORK, "audio")
os.makedirs(OUT, exist_ok=True)
N = int((T.total + 0.5) * SR)
rng = np.random.default_rng(42)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, f0, f1, order=2):
    return sosfilt(butter(order, [f0, f1], "band", fs=SR, output="sos"), x, axis=0)


def pink(n, ch=2):
    out = np.zeros((n, ch))
    for c in range(ch):
        w = rng.standard_normal(n)
        X = np.fft.rfft(w)
        f = np.arange(len(X))
        f[0] = 1
        X /= np.sqrt(f)
        y = np.fft.irfft(X, n)
        out[:, c] = y / (np.std(y) + 1e-9)
    return out


def env_curve(points, n):
    """Piecewise-linear envelope from [(t_seconds, gain)]."""
    t = np.arange(n) / SR
    pts = sorted(points)
    return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])


def db(x):
    return 10 ** (x / 20)


# --------------------------------------------------------------------------
# ambience
# --------------------------------------------------------------------------

def lake_waves(n, period=(4.0, 7.5)):
    base = lp(pink(n), 700, 2)
    fizz = bp(pink(n), 1800, 7000, 2)
    e = np.zeros(n)
    t = 0.0
    while t < n / SR:
        a = int(t * SR)
        L = int(rng.uniform(*period) * SR)
        k = np.arange(min(L, n - a)) / SR
        shape = (1 - np.exp(-k / 0.7)) * np.exp(-k / 2.4)
        e[a:a + len(shape)] += shape * rng.uniform(0.6, 1.0)
        t += rng.uniform(*period) * 0.8
    e = e / (e.max() + 1e-9)
    e2 = np.roll(e, int(0.35 * SR))
    return base * (0.35 + 0.65 * e)[:, None] * 0.5 + fizz * (e2 ** 2)[:, None] * 0.18


def wind(n):
    w = lp(pink(n), 450, 2)
    mod = lp(rng.standard_normal(n), 0.15, 1)
    mod = (mod - mod.min()) / (np.ptp(mod) + 1e-9)
    return w * (0.3 + 0.7 * mod)[:, None] * 0.35


def chirp_bird(dur=0.09, f0=4200, f1=5600):
    k = np.arange(int(dur * SR)) / SR
    f = np.linspace(f0, f1, len(k)) + 300 * np.sin(2 * np.pi * 38 * k)
    ph = 2 * np.pi * np.cumsum(f) / SR
    e = np.sin(np.pi * k / dur) ** 2
    return np.sin(ph) * e


def songbirds(n, times, gain=0.05):
    out = np.zeros((n, 2))
    for t0 in times:
        pan = rng.uniform(0.2, 0.8)
        tt = t0
        for j in range(rng.integers(3, 7)):
            c = chirp_bird(rng.uniform(0.05, 0.11), rng.uniform(3500, 4800), rng.uniform(4800, 6200))
            a = int(tt * SR)
            if a + len(c) < n:
                out[a:a + len(c), 0] += c * (1 - pan) * gain
                out[a:a + len(c), 1] += c * pan * gain
            tt += rng.uniform(0.09, 0.2)
    return lp(out, 7000)


def crickets(n, start, gain=0.03):
    out = np.zeros((n, 2))
    for k in range(5):
        f = rng.uniform(4200, 4800)
        rate = rng.uniform(14, 20)
        pan = rng.uniform(0.15, 0.85)
        t = np.arange(n) / SR
        carrier = np.sin(2 * np.pi * f * t)
        pulse = (np.sin(2 * np.pi * rate * t) > 0.6).astype(float)
        chirp_env = (np.sin(2 * np.pi * rng.uniform(0.6, 1.1) * t + rng.uniform(0, 6)) > -0.2).astype(float)
        s = carrier * lp(pulse * chirp_env, 300, 1)
        s *= np.clip((t - start) / 4.0, 0, 1)
        out[:, 0] += s * (1 - pan) * gain
        out[:, 1] += s * pan * gain
    return out


def load_line(lid):
    x, sr = sf.read(os.path.join(VOICE, lid + ".wav"))
    if sr != SR:
        x = resample_poly(x, SR // 1000 * 1, sr // 1000 * 1) if SR % sr else resample_poly(x, SR // sr, 1)
    return x


def babble(n, gain=0.05, density=3, lp_f=1400, pitch_var=0.12):
    """Unintelligible crowd murmur from the walla takes."""
    files = sorted(os.listdir(os.path.join(VOICE, "walla")))
    clips = [sf.read(os.path.join(VOICE, "walla", f))[0] for f in files]
    out = np.zeros((n, 2))
    for layer in range(density):
        t = rng.uniform(0, 1.0)
        while t * SR < n:
            c = clips[rng.integers(len(clips))]
            r = rng.uniform(1 - pitch_var, 1 + pitch_var)
            up = int(round(SR / 24000 * 100 * r))
            y = resample_poly(c, up, 100)
            a = int(t * SR)
            b = min(n, a + len(y))
            pan = rng.uniform(0.15, 0.85)
            g = rng.uniform(0.5, 1.0)
            out[a:b, 0] += y[: b - a] * (1 - pan) * g
            out[a:b, 1] += y[: b - a] * pan * g
            t += len(y) / SR + rng.uniform(0.1, 0.8)
    return lp(out, lp_f) * gain


def footsteps(n, t0, t1, gain=0.08, rate=1.9, pan=0.75):
    out = np.zeros((n, 2))
    t = t0
    while t < t1:
        L = int(0.07 * SR)
        burst = rng.standard_normal(L) * np.exp(-np.arange(L) / (0.018 * SR))
        burst = bp(burst, 900, 4500)
        a = int(t * SR)
        fade = 1 - (t - t0) / (t1 - t0)
        if a + L < n:
            out[a:a + L, 0] += burst * (1 - pan) * gain * fade
            out[a:a + L, 1] += burst * pan * gain * fade
        t += 1 / rate * rng.uniform(0.85, 1.15)
    return out


def crackle(n, t0, gain=0.25):
    out = np.zeros((n, 2))
    for k in range(26):
        t = t0 + rng.uniform(0, 0.55) ** 1.5
        L = int(rng.uniform(0.004, 0.015) * SR)
        b = rng.standard_normal(L) * np.exp(-np.arange(L) / (0.003 * SR))
        a = int(t * SR)
        if a + L < n:
            out[a:a + L] += (hp(b, 1500) * gain * rng.uniform(0.3, 1.0))[:, None]
    return out


def ambience():
    s1, s2, s3 = T.scene_end["shore"], T.scene_end["synagogue"], T.total + 0.5
    amb = np.zeros((N, 2))
    # shore morning
    shore = lake_waves(N) * db(-24) + wind(N) * db(-30)
    birds = songbirds(N, [1.0, 5.2, 9.5, 21.0, 33.0, 47.5, 62.0, 80.0, 96.0], gain=0.035)
    crowd = babble(N, gain=0.022, density=3, lp_f=1100)
    e_shore = env_curve([(0, 1.0), (s1 - 0.5, 1.0), (s1 + 1.2, 0.0), (s2, 0.0), (s2 + 1.6, 0.85), (s3, 0.85)], N)
    e_crowd = env_curve([(0, 0.0), (11.0, 0.0), (16.0, 0.9), (s1 - 0.5, 0.7), (s1 + 1.0, 0.0), (s3, 0.0)], N)
    amb += shore * e_shore[:, None]
    amb += birds * env_curve([(0, 1), (s1, 1), (s1 + 0.5, 0), (s3, 0)], N)[:, None]
    amb += crowd * e_crowd[:, None]
    # synagogue: room tone + murmur under the grumbling + the uproar
    room = lp(pink(N), 300) * db(-34)
    e_room = env_curve([(0, 0), (s1 - 0.5, 0), (s1 + 1.0, 1), (s2 - 0.3, 1), (s2 + 1.0, 0), (s3, 0)], N)
    murmur = babble(N, gain=0.05, density=4, lp_f=1600)
    e_mur = env_curve([(0, 0), (T("L15") + 2.0, 0), (T("L16") - 1.0, 0.9), (T("L18", "end") + 0.5, 0.9),
                       (T("L19") - 0.2, 0.0), (T("L24", "end") - 0.6, 0.0), (T("L24", "end") + 0.3, 1.6),
                       (T("L25") - 0.35, 1.8), (T("L25") - 0.05, 0.0), (s3, 0)], N)
    amb += room * e_room[:, None]
    syn_ir = hall_ir(SR, rt60=1.4, seed=5)
    mur = murmur * e_mur[:, None]
    mur_wet = np.stack([fftconvolve(mur[:, k], syn_ir[:, k])[:N] for k in range(2)], 1)
    amb += mur * 0.8 + mur_wet * 0.5
    # the uproar: intelligible walla takes, overlapped
    files = sorted(os.listdir(os.path.join(VOICE, "walla")))
    t = T("L24", "end") + 0.1
    up = np.zeros((N, 2))
    for k, f in enumerate(files):
        y, sr = sf.read(os.path.join(VOICE, "walla", f))
        y = resample_poly(y, 2, 1)
        a = int((t + (k % 4) * 0.55 + (k // 4) * 0.35) * SR)
        b = min(N, a + len(y))
        pan = 0.2 + 0.6 * ((k * 37) % 10) / 10
        up[a:b, 0] += y[: b - a] * (1 - pan)
        up[a:b, 1] += y[: b - a] * pan
    up *= env_curve([(0, 1), (T("L25") - 0.3, 1), (T("L25") - 0.05, 0), (s3, 0)], N)[:, None]
    up_wet = np.stack([fftconvolve(up[:, k], syn_ir[:, k])[:N] for k in range(2)], 1)
    amb += (up * 0.5 + up_wet * 0.35) * db(-3)
    # dusk: softer waves, crickets, footsteps of those who leave, bread crackle
    amb += crickets(N, s2 + 2.0, gain=0.012) * env_curve([(0, 0), (s2, 0), (s2 + 3, 1), (s3, 1)], N)[:, None]
    amb += footsteps(N, T("L33") - 0.3, T("L33", "end") + 1.0, gain=0.05)
    amb += crackle(N, T("L36", "end") + 1.85, gain=0.12)  # the loaf splits on screen at +1.88 s
    return amb


# --------------------------------------------------------------------------
# dialogue
# --------------------------------------------------------------------------
LINE_LUFS = {"NARRATOR": -21.0, "JESUS": -20.0, "PETER": -20.0, "ELI": -20.0, "MIRIAM": -21.5, "MAN2": -21.0}
LINE_ADJ = {"L12": -1.0, "L24": +1.5, "L19": +0.5, "L34": -1.5, "L17": -1.0, "L16": -1.0, "L18": -0.5, "L37": -1.0}


def dialogue():
    meter = pyln.Meter(SR)
    out = np.zeros((N, 2))
    presence = np.zeros(N)
    small_ir = hall_ir(SR, rt60=0.35, seed=7)
    room_ir = hall_ir(SR, rt60=1.3, seed=8)
    for lid in T.order:
        m = T.lines[lid]
        x, sr = sf.read(os.path.join(VOICE, lid + ".wav"))
        x = resample_poly(x, 2, 1)
        x = hp(x, 85)
        target = LINE_LUFS[m["speaker"]] + LINE_ADJ.get(lid, 0.0)
        pad = np.concatenate([x, np.zeros(SR)])
        loud = meter.integrated_loudness(pad)
        x = x * db(target - loud)
        if m["speaker"] == "NARRATOR":
            y = np.stack([x, x], 1)
        elif m["scene"] == "synagogue":
            dry = np.stack([x, x], 1)
            wet = np.stack([fftconvolve(x, room_ir[:, k]) for k in range(2)], 1)
            dry = np.pad(dry, ((0, len(wet) - len(dry)), (0, 0)))
            y = dry * 0.9 + wet * 0.22
        else:
            dry = np.stack([x, x], 1)
            wet = np.stack([fftconvolve(x, small_ir[:, k]) for k in range(2)], 1)
            dry = np.pad(dry, ((0, len(wet) - len(dry)), (0, 0)))
            y = dry * 0.95 + wet * 0.10
        a = int(m["start"] * SR)
        b = min(N, a + len(y))
        out[a:b] += y[: b - a]
        presence[a:a + len(x)] = np.maximum(presence[a:a + len(x)], 1.0)
    return out, presence


def smooth_env(x, attack, release):
    y = np.zeros_like(x)
    a = np.exp(-1 / (attack * SR))
    r = np.exp(-1 / (release * SR))
    # vectorised-ish: process in blocks of 1 ms
    hop = SR // 1000
    xs = x[::hop]
    ys = np.zeros_like(xs)
    v = 0.0
    a = np.exp(-1 / (attack * 1000))
    r = np.exp(-1 / (release * 1000))
    for i, s in enumerate(xs):
        v = a * v + (1 - a) * s if s > v else r * v + (1 - r) * s
        ys[i] = v
    return np.repeat(ys, hop)[: len(x)]


def limiter(x, ceiling_db=-1.2, look=0.004, release=0.08):
    ceil = db(ceiling_db)
    peak = np.max(np.abs(x), axis=1)
    hop = 48
    nb = len(peak) // hop + 1
    pk = np.zeros(nb)
    for i in range(nb):
        seg = peak[i * hop:(i + 1) * hop]
        pk[i] = seg.max() if len(seg) else 0
    # look-ahead: max over next few blocks
    la = max(1, int(look * SR / hop))
    pk2 = np.array([pk[i:i + la + 1].max() for i in range(nb)])
    g = np.minimum(1.0, ceil / (pk2 + 1e-9))
    rel = np.exp(-1 / (release * SR / hop))
    gs = np.zeros(nb)
    v = 1.0
    for i in range(nb):
        v = g[i] if g[i] < v else rel * v + (1 - rel) * g[i]
        gs[i] = v
    gain = np.repeat(gs, hop)[: len(x)]
    return x * gain[:, None]


def build():
    music, sr = sf.read(os.path.join(WORK, "music", "music.wav"))
    music = music[:N] if len(music) >= N else np.pad(music, ((0, N - len(music)), (0, 0)))
    dia, pres = dialogue()
    amb = ambience()
    # set music bed level from its loudness (target -27 LUFS before ducking)
    meter = pyln.Meter(SR)
    ml = meter.integrated_loudness(music)
    music = music * db(-24.0 - ml)
    duck = smooth_env(pres, 0.08, 0.7)
    music_d = music * (1 - (1 - db(-6.5)) * duck)[:, None]
    amb_d = amb * (1 - (1 - db(-3.0)) * duck)[:, None]
    mix = dia + music_d + amb_d
    loud = meter.integrated_loudness(mix)
    mix = mix * db(-16.0 - loud)
    mix = limiter(mix, -1.2)
    # the sound fades out with the picture (the last second fades to black)
    i0, i1 = int((T.total - 1.8) * SR), int(T.total * SR)
    mix[i0:i1] *= np.linspace(1.0, 0.0, i1 - i0)[:, None] ** 1.5
    mix[i1:] = 0.0
    print("integrated loudness:", round(meter.integrated_loudness(mix), 2), "peak:", round(20 * np.log10(np.max(np.abs(mix))), 2))
    sf.write(os.path.join(OUT, "mix.wav"), mix.astype(np.float32), SR)
    sf.write(os.path.join(OUT, "dialogue.wav"), dia.astype(np.float32), SR)
    sf.write(os.path.join(OUT, "music_ducked.wav"), music_d.astype(np.float32), SR)
    sf.write(os.path.join(OUT, "ambience.wav"), amb_d.astype(np.float32), SR)
    return mix


if __name__ == "__main__":
    build()
