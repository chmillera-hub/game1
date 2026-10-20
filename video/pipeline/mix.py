"""Sound design + final mix: dialogue (per-scene rooms), score (ducked), ambience beds and spot effects.

/opt/tts/bin/python mix.py  ->  /opt/work/audio/final_mix.wav (48 kHz stereo, -14 LUFS)
"""
import json, os, re, sys
import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.dirname(__file__))
from score import t_of

SR = 48000
TL = json.load(open("/opt/work/timeline.json"))
LINES = {l["id"]: l for l in TL["lines"]}
N = int(TL["duration"] * SR)
rng = np.random.default_rng(11)


# ----------------------------------------------------------------------------- dsp helpers

def db(x):
    return 10 ** (x / 20)


def bandpass(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lowpass(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)


def highpass(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def ir(rt60, predelay=0.012, bright=6000, seed=0, length=None):
    r = np.random.default_rng(seed)
    L = int((length or rt60 * 1.2) * SR)
    t = np.arange(L) / SR
    env = np.exp(-6.9 * t / rt60)
    h = np.stack([r.normal(0, 1, L) * env, r.normal(0, 1, L) * env], axis=1)
    for c in range(2):
        h[:, c] = lowpass(h[:, c], bright)
    pd = int(predelay * SR)
    h = np.concatenate([np.zeros((pd, 2)), h])
    h /= np.sqrt((h ** 2).sum(axis=0, keepdims=True))
    return h


def reverb(x, h, wet):
    out = np.zeros((len(x) + len(h) - 1, 2))
    for c in range(2):
        out[:, c] = signal.fftconvolve(x, h[:, c])
    dry = np.zeros_like(out)
    dry[:len(x), 0] = x
    dry[:len(x), 1] = x
    return dry * (1 - wet * 0.5) + out * wet


def env_follow(x, attack=0.03, release=0.35):
    a = np.abs(x)
    a = signal.sosfilt(signal.butter(1, 30, fs=SR, output="sos"), a)
    out = np.zeros_like(a)
    ka, kr = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    # vectorized-ish one-pole with different attack/release via decimation
    hop = 64
    ad = a[::hop]
    o = np.zeros_like(ad)
    ka, kr = np.exp(-hop / (attack * SR)), np.exp(-hop / (release * SR))
    for i in range(1, len(ad)):
        k = ka if ad[i] > o[i - 1] else kr
        o[i] = k * o[i - 1] + (1 - k) * ad[i]
    return np.interp(np.arange(len(a)), np.arange(len(ad)) * hop, o)


def place(track, clip, t, gain=1.0):
    i = int(t * SR)
    if i >= len(track):
        return
    clip = clip[:len(track) - i]
    if track.ndim == 2 and clip.ndim == 1:
        clip = np.stack([clip, clip], 1)
    track[i:i + len(clip)] += clip * gain


def fade(x, fi=0.01, fo=0.05):
    a, b = int(fi * SR), int(fo * SR)
    x = x.copy()
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


# ----------------------------------------------------------------------------- scene spans
def scene_spans():
    """Contiguous (scene, t0, t1) spans following the dialogue's scene field, split at shot cuts."""
    sys.path.insert(0, os.path.dirname(__file__))
    from shots import shot_bounds
    spans = []
    for shot, a, b in shot_bounds(LINES, TL["duration"]):
        sc = shot["set"]
        if spans and spans[-1][0] == sc:
            spans[-1][2] = b
        else:
            spans.append([sc, a, b])
    return spans


# ----------------------------------------------------------------------------- dialogue
ROOMS = {
    "colonnade": dict(rt=1.9, wet=0.22, pre=0.025, bright=5000),
    "street": dict(rt=1.0, wet=0.14, pre=0.015, bright=6000),
    "upper_room": dict(rt=0.55, wet=0.16, pre=0.006, bright=5000),
    "apartment": dict(rt=0.4, wet=0.08, pre=0.004, bright=7000),
    "sister": dict(rt=0.45, wet=0.1, pre=0.005, bright=7000),
    "door": dict(rt=0.8, wet=0.14, pre=0.008, bright=6000),
    "cosmos": dict(rt=2.8, wet=0.2, pre=0.03, bright=4500),
    "city": dict(rt=2.2, wet=0.16, pre=0.03, bright=4500),
}


def dialogue():
    out = np.zeros((N + SR * 4, 2))
    for l in TL["lines"]:
        y, sr = sf.read(l["wav"])
        y = highpass(y, 85)
        # gentle compression
        e = env_follow(y, 0.005, 0.12)
        g = np.where(e > 0.12, (0.12 / np.maximum(e, 1e-6)) ** 0.35, 1.0)
        y = y * g
        gain = 1.0
        room = ROOMS.get(l["scene"], ROOMS["apartment"])
        if l["speaker"] == "NARRATOR":
            room = dict(rt=0.3, wet=0.04, pre=0.002, bright=8000)
        if l["speaker"] == "JESUS" and l["scene"] in ("apartment", "cosmos", "city", "door"):
            room = dict(rt=1.6, wet=0.12, pre=0.02, bright=5500)   # prayer as voice-over
        if l["id"] == "L023":
            y = lowpass(y, 3200)
            gain = db(-1)
        h = ir(room["rt"], room["pre"], room["bright"], seed=hash(l["scene"]) % 1000)
        st = reverb(y, h, room["wet"])
        place(out, st, l["start"], gain)
    return out[:N]


# ----------------------------------------------------------------------------- generated sounds
def noise(sec, color="pink"):
    n = int(sec * SR)
    w = rng.normal(0, 1, n)
    if color == "brown":
        w = np.cumsum(w)
        w = highpass(w, 20)
    elif color == "pink":
        b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
        w = signal.lfilter(b, a, w)
    return w / (np.abs(w).max() + 1e-9)


def wind(sec, strength=1.0):
    w = bandpass(noise(sec, "brown"), 120, 1100)
    t = np.arange(len(w)) / SR
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * t + 1.3) * np.sin(2 * np.pi * 0.023 * t)
    gust = bandpass(noise(sec, "pink"), 1500, 4500) * np.clip(np.sin(2 * np.pi * 0.05 * t), 0, 1) ** 3 * 0.25
    x = (w * mod + gust) * strength
    return np.stack([x, np.roll(x, 2400)], 1) * 0.5


def crickets(sec):
    t = np.arange(int(sec * SR)) / SR
    out = np.zeros_like(t)
    for k in range(5):
        f = rng.uniform(3800, 4800)
        rate = rng.uniform(1.6, 2.6)
        ph = rng.uniform(0, 1)
        chirp_env = (np.sin(2 * np.pi * rate * t + ph * 6) > 0.6).astype(float)
        pulse = (np.sin(2 * np.pi * 30 * t) > 0).astype(float)
        out += np.sin(2 * np.pi * f * t) * chirp_env * pulse * rng.uniform(0.3, 1.0)
    out = lowpass(out, 6000)
    return np.stack([out, np.roll(out, 900)], 1) * 0.06


def room_tone(sec, hum=60.0, level=1.0):
    t = np.arange(int(sec * SR)) / SR
    h = sum(np.sin(2 * np.pi * hum * k * t) / k ** 1.5 for k in (1, 2, 3))
    x = lowpass(noise(sec, "pink"), 900) * 0.5 + h * 0.08
    return np.stack([x, x], 1) * 0.12 * level


def traffic(sec):
    x = lowpass(noise(sec, "brown"), 500)
    t = np.arange(len(x)) / SR
    swell = 0.5 + 0.5 * np.clip(np.sin(2 * np.pi * 0.06 * t) + 0.3 * np.sin(2 * np.pi * 0.13 * t + 1), -1, 1)
    x = x * swell
    return np.stack([x, np.roll(x, 3000)], 1) * 0.35


def clock_tick(sec):
    out = np.zeros(int(sec * SR))
    click = bandpass(rng.normal(0, 1, 400), 2000, 6000) * np.exp(-np.arange(400) / 60)
    for i in range(int(sec)):
        j = int(i * SR)
        out[j:j + 400] += click * (0.8 if i % 2 else 0.6)
    return np.stack([out, out], 1) * 0.12


def lamp_crackle(sec):
    out = np.zeros(int(sec * SR))
    for _ in range(int(sec * 3)):
        j = rng.integers(0, len(out) - 300)
        out[j:j + 300] += bandpass(rng.normal(0, 1, 300), 1500, 7000) * np.exp(-np.arange(300) / 40) * rng.uniform(0.2, 1)
    return np.stack([out, out], 1) * 0.05


def murmur(sec):
    path = "/opt/work/audio/murmur.wav"
    if os.path.exists(path):
        y, _ = sf.read(path)
    else:
        y = bandpass(noise(30, "pink"), 200, 1200) * 0.3
    reps = int(np.ceil(sec * SR / len(y)))
    y = np.tile(y, reps)[:int(sec * SR)]
    y = lowpass(y, 1400)
    return np.stack([y, np.roll(y, 5000)], 1)


def thud(dur=0.25, f=90, level=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t * (1 - 0.3 * t / dur)) * np.exp(-t / (dur * 0.25))
    x += lowpass(rng.normal(0, 1, n), 1200) * np.exp(-t / 0.02) * 0.6
    return x * level


def stone_crack():
    a = thud(0.5, 120, 1.0)
    n = len(a)
    t = np.arange(n) / SR
    crack = bandpass(rng.normal(0, 1, n), 1500, 7000) * np.exp(-t / 0.012) * 1.4
    ring = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.05) for f in (1830, 2710, 3390)) * 0.15
    bounce = np.zeros(n)
    j = int(0.18 * SR)
    bb = thud(0.3, 140, 0.35)[:n - j]
    bounce[j:j + len(bb)] = bb
    return a * 0.6 + crack + ring + bounce


def scrape(dur=0.45):
    n = int(dur * SR)
    t = np.arange(n) / SR
    g = bandpass(rng.normal(0, 1, n), 900, 5000) * (np.sin(np.pi * t / dur) ** 2)
    g *= 1 + 0.6 * (rng.random(n) > 0.995)
    return g * 0.6 + np.pad(thud(0.15, 160, 0.4), (int(0.3 * SR), 0))[:n]


def footsteps(t0, t1, rate=1.8, level=0.35, jitter=0.05):
    clips = []
    t = t0
    k = 0
    while t < t1:
        c = thud(0.18, 70 + rng.uniform(-10, 10), level) + bandpass(rng.normal(0, 1, int(0.18 * SR)), 2000, 6000) \
            * np.exp(-np.arange(int(0.18 * SR)) / 500) * level * 0.4
        clips.append((t + rng.uniform(-jitter, jitter), c))
        t += 1 / rate
        k += 1
    return clips


def phone_buzz(dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    on = ((t % 0.8) < 0.45).astype(float)
    x = (signal.sawtooth(2 * np.pi * 175 * t) * 0.5 + np.sin(2 * np.pi * 350 * t) * 0.3) * on
    return lowpass(x, 1200) * 0.18


def ringback(dur):
    t = np.arange(int(dur * SR)) / SR
    on = ((t % 6.0) < 2.0).astype(float)
    x = (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * on
    return bandpass(x, 300, 3400) * 0.04


def door_sounds():
    latch = bandpass(rng.normal(0, 1, 2400), 1500, 6000) * np.exp(-np.arange(2400) / 300)
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    creak_f = 300 + 200 * np.sin(2 * np.pi * 0.7 * t)
    creak = np.sin(2 * np.pi * np.cumsum(creak_f) / SR) * (signal.sawtooth(2 * np.pi * 28 * t) > 0.7)
    creak = bandpass(creak, 400, 2500) * np.sin(np.pi * t / 1.2) * 0.08
    out = np.zeros(n)
    out[:2400] += latch * 0.5
    out += creak
    return out


def rustle(dur=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return bandpass(rng.normal(0, 1, n), 800, 5000) * np.sin(np.pi * t / dur) ** 3 * 0.12


# ----------------------------------------------------------------------------- assemble
def ambience_and_fx():
    amb = np.zeros((N, 2))
    fx = np.zeros((N, 2))
    for sc, a, b in scene_spans():
        dur = b - a
        bed = None
        if sc == "colonnade":
            street = a >= t_of("L027-0.6")
            bed = wind(dur, 0.9 if not street else 0.6) * db(-26) + murmur(dur) * db(-34 if not street else -38)
        elif sc == "hillside":
            bed = wind(dur, 0.5) * db(-30)
        elif sc == "upper_room":
            bed = crickets(dur) * db(-12) + lamp_crackle(dur) * db(-6) + room_tone(dur, 50, 0.6) * db(-14)
        elif sc == "apartment":
            bed = room_tone(dur, 60) * db(-10) + traffic(dur) * db(-30)
        elif sc == "sister_kitchen":
            bed = room_tone(dur, 60, 0.8) * db(-10) + clock_tick(dur) * db(-8)
        elif sc == "hallway_door":
            bed = room_tone(dur, 120, 1.2) * db(-10)
        elif sc == "city":
            bed = traffic(dur) * db(-22) + wind(dur, 0.4) * db(-32)
        elif sc in ("scroll",):
            bed = room_tone(dur, 50, 0.4) * db(-16)
        if bed is not None:
            place(amb, fade(bed, 0.25, 0.25), a)
    # crowd stirs when the stones come up
    t13 = t_of("L013")
    place(amb, fade(murmur(6.0) * db(-30), 1.0, 2.0), t13 - 1.0)
    # spot effects
    for t, c in footsteps(t_of("L002-0.1"), t_of("L002") + 2.6, rate=2.2, level=0.25):
        place(fx, c, t, db(-14))
    place(fx, scrape(), t_of("L013:stones") - 0.1, db(-10))
    place(fx, scrape(0.35), t_of("L013:stones") + 0.5, db(-14))
    place(fx, stone_crack(), t_of("L022.e+0.45") + 0.5, db(-6))
    for t, c in footsteps(t_of("L024") + 0.4, t_of("L024") + 3.4, rate=3.0, level=0.3):
        place(fx, c, t, db(-12))
    place(fx, rustle(0.8), t_of("L024") + 0.3, db(-8))
    for t, c in footsteps(t_of("L027") - 0.9, t_of("L027") + 0.1, rate=4.0, level=0.35):
        place(fx, c, t, db(-12))
    # the call: ringback on her phone, buzz on her sister's
    place(fx, ringback(3.0), t_of("L037.e") + 0.1, db(-6))
    place(fx, phone_buzz(1.6), t_of("L040") - 1.9, db(-6))
    place(fx, door_sounds(), t_of("L050") - 0.15, db(-6))
    place(fx, rustle(1.3), t_of("L050c.e") + 0.3, db(-4))
    return amb, fx


def loudness_normalize(x, target=-14.0):
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(x)
    y = x * db(target - lufs)
    # soft limiter to -1 dBTP-ish
    lim = db(-1.2)
    y = np.where(np.abs(y) > lim * 0.8, np.sign(y) * (lim * 0.8 + (lim * 0.2) * np.tanh((np.abs(y) - lim * 0.8) / (lim * 0.2))), y)
    return y, lufs


def main():
    dia = dialogue()
    mus, sr = sf.read("/opt/work/audio/music.wav")
    mus = mus[:N]
    if len(mus) < N:
        mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
    mus = mus * db(4)
    acc, _ = sf.read("/opt/work/audio/music_acc.wav")
    acc = acc[:N]
    if len(acc) < N:
        acc = np.pad(acc, ((0, N - len(acc)), (0, 0)))
    # duck the score bed deeply under dialogue; accents (high/low word hits) only lightly
    env = env_follow(dia.mean(axis=1), 0.04, 0.5)
    k = np.clip(env / 0.03, 0, 1)
    mus = mus * (1.0 - 0.72 * k)[:, None] + acc * db(5) * (1.0 - 0.35 * k)[:, None]
    amb, fx = ambience_and_fx()
    mix = dia * db(0) + mus + amb * db(-6) + fx * db(-2)
    # no fade-in at the start (first frame is live); short fade at the very end
    tail = int(2.5 * SR)
    mix[-tail:] *= np.linspace(1, 0, tail)[:, None]
    mix, lufs_in = loudness_normalize(mix)
    sf.write("/opt/work/audio/final_mix.wav", mix.astype(np.float32), SR)
    sf.write("/opt/work/audio/stem_dialogue.wav", dia.astype(np.float32), SR)
    print("MIX_OK in-LUFS %.1f -> -14, peak %.3f" % (lufs_in, np.abs(mix).max()))


if __name__ == "__main__":
    main()
