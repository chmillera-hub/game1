"""Detect hard cuts in the rendered master (play time) from frame-difference spikes.

    python3 tools/detect_cuts.py [out/master_video.mp4]   -> data/cuts_play.json

Frames are decoded at 90x160 greyscale; a cut is a frame whose mean absolute difference from the previous
frame is large in absolute terms and far above its neighbours (dissolves and camera moves are gradual).
"""
import json, os, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out/master_video.mp4")
    w, h = 90, 160
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", src, "-vf", f"scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    d = np.concatenate([[0.0], np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))])
    cuts = []
    for i in range(1, len(d)):
        lo, hi = max(1, i - 6), min(len(d), i + 7)
        neigh = np.concatenate([d[lo:i], d[i + 1:hi]])
        base = np.median(neigh) if len(neigh) else 0
        if d[i] > 6.0 and d[i] > 4 * base + 2.0:
            cuts.append(round(i / 24.0, 4))
    json.dump({"fps": 24, "cuts": cuts}, open(os.path.join(ROOT, "data/cuts_play.json"), "w"))
    print(f"{len(cuts)} cuts detected in {len(d)} frames")


if __name__ == "__main__":
    main()
