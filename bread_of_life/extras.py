"""Crowd extras: randomized variants of the main rig, pre-rendered as sprites."""
import numpy as np
import skia

import chars
import hair
from gfx import mix
from limbs import make_arms
from rig import Character

SKINS = [("#e8b38c", "#c88763", "#a8694c"), ("#d39a6e", "#b0744f", "#8e5a3d"), ("#c88a60", "#a26a45", "#7f5034"),
         ("#efc29e", "#d0906c", "#ad6e50"), ("#b97c55", "#925c3c", "#704329")]
CLOTH = ["#8a6744", "#6f8197", "#5d6140", "#9a4f3c", "#b59a6a", "#4f5a6e", "#7a5a6a", "#c9b48a", "#6a4a3a", "#8c8c7a"]
HAIRS = [("#2a1d15", "#150e09", "#5a4636"), ("#3d2516", "#24150c", "#7a5236"), ("#1b1512", "#0c0806", "#463a32"),
         ("#8e8880", "#5f5a54", "#d0ccc4")]


def make_extra(seed, female=None):
    rng = np.random.default_rng(seed)
    female = rng.uniform() < 0.4 if female is None else female
    base = dict(chars.MIRIAM_ST if female else chars.JESUS_ST)
    sk = SKINS[rng.integers(len(SKINS))]
    base.update(skin=sk[0], skin_sh=sk[1], skin_sh2=sk[2])
    hc = HAIRS[rng.integers(3 if female else 4)]
    base.update(hair=hc[0], hair_sh=hc[1], hair_hl=hc[2], beard=hc[0], beard_sh=hc[1], brow_col=hc[0])
    cl = CLOTH[rng.integers(len(CLOTH))]
    cl_sh = "#" + "".join(f"{int(c * 255 * 0.72):02x}" for c in mix(cl, cl, 0)[:3])
    head = CLOTH[rng.integers(len(CLOTH))]
    head_sh = "#" + "".join(f"{int(c * 255 * 0.75):02x}" for c in mix(head, head, 0)[:3])
    base.update(cloth=head, cloth_sh=head_sh)
    base["eye_h"] = base["eye_h"] * rng.uniform(0.85, 1.05)
    base["mouth_w"] = base["mouth_w"] * rng.uniform(0.9, 1.1)
    kw = {}
    kind = rng.integers(3)
    if female or kind == 0:
        kw["headwear_back"] = hair.HeadCloth(layer="back", vol=0.2, flare=0.6)
        kw["headwear_front"] = hair.HeadCloth(layer="front", vol=0.2, flare=0.6, hair_fringe=female)
    elif kind == 1:
        kw["headwear_front"] = hair.ShortCurly()
        kw["ears"] = True
    else:
        kw["headwear_back"] = hair.LongHair(layer="back", tip_y=1.6, y_hang=0.3)
        kw["headwear_front"] = hair.LongHair(layer="front", tip_y=1.5, y_hang=0.3)
    if not female:
        grey = 0.6 if hc[0] == "#8e8880" else 0.0
        kw["beard"] = hair.Beard(vol=0.04, chin=rng.uniform(0.06, 0.25), grey=grey)
    neck = "round" if rng.uniform() < 0.6 else "v"
    kw["outfit"] = chars.tunic_outfit(cl, cl_sh, neckline=neck)
    kw["arms"] = make_arms({-1: dict(sleeve=cl, sleeve_sh=cl_sh), 1: dict(sleeve=cl, sleeve_sh=cl_sh)})
    return Character(f"extra{seed}", base, **kw)


_sprites = {}


def sprite(seed, yaw=-15, S=40, expr=None, blur=0.0, female=None, tint=None):
    """Pre-rendered extra: returns (image, anchor_x, anchor_y) where anchor is the neck base."""
    key = (seed, yaw, S, tuple(sorted((expr or {}).items())), blur, female, tint)
    if key in _sprites:
        return _sprites[key]
    ch = make_extra(seed, female)
    w, h = int(S * 5.2), int(S * 9.6)
    surf = skia.Surface(w, h)
    cv = surf.getCanvas()
    cv.clear(skia.ColorTRANSPARENT)
    P = dict(yaw=yaw, **(expr or {}))
    ax, ay = w / 2, S * 4.0
    ch.draw(cv, P, ax, ay, S)
    if tint is not None:
        p = skia.Paint()
        p.setColorFilter(skia.ColorFilters.Blend(skia.Color4f(*tint).toColor(), skia.BlendMode.kSrcATop))
        cv.drawPaint(p)
    img = surf.makeImageSnapshot()
    if blur > 0:
        s2 = skia.Surface(w, h)
        c2 = s2.getCanvas()
        c2.clear(skia.ColorTRANSPARENT)
        p = skia.Paint()
        p.setImageFilter(skia.ImageFilters.Blur(blur, blur, skia.TileMode.kDecal))
        c2.drawImage(img, 0, 0, skia.SamplingOptions(), p)
        img = s2.makeImageSnapshot()
    _sprites[key] = (img, ax, ay)
    return _sprites[key]


def draw_sprite(cv, spr, x, y, scale=1.0, alpha=1.0):
    img, ax, ay = spr
    cv.save()
    cv.translate(x, y)
    cv.scale(scale, scale)
    p = skia.Paint()
    p.setAlphaf(alpha)
    cv.drawImage(img, -ax, -ay, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    cv.restore()
