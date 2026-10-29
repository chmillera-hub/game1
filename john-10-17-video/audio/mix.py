"""Mix narration over the score with sidechain ducking; normalize to -15 LUFS.
Usage: python3 -I audio/mix.py <narration.wav> <music.wav> <out.wav>
"""
import sys
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import butter, sosfilt

nar, sr = sf.read(sys.argv[1], dtype='float32')
mus, sr2 = sf.read(sys.argv[2], dtype='float32')
assert sr == sr2 == 48000
n = max(len(nar), len(mus))
nar = np.pad(nar, (0, n - len(nar))); mus = np.pad(mus, ((0, n - len(mus)), (0, 0)))
meter = pyln.Meter(sr)
# narration: clean low end, gentle presence, normalize
nar = sosfilt(butter(2, 75, 'high', fs=sr, output='sos'), nar)
nar = pyln.normalize.loudness(nar, meter.integrated_loudness(nar), -17.0)
# speech envelope -> ducking gain for the music
win = int(0.05 * sr)
rms = np.sqrt(np.convolve(nar ** 2, np.ones(win) / win, mode='same'))
active = (rms > 10 ** (-42 / 20)).astype(np.float32)
g = np.zeros(n, np.float32); att, rel = np.exp(-1 / (0.12 * sr)), np.exp(-1 / (0.9 * sr)); y = 0.0
for i in range(0, n, 64):  # block-wise smoothing for speed
    target = active[i:i + 64].max()
    c = att if target > y else rel
    y = target + (y - target) * c ** 64
    g[i:i + 64] = y
duck = 10 ** ((-9.5 * g) / 20)
mus = pyln.normalize.loudness(mus, meter.integrated_loudness(mus), -21.0)
mix = mus * duck[:, None] + np.stack([nar, nar], 1) * 0.98
mix = pyln.normalize.loudness(mix, meter.integrated_loudness(mix), -15.0)
peak = np.abs(mix).max()
if peak > 0.89:  # soft ceiling around -1 dBFS
    mix = np.tanh(mix / 0.89 * 1.0) * 0.89 if peak > 1.2 else mix * (0.89 / peak)
print('final LUFS %.1f peak %.2f dBFS' % (meter.integrated_loudness(mix), 20 * np.log10(np.abs(mix).max())))
sf.write(sys.argv[3], mix.astype(np.float32), sr, subtype='PCM_24')
