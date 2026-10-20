"""Mix the fantasy version: voices in their rooms, synthesized sound design and
the score ducked under speech.

Usage: python mix.py BUILD_DIR SCORE_WAV OUT_WAV
Reuses the sound generators and helpers from audio/mix.py.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "audio"))
from mix import (SR, babble, birdsong, bp, brown, chirp, clink, crackle, db, env_ad, flutter, footstep,  # noqa: E402
                 glass, hp, hum, impact, ir, lp, mixsig, noise, place, reverb, tick, whoosh)

rng = np.random.default_rng(11)
INTERLUDES = ("sword", "cross", "sparrows", "flight")


def thunder(d=3.0, amp=1.0, seed=1):
    r = np.random.default_rng(seed)
    n = int(d * SR)
    x = lp(brown(d), 160) * 3 + lp(r.standard_normal(n), 400) * 0.3
    e = env_ad(n, 0.05, d * 0.9) * (1 + 0.6 * np.sin(np.linspace(0, 9, n)) ** 2)
    return x * e * amp


def wind(d, f0=150, f1=900, amp=1.0, seed=2):
    n = int(d * SR)
    x = bp(brown(d), f0, f1)
    gust = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(np.full(n, 0.11 / SR)) + seed) ** 2
    return x * gust * amp


def shimmer(d=1.6, amp=1.0, f=2000):
    """a rising glassy shimmer (the Light, the stars)"""
    return mixsig(*[chirp(f * k, f * k * 1.5, d * (0.6 + 0.1 * k), 0.4 / k) for k in (1, 1.5, 2, 3)]) * amp


def drip(amp=1.0, f=1400):
    return chirp(f, f * 1.8, 0.07, 1.0) * amp


def word_time(line, w):
    ws = line["text"].split()
    k = next((j for j, x in enumerate(ws) if x.lower().strip(".,;:!?'\"").startswith(w)), 0)
    asr = line.get("words") or []
    if len(asr) >= 2:
        j = min(len(asr) - 1, round(k * (len(asr) - 1) / max(1, len(ws) - 1)))
        return line["start"] + asr[j][0]
    return line["start"] + (line["end"] - line["start"]) * k / max(1, len(ws))


def main():
    build = Path(sys.argv[1])
    tl = json.loads((build / "timeline.json").read_text())
    T = tl["duration"] + 0.5
    n = int(T * SR)
    voice = np.zeros((n, 2))
    sfx = np.zeros((n, 2))
    sc = {s["id"]: s for s in tl["scenes"]}
    ln = {l["id"]: l for l in tl["lines"]}
    st, en = (lambda i: ln[i]["start"]), (lambda i: ln[i]["end"])
    wt = lambda i, w: word_time(ln[i], w)   # noqa: E731

    # ---------------------------------------------------------- voices
    rooms = {
        "glass": (ir(1.4, 0.02, 6000), 0.12), "feast": (ir(1.6, 0.025, 5000), 0.16), "sword": (ir(2.4, 0.03, 4500), 0.2),
        "mirrors": (ir(1.9, 0.02, 6500), 0.18), "cross": (ir(2.4, 0.03, 4500), 0.2), "guild": (ir(1.2, 0.015, 5000), 0.14),
        "sparrows": (ir(0.6, 0.02, 6000), 0.08), "pool": (ir(1.4, 0.02, 5500), 0.16), "flight": (ir(2.0, 0.03, 5000), 0.16),
        "haven": (ir(0.5, 0.012, 6500), 0.1),
    }
    for l in tl["lines"]:
        a, sr = sf.read(build / "lines" / f"{l['id']}.wav", dtype="float32")
        a = resample_poly(a, SR // 24000, 1).astype(np.float64) if sr == 24000 else a.astype(np.float64)
        gain = 1.0
        imp, wet = rooms[l["scene"]]
        if l["who"] == "narrator":
            a = a * 1.05
            imp, wet = ir(1.8, 0.02, 5000), 0.13
        if l["who"] == "ai":
            # the Light: a touch of air and shimmer so it reads as a different kind of presence
            a = a + 0.25 * hp(a, 4000)
            imp, wet = ir(1.4, 0.02, 7500), 0.2
            gain = 0.95
        if l.get("fx") == "pool":
            # heard through water: band-limited, a slow wobble, a wet room
            wob = 1 + 0.08 * np.sin(2 * np.pi * 5.5 * np.arange(len(a)) / SR)
            a = (0.75 * bp(a, 280, 3200, 3) * 1.5 + 0.25 * a) * wob
            imp, wet = ir(1.2, 0.03, 3500), 0.24
        if l.get("fx") == "letter":
            imp, wet = ir(0.4, 0.008, 7000), 0.08       # close and intimate: read in her head
            gain = 0.92
        out = reverb(a, imp, wet) * gain
        place(voice, out, l["start"])

    # ---------------------------------------------------------- sound design
    # 1. the city of glass: wind over the ice, faint glass chimes, a murmuring crowd
    g0, g1 = sc["glass"]["start"], sc["glass"]["end"]
    place(sfx, wind(g1 - g0 + 2, 200, 1400, 1.0, 1), 0.0, db(-34))
    for s in np.arange(0.5, g1, 1.7):
        place(sfx, clink(rng.uniform(3200, 4800), 1.4, 0.5), s + rng.uniform(0, 0.6), db(-44), rng.uniform(-0.7, 0.7))
    place(sfx, babble(en("N3") - st("N3") + 2, 1.0) * env_ad(int((en("N3") - st("N3") + 2) * SR), 0.6, 0.8), st("N3") - 0.6, db(-42))

    # 2. the feast: candles, cutlery, the crack
    f0, f1 = sc["feast"]["start"], sc["feast"]["end"]
    place(sfx, crackle(f1 - f0 + 1, 10, 0.6), f0, db(-44))
    place(sfx, lp(brown(f1 - f0 + 1), 300), f0, db(-46))
    for s in np.arange(f0 + 0.5, st("N6"), 0.6):
        if rng.random() < 0.55:
            place(sfx, clink(rng.uniform(2600, 3400), 0.3, 0.6), s + rng.uniform(0, 0.1), db(-34), rng.uniform(-0.3, 0.3))
    place(sfx, clink(2100, 0.9, 1.0), en("L2") + 0.4, db(-28), 0.0)                       # a goblet set down
    tc = wt("N7", "crack")
    place(sfx, glass(True, 1.0, 21), tc - 0.1, db(-22))
    place(sfx, glass(True, 0.8, 22), tc + 0.5, db(-26))
    place(sfx, lp(brown(3.0), 120) * env_ad(int(3.0 * SR), 0.3, 2.5), tc - 0.2, db(-26))

    # 3. the sword: storm, thunder, the descent, the strike, the ice breaking, the household splitting
    s0, s1 = sc["sword"]["start"], sc["sword"]["end"]
    place(sfx, wind(s1 - s0 + 1, 120, 800, 1.0, 3), s0 - 0.5, db(-40))
    for t in [st("N8") + 1.0, wt("N8", "did") - 0.3]:
        place(sfx, thunder(3.0, 1.0, int(t * 10)), t + 0.15, db(-35))
    strike = en("N8") + 0.05                         # right after "...but a sword" (same moment in music.py, direction.js)
    place(sfx, whoosh(1.2, 1.0, False), strike - 1.0, db(-31))
    place(sfx, impact(1.0), strike, db(-14))
    place(sfx, glass(False, 1.0, 31), strike + 0.05, db(-18))
    place(sfx, thunder(2.6, 1.0, 77), strike, db(-22))
    split = wt("N9", "turn") - 0.2
    place(sfx, lp(brown(3.5), 150) * env_ad(int(3.5 * SR), 0.2, 3.0), split, db(-29))
    place(sfx, glass(True, 1.0, 41), split, db(-31), -0.4)
    place(sfx, glass(True, 0.8, 42), split + 0.4, db(-33), 0.4)
    place(sfx, crackle(4.0, 20, 0.8) * env_ad(int(4 * SR), 0.1, 3.5), split, db(-42))
    place(sfx, wind(s1 - st("N10") + 1, 300, 2400, 1.0, 5), st("N10"), db(-46))

    # 4. the hall of mirrors: a quiet room, ringing glass; the Light arrives with a shimmer
    m0, m1 = sc["mirrors"]["start"], sc["mirrors"]["end"]
    place(sfx, lp(brown(m1 - m0 + 1), 250), m0, db(-48))
    for s in np.arange(m0 + 0.4, st("N12"), 2.3):
        place(sfx, clink(rng.uniform(4000, 5200), 2.0, 0.4), s, db(-46), rng.uniform(-0.6, 0.6))
    place(sfx, shimmer(1.8, 1.0, 1800), wt("N12", "light") - 0.4, db(-30))
    for i in ["L6", "L8"]:
        place(sfx, shimmer(0.8, 0.6, 2400), st(i) - 0.3, db(-40))

    # 5. the cross: mountain wind, the mask shatters
    c0, c1 = sc["cross"]["start"], sc["cross"]["end"]
    place(sfx, wind(c1 - c0 + 1, 150, 1000, 1.0, 6), c0, db(-38))
    brk = wt("N13", "lose")                         # "...will lose it": the mask shatters
    place(sfx, glass(False, 1.0, 51), brk - 0.1, db(-17))
    place(sfx, impact(0.6), brk - 0.1, db(-24))
    place(sfx, shimmer(2.5, 1.0, 1600), brk + 0.4, db(-34))

    # 6. the guildhall: lantern hum, tools, voices; then the storm
    k0, k1 = sc["guild"]["start"], sc["guild"]["end"]
    storm = en("N16")
    kd = k1 - k0 + 0.2
    grow = np.clip((np.arange(int(kd * SR)) / SR - (storm - k0)) / 2.5, 0, 1)
    swell = 1 + grow * 4.5
    flick = lambda t: 0.6 + 0.4 * (np.sin(t * 37) * np.sin(t * 11.3) > 0.7)   # noqa: E731
    place(sfx, hum(kd, 110, 1.0, flick) * swell, k0, db(-34))
    place(sfx, babble(kd, 1.0) * swell, k0, db(-40))
    for s in np.arange(k0 + 0.3, k1, 0.37):
        if rng.random() < 0.6:
            place(sfx, tick(rng.random() < 0.5) * (1 + 3 * grow[min(len(grow) - 1, int((s - k0) * SR))]), s, db(-36), rng.uniform(-0.6, 0.6))
    ring = np.sin(2 * np.pi * 5600 * np.arange(int(kd * SR)) / SR) * grow ** 2
    place(sfx, ring, k0, db(-30))

    # 7. the sparrows: market, a coin, birds, the flock
    p0, p1 = sc["sparrows"]["start"], sc["sparrows"]["end"]
    pd = p1 - p0 + 0.5
    place(sfx, babble(wt("N18", "yet") - p0, 1.0), p0, db(-44))
    place(sfx, birdsong(pd, 1.2, 4), p0, db(-34), -0.4)
    place(sfx, birdsong(pd, 0.8, 5), p0, db(-38), 0.5)
    place(sfx, clink(3600, 0.8, 1.0), wt("N17", "coin") - 0.1, db(-28), 0.2)
    place(sfx, whoosh(0.9, 0.6, False), wt("N18", "yet") + 0.4, db(-38))
    place(sfx, shimmer(2.0, 1.0, 1500), wt("N18", "outside") - 0.2, db(-32))
    place(sfx, shimmer(1.6, 0.8, 2600), wt("N19", "hairs") - 0.2, db(-34))
    for k in range(12):
        place(sfx, flutter(0.7, 1.0), st("N20") + 0.3 + k * 0.16, db(-28 - k), rng.uniform(-0.6, 0.6))
    place(sfx, whoosh(2.0, 1.0, True), st("N20") + 0.2, db(-32))

    # 8. the scrying pool: drips and a lapping hush
    q0, q1 = sc["pool"]["start"], sc["pool"]["end"]
    place(sfx, lp(brown(q1 - q0 + 1), 400) * (0.7 + 0.3 * np.sin(np.linspace(0, (q1 - q0) * 2, int((q1 - q0 + 1) * SR)))[:, None].ravel()), q0, db(-44))
    for s in np.arange(q0 + 0.7, q1, 2.1):
        place(sfx, drip(1.0, rng.uniform(1100, 1700)), s + rng.uniform(0, 0.8), db(-36), rng.uniform(-0.5, 0.5))
    for i in ["L11", "L14"]:
        place(sfx, shimmer(1.0, 0.6, 900), st(i) - 0.5, db(-36))

    # 9. the road: snow wind at the gate, footsteps on the bridge, dawn birds
    r0, r1 = sc["flight"]["start"], sc["flight"]["end"]
    rd = r1 - r0 + 1.5
    place(sfx, wind(rd, 200, 1500, 1.0, 9) * np.linspace(1, 0.3, int(rd * SR)), r0 - 0.5, db(-34))
    for k, s in enumerate(np.arange(r0 + 0.3, wt("N23", "stands"), 0.55)):
        place(sfx, footstep(1.0), s, db(-34), -0.15 if k % 2 else 0.15)
    place(sfx, birdsong(r1 - wt("N23", "stands") + 1, 0.8, 12), wt("N23", "stands"), db(-38), 0.4)
    place(sfx, shimmer(1.4, 0.7, 2200), st("L16") - 0.4, db(-38))

    # 10. the next town: birds, a soft room, a sparrow arriving, a letter unrolled
    e0, e1 = sc["haven"]["start"], tl["duration"]
    ed = e1 - e0 + 0.5
    place(sfx, birdsong(ed, 0.6, 14), e0, db(-38), 0.5)
    place(sfx, lp(brown(ed), 400) * 0.6, e0, db(-48))
    place(sfx, flutter(0.6), wt("N26", "sparrow") - 0.2, db(-28), 0.4)
    place(sfx, bp(noise(0.5), 1500, 6000) * env_ad(int(0.5 * SR), 0.05, 0.3), st("L19") - 0.6, db(-36))

    # ---------------------------------------------------------- score, ducked under the voices
    mus, msr = sf.read(sys.argv[2], dtype="float64")
    if msr != SR:
        mus = resample_poly(mus, SR, msr, axis=0)
    mus = np.pad(mus, ((0, max(0, n - len(mus))), (0, 0)))[:n]
    v = np.abs(voice).mean(1)
    win = int(0.05 * SR)
    venv = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, mode="same"))
    act = (venv > db(-42)).astype(float)
    sm = np.zeros(n)
    a_k, r_k = 1 - np.exp(-1 / (0.06 * SR)), 1 - np.exp(-1 / (0.5 * SR))
    stt, step = 0.0, 64
    for i in range(0, n, step):
        x = act[i]
        stt += ((a_k if x > stt else r_k) * step) * (x - stt)
        stt = min(1.0, max(0.0, stt))
        sm[i:i + step] = stt
    music_gain = np.full(n, db(9.0))
    duck = np.full(n, db(-8.0))
    for s in tl["scenes"]:
        i0, i1 = int(s["start"] * SR), int(s["end"] * SR)
        if s["id"] in INTERLUDES:
            music_gain[i0:i1] = db(6.5)
            duck[i0:i1] = db(-11.0)
    gain = music_gain * (1 - sm * (1 - duck))
    music = mus * gain[:, None]

    mix = voice + sfx * db(1.5) + music
    bg = sfx * db(1.5) + music
    ratios = []
    for l in tl["lines"]:
        i0, i1 = int(l["start"] * SR), int(l["end"] * SR)
        vr = np.sqrt(np.mean(voice[i0:i1] ** 2)) + 1e-9
        br = np.sqrt(np.mean(bg[i0:i1] ** 2)) + 1e-9
        ratios.append((round(20 * np.log10(vr / br), 1), l["id"], l["scene"]))
    ratios.sort()
    print("speech-to-background dB (lowest first):", ratios[:8])
    print("median:", ratios[len(ratios) // 2][0])
    Path(sys.argv[3] + ".snr.json").write_text(json.dumps(ratios))
    peak = np.abs(mix).max()
    if peak > 0.98:
        mix *= 0.98 / peak
    sf.write(sys.argv[3], mix.astype(np.float32), SR, subtype="FLOAT")
    print(f"wrote {sys.argv[3]}  {T:.1f}s  peak {peak:.2f}")


if __name__ == "__main__":
    main()
