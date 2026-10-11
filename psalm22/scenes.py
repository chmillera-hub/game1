"""Every shot of the film.  render_frame(t) -> skia.Image (720x1280)."""
import math
import numpy as np
import skia
from rig import (P, lin, rad, smooth, poly, bez, qbez, tapered, mix, lerp, clamp, ease, hx,
                 Noise, Blinker, Saccade, draw_character, c4)
from characters import CAST, hand
import timeline as TL
from timeline import S, E, F, speech

W, H = 720, 1280
CH = {k: f() for k, f in CAST.items()}
NAMES = list(CH)
BLINK = {k: Blinker(i * 7 + 1, mean=3.4) for i, k in enumerate(NAMES)}
SAC = {k: Saccade(i * 11 + 3) for i, k in enumerate(NAMES)}
NZ = {k: Noise(i * 5 + 2) for i, k in enumerate(NAMES)}
VOICE = {'jesus': 'JESUS', 'mary': 'MARY', 'magdalene': 'MAGDALENE', 'john': 'JOHN',
         'centurion': 'CENTURION', 'mocker1': 'MOCKER1', 'mocker2': 'MOCKER2',
         'young': 'YOUNG', 'nana': 'NANA'}
LINEAR = skia.SamplingOptions(skia.FilterMode.kLinear)
FONT_T = skia.Typeface('Caladea', skia.FontStyle.Bold())
FONT_TI = skia.Typeface('Caladea', skia.FontStyle.Italic())
FONT_C = skia.Typeface('Inter', skia.FontStyle.Bold())
CAPTIONS_ON = True

# ------------------------------------------------------------- animation ---

def kf(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t < t1:
            return v0 + (v1 - v0) * ease((t - t0) / max(1e-6, t1 - t0))
    return keys[-1][1]


def kfd(t, keys):
    names = set()
    for _, d in keys:
        names |= set(d)
    out = {}
    for n in names:
        pts = [(tt, d[n]) for tt, d in keys if n in d]
        out[n] = kf(t, pts)
    return out


def live(name, t, base, gain=0.55, blink=True, br_rate=0.24, br_amp=1.0, sacc=1.0, nod=1.0, sway=1.0, mmax=1.0):
    st = dict(base)
    n = NZ[name]
    st['breath'] = st.get('breath', 0.0) + math.sin(2 * math.pi * br_rate * t) * br_amp
    st['roll'] = st.get('roll', 0.0) + n(t, 0.5) * 1.4 * sway
    st['yaw'] = st.get('yaw', 0.0) + n(t + 50, 0.4) * 0.025 * sway
    st['pitch'] = st.get('pitch', 0.0) + n(t + 90, 0.45) * 0.02 * sway
    sx, sy = SAC[name](t)
    st['gx'] = st.get('gx', 0.0) + sx * sacc
    st['gy'] = st.get('gy', 0.0) + sy * sacc
    if blink:
        b = BLINK[name](t)
        st['open_l'] = st.get('open_l', 1.0) * b
        st['open_r'] = st.get('open_r', 1.0) * b
    v = VOICE.get(name)
    if v:
        loud, bright = speech(v, t)
        if loud > 0.02:
            o = clamp(loud ** 0.8 * gain, 0, mmax)
            st['m_open'] = max(st.get('m_open', 0.0), o)
            st['m_wide'] = st.get('m_wide', 1.0) * (0.86 + 0.34 * clamp((bright - 0.12) * 2.6))
            st['m_round'] = max(st.get('m_round', 0.0), clamp(0.45 - bright * 2) * o * 1.3)
            l2, _ = speech(v, t - 0.12)
            st['pitch'] = st['pitch'] - 0.035 * nod * clamp(loud - l2, -0.5, 0.8)
            st['b_in'] = st.get('b_in', 0.0) + 0.14 * clamp(loud - 0.55) * nod
            st['b_out'] = st.get('b_out', 0.0) + 0.08 * clamp(loud - 0.55) * nod
    return st


def put(cv, name, x, y, s, st, t, design=None):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    draw_character(cv, design or CH[name], st, t)
    cv.restore()


def tears_track(t, starts, side, dur=2.6, life=7.0):
    out = []
    for t0 in starts:
        if t0 <= t < t0 + life:
            p = clamp((t - t0) / dur)
            a = 1.0 if t < t0 + life - 1.5 else clamp((t0 + life - t) / 1.5)
            out.append((side, ease(p), a))
    return tuple(out)

# --------------------------------------------------------------- palettes ---

PAL = {
    #           top        mid        horizon    sun        grade      ground
    'amber': ('#38445e', '#8c7470', '#e3a462', '#ffd9a0', '#f2dcc6', '#3a2c26'),
    'dark':  ('#06080e', '#121622', '#3e2420', '#7a2a1c', '#6a7090', '#0c0a0c'),
    'dusk':  ('#1a2034', '#5a3646', '#c2643a', '#ff9a5a', '#d8a890', '#1c1414'),
    'dawn':  ('#5a7cb0', '#c8a2a2', '#ffd290', '#fff0c0', '#ffe8d0', '#3a3428'),
    'night': ('#0a0e18', '#141c2a', '#1e2432', '#000000', '#c8b8a8', '#0e0c0c'),
}


def pal_mix(a, b, k):
    return tuple('#%02x%02x%02x' % tuple(int(v * 255) for v in mix(x, y, k)) for x, y in zip(PAL[a], PAL[b]))


def golgotha_pal(t):
    if t < S['N2']:
        return pal_mix('amber', 'dark', kf(t, [(0, 0.0), (S['N2'], 0.45)]))
    if t < E['X5'] + 2.0:
        return pal_mix('amber', 'dark', kf(t, [(S['N2'], 0.45), (E['N2'] + 1.0, 0.95)]))
    if t < S['N4'] - 0.4:
        return pal_mix('dark', 'dusk', kf(t, [(E['X5'] + 2.0, 0.0), (E['C1'] + 1.0, 0.45)]))
    if t < S['N8'] + 2:
        return pal_mix('dark', 'dusk', kf(t, [(S['N4'] - 0.4, 0.7), (E['N6'], 1.0)]))
    return pal_mix('dawn', 'dawn', 0)


def grade(cv, color, amount=1.0, rect=None):
    p = skia.Paint()
    p.setColor4f(c4(mix('#ffffff', color, amount)))
    p.setBlendMode(skia.BlendMode.kModulate)
    if rect:
        cv.drawRect(rect, p)
    else:
        cv.drawPaint(p)


def vignette(cv, strength=0.55, color='#000000'):
    cv.drawPaint(P(shader=rad((W / 2, H * 0.45), H * 0.72,
                               [(color, 0.0), (color, 0.0), (color, strength)], [0, 0.55, 1])))


def sky(cv, pal, y0=0, y1=None, hor=0.75):
    y1 = y1 or H
    top, mid, horc = pal[0], pal[1], pal[2]
    cv.drawRect(skia.Rect(0, y0, W, y1), P(shader=lin((0, y0), (0, y1), [(top, 1), (mid, 1), (horc, 1)], [0, hor * 0.6, hor])))


class Clouds:
    def __init__(self, seed, n=14):
        r = np.random.default_rng(seed)
        self.c = [(r.uniform(-200, 900), r.uniform(0, 1), r.uniform(60, 180), r.uniform(0.4, 1.0), r.uniform(4, 12))
                  for _ in range(n)]

    def draw(self, cv, t, y0, y1, color, alpha, speed=1.0, light=None):
        for x, v, rr, a, sp in self.c:
            xx = (x + t * sp * speed) % 1100 - 200
            yy = y0 + (y1 - y0) * v
            cv.drawOval(skia.Rect(xx - rr * 1.8, yy - rr * 0.55, xx + rr * 1.8, yy + rr * 0.55),
                        P(color, alpha * a, blur=rr * 0.35))
            if light:
                cv.drawOval(skia.Rect(xx - rr * 1.4, yy - rr * 0.6, xx + rr * 1.2, yy - rr * 0.1),
                            P(light, alpha * a * 0.35, blur=rr * 0.3))


CLOUDS = Clouds(4)
CLOUDS2 = Clouds(9, 10)

# ------------------------------------------------------------ low-res bg ---

_BG = skia.Surface(240, 427)


def soft_bg(cv, fn, *a):
    """Draw fn at 1/3 resolution and upscale: cheap depth-of-field."""
    c2 = _BG.getCanvas()
    c2.save()
    c2.scale(240 / W, 427 / H)
    fn(c2, *a)
    c2.restore()
    img = _BG.makeImageSnapshot()
    cv.drawImageRect(img, skia.Rect(0, 0, W, H), LINEAR)


def crowd_figs(cv, seed, n, y0, y1, color, sc=1.0, t=0.0, x0=-40, x1=760, turn=0.0):
    r = np.random.default_rng(seed)
    figs = sorted([(r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(0.8, 1.2), r.integers(0, 3)) for _ in range(n)],
                  key=lambda q: q[1])
    for x, y, s, kind in figs:
        s *= sc * (0.6 + 0.4 * (y - y0) / max(1, y1 - y0))
        sw = math.sin(t * 0.7 + x) * 1.5
        cv.save(); cv.translate(x + sw, y); cv.scale(s, s)
        body = smooth([(-16, 0), (-22, 30), (-26, 120), (26, 120), (22, 30), (16, 0), (0, -4)])
        cv.drawPath(body, P(color))
        hx_ = turn * 3
        if kind == 0:
            cv.drawPath(smooth([(-13 + hx_, -2), (-14 + hx_, -24), (0 + hx_, -34), (14 + hx_, -24), (13 + hx_, -2), (20, 20), (-20, 20)]), P(color))
        else:
            cv.drawCircle(hx_, -16, 11, P(color))
        cv.restore()

# -------------------------------------------------------------- the hill ---

def cross_fig(cv, x, y, s, color, head=0.0, lifted=0.0, body=True, rim=None):
    """Silhouette of a cross; body=True draws a crucified figure (no detail)."""
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    cv.drawRect(skia.Rect(-8, -10, 8, 420), P(color))
    cv.drawRect(skia.Rect(-110, 38, 110, 52), P(color))
    if rim:
        cv.drawRect(skia.Rect(-8, -10, -5, 420), P(rim, 0.35))
        cv.drawRect(skia.Rect(-110, 38, 110, 40), P(rim, 0.35))
    if body:
        hxo = lerp(4, 0, lifted) + head * 0
        hyo = lerp(8, -3, lifted)
        for sgn in (-1, 1):
            cv.drawPath(tapered([(sgn * 10, 64), (sgn * 50, 54), (sgn * 98, 44)], 10, 6), P(color))
        torso = smooth([(-12, 58), (12, 58), (14, 110), (10, 150), (-10, 150), (-14, 110)])
        cv.drawPath(torso, P(color))
        cv.drawPath(smooth([(-15, 140), (15, 140), (18, 172), (-18, 172)]), P(color))
        cv.drawPath(tapered([(-6, 165), (-8, 210), (-2, 250)], 10, 6), P(color))
        cv.drawPath(tapered([(6, 165), (8, 210), (2, 250)], 10, 6), P(color))
        cv.drawCircle(hxo, 46 + hyo, 12.5, P(color))
        cv.drawRect(skia.Rect(-14, 6, 14, 20), P(color))
    cv.restore()


def hill(cv, pal, t, shake=0.0):
    g = pal[5]
    p = smooth([(-120, 1400), (-60, 1000), (120, 880), (300, 812), (420, 808), (600, 860), (800, 960), (860, 1400)], True)
    cv.drawPath(p, P(g))
    cv.drawPath(smooth([(120, 880), (300, 812), (420, 808), (600, 860)], False), P(pal[2], 0.25, stroke=3, blur=2))


def city(cv, pal):
    c = mix(pal[1], pal[5], 0.45)
    cc = '#%02x%02x%02x' % tuple(int(v * 255) for v in c)
    pts = [(0, 880), (0, 842), (40, 842), (40, 820), (70, 820), (70, 842), (150, 842), (150, 812), (190, 812),
           (190, 790), (205, 790), (205, 812), (260, 812), (260, 846), (420, 846), (420, 830), (470, 830),
           (470, 846), (720, 850), (720, 900)]
    cv.drawPath(poly(pts), P(cc, 0.85))


def birds(cv, t, t0, color, n=14, seed=2):
    if t < t0:
        return
    r = np.random.default_rng(seed)
    for i in range(n):
        x0, y0 = r.uniform(250, 470), r.uniform(700, 820)
        vx, vy = r.uniform(-140, 140), r.uniform(-200, -90)
        dt = t - t0 - r.uniform(0, 0.4)
        if dt < 0:
            continue
        x, y = x0 + vx * dt, y0 + vy * dt + 20 * dt * dt
        flap = math.sin(dt * 16 + i) * 5
        s = 1 + dt * 0.4
        cv.drawPath(smooth([(x - 9 * s, y - flap), (x, y), (x + 9 * s, y - flap)], False), P(color, 0.9, stroke=2.2))


def foreground_three(cv, t, pal, sway=1.0, lean=0.0):
    """Mary, John and Magdalene seen from behind at the bottom of the frame."""
    dk = pal[5]
    figs = [(250, 1140, 1.05, '#1b2a4a', 'veil'), (390, 1110, 1.15, mix(dk, '#2a2018', 0.3), 'curly'),
            (520, 1150, 1.0, '#4a1c14', 'veil')]
    for i, (x, y, s, c, kind) in enumerate(figs):
        cc = c if isinstance(c, str) else '#%02x%02x%02x' % tuple(int(v * 255) for v in c)
        cv.save(); cv.translate(x + math.sin(t * 0.6 + i) * 2 * sway + (lean * 18 if i == 0 else lean * -10 if i == 1 else 0), y)
        cv.scale(s, s)
        cv.drawPath(smooth([(-70, 40), (-60, -10), (-30, -30), (30, -30), (60, -10), (70, 40), (90, 260), (-90, 260)]), P(cc))
        if kind == 'veil':
            cv.drawPath(smooth([(-40, -10), (-44, -70), (-20, -102), (20, -102), (44, -70), (40, -10), (60, 60), (-60, 60)]), P(cc))
            cv.drawPath(smooth([(-38, -60), (-20, -98), (20, -98)], False), P(pal[2], 0.25, stroke=2.5))
        else:
            cv.drawCircle(0, -66, 38, P(cc))
            for k in range(9):
                a = -2.8 + k * 0.33
                cv.drawCircle(math.cos(a) * 34, -66 + math.sin(a) * 34, 9, P(cc))
            cv.drawPath(smooth([(-30, -90), (0, -104), (30, -90)], False), P(pal[2], 0.25, stroke=2.5))
        cv.restore()


class Tree:
    """Deterministic branching tree that grows with g in [0,1]."""

    def __init__(self, seed=3):
        r = np.random.default_rng(seed)
        self.br = []

        def grow(x, y, ang, L, w, depth, t0):
            x2, y2 = x + math.cos(ang) * L, y + math.sin(ang) * L
            dur = 0.16 + 0.04 * depth
            self.br.append((x, y, x2, y2, w, t0, t0 + dur, depth))
            if depth >= 6:
                return
            k = 2 if depth > 1 else 3
            for i in range(k):
                da = (i - (k - 1) / 2) * r.uniform(0.45, 0.7) + r.normal(0, 0.12)
                grow(x2, y2, ang + da, L * r.uniform(0.68, 0.8), w * 0.68, depth + 1, t0 + dur * 0.85)
        grow(0, 0, -math.pi / 2, 120, 26, 0, 0.0)
        self.end = max(b[6] for b in self.br)
        self.leaves = [(b[2], b[3], r.uniform(14, 26), r.uniform(0, 1), b[6]) for b in self.br if b[7] >= 4]

    def draw(self, cv, x, y, s, g, pal, t):
        cv.save(); cv.translate(x, y); cv.scale(s, s)
        T = g * (self.end + 0.35)
        bark = '#3a2a1e'
        for (x0, y0, x1, y1, w, a, b, dp) in self.br:
            if T <= a:
                continue
            k = clamp((T - a) / (b - a))
            xe, ye = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
            sway = math.sin(t * 0.8 + dp) * dp * 0.6
            cv.drawPath(tapered([(x0, y0), ((x0 + xe) / 2 + sway * 0.5, (y0 + ye) / 2), (xe + sway, ye)],
                                w * min(1, 0.3 + T * 0.9), w * 0.7 * min(1, 0.3 + T * 0.9)), P(bark))
        for (lx, ly, rr, hue, tb) in self.leaves:
            k = clamp((T - tb) / 0.25)
            if k <= 0:
                continue
            sway = math.sin(t * 0.9 + lx * 0.05) * 3
            c = mix('#4f7a3a', '#86a85a', hue)
            col = '#%02x%02x%02x' % tuple(int(v * 255) for v in c)
            cv.drawCircle(lx + sway, ly, rr * k * 1.6, P(col, 0.92))
            cv.drawCircle(lx + sway - rr * 0.4, ly - rr * 0.5, rr * k * 0.8, P('#b8d488', 0.35))
        bloom = clamp((T - self.end * 0.95) / 0.3)
        if bloom > 0:
            for i, (lx, ly, rr, hue, tb) in enumerate(self.leaves):
                if i % 2:
                    continue
                sway = math.sin(t * 0.9 + lx * 0.05) * 3
                fx, fy = lx + sway + rr * 0.6 * math.cos(i), ly + rr * 0.6 * math.sin(i)
                cv.drawCircle(fx, fy, 14 * bloom, P('#ffd27a', 0.35 * bloom, blur=8))
                cv.drawCircle(fx, fy, 6.5 * bloom, P('#e8783a' if i % 4 else '#f0b040'))
                cv.drawCircle(fx - 2, fy - 2, 2 * bloom, P('#fff2c0', 0.8))
        cv.restore()


TREE = Tree()


def people_gather(cv, t, k, pal):
    """Silhouettes walking in and leaning on one another under the tree."""
    spots = [(-1, 250, 0), (1, 470, 0.15), (-1, 190, 0.3), (1, 540, 0.45), (-1, 310, 0.55), (1, 410, 0.7)]
    c = mix(pal[5], '#000000', 0.2)
    cc = '#%02x%02x%02x' % tuple(int(v * 255) for v in c)
    for i, (side, xt, delay) in enumerate(spots):
        kk = clamp((k - delay) / 0.45)
        if kk <= 0:
            continue
        x = lerp(-60 if side < 0 else 780, xt, ease(kk))
        y = 905 + (i % 3) * 14
        s = 0.62 + (i % 3) * 0.06
        bob = math.sin(kk * 18) * 3 * (1 - kk)
        lean = (1 if xt < 360 else -1) * 6 * ease(clamp((kk - 0.8) / 0.2))
        cv.save(); cv.translate(x, y + bob); cv.rotate(lean); cv.scale(s, s)
        cv.drawPath(smooth([(-18, 0), (-24, 40), (-28, 150), (28, 150), (24, 40), (18, 0), (0, -6)]), P(cc))
        cv.drawCircle(0, -20, 14, P(cc))
        cv.restore()


def golgotha(cv, t, sh):
    v = sh.variant
    lt = t - sh.start
    pal = golgotha_pal(t)
    if v in ('garden', 'tree'):
        pal = PAL['dawn']
    zoom, cx, cy = 1.0, 360, 700
    shake = 0.0
    if v == 'open':
        zoom = lerp(1.0, 1.12, ease(lt / (sh.end - sh.start)))
    elif v in ('dark', 'ninth'):
        zoom = 1.12 + 0.03 * ease(lt / 4)
    elif v == 'cry':
        zoom = 1.15
        shake = max(0.0, 1 - lt / 1.2) * 6
    elif v == 'quake':
        zoom = 1.12
        shake = 9 * max(0.0, 1 - lt / 1.1)
    elif v in ('dusk', 'dusk2'):
        span = TL.E['N6'] - TL.S['N4']
        zoom = lerp(1.15, 0.98, ease((t - TL.S['N4']) / span))
    elif v == 'garden':
        zoom = lerp(1.05, 1.1, lt / 5)
    elif v == 'tree':
        zoom = lerp(1.0, 1.12, ease(lt / (sh.end - sh.start)))
        cy = 720
    sky(cv, pal, 0, H, 0.66)
    # sun
    sun_x, sun_y = 520, 330
    if v in ('garden', 'tree'):
        sun_y = lerp(820, 640, ease(lt / 18 if v == 'tree' else lt / 30))
        sun_x = 560
    dark = 1.0 if pal[0] == PAL['dark'][0] else 0.0
    cv.drawCircle(sun_x, sun_y, 220, P(pal[3], 0.25, blur=60))
    cv.drawCircle(sun_x, sun_y, 34, P(pal[3], 0.85))
    CLOUDS.draw(cv, t, 80, 600, pal[0], 0.55, 1.0, light=pal[2])
    CLOUDS2.draw(cv, t * 1.3, 300, 760, pal[1], 0.4, 1.0)
    cv.save()
    sx = (math.sin(t * 53) + math.sin(t * 31)) * shake
    sy = (math.cos(t * 47) + math.sin(t * 29)) * shake
    cv.translate(W / 2 + sx, cy + sy)
    cv.scale(zoom, zoom)
    cv.translate(-cx, -cy)
    city(cv, pal)
    rim = pal[2]
    silh = mix(pal[5], '#000000', 0.35)
    sc = '#%02x%02x%02x' % tuple(int(q * 255) for q in silh)
    hill(cv, pal, t)
    bodies = v not in ('garden', 'tree', 'dusk', 'dusk2')
    lifted = 0.0
    if v == 'cry':
        lifted = 1.0
    cross_fig(cv, 165, 560, 0.72, sc, body=bodies, rim=rim)
    cross_fig(cv, 560, 560, 0.72, sc, body=bodies, rim=rim)
    if v in ('garden', 'tree') or not bodies:
        cross_fig(cv, 360, 470, 1.0, sc, body=False, rim=rim)
    else:
        cross_fig(cv, 360, 470, 1.0, sc, body=True, lifted=lifted, rim=rim)
        cv.drawRect(skia.Rect(343, 478, 377, 492), P('#d8ccb0', 0.5))
    if v == 'cry':
        birds(cv, t, sh.start - 0.4, sc)
    elif v == 'ninth':
        pass
    # crowd
    if v in ('open', 'dark', 'ninth', 'cry', 'quake'):
        n = 26 if v == 'open' else 16
        turn = 1.0 if v == 'cry' else 0.0
        crowd_figs(cv, 7, n, 900, 1010, sc, 0.9, t, turn=turn)
    if v in ('dusk', 'dusk2'):
        # the centurion alone, helmet in hand, and the three
        cv.save(); cv.translate(560, 930); cv.scale(0.8, 0.8)
        cv.drawPath(smooth([(-18, 0), (-24, 40), (-28, 150), (28, 150), (24, 40), (18, 0), (0, -6)]), P(sc))
        cv.drawCircle(0, -20, 14, P(sc))
        cv.drawLine(40, -120, 34, 150, P(sc, stroke=3))
        cv.restore()
    if v == 'garden':
        garden_fg(cv, t, pal, 0.0)
    if v == 'tree':
        g = clamp(lt / 11.5)
        garden_fg(cv, t, pal, 0.0)
        TREE.draw(cv, 360, 850, 1.38 * (0.45 + 0.55 * g), g, pal, t)
        people_gather(cv, t, clamp((lt - 8.0) / 8.0), pal)
    if v not in ('garden', 'tree'):
        lean = 0.0
        if v == 'dark':
            lean = 1.0
        foreground_three(cv, t, pal, lean=lean)
    cv.restore()
    if v == 'cry':
        fl = max(0.0, 1 - (t - sh.start) / 0.35)
        if fl > 0:
            cv.drawPaint(P('#d8e0ff', 0.45 * fl))
    if v in ('garden', 'tree'):
        cv.drawCircle(sun_x, sun_y, 500, P('#fff0c0', 0.12, blur=80))
    vignette(cv, 0.5 if v not in ('garden', 'tree') else 0.3)
    if v == 'open':
        title_card(cv, t)


def garden_fg(cv, t, pal, k):
    r = np.random.default_rng(12)
    cv.drawPath(smooth([(-100, 1400), (-50, 1010), (200, 960), (360, 950), (520, 962), (780, 1010), (820, 1400)]), P('#3e5a30'))
    cv.drawPath(smooth([(-100, 1400), (-50, 1060), (200, 1020), (360, 1012), (520, 1024), (780, 1060), (820, 1400)]), P('#4a6a36'))
    for i in range(70):
        x, y = r.uniform(-10, 730), r.uniform(980, 1280)
        sway = math.sin(t * 1.3 + x * 0.05) * 3
        hgt = r.uniform(16, 40) * (0.7 + (y - 980) / 300)
        cv.drawLine(x, y, x + sway, y - hgt, P('#5d8040', 0.9, stroke=2.4))
        if i % 3 == 0:
            col = ['#f2e6c8', '#e89a8a', '#f4d06a', '#c8a8e0'][i % 4]
            cv.drawCircle(x + sway, y - hgt, 4.5 + (y - 980) / 60, P(col))
            cv.drawCircle(x + sway, y - hgt, 1.8, P('#f0c040'))

# ---------------------------------------------------------- level / up bg ---

def bg_level(c2, t, pal, crowd=True, horizon=780):
    sky(c2, pal, 0, H, horizon / H)
    c2.drawCircle(560, 300, 260, P(pal[3], 0.25, blur=60))
    CLOUDS.draw(c2, t, 100, horizon - 120, pal[0], 0.5, 1.0, light=pal[2])
    city(c2, pal) if False else None
    c2.drawRect(skia.Rect(0, horizon, W, H), P(pal[5]))
    c2.drawRect(skia.Rect(0, horizon - 6, W, horizon + 10), P(pal[2], 0.3, blur=6))
    if crowd:
        silh = mix(pal[5], '#000000', 0.2)
        sc = '#%02x%02x%02x' % tuple(int(q * 255) for q in silh)
        crowd_figs(c2, 21, 10, horizon + 20, horizon + 160, sc, 1.6, t)


def bg_up(c2, t, pal):
    sky(c2, pal, 0, H, 1.0)
    c2.drawCircle(150, 250, 240, P(pal[3], 0.3, blur=60))
    CLOUDS.draw(c2, t * 1.4, 0, 1200, pal[0], 0.55, 1.0, light=pal[2])
    CLOUDS2.draw(c2, t * 1.8, 200, 1300, pal[1], 0.45, 1.0)


def wood(cv, rect, base='#4a3626', dark='#2a1c12'):
    cv.drawRect(rect, P(base))
    x0, y0, x1, y1 = rect.left(), rect.top(), rect.right(), rect.bottom()
    horiz = (x1 - x0) > (y1 - y0)
    r = np.random.default_rng(int(x0 + y0) % 1000)
    for i in range(14):
        if horiz:
            y = r.uniform(y0, y1)
            cv.drawLine(x0, y, x1, y + r.uniform(-4, 4), P(dark, 0.5, stroke=r.uniform(1, 2.5)))
        else:
            x = r.uniform(x0, x1)
            cv.drawLine(x, y0, x + r.uniform(-4, 4), y1, P(dark, 0.5, stroke=r.uniform(1, 2.5)))
    cv.drawRect(rect, P(shader=lin((x0, y0), (x0, y1) if horiz else (x1, y0), [('#ffffff', 0.08), ('#000000', 0.35)])))

# ------------------------------------------------------------------ text ---

def text_center(cv, s, y, size, face, color='#ffffff', a=1.0, shadow=0.6, x=W / 2):
    font = skia.Font(face, size)
    w = font.measureText(s)
    if shadow:
        cv.drawString(s, x - w / 2 + 2, y + 3, font, P('#000000', a * shadow, blur=4))
    cv.drawString(s, x - w / 2, y, font, P(color, a))


def wrap(s, font, maxw):
    words, lines, cur = s.split(), [], ''
    for wd in words:
        tryl = (cur + ' ' + wd).strip()
        if font.measureText(tryl) > maxw and cur:
            lines.append(cur); cur = wd
        else:
            cur = tryl
    if cur:
        lines.append(cur)
    return lines


def caption(cv, t):
    if not CAPTIONS_ON:
        return
    txt, lid = TL.caption_at(t)
    if not txt:
        return
    a = clamp((t - TL.S[lid] + 0.1) / 0.2) * clamp((TL.E[lid] + 0.35 - t) / 0.2)
    font = skia.Font(FONT_C, 29)
    lines = wrap(txt, font, 600)
    y = 1028 - (len(lines) - 1) * 19
    for i, ln in enumerate(lines):
        w = font.measureText(ln)
        yy = y + i * 40
        cv.drawString(ln, W / 2 - w / 2 + 1.5, yy + 2.5, font, P('#000000', 0.85 * a, blur=3))
        p = P('#000000', 0.9 * a, stroke=4)
        cv.drawString(ln, W / 2 - w / 2, yy, font, p)
        cv.drawString(ln, W / 2 - w / 2, yy, font, P('#fbf6ec', a))


def title_card(cv, t):
    a = clamp((5.2 - t) / 0.8)
    if a <= 0:
        return
    cv.drawRect(skia.Rect(0, 120, W, 420), P('#000000', 0.25 * a, blur=40))
    text_center(cv, 'PSALM 22', 190, 26, FONT_C, '#f6e7c8', a, 0.7)
    text_center(cv, 'My God, my God,', 270, 60, FONT_T, '#ffffff', a, 0.8)
    text_center(cv, 'why have you', 340, 60, FONT_T, '#ffffff', a, 0.8)
    text_center(cv, 'forsaken me?', 410, 60, FONT_T, '#ffffff', a, 0.8)

# =============================================================== SHOTS =====

def shot_mockers(cv, t, sh):
    lt = t - sh.start
    pal = golgotha_pal(t)
    soft_bg(cv, bg_level, t, pal, True, 820)
    cv.saveLayer(None, None)
    # soldier (back, right)
    shake2 = math.sin((t - S['M2']) * 9) * 0.14 * kf(t, [(E['M2'] - 0.3, 0), (E['M2'] + 0.2, 1), (E['M2'] + 1.8, 0)])
    st2 = live('mocker2', t, kfd(t, [
        (sh.start, dict(gy=-0.7, gx=-0.1, pitch=0.12, smirk=0.2, smile=0.1, yaw=-0.25, b_out=0.2)),
        (S['M2'], dict(smirk=0.6, smile=0.35, lower=0.35, b_out=0.4, b_in=-0.2)),
        (E['M2'], dict(smirk=0.7, smile=0.55, pitch=0.18, lower=0.5)),
    ]))
    st2['yaw'] += shake2
    put(cv, 'mocker2', 520, 470, 1.9, st2, t)
    shake1 = math.sin((t - S['M1']) * 8) * 0.16 * kf(t, [(S['M1'] + 0.3, 0), (S['M1'] + 0.6, 1), (E['M1'] + 0.4, 0.6), (E['M2'] + 1.5, 0)])
    st1 = live('mocker1', t, kfd(t, [
        (sh.start, dict(gy=-0.75, gx=0.15, pitch=0.12, yaw=0.2, b_out=0.3, b_in=-0.2, smirk=0.3)),
        (S['M1'], dict(b_out=0.6, b_in=-0.3, smirk=0.75, lower=0.4)),
        (E['M1'] + 0.2, dict(gx=0.6, gy=-0.2, yaw=0.32, smirk=0.9, lower=0.5)),
        (E['M2'], dict(gx=0.0, gy=-0.6, yaw=0.18, smirk=0.8)),
    ]))
    st1['yaw'] += shake1
    put(cv, 'mocker1', 240, 650, 2.3, st1, t)
    grade(cv, pal[4], 0.9)
    cv.restore()
    vignette(cv)


def mary_state(t, v, sh):
    base = dict(b_in=0.75, knit=0.35, smile=-0.35, wet=0.9, flush=0.45, gy=-0.55, pitch=0.08, open_l=0.92, open_r=0.92)
    if v == 'flinch':
        k = kfd(t, [(sh.start, dict(b_in=0.8, open_l=0.95, open_r=0.95, knit=0.4)),
                    (sh.start + 0.25, dict(b_in=1.0, knit=0.9, open_l=0.0, open_r=0.0, smile=-0.6, roll=-6, yaw=-0.12, flush=0.7)),
                    (sh.end, dict(b_in=1.0, knit=0.9, open_l=0.0, open_r=0.0, smile=-0.6, roll=-6, yaw=-0.12, flush=0.7))])
        base.update(k)
        base['tears'] = tears_track(t, [sh.start + 0.3], 1, 1.8)
        base['tremble'] = 0.5
    elif v == 'let':
        base.update(kfd(t, [(sh.start, dict(gy=-0.7, b_in=1.0, knit=0.6, open_l=1.08, open_r=1.08, smile=-0.5, hand=1.0)),
                            (S['Y1'] - 0.1, dict(hand=1.0)),
                            (E['Y1'] + 0.6, dict(hand=0.0, b_in=0.6, knit=0.2, smile=-0.25)),
                            (E['Y1'] + 0.3, dict(gy=-0.6, b_in=0.55, smile=-0.2, open_l=0.95, open_r=0.95)),
                            (sh.end, dict(gy=-0.3, b_in=0.65, smile=-0.25))]))
        base['tears'] = tears_track(t, [sh.start - 2.0, S['Y1'] + 0.6], 1, 2.8, 9) + tears_track(t, [S['Y1'] + 1.5], -1, 3.0, 9)
    elif v == 'quiet':
        base.update(kfd(t, [(sh.start, dict(gy=-0.6, b_in=0.9, knit=0.5, smile=-0.45, open_l=0.85, open_r=0.85)),
                            (S['Y3'] + 0.2, dict(gy=-0.75, b_in=0.65, knit=0.15, smile=-0.15, open_l=1.0, open_r=1.0, pitch=0.12))]))
        base['tears'] = tears_track(t, [sh.start - 1.0], 1, 2.0, 8) + tears_track(t, [sh.start + 0.4], -1, 2.6, 8)
    elif v == 'praying':
        base.update(kfd(t, [(sh.start, dict(gy=0.1, gx=0.5, yaw=0.18, b_in=0.6, smile=-0.1)),
                            (S['Y4'] + 0.2, dict(gx=0.55, yaw=0.2)),
                            (F('Y4', 0)[1], dict(gy=-0.5, gx=0.0, yaw=0.0, open_l=0.7, open_r=0.7)),
                            (F('Y4', 1)[0], dict(open_l=0.0, open_r=0.0, pitch=0.06, smile=0.05, b_in=0.45)),
                            (sh.end, dict(open_l=0.0, open_r=0.0, pitch=0.1, smile=0.08))]))
        base['tears'] = tears_track(t, [S['Y4'] + 1.2], -1, 2.8, 8)
    elif v == 'look':
        base.update(kfd(t, [(sh.start, dict(gy=-0.2, gx=0.0, yaw=0.0, b_in=1.0, knit=0.4, smile=-0.5, open_l=0.8, open_r=0.8)),
                            (sh.start + 0.5, dict(gx=0.8, yaw=0.32, gy=0.0)),
                            (sh.start + 1.1, dict(b_in=0.7, knit=0.0, smile=-0.1, pitch=-0.05)),
                            (sh.end, dict(pitch=0.02))]))
        base['tears'] = tears_track(t, [sh.start - 3], 1, 2.0, 8) + tears_track(t, [sh.start - 2], -1, 2.0, 8)
    return base


def shot_mary_cu(cv, t, sh):
    v = sh.variant
    pal = golgotha_pal(t)
    soft_bg(cv, bg_level, t, pal, True, 880)
    st = mary_state(t, v, sh)
    hand_k = st.pop('hand', 0.0)
    st = live('mary', t, st, gain=0.5, br_rate=0.3 if v != 'flinch' else 0.5, br_amp=1.4)
    cv.saveLayer(None, None)
    push = 1.0 + 0.04 * ease((t - sh.start) / max(1, sh.end - sh.start))
    cv.save(); cv.translate(W / 2, 560); cv.scale(push, push); cv.translate(-W / 2, -560)
    put(cv, 'mary', 360, 540, 3.15, st, t)
    if hand_k > 0.01:
        d = CH['mary']
        y = lerp(1100, 700, hand_k)
        sl = (y - 540) / 3.15
        cv.save(); cv.translate(360, 540); cv.scale(3.15, 3.15)
        cv.drawPath(tapered([(-8, sl + 30), (-14, sl + 90), (-24, sl + 200)], 30, 44), P('#2c4677'))
        hand(cv, -12, sl + 32, 0.95, -82, d, 'back', 0.45)
        cv.restore()
    cv.restore()
    grade(cv, pal[4], 0.85)
    cv.restore()
    vignette(cv)


def shot_magdalene_cu(cv, t, sh):
    v = sh.variant
    pal = golgotha_pal(t)
    soft_bg(cv, bg_level, t, pal, True, 860)
    if v == 'laugh':
        base = kfd(t, [(sh.start, dict(gx=0.75, gy=-0.1, yaw=0.3, b_in=0.4, knit=0.9, smile=-0.4, open_l=1.05, open_r=1.05)),
                       (S['G1'] + 0.4, dict(gx=0.6, yaw=0.25, b_in=0.9, knit=0.8, smile=-0.5)),
                       (F('G1', 1)[0], dict(gx=-0.1, gy=-0.6, yaw=0.0, b_in=1.0, knit=0.5, pitch=0.1, smile=-0.55)),
                       (sh.end, dict(gx=-0.1, gy=-0.65, b_in=1.0, open_l=0.85, open_r=0.85))])
        base.update(wet=0.8, flush=0.5, tremble=0.4)
        base['tears'] = tears_track(t, [F('G1', 1)[0]], -1, 2.2)
    else:  # mother
        base = kfd(t, [(sh.start, dict(gy=-0.75, gx=0.0, yaw=0.0, b_in=1.0, knit=0.7, open_l=1.2, open_r=1.2, m_open=0.25, pitch=0.15)),
                       (sh.start + 0.6, dict(open_l=1.15, open_r=1.15, m_open=0.12)),
                       (S['G2'] - 0.1, dict(gx=-0.8, gy=0.0, yaw=-0.3, pitch=0.0, m_open=0.0)),
                       (F('G2', 1)[0], dict(gx=-0.3, gy=-0.6, yaw=-0.15, pitch=0.1)),
                       (F('G2', 2)[0], dict(gx=-0.85, gy=0.05, yaw=-0.3, b_in=1.1, knit=0.8)),
                       (sh.end, dict(gx=-0.8, yaw=-0.3, b_in=0.9))])
        base.update(wet=1.0, flush=0.6, tremble=0.5)
        base['tears'] = tears_track(t, [sh.start + 0.5], 1, 2.4) + tears_track(t, [F('G2', 2)[0]], -1, 2.4)
    st = live('magdalene', t, base, gain=0.55, br_rate=0.42, br_amp=1.6)
    cv.saveLayer(None, None)
    put(cv, 'magdalene', 360, 545, 3.1, st, t)
    grade(cv, pal[4], 0.85)
    cv.restore()
    vignette(cv)


def shot_john_cu(cv, t, sh):
    v = sh.variant
    pal = golgotha_pal(t)
    soft_bg(cv, bg_level, t, pal, True, 840)
    if v == 'feel':
        base = kfd(t, [(sh.start, dict(gx=0.7, gy=-0.1, yaw=0.25, knit=0.9, b_in=-0.3, smile=-0.35)),
                       (S['J1'] + 0.2, dict(gx=0.65, knit=0.9, b_in=-0.2)),
                       (F('J1', 1)[0], dict(gx=-0.7, gy=0.1, yaw=-0.2, knit=0.4, b_in=0.4, smile=-0.25)),
                       (sh.end, dict(gx=-0.6, yaw=-0.18, b_in=0.55, knit=0.3, open_l=0.85, open_r=0.85))])
        base.update(wet=0.4)
    else:  # psalm
        base = kfd(t, [(sh.start, dict(gy=-0.6, gx=0.1, b_in=0.7, knit=0.3, open_l=1.05, open_r=1.05, pitch=0.08)),
                       (S['J2'] + 0.3, dict(gy=-0.3, b_in=0.5)),
                       (F('J2', 1)[0], dict(gx=-0.7, gy=0.0, yaw=-0.25, b_in=0.8, smile=0.0, open_l=0.95, open_r=0.95)),
                       (sh.end, dict(gx=-0.75, yaw=-0.28, b_in=0.9, smile=0.08, open_l=0.85, open_r=0.85))])
        base.update(wet=0.9, flush=0.3)
        base['tears'] = tears_track(t, [F('J2', 2)[0] + 0.3], 1, 2.6)
    st = live('john', t, base, gain=0.55)
    cv.saveLayer(None, None)
    put(cv, 'john', 360, 540, 3.1, st, t)
    grade(cv, pal[4], 0.85)
    cv.restore()
    vignette(cv)


def jesus_base(t, v, sh):
    b = dict(pitch=-0.22, roll=7, hy=10, hx=4, b_in=0.75, knit=0.45, smile=-0.25, open_l=0.55, open_r=0.55,
             gy=0.5, wet=0.5, flush=0.25, strain=0.15, sag=1)
    if v == 'low':
        b.update(kfd(t, [(sh.start, dict(open_l=0.2, open_r=0.2, gy=0.6, gx=0.0)),
                         (sh.start + 0.6, dict(open_l=0.55, open_r=0.55, gx=-0.5, gy=0.8, yaw=-0.12, pitch=-0.28, roll=4)),
                         (S['X1'] + 0.2, dict(b_in=0.85, knit=0.2, smile=0.0)),
                         (E['X1'] + 0.2, dict(gx=-0.45, yaw=-0.1, smile=0.08)),
                         (S['X2'] - 0.3, dict(gx=0.55, yaw=0.12, roll=9)),
                         (E['X2'], dict(gx=0.5, yaw=0.1, smile=0.12, b_in=0.9, knit=0.1)),
                         (sh.end, dict(open_l=0.3, open_r=0.3, gx=0.3))]))
        b['tears'] = tears_track(t, [S['X2'] + 0.5], -1, 2.6, 6)
    elif v == 'pray':
        b.update(kfd(t, [(sh.start, dict(open_l=0.0, open_r=0.0, pitch=-0.3, roll=10, b_in=0.9, knit=0.6)),
                         (S['X3'] + 0.1, dict(open_l=0.1, open_r=0.1, pitch=-0.18, roll=7)),
                         (F('X3', 1)[0], dict(open_l=0.35, open_r=0.35, gy=-0.6, pitch=-0.08, b_in=1.0, knit=0.7)),
                         (sh.end, dict(open_l=0.0, open_r=0.0, pitch=-0.25, roll=9))]))
    elif v == 'cry':
        c0 = F('XC', 0)[0]
        b.update(kfd(t, [(sh.start, dict(open_l=0.0, open_r=0.0, pitch=-0.3, roll=9, b_in=0.8, knit=0.6, strain=0.2)),
                         (c0 - 1.0, dict(open_l=0.0, open_r=0.0, pitch=-0.3, roll=9)),
                         (c0 - 0.15, dict(open_l=1.25, open_r=1.25, gy=-1.0, gx=0.0, pitch=0.28, roll=-2, hy=-6, hx=0,
                                          b_in=1.2, knit=1.0, strain=1.0, smile=-0.4, flush=0.7, wet=1.0, arm_lift=1)),
                         (sh.end, dict(open_l=1.15, open_r=1.15, pitch=0.3, b_in=1.2, knit=1.0, strain=1.0))]))
        b['tears'] = tears_track(t, [F('XC', 1)[0]], 1, 2.0, 8) + tears_track(t, [F('XC', 2)[0]], -1, 2.0, 8)
    elif v == 'forsaken':
        b.update(kfd(t, [(sh.start, dict(open_l=1.1, open_r=1.1, gy=-0.9, pitch=0.22, roll=0, hy=-2, b_in=1.2, knit=1.0,
                                         strain=0.8, flush=0.7, wet=1.0, smile=-0.45)),
                         (F('X4', 1)[1], dict(open_l=0.9, open_r=0.9, pitch=0.12, roll=3)),
                         (F('X4', 2)[0], dict(open_l=0.75, open_r=0.75, gy=-0.6, pitch=0.05, b_in=1.25, knit=1.0, strain=0.5)),
                         (E['X4'], dict(open_l=0.3, open_r=0.3, pitch=-0.15, roll=8, hy=8, strain=0.2)),
                         (sh.end, dict(open_l=0.0, open_r=0.0, pitch=-0.25, roll=10, hy=10))]))
        b['tears'] = tears_track(t, [sh.start - 3], 1, 2.0, 12) + tears_track(t, [sh.start - 2], -1, 2.0, 12) + \
            tears_track(t, [F('X4', 2)[0]], 1, 2.4, 8)
    elif v == 'father':
        b.update(kfd(t, [(sh.start, dict(open_l=0.0, open_r=0.0, pitch=-0.25, roll=10, b_in=0.8, knit=0.4)),
                         (S['X5'] - 0.4, dict(open_l=0.5, open_r=0.5, gy=-0.8, pitch=0.12, roll=3, hy=-2, b_in=0.75, knit=0.1, smile=0.0, strain=0.3)),
                         (F('X5', 1)[0], dict(open_l=0.7, open_r=0.7, gy=-0.9, pitch=0.16, smile=0.05, b_in=0.6)),
                         (F('X5', 2)[0], dict(open_l=0.5, open_r=0.5, smile=0.1, b_in=0.45, knit=0.0)),
                         (E['X5'] + 0.3, dict(open_l=0.25, open_r=0.25, gy=-0.4, pitch=0.05, smile=0.12, strain=0.0)),
                         (E['X5'] + 1.6, dict(open_l=0.0, open_r=0.0, pitch=-0.3, roll=17, hy=22, hx=10, b_in=0.3, knit=0.0, smile=0.0, sag=2)),
                         (sh.end, dict(open_l=0.0, open_r=0.0, pitch=-0.3, roll=17, hy=22, hx=10))]))
        b['tears'] = tears_track(t, [F('X5', 2)[0]], -1, 3.0, 9)
    return b


def shot_jesus(cv, t, sh):
    v = 'low' if sh.setup == 'jesus_low' else sh.variant
    pal = golgotha_pal(t)
    soft_bg(cv, bg_up, t, pal)
    lt = t - sh.start
    st = jesus_base(t, v, sh)
    gain = 0.5
    rate, amp = 0.28, 2.2
    if v == 'cry':
        gain = 1.6
        rate, amp = 0.35, 3.0
    if v == 'pray':
        gain = 0.32
    if v == 'father':
        dead = clamp((t - E['X5'] - 0.4) / 1.2)
        amp = 2.2 * (1 - dead)
        st['breath'] = -2.5 * ease(dead)
        if dead > 0:
            st['open_l'] = st['open_r'] = 0.0
    st = live('jesus', t, st, gain=gain, br_rate=rate, br_amp=amp, blink=(v not in ('cry',)), sway=0.6,
              sacc=0.5, nod=0.4, mmax=1.45 if v == 'cry' else 1.0)
    # inhale before the cry: chest heaves
    if v == 'cry':
        c0 = F('XC', 0)[0]
        st['breath'] += 4.0 * ease(clamp((t - (c0 - 1.0)) / 0.8)) * (1 - ease(clamp((t - c0) / 0.6)))
    zoom = 1.0
    cy0 = 470 if v == 'low' else 500
    x0, s = 360, 3.0
    if v == 'low':
        zoom = 1.0 + 0.03 * ease(lt / 9)
    if v == 'cry':
        c0 = F('XC', 0)[0]
        zoom = lerp(1.0, 1.16, ease((t - (c0 - 1.4)) / 6.5))
    if v == 'forsaken':
        zoom = lerp(1.16, 1.06, ease(lt / 6))
    if v == 'father':
        zoom = lerp(1.0, 1.06, ease(lt / 9))
    shake = 0.0
    if v == 'cry':
        loud, _ = speech('JESUS', t)
        shake = clamp(loud - 0.6) * 5
    cv.saveLayer(None, None)
    cv.save()
    cv.translate(W / 2 + math.sin(t * 41) * shake, cy0 + math.cos(t * 37) * shake)
    cv.scale(zoom, zoom)
    cv.translate(-W / 2, -cy0)
    # the cross behind him
    wood(cv, skia.Rect(x0 - 34 * s, -400, x0 + 34 * s, H + 200), '#4a3828', '#2a1c12')
    by = cy0 + 10 * s
    wood(cv, skia.Rect(-400, by, W + 400, by + 58 * s), '#4f3b2a', '#2a1c12')
    cv.drawRect(skia.Rect(x0 - 50, cy0 - 112 * s, x0 + 50, cy0 - 92 * s), P('#d2c4a4'))
    cv.drawRect(skia.Rect(x0 - 50, cy0 - 112 * s, x0 + 50, cy0 - 92 * s), P('#6a5a40', stroke=2))
    font = skia.Font(FONT_T, 34)
    tw = font.measureText('INRI')
    cv.drawString('INRI', x0 - tw / 2, cy0 - 96 * s - 4, font, P('#3a2a1a', 0.9))
    lift = st.get('breath', 0) * 1.5
    put(cv, 'jesus', x0, cy0 - lift, s, st, t)
    cv.restore()
    grade(cv, pal[4], 0.8)
    if v == 'cry':
        c0 = F('XC', 0)[0]
        for k in range(3):
            fl = max(0.0, 1 - (t - F('XC', k)[0]) / 0.3) if t >= F('XC', k)[0] else 0
            if fl > 0:
                cv.drawPaint(P('#e8eeff', 0.32 * fl))
    cv.restore()
    vignette(cv, 0.6)


def shot_group3(cv, t, sh):
    pal = golgotha_pal(t)
    soft_bg(cv, bg_level, t, pal, True, 900)
    lt = t - sh.start
    k = ease(lt / 1.4)
    cv.saveLayer(None, None)
    stj = live('john', t, dict(gy=0.2, gx=-0.6, yaw=-0.25, b_in=0.7, smile=-0.05, wet=0.8, open_l=0.85, open_r=0.85, roll=-4 * k))
    put(cv, 'john', 520, 560, 1.55, stj, t)
    stm = live('mary', t, dict(gy=-0.3 + 0.4 * k, gx=0.3, b_in=0.8, knit=0.3, smile=-0.3 + 0.2 * k, wet=1, flush=0.5,
                               roll=9 * k, hx=8 * k, open_l=lerp(0.9, 0.0, ease((lt - 0.8) / 0.6)),
                               open_r=lerp(0.9, 0.0, ease((lt - 0.8) / 0.6)),
                               tears=tears_track(t, [sh.start + 0.6], -1, 1.6, 6)), br_amp=1.4)
    put(cv, 'mary', 355, 700, 1.6, stm, t)
    # John's hand settles on Mary's shoulder
    d = CH['john']
    hx_ = lerp(640, 505, k)
    hy_ = lerp(1010, 872, k)
    cv.save(); cv.translate(hx_, hy_); cv.scale(1.55, 1.55)
    cv.drawPath(tapered([(70, 60), (40, 20), (6, 2)], 30, 24), P('#7a5634'))
    hand(cv, 0, 0, 0.85, 200, d, 'back', 0.7, flip=False)
    cv.restore()
    stg = live('magdalene', t, dict(gy=-0.2, gx=0.7, yaw=0.3, b_in=0.9, knit=0.4, wet=1, flush=0.5, roll=-6 * k,
                                    hx=10 * k, open_l=0.75, open_r=0.75,
                                    tears=tears_track(t, [sh.start - 1], 1, 2.0, 6)), br_amp=1.4)
    put(cv, 'magdalene', 185, 790, 1.5, stg, t)
    grade(cv, pal[4], 0.85)
    cv.restore()
    vignette(cv)


def shot_centurion(cv, t, sh):
    v = sh.variant
    pal = golgotha_pal(t)
    soft_bg(cv, bg_level, t, pal, True, 860)
    if v == 'react':
        base = kfd(t, [(sh.start, dict(gy=0.2, gx=0.3, yaw=0.15, b_in=0.0, knit=0.2, smile=-0.1)),
                       (sh.start + 0.35, dict(gy=-0.85, gx=0.0, yaw=0.0, pitch=0.14, open_l=1.18, open_r=1.18,
                                              b_in=0.6, b_out=0.3, knit=0.5, m_open=0.08)),
                       (sh.end, dict(gy=-0.85, pitch=0.14, open_l=1.12, open_r=1.12, b_in=0.7))])
        base['helm'] = 1.0
    elif v == 'truly':
        base = kfd(t, [(sh.start, dict(gy=-0.75, pitch=0.12, b_in=0.9, knit=0.5, wet=0.7, open_l=1.0, open_r=1.0,
                                       helm=1.0, helm_hands=0.0, helm_chest=0.0, smile=-0.3, tremble=0.3)),
                       (sh.start + 0.5, dict(helm_hands=1.0)),
                       (sh.start + 1.25, dict(helm=0.0, helm_hands=1.0)),
                       (sh.start + 1.3, dict(helm_hands=0.0)),
                       (sh.start + 1.35, dict(helm_chest=0.0)),
                       (S['C1'] - 0.1, dict(helm_chest=1.0, gy=-0.8, pitch=0.12, b_in=1.0, knit=0.4)),
                       (F('C1', 1)[0], dict(gy=-0.6, b_in=1.1, knit=0.6, wet=1.0, flush=0.4)),
                       (sh.end, dict(gy=0.4, pitch=-0.06, b_in=1.0, open_l=0.6, open_r=0.6))])
        base['tears'] = tears_track(t, [F('C1', 1)[0] + 0.4], -1, 2.4)
    else:  # after
        base = dict(gy=0.55, gx=0.1, pitch=-0.1, b_in=0.8, knit=0.3, wet=1.0, flush=0.3, open_l=0.6, open_r=0.6,
                    helm=0.0, helm_chest=1.0, smile=-0.15)
        base['tears'] = tears_track(t, [sh.start - 4], -1, 2.4, 20)
    if v != 'react':
        base.setdefault('helm', 0.0)
    st = live('centurion', t, base, gain=0.5, br_rate=0.22)
    cv.saveLayer(None, None)
    put(cv, 'centurion', 360, 545, 3.0, st, t)
    grade(cv, pal[4], 0.85)
    cv.restore()
    vignette(cv)


def shot_flashback(cv, t, sh):
    lt = t - sh.start
    # warm lamplit room
    cv.drawPaint(P(shader=rad((470, 380), 900, [('#7a4a26', 1), ('#3a2214', 1), ('#140a06', 1)], [0, 0.45, 1])))
    cv.drawCircle(560, 300, 34, P('#ffcf7a', 0.9, blur=12))
    cv.drawCircle(560, 300, 160, P('#ffb050', 0.25, blur=50))
    rock = math.sin(lt * 1.6) * 3.0
    calm = ease(clamp((t - F('Y2', 2)[0]) / 1.4))
    base = dict(gy=0.85, gx=0.2, pitch=-0.18, roll=rock * 0.8 - 4, smile=lerp(0.1, 0.5, calm), b_in=lerp(0.6, 0.3, calm),
                wet=1.0, flush=0.35, open_l=lerp(0.85, 0.7, calm), open_r=lerp(0.85, 0.7, calm), light=(0.6, -0.8))
    hum = 0.08 + 0.06 * math.sin(lt * 4.3) if calm > 0.3 else 0.0
    base['m_open'] = hum * calm
    base['tears'] = tears_track(t, [sh.start + 1.0], 1, 3.0, 8)
    st = live('young_mary', t, base, br_rate=0.25, blink=True)
    cv.saveLayer(None, None)
    cv.save(); cv.rotate(rock * 0.2)
    put(cv, 'young_mary', 330, 470, 2.6, st, t, CH['young_mary'])
    d = CH['young_mary']
    cv.save(); cv.translate(330, 470); cv.scale(2.6, 2.6)
    cv.drawPath(tapered([(-90, 330), (-60, 250), (10, 215)], 40, 34), P('#2c4677'))
    cv.restore()
    baby(cv, 400 + rock * 4, 900 + rock * 2, 2.3, t, calm)
    cv.save(); cv.translate(330, 470); cv.scale(2.6, 2.6)
    hand(cv, 10, 205, 0.85, -40, d, 'back', 0.55)
    cv.restore()
    cv.restore()
    grade(cv, '#ffd6a0', 0.6)
    cv.restore()
    cv.drawPaint(P(shader=rad((W / 2, H / 2), H * 0.7, [('#ffd8a0', 0.0), ('#2a1408', 0.8)], [0.45, 1])))
    cv.drawPaint(P('#ffe0b0', 0.08))


def baby(cv, x, y, s, t, calm):
    cv.save(); cv.translate(x, y); cv.scale(s, s); cv.rotate(-28)
    sw = smooth([(-95, -30), (-70, -58), (-20, -60), (50, -44), (110, -22), (130, 8), (100, 34), (20, 44), (-60, 40), (-96, 14)])
    cv.drawPath(sw, P('#ece2cc'))
    cv.drawPath(sw, P(shader=lin((-90, -60), (120, 40), [('#ffffff', 0.25), ('#a89878', 0.55)])))
    for k in range(4):
        cv.drawPath(smooth([(-20 + k * 34, -46), (-6 + k * 34, -4), (-14 + k * 34, 38)], False), P('#b8a888', 0.6, stroke=2.2))
    cry = 1 - calm
    fx, fy = -52, -8
    cv.drawOval(skia.Rect(fx - 40, fy - 40, fx + 40, fy + 40), P('#ecdcc0'))
    cv.drawOval(skia.Rect(fx - 31, fy - 30, fx + 31, fy + 31), P('#d8a080'))
    cv.drawOval(skia.Rect(fx - 31, fy - 30, fx + 31, fy + 31), P('#a06a50', 0.5, stroke=1.2))
    cv.drawOval(skia.Rect(fx - 36, fy - 44, fx + 36, fy - 14), P('#ecdcc0'))
    wob = math.sin(t * 9) * cry
    for sgn in (-1, 1):
        ex = fx + sgn * 12
        if cry > 0.3:
            cv.drawPath(smooth([(ex - 7, fy - 1), (ex, fy - 5 - wob), (ex + 7, fy - 1)], False), P('#5a3020', stroke=2.4))
            cv.drawPath(smooth([(ex - 8, fy - 9), (ex, fy - 11), (ex + 8, fy - 9)], False), P('#a06a50', 0.6, stroke=1.4))
        else:
            cv.drawPath(smooth([(ex - 7, fy - 3), (ex, fy + 1), (ex + 7, fy - 3)], False), P('#5a3020', stroke=2.2))
        cv.drawCircle(ex + sgn * 2, fy + 9, 6, P('#e07060', 0.3 + 0.25 * cry, blur=3))
    cv.drawCircle(fx, fy + 4, 3, P('#b07058', 0.6))
    mo = 12 * cry * (0.7 + 0.3 * abs(math.sin(t * 5)))
    if mo > 1.5:
        cv.drawOval(skia.Rect(fx - 8, fy + 11, fx + 8, fy + 11 + mo), P('#7a2a2a'))
    else:
        cv.drawPath(smooth([(fx - 5, fy + 15), (fx, fy + 17), (fx + 5, fy + 15)], False), P('#8a4a40', stroke=1.8))
    cv.restore()


def jesus_dispatch(cv, t, sh):
    shot_jesus(cv, t, sh)

# ----------------------------------------------------------------- modern ---

def porch_bg(c2, t, dawn=0.0, blur_far=True):
    c2.drawPaint(P(mix('#151a24', '#8a9ab8', dawn)))
    # siding
    wall = mix('#3a3430', '#a89a88', dawn * 0.7)
    wc = '#%02x%02x%02x' % tuple(int(v * 255) for v in wall)
    c2.drawRect(skia.Rect(0, 0, 520, 1000), P(wc))
    for i in range(30):
        y = i * 34
        c2.drawLine(0, y, 520, y, P('#000000', 0.25, stroke=3))
    # window with warm light
    c2.drawRect(skia.Rect(90, 230, 330, 560), P('#ffc878', 0.9 - 0.4 * dawn))
    c2.drawRect(skia.Rect(90, 230, 330, 560), P('#2a2018', stroke=14))
    c2.drawLine(210, 230, 210, 560, P('#2a2018', stroke=8))
    c2.drawLine(90, 395, 330, 395, P('#2a2018', stroke=8))
    c2.drawCircle(210, 395, 260, P('#ffb050', 0.18 * (1 - dawn), blur=60))
    # porch lamp
    c2.drawCircle(470, 180, 22, P('#fff0c0', 1 - 0.6 * dawn))
    c2.drawCircle(470, 180, 140, P('#ffcf80', 0.35 * (1 - dawn), blur=40))
    # outside: night garden or dawn sky
    sky_c = mix('#0c1018', '#ffd8a0', dawn)
    c2.drawRect(skia.Rect(520, 0, W, 1000), P(shader=lin((0, 0), (0, 1000), [(mix('#0a0e18', '#7a98c8', dawn), 1), (sky_c, 1)])))
    c2.drawRect(skia.Rect(520, 0, 560, 1000), P('#2a221c'))
    # floor / steps
    floor = mix('#2a2420', '#7a6450', dawn * 0.7)
    c2.drawRect(skia.Rect(0, 1000, W, H), P(floor))
    for i in range(5):
        y = 1000 + i * 60
        c2.drawLine(0, y, W, y, P('#000000', 0.3, stroke=4))
    if dawn < 0.5:
        r = np.random.default_rng(3)
        for i in range(10):
            fx = 560 + r.uniform(0, 160) + math.sin(t * 0.7 + i) * 20
            fy = r.uniform(200, 900) + math.cos(t * 0.5 + i * 2) * 25
            a = 0.5 + 0.5 * math.sin(t * 2.3 + i * 1.7)
            c2.drawCircle(fx, fy, 6, P('#e8f070', 0.7 * a * (1 - dawn), blur=4))


def phone_glow(cv, cx, cy, a, t):
    flick = 0.85 + 0.15 * math.sin(t * 2.1) * math.sin(t * 0.7)
    cv.drawPaint(P(shader=rad((cx, cy), 560, [('#9cc4ff', 0.26 * a * flick), ('#9cc4ff', 0.0)]), blend=skia.BlendMode.kScreen))


def shot_phone_cu(cv, t, sh):
    lt = t - sh.start
    soft_bg(cv, porch_bg, t, 0.0)
    cv.drawPaint(P('#000000', 0.45))
    late = F('N7', 3)[0]
    base = kfd(t, [(sh.start, dict(gy=0.8, gx=0.05, pitch=-0.12, open_l=0.7, open_r=0.7, b_in=0.0, smile=-0.05, phone=1.0)),
                   (late, dict(gy=0.8, b_in=0.1, open_l=0.72, open_r=0.72)),
                   (late + 1.2, dict(b_in=0.75, knit=0.3, wet=0.8, open_l=0.85, open_r=0.85, smile=-0.25)),
                   (E['N7'] - 0.2, dict(phone=1.0, gy=0.6)),
                   (sh.end, dict(phone=0.0, gy=-0.1, gx=0.6, yaw=0.18, pitch=0.0, b_in=0.8, wet=1.0))])
    ph = base.pop('phone')
    base['light'] = (0.0, 1.0)
    st = live('young', t, base, br_rate=0.2, sacc=0.4)
    cv.saveLayer(None, None)
    put(cv, 'young', 360, 520, 3.0, st, t)
    # the phone and the hand that holds it
    py = lerp(1420, 1120, ph)
    cv.save(); cv.translate(360, py); cv.rotate(-8)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-110, -200, 110, 200), 26, 26), P('#14161c'))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-110, -200, 110, 200), 26, 26), P('#5a6070', stroke=3))
    cv.drawCircle(-60, -150, 16, P('#2a2e38'))
    cv.restore()
    d = CH['young']
    cv.save(); cv.translate(360, py); cv.scale(3.0, 3.0)
    hand(cv, -48, 10, 0.95, -60, d, 'back', 0.75)
    thumb = math.sin(lt * 2.4) * 4 if ph > 0.8 else 0
    cv.restore()
    grade(cv, '#a8b0c8', 0.6)
    cv.restore()
    phone_glow(cv, 360, py - 420, ph, t)
    vignette(cv, 0.7)


def shot_porch_two(cv, t, sh):
    soft_bg(cv, porch_bg, t, 0.0)
    cv.saveLayer(None, None)
    # Nana in her chair
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(400, 360, 640, 900), 20, 20), P('#3a2a20'))
    for i in range(5):
        cv.drawLine(420 + i * 50, 380, 420 + i * 50, 880, P('#241a14', stroke=10))
    stn = live('nana', t, kfd(t, [(sh.start, dict(gx=0.3, gy=0.4, yaw=0.0, smile=0.15, open_l=0.85, open_r=0.85)),
                                  (S['Q1'] + 0.8, dict(gx=-0.6, gy=0.3, yaw=-0.2)),
                                  (F('Q1', 1)[0], dict(gx=-0.7, yaw=-0.3, smile=0.0, b_in=0.4, lower=0.2)),
                                  (sh.end, dict(gx=-0.75, yaw=-0.32, smile=-0.05, b_in=0.55))]))
    put(cv, 'nana', 520, 470, 1.45, stn, t)
    sty = live('young', t, kfd(t, [(sh.start, dict(gy=0.6, gx=0.3, yaw=0.1, b_in=0.6, wet=0.8, light=(0.4, -0.6), b_asym=0.0)),
                                   (S['Q1'] + 0.3, dict(b_asym=0.35)),
                                   (S['Q1'] - 0.2, dict(gy=0.0, gx=0.8, yaw=0.3, b_in=0.8, knit=0.2)),
                                   (F('Q1', 2)[0], dict(gy=0.4, gx=0.3, yaw=0.15, b_in=0.9, smile=-0.2)),
                                   (F('Q1', 3)[0], dict(gy=0.0, gx=0.8, yaw=0.32, b_in=1.0, knit=0.3, smile=-0.3)),
                                   (sh.end, dict(gx=0.8, yaw=0.32))]))
    put(cv, 'young', 230, 760, 1.6, sty, t)
    grade(cv, '#e8c8a8', 0.6)
    cv.restore()
    vignette(cv, 0.6)


def shot_nana_cu(cv, t, sh):
    v = sh.variant
    soft_bg(cv, porch_bg, t, 0.0)
    cv.drawPaint(P('#000000', 0.25))
    chest = 0.0
    if v == 'every':
        base = kfd(t, [(sh.start, dict(gx=-0.5, gy=0.1, yaw=-0.2, b_in=0.5, smile=0.0, open_l=0.9, open_r=0.9)),
                       (S['R1'] - 0.4, dict(gx=-0.55, b_in=0.65, smile=0.15, lower=0.3, roll=-4)),
                       (E['R1'], dict(smile=0.3, lower=0.4, b_in=0.55, open_l=0.8, open_r=0.8))])
    elif v == 'heart':
        base = kfd(t, [(sh.start, dict(gx=-0.5, gy=0.0, yaw=-0.2, b_in=0.4, smile=0.2, lower=0.3, chest=0.0)),
                       (S['R2'] - 0.2, dict(chest=1.0)),
                       (F('R2', 1)[0], dict(b_in=0.6, open_l=0.75, open_r=0.75, smile=0.1)),
                       (F('R2', 2)[0] - 0.2, dict(gx=-0.2, gy=-0.4, yaw=-0.1, b_in=0.4, smile=0.15, chest=0.0)),
                       (sh.end, dict(gx=-0.3, gy=-0.3, open_l=0.85, open_r=0.85))])
    elif v == 'silence':
        base = kfd(t, [(sh.start, dict(gx=-0.6, gy=0.0, yaw=-0.25, b_in=0.4, smile=0.05, knit=0.2)),
                       (F('R3', 1)[0], dict(b_in=0.9, knit=0.35, smile=-0.1, wet=0.6, open_l=0.95, open_r=0.95)),
                       (F('R3', 2)[0], dict(b_in=0.5, b_out=0.4, knit=0.0, smile=0.2, lower=0.3, pitch=-0.05, roll=-5, b_asym=-0.4)),
                       (sh.end, dict(smile=0.35, lower=0.4))])
    else:  # plant
        base = kfd(t, [(sh.start, dict(gx=-0.5, gy=0.2, yaw=-0.2, smile=0.45, lower=0.5, b_in=0.3, wet=0.5)),
                       (S['R4'], dict(smile=0.35, lower=0.35)),
                       (F('R4', 1)[0], dict(gy=0.0, b_in=0.5, smile=0.3, open_l=0.85, open_r=0.85)),
                       (sh.end, dict(smile=0.5, lower=0.5, roll=-5, pitch=-0.06))])
    chest = base.pop('chest', 0.0)
    st = live('nana', t, base, gain=0.5, br_rate=0.2)
    cv.saveLayer(None, None)
    put(cv, 'nana', 360, 540, 3.0, st, t)
    if chest > 0.01:
        d = CH['nana']
        cv.save(); cv.translate(360, 540); cv.scale(3.0, 3.0)
        y = lerp(330, 175, chest)
        cv.drawPath(tapered([(60, y + 40), (40, y + 80), (30, y + 200)], 30, 40), P('#6b2f3a'))
        hand(cv, 50, y + 30, 0.95, -130, d, 'back', 0.25, flip=True)
        cv.restore()
    grade(cv, '#f0d0b0', 0.55)
    cv.restore()
    vignette(cv, 0.6)


def shot_young_cu(cv, t, sh):
    v = sh.variant
    dawn = 1.0 if v == 'dawn' else 0.0
    soft_bg(cv, porch_bg, t, dawn)
    cv.drawPaint(P('#000000', 0.25 * (1 - dawn)))
    if v == 'what':
        base = kfd(t, [(sh.start, dict(gx=0.6, gy=0.0, yaw=0.25, b_in=0.9, knit=0.3, wet=1.0, flush=0.4, smile=-0.2, b_asym=0.3)),
                       (F('Q2', 1)[0], dict(gy=0.5, gx=0.2, yaw=0.12, b_in=1.0, knit=0.5, smile=-0.35, b_asym=0.0)),
                       (F('Q2', 2)[0], dict(gx=0.65, gy=-0.05, yaw=0.25, b_in=1.15, knit=0.6, smile=-0.4)),
                       (sh.end, dict(gx=0.6, b_in=1.0, open_l=0.85, open_r=0.85))])
        base['tears'] = tears_track(t, [F('Q2', 2)[0] + 0.5], -1, 2.6)
        base['tremble'] = 0.4
    elif v == 'listen':
        base = kfd(t, [(sh.start, dict(gx=0.6, gy=0.0, yaw=0.25, b_in=0.8, knit=0.2, wet=1.0, flush=0.45, smile=-0.25, tremble=0.5)),
                       (sh.start + 1.4, dict(b_in=1.0, open_l=0.8, open_r=0.8, smile=-0.35)),
                       (sh.end, dict(b_in=0.9, open_l=0.75, open_r=0.75, pitch=-0.06))])
        base['tears'] = tears_track(t, [sh.start + 0.7], 1, 2.2) + tears_track(t, [sh.start + 2.0], -1, 2.2)
        nodk = math.sin((t - sh.start) * 3.0) * 0.04 * clamp((t - sh.start - 1.5) / 0.4)
        base['pitch'] = base.get('pitch', 0) + nodk
    elif v == 'acorn':
        base = kfd(t, [(sh.start, dict(gy=0.85, gx=0.0, pitch=-0.15, b_in=0.9, wet=1.0, flush=0.4, smile=-0.1)),
                       (S['Q3'] + 0.3, dict(gy=0.4, gx=0.55, yaw=0.2, pitch=-0.05, b_in=0.5, b_out=0.4, smile=0.35, lower=0.3)),
                       (sh.end, dict(gx=0.6, yaw=0.25, smile=0.45, lower=0.4))])
        base['tears'] = tears_track(t, [sh.start - 2], 1, 2.0, 8) + tears_track(t, [sh.start - 1], -1, 2.0, 8)
    else:  # dawn: final
        base = kfd(t, [(sh.start, dict(open_l=0.0, open_r=0.0, pitch=0.04, smile=0.15, b_in=0.2, light=(0.7, -0.5))),
                       (S['N13'] + 1.0, dict(open_l=0.0, open_r=0.0)),
                       (S['N13'] + 2.4, dict(open_l=0.9, open_r=0.9, gx=0.6, gy=-0.2, yaw=0.2)),
                       (F('N13', 3)[0], dict(gx=0.5, gy=-0.2, smile=0.25, b_in=0.35)),
                       (F('N13', 4)[0], dict(gx=0.0, gy=0.0, yaw=0.0, smile=0.45, lower=0.35, b_in=0.25, open_l=0.95, open_r=0.95)),
                       (sh.end, dict(smile=0.5, lower=0.4))])
        base['wet'] = 0.5
    st = live('young', t, base, gain=0.55, br_rate=0.25)
    cv.saveLayer(None, None)
    zoom = 1.0 + (0.05 * ease((t - sh.start) / (sh.end - sh.start)) if v == 'dawn' else 0)
    cv.save(); cv.translate(W / 2, 540); cv.scale(zoom, zoom); cv.translate(-W / 2, -540)
    put(cv, 'young', 360, 540, 3.0, st, t)
    if v == 'acorn':
        d = CH['young']
        cv.save(); cv.translate(360, 540); cv.scale(3.0, 3.0)
        hand(cv, -40, 210, 1.0, -20, d, 'palm', 0.35)
        acorn(cv, -5, 196, 1.0)
        cv.restore()
    cv.restore()
    grade(cv, '#ffe2c0' if dawn else '#f0d0b0', 0.55)
    cv.restore()
    if dawn:
        cv.drawPaint(P(shader=rad((650, 300), 700, [('#ffd890', 0.35), ('#ffd890', 0.0)]), blend=skia.BlendMode.kScreen))
    vignette(cv, 0.55)
    if v == 'dawn':
        end_card(cv, t)


def acorn(cv, x, y, s):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    cv.drawOval(skia.Rect(-9, -6, 9, 16), P('#a0662e'))
    cv.drawOval(skia.Rect(-6, -2, 0, 10), P('#d89a5a', 0.6))
    cv.drawPath(smooth([(-11, -2), (-8, -10), (0, -12), (8, -10), (11, -2), (0, 0)]), P('#5a3e22'))
    for i in range(5):
        cv.drawLine(-8 + i * 4, -9, -7 + i * 4, -2, P('#3a2614', 0.7, stroke=0.8))
    cv.drawLine(0, -12, 2, -17, P('#3a2614', stroke=1.6))
    cv.restore()


def shot_acorn_hands(cv, t, sh):
    lt = t - sh.start
    soft_bg(cv, porch_bg, t, 0.0)
    cv.drawPaint(P('#000000', 0.35))
    dn, dy = CH['nana'], CH['young']
    cv.saveLayer(None, None)
    # young palm, up
    curl = lerp(0.2, 0.55, ease((lt - 1.1) / 0.6))
    cv.save(); cv.translate(160, 860); cv.scale(4.4, 4.4)
    cv.drawPath(tapered([(-60, 30), (-30, 15), (0, 0)], 40, 30), P('#7a876a'))
    hand(cv, 0, 0, 1.0, -12, dy, 'palm', curl)
    cv.restore()
    drop = ease(clamp((lt - 0.6) / 0.35))
    ax, ay = lerp(400, 352, drop), lerp(640, 812, drop)
    if lt > 0.55:
        cv.save(); cv.translate(ax, ay); cv.scale(4.0, 4.0); acorn(cv, 0, 0, 1.0); cv.restore()
    # Nana's hand from above
    k = ease(clamp(lt / 0.6)) - ease(clamp((lt - 1.0) / 0.7))
    cv.save(); cv.translate(lerp(760, 560, k), lerp(200, 470, k)); cv.scale(4.2, 4.2)
    cv.drawPath(tapered([(40, -60), (20, -30), (0, 0)], 40, 32), P('#6b2f3a'))
    hand(cv, 0, 0, 1.0, 125, dn, 'back', 0.65)
    cv.restore()
    if lt <= 0.55:
        cv.save(); cv.translate(ax, ay); cv.scale(4.0, 4.0); acorn(cv, 0, 0, 1.0); cv.restore()
    grade(cv, '#f0d0b0', 0.55)
    cv.restore()
    vignette(cv, 0.6)


def shot_planting(cv, t, sh):
    lt = t - sh.start
    dawn = PAL['dawn']
    cv.drawPaint(P(shader=lin((0, 0), (0, 620), [(dawn[0], 1), (dawn[2], 1)])))
    cv.drawCircle(560, 560, 70, P('#fff2c8', 0.9, blur=20))
    cv.drawCircle(560, 560, 400, P('#ffd890', 0.3, blur=90))
    cv.drawRect(skia.Rect(0, 560, W, 640), P('#6a7a58', 0.7, blur=10))
    cv.drawRect(skia.Rect(0, 600, W, H), P(shader=lin((0, 600), (0, H), [('#5a3e2a', 1), ('#2e1e14', 1)])))
    r = np.random.default_rng(4)
    for i in range(160):
        x, y = r.uniform(0, W), r.uniform(620, H)
        rr = r.uniform(2, 7) * (0.5 + (y - 600) / 700)
        cv.drawCircle(x, y, rr, P('#7a5a3e' if i % 2 else '#24160e', 0.6))
    # hole and mound
    cv.drawOval(skia.Rect(270, 880, 450, 940), P('#1e120a'))
    dy = CH['young']
    press = ease(clamp((lt - 1.3) / 0.6))
    gone = ease(clamp((lt - 2.6) / 0.8))
    ay = lerp(760, 905, ease(clamp(lt / 1.2)))
    if press < 0.95:
        cv.save(); cv.translate(360, ay); cv.scale(4.0, 4.0); acorn(cv, 0, 0, 1.0); cv.restore()
    cv.drawOval(skia.Rect(250, 870 + 10 * press, 470, 950), P('#4a321e', press))
    for sgn in (-1, 1):
        hx_ = 360 + sgn * lerp(150, 90, press) + sgn * gone * 300
        hy_ = lerp(760, 880, press) - gone * 200
        cv.save(); cv.translate(hx_, hy_); cv.scale(3.2, 3.2)
        cv.drawPath(tapered([(sgn * 60, -70), (sgn * 30, -36), (0, 0)], 30, 26), P('#7a876a'))
        hand(cv, 0, 0, 1.0, 90 - sgn * 30, dy, 'back', 0.6, flip=(sgn > 0))
        cv.restore()
    sprout = ease(clamp((lt - 3.6) / 2.2))
    if sprout > 0:
        sx, sy = 360, 900
        hgt = 160 * sprout
        cv.drawPath(tapered([(sx, sy), (sx + 6, sy - hgt * 0.5), (sx - 2, sy - hgt)], 8, 4), P('#5d8a3a'))
        for sgn in (-1, 1):
            lk = clamp((sprout - 0.4) / 0.6)
            if lk > 0:
                cv.save(); cv.translate(sx - 2, sy - hgt + 10); cv.rotate(sgn * 40); cv.scale(lk, lk)
                cv.drawOval(skia.Rect(0 if sgn > 0 else -60, -14, 60 if sgn > 0 else 0, 14), P('#7ab04a'))
                cv.restore()
    vignette(cv, 0.45)


def shot_porch_dawn(cv, t, sh):
    lt = t - sh.start
    soft_bg(cv, porch_bg, t, 1.0)
    cv.saveLayer(None, None)
    k = ease(clamp(lt / 2.5))
    stn = live('nana', t, dict(gx=0.6, gy=-0.1, yaw=0.15, smile=0.4, lower=0.4, open_l=0.8, open_r=0.8, roll=4, light=(0.8, -0.5)))
    put(cv, 'nana', 235, 600, 1.5, stn, t)
    sty = live('young', t, dict(gx=0.7, gy=-0.1, yaw=0.2, smile=0.25, open_l=lerp(0.9, 0.5, k), open_r=lerp(0.9, 0.5, k),
                                roll=-11 * k, hx=-14 * k, hy=6 * k, light=(0.8, -0.5)))
    put(cv, 'young', 480, 650, 1.5, sty, t)
    # Nana's arm around her
    dn = CH['nana']
    cv.save(); cv.translate(480, 650); cv.scale(1.5, 1.5)
    cv.drawPath(tapered([(-150, 210), (-60, 175), (50, 150)], 34, 26), P('#6b2f3a'))
    hand(cv, 50, 150, 0.9, -20, dn, 'back', 0.5)
    cv.restore()
    # sapling in a pot, and a lantern
    cv.drawPath(poly([(560, 1060), (660, 1060), (645, 1170), (575, 1170)]), P('#a0583a'))
    cv.drawRect(skia.Rect(552, 1048, 668, 1066), P('#b8683e'))
    cv.drawPath(tapered([(610, 1050), (614, 990), (606, 930)], 6, 3), P('#5d8a3a'))
    for i, (dx, dy_, a) in enumerate(((-28, 960, -30), (26, 945, 30), (-22, 930, -50), (20, 925, 40))):
        cv.save(); cv.translate(608 + dx * 0.3, dy_); cv.rotate(a)
        cv.drawOval(skia.Rect(0 if dx > 0 else -34, -9, 34 if dx > 0 else 0, 9), P('#7ab04a'))
        cv.restore()
    lx, ly = 120, 1080
    cv.drawRect(skia.Rect(lx - 34, ly - 70, lx + 34, ly + 30), P('#2a2a2a', stroke=5))
    flick = 1 + 0.15 * math.sin(t * 13) + 0.08 * math.sin(t * 29)
    cv.drawCircle(lx, ly - 20, 80 * flick, P('#ffb050', 0.35, blur=30))
    cv.drawOval(skia.Rect(lx - 7 * flick, ly - 44 * flick, lx + 7 * flick, ly), P('#ffd070'))
    cv.drawOval(skia.Rect(lx - 3, ly - 26, lx + 3, ly - 2), P('#fff6d0'))
    grade(cv, '#ffe6c8', 0.5)
    cv.restore()
    cv.drawPaint(P(shader=rad((700, 200), 800, [('#ffd890', 0.4), ('#ffd890', 0.0)]), blend=skia.BlendMode.kScreen))
    vignette(cv, 0.45)


def end_card(cv, t):
    a = clamp((t - (TL.E['N13'] + 0.3)) / 0.8)
    if a <= 0:
        return
    cv.drawRect(skia.Rect(0, 760, W, 1000), P('#000000', 0.35 * a, blur=40))
    text_center(cv, 'Keep the fire lit.', 870, 58, FONT_TI, '#fff4e0', a, 0.8)
    text_center(cv, 'PSALM 22', 930, 24, FONT_C, '#f6e0b8', a * 0.9, 0.7)

# ------------------------------------------------------------- dispatcher ---

SETUPS = {
    'open': lambda cv, t, sh: golgotha(cv, t, _as(sh, 'open')),
    'golgotha': golgotha,
    'mockers': shot_mockers,
    'mary_cu': shot_mary_cu,
    'magdalene_cu': shot_magdalene_cu,
    'john_cu': shot_john_cu,
    'jesus_low': shot_jesus,
    'jesus_cu': shot_jesus,
    'group3': shot_group3,
    'centurion_cu': shot_centurion,
    'flashback': shot_flashback,
    'phone_cu': shot_phone_cu,
    'porch_two': shot_porch_two,
    'nana_cu': shot_nana_cu,
    'young_cu': shot_young_cu,
    'acorn_hands': shot_acorn_hands,
    'planting': shot_planting,
    'porch_dawn': shot_porch_dawn,
}


def _as(sh, variant):
    sh.variant = variant
    return sh


SURF = skia.Surface(W, H)


def render_frame(t):
    cv = SURF.getCanvas()
    cv.clear(skia.Color(0, 0, 0))
    sh = TL.shot_at(t)
    SETUPS[sh.setup](cv, t, sh)
    caption(cv, t)
    return SURF.makeImageSnapshot()
