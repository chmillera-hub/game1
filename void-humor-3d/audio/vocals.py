"""Non-verbal vocalizations for `vocal` beats (the Void's laughs/whispers/huffs, Jesus's mm-hms, gasps...).

    python3 audio/vocals.py [data/screenplay.json] [beat_ids]   -> audio/vocals/<beat>.wav, data/vocals.json

Built from Kokoro TTS onomatopoeia (pitched/layered per character) plus synthesized breath/cough/whisper
textures. Every clip is fitted to the beat's `duration` (time-stretched a little, looped or trimmed with fades).
Whispers are "whisperized": the STFT magnitude of a gibberish TTS phrase drives noise excitation (no pitch),
so you hear whispering but can't make out the words — the joke is that we never learn what was said.
"""
import json, os, sys
import numpy as np
import soundfile as sf
from scipy.signal import stft, istft, butter, sosfilt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts import TTS, VOICES, SR, trim, ffmpeg_filter, fade

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VOCAL_VOICES = {
    "VOID": {"blend": [("am_onyx", 0.5), ("am_fenrir", 0.5)], "pitch": 0.72, "speed": 1.0},
    "JESUS": {"blend": VOICES["JESUS"]["blend"], "pitch": 0.985, "speed": 0.95},
    "USER": {"blend": VOICES["USER"]["blend"], "pitch": 1.02, "speed": 1.05},
    "FEAR": {"blend": VOICES["FEAR"]["blend"], "pitch": 1.12, "speed": 0.95},
    "MAGICIAN": {"blend": VOICES["MAGICIAN"]["blend"], "pitch": 0.9, "speed": 0.95},
    "NARRATOR": {"blend": VOICES["NARRATOR"]["blend"], "pitch": 1.0, "speed": 1.0},
}

TEXT = {
    "laugh_maniacal": ["Hah! Ha ha ha ha ha!", "Hahahaha! Ha ha HAAA ha!", "Bwahaha ha ha ha!", "Ha ha ha! Hahahahaha!"],
    "laugh_soft": ["Heh heh heh.", "Ha ha.", "Hm hm hm."],
    "giggle": ["Hehehe.", "Heh heh hehe.", "Hee hee hee."],
    "snort": ["Pfft!"],
    "mmhm": ["Mm-hm.", "Mm-hmm.", "Mhm."],
    "hum": ["Mmmm.", "Hmmm."],
    "scream_short": ["Aaaah!", "Aah!"],
    "whimper": ["Nnn... hnnn...", "Hnn..."],
    "gasp": ["Hah!"],
    "sigh": ["Haaahh."],
    "huff": ["Hmph!", "Hmph."],
    "gulp": [],
    "cough": [],
    "whisper": ["so listen, okay, mm, the thing is, pss, okay, so, pss pss, you know, right, so, sss",
                "okay okay, hm, so here is the thing, psst, right, listen, mm, sss, so, yes"],
}

def rngf(seed):
    return np.random.default_rng(seed)

def noise_breath(dur, seed, lo=500, hi=3500, attack=0.04, inhale=False, gain=0.35):
    n = int(dur * SR); r = rngf(seed)
    x = r.standard_normal(n).astype(np.float32)
    x = sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x).astype(np.float32)
    t = np.linspace(0, 1, n)
    env = np.minimum(1, t / max(1e-3, attack / dur)) * (1 - t) ** (0.6 if not inhale else 0.3)
    if inhale: env = env[::-1]
    return x * env.astype(np.float32) * gain / (np.abs(x).max() + 1e-9)

def cough(seed, gain=0.6):
    r = rngf(seed); n = int(0.22 * SR)
    x = r.standard_normal(n).astype(np.float32)
    x = sosfilt(butter(2, [250, 2200], "band", fs=SR, output="sos"), x)
    t = np.arange(n) / SR
    env = np.exp(-t / 0.05) * (1 - np.exp(-t / 0.004))
    return (x * env / (np.abs(x).max() + 1e-9) * gain).astype(np.float32)

def gulp(seed):
    n = int(0.18 * SR); t = np.arange(n) / SR
    f = 180 + 600 * np.exp(-t / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.04)
    return (x * 0.5).astype(np.float32)

def whisperize(a, seed=1):
    f, tt, Z = stft(a, fs=SR, nperseg=1024, noverlap=768)
    mag = np.abs(Z)
    ph = rngf(seed).uniform(-np.pi, np.pi, mag.shape)
    _, y = istft(mag * np.exp(1j * ph), fs=SR, nperseg=1024, noverlap=768)
    y = sosfilt(butter(2, [350, 7800], "band", fs=SR, output="sos"), y).astype(np.float32)
    return y / (np.abs(y).max() + 1e-9) * 0.5

def fit(a, dur, loop_src=None):
    n = int(dur * SR)
    if len(a) > n:
        ratio = len(a) / n
        if ratio < 1.3:
            a = ffmpeg_filter(a, SR, f"atempo={ratio:.4f}")
        a = a[:n]
        a = fade(a, SR, 0.005, min(0.25, dur * 0.2))
    elif len(a) < n:
        a = np.concatenate([a, np.zeros(n - len(a), np.float32)])
    return a.astype(np.float32)

def make(tts, vocal, spk, dur, seed):
    vv = VOCAL_VOICES.get(spk, VOCAL_VOICES["NARRATOR"])
    def say(text, pitch=None, speed=None):
        x = trim(tts.say(vv["blend"], text, speed or vv["speed"]))
        p = pitch or vv["pitch"]
        if p != 1.0:
            x = ffmpeg_filter(x, SR, f"asetrate={int(SR * p)},aresample={SR},atempo={1 / p:.4f}")
        return x
    texts = TEXT.get(vocal, [])
    if vocal == "laugh_maniacal":
        parts, k = [], 0
        while sum(len(p) for p in parts) < dur * SR:
            low = say(texts[k % len(texts)], speed=1.05 + 0.05 * (k % 2))
            hi = say(texts[k % len(texts)], pitch=vv["pitch"] * 1.32, speed=1.05 + 0.05 * (k % 2))
            m = min(len(low), len(hi))
            seg = low[:m] + 0.32 * hi[:m]
            parts.append(seg)
            if spk == "VOID" and k % 2 == 1:  # coughs mid-laugh (stars come out)
                parts.append(np.zeros(int(0.06 * SR), np.float32)); parts.append(cough(seed + k)); parts.append(cough(seed + k + 7) * 0.8)
            parts.append(np.zeros(int(0.12 * SR), np.float32))
            k += 1
        a = np.concatenate(parts)
        a = a[: int(dur * SR)]
        a = fade(a, SR, 0.01, 0.5)
    elif vocal == "whisper":
        src = say(texts[seed % len(texts)], pitch=1.0, speed=1.1)
        a = whisperize(src, seed)
        while len(a) < dur * SR:
            a = np.concatenate([a, whisperize(src[::-1].copy(), seed + 1)])
        a = fade(a[: int(dur * SR)], SR, 0.05, 0.3) * (0.55 if spk == "VOID" else 0.45)
    elif vocal == "huff":
        a = np.concatenate([noise_breath(0.5, seed, 300, 2500, 0.02, gain=0.5), np.zeros(int(0.08 * SR), np.float32),
                            say(texts[0]), np.zeros(int(0.1 * SR), np.float32), noise_breath(0.45, seed + 1, 300, 2400, 0.02, gain=0.45)])
        if spk == "VOID": a = a + 0.0
    elif vocal == "sigh":
        a = np.concatenate([noise_breath(0.35, seed, 400, 2500, 0.2, inhale=True, gain=0.25), say(texts[0]) * 0.7])
    elif vocal == "gasp":
        a = np.concatenate([noise_breath(0.28, seed, 600, 4000, 0.03, inhale=True, gain=0.45), say(texts[0]) * 0.6])
    elif vocal == "cough":
        a = np.concatenate([cough(seed), np.zeros(int(0.12 * SR), np.float32), cough(seed + 3) * 0.8])
    elif vocal == "gulp":
        a = gulp(seed)
    elif vocal == "snort":
        a = noise_breath(0.18, seed, 200, 1500, 0.005, gain=0.6)
    else:
        a = say(texts[seed % len(texts)] if texts else "Hm.")
    a = fit(a, dur)
    a = a / (np.abs(a).max() + 1e-9) * (0.8 if vocal != "whisper" else 0.45)
    return a.astype(np.float32)

def main():
    sp = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data/screenplay.json")))
    only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    os.makedirs(os.path.join(ROOT, "audio/vocals"), exist_ok=True)
    outp = os.path.join(ROOT, "data/vocals.json")
    res = json.load(open(outp)) if (only and os.path.exists(outp)) else {}
    tts = TTS()
    for sc in sp["scenes"]:
        for i, b in enumerate(sc["beats"]):
            if b["kind"] != "vocal" or (only and b["id"] not in only):
                continue
            seed = sum(map(ord, b["id"]))
            a = make(tts, b["vocal"], b["speaker"], float(b["duration"]), seed)
            f = os.path.join("audio/vocals", f"{b['id']}.wav")
            sf.write(os.path.join(ROOT, f), a, SR, subtype="PCM_16")
            res[b["id"]] = {"speaker": b["speaker"], "vocal": b["vocal"], "file": f, "dur": round(len(a) / SR, 3),
                            "caption": b.get("caption")}
            print(f"{b['id']:8s} {b['speaker']:8s} {b['vocal']:15s} {len(a)/SR:5.2f}s", flush=True)
    json.dump(res, open(outp, "w"), indent=1)

if __name__ == "__main__":
    main()
