import sys, json, numpy as np, soundfile as sf, pyworld as pw, hashlib, os
from scipy import signal
import synth as S
from synth import SR
import story as ST
from sing import tts, sing_word, SR as TSR

FPS = 24
CACHE = "/tmp/claude-0/work/cache"; os.makedirs(CACHE, exist_ok=True)

def cached(key, fn):
    p = os.path.join(CACHE, hashlib.md5(key.encode()).hexdigest() + ".npy")
    if os.path.exists(p): return np.load(p)
    y = fn(); np.save(p, y); return y

def up(x): return signal.resample_poly(x, 2, 1)

def trim(x, thr=0.01):
    a = np.abs(x); i = np.where(a > a.max() * thr)[0]
    return x[max(0, i[0] - 200): i[-1] + 800]

def demonize(x24):
    x = x24.astype(np.float64)
    f0, t = pw.harvest(x, TSR, frame_period=5)
    sp = pw.cheaptrick(x, f0, t, TSR); ap = pw.d4c(x, f0, t, TSR)
    nb = sp.shape[1]; idx = np.minimum((np.arange(nb) * 1.22).astype(int), nb - 1)
    sp2 = np.ascontiguousarray(sp[:, idx])
    y = pw.synthesize(np.ascontiguousarray(f0 * 0.6), sp2, ap, TSR, 5)
    y2 = pw.synthesize(np.ascontiguousarray(f0 * 0.5), sp2, ap, TSR, 5)
    n = min(len(y), len(x), len(y2))
    out = y[:n] * 0.8 + y2[:n] * 0.4 + x[:n] * 0.25
    return np.tanh(out * 2.2) * 0.6

class Mix:
    def __init__(s, dur):
        s.n = int(dur * SR)
        s.bus = {k: np.zeros((2, s.n)) for k in ["voice", "song", "music", "sfx", "storm"]}
        s.send = {k: np.zeros((2, s.n)) for k in ["small", "big"]}
        s.mouth = {"him": np.zeros(s.n), "her": np.zeros(s.n)}
        s.voice_act = np.zeros(s.n)
    def add(s, x, t, bus, gain=1.0, pan=0.0, small=0.0, big=0.0):
        x = np.asarray(x, dtype=np.float64)
        i0 = int(round(t * SR))
        if i0 < 0: x = x[-i0:] if x.ndim == 1 else x[:, -i0:]; i0 = 0
        if x.ndim == 1:
            l = np.cos((pan + 1) * np.pi / 4) * np.sqrt(2); r = np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
            x = np.stack([x * l, x * r])
        m = min(x.shape[1], s.n - i0)
        if m <= 0: return
        seg = x[:, :m] * gain
        s.bus[bus][:, i0:i0 + m] += seg
        if small: s.send["small"][:, i0:i0 + m] += seg * small
        if big: s.send["big"][:, i0:i0 + m] += seg * big
    def track(s, face, x, t):
        i0 = int(t * SR); m = min(len(x), s.n - i0)
        if m > 0: s.mouth[face][i0:i0 + m] += x[:m]

def voice_line(mix, t, spk, text, caps):
    voice, speed, fx = ST.SPEAKERS[spk]
    raw = cached(f"tts|{voice}|{speed}|{text}", lambda: trim(tts(text, voice, speed)))
    if fx == "demon":
        raw = cached(f"demon|{text}", lambda: demonize(raw))
    x = up(raw); x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * 0.09
    dur = len(x) / SR
    if fx == "inner":
        mix.add(S.lp(x, 9000), t, "voice", 1.0, 0, small=0.18)
    elif fx == "inner_hot":
        y = np.tanh(x * 3) / 3 * 1.1
        mix.add(y, t, "voice", 1.1, 0, small=0.22, big=0.06)
    elif fx == "room":
        mix.add(x, t, "voice", 0.95, -0.1 if spk == "her" else 0.1, small=0.4)
    elif fx == "warm":
        mix.add(S.lp(x, 8000), t, "voice", 1.0, 0, small=0.3, big=0.12)
    elif fx == "echo":
        y = S.bp(x, 250, 4000)
        pan = S.rng.uniform(-0.7, 0.7)
        out = np.zeros(len(y) + int(0.9 * SR))
        for d, g in ((0, 1.0), (0.19, 0.45), (0.41, 0.28), (0.66, 0.15)):
            i = int(d * SR); out[i:i + len(y)] += y * g
        mix.add(out, t, "voice", 0.75, pan, small=0.2, big=0.5)
        dur += 0.3
    elif fx == "demon":
        mix.add(x, t, "voice", 1.25, 0, small=0.2, big=0.35)
    face = ST.MOUTH.get(spk)
    if face: mix.track(face, x, t)
    if fx != "echo": mix.voice_act[int(t * SR): int((t + dur) * SR)] = 1
    else: mix.voice_act[int(t * SR): int((t + dur) * SR)] = np.maximum(mix.voice_act[int(t * SR): int((t + dur) * SR)], 0.6)
    caps.append(dict(start=round(t, 3), end=round(t + dur, 3), text=text, spk=spk))
    return dur

def song_section(mix, start, section, kind, caps, vel=1.0, accomp=True, storm=False):
    lines = ST.VERSE if section == "verse" else ST.CHORUS
    texts = ST.VERSE_TEXT if section == "verse" else ST.CHORUS_TEXT
    chords = ST.VERSE_CHORDS if section == "verse" else ST.CHORUS_CHORDS
    B = ST.BEAT; tr = ST.TRANSPOSE
    t = start
    words = []
    for li, line in enumerate(lines):
        lt = t
        for w, ns, ds in line:
            words.append((t, w, ns, ds)); t += sum(ds) * B
        if kind == "sing":
            caps.append(dict(start=round(lt, 3), end=round(t - 0.2, 3), text=texts[li], spk="song"))
    # vocal
    if kind == "sing":
        for (wt, w, ns, ds) in words:
            ns2 = [n + tr for n in ns]
            y = cached(f"sing|{w}|{ns2}|{ds}", lambda: np.concatenate([[sing_word(w, ns2, ds, beat=B)[1]], sing_word(w, ns2, ds, beat=B)[0]]))
            lead, y = y[0], y[1:]
            y = up(y); y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 0.075 * vel
            mix.add(y, wt - lead, "song", 1.0, -0.15, small=0.3, big=0.35)
            mix.track("her", y, wt - lead)
    elif kind == "hum":
        # continuous wordless 'ooh' line
        tot = t - start; tt = np.arange(int((tot + 1.0) * SR)) / SR
        cents = np.zeros_like(tt); amp = np.zeros_like(tt)
        for (wt, w, ns, ds) in words:
            bt = wt - start
            for n, d in zip(ns, ds):
                sel = (tt >= bt) & (tt < bt + d * B)
                cents[sel] = (n + tr) * 100
                amp[sel] = 1.0
                bt += d * B
        k = int(0.07 * SR); cents = np.convolve(np.pad(cents, (k, k), "edge"), np.ones(k) / k, "same")[k:-k]
        amp = np.convolve(np.pad(amp, (k * 3, k * 3), "edge"), np.ones(k * 3) / (k * 3), "same")[k * 3:-k * 3]
        vib = 25 * np.sin(2 * np.pi * 5.2 * tt)
        f = 440 * 2 ** ((cents + vib) / 1200 - 69 / 12)
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = np.zeros_like(tt)
        for kk in range(1, 25):
            fk = kk * np.mean(f)
            a = sum(g / (1 + ((fk - F) / bw) ** 2) for F, bw, g in S.FORM["u"]) / kk ** 0.5
            y += a * np.sin(kk * ph)
        y += S.bp(S.rng.normal(0, 1, len(tt)), 2000, 6000) * 0.01
        y *= amp; y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 0.05 * vel
        mix.add(y, start, "song", 1.0, -0.1, small=0.3, big=0.5)
        mix.track("her", y * 0.25, start)
    if accomp:
        for bi, ch in enumerate(chords):
            bt = start + bi * 4 * B
            cn = S.chord_notes(ch, 3, tr)
            bass = cn[0] - 12
            mix.add(S.piano(bass, 4 * B, 0.32), bt, "music", 1, -0.2, small=0.3, big=0.25)
            pat = [cn[0], cn[1], cn[2], cn[0] + 12, cn[2], cn[1], cn[2], cn[0] + 12]
            for i, m in enumerate(pat):
                mix.add(S.piano(m + 12 if section == "chorus" and i % 4 == 3 else m, B * 0.9, 0.14 + 0.03 * (i % 4 == 0)), bt + i * B / 2, "music", 1, 0.25 * np.sin(i), small=0.3, big=0.3)
            if section == "chorus" or bi >= 8:
                mix.add(S.strings([n + 12 for n in cn], 4 * B, 0.07 if not storm else 0.06, att=0.8, rel=1.0), bt, "music", 1, 0, big=0.3)
    return t

def intro(mix, start, chords=("Am", "E")):
    B = ST.BEAT; tr = ST.TRANSPOSE
    for bi, ch in enumerate(chords):
        cn = S.chord_notes(ch, 3, tr); bt = start + bi * 4 * B
        mix.add(S.piano(cn[0] - 12, 4 * B, 0.28), bt, "music", 1, -0.2, small=0.3, big=0.3)
        for i, m in enumerate([cn[0], cn[1], cn[2], cn[0] + 12, cn[2], cn[1], cn[2], cn[1]]):
            mix.add(S.piano(m, B * 0.9, 0.13), bt + i * B / 2, "music", 1, 0.2, small=0.3, big=0.3)

def ramp(n, pts):
    """pts: list of (time, value) -> per-sample array"""
    ts = [p[0] * SR for p in pts]; vs = [p[1] for p in pts]
    return np.interp(np.arange(n), ts, vs)

def finish(mix, name, caps, dur, storm_auto=None, music_auto=None):
    n = mix.n
    act = mix.voice_act
    k = int(0.25 * SR)
    act_s = np.convolve(act, np.ones(k) / k, "same")
    act_s = np.convolve(act_s, np.ones(k) / k, "same")
    song_g = 1 - 0.68 * act_s
    music_g = 1 - 0.4 * act_s
    if music_auto is not None: music_g *= music_auto
    out = np.zeros((2, n))
    out += mix.bus["voice"]
    out += mix.bus["song"] * song_g
    out += mix.bus["music"] * music_g
    st = mix.bus["storm"] * (storm_auto if storm_auto is not None else 1)
    out += mix.bus["sfx"] + st
    small = S.reverb_ir(0.9, 0.01, 5000); big = S.reverb_ir(3.8, 0.03, 4500)
    send_s = mix.send["small"]; send_b = mix.send["big"].copy()
    # apply ducking to sends approx (song part is mixed in sends at full level; scale by song_g overall)
    for ch in range(2):
        out[ch] += signal.fftconvolve(send_s[ch], small[ch])[:n] * 0.6
        out[ch] += signal.fftconvolve(send_b[ch] * (0.6 + 0.4 * song_g), big[ch])[:n] * 0.5
    # master: gentle compression + limiter
    peak = np.abs(out).max()
    out = out / peak * 0.98
    rms = np.sqrt(np.mean(out ** 2))
    gain = 0.12 / rms
    out = np.tanh(out * gain * 1.0) / np.tanh(1.0 * np.abs(out * gain).max()) * 0.95 if gain > 1 else out
    out = np.clip(out, -0.99, 0.99)
    sf.write(f"{name}.wav", out.T.astype(np.float32), SR)
    # mouth envelopes per frame
    env = {}
    hop = SR // FPS
    for face, x in mix.mouth.items():
        nf = int(dur * FPS)
        r = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(nf)])
        p = np.percentile(r[r > 1e-5], 90) if np.any(r > 1e-5) else 1
        env[face] = np.round(np.clip(r / p, 0, 1.3), 3).tolist()
    caps.sort(key=lambda c: c["start"])
    json.dump(dict(dur=dur, fps=FPS, captions=caps, mouth=env), open(f"{name}_timeline.json", "w"))
    print("wrote", name, "rms", np.sqrt(np.mean(out ** 2)))

def lines_into(mix, part, caps):
    L = part["lines"]
    for i, (t, spk, text) in enumerate(L):
        d = voice_line(mix, t, spk, text, caps)
        nxt = L[i + 1][0] if i + 1 < len(L) else 1e9
        flag = "  <-- OVERLAP" if t + d > nxt and not ST.SPEAKERS[spk][2] == "echo" else ""
        print(f"{t:7.2f} {d:5.2f} {spk:9s} {text[:50]}{flag}")

def build_part1():
    P = ST.PART1; dur = P["dur"]; mix = Mix(dur); caps = []
    lines_into(mix, P, caps)
    # --- music ---
    intro(mix, 44.0)
    t = song_section(mix, 44.0 + 8 * ST.BEAT, "verse", "sing", caps)
    end = song_section(mix, t, "chorus", "sing", caps, storm=True)
    # opening theme fragment over title (bells)
    for i, m in enumerate([64, 67, 71, 69, 64]):
        mix.add(S.bell(m + 12 + ST.TRANSPOSE, 5, 0.12), 1.0 + i * 1.1, "music", 1, 0.3 * (i - 2) / 2, big=0.6)
    mix.add(S.strings([40, 47, 52], 8, 0.08, att=3, rel=3), 0.5, "music", 1, 0, big=0.3)
    # --- ambience ---
    mix.add(S.rain(34) * ramp(int(34 * SR), [(0, 0), (3, 0.5), (9, 1), (31, 1), (34, 0)]), 0, "sfx", 0.22, 0, small=0.1)
    mix.add(S.lp(S.colored_noise(int(26 * SR), 1.8), 300) * ramp(int(26 * SR), [(0, 0), (3, 1), (22, 1), (26, 0)]), 8, "sfx", 0.15)
    mix.add(S.rain(dur - 31, muffled=True) * ramp(int((dur - 31) * SR), [(0, 0), (2, 1), (dur - 31, 1)]), 31, "sfx", 0.18)
    mix.add(S.door_creak(1.3, 0.25), 30.6, "sfx", 1, 0.5, small=0.4)
    mix.add(S.door_thud(0.5), 33.2, "sfx", 1, 0.5, small=0.5)
    for i in range(8):
        mix.add(S.footstep(0.35 - i * 0.02), 31.8 + i * 0.6, "sfx", 1, 0.4 - i * 0.05, small=0.5)
    # bulb hum
    tt = S.tarr(dur - 32)
    hum = sum(np.sin(2 * np.pi * 120 * k * tt) / k for k in range(1, 6)) * 0.01
    hum *= 0.6 + 0.4 * (S.smooth_rand(len(tt), int((dur - 32) * 4)) > 0.3)
    mix.add(hum * ramp(len(tt), [(0, 0), (2, 1), (100, 1), (104, 0.3), (dur - 32, 0.3)]), 32, "sfx", 1, -0.3)
    # memories: drone, heartbeat
    mix.add(S.drone(dur - 86, [28, 35, 40], 0.22) * ramp(int((dur - 86) * SR), [(0, 0), (8, 0.6), (40, 1), (81.5, 1.3), (82, 0), (dur - 86, 0)]), 86, "storm", 1)
    hb = 95.0; gap = 1.05
    while hb < 167.5:
        mix.add(S.heartbeat(0.35 + 0.4 * (hb - 95) / 72), hb, "storm", 1)
        gap = max(0.55, gap * 0.985); hb += gap
    for hb in (171, 172.6, 174.5):
        mix.add(S.heartbeat(0.35), hb, "sfx", 1)
    # storm
    mix.add(S.wind(dur - 126, 1) * ramp(int((dur - 126) * SR), [(0, 0), (6, 0.5), (36, 1.0), (41.6, 1.2), (41.8, 0), (dur - 126, 0)]), 126, "storm", 0.35)
    mix.add(S.rain(42) * ramp(int(42 * SR), [(0, 0), (5, 0.6), (41.6, 1), (41.7, 0), (42, 0)]), 126, "storm", 0.22)
    for tt0, v, cr in [(110.5, .25, False), (116.2, .3, False), (121.4, .35, False), (127.5, .45, True), (131, .55, True), (138.2, .6, True), (143.4, .7, True), (149.3, .7, True), (155.0, .8, True), (159.6, .8, True), (163.6, .9, True)]:
        mix.add(S.thunder(6, cr, v), tt0, "storm", 0.6, S.rng.uniform(-.5, .5), big=0.3)
    mix.add(S.thunder(9, True, 1.0), end + 0.05, "sfx", 0.9, 0, big=0.4)
    # tension cluster strings
    mix.add(S.strings([52, 53, 59, 60], 38, 0.08, att=12, rel=0.3), 130, "storm", 1, 0)
    # end card single low notes
    for i, m in enumerate([40, 47]):
        mix.add(S.piano(m + 12, 3, 0.25), 177 + i * 1.6, "music", 1, 0, big=0.5)
    storm_auto = ramp(mix.n, [(0, 1), (dur, 1)])
    finish(mix, "part1", caps, dur, storm_auto)

def build_part2():
    P = ST.PART2; dur = P["dur"]; mix = Mix(dur); caps = []
    lines_into(mix, P, caps)
    # storm bed 0..100
    mix.add(S.wind(100, 1), 0, "storm", 0.35)
    mix.add(S.rain(100), 0, "storm", 0.22)
    mix.add(S.drone(100, [28, 35, 40], 0.22), 0, "storm", 1)
    mix.add(S.strings([52, 53, 59, 60], 40, 0.07, att=4, rel=2), 0, "storm", 1)
    for tt0, v in [(2.5, .8), (9.6, .9), (17.8, .8), (25.3, .9), (33, 1.0), (47, .6), (66, .5), (76.2, .9), (93, .4)]:
        mix.add(S.thunder(6, True, v), tt0, "storm", 0.6, S.rng.uniform(-.5, .5), big=0.3)
    hb = 2.0; gap = 0.6
    while hb < 40:
        mix.add(S.heartbeat(0.6), hb, "storm", 1); hb += gap
    while hb < 95:
        mix.add(S.heartbeat(0.45 * max(0, 1 - (hb - 40) / 55)), hb, "sfx", 1); gap = min(1.2, gap * 1.03); hb += gap
    # the spark
    for i, m in enumerate([88, 95, 100]):
        mix.add(S.bell(m, 6, 0.12), 40.0 + i * 0.07, "music", 1, (i - 1) * 0.4, big=0.8)
    mix.add(S.shimmer(62, 0.09), 40, "music", 1, 0, big=0.5)
    song_section(mix, 44.0, "chorus", "hum", caps, vel=0.9, accomp=False)
    # celesta doubling of the hum, every other line, plus soft strings
    t = 44.0
    for li, line in enumerate(ST.CHORUS):
        for w, ns, ds in line:
            for n, d in zip(ns, ds):
                if li >= 1: mix.add(S.bell(n + ST.TRANSPOSE + 12, 3, 0.05), t, "music", 1, 0.3, big=0.6)
                t += d * ST.BEAT
    for bi, ch in enumerate(ST.CHORUS_CHORDS):
        cn = S.chord_notes(ch, 3, ST.TRANSPOSE)
        mix.add(S.strings(cn, 4 * ST.BEAT, 0.05 + 0.04 * bi / 16, att=1.5, rel=1.5), 44 + bi * 4 * ST.BEAT, "music", 1, 0, big=0.4)
    # ember crackle 80-92
    n = int(12 * SR); cr = np.zeros(n); pos = S.rng.integers(0, n, 400)
    cr[pos] = S.rng.uniform(-1, 1, 400); cr = S.bp(cr, 1500, 7000) * 0.8 * ramp(n, [(0, 0), (2, 1), (10, 1), (12, 0)])
    mix.add(cr, 80, "sfx", 0.6, 0.2, big=0.3)
    # choir swell 86-101
    for i, ch in enumerate(["F", "C", "Dm", "C"]):
        mix.add(S.choir(S.chord_notes(ch, 3, ST.TRANSPOSE) + [S.chord_notes(ch, 4, ST.TRANSPOSE)[0]], 4.2, 0.22 + 0.06 * i, "a", att=2.5 if i == 0 else 0.8, rel=2.5), 86 + i * 3.6, "music", 1, 0, small=0.2, big=0.6)
    # --- station ---
    mix.add(S.rain(dur - 100, muffled=True) * ramp(int((dur - 100) * SR), [(0, 0), (3, 1), (58, 1), (60, 0)]), 100, "sfx", 0.16)
    tt = S.tarr(60); mix.add(sum(np.sin(2 * np.pi * 120 * k * tt) / k for k in range(1, 6)) * 0.007 * ramp(len(tt), [(0, 0), (2, 1), (58, 1), (60, 0)]), 100, "sfx", 1, -0.3)
    for i in range(6): mix.add(S.footstep(0.22, False), 102.0 + i * 0.75, "sfx", 1, -0.2 + i * 0.03, small=0.5)
    mix.add(S.lp(S.colored_noise(int(1.2 * SR), 0.5), 3000) * np.hanning(int(1.2 * SR)) * 0.08, 107.2, "sfx", 1, small=0.3)  # kneel rustle
    mix.add(S.lp(S.colored_noise(int(1.8 * SR), 0.5), 3500) * np.hanning(int(1.8 * SR)) * 0.12, 138.5, "sfx", 1, -0.1, small=0.3)  # coat
    mix.add(S.lp(S.colored_noise(int(0.8 * SR), 0.3), 5000) * np.hanning(int(0.8 * SR)) * 0.08, 142.5, "sfx", 1, -0.1, small=0.3)  # paper bag
    # soft piano bed under dialogue 104-150
    B = ST.BEAT
    for bi, ch in enumerate(ST.VERSE_CHORDS[:12]):
        cn = S.chord_notes(ch, 3, ST.TRANSPOSE); bt = 104 + bi * 4 * B
        if bt > 151: break
        mix.add(S.piano(cn[0] - 12, 4 * B, 0.18), bt, "music", 1, -0.2, small=0.3, big=0.4)
        for i, m in enumerate([cn[2] + 12, cn[1] + 12]):
            mix.add(S.piano(m, B * 1.8, 0.08), bt + 1 * B + i * 2 * B, "music", 1, 0.2, small=0.3, big=0.4)
    for i in range(6): mix.add(S.footstep(0.2, False), 150.0 + i * 0.8, "sfx", 1, 0.1 + i * 0.07, small=0.5)
    end = song_section(mix, 152.0, "chorus", "sing", caps, vel=1.05)
    mix.add(S.door_creak(1.5, 0.22), 157.0, "sfx", 1, 0.6, small=0.4)
    mix.add(S.rain(dur - 158) * ramp(int((dur - 158) * SR), [(0, 0), (2, 0.8), (40, 0.5), (dur - 160, 0)]), 158, "sfx", 0.14, 0.2)
    for i in range(14): mix.add(S.footstep(0.14 * (1 - i / 14), True), 163.0 + i * 0.8, "sfx", 1, 0.3, small=0.3)
    # choir under reprise, last chords
    for bi, ch in enumerate(ST.CHORUS_CHORDS):
        if bi >= 8:
            mix.add(S.choir(S.chord_notes(ch, 3, ST.TRANSPOSE), 4 * B, 0.12, "o", att=1.2, rel=1.5), 152 + bi * 4 * B, "music", 1, 0, big=0.5)
    fin = S.chord_notes("Am", 3, ST.TRANSPOSE)
    mix.add(S.strings(fin + [fin[0] + 12], 8, 0.1, att=1, rel=4), end, "music", 1, 0, big=0.5)
    mix.add(S.choir(fin + [fin[0] + 12], 7, 0.15, "a", att=1.5, rel=4), end, "music", 1, 0, big=0.6)
    for i, m in enumerate([fin[0] + 24, fin[2] + 24, fin[1] + 36]):
        mix.add(S.bell(m, 6, 0.1), end + 0.5 + i * 0.9, "music", 1, (i - 1) * 0.4, big=0.7)
    storm_auto = ramp(mix.n, [(0, 1), (40, 1), (43, 0.35), (70, 0.3), (80, 0.25), (92, 0.1), (100, 0), (dur, 0)])
    finish(mix, "part2", caps, dur, storm_auto)

if __name__ == "__main__":
    which = sys.argv[1:] or ["1", "2"]
    if "1" in which: build_part1()
    if "2" in which: build_part2()
