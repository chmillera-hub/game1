#!/usr/bin/env python3
"""THE STONE AND THE BREAD -- objective verification of the mix (we cannot listen, so we measure).

    python3 film/audio/mix_check.py            # -> film/build/audio/verify/check.json + PNGs, summary on stdout
    python3 film/audio/mix_check.py --asr [--asr-model medium.en]   # + Whisper intelligibility from the mix
                                               #   (needs faster-whisper and a cached model; set HF_HOME)

Checks
  * format: 48 kHz, stereo, 24-bit, length == the film's frame-exact length; stems sum to the mix
  * loudness: ffmpeg ebur128 (integrated, LRA, true peak) overall and per scene, cross-checked in numpy
  * dialogue-to-background ratio per line: energy of the dialogue stem vs everything else (mix - dialogue) in
    the 300-4000 Hz band over the line's speech-active frames (>= 8 dB required, except the drowned s4_l1,
    which is reported before / after the swell)
  * dialogue timing: cross-correlation of the dialogue stem with each source wav at its placed sample
  * clicks: isolated second-difference spikes (vs. the local texture) in the mix and every stem
  * story beats: the hold loop's notes (pitch + period), the tavern swell (+dB), the S5 silence (drop, LUFS),
    the score's first note vs the laugh, level steps at scene boundaries
  * spectrogram PNGs per scene (lines + beats marked) and zooms for the beats above
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
ROOT = os.path.dirname(FILM)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from film.audio import song as SONG  # noqa: E402
from film.lib import timeline as TL  # noqa: E402

SR = 48000
AUD = os.path.join(FILM, "build", "audio")
VER = os.path.join(AUD, "verify")


# ================================================================================================
# loudness
# ================================================================================================
def ebur128(path, start=None, dur=None):
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-nostats"]
    if start is not None:
        cmd += ["-ss", f"{start:.4f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.4f}"]
    cmd += ["-i", path, "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    txt = r.stderr
    summ = txt[txt.rfind("Summary:"):]
    out = {}
    for key, pat in (("I", r"I:\s+(-?[\d.]+|-inf) LUFS"), ("LRA", r"LRA:\s+(-?[\d.]+) LU"),
                     ("TP", r"Peak:\s+(-?[\d.]+|-inf) dBFS")):
        m = re.search(pat, summ)
        if m:
            v = m.group(1)
            out[key] = -float("inf") if v == "-inf" else float(v)
    return out


def momentary(x, win=0.4, hop=0.1):
    """BS.1770 K-weighted momentary loudness (400 ms) every 100 ms -> (times, LUFS)."""
    from scipy.signal import lfilter
    if x.ndim == 1:
        x = x[:, None]
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)
    p = (y * y).sum(axis=1)
    cs = np.concatenate([[0.0], np.cumsum(p)])
    W, H = int(win * SR), int(hop * SR)
    idx = np.arange(0, len(p) - W, H)
    ms = (cs[idx + W] - cs[idx]) / W
    return (idx + W / 2) / SR, -0.691 + 10 * np.log10(ms + 1e-20)


def true_peak(x):
    from scipy.signal import resample_poly
    pk = 0.0
    for c in range(x.shape[1]):
        for a in range(0, len(x), SR * 10):
            seg = x[max(0, a - 64): a + SR * 10 + 64, c]
            pk = max(pk, np.abs(resample_poly(seg, 4, 1)).max())
    return 20 * math.log10(pk + 1e-12)


# ================================================================================================
# spectra
# ================================================================================================
def stft_power(x, nfft=2048, hop=480):
    if x.ndim == 2:
        x = x.mean(axis=1)
    w = np.hanning(nfft)
    nfr = max(1, 1 + (len(x) - nfft) // hop)
    out = np.empty((nfr, nfft // 2 + 1))
    for a in range(0, nfr, 2000):
        b = min(nfr, a + 2000)
        idx = np.arange(nfft)[None, :] + hop * np.arange(a, b)[:, None]
        out[a:b] = np.abs(np.fft.rfft(x[idx] * w, axis=1)) ** 2
    return out


def band_energy(x, lo=300.0, hi=4000.0, nfft=2048, hop=480):
    P = stft_power(x, nfft, hop)
    f = np.fft.rfftfreq(nfft, 1 / SR)
    m = (f >= lo) & (f <= hi)
    return P[:, m].sum(axis=1)


# ================================================================================================
# PNG
# ================================================================================================
def _cmap(v):
    stops = np.array([[0.0, 6, 6, 20], [0.25, 40, 20, 90], [0.5, 150, 40, 110], [0.7, 230, 100, 50],
                      [0.85, 250, 190, 60], [1.0, 255, 255, 220]])
    return np.stack([np.interp(v, stops[:, 0], stops[:, k]) for k in (1, 2, 3)], -1).astype(np.uint8)


def spectro_png(x, path, t0=0.0, fmin=40, fmax=16000, logf=True, height=380, pps=60, dyn=80, marks=(), spans=(),
                title="", top_db=None, curve=None):
    from PIL import Image, ImageDraw, ImageFont
    if x.ndim == 2:
        x = x.mean(axis=1)
    win, hop = 2048, max(1, int(SR / pps))
    nfr = max(1, 1 + (len(x) - win) // hop)
    xp = np.pad(x, (0, win))
    f = np.fft.rfftfreq(win, 1 / SR)
    fy = np.geomspace(fmin, fmax, height) if logf else np.linspace(fmin, fmax, height)
    cols = []
    w = np.hanning(win)
    for a in range(0, nfr, 1500):
        b = min(nfr, a + 1500)
        idx = np.arange(win)[None, :] + hop * np.arange(a, b)[:, None]
        F = np.abs(np.fft.rfft(xp[idx] * w, axis=1)) ** 2
        cols.append(np.stack([np.interp(fy, f, fr) for fr in F], 1))
    D = 10 * np.log10(np.concatenate(cols, 1) + 1e-14)
    top = D.max() if top_db is None else top_db
    V = np.clip((D - (top - dyn)) / dyn, 0, 1)[::-1]
    im = Image.fromarray(_cmap(V))
    pt, pl, pb = 34, 48, 20
    cv = Image.new("RGB", (im.width + pl + 8, height + pt + pb + (90 if curve is not None else 0)), (0, 0, 0))
    cv.paste(im, (pl, pt))
    d = ImageDraw.Draw(cv)
    try:
        font = ImageFont.truetype(os.path.join(FILM, "assets", "fonts", "Oswald.ttf"), 12)
    except Exception:
        font = ImageFont.load_default()
    d.text((4, 2), title, fill=(255, 255, 255), font=font)
    dur = len(x) / SR
    step = 1 if dur <= 40 else 5
    for s in np.arange(math.ceil(t0), t0 + dur + 1e-6, step):
        xx = pl + int((s - t0) * pps)
        d.line([(xx, pt + height), (xx, pt + height + 4)], fill=(200, 200, 200))
        d.text((xx - 6, pt + height + 5), f"{s:.0f}", fill=(200, 200, 200), font=font)
    for fr in (50, 100, 200, 500, 1000, 2000, 4000, 8000, 16000):
        if fmin <= fr <= fmax:
            pos = np.interp(math.log(fr) if logf else fr, np.log(fy) if logf else fy, np.arange(height))
            yy = pt + height - 1 - int(pos)
            d.line([(pl - 4, yy), (pl, yy)], fill=(200, 200, 200))
            d.text((2, yy - 7), f"{fr}" if fr < 1000 else f"{fr // 1000}k", fill=(200, 200, 200), font=font)
    for (a, b, label, col) in spans:
        xa, xb = pl + int((a - t0) * pps), pl + int((b - t0) * pps)
        d.rectangle([xa, pt - 7, xb, pt - 3], fill=col)
        d.text((xa, pt - 20), label, fill=col, font=font)
    for (tm, label, col) in marks:
        xx = pl + int((tm - t0) * pps)
        d.line([(xx, pt - 2), (xx, pt + height)], fill=col, width=1)
        d.text((xx + 2, pt + 2), label, fill=col, font=font)
    if curve is not None:                       # momentary loudness strip under the spectrogram
        tt, lv = curve
        y0 = pt + height + pb + 4
        hgt = 80
        d.rectangle([pl, y0, pl + im.width, y0 + hgt], outline=(70, 70, 70))
        for ref in (-50, -40, -30, -20, -10):
            yy = y0 + int((-ref - 5) / 50 * hgt)
            d.line([(pl, yy), (pl + im.width, yy)], fill=(40, 40, 40))
            d.text((4, yy - 7), f"{ref}", fill=(150, 150, 150), font=font)
        pts = [(pl + int((a - t0) * pps), y0 + int(np.clip((-b - 5) / 50, 0, 1) * hgt)) for a, b in zip(tt, lv)]
        if len(pts) > 1:
            d.line(pts, fill=(120, 230, 255), width=1)
    cv.save(path)
    return path


# ================================================================================================
# checks
# ================================================================================================
def edits_png(x, pts, path, half=0.05):
    """Waveform close-ups (+-50 ms, both channels) around every edit point: a click shows as a vertical step."""
    from PIL import Image, ImageDraw, ImageFont
    cols, w, h = 4, 300, 120
    rows = (len(pts) + cols - 1) // cols
    im = Image.new("RGB", (cols * w, rows * (h + 18)), (12, 12, 20))
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype(os.path.join(FILM, "assets", "fonts", "Oswald.ttf"), 11)
    except Exception:
        font = ImageFont.load_default()
    for k, (t, name) in enumerate(pts):
        r, c = divmod(k, cols)
        x0, y0 = c * w, r * (h + 18)
        i = int(round(t * SR))
        seg = x[max(0, i - int(half * SR)): i + int(half * SR)]
        pk = max(np.abs(seg).max(), 1e-4)
        d.text((x0 + 4, y0 + 2), f"{name}  t={t:.3f}s  (+-50 ms, peak {20 * math.log10(pk):.0f} dBFS)",
               fill=(230, 230, 230), font=font)
        mid = y0 + 18 + h // 2
        d.line([(x0 + w // 2, y0 + 18), (x0 + w // 2, y0 + 18 + h)], fill=(90, 60, 60))
        for ch, col in ((0, (120, 220, 255)), (1, (255, 170, 120))):
            ys = seg[:, ch] / pk * (h / 2 - 4)
            xs = np.linspace(x0 + 2, x0 + w - 2, len(ys))
            d.line(list(zip(xs.tolist(), (mid - ys).tolist())), fill=col, width=1)
    im.save(path)
    return path


def detect_clicks(x, hf=12000.0, thresh=12.0, floor_db=-66.0, win=0.004, guard=0.00025):
    """Digital discontinuities (steps, truncations, gaps): spikes of energy above `hf` far above the local
    HF texture.  Smooth acoustic transients (grains, plosives, impacts) carry little energy up there."""
    from scipy.ndimage import uniform_filter1d
    from scipy.signal import butter, sosfilt
    if x.ndim == 2:
        x = x.mean(axis=1)
    h = sosfilt(butter(6, hf / (SR / 2), "high", output="sos"), x)
    e = h * h
    W, G = int(win * SR), int(guard * SR)
    tot = uniform_filter1d(e, 2 * W + 1) * (2 * W + 1)
    near = uniform_filter1d(e, 2 * G + 1) * (2 * G + 1)
    ctx = np.sqrt(np.maximum(tot - near, 0) / (2 * (W - G)) + 1e-20)
    r = np.abs(h) / ctx
    cand = np.nonzero((r > thresh) & (np.abs(h) > 10 ** (floor_db / 20)))[0]
    out, last = [], -10 ** 9
    for i in cand:
        if i - last > SR * 0.01:
            out.append((round(i / SR, 4), round(float(r[i]), 1), round(20 * math.log10(abs(h[i]) + 1e-12), 1)))
        last = i
    return out


def edit_points(rep):
    """Every place the mix is cut or switched: scene boundaries, S4 perspective switches, the S5 silence,
    the end of the hold music."""
    S = {sc["id"]: sc for sc in rep["scenes"]}
    pts = [(sc["start"], f"S{sc['id']} start") for sc in rep["scenes"][1:]]
    if TL.has_beat("s4_inside"):
        pts.append((S[4]["start"] + TL.beat("s4_inside").t, "S4 inside"))
    dc = rep.get("tavern", {}).get("door_close_t")
    if dc:
        pts.append((S[4]["start"] + dc, "S4 door"))
    if TL.has_beat("s5_silence"):
        pts.append((S[5]["start"] + TL.beat("s5_silence").t, "S5 silence"))
    return sorted(pts)


def edit_jumps(x, pts, w=0.002, ctx=0.03):
    """At each edit point: the largest sample-to-sample jump within +-w vs the median jump around it."""
    if x.ndim == 2:
        x = x.mean(axis=1)
    out = []
    for t, name in pts:
        i = int(round(t * SR))
        a, b = max(1, i - int(w * SR)), min(len(x), i + int(w * SR))
        d = np.abs(np.diff(x[a - 1: b]))
        c = np.abs(np.diff(x[max(1, i - int(ctx * SR)): min(len(x), i + int(ctx * SR))]))
        med = float(np.median(c)) + 1e-9
        out.append(dict(t=round(t, 4), at=name, max_jump=round(float(d.max()), 5), median=round(med, 6),
                        ratio=round(float(d.max()) / med, 1)))
    return out


def xcorr_lag(a, b, maxlag):
    """Lag (samples) maximizing correlation of a (reference) against b, within +-maxlag."""
    n = len(a) + len(b)
    m = 1 << int(np.ceil(np.log2(n)))
    c = np.fft.irfft(np.fft.rfft(b, m) * np.conj(np.fft.rfft(a, m)), m)
    lags = np.concatenate([np.arange(0, maxlag + 1), np.arange(-maxlag, 0)])
    vals = np.concatenate([c[: maxlag + 1], c[-maxlag:]])
    return int(lags[np.argmax(vals)]), float(vals.max() / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def hold_loop_analysis(music, s0, t0, t1):
    """The S3 music box: (1) the pitch of every scheduled note from the NEW energy at its onset, (2) the blind
    count of strong spectral peaks over the whole hold, (3) the loop period from the band envelope."""
    from film.audio import motif as M
    x = music[s0 + int(t0 * SR): s0 + int(t1 * SR)].mean(axis=1)
    nfft = 1 << 15
    f = np.fft.rfftfreq(nfft, 1 / SR)
    band = (f > 600) & (f < 1100)
    notes = []
    for st, d, m in M.hold_music_events(t1 - t0, t0=t0)[:16]:
        a = int((st - t0) * SR)
        if a - 4800 < 0 or a + 5800 > len(x):
            continue
        new = np.abs(np.fft.rfft(x[a + 960: a + 5760] * np.hanning(4800), nfft)) ** 2
        old = np.abs(np.fft.rfft(x[a - 4800: a] * np.hanning(4800), nfft)) ** 2
        flux = np.maximum(new - old, 0)
        fp = f[band][np.argmax(flux[band])]
        notes.append(dict(t=round(st, 3), expected=M.note_name(m), found_hz=round(float(fp), 1),
                          found=M.note_name(int(round(69 + 12 * math.log2(fp / 440.0)))),
                          cents_off=round(1200 * math.log2(fp / (440 * 2 ** ((m - 69) / 12))), 0)))
    P = np.abs(np.fft.rfft(x * np.hanning(len(x)), 1 << 20)) ** 2
    ff = np.fft.rfftfreq(1 << 20, 1 / SR)
    m = (ff > 600) & (ff < 1100)
    Pd = 10 * np.log10(P[m] + 1e-20)
    fb = ff[m]
    peaks = []
    for i in np.argsort(-Pd):
        if Pd[i] < Pd.max() - 15:
            break
        if all(abs(fb[i] - q) > 25 for q in peaks):
            peaks.append(float(fb[i]))
    hop = 480
    e = np.array([np.sum(x[i:i + hop] ** 2) for i in range(0, len(x) - hop, hop)])
    e = np.log(e + 1e-12)
    e -= e.mean()
    ac = np.correlate(e, e, "full")[len(e) - 1:]
    lo, hi = int(1.0 * SR / hop), int(2.0 * SR / hop)
    period = (lo + int(np.argmax(ac[lo:hi]))) * hop / SR
    return dict(notes=notes, peaks_hz=sorted(round(p, 1) for p in peaks), period_s=round(period, 3))


_NUM = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five"}


def _norm_words(t):
    t = t.lower().replace("—", " ").replace("…", " ").replace("-", " ")
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    return [_NUM.get(w, w) for w in t.split()]


def wer(ref, hyp):
    r, h = _norm_words(ref), _norm_words(hyp)
    d = np.zeros((len(r) + 1, len(h) + 1), int)
    d[:, 0] = np.arange(len(r) + 1)
    d[0, :] = np.arange(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    return d[len(r), len(h)] / max(1, len(r))


def asr_check(mix, dl, rep, model="small.en"):
    """Intelligibility in context: Whisper transcribes every line from the MIX (and from the dry dialogue stem
    for reference); WER against the script.  Needs faster-whisper + a cached model (HF_HOME)."""
    from faster_whisper import WhisperModel
    from scipy.signal import resample_poly
    asr = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=2)
    rows = []
    for ln in rep["lines"]:
        L = TL.line(ln["id"])
        if L.id.endswith("laugh"):
            continue
        a = max(0, ln["sample"] - int(0.2 * SR))
        b = ln["sample"] + int((ln["dur"] + 0.3) * SR)
        res = {}
        for name, src in (("mix", mix), ("dry", dl)):
            x = resample_poly(src[a:b].mean(axis=1), 1, 3).astype(np.float32)
            segs, _ = asr.transcribe(x, language="en", beam_size=5, vad_filter=False,
                                     condition_on_previous_text=False)
            txt = " ".join(sg.text.strip() for sg in segs).strip()
            res[name] = (txt, round(wer(L.text, txt), 3))
        rows.append(dict(id=L.id, text=L.text, mix=res["mix"][0], wer_mix=res["mix"][1], dry=res["dry"][0],
                         wer_dry=res["dry"][1]))
    return rows


def run():
    import soundfile as sf
    os.makedirs(VER, exist_ok=True)
    rep = json.load(open(os.path.join(AUD, "mix_report.json")))
    mix, sr = sf.read(os.path.join(AUD, "mix.wav"))
    info = sf.info(os.path.join(AUD, "mix.wav"))
    stems = {k: sf.read(os.path.join(AUD, f"stem_{k}.wav"))[0] for k in ("dialogue", "music", "sfx", "amb")}
    N = rep["samples"]
    scenes = rep["scenes"]
    S = {sc["id"]: sc for sc in scenes}
    out = {"format": dict(sr=info.samplerate, channels=info.channels, subtype=info.subtype, frames=info.frames,
                          expected=N, seconds=round(info.frames / sr, 4), timeline_total=TL.total(),
                          ok=bool(info.samplerate == 48000 and info.channels == 2 and info.subtype == "PCM_24"
                                  and info.frames == N))}
    ssum = sum(stems.values())
    out["stem_sum_max_err"] = float(np.abs(ssum - mix).max())
    # -------- loudness ------------------------------------------------------------------------------
    path = os.path.join(AUD, "mix.wav")
    out["ebur128"] = {"overall": ebur128(path)}
    for sc in scenes:
        out["ebur128"][f"S{sc['id']}"] = ebur128(path, sc["s0"] / SR, sc["n"] / SR)
    out["numpy"] = dict(lufs=round(SONG.kweight_lufs(mix), 2), true_peak=round(true_peak(mix), 2))
    for k, v in stems.items():
        out["numpy"][f"{k}_lufs"] = round(SONG.kweight_lufs(v), 2) if np.any(v) else None
    tt, mom = momentary(mix)
    # -------- dialogue: DBR + timing -------------------------------------------------------------------
    dl = stems["dialogue"]
    bg = mix - dl
    rows = []
    for ln in rep["lines"]:
        L = TL.line(ln["id"])
        a = ln["sample"]
        n = int(ln["dur"] * SR)
        pad = int(0.02 * SR)
        Ed = band_energy(dl[a - pad: a + n + pad])
        Eb = band_energy(bg[a - pad: a + n + pad])
        act = Ed > Ed.max() * 10 ** (-20 / 10)
        dbr = 10 * math.log10(Ed[act].sum() / (Eb[act].sum() + 1e-18))
        fr = 10 * np.log10(Ed[act] / (Eb[act] + 1e-18))
        row = dict(id=ln["id"], speaker=ln["speaker"], t=ln["t"], dbr_db=round(dbr, 1),
                   dbr_p10_db=round(float(np.percentile(fr, 10)), 1), fx=ln.get("fx"))
        if ln["id"] == "s4_l1" and TL.has_beat("s4_swell"):
            sw = S[4]["start"] + TL.beat("s4_swell").t
            hop = 480
            tf = (a - pad) / SR + (np.arange(len(Ed)) * hop + 1024) / SR
            pre, post = act & (tf < sw), act & (tf >= sw + 0.3)
            row["dbr_before_swell_db"] = round(10 * math.log10(Ed[pre].sum() / (Eb[pre].sum() + 1e-18)), 1) if pre.any() else None
            row["dbr_after_swell_db"] = round(10 * math.log10(Ed[post].sum() / (Eb[post].sum() + 1e-18)), 1) if post.any() else None
        lv_line = SONG.kweight_lufs(dl[a: a + n]) if n > int(0.45 * SR) else None
        row["lufs"] = round(lv_line, 1) if lv_line is not None else None
        src, _ = sf.read(os.path.join(ROOT, L.wav))
        seg = dl[a: a + len(src)].mean(axis=1)
        lag, corr = xcorr_lag(src, seg, int(0.05 * SR))
        row.update(lag_samples=lag, corr=round(corr, 3), placed_s=round(a / SR, 4),
                   timeline_global_s=round(S[L.scene]["start"] + L.start, 4))
        rows.append(row)
    out["dialogue"] = rows
    man = [r["lufs"] for r in rows if r["speaker"] == "MAN" and r["fx"] is None and not r["id"].endswith("laugh")
           and r["lufs"] is not None]
    lg = [r["lufs"] for r in rows if r["id"].endswith("laugh")]
    out["laugh_vs_dialogue_db"] = round(lg[0] - float(np.median(man)), 1) if lg and man else None
    out["stems_per_scene_lufs"] = {}
    for sc in scenes:
        a_, b_ = sc["s0"], sc["s0"] + sc["n"]
        out["stems_per_scene_lufs"][f"S{sc['id']}"] = {k: (round(SONG.kweight_lufs(v[a_:b_]), 1) if np.any(v[a_:b_])
                                                           else None) for k, v in stems.items()}
    bad = [r for r in rows if r["id"] != "s4_l1" and r["dbr_db"] < 8.0]
    out["dialogue_summary"] = dict(min_dbr=min(r["dbr_db"] for r in rows if r["id"] != "s4_l1"),
                                   failing=[r["id"] for r in bad], max_abs_lag=max(abs(r["lag_samples"]) for r in rows))
    # -------- clicks ------------------------------------------------------------------------------------
    out["clicks"] = {"mix": detect_clicks(mix)}
    for k, v in stems.items():
        out["clicks"][k] = detect_clicks(v)
    out["edits"] = edit_jumps(mix, edit_points(rep))
    edits_png(mix, edit_points(rep), os.path.join(VER, "edits.png"))
    # -------- story beats -------------------------------------------------------------------------------
    beats = {}
    if TL.has_beat("s3_hold"):
        h = TL.beat("s3_hold").t
        beats["hold"] = hold_loop_analysis(stems["music"], S[3]["s0"], h, S[3]["dur"] - 0.02)
    if TL.has_beat("s4_swell"):
        sw = S[4]["start"] + TL.beat("s4_swell").t
        ms = stems["music"]
        def lv(a, b):
            seg = ms[int(a * SR): int(b * SR)]
            return 10 * math.log10(np.mean(seg ** 2) + 1e-20)
        beats["swell"] = dict(t=round(sw, 3), break_db=round(lv(sw - 0.9, sw - 0.1), 1),
                              swell_db=round(lv(sw + 0.1, sw + 1.5), 1),
                              rise_db=round(lv(sw + 0.1, sw + 1.5) - lv(sw - 0.9, sw - 0.1), 1))
        ins = S[4]["start"] + (TL.beat("s4_inside").t if TL.has_beat("s4_inside") else 6.3)
        beats["tavern_inside_jump_db"] = round(lv(ins + 0.05, ins + 1.0) - lv(ins - 1.0, ins - 0.05), 1)
    if TL.has_beat("s5_silence"):
        si = S[5]["start"] + TL.beat("s5_silence").t
        def mlv(a, b):
            seg = mix[int(a * SR): int(b * SR)]
            return 10 * math.log10(np.mean(seg ** 2) + 1e-20)
        sel = (tt > si + 0.25) & (tt < si + 2.0)
        beats["silence"] = dict(t=round(si, 3), before_db=round(mlv(si - 1.0, si - 0.05), 1),
                                after_db=round(mlv(si + 0.3, si + 1.5), 1),
                                drop_db=round(mlv(si - 1.0, si - 0.05) - mlv(si + 0.3, si + 1.5), 1),
                                momentary_max_after=round(float(mom[sel].max()), 1) if sel.any() else None)
    if TL.has_beat("s6_laugh"):
        lg = S[6]["start"] + TL.beat("s6_laugh").t
        ms = stems["music"][int(S[6]["start"] * SR): int((lg + 4) * SR)].mean(axis=1)
        env = np.sqrt(np.convolve(ms * ms, np.ones(480) / 480, "same"))
        on = np.nonzero(env > 10 ** (-60 / 20))[0]
        beats["score_first_sound_s"] = round(S[6]["start"] + on[0] / SR, 3) if len(on) else None
        beats["laugh_s"] = round(lg, 3)
        pre = stems["music"][int(S[6]["start"] * SR): int((lg - 0.2) * SR)]
        beats["music_before_laugh_db"] = round(10 * math.log10(np.mean(pre ** 2) + 1e-20), 1)
    steps = []
    for sc in scenes[1:]:
        t = sc["start"]
        a = mom[(tt > t - 1.2) & (tt < t - 0.25)]
        b = mom[(tt > t + 0.25) & (tt < t + 1.2)]
        steps.append(dict(scene=sc["id"], t=round(t, 3), before=round(float(np.median(a)), 1) if len(a) else None,
                          after=round(float(np.median(b)), 1) if len(b) else None))
    beats["boundaries"] = steps
    out["beats"] = beats
    # -------- PNGs -------------------------------------------------------------------------------------
    pngs = []
    cols = {"MAN": (120, 220, 255), "OLD_WOMAN": (255, 170, 220), "PHARMACIST": (180, 255, 160),
            "PHONE": (255, 255, 120), "BOUNCER": (255, 150, 90), "CROWD": (200, 160, 255), "BARD": (255, 220, 150)}
    for sc in scenes:
        s = sc["id"]
        a, b = sc["s0"], sc["s0"] + sc["n"]
        spans = [(l.start, l.end, l.id.split("_", 1)[1], cols.get(l.speaker, (255, 255, 255)))
                 for l in TL.lines_in(s)]
        marks = [(bt.t, bt.id.split("_", 1)[1], (255, 255, 0)) for bt in TL.beats_in(s)]
        for c in rep["cues"].get(f"S{s}", {}).get("cues", [])[:0]:
            marks.append((c["t"], c["kind"][:6], (120, 255, 120)))
        sel = (tt >= a / SR) & (tt < b / SR)
        p = os.path.join(VER, f"spec_s{s}.png")
        spectro_png(mix[a:b], p, 0.0, pps=46 if sc["dur"] < 30 else 30, marks=marks, spans=spans,
                    title=f"S{s} {sc['name']}  (mix; local time; beats yellow, lines coloured; momentary LUFS below)",
                    curve=(tt[sel] - a / SR, mom[sel]), top_db=None, dyn=80)
        pngs.append(p)
    # zooms
    if TL.has_beat("s3_hold"):
        h = TL.beat("s3_hold").t
        a = S[3]["s0"] + int((h - 0.3) * SR)
        p = os.path.join(VER, "zoom_hold_loop.png")
        spectro_png(stems["music"][a: a + int(5.0 * SR)], p, h - 0.3, fmin=300, fmax=3500, logf=False, pps=200,
                    title="S3 hold loop (music stem, linear 300-3500 Hz)", dyn=60)
        pngs.append(p)
    if TL.has_beat("s4_swell"):
        sw = TL.beat("s4_swell").t
        a = S[4]["s0"] + int((sw - 3.0) * SR)
        p = os.path.join(VER, "zoom_swell.png")
        spectro_png(mix[a: a + int(6.0 * SR)], p, sw - 3.0, fmin=60, fmax=12000, pps=120,
                    marks=[(sw, "swell", (255, 80, 80))], spans=[(l.start, l.end, l.id, (120, 220, 255))
                                                                for l in TL.lines_in(4) if l.id == "s4_l1"],
                    title="S4 swell burying s4_l1 (mix)", dyn=75,
                    curve=(tt[(tt >= a / SR) & (tt < a / SR + 6)] - a / SR + sw - 3.0,
                           mom[(tt >= a / SR) & (tt < a / SR + 6)]))
        pngs.append(p)
    if TL.has_beat("s5_silence"):
        si = TL.beat("s5_silence").t
        a = S[5]["s0"] + int((si - 3.0) * SR)
        p = os.path.join(VER, "zoom_silence.png")
        sel = (tt >= a / SR) & (tt < a / SR + 6)
        spectro_png(mix[a: a + int(6.0 * SR)], p, si - 3.0, fmin=40, fmax=16000, pps=120,
                    marks=[(si, "silence", (255, 80, 80))], title="S5 cut to silence (mix)", dyn=90, top_db=None,
                    curve=(tt[sel] - a / SR + si - 3.0, mom[sel]))
        pngs.append(p)
    if TL.has_beat("s6_laugh"):
        lg = TL.beat("s6_laugh").t
        a = S[6]["s0"] + int((lg - 2.0) * SR)
        p = os.path.join(VER, "zoom_score_entry.png")
        spectro_png(stems["music"][a: a + int(7.0 * SR)], p, lg - 2.0, fmin=100, fmax=6000, pps=110,
                    marks=[(lg, "laugh", (255, 255, 0)), (S[7]["start"] - S[6]["start"], "S7", (0, 255, 0))],
                    title="score entering at the laugh (music stem; S6 local)", dyn=70)
        pngs.append(p)
    # whole-film overview: momentary loudness of each stem
    p = os.path.join(VER, "overview.png")
    spectro_png(mix, p, 0.0, pps=6, height=260, marks=[(sc["start"], f"S{sc['id']}", (0, 255, 0)) for sc in scenes],
                title="whole film (mix) + momentary LUFS", curve=(tt, mom), dyn=80)
    pngs.append(p)
    out["pngs"] = pngs
    with open(os.path.join(VER, "check.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=float)
    return out


def summary(o):
    f = o["format"]
    print(f"format: {f['sr']} Hz, {f['channels']} ch, {f['subtype']}, {f['frames']} frames "
          f"({f['seconds']} s; expected {f['expected']}) -> {'OK' if f['ok'] else 'FAIL'}; "
          f"stem sum max err {o['stem_sum_max_err']:.2e}")
    e = o["ebur128"]["overall"]
    print(f"overall (ffmpeg ebur128): I {e.get('I')} LUFS, LRA {e.get('LRA')} LU, TP {e.get('TP')} dBTP | numpy: "
          f"{o['numpy']['lufs']} LUFS, TP {o['numpy']['true_peak']} dBTP")
    print("per scene: " + "  ".join(f"S{k[1:]} {v.get('I')}/{v.get('TP')}" for k, v in o["ebur128"].items()
                                    if k != "overall"))
    print("stems LUFS: " + ", ".join(f"{k} {v}" for k, v in o["numpy"].items() if k.endswith("_lufs")))
    print("stems per scene (LUFS: dialogue / music / sfx / amb):")
    for k, v in o["stems_per_scene_lufs"].items():
        print(f"   {k}: " + " / ".join(f"{v[n]}" for n in ("dialogue", "music", "sfx", "amb")))
    print(f"laugh vs median dragon line: {o['laugh_vs_dialogue_db']} dB")
    print("dialogue (DBR dB in 300-4000 Hz | p10 | lag | line LUFS):")
    for r in o["dialogue"]:
        extra = ""
        if "dbr_before_swell_db" in r:
            extra = f"  before swell {r['dbr_before_swell_db']}  after {r['dbr_after_swell_db']}"
        flag = "" if r["id"] == "s4_l1" or r["dbr_db"] >= 8 else "   <-- LOW"
        print(f"   {r['id']:9s} {r['speaker']:10s} {r['dbr_db']:6.1f} | {r['dbr_p10_db']:6.1f} | {r['lag_samples']:+d} | "
              f"{r['lufs']}{extra}{flag}")
    ds = o["dialogue_summary"]
    print(f"   min DBR {ds['min_dbr']} dB, failing {ds['failing']}, max |lag| {ds['max_abs_lag']} samples")
    print("clicks (HF discontinuities): " + ", ".join(f"{k} {len(v)}" for k, v in o["clicks"].items()))
    for k, v in o["clicks"].items():
        if v:
            print(f"   {k}: " + ", ".join(f"{t}s(x{r},{db}dB)" for t, r, db in v[:8]))
    print("edit points (max jump / local median): " +
          "  ".join(f"{e['at']} {e['ratio']}" for e in o["edits"]))
    b = o["beats"]
    if "hold" in b:
        hh = b["hold"]
        ok = all(n["expected"] == n["found"] for n in hh["notes"])
        print(f"hold loop: notes {'all match' if ok else 'MISMATCH'} "
              f"{[n['found'] for n in hh['notes'][:8]]} | spectral peaks {hh['peaks_hz']} Hz | period {hh['period_s']} s")
    for k in ("swell", "silence"):
        if k in b:
            print(f"{k}: {b[k]}")
    print(f"tavern inside jump: {b.get('tavern_inside_jump_db')} dB; score first sound {b.get('score_first_sound_s')}"
          f" vs laugh {b.get('laugh_s')} (music before laugh {b.get('music_before_laugh_db')} dB)")
    print("boundaries (momentary LUFS median before -> after): " +
          "  ".join(f"S{x['scene']} {x['before']}->{x['after']}" for x in b["boundaries"]))


if __name__ == "__main__":
    o = run()
    summary(o)
    if "--asr" in sys.argv:
        import soundfile as sf
        mname = sys.argv[sys.argv.index("--asr-model") + 1] if "--asr-model" in sys.argv else "small.en"
        rep = json.load(open(os.path.join(AUD, "mix_report.json")))
        mix, _ = sf.read(os.path.join(AUD, "mix.wav"))
        dl, _ = sf.read(os.path.join(AUD, "stem_dialogue.wav"))
        rows = asr_check(mix, dl, rep, model=mname)
        o["asr"] = rows
        with open(os.path.join(VER, "check.json"), "w") as fh:
            json.dump(o, fh, indent=1, default=float)
        print(f"ASR (Whisper {mname}) WER  mix | dry   transcript from the mix")
        for r in rows:
            print(f"   {r['id']:8s} {r['wer_mix']:.2f} | {r['wer_dry']:.2f}   {r['mix']}")
        ok = [r for r in rows if r["id"] != "s4_l1"]
        print(f"   mean WER (mix, excl. drowned s4_l1): {np.mean([r['wer_mix'] for r in ok]):.3f}")
