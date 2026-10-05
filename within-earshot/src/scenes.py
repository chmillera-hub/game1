from lib import *
from base import ICON, bubble, sub, st, en, fcol, cloud, sun, snow, sandwich, tvicon, vsicon

ELLIS = dict(skin=(230, 192, 162), hair=(48, 36, 32), shirt=(70, 122, 128), pants=(60, 62, 84), glasses=True, long=False)
GARRICK = dict(skin=(224, 182, 148), hair=(176, 176, 182), shirt=(176, 98, 72), pants=(80, 76, 70), glasses=False, long=False)
ODILE = dict(skin=(214, 164, 128), hair=(112, 62, 44), shirt=(142, 104, 176), pants=(70, 62, 90), glasses=False, long=True)

SEAT = 478
HIP = 0.35
def feet_for(h): return SEAT + HIP * h - 4

# ---------- park ----------
def tree(c, x, base, s, col=(44, 92, 78), t=0):
    c.rect(x - 12 * s, base - 150 * s, x + 12 * s, base, fill=(74, 52, 48))
    for (dx, dy, r) in ((0, -190, 78), (-60, -150, 58), (60, -150, 58), (-20, -240, 56), (34, -225, 52)):
        c.ell(x + dx * s + math.sin(t * .7 + dx) * 2, base + dy * s, r * s, fill=col)

def lamp_post(c, x, base, t, a=1.0):
    c.rect(x - 4, base - 230, x + 4, base, fill=(40, 36, 46))
    c.glow(x, base - 236, 150, (255, 206, 120), 0.6 * a * (0.93 + 0.07 * math.sin(t * 5 + x)))
    c.rect(x - 14, base - 258, x + 14, base - 232, fill=(250, 226, 160), r=6)
    c.poly([(x - 20, base - 258), (x + 20, base - 258), (x, base - 276)], (40, 36, 46))

def pigeon(c, x, y, s, fly=0, t=0):
    c.ell(x, y, 14 * s, 9 * s, fill=(130, 136, 154)); c.ell(x + 13 * s, y - 5 * s, 6 * s, fill=(110, 116, 136))
    c.poly([(x + 18 * s, y - 5 * s), (x + 24 * s, y - 4 * s), (x + 18 * s, y - 2 * s)], (240, 190, 90))
    c.ell(x + 15 * s, y - 6 * s, 1.3 * s, fill=(20, 20, 20))
    wy = -10 * s * math.sin(t * 20) if fly else 0
    c.poly([(x - 4 * s, y - 2 * s), (x + 6 * s, y - 2 * s), (x - 6 * s, y - 16 * s + wy)], (100, 106, 128))
    c.poly([(x - 14 * s, y), (x - 24 * s, y + 4 * s), (x - 14 * s, y + 6 * s)], (100, 106, 128))
    if not fly:
        c.line([(x, y + 8 * s), (x, y + 14 * s)], 1.6 * s, (220, 150, 140))

def park(c, t, mode='dusk', cam=0, lamps=True):
    c.im.paste(sky(mode), (0, 0))
    if mode in ('night', 'dusk'):
        for (x, y, r, ph) in STARS[:70]:
            b = (0.5 + 0.5 * math.sin(t * 1.6 + ph)) * (0.9 if mode == 'night' else 0.3); v = int(255 * b)
            c.ell(x, y * 0.75, r, fill=(v, v, min(255, v + 20)))
    hills(c, t, 'dusk' if mode == 'dusk' else 'night', cam * 0.2)
    for i, x in enumerate((90, 330, 1010, 1210)):
        tree(c, x - cam * 0.5 % 1, GY + 10, 1.0 + 0.1 * (i % 2), (44, 92, 78) if mode == 'dusk' else (22, 52, 52), t)
    c.rect(0, GY, W, H, fill=(76, 108, 84) if mode == 'dusk' else (30, 52, 52))
    c.rect(0, GY + 36, W, H, fill=(168, 150, 132) if mode == 'dusk' else (70, 66, 80))
    for i in range(0, 14):
        c.line([(i * 100 - (cam % 100) + 40, GY + 36), (i * 100 - (cam % 100) - 30, H)], 1.5, (140, 124, 110) if mode == 'dusk' else (50, 48, 62))
    if lamps:
        for x in (160, 1120): lamp_post(c, x, GY + 36, t)

def bench(c, x, w=420, back=True):
    # drawn BEFORE people (backrest)
    if back: c.rect(x - w / 2, SEAT - 120, x + w / 2, SEAT - 2, fill=(122, 112, 118), r=8)

def bench_front(c, x, w=420):
    c.rect(x - w / 2 - 8, SEAT - 4, x + w / 2 + 8, SEAT + 20, fill=(166, 156, 160), r=6)
    c.rect(x - w / 2, SEAT + 20, x + w / 2, SEAT + 120, fill=(136, 126, 132))
    c.rect(x - w / 2 + 10, SEAT + 120, x + w / 2 - 10, SEAT + 128, fill=(86, 78, 84))

def seated(c, x, h, p, **kw):
    return person(c, x, feet_for(h), h, p, **kw)

def waves(c, x, y, t, n=5, r0=60, col=(255, 236, 190), spd=60, span=260, arc=None):
    for i in range(n):
        r = ((t * spd + i * span / n) % span) + r0
        f = 1 - (r - r0) / span
        v = lerpc((60, 50, 70), col, f * .9)
        a0, a1 = arc if arc else (0, 360)
        c.arc(x, y, r, r, a0, a1, 3, v)

def squawk_text(c, x, y, txt, s, t, col=(255, 90, 90)):
    for i, ch in enumerate(txt):
        c.text(x + (i - len(txt) / 2) * s * 0.62 + math.sin(t * 30 + i) * 2, y + math.sin(t * 25 + i * 2) * 3, ch, s, col, 'mm', bold=True)

def parrot(c, x, y, s, t, beak=0.0, shake=0.0):
    c.line([(x - 140 * s, y + 130 * s), (x + 150 * s, y + 130 * s)], 12 * s, (110, 80, 56))     # perch
    c.poly([(x - 20 * s, y + 20 * s), (x - 70 * s, y + 120 * s), (x - 30 * s, y + 160 * s), (x + 10 * s, y + 70 * s)], (230, 90, 70))    # tail
    c.poly([(x - 10 * s, y + 40 * s), (x - 40 * s, y + 140 * s), (x, y + 172 * s), (x + 22 * s, y + 80 * s)], (80, 150, 230))
    c.ell(x, y, 60 * s, 82 * s, fill=(60, 180, 130))
    c.ell(x - 12 * s, y + 16 * s, 34 * s, 54 * s, fill=(40, 140, 100))
    c.ell(x + 14 * s, y + 24 * s, 34 * s, 46 * s, fill=(246, 214, 110))
    hx = x + 8 * s + shake * 14 * s; hy = y - 84 * s
    c.ell(hx, hy, 44 * s, fill=(230, 80, 70))
    c.ell(hx + 14 * s, hy - 6 * s, 11 * s, fill=(255, 255, 255)); c.ell(hx + 16 * s, hy - 6 * s, 5 * s, fill=(20, 20, 20))
    bo = beak * 22 * s
    c.poly([(hx + 28 * s, hy - 8 * s), (hx + 82 * s, hy + 4 * s - bo * .2), (hx + 56 * s, hy + 26 * s - bo * .5), (hx + 30 * s, hy + 8 * s)], (255, 190, 70))
    c.poly([(hx + 30 * s, hy + 12 * s + bo * .4), (hx + 62 * s, hy + 22 * s + bo), (hx + 36 * s, hy + 36 * s + bo * .8)], (240, 160, 50))
    c.line([(x - 8 * s, y + 80 * s), (x - 8 * s, y + 124 * s)], 5 * s, (240, 180, 110)); c.line([(x + 16 * s, y + 80 * s), (x + 16 * s, y + 124 * s)], 5 * s, (240, 180, 110))

# ---------- scenes ----------
def s0(c, u, k):
    park(c, u, 'dusk', cam=u * 3)
    bench(c, 640)
    seated(c, 560, 330, ELLIS, dir=1, mood='flat', arms=(0, 10))
    seated(c, 730, 330, GARRICK, dir=-1, mood='talk', talk=u * 9, arms=(0, 20 + 15 * math.sin(u * 2)))
    bench_front(c, 640)
    pigeon(c, 280 + 6 * math.sin(u), GY + 78, 1.2, t=u); pigeon(c, 1000, GY + 90, 1.0, t=u)
    a = ramp(u, 0.3, 1.5) * (1 - ramp(u, 3.4, 4.0))
    if a > 0:
        c.veil(0, 40, W, 190, (10, 14, 30), 0.5 * a)
        c.text(640, 96, 'WITHIN EARSHOT', 72, tuple(int(255 * a) for _ in range(3)), 'mm', bold=True, serif=True)
        c.text(640, 150, 'a short film', 24, (int(255 * a), int(220 * a), int(180 * a)), 'mm', serif=True)
    fcol(c, ramp(u, 0, 1.2))
    sub(c, k, u)

def s1(c, u, k):
    park(c, u, 'dusk', cam=u * 3)
    bench(c, 640)
    seated(c, 560, 330, ELLIS, dir=1, mood='flat', arms=(0, 10), nod=0)
    seated(c, 730, 330, GARRICK, dir=-1, mood='talk', talk=u * 9, arms=(0, 20 + 20 * math.sin(u * 2)))
    bench_front(c, 640)
    a4 = ramp(u, st(k, 4), st(k, 4) + 0.8)
    waves(c, 740, 280, u, 6, 60, spd=70, span=420, arc=None) if a4 > 0.01 else None
    for (i, txt, x, y) in ((1, "It's going to rain.", 900, 150), (2, "Then it'll clear.", 1000, 90), (3, "Then it'll rain again.", 930, 220)):
        if u >= st(k, i):
            f = clamp((u - st(k, i)) / 3.0)
            bubble(c, x, y - 40 * f, txt, ramp(u, st(k, i), st(k, i) + 0.3) * (1 - ramp(f, 0.7, 1.0)), (x - 90, y + 80), 'rain' if i != 2 else 'hot', t=u)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s2(c, u, k):
    park(c, u, 'dusk', cam=u * 3)
    bench(c, 640)
    spk = st(k, 1) <= u < en(k, 2)
    seated(c, 560, 330, ELLIS, dir=1, mood='talk' if spk else 'sad', talk=u * 8, arms=(0, 30 if spk else 10))
    nod = math.sin(u * 5) if st(k, 3) <= u < st(k, 3) + 1.6 else 0
    seated(c, 730, 330, GARRICK, dir=-1 if u > st(k, 3) + 1.4 else 1, mood='smile' if u < st(k, 3) + 1.4 else 'talk', talk=u * 9, nod=nod, arms=(0, 20))
    bench_front(c, 640)
    # calendar tag: weeks ago
    a = ramp(u, st(k, 0), st(k, 0) + 0.4) * (1 - ramp(u, en(k, 0) + 0.4, en(k, 0) + 1.0))
    if a > 0:
        c.veil(430, 60, 850, 130, (10, 12, 30), 0.55 * a)
        c.text(640, 95, 'weeks ago', 34, (int(255 * a), int(226 * a), int(160 * a)), 'mm', serif=True)
    for (i, txt) in ((1, "I'm lonely."), (2, "I'd like help meeting someone.")):
        if st(k, i) - 0.05 <= u <= en(k, i) + 0.6:
            bubble(c, 400 if i == 1 else 360, 190, txt, ramp(u, st(k, i), st(k, i) + 0.3) * (1 - ramp(u, en(k, i) + 0.3, en(k, i) + 0.6)), (520, 260), None, 28)
    if u > st(k, 3) + 1.4:
        bubble(c, 900, 190, 'Anyway, it might rain.', ramp(u, st(k, 3) + 1.4, st(k, 3) + 1.8), (790, 260), 'rain', t=u)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s3(c, u, k):
    park(c, u, 'dusk', cam=u * 3)
    bench(c, 640)
    seated(c, 560, 330, ELLIS, dir=1, mood='flat', arms=(0, 10))
    ang = ramp(u, st(k, 1), st(k, 1) + 1.0)
    seated(c, 730, 330, GARRICK, dir=-1, mood='talk' if u > st(k, 0) else 'flat', talk=u * 12, arms=(0, 60 + 40 * math.sin(u * 6) * ang), nod=math.sin(u * 7) * ang)
    bench_front(c, 640)
    if ang > 0.2:
        for i in range(3):
            xx = 700 + i * 28 + math.sin(u * 8 + i) * 3
            c.line([(xx, 258), (xx - 6, 238 - 10 * ang)], 3, (255, 100, 90))
    if st(k, 0) <= u < st(k, 2) + 4:
        bubble(c, 930, 160, 'Can you believe what they said?!', ramp(u, st(k, 0) + 0.4, st(k, 0) + 0.8), (800, 250), 'tv', t=u)
    pf = ramp(u, st(k, 2), st(k, 2) + 2.2)
    for i in range(5):
        x0 = 220 + i * 160; y0 = GY + 84
        if pf <= 0.01:
            pigeon(c, x0, y0, 1.1, t=u)
        elif pf < 1:
            pigeon(c, x0 + pf * (i * 40 - 60), y0 - pf * 380 + pf * pf * 60, 1.1, fly=1, t=u + i)
    if u > st(k, 3):
        a = ramp(u, st(k, 3), st(k, 3) + 0.5)
        c.line([(716, 316), (594, 322)], 2.5, (int(255 * a), int(236 * a), int(150 * a)))
        c.text(655, 296, 'he knows', 22, (int(255 * a), int(236 * a), int(150 * a)), 'mm', bold=True)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s4(c, u, k):
    park(c, u, 'dusk', cam=u * 3)
    bench(c, 640)
    closed = u > st(k, 2)
    away = u > st(k, 2) + 0.8
    seated(c, 560, 330, ELLIS, dir=1, mood='talk' if st(k, 1) < u < en(k, 1) else ('sad' if closed else 'flat'), talk=u * 8, arms=(0, 40 if st(k, 1) < u < en(k, 1) else 10))
    seated(c, 730, 330, GARRICK, dir=-1 if away or u < st(k, 1) else 1, mood='flat' if (closed and not away) else ('talk' if away or u < st(k, 1) else 'flat'), talk=u * 9, arms=(0, 60 if closed else 20))
    bench_front(c, 640)
    if st(k, 1) - 0.1 <= u <= en(k, 1) + 0.6:
        bubble(c, 400, 170, 'Could we talk about something that matters to me?', ramp(u, st(k, 1), st(k, 1) + 0.3) * (1 - ramp(u, en(k, 1) + 0.3, en(k, 1) + 0.6)), (540, 250), None, 26)
    if st(k, 3) - 0.1 <= u <= en(k, 3) + 0.8:
        bubble(c, 930, 170, 'Leave me alone.', ramp(u, st(k, 3), st(k, 3) + 0.3), (800, 250), None, 30)
    if u > st(k, 4): waves(c, 740, 280, u, 6, 60, spd=90, span=420)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def brick_wall(c, t):
    c.rect(0, 0, W, 600, fill=(158, 86, 70))
    for r in range(0, 600, 36):
        c.line([(0, r), (W, r)], 3, (112, 60, 52))
        off = 0 if (r // 36) % 2 == 0 else 50
        for x in range(-100 + off, W, 100): c.line([(x, r), (x, r + 36)], 3, (112, 60, 52))
    c.rect(0, 600, W, H, fill=(76, 70, 82)); c.rect(0, 596, W, 608, fill=(56, 50, 62))

def speaker(c, x, y, t, p=1.0):
    c.rect(x - 150, y - 190, x + 150, y + 190, fill=(30, 30, 40), r=14, outline=(70, 70, 84), w=4)
    for (cy_, r_) in ((y - 80, 76), (y + 90, 52)):
        c.ell(x, cy_, r_ * (1 + 0.05 * math.sin(t * 20) * p), fill=(18, 18, 24), outline=(90, 90, 104), w=4)
        c.ell(x, cy_, r_ * 0.45 * (1 + 0.1 * math.sin(t * 20) * p), fill=(48, 48, 60))
    c.rect(x - 28, y + 156, x + 28, y + 178, fill=(40, 40, 50), r=4)
    c.rect(x - 160, y - 200, x - 150, y + 200, fill=(120, 120, 130)); c.rect(x + 150, y - 200, x + 160, y + 200, fill=(120, 120, 130))

def s5(c, u, k):
    brick_wall(c, u)
    sx, sy = 780, 270
    s2_ = u >= st(k, 2)
    amp = 1.0 + (ramp(u, st(k, 2), st(k, 2) + 3) * 1.5)
    waves(c, sx, sy, u, 6, 120, col=(255, 236, 190), spd=100 * amp, span=520, arc=(90, 270))
    speaker(c, sx, sy, u, amp)
    # play panel
    c.rect(sx - 70, 484, sx + 70, 548, fill=(24, 24, 32), r=8)
    pl = ramp(u, st(k, 1), st(k, 1) + 0.4)
    c.poly([(sx - 14, 498), (sx - 14, 534), (sx + 18, 516)], lerpc((80, 90, 80), (110, 255, 140), pl))
    # no ears
    if pl > 0.2:
        a = pl
        ex, ey = 1100, 270
        c.glow(ex, ey, 100, (255, 230, 180), 0.2 * a)
        c.ell(ex, ey, 44, 60, outline=(int(240 * a), int(210 * a), int(190 * a)), w=8)
        c.arc(ex, ey, 22, 30, 200, 400, 6, (int(240 * a), int(210 * a), int(190 * a)))
        c.line([(ex - 70, ey + 70), (ex + 70, ey - 70)], 10, (int(240 * a), int(70 * a), int(70 * a)))
    esz = 330 + 20 * (1 + math.sin(u * 3)) * (1 if s2_ else 0)
    person(c, 330, 640, esz, ELLIS, dir=1, mood='talk', talk=u * 8, arms=(0, 70))
    if st(k, 2) <= u:
        bubble(c, 330, 200 - 20 * ramp(u, st(k, 2), st(k, 2) + 3), 'COULD WE TALK?' if u > st(k, 2) + 1.5 else 'Could we talk?', ramp(u, st(k, 2), st(k, 2) + 0.3), (330, 290), None, 30 + int(8 * ramp(u, st(k, 2), st(k, 2) + 3)))
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s6(c, u, k):
    park(c, u, 'dusk', cam=u * 3)
    c.rect(700, GY + 40, 1180, GY + 50, fill=(110, 80, 56)) if False else None
    sh = ramp(u, st(k, 2), st(k, 2) + 0.4) * math.sin(u * 14) * (1 - ramp(u, st(k, 2) + 1.0, st(k, 2) + 1.2))
    big = ramp(u, st(k, 2) + 1.0, st(k, 2) + 1.4)
    beak = (0.5 + 0.5 * math.sin(u * 14)) * (1 if u > st(k, 0) else 0.2)
    parrot(c, 860, 340, 1.5, u, beak * (1 + 0.8 * big), sh)
    person(c, 380, 640, 340, ELLIS, dir=1, mood='talk' if st(k, 1) < u < en(k, 1) else 'sad', talk=u * 8, arms=(0, 30))
    if st(k, 0) <= u:
        squawk_text(c, 1060 + 10 * big, 190 - 20 * big, 'SQUAWK!', 36 + int(34 * big), u) if u > st(k, 0) + 0.6 else None
    if st(k, 1) - 0.1 <= u <= en(k, 1) + 1.2:
        bubble(c, 400, 190, 'Bird, could we talk about something else?', ramp(u, st(k, 1), st(k, 1) + 0.3) * (1 - ramp(u, en(k, 1) + 0.5, en(k, 1) + 1.2)), (380, 290), None, 24)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s7(c, u, k):
    park(c, u, 'night', cam=u * 2)
    bench(c, 640)
    seated(c, 560, 360, ELLIS, dir=1, mood='sad', arms=(0, 10))
    seated(c, 740, 360, GARRICK, dir=-1, mood='talk', talk=u * 9, arms=(0, 20))
    bench_front(c, 640)
    a = ramp(u, st(k, 2) + 0.3, st(k, 2) + 1.6)
    if a > 0:
        cx, cy = 480, 150
        c.ell(540, 262, 7 * a, fill=(250, 244, 230)); c.ell(520, 232, 11 * a, fill=(250, 244, 230))
        for (dx, dy, r_) in ((-70, 0, 60), (0, -18, 74), (70, 0, 60), (-30, 30, 56), (40, 34, 56)):
            c.ell(cx + dx, cy + dy, r_ * a, fill=(250, 244, 230))
        if a > 0.6:
            person(c, cx - 36, cy + 56, 100, ELLIS, dir=1, mood='smile', arms=(0, 10))
            person(c, cx + 36, cy + 56, 100, GARRICK, dir=-1, mood='smile', arms=(0, 10))
            c.text(cx, cy - 36, 'I see you.', 24, (70, 50, 70), 'mm', bold=True, serif=True)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s8(c, u, k):
    park(c, u, 'night', cam=u * 2)
    bench(c, 640)
    seated(c, 560, 330, ELLIS, dir=1, mood='sad', arms=(0, 10))
    seated(c, 740, 330, GARRICK, dir=-1, mood='talk', talk=u * 9, arms=(0, 20 + 15 * math.sin(u * 2)))
    bench_front(c, 640)
    f = ramp(u, st(k, 0) + 1.0, st(k, 1) + 2.0)
    for i in range(4):
        d = clamp(f * 1.0 - i * 0.12)
        if d > 0:
            x = 740 + 380 * ease(d)
            person(c, x, 640 + 0 * i, 330 - 8 * i, GARRICK, dir=-1, walk=u * 6 + i, mood='flat', arms=(0, 10), tint=((120, 130, 190), 0.55 + 0.1 * i))
    waves(c, 740, 280, u, 3, 60, spd=60, span=300)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s9(c, u, k):
    park(c, u, 'night', cam=u * 2)
    gx, gy = 780, 330
    # noise field
    r = random.Random(4)
    words = ['rain', 'news', 'rain', 'they said', 'weather', 'can you believe', 'cold', 'hot', 'news', 'outrageous']
    for i in range(22):
        ang = i * 0.7 + u * 0.4 * (1 if i % 2 else -1)
        rad = 190 + 40 * math.sin(u + i) + (i % 3) * 20
        x = gx + math.cos(ang) * rad * 1.15; y = gy + math.sin(ang) * rad * .75
        v = 130 + int(60 * math.sin(u * 2 + i))
        c.text(x, y, words[i % len(words)], 22 + (i % 3) * 6, (v, v, min(255, v + 30)), 'mm', bold=True)
    bench(c, 780)
    seated(c, 780, 330, GARRICK, dir=-1, mood='talk', talk=u * 9, arms=(0, 20 + 20 * math.sin(u * 2)))
    bench_front(c, 780)
    seated(c, 330, 0, ELLIS, dir=1, mood='sad') if False else person(c, 300, 640, 330, ELLIS, dir=1, mood='sad', arms=(0, 10))
    for (i, txt) in ((1, 'a question'), (2, 'a need'), (3, 'a quiet, honest sentence')):
        s_ = st(k, i)
        f = clamp((u - s_) / 2.2)
        if f > 0:
            x = lerp(420, 640, min(1, f / 0.55)) if f < 0.55 else lerp(640, 420, ease((f - 0.55) / 0.45))
            y = 250 + i * 70 - 14 * math.sin(f * 9)
            c.rect(x - 110, y - 22, x + 110, y + 22, fill=(252, 246, 226), r=10, outline=(200, 120, 120) if f > .5 else (120, 200, 140), w=3)
            c.text(x, y, txt, 22, (60, 40, 50), 'mm', bold=True, serif=True)
    c.arc(780, 330, 250, 190, 120, 240, 5, (230, 90, 90)) if u > st(k, 1) else None
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s10(c, u, k):
    sn = sentences(k)
    cam = ramp(u, st(k, 2), D[k] - 1.0) * 700
    park(c, u, 'night', cam=cam, lamps=False)
    # world offset
    ox = -cam
    for x in (160, 1120, 1560, 2000): lamp_post(c, x + ox, GY + 36, u)
    bench(c, 640 + ox); bench(c, 1700 + ox)
    standing = u > st(k, 1) + 0.6
    if not standing:
        seated(c, 560 + ox, 330, ELLIS, dir=1, mood='sad', arms=(0, 10))
    seated(c, 740 + ox, 330, GARRICK, dir=-1, mood='talk', talk=u * 9, arms=(0, 20 + 15 * math.sin(u * 2)))
    bench_front(c, 640 + ox)
    bench_front(c, 1700 + ox)
    # distant Odile
    seated(c, 1720 + ox, 330, ODILE, dir=-1, mood='flat', arms=(0, 10))
    bench_front(c, 1700 + ox)
    if standing:
        walk = ramp(u, st(k, 2), D[k] - 1.0)
        ex = lerp(560, 1330, walk)
        person(c, ex + ox, 640 - 20, 330, ELLIS, dir=1, walk=u * 6 if 0 < walk < 1 else 0, mood='flat', arms=(0, 0))
    if st(k, 1) <= u < en(k, 1) + 1.0:
        bubble(c, 520 + ox, 230, 'Thank you for the company.', ramp(u, st(k, 1) + 0.4, st(k, 1) + 0.8), (560 + ox, 300), None, 26)
    waves(c, 740 + ox, 280, u, 3, 60, spd=60, span=300)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s11(c, u, k):
    park(c, u, 'night', cam=u, lamps=True)
    bench(c, 640)
    arrive = ramp(u, 0.2, st(k, 1) - 0.2)
    book = 1 - ramp(u, st(k, 3), st(k, 3) + 1.0)
    seated(c, 740, 360, ODILE, dir=-1, mood='smile' if u > st(k, 2) else 'flat', talk=u * 8, arms=(0, 50 if book > 0.1 else 10))
    if book > 0.02:
        c.rect(690 + (1 - book) * 160, 360 + (1 - book) * 140, 740 + (1 - book) * 160, 396 + (1 - book) * 140, fill=(120, 70, 90), r=3) if False else None
    bench_front(c, 640)
    if book > 0.02:
        bx = 700 + (1 - book) * 150; by = 500 + (1 - book) * 90
        c.rect(bx - 34, by - 16, bx + 34, by + 18, fill=(130, 76, 96), r=3); c.rect(bx - 30, by - 12, bx - 2, by + 14, fill=(240, 232, 214)); c.rect(bx + 2, by - 12, bx + 30, by + 14, fill=(240, 232, 214))
    ex = lerp(160, 560, ease(arrive)) if u < st(k, 3) else 540
    if u < st(k, 3) - 0.0 and arrive < 1:
        person(c, ex, 640, 330, ELLIS, dir=1, walk=u * 6, mood='flat', arms=(0, 0))
    elif u < st(k, 3):
        person(c, 560, 640, 330, ELLIS, dir=1, mood='talk' if st(k, 1) < u < en(k, 1) else 'flat', talk=u * 8, arms=(0, 20))
    else:
        seated(c, 540, 330, ELLIS, dir=1, mood='smile', arms=(0, 10))
    if st(k, 1) - 0.1 <= u <= en(k, 1) + 0.6:
        bubble(c, 330, 210, 'Is this seat taken?', ramp(u, st(k, 1), st(k, 1) + 0.3), (500, 300), None, 28)
    if st(k, 2) - 0.1 <= u <= en(k, 2) + 0.8:
        bubble(c, 960, 210, 'No.', ramp(u, st(k, 2), st(k, 2) + 0.3), (790, 280), None, 30)
    fcol(c, ramp(u, 0, 0.6))
    sub(c, k, u)

def s12(c, u, k):
    f = ramp(u, 0, 3)
    park(c, u, 'night', cam=u)
    c.veil(0, 0, W, H, (255, 190, 120), 0.1 * f)
    bench(c, 640, 420)
    spk_o = st(k, 1) <= u < en(k, 1)
    spk_e = u >= st(k, 2)
    seated(c, 560, 340, ELLIS, dir=1, mood='talk' if spk_e else 'smile', talk=u * 8, arms=(0, 20 + 15 * math.sin(u * 2) * (1 if spk_e else 0)), tint=((255, 190, 120), 0.08))
    seated(c, 740, 340, ODILE, dir=-1, mood='talk' if spk_o else 'smile', talk=u * 8 + 2, arms=(0, 10), nod=math.sin(u * 2) * .3, tint=((255, 190, 120), 0.08))
    bench_front(c, 640)
    lamp_post(c, 640 + 330, GY + 36, u)
    fireflies(c, u, 16, 31, 0.8)
    if st(k, 1) - 0.1 <= u <= en(k, 1) + 1.0:
        bubble(c, 900, 190, 'What brought you out here tonight?', ramp(u, st(k, 1), st(k, 1) + 0.3), (770, 260), None, 28)
    a = ramp(u, DURS[k] + LEAD[k] + 0.3, DURS[k] + LEAD[k] + 1.5)
    if a > 0:
        v = int(255 * a)
        c.veil(0, 50, W, 170, (10, 10, 30), 0.5 * a)
        c.text(640, 110, 'Talk to someone, not near them.', 56, (v, int(v * .9), int(v * .72)), 'mm', bold=True, serif=True)
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
