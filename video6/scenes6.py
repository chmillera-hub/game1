# ================================================================= Death takes a service call
BONE = (238, 232, 216); BONE_D = (150, 140, 118); CLOAK = (36, 34, 54); CLOAK_D = (22, 20, 34)
GY = 626                                  # ground line for the characters

def death(img, x, yb, h=320, t=0.0, flip=False, jaw=0.0, eyes="norm", look=(0.0, 0.0), L=None, R=None, scythe=True, sa=-6, lean=0.0, bend=0.0, walk=0.0,
          watch=False, alpha=1.0, whiten=0.0, sweat=0.0, brow=0.0, foot=None):
    w = int(h * 2.3); hh = int(h * 1.45); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); cx = w / 2; gy = hh - 8
    ys = 1 - 0.14 * bend
    U = lambda ux, uy: (cx + ux * h, gy + uy * h * ys + 0.07 * h * bend)
    sway = math.sin(walk * 2) * 0.025
    L = L or (-0.24, -0.42 + 0.01 * math.sin(t * 2)); R = R or (0.27, -0.46)
    def arm(S, Hd, hand=True):
        E0 = U(*Hd); vx, vy = E0[0] - S[0], E0[1] - S[1]; n = math.hypot(vx, vy) or 1; mid = ((S[0] + E0[0]) / 2, (S[1] + E0[1]) / 2)
        p1 = (-vy / n * 0.06 * h, vx / n * 0.06 * h); p = p1 if p1[1] > 0 else (-p1[0], -p1[1]); E = (mid[0] + p[0], mid[1] + p[1]); wd = int(h * 0.085)
        d.line([S, E, E0], fill=CLOAK, width=wd, joint="curve")
        for q in (S, E): d.ellipse([q[0] - wd / 2, q[1] - wd / 2, q[0] + wd / 2, q[1] + wd / 2], fill=CLOAK)
        d.ellipse([E0[0] - h * 0.03, E0[1] - h * 0.03, E0[0] + h * 0.03, E0[1] + h * 0.03], fill=BONE, outline=BONE_D)
        for k in range(3): d.line([E0, (E0[0] + (k - 1) * h * 0.02, E0[1] + h * 0.045)], fill=BONE, width=max(2, int(h * 0.011)))
        return E0
    hR = U(*R)
    if scythe:        # the pole goes behind the arm
        a = math.radians(sa); dx, dy = math.sin(a), -math.cos(a)
        p0 = (hR[0] - dx * h * 0.35, hR[1] - dy * h * 0.35); p1 = (hR[0] + dx * h * 1.0, hR[1] + dy * h * 1.0)
        d.line([p0, p1], fill=(92, 66, 44), width=int(h * 0.02))
        bx, by = p1; d.polygon([(bx, by), (bx - h * 0.3 * math.cos(a) - dx * h * 0.02, by - h * 0.3 * math.sin(a) * 0 + h * 0.05), (bx - h * 0.28, by + h * 0.1), (bx - h * 0.02, by + h * 0.03)], fill=(190, 198, 214), outline=(120, 128, 146))
    # legs (bony) + cloak
    for sg in (-1, 1):
        fx = sg * 0.085 + (math.sin(walk * 2 + (0 if sg > 0 else math.pi)) * 0.07 if walk else 0); fy = -0.0 - max(0, math.cos(walk * 2 + (0 if sg > 0 else math.pi))) * 0.05 * (1 if walk else 0)
        if foot and sg > 0: fx, fy = foot
        d.line([U(sg * 0.07, -0.08), U(fx, fy - 0.01)], fill=BONE, width=int(h * 0.022)); d.ellipse([U(fx, fy)[0] - h * 0.04, U(fx, fy)[1] - h * 0.015, U(fx, fy)[0] + h * 0.04, U(fx, fy)[1] + h * 0.015], fill=BONE, outline=BONE_D)
    pts = [U(-0.12, -0.76), U(0.12, -0.76), U(0.19, -0.5), U(0.27, -0.03)]
    for k in range(9): pts.append(U(0.27 - k * 0.0675 + sway * (k % 2 * 2 - 1), -0.0 if k % 2 == 0 else -0.045))
    pts += [U(-0.27, -0.03), U(-0.19, -0.5)]
    d.polygon(pts, fill=CLOAK); d.polygon([U(0.01, -0.76), U(0.12, -0.76), U(0.19, -0.5), U(0.27, -0.03), U(0.05, -0.03)], fill=CLOAK_D)
    d.polygon([U(-0.14, -0.78), U(0.14, -0.78), U(0.12, -0.66), U(-0.12, -0.66)], fill=CLOAK_D)             # shoulders
    # hood and skull
    hx, hy = U(0, -0.85)
    d.ellipse([hx - h * 0.125, hy - h * 0.13, hx + h * 0.125, hy + h * 0.14], fill=CLOAK); d.polygon([(hx - h * 0.1, hy - h * 0.07), (hx, hy - h * 0.2), (hx + h * 0.1, hy - h * 0.07)], fill=CLOAK)
    d.ellipse([hx - h * 0.088, hy - h * 0.088, hx + h * 0.088, hy + h * 0.1], fill=(10, 8, 16))
    d.ellipse([hx - h * 0.066, hy - h * 0.074, hx + h * 0.066, hy + h * 0.074], fill=BONE, outline=BONE_D)
    d.polygon([(hx - h * 0.012, hy + h * 0.012), (hx + h * 0.012, hy + h * 0.012), (hx, hy + h * 0.03)], fill=(30, 24, 30))
    ex = h * 0.03; ey = hy - h * 0.012
    for sg in (-1, 1):
        cxk = hx + sg * ex; r1 = h * (0.024 if eyes != "wide" else 0.032)
        if eyes in ("shut", "squint"):
            d.arc([cxk - r1, ey - r1 * 0.6, cxk + r1, ey + r1 * 0.9], 200, 340, fill=(20, 16, 24), width=max(3, int(h * 0.01))) if eyes == "shut" else d.line([(cxk - r1, ey), (cxk + r1, ey)], fill=(20, 16, 24), width=max(3, int(h * 0.012)))
        else:
            d.ellipse([cxk - r1, ey - r1 * 1.15, cxk + r1, ey + r1 * 1.15], fill=(14, 10, 20))
            if eyes == "roll": px, py = math.cos(t * 7) * r1 * 0.5, math.sin(t * 7) * r1 * 0.5 - r1 * 0.2
            else: px, py = look[0] * r1 * 0.5, look[1] * r1 * 0.5
            d.ellipse([cxk + px - h * 0.007, ey + py - h * 0.007, cxk + px + h * 0.007, ey + py + h * 0.007], fill=(255, 255, 255))
        if brow: d.line([(cxk - r1, ey - r1 * 1.5 - brow * h * 0.01 * sg), (cxk + r1, ey - r1 * 1.5 + brow * h * 0.01 * sg)], fill=CLOAK_D, width=3)
    # teeth + jaw
    ty = hy + h * 0.055
    d.rectangle([hx - h * 0.04, ty - h * 0.012, hx + h * 0.04, ty + h * 0.008], fill=BONE, outline=BONE_D)
    for k in range(-2, 3): d.line([(hx + k * h * 0.016, ty - h * 0.012), (hx + k * h * 0.016, ty + h * 0.008)], fill=BONE_D, width=1)
    jy = lerp(ty + h * 0.012, gy - 0.03 * h, clamp(jaw)) if jaw > 0.01 else ty + h * 0.012
    d.polygon([(hx - h * 0.042, jy - h * 0.01), (hx + h * 0.042, jy - h * 0.01), (hx + h * 0.03, jy + h * 0.026), (hx - h * 0.03, jy + h * 0.026)], fill=BONE, outline=BONE_D)
    for k in range(-2, 3): d.line([(hx + k * h * 0.016, jy - h * 0.01), (hx + k * h * 0.016, jy + h * 0.004)], fill=BONE_D, width=1)
    arm(U(-0.13, -0.72), L); arm(U(0.13, -0.72), R)
    if watch:
        wx, wy = U(*L); d.ellipse([wx - h * 0.026, wy - h * 0.045, wx + h * 0.026, wy + h * 0.007], fill=(232, 192, 70), outline=(150, 112, 30), width=2); d.ellipse([wx - h * 0.017, wy - h * 0.036, wx + h * 0.017, wy - 0.002 * h], fill=(250, 250, 244))
        d.line([(wx, wy - h * 0.019), (wx + 0.008 * h * math.cos(t * 3), wy - h * 0.019 + 0.008 * h * math.sin(t * 3))], fill=(40, 30, 20), width=2)
    if sweat > 0:
        for k in range(3):
            u = (t * 0.9 + k / 3) % 1; sx = hx + (k - 1) * h * 0.11; sy = hy - h * 0.05 + u * h * 0.14
            d.polygon([(sx, sy - 11), (sx - 5, sy), (sx + 5, sy)], fill=(150, 210, 255)); d.ellipse([sx - 5, sy - 4, sx + 5, sy + 7], fill=(150, 210, 255))
    if whiten > 0:
        tint = Image.new("RGBA", lay.size, (255, 252, 236, 255)); a_ = lay.split()[3]; lay = Image.blend(lay, tint, clamp(whiten)); lay.putalpha(a_)
    if flip: lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
    if lean: lay = lay.rotate(-lean if not flip else lean, center=(cx, gy), resample=Image.BICUBIC)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.paste(lay, (int(x - w / 2), int(yb - gy)), lay)
    sgf = -1 if flip else 1
    pos = lambda p_: (x + sgf * (p_[0] - cx), yb - gy + p_[1])
    return {"head": pos((hx, hy)), "L": pos(U(*L)), "R": pos(U(*R)), "shoulder": pos(U(0.1, -0.74)), "jaw": pos((hx, jy))}

def skulldog(img, x, yb, s=1.0, t=0.0, flip=False, mode="stand", alpha=1.0, tongue=1.0, ph=None, tilt=0.0):
    w, hh = int(300 * s), int(220 * s); lay = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); cx = w * 0.45; gy = hh - 8
    U = lambda ux, uy: (cx + ux * s, gy + uy * s)
    ph = (t * 14 if mode == "run" else 0.0) if ph is None else ph
    bob = abs(math.sin(ph)) * 8 if mode == "run" else math.sin(t * 6) * 1.5
    lw = max(3, int(7 * s))
    def bone(a, b, w_=lw):
        d.line([U(*a), U(*b)], fill=BONE, width=w_)
        for q in (a, b): d.ellipse([U(*q)[0] - w_ * 0.8, U(*q)[1] - w_ * 0.8, U(*q)[0] + w_ * 0.8, U(*q)[1] + w_ * 0.8], fill=BONE, outline=BONE_D)
    # legs (behind first)
    for k, (sx, hind, off) in enumerate([(-34, True, 0.0), (-24, True, 3.1), (34, False, 3.1), (44, False, 0.0)]):
        sw = math.sin(ph + off) * (26 if mode == "run" else 3); lift = max(0, math.cos(ph + off)) * (14 if mode == "run" else 0)
        top = (sx, -50 - bob); knee = (sx + sw * 0.5 + (8 if hind else -6), -28 - bob - lift * 0.5); paw = (sx + sw, -4 - lift)
        bone(top, knee); bone(knee, paw)
        d.ellipse([U(*paw)[0] - 9 * s, U(*paw)[1] - 4 * s, U(*paw)[0] + 9 * s, U(*paw)[1] + 5 * s], fill=BONE, outline=BONE_D)
    # tail: a few wagging bones
    tx, ty = -52, -64 - bob; ang = math.sin(t * 16) * 0.5 - 0.5
    for k in range(5):
        nx = tx - 12 * math.cos(ang + k * 0.12); ny = ty + 12 * math.sin(ang + k * 0.12) - 9
        d.line([U(tx, ty), U(nx, ny)], fill=BONE, width=max(3, int(5 * s))); d.ellipse([U(nx, ny)[0] - 4 * s, U(nx, ny)[1] - 4 * s, U(nx, ny)[0] + 4 * s, U(nx, ny)[1] + 4 * s], fill=BONE, outline=BONE_D); tx, ty = nx, ny
    # ribcage
    for k in range(6):
        rx = -34 + k * 13; d.arc([U(rx - 8, -82 - bob)[0], U(rx - 8, -82 - bob)[1], U(rx + 8, -30 - bob)[0], U(rx + 8, -30 - bob)[1]], 270, 90, fill=BONE, width=max(3, int(5 * s)))
    d.line([U(-50, -78 - bob), U(40, -78 - bob)], fill=BONE, width=max(4, int(7 * s)))                          # spine
    # head: skull, snout, jaw, tongue
    hx, hy = 62, -86 - bob; ang_ = math.radians(tilt)
    d.ellipse([U(hx - 24, hy - 20)[0], U(hx - 24, hy - 20)[1], U(hx + 22, hy + 18)[0], U(hx + 22, hy + 18)[1]], fill=BONE, outline=BONE_D, width=2)
    d.rounded_rectangle([U(hx + 12, hy - 4)[0], U(hx + 12, hy - 4)[1], U(hx + 52, hy + 12)[0], U(hx + 52, hy + 12)[1]], 6, fill=BONE, outline=BONE_D, width=2)
    jo = 8 + 5 * math.sin(t * 12) * tongue
    d.polygon([U(hx + 14, hy + 12), U(hx + 50, hy + 12), U(hx + 44, hy + 20 + jo), U(hx + 16, hy + 18 + jo)], fill=BONE, outline=BONE_D)
    d.rounded_rectangle([U(hx + 18, hy + 14)[0], U(hx + 18, hy + 14)[1], U(hx + 42, hy + 14 + jo + 14 * tongue)[0], U(hx + 42, hy + 14 + jo + 14 * tongue)[1]], int(5 * s), fill=(238, 120, 140))     # tongue hanging out
    d.ellipse([U(hx + 46, hy - 4)[0], U(hx + 46, hy - 4)[1], U(hx + 54, hy + 4)[0], U(hx + 54, hy + 4)[1]], fill=(20, 16, 20))
    d.ellipse([U(hx + 2, hy - 14)[0], U(hx + 2, hy - 14)[1], U(hx + 20, hy + 2)[0], U(hx + 20, hy + 2)[1]], fill=(14, 10, 20)); d.ellipse([U(hx + 9, hy - 9)[0], U(hx + 9, hy - 9)[1], U(hx + 14, hy - 4)[0], U(hx + 14, hy - 4)[1]], fill=(255, 255, 255))
    d.polygon([U(hx - 14, hy - 16), U(hx - 26, hy - 44 + math.sin(ph) * 4), U(hx - 2, hy - 20)], fill=BONE, outline=BONE_D)
    if flip: lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
    if tilt: lay = lay.rotate(tilt if not flip else -tilt, center=(cx, gy), resample=Image.BICUBIC)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.paste(lay, (int(x - (w - cx if flip else cx)), int(yb - gy)), lay)

def cross(img, x, y, s, kind="jesus", a=1.0, figure=True, bow=0.0):
    """a stylised cross with a modest, non-graphic figure on it (jesus) or a darker silhouette (thief)."""
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); wood = (112, 80, 52, 255); wd_ = (80, 56, 36, 255); vb = 0.055 * s
    d.rectangle([x - vb / 2, y, x + vb / 2, y + s], fill=wood); d.rectangle([x - 0.31 * s, y + 0.2 * s, x + 0.31 * s, y + 0.2 * s + vb], fill=wood)
    d.line([(x + vb / 2 - 2, y), (x + vb / 2 - 2, y + s)], fill=wd_, width=3)
    if figure:
        j = kind == "jesus"; skin = (226, 184, 142, 255) if j else (96, 78, 66, 255); cloth = (246, 242, 232, 255) if j else (110, 92, 78, 255)
        hy = y + 0.125 * s; hx = x + (0.0 if j else 0.02 * s * bow)
        d.line([(x - 0.045 * s, y + 0.225 * s), (x - 0.29 * s, y + 0.2 * s + vb / 2)], fill=skin, width=int(0.036 * s)); d.line([(x + 0.045 * s, y + 0.225 * s), (x + 0.29 * s, y + 0.2 * s + vb / 2)], fill=skin, width=int(0.036 * s))
        d.polygon([(x - 0.05 * s, y + 0.19 * s), (x + 0.05 * s, y + 0.19 * s), (x + 0.05 * s, y + 0.5 * s), (x - 0.05 * s, y + 0.5 * s)], fill=cloth if j else skin)
        d.line([(x - 0.02 * s, y + 0.5 * s), (x - 0.025 * s, y + 0.82 * s)], fill=skin, width=int(0.036 * s)); d.line([(x + 0.02 * s, y + 0.5 * s), (x + 0.025 * s, y + 0.82 * s)], fill=skin, width=int(0.036 * s))
        d.polygon([(x - 0.06 * s, y + 0.44 * s), (x + 0.06 * s, y + 0.44 * s), (x + 0.07 * s, y + 0.62 * s), (x - 0.07 * s, y + 0.62 * s)], fill=cloth)
        d.ellipse([hx - 0.045 * s, hy - 0.05 * s, hx + 0.045 * s, hy + 0.05 * s], fill=skin)
        if j:
            d.ellipse([hx - 0.05 * s, hy - 0.058 * s, hx + 0.05 * s, hy - 0.012 * s], fill=(100, 68, 46, 255)); d.polygon([(hx - 0.035 * s, hy + 0.01 * s), (hx + 0.035 * s, hy + 0.01 * s), (hx, hy + 0.075 * s)], fill=(100, 68, 46, 255))
            d.ellipse([hx - 0.075 * s, hy - 0.085 * s, hx + 0.075 * s, hy - 0.03 * s], outline=(255, 226, 140, 255), width=max(2, int(0.01 * s)))
        else: d.ellipse([hx - 0.05 * s, hy - 0.056 * s, hx + 0.05 * s, hy - 0.012 * s], fill=(50, 40, 34, 255))
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    img.paste(lay, (0, 0), lay)

# ---- settings
_BG6 = {}
def golgotha():
    if "g" in _BG6: return _BG6["g"].copy()
    img = gradient((52, 38, 84), (232, 128, 92), "golg"); d = ImageDraw.Draw(img); rng = random.Random(4)
    for i in range(7):
        cx = rng.uniform(0, W); cy = rng.uniform(40, 230); w = rng.uniform(260, 520)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); ld.ellipse([cx - w / 2, cy - 26, cx + w / 2, cy + 26], fill=(40, 26, 60, 150)); img.paste(lay, (0, 0), lay)
    d = ImageDraw.Draw(img); d.ellipse([940, 250, 1010, 320], fill=(255, 214, 160))
    d.polygon([(0, 440), (180, 400), (420, 430), (700, 380), (1000, 420), (1280, 390), (1280, 720), (0, 720)], fill=(52, 38, 56))
    d.polygon([(260, 470), (520, 372), (800, 360), (1040, 420), (1280, 470), (1280, 720), (260, 720)], fill=(78, 56, 62))
    d.polygon([(0, 560), (420, 540), (900, 556), (1280, 540), (1280, 720), (0, 720)], fill=(104, 78, 70))
    d.polygon([(0, 700), (600, 640), (1280, 650), (1280, 720), (0, 720)], fill=(150, 112, 90))
    for i in range(20):
        rx, ry = rng.uniform(0, W), rng.uniform(580, 700)
        d.ellipse([rx - 18, ry - 8, rx + 18, ry + 8], fill=(86, 66, 64))
    _BG6["g"] = img; return img.copy()

def office():
    if "o" in _BG6: return _BG6["o"].copy()
    img = gradient((18, 26, 40), (36, 52, 66), "office"); d = ImageDraw.Draw(img)
    for i in range(6):                                                     # a wall of hourglasses
        for j in range(3):
            x = 100 + i * 190; y = 90 + j * 110
            d.rectangle([x - 10, y - 38, x + 38, y - 30], fill=(130, 100, 60)); d.rectangle([x - 10, y + 36, x + 38, y + 44], fill=(130, 100, 60))
            d.polygon([(x - 2, y - 30), (x + 30, y - 30), (x + 16, y + 4), (x + 30, y + 36), (x - 2, y + 36), (x + 14, y + 4)], fill=(190, 210, 230, ), outline=(120, 150, 180)); d.polygon([(x + 4, y - 18), (x + 24, y - 18), (x + 14, y - 2)], fill=(230, 190, 110)); d.polygon([(x + 2, y + 34), (x + 28, y + 34), (x + 14, y + 18)], fill=(230, 190, 110))
    d.rectangle([0, 560, W, H], fill=(46, 36, 34)); d.rectangle([0, 556, W, 566], fill=(70, 54, 48))
    d.rectangle([180, 520, 780, 570], fill=(88, 62, 44)); d.rectangle([180, 510, 780, 524], fill=(116, 84, 58)); d.rectangle([200, 570, 224, 650], fill=(70, 50, 36)); d.rectangle([736, 570, 760, 650], fill=(70, 50, 36))
    d.ellipse([300, 470, 360, 514], fill=(230, 200, 110)); d.rectangle([326, 430, 334, 470], fill=(90, 80, 70))
    _BG6["o"] = img; return img.copy()

def heaven():
    if "h" in _BG6: return _BG6["h"].copy()
    img = gradient((255, 250, 224), (176, 212, 255), "heav"); d = ImageDraw.Draw(img); rng = random.Random(8)
    for i in range(14):
        cx = rng.uniform(0, W); cy = rng.uniform(80, 420); w = rng.uniform(160, 340)
        for k in range(4): d.ellipse([cx - w / 2 + k * w * 0.18, cy - 30 - (k % 2) * 16, cx - w / 2 + k * w * 0.18 + w * 0.45, cy + 24], fill=(255, 255, 255))
    for i in range(16):                                                         # the cloud floor
        cx = i * 90 - 20; d.ellipse([cx - 90, 560 + (i % 3) * 18, cx + 120, 660 + (i % 3) * 18], fill=(250, 250, 255)); d.ellipse([cx - 40, 540 + (i % 2) * 20, cx + 90, 620], fill=(255, 255, 255))
    d.rectangle([0, 640, W, H], fill=(236, 240, 252))
    for x in (1010, 1220):                                                      # golden gate
        d.rectangle([x, 230, x + 34, 600], fill=(236, 200, 110), outline=(176, 140, 60), width=3); d.ellipse([x - 10, 210, x + 44, 250], fill=(250, 226, 150), outline=(176, 140, 60), width=3)
    d.pieslice([1010, 130, 1254, 330], 180, 360, fill=(240, 206, 120), outline=(176, 140, 60), width=3)
    for k in range(8): d.line([(1048 + k * 20, 330), (1048 + k * 20, 598)], fill=(220, 186, 100), width=4)
    _BG6["h"] = img; return img.copy()

def beam(img, x, ytop, ybot, a, t):
    if a <= 0.01: return
    lay = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay); wv = 90 + 12 * math.sin(t * 5)
    d.polygon([(x - wv * 0.35, 0), (x + wv * 0.35, 0), (x + wv, ybot), (x - wv, ybot)], fill=(int(190 * a), int(170 * a), int(110 * a)))
    softglow(img, lay, 44, 1.2); img.paste(ImageChops.add(img, lay.point(lambda v: int(v * 0.6))))
    rays(img, x, ytop, t, (255, 236, 170), n=16, length=900, strength=0.34 * a)

def flare(img, x, y, a):
    if a <= 0.01: return
    lay = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(lay); r = 120 + 200 * a
    d.ellipse([x - r, y - r, x + r, y + r], fill=(int(255 * a), int(240 * a), int(190 * a))); softglow(img, lay, 70, 1.8); img.paste(ImageChops.add(img, lay.point(lambda v: int(v * 0.4))))

def smoke(img, x, y, u, col=(70, 66, 84)):
    if u <= 0 or u >= 1: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(3)
    for i in range(18):
        a = r.random() * 6.28; dist = (20 + u * 130) * r.uniform(0.4, 1); rr = (24 + 60 * u) * r.uniform(0.7, 1.2)
        px, py = x + math.cos(a) * dist, y - 80 + math.sin(a) * dist * 0.7 - u * 40
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=col + (int(220 * (1 - u)),))
    img.paste(lay, (0, 0), lay)

def music_notes(img, t, x, y, a=1.0):
    d = ImageDraw.Draw(img); f = F(34)
    for i in range(4):
        u = (t * 0.55 + i / 4) % 1; c = int(255 * math.sin(u * math.pi) * a)
        d.text((x + math.sin(i * 2.3 + t * 2) * 30 + u * 60, y - u * 120), "♪" if i % 2 else "♫", font=f, fill=(c, int(c * 0.9), int(c * 0.6)))

def jfig(img, x, yb, h=300, rot=0.0, mouth="smile", eyes="open", alpha=1.0, L=None, R=None):
    return cfig(img, x, yb, h, (246, 242, 232), SKIN[0], hair=(100, 68, 46), beard=True, sash=(206, 188, 150), mantle=None, tunic=True, mouth=mouth, eyes=eyes, rot=rot, alpha=alpha, L=L, R=R)

# ---- scenes
CX = {"L": 430, "C": 780, "R": 1110}                      # cross positions: thief, Jesus, thief
def bubble6(img, x, y, text, size=24, a=1.0, tail=None): bubble(img, x, y + OFF - 20, text, size, a, tail=(tail[0], tail[1] + OFF - 20) if tail else None)

def s_title(t, d, p):
    img = golgotha(); img = Image.blend(img, Image.new("RGB", (W, H), (10, 6, 18)), 0.4)
    for k, kx in enumerate((CX["L"], CX["C"], CX["R"])): cross(img, kx, 330 - (0 if k == 1 else -20), 330 if k == 1 else 270, "jesus" if k == 1 else "thief", figure=False)
    a = tseg(t, 0.4, 1.3) * (1 - tseg(t, d - 0.8, d - 0.1))
    title(img, "DEATH TAKES A SERVICE CALL", "a very short tale of a very long day for Death", a, y=235, size=50)
    return img

def s_ticket(t, d, p):
    n1, tk = ev("ticket", "n1"), ev("ticket", "tk"); img = office()
    lamp = 0.5 + 0.1 * math.sin(t * 3); lay = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(lay).ellipse([240, 380, 420, 540], fill=(int(120 * lamp), int(90 * lamp), 40)); softglow(img, lay, 60, 1.2)
    go = tseg(t, tk[1] - 1.6, tk[1] - 0.8); gone = tseg(t, tk[1] - 0.8, tk[1] - 0.2)
    reading = tseg(t, tk[0] - 0.4, tk[0] + 0.4)
    L_ = (-0.1, -0.74 + 0.12 * (1 - reading)) if go < 0.1 else None
    pos = death(img, 520 + 180 * go, GY - 6, 330, t, L=(-0.28, -0.52), R=(0.30 - 0.1 * (1 - go), -0.5), scythe=go > 0.05, sa=-6 + 10 * go, eyes="norm", look=(math.sin(t * 2) * 0.6 * (1 - reading), -0.6 * reading), alpha=1 - gone)
    smoke(img, 700, GY - 60, gone)
    # the service ticket (screen space)
    def _ticket(im):
        a = tseg(t, tk[0] - 0.3, tk[0] + 0.5) * (1 - tseg(t, tk[1] - 2.2, tk[1] - 1.6))
        if a <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); x0, y0 = 760, 90
        ld.rounded_rectangle([x0, y0, x0 + 440, y0 + 330], 16, fill=(250, 242, 214, int(250 * a)), outline=(120, 90, 50, int(255 * a)), width=4)
        for k in range(16): ld.ellipse([x0 - 8 + k * 29, y0 - 6, x0 + 6 + k * 29, y0 + 8], fill=(18, 26, 40, int(255 * a)))
        im.paste(lay, (0, 0), lay)
        T = "Oh, I got a service ticket for the next one. Let's see... thirty-something-year-old dude, named Jesus. Former carpenter. Should be located between two thieves. Alright, I'll go pick him up and bring him to the afterlife. Let's go."
        rows = [("SERVICE TICKET #0033", "Let's see", 24, (90, 50, 30)), ("PICK UP:  JESUS", "dude, named Jesus", 28, (30, 24, 20)), ("AGE:  30-something", "thirty-something", 22, (60, 48, 40)),
                ("OCCUPATION:  former carpenter", "Former carpenter", 22, (60, 48, 40)), ("LOCATION:  between two thieves", "between two thieves", 22, (150, 40, 36)), ("DESTINATION:  the afterlife", "afterlife", 22, (60, 48, 40))]
        for i, (txt, key, sz, col) in enumerate(rows):
            tt = tk[0] + T.index(key) / len(T) * (tk[1] - tk[0]); b = tseg(t, tt - 0.1, tt + 0.5) * a
            if b > 0: label(im, x0 + 26, y0 + 28 + i * 44, txt, sz, col, b, anchor="l")
        s_ = tseg(t, tk[1] - 2.6, tk[1] - 2.2) * a
        if s_ > 0: label(im, x0 + 320, y0 + 270, "URGENT", 34, (200, 40, 40), s_ * 0.9, anchor="c")
    HUD(_ticket)
    return img

def s_walk(t, d, p):
    w1, wh, dg, kk, kd = ev("walk", "w1"), ev("walk", "whistle"), ev("walk", "dogw"), ev("walk", "kick"), ev("walk", "kicked")
    img = golgotha()
    for k, kx in enumerate((830, 900, 970)): cross(img, kx, 380, 150 if k == 1 else 120, "jesus" if k == 1 else "thief", figure=False)
    u = tseg(t, 0.2, kd[1] + 0.8); x = lerp(170, 820, u); walk = t * 4.2
    stroll = 1.0 if t < kd[1] + 0.8 else 0.0
    lookx = math.sin(t * 1.6) * 0.9                                           # looking side to side, bored
    watch_u = tseg(t, w1[1] - 2.8, w1[1] - 2.0) * (1 - tseg(t, w1[1] + 0.2, w1[1] + 0.9))
    Lh = (-0.18 + 0.1 * watch_u, -0.42 - 0.3 * watch_u)
    kicking = tseg(t, kk[0] + 2.5, kk[0] + 3.0) * (1 - tseg(t, kk[0] + 3.0, kk[0] + 3.6))
    stone_x = x + 130 + 380 * tseg(t, kk[0] + 2.8, kd[1]) if t > kk[0] + 2.8 else x + 120
    stone_y = GY + 4 - 90 * math.sin(tseg(t, kk[0] + 2.8, kd[1]) * math.pi) if t > kk[0] + 2.8 else GY + 4
    looking_down = tseg(t, kk[0], kk[0] + 1.0) 
    pos = death(img, x, GY, 320, t, L=Lh, watch=watch_u > 0.1 or True, walk=walk * stroll, eyes="norm", look=(lookx * (1 - watch_u) * (1 - looking_down), 0.9 * looking_down - 0.8 * watch_u), lean=-4 * looking_down,
                scythe=True, sa=-10 + math.sin(walk * 2) * 3, foot=(0.17 * math.sin(walk * 2) + 0.12 * kicking, -0.05 * kicking) if kicking > 0 else None)
    d = ImageDraw.Draw(img)
    if t < kd[1] + 1.5:
        sx = stone_x if t > kk[0] + 2.8 else x + 130; d.ellipse([sx - 13, stone_y - 10, sx + 13, stone_y + 6], fill=(110, 96, 90), outline=(70, 60, 58), width=2)
    if wh[0] - 3.0 < t < wh[1] + 1.0 or t < w1[1] - 3: music_notes(img, t, x + 60, GY - 330, tseg(t, 0.6, 1.4))
    if dg[0] <= t <= dg[1] + 0.4: bubble6(img, x + 40, GY - 440, "...time to walk the skull dog after this.", 24, 1.0, tail=(x + 10, GY - 360))
    return img

def s_cross(t, d, p):
    c1, bt, c2, wtf, th, why, see, dl, br = [ev("cross", k) for k in ("c1", "beat", "c2", "wtf", "thanks", "why", "see", "delay", "bring")]
    img = golgotha()
    stretch = tseg(t, c1[0] + 1.2, c1[0] + 2.4) * (1 - tseg(t, c1[0] + 3.8, c1[0] + 4.4)); cough = tseg(t, c1[0] + 4.6, c1[0] + 5.0) * (1 - tseg(t, c1[0] + 5.6, c1[0] + 6.0))
    look_up = tseg(t, c1[0] + 6.2, c1[1] - 0.2)
    drop = tseg(t, c2[0], c2[0] + 0.45); jb = drop + (0.08 * math.sin((t - c2[0]) * 14) * math.exp(-(t - c2[0]) * 3) if t > c2[0] else 0)
    light = tseg(t, c2[0], c2[0] + 0.6) * (1 - 0.5 * tseg(t, br[0], br[0] + 1.5)) * (1 - 0.0)
    for k, kx in enumerate((CX["L"], CX["C"], CX["R"])):
        cross(img, kx, 130 if k == 1 else 230, 480 if k == 1 else 380, "jesus" if k == 1 else "thief", figure=True)
    beam(img, CX["C"], 150, 600, light, t)
    L_ = (-0.5 * stretch - 0.24 * (1 - stretch), -0.62 * stretch - 0.42 * (1 - stretch)); R_ = (0.5 * stretch + 0.27 * (1 - stretch), -0.62 * stretch - 0.46 * (1 - stretch))
    shield = tseg(t, why[1] - 3.2, why[1] - 2.4) * (1 - tseg(t, br[0] + 0.5, br[0] + 1.5)) if light > 0.2 else 0.0
    if cough > 0: R_ = (0.0 + 0.07 * (1 - cough), -0.78 + 0.0); 
    if shield > 0: L_ = (-0.1, -0.86); 
    gulp = tseg(t, dl[0] - 0.1, dl[0] + 0.3) * (1 - tseg(t, dl[0] + 0.3, dl[0] + 0.9))
    eyes = "shut" if (stretch > 0.2 and look_up < 0.1) else ("squint" if shield > 0.4 else ("wide" if drop > 0.1 else "norm"))
    pos = death(img, 560, GY - 6, 330, t, L=L_, R=R_ if (stretch > 0.01 or cough > 0.01) else (0.27, -0.46), scythe=cough < 0.05 and stretch < 0.05, jaw=jb, eyes=eyes, look=(0.4, -0.9 * look_up), whiten=0.5 * light, sweat=1.0 if gulp > 0.05 or t > dl[0] else 0.0, bend=0.4 * gulp, lean=-5 * shield)
    flare(img, 560, 330, 0.6 * light * (0.5 + 0.5 * math.sin(t * 6)) if light > 0 else 0)
    if cough > 0.3: bubble6(img, 600, 280, "*ahem*", 28, 1.0, tail=(570, 330))
    if drop > 0.05 and t < wtf[0] + 1.0: bubble6(img, 640, 250, "!!!", 40, tseg(t, c2[0], c2[0] + 0.2), tail=(580, 320))
    if why[0] <= t <= why[0] + 3.0: pass
    return img

def s_carry(t, d, p):
    c3, hk, th, hl, pa, dv = [ev("carry", k) for k in ("c3", "heck", "thieves", "hell", "para", "devil")]
    img = golgotha()
    lift = tseg(t, c3[0] + 1.0, c3[0] + 3.2)                              # Jesus is lifted down and over Death's shoulder
    thieves_gone = tseg(t, th[0] + 1.6, th[0] + 2.3); second = tseg(t, th[0] + 2.6, th[0] + 3.2)
    reappear = tseg(t, pa[0] + 2.2, pa[0] + 3.2)
    cross(img, CX["L"], 230, 380, "thief", a=1 - thieves_gone, figure=True); cross(img, CX["R"], 230, 380, "thief", a=1 - second, figure=True)
    cross(img, CX["C"], 130, 480, "jesus", figure=(lift < 0.05))
    # thieves: a red puff down to hell, then golden orbs rising to Paradise
    for kx, g in ((CX["L"], thieves_gone), (CX["R"], second)):
        if 0 < g < 1: smoke(img, kx, 600, g, (200, 50, 30))
        if reappear > 0 and g > 0.9:
            oy = 340 - 120 * reappear; lay = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(lay).ellipse([kx - 26, oy - 26, kx + 26, oy + 26], fill=(255, 230, 150)); softglow(img, lay, 24, 1.6); ImageDraw.Draw(img).ellipse([kx - 16, oy - 16, kx + 16, oy + 16], fill=(255, 250, 220)); ImageDraw.Draw(img).ellipse([kx - 22, oy - 38, kx + 22, oy - 28], outline=(255, 226, 140), width=3)
    walk_to = tseg(t, th[0] - 0.4, th[0] + 1.8) * (1 - tseg(t, th[0] + 2.8, hl[0] + 0.6)) + tseg(t, th[0] + 2.8, th[0] + 3.4) * 0.0
    dx = 560 - 130 * tseg(t, th[0] - 0.4, th[0] + 1.6) + 40 * tseg(t, th[0] + 2.6, th[0] + 4.0)
    bend = 0.9 * lift
    fp = tseg(t, devil[0] if False else dv[0] + 0.3, dv[0] + 0.9)
    pos = death(img, dx, GY - 6, 330, t, L=(-0.24, -0.5), R=(0.26, -0.5) if fp < 0.1 else (0.0, -0.8), scythe=fp < 0.1, bend=bend, eyes="wide" if hk[0] < t < hk[1] + 1 else "norm", sweat=1.0 if lift > 0.5 else 0.0, look=(0.5, 0.2))
    if lift > 0:
        sh = pos["shoulder"]; jx = lerp(CX["C"] + 20, sh[0] - 80, ease(lift)); jy = lerp(340, sh[1] + 70, ease(lift)); rot = lerp(0, -82, ease(lift))
        jfig(img, jx + 130 * (rot / -82), jy + 140 * (rot / -82) * 0 + 150, 300, rot=rot, eyes="closed", mouth="smile")
        crack = tseg(t, c3[0] + 3.0, c3[0] + 3.5)
        d_ = ImageDraw.Draw(img)
        if crack > 0: d_.line([(dx - 90, GY + 8), (dx - 30, GY + 28), (dx + 20, GY + 14), (dx + 90, GY + 34)], fill=(40, 28, 26), width=4)
        if lift > 0.8: label(img, dx - 120, GY - 400, "×100", 52, (255, 220, 160), tseg(t, c3[0] + 3.0, c3[0] + 3.6) * (1 - tseg(t, hk[1], hk[1] + 0.6)))
    return img

def s_whisper(t, d, p):
    nw, wl, rl = ev("whisper", "nwh"), ev("whisper", "will"), ev("whisper", "rules")
    img = golgotha(); img = Image.blend(img, Image.new("RGB", (W, H), (255, 240, 200)), 0.08 * tseg(t, wl[0], wl[1]))
    beam(img, 780, 150, 600, 0.35 + 0.3 * tseg(t, wl[0], wl[1] + 1.0), t)
    pos = death(img, 640, GY - 6, 340, t, L=(-0.22, -0.46), R=(0.27, -0.6), scythe=False, bend=0.7, eyes="norm" if t < wl[0] else "wide", look=(0.8 * math.sin(t * 3) if t > wl[1] else 0.9, 0.0), sweat=1.0 if t > wl[1] else 0.0, brow=1.0 if t > wl[1] else 0.0)
    sh = pos["shoulder"]; jfig(img, sh[0] - 70, sh[1] + 210, 300, rot=-82, eyes="closed" if t < wl[0] - 0.4 else "open", mouth="smile")
    hx, hy = pos["head"]
    if wl[0] <= t <= wl[1] + 0.6:
        bubble6(img, hx + 120, hy - 150, "Thy will has been done.", 22, 1.0, tail=(hx - 10, hy - 40), col=(255, 250, 230))
        ImageDraw.Draw(img).ellipse([hx + 60 - 24, hy - 220 - 6, hx + 60 + 24, hy - 214 + 2], outline=(255, 226, 140), width=3)
    if t > wl[1] + 0.4:
        for k, kx in enumerate((-60, 40)): label(img, hx + kx, hy - 120 - (k % 2) * 30 + math.sin(t * 4 + k) * 4, "?", 56, (255, 240, 200), tseg(t, wl[1] + 0.5 + k * 0.5, wl[1] + 1.0 + k * 0.5))
    return img

def s_arrive(t, d, p):
    th, ar, st, rd, gd = [ev("arrive", k) for k in ("thud", "arise", "stand", "ready", "getdog")]
    img = heaven(); land = th[0] + 3.4
    fall = tseg(t, land - 0.7, land); on_ground = t >= land
    sh = max(0, 1 - (t - land) * 5) * 16 if on_ground else 0
    smoke_u = tseg(t, th[0] + 0.4, th[0] + 2.0)
    if smoke_u < 1: smoke(img, 640, 400, smoke_u)
    beam(img, 640, 100, 600, 0.6 * tseg(t, ar[0] - 0.4, ar[0] + 0.6) * (1 - tseg(t, ar[1] + 1.5, ar[1] + 3.0)) + 0.25, t)
    rot = -82 if not on_ground else lerp(-82, 0, ease(tseg(t, st[0] + 0.2, st[0] + 2.2)))
    jy = lerp(-100, GY + 4, ease(fall)) if t > th[0] + 0.9 else -400
    if t > th[0] + 0.9:
        px = 640 + (100 * (rot / -82) if rot < -1 else 0); jfig(img, px, jy + 150 * (rot / -82) if rot < -1 else jy, 300, rot=rot, eyes="open" if t > st[0] else "closed", mouth="smile")
    if on_ground and t < land + 1.2:                      # the loud thud: a ring of cloud dust
        u = (t - land) / 1.2; lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        for k in range(10): a_ = k / 10 * 6.28; ld.ellipse([640 + math.cos(a_) * 360 * u - 36, GY + 10 + math.sin(a_) * 40 * u - 24, 640 + math.cos(a_) * 360 * u + 36, GY + 10 + math.sin(a_) * 40 * u + 24], fill=(255, 255, 255, int(230 * (1 - u)))); img.paste(lay, (0, 0), lay)
    # dust brushed off his feet, Death steps in from the side to say he'll get the dog
    if st[0] + 1.6 < t < st[1] + 0.4:
        for k in range(8): u = ((t - st[0]) * 1.4 + k / 8) % 1; ImageDraw.Draw(img).ellipse([600 + k * 12 - u * 20, GY - 10 - u * 40, 606 + k * 12 - u * 20, GY - 4 - u * 40], fill=(220, 214, 200))
    dx = lerp(-100, 330, tseg(t, rd[0] + 0.3, rd[0] + 1.4)); dd = ev("arrive", "getdog")
    if t > rd[0] + 0.3: death(img, dx, GY - 6, 320, t, flip=False, eyes="norm", look=(0.5, 0), scythe=True, walk=t * 4 if t < rd[0] + 1.5 else 0)
    if t > dd[0] + 0.6: 
        e = tseg(t, dd[1] + 0.2, dd[1] + 1.2)
        pass
    if sh > 0: img = img.transform((W, H), Image.AFFINE, (1, 0, math.sin(t * 90) * sh, 0, 1, math.cos(t * 70) * sh))
    if on_ground and t < land + 0.2: img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.5 * (1 - (t - land) / 0.2))
    return img

def s_dog(t, d, p):
    rs, bk, pc, jm, cd, wd, sr = [ev("dog", k) for k in ("rush", "bark", "precious", "jump", "cuddle", "walkdone", "sure")]
    img = heaven(); beam(img, 640, 100, 600, 0.22, t)
    JXp = 820
    run_u = tseg(t, bk[0] - 0.4, bk[1] + 1.6)                                    # the dog bursts in from the left
    jump_u = tseg(t, jm[0] + 2.5, jm[0] + 3.5)
    dogx = lerp(-100, 480, run_u) if jump_u <= 0 else lerp(480, 640, jump_u)
    # Death waits with arms crossed (and eyes that roll)
    roll = jm[0] + 3.2 < t
    death(img, 330, GY - 6, 320, t, L=(-0.1, -0.5) if roll else (-0.24, -0.42), R=(0.1, -0.52) if roll else (0.27, -0.46), scythe=not roll, eyes="roll" if (jm[0] + 4.2 < t < wd[0]) else "norm", look=(0.8, 0.0))
    ph = t * 14
    jesus_pos = jfig(img, JXp, GY + 4, 300, mouth="smile", L=(-0.2, -0.5 - 0.1 * jump_u), R=(0.22, -0.5 - 0.1 * jump_u))
    if jump_u <= 0:
        if t > bk[0] - 0.4 and run_u < 1.0: skulldog(img, dogx, GY + 6, 1.0, t, flip=False, mode="run")
        elif run_u >= 1.0: skulldog(img, 480, GY + 6, 1.0, t, flip=False, mode="stand", tongue=1.0)
    else:
        arc = math.sin(jump_u * math.pi) * 150; dx = lerp(480, JXp - 70, jump_u); dy = lerp(GY + 6, GY - 160, ease(jump_u)) - arc
        skulldog(img, dx, dy, 1.0 - 0.15 * jump_u, t, flip=False, mode="stand", ph=jump_u * 6, tilt=-20 * (1 - jump_u))
    if t > jm[0] + 3.5: 
        # cuddling in Jesus's arms, licking
        skulldog(img, JXp - 55, GY - 150, 0.6, t, flip=False, mode="stand", tongue=1.0 + 0.5 * math.sin(t * 10), tilt=-15)
        lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
        for k in range(5):
            u = (t * 0.6 + k / 5) % 1; hx = JXp - 20 + math.sin(k * 2 + t) * 60; hy = GY - 340 - u * 120
            c = (int(255 * (1 - u)), int(120 * (1 - u)), int(150 * (1 - u))); ld.ellipse([hx - 9, hy - 8, hx, hy + 2], fill=c); ld.ellipse([hx, hy - 8, hx + 9, hy + 2], fill=c); ld.polygon([(hx - 9, hy - 2), (hx + 9, hy - 2), (hx, hy + 12)], fill=c)
        softglow(img, lay, 10, 1.6); img.paste(ImageChops.add(img, lay))
    if bk[0] < t < bk[1] + 1.2:
        for k in range(2): bubble6(img, 560 + k * 80, GY - 420 - k * 50, "WOOF!" if k == 0 else "WOOF WOOF!", 26, tseg(t, bk[0] + k * 0.45, bk[0] + k * 0.45 + 0.1) * (1 - tseg(t, bk[1] + 0.8, bk[1] + 1.2)))
    # the walk: they set off together into the light
    go = tseg(t, sr[1] - 0.5, d - 0.4)
    if go > 0: img = Image.blend(img, Image.new("RGB", (W, H), (255, 252, 236)), 0.8 * go)
    return img

SCENE_FN = {"title": s_title, "ticket": s_ticket, "walk": s_walk, "cross": s_cross, "carry": s_carry, "whisper": s_whisper, "arrive": s_arrive, "dog": s_dog}
CAMK = {"ticket": [(0, 640, 400, 1.0), ("end", 560, 400, 1.15)],
        "walk": [(0, 400, 440, 1.2), ("end", 760, 450, 1.2)],
        "cross": [(0, 640, 420, 1.0), (("c2", 0.0), 640, 420, 1.0), (("c2", 0.0), 600, 300, 1.7), (("wtf", 0.0), 600, 300, 1.7), (("thanks", 0.0), 640, 420, 1.0), ("end", 640, 420, 1.0)],
        "carry": [(0, 640, 420, 1.0), ("end", 640, 430, 1.1)],
        "whisper": [(0, 640, 400, 1.3), ("end", 660, 380, 1.55)],
        "arrive": [(0, 640, 420, 1.0), ("end", 640, 430, 1.0)],
        "dog": [(0, 560, 440, 1.0), ("end", 640, 430, 1.1)]}
CONT_IN = {"ticket", "walk", "cross", "carry", "whisper", "arrive", "dog"}
CONT_OUT = {"title", "ticket", "walk", "cross", "carry", "whisper", "arrive"}
