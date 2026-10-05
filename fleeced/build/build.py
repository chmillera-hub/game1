#!/usr/bin/env python3
"""Build the FLEECED soundtrack and the timeline the animation syncs to.

    python build/build.py            # voices (cached) + music + sfx + mix
    python build/build.py --report   # also print per-line timings

Outputs:
    web/audio/soundtrack.mp3   (player)
    .cache/soundtrack.wav      (video render)
    web/js/timeline.js         (window.FLEECED_TIMELINE)
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from dsp import SR, n_of, db, add_at, fade, stereo, pan  # noqa: E402
from sfx import SFX  # noqa: E402
from music import CUES  # noqa: E402

CACHE = ROOT / ".cache"
MODELS = Path(os.environ.get("KOKORO_MODELS", ROOT / ".models"))
FPS_ENV = 30  # mouth-envelope resolution


def sh(*args):
    subprocess.run([str(a) for a in args], check=True)


def rms_db(x):
    x = np.asarray(x)
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


# ------------------------------------------------------------------ voices
_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    return _kokoro


def voice_line(spk, text, lexicon=None):
    """TTS -> 48 kHz mono, character FX, trimmed and level-matched. Cached on disk.
    `lexicon` maps words to IPA overrides (e.g. to stop "bleating" sounding like "bleeding")."""
    fx = spk.get("fx") or {}
    lex = {w: p for w, p in (lexicon or {}).items() if re.search(rf"\b{re.escape(w)}\b", text, re.I)}
    key = hashlib.sha1(json.dumps([spk["voice"], spk["speed"], text, fx, spk["level"], lex, "v3"]).encode()).hexdigest()[:16]
    out = CACHE / "voice" / f"{key}.wav"
    if out.exists():
        y, _ = sf.read(out)
        return y
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = CACHE / "voice" / f"{key}.raw.wav"
    lang = "en-gb" if spk["voice"].startswith("b") else "en-us"
    if lex:
        tok = kokoro().tokenizer
        ph = tok.phonemize(text, lang)
        for w, ipa in lex.items():
            ph = ph.replace(tok.phonemize(w, lang).strip(), ipa)
        samples, sr = kokoro().create(ph, voice=spk["voice"], speed=spk["speed"], lang=lang, is_phonemes=True)
    else:
        samples, sr = kokoro().create(text, voice=spk["voice"], speed=spk["speed"], lang=lang)
    # pad so ffmpeg's rubberband (which has start-up latency) doesn't swallow short clips
    samples = np.concatenate([np.zeros(int(0.5 * sr)), samples, np.zeros(int(1.0 * sr))])
    sf.write(raw, samples, sr)
    chain = ["aresample=48000", "highpass=f=70"]
    if fx:
        chain.append(f"rubberband=pitch={fx.get('pitch', 1.0)}")
        chain.append("equalizer=f=1500:t=q:w=1.1:g=3")
    fxwav = CACHE / "voice" / f"{key}.fx.wav"
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", ",".join(chain), "-ac", "1", "-ar", SR, fxwav)
    y, _ = sf.read(fxwav)
    raw.unlink()
    fxwav.unlink()
    # sheep "bleat" wobble (done here: ffmpeg's vibrato filter emits NaN on digital silence)
    tt = np.arange(len(y)) / SR
    if "vibrato" in fx:
        f, d = fx["vibrato"]
        depth = d * 0.06 / (2 * np.pi * f) * SR  # d=1 -> +/-6% pitch swing
        pos = np.arange(len(y)) - depth * (1 + np.sin(2 * np.pi * f * tt))
        y = np.interp(pos, np.arange(len(y)), y, left=0.0, right=0.0)
    if "tremolo" in fx:
        f, d = fx["tremolo"]
        y = y * (1 - d * (0.5 + 0.5 * np.sin(2 * np.pi * f * tt + 1.0)))
    # trim silence
    a = np.abs(y)
    if a.max() < 1e-4:
        raise RuntimeError(f"voice FX produced silence for {text!r}")
    thr = a.max() * db(-38)
    idx = np.where(a > thr)[0]
    y = y[max(0, idx[0] - n_of(0.03)): idx[-1] + n_of(0.07)]
    y = fade(y, 0.01, 0.04)
    # level: RMS over active 20 ms frames
    fr = n_of(0.02)
    frames = y[: len(y) // fr * fr].reshape(-1, fr)
    fr_rms = np.sqrt((frames ** 2).mean(axis=1))
    active = frames[fr_rms > fr_rms.max() * db(-30)]
    y *= db(spk["level"] - rms_db(active))
    y = np.tanh(y * 1.4) / 1.4 if np.abs(y).max() > 0.7 else y  # soft safety limiter
    sf.write(out, y, SR)
    return y


def mouth_env(y):
    """Per-frame mouth openness 0..9 encoded as a digit string."""
    n = int(np.ceil(len(y) / SR * FPS_ENV))
    hop = SR / FPS_ENV
    vals = []
    for i in range(n):
        a, b = int(i * hop - hop / 2), int(i * hop + hop * 1.5)
        seg = y[max(0, a): max(1, min(len(y), b))]
        vals.append(rms_db(seg) if len(seg) else -90)
    v = np.clip((np.array(vals) + 42) / 26, 0, 1)
    v = np.convolve(v, [0.25, 0.5, 0.25], mode="same")
    return "".join(str(int(round(x * 9))) for x in v)


# ------------------------------------------------------------------ timeline
def build_timeline(script, voices):
    d = script["defaults"]
    t = 0.0
    scenes, lines, cues = [], [], {}
    for sc in script["scenes"]:
        start = t
        cursor = start + sc.get("lead", d["lead"])
        for i, ln in enumerate(sc["lines"]):
            cursor += ln.get("gap", d["gap"] if i else 0)
            dur = len(voices[ln["id"]]) / SR
            ls, le = cursor, cursor + dur
            lines.append({"id": ln["id"], "who": ln["who"], "text": ln.get("cap", ln["text"]),
                          "start": round(ls, 3), "end": round(le, 3), "scene": sc["id"]})
            for c in ln.get("cues", []):
                cues[c["id"]] = (le if c.get("from") == "end" else ls) + c.get("t", 0)
            cursor = le
        end = max(cursor + sc.get("hold", d["hold"]), start + sc.get("minDur", 0))
        for c in sc.get("cues", []):
            cues[c["id"]] = (end if c.get("from") == "end" else start) + c.get("t", 0)
        scenes.append({"id": sc["id"], "start": round(start, 3), "end": round(end, 3)})
        t = end
    return scenes, lines, {k: round(v, 3) for k, v in cues.items()}, t


def resolve(ref, scene_start, scene_end, cues):
    if ref is None:
        return scene_end
    if isinstance(ref, (int, float)):
        return scene_start + ref
    return cues[ref]


# ------------------------------------------------------------------ mix
def duck_curve(voice_mono, attack=0.06, release=0.45, floor_db=-45):
    hop = n_of(0.01)
    nfr = len(voice_mono) // hop + 1
    act = np.zeros(nfr)
    for i in range(nfr):
        seg = voice_mono[i * hop:(i + 1) * hop]
        act[i] = 1.0 if len(seg) and rms_db(seg) > floor_db else 0.0
    env = np.zeros(nfr)
    ka, kr = np.exp(-0.01 / attack), np.exp(-0.01 / release)
    e = 0.0
    # look-ahead so the music dips just before the line starts
    look = int(0.08 / 0.01)
    act = np.concatenate([act[look:], np.zeros(look)])
    for i in range(nfr):
        k = ka if act[i] > e else kr
        e = act[i] + (e - act[i]) * k
        env[i] = e
    return np.interp(np.arange(len(voice_mono)) / hop, np.arange(nfr), env)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--no-mp3", action="store_true")
    args = ap.parse_args()

    script = json.loads((ROOT / "script.json").read_text())
    spk = script["speakers"]

    print("voices ...", flush=True)
    voices = {}
    for sc in script["scenes"]:
        for ln in sc["lines"]:
            voices[ln["id"]] = voice_line(spk[ln["who"]], ln["text"], script.get("lexicon"))

    scenes, lines, cues, total = build_timeline(script, voices)
    N = n_of(total + 0.5)
    print(f"total duration {total:.2f}s ({int(total // 60)}:{total % 60:04.1f})")

    # voice bus
    vbus = np.zeros(N)
    for ln in lines:
        add_at(vbus, voices[ln["id"]], n_of(ln["start"]))
        ln["mouth"] = mouth_env(voices[ln["id"]]) if ln["who"] != "narrator" else ""

    rng = np.random.default_rng(2026)
    # music bus (consecutive scenes sharing a cue are one continuous segment)
    print("music ...", flush=True)
    segs = []
    by_id = {s["id"]: s for s in script["scenes"]}
    for s in scenes:
        name = by_id[s["id"]].get("music")
        if segs and segs[-1]["name"] == name:
            segs[-1]["end"] = s["end"]
            segs[-1]["scene_ids"].append(s["id"])
        else:
            segs.append({"name": name, "start": s["start"], "end": s["end"], "scene_ids": [s["id"]]})
    levels = {"farm": -28, "farm2": -28, "sneaky": -29, "brains": -30, "jesus": -27,
              "tension": -27, "riot": -25, "aftermath": -27}
    bed_bus, lead_bus = np.zeros((N, 2)), np.zeros((N, 2))
    for i, sg in enumerate(segs):
        if sg["name"] is None:
            continue
        last = by_id[sg["scene_ids"][-1]]
        end = cues[last["musicEnd"]] if "musicEnd" in last else sg["end"]
        nxt = segs[i + 1] if i + 1 < len(segs) else None
        hard = "musicEnd" in last or (nxt is not None and by_id[nxt["scene_ids"][0]].get("musicCut"))
        tail = 0.04 if hard else 1.2
        dur = end - sg["start"]
        fn = CUES[sg["name"]]
        if sg["name"] == "riot":
            stems = fn(dur + tail, rng, anchor=cues["stomp1"] - sg["start"])
        else:
            stems = fn(dur + tail, rng)
        n = n_of(dur + tail)
        bed = stems["bed"][:n]
        lead = stems["lead"][:n]
        mix_rms = rms_db(bed + lead)
        g = db(levels[sg["name"]] - mix_rms)
        fin = 0.02 if by_id[sg["scene_ids"][0]].get("musicCut") else 0.4
        add_at(bed_bus, fade(bed * g, fin, tail + (0.0 if hard else 0.3)), n_of(sg["start"]))
        add_at(lead_bus, fade(lead * g, fin, tail + (0.0 if hard else 0.3)), n_of(sg["start"]))

    duck = duck_curve(vbus)
    bed_bus *= db(-8 * duck)[:, None]
    lead_bus *= db(-17 * duck)[:, None]

    # sfx + ambience
    print("sfx ...", flush=True)
    sfx_bus = np.zeros((N, 2))
    allcues = []
    for sc in script["scenes"]:
        allcues += sc.get("cues", [])
        for ln in sc["lines"]:
            allcues += ln.get("cues", [])
    for c in allcues:
        if not c.get("sfx"):
            continue
        y = SFX[c["sfx"]](np.random.default_rng(int(hashlib.md5(c["id"].encode()).hexdigest()[:8], 16)))
        y = stereo(y) if y.ndim == 1 and "pan" not in c else (pan(y, c["pan"]) if y.ndim == 1 else y)
        y = y * (0.9 / max(1e-9, np.abs(y).max())) * db(c.get("gain", -10))
        add_at(sfx_bus, y, n_of(cues[c["id"]]))
    for s in scenes:
        for a in by_id[s["id"]].get("amb", []):
            t0 = resolve(a["from"], s["start"], s["end"], cues)
            t1 = resolve(a["to"], s["start"], s["end"], cues)
            y = SFX[a["sfx"]](np.random.default_rng(7), dur=t1 - t0 + 0.3)
            y = y * db(a["gain"] - rms_db(y))
            add_at(sfx_bus, fade(y, a.get("fade", 1.0), 0.35), n_of(t0))

    master = stereo(vbus) * np.sqrt(2) + bed_bus + lead_bus + sfx_bus
    peak = np.abs(master).max()
    if peak > 0.98:
        master = np.tanh(master / peak * 1.2) * 0.98 / np.tanh(1.2)
    CACHE.mkdir(exist_ok=True)
    pre = CACHE / "premaster.wav"
    sf.write(pre, master.astype(np.float32), SR, subtype="FLOAT")

    print("master ...", flush=True)
    wav = CACHE / "soundtrack.wav"
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af",
                           "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    ln_filter = ("loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:"
                 "measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true").format(**j)
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", pre, "-af", ln_filter + ",aresample=48000", "-c:a", "pcm_s16le", wav)
    if not args.no_mp3:
        mp3 = ROOT / "web" / "audio" / "soundtrack.mp3"
        mp3.parent.mkdir(parents=True, exist_ok=True)
        sh("ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "160k", mp3)

    speakers = {k: {"color": v.get("color", "#fff"), "name": v.get("name", "")} for k, v in spk.items()}
    tl = {"title": script["title"], "subtitle": script["subtitle"], "fps": script["fps"],
          "duration": round(total, 3), "envFps": FPS_ENV, "speakers": speakers,
          "scenes": scenes, "lines": lines, "cues": cues}
    js = ROOT / "web" / "js" / "timeline.js"
    js.write_text("// Generated by build/build.py - do not edit.\nwindow.FLEECED_TIMELINE = "
                  + json.dumps(tl, separators=(",", ":")) + ";\n")
    print("wrote", js.relative_to(ROOT), "and soundtrack")

    if args.report:
        for s in scenes:
            print(f"\n[{s['id']}] {s['start']:7.2f} - {s['end']:7.2f}  ({s['end'] - s['start']:.2f}s)")
            for ln in lines:
                if ln["scene"] == s["id"]:
                    print(f"   {ln['start']:7.2f} {ln['end'] - ln['start']:5.2f}s {ln['who']:9s} {ln['text']}")


if __name__ == "__main__":
    main()
