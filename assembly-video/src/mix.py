"""Mix voices + sfx + music for 'The Assembly' -> audio/mix.wav, lipsync.json"""
import json, numpy as np, soundfile as sf
from scipy.signal import resample_poly
import audio_lib as A
import audio2 as A2
import music2 as M2
from audio_lib import SR

tl = json.load(open("timeline.json"))
M = tl["markers"]
N = int((tl["duration"] + 1.5) * SR)
voice = np.zeros(N)
sfx = np.zeros(N)
mus = np.zeros(N)
GYM_SCENES = {"stands", "losers", "crisis", "hat", "carry", "stool", "roleplay", "bomb", "saves", "assembly2", "solo", "roast"}


def rms(x):
    return np.sqrt(np.mean(x ** 2) + 1e-12)


def scene_at(t):
    for s in tl["scenes"]:
        if s["start"] <= t < s["end"]:
            return s["name"]
    return tl["scenes"][-1]["name"]


def load_voice(lid):
    x, sr = sf.read(f"audio/voice/{lid}.wav")
    return resample_poly(x, SR // sr, 1) if sr != SR else x


envs = {}
for ln in tl["lines"]:
    x = load_voice(ln["id"])
    x = x / rms(x) * 10 ** (-19 / 20)
    hop = SR // 24
    e = np.array([rms(x[i:i + hop]) for i in range(0, len(x), hop)])
    e = np.clip(e / (np.percentile(e, 90) + 1e-9), 0, 1.2)
    envs[ln["id"]] = [round(float(v), 3) for v in e]
    if ln["spk"] == "CINNER":
        y = A.reverb(A.lp(A.hp(x, 160), 6000), 1.0, 0.32, 4000) * 0.9
    elif scene_at(ln["start"]) in GYM_SCENES:
        y = A.reverb(x, 0.9, 0.12, 5000)          # gym / PA room
    elif ln["spk"] == "NARR":
        y = A.reverb(x, 0.5, 0.07, 6000)
    else:
        y = A.reverb(x, 0.35, 0.06, 6000)
    A.place(voice, y, ln["start"])
json.dump(envs, open("lipsync.json", "w"))

SFX_MASTER = 0.55
cache = {}
for ev in tl["sfx"]:
    name = ev["name"]
    if name not in cache:
        cache[name] = A2.ALL_SFX[name]()
    A.place(sfx, cache[name], ev["start"], ev["gain"] * SFX_MASTER)

for m in tl["music"]:
    L = m["end"] - m["start"] + 1
    x = M2.TRACKS2[m["track"]](dur=L)
    n = int((m["end"] - m["start"]) * SR)
    x = x[:n] if len(x) >= n else np.concatenate([x, np.zeros(n - len(x))])
    x = x / rms(x[: max(n, 1)]) * 10 ** (m.get("level", -27) / 20)
    fi, fo = int(m["fin"] * SR), int(m["fout"] * SR)
    if fi: x[:fi] *= np.linspace(0, 1, fi)
    if fo: x[-fo:] *= np.linspace(1, 0, fo)
    A.place(mus, x * m["gain"], m["start"])

venv = A.lp(np.abs(voice), 3)
venv = venv / (venv.max() + 1e-9)
duck = A.lp(1 - 0.5 * np.clip(venv * 6, 0, 1), 4)
duck_sfx = A.lp(1 - 0.3 * np.clip(venv * 6, 0, 1), 4)   # crowd sounds dip a little under dialogue
mix = voice + sfx * duck_sfx + mus * duck
thr = 0.6
a = np.abs(mix)
over = a > thr
mix[over] = np.sign(mix[over]) * (thr + (1 - thr) * np.tanh((a[over] - thr) / (1 - thr)))
sf.write("audio/mix.wav", (mix * 0.95).astype(np.float32), SR)
print("mix written", round(len(mix) / SR, 1), "s")
