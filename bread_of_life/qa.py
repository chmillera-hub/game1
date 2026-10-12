"""Quick checks on the final MP4: size, streams, duration, first frame not dark."""
import json
import subprocess
import sys

import numpy as np


def main(path, cap=15e6):
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                                     capture_output=True, text=True, check=True).stdout)
    size = int(info["format"]["size"])
    dur = float(info["format"]["duration"])
    print(f"size: {size / 1e6:.2f} MB ({size / 2**20:.2f} MiB)  under cap: {size < cap}")
    print(f"duration: {dur:.2f}s  overall bitrate: {size * 8 / dur / 1000:.0f} kbps")
    for s in info["streams"]:
        if s["codec_type"] == "video":
            print(f"video: {s['codec_name']} {s.get('profile')} {s['width']}x{s['height']} {s['r_frame_rate']} {s.get('pix_fmt')} {int(s.get('bit_rate', 0)) // 1000} kbps")
        else:
            print(f"audio: {s['codec_name']} {s.get('sample_rate')} Hz {s.get('channels')} ch {int(s.get('bit_rate', 0)) // 1000} kbps")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    w = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    img = np.frombuffer(raw, np.uint8).reshape(w["height"], w["width"])
    print(f"first frame mean luma: {img.mean():.1f} (black would be ~16)")


if __name__ == "__main__":
    main(sys.argv[1])
