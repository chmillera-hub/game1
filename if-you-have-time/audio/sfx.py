"""Synthesize every sound effect with numpy -> build/sfx/<name>.wav (48 kHz stereo float).

All effects are procedural: filtered noise, swept sines, bell partials and simple
formant filters for breaths. Levels are normalized per effect (peak -3 dBFS); the
mixer sets the final gain from the timeline.
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SFX_DIR, SR  # noqa: E402

RNG = np.random.default_rng(7)


# ----------------------------------------------------------------------------- building blocks

def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def noise(dur, color="white"):
    n = RNG.standard_normal(int(dur * SR))
    if color == "pink":
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]
        n = signal.lfilter(b, a, n) * 8
    elif color == "brown":
        n = np.cumsum(n)
        n = signal.lfilter([1, -1], [1, -0.995], n) * 0.05
    return n


def bp(x, lo, hi, order=2):
    lo, hi = max(lo, 10), min(hi, SR / 2 - 100)
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    sos = signal.butter(order, min(f, SR / 2 - 100), btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, f, order=2):
    sos = signal.butter(order, f, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def sweep_bp(x, f0, f1, q=2.0, curve="exp", block=256):
    """Time-varying band-pass (blockwise biquad, state carried) from f0 to f1."""
    y = np.zeros_like(x)
    n = len(x)
    zi = np.zeros(2)
    for i in range(0, n, block):
        frac = i / max(1, n - 1)
        f = f0 * (f1 / f0) ** frac if curve == "exp" else f0 + (f1 - f0) * frac
        w0 = 2 * np.pi * f / SR
        alpha = np.sin(w0) / (2 * q)
        b = np.array([alpha, 0, -alpha])
        a = np.array([1 + alpha, -2 * np.cos(w0), 1 - alpha])
        seg, zi = signal.lfilter(b / a[0], a / a[0], x[i:i + block], zi=zi)
        y[i:i + block] = seg
    return y


def env_adsr(n, a, d, s, r, sustain_level=0.7):
    """Envelope with times in seconds; total length n samples."""
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    S = max(0, n - A - D - R)
    e = np.concatenate([np.linspace(0, 1, A, endpoint=False) if A else [],
                        np.linspace(1, sustain_level, D, endpoint=False) if D else [],
                        np.full(S, sustain_level),
                        np.linspace(sustain_level, 0, R) if R else []])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def exp_decay(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def bell(freq, dur, tau=0.6, partials=((1, 1.0), (2.76, 0.35), (5.4, 0.12), (8.93, 0.05))):
    t = t_axis(dur)
    out = np.zeros_like(t)
    for ratio, amp in partials:
        out += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / (tau / ratio ** 0.5))
    att = np.minimum(1, t / 0.003)
    return out * att


def formant(x, vowel="ah", strength=1.0):
    F = {"ah": [(800, 80), (1150, 90), (2900, 120)], "eh": [(500, 70), (1700, 100), (2500, 120)],
         "oo": [(350, 60), (800, 80), (2400, 100)], "hh": [(1200, 300), (2500, 400), (3800, 500)]}[vowel]
    y = np.zeros_like(x)
    for f, bw in F:
        y += bp(x, f - bw * 2, f + bw * 2)
    return x * (1 - strength) + y * strength


def stereo(x, pan=0.0, width=0.0, delay_ms=0.0):
    """Mono -> stereo with constant-power pan; width adds a small decorrelated delay."""
    l = x * np.cos((pan + 1) * np.pi / 4)
    r = x * np.sin((pan + 1) * np.pi / 4)
    if width or delay_ms:
        d = int((delay_ms or 7.0) * SR / 1000)
        r2 = np.concatenate([np.zeros(d), r[:-d]]) if d else r
        r = r * (1 - width) + r2 * width
    return np.stack([l, r], axis=1)


def room(x, dur=0.6, wet=0.2, damp=6000):
    """Tiny synthetic room reverb on a stereo or mono signal."""
    n = int(dur * SR)
    ir_l = RNG.standard_normal(n) * exp_decay(n, dur / 6)
    ir_r = RNG.standard_normal(n) * exp_decay(n, dur / 6)
    ir_l, ir_r = lp(ir_l, damp), lp(ir_r, damp)
    ir_l /= np.sqrt(np.sum(ir_l ** 2)); ir_r /= np.sqrt(np.sum(ir_r ** 2))
    if x.ndim == 1:
        x = stereo(x)
    tail = int(dur * SR)
    xp = np.pad(x, ((0, tail), (0, 0)))
    wl = signal.fftconvolve(xp[:, 0], ir_l)[: len(xp)]
    wr = signal.fftconvolve(xp[:, 1], ir_r)[: len(xp)]
    return xp * (1 - wet) + np.stack([wl, wr], axis=1) * wet


def fade(x, fi=0.005, fo=0.02):
    n = len(x)
    e = np.ones(n)
    a, b = int(fi * SR), int(fo * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if b:
        e[-b:] = np.minimum(e[-b:], np.linspace(1, 0, b))
    return x * (e[:, None] if x.ndim == 2 else e)


def norm(x, peak_db=-3.0):
    p = np.max(np.abs(x)) + 1e-12
    return x / p * 10 ** (peak_db / 20)


# ----------------------------------------------------------------------------- effects

def space_rumble():
    d = 17.0
    t = t_axis(d)
    x = lp(noise(d, "brown"), 140, 4) * 1.0
    x += 0.25 * np.sin(2 * np.pi * 41 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t))
    air = bp(noise(d, "pink"), 300, 1400) * 0.05
    x = x + air
    e = np.minimum(1, t / 4.0) * np.minimum(1, (d - t) / 3.0)
    return fade(stereo(x * e, 0, width=0.6, delay_ms=13), 0.5, 1.0)


def whoosh_dive():
    d = 2.8
    t = t_axis(d)
    n = noise(d, "pink")
    x = sweep_bp(n, 180, 5200, q=1.4)
    # swell that peaks ~2.2 s (flash at ~15.4 in the film) then drops fast
    e = np.where(t < 2.2, (t / 2.2) ** 2.4, np.exp(-(t - 2.2) / 0.12))
    shimmer = sum(np.sin(2 * np.pi * f * t) for f in (1760, 2217, 2637)) * 0.04 * np.clip((t - 1.4) / 0.8, 0, 1)
    x = x * e + shimmer * e
    l = x
    r = np.concatenate([np.zeros(240), x[:-240]])
    return fade(np.stack([l, r], 1), 0.01, 0.15)


def ship_hum_loop():
    d = 8.0  # every component completes an integer number of cycles -> seamless
    t = t_axis(d)
    x = (0.5 * np.sin(2 * np.pi * 55 * t) + 0.22 * np.sin(2 * np.pi * 110 * t + 0.3)
         + 0.08 * np.sin(2 * np.pi * 165 * t) + 0.12 * np.sin(2 * np.pi * 55.125 * t))
    x *= 1 + 0.08 * np.sin(2 * np.pi * 0.25 * t)
    air = lp(hp(noise(d + 1.0, "pink"), 120), 900) * 0.12
    # loop the noise by crossfading its tail into its head
    n1 = int(d * SR)
    xf = SR
    a = air[:n1].copy()
    ramp = np.linspace(0, 1, xf)
    a[:xf] = air[n1:n1 + xf] * (1 - ramp) + air[:xf] * ramp
    x = x + a
    # stereo width with a CIRCULAR 11 ms delay so the right channel wraps too (a zero-padded delay left a
    # 0.088 step at the loop point, ticking every 8 s in the mix)
    g = np.cos(np.pi / 4)                                   # centre pan, as stereo(x, 0, ...)
    r = x * g
    return np.stack([x * g, r * 0.5 + np.roll(r, int(11 * SR / 1000)) * 0.5], axis=1)


def _pneumatic(d, rev=False):
    t = t_axis(d)
    n = noise(d, "white")
    hiss = sweep_bp(n, 2400, 900, q=1.2) if not rev else sweep_bp(n, 900, 2400, q=1.2)
    e = env_adsr(len(t), 0.02, 0.25, 0.35, d - 0.4, 0.5)
    slide = lp(noise(d, "pink"), 500) * 0.4 * e
    thunk_t = 0.0 if not rev else d - 0.18
    k = np.zeros_like(t)
    i = int(thunk_t * SR)
    tn = t[: int(0.18 * SR)]
    th = np.sin(2 * np.pi * (90 - 40 * tn / 0.18) * tn) * np.exp(-tn / 0.04)
    k[i: i + len(th)] = th[: len(k) - i]
    x = hiss * e * 0.8 + slide + k * 0.9
    return x


def door_open():
    x = _pneumatic(0.95)
    return fade(room(stereo(x, -0.45, 0.3), 0.5, 0.18), 0.003, 0.05)


def door_close():
    x = _pneumatic(0.85, rev=True)
    return fade(room(stereo(x, -0.45, 0.3), 0.5, 0.18), 0.003, 0.05)


def footsteps_4():
    d = 2.8
    out = np.zeros(int(d * SR))
    times = [0.0, 0.62, 1.3, 1.95]
    for k, st in enumerate(times):
        n = int(0.22 * SR)
        tt = np.arange(n) / SR
        thump = np.sin(2 * np.pi * (110 - 50 * tt / 0.22) * tt) * np.exp(-tt / 0.03)
        scuff = bp(noise(0.22), 900, 4000) * np.exp(-tt / 0.05) * 0.35
        s = (thump + scuff) * (0.8 + 0.2 * (k % 2))
        i = int(st * SR)
        out[i:i + n] += s[: len(out) - i]
    pan = np.linspace(-0.6, -0.1, len(out))
    st_ = np.stack([out * np.cos((pan + 1) * np.pi / 4), out * np.sin((pan + 1) * np.pi / 4)], 1)
    return fade(room(st_, 0.4, 0.15), 0.002, 0.05)


def bench_sit():
    d = 0.7
    t = t_axis(d)
    thud = np.sin(2 * np.pi * (75 - 25 * t / d) * t) * np.exp(-t / 0.07)
    fabric = bp(noise(d), 300, 2500) * np.exp(-t / 0.12) * 0.3
    creak = np.sin(2 * np.pi * 340 * t + 2 * np.sin(2 * np.pi * 9 * t)) * np.exp(-((t - 0.18) / 0.08) ** 2) * 0.05
    return fade(room(stereo(thud + fabric + creak, -0.25), 0.4, 0.12), 0.002, 0.05)


def _breath(d, shape, vowel="ah", lo=400, hi=5000):
    n = noise(d, "pink")
    x = formant(bp(n, lo, hi), vowel, 0.85)
    return x * shape


def sigh_breath():
    d = 1.6
    t = t_axis(d)
    inhale = np.exp(-((t - 0.25) / 0.14) ** 2) * 0.35
    exhale = np.clip((t - 0.45) / 0.12, 0, 1) * np.exp(-np.clip(t - 0.57, 0, None) / 0.38)
    x = _breath(d, inhale, "hh") + _breath(d, exhale, "ah", 250, 3500) * 1.1
    return fade(room(stereo(x, -0.2), 0.4, 0.15), 0.01, 0.1)


def sip():
    d = 0.7
    t = t_axis(d)
    x = bp(noise(d), 900, 3800) * (0.5 + 0.5 * np.sin(2 * np.pi * 31 * t) ** 2)
    e = np.exp(-((t - 0.25) / 0.12) ** 2)
    gulp = np.sin(2 * np.pi * (180 - 60 * t) * t) * np.exp(-((t - 0.52) / 0.035) ** 2) * 0.6
    return fade(stereo(x * e * 0.6 + gulp, -0.2), 0.005, 0.05)


def process_chitter():
    d = 1.9
    out = np.zeros(int(d * SR))
    tk = 0.0
    k = 0
    while tk < d - 0.05:
        n = int(0.012 * SR)
        tt = np.arange(n) / SR
        f = 3200 + 900 * ((k * 7) % 5)
        click = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.002)
        i = int(tk * SR)
        out[i:i + n] += click[: len(out) - i]
        tk += max(0.025, 0.11 * (1 - tk / d) ** 1.5)
        k += 1
    t = t_axis(d)
    warble = np.sin(2 * np.pi * (1900 + 300 * np.sin(2 * np.pi * 13 * t)) * t) * 0.05 * np.sin(np.pi * t / d)
    return fade(room(stereo(out * 0.7 + warble, 0.35, 0.4), 0.3, 0.12), 0.002, 0.05)


def compose_done():
    d = 1.8
    out = np.zeros(int(d * SR))
    for i, (f, st) in enumerate([(1174.66, 0.0), (1479.98, 0.07), (1760.0, 0.14), (2349.32, 0.21)]):
        b = bell(f, d - st, tau=0.5) * (0.9 - 0.12 * i)
        j = int(st * SR)
        out[j:j + len(b)] += b
    return fade(room(stereo(out, 0.3, 0.5), 1.2, 0.3), 0.002, 0.2)


def lights_down():
    d = 1.8
    t = t_axis(d)
    f = 320 * (80 / 320) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sin(ph) + 0.3 * np.sin(2 * ph)) * np.exp(-t / 0.7) * 0.6
    x += lp(noise(d, "pink"), 600) * 0.2 * np.exp(-t / 0.5)
    return fade(room(stereo(x, 0, 0.5), 0.8, 0.25), 0.01, 0.2)


def snap_back():
    d = 3.0
    t = t_axis(d)
    f = 70 * np.exp(-t / 0.15) + 38
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-t / 0.35)
    crack = hp(noise(d), 1500) * np.exp(-t / 0.012) * 0.6
    ring = np.sin(2 * np.pi * 3700 * t) * 0.045 * np.clip(t / 0.05, 0, 1) * np.exp(-t / 0.9)
    x = sub + crack + ring
    return fade(stereo(x, 0, 0.2), 0.0005, 0.3)


def lights_up():
    d = 0.6
    t = t_axis(d)
    clunk = np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.05)
    hum = (np.sin(2 * np.pi * 120 * t) + 0.4 * np.sin(2 * np.pi * 240 * t)) * np.clip(t / 0.05, 0, 1) * np.exp(-t / 0.25) * 0.4
    tick = hp(noise(d), 2000) * np.exp(-t / 0.006) * 0.4
    return fade(room(stereo(clunk + hum + tick, 0, 0.3), 0.4, 0.15), 0.0005, 0.05)


def gasp_breath():
    d = 0.8
    t = t_axis(d)
    shape = np.clip(t / 0.06, 0, 1) * np.exp(-np.clip(t - 0.12, 0, None) / 0.18)
    x = _breath(d, shape, "ah", 500, 6000) * 1.2 + _breath(d, shape * 0.5, "hh")
    return fade(room(stereo(x, -0.2), 0.4, 0.12), 0.003, 0.08)


def holo_open():
    d = 1.6
    t = t_axis(d)
    out = np.zeros_like(t)
    notes = [1174.66, 1318.51, 1479.98, 1760.0, 1975.53, 2349.32, 2637.02, 2959.96]
    for i, f in enumerate(notes):
        st = 0.06 * i
        b = bell(f, d - st, tau=0.35, partials=((1, 1.0), (3.0, 0.15))) * 0.5
        j = int(st * SR)
        out[j:j + len(b)] += b
    swoosh = sweep_bp(noise(d, "pink"), 600, 6000, q=1.5) * np.sin(np.pi * np.clip(t / 0.9, 0, 1)) * 0.5
    return fade(room(stereo(out + swoosh, 0.3, 0.6), 1.0, 0.3), 0.003, 0.2)


def holo_select():
    d = 0.5
    t = t_axis(d)
    a = np.sin(2 * np.pi * 880 * t) * np.exp(-t / 0.06) * (t < 0.08)
    b = np.sin(2 * np.pi * 1318.5 * (t - 0.07)) * np.exp(-np.clip(t - 0.07, 0, None) / 0.12) * (t >= 0.07)
    return fade(room(stereo((a + b) * 0.6, 0.3, 0.4), 0.5, 0.25), 0.002, 0.05)


def sniff():
    d = 0.55
    t = t_axis(d)
    shape = np.exp(-((t - 0.08) / 0.04) ** 2) + 0.8 * np.exp(-((t - 0.28) / 0.06) ** 2)
    x = bp(noise(d), 1800, 6500) * shape
    return fade(stereo(x, -0.4), 0.003, 0.05)


def send_chime():
    d = 2.2
    out = np.zeros(int(d * SR))
    notes = [587.33, 739.99, 880.0, 1174.66, 1479.98, 1760.0, 2349.32, 2959.96]
    for i, f in enumerate(notes):
        st = 0.075 * i
        b = bell(f * 2, d - st, tau=0.45) * (0.55 + 0.05 * i)
        j = int(st * SR)
        out[j:j + len(b)] += b
    return fade(room(stereo(out, -0.2, 0.6), 1.3, 0.35), 0.002, 0.3)


def sip_cut():
    """S1 second sip, interrupted: the slurp starts like `sip` (+0.1, full by +0.25) but never reaches the
    gulp. It is cut dead at +0.56 (the compose_done chime lands there in the mix) and the freeze follows."""
    d = 0.62
    t = t_axis(d)
    x = bp(noise(d), 900, 3800) * (0.5 + 0.5 * np.sin(2 * np.pi * 31 * t) ** 2)
    e = np.exp(-((np.minimum(t, 0.25) - 0.25) / 0.12) ** 2) * (1.0 - 0.25 * np.clip((t - 0.25) / 0.3, 0, 1))
    e *= 1.0 - np.clip((t - 0.545) / 0.015, 0, 1)            # cut off in 15 ms
    return fade(stereo(x * e * 0.6, -0.2), 0.005, 0.01)


def step_soft():
    """One soft, slightly scuffed footstep (backing toward the door in S4); attack at +0.00 like footsteps_4."""
    d = 0.3
    n = int(d * SR)
    tt = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (100 - 45 * tt / 0.22) * tt) * np.exp(-tt / 0.028)
    scuff = bp(noise(d), 1000, 4200) * np.exp(-tt / 0.045) * 0.3
    out = thump + scuff
    pan = -0.3
    st_ = np.stack([out * np.cos((pan + 1) * np.pi / 4), out * np.sin((pan + 1) * np.pi / 4)], 1)
    return fade(room(st_, 0.4, 0.15), 0.002, 0.05)


# new effects go at the END of this list: the shared RNG is consumed in this order, so appending keeps every
# earlier effect bit-identical on a full rebuild
EFFECTS = {f.__name__: f for f in [
    space_rumble, whoosh_dive, ship_hum_loop, door_open, door_close, footsteps_4, bench_sit, sigh_breath, sip,
    process_chitter, compose_done, lights_down, snap_back, lights_up, gasp_breath, holo_open, holo_select,
    sniff, send_chime, sip_cut, step_soft]}


def main(only=None):
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    for name, fn in EFFECTS.items():
        if only and name not in only:
            continue
        x = fn()
        if x.ndim == 1:
            x = stereo(x)
        x = norm(x, -3.0)
        sf.write(SFX_DIR / f"{name}.wav", x.astype(np.float32), SR, subtype="FLOAT")
        print(f"{name:16s} {len(x)/SR:5.2f}s")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
