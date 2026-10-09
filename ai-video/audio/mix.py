"""Final mix: voices + procedural music bed + scene SFX -> out/mix.wav.

    from audio import mix; mix.run()

Pipeline
  * Scene placement follows the VIDEO: each scene segment is round(dur*FPS)
    frames, so scene k starts at sum(frames_j)/FPS (not the unrounded
    timeline start). Keeps lip-sync exact even after many scenes.
  * Voices: HPF, per-line level match, gentle compression, mud/de-ess EQ,
    character colour (villain: small stone-room reverb, AI: subtle chorus +
    bright shimmer, narrator: nearly dry). Line meta: "gain" (dB), "dry" (bool).
  * Music: consecutive scenes with the same `music` cue are rendered as ONE
    seamless render_cue call; 0.6 s equal-power crossfades between cues
    (scene meta "music_xfade" overrides for the cut INTO that scene,
    "music_restart": true forces a new render). Per-scene "music_gain" (dB)
    with smooth ramps. Music sits CFG['music_under_dialog_db'] under the
    dialogue loudness, ducks CFG['duck_db'] more while anyone speaks
    (80 ms attack / 400 ms release, with lookahead so first syllables are
    never masked) and lifts CFG['lift_db'] in longer dialogue-free stretches.
  * SFX: scenes.<module>.SFX(info) -> [(t, name, gain_db[, pan])], scene-local.
  * Master: gentle bus compression, loudness-normalize to -14 LUFS
    (BS.1770-4 gated), true-peak lookahead limiter (ceiling -1.5 dBTP so the
    AAC encode stays under -1 dBTP), TPDF dither, 16-bit 48 kHz stereo.
"""
import importlib
import json
import math
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

import numpy as np
import soundfile as sf
from scipy import signal as sps
from scipy.ndimage import minimum_filter1d, maximum_filter1d

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from audio import music as M  # noqa: E402
from audio import sfx as SFX  # noqa: E402
from engine.timeline import Timeline, TIMELINE, LIP  # noqa: E402

SR = 48000
FPS = 24
OUT = os.path.join(ROOT, "out")
LINES = os.path.join(OUT, "lines")
MIX = os.path.join(OUT, "mix.wav")

CFG = dict(
    voice_rms_db=-20.0,          # per-line active-speech RMS before compression
    music_under_dialog_db=10.0,  # music bed loudness below dialogue loudness
    duck_db=7.0, duck_attack=0.08, duck_release=0.40, duck_lookahead=0.12, duck_hold=0.25,
    lift_db=4.0,                 # extra music level in dialogue-free stretches
    xfade=0.6, end_fade=1.6,
    sfx_db=0.0,
    target_lufs=-14.0, ceiling_dbtp=-1.5,
)


def log(*a):
    print("[mix]", *a, file=sys.stderr)


# =============================================================================
# dynamics helpers (control rate = 1 kHz)
# =============================================================================
CR = 1000


def _frames_ms(x, sr):
    """Mean-square per 1 ms frame (stereo-linked: max over channels)."""
    hop = sr // CR
    n = len(x) // hop
    if x.ndim == 1:
        p = (x[: n * hop].astype(np.float64) ** 2).reshape(n, hop).mean(1)
    else:
        p = (x[: n * hop].astype(np.float64) ** 2).reshape(n, hop, x.shape[1]).mean(1).max(1)
    return p


def _follow(v, attack, release, rate=CR):
    """One-pole attack/release follower over a control-rate sequence."""
    a = math.exp(-1.0 / (attack * rate))
    r = math.exp(-1.0 / (release * rate))
    out = np.empty_like(v)
    y = float(v[0]) if len(v) else 0.0
    for i, x in enumerate(v.tolist()):
        y = (a * y + (1 - a) * x) if x > y else (r * y + (1 - r) * x)
        out[i] = y
    return out


def _to_samples(g_cr, n, sr):
    """Control-rate curve -> per-sample (linear interpolation at frame centres)."""
    hop = sr // CR
    xs = (np.arange(len(g_cr)) + 0.5) * hop
    return np.interp(np.arange(n), xs, g_cr) if len(g_cr) else np.ones(n)


def compress(x, sr, thresh_db, ratio=3.0, knee_db=6.0, attack=0.005, release=0.08,
             rms_win=0.01):
    """Feed-forward RMS compressor; returns (y, max_gain_reduction_db)."""
    p = _frames_ms(x, sr)
    w = max(1, int(rms_win * CR))
    p = np.convolve(p, np.ones(w) / w, mode="same")
    lv = 10 * np.log10(p + 1e-12)
    over = lv - thresh_db
    gr = np.where(over <= -knee_db / 2, 0.0,
                  np.where(over >= knee_db / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee_db / 2) ** 2 / (2 * knee_db)))
    gr = _follow(gr, attack, release)
    g = 10 ** (-_to_samples(gr, len(x), sr) / 20)
    y = x * (g if x.ndim == 1 else g[:, None])
    return y, float(gr.max()) if len(gr) else 0.0


def true_peak_per_sample(x, sr, chunk_s=6.0):
    """|x| true-peak estimate per input sample (max over 4x oversampled phases)."""
    x = M.stereoize(np.asarray(x))
    n = len(x)
    pk = np.empty(n)
    c = int(chunk_s * sr)
    pad = 64
    for s in range(0, n, c):
        e = min(n, s + c)
        a, b = max(0, s - pad), min(n, e + pad)
        up = sps.resample_poly(x[a:b].astype(np.float64), 4, 1, axis=0)
        up = np.abs(up).reshape(b - a, 4, x.shape[1]).max(axis=(1, 2))
        pk[s:e] = np.maximum(up[s - a: s - a + (e - s)], np.abs(x[s:e]).max(axis=1))
    return pk


def limiter(x, sr, ceiling_db=-1.5, lookahead=0.005, release=0.08):
    """Lookahead true-peak limiter. Gain never exceeds what each sample needs."""
    c = 10 ** (ceiling_db / 20)
    pk = true_peak_per_sample(x, sr)
    req = np.minimum(1.0, c / np.maximum(pk, 1e-9))
    if req.min() >= 1.0:
        return x, 0.0
    L = max(1, int(lookahead * sr))
    g1 = minimum_filter1d(req, size=2 * L + 1, mode="nearest")
    w = L + 1                                   # centred moving average (<= req guaranteed)
    cs = np.concatenate(([0.0], np.cumsum(g1)))
    h = w // 2
    idx = np.arange(len(g1))
    lo_i = np.clip(idx - h, 0, len(g1))
    hi_i = np.clip(idx - h + w, 0, len(g1))
    g2 = (cs[hi_i] - cs[lo_i]) / np.maximum(hi_i - lo_i, 1)
    B = 32                                      # smooth release at block rate
    nb = int(math.ceil(len(g2) / B))
    gb = np.pad(g2, (0, nb * B - len(g2)), constant_values=1.0).reshape(nb, B).min(1)
    rc = math.exp(-B / (release * sr))
    sm = np.empty(nb)
    y = 1.0
    for i, v in enumerate(gb.tolist()):
        y = v if v < y else rc * y + (1 - rc) * v
        sm[i] = y
    g3 = np.interp(np.arange(len(g2)), (np.arange(nb) + 0.5) * B, sm)
    g = np.minimum(g2, g3).astype(x.dtype)
    return x * (g[:, None] if x.ndim == 2 else g), float(-20 * math.log10(g.min()))


# =============================================================================
# voices
# =============================================================================
def _active_rms_db(x, sr):
    hop = int(0.02 * sr)
    n = len(x) // hop
    if n == 0:
        return -100.0
    p = (x[: n * hop] ** 2).reshape(n, hop).mean(1)
    pdb = 10 * np.log10(p + 1e-12)
    act = p[pdb > pdb.max() - 30]
    return 10 * math.log10(act.mean() + 1e-12)


def _chorus(x, sr, base_ms, depth_ms, rate, phase=0.0):
    n = len(x)
    t = np.arange(n) / sr
    d = (base_ms + depth_ms * np.sin(2 * math.pi * rate * t + phase)) * sr / 1000.0
    return np.interp(np.arange(n) - d, np.arange(n), x, left=0.0, right=0.0)


def deess(x, sr, split=5000.0, thresh_db=-30.0, ratio=4.0):
    """Split-band de-esser: compress only the >5 kHz band when it gets hot."""
    hi = M.hp(x, split, sr, 2)
    lo = x - hi                                   # complementary split, exact sum
    p = _frames_ms(hi, sr)
    p = np.convolve(p, np.ones(3) / 3, mode="same")
    lv = 10 * np.log10(p + 1e-12)
    gr = np.maximum(0.0, lv - thresh_db) * (1 - 1 / ratio)
    gr = _follow(gr, 0.002, 0.06)
    g = 10 ** (-_to_samples(gr, len(x), sr) / 20)
    return lo + hi * g, float(gr.max()) if len(gr) else 0.0


VOICE_TAIL = 0.9   # seconds of tail kept after each line (reverb / filter ring-out)


def process_voice(x, sr, who, gain_db=0.0, dry=False):
    """Mono line -> stereo processed line (len(x) + VOICE_TAIL seconds)."""
    x = np.asarray(x, dtype=np.float64)
    x = np.concatenate([x, np.zeros(int(VOICE_TAIL * sr))])
    x = M.hp(x, 75, sr, 2)
    x *= 10 ** ((CFG["voice_rms_db"] - _active_rms_db(x, sr)) / 20)
    x, _ = compress(x, sr, CFG["voice_rms_db"] - 4, ratio=3.0, knee_db=6, attack=0.005, release=0.09)
    x *= 10 ** ((CFG["voice_rms_db"] + gain_db - _active_rms_db(x, sr)) / 20)
    x, _ = deess(x, sr, thresh_db=CFG["voice_rms_db"] + gain_db - 9)
    x = M.biquad(x, "peak", 260, sr, 1.0, -1.5)        # de-mud (phone speakers)
    x = M.biquad(x, "peak", 3200, sr, 1.0, 1.5)        # presence
    x = M.biquad(x, "highshelf", 7000, sr, 0.7, -2.0)  # polite top
    # tame consonant peaks so the master limiter barely works (crest ~12 dB)
    x, _ = limiter(x, sr, CFG["voice_rms_db"] + gain_db + 12.5, 0.002, 0.04)
    st = np.stack([x, x], 1)
    if not dry:
        if who == "ai":
            cl = _chorus(x, sr, 9.0, 0.6, 0.55)
            cr = _chorus(x, sr, 11.5, 0.5, 0.71, 1.3)
            st[:, 0] += 0.16 * cl
            st[:, 1] += 0.16 * cr
            sh = M.hp(x, 2500, sr, 2)
            st += 0.06 * M.reverb(sh, sr, rt60=0.9, predelay=0.015, damp=0.15, seed=21)
        elif who == "villain":
            st += 0.14 * M.reverb(x, sr, rt60=0.75, predelay=0.012, damp=0.55, seed=31, er=0.5)
        else:
            st += 0.05 * M.reverb(x, sr, rt60=0.5, predelay=0.01, damp=0.6, seed=41)
    return M.fade_edges(st, sr, 0.0, 0.25)


def _load_line(path, sr):
    a, r = sf.read(path, dtype="float64", always_2d=False)
    if a.ndim > 1:
        a = a.mean(1)
    if r != sr:
        from math import gcd
        g = gcd(r, sr)
        a = sps.resample_poly(a, sr // g, r // g)
    return a


# =============================================================================
# music
# =============================================================================
def _render_group(args):
    cue, dur, fade_in, fade_out = args
    t = time.time()
    y = M.render_cue(cue, dur, SR, fade_in=fade_in, fade_out=fade_out)
    return y, time.time() - t


def music_groups(scenes, vstart, vdur):
    groups = []
    for k, s in enumerate(scenes):
        cue = (s.meta.get("music") or "none").strip()
        if groups and groups[-1]["cue"] == cue and not s.meta.get("music_restart"):
            groups[-1]["t1"] = vstart[k] + vdur[k]
            groups[-1]["scenes"].append(k)
        else:
            groups.append({"cue": cue, "t0": vstart[k], "t1": vstart[k] + vdur[k], "scenes": [k],
                           "xf_in": float(s.meta.get("music_xfade", CFG["xfade"]))})
    return groups


def build_music(scenes, vstart, vdur, n, sr, procs=4):
    groups = music_groups(scenes, vstart, vdur)
    total = n / sr
    jobs = []
    for i, g in enumerate(groups):
        if g["cue"] == "none":
            continue
        xin = g["xf_in"] if i > 0 else 0.0
        xout = groups[i + 1]["xf_in"] if i + 1 < len(groups) else 0.0
        a = max(0.0, g["t0"] - xin / 2)
        b = min(total, g["t1"] + xout / 2) if i + 1 < len(groups) else total
        fi = xin if i > 0 else 0.02
        fo = xout if i + 1 < len(groups) else CFG["end_fade"]
        g.update(a=a, b=b)
        jobs.append((i, (g["cue"], b - a, max(fi, 0.005), max(fo, 0.005))))
    bed = np.zeros((n, 2), np.float32)
    if jobs:
        order = sorted(jobs, key=lambda j: -j[1][1])
        try:
            if procs <= 1 or len(order) == 1:
                raise RuntimeError("serial")
            ctx = mp.get_context("fork")
            with ProcessPoolExecutor(max_workers=max(1, min(procs, len(order))), mp_context=ctx) as ex:
                results = list(ex.map(_render_group, [j[1] for j in order], timeout=600))
        except Exception as e:
            if str(e) != "serial":
                log(f"parallel music render failed ({type(e).__name__}: {e}); rendering serially")
            results = [_render_group(j[1]) for j in order]
        for (i, args), (y, dt) in zip(order, results):
            g = groups[i]
            i0 = int(round(g["a"] * sr))
            e = min(n, i0 + len(y))
            bed[i0:e] += y[: e - i0]
            g["render_s"] = dt
    # per-scene music_gain (dB) with 0.3 s raised-cosine ramps
    gdb = np.zeros(n)
    for k, s in enumerate(scenes):
        v = float(s.meta.get("music_gain", 0.0) or 0.0)
        a, b = int(round(vstart[k] * sr)), min(n, int(round((vstart[k] + vdur[k]) * sr)))
        gdb[a:b] = v
    if np.any(gdb):
        k = int(0.3 * sr)
        win = np.hanning(2 * k + 1)
        win /= win.sum()
        gdb = _smooth_long(gdb, win)
        bed *= (10 ** (gdb / 20)).astype(np.float32)[:, None]
    return bed, groups


def _smooth_long(x, kernel):
    return sps.oaconvolve(np.pad(x, (len(kernel) // 2, len(kernel) // 2), mode="edge"), kernel, mode="valid")


def speech_mask(voice, sr, n):
    """1 kHz mask of 'someone is speaking' (gaps < hold bridged)."""
    p = _frames_ms(voice, sr)
    w = 10
    p = np.convolve(p, np.ones(w) / w, mode="same")
    m = (10 * np.log10(p + 1e-12) > -42).astype(float)
    hold = int(CFG["duck_hold"] * CR)
    if hold > 1:      # close small gaps between words
        m = minimum_filter1d(maximum_filter1d(m, hold), hold)
    nc = int(math.ceil(n / (sr // CR)))
    m = np.pad(m, (0, max(0, nc - len(m))))[:nc]
    return m


def duck_curve(mask):
    look = int(CFG["duck_lookahead"] * CR)
    m = np.concatenate([mask[look:], np.zeros(look)]) if look else mask
    m = np.maximum(m, mask)
    env = _follow(m, CFG["duck_attack"], CFG["duck_release"])
    duck_db = -CFG["duck_db"] * env
    far = maximum_filter1d(mask, int(2.0 * CR) + 1)       # speech within ±1 s
    lift = 1.0 - far
    k = np.hanning(int(0.8 * CR) + 1)
    lift = _smooth_long(lift, k / k.sum())[: len(mask)]
    return duck_db + CFG["lift_db"] * lift, env, lift


# =============================================================================
# sfx
# =============================================================================
def collect_sfx(tl, vstart, n, sr, override=None):
    """override: optional {scene_id: callable(info) | list} used instead of the
    scene module's SFX (for tests)."""
    bus = np.zeros((n, 2), np.float32)
    placed, warnings = 0, []
    counts = {}
    for k, s in enumerate(tl.scenes):
        if override and s.id in override:
            ov = override[s.id]
            fn = ov if callable(ov) else (lambda info, _l=ov: list(_l))
        else:
            try:
                mod = importlib.import_module(f"scenes.{s.module}")
            except Exception as e:  # scene still being written / broken
                warnings.append(f"{s.id}: cannot import scenes.{s.module} ({type(e).__name__}) - no SFX")
                continue
            fn = getattr(mod, "SFX", None)
        if fn is None:
            continue
        try:
            events = list(fn(s) or [])
        except Exception as e:
            warnings.append(f"{s.id}: SFX() raised {type(e).__name__}: {e}")
            continue
        for ev in events:
            try:
                t, name, gdb = float(ev[0]), str(ev[1]), float(ev[2]) if len(ev) > 2 else 0.0
                p = float(ev[3]) if len(ev) > 3 else 0.0
            except Exception:
                warnings.append(f"{s.id}: malformed SFX entry {ev!r}")
                continue
            key = SFX.resolve(name)
            if key is None:
                warnings.append(f"{s.id}: unknown sfx '{name}' at {t:.2f}s - skipped")
                continue
            seed = counts.get(key, 0)
            counts[key] = seed + 1
            y = SFX.render(key, sr, seed % 4)
            if p:
                y = y * np.array([min(1.0, 1 - p), min(1.0, 1 + p)], np.float32)
            i0 = int(round((vstart[k] + t) * sr))
            if i0 < 0:
                y = y[-i0:]
                i0 = 0
            e = min(n, i0 + len(y))
            if e > i0:
                bus[i0:e] += y[: e - i0] * np.float32(10 ** ((gdb + CFG["sfx_db"]) / 20))
                placed += 1
    return bus, placed, warnings, counts


# =============================================================================
# main
# =============================================================================
def ffmpeg_loudness(path):
    try:
        r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-filter_complex",
                            "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True,
                           timeout=300)
        txt = r.stderr[r.stderr.rfind("Summary:"):]
        i = re.search(r"I:\s+(-?[\d.]+) LUFS", txt)
        p = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", txt)
        return (float(i.group(1)) if i else None, float(p.group(1)) if p and p.group(1) != "-inf" else None)
    except Exception:
        return (None, None)


def run(timeline_path=TIMELINE, out_path=MIX, lines_dir=LINES, lip_path=LIP, procs=4,
        sfx_override=None, stems_dir=None):
    """Mix everything -> out_path (16-bit 48 kHz stereo). Returns the path;
    run.report holds the numbers. stems_dir: also write voice/music/sfx stems."""
    t_start = time.time()
    sr = SR
    tl = Timeline(timeline_path, lip_path)
    vdur = [round(s.dur * FPS) / FPS for s in tl.scenes]
    vstart = list(np.concatenate([[0.0], np.cumsum(vdur)[:-1]]))
    total = float(sum(vdur))
    n = int(round(total * sr))
    log(f"timeline {tl.total:.2f}s, video-aligned {total:.3f}s, {len(tl.scenes)} scenes")

    # ---- voices ---------------------------------------------------------
    voice = np.zeros((n, 2), np.float32)
    nlines, missing = 0, []
    for k, s in enumerate(tl.scenes):
        for ln in s.lines:
            path = os.path.join(lines_dir, f"{ln.id}.wav")
            if not os.path.exists(path):
                missing.append(ln.id)
                continue
            x = _load_line(path, sr)
            st = process_voice(x, sr, ln.who, float(ln.meta.get("gain", 0.0) or 0.0),
                               bool(ln.meta.get("dry", False)))
            i0 = int(round((vstart[k] + ln.start) * sr))
            e = min(n, i0 + len(st))
            if e > i0:
                voice[i0:e] += st[: e - i0].astype(np.float32)
                nlines += 1
    v_lufs = M.lufs(voice, sr) if nlines else -70.0
    ref = v_lufs if v_lufs > -50 else CFG["voice_rms_db"]
    log(f"voices: {nlines} lines placed, {len(missing)} missing, dialogue {v_lufs:.1f} LUFS "
        f"({time.time() - t_start:.1f}s)")
    if missing:
        log("  missing line wavs: " + ", ".join(missing[:12]) + (" ..." if len(missing) > 12 else ""))

    # ---- music ------------------------------------------------------------
    t0 = time.time()
    bed, groups = build_music(tl.scenes, vstart, vdur, n, sr, procs)
    t_music = time.time() - t0
    base_db = (ref - CFG["music_under_dialog_db"]) - M.TARGET_LUFS
    mask = speech_mask(voice, sr, n)
    dcurve, duck_env, lift = duck_curve(mask)
    g = 10 ** ((base_db + _to_samples(dcurve, n, sr)) / 20)
    music = bed * g.astype(np.float32)[:, None]
    del bed, g
    log(f"music: {sum(1 for g_ in groups if g_['cue'] != 'none')} renders in {t_music:.1f}s; "
        f"bed {base_db:+.1f} dB, duck -{CFG['duck_db']:.0f} dB, lift +{CFG['lift_db']:.0f} dB")
    for g_ in groups:
        ids = [tl.scenes[k].id for k in g_["scenes"]]
        log(f"  {g_['cue']:8s} {g_['t0']:7.2f}-{g_['t1']:7.2f}s  scenes {ids[0]}..{ids[-1]}"
            + (f"  ({g_['render_s']:.1f}s)" if "render_s" in g_ else ""))

    # ---- sfx ----------------------------------------------------------------
    sfxbus, nsfx, warns, counts = collect_sfx(tl, vstart, n, sr, sfx_override)
    log(f"sfx: {nsfx} placed ({', '.join(f'{k}x{v}' for k, v in sorted(counts.items()))}) "
        f"[t={time.time() - t_start:.1f}s]")
    for w in warns:
        log("  WARN " + w)

    if stems_dir:
        os.makedirs(stems_dir, exist_ok=True)
        for nm, b in (("voice", voice), ("music", music), ("sfx", sfxbus)):
            sf.write(os.path.join(stems_dir, f"audio_stem_{nm}.wav"), b, sr, subtype="FLOAT")
        np.save(os.path.join(stems_dir, "audio_stem_duck.npy"), np.stack([mask, duck_env, lift, dcurve]))
        run.music_groups = groups

    # ---- master -------------------------------------------------------------
    mixb = voice.astype(np.float64) + music + sfxbus
    m_lufs = M.lufs(music, sr) if np.abs(music).max() > 0 else -70.0
    s_lufs = M.lufs(sfxbus, sr) if nsfx else -70.0
    del music, sfxbus
    L0 = M.lufs(mixb, sr)
    if L0 <= -69:
        log("mix is silent!")
        L0 = CFG["target_lufs"]
    mixb, gr_bus = compress(mixb, sr, L0 + 5.0, ratio=2.0, knee_db=8, attack=0.02, release=0.25, rms_win=0.05)
    mixb = M.hp(mixb, 22, sr, 2)
    gain = CFG["target_lufs"] - M.lufs(mixb, sr)
    mixb *= 10 ** (gain / 20)
    lim_gr = 0.0
    for it in range(3):
        mixb, gr = limiter(mixb, sr, CFG["ceiling_dbtp"])
        lim_gr = max(lim_gr, gr)
        L = M.lufs(mixb, sr)
        if abs(L - CFG["target_lufs"]) < 0.15:
            break
        mixb *= 10 ** ((CFG["target_lufs"] - L) / 20)
    tp = M.true_peak(mixb, sr)
    ceil = 10 ** (CFG["ceiling_dbtp"] / 20)
    if tp > ceil:
        mixb *= ceil / tp
    rng = np.random.default_rng(1234)
    lsb = 1.0 / 32768
    out = mixb + (rng.random(mixb.shape) - rng.random(mixb.shape)) * lsb
    out = np.clip(out, -1.0, 32767 / 32768)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sf.write(out_path, out.astype(np.float32), sr, subtype="PCM_16")
    final_lufs = M.lufs(out, sr)
    final_tp = M.db(M.true_peak(out, sr))
    ff_i, ff_p = ffmpeg_loudness(out_path)
    report = {
        "path": out_path, "duration_s": round(n / sr, 3), "dialogue_lufs": round(v_lufs, 1),
        "music_lufs": round(m_lufs, 1), "sfx_lufs": round(s_lufs, 1),
        "bus_comp_max_gr_db": round(gr_bus, 1), "limiter_max_gr_db": round(lim_gr, 1),
        "final_lufs": round(final_lufs, 2), "final_true_peak_dbtp": round(final_tp, 2),
        "ffmpeg_I": ff_i, "ffmpeg_true_peak": ff_p, "lines": nlines, "sfx": nsfx,
        "sfx_warnings": len(warns), "seconds": round(time.time() - t_start, 1)}
    log("master: " + ", ".join(f"{k}={v}" for k, v in report.items() if k != "path"))
    log(f"wrote {out_path}")
    run.report = report
    return out_path


if __name__ == "__main__":
    run()
