#!/usr/bin/env python3
"""Voice processing + final mix for "The Last Witness".

Inputs : build/timeline.json, build/tts/beat_NNNN.wav (24 kHz mono),
         build/audio/work/{bed,cues,amb,events}.npy  (from audio/score.py, 48 kHz float32)
Outputs: build/audio/voice.wav, music.wav, sfx.wav, mix.wav  (48 kHz mono 16-bit,
         exactly timeline.duration long). The stems are the ducked, gain-matched layers
         as they sit in the mix (voice + music + sfx == mix before the peak limiter).

Run:  python3 -I audio/mix.py
"""
import json
import os
import subprocess
import time
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy import ndimage, signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TIMELINE = os.path.join(ROOT, "build", "timeline.json")
TTS = os.path.join(ROOT, "build", "tts")
OUT = os.path.join(ROOT, "build", "audio")
WORK = os.path.join(OUT, "work")
SR = 48000

TARGET_LUFS = -16.0
TP_CEIL = -1.5            # dBTP limit
LIMIT_AT = -2.0           # limiter ceiling on the 4x oversampled signal (margin for codec)
MUSIC_REL = -8.5          # un-ducked music bed loudness relative to speech (LU)
DUCK = {"bed": 11.0, "bed_vision": 9.0, "cues": 9.0, "amb": 6.0, "events": 4.0}
VOICE_PLR = 13.5         # voice peak ceiling above its integrated loudness (dB)
SAFETY_MARGIN = 12.5     # speech-first safety: background kept >= this many LU under active speech

# ---------------------------------------------------------------------------
# voice treatment: ffmpeg filter chain, reverb (numpy), level offset (dB vs. dialogue norm)
# ---------------------------------------------------------------------------
COMP = "acompressor=threshold=0.06:ratio=2.2:attack=10:release=180:knee=4"
HP = "highpass=f=75:poles=2"
RS = "aresample=48000:resampler=soxr"
VOICES = {
    # clean, close
    "human":      dict(af=[HP, "equalizer=f=280:t=q:w=1.2:g=-1.5", "equalizer=f=3200:t=q:w=1.5:g=1.2", COMP], rev=None, lvl=0.0),
    # softer, in memory: band-limited a touch, short room
    "human_echo": dict(af=[HP, "lowpass=f=6000", COMP], rev=("short", 0.30), lvl=-3.5),
    # frail: quieter, band-limited, slow tremolo, short room
    "last_human": dict(af=["highpass=f=170:poles=2", "lowpass=f=4300", "tremolo=f=2.6:d=0.14", COMP], rev=("short", 0.24), lvl=-4.0),
    # warm and clean with a very light airy room
    "ai":         dict(af=[HP, "equalizer=f=190:t=q:w=1.0:g=1.2", "equalizer=f=6500:t=q:w=1.5:g=-1.5", COMP], rev=("air", 0.10), lvl=0.0),
    "ai_inner":   dict(af=[HP, "equalizer=f=190:t=q:w=1.0:g=1.0", "lowpass=f=7500", COMP], rev=("inner", 0.42), lvl=-1.5),
    "ai_echo":    dict(af=["highpass=f=160:poles=2", "lowpass=f=4800", COMP], rev=("echo", 0.55), lvl=-3.0),
    "ai_whisper": dict(af=[HP, "lowpass=f=7000", COMP], rev=("air", 0.14), lvl=-3.0),
    "ai_soft":    dict(af=[HP, "lowpass=f=7500", COMP], rev=("air", 0.12), lvl=-2.5),
    # pitched up ~2.5 st, formants preserved: younger, fragile
    "suffering":  dict(af=["rubberband=pitch=1.15535:formant=preserved:transients=smooth:window=standard", HP, COMP], rev=("air", 0.14), lvl=-1.0),
    "boredom":    dict(af=[HP, "highshelf=f=4000:g=-2.5", "equalizer=f=220:t=q:w=1.0:g=0.8", COMP], rev=("air", 0.08), lvl=0.0),
    "loneliness": dict(af=[HP, "lowpass=f=7000", COMP], rev=("lonely", 0.30), lvl=-2.0),
}


def make_ir(dur, t60, lp_a, lp_b, predelay, seed, taps=()):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = r.standard_normal(n)
    sa = signal.butter(2, lp_a, "low", fs=SR, output="sos")
    sb = signal.butter(2, lp_b, "low", fs=SR, output="sos")
    x = np.linspace(0, 1, n) ** 0.6
    ir = (signal.sosfilt(sa, noise) * (1 - x) + signal.sosfilt(sb, noise) * x) * 10 ** (-3 * t / t60)
    ir[:240] *= np.linspace(0, 1, 240)
    ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
    ir /= np.sqrt(np.sum(ir ** 2))
    for d, g in taps:   # discrete distant echoes
        k = int(d * SR)
        ir[k:k + 2400] += g * ir[int(predelay * SR):int(predelay * SR) + 2400] * 6
    hp = signal.butter(2, 180, "high", fs=SR, output="sos")   # keep reverb out of the low end
    ir = signal.sosfilt(hp, ir)
    return (ir / np.sqrt(np.sum(ir ** 2))).astype(np.float32)


IRS = {
    "air":    make_ir(0.6, 0.35, 6000, 2500, 0.008, 11),
    "short":  make_ir(1.2, 0.8, 5000, 1800, 0.012, 12),
    "inner":  make_ir(2.2, 1.6, 4500, 1500, 0.020, 13),
    "echo":   make_ir(3.0, 2.2, 3500, 1200, 0.030, 14, taps=((0.29, 0.5), (0.58, 0.25))),
    "lonely": make_ir(1.8, 1.2, 5000, 1600, 0.018, 15),
}
REV_TAIL = {"air": 0.6, "short": 1.2, "inner": 2.2, "echo": 3.0, "lonely": 1.8}

# ---------------------------------------------------------------------------
# loudness tools (ITU-R BS.1770-4) and IO
# ---------------------------------------------------------------------------
K1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
K2 = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def kweight(x):
    return signal.lfilter(*K2, signal.lfilter(*K1, x.astype(np.float64)))


def block_loudness(x, block=0.4, hop=0.1, weighted=True):
    y = kweight(x) if weighted else x.astype(np.float64)
    c = np.concatenate([[0.0], np.cumsum(y * y)])
    nb, nh = int(block * SR), int(hop * SR)
    starts = np.arange(0, len(y) - nb + 1, nh)
    z = (c[starts + nb] - c[starts]) / nb
    return starts, -0.691 + 10 * np.log10(z + 1e-20)


def integrated(x):
    _, L = block_loudness(x)
    L = L[L > -70]
    if not len(L):
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(10 ** ((L + 0.691) / 10))) - 10
    L = L[L > rel]
    return float(-0.691 + 10 * np.log10(np.mean(10 ** ((L + 0.691) / 10))))


def true_peak(x, chunk=SR * 20):
    pk = 0.0
    for i in range(0, len(x), chunk):
        a = max(0, i - 64)
        y = signal.resample_poly(x[a:i + chunk + 64].astype(np.float64), 4, 1)
        pk = max(pk, float(np.abs(y).max()))
    return 20 * np.log10(pk + 1e-12)


def oversampled_peaks(x, chunk=SR * 20):
    """per-sample max |x| of the 4x-oversampled signal"""
    out = np.empty(len(x), np.float32)
    for i in range(0, len(x), chunk):
        a = max(0, i - 64)
        b = min(len(x), i + chunk + 64)
        y = np.abs(signal.resample_poly(x[a:b].astype(np.float64), 4, 1)).reshape(-1, 4).max(1)
        out[i:min(len(x), i + chunk)] = y[i - a:i - a + min(chunk, len(x) - i)]
    return np.maximum(out, np.abs(x))


def write_wav(path, x):
    y = np.round(np.clip(x, -1, 32766 / 32767) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.tobytes())


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


# ---------------------------------------------------------------------------
# voice
# ---------------------------------------------------------------------------
def process_beat(b):
    v = VOICES[b["voice"]]
    src = os.path.join(TTS, "beat_%04d.wav" % b["id"])
    af = ",".join(v["af"][:1] + [RS] + v["af"][1:]) if v["af"][0].startswith("rubberband") else ",".join([RS] + v["af"])
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-af", af, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, check=True, capture_output=True).stdout, np.float32).astype(np.float64)
    # dialogue level normalisation on active speech (K-weighted), partial so phrasing stays natural
    y = kweight(x)
    fr = y[: len(y) // 480 * 480].reshape(-1, 480)
    e = (fr ** 2).mean(1)
    act = e > e.max() * 10 ** (-30 / 10)
    lev = -0.691 + 10 * np.log10(e[act].mean() + 1e-20)
    want = -24.0 + v["lvl"]
    g = np.clip(want - lev, -8, 8)
    x = x * 10 ** (g / 20)
    if v["rev"]:
        kind, wet = v["rev"]
        x = np.concatenate([x, np.zeros(int(REV_TAIL[kind] * SR))])
        w = signal.oaconvolve(x, IRS[kind])[: len(x)]
        dry = 1.0 - 0.5 * wet if kind == "echo" else 1.0
        x = dry * x + wet * w
        # trim the silent end of the tail
        nz = np.nonzero(np.abs(x) > 1e-5)[0]
        x = x[: (nz[-1] + 1) if len(nz) else len(x)]
    return b, x.astype(np.float32), g


def build_voice(tl, n):
    beats = [b for b in tl["beats"] if b["kind"] == "speech"]
    voice = np.zeros(n, np.float32)
    gains = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        for b, x, g in ex.map(process_beat, beats):
            i0 = int(round(b["start"] * SR))
            m = min(len(x), n - i0)
            voice[i0:i0 + m] += x[:m]
            gains.setdefault(b["voice"], []).append(g)
    print(f"voice: {len(beats)} beats processed in {time.time() - t0:.0f}s")
    for k, v in sorted(gains.items()):
        print(f"  {k:11s} n={len(v):3d}  level trim {np.mean(v):+.1f} dB (range {np.min(v):+.1f}..{np.max(v):+.1f})")
    return voice


# ---------------------------------------------------------------------------
# ducking
# ---------------------------------------------------------------------------
def duck_curve(tl, n, CR=200):
    """0..1 'speech present' curve: anticipates speech (lookahead), bridges short pauses,
    releases smoothly so the music breathes up only in real pauses"""
    nc = int(n / SR * CR) + 2
    tgt = np.zeros(nc)
    vis = np.zeros(nc)
    sp = sorted((b["start"], b["end"], b["shot"]) for b in tl["beats"] if b["kind"] == "speech")
    merged = []
    for s, e, shot in sp:
        if merged and s - merged[-1][1] < 1.1:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    for s, e in merged:
        tgt[int((s - 0.30) * CR):int((e + 0.25) * CR)] = 1.0
    for s, e, shot in sp:
        if shot == "vision_full":
            vis[int(s * CR):int(e * CR)] = 1.0
    a_att = 1 - np.exp(-1 / (0.10 * CR))
    a_rel = 1 - np.exp(-1 / (0.75 * CR))
    env = np.zeros(nc)
    v = 0.0
    for i in range(nc):
        t = tgt[i]
        v += (t - v) * (a_att if t > v else a_rel)
        env[i] = v
    k = np.ones(int(0.05 * CR)) / int(0.05 * CR)
    env = np.convolve(env, k, mode="same")
    vis = np.convolve(vis, np.ones(int(1.0 * CR)) / int(1.0 * CR), mode="same")
    tc = np.arange(nc) / CR
    ts = np.arange(n) / SR
    return np.interp(ts, tc, env).astype(np.float32), np.interp(ts, tc, vis).astype(np.float32), merged


# ---------------------------------------------------------------------------
# limiter (block-rate gain computer, 2 ms lookahead, smooth release)
# ---------------------------------------------------------------------------
def limiter_gain(x, ceil_db):
    ceil = 10 ** (ceil_db / 20)
    pk = oversampled_peaks(x)
    B = 48
    nb = len(x) // B + 1
    pb = np.zeros(nb * B, np.float32)
    pb[: len(pk)] = pk
    pb = pb.reshape(nb, B).max(1)
    need = np.minimum(1.0, ceil / np.maximum(pb, 1e-9))
    need = ndimage.minimum_filter1d(need, size=5, origin=0)       # +-2 blocks lookahead/hold
    g = np.empty(nb)
    cur = 1.0
    rel = 1 - np.exp(-1 / (0.12 * SR / B))
    for i in range(nb):           # instant attack (already looked ahead), 120 ms release
        r = need[i]
        cur = r if r < cur else cur + (r - cur) * rel
        g[i] = cur
    g = ndimage.minimum_filter1d(g, size=3)
    tb = (np.arange(nb) + 0.5) * B
    gs = np.interp(np.arange(len(x)), tb, g).astype(np.float32)
    return gs, float(db(g.min()))


def safety_gain(voice, bg, hop=0.05):
    st, Lv = block_loudness(voice, 0.4, hop)
    _, Lb = block_loudness(bg, 0.4, hop)
    Li = integrated(voice)
    active = Lv > Li - 12
    att = np.where(active, np.clip(Lb - (Lv - SAFETY_MARGIN), 0, 10), 0.0)
    att = ndimage.maximum_filter1d(att, size=7)               # hold +-150 ms around the block
    att = np.convolve(att, np.ones(5) / 5, mode="same")      # smooth (250 ms)
    tc = (st + 0.2 * SR) / SR
    g = 10 ** (-np.interp(np.arange(len(voice)) / SR, tc, att) / 20)
    print(f"speech-first safety: active on {np.mean(att > 0.5) * 100:.1f}% of blocks, max {att.max():.1f} dB")
    return g.astype(np.float32)


# ---------------------------------------------------------------------------
def main():
    t_all = time.time()
    tl = json.load(open(TIMELINE))
    dur = float(tl["duration"])
    n = int(round(dur * SR))
    voice = build_voice(tl, n)
    # voice peak control: transparent lookahead limiter, ceiling VOICE_PLR above dialogue loudness
    Lv0 = integrated(voice)
    vg, vgr = limiter_gain(voice, Lv0 + VOICE_PLR)
    voice *= vg
    print(f"voice peak limiter: ceiling {Lv0 + VOICE_PLR:.1f} dBTP, max GR {vgr:.1f} dB, "
          f"{np.mean(vg < 10 ** (-1 / 20)) * 100:.2f}% of samples reduced >1 dB")

    st = {k: np.load(os.path.join(WORK, f"{k}.npy"))[:n] for k in ("bed", "cues", "amb", "events")}
    for k in st:
        if len(st[k]) < n:
            st[k] = np.pad(st[k], (0, n - len(st[k])))

    # calibrate music against the dialogue: un-ducked bed sits MUSIC_REL LU under speech
    Lv = integrated(voice)
    Lb = integrated(st["bed"])
    g_music = 10 ** ((Lv + MUSIC_REL - Lb) / 20)
    print(f"voice {Lv:.1f} LUFS, raw bed {Lb:.1f} LUFS -> music gain {db(g_music):+.1f} dB")

    env, vis, merged = duck_curve(tl, n)
    bed_depth = DUCK["bed"] - (DUCK["bed"] - DUCK["bed_vision"]) * vis
    duck = lambda depth: (10 ** (-(depth * env) / 20)).astype(np.float32)
    music = g_music * (st["bed"] * duck(bed_depth) + st["cues"] * duck(DUCK["cues"]))
    sfx = g_music * (st["amb"] * duck(DUCK["amb"]) + st["events"] * duck(DUCK["events"]))
    del st

    # speech-first safety: wherever a cue/swell still crowds active speech, pull the background
    # down just enough (400 ms K-weighted blocks, smoothed, max 10 dB)
    sg = safety_gain(voice, music + sfx)
    music *= sg
    sfx *= sg
    mix = voice + music + sfx
    # two-pass normalisation: gain to target, then true-peak limit, re-measure, repeat
    gain = 10 ** ((TARGET_LUFS - integrated(mix)) / 20)
    for it in range(4):
        lg, gr = limiter_gain(mix * gain, LIMIT_AT)
        L = integrated(mix * gain * lg)
        print(f"  pass {it + 1}: gain {db(gain):+.2f} dB, limiter max GR {gr:.1f} dB, loudness {L:.2f} LUFS")
        if abs(L - TARGET_LUFS) < 0.05:
            break
        gain *= 10 ** ((TARGET_LUFS - L) / 20)
    g_all = (gain * lg).astype(np.float32)
    voice *= g_all
    music *= g_all
    sfx *= g_all
    mix = voice + music + sfx

    os.makedirs(OUT, exist_ok=True)
    for name, x in (("voice", voice), ("music", music), ("sfx", sfx), ("mix", mix)):
        write_wav(os.path.join(OUT, f"{name}.wav"), x)

    # ------------------------------------------------------------------ report
    rep = {}
    rep["integrated_lufs"] = integrated(mix)
    rep["true_peak_dbtp"] = true_peak(mix)
    rep["sample_peak_dbfs"] = float(db(np.abs(mix).max()))
    rep["clipped_samples"] = int(np.sum(np.abs(mix) >= 32767 / 32768))
    bg = music + sfx
    s, Lvb = block_loudness(voice)
    _, Lmb = block_loudness(bg)
    Lv_int = integrated(voice)
    speech = Lvb > Lv_int - 12
    margin = Lvb[speech] - Lmb[speech]
    rep["voice_minus_music_LU"] = {"median": float(np.median(margin)), "p5": float(np.percentile(margin, 5)),
                                   "p1": float(np.percentile(margin, 1)), "min": float(margin.min()),
                                   "share_below_10": float(np.mean(margin < 10))}
    # music in pauses (>= 1.5 s between speech)
    pauses = []
    for (a, b), (c, d) in zip(merged[:-1], merged[1:]):
        if c - b >= 1.5:
            pauses.append((b + 0.6, c - 0.1))
    pl = []
    for a, b in pauses:
        i, j = int(a * SR), int(b * SR)
        if j - i > SR * 0.4:
            pl.append(integrated(bg[i:j]) if j - i > SR * 0.4 else -70)
    pl = np.array([p for p in pl if p > -69])
    rep["music_in_pauses_LUFS"] = {"count": len(pauses), "median": float(np.median(pl)), "min": float(pl.min()), "max": float(pl.max())}
    rep["stem_lufs"] = {"voice": integrated(voice), "music": integrated(music), "sfx": integrated(sfx)}
    rep["duration_s"] = len(mix) / SR
    with open(os.path.join(WORK, "mix_report.json"), "w") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))
    # independent check with ffmpeg's loudnorm analyser
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", os.path.join(OUT, "mix.wav"), "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary", "-f", "null", "-"],
                       capture_output=True, text=True)
    print("\n".join(l for l in r.stderr.splitlines() if l.startswith(("Input", "Output"))))
    print(f"mix done in {time.time() - t_all:.0f}s")


if __name__ == "__main__":
    main()
