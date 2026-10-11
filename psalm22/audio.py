"""Score, ambience and final mix — all synthesized here, cued from the timeline."""
import os
import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter, fftconvolve, sosfilt
import timeline as TL
from timeline import S, E, F, TOTAL

SR = 48000
N = int((TOTAL + 0.5) * SR)
RNG = np.random.default_rng(22)
OUT = TL.WORK


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def buf():
    return np.zeros((N, 2))


def add(bus, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(x) <= 0:
        return
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        x = np.stack([x * l * 1.414, x * r * 1.414], 1)
    if i < 0:
        x = x[-i:]; i = 0
    n = min(len(x), N - i)
    bus[i:i + n] += x[:n] * gain


def lp(x, fc, order=2):
    sos = butter(order, fc / (SR / 2), 'low', output='sos')
    return sosfilt(sos, x, axis=0)


def hp(x, fc, order=2):
    sos = butter(order, fc / (SR / 2), 'high', output='sos')
    return sosfilt(sos, x, axis=0)


def bp(x, f0, f1, order=2):
    sos = butter(order, [f0 / (SR / 2), f1 / (SR / 2)], 'band', output='sos')
    return sosfilt(sos, x, axis=0)


def env_adsr(n, att, rel, total):
    t = np.arange(n) / SR
    a = np.clip(t / max(att, 1e-3), 0, 1)
    a = np.sin(a * np.pi / 2) ** 2
    r = np.clip((total - t) / max(rel, 1e-3), 0, 1)
    return a * r


def reverb_ir(seconds=2.6, damp=4000, seed=1, pre=0.02):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal((n, 2)) * np.exp(-t * 6.9 / seconds)[:, None]
    # darker tail
    ir[:, 0] = lp(ir[:, 0], damp)
    ir[:, 1] = lp(ir[:, 1], damp)
    ir = np.concatenate([np.zeros((int(pre * SR), 2)), ir])
    ir /= np.sqrt(np.sum(ir ** 2) / 2)
    return ir


def conv(x, ir):
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    y = np.stack([fftconvolve(x[:, 0], ir[:, 0])[:len(x)], fftconvolve(x[:, 1], ir[:, 1])[:len(x)]], 1)
    return y

# ------------------------------------------------------------ instruments ---

TABLE_N = 4096


def table(amps):
    ph = np.arange(TABLE_N) / TABLE_N
    tb = np.zeros(TABLE_N)
    for k, a in enumerate(amps, 1):
        tb += a * np.sin(2 * np.pi * k * ph)
    return tb / (np.max(np.abs(tb)) + 1e-9)


def osc(tb, freq, phase0=0.0):
    ph = (phase0 + np.cumsum(freq) / SR) % 1.0
    idx = ph * TABLE_N
    i0 = idx.astype(int)
    fr = idx - i0
    return tb[i0] * (1 - fr) + tb[(i0 + 1) % TABLE_N] * fr


_TB = {}


def string_table(f, bright):
    key = (int(f), bright)
    if key not in _TB:
        nh = max(1, min(48, int(14000 / f)))
        _TB[key] = table([(1 / k) * np.exp(-k / bright) for k in range(1, nh + 1)])
    return _TB[key]


def strings(m, dur, vel=0.5, att=0.8, rel=1.5, bright=7.0, voices=3, vib=0.0035):
    f = midi(m)
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    tb = string_table(f, bright)
    out = np.zeros((n, 2))
    for ch in range(2):
        for v in range(voices):
            det = 1 + 0.0045 * (v - (voices - 1) / 2) + 0.0015 * (ch - 0.5)
            ph = RNG.uniform(0, 6.28)
            fv = f * det * (1 + vib * np.sin(2 * np.pi * (5.0 + 0.4 * v) * t + ph))
            out[:, ch] += osc(tb, fv, RNG.uniform())
    out *= (env_adsr(n, att, rel, dur + rel) * vel / voices)[:, None]
    return lp(out, min(9000, 2200 + f * 4))


def pad(t0, dur, notes, vel=0.4, att=1.2, rel=2.0, bright=6.0, bus=None):
    for m in notes:
        add(bus, strings(m, dur, vel / np.sqrt(len(notes)), att, rel, bright), t0)


def choir_note(m, dur, vel=0.4, att=1.5, rel=2.0, vowel='a'):
    f = midi(m)
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    nh = max(1, min(60, int(12000 / f)))
    tb = table([1 / k ** 0.9 for k in range(1, nh + 1)])
    out = np.zeros((n, 2))
    for ch in range(2):
        for v in range(4):
            det = 1 + 0.006 * (v - 1.5) + 0.002 * ch
            fv = f * det * (1 + 0.007 * np.sin(2 * np.pi * (5.3 + 0.3 * v) * t + RNG.uniform(0, 6)))
            out[:, ch] += osc(tb, fv, RNG.uniform())
    forms = {'a': [(700, 1.0), (1150, 0.6), (2700, 0.25)], 'o': [(450, 1.0), (800, 0.5), (2600, 0.15)]}[vowel]
    y = np.zeros_like(out)
    for fc, g in forms:
        y += bp(out, fc * 0.85, fc * 1.15) * g
    y *= (env_adsr(n, att, rel, dur + rel) * vel / 4)[:, None]
    return y * 3


def reed_line(notes, t0, vel=0.35, kind='duduk'):
    """Legato melody: notes = [(midi, beats)], 1 beat = 1 s by default list of (m, dur)."""
    total = sum(d for _, d in notes) + 1.2
    n = int(total * SR)
    t = np.arange(n) / SR
    fcurve = np.zeros(n)
    amp = np.zeros(n)
    pos = 0.0
    prev = midi(notes[0][0])
    for m, d in notes:
        i0, i1 = int(pos * SR), int((pos + d) * SR)
        f = midi(m)
        g = int(0.07 * SR)
        seg = np.full(i1 - i0, f)
        k = min(g, i1 - i0)
        seg[:k] = prev + (f - prev) * np.sin(np.linspace(0, np.pi / 2, k))
        fcurve[i0:i1] = seg
        # note shape: swell then ease
        tt = np.linspace(0, 1, i1 - i0)
        amp[i0:i1] = 0.75 + 0.25 * np.sin(np.pi * np.clip(tt * 1.2, 0, 1))
        prev = f
        pos += d
    fcurve[int(pos * SR):] = prev
    amp[int(pos * SR):] = np.linspace(amp[int(pos * SR) - 1], 0, n - int(pos * SR))
    vib_depth = np.clip((t % 1.0) * 1.5, 0, 1) * 0.008
    fcurve = fcurve * (1 + vib_depth * np.sin(2 * np.pi * 5.4 * t))
    if kind == 'duduk':
        tb = table([1.0, 0.55, 0.62, 0.35, 0.42, 0.22, 0.25, 0.12, 0.14, 0.07, 0.06, 0.04])
    else:  # cello-ish
        tb = table([1.0, 0.7, 0.45, 0.4, 0.3, 0.22, 0.18, 0.12, 0.1, 0.08, 0.06, 0.05, 0.04])
    y = osc(tb, fcurve)
    y = y + 0.8 * bp(y, 900, 1700)
    breath = bp(RNG.standard_normal(n), 1200, 3500) * 0.05
    y = (y + breath) * amp
    a = env_adsr(n, 0.25, 0.8, total)
    y = lp(y * a * vel, 5000)
    return y


def piano(m, vel=0.4, dur=4.0):
    f = midi(m)
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    B = 0.0003
    for k in range(1, 11):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > 12000:
            break
        a = vel / k ** 1.3 * (1.0 if k < 3 else 0.7)
        dec = 0.6 + 0.35 * k + f / 600
        y += a * np.sin(2 * np.pi * fk * t + RNG.uniform(0, 6)) * np.exp(-t * dec)
    y += lp(RNG.standard_normal(n) * np.exp(-t * 60) * 0.03 * vel, 2000)
    att = np.clip(t / 0.004, 0, 1)
    y *= att
    return lp(y, 3200)


def pluck(m, vel=0.4, dur=3.0, damp=0.996):
    f = midi(m)
    L = int(SR / f)
    n = int(dur * SR)
    x = np.zeros(n)
    x[:L] = lp(RNG.uniform(-1, 1, L), 3000) * vel
    a = np.zeros(L + 2)
    a[0] = 1
    a[L] = -damp / 2
    a[L + 1] = -damp / 2
    y = lfilter([1.0], a, x)
    return lp(y, 4000)


def bell(m, vel=0.3, dur=2.5):
    f = midi(m)
    t = np.arange(int(dur * SR)) / SR
    y = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 3)
         + 0.15 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 5)) * np.exp(-t * 1.6) * vel
    return y * np.clip(t / 0.003, 0, 1)

# ------------------------------------------------------------------- sfx ---

def noise(n):
    return RNG.standard_normal(n)


def brown(n):
    x = np.cumsum(RNG.standard_normal(n))
    x = hp(x, 15)
    return x / (np.max(np.abs(x)) + 1e-9)


def wind(dur, level_fn):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for ch in range(2):
        w = noise(n)
        lo = bp(w, 180, 500) * 1.4
        mid = bp(w, 500, 1400)
        mod1 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + ch) * np.sin(2 * np.pi * 0.023 * t + 1 + ch)
        mod2 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t + 2 + ch)
        out[:, ch] = lo * (0.4 + 0.6 * mod1) + mid * 0.5 * mod2 ** 2
    out *= level_fn(t)[:, None]
    return out * 0.08


def thunder(dur=6.0, crack=0.6, low=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    b = brown(n)
    rumble = lp(b, 160, 4) * low
    flick = np.abs(np.convolve(RNG.standard_normal(n), np.ones(4800) / 4800, mode='same'))
    flick /= flick.max()
    env = (1 - np.exp(-t * 18)) * np.exp(-t * 0.75) * (0.5 + flick)
    c = hp(noise(n), 400) * np.exp(-t * 9) * crack
    y = (rumble * 3.0 + lp(c, 4000)) * env
    return np.stack([y, np.roll(y, 300)], 1) * 0.5


def heartbeat(vel=0.5):
    out = np.zeros(int(0.7 * SR))
    for off, a in ((0.0, 1.0), (0.24, 0.65)):
        n = int(0.18 * SR)
        t = np.arange(n) / SR
        f = 58 - 20 * t / 0.18
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22) * a
        i = int(off * SR)
        out[i:i + n] += s
    return out * vel


def breath(dur=0.8, vel=0.15, ragged=False):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = bp(noise(n), 400, 3200)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    if ragged:
        env *= 0.65 + 0.35 * np.abs(np.sin(2 * np.pi * 7 * t))
        x = x + 0.4 * bp(noise(n), 150, 600)
    return x * env * vel


def crickets(dur, seed=5):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros((n, 2))
    for c in range(4):
        f = r.uniform(4100, 4900)
        pan = r.uniform(-0.8, 0.8)
        period = r.uniform(0.55, 0.9)
        t0 = r.uniform(0, period)
        pulse_n = int(0.018 * SR)
        tt = np.arange(pulse_n) / SR
        pulse = np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / 0.018)
        chirp = np.zeros(int(0.12 * SR))
        for k in range(3):
            i = int(k * 0.033 * SR)
            chirp[i:i + pulse_n] += pulse
        a = r.uniform(0.25, 0.5)
        tcur = t0
        while tcur < dur - 0.2:
            i = int(tcur * SR)
            l, rr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            seg = chirp * a * (0.8 + 0.4 * r.uniform())
            m = min(len(seg), n - i)
            out[i:i + m, 0] += seg[:m] * l
            out[i:i + m, 1] += seg[:m] * rr
            tcur += period * r.uniform(0.9, 1.1)
    return out * 0.05


def birdsong(dur, density=0.5, seed=9):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros((n, 2))
    tcur = r.uniform(0.2, 1.0)
    while tcur < dur - 1.0:
        pan = r.uniform(-0.9, 0.9)
        base = r.uniform(2600, 4200)
        for k in range(r.integers(3, 8)):
            d = r.uniform(0.05, 0.13)
            m = int(d * SR)
            tt = np.arange(m) / SR
            sweep = base * (1 + r.uniform(-0.3, 0.4) * tt / d)
            s = np.sin(2 * np.pi * np.cumsum(sweep) / SR) * np.sin(np.pi * tt / d) ** 2
            s += 0.2 * np.sin(2 * np.pi * np.cumsum(sweep * 2) / SR) * np.sin(np.pi * tt / d) ** 2
            i = int((tcur + k * r.uniform(0.09, 0.16)) * SR)
            if i + m >= n:
                break
            l, rr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            out[i:i + m, 0] += s * l * 0.5
            out[i:i + m, 1] += s * rr * 0.5
        tcur += r.uniform(0.8, 2.8) / density
    return out * 0.06


def flaps(dur=1.6, seed=3):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros(n)
    for b in range(10):
        t0 = r.uniform(0, 0.5)
        rate = r.uniform(9, 14)
        m = int(r.uniform(0.5, 1.0) * SR)
        tt = np.arange(m) / SR
        am = np.clip(np.sin(2 * np.pi * rate * tt), 0, 1) ** 3
        s = bp(noise(m), 600, 3500) * am * np.exp(-tt * 2.0)
        i = int(t0 * SR)
        out[i:i + m] += s[:n - i] * 0.6
    return out * 0.3

# ----------------------------------------------------------------- score ---

def score():
    mus = buf()
    lead = buf()
    # ---- opening: drone + lament (D phrygian dominant)
    pad(0.0, S['M1'] + 1.0, [38, 45, 50], 0.5, att=0.4, rel=2.5, bright=5, bus=mus)
    add(lead, reed_line([(69, 1.1), (70, 0.5), (69, 0.6), (67, 1.0), (66, 1.4), (63, 0.6), (62, 2.4)], 0), E['N1'] - 1.6, 0.9)
    # ---- mockers: uneasy pulse D/Eb
    t = S['M1'] - 0.3
    k = 0
    while t < E['J1']:
        m = 38 if k % 2 == 0 else 39
        add(mus, strings(m, 0.35, 0.55, att=0.03, rel=0.35, bright=4), t)
        t += 0.75; k += 1
    pad(S['M1'], E['J1'] - S['M1'] + 0.5, [50, 51, 57], 0.18, att=2, rel=2, bright=4, bus=mus)
    # ---- "Woman, here is your son": tender turn
    seq = [(S['X1'] - 0.6, [46, 50, 53, 58]), (S['X2'] - 0.3, [41, 53, 57, 60]),
           (E['X2'] + 0.5, [43, 50, 55, 58]), (E['X2'] + 1.9, [45, 52, 57, 61]), (S['N2'] - 0.1, [38, 50, 53, 57])]
    for (a, notes), (b, _) in zip(seq, seq[1:] + [(S['N2'] + 2.5, None)]):
        pad(a, b - a + 0.4, notes, 0.42, att=0.9, rel=1.6, bright=6, bus=mus)
    add(lead, reed_line([(77, 0.9), (76, 0.7), (74, 0.9), (73, 0.8), (74, 1.8)], 0, 0.22, kind='cello'), E['X2'] + 0.2, 0.9)
    # ---- darkness: low cluster + heartbeat, thinning to silence before the cry
    pad(S['N2'] - 0.1, S['N3'] - S['N2'] + 1.2, [26, 38, 45, 51], 0.42, att=2.5, rel=2.0, bright=3, bus=mus)
    t = S['N2'] + 0.6
    while t < E['N3'] - 0.4:
        add(mus, heartbeat(0.55), t, 1.0)
        t += 1.35
    # ---- after the cry: choir swell under "My God, my God"
    a = E['XC'] + 0.15
    for m in (50, 57, 62, 65):
        add(mus, choir_note(m, E['X4'] - a + 1.5, 0.30, att=2.4, rel=3.0), a)
    pad(a, E['X4'] - a + 1.0, [38, 45], 0.35, att=2.5, rel=3, bright=4, bus=mus)
    # ---- the women and John
    seq = [(S['G2'] - 0.4, [38, 50, 53, 57]), (S['Y1'] - 0.2, [34, 50, 53, 58]), (F('Y2', 0)[0], [41, 53, 57, 60]),
           (E['Y2'] + 0.3, [36, 52, 55, 60]), (S['J2'] - 0.2, [38, 50, 53, 57]), (F('J2', 1)[0], [34, 50, 53, 58]),
           (S['Y4'] - 0.2, [33, 49, 52, 57]), (E['Y4'] + 0.3, [38, 50, 53, 57])]
    ends = [s for s, _ in seq[1:]] + [S['X5'] + 1.0]
    for (a, notes), b in zip(seq, ends):
        if F('Y2', 1)[0] - 0.2 < a < E['Y2']:
            continue
        pad(a, b - a + 0.5, notes, 0.36, att=1.0, rel=1.8, bright=5.5, bus=mus)
    add(lead, reed_line([(62, 1.2), (65, 0.8), (64, 0.8), (62, 1.4), (61, 1.0), (62, 2.0)], 0, 0.2, kind='cello'), S['G2'] + 0.2, 0.8)
    # flashback lullaby (F major): harp arpeggios + bell melody
    fb0, fb1 = F('Y2', 1)[0] - 0.15, E['Y2'] + 0.35
    pad(fb0, fb1 - fb0, [41, 53, 57, 60], 0.3, att=0.8, rel=1.5, bright=7, bus=mus)
    t, k = fb0, 0
    arp = [53, 57, 60, 65, 60, 57]
    while t < fb1 - 0.2:
        add(mus, pluck(arp[k % 6], 0.35, 2.5, 0.997), t, 0.9, pan=-0.3 + 0.1 * (k % 6))
        t += 0.42; k += 1
    for i, m in enumerate([72, 69, 65, 67, 69, 65, 64, 65]):
        add(mus, bell(m, 0.18), fb0 + 0.3 + i * 0.75, 1.0, pan=0.2)
    # ---- death: high sustained note, then silence
    pad(S['X5'] - 0.4, E['X5'] - S['X5'] + 0.8, [50, 57, 62], 0.3, att=1.5, rel=1.4, bright=5, bus=mus)
    add(mus, strings(81, E['X5'] - S['X5'] + 0.6, 0.12, att=2.0, rel=1.4, bright=3, voices=2), S['X5'])
    # ---- centurion: revelation in F major
    c0 = E['X5'] + 2.9
    pad(c0, S['C1'] - c0 + 0.2, [26, 38], 0.35, att=1.5, rel=1.2, bright=3, bus=mus)
    for m in (53, 57, 60, 65):
        add(mus, choir_note(m, E['C1'] - F('C1', 1)[0] + 2.5, 0.26, att=1.6, rel=2.5, vowel='o'), F('C1', 1)[0] - 0.4)
    pad(F('C1', 1)[0] - 0.4, E['C1'] - F('C1', 1)[0] + 2.8, [29, 41, 53, 57], 0.35, att=1.6, rel=2.0, bright=5, bus=mus)
    # ---- bridge narration
    b0, b1 = S['N4'] - 0.4, E['N6'] + 0.8
    prog = [[38, 50, 53, 57], [34, 50, 53, 58], [41, 53, 57, 60], [36, 52, 55, 60], [38, 50, 53, 57], [31, 50, 55, 58], [33, 49, 52, 57]]
    step = (b1 - b0) / len(prog)
    for i, notes in enumerate(prog):
        pad(b0 + i * step, step + 0.4, notes, 0.40 + 0.03 * i, att=1.4, rel=1.8, bright=5.5 + 0.3 * i, bus=mus)
    add(lead, reed_line([(62, 0.6), (66, 0.6), (67, 0.6), (69, 1.6), (70, 0.6), (72, 1.0), (70, 0.6), (69, 2.4)], 0, 0.2), E['N5'] - 0.3, 0.7)
    # ---- modern: felt piano + guitar
    m0, m1 = S['N7'] - 0.8, E['R4'] + 0.6
    chords = [[50, 57, 60, 64, 65], [46, 53, 57, 62, 65], [45, 53, 57, 60, 65], [43, 50, 53, 58, 62]]
    bright_chords = [[41, 53, 57, 60, 64], [40, 52, 55, 60, 67], [38, 50, 53, 57, 60], [46, 53, 57, 62, 65]]
    t, k = m0, 0
    while t < m1:
        warm = t > S['R2'] - 1.0
        ch = (bright_chords if warm else chords)[k % 4]
        for j, m in enumerate(ch):
            add(mus, piano(m, 0.16 if j else 0.2, 5.0), t + j * 0.28, 0.9, pan=-0.2 + 0.1 * j)
        add(mus, pluck(ch[0] - 12 + 12, 0.25, 4.0), t + 2.0, 0.6, pan=0.3)
        t += 4.2; k += 1
    # acorn sparkle
    for i, m in enumerate((77, 81, 84)):
        add(mus, bell(m, 0.12), E['R3'] + 0.9 + i * 0.12, 1.0, pan=0.3)
    # ---- garden: dawn, building to the tree in full fruit, D major arrival
    g0 = E['R4'] + 0.8
    prog = [(g0, [46, 53, 58, 62]), (S['N8'] + 2.4, [41, 53, 57, 60]), (S['N9'] - 0.2, [36, 52, 55, 60]),
            (S['N10'] - 0.3, [38, 50, 53, 57]), (F('N10', 2)[0], [34, 50, 53, 58]), (F('N10', 3)[0], [36, 48, 55, 60]),
            (S['N11'] - 0.2, [38, 50, 54, 57, 62]), (F('N11', 1)[0], [43, 50, 55, 59]), (F('N11', 2)[0], [45, 52, 57, 61]),
            (F('N11', 3)[0], [38, 50, 54, 57, 62, 66])]
    ends = [s for s, _ in prog[1:]] + [E['N11'] + 1.5]
    for i, ((a, notes), b) in enumerate(zip(prog, ends)):
        pad(a, b - a + 0.5, notes, 0.32 + 0.025 * i, att=1.0, rel=1.8, bright=5 + 0.35 * i, bus=mus)
        add(mus, piano(notes[-1] + 12, 0.14, 4.0), a + 0.1, 0.8, pan=0.2)
    add(lead, reed_line([(74, 0.8), (76, 0.6), (78, 0.8), (81, 1.4), (79, 0.6), (78, 0.8), (76, 0.6), (74, 2.6)], 0, 0.22), F('N11', 1)[0], 0.8)
    # ---- final: D major, piano and strings
    f0 = E['N11'] + 0.7
    prog = [[38, 50, 54, 57], [43, 50, 55, 59], [35, 50, 54, 59], [43, 50, 55, 59], [45, 52, 57, 61], [38, 50, 54, 57, 62]]
    step = (TOTAL - 3.0 - f0) / len(prog)
    for i, notes in enumerate(prog):
        last = i == len(prog) - 1
        pad(f0 + i * step, (step + 0.3) if not last else (TOTAL - f0 - i * step), notes, 0.3, att=1.2, rel=2.5, bright=6, bus=mus)
        for j, m in enumerate(notes[1:]):
            add(mus, piano(m + 12, 0.13, 5.0), f0 + i * step + j * 0.33, 0.85, pan=-0.15 + 0.1 * j)
    add(mus, bell(86, 0.1, 4.0), TOTAL - 4.0, 1.0)
    # reverb
    hall = reverb_ir(3.2, 3800, 3)
    mus = mus + conv(mus, hall) * 0.45
    lead = lead * 0.85 + conv(lead, hall) * 0.5
    return mus + lead


def ambience():
    amb = buf()
    # wind across Golgotha
    g_end = S['N7'] - 0.6

    def wl(t):
        return np.interp(t, [0, S['N2'], E['N3'], S['XC'], E['XC'] + 2, E['X5'], E['X5'] + 3, S['N4'], g_end - 1, g_end],
                         [0.55, 0.75, 1.0, 0.7, 1.0, 0.5, 0.35, 0.55, 0.5, 0.0])
    add(amb, wind(g_end, wl), 0.0, 1.0)
    # crowd murmur from extra voices
    clips = [sf.read(f'{OUT}/voice/crowd{i}.wav')[0] for i in range(10)]
    r = np.random.default_rng(4)
    for (a, b, dens, vol) in ((0.0, S['N2'], 2.2, 0.06), (S['N2'], S['N3'], 0.6, 0.035), (E['XC'] + 0.6, E['X4'] + 2, 1.6, 0.05)):
        t = a + 0.2
        while t < b:
            c = clips[r.integers(0, 10)]
            add(amb, lp(c, 1700), t, vol * r.uniform(0.6, 1.0), pan=r.uniform(-0.8, 0.8))
            t += r.uniform(0.2, 1.0) * 1.0 / dens * 1.6
    # thunder
    add(amb, thunder(6, 0.3, 0.8), S['N2'] + 0.4, 0.8)
    add(amb, thunder(7, 1.0, 1.0), F('XC', 0)[0] + 0.05, 0.9)
    add(amb, thunder(5, 0.5, 0.7), F('XC', 1)[0] + 0.05, 0.55)
    add(amb, thunder(8, 1.2, 1.2), F('XC', 2)[0] + 0.05, 1.0)
    # birds startle
    add(amb, flaps(), E['XC'] + 0.1, 1.0, pan=0.1)
    # the earth shakes
    q0 = E['X5'] + 1.9
    qn = int(3.5 * SR)
    tq = np.arange(qn) / SR
    quake = lp(brown(qn), 90, 4) * 3.5 * (1 - np.exp(-tq * 8)) * np.exp(-tq * 0.9) + \
        bp(noise(qn), 200, 1200) * 0.12 * np.exp(-tq * 1.5) * (np.abs(np.sin(tq * 31)) > 0.6)
    add(amb, quake, q0, 0.9)
    # porch at night
    p0, p1 = S['N7'] - 0.6, E['R4'] + 0.8
    cr = crickets(p1 - p0)
    fade = np.clip(np.arange(len(cr)) / SR / 1.5, 0, 1) * np.clip((p1 - p0 - np.arange(len(cr)) / SR) / 1.0, 0, 1)
    add(amb, cr * fade[:, None], p0)
    hum = lp(noise(int((p1 - p0) * SR)), 120, 2) * 0.012
    add(amb, hum * fade, p0)
    for k in range(5):
        tt = S['N7'] + 0.6 + k * 1.3
        click = hp(noise(400), 2000) * np.exp(-np.arange(400) / 60) * 0.05
        add(amb, click, tt)
    # soil while planting
    pl = TL.SHOT_LIST[[s.name for s in TL.SHOT_LIST].index('planting')]
    for k in range(4):
        n = int(0.35 * SR)
        s = lp(noise(n), 1400) * np.sin(np.linspace(0, np.pi, n)) * 0.08
        add(amb, s, pl.start + 1.3 + k * 0.32, 1.0, pan=(-1) ** k * 0.3)
    # dawn birds
    d0 = pl.start
    bs = birdsong(TOTAL - d0, 0.6)
    fd = np.clip(np.arange(len(bs)) / SR / 2.0, 0, 1)
    add(amb, bs * fd[:, None], d0)
    add(amb, wind(TOTAL - d0, lambda t: np.full_like(t, 0.25)), d0)
    return amb


def voices():
    vb = buf()
    dry = buf()
    outdoor = reverb_ir(1.4, 5000, 7, 0.015)
    porch = reverb_ir(0.6, 6000, 8, 0.01)
    for lid, m in TL.META.items():
        a, _ = sf.read(f'{OUT}/voice/{lid}.wav')
        a = hp(a, 80)
        ch = m['char']
        if lid == 'XC':
            # the cry rolls across the valley
            y = np.zeros(len(a) + int(3.0 * SR))
            y[:len(a)] += a
            for d, g in ((0.43, 0.32), (0.86, 0.17), (1.29, 0.09), (1.72, 0.045)):
                i = int(d * SR)
                y[i:i + len(a)] += lp(a, 2600) * g
            wet = conv(y, outdoor) * 0.35
            add(vb, y * 0.95, S[lid], 1.0)
            add(vb, wet, S[lid], 1.0)
            continue
        if ch == 'NARRATOR':
            add(dry, a * 0.82, S[lid])
            add(vb, conv(a, porch) * 0.05, S[lid])
            continue
        g = {'JESUS': 0.9, 'MOCKER1': 0.75, 'MOCKER2': 0.75, 'X3': 0.6}.get(ch, 0.85)
        if lid == 'X3':
            g = 0.62
        ir, w = (porch, 0.08) if ch in ('YOUNG', 'NANA') else (outdoor, 0.13)
        if lid in ('X4',):
            w = 0.22
        add(dry, a * g, S[lid])
        add(vb, conv(a, ir) * w * g, S[lid])
    # breaths before key lines
    add(dry, breath(1.0, 0.22, ragged=True), F('XC', 0)[0] - 1.05, 1.0)
    for lid, v in (('G2', 0.07), ('Y1', 0.06), ('X5', 0.08), ('Q1', 0.05), ('Q2', 0.05), ('C1', 0.06)):
        add(dry, breath(0.6, v), S[lid] - 0.65)
    return dry + vb, dry


def mix():
    mus = score()
    amb = ambience()
    vox, dry = voices()
    # duck music + ambience under speech
    act = np.abs(dry).sum(1)
    k = int(0.02 * SR)
    act = np.convolve(act, np.ones(k) / k, mode='same')
    act = np.clip(act / 0.05, 0, 1)
    # slow release
    from scipy.signal import lfilter as lf
    a_rel = np.exp(-1 / (0.35 * SR))
    act = lf([1 - a_rel], [1, -a_rel], act)
    act = np.clip(act * 1.6, 0, 1)
    duck = 1 - 0.5 * act
    mus *= (duck * 0.55)[:, None]
    amb *= (1 - 0.3 * act)[:, None]
    master = vox + mus + amb
    # gentle bus compression via soft knee + limiter
    peak = np.max(np.abs(master))
    master /= peak / 0.95
    master = np.tanh(master * 1.25) / np.tanh(1.25)
    # ultra short fade at very start (pop guard) and long fade at end
    n_in = int(0.02 * SR)
    master[:n_in] *= np.linspace(0, 1, n_in)[:, None]
    n_out = int(2.5 * SR)
    master[-n_out:] *= np.linspace(1, 0, n_out)[:, None] ** 1.5
    sf.write(f'{OUT}/mix.wav', master.astype(np.float32), SR, subtype='FLOAT')
    sf.write(f'{OUT}/stem_music.wav', (mus / (np.max(np.abs(mus)) + 1e-9) * 0.9).astype(np.float32), SR)
    print('mix written', len(master) / SR)


if __name__ == '__main__':
    mix()
