"""Cut the characters out of the cleaned drawings so they can move.

Writes (all in art/):
  cut_girl.png, cut_wolf_end.png, cut_duo.png  - from the_end.png (RGBA)
  cut_wolf_poof.png                             - from poof.png (RGBA)
  plate_end.png   - the_end.png with the characters and "THE END" painted out
  plate_poof.png  - poof.png with Wolf Dog painted out
  cutouts.json    - where each cutout sat in its drawing (to put it back)
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(os.path.dirname(HERE), "art")

ELL = lambda k: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))  # noqa: E731


def fill_holes(m):
    """Fill enclosed holes (flood from a 1px empty frame around the mask)."""
    ff = cv2.copyMakeBorder((m > 0).astype(np.uint8) * 255, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    h, w = ff.shape
    cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 255)
    return ((m > 0) | (ff[1:-1, 1:-1] == 0)).astype(np.uint8)


def flood_from_border(free):
    """Background = free pixels reachable from the image border."""
    h, w = free.shape
    work = free.astype(np.uint8) * 255
    mask = np.zeros((h + 2, w + 2), np.uint8)
    for x in range(0, w, 6):
        for y in (2, h - 3):
            if work[y, x] == 255:
                cv2.floodFill(work, mask, (x, y), 128, flags=8)
    for y in range(0, h, 6):
        for x in (2, w - 3):
            if work[y, x] == 255:
                cv2.floodFill(work, mask, (x, y), 128, flags=8)
    return work == 128


def components_at(mask, points):
    """Keep the connected pieces of `mask` that contain any of `points`."""
    _, lab, _, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    out = np.zeros(mask.shape, np.uint8)
    for x, y in points:
        if lab[y, x] > 0:
            out[lab == lab[y, x]] = 1
    return out


def drop_small(mask, min_area):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    big = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= min_area]
    return np.isin(lab, big).astype(np.uint8)


def end_masks(im):
    """Bunny Girl and Wolf Dog on the lavender 'THE END' page."""
    h, w = im.shape[:2]
    L = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2LAB)[..., 0], (0, 0), 1.0)
    # pencil lines: thin dark strokes stand out in a black-hat transform
    lines = cv2.morphologyEx(L, cv2.MORPH_BLACKHAT, ELL(17)) > 22
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    teal = (hsv[..., 0] > 70) & (hsv[..., 0] < 105) & (hsv[..., 1] > 60)
    walls = cv2.morphologyEx((lines | teal).astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    def segment(k):
        bg = flood_from_border(cv2.dilate(walls, ELL(k)) == 0)
        keep = components_at(~bg, [(470, 640), (470, 450), (835, 455), (860, 650)])
        # pull the wall-dilation margin back to the drawn outline
        margin = (keep > 0) & (cv2.erode(keep, ELL(k + 2)) == 0)
        near = cv2.dilate(walls, ELL(5)) > 0
        keep[margin & ~near] = 0
        keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, ELL(5))
        return fill_holes(drop_small(keep, 1500))

    # Where the hands meet: her hand and the teal pom-pom are hers, the grey
    # paw below them is his.
    yy, xx = np.mgrid[0:h, 0:w]
    hers = (xx >= 688) | ((xx > 620) & (yy < 547))
    girl = components_at(segment(5) * hers, [(835, 455)])
    # Wolf Dog's fur is drawn as separate spikes, so close the gaps between
    # them to get his whole body.
    wolf_strokes = segment(13) * ~hers
    wolf = fill_holes(cv2.morphologyEx(wolf_strokes, cv2.MORPH_CLOSE, ELL(45)))
    wolf = components_at(wolf * ~hers, [(470, 640)])
    return girl.astype(np.uint8), wolf.astype(np.uint8)


def poof_mask(im):
    """Wolf Dog on the green POOF page: a simple green key."""
    b, g, r = [im[..., i].astype(np.int32) for i in range(3)]
    fg = ((g - np.maximum(r, b)) < 14).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return fill_holes(components_at(fg, [(380, 700)]))


def despill_green(rgba):
    b, g, r = [rgba[..., i].astype(np.float32) for i in range(3)]
    limit = np.maximum(r, b) + 6
    rgba[..., 1] = np.minimum(g, limit).astype(np.uint8)
    return rgba


def soft_alpha(mask, sigma=1.1):
    a = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma)
    return np.clip(a * 1.15, 0, 1)


def save_cut(name, im, mask, pad=6, despill=False):
    ys, xs = np.where(mask > 0)
    x0, y0 = max(xs.min() - pad, 0), max(ys.min() - pad, 0)
    x1, y1 = min(xs.max() + pad + 1, im.shape[1]), min(ys.max() + pad + 1, im.shape[0])
    rgba = np.dstack([im, (soft_alpha(mask) * 255).astype(np.uint8)])[y0:y1, x0:x1].copy()
    if despill:
        rgba = despill_green(rgba)
    cv2.imwrite(os.path.join(ART, name), rgba)
    return dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))


def paint_out(im, hole, sigmas=(12, 40, 120), grain=3.0, smooth_all=False):
    """Fill `hole` from the surrounding colours (multi-scale normalised blur).

    With smooth_all the whole image is replaced by the smooth estimate, which
    also irons out leftover screen ripple.
    """
    keep = (hole == 0).astype(np.float32)
    src = im.astype(np.float32)
    fill = None
    for s in sigmas[::-1]:
        num = cv2.GaussianBlur(src * keep[..., None], (0, 0), s)
        den = cv2.GaussianBlur(keep, (0, 0), s)[..., None]
        est = num / np.maximum(den, 1e-6)
        if fill is None:
            fill = est
        else:
            a = np.clip(den / 0.25, 0, 1)
            fill = a * est + (1 - a) * fill
    # a little paper grain so the filled area doesn't look plastic
    rng = np.random.default_rng(7)
    noise = cv2.GaussianBlur(rng.normal(0, grain, im.shape[:2]).astype(np.float32), (0, 0), 0.8)
    fill += noise[..., None]
    if smooth_all:
        return np.clip(fill, 0, 255).astype(np.uint8)
    a = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 2.5)[..., None]
    return np.clip(src * (1 - a) + fill * a, 0, 255).astype(np.uint8)


def smooth_sky(im, exclude, grain=2.0):
    """Fit a gentle quadratic colour gradient to the sky pixels (robustly)."""
    h, w = exclude.shape
    L = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2LAB)[..., 0], (0, 0), 1.0)
    lines = cv2.morphologyEx(L, cv2.MORPH_BLACKHAT, ELL(17)) > 15
    ok = (cv2.dilate(exclude, ELL(31)) == 0) & ~lines
    ys, xs = np.where(ok)
    sel = np.random.default_rng(3).choice(len(ys), min(60000, len(ys)), replace=False)
    ys, xs = ys[sel], xs[sel]

    def basis(x, y):
        x, y = x / w - 0.5, y / h - 0.5
        return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], -1)

    A = basis(xs.astype(np.float32), ys.astype(np.float32))
    vals = cv2.medianBlur(im, 7)[ys, xs].astype(np.float32)
    wts = np.ones(len(ys), np.float32)
    for _ in range(4):  # reweight away from outliers (stray marks, shading)
        coef, *_ = np.linalg.lstsq(A * wts[:, None], vals * wts[:, None], rcond=None)
        err = np.linalg.norm(vals - A @ coef, axis=1)
        wts = 1.0 / np.maximum(1.0, err / (1.5 * np.median(err) + 1e-6))
    gy, gx = np.mgrid[0:h, 0:w].astype(np.float32)
    sky = basis(gx, gy) @ coef
    # the photo darkens toward the bottom corners; keep the sky pastel
    lab = cv2.cvtColor(np.clip(sky, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    floor = np.percentile(lab[..., 0], 70)
    lab[..., 0] = np.maximum(lab[..., 0], floor)
    # the darkest corner also drifts brown; pull its colour toward the median
    for c in (1, 2):
        med = np.median(lab[..., c])
        lab[..., c] = med + 0.6 * (lab[..., c] - med)
    sky = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    noise = np.random.default_rng(7).normal(0, grain, (h, w)).astype(np.float32)
    sky += cv2.GaussianBlur(noise, (0, 0), 0.8)[..., None]
    return np.clip(sky, 0, 255)


def main():
    info = {}
    end = cv2.imread(os.path.join(ART, "the_end.png"))
    girl, wolf = end_masks(end)
    info["girl"] = save_cut("cut_girl.png", end, girl)
    info["wolf_end"] = save_cut("cut_wolf_end.png", end, wolf)
    info["duo"] = save_cut("cut_duo.png", end, girl | wolf)

    # plate: a smooth lavender sky (no screen ripple), with the original sun
    # and grass tufts pasted back on top
    hsv = cv2.cvtColor(end, cv2.COLOR_BGR2HSV)
    h, w = girl.shape
    yy, xx = np.mgrid[0:h, 0:w]
    sun = ((hsv[..., 1] > 70) & ((hsv[..., 0] < 40) | (hsv[..., 0] > 165)) & (xx < 720) & (yy < 440))
    sun = fill_holes(cv2.morphologyEx(sun.astype(np.uint8), cv2.MORPH_CLOSE, ELL(15)))
    sun = drop_small(sun, 5000)
    grass = (((hsv[..., 0] > 35) & (hsv[..., 0] < 105) & (hsv[..., 1] > 50))
             & (((xx > 30) & (xx < 190) & (yy > 660) & (yy < 880))
                | ((xx > 1040) & (xx < 1220) & (yy > 780) & (yy < 1020))))
    grass = cv2.dilate(grass.astype(np.uint8), ELL(5))
    not_sky = cv2.dilate(girl | wolf, ELL(25)) | cv2.dilate(sun, ELL(9)) | grass
    not_sky[915:1015, 340:910] = 1  # the hand-written THE END
    sky = smooth_sky(end, not_sky)
    keep = cv2.GaussianBlur((sun | grass).astype(np.float32), (0, 0), 1.2)[..., None]
    plate = np.clip(end * keep + sky * (1 - keep), 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(ART, "plate_end.png"), plate)

    poof = cv2.imread(os.path.join(ART, "poof.png"))
    pm = poof_mask(poof)
    info["wolf_poof"] = save_cut("cut_wolf_poof.png", poof, pm, despill=True)
    # paint out the wolf plus any stray spike tips just outside his mask
    Lp = cv2.cvtColor(poof, cv2.COLOR_BGR2LAB)[..., 0]
    hole = cv2.dilate(pm, ELL(25)) | ((Lp < 120) & (cv2.dilate(pm, ELL(61)) > 0))
    hole = cv2.dilate(hole.astype(np.uint8), ELL(7))
    cv2.imwrite(os.path.join(ART, "plate_poof.png"), paint_out(poof, hole, sigmas=(10, 30, 90)))

    with open(os.path.join(ART, "cutouts.json"), "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps(info))


if __name__ == "__main__":
    main()
