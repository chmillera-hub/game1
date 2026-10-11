"""Final soundtrack mix.

    python3 audio/mix.py            # -> out/mix.wav (44.1 kHz stereo, loudness-normalised)

Inputs: data/timeline.json (beats: start, speaker, audio, inner, scene), data/sfx_events.json
(from tools/collect_sfx.mjs), out/music.wav (from audio/music.py with data/music_cues.json).
- Narrator: intimate, warm, a touch of short room reverb, centred.
- In-world dialogue: slightly more room (the Mind HQ space); REAL_ROOM scenes drier.
- Inner thoughts: already processed in tts.py; centred, slightly quieter.
- Music: sidechain-ducked under all speech (smooth), then everything normalised to -16 LUFS, peaks < -1 dBTP.
"""
import json, os, subprocess, sys
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt, resample_poly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100

def load(path):
    a, sr = sf.read(path, dtype="float32", always_2d=True)
    if sr != SR:
        from math import gcd
        g = gcd(sr, SR)
        a = resample_poly(a, SR // g, sr // g, axis=0).astype(np.float32)
    if a.shape[1] == 1:
        a = np.repeat(a, 2, axis=1)
    return a[:, :2]

def make_ir(seconds=1.2, decay=0.35, predelay=0.012, damp=6000, seed=1):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    env = np.exp(-t / decay)
    ir = rng.standard_normal((n, 2)) * env[:, None]
    sos = butter(2, damp / (SR / 2), "low", output="sos")
    ir = sosfilt(sos, ir, axis=0)
    ir = np.concatenate([np.zeros((int(predelay * SR), 2)), ir])
    return (ir / np.sqrt((ir ** 2).sum(axis=0, keepdims=True))).astype(np.float32)

IR_SMALL = make_ir(0.6, 0.12, 0.008, 5500, 2)
IR_HQ = make_ir(1.6, 0.42, 0.018, 5000, 3)

def reverb(a, ir, wet):
    w = fftconvolve(a, ir, axes=0)[: len(a) + len(ir)]
    out = np.zeros_like(w)
    out[: len(a)] = a
    return out * (1 - wet * 0.3) + w * wet

def pan(a, p):
    l = np.cos((p + 1) * np.pi / 4); r = np.sin((p + 1) * np.pi / 4)
    return a * np.array([l, r], dtype=np.float32) * np.sqrt(2)

def place(track, clip, at, gain_db=0.0):
    i = int(round(at * SR))
    if i < 0:
        clip = clip[-i:]; i = 0
    j = min(len(track), i + len(clip))
    if j > i:
        track[i:j] += clip[: j - i] * (10 ** (gain_db / 20))

def envelope(x, attack, release):
    y = np.zeros_like(x)
    a = 1 - np.exp(-1 / (attack * SR / 64)); r = 1 - np.exp(-1 / (release * SR / 64))
    v = 0.0
    for i in range(len(x)):
        k = a if x[i] > v else r
        v += (x[i] - v) * k
        y[i] = v
    return y

def main():
    tl = json.load(open(os.path.join(ROOT, "data/timeline.json")))
    N = int((tl["duration"] + 1.0) * SR)
    voice = np.zeros((N, 2), np.float32)
    scenes = {s["id"]: s for s in tl["scenes"]}
    for bid in tl["order"]:
        b = tl["beats"][bid]
        if b["kind"] != "line":
            continue
        a = load(os.path.join(ROOT, b["audio"]))
        loc = scenes[b["scene"]].get("location", "")
        if b["speaker"] == "NARRATOR":
            a = reverb(a, IR_SMALL, 0.12); g = 0.0
        elif b.get("inner"):
            g = -2.0
        else:
            a = reverb(a, IR_SMALL if loc == "REAL_ROOM" else IR_HQ, 0.10 if loc == "REAL_ROOM" else 0.16); g = -1.0
        place(voice, a, b["start"], g)

    sfx = np.zeros((N, 2), np.float32)
    ev_path = os.path.join(ROOT, "data/sfx_events.json")
    events = json.load(open(ev_path)) if os.path.exists(ev_path) else []
    for e in events:
        p = os.path.join(ROOT, "audio/sfx", e["name"] + ".wav")
        if not os.path.exists(p):
            print("missing sfx", e["name"]); continue
        a = load(p)
        if e.get("rate", 1) != 1:
            a = resample_poly(a, 100, int(100 * e["rate"]), axis=0).astype(np.float32)
        if e.get("until") is not None:
            L = int((e["until"] - e["at"]) * SR)
            if L > 0:
                if e.get("loop") and len(a) < L:
                    reps = int(np.ceil(L / len(a)))
                    a = np.concatenate([a] * reps)
                a = a[:L].copy()
                f = min(len(a), int(e.get("fade", 0.3) * SR))
                if f > 0:
                    a[-f:] *= np.linspace(1, 0, f)[:, None]
        if e.get("pan"):
            a = pan(a, e["pan"])
        place(sfx, a, e["at"], e.get("gain", 0))
    sfx = reverb(sfx, IR_HQ, 0.12)[:N]

    music_path = os.path.join(ROOT, "out/music.wav")
    music = np.zeros((N, 2), np.float32)
    if os.path.exists(music_path):
        m = load(music_path)
        music[: min(N, len(m))] = m[:N]
    # sidechain duck music under speech
    det = np.abs(voice).max(axis=1)
    det = det[: N // 64 * 64].reshape(-1, 64).max(axis=1)
    env = envelope((det > 0.02).astype(np.float32), 0.08, 0.6)
    gain_db = -8.5 * env
    g = np.repeat(10 ** (gain_db / 20), 64)
    g = np.concatenate([g, np.full(N - len(g), g[-1] if len(g) else 1.0)])
    music *= g[:, None]

    mix = voice * 1.0 + sfx * 0.9 + music * float(os.environ.get("MUSIC_GAIN", "0.55"))
    mix = mix[: int(tl["duration"] * SR)]
    tmp = os.path.join(ROOT, "out/mix_raw.wav")
    sf.write(tmp, mix, SR, subtype="FLOAT")
    # two-pass loudnorm to -16 LUFS / -1.5 dBTP
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "loudnorm=I=-16:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"): r.stderr.rfind("}") + 1]
    m = json.loads(js)
    af = (f"loudnorm=I=-16:TP=-2.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", af, "-ar", str(SR), os.path.join(ROOT, "out/mix.wav")], check=True)
    print(f"mix: {len(mix)/SR:.1f}s, input loudness {m['input_i']} LUFS -> -16; {len(events)} sfx events")

if __name__ == "__main__":
    main()
