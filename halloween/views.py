"""Scene renderers: each composes a set, its actors and lighting for one moment."""
import math

import skia

from anim import q
from cat import draw_cat, pose as cat_pose
from gfx import (H, W, Xf, clamp, fill, glow, lerp, lin_grad, noise1, poly, rad_grad, smooth_path, stroke)
from mice import KINDS, draw_mouse, pose as mouse_pose
from mom import draw_mom, pose as mom_pose, SKIN, SKIN_SH
import sets as S_
from letters import draw_text

BOIL_HZ = 4.0


def boil(t):
    return int(math.floor(t * BOIL_HZ))


def silhouette(c, fn, color=(4, 3, 8), alpha=1.0, blur=0.0):
    p = skia.Paint()
    if blur > 0:
        p.setImageFilter(skia.ImageFilters.Blur(blur, blur, skia.TileMode.kDecal, None))
    p.setAlphaf(alpha)
    c.saveLayer(None, p)
    c.saveLayer(None, None)
    fn(c)
    c.drawPaint(fill(color, 1.0, blend=skia.BlendMode.kSrcIn))
    c.restore()
    c.restore()


def mouse_head_y(name, P):
    K = KINDS[name]
    return P["y"] - (K["chin"] + K["legs"] + 18) * P.get("scale", 1.0) * K["size"]


def draw_actor(c, a, t, extra=None):
    P = a.pose(t)
    if extra:
        P.update(extra)
    alive = P.get("_speaking") or (a.idle > 0 and not P.get("flat"))
    b = boil(t) if alive else 0
    if a.kind.startswith("mouse:"):
        name = a.kind.split(":")[1]
        P["seed"] = a.seed * 100 + b
        draw_mouse(c, name, mouse_pose(**{k: v for k, v in P.items() if not k.startswith("_")}))
    elif a.kind == "cat":
        draw_cat(c, cat_pose(**{k: v for k, v in P.items() if not k.startswith("_")}))
    elif a.kind == "mom":
        draw_mom(c, mom_pose(**{k: v for k, v in P.items() if not k.startswith("_")}))
    elif a.kind == "sun":
        S_.draw_crayon_sun(c, P["x"], P["y"], P.get("scale", 1.0), t, P, seed=3 + (b if P.get("_speaking") else 0))
    elif a.kind == "ghost":
        S_.draw_ghost_drawing(c, P["x"], P["y"], P.get("scale", 1.0), t, P, seed=9 + (b if P.get("_speaking") else 0))
    return P


# ------------------------------------------------------------------ page (top-down drawing)
PAGE_X, PAGE_Y = 40, 260       # paper origin in page-view world coords


class PageView:
    """The drawing seen from above. Mice are flat actors in paper coords."""

    def __init__(self, actors, state, warm=0.6):
        self.actors = actors          # dict name -> Actor (kind mouse:<name>, flat=True)
        self.state = state            # dict key -> Track (page D params) or constants
        self.warm = warm

    def page_D(self, t):
        D = {}
        for k, v in self.state.items():
            D[k] = v.at(t) if hasattr(v, "at") else v
        return D

    def draw(self, c, t, cam, thumbs=0.0):
        tq = q(t)
        D = self.page_D(tq)
        for name in self.actors:
            D["hide_" + name] = True
        D["boil"] = 0
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill(S_.WOOD))
        c.save()
        cam.apply(c, 1.0)
        S_.draw_table(c, (-1200, -1200, W + 1200, H + 1200))
        with Xf(c, PAGE_X, PAGE_Y):
            c.drawRect(skia.Rect.MakeLTRB(14, 18, S_.PAPER_W + 14, S_.PAPER_H + 18), fill((0, 0, 0), 0.45, blur=14))
            S_.draw_page(c, tq, D)
            c.save()
            c.clipRect(skia.Rect.MakeLTRB(-40, -40, S_.PAPER_W + 40, S_.PAPER_H + 40), skia.ClipOp.kIntersect, True)
            order = sorted(self.actors.values(), key=lambda a: a.raw("z", tq, 0))
            for a in order:
                if a.raw("hidden", tq, False):
                    continue
                draw_actor(c, a, tq, dict(ink=D.get("ink", 1.0)))
            c.restore()
            # moonbeam sweep + lantern warmth
            mb = D.get("moonbeam", 0.0)
            if mb > -1:
                x = lerp(-600, 1500, clamp(mb))
                c.drawPath(poly([(x - 260, -100), (x + 160, -100), (x - 40, S_.PAPER_H + 100), (x - 460, S_.PAPER_H + 100)]),
                           fill((200, 220, 255), 0.22 * D.get("beam_a", 0.0), blur=40, blend=skia.BlendMode.kScreen))
            c.drawRect(skia.Rect.MakeLTRB(-200, -200, S_.PAPER_W + 200, S_.PAPER_H + 200),
                       fill((0, 0, 0), 1.0, lin_grad((-200, 0), (S_.PAPER_W, 0),
                                                     [(255, 140, 50, 0.20 * self.warm), (255, 140, 50, 0.0)]),
                            blend=skia.BlendMode.kScreen))
            c.drawRect(skia.Rect.MakeLTRB(-200, -200, S_.PAPER_W + 200, S_.PAPER_H + 200),
                       fill((14, 18, 50), D.get("night", 0.35)))
            if D.get("magic", 0.0) > 0:
                m = D["magic"]
                c.drawRect(skia.Rect.MakeLTRB(-200, -200, S_.PAPER_W + 200, S_.PAPER_H + 200),
                           fill((170, 200, 255), 0.25 * m, blend=skia.BlendMode.kScreen))
            if thumbs > 0:
                for (tx, ty, ang) in ((70, 1020, 53), (S_.PAPER_W - 70, 980, -53)):
                    with Xf(c, tx, ty, rot=ang):
                        c.drawRoundRect(skia.Rect.MakeLTRB(-60, -40, 60, 260), 60, 60, fill(SKIN_SH, thumbs))
                        c.drawRoundRect(skia.Rect.MakeLTRB(-52, -34, 52, 250), 52, 52, fill(SKIN, thumbs))
                        c.drawRoundRect(skia.Rect.MakeLTRB(-30, -24, 30, 30), 18, 18, fill((248, 226, 214), thumbs))
        c.restore()
        S_.vignette(c, 0.5)


# ------------------------------------------------------------------ tabletop stage
class StageView:
    def __init__(self, actors, state):
        self.actors = actors
        self.state = state

    def S(self, t):
        out = {}
        for k, v in self.state.items():
            out[k] = v.at(t) if hasattr(v, "at") else v
        return out

    def draw(self, c, t, cam):
        tq = q(t)
        S = self.S(tq)
        S["page"] = dict(S.get("page", {}))
        for name in ("wedge", "biscuit", "pip", "crumb", "tilt"):
            S["page"]["hide_" + name] = True
        S["page"]["hide_words"] = S.get("letters_up", 0.0) > 0.0
        S["page"]["r_pumpkins"] = 0.0
        S["page"]["r_flower"] = 0.0
        S["page"]["r_girl"] = 0.0
        S["page"]["ink"] = 1.0
        S["page"]["boil"] = 0
        shadow_fn = S.get("shadow_fn")
        if shadow_fn is not None:
            S["wall_shadow"] = lambda cc: shadow_fn(cc, tq)
        c.save()
        cam.apply(c, 0.3)
        S_.stage_far(c, tq, S)
        c.restore()
        c.save()
        cam.apply(c, 1.0)
        S_.stage_table(c, tq, S)
        S_.stage_page(c, tq, S)
        order = sorted((a for a in self.actors.values() if not a.raw("hidden", tq, False)),
                       key=lambda a: (a.raw("z", tq, 0), a.raw("y", tq, 0)))
        for a in order:
            if a.raw("z", tq, 0) < 0:
                draw_actor(c, a, tq)
        up = S.get("letters_up", 0.0)
        if up > 0:
            S_.draw_popup_letters(c, tq, up, glow_amt=S.get("letters_glow", 0.0), seed=0)
        lit = S.get("lantern", 1.0)
        S_.draw_lantern(c, -330, 1430, 330, tq, lit=lit, glow_amt=S.get("lantern_glow", 1.0))
        for a in order:
            if a.raw("z", tq, 0) >= 0:
                draw_actor(c, a, tq)
        fx = S.get("fx")
        if fx is not None:
            fx(c, tq)
        c.restore()
        dark = S.get("dark", 0.0)
        if dark > 0:
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill((4, 4, 12), dark))
        S_.vignette(c, 0.55)


# ------------------------------------------------------------------ kitchen (wide)
class KitchenView:
    def __init__(self, actors=None, state=None):
        self.actors = actors or {}
        self.state = state or {}

    def draw(self, c, t, cam):
        tq = q(t)
        S = {k: (v.at(tq) if hasattr(v, "at") else v) for k, v in self.state.items()}
        c.save()
        cam.apply(c, 0.85)
        S_.draw_wall(c, (-300, -300, W + 300, H + 300))
        S_.draw_window(c, (170, 150, 910, 1120), tq, moon_rel=(0.6, 0.56), moon_r=0.29)
        c.drawPath(poly([(330, 1120), (820, 1120), (1000, 1560), (380, 1640)]),
                   fill((0, 0, 0), 1, lin_grad((0, 1100), (0, 1640), [(160, 200, 230, 0.20), (160, 200, 230, 0.04)]),
                        blend=skia.BlendMode.kScreen))
        for a in self.actors.values():
            if a.raw("layer", tq, "front") == "sill" and not a.raw("hidden", tq, False):
                draw_actor(c, a, tq)
        c.restore()
        c.save()
        cam.apply(c, 1.0)
        S_.draw_table(c, (-400, 1380, W + 400, H + 400))
        if not S.get("page_gone", False):
            S_.draw_page_in_quad(c, [(420, 1450), (880, 1430), (960, 1800), (400, 1830)], tq,
                                 dict(S.get("page", {}), boil=0))
        c.drawLine(300, 1860, 520, 1880, stroke((240, 190, 60), 16))
        c.drawLine(300, 1860, 330, 1862, stroke((240, 200, 170), 16))
        S_.draw_lantern(c, 215, 1690, 165, tq, lit=S.get("lantern", 1.0))
        for a in self.actors.values():
            if a.raw("layer", tq, "front") == "front" and not a.raw("hidden", tq, False):
                draw_actor(c, a, tq)
        c.restore()
        ta = S.get("title", 0.0)
        if ta > 0:
            draw_text(c, "TOO MOM", 112, 230, 150, style="paper", seed=3, alpha=ta)
            from gfx import font, text_center
            text_center(c, "a Halloween tale", 540, 470, font("Griffy-Regular.ttf", 64), (232, 226, 250), a=ta,
                        outline=(10, 8, 20), outline_w=8)
        d = S.get("dark", 0.0)
        if d > 0:
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill((4, 4, 12), d))
        S_.vignette(c, 0.6)


# ------------------------------------------------------------------ stairs (prologue)
def draw_girl_sil(c, x, y, s, phase):
    with Xf(c, x, y, sx=s):
        bob = abs(math.sin(phase)) * 6
        c.translate(0, -bob)
        col = (6, 4, 10)
        c.drawCircle(0, -150, 30, fill(col))
        for side in (-1, 1):
            c.drawPath(smooth_path([(side * 24, -166), (side * 52, -150), (side * 50, -124), (side * 36, -140)]), fill(col))
        c.drawPath(poly([(0, -122), (-46, -30), (46, -30)]), fill(col))
        la = math.sin(phase) * 14
        c.drawLine(-14, -32, -16 - la * 0.3, 0 - max(0, la), stroke(col, 9))
        c.drawLine(14, -32, 16 + la * 0.3, 0 - max(0, -la), stroke(col, 9))
        # teddy dangling from one hand
        c.drawLine(30, -96, 50, -60, stroke(col, 8))
        c.drawCircle(56, -50, 14, fill(col))
        c.drawCircle(56, -30, 18, fill(col))
        c.drawCircle(46, -62, 6, fill(col))
        c.drawCircle(66, -62, 6, fill(col))


class StairsView:
    def __init__(self, state):
        self.state = state

    def draw(self, c, t, cam):
        tq = q(t)
        S = {k: (v.at(tq) if hasattr(v, "at") else v) for k, v in self.state.items()}
        c.save()
        cam.apply(c, 1.0)
        lamp = S.get("lamp", 1.0)
        S_.draw_stairs(c, tq, lamp)
        g = S.get("girl", -1.0)
        if 0 <= g <= 1:
            x = lerp(150, 900, g)
            y = lerp(1600, 700, g)
            # long shadow on the wall
            silhouette(c, lambda cc: draw_girl_sil(cc, x + 160, y - 220, 3.0, g * 40), (4, 3, 8), 0.5 * lamp, 10)
            draw_girl_sil(c, x, y, 1.5, g * 40)
        feet = S.get("feet", -1.0)
        if 0 <= feet <= 1:
            draw_slipper_steps(c, tq, feet)
        c.restore()
        if lamp < 1:
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill((2, 2, 8), 0.6 * (1 - lamp)))
        S_.vignette(c, 0.6)


def draw_slipper_steps(c, t, u):
    """Bat slippers stepping down the stairs under a striped robe hem."""
    # the camera is close on three steps; each foot drops one step in turn
    steps = [(880, 640), (700, 880), (520, 1120), (340, 1360)]
    pos = u * 2.6
    feet = []
    for side, off in ((-1, 0.0), (1, 0.5)):
        k = min(3.0, max(0.0, pos - off))
        i = int(k)
        f = k - i
        x0, y0 = steps[min(i, 3)]
        x1, y1 = steps[min(i + 1, 3)]
        e = f * f * (3 - 2 * f)
        x = x0 + (x1 - x0) * e + side * 70
        y = y0 + (y1 - y0) * e - math.sin(f * math.pi) * 60
        feet.append((x, y))
    hx = sum(p[0] for p in feet) / 2
    hy = min(p[1] for p in feet) - 70
    hem = smooth_path([(hx - 260, -400), (hx + 260, -400), (hx + 240, hy - 40), (hx + 160, hy + 10), (hx, hy - 10),
                       (hx - 160, hy + 12), (hx - 250, hy - 30)])
    c.drawPath(hem, fill((58, 38, 82)))
    c.save()
    c.clipPath(hem, skia.ClipOp.kIntersect, True)
    for i in range(-9, 10, 2):
        c.drawLine(hx + i * 28, -420, hx + i * 30, hy + 60, stroke((150, 128, 176), 16, 0.9))
    c.restore()
    for (x, y) in feet:
        with Xf(c, x, y, sx=1.7):
            c.drawLine(-6, -60, -4, -14, stroke((236, 210, 196), 16))
            c.drawOval(skia.Rect.MakeLTRB(-70, -30, 70, 26), fill((24, 18, 30)))
            for w in (-1, 1):
                c.drawPath(smooth_path([(w * 36, -12), (w * 92, -48), (w * 84, -18), (w * 104, -14), (w * 70, 8)]),
                           fill((24, 18, 30)))
            c.drawCircle(-16, -10, 6, fill((250, 230, 120)))
            c.drawCircle(16, -10, 6, fill((250, 230, 120)))


# ------------------------------------------------------------------ clock
class ClockView:
    def __init__(self, state):
        self.state = state

    def draw(self, c, t, cam):
        tq = q(t)
        S = {k: (v.at(tq) if hasattr(v, "at") else v) for k, v in self.state.items()}
        c.save()
        cam.apply(c, 1.0)
        S_.draw_wall(c, (-400, -400, W + 400, H + 400))
        glow(c, 200, 500, 1000, (150, 190, 230), 0.16)
        S_.draw_clock(c, 560, 1960, 1.25, tq, S.get("hour", 357.0), S.get("min", 350.0), pend=tq * 3.1,
                      shake=S.get("shake", 0.0))
        c.restore()
        f = S.get("flash", 0.0)
        if f > 0:
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill((210, 225, 255), f, blend=skia.BlendMode.kScreen))
        S_.vignette(c, 0.6)


# ------------------------------------------------------------------ doorway (Mom's entrance)
class DoorwayView:
    def __init__(self, mom, state):
        self.mom = mom
        self.state = state

    def draw(self, c, t, cam):
        tq = q(t)
        S = {k: (v.at(tq) if hasattr(v, "at") else v) for k, v in self.state.items()}
        c.save()
        cam.apply(c, 0.5)
        S_.draw_wall(c, (-600, -600, W + 600, H + 600))
        c.restore()
        c.save()
        cam.apply(c, 1.0)
        # doorway into the lit hall
        x0, x1, top, bot = 160, 920, 160, 2000
        arch = skia.Path()
        arch.moveTo(x0, bot)
        arch.lineTo(x0, top + 380)
        arch.quadTo(x0, top, 540, top - 60)
        arch.quadTo(x1, top, x1, top + 380)
        arch.lineTo(x1, bot)
        arch.close()
        c.drawPath(arch, fill((255, 200, 120), 1.0, lin_grad((0, top), (0, bot), [(255, 220, 150), (210, 140, 70)])))
        c.save()
        c.clipPath(arch, skia.ClipOp.kIntersect, True)
        for i in range(8):  # stairs inside
            yy = 1950 - i * 150
            c.drawLine(x0, yy, x1, yy - 60, stroke((150, 90, 50), 6, 0.6))
        lit = S.get("lit", 0.0)
        P = self.mom.pose(tq)
        mp = mom_pose(**{k: v for k, v in P.items() if not k.startswith("_")})
        silhouette(c, lambda cc: draw_mom(cc, mp), (6, 4, 10), 1.0)
        c.restore()
        if lit > 0:
            with Xf(c, 0, 0, alpha=lit):
                draw_mom(c, mp)
        c.drawPath(arch, stroke(S_.FRAME, 40))
        c.restore()
        # warm candle light on the floor in front
        S_.vignette(c, 0.6)


# ------------------------------------------------------------------ Mom close-up (reading)
class MomView:
    """Mom from the front, the kitchen behind her, the drawing's back facing us."""

    def __init__(self, mom, state):
        self.mom = mom
        self.state = state

    def draw(self, c, t, cam):
        tq = q(t)
        S = {k: (v.at(tq) if hasattr(v, "at") else v) for k, v in self.state.items()}
        c.save()
        cam.apply(c, 0.35)
        S_.draw_wall(c, (-900, -900, W + 900, H + 900))
        S_.draw_window(c, (-120, 0, 620, 1100), tq, moon_rel=(0.6, 0.5), moon_r=0.27, cobweb=False)
        c.restore()
        c.save()
        cam.apply(c, 1.0)
        glow(c, 540, 1500, 1100, (255, 150, 60), 0.30 * S.get("warm", 1.0))
        draw_actor(c, self.mom, tq)
        c.restore()
        S_.vignette(c, 0.55)


def paper_back(c, cx, cy, w, rot=0.0, a=1.0, inner=None):
    """Back of the drawing, held up: pale paper with the words showing through, mirrored."""
    h = w * S_.PAPER_H / S_.PAPER_W
    with Xf(c, cx, cy, rot=rot):
        c.drawRect(skia.Rect.MakeLTRB(-w / 2 + 8, -h / 2 + 10, w / 2 + 8, h / 2 + 10), fill((0, 0, 0), 0.35 * a, blur=8))
        c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2), fill((232, 226, 210), a))
        c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2),
                   fill((0, 0, 0), 1.0, lin_grad((0, -h / 2), (0, h / 2), [(255, 190, 120, 0.25 * a), (60, 40, 80, 0.18 * a)])))
        with Xf(c, w / 2, -h / 2, sx=-w / S_.PAPER_W, sy=w / S_.PAPER_W):
            draw_text(c, "TOO MOM I LOVE YOU", 165, 26, 54, style="pencil", seed=1, alpha=0.30 * a, weight=1.3)
            if inner:
                inner(c)
        c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2), stroke((150, 140, 130), 2, a))


# ------------------------------------------------------------------ fridge
FRIDGE_PAGE_ORIGIN = None


class FridgeView:
    def __init__(self, page_actors, others, state, morning=False):
        self.page_actors = page_actors   # flat mice on our drawing
        self.others = others             # sun, ghost, cat, mom-hand...
        self.state = state
        self.morning = morning

    def draw(self, c, t, cam):
        tq = q(t)
        S = {k: (v.at(tq) if hasattr(v, "at") else v) for k, v in self.state.items()}
        c.save()
        cam.apply(c, 1.0)
        S_.draw_wall(c, (-500, -500, W + 500, H + 500))
        S_.draw_fridge(c, tq, moon=0.0 if self.morning else 1.0, morning=1.0 if self.morning else 0.0)
        S_.draw_family_drawing(c, 270, 1480, 0.85, tq, wave=S.get("family_wave", 0.0), seed=13)
        with Xf(c, 820, 1470, rot=4):
            c.drawRect(skia.Rect.MakeLTRB(-130, -110, 130, 110), fill((250, 246, 232)))
            from gfx import wobble
            for k, col in enumerate(((230, 70, 80), (240, 160, 60), (240, 220, 80), (90, 190, 110), (90, 140, 230))):
                p = skia.Path()
                p.addArc(skia.Rect.MakeLTRB(-100 + k * 14, -60 + k * 14, 100 - k * 14, 140 - k * 14), 180, 180)
                c.drawPath(p, stroke(col, 12, 0.85, effect=wobble(6, 1.8, k)))
        for a in self.others.values():
            if a.kind in ("sun", "ghost") and not a.raw("hidden", tq, False):
                draw_actor(c, a, tq)
        S_.draw_magnet(c, 280, 280, "star")
        S_.draw_magnet(c, 790, 268, "dot")
        S_.draw_magnet(c, 270, 1360, "dot")
        S_.draw_magnet(c, 820, 1370, "star")
        # our drawing
        pin = S.get("pin", 1.0)
        if pin > -1:
            off = (1 - pin) * 700
            quad = S_.fridge_page_quad(cx=S_.FRIDGE_SPOT[0] + off, cy=S_.FRIDGE_SPOT[1] - off * 0.1,
                                       rot=-2.0 + (1 - pin) * 12)
            D = {"hide_" + n: True for n in self.page_actors}
            D.update({k[2:]: v for k, v in S.items() if k.startswith("p_")})
            D["boil"] = 0
            D["ink"] = 1.0
            c.drawPath(poly([(qx + 10, qy + 14) for qx, qy in quad]), fill((0, 0, 0), 0.4, blur=10))
            c.save()
            c.concat(S_.paper_matrix(quad))
            S_.draw_page(c, tq, D)
            for a in self.page_actors.values():
                if not a.raw("hidden", tq, False):
                    draw_actor(c, a, tq, dict(ink=1.0))
            if not self.morning:
                c.drawRect(skia.Rect.MakeLTRB(0, 0, S_.PAPER_W, S_.PAPER_H), fill((20, 30, 70), 0.22))
            c.restore()
            if S.get("magnet", 1.0) > 0:
                S_.draw_magnet(c, S_.FRIDGE_SPOT[0] + off, S_.FRIDGE_SPOT[1] - 280 - off * 0.1, "pumpkin")
        for a in self.others.values():
            if a.kind in ("cat", "mom") and not a.raw("hidden", tq, False):
                draw_actor(c, a, tq)
        hand = S.get("hand", -1.0)
        if hand >= 0:
            draw_mom_arm(c, hand)
        c.restore()
        if self.morning:
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill((0, 0, 0), 1.0, lin_grad((0, 0), (W * 0.7, H * 0.7),
                                                                                    [(255, 214, 150, 0.55), (255, 200, 140, 0.12)]),
                                                             blend=skia.BlendMode.kScreen))
            for k in range(3):  # sunbeams
                x0 = -200 + k * 260
                c.drawPath(poly([(x0, -100), (x0 + 140, -100), (x0 + 900, H), (x0 + 600, H)]),
                           fill((255, 230, 170), 0.10, blur=30, blend=skia.BlendMode.kScreen))
        else:
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill((0, 0, 0), 1.0, lin_grad((0, 0), (W, 0),
                                                                                    [(255, 140, 50, 0.10), (20, 30, 80, 0.15)]),
                                                             blend=skia.BlendMode.kSrcOver))
        S_.vignette(c, 0.5 if self.morning else 0.6)


def draw_mom_arm(c, u):
    """Mom's sleeve and hand reaching in from the right to pin the page (u: 0 out .. 1 placed .. 2 out)."""
    k = u if u <= 1 else 2 - u
    hx = lerp(1500, 760, k)
    hy = lerp(1100, 900, k)
    sleeve = skia.Path()
    sleeve.moveTo(1500, 1400)
    sleeve.quadTo(1300, 1150, hx + 60, hy + 60)
    c.drawPath(sleeve, stroke((58, 38, 82), 120))
    c.drawPath(sleeve, stroke((150, 128, 176), 26, 0.7))
    with Xf(c, hx, hy, rot=-150, sx=1.6):
        c.drawOval(skia.Rect.MakeLTRB(-22, -16, 22, 26), fill(SKIN))
        for i in range(4):
            fx = -15 + i * 10
            p = skia.Path()
            p.moveTo(fx, 16)
            p.quadTo(fx + 3, 40, fx + 6, 60 - abs(i - 1.5) * 8)
            c.drawPath(p, stroke(SKIN_SH, 13))
            c.drawPath(p, stroke(SKIN, 10))


# ------------------------------------------------------------------ exterior
class ExteriorView:
    def __init__(self, state):
        self.state = state

    def draw(self, c, t, cam):
        tq = q(t)
        S = {k: (v.at(tq) if hasattr(v, "at") else v) for k, v in self.state.items()}
        c.save()
        cam.apply(c, 0.4)
        S_.draw_sky(c, (-600, -800, W + 600, H + 400), (700, 520, 230), tq)
        S_.draw_moon(c, 700, 520, 230)
        S_.draw_clouds(c, tq, (-400, -200, W + 400, 900), (700, 520, 230))
        S_.draw_bats(c, tq, (-200, 150, W + 200, 800), n=4)
        c.restore()
        c.save()
        cam.apply(c, 1.0)
        S_.draw_tree(c, 120, 1720, 1.35)
        c.drawRect(skia.Rect.MakeLTRB(-1000, 1640, W + 1000, H + 1500), fill((10, 8, 18)))
        kiss = S.get("kiss", 0.0)

        def sil(cc, wx, wy):
            col = (40, 18, 22)
            # bed + sleeping child
            cc.drawRect(skia.Rect.MakeLTRB(wx - 90, wy + 60, wx + 90, wy + 140), fill(col))
            cc.drawCircle(wx + 40, wy + 50, 20, fill(col))
            # mom bending down
            bend = kiss
            hx = wx - 30 + bend * 40
            hy = wy - 40 + bend * 70
            cc.drawCircle(hx, hy, 26, fill(col))
            cc.drawCircle(hx - 6, hy - 34, 18, fill(col))
            for sd in (-1, 1):
                with Xf(cc, hx + sd * 26, hy - 20, rot=sd * 50):
                    cc.drawRoundRect(skia.Rect.MakeLTRB(-8, -16, 8, 16), 6, 6, fill(col))
            cc.drawPath(poly([(hx - 30, hy + 20), (hx + 20, hy + 26), (wx + 10, wy + 140), (wx - 90, wy + 140)]), fill(col))
        S_.draw_house(c, 600, 1660, 1.05, tq, 1.0, sil)
        fence_y = 1700
        for i in range(-2, 14):
            with Xf(c, i * 90, fence_y, rot=(i % 3 - 1) * 6):
                c.drawPath(poly([(-9, 0), (-9, -110), (0, -128), (9, -110), (9, 0)]), fill((8, 6, 14)))
        c.drawRect(skia.Rect.MakeLTRB(-1000, fence_y - 70, W + 1000, fence_y - 58), fill((8, 6, 14)))
        c.restore()
        S_.vignette(c, 0.6)
