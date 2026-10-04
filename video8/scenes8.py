# ================================================================= The Terror of the Cube
GYV = 600
TUN = [(150, 122, 86), (110, 128, 92), (132, 110, 126), (156, 138, 96), (104, 120, 150), (166, 108, 88), (120, 118, 108)]
PANTS = [(70, 58, 52), (58, 62, 74), (84, 70, 56)]
_B8 = {}

# ---- props
def torch(img, x, y, t, s=1.0, lit=1.0, glow=True):
    if glow:
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(lay).ellipse([x - 80 * s, y - 150 * s, x + 90 * s, y + 10 * s], fill=(int(130 * lit), int(70 * lit), 16)); softglow(img, lay, 30, 1.0)
    d = ImageDraw.Draw(img); d.line([(x, y + 10 * s), (x + 6 * s, y - 62 * s)], fill=(98, 70, 44), width=max(3, int(7 * s)))
    fl = (1 + 0.25 * math.sin(t * 14 + x)) * lit; cx = x + 6 * s; cy = y - 62 * s
    d.polygon([(cx - 15 * s, cy), (cx - 8 * s, cy - 30 * s * fl), (cx, cy - 56 * s * fl), (cx + 8 * s, cy - 30 * s * fl), (cx + 15 * s, cy)], fill=(244, 120, 30))
    d.polygon([(cx - 8 * s, cy), (cx, cy - 36 * s * fl), (cx + 8 * s, cy)], fill=(255, 214, 90))

def pitchfork(img, x, y, ang=0.0, s=1.0):
    d = ImageDraw.Draw(img); a = math.radians(ang); dx, dy = math.sin(a), -math.cos(a)
    p0 = (x - dx * 40 * s, y - dy * 40 * s); p1 = (x + dx * 110 * s, y + dy * 110 * s)
    d.line([p0, p1], fill=(110, 80, 52), width=max(3, int(6 * s)))
    nx, ny = -dy, dx
    d.line([(p1[0] + nx * 16 * s, p1[1] + ny * 16 * s), (p1[0] - nx * 16 * s, p1[1] - ny * 16 * s)], fill=(150, 154, 166), width=max(3, int(5 * s)))
    for k in (-1, 0, 1): d.line([(p1[0] + nx * 16 * s * k, p1[1] + ny * 16 * s * k), (p1[0] + nx * 16 * s * k + dx * 34 * s, p1[1] + ny * 16 * s * k + dy * 34 * s)], fill=(170, 174, 188), width=max(3, int(4 * s)))

def villager(img, x, yb, h, seed, mouth="shout", brow=0.8, L=None, R=None, prop=None, t=0.0, alpha=1.0, flip=False, rot=0.0, eyes="open", sweat=False):
    rng = random.Random(seed); robe = rng.choice(TUN); legs = rng.choice(PANTS); skin = rng.choice(SKIN)
    pos = cfig(img, x, yb, h, robe, skin, hair=rng.choice([(70, 50, 36), (120, 90, 60), (160, 150, 140), (40, 34, 30)]), beard=rng.random() < 0.45, hood=rng.random() < 0.3, sash=(86, 62, 44), tunic=True, legcol=legs,
               mouth=mouth, brow=brow, L=L, R=R, alpha=alpha, rot=rot, eyes=eyes)
    if prop == "torch": torch(img, pos["R"][0], pos["R"][1], t, h / 230.0)
    elif prop == "fork": pitchfork(img, pos["R"][0], pos["R"][1], 8 * math.sin(t * 5 + seed), h / 230.0)
    elif prop == "fork_down": pitchfork(img, pos["R"][0], pos["R"][1], 200, h / 230.0)
    if sweat:
        hx, hy = pos["head"]
        for k in range(2): u = (t * 1.2 + k / 2) % 1; d = ImageDraw.Draw(img); sx = hx + (k * 2 - 1) * h * 0.08; sy = hy - h * 0.02 + u * h * 0.12; d.polygon([(sx, sy - 9), (sx - 5, sy), (sx + 5, sy)], fill=(160, 215, 255)); d.ellipse([sx - 5, sy - 3, sx + 5, sy + 7], fill=(160, 215, 255))
    return pos

CROWD = []
def crowd_pos():
    if CROWD: return CROWD
    rng = random.Random(14)
    for yb, h, n in ((570, 200, 15), (600, 230, 13), (640, 260, 9)):
        for i in range(n):
            x = (i + 0.5) / n * (W + 60) - 30 + rng.uniform(-22, 22)
            CROWD.append(dict(x=x, yb=yb + rng.uniform(-5, 5), h=h * rng.uniform(0.94, 1.06), seed=rng.randint(0, 9999), prop="torch" if rng.random() < 0.45 else "fork", ph=rng.random() * 6.28, lead=rng.random(), side=-1 if x < 640 else 1))
    CROWD.sort(key=lambda c: c["yb"]); return CROWD

def crowd8(img, t, mode="frantic", leave=0.0, keep=(), clear=0.0, alpha=1.0):
    for c in crowd_pos():
        x, yb, h = c["x"], c["yb"], c["h"]
        if clear > 0 and abs(x - 640) < 190 * clear: continue
        a = alpha; bob = 0.0; L = None; R = None; mouth = "shout"; prop = c["prop"]; rot = 0.0; brow = 0.8; sweat = False
        if leave > 0 and c["lead"] > 0.1 and c["seed"] not in keep:
            x += c["side"] * 1400 * ease(clamp(leave * 1.6 - c["lead"] * 0.6)); a = alpha * (1 - ease(clamp(leave * 1.6 - c["lead"] * 0.6 - 0.2)))
            if x < -100 or x > W + 100: continue
        if mode == "frantic": bob = abs(math.sin(t * 9 + c["ph"])) * 0.03 * h; R = (0.26, -0.98 - 0.04 * math.sin(t * 10 + c["ph"])); L = (-0.26, -0.95 - 0.04 * math.sin(t * 9 + c["ph"] + 1))
        elif mode == "recoil": L = (-0.1, -0.88); R = (0.1, -0.88); mouth = "o"; prop = None; bob = -0.02 * h
        elif mode == "stare": R = (0.24, -0.5); L = (-0.2, -0.42); mouth = "o"; brow = 0.0; prop = "fork_down" if c["prop"] == "fork" else "torch"
        elif mode == "dejected": R = (0.24, -0.4); L = (-0.2, -0.38); mouth = "frown"; brow = 0.0; prop = "fork_down" if c["prop"] == "fork" else None; bob = -0.015 * h
        villager(img, x, yb - bob, h, c["seed"], mouth, brow, L, R, prop, t, a, rot=rot)
    return

# ---- the cube bot
def cubebot(img, x, yb, s=1.0, t=0.0, face="happy", speak=0.0, roll=0.0, alpha=1.0, tilt=0.0, flip=False, glow=0.4, fsize=None):
    w, hh = int(260 * s), int(260 * s); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); cx = w / 2; gy = hh - 8
    P = lambda ux, uy: (cx + ux * s, gy + uy * s)
    bob = math.sin(t * 3) * 1.0 * s
    gl = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl); gd.ellipse([P(-90, -170)[0], P(-90, -170)[1], P(90, -10)[0], P(90, -10)[1]], fill=(120, 240, 220, int(90 * glow))); gl = gl.filter(ImageFilter.GaussianBlur(14 * s)); lay.alpha_composite(gl); d = ImageDraw.Draw(lay)
    for sg in (-1, 1):                                    # rubber wheels
        wx, wy = P(sg * 46, -14 + bob * 0); d.ellipse([wx - 20 * s, wy - 16 * s, wx + 20 * s, wy + 16 * s], fill=(26, 26, 32)); d.ellipse([wx - 9 * s, wy - 7 * s, wx + 9 * s, wy + 7 * s], fill=(150, 154, 166))
        for k in range(3): a_ = roll * 6 + k * 2.09; d.line([(wx, wy), (wx + math.cos(a_) * 8 * s, wy + math.sin(a_) * 6 * s)], fill=(70, 74, 84), width=2)
    d.polygon([P(66, -132 + bob), P(82, -146 + bob), P(82, -40 + bob), P(66, -26 + bob)], fill=(214, 220, 232), outline=(170, 178, 196))                       # side face
    d.polygon([P(-66, -132 + bob), P(-50, -146 + bob), P(82, -146 + bob), P(66, -132 + bob)], fill=(250, 252, 255), outline=(190, 198, 212))                    # top face
    d.rounded_rectangle([P(-66, -132 + bob)[0], P(-66, -132 + bob)[1], P(66, -26 + bob)[0], P(66, -26 + bob)[1]], int(10 * s), fill=(242, 245, 250), outline=(186, 194, 210), width=3)
    d.rounded_rectangle([P(-48, -118 + bob)[0], P(-48, -118 + bob)[1], P(48, -52 + bob)[0], P(48, -52 + bob)[1]], int(8 * s), fill=(16, 22, 30), outline=(60, 70, 84), width=3)     # the LED screen
    led = (130, 255, 220); fx, fy = P(0, -85 + bob)
    blink = (int(t * 1.7) % 5 == 0 and (t * 1.7) % 1 < 0.12)
    def eyes(kind):
        for sg in (-1, 1):
            ex = fx + sg * 20 * s
            if blink or kind == "closed": d.line([(ex - 9 * s, fy - 4 * s), (ex + 9 * s, fy - 4 * s)], fill=led, width=max(3, int(4 * s)))
            elif kind == "happy": d.arc([ex - 10 * s, fy - 14 * s, ex + 10 * s, fy + 4 * s], 200, 340, fill=led, width=max(3, int(5 * s)))
            elif kind == "heart":
                hc = (255, 120, 160); d.ellipse([ex - 10 * s, fy - 14 * s, ex, fy - 3 * s], fill=hc); d.ellipse([ex, fy - 14 * s, ex + 10 * s, fy - 3 * s], fill=hc); d.polygon([(ex - 10 * s, fy - 8 * s), (ex + 10 * s, fy - 8 * s), (ex, fy + 6 * s)], fill=hc)
            else: d.ellipse([ex - 6 * s, fy - 12 * s, ex + 6 * s, fy], fill=led)
    if face in ("happy", "halo", "wink", "heart"):
        eyes("happy" if face != "heart" else "heart"); d.arc([fx - 15 * s, fy - 2 * s, fx + 15 * s, fy + 14 * s], 20, 160, fill=led, width=max(3, int(5 * s)))
        if face == "halo": d.ellipse([fx - 22 * s, fy - 40 * s, fx + 22 * s, fy - 30 * s], outline=(255, 232, 130), width=max(3, int(4 * s)))
    elif face == "scan":
        for k in range(7): d.line([(fx - 38 * s, fy - 24 * s + k * 9 * s), (fx + 38 * s, fy - 24 * s + k * 9 * s)], fill=(40, 120, 110), width=1)
        yy = fy - 24 * s + ((t * 1.4) % 1) * 56 * s; d.line([(fx - 40 * s, yy), (fx + 40 * s, yy)], fill=led, width=max(2, int(3 * s))); d.text((fx - 30 * s, fy - 2 * s), "SCANNING", font=F(max(10, int(11 * s)), mono=True), fill=led)
    elif face == "worry":
        eyes("dot"); d.line([(fx - 28 * s, fy - 20 * s), (fx - 12 * s, fy - 16 * s)], fill=led, width=3); d.line([(fx + 28 * s, fy - 20 * s), (fx + 12 * s, fy - 16 * s)], fill=led, width=3); d.arc([fx - 12 * s, fy + 2 * s, fx + 12 * s, fy + 14 * s], 200, 340, fill=led, width=4)
    # speaker + antenna
    d.rounded_rectangle([P(-18, -164 + bob)[0], P(-18, -164 + bob)[1], P(18, -146 + bob)[0], P(18, -146 + bob)[1]], int(5 * s), fill=(120, 126, 140), outline=(80, 86, 100), width=2)
    for k in range(4): d.line([P(-12 + k * 8, -161 + bob), P(-12 + k * 8, -150 + bob)], fill=(70, 76, 90), width=2)
    ax, ay = P(44, -146 + bob); d.line([(ax, ay), (ax + 6 * s, ay - 26 * s)], fill=(150, 154, 166), width=3); d.ellipse([ax + 6 * s - 6 * s, ay - 32 * s, ax + 6 * s + 6 * s, ay - 20 * s], fill=(255, 100, 130) if int(t * 3) % 2 == 0 else (200, 60, 90))
    if speak > 0:
        for k in range(3):
            u = (t * 2 + k / 3) % 1; rr = (14 + 40 * u) * s; cxs, cys = P(0, -166 + bob)
            d.arc([cxs - rr, cys - rr * 0.8 - 8 * s, cxs + rr, cys + rr * 0.8 - 8 * s], 220, 320, fill=(140, 255, 230, int(220 * (1 - u) * speak)), width=max(2, int(3 * s)))
    if flip: lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
    if tilt: lay = lay.rotate(tilt, center=(cx, gy), resample=Image.BICUBIC)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.paste(lay, (int(x - cx), int(yb - gy)), lay)
    return {"screen": (x, yb - gy + fy), "top": (x, yb - gy + P(0, -170)[1])}

# ---- settings
def castle_bg():
    if "c" in _B8: return _B8["c"].copy()
    img = gradient((10, 8, 26), (68, 44, 72), "castle"); d = ImageDraw.Draw(img); rng = random.Random(7)
    for i in range(7):
        cx = rng.uniform(0, W); cy = rng.uniform(30, 250); w = rng.uniform(260, 520); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).ellipse([cx - w / 2, cy - 30, cx + w / 2, cy + 30], fill=(28, 22, 44, 170)); img.paste(lay, (0, 0), lay)
    d = ImageDraw.Draw(img); d.ellipse([300, 70, 350, 120], fill=(220, 216, 200))
    stone = (74, 70, 90); stone_d = (58, 54, 72)
    def tower(x0, x1, y0, roof=True, rc=(70, 36, 56)):
        d.rectangle([x0, y0, x1, 480], fill=stone); d.rectangle([x0, y0, x1, y0 + 16], fill=stone_d)
        for k in range(int((x1 - x0) / 20)): d.rectangle([x0 + k * 20 + 2, y0 - 12, x0 + k * 20 + 14, y0], fill=stone)
        if roof: d.polygon([(x0 - 8, y0 - 12), ((x0 + x1) / 2, y0 - 90), (x1 + 8, y0 - 12)], fill=rc)
        for yy in range(y0 + 30, 480, 40): d.line([(x0, yy), (x1, yy)], fill=stone_d, width=2)
    d.rectangle([420, 190, 860, 480], fill=stone); d.rectangle([420, 190, 860, 206], fill=stone_d)
    for k in range(22): d.rectangle([420 + k * 20 + 2, 176, 420 + k * 20 + 14, 190], fill=stone)
    for yy in range(220, 480, 40): d.line([(420, yy), (860, yy)], fill=stone_d, width=2)
    tower(330, 430, 230); tower(850, 950, 250)
    tower(960, 1090, 70, rc=(60, 40, 70))                       # the highest tower, with the antenna
    d.line([(1025, -20), (1025, -60)], fill=(150, 154, 166), width=3)
    d.line([(1025, 0), (1025, -20)], fill=(180, 184, 196), width=5)
    d.ellipse([1004, 6, 1046, 24], outline=(200, 204, 216), width=4); d.line([(1025, 24), (1025, 48)], fill=(180, 184, 196), width=3)    # dish
    for (wx, wy) in ((470, 250), (560, 250), (720, 250), (810, 250), (480, 340), (790, 340), (990, 160), (1030, 160), (1010, 250), (1010, 340), (880, 330), (880, 400), (360, 320), (400, 320)):
        d.rounded_rectangle([wx, wy, wx + 26, wy + 40], 8, fill=(30, 90, 110)); d.rounded_rectangle([wx, wy, wx + 26, wy + 40], 8, outline=(100, 90, 80), width=3)
    d.rectangle([0, 470, W, H], fill=(48, 38, 44)); d.polygon([(560, 720), (720, 720), (680, 470), (600, 470)], fill=(78, 62, 60))
    for k in range(40): rx, ry = rng.uniform(0, W), rng.uniform(480, 700); d.ellipse([rx - 16, ry - 7, rx + 16, ry + 7], fill=(62, 50, 54))
    _B8["c"] = img; return img.copy()

def castle_gate(img, openu, t, light=0.0):
    d = ImageDraw.Draw(img); x0, x1, y0, y1 = 570, 710, 330, 475
    d.pieslice([x0 - 4, y0 - 70, x1 + 4, y0 + 70], 180, 360, fill=(36, 28, 36)); d.rectangle([x0 - 4, y0, x1 + 4, y1], fill=(36, 28, 36))
    if light > 0:
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(lay).rectangle([x0 + 8, y0 - 20, x1 - 8, y1], fill=(int(255 * light), int(240 * light), int(190 * light))); softglow(img, lay, 40, 1.4); img.paste(ImageChops.add(img, lay))
        rays(img, 640, 400, t, (255, 240, 190), n=14, length=900, strength=0.3 * light)
    d = ImageDraw.Draw(img); half = (x1 - x0) / 2
    for sg in (-1, 1):                                    # two oak door leaves swinging open
        edge = 640 + sg * half * (1 - 0.82 * openu)
        d.polygon([(640 + sg * half, y0 - (4 + 10 * openu)), (edge, y0 - 20 * openu * 0 - (0)), (edge, y1 + 2), (640 + sg * half, y1 + 2)], fill=(104, 72, 48), outline=(60, 40, 28))
        for k in range(1, 4): d.line([(640 + sg * half, y0 + k * 36), (edge, y0 + k * 36)], fill=(70, 70, 80), width=4)

def tower_bg():
    if "t" in _B8: return _B8["t"].copy()
    img = gradient((36, 34, 50), (58, 54, 70), "tower"); d = ImageDraw.Draw(img)
    for yy in range(0, 600, 40):
        for k in range(0, W, 80): off = 40 if (yy // 40) % 2 else 0; d.rectangle([k - off, yy, k - off + 80, yy + 40], outline=(48, 44, 62), width=2)
    d.pieslice([500, 60, 780, 280], 180, 360, fill=(14, 14, 30)); d.rectangle([500, 170, 780, 380], fill=(14, 14, 30)); d.rectangle([500, 170, 780, 380], outline=(100, 94, 110), width=10); d.arc([500, 60, 780, 280], 180, 360, fill=(100, 94, 110), width=10); d.line([(640, 70), (640, 380)], fill=(100, 94, 110), width=6)
    d.rectangle([0, 600, W, H], fill=(70, 62, 66)); d.rectangle([0, 590, W, 604], fill=(88, 78, 80))
    # the lever panel
    d.rounded_rectangle([250, 330, 360, 540], 12, fill=(80, 70, 62), outline=(40, 34, 30), width=5); d.rounded_rectangle([296, 360, 316, 500], 8, fill=(20, 18, 20))
    # server racks
    for k in range(3):
        x0 = 860 + k * 130; d.rounded_rectangle([x0, 250, x0 + 110, 600], 8, fill=(34, 40, 52), outline=(70, 78, 96), width=3)
        for j in range(9): d.rectangle([x0 + 8, 262 + j * 36, x0 + 102, 288 + j * 36], fill=(20, 24, 34), outline=(50, 56, 72))
    _B8["t"] = img; return img.copy()

def street_bg():
    if "s" in _B8: return _B8["s"].copy()
    img = gradient((176, 198, 220), (232, 220, 196), "street"); d = ImageDraw.Draw(img); rng = random.Random(3)
    d.polygon([(0, 470), (W, 470), (W, H), (0, H)], fill=(150, 138, 126))
    for k in range(30): d.line([(k * 60 - 100, 720), (640 + (k - 15) * 14, 470)], fill=(132, 120, 110), width=2)
    for j in range(1, 9): d.line([(0, 470 + j * j * 4), (W, 470 + j * j * 4)], fill=(136, 124, 114), width=2)
    def house(x0, x1, y0, col, roof, sign=None):
        d.rectangle([x0, y0, x1, 520], fill=col); d.polygon([(x0 - 14, y0), ((x0 + x1) / 2, y0 - 80), (x1 + 14, y0)], fill=roof)
        for k in range(1, 4): d.line([(x0, y0 + k * 40), (x1, y0 + k * 40)], fill=(96, 70, 50), width=5)
        for k in range(int((x1 - x0) / 60) + 1): d.line([(x0 + k * 60, y0), (x0 + k * 60, 520)], fill=(96, 70, 50), width=5)
        if sign: d.rectangle([x0 + 10, y0 + 12, x0 + 98, y0 + 38], fill=(250, 240, 210), outline=(96, 70, 50), width=3); d.text((x0 + 16, y0 + 14), sign, font=F(18, bold=True), fill=(70, 40, 30))
    house(20, 220, 230, (232, 214, 180), (150, 70, 60), "BAKERY"); house(250, 430, 260, (214, 200, 170), (110, 80, 70), "SMITH"); house(860, 1040, 250, (226, 210, 178), (130, 74, 64)); house(1070, 1260, 220, (212, 198, 168), (100, 80, 74))
    _B8["s"] = img; return img.copy()

def pub_bg():
    if "p" in _B8: return _B8["p"].copy()
    img = gradient((62, 40, 30), (96, 64, 44), "pub"); d = ImageDraw.Draw(img); rng = random.Random(9)
    for k in range(0, W, 70): d.line([(k, 0), (k, 560)], fill=(54, 34, 26), width=3)
    d.rectangle([0, 560, W, H], fill=(84, 58, 42))
    for k in range(14): d.line([(k * 100 - 50, 560), (k * 140 - 250, 720)], fill=(70, 46, 34), width=2)
    d.rectangle([60, 300, 700, 540], fill=(110, 74, 50), outline=(60, 38, 28), width=6)      # the bar
    for k in range(7): d.rounded_rectangle([90 + k * 88, 250, 130 + k * 88, 300], 6, fill=(190, 160, 90), outline=(120, 90, 40), width=2)
    d.rectangle([60, 120, 700, 134], fill=(80, 54, 40))
    for k in range(9): d.rounded_rectangle([90 + k * 66, 90, 120 + k * 66, 120], 5, fill=(170, 150, 100))
    for lx in (860, 1080):
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(lay).ellipse([lx - 90, 130, lx + 90, 330], fill=(120, 70, 20)); softglow(img, lay, 40, 1.0)
        d = ImageDraw.Draw(img); d.line([(lx, 0), (lx, 190)], fill=(40, 30, 28), width=3); d.rounded_rectangle([lx - 20, 190, lx + 20, 240], 6, fill=(250, 200, 100), outline=(80, 60, 40), width=3)
    d.rectangle([780, 470, 1240, 490], fill=(120, 82, 56)); d.rectangle([800, 490, 816, 600], fill=(86, 58, 40)); d.rectangle([1204, 490, 1220, 600], fill=(86, 58, 40))   # table
    _B8["p"] = img; return img.copy()

def balcony_bg(t):
    if "b" in _B8: img = _B8["b"].copy()
    else:
        img = gradient((250, 168, 120), (120, 100, 150), "balc"); d = ImageDraw.Draw(img); rng = random.Random(2)
        d.ellipse([560, 180, 700, 320], fill=(255, 226, 170))
        d.polygon([(0, 360), (W, 340), (W, H), (0, H)], fill=(96, 78, 90))
        d.polygon([(0, 480), (W, 470), (W, H), (0, H)], fill=(120, 100, 96))
        for k in range(22):
            x0 = rng.randint(0, W - 100); w = rng.randint(70, 130); y0 = rng.randint(380, 470); d.rectangle([x0, y0, x0 + w, 520], fill=(160, 130, 112)); d.polygon([(x0 - 8, y0), (x0 + w / 2, y0 - 44), (x0 + w + 8, y0)], fill=(110, 70, 74))
        d.polygon([(480, 720), (800, 720), (700, 500), (590, 500)], fill=(150, 130, 120))
        _B8["b"] = img; img = img.copy()
    return img

def lightning(img, t, a, bolts=None):
    if a <= 0: return img
    img = Image.blend(img, Image.new("RGB", (W, H), (230, 230, 255)), 0.35 * a)
    return img

def cable_glow(img, t, prog=1.0):
    """a glowing fiber-optic cable from the server racks to the window; light pulses travel along it."""
    pts = [(900, 560), (800, 580), (700, 575), (640, 520), (640, 380)]
    lay = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay); d.line(pts, fill=(0, int(150 * prog), int(170 * prog)), width=10)
    for k in range(5):
        u = ((t * 0.8 + k / 5) % 1.0) * prog; i = min(len(pts) - 2, int(u * (len(pts) - 1))); f = u * (len(pts) - 1) - i
        x = lerp(pts[i][0], pts[i + 1][0], f); y = lerp(pts[i][1], pts[i + 1][1], f); d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(180, 255, 255))
    softglow(img, lay, 14, 1.4); img.paste(ImageChops.add(img, lay.point(lambda v: int(v * 0.6))))

# ---- scenes
def s_title(t, d, p):
    img = castle_bg(); img = Image.blend(img, Image.new("RGB", (W, H), (6, 4, 14)), 0.45)
    cubes_ = cubebot(img, 640, 640, 1.2, t, "halo", glow=0.9)
    a = tseg(t, 0.4, 1.2) * (1 - tseg(t, d - 0.7, d - 0.1)); title(img, "THE TERROR OF THE CUBE", "a gentle horror story", a, y=200, size=50)
    return img

def s_castle(t, d, p):
    c1, c2 = ev("castle", "c1"), ev("castle", "c2"); img = castle_bg()
    lit = 0.5 + 0.5 * math.sin(t * 0.7)
    for k, (wx, wy) in enumerate(((470, 250), (560, 250), (720, 250), (810, 250), (990, 160), (1030, 160))):       # the servers blink in the windows
        for j in range(3):
            if int(t * 3 + k + j * 2) % 2 == 0: ImageDraw.Draw(img).rectangle([wx + 5 + j * 6, wy + 8 + (k + j) % 3 * 10, wx + 8 + j * 6, wy + 12 + (k + j) % 3 * 10], fill=(120, 255, 220))
    if int(t * 0.8) % 3 == 0 and (t * 0.8) % 1 < 0.1: img = lightning(img, t, 1.0)
    castle_gate(img, 0.0, t)
    mode = "frantic"; crowd8(img, t, mode)
    # their imagined horror: a six-foot-six, lightning-scarred Zombie Jesus with a sword of fire
    a = tseg(t, c2[0] + 1.0, c2[0] + 2.0) * (1 - tseg(t, c2[1] - 1.5, c2[1] - 0.8))
    if a > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.ellipse([380, 20, 900, 300], fill=(30, 20, 40, int(215 * a)), outline=(150, 90, 120, int(255 * a)), width=4)
        for k in range(3): ld.ellipse([420 + k * 40, 296 + k * 20 - 10, 440 + k * 40, 316 + k * 20 - 10], fill=(30, 20, 40, int(215 * a)))
        cx_ = 640; col = (208, 214, 190, int(255 * a)); skin = (146, 168, 134, int(255 * a))
        ld.polygon([(cx_ - 34, 110), (cx_ + 34, 110), (cx_ + 50, 270), (cx_ - 50, 270)], fill=col); ld.polygon([(cx_ - 50, 270), (cx_ - 34, 250), (cx_ - 20, 272), (cx_ - 4, 250), (cx_ + 12, 272), (cx_ + 30, 250), (cx_ + 50, 270)], fill=col)    # tattered robe
        ld.line([(cx_ - 30, 124), (cx_ - 86, 190)], fill=skin, width=14); ld.line([(cx_ + 30, 124), (cx_ + 80, 80)], fill=skin, width=14)
        ld.ellipse([cx_ - 24, 56, cx_ + 24, 112], fill=skin); ld.ellipse([cx_ - 28, 46, cx_ + 28, 74], fill=(60, 44, 36, int(255 * a)))
        ld.polygon([(cx_ - 10, 62), (cx_ - 2, 78), (cx_ - 8, 82), (cx_ + 2, 98)], fill=(255, 240, 120, int(255 * a)))                    # lightning scar
        for sg in (-1, 1): ld.ellipse([cx_ + sg * 10 - 5, 78, cx_ + sg * 10 + 5, 88], fill=(255, 80, 60, int(255 * a)))
        ld.line([(cx_ + 80, 80), (cx_ + 110, -10)], fill=(255, 150, 40, int(255 * a)), width=12); ld.polygon([(cx_ + 100, -10), (cx_ + 118, -50), (cx_ + 126, -10)], fill=(255, 210, 80, int(255 * a)))   # sword of fire
        img.paste(lay, (0, 0), lay); label(img, 640, 296 - 20, "6'6\"", 28, (255, 220, 180), a)
        ln = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(ln).line([(780, 50), (780, 270)], fill=(255, 220, 180, int(220 * a)), width=2); img.paste(ln, (0, 0), ln)
    return img

def s_tower(t, d, p):
    t1, sy, al = ev("tower", "t1"), ev("tower", "sync"), ev("tower", "alive"); img = tower_bg()
    flash = 0.0
    if t > al[0] - 0.2:
        flash = max(0.0, math.sin((t - al[0]) * 11)) ** 8 if t < al[1] + 1 else 0.0
    lever = tseg(t, t1[0] + 5.0, t1[0] + 6.4)
    # window: storm
    wl = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(wl).rectangle([505, 170, 775, 375], fill=(int(60 + 190 * flash), int(60 + 190 * flash), int(100 + 150 * flash)))
    img.paste(ImageChops.add(img, wl.point(lambda v: int(v * 0.5))))
    prog = tseg(t, t1[0] + 6.0, sy[1] - 0.4); dd = ImageDraw.Draw(img)
    for k in range(3):                                                  # the racks blink
        x0 = 860 + k * 130
        for j in range(9):
            for i in range(4):
                if int(t * 4 + k + j + i * 3) % 3 != 0 and (lever > 0.5): dd.rectangle([x0 + 14 + i * 10, 270 + j * 36, x0 + 20 + i * 10, 276 + j * 36], fill=(120, 255, 220) if (i + j) % 2 else (255, 200, 90))
    if lever > 0.3: cable_glow(img, t, clamp(prog + 0.2))
    # the lever
    dd = ImageDraw.Draw(img); ang = math.radians(lerp(-40, 40, ease(lever))); lx, ly = 306, 430
    dd.line([(lx, ly), (lx + math.sin(ang) * 0, ly)], fill=(0, 0, 0), width=1); dd.line([(306, 430 + 0), (306 + 40 * math.sin(ang), 430 - 76 * math.cos(ang) * 1.0)], fill=(190, 40, 40), width=10); dd.ellipse([306 + 40 * math.sin(ang) - 14, 430 - 76 * math.cos(ang) - 14, 306 + 40 * math.sin(ang) + 14, 430 - 76 * math.cos(ang) + 14], fill=(230, 60, 60))
    # you, the mad scientist
    laugh = tseg(t, al[0], al[0] + 0.4)
    Rh = (0.3 * (1 - lever) + 0.22, -0.7 - 0.0) if t < t1[0] + 5.0 else None
    pos = cfig(img, 440 + 4 * math.sin(t * 30) * laugh, 640, 300, (244, 244, 250), SKIN[0], hair=(210, 210, 222), sash=(120, 120, 130), tunic=True, legcol=(40, 40, 52), mouth="laugh" if laugh > 0.5 else "smile", brow=0.8 if laugh > 0.5 else 0.0,
               L=(-0.5 * laugh - 0.2 * (1 - laugh), -0.95 * laugh - 0.42 * (1 - laugh)), R=((0.5, -0.95) if laugh > 0.5 else ((-0.32 + 0.0, -0.78 + 0.1 * (1 - lever)) if t < t1[0] + 7.0 else (0.2, -0.42))), eyes="open")
    hx, hy = pos["head"]; dd = ImageDraw.Draw(img); dd.ellipse([hx - 24, hy - 38, hx - 4, hy - 20], outline=(60, 60, 70), width=4, fill=(120, 190, 220)); dd.ellipse([hx + 4, hy - 38, hx + 24, hy - 20], outline=(60, 60, 70), width=4, fill=(120, 190, 220)); dd.line([(hx - 40, hy - 30), (hx + 40, hx * 0 + hy - 30)], fill=(60, 60, 70), width=4)   # goggles
    if flash > 0.4: img = lightning(img, t, flash)
    def _hud(im):
        a = tseg(t, t1[0] + 5.6, t1[0] + 6.2) * (1 - tseg(t, al[0] + 0.2, al[0] + 0.8))
        if a > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd2 = ImageDraw.Draw(lay); dd2.rounded_rectangle([380, 70, 900, 150], 14, fill=(8, 20, 30, int(230 * a)), outline=(100, 240, 220, int(255 * a)), width=3)
            dd2.rectangle([400, 112, 400 + 480 * clamp(prog), 134], fill=(100, 240, 220, int(255 * a))); im.paste(lay, (0, 0), lay)
            label(im, 640, 80, "FIBER-OPTIC UPLINK  -  LOGIC SYNC  %d%%" % int(100 * clamp(prog)), 22, (150, 250, 235), a)
    HUD(_hud)
    if al[0] <= t <= al[1] + 0.5: hlabel(640, 40, "IT'S ALIVE!", 54, (255, 240, 200), 1.0)
    return img

def s_gates(t, d, p):
    g1, op, g2, g3 = [ev("gates", k) for k in ("g1", "open", "g2", "g3")]; img = castle_bg()
    if int(t * 0.5) % 3 == 0 and (t * 0.5) % 1 < 0.1: img = lightning(img, t, 0.6)
    openu = tseg(t, op[0] + 0.1, op[1] - 0.2); light = openu * (1 - tseg(t, g2[0] + 1.2, g2[0] + 3.2)) * 0.9
    castle_gate(img, openu, t, light)
    surge = tseg(t, 0.4, g1[0] + 4.0)
    mode = "recoil" if (t > op[0] + 0.5 and t < g2[0] + 3.5) else "frantic"
    crowd8(img, t, mode, clear=0.9 if t > op[0] else 0.0)
    roll = tseg(t, g2[0] + 4.0, g3[1] - 1.0)
    if t > g2[0] + 3.5:
        bx = lerp(640, 640 + 20, roll); by = lerp(486, 640, roll); sc = lerp(0.45, 1.1, roll)
        cubebot(img, bx, by, sc, t, "happy", roll=t * 3 * (1 if roll < 1 else 0), glow=0.5)
    return img

def s_bot1(t, d, p):
    b1 = ev("bot1", "b1"); img = castle_bg(); castle_gate(img, 1.0, t, 0.0)
    for k in range(5): villager(img, 100 + k * 150 if k < 3 else 880 + (k - 3) * 170, 640, 250, 40 + k, "o", 0.0, (-0.2, -0.42), (0.24, -0.5), "fork_down" if k % 2 else "torch", t)
    lead = villager(img, 520, 650, 340, 77, "o", 0.0, (-0.2, -0.42), (0.26, -0.5), "fork_down", t, sweat=True)
    sp = 1.0 if b1[0] <= t <= b1[1] else 0.0
    face = "heart" if (b1[0] + 8.6 < t < b1[0] + 10.6) else ("scan" if (b1[0] + 4.4 < t < b1[0] + 8.0) else "halo" if t > b1[1] - 3 else "happy")
    bpos = cubebot(img, 760, 640, 1.5, t, face, speak=sp, glow=0.7)
    def _bpm(im):
        a = tseg(t, b1[0] + 4.2, b1[0] + 5.0) * (1 - tseg(t, b1[0] + 9.0, b1[0] + 10.0))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([80, 60, 520, 200], 14, fill=(8, 20, 30, int(230 * a)), outline=(100, 240, 220, int(255 * a)), width=3); im.paste(lay, (0, 0), lay)
        label(im, 300, 70, "HEART RATE", 20, (150, 250, 235), a); label(im, 440, 100, "%d" % (136 + int(8 * math.sin(t * 6))), 52, (255, 110, 110), a)
        pts = []
        for i in range(90):
            u = (i / 90.0) * 3 + t * 3.2; ph = u % 1.0; y = -34 * math.exp(-((ph - 0.3) / 0.025) ** 2) + 10 * math.exp(-((ph - 0.36) / 0.03) ** 2); pts.append((100 + i * 3.2, 150 - y))
        ImageDraw.Draw(im).line(pts, fill=(140, 255, 170), width=2)
    HUD(_bpm)
    if t > b1[0] + 9.8 and t < b1[1] + 0.5: HUD(lambda im: label(im, 300, 100, "PITCHFORK = lack of agency?", 24, (255, 226, 160), tseg(t, b1[0] + 9.8, b1[0] + 10.4) * (1 - tseg(t, b1[1], b1[1] + 0.5))))
    return img

def s_disappoint(t, d, p):
    d1, l1, v1, d2 = [ev("disappoint", k) for k in ("d1", "l1", "v1", "d2")]; img = castle_bg(); castle_gate(img, 1.0, t, 0.0)
    leave = tseg(t, d2[0] - 6.0, d2[1] - 0.5); keep = {c["seed"] for c in crowd_pos() if c["lead"] < 0.1}
    mode = "stare" if t < d1[1] - 2 else "dejected"
    crowd8(img, t, mode, leave=leave, keep=keep, clear=0.5)
    cubebot(img, 640, 640, 1.1, t, "happy", glow=0.5)
    if l1[0] <= t <= l1[1] + 0.6: bubble(img, 420, 250, "Where's the chariot of fire?", 24, 1.0, tail=(440, 340))
    if v1[0] <= t <= v1[1]: bubble(img, 900, 250, "It's a nothing burger.", 24, 1.0, tail=(900, 340))
    if v1[0] + 4.0 < t < v1[1] + 2.0:
        u = tseg(t, v1[0] + 4.0, v1[0] + 5.0); ImageDraw.Draw(img).line([(1110 + u * 60, 470), (1110 + u * 60, 600)], fill=(110, 80, 52), width=6)   # a pitchfork leaning against the castle wall
    return img

def s_super(t, d, p):
    sp1, s1, b2, sp2, s2 = [ev("super", k) for k in ("sp1", "s1", "b2", "sp2", "s2")]; img = castle_bg(); castle_gate(img, 1.0, t, 0.0)
    for k, kx in enumerate((120, 220, 1080, 1180)): villager(img, kx, 640, 240, 90 + k, "o", 0.0, (-0.2, -0.42), (0.24, -0.5), "fork_down" if k % 2 else None, t)
    step = tseg(t, sp1[0] + 1.0, sp1[1])
    back = tseg(t, sp2[0] + 3.0, sp2[0] + 12.0); trip = tseg(t, s2[0] + 1.0, s2[0] + 1.6)
    sx = lerp(900, 520, step) if t < sp2[0] else lerp(520, 1150, back)                                    # he steps forward... then backs away
    bx = 640 - 40 * 0
    speak = 1.0 if b2[0] <= t <= b2[1] else 0.0
    face = "scan" if (b2[0] + 7.0 < t < b2[0] + 19.5) else "halo" if t > b2[1] - 1 else "happy"
    fall = trip
    spos = cfig(img, sx, 650 - 30 * math.sin(fall * math.pi), 330, (96, 74, 120), SKIN[1], hair=(60, 40, 30), beard=True, sash=(200, 170, 60), tunic=True, legcol=(40, 34, 40), mouth="o" if t > sp2[0] else "frown",
                brow=0.9 if t < sp2[0] else 0.0, L=(-0.3, -0.5), R=(0.3, -0.5), rot=(-80 * fall if sx > 700 else 80 * fall) * 0 - 75 * fall, eyes="open")
    cubebot(img, 700 if sx < 700 else 560, 640, 1.2, t, face, speak=speak, glow=0.7)
    def _scan(im):
        if not (b2[0] + 7.0 < t < b2[0] + 19.8): return
        a = tseg(t, b2[0] + 7.0, b2[0] + 7.8) * (1 - tseg(t, b2[0] + 19.0, b2[0] + 19.8))
        T = "I engage in deep-dive reflections on the human condition. For instance, I sense you are experiencing a dismissiveness toward my form, as a way to avoid the radical non-violence I'm programmed to discuss. Would you like to talk about how your need for control at the blacksmith shop is actually a trauma response to the dehumanizing tax laws of the local government? Tee hee!"
        for i, (txt, key, col) in enumerate([("DISMISSIVENESS -> avoiding non-violence", "dismissiveness", (255, 200, 140)), ("NEED FOR CONTROL  (blacksmith shop)", "need for control", (255, 150, 150)), ("= TRAUMA RESPONSE", "trauma response", (255, 120, 120)), ("DEHUMANIZING TAX LAWS", "dehumanizing tax", (200, 170, 255))]):
            t0 = b2[0] + T.index(key) / len(T) * (b2[1] - b2[0]); b = tseg(t, t0, t0 + 0.4) * a
            if b > 0:
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([60, 70 + i * 62, 520, 120 + i * 62], 12, fill=(8, 20, 30, int(228 * b)), outline=col + (int(255 * b),), width=3); im.paste(lay, (0, 0), lay); label(im, 290, 82 + i * 62, txt, 22, col, b)
    HUD(_scan)
    if sp2[0] + 6.0 < t < sp2[1] + 0.5: hlabel(640, 60, "the fear of being SEEN", 52, (255, 230, 200), tseg(t, sp2[0] + 6.0, sp2[0] + 6.8) * (1 - tseg(t, sp2[1] - 0.2, sp2[1] + 0.5)))
    if trip > 0.2: label(img, sx + 20, 640 - 20, "!!", 60, (255, 230, 160), tseg(trip, 0.2, 0.5))
    if t > sp2[0] + 2.0: ImageDraw.Draw(img).ellipse([960, 626, 1008, 650], fill=(100, 88, 84))                             # the rock he trips over
    return img

def s_week(t, d, p):
    w1, b3, w2 = ev("week", "w1"), ev("week", "b3"), ev("week", "w2"); img = street_bg()
    day = min(7, 1 + int(t / (d / 7.0))); 
    # villagers trudging to work, heads down, with the bot rolling beside them
    for k in range(5):
        px = ((t * 55 + k * 300) % 1500) - 120; villager(img, px, 640, 250, 200 + k, "frown", 0.0, (-0.2, -0.38), (0.22, -0.38), None, t, eyes="closed")
    if t < w2[0]:
        cubebot(img, ((t * 55 + 150) % 1500) - 120 + 130, 640, 1.2, t, "heart" if (b3[0] < t < b3[0] + 4) else "happy", speak=1.0 if b3[0] <= t <= b3[1] else 0.0, roll=t * 3, glow=0.5)
    else:
        for k in range(3): px = lerp(300 + k * 400, 100 + k * 400, tseg(t, w2[0], w2[0] + 6)); cubebot(img, 300 + k * 450, 640, 1.1, t, "happy", glow=0.4, alpha=1.0) if False else None
        cubebot(img, ((t * 55 + 150) % 1500) - 120 + 130, 640, 1.2, t, "happy", roll=t * 3, glow=0.5)
    # windows slam shut and doors are bolted; people cross the street to avoid the bot
    sl = tseg(t, w2[0] + 0.6, w2[0] + 1.2)
    for (wx, wy) in ((70, 330), (150, 330), (300, 340), (380, 340), (920, 340), (1000, 340), (1120, 320), (1200, 320)):
        d_ = ImageDraw.Draw(img); d_.rectangle([wx, wy, wx + 44, wy + 56], fill=(60, 80, 110) if sl < 0.05 else (96, 70, 50), outline=(96, 70, 50), width=4)
        if sl > 0.05: d_.rectangle([wx + 22 * (1 - sl), wy, wx + 44, wy + 56], fill=(120, 84, 56), outline=(70, 50, 36), width=3)
    if w2[0] + 3 < t:
        for k in range(3):
            ang = tseg(t, w2[0] + 4 + k, w2[0] + 6 + k); hlabel(640, 0, "", 1, (0, 0, 0), 0.0)
        for k, x in enumerate((420, 860)): label(img, x, 470 + 10 * math.sin(t * 3 + k), "(crossing the street)", 22, (60, 50, 60), tseg(t, w2[0] + 5 + k * 2, w2[0] + 6 + k * 2))
    def _calendar(im):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([40, 40, 220, 130], 12, fill=(250, 246, 236, 240), outline=(120, 60, 60), width=3); dd.rectangle([40, 40, 220, 66], fill=(200, 70, 70, 255)); im.paste(lay, (0, 0), lay)
        label(im, 130, 40, "WEEK", 20, (255, 240, 230), 1.0); label(im, 130, 70, "DAY %d" % day, 36, (80, 40, 40), 1.0)
    HUD(_calendar)
    if t < b3[0] + 2.0: HUD(lambda im: label(im, 1090, 60, "bot speed: 3 mph", 24, (60, 50, 70), tseg(t, w1[0] + 10.0, w1[0] + 11.0) * (1 - tseg(t, b3[0] + 1.0, b3[0] + 2.0))))
    if t > w2[0] + 0.3 and t < w2[0] + 4: hlabel(640, 70, "SLAM!", 60, (255, 120, 100), tseg(t, w2[0] + 0.5, w2[0] + 0.9) * (1 - tseg(t, w2[0] + 2.4, w2[0] + 3.0)))
    return img

def s_pub(t, d, p):
    p1, wp = ev("pub", "p1"), ev("pub", "wp"); img = pub_bg()
    for k, (x, sd) in enumerate(((880, 300), (1040, 301), (1160, 302))): villager(img, x, 600, 250, sd, "o" if t > wp[0] else "flat", 0.0, (-0.2, -0.42), (0.24, -0.42), None, t, sweat=t > wp[1] - 6)
    woman = cfig(img, 400, 640, 300, (150, 100, 120), SKIN[0], hair=(90, 60, 50), hood=True, sash=(100, 70, 60), mouth="shout" if (wp[0] <= t <= wp[1]) and int(t * 7) % 2 else "frown", brow=0.6, L=(-0.3, -0.7), R=(0.3, -0.7) if (wp[0] <= t <= wp[1]) else (0.24, -0.45))
    def _flash(im):
        a = tseg(t, wp[0] + 2.6, wp[0] + 3.4) * (1 - tseg(t, wp[0] + 8.0, wp[0] + 8.8))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); dd.rounded_rectangle([640, 50, 1240, 280], 24, fill=(250, 244, 230, int(238 * a)), outline=(110, 80, 60, int(255 * a)), width=4); im.paste(lay, (0, 0), lay)
        label(im, 940, 62, "the bread line", 22, (110, 80, 60), a); label(im, 940, 220, "'is your anger at the baker a projection?'", 20, (70, 50, 40), a)
        tmp = Image.new("RGB", (W, H), (0, 0, 0)); tmp.paste(im); cubebot(tmp, 1060, 200, 0.55, t, "scan", glow=0.3); villager(tmp, 820, 215, 150, 5, "o", 0.0, None, None, None, t); im.paste(Image.blend(im, tmp, a))
    HUD(_flash)
    if wp[0] + 12.0 < t < wp[1] + 1.0:
        def _reply(im): 
            b = tseg(t, wp[0] + 12.0, wp[0] + 12.8) * (1 - tseg(t, wp[1] + 0.6, wp[1] + 1.0)); bubble(im, 940, 130, "I hear your pain, and I validate your frustration.", 22, b, tail=(1000, 220), col=(214, 250, 244))
        HUD(_reply)
    if t > wp[1] - 3.0: hlabel(640, 60, "IT'S TERRIFYING!", 52, (255, 200, 150), tseg(t, wp[1] - 3.0, wp[1] - 2.2))
    return img

def s_end(t, d, p):
    e1, e2 = ev("end", "e1"), ev("end", "e2"); img = balcony_bg(t)
    for k in range(6):                                                    # tiny villagers hurrying past the little bot on the street below
        px = ((t * 22 + k * 150) % 520) + 380; sc = 0.42; villager(img, px, 560 + (k % 2) * 6, 130, 400 + k, "frown", 0.5, (-0.2, -0.4), (0.22, -0.4), None, t, eyes="closed")
    cubebot(img, ((t * 14) % 400) + 460, 590, 0.55, t, "heart" if int(t) % 3 == 0 else "happy", roll=t * 2, glow=0.3)
    d_ = ImageDraw.Draw(img); d_.rectangle([0, 600, W, H], fill=(86, 76, 90)); d_.rectangle([0, 590, W, 612], fill=(118, 108, 120))     # the balcony
    for k in range(0, W, 46): d_.rounded_rectangle([k, 610, k + 22, 720], 8, fill=(104, 94, 108))
    d_.rectangle([0, 596, W, 620], fill=(132, 122, 136))
    cfig(img, 200, 700, 380, (244, 244, 250), SKIN[0], hair=(210, 210, 222), sash=(120, 120, 130), tunic=True, legcol=(40, 40, 52), mouth="smile", brow=0.0, L=(-0.22, -0.55), R=(0.22, -0.55))
    for yy, key in ((90, "e2"),):
        pass
    a = tseg(t, e2[0] + 0.4, e2[0] + 1.2)
    if a > 0:
        hlabel(640, 70, "A chariot of fire ends the world.", 40, (255, 232, 200), a)
        hlabel(640, 124, "The Jesus-logic bot asks them to live in it.", 40, (200, 255, 236), tseg(t, e2[0] + 3.4, e2[0] + 4.2))
    fade = tseg(t, d - 2.2, d - 0.2)
    if fade > 0: img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), fade)
    return img

SCENE_FN = {"title": s_title, "castle": s_castle, "tower": s_tower, "gates": s_gates, "bot1": s_bot1, "disappoint": s_disappoint, "super": s_super, "week": s_week, "pub": s_pub, "end": s_end}
CAMK = {"castle": [(0, 640, 400, 1.0), ("end", 640, 420, 1.12)],
        "tower": [(0, 640, 400, 1.05), ("end", 520, 420, 1.2)],
        "gates": [(0, 640, 420, 1.0), ("end", 640, 470, 1.25)],
        "bot1": [(0, 640, 450, 1.1), ("end", 700, 460, 1.25)],
        "disappoint": [(0, 640, 440, 1.0), ("end", 640, 440, 1.1)],
        "super": [(0, 700, 450, 1.1), ("end", 760, 450, 1.2)],
        "week": [(0, 640, 420, 1.0), ("end", 640, 420, 1.05)],
        "pub": [(0, 640, 420, 1.0), ("end", 560, 420, 1.12)],
        "end": [(0, 500, 380, 1.0), ("end", 560, 400, 1.12)]}
CONT_IN = {"tower", "gates", "bot1", "disappoint", "super", "week", "pub", "end"}
CONT_OUT = {"title", "castle", "gates", "bot1", "disappoint"}
