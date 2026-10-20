"""Depth masks for parallax (Depth Anything V2 Small).

For every still in BASE_DIR, writes OUT_DIR/<name>_mid.png and <name>_near.png:
white images whose alpha is how near each pixel is (feathered), used by
fantasy/render.js to zoom the nearer parts of a still a little faster than the
rest during a push-in.

Usage: python depth.py BASE_DIR OUT_DIR [name ...]
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

MODEL = "/opt/real/models/depth-small"
torch.set_num_threads(2)


def smoothstep(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def main():
    base, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[3:])
    proc = AutoImageProcessor.from_pretrained(MODEL)
    model = AutoModelForDepthEstimation.from_pretrained(MODEL).eval()
    for p in sorted(base.glob("*.jpg")):
        name = p.stem
        if (only and name not in only) or (out / f"{name}_near.png").exists():
            continue
        img = Image.open(p).convert("RGB")
        with torch.no_grad():
            pred = model(**proc(images=img, return_tensors="pt")).predicted_depth   # relative inverse depth: larger is nearer
        d = cv2.resize(pred[0].numpy(), img.size, interpolation=cv2.INTER_CUBIC)
        lo, hi = np.percentile(d, 2), np.percentile(d, 98)
        d = np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1)
        for suffix, (a, b) in (("mid", (0.40, 0.56)), ("near", (0.62, 0.80))):
            alpha = cv2.GaussianBlur(smoothstep(a, b, d).astype(np.float32), (0, 0), 3.0)
            rgba = np.dstack([np.full(d.shape + (3,), 255, np.uint8), (alpha * 255).astype(np.uint8)])
            Image.fromarray(rgba, "RGBA").save(out / f"{name}_{suffix}.png", optimize=True)
        print(f"{name:18s} near {float((d > 0.7).mean()):.2f}", flush=True)


if __name__ == "__main__":
    main()
