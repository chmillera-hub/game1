#!/usr/bin/env python3
"""Final re-recording mix -> out/mix.wav (44.1 kHz stereo, ≈ -14 LUFS integrated, true peak ≤ -1.5 dBTP).

    python3 audio/mix.py [--timeline data/timeline.json] [--events data/sfx_events.json] [--out out/mix.wav]
                         [--stems out/stems] [--no-music] [--no-sfx] [--lufs -14] [--tp -1.5]

Inputs (all optional except the timeline — anything missing is silence, so the mix runs before TTS exists):
  data/timeline.json        beats with `audio` (dialogue lines: audio/wav/*.wav, vocals: audio/vocals/*.wav)
  data/sfx_events.json      from tools/collect_sfx.py (re-collected in-process if missing)
  out/stems/music_bed.wav + out/stems/music_features.wav  from audio/music.py (else out/music.wav as bed)
  audio/sfx/*.wav, audio/sfx/meta.json, ambience beds amb_edge / amb_backroom

Voices (character-appropriate processing):
  NARRATOR  dry-warm, centred: gentle low-cut, +warmth, a little presence, light compression, a hint of small room.
  JESUS/USER (THE_EDGE, outdoors at dusk): light, short, airy early-reflection room; small pans (Jesus a touch left,
            the user a touch right).
  FEAR / MAGICIAN (MIND_BACKROOM): the back room's warmer, longer reverb. MAGICIAN slightly creepy: a subtle
            detuned double (slow chorus), a darker, longer reverb tail, a touch right/behind.
  VOID vocals (laughs, huffs, giggles, hums...): huge and cosmic — a subtle octave-down layer, wide, plus a long
            'vast' reverb with a faint octave-up shimmer in its feed.
  Whispers (any speaker): close and intimate — dry, a little air, centred (the Void's keep a faint cosmic tail).
Music: the score's bed is side-chain ducked under all speech (smooth: 0.15 s look-ahead attack, 0.55 s hold that
  bridges the breaths between phrases, 0.9 s release); the word-painting accents and comic hits (features stem) duck only lightly so they're felt
  on the words. SFX: placed at t - sync with gain/pan, a touch of location room. Ambience per location,
  crossfaded at location changes. Master: loudness-normalised + true-peak limited (4x oversampled look-ahead).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audiolib as A  # noqa: E402

SR = A.SR

# per-clip loudness targets (LUFS) before bus processing; vocals sit under the lines
LINE_LUFS = {"NARRATOR": -20.0, "JESUS": -20.0, "USER": -19.5, "FEAR": -20.0, "MAGICIAN": -20.0}
VOCAL_LUFS = {"whisper": -27.0, "laugh_maniacal": -21.0, "laugh_soft": -24.0, "giggle": -24.0, "snort": -25.0,
              "huff": -23.5, "sigh": -25.0, "hum": -25.0, "cough": -25.0, "gasp": -24.0, "scream_short": -21.0,
              "mmhm": -24.5, "whimper": -25.0, "gulp": -26.0}
PAN = {"NARRATOR": 0.0, "JESUS": -0.1, "USER": 0.12, "FEAR": -0.08, "MAGICIAN": 0.18, "VOID": 0.0}
MUSIC_BED_DB = -9.0        # score bed relative to its -18 LUFS file (before ducking)
MUSIC_FEAT_DB = -14.0      # word-painting accents + comic hits
DUCK_DB = -7.5             # bed under speech
FEAT_DUCK_DB = -2.0
SFX_DB = 0.0
SFX_DUCK_DB = -4.0         # SFX under speech (dialogue priority)
AMB_DB = {"THE_EDGE": -4.0, "MIND_BACKROOM": -3.0}
AMB_FILE = {"THE_EDGE": "amb_edge.wav", "MIND_BACKROOM": "amb_backroom.wav"}


def rp(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def ffmpeg(x, af):
    with tempfile.TemporaryDirectory() as td:
        i, o = os.path.join(td, "i.wav"), os.path.join(td, "o.wav")
        import soundfile as sf
        sf.write(i, x, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", i, "-af", af, "-ar", str(SR), o], check=True)
        y, _ = sf.read(o, dtype="float32", always_2d=True)
    return y


def octave_down(x):
    """Pitch down one octave, same duration (rubberband if available, else asetrate+atempo)."""
    m = A.to_mono(x)
    try:
        y = ffmpeg(m, "rubberband=pitch=0.5:formant=preserved")
    except Exception:  # noqa: BLE001
        y = ffmpeg(m, f"asetrate={SR // 2},aresample={SR},atempo=2.0")
    y = A.to_mono(y)[: len(m)]
    return np.concatenate([y, np.zeros(max(0, len(m) - len(y)), np.float32)])


def octave_up(x):
    m = A.to_mono(x)
    try:
        y = ffmpeg(m, "rubberband=pitch=2.0")
    except Exception:  # noqa: BLE001
        y = ffmpeg(m, f"asetrate={SR * 2},aresample={SR},atempo=0.5")
    y = A.to_mono(y)[: len(m)]
    return np.concatenate([y, np.zeros(max(0, len(m) - len(y)), np.float32)])


def chorus(x, depth_ms=6.0, rate=0.25, mix=0.35):
    """Slow detuned double (time-varying delay), mono-compatible: L and R get opposite modulation."""
    m = A.to_mono(x).astype(np.float64)
    n = len(m)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for c, ph in enumerate((0.0, np.pi)):
        d = (12.0 + depth_ms * (0.5 + 0.5 * np.sin(2 * np.pi * rate * t + ph))) * SR / 1000
        idx = np.clip(np.arange(n) - d, 0, n - 1)
        out[:, c] = m * (1 - mix) + np.interp(idx, np.arange(n), m) * mix
    return out.astype(np.float32)


def clip_gain(x, target, lo=-8.0, hi=12.0):
    L = A.loudness(x)
    if not np.isfinite(L):
        return 0.0
    return float(np.clip(target - L, lo, hi))


def load_events(tl, path):
    if os.path.exists(rp(path)):
        return json.load(open(rp(path)))
    from collect_sfx import collect
    print(f"[mix] {path} missing — collecting SFX events in-process", file=sys.stderr)
    return collect(tl)


def place_loop(track, clip, at, until, fade=0.3, fade_in=0.0, gain_db=0.0, pan=0.0):
    need = int((until - at) * SR)
    if need <= 0:
        return track
    reps = int(np.ceil(need / len(clip))) + 1
    body = np.concatenate([clip] * reps)[:need]
    body = A.fade_in(body, max(0.006, fade_in))
    body = A.fade_out(body, max(0.02, fade))
    return A.place(track, body, at, gain_db, pan)


def render_sfx(events, N, scene_loc_at):
    meta = json.load(open(rp("audio/sfx/meta.json"))) if os.path.exists(rp("audio/sfx/meta.json")) else {}
    buses = {"THE_EDGE": A.silence(N / SR), "MIND_BACKROOM": A.silence(N / SR)}
    cache = {}
    missing = set()
    for e in events:
        f = rp(e.get("file") or f"audio/sfx/{e['name']}.wav")
        if f not in cache:
            cache[f] = A.load(f) if os.path.exists(f) else None
        clip = cache[f]
        if clip is None:
            missing.add(os.path.basename(f))
            continue
        if e.get("rate") and abs(float(e["rate"]) - 1) > 1e-3:
            clip = A.change_rate(clip, float(e["rate"]))
        sync = float(e.get("sync", meta.get(e["name"], {}).get("sync", 0.0)))
        at = float(e["t"]) - sync
        loc = scene_loc_at(float(e["t"]))
        bus = buses.get(loc, buses["THE_EDGE"])
        if e.get("until") is not None:
            until = float(e["until"])
            if e.get("loop"):
                bus = place_loop(bus, clip, at, until, float(e.get("fade", 0.3)), float(e.get("fade_in", 0.0)),
                                 float(e.get("gain_db", 0)), float(e.get("pan", 0)))
            else:
                need = int((until - at) * SR)
                c = clip[:need] if 0 < need < len(clip) else clip
                if 0 < need < len(clip):
                    c = A.fade_out(c, max(0.02, float(e.get("fade", 0.15))))
                bus = A.place(bus, c, at, float(e.get("gain_db", 0)), float(e.get("pan", 0)))
        else:
            bus = A.place(bus, clip, at, float(e.get("gain_db", 0)), float(e.get("pan", 0)))
        buses[loc if loc in buses else "THE_EDGE"] = bus
    if missing:
        print(f"[mix] missing sfx files (run audio/sfx.py): {sorted(missing)}", file=sys.stderr)
    out = np.zeros((N, 2), np.float64)
    for loc, b in buses.items():
        b = b[:N]
        if not np.any(b):
            continue
        if loc == "MIND_BACKROOM":
            w = A.reverb(b, wet=0.16, dry=1.0, keep_tail=False, decay=1.3, predelay=0.02, damping=0.6, size=0.6, seed=51)
        else:
            w = A.reverb(b, wet=0.06, dry=1.0, keep_tail=False, decay=0.6, predelay=0.01, damping=0.4, size=0.3, seed=52)
        out[: len(w)] += w[:N]
    return out.astype(np.float32)


def ambience(tl, N):
    out = np.zeros((N, 2), np.float32)
    scenes = tl["scenes"]
    # contiguous location blocks
    blocks = []
    for s in scenes:
        loc = s.get("location", "THE_EDGE")
        if blocks and blocks[-1][0] == loc:
            blocks[-1][2] = s["end"]
        else:
            blocks.append([loc, s["start"], s["end"], s.get("transition_in", "cut")])
    for i, (loc, a, b, tr) in enumerate(blocks):
        f = rp(os.path.join("audio/sfx", AMB_FILE.get(loc, "amb_edge.wav")))
        if not os.path.exists(f):
            continue
        clip = A.load(f)
        xf = 2.5 if tr == "dissolve" else 0.8
        a0 = max(0.0, a - (xf / 2 if i else 0.0))
        b1 = min(N / SR, b + (xf / 2 if i + 1 < len(blocks) else 0.0))
        out = place_loop(out, clip, a0, b1, fade=xf if i + 1 < len(blocks) else 1.5, fade_in=xf if i else 0.0,
                         gain_db=AMB_DB.get(loc, 0.0))
    return out[:N]


def dialogue(tl, N):
    """Returns (dialogue stem, speech-detector signal, stats)."""
    beats, order = tl["beats"], tl["order"]
    loc_of = {s["id"]: s.get("location", "THE_EDGE") for s in tl["scenes"]}
    names = ("narr", "edge", "back", "magi", "void", "whis", "voidwhis")
    bus = {k: A.silence(N / SR) for k in names}
    placed, missing = 0, 0
    for bid in order:
        b = beats[bid]
        if b["kind"] not in ("line", "vocal") or not b.get("audio"):
            continue
        p = rp(b["audio"])
        if not os.path.exists(p):
            missing += 1
            continue
        x = A.load(p)
        spk = b.get("speaker", "NARRATOR")
        loc = loc_of.get(b["scene"], "THE_EDGE")
        voc = b.get("vocal")
        if b["kind"] == "line":
            g = clip_gain(x, LINE_LUFS.get(spk, -20.0))
        else:
            g = clip_gain(x, VOCAL_LUFS.get(voc, -24.0))
        x = A.gain_db(x, g)
        pan = PAN.get(spk, 0.0)
        if voc == "whisper":
            key = "voidwhis" if spk == "VOID" else "whis"
            pan = 0.0
        elif spk == "VOID":
            key = "void"
            m = A.to_mono(x)
            low = octave_down(m)
            x = A.to_stereo(m) + A.to_stereo(A.lowpass(low, 1800)) * float(A.db2lin(-9.0))
            # shimmer feed: an octave-up copy goes only to the reverb (bus 'void' handles it via x_shimmer)
            sh = octave_up(m)
            bus.setdefault("void_shimmer", A.silence(N / SR))
            bus["void_shimmer"] = A.place(bus["void_shimmer"], A.highpass(sh, 900), float(b["start"]), -14.0, 0.0)
        elif spk == "NARRATOR":
            key = "narr"
        elif spk == "MAGICIAN":
            key = "magi"
        elif loc == "MIND_BACKROOM":
            key = "back"
        else:
            key = "edge"
        bus[key] = A.place(bus[key], A.to_mono(x), float(b["start"]), 0.0, pan)
        placed += 1
    for k in bus:
        bus[k] = bus[k][:N]
        if len(bus[k]) < N:
            bus[k] = np.concatenate([bus[k], np.zeros((N - len(bus[k]), 2), np.float32)])
    out = np.zeros((N, 2), np.float64)
    det = np.zeros((N, 2), np.float64)
    # NARRATOR: dry-warm, centred
    x = bus["narr"]
    if np.any(x):
        x = A.eq_chain(x, [("hp", 75), ("ls", 180, 1.0), ("peak", 3000, 1.5, 0.9), ("hs", 8500, -1.0)])
        x = A.compress(x, threshold_db=-26, ratio=2.2, attack=0.008, release=0.12, knee_db=8, makeup_db=1.5)
        x = A.reverb(x, wet=0.05, dry=1.0, keep_tail=False, decay=0.35, predelay=0.006, damping=0.5, size=0.12, seed=61)
        out += x
        det += x
    # on-screen dialogue at the dusk edge: light airy room
    x = bus["edge"]
    if np.any(x):
        x = A.eq_chain(x, [("hp", 85), ("peak", 2800, 1.0, 1.0)])
        x = A.compress(x, threshold_db=-26, ratio=2.0, attack=0.01, release=0.15, knee_db=8, makeup_db=1.0)
        x = A.reverb(x, wet=0.1, dry=1.0, keep_tail=False, decay=0.55, predelay=0.012, damping=0.45, size=0.3, seed=62)
        out += x
        det += x
    # back room: warmer, longer
    x = bus["back"]
    if np.any(x):
        x = A.eq_chain(x, [("hp", 90), ("peak", 3000, 1.0, 1.0)])
        x = A.compress(x, threshold_db=-26, ratio=2.0, attack=0.01, release=0.15, knee_db=8, makeup_db=1.0)
        x = A.reverb(x, wet=0.15, dry=1.0, keep_tail=False, decay=1.2, predelay=0.02, damping=0.6, size=0.55, seed=63)
        out += x
        det += x
    # magician: slightly creepy (slow detuned double, darker longer room)
    x = bus["magi"]
    if np.any(x):
        x = A.eq_chain(x, [("hp", 80), ("ls", 160, 1.5), ("peak", 2500, 0.8, 1.0), ("hs", 7000, -2.0)])
        x = A.compress(x, threshold_db=-26, ratio=2.2, attack=0.01, release=0.15, knee_db=8, makeup_db=1.0)
        x = chorus(x, depth_ms=5.0, rate=0.22, mix=0.3)
        x = A.reverb(x, wet=0.2, dry=1.0, keep_tail=False, decay=1.8, predelay=0.03, damping=0.7, size=0.65, seed=64)
        out += x
        det += x
    # whispers: close & intimate (dry, a little air)
    x = bus["whis"]
    if np.any(x):
        x = A.eq_chain(x, [("hp", 160), ("hs", 6000, 2.0)])
        out += x
        det += x
    x = bus["voidwhis"]
    if np.any(x):
        x = A.eq_chain(x, [("hp", 140), ("hs", 6000, 1.5)])
        out += A.reverb(x, wet=0.08, dry=1.0, keep_tail=False, decay=4.0, predelay=0.04, damping=0.6, size=0.95, width=1.3, seed=65)
        det += x
    # the Void: huge & cosmic
    x = bus["void"]
    if np.any(x):
        x = A.eq_chain(x, [("hp", 35), ("ls", 120, 2.0), ("hs", 7000, -1.5)])
        x = A.compress(x, threshold_db=-24, ratio=2.0, attack=0.015, release=0.2, knee_db=8, makeup_db=1.0)
        sh = bus.get("void_shimmer")
        wet_in = x + (sh if sh is not None else 0.0)
        wet = A.reverb_wet(wet_in, decay=4.5, predelay=0.05, damping=0.55, size=0.95, cross=0.4, width=1.4, seed=66)[:N]
        out += x + 0.3 * wet
        det += x
    stats = {"placed": placed, "missing": missing}
    return out.astype(np.float32), det.astype(np.float32), stats


def load_music(N, no_music, music_dir=None):
    if no_music:
        return None, None
    md = rp(music_dir or "out/stems")
    bp, fp = os.path.join(md, "music_bed.wav"), os.path.join(md, "music_features.wav")
    def fit(x):
        x = A.to_stereo(x)
        if len(x) < N:
            x = np.concatenate([x, np.zeros((N - len(x), 2), np.float32)])
        return x[:N]
    if os.path.exists(bp):
        bed = fit(A.load(bp))
        feat = fit(A.load(fp)) if os.path.exists(fp) else None
        return bed, feat
    if os.path.exists(rp("out/music.wav")):
        return fit(A.load(rp("out/music.wav"))), None
    print("[mix] no music found (run audio/music.py) — mixing without score", file=sys.stderr)
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default="data/timeline.json")
    ap.add_argument("--events", default="data/sfx_events.json")
    ap.add_argument("--out", default="out/mix.wav")
    ap.add_argument("--stems", default="out/stems")
    ap.add_argument("--music-dir", default=None, help="folder with music_bed.wav/music_features.wav (default out/stems)")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--no-sfx", action="store_true")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.5)
    o = ap.parse_args()
    tl = json.load(open(rp(o.timeline)))
    dur = float(tl["duration"])
    N = int(round(dur * SR))
    scenes = sorted(tl["scenes"], key=lambda s: s["start"])

    def loc_at(t):
        cur = scenes[0].get("location", "THE_EDGE")
        for s in scenes:
            if s["start"] <= t:
                cur = s.get("location", "THE_EDGE")
        return cur

    voice, det, st = dialogue(tl, N)
    print(f"[mix] dialogue: {st['placed']} clips placed, {st['missing']} missing (silence)", file=sys.stderr)
    sfx = np.zeros((N, 2), np.float32)
    if not o.no_sfx:
        ev = load_events(tl, o.events)
        sfx = A.gain_db(render_sfx(ev, N, loc_at), SFX_DB)
        print(f"[mix] sfx: {len(ev)} events", file=sys.stderr)
    amb = ambience(tl, N)
    bed, feat = load_music(N, o.no_music, o.music_dir)
    has_voice = bool(np.any(det))
    if has_voice and np.any(sfx):  # dialogue priority: SFX dip a little under speech
        sfx = A.duck(sfx, det, depth_db=SFX_DUCK_DB, attack=0.03, release=0.35, threshold_db=-46, hold=0.15, lookahead=0.02)
    stems = {"dialogue": voice, "sfx": sfx, "ambience": amb}
    if bed is not None:
        bed = A.gain_db(A.eq_chain(bed, [("hp", 40), ("ls", 120, -2.0)]), MUSIC_BED_DB)  # leave the voice's low end free
        if has_voice:
            bed = A.duck(bed, det, depth_db=DUCK_DB, attack=0.15, release=0.9, threshold_db=-46, hold=0.55, knee_db=10)
        stems["music_bed"] = bed
        if feat is not None:
            feat = A.gain_db(feat, MUSIC_FEAT_DB)
            if has_voice:
                feat = A.duck(feat, det, depth_db=FEAT_DUCK_DB, attack=0.08, release=0.4, threshold_db=-46, hold=0.2)
            stems["music_features"] = feat
    # bus peak control: estimate the master gain, then keep dialogue and SFX peaks (after that gain) a little under
    # the ceiling, so the master limiter only has to catch the overs of the sum (speech TTS has a high crest factor)
    mix = sum(v.astype(np.float64) for v in stems.values())
    g0 = o.lufs - A.loudness(mix)
    for k in ("dialogue", "sfx"):
        if np.any(stems[k]):
            stems[k] = A.limit(stems[k], o.tp - 1.0 - g0, lookahead=0.004, release=0.06)
    mix = sum(v.astype(np.float64) for v in stems.values())
    mix = A.remove_dc(mix, 15)
    pre = A.loudness(mix)
    y = A.master(mix, o.lufs, o.tp)
    y = A.fade_in(A.fade_out(y, 0.5), 0.01)  # frame 0 is the film: start at once, but never with a click
    A.save(rp(o.out), y)
    g = o.lufs - pre if np.isfinite(pre) else 0.0
    if o.stems:
        os.makedirs(rp(o.stems), exist_ok=True)
        for k, v in stems.items():
            A.save(os.path.join(rp(o.stems), f"mix_{k}.wav"), A.gain_db(v, g), subtype="FLOAT", dither=False)
    an = A.analyze(y)
    for k, v in stems.items():
        L = A.loudness(A.gain_db(v, g))
        print(f"  {k:15s} LUFS {L:6.1f}  peak {A.lin2db(np.abs(v).max() * A.db2lin(g)):6.1f} dBFS", file=sys.stderr)
    print(f"[mix] {o.out}: {an['seconds']} s  LUFS {an['lufs']}  TP {an['true_peak_db']} dBTP  peak {an['peak_db']}  "
          f"click {an['click_score']}  (pre-master {pre:.1f} LUFS, gain {g:+.1f} dB)", file=sys.stderr)


if __name__ == "__main__":
    main()
