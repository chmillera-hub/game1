"""engine/human.py -- ONE shared, data-driven full-body rig for every person.

    draw_person(ctx, who, x, y, s, t, pose="stand", expr="neutral", ...) -> anchors

Layout of this file (read top to bottom):
  1. small math / path helpers
  2. CHARS      -- per-character design data (proportions, colours, head shape)
  3. HANDS      -- hand-shape table (finger angles), blendable
  4. FACE       -- face parameter defaults, EXPR table, per-character tuning
  5. POSES      -- static pose table + CYCLES (wave tables) for animated poses
  6. solver     -- pose resolve/blend + 2.5D FK/IK skeleton (yaw-projected)
  7. drawing    -- limbs, hands, feet, torso/outfits, head/face, accessories
  8. draw_person

Conventions
  * Local rig units are logical px at s=1. Ground contact (x, y) is the origin;
    y grows DOWN (like the canvas).
  * Body frame (3D, before projection): x = screen-right when facing camera,
    y = down, z = toward camera ("forward").  `turn` yaws the body; points are
    projected orthographically (X = x cos + z sin) so limbs foreshorten.
  * Side names "l"/"r" = the side that appears on SCREEN-LEFT / SCREEN-RIGHT
    when flip=False and turn=0 (i.e. "l" is the character's anatomical right).
  * Limb angles are ABSOLUTE (not inherited from the spine) in radians:
      pitch  p : 0 = hanging straight down, +pi/2 = pointing forward, pi = up
      abduct o : 0 = along the body, + = out to that limb's own side
"""
import math
from engine.core import (PAL, hexc, mixc, clamp, lerp, smoothstep, blink_amount, noise1,
                         hash01, smooth_path, circle, ellipse, radial_glow)

TAU = 2 * math.pi
INK_W = 5.5            # outline width at s=1
TURN_RAD = 0.86        # body yaw (rad) at |turn| = 1  (~49 deg: a solid 3/4)
HEAD_TURN_RAD = 0.92   # head yaw per unit head turn


# ============================================================================
# 1. helpers
# ============================================================================
def _col(c):
    return hexc(c)


def _dk(c, k=0.25):
    """Darker shade of a colour (mixed toward ink)."""
    return mixc(c, PAL["ink"], k)


def _lt(c, k=0.25):
    return mixc(c, "#ffffff", k)


def _set(ctx, c):
    ctx.set_source_rgba(*(c if isinstance(c, tuple) else hexc(c)))


def _fill(ctx, c, preserve=False):
    _set(ctx, c)
    if preserve:
        ctx.fill_preserve()
    else:
        ctx.fill()


def _stroke(ctx, c, w, preserve=False):
    _set(ctx, c)
    ctx.set_line_width(w)
    if preserve:
        ctx.stroke_preserve()
    else:
        ctx.stroke()


def _fs(ctx, fc, w=INK_W, sc=None):
    """fill (preserve) + ink stroke current path."""
    _set(ctx, fc)
    ctx.fill_preserve()
    _set(ctx, sc or PAL["ink"])
    ctx.set_line_width(w)
    ctx.stroke()


def _rot(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c)


def _norm(x, y):
    d = math.hypot(x, y)
    return (x / d, y / d) if d > 1e-9 else (0.0, 1.0)


def _capsule(ctx, ax, ay, ra, bx, by, rb):
    """Convex hull of two circles (tapered tube) as a closed, CW sub-path."""
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    if d < 1e-6 or d <= abs(ra - rb):
        if ra >= rb:
            circle(ctx, ax, ay, ra)
        else:
            circle(ctx, bx, by, rb)
        return
    base = math.atan2(dy, dx)
    th = math.acos(clamp((ra - rb) / d, -1.0, 1.0))
    ctx.new_sub_path()
    ctx.arc(bx, by, rb, base - th, base + th)
    ctx.arc(ax, ay, ra, base + th, base + TAU - th)
    ctx.close_path()


def _tube(ctx, pts, radii):
    """Union of capsules along a polyline (adds sub-paths, same winding)."""
    for i in range(len(pts) - 1):
        _capsule(ctx, pts[i][0], pts[i][1], radii[i], pts[i + 1][0], pts[i + 1][1], radii[i + 1])


def _poly(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def _smooth(ctx, pts, closed=True, tension=0.5):
    smooth_path(ctx, pts, closed=closed, tension=tension)


def _lerp2(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def _qcurve(ctx, p0, c, p1):
    """Quadratic bezier p0 -> p1 with control c (as a cubic)."""
    ctx.curve_to(p0[0] + (c[0] - p0[0]) * 2 / 3, p0[1] + (c[1] - p0[1]) * 2 / 3,
                 p1[0] + (c[0] - p1[0]) * 2 / 3, p1[1] + (c[1] - p1[1]) * 2 / 3, p1[0], p1[1])


def _wave(p, base, amp=0.0, ph=0.0, a2=0.0, ph2=0.0, rect=0):
    v = math.sin(TAU * (p + ph))
    if rect == 1:
        v = max(0.0, v)
    elif rect == -1:
        v = min(0.0, v)
    return base + amp * v + (a2 * math.sin(2 * TAU * (p + ph2)) if a2 else 0.0)


# ============================================================================
# 2. CHARACTERS
# ============================================================================
# Head-local frame: origin = centre of the eye line, y down, units = px at s=1.
#   levels: (y, half-width a, front depth f, back depth b) from crown to chin;
#   the 3/4 silhouette is the projection of these cross-section ellipses.
# Torso: spine node heights above the pelvis and cross-section (a, f, b).
def _C(**kw):
    return kw


CHARS = {
    # ------------------------------------------------------------- Tiredness
    "tired": _C(
        seed=11, height=960, sex="m",
        foot_h=30, foot_len=74, foot_r=25, shoe="slipper",
        thigh=192, shin=184, hip_w=42, leg_r=(42, 35, 30), pants="sweat",
        spine=dict(hem=-34, waist=92, chest=190, shoulder=262, neck=280),
        tw=dict(hem=(96, 54, 56), hip=(96, 54, 56), waist=(97, 56, 56), chest=(102, 58, 58),
                shoulder=(98, 48, 48)),
        sw=90, neck_len=46, neck_r=30, arm=(138, 128), arm_r=(31, 27, 24), hand=46,
        top="hoodie", sleeve="long",
        head=dict(levels=[(-124, 0, 0, 0), (-112, 50, 42, 58), (-84, 84, 68, 92), (-44, 99, 82, 102),
                          (0, 101, 86, 98), (34, 97, 86, 86), (62, 86, 82, 64), (86, 62, 74, 38),
                          (100, 30, 64, 14)],
                  chin=106, pivot=0.70, ex=41, ew=27, eh=21, eye="almond", brow_y=-42,
                  brow_len=1.0, brow_th=11.5, nose_y=36, nose="soft", mouth_y=68, mw=24,
                  ear_y=(-6, 40), ear_w=17, hair="mop"),
        col=dict(skin=PAL["t_skin"], skin_sh=PAL["t_skin_sh"], hair=PAL["t_hair"],
                 brow=PAL["t_hair"], iris=PAL["t_iris"], top=PAL["t_hoodie"],
                 top_dk=PAL["t_hoodie_dk"], pants=PAL["t_pants"], pants_dk=_dk(PAL["t_pants"], 0.2),
                 shoe=PAL["t_slipper"], shoe_dk=_dk(PAL["t_slipper"], 0.22), bags=PAL["t_bags"],
                 lip=None),
        posture=dict(lean=0.08, chest=0.06, hunch=0.42, neck=0.30, nod=0.05, al_o=0.02, ar_o=0.02),
        face=dict(lid=0.45, brow=-0.22, bags=1.0, lidshade=0.55),
    ),
    # --------------------------------------------------------- Embarrassment
    "embar": _C(
        seed=23, height=1060, sex="m",
        foot_h=24, foot_len=78, foot_r=19, shoe="loafer",
        thigh=228, shin=222, hip_w=34, leg_r=(27, 22, 18), pants="slacks",
        spine=dict(hem=-26, waist=92, chest=196, shoulder=268, neck=284),
        tw=dict(hem=(78, 44, 46), hip=(78, 44, 46), waist=(76, 44, 44), chest=(84, 48, 48),
                shoulder=(82, 40, 40)),
        sw=80, neck_len=58, neck_r=21, arm=(164, 152), arm_r=(23, 20, 17), hand=46,
        top="labcoat", sleeve="long",
        head=dict(levels=[(-124, 0, 0, 0), (-112, 46, 40, 54), (-84, 80, 64, 88), (-44, 92, 76, 96),
                          (0, 93, 80, 92), (36, 88, 80, 78), (68, 74, 78, 52), (94, 46, 70, 26),
                          (108, 18, 60, 8)],
                  chin=113, pivot=0.70, ex=40, ew=27, eh=27, eye="round", brow_y=-50,
                  brow_len=0.95, brow_th=9.0, nose_y=40, nose="point", mouth_y=74, mw=24,
                  ear_y=(-6, 42), ear_w=19, hair="part", glasses=True),
        col=dict(skin=PAL["e_skin"], skin_sh=PAL["e_skin_sh"], hair=PAL["e_hair"],
                 brow=_dk(PAL["e_hair"], 0.34), iris=PAL["e_iris"], top=PAL["e_coat"],
                 top_dk=PAL["e_coat_sh"], vest=PAL["e_vest"], pants=PAL["e_pants"],
                 pants_dk=_dk(PAL["e_pants"], 0.25), shoe="#7a4a2e", shoe_dk="#4f2f1e", lip=None),
        posture=dict(lean=0.05, chest=0.07, hunch=0.22, neck=0.2, nod=0.0),
        face=dict(lid=0.02, brow=0.1),
    ),
    # --------------------------------------------------------------- the Boss
    "boss": _C(
        seed=37, height=1040, sex="f",
        foot_h=34, foot_len=66, foot_r=15, shoe="heel",
        thigh=220, shin=214, hip_w=36, leg_r=(28, 21, 15), pants="trousers",
        spine=dict(hem=-34, waist=96, chest=192, shoulder=262, neck=276),
        tw=dict(hem=(86, 46, 52), hip=(84, 46, 52), waist=(70, 40, 40), chest=(82, 48, 46),
                shoulder=(90, 40, 40)),
        sw=86, neck_len=56, neck_r=20, arm=(154, 144), arm_r=(23, 19, 15), hand=42,
        top="suit", sleeve="long",
        head=dict(levels=[(-120, 0, 0, 0), (-108, 44, 38, 52), (-80, 76, 62, 86), (-40, 88, 74, 92),
                          (0, 88, 76, 88), (34, 84, 76, 74), (66, 68, 74, 46), (92, 36, 66, 18),
                          (106, 12, 58, 6)],
                  chin=110, pivot=0.70, ex=37, ew=26, eh=17, eye="cat", brow_y=-40,
                  brow_len=1.0, brow_th=6.5, nose_y=38, nose="sharp", mouth_y=70, mw=20,
                  ear_y=(-4, 36), ear_w=15, hair="bob"),
        col=dict(skin=PAL["b_skin"], skin_sh=mixc(PAL["b_skin"], "#b98a7c", 0.5), hair=PAL["b_hair"],
                 brow="#8f94a2", iris=PAL["b_iris"], top=PAL["b_suit"], top_dk=PAL["b_suit_dk"],
                 pants=PAL["b_suit"], pants_dk=PAL["b_suit_dk"], shoe="#14151b", shoe_dk="#0b0b10",
                 lip=PAL["b_lip"]),
        posture=dict(lean=-0.03, hunch=-0.25, neck=-0.04, nod=-0.06),
        face=dict(lid=0.32, brow=-0.08, lidshade=0.3),
    ),
    # -------------------------------------------------------------- the Guard
    "guard": _C(
        seed=41, height=1000, sex="m",
        foot_h=34, foot_len=78, foot_r=26, shoe="boot",
        thigh=192, shin=184, hip_w=48, leg_r=(46, 39, 33), pants="uniform",
        spine=dict(hem=-30, waist=96, chest=196, shoulder=272, neck=290),
        tw=dict(hem=(112, 64, 64), hip=(112, 64, 64), waist=(116, 70, 62), chest=(122, 70, 64),
                shoulder=(118, 56, 52)),
        sw=110, neck_len=38, neck_r=36, arm=(140, 130), arm_r=(36, 32, 27), hand=52,
        top="uniform", sleeve="long",
        head=dict(levels=[(-120, 0, 0, 0), (-108, 52, 44, 60), (-80, 88, 70, 94), (-40, 102, 84, 104),
                          (0, 104, 88, 100), (36, 104, 90, 90), (68, 98, 88, 72), (92, 78, 82, 46),
                          (106, 40, 74, 18)],
                  chin=112, pivot=0.70, ex=40, ew=21, eh=17, eye="small", brow_y=-36,
                  brow_len=1.08, brow_th=13, nose_y=38, nose="broad", mouth_y=74, mw=26,
                  ear_y=(-6, 40), ear_w=18, hair="cap", mustache=True),
        col=dict(skin=PAL["g_skin"], skin_sh=_dk(PAL["g_skin"], 0.2), hair="#231916",
                 brow="#231916", iris="#3b2618", top=PAL["g_uniform"], top_dk=_dk(PAL["g_uniform"], 0.3),
                 pants=_dk(PAL["g_uniform"], 0.12), pants_dk=_dk(PAL["g_uniform"], 0.35),
                 shoe="#1b1b22", shoe_dk="#0d0d12", lip=None),
        posture=dict(lean=-0.02, chest=-0.05, hunch=0.05, neck=0.05, al_o=0.12, ar_o=0.12),
        face=dict(lid=0.16, brow=-0.05),
    ),
    # ------------------------------------------------------- the Receptionist
    "recep": _C(
        seed=53, height=990, sex="f",
        foot_h=26, foot_len=64, foot_r=16, shoe="flat",
        thigh=200, shin=192, hip_w=38, leg_r=(31, 24, 17), pants="trousers",
        spine=dict(hem=-30, waist=90, chest=184, shoulder=252, neck=266),
        tw=dict(hem=(88, 48, 54), hip=(86, 48, 54), waist=(74, 42, 42), chest=(82, 50, 46),
                shoulder=(80, 40, 40)),
        sw=78, neck_len=50, neck_r=20, arm=(146, 136), arm_r=(24, 21, 17), hand=42,
        top="cardigan", sleeve="long",
        head=dict(levels=[(-120, 0, 0, 0), (-108, 46, 40, 54), (-80, 80, 64, 88), (-40, 92, 76, 94),
                          (0, 93, 78, 90), (34, 88, 78, 76), (64, 74, 76, 50), (90, 44, 68, 22),
                          (104, 14, 60, 6)],
                  chin=108, pivot=0.70, ex=38, ew=25, eh=19, eye="almond", brow_y=-40,
                  brow_len=0.95, brow_th=7.5, nose_y=38, nose="soft", mouth_y=70, mw=20,
                  ear_y=(-4, 38), ear_w=15, hair="bun"),
        col=dict(skin=PAL["r_skin"], skin_sh=mixc(PAL["r_skin"], "#a8704e", 0.45), hair="#4a2f25",
                 brow="#3e271f", iris="#5b3b2a", top=PAL["r_top"], top_dk=_dk(PAL["r_top"], 0.25),
                 blouse="#f4f1f6", pants="#3c3a4a", pants_dk="#2a2836", shoe="#2b2530",
                 shoe_dk="#1a161d", lip="#c4587a"),
        posture=dict(lean=0.03, hunch=0.15, neck=0.12),
        face=dict(lid=0.5, brow=-0.12, lidshade=0.35),
    ),
}

# outfit overrides (colour + garment swaps)
OUTFITS = {
    ("tired", "printer"): dict(top="polo", sleeve="short", shoe="sneaker", pants="khaki",
                               col=dict(top=PAL["polo"], top_dk=_dk(PAL["polo"], 0.2),
                                        pants=PAL["khaki"], pants_dk=_dk(PAL["khaki"], 0.22),
                                        shoe="#6b4f3a", shoe_dk="#46321f")),
    ("tired", "sewer"): dict(wet=True, col=dict(hair=_dk(PAL["t_hair"], 0.15),
                                                top=_dk(PAL["t_hoodie"], 0.1),
                                                shoe=mixc(PAL["t_slipper"], "#5b7a6a", 0.45),
                                                shoe_dk=_dk(mixc(PAL["t_slipper"], "#5b7a6a", 0.45), 0.25))),
}

# Furniture heights relative to the ground point (px at s=1), per character.
#   SEAT_H : chair seat surface (sit_chair / sit_game / sit_desk)
#   DESK_H : desk / counter top (sit_desk, type, cover_sweater, slide)
#   SILL_H : window sill line (look_window)
SEAT_H = {k: int(c["shin"] + c["foot_h"] + 8) for k, c in CHARS.items()}
DESK_H = {k: int(c["height"] * 0.47) for k, c in CHARS.items()}
SILL_H = {k: int(c["height"] * 0.56) for k, c in CHARS.items()}


# ============================================================================
# 3. HANDS  (4-finger cartoon hands; numeric so shapes blend)
# ============================================================================
# Hand frame: origin = wrist, +x = toward the fingers, +y = thumb side.
# Units: palm length = 1 (scaled by CHARS[who]["hand"]).
# fingers (index, middle, ring, pinky): (spread angle, length, bend1, bend2)
#   bends curl toward the thumb side (+y).  thumb: (angle, length, bend).
#   hold: (x, y) grip / contact point used for the hand anchor + hold().
def _H(palm=1.0, f=None, th=(0.6, 0.72, 0.2), hold=(0.85, 0.05), cup=0.0):
    return dict(palm=palm, f=f, th=th, hold=hold, cup=cup)


_CURL = (0.0, 0.52, 1.55, 1.6)
HANDS = {
    "open":    _H(f=[(0.30, 0.86, 0.06, 0.05), (0.08, 0.95, 0.04, 0.04), (-0.13, 0.87, 0.04, 0.04),
                     (-0.36, 0.67, 0.06, 0.05)], th=(1.0, 0.78, 0.08), hold=(0.75, 0.0)),
    "relaxed": _H(f=[(0.12, 0.84, 0.34, 0.34), (0.03, 0.92, 0.38, 0.4), (-0.06, 0.85, 0.42, 0.44),
                     (-0.15, 0.66, 0.48, 0.5)], th=(0.5, 0.7, 0.28), hold=(0.8, 0.12)),
    "fist":    _H(palm=0.86, f=[(0.06,) + _CURL[1:], (0.0,) + _CURL[1:], (-0.05,) + _CURL[1:],
                                (-0.1, 0.46, 1.6, 1.6)], th=(1.3, 0.6, 1.25), hold=(0.8, 0.1)),
    "point":   _H(palm=0.9, f=[(0.0, 0.98, 0.0, 0.0), (0.0,) + _CURL[1:], (-0.05,) + _CURL[1:],
                               (-0.1, 0.46, 1.6, 1.6)], th=(0.82, 0.72, 0.05), hold=(1.6, 0.34)),
    "grip":    _H(palm=0.92, f=[(0.06, 0.86, 1.2, 1.35), (0.0, 0.92, 1.25, 1.35), (-0.05, 0.86, 1.3, 1.35),
                                (-0.1, 0.68, 1.35, 1.4)], th=(1.15, 0.68, 0.95), hold=(1.02, 0.22)),
    "splay":   _H(f=[(0.50, 0.92, 0.0, 0.0), (0.17, 1.0, 0.0, 0.0), (-0.17, 0.93, 0.0, 0.0),
                     (-0.5, 0.72, 0.0, 0.0)], th=(1.3, 0.8, 0.0), hold=(0.7, 0.0)),
    "pinch":   _H(f=[(0.3, 0.84, 0.85, 0.75), (0.0, 0.8, 1.25, 1.3), (-0.05, 0.76, 1.3, 1.35),
                     (-0.1, 0.6, 1.35, 1.4)], th=(0.62, 0.84, 0.3), hold=(1.42, 0.52)),
    "flat":    _H(f=[(0.05, 0.88, 0.0, 0.0), (0.0, 0.97, 0.0, 0.0), (-0.05, 0.89, 0.0, 0.0),
                     (-0.1, 0.69, 0.0, 0.0)], th=(0.42, 0.75, 0.04), hold=(0.85, 0.0)),
    "claw":    _H(f=[(0.38, 0.86, 0.75, 0.8), (0.13, 0.94, 0.75, 0.8), (-0.13, 0.87, 0.75, 0.8),
                     (-0.38, 0.68, 0.8, 0.85)], th=(1.05, 0.75, 0.55), hold=(0.8, 0.1)),
    "cup":     _H(f=[(0.1, 0.86, 0.22, 0.2), (0.02, 0.94, 0.22, 0.2), (-0.06, 0.87, 0.24, 0.22),
                     (-0.14, 0.67, 0.28, 0.25)], th=(0.75, 0.74, 0.12), hold=(0.7, 0.3), cup=1.0),
}


def _hand_vec(name):
    h = HANDS[name] if isinstance(name, str) else name
    v = [h["palm"], h["cup"], h["hold"][0], h["hold"][1]]
    for f in h["f"]:
        v.extend(f)
    v.extend(h["th"])
    return v


_HAND_VEC = {k: _hand_vec(k) for k in HANDS}


# ============================================================================
# 4. FACE
# ============================================================================
# Every key is ADDITIVE (expr deltas and `face=` deltas are summed onto the
# character's base).  Eye keys also accept _l / _r suffixes (per eye).
EYE_KEYS = ("brow", "brow_ang", "brow_in", "brow_out", "lid", "lid_ang", "lower",
            "pupil", "iris", "hl", "eye_size", "look_x", "look_y")
FACE_DEFAULTS = dict(
    # eyes / brows (per eye with _l/_r)
    brow=0.0, brow_ang=0.0, brow_in=0.0, brow_out=0.0, lid=0.0, lid_ang=0.0, lower=0.0,
    pupil=1.0, iris=1.0, hl=1.0, eye_size=1.0, look_x=0.0, look_y=0.0,
    # mouth
    curve=0.0, width=1.0, asym=0.0, lip_up=0.0, lip_low=0.0, open=0.0, teeth=0.0, tongue=0.0,
    frown=0.0, press=0.0, smirk=0.0, jaw=0.0, wobble=0.0,
    # misc
    cheek=0.0, flare=0.0, head_tilt=0.0, head_turn=0.0, head_nod=0.0, squash=0.0,
    bags=0.0, lidshade=0.0, blush=0.0, focus=1.0, tear=0.0,
)

# Expression deltas (relative to the character's resting face).
EXPR = {
    # --- basics
    "neutral":    {},
    "bored":      dict(lid=0.12, lid_ang=0.12, brow=-0.08, curve=-0.12, press=0.1, look_y=0.05),
    "deadpan":    dict(lid=0.08, brow=-0.04, press=0.22, width=0.9),
    "annoyed":    dict(brow=-0.2, brow_ang=-0.55, lid=0.14, lid_ang=-0.12, curve=-0.3, press=0.35,
                       asym=0.15, flare=0.3),
    "unamused":   dict(lid=0.24, brow_l=-0.1, brow_r=0.28, brow_ang_r=0.1, curve=-0.2, press=0.35,
                       smirk=-0.15, lid_ang=0.06),
    "squint":     dict(lid=0.32, lower=0.42, brow=-0.3, brow_ang=-0.35, curve=-0.12, press=0.15,
                       cheek=0.15),
    "sigh":       dict(lid=0.36, brow=0.12, brow_ang=0.32, open=0.16, width=0.78, lip_up=0.05,
                       head_nod=0.12, cheek=0.25, lid_ang=0.12),
    "content":    dict(lid=0.62, lower=0.36, curve=0.5, brow=0.12, brow_ang=0.18, cheek=0.1,
                       head_tilt=0.04),
    "soft_smile": dict(curve=0.32, lower=0.16, lid=0.05, brow=0.05, brow_ang=0.08),
    "curious":    dict(brow_l=0.42, brow_r=-0.04, brow_ang_l=0.12, lid=-0.08, lid_l=-0.08,
                       head_tilt=0.12, curve=0.04, pupil=1.1, asym=0.12),
    # --- big reactions
    "surprised":  dict(brow=0.78, lid=-0.34, pupil=0.78, open=0.36, width=0.66, eye_size=1.08,
                       squash=-0.04),
    "alarmed":    dict(brow=0.68, brow_ang=0.4, lid=-0.34, pupil=0.62, open=0.24, width=1.08,
                       curve=-0.42, teeth=0.5, eye_size=1.08),
    "scream":     dict(brow=0.92, brow_ang=0.55, lid=-0.4, pupil=0.45, open=1.0, width=1.18,
                       curve=-0.35, tongue=0.85, teeth=0.6, lip_up=0.4, squash=-0.12,
                       eye_size=1.14, flare=0.6),
    "pain":       dict(lid=0.9, lower=0.5, brow=-0.1, brow_ang=0.62, brow_in=0.3, open=0.42,
                       teeth=1.0, width=1.22, curve=-0.5, cheek=0.2, squash=0.04, flare=0.5),
    "groggy":     dict(lid=0.36, lid_l=0.12, brow=0.06, brow_ang=0.22, curve=-0.06, open=0.06,
                       head_tilt=0.08, pupil=1.12, focus=0.6, asym=0.15),
    "dazed":      dict(lid_l=0.12, lid_r=0.38, lid_ang_l=0.15, brow_l=0.25, brow_r=-0.05,
                       brow_ang=0.2, pupil=0.75, open=0.16, width=0.8, asym=0.35, wobble=0.35,
                       look_x_l=0.2, look_y_l=-0.12, look_x_r=-0.18, look_y_r=0.18, focus=0.0,
                       head_tilt=0.1),
    "determined": dict(lid=-0.28, brow=-0.2, brow_ang=-0.45, lower=0.12, press=0.42, curve=-0.06,
                       pupil=0.95, hl=1.2, head_nod=0.05),
    "awe":        dict(lid=-0.46, brow=0.52, brow_ang=0.26, pupil=1.25, hl=1.45, open=0.3,
                       width=0.82, lip_low=0.1, eye_size=1.06),
    "sad":        dict(brow=0.1, brow_ang=0.68, brow_in=0.2, lid=0.16, lid_ang=0.3, curve=-0.42,
                       frown=0.3, pupil=1.22, hl=1.35, look_y=0.18, head_nod=0.08),
    # --- Embarrassment's nervous range
    "nervous_smile": dict(curve=0.58, width=1.32, open=0.22, teeth=1.0, brow=0.25, brow_ang=0.48,
                          lid=-0.06, wobble=0.5, pupil=0.72, cheek=0.15, blush=0.35),
    "panic":      dict(brow=0.82, brow_ang=0.62, lid=-0.36, pupil=0.45, open=0.6, width=1.1,
                       curve=-0.5, teeth=0.5, wobble=0.45, eye_size=1.1, blush=0.25),
    "terrified":  dict(brow=0.92, brow_ang=0.72, lid=-0.42, pupil=0.32, iris=0.72, open=0.42,
                       width=1.2, teeth=1.0, curve=-0.62, wobble=0.6, squash=-0.06, eye_size=1.14),
    "relieved":   dict(lid=0.42, brow=0.1, brow_ang=0.36, curve=0.32, open=0.12, width=0.9,
                       cheek=0.2, head_nod=-0.06),
    "pleading":   dict(brow=0.26, brow_ang=0.82, brow_in=0.25, lid=-0.1, pupil=1.38, hl=1.6,
                       curve=-0.2, wobble=0.35, lower=0.1, frown=0.2, blush=0.25),
    "guilty":     dict(brow=0.05, brow_ang=0.46, lid=0.2, lid_ang=0.1, look_x=-0.35, look_y=0.4,
                       curve=-0.16, press=0.4, asym=-0.2, blush=0.4),
    "frozen_shock": dict(eye_size=1.3, lid=-0.45, brow=1.0, pupil=0.3, iris=0.0, hl=0.4, press=0.65,
                         width=0.78, wobble=1.0, curve=-0.12, squash=-0.05, blush=0.12),
    "whisper":    dict(open=0.12, width=0.52, lip_up=0.08, brow=0.2, brow_ang=0.32, lid=-0.04,
                       curve=-0.02),
    "sheepish":   dict(curve=0.36, asym=0.25, smirk=0.2, brow=0.12, brow_ang=0.42, lid=0.16,
                       look_x=-0.3, look_y=0.25, teeth=0.7, open=0.08, width=1.12, blush=0.5),
    "fake_cool":  dict(lid=0.26, brow_l=0.3, brow_r=-0.06, curve=0.3, smirk=0.5, wobble=0.22,
                       brow_ang=-0.06, blush=0.2, head_tilt=-0.06),
    # --- others
    "cold":       dict(lid=0.1, brow=-0.05, press=0.32, curve=-0.05),
    "stern":      dict(brow=-0.26, brow_ang=-0.46, lid=0.12, press=0.5, curve=-0.26),
    "yawn":       dict(lid=1.0, lower=0.4, brow=0.42, brow_ang=0.3, open=1.0, width=0.8, tongue=0.6,
                       teeth=0.3, squash=-0.14, head_nod=-0.25, lip_up=0.2, cheek=0.3),
}

# Per-character expression gains (applied to EXPR deltas, not to `face=`):
#   key -> multiplier;  "key-" applies to negative deltas only;  "*" = all.
EXPR_GAIN = {
    "tired": {"lid-": 0.5, "eye_size": 0.6, "brow": 0.85},
    "boss": {"*": 0.4},
    "recep": {"lid-": 0.7},
}
# Per-character additive tweaks for specific expressions (after gain).
CHAR_EXPR = {
    "tired": {
        "determined": dict(lid=-0.2, brow_ang=-0.1, lower=0.05),   # lids lift: rare and important
        "awe": dict(lid=-0.26, brow=0.1),                          # fully open: the payoff
        "bored": dict(lid=0.04),
    },
    "boss": {"cold": dict(lid=0.06, press=0.15), "stern": dict(brow_ang=-0.15, lid=0.05)},
}


# ============================================================================
# 5. POSES
# ============================================================================
# A pose is a dict of joint values layered on top of POSE_DEFAULTS ("stand").
# Values may be numbers, hand names (strings), or W(...) waves (cycles; they
# are evaluated at phase = pose_t / period).  Keys:
#   global : turn dx dy rot plant hip_h lift plant_hands lean chest side twist
#            hip_roll hunch neck nod tilt head_yaw breath sway posture coat_trail
#   arm  a{l,r}_ : p o e eo w (FK, 3D)  h (hand) tf (thumb side +1/-1) hide
#            ik (0..1 weight of 2D IK) tx ty tz (ground target in units of the
#            character height: x outward, y above ground, z forward)
#            th hx hy (head-relative target, head px, x outward) grab (reach the
#            other forearm) cup (reach the headphone cup) wa wabs (absolute hand
#            angle, 0 = forward) bend (+1 elbow out/down, -1 elbow in/up)
#            layer ('back'|'mid'|'front') thumb fing (thumb / finger animation)
#   leg  l{l,r}_ : p o k ko a
def W(base, amp=0.0, ph=0.0, a2=0.0, ph2=0.0, r=0):
    """Wave value for cycle tables: base + amp*sin(2pi(p+ph)) + a2*sin(4pi(p+ph2)).
    r=1 keeps only the positive half (rectified)."""
    return ("~", base, amp, ph, a2, ph2, r)


def A(side, p=None, o=None, e=None, eo=None, w=None, h=None, **kw):
    d = {}
    for k, v in (("p", p), ("o", o), ("e", e), ("eo", eo), ("w", w), ("h", h)):
        if v is not None:
            d[f"a{side}_{k}"] = v
    for k, v in kw.items():
        d[f"a{side}_{k}"] = v
    return d


def IK(side, tx, ty, tz=0.1, h=None, w=1.0, **kw):
    d = {f"a{side}_ik": w, f"a{side}_tx": tx, f"a{side}_ty": ty, f"a{side}_tz": tz}
    if h is not None:
        d[f"a{side}_h"] = h
    for k, v in kw.items():
        d[f"a{side}_{k}"] = v
    return d


def HK(side, hx, hy, h=None, w=1.0, **kw):
    """IK target relative to the head centre (head px; x outward from the face centre)."""
    d = {f"a{side}_ik": w, f"a{side}_th": 1.0, f"a{side}_hx": hx, f"a{side}_hy": hy}
    if h is not None:
        d[f"a{side}_h"] = h
    for k, v in kw.items():
        d[f"a{side}_{k}"] = v
    return d


def L(side, p=None, o=None, k=None, a=None, ko=None):
    d = {}
    for kk, v in (("p", p), ("o", o), ("k", k), ("a", a), ("ko", ko)):
        if v is not None:
            d[f"l{side}_{kk}"] = v
    return d


def P(*parts, **kw):
    d = {}
    for p in parts:
        d.update(p)
    d.update(kw)
    return d


POSE_DEFAULTS = dict(
    turn=0.0, dx=0.0, dy=0.0, rot=0.0, plant=1.0, hip_h=0.0, lift=0.0, plant_hands=0.0,
    lean=0.0, chest=0.0, side=0.0, twist=0.0, hip_roll=0.0, hunch=0.0, neck=0.0, nod=0.0,
    tilt=0.0, head_yaw=0.0, breath=1.0, sway=1.0, posture=1.0, coat_trail=0.0,
    hold=0.0, hold_order=0.0, controller=0.0, counter=0.0,
)
for _s in "lr":
    POSE_DEFAULTS.update({f"a{_s}_p": 0.05, f"a{_s}_o": 0.1, f"a{_s}_e": 0.2, f"a{_s}_eo": 0.0,
                          f"a{_s}_w": 0.0, f"a{_s}_h": "relaxed", f"a{_s}_tf": 1.0, f"a{_s}_hide": 0.0,
                          f"a{_s}_ik": 0.0, f"a{_s}_tx": 0.1, f"a{_s}_ty": 0.5, f"a{_s}_tz": 0.1,
                          f"a{_s}_th": 0.0, f"a{_s}_hx": 0.0, f"a{_s}_hy": 0.0, f"a{_s}_grab": 0.0,
                          f"a{_s}_cup": 0.0, f"a{_s}_wa": 0.0, f"a{_s}_wabs": 0.0, f"a{_s}_bend": 1.0,
                          f"a{_s}_layer": "", f"a{_s}_thumb": 0.0, f"a{_s}_fing": 0.0})
    POSE_DEFAULTS.update({f"l{_s}_p": 0.0, f"l{_s}_o": 0.05, f"l{_s}_k": 0.03, f"l{_s}_ko": 0.0,
                          f"l{_s}_a": 0.0})

_SEAT = dict(plant=0.0, hip_h="seat", **L("l", 1.42, 0.1, 1.42, 0.0), **L("r", 1.42, 0.1, 1.42, 0.0))
_HANDS_BACK = P(A("l", -0.3, 0.16, 0.5, -0.75, h="relaxed", layer="back"),
                A("r", -0.3, 0.16, 0.5, -0.75, h="relaxed", layer="back"))
_CROSSED = P(A("l", 0.3, 0.16, 1.3, -1.32, 0.1, h="relaxed", layer="front", tf=1.0),
             A("r", 0.32, 0.16, 1.22, -1.25, 0.25, h="fist", layer="mid"), hunch=0.15)

POSES = {
    # ------------------------------------------------------------ standing
    "stand": {},
    "slouch": P(A("l", -0.02, 0.06, 0.12), A("r", -0.02, 0.06, 0.12), L("l", k=0.1), L("r", k=0.08),
                lean=0.16, chest=0.12, hunch=0.75, neck=0.42, nod=0.1, hip_roll=0.05),
    "arms_crossed": P(_CROSSED, L("l", o=0.09), L("r", o=0.09)),
    "hands_pockets": P(A("l", 0.0, 0.26, 0.32, -0.42, hide=1.0), A("r", 0.0, 0.26, 0.32, -0.42, hide=1.0),
                       hunch=0.35),
    "hands_behind_back": P(_HANDS_BACK, chest=-0.04),
    "attention": P(A("l", 0.0, 0.06, 0.02, h="flat", tf=1.0), A("r", 0.0, 0.06, 0.02, h="flat"),
                   L("l", o=0.0, k=0.0), L("r", o=0.0, k=0.0), posture=0.1, lean=-0.03, chest=-0.1,
                   hunch=-0.35, neck=-0.12, nod=-0.16, breath=0.35, sway=0.0),
    "awkward": P(IK("l", 0.02, 0.43, 0.12, "relaxed", wa=1.5, wabs=0.6),
                 IK("r", 0.0, 0.42, 0.13, "relaxed", wa=1.5, wabs=0.6),
                 L("l", o=-0.02, k=0.12), L("r", o=-0.02, k=0.12), hunch=1.0, lean=0.03, neck=0.12,
                 nod=0.06),
    "sheepish": P(HK("r", 70, -40, "claw", layer="mid", bend=-1.0, wa=-1.9, wabs=0.7),
                  A("l", 0.02, 0.05, 0.15), hunch=0.6, tilt=-0.12, nod=0.08, lean=0.03),
    "plead": P(IK("l", -0.005, 0.64, 0.16, "flat", wa=-1.45, wabs=0.9, layer="front"),
               IK("r", -0.005, 0.64, 0.16, "flat", wa=-1.45, wabs=0.9, layer="front"),
               lean=0.1, hunch=0.5, nod=-0.08, neck=0.1, L("l", k=0.12), L("r", k=0.12)),
    "cover_eyes": P(HK("l", 16, 2, "flat", layer="front", wa=-1.7, wabs=0.85, bend=1.0),
                    HK("r", 16, 2, "flat", layer="front", wa=-1.7, wabs=0.85, bend=1.0),
                    hunch=0.7, nod=0.12, neck=0.1),
    "peek": P(HK("l", 8, -6, "splay", layer="front", wa=-1.62, wabs=0.9),
              HK("r", 8, -6, "splay", layer="front", wa=-1.62, wabs=0.9),
              hunch=0.7, nod=0.08, neck=0.1),
    "facepalm": P(HK("r", -6, -28, "flat", layer="front", wa=-1.9, wabs=0.8),
                  A("l", 0.02, 0.06, 0.15), nod=0.22, tilt=-0.1, hunch=0.4, neck=0.2),
    "shrug": P(A("l", 0.05, 0.34, 1.35, 0.85, -0.3, h="open", tf=-1.0),
               A("r", 0.05, 0.34, 1.35, 0.85, -0.3, h="open", tf=-1.0), hunch=1.0, tilt=0.12),
    "point": P(A("r", 0.3, 1.3, 0.06, 0.0, 0.0, h="point", tf=1.0), A("l", 0.02, 0.06, 0.15),
               side=-0.03, turn=0.25),
    "hold_arm": P(A("l", 0.12, -0.1, 0.95, -1.0, 0.0, h="relaxed"),
                  P(A("r", 0.2, 0.1, 1.0), {"ar_ik": 1.0, "ar_grab": 1.0, "ar_h": "grip", "ar_layer": "front"}),
                  hunch=0.55, nod=0.08),
    "lean_in": P(_HANDS_BACK, L("l", -0.12, k=0.12), L("r", 0.12, k=0.05), lean=0.48, chest=0.12,
                 neck=0.28, nod=-0.18, hunch=0.25),
    "look_window": P(IK("l", 0.12, 0.56, 0.26, "flat", wa=0.1, wabs=0.9),
                     IK("r", 0.12, 0.56, 0.26, "flat", wa=0.1, wabs=0.9),
                     lean=0.32, neck=0.12, nod=-0.08, L("l", k=0.06), L("r", k=0.06)),
    # ------------------------------------------------------------ seated / floor
    "sit_chair": P(_SEAT, A("l", 0.32, 0.12, 0.85, -0.1, 0.3), A("r", 0.32, 0.12, 0.85, -0.1, 0.3)),
    "sit_game": P(_SEAT, IK("l", 0.06, "seat+0.16", 0.24, "grip", layer="front", wa=-0.4, wabs=0.6),
                  IK("r", 0.06, "seat+0.16", 0.24, "grip", layer="front", wa=-0.4, wabs=0.6),
                  lean=0.3, chest=0.1, hunch=0.65, neck=0.5, nod=-0.16, controller=1.0),
    "sit_desk": P(_SEAT, IK("l", 0.1, "desk", 0.3, "relaxed", wa=0.25, wabs=0.85, layer="front"),
                  IK("r", 0.1, "desk", 0.3, "relaxed", wa=0.25, wabs=0.85, layer="front"),
                  lean=0.18, hunch=0.3, neck=0.15),
    "sit_floor": P(plant=0.0, hip_h=0.11, lean=-0.22, chest=0.14, neck=0.2, tilt=0.12, hunch=0.3,
                   **IK("l", 0.17, 0.02, -0.06, "flat", layer="back"), **IK("r", 0.17, 0.02, -0.06, "flat",
                                                                            layer="back"),
                   **L("l", 1.32, 0.42, 0.28, 0.25), **L("r", 1.3, 0.38, 0.36, 0.2), sway=0.0),
    "heap": P(plant=0.0, hip_h=0.12, rot=0.5, lean=0.75, chest=0.3, neck=-0.2, tilt=-0.5, side=0.15,
              **A("l", 1.1, 0.7, 1.6, -0.6, h="relaxed"), **A("r", 0.5, -0.3, 1.2, -0.5, h="open"),
              **L("l", 1.4, 0.3, 2.0, 0.4), **L("r", 0.6, -0.2, 1.4, 0.2), sway=0.0, breath=0.5),
    "lie_back": P(plant=0.0, hip_h=0.3, rot=-math.pi / 2, **A("l", 0.0, 0.38, 0.25, h="open"),
                  **A("r", 0.0, 0.42, 0.35, h="relaxed"), **L("l", 0.0, 0.12, 0.1, 0.0),
                  **L("r", 0.18, 0.06, 0.5, 0.0), sway=0.0, breath=0.6),
    "sit_up": P(plant=0.0, hip_h=0.11, lean=-0.5, chest=0.25, neck=0.42, tilt=0.18, hunch=0.5,
                **IK("r", 0.15, 0.02, -0.2, "flat", layer="back", bend=-1.0),
                **A("l", 0.6, 0.2, 0.8, -0.2, h="relaxed"),
                **L("l", 1.42, 0.12, 0.1, 0.3), **L("r", 1.25, 0.2, 0.7, 0.2), sway=0.0),
    "crouch": P(L("l", 1.25, 0.28, 2.2, 0.2), L("r", 1.0, 0.22, 2.25, 0.25), lean=0.7, chest=0.1,
                neck=-0.25, nod=-0.18, hunch=0.3,
                **IK("r", 0.1, 0.1, 0.34, "open", wa=0.3, wabs=0.7), **A("l", 0.9, 0.2, 0.6, -0.5)),
    "cover_sweater": P(IK("l", 0.04, "desk", 0.3, "flat", wa=0.15, wabs=0.95, layer="front"),
                       IK("r", 0.04, "desk", 0.32, "flat", wa=0.15, wabs=0.95, layer="front"),
                       lean=0.78, chest=0.12, hunch=0.5, neck=-0.1, nod=-0.25,
                       **L("l", -0.15, k=0.18), **L("r", 0.1, k=0.1)),
    "back_away": P(IK("l", 0.14, 0.62, 0.12, "open", tf=-1.0, wa=-1.3, wabs=0.85),
                   IK("r", 0.14, 0.62, 0.12, "open", tf=-1.0, wa=-1.3, wabs=0.85),
                   lean=-0.2, chest=-0.05, hunch=0.65, nod=0.08, **L("l", 0.25, k=0.18),
                   **L("r", -0.22, k=0.06)),
    "arm_jerk": P(A("r", 0.55, 1.42, 0.0, 0.0, 0.25, h="splay"), A("l", 0.05, 0.08, 0.3),
                  side=-0.1, tilt=0.14, hunch=0.5, twist=0.1),
    "hands_up_small": P(A("l", 0.15, 0.5, 2.55, -0.4, 0.0, h="open", tf=-1.0),
                        A("r", 0.15, 0.5, 2.55, -0.4, 0.0, h="open", tf=-1.0), hunch=0.7, lean=-0.05),
    "catch": P(A("l", 1.32, 0.22, 0.15, 0.0, -0.1, h="claw"), A("r", 1.32, 0.22, 0.15, 0.0, -0.1, h="claw"),
               lean=0.3, chest=0.1, **L("l", 0.62, 0.1, 0.65, 0.2), **L("r", -0.38, 0.06, 0.15)),
    "cradle": P(IK("r", -0.02, 0.52, 0.16, "cup", layer="mid", tf=-1.0, wa=0.0, wabs=0.5),
                IK("l", 0.02, 0.63, 0.18, "relaxed", layer="front", wa=0.6, wabs=0.5),
                hold=2.0, lean=-0.04, hunch=0.3, nod=0.15, tilt=0.06),
    "carry_front": P(IK("l", 0.13, 0.5, 0.18, "grip", wa=1.1, wabs=0.8),
                     IK("r", 0.13, 0.5, 0.18, "grip", wa=1.1, wabs=0.8),
                     hold=2.0, lean=-0.07, hunch=0.2),
    "hold_side": P(A("r", 0.02, 0.12, 0.05, h="grip", tf=1.0), hold=1.0, side=-0.04),
    "present": P(A("r", 0.38, 0.12, 1.12, 0.0, -0.15, h="cup", tf=-1.0), hold=1.0, hold_order=1.0,
                 lean=0.06),
    "slide": P(IK("r", 0.06, "desk", 0.5, "flat", wa=0.05, wabs=1.0, layer="front"),
               IK("l", 0.14, "desk", 0.24, "relaxed", wa=0.3, wabs=0.9, layer="front"), lean=0.5,
               chest=0.1, neck=-0.15, nod=-0.1, **L("l", -0.1, k=0.1)),
    "leap_scared": P(A("l", 0.5, 1.5, 0.75, 0.6, 0.0, h="splay"), A("r", 0.5, 1.5, 0.75, 0.6, 0.0, h="splay"),
                     L("l", 0.45, 0.55, 0.85, -0.3), L("r", 0.25, 0.5, 0.6, -0.3), lift=170.0,
                     lean=-0.1, hunch=0.8, sway=0.0),
    "climb": P(plant=0.0, hip_h=-0.42, lean=0.42, chest=0.15, neck=-0.1, nod=-0.1, hunch=0.6,
               **IK("l", 0.13, 0.0, 0.16, "flat", wa=0.1, wabs=0.9, layer="front"),
               **IK("r", 0.13, 0.0, 0.16, "flat", wa=0.1, wabs=0.9, layer="front"),
               **L("l", -0.1, 0.06, 0.4, -0.5), **L("r", 0.2, 0.08, 0.6, -0.5), sway=0.0, posture=0.3),
    "pick_up": P(L("l", 1.1, 0.25, 1.9, 0.2), L("r", 0.8, 0.18, 2.0, 0.3), lean=0.95, chest=0.15,
                 neck=-0.45, nod=-0.2, **IK("r", 0.06, 0.02, 0.3, "grip", wa=1.3, wabs=0.7),
                 **A("l", 0.7, 0.3, 0.6, -0.3)),
    "throw": P(A("r", -1.7, 1.0, -1.6, 0.0, -0.4, h="grip", layer="back"),
               A("l", 1.1, 0.3, 0.2, h="open"), twist=-0.35, lean=-0.12, side=0.1, hold=1.0,
               **L("l", 0.45, 0.1, 0.2), **L("r", -0.2, 0.1, 0.25)),
    "headphones_on": P(IK("l", 0, 0, cup=1.0, h="grip", wa=-1.4, wabs=0.6, layer="front"),
                       IK("r", 0, 0, cup=1.0, h="grip", wa=-1.4, wabs=0.6, layer="front"), hunch=0.4),
    "yawn": P(HK("r", -8, 62, "relaxed", layer="front", wa=-2.2, wabs=0.7), A("l", 0.0, 0.1, 0.2),
              lean=-0.1, chest=-0.12, nod=-0.18, neck=-0.1),
    "fall": P(A("l", W(0.4, 0.3, 0.0), W(2.1, 0.35, 0.1, a2=0.1), W(0.8, 0.4, 0.3), 0.2, h="splay"),
              A("r", W(0.4, 0.3, 0.5), W(2.1, 0.35, 0.6, a2=0.1), W(0.8, 0.4, 0.8), 0.2, h="splay"),
              L("l", W(0.8, 0.3, 0.2), 0.35, W(1.0, 0.4, 0.4), -0.3),
              L("r", W(0.6, 0.3, 0.7), 0.3, W(0.9, 0.4, 0.9), -0.3), lean=-0.25, nod=-0.2, sway=0.0,
              period=0.5),
    "flip": P(A("l", 1.0, 0.25, 1.4, -0.4, h="grip"), A("r", 1.0, 0.25, 1.4, -0.4, h="grip"),
              L("l", 2.1, 0.12, 2.5, 0.2), L("r", 2.1, 0.12, 2.5, 0.2), lean=0.6, chest=0.3, nod=0.35,
              neck=0.3, hunch=0.6, sway=0.0),
}
