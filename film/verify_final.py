#!/usr/bin/env python3
"""verify_final.py -- check the assembled film before it ships.
    python3 film/verify_final.py        -> film/build/qa/final_report.txt, film/build/qa/final_captions.png

1. Container: one H.264 video and one AAC audio stream, duration matches the timeline, file <= 15 MB.
2. Captions: every caption event is burned in -- the caption band of the final frame differs from the same
   frame of the caption-free scene render (control: a caption-free moment must not); a strip of every
   caption band is saved for eyeballing.
3. Voices: every spoken or sung line is transcribed from the final file's own audio track with
   faster-whisper and compared with the script (word error rate); falls back to a loudness check if no
   speech model can be loaded.
Exit status 1 if anything fails.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
QA = BUILD / "qa"
FILM = ROOT / "out" / "the_stone_and_the_bread.mp4"
FPS = 24
MAX_MB = 15.0
W, H = 1280, 720
BAND = (int(H * 0.80), int(H * 0.985))  # where the bottom-centre captions sit
SR = 16000


def ffprobe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size:stream=codec_type,codec_name,width,height,channels",
                        "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def frame(path, t, scale=False):
    vf = ["-vf", f"scale={W}:{H}:flags=lanczos"] if scale else []
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1", *vf,
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(H, W).astype(np.int16)


def ass_seconds(s):
    h, m, sec = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(sec)


def norm_words(t):
    t = re.sub(r"[^a-z0-9' ]+", " ", t.lower().replace("—", " ").replace("…", " "))
    return t.split()


def wer(ref, hyp):
    r, h = norm_words(ref), norm_words(hyp)
    d = np.arange(len(h) + 1)
    for i, rw in enumerate(r, 1):
        prev, d = d, np.empty_like(d)
        d[0] = i
        for j, hw in enumerate(h, 1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (rw != hw))
    return d[-1] / max(1, len(r))


def main():
    QA.mkdir(parents=True, exist_ok=True)
    tl = json.loads((ROOT / "timeline.json").read_text())
    report, failures = [], []

    def note(ok, msg):
        report.append(("PASS  " if ok else "FAIL  ") + msg)
        if not ok:
            failures.append(msg)

    # 1. container
    info = ffprobe(FILM)
    streams = {s["codec_type"]: s for s in info["streams"]}
    dur, size_mb = float(info["format"]["duration"]), int(info["format"]["size"]) / 1e6
    total = sum(round(sc["duration"] * FPS) / FPS for sc in tl["scenes"])
    v, a = streams.get("video", {}), streams.get("audio", {})
    note(v.get("codec_name") == "h264", f"video stream: {v.get('codec_name')} {v.get('width')}x{v.get('height')}")
    note(a.get("codec_name") == "aac", f"audio stream: {a.get('codec_name')} {a.get('channels')} ch")
    note(abs(dur - total) < 0.15, f"duration {dur:.2f} s (timeline {total:.2f} s)")
    note(size_mb <= MAX_MB, f"file size {size_mb:.2f} MB (limit {MAX_MB} MB)")

    # 2. captions
    starts, acc = [], 0.0
    for sc in sorted(tl["scenes"], key=lambda s: s["id"]):
        starts.append((acc, sc["id"]))
        acc += round(sc["duration"] * FPS) / FPS

    def source_frame(t):
        s0, sid = [(s, i) for s, i in starts if s <= t][-1]
        return frame(BUILD / "video" / f"s{sid}.mp4", t - s0, scale=True)

    def band_diff(t):
        a_, b_ = frame(FILM, t), source_frame(t)
        return int((np.abs(a_ - b_)[BAND[0]:BAND[1]] > 70).sum())

    events = []
    for line in (BUILD / "captions.ass").read_text().splitlines():
        if line.startswith("Dialogue:"):
            f = line.split(",", 9)
            events.append((ass_seconds(f[1]), ass_seconds(f[2]), re.sub(r"\{[^}]*\}", "", f[9])))
    expected = sum(1 for ln in tl["lines"] if ln.get("caption", True))
    note(len(events) == expected, f"{len(events)} caption events for {expected} captioned lines")
    capt = [(e[0], e[1]) for e in events]
    quiet = next((t for t in np.arange(1.0, total, 0.5) if all(not (s - 0.3 <= t <= e + 0.3) for s, e in capt)), 1.0)
    control = band_diff(quiet)
    strips = []
    for s, e, text in events:
        t = s + min(0.6, (e - s) / 2)
        n = band_diff(t)
        ok = n > max(250, 4 * control)
        note(ok, f"caption burned in at {t:7.2f} s ({n} px changed): {text[:60]}")
        img = Image.open(_png(FILM, t)).crop((0, BAND[0] - 10, W, BAND[1]))
        strips.append(img)
    report.append(f"      control (no caption) at {quiet:.2f} s: {control} px changed")
    if strips:
        sheet = Image.new("RGB", (W, sum(s.height for s in strips)))
        y = 0
        for s in strips:
            sheet.paste(s, (0, y))
            y += s.height
        sheet.save(QA / "final_captions.png")

    # 3. voices, from the final file's own audio
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(FILM), "-vn", "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    audio = np.frombuffer(r.stdout, np.float32)
    spoken = [ln for ln in tl["lines"] if not ln["id"].endswith("laugh")]
    try:
        from faster_whisper import WhisperModel
        asr = WhisperModel("base.en", device="cpu", compute_type="int8", cpu_threads=2)
    except Exception as exc:  # no model available offline
        asr = None
        report.append(f"      speech model unavailable ({exc.__class__.__name__}); using loudness only")
    for ln in spoken:
        a0, a1 = int(max(0, ln["global_start"] - 0.2) * SR), int((ln["global_end"] + 0.3) * SR)
        clip = audio[a0:a1]
        rms_db = 20 * np.log10(np.sqrt(np.mean(clip ** 2)) + 1e-9)
        if asr is None:
            note(rms_db > -40, f"{ln['id']:9s} audible ({rms_db:.1f} dBFS)")
            continue
        segs, _ = asr.transcribe(clip, language="en", beam_size=5, vad_filter=False,
                                 condition_on_previous_text=False)
        hyp = " ".join(s.text.strip() for s in segs).strip()
        err = wer(ln["text"], hyp)
        limit = 0.6 if ln["speaker"] == "BARD" else 0.5  # sung lines transcribe less cleanly
        note(err <= limit, f"{ln['id']:9s} voice heard (WER {err:.2f}, {rms_db:.1f} dBFS): \"{hyp[:70]}\"")

    report.append(f"\n{len(failures)} failure(s)")
    text = "\n".join(report)
    (QA / "final_report.txt").write_text(text + "\n")
    print(text)
    sys.exit(1 if failures else 0)


def _png(path, t):
    out = QA / "_cap.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1", str(out)],
                   check=True)
    return out


if __name__ == "__main__":
    main()
