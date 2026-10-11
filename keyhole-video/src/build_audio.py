"""Build the timeline (shot/line/marker timings), mouth tracks, and the final audio mix."""
import json, os, re, sys
import numpy as np
import soundfile as sf
from scipy import signal

import tts
import audio_lib as A
from script import SHOTS, VOICES
import music

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build")
os.makedirs(OUT, exist_ok=True)
FPS = 24
SR = A.SR

# --------------------------------------------------------------- visemes
V_CLOSED = (0.0, 1.0, 0.0)
VIS = {}
for c in "pbm":
    VIS[c] = (0.0, 0.95, 0.0)
for c in "fv":
    VIS[c] = (0.12, 1.0, 0.0)
for c in "θð":
    VIS[c] = (0.22, 1.0, 0.0)
for c in "tdnlszɾ":
    VIS[c] = (0.22, 1.08, 0.0)
for c in "ʃʒʧʤ":
    VIS[c] = (0.25, 0.8, 0.6)
for c in "kgŋ":
    VIS[c] = (0.3, 1.0, 0.0)
VIS["ɹ"] = (0.25, 0.85, 0.5)
VIS["w"] = (0.15, 0.7, 0.9)
VIS["j"] = (0.22, 1.15, 0.0)
VIS["h"] = (0.35, 1.0, 0.0)
for c in "ɑa":
    VIS[c] = (0.9, 1.0, 0.0)
VIS["æ"] = (0.75, 1.15, 0.0)
for c in "ɐʌə":
    VIS[c] = (0.5, 1.0, 0.0)
for c in "ɛe":
    VIS[c] = (0.55, 1.12, 0.0)
for c in "ɪiᵻ":
    VIS[c] = (0.3, 1.25, 0.0)
for c in "ʊu":
    VIS[c] = (0.3, 0.75, 0.85)
for c in "ɔo":
    VIS[c] = (0.6, 0.8, 0.7)
for c in "ɜɝɚ":
    VIS[c] = (0.4, 0.95, 0.35)
PUNCT = set(",.!?;:—…\"'()")


def viseme_track(phones, dur, audio24):
    """Per-frame (open, wide, round, energy) for a clip of length dur seconds."""
    nf = int(np.ceil(dur * FPS)) + 1
    # resolve modifiers: stress marks & length marks inherit neighbours
    seq = []
    last = V_CLOSED
    for pi, (c, t0, t1) in enumerate(phones):
        if c in VIS:
            last = VIS[c]
            seq.append((t0, t1, last))
        elif c == "ː":
            seq.append((t0, t1, last))
        elif c in PUNCT:
            seq.append((t0, t1, V_CLOSED))
            last = V_CLOSED
        elif c == " ":
            nxt = next((VIS[c2] for c2, _, _ in phones[pi + 1:] if c2 in VIS), V_CLOSED)
            seq.append((t0, t1, nxt))
        else:  # stress marks etc.: keep previous briefly
            seq.append((t0, t1, last))
    # sample at 120 Hz then smooth and decimate
    hz = 120
    ns = int(dur * hz) + 2
    o = np.zeros(ns); w = np.ones(ns); r = np.zeros(ns)
    for t0, t1, v in seq:
        t0, t1 = max(0.0, t0 - 0.03), max(0.0, t1 - 0.03)
        i0, i1 = int(t0 * hz), max(int(t0 * hz) + 1, int(t1 * hz))
        o[i0:i1] = v[0]; w[i0:i1] = v[1]; r[i0:i1] = v[2]
    k = np.hanning(9); k /= k.sum()
    o = np.convolve(o, k, "same"); w = np.convolve(w, k, "same"); r = np.convolve(r, k, "same")
    # energy envelope from audio
    hop = 24000 // hz
    nn = len(audio24) // hop
    e = np.sqrt((audio24[: nn * hop].reshape(nn, hop) ** 2).mean(1)) if nn else np.zeros(1)
    e = np.pad(e, (0, max(0, ns - len(e))))[:ns]
    e = e / (np.percentile(e[e > 0], 95) + 1e-6) if np.any(e > 0) else e
    e = np.clip(e, 0, 1.2)
    e = np.convolve(e, k, "same")
    o = o * (0.55 + 0.6 * np.clip(e, 0, 1))
    o = np.where(e < 0.05, o * e / 0.05, o)
    idx = (np.arange(nf) / FPS * hz).astype(int).clip(0, ns - 1)
    return np.stack([o[idx], w[idx], r[idx], e[idx]], 1)


def strip_stress(s):
    return s.replace("ˈ", "").replace("ˌ", "")


def to48(a24):
    return signal.resample_poly(a24, 2, 1)


def rms_norm(a, target_db=-20.0):
    act = a[np.abs(a) > 0.02 * np.abs(a).max()] if len(a) else a
    r = np.sqrt((act ** 2).mean()) if len(act) else 1
    return a * (10 ** (target_db / 20) / (r + 1e-9))


# --------------------------------------------------------------- lines
def render_line(who, text, speed):
    """Return dict with audio24 (normalized), visemes (frames), caption segments, duration."""
    voice, vspeed = VOICES[who]
    sp = speed if speed is not None else vspeed
    parts = re.split(r"\[p([\d.]+)\]", text)
    chunks, pauses = parts[0::2], [float(p) for p in parts[1::2]]
    pieces = []
    phones_all = []
    caps = []
    t = 0.0
    bleeps = []
    for ci, ch in enumerate(chunks):
        bwords = re.findall(r"\[B:(\w+)\]", ch)
        spoken = re.sub(r"\[B:(\w+)\]", r"\1", ch).strip()
        captxt = re.sub(r"\[B:(\w+)\]", "$#!%", ch).strip()
        a, ph, phs = tts.synth(spoken, voice, sp)
        # locate bleeps
        chars = [c for c, _, _ in ph]
        stripped, mapidx = [], []
        for i, c in enumerate(chars):
            if c not in "ˈˌ":
                stripped.append(c); mapidx.append(i)
        stripped = "".join(stripped)
        pos = 0
        for bw in bwords:
            target = strip_stress(tts.phonemize(bw)).strip(" .,!?")
            j = stripped.find(target, pos)
            if j < 0:
                j = stripped.find(target[:2], pos)
                L = 3
            else:
                L = len(target)
            i0, i1 = mapidx[j], mapidx[min(j + L - 1, len(mapidx) - 1)]
            # the word's onset often starts inside the preceding gap token: start mid previous phone
            k = i0 - 1
            while k >= 0 and ph[k][0] in " ˈˌ":
                k -= 1
            bt0 = max(ph[i0][1] - 0.3, ph[k][1] + 0.2 * (ph[k][2] - ph[k][1]) - 0.03) if k >= 0 else ph[i0][1] - 0.08
            bt1 = ph[i1][2] + 0.04
            bleeps.append((t + bt0, t + bt1))
            pos = j + L
        phones_all += [(c, t0 + t, t1 + t) for c, t0, t1 in ph]
        caps.append((t, captxt))
        pieces.append(a)
        t += len(a) / 24000
        if ci < len(pauses):
            pieces.append(np.zeros(int(pauses[ci] * 24000), dtype=np.float32))
            t += pauses[ci]
    audio = np.concatenate(pieces)
    audio = rms_norm(audio, -20.0)
    # apply bleeps
    for b0, b1 in bleeps:
        i0, i1 = int(b0 * 24000), int(b1 * 24000)
        audio[i0:i1] = 0
    dur = len(audio) / 24000
    vis = viseme_track(phones_all, dur, audio)
    return dict(audio=audio, vis=vis, caps=caps, dur=dur, bleeps=bleeps)


# --------------------------------------------------------------- laughs
_SYL = {}


def laugh_syllables(voice):
    key = json.dumps(voice, sort_keys=True)
    if key not in _SYL:
        syl = []
        for ph, spd in [("hˈɑː", 1.0), ("hˈæ", 1.05), ("hˈʌ", 1.0), ("hˈɑː", 1.15), ("hˈɛ", 1.1)]:
            a, _, _ = tts.synth(None, voice, spd, phonemes=ph)
            syl.append(rms_norm(a, -20.0))
        _SYL[key] = syl
    return _SYL[key]


LAUGH_VOICE = {
    "kidme": ("af_heart", 1.32),
    "kiddanny": ("am_puck", 1.5),
    "me": ("af_heart", 1.0),
    "danny": ({"am_michael": 0.7, "am_onyx": 0.3}, 1.0),
    "f1": ("af_nicole", 1.0),
    "f2": ("am_liam", 1.0),
    "anger_d": ("am_onyx", 0.88),
}


def laugh(who, kind, dur, seed):
    v, p = LAUGH_VOICE[who]
    syl = laugh_syllables(v)
    a, onsets = A.make_laugh(syl, 24000, kind=kind, dur=dur, seed=seed, pitch=p)
    return a, onsets


def laugh_track(onsets, dur, base=0.3):
    nf = int(np.ceil(dur * FPS)) + 1
    t = np.arange(nf) / FPS
    o = np.full(nf, base)
    for on in onsets:
        dt = t - on
        o += np.where(dt >= 0, np.exp(-dt / 0.09) * (1 - np.exp(-dt / 0.02)), 0) * 0.9
    o = np.clip(o, 0, 1)
    w = np.full(nf, 1.2)
    r = np.zeros(nf)
    e = np.clip(o, 0, 1)
    return np.stack([o, w, r, e], 1)


# laugh sfx definitions: list of (who, kind, dur, offset, gain)
LAUGH_SFX = {
    "kid_laughs": [("kidme", "kid", 2.7, 0.0, 0.9), ("kiddanny", "kid", 2.9, 0.06, 0.95)],
    "kid_giggle": [("kidme", "chuckle", 0.9, 0.0, 0.6), ("kiddanny", "chuckle", 1.0, 0.12, 0.6)],
    "friends_chuckle": [("f1", "chuckle", 0.8, 0.0, 0.5), ("f2", "chuckle", 0.9, 0.12, 0.5),
                        ("danny", "chuckle", 0.7, 0.05, 0.5)],
    "group_laugh": [("me", "adult", 2.6, 0.05, 0.75), ("danny", "adult", 1.5, 0.0, 0.85),
                    ("f1", "adult", 2.9, 0.1, 0.7), ("f2", "adult", 2.3, 0.25, 0.65)],
    "soft_laughs": [("me", "soft", 2.2, 0.1, 0.55), ("danny", "soft", 2.5, 0.0, 0.6)],
}


def build():
    lines, laughs, sfx, cues, shots = [], [], [], [], []
    marks = {}
    t = 0.0
    for shot_name, events in SHOTS:
        st0 = t
        for ev in events:
            kind = ev[0]
            if kind == "wait":
                t += ev[1]
            elif kind == "mark":
                marks[ev[1]] = t
            elif kind == "music":
                cues.append((ev[1], t))
            elif kind == "sfx":
                sfx.append((ev[1], t))
            elif kind == "say":
                who, text, opts = ev[1], ev[2], ev[3]
                L = render_line(who, text, opts.get("speed"))
                lines.append(dict(who=who, text=text, t0=t, t1=t + L["dur"], L=L))
                t += L["dur"]
        shots.append(dict(name=shot_name, t0=st0, t1=t))
    total = t
    print(f"total duration {total:.2f}s  ({total/60:.2f} min)")

    # ---- dialogue bus
    nS = int((total + 3) * SR)
    dia = np.zeros((nS, 2))
    lau = np.zeros((nS, 2))
    sfxb = np.zeros((nS, 2))
    tracks = {}
    nF = int(np.ceil(total * FPS)) + 2

    def track(who):
        if who not in tracks:
            tr = np.zeros((nF, 4)); tr[:, 1] = 1.0
            tracks[who] = tr
            tracks[who + "_laugh"] = np.zeros(nF)
        return tracks[who]

    PAN = {"danny": 0.12, "me": -0.08, "teacher": 0.0, "emb": -0.1, "doubt": 0.1, "anger": 0.12, "bored": -0.12}
    for ln in lines:
        L = ln["L"]
        a48 = to48(L["audio"])
        if ln["who"] == "narr":
            a48 = A.lowpass(a48, 9000)
        A.place(dia, a48, ln["t0"], 1.0, PAN.get(ln["who"], 0.0))
        # bleeps go on sfx bus so they are not voice-processed
        for b0, b1 in L["bleeps"]:
            A.place(sfxb, A.sfx_bleep(b1 - b0), ln["t0"] + b0, 0.9, PAN.get(ln["who"], 0.0))
        if ln["who"] != "narr":
            tr = track(ln["who"])
            f0 = int(round(ln["t0"] * FPS))
            v = L["vis"]
            n = min(len(v), nF - f0)
            tr[f0:f0 + n] = v[:n]

    laugh_spans = []
    seed = 100
    for name, tt in sfx:
        if name in LAUGH_SFX:
            for who, k, d, off, g in LAUGH_SFX[name]:
                seed += 1
                a, ons = laugh(who, k, d, seed)
                A.place(lau, a, tt + off, g * 0.9, PAN.get(who, 0.0) + (0.25 if who in ("f1",) else -0.25 if who == "f2" else 0))
                tr = track(who)
                f0 = int(round((tt + off) * FPS))
                lt = laugh_track(ons, len(a) / SR, base=0.25 if k != "soft" else 0.15)
                n = min(len(lt), nF - f0)
                tr[f0:f0 + n] = np.maximum(tr[f0:f0 + n], lt[:n])
                # laugh intensity curve
                li = tracks[who + "_laugh"]
                ramp = np.ones(n)
                fr = int(0.15 * FPS)
                ramp[:fr] = np.linspace(0, 1, fr)[: n]
                ramp[-fr:] = np.minimum(ramp[-fr:], np.linspace(1, 0, fr))
                li[f0:f0 + n] = np.maximum(li[f0:f0 + n], ramp * (1.0 if k in ("kid", "adult") else 0.6 if k == "chuckle" else 0.45))
                laugh_spans.append(dict(who=who, t0=tt + off, t1=tt + off + len(a) / SR, kind=k))
        elif name == "echo_laugh":
            # distant echo of the backyard laughter + anger's own deep chuckle
            mixdown = np.zeros(int(4 * SR))
            for who, k, d, off, g in LAUGH_SFX["group_laugh"]:
                seed += 1
                a, _ = laugh(who, k, d, seed)
                j = int(off * SR)
                mixdown[j:j + len(a)] += a[: len(mixdown) - j] * g
            mixdown = A.lowpass(mixdown, 1800)
            wet = A.reverb(mixdown, wet=0.85, decay=3.2, tone=2500, predelay=0.08)
            A.place(lau, wet, tt, 0.35)
            seed += 1
            a, ons = laugh("anger_d", "chuckle", 1.1, seed)
            A.place(lau, a, tt + 0.9, 0.55)
            tr = track("anger_d")
            f0 = int(round((tt + 0.9) * FPS))
            lt = laugh_track(ons, len(a) / SR, base=0.2)
            n = min(len(lt), nF - f0)
            tr[f0:f0 + n] = np.maximum(tr[f0:f0 + n], lt[:n])
            li = tracks["anger_d_laugh"]
            li[f0:f0 + n] = np.maximum(li[f0:f0 + n], 0.6)
            laugh_spans.append(dict(who="anger_d", t0=tt + 0.9, t1=tt + 0.9 + len(a) / SR, kind="chuckle"))
        elif name == "snort":
            A.place(sfxb, A.sfx_snort(1.6, 1), tt, 0.8, 0.1)
        elif name == "snort_adult":
            A.place(sfxb, A.sfx_snort(1.0, 2), tt, 0.8, 0.25)
        elif name == "sizzle_flip":
            A.place(sfxb, A.sfx_flip(), tt, 0.7, 0.15)
            A.place(sfxb, A.sfx_sizzle(1.8, 21), tt + 0.05, 0.9, 0.15)
        elif name == "crickets_short":
            A.place(sfxb, A.sfx_crickets(4.0, 31, 1.3), tt, 1.6)
        elif name == "crickets_long":
            pass  # handled by ambience bed
        elif name == "alarm":
            A.place(sfxb, A.sfx_alarm(1.8), tt, 0.9)
        elif name == "knuckles":
            A.place(sfxb, A.sfx_knuckles(), tt, 0.9, 0.1)
        elif name == "whoosh":
            A.place(sfxb, A.sfx_whoosh(0.9), tt, 0.9)
        elif name == "door_creak":
            A.place(sfxb, A.reverb(A.sfx_creak(1.7), 0.4, 2.5, 3000), tt, 0.6)
        elif name == "sniff":
            A.place(sfxb, A.sfx_sniff(), tt, 0.9, 0.1)

    # ---- ambience beds by shot set
    amb = np.zeros((nS, 2))
    for sh in shots:
        nm, s0, s1 = sh["name"], sh["t0"], sh["t1"]
        d = s1 - s0
        if nm.startswith("yard"):
            if nm == "yard_silence":
                continue
            bed = A.lowpass(A.sfx_sizzle(d + 0.3, int(s0 * 10)), 7000) * 0.14
            A.place(amb, bed, s0, 1.0, 0.2)
        elif nm.startswith("porch") or nm == "sky":
            bed = A.sfx_crickets(d + 0.3, int(s0 * 10), 0.8) * 0.9
            A.place(amb, bed, s0, 1.0)
        elif nm.startswith("fort"):
            rng = np.random.default_rng(int(s0))
            tt_ = A.t_axis(d + 0.3)
            wind = A.lowpass(rng.normal(0, 1, len(tt_)), 400) * 0.06 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * tt_))
            crack = A.sfx_sizzle(d + 0.3, int(s0)) * 0.12
            A.place(amb, A.lowpass(crack, 3500) + wind, s0, 1.0)
        elif nm.startswith("bridge"):
            tt_ = A.t_axis(d + 0.3)
            hum = (np.sin(2 * np.pi * 55 * tt_) + 0.4 * np.sin(2 * np.pi * 110 * tt_)) * 0.025
            A.place(amb, hum, s0, 1.0)
            rng = np.random.default_rng(int(s0))
            for k in range(int(d * 1.2)):
                bt = s0 + rng.uniform(0, d)
                f = rng.choice([1320, 1760, 1568, 2093])
                tb = A.t_axis(0.09)
                A.place(amb, np.sin(2 * np.pi * f * tb) * np.exp(-tb * 30) * 0.05, bt, 1.0, rng.uniform(-0.6, 0.6))

    # ---- music
    mus = music.render_cues(cues, total, marks)

    # ---- ducking
    voice_env = np.abs(dia).max(1) + 0.6 * np.abs(lau).max(1)
    win = int(0.02 * SR)
    ve = np.sqrt(np.convolve(voice_env ** 2, np.ones(win) / win, "same"))
    act = (ve > 0.01).astype(float)
    # attack 60ms, release 500ms one-pole
    duck = signal.lfilter([1 - np.exp(-1 / (0.5 * SR))], [1, -np.exp(-1 / (0.5 * SR))], act)
    duck = np.maximum(duck, signal.lfilter([1 - np.exp(-1 / (0.06 * SR))], [1, -np.exp(-1 / (0.06 * SR))], act) * 0.0)
    mg = 1.0 - 0.42 * np.clip(duck, 0, 1)
    mus = mus[:nS] * mg[:, None]

    dia_r = A.reverb(dia, wet=0.07, decay=0.6, tone=6000, predelay=0.005)[:nS]
    lau_r = A.reverb(lau, wet=0.12, decay=0.8, tone=5000)[:nS]
    mix = dia_r + lau_r + sfxb + amb * 0.9 + mus
    mix = mix[: int((total + 0.05) * SR)]
    peak = np.abs(mix).max()
    mix = mix / peak * 0.89
    sf.write(os.path.join(OUT, "mix.wav"), mix.astype(np.float32), SR)
    sf.write(os.path.join(OUT, "dialogue.wav"), (dia_r[: len(mix)] / peak * 0.89).astype(np.float32), SR)
    sf.write(os.path.join(OUT, "music.wav"), (mus[: len(mix)] / peak * 0.89).astype(np.float32), SR)

    # ---- captions
    COLORS = {"narr": "narr"}
    caps = []
    for ln in lines:
        segs = ln["L"]["caps"]
        group = []
        def flush(group, end):
            if not group:
                return
            for gi, (st, txt) in enumerate(group):
                acc = " ".join(x[1] for x in group[: gi + 1])
                ce = group[gi + 1][0] if gi + 1 < len(group) else end
                caps.append(dict(who=ln["who"], t0=ln["t0"] + st, t1=ln["t0"] + ce, text=acc))
        cur_len = 0
        for i, (st, txt) in enumerate(segs):
            if group and cur_len + len(txt) > 44:
                flush(group, st - 0.05)
                group, cur_len = [], 0
            group.append((st, txt)); cur_len += len(txt) + 1
        flush(group, ln["L"]["dur"] + 0.35)
    # extend each caption to the next one (max +0.6 s) for readability
    caps.sort(key=lambda c: c["t0"])
    for i, c in enumerate(caps):
        nxt = caps[i + 1]["t0"] if i + 1 < len(caps) else c["t1"] + 0.6
        c["t1"] = min(max(c["t1"], c["t0"] + 0.6), nxt - 0.02, c["t1"] + 0.6) if nxt > c["t1"] else min(c["t1"], nxt - 0.02)

    tl = dict(fps=FPS, total=total, shots=shots, marks=marks,
              lines=[dict(who=l["who"], text=l["text"], t0=l["t0"], t1=l["t1"], chunks=[l["t0"] + st for st, _ in l["L"]["caps"]], bleeps=[[l["t0"] + a, l["t0"] + b] for a, b in l["L"]["bleeps"]]) for l in lines],
              laughs=laugh_spans, sfx=[dict(name=n, t=t) for n, t in sfx], cues=[dict(name=n, t=t) for n, t in cues],
              captions=caps)
    with open(os.path.join(OUT, "timeline.json"), "w") as f:
        json.dump(tl, f, indent=1)
    np.savez(os.path.join(OUT, "tracks.npz"), **tracks)
    for s in shots:
        print(f"  {s['t0']:7.2f} - {s['t1']:7.2f}  ({s['t1']-s['t0']:5.2f})  {s['name']}")


if __name__ == "__main__":
    build()
