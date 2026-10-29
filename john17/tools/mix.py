"""Mix narration and music, duck the music under speech, and mux with the video.

Usage: python tools/mix.py build/video.mp4 out.mp4   (run from the john17/ folder)
"""
import json, os, subprocess, sys
import numpy as np
import soundfile as sf
from scipy.ndimage import minimum_filter1d
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def smooth_blocks(target, fall, rise):
    """One-pole smoothing with separate coefficients for falling and rising values."""
    out, s = np.empty_like(target), target[0]
    for i, v in enumerate(target):
        s = v + (s - v) * (fall if v < s else rise)
        out[i] = s
    return out


def compress(v, thr_db=-26.0, ratio=3.0, attack=0.005, release=0.12, blk=48):
    """Gentle RMS compressor for the speech track."""
    nb = len(v) // blk
    rms = np.sqrt((v[: nb * blk].reshape(nb, blk) ** 2).mean(axis=1) + 1e-12)
    gr = -np.maximum(0, 20 * np.log10(rms) - thr_db) * (1 - 1 / ratio)
    gr = smooth_blocks(gr, np.exp(-1 / (attack * 1000)), np.exp(-1 / (release * 1000)))
    g = 10 ** (np.interp(np.arange(len(v)), (np.arange(nb) + 0.5) * blk, gr) / 20)
    return (v * g).astype(np.float32)


def limit(x, thr_db=-2.5, release=0.06, look_blocks=3, blk=48):
    """Look-ahead peak limiter using 2x oversampled peaks (approximates true peak)."""
    over = np.stack([resample_poly(x[:, c], 2, 1) for c in range(x.shape[1])], axis=1)
    a = np.abs(over).max(axis=1)
    nb = len(a) // (2 * blk)
    pk = a[: nb * 2 * blk].reshape(nb, 2 * blk).max(axis=1)
    g = np.minimum(1.0, 10 ** (thr_db / 20) / np.maximum(pk, 1e-9))
    g = minimum_filter1d(g, size=2 * look_blocks + 1)
    g = smooth_blocks(g, 0.0, np.exp(-1 / (release * 1000)))
    gs = np.interp(np.arange(len(x)), (np.arange(nb) + 0.5) * blk, g)
    return (x * gs[:, None]).astype(np.float32)
video, final = sys.argv[1], sys.argv[2]
SR = 48000
voice, sr1 = sf.read(os.path.join(ROOT, "build", "voice.wav"), dtype="float32")
music, sr2 = sf.read(os.path.join(ROOT, "build", "music.wav"), dtype="float32")
assert sr1 == SR and sr2 == SR
n = max(len(voice), len(music))
voice = np.pad(voice, (0, n - len(voice)))
music = np.pad(music, ((0, n - len(music)), (0, 0)))

# Voice: clean up rumble, a touch of short room ambience so it sits in the scene.
voice = sosfilt(butter(2, 80, "high", fs=SR, output="sos"), voice).astype(np.float32)
ir_len = int(0.6 * SR)
t = np.arange(ir_len) / SR
ir = np.random.default_rng(5).standard_normal(ir_len).astype(np.float32) * np.exp(-t / 0.12)
ir = sosfilt(butter(2, [300, 6000], "band", fs=SR, output="sos"), ir)
ir /= np.sqrt((ir ** 2).sum())
room = fftconvolve(voice, ir)[:n].astype(np.float32)
voice = voice + 0.07 * room

# Speech envelope -> ducking gain for the music (about -7 dB under speech).
win = int(0.03 * SR)
power = np.convolve(voice ** 2, np.ones(win) / win, mode="same")
active = (np.sqrt(power) > 0.01).astype(np.float32)
env = np.zeros(n, np.float32)
a_att, a_rel = np.exp(-1 / (0.08 * SR)), np.exp(-1 / (0.7 * SR))
lvl = 0.0
step = 64
for i in range(0, n, step):
    target = active[i]
    lvl = target + (lvl - target) * (a_att if target > lvl else a_rel) ** step
    env[i:i + step] = lvl
duck = 1 - 0.55 * env

voice = compress(voice)
v_rms = np.sqrt(np.mean(voice[active > 0] ** 2))
voice *= 10 ** (-18 / 20) / v_rms              # speech at about -18 dBFS RMS
m_rms = np.sqrt(np.mean(music ** 2))
music *= 10 ** (-25 / 20) / m_rms              # bed at about -25 dBFS RMS before ducking
mix = music * duck[:, None] + voice[:, None]
tmp = os.path.join(ROOT, "build", "mix.wav")


def measure(x):
    sf.write(tmp, x, SR, subtype="FLOAT")
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    return float(st["input_i"]), float(st["input_tp"])


# Drive the mix into a look-ahead limiter so it reaches -14 LUFS with peaks held below -3 dBFS.
li0, _ = measure(mix)
pre = 10 ** ((-14.0 - li0) / 20)
limited = limit(mix * pre, -3.0)
red = 20 * np.log10(np.maximum(np.abs(limited).max(axis=1), 1e-9) / np.maximum(np.abs(mix * pre).max(axis=1), 1e-9))
loud = np.abs(mix * pre).max(axis=1) > 10 ** (-3.0 / 20)
print(f"limiter: {loud.mean() * 100:.2f}% of samples over threshold, median reduction there {np.median(red[loud]):.1f} dB, max {red.min():.1f} dB")
li, tp = measure(limited)
gain = min(-14.0 - li, -2.9 - tp)  # leaves room for AAC overshoot (about 1.4 dB here)
sf.write(tmp, limited * 10 ** (gain / 20), SR, subtype="PCM_24")
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-i", tmp, "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", final],
               check=True)
print(f"wrote {final} | mix {li0:.1f} LUFS -> {li + gain:.1f} LUFS, true peak {tp + gain:.1f} dBTP")
