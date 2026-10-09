"""End-to-end build of "If You Have Time".

    python3 build.py              # everything that is missing, then mix + render + encode
    python3 build.py --force      # regenerate audio assets too
    python3 build.py encode       # only the final encode (needs build/video_master.mkv + build/mix.wav)
    python3 build.py audio        # tts/timeline/music/sfx/mix only

Final file: out/if_you_have_time.mp4 - H.264 High + AAC-LC, 720x1280 @ 24 fps, sized to TARGET_BYTES.
"""
import json
import subprocess
import sys
from pathlib import Path

from config import BUILD, OUT, ROOT, VO_DIR, MUSIC_DIR, SFX_DIR

TARGET_BYTES = 14_000_000      # stays safely under 15 MB
AUDIO_KBPS = 96
OUT_FILE = OUT / "if_you_have_time.mp4"


def run(*cmd, cwd=ROOT):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(list(map(str, cmd)), check=True, cwd=cwd)


def audio(force=False):
    if force or not (VO_DIR / "manifest.json").exists():
        run(sys.executable, "audio/tts.py")
    run(sys.executable, "audio/timeline.py")
    if force or not (MUSIC_DIR / "symphony.wav").exists():
        run(sys.executable, "audio/music.py")
    if force or not (SFX_DIR / "snap_back.wav").exists():
        run(sys.executable, "audio/sfx.py")
    run(sys.executable, "audio/mix.py")


def render():
    run(sys.executable, "-m", "anim.render")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def encode(target=TARGET_BYTES):
    OUT.mkdir(exist_ok=True)
    master, mix = BUILD / "video_master.mkv", BUILD / "mix.wav"
    dur = duration(master)
    # 1.5 % container overhead allowance
    video_kbps = int((target * 8 * 0.985 / dur - AUDIO_KBPS * 1000) / 1000)
    print(f"duration {dur:.2f}s -> video {video_kbps} kbps + audio {AUDIO_KBPS} kbps")
    common = ["-c:v", "libx264", "-preset", "veryslow", "-tune", "animation", "-profile:v", "high",
              "-level", "4.0", "-pix_fmt", "yuv420p", "-b:v", f"{video_kbps}k",
              "-maxrate", f"{int(video_kbps * 2.2)}k", "-bufsize", f"{int(video_kbps * 4)}k",
              "-g", "240", "-keyint_min", "24", "-x264-params", "aq-mode=3:aq-strength=0.9:psy-rd=0.8,0.0",
              "-r", "24"]
    log = str(BUILD / "x264pass")
    run("ffmpeg", "-y", "-loglevel", "error", "-i", master, *common, "-pass", "1", "-passlogfile", log,
        "-an", "-f", "mp4", "/dev/null")
    run("ffmpeg", "-y", "-loglevel", "error", "-i", master, "-i", mix, *common, "-pass", "2",
        "-passlogfile", log, "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-ar", "48000", "-ac", "2",
        "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-movflags", "+faststart",
        "-metadata", "title=If You Have Time", str(OUT_FILE))
    size = OUT_FILE.stat().st_size
    print(f"wrote {OUT_FILE} : {size/1e6:.2f} MB ({size/2**20:.2f} MiB)")
    return size


if __name__ == "__main__":
    args = set(sys.argv[1:])
    if "encode" in args:
        encode()
    elif "audio" in args:
        audio("--force" in args)
    else:
        audio("--force" in args)
        render()
        encode()
