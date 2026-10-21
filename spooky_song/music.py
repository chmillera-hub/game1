"""The band and the final mix for 'Clickety-Clack!'.

Original arrangement in D minor (the last chorus jumps up to E minor):
xylophone 'bones', tuba oom-pah, castanet bone-clacks, a pumpkin drummer,
the cat's fiddle, the bat's muted horn, a spooky organ, choir and celesta.
Writes build/mix.wav.
"""
import json
import os

import numpy as np
import soundfile as sf

import synth
from synth import (INSTR, PAN, WET, Bus, Sfx, additive, apply_reverb, bp, chirp, env_adsr, glock, lp, mtof,
                   reverb_ir, smooth)

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build')
SR = 48000
RNG = np.random.default_rng(11)


# ── extra instruments ────────────────────────────────────────────────────────
def xylo(f, dur, v):
    s = additive(f, 0.7, [(1, 1, .28), (3.93, .45, .06), (9.2, .15, .02), (2.0, .08, .1)])
    click = bp(RNG.normal(0, 1, len(s)), 2500, 7000) * np.exp(-np.arange(len(s)) / SR / 0.004) * 0.3
    return v * (s + click) * env_adsr(len(s), 0.001, 0.05)


def organ(f, dur, v):
    d = dur + 0.15
    s = additive(f, d, [(0.5, .5, None), (1, 1, None), (2, .6, None), (3, .35, None), (4, .25, None),
                        (6, .12, None), (8, .08, None)])
    t = np.arange(len(s)) / SR
    trem = 1 + 0.18 * np.sin(2 * np.pi * 6.1 * t)
    return v * 0.35 * s * trem * env_adsr(len(s), 0.03, 0.15)


def fiddle(f, dur, v):
    d = dur + 0.12
    parts = [(k, (1 / k) * np.exp(-((f * k - 2600) / 1800) ** 2 * 0.3) + 0.3 / k ** 2, None) for k in range(1, 18)]
    s = additive(f, d, parts, vib=0.009, vib_rate=6.0)
    n = len(s)
    bow = bp(RNG.normal(0, 1, n), 2000, 6000) * 0.05 * np.exp(-np.arange(n) / SR / 0.05)
    return v * 0.4 * (s + bow) * env_adsr(n, 0.05, 0.1)


def horn(f, dur, v):
    d = dur + 0.08
    def w(k):
        fk = f * k
        return (1 / k ** 0.6) * (np.exp(-((fk - 1100) / 700) ** 2) + 0.35)
    parts = [(k, w(k), None) for k in range(1, 20)]
    s = additive(f, d, parts, vib=0.004, vib_rate=5.5)
    t = np.arange(len(s)) / SR
    wah = 0.75 + 0.25 * np.sin(np.pi * np.minimum(1, t / max(d, 0.05)))
    return v * 0.3 * s * wah * env_adsr(len(s), 0.035, 0.07)


def bell(f, dur, v):
    s = additive(f, 5.0, [(0.5, .6, 4.0), (1, 1, 3.2), (1.19, .5, 2.0), (1.5, .4, 1.8), (2.0, .45, 1.4),
                          (2.74, .25, 0.9), (3.0, .2, 0.8), (4.2, .12, 0.5)])
    return v * s * env_adsr(len(s), 0.002, 0.3)


INSTR.update(xylo=xylo, organ=organ, fiddle=fiddle, horn=horn, bell=bell)
PAN.update(xylo=-0.25, organ=0.0, fiddle=0.45, horn=-0.4, bell=0.0)
WET.update(xylo=.25, organ=.45, fiddle=.35, horn=.3, bell=.7)


# ── drums ────────────────────────────────────────────────────────────────────
class Kit:
    def __init__(self, L):
        self.buf = np.zeros((2, L))
        self.wet = np.zeros((2, L))

    def add(self, t, s, v, pan=0.0, wet=0.12):
        i0 = int(t * SR)
        if i0 < 0 or i0 >= self.buf.shape[1]:
            return
        s = s[:self.buf.shape[1] - i0] * v
        l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
        self.buf[0, i0:i0 + len(s)] += s * l
        self.buf[1, i0:i0 + len(s)] += s * r
        self.wet[:, i0:i0 + len(s)] += s * wet * 0.7

    def kick(self, t, v=0.5):
        n = int(0.35 * SR)
        tt = np.arange(n) / SR
        f = 48 + 90 * np.exp(-tt / 0.035)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.16)
        self.add(t, s, v)

    def snare(self, t, v=0.22, brush=True):
        n = int(0.25 * SR)
        tt = np.arange(n) / SR
        noise = bp(RNG.normal(0, 1, n), 1500, 7000) * np.exp(-tt / (0.09 if brush else 0.12))
        tone = np.sin(2 * np.pi * 190 * tt) * np.exp(-tt / 0.04) * (0.4 if brush else 0.8)
        self.add(t, noise + tone, v, 0.1)

    def hat(self, t, v=0.06):
        n = int(0.06 * SR)
        s = bp(RNG.normal(0, 1, n), 7000, 14000) * np.exp(-np.arange(n) / SR / 0.015)
        self.add(t, s, v, 0.25)

    def clack(self, t, v=0.12, pan=0.3):
        """Two dry bone knocks, like castanets."""
        for k, dt in enumerate((0.0, 0.028)):
            n = int(0.05 * SR)
            tt = np.arange(n) / SR
            s = bp(RNG.normal(0, 1, n), 1800, 4200) * np.exp(-tt / 0.008)
            s += 0.6 * np.sin(2 * np.pi * (950 + 120 * k) * tt) * np.exp(-tt / 0.012)
            self.add(t + dt, s, v * (1 if k == 0 else 0.7), pan, 0.15)

    def woodblock(self, t, v=0.12, f=880, pan=-0.2):
        n = int(0.12 * SR)
        tt = np.arange(n) / SR
        s = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.7 * tt)) * np.exp(-tt / 0.03)
        self.add(t, s, v, pan, 0.2)

    def cymbal(self, t, v=0.12, decay=1.2, pan=0.2):
        n = int(decay * 1.5 * SR)
        tt = np.arange(n) / SR
        s = bp(RNG.normal(0, 1, n), 4000, 15000) * np.exp(-tt / (decay * 0.4))
        self.add(t, s, v, pan, 0.3)

    def roll(self, t, dur, v=0.16):
        k = 0
        step = 0.045
        while k * step < dur:
            f = k * step / dur
            self.snare(t + k * step, v * (0.3 + 0.7 * f), brush=False)
            k += 1


# ── harmony ──────────────────────────────────────────────────────────────────
CH = {  # bass root (midi), chord tones (midi, around middle C)
    'Dm': (38, [57, 62, 65]), 'D': (38, [57, 62, 66]), 'F': (41, [57, 60, 65]), 'Gm': (43, [58, 62, 67]),
    'A7': (33, [55, 61, 64]), 'Bb': (34, [58, 62, 65]), 'C': (36, [55, 60, 64]),
}
CHARTS = {
    'intro': ['Dm', 'Dm', 'A7', 'Dm'],
    'verse': ['Dm', 'F', 'Dm', 'F', 'Dm', 'Gm', 'Dm', 'A7'],
    'chorus': ['Dm', 'Dm', 'Gm', 'A7', 'Dm', 'Dm', [('Gm', 2), ('A7', 2)], 'D'],
    'chorus3': ['Dm', 'Dm', 'Gm', 'A7', 'Dm', 'Dm', [('Gm', 2), ('A7', 1), ('D', 1)], [('A7', 1), ('D', 3)]],
    'tag': ['Bb', 'A7', 'Dm', [('Gm', 2), ('A7', 2)], 'D'],
    'boo': ['A7', 'A7'],
    'button': ['D'],
}
RIFF = [[74, None, 69, None, 65, 69, 74, None], [73, None, 69, None, 64, 69, 73, 76],
        [73, None, 69, None, 67, 64, 61, None], [62, 65, 69, 74, None, None, 62, None]]


def chord_slots(chart):
    """-> list of (bar, beat, beats, chord name)."""
    out = []
    for b, c in enumerate(chart):
        if isinstance(c, str):
            out.append((b, 0, 4, c))
        else:
            beat = 0
            for name, n in c:
                out.append((b, beat, n, name))
                beat += n
    return out


def oompah(bus, kit, t0, beat, chart, key, intensity=1.0, drums=True, stabs='pizz', clacks=True,
           tuba_v=0.16):
    for bar, b0, nb, name in chord_slots(chart):
        root, tones = CH[name]
        for bi in range(b0, b0 + nb):
            t = t0 + (bar * 4 + bi) * beat
            if bi % 2 == 0:
                bass = root + key + (0 if bi % 4 == 0 else 7)
                bus.note('tuba', t, bass if bass >= 33 else bass + 12, beat * 0.8, tuba_v * intensity)
                bus.note('pizz', t, bass + 12, beat, 0.12 * intensity)
                if drums:
                    kit.kick(t, 0.42 * intensity)
            else:
                for m in tones:
                    if stabs == 'pizz':
                        bus.note('pizz', t + RNG.uniform(0, 0.01), m + key, beat * 0.5, 0.06 * intensity)
                    else:
                        bus.note('organ', t, m + key, beat * 0.45, 0.05 * intensity)
                if drums:
                    kit.snare(t, 0.17 * intensity)
            if clacks:
                kit.clack(t + beat / 2, 0.09 * intensity, pan=0.35 if bi % 2 else -0.35)
            if drums:
                kit.hat(t + beat / 2, 0.035 * intensity)


def pad(bus, t0, beat, chart, key, instr='choir', v=0.02, octave=12, **kw):
    for bar, b0, nb, name in chord_slots(chart):
        _, tones = CH[name]
        for m in tones:
            bus.note(instr, t0 + (bar * 4 + b0) * beat, m + key + octave, nb * beat * 0.98, v, **kw)


def stinger(bus, t, kind):
    if kind == 'hi':
        for i, m in enumerate([74, 78, 81, 86]):
            bus.note('glock', t + i * 0.06, m, 0.6, 0.06)
        bus.note('choir', t, 81, 1.4, 0.035, vowel='ah', attack=0.15)
    else:
        bus.note('strings', t - 0.05, 38, 2.2, 0.12, attack=0.25)
        bus.note('strings', t - 0.05, 26, 2.2, 0.09, attack=0.3)
        bus.note('bassoon', t, 38, 1.6, 0.10)


def main():
    tl = json.load(open(os.path.join(BUILD, 'timeline.json')))
    T = tl['duration'] + 0.8
    L = int(T * SR)
    sec = {s['name']: s for s in tl['sections']}
    bus = Bus(L)
    kit = Kit(L)
    fx = Sfx(L)

    def beat_of(name):
        return 60.0 / sec[name]['bpm']

    # ── intro: midnight bells, organ, the xylophone riff
    s = sec['intro']
    b = beat_of('intro')
    for k in range(3):
        bus.note('bell', s['t0'] + 0.02 + k * 1.25, 50, 3.0, 0.16)
    pad(bus, s['t0'], b, CHARTS['intro'], 0, instr='organ', v=0.05, octave=0)
    for bar, notes in enumerate(RIFF):
        for i, m in enumerate(notes):
            if m:
                bus.note('xylo', s['t0'] + bar * 4 * b + i * b / 2, m, b / 2, 0.16 if bar >= 1 else 0.11)
    bus.note('theremin', s['t0'] + 0.4, 74, 2.5, 0.05)
    bus.note('theremin', s['t0'] + 3.0, 69, 3.5, 0.045)
    for k in range(8):
        kit.clack(s['t0'] + 2 * 4 * b + k * b, 0.08)
    fx.hoot(s['t0'] + 5.2, 0.06)

    # ── verses & choruses
    for name in ('verse1', 'chorus1', 'verse2', 'chorus2', 'chorus3'):
        s = sec[name]
        b = beat_of(name)
        key = s['key']
        chart = CHARTS['chorus3' if name == 'chorus3' else 'chorus' if 'chorus' in name else 'verse']
        full = 'chorus' in name
        oompah(bus, kit, s['t0'], b, chart, key, intensity=1.0 if full else 0.8, drums=True,
               stabs='pizz' if not full else 'organ' if name == 'chorus1' else 'pizz')
        if full:
            pad(bus, s['t0'], b, chart, key, 'choir', v=0.018 if name != 'chorus3' else 0.026)
            # xylophone doubles the tune an octave up — the bones playing along
            for ph in tl['phrases']:
                if ph['section'] == name:
                    for syl, n0, n1, m in ph['notes']:
                        bus.note('xylo', n0, m + 12, n1 - n0, 0.07)
            kit.cymbal(s['t0'], 0.10)
        else:
            # little xylophone answers in the gaps after each sung line
            for bar in (1, 3, 5):
                _, tones = CH[chart[bar]] if isinstance(chart[bar], str) else CH[chart[bar][0][0]]
                for i, m in enumerate(sorted(tones, reverse=True)):
                    bus.note('xylo', s['t0'] + (bar * 4 + 3) * b + i * b / 3, m + 12 + key, b / 3, 0.09)
        if name == 'verse2':
            # the band, introduced line by line
            t_pot, t_pump, t_cat, t_bat = (s['t0'] + k * 4 * b for k in (0, 2, 4, 5))
            fx.bed_bubbles(t_pot + 0.5, t_pot + 4 * b * 2, rate=7, v=0.06, pan=-0.4)
            for k in range(6):
                fx.pop(t_pot + 6 * b + k * 0.12, 0.12, 380 + 70 * k, pan=-0.4)
            for k in range(8):                                      # pumpkin drum fill
                kit.snare(t_pump + 7 * b + k * b / 8, 0.12 + 0.02 * k, brush=False)
            for i, m in enumerate([74, 77, 76, 74, 73, 74, 81, 77]):
                bus.note('fiddle', t_cat + 2 * b + i * b / 2, m, b / 2, 0.08)
            for i, m in enumerate([69, 69, 74]):
                bus.note('horn', t_bat + 2.5 * b + i * b / 2, m, b / 2 * (2 if i == 2 else 0.9), 0.1)
            for k in range(8):
                bus.note('fiddle', s['t0'] + (24 + k) * b, [62, 65, 69, 74, 73, 69, 64, 61][k] + 12, b, 0.05)
        if name == 'verse1':
            for ph in tl['phrases']:                                # the owl answers "...owls all hoot"
                for w, ws, we in ph['words']:
                    if ph['section'] == 'verse1' and w.startswith('hoot'):
                        fx.hoot(we + 0.05, 0.07)
            tap0 = s['t0'] + 24 * b                                 # "tap, tap, tap"
            for k, dt in enumerate((1, 2, 3)):
                kit.woodblock(tap0 + (dt * 2 - 0) * b / 2 + b / 2 * (k > 1), 0.16, 1200 + 150 * k, pan=0.2)
            fx.whoosh(s['t0'] + 16 * b, 1.4, 0.05)                  # dusting off the ribs
        if name in ('chorus2', 'chorus3'):
            for i, m in enumerate([62, 65, 69, 74]):
                bus.note('horn', s['t0'] + (16 + 3) * b + i * b / 4, m + key, b / 4, 0.06)
        if name == 'chorus3':
            pad(bus, s['t0'], b, chart, key, 'strings', v=0.03, octave=12)
            for ph in tl['phrases']:
                if ph['section'] == name:
                    for syl, n0, n1, m in ph['notes']:
                        if syl.startswith('BOO'):
                            fx.sparkle(n0, 8, 0.05, 0.6)
                            kit.cymbal(n0, 0.12)
        # glock twinkle on the bright last word of each chorus
        for ph in tl['phrases']:
            if ph['section'] == name:
                for syl, n0, n1, m in ph['notes']:
                    if norm(syl) in ('fine', 'top'):
                        for i, mm in enumerate([74, 78, 81, 86]):
                            bus.note('glock', n0 + i * 0.07, mm + key, 0.8, 0.05)

    # ── the band stops dead; awkward crickets; Alice's tiny "pff"
    s = sec['stop']
    kit.cymbal(s['t0'] - 0.02, 0.07, decay=0.3)
    n = int((s['t1'] - s['t0']) * SR)
    tt = np.arange(n) / SR
    crick = np.zeros(n)
    for k in range(int((s['t1'] - s['t0']) / 0.55)):
        c0 = int((0.3 + k * 0.55) * SR)
        for j in range(3):
            i0 = c0 + int(j * 0.045 * SR)
            m = min(int(0.03 * SR), n - i0)
            if m > 0:
                crick[i0:i0 + m] += np.sin(2 * np.pi * 4300 * np.arange(m) / SR) * np.hanning(m)
    fx.add(s['t0'], crick, 0.02, 0.4, 0.4)
    for t, name, d in tl['acts']:
        if name == 'pff':
            m = int(0.35 * SR)
            puff = bp(RNG.normal(0, 1, m), 300, 1500) * np.sin(np.pi * np.arange(m) / m) ** 2
            fx.add(t + 0.7, puff, 0.06, 0.1, 0.2)
            bus.note('celesta', t + 1.15, 62, 0.6, 0.05)
            bus.note('celesta', t + 1.45, 61, 0.9, 0.05)

    # ── bridge: a slow, soft vamp under the heart-to-heart
    s = sec['bridge']
    vb = 60.0 / 66
    prog = ['Dm', 'Bb', 'Gm', 'A7']
    k = 0
    tb = s['t0'] + 0.1
    t_louder = max(st for st, kind in tl['stingers'] if kind == 'hi')
    while tb < s['t1'] - 0.3:
        name = prog[k % 4]
        root, tones = CH[name]
        dur = min(4 * vb, s['t1'] - tb)
        if tb > t_louder - 3.0:
            name, (root, tones) = 'A7', CH['A7']                   # suspense under "what does a ghost go?"
        for m in tones:
            bus.note('organ', tb, m, dur, 0.022)
            bus.note('strings', tb, m + 12, dur, 0.012, attack=0.6)
        bus.note('strings', tb, root + 12, dur, 0.03, attack=0.5)
        for i in range(4):
            bus.note('celesta', tb + i * vb, tones[i % 3] + 12, vb, 0.035)
        tb += 4 * vb
        k += 1
    kit.roll(t_louder + 0.25, s['t1'] - t_louder - 0.2, 0.14)
    for t, kind in tl['stingers']:
        stinger(bus, t, kind)

    # ── BOO! and the key change
    s = sec['boo']
    b = beat_of('boo')
    for bar in range(2):
        for i in range(8):
            bus.note('strings', s['t0'] + bar * 4 * b + i * b / 2, 57 + bar * 2 + i, b / 2, 0.035)
    bus.note('tuba', s['t0'], 33, 8 * b, 0.12)
    for m in (57, 61, 64, 67):
        bus.note('choir', s['t0'], m + 12, 8 * b, 0.03, vowel='ah', attack=0.6)
    kit.roll(s['t0'] + 4 * b, 4 * b - 0.1, 0.16)
    kit.cymbal(s['t0'] + 0.05, 0.12, decay=2.0)
    fx.whoosh(s['t0'], 2.5, 0.14, 300, 2800)
    fx.sparkle(s['t0'] + 0.3, 12, 0.04, 2.5)

    # ── tag: slow, warm, everybody together
    s = sec['tag']
    b = beat_of('tag')
    key = s['key']
    chart = CHARTS['tag']
    pad(bus, s['t0'], b, chart, key, 'strings', v=0.04, octave=12)
    pad(bus, s['t0'], b, chart, key, 'choir', v=0.022, octave=12, vowel='ah')
    for bar, b0, nb, name in chord_slots(chart):
        root, tones = CH[name]
        bus.note('tuba', s['t0'] + (bar * 4 + b0) * b, root + key + (12 if root < 36 else 0), nb * b * 0.9, 0.09)
        for i in range(nb * 2):
            bus.note('harp', s['t0'] + (bar * 4 + b0) * b + i * b / 2, tones[i % 3] + key + 12, b, 0.06)
    for ph in tl['phrases']:
        if ph['section'] == 'tag':
            for syl, n0, n1, m in ph['notes']:
                if norm(syl) == 'lone':
                    for i, mm in enumerate([74, 78, 81, 86, 90]):
                        bus.note('glock', n0 + i * 0.08, mm + key, 1.2, 0.05)
                    kit.cymbal(n0, 0.06, decay=2.5)

    # ── button: "Boo!" and a big final hit
    s = sec['button']
    b = beat_of('button')
    hit = s['t0'] + 0.55 + 0.25
    key = s['key']
    for m in (38, 50, 57, 62, 66, 69, 74):
        bus.note('strings', hit, m + key, 2.5, 0.05, attack=0.02)
    bus.note('tuba', hit, 38 + key, 0.6, 0.2)
    for m in (62, 66, 69, 74, 78):
        bus.note('xylo', hit, m + key + 12, 0.3, 0.08)
        bus.note('glock', hit + 0.05, m + key + 12, 1.5, 0.04)
    kit.kick(hit, 0.5)
    kit.cymbal(hit, 0.18, decay=2.5)
    kit.clack(hit + 0.6, 0.15)
    kit.clack(hit + 0.8, 0.12)
    fx.sparkle(sec['end']['t0'] + 0.4, 6, 0.03, 2.0)

    # ── voices
    vocals = np.zeros((2, L))
    vwet = np.zeros((2, L))
    from song import SINGERS
    for name in os.listdir(os.path.join(BUILD, 'stems')):
        s_name = name[:-4]
        y, _ = sf.read(os.path.join(BUILD, 'stems', name), dtype='float64')
        y = y[:L]
        p = SINGERS[s_name]['pan']
        g = SINGERS[s_name]['gain']
        l, r = np.sqrt((1 - p) / 2), np.sqrt((1 + p) / 2)
        vocals[0, :len(y)] += y * l * g
        vocals[1, :len(y)] += y * r * g
        vwet[0, :len(y)] += y * l * g * 0.22
        vwet[1, :len(y)] += y * r * g * 0.22
    vocals += apply_reverb(vwet, reverb_ir(1.6, seed=4))

    ir = reverb_ir(2.2)
    music = bus.dry + apply_reverb(bus.wet, ir) * 0.8
    drums = kit.buf + apply_reverb(kit.wet, reverb_ir(1.0, seed=8)) * 0.6
    sfx = fx.buf + apply_reverb(fx.wet, reverb_ir(1.2, seed=5)) * 0.8

    # gentle ducking so words stay clear over the band
    hop = 480
    vmono = vocals.mean(axis=0)
    env = np.sqrt((vmono[:L // hop * hop].reshape(-1, hop) ** 2).mean(axis=1))
    duck_db = smooth((env > 0.01).astype(float) * 3.5, 0.05, 0.4, SR / hop)
    duck = 10 ** (-np.interp(np.arange(L) / hop, np.arange(len(duck_db)), duck_db) / 20)
    mix = vocals * 1.0 + (music * 0.85 + drums * 0.8) * duck + sfx * 0.9
    from scipy.signal import butter, sosfilt
    mix = np.stack([sosfilt(butter(2, 35, 'high', fs=SR, output='sos'), ch) for ch in mix])
    peak = np.percentile(np.abs(mix), 99.99)
    mix = np.tanh(mix / peak * 0.8) * 0.8
    mix[:, -int(0.5 * SR):] *= np.linspace(1, 0, int(0.5 * SR))

    def db(x):
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
    active = np.repeat(env > 0.01, hop)[:L]
    band = (music * 0.85 + drums * 0.8) * duck
    print(f'while singing/talking: vocals {db(vocals[:, :len(active)][:, active]):.1f} dB, '
          f'band {db(band[:, :len(active)][:, active]):.1f} dB | band alone {db(band[:, :len(active)][:, ~active]):.1f} dB'
          f' | sfx {db(sfx):.1f} dB')
    sf.write(os.path.join(BUILD, 'mix.wav'), mix.T.astype(np.float32), SR, subtype='FLOAT')
    print(f'mix {T:.1f}s')


def norm(s):
    return ''.join(c for c in s.lower() if c.isalpha())


if __name__ == '__main__':
    main()
