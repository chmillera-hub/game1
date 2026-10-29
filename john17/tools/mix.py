"""Mix narration and music, duck the music under speech, and mux with the video.

Usage: python tools/mix.py build/video.mp4 out.mp4   (run from the john17/ folder)
"""
import json, os, subprocess, sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

v_rms = np.sqrt(np.mean(voice[active > 0] ** 2))
voice *= 10 ** (-18 / 20) / v_rms              # speech at about -18 dBFS RMS
m_rms = np.sqrt(np.mean(music ** 2))
music *= 10 ** (-25 / 20) / m_rms              # bed at about -25 dBFS RMS before ducking
mix = music * duck[:, None] + voice[:, None]
mix /= max(1.0, np.abs(mix).max() / 0.95)
tmp = os.path.join(ROOT, "build", "mix.wav")
sf.write(tmp, mix, SR, subtype="PCM_24")

# Two-pass loudness normalisation to -14 LUFS / -1.5 dBTP, then mux with the picture.
probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
stats = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
      f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:offset={stats['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-i", tmp, "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-af", ln + ",aresample=48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", final],
               check=True)
print("wrote", final, "| input loudness", stats["input_i"], "LUFS")
