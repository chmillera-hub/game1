from lib import *

DX, MX = 330, 950   # house door x for Daniel / Maren

def town(c, t, lit_d=True, lit_m=True, mode='dusk'):
    house(c, 100, 170, 130, t, wall=(122, 100, 130), roof=(70, 56, 100), seed=1)
    house(c, DX, 200, 150, t, wall=(158, 104, 88), roof=(100, 54, 62), lit=lit_d, seed=2)
    house(c, MX, 200, 150, t, wall=(170, 130, 90), roof=(110, 70, 56), lit=lit_m, seed=3)
    house(c, 1180, 170, 130, t, wall=(112, 120, 140), roof=(64, 70, 104), seed=4)

def lantern_strings(c, t, a=1.0):
    pole(c, 470, 330); pole(c, 810, 330); pole(c, 20, 340); pole(c, 1260, 340)
    string_lanterns(c, t, 20, 340, 470, 330, 34, 8, a)
    string_lanterns(c, t, 470, 330, 810, 330, 46, 7, a)
    string_lanterns(c, t, 810, 330, 1260, 340, 34, 8, a)

# ---------- item icons ----------
def item(c, kind, x, y, s, t=0, a=1.0):
    cols = {'tv': (90, 220, 255), 'pad': (255, 90, 190), 'phone': (130, 255, 160), 'dice': (255, 230, 120), 'pot': (255, 150, 90), 'weight': (180, 160, 255)}
    col = cols[kind]
    c.glow(x, y, s * 1.2, col, 0.45 * a)
    if kind == 'tv':
        c.rect(x - s * .6, y - s * .45, x + s * .6, y + s * .4, fill=(40, 40, 60), r=s * .08)
        for i in range(6):
            cc = [(255, 90, 120), (255, 200, 80), (90, 230, 140), (90, 200, 255), (200, 120, 255), (255, 130, 60)][i]
            c.rect(x - s * .5 + i * s * .167, y - s * .36, x - s * .5 + (i + 1) * s * .167, y + s * .26, fill=cc)
        c.rect(x - s * .15, y + s * .4, x + s * .15, y + s * .5, fill=(60, 60, 80))
    elif kind == 'pad':
        c.rect(x - s * .6, y - s * .28, x + s * .6, y + s * .3, fill=(60, 50, 90), r=s * .22)
        c.rect(x - s * .42, y - s * .05, x - s * .18, y + s * .03, fill=col); c.rect(x - s * .34, y - s * .13, x - s * .26, y + s * .11, fill=col)
        c.ell(x + s * .24, y - s * .02, s * .07, fill=(255, 230, 90)); c.ell(x + s * .38, y + s * .08, s * .07, fill=(90, 220, 255))
    elif kind == 'phone':
        c.rect(x - s * .3, y - s * .55, x + s * .3, y + s * .55, fill=(36, 36, 50), r=s * .1)
        c.rect(x - s * .25, y - s * .46, x + s * .25, y + s * .44, fill=(110, 240, 160), r=s * .05)
        for i in range(3):
            c.rect(x - s * .19, y - s * .36 + i * s * .26, x + s * .19, y - s * .2 + i * s * .26, fill=(230, 255, 240), r=s * .03)
    elif kind == 'dice':
        c.rect(x - s * .4, y - s * .4, x + s * .4, y + s * .4, fill=(250, 246, 235), r=s * .1)
        for (dx, dy) in ((-.2, -.2), (.2, -.2), (0, 0), (-.2, .2), (.2, .2)):
            c.ell(x + dx * s, y + dy * s, s * .07, fill=(40, 40, 50))
    elif kind == 'pot':
        c.ell(x, y + s * .12, s * .5, s * .32, fill=(200, 110, 70))
        c.rect(x - s * .5, y - s * .1, x + s * .5, y + s * .15, fill=(200, 110, 70))
        c.ell(x, y - s * .1, s * .5, s * .14, fill=(236, 150, 100))
        for i in (-1, 0, 1):
            c.line([(x + i * s * .22, y - s * .3), (x + i * s * .22 + math.sin(t * 3 + i) * 4, y - s * .6)], 2, (255, 255, 255))
    elif kind == 'weight':
        c.line([(x - s * .5, y), (x + s * .5, y)], s * .08, (200, 200, 220))
        for sx in (-1, 1):
            c.rect(x + sx * s * .5 - s * .09, y - s * .3, x + sx * s * .5 + s * .09, y + s * .3, fill=col, r=s * .04)
            c.rect(x + sx * s * .32 - s * .06, y - s * .22, x + sx * s * .32 + s * .06, y + s * .22, fill=lerpc(col, (0, 0, 0), .25), r=s * .03)

# ---------- scene helpers ----------
def sub(c, k, u):
    """caption for scene k at local time u"""
    for (s, e, txt) in sentences(k):
        if s - 0.05 <= u <= e + 0.25:
            a = min(ramp(u, s - 0.05, s + 0.25), 1 - ramp(u, e, e + 0.25) if e < LEAD[k] + DURS[k] - 0.01 else 1)
            caption(c, txt, a); return
    # hold last sentence a bit
    return

def sent_start(k, i): return sentences(k)[i][0]

# ---------- scenes ----------
def s0(c, u, k):
    world(c, u, 'dusk', camx=u * 8)
    town(c, u)
    lantern_strings(c, u)
    fireflies(c, u, 14, 5, 0.8)
    a = ramp(u, 0.3, 1.6) * (1 - ramp(u, 3.0, 3.6))
    if a > 0:
        c.text(640, 150, 'ALDER HOLLOW', 76, tuple(int(255 * a) for _ in range(3)), 'mm', bold=True, serif=True)
        c.text(640, 205, 'a story', 24, (int(255 * a), int(215 * a), int(170 * a)), 'mm', serif=True)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 1.2))

def s1(c, u, k):
    # left: workshop, right: garden
    L = C(636, H); R = C(636, H)
    # workshop
    L.rect(0, 0, 636, H, fill=(84, 58, 46))
    for x in range(0, 636, 52): L.rect(x, 0, x + 3, 520, fill=(70, 48, 40))
    L.rect(0, 520, 636, H, fill=(54, 38, 34))
    L.rect(40, 150, 600, 160, fill=(50, 34, 28))
    for i, cx in enumerate((90, 190, 300, 420, 540)):
        r = 38 if i % 2 == 0 else 28
        L.ell(cx, 110, r, fill=(238, 224, 190), outline=(60, 40, 30), w=4)
        ang = u * (1.0 + i * 0.45)
        L.line([(cx, 110), (cx + r * .7 * math.sin(ang), 110 - r * .7 * math.cos(ang))], 2.5, (40, 30, 30))
        L.line([(cx, 110), (cx + r * .45 * math.sin(ang / 12), 110 - r * .45 * math.cos(ang / 12))], 3.5, (40, 30, 30))
    L.glow(318, 330, 280, (255, 190, 110), 0.55)
    L.rect(110, 400, 540, 520, fill=(120, 80, 54)); L.rect(110, 400, 540, 414, fill=(150, 104, 70))
    # gears on bench
    for (gx, gy, gr) in ((190, 388, 18), (240, 392, 12)):
        L.ell(gx, gy, gr, fill=(190, 170, 120)); L.ell(gx, gy, gr * .4, fill=(84, 58, 46))
    person(L, 380, 520, 290, DAN, dir=-1, mood='flat', arms=(20, 60 + 8 * math.sin(u * 3)), nod=math.sin(u * 2) * 0.4)
    # garden
    R.rect(0, 0, 636, H, fill=(40, 30, 82))
    for i in range(30):
        R.ell((i * 97) % 636, (i * 53) % 300, 1.2, fill=(210, 210, 240))
    R.rect(0, 0, 636, H, fill=None)
    R.poly([(0, 400), (160, 330), (360, 380), (636, 320), (636, H), (0, H)], (44, 40, 90))
    R.rect(0, 500, 636, H, fill=(52, 82, 62))
    R.rect(0, 500, 636, 516, fill=(70, 108, 76))
    R.glow(320, 400, 300, (255, 180, 120), 0.25)
    for hx in (90, 520):
        R.rect(hx - 40, 440, hx + 40, 500, fill=(220, 184, 110)); R.rect(hx - 46, 430, hx + 46, 444, fill=(176, 140, 84))
        R.rect(hx - 40, 470, hx + 40, 474, fill=(150, 112, 70)); R.rect(hx - 10, 456, hx + 10, 466, fill=(50, 34, 26))
    for i in range(9):
        fx = 40 + i * 70
        R.line([(fx, 520), (fx, 478)], 2.5, (50, 120, 70)); R.ell(fx, 474, 9, fill=[(255, 120, 150), (255, 220, 100), (200, 140, 255)][i % 3]); R.ell(fx, 474, 3, fill=(255, 245, 200))
    person(R, 290, 540, 290, MAR, dir=1, mood='flat', arms=(15, 25 + 6 * math.sin(u * 2)), nod=0)
    for i in range(9):
        a = u * (1.4 + i * 0.13) + i
        bx = 300 + 190 * math.sin(a) * math.cos(i); by = 330 + 90 * math.sin(a * 1.3 + i)
        R.glow(bx, by, 10, (255, 230, 120), 0.5)
        R.ell(bx, by, 4, 3, fill=(255, 210, 60)); R.line([(bx - 2, by - 2), (bx + 3, by - 4 + math.sin(u * 40 + i) * 3)], 1.2, (230, 240, 255))
    c.paste(L, 0, 0); c.paste(R, 644, 0)
    # river strip
    c.rect(636, 0, 644, H, fill=(70, 130, 200))
    for i in range(16):
        yy = (i * 47 + u * 60) % H
        c.line([(637, yy), (643, yy + 8)], 1.4, (200, 230, 255))
    # name tags
    a1 = ramp(u, sent_start(k, 1) + 1.2, sent_start(k, 1) + 1.7)
    a2 = ramp(u, sent_start(k, 2) - 0.1, sent_start(k, 2) + 0.4)
    for (a, x, txt, sub_) in ((a1, 320, 'Daniel', 'clockmaker'), (a2, 960, 'Maren', 'beekeeper')):
        if a > 0:
            v = int(255 * a)
            c.veil(x - 110, 60, x + 110, 140, (6, 6, 18), 0.55 * a)
            c.text(x, 88, txt, 38, (v, v, v), 'mm', bold=True, serif=True)
            c.text(x, 122, sub_, 22, (int(255 * a), int(210 * a), int(150 * a)), 'mm', serif=True)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    sub(c, k, u)

def s2(c, u, k):
    world(c, u, 'night', camx=u * 4, moon=(930, 120))
    town(c, u, True, True, 'night')
    lantern_strings(c, u, 0.6)
    st = sentences(k)
    bd = ramp(u, st[0][0] - 0.5, st[0][0] + 0.5)
    walk = 0
    person(c, 430, GY + 14, 120, DAN, dir=1, mood='flat', arms=(0, 15))
    person(c, 850, GY + 14, 120, MAR, dir=-1, mood='flat', arms=(0, 15))
    # family glyph appears
    gl = ramp(u, st[0][0] + 0.8, st[0][0] + 3.0)
    cx, cy = 640, 300
    pulse = 0.85 + 0.15 * math.sin(u * 2.2)
    if gl > 0:
        c.glow(cx, cy, 160, (255, 200, 120), 0.55 * gl * pulse)
        col = lerpc((20, 20, 40), (255, 226, 160), gl)
        c.poly([(cx - 62, cy - 4), (cx, cy - 56), (cx + 62, cy - 4)], col)
        c.rect(cx - 48, cy - 6, cx + 48, cy + 50, fill=col)
        c.rect(cx - 12, cy + 12, cx + 12, cy + 50, fill=(60, 40, 36))
        for (fx, fh) in ((cx - 26, 24), (cx + 26, 24)):
            pass
    # orbs from each person to the house when the second sentence begins
    f = ramp(u, st[1][0] - 0.2, st[1][0] + 3.2)
    for (sx, sgn) in ((430, 1), (850, -1)):
        x = lerp(sx, cx, f); y = lerp(GY - 80, cy + 16, f) - 90 * math.sin(math.pi * f)
        if f > 0.01 or True:
            c.glow(x, y, 34, (255, 210, 120), 0.9)
            c.ell(x, y, 4.5, fill=(255, 245, 210))
    if f > 0.98:
        c.glow(cx, cy + 16, 120, (255, 230, 170), 0.5 + 0.2 * math.sin(u * 3))
    fireflies(c, u, 10, 9, 0.6)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.8))
    sub(c, k, u)

def arcade(c, u, k):
    c.im.paste(sky('indoor_p'), (0, 0))
    for x in range(0, W, 80): c.line([(x, 0), (x, 500)], 1, (40, 24, 70))
    c.rect(0, 540, W, H, fill=(30, 16, 50))
    for x in range(-200, W + 200, 120): c.line([(x, H), (640 + (x - 640) * 0.45, 540)], 2, (60, 30, 100))
    cx = 700
    blink = int(u * 3) % 2
    c.glow(cx, 330, 330, (120, 60, 255), 0.45)
    c.poly([(cx - 130, 560), (cx - 120, 140), (cx + 120, 140), (cx + 130, 560)], (34, 28, 104))
    c.rect(cx - 125, 110, cx + 125, 165, fill=(20, 14, 60), r=8)
    c.text(cx, 138, 'ARCADE', 40, (255, 90, 190) if blink else (255, 230, 90), 'mm', bold=True)
    c.rect(cx - 96, 190, cx + 96, 390, fill=(8, 8, 18), r=6)
    # invaders
    for r_ in range(3):
        for q in range(7):
            ox = 28 * math.sin(u * 1.6) + (q - 3) * 24
            oy = r_ * 24 + (int(u * 2) % 2) * 3
            colr = [(90, 255, 160), (255, 220, 90), (255, 90, 160)][r_]
            c.rect(cx + ox - 8, 215 + oy, cx + ox + 8, 227 + oy, fill=colr)
            c.rect(cx + ox - 11, 219 + oy, cx + ox - 8, 223 + oy, fill=colr); c.rect(cx + ox + 8, 219 + oy, cx + ox + 11, 223 + oy, fill=colr)
    sx = cx + 60 * math.sin(u * 2.3)
    c.rect(sx - 9, 360, sx + 9, 368, fill=(120, 220, 255)); c.rect(sx - 2, 352, sx + 2, 360, fill=(120, 220, 255))
    if int(u * 6) % 2: c.rect(sx - 1, 300 - (u * 120) % 60, sx + 1, 312 - (u * 120) % 60, fill=(255, 255, 255))
    c.rect(cx - 120, 410, cx + 120, 450, fill=(20, 20, 56))
    c.line([(cx - 60, 438), (cx - 60 + 8 * math.sin(u * 5), 418)], 4, (220, 220, 230)); c.ell(cx - 60 + 8 * math.sin(u * 5), 416, 8, fill=(255, 60, 90))
    for i, cc in enumerate([(255, 220, 80), (80, 220, 255), (255, 80, 200)]):
        c.ell(cx + 10 + i * 34, 432, 10, fill=cc)
    # clock
    c.rect(1030, 70, 1160, 200, fill=(40, 30, 70), r=12)
    c.ell(1095, 135, 52, fill=(238, 232, 215), outline=(255, 90, 190), w=4)
    ang = u * 3.0
    c.line([(1095, 135), (1095 + 40 * math.sin(ang), 135 - 40 * math.cos(ang))], 3, (30, 30, 40))
    c.line([(1095, 135), (1095 + 26 * math.sin(ang / 12), 135 - 26 * math.cos(ang / 12))], 5, (30, 30, 40))
    person(c, 440, 586, 300, DAN, dir=1, mood='flat', arms=(60, 80), nod=math.sin(u * 4) * 0.2, tint=((60, 160, 255), 0.18))
    c.glow(480, 380, 120, (90, 180, 255), 0.15 + 0.1 * math.sin(u * 8))

def dark_house(c, u, k, wf):
    world(c, u, 'night', camx=u * 3, moon=(1020, 130))
    town(c, u, False, True, 'night')
    lantern_strings(c, u, 0.5)
    # Daniel walks from x=140 to the door and pauses
    xx = lerp(120, DX - 6, ramp(wf, 0, 0.8))
    walking = 0 < ramp(wf, 0, 0.8) < 1
    person(c, xx, GY + 14, 120, DAN, dir=1, walk=u * 7 if walking else 0, mood='flat' if not walking else 'flat', arms=(0, 0))
    house_dark_hint(c, DX, u)

def house_dark_hint(c, cx, u):
    pass

def s3(c, u, k):
    st = sentences(k)
    t_q = st[3][0] - 0.2
    if u < t_q + 1.2:
        arcade(c, u, k)
    if u >= t_q:
        f = ramp(u, t_q, t_q + 1.2)
        c2 = C()
        dark_house(c2, u, k, (u - t_q - 0.6) / 3.0)
        if u < t_q + 1.2: c.mix(c2, f)
        else: c.reset(c2.im)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    sub(c, k, u)

def board(c, u, k):
    c.im.paste(sky('indoor_w'), (0, 0))
    c.rect(0, 520, W, H, fill=(62, 42, 36))
    c.glow(640, 160, 300, (255, 210, 130), 0.5)
    c.line([(640, 0), (640, 110)], 2, (30, 20, 20)); c.poly([(580, 140), (700, 140), (670, 108), (610, 108)], (210, 170, 90))
    people = [(290, 1, 0), (500, 1, 1), (780, -1, 2), (990, -1, 3)]
    for (x, d, i) in people:
        person(c, x, 600, 330, villager(i), dir=d, mood='talk' if int(u / 1.7 + i) % 2 == 0 else 'smile', talk=u * 9 + i * 2, arms=(10, 30 + 20 * math.sin(u * 2 + i)))
    person(c, 640, 600, 330, DAN, dir=1, mood='flat', arms=(0, 0))
    c.ell(640, 560, 400, 70, fill=(120, 76, 52)); c.rect(240, 540, 1040, 566, fill=(120, 76, 52)); c.ell(640, 540, 400, 62, fill=(150, 100, 66))
    # board
    c.poly([(480, 536), (800, 536), (830, 560), (450, 560)], (230, 214, 160))
    for r_ in range(3):
        for q in range(6):
            if (r_ + q) % 2: c.poly([(500 + q * 50 - r_ * 6, 540 + r_ * 6), (550 + q * 50 - r_ * 6, 540 + r_ * 6), (550 + q * 50 - r_ * 7, 546 + r_ * 6), (500 + q * 50 - r_ * 7, 546 + r_ * 6)], (160, 100, 80))
    for i, cc in enumerate([(220, 70, 70), (70, 120, 220), (240, 200, 60)]):
        c.ell(540 + i * 90, 538 - 6 * abs(math.sin(u * 2 + i)), 10, 14, fill=cc)
    c.text(640, 456, '. . .', 36, (255, 255, 255), 'mm', bold=True) if int(u * 1.5) % 2 else None

def memes(c, u, k):
    c.im.paste(sky('indoor_p'), (0, 0))
    c.glow(640, 330, 460, (80, 120, 255), 0.25)
    # strangers' avatars
    r = random.Random(2)
    for i in range(14):
        ang = i * 0.9 + u * 0.12
        ax = 640 + 440 * math.cos(ang) * (0.9 + 0.1 * math.sin(i)); ay = 330 + 230 * math.sin(ang)
        if abs(ax - 640) < 190: continue
        c.line([(ax, ay), (640 + (ax - 640) * .38, 330 + (ay - 330) * .38)], 1.2, (70, 90, 170))
        c.ell(ax, ay, 24, fill=(110, 116, 150)); c.text(ax, ay, '?', 28, (230, 232, 250), 'mm', bold=True)
        c.text(ax, ay + 38, 'user_%d' % (1000 + (i * 733) % 8999), 15, (170, 176, 210), 'mm')
    # phone
    c.rect(520, 70, 760, 590, fill=(14, 14, 24), r=34, outline=(120, 130, 190), w=4)
    scr = C(212, 470)
    scr.rect(0, 0, 212, 470, fill=(24, 26, 44))
    sc = (u * 90) % 170
    emojis = ['grin', 'cat', 'cool', 'cry', 'wow']
    for i in range(-1, 4):
        y = i * 170 + sc - 0
        y = (i * 170 - sc) % (170 * 4) - 170
        bg = [(255, 140, 120), (110, 200, 255), (255, 220, 110), (170, 140, 255), (120, 230, 170)][(i + int(u * 90 // 170)) % 5]
        scr.rect(8, y + 8, 204, y + 162, fill=bg, r=14)
        scr.ell(32, y + 34, 14, fill=(90, 94, 120)); scr.text(32, y + 34, '?', 18, (240, 240, 250), 'mm', bold=True)
        scr.text(120, y + 34, 'user_%d' % (2000 + ((i + int(u * 90 // 170)) * 421) % 7000), 14, (40, 40, 60), 'mm')
        kind = emojis[(i + int(u * 90 // 170)) % 5]
        ex, ey = 106, y + 98
        scr.ell(ex, ey, 34, fill=(255, 224, 90), outline=(120, 80, 20), w=3)
        if kind == 'cat':
            scr.poly([(ex - 32, ey - 14), (ex - 24, ey - 48), (ex - 8, ey - 30)], (255, 224, 90)); scr.poly([(ex + 32, ey - 14), (ex + 24, ey - 48), (ex + 8, ey - 30)], (255, 224, 90))
        if kind == 'cool': scr.rect(ex - 24, ey - 10, ex + 24, ey + 2, fill=(30, 30, 40), r=4)
        else:
            scr.ell(ex - 12, ey - 6, 4, fill=(50, 30, 20)); scr.ell(ex + 12, ey - 6, 4, fill=(50, 30, 20))
        if kind in ('grin', 'cat', 'cool'): scr.arc(ex, ey + 4, 18, 14, 10, 170, 3, (120, 40, 30))
        elif kind == 'cry':
            scr.arc(ex, ey + 18, 14, 9, 200, 340, 3, (120, 40, 30)); scr.line([(ex - 12, ey), (ex - 12, ey + 14)], 2, (90, 170, 255))
        else: scr.ell(ex, ey + 14, 7, 9, fill=(120, 40, 30))
    mask = Image.new('L', scr.im.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, scr.im.size[0] - 1, scr.im.size[1] - 1], radius=24 * K, fill=255)
    c.im.paste(scr.im, (544 * K, 100 * K), mask)
    c.rect(600, 78, 680, 88, fill=(14, 14, 24), r=5)
    person(c, 300, 640, 300, DAN, dir=1, mood='flat', arms=(0, 70), tint=((90, 130, 255), 0.22))
    c.glow(380, 440, 130, (90, 140, 255), 0.25)

def s4(c, u, k):
    st = sentences(k)
    t_m = st[1][0] - 0.3
    if u < t_m + 1.0: board(c, u, k)
    if u >= t_m:
        c2 = C(); memes(c2, u, k)
        f = ramp(u, t_m, t_m + 1.0)
        if u < t_m + 1.0: c.mix(c2, f)
        else: c.reset(c2.im)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    sub(c, k, u)

# ---------- scene 5: nod and smile ----------
def vignette(c, kind, u, n):
    t = u
    if kind == 'church':
        c.im.paste(sky('indoor_w'), (0, 0))
        c.rect(0, 540, W, H, fill=(70, 46, 40))
        # stained glass
        for i, x in enumerate((220, 640, 1060)):
            c.rect(x - 60, 80, x + 60, 330, fill=(40, 40, 90), r=60)
            for j, cc in enumerate([(230, 80, 90), (240, 200, 80), (80, 160, 230), (110, 210, 140)]):
                c.rect(x - 52 + (j % 2) * 52, 110 + (j // 2) * 100 + (60 if j < 2 else 0) * 0, x - 4 + (j % 2) * 52, 200 + (j // 2) * 100, fill=cc)
            c.glow(x, 200, 120, (255, 220, 140), 0.25)
        for ry, scale in ((470, 1.0), (560, 1.3)):
            for x in (180, 460, 820, 1100):
                person(c, x, ry + 60, 180 * scale, villager(int(x) % 6), dir=1, mood='fake', nod=math.sin(t * 3 + x) * .6, arms=(0, 0), tint=((120, 120, 140), 0.25))
        c.rect(0, 600, W, 640, fill=(112, 70, 48))
        c.rect(0, 640, W, H, fill=(88, 54, 40))
    elif kind == 'potluck':
        c.im.paste(sky('indoor_w'), (0, 0))
        c.rect(0, 520, W, H, fill=(80, 56, 46))
        c.glow(640, 200, 400, (255, 210, 130), 0.35)
        for x in range(60, W, 140): c.line([(x, 0), (x + 30, 90)], 2, (60, 40, 40)); lantern(c, x + 30, 100, t + x, 1.0)
        for x in (180, 440, 860, 1100):
            person(c, x, 600, 330, villager(int(x) % 6 + 1), dir=1 if x < 640 else -1, mood='fake', nod=math.sin(t * 3 + x) * .6, arms=(0, 0), tint=((120, 120, 140), 0.2))
        c.rect(120, 540, 1160, 580, fill=(210, 190, 150)); c.rect(120, 580, 1160, 700, fill=(190, 80, 90))
        for i, x in enumerate(range(170, 1130, 90)):
            c.ell(x, 534, 30, 10, fill=(240, 232, 214)); c.ell(x, 524, 22, 14, fill=[(230, 140, 70), (150, 190, 90), (210, 90, 90), (240, 200, 100)][i % 4])
    elif kind == 'gym':
        c.im.paste(sky('indoor_p'), (0, 0))
        c.rect(0, 540, W, H, fill=(34, 30, 52))
        for x in range(0, W, 160): c.rect(x, 0, x + 6, 540, fill=(50, 44, 80))
        c.rect(100, 100, 360, 300, fill=(24, 26, 44), outline=(90, 90, 140), w=4)
        for x in (180, 520, 900, 1130):
            ph = (t * 2 + x) % 6.28
            person(c, x, 600, 330, villager(int(x) % 6 + 2), dir=1, mood='fake', arms=(60 + 60 * math.sin(ph), 60 + 60 * math.sin(ph)), nod=math.sin(t * 3 + x) * .6, tint=((120, 120, 140), 0.2))
            c.line([(x - 30, 600 - 330 * (0.5 + 0.2 * math.sin(ph))), (x + 30, 600 - 330 * (0.5 + 0.2 * math.sin(ph)))], 4, (200, 200, 220))
        for x in (330, 740, 1020):
            c.rect(x - 40, 630, x + 40, 640, fill=(120, 120, 150)); c.rect(x - 32, 612, x - 18, 630, fill=(200, 60, 80)); c.rect(x + 18, 612, x + 32, 630, fill=(200, 60, 80))
    else:
        c.im.paste(sky('indoor_p'), (0, 0))
        c.rect(0, 540, W, H, fill=(44, 40, 58))
        c.rect(0, 100, W, 108, fill=(70, 70, 100))
        for x in (230, 640, 1050):
            c.rect(x - 150, 460, x + 150, 620, fill=(120, 130, 160))
            c.rect(x - 160, 440, x + 160, 456, fill=(150, 160, 190))
            c.rect(x - 70, 330, x + 70, 430, fill=(24, 26, 44), r=6, outline=(90, 90, 140), w=3)
            c.rect(x - 60, 340, x + 60, 420, fill=(60, 110, 190) if int(t * 2 + x) % 5 else (90, 150, 230))
            c.rect(x - 10, 430, x + 10, 440, fill=(40, 40, 60))
        for x in (140, 430, 850, 1140):
            person(c, x, 640, 300, villager(int(x) % 6 + 3), dir=1 if x < 640 else -1, mood='fake', nod=math.sin(t * 3 + x) * .6, arms=(0, 0), tint=((120, 120, 140), 0.2))
    # Maren center-front
    person(c, 640, 760, 560, MAR, dir=1, mood='fake', nod=math.sin(t * 3.2) * 1.0, arms=(0, 0)) if False else None

def s5(c, u, k):
    st = sentences(k)
    cuts = [0, 2, 3, 4]
    kinds = ['church', 'potluck', 'gym', 'work']
    starts = [st[i][0] - 0.2 if i else 0 for i in cuts]
    idx = max(i for i in range(4) if u >= starts[i])
    ends = starts[1:] + [1e9]
    vignette(c, kinds[idx], u, idx)
    if idx > 0 and u < starts[idx] + 0.6:
        c2 = C(); vignette(c2, kinds[idx - 1], u, idx - 1)
        c.mix(c2, 1 - ramp(u, starts[idx], starts[idx] + 0.6))
    # Maren
    mx = 640
    person(c, mx, 700, 330, MAR, dir=1, mood='fake', nod=math.sin(u * 3.2) * 1.0, arms=(0, 0))
    # counter
    c.veil(1010, 30, 1250, 100, (6, 6, 18), 0.55)
    c.text(1130, 55, 'nod · smile', 24, (255, 255, 255), 'mm', serif=True)
    c.text(1130, 84, '×' + str(idx + 1 if idx < 3 else 4), 24, (255, 205, 130), 'mm', bold=True)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    sub(c, k, u)

def s6(c, u, k):
    world(c, u, 'night', camx=u * 3, moon=(1070, 100))
    town(c, u, False, False, 'night')
    lantern_strings(c, u, 0.9)
    f = ramp(u, 0.6, 5.0)
    walking = 0 < f < 1
    xd = lerp(60, DX - 40, f); xm = lerp(1240, MX + 40, f)
    person(c, xd, GY + 14, 120, DAN, dir=1, walk=u * 7 if walking else 0, mood='flat', arms=(0, 0))
    person(c, xm, GY + 14, 120, MAR, dir=-1, walk=u * 7 if walking else 0, mood='flat', arms=(0, 0))
    # lonely dark windows highlight
    g = ramp(u, 5.4, 6.5)
    for cx in (DX, MX):
        c.glow(cx, GY - 90, 100, (120, 130, 200), 0.18 * g)
    # reflection of lanterns in the water
    for i in range(7):
        c.glow(GL + 20 + i * 28, 640 + 5 * math.sin(u * 2 + i), 12, (255, 190, 90), 0.4)
    fireflies(c, u, 8, 11, 0.5)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.8))
    sub(c, k, u)

def bubble(c, x, y, txt, a, tail_x, sz=26):
    if a <= 0: return
    wd = F(sz, True).getlength(txt) / K + 40
    hh = 54
    sc = 0.6 + 0.4 * a
    x0, x1 = x - wd / 2 * sc, x + wd / 2 * sc
    c.poly([(x - 14 * sc, y + hh / 2 * sc - 2), (x + 14 * sc, y + hh / 2 * sc - 2), (tail_x, y + hh / 2 * sc + 36)], (250, 248, 240))
    c.rect(x0, y - hh / 2 * sc, x1, y + hh / 2 * sc, fill=(250, 248, 240), r=22 * sc)
    if a > 0.7: c.text(x, y, txt, sz, (50, 40, 50), 'mm', bold=True)

def s7(c, u, k):
    st = sentences(k)
    world(c, u, 'dusk', camx=u * 4)
    town(c, u)
    lantern_strings(c, u, 0.8)
    person(c, 270, GY + 14, 120, DAN, dir=-1, mood='flat', arms=(0, 0))
    person(c, 1010, GY + 14, 120, MAR, dir=1, mood='flat', arms=(0, 0))
    c.veil(0, 460, W, H, (10, 8, 30), 0.35)
    spec = [(110, 1, 'o', (0, 40)), (430, -1, 'talk', (0, 80)), (640, 1, 'o', (0, 30)), (850, 1, 'talk', (0, 80)), (1170, -1, 'o', (0, 40))]
    for i, (x, d, m, ar) in enumerate(spec):
        person(c, x, 820, 520, villager(i + 10), dir=d, mood=m, talk=u * 9 + i, arms=(ar[0], ar[1] + 10 * math.sin(u * 2 + i)), nod=0)
    a1 = ramp(u, st[1][0], st[1][0] + 0.3); a2 = ramp(u, st[2][0], st[2][0] + 0.3); a3 = ramp(u, st[3][0], st[3][0] + 0.3)
    bubble(c, 330, 330, "Why won't he play?", a1, 380) if u < st[2][0] else None
    bubble(c, 880, 330, "Why isn't she joining in?", a2, 840) if u < st[3][0] else None
    if a3 > 0:
        bubble(c, 640, 200, "Look at everything we've given them!", a3, 650, 28)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    sub(c, k, u)

def s8(c, u, k):
    st = sentences(k)
    world(c, u, 'dusk', camx=u * 3)
    town(c, u)
    lantern_strings(c, u, 0.7)
    person(c, 330, GY + 14, 120, DAN, dir=1, mood='flat', arms=(0, 0))
    person(c, 950, GY + 14, 120, MAR, dir=-1, mood='flat', arms=(0, 0))
    plan = [  # (sentence, kind, side, restx, resty, size)
        (1, 'tv', 0, 300, GY - 30, 88), (1, 'tv', 1, 980, GY - 30, 88),
        (2, 'pad', 0, 410, GY - 22, 74), (2, 'dice', 1, 880, GY - 24, 62),
        (2, 'dice', 0, 215, GY - 22, 62), (2, 'pad', 1, 1070, GY - 22, 74),
        (3, 'phone', 0, 360, GY - 100, 90), (3, 'phone', 1, 930, GY - 100, 90),
        (3, 'phone', 0, 450, GY - 100, 90), (3, 'phone', 1, 1010, GY - 98, 90),
        (4, 'pot', 0, 255, GY - 96, 80), (4, 'pot', 1, 1100, GY - 96, 80),
        (4, 'pot', 0, 330, GY - 160, 80), (4, 'pot', 1, 950, GY - 164, 80),
        (5, 'weight', 0, 410, GY - 164, 80), (5, 'weight', 1, 1030, GY - 164, 80),
        (5, 'tv', 0, 360, GY - 230, 70), (5, 'tv', 1, 880, GY - 232, 70),
        (5, 'dice', 0, 290, GY - 232, 56), (5, 'pad', 1, 980, GY - 232, 60),
    ]
    for j, (si, kind, side, rx, ry, s_) in enumerate(plan):
        t0 = st[si][0] + 0.10 * (j % 6)
        f = clamp((u - t0) / 0.7)
        if f <= 0: continue
        # drop with a bounce
        y = ry - (1 - ease(f)) * (ry + 80)
        if f >= 1: y = ry
        item(c, kind, rx, y + 6 * math.sin(u * 2 + j) * 0.0, s_, u, 1.0)
    # sparkles
    if u > st[5][0]:
        r = random.Random(4)
        for i in range(24):
            sx = r.choice([r.uniform(190, 520), r.uniform(840, 1100)]); sy = r.uniform(GY - 260, GY - 10)
            b = 0.5 + 0.5 * math.sin(u * 4 + i * 1.7)
            c.line([(sx - 6 * b, sy), (sx + 6 * b, sy)], 1.4, (255, 255, 255)); c.line([(sx, sy - 6 * b), (sx, sy + 6 * b)], 1.4, (255, 255, 255))
    # the missing bridge
    f = ramp(u, st[6][0], st[6][0] + 1.4)
    if f > 0:
        N = 9; pw = (GR - GL + 20) / N
        pulse = 0.6 + 0.4 * math.sin(u * 3)
        for i in range(N):
            x0 = GL - 10 + i * pw
            col = lerpc((60, 60, 90), (200, 220, 255), 0.7 * f * pulse)
            c.rect(x0 + 2, GY - 3, x0 + pw - 2, GY + 7, outline=col, w=1.6)
        c.glow(640, GY, 110, (150, 180, 255), 0.3 * f * pulse)
        c.text(640, GY - 46, '?', 54, (int(230 * f), int(236 * f), int(255 * f)), 'mm', bold=True, serif=True)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    sub(c, k, u)

def s9(c, u, k):
    st = sentences(k)
    world(c, u, 'night', camx=u * 3, moon=(1070, 100))
    town(c, u, True, True, 'night')
    lantern_strings(c, u, 0.6)
    person(c, 430, GY + 14, 120, DAN, dir=1, mood='sad', arms=(0, 0), lantern_t=u)
    person(c, 850, GY + 14, 120, MAR, dir=-1, mood='sad', arms=(0, 0), lantern_t=u + 1)
    a = ramp(u, st[0][0] + 1.2, st[0][0] + 2.4)
    pulse = 0.85 + 0.15 * math.sin(u * 3)
    c.glow(640, 330, 190, (140, 160, 255), 0.45 * a * pulse)
    v = int(255 * a)
    c.text(640, 330, '?', 230, (v, v, min(255, v + 10)), 'mm', bold=True, serif=True)
    fireflies(c, u, 10, 21, 0.6)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    sub(c, k, u)

def s10(c, u, k):
    st = sentences(k)
    world(c, u, 'night', camx=u * 3, moon=(1070, 100))
    town(c, u, True, True, 'night')
    lantern_strings(c, u, 0.5)
    person(c, 420, GY + 20, 210, DAN, dir=1, mood='smile' if u > st[1][0] else 'flat', arms=(0, 10), lantern_t=u)
    person(c, 860, GY + 20, 210, MAR, dir=-1, mood='smile' if u > st[1][0] else 'flat', arms=(0, 10), lantern_t=u + 1)
    r = random.Random(8)
    kinds = ['tv', 'pad', 'phone', 'dice', 'pot', 'weight']
    for i in range(14):
        side = i % 2
        sp = 0.1 + 0.07 * (i % 5)
        f = ((u * sp + r.random()) % 1.0)
        x0 = 30 if side == 0 else 1250
        tx = 420 if side == 0 else 860
        x = lerp(x0, tx + (-60 if side == 0 else 60), f)
        y = 260 + 90 * math.sin(f * 6 + i) + (f * 60)
        a = 1 - ramp(f, 0.55, 0.95)
        item(c, kinds[i % 6], x, y, 46, u, 0.6 * a) if a > 0.05 else None
    a = ramp(u, st[2][0] + 0.2, st[2][0] + 1.4)
    if a > 0:
        c.veil(300, 70, 980, 190, (6, 6, 18), 0.45 * a)
        v = int(255 * a)
        c.text(640, 108, 'distraction', 52, (v, int(v * .62), int(v * .62)), 'mm', serif=True)
        c.line([(470, 108), (810, 108)], 4, (int(255 * a), int(100 * a), int(100 * a)))
        c.text(640, 162, 'connection', 52, (v, int(v * .9), int(v * .6)), 'mm', bold=True, serif=True)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    sub(c, k, u)

def bridge_scene(c, u, k, pl, dpos, mpos, walkd, walkm, glowf, stars_b=1.0, texta=0):
    world(c, u, 'night', camx=u * 3, moon=(1070, 100))
    town(c, u, True, True, 'night')
    lantern_strings(c, u, 0.7)
    planks_draw(c, u, pl)
    person(c, dpos, GY + 4, 130, DAN, dir=1, walk=u * 7 if walkd else 0, mood='smile' if glowf > .2 else 'flat', arms=(0, 0), lantern_t=u)
    person(c, mpos, GY + 4, 130, MAR, dir=-1, walk=u * 7 + 1 if walkm else 0, mood='smile' if glowf > .2 else 'flat', arms=(0, 0), lantern_t=u + 1)
    if glowf > 0:
        mid = (dpos + mpos) / 2
        c.glow(mid, GY - 60, 280, (255, 200, 120), 0.5 * glowf * (0.9 + 0.1 * math.sin(u * 2)))
    fireflies(c, u, 16, 31, 0.5 + 0.5 * glowf)

def s11(c, u, k):
    st = sentences(k)
    pl = 9 * ramp(u, st[0][0] + 0.2, st[1][0] + 1.4)
    fd = ramp(u, st[2][0], DURS[k] + LEAD[k] + 1.2)
    fm = ramp(u, st[3][0], DURS[k] + LEAD[k] + 1.2)
    dpos = lerp(430, 618, fd); mpos = lerp(850, 662, fm)
    wd = 0 < fd < 1; wm = 0 < fm < 1
    glowf = ramp(u, DURS[k] + LEAD[k] + 0.6, DURS[k] + LEAD[k] + 1.8)
    bridge_scene(c, u, k, pl, dpos, mpos, wd, wm, glowf)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    sub(c, k, u)

def s12(c, u, k):
    st = sentences(k)
    bridge_scene(c, u + 4, k, 9, 618, 662, False, False, 1.0)
    # gentle drift: sparks
    a = ramp(u, DURS[k] + LEAD[k] + 0.4, DURS[k] + LEAD[k] + 1.6)
    if a > 0:
        v = int(255 * a)
        c.veil(0, 90, W, 230, (6, 6, 18), 0.4 * a)
        c.text(640, 160, 'Build the bridge.', 74, (v, int(v * .92), int(v * .78)), 'mm', bold=True, serif=True)
    c.fade((0, 0, 0), 1 - ramp(u, 0, 0.6))
    c.fade((0, 0, 0), ramp(u, D[k] - 1.8, D[k] - 0.2))
    sub(c, k, u)

SCENES = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12]

def frame(n):
    t = n / FPS
    k = max(i for i in range(13) if T0[i] <= t + 1e-9)
    c = C()
    SCENES[k](c, t - T0[k], k)
    return c.out(), k
