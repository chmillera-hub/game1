"""Mixes voices + sfx + music according to timeline.json -> audio/mix.wav ; also writes lip-sync envelopes."""
import json, numpy as np, soundfile as sf
from scipy.signal import resample_poly
import audio_lib as A
import music as MU
from audio_lib import SR

tl = json.load(open("timeline.json"))
M = tl["markers"]
N = int((tl["duration"] + 1.0) * SR)
voice = np.zeros(N)
sfx = np.zeros(N)
sfx_duck = np.zeros(N)  # long beds that should dip under dialogue
mus = np.zeros(N)


def rms(x):
    return np.sqrt(np.mean(x ** 2) + 1e-12)


def load_voice(lid):
    x, sr = sf.read(f"audio/voice/{lid}.wav")
    return resample_poly(x, SR // sr * 1, 1) if sr != SR else x


def fx_chain(x, spk, lid):
    if spk == "WHISP":
        x = A.lp(A.hp(x, 180), 5500)
        y = A.reverb(x, 0.9, 0.3, 4000)
        d = np.zeros(len(y)); i = int(0.11 * SR); d[i:] = y[:-i] * 0.3
        return y + d
    if spk in ("THER", "SJW", "GREG", "LINDA"):
        return A.reverb(A.hp(x, 160), 1.3, 0.25, 6000)
    if lid == "G3":
        x = A.bp(x, 300, 3800)
        return np.tanh(2.0 * x / (np.abs(x).max() + 1e-9)) * 0.7
    if spk == "NARR":
        return A.reverb(x, 0.5, 0.07, 6000)
    return A.reverb(x, 0.35, 0.06, 6000)


# ------------------------------------------------------------------ voices
env_fps = 24
envs = {}
for ln in tl["lines"]:
    x = load_voice(ln["id"])
    x = x / rms(x) * 10 ** (-19 / 20)
    if ln["spk"] == "WHISP":
        x *= 0.9
    # lip-sync envelope (per video frame)
    hop = SR // env_fps
    e = np.array([rms(x[i:i + hop]) for i in range(0, len(x), hop)])
    e = np.clip(e / (np.percentile(e, 90) + 1e-9), 0, 1.2)
    envs[ln["id"]] = [round(float(v), 3) for v in e]
    y = fx_chain(x, ln["spk"], ln["id"])
    A.place(voice, y, ln["start"])
for rid in ("R1", "R2"):
    x = load_voice(rid)
    hop = SR // env_fps
    e = np.array([rms(x[i:i + hop]) for i in range(0, len(x), hop)])
    e = np.clip(e / (np.percentile(e, 90) + 1e-9), 0, 1.2)
    envs[rid] = [round(float(v), 3) for v in e]
json.dump(envs, open("lipsync.json", "w"))

# ------------------------------------------------------------------ sfx
SFX_MASTER = 0.55
cache = {}
for ev in tl["sfx"]:
    name = ev["name"]
    if name == "deflate_long":
        d = M["trombone"] - M["deflate_start"] + 0.8
        s = A.sfx_deflate_long(d)
        s[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))
    elif name == "heartbeat":
        s = A.sfx_heartbeat(M["fart"] - ev["start"] - 0.3, 75, 140)
    elif name == "lawnmower":
        s = A.sfx_lawnmower(M["couple_turn"] - ev["start"] + 0.5)
    else:
        if name not in cache:
            cache[name] = A.SFX[name]()
        s = cache[name]
    A.place(sfx_duck if name in ("deflate_long", "lawnmower", "heartbeat") else sfx, s, ev["start"], ev["gain"] * SFX_MASTER)

# ------------------------------------------------------------------ music
tracks = {}
for m in tl["music"]:
    name = m["track"]
    L = m["end"] - m["start"] + m["offset"] + 1
    if name == "remix":
        r1 = load_voice("R1"); r2 = load_voice("R2")
        x = MU.track_remix(r1 / np.abs(r1).max(), r2 / np.abs(r2).max(), A.sfx_clown_honk(False),
                           A.norm(A.inhale_wheeze(0.6)), dur=L)
        level = -17
    else:
        x = MU.TRACKS[name](dur=L)
        level = -27 if name != "sad_clown" else -29
    x = x[int(m["offset"] * SR):]
    n = int((m["end"] - m["start"]) * SR)
    x = x[:n] if len(x) >= n else np.concatenate([x, np.zeros(n - len(x))])
    x = x / rms(x[: max(n, 1)]) * 10 ** (level / 20)
    fi, fo = int(m["fin"] * SR), int(m["fout"] * SR)
    if fi: x[:fi] *= np.linspace(0, 1, fi)
    if fo: x[-fo:] *= np.linspace(1, 0, fo)
    A.place(mus, x * m["gain"], m["start"])

# ducking: music dips under dialogue
venv = A.lp(np.abs(voice), 3)
venv = venv / (venv.max() + 1e-9)
duck = 1 - 0.5 * np.clip(venv * 6, 0, 1)
duck = A.lp(duck, 4)
# no ducking during the remix itself (vocals are part of the track)
duck2 = A.lp(1 - 0.45 * np.clip(venv * 6, 0, 1), 4)
mix = voice + sfx + sfx_duck * duck2 + mus * duck

# soft-knee limiter on peaks only
thr = 0.6
a = np.abs(mix)
over = a > thr
mix[over] = np.sign(mix[over]) * (thr + (1 - thr) * np.tanh((a[over] - thr) / (1 - thr)))
sf.write("audio/mix.wav", (mix * 0.95).astype(np.float32), SR)
print("mix written", len(mix) / SR, "s; voice rms", rms(voice), "sfx rms", rms(sfx), "music rms", rms(mus))
