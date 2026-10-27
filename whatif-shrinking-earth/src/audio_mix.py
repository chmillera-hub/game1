"""Build the full soundtrack: voice + score + accents + SFX + ambience -> mix.wav.

Run: python audio_mix.py   (needs build/timeline.json and build/voice/*.wav)
Writes paths.AUDIO/{voice,music,sfx,mix}.wav and mix_report.json, and a
spectrogram/level overview PNG for visual inspection.
"""
import json
import os
import sys
import time

import numpy as np
import pyloudnorm
import soundfile as sf

import paths
import timeline
from audio_dsp import (SR, ar_smooth, block_rms_db, compress, convolve, eq, hp, limiter, make_ir, ns, true_peak,
                       upsample_ctrl)
import music
import sfx

TARGET_LUFS = -16.0
CEILING_DBTP = -1.6
DUCK_MUSIC_DB = -9.0
DUCK_AMB_DB = -6.0
DUCK_ACC_DB = -3.0
SCRATCH_TESTS = os.path.join(os.path.dirname(paths.BUILD), "tests")


def log(*a):
    print(*a, flush=True)


def place_voice(tl):
    n = ns(tl["total"])
    chars = np.zeros(n)
    narr = np.zeros(n)
    for ln in tl["lines"]:
        a, sr = sf.read(os.path.join(paths.VOICE, f"{ln['id']}.wav"), dtype="float64")
        assert sr == SR, sr
        if a.ndim > 1:
            a = a.mean(axis=1)
        i = ns(ln["start"])
        j = min(n, i + len(a))
        (narr if ln["speaker"] == "NARRATOR" else chars)[i:j] += a[: j - i]
    return chars, narr


def deess(x, lo=4800, hi=11500, thresh_db=-30.0, max_red_db=7.0, ratio=0.6):
    """Split-band de-esser: tame strong sibilants only."""
    from audio_dsp import bp
    hb = bp(x, lo, hi, 2)
    lev, b = block_rms_db(hb, 0.003)
    full, _ = block_rms_db(x, 0.003)
    over = np.clip(lev - thresh_db, 0, None) * ratio
    over = np.minimum(over, max_red_db) * (lev > full - 9)
    red = ar_smooth(over, 0.002, 0.06, 0.003)
    g = upsample_ctrl(10 ** (-red / 20), b, len(x))
    return x - hb + hb * g


def process_voice(chars, narr):
    out = []
    for k, x in enumerate((chars, narr)):
        y = hp(x, 75, 2)
        if k == 0:
            y = deess(y)
        else:
            # the narrator voice is bright and sibilant: shelf down the top, de-ess harder
            y = eq(y, ("highshelf", 6500, 0.7, -2.5))
            y = deess(y, 4500, 12000, thresh_db=-35.0, max_red_db=9.0, ratio=0.75)
        y = compress(y, thresh_db=-27.0, ratio=2.2, attack=0.004, release=0.09, makeup_db=1.5)
        out.append(y)
    chars, narr = out
    # gentle peak control so speech transients don't drive the master limiter
    both = np.stack([chars + narr, chars + narr])
    _, gv = limiter(both, -9.0, look=0.002, release=0.05)
    chars, narr = chars * gv, narr * gv
    ir_room = make_ir(t60=0.38, predelay=0.008, bright=0.45, seed=11, early=8, width=0.9)
    ir_narr = make_ir(t60=1.25, predelay=0.024, bright=0.3, seed=12, early=5, width=1.0)
    dry = np.stack([chars + narr, chars + narr])
    wet = 0.08 * convolve(chars, ir_room) + 0.115 * convolve(narr, ir_narr)
    return dry + wet, chars + narr


def duck_curve(voice_mono, n):
    lev, b = block_rms_db(voice_mono, 0.01)
    x = np.clip((lev + 52.0) / 14.0, 0, 1)
    x = x * x * (3 - 2 * x)
    x = ar_smooth(x, 0.06, 0.40, 0.01)
    return upsample_ctrl(x, b, n)


def lufs(meter, x):
    try:
        v = meter.integrated_loudness(x.T if x.ndim == 2 else x)
        return float(v)
    except Exception:
        return float("nan")


def to_db(x):
    return 20 * np.log10(max(1e-12, x))


def spectrogram_png(mix, stems, tl, secs, sfx_log, out_png):
    from PIL import Image, ImageDraw, ImageFont
    from scipy import signal
    mono = mix.mean(axis=0)
    f, t, Z = signal.stft(mono, fs=SR, nperseg=2048, noverlap=1024, boundary=None)
    P = 20 * np.log10(np.abs(Z) + 1e-9)
    W = 1800
    Hs = 420
    total = tl["total"]
    # time pooling
    cols = np.linspace(0, P.shape[1], W + 1).astype(int)
    Pt = np.stack([P[:, cols[i]:max(cols[i] + 1, cols[i + 1])].max(axis=1) for i in range(W)], 1)
    # log-frequency rows 30 Hz .. 16 kHz
    fr = np.geomspace(30, 16000, Hs)[::-1]
    idx = np.clip(np.searchsorted(f, fr), 0, len(f) - 1)
    img = Pt[idx]
    lo, hi = -110, -20
    v = np.clip((img - lo) / (hi - lo), 0, 1)
    # simple magma-like colormap
    stops = np.array([[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99], [212, 72, 66], [245, 125, 21],
                      [250, 193, 39], [252, 255, 164]], float)
    pos = v * (len(stops) - 1)
    k = np.clip(pos.astype(int), 0, len(stops) - 2)
    fr_ = (pos - k)[..., None]
    rgb = stops[k] * (1 - fr_) + stops[k + 1] * fr_
    H = Hs + 260
    canvas = Image.new("RGB", (W + 60, H + 40), (12, 12, 18))
    canvas.paste(Image.fromarray(rgb.astype(np.uint8)), (50, 10))
    d = ImageDraw.Draw(canvas)
    try:
        fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except Exception:
        fnt = None

    def X(tt):
        return 50 + int(tt / total * W)

    for hz in (50, 100, 200, 500, 1000, 2000, 5000, 10000):
        y = 10 + int(np.argmin(np.abs(fr - hz)))
        d.line([(44, y), (50, y)], fill=(200, 200, 200))
        d.text((2, y - 6), f"{hz if hz < 1000 else str(hz // 1000) + 'k'}", fill=(200, 200, 200), font=fnt)
    for (t0, mood) in secs:
        d.line([(X(t0), 10), (X(t0), 10 + Hs)], fill=(120, 220, 255), width=1)
        d.text((X(t0) + 2, 12), mood, fill=(160, 230, 255), font=fnt)
    colors = dict(hi=(255, 240, 120), lo=(120, 160, 255), boom=(255, 80, 80), comic=(120, 255, 140),
                  swell=(255, 150, 255))
    for ac in tl["accents"]:
        d.polygon([(X(ac["t"]) - 4, 10 + Hs + 2), (X(ac["t"]) + 4, 10 + Hs + 2), (X(ac["t"]), 10 + Hs + 10)],
                  fill=colors.get(ac["kind"], (255, 255, 255)))
    # level lanes (momentary-ish RMS, dB)
    lane_y = 10 + Hs + 18
    lane_h = 220
    d.rectangle([(50, lane_y), (50 + W, lane_y + lane_h)], outline=(70, 70, 90))
    names = list(stems.keys())
    pal = [(255, 255, 255), (255, 170, 60), (80, 220, 120), (120, 170, 255), (255, 90, 160)]
    for i, nm in enumerate(names):
        x = stems[nm]
        lev, b = block_rms_db(x, 0.4)
        lev = np.clip(lev, -70, 0)
        pts = []
        for j, l in enumerate(lev):
            tt = (j + 0.5) * 0.4
            pts.append((X(tt), lane_y + int((-l) / 70 * lane_h)))
        d.line(pts, fill=pal[i % len(pal)], width=1)
        d.text((60 + i * 110, lane_y + lane_h + 4), nm, fill=pal[i % len(pal)], font=fnt)
    for db in (-10, -20, -30, -40, -50, -60):
        y = lane_y + int(-db / 70 * lane_h)
        d.text((10, y - 6), f"{db}", fill=(150, 150, 150), font=fnt)
        d.line([(50, y), (56, y)], fill=(150, 150, 150))
    for s in range(0, int(total) + 1, 30):
        d.text((X(s) - 8, H + 24), f"{s // 60}:{s % 60:02d}", fill=(200, 200, 200), font=fnt)
    canvas.save(out_png)


def click_scan(x):
    """Isolated discontinuities: a block whose 2nd-difference peak towers over the
    block's own 95th percentile (noise and speech raise both; a click raises one)."""
    m = x.mean(axis=0)
    d2 = np.abs(np.diff(m, 2))
    b = 240
    n = len(d2) // b
    blk = d2[: n * b].reshape(n, b)
    pk = blk.max(axis=1)
    p95 = np.percentile(blk, 95, axis=1) + 1e-7
    iso = pk / p95
    bad = np.where((iso > 8) & (pk > 0.02))[0]
    bad = bad[np.argsort(-iso[bad])]
    return [(round(float(i * b / SR), 3), round(float(iso[i]), 1), round(float(pk[i]), 3)) for i in bad[:20]], \
        float(np.max(np.abs(np.diff(m))))


def _sibilance(voice_mono, tl):
    """Mean/max over lines of (5 ms 5-11 kHz band peak) - (line RMS), by speaker."""
    from scipy import signal as sg
    sos = sg.butter(4, [5000, 11000], "band", fs=SR, output="sos")
    out = {}
    for ln in tl["lines"]:
        a, b = ns(ln["start"]), ns(ln["end"])
        x = voice_mono[a:b]
        if len(x) < SR // 4:
            continue
        hb = sg.sosfilt(sos, x)
        bl = ns(0.005)
        n = len(hb) // bl
        br = np.sqrt((hb[: n * bl].reshape(n, bl) ** 2).mean(1))
        rms = np.sqrt((x ** 2).mean()) + 1e-9
        out.setdefault(ln["speaker"], []).append(20 * np.log10(br.max() / rms + 1e-9))
    return {k: [round(float(np.mean(v)), 1), round(float(np.max(v)), 1)] for k, v in out.items()}


def _hotspots(gr_db, thr):
    """Merged time ranges where the limiter reduces gain by more than thr dB."""
    b = ns(0.05)
    n = len(gr_db) // b
    pk = gr_db[: n * b].reshape(n, b).max(axis=1)
    out = []
    for i in np.where(pk > thr)[0]:
        t = i * 0.05
        if out and t - out[-1][1] <= 0.15:
            out[-1][1] = t + 0.05
            out[-1][2] = max(out[-1][2], float(pk[i]))
        else:
            out.append([t, t + 0.05, float(pk[i])])
    return [[round(a, 2), round(b_, 2), round(c, 1)] for a, b_, c in out[:30]]


def main():
    t_start = time.time()
    tl = timeline.load()
    total = tl["total"]
    n = ns(total)
    meter = pyloudnorm.Meter(SR)
    log(f"timeline total {total:.2f}s, {len(tl['lines'])} lines, {len(tl['accents'])} accents")

    log("voice ...")
    chars, narr = place_voice(tl)
    voice, voice_mono = process_voice(chars, narr)

    log("score ...")
    music_bus, ctx, sec_report = music.render_score(tl)
    log("accents ...")
    a_dry, a_hall = music.render_accents(tl, ctx, voice_mono)
    log("sfx + ambience ...")
    s_dry, s_hall, amb, sfx_log, gate = sfx.render_sfx(tl)

    log("reverbs ...")
    ir_room, ir_hall = music.irs()
    acc_bus = a_dry + 0.6 * convolve(a_hall, ir_hall)
    sfx_bus = s_dry + 0.6 * convolve(s_hall, ir_hall)

    # music fades to nothing at the very end
    tail = np.clip((total - np.arange(n) / SR) / 2.5, 0, 1) ** 1.5
    music_bus *= tail
    acc_bus *= tail

    log("ducking ...")
    d = duck_curve(voice_mono, n)
    g_music = 10 ** (DUCK_MUSIC_DB * d / 20)
    g_amb = 10 ** (DUCK_AMB_DB * d / 20)
    g_acc = 10 ** (DUCK_ACC_DB * d / 20)
    music_d = music_bus * g_music
    acc_d = acc_bus * g_acc
    amb_d = amb * g_amb

    mix = voice + music_d + acc_d + amb_d + sfx_bus
    mix = hp(mix, 28, 2)
    mix -= mix.mean(axis=1, keepdims=True)
    for k in range(3):
        L = lufs(meter, mix)
        mix *= 10 ** ((TARGET_LUFS - L) / 20)
        mix, gr = limiter(mix, CEILING_DBTP, look=0.004, release=0.12)
        gr_db = -20 * np.log10(np.maximum(gr, 1e-9))
        L2 = lufs(meter, mix)
        log(f"  master pass {k}: {L:.2f} -> {L2:.2f} LUFS, max gain reduction {to_db(gr.min()):.2f} dB")
        if abs(L2 - TARGET_LUFS) < 0.25:
            break
    tp = true_peak(mix)
    sp = float(np.max(np.abs(mix)))
    if tp > 10 ** (CEILING_DBTP / 20) * 1.02:
        mix *= 10 ** (CEILING_DBTP / 20) / tp * 0.995
        tp = true_peak(mix)
    # short fades so the file never starts or ends on a click
    fs_ = ns(0.02)
    mix[:, :fs_] *= np.linspace(0, 1, fs_)
    fe = ns(0.25)
    mix[:, -fe:] *= np.linspace(1, 0, fe)

    log("writing ...")
    os.makedirs(paths.AUDIO, exist_ok=True)

    def wr(name, x):
        pk = np.max(np.abs(x)) + 1e-12
        y = x / pk * 0.98 if pk > 0.98 else x
        sf.write(os.path.join(paths.AUDIO, name), y.T.astype(np.float32), SR, subtype="PCM_16")

    wr("voice.wav", voice)
    wr("music.wav", music_bus + acc_bus)
    wr("sfx.wav", sfx_bus + amb)
    sf.write(os.path.join(paths.AUDIO, "mix.wav"), mix.T.astype(np.float32), SR, subtype="PCM_16")

    log("verifying ...")
    speech = d > 0.6
    quiet = d < 0.05

    def rms_db(x, mask):
        if mask.sum() < SR:
            return float("nan")
        return to_db(np.sqrt(np.mean(x[:, mask] ** 2)))

    rep = dict(
        duration_s=round(total, 3),
        mix_lufs=round(lufs(meter, mix), 2),
        mix_true_peak_dbtp=round(to_db(tp), 2),
        mix_sample_peak_dbfs=round(to_db(np.max(np.abs(mix))), 2),
        dc_offset=[float(v) for v in mix.mean(axis=1)],
        nan=bool(np.isnan(mix).any() or np.isinf(mix).any()),
        stems_lufs=dict(voice=round(lufs(meter, voice), 2), music=round(lufs(meter, music_bus + acc_bus), 2),
                        music_ducked=round(lufs(meter, music_d + acc_d), 2), sfx=round(lufs(meter, sfx_bus), 2),
                        ambience=round(lufs(meter, amb_d), 2)),
        duck_music_db=round(rms_db(music_d, speech) - rms_db(music_bus, speech), 2),
        music_rms_speech_vs_gaps_db=[round(rms_db(music_d, speech), 2), round(rms_db(music_d, quiet), 2)],
        voice_rms_speech_db=round(rms_db(voice, speech), 2),
        limiter_gr_db=dict(max=round(float(gr_db.max()), 2), p99=round(float(np.percentile(gr_db, 99)), 2),
                           time_over_1db_s=round(float((gr_db > 1.0).sum() / SR), 2),
                           hotspots=_hotspots(gr_db, 1.5)),
    )
    # accent peaks relative to the voice (pre-duck, pre-master)
    accp = []
    for ac in tl["accents"]:
        a, b = ns(ac["t"] - 0.05), ns(ac["t"] + 0.6)
        accp.append((ac["line"], ac["word"], ac["kind"], round(to_db(np.max(np.abs(acc_bus[:, a:b]))), 1),
                     round(to_db(np.max(np.abs(voice[:, a:b]))), 1)))
    rep["accent_peaks_dbfs_vs_voice"] = accp
    # sibilance after processing: 5 ms HF-band peak over speech RMS, per speaker group
    rep["sibilance_db"] = _sibilance(voice_mono, tl)
    sec = []
    secs = [(t0, m) for (m, t0, t1, lu, gdb) in sec_report]
    for (m, t0, t1, lu, gdb) in sec_report:
        a, b = ns(t0), ns(t1)
        seg_mix = mix[:, a:b]
        seg_mus = (music_d + acc_d)[:, a:b]
        sec.append(dict(mood=m, t0=round(t0, 2), t1=round(t1, 2),
                        mix_lufs=round(lufs(meter, seg_mix), 1) if b - a > SR else None,
                        music_lufs=round(lufs(meter, seg_mus), 1) if b - a > SR else None))
    rep["sections"] = sec
    clicks, maxdiff = click_scan(mix)
    rep["click_candidates"] = clicks
    rep["max_sample_step"] = round(maxdiff, 4)
    # silence check: everything but the voice between "And then" and "silence"
    try:
        import anchors
        ts = anchors.resolve(anchors.Wd("L47", "silence"))
        a, b = ns(ts - 1.0), ns(ts - 0.1)
        rest = (music_d + acc_d + sfx_bus + amb_d)[:, a:b]
        rep["silence_moment_nonvoice_rms_dbfs"] = round(to_db(np.sqrt(np.mean(rest ** 2))), 1)
    except Exception as e:
        rep["silence_moment_nonvoice_rms_dbfs"] = str(e)
    rep["sfx_events"] = [(round(t, 2), k, round(p, 1)) for t, k, p in sfx_log]
    rep["runtime_s"] = round(time.time() - t_start, 1)
    json.dump(rep, open(os.path.join(paths.AUDIO, "mix_report.json"), "w"), indent=1)

    os.makedirs(SCRATCH_TESTS, exist_ok=True)
    png = os.path.join(SCRATCH_TESTS, "mix_spectrogram.png")
    spectrogram_png(mix, {"mix": mix, "voice": voice, "music": music_d + acc_d, "sfx": sfx_bus, "amb": amb_d},
                    tl, secs, sfx_log, png)
    log(json.dumps({k: v for k, v in rep.items() if k not in ("sections", "sfx_events")}, indent=1))
    for s in sec:
        log(f"  {s['mood']:8s} {s['t0']:7.2f}-{s['t1']:7.2f} mix {s['mix_lufs']} music {s['music_lufs']}")
    log(f"spectrogram: {png}")
    log(f"done in {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
