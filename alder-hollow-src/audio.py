import wave, numpy as np
from lib import *
SR = 44100
n = int((TOTAL + 0.5) * SR)
voice = np.zeros(n)
for i in range(13):
    with wave.open(f'line{i}.wav') as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
        sr = w.getframerate()
    xs = np.interp(np.arange(int(len(x) * SR / sr)) / SR * sr, np.arange(len(x)), x)
    s = int((T0[i] + LEAD[i]) * SR)
    voice[s:s + len(xs)] += xs
voice *= 0.9 / max(0.01, np.abs(voice).max())

# ambient music: slow pad chords + soft plucks
t = np.arange(n) / SR
chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (261.63, 329.63, 392.0), (196.0, 246.94, 293.66)]
music = np.zeros(n)
seg = 8.0
for i in range(int(TOTAL / seg) + 2):
    ch = chords[i % 4]
    a, b = int(i * seg * SR), min(n, int((i + 1) * seg * SR))
    if a >= n: break
    tt = t[a:b] - i * seg
    env = np.minimum(1, tt / 2.5) * np.minimum(1, (seg + 1 - tt) / 2.5)
    for f in ch:
        music[a:b] += env * (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2 * tt + 0.3) + 0.15 * np.sin(2 * np.pi * f * 3 * tt)) * (1 + 0.15 * np.sin(2 * np.pi * 0.2 * tt))
    # plucks
    for j, f in enumerate((ch[0] * 2, ch[1] * 2, ch[2] * 2, ch[1] * 2) * 2):
        st = int(j * 1.0 * SR)
        if a + st >= n: break
        L = min(int(2.5 * SR), n - a - st)
        tp = np.arange(L) / SR
        music[a + st:a + st + L] += 0.5 * np.sin(2 * np.pi * f * tp) * np.exp(-tp * 2.2) * min(1, 1)
music *= 1.0 / np.abs(music).max()
mfade = np.minimum(1, t / 3) * np.minimum(1, (TOTAL + 0.5 - t) / 3)
music *= mfade
# gentle ducking under the voice
env = np.abs(voice)
k = int(0.25 * SR)
env = np.convolve(env, np.ones(k) / k, mode='same')
duck = 1 - 0.55 * np.clip(env * 6, 0, 1)
mix = voice + music * 0.20 * duck
mix *= 0.92 / np.abs(mix).max()
pcm = (mix * 32767).astype(np.int16)
with wave.open('mix.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('audio ok', TOTAL)
