#!/usr/bin/env python3
"""Psalm 22 - final mix.

narration (EQ, de-ess, gentle compression, small room)  +  music  +  sfx
-> phrase-driven ducking (phrases.json) with a per-phrase intelligibility guarantee
-> loudness normalisation to -14 LUFS integrated, true-peak limiter at -1 dBTP (ceiling -1.3)

Usage:  /opt/venv/bin/python psalm22/audio/mix.py [--whisper] [--no-analysis]
Inputs ($WORK/audio): narration.wav, phrases.json, music.wav, stems/sfx_*.wav
Outputs:
  $WORK/audio/mix.wav                 48 kHz stereo PCM 24-bit, final soundtrack (timing = narration)
  $WORK/audio/stems/mix_{narration,music,sfx}.wav   post-fader stems (pre-limiter, same gain staging)
  $WORK/audio/mix.m4a                 AAC-LC (AAC_KBPS, default 96k) with verified decoded TP <= -1 dBTP
  $WORK/audio/mix_report.json         loudness, true peak, per-phrase voice/music margins
  $WORK/dev/audio/excerpt.mp3         first 90 s
  $WORK/dev/audio/mix_overview.png    waveform/levels/spectrogram (for visual QA)
"""
import argparse, json, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp  # noqa: E402
from dsp import SR  # noqa: E402

OUT = dsp.AUDIO
TARGET_LUFS = -14.0
CEILING_DB = -2.0          # limiter ceiling: leaves ~1 dB for AAC (64-96 kbps) decoder overshoot so the
                           # final MP4 stays <= -1 dBTP as well (measured: +0.8..1 dB with a 15.5 kHz LP)
MASTER_LP_HZ = 15500
AAC_KBPS = int(os.environ.get("AAC_KBPS", "96"))   # mix.m4a: ready-to-mux AAC, decoded TP <= -1 dBTP       # AAC at these bitrates drops >15 kHz anyway; band-limiting first avoids overshoot
# ducking
PRE, POST, BRIDGE = .30, .55, 1.0     # s before phrase / after phrase / merge gaps shorter than this
MUSIC_DUCK_DB = -6.0                  # minimum duck under narration
MUSIC_MARGIN_DB = 12.5                # music must sit at least this far below the voice (speech band)
# sfx stems: (minimum duck, margin) - beds are ducked like music, short spot effects much less
SFX_DUCK = {"amb": (-4.0, 15.0), "fx": (-1.5, 9.5), "trans": (-3.0, 10.0)}
LAST_PHRASE_MARGIN_DB = 6.0           # "He has done it!" - the climax lands on this phrase
# lighter ducking for the resurrection, and a margin that shrinks phrase by phrase through the final
# build so the crescendo is heard under the voice (list = per phrase of the block)
MUSIC_MARGIN_BLOCK = {"b15": 10.0, "b20": [12.0, 11.0, 9.5, 8.5]}
NARR_PEAK_OVER_LUFS = 13.0            # narration peak limiter ceiling relative to its loudness
MUSIC_PEAK_OVER_VOICE = 1.0           # loudest music passage vs voice loudness (short-term, speech band)
AMB_BELOW_VOICE = 21.0                # ambience bed integrated loudness below the voice


# ============================================================================ narration chain
def deesser(x, f_lo=4800, f_hi=10000, thresh_db=-30, ratio=4.0):
    band = dsp.filt(dsp.filt(x, "hp", f_lo, order=2), "lp", f_hi, order=1)
    env = np.sqrt(dsp.smooth(band ** 2, .003) + 1e-12)
    full = np.sqrt(dsp.smooth(x ** 2, .01) + 1e-12)
    # only act when the band is both loud and dominant (true sibilance)
    over = dsp.db(env) - thresh_db
    dom = dsp.db(env) - dsp.db(full) + 6
    red_db = np.where((over > 0) & (dom > 0), -over * (1 - 1 / ratio), 0.0)
    red_db = np.maximum(red_db, -9.0)
    g = dsp.undb(dsp.smooth(red_db, .002))
    return x - band * (1 - g), red_db


def compressor(x, thresh_db=-24, ratio=2.2, attack=.012, release=.18, knee=6):
    from scipy.signal import lfilter
    lvl = dsp.db(np.sqrt(dsp.smooth(x ** 2, .005) + 1e-12))
    over = lvl - thresh_db
    gr = np.where(over <= -knee / 2, 0.0,
                  np.where(over >= knee / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    # attack/release smoothing of the gain reduction
    a_a, a_r = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    # vectorised approximation: fast smoother for rising GR, slow for falling GR
    fast = lfilter([1 - a_a], [1, -a_a], gr)
    slow = lfilter([1 - a_r], [1, -a_r], gr)
    out = np.maximum(fast, slow)          # fast attack, slow release
    return x * dsp.undb(-out), out


def process_narration(v):
    v = dsp.hp(v, 75, order=2)
    v = dsp.filt(v, "peak", 220, q=1.0, gain_db=-1.5)      # a little less boom/boxiness
    v = dsp.filt(v, "peak", 3200, q=.9, gain_db=2.0)       # presence
    v = dsp.filt(v, "peak", 6000, q=2.0, gain_db=-2.0)     # the TTS voice has a sibilance peak at ~6 kHz
    v, ds = deesser(v, thresh_db=-32)
    v, gr = compressor(v)
    # peak control so the master limiter barely works: peaks <= mono loudness + 14 dB
    lim_ceiling = dsp.loudness(v) + NARR_PEAK_OVER_LUFS
    v, glim = dsp.limiter(v, lim_ceiling, lookahead=.003, release=.06)
    v = v[:, 0].astype(np.float64)
    room = dsp.hall_ir(rt60=.55, predelay=.008, seed=41, bright=.8, width=.8)
    vs = dsp.reverb(v, room, wet=.07, dry=1.0)              # stereo, dry signal untouched in time
    return vs, {"deess_max_db": round(float(ds.min()), 2), "comp_max_gr_db": round(float(gr.max()), 2),
                "peak_limiter_max_gr_db": round(float(-dsp.db(glim.min())), 2)}


def leveler(x, ratio=.35, max_up=4.5, max_down=3.5, win=1.5):
    """Gentle slow dynamic-range reduction for the music bus (quiet passages up, peaks down)."""
    m = dsp.stereo(x).astype(np.float64)
    e = dsp.smooth((m ** 2).mean(1), win / 2)
    lvl = 10 * np.log10(e + 1e-12)
    act = lvl[lvl > lvl.max() - 40]
    ref = float(np.median(act))
    g = np.clip(-(lvl - ref) * ratio, -max_down, max_up)
    g = dsp.smooth(g, .6)
    return (m * dsp.undb(g)[:, None]).astype(np.float32), ref


# ============================================================================ ducking
def speech_band(x):
    return dsp.lp(dsp.hp(dsp.stereo(x).mean(1), 200, order=2), 5000, order=2)


def movavg_max_db(x2, L, step=1):
    """max over windows of length L of mean(x2) (x2 = squared signal), in dB."""
    if len(x2) <= L:
        return 10 * np.log10(np.mean(x2) + 1e-20)
    c = np.concatenate([[0.0], np.cumsum(x2)])
    e = (c[L::step] - c[:-L:step][:len(c[L::step])]) / L
    return 10 * np.log10(e.max() + 1e-20)


def rms_db(x):
    return 10 * np.log10(np.mean(np.asarray(x) ** 2) + 1e-20)


def intervals(phrases):
    """Merge phrases separated by less than BRIDGE seconds into speech runs [start, end, [phrases]]."""
    iv = []
    for p in phrases:
        a, b = p["start"], p["end"]
        if iv and a - iv[-1][1] < BRIDGE:
            iv[-1][1] = b
            iv[-1][2].append(p)
        else:
            iv.append([a, b, [p]])
    return iv


def duck_curve(n, ivs, depths_db):
    """Gain curve (dB). depths_db: per run, a list with one depth per phrase.

    Cosine ramp from 0 dB to the first phrase's depth over PRE seconds, linear moves between
    phrase depths inside a run (across the short gaps), cosine release over POST after the run.
    """
    g = np.zeros(n)
    for (a, b, ps), ds in zip(ivs, depths_db):
        pts_t, pts_v = [], []
        for p, d in zip(ps, ds):
            pts_t += [p["start"], p["end"]]
            pts_v += [d, d]
        i0, i1 = max(0, int((a - PRE) * SR)), min(n, int((b + POST) * SR))
        tt = np.arange(i0, i1) / SR
        core = np.interp(tt, pts_t, pts_v)
        w = np.ones_like(tt)
        up = tt < a
        w[up] = .5 - .5 * np.cos(np.pi * (tt[up] - (a - PRE)) / PRE)
        dn = tt > b
        w[dn] = .5 + .5 * np.cos(np.pi * (tt[dn] - b) / POST)
        g[i0:i1] = np.minimum(g[i0:i1], core * w)
    return g


def plan_ducks(voice, bus, ivs, base_db, margin_db, margins=None):
    """Per phrase: duck = min(base, (voice - margin) - bus), measured in the speech band.

    bus level = loudest 1 s window from PRE before the phrase to its end (safe for swells).
    margins: optional {phrase_index_in_film or block_id: margin_db} overrides.
    """
    vb, mb = speech_band(voice), speech_band(bus)
    depths, rows = [], []
    k = 0
    for (a, b, ps) in ivs:
        ds = []
        for p in ps:
            i0, i1 = int(p["start"] * SR), int(p["end"] * SR)
            vdb = rms_db(vb[i0:i1])
            mdb = movavg_max_db(mb[max(0, i0 - int(PRE * SR)):i1] ** 2, SR, SR // 50)
            m = margin_db
            if margins:
                m = margins.get(k, margins.get(p["block"], m))
                if isinstance(m, (list, tuple)):
                    m = m[min(p["index"], len(m) - 1)]
            d = max(min(base_db, (vdb - m) - mdb), -30.0)
            ds.append(d)
            rows.append({"phrase": k, "block": p["block"], "start": round(p["start"], 2),
                         "voice_db": round(vdb, 1), "bus_db": round(mdb, 1), "margin": m, "duck_db": round(d, 1)})
            k += 1
        depths.append(ds)
    return depths, rows


# ============================================================================ analysis
def ffmpeg_loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
                        "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    txt = r.stderr
    out = {}
    tail = txt[txt.rfind("Summary:"):]
    for key, tag in (("I", "I:"), ("LRA", "LRA:"), ("TP", "Peak:")):
        i = tail.find(tag)
        if i >= 0:
            try:
                out[key] = float(tail[i + len(tag):].split()[0])
            except ValueError:
                pass
    return out


def encode_aac(wav, out, kbps, max_tp=-1.2):
    """AAC-LC encode with ffmpeg; low-bitrate AAC adds ~1-3 dB of overshoot on transients, so the
    decoded true peak is measured and the gain stepped down until it is <= max_tp."""
    for gain_db in (0.0, -.15, -.3, -.45, -.6, -.8, -1.0, -1.3, -1.6, -2.0):
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", wav, "-af",
                        "volume=%.2fdB" % gain_db, "-c:a", "aac", "-b:a", "%dk" % kbps, out], check=True)
        m = ffmpeg_loudness(out)
        if m.get("TP", 0.0) <= max_tp:
            break
    return {"path": out, "kbps": kbps, "gain_db": round(gain_db, 2), "I": m.get("I"), "TP": m.get("TP"),
            "bytes": os.path.getsize(out)}


def overview_png(path, mix, narr, music, sfx, T):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.signal import spectrogram
    fig, ax = plt.subplots(3, 1, figsize=(20, 11), sharex=True, gridspec_kw=dict(height_ratios=[1, 1.3, 1.2]))
    m = dsp.stereo(mix).mean(1)
    t = np.arange(len(m)) / SR
    ax[0].plot(t[::200], m[::200], lw=.3, color="k")
    ax[0].axhline(dsp.undb(-1), color="r", lw=.5)
    ax[0].axhline(-dsp.undb(-1), color="r", lw=.5)
    ax[0].set_ylim(-1, 1)
    ax[0].set_title("mix waveform (red = -1 dBFS)")
    hop = SR // 10
    for x, lab in ((narr, "narration"), (music, "music (ducked)"), (sfx, "sfx (ducked)"), (mix, "mix")):
        y = dsp.stereo(x).mean(1)
        k = len(y) // hop
        r = 10 * np.log10((y[:k * hop].reshape(k, hop) ** 2).mean(1) + 1e-12)
        r = np.convolve(r, np.ones(4) / 4, mode="same")
        ax[1].plot(np.arange(k) * hop / SR, r, lw=.8, label=lab)
    for b, bt in T["blocks"].items():
        ax[1].axvline(bt["t0"], color="gray", lw=.4)
        ax[1].text(bt["t0"], -8, b, fontsize=7)
    ax[1].set_ylim(-75, 0)
    ax[1].legend(loc="lower left", fontsize=8, ncol=4)
    ax[1].grid(alpha=.3)
    f, tt, S = spectrogram(m, SR, nperseg=4096, noverlap=2048)
    ax[2].pcolormesh(tt, f, 10 * np.log10(S + 1e-16), vmin=-120, vmax=-35, shading="auto", cmap="magma")
    ax[2].set_yscale("symlog", linthresh=200)
    ax[2].set_ylim(30, 18000)
    plt.tight_layout()
    plt.savefig(path, dpi=55)
    plt.close(fig)


def whisper_check(path, phrases):
    import soundfile as sf
    from scipy.signal import resample_poly
    from faster_whisper import WhisperModel
    import re
    x, sr = sf.read(path, always_2d=True)
    x = resample_poly(x.mean(1), 1, 3).astype(np.float32)   # 48k -> 16k
    model = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=2)
    segs, _ = model.transcribe(x, beam_size=5, language="en")
    hyp = " ".join(s.text for s in segs)
    ref = " ".join(p["text"] for p in phrases)

    def words(s):
        return re.sub(r"[^a-z' ]", " ", s.lower().replace("’", "'")).split()
    r, h = words(ref), words(hyp)
    # word error rate (Levenshtein)
    d = np.arange(len(h) + 1)
    for i in range(1, len(r) + 1):
        prev = d.copy()
        d[0] = i
        for j in range(1, len(h) + 1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (r[i - 1] != h[j - 1]))
    return {"wer": round(float(d[-1]) / max(1, len(r)), 4), "ref_words": len(r), "hyp": hyp}


# ============================================================================ main
def fit(x, n):
    x = dsp.stereo(x).astype(np.float32)
    return x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x), 2), np.float32)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whisper", action="store_true", help="transcribe the mix and report WER (slow)")
    ap.add_argument("--no-analysis", action="store_true")
    a = ap.parse_args()
    T = dsp.load_timing()
    ph = json.load(open(os.path.join(OUT, "phrases.json")))
    phrases = ph["phrases"]
    narr_raw = dsp.read(os.path.join(OUT, "narration.wav"), "float64")
    n = len(narr_raw)                                   # the narration defines the timeline length
    narr, nstats = process_narration(narr_raw)
    del narr_raw
    narr = fit(narr, n)
    L_voice = dsp.loudness(narr)

    def short_term_max(x, win=3.0):
        y = speech_band(x)
        return movavg_max_db(y ** 2, int(win * SR), SR // 10)

    # ---- bus levels (before ducking)
    music = fit(dsp.read(os.path.join(OUT, "music.wav")), n)
    music = dsp.hp(music, 30, order=2).astype(np.float32)
    music, _ = leveler(music)
    vb_st = short_term_max(narr)
    g_music = dsp.undb(vb_st + MUSIC_PEAK_OVER_VOICE - short_term_max(music))
    music *= np.float32(g_music)
    sfx_st = {k: fit(dsp.read(os.path.join(OUT, "stems", "sfx_%s.wav" % k)), n) for k in ("amb", "fx", "trans")}
    g_sfx = dsp.undb(L_voice - AMB_BELOW_VOICE - dsp.loudness(sfx_st["amb"]))

    # ---- ducking (phrase driven, guaranteed margins)
    ivs = intervals(phrases)
    mmar = dict(MUSIC_MARGIN_BLOCK)
    mmar[len(phrases) - 1] = LAST_PHRASE_MARGIN_DB
    m_depth, m_rows = plan_ducks(narr, music, ivs, MUSIC_DUCK_DB, MUSIC_MARGIN_DB, mmar)
    gm = duck_curve(n, ivs, m_depth)
    # extra speech-band carve on the music while the voice speaks (dynamic EQ via crossfade)
    w = np.clip(gm / MUSIC_DUCK_DB, 0, 1).astype(np.float32)
    gmu = dsp.undb(gm).astype(np.float32)
    for c in range(2):
        carve = dsp.filt(music[:, c], "peak", 2600, q=.8, gain_db=-4.0).astype(np.float32)
        music[:, c] = (music[:, c] * (1 - w) + carve * w) * gmu
    del carve, w, gmu
    music_d = music
    sfx_d = np.zeros_like(music)
    s_rows = {}
    for k, x in sfx_st.items():
        x = dsp.hp(x, 38, order=2).astype(np.float32) * np.float32(g_sfx)   # no sub rumble below 38 Hz
        base, margin = SFX_DUCK[k]
        d, s_rows[k] = plan_ducks(narr, x, ivs, base, margin)
        sfx_d += x * dsp.undb(duck_curve(n, ivs, d)).astype(np.float32)[:, None]
    del sfx_st

    # ---- master: loudness to target, true-peak limiting (iterate for the limiter's loss)
    pre = narr + music_d + sfx_d
    pre = dsp.filt(pre, "lp", MASTER_LP_HZ, order=2).astype(np.float32)
    gain = TARGET_LUFS - dsp.loudness(pre)
    for _ in range(4):
        y, glim = dsp.limiter(pre * np.float32(dsp.undb(gain)), CEILING_DB)
        L = dsp.loudness(y)
        if abs(L - TARGET_LUFS) < .1:
            break
        gain += TARGET_LUFS - L
    del pre
    mix = y
    os.makedirs(os.path.join(OUT, "stems"), exist_ok=True)
    gl = np.float32(dsp.undb(gain))
    dsp.write(os.path.join(OUT, "mix.wav"), mix, "PCM_24")
    for k, x in (("narration", narr), ("music", music_d), ("sfx", sfx_d)):
        dsp.write(os.path.join(OUT, "stems", "mix_%s.wav" % k), x * gl)

    rep = {"target_lufs": TARGET_LUFS, "integrated_lufs_pyln": round(dsp.loudness(mix), 2),
           "true_peak_dbtp_4x": round(dsp.true_peak_db(mix), 2),
           "limiter_max_gr_db": round(float(-dsp.db(glim.min())), 2),
           "master_gain_db": round(gain, 2), "music_bus_gain_db": round(float(dsp.db(g_music)), 2),
           "sfx_bus_gain_db": round(float(dsp.db(g_sfx)), 2), "narration": nstats,
           "music_ducks": m_rows, "sfx_ducks": s_rows}
    if not a.no_analysis:
        rep["ffmpeg_ebur128"] = ffmpeg_loudness(os.path.join(OUT, "mix.wav"))
        # silence / clipping checks
        m = dsp.stereo(mix).mean(1)
        hop = int(.4 * SR)
        k = len(m) // hop
        st = 10 * np.log10((m[:k * hop].reshape(k, hop) ** 2).mean(1) + 1e-20)
        rep["min_400ms_rms_dbfs"] = round(float(st.min()), 1)
        rep["first_second_rms_dbfs"] = round(float(rms_db(m[:SR])), 1)
        rep["samples_over_-1dBFS"] = int(np.sum(np.abs(mix) > dsp.undb(-1.0)))
        # voice vs (music+sfx) in the speech band, per phrase, after the mix
        vb, bb = speech_band(narr), speech_band(music_d + sfx_d)
        margins = []
        for p in phrases:
            i0, i1 = int(p["start"] * SR), int(p["end"] * SR)
            margins.append(round(rms_db(vb[i0:i1]) - rms_db(bb[i0:i1]), 1))
        rep["phrase_voice_over_bed_db"] = {"min": min(margins), "median": float(np.median(margins)),
                                           "per_phrase": margins}
        dev = dsp.DEV
        os.makedirs(dev, exist_ok=True)
        overview_png(os.path.join(dev, "mix_overview.png"), mix, narr * gl, music_d * gl, sfx_d * gl, T)
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", os.path.join(OUT, "mix.wav"),
                        "-t", "90", "-c:a", "libmp3lame", "-b:a", "192k", os.path.join(dev, "excerpt.mp3")], check=True)
        rep["aac"] = encode_aac(os.path.join(OUT, "mix.wav"), os.path.join(OUT, "mix.m4a"), AAC_KBPS)
        if a.whisper:
            rep["whisper"] = whisper_check(os.path.join(OUT, "mix.wav"), phrases)
    json.dump(rep, open(os.path.join(OUT, "mix_report.json"), "w"), indent=1)
    short = {k: v for k, v in rep.items() if k not in ("music_ducks", "sfx_ducks")}
    if "phrase_voice_over_bed_db" in short:
        short["phrase_voice_over_bed_db"] = {k: v for k, v in short["phrase_voice_over_bed_db"].items() if k != "per_phrase"}
    if "whisper" in short:
        short["whisper"] = {k: v for k, v in short["whisper"].items() if k != "hyp"}
    print(json.dumps(short, indent=1))


if __name__ == "__main__":
    main()
