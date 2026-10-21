"""Sing every line of the score; write vocal stems + lyric timings.

  python3 vocals.py  ->  build/vox_*.wav (48 kHz stereo), build/lyrics.json
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import score as SC  # noqa: E402
from sing import Note, SR_TTS, sing_phrase, pipeline  # noqa: E402
from synth import midi  # noqa: E402

BUILD = os.path.join(HERE, "build")
CACHE = os.path.join(BUILD, "cache")
SR = 48000


def sec_start(section):
    for name, bar0, nbars, _ in SC.SECTIONS:
        if name == section:
            return bar0 * SC.BAR
    raise KeyError(section)


def parse(tokens, transpose=0):
    """-> words [(display, nsyl)], notes [Note] with times relative to the line start."""
    words, notes = [], []
    t = 0.0
    cur = None
    for tok in tokens.split():
        syl, note, beats = tok.split("|")
        accent = beats.endswith(">")
        fall = beats.endswith("~")
        beats = float(beats.rstrip(">~"))
        d = beats * SC.BEAT
        if syl == "_":
            notes.append(Note(None, None, t, d, None))
            t += d
            continue
        cont = cur is not None and cur[2]
        part = syl.rstrip("-")
        if cont:
            cur[0] += part
            cur[1] += 1
        else:
            cur = [part, 1, False]
            words.append(cur)
        cur[2] = syl.endswith("-")
        notes.append(Note(part, midi(note) + transpose, t, d, None, accent=accent, fall=fall))
        notes[-1].word = len(words) - 1
        t += d
    return [(w[0], w[1]) for w in words], notes


def tts_word(display):
    return re.sub(r"[^\w']", "", display)


def sing_cached(words, notes, voice, shift, formant=1.0):
    key = hashlib.md5(json.dumps([[w for w in words], [(n.pitch, round(n.start, 4), round(n.dur, 4), n.accent, n.fall)
                                                        for n in notes], voice, shift, formant, 4]).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"{key}.npz")
    if os.path.exists(path):
        d = np.load(path, allow_pickle=True)
        return d["y"], list(d["timings"]), float(d["pre"])
    sn = []
    for n in notes:
        m = Note(n.syl, None if n.pitch is None else n.pitch + shift, n.start, n.dur, n.word, n.accent, n.fall)
        sn.append(m)
    tw = [(tts_word(w), k) for w, k in words]
    y, timings, pre = sing_phrase(tw, sn, voice, formant_shift=formant)
    np.savez(path, y=y, timings=np.array(timings, dtype=object), pre=pre)
    return y, timings, pre


def to48(y):
    return resample_poly(y, 2, 1).astype(np.float32)


def place(buf, t, y, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i < 0:
        y = y[-i:]
        i = 0
    m = min(len(y), len(buf) - i)
    if m <= 0:
        return
    a = (pan + 1) * math.pi / 4
    buf[i:i + m, 0] += y[:m] * gain * math.cos(a)
    buf[i:i + m, 1] += y[:m] * gain * math.sin(a)


def rubberband(y, sr, pitch=0.0, tempo=1.0):
    if abs(pitch) < 1e-3 and abs(tempo - 1) < 1e-3:
        return y
    tmp_i, tmp_o = os.path.join(BUILD, "_rb_in.wav"), os.path.join(BUILD, "_rb_out.wav")
    sf.write(tmp_i, y, sr, subtype="FLOAT")
    af = f"rubberband=pitch={2 ** (pitch / 12):.5f}:tempo={tempo:.5f}:formant=preserved:pitchq=quality"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp_i, "-af", af, "-c:a", "pcm_f32le", tmp_o], check=True)
    out, _ = sf.read(tmp_o, dtype="float32")
    return out if out.ndim == 1 else out[:, 0]


def with_punctuation(text, words):
    """TTS word tokens drop punctuation; take the written words back when they line up."""
    src = re.sub(r"\|[0-9.]*\|", " ", text).split()
    if len(src) != len(words):
        return words
    return [(s, a, b) for s, (w, a, b) in zip(src, words)]


def speak_line(text, voice, speed):
    """Spoken line with '|pause|' chunks -> (audio 24k, [(word, t0, t1)])."""
    parts = re.split(r"\s*\|([0-9.]*)\|?\s*", text)
    out, words, t = [], [], 0.0
    for i in range(0, len(parts), 2):
        chunk = parts[i].strip()
        if not chunk:
            continue
        pause = float(parts[i + 1]) if i + 1 < len(parts) and parts[i + 1] else 0.0
        segs, cw, off = [], [], 0.0
        for r in pipeline()(chunk, voice=voice, speed=speed):
            a = r.output.audio.numpy()
            for tk in r.tokens:
                if tk.start_ts is not None and any(c.isalnum() for c in tk.text):
                    cw.append((tk.text, off + tk.start_ts, off + tk.end_ts))
            segs.append(a)
            off += len(a) / SR_TTS
        a = np.concatenate(segs)
        env = np.convolve(np.abs(a), np.ones(240) / 240, mode="same")
        idx = np.where(env > 0.006)[0]
        s0 = max(0, idx[0] - 240) if len(idx) else 0
        e0 = min(len(a), idx[-1] + 1200) if len(idx) else len(a)
        a = a[s0:e0]
        shift = s0 / SR_TTS
        words += [(w, t + max(0.0, x0 - shift), t + max(0.0, x1 - shift)) for (w, x0, x1) in cw]
        out.append(a)
        t += len(a) / SR_TTS
        if pause:
            out.append(np.zeros(int(pause * SR_TTS), np.float32))
            t += pause
    y = np.concatenate(out) if out else np.zeros(1, np.float32)
    return y, words


def main():
    os.makedirs(CACHE, exist_ok=True)
    total = SC.TOTAL_BARS * SC.BAR + 2.0
    n = int(total * SR)
    stems = {k: np.zeros((n, 2), np.float32) for k in ("lead", "gang", "kids", "spoken")}
    lyrics = []
    for (section, bar_off, beat_off, who, tokens, tr) in SC.LINES:
        t0 = sec_start(section) + bar_off * SC.BAR + beat_off * SC.BEAT
        words, notes = parse(tokens, tr)
        timing = None
        if who == "ALL":
            gang = SC.GANG_FINAL if section in ("chorus3", "chorus4") else SC.GANG
            for (voice, shift, gain, pan, delay) in gang:
                y, timings, pre = sing_cached(words, notes, voice, shift)
                y = to48(y)
                place(stems["gang"], t0 - pre + delay, y / (np.abs(y).max() + 1e-9) * 0.5, gain, pan)
                if timing is None:
                    timing = timings
        elif who in ("TIBBS", "MICE"):
            y, timings, pre = sing_cached(words, notes, SC.SINGERS[who]["voice"], 0, formant=1.18)
            place(stems["kids"], t0 - pre, to48(y) / (np.abs(y).max() + 1e-9) * 0.55, 1.0, 0.1)
            y2, _, pre2 = sing_cached(words, notes, "af_bella", 0, formant=1.12)
            place(stems["kids"], t0 - pre2 + 0.015, to48(y2) / (np.abs(y2).max() + 1e-9) * 0.4, 1.0, -0.25)
            timing = timings
        else:
            voice = SC.SINGERS[who]["voice"]
            y, timings, pre = sing_cached(words, notes, voice, 0)
            y48 = to48(y) / (np.abs(y).max() + 1e-9) * 0.62
            place(stems["lead"], t0 - pre, y48, 1.0, 0.0)
            # a quiet double for body
            yd, _, pre_d = sing_cached(words, notes, voice, 0, formant=0.98)
            place(stems["lead"], t0 - pre_d + 0.016, to48(yd) / (np.abs(yd).max() + 1e-9) * 0.62, 0.32, 0.25)
            timing = timings
        # lyric words (absolute)
        wmap = {}
        for (wi, a, b) in timing:
            if wi is None:
                continue
            wmap.setdefault(int(wi), [a, b])
            wmap[int(wi)][1] = b
        lw = [dict(text=words[i][0], start=round(t0 + wmap[i][0], 3), end=round(t0 + wmap[i][1], 3), mark=None, chunk=0)
              for i in sorted(wmap)]
        lyrics.append(dict(id=f"{section}_{bar_off}_{beat_off}", who=who, start=lw[0]["start"], end=lw[-1]["end"],
                           words=lw, sung=True))
        print(f"{section:8s} {who:9s} {lw[0]['start']:7.2f}-{lw[-1]['end']:7.2f}  {' '.join(w['text'] for w in lw)[:60]}",
              flush=True)
    for (section, bar_off, beat_off, who, text, speed, max_bars) in SC.SPOKEN:
        t0 = sec_start(section) + bar_off * SC.BAR + beat_off * SC.BEAT
        voice = SC.SINGERS[who]["voice"]
        y, words = speak_line(text, voice, speed)
        dur = len(y) / SR_TTS
        tempo = max(1.0, dur / (max_bars * SC.BAR))
        y = rubberband(y, SR_TTS, SC.SPOKEN_PITCH.get(who, 0.0), tempo)
        words = with_punctuation(text, [(w, a / tempo, b / tempo) for (w, a, b) in words])
        y48 = to48(y) / (np.abs(y).max() + 1e-9) * 0.6
        if who == "MICE":
            yk, _ = speak_line(text, "af_bella", speed)
            yk = rubberband(yk, SR_TTS, 2.0, 1.0)
            place(stems["spoken"], t0 + 0.02, to48(yk) / (np.abs(yk).max() + 1e-9) * 0.45, 1.0, -0.3)
        place(stems["spoken"], t0, y48, 1.0, 0.0)
        lw = [dict(text=w, start=round(t0 + a, 3), end=round(t0 + b, 3), mark=None, chunk=0) for (w, a, b) in words]
        lyrics.append(dict(id=f"{section}_{bar_off}_spoken", who=who, start=lw[0]["start"], end=lw[-1]["end"],
                           words=lw, sung=False))
        print(f"{section:8s} {who:9s} {lw[0]['start']:7.2f}-{lw[-1]['end']:7.2f}  (spoken) {text[:50]}  x{tempo:.2f}",
              flush=True)
    lyrics.sort(key=lambda d: d["start"])
    for k, buf in stems.items():
        sf.write(os.path.join(BUILD, f"vox_{k}.wav"), buf, SR, subtype="FLOAT")
    with open(os.path.join(BUILD, "lyrics.json"), "w") as f:
        json.dump(lyrics, f, indent=1)
    print("done", total)


if __name__ == "__main__":
    main()
