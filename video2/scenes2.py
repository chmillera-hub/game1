# ================================================================= Buzz story scenes
LAND_Y = 310
def stairtop(x): return LAND_Y + max(0, (x - 240)) * 28 / 58
def arcpos(u): return 225 + 655 * u, 262 - 180 * u + 508 * u * u   # feet position
WIN = (1005, 70, 170, 210)
WCX, WCY = 1090, 175

def put_c(img, spr, cx, cy, rot=0, alpha=1.0, flip=False):
    s = spr.transpose(Image.FLIP_LEFT_RIGHT) if flip else spr
    if rot: s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = s.split()[3].point(lambda v: int(v * alpha)); s = s.copy(); s.putalpha(a)
    img.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)

_t2 = {}
def toy(wings=0.0, arm=True, h=104):
    wq = round(wings * 4) / 4; key = (wq, arm)
    if key in _t2: return _t2[key]
    w = 200; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = w // 2
    if wq > 0:   # wings (behind body)
        for sgn in (-1, 1):
            ang = math.radians(25 + 55 * wq)
            tip = (cx + sgn * (30 + 62 * wq) , 40 - 28 * wq)
            d.polygon([(cx + sgn * 14, 38), tip, (cx + sgn * (18 + 40 * wq), 64)], fill=(235, 235, 245))
            d.polygon([(cx + sgn * 14, 46), (cx + sgn * (28 + 46 * wq), 40 - 14 * wq), (cx + sgn * (16 + 30 * wq), 58)], fill=(150, 80, 200))
    d.rectangle([cx - 15, 66, cx + 15, h - 4], fill=(140, 80, 200))                # legs
    d.line([(cx, 74), (cx, h - 4)], fill=(90, 50, 140), width=2)
    d.rectangle([cx - 17, h - 12, cx - 1, h - 1], fill=(235, 235, 240)); d.rectangle([cx + 1, h - 12, cx + 17, h - 1], fill=(235, 235, 240))
    d.rounded_rectangle([cx - 25, 30, cx + 25, 70], 8, fill=(240, 240, 245))        # torso
    d.rectangle([cx - 14, 38, cx + 14, 56], fill=(70, 190, 90)); d.ellipse([cx - 4, 42, cx + 4, 50], fill=(230, 60, 60))
    d.ellipse([cx - 26, 28, cx - 10, 44], fill=(70, 190, 90)); d.ellipse([cx + 10, 28, cx + 26, 44], fill=(70, 190, 90))   # shoulders
    d.rectangle([cx - 31, 36, cx - 24, 62], fill=(240, 240, 245)); d.ellipse([cx - 33, 58, cx - 22, 68], fill=(70, 190, 90))
    if arm: d.rectangle([cx + 24, 36, cx + 31, 62], fill=(240, 240, 245)); d.ellipse([cx + 22, 58, cx + 33, 68], fill=(70, 190, 90))
    d.ellipse([cx - 17, -1, cx + 17, 33], fill=(235, 235, 240)); d.ellipse([cx - 13, 3, cx + 13, 29], fill=(185, 220, 245))   # helmet / face
    d.ellipse([cx - 9, 10, cx + 9, 28], fill=(245, 205, 170))
    d.ellipse([cx - 5, 15, cx - 2, 18], fill=(30, 30, 30)); d.ellipse([cx + 2, 15, cx + 5, 18], fill=(30, 30, 30))
    d.arc([cx - 5, 17, cx + 5, 25], 20, 160, fill=(120, 50, 50), width=1)
    d.rectangle([cx - 14, 30, cx + 14, 34], fill=(70, 190, 90))
    _t2[key] = im
    return im

def arm_piece(img, x, y, ang, t=0):
    lay = Image.new("RGBA", (40, 70), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([14, 6, 22, 52], fill=(240, 240, 245)); d.ellipse([11, 48, 25, 64], fill=(70, 190, 90))
    put_c(img, lay, x, y, ang)

_j = {}
def jesus(h=130, pose="stand"):
    key = (h, pose)
    if key in _j: return _j[key]
    w = int(h * 1.1); im = Image.new("RGBA", (w, h + 6), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = w // 2
    robe = (238, 234, 226); skin = (224, 182, 142); hair = (92, 62, 42)
    hr = h * 0.075
    bottom = h if pose != "kneel" else h
    if pose == "kneel":
        d.ellipse([cx - h * 0.42, h * 0.74, cx + h * 0.42, h + 2], fill=robe)
        d.polygon([(cx - h * 0.12, h * 0.24), (cx + h * 0.12, h * 0.24), (cx + h * 0.22, h * 0.86), (cx - h * 0.22, h * 0.86)], fill=robe)
    else:
        d.polygon([(cx - h * 0.12, h * 0.24), (cx + h * 0.12, h * 0.24), (cx + h * 0.2, h), (cx - h * 0.2, h)], fill=robe)
    d.polygon([(cx - h * 0.12, h * 0.4), (cx + h * 0.12, h * 0.4), (cx + h * 0.12, h * 0.44), (cx - h * 0.12, h * 0.44)], fill=(190, 150, 110))
    lw = max(4, int(h * 0.05)); sx, sy = cx + h * 0.1, h * 0.27; slx = cx - h * 0.1
    if pose == "head":
        d.line([(sx, sy), (cx + h * 0.2, h * 0.13), (cx + h * 0.05, h * 0.05)], fill=robe, width=lw)
        d.line([(slx, sy), (slx - 4, h * 0.55)], fill=robe, width=lw)
    elif pose == "face":
        d.line([(sx, sy), (cx + h * 0.16, h * 0.18), (cx + h * 0.02, h * 0.1)], fill=robe, width=lw)
        d.ellipse([cx - h * 0.02, h * 0.07, cx + h * 0.08, h * 0.15], fill=skin)
        d.line([(slx, sy), (slx - 4, h * 0.55)], fill=robe, width=lw)
    elif pose == "kneel":
        d.line([(sx, sy + 6), (cx + h * 0.42, h * 0.52)], fill=robe, width=lw); d.line([(slx, sy + 6), (cx + h * 0.4, h * 0.56)], fill=robe, width=lw)
        d.ellipse([cx + h * 0.4, h * 0.5, cx + h * 0.47, h * 0.58], fill=skin)
    elif pose == "open":
        d.line([(sx, sy), (cx + h * 0.42, h * 0.5)], fill=robe, width=lw); d.line([(slx, sy), (cx - h * 0.42, h * 0.5)], fill=robe, width=lw)
    else:
        d.line([(sx, sy), (sx + 4, h * 0.55)], fill=robe, width=lw); d.line([(slx, sy), (slx - 4, h * 0.55)], fill=robe, width=lw)
    d.ellipse([cx - hr * 1.5, h * 0.03, cx + hr * 1.5, h * 0.03 + hr * 3.6], fill=hair)   # hair
    d.ellipse([cx - hr, h * 0.05, cx + hr, h * 0.05 + hr * 2.2], fill=skin)
    d.polygon([(cx - hr * 0.8, h * 0.05 + hr * 1.5), (cx + hr * 0.8, h * 0.05 + hr * 1.5), (cx, h * 0.05 + hr * 3.1)], fill=hair)  # beard
    ey = h * 0.05 + hr * 0.95
    d.ellipse([cx - hr * 0.5, ey, cx - hr * 0.3, ey + 3], fill=(40, 30, 25)); d.ellipse([cx + hr * 0.3, ey, cx + hr * 0.5, ey + 3], fill=(40, 30, 25))
    if pose not in ("face",):
        d.arc([cx - hr * 0.5, ey + 3, cx + hr * 0.5, ey + hr * 0.9], 20, 160, fill=(210, 150, 130), width=1)
    d.ellipse([cx - hr * 1.7, -2, cx + hr * 1.7, hr * 0.9], outline=(255, 215, 120), width=3)   # halo
    _j[key] = im
    return im

def emo(img, x, yb, kind, mood, t, r=22, ph=0.0):
    cols = {"anger": (220, 70, 60), "sadness": (80, 120, 225), "fear": (170, 115, 220)}
    d = ImageDraw.Draw(img); c = cols[kind]
    bob = abs(math.sin(t * 9 + ph)) * 9 if mood == "laugh" else 0
    jit = math.sin(t * 40 + ph) * 2.2 if mood == "worry" else 0
    cx, cy = x + jit, yb - r - bob
    if kind == "anger":
        for k in range(-2, 3): d.polygon([(cx + k * r * 0.4 - 5, cy - r * 0.8), (cx + k * r * 0.4, cy - r * 1.4 - abs(k) * -3), (cx + k * r * 0.4 + 5, cy - r * 0.8)], fill=c)
    if kind == "sadness": d.polygon([(cx - r * 0.5, cy - r * 0.6), (cx, cy - r * 1.55), (cx + r * 0.5, cy - r * 0.6)], fill=c)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    ex = r * 0.38; ey = cy - r * 0.15
    if mood == "laugh":
        for s in (-1, 1): d.arc([cx + s * ex - 6, ey - 5, cx + s * ex + 6, ey + 5], 200, 340, fill=(30, 20, 20), width=2)
        d.ellipse([cx - 7, cy + r * 0.25, cx + 7, cy + r * 0.6], fill=(60, 20, 25))
    elif mood == "worry":
        for s in (-1, 1):
            d.ellipse([cx + s * ex - 6, ey - 7, cx + s * ex + 6, ey + 7], fill=(255, 255, 255)); d.ellipse([cx + s * ex - 2, ey - 2, cx + s * ex + 2, ey + 2], fill=(20, 20, 20))
        d.line([(cx - 8, cy + r * 0.5), (cx - 3, cy + r * 0.4), (cx + 3, cy + r * 0.55), (cx + 8, cy + r * 0.45)], fill=(40, 20, 30), width=2)
    elif mood == "sad":
        for s in (-1, 1): d.ellipse([cx + s * ex - 3, ey - 3, cx + s * ex + 3, ey + 3], fill=(20, 20, 30))
        d.arc([cx - 8, cy + r * 0.35, cx + 8, cy + r * 0.8], 200, 340, fill=(30, 20, 30), width=2)
    else:   # hold / caring
        for s in (-1, 1): d.ellipse([cx + s * ex - 3, ey - 3, cx + s * ex + 3, ey + 3], fill=(20, 20, 30))
        d.arc([cx - 7, cy + r * 0.1, cx + 7, cy + r * 0.55], 20, 160, fill=(30, 20, 30), width=2)
    if kind == "anger":
        d.line([(cx - ex - 8, ey - 12), (cx - 2, ey - 6)], fill=(60, 10, 10), width=3); d.line([(cx + ex + 8, ey - 12), (cx + 2, ey - 6)], fill=(60, 10, 10), width=3)

def bubble(img, x, y, text, size=20, a=1.0, tail=None):
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = F(size)
    tw = d.textlength(text, font=f); bx0, by0, bx1, by1 = x - tw / 2 - 14, y - 6, x + tw / 2 + 14, y + size + 12
    d.rounded_rectangle([bx0, by0, bx1, by1], 14, fill=(250, 248, 240, int(235 * a)))
    if tail: d.polygon([(x - 8, by1 - 2), (x + 8, by1 - 2), tail], fill=(250, 248, 240, int(235 * a)))
    d.text((x - tw / 2, y), text, font=f, fill=(40, 35, 45, int(255 * a)))
    img.paste(lay, (0, 0), lay)

def card(img, x, y, wd, ht, text, hue=(90, 140, 230), a=1.0, rot=0):
    lay = Image.new("RGBA", (wd + 8, ht + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([2, 2, wd + 2, ht + 2], 8, fill=(246, 246, 250, 240), outline=hue + (255,), width=2)
    d.rectangle([4, 4, wd, 14], fill=hue + (255,))
    f = F(max(10, int(ht * 0.2)), bold=True); d.text((10, 18), text, font=f, fill=(40, 40, 55, 255))
    d.line([(10, ht - 22), (wd - 20, ht - 22)], fill=(190, 190, 200, 255), width=3); d.line([(10, ht - 10), (wd - 50, ht - 10)], fill=(190, 190, 200, 255), width=3)
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    put_c(img, lay, x, y, rot)

def stage(t, win=0.5, dim=0.0, shake=0.0):
    img = gradient((24, 22, 52), (74, 54, 86), "stage")
    d = ImageDraw.Draw(img)
    for x in range(0, W, 80): d.line([(x, 0), (x, 590)], fill=(30, 28, 62), width=2)
    # window
    wx, wy, ww, wh = WIN
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    lc = mix((60, 70, 130), (255, 225, 150), win); ld.rectangle([wx, wy, wx + ww, wy + wh], fill=lc)
    glow(img, lay, 40, 0.8 + win)
    if win > 0.3: rays(img, WCX, WCY, t, (255, 225, 150), n=10, length=520, strength=0.16 * win)
    d = ImageDraw.Draw(img)
    d.rectangle([wx, wy, wx + ww, wy + wh], outline=(210, 175, 125), width=8)
    d.line([(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], fill=(210, 175, 125), width=6); d.line([(wx, wy + wh / 2), (wx + ww, wy + wh / 2)], fill=(210, 175, 125), width=6)
    d.rectangle([wx - 14, wy + wh, wx + ww + 14, wy + wh + 12], fill=(190, 150, 105))
    # landing, stairs, floor
    d.rectangle([0, LAND_Y, 240, 720], fill=(74, 48, 38)); d.line([(0, LAND_Y), (240, LAND_Y)], fill=(150, 104, 70), width=5)
    for i in range(10):
        x0 = 240 + i * 58; top = LAND_Y + i * 28
        d.rectangle([x0, top, x0 + 58, 720], fill=(104 - i * 3, 68 - i * 2, 48 - i * 2)); d.line([(x0, top), (x0 + 58, top)], fill=(158, 112, 76), width=5)
    d.rectangle([820, 590, W, 720], fill=(112, 74, 52)); d.line([(820, 590), (W, 590)], fill=(165, 118, 82), width=5)
    for k in range(6): d.line([(820 + k * 90, 590), (780 + k * 120, 720)], fill=(92, 60, 42), width=2)
    # railing
    d.rectangle([220, 258, 240, LAND_Y], fill=(120, 78, 52)); d.ellipse([216, 248, 244, 268], fill=(150, 100, 66))
    for i in range(10):
        bx = 240 + i * 58 + 29; d.line([(bx, stairtop(bx)), (bx, stairtop(bx) - 48)], fill=(130, 86, 58), width=5)
    d.line([(238, 262), (820, 543)], fill=(150, 100, 66), width=8)
    if dim > 0: img = Image.blend(img, Image.new("RGB", (W, H), (4, 3, 12)), dim)
    return img

def push(img, p, cx, cy, amt=0.08):
    z = 1 + amt * p; w, h = W / z, H / z
    x0 = clamp(cx - w / 2, 0, W - w); y0 = clamp(cy - h / 2, 0, H - h)
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)

def notes(img, t, x, y, n=6, a=1.0):
    d = ImageDraw.Draw(img); f = F(30)
    for i in range(n):
        u = ((t * 0.35 + i / n) % 1.0)
        c = int(255 * math.sin(u * math.pi) * a)
        d.text((x + math.sin(i * 2.1 + t) * 70 + i * 22, y - u * 220), "♪" if i % 2 else "♫", font=f, fill=(c, int(c * 0.85), int(c * 0.5)))

def crowd(img, t, p0=0.0, mood="laugh", jesus_pose="head", names=False, seeds=0.0):
    img.paste(Image.new("RGB", (1, 1)), (0, 0)) if False else None
    sp = jesus(130, jesus_pose); put(img, sp, 60, LAND_Y + 2)
    for k, (x, kind) in enumerate([(135, "anger"), (180, "sadness"), (215, "fear")]):
        pass
    emo(img, 120, LAND_Y, "anger", mood, t, 22, 0.0); emo(img, 160, LAND_Y, "sadness", mood, t, 20, 1.3); emo(img, 200, LAND_Y, "fear", mood, t, 19, 2.1)

# ---------------------------------------------------------------- scenes
def s_title(t, d, p):
    img = stage(t, 0.35, 0.45)
    put_c(img, toy(0.0), 228, 262 - 52)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov); od.rounded_rectangle([250, 220, 1030, 420], 20, fill=(8, 6, 20, int(170 * seg(p, 0.05, 0.25))))
    img.paste(ov, (0, 0), ov)
    a = seg(p, 0.1, 0.35) * (1 - seg(p, 0.9, 1.0))
    title(img, "THE BUZZ LIGHTYEAR LEAP", "a story about falling, and being held", a, y=262, size=44)
    return img

def s_launch(t, d, p):
    img = stage(t, 0.3 + 0.2 * seg(p, 0.3, 1))
    rays(img, 228, 230, t, (255, 220, 140), n=12, length=700, strength=0.2 * seg(p, 0.1, 0.5))
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([228 - 55, 215 - 55, 228 + 55, 215 + 55], fill=(120, 90, 40)); glow(img, lay, 40, 0.8)
    put_c(img, toy(0.0), 228, 262 - 52 + math.sin(t * 2) * 1.5)
    notes(img, t, 300, 260, 7, seg(p, 0.15, 0.4))
    title(img, "THE LAUNCHPAD TO DESTINY", a=seg(p, 0.02, 0.15), y=26, size=28)
    return push(img, p, 228, 250, 0.22)

def s_crowd(t, d, p):
    img = stage(t, 0.3)
    put_c(img, toy(0.0), 228, 262 - 52)
    sp = jesus(130, "head"); a = seg(p, 0.1, 0.25)
    put(img, sp, 60, LAND_Y + 2, alpha=a)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([60 - 30, 200 - 30, 60 + 30, 200 + 30], outline=(200, 160, 60), width=4); glow(img, lay, 24, 0.7)
    for (x, kind, ph, th) in [(120, "anger", 0.0, 0.3), (160, "sadness", 1.3, 0.38), (205, "fear", 2.1, 0.46)]:
        if p > th: emo(img, x, LAND_Y, kind, "laugh" if p > 0.5 else "hold", t, 22 if kind == "anger" else 20, ph)
    nm = [(60, 160, "Jesus", 0.12), (120, 240, "Anger", 0.32), (160, 262, "Sadness", 0.4), (205, 240, "Fear", 0.48)]
    for x, y, s, th in nm: label(img, x, y - 8 if s != "Jesus" else 100, s, 20, (255, 235, 200), seg(p, th, th + 0.05) * (1 - seg(p, 0.8, 0.9)))
    bubble(img, 190, 130, "oh my God, he's actually going to do it", 18, seg(p, 0.55, 0.62) * (1 - seg(p, 0.78, 0.84)), tail=(170, 205))
    bubble(img, 330, 150, "we've seen you leap before", 18, seg(p, 0.8, 0.86), tail=(215, 200))
    title(img, "A STRANGE LITTLE CROWD", a=seg(p, 0.02, 0.1), y=26, size=28)
    return push(img, p, 180, 250, 0.2)

def s_dream(t, d, p):
    win = 0.35 + 0.6 * seg(p, 0.45, 0.75)
    img = stage(t, win)
    crowd_draw(img, t, "laugh", "head")
    wing = seg(p, 0.05, 0.3)
    put_c(img, toy(wing), 228, 262 - 52 + math.sin(t * 2) * 1.5)
    # posts streaming from Buzz toward the window
    lines = [("Watch me post online", 0.12), ("emotional suppression", 0.2), ("capitalism", 0.26), ("Jesus", 0.31), ("loneliness", 0.35), ("the human condition", 0.39)]
    cols = [(90, 140, 230), (230, 110, 90), (240, 190, 70), (120, 200, 140), (170, 120, 220), (230, 140, 190)]
    for i, (txt, th) in enumerate(lines):
        u = (p - th) / 0.3
        if 0 < u < 1:
            x = lerp(300, 880, ease(u)); y = lerp(230, 140, ease(u)) + math.sin(u * 8 + i) * 12
            card(img, x, y, 170, 66, txt[:20], cols[i], a=math.sin(u * math.pi) ** 0.5, rot=math.sin(u * 5 + i) * 8)
    # the dream
    items = ["emotional literacy", "nonviolent, pro-human frameworks", "people who feel, speak & connect"]
    label(img, 780, 300, "THE WINDOW", 28, (255, 235, 170), seg(p, 0.55, 0.65))
    for i, s in enumerate(items): label(img, 780, 340 + i * 30, s, 20, (255, 245, 215), seg(p, 0.62 + i * 0.09, 0.7 + i * 0.09))
    title(img, "WATCH ME REACH THE WINDOW", a=seg(p, 0.02, 0.1), y=26, size=28)
    return img

def crowd_draw(img, t, mood, jpose):
    put(img, jesus(130, jpose), 60, LAND_Y + 2)
    emo(img, 120, LAND_Y, "anger", mood, t, 22, 0.0); emo(img, 160, LAND_Y, "sadness", mood, t, 20, 1.3); emo(img, 205, LAND_Y, "fear", mood, t, 19, 2.1)

def buzz_arc(img, u, t, wings, spin_rate=0.0, arm=True):
    x, y = arcpos(u)
    put_c(img, toy(wings, arm), x, y - 52, rot=-spin_rate * u * 360)
    return x, y

def s_leap(t, d, p):
    img = stage(t, 0.95)
    crowd_draw(img, t, "laugh", "head")
    u = 0.32 * seg(p, 0.05, 0.95)
    x, y = arcpos(u)
    rays(img, x, y - 50, t, (255, 230, 150), n=14, length=420, strength=0.2)
    buzz_arc(img, u, t, 1.0)
    for k in range(1, 5):   # trail of hopeful posts
        uu = u - k * 0.04
        if uu > 0:
            xx, yy = arcpos(uu); card(img, xx - 10, yy - 70 - k * 5, 90, 40, "my deep dive", (90, 140, 230), a=0.5 - k * 0.1, rot=k * 6)
    notes(img, t, 500, 300, 5, 1.0)
    title(img, "FOR A MOMENT, HE FLIES", a=seg(p, 0.1, 0.3), y=26, size=28)
    return img

def s_fall(t, d, p):
    img = stage(t, 0.95 - 0.35 * seg(p, 0, 1))
    u = lerp(0.32, 0.985, seg(p, 0.02, 0.97))
    crowd_draw(img, t, "worry", "face")
    for k, (x, s) in enumerate([(120, "oh no"), (175, "oh no"), (215, "oh no")]):
        label(img, x + 20 * math.sin(t * 25 + k), 200 - k * 22 + math.sin(t * 30 + k) * 2, s, 22, (255, 220, 200), seg(p, 0.15 + k * 0.07, 0.2 + k * 0.07))
    buzz_arc(img, u, t, 1 - seg(p, 0.0, 0.25), spin_rate=1.4)
    title(img, "THEN GRAVITY CATCHES UP", a=seg(p, 0.02, 0.1), y=26, size=28)
    return img

SOCIAL = [("BANNED", (230, 60, 60)), ("BLOCKED", (230, 100, 50)), ("TROLLED", (230, 160, 40)), ("INVALIDATED", (200, 70, 150)),
          ("IGNORED", (130, 130, 160)), ("BURIED BY THE FEED", (110, 120, 200)), ("“nobody cares”", (170, 170, 190))]
def s_impact(t, d, p):
    hit = 0.1
    sh = max(0, 1 - (p - hit) * 12) * 10 if p > hit else 0
    img = stage(t, 0.4, 0.2)
    crowd_draw(img, t, "worry", "face")
    if p < hit:
        buzz_arc(img, lerp(0.95, 1.0, p / hit), t, 0.0, spin_rate=1.4)
    else:
        put_c(img, toy(0.0, False), 880, 590 - 24, rot=-82)
        ap = seg(p, hit, hit + 0.12)    # arm flies off and bounces
        ax = 880 + 110 * ap; ay = 590 - 40 - math.sin(ap * math.pi) * 90 + ap * 22
        arm_piece(img, ax, ay, 200 * ap + 20)
    if p > hit:
        for i, (txt, col) in enumerate(SOCIAL):
            th = 0.25 + i * 0.09; u = (p - th) / 0.2
            if 0 <= u <= 1:
                sx = lerp(330, 760, ease(u)); sy = lerp(210, 580, ease(u)) - math.sin(u * math.pi) * 40
                lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); ld.text((sx - 10, sy), txt, font=F(30, bold=True), fill=tuple(int(c * 0.6) for c in col)); glow(img, lay, 10, 0.8)
                label(img, sx + 60, sy, txt, 30, col, math.sin(u * math.pi) ** 0.4, anchor="l")
    title(img, "THE BOTTOM OF THE ALGORITHM", a=seg(p, 0.0, 0.1), y=26, size=28)
    if sh > 0: img = img.transform((W, H), Image.AFFINE, (1, 0, math.sin(t * 90) * sh, 0, 1, math.cos(t * 70) * sh))
    return img

def s_lying(t, d, p):
    img = stage(t, 0.18, 0.45)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([780, 520, 980, 640], fill=(40, 40, 70)); glow(img, lay, 40, 0.8)
    put_c(img, toy(0.0, False), 880, 590 - 24, rot=-82)
    arm_piece(img, 990, 556, 20)
    bubble(img, 700, 360, "I failed you guys.", 24, seg(p, 0.1, 0.2) * (1 - seg(p, 0.35, 0.4)), tail=(830, 480))
    bubble(img, 690, 330, "I tried to reach the window.", 24, seg(p, 0.45, 0.52) * (1 - seg(p, 0.7, 0.76)), tail=(830, 480))
    bubble(img, 690, 330, "And it feels like nobody cares.", 24, seg(p, 0.78, 0.86), tail=(830, 480))
    title(img, "HE LIES THERE, ASHAMED", a=seg(p, 0.0, 0.1), y=26, size=28)
    return push(img, p, 880, 520, 0.28)

def s_comfort(t, d, p):
    img = stage(t, 0.25 + 0.25 * seg(p, 0.85, 1.0), 0.25 * (1 - seg(p, 0.7, 1.0)))
    ap = seg(p, 0.82, 0.9)
    # emotions run down the stairs
    run = seg(p, 0.03, 0.34); sx = lambda k: lerp(120 + k * 40, [820, 940, 880][k], run)
    for k, (kind, ph, r) in enumerate([("anger", 0.0, 22), ("sadness", 1.3, 20), ("fear", 2.1, 19)]):
        x = sx(k); yb = min(stairtop(x), 590) if run < 1 else 590
        if kind == "fear" and run >= 1: yb = 520 + math.sin(t * 3) * 8
        mood = "worry" if run < 1 else "hold"
        emo(img, x, yb, kind, mood, t, r, ph)
    put_c(img, toy(0.0, p > 0.86), 880, 590 - 24, rot=-82 + 80 * ap)
    # Jesus walks down and kneels
    jx = lerp(60, 985, seg(p, 0.12, 0.5)); jyb = min(stairtop(jx), 590) if jx < 820 else 590
    pose = "kneel" if p > 0.5 else "stand"
    put(img, jesus(130, pose), jx, jyb + 2, flip=True)
    if p <= 0.86: arm_piece(img, jx - 48, jyb - 66, 90)
    if 0.84 < p < 0.96:
        fl = 1 - abs(p - 0.88) / 0.04
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([900 - 60, 540 - 60, 900 + 60, 540 + 60], fill=(255, 235, 170)); glow(img, lay, 30, 1.6 * max(0, fl))
    label(img, 880, 380, "gently,\nno lecture, no shame".split("\n")[1], 22, (255, 240, 210), seg(p, 0.55, 0.65) * (1 - seg(p, 0.8, 0.86)))
    label(img, 880, 410, "no “I told you so”", 22, (255, 240, 210), seg(p, 0.62, 0.7) * (1 - seg(p, 0.8, 0.86)))
    label(img, 880, 380, "pop.", 40, (255, 235, 160), seg(p, 0.86, 0.9) * (1 - seg(p, 0.96, 1)))
    title(img, "NOT HOW IT LOOKS — HOW IT HEALS", a=0.0, y=26, size=28)
    return img

def s_repost(t, d, p):
    img = stage(t, 0.5 + 0.2 * p, 0.1)
    crowd_draw(img, t, "hold", "stand")
    put_c(img, toy(0.0, True), 880, 590 - 52)
    phr = [("my inner landscape matters", (240, 190, 70)), ("my emotions matter", (230, 110, 90)), ("the pro-human framework matters", (120, 200, 140)), ("the window matters", (255, 225, 150))]
    for i, (s, c) in enumerate(phr):
        th = 0.34 + i * 0.16; u = (p - th) / 0.35
        if 0 < u < 1:
            x = lerp(880, 600 + i * 130, ease(u)); y = lerp(500, 120 + i * 40, ease(u))
            card(img, x, y, 200, 70, s[:22], c, a=math.sin(u * math.pi) ** 0.5, rot=math.sin(u * 4 + i) * 6)
            lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([x - 8, y - 8, x + 8, y + 8], fill=tuple(int(v * 0.6) for v in c)); glow(img, lay, 20, 0.7)
    label(img, 640, 100, "Maybe not here.  Maybe not on this platform.  But somewhere.", 28, (255, 245, 215), seg(p, 0.12, 0.22) * (1 - seg(p, 0.3, 0.38)))
    title(img, "I'LL POST AGAIN", a=seg(p, 0.0, 0.1), y=26, size=28)
    return img

def rope_x(y): return lerp(1060, 1010, clamp((y - 280) / 310)) + math.sin(y * 0.03) * 4

def s_rope(t, d, p):
    img = stage(t, 0.75 + 0.2 * seg(p, 0.5, 1))
    d2 = ImageDraw.Draw(img)
    pts = [(rope_x(y) + math.sin(t * 1.5 + y * 0.02) * 3, y) for y in range(286, 592, 6)]
    d2.line(pts, fill=(190, 150, 100), width=6); d2.line(pts, fill=(130, 95, 60), width=2)
    for k in range(0, len(pts), 3): d2.line([(pts[k][0] - 3, pts[k][1] - 3), (pts[k][0] + 3, pts[k][1] + 3)], fill=(110, 80, 50), width=2)
    put_c(img, toy(0.0, True), 880, 590 - 52)
    # Buzz looks up (floating small hope) + community arrives
    people = [(940, (200, 120, 90)), (1070, (110, 160, 200)), (790, (150, 190, 120)), (1130, (190, 140, 200)), (700, (220, 180, 100))]
    for i, (x, c) in enumerate(people):
        ar = seg(p, 0.3 + i * 0.07, 0.42 + i * 0.07); xx = x + (1 - ar) * (150 if i % 2 else -150) * 0
        if ar > 0:
            put(img, person_sprite(66, c, "up" if (int(t * 2) + i) % 2 else "down"), xx, 590, alpha=ar)
    # climbers on the rope
    for i, c in enumerate([(120, 170, 220), (220, 170, 110), (170, 220, 140)]):
        b = seg(p, 0.45 + i * 0.1, 0.95 + i * 0.0)
        yy = lerp(570, 330 + i * 70, b)
        if b > 0:
            x = rope_x(yy) + (i - 1) * 16
            put(img, person_sprite(44, c, "up"), x, yy + 24, alpha=min(1, b * 4))
    cap = [("rope", 0.3), ("community", 0.4), ("collaboration", 0.5), ("slow, steady climbing", 0.62)]
    for i, (s, th) in enumerate(cap): label(img, 560, 150 + i * 36, s, 28, (255, 240, 205), seg(p, th, th + 0.06))
    label(img, 560, 118, "maybe he doesn't need to leap… maybe he needs:", 22, (210, 220, 245), seg(p, 0.25, 0.32))
    title(img, "STILL HIGH — BUT NOT ALONE", a=seg(p, 0.0, 0.1), y=26, size=28)
    return img

def s_arms(t, d, p):
    img = gradient((8, 10, 30), mix((30, 30, 70), (110, 80, 70), seg(p, 0.5, 1)), "arms%d" % int(seg(p, 0.5, 1) * 20))
    d2 = ImageDraw.Draw(img)
    r = random.Random(5)
    for i in range(90): d2.point((r.random() * W, r.random() * H * 0.7), fill=(150, 150, 190))
    # glowing arms (cradle) rise from both sides
    rise = seg(p, 0.2, 0.7)
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    for sgn in (-1, 1):
        pts = []
        for k in range(30):
            u = k / 29; x = 640 + sgn * lerp(640, 70, ease(u)); y = lerp(740, 560 - 50 * rise, u) + math.sin(u * 3.14) * 20 * (1 - rise)
            pts.append((x, y))
        ld.line(pts, fill=(255, 205, 120), width=70)
        for (x, y) in pts[::3]: ld.ellipse([x - 35, y - 35, x + 35, y + 35], fill=(255, 205, 120))
        ld.ellipse([640 + sgn * 80 - 45, 590 - 50 * rise - 40, 640 + sgn * 80 + 45, 590 - 50 * rise + 40], fill=(255, 225, 150))
    lay = lay.point(lambda v: int(v * (0.15 + 0.5 * rise))); glow(img, lay, 36, 1.5)
    # Buzz falls from above and is caught
    fy = lerp(-60, 500, ease(seg(p, 0.05, 0.65))); rot = lerp(180, -10, ease(seg(p, 0.05, 0.65)))
    put_c(img, toy(0.0, True), 640, fy, rot=rot)
    for s, th in (("banned again", 0.12), ("blocked again", 0.2), ("ignored again", 0.28)):
        u = (p - th) / 0.2
        if 0 < u < 1: label(img, 640 + 160 * (1 if th == 0.2 else -1), lerp(80, 430, u), s, 22, (200, 120, 120), math.sin(u * math.pi))
    # companions
    a = seg(p, 0.6, 0.8)
    put(img, jesus(110, "open"), 330, 650, alpha=a)
    for x, kind, ph in [(910, "anger", 0.0), (960, "sadness", 1.3), (1010, "fear", 2.1)]: emo(img, x, 650, kind, "hold", t, 20, ph) if a > 0.5 else None
    label(img, 640, 120, "“The eternal God is thy refuge, and underneath are the everlasting arms.”", 26, (255, 235, 180), seg(p, 0.4, 0.55))
    label(img, 640, 158, "— Deuteronomy 33:27", 20, (220, 200, 150), seg(p, 0.45, 0.6))
    title(img, "THE EVERLASTING ARMS", a=seg(p, 0.0, 0.1), y=26, size=28)
    return img

def s_end(t, d, p):
    img = stage(t, 0.9 + 0.1 * math.sin(t))
    d2 = ImageDraw.Draw(img)
    pts = [(rope_x(y), y) for y in range(286, 592, 6)]; d2.line(pts, fill=(190, 150, 100), width=6)
    put_c(img, toy(0.0, True), 880, 590 - 52)
    for i, (x, c) in enumerate([(780, (150, 190, 120)), (940, (200, 120, 90)), (700, (220, 180, 100)), (1000, (110, 160, 200)), (1130, (190, 140, 200))]):
        put(img, person_sprite(66, c, "up" if (int(t * 2) + i) % 2 else "down"), x, 590)
    for i, yy in enumerate((420, 360, 330)):
        put(img, person_sprite(44, [(120, 170, 220), (220, 170, 110), (170, 220, 140)][i], "up"), rope_x(yy) + (i - 1) * 16, yy + 24)
    put(img, jesus(130, "stand"), 640, 592); emo(img, 600, 590, "anger", "hold", t, 20, 0); emo(img, 560, 590, "sadness", "hold", t, 20, 1); emo(img, 520, 590, "fear", "hold", t, 20, 2)
    rays(img, WCX, WCY, t, (255, 225, 150), n=12, length=900, strength=0.22)
    for i, s in enumerate(["Not by jumping.", "Not alone.", "Through persistence, honesty & community."]):
        label(img, 420, 90 + i * 50, s, 36 if i < 2 else 30, (255, 248, 230), seg(p, 0.08 + i * 0.2, 0.2 + i * 0.2))
    return img

SCENE_FN = {"title": s_title, "launch": s_launch, "crowd": s_crowd, "dream": s_dream, "leap": s_leap, "fall": s_fall,
            "impact": s_impact, "lying": s_lying, "comfort": s_comfort, "repost": s_repost, "rope": s_rope, "arms": s_arms, "end": s_end}
CONT_IN = {"fall"}; CONT_OUT = {"leap"}
