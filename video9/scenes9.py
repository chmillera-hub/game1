# ================================================================= The Parasite Problem
GY = 520
_B9 = {}
PUR = (190, 110, 255)
HOOD = dict(robe=(70, 92, 124), skin=SKIN[0], hair=None, sash=None, tunic=True, legcol=(48, 58, 80))

def softdot(img, x, y, r, col, strength=1.0, blur=None):
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(lay).ellipse([x - r, y - r, x + r, y + r], fill=col); softglow(img, lay, blur or r * 0.8, strength)

def sword(img, hand, ang, s=1.0, col=(214, 220, 232), glow=0.0):
    x, y = hand; a = math.radians(ang); dx, dy = math.sin(a), -math.cos(a); nx, ny = -dy, dx; d = ImageDraw.Draw(img)
    d.line([(x - dx * 18 * s, y - dy * 18 * s), (x + dx * 10 * s, y + dy * 10 * s)], fill=(90, 60, 40), width=max(3, int(7 * s)))
    d.line([(x + dx * 10 * s + nx * 22 * s, y + dy * 10 * s + ny * 22 * s), (x + dx * 10 * s - nx * 22 * s, y + dy * 10 * s - ny * 22 * s)], fill=(170, 140, 70), width=max(3, int(6 * s)))
    tip = (x + dx * 150 * s, y + dy * 150 * s); b0 = (x + dx * 12 * s, y + dy * 12 * s)
    d.polygon([(b0[0] + nx * 7 * s, b0[1] + ny * 7 * s), (tip[0] + nx * 3 * s - dx * 14 * s, tip[1] + ny * 3 * s - dy * 14 * s), tip, (tip[0] - nx * 3 * s - dx * 14 * s, tip[1] - ny * 3 * s - dy * 14 * s), (b0[0] - nx * 7 * s, b0[1] - ny * 7 * s)], fill=col, outline=(120, 126, 140))
    if glow > 0:
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(lay).line([b0, tip], fill=(int(150 * glow), int(80 * glow), int(220 * glow)), width=int(16 * s)); softglow(img, lay, 14, 1.4)

def knight(img, x, yb, h, mouth="flat", L=None, R=None, rot=0.0, sw=None, alpha=1.0, eyes="open", brow=0.0, cut=None, aura=0.0, t=0.0):
    if aura > 0: softdot(img, x, yb - h * 0.5, h * 0.42, (int(110 * aura), int(50 * aura), int(170 * aura)), 1.0, 40)
    pos = cfig(img, x, yb, h, (128, 134, 150), SKIN[1], hair=(90, 62, 40), beard=True, sash=(110, 70, 40), tunic=True, legcol=(60, 60, 72), mantle=(150, 44, 44),
               mouth=mouth, L=L, R=R, rot=rot, alpha=alpha, eyes=eyes, brow=brow, cut=cut)
    if sw is not None and not rot: sword(img, pos["R"], sw, h / 300.0, glow=aura)
    return pos

def ranger(img, x, yb, h, mouth="flat", L=None, R=None, rot=0.0, sw=None, alpha=1.0, eyes="open", brow=0.0, cut=None, aura=0.0, t=0.0):
    if aura > 0: softdot(img, x, yb - h * 0.5, h * 0.42, (int(110 * aura), int(50 * aura), int(170 * aura)), 1.0, 40)
    pos = cfig(img, x, yb, h, (74, 108, 70), SKIN[0], hair=(150, 72, 40) if rot else None, sash=(96, 66, 40), tunic=True, legcol=(78, 60, 46), mantle=(54, 82, 54),
               mouth=mouth, L=L, R=R, rot=rot, alpha=alpha, eyes=eyes, brow=brow, cut=cut)
    if not rot and alpha >= 0.99: hairdo(img, pos["head"], h, (150, 72, 40))
    elif not rot: tmp = img.copy(); hairdo(tmp, pos["head"], h, (150, 72, 40)); img.paste(Image.blend(img, tmp, alpha))
    if sw is not None and not rot: sword(img, pos["R"], sw, h / 300.0, glow=aura)
    return pos

def hairdo(img, head, h, col, long=True):
    hx, hy = head; r = h * 0.07; d = ImageDraw.Draw(img)
    if long:
        for sg in (-1, 1): d.rounded_rectangle([hx + sg * r * 1.08 - r * 0.32, hy - r * 0.5, hx + sg * r * 1.08 + r * 0.32, hy + r * 2.3], int(r * 0.3), fill=col)
    d.chord([hx - r * 1.12, hy - r * 1.32, hx + r * 1.12, hy + r * 0.1], 180, 360, fill=col)
    if long: d.polygon([(hx - r * 1.1, hy - r * 0.55), (hx - r * 0.1, hy - r * 1.0), (hx - r * 0.75, hy - r * 0.25)], fill=col)

def tadpole(img, x, y, t, s=1.0, ang=0.0, glow=1.0, alpha=1.0):
    a = math.radians(ang); dx, dy = math.cos(a), math.sin(a); nx, ny = -dy, dx
    if glow > 0: softdot(img, x, y, 26 * s, (int(120 * glow * alpha), int(60 * glow * alpha), int(190 * glow * alpha)), 1.2, 18 * s)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); A = int(255 * alpha)
    pts = []
    for i in range(14):
        u = i / 13.0; wob = math.sin(t * 14 - u * 6) * 7 * s * u
        pts.append((x - dx * (12 + 46 * u) * s + nx * wob, y - dy * (12 + 46 * u) * s + ny * wob))
    for i in range(13): d.line([pts[i], pts[i + 1]], fill=(206, 176, 226, A), width=max(2, int((9 - 0.6 * i) * s)))
    d.ellipse([x - 15 * s, y - 12 * s, x + 15 * s, y + 12 * s], fill=(222, 196, 236, A), outline=(130, 80, 160, A), width=2)
    for k in (-1, 1): d.ellipse([x + dx * 6 * s + nx * k * 5 * s - 2.5 * s, y + dy * 6 * s + ny * k * 5 * s - 2.5 * s, x + dx * 6 * s + nx * k * 5 * s + 2.5 * s, y + dy * 6 * s + ny * k * 5 * s + 2.5 * s], fill=(60, 20, 70, A))
    img.paste(lay, (0, 0), lay)

def brainglow(img, head, h, t, k=1.0):
    if k <= 0: return
    hx, hy = head; r = h * 0.07
    softdot(img, hx, hy - r * 0.5, r * 1.3 * (1 + 0.12 * math.sin(t * 6)), (int(150 * k), int(70 * k), int(230 * k)), 1.3, r)
    d = ImageDraw.Draw(img); d.ellipse([hx - 3, hy - r * 0.62 - 3, hx + 3, hy - r * 0.62 + 3], fill=mix((230, 200, 255), (255, 255, 255), 0.5))

def link(img, a, b, t, k=1.0):
    if k <= 0: return
    lay = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay); pts = []
    for i in range(41):
        u = i / 40.0; x = lerp(a[0], b[0], u); y = lerp(a[1], b[1], u) - math.sin(u * math.pi) * 40 + math.sin(u * 18 - t * 9) * 8
        pts.append((x, y))
    d.line(pts, fill=(int(170 * k), int(90 * k), int(255 * k)), width=5); softglow(img, lay, 10, 1.6); img.paste(ImageChops.add(img, lay.point(lambda v: int(v * 0.7))))

def mind_alien(img, x, yb, h, t, L=None, R=None, alpha=1.0, eyeglow=0.0):
    sk = (178, 142, 198)
    pos = cfig(img, x, yb, h, (52, 30, 72), sk, face=sk, hscale=1.4, L=L, R=R, alpha=alpha, mouth="none", sash=(120, 60, 140))
    hx, hy = pos["head"]; r = h * 0.07 * 1.4
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); A = int(255 * alpha)
    for sg in (-1, 1): d.polygon([(hx + sg * r * 0.9, hy + r * 0.8), (hx + sg * r * 2.0, hy - r * 0.6), (hx + sg * r * 1.7, hy + r * 1.7)], fill=(70, 36, 96, A))         # high collar
    d.ellipse([hx - r, hy - r * 1.18, hx + r, hy + r * 1.05], fill=sk + (A,))
    d.ellipse([hx - r * 0.75, hy - r * 1.05, hx + r * 0.75, hy - r * 0.3], fill=(196, 160, 214, A))                                                          # bulbous brow
    for k_ in range(5):                                                                                                                                   # four... five tentacles
        bx = hx + (k_ - 2) * r * 0.32; pts = []
        for i in range(10):
            u = i / 9.0; pts.append((bx + math.sin(t * 2.4 + k_ * 1.3 + u * 3) * r * 0.35 * u + (k_ - 2) * r * 0.15 * u, hy + r * 0.35 + u * r * 2.1))
        for i in range(9): d.line([pts[i], pts[i + 1]], fill=(150, 112, 176, A), width=max(2, int(r * (0.26 - 0.022 * i))))
    for sg in (-1, 1):
        ex = hx + sg * r * 0.42; ey = hy - r * 0.05
        d.ellipse([ex - r * 0.26, ey - r * 0.16, ex + r * 0.26, ey + r * 0.16], fill=mix((240, 236, 210), (255, 140, 255), eyeglow) + (A,))
        d.ellipse([ex - r * 0.06, ey - r * 0.12, ex + r * 0.06, ey + r * 0.12], fill=(40, 10, 50, A))
    img.paste(lay, (0, 0), lay)
    if eyeglow > 0:
        for sg in (-1, 1): softdot(img, hx + sg * r * 0.42, hy - r * 0.05, r * 0.4, (int(200 * eyeglow), int(80 * eyeglow), int(230 * eyeglow)), 1.0, r * 0.4)
    return pos

def beast(img, x, yb, s, t, alpha=1.0, flip=False, seed=0):
    if alpha <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); A = int(255 * alpha); sg = -1 if flip else 1
    bob = abs(math.sin(t * 8 + seed)) * 6 * s; body = (34, 24, 44, A)
    for k in range(4): lx = x + (k - 1.5) * 34 * s; d.line([(lx, yb - 40 * s - bob), (lx + math.sin(t * 10 + k + seed) * 10 * s, yb)], fill=body, width=int(10 * s))
    d.ellipse([x - 80 * s, yb - 120 * s - bob, x + 80 * s, yb - 34 * s - bob], fill=body)
    for k in range(6): sx = x - 60 * s + k * 24 * s; d.polygon([(sx - 12 * s, yb - 110 * s - bob), (sx, yb - 150 * s - bob - 8 * s * math.sin(k)), (sx + 12 * s, yb - 108 * s - bob)], fill=body)
    hx = x + sg * 76 * s; d.ellipse([hx - 40 * s, yb - 130 * s - bob, hx + 40 * s, yb - 70 * s - bob], fill=body)
    for k in (-1, 1): d.ellipse([hx + sg * 14 * s + k * 12 * s - 6 * s, yb - 108 * s - bob - 5 * s, hx + sg * 14 * s + k * 12 * s + 6 * s, yb - 108 * s - bob + 5 * s], fill=(255, 220, 90, A))
    img.paste(lay, (0, 0), lay)

def poof(img, x, y, u, s=1.0):
    if not (0 < u < 1): return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); rng = random.Random(int(x))
    for k in range(10):
        a = rng.uniform(0, 6.28); r = (20 + 90 * ease(u)) * s * rng.uniform(0.6, 1.1); rr = (26 + 30 * u) * s
        d.ellipse([x + math.cos(a) * r - rr, y + math.sin(a) * r * 0.6 - rr, x + math.cos(a) * r + rr, y + math.sin(a) * r * 0.6 + rr], fill=(120, 100, 140, int(200 * (1 - u))))
    img.paste(lay, (0, 0), lay)

def bigcoin(img, x, y, r, t, tail=1.0, glow=0.6, alpha=1.0):
    if glow > 0: softdot(img, x, y, r * 1.2, (int(120 * glow * alpha), int(70 * glow * alpha), int(170 * glow * alpha)), 1.0, r * 0.7)
    if tail > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); A = int(255 * alpha * tail); pts = []
        for i in range(16):
            u = i / 15.0; pts.append((x + r * 0.8 + u * r * 2.2, y + r * 0.3 + math.sin(t * 9 - u * 6) * r * 0.35 * u))
        for i in range(15): d.line([pts[i], pts[i + 1]], fill=(206, 176, 226, A), width=max(2, int(r * (0.32 - 0.018 * i))))
        img.paste(lay, (0, 0), lay)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); A = int(255 * alpha)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(232, 186, 70, A), outline=(160, 112, 30, A), width=max(2, int(r * 0.08)))
    d.ellipse([x - r * 0.74, y - r * 0.74, x + r * 0.74, y + r * 0.74], outline=(196, 146, 46, A), width=max(2, int(r * 0.05)))
    f = F(max(10, int(r * 0.9)), bold=True); tw = d.textlength("$", font=f); d.text((x - tw / 2, y - r * 0.62), "$", font=f, fill=(150, 100, 26, A))
    for k in (-1, 1): d.ellipse([x + k * r * 0.36 - r * 0.1, y - r * 0.5, x + k * r * 0.36 + r * 0.1, y - r * 0.3], fill=(60, 20, 70, A))       # its little eyes
    img.paste(lay, (0, 0), lay)

def tag9(img, x, y, text, col=(255, 236, 200), a=1.0, size=22, bg=(20, 12, 28)):
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = F(size, bold=True); tw = d.textlength(text, font=f)
    d.rounded_rectangle([x - tw / 2 - 14, y - 8, x + tw / 2 + 14, y + size + 10], 10, fill=bg + (int(225 * a),), outline=col + (int(255 * a),), width=2)
    d.text((x - tw / 2, y), text, font=f, fill=col + (int(255 * a),)); img.paste(lay, (0, 0), lay)

# ---- settings
def room_bg():
    if "room" in _B9: return _B9["room"].copy()
    img = gradient((20, 22, 40), (36, 32, 52), "room9"); d = ImageDraw.Draw(img)
    d.rectangle([760, 70, 1180, 330], fill=(14, 18, 36)); d.rectangle([760, 70, 1180, 330], outline=(70, 66, 84), width=10); d.line([(970, 70), (970, 330)], fill=(70, 66, 84), width=8)
    rng = random.Random(3)
    for k in range(9):                                                   # city outside the window
        bx = 770 + k * 46; bh = rng.randint(60, 200); d.rectangle([bx, 330 - bh, bx + 40, 330], fill=(26, 30, 52))
        for j in range(bh // 22):
            if rng.random() < 0.5: d.rectangle([bx + 8 + (j % 2) * 16, 330 - bh + 10 + j * 20, bx + 16 + (j % 2) * 16, 330 - bh + 18 + j * 20], fill=(220, 190, 110))
    d.rectangle([0, 520, W, H], fill=(44, 36, 46))
    for k in range(10): d.line([(0, 540 + k * 20), (W, 540 + k * 20)], fill=(50, 42, 52), width=2)
    d.rectangle([60, 400, 380, 520], fill=(50, 40, 40)); d.rectangle([60, 400, 380, 412], fill=(70, 58, 56))                                   # TV stand
    d.rounded_rectangle([40, 170, 400, 400], 8, fill=(10, 10, 14), outline=(30, 30, 36), width=6)                                              # TV
    _B9["room"] = img; return img.copy()

def tv_screen(img, t, a=1.0):
    lay = Image.new("RGB", (340, 210), (30, 16, 46)); d = ImageDraw.Draw(lay)
    for k in range(7): d.arc([20 + k * 44 - 60, 10, 20 + k * 44 + 60, 330], 180, 360, fill=(70, 40, 96), width=6)
    small = Image.new("RGB", (W, H), (0, 0, 0)); 
    tmp = Image.new("RGB", (W, H), (30, 16, 46)); mind_alien(tmp, 640, 640, 520, t * 0.7)
    tmp = tmp.crop((440, 200, 840, 640)).resize((160, 176)); lay.paste(tmp, (90, 30))
    if int(t * 2) % 3 == 0: tadpole(lay, 270, 70 + 10 * math.sin(t * 3), t, 0.6, 180, 0.4)
    img.paste(lay, (50, 180)); lay2 = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(lay2).rectangle([60, 190, 380, 380], fill=(60, 30, 90)); softglow(img, lay2, 60, 0.8 * a)

def ship_bg():
    if "ship" in _B9: return _B9["ship"].copy()
    img = gradient((26, 10, 36), (62, 26, 66), "ship9"); d = ImageDraw.Draw(img)
    for k in range(9):                                                    # organic ribs
        x = -80 + k * 180; d.arc([x - 260, -120, x + 260, 900], 200, 340, fill=(74, 36, 84), width=26); d.arc([x - 260, -120, x + 260, 900], 200, 340, fill=(96, 50, 104), width=6)
    d.rectangle([0, GY, W, H], fill=(46, 20, 50))
    for k in range(14): rx = k * 100 + 30; d.ellipse([rx - 46, GY + 30 + (k % 3) * 40, rx + 46, GY + 50 + (k % 3) * 40], fill=(56, 26, 60))
    _B9["ship"] = img; return img.copy()

def pod(img, x, yb, t, who, glowc=(150, 255, 200), wake=0.0, front=True):
    d = ImageDraw.Draw(img); w, h = 150, 340
    if not front:
        d.rounded_rectangle([x - w / 2 - 12, yb - h - 12, x + w / 2 + 12, yb + 14], 70, fill=(80, 40, 90), outline=(130, 80, 140), width=6)
        d.rounded_rectangle([x - w / 2, yb - h, x + w / 2, yb], 64, fill=(30, 60, 60))
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([x - w / 2, yb - h, x + w / 2, yb], 64, fill=glowc + (54,), outline=glowc + (150,), width=3)
    for k in range(5): by = yb - ((t * 40 + k * 70) % h); ld.ellipse([x - 30 + k * 13 - 4, by - 4, x - 30 + k * 13 + 4, by + 4], outline=(220, 255, 240, 140), width=1)
    ld.line([(x - w / 2 + 22, yb - h + 50), (x - w / 2 + 22, yb - 60)], fill=(255, 255, 255, 90), width=6)
    img.paste(lay, (0, 0), lay)

def forest_bg(key="dawn"):
    if key in _B9: return _B9[key].copy()
    sky = ((80, 110, 150), (240, 180, 140)) if key == "dawn" else ((30, 20, 46), (120, 70, 90))
    img = gradient(sky[0], sky[1], "f9" + key); d = ImageDraw.Draw(img); rng = random.Random(5)
    far = mix(sky[0], (20, 30, 40), 0.5)
    for k in range(18): x = k * 80 - 20 + rng.uniform(-20, 20); th = rng.uniform(160, 260); d.polygon([(x - 50, 470), (x, 470 - th), (x + 50, 470)], fill=far)
    # the crashed ship, a purple organic hulk on the horizon
    d.polygon([(860, 470), (920, 300), (1010, 250), (1120, 290), (1200, 380), (1240, 470)], fill=(70, 40, 84)); d.polygon([(960, 330), (1010, 270), (1080, 300), (1060, 360)], fill=(96, 56, 110))
    for k in range(4): d.arc([900 + k * 60, 280 + k * 10, 1000 + k * 60, 470], 180, 300, fill=(54, 30, 66), width=8)
    gcol = (86, 104, 70) if key == "dawn" else (40, 44, 46)
    d.rectangle([0, 460, W, H], fill=gcol)
    for k in range(60): rx, ry = rng.uniform(0, W), rng.uniform(470, 710); d.line([(rx, ry), (rx + 3, ry - 10)], fill=mix(gcol, (140, 160, 100), 0.4), width=2)
    for x in (60, 1230):
        d.rectangle([x - 18, 120, x + 18, 520], fill=(50, 38, 32)); d.ellipse([x - 120, 40, x + 120, 260], fill=(40, 60, 40) if key == "dawn" else (24, 30, 26))
    _B9[key] = img; return img.copy()

def camp_bg():
    if "camp" in _B9: return _B9["camp"].copy()
    img = gradient((8, 10, 26), (34, 30, 54), "camp9"); d = ImageDraw.Draw(img); rng = random.Random(8)
    for k in range(90): sx, sy = rng.uniform(0, W), rng.uniform(0, 380); r = rng.uniform(0.8, 2.2); d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(220, 220, 240))
    d.ellipse([1080, 60, 1140, 120], fill=(230, 230, 210)); d.ellipse([1096, 54, 1150, 112], fill=(8, 10, 26))
    for k in range(20): x = k * 70 + rng.uniform(-20, 20); th = rng.uniform(140, 240); d.polygon([(x - 46, 470), (x, 470 - th), (x + 46, 470)], fill=(14, 20, 24))
    d.rectangle([0, 460, W, H], fill=(30, 30, 30))
    _B9["camp"] = img; return img.copy()

def campfire(img, x, y, t, s=1.0):
    softdot(img, x, y - 40 * s, 200 * s, (130, 70, 20), 1.0, 90)
    d = ImageDraw.Draw(img)
    for k in (-1, 1): d.line([(x - 60 * s, y + k * 4), (x + 60 * s, y - k * 10)], fill=(90, 60, 40), width=int(14 * s))
    for k in range(5):
        fx = x + (k - 2) * 18 * s; fl = 1 + 0.3 * math.sin(t * 13 + k * 2); hgt = (80 - abs(k - 2) * 18) * s * fl
        d.polygon([(fx - 16 * s, y), (fx, y - hgt), (fx + 16 * s, y)], fill=(244, 120, 30)); d.polygon([(fx - 8 * s, y), (fx, y - hgt * 0.55), (fx + 8 * s, y)], fill=(255, 220, 100))

def apt_bg():
    if "apt" in _B9: return _B9["apt"].copy()
    img = gradient((196, 170, 140), (170, 142, 116), "apt9"); d = ImageDraw.Draw(img)
    for k in range(0, W, 60): d.line([(k, 0), (k, GY)], fill=(186, 160, 132), width=2)
    d.rectangle([860, 80, 1180, 330], fill=(150, 190, 220)); d.rectangle([860, 80, 1180, 330], outline=(240, 236, 226), width=12); d.line([(1020, 80), (1020, 330)], fill=(240, 236, 226), width=8)
    for k in range(6): bx = 872 + k * 52; bh = 60 + (k * 37) % 120; d.rectangle([bx, 330 - bh, bx + 44, 318], fill=(120, 140, 170))
    d.rectangle([0, GY - 10, W, H], fill=(130, 96, 70)); d.rectangle([0, GY - 10, W, GY], fill=(110, 80, 58))
    for k in range(12): d.line([(k * 120, GY), (k * 120 - 200, H)], fill=(118, 86, 62), width=2)
    # table with a bowl of food
    d.rectangle([520, 400, 800, 418], fill=(120, 80, 50)); d.rectangle([536, 418, 552, 520], fill=(100, 66, 42)); d.rectangle([768, 418, 784, 520], fill=(100, 66, 42))
    d.pieslice([590, 350, 690, 420], 0, 180, fill=(236, 236, 240)); 
    for k in range(5): d.ellipse([600 + k * 16, 370 - (k % 2) * 8, 624 + k * 16, 392 - (k % 2) * 8], fill=[(220, 60, 50), (90, 160, 60), (240, 190, 60)][k % 3])
    d.rectangle([700, 360, 780, 400], fill=(170, 130, 80)); d.line([(700, 380), (780, 380)], fill=(140, 100, 60), width=3)               # a shipping box
    _B9["apt"] = img; return img.copy()

def ghost_worker(img, x, yb, h, kind, t, a):
    if a <= 0: return
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); base = Image.new("RGB", (W, H), (0, 0, 0))
    sw = math.sin(t * 3 + x) 
    R = (0.3, -0.9 + 0.3 * max(0, sw)) if kind == "build" else (0.22, -0.2 + 0.15 * sw) if kind == "field" else (0.25, -0.75)
    L = (-0.25, -0.75) if kind == "carry" else (-0.2, -0.3 + 0.1 * sw) if kind == "field" else (-0.2, -0.45)
    pos = cfig(base, x, yb + (h * 0.12 if kind == "field" else 0), h, (200, 210, 230), (200, 210, 230), hair=(200, 210, 230), tunic=True, legcol=(200, 210, 230), L=L, R=R, rot=-25 if kind == "field" else 0, mouth="frown")
    d = ImageDraw.Draw(base)
    if kind == "build": hx, hy = pos["R"]; d.line([(hx, hy), (hx + 10, hy - 40)], fill=(200, 210, 230), width=6); d.rectangle([hx - 4, hy - 52, hx + 26, hy - 36], fill=(200, 210, 230))
    if kind == "carry": hx, hy = pos["L"]; d.rectangle([hx - 4, hy - 60, hx + 90, hy + 4], fill=(200, 210, 230))
    if kind == "field": hx, hy = pos["R"]; d.line([(hx, hy), (hx + 30, hy + 50)], fill=(200, 210, 230), width=5)
    m = base.convert("L").point(lambda v: int(min(255, v) * 0.55 * a)); col = Image.new("RGB", (W, H), (220, 230, 255)); img.paste(col, (0, 0), m)

# ---- scenes
def s_title(t, d, p):
    img = ship_bg(); img = Image.blend(img, Image.new("RGB", (W, H), (6, 2, 10)), 0.5)
    tadpole(img, 640 + 30 * math.sin(t * 1.2), 420 + 12 * math.sin(t * 2), t, 2.2, 180 + 10 * math.sin(t), 1.0)
    a = tseg(t, 0.3, 1.1) * (1 - tseg(t, d - 0.7, d - 0.1)); title(img, "THE PARASITE PROBLEM", "a thought experiment, inspired by a video game", a, y=150, size=52)
    return img

def s_couch(t, d, p):
    c1, c2 = ev("couch", "c1"), ev("couch", "c2"); img = room_bg(); tv_screen(img, t)
    dd = ImageDraw.Draw(img)
    dd.rounded_rectangle([480, 300, 860, 470], 30, fill=(112, 60, 56))                                     # couch back
    tvk = 0.5 + 0.5 * math.sin(t * 7) * math.sin(t * 2.3)
    softdot(img, 560, 300, 160, (int(40 * tvk + 30), int(20 * tvk), int(60 * tvk + 40)), 0.6, 80)        # TV light on the face
    idea = tseg(t, c1[1] - 2.6, c1[1] - 1.4)
    pos = cfig(img, 670, 560, 300, HOOD["robe"], HOOD["skin"], hair=HOOD["hair"], tunic=True, legcol=HOOD["legcol"], L=(-0.12, -0.46), R=(0.12, -0.46), mouth="o" if idea > 0.5 and t < c2[0] else "flat",
               brow=0.0, eyes="open", cut=480)
    hairdo(img, pos["head"], 300, (64, 46, 34), long=False)
    dd = ImageDraw.Draw(img); lx, ly = pos["L"]; dd.rounded_rectangle([lx - 6, ly - 12, pos["R"][0] + 6, ly + 10], 10, fill=(40, 40, 48))         # game controller
    dd.rounded_rectangle([440, 440, 900, 540], 26, fill=(128, 70, 64)); dd.rounded_rectangle([430, 380, 490, 540], 22, fill=(120, 64, 60)); dd.rounded_rectangle([850, 380, 910, 540], 22, fill=(120, 64, 60))
    hx, hy = pos["head"]
    if idea > 0:      # an idea crawls in: a tiny tadpole wiggles into the thought bubble
        a = idea; tx = lerp(250, hx + 120, idea); ty = lerp(280, hy - 140, idea)
        if t < c2[0] + 1.0: tadpole(img, tx, ty, t, 0.5, 200, 0.6, a * (1 - tseg(t, c2[0] + 0.4, c2[0] + 1.0)))
    thought = tseg(t, c2[0] + 0.2, c2[0] + 1.2)
    if thought > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); A = int(240 * thought)
        for k, (cx, cy, r) in enumerate(((hx + 60, hy - 70, 10), (hx + 90, hy - 110, 16))): ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(246, 240, 250, A))
        ld.rounded_rectangle([700, 30, 1240, 300], 60, fill=(246, 240, 250, A), outline=(120, 90, 150, A), width=4); img.paste(lay, (0, 0), lay)
        sub = Image.new("RGB", (540, 270), (246, 240, 250)); 
        tmp = Image.new("RGB", (W, H), (246, 240, 250)); mind_alien(tmp, 640, 600, 420, t)
        for k, fn in enumerate((knight, ranger)):
            fn(tmp, 360 + k * 560, 600, 330, "o", eyes="open")
        u = tseg(t, c2[0] + 3.5, c2[0] + 7.0)
        if u > 0:
            for k in range(2):
                hpx = 360 + k * 560; tadpole(tmp, lerp(700, hpx, u), lerp(300, 395, u) - 60 * math.sin(u * math.pi), t, 1.4, 0 if k else 180, 0.8, 1.0 - tseg(u, 0.9, 1.0))
            if u >= 1:
                for k in range(2): softdot(tmp, 360 + k * 560, 390, 40, (120, 60, 170), 1.2, 30)
        tmp = tmp.crop((140, 140, 1140, 640)).resize((520, 260))
        m = Image.new("L", (520, 260), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 519, 259], 54, fill=int(255 * thought)); img.paste(tmp, (710, 35), m)
        if t > c2[1] - 4.0: hlabel(300, 60, "more mind flayers?", 34, (255, 210, 255), tseg(t, c2[1] - 4.0, c2[1] - 3.2))
    return img

def s_ship(t, d, p):
    m1, im, s1 = [ev("ship", k) for k in ("m1", "implant", "s1")]; img = ship_bg()
    xs = (290, 990)
    for x in xs: pod(img, x, GY, t, None, front=False)
    hit = tseg(t, im[0] + 1.1, im[0] + 1.5)
    knight(img, xs[0], GY - 10, 300, "frown" if hit > 0 else "flat", eyes="closed", brow=0.5 * hit)
    ranger(img, xs[1], GY - 10, 300, "frown" if hit > 0 else "flat", eyes="closed", brow=0.5 * hit)
    for x in xs: pod(img, x, GY, t, None)
    raise_ = tseg(t, m1[0] + 0.5, m1[0] + 1.5)
    apos = mind_alien(img, 640, GY + 40, 380, t, L=(-0.2, -0.42), R=(0.2 + 0.1 * raise_, -0.42 - 0.5 * raise_), eyeglow=tseg(t, s1[1] - 4, s1[1] - 3))
    rx, ry = apos["R"]
    fly = tseg(t, im[0], im[0] + 1.3)
    if t < im[0]:
        if raise_ > 0: tadpole(img, rx, ry - 30, t, 1.0, 270 + 20 * math.sin(t * 3), 1.0, raise_)
    elif fly < 1:
        for k, x in enumerate(xs):
            tx = lerp(rx, x, fly); ty = lerp(ry - 30, GY - 10 - 300 * 0.9, fly) - 80 * math.sin(fly * math.pi); tadpole(img, tx, ty, t, 1.0, 180 if k == 0 else 0, 1.0)
    if t > im[0] + 1.1:
        flash = 1 - tseg(t, im[0] + 1.2, im[0] + 2.4)
        for x in xs: brainglow(img, (x, GY - 10 - 300 * 0.88), 300, t, 0.6 + 0.8 * flash)
    if t > s1[0] + 3.0:
        def _stamp(im_):
            a = tseg(t, s1[0] + 3.0, s1[0] + 3.3); sc = 1 + 0.6 * (1 - a)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); f = F(int(54 * sc), bold=True); txt = "BOUNDARIES VIOLATED"; tw = ld.textlength(txt, font=f)
            ld.rounded_rectangle([640 - tw / 2 - 26, 46, 640 + tw / 2 + 26, 46 + 54 * sc + 34], 12, outline=(230, 60, 70, int(255 * a)), width=6)
            ld.text((640 - tw / 2, 60), txt, font=f, fill=(240, 70, 80, int(255 * a))); lay = lay.rotate(-4, center=(640, 90)); im_.paste(lay, (0, 0), lay)
        HUD(_stamp)
    return img

def wake_pose(t):
    w1, r1, k1, r2, lp = [ev("wake", k) for k in ("w1", "r1", "k1", "r2", "leap")]
    rise = tseg(t, w1[0] + 3.0, w1[0] + 5.5)
    return w1, r1, k1, r2, lp, rise

def leap_state(u):
    """ranger mid-leap: u in 0..1 over the jump"""
    x = lerp(900, 640, u); lift = math.sin(min(u, 1.0) * math.pi * 0.9) * 150
    return x, lift

def s_wake(t, d, p):
    w1, r1, k1, r2, lp, rise = wake_pose(t); img = forest_bg("dawn")
    for k in range(6):                                                    # smoking wreckage
        u = (t * 0.25 + k / 6) % 1; ImageDraw.Draw(img).ellipse([1030 + k * 10 - 20 - 40 * u, 250 - 220 * u - 20 - 30 * u, 1030 + k * 10 + 20 + 40 * u, 250 - 220 * u + 20 + 30 * u], fill=mix((120, 100, 120), (200, 170, 160), u))
    kr = 90 * (1 - rise); rr = -90 * (1 - rise)
    hands_up = tseg(t, k1[0] - 0.2, k1[0] + 0.4)
    kp = knight(img, 400, GY, 300, "o" if hands_up > 0.5 else ("frown" if rise >= 1 else "flat"), L=(-0.2 - 0.12 * hands_up, -0.42 - 0.5 * hands_up), R=(0.2 + 0.12 * hands_up, -0.42 - 0.5 * hands_up),
                rot=kr, eyes="closed" if rise < 0.3 else "open", brow=0.6 if rise >= 1 and hands_up < 0.5 else 0.0)
    draw = tseg(t, r1[0] + 0.5, r1[0] + 1.5); crouch = tseg(t, r2[0], r2[1] - 0.2); jump = tseg(t, lp[0], lp[1] + 0.05)
    x, lift = leap_state(jump * 0.5)
    sw = None
    if rise >= 1: sw = lerp(150, 20, draw) if jump <= 0 else lerp(20, -40, jump)
    rp = ranger(img, x, GY - lift + 20 * crouch * (1 - jump), 300, "frown" if t < r2[0] else "shout", L=(-0.2, -0.42 - 0.3 * jump), R=(0.22 - 0.1 * draw, -0.42 - 0.3 * draw - 0.25 * jump),
                rot=rr, sw=sw, eyes="closed" if rise < 0.3 else "open", brow=0.9 if rise >= 1 else 0.0)
    if rise >= 1:
        label(img, 400, GY + 6, "THE KNIGHT", 18, (255, 220, 200), tseg(t, w1[0] + 6, w1[0] + 7) * (1 - tseg(t, r1[0], r1[0] + 1)))
        label(img, 880, GY + 6, "THE RANGER", 18, (220, 255, 210), tseg(t, w1[0] + 6, w1[0] + 7) * (1 - tseg(t, r1[0], r1[0] + 1)))
        g = tseg(t, w1[0] + 7.5, w1[0] + 8.5)
        brainglow(img, kp["head"], 300, t, 0.6 * g); brainglow(img, rp["head"], 300, t, 0.6 * g)
    if t > lp[0]: img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.0)
    return img

def s_freeze(t, d, p):
    st, p1, f1, f2 = [ev("freeze", k) for k in ("stop", "p1", "f1", "f2")]; img = forest_bg("dawn")
    fz = tseg(t, 0.0, 0.5)
    x, lift = leap_state(0.5 + 0.12 * tseg(t, 0, 0.25))
    down = tseg(t, f1[0] + 2.0, f1[0] + 4.0); lift = lift * (1 - down)
    trem = math.sin(t * 40) * 3 * (1 - tseg(t, f1[1], f1[1] + 1))
    lower = tseg(t, f2[0] + 1.0, f2[0] + 3.0)
    kp = knight(img, 400, GY, 300, "o", L=(-0.32, -0.92), R=(0.32, -0.92), eyes="open")
    rp = ranger(img, x + trem, GY - lift, 300, "shout" if t < f1[0] else "o", L=(-0.2, -0.72 + 0.3 * lower), R=(0.12 + 0.1 * lower, -0.72 + 0.3 * lower), sw=lerp(-40, 130, lower), eyes="open", brow=0.9 * (1 - lower))
    k = 0.6 + 0.6 * fz
    brainglow(img, kp["head"], 300, t, k); brainglow(img, rp["head"], 300, t, k)
    link(img, (kp["head"][0], kp["head"][1] - 20), (rp["head"][0], rp["head"][1] - 20), t, fz * (1 - 0.5 * tseg(t, f2[0], f2[0] + 2)))
    if fz > 0 and t < f1[0] + 4:                                          # frozen moment: everything tinted violet
        tint = Image.new("RGB", (W, H), (90, 40, 140)); img = Image.blend(img, tint, 0.22 * fz * (1 - tseg(t, f1[0] + 2, f1[0] + 4)))
    if p1[0] - 0.1 < t < p1[1] + 1.0: hlabel(640, 40, "NOT THIS ONE.", 56, (220, 170, 255), tseg(t, p1[0], p1[0] + 0.4) * (1 - tseg(t, p1[1] + 0.4, p1[1] + 1.0)))
    def _cards(im):
        for i, (txt, col, t0) in enumerate((("A DEATH, PREVENTED", (150, 240, 170), f2[0] + 2.2), ("REASON: SELFISH", (255, 150, 150), f2[0] + 4.3), ("GOAL: MORE MIND FLAYERS", (220, 170, 255), f2[0] + 8.0))):
            a = tseg(t, t0, t0 + 0.5) * (1 - tseg(t, d - 1.0, d - 0.3)); tag9(im, 960, 50 + i * 62, txt, col, a, 24)
    HUD(_cards)
    return img

def s_boost(t, d, p):
    b1, p2, b2 = [ev("boost", k) for k in ("b1", "p2", "b2")]; img = forest_bg("dusk")
    aura = 0.4 + 0.4 * tseg(t, b1[0] + 6, b1[0] + 9) + 0.4 * (1 - tseg(t, p2[1], p2[1] + 2)) * tseg(t, p2[0], p2[0] + 0.5)
    fight = t > b2[0]
    swing = lambda ph: 0.5 + 0.5 * math.sin(t * 6 + ph) if fight else 0.0
    sk, sr = swing(0), swing(2.2)
    # shadow beasts closing in, then poofing as the two cut through them
    beasts = [(-220, 0.0, False), (-140, 1.6, False), (1500, 0.6, True), (1420, 2.4, True), (-300, 3.4, False), (1560, 4.4, True)]
    for i, (sx, delay, fl) in enumerate(beasts):
        app = tseg(t, 2.0 + delay * 1.6, 6.0 + delay * 1.6)
        tx = 200 if not fl else 1080
        bx = lerp(sx, tx + (i % 2) * (60 if fl else -60), app)
        dieT = b2[0] + 0.6 + i * 1.1
        if t < dieT: beast(img, bx, GY + 10, 0.8, t, 1.0, flip=fl, seed=i)
        else: poof(img, bx, GY - 50, tseg(t, dieT, dieT + 0.8), 0.9)
    kp = knight(img, 520, GY, 300, "shout" if fight and sk > 0.6 else "frown", L=(-0.2, -0.42), R=(-0.3 + 0.1 * sk, -0.85 + 0.4 * sk), sw=lerp(-70, -150, sk) if fight else -40, aura=aura * 0.8, brow=0.6)
    rp = ranger(img, 760, GY, 300, "shout" if fight and sr > 0.6 else "frown", L=(-0.2, -0.42), R=(0.3 - 0.1 * sr, -0.85 + 0.4 * sr), sw=lerp(70, 150, sr) if fight else 40, aura=aura * 0.8, brow=0.6)
    for pp in (kp, rp): brainglow(img, pp["head"], 300, t, 0.7 + 0.5 * aura)
    if p2[0] < t < p2[1] + 1.5:
        img = Image.blend(img, Image.new("RGB", (W, H), (70, 20, 100)), 0.25 * tseg(t, p2[0], p2[0] + 0.4) * (1 - tseg(t, p2[1] + 0.5, p2[1] + 1.5)))
        hlabel(640, 46, "WE NEED YOU RIPE.", 52, (220, 170, 255), tseg(t, p2[1] - 1.2, p2[1] - 0.8) * (1 - tseg(t, p2[1] + 0.5, p2[1] + 1.5)))
    def _stats(im):
        a = tseg(t, b1[0] + 7.6, b1[0] + 8.4) * (1 - tseg(t, p2[0] - 0.6, p2[0]))
        a2 = tseg(t, b2[0] + 4.0, b2[0] + 4.6) * (1 - tseg(t, d - 1, d - 0.3))
        for (aa, rows) in ((a, (("STRENGTH", 0.92, (255, 190, 120)), ("SPEED", 0.86, (150, 220, 255)))), (a2, (("STRENGTH", 0.95, (255, 190, 120)), ("VIOLENCE TOWARD EACH OTHER", 0.08, (255, 120, 120))))):
            if aa <= 0: continue
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); ld.rounded_rectangle([380, 30, 900, 170], 14, fill=(16, 8, 26, int(225 * aa)), outline=(190, 120, 255, int(255 * aa)), width=3)
            for i, (nm, v, col) in enumerate(rows):
                ld.rectangle([400, 86 + i * 50, 880, 104 + i * 50], fill=(50, 40, 60, int(255 * aa))); ld.rectangle([400, 86 + i * 50, 400 + 480 * v * aa, 104 + i * 50], fill=col + (int(255 * aa),))
            im.paste(lay, (0, 0), lay)
            for i, (nm, v, col) in enumerate(rows): label(im, 640, 56 + i * 50, nm, 20, col, aa)
    HUD(_stats)
    return img

def s_scales(t, d, p):
    q1, q2, q3 = [ev("scales", k) for k in ("q1", "q2", "q3")]; img = gradient((24, 16, 34), (54, 38, 62), "sc9")
    good = [("THEY SURVIVED", q1[0] + 0.5), ("NOBODY KILLED", q1[0] + 4.5), ("STRONGER", q1[0] + 8.5)]
    tilt = 0.0
    for nm, t0 in good: tilt -= 4.0 * tseg(t, t0, t0 + 0.8)
    bad_in = tseg(t, q1[0] + 9.5, q1[0] + 10.5)
    tilt += 10.0 * bad_in + 12.0 * tseg(t, q3[0] + 0.8, q3[0] + 2.5)
    tilt += 1.5 * math.sin(t * 2) * (1 - tseg(t, q3[0], q3[0] + 2))
    d_ = ImageDraw.Draw(img); cx, cy = 640, 210
    d_.polygon([(cx - 70, 500), (cx + 70, 500), (cx + 14, cy), (cx - 14, cy)], fill=(150, 120, 70)); d_.rectangle([cx - 120, 494, cx + 120, 512], fill=(130, 100, 60))
    a = -math.radians(tilt); L_ = 330
    lx, ly = cx - L_ * math.cos(a), cy - L_ * math.sin(a); rx, ry = cx + L_ * math.cos(a), cy + L_ * math.sin(a)
    d_.line([(lx, ly), (rx, ry)], fill=(200, 160, 80), width=12); d_.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(220, 180, 90))
    for (px, py) in ((lx, ly), (rx, ry)):
        d_.line([(px, py), (px - 100, py + 170)], fill=(170, 140, 80), width=3); d_.line([(px, py), (px + 100, py + 170)], fill=(170, 140, 80), width=3)
        d_.pieslice([px - 130, py + 130, px + 130, py + 210], 0, 180, fill=(190, 150, 70))
    # the right pan: what came out of it; the left: the violation
    for i, (nm, t0) in enumerate(good): tag9(img, rx, ry + 120 - i * 46, nm, (150, 240, 170), tseg(t, t0, t0 + 0.6), 20)
    if bad_in > 0:
        mind_alien(img, lx - 30, ly + 168, 190, t, alpha=bad_in); tadpole(img, lx + 70, ly + 120, t, 0.9, 200, 0.8, bad_in)
        tag9(img, lx, ly - 64 + 0 * bad_in, "THE VIOLATION", (255, 140, 140), bad_in, 22)
    if q2[0] < t < q3[0] + 1.0: hlabel(640, 40, "JUSTIFIED?", 60, (255, 236, 200), tseg(t, q2[0] + 0.3, q2[0] + 0.9) * (1 - tseg(t, q3[0] + 0.3, q3[0] + 1.0)))
    if t > q3[0] + 0.3:
        hlabel(640, 34, "NO.", 66, (255, 140, 140), tseg(t, q3[0] + 0.3, q3[0] + 0.7))
        hlabel(640, 114, "A benefit afterward doesn't excuse the violation.", 28, (255, 236, 220), tseg(t, q3[0] + 4.5, q3[0] + 5.3))
    return img

def s_camp(t, d, p):
    a1, k2, r3 = [ev("camp", k) for k in ("a1", "k2", "r3")]; img = camp_bg()
    campfire(img, 640, GY - 10, t, 1.0)
    flex = tseg(t, r3[0] + 0.8, r3[0] + 1.4)
    kp = knight(img, 400, GY, 290, "flat" if not (k2[0] <= t <= k2[1]) else "shout", L=(-0.2, -0.42), R=(0.3, -0.62) if k2[0] - 0.3 <= t <= k2[1] + 0.5 else (0.2, -0.42), brow=0.4)
    rp = ranger(img, 880, GY, 290, "smile" if t > r3[0] + 0.6 else "flat", L=(-0.2, -0.42), R=(0.26 + 0.06 * flex, -0.42 - 0.4 * flex))
    for pp in (kp, rp): brainglow(img, pp["head"], 290, t, 0.55)
    if flex > 0: softdot(img, rp["R"][0], rp["R"][1], 22 + 6 * math.sin(t * 8), (150, 70, 230), 1.6, 18)
    def _plan(im):
        a = tseg(t, a1[0] + 3.4, a1[0] + 4.0); b = tseg(t, a1[0] + 5.8, a1[0] + 6.4)
        tag9(im, 380, 50, "GOAL: GET IT OUT", (255, 236, 200), a, 26); tag9(im, 900, 50, "MEANWHILE: USE IT", (220, 170, 255), b, 26)
    HUD(_plan)
    if k2[0] <= t <= k2[1] + 0.6: bubble(img, 400, 140, "We find a cure.", 24, 1.0, tail=(410, 200))
    if r3[0] <= t <= r3[1] + 1.0: bubble(img, 880, 140, "...not before the next fight.", 24, 1.0, tail=(870, 200))
    return img

def s_money(t, d, p):
    o1, o2, o3 = [ev("money", k) for k in ("o1", "o2", "o3")]; img = apt_bg()
    ga = tseg(t, o2[0] + 2.0, o2[0] + 3.5) * (1 - 0.4 * tseg(t, o3[0] + 1, o3[0] + 3))
    ghost_worker(img, 150, 470, 230, "build", t, ga); ghost_worker(img, 300, 476, 220, "field", t, tseg(t, o2[0] + 3.5, o2[0] + 5)); ghost_worker(img, 1200, 470, 230, "carry", t, tseg(t, o2[0] + 5.0, o2[0] + 6.5))
    pos = cfig(img, 920, GY + 30, 330, HOOD["robe"], HOOD["skin"], hair=HOOD["hair"], tunic=True, legcol=HOOD["legcol"], L=(-0.2, -0.42), R=(-0.05, -0.6) if t > o1[0] + 0.5 else (0.2, -0.42),
               mouth="frown" if t > o2[0] else "flat", brow=0.3)
    hairdo(img, pos["head"], 330, (64, 46, 34), long=False)
    ca = tseg(t, o1[0] + 0.4, o1[0] + 1.2)
    if ca > 0:
        hx, hy = pos["R"]; bigcoin(img, hx - 50, hy - 40 + 6 * math.sin(t * 2), 38, t, tail=tseg(t, o1[0] + 1.2, o1[0] + 2.0), glow=0.6, alpha=ca)
        label(img, hx - 60, hy - 170, "the money system", 22, (90, 40, 110), tseg(t, o1[0] + 1.4, o1[0] + 2.0) * (1 - tseg(t, o2[0] + 1, o2[0] + 2)))
    def _tags(im):
        tag9(im, 220, 150, "under penalty of starvation", (220, 230, 255), tseg(t, o2[0] + 6.6, o2[0] + 7.2) * (1 - tseg(t, o3[0], o3[0] + 0.6)), 22, bg=(30, 34, 60))
        tag9(im, 1120, 360, "or homelessness", (220, 230, 255), tseg(t, o2[0] + 8.8, o2[0] + 9.4) * (1 - tseg(t, o3[0], o3[0] + 0.6)), 22, bg=(30, 34, 60))
        tag9(im, 330, 60, "the walls: built by whom?", (255, 236, 200), tseg(t, o3[0] + 2.4, o3[0] + 3.0), 22)
        tag9(im, 640, 300, "the food: grown by whom?", (255, 236, 200), tseg(t, o3[0] + 5.6, o3[0] + 6.2), 22)
        tag9(im, 740, 440, "shipped by whom?", (255, 236, 200), tseg(t, o3[0] + 7.4, o3[0] + 8.0), 20)
    HUD(_tags)
    return img

def s_end(t, d, p):
    e1, e2, e3 = [ev("end", k) for k in ("e1", "e2", "e3")]; img = camp_bg()
    softdot(img, 640, 380, 360, (40, 26, 60), 1.0, 120)
    side = tseg(t, e1[0] + 0.5, e1[0] + 2.0)
    kp = knight(img, 210, GY, 270, "flat", alpha=side); rp = ranger(img, 1070, GY, 270, "flat", alpha=side)
    for pp in (kp, rp): brainglow(img, pp["head"], 270, t, 0.5 * side)
    det = tseg(t, e2[0] + 2.0, e2[1])
    pos = cfig(img, 640, GY + 20, 330, HOOD["robe"], HOOD["skin"], hair=HOOD["hair"], tunic=True, legcol=HOOD["legcol"], L=(-0.2, -0.42), R=(0.25 + 0.15 * det, -0.62 - 0.1 * det),
               mouth="flat" if t < e3[0] else "smile", brow=0.0)
    hairdo(img, pos["head"], 330, (64, 46, 34), long=False)
    hx, hy = pos["head"]
    # the coin parasite, clinging near the head, slowly being pulled away
    cx = lerp(hx + 46, pos["R"][0] + 70, det); cy = lerp(hy - 30, pos["R"][1] - 50, det)
    if det < 1 or True: bigcoin(img, cx, cy, 30, t, tail=1.0, glow=0.5 * (1 - 0.5 * det))
    if det > 0: link(img, (hx + 10, hy - 20), (cx - 20, cy), t, 0.5 * (1 - det))
    lab = tseg(t, e1[0] + 4.0, e1[0] + 5.0) * (1 - tseg(t, e2[0], e2[0] + 1))
    label(img, 640, GY + 0, "keeps me fed  -  keeps a roof over my head  -  still a violation", 20, (230, 220, 255), lab)
    if t > e3[0]:
        hlabel(640, 46, "The parasite kept them alive.", 42, (255, 236, 210), tseg(t, e3[0] + 0.1, e3[0] + 0.8))
        hlabel(640, 104, "It still has to come out.", 42, (220, 170, 255), tseg(t, e3[0] + 2.0, e3[0] + 2.7))
    fade = tseg(t, d - 2.2, d - 0.2)
    if fade > 0: img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), fade)
    return img

SCENE_FN = {"title": s_title, "couch": s_couch, "ship": s_ship, "wake": s_wake, "freeze": s_freeze, "boost": s_boost, "scales": s_scales, "camp": s_camp, "money": s_money, "end": s_end}
CAMK = {"couch": [(0, 640, 360, 1.0), (("c2", 0.0), 640, 360, 1.0), (("c2", 3.0), 900, 300, 1.25), ("end", 960, 260, 1.4)],
        "ship": [(0, 640, 340, 1.05), ("end", 640, 330, 1.15)],
        "wake": [(0, 640, 360, 1.0), (("leap", 0.0), 640, 360, 1.0), ("end", 660, 330, 1.12)],
        "freeze": [(0, 660, 330, 1.12), (("f1", 2.0), 660, 330, 1.12), ("end", 640, 360, 1.0)],
        "boost": [(0, 640, 360, 1.0), ("end", 640, 340, 1.1)],
        "scales": [(0, 640, 360, 1.0), ("end", 640, 340, 1.06)],
        "camp": [(0, 640, 360, 1.08), ("end", 640, 340, 1.0)],
        "money": [(0, 640, 360, 1.0), ("end", 700, 330, 1.08)],
        "end": [(0, 640, 360, 1.0), ("end", 640, 330, 1.1)]}
CONT_IN = {"freeze"}
CONT_OUT = {"wake"}
VSH = {}
