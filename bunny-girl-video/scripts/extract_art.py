"""Pull each illustration out of the phone photos of the Kindle Create screen.

Steps per page: remove the screen moire, straighten the photo (perspective
warp), white-balance against the white page/toolbar, smooth the colour noise,
give the pencil colours a gentle lift and calm any ripple left in flat areas.

Usage: python extract_art.py   (writes art/*.png)
"""
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "source_pages")
OUT = os.path.join(ROOT, "art")

# quad   = TL, TR, BR, BL corners of the drawing in the photo (pixels)
# white  = a patch of the photo that is white on screen (x0, y0, x1, y1)
# moire  = "notch" (tile-wise spectral notch, for diagonal/drifting stripes)
#          or "blur" (narrow horizontal blur, for pixel-grid stripes)
# clahe  = local contrast clip limit to lift glare/haze (0 = off)
# flat   = even out the photo's vignette (dark corners) on white-paper pages
# nlm    = denoise strength, sharp = unsharp-mask amount
# calm   = (lo, hi, sigma) for smoothing ripple in flat areas
PAGES = {
    "park": dict(src="page2_wolfdog_invisible.jpg",
                 quad=[(803, 548), (1558, 556), (1558, 1930), (808, 1930)],
                 white=(100, 1680, 700, 1880), moire="notch", clahe=1.3, flat=True, nlm=16, sharp=0.3,
                 calm=(12, 40, 3.2)),
    "hug": dict(src="page3_hug.jpg",
                quad=[(780, 600), (1558, 606), (1558, 1722), (772, 1722)],
                white=(100, 1560, 600, 1700), moire="blur", clahe=0, flat=True, nlm=5, sharp=0.55),
    "poof": dict(src="page4_poof.jpg",
                 quad=[(752, 566), (1497, 565), (1477, 1592), (752, 1594)],
                 white=(100, 1250, 600, 1500), moire="blur", clahe=0, flat=False, nlm=5, sharp=0.55),
    "family": dict(src="page5_family.jpg",
                   quad=[(731, 537), (1558, 527), (1558, 1735), (712, 1735)],
                   white=(100, 1250, 600, 1600), moire="blur", clahe=1.2, flat=True, nlm=7, sharp=0.45),
    "the_end": dict(src="page6_the_end.jpg",
                    quad=[(85, 500), (1478, 525), (1438, 1595), (100, 1590)],
                    white=(500, 300, 1300, 440), moire="blur", clahe=0, flat=False, nlm=5, sharp=0.55),
}


def descreen(img, tile=192, r_min=0.06, thresh=0.9, strength=0.97):
    """Remove screen moire with a tile-wise notch filter.

    The stripes come from the monitor's pixel grid beating against the camera
    sensor, so they show up as sharp peaks in the spectrum. Their frequency
    drifts across the photo, so every overlapping tile finds and suppresses
    its own peaks (anything that stands out above the smoothed spectrum).
    """
    img = img.astype(np.float32)
    step = tile // 2
    pad = tile
    p = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REFLECT)
    H, W = p.shape[:2]
    out = np.zeros_like(p)
    wsum = np.zeros(p.shape[:2], np.float32)
    win = np.outer(np.hanning(tile), np.hanning(tile)).astype(np.float32)
    f = np.fft.fftshift(np.fft.fftfreq(tile))
    R = np.sqrt(f[:, None] ** 2 + f[None, :] ** 2)
    keep = (R < r_min) | (np.abs(f)[:, None] < 0.01) | (np.abs(f)[None, :] < 0.01)
    for y in range(0, H - tile + 1, step):
        for x in range(0, W - tile + 1, step):
            t = p[y:y + tile, x:x + tile]
            g = t.mean(2)
            F = np.fft.fftshift(np.fft.fft2((g - g.mean()) * win))
            mag = np.log1p(np.abs(F)).astype(np.float32)
            bg = cv2.GaussianBlur(mag, (0, 0), 4)
            m = ((mag - bg) > thresh) & ~keep
            m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
            m = cv2.GaussianBlur(m, (0, 0), 1.0)
            gain = np.fft.ifftshift(1 - strength * np.clip(m * 1.8, 0, 1))
            for c in range(3):
                tc = t[..., c]
                mu = tc.mean()
                rec = np.real(np.fft.ifft2(np.fft.fft2(tc - mu) * gain)) + mu
                out[y:y + tile, x:x + tile, c] += rec * win
            wsum[y:y + tile, x:x + tile] += win
    out /= np.maximum(wsum, 1e-6)[..., None]
    return np.clip(out[pad:-pad, pad:-pad], 0, 255)


def remove_moire(img, quad, **kw):
    """Descreen only the drawing's bounding box (plus margin) to save time."""
    q = np.array(quad)
    x0, y0 = np.maximum(q.min(0) - 40, 0)
    x1, y1 = np.minimum(q.max(0) + 40, [img.shape[1], img.shape[0]])
    out = img.astype(np.float32).copy()
    out[y0:y1, x0:x1] = descreen(img[y0:y1, x0:x1], **kw)
    return out


def blur_moire(img):
    # pixel-grid moire sits at ~0.45-0.5 cycles/px horizontally; a narrow
    # horizontal gaussian removes it and barely touches the soft drawing
    return cv2.GaussianBlur(img.astype(np.float32), (0, 0), sigmaX=1.15, sigmaY=0.6)


def smooth_flat(img, lo=8.0, hi=26.0, sigma=2.6):
    """Smooth leftover ripple in flat areas only; pencil lines stay sharp."""
    L = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32)
    L = cv2.GaussianBlur(L, (0, 0), 1.5)
    mag = cv2.magnitude(cv2.Sobel(L, cv2.CV_32F, 1, 0), cv2.Sobel(L, cv2.CV_32F, 0, 1))
    flat = np.clip((hi - mag) / (hi - lo), 0, 1)
    flat = cv2.erode(flat, np.ones((5, 5), np.uint8))
    flat = cv2.GaussianBlur(flat, (0, 0), 2.0)[..., None]
    soft = cv2.GaussianBlur(img.astype(np.float32), (0, 0), sigma)
    return np.clip(img * (1 - flat) + soft * flat, 0, 255).astype(np.uint8)


def flatfield(img, k=160, max_gain=1.6):
    """Even out the photo's vignette: divide lightness by a smooth estimate
    of the paper brightness (closing removes the darker drawing on top)."""
    lab = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0]
    small = cv2.resize(L, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k // 4, k // 4))
    env = cv2.GaussianBlur(cv2.morphologyEx(small, cv2.MORPH_CLOSE, ker), (0, 0), k / 10)
    env = cv2.resize(env, (L.shape[1], L.shape[0]), interpolation=cv2.INTER_CUBIC)
    gain = np.clip(np.percentile(env, 85) / np.maximum(env, 1), 1.0, max_gain)
    lab[..., 0] = np.clip(L * gain, 0, 255)
    return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)


def warp(img, quad):
    q = np.float32(quad)
    w = int(round((np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3])) / 2))
    h = int(round((np.linalg.norm(q[3] - q[0]) + np.linalg.norm(q[2] - q[1])) / 2))
    dst = np.float32([(0, 0), (w - 1, 0), (w - 1, h - 1), (0, h - 1)])
    M = cv2.getPerspectiveTransform(q, dst)
    return cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_REPLICATE)


def white_balance(img, ref_patch):
    ref = ref_patch.reshape(-1, 3).astype(np.float32)
    ref = np.median(ref, axis=0)
    gain = ref.mean() / np.maximum(ref, 1)
    return np.clip(img.astype(np.float32) * gain, 0, 255)


def tone(img, clahe=0, nlm=5, sharp=0.55):
    """Lift the washed-out screen photo: levels, chroma smoothing, saturation."""
    lab = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    L, a, b = cv2.split(lab)
    # levels on lightness: the brightest part of the drawing becomes paper white
    lo, hi = np.percentile(L, 0.7), np.percentile(L, 99.3)
    L = np.clip((L - lo) / max(hi - lo, 1) * 255, 0, 255)
    L = 255 * (L / 255) ** 1.12  # small gamma so pastel colours keep body
    L8 = L.astype(np.uint8)
    if clahe:  # lift glare first, then denoise what that lifts
        L8 = cv2.createCLAHE(clipLimit=clahe, tileGridSize=(3, 4)).apply(L8)
    L8 = cv2.fastNlMeansDenoising(L8, None, h=nlm, templateWindowSize=7, searchWindowSize=21)
    # colour noise / low-frequency moire lives in the chroma channels
    a = cv2.bilateralFilter(a, 9, 18, 7)
    b = cv2.bilateralFilter(b, 9, 18, 7)
    a = cv2.GaussianBlur(a, (0, 0), 1.4)
    b = cv2.GaussianBlur(b, (0, 0), 1.4)
    # saturation boost around neutral (128)
    a = np.clip((a - 128) * 1.45 + 128, 0, 255)
    b = np.clip((b - 128) * 1.45 + 128, 0, 255)
    out = cv2.cvtColor(cv2.merge([L8.astype(np.float32), a, b]).astype(np.uint8), cv2.COLOR_LAB2BGR)
    # unsharp mask to bring the pencil lines back
    blur = cv2.GaussianBlur(out, (0, 0), 2.2)
    return cv2.addWeighted(out, 1 + sharp, blur, -sharp, 0)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, p in PAGES.items():
        img = cv2.imread(os.path.join(SRC, p["src"]))
        x0, y0, x1, y1 = p["white"]
        ref = cv2.GaussianBlur(img, (0, 0), 3)[y0:y1, x0:x1]
        if p["moire"] == "notch":
            img = remove_moire(img, p["quad"])
        else:
            img = blur_moire(img)
        img = warp(img, p["quad"])
        img = white_balance(img, ref)
        if p["flat"]:
            img = flatfield(img)
        img = tone(img, p["clahe"], p["nlm"], p["sharp"])
        img = smooth_flat(img, *p.get("calm", (8, 26, 2.6)))
        cv2.imwrite(os.path.join(OUT, f"{name}.png"), img)
        print(name, img.shape[1], "x", img.shape[0])


if __name__ == "__main__":
    main()
