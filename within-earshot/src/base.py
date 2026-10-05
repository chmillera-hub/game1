from lib import *

JUNO = dict(skin=(222, 172, 140), hair=(30, 24, 30), shirt=(238, 112, 96), pants=(60, 66, 96), glasses=True, long=True)
PELL = dict(skin=(238, 198, 168), hair=(120, 84, 52), shirt=(84, 130, 182), pants=(70, 70, 86), glasses=False, long=False)
DANA = dict(skin=(190, 140, 106), hair=(52, 36, 30), shirt=(226, 180, 80), pants=(86, 70, 90), glasses=False, long=True)
EXTRA = [villager(5), villager(6), villager(9)]
FY = 580   # floor line

def sub(c, k, u):
    for (s, e, txt) in sentences(k):
        if s - 0.05 <= u <= e + 0.25:
            a = min(ramp(u, s - 0.05, s + 0.25), 1 - ramp(u, e, e + 0.25) if e < LEAD[k] + DURS[k] - 0.01 else 1)
            caption(c, txt, a); return

def st(k, i): return sentences(k)[i][0]
def en(k, i): return sentences(k)[i][1]
def fcol(c, a): c.fade((0, 0, 0), 1 - a)

# ---------- icons ----------
def sun(c, x, y, r, t=0):
    c.glow(x, y, r * 2.6, (255, 210, 90), 0.6)
    for i in range(12):
        a = i * math.pi / 6 + t * 0.5
        c.line([(x + math.cos(a) * r * 1.25, y + math.sin(a) * r * 1.25), (x + math.cos(a) * r * 1.65, y + math.sin(a) * r * 1.65)], max(2, r * .16), (255, 200, 70))
    c.ell(x, y, r, fill=(255, 218, 80))

def snow(c, x, y, r, col=(220, 240, 255)):
    for i in range(3):
        a = i * math.pi / 3
        c.line([(x - math.cos(a) * r, y - math.sin(a) * r), (x + math.cos(a) * r, y + math.sin(a) * r)], max(2, r * .16), col)
        for sgn in (-1, 1):
            bx, by = x + math.cos(a) * r * .6 * sgn, y + math.sin(a) * r * .6 * sgn
            c.line([(bx, by), (bx + math.cos(a + 1) * r * .28, by + math.sin(a + 1) * r * .28)], max(1.5, r * .1), col)
            c.line([(bx, by), (bx + math.cos(a - 1) * r * .28, by + math.sin(a - 1) * r * .28)], max(1.5, r * .1), col)

def cloud(c, x, y, s, col=(190, 200, 215), rain=False, t=0):
    for (dx, dy, rr) in ((-.5, .1, .42), (0, -.12, .52), (.5, .08, .4), (.1, .18, .5)):
        c.ell(x + dx * s, y + dy * s, rr * s, fill=col)
    if rain:
        for i in range(5):
            xx = x + (i - 2) * s * .26; yy = y + s * .6 + ((t * 80 + i * 17) % 26)
            c.line([(xx, yy), (xx - 4, yy + 12)], max(2, s * .06), (110, 160, 230))

def sandwich(c, x, y, s):
    c.rect(x - s * .6, y - s * .1, x + s * .6, y + s * .42, fill=(226, 180, 112), r=s * .18)
    c.rect(x - s * .64, y + s * .02, x + s * .64, y + s * .12, fill=(110, 190, 90), r=s * .05)
    c.rect(x - s * .58, y + s * .12, x + s * .58, y + s * .2, fill=(230, 80, 70), r=s * .04)
    c.rect(x - s * .6, y + s * .2, x + s * .6, y + s * .27, fill=(255, 214, 90))
    c.ell(x, y - s * .1, s * .62, s * .34, fill=(240, 200, 130))

def tvicon(c, x, y, s):
    c.rect(x - s * .6, y - s * .45, x + s * .6, y + s * .4, fill=(40, 42, 60), r=s * .08)
    c.rect(x - s * .5, y - s * .36, x + s * .5, y + s * .28, fill=(90, 150, 230))
    c.ell(x, y - s * .06, s * .17, fill=(250, 220, 190)); c.rect(x - s * .2, y + s * .08, x + s * .2, y + s * .28, fill=(40, 40, 70))

def vsicon(c, x, y, s):
    c.ell(x - s * .3, y, s * .38, fill=(220, 70, 80)); c.ell(x + s * .3, y, s * .38, fill=(70, 110, 220))
    c.text(x, y, 'vs', int(s * .5), (255, 255, 255), 'mm', bold=True)

ICON = {'cold': lambda c, x, y, s, t=0: snow(c, x, y, s * .5), 'hot': lambda c, x, y, s, t=0: sun(c, x, y, s * .36, t),
        'rain': lambda c, x, y, s, t=0: cloud(c, x, y - s * .1, s * .8, rain=True, t=t), 'food': lambda c, x, y, s, t=0: sandwich(c, x, y, s),
        'tv': lambda c, x, y, s, t=0: tvicon(c, x, y, s), 'vs': lambda c, x, y, s, t=0: vsicon(c, x, y, s)}

def bubble(c, x, y, txt, a, tail, icon=None, sz=26, t=0):
    if a <= 0: return
    wd = F(sz, True).getlength(txt) / K + 40 + (60 if icon else 0)
    hh = 60
    sc = 0.6 + 0.4 * a
    x0, x1 = x - wd / 2 * sc, x + wd / 2 * sc
    c.poly([(x - 14 * sc, y + hh / 2 * sc - 2), (x + 14 * sc, y + hh / 2 * sc - 2), (tail[0], tail[1])], (252, 250, 244))
    c.rect(x0, y - hh / 2 * sc, x1, y + hh / 2 * sc, fill=(252, 250, 244), r=24 * sc)
    if a > 0.7:
        if icon:
            ICON[icon](c, x0 + 36, y, 40, t)
            c.text(x + 30, y, txt, sz, (50, 40, 56), 'mm', bold=True)
        else:
            c.text(x, y, txt, sz, (50, 40, 56), 'mm', bold=True)

# ---------- the break room ----------
def window_view(c, t, wx):
    x0, y0, x1, y1 = 880, 90, 1170, 340
    cols = {'cold': ((176, 196, 222), (226, 236, 248)), 'hot': ((255, 166, 90), (255, 224, 140)), 'rain': ((112, 124, 148), (150, 160, 182)), 'fair': ((120, 176, 236), (200, 228, 250)), 'night': ((24, 28, 60), (60, 56, 100)), 'dawn': ((255, 176, 120), (255, 224, 170))}
    top, bot = cols[wx]
    for i in range(25):
        c.rect(x0, y0 + (y1 - y0) * i / 25, x1, y0 + (y1 - y0) * (i + 1) / 25 + 1, fill=lerpc(top, bot, i / 24))
    if wx == 'hot': sun(c, 1030, 200, 46, t)
    if wx == 'cold':
        for i in range(26):
            sx = x0 + (i * 53 + math.sin(t + i) * 12) % (x1 - x0); sy = y0 + (t * 40 + i * 37) % (y1 - y0)
            c.ell(sx, sy, 2.4, fill=(255, 255, 255))
    if wx == 'rain':
        cloud(c, 980, 140, 90, (96, 106, 128)); cloud(c, 1100, 170, 80, (110, 120, 142))
        for i in range(40):
            sx = x0 + (i * 37) % (x1 - x0); sy = y0 + (t * 260 + i * 53) % (y1 - y0)
            c.line([(sx, sy), (sx - 4, sy + 14)], 1.6, (190, 210, 250))
    c.rect(x0 - 8, y0 - 8, x1 + 8, y1 + 8, outline=(250, 248, 240), w=10)
    c.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], 8, (250, 248, 240)); c.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], 8, (250, 248, 240))
    c.rect(x0 - 16, y1 + 8, x1 + 16, y1 + 22, fill=(236, 232, 222))

def room(c, t, wx='fair', hands=None, dim=0.0, cal=True):
    for i in range(30):
        c.rect(0, FY * i / 30, W, FY * (i + 1) / 30 + 1, fill=lerpc((190, 226, 208), (172, 212, 192), i / 29))
    c.rect(0, 400, W, FY, fill=(122, 176, 156)); c.rect(0, 396, W, 408, fill=(236, 240, 228))
    c.rect(0, FY, W, H, fill=(204, 164, 122))
    for x in range(-40, W + 60, 90): c.line([(x, FY), (x - 30, H)], 2, (180, 140, 100))
    c.rect(0, FY - 4, W, FY + 8, fill=(240, 236, 224))
    window_view(c, t, wx)
    # fridge
    c.rect(560, 190, 660, FY, fill=(214, 222, 228), r=8); c.line([(560, 330), (660, 330)], 3, (160, 170, 180)); c.rect(640, 230, 646, 300, fill=(150, 160, 170)); c.rect(640, 350, 646, 420, fill=(150, 160, 170))
    for (mx, my, mc) in ((590, 240, (230, 90, 90)), (620, 262, (90, 150, 230)), (588, 290, (240, 200, 80))): c.rect(mx - 10, my - 8, mx + 10, my + 8, fill=mc)
    # counter and coffee machine
    c.rect(40, 440, 520, FY, fill=(150, 110, 86)); c.rect(30, 426, 530, 444, fill=(236, 232, 224))
    c.rect(100, 340, 190, 426, fill=(40, 42, 54), r=6); c.ell(145, 372, 10, fill=(230, 70, 70)); c.rect(122, 396, 168, 426, fill=(230, 226, 214))
    c.rect(280, 372, 400, 426, fill=(220, 224, 230), r=6); c.rect(292, 384, 360, 414, fill=(60, 70, 86))
    # wall clock and calendar
    c.ell(760, 130, 46, fill=(250, 248, 240), outline=(60, 60, 70), w=5)
    h_ = t * (hands or 0.4)
    c.line([(760, 130), (760 + 34 * math.sin(h_ * 12), 130 - 34 * math.cos(h_ * 12))], 3, (40, 40, 50)); c.line([(760, 130), (760 + 22 * math.sin(h_), 130 - 22 * math.cos(h_))], 5, (40, 40, 50))
    if cal:
        c.rect(250, 100, 380, 220, fill=(250, 248, 240), outline=(80, 70, 70), w=3); c.rect(250, 100, 380, 132, fill=(220, 70, 70))
        c.text(315, 116, 'TUESDAY', 18, (255, 255, 255), 'mm', bold=True); c.text(315, 172, '12', 54, (60, 50, 60), 'mm', bold=True)
    if dim > 0: c.veil(0, 0, W, H, (10, 12, 32), dim)

def pair(c, t, pm='flat', dm='flat', talk=0, arms_p=(0, 10), arms_d=(0, 10), px=380, dx=840, h=390):
    person(c, px, 640, h, PELL, dir=1, mood=pm, talk=t * 9 if talk == 1 else 0, arms=arms_p, nod=math.sin(t * 2) * .3)
    person(c, dx, 640, h, DANA, dir=-1, mood=dm, talk=t * 9 + 1 if talk == 2 else 0, arms=arms_d, nod=math.sin(t * 2 + 1) * .3)

# ---------- scenes ----------
def s0(c, u, k):
    sn = sentences(k)
    room(c, u, 'cold')
    sp = 1 if st(k, 1) <= u < en(k, 1) else (2 if st(k, 2) <= u < en(k, 2) else 0)
    pair(c, u, 'talk' if sp == 1 else 'flat', 'talk' if sp == 2 else 'flat', sp)
    for (i, txt, x, y, tail, ic) in ((1, "It's cold today.", 330, 190, (380, 260), 'cold'), (2, 'Freezing.', 900, 250, (850, 300), 'cold')):
        a = ramp(u, st(k, i), st(k, i) + 0.3)
        if u > st(k, i) - 0.1: bubble(c, x, y, txt, a, tail, ic, t=u)
    a = ramp(u, 0.3, 1.5) * (1 - ramp(u, 3.2, 3.8))
    if a > 0:
        c.veil(0, 40, W, 190, (10, 14, 30), 0.5 * a)
        c.text(640, 96, 'NICE WEATHER', 72, tuple(int(255 * a) for _ in range(3)), 'mm', bold=True, serif=True)
        c.text(640, 150, 'a short film about small talk', 24, (int(255 * a), int(220 * a), int(180 * a)), 'mm', serif=True)
    fcol(c, ramp(u, 0, 1.2))
    sub(c, k, u)

def s1(c, u, k):
    sn = sentences(k)
    wx = 'cold' if u < st(k, 0) + 0.3 else ('hot' if u < st(k, 1) + 0.2 else 'fair')
    room(c, u, wx, hands=2.0)
    spk = [0, 1, 2, 1, 2, 1]
    cur = max((i for i in range(6) if u >= st(k, i) - 0.05), default=0)
    sp = spk[cur]
    pair(c, u, 'talk' if sp == 1 else 'flat', 'talk' if sp == 2 else 'flat', sp)
    spec = [(0, 'Too hot.', 'hot', 330, 190), (1, 'Lunch time.', 'food', 900, 210), (2, 'What did you have?', 'food', 330, 190), (3, 'A sandwich.', 'food', 900, 230), (4, 'Any good?', 'food', 330, 190), (5, 'Not bad.', None, 900, 230)]
    for (i, txt, ic, x, y) in spec:
        if cur == i:
            a = ramp(u, st(k, i), st(k, i) + 0.25)
            bubble(c, x, y, txt, a, (x + (50 if x < 640 else -50), y + 80), ic, t=u)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def pundit(c, x, y, w, h, t, side):
    c.rect(x, y, x + w, y + h, fill=(30, 32, 44), r=10)
    scr = (x + 10, y + 10, x + w - 10, y + h - 40)
    c.rect(*scr, fill=(70, 110, 190) if side == 0 else (190, 80, 80))
    fx = x + w / 2; fy = y + h * 0.42
    c.rect(fx - 40, fy + 20, fx + 40, y + h - 40, fill=(40, 40, 60))
    c.ell(fx, fy, 34, fill=(240, 204, 176)); c.ell(fx, fy - 12, 36, 26, fill=(80, 70, 70))
    c.ell(fx - 12, fy - 4, 3, fill=(40, 30, 30)); c.ell(fx + 12, fy - 4, 3, fill=(40, 30, 30))
    c.ell(fx, fy + 16, 10, 3 + 7 * abs(math.sin(t * 9 + side)), fill=(120, 40, 50))
    c.rect(x + 10, y + h - 40, x + w - 10, y + h - 8, fill=(240, 220, 80))
    txt = '   THE OTHER SIDE IS WORSE   ' * 3
    off = (t * 60) % 400
    c.text(x + 14 - off + 0, y + h - 24, txt, 18, (40, 30, 20), 'lm', bold=True) if False else c.text(x + w / 2, y + h - 24, 'THE OTHER SIDE IS WORSE', 16, (40, 30, 20), 'mm', bold=True)

def s2(c, u, k):
    room(c, u, 'rain', hands=2.4)
    pundit(c, 880, 80, 280, 220, u, 0)
    cur = max((i for i in range(4) if u >= st(k, i) - 0.05), default=0)
    nod = math.sin(u * 5) * (1.0 if cur >= 2 else 0.2)
    person(c, 330, 640, 390, PELL, dir=1, mood='flat', arms=(0, 10), nod=nod, talk=u * 9)
    person(c, 640, 640, 390, DANA, dir=1, mood='talk' if cur == 1 else 'flat', talk=u * 9, arms=(0, 10), nod=nod)
    person(c, 980, 640, 390, EXTRA[0], dir=-1, mood='flat', arms=(0, 10), nod=nod)
    if cur == 0: bubble(c, 400, 200, 'Did you see what he said?', ramp(u, st(k, 0) + 0.3, st(k, 0) + 0.7), (350, 270), 'tv', t=u)
    if cur == 1: bubble(c, 700, 190, 'He is wrong. The other side is worse.', ramp(u, st(k, 1), st(k, 1) + 0.3), (650, 270), 'vs', t=u)
    if cur >= 2:
        a = ramp(u, st(k, 2), st(k, 2) + 0.5)
        for (i, x) in enumerate((330, 640, 980)):
            c.text(x, 330 - 6 * math.sin(u * 5 + i), 'yes', 30, (int(250 * a), int(250 * a), int(230 * a)), 'mm', bold=True)
    if cur >= 3:
        a = ramp(u, st(k, 3), st(k, 3) + 0.6)
        c.veil(0, 430, W, 470, (10, 10, 30), 0) if False else None
        c.text(640, 410, 'opinions before: same   ·   after: same', 30, (int(40 * a), int(40 * a), int(60 * a)), 'mm', bold=True) if False else None
        c.veil(300, 24, 980, 74, (10, 12, 30), 0.6 * a)
        c.text(640, 49, 'opinions before: same    after: same', 28, (int(255 * a), int(230 * a), int(150 * a)), 'mm', bold=True)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s3(c, u, k):
    c.im.paste(sky('warm'), (0, 0)) if False else None
    room(c, u, 'fair', hands=2.0, dim=0.1)
    sn = sentences(k)
    names = ['Weather', 'Food', 'Headlines', 'The other side']
    icons = ['hot', 'food', 'tv', 'vs']
    for i in range(4):
        a = ramp(u, st(k, i + 1), st(k, i + 1) + 0.4)
        x = 230 + i * 270
        c.veil(x - 110, 56, x + 110, 160, (10, 12, 30), 0.55 * a)
        if a > 0.2:
            ICON[icons[i]](c, x - 60, 108, 52, u)
            c.text(x + 18, 108, names[i], 22, (int(255 * a), int(250 * a), int(230 * a)), 'mm', bold=True)
    pair(c, u, 'flat', 'flat', 0, arms_p=(0, 90), arms_d=(0, 90), px=270, dx=1010)
    # the ball
    t0 = st(k, 5)
    per = 1.6
    tt = u if u < t0 else u
    ph = (u / per) % 2
    f = ph if ph < 1 else 2 - ph
    f = ease(f) if True else f
    x = lerp(340, 940, f); y = 330 - 150 * math.sin(math.pi * f) * (1 if True else 0) + 160 * 0
    y = 380 - 170 * math.sin(math.pi * ((u / per) % 1))
    idx = int(u / per) % 4
    c.ell(x, y, 46, fill=(250, 246, 235), outline=(70, 60, 80), w=4)
    ICON[icons[idx]](c, x, y, 52, u)
    c.ell(x, 600, 34 - 8 * math.sin(math.pi * ((u / per) % 1)), 8, fill=(150, 112, 84))
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s4(c, u, k):
    room(c, u, 'rain', hands=3.0, cal=False)
    # flipping calendar pages
    f = u * 7
    c.rect(210, 90, 450, 330, fill=(250, 248, 240), outline=(80, 70, 70), w=4); c.rect(210, 90, 450, 142, fill=(220, 70, 70))
    c.text(330, 116, 'TUESDAY', 30, (255, 255, 255), 'mm', bold=True)
    c.text(330, 214, str(1 + int(f) % 28), 90, (60, 50, 60), 'mm', bold=True)
    c.text(330, 296, '1,560 workdays of weather', 18, (120, 60, 60), 'mm', bold=True)
    s0_ = st(k, 1) - 0.4
    still = u > s0_
    person(c, 820, 640, 440, JUNO, dir=-1, mood='fake' if not still else 'flat', arms=(0, 10 if still else 40 + 30 * math.sin(u * 4)), nod=math.sin(u * 3) * (0.0 if still else 1), t=u)
    person(c, 480, 640, 400, PELL, dir=1, mood='talk' if not still else 'o', talk=u * 9, arms=(0, 30), t=u)
    if not still: bubble(c, 520, 215, "Looks like rain again...", ramp(u, st(k, 0), st(k, 0) + 0.5), (490, 320), 'rain', t=u)
    elif u < st(k, 1) + 2.4: bubble(c, 520, 215, "Looks like rain a-", ramp(u, st(k, 1) + 0.4, st(k, 1) + 0.8), (490, 320), 'rain', t=u)
    if still:
        c.veil(0, 0, W, H, (6, 8, 20), 0.35 * ramp(u, s0_, s0_ + 1.0))
        person(c, 820, 640, 440, JUNO, dir=-1, mood='flat', arms=(0, 10), t=u)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s5(c, u, k):
    room(c, u, 'rain', hands=0.6, dim=0.1)
    person(c, 330, 640, 400, PELL, dir=1, mood='flat', arms=(0, 10), nod=0)
    person(c, 640, 640, 400, DANA, dir=1, mood='flat', arms=(0, 10), nod=0)
    person(c, 1010, 640, 440, JUNO, dir=-1, mood='talk', talk=u * 8, arms=(0, 40 + 20 * math.sin(u * 3)))
    for (i, txt, y) in ((1, 'When you talk about the weather, I learn nothing about you.', 160), (2, 'If you never mentioned it again, nothing would change.', 160)):
        if st(k, i) - 0.1 <= u <= en(k, i) + 0.5:
            a = ramp(u, st(k, i), st(k, i) + 0.3) * (1 - ramp(u, en(k, i) + 0.2, en(k, i) + 0.5))
            if i == 2 or True:
                bubble(c, 820 if i == 1 else 780, 250, txt if i == 1 else txt, a, (990, 330), None, 25)
    if st(k, 0) <= u <= en(k, 0) + 0.6:
        bubble(c, 800, 250, "I'm not being rude.", ramp(u, st(k, 0), st(k, 0) + 0.3), (990, 330), None, 26)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s6(c, u, k):
    sn = sentences(k)
    f = ramp(u, 0, 4)
    room(c, u, 'rain', hands=0.1, dim=0.55 * f)
    person(c, 330, 640, 400, PELL, dir=1, mood='talk' if (st(k, 1) < u < st(k, 1) + 1.2) else 'flat', talk=u * 5, arms=(0, 10))
    person(c, 640, 640, 400, DANA, dir=1, mood='flat', arms=(0, 60 if st(k, 2) < u < en(k, 2) - .5 else 10))
    person(c, 1010, 640, 440, JUNO, dir=-1, mood='flat', arms=(0, 10))
    # popping topic bubbles
    r = random.Random(3)
    ics = ['cold', 'hot', 'rain', 'food', 'tv', 'vs']
    for i in range(10):
        s_ = st(k, 0) + 0.2 + i * 0.5
        if u < s_: continue
        life = u - s_
        x = 300 + r.uniform(0, 700) + 20 * math.sin(life * 2 + i); y = 360 - life * 50
        if life < 2.0:
            c.ell(x, y, 38, fill=None, outline=(230, 240, 255), w=2.5)
            ICON[ics[i % 6]](c, x, y, 40, u)
        elif life < 2.25:
            for j in range(8):
                a = j * math.pi / 4
                c.line([(x + math.cos(a) * 40, y + math.sin(a) * 40), (x + math.cos(a) * 56, y + math.sin(a) * 56)], 2, (230, 240, 255))
    if st(k, 0) < u < en(k, 1) and int(u * 2) % 2: c.text(640, 520, '. . .', 54, (250, 250, 250), 'mm', bold=True)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def qcard(c, x, y, txt, a, u):
    if a <= 0: return
    sc = ease(a)
    w = 360 * sc; h = 110 * sc
    c.rect(x - w / 2 + 6, y - h / 2 + 8, x + w / 2 + 6, y + h / 2 + 8, fill=(10, 10, 20), r=14)
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=(255, 244, 214), r=14, outline=(200, 70, 70), w=4)
    if a > 0.8: c.text(x, y, txt, 30, (60, 40, 50), 'mm', bold=True, serif=True)

def s7(c, u, k):
    room(c, u, 'rain', hands=0.1, dim=0.35)
    shrug = ramp(u, st(k, 4), st(k, 4) + 0.3) * (1 - ramp(u, st(k, 4) + 1.2, st(k, 4) + 1.6))
    person(c, 330, 640, 400, PELL, dir=1, mood='o' if u > st(k, 2) else 'flat', arms=(0, 10 + 90 * ramp(u, st(k, 2), st(k, 2) + 0.2) * (1 - ramp(u, st(k, 2) + .9, st(k, 2) + 1.2))))
    person(c, 640, 640, 400, DANA, dir=1, mood='flat', arms=(30 * shrug, 10 + 140 * shrug))
    person(c, 1010, 640, 440, JUNO, dir=-1, mood='talk' if any(st(k, i) < u < en(k, i) for i in (1, 3, 5)) else 'flat', talk=u * 8, arms=(0, 70))
    for (i, txt, y) in ((1, 'What do you value?', 150), (3, 'What do you want?', 230), (5, 'What are your goals?', 310)):
        qcard(c, 820, y, txt, ramp(u, st(k, i), st(k, i) + 0.35), u)
    # Pell blink
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def card(c, x, y, head, body, a, u):
    if a <= 0: return
    yy = y - (1 - ease(a)) * 200
    c.rect(x - 150 + 5, yy - 70 + 7, x + 150 + 5, yy + 70 + 7, fill=(30, 30, 50), r=6)
    c.rect(x - 150, yy - 70, x + 150, yy + 70, fill=(252, 246, 226), r=6)
    c.rect(x - 150, yy - 70, x + 150, yy - 44, fill=(220, 90, 90), r=6)
    for i in range(3): c.line([(x - 136, yy - 20 + i * 28), (x + 136, yy - 20 + i * 28)], 1.4, (150, 190, 230))
    c.text(x, yy - 56, head.upper(), 17, (255, 255, 255), 'mm', bold=True)
    c.text(x, yy + 8, body, 24, (50, 50, 90), 'mm', serif=True)

def s8(c, u, k):
    room(c, u, 'rain', hands=0.1, dim=0.45)
    # filing cabinet
    c.rect(60, 250, 270, FY, fill=(120, 130, 150), r=4)
    op = ramp(u, 0.6, 2.2)
    for i in range(3):
        yy = 262 + i * 100
        if i == 0:
            c.rect(70, yy, 260 + 70 * op, yy + 88 if False else yy + 88, fill=(150, 160, 180), r=4)
            c.rect(120, yy + 10, 210 + 70 * op, yy + 30, fill=(100, 110, 130)) if False else None
            c.rect(120, yy + 36, 210, yy + 52, fill=(230, 230, 240))
        else:
            c.rect(70, yy, 260, yy + 88, fill=(150, 160, 180), r=4); c.rect(120, yy + 36, 210, yy + 52, fill=(230, 230, 240))
    # dust
    for i in range(18):
        dx = 150 + (i * 31) % 160 + 20 * math.sin(u * .8 + i); dy = 280 + (i * 17 + u * 12) % 80
        c.ell(dx, dy, 1.6, fill=(240, 232, 214))
    cards = [(1, 'Values', 'have a good life'), (2, 'Character', 'be a good person'), (3, 'Desires', 'do fun stuff'), (4, 'Goals', 'survive the month')]
    for (i, (si, hd, bd)) in enumerate(cards):
        a = ramp(u, st(k, si), st(k, si) + 0.6)
        card(c, 470 + (i % 2) * 330, 250 + (i // 2) * 170, hd, bd, a, u)
    person(c, 1090, 640, 420, JUNO, dir=-1, mood='flat', arms=(0, 60))
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def box(c, x, y, w, h, label, lid):
    c.rect(x - w / 2, y - h, x + w / 2, y, fill=(196, 150, 96), r=3)
    c.rect(x - w / 2, y - h, x + w / 2, y - h + 12, fill=(176, 130, 80))
    if lid > 0:
        c.rect(x - w / 2 + 4, y - h + 12, x + w / 2 - 4, y - h + 34, fill=(24, 20, 24))
        c.glow(x, y - h + 24, 60, (255, 230, 170), .1 * lid)
        for i in range(6): c.line([(x - w / 2 + 6, y - h + 14 + i * 4), (x - w / 2 + 6 + 14 * (1 + i % 2), y - h + 14 + i * 4 - 4)], 1, (200, 200, 210))
    c.rect(x - w / 2 + 12, y - h * .62, x + w / 2 - 12, y - h * .28, fill=(250, 246, 232))
    c.text(x, y - h * .45, label, 20, (40, 30, 40), 'mm', bold=True)

def s9(c, u, k):
    room(c, u, 'rain', hands=0.1, dim=0.3)
    lid = ramp(u, st(k, 2) + 0.2, st(k, 2) + 1.0)
    c.rect(130, 470, 1150, 500, fill=(150, 110, 86)); c.rect(150, 500, 170, FY, fill=(120, 86, 66)); c.rect(1110, 500, 1130, FY, fill=(120, 86, 66))
    for (i, lb) in enumerate(('VALUES', 'CHARACTER', 'DESIRES', 'GOALS')):
        box(c, 330 + i * 190, 470, 140, 120, lb, lid if i == 0 else 0)
    if lid > 0.1:
        c.poly([(330 - 70, 350 - 40 * lid), (330 + 70, 350 - 40 * lid), (330 + 76, 360 - 40 * lid), (330 - 76, 360 - 40 * lid)], (176, 130, 80))
    person(c, 1010, 640, 420, JUNO, dir=-1, mood='flat', arms=(0, 70 + 40 * lid))
    person(c, 120, 640, 420, PELL, dir=1, mood='o' if lid > 0.2 else 'flat', arms=(0, 10))
    if lid > 0.5:
        c.text(330, 316, 'empty', 26, (int(240 * lid), int(230 * lid), int(200 * lid)), 'mm', serif=True)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s10(c, u, k):
    f = ramp(u, st(k, 1) - 0.5, st(k, 1) + 1.5)
    room(c, u, 'rain', hands=0.1 * (1 - f) + 0.02, dim=0.2 + 0.4 * f)
    # carousel of topics
    spin = (1 - f)
    ics = ['cold', 'hot', 'rain', 'food', 'tv', 'vs']
    ang0 = u * 1.6 * (1 - f) + 3 * f
    for i in range(6):
        a = ang0 + i * math.pi / 3
        x = 640 + 380 * math.cos(a); y = 200 + 60 * math.sin(a)
        al = 1 - 0.8 * f
        if al > 0.05:
            c.ell(x, y, 40, fill=(250, 248, 240) if f < 0.5 else (170, 170, 190), outline=(60, 60, 80), w=3)
            ICON[ics[i]](c, x, y, 44, u)
    person(c, 440, 640, 420, PELL, dir=1, mood='flat', arms=(0, 10))
    person(c, 840, 640, 420, DANA, dir=-1, mood='flat', arms=(0, 10))
    a = ramp(u, st(k, 1) + 1.8, st(k, 1) + 3.0)
    if a > 0:
        for x in (440, 840):
            c.glow(x, 440, 120, (255, 220, 160), .4 * a)
            for (dx0, dy0, dx1, dy1) in ((-34, -22, 34, -22), (34, -22, 34, 30), (34, 30, -34, 30), (-34, 30, -34, -22)):
                c.line([(x + dx0, 440 + dy0), (x + dx1, 440 + dy1)], 3, (int(255 * a), int(235 * a), int(190 * a)))
            c.text(x, 442, '?', 40, (int(255 * a), int(235 * a), int(190 * a)), 'mm', bold=True)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s11(c, u, k):
    w = ramp(u, st(k, 1) - 1, st(k, 3) + 1)
    room(c, u, 'dawn' if w > 0.5 else 'rain', hands=0.1, dim=0.35 * (1 - w))
    c.veil(0, 0, W, H, (255, 200, 140), 0.15 * w)
    person(c, 380, 700, 560, DANA, dir=1, mood='sad' if u < st(k, 1) else ('smile' if u > st(k, 3) else 'talk'), talk=u * 7, arms=(0, 20), nod=math.sin(u) * .2)
    person(c, 1050, 700, 440, PELL, dir=-1, mood='o' if u < st(k, 3) else 'smile', arms=(0, 10))
    # hammer doodle
    a = ramp(u, st(k, 1) + 0.6, st(k, 1) + 1.4)
    if a > 0:
        c.glow(380, 150, 90, (255, 220, 150), .4 * a)
        c.line([(350, 190), (400, 120)], 8, (150, 100, 60)); c.rect(376, 96, 428, 126, fill=(150, 156, 170), r=4)
    for (i, txt, y) in ((1, 'I wanted to be a carpenter.', 180), (2, 'I never told anyone.', 260), (3, 'I think I still do.', 340)):
        qcard_ = ramp(u, st(k, i), st(k, i) + 0.35)
        bubble(c, 760, y, txt, qcard_, (500, 330) if False else (560, 380 if i == 1 else 400), None, 28)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s12(c, u, k):
    f = ramp(u, 0, 3)
    room(c, u, 'rain', hands=0.15)
    c.veil(0, 0, W, H, (255, 196, 140), 0.18)
    ppl = [(JUNO, 420, 1), (DANA, 560, 1), (PELL, 720, -1), (EXTRA[1], 860, -1)]
    for i, (p, x, d) in enumerate(ppl):
        person(c, x, 590, 360, p, dir=d, mood='talk' if int(u / 1.8 + i) % 4 == i else 'smile', talk=u * 8 + i * 3, arms=(0, 20 + 15 * math.sin(u + i)), nod=math.sin(u * 1.4 + i) * .3, tint=((255, 190, 120), 0.08))
    c.rect(300, 560, 980, 590, fill=(170, 120, 80)); c.rect(330, 590, 350, 650, fill=(130, 90, 60)); c.rect(930, 590, 950, 650, fill=(130, 90, 60))
    for x in (380, 520, 700, 840):
        c.rect(x - 16, 536, x + 16, 560, fill=(250, 248, 240), r=4); c.ell(x, 536, 14, 4, fill=(110, 70, 50))
        c.line([(x, 520), (x + 4 * math.sin(u * 2 + x), 500)], 1.4, (255, 255, 255))
    a = ramp(u, DURS[k] + LEAD[k] + 0.2, DURS[k] + LEAD[k] + 1.4)
    if a > 0:
        c.veil(0, 50, W, 170, (10, 10, 30), 0.5 * a)
        v = int(255 * a)
        c.text(640, 110, 'Say something true.', 68, (v, int(v * .9), int(v * .72)), 'mm', bold=True, serif=True)
    fcol(c, ramp(u, 0, 1.0))
    c.fade((0, 0, 0), ramp(u, D[k] - 1.8, D[k] - 0.2))
    sub(c, k, u)

SCENES = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12]

def frame(n):
    t = n / FPS
    k = max(i for i in range(13) if T0[i] <= t + 1e-9)
    c = C()
    SCENES[k](c, t - T0[k], k)
    return c.out(), k
