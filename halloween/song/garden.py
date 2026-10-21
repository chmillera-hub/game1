"""The moonlit garden behind the crooked house: the skeletons' dance floor."""
import math

import skia

import sets as S_
from gfx import H, W, Xf, clamp, fill, glow, lerp, lin_grad, noise1, poly, rad_grad, rng, smooth_path, spiral_pts, \
    stroke, open_path

GROUND_Y = 1150
MOUNDS = {"tibbs": (200, 1690), "rattles": (420, 1615), "femurella": (690, 1615), "clatter": (880, 1530)}
PUMPKINS = [(520, 1238, 30, 0.7), (150, 1330, 58, 1.0), (952, 1318, 52, 1.0), (70, 1760, 95, 1.0),
            (1020, 1800, 100, 1.0)]
FENCE_POST_CAT = (532, 1024)   # the cat perches on top of this fence post
HOUSE = (250, 1185, 0.6)
KITCHEN_WINDOW = (250 - 150 * 0.6, 1185 - 200 * 0.6)


def sky(c, t, dawn=0.0):
    top = (12, 16, 42)
    mid = (34, 58, 96)
    if dawn > 0:
        top = tuple(lerp(a, b, dawn) for a, b in zip(top, (70, 90, 150)))
        mid = tuple(lerp(a, b, dawn) for a, b in zip(mid, (250, 170, 120)))
    c.drawRect(skia.Rect.MakeLTRB(-600, -800, W + 600, GROUND_Y + 50),
               fill((0, 0, 0), 1.0, lin_grad((0, -200), (0, GROUND_Y), [top, mid])))
    rr = rng("song_stars")
    ts = math.floor(t * 2) / 2
    for _ in range(90):
        x, y = rr.uniform(-200, W + 200), rr.uniform(-300, 900)
        tw = 0.5 + 0.5 * math.sin(ts * rr.uniform(0.5, 1.5) + rr.uniform(0, 6))
        c.drawCircle(x, y, rr.uniform(1.0, 2.6), fill((235, 235, 255), (0.25 + 0.5 * tw) * (1 - dawn)))


def moon(c, t, dawn=0.0):
    S_.draw_moon(c, 760, 400, 205, a=1.0 - 0.6 * dawn)
    S_.draw_clouds(c, t, (-300, 150, W + 300, 800), (760, 400, 205))
    if dawn > 0:  # the sun peeks over the hills
        sy = lerp(GROUND_Y + 120, GROUND_Y - 60, dawn)
        glow(c, 540, sy, 700, (255, 190, 110), 0.7 * dawn)
        c.drawCircle(540, sy, 110, fill((255, 214, 120), dawn))


def backdrop_far(c, t, dawn=0.0):
    """Sky, moon and bats: drawn with camera parallax so close-ups keep the moon."""
    sky(c, t, dawn)
    moon(c, t, dawn)
    S_.draw_bats(c, t, (-100, 120, W + 100, 700), n=3, speed=0.8)


def backdrop_near(c, t, dawn=0.0, window=1.0, cat_on_fence=None):
    """Hills, house, tree and fence: these sit on the ground line, so no parallax."""
    # far hills
    c.drawPath(smooth_path([(-300, GROUND_Y + 40), (-300, GROUND_Y - 60), (200, GROUND_Y - 120), (600, GROUND_Y - 70),
                            (1000, GROUND_Y - 130), (1400, GROUND_Y - 60), (1400, GROUND_Y + 40)], closed=True),
               fill((16, 16, 34)))
    # the crooked house (same one as in TOO MOM) with the kitchen light on
    hx, hy, hs = HOUSE

    def sil(cc, wx, wy):
        pass
    S_.draw_house(c, hx, hy, hs, t, window, sil)
    S_.draw_tree(c, 980, GROUND_Y + 80, 0.95)
    # crooked fence
    for i in range(-2, 14):
        with Xf(c, i * 92 - 20, GROUND_Y + 10, rot=((i * 37) % 5 - 2) * 3):
            c.drawPath(poly([(-9, 0), (-9, -120), (0, -138), (9, -120), (9, 0)]), fill((10, 8, 18)))
    c.drawRect(skia.Rect.MakeLTRB(-400, GROUND_Y - 80, W + 400, GROUND_Y - 66), fill((10, 8, 18)))
    if cat_on_fence is not None:
        cat_on_fence(c)


def ground(c, t, freeze=False):
    c.drawRect(skia.Rect.MakeLTRB(-600, GROUND_Y, W + 600, H + 900),
               fill((0, 0, 0), 1.0, lin_grad((0, GROUND_Y), (0, H), [(30, 34, 40), (22, 20, 30), (12, 10, 18)])))
    rr = rng("grass")
    for i in range(70):  # tufts of dark grass
        x = rr.uniform(-100, W + 100)
        y = GROUND_Y + (rr.uniform(0, 1) ** 1.6) * (H - GROUND_Y)
        s = 0.5 + (y - GROUND_Y) / (H - GROUND_Y) * 1.2
        p = skia.Path()
        for k in range(3):
            p.moveTo(x + (k - 1) * 6 * s, y)
            p.quadTo(x + (k - 1) * 9 * s, y - 14 * s, x + (k - 1) * 13 * s + 4, y - 24 * s)
        c.drawPath(p, stroke((40, 52, 50), 2.4 * s, 0.8))
    # crooked garden stones with spiral carvings
    for (sx, sy, sc, rot) in ((330, 1268, 0.7, -6), (760, 1262, 0.8, 5)):
        with Xf(c, sx, sy, rot=rot, sx=sc):
            st = smooth_path([(-40, 0), (-44, -90), (-20, -126), (20, -126), (44, -90), (40, 0)], tension=0.7)
            c.drawPath(st, fill((84, 86, 100)))
            c.drawPath(st, stroke((40, 40, 56), 4))
            c.drawPath(open_path(spiral_pts(0, -70, 2, 22, 2.0, n=30)), stroke((50, 50, 66), 3))


def mound(c, x, y, s=1.0, open_=1.0, shake=0.0, seed=0):
    if shake > 0.15:  # clods of dirt jumping off a knocking mound
        rr = rng(f"clods{seed}")
        for k in range(7):
            cx = x + rr.uniform(-90, 90) * s
            c.drawCircle(cx, y - 30 - shake * rr.uniform(20, 70), rr.uniform(5, 10), fill((86, 66, 52)))
    with Xf(c, x, y - 10 * shake, sx=s * (1 + 0.06 * shake), sy=s * (1 - 0.05 * shake)):
        c.drawPath(smooth_path([(-110, 4), (-80, -26), (-20, -42), (40, -38), (90, -20), (112, 6)], tension=0.7),
                   fill((52, 40, 34)))
        if open_ > 0:
            c.drawOval(skia.Rect.MakeLTRB(-60, -16, 60, 10), fill((14, 10, 12), open_))
        for k in range(5):
            c.drawCircle(-70 + k * 34, -10 - (k % 2) * 12, 6, fill((70, 56, 46)))


def pumpkins(c, t, freeze=False, hop=0.0):
    tt = 0.0 if freeze else t
    for i, (x, y, r, a) in enumerate(PUMPKINS):
        dy = -abs(math.sin(hop * math.pi + i)) * 30 if hop else 0.0
        S_.draw_lantern(c, x, y + dy, r, tt + i * 1.3, lit=a, glow_amt=0.9)


def fog(c, t, a=1.0):
    ts = math.floor(t * 4) / 4
    for k in range(3):
        y = GROUND_Y + 40 + k * 160
        x = (ts * (12 + 6 * k) + k * 300) % 1600 - 300
        c.drawOval(skia.Rect.MakeLTRB(x - 600, y - 50, x + 600, y + 50),
                   fill((190, 200, 230), 0.07 * a, blur=30))
        c.drawOval(skia.Rect.MakeLTRB(x + 300, y - 40, x + 1300, y + 40),
                   fill((190, 200, 230), 0.05 * a, blur=30))
