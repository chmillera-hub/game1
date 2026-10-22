#!/usr/bin/env python3
"""THE STONE AND THE BREAD -- the re-recording mix (SPEC section 5).

    python3 film/audio/mix.py                       # -> film/build/audio/mix.wav + 4 stems + mix_report.json
    python3 film/audio/mix.py --placeholder-foley   # scenes whose module is missing get beat-sheet foley
    python3 film/audio/mix_check.py                 # objective verification (LUFS, TP, DBR, PNGs, clicks)

OUTPUT  film/build/audio/mix.wav  48 kHz stereo 24-bit, EXACTLY the film's length (sum over scenes of
        round(duration * 24) frames, 2000 samples per frame -- the same frames render.py renders), and the stems
        stem_dialogue.wav, stem_music.wav, stem_sfx.wav, stem_amb.wav.  Every stem passes through the SAME
        master gain curve (loudness gain x bus compressor x true-peak limiter), so the four stems sum to the
        mix (to 24-bit rounding).

DIALOGUE  each film/assets/dialogue/<id>.wav (-20 LUFS) is placed at its scene's frame-exact start + the
          line's local start (sample-exact).  Per line: high-pass (4th order) at 65 Hz (50 Hz for the troll),
          the cast-note EQ (dragon -2 dB shelf > 5 kHz; gnome -2 dB > 3.5 kHz; troll +1.5 dB low shelf and
          +2 dB presence for the din; lioness +1.5 dB presence), a gentle split-band de-esser, a soft
          compressor + look-ahead peak limiter (speech crest factor tamed so the film can sit at -16 LUFS
          without the master limiter touching voices), a level per speaker, and a touch of the scene's room.
            fx "phone"   -> the speaking stone: 300-3400 Hz band-pass, a little grit, a 1.7 kHz presence
                            peak and a faint magical shimmer (an airy, tremolo'd high-passed tail).
            fx "vo"      -> intimate: proximity warmth, a gentle 2:1 squeeze, a small warm room.
            fx "drowned" -> not protected: no ducking key; after beat s4_swell the line sinks 6 dB as the
                            tavern swells over it (buried by design).
            s6_laugh     -> 3-4 dB under his dialogue level (cast note), and it does not duck the score.
MUSIC     prologue_mix.wav at S0 start; reprise_mix.wav at S9 start + beat s9_song; music.hold_music (S3),
          music.tavern_band (S4), music.score (S6-S9).
SFX       every film/scenes/s*_*.py that exists is imported and its SFX_CUES [(local_t, kind, params)] are
          rendered with sfx.render_cue at scene start + t (unknown kinds -> nearest kind, warned; modules that
          are missing are skipped quietly, or get beat-sheet placeholder cues with --placeholder-foley).
          Each scene's foley also feeds that scene's room (sfx.SCENE_SPACE).
AMBIENCE  sfx.ambience(scene) beds, rendered with 0.5 s margins and joined with short equal-power crossfades at
          the hard cuts (0.25 s); fades follow the picture where it fades (S0 -> S1 through black, S8 -> S9).
          The cuts that are hard FOR EFFECT live inside the beds: S5's silence at s5_silence and the tavern's
          door (outside/inside/outside perspective) in S4.
DUCKING   a sidechain keyed from the processed dialogue (minus the drowned line; minus the laugh for the
          music) with look-ahead, hold, smooth attack/release: music -10 dB (score under the voice-over -9 dB,
          the tavern under the troll -12 dB), ambience -9 dB (tavern -12 dB).
MASTER    loudness gain to -16 LUFS integrated, a gentle stereo-linked compressor (1.5:1 above -14 dBFS RMS,
          30 ms / 300 ms), a 4x-oversampled true-peak look-ahead limiter at -1.3 dBTP (verified <= -1 dBTP),
          iterated until the integrated loudness is within 0.15 LU of the target.  Fade-out with the picture
          over beat s9_fadeout.  Deterministic: fixed seeds everywhere.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib
import json
import math
import os
import sys
import time

import numpy as np
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import fftconvolve, lfilter, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
ROOT = os.path.dirname(FILM)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from film.audio import music as MU  # noqa: E402
from film.audio import sfx as FX  # noqa: E402
from film.audio import song as SONG  # noqa: E402
from film.audio.sfx import SR, bp, hp, lp, ns, peq, shelf, stereo, tvec  # noqa: E402
from film.lib import timeline as TL  # noqa: E402

FPS = 24
SPF = SR // FPS                     # 2000 samples per video frame
OUT_DIR = os.path.join(FILM, "build", "audio")
SONG_DIR = os.path.join(FILM, "assets", "song")
PRE, POST = 0.5, 0.5                # ambience / music margins around each scene (s)
TARGET_LUFS = -16.0
TP_CEIL_DB = -1.3

# ---- levels (dB, pre-master) ---------------------------------------------------------------------------
DLG_GAIN = {"MAN": 2.0, "OLD_WOMAN": 2.0, "PHARMACIST": 2.0, "PHONE": 3.5, "BOUNCER": 5.0, "CROWD": 1.5}
VO_GAIN = 3.0
LAUGH_REL_DB = -4.0
AMB_TARGET = {0: -42.0, 1: -31.0, 2: -41.0, 3: -27.5, 4: -25.0, 5: -24.0, 6: -39.0, 7: -37.5, 8: -38.0, 9: -68.0}
ROOM_SEND = {0: 0.0, 1: 0.22, 2: 0.10, 3: 0.07, 4: 0.12, 5: 0.16, 6: 0.06, 7: 0.06, 8: 0.0, 9: 0.0}
SFX_SEND = {0: 0.3, 1: 0.55, 2: 0.3, 3: 0.35, 4: 0.35, 5: 0.45, 6: 0.25, 7: 0.25, 8: 0.25, 9: 0.2}
MODULE_GAIN_OFFSET_DB = 5.0         # scene modules write gain as a linear 0..1 (1 = loud): 0.55 ~ our reference
DLG_PLR_DB = 13.5                   # per-line peak-to-loudness ceiling after compression (true-peak limiter)
SONG_PLR_DB = 13.0                  # the song stems' glue: gentle compression + limiter to this PLR
SONG_GAIN_DB = {"prologue": -1.5, "reprise": -3.0}
HOLD_LUFS = -26.0                   # the music box at his ear (active region)
BAND_LUFS = -20.0                   # tavern band inside, 'normal' bars
DUCK_MUSIC_DB = 10.0
DUCK_AMB_DB = 9.0
DUCK_SCORE_VO_DB = 9.0
DUCK_TAVERN_DB = 12.0
DUCK_PHONE_AMB_DB = 12.0
DUCK_SFX_DB = 6.0                   # foley rides 6 dB under lines (a mixer's fader, not a pump)
CROWD_KINDS = ("laugh_crowd_burst",)  # crowd-like cues duck with the crowd bed (ambience depth), not as foley
SILENCE_RIDE = (-18.0, 1.6, -7.0)   # S5: foley/amb at -18 dB for 1.6 s after s5_silence, back to -7 dB by s5_lower end
SCORE_LUFS = -27.0                  # score 'bloom' section (S8 under the voice-over, pre-duck)

_LOG = []


def log(msg, quiet=False):
    _LOG.append(msg)
    if not quiet:
        print(msg, flush=True)


# ================================================================================================
# timing
# ================================================================================================
def scene_table():
    """Frame-exact scene placement: [{id, frames, s0 (sample), n (samples), dur, start (s)}], total samples."""
    out, acc = [], 0
    for sc in TL.scenes():
        nfr = int(round(sc.duration * FPS))
        out.append(dict(id=sc.id, name=sc.name, frames=nfr, s0=acc * SPF, n=nfr * SPF, dur=sc.duration,
                        start=acc / FPS))
        acc += nfr
    return out, acc * SPF


def scene_files():
    out = {}
    for p in sorted(glob.glob(os.path.join(FILM, "scenes", "s[0-9]*_*.py"))):
        stem = os.path.splitext(os.path.basename(p))[0]
        num = ""
        for ch in stem[1:]:
            if not ch.isdigit():
                break
            num += ch
        if num:
            out.setdefault(int(num), p)
    return out


# ================================================================================================
# SFX cues
# ================================================================================================
def _norm_cue(c, dur):
    """(t, kind[, params]) | {"t"/"time", "kind"/"type", ...} -> (t, kind, params) or None."""
    try:
        if isinstance(c, dict):
            t = float(c.get("t", c.get("time", c.get("at"))))
            kind = c.get("kind", c.get("type", c.get("sfx")))
            params = {k: v for k, v in c.items() if k not in ("t", "time", "at", "kind", "type", "sfx")}
        else:
            c = list(c)
            t, kind = float(c[0]), c[1]
            params = c[2] if len(c) > 2 else {}
            if len(c) > 3 and isinstance(params, dict):
                params = dict(params, extra=c[3:])
    except (TypeError, ValueError, IndexError, KeyError):
        return None
    if kind is None or not math.isfinite(t):
        return None
    if t < -0.25 or t > dur + 0.25:
        FX.warn(f"SFX cue at t={t:.2f}s is outside the scene (0..{dur:.2f}); skipped")
        return None
    return (max(0.0, t), str(kind), params)


def placeholder_cues(s):
    """Beat-sheet foley for scenes whose module does not exist yet (only with --placeholder-foley)."""
    def bt(bid, d=None):
        return TL.beat(bid).t if TL.has_beat(bid) else d

    def be(bid, d=None):
        b = TL.beat(bid) if TL.has_beat(bid) else None
        return d if b is None or b.end is None else b.end

    def ln(lid):
        return TL.line(lid) if TL.has_line(lid) else None
    c = []
    if s == 0:
        c += [(bt("s0_bookopen", 2.86), "book_open", {"gain_db": -2}),
              (bt("s0_page_turn_v2", 17.6), "page_turn", {"heavy": True, "gain_db": -3})]
        try:
            st = json.load(open(os.path.join(SONG_DIR, "song_timing.json")))
            bread = st["prologue"]["lines"][-1]["words"][-1]["start"]
        except Exception:
            bread = 39.0
        c += [(bread + 0.2, "page_turn", {"heavy": True, "gain_db": -3})]
        c += [(t, "candle_flicker", {}) for t in (1.2, 9.5, 24.0, 33.5)]
    elif s == 1:
        c += [(bt("s1_glance", 5.5), "cloth_rustle", {"dur": 0.4, "gain_db": -6}),
              (bt("s1_lean", 7.0), "creak_wood", {"material": "stool", "dur": 0.6}),
              (bt("s1_lean", 7.0) + 0.1, "cloth_rustle", {"weight": 0.8}),
              (bt("s1_tap", 8.3) + 0.5, "tap_wood", {"count": 2, "interval": 0.24}),
              (bt("s1_hold", 21.0) + 0.7, "sigh", {"who": "dragon"}),
              (bt("s1_hold", 21.0) + 1.0, "smoke_puff", {})]
    elif s == 2:
        c += [(bt("s2_slide", 1.5), "paper_slide", {})]
        mats = ("glass", "jar", "candle", "book")
        for k, mat in enumerate(mats, start=1):
            t = bt(f"s2_item{k}", 7.0 + 2 * k)
            c += [(t - 1.1, "footstep", {"surface": "wood", "weight": 0.3, "gain_db": -5}),
                  (t - 0.6, "glass_clink", {"material": "glass", "gain_db": -9, "pan": 0.4}),
                  (t, "item_set_down", {"material": mat})]
        c += [(bt("s2_ring", 23.5), "till_bell", {}), (bt("s2_ring", 23.5) + 0.55, "receipt", {})]
    elif s == 3:
        t = 0.35
        k = 0
        while t < 13.6:
            c.append((t, "footstep_wet", {"weight": 0.75, "who": "dragon", "pan": -0.05 + 0.1 * (k % 2)}))
            t += 0.6 if t < 9.5 else 0.82
            k += 1
        c += [(5.1, "splash", {"gain_db": -8}), (0.6, "rune_glow", {"gain_db": -6, "dur": 0.9})]
        h = bt("s3_hold", 10.0)
        c += [(h + 1.4, "hourglass_flip", {"gain_db": -4}), (h + 4.4, "hourglass_flip", {"gain_db": -5}),
              (h + 7.4, "hourglass_flip", {"gain_db": -6})]
    elif s == 4:
        c += [(t, "footstep", {"surface": "stone", "weight": 0.75, "who": "dragon"}) for t in (0.3, 0.9, 1.5, 2.1)]
        c += [(bt("s4_stamp", 3.0), "stamp_thunk", {})]
        ti = bt("s4_inside", 6.3)
        c += [(ti + 0.15, "laugh_crowd_burst", {}), (ti + 0.95, "glass_clink", {"material": "pewter", "gain_db": 2}),
              (ti + 1.7, "laugh_crowd_burst", {"gain_db": -1}), (ti + 3.2, "laugh_crowd_burst", {"gain_db": -2})]
        te = bt("s4_exit", 20.0)
        c += [(te + 0.3 + 0.62 * k, "footstep", {"surface": "wood", "weight": 0.75, "gain_db": -3}) for k in range(4)]
        c += [(te + 2.6, "door_close", {})]
    elif s == 5:
        c += [(t, "thud_shove", {"dist": 0.35, "gain_db": -2}) for t in (0.8, 2.2, 3.6, 4.9, 6.2, 7.4)]
        c += [(bt("s5_hug", 9.6), "hug_rustle", {"dist": 0.3})]
        lo = bt("s5_lower", 10.8)
        c += [(lo + 0.1, "crystal_chime", {"dir": "down", "gain_db": -2}), (lo + 0.8, "crystal_chime", {"dir": "down"}),
              (lo + 1.6, "crystal_chime", {"dir": "down", "gain_db": -3})]
        c += [(t, "footstep", {"dist": 0.6, "weight": 0.4, "gain_db": -4}) for t in (19.6, 20.1, 20.5, 21.0, 21.6)]
    elif s == 6:
        c += [(t, "footstep", {"surface": "gravel", "weight": 0.75, "who": "dragon"}) for t in (0.25, 0.8, 1.35)]
        sit = bt("s6_sit", 1.5)
        c += [(sit + 0.7, "bench_creak", {"weight": 0.9}), (sit + 0.6, "cloth_rustle", {"weight": 0.8})]
        c += [(0.45, "crumbs", {"gain_db": 2}), (3.4, "crumbs", {"gain_db": 2})]
        c += [(5.0, "pigeon_coo", {}), (6.9, "pigeon_coo", {"gain_db": -2})]
        bk = bt("s6_book", 9.0)
        c += [(bk, "cloth_rustle", {"dur": 0.5}), (bk + 0.8, "page_turn", {}), (bk + 1.4, "page_turn", {}),
              (bk + 2.0, "page_turn", {}), (be("s6_book", 12.0), "item_set_down", {"material": "book", "gain_db": -4})]
        lg = bt("s6_laugh", 27.19)
        c += [(lg + 0.25, "ember_crackle", {}), (lg + 0.35, "wing_flutter", {"size": "dragon", "count": 2, "gain_db": -6})]
    elif s == 7:
        c += [(bt("s7_tear", 0.8), "bread_tear", {}), (bt("s7_hand", 1.8), "cloth_rustle", {"dur": 0.4})]
        c += [(3.0, "crumbs", {"gain_db": 2}), (3.4, "pigeon_flap", {"dir": "land", "count": 2}),
              (4.6, "crumbs", {"gain_db": 2}), (5.3, "pigeon_flap", {"dir": "land", "count": 3, "gain_db": -2}),
              (4.0, "pigeon_coo", {}), (6.0, "pigeon_coo", {"gain_db": -2})]
        c += [(bt("s7_offer", 8.0), "bread_tear", {"gain_db": -2})]
        c += [(t, "footstep", {"surface": "gravel", "weight": 0.3, "gain_db": -4}) for t in (6.2, 6.8, 7.4, 9.2)]
        c += [(bt("s7_teensit", 9.8) + 0.3, "bench_creak", {"weight": 0.4})]
        c += [(bt("s7_driver", 11.5), "wing_flutter", {"size": "bird", "count": 3, "gain_db": -4}),
              (bt("s7_driver", 11.5) + 0.45, "bench_creak", {"weight": 0.7})]
        c += [(bt("s7_worker", 13.5) + 0.4, "bench_creak", {"weight": 0.8})]
        d0, d1 = bt("s7_drag", 15.5), be("s7_drag", 18.0)
        c += [(d0, "bench_scrape", {"dur": d1 - d0})]
        l3 = ln("s7_l3")
        if l3:
            c += [(l3.start + 1.0, "bread_tear", {"gain_db": -8})]
    elif s == 8:
        c += [(6.0, "candle_flicker", {"gain_db": -4})]
    return c


def collect_cues(scenes, placeholder=False, quiet=False):
    files = scene_files()
    out = {}
    for sc in scenes:
        s = sc["id"]
        path = files.get(s)
        cues, source, from_module = None, "missing module (skipped)", False
        if path:
            name = os.path.basename(path)
            try:
                mod = importlib.import_module(f"film.scenes.{os.path.splitext(name)[0]}")
                if hasattr(mod, "SFX_CUES"):
                    cues = list(mod.SFX_CUES or [])
                    source = f"film/scenes/{name}"
                else:
                    source = f"film/scenes/{name} (no SFX_CUES)"
            except BaseException as e:          # a scene still being written must not break the mix
                FX.warn(f"could not import {name}: {e!r}; its SFX skipped")
                source = f"film/scenes/{name} (import failed)"
        if not cues and placeholder:                  # missing module, no SFX_CUES, or an empty (unwritten) list
            cues = placeholder_cues(s)
            source = "placeholder (beat sheet)" + (f" [{source} had none]" if path else "")
            from_module = False
        else:
            from_module = cues is not None
        norm = []
        for c in cues or []:
            r = _norm_cue(c, sc["dur"])
            if r is not None:
                norm.append(r)
        out[s] = dict(source=source, cues=sorted(norm, key=lambda r: r[0]), module=from_module)
        if norm:
            log(f"  S{s}: {len(norm)} SFX cues from {source}", quiet)
    return out


# ================================================================================================
# dialogue
# ================================================================================================
def _compress(x, thresh_db, ratio, attack=0.004, release=0.07, win=0.008, knee=6.0):
    a = math.exp(-1 / (win * SR))
    lvl = 10 * np.log10(lfilter([1 - a], [1, -a], x * x) + 1e-12)
    over = lvl - thresh_db
    gr = np.where(over <= -knee / 2, 0.0, np.where(over >= knee / 2, over * (1 - 1 / ratio),
                                                    (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    ga, gr_ = math.exp(-1 / (attack * SR)), math.exp(-1 / (release * SR))
    sm = np.maximum(lfilter([1 - ga], [1, -ga], gr), lfilter([1 - gr_], [1, -gr_], gr))
    return x * 10 ** (-sm / 20)


def _peak_limit(x, ceil_db, lookahead=0.0015, release=0.04):
    """Look-ahead peak limiter (mono, 4x-oversampled detection), smooth attack over the look-ahead."""
    up = np.abs(resample_poly(x, 4, 1))
    pk = np.maximum(np.abs(x), up[: 4 * len(x)].reshape(-1, 4).max(axis=1)[: len(x)])
    need = np.minimum(1.0, 10 ** (ceil_db / 20) / np.maximum(pk, 1e-9))
    L = max(1, ns(lookahead))
    m = minimum_filter1d(need, 2 * L + 1)
    g = uniform_filter1d(m, L + 1)
    b = math.exp(-1 / (release * SR))
    g = 1 - np.maximum(lfilter([1 - b], [1, -b], 1 - g), 1 - g)
    return x * g


def stone_voice(x, seed=7):
    """fx 'phone': the enchanted speaking stone -- band-limited, a little gritty, a faint magical shimmer."""
    from scipy.signal import butter, sosfiltfilt
    y = sosfiltfilt(butter(4, [300 / (SR / 2), 3400 / (SR / 2)], "band", output="sos"), x)   # zero-phase: in sync
    pk = np.abs(y).max() + 1e-9
    y = np.tanh(1.4 * y / pk) / np.tanh(1.4) * pk
    y = peq(y, 1700, 3.0, 1.1)
    air = hp(y, 2200)
    sh = FX.reverb(air, "shimmer")[: len(y) + ns(1.2)]
    t = tvec(len(sh))
    sh *= (0.65 + 0.35 * np.sin(2 * np.pi * 5.2 * t))[:, None]          # a soft magical tremolo
    sh *= 0.1 * np.sqrt(np.mean(y * y)) / (np.sqrt(np.mean(sh * sh)) + 1e-12)
    dry = np.zeros((len(sh), 2))
    dry[: len(y)] = stereo(y, 0.0)
    return dry + sh


def vo_voice(x):
    """fx 'vo': intimate, close, a small warm room."""
    y = shelf(x, 180, 2.0, high=False)
    y = _compress(y, -26.0, 2.0, 0.008, 0.12)
    room = FX.reverb(y, "vo")[: len(y) + ns(0.8)]
    room *= 10 ** (-15.0 / 20) * np.sqrt(np.mean(y * y)) / (np.sqrt(np.mean(room * room)) + 1e-12)
    out = np.zeros((len(room), 2))
    out[: len(y)] = stereo(y, 0.0)
    return out + room


def process_line(ln, x, scene_id, beats):
    """-> (stereo dry+fx (n,2), mono room-send, key_weight for the sidechain, info)."""
    spk = ln.speaker
    x = np.concatenate([x, np.zeros(ns(0.3))])                    # room for every filter's tail (no cut-off)
    k0 = ns(0.002)
    x[:k0] *= np.linspace(0.0, 1.0, k0)                           # no step into the high-pass
    y = hp(x, 50.0 if spk == "BOUNCER" else 65.0, order=4)
    if spk == "MAN":
        y = shelf(y, 5000, -2.0, high=True)
    elif spk == "OLD_WOMAN":
        y = shelf(y, 3500, -2.0, high=True)
    elif spk == "BOUNCER":
        y = peq(shelf(y, 120, 1.5, high=False), 2500, 2.0, 1.0)
    elif spk == "PHARMACIST":
        y = peq(y, 3000, 1.5, 1.0)
    y = SONG.deess(y, SR, thresh_db=-8.0, max_cut_db=6.0)
    l0 = FX.lufs(y)
    y = _compress(y, l0 - 5.0, 2.5)                                # tame the loudest syllables
    if FX.lufs(y) > -69:
        y *= 10 ** ((l0 - FX.lufs(y)) / 20)                       # back to the source loudness (-20 LUFS)
    y = _peak_limit(y, l0 + DLG_PLR_DB)                           # speech crest factor <= DLG_PLR_DB
    g_db = DLG_GAIN.get(spk, 2.0)
    if ln.id.endswith("laugh") or "(laugh" in ln.text:
        g_db = DLG_GAIN["MAN"] + LAUGH_REL_DB
    if ln.fx == "vo" or ln.vo:
        g_db = VO_GAIN
    y *= 10 ** (g_db / 20)
    y[-ns(0.05):] *= np.linspace(1.0, 0.0, ns(0.05))
    info = dict(gain_db=round(g_db, 2), fx=ln.fx)
    send = np.zeros(0)
    if ln.fx == "phone":
        st = stone_voice(y)
    elif ln.fx == "vo" or ln.vo:
        st = vo_voice(y)
    else:
        st = stereo(y, 0.0)
        send = y * ROOM_SEND.get(scene_id, 0.0)
    if ln.fx == "drowned":                       # swallowed by the swell: sinks 6 dB after the swell hits
        sw = beats.get("s4_swell", (ln.start + 0.8, None))[0]
        t = tvec(len(st)) + ln.start
        g = 10 ** (-6.0 * np.clip((t - sw - 0.25) / 0.5, 0, 1) / 20)
        st = st * g[:, None]
        info["sinks_after"] = round(sw + 0.25, 3)
    return st, send, info


# ================================================================================================
# ducking
# ================================================================================================
def duck_gain(key, depth_db, hop=480, thresh_db=-46.0, lookahead=0.14, hold=0.65, attack=0.09, release=0.45):
    """Sidechain duck: frame RMS of `key` (mono) -> activity (look-ahead + hold) -> smooth attack/release ->
    per-sample linear gain (depth_db may be a per-sample array)."""
    n = len(key)
    nf = n // hop + 1
    kp = np.pad(key, (0, nf * hop - n))
    rms = np.sqrt(np.mean(kp.reshape(nf, hop) ** 2, axis=1) + 1e-14)
    act = (20 * np.log10(rms) > thresh_db).astype(float)
    fr = SR / hop
    la, hd = int(round(lookahead * fr)), int(round(hold * fr))
    a2 = act.copy()
    idx = np.nonzero(act)[0]
    for i in idx:                                                       # dilate: look-ahead + hold
        a2[max(0, i - la): min(nf, i + hd + 1)] = 1.0
    sm = np.zeros(nf)
    ka, kr = 1 - math.exp(-1 / (attack * fr)), 1 - math.exp(-1 / (release * fr))
    v = 0.0
    for i in range(nf):
        tgt = a2[i]
        v += (ka if tgt > v else kr) * (tgt - v)
        sm[i] = v
    smp = np.interp(np.arange(n) / hop, np.arange(nf), sm)
    depth = depth_db if np.ndim(depth_db) == 0 else depth_db[:n]
    return 10 ** (-depth * smp / 20), smp


# ================================================================================================
# master
# ================================================================================================
def tp_envelope(x, ceil_db=None, margin_db=4.0, pad=512):
    """Per-sample true-peak estimate (max |.| over channels of the 4x-oversampled signal).  With ceil_db, only
    the regions whose sample peaks come within margin_db of the ceiling are oversampled (inter-sample overs
    beyond that margin do not occur in practice); elsewhere the sample peak is returned."""
    n = len(x)
    out = np.abs(x).max(axis=1)
    if ceil_db is None:
        hot = np.ones(n, bool)
    else:
        hot = out > 10 ** ((ceil_db - margin_db) / 20)
    idx = np.nonzero(hot)[0]
    if len(idx) == 0:
        return out
    gaps = np.nonzero(np.diff(idx) > 4 * pad)[0]
    starts = np.concatenate([[idx[0]], idx[gaps + 1]])
    ends = np.concatenate([idx[gaps], [idx[-1]]])
    for a0, b0 in zip(starts, ends):
        for a in range(int(a0), int(b0) + 1, SR * 8):
            b = min(int(b0) + 1, a + SR * 8)
            lo, hi = max(0, a - pad), min(n, b + pad)
            for c in range(x.shape[1]):
                up = np.abs(resample_poly(x[lo:hi, c], 4, 1))
                pk = up[: 4 * (hi - lo)].reshape(-1, 4).max(axis=1)
                out[lo:hi] = np.maximum(out[lo:hi], pk)
    return out


def limiter_gain(x, ceil_db=TP_CEIL_DB, lookahead=0.002, release=0.06):
    pk = tp_envelope(x, ceil_db)
    need = np.minimum(1.0, 10 ** (ceil_db / 20) / np.maximum(pk, 1e-9))
    L = max(1, ns(lookahead))
    m = minimum_filter1d(need, 2 * L + 1)
    g = uniform_filter1d(m, L + 1)
    b = math.exp(-1 / (release * SR))
    return 1 - np.maximum(lfilter([1 - b], [1, -b], 1 - g), 1 - g)


def compressor_gain(x, thresh_db=-14.0, ratio=1.5, knee=8.0, attack=0.03, release=0.3, win=0.05):
    p = np.mean(x * x, axis=1)
    a = math.exp(-1 / (win * SR))
    lvl = 10 * np.log10(lfilter([1 - a], [1, -a], p) + 1e-12)
    over = lvl - thresh_db
    gr = np.where(over <= -knee / 2, 0.0, np.where(over >= knee / 2, over * (1 - 1 / ratio),
                                                    (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    ga, gr_ = math.exp(-1 / (attack * SR)), math.exp(-1 / (release * SR))
    sm = np.maximum(lfilter([1 - ga], [1, -ga], gr), lfilter([1 - gr_], [1, -gr_], gr))
    return 10 ** (-sm / 20)


def lufs_of(x):
    return FX.lufs(x)


# ================================================================================================
# build
# ================================================================================================
def _ctx(sc, walla, cues):
    s = sc["id"]
    ctx = dict(dur=sc["dur"], pre=PRE, post=POST, walla=walla,
               beats={b.id: (b.t, b.end) for b in TL.beats_in(s)},
               lines=[(l.id, l.start, l.end, l.speaker) for l in TL.lines_in(s)],
               cues=cues.get(s, {}).get("cues", []))
    if s == 4:
        dc = [t for (t, k, p) in ctx["cues"] if FX.resolve_kind(k) == "door_close"]
        ex = TL.beat("s4_exit").t if TL.has_beat("s4_exit") else 20.0
        dc = [t for t in dc if t >= ex - 1.0] or dc
        if dc:
            ctx["door_close_t"] = float(dc[-1]) + 0.05
    return ctx


def _add_local(bus, arr, s0, pre=PRE):
    """Add a scene-local array that starts `pre` seconds before the scene start into a global bus."""
    FX.place(bus, arr, s0 - ns(pre))


def _region_lufs(x, a, b):
    a, b = max(0, int(a)), min(len(x), int(b))
    if b - a < ns(0.5):
        return -70.0
    return lufs_of(x[a:b])


# ================================================================================================
# heavy layers: rendered in a process pool, cached on disk (key = audio source code + the timeline data used)
# ================================================================================================
CACHE_DIR = os.path.join(OUT_DIR, "cache")
_SRC_FILES = ("sfx.py", "music.py", "motif.py", "song.py")


def _src_hash():
    h = hashlib.sha1()
    for f in _SRC_FILES:
        with open(os.path.join(HERE, f), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:12]


def _job(kind, s, ctx):
    """Worker: render one heavy layer.  ctx is picklable (no Walla); the walla cache is re-opened here."""
    import numpy as _np
    from film.audio import music as _MU, sfx as _FX
    from film.lib import timeline as _TL
    if kind in ("amb", "band"):
        ctx = dict(ctx, walla=None if ctx.get("no_walla") else _FX.Walla(verbose=False))
        _FX.set_walla(ctx["walla"])
    if kind == "amb":
        return _np.asarray(_FX.ambience(s, ctx), _np.float32), {}
    if kind == "hold":
        y, ev = _MU.hold_music(ctx)
        return _np.asarray(y, _np.float32), {"events": [list(map(float, e)) for e in ev]}
    if kind == "band":
        y, info = _MU.tavern_band(ctx)
        return _np.asarray(y, _np.float32), info
    if kind == "score":
        info = {}
        y, ev = _MU.score(_TL, info)
        info["events"] = len(ev)
        info["first"] = float(ev[0].t) if ev else None
        return _np.asarray(y, _np.float32), info
    raise KeyError(kind)


def render_layers(jobs, workers=3, use_cache=True, quiet=False):
    """jobs: {name: (kind, scene, ctx)} -> {name: (array, info)}; cached by content hash."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    src = _src_hash()
    keys, todo, out = {}, {}, {}
    for name, (kind, s, ctx) in jobs.items():
        key = hashlib.sha1(json.dumps([src, kind, s, {k: v for k, v in ctx.items() if k != "walla"}],
                                      sort_keys=True, default=str).encode()).hexdigest()[:16]
        keys[name] = key
        npy, js = os.path.join(CACHE_DIR, f"{name}_{key}.npy"), os.path.join(CACHE_DIR, f"{name}_{key}.json")
        for old in glob.glob(os.path.join(CACHE_DIR, f"{name}_*")):          # prune stale renders of this layer
            if os.path.splitext(os.path.basename(old))[0] != f"{name}_{key}":
                os.remove(old)
        if use_cache and os.path.exists(npy) and os.path.exists(js):
            out[name] = (np.load(npy).astype(np.float64), json.load(open(js)))
        else:
            todo[name] = (kind, s, ctx)
    if todo:
        log(f"[mix] rendering {len(todo)} layer(s): {', '.join(todo)} ({workers} workers) ...", quiet)
        from concurrent.futures import ProcessPoolExecutor
        order = sorted(todo, key=lambda n: 0 if n == "score" else 1)          # longest first
        if workers > 1:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                futs = {n: ex.submit(_job, *todo[n]) for n in order}
                res = {n: f.result() for n, f in futs.items()}
        else:
            res = {n: _job(*todo[n]) for n in order}
        for name, (arr, info) in res.items():
            np.save(os.path.join(CACHE_DIR, f"{name}_{keys[name]}.npy"), arr)
            with open(os.path.join(CACHE_DIR, f"{name}_{keys[name]}.json"), "w") as fh:
                json.dump(info, fh, default=float)
            out[name] = (np.asarray(arr, np.float64), info)
    else:
        log("[mix] all heavy layers from cache", quiet)
    return out


def song_glue(x, plr=SONG_PLR_DB):
    """Gentle glue for a finished song stem: 1.6:1 above (loudness + 6 dB), then a true-peak limiter at
    loudness + plr -- the stem keeps its shape but can sit at the film's level without the master limiter."""
    l0 = lufs_of(x)
    p = np.mean(x * x, axis=1)
    a = math.exp(-1 / (0.03 * SR))
    lvl = 10 * np.log10(lfilter([1 - a], [1, -a], p) + 1e-12)
    over = np.maximum(lvl - (l0 + 6.0), 0)
    gr = over * (1 - 1 / 1.6)
    ga, gr_ = math.exp(-1 / (0.015 * SR)), math.exp(-1 / (0.25 * SR))
    sm = np.maximum(lfilter([1 - ga], [1, -ga], gr), lfilter([1 - gr_], [1, -gr_], gr))
    y = x * (10 ** (-sm / 20))[:, None]
    y *= 10 ** ((l0 - lufs_of(y)) / 20)
    return y * limiter_gain(y, l0 + plr, 0.002, 0.08)[:, None]


def bus_limit(x, ceil_db):
    """Stereo-linked true-peak look-ahead limiter for one bus; returns (limited, max gain reduction dB)."""
    if not np.any(x):
        return x, 0.0
    g = limiter_gain(x, ceil_db, 0.002, 0.08)
    return x * g[:, None], float(-20 * np.log10(g.min()))


def build(placeholder=False, quiet=False, use_walla=True, out_dir=OUT_DIR, workers=3, use_cache=True,
          cues_json=None, dump_cues=None):
    t_start = time.time()
    os.makedirs(out_dir, exist_ok=True)
    scenes, N = scene_table()
    S = {sc["id"]: sc for sc in scenes}
    log(f"[mix] {len(scenes)} scenes, {N} samples = {N / SR:.4f} s (timeline total {TL.total():.4f} s)", quiet)
    walla = FX.Walla(verbose=not quiet) if use_walla else None
    FX.set_walla(walla)
    report = dict(samples=N, seconds=N / SR, sr=SR, scenes=[{k: v for k, v in sc.items()} for sc in scenes],
                  lines=[], cues={}, warnings=[], levels={}, timing={})
    tick = [time.time()]

    def lap(name):
        now = time.time()
        report["timing"][name] = round(now - tick[0], 1)
        tick[0] = now

    # ---------------- SFX cues (scene modules) ---------------------------------------------------
    if cues_json:                                     # a frozen cue set (exact reproduction / testing)
        with open(cues_json) as fh:
            raw_c = json.load(fh)
        cues = {int(k): dict(v, cues=[tuple(c) for c in v["cues"]]) for k, v in raw_c.items()}
        log(f"[mix] SFX cues from {cues_json}", quiet)
    else:
        log("[mix] collecting SFX cues ...", quiet)
        cues = collect_cues(scenes, placeholder, quiet)
    if dump_cues:
        with open(dump_cues, "w") as fh:
            json.dump({str(k): v for k, v in cues.items()}, fh, indent=0, default=str)
    lap("cues")

    # ---------------- heavy layers (pool + cache) -----------------------------------------------
    jobs = {}
    for sc in scenes:
        c = _ctx(sc, None, cues)
        c.pop("walla", None)
        c.pop("cues", None)                       # beds depend on the timeline (+ S4's door), not on the foley
        if not use_walla:
            c["no_walla"] = True
        jobs[f"amb{sc['id']}"] = ("amb", sc["id"], c)
    c3 = {k: v for k, v in _ctx(S[3], None, cues).items() if k not in ("walla", "cues")}
    c4 = {k: v for k, v in _ctx(S[4], None, cues).items() if k not in ("walla", "cues")}
    jobs["hold"] = ("hold", 3, c3)
    jobs["band"] = ("band", 4, c4)
    jobs["score"] = ("score", None, {"total": TL.total(), "timeline": TL.path().name,
                                     "beats": {b: TL.raw()["beats"][i] for i, b in enumerate(
                                         x["id"] for x in TL.raw()["beats"]) if b.startswith(("s6", "s7", "s8", "s9"))},
                                     "lines": [l for l in TL.raw()["lines"] if l["scene"] in (7, 8)]})
    layers = render_layers(jobs, workers=workers, use_cache=use_cache, quiet=quiet)
    lap("layers")

    # ---------------- dialogue ------------------------------------------------------------------
    log("[mix] dialogue ...", quiet)
    import soundfile as sf
    dlg = np.zeros((N, 2))
    key_all = np.zeros(N)            # sidechain for the ambience
    key_mus = np.zeros(N)            # sidechain for the music (no laugh)
    sends = {}
    TAIL = ns(3.0)
    for ln in sorted((l for l in TL.raw()["lines"] if l.get("wav")), key=lambda d: d["global_start"]):
        L = TL.line(ln["id"])
        sc = S[L.scene]
        x, sr = sf.read(os.path.join(ROOT, L.wav))
        if sr != SR:
            raise SystemExit(f"{L.wav}: {sr} Hz")
        if x.ndim == 2:
            x = x.mean(axis=1)
        st, send, info = process_line(L, x, L.scene, {b.id: (b.t, b.end) for b in TL.beats_in(L.scene)})
        i0 = sc["s0"] + int(round(L.start * SR))
        FX.place(dlg, st, i0)
        if len(send):
            buf = sends.setdefault(L.scene, np.zeros(sc["n"] + TAIL))
            FX.place(buf, send, i0 - sc["s0"])
        if L.fx != "drowned":
            FX.place(key_all, x * 0.5, i0)
            if not L.id.endswith("laugh"):
                FX.place(key_mus, x * 0.5, i0)
        report["lines"].append(dict(id=L.id, speaker=L.speaker, scene=L.scene, sample=i0, t=round(i0 / SR, 4),
                                    local=L.start, dur=round(len(x) / SR, 4), **info))
    for s, buf in sends.items():
        wet = FX.reverb(buf, FX.SCENE_SPACE[s])
        FX.place(dlg, wet, S[s]["s0"])
    lap("dialogue")

    # ---------------- music ---------------------------------------------------------------------
    log("[mix] music: song stems, hold music, tavern band, score ...", quiet)
    mus = np.zeros((N, 2))
    pm, _ = sf.read(os.path.join(SONG_DIR, "prologue_mix.wav"))
    pm = song_glue(pm) * 10 ** (SONG_GAIN_DB["prologue"] / 20)
    FX.place(mus, pm, S[0]["s0"])
    rp, _ = sf.read(os.path.join(SONG_DIR, "reprise_mix.wav"))
    rp = song_glue(rp) * 10 ** (SONG_GAIN_DB["reprise"] / 20)
    t_rep = TL.beat("s9_song").t if TL.has_beat("s9_song") else 5.0
    i_rep = S[9]["s0"] + int(round(t_rep * SR))
    FX.place(mus, rp, i_rep)
    report["song"] = dict(prologue_sample=S[0]["s0"], reprise_sample=i_rep, reprise_local=t_rep,
                          prologue_lufs=round(lufs_of(pm), 2), reprise_lufs=round(lufs_of(rp), 2))
    duck_music = np.zeros((N, 2))
    # hold music (S3)
    hold, hinfo = layers["hold"]
    hold_ev = hinfo["events"]
    h0 = c3["beats"].get("s3_hold", (10.0, None))[0]
    lv = _region_lufs(hold, ns(PRE + h0), ns(PRE + S[3]["dur"]))
    hold *= 10 ** ((HOLD_LUFS - lv) / 20)
    _add_local(duck_music, hold, S[3]["s0"])
    report["hold"] = dict(t0=h0, notes=len(hold_ev), first=[(round(a, 3), round(b, 3), int(m)) for a, b, m in hold_ev[:8]])
    # tavern band (S4)
    band, binfo = layers["band"]
    ti = c4["beats"].get("s4_inside", (6.3, None))[0]
    lv = _region_lufs(band, ns(PRE + ti), ns(PRE + binfo["T0"] + 8 * binfo["bar"]))
    band *= 10 ** ((BAND_LUFS - lv) / 20)
    _add_local(duck_music, band, S[4]["s0"])
    report["tavern"] = dict(T0=binfo["T0"], bar=binfo["bar"], form=binfo["form"],
                            door_close_t=c4.get("door_close_t"))
    lap("music_cues")
    # score (S6-S9), global time
    score, sinfo = layers["score"]
    bl = [(a, b) for (nm_, a, b) in sinfo["sections"] if nm_ == "bloom"][0]
    lv = _region_lufs(score, ns(bl[0]), ns(bl[1]))
    score *= 10 ** ((SCORE_LUFS - lv) / 20)
    FX.place(duck_music, score[:N], 0)
    report["score"] = dict(events=sinfo.get("events"), first=round(sinfo["first"], 3) if sinfo.get("first") else None,
                           arc={k: v for k, v in sinfo.items() if k not in ("events", "first")},
                           laugh_global=round(S[6]["start"] + TL.beat("s6_laugh").t, 3) if TL.has_beat("s6_laugh")
                           else None)
    lap("score")

    # ---------------- ambience ------------------------------------------------------------------
    log("[mix] ambience ...", quiet)
    amb = np.zeros((N, 2))
    xf = 0.125
    for sc in scenes:
        s = sc["id"]
        a = layers[f"amb{s}"][0]
        lv = FX.lufs(a)
        a *= 10 ** ((AMB_TARGET[s] - lv) / 20) if lv > -69 else 1.0
        n = len(a)
        t = tvec(n) - PRE                                   # scene-local time of each sample
        if s == 0:
            fi = (0.0, 2.0)                                  # with the opening fade from black (s0_open)
        elif s == 1:
            fi = (-1.0, 1.0)                                 # pre-lap under the page dissolve, up with s1_fadein
        elif s == 9:
            fi = (0.0, 1.5)
        else:
            fi = (-xf, xf)
        if s == 0:
            o = TL.beat("s0_out") if TL.has_beat("s0_out") else None
            fo = (o.t, o.end) if o else (sc["dur"] - 1.2, sc["dur"])
        elif s == 8:
            fo = (TL.beat("s8_fade").t, TL.beat("s8_fade").end) if TL.has_beat("s8_fade") else (sc["dur"] - 2.5, sc["dur"])
        elif s == 9:
            fo = (sc["dur"] - 1.5, sc["dur"])
        else:
            fo = (sc["dur"] - xf, sc["dur"] + xf)
        up = np.clip((t - fi[0]) / max(fi[1] - fi[0], 1e-3), 0, 1)
        dn = np.clip((fo[1] - t) / max(fo[1] - fo[0], 1e-3), 0, 1)
        w = np.sin(0.5 * np.pi * up) * np.sin(0.5 * np.pi * dn)
        _add_local(amb, a * w[:, None], sc["s0"])
        report["levels"][f"amb_s{s}"] = round(AMB_TARGET[s], 1)
    lap("ambience")

    # ---------------- SFX -----------------------------------------------------------------------
    log("[mix] foley ...", quiet)
    sfx_bus = np.zeros((N, 2))
    sfx_crowd = np.zeros((N, 2))
    nrend = 0
    hard_out = {s_: True for s_ in S}
    hard_out[0] = hard_out[8] = hard_out[9] = False       # these scenes end in a fade: tails may ring through
    for sc in scenes:
        s = sc["id"]
        info = cues.get(s, {})
        rows = []
        local = np.zeros((sc["n"] + TAIL, 2))               # this scene's foley, dry + room
        local_c = np.zeros((sc["n"] + TAIL, 2))             # crowd-like cues (ducked like the crowd bed)
        send = np.zeros((sc["n"] + TAIL, 2))
        off = MODULE_GAIN_OFFSET_DB if info.get("module") else 0.0
        for k, (t, kind, params) in enumerate(info.get("cues", [])):
            seed = FX.seed_of("cue", s, k, kind, round(t, 3))
            y, wet = FX.render_cue(kind, params, seed, scene=s, gain_offset_db=off)
            if y is None:
                rows.append(dict(t=t, kind=kind, resolved=None))
                continue
            i0 = int(round(t * SR))
            FX.place(local_c if FX.resolve_kind(kind) in CROWD_KINDS else local, y, i0)
            FX.place(send, y * wet, i0)
            rows.append(dict(t=round(t, 3), kind=kind, resolved=FX.resolve_kind(kind), sample=sc["s0"] + i0))
            nrend += 1
        if np.any(send):
            FX.place(local, SFX_SEND[s] * FX.reverb(send, FX.SCENE_SPACE[s]), 0)
        if hard_out.get(s, True):                            # a hard picture cut cuts the foley too (60 ms)
            k = ns(0.06)
            for buf in (local, local_c):
                buf[sc["n"]: sc["n"] + k] *= np.linspace(1.0, 0.0, k)[:, None]
                buf[sc["n"] + k:] = 0.0
        FX.place(sfx_bus, local, sc["s0"])
        FX.place(sfx_crowd, local_c, sc["s0"])
        report["cues"][f"S{s}"] = dict(source=info.get("source"), cues=rows)
    log(f"[mix] {nrend} SFX cues rendered", quiet)
    lap("foley")

    # ---------------- ducking -------------------------------------------------------------------
    log("[mix] ducking ...", quiet)
    scene_of = np.zeros(N, np.int8)
    for sc in scenes:
        scene_of[sc["s0"]: sc["s0"] + sc["n"]] = sc["id"]
    depth_m = np.full(N, DUCK_MUSIC_DB)
    depth_m[scene_of == 8] = DUCK_SCORE_VO_DB
    depth_m[scene_of == 4] = DUCK_TAVERN_DB
    depth_a = np.full(N, DUCK_AMB_DB)
    depth_a[scene_of == 4] = DUCK_TAVERN_DB
    depth_a[scene_of == 3] = DUCK_PHONE_AMB_DB            # the stone is at his ear: the rain recedes
    gm, _ = duck_gain(key_mus, depth_m)
    ga, _ = duck_gain(key_all, depth_a)
    mus += duck_music * gm[:, None]
    del duck_music
    amb *= ga[:, None]
    gs, _ = duck_gain(key_all, DUCK_SFX_DB, attack=0.05, release=0.35)
    sfx_bus *= gs[:, None]
    sfx_bus += sfx_crowd * ga[:, None]
    del sfx_crowd
    if TL.has_beat("s5_silence"):                     # the silence must LAND: ride S5's foley + bed right down
        t_si = S[5]["s0"] + ns(TL.beat("s5_silence").t)
        t_lo = S[5]["s0"] + ns(TL.beat("s5_lower").end if TL.has_beat("s5_lower") and TL.beat("s5_lower").end
                               else TL.beat("s5_silence").t + 3.0)
        d0, hold_s, d1 = SILENCE_RIDE
        i1 = t_si + ns(hold_s)
        ride = np.zeros(S[5]["n"] + S[5]["s0"] - t_si)
        tt_ = np.arange(len(ride))
        ride[:] = d0
        k = max(1, t_lo - i1)
        rr = np.clip((tt_ - (i1 - t_si)) / k, 0, 1)
        ride = d0 + (d1 - d0) * rr
        end_up = np.clip((tt_ - (t_lo - t_si)) / ns(2.5), 0, 1)
        ride = ride * (1 - end_up)                       # back to 0 dB 2.5 s after the crystals are down
        g = 10 ** (ride / 20)
        g[: ns(0.004)] = np.linspace(1.0, g[ns(0.004)], ns(0.004))
        sfx_bus[t_si: t_si + len(g)] *= g[:, None]
        report["silence_ride"] = dict(start=round(t_si / SR, 3), db=d0, hold_s=hold_s, then_db=d1,
                                      until=round(t_lo / SR, 3))
    report["duck"] = dict(music_db=DUCK_MUSIC_DB, score_vo_db=DUCK_SCORE_VO_DB, tavern_db=DUCK_TAVERN_DB,
                          amb_db=DUCK_AMB_DB, s3_amb_under_stone_db=DUCK_PHONE_AMB_DB, sfx_db=DUCK_SFX_DB,
                          crowd_cues="ambience depth")
    lap("ducking")

    # ---------------- master --------------------------------------------------------------------
    log("[mix] master ...", quiet)
    buses = dict(dialogue=dlg, music=mus, sfx=sfx_bus, amb=amb)
    fo_t = TL.beat("s9_fadeout").t if TL.has_beat("s9_fadeout") else S[9]["dur"] - 1.5
    a_fo = S[9]["s0"] + ns(fo_t)
    k = N - a_fo
    if k > 0:
        ramp = np.cos(0.5 * np.pi * np.linspace(0, 1, k)) ** 2
        for b in buses.values():
            b[a_fo:] *= ramp[:, None]
    g_est = TARGET_LUFS - lufs_of(dlg + mus + sfx_bus + amb)
    bus_ceil = TP_CEIL_DB - g_est - 0.3
    report["bus_limit"] = {"ceiling_dbfs": round(bus_ceil, 2)}
    for name in ("dialogue", "music", "sfx", "amb"):
        buses[name], gr = bus_limit(buses[name], bus_ceil)
        report["bus_limit"][name + "_max_gr_db"] = round(gr, 2)
    mix = sum(buses.values())
    g0 = 10 ** ((TARGET_LUFS - lufs_of(mix)) / 20)
    for it in range(4):
        cg = compressor_gain(mix * g0)
        lg = limiter_gain(mix * (g0 * cg)[:, None])
        gain = g0 * cg * lg
        L_ = lufs_of(mix * gain[:, None])
        log(f"[mix]   pass {it + 1}: {L_:.2f} LUFS, gain {20 * math.log10(g0):+.2f} dB, comp max "
            f"{-20 * np.log10(cg.min()):.1f} dB, limiter max {-20 * np.log10(lg.min()):.1f} dB", quiet)
        if abs(L_ - TARGET_LUFS) < 0.15:
            break
        g0 *= 10 ** ((TARGET_LUFS - L_) / 20)
    for name in buses:
        buses[name] = buses[name] * gain[:, None]
    out = buses["dialogue"] + buses["music"] + buses["sfx"] + buses["amb"]
    tp = 20 * np.log10(tp_envelope(out, 20 * np.log10(np.abs(out).max() + 1e-12)).max() + 1e-12)
    report["master"] = dict(lufs=round(lufs_of(out), 2), true_peak_dbtp=round(float(tp), 2),
                            gain_db=round(20 * math.log10(g0), 2),
                            comp_max_db=round(float(-20 * math.log10(cg.min())), 2),
                            limiter_max_db=round(float(-20 * math.log10(lg.min())), 2),
                            limiter_active_pct=round(float(np.mean(lg < 0.989) * 100), 3))
    log(f"[mix] master: {report['master']}", quiet)
    lap("master")

    # ---------------- write -------------------------------------------------------------------
    def w(path, x):
        sf.write(path, np.clip(x, -1.0, 1.0).astype(np.float32), SR, subtype="PCM_24")
    w(os.path.join(out_dir, "mix.wav"), out)
    for name, b in buses.items():
        w(os.path.join(out_dir, f"stem_{name}.wav"), b)
        report["levels"][f"stem_{name}_lufs"] = round(lufs_of(b), 2) if np.any(b) else None
    report["warnings"] = sorted(FX._WARNED)
    report["log"] = _LOG
    lap("write")
    report["runtime_s"] = round(time.time() - t_start, 1)
    with open(os.path.join(out_dir, "mix_report.json"), "w") as fh:
        json.dump(report, fh, indent=1, default=float)
    log(f"[mix] wrote {out_dir}/mix.wav + stems ({N / SR:.3f} s) in {time.time() - t_start:.0f} s "
        f"{report['timing']}", quiet)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="build the film's soundtrack mix")
    ap.add_argument("--placeholder-foley", action="store_true",
                    help="render beat-sheet foley for scenes whose module (or SFX_CUES) does not exist yet")
    ap.add_argument("--no-walla", action="store_true", help="skip the Piper crowd walla (procedural babble only)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--workers", type=int, default=3, help="processes for the heavy layers (default 3)")
    ap.add_argument("--no-cache", action="store_true", help="re-render every layer (ignore build/audio/cache)")
    ap.add_argument("--dump-cues", metavar="JSON", help="write the SFX cue set used to JSON")
    ap.add_argument("--cues-json", metavar="JSON", help="use a frozen SFX cue set instead of the scene modules")
    a = ap.parse_args(argv)
    build(placeholder=a.placeholder_foley, quiet=a.quiet, use_walla=not a.no_walla, workers=max(1, a.workers),
          use_cache=not a.no_cache, cues_json=a.cues_json, dump_cues=a.dump_cues)


if __name__ == "__main__":
    main()
