#!/usr/bin/env python3
"""Narrator treatment + final mix for "Nursery Rhymes, Examined".

Inputs : build/timeline.json, build/tts/beat_NNNN.wav (24 kHz mono, one per speech beat),
         build/audio/work/{bed,song,cues,amb,events}.npy (from audio/score.py, 48 kHz float32)
Outputs: build/audio/voice.wav, music.wav, sfx.wav, mix.wav (48 kHz mono 16-bit, exactly
         timeline.duration long). Stems are the ducked, gain-matched layers as they sit in the
         mix (voice + music + sfx == mix, the final limiter gain is applied to all three).
         music = bed + song + cues, sfx = amb + events.

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
LIMIT_AT = -2.0           # limiter ceiling on the 4x oversampled signal (TP spec -1.5, margin for codec)
VOICE_PLR = 13.0          # voice peak ceiling above its integrated loudness (dB)
SAFETY_MARGIN = 11.0      # background kept >= this many LU under active speech (spec: >= 10)

# un-ducked level of each bus relative to the narrator's integrated loudness (LU), measured on
# the bus's own active (non-silent) material
REL = {"bed": -10.5, "song": -9.0, "amb": -15.0}
# duck depth (dB) while the narrator speaks
DUCK = {"bed": 9.0, "cues": 7.0, "song": 6.0, "amb": 3.0, "events": 2.0}

# ---------------------------------------------------------------------------
# narrator: -1 semitone, formants preserved; warmth, gentle compression, very subtle room
# ---------------------------------------------------------------------------
PITCH = 2 ** (-1 / 12)
VOICE_AF = ",".join([
    f"rubberband=pitch={PITCH:.6f}:formant=preserved:transients=smooth:window=standard:pitchq=quality",
    "aresample=48000:resampler=soxr",
    "highpass=f=55:poles=2",
    "lowshelf=f=170:g=1.8",                     # low-end warmth
    "equalizer=f=330:t=q:w=1.1:g=-1.2",         # keep the warmth from getting boxy
    "equalizer=f=3000:t=q:w=1.4:g=1.0",         # presence
    "highshelf=f=7500:g=-1.5",                  # soften TTS sibilance for the codec
    "acompressor=threshold=0.07:ratio=2.0:attack=12:release=200:knee=4:makeup=1",
])


def make_ir(dur, t60, lp_a, lp_b, predelay, seed):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = r.standard_normal(n)
    sa = signal.butter(2, lp_a, "low", fs=SR, output="sos")
    sb = signal.butter(2, lp_b, "low", fs=SR, output="sos")
    x = np.linspace(0, 1, n) ** 0.6
    ir = (signal.sosfilt(sa, nz) * (1 - x) + signal.sosfilt(sb, nz) * x) * 10 ** (-3 * t / t60)
    ir[:240] *= np.linspace(0, 1, 240)
    ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
    ir = signal.sosfilt(signal.butter(2, 200, "high", fs=SR, output="sos"), ir)
    return (ir / np.sqrt(np.sum(ir ** 2))).astype(np.float32)


ROOM = make_ir(0.9, 0.55, 5500, 2000, 0.012, 21)   # small, dark documentary booth/room
ROOM_WET = 0.075

# ---------------------------------------------------------------------------
# loudness tools (ITU-R BS.1770-4) and IO
# ---------------------------------------------------------------------------
K1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
K2 = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def kweight(x):
    return signal.lfilter(*K2, signal.lfilter(*K1, x.astype(np.float64)))


def block_loudness(x, block=0.4, hop=0.1):
    y = kweight(x)
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


def oversampled_peaks(x, chunk=SR * 20):
    out = np.empty(len(x), np.float32)
    for i in range(0, len(x), chunk):
        a = max(0, i - 64)
        b = min(len(x), i + chunk + 64)
        y = np.abs(signal.resample_poly(x[a:b].astype(np.float64), 4, 1)).reshape(-1, 4).max(1)
        out[i:min(len(x), i + chunk)] = y[i - a:i - a + min(chunk, len(x) - i)]
    return np.maximum(out, np.abs(x))


def true_peak(x):
    return float(db(oversampled_peaks(x).max()))


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
    src = os.path.join(TTS, "beat_%04d.wav" % b["id"])
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-af", VOICE_AF, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, check=True, capture_output=True).stdout, np.float32).astype(np.float64)
    # partial dialogue-level normalisation on active speech so beats sit evenly
    y = kweight(x)
    fr = y[: len(y) // 480 * 480].reshape(-1, 480)
    e = (fr ** 2).mean(1)
    act = e > e.max() * 10 ** (-30 / 10)
    lev = -0.691 + 10 * np.log10(e[act].mean() + 1e-20)
    g = float(np.clip(-24.0 - lev, -8, 8))
    x = x * 10 ** (g / 20)
    x = np.concatenate([x, np.zeros(int(0.9 * SR))])
    x = x + ROOM_WET * signal.oaconvolve(x, ROOM)[: len(x)]
    nz = np.nonzero(np.abs(x) > 1e-5)[0]
    x = x[: (nz[-1] + 1) if len(nz) else len(x)]
    return b, x.astype(np.float32), g


def build_voice(tl, n):
    beats = [b for b in tl["beats"] if b["kind"] == "speech"]
    voice = np.zeros(n, np.float32)
    gains = []
    missing = []
    t0 = time.time()
    beats_ok = [b for b in beats if os.path.exists(os.path.join(TTS, "beat_%04d.wav" % b["id"]))]
    missing = [b["id"] for b in beats if b not in beats_ok]
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        for b, x, g in ex.map(process_beat, beats_ok):
            i0 = int(round(b["start"] * SR))
            m = min(len(x), n - i0)
            voice[i0:i0 + m] += x[:m]
            gains.append(g)
    print(f"voice: {len(beats_ok)} beats processed in {time.time() - t0:.0f}s "
          f"(pitch {12 * np.log2(PITCH):+.1f} st, formant-preserved); level trims {np.min(gains):+.1f}..{np.max(gains):+.1f} dB")
    if missing:
        print("  WARNING missing tts for beats", missing)
    return voice


# ---------------------------------------------------------------------------
# ducking + safety + limiter
# ---------------------------------------------------------------------------
def duck_curve(tl, n, CR=200):
    nc = int(n / SR * CR) + 2
    tgt = np.zeros(nc)
    sp = sorted((b["start"], b["end"]) for b in tl["beats"] if b["kind"] == "speech")
    merged = []
    for s, e in sp:
        if merged and s - merged[-1][1] < 1.1:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    for s, e in merged:
        tgt[int((s - 0.30) * CR):int((e + 0.25) * CR)] = 1.0
    a_att = 1 - np.exp(-1 / (0.10 * CR))
    a_rel = 1 - np.exp(-1 / (0.80 * CR))
    env = np.zeros(nc)
    v = 0.0
    for i in range(nc):
        t = tgt[i]
        v += (t - v) * (a_att if t > v else a_rel)
        env[i] = v
    env = ndimage.uniform_filter1d(env, int(0.05 * CR))
    return np.interp(np.arange(n) / SR, np.arange(nc) / CR, env).astype(np.float32), merged


def limiter_gain(x, ceil_db):
    ceil = 10 ** (ceil_db / 20)
    pk = oversampled_peaks(x)
    B = 48
    nb = len(x) // B + 1
    pb = np.zeros(nb * B, np.float32)
    pb[: len(pk)] = pk
    pb = pb.reshape(nb, B).max(1)
    need = np.minimum(1.0, ceil / np.maximum(pb, 1e-9))
    need = ndimage.minimum_filter1d(need, size=5)
    g = np.empty(nb)
    cur = 1.0
    rel = 1 - np.exp(-1 / (0.12 * SR / B))
    for i in range(nb):
        r = need[i]
        cur = r if r < cur else cur + (r - cur) * rel
        g[i] = cur
    g = ndimage.minimum_filter1d(g, size=3)
    gs = np.interp(np.arange(len(x)), (np.arange(nb) + 0.5) * B, g).astype(np.float32)
    return gs, float(db(g.min()))


def safety_gain(voice, bg, hop=0.05):
    st, Lv = block_loudness(voice, 0.4, hop)
    _, Lb = block_loudness(bg, 0.4, hop)
    Li = integrated(voice)
    active = Lv > Li - 12
    att = np.where(active, np.clip(Lb - (Lv - SAFETY_MARGIN), 0, 12), 0.0)
    att = ndimage.maximum_filter1d(att, size=11)              # hold +-250 ms
    att = np.convolve(att, np.ones(9) / 9, mode="same")       # smooth (450 ms): no syllable pumping
    tc = (st + 0.2 * SR) / SR
    g = 10 ** (-np.interp(np.arange(len(voice)) / SR, tc, att) / 20)
    print(f"speech-first safety: active on {np.mean(att > 0.5) * 100:.1f}% of blocks, max {att.max():.1f} dB")
    return g.astype(np.float32)


def active_loudness(x):
    """integrated loudness of the non-silent part of a bus"""
    nz = np.abs(x) > 1e-4
    nz = ndimage.maximum_filter1d(nz.astype(np.uint8), SR // 2) > 0
    return integrated(x[nz]) if nz.sum() > SR else -70.0


# ---------------------------------------------------------------------------
def main():
    t_all = time.time()
    tl = json.load(open(TIMELINE))
    dur = float(tl["duration"])
    n = int(round(dur * SR))
    voice = build_voice(tl, n)
    Lv0 = integrated(voice)
    vg, vgr = limiter_gain(voice, Lv0 + VOICE_PLR)
    voice *= vg
    print(f"voice peak control: ceiling {Lv0 + VOICE_PLR:.1f} dBTP, max GR {vgr:.1f} dB")
    Lv = integrated(voice)

    st = {}
    for k in ("bed", "song", "cues", "amb", "events"):
        x = np.load(os.path.join(WORK, f"{k}.npy"))[:n]
        st[k] = np.pad(x, (0, n - len(x))) if len(x) < n else x
    g = {}
    for k in ("bed", "song", "amb"):
        La = active_loudness(st[k])
        g[k] = 10 ** ((Lv + REL[k] - La) / 20)
        print(f"  {k:5s}: active loudness {La:6.1f} LUFS -> gain {db(g[k]):+6.1f} dB (target {REL[k]:+.1f} LU vs voice)")
    g["cues"] = g["bed"]
    g["events"] = g["amb"]

    env, merged = duck_curve(tl, n)
    duck = lambda k: (10 ** (-(DUCK[k] * env) / 20)).astype(np.float32)
    lay = {k: g[k] * st[k] * duck(k) for k in st}
    del st
    music = lay["bed"] + lay["song"] + lay["cues"]
    sfx = lay["amb"] + lay["events"]
    sg = safety_gain(voice, music + sfx)
    music *= sg
    sfx *= sg
    mix = voice + music + sfx
    gain = 10 ** ((TARGET_LUFS - integrated(mix)) / 20)
    for it in range(5):
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
    rep = {"duration_s": len(mix) / SR, "integrated_lufs": integrated(mix), "true_peak_dbtp": true_peak(mix),
           "sample_peak_dbfs": float(db(np.abs(mix).max()))}
    bg = music + sfx
    s, Lvb = block_loudness(voice)
    _, Lmb = block_loudness(music)
    _, Lbb = block_loudness(bg)
    speech = Lvb > integrated(voice) - 12
    for key, Lx in (("voice_minus_music_LU", Lmb), ("voice_minus_music+sfx_LU", Lbb)):
        m = Lvb[speech] - Lx[speech]
        rep[key] = {"median": float(np.median(m)), "p5": float(np.percentile(m, 5)), "p1": float(np.percentile(m, 1)),
                    "min": float(m.min()), "share_below_10": float(np.mean(m < 10))}
    rep["stem_lufs"] = {"voice": integrated(voice), "music": integrated(music), "sfx": integrated(sfx)}
    se = float(tl["songEnd"])

    def win(x, a, b):
        return integrated(x[int(a * SR):int(b * SR)])
    rep["checks"] = {
        "first_second_mix_LUFS": win(mix, 0, 1.0),
        "first_100ms_rms_dBFS": float(db(np.sqrt(np.mean(mix[:4800] ** 2)))),
        "song_last_second_music_LUFS": win(music, se - 1.0, se),
        "after_cut_music_LUFS(+0.5..+2.5s)": win(music, se + 0.5, se + 2.5),
        "after_cut_sfx_LUFS(+0.5..+2.5s)": win(sfx, se + 0.5, se + 2.5),
        "after_cut_mix_LUFS(+0.5..+2.5s)": win(mix, se + 0.5, se + 2.5),
        "last_5s_mix_LUFS": win(mix, dur - 5.0, dur),
        "last_0.5s_rms_dBFS": float(db(np.sqrt(np.mean(mix[-SR // 2:] ** 2)))),
    }
    # music level right before vs right after the cut, 50 ms resolution
    a = int((se - 0.3) * SR)
    rms = [float(db(np.sqrt(np.mean((music + 0 * sfx)[a + i * 2400:a + (i + 1) * 2400] ** 2)))) for i in range(16)]
    rep["checks"]["music_rms_50ms_from_songEnd-0.3s"] = [round(r, 1) for r in rms]
    with open(os.path.join(WORK, "mix_report.json"), "w") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", os.path.join(OUT, "mix.wav"), "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary", "-f", "null", "-"],
                       capture_output=True, text=True)
    print("ffmpeg loudnorm analysis:\n" + "\n".join(l for l in r.stderr.splitlines() if l.startswith(("Input", "Output"))))
    print(f"mix done in {time.time() - t_all:.0f}s")


if __name__ == "__main__":
    main()
