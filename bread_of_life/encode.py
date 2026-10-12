"""Final encode: concat rendered segments + mix -> H.264/AAC MP4 under a size cap.

Two-pass x264 tuned for animation; the video bitrate is derived from the size
budget so the file lands just under the cap.
"""
import json
import os
import subprocess
import sys

from config import FPS, WORK

SEG = os.path.join(WORK, "segments")
MIX = os.path.join(WORK, "audio", "mix.wav")


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def encode(out_path, cap_bytes=14.6e6, audio_kbps=80, codec="h264"):
    concat = os.path.join(WORK, "video_lossless.mkv")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                    os.path.join(SEG, "list.txt"), "-c", "copy", concat], check=True)
    dur = probe_duration(concat)
    overhead = 0.012 * cap_bytes
    v_kbps = int(((cap_bytes - overhead) * 8 / dur - audio_kbps * 1000) / 1000)
    print(f"duration {dur:.2f}s -> video {v_kbps} kbps, audio {audio_kbps} kbps")
    passlog = os.path.join(WORK, "x264pass")
    if codec == "h264":
        vargs = ["-c:v", "libx264", "-preset", "veryslow", "-tune", "animation", "-profile:v", "high",
                 "-level:v", "4.0", "-pix_fmt", "yuv420p", "-b:v", f"{v_kbps}k",
                 "-maxrate", f"{int(v_kbps * 2.2)}k", "-bufsize", f"{int(v_kbps * 4)}k",
                 "-x264-params", "aq-mode=3:aq-strength=0.85:psy-rd=0.7,0.0:ref=6:bframes=8:keyint=240:min-keyint=24:deblock=1,1",
                 "-passlogfile", passlog]
    else:
        vargs = ["-c:v", "libx265", "-preset", "slow", "-pix_fmt", "yuv420p", "-b:v", f"{v_kbps}k", "-tag:v", "hvc1",
                 "-x265-params", f"pass=PASS:stats={passlog}.x265:aq-mode=3:keyint=240"]
    common = ["ffmpeg", "-y", "-loglevel", "error", "-i", concat]
    p1 = list(vargs)
    p2 = list(vargs)
    if codec == "h264":
        p1 += ["-pass", "1"]
        p2 += ["-pass", "2"]
    else:
        p1 = [a.replace("PASS", "1") for a in p1]
        p2 = [a.replace("PASS", "2") for a in p2]
    subprocess.run(common + p1 + ["-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(common[:-2] + ["-i", concat, "-i", MIX] + p2 +
                   ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", f"{audio_kbps}k", "-ac", "2", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart",
                    "-metadata", "title=The Bread of Life (John 6)", out_path], check=True)
    size = os.path.getsize(out_path)
    print(f"wrote {out_path}: {size / 1e6:.2f} MB ({size / 2**20:.2f} MiB)")
    return size


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "bread_of_life.mp4")
    codec = sys.argv[2] if len(sys.argv) > 2 else "h264"
    encode(out, codec=codec)
