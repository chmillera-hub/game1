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
               lean=0.1, hunch=0.5, nod=-0.08, neck=0.1, **L("l", k=0.12), **L("r", k=0.12)),
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
                     lean=0.32, neck=0.12, nod=-0.08, **L("l", k=0.06), **L("r", k=0.06)),
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

# ---------------------------------------------------------------------------
# Animated cycles: name -> (period seconds, base pose, wave table)
# ---------------------------------------------------------------------------
_WALK_LEGS = P(L("l", W(0.0, 0.42, 0.0), 0.04, W(0.06, 0.78, 0.22, r=1), W(0.02, 0.26, 0.02)),
               L("r", W(0.0, 0.42, 0.5), 0.04, W(0.06, 0.78, 0.72, r=1), W(0.02, 0.26, 0.52)))
_RUN_LEGS = P(L("l", W(0.18, 0.78, 0.0), 0.05, W(0.4, 1.3, 0.16, r=1), W(-0.05, 0.35, 0.0)),
              L("r", W(0.18, 0.78, 0.5), 0.05, W(0.4, 1.3, 0.66, r=1), W(-0.05, 0.35, 0.5)))
CYCLES = {
    # ------------------------------------------------------------ locomotion
    "walk": (1.0, "stand", P(_WALK_LEGS,
                             A("l", W(0.02, 0.36, 0.5), 0.1, W(0.3, 0.14, 0.5)),
                             A("r", W(0.02, 0.36, 0.0), 0.1, W(0.3, 0.14, 0.0)),
                             twist=W(0.0, 0.07, 0.5), hip_roll=W(0.0, 0.0, 0.0, 0.035, 0.0),
                             lean=0.05, nod=W(0.0, 0.0, 0.0, 0.025, 0.1), sway=0.0, coat_trail=0.2)),
    "run": (0.56, "stand", P(_RUN_LEGS,
                             A("l", W(0.15, 0.85, 0.5), 0.15, W(1.45, 0.2, 0.5), h="fist"),
                             A("r", W(0.15, 0.85, 0.0), 0.15, W(1.45, 0.2, 0.0), h="fist"),
                             twist=W(0.0, 0.14, 0.5), lean=0.26, neck=0.1, lift=W(10, 0, 0, 12, 0.0),
                             nod=W(0.0, 0.0, 0.0, 0.04, 0.2), sway=0.0, coat_trail=0.85)),
    "run_panic": (0.44, "stand", P(_RUN_LEGS,
                                   A("l", W(0.7, 1.0, 0.3), W(1.05, 0.5, 0.05), W(0.9, 0.6, 0.7), h="splay"),
                                   A("r", W(0.7, 1.0, 0.8), W(1.05, 0.5, 0.55), W(0.9, 0.6, 0.2), h="splay"),
                                   lean=0.14, nod=-0.12, hunch=0.5, lift=W(10, 0, 0, 12, 0.0),
                                   tilt=W(0.0, 0.08, 0.1), sway=0.0, coat_trail=1.0)),
    "scream_run": (0.46, "stand", P(_RUN_LEGS,
                                    A("l", W(0.2, 0.2, 0.0), W(2.25, 0.3, 0.0, 0.12, 0.1), W(0.75, 0.4, 0.3),
                                      h="splay"),
                                    A("r", W(0.2, 0.2, 0.5), W(2.25, 0.3, 0.5, 0.12, 0.6), W(0.75, 0.4, 0.8),
                                      h="splay"),
                                    lean=0.02, nod=-0.18, lift=W(10, 0, 0, 12, 0.0), tilt=W(0, 0.06, 0.2),
                                    sway=0.0, coat_trail=1.0)),
    "tiptoe": (1.4, "stand", P(L("l", W(0.42, 0.62, 0.0), 0.08, W(0.45, 1.25, 0.17, r=1), -0.55),
                               L("r", W(0.42, 0.62, 0.5), 0.08, W(0.45, 1.25, 0.67, r=1), -0.55),
                               A("l", W(1.05, 0.2, 0.5), 0.4, 1.75, -0.45, 1.05, h="relaxed"),
                               A("r", W(1.05, 0.2, 0.0), 0.4, 1.75, -0.45, 1.05, h="relaxed"),
                               lean=0.24, hunch=0.7, neck=0.32, nod=-0.06, lift=W(4, 0, 0, 7, 0.1),
                               twist=W(0, 0.06, 0.5), sway=0.0)),
    "crawl": (1.2, "stand", P(L("l", W(0.05, 0.3, 0.0), 0.08, W(1.55, 0.22, 0.25), -0.6),
                              L("r", W(0.05, 0.3, 0.5), 0.08, W(1.55, 0.22, 0.75), -0.6),
                              A("l", W(0.02, 0.3, 0.5), 0.12, W(0.12, 0.25, 0.75, r=1), h="flat",
                                wa=0.1, wabs=0.5),
                              A("r", W(0.02, 0.3, 0.0), 0.12, W(0.12, 0.25, 0.25, r=1), h="flat",
                                wa=0.1, wabs=0.5),
                              lean=1.3, chest=0.12, neck=-0.85, nod=-0.25, plant_hands=1.0, sway=0.0,
                              twist=W(0, 0.05, 0.0), posture=0.0)),
    "stumble": (1.6, "stand", P(L("l", W(0.0, 0.3, 0.0, 0.08), 0.1, W(0.15, 0.5, 0.22, r=1), 0.05),
                                L("r", W(0.0, 0.26, 0.5, 0.08), 0.1, W(0.15, 0.5, 0.72, r=1), 0.05),
                                A("l", W(0.0, 0.2, 0.5), W(0.18, 0.06, 0.2), 0.15, h="relaxed"),
                                A("r", W(0.0, 0.2, 0.0), W(0.18, 0.06, 0.7), 0.15, h="relaxed"),
                                side=W(0, 0.08, 0.0), rot=W(0, 0.045, 0.1), lean=0.14, hunch=0.7,
                                nod=W(0.1, 0.06, 0.2), tilt=W(0.0, 0.12, 0.3), sway=0.0)),
    # ------------------------------------------------------------ gestures
    "bang_door": (0.5, "stand", P(A("r", W(1.55, 0.1, 0.0), 0.15, W(0.55, 0.5, 0.0), 0.0, -0.2, h="fist"),
                                  A("l", 1.3, 0.25, 0.7, -0.2, -0.6, h="flat"),
                                  lean=W(0.12, 0.05, 0.0), hunch=0.4, nod=W(0.0, 0.04, 0.05),
                                  **L("l", 0.15, k=0.1), **L("r", -0.12, k=0.05))),
    "wring_hands": (0.8, "stand", P(IK("l", W(0.0, 0.015, 0.0), W(0.53, 0.012, 0.25), 0.14, "relaxed",
                                       w=1.0, wa=-1.2, wabs=0.5),
                                    IK("r", W(0.0, 0.015, 0.5), W(0.53, 0.012, 0.75), 0.14, "relaxed",
                                       w=1.0, wa=-1.2, wabs=0.5),
                                    {"al_w": W(0, 0.5, 0.0), "ar_w": W(0, 0.5, 0.5)},
                                    hunch=0.85, nod=0.06, tilt=W(0, 0.04, 0.0))),
    "shake_arms": (0.25, "stand", P(A("l", 0.75, W(0.62, 0.18, 0.25), W(0.75, 0.35, 0.0), 0.2, h="splay"),
                                    A("r", 0.75, W(0.62, 0.18, 0.75), W(0.75, 0.35, 0.5), 0.2, h="splay"),
                                    hunch=0.8, tilt=W(0, 0.035, 0.0), nod=W(0, 0.02, 0.3), sway=0.0)),
    "tap_foot": (0.5, "arms_crossed", P(L("r", 0.18, 0.12, 0.06, W(0.22, 0.22, 0.0, r=1)),
                                        nod=W(0, 0.012, 0.0))),
    "roll_hand": (0.7, "stand", P(IK("r", W(0.17, 0.03, 0.0), W(0.56, 0.03, 0.25), 0.18, "open", tf=-1.0,
                                     wa=W(-0.4, 0.8, 0.1), wabs=0.8),
                                  A("l", 0.05, 0.1, 0.2), tilt=0.06)),
    "tug": (1.2, "stand", P(IK("l", 0.05, 0.47, W(0.36, 0.03, 0.0), "grip", wa=0.0, wabs=0.6),
                            IK("r", 0.05, 0.5, W(0.36, 0.03, 0.0), "grip", wa=0.0, wabs=0.6),
                            L("l", 0.55, 0.06, 0.12, 0.25), L("r", -0.1, 0.08, 0.62, 0.0),
                            lean=W(-0.36, 0.08, 0.0), dx=W(0, 10, 0.0), hunch=0.4, nod=0.1,
                            tilt=W(0, 0.05, 0.25), hold=2.0, sway=0.0)),
    "struggle_hold": (0.9, "stand", P(IK("l", W(0.0, 0.02, 0.0), W(0.52, 0.03, 0.25), 0.17, "claw",
                                         layer="front", wa=0.4, wabs=0.5),
                                      IK("r", W(0.0, 0.02, 0.5), W(0.58, 0.03, 0.75), 0.17, "claw",
                                         layer="mid", wa=-0.4, wabs=0.5),
                                      L("l", 0.12, 0.16, 0.25), L("r", -0.08, 0.16, 0.3),
                                      side=W(0, 0.08, 0.0), twist=W(0, 0.15, 0.25), lean=W(0.05, 0.06, 0.5),
                                      dx=W(0, 7, 0.0), tilt=W(0, 0.08, 0.1), hold=2.0, sway=0.0)),
    "game": (0.3, "sit_game", P({"al_thumb": W(0, 0.3, 0.0), "ar_thumb": W(0, 0.3, 0.37)},
                                nod=W(-0.16, 0.012, 0.0), lean=W(0.3, 0.01, 0.2))),
    "type": (0.35, "sit_desk", P({"al_fing": 1.0, "ar_fing": 1.0, "al_h": "claw", "ar_h": "claw"},
                                 nod=W(0.05, 0.01, 0.0))),
}

# Per-character pose tweaks: (who, pose) -> overrides merged on top.
POSE_WHO = {
    ("tired", "hands_pockets"): P(A("l", 0.32, 0.2, 0.95, -1.05, hide=1.0),
                                  A("r", 0.32, 0.2, 0.95, -1.05, hide=1.0), hunch=0.6),
    ("boss", "stand"): P(_HANDS_BACK),
    ("guard", "stand"): P(A("l", 0.05, 0.16, 0.25), A("r", 0.05, 0.16, 0.25)),
}

# Static poses that are secretly animated (waves) use this period (s).
STATIC_PERIOD = 0.5

# Poses whose hands hold a prop: "hold" 1 = right hand, 2 = both hands (the
# callback gets side "both" and the midpoint between the hands).


# ============================================================================
# 6. SOLVER
# ============================================================================
_HAND_KEYS = ("al_h", "ar_h")
_STR_KEYS = ("al_layer", "ar_layer")


def _eval(v, phase):
    if isinstance(v, tuple) and v and v[0] == "~":
        return _wave(phase, *v[1:])
    return v


def _overlay(d, table, phase):
    for k, v in table.items():
        if k in ("base", "period"):
            continue
        d[k] = _eval(v, phase)


def _pose_raw(spec, who, pt):
    """Resolve one pose spec (name / dict) into a flat dict (hand names kept)."""
    if isinstance(spec, dict):
        d = _pose_raw(spec.get("base", "stand"), who, pt)
        _overlay(d, spec, (pt / spec.get("period", STATIC_PERIOD)) % 1.0)
        return d
    name = spec
    if name in CYCLES:
        period, base, table = CYCLES[name]
        d = _pose_raw(base, who, pt)
        _overlay(d, table, (pt / period) % 1.0)
        d["_cycle"] = period
    else:
        if name not in POSES:
            raise KeyError(f"human: unknown pose {name!r}")
        d = dict(POSE_DEFAULTS)
        if name != "stand" and ("boss", "stand") in POSE_WHO and who == "boss":
            pass
        tab = POSES[name]
        _overlay(d, tab, (pt / tab.get("period", STATIC_PERIOD)) % 1.0)
    tw = POSE_WHO.get((who, name))
    if tw:
        _overlay(d, tw, 0.0)
    return d


def _numeric(d, C, who):
    """Hand names -> vectors, named heights -> numbers."""
    out = dict(d)
    for k in _HAND_KEYS:
        v = out[k]
        out[k] = list(_HAND_VEC[v]) if isinstance(v, str) else list(v)
    H = C["height"]
    leglen = C["thigh"] + C["shin"] + C["foot_h"]
    for k in ("hip_h", "al_ty", "ar_ty"):
        v = out[k]
        if isinstance(v, str):
            base, _, add = v.partition("+")
            if base == "seat":
                val = SEAT_H[who] + C["leg_r"][0] * 0.75
            elif base == "desk":
                val = DESK_H[who]
            elif base == "sill":
                val = SILL_H[who]
            else:
                val = 0.0
            if k == "hip_h":
                out[k] = val / leglen + (float(add) if add else 0.0)
            else:
                out[k] = val / H + (float(add) if add else 0.0)
    return out


def resolve_pose(pose, who, pt):
    """pose (name | dict | (a, b, k)) -> numeric joint dict."""
    C = CHARS[who]
    if isinstance(pose, (tuple, list)) and len(pose) == 3 and not isinstance(pose[0], (int, float)):
        a = resolve_pose(pose[0], who, pt)
        b = resolve_pose(pose[1], who, pt)
        k = clamp(float(pose[2]))
        out = {}
        for key, va in a.items():
            vb = b.get(key, va)
            if isinstance(va, list):
                out[key] = [x + (y - x) * k for x, y in zip(va, vb)]
            elif isinstance(va, str) or isinstance(vb, str):
                out[key] = vb if k >= 0.5 else va
            else:
                out[key] = va + (vb - va) * k
        for key, vb in b.items():
            if key not in out:
                out[key] = vb
        return out
    return _numeric(_pose_raw(pose, who, pt), C, who)


def _up(p, r):
    return (math.sin(r), -math.cos(r) * math.cos(p), math.cos(r) * math.sin(p))


def _dir(p, o, sgn):
    co = math.cos(o)
    return (sgn * math.sin(o), co * math.cos(p), co * math.sin(p))


def _add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


class _Proj:
    """Yaw projection + whole-body screen roll + translation (rig-local 2D)."""
    __slots__ = ("c", "s", "rc", "rs", "tx", "ty")

    def __init__(self, yaw, rot, tx=0.0, ty=0.0):
        self.c, self.s = math.cos(yaw), math.sin(yaw)
        self.rc, self.rs = math.cos(rot), math.sin(rot)
        self.tx, self.ty = tx, ty

    def __call__(self, p):
        X = p[0] * self.c + p[2] * self.s
        Z = -p[0] * self.s + p[2] * self.c
        Y = p[1]
        return (X * self.rc - Y * self.rs + self.tx, X * self.rs + Y * self.rc + self.ty, Z)


def _ik2(S, T, L1, L2, pref, bend):
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = math.hypot(dx, dy)
    d = clamp(d, abs(L1 - L2) + 1.0, L1 + L2 - 0.5)
    ux, uy = _norm(dx, dy)
    ca = clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1.0, 1.0)
    a = math.acos(ca)
    best = None
    for sgn in (1, -1):
        ex, ey = _rot(ux, uy, sgn * a)
        E = (S[0] + ex * L1, S[1] + ey * L1)
        sc = (ex * pref[0] + ey * pref[1]) * bend
        if best is None or sc > best[0]:
            best = (sc, E)
    E = best[1]
    W = (S[0] + ux * d, S[1] + uy * d)
    return E, W


def _ang_lerp(a, b, k):
    d = (b - a + math.pi) % TAU - math.pi
    return a + d * k


def _solve(C, Q, who, turn, t, fx, headphones, lag_Q=None):
    """Skeleton in rig-local 2D (ground origin, y down). Returns dict J."""
    H = C["height"]
    sp = C["spine"]
    leglen = C["thigh"] + C["shin"] + C["foot_h"]
    tq = clamp(turn + Q["turn"], -1.6, 1.6)
    phi = tq * TURN_RAD
    tw = Q["twist"]
    rot = Q["rot"]
    seed = C["seed"]
    br = Q["breath"] * math.sin(TAU * t / 3.7 + seed)
    lean, chest, side, hunch = Q["lean"], Q["chest"], Q["side"], Q["hunch"]

    # ---- spine (body frame, pelvis at origin)
    P0 = (0.0, 0.0, 0.0)
    hem = _add(P0, _up(lean * 0.3, side * 0.3), sp["hem"])
    wst = _add(P0, _up(lean * 0.5, side * 0.5), sp["waist"])
    chs = _add(wst, _up(lean, side), sp["chest"] - sp["waist"])
    shl = _add(chs, _up(lean + chest * 0.6, side), sp["shoulder"] - sp["chest"])
    shl = (shl[0], shl[1] - br * 1.6 - hunch * 8, shl[2] + hunch * 6)
    nck = _add(shl, _up(lean + chest + Q["neck"] * 0.3, side), sp["neck"] - sp["shoulder"] + hunch * 4)
    hpv = _add(nck, _up(lean + chest + Q["neck"], side * 1.2), C["neck_len"] - hunch * 10)
    hpv = (hpv[0], hpv[1], hpv[2] + hunch * 10)

    pr = _Proj(phi, rot)
    pr_w = _Proj(phi + tw * 0.3, rot)
    pr_c = _Proj(phi + tw * 0.65, rot)
    pr_s = _Proj(phi + tw, rot)

    J = {"phi": phi, "turn": tq, "rot": rot}
    # ---- legs
    lowest = -1e9
    legs = {}
    for s_, sgn in (("l", -1), ("r", 1)):
        hip = (sgn * C["hip_w"] * math.cos(Q["hip_roll"]), sgn * C["hip_w"] * math.sin(Q["hip_roll"]) * -1, 0.0)
        p, o, k = Q[f"l{s_}_p"], Q[f"l{s_}_o"], Q[f"l{s_}_k"]
        kn = _add(hip, _dir(p, o, sgn), C["thigh"])
        q = p - k
        an = _add(kn, _dir(q, o + Q[f"l{s_}_ko"], sgn), C["shin"])
        fp = q + Q[f"l{s_}_a"]
        fdir = (sgn * 0.1, -math.sin(fp), math.cos(fp))
        dn = (0.0, math.cos(fp), math.sin(fp))
        sole = _add(an, dn, C["foot_h"])
        toe = _add(sole, fdir, C["foot_len"] * 0.72)
        heel = _add(sole, fdir, -C["foot_len"] * 0.28)
        g = dict(hip=pr(hip), knee=pr(kn), ankle=pr(an), sole=pr(sole), toe=pr(toe), heel=pr(heel),
                 fp=fp)
        legs[s_] = g
        lowest = max(lowest, g["sole"][1], g["toe"][1], g["heel"][1], g["knee"][1] + C["leg_r"][1])
    # ---- torso nodes
    nodes = dict(hem=pr(hem), pel=pr(P0), wst=pr_w(wst), chs=pr_c(chs), shl=pr_s(shl), nck=pr_s(nck),
                 hpv=pr_s(hpv))
    sw = C["sw"] * (1 - 0.05 * hunch)
    shj = {}
    for s_, sgn in (("l", -1), ("r", 1)):
        off = _rot(sgn * sw, 0.0, side)
        shj[s_] = pr_s((shl[0] + off[0], shl[1] + off[1] + hunch * 4, shl[2] - hunch * 4))
    # ---- arms (FK)
    arms = {}
    for s_, sgn in (("l", -1), ("r", 1)):
        off = _rot(sgn * sw, 0.0, side)
        S3 = (shl[0] + off[0], shl[1] + off[1] + hunch * 4, shl[2] - hunch * 4)
        p, o, e, eo = Q[f"a{s_}_p"], Q[f"a{s_}_o"], Q[f"a{s_}_e"], Q[f"a{s_}_eo"]
        E3 = _add(S3, _dir(p, o, sgn), C["arm"][0])
        W3 = _add(E3, _dir(p + e, o + eo, sgn), C["arm"][1])
        T3 = _add(W3, _dir(p + e + Q[f"a{s_}_w"], o + eo, sgn), 30.0)
        arms[s_] = dict(S=pr_s(S3), E=pr_s(E3), W=pr_s(W3), T=pr_s(T3))
        if Q["plant_hands"] > 0:
            lowest = max(lowest, arms[s_]["W"][1] + C["hand"] * 0.35)

    # ---- ground lock
    lock_dy = -lowest
    pel_dy = -Q["hip_h"] * leglen
    gy = lerp(pel_dy, lock_dy, Q["plant"]) - Q["lift"] + Q["dy"]
    gx = Q["dx"] + Q["sway"] * 2.5 * noise1(t * 0.33, seed)

    def mv(p):
        return (p[0] + gx, p[1] + gy, p[2])

    for g in legs.values():
        for k in ("hip", "knee", "ankle", "sole", "toe", "heel"):
            g[k] = mv(g[k])
    for k in list(nodes):
        nodes[k] = mv(nodes[k])
    for s_ in "lr":
        shj[s_] = mv(shj[s_])
        for k in ("S", "E", "W", "T"):
            arms[s_][k] = mv(arms[s_][k])
    J["legs"], J["nodes"], J["shj"], J["arms"] = legs, nodes, shj, arms
    J["pel_y"] = gy

    # ---- head transform (needed for head-relative IK targets)
    fdir = 1.0 if tq >= -0.001 else -1.0
    J["fdir"] = fdir
    hd = C["head"]
    psi = clamp(tq + tw / TURN_RAD + Q["head_yaw"] + fx["head_turn"], -1.6, 1.6) * HEAD_TURN_RAD
    tilt = (Q["tilt"] + fx["head_tilt"] + rot + side * 0.5
            + (lean + chest + Q["neck"]) * math.sin(phi) * 0.35
            + Q["sway"] * 0.022 * noise1(t * 0.27, seed + 3))
    nod = Q["nod"] + fx["head_nod"] + (lean + chest + Q["neck"]) * 0.1
    piv = nodes["hpv"]
    up_off = hd["chin"] * hd["pivot"]
    hcx, hcy = _rot(0.0, -up_off, tilt)
    J["head"] = dict(pivot=(piv[0], piv[1]), cx=piv[0] + hcx, cy=piv[1] + hcy, tilt=tilt, psi=psi,
                     nod=nod, z=piv[2])

    # ---- arm IK (2D) + hand angles + layering
    cphi, sphi = math.cos(phi), math.sin(phi)
    order = ("l", "r") if Q["ar_grab"] >= Q["al_grab"] else ("r", "l")
    for s_ in order:
        sgn = -1 if s_ == "l" else 1
        a = arms[s_]
        S, E, Wr, T = a["S"], a["E"], a["W"], a["T"]
        fk_ang = math.atan2(T[1] - Wr[1], T[0] - Wr[0]) if math.hypot(T[0] - Wr[0], T[1] - Wr[1]) > 4 \
            else math.pi / 2
        ik = Q[f"a{s_}_ik"]
        z_e, z_w = E[2], Wr[2]
        Ef, Wf, ang = (E[0], E[1]), (Wr[0], Wr[1]), fk_ang
        if ik > 0.001:
            # ground-frame target
            x3, z3 = sgn * Q[f"a{s_}_tx"] * H, Q[f"a{s_}_tz"] * H
            tgt = (nodes["pel"][0] + x3 * cphi + z3 * sphi, -Q[f"a{s_}_ty"] * H)
            tz_ = -x3 * sphi + z3 * cphi
            th = Q[f"a{s_}_th"]
            if th > 0:
                hh = J["head"]
                ox = sgn * Q[f"a{s_}_hx"] * math.cos(psi) + hd["levels"][4][2] * math.sin(psi) * 0.6
                oy = Q[f"a{s_}_hy"]
                rx, ry = _rot(ox, oy, hh["tilt"])
                tgt = _lerp2(tgt, (hh["cx"] + rx, hh["cy"] + ry), th)
                tz_ = lerp(tz_, hh["z"] + 60, th)
            if Q[f"a{s_}_cup"] > 0:
                cups = _cup_positions(C, J, headphones)
                tgt = _lerp2(tgt, cups[s_], Q[f"a{s_}_cup"])
                tz_ = lerp(tz_, J["head"]["z"] + 40, Q[f"a{s_}_cup"])
            if Q[f"a{s_}_grab"] > 0:
                o_ = arms["r" if s_ == "l" else "l"]
                m = _lerp2(o_["E2"], o_["W2"], 0.62)
                tgt = _lerp2(tgt, m, Q[f"a{s_}_grab"])
                tz_ = lerp(tz_, max(o_["E"][2], o_["W"][2]) + 20, Q[f"a{s_}_grab"])
            hand_back = C["hand"] * 0.42
            pref = (0.55 * sgn * cphi - 0.6 * sphi, 0.65)
            Ei, Wi = _ik2((S[0], S[1]), tgt, C["arm"][0], C["arm"][1] + hand_back * 0.0, pref,
                          Q[f"a{s_}_bend"])
            ik_ang = math.atan2(Wi[1] - Ei[1], Wi[0] - Ei[0]) + Q[f"a{s_}_w"] * 1.0
            Ef = _lerp2(Ef, Ei, ik)
            Wf = _lerp2(Wf, Wi, ik)
            ang = _ang_lerp(ang, ik_ang, ik)
            z_e = lerp(z_e, tz_ * 0.6, ik)
            z_w = lerp(z_w, tz_, ik)
        wabs = Q[f"a{s_}_wabs"]
        if wabs > 0:
            wa = Q[f"a{s_}_wa"]
            abs_ang = wa if fdir > 0 else math.pi - wa
            ang = _ang_lerp(ang, abs_ang, wabs)
        a["E2"], a["W2"], a["ang"], a["zE"], a["zW"] = Ef, Wf, ang, z_e, z_w
    J["Q"] = Q
    J["lag"] = lag_Q
    return J


def _cup_positions(C, J, hp):
    """Screen positions of the headphone cups for state hp (0 neck .. 1 on)."""
    hh = J["head"]
    hd = C["head"]
    a = hd["levels"][4][1]
    k = smoothstep(hp)
    psi = hh["psi"]
    out = {}
    nk = J["nodes"]["nck"]
    for s_, sgn in (("l", -1), ("r", 1)):
        ex, ey = _rot(sgn * (a + 6) * math.cos(psi) - math.sin(psi) * 10, (hd["ear_y"][0] + hd["ear_y"][1]) / 2,
                      hh["tilt"])
        on = (hh["cx"] + ex, hh["cy"] + ey)
        neck = (nk[0] + sgn * (C["neck_r"] + 34) * math.cos(J["phi"]), nk[1] + 6)
        mid = _lerp2(neck, on, k)
        # arc outward while lifting
        bulge = math.sin(k * math.pi) * 34
        out[s_] = (mid[0] + sgn * bulge, mid[1])
    return out


# ============================================================================
# 7a. DRAWING: hands, feet, legs, arms
# ============================================================================
_FBASE = ((0.95, 0.33, 0.27), (1.0, 0.11, 0.28), (0.97, -0.11, 0.265), (0.9, -0.31, 0.235))
_PALM = ((0.0, -0.29), (0.42, -0.42), (0.86, -0.43), (1.0, -0.24), (1.02, 0.12), (0.92, 0.42),
         (0.45, 0.44), (0.02, 0.3))


def _draw_hand(ctx, skin, ink, W, ang, hv, ysign, hs, inkw, phase=0.0, fing=0.0, thumb=0.0,
               palm_view=False):
    """Draw one cartoon hand. W = wrist (2D), ang = pointing angle. Returns hold point."""
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = -sa * ysign, ca * ysign            # +y (thumb side) in screen

    def M(x, y):
        return (W[0] + (ca * x + px * y) * hs, W[1] + (sa * x + py * y) * hs)

    palm = hv[0]
    cup = hv[1]
    # palm shape
    pts = [M(x * palm, y * (1 - 0.12 * cup)) for x, y in _PALM]
    ink_w2 = inkw * 2
    _set(ctx, ink)
    _smooth(ctx, pts, True, 0.6)
    ctx.set_line_width(ink_w2)
    ctx.stroke_preserve()
    _set(ctx, skin)
    ctx.fill()
    # fingers: pinky -> index (each overlaps the previous => separation lines)
    for i in (3, 2, 1, 0):
        sp, ln, b1, b2 = hv[4 + i * 4: 8 + i * 4]
        if fing:
            w = math.sin(TAU * (phase * 2.0 + i * 0.27))
            b1 += fing * 0.32 * max(0.0, w)
            b2 += fing * 0.2 * max(0.0, w)
        bx, by, fw = _FBASE[i]
        bx *= palm
        a1 = sp
        j1 = (bx + math.cos(a1) * ln * 0.55, by + math.sin(a1) * ln * 0.55)
        a2 = a1 + b1
        j2 = (j1[0] + math.cos(a2) * ln * 0.3, j1[1] + math.sin(a2) * ln * 0.3)
        a3 = a2 + b2
        tip = (j2[0] + math.cos(a3) * ln * 0.2, j2[1] + math.sin(a3) * ln * 0.2)
        seq = [M(bx - 0.12, by * 0.95), M(*j1), M(*j2), M(*tip)]
        ctx.move_to(*seq[0])
        for q in seq[1:]:
            ctx.line_to(*q)
        _set(ctx, ink)
        ctx.set_line_width(fw * hs + ink_w2)
        ctx.stroke_preserve()
        _set(ctx, skin)
        ctx.set_line_width(fw * hs)
        ctx.stroke()
    # palm patch hides finger roots inside the palm
    pts2 = [M(0.1 + x * palm * 0.78, y * 0.74 * (1 - 0.12 * cup)) for x, y in _PALM]
    _set(ctx, skin)
    _smooth(ctx, pts2, True, 0.6)
    ctx.fill()
    # palm creases when the palm faces camera
    if palm_view:
        ctx.move_to(*M(0.25 * palm, 0.28))
        _qcurve(ctx, M(0.25 * palm, 0.28), M(0.5 * palm, 0.02), M(0.82 * palm, -0.12))
        _set(ctx, alpha_ink(ink, 0.55))
        ctx.set_line_width(inkw * 0.55)
        ctx.stroke()
    # thumb on top
    ta, tl, tb = hv[20] + thumb, hv[21], hv[22]
    b0 = (0.2 * palm, 0.3)
    t1 = (b0[0] + math.cos(ta) * tl * 0.5, b0[1] + math.sin(ta) * tl * 0.5)
    tb_a = ta - tb if ta > 0.9 else ta + tb * 0.6
    if ta > 0.9:   # wrapped thumbs curl forward across the fingers
        tb_a = ta - tb
    t2 = (t1[0] + math.cos(tb_a) * tl * 0.5, t1[1] + math.sin(tb_a) * tl * 0.5)
    seq = [M(*b0), M(*t1), M(*t2)]
    ctx.move_to(*seq[0])
    ctx.line_to(*seq[1])
    ctx.line_to(*seq[2])
    _set(ctx, ink)
    ctx.set_line_width(0.3 * hs + ink_w2)
    ctx.stroke_preserve()
    _set(ctx, skin)
    ctx.set_line_width(0.3 * hs)
    ctx.stroke()
    return M(hv[2] * palm, hv[3])


def alpha_ink(c, a):
    c = hexc(c)
    return (c[0], c[1], c[2], c[3] * a)


def _draw_shoe(ctx, C, col, g, inkw):
    style = C["_shoe"]
    r = C["foot_r"]
    an, so, toe, heel = g["ankle"], g["sole"], g["toe"], g["heel"]
    ux, uy = _norm(an[0] - so[0], an[1] - so[1])
    hc = (heel[0] + ux * r * 0.95, heel[1] + uy * r * 0.95)
    tc = (toe[0] + ux * r * 0.8, toe[1] + uy * r * 0.8)
    ln = math.hypot(tc[0] - hc[0], tc[1] - hc[1])
    front = 1.0 - min(1.0, ln / (C["foot_len"] * 0.75))
    rt = r * (0.62 if style == "heel" else 0.9)
    ctx.new_path()
    _capsule(ctx, hc[0], hc[1], r, tc[0], tc[1], rt)
    if front > 0.05:
        ellipse(ctx, tc[0], tc[1] + r * 0.05, r * (1.0 + 0.32 * front), r * 0.92)
    if style == "slipper":
        for i in range(5):
            k = i / 4.0
            q = _lerp2(hc, tc, k)
            circle(ctx, q[0] - ux * r * 0.55 + uy * 0.0, q[1] - uy * r * 0.55, r * 0.5)
    if style == "boot":
        _capsule(ctx, an[0], an[1] - 4, r * 0.95, hc[0], hc[1], r)
    _set(ctx, PAL["ink"])
    ctx.set_line_width(inkw * 2)
    ctx.stroke_preserve()
    _set(ctx, col["shoe"])
    ctx.fill()
    # sole strip / details
    sole_c = {"sneaker": "#f2efe8", "flat": col["shoe_dk"], "slipper": _lt(col["shoe"], 0.35)}.get(
        style, col["shoe_dk"])
    a0 = (heel[0] + ux * 3, heel[1] + uy * 3)
    a1 = (toe[0] + ux * 3, toe[1] + uy * 3)
    ctx.move_to(*a0)
    ctx.line_to(*a1)
    _set(ctx, sole_c)
    ctx.set_line_width(r * (0.42 if style in ("boot", "sneaker") else 0.3))
    ctx.stroke()
    if style == "heel":
        # little heel block under the heel
        hb = (heel[0] + ux * 2, heel[1])
        ctx.move_to(hb[0] - 4, hb[1] - r * 0.6)
        ctx.line_to(hb[0] - 3, hb[1] + 2)
        ctx.line_to(hb[0] + 5, hb[1] + 2)
        ctx.line_to(hb[0] + 6, hb[1] - r * 0.6)
        _fs(ctx, col["shoe_dk"], inkw * 0.8)


def _leg_path(ctx, C, g, rr):
    _capsule(ctx, g["hip"][0], g["hip"][1], rr[0], g["knee"][0], g["knee"][1], rr[1])
    _capsule(ctx, g["knee"][0], g["knee"][1], rr[1], g["ankle"][0], g["ankle"][1] - 4, rr[2])


def _draw_leg(ctx, C, col, g, inkw, other=None):
    _draw_shoe(ctx, C, col, g, inkw)
    rr = C["leg_r"]
    ctx.new_path()
    _leg_path(ctx, C, g, rr)
    if other is not None:    # pelvis piece joins this (near) leg with the hips
        h0, h1 = g["hip"], other["hip"]
        _capsule(ctx, h0[0], h0[1] - 6, rr[0] * 1.05, h1[0], h1[1] - 6, rr[0] * 1.05)
    _set(ctx, PAL["ink"])
    ctx.set_line_width(inkw * 2)
    ctx.stroke_preserve()
    _set(ctx, col["pants"])
    ctx.fill()
    # cuff band at the ankle (sweatpants elastic / trousers hem)
    kn, an = g["knee"], g["ankle"]
    dx, dy = _norm(an[0] - kn[0], an[1] - kn[1])
    st = C["_pants"]
    if st in ("sweat",):
        c0 = (an[0] - dx * 18, an[1] - dy * 18 - 4)
        ctx.new_path()
        _capsule(ctx, c0[0], c0[1], rr[2] * 1.02, an[0] - dx * 2, an[1] - dy * 2 - 4, rr[2] * 0.95)
        _fs(ctx, col["pants_dk"], inkw * 0.8)
    # knee fold line on bent knees
    bend = abs(math.atan2(an[1] - kn[1], an[0] - kn[0]) - math.atan2(kn[1] - g["hip"][1], kn[0] - g["hip"][0]))
    bend = min(bend, TAU - bend)
    if bend > 0.35:
        nx, ny = -dy, dx
        ctx.move_to(kn[0] + nx * rr[1] * 0.2 - dx * 6, kn[1] + ny * rr[1] * 0.2 - dy * 6)
        ctx.line_to(kn[0] - nx * rr[1] * 0.5 + dx * 4, kn[1] - ny * rr[1] * 0.5 + dy * 4)
        _set(ctx, alpha_ink(PAL["ink"], 0.5))
        ctx.set_line_width(inkw * 0.6)
        ctx.stroke()


def _draw_arm(ctx, C, col, a, side, J, inkw, t, phase):
    Q = J["Q"]
    S, E, Wr, ang = a["S"], a["E2"], a["W2"], a["ang"]
    rr = C["arm_r"]
    hide = Q[f"a{side}_hide"] > 0.5
    hand_pt = Wr
    ysign = (-1.0 if side == "l" else 1.0) * (1.0 if Q[f"a{side}_tf"] >= 0 else -1.0)
    tfk = abs(Q[f"a{side}_tf"])
    persp = clamp(1.0 + a["zW"] * 0.0011, 0.88, 1.22)
    hs = C["hand"] * persp
    skin = col["skin"]
    sleeve = C["_sleeve"]
    if not hide:
        hy = ysign * max(0.35, tfk)
        hand_pt = _draw_hand(ctx, skin, PAL["ink"], Wr, ang, Q[f"a{side}_h"], hy, hs, inkw, phase,
                             Q[f"a{side}_fing"], Q[f"a{side}_thumb"], palm_view=Q[f"a{side}_tf"] < 0)
    a["hold_pt"] = hand_pt
    if sleeve == "short":
        ctx.new_path()
        _capsule(ctx, S[0], S[1], rr[0] * 0.8, E[0], E[1], rr[1] * 0.78)
        _capsule(ctx, E[0], E[1], rr[1] * 0.78, Wr[0], Wr[1], rr[2] * 0.75)
        _set(ctx, PAL["ink"])
        ctx.set_line_width(inkw * 2)
        ctx.stroke_preserve()
        _set(ctx, skin)
        ctx.fill()
        m = _lerp2(S, E, 0.62)
        ctx.new_path()
        circle(ctx, S[0], S[1], rr[0] * 1.08)
        _capsule(ctx, S[0], S[1], rr[0] * 1.08, m[0], m[1], rr[0] * 0.98)
        _set(ctx, PAL["ink"])
        ctx.set_line_width(inkw * 2)
        ctx.stroke_preserve()
        _set(ctx, col["top"])
        ctx.fill()
        return
    ctx.new_path()
    circle(ctx, S[0], S[1], rr[0] * 1.04)
    _capsule(ctx, S[0], S[1], rr[0], E[0], E[1], rr[1])
    _capsule(ctx, E[0], E[1], rr[1], Wr[0], Wr[1], rr[2])
    _set(ctx, PAL["ink"])
    ctx.set_line_width(inkw * 2)
    ctx.stroke_preserve()
    _set(ctx, col["top"] if C["_top"] != "labcoat" else col["top"])
    ctx.fill()
    # cuff
    dx, dy = _norm(Wr[0] - E[0], Wr[1] - E[1])
    cuff = {"hoodie": col["top_dk"], "labcoat": col["top_dk"], "suit": "#e9ecf2",
            "uniform": col["top_dk"], "cardigan": col["top_dk"]}.get(C["_top"], col["top_dk"])
    clen = 20 if C["_top"] in ("hoodie", "cardigan") else 12
    ctx.new_path()
    _capsule(ctx, Wr[0] - dx * clen, Wr[1] - dy * clen, rr[2] * 1.05, Wr[0] + dx * 2, Wr[1] + dy * 2,
             rr[2] * 1.02)
    _fs(ctx, cuff, inkw * 0.85)
    # elbow fold
    ex, ey = _norm(E[0] - S[0], E[1] - S[1])
    cr = ex * dy - ey * dx
    if abs(cr) > 0.3:
        nx, ny = -ey * (1 if cr > 0 else -1), ex * (1 if cr > 0 else -1)
        ctx.move_to(E[0] + nx * rr[1] * 0.75 - ex * 8, E[1] + ny * rr[1] * 0.75 - ey * 8)
        ctx.line_to(E[0] + nx * rr[1] * 0.1 + dx * 3, E[1] + ny * rr[1] * 0.1 + dy * 3)
        _set(ctx, alpha_ink(PAL["ink"], 0.45))
        ctx.set_line_width(inkw * 0.55)
        ctx.stroke()


# ============================================================================
# 7b. DRAWING: torso + outfits
# ============================================================================
def _torso_geom(C, J):
    """Torso outline points + per-level frames (centre, normal, wL, wR, front offset)."""
    nd = J["nodes"]
    phi = J["phi"]
    c, s = math.cos(phi), math.sin(phi)
    tw = C["tw"]
    keys = (("hem", "hem"), ("pel", "hip"), ("wst", "waist"), ("chs", "chest"), ("shl", "shoulder"))
    lv = {}
    for i, (nk, wk) in enumerate(keys):
        p = nd[nk]
        up_from = nd[keys[max(0, i - 1)][0]] if i > 0 else nd["hem"]
        up_to = nd[keys[min(len(keys) - 1, i + 1)][0]]
        if i == 0:
            up_from, up_to = nd["hem"], nd["pel"]
        tx, ty = _norm(up_to[0] - up_from[0], up_to[1] - up_from[1])
        nx, ny = -ty, tx
        if ny > 0.9 or (abs(nx) < 1e-6 and abs(ny) < 1e-6):
            nx, ny = 1.0, 0.0
        a, f, b = tw[wk]
        if wk == "chest":
            a += J["Q"]["breath"] * 1.2 * math.sin(TAU * J["t"] / 3.7 + C["seed"])
        fr = f if s >= 0 else b
        bk = b if s >= 0 else f
        wR = math.sqrt((a * c) ** 2 + (fr * s) ** 2)
        wL = math.sqrt((a * c) ** 2 + (bk * s) ** 2)
        lv[wk] = dict(p=p, n=(nx, ny), t=(tx, ty), wL=wL, wR=wR, front=f * s, a=a)
    return lv


def _pt(lv, key, u, du=0.0):
    """Point on level `key` at u (-1 = left edge, 0 = centre, +1 = right edge), du along spine."""
    L = lv[key]
    w = L["wR"] if u >= 0 else L["wL"]
    p, n, t = L["p"], L["n"], L["t"]
    return (p[0] + n[0] * w * u + t[0] * du, p[1] + n[1] * w * u + t[1] * du)


def _front(lv, key, off=0.0, du=0.0):
    """Point on the front centre line of level `key` (off = sideways px, du along spine)."""
    L = lv[key]
    p, n, t = L["p"], L["n"], L["t"]
    k = math.cos(abs(math.asin(clamp(L["front"] / max(1.0, L["a"] + 30), -1, 1))))
    x = L["front"] + off * k
    return (p[0] + n[0] * x + t[0] * du, p[1] + n[1] * x + t[1] * du)


def _torso_pts(C, J, lv):
    sh = J["shj"]
    nk = J["nodes"]["nck"]
    Ls, Lc = lv["shoulder"], lv["chest"]
    t = Ls["t"]
    n = Ls["n"]
    ar = C["arm_r"][0]
    pts = [_pt(lv, "hem", -1.0), _pt(lv, "hip", -1.0), _pt(lv, "waist", -1.0), _pt(lv, "chest", -1.0)]
    sl, sr = sh["l"], sh["r"]
    # outer shoulder tops: whichever is further out than the chest edge
    pts.append((sl[0] - n[0] * ar * 0.25 + t[0] * ar * 0.8, sl[1] - n[1] * ar * 0.25 + t[1] * ar * 0.8))
    nr = C["neck_r"] * 1.35
    pts.append((nk[0] - n[0] * nr + t[0] * 4, nk[1] - n[1] * nr + t[1] * 4))
    pts.append((nk[0] + n[0] * nr + t[0] * 4, nk[1] + n[1] * nr + t[1] * 4))
    pts.append((sr[0] + n[0] * ar * 0.25 + t[0] * ar * 0.8, sr[1] + n[1] * ar * 0.25 + t[1] * ar * 0.8))
    pts += [_pt(lv, "chest", 1.0), _pt(lv, "waist", 1.0), _pt(lv, "hip", 1.0), _pt(lv, "hem", 1.0)]
    hc = lv["hem"]["p"]
    ht = lv["hem"]["t"]
    pts.append((hc[0] - ht[0] * 5, hc[1] - ht[1] * 5))
    return pts


def _draw_hood(ctx, C, col, J, inkw):
    """Tiredness's hood lump behind the neck (drawn before the torso)."""
    nk = J["nodes"]["nck"]
    lv = J["_lv"]
    n, t = lv["shoulder"]["n"], lv["shoulder"]["t"]
    s = math.sin(J["phi"])
    cx = nk[0] - n[0] * s * 22
    cy = nk[1] - n[1] * s * 22
    w = C["neck_r"] * 2.5
    pts = [(cx - n[0] * w + t[0] * -14, cy - n[1] * w - t[1] * 14),
           (cx - n[0] * w * 0.8 + t[0] * 26, cy - n[1] * w * 0.8 + t[1] * 26),
           (cx + t[0] * 36, cy + t[1] * 36),
           (cx + n[0] * w * 0.8 + t[0] * 26, cy + n[1] * w * 0.8 + t[1] * 26),
           (cx + n[0] * w + t[0] * -14, cy + n[1] * w - t[1] * 14),
           (cx, cy - t[1] * 10)]
    _smooth(ctx, pts, True, 0.55)
    _fs(ctx, col["top_dk"], inkw * 2 * 0.5 * 2)


def _draw_neck(ctx, C, col, J, inkw, blush_k=0.0):
    a, b = J["nodes"]["nck"], J["head"]["pivot"]
    r = C["neck_r"]
    ctx.new_path()
    _capsule(ctx, a[0], a[1] + 8, r * 1.05, b[0], b[1], r)
    _set(ctx, PAL["ink"])
    ctx.set_line_width(inkw * 2)
    ctx.stroke_preserve()
    skin = col["skin"]
    if blush_k > 0:
        skin = mixc(skin, PAL["blush"], 0.35 * blush_k)
    _set(ctx, skin)
    ctx.fill()
    # chin shadow
    ctx.save()
    ctx.new_path()
    _capsule(ctx, a[0], a[1] + 8, r * 1.05, b[0], b[1], r)
    ctx.clip()
    ellipse(ctx, b[0], b[1] + 6, r * 1.3, r * 0.8, J["head"]["tilt"])
    _set(ctx, col["skin_sh"])
    ctx.fill()
    ctx.restore()


def _coat_tails(ctx, C, col, J, inkw, part):
    """Lab-coat skirt below the torso hem. part = 'back' (between legs) or 'front'."""
    lv = J["_lv"]
    Q = J["Q"]
    lagQ = J["lag"] or Q
    fd = J["fdir"]
    trail = Q["coat_trail"]
    ln = C["thigh"] * 0.5
    out = {}
    for s_, sgn, u in (("l", -1, -1.0), ("r", 1, 1.0)):
        lp = lagQ[f"l{s_}_p"]
        lo = lagQ[f"l{s_}_o"]
        d3 = _dir(lp * 0.65, lo, sgn)
        dx = d3[0] * math.cos(J["phi"]) + d3[2] * math.sin(J["phi"])
        dy = d3[1]
        dx = dx * 0.8 - fd * trail * 0.55
        dx, dy = _norm(dx, max(0.35, dy))
        top_o = _pt(lv, "hem", u, 2)
        top_i = _front(lv, "hem", sgn * C["tw"]["hem"][0] * 0.16, 2)
        out[s_] = (top_o, top_i, (dx, dy))
    if part == "back":
        (lo_, li_, dl), (ro_, ri_, dr) = out["l"], out["r"]
        pts = [lo_, ro_, (ro_[0] + dr[0] * ln, ro_[1] + dr[1] * ln),
               (lo_[0] + dl[0] * ln, lo_[1] + dl[1] * ln)]
        _poly(ctx, pts)
        _fs(ctx, col["top_dk"], inkw)
        return
    for s_, sgn in (("l", -1), ("r", 1)):
        top_o, top_i, (dx, dy) = out[s_]
        flare = sgn * 10 + (-J["fdir"]) * trail * 22
        bo = (top_o[0] + dx * ln * 1.02 + flare, top_o[1] + dy * ln * 1.02)
        bi = (top_i[0] + dx * ln * 0.96, top_i[1] + dy * ln * 0.96)
        pts = [top_o, bo, bi, top_i]
        _poly(ctx, pts)
        _fs(ctx, col["top"], inkw)
        # hem shading line
        ctx.move_to(*_lerp2(bo, bi, 0.0))
        ctx.line_to(*bi)
        _set(ctx, alpha_ink(col["top_dk"], 1.0))
        ctx.set_line_width(5)
        ctx.stroke()


def _draw_torso(ctx, C, col, J, inkw, t):
    lv = J["_lv"]
    pts = _torso_pts(C, J, lv)
    top = C["_top"]
    base = col["top"]
    ctx.save()
    _smooth(ctx, pts, True, 0.5)
    ctx.clip_preserve()
    _set(ctx, col["top_dk"])
    ctx.fill()
    ctx.translate(-13, -6)
    _smooth(ctx, pts, True, 0.5)
    _set(ctx, base)
    ctx.fill()
    ctx.translate(13, 6)
    anchors = _torso_details(ctx, C, col, J, lv, top, inkw, t)
    ctx.restore()
    _smooth(ctx, pts, True, 0.5)
    _stroke(ctx, PAL["ink"], inkw)
    _torso_overlay(ctx, C, col, J, lv, top, inkw, t)
    return anchors


def _shape(ctx, pts, fc, inkw, tension=0.0):
    if tension:
        _smooth(ctx, pts, True, tension)
    else:
        _poly(ctx, pts)
    _fs(ctx, fc, inkw)


def _torso_details(ctx, C, col, J, lv, top, inkw, t):
    """Garment details inside the torso clip. Returns {'pocket': (x, y)}."""
    ink = PAL["ink"]
    thin = inkw * 0.7
    aw = C["tw"]["waist"][0]
    pocket = _front(lv, "chest", C["tw"]["chest"][0] * 0.5, 22)
    if top == "hoodie":
        # hem band
        _shape(ctx, [_pt(lv, "hem", -1.2, -4), _pt(lv, "hem", 1.2, -4), _pt(lv, "hem", 1.2, 20),
                     _pt(lv, "hem", -1.2, 20)], col["top_dk"], thin)
        # kangaroo pocket
        y0, y1 = 20, 62
        p = [_front(lv, "hem", -aw * 0.62, y0), _front(lv, "hem", aw * 0.62, y0),
             _front(lv, "hem", aw * 0.44, y1 + 26), _front(lv, "hem", -aw * 0.44, y1 + 26)]
        _shape(ctx, p, _dk(col["top"], 0.08), thin, 0.0)
        for sgn in (-1, 1):
            a0 = _front(lv, "hem", sgn * aw * 0.44, y1 + 24)
            a1 = _front(lv, "hem", sgn * aw * 0.6, y0 + 2)
            c0 = _front(lv, "hem", sgn * aw * 0.66, y1 + 16)
            ctx.move_to(*a0)
            _qcurve(ctx, a0, c0, a1)
            _stroke(ctx, ink, thin)
        pocket = _front(lv, "chest", C["tw"]["chest"][0] * 0.45, 26)
    elif top == "polo":
        # placket + buttons
        a0, a1 = _front(lv, "shoulder", -9, 8), _front(lv, "chest", -9, -8)
        b0, b1 = _front(lv, "shoulder", 9, 8), _front(lv, "chest", 9, -8)
        _shape(ctx, [a0, b0, b1, a1], _dk(col["top"], 0.06), thin)
        for k in (0.35, 0.75):
            q = _lerp2(_front(lv, "shoulder", 0, 8), _front(lv, "chest", 0, -8), k)
            circle(ctx, q[0], q[1], 3.2)
            _fs(ctx, "#f4efe2", 2)
        _shape(ctx, [_pt(lv, "hem", -1.2, -4), _pt(lv, "hem", 1.2, -4), _pt(lv, "hem", 1.2, 10),
                     _pt(lv, "hem", -1.2, 10)], col["top_dk"], thin)
    elif top == "labcoat":
        # open front: vest + shirt + slacks visible
        g_top = C["neck_r"] * 1.1
        g_bot = aw * 0.36
        L0, R0 = _front(lv, "shoulder", -g_top, 16), _front(lv, "shoulder", g_top, 16)
        L1, R1 = _front(lv, "hem", -g_bot, -4), _front(lv, "hem", g_bot, -4)
        _shape(ctx, [L0, R0, R1, L1], col["vest"], thin)
        # slacks showing below the vest
        W0, W1 = _front(lv, "waist", -g_bot * 0.9, -8), _front(lv, "waist", g_bot * 0.9, -8)
        _shape(ctx, [W0, W1, R1, L1], col["pants"], thin)
        # shirt collar V
        n0 = _front(lv, "shoulder", 0, -10)
        v = _front(lv, "chest", 0, 10)
        _shape(ctx, [_front(lv, "shoulder", -g_top * 0.9, 18), _front(lv, "shoulder", g_top * 0.9, 18), v],
               "#ffffff", thin)
        _shape(ctx, [_front(lv, "shoulder", -g_top * 0.95, 22), n0, _front(lv, "shoulder", -2, 0),
                     _front(lv, "shoulder", -g_top * 0.2, -8)], "#ffffff", thin)
        # lapels
        for sgn in (-1, 1):
            a = _front(lv, "shoulder", sgn * g_top * 1.0, 18)
            b = _front(lv, "chest", sgn * (g_top * 1.0 + 26), 10)
            c = _front(lv, "chest", sgn * g_top * 0.95, -16)
            _shape(ctx, [a, b, c], col["top_dk"] if sgn > 0 else col["top"], thin)
        # breast pocket (wearer's left = screen right) with pens
        pc = _front(lv, "chest", aw * 0.66, 4)
        pw, ph = 22, 24
        n, tt = lv["chest"]["n"], lv["chest"]["t"]

        def Pp(x, y):
            return (pc[0] + n[0] * x - tt[0] * y, pc[1] + n[1] * x - tt[1] * y)
        for i, pcol in enumerate(("#2b6cd8", "#e2463f")):
            x = -8 + i * 11
            _shape(ctx, [Pp(x - 3, -10), Pp(x + 3, -10), Pp(x + 3, 12), Pp(x - 3, 12)], pcol, 2.5)
        _shape(ctx, [Pp(-pw, 0), Pp(pw, 0), Pp(pw * 0.9, ph), Pp(-pw * 0.9, ph)], col["top"], thin)
        pocket = Pp(0, 6)
        # hip pockets
        for sgn in (-1, 1):
            q = _front(lv, "hem", sgn * aw * 0.85, 30)
            ctx.move_to(q[0] - 18, q[1])
            ctx.line_to(q[0] + 18, q[1])
            _stroke(ctx, ink, thin)
    elif top == "suit":
        g = C["neck_r"] * 1.0
        v = _front(lv, "waist", 0, 20)
        _shape(ctx, [_front(lv, "shoulder", -g, 20), _front(lv, "shoulder", g, 20), v],
               col["top_dk"], thin)
        for sgn in (-1, 1):
            a = _front(lv, "shoulder", sgn * g * 1.05, 18)
            b = _front(lv, "chest", sgn * (g + 30), 16)
            c = _front(lv, "chest", sgn * (g + 14), -6)
            _shape(ctx, [a, b, c, v], _dk(col["top"], 0.18), thin)
        btn = _front(lv, "waist", 0, 14)
        circle(ctx, btn[0], btn[1], 4.5)
        _fs(ctx, "#111218", 2)
        # jacket front parting below the button
        h0 = _front(lv, "hem", 0, 0)
        ctx.move_to(*btn)
        ctx.line_to(h0[0] - 6, h0[1] + 6)
        _stroke(ctx, ink, thin)
        pocket = _front(lv, "chest", C["tw"]["chest"][0] * 0.5, 14)
    elif top == "uniform":
        # placket
        a0, a1 = _front(lv, "shoulder", 0, 10), _front(lv, "hem", 0, 0)
        ctx.move_to(*a0)
        ctx.line_to(*a1)
        _stroke(ctx, ink, thin)
        for k in (0.2, 0.42, 0.64):
            q = _lerp2(a0, a1, k)
            circle(ctx, q[0] + 6, q[1], 3.5)
            _fs(ctx, "#c9ced8", 2)
        # chest pocket flaps
        for sgn in (-1, 1):
            c0 = _front(lv, "chest", sgn * 46, 14)
            _shape(ctx, [(c0[0] - 22, c0[1] - 8), (c0[0] + 22, c0[1] - 8), (c0[0] + 20, c0[1] + 6),
                         (c0[0], c0[1] + 12), (c0[0] - 20, c0[1] + 6)], col["top_dk"], thin)
        # belt
        _shape(ctx, [_pt(lv, "hem", -1.2, 14), _pt(lv, "hem", 1.2, 14), _pt(lv, "hem", 1.2, 34),
                     _pt(lv, "hem", -1.2, 34)], "#1a1b22", thin)
        bk = _front(lv, "hem", 0, 24)
        ctx.rectangle(bk[0] - 11, bk[1] - 8, 22, 16)
        _fs(ctx, "#c9ced8", 2.5)
        pocket = _front(lv, "chest", 46, 22)
    elif top == "cardigan":
        g_top = C["neck_r"] * 1.0
        L0, R0 = _front(lv, "shoulder", -g_top, 14), _front(lv, "shoulder", g_top, 14)
        v = _front(lv, "waist", 0, 6)
        _shape(ctx, [L0, R0, (v[0] + 4, v[1]), (v[0] - 4, v[1])], col["blouse"], thin)
        for k in (0.25, 0.55, 0.85):
            q = _lerp2(L0, _front(lv, "hem", -6, 0), 0.25 + k * 0.7)
            circle(ctx, q[0] - 8, q[1], 3.5)
            _fs(ctx, "#f2e9f7", 2)
        _shape(ctx, [_pt(lv, "hem", -1.2, -4), _pt(lv, "hem", 1.2, -4), _pt(lv, "hem", 1.2, 16),
                     _pt(lv, "hem", -1.2, 16)], col["top_dk"], thin)
        # name badge
        bc = _front(lv, "chest", 44, 18)
        ctx.rectangle(bc[0] - 15, bc[1] - 7, 30, 14)
        _fs(ctx, "#ffffff", 2.5)
        pocket = bc
    return {"pocket": pocket}


def _torso_overlay(ctx, C, col, J, lv, top, inkw, t):
    """Details that sit on top of the torso outline (collars, strings, badges)."""
    thin = inkw * 0.7
    nk = J["nodes"]["nck"]
    n, tt = lv["shoulder"]["n"], lv["shoulder"]["t"]
    if top == "hoodie":
        # collar ribbing around the neck front
        fx = lv["shoulder"]["front"] * 0.35
        cx, cy = nk[0] + n[0] * fx, nk[1] + n[1] * fx
        r = C["neck_r"] * 1.4
        ctx.move_to(cx - n[0] * r, cy - n[1] * r)
        _qcurve(ctx, (cx - n[0] * r, cy - n[1] * r), (cx - tt[0] * 30, cy - tt[1] * 30 + 0),
                (cx + n[0] * r, cy + n[1] * r))
        _stroke(ctx, PAL["ink"], inkw * 0.9)
        # drawstrings
        sw_ = math.sin(t * 1.3 + C["seed"]) * 2
        for sgn in (-1, 1):
            a = (cx + n[0] * sgn * 13 - tt[0] * 20, cy + n[1] * sgn * 13 - tt[1] * 20)
            ln = 70 + sgn * 8
            b = (a[0] - tt[0] * ln + sw_ + sgn * 3, a[1] - tt[1] * ln)
            ctx.move_to(*a)
            _qcurve(ctx, a, ((a[0] + b[0]) / 2 + sgn * 4, (a[1] + b[1]) / 2), b)
            _stroke(ctx, PAL["ink"], 7.5)
            ctx.move_to(*a)
            _qcurve(ctx, a, ((a[0] + b[0]) / 2 + sgn * 4, (a[1] + b[1]) / 2), b)
            _stroke(ctx, "#e9e6f2", 3.2)
            ctx.new_path()
            _capsule(ctx, b[0], b[1] - 2, 3.6, b[0], b[1] + 9, 3.6)
            _fs(ctx, "#d8d4e2", 2.5)
    elif top == "polo":
        fx = lv["shoulder"]["front"] * 0.35
        cx, cy = nk[0] + n[0] * fx, nk[1] + n[1] * fx
        r = C["neck_r"] * 1.35
        for sgn in (-1, 1):
            p = [(cx + n[0] * sgn * r * 0.15 + tt[0] * 2, cy + tt[1] * 2),
                 (cx + n[0] * sgn * r * 1.15, cy + n[1] * sgn * r * 1.15 - tt[1] * 6),
                 (cx + n[0] * sgn * r * 0.75 - tt[0] * 28, cy - tt[1] * 28)]
            _shape(ctx, p, _lt(col["top"], 0.25), thin)
        # lanyard + badge
        b = _front(lv, "chest", -6, -6)
        for sgn in (-1, 1):
            ctx.move_to(cx + n[0] * sgn * r, cy + n[1] * sgn * r)
            ctx.line_to(b[0] + sgn * 5, b[1] - 18)
            _stroke(ctx, PAL["ink"], 8)
            ctx.move_to(cx + n[0] * sgn * r, cy + n[1] * sgn * r)
            ctx.line_to(b[0] + sgn * 5, b[1] - 18)
            _stroke(ctx, PAL["hush"], 4)
        ctx.new_path()
        ctx.rectangle(b[0] - 18, b[1] - 16, 36, 46)
        _fs(ctx, "#ffffff", 3)
        ctx.rectangle(b[0] - 18, b[1] - 16, 36, 9)
        _fs(ctx, PAL["hush"], 2)
        ctx.rectangle(b[0] - 10, b[1] - 2, 20, 18)
        _fs(ctx, "#c9d2da", 2)
    elif top == "suit":
        pin = _front(lv, "chest", 34, 26)
        circle(ctx, pin[0], pin[1], 5.5)
        _fs(ctx, PAL["hush"], 2.5)
    elif top == "uniform":
        # badge (wearer's left) + shoulder radio
        bd = _front(lv, "chest", 48, 34)
        p = [(bd[0], bd[1] - 14), (bd[0] + 12, bd[1] - 8), (bd[0] + 10, bd[1] + 8), (bd[0], bd[1] + 14),
             (bd[0] - 10, bd[1] + 8), (bd[0] - 12, bd[1] - 8)]
        _shape(ctx, p, "#e8c25a", 3)
        sl = J["shj"]["l"]
        rx, ry = sl[0] + n[0] * 26 - tt[0] * 0, sl[1] + 24
        ctx.new_path()
        ctx.rectangle(rx - 12, ry - 16, 24, 32)
        _fs(ctx, "#1a1b22", 3)
        ctx.move_to(rx - 6, ry - 16)
        ctx.line_to(rx - 6, ry - 38)
        _stroke(ctx, PAL["ink"], 5)
        circle(ctx, rx + 3, ry - 6, 3)
        _fs(ctx, PAL["danger"], 1.5)
