"""Choreography: staging, cameras and acting for every shot."""
import math
import skia
import gfx
from gfx import (fill, stroke, alpha, shade, Track, ease_io, ease_out, ease_in, ease_back, smooth, clamp, lerp, wobble,
                 rad_grad, lin_grad, ellipse, font, text_width)
import rig
from engine import Actor, LN, LNB, M, SH, TL
import sets as S

CAST = rig.make_cast()


def blurred(cv, ctx, fn, *args, **kw):
    b = ctx.get("blur", 0.0)
    if b > 0.05:
        cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(b, b, skia.TileMode.kClamp)))
        fn(cv, *args, **kw)
        cv.restore()
    else:
        fn(cv, *args, **kw)


def cam_track(v0):
    return Track(v0, dur=1.0, ease=ease_io)


# ======================================================================= CLASSROOM
class ClassScene:
    sets = ("class_kids_wide", "class_kids_close", "class_kids_after", "class_teacher", "class_teacher_react")

    def __init__(self):
        c = CAST
        T0 = 0.0
        km = self.km = Actor(c["kidme"], seed=11, kid_laugh=True, x=300, y=1250,
                             expr=("attentive", dict(smile=0.15)), look=(0.0, 0.45), nod=0.15,
                             armL=(-0.55, -0.02, 1.0, "mitt"), armR=(0.5, -0.05, 1.0, "fist", ("pencil", 0.9, 0.5)))
        kd = self.kd = Actor(c["kiddanny"], seed=23, kid_laugh=True, x=780, y=1250,
                             expr=("neutral", dict(smile=0.2)), look=(-0.7, -0.3), turn=-0.25, lean=-3,
                             armL=(-0.5, -0.05, 1.0, "mitt"), armR=(0.55, -0.05, 1.0, "mitt"))
        tc = self.tc = Actor(c["teacher"], seed=31, x=540, y=1310, expr=("neutral", dict(smile=0.0)), look=(0.0, 0.5), nod=0.35,
                             armL=(-0.6, -0.3, 1.0, "mitt"), armR=(0.6, -0.3, 1.0, "mitt"))
        # --- wide: restless kids, then "Eyes forward"
        kd.at(0.6, 0.5, look=(-0.9, -0.5), turn=-0.35)
        kd.at(1.0, 0.25, expr=("neutral", dict(smile=0.3, brow=0.2)))
        km.at(0.8, 0.3, look=(0.1, 0.55))
        tcall = M["teacher_call"]
        for a in (km, kd):
            a.at(tcall + 0.15, 0.2, look=(0.0, -0.25), turn=0.0, nod=-0.05, lean=0, bob=-0.05,
                 expr=("attentive", dict(lid=1.12, brow=0.4, smile=0.05)))
            a.at(tcall + 0.6, 0.4, bob=0.0)
        km.at(tcall + 0.2, 0.25, armR=(0.42, -0.05, 1.0, "fist", ("pencil", 0.9, 0.5)))
        # --- teacher: "Not. One. Sound."
        t1 = M["not_one_sound"]
        c0, c1, c2 = LN("teacher", "Not.", 0), LN("teacher", "Not.", 1), LN("teacher", "Not.", 2)
        tc.at(SH["class_teacher"][0] + 0.1, 0.5, look=(0.0, -0.1), nod=0.25, expr=("stern", dict(lid=0.9)))
        tc.at(c0 - 0.25, 0.3, armR=(1.45, -3.6, -1.0, "point"), lean=3, nod=0.15)
        tc.at(c1 - 0.1, 0.25, nod=0.22, lean=4, expr=("stern", dict(lid=0.75, brow=-0.35)))
        tc.at(c2 - 0.1, 0.3, nod=0.1, lean=5, expr=("stern", dict(lid=0.62, brow=-0.45, lid_tilt=0.5)))
        tc.at(c2 + 1.0, 0.5, armR=(0.6, -0.3, 1.0, "mitt"), lean=0)
        tc.at(SH["class_teacher"][1] - 0.6, 0.3, nod=0.2)
        tc.blink_at(SH["class_teacher"][1] - 0.4)
        # --- kids close: glances, eye contact, held laughter
        g1, g2, ec = M["glance1"], M["glance2"], M["eye_contact"]
        for a in (km, kd):
            a.at(SH["class_kids_close"][0], 0.01, look=(0.0, -0.25), expr=("attentive", dict(press=0.4, lid=1.05, brow=0.15)))
        km.at(g1, 0.45, look=(0.85, -0.05), fixed_gaze=1.0)
        km.at(g1 + 0.5, 0.3, turn=0.12)
        kd.at(g2, 0.45, look=(-0.85, -0.05), fixed_gaze=1.0)
        kd.at(g2 + 0.5, 0.3, turn=-0.12)
        for a in (km, kd):
            a.at(ec, 0.18, expr=("attentive", dict(press=0.8, lid=1.18, brow=0.55, smile=0.2)))
            a.blink_at(ec + 0.45)
            a.at(ec + 0.7, 0.4, expr=("attentive", dict(press=1.0, lid=1.0, brow=0.35, smile=0.3)))
        ps = M["puff_start"]
        for a, d in ((km, 0.0), (kd, 0.25)):
            a.at(ps + d, 2.6, ease=ease_io, expr=("hold_laugh", dict(puff=0.6, tears=0.35)), shake=0.12)
            a.at(ps + 2.8 + d, 1.4, expr=("hold_laugh", dict(puff=0.95, tears=0.8, brow=0.75, blush=0.85, lid=0.7)), shake=0.3)
        # danny looks away trying to survive, then back
        kd.at(ps + 0.9, 0.25, look=(0.35, -0.3), turn=0.15)
        kd.at(ps + 2.0, 0.2, look=(-0.85, -0.05), turn=-0.12)
        km.at(ps + 3.0, 0.2, look=(0.85, 0.05))
        sn, bu = M["snort"], M["burst"]
        kd.at(sn, 0.06, nod=-0.25, expr=("hold_laugh", dict(puff=0.1, lid=1.2, brow=0.9, open=0.15, press=0.0, tears=0.8, blush=0.9)))
        kd.at(sn + 0.15, 0.15, nod=-0.05)
        km.at(sn + 0.1, 0.1, expr=("hold_laugh", dict(puff=1.0, lid=1.2, brow=1.0, tears=0.9, blush=1.0)))
        km.at(bu, 0.15, armR=(0.12, -2.05, -1.0, "mitt"), lean=6, shake=0.0, fixed_gaze=0.0)
        kd.at(bu, 0.15, armL=(-0.25, -0.45, 1.0, "mitt"), armR=(0.3, -0.4, 1.0, "mitt"), lean=-8, shake=0.0, fixed_gaze=0.0)
        for a in (km, kd):
            a.at(bu, 0.1, expr=("laughing", dict(tears=0.6, blush=0.8)))
        # --- teacher reacts
        tr0, tr1 = SH["class_teacher_react"]
        tc.at(tr0, 0.01, look=(0.0, -0.05), nod=0.05, expr=("unimpressed", dict(browR=0.65)))
        tc.blink_at(tr0 + 0.9)
        tc.at(tr0 + 1.4, 0.6, armL=(0.55, -1.25, 1.0, "mitt"), armR=(-0.5, -1.35, 1.0, "mitt"))
        tc.blink_at(tr0 + 3.2)
        tc.at(tr0 + 4.6, 0.5, expr=("unimpressed", dict(browR=0.4, smirk=0.35, smile=0.12)))  # almost smiles
        tc.at(tr0 + 5.6, 0.4, expr=("unimpressed", dict(browR=0.55, smirk=-0.1)))
        # --- kids after: recomposing, peek, giggle, tender look
        ka = SH["class_kids_after"][0]
        for a in (km, kd):
            a.at(ka, 0.01, expr=("attentive", dict(press=0.7, lid=0.95, brow=0.25, tears=0.4, blush=0.5, smile=0.2)), look=(0.0, -0.25),
                 lean=0, fixed_gaze=0.0, turn=0.0)
        km.at(ka, 0.01, armR=(0.42, -0.05, 1.0, "fist", ("pencil", 0.9, 0.5)))
        kd.at(ka, 0.01, armL=(-0.5, -0.05, 1.0, "mitt"), armR=(0.55, -0.05, 1.0, "mitt"))
        r0 = LN("narr", "But a friend")[0]
        for a in (km, kd):
            a.at(r0 + 0.8, 0.5, expr=("attentive", dict(press=1.0, brow=-0.15, lid=0.9, smile=0.1, blush=0.3)), nod=0.05)
        pk = M["peek_again"]
        kd.at(pk - 0.7, 0.35, look=(-0.85, 0.0), fixed_gaze=1.0)
        km.at(pk - 0.3, 0.3, look=(0.85, 0.0), fixed_gaze=1.0)
        lv = LN("narr", "Maybe that's what")
        k_love = LN("narr", "Maybe that's what", 1)
        for a, tt in ((km, 0.0), (kd, 0.1)):
            a.at(pk + 1.4 + tt, 0.6, expr=("tender", dict(smile=0.55, lower=0.35, tears=0.3, blush=0.4)))
            a.at(k_love, 0.8, expr=("tender", dict(smile=0.65, lower=0.4, tears=0.35, blush=0.5, brow_ang=0.35)))
        km.at(k_love + 0.3, 0.8, turn=0.25, tilt=6)
        kd.at(k_love + 0.4, 0.8, turn=-0.25, tilt=-5)
        self.actors = [km, kd]

        self.cam = {
            "class_kids_wide": cam_track((540, 1010, 1.17)).key(0.0, (540, 1015, 1.24), 4.5),
            "class_kids_close": cam_track((540, 990, 1.42)).key(SH["class_kids_close"][0], (540, 985, 1.62), 10.0),
            "class_teacher": cam_track((540, 1040, 1.4)).key(c0 - 0.3, (560, 990, 1.62), 3.6),
            "class_teacher_react": cam_track((540, 1010, 1.45)).key(tr0, (540, 1000, 1.55), 7.0),
            "class_kids_after": cam_track((540, 1000, 1.36)).key(lv[0], (540, 960, 1.75), lv[1] - lv[0] + 0.5),
        }

    def draw(self, cv, t, shot, ctx):
        if shot.startswith("class_teacher"):
            blurred(cv, ctx, S.class_front_bg, t)
            self.tc.draw(cv, t)
            S.class_front_fg(cv, t)
            if shot == "class_teacher_react":
                self.hug_bubble(cv, t)
        else:
            blurred(cv, ctx, S.class_back_bg, t)
            for a in self.actors:
                a.draw(cv, t, part="body")
            S.class_back_fg(cv, t)
            for a in self.actors:
                a.draw(cv, t, part="arms")

    def hug_bubble(self, cv, t):
        t0 = LN("narr", "If my mom")[0] + 0.2
        t1 = LN("narr", "No one laughs")[1] + 0.3
        if t < t0 or t > t1 + 0.4:
            return
        s = ease_back(clamp((t - t0) / 0.45)) * (1 - smooth(clamp((t - t1) / 0.4)))
        if s <= 0.01:
            return
        cx, cy = 300, 560
        cv.save()
        cv.translate(cx, cy)
        cv.scale(s, s)
        for (x, y, r) in [(-170, 20, 120), (-60, -60, 140), (90, -50, 130), (180, 40, 110), (60, 90, 130), (-90, 95, 120)]:
            cv.drawCircle(x, y, r, fill("#ffffff"))
        for (x, y, r) in [(-170, 20, 120), (-60, -60, 140), (90, -50, 130), (180, 40, 110), (60, 90, 130), (-90, 95, 120)]:
            cv.drawCircle(x, y, r, stroke(alpha("#b7a9c9", 0.8), 6))
        for (x, y, r) in [(-170, 20, 117), (-60, -60, 137), (90, -50, 127), (180, 40, 107), (60, 90, 127), (-90, 95, 117)]:
            cv.drawCircle(x, y, r, fill("#ffffff"))
        for (x, y, r) in [(140, 260, 34), (200, 330, 20)]:
            cv.drawCircle(x, y, r, fill("#ffffff"))
            cv.drawCircle(x, y, r, stroke(alpha("#b7a9c9", 0.8), 5))
        # mom + kid hugging
        tt = t - t0
        sway = 4 * math.sin(tt * 2.2)
        cv.save()
        cv.rotate(sway)
        mom_body = ellipse(30, 120, 85, 110)
        cv.drawPath(mom_body, fill("#6fa8dc"))
        cv.drawPath(mom_body, stroke("#3d6e99", 5))
        cv.drawCircle(30, -40, 60, fill("#f3c9a8"))
        cv.drawCircle(30, -40, 60, stroke("#a5765a", 5))
        cv.drawCircle(50, -112, 30, fill("#5a3a2a"))
        hair = skia.Path()
        hair.addArc(skia.Rect.MakeLTRB(-30, -100, 90, 20), 180, 180)
        cv.drawPath(hair, fill("#5a3a2a"))
        for side in (-1, 1):
            arc = skia.Path()
            arc.moveTo(30 + side * 14 - 10, -40)
            arc.quadTo(30 + side * 14, -50, 30 + side * 14 + 10, -40)
            cv.drawPath(arc, stroke("#4a2a20", 4))
        sm = skia.Path()
        sm.moveTo(15, -18)
        sm.quadTo(30, -5, 45, -18)
        cv.drawPath(sm, stroke("#4a2a20", 4))
        kid = ellipse(-70, 150, 60, 80)
        cv.drawPath(kid, fill("#f0b030"))
        cv.drawPath(kid, stroke("#a07010", 5))
        cv.drawCircle(-70, 40, 48, fill("#f6cfae"))
        cv.drawCircle(-70, 40, 48, stroke("#a5765a", 5))
        kh = skia.Path()
        kh.addArc(skia.Rect.MakeLTRB(-125, -12, -15, 92), 170, 200)
        cv.drawPath(kh, fill("#7a3f26"))
        for side in (-1, 1):
            arc = skia.Path()
            arc.moveTo(-70 + side * 14 - 9, 42)
            arc.quadTo(-70 + side * 14, 32, -70 + side * 14 + 9, 42)
            cv.drawPath(arc, stroke("#4a2a20", 4))
        arm = skia.Path()
        arm.moveTo(-20, 120)
        arm.quadTo(20, 175, 70, 120)
        cv.drawPath(arm, stroke("#a07010", 30))
        cv.drawPath(arm, stroke("#f0b030", 22))
        cv.restore()
        hs = 1 + 0.12 * math.sin(tt * 6)
        hp = skia.Path()
        hx, hy = 140, -150
        hp.moveTo(hx, hy + 20 * hs)
        hp.cubicTo(hx - 50 * hs, hy - 15 * hs, hx - 25 * hs, hy - 50 * hs, hx, hy - 25 * hs)
        hp.cubicTo(hx + 25 * hs, hy - 50 * hs, hx + 50 * hs, hy - 15 * hs, hx, hy + 20 * hs)
        cv.drawPath(hp, fill("#ff5f7a"))
        cv.restore()


# ======================================================================= BACKYARD
class YardScene:
    def __init__(self):
        c = CAST
        me = self.me = Actor(c["me"], seed=41, x=225, y=1440, expr=("smile", dict(smile=0.35)), look=(0.2, 0.55), nod=0.2,
                             turn=0.15, armL=(-0.6, -0.2, 1.0, "mitt"), armR=(0.55, -0.2, 1.0, "mitt"))
        f1 = self.f1 = Actor(c["f1"], seed=53, x=478, y=1440, expr="smile", look=(0.6, 0.0), turn=0.35,
                             armL=(-0.6, -0.2, 1.0, "mitt"), armR=(0.6, -0.2, 1.0, "fist", ("can", 0.9, 0.0)))
        f2 = self.f2 = Actor(c["f2"], seed=67, x=718, y=1440, expr="grin", look=(-0.6, 0.0), turn=-0.35,
                             armL=(-0.55, -0.2, 1.0, "fist", ("corn", 0.8, 0.0)), armR=(0.6, -0.2, 1.0, "mitt"))
        dn = self.dn = Actor(c["danny"], seed=79, x=925, y=1330, scale=0.95, expr="smile", look=(-0.3, 0.6), nod=0.25, turn=-0.25,
                             armL=(-0.75, -0.6, 1.0, "fist", ("spatula", 1.0, -0.3)), armR=(0.65, -0.45, 1.0, "mitt"))
        self.actors = [dn, me, f1, f2]
        # ---- wide: party life
        w0, w1 = SH["yard_wide"]
        f1.at(w0 + 0.5, 0.4, expr=("grin", dict(open=0.0, smile=0.7)), nod=-0.05)
        f2.at(w0 + 0.9, 0.3, nod=0.12)
        f2.at(w0 + 1.3, 0.3, nod=-0.02)
        f2.at(w0 + 3.0, 0.3, nod=0.1)
        f2.at(w0 + 3.3, 0.3, nod=0.0)
        me.at(w0 + 1.0, 0.5, armR=(0.4, -0.55, 1.0, "fist"))
        me.at(w0 + 1.8, 0.5, armR=(0.55, -0.2, 1.0, "mitt"))
        kd = LN("narr", "Twenty years later", 1)
        dn.at(kd - 0.2, 0.35, look=(-0.2, -0.1), nod=0.0, expr=("grin", dict(open=0.12)))
        dn.at(kd + 0.6, 0.4, armR=(0.55, -3.35, -1.0, "mitt"))  # salute
        dn.at(kd + 1.6, 0.4, armR=(0.65, -0.45, 1.0, "mitt"), expr="smile")
        tt = LN("narr", "Two tours", 1)
        dn.at(tt - 0.1, 0.3, look=(0.1, 0.6), nod=0.25)
        me.at(tt + 0.5, 0.4, look=(0.6, -0.4), turn=0.3)  # glance at Danny
        # ---- Danny: flip + jab
        fl = M["flip"]
        dn.at(fl - 0.25, 0.15, armL=(-0.6, -1.4, 1.0, "fist", ("spatula", 1.0, 0.4)))
        dn.at(fl, 0.12, armL=(-0.75, -0.6, 1.0, "fist", ("spatula", 1.0, -0.5)))
        dn.at(fl + 0.4, 0.4, look=(-0.7, 0.55), turn=-0.3, nod=0.2, expr=("smug", dict(smile=0.4)))
        b0, b1 = LN("danny", "burned the buns")
        dn.at(b0 + 0.2, 0.3, expr=("smug", dict(smile=0.25, brow=0.3, browR=0.3)))
        dn.at(b0 + 0.4, 0.25, tilt=-6)
        dn.at(b0 + 0.75, 0.25, tilt=6)
        dn.at(b0 + 1.1, 0.25, tilt=-2)
        pt = M["point"]
        dn.at(pt, 0.3, armL=(-1.95, -2.2, -1.0, "fist", ("spatula", 1.0, -1.45)), look=(-0.8, 0.1), turn=-0.4, nod=0.0,
              expr=("grin", dict(open=0.0, smile=0.85, brow=0.45)))
        dn.at(pt + 2.2, 0.6, armL=(-0.75, -0.6, 1.0, "fist", ("spatula", 1.0, -0.3)))
        # ---- table: friends expect a comeback; me tired
        tb0, tb1 = SH["yard_table"]
        for a, lk in ((f1, (-0.75, 0.0)), (f2, (-0.8, 0.0))):
            a.at(tb0 + 0.6, 0.4, look=lk, expr=("grin", dict(open=0.0, smile=0.7, brow=0.45)))
        f1.at(tb0 + 0.6, 0.4, turn=-0.3)
        f2.at(tb0 + 0.6, 0.4, turn=-0.45)
        f2.at(tb0 + 3.5, 0.3, expr=("grin", dict(open=0.0, smile=0.75, brow=0.6, browL=0.2)))
        me.at(tb0 + 0.3, 0.6, look=(0.15, 0.6), turn=0.1, nod=0.25, expr=("tired", dict(smile=0.1)), shrug=-0.2)
        # ---- me close: tired, forgot to exaggerate
        mc0 = SH["yard_me_close"][0]
        me.at(mc0 + 1.0, 1.2, expr=("tired", dict(lid=0.5, smile=0.0, tears=0.25)), nod=0.32)
        cf = M["confess"]
        me.at(cf - 0.5, 0.6, shrug=0.5, look=(0.05, 0.75))
        me.at(cf + 0.3, 0.6, shrug=0.0, expr=("ashamed", dict(lid=0.6, tears=0.35)))
        me.at(cf + 2.0, 0.6, expr=("ashamed", dict(lid=0.55, tears=0.45, press=0.6)))
        # ---- silence: everybody freezes
        si = M["silence"]
        dn.at(si - 0.4, 0.2, armL=(-0.75, -0.6, 1.0, "fist", ("spatula", 1.0, -0.3)), look=(-0.8, 0.25), turn=-0.4)
        dn.at(si + 0.3, 1.8, ease=ease_in, expr=("neutral", dict(smile=0.05, brow=0.15)))
        f1.at(si - 0.6, 0.5, armR=(0.15, -2.75, -1.0, "fist", ("can", 0.9, 0.2)))  # mid-sip
        f1.at(si - 0.1, 0.2, fixed_gaze=1.0, look=(-0.8, 0.0), expr=("neutral", dict(lid=1.15, brow=0.35, smile=0.0)))
        f1.at(si + 0.9, 0.08, look=(0.6, -0.1))
        f1.at(si + 1.5, 0.08, look=(-0.8, 0.0))
        f1.at(si + 2.3, 0.08, look=(0.6, -0.1))
        f2.at(si + 0.1, 1.6, ease=ease_io, armL=(-0.55, -0.15, 1.0, "fist", ("corn", 0.8, 0.0)), fixed_gaze=1.0,
              expr=("neutral", dict(brow=0.55, lid=1.08, smile=-0.05, press=0.5)))
        f2.at(si + 1.2, 0.1, look=(-0.6, -0.35))
        f2.at(si + 2.0, 0.1, look=(-1.0, 0.0))
        me.at(si, 0.01, look=(0.05, 0.75))
        # ---- danny close: concern dawning
        dc0 = SH["yard_danny_close"][0]
        dn.at(dc0 + 0.3, 0.8, expr=("worried", dict(smile=0.0, brow=0.1, brow_ang=0.45, lid=1.0)), look=(-0.85, 0.3))
        dn.at(dc0 + 2.4, 0.3, expr=("worried", dict(open=0.12, brow_ang=0.55, lid=1.02)))
        dn.at(dc0 + 2.9, 0.3, expr=("worried", dict(open=0.0, brow_ang=0.55, press=0.4)), look=(-0.3, 0.6))
        dn.blink_at(dc0 + 3.2)
        dn.at(dc0 + 4.4, 0.5, look=(-0.85, 0.3), expr=("worried", dict(brow_ang=0.75, press=0.3, lid=0.95)))
        # ---- alchemy (after bridge)
        fp0 = SH["yard_me_flip"][0]
        me.at(fp0, 0.01, expr=("ashamed", dict(lid=0.55, tears=0.4)), look=(0.05, 0.75), nod=0.32)
        me.at(fp0 + 0.3, 1.1, ease=ease_io, nod=0.0, look=(0.6, -0.2), turn=0.3)
        me.at(fp0 + 0.6, 0.9, expr=("smug", dict(smile=0.4, lid=0.85, tears=0.2, browR=0.5)))
        me.at(fp0 + 1.0, 0.4, armR=(1.75, -2.9, -1.0, "fist", ("cup", 0.9, 0.0)))  # raise cup
        p1 = LN("me", "I mean")
        me.at(p1[0] + 0.9, 0.35, armL=(0.05, -1.5, 1.0, "mitt"))  # hand on chest
        ga = M["gesture_all"]
        me.at(ga + 0.2, 0.5, armL=(-0.6, -0.25, 1.0, "mitt"), armR=(2.0, -2.0, -1.0, "mitt"), turn=0.5, look=(0.85, 0.0),
              expr=("grin", dict(open=0.0, smile=0.75, brow=0.4)))
        f1.at(ga + 0.3, 0.3, look=(-0.85, 0.05), fixed_gaze=0.0, armR=(0.6, -0.2, 1.0, "fist", ("can", 0.9, 0.0)),
              expr=("neutral", dict(smile=0.25, brow=0.3)))
        f2.at(ga + 0.5, 0.3, look=(-0.9, 0.0), fixed_gaze=0.0, expr=("neutral", dict(smile=0.3, brow=0.35)))
        pl = LN("me", "On a")
        me.at(pl[0] + 0.1, 0.6, armL=(-1.9, -2.6, -1.0, "mitt"), armR=(1.9, -2.6, -1.0, "mitt"), look=(0.0, -0.8), nod=-0.25, turn=0.0,
              expr=("grin", dict(open=0.0, smile=0.6, brow=0.7)))
        bp = M["best_pile"]
        me.at(bp, 0.5, armL=(-0.6, -0.25, 1.0, "mitt"), armR=(0.1, -1.55, 1.0, "mitt"), look=(0.7, -0.1), nod=0.05, turn=0.35,
              expr=("warm", dict(smile=0.7, lower=0.4)))
        k2 = LN("me", "and honestly", 1)
        me.at(k2, 0.4, tilt=7, expr=("warm", dict(smile=0.85, lower=0.45, brow=0.3)))
        # danny reacting during the speech
        dn.at(fp0 + 1.5, 0.5, expr=("neutral", dict(brow=0.5, lid=1.1, smile=0.0)), look=(-0.85, 0.3))
        dn.at(ga + 0.8, 0.6, expr=("neutral", dict(brow=0.6, smile=0.3, lid=1.05)))
        dn.at(bp + 0.5, 0.5, expr=("smile", dict(smile=0.6, brow=0.5)))
        # ---- big laugh
        fs = M["friend_snort"]
        f1.at(fs, 0.08, nod=-0.2, expr=("surprised", dict(open=0.1, round=0.2)), armR=(0.2, -2.6, -1.0, "mitt"))
        al = M["all_laugh"]
        f1.at(al, 0.2, nod=0.0, armR=(0.15, -2.55, -1.0, "mitt"))
        f2.at(al + 0.2, 0.15, armR=(0.6, -0.1, 1.0, "fist"), lean=6)  # table slap
        f2.at(al + 0.45, 0.15, armR=(0.6, -0.6, 1.0, "fist"))
        f2.at(al + 0.7, 0.15, armR=(0.6, -0.1, 1.0, "fist"))
        dn.at(al, 0.25, lean=-16, armR=(0.1, -0.7, 1.0, "mitt"))
        dn.at(al + 1.2, 0.4, lean=0)
        po = LN("danny", "poet")
        dn.at(po[0] - 0.1, 0.3, armL=(-1.95, -2.2, -1.0, "fist", ("spatula", 1.0, -1.45)), look=(-0.8, 0.1), turn=-0.4)
        dn.at(po[1] + 0.3, 0.4, armL=(-0.75, -0.6, 1.0, "fist", ("spatula", 1.0, -0.3)), armR=(0.65, -0.45, 1.0, "mitt"))
        dn.at(po[1] + 0.8, 0.3, armR=(0.3, -3.3, -1.0, "fist"))  # wipe eye
        dn.at(po[1] + 1.6, 0.4, armR=(0.65, -0.45, 1.0, "mitt"))
        sw = LN("narr", "Same words")
        for a in (dn, me, f1, f2):
            a.at(sw[0] + 0.8, 0.6, expr=("warm", dict(smile=0.65)))
        me.at(sw[0] + 1.6, 0.5, look=(0.7, -0.45), turn=0.35, armR=(0.55, -0.2, 1.0, "mitt"), armL=(-0.6, -0.2, 1.0, "mitt"))
        dn.at(sw[0] + 2.2, 0.5, look=(-0.8, 0.35), nod=0.15)
        dn.at(sw[0] + 3.2, 0.25, nod=0.3)
        dn.at(sw[0] + 3.5, 0.25, nod=0.12)

        d0 = SH["yard_danny"][0]
        self.cam = {
            "yard_wide": cam_track((560, 1090, 1.1)).key(SH["yard_wide"][0], (590, 1080, 1.2), 9.0),
            "yard_danny": cam_track((870, 1040, 1.85)).key(d0, (860, 1020, 2.05), 5.4),
            "yard_table": cam_track((470, 1190, 1.3)).key(tb0, (460, 1185, 1.38), 8.5),
            "yard_me_close": cam_track((240, 1110, 2.6)).key(mc0, (240, 1115, 3.0), 8.0),
            "yard_silence": cam_track((570, 1100, 1.12)).key(si, (570, 1100, 1.16), 3.4),
            "yard_danny_close": cam_track((905, 985, 2.6)).key(dc0, (900, 985, 2.95), 7.0),
            "yard_me_flip": cam_track((245, 1110, 2.45)).key(ga, (360, 1150, 1.7), 0.9).key(bp, (285, 1110, 2.3), 1.2),
            "yard_laugh": cam_track((570, 1090, 1.1)).key(al + 3.0, (560, 1080, 1.28), 6.0),
        }

    def draw(self, cv, t, shot, ctx):
        blurred(cv, ctx, S.yard_bg, t)
        solo_danny = shot in ("yard_danny", "yard_danny_close")
        solo_me = shot == "yard_me_close"
        sitters = [a for a in (self.me, self.f1, self.f2) if not solo_danny and (not solo_me or a is self.me)]
        if not solo_me:
            S.smoke(cv, 905, 1305, t)
            self.dn.draw(cv, t)
            S.grill(cv, 925, 1345, t, with_smoke=False)
        for a in sitters:
            a.draw(cv, t, part="body")
        S.picnic_table(cv, t)
        for a in sitters:
            a.draw(cv, t, part="arms")


# ======================================================================= MIND BRIDGE
class BridgeScene:
    def __init__(self):
        c = CAST
        b0, b1 = SH["bridge_wide"][0], SH["bridge_bored"][1]
        em = self.em = Actor(c["emb"], seed=91, x=540, y=1520, scale=1.7, expr="panic", talk_gain=1.15,
                             armL=(-1.3, 0.2, -1.0, "mitt"), armR=(1.3, 0.2, -1.0, "mitt"), run=1.0)
        db = self.db = Actor(c["doubt"], seed=97, x=195, y=1185, scale=1.5, expr="unimpressed", look=(0.7, 0.2), turn=0.35,
                             armL=(-0.8, 2.55, 1.0), armR=(0.8, 2.55, 1.0))
        an = self.an = Actor(c["anger"], seed=101, x=880, y=1140, scale=1.45, expr=("angry", dict(press=0.2)), look=(-0.7, 0.2),
                             turn=-0.35, armL=(-1.05, 2.1, 1.0), armR=(1.05, 2.1, 1.0))
        bo = self.bo = Actor(c["bored"], seed=103, x=860, y=1655, scale=1.4, expr=("deadpan", dict(lid=0.5)), look=(-0.5, 0.3),
                             turn=-0.3, lean=-8, armL=(-1.15, 2.45, 1.0), armR=(1.15, 2.45, 1.0), pose="sit")
        self.actors = [db, an, bo, em]
        # embarrassment runs in panic, then stops facing camera
        o1 = LN("emb", "Oh my God")
        o2 = LN("emb", "Three people")
        em.at(o1[1] + 0.1, 0.4, run=0.0, x=540, expr=("panic", dict(open=0.2)))
        em.at(o1[1] + 0.1, 0.3, armL=(-0.72, 1.5, -1.0, "mitt"), armR=(0.72, 1.5, -1.0, "mitt"))  # hands on cheeks
        em.at(o2[0] + 0.1, 0.3, armR=(1.1, 0.1, -1.0, "mitt"), armL=(-0.72, 1.5, -1.0, "mitt"))
        em.at(LN("emb", "Three people", 1), 0.25, armR=(1.0, -0.2, -1.0, "mitt"), expr=("panic", dict(brow=1.0, lid=1.25, blush=1.0)))
        # watchers
        db.at(b0 + 0.3, 0.3, look=(0.5, 0.3))
        an.at(b0 + 0.6, 0.3, look=(-0.4, 0.3), expr=("angry", dict(press=0.5)))
        bo.at(b0 + 0.2, 0.0, turn=-0.3)
        # doubt
        d0 = SH["bridge_doubt"][0]
        dl = LN("doubt", "Well")
        db.at(d0, 0.01, look=(0.35, 0.0), turn=0.15)
        db.at(d0 + 0.05, 0.35, armR=(0.18, 1.18, -1.0, "point"))  # push glasses
        db.at(d0 + 0.45, 0.25, armR=(0.18, 1.08, -1.0, "point"))
        db.at(d0 + 0.75, 0.35, armR=(0.8, 2.55, 1.0))
        db.at(LN("doubt", "Well", 1) - 0.1, 0.3, expr=("unimpressed", dict(browR=0.8, smirk=0.3)), look=(0.6, -0.1))
        db.blink_at(dl[1] + 0.25)
        # anger
        a0 = SH["bridge_anger"][0]
        an.at(a0, 0.01, look=(-0.2, 0.0), turn=-0.15)
        an.at(a0 + 0.25, 0.25, armL=(-0.12, 1.85, 1.0, "fist"), armR=(0.12, 1.85, 1.0, "mitt"), lean=0)
        an.at(a0 + 0.8, 0.2, shake=0.4)
        an.at(a0 + 1.3, 0.2, shake=0.0)
        al = LN("anger", "Want me")
        an.at(al[0] - 0.1, 0.3, lean=6, expr=("angry", dict(smile=0.45, press=0.0, brow=-0.1, lid=0.9)), look=(-0.1, -0.05),
              armL=(-0.9, 1.95, 1.0, "fist"), armR=(0.9, 1.95, 1.0, "fist"))
        # boredom
        bb0 = SH["bridge_bored"][0]
        bl = LN("bored", "Nope")
        bo.at(bb0, 0.01, turn=-0.6)
        bo.at(bb0 + 0.1, 0.5, turn=0.45)
        bo.at(bb0 + 0.6, 0.4, turn=-0.1)
        bo.at(bl[0] - 0.1, 0.3, turn=0.0, look=(-0.2, -0.1), expr=("deadpan", dict(lid=0.55)))
        bo.at(LN("bored", "Nope", 1) - 0.4, 0.5, lean=0, expr=("smug", dict(lid=0.72, smile=0.45, smirk=0.8)),
              armR=(1.05, 1.25, -1.0, "point"), look=(-0.3, -0.2))
        bo.at(bl[1] + 0.3, 0.4, armR=(1.15, 2.45, 1.0))
        self.cam = {
            "bridge_wide": cam_track((540, 1150, 1.1)).key(b0, (540, 1170, 1.2), 6.0),
            "bridge_doubt": cam_track((200, 1000, 2.3)).key(d0, (200, 990, 2.55), 3.6),
            "bridge_anger": cam_track((875, 1000, 2.2)).key(a0, (875, 990, 2.5), 2.7),
            "bridge_bored": cam_track((850, 1480, 2.25)).key(bb0, (850, 1475, 2.5), 3.4),
        }
        self.screen_img = None

    def draw(self, cv, t, shot, ctx):
        al = LN("emb", "Oh my God")
        alarm = 1.0 if t < LN("emb", "Three people")[1] else max(0.0, 1 - (t - LN("emb", "Three people")[1]) / 1.0)
        blurred(cv, ctx, S.bridge_bg, t, ctx.get("yard_freeze"), alarm=alarm)
        self.db.draw(cv, t)
        self.an.draw(cv, t)
        S.bridge_consoles(cv, t)
        # emb runs back and forth
        P = self.em.P(t)
        run = P["run"]
        if run > 0.01:
            ph = (t - SH["bridge_wide"][0]) * 1.6
            P["x"] = lerp(P["x"], 540 + 250 * math.sin(ph), run)
            P["flip"] = 1 if math.cos(ph) > 0 else -1
            P["bob"] = -abs(math.sin(t * 14)) * 0.15 * run
            fl = math.sin(t * 13)
            P["armL"] = (-1.2 + 0.3 * fl, -0.4 + 0.5 * fl, 1.0, "mitt")
            P["armR"] = (1.2 - 0.3 * fl, -0.4 - 0.5 * fl, 1.0, "mitt")
            P["tilt"] += 8 * math.sin(t * 7)
        self.em.ch.draw(cv, P, t)
        S.captain_chair(cv, t)
        S.stool(cv, 860, 1680)
        self.bo.draw(cv, t)


# ======================================================================= PORCH
class PorchScene:
    def __init__(self):
        c = CAST
        p0 = SH["porch_wide"][0]
        me = self.me = Actor(c["me"], seed=111, x=390, y=1500, legs="steps", talk_gain=0.72, expr=("tender", dict(smile=0.1, brow_ang=0.3)),
                             look=(0.0, 0.25), turn=0.1, nod=0.1,
                             armL=(-0.3, -0.25, 1.0, "mitt"), armR=(0.3, -0.25, 1.0, "mitt"))
        dn = self.dn = Actor(c["danny"], seed=113, x=700, y=1500, legs="steps", talk_gain=0.68, expr=("neutral", dict(smile=0.05, lid=0.85)),
                             look=(0.1, 0.0), turn=-0.05, nod=0.0, lean=4,
                             armL=(-0.12, -0.45, 1.0, "fist"), armR=(0.12, -0.45, 1.0, "fist"))
        self.actors = [me, dn]
        # wide: hesitation
        me.at(p0 + 0.8, 0.4, look=(0.75, -0.2), turn=0.2)
        me.at(p0 + 1.5, 0.4, look=(0.0, 0.3), turn=0.05)
        hy = LN("me", "Can I say")
        me.at(hy[0] - 0.1, 0.5, turn=0.55, look=(0.7, -0.15), expr=("tender", dict(smile=0.05, brow_ang=0.45, brow=0.15)))
        dn.at(hy[0] + 0.4, 0.6, turn=-0.35, look=(-0.6, 0.0))
        # danny1: wary
        d1 = SH["porch_danny1"][0]
        dn.at(d1, 0.01, turn=-0.35, look=(-0.85, 0.05), expr=("wary", dict(lid=0.9)))
        dn.at(d1 + 0.3, 0.25, nod=0.15)
        dn.at(d1 + 0.6, 0.3, nod=0.0)
        # me1: stung
        m1 = SH["porch_me1"][0]
        me.at(m1, 0.01, look=(0.2, 0.55), turn=0.4, expr=("hurt", dict(smile=0.05)))
        me.at(m1 + 0.4, 0.4, look=(0.85, -0.1), turn=0.55)
        fl = LN("me", "I flipped it")
        me.at(fl[0] + 0.3, 0.4, look=(0.2, 0.5))
        me.at(LN("me", "I flipped it", 1) - 0.3, 0.4, look=(0.85, -0.1), expr=("hurt", dict(tears=0.55, smile=-0.1, brow_ang=0.8)))
        # danny2: defensive
        d2 = SH["porch_danny2"][0]
        dn.at(d2, 0.01, look=(-0.85, 0.05), expr=("wary", dict(lid=0.9)))
        dn.at(d2 + 0.25, 0.35, expr=("stern", dict(press=0.8, brow=-0.3)), look=(0.4, 0.2), turn=0.0)
        dn.at(LN("danny", "how we talk")[0] + 0.3, 0.25, tilt=-4)
        dn.at(LN("danny", "how we talk")[0] + 0.6, 0.25, tilt=4)
        dn.at(LN("danny", "how we talk")[0] + 0.9, 0.25, tilt=0)
        # me2: compassion
        m2 = SH["porch_me2"][0]
        me.at(m2, 0.01, look=(0.85, -0.1), expr=("tender", dict(smile=0.25, tears=0.4, brow_ang=0.6)))
        me.at(m2 + 0.3, 0.3, nod=0.15)
        me.at(m2 + 0.6, 0.3, nod=0.05)
        me.at(LN("me", "I know.[p0.5]Over", 1), 0.5, expr=("tender", dict(smile=0.15, tears=0.5, brow_ang=0.75, lid=0.85)), tilt=5)
        # danny3: the wall comes down
        d3 = SH["porch_danny3"][0]
        dn.at(d3, 0.01, look=(0.4, 0.2), expr=("stern", dict(press=0.8, brow=-0.3)))
        dn.at(d3 + 0.4, 1.0, expr=("sad", dict(press=0.4, lid=0.75, brow_ang=0.6)), look=(0.0, 0.55), nod=0.15)
        dn.at(d3 + 0.9, 0.12, nod=0.22)
        dn.at(d3 + 1.05, 0.15, nod=0.15)
        ov = LN("danny", "Over there")
        dn.at(LN("danny", "Over there", 1) - 0.3, 0.6, expr=("sad", dict(lid=0.7, brow_ang=0.85, tears=0.55)), look=(-0.4, 0.45))
        # me3
        m3 = SH["porch_me3"][0]
        me.at(m3, 0.01, look=(0.85, -0.05), tilt=8, expr=("tender", dict(smile=0.1, tears=0.5, brow_ang=0.7, brow=0.2)))
        # danny4: tears
        d4 = SH["porch_danny4"][0]
        dn.at(d4, 0.01, look=(-0.4, 0.45), expr=("sad", dict(lid=0.72, brow_ang=0.85, tears=0.6)))
        dn.at(d4 + 0.3, 0.4, look=(-0.85, -0.05), expr=("glassy", dict(tears=0.9, brow_ang=0.9, smile=-0.2)))
        dn.blink_at(d4 + 0.9)
        dn.at(d4 + 1.0, 0.6, look=(0.3, -0.6), nod=-0.12)  # looks up/away to hold it in
        dn.at(d4 + 1.2, 0.2, expr=("glassy", dict(tears=0.95, brow_ang=0.95, open=0.08, smile=-0.25)))
        dn.at(d4 + 1.4, 0.2, expr=("glassy", dict(tears=0.95, brow_ang=0.95, open=0.0, smile=-0.3, press=0.3)))
        h4 = LN("danny", "Here...")
        dn.at(h4[0] + 0.2, 0.6, look=(-0.2, 0.5), nod=0.18)
        dn.at(LN("danny", "Here...", 1) - 0.2, 0.5, look=(-0.7, 0.2))
        dn.at(h4[1] - 0.6, 1.6, stream=0.7)
        dn.at(h4[1] + 0.3, 0.6, nod=0.28, look=(0.0, 0.7))
        # ---- resolution
        r0 = SH["porch_two"][0]
        hs = M["hand_shoulder"]
        me.at(r0, 0.01, turn=0.5, look=(0.85, 0.0), expr=("tender", dict(smile=0.2, tears=0.4, brow_ang=0.6)), tilt=0)
        dn.at(r0, 0.01, turn=-0.1, look=(0.0, 0.65), nod=0.28, expr=("glassy", dict(tears=0.8, brow_ang=0.8)), stream=0.7)
        me.at(hs, 0.8, armR=(2.1, -2.0, -1.0, "mitt"), lean=-4)
        dn.at(hs + 0.7, 0.4, look=(-0.6, 0.3), turn=-0.2)  # looks at hand
        dn.at(hs + 1.4, 0.5, look=(-0.85, 0.0), turn=-0.4, nod=0.1)
        y1 = LN("me", "You don't have")
        me.at(y1[0], 0.4, expr=("tender", dict(smile=0.35, tears=0.35, brow_ang=0.5)))
        dl = LN("me", "Just...")
        me.at(LN("me", "Just...", 1) - 0.1, 0.35, expr=("tender", dict(smile=0.45, tears=0.3, brow=0.45, brow_ang=0.3)), tilt=6)
        # danny5
        d5 = SH["porch_danny5"][0]
        dn.at(d5, 0.01, look=(-0.85, 0.0), turn=-0.4, nod=0.1, expr=("glassy", dict(tears=0.8, brow_ang=0.75)))
        dn.at(d5 + 0.3, 0.6, shrug=-0.3, nod=0.2, expr=("relief", dict(tears=0.75, lid=0.7)))
        dn.at(d5 + 0.9, 0.3, nod=0.05, look=(-0.85, 0.0))
        de = LN("danny", "Okay. Deal")
        dn.at(de[1] + 0.2, 0.3, nod=0.15)
        dn.at(de[1] + 0.5, 0.3, nod=0.05, shrug=0.0)
        sk = M["smirk"]
        dn.at(sk - 0.2, 0.5, expr=("smug", dict(smile=0.45, tears=0.6, lid=0.8, brow_ang=0.3)), armR=(0.3, -3.3, -1.0, "fist"))
        dn.at(sk + 0.6, 0.4, armR=(0.12, -0.45, 1.0, "fist"))
        dn.at(LN("danny", "still a piece")[0] + 0.2, 0.4, tilt=-5, expr=("smug", dict(smile=0.6, tears=0.5, brow=0.3)))
        # me4
        m4 = SH["porch_me4"][0]
        me.at(m4, 0.01, expr=("warm", dict(smile=0.6, tears=0.3)), look=(0.85, -0.05), tilt=0)
        me.at(LN("me", "I'm your", 1) - 0.1, 0.4, tilt=9, expr=("grin", dict(open=0.0, smile=0.8, brow=0.45, tears=0.25)))
        # soft laughs, lean together
        sl = M["soft_laugh"]
        dn.at(sl, 0.5, lean=-7, turn=-0.3, stream=0.0)
        me.at(sl + 0.2, 0.6, lean=6, armR=(1.95, -1.7, -1.0, "mitt"))
        # ---- sky: both look up at the stars
        sk0 = SH["sky"][0]
        for a in (me, dn):
            a.at(sk0 + 0.8, 1.2, look=(0.0, -0.9), nod=-0.25, turn=0.0, expr=("warm", dict(smile=0.4)))
        self.cam = {
            "porch_wide": cam_track((545, 1250, 1.42)).key(p0, (545, 1240, 1.55), 5.4),
            "porch_danny1": cam_track((690, 1150, 2.6)).key(d1, (690, 1148, 2.75), 2.3),
            "porch_me1": cam_track((395, 1185, 2.55)).key(m1, (395, 1180, 2.8), 6.6),
            "porch_danny2": cam_track((690, 1150, 2.65)).key(d2, (690, 1148, 2.8), 3.0),
            "porch_me2": cam_track((395, 1185, 2.65)).key(m2, (395, 1180, 2.95), 5.3),
            "porch_danny3": cam_track((690, 1150, 2.7)).key(d3, (690, 1145, 3.1), 6.3),
            "porch_me3": cam_track((395, 1185, 2.95)).key(m3, (395, 1182, 3.05), 1.7),
            "porch_danny4": cam_track((690, 1150, 2.9)).key(d4, (690, 1140, 3.4), 6.2),
            "porch_two": cam_track((545, 1200, 1.62)).key(r0, (545, 1195, 1.78), 7.8),
            "porch_danny5": cam_track((690, 1150, 2.6)).key(d5, (690, 1148, 2.85), 6.0),
            "porch_me4": cam_track((395, 1185, 2.6)).key(m4, (395, 1182, 2.8), 3.3),
            "porch_two_laugh": cam_track((545, 1205, 1.7)).key(sl, (545, 1210, 1.55), 3.0),
            "sky": cam_track((545, 1210, 1.55)).key(sk0 + 0.5, (540, -900, 1.0), 8.5, ease=ease_io),
            "title_end": cam_track((540, -900, 1.0)),
        }

    def draw(self, cv, t, shot, ctx):
        star = 0.0
        if shot in ("sky", "title_end"):
            kh = LN("narr", "But right in the middle")
            star = clamp((t - kh[0]) / (kh[1] - kh[0] + 0.5))
        blurred(cv, ctx, S.porch_bg, t, star)
        # night grade on characters + lamp light
        cm = skia.ColorFilters.Matrix([0.74, 0, 0, 0, 0.0,
                                       0, 0.76, 0, 0, 0.0,
                                       0, 0, 0.92, 0, 0.03,
                                       0, 0, 0, 1, 0])
        cv.saveLayer(None, skia.Paint(ColorFilter=cm))
        self.me.draw(cv, t)
        self.dn.draw(cv, t)
        cv.restore()
        lp = skia.Paint(AntiAlias=True)
        lp.setShader(skia.GradientShader.MakeRadial(skia.Point(960, 720), 900,
                                                    [gfx.C(alpha("#ffb85a", 0.22)).toColor(), gfx.C(alpha("#ffb85a", 0.0)).toColor()]))
        lp.setBlendMode(skia.BlendMode.kPlus)
        cv.drawRect(skia.Rect.MakeLTRB(-400, 300, 1480, 2400), lp)


# ======================================================================= FORTRESS
class FortScene:
    def __init__(self):
        c = CAST
        f0 = SH["fort_hall"][0]
        ag = self.ag = Actor(c["anger_d"], seed=121, talk_name="anger_d", x=835, y=1610, scale=1.6,
                             expr=("stern", dict(press=0.7, brow=-0.35)), look=(-0.2, 0.1), turn=-0.2, cross=1.0)
        gu = self.gu = Actor(c["guilt"], seed=131, x=540, y=1610, scale=1.8, pose="hug_knees",
                             expr=("sad", dict(lid=0.7, smile=-0.3, brow_ang=0.9)), look=(0.0, 0.6), nod=0.2, sacc=0.04)
        gd = self.gd = Actor(c["guilt"], seed=137, x=545, y=1497, scale=1.35, pose="hug_knees",
                             expr=("sad", dict(lid=0.65, smile=-0.3, brow_ang=0.9)), look=(0.0, 0.6), nod=0.25, sacc=0.04)
        n1 = LN("narr", "I used to joke")
        ag.at(n1[0] + 0.8, 0.25, look=(-0.85, 0.0))
        ag.at(n1[0] + 1.9, 0.25, look=(0.6, 0.0))
        ag.at(n1[0] + 3.0, 0.3, look=(-0.2, 0.1))
        g = LN("narr", "Anger was the guard")
        ag.at(LN("narr", "But it was never", 1) - 0.2, 0.5, nod=-0.12, expr=("stern", dict(press=0.85, brow=-0.45, lid=0.8)))
        # cell
        c0 = SH["fort_cell"][0]
        gu.at(c0 + 0.8, 0.8, look=(0.2, 0.7))
        gu.blink_at(c0 + 1.4)
        gl = LN("narr", "What he was guarding", 1)
        gu.at(gl, 0.9, look=(0.0, -0.3), nod=0.05, expr=("sad", dict(lid=0.85, brow_ang=1.0, tears=0.6, smile=-0.25)))
        # door opens
        ec = M["echo"]
        do = M["door_open"]
        ag.at(ec + 0.3, 0.3, expr=("stern", dict(press=0.6, brow=0.3, lid=1.05)), look=(0.6, -0.4), turn=0.2)
        ag.at(ec + 0.85, 0.3, expr=("smile", dict(smile=0.5, brow=0.3)))
        ag.at(do - 0.3, 0.5, cross=0.0, armL=(-1.5, 2.2, 1.0, "mitt"), armR=(1.25, 2.5, 1.0), turn=-0.5, look=(-0.85, 0.3))
        ag.at(do + 1.2, 0.6, x=880)
        hb = LN("narr", "Humor is a back door")
        ag.at(hb[1] + 0.3, 0.6, expr=("tender", dict(smile=0.35, brow_ang=0.6, lid=0.9)), look=(-0.9, 0.55), nod=0.12)
        ev = LN("narr", "evolution only")
        ag.at(ev[0] + 1.6, 0.8, armL=(-1.55, 2.65, 1.0, "mitt"))  # offers a hand
        gd.at(do + 0.6, 0.6, look=(0.4, -0.5), nod=-0.05, expr=("surprised", dict(open=0.0, lid=0.75, lower=0.3, brow_ang=0.5)))
        gd.blink_at(do + 1.2)
        gd.blink_at(do + 1.5)
        gd.at(do + 2.2, 0.6, expr=("worried", dict(lid=1.0, brow_ang=0.7, smile=-0.05)), look=(0.85, -0.35))
        gd.at(ev[0] + 2.6, 0.8, expr=("tender", dict(smile=0.25, brow_ang=0.6, tears=0.4)), look=(0.85, -0.45), nod=-0.05)
        self.cam = {
            "fort_hall": cam_track((560, 1150, 1.05)).key(f0, (640, 1230, 1.35), 10.0),
            "fort_cell": cam_track((540, 1460, 1.55)).key(c0, (540, 1455, 1.8), 3.9),
            "fort_open": cam_track((620, 1260, 1.2)).key(do + 0.4, (640, 1300, 1.4), 7.5),
        }

    def door_amt(self, t):
        do = M["door_open"]
        return 0.75 * ease_io(clamp((t - do) / 2.6))

    def draw(self, cv, t, shot, ctx):
        warm = skia.ColorFilters.Matrix([0.98, 0, 0, 0, 0.02,
                                         0, 0.86, 0, 0, 0.0,
                                         0, 0, 0.78, 0, 0.0,
                                         0, 0, 0, 1, 0])
        if shot == "fort_cell":
            blurred(cv, ctx, S.cell_bg, t)
            self.gu.draw(cv, t)
            return
        blurred(cv, ctx, S.fortress_bg, t)
        oa = self.door_amt(t)
        if oa > 0.001:
            S.cell_interior(cv, t, light=oa / 0.75)
            cv.save()
            cv.clipRect(skia.Rect.MakeLTRB(360, 700, 720, 1500))
            self.gd.draw(cv, t)
            beam = gfx.path_poly([(360, 1500), (420, 900), (560, 900), (760, 1500)])
            bp = skia.Paint(AntiAlias=True)
            bp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 900), skia.Point(0, 1500)],
                                                        [gfx.C(alpha("#ffc070", 0.0)).toColor(), gfx.C(alpha("#ffc070", 0.3 * oa / 0.75)).toColor()]))
            bp.setBlendMode(skia.BlendMode.kPlus)
            cv.drawPath(beam, bp)
            cv.restore()
        S.door(cv, t, oa, keyhole_glow=0.7 if oa < 0.05 else 0.0)
        cv.saveLayer(None, skia.Paint(ColorFilter=warm))
        self.ag.draw(cv, t)
        cv.restore()
