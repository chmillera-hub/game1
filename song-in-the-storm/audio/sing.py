import numpy as np, pyworld as pw, soundfile as sf
from kokoro_onnx import Kokoro
SR = 24000
_k = None
def tts(text, voice, speed=1.0, lang="en-us"):
    global _k
    if _k is None:
        _k = Kokoro("/tmp/claude-0/kokoro/kokoro-v1.0.onnx", "/tmp/claude-0/kokoro/voices-v1.0.bin")
    s, sr = _k.create(text, voice=voice, speed=speed, lang=lang)
    assert sr == SR
    return s.astype(np.float64)

def midi_hz(m): return 440.0 * 2 ** ((m - 69) / 12)

def sing_word(word, notes, durs, voice="af_heart", beat=0.909, fp=5.0, rng=None):
    """Return (audio, lead) where lead = seconds of consonant onset before the beat."""
    rng = rng or np.random.default_rng(0)
    x = tts(word, voice, speed=0.85)
    # trim silence
    a = np.abs(x); thr = a.max() * 0.02
    idx = np.where(a > thr)[0]
    x = x[max(0, idx[0] - 240): idx[-1] + 480]
    f0, t = pw.harvest(x, SR, frame_period=fp, f0_floor=70, f0_ceil=600)
    sp = pw.cheaptrick(x, f0, t, SR)
    ap = pw.d4c(x, f0, t, SR)
    n = len(f0)
    voiced = np.where(f0 > 0)[0]
    if len(voiced) == 0:
        v0, v1 = n // 3, 2 * n // 3
    else:
        v0, v1 = voiced[0], voiced[-1] + 1
    onset = v0; coda = min(n - v1, int(0.12 * 1000 / fp))
    total = sum(durs) * beat
    target_frames = int(total * 1000 / fp)
    core_frames = max(4, target_frames - coda)
    # build new frame index mapping: onset frames natural, core stretched, coda natural
    src = list(range(0, onset))
    core = np.linspace(v0, v1 - 1, core_frames)
    src += list(core)
    src += list(range(v1, v1 + coda))
    src = np.array(src)
    lo = np.floor(src).astype(int); hi = np.minimum(lo + 1, n - 1); fr = (src - lo)[:, None]
    lsp = np.log(sp + 1e-12)
    sp2 = np.exp(lsp[lo] * (1 - fr) + lsp[hi] * fr)
    ap2 = ap[lo] * (1 - fr) + ap[hi] * fr
    # f0 contour over core
    m = len(src)
    f2 = np.zeros(m)
    times = np.arange(core_frames) * fp / 1000.0
    bounds = np.cumsum([0] + [d * beat for d in durs])
    cents = np.zeros(core_frames)
    for i in range(len(notes)):
        sel = (times >= bounds[i]) & (times < bounds[i + 1] + 1e-9)
        cents[sel] = notes[i] * 100
    cents[times >= bounds[-1]] = notes[-1] * 100
    # portamento smoothing
    k = int(0.06 * 1000 / fp)
    ker = np.ones(k) / k
    cents = np.convolve(np.pad(cents, (k, k), mode="edge"), ker, mode="same")[k:-k]
    # vibrato (delayed per note), slight scoop at note start
    vib = np.zeros(core_frames)
    for i in range(len(notes)):
        sel = (times >= bounds[i]) & (times < bounds[i + 1])
        lt = times[sel] - bounds[i]
        depth = np.clip((lt - 0.25) / 0.4, 0, 1) * 28
        vib[sel] = depth * np.sin(2 * np.pi * 5.3 * lt + rng.uniform(0, 6))
    jitter = np.convolve(rng.normal(0, 6, core_frames), np.ones(8) / 8, mode="same")
    hz = 440 * 2 ** ((cents + vib + jitter) / 100 / 12 - 69 / 12)
    f2[onset:onset + core_frames] = hz
    # make onset voiced frames (rare) unvoiced; keep coda unvoiced
    ap2[onset:onset + core_frames] = np.minimum(ap2[onset:onset + core_frames], 0.6)
    y = pw.synthesize(np.ascontiguousarray(f2), np.ascontiguousarray(sp2), np.ascontiguousarray(ap2), SR, fp)
    # gentle amplitude envelope on sustained part
    env = np.ones(len(y))
    rel = int(0.15 * SR)
    env[-rel:] = np.linspace(1, 0, rel)
    y *= env
    lead = onset * fp / 1000.0
    return y, lead

if __name__ == "__main__":
    beat = 0.909
    line = [("Cold",[76],[2]),("is",[74],[1]),("the",[72],[1]),("rain",[71],[2]),("on",[69],[1]),("the",[71],[1]),("street",[72],[2]),("where",[71],[1]),("I",[69],[1]),("stay",[64],[4])]
    out = np.zeros(int(SR * 18))
    t = 0.5
    for w, ns, ds in line:
        y, lead = sing_word(w, [n - 12 + 12 for n in ns], ds)
        s = int((t - lead) * SR)
        out[s:s + len(y)] += y[: len(out) - s]
        t += sum(ds) * beat
    out /= np.abs(out).max() * 1.1
    sf.write("sing_test.wav", out, SR)
    f0, tt = pw.harvest(out, SR, frame_period=50)
    print(np.round(12*np.log2(np.maximum(f0,1)/440)+69,1)[::4])
