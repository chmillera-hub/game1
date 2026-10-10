"""End-to-end build of "If You Have Time".

    python3 build.py              # everything that is missing, then mix + render + encode
    python3 build.py --force      # regenerate audio assets too
    python3 build.py encode       # only the final encode (needs build/video_master.mkv + build/mix.wav)
    python3 build.py audio        # tts/timeline/music/sfx/mix only

Final file: out/if_you_have_time.mp4 - H.264 High + AAC-LC, 720x1280 @ 24 fps, BT.709 (converted + tagged),
sized to TARGET_BYTES.
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


# The master is BT.601 limited range (anim/render.py pipes rgb24 into yuv444p with swscale's default matrix).
# Convert the matrix to BT.709 and tag it: untagged HD video is decoded as BT.709 by browsers/players, which shifts
# the teals by ~dE 10.  colormatrix is an exact integer matrix in YUV (no dither, no bias); the swscale
# scale=in_color_matrix=...:out_color_matrix=... route to yuv420p darkens Y/U/V by ~0.5 code and adds dither texture.
COLOR_VF = "colormatrix=bt601:bt709,format=yuv420p"
COLOR_TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
# Beats whose frame must start a new IDR.  The snap is a flash cut (overexposed frame between a dark and a normal
# shot); x264's flash handling codes it as P and puts the I-frame one frame late.  Ordinary hard cuts get IDRs from
# scenecut, and scene starts are NOT all cuts (S0->S1 fades from white, S3 opens on S2's held shot, S3->S4 is
# continuous), so they are deliberately not forced.
KEY_BEATS = ("snap",)


def forced_key_times():
    """'t1,t2,...' for -force_key_frames: ffmpeg keys the first frame with pts >= t, the same rule the scenes use
    (frame f shows time f/FPS, the new shot starts once t >= beat)."""
    try:
        beats = json.loads((BUILD / "timeline.json").read_text())["beats"]
    except (OSError, ValueError, KeyError):
        return ""
    return ",".join(f"{beats[b]:.4f}" for b in KEY_BEATS if b in beats)


def encode(target=TARGET_BYTES):
    OUT.mkdir(exist_ok=True)
    master, mix = BUILD / "video_master.mkv", BUILD / "mix.wav"
    dur = duration(master)
    # 1.5 % container overhead allowance
    video_kbps = int((target * 8 * 0.985 / dur - AUDIO_KBPS * 1000) / 1000)
    print(f"duration {dur:.2f}s -> video {video_kbps} kbps + audio {AUDIO_KBPS} kbps")
    keys = forced_key_times()
    # no VBV cap (a downloadable file; level 4.0 allows far more) and a 30 s keyint, so IDRs land on cuts (scenecut)
    # instead of pulsing mid-shot; aq/psy kept moderate so thin high-contrast detail (card text, faces) keeps its bits
    common = ["-c:v", "libx264", "-preset", "veryslow", "-tune", "animation", "-profile:v", "high",
              "-level", "4.0", "-vf", COLOR_VF, *COLOR_TAGS, "-b:v", f"{video_kbps}k",
              "-g", "720", "-keyint_min", "24", *(["-force_key_frames", keys] if keys else []),
              "-x264-params", "aq-mode=3:aq-strength=0.7:psy-rd=0.6,0.0",
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
