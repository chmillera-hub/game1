"""The film, shot by shot: actor keyframes and cameras anchored to the voice timeline."""
import math

from anim import Actor, Cam, Track, pulse
from gfx import back_out, ease_in, ease_in_out, ease_out, lerp, noise1
from mice import KINDS
import sets as S_
import views as V

T = None


def hy(name, y, scale):
    K = KINDS[name]
    return y - (K["chin"] + K["legs"] + 18) * scale * K["size"]


def framing(x, y, zoom, sy=760):
    """Camera values putting world point (x, y) at screen height sy."""
    return dict(cx=x, cy=y + (960 - sy) / zoom, zoom=zoom)


def cam_at(x, y, zoom, sy=760):
    f = framing(x, y, zoom, sy)
    return Cam(f["cx"], f["cy"], f["zoom"])


def W_(lid, word, nth=0, edge="start"):
    return T.word(lid, word, nth, edge)


# =================================================================== PROLOGUE
def prologue(shots):
    # --- title shot in the moonlit kitchen (frame 0 is already the full picture)
    kv = V.KitchenView(state=dict(title=Track(1.0).to(3.6, 0.0, 1.2), page=dict(ink=0.0), lantern=1.0))
    cam = Cam(540, 960, 1.0).k(0.0, dur=T.s("n2"), zoom=1.16, cy=1060, ease=ease_in_out)
    shots.append((0.0, kv, cam))

    # --- the drawing being drawn, line by line, as the narrator describes it
    st = dict(
        ink=0.0, night=0.28,
        r_girl=Track(0.0).to(W_("n2", "girl") - 0.1, 1.0, 1.0),
        r_mice=Track(0.0).to(W_("n3", "Five"), 1.0, 1.6, ease=ease_in_out),
        r_pumpkins=Track(0.0).to(W_("n3", "Three"), 1.0, 1.1),
        r_flower=Track(0.0).to(W_("n3", "One"), 1.0, 0.9),
        r_words=Track(0.0).to(W_("n3", "note") - 0.2, 1.0, 3.2, ease=ease_in_out),
    )
    mice = {}
    stagger = {"wedge": 0.0, "biscuit": 0.3, "tilt": 0.55, "crumb": 0.8, "pip": 1.05}
    for i, (name, base) in enumerate(S_.PAGE_MICE.items()):
        a = Actor(name, "mouse:" + name, T, seed=40 + i, flat=True, **base)
        a.k(T.s("n2") - 1, dur=0.01, alpha=0.0)
        a.k(W_("n3", "Five") + stagger[name], dur=0.45, alpha=1.0)
        a.idle = 0.0
        a.hold_still(0, T.e("chimes") - 1.4)
        mice[name] = a
    pv = V.PageView(mice, st, warm=0.7)
    shots.append((T.s("n2") - 0.25, pv, Cam(540, 920, 1.02)))
    shots.append((W_("n3", "note") - 0.35, pv, Cam(582, 420, 1.36)))

    # --- she climbs to bed; the hall lamp goes out
    sv = V.StairsView(dict(girl=Track(0.0).to(T.s("n4") - 0.3, 0.85, 7.4, ease=ease_in_out),
                           lamp=Track(1.0).to(W_("n4", "goodnight", edge="end") + 0.1, 0.0, 0.25)))
    shots.append((T.s("n4") - 0.3, sv, Cam(600, 960, 1.1)))

    # --- the old clock strikes twelve
    bong = [T.s("chimes") + o for o in (0.2, 1.45, 2.7, 3.95)]
    shake = Track(0.0)
    for b in bong:
        shake.to(b, 1.0, 0.05).to(b + 0.06, 0.0, 0.5)
    cv = V.ClockView(dict(min=Track(338.0).to(T.s("n5"), 360.0, T.e("n5") - T.s("n5") + 0.3, ease=ease_in_out),
                          hour=Track(358.0).to(T.s("n5"), 360.0, 8.0),
                          shake=shake,
                          flash=Track(0.0).to(bong[-1], 0.55, 0.06).to(bong[-1] + 0.1, 0.0, 1.0)))
    shots.append((T.s("n5") - 0.4, cv, Cam(560, 1050, 1.0)))
    cam = Cam(560, 700, 1.6)
    for b in bong:
        cam.shake(b, 10, 0.4)
    shots.append((bong[0] - 0.15, cv, cam))


# =================================================================== WAKING ON THE PAGE
def waking(shots):
    t0 = T.e("chimes") - 1.4
    wake = T.e("chimes") - 0.2
    st = dict(
        ink=Track(0.0).to(t0 + 0.4, 1.0, 1.6),
        night=Track(0.28).to(t0, 0.18, 1.0),
        moonbeam=Track(0.0).to(t0, 1.0, 2.6, ease=ease_in_out),
        beam_a=Track(1.0).to(t0 + 2.2, 0.0, 0.8),
        magic=Track(0.0).to(t0 + 0.6, 0.6, 0.4).to(t0 + 1.1, 0.0, 1.0),
    )
    mice = {}
    for i, (name, base) in enumerate(S_.PAGE_MICE.items()):
        a = Actor(name, "mouse:" + name, T, seed=40 + i, flat=True, **base)
        a.hold_still(0, wake)
        a.blink_at(wake + 0.15 * i)
        a.blink_at(wake + 0.15 * i + 0.45)
        if name == "tilt":
            a.k(wake + 0.8, dur=0.5, lid=0.9)
            a.k(wake + 1.4, sleep=True, dur=0.01)
        mice[name] = a
    w = mice["wedge"]
    w.says("w1")
    w.k(wake + 0.3, look=(-0.5, 0.0), dur=0.25)
    w.k(W_("w1", "Hmm"), look=(-0.7, -0.2), brow=-0.2, brow_tilt=-0.3, dur=0.3)
    w.k(W_("w1", "Hmm") + 0.45, look=(0.7, -0.2), dur=0.3)
    w.k(W_("w1", "Oh") - 0.1, look=(0.0, 0.0), pupil=0.75, brow=0.9, brow_tilt=0.0, dur=0.15)
    w.k(W_("w1", "my") - 0.2, look=(0.9, 0.6), yaw=0.5, pupil=0.9, dur=0.4)
    w.k(W_("w1", "tail") - 0.8, tail_amp=3.5, dur=0.4)
    w.k(W_("w1", "appear"), smile=0.75, brow=0.6, ear_perk=0.8, dur=0.6)
    w.k(T.e("w1") - 0.1, look=(-0.2, -0.1), yaw=0.0, dur=0.4)
    # everyone looks around in the background
    mice["biscuit"].k(wake + 0.8, look=(0.6, -0.3), dur=0.3).k(wake + 2.0, look=(-0.6, 0.4), dur=0.3)
    mice["crumb"].k(wake + 0.9, look=(-0.6, 0.0), pupil=1.3, dur=0.3)
    mice["pip"].k(wake + 1.0, look=(0.4, -0.7), brow_tilt=0.5, dur=0.4)
    # pop off the page right before the cut
    for i, a in enumerate(mice.values()):
        a.k(T.e("w1") + 0.05 + i * 0.04, dur=0.25, scale=a.base["scale"] * 1.12, ease=back_out)
    pv = V.PageView(mice, st, warm=0.7)
    hx, hy_ = V.PAGE_X + 470, V.PAGE_Y + 640
    f = framing(hx, hy_, 2.5, 760)
    shots.append((t0, pv, Cam(540, 920, 1.0)))
    shots.append((T.s("w1") - 0.25, pv, Cam(f["cx"], f["cy"], f["zoom"])))
    shots.append((T.e("w1") - 0.1, pv, Cam(540, 920, 1.0)))


# =================================================================== THE TABLETOP STAGE
def stage(shots):
    LX = [S_.letter_x(i) for i in range(14)]          # T O O M O M I L O V E Y O U
    A = {}
    w = A["wedge"] = Actor("wedge", "mouse:wedge", T, seed=1, x=520, y=1640, scale=1.25, facing=1, light=(-0.6, 0))
    p = A["pip"] = Actor("pip", "mouse:pip", T, seed=2, x=230, y=1700, scale=1.15, facing=1, light=(-0.6, 0))
    b = A["biscuit"] = Actor("biscuit", "mouse:biscuit", T, seed=3, x=900, y=1600, scale=1.12, facing=1,
                             prop="pumpkin", arm_l=(-40.0, -60.0), arm_r=(-40.0, -60.0), smile=0.3, light=(-0.6, 0))
    cr = A["crumb"] = Actor("crumb", "mouse:crumb", T, seed=4, x=390, y=1800, scale=1.3, facing=1, light=(-0.6, 0))
    k = A["cat"] = Actor("cat", "cat", T, seed=5, x=1060, y=1330, scale=1.45, facing=-1, z=-1, rise=0.15,
                         eyes_only=1.0, lid=1.0, light_dir=-1.0, hidden=True, pupil=0.2, lid_tilt=0.5)
    w.says("w2", "w3", "w4", "w5")
    p.says("p1", "p2", "p3", "p4", "p5")
    b.says("b1", "b2", "b3", "b4", "b5")
    cr.says("c1", "c2", "c3", "c4", "c5", "c6", "c7")
    k.says("k1", "k2", "k3", "k4", "k5", "k6")
    k.mouth_gain = 0.8
    mice = [w, p, b, cr]
    t_in = T.s("b1") - 0.15
    for m in mice:
        m.hop(t_in, 30, 0.3)

    # ---- b1: Biscuit discovers his corners
    b.look_at(t_in, None)
    b.k(W_("b1", "corners") - 0.5, look=(-0.8, -0.9), arm_l=(150.0, -30.0), arm_r=(10.0, 10.0), dur=0.3)
    b.k(W_("b1", "corners") - 0.1, look=(0.8, -0.9), arm_r=(150.0, -30.0), dur=0.25)
    b.k(W_("b1", "Look"), look=(0.0, 0.0), arm_l=(100.0, 10.0), arm_r=(100.0, 10.0), smile=0.95, brow=0.6, dur=0.25)
    b.hop(W_("b1", "square"), 40, 0.35)
    b.k(W_("b1", "Is"), smile=0.1, brow=0.7, brow_tilt=0.6, arm_l=(60.0, 40.0), arm_r=(60.0, 40.0), look=(-0.4, 0.1), dur=0.3)
    b.k(W_("b1", "feel"), smile=0.85, brow=0.3, brow_tilt=0.0, lid_low=0.45, dur=0.4)
    b.nod(W_("b1", "good"), 1.0)
    b.k(T.e("b1") + 0.2, arm_l=(-40.0, -60.0), arm_r=(-40.0, -60.0), lid_low=0.0, smile=0.5, dur=0.4)
    # others watch Biscuit
    for m in (w, p, cr):
        m.look_at(t_in + 0.3, b)
    w.k(t_in + 0.6, smile=0.4, dur=0.5)
    p.k(t_in + 0.4, smile=0.2, dur=0.5)
    cr.k(t_in + 0.4, smile=0.6, pupil=1.25, dur=0.4)

    # ---- c1: Crumb: we're alive!
    cr.look_at(T.s("c1") - 0.2, None)
    cr.k(T.s("c1") - 0.15, look=(0.0, -0.3), arm_l=(160.0, -20.0), arm_r=(160.0, -20.0), brow=1.0, pupil=1.35,
         ear_perk=1.0, smile=0.9, dur=0.2)
    cr.hop(W_("c1", "alive", 0) - 0.1, 70, 0.4)
    cr.hop(W_("c1", "alive", 1) - 0.1, 90, 0.45)
    cr.k(T.e("c1") + 0.1, arm_l=(30.0, 20.0), arm_r=(30.0, 20.0), brow=0.3, ear_perk=0.3, dur=0.4)
    for m in (w, p, b):
        m.look_at(T.s("c1") - 0.1, cr)
    b.k(T.s("c1"), smile=0.8, dur=0.3)

    # ---- p1: Pip peers into the dark
    p.look_at(T.s("p1") - 0.5, None)
    p.k(T.s("p1") - 0.5, look=(-0.95, 0.1), yaw=-0.5, ear_droop=0.55, brow_tilt=0.85, brow=0.2, smile=-0.35,
        arm_l=(-70.0, -40.0), arm_r=(-70.0, -40.0), pupil=0.85, dur=0.5)
    p.tremble(T.s("p1"), T.e("p1"), 1.2)
    p.k(W_("p1", "Is"), look=(0.8, -0.3), yaw=0.3, dur=0.35)
    for m in (b, cr):
        m.look_at(T.s("p1"), p)
    w.look_at(T.s("p1") - 0.2, p)
    w.k(T.s("p1") + 0.5, smile=0.0, brow_tilt=0.3, dur=0.6)

    # ---- w2: Wedge comforts Pip
    w.k(T.s("w2") - 0.3, smile=0.55, lid_low=0.35, brow_tilt=0.35, brow=0.1, arm_l=(105.0, 25.0), dur=0.5)
    w.k(T.s("w2") - 0.3, x=470, dur=0.8)
    p.k(W_("w2", "Stay"), x=340, lean=-4.0, ear_droop=0.2, smile=0.35, brow_tilt=0.4, arm_l=(30.0, 20.0),
        arm_r=(30.0, 20.0), dur=0.7)
    p.look_at(T.s("w2"), w)
    w.k(T.e("w2") + 0.4, arm_l=(30.0, 20.0), lid_low=0.0, dur=0.5)

    # ---- popup: the words stand up out of the page
    up0 = T.s("popup")
    for m in mice:
        m.look_at(up0 + 0.2, (600 + 200 * (m is b), 1250))
        m.k(up0 + 0.2, pupil=1.15, brow=0.6, dur=0.3)
    cr.hop(up0 + 0.5, 50, 0.35)
    b.hop(up0 + 0.7, 30, 0.3)

    # ---- c2: Crumb reads them, letter by letter
    t = T.s("c2") + 0.05
    cr.k(t, x=LX[0] + 20, y=1505, scale=1.12, dur=0.9, ease=ease_in_out)
    cr.k(t, walking=1.0, dur=0.1).k(t + 0.9, walking=0.0, dur=0.1)
    cr.k(t, walk=6.0, dur=0.9, ease=lambda u: u)
    cr.look_at(t + 0.9, (LX[0], 1200))
    for i, word in ((1, "O"), (2, "O")):
        tw = W_("c2", word, i - 1)
        cr.k(tw - 0.25, x=LX[i] + 10, dur=0.3)
        cr.hop(tw - 0.25, 38, 0.3)
        cr.look_at(tw - 0.1, (LX[i], 1200))
    cr.k(W_("c2", "Too"), tilt=14.0, brow_tilt=0.35, brow=0.4, dur=0.3)
    cr.look_at(W_("c2", "Mom") - 0.1, (800, 1350))
    cr.k(T.e("c2") + 0.4, tilt=0.0, dur=0.4)
    # the others wander over
    tw = T.s("c2") + 0.6
    b.k(tw, x=LX[2] + 118, y=1490, scale=1.0, dur=2.2).k(tw, walking=1.0, dur=0.1).k(tw + 2.2, walking=0.0, dur=0.1)
    b.k(tw, walk=-8.0, dur=2.2, ease=lambda u: u)
    p.k(tw + 0.3, x=640, y=1568, scale=1.05, dur=2.0).k(tw + 0.3, walking=1.0, dur=0.1).k(tw + 2.3, walking=0.0, dur=0.1)
    p.k(tw + 0.3, walk=7.0, dur=2.0, ease=lambda u: u)
    w.k(tw + 0.1, x=830, y=1600, scale=1.15, dur=2.3).k(tw + 0.1, walking=1.0, dur=0.1).k(tw + 2.4, walking=0.0, dur=0.1)
    w.k(tw + 0.1, walk=8.0, dur=2.3, ease=lambda u: u)
    for m in (w, p, b):
        m.look_at(tw + 2.4, cr)

    # ---- b2: Biscuit leans on the second O, smug
    b.k(T.s("b2") - 0.3, lean=-11.0, arm_l=(-75.0, -70.0), arm_r=(-75.0, -70.0), lid=0.35, brow=0.5,
        brow_tilt=-0.3, smile=0.45, dur=0.4)
    b.look_at(T.s("b2") - 0.3, cr)
    b.k(W_("b2", "Everybody"), arm_r=(120.0, -60.0), dur=0.25)
    b.k(W_("b2", "knows") + 0.15, arm_r=(105.0, -40.0), dur=0.15)
    b.k(W_("b2", "knows") + 0.3, arm_r=(120.0, -60.0), dur=0.15)
    b.k(T.e("b2") + 0.2, arm_r=(-75.0, -70.0), lid=0.15, dur=0.3)
    cr.look_at(T.s("b2"), b)
    cr.k(T.s("b2") + 0.3, smile=0.2, brow=0.1, dur=0.3)

    # ---- c3: Crumb's ghost joke
    cr.k(T.s("c3") - 0.2, smile=0.9, brow=0.9, pupil=1.3, dur=0.3)
    cr.look_at(T.s("c3"), b)
    cr.k(W_("c3", "Oooo") - 0.15, arm_l=(150.0, -40.0), arm_r=(150.0, -40.0), mround=1.0, lid=0.25, brow=1.0,
         dur=0.2)
    for i in range(5):
        tt = W_("c3", "Oooo") + i * 0.16
        cr.k(tt, arm_l=(150.0 + (12 if i % 2 else -12), -40.0), arm_r=(150.0 + (-12 if i % 2 else 12), -40.0), dur=0.08)
    b.k(W_("c3", "ghost"), lid=0.0, lean=-4.0, smile=0.6, brow=0.5, brow_tilt=0.0, dur=0.3)

    # ---- oooo: the wind answers. Everyone freezes.
    t = T.s("oooo")
    for m in mice:
        m.k(t + 0.25, pupil=0.45, lid=0.0, brow=1.0, brow_tilt=0.3, ear_perk=1.0, ear_droop=0.0, smile=-0.2,
            dur=0.12)
        m.look_at(t + 0.25, None)
        m.k(t + 0.25, look=(0.0, 0.0), dur=0.1)
        m.hold_still(t, T.e("c4"))
    cr.k(t + 0.25, arm_l=(150.0, -40.0), arm_r=(150.0, -40.0), dur=0.05)
    b.k(t + 0.25, lean=0.0, arm_l=(-40.0, -60.0), arm_r=(-40.0, -60.0), dur=0.15)
    w.k(t + 0.25, arm_l=(30.0, 20.0), dur=0.1)
    # eyes slide toward each other during the whispers
    b.k(T.s("b3") - 0.1, look=(-1.0, 0.1), dur=0.25)
    p.k(T.s("p2") - 0.15, look=(-0.9, 0.0), dur=0.25)
    cr.k(T.s("c4") - 0.2, look=(1.0, -0.2), arm_l=(60.0, 40.0), arm_r=(60.0, 40.0), dur=0.25)
    b.k(T.s("c4") - 0.1, look=(-1.0, 0.2), dur=0.2)

    # ---- eyes in the dark
    t = T.s("eyes")
    k.snap(t, hidden=False)
    k.k(t + 0.7, lid=0.25, dur=0.35)
    k.k(t + 1.3, look=(-0.7, 0.4), dur=0.4)
    for i, m in enumerate(mice):
        m.k(t + 0.9 + i * 0.12, look=(1.0, -0.5), yaw=0.4, pupil=0.4, dur=0.25)
    cr.k(t + 1.2, x=560, y=1588, scale=1.2, arm_l=(30.0, 20.0), arm_r=(30.0, 20.0), dur=0.6, ease=ease_out)
    p.k(t + 1.4, x=700, y=1555, dur=0.6)
    w.k(t + 1.6, x=860, y=1610, dur=0.5)
    b.k(t + 1.2, arm_l=(-60.0, -80.0), arm_r=(-60.0, -80.0), dur=0.3)
    for m in mice:
        m.tremble(t + 1.0, T.e("w3"), 1.0)

    # ---- k1: 'Well, well, well. Mice. On my table.'  -> the cat rises
    k.k(T.s("k1"), lid=0.35, lid_tilt=0.6, pupil=0.15, dur=0.4)
    k.k(W_("k1", "Mice"), look=(-0.9, 0.6), dur=0.3)
    k.k(W_("k1", "table") - 0.4, eyes_only=0.0, dur=0.01)
    k.k(W_("k1", "table") - 0.4, rise=1.0, dur=1.6, ease=ease_in_out)
    k.k(W_("k1", "table") - 0.4, smile=0.35, dur=1.0)
    for m in mice:
        m.look_at(W_("k1", "table"), k)
        m.k(W_("k1", "table"), ear_droop=0.4, ear_perk=0.0, dur=0.4)

    # ---- w3: Wedge stands up to the cat
    w.k(T.s("w3") - 0.5, x=900, brow=-0.3, brow_tilt=0.45, pupil=0.7, ear_droop=0.25, smile=-0.1, dur=0.6)
    w.k(W_("w3", "pencil", 0), arm_r=(130.0, -20.0), dur=0.3)
    w.k(W_("w3", "pencil", 1) - 0.3, arm_r=(150.0, 20.0), brow=0.1, dur=0.3)
    w.k(T.e("w3"), arm_r=(30.0, 20.0), dur=0.4)
    k.look_at(T.s("w3") - 0.3, w)
    k.k(W_("w3", "eat"), smile=0.55, lid=0.45, dur=0.5)

    # ---- k2
    k.k(T.s("k2"), tilt=10.0, smile=0.6, lid=0.45, lid_tilt=0.3, dur=0.5)
    k.blink_at(W_("k2", "darling") - 0.05)
    k.k(W_("k2", "I"), tilt=-4.0, rise=0.86, lid=0.4, lid_tilt=0.65, pupil=0.12, smile=0.3, dur=0.9)
    w.k(W_("k2", "story"), pupil=0.55, ear_droop=0.4, dur=0.4)

    # ---- k3: the cat's prophecy
    k.k(T.s("k3"), rise=0.92, tilt=0.0, dur=0.6)
    k.look_at(T.s("k3"), (900, 300))
    k.k(W_("k3", "drawer"), tail_amp=2.2, dur=0.3).k(W_("k3", "box"), tail_amp=1.0, dur=0.3)
    k.look_at(W_("k3", "And"), w)
    k.k(W_("k3", "recycling") - 0.2, lid=0.5, lid_tilt=0.7, smile=0.45, dur=0.5)
    k.blink_at(T.e("k3") - 0.2)
    falls = [(p, 1.0, 0.9), (b, 0.6, 0.6), (cr, 0.7, 0.5), (w, 0.6, 0.6)]
    for i, (m, sad, droop) in enumerate(falls):
        tt = W_("k3", "drawer") + i * 0.35
        m.k(tt, brow_tilt=0.5 * sad, ear_droop=droop * 0.6, smile=-0.2, pupil=0.85, dur=0.8)
        tt = W_("k3", "recycling") + i * 0.2
        m.k(tt, brow_tilt=sad, brow=0.2, ear_droop=droop, smile=-0.55, lid=0.15, dur=0.9)
    b.k(W_("k3", "box"), smile=-0.4, arm_l=(-45.0, -75.0), arm_r=(-45.0, -75.0), dur=0.8)
    cr.look_at(W_("k3", "gray"), w)
    p.k(W_("k3", "bin"), glisten=0.6, dur=0.8)

    # ---- p3 / k4
    p.look_at(T.s("p3") - 0.3, k)
    p.k(T.s("p3") - 0.3, brow_tilt=1.0, ear_droop=0.95, glisten=0.85, pupil=0.95, smile=-0.6, dur=0.5)
    p.tremble(T.s("p3"), T.e("p3"), 0.8)
    k.look_at(T.s("p3"), p)
    k.k(T.s("p3") + 0.3, lid=0.25, lid_tilt=0.0, smile=0.0, dur=0.6)
    k.k(T.s("k4") - 0.2, lid_tilt=-0.5, pupil=0.75, lid=0.3, dur=0.8)
    k.look_at(W_("k4", "Everything") - 0.4, (300, 250))
    k.k(W_("k4", "Everything"), lid=0.62, ear_back=0.3, dur=1.2)
    k.k(T.e("k4") + 0.3, lid=0.4, dur=0.8)

    # ---- silence / w4: Wedge looks at his own faint edges
    t = T.s("silence")
    w.look_at(t + 0.2, None)
    w.k(t + 0.3, arm_r=(105.0, -55.0), look=(0.9, 0.35), yaw=0.35, lid=0.4, brow_tilt=0.7, smile=-0.25, ear_droop=0.7,
        dur=0.8)
    w.k(W_("w4", "edges") - 0.6, look=(-0.4, 0.1), yaw=-0.1, arm_r=(30.0, 20.0), lid=0.3, dur=0.6)
    for m in (p, b, cr):
        m.look_at(t + 0.8, w)

    # ---- crumbwalks / c5 / c6: the paper remembers
    t = T.s("crumbwalks")
    cr.look_at(t, (LX[2], 1250))
    cr.k(t + 0.1, x=LX[2] - 4, y=1508, scale=1.12, dur=1.4, ease=ease_in_out)
    cr.k(t + 0.1, walking=1.0, dur=0.1).k(t + 1.5, walking=0.0, dur=0.1)
    cr.k(t + 0.1, walk=-6.0, dur=1.4, ease=lambda u: u)
    cr.k(t + 0.2, brow_tilt=0.2, ear_droop=0.3, smile=0.0, dur=0.6)
    cr.k(T.s("c5") - 0.2, arm_r=(150.0, 0.0), pupil=1.2, brow=0.5, dur=0.4)
    cr.k(W_("c5", "dents") - 0.2, arm_r=(140.0, -10.0), dur=0.2).k(W_("c5", "dents") + 0.1, arm_r=(150.0, 0.0), dur=0.2)
    cr.look_at(W_("c5", "You") - 0.1, w)
    cr.k(T.s("c6") - 0.4, arm_r=(30.0, 20.0), smile=0.85, brow=0.8, brow_tilt=0.0, ear_droop=0.0, ear_perk=0.7,
         pupil=1.35, dur=0.5)
    for m in (w, p, b):
        m.look_at(T.s("c5"), cr)
    tr = W_("c6", "remembers")
    for i, m in enumerate((w, p, b)):
        m.k(tr + 0.1 + i * 0.15, pupil=1.2, brow=0.6, brow_tilt=0.2, ear_droop=0.2, smile=0.15, lid=0.0, dur=0.6)

    # ---- p4: Pip understands the 'TOO'
    p.look_at(T.s("p4") - 0.4, (LX[1], 1250))
    p.k(T.s("p4") - 0.4, smile=0.0, brow_tilt=0.3, brow=0.3, glisten=0.4, ear_droop=0.3, dur=0.6)
    p.look_at(W_("p4", "Too") - 0.2, (LX[2], 1220))
    p.k(W_("p4", "Too"), pupil=1.3, brow=0.8, dur=0.5)
    p.look_at(W_("p4", "Like") - 0.2, w)
    p.k(W_("p4", "love"), glisten=1.0, smile=0.55, brow_tilt=0.5, ear_droop=0.0, ear_perk=0.4, dur=0.8)
    p.k(W_("p4", "Because"), tear=0.01, dur=0.01)
    p.k(W_("p4", "Because"), tear=1.0, dur=2.2, ease=ease_in)
    p.k(W_("p4", "first") - 0.3, smile=0.9, lid_low=0.4, dur=0.6)
    for m in (w, b, cr):
        m.look_at(T.s("p4"), p)
    w.k(W_("p4", "love"), smile=0.6, lid_low=0.3, brow_tilt=0.4, glisten=0.5, ear_droop=0.0, dur=1.0)
    cr.k(W_("p4", "first"), smile=0.9, dur=0.6)

    # ---- b4: Biscuit, teary, trying to joke
    b.k(T.s("b4") - 0.6, glisten=1.0, smile=0.25, brow_tilt=0.9, brow=0.4, ear_droop=0.3, arm_l=(-50.0, -90.0),
        arm_r=(-50.0, -90.0), dur=0.6)
    b.tremble(T.s("b4"), W_("b4", "best"), 1.2)
    b.k(W_("b4", "best"), smile=0.85, lid_low=0.35, dur=0.6)
    b.k(W_("b4", "best"), tear=0.01, dur=0.01).k(W_("b4", "best"), tear=1.0, dur=2.0, ease=ease_in)
    b.nod(W_("b4", "heard"), 1.2)
    for m in (w, p, cr):
        m.look_at(T.s("b4"), b)

    # ---- k5: nobody draws the black cat
    k.look_at(T.s("k5") - 0.8, (-400, 300))
    k.k(T.s("k5") - 0.8, turn=-0.6, ear_back=0.5, lid=0.45, lid_tilt=-0.6, pupil=0.85, smile=-0.1, dur=1.0)
    k.look_at(W_("k5", "Not") - 0.3, (900, 1600))
    k.k(W_("k5", "Not"), lid=0.55, dur=0.6)
    k.k(W_("k5", "luck") - 0.2, lid=0.85, dur=0.6).k(T.e("k5") + 0.3, lid=0.5, dur=0.6)
    for m in mice:
        m.look_at(T.s("k5"), k)
        m.k(T.s("k5") + 0.6, brow_tilt=0.7, ear_droop=0.3, smile=-0.1, glisten=0.0, tear=0.0, dur=0.8)

    # ---- c7: Crumb offers the cat a place in the picture
    t = T.s("c7") - 0.9
    cr.k(t, x=1010, y=1388, scale=0.98, dur=1.1, ease=ease_in_out)
    cr.k(t, walking=1.0, dur=0.1).k(t + 1.1, walking=0.0, dur=0.1)
    cr.k(t, walk=9.0, dur=1.1, ease=lambda u: u)
    cr.look_at(t + 1.0, k)
    cr.k(t + 1.0, smile=0.55, lid_low=0.25, brow_tilt=0.3, brow=0.3, ear_perk=0.3, dur=0.5)
    cr.k(W_("c7", "Right"), arm_l=(110.0, 10.0), dur=0.4).k(T.e("c7") + 0.3, arm_l=(30.0, 20.0), dur=0.4)
    k.look_at(W_("c7", "room"), cr)
    k.k(W_("c7", "room"), turn=0.0, lid=0.2, lid_tilt=-0.3, pupil=1.0, ear_back=0.1, dur=0.8)

    # ---- k6: a slow blink. Humph.
    k.k(T.s("k6") - 0.9, lid=1.0, dur=0.45).k(T.s("k6") - 0.3, lid=0.3, dur=0.5)
    k.k(T.s("k6") - 0.3, smile=0.4, tail_amp=1.8, dur=0.6)
    cr.k(T.e("k6"), smile=0.9, dur=0.4)

    # ---- thumps: something is coming down the stairs
    t = T.s("thumps")
    for o in (0.05, 1.15, 3.25):
        for m in mice:
            m.hop(t + o, 22, 0.22)
            m.k(t + o, pupil=0.5, brow=0.9, ear_perk=1.0, ear_droop=0.0, smile=-0.3, dur=0.1)
    for m in mice:
        m.look_at(t + 0.3, (1700, 900))
    k.k(t + 0.1, ear_back=0.0, lid=0.0, pupil=0.9, turn=0.5, dur=0.2)
    k.look_at(t + 0.1, (1800, 1000))
    k.hop(t + 3.0, 120, 0.5)
    k.k(t + 3.0, x=1700, dur=0.6, ease=ease_in)
    k.snap(t + 3.7, hidden=True)
    # mice drift together into a frightened huddle near the letters
    cr.k(t + 1.5, x=600, y=1560, scale=1.15, dur=0.7, ease=ease_out)
    b.k(t + 1.6, x=450, y=1515, scale=1.0, dur=0.6)

    def mom_shadow(c, tt):
        t_a = T.s("thumps") + 3.0
        t_b = T.s("p5") + 0.2
        u = (tt - t_a) / (t_b - t_a)
        if u <= 0:
            return
        from mom import draw_mom, pose as mom_pose
        u2 = max(0.0, min(1.0, (tt - t_b) / (T.e("scramble") - t_b)))
        u = min(1.0, u)
        sc = lerp(0.2, 0.47, ease_out(u)) + 0.07 * u2
        x = lerp(S_.DOOR_X - 60, 470, ease_out(u)) - 120 * u2
        base = S_.STAGE_GROUND + 40
        mp = mom_pose(full=True, arms="candle", candle=-1.0, scale=sc, x=0, y=0)

        def fn(cc):
            cc.save()
            cc.translate(x, base)
            cc.skew(-0.16, 0.0)
            cc.translate(0, -1720 * sc)
            draw_mom(cc, mp)
            cc.restore()
        V.silhouette(c, fn, (4, 2, 8), 0.82 * min(1.0, u * 5), 5)

    st = dict(letters_up=Track(0.0).to(up0 + 0.1, 1.0, 1.9, ease=lambda u: u),
              letters_glow=Track(0.0).to(W_("c5", "pressed"), 0.25, 0.6).to(W_("c6", "remembers") - 0.1, 1.0, 0.5)
              .to(T.e("c6") + 1.0, 0.35, 2.0).to(T.e("p4"), 0.0, 3.0),
              lantern=1.0,
              lantern_glow=Track(1.0).to(T.s("oooo") + 0.2, 0.55, 0.3).to(T.s("oooo") + 2.4, 1.0, 0.8),
              door_light=Track(0.0).to(T.s("thumps") + 2.95, 1.0, 0.12),
              shadow_fn=mom_shadow,
              page=dict(r_words=1.0))
    view = V.StageView(A, st)

    def add(t0, cam):
        shots.append((t0, view, cam))

    # b1 Biscuit
    bh = hy("biscuit", 1600, 1.12)
    add(T.s("b1") - 0.15, cam_at(930, bh, 2.2).k(T.s("b1"), dur=3.5, zoom=2.35, cy=bh + 200 / 2.35))
    # c1 Crumb
    ch = hy("crumb", 1800, 1.3)
    add(T.s("c1") - 0.1, cam_at(400, ch, 3.2, 820))
    # p1 Pip (looking off into the dark)
    ph = hy("pip", 1700, 1.15)
    add(T.s("p1") - 0.2, cam_at(220, ph, 2.4).k(T.s("p1"), dur=4.0, cx=200, zoom=2.6, cy=ph + 200 / 2.6))
    # w2 two-shot
    add(T.s("w2") - 0.1, cam_at(410, 1480, 1.6, 820).k(T.s("w2"), dur=3.5, zoom=1.75, cy=1480 + 140 / 1.75))
    # popup wide
    add(T.s("popup"), Cam(640, 1330, 0.92).k(T.s("popup"), dur=2.4, zoom=1.0, cx=560))
    # c2 tracking Crumb along the letters
    cam = Cam(LX[0] + 70, 1480, 1.9)
    cam.k(W_("c2", "O", 0) - 0.2, dur=0.5, cx=LX[1] + 40, keep=True)
    cam.k(W_("c2", "O", 1) - 0.2, dur=0.5, cx=LX[2] + 30, keep=True)
    add(T.s("c2") - 0.2, Cam(330, 1450, 1.35))
    add(T.s("c2") + 0.95, cam)
    add(W_("c2", "Too") - 0.1, Cam(LX[2] + 80, 1470, 1.65))
    # b2 Biscuit + Crumb
    add(T.s("b2") - 0.2, Cam(LX[2] + 70, 1440, 1.8).k(T.s("b2"), dur=3.0, zoom=1.9))
    # c3 Crumb's ghost
    cr_h = hy("crumb", 1505, 1.12)
    add(T.s("c3") - 0.2, cam_at(LX[2] + 10, cr_h, 3.0, 780))
    # oooo: pull back, everyone frozen
    cam = Cam(LX[2] + 120, 1420, 1.6).k(T.s("oooo"), dur=2.8, zoom=1.15, cx=560, cy=1360)
    cam.shake(T.s("oooo") + 0.3, 10, 1.2)
    add(T.s("oooo"), cam)
    # whispers: tight trio
    add(T.s("b3") - 0.2, Cam(LX[2] + 110, 1430, 1.7))
    # eyes in the dark
    cam = Cam(700, 1350, 1.2).k(T.s("eyes") + 0.3, dur=2.2, cx=980, cy=1240, zoom=1.7, keep=True)
    add(T.s("eyes"), cam)
    # k1: rise
    cam = Cam(1030, 1190, 1.9)
    cam.k(W_("k1", "table") - 0.4, dur=1.8, cx=960, cy=1020, zoom=1.0, keep=True)
    add(T.s("k1"), cam)
    # w3 low two-shot
    add(T.s("w3") - 0.4, Cam(960, 1060, 0.98).k(T.s("w3"), dur=4.0, zoom=1.04))
    # k2 cat close
    kh = 1330 - 480 * 1.45
    add(T.s("k2") - 0.3, cam_at(1060, kh, 1.9, 700).k(W_("k2", "I"), dur=2.5, zoom=2.1, cy=kh + 30 + 260 / 2.1))
    # k3: cat / mice reactions / cat
    add(T.s("k3") - 0.2, cam_at(1050, kh + 40, 1.8, 700))
    add(W_("k3", "box", edge="end") + 0.1, cam_at(700, 1400, 1.55, 830).k(W_("k3", "And"), dur=3.0, zoom=1.7))
    add(W_("k3", "Right") - 0.1, cam_at(1060, kh + 60, 2.2, 700))
    # p3 Pip close
    ph2 = hy("pip", 1555, 1.05)
    add(T.s("p3") - 0.3, cam_at(700, ph2, 3.3, 760))
    # k4 cat close, softer
    add(T.s("k4") - 0.4, cam_at(1050, kh + 40, 2.0, 700).k(T.s("k4"), dur=4.5, zoom=2.25, cy=kh + 40 + 260 / 2.25))
    # silence: wide, still
    add(T.s("silence"), Cam(760, 1240, 1.0).k(T.s("silence"), dur=1.8, zoom=1.15, cx=820, cy=1300))
    # w4 Wedge close
    wh = hy("wedge", 1610, 1.15)
    add(T.s("w4") - 0.2, cam_at(900, wh, 2.6, 760).k(T.s("w4"), dur=4.0, zoom=2.9, cy=wh + 200 / 2.9))
    # crumbwalks + c5: follow Crumb to the O
    cam = Cam(600, 1450, 1.4).k(T.s("crumbwalks") + 0.2, dur=1.4, cx=LX[2] + 20, cy=1390, zoom=1.9)
    add(T.s("crumbwalks"), cam)
    # c6 Crumb close, then pull back to the glowing letters
    crh = hy("crumb", 1508, 1.12)
    add(T.s("c6") - 0.4, cam_at(LX[2] + 10, crh, 3.0, 800))
    add(W_("c6", "remembers") - 0.1, Cam(520, 1330, 1.15))
    # p4 Pip close
    add(T.s("p4") - 0.5, cam_at(700, ph2, 3.0, 760).k(T.s("p4"), dur=7.5, zoom=3.6, cy=ph2 + 200 / 3.6))
    # b4 Biscuit close
    bh2 = hy("biscuit", 1490, 1.0)
    add(T.s("b4") - 0.5, cam_at(LX[2] + 118, bh2, 3.2, 760).k(T.s("b4"), dur=4.0, zoom=3.5, cy=bh2 + 200 / 3.5))
    # k5 cat, turned to the moon
    add(T.s("k5") - 0.8, cam_at(1000, kh, 1.45, 640).k(T.s("k5"), dur=7.0, zoom=1.6, cy=kh + 320 / 1.6))
    # c7 Crumb looks up at the cat
    add(T.s("c7") - 0.9, Cam(980, 1010, 1.08))
    # k6 cat close
    add(T.s("k6") - 1.0, cam_at(1060, kh + 60, 2.0, 700))
    # thumps
    cam = Cam(760, 1260, 1.0)
    for o in (0.05, 1.15):
        cam.shake(T.s("thumps") + o, 22, 0.35)
    add(T.s("thumps"), cam)
    sv = V.StairsView(dict(feet=Track(0.0).to(T.s("thumps") + 1.5, 0.8, 1.3, ease=lambda u: u), lamp=1.0))
    shots.append((T.s("thumps") + 1.55, sv, Cam(600, 1100, 1.25).shake(T.s("thumps") + 2.2, 16, 0.3)))
    cam = Cam(860, 1150, 0.86).shake(T.s("thumps") + 3.25, 20, 0.35)
    add(T.s("thumps") + 2.85, cam)
    # b5 / p5 / w5 panic
    add(T.s("b5") - 0.1, Cam(560, 1330, 1.45).k(T.s("b5"), dur=1.6, zoom=1.6))
    add(T.s("p5") - 0.15, cam_at(700, hy("pip", 1555, 1.05), 1.9, 960))
    add(T.s("w5") - 0.15, cam_at(860, hy("wedge", 1610, 1.15), 2.0, 800))
    p.k(T.s("p5"), pupil=0.35, brow=1.0, brow_tilt=0.5, dur=0.15)
    p.tremble(T.s("p5"), T.e("p5"), 2.0)
    p.look_at(T.s("p5"), (200, 700))
    p.k(W_("p5", "horns") - 0.3, arm_r=(130.0, -40.0), dur=0.25)
    b.k(T.s("b5") - 0.1, arm_l=(160.0, -20.0), arm_r=(160.0, -20.0), mouth=0.3, dur=0.15)
    b.k(T.e("b5"), arm_l=(-60.0, -80.0), arm_r=(-60.0, -80.0), mouth=0.0, dur=0.3)
    w.look_at(T.s("w5") - 0.2, None)
    w.k(T.s("w5") - 0.2, look=(-0.3, 0.2), brow=-0.6, brow_tilt=-0.7, pupil=0.8, ear_droop=0.0, arm_r=(70.0, -30.0),
        dur=0.25)
    w.k(W_("w5", "And"), lid=0.3, brow=-0.2, brow_tilt=-0.5, look=(-0.5, 0.0), arm_r=(130.0, -60.0), dur=0.3)
    for i in range(3):
        tt = W_("w5", "dare") + i * 0.18
        w.k(tt, arm_r=(130.0 + (10 if i % 2 else -10), -60.0), dur=0.09)
    for m in (p, b, cr):
        m.look_at(T.s("w5"), w)
        m.k(W_("w5", "back"), pupil=0.6, dur=0.2)
    return A


# =================================================================== SCRAMBLE BACK ONTO THE PAGE + MOM
def scramble_and_mom(shots):
    t = T.s("scramble")
    mice = {}
    land = {"wedge": 0.25, "pip": 0.55, "biscuit": 0.85, "crumb": 1.45}
    for i, (name, base) in enumerate(S_.PAGE_MICE.items()):
        a = Actor(name, "mouse:" + name, T, seed=40 + i, flat=True, **base)
        a.idle = 0.0
        if name == "tilt":
            a.snap(0, sleep=True)
        else:
            tl = t + land[name]
            a.snap(0, alpha=0.0, scale=base["scale"] * 1.9)
            a.k(tl - 0.25, alpha=1.0, dur=0.1)
            a.k(tl - 0.25, scale=base["scale"], dur=0.25, ease=ease_in)
            a.k(tl, squash=0.8, dur=0.06).k(tl + 0.08, squash=1.0, dur=0.2)
            a.k(tl + 0.3, pupil=0.6, brow=0.5, dur=0.2)
            a.hold_still(tl, T.s("wake2") + 0.3)
        if name == "biscuit":
            a.snap(0, upside=True)
        mice[name] = a
    # eyes darting while they hold their breath
    darts = {"wedge": [(-0.6, 0.2), (0.6, 0.2), (0.0, -0.4)], "pip": [(0.7, -0.5), (-0.3, 0.6), (0.6, 0.0)],
             "biscuit": [(0.5, 0.5), (-0.6, -0.4), (0.0, 0.6)], "crumb": [(-0.8, 0.0), (0.8, -0.2), (0.0, 0.5)]}
    for name, seq in darts.items():
        for j, lk in enumerate(seq):
            for base_t in (t + 1.8, T.s("pickup") + 1.2):
                mice[name].k(base_t + j * 0.55 + 0.1 * (hash(name) % 3), look=lk, dur=0.12)
    st = dict(ink=1.0, night=Track(0.22).to(t + 1.6, 0.42, 0.8), moonbeam=-2, beam_a=0.0)
    pv = V.PageView(mice, st, warm=0.8)
    shots.append((t, pv, Cam(540, 900, 1.0).k(t + 1.6, dur=1.0, zoom=1.08)))

    # ---- Mom in the doorway
    t = T.s("momenter")
    mom = Actor("mom", "mom", T, seed=9, x=540, y=470, scale=0.78, full=True, arms="candle", candle=0.0, lid=0.55,
                warm=1.0)
    mom.k(t + 0.4, scale=0.86, y=440, dur=2.0, ease=ease_in_out)
    mom.k(t + 1.7, lid=1.0, closed_curve=-0.5, mouth=1.0, mround=0.7, brow=0.6, dur=0.35)
    mom.k(t + 2.35, lid=0.6, closed_curve=0.0, mouth=0.0, mround=0.0, brow=0.0, dur=0.3)
    mom.hold_still(t + 1.5, t + 2.6)
    dv = V.DoorwayView(mom, dict(lit=Track(0.0).to(t + 1.2, 1.0, 1.2)))
    shots.append((t, dv, Cam(540, 980, 1.0).k(t, dur=3.0, zoom=1.06, cy=900)))

    # ---- Mom at the table: the pumpkin, then the drawing
    mt = Actor("mom2", "mom", T, seed=9, x=560, y=560, scale=1.05, arms="candle", candle=0.0, lid=0.55, warm=1.2,
               turn=-0.35, lean=-5.0, look=(-0.6, 0.85), smile=-0.15, brow=-0.1)
    mt.mouth_gain = 0.7
    mt.says("m1")
    mt.k(T.s("pickup") + 0.05, look=(0.65, 0.95), turn=0.25, lean=3.0, lid=0.05, brow=0.7, smile=0.0, dur=0.45)
    mt.blink_at(T.s("pickup") + 0.4)
    table_state = dict(page_y=Track(0.0).to(T.s("pickup") + 0.9, 1.0, 0.4, ease=ease_in))
    mv = MomTableView(mt, table_state)
    shots.append((T.s("m1") - 0.05, mv, Cam(560, 980, 1.0).k(T.s("m1"), dur=3.0, zoom=1.08, cy=930)))

    # POV: the drawing in her hands, the mice frozen (Biscuit upside down)
    pv2 = V.PageView(mice, dict(ink=1.0, night=0.12, moonbeam=-2, beam_a=0.0), warm=1.6)

    class Thumbs:
        def draw(self, c, tt, cam):
            pv2.draw(c, tt, cam, thumbs=1.0)
    shots.append((T.s("pickup") + 1.0, Thumbs(), Cam(560, 900, 1.06).k(T.s("pickup") + 1.0, dur=1.8, zoom=1.12,
                                                                        roll=-2.5)))

    # ---- Mom reads it
    m = Actor("mom3", "mom", T, seed=9, x=540, y=560, scale=1.3, arms="hold", candle=-1.0, warm=1.0, lid=0.12,
              look=(-0.55, 0.85), brow=0.2)
    m.mouth_gain = 0.62
    m.says("m2", "m3", "m4", "m5")
    m.base["paper"] = lambda c: V.paper_back(c, 0, 520, 360, rot=-3.0)
    for word, lx in (("Too", -0.55), ("Mom", 0.0), ("I", 0.35), ("love", 0.5), ("you", 0.7)):
        m.k(W_("m2", word) - 0.1, look=(lx, 0.85), dur=0.25)
    m.k(W_("m2", "love"), brow=0.55, dur=0.6)
    m.k(T.e("m2") - 0.1, lid=0.08, dur=0.3)
    # 'Two O's.' soft laugh, then remembering last year
    m.k(T.s("m3") - 0.5, smile=0.65, lid_low=0.45, look=(0.0, 0.7), brow=0.35, dur=0.5)
    m.nod(T.s("m3") + 0.1, 0.7)
    m.k(W_("m3", "Last") - 0.2, look=(-0.6, -0.55), lid_low=0.15, smile=0.45, brow=0.45, tilt=-5.0, dur=0.6)
    m.k(W_("m3", "squiggle") - 0.1, smile=0.7, lid_low=0.4, dur=0.5)
    # bittersweet
    m.k(T.s("m4") - 0.6, look=(0.0, 0.85), tilt=0.0, smile=0.2, lid_low=0.0, brow_tilt=0.75, brow=0.3, glisten=0.6,
        dur=0.8)
    m.k(W_("m4", "and") - 0.1, glisten=1.0, lid=0.28, smile=0.05, dur=0.7)
    m.k(W_("m4", "miss"), tear=0.01, dur=0.01).k(W_("m4", "miss"), tear=0.35, dur=1.0)
    # hug: presses it to her heart, eyes closed
    th = T.s("hug")
    m.k(th - 0.1, arms="hug", dur=0.01)
    m.k(th, lid=1.0, closed_curve=0.4, smile=0.45, brow_tilt=0.6, tear=1.0, dur=1.0)
    m.k(th, paper=(lambda c: V.paper_back(c, 0, 520, 360, rot=8.0)), dur=0.01)
    m.k(W_("m5", "baby") - 0.2, lid=0.15, closed_curve=0.0, smile=0.85, lid_low=0.35, brow_tilt=0.45, dur=0.5)
    m.k(W_("m5", "With"), smile=1.0, lid_low=0.5, dur=0.5)
    mv2 = V.MomView(m, {})
    shots.append((T.s("m2") - 0.3, mv2, Cam(540, 980, 1.0).k(T.s("m2"), dur=3.0, zoom=1.05, cy=940)))
    f = framing(540, 560, 1.45, 700)
    shots.append((T.s("m3") - 0.6, mv2, Cam(f["cx"], f["cy"], 1.4).k(T.s("m3"), dur=4.5, zoom=1.5)))
    shots.append((T.s("m4") - 0.7, mv2, Cam(f["cx"], f["cy"] - 10, 1.5).k(T.s("m4"), dur=4.0, zoom=1.68,
                                                                          cy=560 + 260 / 1.68)))
    shots.append((T.s("hug") - 0.15, mv2, Cam(540, 900, 1.05).k(T.s("hug"), dur=4.4, zoom=1.3, cy=760)))
    return mice


class MomTableView:
    """Mom over the table, the jack-o'-lantern lighting her from below."""

    def __init__(self, mom, state):
        self.mom = mom
        self.state = state

    def draw(self, c, t, cam):
        import skia
        from anim import q
        from gfx import W, H, fill, glow, lin_grad
        tq = q(t)
        page_y = self.state["page_y"].at(tq)
        c.save()
        cam.apply(c, 0.35)
        S_.draw_wall(c, (-900, -900, W + 900, H + 900))
        S_.draw_window(c, (-140, 60, 600, 1160), tq, moon_rel=(0.6, 0.5), moon_r=0.27, cobweb=False)
        c.restore()
        c.save()
        cam.apply(c, 1.0)
        V.draw_actor(c, self.mom, tq)
        S_.draw_table(c, (-600, 1560, W + 600, H + 900))
        if page_y < 1:
            dy = -page_y * 500
            S_.draw_page_in_quad(c, [(560, 1590 + dy), (980, 1584 + dy), (1060, 1700 + dy), (500, 1708 + dy)], tq,
                                 dict(ink=1.0, hide_wedge=False))
        S_.draw_lantern(c, 220, 1760, 230, tq, lit=1.0)
        c.restore()
        S_.vignette(c, 0.6)


# =================================================================== FRIDGE
def page_to_fridge(px, py):
    m = S_.paper_matrix(S_.fridge_page_quad())
    pt = m.mapXY(px, py)
    return pt.x(), pt.y()


def fridge(shots, scramble_mice):
    t_pin = T.s("fridge")
    mice = {}
    for i, (name, base) in enumerate(S_.PAGE_MICE.items()):
        a = Actor(name, "mouse:" + name, T, seed=40 + i, flat=True, **base)
        a.idle = 0.0
        if name == "biscuit":
            a.snap(0, upside=True)
        if name == "tilt":
            a.snap(0, sleep=True)
        a.hold_still(0, T.s("wake2") + 0.4)
        mice[name] = a
    sun = Actor("sun", "sun", T, seed=21, x=280, y=420, scale=0.95, lid=1.0, smile=0.5)
    ghost = Actor("ghost", "ghost", T, seed=22, x=790, y=420, scale=0.95)
    cat = Actor("cat2", "cat", T, seed=23, x=-300, y=1870, scale=0.75, facing=1, hidden=True, lid=0.3, light_dir=-1.0,
                lid_tilt=-0.2, pupil=0.9, look=(0.0, -1.0))
    momf = Actor("momf", "mom", T, seed=9, x=1010, y=640, scale=0.95, arms="candle", candle=0.0, warm=0.8, turn=-0.6,
                 look=(-1.0, 0.35), lid=0.2, hidden=True)
    sun.says("s1", "s2")
    ghost.says("g1")
    cat.says("k8")
    momf.says("m7")
    mice["pip"].says("p6")
    mice["biscuit"].says("b6", "b7")
    mice["crumb"].says("c8")
    mice["tilt"].says("t1")
    momf.mouth_gain = 0.65
    others = dict(sun=sun, ghost=ghost, cat=cat, mom=momf)
    st = dict(pin=Track(0.0).to(t_pin + 0.3, 1.0, 1.5, ease=ease_out),
              hand=Track(-1.0).to(t_pin + 0.2, 0.0, 0.01).to(t_pin + 0.3, 1.0, 1.5, ease=ease_out)
              .to(t_pin + 2.2, 2.0, 1.0, ease=ease_in).to(t_pin + 3.25, -1.0, 0.01),
              magnet=Track(0.0).to(t_pin + 1.8, 1.0, 0.01))
    fv = V.FridgeView(mice, others, st)
    shots.append((t_pin, fv, Cam(560, 1000, 1.0).k(t_pin + 1.5, dur=1.9, zoom=1.2, cy=950)))

    # ---- Mom squints at the fridge: was that one always upside down?
    t = T.s("m7") - 0.6
    momf.snap(t - 0.1, hidden=False)
    momf.k(t, lid=0.3, lid_low=0.5, brow=0.3, brow_tilt=-0.45, tilt=10.0, dur=0.5)
    momf.k(T.e("m7") + 0.3, tilt=0.0, lid_low=0.0, brow_tilt=0.0, dur=0.4)
    tl = T.s("momleave")
    momf.k(tl + 0.4, mouth=0.95, mround=0.6, lid=1.0, closed_curve=-0.4, dur=0.4)
    momf.k(tl + 1.1, mouth=0.0, mround=0.0, lid=0.5, closed_curve=0.0, dur=0.3)
    momf.k(tl + 1.3, x=1750, dur=1.2, ease=ease_in)
    momf.snap(tl + 2.6, hidden=True)
    shots.append((t, fv, Cam(640, 880, 1.12).k(t, dur=3.0, zoom=1.2)))

    # ---- the fridge wakes up
    t = T.s("wake2")
    for i, (name, a) in enumerate(mice.items()):
        if name == "tilt":
            continue
        a.blink_at(t + 0.3 + i * 0.12)
        a.k(t + 0.2 + i * 0.1, squash=0.9, dur=0.25).k(t + 0.5 + i * 0.1, squash=1.0, dur=0.4)
        a.k(t + 0.6, pupil=1.0, brow=0.0, dur=0.4)
    sun.k(t + 0.9, lid=0.0, dur=0.5)
    ghost.k(t + 0.6, wobble=1.0, dur=0.4).k(t + 1.2, wobble=-1.0, dur=0.4).k(t + 1.8, wobble=0.0, dur=0.4)
    for nm, lk in (("wedge", (0.6, -0.6)), ("pip", (-0.5, -0.8)), ("crumb", (0.4, -0.5)), ("biscuit", (0.5, 0.2))):
        mice[nm].k(t + 1.0, look=lk, dur=0.3)
    shots.append((t, fv, Cam(540, 960, 1.0).k(t, dur=2.2, zoom=1.05)))

    # ---- g1: BOO!
    tb = W_("g1", "Boo")
    ghost.k(tb - 0.1, scale=1.15, dur=0.12, ease=back_out).k(tb + 0.35, scale=0.95, dur=0.4)
    ghost.k(W_("g1", "Sorry") - 0.1, look=0.6, wobble=0.6, dur=0.3).k(T.e("g1"), wobble=0.0, dur=0.4)
    for nm, a in mice.items():
        if nm == "tilt":
            continue
        a.k(tb + 0.05, pupil=0.4, brow=1.0, scale=a.base["scale"] * 1.08, dur=0.08)
        a.k(tb + 0.35, scale=a.base["scale"], dur=0.25)
        a.k(W_("g1", "Habit"), pupil=1.0, brow=0.2, smile=0.45, dur=0.4)
        a.look_at(tb, page_to_fridge_inv(790, 420))
    shots.append((T.s("g1") - 0.1, fv, Cam(700, 640, 1.45).k(T.s("g1"), dur=3.0, zoom=1.5)))

    # ---- s1: welcome
    sun.k(T.s("s1") - 0.2, smile=0.8, look=0.5, dur=0.4)
    for nm, a in mice.items():
        if nm != "tilt":
            a.look_at(T.s("s1"), page_to_fridge_inv(280, 420))
    shots.append((T.s("s1") - 0.2, fv, Cam(420, 640, 1.45)))

    # ---- p6: do we get to stay?
    px, py = page_to_fridge(*[S_.PAGE_MICE["pip"][k] for k in ("x", "y")])
    pip = mice["pip"]
    pip.look_at(T.s("p6") - 0.3, page_to_fridge_inv(280, 420))
    pip.k(T.s("p6") - 0.3, brow=0.5, brow_tilt=0.55, glisten=0.8, ear_perk=0.5, smile=0.15, dur=0.4)
    pip.k(W_("p6", "stay") - 0.2, pupil=1.25, dur=0.4)
    f = framing(px, py, 3.8, 780)
    shots.append((T.s("p6") - 0.3, fv, Cam(f["cx"], f["cy"], 3.8).k(T.s("p6"), dur=2.4, zoom=4.1,
                                                                    cy=py + 180 / 4.1)))

    # ---- s2: the wonky ones
    sun.k(T.s("s2"), look=0.6, dur=0.3)
    sun.k(W_("s2", "purple") - 0.1, smile=1.0, dur=0.3)
    sun.k(W_("s2", "bigger") - 0.1, lid=0.5, dur=0.2).k(W_("s2", "other"), lid=0.0, dur=0.3)
    sun.k(W_("s2", "Nobody") - 0.1, smile=0.7, dur=0.4)
    sun.k(W_("s2", "wonky") - 0.1, lid=0.75, smile=1.0, dur=0.2).k(T.e("s2") + 0.3, lid=0.0, dur=0.3)
    for nm, a in mice.items():
        if nm == "tilt":
            continue
        a.k(W_("s2", "purple"), smile=0.6, lid_low=0.25, dur=0.6)
        a.k(W_("s2", "wonky"), smile=0.9, lid_low=0.4, glisten=0.4 if nm == "pip" else 0.0, dur=0.6)
    pip.k(W_("s2", "Nobody"), tear=0.01, dur=0.01).k(W_("s2", "Nobody"), tear=1.0, dur=2.5)
    f = framing(280, 420, 2.0, 640)
    shots.append((T.s("s2") - 0.2, fv, Cam(f["cx"], f["cy"], 1.9).k(T.s("s2"), dur=4.0, zoom=2.05)))
    shots.append((W_("s2", "Nobody") - 0.2, fv, Cam(430, 760, 1.25).k(W_("s2", "Nobody"), dur=4.0, zoom=1.32)))

    # ---- b6: upside-down Biscuit
    bx, by = page_to_fridge(*[S_.PAGE_MICE["biscuit"][k] for k in ("x", "y")])
    bis = mice["biscuit"]
    bis.k(T.s("b6") - 0.2, lid=0.5, smile=0.0, brow=0.0, look=(0.0, 0.0), lid_low=0.0, dur=0.3)
    bis.k(W_("b6", "Could") - 0.1, lid=0.0, brow=0.8, brow_tilt=0.6, pupil=1.2, dur=0.3)
    f = framing(bx, by, 4.6, 760)
    shots.append((T.s("b6") - 0.25, fv, Cam(f["cx"], f["cy"], 4.6)))

    # ---- catcurl / k8: the cat comes to say goodnight
    t = T.s("catcurl")
    cat.snap(t, hidden=False)
    cat.k(t + 0.1, x=430, dur=0.9, ease=ease_out)
    cat.hop(t + 0.1, 160, 0.9)
    cat.k(t + 1.1, look=(0.0, -1.0), lid=0.25, dur=0.4)
    cat.k(T.s("k8") - 0.1, smile=0.35, lid=0.3, lid_tilt=-0.4, dur=0.5)
    cat.blink_at(T.e("k8") + 0.2)
    for nm, a in mice.items():
        if nm != "tilt":
            a.look_at(t + 1.0, page_to_fridge_inv(430, 1500))
            a.k(t + 1.0, smile=0.5, dur=0.6)
    shots.append((t, fv, Cam(540, 1240, 0.95).k(t, dur=3.5, zoom=1.02)))

    # ---- c8: goodnight, cat... tomorrow, we draw him
    cx_, cy_ = page_to_fridge(*[S_.PAGE_MICE["crumb"][k] for k in ("x", "y")])
    crb = mice["crumb"]
    crb.k(T.s("c8") - 0.2, smile=0.8, lid_low=0.3, dur=0.4)
    crb.look_at(W_("c8", "Tomorrow") - 0.3, page_to_fridge_inv(*page_to_fridge(470, 640)))
    crb.k(W_("c8", "Tomorrow"), lid=0.35, brow=0.6, dur=0.3)
    for j in range(2):
        crb.k(W_("c8", "draw") + j * 0.25, brow=1.0, dur=0.1).k(W_("c8", "draw") + j * 0.25 + 0.12, brow=0.4, dur=0.1)
    f = framing(cx_, cy_, 4.6, 760)
    shots.append((T.s("c8") - 0.3, fv, Cam(f["cx"], f["cy"], 4.6)))

    # ---- t1 / b7: Tilt wakes up a moment too late
    tx_, ty_ = page_to_fridge(*[S_.PAGE_MICE["tilt"][k] for k in ("x", "y")])
    tilt = mice["tilt"]
    tilt.k(T.s("t1") - 0.2, sleep=False, lid=0.75, dur=0.01)
    tilt.k(W_("t1", "Did"), lid=0.35, look=(0.7, 0.2), dur=0.3)
    tilt.k(W_("t1", "anything") - 0.2, look=(0.9, 0.5), brow=0.5, dur=0.3)
    tilt.k(T.e("b7") - 0.4, lid=0.95, dur=0.4).k(T.e("b7"), sleep=True, dur=0.01)
    bis.look_at(T.s("t1"), page_to_fridge_inv(tx_, ty_))
    bis.k(T.s("b7") - 0.1, lid=0.0, pupil=1.3, brow=0.9, smile=0.5, dur=0.2)
    bis.k(W_("b7", "Go"), lid_low=0.4, smile=0.7, dur=0.3)
    mx_ = (tx_ + bx) / 2
    f = framing(mx_, (ty_ + by) / 2, 3.4, 760)
    shots.append((T.s("t1") - 0.3, fv, Cam(f["cx"], f["cy"], 3.4)))
    cat.k(T.e("b7") + 0.2, curl=1.0, lid=1.0, dur=0.01)
    return fv


def page_to_fridge_inv(x, y):
    """Look target on the fridge given in world coords, converted to paper coords for flat mice."""
    m = S_.paper_matrix(S_.fridge_page_quad())
    inv = skia_inv(m)
    pt = inv.mapXY(x, y)
    return pt.x(), pt.y()


def skia_inv(m):
    import skia
    inv = skia.Matrix()
    m.invert(inv)
    return inv


# =================================================================== EPILOGUE
def epilogue(shots):
    t = T.s("exterior")
    ev = V.ExteriorView(dict(kiss=Track(0.0).to(T.s("m8") - 0.7, 1.0, 0.8).to(T.e("m8") + 0.5, 0.0, 0.9)))
    wx, wy = 600 + 110 * 1.05, 1660 - 500 * 1.05
    cam = Cam(wx, wy + 60, 2.4)
    cam.k(T.e("m8") + 0.4, dur=T.e("n7") - T.e("m8") - 0.4, cx=560, cy=980, zoom=0.92, ease=ease_in_out, keep=True)
    shots.append((t, ev, cam))

    # morning: the mice drew the cat in
    t = T.s("morning")
    mice = {}
    for i, (name, base) in enumerate(S_.PAGE_MICE.items()):
        a = Actor(name, "mouse:" + name, T, seed=40 + i, flat=True, **base)
        a.idle = 0.0
        a.snap(0, lid=1.0, closed_curve=0.7, smile=0.6)
        a.hold_still(0, T.duration + 5)
        if name == "biscuit":
            a.snap(0, upside=True)
        mice[name] = a
    sun = Actor("sun", "sun", T, seed=21, x=280, y=420, scale=0.95, lid=1.0, smile=0.6)
    ghost = Actor("ghost", "ghost", T, seed=22, x=790, y=420, scale=0.95)
    cat = Actor("cat3", "cat", T, seed=24, x=470, y=1870, scale=0.78, facing=1, lid=0.3, light_dir=-1.0, pupil=0.7,
                lid_tilt=-0.3, look=(0.0, -1.0), smile=0.3)
    cat.blink_at(T.s("end") + 1.0)
    fv = V.FridgeView(mice, dict(sun=sun, ghost=ghost, cat=cat), dict(p_cat=True), morning=True)
    shots.append((t, EndCard(fv), Cam(540, 1000, 1.0).k(t, dur=T.duration - t, zoom=1.12, cy=930)))


class EndCard:
    def __init__(self, view):
        self.view = view

    def draw(self, c, t, cam):
        from gfx import font, text_center, clamp
        from letters import draw_text
        self.view.draw(c, t, cam)
        a = clamp((t - T.s("end")) / 0.8)
        if a > 0:
            import skia
            from gfx import fill, W, H, lin_grad
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 560), fill((0, 0, 0), 1.0, lin_grad((0, 0), (0, 560),
                                                                                      [(10, 6, 20, 0.75 * a), (10, 6, 20, 0)])))
            draw_text(c, "I LOVE YOU TOO", 66, 130, 88, style="paper", seed=5, alpha=a, weight=0.95)
            text_center(c, "Happy Halloween", 540, 360, font("Griffy-Regular.ttf", 76), (255, 196, 120), a=a,
                        outline=(20, 10, 20), outline_w=9)


# =================================================================== BUILD
def build(timeline):
    global T
    T = timeline
    shots = []
    prologue(shots)
    waking(shots)
    stage(shots)
    mice = scramble_and_mom(shots)
    fridge(shots, mice)
    # Mom & the cat on the windowsill (m6 + mrrp), in the kitchen
    mk = Actor("momk", "mom", T, seed=9, x=870, y=790, scale=1.1, arms="candle", candle=0.0, warm=0.8, turn=-0.7,
               look=(-1.0, 0.25), lid=0.15)
    mk.says("m6")
    mk.mouth_gain = 0.65
    mk.k(W_("m6", "mister") - 0.2, brow=0.6, brow_tilt=-0.35, smile=0.25, tilt=-6.0, dur=0.4)
    mk.k(W_("m6", "No"), smile=0.4, brow=0.2, dur=0.4)
    mk.nod(W_("m6", "drawings"), 0.8)
    kc = Actor("catk", "cat", T, seed=25, x=520, y=1112, scale=0.56, facing=1, layer="sill", lid=0.35, light_dir=1.0,
               pupil=0.6, look=(1.0, 0.2), lid_tilt=-0.1)
    tm = T.s("mrrp")
    kc.k(tm + 0.1, mouth=0.55, mround=0.6, dur=0.1).k(tm + 0.45, mouth=0.0, dur=0.15)
    kc.k(tm + 0.55, lid=1.0, dur=0.35).k(tm + 1.0, lid=0.35, dur=0.4)
    kc.k(tm, tail_amp=2.5, dur=0.3)
    kv = V.KitchenView(dict(momk=mk, catk=kc), dict(page_gone=True, lantern=1.0, title=0.0))
    shots.append((T.s("m6") - 0.2, kv, Cam(700, 1000, 1.05).k(T.s("m6"), dur=4.0, zoom=1.12)))
    epilogue(shots)
    shots.sort(key=lambda s: s[0])
    return shots
