"""Character designs: hair, veils, beards, helmets, clothing, hands."""
import math
import numpy as np
import skia
from rig import (P, lin, rad, smooth, poly, bez, qbez, tapered, mix, lerp, clamp, ease,
                 hp, Design, Face)


def H(f, pts, follow=1.0):
    return [hp(f, x, y, follow) for x, y in pts]


def mirror(pts):
    return [(-x, y) for x, y in pts]


def strands(cv, f, lines, c, a, w, follow=1.0):
    for pts in lines:
        cv.drawPath(smooth(H(f, pts, follow), False), P(c, a, stroke=w))

# ------------------------------------------------------------------ bodies ---

def neck(cv, d, top=28, bottom=112, w0=17, w1=22, strain=0.0, fade=False):
    p = poly([(-w0, top), (w0, top), (w1, bottom), (-w1, bottom)])
    if fade:
        cv.drawPath(p, P(shader=lin((0, bottom - 34), (0, bottom), [(d.skin, 1.0), (d.skin, 0.0)])))
    else:
        p = poly([(-w0, top), (w0, top), (w1 + 2, bottom + 40), (-w1 - 2, bottom + 40)])
        cv.drawPath(p, P(d.skin))
    cv.drawPath(p, P(shader=lin((0, top), (0, top + 40), [(d.shade, 0.75), (d.shade, 0.0)])))
    if strain > 0:
        for s in (-1, 1):
            cv.drawPath(tapered(qbez((s * 14, 40), (s * 10, 70), (s * 4, 104), 10), 3, 1.5),
                        P(d.shade, 0.45 * strain, blur=1))
            cv.drawPath(tapered(qbez((s * 15, 42), (s * 11, 72), (s * 5, 104), 10), 1.2, 0.5),
                        P(d.hi, 0.35 * strain))


def torso_path(sw=108, top=100, nw=24, dip=16, bottom=520):
    pts = [(-nw, top - 4), (-sw * 0.5, top + 4), (-sw * 0.88, top + 16), (-sw * 1.02, top + 44),
           (-sw * 1.08, top + 120), (-sw * 1.12, bottom), (sw * 1.12, bottom), (sw * 1.08, top + 120),
           (sw * 1.02, top + 44), (sw * 0.88, top + 16), (sw * 0.5, top + 4), (nw, top - 4)]
    p = smooth(pts, False, 0.5)
    p.quadTo(0, top + dip * 2, -nw, top - 4)
    p.close()
    return p


def robe(cv, d, color, shade, top=100, sw=108, dip=16, folds=True):
    p = torso_path(sw, top, 24, dip)
    cv.drawPath(p, P(color))
    cv.save()
    cv.clipPath(p, doAntiAlias=True)
    cv.drawPaint(P(shader=lin((-sw, 0), (sw, 0), [(shade, 0.0), (shade, 0.0), (shade, 0.6)], [0, 0.45, 1])))
    if folds:
        for x0, x1, a in ((-60, -75, 0.35), (-25, -32, 0.25), (30, 40, 0.3), (70, 82, 0.35)):
            cv.drawPath(tapered(qbez((x0, top + 40), (x0 - 8, top + 140), (x1, top + 380), 12), 0.5, 6),
                        P(shade, a, blur=3))
    cv.drawPath(tapered(qbez((-24, top - 2), (0, top + dip * 2 + 4), (24, top - 2), 12), 4, 4, 7), P(shade, 0.35, blur=2))
    cv.restore()

# -------------------------------------------------------------------- hands ---

def hand(cv, x, y, s, ang, d, pose='back', curl=0.0, flip=False, t=0.0):
    """Stylised hand.  Local frame: wrist at origin, fingers toward +x."""
    cv.save()
    cv.translate(x, y)
    cv.rotate(ang)
    cv.scale(s * 0.95, s * (-1 if flip else 1) * 0.95)
    skin, sh = d.skin, d.shade
    edge = P(sh, 0.45, stroke=0.9)
    # fingers: (base y, length, fan angle)
    fingers = [(-10.5, 29, -0.10), (-3.6, 32, -0.03), (3.4, 30, 0.04), (10.0, 23, 0.12)]
    c = clamp(curl)
    for by, L, fa in fingers:
        L *= 1 - 0.28 * c
        b = np.array([31.0, by])
        dirv = np.array([math.cos(fa), math.sin(fa)])
        mid = b + dirv * L * 0.5
        a2 = fa + c * 1.35
        tip = mid + np.array([math.cos(a2), math.sin(a2)]) * L * 0.5
        pts = qbez(tuple(b), tuple(mid), tuple(tip), 9)
        w0, w1 = 8.6, 7.0
        cv.drawPath(tapered(pts, w0, w1), P(skin))
        cv.drawPath(tapered(pts, w0, w1), edge)
        cv.drawCircle(*tip, w1 / 2, P(skin))
        if pose == 'back':
            nail = tip - (tip - mid) / (np.linalg.norm(tip - mid) + 1e-6) * 3.2
            cv.drawOval(skia.Rect(nail[0] - 2.6, nail[1] - 2.0, nail[0] + 2.6, nail[1] + 2.0), P(d.hi, 0.45))
            cv.drawLine(mid[0] - 1, mid[1], mid[0] + 1.2, mid[1], P(sh, 0.4, stroke=0.8))
    # thumb
    th = qbez((8, -11), (22, -21 - 4 * (1 - c)), (33 - 6 * c, -19 + 6 * c), 9)
    cv.drawPath(tapered(th, 11, 8), P(skin))
    cv.drawPath(tapered(th, 11, 8), edge)
    cv.drawCircle(*th[-1], 4, P(skin))
    # palm / back of hand
    body = smooth([(-2, -9), (14, -12.5), (32, -14.5), (37.5, -6), (37.5, 6), (32, 14), (14, 13), (-2, 9)], True, 0.6)
    cv.drawPath(body, P(skin))
    if pose == 'palm':
        cv.drawPath(body, P(shader=lin((0, -14), (0, 14), [(d.hi, 0.25), (sh, 0.15)])))
        cv.drawPath(smooth([(10, -5), (20, -2), (30, 5)], False), P(sh, 0.4, stroke=0.9))
        cv.drawPath(smooth([(12, 8), (22, 3), (31, -8)], False), P(sh, 0.35, stroke=0.9))
    else:
        cv.drawPath(body, P(shader=lin((0, -14), (0, 14), [(d.hi, 0.3), (sh, 0.3)])))
        for by, _, _ in fingers:
            cv.drawCircle(31, by, 2.4, P(d.hi, 0.14, blur=1))
        cv.drawPath(smooth([(6, -4), (20, -6), (30, -8)], False), P(sh, 0.18, stroke=1.2))
    cv.drawPath(body, edge)
    cv.restore()


def sleeve(cv, x0, y0, x1, y1, w0, w1, color, shade):
    pts = [(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + 6), (x1, y1)]
    path = tapered(qbez(*pts, 10), w0, w1)
    cv.drawPath(path, P(color))
    cv.drawPath(path, P(shade, 0.4, stroke=1.2))

# ------------------------------------------------------------------- JESUS ---

def make_jesus():
    d = Design(skin='#ad7653', shade='#6f4430', hi='#d8a07a', lip='#8e5046', iris='#2e1c10',
               brow='#2b1a10', lash='#1a100a', blush='#b24a3a', age=0.25, jaw=1.02, chin=66,
               ears=False, brow_w=3.4)
    HAIR, HAIR_HI = '#33201a', '#5a3a28'

    def back(cv, f, st, t):
        pts = [(0, -86), (38, -80), (58, -58), (63, -20), (63, 20), (66, 60), (72, 105), (80, 150),
               (58, 168), (30, 156), (-30, 156), (-58, 168), (-80, 150), (-72, 105), (-66, 60),
               (-63, 20), (-63, -20), (-58, -58), (-38, -80)]
        cv.drawPath(smooth(H(f, pts, 0.6)), P(mix(HAIR, '#000000', 0.25)))

    def body(cv, f, st, t):
        sk, sh = d.skin, d.shade
        lift = st.get('arm_lift', 0.0)
        pts = [(-22, 92), (-62, 102), (-100, 104 - lift * 6), (-180, 70 - lift * 10), (-430, -20 - lift * 10),
               (-430, 34 - lift * 10), (-190, 128 - lift * 6), (-112, 168), (-100, 250), (-96, 520),
               (96, 520), (100, 250), (112, 168), (190, 128 - lift * 6), (430, 34 - lift * 10),
               (430, -20 - lift * 10), (180, 70 - lift * 10), (100, 104 - lift * 6), (62, 102), (22, 92)]
        neck(cv, d, 26, 124, 18, 26, 0, fade=True)
        p = smooth(pts, True, 0.35)
        cv.drawPath(p, P(sk))
        cv.save()
        cv.clipPath(p, doAntiAlias=True)
        cv.drawPaint(P(shader=lin((-120, 0), (140, 60), [(d.hi, 0.25), (sh, 0.0), (sh, 0.55)], [0, 0.45, 1])))
        exp = st['breath']
        # collarbones, chest, ribs (no wounds)
        for s in (-1, 1):
            cv.drawPath(tapered(qbez((s * 16, 104), (s * 45, 98), (s * 82, 106), 10), 2.4, 0.6), P(sh, 0.45, blur=1.2))
            cv.drawPath(tapered(qbez((s * 6, 150 + exp), (s * 50, 176 + exp), (s * 92, 150), 12), 4, 1),
                        P(sh, 0.35, blur=2.5))
            for k in range(3):
                y = 205 + k * 26 + exp * 2
                cv.drawPath(tapered(qbez((s * 40, y), (s * 66, y + 6), (s * 88, y - 4), 8), 2.5, 0.5),
                            P(sh, 0.18 + 0.05 * k, blur=2))
            cv.drawPath(tapered(qbez((s * 104, 106), (s * 150, 92), (s * 230, 72), 10), 6, 2), P(sh, 0.3, blur=4))
            cv.drawPath(tapered(qbez((s * 110, 160), (s * 160, 140), (s * 260, 106), 10), 5, 2), P(sh, 0.35, blur=4))
        cv.drawLine(0, 120, 0, 240, P(sh, 0.3, stroke=2.5, blur=2))
        cv.drawOval(skia.Rect(-26, 96, 26, 122), P(sh, 0.35, blur=5))
        cv.restore()
        if st['strain'] > 0:
            neck(cv, d, 26, 112, 18, 24, st['strain'], fade=True)

    def front(cv, f, st, t):
        # curtains of hair
        L = [(-3, -73), (-25, -71), (-45, -59), (-56, -34), (-59, -4), (-57, 30), (-61, 70), (-68, 112),
             (-64, 140), (-56, 146), (-50, 120), (-47, 82), (-46, 46), (-48, 12), (-47, -20), (-39, -44),
             (-23, -60), (-6, -66)]
        for side in (-1, 1):
            pts = L if side < 0 else mirror(L)
            path = smooth(H(f, pts))
            cv.drawPath(path, P(HAIR))
            cv.save(); cv.clipPath(path, doAntiAlias=True)
            cv.drawPaint(P(shader=lin((0, -70), (0, 140), [(HAIR_HI, 0.35), (HAIR, 0.0), ('#000000', 0.25)])))
            sg = side
            strands(cv, f, [[(sg * 8, -68), (sg * 30, -60), (sg * 48, -36), (sg * 53, 0), (sg * 54, 40)],
                            [(sg * 14, -66), (sg * 40, -50), (sg * 51, -20), (sg * 52, 20), (sg * 58, 80), (sg * 60, 120)],
                            [(sg * 50, 30), (sg * 54, 70), (sg * 62, 110)]], '#1a100a', 0.45, 1.3)
            strands(cv, f, [[(sg * 20, -64), (sg * 42, -46), (sg * 54, -10)]], HAIR_HI, 0.5, 1.0)
            cv.restore()
        # crown of thorns: a thin woven ring (no blood)
        ring = [(-58, -40), (-40, -52), (-20, -57), (0, -59), (20, -57), (40, -52), (58, -40)]
        R = H(f, ring)
        for k, (a, ph) in enumerate(((2.2, 0), (2.0, 2.1), (1.8, 4.0))):
            pts = []
            for i in range(40):
                u = i / 39
                idx = u * (len(R) - 1)
                j = min(int(idx), len(R) - 2)
                fr = idx - j
                x = R[j][0] + (R[j + 1][0] - R[j][0]) * fr
                y = R[j][1] + (R[j + 1][1] - R[j][1]) * fr + a * math.sin(u * 23 + ph)
                pts.append((x, y))
            cv.drawPath(smooth(pts, False), P('#3a2a1c' if k != 1 else '#55402a', 0.95, stroke=1.6))
        for i in range(12):
            u = (i + 0.5) / 12
            idx = u * (len(R) - 1)
            j = min(int(idx), len(R) - 2)
            fr = idx - j
            x = R[j][0] + (R[j + 1][0] - R[j][0]) * fr
            y = R[j][1] + (R[j + 1][1] - R[j][1]) * fr
            dx = 3.2 * (1 if i % 2 else -1)
            cv.drawLine(x, y, x + dx, y - 4.5, P('#2a1e14', 0.9, stroke=1.0))

    def beard(cv, f, st, t):
        outer = [(-51, 2), (-53, 30), (-45, 56), (-28, 74), (0, 82), (28, 74), (45, 56), (53, 30), (51, 2)]
        inner = [(48, 10), (42, 26), (32, 37), (23, 44), (15, 53), (0, 55), (-15, 53), (-23, 44), (-32, 37),
                 (-42, 26), (-48, 10)]
        pts = H(f, outer) + [f.pr(x, y + (f.jawdrop * 0.9 if y > 44 else 0), 4) for x, y in inner]
        path = smooth(pts, True, 0.45)
        cv.drawPath(path, P(mix(HAIR, '#000000', 0.05), blur=1.2))
        cv.drawPath(path, P(mix(HAIR, d.skin, 0.25), 0.6, stroke=2.5, blur=2))
        cv.save(); cv.clipPath(path, doAntiAlias=True)
        for i in range(14):
            x = -44 + i * 6.8
            strands(cv, f, [[(x, 30), (x * 0.92, 52), (x * 0.7, 74)]], HAIR_HI if i % 3 == 0 else '#160d08', 0.45, 1.0)
        cv.restore()

    def mustache(cv, f, st, t):
        m = [(0, 30), (9, 29), (17, 33), (21, 43), (17, 42), (10, 36.5), (0, 35), (-10, 36.5), (-17, 42),
             (-21, 43), (-17, 33), (-9, 29)]
        pts = [f.pr(x, y + (f.st['m_open'] * 1.5 if abs(x) > 15 else 0), 9) for x, y in m]
        cv.drawPath(smooth(pts, True, 0.4), P(HAIR))
        cv.drawPath(smooth([f.pr(-14, 33, 9), f.pr(0, 31.5, 9), f.pr(14, 33, 9)], False), P(HAIR_HI, 0.5, stroke=1))

    d.layers_back = [back]
    d.layers_body = [body]
    d.layers_mid = [beard]
    d.layers_over_mouth = [mustache]
    d.layers_front = [front]
    return d

# -------------------------------------------------------------------- MARY ---

VEIL_IN = [(0, -60), (-28, -57), (-46, -42), (-53, -14), (-54, 18), (-50, 44), (-42, 62), (-36, 90), (-34, 130), (-32, 300)]
VEIL_OUT = [(-36, 300), (-150, 300), (-122, 170), (-98, 110), (-82, 60), (-76, 10), (-72, -40), (-56, -78), (-30, -94), (0, -98)]


def veil_path(f, inset=0.0, out_scale=1.0):
    inner = [(x * (1 - inset), y + (inset * 40 if y < -40 else 0)) for x, y in VEIL_IN]
    left = [(x * out_scale, y) for x, y in VEIL_OUT] + inner[::-1]
    pts_left = H(f, left)
    pts_right = H(f, mirror(left))
    # build one path: left outer up to top, across to right outer down, right inner up, left inner down
    p = skia.Path()
    lo = H(f, [(x * out_scale, y) for x, y in VEIL_OUT])
    li = H(f, inner)
    ro = H(f, mirror([(x * out_scale, y) for x, y in VEIL_OUT]))
    ri = H(f, mirror(inner))
    pts = lo + ro[::-1][1:] + ri[::-1] + li[1:]
    return smooth(pts, True, 0.4), li, ri


def make_mary():
    d = Design(skin='#c08a66', shade='#83553c', hi='#e6b690', lip='#a0574e', iris='#3a2416',
               brow='#3a2416', lash='#1e120c', blush='#c25a48', fem=1.0, age=0.45, jaw=0.94, chin=62,
               ears=False, brow_w=2.6, eye_w=19.5, eye_h=9.4)
    BLUE, BLUE_D, BLUE_L = '#2c4677', '#18284a', '#4d6ba3'

    def back(cv, f, st, t):
        pts = [(0, -100), (60, -86), (84, -40), (92, 20), (108, 90), (140, 170), (170, 320), (-170, 320),
               (-140, 170), (-108, 90), (-92, 20), (-84, -40), (-60, -86)]
        cv.drawPath(smooth(H(f, pts, 0.5)), P(BLUE_D))

    def body(cv, f, st, t):
        neck(cv, d, 28, 118, 16, 21)
        robe(cv, d, '#7c4646', '#3e1e20', top=104, sw=100, dip=14)
        # mantle over shoulders
        for s in (-1, 1):
            pts = [(s * 40, 96), (s * 92, 104), (s * 120, 150), (s * 132, 320), (s * 70, 320), (s * 52, 200), (s * 40, 130)]
            p = smooth(pts, True, 0.4)
            cv.drawPath(p, P(BLUE))
            cv.drawPath(p, P(shader=lin((s * 40, 0), (s * 130, 0), [(BLUE_L, 0.25), (BLUE_D, 0.6)])))
            cv.drawPath(tapered(qbez((s * 60, 140), (s * 70, 220), (s * 80, 320), 10), 1, 6), P(BLUE_D, 0.5, blur=2))

    def front(cv, f, st, t):
        # dark hair under the veil
        for s in (-1, 1):
            hpts = [(0, -60), (s * 18, -59), (s * 36, -50), (s * 47, -34), (s * 44, -30), (s * 30, -45), (s * 12, -51), (0, -52)]
            cv.drawPath(smooth(H(f, hpts)), P('#2a1a12'))
        cream, _, _ = veil_path(f, inset=0.06)
        cv.drawPath(cream, P('#e3d6bd'))
        cv.drawPath(cream, P('#a89878', 0.6, stroke=1))
        vp, li, ri = veil_path(f)
        cv.drawPath(vp, P(BLUE))
        cv.save(); cv.clipPath(vp, doAntiAlias=True)
        cv.drawPaint(P(shader=lin((0, -100), (0, 300), [(BLUE_L, 0.35), (BLUE, 0.0), (BLUE_D, 0.5)], [0, 0.4, 1])))
        for s in (-1, 1):
            strands(cv, f, [[(s * 66, -60), (s * 74, -10), (s * 80, 60), (s * 100, 150)],
                            [(s * 58, 20), (s * 66, 80), (s * 70, 180)]], BLUE_D, 0.6, 3.0, 0.5)
        cv.restore()
        cv.drawPath(smooth(li, False), P(BLUE_L, 0.9, stroke=1.6))
        cv.drawPath(smooth(ri, False), P(BLUE_L, 0.9, stroke=1.6))

    d.layers_back = [back]
    d.layers_body = [body]
    d.layers_front = [front]
    return d

# --------------------------------------------------------------- MAGDALENE ---

def make_magdalene():
    d = Design(skin='#b98264', shade='#7a4c36', hi='#e0ae8a', lip='#a24e4c', iris='#4a3a1c',
               brow='#3a1e14', lash='#1e100a', blush='#c45446', fem=1.0, age=0.05, jaw=0.92, chin=61,
               ears=False, brow_w=2.5, eye_w=20.0, eye_h=9.6)
    HAIR, HAIR_HI = '#4a2218', '#7a3e28'
    SCARF, SCARF_D, SCARF_L = '#8e3e2c', '#5a2218', '#b0583e'

    def back(cv, f, st, t):
        pts = [(0, -96), (60, -82), (84, -36), (90, 20), (104, 90), (130, 170), (150, 320), (-150, 320),
               (-130, 170), (-104, 90), (-90, 20), (-84, -36), (-60, -82)]
        cv.drawPath(smooth(H(f, pts, 0.5)), P(SCARF_D))
        hpts = [(0, -84), (50, -74), (66, -40), (68, 10), (70, 70), (78, 130), (40, 150), (-40, 150),
                (-78, 130), (-70, 70), (-68, 10), (-66, -40), (-50, -74)]
        cv.drawPath(smooth(H(f, hpts, 0.6)), P(mix(HAIR, '#000000', 0.3)))

    def body(cv, f, st, t):
        neck(cv, d, 28, 118, 15, 20)
        robe(cv, d, '#6e5c48', '#3a2c20', top=104, sw=98, dip=18)
        pts = [(-30, 100), (-96, 108), (-118, 160), (-126, 320), (-20, 320), (40, 200), (60, 130), (30, 112)]
        p = smooth(pts, True, 0.4)
        cv.drawPath(p, P(SCARF))
        cv.drawPath(p, P(shader=lin((-120, 0), (60, 200), [(SCARF_D, 0.6), (SCARF_L, 0.15)])))
        cv.drawPath(tapered(qbez((-80, 140), (-40, 220), (10, 300), 10), 2, 7), P(SCARF_D, 0.5, blur=2))

    def front(cv, f, st, t):
        for side in (-1, 1):
            L = [(0, -64), (-22, -62), (-40, -52), (-53, -30), (-58, 0), (-58, 36), (-64, 76), (-74, 118),
                 (-66, 140), (-56, 124), (-50, 90), (-47, 50), (-49, 14), (-48, -16), (-40, -40), (-22, -54), (-4, -58)]
            pts = L if side < 0 else mirror(L)
            if side > 0:
                pts = pts[:7] + [(68, 120), (52, 190), (38, 220), (32, 196), (44, 140), (50, 96)] + pts[11:]
            path = smooth(H(f, pts))
            cv.drawPath(path, P(HAIR))
            cv.save(); cv.clipPath(path, doAntiAlias=True)
            cv.drawPaint(P(shader=lin((0, -70), (0, 200), [(HAIR_HI, 0.4), (HAIR, 0.0), ('#000000', 0.3)])))
            sg = side
            strands(cv, f, [[(sg * 8, -61), (sg * 32, -54), (sg * 50, -30), (sg * 54, 4), (sg * 56, 40), (sg * 62, 80)],
                            [(sg * 18, -60), (sg * 44, -40), (sg * 54, -8), (sg * 58, 50), (sg * 66, 110)]],
                    '#2a120c', 0.5, 1.2)
            strands(cv, f, [[(sg * 14, -60), (sg * 38, -48), (sg * 52, -18)]], HAIR_HI, 0.6, 1.1)
            cv.restore()
        # scarf over the crown, set back on the head
        sc = [(-70, 10), (-74, -30), (-64, -62), (-38, -86), (0, -94), (38, -86), (64, -62), (74, -30), (70, 10),
              (60, -10), (58, -44), (40, -66), (0, -74), (-40, -66), (-58, -44), (-60, -10)]
        path = smooth(H(f, sc, 0.7))
        cv.drawPath(path, P(SCARF))
        cv.save(); cv.clipPath(path, doAntiAlias=True)
        cv.drawPaint(P(shader=lin((0, -94), (0, 10), [(SCARF_L, 0.4), (SCARF_D, 0.4)])))
        strands(cv, f, [[(-50, -70), (0, -82), (50, -70)], [(-62, -40), (-50, -66)], [(62, -40), (50, -66)]], SCARF_D, 0.6, 2.2, 0.7)
        cv.restore()
        inner = H(f, [(-60, -10), (-58, -44), (-40, -66), (0, -74), (40, -66), (58, -44), (60, -10)], 0.7)
        cv.drawPath(smooth(inner, False), P(SCARF_L, 0.9, stroke=1.6))

    d.layers_back = [back]
    d.layers_body = [body]
    d.layers_front = [front]
    return d

# -------------------------------------------------------------------- JOHN ---

def curl_cap(cv, f, hairline, crown, color, hi, bumps=18, r=7.0, seed=1, follow=0.8):
    """Short curly hair: bumpy outline from hairline over crown."""
    pts = H(f, hairline + crown, follow)
    path = smooth(pts, True, 0.45)
    cv.drawPath(path, P(color))
    rng = np.random.default_rng(seed)
    cr = H(f, crown, follow)
    for i in range(len(cr) - 1):
        for k in range(3):
            u = (k + 0.5) / 3
            x = cr[i][0] + (cr[i + 1][0] - cr[i][0]) * u
            y = cr[i][1] + (cr[i + 1][1] - cr[i][1]) * u
            cv.drawCircle(x, y, r * rng.uniform(0.8, 1.15), P(color))
    cv.save(); cv.clipPath(path, doAntiAlias=True)
    for i in range(bumps * 3):
        x = rng.uniform(-60, 60); y = rng.uniform(-100, -20)
        X, Y = hp(f, x, y, follow)
        a0 = rng.uniform(0, 360)
        ov = skia.Rect(X - 4, Y - 3, X + 4, Y + 3)
        p = skia.Path(); p.addArc(ov, a0, 200)
        cv.drawPath(p, P(hi, 0.5, stroke=1.1))
    cv.restore()


def make_john():
    d = Design(skin='#b98058', shade='#7a4c33', hi='#e2ad84', lip='#9a5248', iris='#3a2414',
               brow='#22140c', lash='#160c08', blush='#bc5240', fem=0.0, age=0.0, jaw=1.03, chin=64,
               ears=True, brow_w=3.3, stubble=0.12)
    HAIR, HAIR_HI = '#22140c', '#4a3020'

    def back(cv, f, st, t):
        pts = [(-56, -10), (-62, -50), (-46, -82), (0, -94), (46, -82), (62, -50), (56, -10), (52, 20), (-52, 20)]
        cv.drawPath(smooth(H(f, pts, 0.6)), P(mix(HAIR, '#000000', 0.2)))

    def body(cv, f, st, t):
        neck(cv, d, 28, 118, 18, 23)
        robe(cv, d, '#59613f', '#2c3020', top=104, sw=110, dip=16)
        pts = [(30, 100), (100, 108), (122, 160), (130, 320), (10, 320), (-50, 200), (-60, 130), (-30, 110)]
        p = smooth(pts, True, 0.4)
        cv.drawPath(p, P('#7a5634'))
        cv.drawPath(p, P(shader=lin((120, 0), (-60, 200), [('#3e2a18', 0.55), ('#a07a50', 0.1)])))

    def front(cv, f, st, t):
        hairline = [(-50, -14), (-50, -30), (-44, -46), (-28, -54), (-8, -56), (10, -57), (30, -54), (45, -46), (51, -30), (50, -14)]
        crown = [(56, -14), (60, -44), (48, -76), (22, -90), (-6, -92), (-30, -88), (-52, -72), (-60, -44), (-56, -14)]
        curl_cap(cv, f, hairline, crown, HAIR, HAIR_HI, seed=3)
        for s in (-1, 1):
            sb = H(f, [(s * 50, -24), (s * 52, -6), (s * 49, 6), (s * 46, -10), (s * 46, -24)])
            cv.drawPath(smooth(sb), P(HAIR, 0.85))

    d.layers_back = [back]
    d.layers_body = [body]
    d.layers_front = [front]
    return d

# ------------------------------------------------------------ ROMAN HELMET ---

def helmet(cv, f, st, t, crest=True, lift=0.0, crest_c='#a0261e'):
    cv.save()
    cv.translate(0, -lift * 70)
    cv.rotate(-lift * 8)
    IRON, IRON_D, IRON_L, BR = '#7c7568', '#3e3a34', '#c8c0ae', '#9a7a44'
    if crest:
        cr = [(-74, -70), (-66, -102), (-40, -124), (0, -132), (40, -124), (66, -102), (74, -70), (52, -86), (0, -100), (-52, -86)]
        path = smooth(H(f, cr, 0.4))
        cv.drawPath(path, P(crest_c))
        cv.save(); cv.clipPath(path, doAntiAlias=True)
        for i in range(30):
            a = -70 + i * 4.8
            x0, y0 = hp(f, a * 0.72, -88 + abs(a) * 0.15, 0.4)
            x1, y1 = hp(f, a * 1.02, -126 + abs(a) * 0.62, 0.4)
            cv.drawLine(x0, y0, x1, y1, P('#5a1410', 0.5, stroke=1.4))
        cv.restore()
        b = H(f, [(-10, -100), (10, -100), (8, -86), (-8, -86)], 0.4)
        cv.drawPath(poly(b), P(BR))
    # cheek guards
    for s in (-1, 1):
        g = H(f, [(s * 46, -36), (s * 58, -30), (s * 56, 10), (s * 48, 36), (s * 38, 30), (s * 40, 0), (s * 38, -30)])
        path = smooth(g, True, 0.4)
        cv.drawPath(path, P(IRON))
        cv.drawPath(path, P(shader=lin((s * 38, -30), (s * 58, 30), [(IRON_L, 0.35), (IRON_D, 0.5)])))
        cv.drawPath(path, P(IRON_D, 0.9, stroke=1.4))
        for yy in (-18, 6):
            x, y = hp(f, s * 48, yy)
            cv.drawCircle(x, y, 1.8, P(BR))
    dome = [(-62, -26), (-64, -50), (-54, -78), (-30, -94), (0, -98), (30, -94), (54, -78), (64, -50), (62, -26),
            (44, -36), (20, -42), (0, -43), (-20, -42), (-44, -36)]
    path = smooth(H(f, dome, 0.8), True, 0.4)
    cv.drawPath(path, P(IRON))
    cv.save(); cv.clipPath(path, doAntiAlias=True)
    lx = -20 + f.yaw * 40
    cv.drawPaint(P(shader=lin((0, -98), (0, -30), [(IRON_L, 0.5), (IRON, 0.0), (IRON_D, 0.6)], [0, 0.4, 1])))
    cv.drawOval(skia.Rect(lx - 18, -92, lx + 8, -70), P('#ffffff', 0.35, blur=6))
    cv.restore()
    cv.drawPath(path, P(IRON_D, 0.9, stroke=1.6))
    brow = H(f, [(-64, -30), (-40, -38), (0, -44), (40, -38), (64, -30)], 0.8)
    cv.drawPath(smooth(brow, False), P(BR, 1, stroke=4.5))
    cv.drawPath(smooth(brow, False), P('#e0c080', 0.5, stroke=1.2))
    cv.restore()


def make_centurion():
    d = Design(skin='#b07a58', shade='#70462e', hi='#d8a27c', lip='#93524a', iris='#2e2418',
               brow='#2a2420', lash='#14100c', blush='#b04a3a', fem=0.0, age=0.55, jaw=1.12, chin=67,
               ears=True, brow_w=3.8, stubble=0.35, stubble_c='#2e2622')
    CLOAK, CLOAK_D = '#8a2620', '#4a120e'

    def back(cv, f, st, t):
        pass

    def body(cv, f, st, t):
        neck(cv, d, 28, 118, 20, 25, st['strain'])
        robe(cv, d, '#6d6a62', '#2e2c28', top=106, sw=118, dip=12, folds=False)
        # lorica bands
        for i in range(6):
            y = 140 + i * 30
            cv.drawPath(smooth([(-120, y + 6), (0, y - 4), (120, y + 6)], False), P('#2e2c28', 0.8, stroke=2.2))
            cv.drawPath(smooth([(-118, y + 9), (0, y - 1), (118, y + 9)], False), P('#b0aa9c', 0.35, stroke=1.4))
        cv.drawPath(tapered(qbez((-20, 100), (0, 116), (20, 100), 8), 9, 9), P('#d8ccb0'))
        pts = [(-24, 98), (-110, 104), (-136, 150), (-140, 330), (-96, 330), (-80, 180), (-40, 124)]
        cv.drawPath(smooth(pts, True, 0.4), P(CLOAK))
        pts = [(24, 98), (110, 104), (136, 150), (140, 330), (96, 330), (90, 170), (52, 120)]
        cv.drawPath(smooth(pts, True, 0.4), P(mix(CLOAK, CLOAK_D, 0.4)))
        cv.drawCircle(-62, 118, 7, P('#b08a4a'))
        cv.drawCircle(-62, 118, 7, P('#5a4020', stroke=1.4))

    def hair(cv, f, st, t):
        hairline = [(-50, -16), (-50, -32), (-42, -46), (-24, -52), (0, -54), (24, -52), (42, -46), (50, -32), (50, -16)]
        crown = [(54, -16), (58, -44), (44, -72), (0, -84), (-44, -72), (-58, -44), (-54, -16)]
        pts = H(f, hairline + crown, 0.8)
        cv.drawPath(smooth(pts, True, 0.4), P('#34302c'))
        cv.drawPath(smooth(pts, True, 0.4), P(shader=lin((0, -84), (0, -16), [('#6a6660', 0.4), ('#000000', 0.0)])))

    def front(cv, f, st, t):
        h = st.get('helm', 1.0)
        if h > 0:
            helmet(cv, f, st, t, crest=True, lift=1 - h)

    def hands(cv, f, st, t):
        h = st.get('helm', 1.0)
        hu = st.get('helm_hands', 0.0)
        if hu > 0.01:
            # hands bring the helmet down to the chest
            y = lerp(330, -40, hu) if h > 0 else lerp(330, 170, hu)
            for s in (-1, 1):
                hand(cv, s * 62, y + 30, 0.95, -100 if s < 0 else -80, d, 'back', 0.9, flip=(s > 0))
        hc = st.get('helm_chest', 0.0)
        if hc > 0.01:
            cv.save(); cv.translate(0, lerp(420, 230, hc)); cv.scale(0.95, 0.95)
            ff = Face(d, dict(f.st, yaw=0.0, pitch=0.0, m_open=0.0))
            helmet(cv, ff, st, t, crest=True)
            cv.restore()
            for s in (-1, 1):
                hand(cv, s * 74, lerp(440, 250, hc), 0.95, -95 if s < 0 else -85, d, 'back', 0.7, flip=(s > 0))

    d.layers_back = [back]
    d.layers_body = [body]
    d.layers_front = [hair, front]
    d.layers_hands = [hands]
    return d

# ----------------------------------------------------------------- MOCKERS ---

def make_mocker1():
    """A passer-by: older man, plain head cloth, short grey beard."""
    d = Design(skin='#a87452', shade='#6c472f', hi='#d29e78', lip='#8a4c44', iris='#2e2016',
               brow='#8d877c', lash='#1a120c', blush='#a84a3a', fem=0.0, age=0.8, jaw=1.06, chin=65,
               ears=False, brow_w=4.0)
    CLOTH, CLOTH_D = '#8c7c5c', '#4e4230'

    def back(cv, f, st, t):
        pts = [(0, -100), (62, -86), (80, -40), (84, 20), (100, 90), (130, 160), (140, 320), (-140, 320),
               (-130, 160), (-100, 90), (-84, 20), (-80, -40), (-62, -86)]
        cv.drawPath(smooth(H(f, pts, 0.5)), P(CLOTH_D))

    def body(cv, f, st, t):
        neck(cv, d, 28, 118, 18, 23)
        robe(cv, d, '#5a4a3a', '#2a2018', top=104, sw=112, dip=12)
        for s in (-1, 1):
            cv.drawPath(smooth([(s * 36, 100), (s * 50, 200), (s * 54, 330)], False), P('#c8b890', 0.7, stroke=6))

    def beard(cv, f, st, t):
        G = '#b8b2a6'
        outer = [(-50, 4), (-52, 30), (-44, 58), (-26, 80), (0, 90), (26, 80), (44, 58), (52, 30), (50, 4)]
        inner = [(44, 10), (32, 22), (22, 33), (18, 44), (12, 52), (0, 54), (-12, 52), (-18, 44), (-22, 33), (-32, 22), (-44, 10)]
        pts = H(f, outer) + [f.pr(x, y + (f.jawdrop * 0.9 if y > 44 else 0), 4) for x, y in inner]
        path = smooth(pts, True, 0.45)
        cv.drawPath(path, P(G))
        cv.save(); cv.clipPath(path, doAntiAlias=True)
        for i in range(14):
            x = -44 + i * 6.8
            strands(cv, f, [[(x, 30), (x * 0.92, 56), (x * 0.7, 84)]], '#7a7468', 0.5, 1.0)
        cv.restore()

    def mustache(cv, f, st, t):
        m = [(0, 30), (10, 29), (19, 34), (22, 44), (17, 42), (10, 36.5), (0, 35), (-10, 36.5), (-17, 42), (-22, 44), (-19, 34), (-10, 29)]
        cv.drawPath(smooth([f.pr(x, y, 9) for x, y in m], True, 0.4), P('#a8a296'))

    def front(cv, f, st, t):
        # head cloth with a cord band
        pts = [(-76, 40), (-70, -20), (-60, -62), (-34, -86), (0, -92), (34, -86), (60, -62), (70, -20), (76, 40),
               (60, 30), (56, -10), (50, -34), (30, -46), (0, -50), (-30, -46), (-50, -34), (-56, -10), (-60, 30)]
        path = smooth(H(f, pts, 0.7))
        cv.drawPath(path, P(CLOTH))
        cv.save(); cv.clipPath(path, doAntiAlias=True)
        cv.drawPaint(P(shader=lin((0, -92), (0, 40), [('#b8a882', 0.4), (CLOTH_D, 0.5)])))
        strands(cv, f, [[(-60, 20), (-62, -30), (-40, -70)], [(60, 20), (62, -30), (40, -70)]], CLOTH_D, 0.6, 2.4, 0.7)
        cv.restore()
        band = H(f, [(-56, -40), (-30, -52), (0, -56), (30, -52), (56, -40)], 0.7)
        cv.drawPath(smooth(band, False), P('#2a2018', 1, stroke=5))

    d.layers_back = [back]
    d.layers_body = [body]
    d.layers_mid = [beard]
    d.layers_over_mouth = [mustache]
    d.layers_front = [front]
    return d


def make_mocker2():
    """A young Roman soldier."""
    d = Design(skin='#c08a66', shade='#7e523a', hi='#e6b48e', lip='#9a5650', iris='#3a3020',
               brow='#3a2a1c', lash='#1a120c', blush='#c05040', fem=0.0, age=0.05, jaw=1.06, chin=64,
               ears=True, brow_w=3.4, stubble=0.18)

    def body(cv, f, st, t):
        neck(cv, d, 28, 118, 18, 23)
        robe(cv, d, '#8e3a2a', '#4a1a12', top=104, sw=110, dip=10, folds=False)
        arm = torso_path(92, 118, 30, 6)
        cv.drawPath(arm, P('#5e5a52'))
        cv.save(); cv.clipPath(arm, doAntiAlias=True)
        for i in range(7):
            y = 132 + i * 30
            cv.drawPath(smooth([(-110, y + 6), (0, y - 4), (110, y + 6)], False), P('#2e2c28', 0.9, stroke=2.5))
            cv.drawPath(smooth([(-110, y + 10), (0, y), (110, y + 10)], False), P('#b0aa9c', 0.45, stroke=2))
        cv.drawPaint(P(shader=lin((-100, 0), (100, 0), [('#ffffff', 0.12), ('#000000', 0.35)])))
        cv.restore()
        cv.drawPath(tapered(qbez((-24, 100), (0, 114), (24, 100), 8), 9, 9), P('#d8ccb0'))

    def front(cv, f, st, t):
        hairline = [(-50, -16), (-48, -34), (-30, -48), (0, -52), (30, -48), (48, -34), (50, -16)]
        crown = [(54, -16), (58, -44), (40, -76), (0, -86), (-40, -76), (-58, -44), (-54, -16)]
        cv.drawPath(smooth(H(f, hairline + crown, 0.8)), P('#3a2a1c'))
        helmet(cv, f, st, t, crest=False)

    d.layers_body = [body]
    d.layers_front = [front]
    return d

# ------------------------------------------------------------------ MODERN ---

def make_young():
    d = Design(skin='#7e4d35', shade='#4c2c1d', hi='#a8735a', lip='#6c3934', iris='#22140c',
               brow='#160d08', lash='#0e0805', blush='#9a3a30', fem=1.0, age=0.0, jaw=0.94, chin=61,
               ears=True, brow_w=2.7, eye_w=20.5, eye_h=9.8)
    HAIR, HAIR_HI = '#1a110c', '#3e2a20'
    HOOD, HOOD_D, HOOD_L = '#7a876a', '#46503c', '#9fac8c'

    def back(cv, f, st, t):
        # puff
        cx, cy = hp(f, 0, -100, 0.5)
        cv.drawCircle(cx, cy + 4, 50, P(HAIR))
        rng = np.random.default_rng(5)
        for i in range(40):
            a = rng.uniform(0, 6.28); r = rng.uniform(30, 52)
            cv.drawCircle(cx + math.cos(a) * r, cy + 4 + math.sin(a) * r, rng.uniform(5, 9), P(HAIR))
        for i in range(30):
            a = rng.uniform(0, 6.28); r = rng.uniform(5, 44)
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
            p = skia.Path(); p.addArc(skia.Rect(x - 4, y - 3, x + 4, y + 3), rng.uniform(0, 360), 180)
            cv.drawPath(p, P(HAIR_HI, 0.6, stroke=1.2))

    def body(cv, f, st, t):
        neck(cv, d, 28, 118, 15, 19)
        # hood bunched behind the neck
        hood = [(-34, 70), (-74, 84), (-96, 110), (0, 128), (96, 110), (74, 84), (34, 70), (0, 92)]
        cv.drawPath(smooth(hood, True, 0.4), P(HOOD_D))
        p = torso_path(104, 106, 22, 10)
        cv.drawPath(p, P(HOOD))
        cv.save(); cv.clipPath(p, doAntiAlias=True)
        cv.drawPaint(P(shader=lin((-110, 0), (110, 0), [(HOOD_L, 0.25), (HOOD_D, 0.0), (HOOD_D, 0.55)], [0, 0.5, 1])))
        for s in (-1, 1):
            cv.drawPath(smooth([(s * 10, 122), (s * 14, 190), (s * 12, 240)], False), P('#e8e2d4', 0.9, stroke=2.4))
            cv.drawCircle(s * 12, 244, 3.2, P('#c8c0b0'))
        cv.drawPath(tapered(qbez((-90, 112), (0, 140), (90, 112), 12), 10, 10, 14), P(HOOD_D, 0.8))
        cv.restore()

    def front(cv, f, st, t):
        hairline = [(-50, -10), (-49, -30), (-42, -46), (-24, -55), (0, -58), (24, -55), (42, -46), (49, -30), (50, -10)]
        crown = [(53, -10), (57, -44), (46, -74), (20, -90), (-20, -90), (-46, -74), (-57, -44), (-53, -10)]
        pts = H(f, hairline + crown, 0.8)
        path = smooth(pts, True, 0.45)
        cv.drawPath(path, P(HAIR))
        cv.save(); cv.clipPath(path, doAntiAlias=True)
        for i in range(9):
            x = -40 + i * 10
            strands(cv, f, [[(x, -50 + abs(x) * 0.1), (x * 0.6, -74), (x * 0.2, -92)]], HAIR_HI, 0.6, 1.0)
        cv.restore()
        for s in (-1, 1):
            e = H(f, [(s * 40, -46), (s * 34, -44), (s * 36, -40), (s * 42, -41)])
            cv.drawPath(smooth(e, False), P(HAIR, 0.9, stroke=1.2))
            # earrings
            vis = math.cos(math.asin(0.93) + f.yaw * s)
            if vis > 0.05:
                ex, ey = hp(f, s * 52, 16)
                cv.drawCircle(ex, ey + 4, 3.6, P('#d8b24a', stroke=1.4))

    d.layers_back = [back]
    d.layers_body = [body]
    d.layers_front = [front]
    return d


def make_nana():
    d = Design(skin='#6e4330', shade='#43261a', hi='#996452', lip='#5c3330', iris='#24160e',
               brow='#9e9890', lash='#140c08', blush='#8a3a2e', fem=0.8, age=0.95, jaw=1.0, chin=63,
               ears=True, brow_w=2.6, eye_w=19.0, eye_h=8.6)
    G, G_D, G_L = '#c9c4bb', '#8e887e', '#ece8e0'

    def back(cv, f, st, t):
        pts = [(-58, 0), (-66, -40), (-54, -80), (-20, -96), (20, -96), (54, -80), (66, -40), (58, 0)]
        cv.drawPath(smooth(H(f, pts, 0.6)), P(G_D))

    def body(cv, f, st, t):
        neck(cv, d, 28, 118, 16, 20)
        p = torso_path(108, 106, 22, 20)
        cv.drawPath(p, P('#e4dac8'))
        for s in (-1, 1):
            pts = [(s * 24, 102), (s * 70, 108), (s * 112, 140), (s * 124, 520), (s * 30, 520), (s * 26, 260), (s * 22, 150)]
            pp = smooth(pts, True, 0.35)
            cv.drawPath(pp, P('#6b2f3a'))
            cv.drawPath(pp, P(shader=lin((s * 20, 0), (s * 120, 0), [('#8a4452', 0.3), ('#3a141c', 0.5)])))
            for k in range(4):
                cv.drawCircle(s * 30, 200 + k * 46, 3.2, P('#d8c8a8'))
        # gold chain and small cross
        cv.drawPath(smooth([(-18, 104), (0, 150), (18, 104)], False), P('#c8a040', 0.9, stroke=1.2))
        cv.drawRect(skia.Rect(-1.6, 148, 1.6, 164), P('#d8b04a'))
        cv.drawRect(skia.Rect(-5, 152, 5, 155), P('#d8b04a'))

    def front(cv, f, st, t):
        hairline = [(-52, 0), (-52, -28), (-44, -44), (-26, -52), (0, -54), (26, -52), (44, -44), (52, -28), (52, 0)]
        crown = [(58, 0), (64, -40), (52, -74), (24, -92), (-24, -92), (-52, -74), (-64, -40), (-58, 0)]
        curl_cap(cv, f, hairline, crown, G, G_D, seed=8, r=8)
        # glasses
        for s in (-1, 1):
            ex, ey = f.pr(d.eye_x * s, d.eye_y + 1, 6)
            w = 15 * f.sx(d.eye_x * s)
            r = skia.RRect.MakeRectXY(skia.Rect(ex - w, ey - 11, ex + w, ey + 10), 7, 7)
            cv.drawRRect(r, P('#ffffff', 0.06))
            cv.save(); cv.clipRRect(r, doAntiAlias=True)
            cv.drawPath(poly([(ex - w, ey - 2), (ex - w * 0.3, ey - 11), (ex - w * 0.05, ey - 11), (ex - w * 0.75, ey + 1)]), P('#ffffff', 0.18))
            cv.restore()
            cv.drawRRect(r, P('#6a4a2a', 0.95, stroke=1.6))
            tx, ty = f.pr(s * 50, -2, 0)
            if math.cos(math.asin(0.93) + f.yaw * s) > 0.05:
                cv.drawLine(ex + s * w, ey - 6, tx, ty, P('#6a4a2a', 0.9, stroke=1.4))
        a = f.pr(-5, -1, 10); b = f.pr(5, -1, 10)
        cv.drawPath(smooth([a, ((a[0] + b[0]) / 2, a[1] - 3), b], False), P('#6a4a2a', stroke=1.5))

    d.layers_back = [back]
    d.layers_body = [body]
    d.layers_front = [front]
    return d


def make_young_mary():
    """Mary on the night of the birth (flashback)."""
    d = make_mary()
    d.age = 0.0
    d.skin, d.shade, d.hi = '#c8946e', '#8a5c40', '#ecc09a'
    return d


CAST = {
    'jesus': make_jesus, 'mary': make_mary, 'magdalene': make_magdalene, 'john': make_john,
    'centurion': make_centurion, 'mocker1': make_mocker1, 'mocker2': make_mocker2,
    'young': make_young, 'nana': make_nana, 'young_mary': make_young_mary,
}
