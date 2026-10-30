#!/usr/bin/env python3
"""Final mix for "The Family Inside".

    python3 audio/mix.py [cues.json] [--music path.wav]  -> build/mix.wav, build/mix_report.txt

Default cue path build/cues.json, falling back to build/cues_test.json.
Inputs: build/schedule.json (+ voice wavs), build/music.wav (optional), audio/sfx.py.

Chain
  dialogue : per-line level match (+-4 dB max), scene-dependent synthetic room
             reverb (narrator always intimate/near-dry), centred.
  music    : set ~6 LU under dialogue, sidechain-ducked -7 dB from the dialogue
             envelope (120 ms attack, 400 ms release, 150 ms look-ahead).
  sfx/amb  : cue times / regions with gain + constant-power pan; ambience regions
             get ~1 s equal-power fades centred on their edges.
  safety   : any line where dialogue RMS < bed RMS + 11 dB gets the bed pulled
             down locally (smooth ramps) so speech always sits on top.
  bus      : gentle RMS compressor (2:1, soft knee), BS.1770-4 loudness
             normalise to -16 LUFS, 4x-oversampled look-ahead true-peak limiter
             (ceiling -1.7 dBTP), TPDF-dithered 16-bit output.
Deterministic: all noise from seeded RNGs.
"""
import json
import os
import sys
import time
import subprocess

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build")
sys.path.insert(0, HERE)
import sfx as SFXLIB  # noqa: E402

SR = 48000
TARGET_LUFS = -16.0
TP_CEIL_DB = -1.7          # limiter ceiling (spec: <= -1.5 dBTP)
VOICE_TARGET_DB = -20.0    # active RMS per line before bus processing
MUSIC_REL_LU = -6.0        # music loudness relative to dialogue loudness (unducked)
DUCK_DB = -7.0
DUCK_ATT, DUCK_REL, DUCK_LOOK = 0.120, 0.400, 0.150
SFX_BUS = 0.5              # sfx one-shots are peak -6 dBFS * cue gain * this
AMB_BUS = 1.0
MIN_MARGIN_DB = 11.0       # safety target (spec ~10 dB)
AMB_XFADE = 1.0

# room presets: rt60 (s), wet gain, predelay (s), tail lowpass (Hz), early-ref density
ROOMS = {
    "kitchen":  dict(rt=0.35, wet=0.14, pre=0.006, lp=6000, er=6),
    "hearth":   dict(rt=0.75, wet=0.20, pre=0.014, lp=4200, er=8),
    "memory":   dict(rt=1.70, wet=0.36, pre=0.030, lp=5000, er=10),
    "reflect":  dict(rt=0.28, wet=0.05, pre=0.004, lp=5000, er=4),
    "small":    dict(rt=0.40, wet=0.13, pre=0.007, lp=5500, er=6),
    "end":      dict(rt=0.85, wet=0.18, pre=0.016, lp=4500, er=8),
    "narrator": dict(rt=0.28, wet=0.05, pre=0.004, lp=5000, er=4),
}


def room_for_scene(name):
    n = (name or "").lower()
    for pre, room in (("kitchen", "kitchen"), ("hearth", "hearth"), ("memory", "memory"),
                      ("reflect", "reflect"), ("porch", "small"), ("nanahouse", "small"),
                      ("nana", "small"), ("end", "end")):
        if n.startswith(pre):
            return room
    return "kitchen"


def make_ir(room, seed):
    p = ROOMS[room]
    rng = np.random.default_rng(1000 + seed)
    n = int((p["pre"] + p["rt"] * 1.2) * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    i0 = int(p["pre"] * SR)
    # early reflections
    for k in range(p["er"]):
        d = i0 + int(rng.uniform(0.002, 0.04 + p["rt"] * 0.03) * SR)
        if d < n:
            ir[d, rng.integers(0, 2)] += rng.uniform(0.2, 0.6) * (-1) ** k
    # late tail: decorrelated noise, exponential decay (60 dB over rt), darker over time
    tail = rng.standard_normal((n, 2))
    env = np.exp(-6.91 * np.maximum(t - p["pre"], 0) / p["rt"]) * (t >= p["pre"])
    env *= np.minimum(1, np.maximum(t - p["pre"], 0) / 0.01)
    bright = signal.sosfilt(signal.butter(2, p["lp"], "lowpass", fs=SR, output="sos"), tail, axis=0)
    dark = signal.sosfilt(signal.butter(2, p["lp"] * 0.35, "lowpass", fs=SR, output="sos"), tail, axis=0)
    mixw = np.clip(t / max(p["rt"], 1e-3), 0, 1)[:, None]
    ir += (bright * (1 - mixw) + dark * mixw) * env[:, None]
    ir = signal.sosfilt(signal.butter(1, 180, "highpass", fs=SR, output="sos"), ir, axis=0)
    ir /= np.sqrt(np.sum(ir ** 2) / 2) + 1e-12
    return ir * p["wet"]


# ------------------------------------------------------------------ loudness
def k_weight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x):
    """BS.1770-4 integrated loudness (gated). x: (n,) or (n,2)."""
    x = x if x.ndim == 2 else x[:, None]
    y = k_weight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(y) < blk:
        return -np.inf
    p = np.cumsum(np.concatenate([np.zeros((1, y.shape[1])), y ** 2]), axis=0)
    starts = np.arange(0, len(y) - blk + 1, hop)
    z = ((p[starts + blk] - p[starts]) / blk).sum(1)
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    g = z[lk > -70]
    if len(g) == 0:
        return -np.inf
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = z[(lk > -70) & (lk > rel)]
    return -0.691 + 10 * np.log10(g2.mean()) if len(g2) else -np.inf


def os_peaks(x, factor=4, chunk=SR * 10):
    """Per-sample 4x-oversampled absolute peak (max over channels)."""
    n = len(x)
    out = np.zeros(n, dtype=np.float32)
    pad = 64
    for s in range(0, n, chunk):
        a, b = max(0, s - pad), min(n, s + chunk + pad)
        seg = x[a:b]
        up = signal.resample_poly(seg, factor, 1, axis=0)
        pk = np.abs(up).max(axis=1).reshape(-1, factor).max(axis=1)
        pk = np.maximum(pk, np.abs(seg).max(axis=1))
        out[s:min(n, s + chunk)] = pk[s - a:s - a + min(chunk, n - s)]
    return out


def true_peak_db(x):
    return 20 * np.log10(os_peaks(x).max() + 1e-12)


def limiter(x, ceil_db=TP_CEIL_DB, look=0.0015, release=0.08):
    ceil = 10 ** (ceil_db / 20)
    pk = os_peaks(x).astype(np.float64)
    req = np.minimum(1.0, ceil / (pk + 1e-12))
    if req.min() >= 1.0:
        limiter.stats = (0.0, 0.0)
        return x, 0.0
    w = int(look * SR)
    g = minimum_filter1d(req, 2 * w + 1)              # look-ahead: gain already down at the peak
    r = int(release * SR)
    gh = minimum_filter1d(g, r, origin=(r - 1) // 2)  # hold for `release` after each peak
    gh = np.minimum(uniform_filter1d(gh, r // 2), g)  # soften the recovery
    g = uniform_filter1d(gh, w + 1)                   # smooth attack (stays <= required gain)
    limiter.stats = (float((g < 10 ** (-1 / 20)).mean() * 100), float((g < 10 ** (-3 / 20)).mean() * 100))
    return x * g[:, None], 20 * np.log10(g.min())


def compressor(x, thr_db=-21.0, ratio=2.0, knee=6.0, att=0.015, rel=0.25):
    hop = int(0.005 * SR)
    m = (x ** 2).mean(1)
    nfr = len(m) // hop + 1
    mp = np.concatenate([m, np.zeros(nfr * hop - len(m))]).reshape(nfr, hop).mean(1)
    # 30 ms RMS detector
    mp = uniform_filter1d(mp, 6)
    lvl = 10 * np.log10(mp + 1e-12)
    over = lvl - thr_db
    gr = np.where(over <= -knee / 2, 0.0,
                  np.where(over >= knee / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    ca, cr = np.exp(-hop / (att * SR)), np.exp(-hop / (rel * SR))
    out = np.zeros(nfr)
    s = 0.0
    for i in range(nfr):
        c = ca if gr[i] > s else cr
        s = c * s + (1 - c) * gr[i]
        out[i] = s
    gain = 10 ** (-np.interp(np.arange(len(x)) / hop, np.arange(nfr), out) / 20)
    return x * gain[:, None], out.max()


# ------------------------------------------------------------------ helpers
def load_cues(argv):
    cands = [argv[1]] if len(argv) > 1 else []
    cands += [os.path.join(BUILD, "cues.json"), os.path.join(BUILD, "cues_test.json")]
    for p in cands:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f), p
    print("[mix] WARNING: no cue file found; mixing dialogue (+music) only")
    return {"scenes": [], "sfx": [], "amb": []}, None


def read_audio(path):
    x, sr = sf.read(path, dtype="float64", always_2d=True)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g, axis=0)
    return x


def to_stereo(x, pan=0.0):
    if x.ndim == 2 and x.shape[1] >= 2:
        x = x[:, :2]
        if pan:
            l, r = np.cos((pan + 1) * np.pi / 4) * np.sqrt(2), np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
            x = x * np.array([[min(l, 1.0), min(r, 1.0)]])
        return x
    x = x.reshape(-1)
    pan = float(np.clip(pan, -1, 1))
    return np.stack([x * np.cos((pan + 1) * np.pi / 4), x * np.sin((pan + 1) * np.pi / 4)], 1)


def add_at(dst, src, i0):
    i0 = int(round(i0))
    s0 = max(0, -i0)
    i0 = max(0, i0)
    m = min(len(src) - s0, len(dst) - i0)
    if m > 0:
        dst[i0:i0 + m] += src[s0:s0 + m]


def frame_rms(x, hop):
    m = (x ** 2).mean(1) if x.ndim == 2 else x ** 2
    nfr = len(m) // hop + 1
    mp = np.concatenate([m, np.zeros(nfr * hop - len(m))]).reshape(nfr, hop).mean(1)
    return mp


def db(p):  # power -> dB
    return 10 * np.log10(np.maximum(p, 0) + 1e-20)


def win_power(x, t0, t1):
    a, b = int(max(0, t0) * SR), int(min(len(x) / SR, t1) * SR)
    if b <= a:
        return 0.0
    return float((x[a:b] ** 2).mean())


def scene_at(scenes, t):
    for s in scenes:
        if s["t0"] <= t < s["t1"]:
            return s
    if not scenes:
        return None
    return min(scenes, key=lambda s: min(abs(t - s["t0"]), abs(t - s["t1"])))


# ------------------------------------------------------------------ main
def main(argv):
    T0 = time.time()
    sched = json.load(open(os.path.join(BUILD, "schedule.json")))
    cues, cue_path = load_cues(argv)
    scenes = sorted(cues.get("scenes", []), key=lambda s: s["t0"])
    dur = float(sched["duration"])
    N = int(round(dur * SR))
    log = []

    def P(*a):
        s = " ".join(str(v) for v in a)
        print(s)
        log.append(s)

    P(f"The Family Inside - mix report   ({time.strftime('%Y-%m-%d %H:%M')})")
    P(f"cues: {cue_path}   duration {dur:.3f} s ({N} samples @ {SR})")

    # ---------------- dialogue
    dlg_dry = np.zeros((N, 2))
    dlg = np.zeros((N, 2))
    irs = {}
    line_info = []
    silent = []
    for i, ln in enumerate(sched["lines"]):
        path = os.path.join(BUILD, ln["wav"])
        if not os.path.exists(path):
            P(f"  WARNING missing voice {ln['wav']}")
            continue
        v = read_audio(path).mean(1)
        if np.max(np.abs(v)) < 1e-5:
            P(f"  WARNING voice {ln['id']} ({ln['wav']}) is silent - placed nothing")
            silent.append(ln["id"])
            continue
        hop = int(0.02 * SR)
        fr = frame_rms(v, hop)
        act = fr[db(fr) > db(fr.max()) - 35]
        lvl = db(act.mean()) if len(act) else -60
        corr = float(np.clip(VOICE_TARGET_DB - lvl, -4, 4))
        v = v * 10 ** (corr / 20)
        v = SFXLIB.fade(v, 0.003, 0.01)
        sc = scene_at(scenes, ln["t0"])
        sname = sc["name"] if sc else ln.get("sc", "kitchen")
        room = "narrator" if ln.get("sp") == "nar" else room_for_scene(sname)
        if room not in irs:
            irs[room] = make_ir(room, len(irs))
        ir = irs[room]
        wet = np.stack([signal.fftconvolve(v, ir[:, c]) for c in range(2)], 1)
        dry = to_stereo(np.concatenate([v, np.zeros(len(wet) - len(v))]), 0.0) * np.sqrt(2) * 0.7071
        i0 = ln["t0"] * SR
        add_at(dlg, dry + wet, i0)
        add_at(dlg_dry, dry, i0)
        line_info.append(dict(id=ln["id"], sp=ln["sp"], t0=ln["t0"], t1=ln["t1"], scene=sname,
                              room=room, corr=corr))
    P(f"dialogue: {len(line_info)} lines placed; rooms used: {sorted(irs)}")

    # ---------------- ducking envelope (from dry dialogue)
    hop = int(0.005 * SR)
    fr = frame_rms(dlg_dry, hop)
    fr = uniform_filter1d(fr, 4)
    pres = (db(fr) > VOICE_TARGET_DB - 26).astype(float)
    look = int(DUCK_LOOK / 0.005)
    pres = np.concatenate([pres[look:], np.zeros(look)])     # look-ahead: lead the speech
    tgt = DUCK_DB * pres
    ca, cr = np.exp(-0.005 / DUCK_ATT), np.exp(-0.005 / DUCK_REL)
    g = np.zeros(len(tgt))
    s = 0.0
    for k in range(len(tgt)):
        c = ca if tgt[k] < s else cr
        s = c * s + (1 - c) * tgt[k]
        g[k] = s
    duck = 10 ** (np.interp(np.arange(N) / hop, np.arange(len(g)), g) / 20)

    dlg_lufs = lufs(dlg)
    P(f"dialogue stem loudness {dlg_lufs:.1f} LUFS (pre-bus)")

    # ---------------- music
    music = np.zeros((N, 2))
    mpath = MUSIC_OVERRIDE or os.path.join(BUILD, "music.wav")
    have_music = os.path.exists(mpath)
    if have_music:
        try:
            m = to_stereo(read_audio(mpath))
            m = m[:N]
            music[:len(m)] = m
            ml = lufs(music)
            if np.isfinite(ml):
                mg = dlg_lufs + MUSIC_REL_LU - ml
                music *= 10 ** (mg / 20)
                P(f"music: {mpath} ({len(m)/SR:.1f}s) {ml:.1f} LUFS -> gain {mg:+.1f} dB, ducked {DUCK_DB} dB")
            else:
                P("music: silent file, ignored")
        except Exception as e:  # never die on a bad music file
            P(f"music: WARNING could not read ({e}); continuing without")
            have_music = False
    else:
        P("music: build/music.wav not present - mixing without music")
    music *= duck[:, None]

    # ---------------- sfx
    sfxb = np.zeros((N, 2))
    cache = {}
    nplaced = 0
    for k, c in enumerate(sorted(cues.get("sfx", []), key=lambda c: c["t"])):
        nm = c.get("name")
        key = (nm, k % 3)  # up to 3 deterministic variations per name
        if key not in cache:
            cache[key] = SFXLIB.sfx(nm, seed=k % 3)
        y = cache[key]
        if y is None:
            P(f"  sfx WARNING: unknown '{nm}' at {c.get('t')} skipped")
            continue
        y = to_stereo(np.asarray(y, float), float(c.get("pan", 0)))
        add_at(sfxb, y * float(c.get("gain", 1.0)) * SFX_BUS, float(c["t"]) * SR)
        nplaced += 1
    P(f"sfx: {nplaced} one-shots placed")

    # ---------------- ambience
    ambb = np.zeros((N, 2))
    for k, a in enumerate(cues.get("amb", [])):
        t0, t1 = float(a["t0"]), float(a["t1"])
        r0, r1 = max(0.0, t0 - AMB_XFADE / 2), min(dur, t1 + AMB_XFADE / 2)
        if r1 - r0 < 0.1:
            continue
        y = SFXLIB.amb(a["name"], r1 - r0, seed=k)
        if y is None:
            P(f"  amb WARNING: unknown '{a['name']}' skipped")
            continue
        y = np.asarray(y, float)
        n = len(y)
        tt = r0 + np.arange(n) / SR
        fin = np.clip((tt - (t0 - AMB_XFADE / 2)) / AMB_XFADE, 0, 1) if t0 > 0.01 else np.ones(n)
        fout = np.clip(((t1 + AMB_XFADE / 2) - tt) / AMB_XFADE, 0, 1) if t1 < dur - 0.01 else np.ones(n)
        w = np.sin(np.pi / 2 * np.minimum(fin, fout))           # equal-power edges
        if t0 <= 0.01:  # very start of the film: short fade-in only
            w *= np.clip((tt - 0) / 0.3, 0, 1)
        add_at(ambb, y * w[:, None] * float(a.get("gain", 1.0)) * AMB_BUS, r0 * SR)
    P(f"amb: {len(cues.get('amb', []))} regions")

    # ---------------- dialogue safety (bed pull-down per line)
    bed = music + sfxb + ambb
    att_db = np.zeros(N)
    pulls = []
    for li in line_info:
        dp = win_power(dlg, li["t0"], li["t1"])
        bp_ = win_power(bed, li["t0"], li["t1"])
        marg = db(dp) - db(bp_)
        if marg < MIN_MARGIN_DB:
            need = MIN_MARGIN_DB - marg + 0.5
            a, b = int(max(0, li["t0"] - 0.15) * SR), int(min(dur, li["t1"] + 0.3) * SR)
            att_db[a:b] = np.minimum(att_db[a:b], -need)
            pulls.append((li["id"], marg, need))
    if pulls:
        ramp = int(0.15 * SR)
        att_db = uniform_filter1d(minimum_filter1d(att_db, 2 * ramp + 1), 2 * ramp + 1)
        bedgain = 10 ** (att_db / 20)
        music *= bedgain[:, None]
        sfxb *= bedgain[:, None]
        ambb *= bedgain[:, None]
        P(f"safety: bed pulled down under {len(pulls)} lines: " +
          ", ".join(f"{i}({m:.1f}dB,-{n:.1f})" for i, m, n in pulls))
    else:
        P("safety: no bed pull-down needed")

    # ---------------- end fade (last 2.5 s) + start micro-fade
    fo = int(2.5 * SR)
    fade = np.ones(N)
    fade[-fo:] = np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    fade[:int(0.02 * SR)] = np.linspace(0, 1, int(0.02 * SR))
    stems = {"dialogue": dlg, "music": music, "sfx": sfxb, "amb": ambb}
    for k in stems:
        stems[k] = stems[k] * fade[:, None]
    mix = sum(stems.values())

    # ---------------- bus: pre-gain, compress, normalise, limit
    l0 = lufs(mix)
    pre = TARGET_LUFS - l0
    mix *= 10 ** (pre / 20)
    mix, gr_max = compressor(mix)
    for it in range(3):
        l1 = lufs(mix)
        mix *= 10 ** ((TARGET_LUFS - l1) / 20)
        mix, lim_db = limiter(mix)
        lf = lufs(mix)
        if abs(lf - TARGET_LUFS) < 0.15:
            break
    tp = true_peak_db(mix)
    if tp > TP_CEIL_DB + 0.05:
        mix *= 10 ** ((TP_CEIL_DB - tp) / 20)
        tp = true_peak_db(mix)
    lf = lufs(mix)
    assert np.all(np.isfinite(mix)), "NaN/Inf in mix"
    mix = mix[:N]

    # ---------------- write 16-bit with TPDF dither
    rng = np.random.default_rng(12345)
    d = (rng.random(mix.shape) - rng.random(mix.shape)) / 32768.0
    out = np.clip(mix + d, -1, 32767 / 32768)
    os.makedirs(BUILD, exist_ok=True)
    out_path = os.path.join(BUILD, "mix.wav")
    sf.write(out_path, out.astype(np.float32), SR, subtype="PCM_16")

    # ---------------- report
    P("")
    P("== bus ==")
    P(f"pre-gain {pre:+.1f} dB, compressor max GR {gr_max:.1f} dB, limiter max GR {-lim_db if lim_db else 0:.1f} dB "
      f"(limiting >1 dB {limiter.stats[0]:.2f}% of time, >3 dB {limiter.stats[1]:.3f}%)")
    P(f"INTEGRATED LOUDNESS {lf:.2f} LUFS (target {TARGET_LUFS})   TRUE PEAK {tp:.2f} dBTP (ceiling {TP_CEIL_DB})")
    P(f"sample peak {20*np.log10(np.abs(out).max()):.2f} dBFS, clipped samples {(np.abs(mix) >= 1).sum()}, "
      f"NaN {int(np.isnan(mix).sum())}, length {len(out)/SR:.3f} s")

    # stems scaled by the bus gains: bus gains are common to all stems, so ratios hold;
    # absolute values computed with the overall average gain for display.
    raw = sum(stems.values())
    gtot = np.sqrt((mix ** 2).sum() / ((raw ** 2).sum() + 1e-20))
    P("")
    P("== per-scene (dB re full scale, final level; bed = music+sfx+amb) ==")
    P(f"{'scene':10s} {'t0':>7s} {'t1':>7s} {'LUFS':>6s} {'dlgRMS':>7s} {'music':>7s} {'sfx':>7s} {'amb':>7s}")
    for s in scenes:
        a, b = int(s["t0"] * SR), int(min(s["t1"], dur) * SR)
        L = lufs(mix[a:b])
        vals = [db(win_power(stems[k] * gtot, s["t0"], s["t1"])) for k in ("dialogue", "music", "sfx", "amb")]
        P(f"{s['name']:10s} {s['t0']:7.2f} {s['t1']:7.2f} {L:6.1f} " + " ".join(f"{v:7.1f}" for v in vals))

    P("")
    P("== dialogue vs bed margin per line (RMS over line window, dB) ==")
    margins = []
    bed = stems["music"] + stems["sfx"] + stems["amb"]
    for li in line_info:
        m = db(win_power(stems["dialogue"], li["t0"], li["t1"])) - db(win_power(bed, li["t0"], li["t1"]))
        margins.append(m)
        P(f"  {li['id']:5s} {li['sp']:6s} {li['t0']:7.2f}-{li['t1']:7.2f} {li['scene']:10s} room={li['room']:8s} "
          f"lvl{li['corr']:+4.1f}  margin " + (f"{m:5.1f}" if m < 60 else " >60 (bed silent)") +
          ('  <10!' if m < 10 else ''))
    margins = np.array(margins)
    if silent:
        P(f"SILENT voice files (nothing to mix): {', '.join(silent)}")
    P(f"margin: min {margins.min():.1f} dB, median {np.median(margins):.1f} dB, "
      f"lines < 10 dB: {(margins < 10).sum()}")

    # independent check with ffmpeg ebur128
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", out_path, "-af",
                            "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, timeout=120)
        tail = [l.strip() for l in r.stderr.splitlines()[-14:] if any(k in l for k in ("I:", "LRA:", "Peak:"))]
        P("ffmpeg ebur128 check: " + " | ".join(tail))
    except Exception as e:
        P(f"ffmpeg check skipped ({e})")
    P(f"music present: {have_music}.  runtime {time.time() - T0:.1f} s")
    with open(os.path.join(BUILD, "mix_report.txt"), "w") as f:
        f.write("\n".join(log) + "\n")
    print(f"wrote {out_path}")


MUSIC_OVERRIDE = None

if __name__ == "__main__":
    args = list(sys.argv)
    if "--music" in args:  # testing aid: python3 audio/mix.py [cues] --music other.wav
        k = args.index("--music")
        MUSIC_OVERRIDE = args[k + 1]
        del args[k:k + 2]
    main(args)
