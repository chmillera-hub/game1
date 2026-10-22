#!/usr/bin/env python3
"""assemble.py -- join the rendered scenes, the soundtrack and the captions into the final film.

    python3 film/assemble.py            -> film/out/the_stone_and_the_bread.mp4

Inputs: film/build/video/s0.mp4 .. s9.mp4 (python3 film/render.py --all), film/build/audio/mix.wav
(python3 film/audio/mix.py) and film/timeline.json (captions). Captions follow SPEC section 3: Inter
SemiBold, bottom-center; "caption": false lines are skipped; voiceover is italic; sung lines are italic
with a note on each side; the drowned tavern line fades out as the music swells.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
VIDEO = BUILD / "video"
OUT = ROOT / "out" / "the_stone_and_the_bread.mp4"
FPS = 24
MAX_MB = 15.0     # hard ceiling for the final file (MB = 10^6 bytes)
TARGET_MB = 14.2  # what the two-pass encode aims for, leaving room for container overhead
AUDIO_KBPS = 96
OUT_SIZE = "1280:720"


def ass_time(t):
    cs = max(0, int(round(t * 100)))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_escape(text):
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def build_captions(tl, path):
    """Write an ASS subtitle file from timeline lines, timed on the frame grid the scenes render on."""
    starts, acc = {}, 0.0
    for sc in sorted(tl["scenes"], key=lambda s: s["id"]):
        starts[sc["id"]] = acc
        acc += round(sc["duration"] * FPS) / FPS
    beats = {b["id"]: b for b in tl.get("beats", [])}
    shown = sorted((ln for ln in tl["lines"] if ln.get("caption", True)),
                   key=lambda ln: starts[ln["scene"]] + ln["start"])
    events = []
    for k, ln in enumerate(shown):
        t0 = starts[ln["scene"]] + ln["start"]
        t1 = starts[ln["scene"]] + ln["end"] + 0.25
        if k + 1 < len(shown):  # never stack two captions: hand over just before the next line
            nxt = shown[k + 1]
            t1 = min(t1, starts[nxt["scene"]] + nxt["start"] - 0.04)
        text = ass_escape(ln["text"])
        if ln.get("sung"):
            text = "{\\i1}♪ " + text + " ♪"
        elif ln.get("vo"):
            text = "{\\i1}" + text
        if ln.get("fx") == "drowned":
            swell = beats.get(f"s{ln['scene']}_swell")
            fade_ms = int(max(0.3, t1 - (starts[ln["scene"]] + swell["t"])) * 1000) if swell else 900
            text = "{\\fad(120,%d)}" % fade_ms + text
        events.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Main,,0,0,0,,{text}")
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Inter SemiBold,46,&H00FFFFFF,&H00FFFFFF,&H64000000,&H8C000000,0,0,0,0,100,100,0.5,0,1,2.6,1.6,2,160,160,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return acc


def main():
    tl = json.loads((ROOT / "timeline.json").read_text())
    ids = [s["id"] for s in sorted(tl["scenes"], key=lambda s: s["id"])]
    missing = [i for i in ids if not (VIDEO / f"s{i}.mp4").exists()]
    if missing:
        sys.exit(f"missing scene videos: {missing} (run python3 film/render.py --all)")
    mix = BUILD / "audio" / "mix.wav"
    if not mix.exists():
        sys.exit("missing film/build/audio/mix.wav (run python3 film/audio/mix.py)")
    BUILD.mkdir(exist_ok=True)
    subs = BUILD / "captions.ass"
    total = build_captions(tl, subs)
    concat = BUILD / "concat.txt"
    concat.write_text("".join(f"file '{(VIDEO / f's{i}.mp4').resolve()}'\n" for i in ids))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Two-pass 720p H.264 sized to stay under MAX_MB. The film grain is lightly denoised first: at this
    # bitrate it would otherwise eat the bits and crawl as blocks; captions are burned in before the
    # downscale so the text stays crisp.
    target = TARGET_MB
    for attempt in range(3):
        video_kbps = int((target * 8e3 / total) - AUDIO_KBPS)
        base = ["ffmpeg", "-y", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", str(concat), "-i", str(mix),
                "-vf", f"hqdn3d=1.5:1.5:3:3,subtitles={subs},scale={OUT_SIZE}:flags=lanczos",
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-b:v", f"{video_kbps}k",
                "-maxrate", f"{video_kbps * 2}k", "-bufsize", f"{video_kbps * 4}k",
                "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", f"{total:.4f}",
                "-passlogfile", str(BUILD / "x264pass")]
        print(f"encoding at {video_kbps} kb/s video + {AUDIO_KBPS} kb/s audio")
        subprocess.run(base + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"], check=True)
        subprocess.run(base + ["-pass", "2", "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-ar", "48000",
                               "-movflags", "+faststart", str(OUT)], check=True)
        size_mb = OUT.stat().st_size / 1e6
        if size_mb <= MAX_MB:
            break
        target *= 0.97 * MAX_MB / size_mb
        print(f"{size_mb:.2f} MB is over {MAX_MB} MB: retrying smaller")
    print(f"wrote {OUT} ({total:.2f} s, {size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
