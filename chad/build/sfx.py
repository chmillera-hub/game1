"""Procedural sound effects. Every function takes a numpy Generator and returns audio
(mono or stereo) at dsp.SR. Registered in SFX by the names script.json uses."""
import numpy as np

from dsp import (SR, n_of, t_of, db, norm, add_at, expdec, adsr, white, pink, brown,
                 lowpass, highpass, bandpass, peak_band, sweep_filter, sine, additive,
                 square, saw, karplus, pan, stereo, reverb, midi_hz, fade)

SFX = {}


def sfx(name):
    def deco(fn):
        SFX[name] = fn
        return fn
    return deco


# ------------------------------------------------------------------ building blocks
def coin_hit(rng, f=None, dur=0.55):
    f = f or rng.uniform(2100, 2700)
    n = n_of(dur)
    y = np.zeros(n)
    for ratio, amp, tau in [(1, 1, 0.35), (2.41, 0.6, 0.22), (4.12, 0.35, 0.12), (6.33, 0.2, 0.07), (8.9, 0.1, 0.04)]:
        y += amp * sine(f * ratio * (1 + rng.uniform(-0.003, 0.003)), n) * expdec(n, tau, 0.0005)
    click = highpass(white(n_of(0.004), rng), 3000) * 0.6
    y[:len(click)] += click
    return y


def thud(rng, f=70, dur=0.35, body=0.6):
    n = n_of(dur)
    t = t_of(n)
    fr = f * (1 + 0.8 * np.exp(-t / 0.02))
    y = sine(fr, n) * expdec(n, dur / 4, 0.001)
    nz = lowpass(white(n, rng), 900) * expdec(n, 0.03, 0.0005) * body
    return y + nz


def formant_voice(f0_curve, rng, formants, breath=0.15, harsh=0.0):
    """Glottal-ish source through parallel formant resonators."""
    n = len(f0_curve)
    ph = 2 * np.pi * np.cumsum(f0_curve) / SR
    K = int(min(40, 9000 / max(np.max(f0_curve), 50)))
    src = np.zeros(n)
    for k in range(1, K + 1):
        src += np.sin(k * ph) / (k ** 0.85)
    src += breath * white(n, rng) + harsh * np.sign(np.sin(ph)) * 0.4
    y = np.zeros(n)
    for f, q, g in formants:
        y += g * peak_band(src, f, q)
    return y


def bleat_one(rng, f0=None, dur=None, harsh=0.0, angry=False):
    f0 = f0 or rng.uniform(290, 420)
    dur = dur or rng.uniform(0.55, 0.95)
    n = n_of(dur)
    t = t_of(n)
    rate = rng.uniform(9, 13)
    contour = 1 + 0.1 * np.sin(np.pi * np.clip(t / dur, 0, 1)) - (0.12 if angry else 0.05) * t / dur
    trill = 1 + (0.06 if not angry else 0.09) * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6))
    f0c = f0 * contour * trill
    form = [(750, 5, 1.0), (1650, 7, 0.55), (2650, 8, 0.25), (3600, 9, 0.1)]
    y = formant_voice(f0c, rng, form, breath=0.08 + harsh * 0.3, harsh=harsh)
    am = 1 - (0.35 if not angry else 0.5) * (0.5 + 0.5 * np.sin(2 * np.pi * rate * t))
    env = adsr(n, 0.03, 0.1, 0.85, 0.2) * am
    # nasal "m/b" onset: low-passed start
    onset = n_of(0.06)
    y[:onset] = lowpass(y[:onset], 500)
    return norm(y * env, 0.9)


def chorus_of(rng, count, span, maker, pan_spread=0.8):
    total = n_of(span + 1.5)
    out = np.zeros((total, 2))
    for _ in range(count):
        y = maker()
        add_at(out, pan(y, rng.uniform(-pan_spread, pan_spread)) * rng.uniform(0.5, 1.0), n_of(rng.uniform(0, span)))
    return out


# ------------------------------------------------------------------ registry
@sfx("pop")
def _pop(rng):
    n = n_of(0.16)
    t = t_of(n)
    f = 380 + 1100 * (1 - np.exp(-t / 0.03))
    return sine(f, n) * expdec(n, 0.045, 0.001)


@sfx("boing")
def _boing(rng):
    n = n_of(0.75)
    t = t_of(n)
    f = 160 * (1 + 0.9 * t) * (1 + 0.25 * np.sin(2 * np.pi * 13 * t) * np.exp(-t / 0.3))
    y = additive(f, n, [1, 0.4, 0.15]) * expdec(n, 0.25, 0.003)
    return y


@sfx("whoosh")
def _whoosh(rng):
    n = n_of(0.7)
    t = t_of(n)
    y = sweep_filter(white(n, rng), lambda tt: 300 + 2600 * np.sin(np.pi * np.clip(tt / 0.7, 0, 1)) ** 2, q=1.3)
    env = np.sin(np.pi * np.clip(t / 0.7, 0, 1)) ** 2
    return np.stack([y * env * (0.6 + 0.4 * t / 0.7), y * env * (1 - 0.4 * t / 0.7)], axis=1)


@sfx("thump")
def _thump(rng):
    return thud(rng, 65, 0.4, 0.5)


@sfx("bleat_chorus")
def _bleat_chorus(rng):
    return chorus_of(rng, 5, 1.1, lambda: bleat_one(rng))


@sfx("bleat_loud")
def _bleat_loud(rng):
    return bleat_one(rng, f0=rng.uniform(330, 360), dur=1.05, harsh=0.35)


@sfx("bleat_angry")
def _bleat_angry(rng):
    return chorus_of(rng, 9, 2.4, lambda: bleat_one(rng, f0=rng.uniform(200, 290), dur=rng.uniform(0.35, 0.6), harsh=0.6, angry=True))


@sfx("crowd_roar")
def _crowd_roar(rng):
    span = 3.0
    out = chorus_of(rng, 34, span, lambda: bleat_one(rng, f0=rng.uniform(180, 380), dur=rng.uniform(0.4, 0.9), harsh=0.5, angry=True), 1.0)
    n = len(out)
    t = t_of(n)
    rumble = lowpass(brown(n, rng), 160) * np.clip(t / 1.2, 0, 1) * np.exp(-np.maximum(0, t - span) / 0.5)
    out += stereo(rumble * 0.8)
    swell = np.clip(t / 0.8, 0.3, 1)[:, None]
    return out * swell


@sfx("shine")
def _shine(rng):
    n = n_of(1.1)
    out = np.zeros(n)
    for i, m in enumerate([88, 92, 95, 100]):
        tone = additive(midi_hz(m), n, [1, 0.3]) * expdec(n, 0.35, 0.002)
        add_at(out, tone[: n - n_of(0.05 * i)] * 0.6, n_of(0.05 * i))
    return reverb(out, 0.35, 1.2)


@sfx("ting")
def _ting(rng):
    n = n_of(1.0)
    y = sine(3150, n) * expdec(n, 0.4, 0.001) + 0.5 * sine(3170, n) * expdec(n, 0.3, 0.001) + 0.3 * sine(6300, n) * expdec(n, 0.12)
    return reverb(y, 0.3, 1.0)


@sfx("sparkle")
def _sparkle(rng):
    notes = [74, 76, 79, 81, 83, 86, 88, 91, 93, 95]
    n = n_of(2.6)
    out = np.zeros(n)
    for i, m in enumerate(notes):
        tone = additive(midi_hz(m), n_of(1.6), [1, 0.25, 0.1]) * expdec(n_of(1.6), 0.5, 0.003)
        add_at(out, tone * 0.45, n_of(0.09 * i))
    return reverb(out, 0.5, 2.5)


@sfx("bling")
def _bling(rng):
    n = n_of(1.0)
    out = np.zeros(n)
    for i, m in enumerate([93, 100]):
        add_at(out, (sine(midi_hz(m), n) + 0.4 * sine(midi_hz(m) * 2.01, n)) * expdec(n, 0.3, 0.001) * 0.6, n_of(0.08 * i))
    return reverb(out, 0.3, 1.0)


@sfx("coins_rain")
def _coins_rain(rng):
    n = n_of(1.6)
    out = np.zeros((n, 2))
    for i in range(7):
        add_at(out, pan(coin_hit(rng), rng.uniform(-0.7, 0.7)) * rng.uniform(0.5, 0.9), n_of(i * 0.11 + rng.uniform(0, 0.03)))
    return out


@sfx("coins_spill")
def _coins_spill(rng):
    n = n_of(2.2)
    out = np.zeros((n, 2))
    t = 0.0
    for i in range(22):
        add_at(out, pan(coin_hit(rng, dur=0.35), rng.uniform(-0.6, 0.6)) * rng.uniform(0.3, 0.8) * (1 - i / 30), n_of(t))
        t += rng.uniform(0.02, 0.11) * (1 + i / 15)
    return out


@sfx("coin_slot")
def _coin_slot(rng):
    n = n_of(0.8)
    out = np.zeros(n)
    add_at(out, coin_hit(rng, 2300, 0.4) * 0.7, 0)
    add_at(out, coin_hit(rng, 1900, 0.3) * 0.4, n_of(0.12))
    add_at(out, thud(rng, 120, 0.2, 0.8) * 0.6, n_of(0.3))
    return out


@sfx("turnstile")
def _turnstile(rng):
    n = n_of(0.6)
    out = np.zeros(n)
    add_at(out, coin_hit(rng, 2500, 0.3) * 0.5, 0)
    for i in range(4):
        click = bandpass(white(n_of(0.008), rng), 1500, 5000) * expdec(n_of(0.008), 0.002)
        add_at(out, click * 0.7, n_of(0.18 + 0.05 * i))
    return out


@sfx("hay")
def _hay(rng):
    n = n_of(0.6)
    y = bandpass(white(n, rng), 1800, 7000) * adsr(n, 0.02, 0.1, 0.5, 0.35) * 0.5
    add_at(y, thud(rng, 90, 0.3, 0.9) * 0.5, 0)
    return y


@sfx("munch")
def _munch(rng):
    n = n_of(1.6)
    out = np.zeros(n)
    for i in range(6):
        b = bandpass(white(n_of(0.07), rng), 700, 3500) * adsr(n_of(0.07), 0.003, 0.02, 0.4, 0.04)
        add_at(out, b * rng.uniform(0.5, 1), n_of(i * 0.24 + rng.uniform(0, 0.03)))
    return out


@sfx("clatter")
def _clatter(rng):
    n = n_of(0.9)
    out = np.zeros(n)
    t = 0.0
    for i in range(5):
        f = rng.uniform(380, 900)
        knock = (sine(f, n_of(0.12)) + 0.5 * sine(f * 2.7, n_of(0.12))) * expdec(n_of(0.12), 0.025, 0.0005)
        add_at(out, knock * (1 - i * 0.17), n_of(t))
        t += 0.09 + 0.03 * i
    return out


@sfx("door_slam")
def _door_slam(rng):
    n = n_of(1.4)
    y = np.zeros(n)
    add_at(y, thud(rng, 55, 0.6, 1.0), 0)
    add_at(y, sine(118, n_of(0.5)) * expdec(n_of(0.5), 0.09) * 0.5, 0)
    add_at(y, lowpass(white(n_of(0.15), rng), 2500) * expdec(n_of(0.15), 0.03) * 0.8, 0)
    for i in range(4):
        add_at(y, bandpass(white(n_of(0.01), rng), 800, 3000) * 0.3 * (1 - i / 4), n_of(0.06 + i * 0.045))
    return reverb(y, 0.3, 1.2)


@sfx("lock")
def _lock(rng):
    n = n_of(0.5)
    y = np.zeros(n)
    for i, f in enumerate([3400, 2600]):
        add_at(y, highpass(white(n_of(0.005), rng), 2500) * 0.8, n_of(i * 0.09))
        add_at(y, sine(f, n_of(0.15)) * expdec(n_of(0.15), 0.03) * 0.4, n_of(i * 0.09))
    return y


@sfx("rain")
def _rain(rng, dur=12.0):
    n = n_of(dur)
    out = np.zeros((n, 2))
    for c in range(2):
        bed = highpass(pink(n, rng), 500) * 0.35
        drops = np.zeros(n)
        idx = rng.integers(0, n, int(dur * 140))
        drops[idx] = rng.uniform(0.2, 1.0, len(idx)) * rng.choice([-1, 1], len(idx))
        drops = bandpass(drops, 2000, 9000)
        out[:, c] = bed + drops * 0.8
    return out


@sfx("wind")
def _wind(rng, dur=12.0):
    n = n_of(dur)
    out = np.zeros((n, 2))
    for c in range(2):
        ph = rng.uniform(0, 6, 3)
        fc = lambda tt: 420 + 260 * np.sin(2 * np.pi * 0.11 * tt + ph[0]) + 140 * np.sin(2 * np.pi * 0.27 * tt + ph[1])
        y = sweep_filter(pink(n, rng), fc, q=1.6)
        t = t_of(n)
        gust = 0.55 + 0.45 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + ph[2]))
        out[:, c] = y * gust
    return out


@sfx("crickets")
def _crickets(rng, dur=12.0):
    n = n_of(dur)
    out = np.zeros((n, 2))
    for k in range(4):
        f = rng.uniform(4200, 5200)
        period = rng.uniform(0.7, 1.1)
        p = rng.uniform(-0.8, 0.8)
        g = rng.uniform(0.3, 0.8)
        t = rng.uniform(0, period)
        chirp = np.zeros(n_of(0.14))
        for j in range(3):
            pulse = sine(f, n_of(0.016)) * np.hanning(n_of(0.016))
            add_at(chirp, pulse, n_of(j * 0.04))
        while t < dur:
            add_at(out, pan(chirp * g, p), n_of(t))
            t += period * rng.uniform(0.92, 1.08)
    return out


@sfx("thunder")
def _thunder(rng):
    dur = 5.0
    n = n_of(dur)
    t = t_of(n)
    crack = highpass(white(n, rng), 600) * expdec(n, 0.12, 0.002) * 0.9
    swells = np.zeros(n)
    for _ in range(5):
        c = rng.uniform(0.1, 2.5)
        w = rng.uniform(0.25, 0.8)
        swells += rng.uniform(0.4, 1.0) * np.exp(-((t - c) / w) ** 2)
    rumble = lowpass(brown(n, rng), 220, 2) * (swells + 0.2) * np.exp(-t / 2.2) * 1.6
    y = crack + rumble
    return reverb(y, 0.35, 2.5, tone=2500)


@sfx("thunder_far")
def _thunder_far(rng):
    dur = 5.5
    n = n_of(dur)
    t = t_of(n)
    swells = np.zeros(n)
    for _ in range(4):
        c = rng.uniform(0.6, 3.0)
        w = rng.uniform(0.4, 1.0)
        swells += rng.uniform(0.4, 1.0) * np.exp(-((t - c) / w) ** 2)
    y = lowpass(brown(n, rng), 140, 2) * swells * 1.5
    return reverb(fade(y, 0.4, 1.0), 0.4, 3.0, tone=1500)


@sfx("ghost")
def _ghost(rng):
    n = n_of(2.2)
    t = t_of(n)
    f = 520 + 260 * np.sin(np.pi * np.clip(t / 2.2, 0, 1)) + 14 * np.sin(2 * np.pi * 5.5 * t)
    y = additive(f, n, [1, 0.2, 0.05]) * adsr(n, 0.3, 0.3, 0.8, 0.8) * 0.5
    return reverb(y, 0.45, 2.0)


@sfx("crunch")
def _crunch(rng):
    n = n_of(0.5)
    y = np.zeros(n)
    add_at(y, coin_hit(rng, 1700, 0.3) * 0.5, 0)
    for i in range(5):
        b = bandpass(white(n_of(0.03), rng), 1000, 5000) * expdec(n_of(0.03), 0.008)
        add_at(y, b * rng.uniform(0.4, 0.9), n_of(0.02 + i * 0.035))
    return y


@sfx("error")
def _error(rng):
    n = n_of(0.6)
    y = np.zeros(n)
    for i, f in enumerate([330, 220]):
        tone = square(f, n_of(0.18), 15) * adsr(n_of(0.18), 0.005, 0.02, 0.8, 0.03)
        add_at(y, lowpass(tone, 3000) * 0.4, n_of(i * 0.2))
    return y


@sfx("powerup")
def _powerup(rng):
    notes = [60, 64, 67, 72, 76, 79, 84, 88, 91, 96]
    n = n_of(1.6)
    y = np.zeros(n)
    for i, m in enumerate(notes):
        seg = square(midi_hz(m), n_of(0.14), 11) * adsr(n_of(0.14), 0.003, 0.03, 0.6, 0.05)
        add_at(y, lowpass(seg, 6000) * 0.35, n_of(i * 0.12))
    return reverb(y, 0.2, 0.8)


@sfx("flash")
def _flash(rng):
    n = n_of(1.6)
    t = t_of(n)
    y = sweep_filter(white(n, rng), lambda tt: 600 + 7000 * np.clip(tt / 0.4, 0, 1), q=0.9) * np.exp(-t / 0.5) * 0.6
    for m in [84, 88, 91, 96]:
        y += sine(midi_hz(m), n) * expdec(n, 0.6, 0.01) * 0.12
    return reverb(y, 0.4, 1.6)


@sfx("stamp")
def _stamp(rng):
    n = n_of(0.5)
    y = thud(rng, 90, 0.4, 1.0)[:n]
    y[:n_of(0.03)] += bandpass(white(n_of(0.03), rng), 600, 4000) * 0.8
    return reverb(y, 0.15, 0.6)


@sfx("click")
def _click(rng):
    n = n_of(0.12)
    y = bandpass(white(n, rng), 2000, 8000) * expdec(n, 0.006, 0.0003)
    y += sine(1800, n) * expdec(n, 0.01) * 0.3
    return y


@sfx("drain")
def _drain(rng):
    n = n_of(1.3)
    y = np.zeros(n)
    for i in range(10):
        f = 1400 * (0.83 ** i)
        seg = square(f, n_of(0.07), 9) * adsr(n_of(0.07), 0.002, 0.01, 0.7, 0.02)
        add_at(y, lowpass(seg, 5000) * 0.3, n_of(i * 0.08))
    buzz = saw(70, n_of(0.35), 30) * adsr(n_of(0.35), 0.01, 0.05, 0.8, 0.1) * 0.35
    add_at(y, lowpass(buzz, 1200), n_of(0.85))
    return y


@sfx("denied")
def _denied(rng):
    n = n_of(0.75)
    y = (square(140, n, 21) + square(147, n, 21)) * adsr(n, 0.01, 0.05, 0.9, 0.08) * 0.3
    return lowpass(y, 2500)


@sfx("splash")
def _splash(rng):
    n = n_of(1.0)
    y = bandpass(white(n, rng), 900, 7000) * adsr(n, 0.01, 0.15, 0.25, 0.6) * 0.6
    for i in range(7):
        bn = n_of(0.05)
        tb = t_of(bn)
        bub = sine(500 + 2200 * tb / 0.05 * rng.uniform(0.6, 1.2), bn) * np.hanning(bn)
        add_at(y, bub * 0.25, n_of(0.1 + i * 0.09 + rng.uniform(0, 0.04)))
    return y


@sfx("whistle")
def _whistle(rng):
    notes = [(79, 0.18), (83, 0.18), (86, 0.3), (84, 0.18), (83, 0.45)]
    total = sum(d for _, d in notes) + 0.4
    y = np.zeros(n_of(total))
    t = 0.0
    for m, d in notes:
        nn = n_of(d)
        tt = t_of(nn)
        f = midi_hz(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * tt))
        tone = sine(f, nn) * adsr(nn, 0.03, 0.05, 0.85, 0.06)
        tone += bandpass(white(nn, rng), 2000, 6000) * 0.04
        add_at(y, tone * 0.5, n_of(t))
        t += d
    return reverb(y, 0.25, 1.0)


@sfx("scratch")
def _scratch(rng):
    n = n_of(0.55)
    t = t_of(n)
    f = lambda tt: 400 + 3500 * np.abs(np.sin(2 * np.pi * 2.7 * tt))
    y = sweep_filter(white(n, rng), f, q=3.0)
    fz = 200 + 900 * np.abs(np.sin(2 * np.pi * 2.7 * t))
    y += saw(fz, n, 12) * 0.25
    return y * adsr(n, 0.005, 0.05, 0.9, 0.12)


@sfx("snore")
def _snore(rng):
    n = n_of(2.6)
    t = t_of(n)
    y = np.zeros(n)
    inhale = lowpass(pink(n, rng), 700) * (0.5 + 0.5 * np.sin(2 * np.pi * 32 * t)) * np.exp(-((t - 0.6) / 0.35) ** 2)
    exhale = bandpass(pink(n, rng), 300, 2500) * np.exp(-((t - 1.6) / 0.45) ** 2) * 0.35
    y += inhale + exhale
    return y


@sfx("startle")
def _startle(rng):
    n = n_of(0.25)
    t = t_of(n)
    f = 300 + 1600 * (t / 0.25) ** 0.7
    return additive(f, n, [1, 0.3]) * adsr(n, 0.005, 0.05, 0.7, 0.08) * 0.5


@sfx("steam")
def _steam(rng):
    n = n_of(1.3)
    t = t_of(n)
    whistle = sine(2700 + 300 * t, n) * 0.35
    hiss = highpass(white(n, rng), 3000) * 0.4
    return (whistle + hiss) * adsr(n, 0.35, 0.1, 0.8, 0.3)


@sfx("sigh")
def _sigh(rng):
    dur = 1.6
    n = n_of(dur)
    t = t_of(n)
    breath = bandpass(pink(n, rng), 350, 2600)
    env = np.exp(-((t - 0.45) / 0.35) ** 2) * 0.45 + np.exp(-((t - 1.05) / 0.4) ** 2)
    f0 = 125 - 30 * np.clip((t - 0.7) / 0.8, 0, 1)
    voiced = formant_voice(f0, rng, [(700, 6, 1.0), (1150, 7, 0.5), (2500, 8, 0.2)], breath=0.4)
    voiced *= np.exp(-((t - 1.0) / 0.32) ** 2) * 0.08
    return norm(breath * env * 0.8 + voiced, 0.9)


@sfx("slap")
def _slap(rng):
    n = n_of(0.35)
    y = bandpass(white(n, rng), 700, 5000) * expdec(n, 0.018, 0.0005)
    y += thud(rng, 140, 0.35, 0.3)[:n] * 0.6
    return reverb(y, 0.18, 0.5)


@sfx("stomp")
def _stomp(rng):
    n = n_of(0.8)
    y = thud(rng, 52, 0.8, 0.7)[:n]
    y += lowpass(white(n, rng), 1200) * expdec(n, 0.05) * 0.4
    return reverb(y, 0.25, 1.0, tone=2000)


@sfx("hit")
def _hit(rng):
    n = n_of(2.4)
    y = thud(rng, 45, 2.4, 0.8)[:n] * 1.2
    for m in [36, 43, 48, 51, 55]:
        y += saw(midi_hz(m), n, 30) * expdec(n, 0.35, 0.004) * 0.18
    y += lowpass(white(n, rng), 3000) * expdec(n, 0.08) * 0.5
    return reverb(lowpass(y, 4000), 0.35, 2.0)


@sfx("heart")
def _heart(rng):
    n = n_of(0.35)
    y = np.zeros(n)
    for i, f0 in enumerate([700, 1050]):
        nn = n_of(0.1)
        tt = t_of(nn)
        add_at(y, sine(f0 + 600 * tt / 0.1, nn) * expdec(nn, 0.04, 0.002) * 0.6, n_of(i * 0.11))
    return y


@sfx("flip")
def _flip(rng):
    n = n_of(0.5)
    y = np.zeros(n)
    for i in range(3):
        b = bandpass(white(n_of(0.06), rng), 1500, 8000) * adsr(n_of(0.06), 0.005, 0.02, 0.5, 0.03)
        add_at(y, b * 0.6, n_of(i * 0.12))
    return y


@sfx("bell")
def _bell(rng):
    dur = 7.5
    n = n_of(dur)
    f = 311.0  # nominal
    y = np.zeros(n)
    for ratio, amp, tau in [(0.5, 0.55, 4.5), (1.0, 0.45, 3.2), (1.19, 0.4, 2.4), (1.5, 0.2, 1.8),
                            (2.0, 0.65, 1.8), (2.52, 0.25, 1.0), (3.0, 0.2, 0.8), (4.0, 0.1, 0.5)]:
        y += amp * sine(f * ratio, n) * expdec(n, tau, 0.002)
    y[:n_of(0.01)] += highpass(white(n_of(0.01), rng), 1500) * 0.4
    return reverb(y, 0.45, 3.5, tone=3000)


@sfx("boom")
def _boom(rng):
    n = n_of(4.0)
    t = t_of(n)
    y = sine(80 * np.exp(-t / 0.6) + 32, n) * expdec(n, 1.1, 0.01)
    y += lowpass(brown(n, rng), 120) * expdec(n, 0.8, 0.01) * 0.5
    return reverb(y, 0.4, 3.0, tone=1200)


@sfx("birds")
def _birds(rng, dur=12.0):
    """Morning birdsong: a few birds, each with its own little phrase, repeating loosely."""
    n = n_of(dur)
    out = np.zeros((n, 2))
    for b in range(4):
        base = rng.uniform(2600, 4200)
        p = rng.uniform(-0.8, 0.8)
        phrase = []
        for k in range(rng.integers(2, 5)):
            d = rng.uniform(0.05, 0.14)
            nn = n_of(d)
            tt = t_of(nn)
            f = base * (1 + rng.uniform(-0.25, 0.25)) + rng.uniform(-900, 900) * tt / d
            f = f * (1 + 0.04 * np.sin(2 * np.pi * rng.uniform(25, 45) * tt))
            phrase.append((sine(f, nn) * np.hanning(nn) * rng.uniform(0.5, 1.0), rng.uniform(0.03, 0.09)))
        t = rng.uniform(0, 2.0)
        while t < dur:
            tt = t
            for y, gap in phrase:
                add_at(out, pan(y * 0.6, p), n_of(tt))
                tt += len(y) / SR + gap
            t += rng.uniform(1.4, 3.2)
    return reverb(out, 0.25, 1.4, tone=6000)


@sfx("poof")
def _poof(rng):
    n = n_of(0.7)
    t = t_of(n)
    y = lowpass(white(n, rng), 1800) * expdec(n, 0.12, 0.004) * 0.8
    y += sine(260 + 500 * np.exp(-t / 0.05), n) * expdec(n, 0.06, 0.002) * 0.5
    return reverb(y, 0.25, 0.8)


@sfx("chaching")
def _chaching(rng):
    n = n_of(1.4)
    y = np.zeros(n)
    for i in range(3):
        add_at(y, coin_hit(rng, rng.uniform(2200, 2600), 0.35) * 0.5, n_of(0.02 + i * 0.05))
    drawer = bandpass(white(n_of(0.14), rng), 300, 2500) * adsr(n_of(0.14), 0.01, 0.04, 0.5, 0.06)
    add_at(y, drawer * 0.6, n_of(0.2))
    bell = (sine(1568, n_of(1.0)) + 0.5 * sine(3136, n_of(1.0)) + 0.25 * sine(4704, n_of(1.0))) * expdec(n_of(1.0), 0.35, 0.002)
    add_at(y, bell * 0.55, n_of(0.32))
    return reverb(y, 0.2, 0.9)


# ---------------------------------------------------------------- EMOTIONAL CHAD
@sfx("yell")
def _yell(rng):
    """Power-up scream: a strained 'AAAH' that climbs in pitch and grit."""
    dur = 6.0
    n = n_of(dur)
    t = t_of(n)
    f0 = 170 + 80 * np.clip(t / dur, 0, 1) ** 1.5
    f0 = f0 * (1 + 0.025 * np.sin(2 * np.pi * 7 * t) + 0.01 * np.sin(2 * np.pi * 23 * t))
    y = formant_voice(f0, rng, [(800, 4, 1.0), (1250, 5, 0.7), (2600, 6, 0.35), (3400, 8, 0.15)], breath=0.35, harsh=0.6)
    y = np.tanh(norm(y, 1.0) * 2.5)
    env = adsr(n, 0.25, 0.3, 0.9, 0.9) * (0.75 + 0.25 * np.clip(t / dur, 0, 1))
    return reverb(lowpass(y * env, 5000), 0.3, 1.6)


@sfx("aura")
def _aura(rng, dur=12.0):
    n = n_of(dur)
    t = t_of(n)
    hum = sine(55 + 6 * np.sin(2 * np.pi * 0.3 * t), n) * 0.6 + sine(110, n) * 0.25
    crackle = highpass(white(n, rng), 3000) * (rng.random(n) < 0.004) * 3
    roar = bandpass(pink(n, rng), 120, 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.7 * t))
    y = hum + roar * 0.8 + crackle * 0.4
    return np.stack([y, np.roll(y, 300)], axis=1)


@sfx("punch")
def _punch(rng):
    n = n_of(0.5)
    y = thud(rng, 90, 0.5, 1.0)[:n]
    y[:n_of(0.02)] += bandpass(white(n_of(0.02), rng), 800, 6000) * 0.9
    return reverb(y, 0.2, 0.6)


@sfx("punch_big")
def _punch_big(rng):
    n = n_of(1.4)
    t = t_of(n)
    y = np.zeros(n)
    add_at(y, thud(rng, 60, 1.0, 1.2) * 1.2, 0)
    add_at(y, bandpass(white(n_of(0.05), rng), 600, 7000) * expdec(n_of(0.05), 0.012) * 1.2, 0)
    sweep = sweep_filter(white(n, rng), lambda tt: 4000 * np.exp(-tt / 0.3) + 300, q=1.2) * np.exp(-t / 0.5) * 0.7
    return reverb(y + sweep, 0.3, 1.2)


@sfx("explosion")
def _explosion(rng):
    dur = 5.0
    n = n_of(dur)
    t = t_of(n)
    crack = highpass(white(n, rng), 300) * expdec(n, 0.15, 0.002)
    body = lowpass(brown(n, rng), 400, 2) * np.exp(-t / 1.4) * 1.6
    sub = sine(45 * np.exp(-t / 1.5) + 25, n) * np.exp(-t / 1.2) * 0.9
    debris = np.zeros(n)
    for i in range(40):
        at = n_of(rng.uniform(0.3, 3.0))
        k = bandpass(white(n_of(0.03), rng), 800, 5000) * expdec(n_of(0.03), 0.008) * rng.uniform(0.1, 0.4)
        add_at(debris, k, at)
    return reverb(np.tanh((crack + body + sub + debris) * 1.3), 0.35, 2.5, tone=3000)


@sfx("pant")
def _pant(rng):
    n = n_of(2.2)
    t = t_of(n)
    y = np.zeros(n)
    for i in range(4):
        b = bandpass(pink(n_of(0.35), rng), 500, 3000) * np.hanning(n_of(0.35)) * (0.9 if i % 2 == 0 else 0.6)
        add_at(y, b, n_of(i * 0.5))
    return y


@sfx("dial")
def _dial(rng):
    n = n_of(2.6)
    y = np.zeros(n)
    for i, f in enumerate([941, 1336, 852, 1209]):
        add_at(y, (sine(f, n_of(0.09)) + sine(f * 0.55, n_of(0.09))) * 0.3, n_of(i * 0.13))
    ring = (sine(440, n_of(0.9)) + sine(480, n_of(0.9))) * 0.2
    add_at(y, ring, n_of(0.8))
    return bandpass(y, 300, 3400)


@sfx("beep")
def _beep(rng):
    n = n_of(0.6)
    return sine(1000, n) * adsr(n, 0.005, 0.02, 0.9, 0.02) * 0.4


@sfx("putt")
def _putt(rng):
    n = n_of(1.6)
    t = t_of(n)
    y = np.zeros(n)
    add_at(y, (sine(1900, n_of(0.08)) + bandpass(white(n_of(0.08), rng), 1500, 6000)) * expdec(n_of(0.08), 0.01), 0)
    roll = lowpass(white(n, rng), 600) * np.clip(1 - t / 1.2, 0, 1) * 0.15
    y += roll
    add_at(y, (sine(700, n_of(0.3)) + sine(1150, n_of(0.3)) * 0.5) * expdec(n_of(0.3), 0.06), n_of(1.2))
    return y
