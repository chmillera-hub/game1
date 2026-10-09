"""Final stereo mix from build/timeline.json -> build/mix.wav (48 kHz float).

Buses
    VO     : every dialogue line, high-passed, a touch of room reverb, panned slightly
             toward the speaker (Rae left of center, Quill right).
    MUSIC  : cues with gain/fades from the timeline; ducked under dialogue.
    SFX    : effects with timeline gains; *_loop effects tile until their `end`.
Master: loudness-normalized to TARGET_LUFS, then a lookahead peak limiter.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import BUILD, MUSIC_DIR, SFX_DIR, SR, TIMELINE, VO_DIR  # noqa: E402

TARGET_LUFS = -15.0
CEILING_DB = -1.2
PAN = {"rae": -0.18, "quill": 0.18}
VO_GAIN_DB = {"rae": 0.0, "quill": -0.5}
# How much each music cue ducks (dB) while somebody is talking.
DUCK_DB = {"opening": 0, "lounge": 7, "symphony": 4, "alt_kazoo": 8, "alt_chip": 8, "alt_lofi": 8,
           "alt_theremin": 8, "alt_lullaby": 8, "coda": 6}
# Extra per-line gain tweaks (dB) for performance.
LINE_GAIN = {"r09": -9.0, "r15": -2.0, "q13": -1.0, "q14": -1.5, "r14": -1.0}


def db(x):
    return 10 ** (x / 20)


def load(path):
    x, sr = sf.read(path, always_2d=True)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr, axis=0)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x


def pan_mono(x, p):
    if x.ndim == 2:
        x = x.mean(axis=1)
    return np.stack([x * np.cos((p + 1) * np.pi / 4), x * np.sin((p + 1) * np.pi / 4)], axis=1) * np.sqrt(2)


def place(bus, x, start, gain=1.0):
    i = int(round(start * SR))
    if i < 0:
        x = x[-i:]
        i = 0
    j = min(len(bus), i + len(x))
    if j > i:
        bus[i:j] += x[: j - i] * gain


def fades(x, fi, fo):
    n = len(x)
    e = np.ones(n)
    a, b = int(fi * SR), int(fo * SR)
    if a > 0:
        e[: min(a, n)] = np.linspace(0, 1, a)[: min(a, n)]
    if b > 0:
        b = min(b, n)
        e[-b:] = np.minimum(e[-b:], np.linspace(1, 0, b))
    return x * e[:, None]


def room_ir(dur=0.45, seed=3):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    irs = []
    for _ in range(2):
        ir = rng.standard_normal(n) * np.exp(-t / (dur / 6.5))
        sos = signal.butter(2, 5000, btype="low", fs=SR, output="sos")
        ir = signal.sosfilt(sos, ir)
        ir[: int(0.006 * SR)] = 0  # pre-delay
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return irs


def limiter(x, ceiling_db=CEILING_DB, block=48, look_blocks=4, release_ms=150.0):
    """Lookahead peak limiter working on 1 ms blocks: instant attack (ahead of the
    peak), exponential release, gain interpolated per sample."""
    ceil = db(ceiling_db)
    n = len(x)
    nb = (n + block - 1) // block
    pk = np.pad(np.max(np.abs(x), axis=1), (0, nb * block - n)).reshape(nb, block).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    from scipy.ndimage import minimum_filter1d
    # each block's gain must already be low enough look_blocks ahead of a peak
    need = minimum_filter1d(need, size=2 * look_blocks + 1)
    rel = np.exp(-block / (release_ms * SR / 1000))
    g = np.empty(nb)
    cur = 1.0
    for i in range(nb):
        cur = need[i] if need[i] < cur else need[i] + (cur - need[i]) * rel
        g[i] = cur
    gs = np.interp(np.arange(n), np.arange(nb) * block + block / 2, g)
    y = x * gs[:, None]
    # safety clip at the ceiling (only catches inter-block slivers)
    return np.clip(y, -ceil, ceil)


def main():
    tl = json.loads(Path(TIMELINE).read_text())
    dur = tl["duration"] + 0.5
    n = int(dur * SR)
    vo = np.zeros((n, 2))
    music = np.zeros((n, 2))
    sfx = np.zeros((n, 2))

    # ---------------- VO
    hp = signal.butter(2, 85, btype="high", fs=SR, output="sos")
    activity = np.zeros(n)
    for ln in tl["lines"]:
        x = load(VO_DIR / f"{ln['id']}.wav").mean(axis=1)
        x = signal.sosfilt(hp, x)
        g = db(VO_GAIN_DB[ln["char"]] + LINE_GAIN.get(ln["id"], 0.0))
        place(vo, pan_mono(x, PAN[ln["char"]]), ln["start"], g)
        a, b = int(ln["start"] * SR), int(ln["end"] * SR)
        if ln["id"] != "r09":
            activity[a:b] = 1.0
    ir_l, ir_r = room_ir()
    wet = np.stack([signal.fftconvolve(vo[:, 0], ir_l)[:n], signal.fftconvolve(vo[:, 1], ir_r)[:n]], axis=1)
    vo = vo + wet * 0.13

    # duck envelope: attack 60 ms, release 350 ms (smoothed activity)
    att = np.exp(-1 / (0.06 * SR))
    rel = np.exp(-1 / (0.35 * SR))
    up = signal.lfilter([1 - att], [1, -att], activity)
    down = signal.lfilter([1 - rel], [1, -rel], activity)
    duck = np.clip(np.maximum(up, down) * 1.25, 0, 1)

    # ---------------- MUSIC
    for m in tl["music"]:
        p = MUSIC_DIR / f"{m['cue']}.wav"
        if not p.exists():
            print("missing music", p)
            continue
        x = load(p)
        length = m["end"] - m["start"]
        x = x[: int(length * SR)]
        x = fades(x, m.get("fade_in", 0.0), m.get("fade_out", 0.0))
        i = int(m["start"] * SR)
        seg = duck[i:i + len(x)]
        dd = DUCK_DB.get(m["cue"], 6)
        x = x * db(-dd * seg)[:, None] if len(seg) == len(x) else x
        place(music, x, m["start"], db(m["gain_db"]))

    # ---------------- SFX
    for s in tl["sfx"]:
        p = SFX_DIR / f"{s['name']}.wav"
        if not p.exists():
            print("missing sfx", p)
            continue
        x = load(p)
        if s["name"].endswith("_loop"):
            length = s["end"] - s["start"]
            reps = int(np.ceil(length * SR / len(x))) + 1
            x = np.tile(x, (reps, 1))[: int(length * SR)]
            x = fades(x, 1.0, 1.5)
        place(sfx, x, s["start"], db(s["gain_db"]))

    raw = vo + music + sfx
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(raw)
    gain_db = TARGET_LUFS - lufs
    for _ in range(4):  # limiting lowers loudness a little; converge on the target
        mix = limiter(raw * db(gain_db))
        err = TARGET_LUFS - meter.integrated_loudness(mix)
        if abs(err) < 0.2:
            break
        gain_db += err
    out = BUILD / "mix.wav"
    sf.write(out, mix.astype(np.float32), SR, subtype="FLOAT")
    final = meter.integrated_loudness(mix)
    print(f"mix: {dur:.2f}s  pre {lufs:.1f} LUFS -> {final:.1f} LUFS, peak {20*np.log10(np.max(np.abs(mix))):.2f} dBFS")
    # stems for QA
    for name, bus in (("vo", vo), ("music", music), ("sfx", sfx)):
        print(f"  {name:5s} LUFS {meter.integrated_loudness(bus + 1e-9):6.1f}")


if __name__ == "__main__":
    main()
