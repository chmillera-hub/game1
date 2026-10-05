from lib import *

WREN = dict(skin=(205, 152, 116), hair=(30, 26, 32), shirt=(36, 150, 150), pants=(74, 62, 52), glasses=False, long=False)
SHOPS = [  # (colour, sign)
    ((196, 120, 96), 'COMMUNITY'), ((98, 150, 150), 'BELONGING'), ((214, 168, 90), 'CONNECTION'), ((134, 120, 176), 'THE VILLAGE'),
    ((190, 110, 130), 'HEALING'), ((104, 152, 112), 'SUPPORT'), ((200, 140, 84), 'TOGETHER'), ((112, 136, 180), 'WELCOME'),
]
SW = 320   # shop pitch
FW = 290   # facade width
FH = 330   # facade height
DW, DH = 70, 150

def sub(c, k, u):
    for (s, e, txt) in sentences(k):
        if s - 0.05 <= u <= e + 0.25:
            a = min(ramp(u, s - 0.05, s + 0.25), 1 - ramp(u, e, e + 0.25) if e < LEAD[k] + DURS[k] - 0.01 else 1)
            caption(c, txt, a); return

def st(k, i): return sentences(k)[i][0]

def bubble(c, x, y, txt, a, tail_x, sz=26):
    if a <= 0: return
    wd = F(sz, True).getlength(txt) / K + 40
    hh = 54; sc = 0.6 + 0.4 * a
    x0, x1 = x - wd / 2 * sc, x + wd / 2 * sc
    c.poly([(x - 14 * sc, y + hh / 2 * sc - 2), (x + 14 * sc, y + hh / 2 * sc - 2), (tail_x, y + hh / 2 * sc + 36)], (250, 248, 240))
    c.rect(x0, y - hh / 2 * sc, x1, y + hh / 2 * sc, fill=(250, 248, 240), r=22 * sc)
    if a > 0.7: c.text(x, y, txt, sz, (50, 40, 50), 'mm', bold=True)

# ---------- shopfronts ----------
def door(c, x, yb, w, h, openf, inside=None, col=(112, 70, 52)):
    """x = centre. openf 0 closed .. 1 wide open. Hinged on the left."""
    x0 = x - w / 2
    c.rect(x0 - 5, yb - h - 5, x0 + w + 5, yb, fill=(46, 34, 34))
    c.rect(x0, yb - h, x0 + w, yb, fill=(30, 24, 30))
    if inside: inside(c, x0, yb - h, w, h)
    wl = w * math.cos(openf * 1.25)
    sk = h * 0.05 * math.sin(openf * 1.25)
    c.poly([(x0, yb - h), (x0 + wl, yb - h + sk), (x0 + wl, yb - sk), (x0, yb)], col)
    if wl > w * 0.3:
        c.poly([(x0 + wl * .14, yb - h * .9 + sk * .3), (x0 + wl * .86, yb - h * .9 + sk * .6), (x0 + wl * .86, yb - h * .55 - sk * .2), (x0 + wl * .14, yb - h * .55)], lerpc(col, (0, 0, 0), .18))
        c.poly([(x0 + wl * .14, yb - h * .48), (x0 + wl * .86, yb - h * .48 + sk * .1), (x0 + wl * .86, yb - h * .1 - sk * .5), (x0 + wl * .14, yb - h * .1)], lerpc(col, (0, 0, 0), .18))
        c.ell(x0 + wl * .8, yb - h * .5, 3.5, fill=(226, 196, 110))

def facade(c, x, col, sign, t, a_sign=1.0, back=False, dark=False, door_open=0, inside=None, lean=0.0):
    y0 = GY - FH
    if back:
        c.rect(x - FW / 2, y0, x + FW / 2, GY, fill=(142, 112, 80))
        for i in range(1, 6): c.line([(x - FW / 2, y0 + i * FH / 6), (x + FW / 2, y0 + i * FH / 6)], 2, (112, 86, 60))
        for i in range(1, 8): c.line([(x - FW / 2 + i * FW / 8, y0), (x - FW / 2 + i * FW / 8, GY)], 1.5, (122, 94, 66))
        c.rect(x - FW / 2 - 8, y0 - 14, x + FW / 2 + 8, y0, fill=(112, 86, 60))
        # braces
        for s in (-1, 1):
            bx = x + s * FW * 0.28
            c.line([(bx, y0 + 20), (bx + s * 120, GY + 26)], 12, (120, 82, 50))
            c.line([(bx, y0 + 20), (bx + s * 120, GY + 26)], 3, (160, 118, 76))
            c.rect(bx + s * 120 - 22, GY + 18, bx + s * 120 + 22, GY + 34, fill=(100, 68, 44))
        c.rect(x - 14, y0 + FH * 0.55, x + 14, GY, fill=(98, 70, 50)) if False else None
        return
    shade = 0.35 if dark else 0.0
    cc = lerpc(col, (10, 10, 30), shade)
    c.rect(x - FW / 2, y0, x + FW / 2, GY, fill=cc)
    # painted plank stripes
    for i in range(1, 12): c.line([(x - FW / 2 + i * FW / 12, y0 + 6), (x - FW / 2 + i * FW / 12, GY - 4)], 1.2, lerpc(cc, (0, 0, 0), .12))
    c.rect(x - FW / 2 - 10, y0 - 16, x + FW / 2 + 10, y0 + 4, fill=lerpc(cc, (255, 255, 255), .22))
    c.poly([(x - 60, y0 - 16), (x + 60, y0 - 16), (x + 34, y0 - 46), (x - 34, y0 - 46)], lerpc(cc, (255, 255, 255), .12))
    # sign
    sb = lerpc((38, 32, 52), (0, 0, 0), shade)
    c.rect(x - FW / 2 + 16, y0 + 18, x + FW / 2 - 16, y0 + 78, fill=sb, r=4, outline=(236, 214, 150), w=3)
    if a_sign > 0.02:
        sz = 30 if len(sign) < 10 else 25
        v = int(255 * a_sign)
        c.glow(x, y0 + 48, 120, (255, 220, 140), 0.18 * a_sign)
        c.text(x, y0 + 49, sign, sz, (v, int(v * .9), int(v * .6)), 'mm', bold=True, serif=True)
    # painted windows (flat, no depth)
    for s in (-1, 1):
        wx = x + s * 82
        c.rect(wx - 42, y0 + 110, wx + 42, y0 + 215, fill=lerpc((170, 214, 236), (10, 10, 30), shade), outline=(250, 240, 220), w=5)
        c.line([(wx - 30, y0 + 205), (wx - 6, y0 + 120)], 6, lerpc((220, 240, 250), (10, 10, 30), shade))
        c.line([(wx, y0 + 112), (wx, y0 + 213)], 3, (250, 240, 220)); c.line([(wx - 40, y0 + 162), (wx + 40, y0 + 162)], 3, (250, 240, 220))
    door(c, x, GY, DW, DH, door_open, inside)

def street(c, t, cam=0, signs=None, dark=False, lamps=True):
    c.im.paste(sky('dusk'), (0, 0))
    for (x, y, r, ph) in STARS[:60]:
        b = (0.5 + 0.5 * math.sin(t * 1.6 + ph)) * 0.35; v = int(255 * b)
        c.ell(x, y * 0.7, r, fill=(v, v, min(255, v + 20)))
    hills(c, t, 'dusk', cam * 0.3)
    c.rect(0, GY, W, H, fill=(88, 72, 84))
    for i in range(0, 14):   # cobbles
        yy = GY + 8 + i * 14
        for j in range(-1, 14):
            ox = (j * 110 + (i % 2) * 55 - cam * (1 + i * .05)) % (W + 110) - 55
            c.rect(ox, yy, ox + 100, yy + 10, fill=(100 + (i * 3) % 14, 84, 94), r=4)
    c.rect(0, GY - 3, W, GY + 6, fill=(60, 50, 62))
    base = int(cam // SW) - 1
    for i in range(base, base + 6):
        x = i * SW - cam + 100
        col, sign = SHOPS[i % len(SHOPS)]
        a = 1.0 if signs is None else signs(i % len(SHOPS))
        if -FW <= x <= W + FW:
            facade(c, x, col, sign, t, a, dark=dark)
        if lamps:
            lx = x + SW / 2
            c.rect(lx - 3, GY - 190, lx + 3, GY, fill=(40, 34, 42))
            lantern(c, lx, GY - 196, t + i, 1.1)

def backlot(c, t, cam=0, mode='night'):
    c.im.paste(sky('night'), (0, 0))
    for (x, y, r, ph) in STARS:
        b = (0.55 + 0.45 * math.sin(t * 1.6 + ph)); v = int(255 * b)
        c.ell(x, y, r, fill=(v, v, min(255, v + 20)))
    hills(c, t, 'night', cam * 0.3)
    c.rect(0, GY, W, H, fill=(52, 42, 46))
    r = random.Random(5)
    for i in range(50):
        wx = (r.uniform(0, W * 3) - cam) % W
        c.line([(wx, GY + r.uniform(10, 150)), (wx + r.uniform(-4, 4), GY + r.uniform(0, 8))], 1.4, (70, 110, 70))
    base = int(cam // SW) - 1
    for i in range(base, base + 6):
        x = i * SW - cam + 100
        facade(c, x, SHOPS[i % 8][0], '', t, 0, back=True)

# ---------- small props ----------
def glyph_house(c, cx, cy, s, a, t):
    pulse = 0.85 + 0.15 * math.sin(t * 2)
    c.glow(cx, cy, s * 2.4, (255, 200, 120), 0.5 * a * pulse)
    col = lerpc((30, 26, 50), (255, 226, 160), a)
    c.poly([(cx - s, cy), (cx, cy - s * .9), (cx + s, cy)], col)
    c.rect(cx - s * .8, cy - 2, cx + s * .8, cy + s * .8, fill=col)
    for dx, hh in ((-.4, .38), (0, .46), (.4, .3)):
        c.ell(cx + dx * s, cy + s * .8 - hh * s - 8, s * .1, fill=(110, 70, 60))
        c.rect(cx + dx * s - s * .09, cy + s * .8 - hh * s, cx + dx * s + s * .09, cy + s * .8, fill=(110, 70, 60), r=s * .05)

def table(c, x, y, w=120, h=70):
    c.rect(x - w / 2, y - h, x + w / 2, y - h + 10, fill=(150, 104, 70))
    c.rect(x - w / 2 + 8, y - h + 10, x - w / 2 + 14, y, fill=(110, 76, 52)); c.rect(x + w / 2 - 14, y - h + 10, x + w / 2 - 8, y, fill=(110, 76, 52))

def lamp(c, x, y, t, a=1.0):
    c.glow(x, y - 20, 70, (255, 200, 120), 0.5 * a)
    c.rect(x - 2, y - 24, x + 2, y, fill=(60, 50, 50)); c.poly([(x - 12, y - 24), (x + 12, y - 24), (x + 6, y - 38), (x - 6, y - 38)], (236, 190, 100))

def beam(c, x0, y0, x1, y1, w=14):
    c.line([(x0, y0), (x1, y1)], w, (170, 122, 76))
    c.line([(x0, y0 - w * .25), (x1, y1 - w * .25)], 2.2, (206, 158, 104))

def fcol(c, a): c.fade((0, 0, 0), 1 - a)

# ---------- scenes ----------
def s0(c, u, k):
    sn = sentences(k)
    def sg(i):
        # sign i lights up with its word; first one at sentence 1
        if i > 3: return 1.0 if u > sn[4][1] else 0.0
        return ramp(u, sn[i + 1][0] if i < 4 else 0, sn[i + 1][0] + 0.5)
    street(c, u, cam=u * 22, signs=sg)
    a = ramp(u, 0.3, 1.5) * (1 - ramp(u, 3.0, 3.5))
    if a > 0:
        c.text(640, 140, 'MERROW GREEN', 74, tuple(int(255 * a) for _ in range(3)), 'mm', bold=True, serif=True)
        c.text(640, 196, 'a small film', 24, (int(255 * a), int(215 * a), int(170 * a)), 'mm', serif=True)
    fcol(c, ramp(u, 0, 1.2))
    sub(c, k, u)

def s1(c, u, k):
    street(c, u, cam=300 + u * 6)
    c.veil(0, 0, W, H, (8, 8, 30), 0.18)
    person(c, 400, GY + 130, 360, WREN, dir=1, mood='smile' if u > 2 else 'flat', arms=(0, 12 + 4 * math.sin(u * 2)), t=u)
    a = ramp(u, st(k, 1) + 0.3, st(k, 1) + 1.6)
    if a > 0:
        cx, cy = 640, 170
        for (dx, dy, r_) in ((-16, 60, 6), (-30, 90, 10)):
            c.ell(cx - 100 + dx * 0 + dx, cy + 120 + dy * 0, r_ * a, fill=(250, 244, 230)) if False else None
        c.ell(470, 250, 7 * a, fill=(250, 244, 230)); c.ell(500, 218, 11 * a, fill=(250, 244, 230))
        for (dx, dy, r_) in ((-70, 0, 60), (0, -18, 74), (70, 0, 60), (-30, 30, 56), (40, 34, 56)):
            c.ell(cx + dx, cy + dy, r_ * a, fill=(250, 244, 230))
        glyph_house(c, cx, cy + 6, 58 * a, a, u)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s2(c, u, k):
    street(c, u, cam=520, lamps=False)
    c.veil(0, 0, W, H, (8, 8, 30), 0.25)
    kn = math.sin(u * 9) if u < st(k, 1) else 0
    person(c, 430, GY + 150, 400, WREN, dir=1, mood='flat', arms=(0, 100 + 12 * kn if u < st(k, 1) else 20), talk=u * 8, t=u)
    if u >= st(k, 1): pass
    a = ramp(u, st(k, 1) + 0.1, st(k, 1) + 0.5)
    bubble(c, 640, 150, 'I want to build a life with another person.', a, 500, 28)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def peek(c, x0, y0, w, h, p, mood='fake'):
    person(c, x0 + w * 0.55, y0 + h + 40, 300, p, dir=-1, mood=mood, nod=0, arms=(0, 0))

def s3(c, u, k):
    street(c, u, cam=520, lamps=False)
    c.veil(0, 0, W, H, (8, 8, 30), 0.25)
    sn = sentences(k)
    o = ramp(u, sn[0][0], sn[0][0] + 0.9) * 0.16
    yb = GY + 130
    vl = villager(41)
    def inside(cc, x0, y0, w, h):
        cc.rect(x0, y0, x0 + w, y0 + h, fill=(60, 44, 50)); cc.glow(x0 + w / 2, y0 + h / 2, 160, (255, 190, 120), 0.35)
        if o > 0.02:
            person(cc, x0 + w * 0.62, y0 + h + 40, 460, vl, dir=-1, mood='fake', arms=(0, 0), nod=math.sin(u * 3) * 0.3)
    # redraw with person inside the doorway (before leaf)
    c.rect(800 - 130, yb - 440, 800 + 130, yb, fill=(30, 24, 30))
    inside(c, 800 - 130, yb - 440, 260, 440)
    wl = 260 * math.cos(ramp(u, sn[0][0], sn[0][0] + 0.9) * 0.95)
    x0 = 800 - 130
    c.poly([(x0, yb - 440), (x0 + wl, yb - 440 + 6), (x0 + wl, yb - 6), (x0, yb)], (112, 70, 52))
    c.poly([(x0 + wl * .14, yb - 400), (x0 + wl * .86, yb - 396), (x0 + wl * .86, yb - 250), (x0 + wl * .14, yb - 250)], (92, 56, 42))
    c.poly([(x0 + wl * .14, yb - 220), (x0 + wl * .86, yb - 218), (x0 + wl * .86, yb - 50), (x0 + wl * .14, yb - 50)], (92, 56, 42))
    c.ell(x0 + wl * .8, yb - 210, 7, fill=(226, 196, 110))
    person(c, 330, GY + 150, 400, WREN, dir=1, mood='flat', arms=(0, 10), t=u)
    lines = ["", "Have you tried the app?", "You'll find someone.", "Don't worry about it.", "Focus on yourself."]
    for i in range(1, 5):
        s_, e_ = sn[i][0], sn[i][1]
        if s_ - 0.05 <= u <= e_ + 0.5:
            bubble(c, 1050, 200, lines[i], ramp(u, s_, s_ + 0.25) * (1 - ramp(u, e_ + 0.25, e_ + 0.5)), 880, 28 if i != 4 else 28)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s4(c, u, k):
    c.im.paste(sky('dusk'), (0, 0))
    c.veil(0, 0, W, H, (8, 8, 30), 0.3)
    c.rect(0, GY, W, H, fill=(80, 66, 78))
    sn = sentences(k)
    for i in range(5):
        x = 160 + i * 240
        cl = ramp(u, sn[1][0] + 0.4 + i * 0.35, sn[1][0] + 1.1 + i * 0.35)
        vl = villager(50 + i)
        def inside(cc, x0, y0, w, h, i=i, vl=vl):
            cc.rect(x0, y0, x0 + w, y0 + h, fill=(60, 44, 50)); cc.glow(x0 + w / 2, y0 + h / 2, 90, (255, 190, 120), 0.3)
            person(cc, x0 + w * 0.55, y0 + h + 12, 230, vl, dir=-1, mood='fake', arms=(0, 0), nod=math.sin(u * 3 + i) * .3)
        o = 0.12 * (1 - cl) + 0.0
        # draw door with a person visible through the gap
        door(c, x, GY + 40, 150, 330, o * 6 if cl < 0.99 else 0, inside=inside if cl < 0.97 else None)
    person(c, 90, GY + 150, 340, WREN, dir=1, mood='flat', arms=(0, 0), t=u)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s5(c, u, k):
    sn = sentences(k)
    cam = 360 + u * 38
    street(c, u, cam=cam)
    c.veil(0, 0, W, H, (8, 8, 30), 0.2)
    # neighbours peeking
    base = int(cam // SW) - 1
    if u < sn[4][0] + 0.3:
        for i in range(base, base + 6):
            x = i * SW - cam + 100
            if 150 < x < 1130 and (i % 2 == 0):
                door(c, x, GY, DW, DH, 0.12, inside=lambda cc, x0, y0, w, h: cc.rect(x0, y0, x0 + w, y0 + h, fill=(70, 50, 56)))
    # speech: good luck / can't help
    for (si, txt, px) in ((1, 'Good luck!', 760), (2, "I can't help with that.", 1010)):
        s_, e_ = sn[si][0], sn[si][1]
        if s_ - 0.05 <= u <= e_ + 0.4:
            bubble(c, px, 250, txt, ramp(u, s_, s_ + 0.25) * (1 - ramp(u, e_ + 0.1, e_ + 0.4)), px - 40, 26)
            person(c, px - 20, GY + 6, 170, villager(60 + si), dir=-1, mood='fake', arms=(0, 70), t=u)
    wk = u < sn[4][0] + 1
    person(c, 380, GY + 130, 300, WREN, dir=1, walk=u * 6 if wk else 0, mood='sad' if u > sn[3][0] else 'flat', arms=(0, 0), t=u)
    if u > sn[4][0] + 1.0:
        c.veil(0, 0, W, H, (8, 8, 30), 0.25 * ramp(u, sn[4][0] + 1, sn[4][0] + 2))
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def clapper(c, x, y, a, t, clap):
    c.rect(x - 90, y, x + 90, y + 110, fill=(30, 30, 36), r=4)
    ang = (1 - clap) * 0.5
    c.poly([(x - 90, y - 4), (x + 90, y - 4 - 70 * math.sin(ang)), (x + 90, y - 28 - 70 * math.sin(ang)), (x - 90, y - 28)], (240, 240, 240))
    for i in range(6):
        px = x - 90 + i * 30
        c.poly([(px, y - 4), (px + 15, y - 4 - 70 * math.sin(ang) * (px + 15 - (x - 90)) / 180), (px + 30, y - 4 - 70 * math.sin(ang) * (px + 30 - (x - 90)) / 180), (px + 15, y - 4)], (30, 30, 36)) if False else None
    c.text(x, y + 30, 'THE VILLAGE', 22, (240, 240, 240), 'mm', bold=True)
    c.text(x, y + 62, 'scene 1 · take 1', 18, (200, 200, 210), 'mm')
    c.text(x, y + 88, 'painted', 16, (200, 160, 100), 'mm')

def s6(c, u, k):
    sn = sentences(k)
    f = ramp(u, sn[0][0] + 1.0, sn[0][1] + 0.4)
    if f < 1:
        street(c, u, cam=900 + u * 20, dark=False)
        c.veil(0, 0, W, H, (8, 8, 30), 0.3)
    if f > 0:
        c2 = C(); backlot(c2, u, cam=900 + u * 26)
        c2.veil(0, 0, W, H, (4, 4, 20), 0.15)
        person(c2, 300, GY + 150, 300, WREN, dir=1, walk=u * 6, mood='o', arms=(0, 0), lantern_t=u, t=u)
        if f < 1: c.mix(c2, f)
        else: c.reset(c2.im)
    else:
        person(c, 300, GY + 130, 300, WREN, dir=1, walk=u * 6, mood='flat', arms=(0, 0), t=u)
    a = ramp(u, sn[1][0] + 0.2, sn[1][0] + 0.8)
    if a > 0:
        cl = ramp(u, sn[1][0] + 0.8, sn[1][0] + 1.0)
        clapper(c, 900, 120 + (1 - ease(a)) * -200, a, u, 1 - cl if cl < 1 else 1)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s7(c, u, k):
    sn = sentences(k)
    cam = 760 + u * 26
    backlot(c, u, cam=cam)
    c.veil(0, 0, W, H, (4, 4, 20), 0.15)
    base = int(cam // SW) - 1
    for i in range(base, base + 6):
        x = i * SW - cam + 100
        vl = villager(70 + (i % 8))
        yb = GY + 120
        # brace the person holds: on the right brace
        person(c, x + 40, yb, 250, vl, dir=-1, mood='sad', arms=(0, 150), nod=math.sin(u * 1.1 + i) * .3, t=u)
        table(c, x + 40, yb + 6, 130, 80)
        lamp(c, x + 10, yb - 74, u)
        c.ell(x + 70, yb - 80, 8, 4, fill=(230, 226, 220))   # cold cup
    # front lamp for Wren
    person(c, 330, H - 8, 330, WREN, dir=1, walk=u * 6, mood='o' if u < sn[1][1] else 'sad', arms=(0, 0), lantern_t=u, t=u)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def feather(c, x, y, s, t):
    c.line([(x - s, y + s * .3), (x + s, y - s * .3)], 3, (230, 230, 240))
    for i in range(9):
        f = i / 8
        px = lerp(x - s * .9, x + s * .7, f); py = lerp(y + s * .26, y - s * .22, f)
        c.line([(px, py), (px + 6, py - 28 * math.sin(math.pi * (0.2 + 0.6 * f)))], 2, (235, 238, 250))
        c.line([(px, py), (px - 4, py + 22 * math.sin(math.pi * (0.2 + 0.6 * f)))], 2, (225, 228, 244))

def s8(c, u, k):
    sn = sentences(k)
    c.im.paste(sky('warm'), (0, 0))
    c.rect(0, 560, W, H, fill=(60, 44, 56))
    # shock villager
    sh = 0.5 + 0.5 * math.sin(u * 7)
    person(c, 260, 650, 460, villager(81), dir=1, mood='o', arms=(10, 70), nod=sh, t=u)
    if int(u * 4) % 2 == 0:
        c.text(400, 160, '!', 90, (255, 230, 120), 'mm', bold=True); c.text(150, 190, '!', 60, (255, 230, 120), 'mm', bold=True)
    # pedestals
    a1 = ramp(u, sn[1][0], sn[1][0] + 0.6)
    for (px, name) in ((640, 'Shock'), (960, 'Responsibility')):
        c.rect(px - 80, 500, px + 80, 560, fill=(110, 84, 76)); c.rect(px - 90, 490, px + 90, 504, fill=(150, 120, 104))
    feather(c, 640, 460 - 8 * math.sin(u * 2), 60, u)
    beam(c, 880, 462, 1040, 462, 34)
    c.rect(880, 444, 1040, 480, outline=(100, 70, 40), w=2) if False else None
    for (px, name, col) in ((640, 'Shock', (255, 226, 160)), (960, 'Responsibility', (255, 170, 120))):
        v = a1
        c.text(px, 398, name, 30, (int(col[0] * v), int(col[1] * v), int(col[2] * v)), 'mm', bold=True, serif=True)
    # empty rooms
    a2 = ramp(u, sn[2][0] + 0.8, sn[2][0] + 2.2)
    if a2 > 0:
        c.veil(0, 0, W, 330, (6, 6, 20), 0.55 * a2)
        c.rect(520, 60, 1180, 300, fill=lerpc((40, 30, 50), (20, 16, 34), 1), outline=(120, 100, 140), w=3)
        c.rect(540, 80, 1160, 280, fill=(44, 34, 56))
        for rx in (610, 850, 1090):
            c.rect(rx - 36, 190, rx + 36, 260, fill=(90, 66, 60)); c.rect(rx - 40, 150, rx - 30, 260, fill=(90, 66, 60))
        c.glow(850, 160, 120, (255, 190, 120), 0.12 + 0.05 * math.sin(u * 3))
        c.text(850, 112, 'empty rooms', 30, (int(220 * a2), int(206 * a2), int(240 * a2)), 'mm', serif=True)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s9(c, u, k):
    sn = sentences(k)
    c.im.paste(sky('dusk'), (0, 0))
    hills(c, u, 'dusk', u * 3)
    c.rect(0, 560, W, H, fill=(86, 70, 84))
    # billboard painter
    c.rect(150, 190, 640, 420, fill=(236, 226, 200), outline=(90, 66, 50), w=6)
    c.rect(220, 420, 240, 560, fill=(90, 66, 50)); c.rect(550, 420, 570, 560, fill=(90, 66, 50))
    p = ramp(u, sn[0][0] + 0.3, sn[0][1] + 0.5)
    word = 'THE VILLAGE'
    n = int(len(word) * p)
    c.text(395, 305, word[:n], 66, (200, 70, 80), 'mm', bold=True, serif=True) if n else None
    wd = F(66, True, True).getlength(word[:n]) / K if n else 0
    bx = 395 - F(66, True, True).getlength(word) / K / 2 + wd
    person(c, 720, 600, 300, villager(90), dir=-1, mood='smile', arms=(0, 100 + 15 * math.sin(u * 5)), t=u)
    c.line([(bx, 300 + 20 * math.sin(u * 5)), (bx + 40, 290)], 4, (150, 100, 60)) if False else None
    # drifting words
    for i, wd_ in enumerate(('connection', 'belonging', 'community', 'support')):
        s_ = sn[1][0] + i * 0.7
        f = clamp((u - s_) / 3.0)
        if f > 0:
            x = 360 + i * 120 + 20 * math.sin(u + i); y = 190 - f * 150
            a = 1 - ramp(f, 0.7, 1.0)
            v = int(255 * a)
            c.text(x, y, wd_, 26, (v, int(v * .86), int(v * .6)), 'mm', serif=True)
    # neglected lumber
    c.rect(850, 520, 1210, 560, fill=(150, 104, 70)); c.rect(870, 480, 1190, 520, fill=(130, 90, 60)); c.rect(900, 440, 1170, 480, fill=(150, 104, 70))
    for yy in (462, 500, 540): c.line([(860, yy), (1200, yy)], 2, (110, 76, 52))
    c.line([(1000, 440), (1020, 380)], 6, (120, 120, 130)); c.rect(1008, 360, 1052, 384, fill=(90, 90, 100))   # hammer
    c.line([(1100, 440), (1160, 360)], 5, (170, 170, 180))
    # cobwebs & dust fade in during the practice sentence
    a = ramp(u, sn[1][0] + 1.4, sn[1][0] + 3.0)
    if a > 0:
        for (cx, cy, s_) in ((850, 440, 90), (1210, 440, 90)):
            for j in range(5):
                ang = math.pi * (0.5 + 0.5 * j / 4) if cx > 1000 else math.pi * 0.5 * j / 4
                c.line([(cx, cy), (cx + (-1 if cx > 1000 else 1) * s_ * math.cos(ang) * 0.0 + (s_ if cx < 1000 else -s_) * math.sin(ang), cy - s_ * math.cos(ang))], 1.2, (int(200 * a), int(200 * a), int(210 * a)))
        c.text(1030, 600, 'practice', 30, (int(220 * a), int(200 * a), int(170 * a)), 'mm', serif=True)
    c.text(395, 460, 'language', 30, (int(236 * ramp(u, sn[1][0] + 0.2, sn[1][0] + 1.0)), int(214 * ramp(u, sn[1][0] + 0.2, sn[1][0] + 1.0)), int(180 * ramp(u, sn[1][0] + 0.2, sn[1][0] + 1.0))), 'mm', serif=True)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s10(c, u, k):
    sn = sentences(k)
    backlot(c, u, cam=1100)
    c.veil(0, 0, W, H, (4, 4, 20), 0.15)
    lift = ramp(u, sn[1][0] + 0.2, sn[1][0] + 1.2)
    yb = GY + 130
    # neighbour behind a front, holding brace
    person(c, 900, yb, 300, villager(71), dir=-1, mood='sad' if lift < 0.99 else 'o', arms=(0, 150 if u < sn[1][0] + 2.8 else 100), nod=math.sin(u) * .2, t=u)
    table(c, 900, yb + 6, 150, 90); lamp(c, 860, yb - 84, u)
    wy = lerp(yb - 6, yb - 120, lift)
    person(c, 380, yb, 340, WREN, dir=1, mood='smile' if u > sn[1][0] + 2 else 'flat', arms=(0, 60 + 80 * lift), lantern_t=None, t=u)
    beam(c, 380 + 70 * (1 - lift) + 20, wy + 10, lerp(620, 720, lift), wy + 10, 22)
    a = ramp(u, sn[1][0] + 2.2, sn[1][0] + 2.6)
    bubble(c, 540, 220, 'Can you hold the other end?', a, 450, 26)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s11(c, u, k):
    sn = sentences(k)
    cam = 1100
    backlot(c, u, cam=cam)
    c.veil(0, 0, W, H, (4, 4, 20), 0.12)
    yb = GY + 130
    # people join: (start sentence, start x, villager)
    j2 = ramp(u, sn[2][0], sn[2][0] + 3.0); j3 = ramp(u, sn[3][0], sn[3][0] + 2.0)
    # stations (sitting) for neighbours not yet joined
    for (x, vi, j) in ((1080, 73, j2), (1190, 74, j3)):
        if j < 0.02:
            person(c, x, yb, 270, villager(vi), dir=-1, mood='sad', arms=(0, 150), t=u)
            table(c, x, yb + 6, 130, 80)
    wlk = 0.0
    xw = 300 + 90 * ramp(u, 0, D[k] - 3)
    walkp = u * 6
    # carriers along the beam
    pos = [xw, xw + 130]
    people = [(WREN, pos[0]), (villager(71), pos[1])]
    if j2 > 0.02: people.append((villager(73), lerp(1080, xw + 260, ease(j2))))
    if j3 > 0.02: people.append((villager(74), lerp(1190, xw + 390, ease(j3))))
    xs = [p[1] for p in people]
    beam(c, xs[0] + 20, yb - 128, xs[-1] + 40, yb - 128, 24)
    for i, (p, x) in enumerate(people):
        moving = (i >= 2 and (j2 < 0.99 if i == 2 else j3 < 0.99)) or True
        person(c, x, yb, 300 if i != 0 else 330, p, dir=1 if i < 2 else (-1 if (j2 if i == 2 else j3) < 0.98 else 1), walk=walkp + i, mood='o' if i == 1 and u < sn[1][1] else ('smile' if u > sn[2][0] else 'flat'), arms=(100, 100), t=u)
    # dropped braces
    for (x, j) in ((1080, j2), (1190, j3)):
        if j > 0.02:
            c.line([(x - 40, GY + 20), (x + 80, GY + 30)], 10, (120, 82, 50))
    a = ramp(u, sn[0][0], sn[0][0] + 0.4)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def timber_house(c, cx, base, w, h, p, t, lit):
    x0, x1 = cx - w / 2, cx + w / 2
    n = 6
    for i in range(n + 1):
        if p > i / (n + 1):
            xx = lerp(x0, x1, i / n)
            beam(c, xx, base, xx, base - h, 12)
    if p > 0.45:
        beam(c, x0 - 6, base - h, x1 + 6, base - h, 14)
        beam(c, x0 - 6, base - h * .5, x1 + 6, base - h * .5, 10)
    if p > 0.7:
        wall = (200, 160, 110)
        c.rect(x0 + 6, base - h * .5, x1 - 6, base, fill=wall)
        c.rect(x0 + 6, base - h + 8, x1 - 6, base - h * .5, fill=(210, 172, 120))
    if p > 0.85:
        c.poly([(x0 - 24, base - h), (x1 + 24, base - h), (cx, base - h - w * .38)], (130, 74, 60))
        c.line([(x0 - 24, base - h), (cx, base - h - w * .38), (x1 + 24, base - h)], 8, (170, 108, 80))
    if p > 0.9:
        for wx in (cx - w * .28, cx + w * .28):
            c.glow(wx, base - h * .75, 70, (255, 200, 120), 0.5 * lit)
            c.rect(wx - 24, base - h * .9, wx + 24, base - h * .58, fill=lerpc((120, 130, 150), (255, 220, 150), lit), outline=(110, 74, 54), w=4)
        c.rect(cx - 22, base - h * .45, cx + 22, base, fill=(120, 76, 54), r=3)

def s12(c, u, k):
    sn = sentences(k)
    f = ramp(u, 0, 2.0)
    c.im.paste(sky('dawn'), (0, 0))
    c.glow(900, 450, 400, (255, 220, 150), 0.5 * f)
    hills(c, u, 'dusk', u * 3)
    c.veil(0, 0, W, 560, (255, 200, 150), 0.2)
    c.rect(0, GY, W, H, fill=(112, 98, 90))
    c.rect(0, GY - 3, W, GY + 6, fill=(150, 130, 110))
    # old dim facades in the back
    for i in range(0, 5):
        x = i * 330 + 60 - 20
        col, sign = SHOPS[i % 8]
        c.veil(0, 0, 0, 0, (0, 0, 0), 0)
    for i in range(4):
        x = 90 + i * 360
        facade(c, x, SHOPS[(i + 2) % 8][0], SHOPS[(i + 2) % 8][1], u, 1 - ramp(u, sn[0][0], sn[0][0] + 1.5), dark=False)
    c.veil(0, GY - 360, W, GY + 8, (255, 214, 170), 0.35)
    p = ramp(u, 0.0, 3.0)
    timber_house(c, 460, GY + 30, 320, 250, 1.0, u, f)
    # people with the table
    c.rect(700, 600, 1230, 626, fill=(170, 120, 80))
    for i, x in enumerate((760, 860, 960, 1060, 1160)):
        person(c, x, 626, 320, villager(30 + i) if i else WREN, dir=-1 if i % 2 else 1, mood='talk' if int(u / 1.4 + i) % 2 else 'smile', talk=u * 8 + i * 2, arms=(0, 30 + 25 * math.sin(u * 2 + i)), t=u, tint=((255, 200, 140), 0.1))
    c.rect(690, 560, 1240, 590, fill=(190, 140, 94))
    for i, x in enumerate(range(730, 1230, 70)):
        c.ell(x, 556, 22, 8, fill=(240, 232, 214)); c.ell(x, 548, 16, 10, fill=[(230, 140, 70), (150, 190, 90), (210, 90, 90), (240, 200, 100)][i % 4])
    lantern(c, 700, 520, u, 1.2); lantern(c, 1230, 520, u, 1.2)
    # final card
    a = ramp(u, DURS[k] + LEAD[k] + 0.4, DURS[k] + LEAD[k] + 1.6)
    if a > 0:
        c.veil(0, 70, W, 250, (10, 8, 30), 0.5 * a)
        v = int(255 * a)
        c.text(640, 128, 'Do not paint the village.', 56, (v, int(v * .92), int(v * .8)), 'mm', bold=True, serif=True)
        c.text(640, 196, 'Raise it.', 70, (v, int(v * .72), int(v * .35)), 'mm', bold=True, serif=True)
    fcol(c, ramp(u, 0, 1.2))
    c.fade((0, 0, 0), ramp(u, D[k] - 1.8, D[k] - 0.2))
    sub(c, k, u)

SCENES = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12]

def frame(n):
    t = n / FPS
    k = max(i for i in range(13) if T0[i] <= t + 1e-9)
    c = C()
    SCENES[k](c, t - T0[k], k)
    return c.out(), k
