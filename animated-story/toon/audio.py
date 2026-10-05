"""Voices (Kokoro TTS), procedurally synthesised music and sound effects, and the mixer."""
import hashlib
import json
import os
import re
import subprocess
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get("TOON_CACHE", os.path.join(HERE, ".cache"))
MODEL_DIR = os.environ.get("KOKORO_DIR", os.path.join(CACHE, "models"))

# ------------------------------------------------------------------------------------------
# Voice casting: voice id, speed, pitch factor (rubberband), gain
# ------------------------------------------------------------------------------------------
VOICES = {
    "narrator": dict(voice="bm_george", speed=1.06, pitch=1.0, gain=1.0),
    "cartman": dict(voice="am_puck", speed=1.08, pitch=1.38, gain=1.0),
    "pc": dict(voice="am_fenrir", speed=1.05, pitch=0.97, gain=1.0),
    "chad": dict(voice="am_michael", speed=1.0, pitch=1.03, gain=1.0),
    "broA": dict(voice="am_onyx", speed=0.95, pitch=0.9, gain=1.0),
    "broB": dict(voice="am_eric", speed=0.95, pitch=0.88, gain=1.0),
    "friend1": dict(voice="af_bella", speed=1.05, pitch=1.22, gain=0.95),
    "friend2": dict(voice="am_echo", speed=1.05, pitch=1.32, gain=0.95),
    "heckler": dict(voice="am_liam", speed=1.08, pitch=1.3, gain=1.0),
    "hecklerpal": dict(voice="am_eric", speed=1.05, pitch=1.35, gain=0.9),
    "kid1": dict(voice="af_sky", speed=1.05, pitch=1.25, gain=0.9),
    "kid2": dict(voice="am_echo", speed=1.05, pitch=1.4, gain=0.9),
    "kid3": dict(voice="af_nicole", speed=1.05, pitch=1.2, gain=0.9),
    "kid4": dict(voice="am_liam", speed=1.05, pitch=1.4, gain=0.9),
}

_kokoro = None


def _kok():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))
    return _kokoro


def _ff(x, sr_in, filters, sr_out=SR):
    """Run a mono float32 array through an ffmpeg filter chain."""
    cmd = ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr_in), "-ac", "1", "-i", "pipe:0",
           "-af", filters + f",aresample={sr_out}", "-f", "f32le", "-ar", str(sr_out), "-ac", "1", "pipe:1"]
    out = subprocess.run(cmd, input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def _tts_raw(voice, text, speed):
    samples, sr = _kok().create(text, voice=voice, speed=speed, lang="en-us")
    return np.asarray(samples, dtype=np.float32), sr


def trim(x, thresh=0.01, pad=0.03):
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(pad * SR))
    return x[a:b]


def tts(who, text, fx=None, speed=None, pitch=None):
    """Synthesize a line for character `who`. Supports [bleep] markers. Returns 48k mono array."""
    cfg = dict(VOICES[who])
    if speed:
        cfg["speed"] *= speed
    if pitch:
        cfg["pitch"] *= pitch
    key = hashlib.sha1(json.dumps([cfg, text, fx], sort_keys=True).encode()).hexdigest()[:16]
    os.makedirs(os.path.join(CACHE, "tts"), exist_ok=True)
    path = os.path.join(CACHE, "tts", f"{who}_{key}.wav")
    if os.path.exists(path):
        x, _ = sf.read(path, dtype="float32")
        return x
    parts = re.split(r"\[bleep(?::([0-9.]+))?\]", text)
    chunks = []
    i = 0
    while i < len(parts):
        seg = parts[i].strip()
        if seg:
            raw, sr = _tts_raw(cfg["voice"], seg, cfg["speed"])
            filt = "anull"
            if abs(cfg["pitch"] - 1.0) > 1e-3:
                filt = f"rubberband=pitch={cfg['pitch']:.3f}"
            chunks.append(trim(_ff(raw, sr, filt)))
        if i + 1 < len(parts):
            bl = float(parts[i + 1]) if parts[i + 1] else 0.45
            chunks.append(bleep(bl))
        i += 2
    gap = np.zeros(int(0.06 * SR), np.float32)
    out = []
    for k, ch in enumerate(chunks):
        if k:
            out.append(gap)
        out.append(ch)
    x = np.concatenate(out) if out else np.zeros(SR // 4, np.float32)
    x = normalize(x, 0.85) * cfg["gain"]
    if fx == "thought":
        x = x * 0.85
        x = x + 0.32 * reverb(x, 0.9, 0.25)[: len(x)]
        x = np.concatenate([x, 0.32 * reverb(x, 0.9, 0.25)[len(x):len(x) + int(0.3 * SR)]])
    elif fx == "whisper":
        x = _ff(x, SR, "highpass=f=300,lowpass=f=5000,volume=0.55")
    elif fx == "shout":
        x = np.tanh(x * 1.6) * 0.95
    elif fx == "radio":
        x = _ff(x, SR, "highpass=f=500,lowpass=f=3000")
    sf.write(path, x, SR)
    return x


def normalize(x, peak=0.9):
    m = np.max(np.abs(x)) if len(x) else 0
    return x if m < 1e-6 else x * (peak / m)


# ------------------------------------------------------------------------------------------
# Synth helpers
# ------------------------------------------------------------------------------------------
RNG = np.random.default_rng(7)


def T(d):
    return np.arange(int(d * SR)) / SR


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.1):
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    s_n = max(0, n - a_n - d_n - r_n)
    e = np.concatenate([np.linspace(0, 1, a_n, endpoint=False), np.linspace(1, s, d_n, endpoint=False),
                        np.full(s_n, s), np.linspace(s, 0, r_n)])
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def expdecay(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def saw(f, t):
    return 2 * ((f * t) % 1.0) - 1


def sq(f, t, duty=0.5):
    return np.where((f * t) % 1.0 < duty, 1.0, -1.0)


def tri(f, t):
    return 2 * np.abs(saw(f, t)) - 1


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), "high")
    return signal.lfilter(b, a, x)


def bp(x, f0, f1, order=2):
    b, a = signal.butter(order, [f0 / (SR / 2), min(f1 / (SR / 2), 0.99)], "band")
    return signal.lfilter(b, a, x)


def noise(n):
    return RNG.standard_normal(n)


_IR = {}


def reverb(x, size=1.2, wet=0.3):
    key = round(size, 2)
    if key not in _IR:
        n = int(size * SR)
        ir = noise(n) * np.exp(-np.arange(n) / (size * 0.22 * SR))
        ir = lp(ir, 6000)
        ir[0] = 0
        _IR[key] = ir / np.sqrt(np.sum(ir ** 2)) * 0.5
    y = signal.fftconvolve(x, _IR[key])
    return y * wet / 0.3


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, x, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]
        i = 0
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * gain


def ks_pluck(f, dur, bright=0.5, decay=0.996):
    """Karplus-Strong plucked string."""
    n = int(dur * SR)
    p = max(2, int(SR / f))
    buf = RNG.uniform(-1, 1, p)
    buf = lp(buf, 1000 + bright * 8000)
    out = np.zeros(n)
    idx = 0
    b = buf.copy()
    # vectorised in blocks of period length
    pos = 0
    while pos < n:
        m = min(p, n - pos)
        out[pos:pos + m] = b[:m]
        nb = decay * 0.5 * (b + np.roll(b, -1))
        b = nb
        pos += m
    return out * expdecay(n, dur * 0.5)


def epiano(f, dur, vel=0.6):
    t = T(dur)
    e = expdecay(len(t), 0.6)
    x = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * expdecay(len(t), 0.25)
         + 0.12 * np.sin(2 * np.pi * 3 * f * t) * expdecay(len(t), 0.12))
    return x * e * vel * env_adsr(len(t), 0.004, 0.05, 1.0, 0.08)


def kick(dur=0.3):
    t = T(dur)
    f = 45 + 110 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * expdecay(len(t), 0.09) * 0.9


def snare(dur=0.2):
    t = T(dur)
    n = bp(noise(len(t)), 1200, 8000) * expdecay(len(t), 0.05)
    tone = np.sin(2 * np.pi * 190 * t) * expdecay(len(t), 0.04)
    return (n * 0.6 + tone * 0.5)


def hat(dur=0.05, open_=False):
    n = int((0.25 if open_ else dur) * SR)
    return hp(noise(n), 7000) * expdecay(n, 0.08 if open_ else 0.012) * 0.35


def crash(dur=2.0):
    n = int(dur * SR)
    return hp(noise(n), 4000) * expdecay(n, 0.5) * 0.5


# ------------------------------------------------------------------------------------------
# Music cues
# ------------------------------------------------------------------------------------------
def _chord_notes(root, kind="maj"):
    return [root, root + (4 if kind == "maj" else 3), root + 7]


def music_assembly(dur):
    bpm = 118
    beat = 60 / bpm
    bar = beat * 4
    prog = [(60, "maj"), (67, "maj"), (69, "min"), (65, "maj")]  # C G Am F
    mel = [[72, 74, 76, 79, 76, 74, 72, None], [74, 76, 79, 81, 79, None, 74, 76],
           [76, 74, 72, 69, 72, 74, 76, None], [77, 76, 74, 72, 74, None, 72, None]]
    n = int(dur * SR) + SR
    buf = np.zeros(n)
    nbars = int(dur / bar) + 2
    for b in range(nbars):
        t0 = b * bar
        root, kind = prog[b % 4]
        notes = _chord_notes(root, kind)
        for k in range(4):
            tb = t0 + k * beat
            if k in (0, 2):
                place(buf, kick(), tb, 0.8)
            if k in (1, 3):
                place(buf, snare(), tb, 0.45)
            for h in (0, 0.5):
                place(buf, hat(), tb + h * beat, 0.5 if h else 0.3)
        # bass eighths
        for e in range(8):
            f = mtof(root - 24 + (12 if e % 4 == 3 else 0))
            tt = T(beat / 2 * 0.9)
            x = lp(saw(f, tt), 700) * env_adsr(len(tt), 0.005, 0.08, 0.6, 0.05)
            place(buf, x, t0 + e * beat / 2, 0.28)
        # chord stabs on off-beats
        for k in range(4):
            tt = T(beat * 0.35)
            x = sum(saw(mtof(m) * d, tt) for m in notes for d in (0.997, 1.003))
            x = lp(x, 2200) * env_adsr(len(tt), 0.005, 0.1, 0.4, 0.06)
            place(buf, x, t0 + k * beat + beat / 2, 0.05)
        # lead (second half of each 8-bar phrase)
        if (b // 4) % 2 == 1 or b >= 8:
            line_ = mel[b % 4]
            for e, m in enumerate(line_):
                if m is None:
                    continue
                tt = T(beat / 2 * 0.95)
                x = lp(sq(mtof(m), tt, 0.3), 3500) * env_adsr(len(tt), 0.01, 0.08, 0.7, 0.05)
                place(buf, x, t0 + e * beat / 2, 0.07)
    buf = buf + 0.15 * reverb(buf, 1.0)[: len(buf)]
    return buf[: int(dur * SR)]


def music_comedy(dur):
    """Bouncy sitcom pizzicato with a whistled melody (F major)."""
    bpm = 132
    beat = 60 / bpm
    bar = beat * 4
    prog = [65, 60, 62, 58]  # F C Dm Bb
    kinds = ["maj", "maj", "min", "maj"]
    mel = [[77, None, 81, 79, 77, None, 72, None], [76, None, 79, 77, 76, 74, 72, None],
           [74, 77, 81, None, 79, 77, 74, None], [70, 72, 74, 77, 76, None, None, None]]
    n = int(dur * SR) + SR
    buf = np.zeros(n)
    nbars = int(dur / bar) + 2
    for b in range(nbars):
        t0 = b * bar
        root = prog[b % 4]
        notes = _chord_notes(root, kinds[b % 4])
        for k in range(4):
            tb = t0 + k * beat
            if k % 2 == 0:
                place(buf, ks_pluck(mtof(root - 24 + (7 if k == 2 else 0)), 0.4, 0.3), tb, 0.55)
            else:
                for m in notes:
                    place(buf, ks_pluck(mtof(m - 12), 0.25, 0.6), tb, 0.18)
            place(buf, hat(0.03), tb + beat / 2, 0.25)
        if b % 8 >= 2:
            for e, m in enumerate(mel[b % 4]):
                if m is None:
                    continue
                tt = T(beat / 2 * 0.9)
                vib = 1 + 0.008 * np.sin(2 * np.pi * 6 * tt)
                ph = 2 * np.pi * np.cumsum(mtof(m) * vib) / SR
                x = np.sin(ph) * env_adsr(len(tt), 0.03, 0.05, 0.8, 0.06)
                x += 0.02 * hp(noise(len(tt)), 3000) * env_adsr(len(tt), 0.03, 0.05, 0.8, 0.06)
                place(buf, x, t0 + e * beat / 2, 0.12)
    buf = buf + 0.12 * reverb(buf, 0.8)[: len(buf)]
    return buf[: int(dur * SR)]


def music_warm(dur):
    bpm = 72
    beat = 60 / bpm
    bar = beat * 4
    prog = [(65, "maj"), (60, "maj"), (62, "min"), (58, "maj")]
    n = int(dur * SR) + 2 * SR
    buf = np.zeros(n)
    nbars = int(dur / bar) + 2
    for b in range(nbars):
        t0 = b * bar
        root, kind = prog[b % 4]
        notes = _chord_notes(root, kind)
        tt = T(bar * 1.1)
        pad = sum(np.sin(2 * np.pi * mtof(m) * d * tt) for m in notes for d in (0.998, 1.002))
        pad += 0.5 * np.sin(2 * np.pi * mtof(root - 12) * tt)
        pad *= env_adsr(len(tt), 0.6, 0.2, 0.8, 0.6)
        place(buf, pad, t0, 0.05)
        arp = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 12]
        for e in range(8):
            place(buf, epiano(mtof(arp[e % 4]), 1.2, 0.5), t0 + e * beat / 2, 0.11)
    buf = buf + 0.35 * reverb(buf, 1.8)[: len(buf)]
    return buf[: int(dur * SR)]


def music_sad(dur):
    bpm = 62
    beat = 60 / bpm
    bar = beat * 4
    prog = [(57, "min"), (53, "maj"), (60, "maj"), (55, "maj")]  # Am F C G
    n = int(dur * SR) + 2 * SR
    buf = np.zeros(n)
    nbars = int(dur / bar) + 2
    for b in range(nbars):
        t0 = b * bar
        root, kind = prog[b % 4]
        notes = _chord_notes(root, kind)
        place(buf, epiano(mtof(root - 12), 3.0, 0.5), t0, 0.2)
        for e, m in enumerate([notes[0], notes[2], notes[1] + 12, notes[2]]):
            place(buf, epiano(mtof(m), 2.0, 0.45), t0 + e * beat, 0.13)
    buf = buf + 0.45 * reverb(buf, 2.2)[: len(buf)]
    return buf[: int(dur * SR)]


def music_tension(dur):
    t = T(dur + 0.5)
    drone = sum(saw(mtof(33) * d, t) for d in (0.995, 1.0, 1.006))
    drone = lp(drone, 260) * 0.35
    trem = lp(saw(mtof(68), t) + saw(mtof(69), t), 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t)) * 0.04
    buf = drone + trem
    beat = 0.85
    k = 0
    while k * beat < dur:
        place(buf, kick(0.25) * 0.7, k * beat)
        place(buf, kick(0.2) * 0.45, k * beat + 0.22)
        k += 1
    buf *= np.minimum(1, t / 1.5)
    return buf[: int(dur * SR)]


def music_triumph(dur):
    a = music_assembly(dur)
    w = music_warm(dur)
    return a * 0.8 + w * 0.6


MUSIC = {
    "assembly": music_assembly,
    "comedy": music_comedy,
    "warm": music_warm,
    "sad": music_sad,
    "tension": music_tension,
    "triumph": music_triumph,
}


# ------------------------------------------------------------------------------------------
# Sound effects
# ------------------------------------------------------------------------------------------
def bleep(d=0.45):
    t = T(d)
    return 0.45 * np.sin(2 * np.pi * 1000 * t) * env_adsr(len(t), 0.005, 0.01, 1.0, 0.01)


def sfx_scratch():
    t = T(0.55)
    f = 900 * np.exp(-t * 5) + 120
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sign(np.sin(ph)) * 0.3 + bp(noise(len(t)), 600, 4000) * 0.9
    x *= env_adsr(len(t), 0.005, 0.1, 0.6, 0.3)
    # second short scratch
    t2 = T(0.2)
    f2 = 300 + 1500 * t2 / 0.2
    ph2 = 2 * np.pi * np.cumsum(f2) / SR
    y = (np.sign(np.sin(ph2)) * 0.25 + bp(noise(len(t2)), 800, 5000)) * env_adsr(len(t2), 0.005, 0.05, 0.7, 0.1)
    return np.concatenate([y, x]) * 0.8


def sfx_tick(hi=True):
    n = int(0.05 * SR)
    x = bp(noise(n), 2500 if hi else 1800, 6000) * expdecay(n, 0.004)
    return x * 0.9


def sfx_cough():
    out = []
    for k in range(2):
        n = int(0.22 * SR)
        x = bp(noise(n), 250, 2500) * env_adsr(n, 0.008, 0.06, 0.3, 0.12)
        x += 0.3 * np.sin(2 * np.pi * 160 * T(0.22)[:n]) * env_adsr(n, 0.008, 0.06, 0.2, 0.1)
        out.append(x)
        out.append(np.zeros(int(0.12 * SR)))
    y = np.concatenate(out) * 0.8
    return y + 0.4 * reverb(y, 1.4)[: len(y)]


def sfx_thud():
    t = T(0.45)
    f = 40 + 80 * np.exp(-t * 25)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(len(t), 0.12)
    x += lp(noise(len(t)), 900) * expdecay(len(t), 0.03) * 0.5
    return x * 0.95


def sfx_whoosh(d=0.5):
    n = int(d * SR)
    x = noise(n)
    out = np.zeros(n)
    seg = n // 8
    for k in range(8):
        f0 = 300 + 2400 * np.sin(np.pi * k / 8)
        sl = slice(k * seg, (k + 1) * seg)
        out[sl] = bp(x[sl], f0, f0 * 2)
    return out * np.sin(np.pi * np.arange(n) / n) * 0.6


def sfx_squeal(d=1.6):
    t = T(d)
    f = 1100 + 280 * np.sin(2 * np.pi * 7 * t) + 300 * np.sin(2 * np.pi * 0.9 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)
    x += 0.15 * bp(noise(len(t)), 1500, 4500)
    x *= env_adsr(len(t), 0.03, 0.1, 0.9, 0.2) * (0.75 + 0.25 * np.sin(2 * np.pi * 11 * t))
    return np.tanh(x * 1.2) * 0.38


def sfx_creak(d=1.3):
    t = T(d)
    f = 180 + 120 * np.sin(2 * np.pi * 0.6 * t) + 25 * noise(len(t)).cumsum() / np.sqrt(len(t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    pulses = (np.sin(ph) > 0.96).astype(float)
    x = bp(pulses, 300, 3000) * env_adsr(len(t), 0.1, 0.2, 0.8, 0.3)
    return normalize(x, 0.45)


def sfx_crickets(d=3.0):
    buf = np.zeros(int(d * SR))
    k = 0.0
    while k < d - 0.3:
        for j in range(3):
            tt = T(0.035)
            x = np.sin(2 * np.pi * 4600 * tt) * np.sin(np.pi * np.arange(len(tt)) / len(tt))
            place(buf, x, k + j * 0.06, 0.12)
        k += 0.55 + RNG.uniform(-0.05, 0.1)
    return buf


def sfx_sparkle():
    buf = np.zeros(int(1.4 * SR))
    for i, m in enumerate([84, 88, 91, 96, 100]):
        tt = T(0.9)
        x = np.sin(2 * np.pi * mtof(m) * tt) * expdecay(len(tt), 0.25)
        place(buf, x, i * 0.07, 0.18)
    return buf + 0.3 * reverb(buf, 1.2)[: len(buf)]


def sfx_gulp():
    t = T(0.25)
    f = 500 * np.exp(-t * 9) + 120
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_adsr(len(t), 0.01, 0.05, 0.6, 0.1)
    return x * 0.55


def sfx_drumroll(d=2.4):
    buf = np.zeros(int((d + 2.0) * SR))
    k = 0.0
    while k < d:
        amp = 0.15 + 0.6 * (k / d) ** 1.5
        place(buf, snare(0.08), k, amp)
        k += 0.045
    place(buf, crash(1.8), d, 0.9)
    place(buf, kick(), d, 0.9)
    return buf


def sfx_applause(d=3.0, density=40):
    buf = np.zeros(int(d * SR))
    nclaps = int(d * density)
    for _ in range(nclaps):
        tt = RNG.uniform(0, d - 0.05)
        n = int(0.02 * SR)
        x = bp(noise(n), RNG.uniform(800, 1500), 5000) * expdecay(n, 0.004)
        place(buf, x, tt, RNG.uniform(0.2, 0.6))
    e = np.minimum(1, T(d) / 0.3) * np.minimum(1, (d - T(d)) / 0.8)
    buf = buf * e
    return buf + 0.3 * reverb(buf, 1.4)[: len(buf)]


def sfx_pop():
    t = T(0.12)
    f = 400 + 1200 * t / 0.12
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(len(t), 0.03) * 0.5


def sfx_boing():
    t = T(0.6)
    f = 220 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(len(t), 0.2) * 0.5


def sfx_crash():
    return crash(2.2) * 1.2 + np.pad(kick(), (0, int(2.2 * SR) - len(kick())))


def sfx_sting():
    """Title sting: drum fill + bright chord stab."""
    buf = np.zeros(int(2.4 * SR))
    for i in range(4):
        place(buf, snare(0.12), i * 0.09, 0.3 + i * 0.12)
    tt = T(1.6)
    notes = [60, 64, 67, 72, 76]
    x = sum(saw(mtof(m) * d, tt) for m in notes for d in (0.996, 1.004))
    fc = 600 + 5000 * np.exp(-tt * 3)
    x = lp(x, 3000) * env_adsr(len(tt), 0.01, 0.3, 0.5, 0.6)
    place(buf, x, 0.36, 0.09)
    place(buf, crash(1.8), 0.36, 0.8)
    place(buf, kick(), 0.36, 0.9)
    return buf + 0.2 * reverb(buf, 1.2)[: len(buf)]


def sfx_badum():
    buf = np.zeros(int(1.6 * SR))
    place(buf, snare(0.12), 0.0, 0.6)
    place(buf, kick(), 0.18, 0.8)
    place(buf, crash(1.2) * 0.6, 0.36, 0.8)
    place(buf, hat(0.2, True), 0.36, 0.8)
    return buf


def sfx_heartbeat():
    buf = np.zeros(int(1.0 * SR))
    place(buf, lp(kick(0.25), 200), 0.0, 1.2)
    place(buf, lp(kick(0.2), 200), 0.22, 0.8)
    return buf


def sfx_gasp_crowd(n_voices=10):
    buf = np.zeros(int(1.2 * SR))
    for _ in range(n_voices):
        d = RNG.uniform(0.25, 0.4)
        nn = int(d * SR)
        f0 = RNG.uniform(900, 1600)
        x = bp(noise(nn), f0, f0 * 2.5) * env_adsr(nn, d * 0.6, 0.05, 0.5, d * 0.3)
        place(buf, x, RNG.uniform(0, 0.15), 0.25)
    return buf + 0.4 * reverb(buf, 1.4)[: len(buf)]


def sfx_choir(d=2.6):
    """Ominous 'sacrifice' choir: stacked vowel-ish formant pads."""
    t = T(d)
    out = np.zeros(len(t))
    for m in (45, 52, 57, 60, 64):
        f = mtof(m) * (1 + 0.004 * np.sin(2 * np.pi * 5 * t + m))
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = saw(1, ph / (2 * np.pi))
        x = bp(x, 600, 1300) + 0.6 * bp(x, 2300, 3200)
        out += x
    out *= env_adsr(len(t), 0.35, 0.2, 0.9, 0.6)
    out = normalize(out, 0.35)
    return out + 0.4 * reverb(out, 2.0)[: len(out)]


SFX = {
    "scratch": sfx_scratch, "tick": lambda: sfx_tick(True), "tock": lambda: sfx_tick(False),
    "cough": sfx_cough, "thud": sfx_thud, "whoosh": sfx_whoosh, "squeal": sfx_squeal,
    "creak": sfx_creak, "crickets": sfx_crickets, "sparkle": sfx_sparkle, "gulp": sfx_gulp,
    "drumroll": sfx_drumroll, "applause": sfx_applause, "pop": sfx_pop, "boing": sfx_boing,
    "crash": sfx_crash, "sting": sfx_sting, "badum": sfx_badum, "heartbeat": sfx_heartbeat,
    "gasp": sfx_gasp_crowd, "choir": sfx_choir,
    "applause_big": lambda: sfx_applause(4.5, 70),
    "squeal_long": lambda: sfx_squeal(2.6),
}

# Crowd beds made from many layered TTS voices
CROWD_VOICES = ["af_bella", "af_sky", "af_nicole", "am_puck", "am_echo", "am_liam", "af_jessica",
                "af_river", "am_eric", "af_kore", "af_sarah", "am_michael"]


def crowd_bed(kind, d=3.0, layers=12, seed=3):
    key = f"crowd_{kind}_{d}_{layers}_{seed}"
    path = os.path.join(CACHE, "tts", key + ".wav")
    if os.path.exists(path):
        x, _ = sf.read(path, dtype="float32")
        return x
    rng = np.random.default_rng(seed)
    texts = {
        "laugh": ["Hahahahaha!", "Ha ha ha ha!", "Hahaha, oh my god!", "Hehehehe!", "Ahahahaha!",
                  "Ha! Ha ha ha!", "Hahahaha, stop!", "Bahahaha!"],
        "ooh": ["Ooooooooh!", "Oooooh!", "Ooooh, dude!"],
        "murmur": ["What?", "What is he doing?", "Dude.", "Why is he screaming?", "What the heck?",
                   "Is he okay?", "Oh my god.", "Bro, what?", "Why is he squealing?", "Huh?"],
        "aww": ["Awwwwww!", "Awww.", "Aww, man."],
        "groan": ["Uggghhh.", "Ohhh no.", "Ugh.", "Oof."],
        "cheer": ["Yeaaaah!", "Woooo!", "Let's go!", "Yeah!", "Woohoo!"],
    }[kind]
    buf = np.zeros(int((d + 1.5) * SR))
    for i in range(layers):
        v = CROWD_VOICES[i % len(CROWD_VOICES)]
        txt = texts[rng.integers(len(texts))]
        raw, sr = _tts_raw(v, txt, float(rng.uniform(0.95, 1.2)))
        p = float(rng.uniform(1.15, 1.45))
        x = trim(_ff(raw, sr, f"rubberband=pitch={p:.3f}"))
        x = normalize(x, 0.5)
        if kind == "murmur":
            x = _ff(x, SR, "lowpass=f=3200") * 0.6
        off = float(rng.uniform(0, max(0.1, d - len(x) / SR))) if kind != "laugh" else float(rng.uniform(0, 0.5))
        place(buf, x, off, float(rng.uniform(0.35, 0.8)))
        if kind == "laugh" and d > 2.5:
            place(buf, x, off + len(x) / SR + float(rng.uniform(0.0, 0.4)), float(rng.uniform(0.2, 0.45)))
    buf = buf + 0.5 * reverb(buf, 1.4)[: len(buf)]
    buf = normalize(buf, 0.8)
    n = int(d * SR)
    fade = np.ones(len(buf))
    fl = int(0.6 * SR)
    if len(buf) > n:
        fade[n:] = 0
        fade[max(0, n - fl):n] = np.linspace(1, 0, min(fl, n))
    buf = buf * fade
    sf.write(path, buf[: n + 1].astype(np.float32), SR)
    return buf[: n + 1]


CROWD = {"laugh", "ooh", "murmur", "aww", "groan", "cheer"}


def get_sfx(name, d=None):
    x = _get_sfx(name, d)
    pk = np.max(np.abs(x)) if len(x) else 0
    return x * (0.95 / pk) if pk > 0.95 else x


def _get_sfx(name, d=None):
    if name.startswith("crowd_"):
        kind = name[6:]
        return crowd_bed(kind, d or 3.0, layers=14 if kind == "laugh" else 10)
    if name == "crickets":
        return sfx_crickets(d or 3.0)
    if name == "silence":
        return np.zeros(int((d or 1) * SR))
    return SFX[name]()


# ------------------------------------------------------------------------------------------
# Mixer
# ------------------------------------------------------------------------------------------
def mix(total, dialogue, sfx, music, out_path):
    """dialogue/sfx: list of (t, array, gain). music: list of (t0, t1, cue, gain, fade_in, fade_out)."""
    n = int(total * SR) + SR
    dia = np.zeros(n)
    for t, x, g in dialogue:
        place(dia, x, t, g)
    fx = np.zeros(n)
    for t, x, g in sfx:
        place(fx, x, t, g)
    mus = np.zeros(n)
    cache = {}
    for t0, t1, cue, g, fi, fo in music:
        d = t1 - t0
        if d <= 0:
            continue
        if cue not in cache or len(cache[cue]) < int(d * SR):
            m = MUSIC[cue](max(d, 8.0) + 0.5)
            cache[cue] = m * (0.12 / (np.sqrt(np.mean(m ** 2)) + 1e-9))
        x = cache[cue][: int(d * SR)].copy()
        e = np.ones(len(x))
        if fi > 0:
            k = min(len(x), int(fi * SR))
            e[:k] = np.linspace(0, 1, k)
        if fo > 0:
            k = min(len(x), int(fo * SR))
            e[len(x) - k:] *= np.linspace(1, 0, k)
        place(mus, x * e, t0, g)
    # duck music under dialogue
    env = np.abs(dia)
    win = int(0.25 * SR)
    env = signal.lfilter(np.ones(win) / win, [1], env)
    env = np.convolve(env, np.ones(int(0.3 * SR)) / (0.3 * SR), mode="same")
    duck = 1 - 0.55 * np.clip(env * 12, 0, 1)
    out = dia + fx + mus * duck
    out = np.tanh(out * 0.95) * 0.98
    stereo = np.stack([out, out], axis=1).astype(np.float32)
    sf.write(out_path, stereo[: int(total * SR)], SR)
    return out_path
