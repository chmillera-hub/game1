import json, wave, math, subprocess, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, AH, SS = 1080, 1920, 24, 960, 2
segs = json.load(open("segs.json"))
INTRO, GAP, OUTRO = 2.4, 1.6, 3.2
t = INTRO
for s in segs:
    with wave.open(f"seg{segs.index(s)}.wav") as w: s["dur"] = w.getnframes() / w.getframerate()
    s["start"] = t; s["end"] = t + s["dur"]; t = s["end"] + GAP
TOTAL = segs[-1]["end"] + OUTRO
B = [0] + [(segs[k-1]["end"] + segs[k]["start"]) / 2 for k in range(1, 6)] + [TOTAL]

clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
ease = lambda x: (lambda y: y*y*(3-2*y))(clamp(x))
lerp = lambda a, b, x: a + (b - a) * x
rad = math.radians
def g(x): return 815 + 16*math.sin(x/190+.8) - 8*math.sin(x/70)

ROBE=(238,230,214,255); ROBE_SH=(206,196,184,255); SASH=(214,168,92,255)
SKIN=(206,160,124,255); HAIR=(74,48,38,255); WOOL=(246,240,228,255); DARK=(58,44,50,255)

_gs = {}
def sprite(r):
    r = max(8, int(round(r/8))*8)
    if r not in _gs:
        yy, xx = np.mgrid[-r:r, -r:r].astype(np.float32)
        d = np.sqrt(xx*xx+yy*yy)/r
        _gs[r] = np.exp(-(d*2.1)**2) * (d < 1)
    return _gs[r]

class Ctx:
    def __init__(self, cv): self.cv = cv; self.layer = None; self.q = []
    def d(self):
        if self.layer is None:
            self.layer = Image.new("RGBA", (W*SS, AH*SS), (0,0,0,0)); self._d = ImageDraw.Draw(self.layer)
        return self._d
    def flush(self):
        if self.layer is None: return
        a = np.asarray(self.layer.resize((W, AH), Image.LANCZOS)).astype(np.float32)
        al = a[..., 3:4]/255
        self.cv = self.cv*(1-al) + a[..., :3]*al
        self.layer = None
    def _add(self, cx, cy, r, color, k):
        sp = sprite(r); h = sp.shape[0]//2
        x0, y0 = int(cx)-h, int(cy)-h
        xa, ya, xb, yb = max(0,x0), max(0,y0), min(W,x0+2*h), min(AH,y0+2*h)
        if xa >= xb or ya >= yb: return
        sub = sp[ya-y0:yb-y0, xa-x0:xb-x0, None]
        self.cv[ya:yb, xa:xb] += sub*np.array(color, np.float32)*k
    def glow(self, cx, cy, r, color, k=1.0):
        self.flush(); self._add(cx, cy, r, color, k)
    def fx(self, cx, cy, r, color, k=1.0): self.q.append((cx, cy, r, color, k))
    def ell(self, cx, cy, rx, ry, fill): self.d().ellipse([(cx-rx)*SS,(cy-ry)*SS,(cx+rx)*SS,(cy+ry)*SS], fill=fill)
    def circ(self, cx, cy, r, fill): self.ell(cx, cy, r, r, fill)
    def poly(self, pts, fill): self.d().polygon([(x*SS,y*SS) for x,y in pts], fill=fill)
    def line(self, p, w, fill):
        d = self.d(); d.line([(x*SS,y*SS) for x,y in p], fill=fill, width=max(1,int(w*SS)))
        for x,y in (p[0], p[-1]): self.circ(x, y, w/2, fill)
    def arc(self, cx, cy, r, a0, a1, w, fill):
        self.d().arc([(cx-r)*SS,(cy-r)*SS,(cx+r)*SS,(cy+r)*SS], a0, a1, fill=fill, width=max(1,int(w*SS)))
    def ring(self, cx, cy, r, w, fill): self.arc(cx, cy, r, 0, 360, w, fill)
    def done(self):
        self.flush()
        for a in self.q: self._add(*a)
        return np.clip(self.cv, 0, 255)

_sky = {}
def sky(warm):
    key = round(warm, 2)
    if key not in _sky:
        f = (np.arange(AH, dtype=np.float32)/AH)[:, None, None]
        stops = [(0,(12,12,40)),(.5,(48,30,86)),(.8,(150*warm**.5,84,104)),(.95,(225*min(1.1,warm),140*warm,100))]
        out = np.zeros((AH,1,3), np.float32)
        for (f0,c0),(f1,c1) in zip(stops, stops[1:]):
            m = ((f>=f0)&(f<f1)); x = (f-f0)/(f1-f0)
            out += m*(np.array(c0)*(1-x)+np.array(c1)*x)
        out[f[:,0,0] > .95] = stops[-1][1]
        _sky[key] = np.repeat(out, W, axis=1)
    return _sky[key].copy()

random.seed(7)
STARS = [(random.random()*W, random.random()*430, random.uniform(1.2,3), random.uniform(0,6.28)) for _ in range(55)]

def backdrop(tm, warm, sun=None):
    c = Ctx(sky(warm))
    sx, sy = sun if sun else (W/2, 770)
    c.glow(sx, sy, 560, (255,170,100), .55*warm)
    for x, y, r, ph in STARS:
        a = int(200*(.5+.5*math.sin(tm*1.3+ph))*(1-y/480))
        c.circ(x, y, r, (255,245,220,max(0,a)))
    if sun:
        c.glow(sx, sy, 260, (255,215,150), .9)
        c.circ(sx, sy, 70, (255,236,190,255))
    far = [(x, 690+45*math.sin(x/250+2)+22*math.sin(x/110)) for x in range(-10, W+20, 10)]
    c.poly(far+[(W+10,AH),(-10,AH)], (52,36,80,255))
    near = [(x, g(x)) for x in range(-10, W+20, 10)]
    c.poly(near+[(W+10,AH),(-10,AH)], (27,20,50,255))
    return c

def sheep(c, x, s, ph=0.0, face=-1, gy=None, bob_on=True):
    gy = g(x)+6 if gy is None else gy
    bob = abs(math.sin(ph))*s*.06 if bob_on else 0
    for dx, off in ((-.35,0),(-.14,math.pi),(.18,math.pi),(.38,0)):
        sw = math.sin(ph+off)*s*.09
        c.line([(x+dx*s, gy-.4*s-bob), (x+dx*s+sw, gy)], .09*s, DARK)
    puffs = ((-.3,-.62,.3),(0,-.7,.34),(.3,-.62,.3),(-.12,-.5,.3),(.14,-.5,.3),(-.02,-.88,.24))
    for dx, dy, r in puffs: c.circ(x+dx*s, gy+dy*s-bob, r*s*1.1+1.5, (96,78,92,255))
    for dx, dy, r in puffs: c.circ(x+dx*s, gy+dy*s-bob, r*s, WOOL)
    hx = x+face*.55*s
    c.ell(hx, gy-.62*s-bob, .15*s, .2*s, DARK)
    c.ell(hx-face*.1*s, gy-.8*s-bob, .07*s, .12*s, DARK)

def person(c, x, base, h, glowk, tint):
    u = h/6
    c.glow(x, base-h*.55, h*1.0, (255,205,140), glowk)
    c.poly([(x-.62*u,base-4.4*u),(x+.62*u,base-4.4*u),(x+1.15*u,base),(x-1.15*u,base)], tint)
    c.ell(x, base-5.15*u, .6*u, .66*u, SKIN)
    c.ell(x, base-5.45*u, .66*u, .42*u, (60,42,40,255))

def christ(c, cx, base, h, ar, al, staff=False, mid=None, halo=1.0, post=None):
    u = h/9.6; top = base-h; hy = top+.85*u; sy = top+2.0*u
    c.glow(cx, hy, 4.0*u, (255,215,140), .85*halo)
    hands = {}
    for side, (a1, a2) in ((1,ar),(-1,al)):
        sx = cx+side*.95*u
        ex, ey = sx+side*math.sin(rad(a1))*2.2*u, sy+math.cos(rad(a1))*2.2*u
        hx, hyy = ex+side*math.sin(rad(a2))*2.0*u, ey+math.cos(rad(a2))*2.0*u
        hands[side] = (sx, sy, ex, ey, hx, hyy)
    if staff:
        xh = hands[-1][4]
        c.line([(xh, base+4), (xh, top-.4*u)], .17*u, (122,86,56,255))
        c.arc(xh+.5*u, top-.4*u, .5*u, 180, 360, .17*u, (122,86,56,255))
    c.poly([(cx-.95*u,sy),(cx+.95*u,sy),(cx+2.0*u,base),(cx-2.0*u,base)], ROBE)
    c.poly([(cx-.95*u,sy),(cx,sy),(cx,base),(cx-2.0*u,base)], ROBE_SH)
    c.line([(cx-1.25*u, top+5.0*u),(cx+1.25*u, top+5.0*u)], .3*u, SASH)
    if mid: mid(u, top)
    for side in (1,-1):
        sx, s_y, ex, ey, hx, hyy = hands[side]
        col = ROBE if side == 1 else ROBE_SH
        c.line([(sx,s_y),(ex,ey),(hx,hyy)], .8*u, col)
        c.circ(hx, hyy, .4*u, SKIN)
    if post: post(u, top)
    c.ell(cx, sy-.1*u, .38*u, .5*u, SKIN)
    c.ell(cx, hy+.3*u, .98*u, 1.25*u, HAIR)
    c.ell(cx-.8*u, hy+1.0*u, .35*u, .9*u, HAIR); c.ell(cx+.8*u, hy+1.0*u, .35*u, .9*u, HAIR)
    c.ell(cx, hy+.12*u, .7*u, .84*u, SKIN)
    c.ell(cx, hy+.68*u, .5*u, .42*u, HAIR)
    c.ring(cx, hy, 1.6*u, .1*u, (255,226,150,210))
    return u, top, hands

def arcs_sound(c, x, y, tl, n=3):
    for k in range(n):
        f = ((tl*.5)+k/n) % 1
        a = int(190*(1-f)*clamp(f*6))
        c.arc(x, y, 70+f*330, -38, 38, 7, (255,228,160,a))

# ---------------- scenes ----------------
def scene1(tm, tl, p):
    c = backdrop(tm, .95)
    cx = 300; base = g(cx)+4
    for i in range(5):
        st, en = 1350+i*140, 540+i*118
        q = ease(tl/(4.8+i*.15)); x = lerp(st, en, q)
        sheep(c, x, [92,80,96,84,90][i], ph=x/38 if q < 1 else tm*.8+i)
    u, top, h_ = christ(c, cx, base, 500, (98, 98+14*math.sin(tm*3.2)), (22,6), staff=True)
    hx = cx+.9*u; hy = top+.85*u
    arcs_sound(c, hx+30, hy, tm)
    return c.done()

def scene2(tm, tl, p):
    c = backdrop(tm, .7)
    cx = 540; base = g(cx)+4
    for k in range(6):
        f = ((tl*.28)+k/6) % 1; ang = rad(k*60+tl*14); d = lerp(330, 760, f)
        a = int(110*(1-f))
        x, y = cx+math.cos(ang)*d, 560+math.sin(ang)*d*.8
        c.ell(x, y, 60, 14, (8,6,18,a))
    sheep(c, 190, 85, face=1, ph=tm*.7); sheep(c, 900, 80, face=-1, ph=tm*.9+1)
    def lamb(u, top):
        cy = top+5.1*u
        sheep(c, cx, 2.4*u, ph=0, face=1, gy=cy, bob_on=False)
        for dx in (-1.25, 1.25): c.circ(cx+dx*u, cy-.5*u, .42*u, SKIN)
    c.glow(cx, base-520+3.3*(520/9.6), 3.6*(520/9.6)*(1+.06*math.sin(tm*2)), (255,215,150), .6)
    u, top, h_ = christ(c, cx, base, 520, (25,-108), (25,-108), post=lamb)
    lc = (cx, top+3.7*u)
    for k in range(3):
        f = ((tl*.4)+k/3) % 1
        c.ring(lc[0], lc[1], lerp(2.2*u, 7.5*u, f), 5, (255,226,160,int(170*(1-f))))
    return c.done()

def scene3(tm, tl, p):
    sy = lerp(150, 215, ease(p*1.3))
    c = backdrop(tm, .85, sun=(540, sy))
    cx = 540; base = g(cx)+4
    for k in range(18):
        a = rad(k*20+tl*8)
        c.line([(540+math.cos(a)*100, sy+math.sin(a)*100),(540+math.cos(a)*(150+14*math.sin(tm*2+k)), sy+math.sin(a)*(150+14*math.sin(tm*2+k)))], 6, (255,232,175,160))
    u, top, h_ = christ(c, cx, base, 500, (132,165), (132,165), halo=.8+.5*ease(p))
    hy = top+.85*u
    c.poly([(510,sy+60),(570,sy+60),(540+1.9*u,hy-1.6*u),(540-1.9*u,hy-1.6*u)], (255,232,170,38))
    for k in range(5):
        f = ((tl*.45)+k/5) % 1
        c.fx(540, lerp(sy+60, hy-1.6*u, f), 45, (255,235,180), .9)
    c.fx(540, hy-60, 260*(1+.4*ease(p)), (255,215,140), .25)
    return c.done()

XS = [130, 250, 370, 710, 830, 950]
TINT = [(150,118,150,255),(118,148,170,255),(170,140,110,255),(124,160,140,255),(168,120,126,255),(140,130,176,255)]
def crowd(tm, tl, p, love):
    c = backdrop(tm, .8 if not love else .95)
    cx = 540; base = g(cx)+4; ph_ = 290
    glowk = lerp(.15, .5, ease(p)) if not love else lerp(.5, 1.0, ease(p))
    for i, x in enumerate(XS):
        person(c, x, g(x)+10, ph_, glowk, TINT[i])
    ar = (100,100) if not love else (128,142)
    u, top, hands = christ(c, cx, base, 430, ar, ar)
    chest = [(x, g(x)+10-ph_*.58) for x in XS]
    heart = (cx, top+3.3*u)
    # light lines
    pts = [chest[0], chest[1], chest[2], (hands[-1][4], hands[-1][5]), heart, (hands[1][4], hands[1][5]), chest[3], chest[4], chest[5]]
    segs_ = list(zip(pts, pts[1:]))
    mid_i = 4
    for i, (a, b) in enumerate(segs_):
        dist = abs(i+.5-mid_i)
        al = clamp(p*(1.5 if not love else 4) - dist*.12 + (0 if not love else 1))
        c.line([a, b], 5, (255,222,150,int(150*al)))
    if not love:
        for k in range(4):
            f = ((tl*.35)+k/4) % 1; fl = f*(len(pts)-1); i = min(int(fl), len(pts)-2); r_ = fl-i
            x = lerp(pts[i][0], pts[i+1][0], r_); y = lerp(pts[i][1], pts[i+1][1], r_)
            c.fx(x, y, 45, (255,235,180), 1.1*clamp(p*2.5))
    else:
        c.fx(heart[0], heart[1], 220*(1+.1*math.sin(tm*3)), (255,200,140), .9)
        for i, ch in enumerate(chest):
            for k in range(3):
                f = ((tl*.5)+k/3+i*.11) % 1; e = ease(f)
                x = lerp(heart[0], ch[0], e); y = lerp(heart[1], ch[1], e)-math.sin(f*math.pi)*70
                c.fx(x, y, 34, (255,225,170), 1.3*math.sin(f*math.pi))
    return c.done()
scene4 = lambda tm, tl, p: crowd(tm, tl, p, False)
scene5 = lambda tm, tl, p: crowd(tm, tl, p, True)

def scene6(tm, tl, p):
    c = backdrop(tm, 1.1, sun=(830, lerp(790, 470, ease(p))))
    cx = 540; base = g(cx)+4
    for x, s, f in ((200,85,1),(310,78,1),(850,82,-1),(960,76,-1)):
        sheep(c, x, s, face=f, ph=0, bob_on=False)
    u, top, h_ = christ(c, cx, base, 500, (20,-118), (20,-118), halo=.8)
    heart = (cx, top+3.3*u)
    b = ease(tl/2.9) if tl < 2.9 else 1-ease((tl-2.9)/2.9)
    R = 70+150*b
    c.ring(heart[0], heart[1], R, 5, (255,230,170,int(120+100*b)))
    c.fx(heart[0], heart[1]+30, R*1.3, (255,205,140), .12+.22*b)
    return c.done()

SCENES = [scene1, scene2, scene3, scene4, scene5, scene6]
LABELS = [("Christ calls, and they follow.", "Try it: stop and listen for a voice."),
          ("Christ holds them close.", "Try it: wrap your arms around yourself."),
          ("Christ stands in the Father's light.", "Try it: lift your open hands."),
          ("Christ draws people together.", "Try it: reach out to someone."),
          ("Christ opens his arms in love.", "Try it: open your arms wide."),
          ("Christ rests, and breathes.", "Try it: breathe in, then out.")]

bg = np.zeros((H, W, 3), np.float32)
v = (np.arange(H)/H)[:, None, None]
bg[:] = np.array([14,18,46])*(1-v) + np.array([40,22,54])*v
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
bg += (np.exp(-(np.sqrt(((xx-W/2)/W)**2+((yy-1340)/H)**2)/.28)**2)[..., None]*np.array([255,190,110])*.16)

F = lambda size, style="": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/DejaVuSerif{style}.ttf", size)
f_main, f_ref, f_title, f_sub, f_l1, f_l2 = F(54), F(34), F(84,"-Bold"), F(38), F(40,"-Bold"), F(32)
CREAM, GOLD = (250,240,220), (232,185,105)
random.seed(4)
motes = [dict(x=random.random(), y=random.random(), r=random.uniform(2,6), sp=random.uniform(.01,.04), ph=random.uniform(0,6.28)) for _ in range(40)]

def fade(tm, a, b, fi=.6, fo=.6):
    return 0.0 if (tm < a or tm > b) else min(1, (tm-a)/fi, (b-tm)/fo)

def text(img, s, font, y, color, alpha, rise=0, spacing=18):
    if alpha <= 0: return
    layer = Image.new("RGBA", (W, H), (0,0,0,0)); dr = ImageDraw.Draw(layer)
    lines = s.split("\n"); lh = font.size+spacing; y0 = y+rise-len(lines)*lh/2
    for k, ln in enumerate(lines):
        w = dr.textlength(ln, font=font)
        dr.text(((W-w)/2, y0+k*lh), ln, font=font, fill=color+(int(255*alpha),))
    img.alpha_composite(layer)

def art_at(tm):
    k = max(i for i in range(6) if B[i] <= tm+.3 and (i == 0 or B[i] <= tm+.3))
    k = min(5, sum(1 for i in range(1,6) if B[i] <= tm))
    def render(i):
        tl = max(0, tm-B[i]); p = clamp(tl/(B[i+1]-B[i]))
        return SCENES[i](tm, tl, p)
    for j in range(1, 6):
        if abs(tm-B[j]) < .3:
            a = (tm-(B[j]-.3))/.6; a = a*a*(3-2*a)
            return render(j-1)*(1-a)+render(j)*a
    return render(k)

def frame(fi):
    tm = fi/FPS
    full = bg.copy(); full[:AH] = art_at(tm)
    img = Image.fromarray(np.clip(full, 0, 255).astype(np.uint8)).convert("RGBA")
    ml = Image.new("RGBA", (W//2, H//2), (0,0,0,0)); md = ImageDraw.Draw(ml)
    for m in motes:
        y = (m["y"]-tm*m["sp"]) % 1.0; x = m["x"]+.02*math.sin(tm*.5+m["ph"])
        a = int(100*(.5+.5*math.sin(tm*1.1+m["ph"]))); r = m["r"]
        md.ellipse([x*W/2-r, y*H/2-r, x*W/2+r, y*H/2+r], fill=(255,215,150,a))
    img.alpha_composite(ml.filter(ImageFilter.GaussianBlur(2.2)).resize((W,H)))
    # intro title (bottom half)
    a = fade(tm, .2, INTRO+.3, .8, .6)
    text(img, "A Moment\nof Reflection", f_title, 1330, CREAM, a, (1-a)*20, 24)
    text(img, "John 10  ·  John 17", f_sub, 1330+185, GOLD, a)
    for i, s in enumerate(segs):
        last = i == len(segs)-1
        a = fade(tm, s["start"]-.1, s["end"]+(OUTRO-.4 if last else .7), .7, .8)
        if a > 0:
            text(img, s["cap"], f_main, 1330, CREAM, a, (1-a)*24)
            text(img, s["ref"], f_ref, 1330+75+36*(s["cap"].count("\n")+1)+30, GOLD, a*.9)
    for i in range(6):
        l0 = max(B[i]+.3, INTRO-.2 if i == 0 else 0); l1 = B[i+1]-.1 if i < 5 else TOTAL-.3
        a = fade(tm, l0, l1, .6, .5)
        text(img, LABELS[i][0], f_l1, 868, GOLD, a)
        text(img, LABELS[i][1], f_l2, 922, CREAM, a*.85)
    ImageDraw.Draw(img).rectangle([W//4, H-110, W//4+int(W*.5*tm/TOTAL), H-108], fill=GOLD+(255,))
    return img.convert("RGB")

if __name__ == "__main__":
    if sys.argv[1] == "prev":
        for t_ in map(float, sys.argv[2:]): frame(int(t_*FPS)).save(f"p_{t_}.png")
    else:
        nf = int(TOTAL*FPS)
        p = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),
            "-i","-","-i","mix.wav","-c:v","libx264","-pix_fmt","yuv420p","-crf","20","-preset","medium","-c:a","aac","-b:a","160k",
            "-shortest","-movflags","+faststart","reflection2.mp4"], stdin=subprocess.PIPE)
        for fi in range(nf): p.stdin.write(frame(fi).tobytes())
        p.stdin.close(); p.wait(); print("done", nf)
