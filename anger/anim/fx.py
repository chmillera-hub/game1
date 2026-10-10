"""Effects for "ANGER": title, torch flame, dust, debris, sparks, splash/steam, drips, saliva, specks,
dazed vision and camera shake (BIBLE sections 3, 4, 7).

Coordinates: unless marked SCREEN space, functions draw in whatever space the canvas is in -- normally
STAGE units under the scene's Camera.  SCREEN-space functions reset the matrix themselves.
Everything is stateless (a pure function of its arguments and t / age), so frames render in any order.

Light / darkness: sets, dust, debris, splash, steam, drips and saliva are "lit" things -- draw them
BEFORE light.apply_darkness so the torch / fungi light them.  The torch flame, sparks, embers and the
title are EMISSIVE -- draw them AFTER apply_darkness.

Public API
  SCREEN space
    draw_title(canvas, t, text="ANGER", alpha=1.0, cy=None, size=None, tracking=None, glow=1.0,
               embers=1.0, cx=W/2)
        Heavy wide-tracked caps (Inter Display Black) filled with a hot-metal gradient, a deep
        ember-orange glow that breathes, a few embers drifting up.  cy = baseline (default 0.70*H).
        Rendered once per (text, size, tracking) into cached images -> ~2 ms per frame.
    flash(canvas, amount, color="#FFE7C2")                     full-frame flash (src-over)
    blur_vision(canvas, amount, t=0.0)                          dazed / doubled vision (S4) ~6-8 ms
        Soft blur (2x2x downsample + blur), a drifting ghost double image and darker blurry edges.
  STAGE (or any) space
    draw_torch_flame(canvas, x, y, t, scale=1.0, angle=0.0, wind=(0, 0), intensity=1.0, seed=0,
                     embers=1.0, glow=1.0)
        (x, y) = flame base (top of the torch head).  Flame ~125*scale units tall.  angle = torch tilt
        in degrees (0 = upright, + = clockwise): only the base follows it, the plume always rises.
        wind = air velocity relative to the flame (stage units/s), e.g. -torch velocity while it flies:
        the plume leans/streams that way and stretches.  intensity 0..1 shrinks/dims (dying flame).
    draw_torch(canvas, x, y, t, angle=0.0, scale=1.0, lit=1.0, wind=(0, 0), seed=0)
        The whole torch prop (wooden handle + wrapped pitch head + flame if lit>0) centred on (x, y),
        rotated by angle (deg, 0 = head up).  For the torch tumbling through the air / floating.
        torch_head(x, y, angle, scale) -> (hx, hy) = flame base of such a torch.
    dust_cloud(canvas, t, x, y, age, size=1.0, seed=0, n=14, color="#8E7E6C", alpha=0.85, life=3.2,
               spread=1.0, drift=(0, -14), ground=True)
        Billowing puffs from (x, y), age seconds after the event; ground=True spreads them sideways.
    dust_fall(canvas, t, x0, x1, y, amount=1.0, seed=0, length=260, color="#9A8A76")
        Thin trickles of dust/grit falling from the edge [x0, x1] at height y (ledge, door arch).
    debris(canvas, t, age, origin, seed=0, kind="stone"|"wood"|"mix", n=12, speed=800, direction=-90,
           spread=140, gravity=2600, floor_y=None, size=1.0, spin=1.0, toward=0.0, alpha=1.0, life=None)
        Chunks flying ballistically from origin (age seconds after the event); direction in degrees
        (-90 = up, 0 = right), spread = fan width in degrees; floor_y lands/settles them;
        toward > 0 grows them over time (flying at the camera).
    sparks(canvas, t, x, y, rate=120, direction=-90, spread=40, speed=750, life=0.5, gravity=1500,
           size=1.0, seed=0, alpha=1.0, drift=(0, 0), t0=None, t1=None)
        Continuous stream of hot sparks (streaks cooling white -> yellow -> orange -> red).
        drift = velocity of the air/world in the canvas frame (e.g. (0, -fall_speed) while the camera
        follows a falling Anger), so old sparks get carried.  t0/t1: emission window (absolute t).
    ember_burst(canvas, t, x, y, age, n=16, seed=0, size=1.0)           one-off burst of embers
    splash(canvas, t, x, y, age, size=1.0, seed=0, rings=True, clip=None)
        Water splash: central jet + crown, droplets, ripple rings (ellipses on the surface, optionally
        clipped to `clip` path).  steam(...) for the hiss.
    steam(canvas, t, x, y, age, amount=1.0, size=1.0, seed=0, life=2.8, emit=1.8)
    ripples(canvas, x, y, age, size=1.0, n=3, clip=None, alpha=1.0, squash=0.22)
    drips(canvas, t, x, y, period=2.6, seed=0, fall=320, size=1.0, color="water_hi", splash=True,
          phase=0.0)
        A drop swells at (x, y), lets go, falls `fall` units, tiny splash.  drip_times(t0, t1, period,
        seed, phase, fall) -> impact times (for SFX).
    saliva_drop(canvas, x, y, size=1.0, stretch=0.0, alpha=1.0, color="m_drool", detached=False)
        Glossy viscous drop hanging from (x, y); stretch 0 bead .. 1 long string about to snap.
        detached=True draws a falling teardrop centred at (x, y).
    crunch_specks(canvas, t, x, y, age, seed=0, n=9, size=1.0, direction=-60)
        Little bone-white chips and crumbs popping out of the dark (crunching).
  helpers
    shake_offset(t, events, freq=13.0, seed=0) -> (dx, dy, drot)
        events = [(t0, amp, dur), ...]: decaying noise shake (amp stage units, ends at t0+dur).
    camera_shake(cam, t, events, freq=13.0, seed=0, rot=True) -> Camera   copy of cam with the shake.

Performance: soft things are cached sprite blits; streaks/polygons are tiny vector draws.  Flame
~1-2 ms, 70-spark stream ~2 ms, dust cloud ~1 ms, title ~2 ms.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from anim.core import (Camera, clamp, col, ease_out, font, hash01, lerp, noise1, rgb, smooth_path,
                       smoothstep)
from config import H, W

TAU = math.tau
_LIN = skia.SamplingOptions(skia.FilterMode.kLinear)
_LINM = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
_NEAR = skia.SamplingOptions()


# =========================================================================== helpers
def _rgb(c):
    if isinstance(c, str):
        return rgb(c)
    if isinstance(c, int):
        return (skia.ColorGetR(c), skia.ColorGetG(c), skia.ColorGetB(c))
    return (int(c[0]), int(c[1]), int(c[2]))


def _hex(c) -> str:
    r, g, b = _rgb(c)
    return f"#{r:02X}{g:02X}{b:02X}"


def _c(c, a=1.0):
    r, g, b = _rgb(c)
    return skia.Color(r, g, b, int(255 * clamp(a)))


def _mix(a, b, t):
    a, b = _rgb(a), _rgb(b)
    t = clamp(t)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _P(color, a=1.0, add=False, blur=0.0):
    p = skia.Paint(AntiAlias=True)
    p.setColor(_c(color, a))
    if add:
        p.setBlendMode(skia.BlendMode.kPlus)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def _S(color, w, a=1.0, add=False, cap="round"):
    p = _P(color, a, add)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(w)
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def _G(shader, a=1.0, add=False, blur=0.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(shader)
    p.setAlphaf(clamp(a))
    if add:
        p.setBlendMode(skia.BlendMode.kPlus)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def _poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def _img(arr_rgba01: np.ndarray) -> skia.Image:
    """float (h, w, 4) premultiplied 0..1 -> skia Image (BGRA native)."""
    a8 = np.clip(arr_rgba01 * 255.0 + 0.5, 0, 255).astype(np.uint8)
    out = np.empty_like(a8)
    out[..., 0], out[..., 1], out[..., 2], out[..., 3] = a8[..., 2], a8[..., 1], a8[..., 0], a8[..., 3]
    return skia.Image.fromarray(np.ascontiguousarray(out), colorType=skia.kBGRA_8888_ColorType,
                                alphaType=skia.kPremul_AlphaType)


@lru_cache(maxsize=256)
def _sprite(color: str, kind: str = "soft", add: bool = False) -> skia.Image:
    """Radial sprite. add=True -> premultiplied with alpha 0 (src-over composites it additively)."""
    n = 96
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx - (n - 1) / 2) ** 2 + (yy - (n - 1) / 2) ** 2) / (n / 2)
    edge = np.clip(1 - d * d, 0, 1) ** 1.5
    if kind == "soft":
        prof = np.exp(-d * d * 4.0) * edge
    elif kind == "core":
        prof = (np.exp(-d * d * 40.0) * 0.7 + np.exp(-d * d * 7.0) * 0.3 + np.exp(-d * d * 2.5) * 0.12) * edge
    elif kind == "puff":       # dust / steam puff: soft but body-like
        tt = np.clip((1.0 - d) / 0.95, 0, 1)
        prof = tt * tt * (3 - 2 * tt)
        prof = prof ** 1.6
    elif kind == "wide":
        prof = np.clip(1 - d, 0, 1) ** 2.0
    elif kind == "cloud":      # soft puff, lit from above (2-tone baked into the colour below)
        tt = np.clip((1.0 - d) / 1.0, 0, 1)
        prof = (tt * tt * (3 - 2 * tt)) ** 1.8
    else:
        raise ValueError(kind)
    prof = np.clip(prof, 0, 1).astype(np.float32)
    c = np.array(_rgb(color), np.float32) / 255.0
    a = np.zeros_like(prof) if add else prof
    if kind == "cloud":        # lighter top, darker bottom
        v = (yy / (n - 1))[..., None]
        shade = 1.18 - 0.42 * v
        rgbf = np.clip(c[None, None, :] * shade, 0, 1) * prof[..., None]
        return _img(np.dstack([rgbf, a]))
    return _img(np.dstack([c[None, None, :] * prof[..., None], a]))


def _blob(canvas, x, y, r, color, alpha=1.0, kind="soft", add=False, ry=None, angle=0.0):
    if alpha <= 0.004 or r <= 0.05:
        return
    p = skia.Paint()
    p.setAlphaf(clamp(alpha))
    ry = r if ry is None else ry
    img = _sprite(_hex(color), kind, add)
    if angle:
        canvas.save()
        canvas.translate(x, y)
        canvas.rotate(angle)
        canvas.drawImageRect(img, skia.Rect(-r, -ry, r, ry), _LIN, p)
        canvas.restore()
    else:
        canvas.drawImageRect(img, skia.Rect(x - r, y - ry, x + r, y + ry), _LIN, p)


def _mscale(canvas) -> float:
    m = canvas.getTotalMatrix()
    return math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY())) or 1.0


def _h(i, k, seed):
    return hash01(i * 7919 + k * 104729, seed)


# =========================================================================== SCREEN: title, flash
_TITLE_FAMILY = "Inter Display"


@lru_cache(maxsize=8)
def _title_layers(text, size, tracking):
    """(glow_img, letters_img, iw, ih, pad, baseline, width) rendered once per (text, size, tracking)."""
    f = font(size, _TITLE_FAMILY, 900)
    widths = [f.measureText(ch) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    pad = int(size * 1.3)
    iw, ih = int(total + 2 * pad), int(size * 1.0 + 2 * pad)
    base = pad + size * 0.86            # baseline inside the image
    path = skia.Path()
    xx = pad
    for ch, w_ in zip(text, widths):
        gp = f.getPath(f.textToGlyphs(ch)[0])
        if gp is not None:
            gp.offset(xx, base)
            path.addPath(gp)
        xx += w_ + tracking
    cap_top = base - size * 0.73
    # --- glow: soft, wide, low (additive: premul rgb with alpha 0)
    gs = skia.Surface(iw, ih)
    gc = gs.getCanvas()
    gc.clear(skia.ColorTRANSPARENT)
    gc.drawPath(path, _P("#C83A10", 0.30, blur=size * 0.42))
    gc.drawPath(path, _P("#FF6A20", 0.22, blur=size * 0.16))
    gc.drawPath(path, _P("#FFA040", 0.16, blur=size * 0.05))
    arr = gs.makeImageSnapshot().toarray(colorType=skia.kBGRA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    arr[..., 3] = 0
    glow = skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kBGRA_8888_ColorType,
                                alphaType=skia.kPremul_AlphaType)
    # --- letters: hot-metal face (pale gold top -> ember bottom), thin dark edge, soft inner shade
    ls = skia.Surface(iw, ih)
    lc = ls.getCanvas()
    lc.clear(skia.ColorTRANSPARENT)
    lc.drawPath(path, _S("#2A0C04", size * 0.035, 0.9))
    sh = skia.GradientShader.MakeLinear([(0, cap_top), (0, base)],
                                        [_c("#FFEBC8"), _c("#FFC872"), _c("#F2862E"), _c("#C2400F")],
                                        [0.0, 0.38, 0.75, 1.0])
    lc.drawPath(path, _G(sh))
    lc.save()
    lc.clipPath(path, skia.ClipOp.kIntersect, True)
    inner = skia.Path(path)
    inner.offset(0, -size * 0.05)
    lc.drawPath(inner, _S("#7A1E06", size * 0.06, 0.35, cap="round"))
    lc.restore()
    letters = ls.makeImageSnapshot()
    return glow, letters, iw, ih, pad, base, total


def draw_title(canvas, t, text="ANGER", alpha=1.0, cy=None, size=None, tracking=None, glow=1.0, embers=1.0,
               cx=W / 2):
    """SCREEN space: heavy wide-tracked caps with an ember-orange glow (see module doc)."""
    if alpha <= 0.003:
        return
    txt = text.upper()
    if size is None:
        size = 118.0 if len(txt) <= 6 else max(40.0, 118.0 * 6 / len(txt))
    tr = size * 0.30 if tracking is None else tracking
    f = font(size, _TITLE_FAMILY, 900)
    total = sum(f.measureText(ch) for ch in txt) + tr * (len(txt) - 1)
    if total > W - 70:                      # fit the portrait frame
        k = (W - 70) / total
        size, tr = size * k, tr * k
    size, tr = round(size, 1), round(tr, 1)
    cy = H * 0.70 if cy is None else cy
    gimg, limg, iw, ih, pad, base, total = _title_layers(txt, size, tr)
    a = clamp(alpha)
    canvas.save()
    canvas.resetMatrix()
    x0 = cx - total / 2 - pad
    y0 = cy - base
    # breathing, flickering glow (smooth, slow)
    br = 0.86 + 0.10 * noise1(t * 1.3, 5) + 0.04 * noise1(t * 4.1, 9)
    # glow grows in slightly before the letters are solid
    ga = clamp(glow * br * smoothstep(a * 1.4))
    if ga > 0.003:
        pg = skia.Paint()
        pg.setAlphaf(ga)
        sc = 1.0 + 0.04 * (1.0 - a)
        canvas.drawImageRect(gimg, skia.Rect(cx - iw * sc / 2, y0 - ih * (sc - 1) / 2,
                                             cx + iw * sc / 2, y0 + ih * (1 + (sc - 1) / 2)), _LIN, pg)
    pl = skia.Paint()
    pl.setAlphaf(clamp(a * a * (3 - 2 * a)))
    canvas.drawImage(limg, x0, y0, _LIN, pl)
    # embers drifting up through the title
    if embers > 0:
        n = 14
        for i in range(n):
            per = 2.6 + 1.6 * _h(i, 1, 41)
            ph = (t / per + _h(i, 2, 41)) % 1.0
            ex = cx + (_h(i, 3, 41) - 0.5) * total * 1.15 + 18 * math.sin(t * 1.3 + i) * ph
            ey = cy + size * 0.35 - ph * size * 1.9
            ea = a * embers * math.sin(math.pi * ph) ** 1.5 * (0.5 + 0.5 * _h(i, 4, 41))
            er = 1.2 + 1.6 * _h(i, 5, 41)
            colr = _mix("#FFE2A0", "#FF5A1E", ph)
            _blob(canvas, ex, ey, er * 5, colr, ea * 0.45, kind="soft", add=True)
            canvas.drawCircle(ex, ey, er, _P(colr, ea))
    canvas.restore()


def flash(canvas, amount, color="#FFE7C2"):
    """SCREEN space full-frame flash (src-over, amount 0..1)."""
    if amount <= 0.002:
        return
    canvas.save()
    canvas.resetMatrix()
    canvas.drawRect(skia.Rect(0, 0, W, H), _P(color, clamp(amount)))
    canvas.restore()


# =========================================================================== torch flame
def torch_head(x, y, angle=0.0, scale=1.0):
    """Flame base of a torch prop drawn by draw_torch at (x, y) (its centre) with this angle."""
    a = math.radians(angle)
    L = 92.0 * scale
    return x + math.sin(a) * L, y - math.cos(a) * L


def _flame_outline(bx, by, ux, uy, Hh, Wd, t, seed, sway=1.0, n=9):
    """Closed teardrop outline around a swaying spine from the base (bx,by) along unit (ux,uy)."""
    px, py = -uy, ux                      # perpendicular
    left, right, spine = [], [], []
    for i in range(n):
        s = i / (n - 1)
        sw = (noise1(t * 6.0 - s * 2.2, seed) * 0.55 + noise1(t * 11.0 - s * 3.5, seed + 3) * 0.3) * Wd * 0.55 * sway * s ** 1.2
        cxs = bx + ux * Hh * s + px * sw
        cys = by + uy * Hh * s + py * sw
        w = Wd * 0.5 * (math.sin(math.pi * min(1.0, 0.18 + s * 0.95)) ** 0.75) * (1.0 - s) ** 0.45
        w *= 1.0 + 0.10 * noise1(t * 9.0 + s * 3.0, seed + 7)
        spine.append((cxs, cys))
        left.append((cxs - px * w, cys - py * w))
        right.append((cxs + px * w, cys + py * w))
    # rounded bottom below the base
    r0 = Wd * 0.42
    bottom = [(bx - ux * r0 * 0.55 + px * r0 * 0.55, by - uy * r0 * 0.55 + py * r0 * 0.55),
              (bx - ux * r0 * 0.75, by - uy * r0 * 0.75),
              (bx - ux * r0 * 0.55 - px * r0 * 0.55, by - uy * r0 * 0.55 - py * r0 * 0.55)]
    pts = left[:-1] + [spine[-1]] + right[-2::-1] + bottom
    return smooth_path(pts, closed=True, tension=0.5), spine


def draw_torch_flame(canvas, x, y, t, scale=1.0, angle=0.0, wind=(0.0, 0.0), intensity=1.0, seed=0, embers=1.0,
                     glow=1.0):
    """Emissive layered flame; (x, y) = flame base. See module doc."""
    k = clamp(intensity, 0.0, 1.5)
    if k <= 0.01 or scale <= 0:
        return
    s = scale * (0.35 + 0.65 * min(k, 1.0))
    wx, wy = wind
    wl = math.hypot(wx, wy)
    # plume direction: buoyancy up + wind
    dx, dy = wx / 420.0, -1.0 + wy / 420.0
    dl = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dl, dy / dl
    flick = 1.0 + 0.10 * noise1(t * 7.5, seed + 1) + 0.06 * noise1(t * 15.0, seed + 2)
    Hh = 125.0 * s * flick * (1.0 + min(wl, 1500.0) / 1300.0)
    Wd = 52.0 * s * (1.0 - 0.25 * min(wl, 1500.0) / 1500.0)
    blur = max(0.6, 2.4 * s)
    # base follows the torch angle a little (the head is tilted)
    a = math.radians(angle)
    bx, by = x - math.sin(a) * 4 * s, y + math.cos(a) * 6 * s
    # ---- big soft glow (additive)
    if glow > 0:
        gx, gy = bx + ux * Hh * 0.35, by + uy * Hh * 0.35
        _blob(canvas, gx, gy, Hh * 2.3, "#FF7A2A", 0.22 * glow * k * flick, kind="soft", add=True)
        _blob(canvas, gx, gy, Hh * 0.95, "#FFB04A", 0.30 * glow * k * flick, kind="soft", add=True)
    # ---- outer flame
    path, spine = _flame_outline(bx, by, ux, uy, Hh, Wd, t, seed)
    tipx, tipy = spine[-1]
    sh = skia.GradientShader.MakeLinear([(bx, by), (tipx, tipy)],
                                        [_c("#FF7A26", 0.95 * k), _c("#FF5418", 0.85 * k), _c("#C8280C", 0.0)],
                                        [0.0, 0.55, 1.0])
    canvas.drawPath(path, _G(sh, 1.0, add=True, blur=blur))
    # ---- tongues that lick up and detach
    for j in range(3):
        per = 0.42 + 0.18 * hash01(j, seed + 11)
        cyc = math.floor((t + j * 0.137) / per)
        ph = ((t + j * 0.137) / per) % 1.0
        side = (j - 1) * 0.45 + (hash01(cyc, seed + j) - 0.5) * 0.3
        h0 = Hh * (0.45 + 0.35 * hash01(cyc, seed + 20 + j))
        lift = smoothstep((ph - 0.45) / 0.55) * Hh * 0.45
        th = h0 * (1.0 - 0.6 * smoothstep((ph - 0.5) / 0.5))
        tw = Wd * (0.38 - 0.18 * ph)
        tb = 0.18 * Hh + lift
        ox = bx + ux * tb + (-uy) * side * Wd * 0.5
        oy = by + uy * tb + ux * side * Wd * 0.5
        ta = k * 0.75 * math.sin(math.pi * ph) ** 0.6
        if ta < 0.02 or th < 4:
            continue
        tp, tsp = _flame_outline(ox, oy, ux, uy, th, tw, t, seed + 30 + j, sway=1.3, n=7)
        sh_t = skia.GradientShader.MakeLinear([(ox, oy), tsp[-1]], [_c("#FFA040", ta), _c("#FF5A1C", 0.0)])
        canvas.drawPath(tp, _G(sh_t, 1.0, add=True, blur=blur * 0.8))
    # ---- mid flame
    p2, sp2 = _flame_outline(bx + ux * 4 * s, by + uy * 4 * s, ux, uy, Hh * 0.68, Wd * 0.66, t + 0.05, seed + 5,
                             sway=0.8)
    sh2 = skia.GradientShader.MakeLinear([(bx, by), sp2[-1]],
                                         [_c("#FFD27A", 0.95 * k), _c("#FFB347", 0.75 * k), _c("#FF8A30", 0.0)],
                                         [0.0, 0.5, 1.0])
    canvas.drawPath(p2, _G(sh2, 1.0, add=True, blur=blur * 0.7))
    # ---- core
    p3, sp3 = _flame_outline(bx + ux * 6 * s, by + uy * 6 * s, ux, uy, Hh * 0.36, Wd * 0.40, t + 0.1, seed + 9,
                             sway=0.5, n=7)
    sh3 = skia.GradientShader.MakeLinear([(bx, by), sp3[-1]], [_c("#FFFBEA", 0.95 * k), _c("#FFF2C0", 0.0)])
    canvas.drawPath(p3, _G(sh3, 1.0, add=True, blur=blur * 0.6))
    _blob(canvas, bx + ux * 10 * s, by + uy * 10 * s, 26 * s, "#FFF6DA", 0.55 * k, kind="soft", add=True)
    # ---- embers rising
    if embers > 0:
        rate = 7.0
        life = 1.3
        i1 = math.floor(t * rate)
        for i in range(i1 - int(life * rate) - 1, i1 + 1):
            t_b = i / rate + hash01(i, seed + 50) / rate
            age = t - t_b
            if age < 0 or age > life * (0.6 + 0.4 * hash01(i, seed + 51)):
                continue
            lf = age / life
            vx = (hash01(i, seed + 52) - 0.5) * 90 * s + wx * 0.5
            vy = -(140 + 120 * hash01(i, seed + 53)) * s + wy * 0.5
            ex = bx + ux * Hh * 0.5 + vx * age + math.sin(age * 7 + i) * 6 * s
            ey = by + uy * Hh * 0.5 + vy * age
            er = (1.1 + 1.2 * hash01(i, seed + 54)) * max(0.6, s)
            ea = embers * k * (1.0 - lf) ** 1.2
            cc = _mix("#FFE9A8", "#E8401A", lf)
            _blob(canvas, ex, ey, er * 4.5, cc, ea * 0.5, add=True)
            canvas.drawCircle(ex, ey, er, _P(cc, ea))


def draw_torch(canvas, x, y, t, angle=0.0, scale=1.0, lit=1.0, wind=(0.0, 0.0), seed=0, wet=0.0):
    """Torch prop centred on (x, y), angle deg (0 = head up). lit 0..1 flame strength; wet darkens."""
    s = scale
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(angle)
    # handle (tapered wood)
    hp = _poly([(-7 * s, 80 * s), (7 * s, 80 * s), (9 * s, -55 * s), (-9 * s, -55 * s)])
    canvas.drawPath(hp, _P(_mix("#5A3B22", "#2A1C12", wet), 1.0))
    canvas.drawPath(_poly([(-7 * s, 80 * s), (-2 * s, 80 * s), (-3 * s, -55 * s), (-9 * s, -55 * s)]),
                    _P("#7A5634", 0.55 * (1 - wet)))
    canvas.drawPath(hp, _S("#1A1008", 1.6 * s, 0.8))
    # wrapped, charred head
    head = smooth_path([(-15 * s, -50 * s), (-17 * s, -72 * s), (-13 * s, -92 * s), (0, -97 * s), (13 * s, -92 * s),
                        (17 * s, -72 * s), (15 * s, -50 * s), (0, -46 * s)], closed=True)
    canvas.drawPath(head, _P(_mix("#3A2A20", "#151010", 0.4 + 0.6 * wet)))
    for k in range(4):
        yy = -54 * s - k * 10 * s
        canvas.drawLine(-15 * s, yy, 15 * s, yy - 5 * s, _S("#6A4A30", 2.2 * s, 0.6 * (1 - wet)))
    canvas.drawPath(head, _S("#0E0A08", 1.6 * s, 0.9))
    if lit > 0.02:
        # hot glowing pitch at the top of the head
        _blob(canvas, 0, -88 * s, 18 * s, "#FF7A2A", 0.6 * lit, add=True)
    canvas.restore()
    if lit > 0.02:
        hx, hy = torch_head(x, y, angle, s)
        draw_torch_flame(canvas, hx, hy, t, scale=s, angle=angle, wind=wind, intensity=lit, seed=seed)


# =========================================================================== dust
def dust_cloud(canvas, t, x, y, age, size=1.0, seed=0, n=16, color="#8A8075", alpha=0.85, life=3.2, spread=1.0,
               drift=(0.0, -14.0), ground=True):
    """Billowing dust puffs (lit thing: draw before the darkness). See module doc."""
    if age is None or age < 0 or age > life:
        return
    fade = (1.0 - age / life) ** 1.6 * smoothstep(age / 0.06)
    for i in range(n):
        h1, h2, h3, h4 = (_h(i, k, seed) for k in range(4))
        if ground:
            side = -1 if i % 2 == 0 else 1
            ang = math.radians(-8 - 40 * h1) if side > 0 else math.radians(-172 + 40 * h1)
        else:
            ang = TAU * h1
        v0 = (240 + 560 * h2) * size * spread
        tau = 0.30 + 0.25 * h3
        dist = v0 * tau * (1.0 - math.exp(-age / tau))
        px = x + math.cos(ang) * dist + drift[0] * age
        py = y + math.sin(ang) * dist * (0.55 if ground else 1.0) + drift[1] * age * (0.6 + 0.8 * h4)
        r = size * (55 + 60 * h4) * (0.45 + 0.55 * (1.0 - math.exp(-age / 0.45))) + 32 * size * age * (0.6 + h3)
        a = alpha * fade * (0.45 + 0.35 * h2)
        _blob(canvas, px, py, r, color, a, kind="cloud", ry=r * (0.8 if ground else 1.0))


def dust_fall(canvas, t, x0, x1, y, amount=1.0, seed=0, length=260.0, color="#9A8A76", size=1.0):
    """Trickles of grit falling from the edge [x0, x1] at height y (continuous while amount > 0)."""
    if amount <= 0.01:
        return
    n = max(1, int(abs(x1 - x0) / 60 * amount) + 1)
    for i in range(n):
        sx = lerp(x0, x1, (i + 0.5) / n + (_h(i, 1, seed) - 0.5) * 0.6 / n)
        per = 0.9 + 0.6 * _h(i, 2, seed)
        on = 0.5 + 0.5 * noise1(t * 0.8 + i * 3.1, seed + 3)
        if on * amount < 0.25:
            continue
        for j in range(7):
            ph = (t / per + j / 7 + _h(i, 3, seed)) % 1.0
            py = y + ph * ph * length
            px = sx + (_h(j, i, seed) - 0.5) * 6 * size
            a = amount * on * (1 - ph) * 0.8
            canvas.drawCircle(px, py, (1.3 + 1.2 * _h(j, i + 7, seed)) * size, _P(color, a))
        # the thin stream
        canvas.drawLine(sx, y, sx, y + length * 0.35, _S(color, 1.2 * size, 0.18 * amount * on))


# =========================================================================== debris
def _chunk_shape(i, seed, kind, sz):
    if kind == "wood":
        L = sz * (2.2 + 3.0 * _h(i, 11, seed))
        w = sz * (0.45 + 0.35 * _h(i, 12, seed))
        j1, j2 = _h(i, 13, seed), _h(i, 14, seed)
        pts = [(-L / 2, -w / 2), (L / 2 - w * j1, -w / 2), (L / 2, -w * 0.1), (L / 2 - w * 0.6 * j2, w / 2),
               (-L / 2 + w * 0.4, w / 2), (-L / 2 - w * 0.5 * j2, w * 0.1)]
        return pts, L
    m = 6
    pts = []
    for k in range(m):
        a = TAU * k / m + (_h(i, 20 + k, seed) - 0.5) * 0.6
        r = sz * (0.65 + 0.45 * _h(i, 30 + k, seed))
        pts.append((math.cos(a) * r, math.sin(a) * r * 0.85))
    return pts, sz


def debris(canvas, t, age, origin, seed=0, kind="stone", n=12, speed=800.0, direction=-90.0, spread=140.0,
           gravity=2600.0, floor_y=None, size=1.0, spin=1.0, toward=0.0, alpha=1.0, life=None):
    """Ballistic chunks (stone / wood splinters). See module doc."""
    if age is None or age < 0:
        return
    if life is not None and age > life:
        return
    ox, oy = origin
    fa = 1.0 if life is None else clamp((life - age) / 0.4)
    for i in range(n):
        knd = kind if kind != "mix" else ("wood" if _h(i, 1, seed) < 0.5 else "stone")
        ang = math.radians(direction + (_h(i, 2, seed) - 0.5) * spread)
        v = speed * (0.35 + 0.75 * _h(i, 3, seed))
        vx, vy = math.cos(ang) * v, math.sin(ang) * v
        sz = size * ((7 + 15 * _h(i, 4, seed) ** 2) if knd == "stone" else (9 + 9 * _h(i, 4, seed)))
        w0 = (_h(i, 5, seed) - 0.5) * 900 * spin
        tt = age
        px = ox + vx * tt
        py = oy + vy * tt + 0.5 * gravity * tt * tt
        rot = _h(i, 6, seed) * 360 + w0 * tt
        if floor_y is not None:
            fy = floor_y + (_h(i, 7, seed) - 0.5) * 40 * size
            # landing time (y(t) = fy, descending branch)
            a_, b_, c_ = 0.5 * gravity, vy, oy - fy
            disc = b_ * b_ - 4 * a_ * c_
            if disc >= 0 and gravity > 0:
                tl = (-b_ + math.sqrt(disc)) / (2 * a_)
                if 0 < tl < age:
                    dt = age - tl
                    vxl = vx * 0.35
                    px = ox + vx * tl + vxl * 0.18 * (1 - math.exp(-dt / 0.18))
                    vb = abs(vy + gravity * tl) * 0.22
                    tb = 2 * vb / gravity
                    py = fy - (vb * dt - 0.5 * gravity * dt * dt if dt < tb else 0.0)
                    rot = _h(i, 6, seed) * 360 + w0 * tl + w0 * 0.15 * 0.2 * (1 - math.exp(-dt / 0.2))
        sc = 1.0 + toward * age
        pts, _ = _chunk_shape(i, seed, knd, sz * sc)
        canvas.save()
        canvas.translate(px, py)
        canvas.rotate(rot)
        path = _poly(pts)
        if knd == "wood":
            base = _mix("#6A4528", "#3A2414", _h(i, 8, seed))
            canvas.drawPath(path, _P(base, alpha * fa))
            L = max(abs(p[0]) for p in pts)
            canvas.drawLine(-L * 0.8, -sz * sc * 0.1, L * 0.7, -sz * sc * 0.05, _S("#2A180C", 1.2 * sc * size, 0.6 * alpha * fa))
            canvas.drawLine(-L * 0.6, -sz * sc * 0.22, L * 0.8, -sz * sc * 0.2, _S("#9A7048", 1.0 * sc * size, 0.5 * alpha * fa))
        else:
            base = _mix("#4E4856", "#2A2630", _h(i, 8, seed))
            canvas.drawPath(path, _P(base, alpha * fa))
            hl = [(p[0] * 0.7 - sz * sc * 0.12, p[1] * 0.7 - sz * sc * 0.15) for p in pts[2:5]] + [(0, 0)]
            canvas.drawPath(_poly(hl), _P("#7A7280", 0.55 * alpha * fa))
        canvas.drawPath(path, _S("#0E0C12", 1.0 * sc * size, 0.7 * alpha * fa))
        canvas.restore()


# =========================================================================== sparks / embers
def _spark_color(lf):
    if lf < 0.25:
        return _mix("#FFFBEA", "#FFE08A", lf / 0.25)
    if lf < 0.6:
        return _mix("#FFE08A", "#FF9A3A", (lf - 0.25) / 0.35)
    return _mix("#FF9A3A", "#C8300E", (lf - 0.6) / 0.4)


def sparks(canvas, t, x, y, rate=120.0, direction=-90.0, spread=40.0, speed=750.0, life=0.5, gravity=1500.0,
           size=1.0, seed=0, alpha=1.0, drift=(0.0, 0.0), t0=None, t1=None, glow=True):
    """A continuous stream of hot sparks from (x, y) (EMISSIVE). See module doc."""
    if rate <= 0 or alpha <= 0.003:
        return
    lmax = life * 1.3
    i0 = math.floor((t - lmax) * rate)
    i1 = math.floor(t * rate)
    sw = 2.6 * size
    for i in range(i0, i1 + 1):
        tb = (i + hash01(i, seed + 1)) / rate
        age = t - tb
        if age < 0:
            continue
        if t0 is not None and tb < t0:
            continue
        if t1 is not None and tb > t1:
            continue
        lf_i = life * (0.5 + 0.8 * hash01(i, seed + 2))
        if age > lf_i:
            continue
        ang = math.radians(direction + (hash01(i, seed + 3) - 0.5) * spread + (hash01(i, seed + 9) - 0.5) * spread * 0.6)
        v = speed * (0.45 + 0.85 * hash01(i, seed + 4))
        vx, vy = math.cos(ang) * v, math.sin(ang) * v
        drag = 0.9
        dist = (1 - math.exp(-age * drag)) / drag
        px = x + vx * dist + drift[0] * age
        py = y + vy * dist + 0.5 * gravity * age * age + drift[1] * age
        cvx = vx * math.exp(-age * drag) + drift[0]
        cvy = vy * math.exp(-age * drag) + gravity * age + drift[1]
        lf = age / lf_i
        ln = 0.035 * (1.0 - 0.5 * lf)
        qx, qy = px - cvx * ln, py - cvy * ln
        a = alpha * (1.0 - lf ** 2)
        cc = _spark_color(lf)
        canvas.drawLine(qx, qy, px, py, _S(cc, sw * (1.0 - 0.45 * lf), a, add=True))
    if glow:
        fl = 0.8 + 0.2 * noise1(t * 23.0, seed + 5)
        _blob(canvas, x, y, 60 * size, "#FFB050", 0.55 * alpha * fl, add=True)
        _blob(canvas, x, y, 16 * size, "#FFF6DA", 0.9 * alpha * fl, add=True)


def ember_burst(canvas, t, x, y, age, n=16, seed=0, size=1.0, speed=380.0, life=1.4):
    """One-off burst of embers (EMISSIVE)."""
    if age is None or age < 0 or age > life * 1.5:
        return
    for i in range(n):
        ang = TAU * _h(i, 1, seed)
        v = speed * (0.3 + 0.7 * _h(i, 2, seed)) * size
        lf_i = life * (0.5 + 0.7 * _h(i, 3, seed))
        if age > lf_i:
            continue
        tau = 0.5
        d = (1 - math.exp(-age / tau)) * tau
        px = x + math.cos(ang) * v * d
        py = y + math.sin(ang) * v * d - 60 * size * age * age
        lf = age / lf_i
        cc = _spark_color(0.2 + 0.8 * lf)
        r = (1.2 + 1.6 * _h(i, 4, seed)) * size
        _blob(canvas, px, py, r * 5, cc, 0.4 * (1 - lf), add=True)
        canvas.drawCircle(px, py, r, _P(cc, 1 - lf))


# =========================================================================== water
def ripples(canvas, x, y, age, size=1.0, n=3, clip=None, alpha=1.0, squash=0.22, speed=1.0,
            color="water_hi", life=3.0):
    """Expanding elliptical rings on a water surface (age seconds after the disturbance)."""
    if age is None or age < 0 or age > life + 0.6 * n:
        return
    if clip is not None:
        canvas.save()
        canvas.clipPath(clip, skia.ClipOp.kIntersect, True)
    for k in range(n):
        ak = age - k * 0.32
        if ak <= 0 or ak > life:
            continue
        rx = size * (14 + 230 * math.sqrt(ak * speed))
        ry = rx * squash
        a = alpha * (1 - ak / life) ** 1.4 * (0.9 - 0.2 * k)
        w = size * (3.2 - 1.6 * ak / life)
        r = skia.Rect(x - rx, y - ry, x + rx, y + ry)
        canvas.drawOval(r, _S(color, w, a * 0.7))
        r2 = skia.Rect(x - rx * 0.96, y - ry * 0.9 + w, x + rx * 0.96, y + ry * 0.9 + w)
        canvas.drawOval(r2, _S("#0A1820", w * 0.8, a * 0.5))
    if clip is not None:
        canvas.restore()


def splash(canvas, t, x, y, age, size=1.0, seed=0, rings=True, clip=None, color="water_hi"):
    """Splash on a water surface at (x, y) (lit thing). age = seconds since impact."""
    if age is None or age < 0 or age > 4.0:
        return
    s = size
    hi = "#CFEFF8"
    # central jet / column
    if age < 0.75:
        u = age / 0.75
        hgt = 170 * s * math.sin(math.pi * min(1.0, u * 1.15)) * (1 - 0.3 * u)
        wd = 22 * s * (1 + 0.6 * u)
        if hgt > 2:
            jp = smooth_path([(x - wd, y), (x - wd * 0.45, y - hgt * 0.55), (x - wd * 0.2, y - hgt),
                              (x + wd * 0.25, y - hgt * 0.98), (x + wd * 0.5, y - hgt * 0.5), (x + wd, y)], closed=True)
            canvas.drawPath(jp, _P(color, 0.75 * (1 - u)))
            canvas.drawPath(jp, _S(hi, 2.0 * s, 0.8 * (1 - u)))
            canvas.drawCircle(x - wd * 0.05, y - hgt - 6 * s, 7 * s * (1 - u * 0.5), _P(hi, 0.85 * (1 - u)))
    # crown petals
    if age < 0.5:
        u = age / 0.5
        cr = 40 * s + 110 * s * ease_out(u)
        chh = 70 * s * math.sin(math.pi * min(1.0, u * 1.1))
        for side in (-1, 1):
            pts = [(x + side * cr * 0.25, y), (x + side * cr * 0.7, y - chh * 0.8), (x + side * cr * 1.05, y - chh),
                   (x + side * cr * 1.0, y - chh * 0.55), (x + side * cr * 0.8, y)]
            pp = smooth_path(pts, closed=True)
            canvas.drawPath(pp, _P(color, 0.55 * (1 - u)))
            canvas.drawPath(pp, _S(hi, 1.6 * s, 0.7 * (1 - u)))
    # droplets
    g = 2200.0
    for i in range(20):
        ang = math.radians(-90 + (_h(i, 1, seed) - 0.5) * 130)
        v = (380 + 520 * _h(i, 2, seed)) * s
        vx, vy = math.cos(ang) * v, math.sin(ang) * v
        tl = 2 * -vy / g
        if age > tl:
            continue
        px = x + vx * age
        py = y + vy * age + 0.5 * g * age * age
        r = (2.2 + 3.5 * _h(i, 3, seed)) * s
        sp = math.hypot(vx, vy + g * age)
        canvas.save()
        canvas.translate(px, py)
        canvas.rotate(math.degrees(math.atan2(vy + g * age, vx)))
        stretch = 1 + min(1.6, sp / 600)
        canvas.drawOval(skia.Rect(-r * stretch, -r, r * stretch, r), _P(hi, 0.85))
        canvas.restore()
    if rings:
        ripples(canvas, x, y, age, size=s, n=3, clip=clip, color=color)


def steam(canvas, t, x, y, age, amount=1.0, size=1.0, seed=0, life=2.8, emit=1.8, rate=12.0):
    """Hissing steam: puffs emitted during [0, emit] s after the event, rising and spreading."""
    if age is None or age < 0 or age > emit + life or amount <= 0.01:
        return
    i1 = int(min(age, emit) * rate)
    for i in range(i1 + 1):
        tb = i / rate
        a_i = age - tb
        if a_i < 0 or a_i > life:
            continue
        lf = a_i / life
        vx = (_h(i, 1, seed) - 0.5) * 50 * size
        rise = (90 + 80 * _h(i, 2, seed)) * size
        px = x + (_h(i, 3, seed) - 0.5) * 60 * size + vx * a_i + math.sin(a_i * 2.2 + i) * 14 * size * lf
        py = y - rise * a_i - 10 * size
        r = size * (22 + 30 * _h(i, 4, seed)) * (0.5 + 1.6 * lf)
        strength = amount * (1 - tb / (emit + 0.3)) ** 0.7
        a = 0.32 * strength * smoothstep(a_i / 0.15) * (1 - lf) ** 1.3
        _blob(canvas, px, py, r, "#C9D3D8", a, kind="puff")


def drip_times(t0, t1, period=2.6, seed=0, phase=0.0, fall=320.0):
    """Absolute impact times of drips(...) with these parameters inside [t0, t1] (for SFX)."""
    g = 2000.0
    tf = math.sqrt(2 * fall / g)
    out = []
    k0 = math.floor((t0 - phase) / period) - 1
    k1 = math.floor((t1 - phase) / period) + 1
    for k in range(k0, k1 + 1):
        st = phase + k * period + (hash01(k, seed) - 0.5) * period * 0.3
        ti = st + period * 0.78 + tf
        if t0 <= ti <= t1:
            out.append(ti)
    return out


def drips(canvas, t, x, y, period=2.6, seed=0, fall=320.0, size=1.0, color="water_hi", splash=True, phase=0.0,
          alpha=1.0):
    """A drop forms at (x, y), falls `fall` units and splashes (lit thing)."""
    g = 2000.0
    tf = math.sqrt(2 * fall / g)
    k = math.floor((t - phase) / period)
    hi = "#D8F2FA"
    for kk in (k - 1, k):
        st = phase + kk * period + (hash01(kk, seed) - 0.5) * period * 0.3
        u = t - st
        grow = period * 0.78
        if u < 0:
            continue
        if u < grow:                            # swelling bead
            f = u / grow
            r = size * (1.5 + 4.5 * f ** 0.7)
            st_ = 1 + 0.7 * f ** 3
            canvas.drawOval(skia.Rect(x - r, y, x + r, y + r * 2 * st_), _P(color, 0.75 * alpha))
            canvas.drawCircle(x - r * 0.3, y + r * 0.7 * st_, r * 0.3, _P(hi, 0.8 * alpha))
        elif u < grow + tf:                     # falling
            ft = u - grow
            py = y + 0.5 * g * ft * ft
            r = size * 5.0
            sp = g * ft
            ln = r * (1.3 + min(3.0, sp / 500.0))
            canvas.drawOval(skia.Rect(x - r * 0.8, py - ln, x + r * 0.8, py + r), _P(color, 0.8 * alpha))
            canvas.drawCircle(x - r * 0.25, py - r * 0.1, r * 0.3, _P(hi, 0.9 * alpha))
        elif splash and u < grow + tf + 0.5:    # tiny splash at the bottom
            a_ = u - grow - tf
            yb = y + fall
            for j in range(5):
                ang = math.radians(-90 + (j - 2) * 30 + (hash01(j + kk * 5, seed) - 0.5) * 20)
                v = (120 + 90 * hash01(j + kk * 9, seed)) * size
                px = x + math.cos(ang) * v * a_
                py = yb + math.sin(ang) * v * a_ + 0.5 * g * a_ * a_
                if py <= yb + 2:
                    canvas.drawCircle(px, py, 1.8 * size, _P(hi, 0.85 * alpha * (1 - a_ / 0.5)))
            rr = size * (6 + 60 * a_)
            canvas.drawOval(skia.Rect(x - rr, yb - rr * 0.25, x + rr, yb + rr * 0.25),
                            _S(hi, 1.4 * size, 0.6 * alpha * (1 - a_ / 0.5)))


# =========================================================================== saliva / specks
def saliva_drop(canvas, x, y, size=1.0, stretch=0.0, alpha=1.0, color="m_drool", detached=False):
    """Glossy viscous drop hanging from (x, y) (lit thing). See module doc."""
    s = size
    st = clamp(stretch)
    hi = "#FFFFFF"
    edge = _mix(color, "#20302E", 0.55)
    if detached:
        r = 6.5 * s
        p = smooth_path([(x, y - r * 2.4), (x + r * 0.55, y - r * 0.9), (x + r, y + r * 0.1), (x + r * 0.6, y + r * 0.85),
                         (x, y + r), (x - r * 0.6, y + r * 0.85), (x - r, y + r * 0.1), (x - r * 0.55, y - r * 0.9)])
        canvas.drawPath(p, _P(color, 0.72 * alpha))
        canvas.drawPath(p, _S(edge, 1.1 * s, 0.6 * alpha))
        canvas.drawOval(skia.Rect(x - r * 0.55, y - r * 0.45, x - r * 0.1, y + r * 0.15), _P(hi, 0.85 * alpha))
        return
    wa = 6.0 * s * (1 - 0.3 * st)
    ln = s * (3 + 70 * st ** 1.3)
    wn = s * (4.6 * (1 - st) + 1.0)
    rb = s * (6.5 + 2.0 * st)
    cyb = y + ln + rb * 0.85
    pts = [(x - wa, y), (x - wn * 0.8, y + ln * 0.35), (x - wn * 0.5, y + ln), (x - rb * 0.85, cyb - rb * 0.35),
           (x - rb, cyb + rb * 0.15), (x - rb * 0.5, cyb + rb * 0.85), (x, cyb + rb), (x + rb * 0.5, cyb + rb * 0.85),
           (x + rb, cyb + rb * 0.15), (x + rb * 0.85, cyb - rb * 0.35), (x + wn * 0.5, y + ln), (x + wn * 0.8, y + ln * 0.35),
           (x + wa, y)]
    p = smooth_path(pts, closed=True, tension=0.45)
    canvas.drawPath(p, _P(color, 0.62 * alpha))
    sh = skia.GradientShader.MakeLinear([(x - rb, 0), (x + rb, 0)], [_c("#FFFFFF", 0.0), _c("#FFFFFF", 0.0),
                                                                       _c(edge, 0.35 * alpha)], [0, 0.55, 1])
    canvas.drawPath(p, _G(sh))
    canvas.drawPath(p, _S(edge, 1.0 * s, 0.55 * alpha))
    canvas.drawOval(skia.Rect(x - rb * 0.62, cyb - rb * 0.55, x - rb * 0.12, cyb + rb * 0.05), _P(hi, 0.9 * alpha))
    canvas.drawCircle(x + rb * 0.35, cyb + rb * 0.55, rb * 0.14, _P(hi, 0.6 * alpha))
    if st > 0.2:
        canvas.drawLine(x - wn * 0.15, y + 2 * s, x - wn * 0.15, y + ln, _S(hi, 0.9 * s, 0.5 * alpha * st))


def crunch_specks(canvas, t, x, y, age, seed=0, n=9, size=1.0, direction=-60.0, life=0.9):
    """Little bone-white chips and dark crumbs popping out (lit thing)."""
    if age is None or age < 0 or age > life:
        return
    g = 1800.0
    for i in range(n):
        ang = math.radians(direction + (_h(i, 1, seed) - 0.5) * 80)
        v = (220 + 260 * _h(i, 2, seed)) * size
        px = x + math.cos(ang) * v * age
        py = y + math.sin(ang) * v * age + 0.5 * g * age * age
        r = (2.0 + 3.0 * _h(i, 3, seed)) * size
        cc = "#E8E0CC" if _h(i, 4, seed) < 0.6 else "#5A3A2A"
        a = 1 - age / life
        canvas.save()
        canvas.translate(px, py)
        canvas.rotate(_h(i, 5, seed) * 360 + 700 * age)
        canvas.drawPath(_poly([(-r, -r * 0.5), (r * 0.8, -r * 0.7), (r, r * 0.4), (-r * 0.4, r * 0.7)]), _P(cc, a))
        canvas.restore()


# =========================================================================== SCREEN: dazed vision
_BV: dict = {}


def blur_vision(canvas, amount, t=0.0, ghost=1.0, edge=1.0):
    """SCREEN space dazed vision: soft blur + drifting double image + dark blurry edges. amount 0..1."""
    a = clamp(amount)
    if a <= 0.01:
        return
    surf = canvas.getSurface()
    if surf is None:
        return
    info = canvas.imageInfo()
    dw, dh = info.width(), info.height()
    key = (dw, dh)
    if key not in _BV:
        _BV[key] = (skia.Surface(dw // 2, dh // 2), skia.Surface(dw // 4, dh // 4), skia.Surface(dw // 8, dh // 8))
    s2, s4, s8 = _BV[key]
    snap = surf.makeImageSnapshot()
    s2.getCanvas().drawImageRect(snap, skia.Rect(0, 0, dw // 2, dh // 2), _LIN, skia.Paint())
    s4.getCanvas().drawImageRect(s2.makeImageSnapshot(), skia.Rect(0, 0, dw // 4, dh // 4), _LIN, skia.Paint())
    s8.getCanvas().drawImageRect(s4.makeImageSnapshot(), skia.Rect(0, 0, dw // 8, dh // 8), _LIN, skia.Paint())
    small = s8.makeImageSnapshot()
    canvas.save()
    canvas.resetMatrix()
    # ghost (double vision): the sharp frame offset, drifting slowly
    if ghost > 0:
        gx = (10 + 8 * noise1(t * 0.6, 3)) * a
        gy = 5 * noise1(t * 0.5, 7) * a
        pg = skia.Paint()
        pg.setAlphaf(0.38 * a * ghost)
        canvas.drawImage(snap, gx, gy, _LIN, pg)
    # overall soft blur
    pb = skia.Paint()
    pb.setAlphaf(0.62 * a)
    canvas.drawImageRect(small, skia.Rect(0, 0, dw, dh), _LIN, pb)
    canvas.restore()
    if edge > 0:
        from anim.light import vignette
        vignette(canvas, 0.75 * a * edge)


# =========================================================================== camera shake
def shake_offset(t, events, freq=13.0, seed=0):
    """(dx, dy, drot) of a decaying noise shake; events = [(t0, amp, dur), ...]."""
    dx = dy = dr = 0.0
    for ev in events or ():
        t0, amp, dur = ev[0], ev[1], ev[2]
        age = t - t0
        if 0 <= age < dur:
            k = amp * (1 - age / dur) ** 2 * smoothstep(age / 0.02)
            dx += noise1(t * freq, seed + 1) * k
            dy += noise1(t * freq * 1.1, seed + 2) * k * 1.15
            dr += noise1(t * freq * 0.7, seed + 3) * k * 0.035
    return dx, dy, dr


def camera_shake(cam, t, events, freq=13.0, seed=0, rot=True):
    """Copy of `cam` (anim.core.Camera) with the decaying shake applied."""
    dx, dy, dr = shake_offset(t, events, freq, seed)
    return Camera(cam.cx + dx, cam.cy + dy, cam.zoom, cam.rot + (dr if rot else 0.0), cam.shake)
